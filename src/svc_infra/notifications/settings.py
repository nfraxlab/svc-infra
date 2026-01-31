"""Notification settings configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class NotificationSettings(BaseSettings):
    """Settings for notification infrastructure.

    All settings can be overridden via environment variables
    with the NOTIFICATION_ prefix.

    Example:
        NOTIFICATION_DEFAULT_CHANNELS='["in_app", "email"]'
        NOTIFICATION_REALTIME_ENABLED=true
        NOTIFICATION_RETENTION_DAYS=90
    """

    notification_default_channels: list[str] = ["in_app"]
    """Default channels for notifications when not specified."""

    notification_realtime_enabled: bool = True
    """Enable WebSocket real-time delivery."""

    notification_email_enabled: bool = True
    """Enable email delivery channel."""

    notification_push_enabled: bool = False
    """Enable push notification channel (FCM/APNs)."""

    notification_max_per_page: int = 50
    """Maximum notifications per page in list queries."""

    notification_retention_days: int = 90
    """Days to keep notifications before cleanup."""

    model_config = {"env_prefix": "NOTIFICATION_", "extra": "ignore"}
