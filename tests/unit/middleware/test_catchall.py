"""Tests for svc_infra.api.fastapi.middleware.errors.catchall module."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from svc_infra.api.fastapi.middleware.errors.catchall import (
    PROBLEM_MT,
    CatchAllExceptionMiddleware,
)


class TestProblemMediaType:
    """Tests for PROBLEM_MT constant."""

    def test_is_application_problem_json(self) -> None:
        """Should be application/problem+json."""
        assert PROBLEM_MT == "application/problem+json"


class TestCatchAllExceptionMiddlewareInit:
    """Tests for CatchAllExceptionMiddleware initialization."""

    def test_stores_app_reference(self) -> None:
        """Should store app reference."""
        app = AsyncMock()
        middleware = CatchAllExceptionMiddleware(app)
        assert middleware.app is app


class TestCatchAllExceptionMiddlewareCall:
    """Tests for CatchAllExceptionMiddleware __call__ method."""

    @pytest.mark.asyncio
    async def test_passes_non_http_requests_through(self) -> None:
        """Should pass non-HTTP requests through unchanged."""
        app = AsyncMock()
        middleware = CatchAllExceptionMiddleware(app)

        scope = {"type": "websocket"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        app.assert_awaited_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_passes_successful_request_through(self) -> None:
        """Should pass successful HTTP requests through."""

        async def mock_app(scope, receive, send):
            await send({"type": "http.response.start", "status": 200})
            await send({"type": "http.response.body", "body": b"OK"})

        middleware = CatchAllExceptionMiddleware(mock_app)

        scope = {"type": "http", "path": "/test"}
        receive = AsyncMock()
        sent_messages = []

        async def capture_send(message):
            sent_messages.append(message)

        await middleware(scope, receive, capture_send)

        assert len(sent_messages) == 2
        assert sent_messages[0]["status"] == 200

    @pytest.mark.asyncio
    async def test_handles_exception_before_response_started(self) -> None:
        """Should return 500 response on exception before response started."""

        async def failing_app(scope, receive, send):
            raise ValueError("Test error")

        middleware = CatchAllExceptionMiddleware(failing_app)

        scope = {"type": "http", "path": "/test"}
        receive = AsyncMock()
        sent_messages = []

        async def capture_send(message):
            sent_messages.append(message)

        await middleware(scope, receive, capture_send)

        assert len(sent_messages) == 2
        assert sent_messages[0]["type"] == "http.response.start"
        assert sent_messages[0]["status"] == 500
        assert sent_messages[1]["type"] == "http.response.body"

    @pytest.mark.asyncio
    async def test_response_body_is_problem_json(self) -> None:
        """Response body should be valid problem+json."""

        async def failing_app(scope, receive, send):
            raise ValueError("Test error message")

        middleware = CatchAllExceptionMiddleware(failing_app)

        scope = {"type": "http", "path": "/api/resource"}
        receive = AsyncMock()
        sent_messages = []

        async def capture_send(message):
            sent_messages.append(message)

        await middleware(scope, receive, capture_send)

        body = sent_messages[1]["body"]
        data = json.loads(body)

        assert data["type"] == "about:blank"
        assert data["title"] == "Internal Server Error"
        assert data["status"] == 500
        assert "Test error message" in data["detail"]
        assert data["instance"] == "/api/resource"
        assert data["code"] == "INTERNAL_ERROR"

    @pytest.mark.asyncio
    async def test_response_has_problem_content_type(self) -> None:
        """Response should have application/problem+json content type."""

        async def failing_app(scope, receive, send):
            raise ValueError("Error")

        middleware = CatchAllExceptionMiddleware(failing_app)

        scope = {"type": "http", "path": "/test"}
        receive = AsyncMock()
        sent_messages = []

        async def capture_send(message):
            sent_messages.append(message)

        await middleware(scope, receive, capture_send)

        headers = dict(sent_messages[0]["headers"])
        assert headers[b"content-type"] == b"application/problem+json"

    @pytest.mark.asyncio
    async def test_handles_exception_after_response_started(self) -> None:
        """Should gracefully handle exception after response started."""

        async def failing_app(scope, receive, send):
            await send({"type": "http.response.start", "status": 200})
            raise ValueError("Error after response started")

        middleware = CatchAllExceptionMiddleware(failing_app)

        scope = {"type": "http", "path": "/test"}
        receive = AsyncMock()
        sent_messages = []

        async def capture_send(message):
            sent_messages.append(message)

        # Should not raise
        await middleware(scope, receive, capture_send)

        # Should have sent empty body to close response
        assert any(m["type"] == "http.response.body" for m in sent_messages)

    @pytest.mark.asyncio
    async def test_uses_path_in_instance_field(self) -> None:
        """Instance field should contain request path."""

        async def failing_app(scope, receive, send):
            raise ValueError("Error")

        middleware = CatchAllExceptionMiddleware(failing_app)

        scope = {"type": "http", "path": "/users/123/profile"}
        receive = AsyncMock()
        sent_messages = []

        async def capture_send(message):
            sent_messages.append(message)

        await middleware(scope, receive, capture_send)

        body = sent_messages[1]["body"]
        data = json.loads(body)
        assert data["instance"] == "/users/123/profile"

    @pytest.mark.asyncio
    async def test_handles_missing_path_in_scope(self) -> None:
        """Should handle missing path in scope."""

        async def failing_app(scope, receive, send):
            raise ValueError("Error")

        middleware = CatchAllExceptionMiddleware(failing_app)

        scope = {"type": "http"}  # No path
        receive = AsyncMock()
        sent_messages = []

        async def capture_send(message):
            sent_messages.append(message)

        await middleware(scope, receive, capture_send)

        body = sent_messages[1]["body"]
        data = json.loads(body)
        assert data["instance"] == "/"  # Default value
