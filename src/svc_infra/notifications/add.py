"""FastAPI integration for notifications."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING
from uuid import UUID

from .channels.email import EmailChannel
from .channels.in_app import InAppChannel
from .channels.realtime import RealtimeChannel
from .service import NotificationService

if TYPE_CHECKING:
    from fastapi import FastAPI, Request

    from svc_infra.websocket import ConnectionManager

_NOTIFIER_ATTR = "_svc_infra_notifier"


def add_notifications(
    app: FastAPI,
    session_factory: Callable,
    notification_model: type,
    ws_manager: ConnectionManager | None = None,
    get_user_email: Callable[[UUID], str | None] | None = None,
) -> NotificationService:
    """Add notification infrastructure to a FastAPI application.

    This sets up the notification service with default channels:
    - InAppChannel: Always enabled (database persistence)
    - RealtimeChannel: Enabled if ws_manager is provided
    - EmailChannel: Enabled if svc_infra.email is configured

    Args:
        app: FastAPI application instance.
        session_factory: Async session factory (context manager).
        notification_model: SQLAlchemy model extending NotificationMixin.
        ws_manager: Optional WebSocket connection manager for realtime.
        get_user_email: Optional callback to lookup user email by ID.

    Returns:
        Configured NotificationService instance.

    Example:
        from svc_infra.notifications import add_notifications

        notifier = add_notifications(
            app,
            session_factory=get_async_session,
            notification_model=Notification,
            ws_manager=ws_manager,
        )
    """
    # Create channels
    channels = [InAppChannel()]

    if ws_manager:
        channels.append(RealtimeChannel(ws_manager))

    channels.append(EmailChannel(get_user_email))

    # Create service
    notifier = NotificationService(
        session_factory=session_factory,
        notification_model=notification_model,
        channels=channels,
    )

    # Store on app state
    setattr(app.state, _NOTIFIER_ATTR, notifier)
    return notifier


def get_notifier(app_or_request: FastAPI | Request) -> NotificationService:
    """Get the notification service from app or request.

    Args:
        app_or_request: FastAPI app or Request object.

    Returns:
        NotificationService instance.

    Raises:
        RuntimeError: If notifications not configured.

    Example:
        @router.post("/some-action")
        async def some_action(request: Request):
            notifier = get_notifier(request)
            await notifier.notify(...)
    """
    # Handle both FastAPI app and Request objects
    if hasattr(app_or_request, "app"):
        # It's a Request
        app = app_or_request.app
    else:
        # It's a FastAPI app
        app = app_or_request

    notifier = getattr(app.state, _NOTIFIER_ATTR, None)
    if not notifier:
        raise RuntimeError(
            "Notifications not configured. Call add_notifications() during app startup."
        )
    return notifier
