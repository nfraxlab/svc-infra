"""Tests for FastAPI auth sender - Coverage improvement."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from svc_infra.api.fastapi.auth.sender import ConsoleSender, SMTPSender, get_sender

# ─── ConsoleSender Tests ───────────────────────────────────────────────────


class TestConsoleSender:
    """Tests for ConsoleSender (legacy)."""

    def test_send(self, capsys: pytest.CaptureFixture) -> None:
        """Test send prints to console."""
        sender = ConsoleSender()
        sender.send("user@example.com", "Test Subject", "<p>Hello</p>")

        captured = capsys.readouterr()
        assert "user@example.com" in captured.out
        assert "Test Subject" in captured.out
        assert "<p>Hello</p>" in captured.out


# ─── SMTPSender Tests ──────────────────────────────────────────────────────


class TestSMTPSender:
    """Tests for SMTPSender (legacy)."""

    def test_init(self) -> None:
        """Test SMTPSender initialization."""
        sender = SMTPSender(
            host="smtp.example.com",
            port=587,
            username="user",
            password="secret",
            from_addr="noreply@example.com",
        )
        assert sender.host == "smtp.example.com"
        assert sender.port == 587
        assert sender.username == "user"
        assert sender.password == "secret"
        assert sender.from_addr == "noreply@example.com"


# ─── get_sender Tests ──────────────────────────────────────────────────────


class TestGetSender:
    """Tests for get_sender function."""

    @pytest.fixture(autouse=True)
    def clear_env(self) -> None:
        """Clear email-related env vars before each test."""
        for key in list(os.environ.keys()):
            if key.startswith("EMAIL_") or key.startswith("AUTH_SMTP"):
                os.environ.pop(key, None)
        # Clear settings cache
        from svc_infra.email.settings import get_email_settings

        get_email_settings.cache_clear()

    @patch("svc_infra.api.fastapi.auth.sender.CURRENT_ENVIRONMENT", "dev")
    @patch("svc_infra.api.fastapi.auth.sender.PROD_ENV", "prod")
    @patch("svc_infra.api.fastapi.auth.sender.get_auth_settings")
    def test_returns_console_sender_in_dev(self, mock_get_settings: MagicMock) -> None:
        """Test returns ConsoleSender when not configured in dev."""
        mock_settings = MagicMock()
        mock_settings.smtp_host = None
        mock_settings.smtp_username = None
        mock_settings.smtp_password = None
        mock_settings.smtp_from = None
        mock_get_settings.return_value = mock_settings

        sender = get_sender()

        assert isinstance(sender, ConsoleSender)

    @patch("svc_infra.api.fastapi.auth.sender.CURRENT_ENVIRONMENT", "prod")
    @patch("svc_infra.api.fastapi.auth.sender.PROD_ENV", "prod")
    @patch("svc_infra.api.fastapi.auth.sender.get_auth_settings")
    def test_raises_in_prod_without_config(self, mock_get_settings: MagicMock) -> None:
        """Test raises RuntimeError in prod without email configuration."""
        mock_settings = MagicMock()
        mock_settings.smtp_host = None
        mock_settings.smtp_username = None
        mock_settings.smtp_password = None
        mock_settings.smtp_from = None
        mock_get_settings.return_value = mock_settings

        with pytest.raises(RuntimeError) as exc_info:
            get_sender()

        assert "Email is required in prod" in str(exc_info.value)

    @patch("svc_infra.api.fastapi.auth.sender.CURRENT_ENVIRONMENT", "dev")
    @patch("svc_infra.api.fastapi.auth.sender.PROD_ENV", "prod")
    @patch("svc_infra.api.fastapi.auth.sender.get_auth_settings")
    def test_returns_adapter_when_configured(self, mock_get_settings: MagicMock) -> None:
        """Test returns email adapter when configured via EMAIL_* vars."""
        mock_password = MagicMock()
        mock_password.get_secret_value.return_value = "secret123"

        mock_settings = MagicMock()
        mock_settings.smtp_host = "smtp.example.com"
        mock_settings.smtp_port = 587
        mock_settings.smtp_username = "user"
        mock_settings.smtp_password = mock_password
        mock_settings.smtp_from = "noreply@example.com"
        mock_get_settings.return_value = mock_settings

        # Set EMAIL_FROM to trigger adapter (not just console)
        os.environ["EMAIL_FROM"] = "noreply@example.com"
        os.environ["EMAIL_SMTP_HOST"] = "smtp.example.com"
        os.environ["EMAIL_SMTP_USERNAME"] = "user"
        os.environ["EMAIL_SMTP_PASSWORD"] = "secret123"

        sender = get_sender()

        # Should return the adapter, not ConsoleSender
        from svc_infra.api.fastapi.auth.sender import _EmailSenderAdapter

        assert isinstance(sender, _EmailSenderAdapter)

    @patch("svc_infra.api.fastapi.auth.sender.CURRENT_ENVIRONMENT", "dev")
    @patch("svc_infra.api.fastapi.auth.sender.PROD_ENV", "prod")
    @patch("svc_infra.api.fastapi.auth.sender.get_auth_settings")
    def test_syncs_auth_smtp_to_email_env(self, mock_get_settings: MagicMock) -> None:
        """Test AUTH_SMTP_* env vars are synced to EMAIL_* vars."""
        mock_password = MagicMock()
        mock_password.get_secret_value.return_value = "secret123"

        mock_settings = MagicMock()
        mock_settings.smtp_host = "smtp.example.com"
        mock_settings.smtp_port = 587
        mock_settings.smtp_username = "user"
        mock_settings.smtp_password = mock_password
        mock_settings.smtp_from = "noreply@example.com"
        mock_get_settings.return_value = mock_settings

        # Set AUTH_SMTP_* vars
        os.environ["AUTH_SMTP_HOST"] = "smtp.example.com"
        os.environ["AUTH_SMTP_FROM"] = "noreply@example.com"

        get_sender()

        # Should have synced to EMAIL_*
        assert os.environ.get("EMAIL_SMTP_HOST") == "smtp.example.com"
        assert os.environ.get("EMAIL_FROM") == "noreply@example.com"
