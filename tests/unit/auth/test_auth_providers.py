"""Unit tests for svc_infra.api.fastapi.auth.providers module."""

from __future__ import annotations

from unittest.mock import MagicMock

from svc_infra.api.fastapi.auth.providers import providers_from_settings


class TestProvidersFromSettings:
    """Tests for providers_from_settings function."""

    def test_empty_settings(self) -> None:
        """Test with no providers configured."""
        settings = MagicMock()
        settings.google_client_id = None
        settings.google_client_secret = None
        settings.github_client_id = None
        settings.github_client_secret = None
        settings.ms_client_id = None
        settings.ms_client_secret = None
        settings.ms_tenant = None
        settings.li_client_id = None
        settings.li_client_secret = None
        settings.oidc_providers = []

        result = providers_from_settings(settings)

        assert result == {}

    def test_google_provider(self) -> None:
        """Test Google OIDC provider configuration."""
        settings = MagicMock()
        settings.google_client_id = "google-client-123"
        settings.google_client_secret = MagicMock()
        settings.google_client_secret.get_secret_value.return_value = "google-secret"
        settings.github_client_id = None
        settings.github_client_secret = None
        settings.ms_client_id = None
        settings.ms_client_secret = None
        settings.ms_tenant = None
        settings.li_client_id = None
        settings.li_client_secret = None
        settings.oidc_providers = []

        result = providers_from_settings(settings)

        assert "google" in result
        assert result["google"]["kind"] == "oidc"
        assert result["google"]["issuer"] == "https://accounts.google.com"
        assert result["google"]["client_id"] == "google-client-123"
        assert result["google"]["client_secret"] == "google-secret"
        assert result["google"]["scope"] == "openid email profile"

    def test_github_provider(self) -> None:
        """Test GitHub OAuth provider configuration."""
        settings = MagicMock()
        settings.google_client_id = None
        settings.google_client_secret = None
        settings.github_client_id = "github-client-456"
        settings.github_client_secret = MagicMock()
        settings.github_client_secret.get_secret_value.return_value = "github-secret"
        settings.ms_client_id = None
        settings.ms_client_secret = None
        settings.ms_tenant = None
        settings.li_client_id = None
        settings.li_client_secret = None
        settings.oidc_providers = []

        result = providers_from_settings(settings)

        assert "github" in result
        assert result["github"]["kind"] == "github"
        assert result["github"]["authorize_url"] == "https://github.com/login/oauth/authorize"
        assert result["github"]["access_token_url"] == "https://github.com/login/oauth/access_token"
        assert result["github"]["api_base_url"] == "https://api.github.com/"
        assert result["github"]["client_id"] == "github-client-456"
        assert result["github"]["client_secret"] == "github-secret"
        assert result["github"]["scope"] == "user:email"

    def test_microsoft_provider(self) -> None:
        """Test Microsoft Entra ID OIDC provider configuration."""
        settings = MagicMock()
        settings.google_client_id = None
        settings.google_client_secret = None
        settings.github_client_id = None
        settings.github_client_secret = None
        settings.ms_client_id = "ms-client-789"
        settings.ms_client_secret = MagicMock()
        settings.ms_client_secret.get_secret_value.return_value = "ms-secret"
        settings.ms_tenant = "my-tenant-id"
        settings.li_client_id = None
        settings.li_client_secret = None
        settings.oidc_providers = []

        result = providers_from_settings(settings)

        assert "microsoft" in result
        assert result["microsoft"]["kind"] == "oidc"
        assert (
            result["microsoft"]["issuer"] == "https://login.microsoftonline.com/my-tenant-id/v2.0"
        )
        assert result["microsoft"]["client_id"] == "ms-client-789"
        assert result["microsoft"]["client_secret"] == "ms-secret"
        assert result["microsoft"]["scope"] == "openid email profile"

    def test_linkedin_provider(self) -> None:
        """Test LinkedIn OAuth provider configuration."""
        settings = MagicMock()
        settings.google_client_id = None
        settings.google_client_secret = None
        settings.github_client_id = None
        settings.github_client_secret = None
        settings.ms_client_id = None
        settings.ms_client_secret = None
        settings.ms_tenant = None
        settings.li_client_id = "li-client-abc"
        settings.li_client_secret = MagicMock()
        settings.li_client_secret.get_secret_value.return_value = "li-secret"
        settings.oidc_providers = []

        result = providers_from_settings(settings)

        assert "linkedin" in result
        assert result["linkedin"]["kind"] == "linkedin"
        assert (
            result["linkedin"]["authorize_url"] == "https://www.linkedin.com/oauth/v2/authorization"
        )
        assert (
            result["linkedin"]["access_token_url"]
            == "https://www.linkedin.com/oauth/v2/accessToken"
        )
        assert result["linkedin"]["api_base_url"] == "https://api.linkedin.com/v2/"
        assert result["linkedin"]["client_id"] == "li-client-abc"
        assert result["linkedin"]["client_secret"] == "li-secret"
        assert result["linkedin"]["scope"] == "r_liteprofile r_emailaddress"

    def test_generic_oidc_providers(self) -> None:
        """Test generic OIDC providers (Okta, Auth0, Keycloak)."""
        okta_provider = MagicMock()
        okta_provider.name = "okta"
        okta_provider.issuer = "https://dev-123.okta.com/"
        okta_provider.client_id = "okta-client"
        okta_provider.client_secret = MagicMock()
        okta_provider.client_secret.get_secret_value.return_value = "okta-secret"
        okta_provider.scope = "openid profile email"

        settings = MagicMock()
        settings.google_client_id = None
        settings.google_client_secret = None
        settings.github_client_id = None
        settings.github_client_secret = None
        settings.ms_client_id = None
        settings.ms_client_secret = None
        settings.ms_tenant = None
        settings.li_client_id = None
        settings.li_client_secret = None
        settings.oidc_providers = [okta_provider]

        result = providers_from_settings(settings)

        assert "okta" in result
        assert result["okta"]["kind"] == "oidc"
        assert result["okta"]["issuer"] == "https://dev-123.okta.com"  # trailing slash stripped
        assert result["okta"]["client_id"] == "okta-client"
        assert result["okta"]["client_secret"] == "okta-secret"
        assert result["okta"]["scope"] == "openid profile email"

    def test_oidc_provider_default_scope(self) -> None:
        """Test generic OIDC provider uses default scope when not specified."""
        auth0_provider = MagicMock()
        auth0_provider.name = "auth0"
        auth0_provider.issuer = "https://myapp.auth0.com"
        auth0_provider.client_id = "auth0-client"
        auth0_provider.client_secret = MagicMock()
        auth0_provider.client_secret.get_secret_value.return_value = "auth0-secret"
        auth0_provider.scope = None

        settings = MagicMock()
        settings.google_client_id = None
        settings.google_client_secret = None
        settings.github_client_id = None
        settings.github_client_secret = None
        settings.ms_client_id = None
        settings.ms_client_secret = None
        settings.ms_tenant = None
        settings.li_client_id = None
        settings.li_client_secret = None
        settings.oidc_providers = [auth0_provider]

        result = providers_from_settings(settings)

        assert "auth0" in result
        assert result["auth0"]["scope"] == "openid email profile"

    def test_multiple_providers(self) -> None:
        """Test multiple providers configured simultaneously."""
        settings = MagicMock()
        settings.google_client_id = "google-client"
        settings.google_client_secret = MagicMock()
        settings.google_client_secret.get_secret_value.return_value = "google-secret"
        settings.github_client_id = "github-client"
        settings.github_client_secret = MagicMock()
        settings.github_client_secret.get_secret_value.return_value = "github-secret"
        settings.ms_client_id = None
        settings.ms_client_secret = None
        settings.ms_tenant = None
        settings.li_client_id = None
        settings.li_client_secret = None
        settings.oidc_providers = []

        result = providers_from_settings(settings)

        assert len(result) == 2
        assert "google" in result
        assert "github" in result
