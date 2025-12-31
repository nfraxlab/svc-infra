"""Unit tests for svc_infra.api.fastapi.http.concurrency module."""

from __future__ import annotations

import pytest
from fastapi import HTTPException, status
from starlette.requests import Request

from svc_infra.api.fastapi.http.concurrency import require_if_match


def make_request(headers: dict[str, str] | None = None) -> Request:
    """Create a mock request with given headers."""
    scope = {
        "type": "http",
        "method": "PUT",
        "path": "/test",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
    }
    return Request(scope)


class TestRequireIfMatch:
    """Tests for require_if_match function."""

    def test_missing_if_match_header_raises_428(self) -> None:
        """Test that missing If-Match header raises 428."""
        request = make_request()
        with pytest.raises(HTTPException) as exc_info:
            require_if_match(request, '"abc123"')
        assert exc_info.value.status_code == status.HTTP_428_PRECONDITION_REQUIRED
        assert "If-Match header required" in exc_info.value.detail

    def test_matching_etag_passes(self) -> None:
        """Test that matching ETag passes without error."""
        request = make_request({"If-Match": '"abc123"'})
        # Should not raise
        require_if_match(request, '"abc123"')

    def test_non_matching_etag_raises_412(self) -> None:
        """Test that non-matching ETag raises 412."""
        request = make_request({"If-Match": '"old_etag"'})
        with pytest.raises(HTTPException) as exc_info:
            require_if_match(request, '"new_etag"')
        assert exc_info.value.status_code == status.HTTP_412_PRECONDITION_FAILED
        assert "ETag precondition failed" in exc_info.value.detail

    def test_multiple_etags_one_matching(self) -> None:
        """Test that one matching ETag in list passes."""
        request = make_request({"If-Match": '"etag1", "etag2", "etag3"'})
        # Should not raise - etag2 matches
        require_if_match(request, '"etag2"')

    def test_multiple_etags_none_matching(self) -> None:
        """Test that no matching ETag in list raises 412."""
        request = make_request({"If-Match": '"etag1", "etag2", "etag3"'})
        with pytest.raises(HTTPException) as exc_info:
            require_if_match(request, '"etag4"')
        assert exc_info.value.status_code == status.HTTP_412_PRECONDITION_FAILED

    def test_wildcard_etag_not_supported(self) -> None:
        """Test that wildcard * doesn't match specific ETag."""
        request = make_request({"If-Match": "*"})
        with pytest.raises(HTTPException) as exc_info:
            require_if_match(request, '"specific_etag"')
        assert exc_info.value.status_code == status.HTTP_412_PRECONDITION_FAILED

    def test_etag_with_whitespace_trimmed(self) -> None:
        """Test that whitespace around ETags is trimmed."""
        request = make_request({"If-Match": '  "etag1"  ,   "etag2"  '})
        # Should not raise - whitespace is trimmed
        require_if_match(request, '"etag2"')
