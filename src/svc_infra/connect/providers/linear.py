from __future__ import annotations

from svc_infra.connect.registry import OAuthProvider


def build_linear_provider() -> OAuthProvider | None:
    """Build Linear OAuth 2.0 provider from environment variables.

    Delegates to the master catalog in generic.py.
    Env vars: LINEAR_CLIENT_ID / LINEAR_CLIENT_SECRET (or CONNECT_LINEAR_*)
    """
    from svc_infra.connect.providers.generic import _load_known_provider

    return _load_known_provider("linear")
