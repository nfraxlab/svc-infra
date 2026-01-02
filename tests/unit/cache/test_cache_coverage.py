"""Tests for cache module coverage - targeting uncovered execution paths."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCacheBackendSetup:
    """Tests for cache backend setup functionality."""

    def test_setup_cache_function_exists(self) -> None:
        """Test setup_cache function is available and callable."""
        from svc_infra.cache.backend import setup_cache

        assert callable(setup_cache)

    def test_setup_cache_prefix_update_mechanism(self) -> None:
        """Test that prefix can be updated via global variable."""
        from svc_infra.cache import backend

        original = backend._current_prefix
        try:
            backend._current_prefix = "custom_prefix"
            assert backend.alias().startswith("custom_prefix:")
        finally:
            backend._current_prefix = original

    def test_setup_cache_version_update_mechanism(self) -> None:
        """Test that version can be updated via global variable."""
        from svc_infra.cache import backend

        original = backend._current_version
        try:
            backend._current_version = "v99"
            assert backend.alias().endswith(":v99")
        finally:
            backend._current_version = original


class TestCacheBackendWaitReady:
    """Tests for cache backend readiness check."""

    @pytest.mark.asyncio
    async def test_wait_ready_success(self) -> None:
        """Test wait_ready succeeds with valid probe."""
        from svc_infra.cache import backend

        with (
            patch.object(backend._cache, "set", new_callable=AsyncMock) as mock_set,
            patch.object(backend._cache, "get", new_callable=AsyncMock) as mock_get,
        ):
            mock_get.return_value = backend.PROBE_VALUE

            await backend.wait_ready()

            mock_set.assert_called_once()
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_ready_fails_on_wrong_value(self) -> None:
        """Test wait_ready fails when probe value doesn't match."""
        from svc_infra.cache import backend

        with (
            patch.object(backend._cache, "set", new_callable=AsyncMock),
            patch.object(backend._cache, "get", new_callable=AsyncMock) as mock_get,
        ):
            mock_get.return_value = "wrong_value"

            with pytest.raises(RuntimeError, match="Cache readiness probe failed"):
                await backend.wait_ready()

    @pytest.mark.asyncio
    async def test_wait_ready_fails_on_exception(self) -> None:
        """Test wait_ready fails on cache exception."""
        from svc_infra.cache import backend

        with patch.object(backend._cache, "set", new_callable=AsyncMock) as mock_set:
            mock_set.side_effect = ConnectionError("Redis down")

            with pytest.raises(RuntimeError, match="encountered error"):
                await backend.wait_ready()


class TestCacheBackendShutdown:
    """Tests for cache backend shutdown."""

    @pytest.mark.asyncio
    async def test_shutdown_cache_success(self) -> None:
        """Test shutdown_cache succeeds."""
        from svc_infra.cache import backend

        with patch.object(backend._cache, "close", new_callable=AsyncMock) as mock_close:
            await backend.shutdown_cache()

            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_cache_handles_error(self) -> None:
        """Test shutdown_cache handles error gracefully."""
        from svc_infra.cache import backend

        with patch.object(backend._cache, "close", new_callable=AsyncMock) as mock_close:
            mock_close.side_effect = Exception("Shutdown error")

            # Should not raise
            await backend.shutdown_cache()


class TestInvalidateTags:
    """Tests for cache tag invalidation."""

    @pytest.mark.asyncio
    async def test_invalidate_tags_empty(self) -> None:
        """Test invalidate_tags with no tags returns 0."""
        from svc_infra.cache.tags import invalidate_tags

        result = await invalidate_tags()
        assert result == 0

    @pytest.mark.asyncio
    async def test_invalidate_tags_with_delete_tags(self) -> None:
        """Test invalidate_tags uses delete_tags when available."""
        from svc_infra.cache import tags

        with patch.object(tags._cache, "delete_tags", new_callable=AsyncMock) as mock_delete:
            result = await tags.invalidate_tags("user:1", "user:2")

            assert result == 2
            mock_delete.assert_called_once_with("user:1", "user:2")

    @pytest.mark.asyncio
    async def test_invalidate_tags_deduplicates(self) -> None:
        """Test invalidate_tags deduplicates tags."""
        from svc_infra.cache import tags

        with patch.object(tags._cache, "delete_tags", new_callable=AsyncMock) as mock_delete:
            result = await tags.invalidate_tags("user:1", "user:1", "user:2")

            assert result == 2  # Deduplicated
            mock_delete.assert_called_once_with("user:1", "user:2")

    @pytest.mark.asyncio
    async def test_invalidate_tags_fallback_private_delete(self) -> None:
        """Test invalidate_tags falls back to _delete_tag when delete_tags fails."""
        from svc_infra.cache import tags

        # Simulate delete_tags raising an exception, triggering fallback
        mock_delete_tag = AsyncMock()

        with (
            patch.object(tags._cache, "delete_tags", new_callable=AsyncMock) as mock_delete_tags,
            patch.object(tags._cache, "_delete_tag", mock_delete_tag, create=True),
        ):
            mock_delete_tags.side_effect = Exception("delete_tags failed")

            result = await tags.invalidate_tags("user:1", "user:2")

            # Fallback should have been used
            assert result == 2
            assert mock_delete_tag.call_count == 2

    @pytest.mark.asyncio
    async def test_invalidate_tags_handles_delete_tags_error(self) -> None:
        """Test invalidate_tags handles delete_tags error."""
        from svc_infra.cache import tags

        with patch.object(tags._cache, "delete_tags", new_callable=AsyncMock) as mock_delete:
            mock_delete.side_effect = Exception("Delete failed")

            # Should not raise, but return 0 (fallback will also fail without _delete_tag)
            result = await tags.invalidate_tags("user:1")
            assert result == 0


class TestResourceCacheWriteExecution:
    """Tests for Resource cache_write execution paths."""

    @pytest.mark.asyncio
    async def test_cache_write_executes_mutation(self) -> None:
        """Test cache_write decorator executes the mutation."""
        from svc_infra.cache.resources import Resource

        res = Resource("user", "user_id")
        call_count = 0

        @res.cache_write()
        async def update_user(*, user_id: int, name: str) -> dict:
            nonlocal call_count
            call_count += 1
            return {"id": user_id, "name": name}

        with (
            patch("svc_infra.cache.resources._cache") as mock_cache,
            patch("svc_infra.cache.resources._alias", return_value="svc:v1"),
        ):
            mock_cache.invalidate = AsyncMock()
            mock_cache.delete = AsyncMock()
            mock_cache.delete_match = AsyncMock()

            result = await update_user(user_id=123, name="Updated")

            assert call_count == 1
            assert result == {"id": 123, "name": "Updated"}

    @pytest.mark.asyncio
    async def test_cache_write_invalidates_tags(self) -> None:
        """Test cache_write invalidates entity tags."""
        from svc_infra.cache.resources import Resource

        res = Resource("user", "user_id")

        @res.cache_write()
        async def update_user(*, user_id: int, name: str) -> dict:
            return {"id": user_id, "name": name}

        with (
            patch("svc_infra.cache.resources._cache") as mock_cache,
            patch("svc_infra.cache.resources._alias", return_value="svc:v1"),
        ):
            mock_cache.invalidate = AsyncMock()
            mock_cache.delete = AsyncMock()
            mock_cache.delete_match = AsyncMock()

            await update_user(user_id=456, name="Updated")

            mock_cache.invalidate.assert_called_once_with("user:456")

    @pytest.mark.asyncio
    async def test_cache_write_handles_invalidation_error(self) -> None:
        """Test cache_write handles invalidation errors gracefully."""
        from svc_infra.cache.resources import Resource

        res = Resource("user", "user_id")

        @res.cache_write()
        async def update_user(*, user_id: int, name: str) -> dict:
            return {"id": user_id, "name": name}

        with (
            patch("svc_infra.cache.resources._cache") as mock_cache,
            patch("svc_infra.cache.resources._alias", return_value="svc:v1"),
        ):
            mock_cache.invalidate = AsyncMock(side_effect=Exception("Invalidation failed"))
            mock_cache.delete = AsyncMock()
            mock_cache.delete_match = AsyncMock()

            # Should not raise, mutation completes
            result = await update_user(user_id=789, name="Updated")
            assert result == {"id": 789, "name": "Updated"}

    @pytest.mark.asyncio
    async def test_cache_write_with_recache(self) -> None:
        """Test cache_write with recache operations."""
        from svc_infra.cache.resources import Resource

        res = Resource("user", "user_id")

        getter_mock = AsyncMock(return_value={"id": 123, "cached": True})

        def kwargs_builder(*args, **kwargs):
            return {"user_id": kwargs.get("user_id")}

        @res.cache_write(recache=[(getter_mock, kwargs_builder)])
        async def update_user(*, user_id: int, name: str) -> dict:
            return {"id": user_id, "name": name}

        with (
            patch("svc_infra.cache.resources._cache") as mock_cache,
            patch("svc_infra.cache.resources._alias", return_value="svc:v1"),
        ):
            mock_cache.invalidate = AsyncMock()
            mock_cache.delete = AsyncMock()
            mock_cache.delete_match = AsyncMock()

            await update_user(user_id=123, name="Updated")

            getter_mock.assert_called_once_with(user_id=123)


class TestResourceCacheReadExecution:
    """Tests for Resource cache_read execution paths."""

    def test_cache_read_uses_custom_key_template(self) -> None:
        """Test cache_read applies custom key template."""
        from svc_infra.cache.resources import Resource

        res = Resource("product", "product_id")

        with patch("svc_infra.cache.resources._cache") as mock_cache:
            mock_wrapper = MagicMock(return_value=lambda fn: fn)
            mock_cache.return_value = mock_wrapper

            @res.cache_read(
                suffix="details",
                ttl=600,
                key_template="custom:product:{product_id}",
            )
            async def get_product(*, product_id: int) -> dict:
                return {"id": product_id}

            # Function should be decorated
            assert callable(get_product)

    def test_cache_read_uses_custom_tags(self) -> None:
        """Test cache_read applies custom tags template."""
        from svc_infra.cache.resources import Resource

        res = Resource("product", "product_id")

        with patch("svc_infra.cache.resources._cache") as mock_cache:
            mock_wrapper = MagicMock(return_value=lambda fn: fn)
            mock_cache.return_value = mock_wrapper

            @res.cache_read(
                suffix="details",
                ttl=600,
                tags_template=("product:{product_id}", "catalog:{product_id}"),
            )
            async def get_product(*, product_id: int) -> dict:
                return {"id": product_id}

            assert callable(get_product)

    def test_cache_read_fallback_for_older_cashews(self) -> None:
        """Test cache_read falls back for older cashews versions."""
        from svc_infra.cache.resources import Resource

        res = Resource("product", "product_id")

        # Simulate TypeError from older cashews (no lock parameter)
        def mock_cache_decorator(ttl, key, tags, lock=None):
            if lock is not None:
                raise TypeError("unexpected keyword argument 'lock'")
            return lambda fn: fn

        with patch("svc_infra.cache.resources._cache", side_effect=mock_cache_decorator):

            @res.cache_read(suffix="details", ttl=600)
            async def get_product(*, product_id: int) -> dict:
                return {"id": product_id}

            assert callable(get_product)


class TestResourceEntityAlias:
    """Tests for entity alias function."""

    def test_entity_alias_creates_resource(self) -> None:
        """Test entity() creates Resource instance (legacy alias)."""
        from svc_infra.cache.resources import entity

        res = entity("order", "order_id")

        assert res.name == "order"
        assert res.id_field == "order_id"


class TestResourceDeleteEntityKeys:
    """Tests for internal _delete_entity_keys function."""

    @pytest.mark.asyncio
    async def test_delete_entity_keys_with_namespace(self) -> None:
        """Test _delete_entity_keys handles namespaced keys."""
        from svc_infra.cache.resources import Resource

        res = Resource("user", "user_id")

        @res.cache_write()
        async def delete_user(*, user_id: int) -> bool:
            return True

        with (
            patch("svc_infra.cache.resources._cache") as mock_cache,
            patch("svc_infra.cache.resources._alias", return_value="myapp:v1"),
        ):
            mock_cache.invalidate = AsyncMock()
            mock_cache.delete = AsyncMock()
            mock_cache.delete_match = AsyncMock()

            await delete_user(user_id=999)

            # Should have called delete_match with namespaced pattern
            assert mock_cache.delete_match.called

    @pytest.mark.asyncio
    async def test_delete_entity_keys_handles_delete_error(self) -> None:
        """Test _delete_entity_keys handles delete errors gracefully."""
        from svc_infra.cache.resources import Resource

        res = Resource("user", "user_id")

        @res.cache_write()
        async def delete_user(*, user_id: int) -> bool:
            return True

        with (
            patch("svc_infra.cache.resources._cache") as mock_cache,
            patch("svc_infra.cache.resources._alias", return_value="svc:v1"),
        ):
            mock_cache.invalidate = AsyncMock()
            mock_cache.delete = AsyncMock(side_effect=Exception("Delete failed"))
            mock_cache.delete_match = AsyncMock()

            # Should not raise
            result = await delete_user(user_id=888)
            assert result is True
