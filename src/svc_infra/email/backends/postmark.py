"""
Postmark email backend.

Sends emails via Postmark's transactional email API.
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

# Postmark API base URL
POSTMARK_API_URL = "https://api.postmarkapp.com"


class PostmarkBackend:
    """
    Postmark email backend for transactional email.

    Postmark is focused on transactional email with excellent deliverability
    and detailed tracking (opens, clicks, bounces).

    Attributes:
        api_token: Postmark server API token
        message_stream: Message stream ID (default: "outbound")
        from_addr: Default sender address
        track_opens: Enable open tracking (default: True)
        track_links: Enable click tracking (default: None - uses server setting)

    Example:
        >>> from svc_infra.email.backends import PostmarkBackend
        >>> from svc_infra.email import EmailMessage
        >>>
        >>> backend = PostmarkBackend(
        ...     api_token="xxxxx-xxxxx-xxxxx",
        ...     from_addr="noreply@example.com",
        ... )
        >>> result = await backend.send(EmailMessage(
        ...     to="user@example.com",
        ...     subject="Welcome!",
        ...     html="<h1>Hello!</h1>",
        ... ))

    Note:
        Get your API token from https://account.postmarkapp.com/servers
        Sender signature or domain must be verified.
    """

    provider_name: ClassVar[str] = "postmark"

    def __init__(
        self,
        api_token: str | None = None,
        message_stream: str = "outbound",
        from_addr: str | None = None,
        track_opens: bool = True,
        track_links: str | None = None,
        reply_to: str | None = None,
    ) -> None:
        """
        Initialize Postmark backend.

        Args:
            api_token: Postmark server API token (required)
            message_stream: Message stream ID (default: "outbound")
            from_addr: Default sender email address
            track_opens: Enable open tracking
            track_links: Link tracking mode ("None", "HtmlAndText", "HtmlOnly", "TextOnly")
            reply_to: Default reply-to address

        Raises:
            ConfigurationError: If API token is not provided
        """
        if not api_token:
            raise ConfigurationError(
                "Postmark API token is required. Set EMAIL_POSTMARK_API_TOKEN environment variable."
            )

        self.api_token = api_token
        self.message_stream = message_stream
        self.from_addr = from_addr
        self.track_opens = track_opens
        self.track_links = track_links
        self.default_reply_to = reply_to

    async def send(self, message: EmailMessage) -> EmailResult:
        """
        Send email asynchronously via Postmark API.

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
                "Postmark backend requires httpx. Install with: pip install httpx"
            ) from e

        payload = self._build_payload(message)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{POSTMARK_API_URL}/email",
                    json=payload,
                    headers={
                        "X-Postmark-Server-Token": self.api_token,
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    timeout=30.0,
                )

                if response.status_code == 429:
                    raise RateLimitError("Postmark rate limit exceeded")

                data = response.json()

                if response.status_code >= 400:
                    error_code = data.get("ErrorCode", 0)
                    error_message = data.get("Message", response.text)

                    # Handle specific Postmark error codes
                    if error_code == 300:  # Invalid email request
                        raise DeliveryError(
                            f"Postmark invalid request: {error_message}",
                            provider_error=error_message,
                        )
                    elif error_code == 406:  # Inactive recipient
                        raise DeliveryError(
                            f"Postmark inactive recipient: {error_message}",
                            provider_error=error_message,
                        )
                    else:
                        raise DeliveryError(
                            f"Postmark API error ({error_code}): {error_message}",
                            provider_error=error_message,
                        )

                message_id = data.get("MessageID", "")

                logger.info(f"Email sent via Postmark: {message_id} to {message.to}")

                return EmailResult(
                    message_id=message_id,
                    provider=self.provider_name,
                    status=EmailStatus.SENT,
                    raw_response=data,
                )

            except httpx.TimeoutException as e:
                raise DeliveryError(
                    "Postmark API timeout",
                    provider_error=str(e),
                ) from e
            except httpx.RequestError as e:
                raise DeliveryError(
                    f"Postmark API request failed: {e}",
                    provider_error=str(e),
                ) from e

    def send_sync(self, message: EmailMessage) -> EmailResult:
        """
        Send email synchronously via Postmark API.

        Args:
            message: Email message to send

        Returns:
            EmailResult with message ID and status
        """
        try:
            import httpx
        except ImportError as e:
            raise ImportError(
                "Postmark backend requires httpx. Install with: pip install httpx"
            ) from e

        payload = self._build_payload(message)

        with httpx.Client() as client:
            try:
                response = client.post(
                    f"{POSTMARK_API_URL}/email",
                    json=payload,
                    headers={
                        "X-Postmark-Server-Token": self.api_token,
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    timeout=30.0,
                )

                if response.status_code == 429:
                    raise RateLimitError("Postmark rate limit exceeded")

                data = response.json()

                if response.status_code >= 400:
                    error_code = data.get("ErrorCode", 0)
                    error_message = data.get("Message", response.text)
                    raise DeliveryError(
                        f"Postmark API error ({error_code}): {error_message}",
                        provider_error=error_message,
                    )

                message_id = data.get("MessageID", "")

                logger.info(f"Email sent via Postmark (sync): {message_id} to {message.to}")

                return EmailResult(
                    message_id=message_id,
                    provider=self.provider_name,
                    status=EmailStatus.SENT,
                    raw_response=data,
                )

            except httpx.TimeoutException as e:
                raise DeliveryError(
                    "Postmark API timeout",
                    provider_error=str(e),
                ) from e
            except httpx.RequestError as e:
                raise DeliveryError(
                    f"Postmark API request failed: {e}",
                    provider_error=str(e),
                ) from e

    def _build_payload(self, message: EmailMessage) -> dict[str, Any]:
        """Build Postmark API payload from EmailMessage."""
        from_addr = message.from_addr or self.from_addr
        if not from_addr:
            raise ConfigurationError(
                "No sender address. Set from_addr in message or EMAIL_FROM env var."
            )

        # Build recipients
        to_list = message.to if isinstance(message.to, list) else [message.to]

        payload: dict[str, Any] = {
            "From": from_addr,
            "To": ", ".join(to_list),
            "Subject": message.subject,
            "MessageStream": self.message_stream,
        }

        # Add body content
        if message.html:
            payload["HtmlBody"] = message.html
        if message.text:
            payload["TextBody"] = message.text

        # Add optional fields
        if message.cc:
            payload["Cc"] = ", ".join(message.cc)
        if message.bcc:
            payload["Bcc"] = ", ".join(message.bcc)

        reply_to = message.reply_to or self.default_reply_to
        if reply_to:
            payload["ReplyTo"] = reply_to

        # Tracking settings
        payload["TrackOpens"] = self.track_opens
        if self.track_links:
            payload["TrackLinks"] = self.track_links

        # Add tags (Postmark supports Tag field)
        if message.tags:
            # Postmark only supports a single tag
            payload["Tag"] = message.tags[0]

        # Add metadata
        if message.metadata:
            payload["Metadata"] = message.metadata

        # Add headers
        if message.headers:
            payload["Headers"] = [
                {"Name": key, "Value": value} for key, value in message.headers.items()
            ]

        # Handle attachments
        if message.attachments:
            import base64

            payload["Attachments"] = [
                {
                    "Name": att.filename,
                    "Content": base64.b64encode(att.content).decode("utf-8"),
                    "ContentType": att.content_type,
                    **({"ContentID": f"cid:{att.content_id}"} if att.content_id else {}),
                }
                for att in message.attachments
            ]

        return payload

    async def send_template(
        self,
        to: str | list[str],
        template_alias: str,
        template_model: dict[str, Any] | None = None,
        *,
        from_addr: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        tag: str | None = None,
    ) -> EmailResult:
        """
        Send email using a Postmark template.

        Args:
            to: Recipient email address(es)
            template_alias: Postmark template alias or ID
            template_model: Template variables
            from_addr: Sender email address
            cc: Carbon copy recipients
            bcc: Blind carbon copy recipients
            tag: Email tag for tracking

        Returns:
            EmailResult with message ID and status

        Example:
            >>> result = await backend.send_template(
            ...     to="user@example.com",
            ...     template_alias="welcome-email",
            ...     template_model={"name": "John", "product": "MyApp"},
            ... )
        """
        try:
            import httpx
        except ImportError as e:
            raise ImportError(
                "Postmark backend requires httpx. Install with: pip install httpx"
            ) from e

        sender = from_addr or self.from_addr
        if not sender:
            raise ConfigurationError("No sender address configured")

        to_list = to if isinstance(to, list) else [to]

        payload: dict[str, Any] = {
            "From": sender,
            "To": ", ".join(to_list),
            "TemplateAlias": template_alias,
            "TemplateModel": template_model or {},
            "MessageStream": self.message_stream,
            "TrackOpens": self.track_opens,
        }

        if cc:
            payload["Cc"] = ", ".join(cc)
        if bcc:
            payload["Bcc"] = ", ".join(bcc)
        if tag:
            payload["Tag"] = tag
        if self.track_links:
            payload["TrackLinks"] = self.track_links

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{POSTMARK_API_URL}/email/withTemplate",
                json=payload,
                headers={
                    "X-Postmark-Server-Token": self.api_token,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=30.0,
            )

            data = response.json()

            if response.status_code >= 400:
                error_code = data.get("ErrorCode", 0)
                error_message = data.get("Message", response.text)
                raise DeliveryError(
                    f"Postmark template error ({error_code}): {error_message}",
                    provider_error=error_message,
                )

            message_id = data.get("MessageID", "")

            return EmailResult(
                message_id=message_id,
                provider=self.provider_name,
                status=EmailStatus.SENT,
                raw_response=data,
            )
