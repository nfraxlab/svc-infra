"""Unit tests for svc_infra.api.fastapi.auth.gaurd module - login_client_gaurd."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class TestLoginClientGuard:
    """Tests for login_client_gaurd function."""

    @pytest.mark.asyncio
    @patch("svc_infra.api.fastapi.auth.gaurd.get_auth_settings")
    async def test_skips_when_setting_disabled(self, mock_settings: MagicMock) -> None:
        """Test guard is skipped when require_client_secret_on_password_login is False."""
        from svc_infra.api.fastapi.auth.gaurd import login_client_gaurd

        mock_settings.return_value = MagicMock(
            require_client_secret_on_password_login=False,
        )

        request = MagicMock()
        request.method = "POST"
        request.url.path = "/auth/login"

        # Should not raise, just return None
        result = await login_client_gaurd(request)
        assert result is None

    @pytest.mark.asyncio
    @patch("svc_infra.api.fastapi.auth.gaurd.get_auth_settings")
    async def test_skips_for_non_login_endpoints(self, mock_settings: MagicMock) -> None:
        """Test guard is skipped for non-login endpoints."""
        from svc_infra.api.fastapi.auth.gaurd import login_client_gaurd

        mock_settings.return_value = MagicMock(
            require_client_secret_on_password_login=True,
            password_clients=[],
        )

        request = MagicMock()
        request.method = "POST"
        request.url.path = "/auth/register"

        # Should not raise for non-login path
        result = await login_client_gaurd(request)
        assert result is None

    @pytest.mark.asyncio
    @patch("svc_infra.api.fastapi.auth.gaurd.get_auth_settings")
    async def test_skips_for_get_requests(self, mock_settings: MagicMock) -> None:
        """Test guard is skipped for GET requests."""
        from svc_infra.api.fastapi.auth.gaurd import login_client_gaurd

        mock_settings.return_value = MagicMock(
            require_client_secret_on_password_login=True,
            password_clients=[],
        )

        request = MagicMock()
        request.method = "GET"
        request.url.path = "/auth/login"

        # Should not raise for GET
        result = await login_client_gaurd(request)
        assert result is None

    @pytest.mark.asyncio
    @patch("svc_infra.api.fastapi.auth.gaurd.get_auth_settings")
    async def test_raises_when_missing_credentials(self, mock_settings: MagicMock) -> None:
        """Test guard raises 401 when client credentials are missing."""
        from svc_infra.api.fastapi.auth.gaurd import login_client_gaurd

        mock_settings.return_value = MagicMock(
            require_client_secret_on_password_login=True,
            password_clients=[],
        )

        request = MagicMock()
        request.method = "POST"
        request.url.path = "/auth/login"
        request.form = AsyncMock(return_value={})

        with pytest.raises(HTTPException) as exc_info:
            await login_client_gaurd(request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "client_credentials_required"

    @pytest.mark.asyncio
    @patch("svc_infra.api.fastapi.auth.gaurd.get_auth_settings")
    async def test_raises_when_only_client_id_provided(self, mock_settings: MagicMock) -> None:
        """Test guard raises 401 when only client_id is provided."""
        from svc_infra.api.fastapi.auth.gaurd import login_client_gaurd

        mock_settings.return_value = MagicMock(
            require_client_secret_on_password_login=True,
            password_clients=[],
        )

        request = MagicMock()
        request.method = "POST"
        request.url.path = "/auth/login"
        request.form = AsyncMock(return_value={"client_id": "my-client"})

        with pytest.raises(HTTPException) as exc_info:
            await login_client_gaurd(request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "client_credentials_required"

    @pytest.mark.asyncio
    @patch("svc_infra.api.fastapi.auth.gaurd.get_auth_settings")
    async def test_raises_for_invalid_client_credentials(self, mock_settings: MagicMock) -> None:
        """Test guard raises 401 for invalid client credentials."""
        from svc_infra.api.fastapi.auth.gaurd import login_client_gaurd

        valid_client = MagicMock()
        valid_client.client_id = "valid-client"
        valid_client.client_secret = MagicMock()
        valid_client.client_secret.get_secret_value.return_value = "valid-secret"

        mock_settings.return_value = MagicMock(
            require_client_secret_on_password_login=True,
            password_clients=[valid_client],
        )

        request = MagicMock()
        request.method = "POST"
        request.url.path = "/auth/login"
        request.form = AsyncMock(
            return_value={
                "client_id": "invalid-client",
                "client_secret": "wrong-secret",
            }
        )

        with pytest.raises(HTTPException) as exc_info:
            await login_client_gaurd(request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "invalid_client_credentials"

    @pytest.mark.asyncio
    @patch("svc_infra.api.fastapi.auth.gaurd.get_auth_settings")
    async def test_passes_with_valid_client_credentials(self, mock_settings: MagicMock) -> None:
        """Test guard passes with valid client credentials."""
        from svc_infra.api.fastapi.auth.gaurd import login_client_gaurd

        valid_client = MagicMock()
        valid_client.client_id = "valid-client"
        valid_client.client_secret = MagicMock()
        valid_client.client_secret.get_secret_value.return_value = "valid-secret"

        mock_settings.return_value = MagicMock(
            require_client_secret_on_password_login=True,
            password_clients=[valid_client],
        )

        request = MagicMock()
        request.method = "POST"
        request.url.path = "/auth/login"
        request.form = AsyncMock(
            return_value={
                "client_id": "valid-client",
                "client_secret": "valid-secret",
            }
        )

        # Should not raise
        result = await login_client_gaurd(request)
        assert result is None

    @pytest.mark.asyncio
    @patch("svc_infra.api.fastapi.auth.gaurd.get_auth_settings")
    async def test_handles_form_parse_error(self, mock_settings: MagicMock) -> None:
        """Test guard handles form parsing errors gracefully."""
        from svc_infra.api.fastapi.auth.gaurd import login_client_gaurd

        mock_settings.return_value = MagicMock(
            require_client_secret_on_password_login=True,
            password_clients=[],
        )

        request = MagicMock()
        request.method = "POST"
        request.url.path = "/auth/login"
        request.form = AsyncMock(side_effect=Exception("Parse error"))

        with pytest.raises(HTTPException) as exc_info:
            await login_client_gaurd(request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "client_credentials_required"

    @pytest.mark.asyncio
    @patch("svc_infra.api.fastapi.auth.gaurd.get_auth_settings")
    async def test_strips_whitespace_from_credentials(self, mock_settings: MagicMock) -> None:
        """Test guard strips whitespace from credentials."""
        from svc_infra.api.fastapi.auth.gaurd import login_client_gaurd

        valid_client = MagicMock()
        valid_client.client_id = "valid-client"
        valid_client.client_secret = MagicMock()
        valid_client.client_secret.get_secret_value.return_value = "valid-secret"

        mock_settings.return_value = MagicMock(
            require_client_secret_on_password_login=True,
            password_clients=[valid_client],
        )

        request = MagicMock()
        request.method = "POST"
        request.url.path = "/auth/login"
        request.form = AsyncMock(
            return_value={
                "client_id": "  valid-client  ",
                "client_secret": "  valid-secret  ",
            }
        )

        # Should pass after stripping whitespace
        result = await login_client_gaurd(request)
        assert result is None

    @pytest.mark.asyncio
    @patch("svc_infra.api.fastapi.auth.gaurd.get_auth_settings")
    async def test_multiple_clients_finds_matching(self, mock_settings: MagicMock) -> None:
        """Test guard finds matching client from multiple configured clients."""
        from svc_infra.api.fastapi.auth.gaurd import login_client_gaurd

        client1 = MagicMock()
        client1.client_id = "client-1"
        client1.client_secret = MagicMock()
        client1.client_secret.get_secret_value.return_value = "secret-1"

        client2 = MagicMock()
        client2.client_id = "client-2"
        client2.client_secret = MagicMock()
        client2.client_secret.get_secret_value.return_value = "secret-2"

        mock_settings.return_value = MagicMock(
            require_client_secret_on_password_login=True,
            password_clients=[client1, client2],
        )

        request = MagicMock()
        request.method = "POST"
        request.url.path = "/auth/login"
        request.form = AsyncMock(
            return_value={
                "client_id": "client-2",
                "client_secret": "secret-2",
            }
        )

        # Should pass with second client
        result = await login_client_gaurd(request)
        assert result is None
