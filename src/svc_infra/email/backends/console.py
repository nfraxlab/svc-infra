"""
Console email backend for development.

Prints emails to stdout/logger instead of sending them.
Useful for development and testing.
"""

from __future__ import annotations

import logging
import uuid
from typing import ClassVar

from ..base import EmailMessage, EmailResult, EmailStatus

logger = logging.getLogger(__name__)


class ConsoleBackend:
    """
    Development email backend that prints to console.

    Instead of sending emails, this backend logs them to the console
    with pretty formatting. Useful for local development and testing.

    Attributes:
        log_level: Logging level for email output (default: INFO)
        truncate_body: Maximum body length to display (default: 500)

    Example:
        >>> from svc_infra.email.backends import ConsoleBackend
        >>> from svc_infra.email import EmailMessage
        >>>
        >>> backend = ConsoleBackend()
        >>> result = await backend.send(EmailMessage(
        ...     to="user@example.com",
        ...     subject="Test Email",
        ...     html="<h1>Hello!</h1>",
        ... ))
        >>> # Prints formatted email to console
    """

    provider_name: ClassVar[str] = "console"

    def __init__(
        self,
        log_level: int = logging.INFO,
        truncate_body: int = 500,
    ) -> None:
        """
        Initialize console backend.

        Args:
            log_level: Logging level for email output
            truncate_body: Maximum body length to display (0 = no truncation)
        """
        self.log_level = log_level
        self.truncate_body = truncate_body

    async def send(self, message: EmailMessage) -> EmailResult:
        """
        Log email to console (async).

        Args:
            message: Email message to "send"

        Returns:
            Successful EmailResult with fake message ID
        """
        return self._log_message(message)

    def send_sync(self, message: EmailMessage) -> EmailResult:
        """
        Log email to console (sync).

        Args:
            message: Email message to "send"

        Returns:
            Successful EmailResult with fake message ID
        """
        return self._log_message(message)

    def _log_message(self, message: EmailMessage) -> EmailResult:
        """Format and log the email message."""
        message_id = f"console-{uuid.uuid4().hex[:12]}"

        # Format recipients
        to_list = message.to if isinstance(message.to, list) else [message.to]
        recipients = ", ".join(to_list)

        # Get body content
        body = message.html or message.text or "(empty)"
        if self.truncate_body > 0 and len(body) > self.truncate_body:
            body = body[: self.truncate_body] + "... (truncated)"

        # Format CC/BCC if present
        extra_recipients = []
        if message.cc:
            extra_recipients.append(f"CC: {', '.join(message.cc)}")
        if message.bcc:
            extra_recipients.append(f"BCC: {', '.join(message.bcc)}")
        extra_line = f"\n    {' | '.join(extra_recipients)}" if extra_recipients else ""

        # Log the email
        log_message = (
            f"\n{'=' * 60}\n"
            f"  EMAIL (console backend - not sent)\n"
            f"{'=' * 60}\n"
            f"  From: {message.from_addr or '(not set)'}\n"
            f"  To: {recipients}{extra_line}\n"
            f"  Subject: {message.subject}\n"
            f"  Message-ID: {message_id}\n"
            f"{'-' * 60}\n"
            f"{body}\n"
            f"{'=' * 60}\n"
        )

        logger.log(self.log_level, log_message)

        return EmailResult(
            message_id=message_id,
            provider=self.provider_name,
            status=EmailStatus.SENT,
        )
