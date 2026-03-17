from __future__ import annotations

import re
import time
from typing import Any

import httpx

from svc_infra.connect.registry import OAuthProvider


class MCPOAuthNotSupported(Exception):
    """Raised when an MCP server does not implement the OAuth Authorization spec.

    Callers should fall back to the manual-token UX when this is raised.
    """


_DISCOVERY_CACHE: dict[str, tuple[OAuthProvider, float]] = {}
_CACHE_TTL_SECONDS = 3600  # MCP server metadata rarely changes


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

    async def discover(self, mcp_server_url: str) -> OAuthProvider:
        """Discover a fully-populated OAuthProvider for the given MCP server URL.

        Results are cached in-process for 1 hour.

        Raises MCPOAuthNotSupported if:
        - The server does not implement RFC 9728 resource metadata
        - The authorization server metadata is unreachable or malformed
        """
        now = time.monotonic()
        cached = _DISCOVERY_CACHE.get(mcp_server_url)
        if cached is not None:
            provider, ts = cached
            if now - ts < _CACHE_TTL_SECONDS:
                return provider

        resource_meta = await self._fetch_resource_metadata(mcp_server_url)
        auth_server_url = self._extract_auth_server(resource_meta)
        auth_meta = await self._fetch_auth_server_metadata(auth_server_url)

        provider = self._build_provider(mcp_server_url, auth_meta)
        _DISCOVERY_CACHE[mcp_server_url] = (provider, now)
        return provider

    async def is_mcp_oauth_supported(self, mcp_server_url: str) -> bool:
        """Lightweight check: probe the MCP server and inspect the 401 response headers.

        Returns True if the server returns a WWW-Authenticate: Bearer header containing
        resource_metadata, indicating it implements RFC 9728.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    mcp_server_url,
                    json={"jsonrpc": "2.0", "method": "initialize", "id": 1, "params": {}},
                    headers={"Content-Type": "application/json"},
                )
            if response.status_code != 401:
                return False
            www_auth = response.headers.get("www-authenticate", "")
            if not www_auth.lower().startswith("bearer"):
                return False
            parsed = parse_www_authenticate(www_auth)
            return "resource_metadata" in parsed
        except (httpx.RequestError, httpx.HTTPStatusError):
            return False

    async def _fetch_resource_metadata(self, mcp_server_url: str) -> dict[str, Any]:
        url = mcp_server_url.rstrip("/") + "/.well-known/oauth-protected-resource"
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

    def _extract_auth_server(self, resource_meta: dict[str, Any]) -> str:
        servers = resource_meta.get("authorization_servers")
        if not servers or not isinstance(servers, list):
            raise MCPOAuthNotSupported("Resource metadata contains no authorization_servers field")
        return servers[0].rstrip("/")

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

        from svc_infra.connect.registry import OAuthProvider as _OAuthProvider

        return _OAuthProvider(
            name=f"mcp:{mcp_server_url}",
            client_id="",
            client_secret="",
            authorize_url=authorize_url,
            token_url=token_url,
            revoke_url=auth_meta.get("revocation_endpoint"),
            default_scopes=[],
            pkce_required=pkce_required,
            extra_authorize_params={},
            userinfo_url=None,
        )
