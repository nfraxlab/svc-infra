"""
High-level email sending API.

Provides a unified interface for sending emails with template support
and convenience methods for common email types.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .base import (
    Attachment,
    ConfigurationError,
    EmailBackend,
    EmailMessage,
    EmailResult,
    InvalidRecipientError,
)
from .settings import EmailSettings, get_email_settings

if TYPE_CHECKING:
    from .templates.loader import EmailTemplateLoader


# Email validation pattern (basic RFC 5322)
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def validate_email(email: str) -> bool:
    """
    Validate an email address.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    return bool(EMAIL_PATTERN.match(email))


def validate_recipients(recipients: str | list[str]) -> list[str]:
    """
    Validate and normalize recipients list.

    Args:
        recipients: Single email or list of emails

    Returns:
        Normalized list of email addresses

    Raises:
        InvalidRecipientError: If any recipient is invalid
    """
    if isinstance(recipients, str):
        recipients = [recipients]

    validated = []
    for email in recipients:
        email = email.strip()
        if not validate_email(email):
            raise InvalidRecipientError(
                f"Invalid email address: {email}",
                recipient=email,
            )
        validated.append(email)

    return validated


@dataclass
class EmailSender:
    """
    High-level email sender with template support.

    Wraps an EmailBackend with additional functionality:
    - Template rendering with built-in templates
    - Recipient validation
    - Settings-based defaults
    - Convenience methods for common emails

    Example:
        >>> from svc_infra.email import EmailSender
        >>> from svc_infra.email.backends import ConsoleBackend
        >>>
        >>> sender = EmailSender(
        ...     backend=ConsoleBackend(),
        ...     app_name="MyApp",
        ...     app_url="https://myapp.com",
        ... )
        >>>
        >>> # Send with template
        >>> result = await sender.send(
        ...     to="user@example.com",
        ...     subject="Welcome!",
        ...     template="welcome",
        ...     context={"user_name": "John"},
        ... )
        >>>
        >>> # Send verification email
        >>> result = await sender.send_verification(
        ...     to="user@example.com",
        ...     code="123456",
        ...     user_name="John",
        ... )
    """

    backend: EmailBackend
    settings: EmailSettings | None = None
    template_loader: EmailTemplateLoader | None = None

    # Branding (used for templates)
    app_name: str = "Our Service"
    app_url: str = ""
    support_email: str = ""
    unsubscribe_url: str = ""

    def __post_init__(self) -> None:
        """Initialize template loader if templates are available."""
        if self.settings is None:
            self.settings = get_email_settings()

        # Only initialize template loader if not provided and jinja2 is available
        if self.template_loader is None:
            try:
                from .templates.loader import EmailTemplateLoader

                self.template_loader = EmailTemplateLoader(
                    template_dir=self.settings.templates_path,
                    app_name=self.app_name,
                    app_url=self.app_url,
                    support_email=self.support_email,
                    unsubscribe_url=self.unsubscribe_url,
                )
            except ImportError:
                # jinja2 not available, templates disabled
                self.template_loader = None

    async def send(
        self,
        to: str | list[str],
        subject: str,
        *,
        html: str | None = None,
        text: str | None = None,
        template: str | None = None,
        context: dict[str, Any] | None = None,
        from_addr: str | None = None,
        reply_to: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[Attachment] | None = None,
        headers: dict[str, str] | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> EmailResult:
        """
        Send an email with optional template support.

        Args:
            to: Recipient email address(es)
            subject: Email subject line
            html: HTML body content (mutually exclusive with template)
            text: Plain text body content
            template: Template name to render (e.g., "verification")
            context: Context variables for template rendering
            from_addr: Sender address (uses settings default if not provided)
            reply_to: Reply-to address
            cc: Carbon copy recipients
            bcc: Blind carbon copy recipients
            attachments: File attachments
            headers: Custom email headers
            tags: Tags for categorization/tracking
            metadata: Additional metadata

        Returns:
            EmailResult with send status

        Raises:
            InvalidRecipientError: If any recipient is invalid
            ConfigurationError: If template specified but not available
            DeliveryError: If email delivery fails

        Example:
            >>> # Send with raw HTML
            >>> result = await sender.send(
            ...     to="user@example.com",
            ...     subject="Hello",
            ...     html="<p>Hello World!</p>",
            ... )
            >>>
            >>> # Send with template
            >>> result = await sender.send(
            ...     to="user@example.com",
            ...     subject="Verify Your Email",
            ...     template="verification",
            ...     context={"code": "123456", "user_name": "John"},
            ... )
        """
        # Validate recipients
        validated_to = validate_recipients(to)

        if cc:
            cc = validate_recipients(cc)
        if bcc:
            bcc = validate_recipients(bcc)

        # Resolve template if specified
        if template:
            if not self.template_loader:
                raise ConfigurationError(
                    f"Template '{template}' requested but templates are not available. "
                    "Install jinja2: pip install svc-infra[email-templates]"
                )

            if not self.template_loader.template_exists(template):
                raise ConfigurationError(
                    f"Template '{template}' not found. "
                    f"Available templates: {self.template_loader.get_available_templates()}"
                )

            template_context = context or {}
            html, text = self.template_loader.render(template, **template_context)

        # Fall back to settings for from_addr
        if not from_addr and self.settings:
            from_addr = self.settings.from_addr

        if not from_addr:
            raise ConfigurationError(
                "No sender address provided. "
                "Set EMAIL_FROM environment variable or pass from_addr parameter."
            )

        # Build message
        message = EmailMessage(
            to=validated_to,
            subject=subject,
            html=html,
            text=text,
            from_addr=from_addr,
            reply_to=reply_to or (self.settings.reply_to if self.settings else None),
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            headers=headers,
            tags=tags,
            metadata=metadata,
        )

        # Send via backend
        return await self.backend.send(message)

    def send_sync(
        self,
        to: str | list[str],
        subject: str,
        *,
        html: str | None = None,
        text: str | None = None,
        template: str | None = None,
        context: dict[str, Any] | None = None,
        from_addr: str | None = None,
        reply_to: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[Attachment] | None = None,
        headers: dict[str, str] | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> EmailResult:
        """
        Send an email synchronously.

        Same as send() but blocking. Prefer send() for async applications.

        Args:
            See send() for parameter documentation.

        Returns:
            EmailResult with send status
        """
        # Validate recipients
        validated_to = validate_recipients(to)

        if cc:
            cc = validate_recipients(cc)
        if bcc:
            bcc = validate_recipients(bcc)

        # Resolve template if specified
        if template:
            if not self.template_loader:
                raise ConfigurationError(
                    f"Template '{template}' requested but templates are not available. "
                    "Install jinja2: pip install svc-infra[email-templates]"
                )

            if not self.template_loader.template_exists(template):
                raise ConfigurationError(
                    f"Template '{template}' not found. "
                    f"Available templates: {self.template_loader.get_available_templates()}"
                )

            template_context = context or {}
            html, text = self.template_loader.render(template, **template_context)

        # Fall back to settings for from_addr
        if not from_addr and self.settings:
            from_addr = self.settings.from_addr

        if not from_addr:
            raise ConfigurationError(
                "No sender address provided. "
                "Set EMAIL_FROM environment variable or pass from_addr parameter."
            )

        # Build message
        message = EmailMessage(
            to=validated_to,
            subject=subject,
            html=html,
            text=text,
            from_addr=from_addr,
            reply_to=reply_to or (self.settings.reply_to if self.settings else None),
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            headers=headers,
            tags=tags,
            metadata=metadata,
        )

        # Send via backend
        return self.backend.send_sync(message)

    # -------------------------------------------------------------------------
    # Convenience Methods
    # -------------------------------------------------------------------------

    async def send_verification(
        self,
        to: str,
        *,
        code: str | None = None,
        verification_url: str | None = None,
        user_name: str | None = None,
        expires_in: str = "24 hours",
        from_addr: str | None = None,
        tags: list[str] | None = None,
    ) -> EmailResult:
        """
        Send an email verification email.

        Uses the built-in 'verification' template.

        Args:
            to: Recipient email address
            code: Verification code (for code-based verification)
            verification_url: Verification link URL (for link-based verification)
            user_name: Recipient's name for personalization
            expires_in: Human-readable expiration time
            from_addr: Override sender address
            tags: Tags for tracking

        Returns:
            EmailResult with send status

        Example:
            >>> # Code-based verification
            >>> result = await sender.send_verification(
            ...     to="user@example.com",
            ...     code="123456",
            ...     user_name="John",
            ... )
            >>>
            >>> # Link-based verification
            >>> result = await sender.send_verification(
            ...     to="user@example.com",
            ...     verification_url="https://app.com/verify?token=abc123",
            ...     user_name="John",
            ... )
        """
        if not code and not verification_url:
            raise ValueError("Either code or verification_url must be provided")

        return await self.send(
            to=to,
            subject=f"Verify Your Email - {self.app_name}",
            template="verification",
            context={
                "code": code,
                "verification_url": verification_url,
                "user_name": user_name,
                "expires_in": expires_in,
            },
            from_addr=from_addr,
            tags=tags or ["verification", "transactional"],
        )

    async def send_password_reset(
        self,
        to: str,
        *,
        reset_url: str,
        user_name: str | None = None,
        expires_in: str = "1 hour",
        from_addr: str | None = None,
        tags: list[str] | None = None,
    ) -> EmailResult:
        """
        Send a password reset email.

        Uses the built-in 'password_reset' template.

        Args:
            to: Recipient email address
            reset_url: Password reset link URL
            user_name: Recipient's name for personalization
            expires_in: Human-readable expiration time
            from_addr: Override sender address
            tags: Tags for tracking

        Returns:
            EmailResult with send status

        Example:
            >>> result = await sender.send_password_reset(
            ...     to="user@example.com",
            ...     reset_url="https://app.com/reset?token=abc123",
            ...     user_name="Jane",
            ... )
        """
        return await self.send(
            to=to,
            subject=f"Reset Your Password - {self.app_name}",
            template="password_reset",
            context={
                "reset_url": reset_url,
                "user_name": user_name,
                "expires_in": expires_in,
            },
            from_addr=from_addr,
            tags=tags or ["password_reset", "transactional"],
        )

    async def send_invitation(
        self,
        to: str,
        *,
        invitation_url: str,
        inviter_name: str | None = None,
        workspace_name: str | None = None,
        workspace_description: str | None = None,
        role: str | None = None,
        message: str | None = None,
        expires_in: str = "7 days",
        from_addr: str | None = None,
        tags: list[str] | None = None,
    ) -> EmailResult:
        """
        Send a team/workspace invitation email.

        Uses the built-in 'invitation' template.

        Args:
            to: Recipient email address
            invitation_url: Invitation acceptance URL
            inviter_name: Name of the person who sent the invite
            workspace_name: Name of the workspace/team
            workspace_description: Description of the workspace
            role: Role being assigned to the invitee
            message: Personal message from the inviter
            expires_in: Human-readable expiration time
            from_addr: Override sender address
            tags: Tags for tracking

        Returns:
            EmailResult with send status

        Example:
            >>> result = await sender.send_invitation(
            ...     to="new.member@example.com",
            ...     invitation_url="https://app.com/invite/abc123",
            ...     inviter_name="Alice",
            ...     workspace_name="Engineering Team",
            ...     role="Developer",
            ... )
        """
        subject = f"You're Invited to {workspace_name or self.app_name}"

        return await self.send(
            to=to,
            subject=subject,
            template="invitation",
            context={
                "invitation_url": invitation_url,
                "inviter_name": inviter_name,
                "workspace_name": workspace_name,
                "workspace_description": workspace_description,
                "role": role,
                "message": message,
                "expires_in": expires_in,
            },
            from_addr=from_addr,
            tags=tags or ["invitation", "transactional"],
        )

    async def send_welcome(
        self,
        to: str,
        *,
        user_name: str | None = None,
        is_verified: bool = True,
        getting_started_steps: list[str] | None = None,
        features: list[str] | None = None,
        docs_url: str | None = None,
        from_addr: str | None = None,
        tags: list[str] | None = None,
    ) -> EmailResult:
        """
        Send a welcome email.

        Uses the built-in 'welcome' template.

        Args:
            to: Recipient email address
            user_name: Recipient's name for personalization
            is_verified: Whether the user's email is verified
            getting_started_steps: Custom getting started steps
            features: Key features to highlight
            docs_url: Link to documentation
            from_addr: Override sender address
            tags: Tags for tracking

        Returns:
            EmailResult with send status

        Example:
            >>> result = await sender.send_welcome(
            ...     to="user@example.com",
            ...     user_name="John",
            ...     features=["Real-time sync", "Team collaboration", "Advanced analytics"],
            ... )
        """
        return await self.send(
            to=to,
            subject=f"Welcome to {self.app_name}!",
            template="welcome",
            context={
                "user_name": user_name,
                "is_verified": is_verified,
                "getting_started_steps": getting_started_steps,
                "features": features,
                "docs_url": docs_url,
            },
            from_addr=from_addr,
            tags=tags or ["welcome", "onboarding"],
        )
