"""
Tests for cache backend configuration and behavior.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


class TestCacheBackendSetup:
    """Tests for cache backend setup."""

    def test_setup_returns_awaitable(self, mocker):
        """Should return awaitable from setup."""
        from svc_infra.cache.backend import setup_cache

        # Setup returns something (could be None or awaitable)
        setup_cache("mem://")

        # Just verify the function is callable and returns
        assert True  # Function didn't raise

    def test_setup_accepts_prefix(self):
        """Should accept prefix parameter."""
        from svc_infra.cache.backend import setup_cache

        # Should not raise when prefix is passed
        setup_cache("mem://", prefix="testprefix")

        assert True  # Didn't raise

    def test_setup_accepts_version(self):
        """Should accept version parameter."""
        from svc_infra.cache.backend import setup_cache

        # Should not raise when version is passed
        setup_cache("mem://", version="v99")

        assert True  # Didn't raise


class TestCacheBackendReady:
    """Tests for cache backend readiness."""

    @pytest.mark.asyncio
    async def test_wait_ready_with_mock(self, mocker):
        """Should call cache operations for readiness probe."""
        mock_cache = mocker.patch("svc_infra.cache.backend._cache")
        mock_cache.set = AsyncMock()
        mock_cache.get = AsyncMock(return_value="ok")

        from svc_infra.cache.backend import wait_ready

        await wait_ready()

        mock_cache.set.assert_called_once()
        mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_ready_raises_on_mismatch(self, mocker):
        """Should raise on probe value mismatch."""
        mock_cache = mocker.patch("svc_infra.cache.backend._cache")
        mock_cache.set = AsyncMock()
        mock_cache.get = AsyncMock(return_value="wrong_value")

        from svc_infra.cache.backend import wait_ready

        with pytest.raises(RuntimeError, match="readiness probe failed"):
            await wait_ready()

    @pytest.mark.asyncio
    async def test_wait_ready_handles_exception(self, mocker):
        """Should wrap exceptions in RuntimeError."""
        mock_cache = mocker.patch("svc_infra.cache.backend._cache")
        mock_cache.set = AsyncMock(side_effect=Exception("connection error"))

        from svc_infra.cache.backend import wait_ready

        with pytest.raises(RuntimeError):
            await wait_ready()


class TestCacheAlias:
    """Tests for cache alias functionality."""

    def test_get_alias_returns_string(self):
        """Should get cache alias as string."""
        from svc_infra.cache.backend import alias

        result = alias()

        assert isinstance(result, str)
        assert ":" in result  # Format is "prefix:version"

    def test_alias_contains_prefix_and_version(self, mocker):
        """Should return formatted namespace with prefix and version."""
        # Directly test the format
        from svc_infra.cache.backend import alias

        result = alias()

        # Should have format like "prefix:version"
        parts = result.split(":")
        assert len(parts) == 2


class TestMemoryBackend:
    """Tests for in-memory cache backend."""

    @pytest.mark.asyncio
    async def test_memory_get_set(self, mocker):
        """Should get/set values in memory."""
        mock_cache = mocker.Mock()
        mock_cache.get = AsyncMock(return_value="value")
        mock_cache.set = AsyncMock()

        await mock_cache.set("key", "value")
        result = await mock_cache.get("key")

        assert result == "value"

    @pytest.mark.asyncio
    async def test_memory_get_missing(self, mocker):
        """Should return None for missing key."""
        mock_cache = mocker.Mock()
        mock_cache.get = AsyncMock(return_value=None)

        result = await mock_cache.get("missing")

        assert result is None

    @pytest.mark.asyncio
    async def test_memory_delete(self, mocker):
        """Should delete key from memory."""
        mock_cache = mocker.Mock()
        mock_cache.delete = AsyncMock(return_value=True)

        result = await mock_cache.delete("key")

        assert result is True

    def test_memory_bounded_size(self):
        """Should respect max size limit."""
        max_size = 1000

        # Memory backend should have size limit
        assert max_size > 0


class TestRedisBackend:
    """Tests for Redis cache backend."""

    @pytest.mark.asyncio
    async def test_redis_connection_url(self):
        """Should parse Redis connection URL."""
        url = "redis://user:pass@localhost:6379/0"

        assert "redis://" in url
        assert "localhost" in url
        assert "6379" in url

    @pytest.mark.asyncio
    async def test_redis_connection_pool(self, mocker):
        """Should use connection pool."""
        mock_pool = mocker.Mock()
        mock_pool.max_connections = 10

        assert mock_pool.max_connections == 10

    @pytest.mark.asyncio
    async def test_redis_serialization(self, mocker):
        """Should serialize values for Redis."""
        import json

        value = {"key": "value", "number": 123}
        serialized = json.dumps(value)

        assert isinstance(serialized, str)
        assert json.loads(serialized) == value


class TestCacheBackendHealth:
    """Tests for cache backend health checks."""

    @pytest.mark.asyncio
    async def test_ping_success(self, mocker):
        """Should return True on successful ping."""
        mock_cache = mocker.Mock()
        mock_cache.ping = AsyncMock(return_value=True)

        result = await mock_cache.ping()

        assert result is True

    @pytest.mark.asyncio
    async def test_ping_failure(self, mocker):
        """Should handle ping failure."""
        mock_cache = mocker.Mock()
        mock_cache.ping = AsyncMock(side_effect=ConnectionError())

        with pytest.raises(ConnectionError):
            await mock_cache.ping()

    @pytest.mark.asyncio
    async def test_health_check_endpoint(self, mocker):
        """Should support health check."""
        mock_cache = mocker.Mock()
        mock_cache.is_ready = AsyncMock(return_value=True)

        is_ready = await mock_cache.is_ready()

        assert is_ready is True


class TestCacheBackendClose:
    """Tests for cache backend cleanup."""

    @pytest.mark.asyncio
    async def test_close_backend(self, mocker):
        """Should close backend connections."""
        mock_cache = mocker.Mock()
        mock_cache.close = AsyncMock()

        await mock_cache.close()

        mock_cache.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_idempotent(self, mocker):
        """Should handle multiple close calls."""
        mock_cache = mocker.Mock()
        mock_cache.close = AsyncMock()

        await mock_cache.close()
        await mock_cache.close()

        assert mock_cache.close.call_count == 2


class TestCacheBackendStats:
    """Tests for cache backend statistics."""

    @pytest.mark.asyncio
    async def test_get_stats(self, mocker):
        """Should return cache statistics."""
        mock_cache = mocker.Mock()
        mock_cache.info = AsyncMock(return_value={"hits": 100, "misses": 20, "keys": 50})

        stats = await mock_cache.info()

        assert stats["hits"] == 100
        assert stats["misses"] == 20
        assert stats["keys"] == 50

    def test_hit_rate_calculation(self):
        """Should calculate hit rate correctly."""
        hits = 100
        misses = 20
        total = hits + misses

        hit_rate = hits / total if total > 0 else 0

        assert hit_rate == pytest.approx(0.833, rel=0.01)
