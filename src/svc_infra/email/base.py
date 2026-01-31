"""
Base email abstractions and exceptions.

Defines the EmailBackend protocol that all email implementations must follow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, runtime_checkable


class EmailError(Exception):
    """Base exception for all email operations."""

    pass


class ConfigurationError(EmailError):
    """Raised when email is not properly configured."""

    pass


class DeliveryError(EmailError):
    """Raised when email delivery fails."""

    def __init__(self, message: str, provider_error: str | None = None) -> None:
        super().__init__(message)
        self.provider_error = provider_error


class RateLimitError(EmailError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class InvalidRecipientError(EmailError):
    """Raised when recipient address is invalid."""

    def __init__(self, message: str, recipient: str) -> None:
        super().__init__(message)
        self.recipient = recipient


class EmailStatus(str, Enum):
    """Status of an email send operation."""

    SENT = "sent"
    QUEUED = "queued"
    FAILED = "failed"


@dataclass
class Attachment:
    """Email attachment.

    Attributes:
        filename: Name of the file
        content: File content as bytes
        content_type: MIME type (e.g., "application/pdf")
        content_id: Optional content ID for inline attachments (e.g., images in HTML)
    """

    filename: str
    content: bytes
    content_type: str
    content_id: str | None = None


@dataclass
class EmailMessage:
    """Email message to send.

    Attributes:
        to: Recipient email address(es)
        subject: Email subject line
        html: HTML body content
        text: Plain text body content (auto-generated from HTML if not provided)
        from_addr: Sender email address (uses default if not provided)
        reply_to: Reply-to email address
        cc: Carbon copy recipients
        bcc: Blind carbon copy recipients
        attachments: List of file attachments
        headers: Custom email headers
        tags: Tags for categorization/tracking (provider-specific)
        metadata: Additional metadata (provider-specific)

    Example:
        >>> msg = EmailMessage(
        ...     to="user@example.com",
        ...     subject="Welcome!",
        ...     html="<h1>Hello</h1><p>Welcome to our service.</p>",
        ... )
        >>>
        >>> # Multiple recipients
        >>> msg = EmailMessage(
        ...     to=["user1@example.com", "user2@example.com"],
        ...     subject="Team Update",
        ...     html="<p>Here's the latest update...</p>",
        ...     cc=["manager@example.com"],
        ... )
    """

    to: str | list[str]
    subject: str
    html: str | None = None
    text: str | None = None
    from_addr: str | None = None
    reply_to: str | None = None
    cc: list[str] | None = None
    bcc: list[str] | None = None
    attachments: list[Attachment] | None = None
    headers: dict[str, str] | None = None
    tags: list[str] | None = None
    metadata: dict[str, str] | None = None

    def __post_init__(self) -> None:
        """Validate message after initialization."""
        if not self.html and not self.text:
            raise ValueError("Either html or text body must be provided")

        # Normalize to list
        if isinstance(self.to, str):
            self.to = [self.to]


@dataclass
class EmailResult:
    """Result of an email send operation.

    Attributes:
        message_id: Provider-assigned message ID
        provider: Name of the email provider used
        status: Status of the operation
        error: Error message if status is FAILED
        raw_response: Raw response from the provider (for debugging)

    Example:
        >>> result = await email.send(msg)
        >>> if result.status == EmailStatus.SENT:
        ...     print(f"Email sent with ID: {result.message_id}")
        ... else:
        ...     print(f"Email failed: {result.error}")
    """

    message_id: str | None = None
    provider: str = ""
    status: EmailStatus = EmailStatus.SENT
    error: str | None = None
    raw_response: dict | None = field(default=None, repr=False)


@runtime_checkable
class EmailBackend(Protocol):
    """
    Abstract email backend interface.

    All email backends must implement this protocol to be compatible
    with the email system.

    Example:
        >>> from svc_infra.email import EmailBackend, EmailMessage
        >>>
        >>> class MyBackend:
        ...     async def send(self, message: EmailMessage) -> EmailResult:
        ...         # Custom implementation
        ...         ...
        ...     def send_sync(self, message: EmailMessage) -> EmailResult:
        ...         # Sync fallback
        ...         ...
        >>>
        >>> # MyBackend is now a valid EmailBackend
    """

    async def send(self, message: EmailMessage) -> EmailResult:
        """
        Send an email asynchronously.

        Args:
            message: Email message to send

        Returns:
            Result of the send operation

        Raises:
            ConfigurationError: If email is not properly configured
            DeliveryError: If email delivery fails
            RateLimitError: If rate limit is exceeded
            InvalidRecipientError: If recipient is invalid

        Example:
            >>> result = await backend.send(EmailMessage(
            ...     to="user@example.com",
            ...     subject="Hello",
            ...     html="<p>Hello!</p>",
            ... ))
        """
        ...

    def send_sync(self, message: EmailMessage) -> EmailResult:
        """
        Send an email synchronously.

        This is a blocking version for use in sync contexts.
        Prefer `send()` for async applications.

        Args:
            message: Email message to send

        Returns:
            Result of the send operation

        Raises:
            ConfigurationError: If email is not properly configured
            DeliveryError: If email delivery fails
            RateLimitError: If rate limit is exceeded
            InvalidRecipientError: If recipient is invalid
        """
        ...

    @property
    def provider_name(self) -> str:
        """Return the name of the email provider."""
        ...
