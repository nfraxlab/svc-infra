"""Unit tests for svc_infra.api.fastapi.auth.sender module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestConsoleSender:
    """Tests for ConsoleSender class."""

    def test_send_prints_to_console(self, capsys) -> None:
        """Test that send prints email to console."""
        from svc_infra.api.fastapi.auth.sender import ConsoleSender

        sender = ConsoleSender()
        sender.send("user@example.com", "Test Subject", "<p>Hello World</p>")

        captured = capsys.readouterr()
        assert "[MAIL -> user@example.com]" in captured.out
        assert "Test Subject" in captured.out
        assert "<p>Hello World</p>" in captured.out


class TestSMTPSender:
    """Tests for SMTPSender class."""

    def test_initialization(self) -> None:
        """Test SMTPSender initialization."""
        from svc_infra.api.fastapi.auth.sender import SMTPSender

        sender = SMTPSender(
            host="smtp.example.com",
            port=587,
            username="user@example.com",
            password="secret123",
            from_addr="noreply@example.com",
        )

        assert sender.host == "smtp.example.com"
        assert sender.port == 587
        assert sender.username == "user@example.com"
        assert sender.password == "secret123"
        assert sender.from_addr == "noreply@example.com"

    @patch("svc_infra.api.fastapi.auth.sender.smtplib.SMTP")
    def test_send_creates_message_correctly(self, mock_smtp: MagicMock) -> None:
        """Test send creates proper email message."""
        from svc_infra.api.fastapi.auth.sender import SMTPSender

        mock_instance = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_instance)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        sender = SMTPSender(
            host="smtp.example.com",
            port=587,
            username="user@example.com",
            password="secret123",
            from_addr="noreply@example.com",
        )

        sender.send("recipient@example.com", "Test Subject", "<p>Body</p>")

        mock_smtp.assert_called_once_with("smtp.example.com", 587)
        mock_instance.starttls.assert_called_once()
        mock_instance.login.assert_called_once_with("user@example.com", "secret123")
        mock_instance.send_message.assert_called_once()


class TestGetSender:
    """Tests for get_sender function."""

    @patch("svc_infra.api.fastapi.auth.sender.get_auth_settings")
    @patch("svc_infra.api.fastapi.auth.sender.CURRENT_ENVIRONMENT", "development")
    def test_returns_console_sender_when_not_configured(self, mock_settings: MagicMock) -> None:
        """Test returns ConsoleSender when SMTP not configured in dev."""
        from svc_infra.api.fastapi.auth.sender import ConsoleSender, get_sender

        mock_settings.return_value = MagicMock(
            smtp_host=None,
            smtp_username=None,
            smtp_password=None,
            smtp_from=None,
        )

        sender = get_sender()

        assert isinstance(sender, ConsoleSender)

    @patch("svc_infra.api.fastapi.auth.sender.get_auth_settings")
    @patch("svc_infra.api.fastapi.auth.sender.CURRENT_ENVIRONMENT", "development")
    def test_returns_smtp_sender_when_configured(self, mock_settings: MagicMock) -> None:
        """Test returns SMTPSender when SMTP is configured."""
        from svc_infra.api.fastapi.auth.sender import SMTPSender, get_sender

        mock_password = MagicMock()
        mock_password.get_secret_value.return_value = "password123"

        mock_settings.return_value = MagicMock(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_username="user@example.com",
            smtp_password=mock_password,
            smtp_from="noreply@example.com",
        )

        sender = get_sender()

        assert isinstance(sender, SMTPSender)
        assert sender.host == "smtp.example.com"
        assert sender.port == 587

    @patch("svc_infra.api.fastapi.auth.sender.get_auth_settings")
    @patch("svc_infra.api.fastapi.auth.sender.CURRENT_ENVIRONMENT", "production")
    @patch("svc_infra.api.fastapi.auth.sender.PROD_ENV", "production")
    def test_raises_error_in_prod_without_smtp(self, mock_settings: MagicMock) -> None:
        """Test raises RuntimeError in production without SMTP config."""
        from svc_infra.api.fastapi.auth.sender import get_sender

        mock_settings.return_value = MagicMock(
            smtp_host=None,
            smtp_username=None,
            smtp_password=None,
            smtp_from=None,
        )

        with pytest.raises(RuntimeError, match="SMTP is required in prod"):
            get_sender()

    @patch("svc_infra.api.fastapi.auth.sender.get_auth_settings")
    @patch("svc_infra.api.fastapi.auth.sender.CURRENT_ENVIRONMENT", "development")
    def test_partial_config_returns_console_sender(self, mock_settings: MagicMock) -> None:
        """Test partial SMTP config falls back to console sender."""
        from svc_infra.api.fastapi.auth.sender import ConsoleSender, get_sender

        mock_settings.return_value = MagicMock(
            smtp_host="smtp.example.com",
            smtp_username=None,  # Missing
            smtp_password=None,  # Missing
            smtp_from="noreply@example.com",
        )

        sender = get_sender()

        assert isinstance(sender, ConsoleSender)


class TestSenderProtocol:
    """Tests for Sender protocol conformance."""

    def test_console_sender_conforms_to_protocol(self) -> None:
        """Test ConsoleSender implements Sender protocol."""
        from svc_infra.api.fastapi.auth.sender import ConsoleSender

        sender = ConsoleSender()
        # Protocol conformance check - should have send method
        assert hasattr(sender, "send")
        assert callable(sender.send)

    def test_smtp_sender_conforms_to_protocol(self) -> None:
        """Test SMTPSender implements Sender protocol."""
        from svc_infra.api.fastapi.auth.sender import SMTPSender

        sender = SMTPSender(
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            from_addr="from@example.com",
        )
        # Protocol conformance check - should have send method
        assert hasattr(sender, "send")
        assert callable(sender.send)
