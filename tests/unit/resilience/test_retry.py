"""Unit tests for svc_infra.resilience.retry module."""

from __future__ import annotations

import pytest

from svc_infra.resilience.retry import (
    RetryConfig,
    RetryExhaustedError,
    with_retry,
)


class TestRetryExhaustedError:
    """Tests for RetryExhaustedError exception."""

    def test_basic_initialization(self) -> None:
        """Test basic error initialization."""
        error = RetryExhaustedError("All retries failed", attempts=3)

        assert error.attempts == 3
        assert error.last_exception is None
        assert "All retries failed" in str(error)

    def test_with_last_exception(self) -> None:
        """Test initialization with last exception."""
        original = ValueError("Original error")
        error = RetryExhaustedError(
            "Retries exhausted",
            attempts=5,
            last_exception=original,
        )

        assert error.attempts == 5
        assert error.last_exception is original

    def test_repr(self) -> None:
        """Test string representation."""
        error = RetryExhaustedError("msg", attempts=3)

        assert repr(error) == "RetryExhaustedError(attempts=3)"


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
        config = RetryConfig(base_delay=1.0, jitter=0)

        delay = config.calculate_delay(1)

        assert delay == 1.0

    def test_calculate_delay_exponential_growth(self) -> None:
        """Test exponential backoff delay calculation."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=0)

        assert config.calculate_delay(1) == 1.0
        assert config.calculate_delay(2) == 2.0
        assert config.calculate_delay(3) == 4.0
        assert config.calculate_delay(4) == 8.0

    def test_calculate_delay_respects_max(self) -> None:
        """Test delay is capped at max_delay."""
        config = RetryConfig(
            base_delay=1.0,
            max_delay=5.0,
            exponential_base=2.0,
            jitter=0,
        )

        # 4th attempt would be 8.0, but capped at 5.0
        assert config.calculate_delay(4) == 5.0

    def test_calculate_delay_with_jitter(self) -> None:
        """Test delay includes jitter."""
        config = RetryConfig(base_delay=1.0, jitter=0.5)

        delays = [config.calculate_delay(1) for _ in range(20)]

        # With 50% jitter, delays should vary between 0.5 and 1.5
        assert all(0.5 <= d <= 1.5 for d in delays)
        # At least some variation
        assert len(set(delays)) > 1


class TestWithRetry:
    """Tests for with_retry decorator."""

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self) -> None:
        """Test function succeeds on first attempt."""
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
        """Test retries when function fails."""
        call_count = 0

        @with_retry(max_attempts=3, base_delay=0.01)
        async def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet")
            return "success"

        result = await fail_twice()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_raises_retry_exhausted_error(self) -> None:
        """Test raises RetryExhaustedError when all attempts fail."""

        @with_retry(max_attempts=3, base_delay=0.01)
        async def always_fail():
            raise ValueError("Always fails")

        with pytest.raises(RetryExhaustedError) as exc_info:
            await always_fail()

        assert exc_info.value.attempts == 3
        assert isinstance(exc_info.value.last_exception, ValueError)

    @pytest.mark.asyncio
    async def test_only_retries_specified_exceptions(self) -> None:
        """Test only retries on specified exception types."""

        @with_retry(max_attempts=3, base_delay=0.01, retry_on=(ValueError,))
        async def raise_type_error():
            raise TypeError("Wrong type")

        # TypeError should not be retried, should propagate immediately
        with pytest.raises(TypeError):
            await raise_type_error()

    @pytest.mark.asyncio
    async def test_on_retry_callback(self) -> None:
        """Test on_retry callback is called."""
        callback_calls = []

        def on_retry(attempt: int, exc: Exception) -> None:
            callback_calls.append((attempt, str(exc)))

        @with_retry(max_attempts=3, base_delay=0.01, on_retry=on_retry)
        async def fail_then_succeed():
            if len(callback_calls) < 2:
                raise ValueError("Fail")
            return "ok"

        result = await fail_then_succeed()

        assert result == "ok"
        assert len(callback_calls) == 2
        assert callback_calls[0][0] == 1
        assert callback_calls[1][0] == 2

    @pytest.mark.asyncio
    async def test_preserves_function_metadata(self) -> None:
        """Test decorator preserves function name and docstring."""

        @with_retry(max_attempts=3)
        async def my_function():
            """My docstring."""
            pass

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My docstring."

    @pytest.mark.asyncio
    async def test_custom_exponential_base(self) -> None:
        """Test custom exponential base affects delays."""
        call_count = 0

        @with_retry(max_attempts=3, base_delay=0.01, exponential_base=3.0, jitter=0)
        async def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Fail")
            return "ok"

        result = await fail_twice()

        assert result == "ok"
        assert call_count == 3
