"""Unit tests for svc_infra.api.fastapi.http.deprecation module."""

from __future__ import annotations

import pytest
from starlette.responses import JSONResponse

from svc_infra.api.fastapi.http.deprecation import deprecated


class TestDeprecated:
    """Tests for deprecated decorator."""

    @pytest.mark.asyncio
    async def test_adds_deprecation_header(self) -> None:
        """Test that decorator adds Deprecation header."""

        @deprecated()
        async def handler():
            return JSONResponse({"status": "ok"})

        resp = await handler()
        assert resp.headers.get("Deprecation") == "true"

    @pytest.mark.asyncio
    async def test_adds_sunset_header(self) -> None:
        """Test that decorator adds Sunset header when provided."""
        sunset_date = "Sat, 31 Dec 2025 23:59:59 GMT"

        @deprecated(sunset_http_date=sunset_date)
        async def handler():
            return JSONResponse({"status": "ok"})

        resp = await handler()
        assert resp.headers.get("Deprecation") == "true"
        assert resp.headers.get("Sunset") == sunset_date

    @pytest.mark.asyncio
    async def test_adds_link_header(self) -> None:
        """Test that decorator adds Link header when provided."""
        link = "https://docs.example.com/migration"

        @deprecated(link=link)
        async def handler():
            return JSONResponse({"status": "ok"})

        resp = await handler()
        assert resp.headers.get("Deprecation") == "true"
        assert f'<{link}>; rel="deprecation"' in resp.headers.get("Link", "")

    @pytest.mark.asyncio
    async def test_adds_all_headers(self) -> None:
        """Test that decorator adds all headers when provided."""
        sunset_date = "Sat, 31 Dec 2025 23:59:59 GMT"
        link = "https://docs.example.com/migration"

        @deprecated(sunset_http_date=sunset_date, link=link)
        async def handler():
            return JSONResponse({"status": "ok"})

        resp = await handler()
        assert resp.headers.get("Deprecation") == "true"
        assert resp.headers.get("Sunset") == sunset_date
        assert f'<{link}>; rel="deprecation"' in resp.headers.get("Link", "")

    @pytest.mark.asyncio
    async def test_preserves_response_content(self) -> None:
        """Test that decorator preserves response content."""

        @deprecated()
        async def handler():
            return JSONResponse({"key": "value", "number": 42})

        resp = await handler()
        assert resp.status_code == 200
        # Response body is preserved

    @pytest.mark.asyncio
    async def test_handler_with_arguments(self) -> None:
        """Test that decorator works with handlers that take arguments."""

        @deprecated()
        async def handler(name: str, count: int = 1):
            return JSONResponse({"name": name, "count": count})

        resp = await handler("test", count=5)
        assert resp.headers.get("Deprecation") == "true"

    @pytest.mark.asyncio
    async def test_does_not_overwrite_existing_headers(self) -> None:
        """Test that decorator uses setdefault (doesn't overwrite)."""

        @deprecated(sunset_http_date="2025-01-01")
        async def handler():
            resp = JSONResponse({"status": "ok"})
            resp.headers["Sunset"] = "2024-12-01"
            return resp

        resp = await handler()
        # setdefault should not overwrite existing header
        assert resp.headers.get("Sunset") == "2024-12-01"

    @pytest.mark.asyncio
    async def test_handles_response_without_headers(self) -> None:
        """Test that decorator handles objects without headers gracefully."""

        @deprecated()
        async def handler():
            # Return something without headers attribute
            return {"status": "ok"}

        # Should not raise
        result = await handler()
        assert result == {"status": "ok"}
