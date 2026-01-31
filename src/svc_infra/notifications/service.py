"""Notification service for orchestrating delivery."""

from __future__ import annotations

import inspect
import logging
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import CursorResult, and_, func, select, update
from sqlalchemy import delete as delete_stmt
from sqlalchemy.ext.asyncio import AsyncSession

from .channels.base import NotificationChannel

logger = logging.getLogger(__name__)

# Type alias for session factory - can be either:
# 1. An async generator function (like FastAPI's get_session)
# 2. A function that returns an async context manager
SessionFactory = Callable[
    [], AbstractAsyncContextManager[AsyncSession] | AsyncIterator[AsyncSession]
]


def _wrap_async_generator_factory(
    factory: Callable[[], AsyncIterator[AsyncSession]],
) -> Callable[[], AbstractAsyncContextManager[AsyncSession]]:
    """Wrap an async generator factory to work with async with.

    FastAPI's get_session returns an async generator, but we need
    an async context manager for `async with factory() as session:`.

    This wrapper converts async generators into proper context managers.
    """

    @asynccontextmanager
    async def wrapped() -> AsyncIterator[AsyncSession]:
        gen = factory()
        try:
            session = await gen.__anext__()
            yield session
        finally:
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass

    return wrapped


class NotificationService:
    """Main notification service.

    Orchestrates notification creation, storage, and delivery
    across multiple channels.

    Example:
        service = NotificationService(
            session_factory=get_async_session,
            notification_model=Notification,
            channels=[InAppChannel(), RealtimeChannel(ws_manager)],
        )

        await service.notify(
            user_id=user.id,
            type="order_shipped",
            title="Your order shipped!",
            body="Track it at...",
            channels=["in_app", "realtime"],
        )
    """

    def __init__(
        self,
        session_factory: SessionFactory,
        notification_model: type[Any],
        channels: list[NotificationChannel] | None = None,
    ) -> None:
        """Initialize notification service.

        Args:
            session_factory: Async generator or context manager returning AsyncSession.
            notification_model: SQLAlchemy model extending NotificationMixin.
            channels: List of delivery channels.
        """
        # Wrap async generator factories (like FastAPI's get_session) to work
        # with `async with factory() as session:` pattern
        if inspect.isasyncgenfunction(session_factory):
            self.session_factory: Callable[[], AbstractAsyncContextManager[AsyncSession]] = (
                _wrap_async_generator_factory(session_factory)
            )
        else:
            self.session_factory = session_factory  # type: ignore[assignment]
        self.model: Any = notification_model
        self._channels: dict[str, NotificationChannel] = {}

        for channel in channels or []:
            self._channels[channel.name] = channel

    def register_channel(self, channel: NotificationChannel) -> None:
        """Register a delivery channel.

        Args:
            channel: Channel instance to register.
        """
        self._channels[channel.name] = channel
        logger.info(f"Registered notification channel: {channel.name}")

    async def notify(
        self,
        user_id: UUID,
        type: str,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
        action_url: str | None = None,
        channels: list[str] | None = None,
    ) -> UUID:
        """Create and deliver a notification.

        Args:
            user_id: Target user UUID.
            type: Notification type (e.g., 'workspace_invite').
            title: Short title text.
            body: Longer description text.
            data: Arbitrary JSON data (optional).
            action_url: URL for click action (optional).
            channels: Delivery channels (default: ['in_app']).
                      If 'in_app' is NOT in channels, no database record is created.

        Returns:
            UUID of the created notification (always generated, even for ephemeral).
        """
        channels = channels or ["in_app"]
        data = data or {}

        # Only create database record if in_app channel is requested
        # Other channels (email, push, realtime) are ephemeral and don't need storage
        notification_id: UUID = uuid4()
        if "in_app" in channels:
            async with self.session_factory() as session:
                notification = self.model(
                    id=notification_id,
                    user_id=user_id,
                    type=type,
                    title=title,
                    body=body,
                    data=data,
                    action_url=action_url,
                )
                session.add(notification)
                await session.commit()
            logger.debug(f"Created notification {notification_id} for user {user_id}")
        else:
            logger.debug(
                f"Ephemeral notification {notification_id} for user {user_id} (no db record)"
            )

        # Deliver to channels (fire-and-forget, don't fail if delivery fails)
        for channel_name in channels:
            channel = self._channels.get(channel_name)
            if not channel:
                logger.warning(f"Channel '{channel_name}' not registered")
                continue

            try:
                if await channel.is_available():
                    success = await channel.deliver(
                        user_id=user_id,
                        notification_id=notification_id,
                        type=type,
                        title=title,
                        body=body,
                        data=data,
                        action_url=action_url,
                    )
                    if success:
                        logger.debug(f"Delivered to channel '{channel_name}'")
                else:
                    logger.debug(f"Channel '{channel_name}' not available")
            except Exception as e:
                logger.warning(f"Channel '{channel_name}' delivery failed: {e}")

        return notification_id

    async def notify_many(
        self,
        user_ids: list[UUID],
        type: str,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
        action_url: str | None = None,
        channels: list[str] | None = None,
    ) -> list[UUID]:
        """Send notification to multiple users.

        Args:
            user_ids: List of target user UUIDs.
            type: Notification type.
            title: Short title text.
            body: Longer description text.
            data: Arbitrary JSON data (optional).
            action_url: URL for click action (optional).
            channels: Delivery channels (default: ['in_app']).

        Returns:
            List of created notification UUIDs.
        """
        notification_ids = []
        for user_id in user_ids:
            notification_id = await self.notify(
                user_id=user_id,
                type=type,
                title=title,
                body=body,
                data=data,
                action_url=action_url,
                channels=channels,
            )
            notification_ids.append(notification_id)
        return notification_ids

    async def list_for_user(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list, int, int]:
        """List notifications for a user.

        Args:
            user_id: Target user UUID.
            unread_only: If True, only return unread notifications.
            limit: Maximum notifications to return.
            offset: Pagination offset.

        Returns:
            Tuple of (notifications, total_count, unread_count).
        """
        async with self.session_factory() as session:
            # Base query
            base = select(self.model).where(self.model.user_id == user_id)

            # Unread filter
            if unread_only:
                base = base.where(self.model.read_at.is_(None))

            # Get items
            query = base.order_by(self.model.created_at.desc()).limit(limit).offset(offset)
            result = await session.execute(query)
            items = list(result.scalars().all())

            # Get total count
            count_query = select(func.count()).select_from(
                select(self.model).where(self.model.user_id == user_id).subquery()
            )
            total = (await session.execute(count_query)).scalar() or 0

            # Get unread count
            unread_query = select(func.count()).select_from(
                select(self.model)
                .where(
                    and_(
                        self.model.user_id == user_id,
                        self.model.read_at.is_(None),
                    )
                )
                .subquery()
            )
            unread = (await session.execute(unread_query)).scalar() or 0

            return items, total, unread

    async def mark_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """Mark a notification as read.

        Args:
            notification_id: Notification UUID.
            user_id: User UUID (for authorization).

        Returns:
            True if notification was updated, False if not found.
        """
        async with self.session_factory() as session:
            query = (
                update(self.model)
                .where(
                    and_(
                        self.model.id == notification_id,
                        self.model.user_id == user_id,
                    )
                )
                .values(read_at=datetime.now(UTC))
            )
            result = cast(CursorResult[Any], await session.execute(query))
            await session.commit()
            return result.rowcount > 0

    async def mark_all_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user.

        Args:
            user_id: User UUID.

        Returns:
            Number of notifications marked as read.
        """
        async with self.session_factory() as session:
            query = (
                update(self.model)
                .where(
                    and_(
                        self.model.user_id == user_id,
                        self.model.read_at.is_(None),
                    )
                )
                .values(read_at=datetime.now(UTC))
            )
            result = cast(CursorResult[Any], await session.execute(query))
            await session.commit()
            return result.rowcount

    async def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications.

        Args:
            user_id: User UUID.

        Returns:
            Number of unread notifications.
        """
        async with self.session_factory() as session:
            query = select(func.count()).where(
                and_(
                    self.model.user_id == user_id,
                    self.model.read_at.is_(None),
                )
            )
            result = await session.execute(query)
            return result.scalar() or 0

    async def get(self, notification_id: UUID, user_id: UUID | None = None) -> Any | None:
        """Get a single notification by ID.

        Args:
            notification_id: Notification UUID.
            user_id: Optional user UUID for authorization check.

        Returns:
            Notification model instance or None if not found.
        """
        async with self.session_factory() as session:
            conditions = [self.model.id == notification_id]
            if user_id is not None:
                conditions.append(self.model.user_id == user_id)

            query = select(self.model).where(and_(*conditions))
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def delete(self, notification_id: UUID, user_id: UUID) -> bool:
        """Delete a notification.

        Args:
            notification_id: Notification UUID.
            user_id: User UUID (for authorization).

        Returns:
            True if notification was deleted, False if not found.
        """
        async with self.session_factory() as session:
            query = select(self.model).where(
                and_(
                    self.model.id == notification_id,
                    self.model.user_id == user_id,
                )
            )
            result = await session.execute(query)
            notification = result.scalar_one_or_none()

            if not notification:
                return False

            await session.delete(notification)
            await session.commit()
            return True

    async def delete_all(self, user_id: UUID) -> int:
        """Delete all notifications for a user.

        Args:
            user_id: User UUID.

        Returns:
            Number of notifications deleted.
        """
        async with self.session_factory() as session:
            query = delete_stmt(self.model).where(self.model.user_id == user_id)
            result = cast(CursorResult[Any], await session.execute(query))
            await session.commit()
            return result.rowcount
