"""Notification infrastructure for svc-infra.

Provides a unified notification system with multi-channel delivery:
- In-app notifications (database persistence)
- Real-time delivery (WebSocket)
- Email notifications
- Push notifications (future)

Quick Start:
    from svc_infra.notifications import add_notifications, get_notifier

    # In app setup
    notifier = add_notifications(app, session_factory, Notification)

    # Send a notification
    await notifier.notify(
        user_id=user.id,
        type="order_shipped",
        title="Your order shipped!",
        body="Track it at...",
        channels=["in_app", "email"],
    )

Example Model:
    from svc_infra.notifications import NotificationMixin
    from your_app.models import Base

    class Notification(Base, NotificationMixin):
        __tablename__ = "notifications"
        # Add app-specific fields
        workspace_id: Mapped[UUID | None] = mapped_column(...)
"""

from __future__ import annotations

from .add import add_notifications, get_notifier
from .channels.base import NotificationChannel
from .channels.email import EmailChannel
from .channels.in_app import InAppChannel
from .channels.push import PushChannel
from .channels.realtime import RealtimeChannel
from .mixin import NotificationMixin
from .models import NotificationCreate, NotificationList, NotificationRead
from .service import NotificationService
from .settings import NotificationSettings

__all__ = [
    # Integration
    "add_notifications",
    "get_notifier",
    # Mixin
    "NotificationMixin",
    # Service
    "NotificationService",
    # Settings
    "NotificationSettings",
    # Models
    "NotificationCreate",
    "NotificationRead",
    "NotificationList",
    # Channels
    "NotificationChannel",
    "InAppChannel",
    "RealtimeChannel",
    "EmailChannel",
    "PushChannel",
]
