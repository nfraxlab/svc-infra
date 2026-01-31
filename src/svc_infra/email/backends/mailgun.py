"""
Mailgun email backend.

Sends emails via Mailgun's transactional email API.
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

# Mailgun API base URLs
MAILGUN_API_URL = "https://api.mailgun.net/v3"
MAILGUN_API_URL_EU = "https://api.eu.mailgun.net/v3"


class MailgunBackend:
    """
    Mailgun email backend for transactional email.

    Mailgun is a reliable email delivery platform with advanced features
    like detailed analytics, EU data residency, and inbound routing.

    Attributes:
        api_key: Mailgun API key
        domain: Sending domain (e.g., mg.example.com)
        region: API region ("us" or "eu")
        from_addr: Default sender address
        tags: Default tags for tracking

    Example:
        >>> from svc_infra.email.backends import MailgunBackend
        >>> from svc_infra.email import EmailMessage
        >>>
        >>> backend = MailgunBackend(
        ...     api_key="key-xxxxx",
        ...     domain="mg.example.com",
        ...     from_addr="noreply@example.com",
        ... )
        >>> result = await backend.send(EmailMessage(
        ...     to="user@example.com",
        ...     subject="Welcome!",
        ...     html="<h1>Hello!</h1>",
        ...     tags=["welcome"],
        ... ))

    Note:
        Get your API key from https://app.mailgun.com/settings/api_security
        Sender domain must be verified in Mailgun dashboard.
        Use region="eu" for EU data residency (GDPR compliance).
    """

    provider_name: ClassVar[str] = "mailgun"

    def __init__(
        self,
        api_key: str | None = None,
        domain: str | None = None,
        region: str = "us",
        from_addr: str | None = None,
        tags: list[str] | None = None,
        reply_to: str | None = None,
    ) -> None:
        """
        Initialize Mailgun backend.

        Args:
            api_key: Mailgun API key (required)
            domain: Sending domain (required)
            region: API region - "us" or "eu" (default: "us")
            from_addr: Default sender email address
            tags: Default tags for email tracking
            reply_to: Default reply-to address

        Raises:
            ConfigurationError: If API key or domain is not provided
        """
        if not api_key:
            raise ConfigurationError(
                "Mailgun API key is required. Set EMAIL_MAILGUN_API_KEY environment variable."
            )
        if not domain:
            raise ConfigurationError(
                "Mailgun domain is required. Set EMAIL_MAILGUN_DOMAIN environment variable."
            )

        self.api_key = api_key
        self.domain = domain
        self.region = region.lower()
        self.from_addr = from_addr
        self.default_tags = tags or []
        self.default_reply_to = reply_to

        # Select API base URL based on region
        self.api_base = MAILGUN_API_URL_EU if self.region == "eu" else MAILGUN_API_URL

    async def send(self, message: EmailMessage) -> EmailResult:
        """
        Send email asynchronously via Mailgun API.

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
                "Mailgun backend requires httpx. Install with: pip install httpx"
            ) from e

        data = self._build_payload(message)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_base}/{self.domain}/messages",
                    data=data,
                    auth=("api", self.api_key),
                    timeout=30.0,
                )

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    raise RateLimitError(
                        "Mailgun rate limit exceeded",
                        retry_after=int(retry_after) if retry_after else None,
                    )

                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    error_message = error_data.get("message", response.text)
                    raise DeliveryError(
                        f"Mailgun API error: {error_message}",
                        provider_error=error_message,
                    )

                response_data = response.json()
                message_id = response_data.get("id", "")

                logger.info(f"Email sent via Mailgun: {message_id} to {message.to}")

                return EmailResult(
                    message_id=message_id,
                    provider=self.provider_name,
                    status=EmailStatus.SENT,
                    raw_response=response_data,
                )

            except httpx.TimeoutException as e:
                raise DeliveryError(
                    "Mailgun API timeout",
                    provider_error=str(e),
                ) from e
            except httpx.RequestError as e:
                raise DeliveryError(
                    f"Mailgun API request failed: {e}",
                    provider_error=str(e),
                ) from e

    def send_sync(self, message: EmailMessage) -> EmailResult:
        """
        Send email synchronously via Mailgun API.

        Args:
            message: Email message to send

        Returns:
            EmailResult with message ID and status
        """
        try:
            import httpx
        except ImportError as e:
            raise ImportError(
                "Mailgun backend requires httpx. Install with: pip install httpx"
            ) from e

        data = self._build_payload(message)

        with httpx.Client() as client:
            try:
                response = client.post(
                    f"{self.api_base}/{self.domain}/messages",
                    data=data,
                    auth=("api", self.api_key),
                    timeout=30.0,
                )

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    raise RateLimitError(
                        "Mailgun rate limit exceeded",
                        retry_after=int(retry_after) if retry_after else None,
                    )

                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    error_message = error_data.get("message", response.text)
                    raise DeliveryError(
                        f"Mailgun API error: {error_message}",
                        provider_error=error_message,
                    )

                response_data = response.json()
                message_id = response_data.get("id", "")

                logger.info(f"Email sent via Mailgun (sync): {message_id} to {message.to}")

                return EmailResult(
                    message_id=message_id,
                    provider=self.provider_name,
                    status=EmailStatus.SENT,
                    raw_response=response_data,
                )

            except httpx.TimeoutException as e:
                raise DeliveryError(
                    "Mailgun API timeout",
                    provider_error=str(e),
                ) from e
            except httpx.RequestError as e:
                raise DeliveryError(
                    f"Mailgun API request failed: {e}",
                    provider_error=str(e),
                ) from e

    def _build_payload(self, message: EmailMessage) -> dict[str, Any]:
        """Build Mailgun API payload from EmailMessage."""
        from_addr = message.from_addr or self.from_addr
        if not from_addr:
            raise ConfigurationError(
                "No sender address. Set from_addr in message or EMAIL_FROM env var."
            )

        # Build recipients
        to_list = message.to if isinstance(message.to, list) else [message.to]

        data: dict[str, Any] = {
            "from": from_addr,
            "to": to_list,
            "subject": message.subject,
        }

        # Add body content
        if message.html:
            data["html"] = message.html
        if message.text:
            data["text"] = message.text

        # Add optional fields
        if message.cc:
            data["cc"] = message.cc if isinstance(message.cc, list) else [message.cc]
        if message.bcc:
            data["bcc"] = message.bcc if isinstance(message.bcc, list) else [message.bcc]

        reply_to = message.reply_to or self.default_reply_to
        if reply_to:
            data["h:Reply-To"] = reply_to

        # Add tags (Mailgun calls them "o:tag")
        tags = list(self.default_tags)
        if message.tags:
            tags.extend(message.tags)
        if tags:
            # Mailgun supports multiple o:tag parameters
            data["o:tag"] = tags[:3]  # Mailgun allows up to 3 tags

        # Add custom headers
        if message.headers:
            for key, value in message.headers.items():
                data[f"h:{key}"] = value

        # Note: Attachments require multipart form handling
        # For simplicity, attachments are handled separately if needed

        return data
