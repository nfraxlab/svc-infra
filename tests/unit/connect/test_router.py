from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from cryptography.fernet import Fernet
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from svc_infra.connect.registry import ConnectRegistry, OAuthProvider
from svc_infra.connect.settings import ConnectSettings
from svc_infra.connect.state import set_connect_state
from svc_infra.connect.token_manager import ConnectionTokenManager

_KEY = Fernet.generate_key().decode()
_USER_ID = uuid4()
_CONN_ID = uuid4()


def _make_provider() -> OAuthProvider:
    return OAuthProvider(
        name="github",
        client_id="cid",
        client_secret="csecret",
        authorize_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        default_scopes=["repo"],
    )


@pytest_asyncio.fixture
async def connect_app(mocker):
    """FastAPI app with connect router mounted and all deps mocked."""
    from svc_infra.api.fastapi.auth.security import _current_principal
    from svc_infra.api.fastapi.db.sql.session import get_session
    from svc_infra.connect.router import connect_router

    app = FastAPI()

    # ---- mock principal ----------------------------------------
    mock_user = mocker.Mock()
    mock_user.id = _USER_ID
    mock_principal = mocker.Mock()
    mock_principal.user = mock_user

    async def _mock_principal():
        return mock_principal

    app.dependency_overrides[_current_principal] = _mock_principal

    # ---- mock db session ----------------------------------------
    from tests.unit.utils.test_helpers import MockDatabaseSession

    mock_db = MockDatabaseSession()

    async def _mock_session():
        return mock_db

    app.dependency_overrides[get_session] = _mock_session

    # ---- connect state ------------------------------------------
    reg = ConnectRegistry()
    reg.register(_make_provider())

    settings = ConnectSettings(
        connect_token_encryption_key=_KEY,
        connect_api_base="http://testserver",
        connect_default_redirect_uri="https://app.example.com/callback",
        connect_state_ttl_seconds=600,
        connect_redirect_allow_hosts="app.example.com",
    )
    token_manager = ConnectionTokenManager(_KEY, registry=reg)
    set_connect_state(settings, token_manager)

    # patch registry used inside router
    with patch("svc_infra.connect.router._default_registry", reg):
        app.include_router(connect_router, prefix="/connect")
        yield app, mock_db, token_manager, reg


@pytest_asyncio.fixture
async def connect_client(connect_app):
    app, mock_db, token_manager, reg = connect_app
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client, mock_db, token_manager, reg


@pytest.mark.asyncio
class TestAuthorizeEndpoint:
    async def test_returns_authorize_url(self, connect_client):
        client, _, _, _ = connect_client
        resp = await client.get(
            "/connect/authorize",
            params={
                "provider": "github",
                "connection_id": str(_CONN_ID),
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "authorize_url" in body
        assert "github.com/login/oauth/authorize" in body["authorize_url"]
        assert "code_challenge" in body["authorize_url"]

    async def test_returns_404_for_unknown_provider(self, connect_client):
        client, _, _, _ = connect_client
        resp = await client.get(
            "/connect/authorize",
            params={
                "provider": "unknown_provider_xyz",
                "connection_id": str(_CONN_ID),
            },
        )
        assert resp.status_code == 404

    async def test_returns_400_when_no_provider_or_mcp_url(self, connect_client):
        client, _, _, _ = connect_client
        resp = await client.get(
            "/connect/authorize",
            params={"connection_id": str(_CONN_ID)},
        )
        assert resp.status_code == 400

    async def test_mcp_discovery_path(self, connect_client):
        """mcp_server_url triggers MCPOAuthDiscovery.discover() and resolves provider."""
        client, _, _, reg = connect_client

        mock_provider = _make_provider()
        mock_provider = mock_provider.model_copy(update={"name": "mcp:https://mcp.example.com"})

        with patch("svc_infra.connect.router._mcp_discovery") as mock_disc:
            mock_disc.discover = AsyncMock(return_value=mock_provider)
            resp = await client.get(
                "/connect/authorize",
                params={
                    "mcp_server_url": "https://mcp.example.com",
                    "connection_id": str(_CONN_ID),
                },
            )

        assert resp.status_code == 200
        mock_disc.discover.assert_awaited_once()

    async def test_mcp_discovery_not_supported_returns_422(self, connect_client):
        from svc_infra.connect.mcp_discovery import MCPOAuthNotSupported

        client, _, _, _ = connect_client
        with patch("svc_infra.connect.router._mcp_discovery") as mock_disc:
            mock_disc.discover = AsyncMock(side_effect=MCPOAuthNotSupported("no oauth"))
            resp = await client.get(
                "/connect/authorize",
                params={
                    "mcp_server_url": "https://mcp.example.com",
                    "connection_id": str(_CONN_ID),
                },
            )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestCallbackEndpoint:
    def _make_oauth_state(self, manager: ConnectionTokenManager, provider: str = "github"):
        from svc_infra.connect.models import OAuthState

        state = MagicMock(spec=OAuthState)
        state.state = "valid_state"
        state.provider = provider
        state.pkce_verifier = "verifier"
        state.user_id = _USER_ID
        state.connection_id = _CONN_ID
        state.redirect_uri = "http://app.example.com/callback"
        state.expires_at = datetime.now(UTC) + timedelta(seconds=600)
        return state

    async def test_callback_success_redirects(self, connect_client):
        client, mock_db, token_manager, _ = connect_client
        oauth_state = self._make_oauth_state(token_manager)

        # Patch db.execute to return the oauth state
        async def _execute(_stmt):
            result = MagicMock()
            scalars = MagicMock()
            scalars.first = MagicMock(return_value=oauth_state)
            result.scalars = MagicMock(return_value=scalars)
            return result

        mock_db.execute = _execute

        with (
            patch(
                "svc_infra.connect.router.exchange_code",
                new_callable=AsyncMock,
                return_value={"access_token": "tok", "token_type": "Bearer"},
            ),
            patch.object(token_manager, "store", new_callable=AsyncMock, return_value=MagicMock()),
        ):
            resp = await client.get(
                "/connect/callback/github",
                params={"code": "auth_code_123", "state": "valid_state"},
                follow_redirects=False,
            )

        assert resp.status_code == 302
        assert "success=true" in resp.headers["location"]

    async def test_callback_invalid_state_redirects_with_error(self, connect_client):
        client, mock_db, _, _ = connect_client

        # Return None for the state query
        async def _execute(_stmt):
            result = MagicMock()
            scalars = MagicMock()
            scalars.first = MagicMock(return_value=None)
            result.scalars = MagicMock(return_value=scalars)
            return result

        mock_db.execute = _execute

        resp = await client.get(
            "/connect/callback/github",
            params={"code": "code", "state": "invalid_state"},
            follow_redirects=False,
        )

        assert resp.status_code == 302
        assert "error=invalid_state" in resp.headers["location"]

    async def test_callback_with_error_param_redirects(self, connect_client):
        client, mock_db, token_manager, _ = connect_client
        oauth_state = self._make_oauth_state(token_manager)

        async def _execute(_stmt):
            result = MagicMock()
            scalars = MagicMock()
            scalars.first = MagicMock(return_value=oauth_state)
            result.scalars = MagicMock(return_value=scalars)
            return result

        mock_db.execute = _execute

        resp = await client.get(
            "/connect/callback/github",
            params={"code": "code", "state": "valid_state", "error": "access_denied"},
            follow_redirects=False,
        )

        assert resp.status_code == 302
        assert "access_denied" in resp.headers["location"]

    async def test_callback_exchange_failure_redirects_with_error(self, connect_client):
        from svc_infra.connect.pkce import OAuthExchangeError

        client, mock_db, token_manager, _ = connect_client
        oauth_state = self._make_oauth_state(token_manager)

        async def _execute(_stmt):
            result = MagicMock()
            scalars = MagicMock()
            scalars.first = MagicMock(return_value=oauth_state)
            result.scalars = MagicMock(return_value=scalars)
            return result

        mock_db.execute = _execute

        with patch(
            "svc_infra.connect.router.exchange_code",
            new_callable=AsyncMock,
            side_effect=OAuthExchangeError("bad code"),
        ):
            resp = await client.get(
                "/connect/callback/github",
                params={"code": "bad", "state": "valid_state"},
                follow_redirects=False,
            )

        assert resp.status_code == 302
        assert "exchange_failed" in resp.headers["location"]


@pytest.mark.asyncio
class TestGetTokenEndpoint:
    def _make_token_row(self, manager: ConnectionTokenManager):
        from svc_infra.connect.models import ConnectionToken

        row = MagicMock(spec=ConnectionToken)
        row.id = uuid4()
        row.user_id = _USER_ID
        row.connection_id = _CONN_ID
        row.provider = "github"
        row.access_token = manager._encrypt("my_access_token")
        row.refresh_token = None
        row.expires_at = datetime.now(UTC) + timedelta(hours=2)
        return row

    async def test_returns_valid_token(self, connect_client):
        client, _, token_manager, _ = connect_client
        row = self._make_token_row(token_manager)

        with (
            patch.object(
                token_manager,
                "get_valid_token",
                new_callable=AsyncMock,
                return_value="my_access_token",
            ),
            patch.object(token_manager, "get", new_callable=AsyncMock, return_value=row),
        ):
            resp = await client.get(
                f"/connect/token/{_CONN_ID}",
                params={"provider": "github"},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["token"] == "my_access_token"
        assert "expires_at" in body

    async def test_returns_404_when_no_token_stored(self, connect_client):
        client, _, token_manager, _ = connect_client

        with (
            patch.object(
                token_manager, "get_valid_token", new_callable=AsyncMock, return_value=None
            ),
            patch.object(token_manager, "get", new_callable=AsyncMock, return_value=None),
        ):
            resp = await client.get(
                f"/connect/token/{_CONN_ID}",
                params={"provider": "github"},
            )

        assert resp.status_code == 404

    async def test_returns_502_when_token_exists_but_refresh_failed(self, connect_client):
        client, _, token_manager, _ = connect_client
        row = self._make_token_row(token_manager)

        with (
            patch.object(
                token_manager, "get_valid_token", new_callable=AsyncMock, return_value=None
            ),
            patch.object(token_manager, "get", new_callable=AsyncMock, return_value=row),
        ):
            resp = await client.get(
                f"/connect/token/{_CONN_ID}",
                params={"provider": "github"},
            )

        assert resp.status_code == 502
