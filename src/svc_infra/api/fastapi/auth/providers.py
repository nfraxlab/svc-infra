"""Auth provider registry — reads from the unified connect provider catalog.

svc_infra.connect is the single source of truth for OAuth provider definitions.
This module adapts login-capable providers into the authlib-compatible format
consumed by the svc_infra.auth OAuth router.

Unification model
-----------------
1. The connect provider catalog (_KNOWN in connect/providers/generic.py) lists
   60+ providers.  Providers with login_enabled=True are automatically surfaced
   for user authentication.
2. providers_from_settings() reads from the connect registry first, then falls
   back to the legacy AuthSettings credential fields so existing deployments
   that set AUTH_GITHUB_CLIENT_ID etc. continue to work unchanged.
3. A single env var set (e.g. GITHUB_CLIENT_ID + GITHUB_CLIENT_SECRET) powers
   BOTH workspace tool connections (svc_infra.connect) AND user login
   (svc_infra.auth) without any duplication.
"""

from __future__ import annotations

from typing import Any


def providers_from_settings(settings: Any) -> dict[str, dict[str, Any]]:
    """Return authlib-compatible OAuth provider config.

    Primary source: the global connect registry (providers with
    login_enabled=True are included automatically when their env vars are set).

    Fallback: AuthSettings credential fields (AUTH_GITHUB_CLIENT_ID etc.) for
    backward compatibility with existing deployments.
    """
    from svc_infra.connect.registry import registry

    result: dict[str, dict[str, Any]] = {}

    # 1. Read login-capable providers from the unified connect registry
    for provider in registry.list():
        if not provider.login_enabled:
            continue
        result[provider.name] = _to_auth_cfg(provider)

    # 2. Fallback to AuthSettings fields (backward compat — only adds missing ones)
    _apply_auth_settings_fallback(settings, result)

    return result


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------


def _login_scope_str(provider: Any) -> str:
    """Return the scope string to use during a user-login flow."""
    if getattr(provider, "oidc_discovery_url", None):
        return "openid email profile"
    kind = getattr(provider, "userinfo_kind", "standard")
    if kind == "oidc":
        return "openid email profile"
    if kind == "github":
        return "user:email"
    if kind == "linkedin":
        return "r_liteprofile r_emailaddress"
    # For "standard" providers: use the provider's own default scopes
    scopes = getattr(provider, "default_scopes", []) or []
    return " ".join(scopes)


def _to_auth_cfg(provider: Any) -> dict[str, Any]:
    """Convert an OAuthProvider to authlib-compatible login config."""
    cid: str = provider.client_id
    csec: str = provider.client_secret.get_secret_value()

    if getattr(provider, "oidc_discovery_url", None):
        return {
            "kind": "oidc",
            "issuer": provider.oidc_discovery_url.rstrip("/"),
            "client_id": cid,
            "client_secret": csec,
            "scope": "openid email profile",
        }

    kind = getattr(provider, "userinfo_kind", "standard")

    if kind == "github":
        return {
            "kind": "github",
            "authorize_url": provider.authorize_url,
            "access_token_url": provider.token_url,
            "api_base_url": "https://api.github.com/",
            "client_id": cid,
            "client_secret": csec,
            "scope": "user:email",
        }

    if kind == "linkedin":
        return {
            "kind": "linkedin",
            "authorize_url": provider.authorize_url,
            "access_token_url": provider.token_url,
            "api_base_url": "https://api.linkedin.com/v2/",
            "client_id": cid,
            "client_secret": csec,
            "scope": "r_liteprofile r_emailaddress",
        }

    # "standard" — generic OAuth2 with a userinfo endpoint (discord, twitter, etc.)
    return {
        "kind": "oauth2",
        "authorize_url": provider.authorize_url,
        "access_token_url": provider.token_url,
        "client_id": cid,
        "client_secret": csec,
        "scope": _login_scope_str(provider),
        "userinfo_url": getattr(provider, "userinfo_url", None),
    }


def _apply_auth_settings_fallback(settings: Any, result: dict[str, dict[str, Any]]) -> None:
    """Apply AuthSettings credential fields for providers not yet in result.

    This preserves backward compatibility: existing deployments that configure
    AUTH_GOOGLE_CLIENT_ID / AUTH_GITHUB_CLIENT_ID etc. continue to work even
    if those providers are not registered in the connect registry.
    """
    # Google
    if "google" not in result:
        cid = getattr(settings, "google_client_id", None)
        csec = getattr(settings, "google_client_secret", None)
        if cid and csec:
            result["google"] = {
                "kind": "oidc",
                "issuer": "https://accounts.google.com",
                "client_id": cid,
                "client_secret": csec.get_secret_value(),
                "scope": "openid email profile",
            }

    # GitHub
    if "github" not in result:
        cid = getattr(settings, "github_client_id", None)
        csec = getattr(settings, "github_client_secret", None)
        if cid and csec:
            result["github"] = {
                "kind": "github",
                "authorize_url": "https://github.com/login/oauth/authorize",
                "access_token_url": "https://github.com/login/oauth/access_token",
                "api_base_url": "https://api.github.com/",
                "client_id": cid,
                "client_secret": csec.get_secret_value(),
                "scope": "user:email",
            }

    # Microsoft
    if "microsoft" not in result:
        cid = getattr(settings, "ms_client_id", None)
        csec = getattr(settings, "ms_client_secret", None)
        tenant = getattr(settings, "ms_tenant", None)
        if cid and csec and tenant:
            result["microsoft"] = {
                "kind": "oidc",
                "issuer": f"https://login.microsoftonline.com/{tenant}/v2.0",
                "client_id": cid,
                "client_secret": csec.get_secret_value(),
                "scope": "openid email profile",
            }

    # LinkedIn
    if "linkedin" not in result:
        cid = getattr(settings, "li_client_id", None)
        csec = getattr(settings, "li_client_secret", None)
        if cid and csec:
            result["linkedin"] = {
                "kind": "linkedin",
                "authorize_url": "https://www.linkedin.com/oauth/v2/authorization",
                "access_token_url": "https://www.linkedin.com/oauth/v2/accessToken",
                "api_base_url": "https://api.linkedin.com/v2/",
                "client_id": cid,
                "client_secret": csec.get_secret_value(),
                "scope": "r_liteprofile r_emailaddress",
            }

    # Generic OIDC providers from oidc_providers list
    for p in getattr(settings, "oidc_providers", []) or []:
        if p.name not in result:
            result[p.name] = {
                "kind": "oidc",
                "issuer": p.issuer.rstrip("/"),
                "client_id": p.client_id,
                "client_secret": p.client_secret.get_secret_value(),
                "scope": p.scope or "openid email profile",
            }
