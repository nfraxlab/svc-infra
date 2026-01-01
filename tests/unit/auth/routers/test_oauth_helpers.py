"""Tests for OAuth router async helpers."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from svc_infra.api.fastapi.auth.routers.oauth_router import (
    _exchange_code_for_token,
    _extract_user_info_from_provider,
    _extract_user_info_github,
    _extract_user_info_linkedin,
    _extract_user_info_oidc,
    _find_or_create_user,
    _find_user_by_provider_link,
    _handle_mfa_redirect,
    _register_oauth_providers,
    _update_provider_account,
    _validate_and_decode_jwt_token,
    _validate_oauth_state,
)


class TestRegisterOAuthProviders:
    """Tests for OAuth provider registration."""

    def test_registers_oidc_provider(self) -> None:
        """Should register OIDC provider with metadata URL."""
        oauth = MagicMock()
        providers = {
            "google": {
                "kind": "oidc",
                "client_id": "client-id",
                "client_secret": "secret",
                "issuer": "https://accounts.google.com",
                "scope": "openid email profile",
            }
        }

        _register_oauth_providers(oauth, providers)

        oauth.register.assert_called_once()
        call_kwargs = oauth.register.call_args[1]
        assert call_kwargs["client_id"] == "client-id"
        assert "openid-configuration" in call_kwargs["server_metadata_url"]

    def test_registers_github_provider(self) -> None:
        """Should register GitHub provider with explicit URLs."""
        oauth = MagicMock()
        providers = {
            "github": {
                "kind": "github",
                "client_id": "gh-client-id",
                "client_secret": "gh-secret",
                "authorize_url": "https://github.com/login/oauth/authorize",
                "access_token_url": "https://github.com/login/oauth/access_token",
                "api_base_url": "https://api.github.com/",
            }
        }

        _register_oauth_providers(oauth, providers)

        oauth.register.assert_called_once()
        call_kwargs = oauth.register.call_args[1]
        assert call_kwargs["authorize_url"] == "https://github.com/login/oauth/authorize"

    def test_registers_linkedin_provider(self) -> None:
        """Should register LinkedIn provider."""
        oauth = MagicMock()
        providers = {
            "linkedin": {
                "kind": "linkedin",
                "client_id": "li-client-id",
                "client_secret": "li-secret",
                "authorize_url": "https://www.linkedin.com/oauth/v2/authorization",
                "access_token_url": "https://www.linkedin.com/oauth/v2/accessToken",
                "api_base_url": "https://api.linkedin.com/v2/",
            }
        }

        _register_oauth_providers(oauth, providers)

        oauth.register.assert_called_once()


class TestValidateOAuthState:
    """Tests for OAuth state validation."""

    @pytest.mark.asyncio
    async def test_valid_state_returns_session_values(self) -> None:
        """Should return verifier and nonce for valid state."""
        request = MagicMock()
        request.query_params = {"state": "valid-state"}
        request.session = {
            "oauth:google:state": "valid-state",
            "oauth:google:pkce_verifier": "verifier123",
            "oauth:google:nonce": "nonce456",
        }

        verifier, nonce = await _validate_oauth_state(request, "google")

        assert verifier == "verifier123"
        assert nonce == "nonce456"

    @pytest.mark.asyncio
    async def test_invalid_state_raises(self) -> None:
        """Should raise HTTPException for invalid state."""
        request = MagicMock()
        request.query_params = {"state": "wrong-state"}
        request.session = {"oauth:google:state": "expected-state"}

        with pytest.raises(HTTPException) as exc_info:
            await _validate_oauth_state(request, "google")

        assert exc_info.value.status_code == 400
        assert "invalid_state" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_missing_state_raises(self) -> None:
        """Should raise HTTPException when session state missing."""
        request = MagicMock()
        request.query_params = {"state": "some-state"}
        request.session = {}  # No state stored

        with pytest.raises(HTTPException) as exc_info:
            await _validate_oauth_state(request, "google")

        assert exc_info.value.status_code == 400


class TestExchangeCodeForToken:
    """Tests for OAuth code exchange."""

    @pytest.mark.asyncio
    async def test_successful_exchange(self) -> None:
        """Should return token on successful exchange."""
        client = AsyncMock()
        client.authorize_access_token = AsyncMock(
            return_value={"access_token": "token123", "token_type": "Bearer"}
        )
        request = MagicMock()

        result = await _exchange_code_for_token(client, request, "verifier", "google")

        assert result["access_token"] == "token123"

    @pytest.mark.asyncio
    async def test_oauth_error_returns_redirect(self) -> None:
        """Should return redirect response on OAuth error."""
        from authlib.integrations.base_client.errors import OAuthError

        client = AsyncMock()
        client.authorize_access_token = AsyncMock(
            side_effect=OAuthError(error="access_denied", description="User denied")
        )
        request = MagicMock()
        request.session = {}

        with patch(
            "svc_infra.api.fastapi.auth.routers.oauth_router.get_auth_settings"
        ) as mock_settings:
            mock_settings.return_value.post_login_redirect = "/login"
            result = await _exchange_code_for_token(client, request, "verifier", "google")

        # Should return a redirect response, not raise
        assert result.status_code == 302


class TestExtractUserInfoOIDC:
    """Tests for OIDC user info extraction."""

    @pytest.mark.asyncio
    async def test_extracts_from_id_token(self) -> None:
        """Should extract user info from ID token."""
        request = MagicMock()
        client = AsyncMock()
        client.parse_id_token = AsyncMock(
            return_value={
                "sub": "user-123",
                "email": "user@example.com",
                "name": "Test User",
                "email_verified": True,
            }
        )
        token = {"id_token": "jwt-token", "access_token": "access"}

        email, name, user_id, verified, claims = await _extract_user_info_oidc(
            request, client, token, nonce="nonce123"
        )

        assert email == "user@example.com"
        assert name == "Test User"
        assert user_id == "user-123"
        assert verified is True

    @pytest.mark.asyncio
    async def test_falls_back_to_userinfo(self) -> None:
        """Should fall back to userinfo endpoint if no ID token."""
        request = MagicMock()
        client = AsyncMock()
        client.userinfo = AsyncMock(
            return_value={
                "sub": "user-456",
                "email": "fallback@example.com",
                "name": "Fallback User",
            }
        )
        token = {"access_token": "access"}  # No id_token

        email, name, user_id, verified, claims = await _extract_user_info_oidc(
            request, client, token, nonce=None
        )

        assert email == "fallback@example.com"

    @pytest.mark.asyncio
    async def test_invalid_nonce_raises(self) -> None:
        """Should raise if nonce doesn't match."""
        request = MagicMock()
        client = AsyncMock()
        client.parse_id_token = AsyncMock(
            return_value={
                "sub": "user-123",
                "email": "user@example.com",
                "nonce": "wrong-nonce",
            }
        )
        token = {"id_token": "jwt-token"}

        with pytest.raises(HTTPException) as exc_info:
            await _extract_user_info_oidc(request, client, token, nonce="expected-nonce")

        assert exc_info.value.status_code == 400
        assert "invalid_nonce" in str(exc_info.value.detail)


class TestExtractUserInfoGitHub:
    """Tests for GitHub user info extraction."""

    @pytest.mark.asyncio
    async def test_extracts_github_user_info(self) -> None:
        """Should extract user info from GitHub API."""
        client = AsyncMock()

        user_response = MagicMock()
        user_response.json.return_value = {
            "id": 12345,
            "login": "testuser",
            "name": "Test User",
        }

        emails_response = MagicMock()
        emails_response.json.return_value = [
            {"email": "test@example.com", "primary": True, "verified": True}
        ]

        client.get = AsyncMock(
            side_effect=lambda path, token: user_response if path == "user" else emails_response
        )

        token = {"access_token": "gh-token"}

        email, name, user_id, verified, claims = await _extract_user_info_github(client, token)

        assert email == "test@example.com"
        assert name == "Test User"
        assert user_id == "12345"
        assert verified is True

    @pytest.mark.asyncio
    async def test_rejects_unverified_email(self) -> None:
        """Should raise if no verified primary email."""
        client = AsyncMock()

        user_response = MagicMock()
        user_response.json.return_value = {"id": 12345}

        emails_response = MagicMock()
        emails_response.json.return_value = [
            {"email": "test@example.com", "primary": True, "verified": False}
        ]

        client.get = AsyncMock(
            side_effect=lambda path, token: user_response if path == "user" else emails_response
        )

        with pytest.raises(HTTPException) as exc_info:
            await _extract_user_info_github(client, {"access_token": "token"})

        assert exc_info.value.status_code == 400
        assert "unverified_email" in str(exc_info.value.detail)


class TestExtractUserInfoLinkedIn:
    """Tests for LinkedIn user info extraction."""

    @pytest.mark.asyncio
    async def test_extracts_linkedin_user_info(self) -> None:
        """Should extract user info from LinkedIn API."""
        client = AsyncMock()

        me_response = MagicMock()
        me_response.json.return_value = {
            "id": "linkedin-123",
            "firstName": {"localized": {"en_US": "Test"}},
            "lastName": {"localized": {"en_US": "User"}},
        }

        email_response = MagicMock()
        email_response.json.return_value = {
            "elements": [{"handle~": {"emailAddress": "linkedin@example.com"}}]
        }

        async def mock_get(path, token):
            if "emailAddress" in path:
                return email_response
            return me_response

        client.get = mock_get

        token = {"access_token": "li-token"}

        email, name, user_id, verified, claims = await _extract_user_info_linkedin(client, token)

        assert email == "linkedin@example.com"
        assert name == "Test User"
        assert user_id == "linkedin-123"


class TestExtractUserInfoFromProvider:
    """Tests for provider-agnostic user info extraction."""

    @pytest.mark.asyncio
    async def test_routes_to_oidc(self) -> None:
        """Should route to OIDC extraction for OIDC providers."""
        request = MagicMock()
        client = AsyncMock()
        client.userinfo = AsyncMock(return_value={"sub": "123", "email": "test@test.com"})
        token = {"access_token": "token"}
        cfg = {"kind": "oidc"}

        email, *_ = await _extract_user_info_from_provider(
            request, client, token, "google", cfg, nonce=None
        )

        assert email == "test@test.com"

    @pytest.mark.asyncio
    async def test_routes_to_github(self) -> None:
        """Should route to GitHub extraction for GitHub providers."""
        request = MagicMock()
        client = AsyncMock()

        user_resp = MagicMock()
        user_resp.json.return_value = {"id": 1, "name": "GH User"}

        email_resp = MagicMock()
        email_resp.json.return_value = [{"email": "gh@test.com", "primary": True, "verified": True}]

        client.get = AsyncMock(
            side_effect=lambda p, token: user_resp if p == "user" else email_resp
        )

        cfg = {"kind": "github"}

        email, *_ = await _extract_user_info_from_provider(request, client, {}, "github", cfg)

        assert email == "gh@test.com"

    @pytest.mark.asyncio
    async def test_unsupported_provider_raises(self) -> None:
        """Should raise for unsupported provider kinds."""
        request = MagicMock()
        client = AsyncMock()
        cfg = {"kind": "unknown"}

        with pytest.raises(HTTPException) as exc_info:
            await _extract_user_info_from_provider(request, client, {}, "unknown", cfg)

        assert exc_info.value.status_code == 400


class TestFindOrCreateUser:
    """Tests for user finding/creation."""

    @pytest.mark.asyncio
    async def test_finds_existing_user(self) -> None:
        """Should return existing user by email."""
        session = AsyncMock()
        existing_user = MagicMock(id="user-123", email="test@example.com")

        execute_result = MagicMock()
        execute_result.scalars.return_value.first.return_value = existing_user
        session.execute = AsyncMock(return_value=execute_result)

        # Need to patch select to avoid SQLAlchemy validation
        with patch("svc_infra.api.fastapi.auth.routers.oauth_router.select") as mock_select:
            mock_select.return_value.filter_by.return_value = MagicMock()

            result = await _find_or_create_user(session, MagicMock, "test@example.com", "Test User")

        assert result == existing_user
        session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_creates_new_user(self) -> None:
        """Should create new user if not found."""
        session = AsyncMock()

        execute_result = MagicMock()
        execute_result.scalars.return_value.first.return_value = None
        session.execute = AsyncMock(return_value=execute_result)

        user_model = MagicMock()
        user_model.return_value = MagicMock(id="new-user")

        with patch("svc_infra.api.fastapi.auth.routers.oauth_router.select") as mock_select:
            mock_select.return_value.filter_by.return_value = MagicMock()

            await _find_or_create_user(session, user_model, "new@example.com", "New User")

        session.add.assert_called_once()
        session.flush.assert_called_once()


class TestFindUserByProviderLink:
    """Tests for user lookup by provider account."""

    @pytest.mark.asyncio
    async def test_finds_linked_user(self) -> None:
        """Should find user by provider account link."""
        session = AsyncMock()
        user = MagicMock(id="user-123")

        link = MagicMock(user_id="user-123")
        execute_result = MagicMock()
        execute_result.scalars.return_value.first.return_value = link
        session.execute = AsyncMock(return_value=execute_result)
        session.get = AsyncMock(return_value=user)

        provider_model = MagicMock()
        user_model = MagicMock()

        with patch("svc_infra.api.fastapi.auth.routers.oauth_router.select") as mock_select:
            mock_select.return_value.filter_by.return_value = MagicMock()

            result = await _find_user_by_provider_link(
                session, provider_model, user_model, "google", "provider-user-123"
            )

        assert result == user

    @pytest.mark.asyncio
    async def test_returns_none_if_no_link(self) -> None:
        """Should return None if no provider link exists."""
        session = AsyncMock()

        execute_result = MagicMock()
        execute_result.scalars.return_value.first.return_value = None
        session.execute = AsyncMock(return_value=execute_result)

        with patch("svc_infra.api.fastapi.auth.routers.oauth_router.select") as mock_select:
            mock_select.return_value.filter_by.return_value = MagicMock()

            result = await _find_user_by_provider_link(
                session, MagicMock(), MagicMock(), "google", "unknown-id"
            )

        assert result is None

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_if_no_model(self) -> None:
        """Should return None if provider account model is None."""
        result = await _find_user_by_provider_link(
            AsyncMock(), None, MagicMock(), "google", "user-id"
        )

        assert result is None


class TestUpdateProviderAccount:
    """Tests for provider account creation/update."""

    @pytest.mark.asyncio
    async def test_creates_new_link(self) -> None:
        """Should create new provider account link."""
        session = AsyncMock()

        execute_result = MagicMock()
        execute_result.scalars.return_value.first.return_value = None
        session.execute = AsyncMock(return_value=execute_result)

        provider_model = MagicMock()
        user = MagicMock(id="user-123")
        token = {"access_token": "token", "refresh_token": "refresh"}

        with patch("svc_infra.api.fastapi.auth.routers.oauth_router.select") as mock_select:
            mock_select.return_value.filter_by.return_value = MagicMock()

            await _update_provider_account(
                session, provider_model, user, "google", "provider-123", token, {}
            )

        session.add.assert_called_once()
        session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_existing_link(self) -> None:
        """Should update existing provider account link."""
        session = AsyncMock()

        existing_link = MagicMock()
        existing_link.access_token = "old-token"
        existing_link.refresh_token = None

        execute_result = MagicMock()
        execute_result.scalars.return_value.first.return_value = existing_link
        session.execute = AsyncMock(return_value=execute_result)

        provider_model = MagicMock()
        user = MagicMock(id="user-123")
        token = {"access_token": "new-token", "refresh_token": "new-refresh"}

        with patch("svc_infra.api.fastapi.auth.routers.oauth_router.select") as mock_select:
            mock_select.return_value.filter_by.return_value = MagicMock()

            await _update_provider_account(
                session, provider_model, user, "google", "provider-123", token, {}
            )

        assert existing_link.access_token == "new-token"
        session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_if_no_model(self) -> None:
        """Should skip if provider account model is None."""
        session = AsyncMock()

        await _update_provider_account(session, None, MagicMock(), "google", "id", {}, {})

        session.execute.assert_not_called()


class TestValidateAndDecodeJwtToken:
    """Tests for JWT token validation."""

    @pytest.mark.asyncio
    async def test_decodes_valid_token(self) -> None:
        """Should decode valid JWT and return user ID."""
        import jwt

        secret = "test-secret"
        token = jwt.encode(
            {"sub": "user-123", "aud": ["fastapi-users:auth"]},
            secret,
            algorithm="HS256",
        )

        with patch(
            "svc_infra.api.fastapi.auth.routers.oauth_router.get_auth_settings"
        ) as mock_settings:
            mock_jwt = MagicMock()
            mock_jwt.secret.get_secret_value.return_value = secret
            mock_settings.return_value.jwt = mock_jwt

            result = await _validate_and_decode_jwt_token(token)

        assert result == "user-123"

    @pytest.mark.asyncio
    async def test_rejects_invalid_token(self) -> None:
        """Should raise for invalid token."""
        with patch(
            "svc_infra.api.fastapi.auth.routers.oauth_router.get_auth_settings"
        ) as mock_settings:
            mock_jwt = MagicMock()
            mock_jwt.secret.get_secret_value.return_value = "secret"
            mock_settings.return_value.jwt = mock_jwt

            with pytest.raises(HTTPException) as exc_info:
                await _validate_and_decode_jwt_token("invalid-token")

            assert exc_info.value.status_code == 401


class TestHandleMfaRedirect:
    """Tests for MFA redirect handling."""

    @pytest.mark.asyncio
    async def test_returns_none_if_mfa_not_required(self) -> None:
        """Should return None if MFA not required."""
        policy = AsyncMock()
        policy.should_require_mfa = AsyncMock(return_value=False)
        user = MagicMock()

        result = await _handle_mfa_redirect(policy, user, "/dashboard")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_redirect_if_mfa_required(self) -> None:
        """Should return redirect if MFA required."""
        policy = AsyncMock()
        policy.should_require_mfa = AsyncMock(return_value=True)
        user = MagicMock()

        with patch(
            "svc_infra.api.fastapi.auth.routers.oauth_router.get_mfa_pre_jwt_writer"
        ) as mock_writer:
            mock_writer.return_value.write = AsyncMock(return_value="pre-token")

            result = await _handle_mfa_redirect(policy, user, "/dashboard")

        assert result is not None
        assert result.status_code == 302
        assert "mfa=required" in str(result.headers.get("location", ""))
