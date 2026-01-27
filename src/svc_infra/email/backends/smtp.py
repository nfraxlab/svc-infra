"""
SMTP email backend.

Sends emails via SMTP using aiosmtplib (async) with smtplib fallback (sync).
Supports StartTLS and SSL/TLS connections.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
import uuid
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import ClassVar

from ..base import (
    ConfigurationError,
    DeliveryError,
    EmailMessage,
    EmailResult,
    EmailStatus,
)

logger = logging.getLogger(__name__)


class SMTPBackend:
    """
    SMTP email backend for sending emails via standard SMTP servers.

    Supports both async (via aiosmtplib) and sync (via smtplib) sending.
    Provides StartTLS and SSL/TLS connection options.

    Attributes:
        host: SMTP server hostname
        port: SMTP server port (default: 587 for TLS, 465 for SSL)
        username: SMTP authentication username
        password: SMTP authentication password
        use_tls: Use STARTTLS (default: True for port 587)
        use_ssl: Use SSL/TLS (default: True for port 465)
        from_addr: Default sender address
        timeout: Connection timeout in seconds (default: 30)

    Example:
        >>> from svc_infra.email.backends import SMTPBackend
        >>> from svc_infra.email import EmailMessage
        >>>
        >>> # Gmail example
        >>> backend = SMTPBackend(
        ...     host="smtp.gmail.com",
        ...     port=587,
        ...     username="user@gmail.com",
        ...     password="app-password",
        ...     from_addr="user@gmail.com",
        ... )
        >>> result = await backend.send(EmailMessage(
        ...     to="recipient@example.com",
        ...     subject="Hello",
        ...     html="<p>Hello World</p>",
        ... ))

    Note:
        For Gmail, you need to use an App Password, not your regular password.
        Enable 2FA and generate an App Password in Google Account settings.
    """

    provider_name: ClassVar[str] = "smtp"

    def __init__(
        self,
        host: str | None = None,
        port: int = 587,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = True,
        use_ssl: bool = False,
        from_addr: str | None = None,
        timeout: int = 30,
    ) -> None:
        """
        Initialize SMTP backend.

        Args:
            host: SMTP server hostname (required)
            port: SMTP server port (default: 587)
            username: SMTP authentication username
            password: SMTP authentication password
            use_tls: Use STARTTLS after connecting (default: True)
            use_ssl: Use SSL/TLS connection (default: False)
            from_addr: Default sender email address
            timeout: Connection timeout in seconds

        Raises:
            ConfigurationError: If host is not provided
        """
        if not host:
            raise ConfigurationError(
                "SMTP host is required. Set EMAIL_SMTP_HOST environment variable."
            )

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.from_addr = from_addr
        self.timeout = timeout

        # Validate TLS/SSL settings
        if use_tls and use_ssl:
            logger.warning("Both use_tls and use_ssl are True. use_ssl takes precedence.")

    async def send(self, message: EmailMessage) -> EmailResult:
        """
        Send email asynchronously via SMTP.

        Uses aiosmtplib for non-blocking SMTP operations.

        Args:
            message: Email message to send

        Returns:
            EmailResult with message ID and status

        Raises:
            DeliveryError: If email sending fails
            ConfigurationError: If SMTP is not configured
        """
        try:
            import aiosmtplib
        except ImportError:
            # Fall back to sync if aiosmtplib not installed
            logger.warning(
                "aiosmtplib not installed, falling back to sync SMTP. "
                "Install with: pip install aiosmtplib"
            )
            return await asyncio.to_thread(self.send_sync, message)

        mime_message = self._build_mime_message(message)
        message_id = mime_message["Message-ID"]

        try:
            if self.use_ssl:
                # SSL/TLS connection (port 465)
                smtp = aiosmtplib.SMTP(
                    hostname=self.host,
                    port=self.port,
                    use_tls=True,
                    timeout=self.timeout,
                )
            else:
                # Plain or STARTTLS connection (port 587/25)
                smtp = aiosmtplib.SMTP(
                    hostname=self.host,
                    port=self.port,
                    use_tls=False,
                    timeout=self.timeout,
                )

            await smtp.connect()

            # STARTTLS if requested and not already using SSL
            if self.use_tls and not self.use_ssl:
                await smtp.starttls()

            # Authenticate if credentials provided
            if self.username and self.password:
                await smtp.login(self.username, self.password)

            # Send the message
            await smtp.send_message(mime_message)
            await smtp.quit()

            logger.info(f"Email sent via SMTP: {message_id} to {message.to}")

            return EmailResult(
                message_id=message_id,
                provider=self.provider_name,
                status=EmailStatus.SENT,
            )

        except aiosmtplib.SMTPException as e:
            logger.error(f"SMTP error sending email: {e}")
            raise DeliveryError(
                f"Failed to send email via SMTP: {e}",
                provider_error=str(e),
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            raise DeliveryError(
                f"Unexpected error sending email: {e}",
                provider_error=str(e),
            ) from e

    def send_sync(self, message: EmailMessage) -> EmailResult:
        """
        Send email synchronously via SMTP.

        Uses standard library smtplib for blocking SMTP operations.

        Args:
            message: Email message to send

        Returns:
            EmailResult with message ID and status

        Raises:
            DeliveryError: If email sending fails
            ConfigurationError: If SMTP is not configured
        """
        mime_message = self._build_mime_message(message)
        message_id = mime_message["Message-ID"]

        try:
            if self.use_ssl:
                # SSL/TLS connection (port 465)
                smtp = smtplib.SMTP_SSL(
                    host=self.host,
                    port=self.port,
                    timeout=self.timeout,
                )
            else:
                # Plain or STARTTLS connection (port 587/25)
                smtp = smtplib.SMTP(
                    host=self.host,
                    port=self.port,
                    timeout=self.timeout,
                )

            with smtp:
                # STARTTLS if requested and not already using SSL
                if self.use_tls and not self.use_ssl:
                    smtp.starttls()

                # Authenticate if credentials provided
                if self.username and self.password:
                    smtp.login(self.username, self.password)

                # Send the message
                smtp.send_message(mime_message)

            logger.info(f"Email sent via SMTP (sync): {message_id} to {message.to}")

            return EmailResult(
                message_id=message_id,
                provider=self.provider_name,
                status=EmailStatus.SENT,
            )

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email: {e}")
            raise DeliveryError(
                f"Failed to send email via SMTP: {e}",
                provider_error=str(e),
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            raise DeliveryError(
                f"Unexpected error sending email: {e}",
                provider_error=str(e),
            ) from e

    def _build_mime_message(self, message: EmailMessage) -> MIMEMultipart:
        """
        Build a MIME message from EmailMessage.

        Args:
            message: Email message to convert

        Returns:
            MIMEMultipart message ready for sending
        """
        # Create multipart message
        mime_msg = MIMEMultipart("alternative")

        # Set headers
        from_addr = message.from_addr or self.from_addr
        if not from_addr:
            raise ConfigurationError(
                "No sender address. Set from_addr in message or EMAIL_FROM env var."
            )

        mime_msg["From"] = from_addr
        mime_msg["Subject"] = message.subject
        mime_msg["Message-ID"] = f"<{uuid.uuid4().hex}@{self.host}>"

        # Handle recipients
        to_list = message.to if isinstance(message.to, list) else [message.to]
        mime_msg["To"] = ", ".join(to_list)

        if message.cc:
            mime_msg["Cc"] = ", ".join(message.cc)

        if message.reply_to:
            mime_msg["Reply-To"] = message.reply_to

        # Add custom headers
        if message.headers:
            for key, value in message.headers.items():
                mime_msg[key] = value

        # Add body parts
        if message.text:
            mime_msg.attach(MIMEText(message.text, "plain", "utf-8"))

        if message.html:
            mime_msg.attach(MIMEText(message.html, "html", "utf-8"))

        # If only text provided, add it as HTML fallback too
        if message.text and not message.html:
            # Already added as plain text above
            pass

        # If only HTML provided, generate plain text
        if message.html and not message.text:
            # Add HTML as the main content (already done above)
            # Could add a text version here by stripping HTML tags
            pass

        # Handle attachments
        if message.attachments:
            # Switch to mixed for attachments
            mixed_msg = MIMEMultipart("mixed")
            mixed_msg["From"] = mime_msg["From"]
            mixed_msg["To"] = mime_msg["To"]
            mixed_msg["Subject"] = mime_msg["Subject"]
            mixed_msg["Message-ID"] = mime_msg["Message-ID"]

            if mime_msg.get("Cc"):
                mixed_msg["Cc"] = mime_msg["Cc"]
            if mime_msg.get("Reply-To"):
                mixed_msg["Reply-To"] = mime_msg["Reply-To"]

            # Copy custom headers
            if message.headers:
                for key, value in message.headers.items():
                    mixed_msg[key] = value

            # Attach the alternative part (text/html)
            mixed_msg.attach(mime_msg)

            # Add attachments
            for attachment in message.attachments:
                part = MIMEApplication(
                    attachment.content,
                    Name=attachment.filename,
                )
                part["Content-Disposition"] = f'attachment; filename="{attachment.filename}"'

                # Set content ID for inline attachments
                if attachment.content_id:
                    part["Content-ID"] = f"<{attachment.content_id}>"
                    part["Content-Disposition"] = f'inline; filename="{attachment.filename}"'

                mixed_msg.attach(part)

            return mixed_msg

        return mime_msg

    def _get_all_recipients(self, message: EmailMessage) -> list[str]:
        """Get all recipients (to, cc, bcc) for sending."""
        recipients = []

        to_list = message.to if isinstance(message.to, list) else [message.to]
        recipients.extend(to_list)

        if message.cc:
            recipients.extend(message.cc)

        if message.bcc:
            recipients.extend(message.bcc)

        return recipients
