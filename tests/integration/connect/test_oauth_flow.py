"""Integration tests for svc_infra.connect OAuth flow.

These tests verify the full authorize → callback → token retrieval cycle.
The OAuth provider HTTP calls are mocked; all other logic runs against real
in-memory SQLite via aiosqlite so model/schema correctness is validated end-to-end.

Run with: pytest tests/integration/connect/ -v -m integration
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from cryptography.fernet import Fernet
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Column, Table
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from svc_infra.connect.models import ConnectionToken, OAuthState
from svc_infra.connect.registry import ConnectRegistry, OAuthProvider
from svc_infra.connect.settings import ConnectSettings
from svc_infra.connect.state import set_connect_state
from svc_infra.connect.token_manager import ConnectionTokenManager
from svc_infra.db.sql.base import ModelBase
from svc_infra.db.sql.types import GUID

# auth_sessions (and connect models) have FK → users.id; svc-infra itself does not
# define a users model (that belongs to the app). Registering a minimal stub here
# ensures ModelBase.metadata.create_all can resolve the FK reference in SQLite.
if "users" not in ModelBase.metadata.tables:
    Table("users", ModelBase.metadata, Column("id", GUID(), primary_key=True))

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
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(ModelBase.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def integration_app(mocker, session_factory):
    from svc_infra.api.fastapi.auth.security import _current_principal
    from svc_infra.api.fastapi.db.sql.session import get_session
    from svc_infra.connect.router import connect_router

    app = FastAPI()

    mock_user = mocker.Mock()
    mock_user.id = _USER_ID
    mock_principal = mocker.Mock()
    mock_principal.user = mock_user

    async def _mock_principal():
        return mock_principal

    app.dependency_overrides[_current_principal] = _mock_principal

    async def _get_db():
        async with session_factory() as db:
            yield db
            await db.commit()

    app.dependency_overrides[get_session] = _get_db

    reg = ConnectRegistry()
    reg.register(_make_provider())

    settings = ConnectSettings(
        connect_token_encryption_key=_KEY,
        connect_api_base="http://testserver",
        connect_default_redirect_uri="https://app.example.com/done",
        connect_state_ttl_seconds=600,
        connect_redirect_allow_hosts="app.example.com",
    )
    token_manager = ConnectionTokenManager(_KEY, registry=reg)
    set_connect_state(settings, token_manager)

    with patch("svc_infra.connect.router._default_registry", reg):
        app.include_router(connect_router, prefix="/connect")
        yield app, session_factory, token_manager, reg


@pytest_asyncio.fixture
async def integration_client(integration_app):
    app, session_factory, token_manager, reg = integration_app
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client, session_factory, token_manager, reg


@pytest.mark.integration
@pytest.mark.asyncio
class TestFullOAuthFlow:
    async def test_authorize_returns_url(self, integration_client):
        client, _, _, _ = integration_client
        resp = await client.get(
            "/connect/authorize",
            params={"provider": "github", "connection_id": str(_CONN_ID)},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "authorize_url" in body
        assert "github.com" in body["authorize_url"]

    async def test_authorize_persists_oauth_state(self, integration_client):
        """OAuthState row is written to the DB after /authorize is called."""
        client, session_factory, _, _ = integration_client
        await client.get(
            "/connect/authorize",
            params={"provider": "github", "connection_id": str(_CONN_ID)},
        )

        async with session_factory() as db:
            from sqlalchemy import select

            result = await db.execute(select(OAuthState).where(OAuthState.provider == "github"))
            rows = result.scalars().all()

        assert len(rows) >= 1

    async def test_full_callback_stores_token(self, integration_client):
        """Full authorize → callback cycle results in a ConnectionToken row."""
        client, session_factory, token_manager, _ = integration_client

        # Initiate authorize to create an OAuthState row
        resp = await client.get(
            "/connect/authorize",
            params={"provider": "github", "connection_id": str(_CONN_ID)},
        )
        assert resp.status_code == 200

        # Fetch the state value from the DB
        async with session_factory() as db:
            from sqlalchemy import select

            result = await db.execute(
                select(OAuthState)
                .where(OAuthState.provider == "github")
                .order_by(OAuthState.created_at.desc())
            )
            oauth_state = result.scalars().first()
        assert oauth_state is not None

        # Simulate callback from GitHub
        token_resp = {"access_token": "gh_tok_abc123", "token_type": "Bearer", "scope": "repo"}
        with patch(
            "svc_infra.connect.router.exchange_code",
            new_callable=AsyncMock,
            return_value=token_resp,
        ):
            cb_resp = await client.get(
                "/connect/callback/github",
                params={"code": "auth_code", "state": oauth_state.state},
                follow_redirects=False,
            )

        assert cb_resp.status_code == 302
        assert "success=true" in cb_resp.headers["location"]

        # Verify the token was persisted and encrypted
        async with session_factory() as db:
            from sqlalchemy import select

            result = await db.execute(
                select(ConnectionToken).where(ConnectionToken.connection_id == _CONN_ID)
            )
            token_row = result.scalars().first()

        assert token_row is not None
        assert token_row.access_token != "gh_tok_abc123"  # Must be encrypted
        assert token_manager._decrypt(token_row.access_token) == "gh_tok_abc123"

    async def test_token_endpoint_after_full_flow(self, integration_client):
        """After full flow, /token/{connection_id} returns the access token."""
        client, session_factory, token_manager, _ = integration_client

        await client.get(
            "/connect/authorize",
            params={"provider": "github", "connection_id": str(_CONN_ID)},
        )

        async with session_factory() as db:
            from sqlalchemy import select

            result = await db.execute(
                select(OAuthState)
                .where(OAuthState.provider == "github")
                .order_by(OAuthState.created_at.desc())
            )
            oauth_state = result.scalars().first()

        token_resp = {
            "access_token": "final_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        with patch(
            "svc_infra.connect.router.exchange_code",
            new_callable=AsyncMock,
            return_value=token_resp,
        ):
            await client.get(
                "/connect/callback/github",
                params={"code": "auth_code", "state": oauth_state.state},
                follow_redirects=False,
            )

        resp = await client.get(
            f"/connect/token/{_CONN_ID}",
            params={"provider": "github"},
        )
        assert resp.status_code == 200
        assert resp.json()["token"] == "final_token"
