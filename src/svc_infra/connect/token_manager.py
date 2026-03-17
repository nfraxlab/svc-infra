from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from svc_infra.connect.models import ConnectionToken
from svc_infra.connect.pkce import OAuthRefreshError, coerce_expires_at, exchange_refresh
from svc_infra.connect.registry import ConnectRegistry
from svc_infra.db.sql.repository import SqlRepository

logger = logging.getLogger(__name__)

_REFRESH_AHEAD_SECONDS = 300  # 5 minutes


class ConnectionTokenManager:
    """Store, retrieve, and background-refresh OAuth tokens for connections.

    Wraps SqlRepository(model=ConnectionToken) for all DB access.
    access_token, refresh_token, and raw_token are Fernet-encrypted at rest.
    """

    def __init__(self, encryption_key: str, registry: ConnectRegistry | None = None) -> None:
        key_bytes = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
        self._fernet = Fernet(key_bytes)
        self._repo = SqlRepository(model=ConnectionToken)
        self._registry = registry

    # ------------------------------------------------------------------
    # Encryption helpers
    # ------------------------------------------------------------------

    def _encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode()).decode()

    def _decrypt(self, value: str) -> str:
        return self._fernet.decrypt(value.encode()).decode()

    def _encrypt_json(self, value: dict[str, Any]) -> str:
        return self._encrypt(json.dumps(value))

    def _decrypt_json(self, value: str) -> dict[str, Any]:
        return json.loads(self._decrypt(value))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def store(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        connection_id: UUID,
        provider: str,
        token_response: dict[str, Any],
    ) -> ConnectionToken:
        """Upsert a ConnectionToken row for the given (connection_id, user_id, provider).

        access_token, refresh_token, and raw_token are Fernet-encrypted before writing.
        expires_at is normalised via coerce_expires_at().
        """
        access_token_raw = token_response.get("access_token", "")
        refresh_token_raw = token_response.get("refresh_token")
        token_type = token_response.get("token_type", "Bearer")
        scopes_raw = token_response.get("scope", "")
        scopes: list[str] = (
            [s.strip() for s in scopes_raw.split() if s.strip()]
            if isinstance(scopes_raw, str)
            else (scopes_raw or [])
        )
        expires_at = coerce_expires_at(token_response)

        data: dict[str, Any] = {
            "connection_id": connection_id,
            "user_id": user_id,
            "provider": provider,
            "access_token": self._encrypt(access_token_raw),
            "refresh_token": self._encrypt(refresh_token_raw) if refresh_token_raw else None,
            "token_type": token_type,
            "expires_at": expires_at,
            "scopes": scopes,
            "raw_token": self._encrypt_json(token_response),
        }

        existing = await self.get(
            db, connection_id=connection_id, user_id=user_id, provider=provider
        )
        if existing is not None:
            update_data = {
                k: v for k, v in data.items() if k not in {"connection_id", "user_id", "provider"}
            }
            updated = await self._repo.update(db, existing.id, update_data)
            return updated  # type: ignore[return-value]

        return await self._repo.create(db, data)  # type: ignore[return-value]

    async def get(
        self,
        db: AsyncSession,
        *,
        connection_id: UUID,
        user_id: UUID,
        provider: str,
    ) -> ConnectionToken | None:
        """Retrieve a ConnectionToken by (connection_id, user_id, provider)."""
        stmt = select(ConnectionToken).where(
            and_(
                ConnectionToken.connection_id == connection_id,
                ConnectionToken.user_id == user_id,
                ConnectionToken.provider == provider,
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_valid_token(
        self,
        db: AsyncSession,
        *,
        connection_id: UUID,
        user_id: UUID,
        provider: str,
    ) -> str | None:
        """Return a decrypted, valid access token; auto-refresh if within 5 minutes of expiry.

        Returns None if no token is stored or refresh fails. Never raises.
        """
        try:
            row = await self.get(
                db, connection_id=connection_id, user_id=user_id, provider=provider
            )
            if row is None:
                return None

            now = datetime.now(UTC)
            expires_at = row.expires_at
            if expires_at is not None and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
            needs_refresh = expires_at is not None and expires_at <= now + timedelta(
                seconds=_REFRESH_AHEAD_SECONDS
            )

            if needs_refresh and row.refresh_token:
                row = await self._refresh_token(db, row)

            if row is None:
                return None

            return self._decrypt(row.access_token)
        except (InvalidToken, Exception) as exc:
            logger.warning(
                "get_valid_token failed for connection_id=%s provider=%s: %s",
                connection_id,
                provider,
                exc,
            )
            return None

    async def revoke(
        self,
        db: AsyncSession,
        *,
        connection_id: UUID,
        user_id: UUID,
        provider: str,
    ) -> None:
        """Revoke the token at the provider (if revoke_url configured) and delete the DB row."""
        row = await self.get(db, connection_id=connection_id, user_id=user_id, provider=provider)
        if row is None:
            return

        if self._registry is not None:
            prov = self._registry.get(provider)
            if prov and prov.revoke_url:
                try:
                    access_token = self._decrypt(row.access_token)
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        await client.post(
                            prov.revoke_url,
                            data={"token": access_token, "client_id": prov.client_id},
                        )
                except Exception as exc:
                    logger.warning("Token revocation request failed: %s", exc)

        await self._repo.delete(db, row.id)

    async def delete_all_for_connection(
        self,
        db: AsyncSession,
        connection_id: UUID,
    ) -> None:
        """Delete all ConnectionToken rows for a connection (used when connection is deleted)."""
        from sqlalchemy import delete

        stmt = delete(ConnectionToken).where(ConnectionToken.connection_id == connection_id)
        await db.execute(stmt)
        await db.flush()

    async def refresh_expiring_tokens(self, db: AsyncSession) -> int:
        """Refresh all tokens expiring within the next 10 minutes.

        Registered as a periodic InMemoryScheduler job via easy_jobs().
        Returns the count of successfully refreshed tokens.
        """
        cutoff = datetime.now(UTC) + timedelta(minutes=10)
        stmt = select(ConnectionToken).where(
            and_(
                ConnectionToken.expires_at.is_not(None),
                ConnectionToken.expires_at <= cutoff,
                ConnectionToken.refresh_token.is_not(None),
            )
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()

        refreshed = 0
        for row in rows:
            try:
                await self._refresh_token(db, row)
                refreshed += 1
            except Exception as exc:
                logger.warning(
                    "Background refresh failed for token id=%s provider=%s: %s",
                    row.id,
                    row.provider,
                    exc,
                )
        return refreshed

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _refresh_token(
        self,
        db: AsyncSession,
        row: ConnectionToken,
    ) -> ConnectionToken | None:
        if self._registry is None:
            logger.warning("Cannot refresh token: no registry attached to ConnectionTokenManager")
            return row

        prov = self._registry.get(row.provider)
        if prov is None:
            logger.warning("Cannot refresh token: provider %s not in registry", row.provider)
            return row

        if not row.refresh_token:
            return row

        try:
            refresh_token_plain = self._decrypt(row.refresh_token)
            new_token = await exchange_refresh(prov, refresh_token_plain)
            return await self.store(
                db,
                user_id=row.user_id,
                connection_id=row.connection_id,
                provider=row.provider,
                token_response=new_token,
            )
        except OAuthRefreshError as exc:
            logger.warning(
                "Token refresh failed for id=%s provider=%s: %s",
                row.id,
                row.provider,
                exc,
            )
            return None
