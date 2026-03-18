from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from urllib.parse import urlencode, urlparse

import httpx
from fastapi import HTTPException

from svc_infra.connect.registry import OAuthProvider


class OAuthExchangeError(Exception):
    """Raised when an authorization code exchange fails."""


class OAuthRefreshError(Exception):
    """Raised when a token refresh fails."""


def generate_pkce_pair() -> tuple[str, str]:
    """Generate a PKCE (verifier, challenge) pair.

    Returns (verifier, challenge). verifier is stored server-side in OAuthState;
    challenge is sent to the provider authorization endpoint.
    Implementation moved verbatim from oauth_router._gen_pkce_pair().
    """
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def generate_state() -> str:
    """Generate a 32-byte URL-safe random state value."""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()


def validate_redirect(
    url: str,
    allow_hosts: list[str],
    *,
    require_https: bool = True,
) -> None:
    """Validate a redirect URI against an allow-list of hosts.

    Raises HTTPException(400) on disallowed host or non-HTTPS when required.
    Implementation moved verbatim from oauth_router._validate_redirect().
    """
    p = urlparse(url)
    if not p.netloc:
        return
    # Skip host+https checks for non-http(s) custom schemes (e.g. pulse-app://).
    if p.scheme not in ("http", "https"):
        return
    hostname = p.hostname
    host_port = (hostname or "").lower() + (f":{p.port}" if p.port else "")
    allowed = {h.lower() for h in allow_hosts}
    if host_port not in allowed and (hostname or "").lower() not in allowed:
        raise HTTPException(400, "redirect_not_allowed")
    if require_https and p.scheme != "https":
        raise HTTPException(400, "https_required")


def coerce_expires_at(token: dict | None) -> datetime | None:
    """Normalise expires_at / expires_in fields from a provider token response.

    Handles both unix timestamp (expires_at) and relative-seconds (expires_in) formats.
    Millisecond timestamps (> 1e12) are automatically divided by 1000.
    Implementation moved verbatim from oauth_router._coerce_expires_at().
    """
    if not isinstance(token, dict):
        return None
    if token.get("expires_at") is not None:
        v = float(token["expires_at"])
        if v > 1e12:
            v /= 1000.0
        return datetime.fromtimestamp(v, tz=UTC)
    if token.get("expires_in") is not None:
        secs = int(token["expires_in"])
        return datetime.now(UTC) + timedelta(seconds=secs)
    return None


def build_authorize_url(
    provider: OAuthProvider,
    state: str,
    pkce_challenge: str,
    redirect_uri: str,
    scopes: list[str] | None = None,
    extra: dict[str, str] | None = None,
) -> str:
    """Construct the full OAuth authorization redirect URL."""
    effective_scopes = scopes if scopes is not None else provider.default_scopes
    params: dict[str, str] = {
        "client_id": provider.client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": " ".join(effective_scopes),
    }
    if provider.pkce_required:
        params["code_challenge"] = pkce_challenge
        params["code_challenge_method"] = "S256"
    params.update(provider.extra_authorize_params)
    if extra:
        params.update(extra)
    return f"{provider.authorize_url}?{urlencode(params)}"


async def exchange_code(
    provider: OAuthProvider,
    code: str,
    pkce_verifier: str,
    redirect_uri: str,
) -> dict:
    """Exchange an authorization code for tokens.

    Raises OAuthExchangeError on non-200 or error JSON from the provider.
    """
    payload: dict[str, str] = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": provider.client_id,
    }
    secret = provider.client_secret.get_secret_value()
    if secret:
        payload["client_secret"] = secret
    if provider.pkce_required:
        payload["code_verifier"] = pkce_verifier

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            provider.token_url,
            data=payload,
            headers={"Accept": "application/json"},
        )

    if response.status_code != 200:
        raise OAuthExchangeError(f"Token exchange failed: {response.status_code} {response.text}")

    data = response.json()
    if "error" in data:
        raise OAuthExchangeError(
            f"Token exchange error: {data['error']} — {data.get('error_description', '')}"
        )

    return cast(dict[str, Any], data)


async def exchange_refresh(
    provider: OAuthProvider,
    refresh_token_str: str,
) -> dict:
    """Refresh an access token using a refresh token grant.

    Raises OAuthRefreshError if the refresh token is absent, or the provider rejects the grant.
    """
    payload: dict[str, str] = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token_str,
        "client_id": provider.client_id,
    }
    secret = provider.client_secret.get_secret_value()
    if secret:
        payload["client_secret"] = secret

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            provider.token_url,
            data=payload,
            headers={"Accept": "application/json"},
        )

    if response.status_code != 200:
        raise OAuthRefreshError(f"Token refresh failed: {response.status_code} {response.text}")

    data = response.json()
    if "error" in data:
        raise OAuthRefreshError(
            f"Token refresh error: {data['error']} — {data.get('error_description', '')}"
        )

    if "access_token" not in data:
        raise OAuthRefreshError("No access_token in refresh response")

    return cast(dict[str, Any], data)
