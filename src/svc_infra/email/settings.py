"""
Email configuration and settings.

Handles environment-based configuration and auto-detection of email backends.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class EmailSettings(BaseSettings):
    """
    Email system configuration.

    Supports multiple backends with auto-detection from environment variables.

    Environment Variables:
        EMAIL_BACKEND: Explicit backend selection ("console", "smtp", "resend", "sendgrid", "ses", "postmark")
        EMAIL_FROM: Default sender email address
        EMAIL_REPLY_TO: Default reply-to address

        SMTP Backend:
            EMAIL_SMTP_HOST: SMTP server hostname
            EMAIL_SMTP_PORT: SMTP server port (default: 587)
            EMAIL_SMTP_USERNAME: SMTP username
            EMAIL_SMTP_PASSWORD: SMTP password
            EMAIL_SMTP_USE_TLS: Use STARTTLS (default: True)
            EMAIL_SMTP_USE_SSL: Use SSL/TLS (default: False)

        Resend Backend:
            EMAIL_RESEND_API_KEY: Resend API key

        SendGrid Backend:
            EMAIL_SENDGRID_API_KEY: SendGrid API key

        AWS SES Backend:
            EMAIL_SES_REGION: AWS region (default: us-east-1)
            EMAIL_SES_ACCESS_KEY: AWS access key (optional, uses default chain)
            EMAIL_SES_SECRET_KEY: AWS secret key (optional, uses default chain)

        Postmark Backend:
            EMAIL_POSTMARK_API_TOKEN: Postmark server API token
            EMAIL_POSTMARK_MESSAGE_STREAM: Message stream (default: outbound)

        Templates:
            EMAIL_TEMPLATES_PATH: Custom templates directory (optional)

    Example:
        >>> # Auto-detect backend from environment
        >>> settings = EmailSettings()
        >>> backend = settings.detect_backend()
        >>>
        >>> # Check if configured for production
        >>> if not settings.is_configured:
        ...     raise ConfigurationError("Email not configured")
    """

    model_config = SettingsConfigDict(
        env_prefix="EMAIL_",
        env_file=".env",
        extra="ignore",
    )

    # Backend selection
    backend: Literal["console", "smtp", "resend", "sendgrid", "ses", "postmark"] | None = Field(
        default=None,
        description="Email backend type (auto-detected if not set)",
    )

    # Common settings
    from_addr: str | None = Field(
        default=None,
        alias="from",
        validation_alias="EMAIL_FROM",
        description="Default sender email address",
    )
    reply_to: str | None = Field(
        default=None,
        description="Default reply-to address",
    )

    # SMTP backend settings
    smtp_host: str | None = Field(
        default=None,
        description="SMTP server hostname",
    )
    smtp_port: int = Field(
        default=587,
        description="SMTP server port",
    )
    smtp_username: str | None = Field(
        default=None,
        description="SMTP username",
    )
    smtp_password: SecretStr | None = Field(
        default=None,
        description="SMTP password",
    )
    smtp_use_tls: bool = Field(
        default=True,
        description="Use STARTTLS for SMTP connection",
    )
    smtp_use_ssl: bool = Field(
        default=False,
        description="Use SSL/TLS for SMTP connection (port 465)",
    )

    # Resend backend settings
    resend_api_key: SecretStr | None = Field(
        default=None,
        description="Resend API key",
    )

    # SendGrid backend settings
    sendgrid_api_key: SecretStr | None = Field(
        default=None,
        description="SendGrid API key",
    )

    # AWS SES backend settings
    ses_region: str = Field(
        default="us-east-1",
        description="AWS region for SES",
    )
    ses_access_key: SecretStr | None = Field(
        default=None,
        description="AWS access key (optional, uses default credentials chain)",
    )
    ses_secret_key: SecretStr | None = Field(
        default=None,
        description="AWS secret key (optional, uses default credentials chain)",
    )

    # Postmark backend settings
    postmark_api_token: SecretStr | None = Field(
        default=None,
        description="Postmark server API token",
    )
    postmark_message_stream: str = Field(
        default="outbound",
        description="Postmark message stream",
    )

    # Template settings
    templates_path: str | None = Field(
        default=None,
        description="Custom templates directory path",
    )

    def detect_backend(self) -> str:
        """
        Auto-detect email backend from environment.

        Detection Order:
            1. Explicit EMAIL_BACKEND setting
            2. EMAIL_RESEND_API_KEY → resend
            3. EMAIL_SENDGRID_API_KEY → sendgrid
            4. EMAIL_SES_REGION or AWS credentials → ses
            5. EMAIL_POSTMARK_API_TOKEN → postmark
            6. EMAIL_SMTP_HOST → smtp
            7. Default: console (development)

        Returns:
            Backend type string

        Example:
            >>> settings = EmailSettings()
            >>> backend_type = settings.detect_backend()
            >>> print(backend_type)
            "resend"
        """
        # Explicit backend takes priority
        if self.backend:
            return self.backend

        # Auto-detect from credentials
        if self.resend_api_key:
            return "resend"

        if self.sendgrid_api_key:
            return "sendgrid"

        if self.postmark_api_token:
            return "postmark"

        # Check for AWS SES (via explicit config or default chain)
        if self.ses_access_key or os.getenv("AWS_ACCESS_KEY_ID"):
            return "ses"

        # Check for SMTP configuration
        if self.smtp_host:
            return "smtp"

        # Default to console for development
        return "console"

    @property
    def is_configured(self) -> bool:
        """
        Check if email is properly configured for production.

        Returns:
            True if a non-console backend can be used

        Example:
            >>> settings = EmailSettings()
            >>> if not settings.is_configured:
            ...     logger.warning("Email not configured, using console backend")
        """
        detected = self.detect_backend()
        return detected != "console"

    @property
    def has_sender(self) -> bool:
        """
        Check if a default sender address is configured.

        Returns:
            True if EMAIL_FROM is set
        """
        return self.from_addr is not None


@lru_cache
def get_email_settings() -> EmailSettings:
    """
    Get cached email settings instance.

    Returns:
        EmailSettings instance (cached)

    Example:
        >>> settings = get_email_settings()
        >>> print(settings.detect_backend())
    """
    return EmailSettings()
