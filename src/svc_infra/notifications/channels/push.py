"""Push notification channel (FCM/APNs)."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from .base import NotificationChannel

logger = logging.getLogger(__name__)


class PushChannel(NotificationChannel):
    """Push notification channel for mobile devices.

    Delivers notifications via:
    - Firebase Cloud Messaging (FCM) for Android
    - Apple Push Notification service (APNs) for iOS

    Note: This is a placeholder implementation. Full implementation
    will be added when mobile app support is needed.
    """

    name = "push"

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
        """Push notification to mobile devices.

        TODO: Implement FCM/APNs integration when mobile support is needed.
        """
        logger.debug(f"Push channel not yet implemented, skipping for user {user_id}")
        return False

    async def is_available(self) -> bool:
        """Push channel is not yet implemented."""
        return False
