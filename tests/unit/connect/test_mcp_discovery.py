from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from svc_infra.connect import mcp_discovery as _mod
from svc_infra.connect.mcp_discovery import (
    MCPOAuthDiscovery,
    MCPOAuthNotSupported,
    parse_www_authenticate,
)


def _mock_http_response(
    status_code: int, json_data: dict, headers: dict | None = None
) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.headers = headers or {}
    return resp


class TestParseWwwAuthenticate:
    def test_parses_resource_metadata(self):
        header = 'Bearer resource_metadata="https://example.com/.well-known/oauth"'
        result = parse_www_authenticate(header)
        assert result.get("resource_metadata") == "https://example.com/.well-known/oauth"

    def test_parses_multiple_fields(self):
        header = 'Bearer resource_metadata="https://auth.example.com/meta" realm="api"'
        result = parse_www_authenticate(header)
        assert "resource_metadata" in result
        assert "realm" in result

    def test_empty_header_returns_empty_dict(self):
        assert parse_www_authenticate("") == {}

    def test_non_bearer_header_parsed_best_effort(self):
        header = "Basic realm=example"
        result = parse_www_authenticate(header)
        assert "realm" in result


class TestMCPOAuthDiscovery:
    def setup_method(self):
        _mod._DISCOVERY_CACHE.clear()

    def _make_discovery(self) -> MCPOAuthDiscovery:
        return MCPOAuthDiscovery()

    @pytest.mark.asyncio
    async def test_full_discovery_success(self):
        """Happy path: resource metadata + auth server metadata → OAuthProvider."""
        resource_meta = {
            "resource": "https://mcp.example.com",
            "authorization_servers": ["https://auth.example.com"],
        }
        auth_meta = {
            "issuer": "https://auth.example.com",
            "authorization_endpoint": "https://auth.example.com/authorize",
            "token_endpoint": "https://auth.example.com/token",
        }

        discovery = self._make_discovery()
        with (
            patch.object(
                discovery,
                "_fetch_resource_metadata",
                new_callable=AsyncMock,
                return_value=resource_meta,
            ),
            patch.object(
                discovery,
                "_fetch_auth_server_metadata",
                new_callable=AsyncMock,
                return_value=auth_meta,
            ),
        ):
            provider = await discovery.discover("https://mcp.example.com")

        assert provider.name == "mcp-mcp.example.com"
        assert provider.authorize_url == "https://auth.example.com/authorize"
        assert provider.token_url == "https://auth.example.com/token"

    @pytest.mark.asyncio
    async def test_in_process_cache_hit(self):
        """Second call with same URL returns cached result without calling helpers."""
        resource_meta = {
            "authorization_servers": ["https://auth.example.com"],
        }
        auth_meta = {
            "authorization_endpoint": "https://auth.example.com/authorize",
            "token_endpoint": "https://auth.example.com/token",
        }

        discovery = self._make_discovery()
        with (
            patch.object(
                discovery,
                "_fetch_resource_metadata",
                new_callable=AsyncMock,
                return_value=resource_meta,
            ) as mock_res,
            patch.object(
                discovery,
                "_fetch_auth_server_metadata",
                new_callable=AsyncMock,
                return_value=auth_meta,
            ),
        ):
            await discovery.discover("https://mcp.example.com")
            await discovery.discover("https://mcp.example.com")

        assert mock_res.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_expires(self):
        """Cache entry older than TTL triggers a fresh discovery."""
        resource_meta = {"authorization_servers": ["https://auth.example.com"]}
        auth_meta = {
            "authorization_endpoint": "https://auth.example.com/authorize",
            "token_endpoint": "https://auth.example.com/token",
        }

        url = "https://mcp.example.com"
        discovery = self._make_discovery()

        with (
            patch.object(
                discovery,
                "_fetch_resource_metadata",
                new_callable=AsyncMock,
                return_value=resource_meta,
            ) as mock_res,
            patch.object(
                discovery,
                "_fetch_auth_server_metadata",
                new_callable=AsyncMock,
                return_value=auth_meta,
            ),
        ):
            await discovery.discover(url)
            _mod._DISCOVERY_CACHE[url] = (
                _mod._DISCOVERY_CACHE[url][0],
                time.monotonic() - _mod._CACHE_TTL_SECONDS - 1,
            )
            await discovery.discover(url)

        assert mock_res.call_count == 2

    @pytest.mark.asyncio
    async def test_raises_when_no_authorization_servers(self):
        """Missing authorization_servers field → MCPOAuthNotSupported."""
        resource_meta = {"resource": "https://mcp.example.com"}

        discovery = self._make_discovery()
        with patch.object(
            discovery,
            "_fetch_resource_metadata",
            new_callable=AsyncMock,
            return_value=resource_meta,
        ):
            with pytest.raises(MCPOAuthNotSupported, match="authorization_servers"):
                await discovery.discover("https://mcp.example.com")

    @pytest.mark.asyncio
    async def test_raises_when_missing_authorize_endpoint(self):
        """Auth server metadata missing authorization_endpoint → MCPOAuthNotSupported."""
        resource_meta = {"authorization_servers": ["https://auth.example.com"]}
        auth_meta = {"token_endpoint": "https://auth.example.com/token"}

        discovery = self._make_discovery()
        with (
            patch.object(
                discovery,
                "_fetch_resource_metadata",
                new_callable=AsyncMock,
                return_value=resource_meta,
            ),
            patch.object(
                discovery,
                "_fetch_auth_server_metadata",
                new_callable=AsyncMock,
                return_value=auth_meta,
            ),
        ):
            with pytest.raises(MCPOAuthNotSupported, match="authorization_endpoint"):
                await discovery.discover("https://mcp.example.com")

    @pytest.mark.asyncio
    async def test_is_mcp_oauth_supported_true(self):
        """Returns True when server responds 401 + Bearer WWW-Authenticate with resource_metadata."""
        mock_resp = _mock_http_response(
            401,
            {},
            headers={
                "www-authenticate": 'Bearer resource_metadata="https://mcp.example.com/.well-known/oauth"'
            },
        )
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        discovery = self._make_discovery()
        with patch("svc_infra.connect.mcp_discovery.httpx.AsyncClient", return_value=mock_client):
            result = await discovery.is_mcp_oauth_supported("https://mcp.example.com")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_mcp_oauth_supported_false_on_200(self):
        """Returns False when server responds with 200 instead of 401."""
        mock_resp = _mock_http_response(200, {}, headers={})
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        discovery = self._make_discovery()
        with patch("svc_infra.connect.mcp_discovery.httpx.AsyncClient", return_value=mock_client):
            result = await discovery.is_mcp_oauth_supported("https://mcp.example.com")
        assert result is False

    @pytest.mark.asyncio
    async def test_is_mcp_oauth_supported_false_on_network_error(self):
        """Returns False (no raise) when server is unreachable."""
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

        discovery = self._make_discovery()
        with patch("svc_infra.connect.mcp_discovery.httpx.AsyncClient", return_value=mock_client):
            result = await discovery.is_mcp_oauth_supported("https://mcp.example.com")
        assert result is False

    @pytest.mark.asyncio
    async def test_fetch_resource_metadata_raises_on_404(self):
        """404 from resource metadata endpoint → MCPOAuthNotSupported."""
        mock_resp = _mock_http_response(404, {})
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)

        discovery = self._make_discovery()
        with (
            patch.object(
                discovery,
                "_probe_resource_metadata_url",
                new_callable=AsyncMock,
                return_value="https://mcp.example.com/.well-known/oauth-protected-resource",
            ),
            patch("svc_infra.connect.mcp_discovery.httpx.AsyncClient", return_value=mock_client),
        ):
            with pytest.raises(MCPOAuthNotSupported, match="RFC 9728"):
                await discovery._fetch_resource_metadata("https://mcp.example.com")

    @pytest.mark.asyncio
    async def test_fetch_resource_metadata_raises_on_network_error(self):
        """Network error fetching resource metadata → MCPOAuthNotSupported."""
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

        discovery = self._make_discovery()
        with (
            patch.object(
                discovery,
                "_probe_resource_metadata_url",
                new_callable=AsyncMock,
                return_value="https://mcp.example.com/.well-known/oauth-protected-resource",
            ),
            patch("svc_infra.connect.mcp_discovery.httpx.AsyncClient", return_value=mock_client),
        ):
            with pytest.raises(MCPOAuthNotSupported, match="resource metadata"):
                await discovery._fetch_resource_metadata("https://mcp.example.com")

    @pytest.mark.asyncio
    async def test_probe_resource_metadata_url_returns_header_url(self):
        """When server returns 401 with resource_metadata in WWW-Authenticate, use that URL."""
        mock_resp = _mock_http_response(
            401,
            {},
            headers={
                "www-authenticate": 'Bearer resource_metadata="https://api.example.com/.well-known/oauth-protected-resource/mcp/"'
            },
        )
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        discovery = self._make_discovery()
        with patch("svc_infra.connect.mcp_discovery.httpx.AsyncClient", return_value=mock_client):
            url = await discovery._probe_resource_metadata_url("https://api.example.com/mcp/")

        assert url == "https://api.example.com/.well-known/oauth-protected-resource/mcp/"

    @pytest.mark.asyncio
    async def test_probe_resource_metadata_url_falls_back_on_200(self):
        """When server returns 200 (no auth), fall back to default URL construction."""
        mock_resp = _mock_http_response(200, {}, headers={})
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        discovery = self._make_discovery()
        with patch("svc_infra.connect.mcp_discovery.httpx.AsyncClient", return_value=mock_client):
            url = await discovery._probe_resource_metadata_url("https://mcp.example.com/")

        assert url == "https://mcp.example.com/.well-known/oauth-protected-resource"

    @pytest.mark.asyncio
    async def test_probe_resource_metadata_url_falls_back_on_network_error(self):
        """Network error probing server falls back to default URL construction."""
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))

        discovery = self._make_discovery()
        with patch("svc_infra.connect.mcp_discovery.httpx.AsyncClient", return_value=mock_client):
            url = await discovery._probe_resource_metadata_url("https://mcp.example.com/")

        assert url == "https://mcp.example.com/.well-known/oauth-protected-resource"

    def test_build_provider_reuses_registered_provider_on_matching_auth_url(self):
        """When a registered provider's authorize_url matches the discovered
        authorization_endpoint, _build_provider returns that provider so its
        client_id/secret are preserved (needed for GitHub which has no dynamic
        client registration)."""
        from pydantic import SecretStr as _SecretStr

        from svc_infra.connect.registry import OAuthProvider

        github_provider = OAuthProvider(
            name="github",
            client_id="test-client-id",
            client_secret=_SecretStr("test-client-secret"),
            authorize_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            default_scopes=["repo", "user:email"],
        )

        discovery = self._make_discovery()
        auth_meta = {
            "authorization_endpoint": "https://github.com/login/oauth/authorize",
            "token_endpoint": "https://github.com/login/oauth/access_token",
            "code_challenge_methods_supported": ["S256"],
        }

        with patch("svc_infra.connect.mcp_discovery._registry") as mock_reg:
            mock_reg.list.return_value = [github_provider]
            result = discovery._build_provider("https://api.githubcopilot.com/mcp/", auth_meta)

        assert result is github_provider
        assert result.client_id == "test-client-id"

    def test_build_provider_creates_new_provider_when_no_match(self):
        """When no registered provider matches, _build_provider builds a new
        one with empty client_id (standard MCP dynamic registration path)."""
        discovery = self._make_discovery()
        auth_meta = {
            "authorization_endpoint": "https://auth.example.com/oauth/authorize",
            "token_endpoint": "https://auth.example.com/oauth/token",
            "code_challenge_methods_supported": ["S256"],
        }

        with patch("svc_infra.connect.mcp_discovery._registry") as mock_reg:
            mock_reg.list.return_value = []
            result = discovery._build_provider("https://mcp.example.com/", auth_meta)

        assert result.client_id == ""
        assert result.name == "mcp-mcp.example.com"

    @pytest.mark.asyncio
    async def test_discover_uses_registry_shortcut_for_providers_without_rfc8414(self):
        """discover() skips the RFC 8414 metadata fetch when a registered
        provider's authorize_url starts with the extracted auth_server_url.
        This is the critical path for GitHub, which does not publish
        /.well-known/oauth-authorization-server."""
        from pydantic import SecretStr as _SecretStr

        from svc_infra.connect.registry import OAuthProvider

        github_provider = OAuthProvider(
            name="github",
            client_id="real-client-id",
            client_secret=_SecretStr("real-client-secret"),
            authorize_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            default_scopes=["repo"],
        )

        resource_meta_response = _mock_http_response(
            200,
            {"authorization_servers": ["https://github.com/login/oauth"]},
        )
        www_auth_header = 'Bearer resource_metadata="https://api.githubcopilot.com/.well-known/oauth-protected-resource/mcp/"'
        probe_401_response = _mock_http_response(
            401,
            {},
            {"www-authenticate": www_auth_header, "content-type": "text/plain"},
        )

        discovery = self._make_discovery()

        async def fake_post(*args, **kwargs):
            return probe_401_response

        async def fake_get(url, **kwargs):
            return resource_meta_response

        with (
            patch("svc_infra.connect.mcp_discovery._registry") as mock_reg,
            patch.object(
                discovery,
                "_probe_resource_metadata_url",
                return_value="https://api.githubcopilot.com/.well-known/oauth-protected-resource/mcp/",
            ),
            patch.object(
                discovery,
                "_fetch_resource_metadata",
                return_value={"authorization_servers": ["https://github.com/login/oauth"]},
            ),
        ):
            mock_reg.list.return_value = [github_provider]
            # _fetch_auth_server_metadata must NOT be called for this path
            with patch.object(
                discovery,
                "_fetch_auth_server_metadata",
                side_effect=AssertionError("should not be called"),
            ):
                result = await discovery.discover("https://api.githubcopilot.com/mcp/")

        assert result is github_provider
        assert result.client_id == "real-client-id"


class TestWellKnownFallback:
    """Tests for the .well-known/oauth-protected-resource fallback."""

    @pytest.mark.asyncio
    async def test_wellknown_fallback_when_server_returns_404(self):
        """OAuth is detected when the server returns 404 (not 401) but publishes .well-known."""
        from svc_infra.connect.mcp_discovery import MCPOAuthDiscovery

        discovery = MCPOAuthDiscovery()

        # Server returns 404 for POST (like Notion)
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 404
        mock_post_resp.headers = {}

        # .well-known returns valid metadata
        mock_wellknown_resp = MagicMock()
        mock_wellknown_resp.status_code = 200
        mock_wellknown_resp.json.return_value = {
            "resource": "https://mcp.notion.com",
            "authorization_servers": ["https://mcp.notion.com"],
        }

        with patch("svc_infra.connect.mcp_discovery.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.post.return_value = mock_post_resp
            client_instance.get.return_value = mock_wellknown_resp
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await discovery.is_mcp_oauth_supported("https://mcp.notion.com/")

        assert result is True

    @pytest.mark.asyncio
    async def test_wellknown_fallback_returns_false_when_no_metadata(self):
        """OAuth is not detected when .well-known also fails."""
        from svc_infra.connect.mcp_discovery import MCPOAuthDiscovery

        discovery = MCPOAuthDiscovery()

        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 404
        mock_post_resp.headers = {}

        mock_wellknown_resp = MagicMock()
        mock_wellknown_resp.status_code = 404

        with patch("svc_infra.connect.mcp_discovery.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.post.return_value = mock_post_resp
            client_instance.get.return_value = mock_wellknown_resp
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await discovery.is_mcp_oauth_supported("https://mcp.example.com/")

        assert result is False


class TestDynamicClientRegistration:
    """Tests for RFC 7591 dynamic client registration."""

    @pytest.mark.asyncio
    async def test_dynamic_registration_populates_client_id(self):
        """When auth server has registration_endpoint, discover() registers dynamically."""
        from svc_infra.connect.mcp_discovery import _DISCOVERY_CACHE, MCPOAuthDiscovery

        _DISCOVERY_CACHE.clear()
        discovery = MCPOAuthDiscovery()

        resource_meta = {
            "authorization_servers": ["https://mcp.notion.com"],
        }
        auth_meta = {
            "authorization_endpoint": "https://mcp.notion.com/authorize",
            "token_endpoint": "https://mcp.notion.com/token",
            "registration_endpoint": "https://mcp.notion.com/register",
            "code_challenge_methods_supported": ["S256"],
        }
        registration_response = {
            "client_id": "dynamic-client-abc",
            "client_secret": "",
        }

        with (
            patch.object(
                discovery,
                "_fetch_resource_metadata",
                new_callable=AsyncMock,
                return_value=resource_meta,
            ),
            patch.object(
                discovery,
                "_fetch_auth_server_metadata",
                new_callable=AsyncMock,
                return_value=auth_meta,
            ),
            patch("svc_infra.connect.mcp_discovery.httpx.AsyncClient") as MockClient,
        ):
            mock_resp = MagicMock()
            mock_resp.status_code = 201
            mock_resp.json.return_value = registration_response
            client_instance = AsyncMock()
            client_instance.post.return_value = mock_resp
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            provider = await discovery.discover(
                "https://mcp.notion.com/",
                api_base="http://127.0.0.1:8765",
            )

        assert provider.client_id == "dynamic-client-abc"
        assert provider.name == "mcp-mcp.notion.com"
        assert provider.authorize_url == "https://mcp.notion.com/authorize"

    @pytest.mark.asyncio
    async def test_no_registration_without_api_base(self):
        """Without api_base, discover() skips dynamic registration."""
        from svc_infra.connect.mcp_discovery import _DISCOVERY_CACHE, MCPOAuthDiscovery

        _DISCOVERY_CACHE.clear()
        discovery = MCPOAuthDiscovery()

        resource_meta = {"authorization_servers": ["https://mcp.notion.com"]}
        auth_meta = {
            "authorization_endpoint": "https://mcp.notion.com/authorize",
            "token_endpoint": "https://mcp.notion.com/token",
            "registration_endpoint": "https://mcp.notion.com/register",
        }

        with (
            patch.object(
                discovery,
                "_fetch_resource_metadata",
                new_callable=AsyncMock,
                return_value=resource_meta,
            ),
            patch.object(
                discovery,
                "_fetch_auth_server_metadata",
                new_callable=AsyncMock,
                return_value=auth_meta,
            ),
        ):
            provider = await discovery.discover("https://mcp.notion.com/")

        assert provider.client_id == ""  # no registration attempted


class TestOriginUrl:
    """Tests for _origin_url — RFC 9728 well-known endpoints live at origin level."""

    def test_url_without_path(self):
        from svc_infra.connect.mcp_discovery import _origin_url

        assert _origin_url("https://mcp.example.com") == "https://mcp.example.com"

    def test_url_with_path(self):
        from svc_infra.connect.mcp_discovery import _origin_url

        assert _origin_url("https://mcp.notion.com/mcp") == "https://mcp.notion.com"

    def test_url_with_trailing_slash(self):
        from svc_infra.connect.mcp_discovery import _origin_url

        assert _origin_url("https://mcp.example.com/") == "https://mcp.example.com"

    def test_url_with_port(self):
        from svc_infra.connect.mcp_discovery import _origin_url

        assert _origin_url("https://localhost:8080/mcp/v1") == "https://localhost:8080"

    def test_url_with_deep_path(self):
        from svc_infra.connect.mcp_discovery import _origin_url

        assert _origin_url("https://api.example.com/v2/mcp/endpoint") == "https://api.example.com"


class TestOriginUrlInWellKnown:
    """Verify well-known URL construction uses origin, not full path."""

    @pytest.mark.asyncio
    async def test_probe_falls_back_to_origin_wellknown_for_path_url(self):
        """For https://mcp.notion.com/mcp, default should be
        https://mcp.notion.com/.well-known/..., NOT .../mcp/.well-known/..."""
        mock_resp = _mock_http_response(200, {}, headers={})
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        discovery = MCPOAuthDiscovery()
        with patch("svc_infra.connect.mcp_discovery.httpx.AsyncClient", return_value=mock_client):
            url = await discovery._probe_resource_metadata_url("https://mcp.notion.com/mcp")

        assert url == "https://mcp.notion.com/.well-known/oauth-protected-resource"

    @pytest.mark.asyncio
    async def test_wellknown_check_uses_origin_for_path_url(self):
        """_check_wellknown_resource_metadata for a path URL hits origin."""
        mock_wellknown_resp = MagicMock()
        mock_wellknown_resp.status_code = 200
        mock_wellknown_resp.json.return_value = {
            "resource": "https://mcp.notion.com",
            "authorization_servers": ["https://mcp.notion.com"],
        }

        with patch("svc_infra.connect.mcp_discovery.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.get.return_value = mock_wellknown_resp
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            discovery = MCPOAuthDiscovery()
            result = await discovery._check_wellknown_resource_metadata(
                "https://mcp.notion.com/mcp"
            )

        assert result is True
        # Verify the GET was to the origin, not the path
        call_args = client_instance.get.call_args
        assert call_args[0][0] == "https://mcp.notion.com/.well-known/oauth-protected-resource"

    @pytest.mark.asyncio
    async def test_is_mcp_oauth_supported_401_without_resource_metadata(self):
        """401 + Bearer but no resource_metadata field falls through to well-known check."""
        mock_post_resp = _mock_http_response(
            401,
            {},
            headers={"www-authenticate": 'Bearer realm="OAuth", error="invalid_token"'},
        )
        mock_wellknown_resp = MagicMock()
        mock_wellknown_resp.status_code = 200
        mock_wellknown_resp.json.return_value = {
            "resource": "https://mcp.notion.com",
            "authorization_servers": ["https://mcp.notion.com"],
        }

        with patch("svc_infra.connect.mcp_discovery.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.post.return_value = mock_post_resp
            client_instance.get.return_value = mock_wellknown_resp
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            discovery = MCPOAuthDiscovery()
            result = await discovery.is_mcp_oauth_supported("https://mcp.notion.com/mcp")

        assert result is True
