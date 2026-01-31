"""
Brevo email backend (formerly Sendinblue).

Sends emails via Brevo's transactional email API.
Uses httpx for async HTTP requests.
"""

from __future__ import annotations

import logging
from typing import Any, ClassVar

from ..base import (
    ConfigurationError,
    DeliveryError,
    EmailMessage,
    EmailResult,
    EmailStatus,
    RateLimitError,
)

logger = logging.getLogger(__name__)

# Brevo API base URL
BREVO_API_URL = "https://api.brevo.com/v3"


class BrevoBackend:
    """
    Brevo email backend for transactional email (formerly Sendinblue).

    Brevo is a European email platform with strong GDPR compliance,
    generous free tier (300 emails/day), and marketing integration.

    Attributes:
        api_key: Brevo API key
        from_addr: Default sender address
        from_name: Default sender name
        tags: Default tags for tracking

    Example:
        >>> from svc_infra.email.backends import BrevoBackend
        >>> from svc_infra.email import EmailMessage
        >>>
        >>> backend = BrevoBackend(
        ...     api_key="xkeysib-xxxxx",
        ...     from_addr="noreply@example.com",
        ...     from_name="My App",
        ... )
        >>> result = await backend.send(EmailMessage(
        ...     to="user@example.com",
        ...     subject="Welcome!",
        ...     html="<h1>Hello!</h1>",
        ...     tags=["welcome"],
        ... ))

    Note:
        Get your API key from https://app.brevo.com/settings/keys/api
        Sender must be verified in Brevo dashboard.
        Brevo has a generous free tier: 300 emails/day.
    """

    provider_name: ClassVar[str] = "brevo"

    def __init__(
        self,
        api_key: str | None = None,
        from_addr: str | None = None,
        from_name: str | None = None,
        tags: list[str] | None = None,
        reply_to: str | None = None,
    ) -> None:
        """
        Initialize Brevo backend.

        Args:
            api_key: Brevo API key (required)
            from_addr: Default sender email address
            from_name: Default sender display name
            tags: Default tags for email tracking
            reply_to: Default reply-to address

        Raises:
            ConfigurationError: If API key is not provided
        """
        if not api_key:
            raise ConfigurationError(
                "Brevo API key is required. Set EMAIL_BREVO_API_KEY environment variable."
            )

        self.api_key = api_key
        self.from_addr = from_addr
        self.from_name = from_name
        self.default_tags = tags or []
        self.default_reply_to = reply_to

    async def send(self, message: EmailMessage) -> EmailResult:
        """
        Send email asynchronously via Brevo API.

        Args:
            message: Email message to send

        Returns:
            EmailResult with message ID and status

        Raises:
            DeliveryError: If email sending fails
            RateLimitError: If rate limit is exceeded
            ConfigurationError: If sender not configured
        """
        try:
            import httpx
        except ImportError as e:
            raise ImportError(
                "Brevo backend requires httpx. Install with: pip install httpx"
            ) from e

        payload = self._build_payload(message)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{BREVO_API_URL}/smtp/email",
                    json=payload,
                    headers={
                        "api-key": self.api_key,
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    timeout=30.0,
                )

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    raise RateLimitError(
                        "Brevo rate limit exceeded",
                        retry_after=int(retry_after) if retry_after else None,
                    )

                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    error_message = error_data.get("message", response.text)
                    raise DeliveryError(
                        f"Brevo API error: {error_message}",
                        provider_error=error_message,
                    )

                response_data = response.json()
                message_id = response_data.get("messageId", "")

                logger.info(f"Email sent via Brevo: {message_id} to {message.to}")

                return EmailResult(
                    message_id=message_id,
                    provider=self.provider_name,
                    status=EmailStatus.SENT,
                    raw_response=response_data,
                )

            except httpx.TimeoutException as e:
                raise DeliveryError(
                    "Brevo API timeout",
                    provider_error=str(e),
                ) from e
            except httpx.RequestError as e:
                raise DeliveryError(
                    f"Brevo API request failed: {e}",
                    provider_error=str(e),
                ) from e

    def send_sync(self, message: EmailMessage) -> EmailResult:
        """
        Send email synchronously via Brevo API.

        Args:
            message: Email message to send

        Returns:
            EmailResult with message ID and status
        """
        try:
            import httpx
        except ImportError as e:
            raise ImportError(
                "Brevo backend requires httpx. Install with: pip install httpx"
            ) from e

        payload = self._build_payload(message)

        with httpx.Client() as client:
            try:
                response = client.post(
                    f"{BREVO_API_URL}/smtp/email",
                    json=payload,
                    headers={
                        "api-key": self.api_key,
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    timeout=30.0,
                )

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    raise RateLimitError(
                        "Brevo rate limit exceeded",
                        retry_after=int(retry_after) if retry_after else None,
                    )

                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    error_message = error_data.get("message", response.text)
                    raise DeliveryError(
                        f"Brevo API error: {error_message}",
                        provider_error=error_message,
                    )

                response_data = response.json()
                message_id = response_data.get("messageId", "")

                logger.info(f"Email sent via Brevo (sync): {message_id} to {message.to}")

                return EmailResult(
                    message_id=message_id,
                    provider=self.provider_name,
                    status=EmailStatus.SENT,
                    raw_response=response_data,
                )

            except httpx.TimeoutException as e:
                raise DeliveryError(
                    "Brevo API timeout",
                    provider_error=str(e),
                ) from e
            except httpx.RequestError as e:
                raise DeliveryError(
                    f"Brevo API request failed: {e}",
                    provider_error=str(e),
                ) from e

    def _build_payload(self, message: EmailMessage) -> dict[str, Any]:
        """Build Brevo API payload from EmailMessage."""
        from_addr = message.from_addr or self.from_addr
        if not from_addr:
            raise ConfigurationError(
                "No sender address. Set from_addr in message or EMAIL_FROM env var."
            )

        # Build recipients (Brevo expects list of {email, name} objects)
        to_list = message.to if isinstance(message.to, list) else [message.to]
        recipients = [{"email": email} for email in to_list]

        # Build sender object
        sender: dict[str, str] = {"email": from_addr}
        if self.from_name:
            sender["name"] = self.from_name

        payload: dict[str, Any] = {
            "sender": sender,
            "to": recipients,
            "subject": message.subject,
        }

        # Add body content
        if message.html:
            payload["htmlContent"] = message.html
        if message.text:
            payload["textContent"] = message.text

        # Add optional fields
        if message.cc:
            cc_list = message.cc if isinstance(message.cc, list) else [message.cc]
            payload["cc"] = [{"email": email} for email in cc_list]
        if message.bcc:
            bcc_list = message.bcc if isinstance(message.bcc, list) else [message.bcc]
            payload["bcc"] = [{"email": email} for email in bcc_list]

        reply_to = message.reply_to or self.default_reply_to
        if reply_to:
            payload["replyTo"] = {"email": reply_to}

        # Add tags
        tags = list(self.default_tags)
        if message.tags:
            tags.extend(message.tags)
        if tags:
            # Brevo supports up to 10 tags
            payload["tags"] = tags[:10]

        # Add custom headers
        if message.headers:
            payload["headers"] = message.headers

        # Handle attachments
        if message.attachments:
            import base64

            payload["attachment"] = [
                {
                    "name": att.filename,
                    "content": base64.b64encode(att.content).decode("utf-8"),
                }
                for att in message.attachments
            ]

        return payload
