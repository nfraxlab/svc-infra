from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import FastAPI
from fastapi_users.password import PasswordHelper
from httpx import ASGITransport, AsyncClient

import svc_infra.api.fastapi.auth.gaurd as guard_module
import svc_infra.api.fastapi.auth.session_tokens as session_tokens_module
import svc_infra.security.lockout as lockout_module
import svc_infra.security.session as session_module
from svc_infra.api.fastapi.auth.gaurd import auth_session_router
from svc_infra.api.fastapi.db.sql.session import get_session

_pwd = PasswordHelper()


async def _call(app: FastAPI, method: str, path: str, **kwargs):
    cookies = kwargs.pop("cookies", None)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        if cookies:
            client.cookies.update(cookies)
        return await client.request(method, path, **kwargs)


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        require_client_secret_on_password_login=False,
        auth_cookie_name="svc_auth",
        session_cookie_name="svc_session",
        session_cookie_secure=False,
        session_cookie_domain=None,
        session_cookie_samesite="lax",
        session_cookie_max_age_seconds=3600,
    )


def _build_login_app(mocker) -> tuple[FastAPI, AsyncMock, AsyncMock]:
    mocker.patch.object(
        guard_module,
        "get_auth_settings",
        return_value=_settings(),
    )
    mocker.patch.object(
        session_tokens_module,
        "get_auth_settings",
        return_value=_settings(),
    )
    mocker.patch.object(
        lockout_module,
        "get_lockout_status",
        AsyncMock(return_value=SimpleNamespace(locked=False, next_allowed_at=None)),
    )
    mocker.patch.object(lockout_module, "record_attempt", AsyncMock(return_value=None))
    issue_session = AsyncMock(return_value=("fresh-refresh-token", object()))
    mocker.patch.object(session_module, "issue_session_and_refresh", issue_session)
    mocker.patch.object(session_module, "lookup_ip_location", AsyncMock(return_value=None))

    user = SimpleNamespace(
        id="user-123",
        email="tester@example.com",
        is_active=True,
        is_verified=True,
        hashed_password=_pwd.hash("P@ssw0rd!1234"),
        tenant_id=None,
        last_login=None,
    )

    user_db = SimpleNamespace(
        get_by_email=AsyncMock(return_value=user),
        update=AsyncMock(return_value=user),
    )

    class DummyFastAPIUsers:
        async def get_user_manager(self):
            return SimpleNamespace(user_db=user_db)

    strategy = Mock()
    strategy.write_token = AsyncMock(return_value="fresh-access-token")

    auth_backend = Mock()

    def _get_strategy():
        return strategy

    auth_backend.get_strategy = _get_strategy

    router = auth_session_router(
        fapi=DummyFastAPIUsers(),
        auth_backend=auth_backend,
        user_model=SimpleNamespace,
        get_mfa_pre_writer=lambda: None,
        auth_policy=SimpleNamespace(should_require_mfa=AsyncMock(return_value=False)),
    )

    app = FastAPI()
    app.include_router(router)

    session = Mock()
    session.commit = AsyncMock(return_value=None)

    async def _session_override():
        return session

    app.dependency_overrides[get_session] = _session_override

    return app, issue_session, user_db.update


@pytest.mark.asyncio
async def test_password_login_returns_refresh_token_and_sets_cookie(mocker):
    app, issue_session, update_user = _build_login_app(mocker)

    response = await _call(
        app,
        "POST",
        "/login",
        data={"username": "tester@example.com", "password": "P@ssw0rd!1234"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "fresh-access-token",
        "refresh_token": "fresh-refresh-token",
        "token_type": "bearer",
    }
    assert response.cookies.get("svc_auth") == "fresh-access-token"
    assert response.cookies.get("svc_session") == "fresh-refresh-token"
    issue_session.assert_awaited_once()
    update_user.assert_awaited()


def _build_refresh_app(mocker) -> FastAPI:
    mocker.patch.object(
        guard_module,
        "get_auth_settings",
        return_value=_settings(),
    )
    mocker.patch.object(
        session_tokens_module,
        "get_auth_settings",
        return_value=_settings(),
    )
    mocker.patch.object(
        session_tokens_module,
        "rotate_session_refresh",
        AsyncMock(return_value=("rotated-refresh-token", object())),
    )

    strategy = Mock()
    strategy.write_token = AsyncMock(return_value="rotated-access-token")

    auth_backend = Mock()

    def _get_strategy():
        return strategy

    auth_backend.get_strategy = _get_strategy

    policy = SimpleNamespace(
        should_require_mfa=AsyncMock(return_value=False),
        on_token_refresh=AsyncMock(return_value=None),
    )

    router = auth_session_router(
        fapi=SimpleNamespace(get_user_manager=lambda: None),
        auth_backend=auth_backend,
        user_model=SimpleNamespace,
        get_mfa_pre_writer=lambda: None,
        auth_policy=policy,
    )

    app = FastAPI()
    app.include_router(router)

    user = SimpleNamespace(id="user-123", is_active=True)
    found = SimpleNamespace(
        revoked_at=None,
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
        session=SimpleNamespace(user_id="user-123"),
    )

    session = Mock()
    session.get = AsyncMock(return_value=user)
    session.commit = AsyncMock(return_value=None)
    session.execute = AsyncMock(
        return_value=SimpleNamespace(scalars=lambda: SimpleNamespace(first=lambda: found))
    )

    async def _session_override():
        return session

    app.dependency_overrides[get_session] = _session_override

    return app


@pytest.mark.asyncio
async def test_password_refresh_rotates_tokens_without_access_jwt(mocker):
    app = _build_refresh_app(mocker)

    response = await _call(
        app,
        "POST",
        "/refresh",
        json={"refresh_token": "current-refresh-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "rotated-access-token",
        "refresh_token": "rotated-refresh-token",
        "token_type": "bearer",
    }
    assert response.cookies.get("svc_auth") == "rotated-access-token"
    assert response.cookies.get("svc_session") == "rotated-refresh-token"
