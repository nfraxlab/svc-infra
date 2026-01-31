"""Pydantic models for notification data transfer."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationCreate(BaseModel):
    """Schema for creating a notification."""

    user_id: UUID
    """Target user for this notification."""

    type: str = Field(..., max_length=100)
    """Notification type (e.g., 'workspace_invite', 'budget_warning')."""

    title: str = Field(..., max_length=255)
    """Short title displayed prominently."""

    body: str
    """Longer description text."""

    data: dict[str, Any] = Field(default_factory=dict)
    """Arbitrary JSON data for the notification."""

    action_url: str | None = Field(default=None, max_length=500)
    """URL to navigate when notification is clicked."""

    channels: list[str] = Field(default_factory=lambda: ["in_app"])
    """Delivery channels: 'in_app', 'realtime', 'email', 'push'."""


class NotificationRead(BaseModel):
    """Schema for reading a notification."""

    id: UUID
    user_id: UUID
    type: str
    title: str
    body: str
    data: dict[str, Any]
    action_url: str | None
    read_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationList(BaseModel):
    """Schema for paginated notification list."""

    items: list[NotificationRead]
    """List of notifications."""

    total: int
    """Total count of matching notifications."""

    unread_count: int
    """Count of unread notifications for user."""
