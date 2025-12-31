"""Unit tests for svc_infra.resilience.retry module."""

from __future__ import annotations

import pytest

from svc_infra.resilience.retry import (
    RetryConfig,
    RetryExhaustedError,
    retry_sync,
    with_retry,
)


class TestRetryExhaustedError:
    """Tests for RetryExhaustedError exception."""

    def test_basic_creation(self) -> None:
        """Test basic exception creation."""
        exc = RetryExhaustedError("Test error", attempts=3)
        assert exc.attempts == 3
        assert exc.last_exception is None
        assert "Test error" in str(exc)

    def test_with_last_exception(self) -> None:
        """Test exception with last_exception set."""
        cause = ValueError("original error")
        exc = RetryExhaustedError("Retry failed", attempts=5, last_exception=cause)
        assert exc.attempts == 5
        assert exc.last_exception is cause

    def test_repr(self) -> None:
        """Test exception repr."""
        exc = RetryExhaustedError("Test", attempts=3)
        assert "RetryExhaustedError(attempts=3)" in repr(exc)


class TestRetryConfig:
    """Tests for RetryConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay == 0.1
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter == 0.1
        assert config.retry_on == (Exception,)

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=0.5,
            max_delay=30.0,
            exponential_base=3.0,
            jitter=0.2,
            retry_on=(ValueError, TypeError),
        )
        assert config.max_attempts == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.exponential_base == 3.0
        assert config.jitter == 0.2
        assert config.retry_on == (ValueError, TypeError)

    def test_calculate_delay_first_attempt(self) -> None:
        """Test delay calculation for first attempt."""
        config = RetryConfig(base_delay=1.0, jitter=0.0)
        # First attempt: base_delay * (2 ** 0) = 1.0
        assert config.calculate_delay(1) == 1.0

    def test_calculate_delay_exponential(self) -> None:
        """Test exponential delay growth."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=0.0)
        assert config.calculate_delay(1) == 1.0  # 1 * 2^0
        assert config.calculate_delay(2) == 2.0  # 1 * 2^1
        assert config.calculate_delay(3) == 4.0  # 1 * 2^2
        assert config.calculate_delay(4) == 8.0  # 1 * 2^3

    def test_calculate_delay_respects_max(self) -> None:
        """Test that delay is capped at max_delay."""
        config = RetryConfig(base_delay=1.0, max_delay=5.0, jitter=0.0)
        # Without cap: 1 * 2^9 = 512
        assert config.calculate_delay(10) == 5.0

    def test_calculate_delay_with_jitter(self) -> None:
        """Test that jitter adds variance to delay."""
        config = RetryConfig(base_delay=1.0, jitter=0.5)
        delays = [config.calculate_delay(1) for _ in range(20)]
        # With 50% jitter, delays should vary between 0.5 and 1.5
        assert any(d != 1.0 for d in delays)  # Should have some variance
        assert all(0.5 <= d <= 1.5 for d in delays)


class TestWithRetry:
    """Tests for with_retry async decorator."""

    @pytest.mark.asyncio
    async def test_successful_first_attempt(self) -> None:
        """Test that successful function returns immediately."""
        call_count = 0

        @with_retry(max_attempts=3)
        async def succeed():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await succeed()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_failure(self) -> None:
        """Test that function is retried on failure."""
        call_count = 0

        @with_retry(max_attempts=3, base_delay=0.01)
        async def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = await fail_twice()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_attempts(self) -> None:
        """Test that RetryExhaustedError is raised after max attempts."""
        call_count = 0

        @with_retry(max_attempts=3, base_delay=0.01)
        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent error")

        with pytest.raises(RetryExhaustedError) as exc_info:
            await always_fail()

        assert exc_info.value.attempts == 3
        assert isinstance(exc_info.value.last_exception, ValueError)
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_only_retries_on_specified_exceptions(self) -> None:
        """Test that only specified exceptions trigger retry."""
        call_count = 0

        @with_retry(max_attempts=3, retry_on=(ValueError,), base_delay=0.01)
        async def raise_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("Not retryable")

        with pytest.raises(TypeError):
            await raise_type_error()

        # Should only be called once - TypeError is not in retry_on
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_on_retry_callback(self) -> None:
        """Test that on_retry callback is called."""
        retry_calls = []

        def on_retry_cb(attempt: int, exc: Exception):
            retry_calls.append((attempt, str(exc)))

        @with_retry(max_attempts=3, base_delay=0.01, on_retry=on_retry_cb)
        async def fail_twice():
            if len(retry_calls) < 2:
                raise ValueError(f"Attempt {len(retry_calls) + 1}")
            return "success"

        await fail_twice()
        assert len(retry_calls) == 2
        assert retry_calls[0][0] == 1
        assert retry_calls[1][0] == 2


class TestRetrySync:
    """Tests for retry_sync decorator."""

    def test_successful_first_attempt(self) -> None:
        """Test that successful function returns immediately."""
        call_count = 0

        @retry_sync(max_attempts=3)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "success"

        result = succeed()
        assert result == "success"
        assert call_count == 1

    def test_retries_on_failure(self) -> None:
        """Test that function is retried on failure."""
        call_count = 0

        @retry_sync(max_attempts=3, base_delay=0.01)
        def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = fail_twice()
        assert result == "success"
        assert call_count == 3

    def test_raises_after_max_attempts(self) -> None:
        """Test that RetryExhaustedError is raised after max attempts."""
        call_count = 0

        @retry_sync(max_attempts=3, base_delay=0.01)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent error")

        with pytest.raises(RetryExhaustedError) as exc_info:
            always_fail()

        assert exc_info.value.attempts == 3
        assert isinstance(exc_info.value.last_exception, ValueError)
        assert call_count == 3

    def test_only_retries_on_specified_exceptions(self) -> None:
        """Test that only specified exceptions trigger retry."""
        call_count = 0

        @retry_sync(max_attempts=3, retry_on=(ValueError,), base_delay=0.01)
        def raise_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("Not retryable")

        with pytest.raises(TypeError):
            raise_type_error()

        assert call_count == 1

    def test_on_retry_callback(self) -> None:
        """Test that on_retry callback is called."""
        retry_calls = []

        def on_retry_cb(attempt: int, exc: Exception):
            retry_calls.append((attempt, str(exc)))

        @retry_sync(max_attempts=3, base_delay=0.01, on_retry=on_retry_cb)
        def fail_twice():
            if len(retry_calls) < 2:
                raise ValueError(f"Attempt {len(retry_calls) + 1}")
            return "success"

        fail_twice()
        assert len(retry_calls) == 2
