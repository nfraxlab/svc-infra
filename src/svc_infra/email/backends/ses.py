"""
AWS SES email backend.

Sends emails via Amazon Simple Email Service.
Uses boto3 (sync) or aioboto3 (async) for AWS API calls.
"""

from __future__ import annotations

import asyncio
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


class SESBackend:
    """
    AWS SES email backend for cost-effective transactional email.

    Amazon SES is a highly scalable and cost-effective email service.
    This backend supports both sync (boto3) and async (aioboto3) operations.

    Attributes:
        region: AWS region for SES (e.g., 'us-east-1')
        access_key: AWS access key ID (optional, uses default chain)
        secret_key: AWS secret access key (optional, uses default chain)
        configuration_set: SES configuration set name (optional)
        from_addr: Default sender address

    Example:
        >>> from svc_infra.email.backends import SESBackend
        >>> from svc_infra.email import EmailMessage
        >>>
        >>> # Using default AWS credentials chain
        >>> backend = SESBackend(
        ...     region="us-east-1",
        ...     from_addr="noreply@example.com",
        ... )
        >>>
        >>> # Or with explicit credentials
        >>> backend = SESBackend(
        ...     region="us-east-1",
        ...     access_key="AKIAIOSFODNN7EXAMPLE",
        ...     secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        ...     from_addr="noreply@example.com",
        ... )
        >>>
        >>> result = await backend.send(EmailMessage(
        ...     to="user@example.com",
        ...     subject="Welcome!",
        ...     html="<h1>Hello!</h1>",
        ... ))

    Note:
        Sender email/domain must be verified in SES.
        In sandbox mode, recipients must also be verified.
    """

    provider_name: ClassVar[str] = "ses"

    def __init__(
        self,
        region: str = "us-east-1",
        access_key: str | None = None,
        secret_key: str | None = None,
        configuration_set: str | None = None,
        from_addr: str | None = None,
        endpoint_url: str | None = None,
    ) -> None:
        """
        Initialize AWS SES backend.

        Args:
            region: AWS region for SES
            access_key: AWS access key ID (uses default chain if not provided)
            secret_key: AWS secret access key (uses default chain if not provided)
            configuration_set: SES configuration set name for tracking
            from_addr: Default sender email address
            endpoint_url: Custom endpoint URL (for LocalStack, etc.)
        """
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        self.configuration_set = configuration_set
        self.from_addr = from_addr
        self.endpoint_url = endpoint_url

    def _get_boto3_kwargs(self) -> dict[str, Any]:
        """Get boto3 client configuration kwargs."""
        kwargs: dict[str, Any] = {
            "region_name": self.region,
        }

        if self.access_key and self.secret_key:
            kwargs["aws_access_key_id"] = self.access_key
            kwargs["aws_secret_access_key"] = self.secret_key

        if self.endpoint_url:
            kwargs["endpoint_url"] = self.endpoint_url

        return kwargs

    async def send(self, message: EmailMessage) -> EmailResult:
        """
        Send email asynchronously via AWS SES.

        Uses aioboto3 for non-blocking AWS API calls.

        Args:
            message: Email message to send

        Returns:
            EmailResult with message ID and status

        Raises:
            DeliveryError: If email sending fails
            RateLimitError: If rate limit is exceeded
        """
        try:
            import aioboto3
        except ImportError:
            # Fall back to sync if aioboto3 not installed
            logger.warning(
                "aioboto3 not installed, falling back to sync SES. "
                "Install with: pip install aioboto3"
            )
            return await asyncio.to_thread(self.send_sync, message)

        email_request = self._build_email_request(message)

        session = aioboto3.Session()
        async with session.client("sesv2", **self._get_boto3_kwargs()) as client:
            try:
                response = await client.send_email(**email_request)
                message_id = response.get("MessageId", "")

                logger.info(f"Email sent via SES: {message_id} to {message.to}")

                return EmailResult(
                    message_id=message_id,
                    provider=self.provider_name,
                    status=EmailStatus.SENT,
                    raw_response=response,
                )

            except client.exceptions.TooManyRequestsException as e:
                raise RateLimitError(
                    "SES rate limit exceeded",
                ) from e
            except client.exceptions.MessageRejected as e:
                raise DeliveryError(
                    f"SES rejected message: {e}",
                    provider_error=str(e),
                ) from e
            except client.exceptions.MailFromDomainNotVerifiedException as e:
                raise ConfigurationError(f"Sender domain not verified: {e}") from e
            except Exception as e:
                raise DeliveryError(
                    f"SES error: {e}",
                    provider_error=str(e),
                ) from e

    def send_sync(self, message: EmailMessage) -> EmailResult:
        """
        Send email synchronously via AWS SES.

        Uses boto3 for blocking AWS API calls.

        Args:
            message: Email message to send

        Returns:
            EmailResult with message ID and status
        """
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError as e:
            raise ImportError("SES backend requires boto3. Install with: pip install boto3") from e

        email_request = self._build_email_request(message)

        client = boto3.client("sesv2", **self._get_boto3_kwargs())

        try:
            response = client.send_email(**email_request)
            message_id = response.get("MessageId", "")

            logger.info(f"Email sent via SES (sync): {message_id} to {message.to}")

            return EmailResult(
                message_id=message_id,
                provider=self.provider_name,
                status=EmailStatus.SENT,
                raw_response=response,
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            if error_code == "TooManyRequestsException":
                raise RateLimitError("SES rate limit exceeded") from e
            elif error_code == "MessageRejected":
                raise DeliveryError(
                    f"SES rejected message: {error_message}",
                    provider_error=error_message,
                ) from e
            elif error_code == "MailFromDomainNotVerifiedException":
                raise ConfigurationError(f"Sender domain not verified: {error_message}") from e
            else:
                raise DeliveryError(
                    f"SES error: {error_message}",
                    provider_error=error_message,
                ) from e

    def _build_email_request(self, message: EmailMessage) -> dict[str, Any]:
        """Build SES SendEmail request from EmailMessage."""
        from_addr = message.from_addr or self.from_addr
        if not from_addr:
            raise ConfigurationError(
                "No sender address. Set from_addr in message or EMAIL_FROM env var."
            )

        # Build recipients
        to_list = message.to if isinstance(message.to, list) else [message.to]

        destination: dict[str, Any] = {
            "ToAddresses": to_list,
        }

        if message.cc:
            destination["CcAddresses"] = message.cc
        if message.bcc:
            destination["BccAddresses"] = message.bcc

        # Build content
        body: dict[str, Any] = {}

        if message.text:
            body["Text"] = {
                "Data": message.text,
                "Charset": "UTF-8",
            }

        if message.html:
            body["Html"] = {
                "Data": message.html,
                "Charset": "UTF-8",
            }

        content: dict[str, Any] = {
            "Simple": {
                "Subject": {
                    "Data": message.subject,
                    "Charset": "UTF-8",
                },
                "Body": body,
            }
        }

        request: dict[str, Any] = {
            "FromEmailAddress": from_addr,
            "Destination": destination,
            "Content": content,
        }

        # Add reply-to
        if message.reply_to:
            request["ReplyToAddresses"] = [message.reply_to]

        # Add configuration set
        if self.configuration_set:
            request["ConfigurationSetName"] = self.configuration_set

        # Add tags (as email tags for SES)
        if message.tags:
            request["EmailTags"] = [{"Name": tag, "Value": "true"} for tag in message.tags[:50]]

        return request

    async def send_raw(
        self,
        message: EmailMessage,
    ) -> EmailResult:
        """
        Send a raw MIME email via SES.

        Use this for emails with attachments or complex MIME structures.

        Args:
            message: Email message with attachments

        Returns:
            EmailResult with message ID and status
        """
        from email.mime.application import MIMEApplication
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        try:
            import aioboto3
        except ImportError:
            logger.warning("aioboto3 not installed, falling back to sync")
            return await asyncio.to_thread(self._send_raw_sync, message)

        from_addr = message.from_addr or self.from_addr
        if not from_addr:
            raise ConfigurationError("No sender address configured")

        # Build MIME message
        mime_msg = MIMEMultipart("mixed")
        mime_msg["From"] = from_addr
        mime_msg["Subject"] = message.subject

        to_list = message.to if isinstance(message.to, list) else [message.to]
        mime_msg["To"] = ", ".join(to_list)

        if message.cc:
            mime_msg["Cc"] = ", ".join(message.cc)

        if message.reply_to:
            mime_msg["Reply-To"] = message.reply_to

        # Add body
        body_part = MIMEMultipart("alternative")
        if message.text:
            body_part.attach(MIMEText(message.text, "plain", "utf-8"))
        if message.html:
            body_part.attach(MIMEText(message.html, "html", "utf-8"))
        mime_msg.attach(body_part)

        # Add attachments
        if message.attachments:
            for att in message.attachments:
                part = MIMEApplication(att.content)
                part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=att.filename,
                )
                if att.content_id:
                    part["Content-ID"] = f"<{att.content_id}>"
                mime_msg.attach(part)

        # Send via SES
        session = aioboto3.Session()
        async with session.client("sesv2", **self._get_boto3_kwargs()) as client:
            response = await client.send_email(
                FromEmailAddress=from_addr,
                Destination={
                    "ToAddresses": to_list,
                    **({"CcAddresses": message.cc} if message.cc else {}),
                    **({"BccAddresses": message.bcc} if message.bcc else {}),
                },
                Content={
                    "Raw": {
                        "Data": mime_msg.as_bytes(),
                    }
                },
                **(
                    {"ConfigurationSetName": self.configuration_set}
                    if self.configuration_set
                    else {}
                ),
            )

            return EmailResult(
                message_id=response.get("MessageId", ""),
                provider=self.provider_name,
                status=EmailStatus.SENT,
            )

    def _send_raw_sync(self, message: EmailMessage) -> EmailResult:
        """Sync version of send_raw."""
        return asyncio.get_event_loop().run_until_complete(self.send_raw(message))
