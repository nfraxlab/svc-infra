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

        assert provider.name == "mcp:https://mcp.example.com"
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
        with patch("svc_infra.connect.mcp_discovery.httpx.AsyncClient", return_value=mock_client):
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
        with patch("svc_infra.connect.mcp_discovery.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(MCPOAuthNotSupported, match="resource metadata"):
                await discovery._fetch_resource_metadata("https://mcp.example.com")
