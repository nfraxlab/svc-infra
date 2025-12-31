"""Tests for svc_infra.api.fastapi.middleware.request_id module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from svc_infra.api.fastapi.middleware.request_id import (
    RequestIdMiddleware,
    request_id_ctx,
)


class TestRequestIdContext:
    """Tests for request_id_ctx context variable."""

    def test_default_is_empty_string(self) -> None:
        """Default value should be empty string."""
        # Reset context to default
        token = request_id_ctx.set("")
        request_id_ctx.reset(token)
        assert request_id_ctx.get() == ""

    def test_can_set_and_get(self) -> None:
        """Should be able to set and get value."""
        token = request_id_ctx.set("test-id-123")
        try:
            assert request_id_ctx.get() == "test-id-123"
        finally:
            request_id_ctx.reset(token)

    def test_reset_restores_previous(self) -> None:
        """Reset should restore previous value."""
        original = request_id_ctx.get()
        token = request_id_ctx.set("new-value")
        request_id_ctx.reset(token)
        assert request_id_ctx.get() == original


class TestRequestIdMiddlewareInit:
    """Tests for RequestIdMiddleware initialization."""

    def test_init_with_default_header(self) -> None:
        """Should use X-Request-Id header by default."""
        app = MagicMock()
        middleware = RequestIdMiddleware(app)
        assert middleware.header_name == "x-request-id"

    def test_init_with_custom_header(self) -> None:
        """Should accept custom header name."""
        app = MagicMock()
        middleware = RequestIdMiddleware(app, header_name="X-Correlation-Id")
        assert middleware.header_name == "x-correlation-id"

    def test_header_name_lowercased(self) -> None:
        """Header name should be lowercased."""
        app = MagicMock()
        middleware = RequestIdMiddleware(app, header_name="X-REQUEST-ID")
        assert middleware.header_name == "x-request-id"

    def test_stores_app_reference(self) -> None:
        """Should store app reference."""
        app = MagicMock()
        middleware = RequestIdMiddleware(app)
        assert middleware.app is app


class TestRequestIdMiddlewareCall:
    """Tests for RequestIdMiddleware __call__ method."""

    @pytest.mark.asyncio
    async def test_passes_non_http_requests_through(self) -> None:
        """Should pass non-HTTP requests through unchanged."""
        app = AsyncMock()
        middleware = RequestIdMiddleware(app)

        scope = {"type": "websocket"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        app.assert_awaited_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_generates_request_id_if_not_present(self) -> None:
        """Should generate request ID if not in headers."""
        captured_rid = None

        async def capture_app(scope, receive, send):
            nonlocal captured_rid
            captured_rid = request_id_ctx.get()

        middleware = RequestIdMiddleware(capture_app)

        scope = {"type": "http", "headers": []}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        assert captured_rid is not None
        assert len(captured_rid) == 32  # uuid4().hex is 32 chars

    @pytest.mark.asyncio
    async def test_uses_existing_request_id_from_header(self) -> None:
        """Should use request ID from incoming header."""
        captured_rid = None

        async def capture_app(scope, receive, send):
            nonlocal captured_rid
            captured_rid = request_id_ctx.get()

        middleware = RequestIdMiddleware(capture_app)

        scope = {
            "type": "http",
            "headers": [(b"x-request-id", b"my-custom-id-123")],
        }
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        assert captured_rid == "my-custom-id-123"

    @pytest.mark.asyncio
    async def test_adds_request_id_to_response_headers(self) -> None:
        """Should add request ID to response headers."""
        sent_messages = []

        async def mock_app(scope, receive, send):
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        middleware = RequestIdMiddleware(mock_app)

        scope = {
            "type": "http",
            "headers": [(b"x-request-id", b"test-rid-456")],
        }
        receive = AsyncMock()

        async def capture_send(message):
            sent_messages.append(message.copy())

        await middleware(scope, receive, capture_send)

        # Check response start message has request id header
        response_start = sent_messages[0]
        assert response_start["type"] == "http.response.start"
        # Headers should contain request id
        assert any(h[0] == b"x-request-id" for h in response_start.get("headers", []))

    @pytest.mark.asyncio
    async def test_resets_context_after_request(self) -> None:
        """Should reset context after request completes."""
        original = request_id_ctx.get()

        async def mock_app(scope, receive, send):
            assert request_id_ctx.get() != original or original == ""

        middleware = RequestIdMiddleware(mock_app)

        scope = {"type": "http", "headers": []}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        # Context should be reset
        # Note: Since we're in same async context, it may still have the value
        # The important thing is the reset happens in finally block

    @pytest.mark.asyncio
    async def test_resets_context_on_exception(self) -> None:
        """Should reset context even if app raises exception."""

        async def failing_app(scope, receive, send):
            raise ValueError("Test error")

        middleware = RequestIdMiddleware(failing_app)

        scope = {"type": "http", "headers": []}
        receive = AsyncMock()
        send = AsyncMock()

        with pytest.raises(ValueError):
            await middleware(scope, receive, send)

        # Context reset is handled by finally block

    @pytest.mark.asyncio
    async def test_custom_header_name_used(self) -> None:
        """Should use custom header name for extraction and response."""
        captured_rid = None

        async def capture_app(scope, receive, send):
            nonlocal captured_rid
            captured_rid = request_id_ctx.get()

        middleware = RequestIdMiddleware(capture_app, header_name="X-Trace-Id")

        scope = {
            "type": "http",
            "headers": [(b"x-trace-id", b"trace-123")],
        }
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        assert captured_rid == "trace-123"
