"""
Email infrastructure for svc-infra.

Provides a unified email sending API with multiple backend support:
- Console (development - prints to stdout)
- SMTP (standard email servers)
- Resend (modern transactional email)
- SendGrid (enterprise email)
- AWS SES (cost-effective, AWS-native)
- Postmark (transactional focus)

Quick Start:
    >>> from svc_infra.email import add_email, easy_email, get_email
    >>> from fastapi import FastAPI, Depends
    >>>
    >>> app = FastAPI()
    >>>
    >>> # Auto-detect backend from environment
    >>> email = add_email(app)
    >>>
    >>> # Or create standalone
    >>> email = easy_email()

Usage in Routes:
    >>> from svc_infra.email import get_email, EmailBackend, EmailMessage
    >>> from fastapi import Depends
    >>>
    >>> @router.post("/notify")
    >>> async def notify_user(
    ...     user_email: str,
    ...     email: EmailBackend = Depends(get_email),
    ... ):
    ...     result = await email.send(EmailMessage(
    ...         to=user_email,
    ...         subject="Notification",
    ...         html="<p>You have a new notification.</p>",
    ...     ))
    ...     return {"message_id": result.message_id}

Environment Variables:
    EMAIL_BACKEND: Backend type (console, smtp, resend, sendgrid, ses, postmark)
    EMAIL_FROM: Default sender email address
    EMAIL_REPLY_TO: Default reply-to address

    SMTP:
        EMAIL_SMTP_HOST: SMTP server hostname
        EMAIL_SMTP_PORT: SMTP port (default: 587)
        EMAIL_SMTP_USERNAME: SMTP username
        EMAIL_SMTP_PASSWORD: SMTP password

    Resend:
        EMAIL_RESEND_API_KEY: Resend API key

    SendGrid:
        EMAIL_SENDGRID_API_KEY: SendGrid API key

    AWS SES:
        EMAIL_SES_REGION: AWS region (default: us-east-1)
        EMAIL_SES_ACCESS_KEY: AWS access key
        EMAIL_SES_SECRET_KEY: AWS secret key

    Postmark:
        EMAIL_POSTMARK_API_TOKEN: Postmark API token
        EMAIL_POSTMARK_MESSAGE_STREAM: Message stream (default: outbound)

See Also:
    - docs/email.md: Comprehensive email guide
    - examples/email/: Working examples
"""

from __future__ import annotations

from .add import (
    EmailDep,
    SenderDep,
    add_email,
    add_sender,
    get_email,
    get_sender,
    health_check_email,
)
from .base import (
    Attachment,
    ConfigurationError,
    DeliveryError,
    EmailBackend,
    EmailError,
    EmailMessage,
    EmailResult,
    EmailStatus,
    InvalidRecipientError,
    RateLimitError,
)
from .easy import easy_email, easy_sender
from .sender import EmailSender
from .settings import EmailSettings, get_email_settings

# Template system (optional - requires jinja2)
try:
    from .templates import EmailTemplateLoader as EmailTemplateLoader
except ImportError:
    EmailTemplateLoader = None  # type: ignore[misc, assignment]

__all__ = [
    # Main API - Low-level (backend)
    "add_email",
    "easy_email",
    "get_email",
    "health_check_email",
    # Main API - High-level (sender with templates)
    "add_sender",
    "easy_sender",
    "get_sender",
    "EmailSender",
    # Dependency injection
    "EmailDep",
    "SenderDep",
    # Base types
    "EmailBackend",
    "EmailMessage",
    "EmailResult",
    "EmailStatus",
    "Attachment",
    # Settings
    "EmailSettings",
    "get_email_settings",
    # Templates
    "EmailTemplateLoader",
    # Exceptions
    "EmailError",
    "ConfigurationError",
    "DeliveryError",
    "RateLimitError",
    "InvalidRecipientError",
]
