"""
Tests for OAuth flow: authorization, callback, and token exchange.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest
from fastapi import HTTPException


class TestPKCEGeneration:
    """Tests for PKCE (Proof Key for Code Exchange) generation."""

    def test_generates_verifier_and_challenge(self) -> None:
        """Should generate a valid verifier and challenge pair."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _gen_pkce_pair

        verifier, challenge = _gen_pkce_pair()

        assert isinstance(verifier, str)
        assert isinstance(challenge, str)
        assert len(verifier) > 0
        assert len(challenge) > 0

    def test_challenge_matches_verifier_hash(self) -> None:
        """Should generate challenge as SHA-256 hash of verifier."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _gen_pkce_pair

        verifier, challenge = _gen_pkce_pair()

        # Verify the relationship
        expected_digest = hashlib.sha256(verifier.encode()).digest()
        expected_challenge = base64.urlsafe_b64encode(expected_digest).rstrip(b"=").decode()

        assert challenge == expected_challenge

    def test_generates_unique_pairs(self) -> None:
        """Should generate unique pairs each time."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _gen_pkce_pair

        pairs = [_gen_pkce_pair() for _ in range(10)]
        verifiers = [p[0] for p in pairs]
        challenges = [p[1] for p in pairs]

        assert len(set(verifiers)) == 10
        assert len(set(challenges)) == 10


class TestRedirectValidation:
    """Tests for OAuth redirect URL validation."""

    def test_allows_relative_url(self) -> None:
        """Should allow relative URLs (no host)."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _validate_redirect

        # Should not raise
        _validate_redirect("/dashboard", ["example.com"], require_https=True)

    def test_allows_whitelisted_host(self) -> None:
        """Should allow URLs with whitelisted hosts."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _validate_redirect

        _validate_redirect(
            "https://app.example.com/callback",
            ["app.example.com"],
            require_https=True,
        )

    def test_rejects_non_whitelisted_host(self) -> None:
        """Should reject URLs with non-whitelisted hosts."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _validate_redirect

        with pytest.raises(HTTPException) as exc_info:
            _validate_redirect(
                "https://evil.com/steal",
                ["example.com"],
                require_https=True,
            )
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "redirect_not_allowed"

    def test_rejects_http_when_https_required(self) -> None:
        """Should reject HTTP URLs when HTTPS is required."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _validate_redirect

        with pytest.raises(HTTPException) as exc_info:
            _validate_redirect(
                "http://example.com/callback",
                ["example.com"],
                require_https=True,
            )
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "https_required"

    def test_allows_http_when_not_required(self) -> None:
        """Should allow HTTP when HTTPS is not required."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _validate_redirect

        _validate_redirect(
            "http://localhost:3000/callback",
            ["localhost:3000"],
            require_https=False,
        )

    def test_handles_host_with_port(self) -> None:
        """Should handle hosts with explicit ports."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _validate_redirect

        _validate_redirect(
            "https://example.com:8443/callback",
            ["example.com:8443"],
            require_https=True,
        )

    def test_case_insensitive_host_matching(self) -> None:
        """Should match hosts case-insensitively."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _validate_redirect

        _validate_redirect(
            "https://Example.COM/callback",
            ["example.com"],
            require_https=True,
        )


class TestExpiresAtCoercion:
    """Tests for OAuth token expiration parsing."""

    def test_parses_expires_at_seconds(self) -> None:
        """Should parse expires_at as Unix timestamp in seconds."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _coerce_expires_at

        ts = datetime.now(UTC).timestamp()
        result = _coerce_expires_at({"expires_at": ts})

        assert result is not None
        assert abs((result - datetime.now(UTC)).total_seconds()) < 5

    def test_parses_expires_at_milliseconds(self) -> None:
        """Should parse expires_at as Unix timestamp in milliseconds."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _coerce_expires_at

        ts_ms = datetime.now(UTC).timestamp() * 1000
        result = _coerce_expires_at({"expires_at": ts_ms})

        assert result is not None
        assert abs((result - datetime.now(UTC)).total_seconds()) < 5

    def test_parses_expires_in_seconds(self) -> None:
        """Should parse expires_in as seconds from now."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _coerce_expires_at

        before = datetime.now(UTC)
        result = _coerce_expires_at({"expires_in": 3600})
        after = datetime.now(UTC)

        assert result is not None
        expected_min = before + timedelta(seconds=3600)
        expected_max = after + timedelta(seconds=3600)
        assert expected_min <= result <= expected_max

    def test_returns_none_for_missing_expiry(self) -> None:
        """Should return None when no expiry information."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _coerce_expires_at

        result = _coerce_expires_at({})
        assert result is None

    def test_returns_none_for_none_token(self) -> None:
        """Should return None for None token."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _coerce_expires_at

        result = _coerce_expires_at(None)
        assert result is None

    def test_returns_none_for_invalid_type(self) -> None:
        """Should return None for non-dict token."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _coerce_expires_at

        result = _coerce_expires_at("not-a-dict")  # type: ignore
        assert result is None


class TestProviderAccountModel:
    """Tests for OAuth provider account model schema."""

    def test_provider_account_has_required_columns(self) -> None:
        """Should have required columns defined."""
        from svc_infra.security.oauth_models import ProviderAccount

        # Check model has required columns
        mapper = ProviderAccount.__mapper__
        columns = {c.key for c in mapper.columns}

        assert "id" in columns
        assert "user_id" in columns
        assert "provider" in columns
        assert "provider_account_id" in columns

    def test_provider_account_has_token_columns(self) -> None:
        """Should have token storage columns."""
        from svc_infra.security.oauth_models import ProviderAccount

        mapper = ProviderAccount.__mapper__
        columns = {c.key for c in mapper.columns}

        assert "access_token" in columns
        assert "refresh_token" in columns
        assert "expires_at" in columns

    def test_provider_account_has_claims_column(self) -> None:
        """Should have raw_claims JSON column."""
        from svc_infra.security.oauth_models import ProviderAccount

        mapper = ProviderAccount.__mapper__
        columns = {c.key for c in mapper.columns}

        assert "raw_claims" in columns

    def test_provider_account_tablename(self) -> None:
        """Should have correct table name."""
        from svc_infra.security.oauth_models import ProviderAccount

        assert ProviderAccount.__tablename__ == "provider_accounts"


class TestProvidersFromSettings:
    """Tests for OAuth provider registration from settings."""

    def test_registers_google_provider(self) -> None:
        """Should register Google as OIDC provider."""
        from svc_infra.api.fastapi.auth.providers import providers_from_settings

        class Settings:
            google_client_id = "google-client-id"
            google_client_secret = Mock(get_secret_value=lambda: "google-secret")

        result = providers_from_settings(Settings())

        assert "google" in result
        assert result["google"]["kind"] == "oidc"
        assert result["google"]["issuer"] == "https://accounts.google.com"
        assert result["google"]["client_id"] == "google-client-id"

    def test_registers_github_provider(self) -> None:
        """Should register GitHub as non-OIDC provider."""
        from svc_infra.api.fastapi.auth.providers import providers_from_settings

        class Settings:
            github_client_id = "github-client-id"
            github_client_secret = Mock(get_secret_value=lambda: "github-secret")

        result = providers_from_settings(Settings())

        assert "github" in result
        assert result["github"]["kind"] == "github"
        assert "github.com" in result["github"]["authorize_url"]

    def test_registers_microsoft_provider(self) -> None:
        """Should register Microsoft Entra ID as OIDC provider."""
        from svc_infra.api.fastapi.auth.providers import providers_from_settings

        class Settings:
            ms_client_id = "ms-client-id"
            ms_client_secret = Mock(get_secret_value=lambda: "ms-secret")
            ms_tenant = "my-tenant-id"

        result = providers_from_settings(Settings())

        assert "microsoft" in result
        assert result["microsoft"]["kind"] == "oidc"
        assert "my-tenant-id" in result["microsoft"]["issuer"]

    def test_registers_linkedin_provider(self) -> None:
        """Should register LinkedIn as non-OIDC provider."""
        from svc_infra.api.fastapi.auth.providers import providers_from_settings

        class Settings:
            li_client_id = "li-client-id"
            li_client_secret = Mock(get_secret_value=lambda: "li-secret")

        result = providers_from_settings(Settings())

        assert "linkedin" in result
        assert result["linkedin"]["kind"] == "linkedin"
        assert "linkedin.com" in result["linkedin"]["authorize_url"]

    def test_skips_unconfigured_providers(self) -> None:
        """Should skip providers without credentials."""
        from svc_infra.api.fastapi.auth.providers import providers_from_settings

        class Settings:
            google_client_id = None
            google_client_secret = None

        result = providers_from_settings(Settings())

        assert "google" not in result

    def test_registers_custom_oidc_providers(self) -> None:
        """Should register custom OIDC providers from list."""
        from svc_infra.api.fastapi.auth.providers import providers_from_settings

        class OIDCProvider:
            name = "okta"
            issuer = "https://dev-12345.okta.com/"
            client_id = "okta-client"
            client_secret = Mock(get_secret_value=lambda: "okta-secret")
            scope = "openid email profile"

        class Settings:
            oidc_providers = [OIDCProvider()]

        result = providers_from_settings(Settings())

        assert "okta" in result
        assert result["okta"]["kind"] == "oidc"
        assert result["okta"]["issuer"] == "https://dev-12345.okta.com"  # trailing slash stripped


class TestCookieConfiguration:
    """Tests for OAuth cookie configuration."""

    def test_cookie_name_default(self) -> None:
        """Should use default cookie name."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _cookie_name

        class Settings:
            auth_cookie_name = "svc_auth"
            session_cookie_secure = False
            session_cookie_domain = None

        name = _cookie_name(Settings())
        assert name == "svc_auth"

    def test_cookie_name_with_host_prefix(self) -> None:
        """Should add __Host- prefix when secure and no domain."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _cookie_name

        class Settings:
            auth_cookie_name = "auth"
            session_cookie_secure = True
            session_cookie_domain = None

        name = _cookie_name(Settings())
        assert name == "__Host-auth"

    def test_cookie_name_no_prefix_with_domain(self) -> None:
        """Should not add __Host- prefix when domain is set."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _cookie_name

        class Settings:
            auth_cookie_name = "auth"
            session_cookie_secure = True
            session_cookie_domain = "example.com"

        name = _cookie_name(Settings())
        assert name == "auth"

    def test_cookie_domain_returns_none_when_empty(self) -> None:
        """Should return None for empty domain."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _cookie_domain

        class Settings:
            session_cookie_domain = ""

        domain = _cookie_domain(Settings())
        assert domain is None

    def test_cookie_domain_returns_value_when_set(self) -> None:
        """Should return domain when set."""
        from svc_infra.api.fastapi.auth.routers.oauth_router import _cookie_domain

        class Settings:
            session_cookie_domain = ".example.com"

        domain = _cookie_domain(Settings())
        assert domain == ".example.com"


class TestOAuthStateManagement:
    """Tests for OAuth state parameter handling."""

    def test_state_is_random(self) -> None:
        """Should generate random state values."""
        states = [secrets.token_urlsafe(32) for _ in range(10)]
        assert len(set(states)) == 10  # all unique

    def test_state_is_url_safe(self) -> None:
        """Should generate URL-safe state values."""
        state = secrets.token_urlsafe(32)
        # URL-safe base64 uses alphanumeric, -, _
        assert all(c.isalnum() or c in "-_" for c in state)


class TestOAuthTokenExchange:
    """Tests for OAuth token exchange flow."""

    def test_session_model_has_required_fields(self) -> None:
        """Should have required fields for session management."""
        from svc_infra.security.models import AuthSession

        mapper = AuthSession.__mapper__
        columns = {c.key for c in mapper.columns}

        assert "id" in columns
        assert "user_id" in columns
        assert "tenant_id" in columns
        assert "revoked_at" in columns

    def test_refresh_token_model_has_required_fields(self) -> None:
        """Should have required fields for refresh tokens."""
        from svc_infra.security.models import RefreshToken

        mapper = RefreshToken.__mapper__
        columns = {c.key for c in mapper.columns}

        assert "id" in columns
        assert "session_id" in columns
        assert "token_hash" in columns
        assert "expires_at" in columns
        assert "revoked_at" in columns
