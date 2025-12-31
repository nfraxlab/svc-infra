"""Tests for svc_infra.cache.backend module."""

from __future__ import annotations

from svc_infra.cache import backend as cache_backend


class TestAlias:
    """Tests for alias function."""

    def test_returns_formatted_alias(self) -> None:
        """Returns formatted alias string."""
        # Save original values
        original_prefix = cache_backend._current_prefix
        original_version = cache_backend._current_version
        try:
            cache_backend._current_prefix = "test"
            cache_backend._current_version = "v1"
            result = cache_backend.alias()
            assert result == "test:v1"
        finally:
            cache_backend._current_prefix = original_prefix
            cache_backend._current_version = original_version

    def test_uses_defaults(self) -> None:
        """Uses default values when not configured."""
        # Save original values
        original_prefix = cache_backend._current_prefix
        original_version = cache_backend._current_version
        try:
            cache_backend._current_prefix = cache_backend.DEFAULT_PREFIX
            cache_backend._current_version = cache_backend.DEFAULT_VERSION
            result = cache_backend.alias()
            assert result == f"{cache_backend.DEFAULT_PREFIX}:{cache_backend.DEFAULT_VERSION}"
        finally:
            cache_backend._current_prefix = original_prefix
            cache_backend._current_version = original_version


class TestFullPrefix:
    """Tests for _full_prefix function."""

    def test_returns_formatted_prefix_with_colon(self) -> None:
        """Returns formatted prefix with trailing colon."""
        original_prefix = cache_backend._current_prefix
        original_version = cache_backend._current_version
        try:
            cache_backend._current_prefix = "myapp"
            cache_backend._current_version = "v2"
            result = cache_backend._full_prefix()
            assert result == "myapp:v2:"
        finally:
            cache_backend._current_prefix = original_prefix
            cache_backend._current_version = original_version


class TestSetupCache:
    """Tests for setup_cache function."""

    def test_updates_prefix_global_variable(self) -> None:
        """Updates global prefix variable directly."""
        original = cache_backend._current_prefix
        try:
            cache_backend._current_prefix = "testprefix"
            assert cache_backend._current_prefix == "testprefix"
            assert cache_backend.alias().startswith("testprefix:")
        finally:
            cache_backend._current_prefix = original

    def test_updates_version_global_variable(self) -> None:
        """Updates global version variable directly."""
        original = cache_backend._current_version
        try:
            cache_backend._current_version = "v99"
            assert cache_backend._current_version == "v99"
            assert cache_backend.alias().endswith(":v99")
        finally:
            cache_backend._current_version = original

    def test_setup_cache_exists(self) -> None:
        """setup_cache function exists and is callable."""
        assert callable(cache_backend.setup_cache)


class TestGetCache:
    """Tests for get_cache function."""

    def test_returns_cache_instance(self) -> None:
        """Returns the cache instance."""
        result = cache_backend.get_cache()
        assert result is not None

    def test_returns_same_instance(self) -> None:
        """Returns the same cache instance."""
        result1 = cache_backend.get_cache()
        result2 = cache_backend.get_cache()
        assert result1 is result2


class TestConstants:
    """Tests for module constants."""

    def test_default_prefix(self) -> None:
        """Default prefix is set."""
        assert cache_backend.DEFAULT_PREFIX == "svc"

    def test_default_version(self) -> None:
        """Default version is set."""
        assert cache_backend.DEFAULT_VERSION == "v1"

    def test_default_readiness_timeout(self) -> None:
        """Default readiness timeout is set."""
        assert cache_backend.DEFAULT_READINESS_TIMEOUT == 5.0

    def test_probe_key_suffix(self) -> None:
        """Probe key suffix is set."""
        assert cache_backend.PROBE_KEY_SUFFIX == "__probe__"

    def test_probe_value(self) -> None:
        """Probe value is set."""
        assert cache_backend.PROBE_VALUE == "ok"

    def test_probe_expire_seconds(self) -> None:
        """Probe expire seconds is set."""
        assert cache_backend.PROBE_EXPIRE_SECONDS == 3


class TestWaitReady:
    """Tests for wait_ready function."""

    def test_wait_ready_exists(self) -> None:
        """wait_ready function exists and is callable."""
        assert callable(cache_backend.wait_ready)

    def test_wait_ready_is_coroutine_function(self) -> None:
        """wait_ready is an async function."""
        import asyncio

        assert asyncio.iscoroutinefunction(cache_backend.wait_ready)


class TestShutdownCache:
    """Tests for shutdown_cache function."""

    def test_shutdown_cache_exists(self) -> None:
        """shutdown_cache function exists and is callable."""
        assert callable(cache_backend.shutdown_cache)

    def test_shutdown_cache_is_coroutine_function(self) -> None:
        """shutdown_cache is an async function."""
        import asyncio

        assert asyncio.iscoroutinefunction(cache_backend.shutdown_cache)
