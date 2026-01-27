"""Tests for EmailSender and high-level send API."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from svc_infra.email.backends.console import ConsoleBackend
from svc_infra.email.base import (
    ConfigurationError,
    EmailResult,
    EmailStatus,
    InvalidRecipientError,
)
from svc_infra.email.sender import (
    EmailSender,
    validate_email,
    validate_recipients,
)
from svc_infra.email.settings import EmailSettings

# ─── Email Validation Tests ────────────────────────────────────────────────


class TestValidateEmail:
    """Tests for email validation."""

    def test_valid_emails(self) -> None:
        """Test valid email addresses."""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user@subdomain.example.com",
            "user123@example.co.uk",
        ]
        for email in valid_emails:
            assert validate_email(email) is True, f"Expected {email} to be valid"

    def test_invalid_emails(self) -> None:
        """Test invalid email addresses."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user@.com",
            "user@example",
            "",
            "user name@example.com",
        ]
        for email in invalid_emails:
            assert validate_email(email) is False, f"Expected {email} to be invalid"


class TestValidateRecipients:
    """Tests for recipient validation."""

    def test_single_recipient_string(self) -> None:
        """Test single recipient as string."""
        result = validate_recipients("user@example.com")
        assert result == ["user@example.com"]

    def test_multiple_recipients(self) -> None:
        """Test multiple recipients as list."""
        result = validate_recipients(["user1@example.com", "user2@example.com"])
        assert result == ["user1@example.com", "user2@example.com"]

    def test_strips_whitespace(self) -> None:
        """Test that whitespace is stripped."""
        result = validate_recipients("  user@example.com  ")
        assert result == ["user@example.com"]

    def test_invalid_recipient_raises(self) -> None:
        """Test that invalid recipient raises error."""
        with pytest.raises(InvalidRecipientError) as exc_info:
            validate_recipients("invalid-email")
        assert exc_info.value.recipient == "invalid-email"

    def test_mixed_valid_invalid_raises(self) -> None:
        """Test that mixed valid/invalid raises on first invalid."""
        with pytest.raises(InvalidRecipientError):
            validate_recipients(["valid@example.com", "invalid"])


# ─── EmailSender Tests ─────────────────────────────────────────────────────


class TestEmailSender:
    """Tests for EmailSender class."""

    @pytest.fixture
    def mock_backend(self) -> MagicMock:
        """Create a mock email backend."""
        backend = MagicMock()
        backend.send = AsyncMock(
            return_value=EmailResult(
                message_id="test-123",
                provider="mock",
                status=EmailStatus.SENT,
            )
        )
        backend.send_sync = MagicMock(
            return_value=EmailResult(
                message_id="test-456",
                provider="mock",
                status=EmailStatus.SENT,
            )
        )
        backend.provider_name = "mock"
        return backend

    @pytest.fixture
    def sender(self, mock_backend: MagicMock) -> EmailSender:
        """Create an EmailSender with mock backend."""
        # Use model_construct to bypass validation/alias issues
        settings = EmailSettings.model_construct(from_addr="noreply@test.com")
        sender = EmailSender(
            backend=mock_backend,
            settings=settings,
            app_name="TestApp",
            app_url="https://testapp.com",
        )
        return sender

    def test_init(self, mock_backend: MagicMock) -> None:
        """Test EmailSender initialization."""
        sender = EmailSender(
            backend=mock_backend,
            app_name="MyApp",
            app_url="https://myapp.com",
            support_email="help@myapp.com",
        )
        assert sender.backend == mock_backend
        assert sender.app_name == "MyApp"
        assert sender.app_url == "https://myapp.com"
        assert sender.support_email == "help@myapp.com"

    @pytest.mark.asyncio
    async def test_send_with_html(self, sender: EmailSender) -> None:
        """Test send with HTML body."""
        result = await sender.send(
            to="user@example.com",
            subject="Test",
            html="<p>Hello</p>",
        )

        assert result.status == EmailStatus.SENT
        assert result.message_id == "test-123"
        sender.backend.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_with_template(self, sender: EmailSender) -> None:
        """Test send with template."""
        result = await sender.send(
            to="user@example.com",
            subject="Verify",
            template="verification",
            context={"code": "123456"},
        )

        assert result.status == EmailStatus.SENT
        # Check that the message was sent with rendered template
        call_args = sender.backend.send.call_args
        message = call_args[0][0]
        assert "123456" in message.html

    @pytest.mark.asyncio
    async def test_send_validates_recipients(self, sender: EmailSender) -> None:
        """Test that send validates recipients."""
        with pytest.raises(InvalidRecipientError):
            await sender.send(
                to="invalid-email",
                subject="Test",
                html="<p>Hello</p>",
            )

    @pytest.mark.asyncio
    async def test_send_requires_from_addr(self, mock_backend: MagicMock) -> None:
        """Test that send requires from_addr."""
        # Clear EMAIL_FROM
        os.environ.pop("EMAIL_FROM", None)

        # Create sender without from_addr configured
        with patch("svc_infra.email.sender.get_email_settings") as mock_settings:
            mock_settings.return_value = MagicMock(from_addr=None, reply_to=None)

            sender = EmailSender(backend=mock_backend, app_name="Test")

            with pytest.raises(ConfigurationError) as exc_info:
                await sender.send(
                    to="user@example.com",
                    subject="Test",
                    html="<p>Hello</p>",
                )

            assert "No sender address provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_nonexistent_template_raises(self, sender: EmailSender) -> None:
        """Test that nonexistent template raises error."""
        with pytest.raises(ConfigurationError) as exc_info:
            await sender.send(
                to="user@example.com",
                subject="Test",
                template="nonexistent",
            )

        assert "not found" in str(exc_info.value)

    def test_send_sync(self, sender: EmailSender) -> None:
        """Test synchronous send."""
        result = sender.send_sync(
            to="user@example.com",
            subject="Test",
            html="<p>Hello</p>",
        )

        assert result.status == EmailStatus.SENT
        assert result.message_id == "test-456"
        sender.backend.send_sync.assert_called_once()


# ─── Convenience Method Tests ──────────────────────────────────────────────


class TestConvenienceMethods:
    """Tests for convenience methods."""

    @pytest.fixture
    def sender(self) -> EmailSender:
        """Create an EmailSender with console backend."""
        # Use model_construct to bypass validation/alias issues
        settings = EmailSettings.model_construct(from_addr="noreply@test.com")
        return EmailSender(
            backend=ConsoleBackend(),
            settings=settings,
            app_name="TestApp",
            app_url="https://testapp.com",
        )

    @pytest.mark.asyncio
    async def test_send_verification_with_code(self, sender: EmailSender) -> None:
        """Test send_verification with code."""
        result = await sender.send_verification(
            to="user@example.com",
            code="123456",
            user_name="John",
        )

        assert result.status == EmailStatus.SENT

    @pytest.mark.asyncio
    async def test_send_verification_with_url(self, sender: EmailSender) -> None:
        """Test send_verification with URL."""
        result = await sender.send_verification(
            to="user@example.com",
            verification_url="https://example.com/verify?token=abc",
            user_name="John",
        )

        assert result.status == EmailStatus.SENT

    @pytest.mark.asyncio
    async def test_send_verification_requires_code_or_url(self, sender: EmailSender) -> None:
        """Test that send_verification requires code or URL."""
        with pytest.raises(ValueError) as exc_info:
            await sender.send_verification(to="user@example.com")

        assert "Either code or verification_url must be provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_password_reset(self, sender: EmailSender) -> None:
        """Test send_password_reset."""
        result = await sender.send_password_reset(
            to="user@example.com",
            reset_url="https://example.com/reset?token=xyz",
            user_name="Jane",
        )

        assert result.status == EmailStatus.SENT

    @pytest.mark.asyncio
    async def test_send_invitation(self, sender: EmailSender) -> None:
        """Test send_invitation."""
        result = await sender.send_invitation(
            to="newuser@example.com",
            invitation_url="https://example.com/invite/abc",
            inviter_name="Alice",
            workspace_name="Engineering",
            role="Developer",
        )

        assert result.status == EmailStatus.SENT

    @pytest.mark.asyncio
    async def test_send_welcome(self, sender: EmailSender) -> None:
        """Test send_welcome."""
        result = await sender.send_welcome(
            to="user@example.com",
            user_name="Bob",
            features=["Feature 1", "Feature 2"],
        )

        assert result.status == EmailStatus.SENT


# ─── Easy API Tests ────────────────────────────────────────────────────────


class TestEasyApi:
    """Tests for easy_email and easy_sender functions."""

    def test_easy_email_returns_backend(self) -> None:
        """Test easy_email returns a backend."""
        from svc_infra.email import easy_email

        backend = easy_email()
        assert hasattr(backend, "send")
        assert hasattr(backend, "send_sync")
        assert hasattr(backend, "provider_name")

    def test_easy_sender_returns_sender(self) -> None:
        """Test easy_sender returns an EmailSender."""
        from svc_infra.email import easy_sender

        sender = easy_sender(app_name="TestApp")
        assert isinstance(sender, EmailSender)
        assert sender.app_name == "TestApp"

    def test_easy_email_console_backend_default(self) -> None:
        """Test easy_email defaults to console in dev."""
        from svc_infra.email import easy_email

        backend = easy_email()
        assert backend.provider_name == "console"

    def test_easy_email_explicit_backend(self) -> None:
        """Test easy_email with explicit backend."""
        from svc_infra.email import easy_email

        backend = easy_email(backend="console")
        assert backend.provider_name == "console"
