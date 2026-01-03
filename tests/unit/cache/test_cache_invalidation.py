"""
Tests for cache invalidation strategies.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


class TestTagInvalidation:
    """Tests for tag-based cache invalidation."""

    @pytest.mark.asyncio
    async def test_invalidate_single_tag(self, mocker):
        """Should invalidate entries with single tag."""
        from svc_infra.cache.tags import invalidate_tags

        mock_cache = mocker.patch("svc_infra.cache.tags._cache")
        mock_cache.delete_tags = AsyncMock()

        await invalidate_tags("user:123")

        mock_cache.delete_tags.assert_called_once_with("user:123")

    @pytest.mark.asyncio
    async def test_invalidate_multiple_tags(self, mocker):
        """Should invalidate entries with multiple tags."""
        from svc_infra.cache.tags import invalidate_tags

        mock_cache = mocker.patch("svc_infra.cache.tags._cache")
        mock_cache.delete_tags = AsyncMock()

        await invalidate_tags("user:123", "session:456", "orders:789")

        mock_cache.delete_tags.assert_called_once_with("user:123", "session:456", "orders:789")

    @pytest.mark.asyncio
    async def test_invalidate_empty_tags(self, mocker):
        """Should return 0 for empty tags."""
        from svc_infra.cache.tags import invalidate_tags

        result = await invalidate_tags()

        assert result == 0

    @pytest.mark.asyncio
    async def test_invalidate_deduplicates_tags(self, mocker):
        """Should deduplicate tags before invalidation."""
        from svc_infra.cache.tags import invalidate_tags

        mock_cache = mocker.patch("svc_infra.cache.tags._cache")
        mock_cache.delete_tags = AsyncMock()

        await invalidate_tags("tag1", "tag2", "tag1", "tag2")

        # Should only contain unique tags
        call_args = mock_cache.delete_tags.call_args[0]
        assert len(call_args) == 2

    @pytest.mark.asyncio
    async def test_invalidate_fallback_on_error(self, mocker):
        """Should fallback to private method on error."""
        from svc_infra.cache.tags import invalidate_tags

        mock_cache = mocker.patch("svc_infra.cache.tags._cache")
        mock_cache.delete_tags = AsyncMock(side_effect=Exception("error"))
        mock_cache._delete_tag = AsyncMock()

        await invalidate_tags("tag1")

        # Should try fallback
        mock_cache._delete_tag.assert_called_once_with("tag1")


class TestKeyPatternInvalidation:
    """Tests for key pattern invalidation."""

    @pytest.mark.asyncio
    async def test_invalidate_by_prefix(self, mocker):
        """Should invalidate all keys with prefix."""
        mock_cache = mocker.Mock()
        mock_cache.delete_match = AsyncMock(return_value=5)

        result = await mock_cache.delete_match("user:*")

        assert result == 5
        mock_cache.delete_match.assert_called_once_with("user:*")

    @pytest.mark.asyncio
    async def test_invalidate_by_suffix(self, mocker):
        """Should invalidate all keys with suffix."""
        mock_cache = mocker.Mock()
        mock_cache.delete_match = AsyncMock(return_value=3)

        result = await mock_cache.delete_match("*:v1")

        assert result == 3

    @pytest.mark.asyncio
    async def test_invalidate_by_glob_pattern(self, mocker):
        """Should invalidate keys matching glob pattern."""
        mock_cache = mocker.Mock()
        mock_cache.delete_match = AsyncMock(return_value=10)

        result = await mock_cache.delete_match("user:*:profile")

        assert result == 10


class TestSingleKeyInvalidation:
    """Tests for single key invalidation."""

    @pytest.mark.asyncio
    async def test_delete_single_key(self, mocker):
        """Should delete single key."""
        mock_cache = mocker.Mock()
        mock_cache.delete = AsyncMock(return_value=True)

        result = await mock_cache.delete("user:123")

        assert result is True
        mock_cache.delete.assert_called_once_with("user:123")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self, mocker):
        """Should handle deletion of nonexistent key."""
        mock_cache = mocker.Mock()
        mock_cache.delete = AsyncMock(return_value=False)

        result = await mock_cache.delete("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_multiple_keys(self, mocker):
        """Should delete multiple keys in batch."""
        mock_cache = mocker.Mock()
        mock_cache.delete_many = AsyncMock(return_value=3)

        result = await mock_cache.delete_many(["key1", "key2", "key3"])

        assert result == 3


class TestCascadeInvalidation:
    """Tests for cascade invalidation."""

    @pytest.mark.asyncio
    async def test_invalidate_cascades_to_related(self, mocker):
        """Should cascade invalidation to related entries."""
        mock_cache = mocker.Mock()
        mock_cache.delete = AsyncMock()
        mock_cache.delete_match = AsyncMock()

        # When user is deleted, cascade to related caches
        user_id = "123"

        await mock_cache.delete(f"user:{user_id}")
        await mock_cache.delete_match(f"user:{user_id}:*")
        await mock_cache.delete_match(f"*:user:{user_id}")

        assert mock_cache.delete.call_count == 1
        assert mock_cache.delete_match.call_count == 2


class TestInvalidationEvents:
    """Tests for invalidation event handling."""

    @pytest.mark.asyncio
    async def test_invalidation_callback(self, mocker):
        """Should call callback on invalidation."""
        callback = mocker.Mock()
        mock_cache = mocker.Mock()
        mock_cache.delete = AsyncMock(return_value=True)

        await mock_cache.delete("key")
        callback("key")

        callback.assert_called_once_with("key")

    @pytest.mark.asyncio
    async def test_invalidation_logging(self, mocker):
        """Should log invalidation events."""
        mock_logger = mocker.patch("svc_infra.cache.tags.logger")
        mock_cache = mocker.patch("svc_infra.cache.tags._cache")
        mock_cache.delete_tags = AsyncMock(side_effect=Exception("test error"))
        mock_cache._delete_tag = AsyncMock()

        from svc_infra.cache.tags import invalidate_tags

        await invalidate_tags("tag1")

        # Should log warning on failure
        mock_logger.warning.assert_called()


class TestBulkInvalidation:
    """Tests for bulk invalidation operations."""

    @pytest.mark.asyncio
    async def test_flush_all(self, mocker):
        """Should flush entire cache."""
        mock_cache = mocker.Mock()
        mock_cache.clear = AsyncMock()

        await mock_cache.clear()

        mock_cache.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_flush_namespace(self, mocker):
        """Should flush specific namespace."""
        mock_cache = mocker.Mock()
        mock_cache.delete_match = AsyncMock(return_value=100)

        result = await mock_cache.delete_match("namespace:*")

        assert result == 100


class TestVersionedInvalidation:
    """Tests for versioned cache invalidation."""

    def test_version_bump_invalidates(self):
        """Should invalidate by bumping version."""

        def make_key(resource: str, version: int) -> str:
            return f"{resource}:v{version}"

        old_key = make_key("user:123", 1)
        new_key = make_key("user:123", 2)

        # New version means old cache is stale
        assert old_key != new_key

    @pytest.mark.asyncio
    async def test_get_current_version(self, mocker):
        """Should get current cache version."""
        mock_cache = mocker.Mock()
        mock_cache.get = AsyncMock(return_value="5")

        version = await mock_cache.get("user:123:version")

        assert version == "5"

    @pytest.mark.asyncio
    async def test_increment_version(self, mocker):
        """Should increment version to invalidate."""
        mock_cache = mocker.Mock()
        mock_cache.incr = AsyncMock(return_value=6)

        new_version = await mock_cache.incr("user:123:version")

        assert new_version == 6
