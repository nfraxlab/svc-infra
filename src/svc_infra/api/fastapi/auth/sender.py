"""
Email sender for authentication module.

This module provides backward-compatible email sending using the new
svc_infra.email infrastructure. The Sender protocol and get_sender()
function maintain the same interface for existing code.

Migration Note:
    For new code, prefer using svc_infra.email directly:

    >>> from svc_infra.email import easy_sender
    >>> sender = easy_sender(app_name="MyApp")
    >>> await sender.send_verification(to=email, code="123456")
"""

from __future__ import annotations

import os
from typing import Protocol

from svc_infra.app.env import CURRENT_ENVIRONMENT, PROD_ENV

from .settings import get_auth_settings


class Sender(Protocol):
    """Protocol for email senders (backward compatibility)."""

    def send(self, to: str, subject: str, html_body: str) -> None:
        """Send an email synchronously."""
        pass


class _EmailSenderAdapter:
    """
    Adapter that wraps the new email module with the old Sender interface.

    This allows existing code using get_sender().send() to work without changes.
    """

    def __init__(self) -> None:
        from svc_infra.email import easy_email
        from svc_infra.email.base import EmailMessage

        self._backend = easy_email()
        self._EmailMessage = EmailMessage

    def send(self, to: str, subject: str, html_body: str) -> None:
        """Send an email using the new email infrastructure."""
        from svc_infra.email.settings import get_email_settings

        settings = get_email_settings()
        from_addr = settings.from_addr

        if not from_addr:
            # Fall back to AUTH_SMTP_FROM
            auth_settings = get_auth_settings()
            from_addr = auth_settings.smtp_from

        if not from_addr:
            raise RuntimeError(
                "No sender address configured. "
                "Set EMAIL_FROM or AUTH_SMTP_FROM environment variable."
            )

        message = self._EmailMessage(
            to=to,
            subject=subject,
            html=html_body,
            from_addr=from_addr,
        )
        self._backend.send_sync(message)


# Legacy classes for backward compatibility
class ConsoleSender:
    """Console sender - prints emails to stdout (legacy)."""

    def send(self, to: str, subject: str, html_body: str) -> None:
        print(f"[MAIL -> {to}] {subject}\n{html_body}\n")


class SMTPSender:
    """SMTP sender (legacy - use svc_infra.email.backends.SMTPBackend instead)."""

    def __init__(self, host: str, port: int, username: str, password: str, from_addr: str) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_addr = from_addr

    def send(self, to: str, subject: str, html_body: str) -> None:
        import smtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["From"] = self.from_addr
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(html_body, subtype="html")
        with smtplib.SMTP(self.host, self.port) as s:
            s.starttls()
            s.login(self.username, self.password)
            s.send_message(msg)


def _sync_auth_env_to_email_env() -> None:
    """
    Sync AUTH_SMTP_* env vars to EMAIL_* env vars.

    This allows existing deployments using AUTH_SMTP_* to work
    with the new email infrastructure without config changes.
    """
    mappings = [
        ("AUTH_SMTP_HOST", "EMAIL_SMTP_HOST"),
        ("AUTH_SMTP_PORT", "EMAIL_SMTP_PORT"),
        ("AUTH_SMTP_USERNAME", "EMAIL_SMTP_USERNAME"),
        ("AUTH_SMTP_PASSWORD", "EMAIL_SMTP_PASSWORD"),
        ("AUTH_SMTP_FROM", "EMAIL_FROM"),
    ]

    for auth_key, email_key in mappings:
        auth_val = os.environ.get(auth_key)
        if auth_val and not os.environ.get(email_key):
            os.environ[email_key] = auth_val


def get_sender() -> Sender:
    """
    Get an email sender instance.

    Returns a sender that uses the new svc_infra.email infrastructure
    while maintaining backward compatibility with the old interface.

    In production, requires email configuration (either EMAIL_* or AUTH_SMTP_*).
    In development, falls back to console output if not configured.

    Returns:
        Sender instance

    Raises:
        RuntimeError: In production if email is not configured

    Example:
        >>> sender = get_sender()
        >>> sender.send(
        ...     to="user@example.com",
        ...     subject="Hello",
        ...     html_body="<p>Hello World!</p>",
        ... )
    """
    # Sync legacy AUTH_SMTP_* env vars to EMAIL_* env vars
    _sync_auth_env_to_email_env()

    st = get_auth_settings()

    # Check if we have EMAIL_* or AUTH_SMTP_* configuration
    from svc_infra.email.settings import get_email_settings

    # Clear cache to pick up synced env vars
    get_email_settings.cache_clear()
    email_settings = get_email_settings()

    # Check if properly configured
    is_configured = email_settings.is_configured or (
        st.smtp_host and st.smtp_username and st.smtp_password and st.smtp_from
    )

    # In prod, hard error if not configured
    if CURRENT_ENVIRONMENT == PROD_ENV and not is_configured:
        raise RuntimeError(
            "Email is required in prod for verification emails. "
            "Configure EMAIL_* or AUTH_SMTP_* environment variables."
        )

    # Dev fallback: console if not configured
    if not is_configured:
        return ConsoleSender()

    # Use new email infrastructure via adapter
    return _EmailSenderAdapter()
