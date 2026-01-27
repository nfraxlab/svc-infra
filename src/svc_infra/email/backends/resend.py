"""
Resend email backend.

Sends emails via Resend's modern transactional email API.
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

# Resend API base URL
RESEND_API_URL = "https://api.resend.com"


class ResendBackend:
    """
    Resend email backend for modern transactional email.

    Resend is a developer-friendly email API with excellent deliverability.
    This backend uses httpx for async HTTP requests.

    Attributes:
        api_key: Resend API key (starts with 're_')
        from_addr: Default sender address
        tags: Default tags to apply to all emails
        headers: Default headers to include

    Example:
        >>> from svc_infra.email.backends import ResendBackend
        >>> from svc_infra.email import EmailMessage
        >>>
        >>> backend = ResendBackend(
        ...     api_key="re_xxxxx",
        ...     from_addr="noreply@example.com",
        ... )
        >>> result = await backend.send(EmailMessage(
        ...     to="user@example.com",
        ...     subject="Welcome!",
        ...     html="<h1>Hello!</h1>",
        ...     tags=["welcome", "onboarding"],
        ... ))

    Note:
        Get your API key from https://resend.com/api-keys
        Sender domain must be verified in Resend dashboard.
    """

    provider_name: ClassVar[str] = "resend"

    def __init__(
        self,
        api_key: str | None = None,
        from_addr: str | None = None,
        tags: list[str] | None = None,
        reply_to: str | None = None,
    ) -> None:
        """
        Initialize Resend backend.

        Args:
            api_key: Resend API key (required)
            from_addr: Default sender email address
            tags: Default tags to apply to all emails
            reply_to: Default reply-to address

        Raises:
            ConfigurationError: If API key is not provided
        """
        if not api_key:
            raise ConfigurationError(
                "Resend API key is required. Set EMAIL_RESEND_API_KEY environment variable."
            )

        self.api_key = api_key
        self.from_addr = from_addr
        self.default_tags = tags or []
        self.default_reply_to = reply_to

    async def send(self, message: EmailMessage) -> EmailResult:
        """
        Send email asynchronously via Resend API.

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
                "Resend backend requires httpx. Install with: pip install httpx"
            ) from e

        payload = self._build_payload(message)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{RESEND_API_URL}/emails",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    raise RateLimitError(
                        "Resend rate limit exceeded",
                        retry_after=int(retry_after) if retry_after else None,
                    )

                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    error_message = error_data.get("message", response.text)
                    raise DeliveryError(
                        f"Resend API error: {error_message}",
                        provider_error=error_message,
                    )

                data = response.json()
                message_id = data.get("id", "")

                logger.info(f"Email sent via Resend: {message_id} to {message.to}")

                return EmailResult(
                    message_id=message_id,
                    provider=self.provider_name,
                    status=EmailStatus.SENT,
                    raw_response=data,
                )

            except httpx.TimeoutException as e:
                raise DeliveryError(
                    "Resend API timeout",
                    provider_error=str(e),
                ) from e
            except httpx.RequestError as e:
                raise DeliveryError(
                    f"Resend API request failed: {e}",
                    provider_error=str(e),
                ) from e

    def send_sync(self, message: EmailMessage) -> EmailResult:
        """
        Send email synchronously via Resend API.

        Args:
            message: Email message to send

        Returns:
            EmailResult with message ID and status
        """
        try:
            import httpx
        except ImportError as e:
            raise ImportError(
                "Resend backend requires httpx. Install with: pip install httpx"
            ) from e

        payload = self._build_payload(message)

        with httpx.Client() as client:
            try:
                response = client.post(
                    f"{RESEND_API_URL}/emails",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    raise RateLimitError(
                        "Resend rate limit exceeded",
                        retry_after=int(retry_after) if retry_after else None,
                    )

                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    error_message = error_data.get("message", response.text)
                    raise DeliveryError(
                        f"Resend API error: {error_message}",
                        provider_error=error_message,
                    )

                data = response.json()
                message_id = data.get("id", "")

                logger.info(f"Email sent via Resend (sync): {message_id} to {message.to}")

                return EmailResult(
                    message_id=message_id,
                    provider=self.provider_name,
                    status=EmailStatus.SENT,
                    raw_response=data,
                )

            except httpx.TimeoutException as e:
                raise DeliveryError(
                    "Resend API timeout",
                    provider_error=str(e),
                ) from e
            except httpx.RequestError as e:
                raise DeliveryError(
                    f"Resend API request failed: {e}",
                    provider_error=str(e),
                ) from e

    def _build_payload(self, message: EmailMessage) -> dict[str, Any]:
        """Build Resend API payload from EmailMessage."""
        from_addr = message.from_addr or self.from_addr
        if not from_addr:
            raise ConfigurationError(
                "No sender address. Set from_addr in message or EMAIL_FROM env var."
            )

        # Build recipients
        to_list = message.to if isinstance(message.to, list) else [message.to]

        payload: dict[str, Any] = {
            "from": from_addr,
            "to": to_list,
            "subject": message.subject,
        }

        # Add body content
        if message.html:
            payload["html"] = message.html
        if message.text:
            payload["text"] = message.text

        # Add optional fields
        if message.cc:
            payload["cc"] = message.cc
        if message.bcc:
            payload["bcc"] = message.bcc

        reply_to = message.reply_to or self.default_reply_to
        if reply_to:
            payload["reply_to"] = reply_to

        # Add tags (merge default + message tags)
        tags = list(self.default_tags)
        if message.tags:
            tags.extend(message.tags)
        if tags:
            # Resend supports up to 5 tags
            payload["tags"] = [{"name": tag, "value": "true"} for tag in tags[:5]]

        # Add headers
        if message.headers:
            payload["headers"] = message.headers

        # Handle attachments
        if message.attachments:
            import base64

            payload["attachments"] = [
                {
                    "filename": att.filename,
                    "content": base64.b64encode(att.content).decode("utf-8"),
                    "content_type": att.content_type,
                }
                for att in message.attachments
            ]

        return payload
