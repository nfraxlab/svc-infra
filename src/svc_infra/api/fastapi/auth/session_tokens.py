from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi_users.authentication import Strategy
from sqlalchemy import select

from svc_infra.api.fastapi.auth._cookies import compute_cookie_params
from svc_infra.api.fastapi.auth.settings import get_auth_settings
from svc_infra.security.models import RefreshToken, hash_refresh_token
from svc_infra.security.session import DEFAULT_REFRESH_TTL_MINUTES, rotate_session_refresh


def set_auth_cookies(
    response: Response,
    request: Request,
    *,
    access_token: str,
    refresh_token: str | None = None,
) -> None:
    st = get_auth_settings()

    auth_params = compute_cookie_params(request, name=st.auth_cookie_name)
    response.set_cookie(**auth_params, value=access_token)

    if refresh_token:
        refresh_params = compute_cookie_params(request, name=st.session_cookie_name)
        refresh_params["max_age"] = DEFAULT_REFRESH_TTL_MINUTES * 60
        response.set_cookie(**refresh_params, value=refresh_token)


def build_session_token_response(
    request: Request,
    *,
    access_token: str,
    refresh_token: str | None = None,
) -> JSONResponse:
    content: dict[str, Any] = {
        "access_token": access_token,
        "token_type": "bearer",
    }
    if refresh_token:
        content["refresh_token"] = refresh_token

    response = JSONResponse(content)
    set_auth_cookies(
        response,
        request,
        access_token=access_token,
        refresh_token=refresh_token,
    )
    return response


def refresh_token_from_request(
    request: Request, payload: dict[str, Any] | None = None
) -> str | None:
    candidate = payload.get("refresh_token") if payload else None
    if isinstance(candidate, str):
        trimmed = candidate.strip()
        if trimmed:
            return trimmed

    st = get_auth_settings()
    cookie_value = (request.cookies.get(st.session_cookie_name) or "").strip()
    return cookie_value or None


async def rotate_refresh_session(
    *,
    request: Request,
    session: Any,
    user_model: type,
    strategy: Strategy[Any, Any],
    refresh_token: str,
) -> tuple[Any, JSONResponse]:
    token_hash = hash_refresh_token(refresh_token)
    found: RefreshToken | None = (
        (await session.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash)))
        .scalars()
        .first()
    )
    expires_at = found.expires_at if found else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if not found or found.revoked_at or (expires_at and expires_at < datetime.now(UTC)):
        raise HTTPException(401, "invalid_refresh_token")

    user = await cast("Any", session).get(user_model, found.session.user_id)
    if not user:
        raise HTTPException(401, "invalid_refresh_token")
    if not getattr(user, "is_active", True):
        raise HTTPException(401, "account_disabled")

    new_refresh_token, _ = await rotate_session_refresh(session, current=found)
    await session.commit()

    access_token = await strategy.write_token(user)
    response = build_session_token_response(
        request,
        access_token=access_token,
        refresh_token=new_refresh_token,
    )
    return user, response
