from __future__ import annotations

from svc_infra.connect.registry import OAuthProvider


def build_atlassian_provider() -> OAuthProvider | None:
    """Build Atlassian OAuth 2.0 provider (Jira, Confluence) from env vars.

    Delegates to the master catalog in generic.py.
    Env vars: ATLASSIAN_CLIENT_ID / ATLASSIAN_CLIENT_SECRET (or CONNECT_ATLASSIAN_*)
    """
    from svc_infra.connect.providers.generic import _load_known_provider

    return _load_known_provider("atlassian")
