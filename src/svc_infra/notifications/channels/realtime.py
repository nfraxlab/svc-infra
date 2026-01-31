"""Real-time WebSocket notification channel."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID

from .base import NotificationChannel

if TYPE_CHECKING:
    from svc_infra.websocket import ConnectionManager

logger = logging.getLogger(__name__)


class RealtimeChannel(NotificationChannel):
    """Real-time WebSocket notification channel.

    Uses svc_infra.websocket.ConnectionManager to push notifications
    to connected clients immediately.

    If the user is not connected, the notification is silently skipped
    (they'll see it in the notification center when they reconnect).
    """

    name = "realtime"

    def __init__(self, manager: ConnectionManager | None = None) -> None:
        """Initialize realtime channel.

        Args:
            manager: WebSocket connection manager instance.
                     If None, channel will be unavailable.
        """
        self._manager = manager

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
        """Push notification to connected WebSocket clients."""
        if not self._manager:
            return False

        user_key = str(user_id)

        # Check if user has active connections
        if not self._manager.is_user_connected(user_key):
            logger.debug(f"User {user_key} not connected, skipping realtime delivery")
            return False

        payload = {
            "type": "notification",
            "notification": {
                "id": str(notification_id),
                "type": type,
                "title": title,
                "body": body,
                "data": data,
                "action_url": action_url,
            },
        }

        try:
            sent_count = await self._manager.send_to_user(user_key, payload)
            if sent_count > 0:
                logger.debug(f"Sent notification to {sent_count} connections for user {user_key}")
                return True
            return False
        except Exception as e:
            logger.warning(f"Realtime delivery failed for user {user_key}: {e}")
            return False

    async def is_available(self) -> bool:
        """Check if WebSocket manager is configured."""
        return self._manager is not None
