from __future__ import annotations

# Backward-compat re-exports so callers that import build_*_provider directly
# continue to work.  Each thin wrapper delegates to the master catalog.
from svc_infra.connect.providers.atlassian import build_atlassian_provider
from svc_infra.connect.providers.generic import load_all_connect_providers
from svc_infra.connect.providers.github import build_github_provider
from svc_infra.connect.providers.google import build_google_provider
from svc_infra.connect.providers.linear import build_linear_provider
from svc_infra.connect.providers.microsoft import build_microsoft_provider
from svc_infra.connect.providers.notion import build_notion_provider
from svc_infra.connect.providers.slack import build_slack_provider
from svc_infra.connect.registry import registry


def _load_builtin_providers() -> None:
    """Register all configured OAuth providers from the master catalog."""
    for provider in load_all_connect_providers():
        registry.register(provider)


_load_builtin_providers()

__all__ = [
    "build_atlassian_provider",
    "build_github_provider",
    "build_google_provider",
    "build_linear_provider",
    "build_microsoft_provider",
    "build_notion_provider",
    "build_slack_provider",
]
