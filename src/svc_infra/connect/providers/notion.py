from __future__ import annotations

from svc_infra.connect.registry import OAuthProvider


def build_notion_provider() -> OAuthProvider | None:
    """Build Notion OAuth provider from environment variables.

    Delegates to the master catalog in generic.py.
    Env vars: NOTION_CLIENT_ID / NOTION_CLIENT_SECRET (or CONNECT_NOTION_*)
    """
    from svc_infra.connect.providers.generic import _load_known_provider

    return _load_known_provider("notion")
