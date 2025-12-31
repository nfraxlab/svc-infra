"""Unit tests for svc_infra.api.fastapi.http.conditional module."""

from __future__ import annotations

from datetime import UTC, datetime
from email.utils import format_datetime

from starlette.requests import Request
from starlette.responses import Response

from svc_infra.api.fastapi.http.conditional import (
    compute_etag,
    maybe_not_modified,
    set_conditional_headers,
)


def make_request(headers: dict[str, str] | None = None) -> Request:
    """Create a mock request with given headers."""
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
    }
    return Request(scope)


class TestComputeEtag:
    """Tests for compute_etag function."""

    def test_returns_quoted_etag(self) -> None:
        """Test that ETag is wrapped in quotes."""
        etag = compute_etag(b"test content")
        assert etag.startswith('"')
        assert etag.endswith('"')

    def test_same_content_same_etag(self) -> None:
        """Test that same content produces same ETag."""
        etag1 = compute_etag(b"hello world")
        etag2 = compute_etag(b"hello world")
        assert etag1 == etag2

    def test_different_content_different_etag(self) -> None:
        """Test that different content produces different ETag."""
        etag1 = compute_etag(b"hello")
        etag2 = compute_etag(b"world")
        assert etag1 != etag2

    def test_empty_content(self) -> None:
        """Test ETag for empty content."""
        etag = compute_etag(b"")
        assert etag.startswith('"')
        assert etag.endswith('"')
        # Empty content still has a hash
        assert len(etag) > 2


class TestSetConditionalHeaders:
    """Tests for set_conditional_headers function."""

    def test_sets_etag_header(self) -> None:
        """Test that ETag header is set."""
        resp = Response()
        set_conditional_headers(resp, etag='"abc123"')
        assert resp.headers["ETag"] == '"abc123"'

    def test_sets_last_modified_header(self) -> None:
        """Test that Last-Modified header is set."""
        resp = Response()
        dt = datetime(2024, 1, 15, 12, 30, 0, tzinfo=UTC)
        set_conditional_headers(resp, last_modified=dt)
        assert "Last-Modified" in resp.headers
        assert "Mon, 15 Jan 2024" in resp.headers["Last-Modified"]

    def test_sets_both_headers(self) -> None:
        """Test that both headers are set."""
        resp = Response()
        dt = datetime(2024, 1, 15, 12, 30, 0, tzinfo=UTC)
        set_conditional_headers(resp, etag='"abc123"', last_modified=dt)
        assert resp.headers["ETag"] == '"abc123"'
        assert "Last-Modified" in resp.headers

    def test_handles_naive_datetime(self) -> None:
        """Test that naive datetime gets UTC timezone added."""
        resp = Response()
        dt = datetime(2024, 1, 15, 12, 30, 0)  # No timezone
        set_conditional_headers(resp, last_modified=dt)
        assert "Last-Modified" in resp.headers

    def test_no_headers_when_none(self) -> None:
        """Test that no headers are set when values are None."""
        resp = Response()
        set_conditional_headers(resp, etag=None, last_modified=None)
        assert "ETag" not in resp.headers
        assert "Last-Modified" not in resp.headers


class TestMaybeNotModified:
    """Tests for maybe_not_modified function."""

    def test_matching_etag_returns_true(self) -> None:
        """Test that matching ETag returns True."""
        request = make_request({"If-None-Match": '"abc123"'})
        assert maybe_not_modified(request, '"abc123"', None) is True

    def test_non_matching_etag_returns_false(self) -> None:
        """Test that non-matching ETag returns False."""
        request = make_request({"If-None-Match": '"old"'})
        assert maybe_not_modified(request, '"new"', None) is False

    def test_multiple_etags_one_matching(self) -> None:
        """Test with multiple ETags where one matches."""
        request = make_request({"If-None-Match": '"tag1", "tag2", "tag3"'})
        assert maybe_not_modified(request, '"tag2"', None) is True

    def test_if_modified_since_not_modified(self) -> None:
        """Test If-Modified-Since when resource is older."""
        # Resource was last modified Jan 1, client has cached since Jan 15
        last_modified = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        client_cached = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        request = make_request({"If-Modified-Since": format_datetime(client_cached)})
        assert maybe_not_modified(request, None, last_modified) is True

    def test_if_modified_since_modified(self) -> None:
        """Test If-Modified-Since when resource is newer."""
        # Resource was last modified Jan 15, client has cached since Jan 1
        last_modified = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        client_cached = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        request = make_request({"If-Modified-Since": format_datetime(client_cached)})
        assert maybe_not_modified(request, None, last_modified) is False

    def test_no_cache_headers_returns_false(self) -> None:
        """Test that missing cache headers returns False."""
        request = make_request()
        assert maybe_not_modified(request, '"abc"', None) is False

    def test_invalid_date_handled_gracefully(self) -> None:
        """Test that invalid If-Modified-Since date is handled."""
        request = make_request({"If-Modified-Since": "invalid date"})
        last_modified = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        # Should not raise, returns False
        assert maybe_not_modified(request, None, last_modified) is False

    def test_etag_or_time_check(self) -> None:
        """Test that either ETag or time check passing returns True."""
        # ETag matches but time doesn't
        last_modified = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        client_cached = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        request = make_request(
            {
                "If-None-Match": '"abc123"',
                "If-Modified-Since": format_datetime(client_cached),
            }
        )
        assert maybe_not_modified(request, '"abc123"', last_modified) is True
