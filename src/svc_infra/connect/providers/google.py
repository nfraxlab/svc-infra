from __future__ import annotations

from svc_infra.connect.registry import OAuthProvider


def build_google_provider() -> OAuthProvider | None:
    """Build Google OAuth provider from environment variables.

    Delegates to the master catalog in generic.py.
    Env vars: GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET (or CONNECT_GOOGLE_* or GOOGLE_CONNECT_*)
    """
    from svc_infra.connect.providers.generic import _load_known_provider

    return _load_known_provider("google")
