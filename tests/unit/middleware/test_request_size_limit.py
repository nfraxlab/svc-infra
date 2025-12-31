"""Tests for svc_infra.api.fastapi.middleware.request_size_limit module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from svc_infra.api.fastapi.middleware.request_size_limit import (
    RequestSizeLimitMiddleware,
)


class TestRequestSizeLimitMiddlewareInit:
    """Tests for RequestSizeLimitMiddleware initialization."""

    def test_default_max_bytes(self) -> None:
        """Should have 1MB default max_bytes."""
        app = MagicMock()
        middleware = RequestSizeLimitMiddleware(app)
        assert middleware.max_bytes == 1_000_000

    def test_custom_max_bytes(self) -> None:
        """Should accept custom max_bytes."""
        app = MagicMock()
        middleware = RequestSizeLimitMiddleware(app, max_bytes=5_000_000)
        assert middleware.max_bytes == 5_000_000

    def test_small_limit(self) -> None:
        """Should accept small limit."""
        app = MagicMock()
        middleware = RequestSizeLimitMiddleware(app, max_bytes=1024)
        assert middleware.max_bytes == 1024


class TestRequestSizeLimitMiddlewareDispatch:
    """Tests for RequestSizeLimitMiddleware dispatch method."""

    @pytest.fixture
    def mock_app(self) -> MagicMock:
        return MagicMock()

    @pytest.mark.asyncio
    async def test_allows_request_under_limit(self, mock_app: MagicMock) -> None:
        """Should allow requests under the size limit."""
        middleware = RequestSizeLimitMiddleware(mock_app, max_bytes=1000)

        request = MagicMock()
        request.headers = {"content-length": "500"}

        call_next = AsyncMock(return_value=MagicMock())

        await middleware.dispatch(request, call_next)

        call_next.assert_awaited_once_with(request)

    @pytest.mark.asyncio
    async def test_allows_request_at_limit(self, mock_app: MagicMock) -> None:
        """Should allow requests exactly at the size limit."""
        middleware = RequestSizeLimitMiddleware(mock_app, max_bytes=1000)

        request = MagicMock()
        request.headers = {"content-length": "1000"}

        call_next = AsyncMock(return_value=MagicMock())

        await middleware.dispatch(request, call_next)

        call_next.assert_awaited_once_with(request)

    @pytest.mark.asyncio
    async def test_rejects_request_over_limit(self, mock_app: MagicMock) -> None:
        """Should reject requests over the size limit with 413."""
        middleware = RequestSizeLimitMiddleware(mock_app, max_bytes=1000)

        request = MagicMock()
        request.headers = {"content-length": "2000"}
        request.url = MagicMock()
        request.url.path = "/api/upload"

        call_next = AsyncMock()

        result = await middleware.dispatch(request, call_next)

        call_next.assert_not_awaited()
        assert result.status_code == 413

    @pytest.mark.asyncio
    async def test_allows_request_without_content_length(self, mock_app: MagicMock) -> None:
        """Should allow requests without content-length header."""
        middleware = RequestSizeLimitMiddleware(mock_app, max_bytes=1000)

        request = MagicMock()
        request.headers = {}

        call_next = AsyncMock(return_value=MagicMock())

        await middleware.dispatch(request, call_next)

        call_next.assert_awaited_once_with(request)

    @pytest.mark.asyncio
    async def test_handles_invalid_content_length(self, mock_app: MagicMock) -> None:
        """Should allow request if content-length is invalid."""
        middleware = RequestSizeLimitMiddleware(mock_app, max_bytes=1000)

        request = MagicMock()
        request.headers = {"content-length": "not-a-number"}

        call_next = AsyncMock(return_value=MagicMock())

        await middleware.dispatch(request, call_next)

        call_next.assert_awaited_once_with(request)

    @pytest.mark.asyncio
    async def test_handles_empty_content_length(self, mock_app: MagicMock) -> None:
        """Should allow request if content-length is empty."""
        middleware = RequestSizeLimitMiddleware(mock_app, max_bytes=1000)

        request = MagicMock()
        request.headers = {"content-length": ""}

        call_next = AsyncMock(return_value=MagicMock())

        await middleware.dispatch(request, call_next)

        call_next.assert_awaited_once_with(request)


class TestRequestSizeLimitResponse:
    """Tests for the 413 response format."""

    @pytest.fixture
    def mock_app(self) -> MagicMock:
        return MagicMock()

    @pytest.mark.asyncio
    async def test_response_has_correct_status(self, mock_app: MagicMock) -> None:
        """Response should have 413 status code."""
        middleware = RequestSizeLimitMiddleware(mock_app, max_bytes=100)

        request = MagicMock()
        request.headers = {"content-length": "1000"}
        request.url = MagicMock()
        request.url.path = "/test"

        call_next = AsyncMock()

        result = await middleware.dispatch(request, call_next)

        assert result.status_code == 413

    @pytest.mark.asyncio
    async def test_response_body_contains_title(self, mock_app: MagicMock) -> None:
        """Response body should contain title."""
        middleware = RequestSizeLimitMiddleware(mock_app, max_bytes=100)

        request = MagicMock()
        request.headers = {"content-length": "1000"}
        request.url = MagicMock()
        request.url.path = "/test"

        call_next = AsyncMock()

        result = await middleware.dispatch(request, call_next)

        body = result.body
        assert b"Payload Too Large" in body

    @pytest.mark.asyncio
    async def test_response_body_contains_error_code(self, mock_app: MagicMock) -> None:
        """Response body should contain error code."""
        middleware = RequestSizeLimitMiddleware(mock_app, max_bytes=100)

        request = MagicMock()
        request.headers = {"content-length": "1000"}
        request.url = MagicMock()
        request.url.path = "/test"

        call_next = AsyncMock()

        result = await middleware.dispatch(request, call_next)

        body = result.body
        assert b"PAYLOAD_TOO_LARGE" in body

    @pytest.mark.asyncio
    async def test_handles_missing_url_attribute(self, mock_app: MagicMock) -> None:
        """Should handle request without url attribute."""
        middleware = RequestSizeLimitMiddleware(mock_app, max_bytes=100)

        request = MagicMock(spec=[])  # No url attribute
        request.headers = {"content-length": "1000"}

        call_next = AsyncMock()

        # Should not raise
        result = await middleware.dispatch(request, call_next)

        assert result.status_code == 413
