"""Email notification channel."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any
from uuid import UUID

from .base import NotificationChannel

logger = logging.getLogger(__name__)


class EmailChannel(NotificationChannel):
    """Email notification channel.

    Uses svc_infra.email infrastructure for delivery. Requires either:
    1. Email address in data["_email"]
    2. A get_user_email callback function

    Email is built from the notification title/body with optional
    action button for action_url.
    """

    name = "email"

    def __init__(
        self,
        get_user_email: Callable[[UUID], str | None] | None = None,
    ) -> None:
        """Initialize email channel.

        Args:
            get_user_email: Optional async callback to lookup user email by ID.
        """
        self._get_user_email = get_user_email

    async def deliver(
        self,
        user_id: UUID,
        notification_id: UUID,
        type: str,
        title: str,
        body: str,
        data: dict[str, Any],
        action_url: str | None = None,
    ) -> bool:
        """Send notification via email."""
        # Get email address
        email_address = data.get("_email")
        if not email_address and self._get_user_email:
            email_address = self._get_user_email(user_id)

        if not email_address:
            logger.debug(f"No email address for user {user_id}, skipping email delivery")
            return False

        html_body = self._build_html(title, body, action_url)

        try:
            from svc_infra.email import get_sender

            sender = get_sender()
            await sender.send(
                to=email_address,
                subject=title,
                html=html_body,
            )
            logger.debug(f"Sent notification email to {email_address}")
            return True
        except Exception as e:
            logger.warning(f"Email delivery failed for {email_address}: {e}")
            return False

    def _build_html(self, title: str, body: str, action_url: str | None) -> str:
        """Build HTML email from notification content."""
        action_button = ""
        if action_url:
            action_button = f"""
                <p style="text-align: center; margin: 32px 0;">
                    <a href="{action_url}"
                       style="background: #0070f3; color: white; padding: 12px 32px;
                              text-decoration: none; border-radius: 6px;
                              display: inline-block; font-weight: 500;">
                        View Details
                    </a>
                </p>
            """

        return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="margin: 0; padding: 0; background-color: #f5f5f5;">
                <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                    <div style="background: white; border-radius: 8px; padding: 32px;
                                box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <h2 style="margin: 0 0 16px 0; font-size: 20px; color: #111;">
                            {title}
                        </h2>
                        <p style="margin: 0; font-size: 16px; color: #444; line-height: 1.5;">
                            {body}
                        </p>
                        {action_button}
                    </div>
                </div>
            </body>
            </html>
        """

    async def is_available(self) -> bool:
        """Email channel is available if svc_infra.email is configured."""
        try:
            from svc_infra.email import get_sender

            get_sender()
            return True
        except Exception:
            return False
