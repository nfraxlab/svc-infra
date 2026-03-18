from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from svc_infra.api.fastapi.auth.security import Identity
from svc_infra.api.fastapi.db.sql.session import SqlSessionDep
from svc_infra.connect.mcp_discovery import MCPOAuthDiscovery, MCPOAuthNotSupported
from svc_infra.connect.models import OAuthState
from svc_infra.connect.pkce import (
    OAuthExchangeError,
    build_authorize_url,
    exchange_code,
    generate_pkce_pair,
    generate_state,
    validate_redirect,
)
from svc_infra.connect.registry import registry as _default_registry
from svc_infra.connect.state import get_connect_settings, get_connect_token_manager

logger = logging.getLogger(__name__)
_mcp_discovery = MCPOAuthDiscovery()

connect_router = APIRouter(tags=["connect"])


@connect_router.get("/authorize")
async def authorize(
    request: Request,
    db: SqlSessionDep,
    principal: Identity,
    connection_id: UUID = Query(..., description="Connection ID to associate with the token"),
    provider: str | None = Query(None, description="Static provider name (e.g. github)"),
    mcp_server_url: str | None = Query(None, description="MCP server URL for dynamic discovery"),
    redirect_uri: str | None = Query(None, description="URI to redirect to after OAuth completes"),
    scopes: str | None = Query(None, description="Space-separated scope override"),
) -> dict:
    """Initiate an OAuth authorization flow.

    Returns {"authorize_url": "..."} — the client opens this URL. The server
    does not redirect directly to avoid CORS issues with API-first applications.
    """
    settings = get_connect_settings()

    if provider is None and mcp_server_url is None:
        raise HTTPException(400, "Either 'provider' or 'mcp_server_url' is required")

    effective_redirect = redirect_uri or settings.connect_default_redirect_uri
    if effective_redirect:
        require_https = not effective_redirect.startswith(("pulse-app://", "http://localhost"))
        validate_redirect(
            effective_redirect,
            settings.allowed_hosts(),
            require_https=require_https,
        )

    if mcp_server_url is not None:
        try:
            resolved_provider = await _mcp_discovery.discover(
                mcp_server_url, api_base=settings.connect_api_base or None
            )
            _default_registry.register(resolved_provider)
            provider = resolved_provider.name
        except MCPOAuthNotSupported as exc:
            raise HTTPException(422, f"MCP OAuth not supported by this server: {exc}") from exc
    else:
        _rp = _default_registry.get(provider)  # type: ignore[arg-type]
        if _rp is None:
            raise HTTPException(404, f"Provider '{provider}' not registered")
        resolved_provider = _rp

    pkce_verifier, pkce_challenge = generate_pkce_pair()
    state_value = generate_state()
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.connect_state_ttl_seconds)

    oauth_state = OAuthState(
        state=state_value,
        pkce_verifier=pkce_verifier,
        provider=provider,
        connection_id=connection_id,
        user_id=principal.user.id,
        redirect_uri=effective_redirect,
        expires_at=expires_at,
    )
    db.add(oauth_state)
    await db.flush()

    scope_list = scopes.split() if scopes else None
    return {
        "authorize_url": build_authorize_url(
            resolved_provider,
            state=state_value,
            pkce_challenge=pkce_challenge,
            redirect_uri=f"{settings.connect_api_base}/connect/callback/{provider}",
            scopes=scope_list,
        )
    }


@connect_router.get("/callback/{provider}")
async def callback(
    request: Request,
    provider: str,
    db: SqlSessionDep,
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    error_description: str | None = Query(None),
) -> RedirectResponse:
    """OAuth callback endpoint. Public — identity is carried via the state param.

    Validates state, exchanges code, stores token, then redirects to redirect_uri.
    """
    settings = get_connect_settings()
    token_manager = get_connect_token_manager()
    fallback_redirect = settings.connect_default_redirect_uri

    logger.info(
        "OAuth callback received: provider=%s query=%s",
        provider,
        dict(request.query_params),
    )

    if error:
        logger.warning(
            "OAuth callback error from provider=%s: %s (%s)",
            provider,
            error,
            error_description,
        )
        return RedirectResponse(url=f"{fallback_redirect}?error={error}", status_code=302)

    if not code or not state:
        logger.error(
            "OAuth callback missing required params: provider=%s code=%s state=%s",
            provider,
            bool(code),
            bool(state),
        )
        return RedirectResponse(url=f"{fallback_redirect}?error=missing_params", status_code=302)

    from sqlalchemy import and_, select

    result = await db.execute(
        select(OAuthState).where(
            and_(
                OAuthState.state == state,
                OAuthState.provider == provider,
                OAuthState.expires_at > datetime.now(UTC),
            )
        )
    )
    oauth_state = result.scalars().first()

    if oauth_state is None:
        logger.warning("OAuth callback: no valid state found for provider=%s", provider)
        return RedirectResponse(
            url=f"{fallback_redirect}?error=invalid_state",
            status_code=302,
        )

    fallback_redirect = oauth_state.redirect_uri or fallback_redirect

    resolved_provider = _default_registry.get(provider)
    if resolved_provider is None:
        # Provider not in registry — attempt re-discovery for dynamically
        # registered MCP providers that may have been lost on restart.
        logger.warning(
            "OAuth callback: provider '%s' not in registry, attempting re-discovery",
            provider,
        )
        if provider.startswith("mcp-") and settings.connect_api_base:
            mcp_url = "https://" + provider.removeprefix("mcp-")
            try:
                resolved_provider = await _mcp_discovery.discover(
                    mcp_url, api_base=settings.connect_api_base
                )
                _default_registry.register(resolved_provider)
                logger.info("OAuth callback: re-discovered provider '%s'", provider)
            except MCPOAuthNotSupported:
                logger.error("OAuth callback: re-discovery failed for '%s'", provider)

    if resolved_provider is None:
        logger.error("OAuth callback: provider '%s' not found after re-discovery", provider)
        await db.delete(oauth_state)
        await db.flush()
        return RedirectResponse(
            url=f"{fallback_redirect}?error=provider_not_found",
            status_code=302,
        )

    try:
        token_response = await exchange_code(
            resolved_provider,
            code=code,
            pkce_verifier=oauth_state.pkce_verifier,
            redirect_uri=f"{settings.connect_api_base}/connect/callback/{provider}",
        )
    except OAuthExchangeError as exc:
        logger.error("OAuth code exchange failed for provider=%s: %s", provider, exc)
        await db.delete(oauth_state)
        await db.flush()
        return RedirectResponse(url=f"{fallback_redirect}?error=exchange_failed", status_code=302)

    connection_id = oauth_state.connection_id
    user_id = oauth_state.user_id
    assert connection_id is not None

    logger.info(
        "OAuth token exchange succeeded: provider=%s connection_id=%s",
        provider,
        connection_id,
    )

    await db.delete(oauth_state)
    await token_manager.store(
        db,
        user_id=user_id,
        connection_id=connection_id,
        provider=provider,
        token_response=token_response,
    )
    await db.flush()

    return RedirectResponse(
        url=f"{fallback_redirect}?success=true&connection_id={connection_id}",
        status_code=302,
    )


@connect_router.get("/token/{connection_id}")
async def get_token(
    connection_id: UUID,
    db: SqlSessionDep,
    principal: Identity,
    provider: str = Query(..., description="Provider name"),
) -> dict:
    """Return a valid access token for the given connection.

    Returns 404 if no token is stored; 502 if refresh fails.
    """
    token_manager = get_connect_token_manager()
    token = await token_manager.get_valid_token(
        db,
        connection_id=connection_id,
        user_id=principal.user.id,
        provider=provider,
    )

    if token is None:
        row = await token_manager.get(
            db,
            connection_id=connection_id,
            user_id=principal.user.id,
            provider=provider,
        )
        if row is None:
            raise HTTPException(404, "No token stored for this connection")
        raise HTTPException(502, "Token refresh failed")

    row = await token_manager.get(
        db,
        connection_id=connection_id,
        user_id=principal.user.id,
        provider=provider,
    )
    expires_at_str = row.expires_at.isoformat() if row and row.expires_at else None
    return {"token": token, "expires_at": expires_at_str}
