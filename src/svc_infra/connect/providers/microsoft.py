from __future__ import annotations

from svc_infra.connect.registry import OAuthProvider


def build_microsoft_provider() -> OAuthProvider | None:
    """Build Microsoft OAuth provider from environment variables.

    Delegates to the master catalog in generic.py.
    Env vars: MICROSOFT_CLIENT_ID / MICROSOFT_CLIENT_SECRET (or CONNECT_MICROSOFT_*)
    Optional: CONNECT_MICROSOFT_TENANT_ID or MICROSOFT_TENANT_ID (default: common)
    """
    from svc_infra.connect.providers.generic import _load_known_provider

    return _load_known_provider("microsoft")
