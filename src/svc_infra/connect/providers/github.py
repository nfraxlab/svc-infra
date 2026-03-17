from __future__ import annotations

from svc_infra.connect.registry import OAuthProvider


def build_github_provider() -> OAuthProvider | None:
    """Build GitHub OAuth provider from environment variables.

    Delegates to the master catalog in generic.py.
    Env vars: GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET (or CONNECT_GITHUB_*)
    """
    from svc_infra.connect.providers.generic import _load_known_provider

    return _load_known_provider("github")
