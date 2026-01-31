"""Base class for notification channels."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class NotificationChannel(ABC):
    """Abstract base class for notification delivery channels.

    Each channel is responsible for delivering notifications through
    a specific mechanism (database, WebSocket, email, push, etc.).

    Channels should:
    - Handle their own errors gracefully (log, don't raise)
    - Return True/False to indicate delivery success
    - Be idempotent when possible
    """

    name: str
    """Unique identifier for this channel."""

    @abstractmethod
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
        """Deliver a notification to the user.

        Args:
            user_id: Target user UUID.
            notification_id: Notification UUID for reference.
            type: Notification type string.
            title: Short title text.
            body: Longer description text.
            data: Arbitrary JSON data.
            action_url: Optional URL for click action.

        Returns:
            True if delivery succeeded, False otherwise.
            Should not raise exceptions - log errors internally.
        """
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if this channel is configured and available.

        Returns:
            True if channel can deliver notifications.
        """
        ...
