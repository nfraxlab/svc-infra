from __future__ import annotations

import logging
import re
import time
from typing import Any
from urllib.parse import urlparse

import httpx
from pydantic import SecretStr

from svc_infra.connect.registry import OAuthProvider
from svc_infra.connect.registry import registry as _registry

logger = logging.getLogger(__name__)


class MCPOAuthNotSupported(Exception):
    """Raised when an MCP server does not implement the OAuth Authorization spec.

    Callers should fall back to the manual-token UX when this is raised.
    """


_DISCOVERY_CACHE: dict[str, tuple[OAuthProvider, float]] = {}
_CACHE_TTL_SECONDS = 3600  # MCP server metadata rarely changes


def _origin_url(url: str) -> str:
    """Extract the origin (scheme + authority) from a URL.

    RFC 9728 well-known endpoints live at the origin level, not relative
    to the resource path.  For ``https://mcp.notion.com/mcp`` this returns
    ``https://mcp.notion.com``.
    """
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.hostname or 'localhost'}"
    if parsed.port:
        origin += f":{parsed.port}"
    return origin


def parse_www_authenticate(header: str) -> dict[str, str]:
    """Parse a Bearer WWW-Authenticate header into a key/value dict.

    Handles: Bearer resource_metadata="https://..." realm="..."
    """
    result: dict[str, str] = {}
    for match in re.finditer(r'(\w+)=["\']?([^"\',\s]+)["\']?', header):
        result[match.group(1)] = match.group(2)
    return result


class MCPOAuthDiscovery:
    """Discover OAuth authorization server metadata from an MCP server URL.

    Implements RFC 9728 (OAuth 2.0 Protected Resource Metadata) +
    RFC 8414 (OAuth 2.0 Authorization Server Metadata).

    After token acquisition, the access token is injected into the Authorization
    header of MCP connections. ai_infra.mcp.client.MCPClient picks it up through
    the standard Bearer path — this module is only responsible for obtaining and
    refreshing the token; protocol internals remain in ai-infra.
    """

    async def discover(
        self,
        mcp_server_url: str,
        *,
        api_base: str | None = None,
    ) -> OAuthProvider:
        """Discover a fully-populated OAuthProvider for the given MCP server URL.

        Results are cached in-process for 1 hour.

        When *api_base* is provided and the authorization server advertises a
        ``registration_endpoint`` (RFC 7591), the client is dynamically
        registered so a valid ``client_id`` is obtained automatically.

        Raises MCPOAuthNotSupported if:
        - The server does not implement RFC 9728 resource metadata
        - The authorization server metadata is unreachable or malformed
        """
        now = time.monotonic()
        cached = _DISCOVERY_CACHE.get(mcp_server_url)
        if cached is not None:
            provider, ts = cached
            if now - ts < _CACHE_TTL_SECONDS:
                logger.debug(
                    "discover: cache hit", extra={"url": mcp_server_url, "provider": provider.name}
                )
                return provider

        resource_meta = await self._fetch_resource_metadata(mcp_server_url)
        auth_server_url = self._extract_auth_server(resource_meta)
        logger.debug("discover: auth_server_url=%s", auth_server_url, extra={"url": mcp_server_url})

        registered = _registry.list()
        logger.info(
            "discover: registry has %d provider(s): %s",
            len(registered),
            [p.name for p in registered],
            extra={"url": mcp_server_url},
        )
        # Shortcut: if a registered provider already covers this auth server
        # (i.e. its authorize_url begins with the auth_server_url), use it
        # directly.  This avoids the RFC 8414 metadata fetch for providers
        # like GitHub that do not publish /.well-known/oauth-authorization-server.
        for existing in registered:
            if existing.authorize_url.startswith(auth_server_url):
                logger.info(
                    "discover: shortcut matched provider=%s",
                    existing.name,
                    extra={"url": mcp_server_url},
                )
                _DISCOVERY_CACHE[mcp_server_url] = (existing, now)
                return existing

        logger.info(
            "discover: no shortcut match, falling back to RFC 8414",
            extra={"url": mcp_server_url, "auth_server_url": auth_server_url},
        )
        auth_meta = await self._fetch_auth_server_metadata(auth_server_url)

        provider = self._build_provider(mcp_server_url, auth_meta)

        # Dynamic client registration (RFC 7591): when no pre-configured
        # client_id exists and the auth server offers a registration endpoint,
        # register automatically to obtain credentials.
        registration_endpoint = auth_meta.get("registration_endpoint")
        if not provider.client_id and registration_endpoint and api_base:
            redirect_uri = f"{api_base}/connect/callback/{provider.name}"
            provider = await self._register_dynamic_client(
                provider, registration_endpoint, redirect_uri
            )

        _DISCOVERY_CACHE[mcp_server_url] = (provider, now)
        return provider

    async def is_mcp_oauth_supported(self, mcp_server_url: str) -> bool:
        """Check whether the MCP server requires OAuth authorization.

        First probes the server for a 401 response with a WWW-Authenticate:
        Bearer header (RFC 9728 §3).  If the server does not return 401 (some
        servers return 404 for unauthenticated requests), falls back to
        checking the well-known resource metadata endpoint directly.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    mcp_server_url,
                    json={"jsonrpc": "2.0", "method": "initialize", "id": 1, "params": {}},
                    headers={"Content-Type": "application/json"},
                )
            logger.debug(
                "OAuth probe response",
                extra={
                    "url": mcp_server_url,
                    "status": response.status_code,
                    "www_auth": response.headers.get("www-authenticate", ""),
                },
            )
            if response.status_code == 401:
                www_auth = response.headers.get("www-authenticate", "")
                if www_auth.lower().startswith("bearer"):
                    parsed = parse_www_authenticate(www_auth)
                    if "resource_metadata" in parsed:
                        logger.info(
                            "OAuth probe: 401 with resource_metadata",
                            extra={"url": mcp_server_url, "parsed_keys": list(parsed.keys())},
                        )
                        return True

            # 401 without resource_metadata field — some servers (e.g.
            # Notion /mcp) return a plain Bearer challenge.  Fall through to
            # the well-known check below.
            if response.status_code == 401:
                logger.debug(
                    "OAuth probe: 401 without resource_metadata, trying well-known",
                    extra={"url": mcp_server_url},
                )
                return await self._check_wellknown_resource_metadata(mcp_server_url)

            # Server did not return 401 — fall back to checking the well-known
            # endpoint directly.  Some servers (e.g. Notion) return 404 for
            # unauthenticated requests but still publish RFC 9728 metadata.
            logger.debug(
                "OAuth probe: no 401, trying well-known fallback",
                extra={"url": mcp_server_url, "status": response.status_code},
            )
            return await self._check_wellknown_resource_metadata(mcp_server_url)
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            logger.warning(
                "OAuth probe request failed", extra={"url": mcp_server_url, "error": str(exc)}
            )
            return False

    async def _check_wellknown_resource_metadata(self, mcp_server_url: str) -> bool:
        """GET the well-known resource metadata URL and check for authorization_servers."""
        url = _origin_url(mcp_server_url) + "/.well-known/oauth-protected-resource"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers={"Accept": "application/json"})
        except httpx.RequestError as exc:
            logger.debug(
                "Well-known fallback request failed",
                extra={"url": url, "error": str(exc)},
            )
            return False

        if response.status_code != 200:
            logger.debug(
                "Well-known fallback: non-200",
                extra={"url": url, "status": response.status_code},
            )
            return False

        try:
            data = response.json()
        except Exception:
            return False

        result = bool(data.get("authorization_servers"))
        logger.info(
            "Well-known fallback: authorization_servers=%s",
            result,
            extra={"url": url},
        )
        return result

    async def _fetch_resource_metadata(self, mcp_server_url: str) -> dict[str, Any]:
        # RFC 9728 §3: the protected resource advertises its metadata URL in the
        # WWW-Authenticate header of its 401 response.  Probe the MCP endpoint
        # first so we can use the canonical URL rather than constructing a guess.
        url = await self._probe_resource_metadata_url(mcp_server_url)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers={"Accept": "application/json"})
        except httpx.RequestError as exc:
            raise MCPOAuthNotSupported(
                f"Could not reach resource metadata endpoint: {exc}"
            ) from exc

        if response.status_code == 404 or response.status_code == 405:
            raise MCPOAuthNotSupported(
                f"Server at {mcp_server_url} does not expose RFC 9728 resource metadata "
                f"(got {response.status_code})"
            )
        if response.status_code != 200:
            raise MCPOAuthNotSupported(f"Resource metadata returned {response.status_code}")

        try:
            data: dict[str, Any] = response.json()
        except Exception as exc:
            raise MCPOAuthNotSupported("Resource metadata response is not valid JSON") from exc

        return data

    async def _probe_resource_metadata_url(self, mcp_server_url: str) -> str:
        """Probe the MCP server to discover the canonical resource metadata URL.

        Sends an unauthenticated POST to the MCP endpoint and extracts
        ``resource_metadata`` from the ``WWW-Authenticate`` header of the 401
        response (RFC 9728 §3).  Falls back to constructing the default path
        (``<mcp_server_url>/.well-known/oauth-protected-resource``) if the
        server does not include the field or is unreachable.
        """
        default = _origin_url(mcp_server_url) + "/.well-known/oauth-protected-resource"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    mcp_server_url,
                    json={"jsonrpc": "2.0", "method": "initialize", "id": 1, "params": {}},
                    headers={"Content-Type": "application/json"},
                )
        except httpx.RequestError:
            return default

        if response.status_code != 401:
            return default

        www_auth = response.headers.get("www-authenticate", "")
        if www_auth.lower().startswith("bearer"):
            parsed = parse_www_authenticate(www_auth)
            if "resource_metadata" in parsed:
                return parsed["resource_metadata"]

        return default

    def _extract_auth_server(self, resource_meta: dict[str, Any]) -> str:
        servers = resource_meta.get("authorization_servers")
        if not servers or not isinstance(servers, list):
            raise MCPOAuthNotSupported("Resource metadata contains no authorization_servers field")
        return str(servers[0]).rstrip("/")

    async def _fetch_auth_server_metadata(self, auth_server_url: str) -> dict[str, Any]:
        url = auth_server_url + "/.well-known/oauth-authorization-server"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers={"Accept": "application/json"})
        except httpx.RequestError as exc:
            raise MCPOAuthNotSupported(
                f"Could not reach authorization server metadata: {exc}"
            ) from exc

        if response.status_code != 200:
            raise MCPOAuthNotSupported(
                f"Authorization server metadata returned {response.status_code}"
            )

        try:
            data: dict[str, Any] = response.json()
        except Exception as exc:
            raise MCPOAuthNotSupported("Authorization server metadata is not valid JSON") from exc

        return data

    def _build_provider(self, mcp_server_url: str, auth_meta: dict[str, Any]) -> OAuthProvider:
        authorize_url = auth_meta.get("authorization_endpoint")
        token_url = auth_meta.get("token_endpoint")
        if not authorize_url or not token_url:
            raise MCPOAuthNotSupported(
                "Authorization server metadata missing authorization_endpoint or token_endpoint"
            )

        supported_methods = auth_meta.get("code_challenge_methods_supported", [])
        pkce_required = "S256" in supported_methods or not supported_methods

        # If a registered provider already covers this authorization_endpoint,
        # reuse it so the pre-configured client_id/secret are preserved.
        # This is required for providers like GitHub that do not support
        # dynamic client registration (RFC 7591).
        for existing in _registry.list():
            if existing.authorize_url.rstrip("/") == authorize_url.rstrip("/"):
                return existing

        hostname = urlparse(mcp_server_url).hostname or "unknown"
        return OAuthProvider(
            name=f"mcp-{hostname}",
            client_id="",
            client_secret=SecretStr(""),
            authorize_url=authorize_url,
            token_url=token_url,
            revoke_url=auth_meta.get("revocation_endpoint"),
            default_scopes=[],
            pkce_required=pkce_required,
            extra_authorize_params={},
            userinfo_url=None,
        )

    async def _register_dynamic_client(
        self,
        provider: OAuthProvider,
        registration_endpoint: str,
        redirect_uri: str,
    ) -> OAuthProvider:
        """RFC 7591 Dynamic Client Registration.

        Registers with the authorization server to obtain a ``client_id``.
        Returns a new OAuthProvider with the credentials populated.
        Falls back to the original provider (empty client_id) on failure.
        """
        body = {
            "client_name": "nfrax-connect",
            "redirect_uris": [redirect_uri],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    registration_endpoint,
                    json=body,
                    headers={"Content-Type": "application/json"},
                )
        except httpx.RequestError as exc:
            logger.warning(
                "Dynamic client registration request failed: %s",
                exc,
                extra={"endpoint": registration_endpoint},
            )
            return provider

        if response.status_code not in (200, 201):
            logger.warning(
                "Dynamic client registration returned %d",
                response.status_code,
                extra={
                    "endpoint": registration_endpoint,
                    "body": response.text[:500],
                },
            )
            return provider

        try:
            data = response.json()
        except Exception:
            logger.warning("Dynamic client registration response is not valid JSON")
            return provider

        client_id = data.get("client_id", "")
        client_secret = data.get("client_secret", "")
        if not client_id:
            logger.warning("Dynamic client registration response missing client_id")
            return provider

        logger.info(
            "Dynamic client registered: client_id=%s provider=%s",
            client_id,
            provider.name,
            extra={"endpoint": registration_endpoint},
        )

        return provider.model_copy(
            update={
                "client_id": client_id,
                "client_secret": SecretStr(client_secret) if client_secret else SecretStr(""),
            }
        )
