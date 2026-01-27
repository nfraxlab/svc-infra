"""
Easy email backend builder with auto-detection.

Simplifies email backend initialization with sensible defaults.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from .backends import ConsoleBackend
from .base import ConfigurationError, EmailBackend
from .settings import get_email_settings

if TYPE_CHECKING:
    from .sender import EmailSender

logger = logging.getLogger(__name__)


def easy_email(
    backend: str | None = None,
    **kwargs,
) -> EmailBackend:
    """
    Create an email backend with auto-detection or explicit selection.

    This is the recommended way to initialize email in most applications.
    It handles environment-based configuration and provides sensible defaults.

    Args:
        backend: Explicit backend type ("console", "smtp", "resend", "sendgrid", "ses", "postmark")
                If None, auto-detects from environment variables
        **kwargs: Backend-specific configuration overrides

    Returns:
        Initialized email backend

    Auto-Detection Order:
        1. Explicit backend parameter
        2. EMAIL_BACKEND environment variable
        3. EMAIL_RESEND_API_KEY → Resend
        4. EMAIL_SENDGRID_API_KEY → SendGrid
        5. EMAIL_MAILGUN_API_KEY → Mailgun
        6. EMAIL_BREVO_API_KEY → Brevo
        7. EMAIL_POSTMARK_API_TOKEN → Postmark
        8. AWS credentials → SES
        9. EMAIL_SMTP_HOST → SMTP
        10. Default: Console (with warning in production)

    Examples:
        >>> # Auto-detect backend from environment
        >>> email = easy_email()
        >>>
        >>> # Explicit console backend (development)
        >>> email = easy_email(backend="console")
        >>>
        >>> # Explicit Resend backend
        >>> email = easy_email(backend="resend", api_key="re_xxx")
        >>>
        >>> # Explicit SMTP backend
        >>> email = easy_email(
        ...     backend="smtp",
        ...     host="smtp.gmail.com",
        ...     username="user@gmail.com",
        ...     password="app-password",
        ... )

    Environment Variables:
        See EmailSettings for full list of environment variables.

    Raises:
        ConfigurationError: If backend is not supported or configuration is invalid
        ImportError: If required backend dependencies are not installed

    Note:
        For production deployments, set EMAIL_BACKEND explicitly and
        ensure EMAIL_FROM is configured for the default sender.
    """
    # Load settings
    settings = get_email_settings()

    # Determine backend type
    backend_type = backend or settings.detect_backend()

    logger.info(f"Initializing {backend_type} email backend")

    # Create backend instance
    if backend_type == "console":
        # Console backend for development
        if not backend and _is_production():
            logger.warning(
                "Using ConsoleBackend in production. "
                "Emails will NOT be delivered. "
                "Set EMAIL_BACKEND or configure a provider."
            )

        log_level = kwargs.get("log_level", logging.INFO)
        truncate_body = kwargs.get("truncate_body", 500)
        return ConsoleBackend(log_level=log_level, truncate_body=truncate_body)

    elif backend_type == "smtp":
        # SMTP backend
        try:
            from .backends.smtp import SMTPBackend
        except ImportError as e:
            raise ImportError(
                "SMTP backend requires aiosmtplib. Install with: pip install aiosmtplib"
            ) from e

        return SMTPBackend(
            host=kwargs.get("host", settings.smtp_host),
            port=kwargs.get("port", settings.smtp_port),
            username=kwargs.get("username", settings.smtp_username),
            password=kwargs.get(
                "password",
                settings.smtp_password.get_secret_value() if settings.smtp_password else None,
            ),
            use_tls=kwargs.get("use_tls", settings.smtp_use_tls),
            use_ssl=kwargs.get("use_ssl", settings.smtp_use_ssl),
            from_addr=kwargs.get("from_addr", settings.from_addr),
        )

    elif backend_type == "resend":
        # Resend backend
        try:
            from .backends.resend import ResendBackend
        except ImportError as e:
            raise ImportError(
                "Resend backend requires httpx. Install with: pip install httpx"
            ) from e

        api_key = kwargs.get(
            "api_key",
            settings.resend_api_key.get_secret_value() if settings.resend_api_key else None,
        )
        if not api_key:
            raise ConfigurationError(
                "Resend backend requires EMAIL_RESEND_API_KEY environment variable"
            )

        return ResendBackend(
            api_key=api_key,
            from_addr=kwargs.get("from_addr", settings.from_addr),
        )

    elif backend_type == "sendgrid":
        # SendGrid backend
        try:
            from .backends.sendgrid import SendGridBackend
        except ImportError as e:
            raise ImportError(
                "SendGrid backend requires httpx. Install with: pip install httpx"
            ) from e

        api_key = kwargs.get(
            "api_key",
            settings.sendgrid_api_key.get_secret_value() if settings.sendgrid_api_key else None,
        )
        if not api_key:
            raise ConfigurationError(
                "SendGrid backend requires EMAIL_SENDGRID_API_KEY environment variable"
            )

        return SendGridBackend(
            api_key=api_key,
            from_addr=kwargs.get("from_addr", settings.from_addr),
        )

    elif backend_type == "ses":
        # AWS SES backend
        try:
            from .backends.ses import SESBackend
        except ImportError as e:
            raise ImportError(
                "SES backend requires aioboto3. Install with: pip install aioboto3"
            ) from e

        return SESBackend(
            region=kwargs.get("region", settings.ses_region),
            access_key=kwargs.get(
                "access_key",
                settings.ses_access_key.get_secret_value() if settings.ses_access_key else None,
            ),
            secret_key=kwargs.get(
                "secret_key",
                settings.ses_secret_key.get_secret_value() if settings.ses_secret_key else None,
            ),
            from_addr=kwargs.get("from_addr", settings.from_addr),
        )

    elif backend_type == "postmark":
        # Postmark backend
        try:
            from .backends.postmark import PostmarkBackend
        except ImportError as e:
            raise ImportError(
                "Postmark backend requires httpx. Install with: pip install httpx"
            ) from e

        api_token = kwargs.get(
            "api_token",
            settings.postmark_api_token.get_secret_value() if settings.postmark_api_token else None,
        )
        if not api_token:
            raise ConfigurationError(
                "Postmark backend requires EMAIL_POSTMARK_API_TOKEN environment variable"
            )

        return PostmarkBackend(
            api_token=api_token,
            message_stream=kwargs.get("message_stream", settings.postmark_message_stream),
            from_addr=kwargs.get("from_addr", settings.from_addr),
        )

    elif backend_type == "mailgun":
        # Mailgun backend
        try:
            from .backends.mailgun import MailgunBackend
        except ImportError as e:
            raise ImportError(
                "Mailgun backend requires httpx. Install with: pip install httpx"
            ) from e

        api_key = kwargs.get(
            "api_key",
            settings.mailgun_api_key.get_secret_value() if settings.mailgun_api_key else None,
        )
        domain = kwargs.get("domain", settings.mailgun_domain)
        if not api_key:
            raise ConfigurationError(
                "Mailgun backend requires EMAIL_MAILGUN_API_KEY environment variable"
            )
        if not domain:
            raise ConfigurationError(
                "Mailgun backend requires EMAIL_MAILGUN_DOMAIN environment variable"
            )

        return MailgunBackend(
            api_key=api_key,
            domain=domain,
            region=kwargs.get("region", settings.mailgun_region),
            from_addr=kwargs.get("from_addr", settings.from_addr),
        )

    elif backend_type == "brevo":
        # Brevo backend (formerly Sendinblue)
        try:
            from .backends.brevo import BrevoBackend
        except ImportError as e:
            raise ImportError(
                "Brevo backend requires httpx. Install with: pip install httpx"
            ) from e

        api_key = kwargs.get(
            "api_key",
            settings.brevo_api_key.get_secret_value() if settings.brevo_api_key else None,
        )
        if not api_key:
            raise ConfigurationError(
                "Brevo backend requires EMAIL_BREVO_API_KEY environment variable"
            )

        return BrevoBackend(
            api_key=api_key,
            from_addr=kwargs.get("from_addr", settings.from_addr),
        )

    else:
        raise ConfigurationError(f"Unsupported email backend: {backend_type}")


def easy_sender(
    backend: str | None = None,
    *,
    app_name: str = "Our Service",
    app_url: str = "",
    support_email: str = "",
    unsubscribe_url: str = "",
    **kwargs,
) -> EmailSender:
    """
    Create an EmailSender with auto-detection or explicit backend.

    This is the recommended high-level API for sending emails with templates.
    It wraps easy_email() and adds template support and convenience methods.

    Args:
        backend: Explicit backend type (auto-detects if None)
        app_name: Application name for templates
        app_url: Application URL for templates
        support_email: Support email for templates
        unsubscribe_url: Unsubscribe URL for templates
        **kwargs: Backend-specific configuration

    Returns:
        Configured EmailSender instance

    Example:
        >>> sender = easy_sender(app_name="MyApp", app_url="https://myapp.com")
        >>>
        >>> # Send with template
        >>> result = await sender.send(
        ...     to="user@example.com",
        ...     subject="Welcome!",
        ...     template="welcome",
        ...     context={"user_name": "John"},
        ... )
        >>>
        >>> # Use convenience method
        >>> result = await sender.send_verification(
        ...     to="user@example.com",
        ...     code="123456",
        ... )
    """
    from .sender import EmailSender

    email_backend = easy_email(backend=backend, **kwargs)

    return EmailSender(
        backend=email_backend,
        app_name=app_name,
        app_url=app_url,
        support_email=support_email,
        unsubscribe_url=unsubscribe_url,
    )


def _is_production() -> bool:
    """Check if running in production environment."""
    env = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")).lower()
    return env in ("production", "prod", "live")
