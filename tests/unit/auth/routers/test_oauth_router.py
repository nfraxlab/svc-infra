"""Tests for svc_infra.api.fastapi.auth.routers.oauth_router module."""

from __future__ import annotations

import base64
import hashlib
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from svc_infra.api.fastapi.auth.routers.oauth_router import (
    _clean_oauth_session_state,
    _coerce_expires_at,
    _cookie_domain,
    _cookie_name,
    _determine_final_redirect_url,
    _gen_pkce_pair,
    _handle_oauth_error,
    _validate_redirect,
)


class TestGenPkcePair:
    """Tests for PKCE pair generation."""

    def test_generates_verifier_and_challenge(self) -> None:
        """Should generate both verifier and challenge."""
        verifier, challenge = _gen_pkce_pair()
        assert verifier is not None
        assert challenge is not None
        assert len(verifier) > 0
        assert len(challenge) > 0

    def test_verifier_and_challenge_are_different(self) -> None:
        """Should generate different verifier and challenge."""
        verifier, challenge = _gen_pkce_pair()
        assert verifier != challenge

    def test_challenge_is_sha256_of_verifier(self) -> None:
        """Challenge should be base64-encoded SHA256 of verifier."""
        verifier, challenge = _gen_pkce_pair()
        # Verify the challenge is correctly derived from verifier
        digest = hashlib.sha256(verifier.encode()).digest()
        expected_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        assert challenge == expected_challenge

    def test_generates_unique_pairs(self) -> None:
        """Should generate unique pairs each time."""
        pairs = [_gen_pkce_pair() for _ in range(10)]
        verifiers = [p[0] for p in pairs]
        challenges = [p[1] for p in pairs]
        assert len(set(verifiers)) == 10
        assert len(set(challenges)) == 10


class TestValidateRedirect:
    """Tests for redirect URL validation."""

    def test_allows_relative_url(self) -> None:
        """Should allow relative URLs."""
        # Should not raise
        _validate_redirect("/dashboard", [], require_https=False)

    def test_allows_whitelisted_host(self) -> None:
        """Should allow whitelisted hosts."""
        _validate_redirect(
            "https://app.example.com/callback",
            ["app.example.com"],
            require_https=False,
        )

    def test_allows_host_with_port(self) -> None:
        """Should allow host with port when whitelisted."""
        _validate_redirect(
            "http://localhost:3000/callback",
            ["localhost:3000"],
            require_https=False,
        )

    def test_rejects_non_whitelisted_host(self) -> None:
        """Should reject hosts not in whitelist."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_redirect(
                "https://evil.com/steal",
                ["app.example.com"],
                require_https=False,
            )
        assert exc_info.value.status_code == 400
        assert "redirect_not_allowed" in str(exc_info.value.detail)

    def test_rejects_http_when_https_required(self) -> None:
        """Should reject HTTP URLs when HTTPS required."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_redirect(
                "http://app.example.com/callback",
                ["app.example.com"],
                require_https=True,
            )
        assert exc_info.value.status_code == 400
        assert "https_required" in str(exc_info.value.detail)

    def test_allows_https_when_required(self) -> None:
        """Should allow HTTPS URLs when HTTPS required."""
        # Should not raise
        _validate_redirect(
            "https://app.example.com/callback",
            ["app.example.com"],
            require_https=True,
        )


class TestCoerceExpiresAt:
    """Tests for OAuth token expiration parsing."""

    def test_none_input(self) -> None:
        """Should return None for None input."""
        assert _coerce_expires_at(None) is None

    def test_non_dict_input(self) -> None:
        """Should return None for non-dict input."""
        assert _coerce_expires_at("not a dict") is None  # type: ignore

    def test_extracts_expires_at_seconds(self) -> None:
        """Should extract expires_at in seconds."""
        now = datetime.now(UTC).timestamp()
        token = {"expires_at": now + 3600}
        result = _coerce_expires_at(token)
        assert result is not None
        # Should be approximately 1 hour from now
        assert abs((result - datetime.now(UTC)).total_seconds() - 3600) < 2

    def test_extracts_expires_at_milliseconds(self) -> None:
        """Should handle expires_at in milliseconds."""
        now_ms = datetime.now(UTC).timestamp() * 1000 + 3600000
        token = {"expires_at": now_ms}
        result = _coerce_expires_at(token)
        assert result is not None
        # Should be approximately 1 hour from now
        assert abs((result - datetime.now(UTC)).total_seconds() - 3600) < 2

    def test_extracts_expires_in(self) -> None:
        """Should calculate expiry from expires_in."""
        token = {"expires_in": 3600}  # 1 hour
        result = _coerce_expires_at(token)
        assert result is not None
        assert abs((result - datetime.now(UTC)).total_seconds() - 3600) < 2

    def test_prefers_expires_at_over_expires_in(self) -> None:
        """Should prefer expires_at when both present."""
        future = datetime.now(UTC) + timedelta(hours=2)
        token = {"expires_at": future.timestamp(), "expires_in": 3600}
        result = _coerce_expires_at(token)
        assert result is not None
        # Should be ~2 hours, not ~1 hour
        assert abs((result - datetime.now(UTC)).total_seconds() - 7200) < 2

    def test_returns_none_for_invalid_values(self) -> None:
        """Should return None for invalid expires values."""
        assert _coerce_expires_at({"expires_at": "invalid"}) is None
        assert _coerce_expires_at({"expires_in": "not-a-number"}) is None


class TestCookieName:
    """Tests for cookie name generation."""

    def test_returns_default_name(self) -> None:
        """Should return default cookie name."""
        st = MagicMock()
        st.auth_cookie_name = "svc_auth"
        st.session_cookie_secure = False
        st.session_cookie_domain = None
        assert _cookie_name(st) == "svc_auth"

    def test_adds_host_prefix_when_secure(self) -> None:
        """Should add __Host- prefix when secure and no domain."""
        st = MagicMock()
        st.auth_cookie_name = "svc_auth"
        st.session_cookie_secure = True
        st.session_cookie_domain = None
        assert _cookie_name(st) == "__Host-svc_auth"

    def test_no_prefix_when_domain_set(self) -> None:
        """Should not add prefix when domain is set."""
        st = MagicMock()
        st.auth_cookie_name = "svc_auth"
        st.session_cookie_secure = True
        st.session_cookie_domain = ".example.com"
        assert _cookie_name(st) == "svc_auth"

    def test_no_double_prefix(self) -> None:
        """Should not add prefix if already present."""
        st = MagicMock()
        st.auth_cookie_name = "__Host-svc_auth"
        st.session_cookie_secure = True
        st.session_cookie_domain = None
        assert _cookie_name(st) == "__Host-svc_auth"


class TestCookieDomain:
    """Tests for cookie domain extraction."""

    def test_returns_domain(self) -> None:
        """Should return configured domain."""
        st = MagicMock()
        st.session_cookie_domain = ".example.com"
        assert _cookie_domain(st) == ".example.com"

    def test_returns_none_for_empty(self) -> None:
        """Should return None for empty domain."""
        st = MagicMock()
        st.session_cookie_domain = ""
        assert _cookie_domain(st) is None

    def test_returns_none_when_not_set(self) -> None:
        """Should return None when domain not set."""
        st = MagicMock(spec=[])  # No session_cookie_domain attribute
        assert _cookie_domain(st) is None


class TestHandleOAuthError:
    """Tests for OAuth error handling."""

    def test_returns_redirect_response(self) -> None:
        """Should return a redirect response."""
        request = MagicMock()
        request.session = {}

        with patch(
            "svc_infra.api.fastapi.auth.routers.oauth_router.get_auth_settings"
        ) as mock_settings:
            mock_settings.return_value.post_login_redirect = "/login"
            response = _handle_oauth_error(request, "google", "access_denied", "User denied")

        assert response.status_code == 302
        assert "oauth_error=access_denied" in str(response.headers.get("location", ""))

    def test_clears_session_state(self) -> None:
        """Should clear OAuth session state."""
        request = MagicMock()
        request.session = {
            "oauth:google:state": "some-state",
            "oauth:google:pkce_verifier": "verifier",
            "oauth:google:nonce": "nonce",
            "oauth:google:next": "/dashboard",
        }

        with patch(
            "svc_infra.api.fastapi.auth.routers.oauth_router.get_auth_settings"
        ) as mock_settings:
            mock_settings.return_value.post_login_redirect = "/login"
            _handle_oauth_error(request, "google", "error", "desc")

        # All session values should be cleared
        assert "oauth:google:state" not in request.session
        assert "oauth:google:pkce_verifier" not in request.session


class TestCleanOAuthSessionState:
    """Tests for session state cleanup."""

    def test_cleans_all_oauth_keys(self) -> None:
        """Should clean all OAuth-related session keys."""
        request = MagicMock()
        request.session = {
            "oauth:github:state": "state123",
            "oauth:github:pkce_verifier": "verifier",
            "oauth:github:nonce": "nonce",
            "oauth:github:next": "/dashboard",
            "other_key": "preserved",
        }

        _clean_oauth_session_state(request, "github")

        assert "oauth:github:state" not in request.session
        assert "oauth:github:pkce_verifier" not in request.session
        assert "oauth:github:nonce" not in request.session
        assert "oauth:github:next" not in request.session
        assert request.session.get("other_key") == "preserved"

    def test_handles_missing_keys(self) -> None:
        """Should handle missing session keys gracefully."""
        request = MagicMock()
        request.session = {}

        # Should not raise
        _clean_oauth_session_state(request, "google")


class TestDetermineRedirectUrl:
    """Tests for final redirect URL determination."""

    def test_uses_post_login_redirect(self) -> None:
        """Should use post_login_redirect by default."""
        request = MagicMock()
        request.query_params = {}
        request.session = {}

        with patch(
            "svc_infra.api.fastapi.auth.routers.oauth_router.get_auth_settings"
        ) as mock_settings:
            mock_settings.return_value.post_login_redirect = "/default"
            mock_settings.return_value.redirect_allow_hosts_raw = None
            mock_settings.return_value.session_cookie_secure = False

            result = _determine_final_redirect_url(request, "google", "/dashboard")

        assert result == "/dashboard"

    def test_prefers_next_query_param(self) -> None:
        """Should prefer ?next query parameter."""
        request = MagicMock()
        request.query_params = {"next": "/profile"}
        request.session = {}

        with patch(
            "svc_infra.api.fastapi.auth.routers.oauth_router.get_auth_settings"
        ) as mock_settings:
            mock_settings.return_value.post_login_redirect = "/default"
            mock_settings.return_value.redirect_allow_hosts_raw = None
            mock_settings.return_value.session_cookie_secure = False

            result = _determine_final_redirect_url(request, "google", "/dashboard")

        assert result == "/profile"

    def test_uses_stashed_next_from_session(self) -> None:
        """Should use stashed next from session if query param not present."""
        request = MagicMock()
        request.query_params = {}
        request.session = {"oauth:google:next": "/settings"}

        with patch(
            "svc_infra.api.fastapi.auth.routers.oauth_router.get_auth_settings"
        ) as mock_settings:
            mock_settings.return_value.post_login_redirect = "/default"
            mock_settings.return_value.redirect_allow_hosts_raw = None
            mock_settings.return_value.session_cookie_secure = False

            result = _determine_final_redirect_url(request, "google", "/dashboard")

        assert result == "/settings"
