from __future__ import annotations

from svc_infra.connect.registry import OAuthProvider


def build_slack_provider() -> OAuthProvider | None:
    """Build Slack OAuth v2 provider from environment variables.

    Delegates to the master catalog in generic.py.
    Env vars: SLACK_CLIENT_ID / SLACK_CLIENT_SECRET (or CONNECT_SLACK_*)
    """
    from svc_infra.connect.providers.generic import _load_known_provider

    return _load_known_provider("slack")
