"""Tests for resolve_jwt_secret env-var fallback behaviour."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from svc_infra.api.fastapi.auth.settings import resolve_jwt_secret
from svc_infra.app.env import MissingSecretError


class TestResolveJwtSecret:
    """Verify the JWT secret resolution order."""

    def test_uses_jwt_block_secret_when_present(self) -> None:
        """AuthSettings.jwt.secret (AUTH_JWT__SECRET) takes priority."""
        mock_jwt = MagicMock()
        mock_jwt.secret.get_secret_value.return_value = "from-nested-settings"
        mock_settings = MagicMock()
        mock_settings.jwt = mock_jwt

        with patch(
            "svc_infra.api.fastapi.auth.settings.get_auth_settings",
            return_value=mock_settings,
        ):
            assert resolve_jwt_secret() == "from-nested-settings"

    def test_falls_back_to_auth_jwt_secret_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """AUTH_JWT_SECRET (single underscore) is honoured as fallback."""
        mock_settings = MagicMock()
        mock_settings.jwt = None

        monkeypatch.setenv("AUTH_JWT_SECRET", "from-single-underscore")
        monkeypatch.delenv("JWT_SECRET", raising=False)
        monkeypatch.setenv("APP_ENV", "dev")

        with patch(
            "svc_infra.api.fastapi.auth.settings.get_auth_settings",
            return_value=mock_settings,
        ):
            assert resolve_jwt_secret() == "from-single-underscore"

    def test_falls_back_to_jwt_secret_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Bare JWT_SECRET env var is honoured when AUTH_JWT_SECRET missing."""
        mock_settings = MagicMock()
        mock_settings.jwt = None

        monkeypatch.delenv("AUTH_JWT_SECRET", raising=False)
        monkeypatch.setenv("JWT_SECRET", "from-bare-env")
        monkeypatch.setenv("APP_ENV", "dev")

        with patch(
            "svc_infra.api.fastapi.auth.settings.get_auth_settings",
            return_value=mock_settings,
        ):
            assert resolve_jwt_secret() == "from-bare-env"

    def test_auth_jwt_secret_takes_priority_over_jwt_secret(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AUTH_JWT_SECRET wins over JWT_SECRET."""
        mock_settings = MagicMock()
        mock_settings.jwt = None

        monkeypatch.setenv("AUTH_JWT_SECRET", "winner")
        monkeypatch.setenv("JWT_SECRET", "loser")
        monkeypatch.setenv("APP_ENV", "dev")

        with patch(
            "svc_infra.api.fastapi.auth.settings.get_auth_settings",
            return_value=mock_settings,
        ):
            assert resolve_jwt_secret() == "winner"

    def test_returns_dev_default_when_no_secret_in_dev(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """In dev, returns the dev_default when nothing is set."""
        mock_settings = MagicMock()
        mock_settings.jwt = None

        monkeypatch.delenv("AUTH_JWT_SECRET", raising=False)
        monkeypatch.delenv("JWT_SECRET", raising=False)
        monkeypatch.setenv("APP_ENV", "dev")

        with patch(
            "svc_infra.api.fastapi.auth.settings.get_auth_settings",
            return_value=mock_settings,
        ):
            result = resolve_jwt_secret(dev_default="my-dev-default")
            assert result == "my-dev-default"

    def test_raises_in_production_when_no_secret(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """In production, raises MissingSecretError when nothing is set."""
        mock_settings = MagicMock()
        mock_settings.jwt = None

        monkeypatch.delenv("AUTH_JWT_SECRET", raising=False)
        monkeypatch.delenv("JWT_SECRET", raising=False)
        monkeypatch.setenv("APP_ENV", "prod")

        with (
            patch(
                "svc_infra.api.fastapi.auth.settings.get_auth_settings",
                return_value=mock_settings,
            ),
            pytest.raises(MissingSecretError),
        ):
            resolve_jwt_secret()
