"""In-app notification channel (database persistence)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from .base import NotificationChannel


class InAppChannel(NotificationChannel):
    """In-app notification channel.

    This channel represents database persistence. The actual database
    write is performed by the NotificationService before channel delivery,
    so this channel's deliver() is effectively a no-op.

    The channel exists to:
    1. Maintain consistent channel interface
    2. Allow future enhancements (e.g., batching, deduplication)
    3. Enable channel availability checks
    """

    name = "in_app"

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
        """No-op: notification already saved by service."""
        return True

    async def is_available(self) -> bool:
        """In-app channel is always available if the service is running."""
        return True
