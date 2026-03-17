from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.expression import text

from svc_infra.db.sql.base import ModelBase
from svc_infra.db.sql.types import GUID


class ConnectionToken(ModelBase):
    """Encrypted OAuth token for a third-party provider connection.

    Keyed to (connection_id, user_id, provider). Distinct from ProviderAccount which
    tracks login-provider identities. access_token, refresh_token, and raw_token are
    Fernet-encrypted at rest by ConnectionTokenManager.
    """

    __tablename__ = "connection_tokens"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    connection_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        nullable=False,
        index=True,
        comment="Logical FK to consuming app connection table; not DB-enforced",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    access_token: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Fernet-encrypted; never logged",
    )
    refresh_token: Mapped[str | None] = mapped_column(
        Text,
        comment="Fernet-encrypted; None for non-refreshable tokens",
    )
    token_type: Mapped[str] = mapped_column(String(32), nullable=False, default="Bearer")
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        comment="None means non-expiring token",
    )
    scopes: Mapped[list | None] = mapped_column(JSON, comment="List of scope strings")
    raw_token: Mapped[dict | None] = mapped_column(
        JSON,
        comment="Fernet-encrypted full provider token response",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("connection_id", "user_id", "provider", name="uq_connection_token"),
        Index("ix_connection_tokens_user_provider", "user_id", "provider"),
    )


class OAuthState(ModelBase):
    """Short-lived PKCE state store for OAuth flows.

    Replaces SessionMiddleware-based state from oauth_router.py, enabling stateless
    API servers. Rows are purged by a background InMemoryScheduler job after TTL.
    """

    __tablename__ = "oauth_states"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    state: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        unique=True,
        comment="32-byte URL-safe random value; SHA-256 verified on callback",
    )
    pkce_verifier: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Stored server-side; sent to token endpoint on callback",
    )
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    connection_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        comment="Pre-linked before redirect; may be None for new connections",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    redirect_uri: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Validated against allow-list before storage",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="10-minute TTL; background job purges expired rows",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
