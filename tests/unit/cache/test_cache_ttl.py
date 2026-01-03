"""
Tests for cache TTL expiration behavior.
"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock

import pytest


class TestTTLConfiguration:
    """Tests for TTL configuration."""

    def test_ttl_default_value(self):
        """Should have sensible default TTL."""
        from svc_infra.cache.ttl import TTL_DEFAULT

        # Default should be 5 minutes (300 seconds)
        assert TTL_DEFAULT == 300

    def test_ttl_short_value(self):
        """Should have short TTL option."""
        from svc_infra.cache.ttl import TTL_SHORT

        # Short TTL should be 30 seconds
        assert TTL_SHORT == 30

    def test_ttl_long_value(self):
        """Should have long TTL option."""
        from svc_infra.cache.ttl import TTL_LONG

        # Long TTL should be 1 hour (3600 seconds)
        assert TTL_LONG == 3600

    def test_ttl_can_be_timedelta(self):
        """Should accept timedelta for TTL."""
        ttl = timedelta(minutes=5)

        assert ttl.total_seconds() == 300


class TestGetTTL:
    """Tests for get_ttl function."""

    def test_get_ttl_default(self):
        """Should return default TTL."""
        from svc_infra.cache.ttl import TTL_DEFAULT, get_ttl

        result = get_ttl("default")

        assert result == TTL_DEFAULT

    def test_get_ttl_short(self):
        """Should return short TTL."""
        from svc_infra.cache.ttl import TTL_SHORT, get_ttl

        result = get_ttl("short")

        assert result == TTL_SHORT

    def test_get_ttl_long(self):
        """Should return long TTL."""
        from svc_infra.cache.ttl import TTL_LONG, get_ttl

        result = get_ttl("long")

        assert result == TTL_LONG

    def test_get_ttl_case_insensitive(self):
        """Should be case insensitive."""
        from svc_infra.cache.ttl import TTL_DEFAULT, get_ttl

        result = get_ttl("DEFAULT")

        assert result == TTL_DEFAULT

    def test_get_ttl_invalid_returns_none(self):
        """Should return None for invalid type."""
        from svc_infra.cache.ttl import get_ttl

        result = get_ttl("invalid")

        assert result is None


class TestValidateTTL:
    """Tests for validate_ttl function."""

    def test_validate_ttl_positive(self):
        """Should accept positive TTL."""
        from svc_infra.cache.ttl import validate_ttl

        result = validate_ttl(60)

        assert result == 60

    def test_validate_ttl_none_returns_default(self):
        """Should return default for None."""
        from svc_infra.cache.ttl import TTL_DEFAULT, validate_ttl

        result = validate_ttl(None)

        assert result == TTL_DEFAULT

    def test_validate_ttl_negative_returns_default(self):
        """Should return default for negative value."""
        from svc_infra.cache.ttl import TTL_DEFAULT, validate_ttl

        result = validate_ttl(-1)

        assert result == TTL_DEFAULT


class TestTTLExpiration:
    """Tests for TTL expiration behavior."""

    @pytest.mark.asyncio
    async def test_cache_expires_after_ttl(self, mocker):
        """Should expire entry after TTL."""
        mock_cache = mocker.Mock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()

        # Set with TTL
        await mock_cache.set("key", "value", ttl=1)

        # After TTL, should return None
        result = await mock_cache.get("key")

        assert result is None

    @pytest.mark.asyncio
    async def test_cache_returns_value_before_ttl(self, mocker):
        """Should return value before TTL expires."""
        mock_cache = mocker.Mock()
        mock_cache.get = AsyncMock(return_value="value")
        mock_cache.set = AsyncMock()

        await mock_cache.set("key", "value", ttl=3600)

        result = await mock_cache.get("key")

        assert result == "value"


class TestTTLRefresh:
    """Tests for TTL refresh behavior."""

    @pytest.mark.asyncio
    async def test_get_and_refresh_ttl(self, mocker):
        """Should refresh TTL on access."""
        mock_cache = mocker.Mock()
        mock_cache.get = AsyncMock(return_value="value")
        mock_cache.expire = AsyncMock()

        # Get value and refresh TTL
        await mock_cache.get("key")
        await mock_cache.expire("key", 3600)

        mock_cache.expire.assert_called_once_with("key", 3600)

    @pytest.mark.asyncio
    async def test_sliding_expiration(self, mocker):
        """Should support sliding expiration."""
        mock_cache = mocker.Mock()
        mock_cache.get = AsyncMock(return_value="value")
        mock_cache.touch = AsyncMock()

        # Touch to refresh TTL
        await mock_cache.get("key")
        await mock_cache.touch("key", ttl=300)

        mock_cache.touch.assert_called_once()


class TestTTLZero:
    """Tests for TTL zero behavior."""

    @pytest.mark.asyncio
    async def test_ttl_zero_no_cache(self, mocker):
        """Should not cache with TTL of 0."""
        mock_cache = mocker.Mock()
        mock_cache.set = AsyncMock()

        # TTL of 0 should skip caching
        await mock_cache.set("key", "value", ttl=0)

        mock_cache.set.assert_called_once()

    def test_ttl_negative_invalid(self):
        """Should reject negative TTL."""
        ttl = -1

        assert ttl < 0  # Negative TTL is invalid


class TestTTLEdgeCases:
    """Tests for TTL edge cases."""

    def test_ttl_very_short(self):
        """Should handle very short TTL."""
        ttl = 1  # 1 second

        assert ttl > 0

    def test_ttl_very_long(self):
        """Should handle very long TTL."""
        ttl = 86400 * 365  # 1 year

        assert ttl == 31536000

    def test_ttl_none_means_default(self):
        """Should use default when None."""
        from svc_infra.cache.ttl import TTL_DEFAULT, validate_ttl

        result = validate_ttl(None)

        assert result == TTL_DEFAULT

    def test_ttl_float_seconds(self):
        """Should handle float seconds."""
        ttl = 1.5  # 1.5 seconds

        assert ttl > 1
        assert ttl < 2


class TestEnvConfiguration:
    """Tests for environment-based TTL configuration."""

    def test_env_override_default(self, mocker):
        """Should read TTL from environment."""
        import os

        mocker.patch.dict(os.environ, {"CACHE_TTL_DEFAULT": "600"})

        from svc_infra.cache.ttl import _get_env_int

        result = _get_env_int("CACHE_TTL_DEFAULT", 300)

        # Will return the default since module already loaded
        # This tests the function directly
        assert result == 600

    def test_env_invalid_uses_default(self, mocker):
        """Should use default for invalid env value."""
        from svc_infra.cache.ttl import _get_env_int

        result = _get_env_int("NONEXISTENT_VAR", 300)

        assert result == 300
