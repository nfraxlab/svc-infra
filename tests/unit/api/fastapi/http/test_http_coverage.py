"""Tests for FastAPI HTTP utilities - Coverage improvement."""

from __future__ import annotations

from datetime import UTC, datetime
from email.utils import format_datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from svc_infra.api.fastapi.http.concurrency import require_if_match
from svc_infra.api.fastapi.http.conditional import (
    compute_etag,
    maybe_not_modified,
    set_conditional_headers,
)
from svc_infra.api.fastapi.http.deprecation import deprecated

# ─── require_if_match Tests ────────────────────────────────────────────────


class TestRequireIfMatch:
    """Tests for require_if_match function."""

    def test_missing_header_raises(self) -> None:
        """Test raises 428 when If-Match header missing."""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            require_if_match(mock_request, '"etag123"')

        assert exc_info.value.status_code == 428
        assert "If-Match header required" in exc_info.value.detail

    def test_etag_mismatch_raises(self) -> None:
        """Test raises 412 when ETag doesn't match."""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = '"old-etag"'

        with pytest.raises(HTTPException) as exc_info:
            require_if_match(mock_request, '"new-etag"')

        assert exc_info.value.status_code == 412
        assert "ETag precondition failed" in exc_info.value.detail

    def test_etag_match_passes(self) -> None:
        """Test passes when ETag matches."""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = '"etag123"'

        # Should not raise
        require_if_match(mock_request, '"etag123"')

    def test_etag_in_list_passes(self) -> None:
        """Test passes when ETag is in comma-separated list."""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = '"etag1", "etag2", "etag3"'

        # Should not raise
        require_if_match(mock_request, '"etag2"')


# ─── compute_etag Tests ────────────────────────────────────────────────────


class TestComputeEtag:
    """Tests for compute_etag function."""

    def test_returns_quoted_hash(self) -> None:
        """Test returns properly quoted ETag."""
        etag = compute_etag(b"hello world")
        assert etag.startswith('"')
        assert etag.endswith('"')
        # SHA256 is 64 hex chars
        assert len(etag) == 66

    def test_deterministic(self) -> None:
        """Test same input gives same ETag."""
        data = b"test data"
        assert compute_etag(data) == compute_etag(data)

    def test_different_data_different_etag(self) -> None:
        """Test different input gives different ETag."""
        assert compute_etag(b"data1") != compute_etag(b"data2")


# ─── set_conditional_headers Tests ─────────────────────────────────────────


class TestSetConditionalHeaders:
    """Tests for set_conditional_headers function."""

    def test_sets_etag(self) -> None:
        """Test sets ETag header."""
        mock_response = MagicMock()
        mock_response.headers = {}

        set_conditional_headers(mock_response, etag='"abc123"')

        assert mock_response.headers["ETag"] == '"abc123"'

    def test_sets_last_modified(self) -> None:
        """Test sets Last-Modified header."""
        mock_response = MagicMock()
        mock_response.headers = {}
        dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

        set_conditional_headers(mock_response, last_modified=dt)

        assert "Last-Modified" in mock_response.headers

    def test_naive_datetime_gets_utc(self) -> None:
        """Test naive datetime is converted to UTC."""
        mock_response = MagicMock()
        mock_response.headers = {}
        dt = datetime(2024, 1, 15, 12, 0, 0)  # naive

        set_conditional_headers(mock_response, last_modified=dt)

        assert "Last-Modified" in mock_response.headers

    def test_sets_both_headers(self) -> None:
        """Test sets both headers when provided."""
        mock_response = MagicMock()
        mock_response.headers = {}
        dt = datetime(2024, 1, 15, tzinfo=UTC)

        set_conditional_headers(mock_response, etag='"xyz"', last_modified=dt)

        assert mock_response.headers["ETag"] == '"xyz"'
        assert "Last-Modified" in mock_response.headers

    def test_no_headers_when_none(self) -> None:
        """Test no headers set when all None."""
        mock_response = MagicMock()
        mock_response.headers = {}

        set_conditional_headers(mock_response)

        assert "ETag" not in mock_response.headers
        assert "Last-Modified" not in mock_response.headers


# ─── maybe_not_modified Tests ──────────────────────────────────────────────


class TestMaybeNotModified:
    """Tests for maybe_not_modified function."""

    def test_etag_match(self) -> None:
        """Test returns True when ETag matches."""
        mock_request = MagicMock()
        mock_request.headers.get.side_effect = lambda h: (
            '"etag123"' if h == "If-None-Match" else None
        )

        result = maybe_not_modified(mock_request, '"etag123"', None)
        assert result is True

    def test_etag_in_list(self) -> None:
        """Test returns True when ETag is in list."""
        mock_request = MagicMock()
        mock_request.headers.get.side_effect = lambda h: (
            '"a", "b", "c"' if h == "If-None-Match" else None
        )

        result = maybe_not_modified(mock_request, '"b"', None)
        assert result is True

    def test_etag_no_match(self) -> None:
        """Test returns False when ETag doesn't match."""
        mock_request = MagicMock()
        mock_request.headers.get.side_effect = lambda h: ('"old"' if h == "If-None-Match" else None)

        result = maybe_not_modified(mock_request, '"new"', None)
        assert result is False

    def test_last_modified_match(self) -> None:
        """Test returns True when not modified since."""
        past = datetime(2024, 1, 1, tzinfo=UTC)
        future = datetime(2024, 6, 1, tzinfo=UTC)
        mock_request = MagicMock()
        mock_request.headers.get.side_effect = lambda h: (
            format_datetime(future) if h == "If-Modified-Since" else None
        )

        result = maybe_not_modified(mock_request, None, past)
        assert result is True

    def test_last_modified_no_match(self) -> None:
        """Test returns False when modified since."""
        past = datetime(2024, 1, 1, tzinfo=UTC)
        future = datetime(2024, 6, 1, tzinfo=UTC)
        mock_request = MagicMock()
        mock_request.headers.get.side_effect = lambda h: (
            format_datetime(past) if h == "If-Modified-Since" else None
        )

        result = maybe_not_modified(mock_request, None, future)
        assert result is False

    def test_invalid_if_modified_since(self) -> None:
        """Test handles invalid If-Modified-Since gracefully."""
        mock_request = MagicMock()
        mock_request.headers.get.side_effect = lambda h: (
            "not-a-date" if h == "If-Modified-Since" else None
        )

        result = maybe_not_modified(mock_request, None, datetime.now(UTC))
        assert result is False

    def test_no_headers_returns_false(self) -> None:
        """Test returns False when no conditional headers."""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None

        result = maybe_not_modified(mock_request, '"etag"', datetime.now(UTC))
        assert result is False


# ─── deprecated Tests ──────────────────────────────────────────────────────


class TestDeprecated:
    """Tests for deprecated decorator."""

    @pytest.mark.asyncio
    async def test_adds_deprecation_header(self) -> None:
        """Test adds Deprecation header."""
        mock_response = MagicMock()
        mock_response.headers = {}

        @deprecated()
        async def handler():
            return mock_response

        result = await handler()

        assert result.headers.get("Deprecation") == "true"

    @pytest.mark.asyncio
    async def test_adds_sunset_header(self) -> None:
        """Test adds Sunset header when provided."""
        mock_response = MagicMock()
        mock_response.headers = {}

        @deprecated(sunset_http_date="Sat, 01 Jan 2025 00:00:00 GMT")
        async def handler():
            return mock_response

        result = await handler()

        assert result.headers.get("Sunset") == "Sat, 01 Jan 2025 00:00:00 GMT"

    @pytest.mark.asyncio
    async def test_adds_link_header(self) -> None:
        """Test adds Link header when provided."""
        mock_response = MagicMock()
        mock_response.headers = {}

        @deprecated(link="https://docs.example.com/migration")
        async def handler():
            return mock_response

        result = await handler()

        assert 'rel="deprecation"' in result.headers.get("Link", "")

    @pytest.mark.asyncio
    async def test_response_without_headers(self) -> None:
        """Test handles response without headers attribute."""

        @deprecated()
        async def handler():
            return {"data": "value"}  # No headers attribute

        result = await handler()

        assert result == {"data": "value"}

    @pytest.mark.asyncio
    async def test_preserves_existing_headers(self) -> None:
        """Test doesn't overwrite existing headers."""
        mock_response = MagicMock()
        mock_response.headers = {"Deprecation": "custom"}

        @deprecated()
        async def handler():
            return mock_response

        result = await handler()

        # setdefault should preserve existing
        assert result.headers.get("Deprecation") == "custom"
