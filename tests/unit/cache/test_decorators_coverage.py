"""Tests for cache decorators - Coverage improvement."""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from svc_infra.cache.decorators import (
    cache_read,
    cache_write,
    cached,
    init_cache,
    init_cache_async,
    mutates,
    recache,
)

# ─── init_cache Tests ──────────────────────────────────────────────────────


class TestInitCache:
    """Tests for init_cache function."""

    @patch("svc_infra.cache.decorators._setup_cache")
    def test_default_args(self, mock_setup: MagicMock) -> None:
        """Test init_cache with default args."""
        init_cache()
        mock_setup.assert_called_once_with(url=None, prefix=None, version=None)

    @patch("svc_infra.cache.decorators._setup_cache")
    def test_with_url(self, mock_setup: MagicMock) -> None:
        """Test init_cache with URL."""
        init_cache(url="redis://localhost:6379")
        mock_setup.assert_called_once_with(url="redis://localhost:6379", prefix=None, version=None)

    @patch("svc_infra.cache.decorators._setup_cache")
    def test_with_prefix(self, mock_setup: MagicMock) -> None:
        """Test init_cache with prefix."""
        init_cache(prefix="myapp")
        mock_setup.assert_called_once_with(url=None, prefix="myapp", version=None)

    @patch("svc_infra.cache.decorators._setup_cache")
    def test_with_all_args(self, mock_setup: MagicMock) -> None:
        """Test init_cache with all args."""
        init_cache(url="redis://host", prefix="app", version="v2")
        mock_setup.assert_called_once_with(url="redis://host", prefix="app", version="v2")


# ─── init_cache_async Tests ────────────────────────────────────────────────


class TestInitCacheAsync:
    """Tests for init_cache_async function."""

    @pytest.mark.asyncio
    @patch("svc_infra.cache.decorators._wait_ready")
    @patch("svc_infra.cache.decorators._setup_cache")
    async def test_calls_setup_and_wait(self, mock_setup: MagicMock, mock_wait: AsyncMock) -> None:
        """Test init_cache_async calls setup and wait."""
        mock_wait.return_value = None
        await init_cache_async()
        mock_setup.assert_called_once()
        mock_wait.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("svc_infra.cache.decorators._wait_ready")
    @patch("svc_infra.cache.decorators._setup_cache")
    async def test_with_args(self, mock_setup: MagicMock, mock_wait: AsyncMock) -> None:
        """Test init_cache_async with args."""
        mock_wait.return_value = None
        await init_cache_async(url="redis://host", prefix="pf", version="v1")
        mock_setup.assert_called_once_with(url="redis://host", prefix="pf", version="v1")


# ─── cache_read Tests ──────────────────────────────────────────────────────


class TestCacheRead:
    """Tests for cache_read decorator."""

    @patch("svc_infra.cache.decorators._alias")
    @patch("svc_infra.cache.decorators._cache")
    def test_basic_decorator(self, mock_cache: MagicMock, mock_alias: MagicMock) -> None:
        """Test basic cache_read decorator."""
        mock_alias.return_value = ""
        mock_cache.cache.return_value = lambda f: f

        @cache_read(key="test:{id}")
        async def get_item(id: int) -> str:
            return f"item:{id}"

        assert callable(get_item)

    @patch("svc_infra.cache.decorators._alias")
    @patch("svc_infra.cache.decorators._cache")
    def test_with_ttl(self, mock_cache: MagicMock, mock_alias: MagicMock) -> None:
        """Test cache_read with custom TTL."""
        mock_alias.return_value = ""
        mock_cache.cache.return_value = lambda f: f

        @cache_read(key="item:{id}", ttl=600)
        async def get_item(id: int) -> str:
            return f"item:{id}"

        assert callable(get_item)

    @patch("svc_infra.cache.decorators._alias")
    @patch("svc_infra.cache.decorators._cache")
    def test_with_tuple_key(self, mock_cache: MagicMock, mock_alias: MagicMock) -> None:
        """Test cache_read with tuple key."""
        mock_alias.return_value = ""
        mock_cache.cache.return_value = lambda f: f

        @cache_read(key=("user", "{id}", "profile"))
        async def get_profile(id: int) -> dict:
            return {"id": id}

        assert callable(get_profile)

    @patch("svc_infra.cache.decorators._alias")
    @patch("svc_infra.cache.decorators._cache")
    def test_with_static_tags(self, mock_cache: MagicMock, mock_alias: MagicMock) -> None:
        """Test cache_read with static tags."""
        mock_alias.return_value = ""
        mock_cache.cache.return_value = lambda f: f

        @cache_read(key="item:{id}", tags=["items", "catalog"])
        async def get_item(id: int) -> str:
            return f"item:{id}"

        assert callable(get_item)

    @patch("svc_infra.cache.decorators._alias")
    @patch("svc_infra.cache.decorators._cache")
    def test_with_early_ttl(self, mock_cache: MagicMock, mock_alias: MagicMock) -> None:
        """Test cache_read with early_ttl."""
        mock_alias.return_value = ""
        mock_cache.cache.return_value = lambda f: f

        @cache_read(key="item:{id}", early_ttl=60)
        async def get_item(id: int) -> str:
            return f"item:{id}"

        assert callable(get_item)

    @patch("svc_infra.cache.decorators._alias")
    @patch("svc_infra.cache.decorators._cache")
    def test_with_refresh(self, mock_cache: MagicMock, mock_alias: MagicMock) -> None:
        """Test cache_read with refresh."""
        mock_alias.return_value = ""
        mock_cache.cache.return_value = lambda f: f

        @cache_read(key="item:{id}", refresh=True)
        async def get_item(id: int) -> str:
            return f"item:{id}"

        assert callable(get_item)

    @patch("svc_infra.cache.decorators._alias")
    @patch("svc_infra.cache.decorators._cache")
    def test_with_namespace(self, mock_cache: MagicMock, mock_alias: MagicMock) -> None:
        """Test cache_read with namespace prefix."""
        mock_alias.return_value = "myapp"
        # First call with prefix fails, second succeeds
        mock_cache.cache.side_effect = [TypeError("no prefix"), lambda f: f]

        @cache_read(key="item:{id}")
        async def get_item(id: int) -> str:
            return f"item:{id}"

        assert callable(get_item)


# ─── cached alias Tests ────────────────────────────────────────────────────


class TestCachedAlias:
    """Tests for cached alias."""

    def test_cached_is_cache_read(self) -> None:
        """Test that cached is cache_read."""
        assert cached is cache_read


# ─── cache_write Tests ─────────────────────────────────────────────────────


class TestCacheWrite:
    """Tests for cache_write decorator."""

    @pytest.mark.asyncio
    @patch("svc_infra.cache.decorators.invalidate_tags")
    @patch("svc_infra.cache.decorators.resolve_tags")
    async def test_basic_invalidation(
        self, mock_resolve: MagicMock, mock_invalidate: AsyncMock
    ) -> None:
        """Test basic cache invalidation."""
        mock_resolve.return_value = ["tag1", "tag2"]
        mock_invalidate.return_value = 5

        @cache_write(tags=["item:{id}"])
        async def update_item(id: int, data: str) -> str:
            return f"updated:{id}"

        result = await update_item(id=42, data="new")
        assert result == "updated:42"
        mock_invalidate.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("svc_infra.cache.decorators.invalidate_tags")
    @patch("svc_infra.cache.decorators.resolve_tags")
    async def test_with_callable_tags(
        self, mock_resolve: MagicMock, mock_invalidate: AsyncMock
    ) -> None:
        """Test cache_write with callable tags."""
        mock_resolve.return_value = ["user:123"]
        mock_invalidate.return_value = 1

        def get_tags(*args, **kwargs):
            return [f"user:{kwargs.get('user_id')}"]

        @cache_write(tags=get_tags)
        async def update_user(user_id: int) -> str:
            return f"user:{user_id}"

        result = await update_user(user_id=123)
        assert result == "user:123"

    @pytest.mark.asyncio
    @patch("svc_infra.cache.decorators.execute_recache")
    @patch("svc_infra.cache.decorators.invalidate_tags")
    @patch("svc_infra.cache.decorators.resolve_tags")
    async def test_with_recache(
        self,
        mock_resolve: MagicMock,
        mock_invalidate: AsyncMock,
        mock_exec_recache: AsyncMock,
    ) -> None:
        """Test cache_write with recache."""
        mock_resolve.return_value = ["item:1"]
        mock_invalidate.return_value = 1
        mock_exec_recache.return_value = None

        async def getter(id: int):
            pass

        @cache_write(tags=["item:{id}"], recache=[recache(getter)])
        async def update_item(id: int) -> str:
            return f"item:{id}"

        await update_item(id=1)
        mock_exec_recache.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("svc_infra.cache.decorators.invalidate_tags")
    @patch("svc_infra.cache.decorators.resolve_tags")
    async def test_invalidation_exception_logged(
        self,
        mock_resolve: MagicMock,
        mock_invalidate: AsyncMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that invalidation exceptions are logged."""
        mock_resolve.return_value = ["tag"]
        mock_invalidate.side_effect = Exception("invalidation failed")

        @cache_write(tags=["tag"])
        async def action() -> str:
            return "done"

        with caplog.at_level(logging.ERROR):
            result = await action()

        assert result == "done"  # Should still return result
        assert "invalidation failed" in caplog.text

    @pytest.mark.asyncio
    @patch("svc_infra.cache.decorators.execute_recache")
    @patch("svc_infra.cache.decorators.invalidate_tags")
    @patch("svc_infra.cache.decorators.resolve_tags")
    async def test_recache_exception_logged(
        self,
        mock_resolve: MagicMock,
        mock_invalidate: AsyncMock,
        mock_exec_recache: AsyncMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that recache exceptions are logged."""
        mock_resolve.return_value = []
        mock_invalidate.return_value = 0
        mock_exec_recache.side_effect = Exception("recache failed")

        async def getter():
            pass

        @cache_write(tags=[], recache=[getter])
        async def action() -> str:
            return "done"

        with caplog.at_level(logging.ERROR):
            result = await action()

        assert result == "done"
        assert "recaching failed" in caplog.text

    @pytest.mark.asyncio
    @patch("svc_infra.cache.decorators.execute_recache")
    @patch("svc_infra.cache.decorators.invalidate_tags")
    @patch("svc_infra.cache.decorators.resolve_tags")
    async def test_recache_max_concurrency(
        self,
        mock_resolve: MagicMock,
        mock_invalidate: AsyncMock,
        mock_exec_recache: AsyncMock,
    ) -> None:
        """Test that recache_max_concurrency is passed."""
        mock_resolve.return_value = []
        mock_invalidate.return_value = 0
        mock_exec_recache.return_value = None

        async def getter():
            pass

        @cache_write(tags=[], recache=[getter], recache_max_concurrency=10)
        async def action(id: int) -> str:
            return str(id)

        await action(id=5)
        # Check that max_concurrency was passed
        call_kwargs = mock_exec_recache.call_args.kwargs
        assert call_kwargs.get("max_concurrency") == 10

    @pytest.mark.asyncio
    @patch("svc_infra.cache.decorators.invalidate_tags")
    @patch("svc_infra.cache.decorators.resolve_tags")
    async def test_empty_resolved_tags(
        self, mock_resolve: MagicMock, mock_invalidate: AsyncMock
    ) -> None:
        """Test with empty resolved tags."""
        mock_resolve.return_value = []

        @cache_write(tags=[])
        async def action() -> str:
            return "done"

        result = await action()
        assert result == "done"
        mock_invalidate.assert_not_awaited()


# ─── mutates alias Tests ───────────────────────────────────────────────────


class TestMutatesAlias:
    """Tests for mutates alias."""

    def test_mutates_is_cache_write(self) -> None:
        """Test that mutates is cache_write."""
        assert mutates is cache_write
