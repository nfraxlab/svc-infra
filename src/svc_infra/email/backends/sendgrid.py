"""
SendGrid email backend.

Sends emails via SendGrid's transactional email API.
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

# SendGrid API base URL
SENDGRID_API_URL = "https://api.sendgrid.com/v3"


class SendGridBackend:
    """
    SendGrid email backend for enterprise transactional email.

    SendGrid is a reliable email delivery platform with advanced features
    like dynamic templates and detailed analytics.

    Attributes:
        api_key: SendGrid API key
        from_addr: Default sender address
        from_name: Default sender name
        categories: Default categories for tracking

    Example:
        >>> from svc_infra.email.backends import SendGridBackend
        >>> from svc_infra.email import EmailMessage
        >>>
        >>> backend = SendGridBackend(
        ...     api_key="SG.xxxxx",
        ...     from_addr="noreply@example.com",
        ...     from_name="My App",
        ... )
        >>> result = await backend.send(EmailMessage(
        ...     to="user@example.com",
        ...     subject="Welcome!",
        ...     html="<h1>Hello!</h1>",
        ...     tags=["welcome"],  # Maps to categories
        ... ))

    Note:
        Get your API key from https://app.sendgrid.com/settings/api_keys
        Sender must be verified in SendGrid.
    """

    provider_name: ClassVar[str] = "sendgrid"

    def __init__(
        self,
        api_key: str | None = None,
        from_addr: str | None = None,
        from_name: str | None = None,
        categories: list[str] | None = None,
        sandbox_mode: bool = False,
    ) -> None:
        """
        Initialize SendGrid backend.

        Args:
            api_key: SendGrid API key (required)
            from_addr: Default sender email address
            from_name: Default sender display name
            categories: Default categories for email tracking
            sandbox_mode: If True, emails won't be sent (for testing)

        Raises:
            ConfigurationError: If API key is not provided
        """
        if not api_key:
            raise ConfigurationError(
                "SendGrid API key is required. Set EMAIL_SENDGRID_API_KEY environment variable."
            )

        self.api_key = api_key
        self.from_addr = from_addr
        self.from_name = from_name
        self.default_categories = categories or []
        self.sandbox_mode = sandbox_mode

    async def send(self, message: EmailMessage) -> EmailResult:
        """
        Send email asynchronously via SendGrid API.

        Args:
            message: Email message to send

        Returns:
            EmailResult with message ID and status

        Raises:
            DeliveryError: If email sending fails
            RateLimitError: If rate limit is exceeded
        """
        try:
            import httpx
        except ImportError as e:
            raise ImportError(
                "SendGrid backend requires httpx. Install with: pip install httpx"
            ) from e

        payload = self._build_payload(message)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{SENDGRID_API_URL}/mail/send",
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
                        "SendGrid rate limit exceeded",
                        retry_after=int(retry_after) if retry_after else None,
                    )

                # SendGrid returns 202 for successful send
                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    errors = error_data.get("errors", [])
                    error_message = errors[0].get("message") if errors else response.text
                    raise DeliveryError(
                        f"SendGrid API error: {error_message}",
                        provider_error=error_message,
                    )

                # SendGrid returns message ID in header
                message_id = response.headers.get("X-Message-Id", "")

                logger.info(f"Email sent via SendGrid: {message_id} to {message.to}")

                return EmailResult(
                    message_id=message_id,
                    provider=self.provider_name,
                    status=EmailStatus.QUEUED if self.sandbox_mode else EmailStatus.SENT,
                )

            except httpx.TimeoutException as e:
                raise DeliveryError(
                    "SendGrid API timeout",
                    provider_error=str(e),
                ) from e
            except httpx.RequestError as e:
                raise DeliveryError(
                    f"SendGrid API request failed: {e}",
                    provider_error=str(e),
                ) from e

    def send_sync(self, message: EmailMessage) -> EmailResult:
        """
        Send email synchronously via SendGrid API.

        Args:
            message: Email message to send

        Returns:
            EmailResult with message ID and status
        """
        try:
            import httpx
        except ImportError as e:
            raise ImportError(
                "SendGrid backend requires httpx. Install with: pip install httpx"
            ) from e

        payload = self._build_payload(message)

        with httpx.Client() as client:
            try:
                response = client.post(
                    f"{SENDGRID_API_URL}/mail/send",
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
                        "SendGrid rate limit exceeded",
                        retry_after=int(retry_after) if retry_after else None,
                    )

                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    errors = error_data.get("errors", [])
                    error_message = errors[0].get("message") if errors else response.text
                    raise DeliveryError(
                        f"SendGrid API error: {error_message}",
                        provider_error=error_message,
                    )

                message_id = response.headers.get("X-Message-Id", "")

                logger.info(f"Email sent via SendGrid (sync): {message_id} to {message.to}")

                return EmailResult(
                    message_id=message_id,
                    provider=self.provider_name,
                    status=EmailStatus.QUEUED if self.sandbox_mode else EmailStatus.SENT,
                )

            except httpx.TimeoutException as e:
                raise DeliveryError(
                    "SendGrid API timeout",
                    provider_error=str(e),
                ) from e
            except httpx.RequestError as e:
                raise DeliveryError(
                    f"SendGrid API request failed: {e}",
                    provider_error=str(e),
                ) from e

    def _build_payload(self, message: EmailMessage) -> dict[str, Any]:
        """Build SendGrid API payload from EmailMessage."""
        from_addr = message.from_addr or self.from_addr
        if not from_addr:
            raise ConfigurationError(
                "No sender address. Set from_addr in message or EMAIL_FROM env var."
            )

        # Build recipients
        to_list = message.to if isinstance(message.to, list) else [message.to]

        personalizations: dict[str, Any] = {
            "to": [{"email": email} for email in to_list],
        }

        if message.cc:
            personalizations["cc"] = [{"email": email} for email in message.cc]
        if message.bcc:
            personalizations["bcc"] = [{"email": email} for email in message.bcc]

        # Build from field
        from_field: dict[str, str] = {"email": from_addr}
        if self.from_name:
            from_field["name"] = self.from_name

        payload: dict[str, Any] = {
            "personalizations": [personalizations],
            "from": from_field,
            "subject": message.subject,
        }

        # Add content
        content = []
        if message.text:
            content.append({"type": "text/plain", "value": message.text})
        if message.html:
            content.append({"type": "text/html", "value": message.html})

        if content:
            payload["content"] = content

        # Add reply-to
        if message.reply_to:
            payload["reply_to"] = {"email": message.reply_to}

        # Add categories (merge default + message tags)
        categories = list(self.default_categories)
        if message.tags:
            categories.extend(message.tags)
        if categories:
            # SendGrid supports up to 10 categories
            payload["categories"] = categories[:10]

        # Add custom headers
        if message.headers:
            payload["headers"] = message.headers

        # Handle attachments
        if message.attachments:
            import base64

            payload["attachments"] = [
                {
                    "filename": att.filename,
                    "content": base64.b64encode(att.content).decode("utf-8"),
                    "type": att.content_type,
                    **({"content_id": att.content_id} if att.content_id else {}),
                    "disposition": "inline" if att.content_id else "attachment",
                }
                for att in message.attachments
            ]

        # Sandbox mode for testing
        if self.sandbox_mode:
            payload["mail_settings"] = {"sandbox_mode": {"enable": True}}

        return payload

    async def send_template(
        self,
        to: str | list[str],
        template_id: str,
        dynamic_data: dict[str, Any] | None = None,
        *,
        from_addr: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        categories: list[str] | None = None,
    ) -> EmailResult:
        """
        Send email using a SendGrid dynamic template.

        Args:
            to: Recipient email address(es)
            template_id: SendGrid template ID (e.g., "d-xxxxx")
            dynamic_data: Template variables
            from_addr: Sender email address
            cc: Carbon copy recipients
            bcc: Blind carbon copy recipients
            categories: Email categories for tracking

        Returns:
            EmailResult with message ID and status

        Example:
            >>> result = await backend.send_template(
            ...     to="user@example.com",
            ...     template_id="d-xxxxx",
            ...     dynamic_data={"name": "John", "order_id": "12345"},
            ... )
        """
        try:
            import httpx
        except ImportError as e:
            raise ImportError(
                "SendGrid backend requires httpx. Install with: pip install httpx"
            ) from e

        sender = from_addr or self.from_addr
        if not sender:
            raise ConfigurationError("No sender address configured")

        to_list = to if isinstance(to, list) else [to]

        personalizations: dict[str, Any] = {
            "to": [{"email": email} for email in to_list],
        }

        if dynamic_data:
            personalizations["dynamic_template_data"] = dynamic_data
        if cc:
            personalizations["cc"] = [{"email": email} for email in cc]
        if bcc:
            personalizations["bcc"] = [{"email": email} for email in bcc]

        from_field: dict[str, str] = {"email": sender}
        if self.from_name:
            from_field["name"] = self.from_name

        payload: dict[str, Any] = {
            "personalizations": [personalizations],
            "from": from_field,
            "template_id": template_id,
        }

        # Add categories
        all_categories = list(self.default_categories)
        if categories:
            all_categories.extend(categories)
        if all_categories:
            payload["categories"] = all_categories[:10]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SENDGRID_API_URL}/mail/send",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )

            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                errors = error_data.get("errors", [])
                error_message = errors[0].get("message") if errors else response.text
                raise DeliveryError(
                    f"SendGrid template error: {error_message}",
                    provider_error=error_message,
                )

            message_id = response.headers.get("X-Message-Id", "")

            return EmailResult(
                message_id=message_id,
                provider=self.provider_name,
                status=EmailStatus.SENT,
            )
