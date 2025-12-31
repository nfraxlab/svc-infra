"""Unit tests for svc_infra.api.fastapi.pagination module."""

from __future__ import annotations

from svc_infra.api.fastapi.pagination import (
    CursorParams,
    FilterParams,
    PageParams,
    Paginated,
    PaginationContext,
    _encode_cursor,
    decode_cursor,
)


class TestCursorParams:
    """Tests for CursorParams model."""

    def test_default_values(self) -> None:
        """Test default parameter values."""
        params = CursorParams()
        assert params.cursor is None
        assert params.limit == 50

    def test_custom_cursor(self) -> None:
        """Test custom cursor value."""
        params = CursorParams(cursor="abc123")
        assert params.cursor == "abc123"

    def test_custom_limit(self) -> None:
        """Test custom limit value."""
        params = CursorParams(limit=100)
        assert params.limit == 100


class TestPageParams:
    """Tests for PageParams model."""

    def test_default_values(self) -> None:
        """Test default parameter values."""
        params = PageParams()
        assert params.page == 1
        assert params.page_size == 50

    def test_custom_values(self) -> None:
        """Test custom values."""
        params = PageParams(page=5, page_size=25)
        assert params.page == 5
        assert params.page_size == 25


class TestFilterParams:
    """Tests for FilterParams model."""

    def test_default_values(self) -> None:
        """Test all defaults are None."""
        params = FilterParams()
        assert params.q is None
        assert params.sort is None
        assert params.created_after is None
        assert params.created_before is None
        assert params.updated_after is None
        assert params.updated_before is None

    def test_search_query(self) -> None:
        """Test search query."""
        params = FilterParams(q="search term")
        assert params.q == "search term"

    def test_sort_param(self) -> None:
        """Test sort parameter."""
        params = FilterParams(sort="-created_at")
        assert params.sort == "-created_at"

    def test_date_filters(self) -> None:
        """Test date filter parameters."""
        params = FilterParams(
            created_after="2024-01-01",
            created_before="2024-12-31",
        )
        assert params.created_after == "2024-01-01"
        assert params.created_before == "2024-12-31"


class TestPaginated:
    """Tests for Paginated model."""

    def test_basic_paginated_response(self) -> None:
        """Test basic paginated response."""
        response = Paginated[str](items=["a", "b", "c"])
        assert response.items == ["a", "b", "c"]
        assert response.next_cursor is None
        assert response.total is None

    def test_with_next_cursor(self) -> None:
        """Test response with next cursor."""
        response = Paginated[int](items=[1, 2, 3], next_cursor="cursor123")
        assert response.items == [1, 2, 3]
        assert response.next_cursor == "cursor123"

    def test_with_total(self) -> None:
        """Test response with total count."""
        response = Paginated[dict](
            items=[{"id": 1}, {"id": 2}],
            total=100,
        )
        assert len(response.items) == 2
        assert response.total == 100

    def test_empty_items(self) -> None:
        """Test with empty items list."""
        response = Paginated[str](items=[])
        assert response.items == []


class TestCursorEncoding:
    """Tests for cursor encoding/decoding."""

    def test_encode_decode_roundtrip(self) -> None:
        """Test encoding and decoding a cursor."""
        payload = {"id": 123, "timestamp": "2024-01-01T00:00:00Z"}
        encoded = _encode_cursor(payload)
        decoded = decode_cursor(encoded)
        assert decoded == payload

    def test_decode_empty_cursor(self) -> None:
        """Test decoding empty cursor returns empty dict."""
        assert decode_cursor(None) == {}
        assert decode_cursor("") == {}

    def test_encode_simple_payload(self) -> None:
        """Test encoding simple payload."""
        encoded = _encode_cursor({"key": "value"})
        assert isinstance(encoded, str)
        # Should not contain padding
        assert "=" not in encoded

    def test_decode_handles_missing_padding(self) -> None:
        """Test decoder handles missing base64 padding."""
        payload = {"test": True}
        encoded = _encode_cursor(payload)
        # Verify it can be decoded
        decoded = decode_cursor(encoded)
        assert decoded == payload


class TestPaginationContext:
    """Tests for PaginationContext class."""

    def test_basic_context(self) -> None:
        """Test basic context creation."""
        ctx = PaginationContext(
            envelope=True,
            allow_cursor=True,
            allow_page=False,
            cursor_params=CursorParams(cursor="abc", limit=25),
            page_params=None,
            filters=None,
        )
        assert ctx.envelope is True
        assert ctx.allow_cursor is True
        assert ctx.allow_page is False
        assert ctx.cursor == "abc"
        assert ctx.limit == 25

    def test_page_mode_context(self) -> None:
        """Test context with page mode."""
        ctx = PaginationContext(
            envelope=True,
            allow_cursor=False,
            allow_page=True,
            cursor_params=None,
            page_params=PageParams(page=2, page_size=10),
            filters=None,
        )
        assert ctx.allow_page is True
        assert ctx.page_params.page == 2
        assert ctx.page_params.page_size == 10

    def test_cursor_property_when_disabled(self) -> None:
        """Test cursor property returns None when disabled."""
        ctx = PaginationContext(
            envelope=False,
            allow_cursor=False,
            allow_page=True,
            cursor_params=CursorParams(cursor="should_be_ignored"),
            page_params=None,
            filters=None,
        )
        assert ctx.cursor is None

    def test_cursor_property_when_enabled(self) -> None:
        """Test cursor property returns value when enabled."""
        ctx = PaginationContext(
            envelope=True,
            allow_cursor=True,
            allow_page=False,
            cursor_params=CursorParams(cursor="my_cursor"),
            page_params=None,
            filters=None,
        )
        assert ctx.cursor == "my_cursor"

    def test_limit_from_cursor_params(self) -> None:
        """Test limit comes from cursor params."""
        ctx = PaginationContext(
            envelope=True,
            allow_cursor=True,
            allow_page=False,
            cursor_params=CursorParams(limit=75),
            page_params=None,
            filters=None,
        )
        assert ctx.limit == 75

    def test_with_filters(self) -> None:
        """Test context with filter params."""
        ctx = PaginationContext(
            envelope=True,
            allow_cursor=True,
            allow_page=False,
            cursor_params=None,
            page_params=None,
            filters=FilterParams(q="search", sort="-name"),
        )
        assert ctx.filters.q == "search"
        assert ctx.filters.sort == "-name"

    def test_limit_override(self) -> None:
        """Test limit override takes precedence."""
        ctx = PaginationContext(
            envelope=True,
            allow_cursor=True,
            allow_page=False,
            cursor_params=CursorParams(limit=50),
            page_params=None,
            filters=None,
            limit_override=10,
        )
        assert ctx.limit_override == 10
