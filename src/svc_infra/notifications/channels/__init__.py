"""Notification delivery channels.

Each channel represents a different delivery mechanism:
- InAppChannel: Database persistence for notification center
- RealtimeChannel: WebSocket push to connected clients
- EmailChannel: Email delivery via svc_infra.email
- PushChannel: Mobile push via FCM/APNs (future)
"""

from __future__ import annotations

from .base import NotificationChannel
from .email import EmailChannel
from .in_app import InAppChannel
from .push import PushChannel
from .realtime import RealtimeChannel

__all__ = [
    "NotificationChannel",
    "InAppChannel",
    "RealtimeChannel",
    "EmailChannel",
    "PushChannel",
]
