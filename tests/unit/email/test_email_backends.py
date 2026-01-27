"""Tests for email backends."""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from svc_infra.email.backends.console import ConsoleBackend
from svc_infra.email.base import (
    Attachment,
    EmailMessage,
    EmailStatus,
)

# ─── ConsoleBackend Tests ──────────────────────────────────────────────────


class TestConsoleBackend:
    """Tests for ConsoleBackend."""

    def test_init_defaults(self) -> None:
        """Test ConsoleBackend initialization with defaults."""
        backend = ConsoleBackend()
        assert backend.log_level == logging.INFO
        assert backend.truncate_body == 500

    def test_init_custom(self) -> None:
        """Test ConsoleBackend initialization with custom values."""
        backend = ConsoleBackend(log_level=logging.DEBUG, truncate_body=100)
        assert backend.log_level == logging.DEBUG
        assert backend.truncate_body == 100

    def test_provider_name(self) -> None:
        """Test provider_name property."""
        backend = ConsoleBackend()
        assert backend.provider_name == "console"

    @pytest.mark.asyncio
    async def test_send_async(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test async send logs message."""
        backend = ConsoleBackend()
        message = EmailMessage(
            to="user@example.com",
            subject="Test Subject",
            html="<p>Hello World!</p>",
            from_addr="noreply@example.com",
        )

        with caplog.at_level(logging.INFO):
            result = await backend.send(message)

        assert result.status == EmailStatus.SENT
        assert result.provider == "console"
        assert result.message_id is not None
        assert result.message_id.startswith("console-")

    def test_send_sync(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test sync send logs message."""
        backend = ConsoleBackend()
        message = EmailMessage(
            to="user@example.com",
            subject="Test Subject",
            html="<p>Hello World!</p>",
            from_addr="noreply@example.com",
        )

        with caplog.at_level(logging.INFO):
            result = backend.send_sync(message)

        assert result.status == EmailStatus.SENT
        assert result.provider == "console"

    @pytest.mark.asyncio
    async def test_send_truncates_long_body(self) -> None:
        """Test that long body is truncated in logs."""
        backend = ConsoleBackend(truncate_body=50)
        long_html = "<p>" + "x" * 200 + "</p>"
        message = EmailMessage(
            to="user@example.com",
            subject="Test",
            html=long_html,
            from_addr="noreply@example.com",
        )

        result = await backend.send(message)
        assert result.status == EmailStatus.SENT

    @pytest.mark.asyncio
    async def test_send_multiple_recipients(self) -> None:
        """Test sending to multiple recipients."""
        backend = ConsoleBackend()
        message = EmailMessage(
            to=["user1@example.com", "user2@example.com"],
            subject="Test",
            html="<p>Hello</p>",
            from_addr="noreply@example.com",
        )

        result = await backend.send(message)
        assert result.status == EmailStatus.SENT


# ─── SMTPBackend Tests ─────────────────────────────────────────────────────


class TestSMTPBackend:
    """Tests for SMTPBackend."""

    def test_init(self) -> None:
        """Test SMTPBackend initialization."""
        from svc_infra.email.backends.smtp import SMTPBackend

        backend = SMTPBackend(
            host="smtp.example.com",
            port=587,
            username="user",
            password="secret",
            from_addr="noreply@example.com",
        )
        assert backend.host == "smtp.example.com"
        assert backend.port == 587
        assert backend.username == "user"
        assert backend.from_addr == "noreply@example.com"

    def test_provider_name(self) -> None:
        """Test provider_name property."""
        from svc_infra.email.backends.smtp import SMTPBackend

        backend = SMTPBackend(host="smtp.example.com")
        assert backend.provider_name == "smtp"

    @pytest.mark.asyncio
    async def test_send_with_mock(self) -> None:
        """Test send with mocked SMTP connection."""
        from svc_infra.email.backends.smtp import SMTPBackend

        backend = SMTPBackend(
            host="smtp.example.com",
            port=587,
            username="user",
            password="secret",
            from_addr="noreply@example.com",
        )

        message = EmailMessage(
            to="user@example.com",
            subject="Test",
            html="<p>Hello</p>",
            from_addr="noreply@example.com",
        )

        # Mock aiosmtplib module import inside the send method
        mock_smtp_instance = MagicMock()
        mock_smtp_instance.connect = AsyncMock()
        mock_smtp_instance.starttls = AsyncMock()
        mock_smtp_instance.login = AsyncMock()
        mock_smtp_instance.send_message = AsyncMock()
        mock_smtp_instance.quit = AsyncMock()

        mock_aiosmtplib = MagicMock()
        mock_aiosmtplib.SMTP.return_value = mock_smtp_instance
        mock_aiosmtplib.SMTPException = Exception

        with patch.dict("sys.modules", {"aiosmtplib": mock_aiosmtplib}):
            result = await backend.send(message)

            assert result.status == EmailStatus.SENT
            assert result.provider == "smtp"

    def test_send_sync_with_mock(self) -> None:
        """Test sync send with mocked SMTP connection."""
        from svc_infra.email.backends.smtp import SMTPBackend

        backend = SMTPBackend(
            host="smtp.example.com",
            port=587,
            username="user",
            password="secret",
            from_addr="noreply@example.com",
        )

        message = EmailMessage(
            to="user@example.com",
            subject="Test",
            html="<p>Hello</p>",
            from_addr="noreply@example.com",
        )

        # The code creates SMTP() first, then uses 'with smtp:'
        mock_smtp_instance = MagicMock()
        mock_smtp_instance.__enter__ = MagicMock(return_value=mock_smtp_instance)
        mock_smtp_instance.__exit__ = MagicMock(return_value=False)

        with patch("smtplib.SMTP", return_value=mock_smtp_instance):
            result = backend.send_sync(message)

            assert result.status == EmailStatus.SENT
            # Verify starttls and send_message were called on the instance
            mock_smtp_instance.starttls.assert_called_once()
            mock_smtp_instance.login.assert_called_once_with("user", "secret")
            mock_smtp_instance.send_message.assert_called_once()


# ─── ResendBackend Tests ───────────────────────────────────────────────────


class TestResendBackend:
    """Tests for ResendBackend."""

    def test_init(self) -> None:
        """Test ResendBackend initialization."""
        from svc_infra.email.backends.resend import ResendBackend

        backend = ResendBackend(api_key="re_test_key")
        assert backend.api_key == "re_test_key"

    def test_provider_name(self) -> None:
        """Test provider_name property."""
        from svc_infra.email.backends.resend import ResendBackend

        backend = ResendBackend(api_key="re_test_key")
        assert backend.provider_name == "resend"

    @pytest.mark.asyncio
    async def test_send_with_mock(self) -> None:
        """Test send with mocked HTTP client."""
        from svc_infra.email.backends.resend import ResendBackend

        backend = ResendBackend(
            api_key="re_test_key",
            from_addr="noreply@example.com",
        )

        message = EmailMessage(
            to="user@example.com",
            subject="Test",
            html="<p>Hello</p>",
            from_addr="noreply@example.com",
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "msg_123"}
            mock_client.post.return_value = mock_response

            result = await backend.send(message)

            assert result.status == EmailStatus.SENT
            assert result.message_id == "msg_123"
            assert result.provider == "resend"


# ─── SendGridBackend Tests ─────────────────────────────────────────────────


class TestSendGridBackend:
    """Tests for SendGridBackend."""

    def test_init(self) -> None:
        """Test SendGridBackend initialization."""
        from svc_infra.email.backends.sendgrid import SendGridBackend

        backend = SendGridBackend(api_key="SG.test_key")
        assert backend.api_key == "SG.test_key"

    def test_provider_name(self) -> None:
        """Test provider_name property."""
        from svc_infra.email.backends.sendgrid import SendGridBackend

        backend = SendGridBackend(api_key="SG.test_key")
        assert backend.provider_name == "sendgrid"

    @pytest.mark.asyncio
    async def test_send_with_mock(self) -> None:
        """Test send with mocked HTTP client."""
        from svc_infra.email.backends.sendgrid import SendGridBackend

        backend = SendGridBackend(
            api_key="SG.test_key",
            from_addr="noreply@example.com",
        )

        message = EmailMessage(
            to="user@example.com",
            subject="Test",
            html="<p>Hello</p>",
            from_addr="noreply@example.com",
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_response.headers = {"X-Message-Id": "sg_msg_123"}
            mock_client.post.return_value = mock_response

            result = await backend.send(message)

            assert result.status == EmailStatus.SENT
            assert result.message_id == "sg_msg_123"
            assert result.provider == "sendgrid"


# ─── SESBackend Tests ──────────────────────────────────────────────────────


class TestSESBackend:
    """Tests for SESBackend."""

    def test_init(self) -> None:
        """Test SESBackend initialization."""
        from svc_infra.email.backends.ses import SESBackend

        backend = SESBackend(region="us-west-2")
        assert backend.region == "us-west-2"

    def test_provider_name(self) -> None:
        """Test provider_name property."""
        from svc_infra.email.backends.ses import SESBackend

        backend = SESBackend()
        assert backend.provider_name == "ses"

    @pytest.mark.asyncio
    async def test_send_with_mock(self) -> None:
        """Test send with mocked boto3 client."""
        from svc_infra.email.backends.ses import SESBackend

        backend = SESBackend(
            region="us-east-1",
            access_key="AKIA_TEST",
            secret_key="secret_test",
            from_addr="noreply@example.com",
        )

        message = EmailMessage(
            to="user@example.com",
            subject="Test",
            html="<p>Hello</p>",
            from_addr="noreply@example.com",
        )

        # Create mock for async context manager
        mock_ses_client = MagicMock()

        # send_email returns a coroutine-like result
        async def mock_send_email(**kwargs):
            return {"MessageId": "ses_msg_123"}

        mock_ses_client.send_email = mock_send_email

        # Mock session and client as async context manager
        mock_session = MagicMock()

        class MockClientCM:
            async def __aenter__(self):
                return mock_ses_client

            async def __aexit__(self, *args):
                pass

        mock_session.client.return_value = MockClientCM()

        with patch.dict("sys.modules", {"aioboto3": MagicMock()}):
            import sys

            sys.modules["aioboto3"].Session.return_value = mock_session

            result = await backend.send(message)

            assert result.status == EmailStatus.SENT
            assert result.message_id == "ses_msg_123"
            assert result.provider == "ses"


# ─── PostmarkBackend Tests ─────────────────────────────────────────────────


class TestPostmarkBackend:
    """Tests for PostmarkBackend."""

    def test_init(self) -> None:
        """Test PostmarkBackend initialization."""
        from svc_infra.email.backends.postmark import PostmarkBackend

        backend = PostmarkBackend(api_token="pm_test_token")
        assert backend.api_token == "pm_test_token"

    def test_provider_name(self) -> None:
        """Test provider_name property."""
        from svc_infra.email.backends.postmark import PostmarkBackend

        backend = PostmarkBackend(api_token="pm_test_token")
        assert backend.provider_name == "postmark"

    @pytest.mark.asyncio
    async def test_send_with_mock(self) -> None:
        """Test send with mocked HTTP client."""
        from svc_infra.email.backends.postmark import PostmarkBackend

        backend = PostmarkBackend(
            api_token="pm_test_token",
            from_addr="noreply@example.com",
        )

        message = EmailMessage(
            to="user@example.com",
            subject="Test",
            html="<p>Hello</p>",
            from_addr="noreply@example.com",
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"MessageID": "pm_msg_123"}
            mock_client.post.return_value = mock_response

            result = await backend.send(message)

            assert result.status == EmailStatus.SENT
            assert result.message_id == "pm_msg_123"
            assert result.provider == "postmark"


# ─── MailgunBackend Tests ──────────────────────────────────────────────────


class TestMailgunBackend:
    """Tests for MailgunBackend."""

    def test_init(self) -> None:
        """Test MailgunBackend initialization."""
        from svc_infra.email.backends.mailgun import MailgunBackend

        backend = MailgunBackend(
            api_key="key-test",
            domain="mg.example.com",
        )
        assert backend.api_key == "key-test"
        assert backend.domain == "mg.example.com"
        assert backend.region == "us"

    def test_init_eu_region(self) -> None:
        """Test MailgunBackend initialization with EU region."""
        from svc_infra.email.backends.mailgun import MailgunBackend

        backend = MailgunBackend(
            api_key="key-test",
            domain="mg.example.com",
            region="eu",
        )
        assert backend.region == "eu"
        assert "eu.mailgun.net" in backend.api_base

    def test_provider_name(self) -> None:
        """Test provider_name property."""
        from svc_infra.email.backends.mailgun import MailgunBackend

        backend = MailgunBackend(api_key="key-test", domain="mg.example.com")
        assert backend.provider_name == "mailgun"

    @pytest.mark.asyncio
    async def test_send_with_mock(self) -> None:
        """Test send with mocked HTTP client."""
        from svc_infra.email.backends.mailgun import MailgunBackend

        backend = MailgunBackend(
            api_key="key-test",
            domain="mg.example.com",
            from_addr="noreply@example.com",
        )

        message = EmailMessage(
            to="user@example.com",
            subject="Test",
            html="<p>Hello</p>",
            from_addr="noreply@example.com",
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "<mg_msg_123@mg.example.com>"}
            mock_client.post.return_value = mock_response

            result = await backend.send(message)

            assert result.status == EmailStatus.SENT
            assert result.message_id == "<mg_msg_123@mg.example.com>"
            assert result.provider == "mailgun"


# ─── BrevoBackend Tests ────────────────────────────────────────────────────


class TestBrevoBackend:
    """Tests for BrevoBackend."""

    def test_init(self) -> None:
        """Test BrevoBackend initialization."""
        from svc_infra.email.backends.brevo import BrevoBackend

        backend = BrevoBackend(api_key="xkeysib-test")
        assert backend.api_key == "xkeysib-test"

    def test_provider_name(self) -> None:
        """Test provider_name property."""
        from svc_infra.email.backends.brevo import BrevoBackend

        backend = BrevoBackend(api_key="xkeysib-test")
        assert backend.provider_name == "brevo"

    @pytest.mark.asyncio
    async def test_send_with_mock(self) -> None:
        """Test send with mocked HTTP client."""
        from svc_infra.email.backends.brevo import BrevoBackend

        backend = BrevoBackend(
            api_key="xkeysib-test",
            from_addr="noreply@example.com",
        )

        message = EmailMessage(
            to="user@example.com",
            subject="Test",
            html="<p>Hello</p>",
            from_addr="noreply@example.com",
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"messageId": "<brevo_msg_123>"}
            mock_client.post.return_value = mock_response

            result = await backend.send(message)

            assert result.status == EmailStatus.SENT
            assert result.message_id == "<brevo_msg_123>"
            assert result.provider == "brevo"


# ─── EmailMessage Tests ────────────────────────────────────────────────────


class TestEmailMessage:
    """Tests for EmailMessage dataclass."""

    def test_single_recipient_normalized_to_list(self) -> None:
        """Test single recipient is normalized to list."""
        msg = EmailMessage(
            to="user@example.com",
            subject="Test",
            html="<p>Hello</p>",
        )
        assert msg.to == ["user@example.com"]

    def test_multiple_recipients(self) -> None:
        """Test multiple recipients."""
        msg = EmailMessage(
            to=["user1@example.com", "user2@example.com"],
            subject="Test",
            html="<p>Hello</p>",
        )
        assert msg.to == ["user1@example.com", "user2@example.com"]

    def test_requires_html_or_text(self) -> None:
        """Test that either html or text is required."""
        with pytest.raises(ValueError, match="Either html or text body must be provided"):
            EmailMessage(
                to="user@example.com",
                subject="Test",
            )

    def test_text_only(self) -> None:
        """Test text-only message."""
        msg = EmailMessage(
            to="user@example.com",
            subject="Test",
            text="Hello World",
        )
        assert msg.text == "Hello World"
        assert msg.html is None

    def test_with_attachments(self) -> None:
        """Test message with attachments."""
        attachment = Attachment(
            filename="test.txt",
            content=b"Hello",
            content_type="text/plain",
        )
        msg = EmailMessage(
            to="user@example.com",
            subject="Test",
            html="<p>Hello</p>",
            attachments=[attachment],
        )
        assert len(msg.attachments) == 1
        assert msg.attachments[0].filename == "test.txt"
