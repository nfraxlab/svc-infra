"""Unit tests for svc_infra.api.fastapi.auth._cookies module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from starlette.requests import Request


class TestIsLocalHost:
    """Tests for _is_local_host function."""

    def test_localhost(self) -> None:
        """Test localhost detection."""
        from svc_infra.api.fastapi.auth._cookies import _is_local_host

        assert _is_local_host("localhost") is True
        assert _is_local_host("localhost:8000") is True

    def test_127_0_0_1(self) -> None:
        """Test 127.0.0.1 detection."""
        from svc_infra.api.fastapi.auth._cookies import _is_local_host

        assert _is_local_host("127.0.0.1") is True
        assert _is_local_host("127.0.0.1:3000") is True

    def test_ipv6_localhost(self) -> None:
        """Test IPv6 localhost - note: current impl doesn't handle ::1 correctly due to split."""
        from svc_infra.api.fastapi.auth._cookies import _is_local_host

        # The current implementation splits by ":" which breaks IPv6
        # This tests the actual behavior, not ideal behavior
        assert _is_local_host("::1") is False  # Known limitation

    def test_subdomain_localhost(self) -> None:
        """Test subdomain.localhost detection."""
        from svc_infra.api.fastapi.auth._cookies import _is_local_host

        assert _is_local_host("app.localhost") is True
        assert _is_local_host("api.localhost:8080") is True

    def test_non_local_hosts(self) -> None:
        """Test non-local hosts return False."""
        from svc_infra.api.fastapi.auth._cookies import _is_local_host

        assert _is_local_host("example.com") is False
        assert _is_local_host("api.example.com") is False
        assert _is_local_host("192.168.1.1") is False

    def test_empty_host(self) -> None:
        """Test empty host returns False."""
        from svc_infra.api.fastapi.auth._cookies import _is_local_host

        assert _is_local_host("") is False


class TestIsHttps:
    """Tests for _is_https function."""

    def test_https_from_url_scheme(self) -> None:
        """Test HTTPS detection from URL scheme."""
        from svc_infra.api.fastapi.auth._cookies import _is_https

        request = MagicMock(spec=Request)
        request.headers = {}
        request.url.scheme = "https"

        assert _is_https(request) is True

    def test_http_from_url_scheme(self) -> None:
        """Test HTTP detection from URL scheme."""
        from svc_infra.api.fastapi.auth._cookies import _is_https

        request = MagicMock(spec=Request)
        request.headers = {}
        request.url.scheme = "http"

        assert _is_https(request) is False

    def test_https_from_forwarded_proto(self) -> None:
        """Test HTTPS detection from X-Forwarded-Proto header."""
        from svc_infra.api.fastapi.auth._cookies import _is_https

        request = MagicMock(spec=Request)
        request.headers = {"x-forwarded-proto": "https"}
        request.url.scheme = "http"

        assert _is_https(request) is True

    def test_http_from_forwarded_proto(self) -> None:
        """Test HTTP detection from X-Forwarded-Proto header."""
        from svc_infra.api.fastapi.auth._cookies import _is_https

        request = MagicMock(spec=Request)
        request.headers = {"x-forwarded-proto": "http"}
        request.url.scheme = "https"

        assert _is_https(request) is False

    def test_forwarded_proto_multiple_values(self) -> None:
        """Test X-Forwarded-Proto with multiple values takes first."""
        from svc_infra.api.fastapi.auth._cookies import _is_https

        request = MagicMock(spec=Request)
        request.headers = {"x-forwarded-proto": "https, http"}
        request.url.scheme = "http"

        assert _is_https(request) is True


class TestComputeCookieParams:
    """Tests for compute_cookie_params function."""

    @patch("svc_infra.api.fastapi.auth._cookies.get_auth_settings")
    def test_basic_cookie_params(self, mock_settings: MagicMock) -> None:
        """Test basic cookie parameter computation."""
        from svc_infra.api.fastapi.auth._cookies import compute_cookie_params

        mock_settings.return_value = MagicMock(
            session_cookie_domain="",
            session_cookie_secure=True,
            session_cookie_samesite="lax",
            session_cookie_max_age_seconds=3600,
        )

        request = MagicMock(spec=Request)
        request.headers = {}
        request.url.scheme = "https"

        params = compute_cookie_params(request, name="auth_token")

        assert params["key"] == "auth_token"
        assert params["httponly"] is True
        assert params["secure"] is True
        assert params["samesite"] == "lax"
        assert params["path"] == "/"
        assert params["max_age"] == 3600

    @patch("svc_infra.api.fastapi.auth._cookies.get_auth_settings")
    def test_domain_set_for_non_localhost(self, mock_settings: MagicMock) -> None:
        """Test domain is set for non-localhost."""
        from svc_infra.api.fastapi.auth._cookies import compute_cookie_params

        mock_settings.return_value = MagicMock(
            session_cookie_domain="example.com",
            session_cookie_secure=True,
            session_cookie_samesite="strict",
            session_cookie_max_age_seconds=7200,
        )

        request = MagicMock(spec=Request)
        request.headers = {}
        request.url.scheme = "https"

        params = compute_cookie_params(request, name="session")

        assert params["domain"] == "example.com"
        assert params["samesite"] == "strict"
        assert params["max_age"] == 7200

    @patch("svc_infra.api.fastapi.auth._cookies.get_auth_settings")
    def test_domain_none_for_localhost(self, mock_settings: MagicMock) -> None:
        """Test domain is None for localhost."""
        from svc_infra.api.fastapi.auth._cookies import compute_cookie_params

        mock_settings.return_value = MagicMock(
            session_cookie_domain="localhost",
            session_cookie_secure=False,
            session_cookie_samesite="lax",
            session_cookie_max_age_seconds=3600,
        )

        request = MagicMock(spec=Request)
        request.headers = {}
        request.url.scheme = "http"

        params = compute_cookie_params(request, name="token")

        assert params["domain"] is None

    @patch("svc_infra.api.fastapi.auth._cookies.IS_PROD", True)
    @patch("svc_infra.api.fastapi.auth._cookies.get_auth_settings")
    def test_secure_true_in_prod(self, mock_settings: MagicMock) -> None:
        """Test secure is True in production when not explicitly set."""
        from svc_infra.api.fastapi.auth._cookies import compute_cookie_params

        mock_settings.return_value = MagicMock(
            session_cookie_domain="",
            session_cookie_secure=None,
            session_cookie_samesite="lax",
            session_cookie_max_age_seconds=3600,
        )

        request = MagicMock(spec=Request)
        request.headers = {}
        request.url.scheme = "http"

        params = compute_cookie_params(request, name="token")

        assert params["secure"] is True
