"""Unit tests for svc_infra.cache.tags module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from svc_infra.cache.tags import invalidate_tags


class TestInvalidateTags:
    """Tests for invalidate_tags function."""

    @pytest.mark.asyncio
    async def test_returns_zero_for_empty_tags(self) -> None:
        """Test returns 0 when no tags provided."""
        result = await invalidate_tags()

        assert result == 0

    @pytest.mark.asyncio
    @patch("svc_infra.cache.tags._cache")
    async def test_uses_delete_tags_when_available(self, mock_cache: MagicMock) -> None:
        """Test uses delete_tags method when available."""
        mock_cache.delete_tags = AsyncMock()

        result = await invalidate_tags("tag1", "tag2", "tag3")

        mock_cache.delete_tags.assert_called_once_with("tag1", "tag2", "tag3")
        assert result == 3

    @pytest.mark.asyncio
    @patch("svc_infra.cache.tags._cache")
    async def test_deduplicates_tags(self, mock_cache: MagicMock) -> None:
        """Test deduplicates tags before invalidation."""
        mock_cache.delete_tags = AsyncMock()

        result = await invalidate_tags("tag1", "tag2", "tag1", "tag3", "tag2")

        # Should only have 3 unique tags
        mock_cache.delete_tags.assert_called_once()
        call_args = mock_cache.delete_tags.call_args[0]
        assert len(call_args) == 3
        assert result == 3

    @pytest.mark.asyncio
    @patch("svc_infra.cache.tags._cache")
    async def test_preserves_tag_order(self, mock_cache: MagicMock) -> None:
        """Test preserves order while deduplicating."""
        mock_cache.delete_tags = AsyncMock()

        await invalidate_tags("c", "a", "b", "a", "c")

        call_args = mock_cache.delete_tags.call_args[0]
        assert call_args == ("c", "a", "b")

    @pytest.mark.asyncio
    @patch("svc_infra.cache.tags._cache")
    async def test_fallback_to_delete_tag_method(self, mock_cache: MagicMock) -> None:
        """Test falls back to _delete_tag when delete_tags fails."""
        # Remove delete_tags to simulate it not existing
        del mock_cache.delete_tags
        mock_cache._delete_tag = AsyncMock()

        result = await invalidate_tags("tag1", "tag2")

        assert mock_cache._delete_tag.call_count == 2
        assert result == 2

    @pytest.mark.asyncio
    @patch("svc_infra.cache.tags._cache")
    async def test_handles_delete_tags_exception(self, mock_cache: MagicMock) -> None:
        """Test handles exception from delete_tags gracefully."""
        mock_cache.delete_tags = AsyncMock(side_effect=Exception("Cache error"))
        mock_cache._delete_tag = AsyncMock()

        result = await invalidate_tags("tag1", "tag2")

        # Should fall back to _delete_tag
        assert mock_cache._delete_tag.call_count == 2
        assert result == 2

    @pytest.mark.asyncio
    @patch("svc_infra.cache.tags._cache")
    async def test_handles_delete_tag_exception(self, mock_cache: MagicMock) -> None:
        """Test handles exception from _delete_tag gracefully."""
        del mock_cache.delete_tags
        mock_cache._delete_tag = AsyncMock(side_effect=Exception("Tag error"))

        result = await invalidate_tags("tag1", "tag2")

        # Should catch exceptions and return 0
        assert result == 0

    @pytest.mark.asyncio
    @patch("svc_infra.cache.tags._cache")
    async def test_single_tag(self, mock_cache: MagicMock) -> None:
        """Test with a single tag."""
        mock_cache.delete_tags = AsyncMock()

        result = await invalidate_tags("single-tag")

        mock_cache.delete_tags.assert_called_once_with("single-tag")
        assert result == 1
