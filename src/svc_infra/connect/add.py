from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from sqlalchemy import delete

from svc_infra.connect.models import OAuthState
from svc_infra.connect.registry import registry as _default_registry
from svc_infra.connect.router import connect_router
from svc_infra.connect.settings import ConnectSettings
from svc_infra.connect.state import set_connect_state
from svc_infra.connect.token_manager import ConnectionTokenManager
from svc_infra.jobs.easy import easy_jobs

logger = logging.getLogger(__name__)


def add_connect(app: FastAPI, *, prefix: str = "/connect") -> None:
    """Mount the svc_infra.connect OAuth module on the given FastAPI application.

    Reads ConnectSettings from environment variables at lifespan startup so that
    validation failures are caught before the app begins serving traffic.
    Wraps any existing lifespan context using the same idiom as add_sql_db().
    Registers background jobs for token refresh and OAuthState cleanup.

    Must be called after add_sql_db() so that the DB session is available.

    Example::

        from svc_infra.api.fastapi.db.sql.add import add_sql_db
        from svc_infra.connect import add_connect

        app = FastAPI()
        add_sql_db(app)
        add_connect(app)
    """
    existing_lifespan = getattr(app.router, "lifespan_context", None)

    @asynccontextmanager
    async def connect_lifespan(_app: FastAPI):
        try:
            settings = ConnectSettings()  # type: ignore[call-arg]
        except Exception as exc:
            raise RuntimeError(
                "CONNECT_TOKEN_ENCRYPTION_KEY is missing or invalid. "
                'Generate one with: python -c "from cryptography.fernet import Fernet; '
                'print(Fernet.generate_key().decode())"'
            ) from exc

        token_manager = ConnectionTokenManager(
            encryption_key=settings.connect_token_encryption_key.get_secret_value(),
            registry=_default_registry,
        )
        set_connect_state(settings, token_manager)

        # Populate the OAuth provider registry from environment variables.
        # Must happen inside the lifespan (after env vars are set) so that
        # credentials like GITHUB_CLIENT_ID are visible.
        from svc_infra.connect.providers.generic import load_all_connect_providers

        for _provider in load_all_connect_providers():
            _default_registry.register(_provider)

        _loaded = len(_default_registry.list())
        if _loaded:
            logger.info("connect: loaded %d OAuth provider(s) from environment", _loaded)
        else:
            logger.warning("connect: no OAuth providers found in environment")

        _, scheduler = easy_jobs()

        from svc_infra.api.fastapi.db.sql import get_session_factory

        async def _refresh_task() -> None:
            session_factory = get_session_factory()
            if session_factory is None:
                logger.warning("connect: DB not initialised, skipping token refresh")
                return
            try:
                async with session_factory() as db:
                    count = await token_manager.refresh_expiring_tokens(db)
                    await db.commit()
                    if count:
                        logger.info("connect: refreshed %d expiring tokens", count)
            except Exception as exc:
                logger.error("connect: token refresh background task failed: %s", exc)

        async def _cleanup_expired_states() -> None:
            session_factory = get_session_factory()
            if session_factory is None:
                logger.warning("connect: DB not initialised, skipping state cleanup")
                return
            try:
                async with session_factory() as db:
                    result = await db.execute(
                        delete(OAuthState).where(OAuthState.expires_at <= datetime.now(UTC))
                    )
                    await db.commit()
                    deleted = result.rowcount  # type: ignore[attr-defined]
                    if deleted:
                        logger.debug("connect: purged %d expired OAuthState rows", deleted)
            except Exception as exc:
                logger.error("connect: OAuthState cleanup task failed: %s", exc)

        async def _cleanup_expired_tokens() -> None:
            session_factory = get_session_factory()
            if session_factory is None:
                logger.warning("connect: DB not initialised, skipping token cleanup")
                return
            try:
                async with session_factory() as db:
                    count = await token_manager.cleanup_expired_tokens(db)
                    await db.commit()
                    if count:
                        logger.debug("connect: purged %d expired token rows", count)
            except Exception as exc:
                logger.error("connect: token cleanup task failed: %s", exc)

        scheduler.add_task("connect:refresh_tokens", 300, _refresh_task)
        scheduler.add_task("connect:cleanup_states", 600, _cleanup_expired_states)
        scheduler.add_task("connect:cleanup_tokens", 3600, _cleanup_expired_tokens)
        scheduler_task = asyncio.create_task(scheduler.run())

        if existing_lifespan is not None:
            async with existing_lifespan(_app):
                try:
                    yield
                finally:
                    scheduler_task.cancel()
        else:
            try:
                yield
            finally:
                scheduler_task.cancel()

    app.router.lifespan_context = connect_lifespan
    app.include_router(connect_router, prefix=prefix)
