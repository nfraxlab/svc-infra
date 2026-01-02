"""Additional Coverage Tests for Phase 0.8.

Targets:
- headers.py: SecurityHeadersMiddleware
- org_invites.py: invite generation and validation
- session.py: edge cases
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock

import pytest

from svc_infra.security.headers import SECURE_DEFAULTS, SecurityHeadersMiddleware
from svc_infra.security.models import (
    AuthSession,
)
from svc_infra.security.session import (
    DEFAULT_REFRESH_TTL_MINUTES,
    issue_session_and_refresh,
    rotate_session_refresh,
)

# ============== SecurityHeadersMiddleware Tests ==============


class TestSecureDefaults:
    def test_defaults_contains_hsts(self) -> None:
        assert "Strict-Transport-Security" in SECURE_DEFAULTS
        assert "max-age=" in SECURE_DEFAULTS["Strict-Transport-Security"]

    def test_defaults_contains_csp(self) -> None:
        assert "Content-Security-Policy" in SECURE_DEFAULTS
        assert "default-src" in SECURE_DEFAULTS["Content-Security-Policy"]

    def test_defaults_contains_xfo(self) -> None:
        assert "X-Frame-Options" in SECURE_DEFAULTS
        assert SECURE_DEFAULTS["X-Frame-Options"] == "DENY"

    def test_defaults_contains_xcto(self) -> None:
        assert "X-Content-Type-Options" in SECURE_DEFAULTS
        assert SECURE_DEFAULTS["X-Content-Type-Options"] == "nosniff"


class TestSecurityHeadersMiddleware:
    @pytest.mark.asyncio
    async def test_non_http_scope_passthrough(self) -> None:
        app = AsyncMock()
        middleware = SecurityHeadersMiddleware(app)
        scope = {"type": "websocket"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)
        app.assert_awaited_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_http_scope_adds_headers(self) -> None:
        messages_sent: list[dict] = []

        async def fake_app(scope: dict, receive: Any, send: Any) -> None:
            await send({"type": "http.response.start", "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})

        async def capture_send(message: dict) -> None:
            messages_sent.append(message)

        middleware = SecurityHeadersMiddleware(fake_app)
        scope = {"type": "http"}

        await middleware(scope, AsyncMock(), capture_send)

        assert len(messages_sent) == 2
        start_msg = messages_sent[0]
        assert start_msg["type"] == "http.response.start"
        headers = {k.decode(): v.decode() for k, v in start_msg["headers"]}
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"

    @pytest.mark.asyncio
    async def test_http_scope_with_overrides(self) -> None:
        messages_sent: list[dict] = []

        async def fake_app(scope: dict, receive: Any, send: Any) -> None:
            await send({"type": "http.response.start", "headers": []})

        async def capture_send(message: dict) -> None:
            messages_sent.append(message)

        overrides = {"X-Custom-Header": "custom-value", "X-Frame-Options": "SAMEORIGIN"}
        middleware = SecurityHeadersMiddleware(fake_app, overrides=overrides)
        scope = {"type": "http"}

        await middleware(scope, AsyncMock(), capture_send)

        start_msg = messages_sent[0]
        headers = {k.decode(): v.decode() for k, v in start_msg["headers"]}
        assert headers["X-Custom-Header"] == "custom-value"
        assert headers["X-Frame-Options"] == "SAMEORIGIN"  # Override takes precedence

    @pytest.mark.asyncio
    async def test_http_scope_preserves_existing_headers(self) -> None:
        messages_sent: list[dict] = []

        async def fake_app(scope: dict, receive: Any, send: Any) -> None:
            await send(
                {
                    "type": "http.response.start",
                    "headers": [(b"Content-Type", b"text/html")],
                }
            )

        async def capture_send(message: dict) -> None:
            messages_sent.append(message)

        middleware = SecurityHeadersMiddleware(fake_app)
        scope = {"type": "http"}

        await middleware(scope, AsyncMock(), capture_send)

        start_msg = messages_sent[0]
        headers = {k.decode(): v.decode() for k, v in start_msg["headers"]}
        assert headers["Content-Type"] == "text/html"
        assert "X-Frame-Options" in headers  # Also added security headers

    @pytest.mark.asyncio
    async def test_non_start_message_passthrough(self) -> None:
        messages_sent: list[dict] = []

        async def fake_app(scope: dict, receive: Any, send: Any) -> None:
            await send({"type": "http.response.body", "body": b"test"})

        async def capture_send(message: dict) -> None:
            messages_sent.append(message)

        middleware = SecurityHeadersMiddleware(fake_app)
        scope = {"type": "http"}

        await middleware(scope, AsyncMock(), capture_send)

        assert len(messages_sent) == 1
        assert messages_sent[0]["type"] == "http.response.body"


# ============== Session Edge Cases ==============


class FakeDB:
    def __init__(self) -> None:
        self.added: list[Any] = []

    async def flush(self) -> None:
        pass

    def add(self, obj: Any) -> None:
        self.added.append(obj)


class TestIssueSessionAndRefresh:
    @pytest.mark.asyncio
    async def test_issue_with_all_optional_params(self) -> None:
        db = FakeDB()
        raw, rt = await issue_session_and_refresh(
            db,
            user_id=uuid.uuid4(),
            tenant_id="tenant-123",
            user_agent="Mozilla/5.0",
            ip_hash="abc123hash",
            ttl_minutes=120,
        )
        assert raw is not None
        assert rt is not None
        # Check session was created with correct params
        session = next(o for o in db.added if isinstance(o, AuthSession))
        assert session.tenant_id == "tenant-123"
        assert session.user_agent == "Mozilla/5.0"
        assert session.ip_hash == "abc123hash"

    @pytest.mark.asyncio
    async def test_issue_with_default_ttl(self) -> None:
        db = FakeDB()
        _raw, rt = await issue_session_and_refresh(db, user_id=uuid.uuid4())
        # Token should expire in about DEFAULT_REFRESH_TTL_MINUTES
        expected_expiry = datetime.now(UTC) + timedelta(minutes=DEFAULT_REFRESH_TTL_MINUTES)
        assert rt.expires_at is not None
        # Allow 1 minute tolerance
        assert abs((rt.expires_at - expected_expiry).total_seconds()) < 60


class TestRotateSessionRefresh:
    @pytest.mark.asyncio
    async def test_rotate_already_revoked_raises(self) -> None:
        db = FakeDB()
        _raw, rt = await issue_session_and_refresh(db, user_id=uuid.uuid4())
        # Manually mark as revoked
        rt.revoked_at = datetime.now(UTC)

        with pytest.raises(ValueError, match="already revoked"):
            await rotate_session_refresh(db, current=rt)

    @pytest.mark.asyncio
    async def test_rotate_expired_raises(self) -> None:
        db = FakeDB()
        _raw, rt = await issue_session_and_refresh(db, user_id=uuid.uuid4())
        # Set expires_at to past
        rt.expires_at = datetime.now(UTC) - timedelta(hours=1)

        with pytest.raises(ValueError, match="expired"):
            await rotate_session_refresh(db, current=rt)

    @pytest.mark.asyncio
    async def test_rotate_with_custom_ttl(self) -> None:
        db = FakeDB()
        _raw, rt = await issue_session_and_refresh(db, user_id=uuid.uuid4())

        _new_raw, new_rt = await rotate_session_refresh(db, current=rt, ttl_minutes=60)

        expected_expiry = datetime.now(UTC) + timedelta(minutes=60)
        assert new_rt.expires_at is not None
        assert abs((new_rt.expires_at - expected_expiry).total_seconds()) < 60

    @pytest.mark.asyncio
    async def test_rotate_with_none_expires_at(self) -> None:
        db = FakeDB()
        _raw, rt = await issue_session_and_refresh(db, user_id=uuid.uuid4())
        # Set expires_at to None (edge case)
        rt.expires_at = None

        # Should work - token without expiry can still be rotated
        new_raw, _new_rt = await rotate_session_refresh(db, current=rt)

        assert new_raw is not None
        assert rt.revoked_at is not None
        # expires_at should be set to revoked_at
        assert rt.expires_at == rt.revoked_at
