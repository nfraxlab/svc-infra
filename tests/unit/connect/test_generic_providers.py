"""Tests for the master OAuth provider catalog (connect/providers/generic.py).

Covers:
- _resolve_creds: primary CONNECT_* vars, legacy env var fallbacks, missing
- _load_known_provider: standard provider, dynamic builder, env overrides
- _url_builders: microsoft, okta, auth0, shopify (with and without domain)
- _load_generic_providers: empty, known via CONNECT_PROVIDERS, unknown with URLs
- load_all_connect_providers: assembles known + overrides from CONNECT_PROVIDERS
"""

from __future__ import annotations

from svc_infra.connect.providers.generic import (
    _build_auth0_urls,
    _build_microsoft_urls,
    _build_okta_urls,
    _build_shopify_urls,
    _load_generic_providers,
    _load_known_provider,
    _resolve_creds,
    load_all_connect_providers,
)
from svc_infra.connect.registry import OAuthProvider

# ===========================================================================
# _resolve_creds
# ===========================================================================


class TestResolveCreds:
    def test_returns_primary_connect_vars(self, monkeypatch):
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_ID", "primary-id")
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_SECRET", "primary-sec")
        result = _resolve_creds("github")
        assert result == ("primary-id", "primary-sec")

    def test_primary_takes_precedence_over_legacy(self, monkeypatch):
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_ID", "primary-id")
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_SECRET", "primary-sec")
        monkeypatch.setenv("GITHUB_CLIENT_ID", "legacy-id")
        monkeypatch.setenv("GITHUB_CLIENT_SECRET", "legacy-sec")
        result = _resolve_creds("github")
        assert result == ("primary-id", "primary-sec")

    def test_falls_back_to_legacy_when_primary_absent(self, monkeypatch):
        monkeypatch.delenv("CONNECT_GITHUB_CLIENT_ID", raising=False)
        monkeypatch.delenv("CONNECT_GITHUB_CLIENT_SECRET", raising=False)
        monkeypatch.setenv("GITHUB_CLIENT_ID", "legacy-id")
        monkeypatch.setenv("GITHUB_CLIENT_SECRET", "legacy-sec")
        result = _resolve_creds("github")
        assert result == ("legacy-id", "legacy-sec")

    def test_google_legacy_fallbacks(self, monkeypatch):
        monkeypatch.delenv("CONNECT_GOOGLE_CLIENT_ID", raising=False)
        monkeypatch.delenv("CONNECT_GOOGLE_CLIENT_SECRET", raising=False)
        monkeypatch.setenv("GOOGLE_CONNECT_CLIENT_ID", "gc-id")
        monkeypatch.setenv("GOOGLE_CONNECT_CLIENT_SECRET", "gc-sec")
        result = _resolve_creds("google")
        assert result == ("gc-id", "gc-sec")

    def test_google_plain_legacy_fallback(self, monkeypatch):
        for var in (
            "CONNECT_GOOGLE_CLIENT_ID",
            "CONNECT_GOOGLE_CLIENT_SECRET",
            "GOOGLE_CONNECT_CLIENT_ID",
            "GOOGLE_CONNECT_CLIENT_SECRET",
        ):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "plain-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "plain-sec")
        result = _resolve_creds("google")
        assert result == ("plain-id", "plain-sec")

    def test_returns_none_when_no_creds(self, monkeypatch):
        monkeypatch.delenv("CONNECT_NOTION_CLIENT_ID", raising=False)
        monkeypatch.delenv("CONNECT_NOTION_CLIENT_SECRET", raising=False)
        monkeypatch.delenv("NOTION_CLIENT_ID", raising=False)
        monkeypatch.delenv("NOTION_CLIENT_SECRET", raising=False)
        assert _resolve_creds("notion") is None

    def test_returns_none_when_only_id_set(self, monkeypatch):
        monkeypatch.setenv("CONNECT_SLACK_CLIENT_ID", "only-id")
        monkeypatch.delenv("CONNECT_SLACK_CLIENT_SECRET", raising=False)
        monkeypatch.delenv("SLACK_CLIENT_ID", raising=False)
        monkeypatch.delenv("SLACK_CLIENT_SECRET", raising=False)
        assert _resolve_creds("slack") is None

    def test_unknown_provider_without_legacy_uses_primary_only(self, monkeypatch):
        monkeypatch.setenv("CONNECT_ACME_CLIENT_ID", "acme-id")
        monkeypatch.setenv("CONNECT_ACME_CLIENT_SECRET", "acme-sec")
        result = _resolve_creds("acme")
        assert result == ("acme-id", "acme-sec")


# ===========================================================================
# URL builders
# ===========================================================================


class TestBuildMicrosoftUrls:
    def test_builds_with_default_tenant(self, monkeypatch):
        monkeypatch.delenv("CONNECT_MICROSOFT_TENANT_ID", raising=False)
        monkeypatch.delenv("MICROSOFT_TENANT_ID", raising=False)
        urls = _build_microsoft_urls()
        assert urls is not None
        assert "common" in urls["authorize_url"]
        assert "common" in urls["token_url"]

    def test_builds_with_custom_tenant(self, monkeypatch):
        monkeypatch.setenv("CONNECT_MICROSOFT_TENANT_ID", "mytenant")
        urls = _build_microsoft_urls()
        assert urls is not None
        assert "mytenant" in urls["authorize_url"]
        assert "mytenant" in urls["token_url"]
        assert "mytenant" in urls["oidc_discovery_url"]

    def test_legacy_tenant_env_var(self, monkeypatch):
        monkeypatch.delenv("CONNECT_MICROSOFT_TENANT_ID", raising=False)
        monkeypatch.setenv("MICROSOFT_TENANT_ID", "legacy-tenant")
        urls = _build_microsoft_urls()
        assert urls is not None
        assert "legacy-tenant" in urls["authorize_url"]


class TestBuildOktaUrls:
    def test_returns_none_without_domain(self, monkeypatch):
        monkeypatch.delenv("CONNECT_OKTA_DOMAIN", raising=False)
        monkeypatch.delenv("OKTA_DOMAIN", raising=False)
        assert _build_okta_urls() is None

    def test_builds_with_domain(self, monkeypatch):
        monkeypatch.setenv("CONNECT_OKTA_DOMAIN", "acme.okta.com")
        urls = _build_okta_urls()
        assert urls is not None
        assert "acme.okta.com" in urls["authorize_url"]
        assert "acme.okta.com" in urls["oidc_discovery_url"]

    def test_strips_trailing_slash(self, monkeypatch):
        monkeypatch.setenv("OKTA_DOMAIN", "acme.okta.com/")
        monkeypatch.delenv("CONNECT_OKTA_DOMAIN", raising=False)
        urls = _build_okta_urls()
        assert urls is not None
        # Domain trailing slash is stripped so the resulting URL has no double slash
        assert "//oauth2" not in urls["authorize_url"]
        assert urls["authorize_url"].startswith("https://acme.okta.com/oauth2")


class TestBuildAuth0Urls:
    def test_returns_none_without_domain(self, monkeypatch):
        monkeypatch.delenv("CONNECT_AUTH0_DOMAIN", raising=False)
        monkeypatch.delenv("AUTH0_DOMAIN", raising=False)
        assert _build_auth0_urls() is None

    def test_builds_with_domain(self, monkeypatch):
        monkeypatch.setenv("CONNECT_AUTH0_DOMAIN", "acme.auth0.com")
        urls = _build_auth0_urls()
        assert urls is not None
        assert "acme.auth0.com" in urls["authorize_url"]
        assert "acme.auth0.com" in urls["oidc_discovery_url"]


class TestBuildShopifyUrls:
    def test_returns_none_without_shop(self, monkeypatch):
        monkeypatch.delenv("CONNECT_SHOPIFY_SHOP", raising=False)
        monkeypatch.delenv("SHOPIFY_SHOP", raising=False)
        assert _build_shopify_urls() is None

    def test_builds_with_shop(self, monkeypatch):
        monkeypatch.setenv("CONNECT_SHOPIFY_SHOP", "mystore.myshopify.com")
        urls = _build_shopify_urls()
        assert urls is not None
        assert "mystore.myshopify.com" in urls["authorize_url"]
        assert "mystore.myshopify.com" in urls["token_url"]


# ===========================================================================
# _load_known_provider
# ===========================================================================


class TestLoadKnownProvider:
    def test_loads_github_with_primary_vars(self, monkeypatch):
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_ID", "gh-id")
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_SECRET", "gh-sec")
        p = _load_known_provider("github")
        assert p is not None
        assert p.name == "github"
        assert p.client_id == "gh-id"
        assert p.login_enabled is True
        assert p.userinfo_kind == "github"

    def test_loads_github_with_legacy_vars(self, monkeypatch):
        monkeypatch.delenv("CONNECT_GITHUB_CLIENT_ID", raising=False)
        monkeypatch.delenv("CONNECT_GITHUB_CLIENT_SECRET", raising=False)
        monkeypatch.setenv("GITHUB_CLIENT_ID", "legacy-gh-id")
        monkeypatch.setenv("GITHUB_CLIENT_SECRET", "legacy-gh-sec")
        p = _load_known_provider("github")
        assert p is not None
        assert p.client_id == "legacy-gh-id"

    def test_returns_none_when_no_creds(self, monkeypatch):
        monkeypatch.delenv("CONNECT_GITHUB_CLIENT_ID", raising=False)
        monkeypatch.delenv("CONNECT_GITHUB_CLIENT_SECRET", raising=False)
        monkeypatch.delenv("GITHUB_CLIENT_ID", raising=False)
        monkeypatch.delenv("GITHUB_CLIENT_SECRET", raising=False)
        assert _load_known_provider("github") is None

    def test_returns_none_for_unknown_name(self, monkeypatch):
        monkeypatch.setenv("CONNECT_UNKNOWN_CLIENT_ID", "id")
        monkeypatch.setenv("CONNECT_UNKNOWN_CLIENT_SECRET", "sec")
        assert _load_known_provider("unknown_provider_xyz") is None

    def test_google_has_oidc_discovery_url(self, monkeypatch):
        monkeypatch.setenv("CONNECT_GOOGLE_CLIENT_ID", "g-id")
        monkeypatch.setenv("CONNECT_GOOGLE_CLIENT_SECRET", "g-sec")
        p = _load_known_provider("google")
        assert p is not None
        assert p.oidc_discovery_url == "https://accounts.google.com"
        assert p.userinfo_kind == "oidc"

    def test_microsoft_uses_builder(self, monkeypatch):
        monkeypatch.setenv("CONNECT_MICROSOFT_CLIENT_ID", "ms-id")
        monkeypatch.setenv("CONNECT_MICROSOFT_CLIENT_SECRET", "ms-sec")
        monkeypatch.delenv("CONNECT_MICROSOFT_TENANT_ID", raising=False)
        monkeypatch.delenv("MICROSOFT_TENANT_ID", raising=False)
        p = _load_known_provider("microsoft")
        assert p is not None
        assert "common" in p.authorize_url

    def test_okta_returns_none_without_domain(self, monkeypatch):
        monkeypatch.setenv("CONNECT_OKTA_CLIENT_ID", "okta-id")
        monkeypatch.setenv("CONNECT_OKTA_CLIENT_SECRET", "okta-sec")
        monkeypatch.delenv("CONNECT_OKTA_DOMAIN", raising=False)
        monkeypatch.delenv("OKTA_DOMAIN", raising=False)
        assert _load_known_provider("okta") is None

    def test_okta_loads_with_domain(self, monkeypatch):
        monkeypatch.setenv("CONNECT_OKTA_CLIENT_ID", "okta-id")
        monkeypatch.setenv("CONNECT_OKTA_CLIENT_SECRET", "okta-sec")
        monkeypatch.setenv("CONNECT_OKTA_DOMAIN", "corp.okta.com")
        p = _load_known_provider("okta")
        assert p is not None
        assert "corp.okta.com" in p.authorize_url

    def test_scope_override_via_env(self, monkeypatch):
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_ID", "gh-id")
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_SECRET", "gh-sec")
        monkeypatch.setenv("CONNECT_GITHUB_SCOPES", "repo,read:org")
        p = _load_known_provider("github")
        assert p is not None
        assert p.default_scopes == ["repo", "read:org"]

    def test_pkce_override_false(self, monkeypatch):
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_ID", "gh-id")
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_SECRET", "gh-sec")
        monkeypatch.setenv("CONNECT_GITHUB_PKCE", "false")
        p = _load_known_provider("github")
        assert p is not None
        assert p.pkce_required is False

    def test_login_override_false(self, monkeypatch):
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_ID", "gh-id")
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_SECRET", "gh-sec")
        monkeypatch.setenv("CONNECT_GITHUB_LOGIN", "false")
        p = _load_known_provider("github")
        assert p is not None
        assert p.login_enabled is False

    def test_login_override_true_for_non_login_provider(self, monkeypatch):
        monkeypatch.setenv("CONNECT_NOTION_CLIENT_ID", "n-id")
        monkeypatch.setenv("CONNECT_NOTION_CLIENT_SECRET", "n-sec")
        monkeypatch.setenv("CONNECT_NOTION_LOGIN", "true")
        p = _load_known_provider("notion")
        assert p is not None
        assert p.login_enabled is True

    def test_authorize_url_override(self, monkeypatch):
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_ID", "gh-id")
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_SECRET", "gh-sec")
        monkeypatch.setenv("CONNECT_GITHUB_AUTHORIZE_URL", "https://custom.host/auth")
        p = _load_known_provider("github")
        assert p is not None
        assert p.authorize_url == "https://custom.host/auth"


# ===========================================================================
# _load_generic_providers (CONNECT_PROVIDERS list)
# ===========================================================================


class TestLoadGenericProviders:
    def test_empty_when_connect_providers_not_set(self, monkeypatch):
        monkeypatch.delenv("CONNECT_PROVIDERS", raising=False)
        assert _load_generic_providers() == []

    def test_empty_when_connect_providers_empty_string(self, monkeypatch):
        monkeypatch.setenv("CONNECT_PROVIDERS", "")
        assert _load_generic_providers() == []

    def test_loads_known_provider_from_list(self, monkeypatch):
        monkeypatch.setenv("CONNECT_PROVIDERS", "github")
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_ID", "gh-id")
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_SECRET", "gh-sec")
        result = _load_generic_providers()
        assert len(result) == 1
        assert result[0].name == "github"

    def test_loads_unknown_provider_with_full_config(self, monkeypatch):
        monkeypatch.setenv("CONNECT_PROVIDERS", "acme")
        monkeypatch.setenv("CONNECT_ACME_CLIENT_ID", "acme-id")
        monkeypatch.setenv("CONNECT_ACME_CLIENT_SECRET", "acme-sec")
        monkeypatch.setenv("CONNECT_ACME_AUTHORIZE_URL", "https://acme.com/auth")
        monkeypatch.setenv("CONNECT_ACME_TOKEN_URL", "https://acme.com/token")
        result = _load_generic_providers()
        assert len(result) == 1
        p = result[0]
        assert p.name == "acme"
        assert p.authorize_url == "https://acme.com/auth"
        assert p.token_url == "https://acme.com/token"

    def test_skips_unknown_provider_missing_urls(self, monkeypatch):
        monkeypatch.setenv("CONNECT_PROVIDERS", "acme")
        monkeypatch.setenv("CONNECT_ACME_CLIENT_ID", "acme-id")
        monkeypatch.setenv("CONNECT_ACME_CLIENT_SECRET", "acme-sec")
        monkeypatch.delenv("CONNECT_ACME_AUTHORIZE_URL", raising=False)
        monkeypatch.delenv("CONNECT_ACME_TOKEN_URL", raising=False)
        assert _load_generic_providers() == []

    def test_skips_unknown_provider_missing_creds(self, monkeypatch):
        monkeypatch.setenv("CONNECT_PROVIDERS", "acme")
        monkeypatch.delenv("CONNECT_ACME_CLIENT_ID", raising=False)
        monkeypatch.delenv("CONNECT_ACME_CLIENT_SECRET", raising=False)
        monkeypatch.setenv("CONNECT_ACME_AUTHORIZE_URL", "https://acme.com/auth")
        monkeypatch.setenv("CONNECT_ACME_TOKEN_URL", "https://acme.com/token")
        assert _load_generic_providers() == []

    def test_unknown_provider_scopes_parsed(self, monkeypatch):
        monkeypatch.setenv("CONNECT_PROVIDERS", "acme")
        monkeypatch.setenv("CONNECT_ACME_CLIENT_ID", "acme-id")
        monkeypatch.setenv("CONNECT_ACME_CLIENT_SECRET", "acme-sec")
        monkeypatch.setenv("CONNECT_ACME_AUTHORIZE_URL", "https://acme.com/auth")
        monkeypatch.setenv("CONNECT_ACME_TOKEN_URL", "https://acme.com/token")
        monkeypatch.setenv("CONNECT_ACME_SCOPES", "read,write,admin")
        result = _load_generic_providers()
        assert result[0].default_scopes == ["read", "write", "admin"]

    def test_loads_multiple_providers(self, monkeypatch):
        monkeypatch.setenv("CONNECT_PROVIDERS", "github, acme")
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_ID", "gh-id")
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_SECRET", "gh-sec")
        monkeypatch.setenv("CONNECT_ACME_CLIENT_ID", "acme-id")
        monkeypatch.setenv("CONNECT_ACME_CLIENT_SECRET", "acme-sec")
        monkeypatch.setenv("CONNECT_ACME_AUTHORIZE_URL", "https://acme.com/auth")
        monkeypatch.setenv("CONNECT_ACME_TOKEN_URL", "https://acme.com/token")
        result = _load_generic_providers()
        names = {p.name for p in result}
        assert names == {"github", "acme"}


# ===========================================================================
# load_all_connect_providers
# ===========================================================================


class TestLoadAllConnectProviders:
    def test_returns_empty_when_no_creds(self, monkeypatch):
        # Clear all provider env vars that could accidentally be set
        for var in (
            "CONNECT_GITHUB_CLIENT_ID",
            "GITHUB_CLIENT_ID",
            "CONNECT_GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CONNECT_CLIENT_ID",
            "CONNECT_SLACK_CLIENT_ID",
            "SLACK_CLIENT_ID",
            "CONNECT_NOTION_CLIENT_ID",
            "NOTION_CLIENT_ID",
            "CONNECT_PROVIDERS",
        ):
            monkeypatch.delenv(var, raising=False)
        result = load_all_connect_providers()
        assert result == []

    def test_includes_github_when_creds_set(self, monkeypatch):
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_ID", "gh-id")
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_SECRET", "gh-sec")
        result = load_all_connect_providers()
        names = {p.name for p in result}
        assert "github" in names

    def test_connect_providers_override_catalog_entry(self, monkeypatch):
        # Provider in CONNECT_PROVIDERS overrides catalog entry
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_ID", "gh-catalog-id")
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_SECRET", "gh-catalog-sec")
        monkeypatch.setenv("CONNECT_PROVIDERS", "github")
        result = load_all_connect_providers()
        github = next(p for p in result if p.name == "github")
        # The CONNECT_PROVIDERS entry wins (loads via _load_known_provider again
        # but replaces the catalog entry in the dict — same result since same creds)
        assert github.client_id == "gh-catalog-id"

    def test_includes_unknown_provider_from_connect_providers(self, monkeypatch):
        monkeypatch.setenv("CONNECT_PROVIDERS", "acme")
        monkeypatch.setenv("CONNECT_ACME_CLIENT_ID", "acme-id")
        monkeypatch.setenv("CONNECT_ACME_CLIENT_SECRET", "acme-sec")
        monkeypatch.setenv("CONNECT_ACME_AUTHORIZE_URL", "https://acme.com/auth")
        monkeypatch.setenv("CONNECT_ACME_TOKEN_URL", "https://acme.com/token")
        result = load_all_connect_providers()
        names = {p.name for p in result}
        assert "acme" in names

    def test_returns_only_oauth_provider_instances(self, monkeypatch):
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_ID", "gh-id")
        monkeypatch.setenv("CONNECT_GITHUB_CLIENT_SECRET", "gh-sec")
        result = load_all_connect_providers()
        assert all(isinstance(p, OAuthProvider) for p in result)
