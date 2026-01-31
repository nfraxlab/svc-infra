"""SQLAlchemy mixin for notification models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from svc_infra.db.sql.types import GUID


class NotificationMixin:
    """SQLAlchemy mixin providing notification fields.

    Applications extend this mixin to create their notification table,
    adding any app-specific fields they need.

    Example:
        from svc_infra.notifications import NotificationMixin
        from your_app.models import Base

        class Notification(Base, NotificationMixin):
            __tablename__ = "notifications"

            # App-specific fields
            workspace_id: Mapped[UUID | None] = mapped_column(
                GUID(),
                ForeignKey("workspaces.id", ondelete="CASCADE"),
                nullable=True,
                index=True,
            )

    Recommended indexes:
        - (user_id, read_at IS NULL) partial index for unread queries
        - (user_id, created_at DESC) for listing
        - (type) for filtering by notification type
    """

    @declared_attr
    def id(cls) -> Mapped[UUID]:
        """Primary key."""
        return mapped_column(GUID(), primary_key=True)

    @declared_attr
    def user_id(cls) -> Mapped[UUID]:
        """Target user for this notification."""
        return mapped_column(GUID(), nullable=False, index=True)

    @declared_attr
    def type(cls) -> Mapped[str]:
        """Notification type (e.g., 'workspace_invite', 'budget_warning')."""
        return mapped_column(String(100), nullable=False, index=True)

    @declared_attr
    def title(cls) -> Mapped[str]:
        """Short title displayed prominently."""
        return mapped_column(String(255), nullable=False)

    @declared_attr
    def body(cls) -> Mapped[str]:
        """Longer description text."""
        return mapped_column(Text, nullable=False)

    @declared_attr
    def data(cls) -> Mapped[dict]:
        """Arbitrary JSON data for the notification."""
        return mapped_column(JSONB, nullable=False, server_default="{}")

    @declared_attr
    def action_url(cls) -> Mapped[str | None]:
        """URL to navigate when notification is clicked."""
        return mapped_column(String(500), nullable=True)

    @declared_attr
    def read_at(cls) -> Mapped[datetime | None]:
        """Timestamp when notification was read (null if unread)."""
        return mapped_column(DateTime(timezone=True), nullable=True)

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        """Timestamp when notification was created."""
        return mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
