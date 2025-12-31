"""Tests for svc_infra.resilience.circuit_breaker module."""

from __future__ import annotations

import asyncio
import time

import pytest

from svc_infra.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitBreakerStats,
    CircuitState,
)


class TestCircuitState:
    """Tests for CircuitState enum."""

    def test_closed_state_value(self) -> None:
        """Closed state has correct value."""
        assert CircuitState.CLOSED.value == "closed"

    def test_open_state_value(self) -> None:
        """Open state has correct value."""
        assert CircuitState.OPEN.value == "open"

    def test_half_open_state_value(self) -> None:
        """Half-open state has correct value."""
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestCircuitBreakerError:
    """Tests for CircuitBreakerError exception."""

    def test_error_with_open_state(self) -> None:
        """Error message contains state and name."""
        err = CircuitBreakerError("test-breaker", state=CircuitState.OPEN)
        assert err.name == "test-breaker"
        assert err.state == CircuitState.OPEN
        assert err.remaining_timeout is None
        assert "test-breaker" in str(err)
        assert "open" in str(err)

    def test_error_with_remaining_timeout(self) -> None:
        """Error message includes retry time when provided."""
        err = CircuitBreakerError(
            "test-breaker",
            state=CircuitState.OPEN,
            remaining_timeout=15.5,
        )
        assert err.remaining_timeout == 15.5
        assert "15.5s" in str(err)

    def test_error_with_half_open_state(self) -> None:
        """Error works with half-open state."""
        err = CircuitBreakerError("api-breaker", state=CircuitState.HALF_OPEN)
        assert err.state == CircuitState.HALF_OPEN
        assert "half_open" in str(err)


class TestCircuitBreakerStats:
    """Tests for CircuitBreakerStats dataclass."""

    def test_default_stats(self) -> None:
        """Default stats are all zero."""
        stats = CircuitBreakerStats()
        assert stats.total_calls == 0
        assert stats.successful_calls == 0
        assert stats.failed_calls == 0
        assert stats.rejected_calls == 0
        assert stats.state_changes == 0

    def test_stats_with_values(self) -> None:
        """Stats can be initialized with values."""
        stats = CircuitBreakerStats(
            total_calls=100,
            successful_calls=90,
            failed_calls=10,
            rejected_calls=5,
            state_changes=3,
        )
        assert stats.total_calls == 100
        assert stats.successful_calls == 90
        assert stats.failed_calls == 10
        assert stats.rejected_calls == 5
        assert stats.state_changes == 3


class TestCircuitBreakerInit:
    """Tests for CircuitBreaker initialization."""

    def test_default_values(self) -> None:
        """Default parameters are set correctly."""
        breaker = CircuitBreaker()
        assert breaker.name == "default"
        assert breaker.failure_threshold == 5
        assert breaker.recovery_timeout == 30.0
        assert breaker.half_open_max_calls == 3
        assert breaker.success_threshold == 2
        assert breaker.failure_exceptions == (Exception,)

    def test_custom_values(self) -> None:
        """Custom parameters are set correctly."""
        breaker = CircuitBreaker(
            name="custom-breaker",
            failure_threshold=10,
            recovery_timeout=60.0,
            half_open_max_calls=5,
            success_threshold=3,
            failure_exceptions=(ValueError, TypeError),
        )
        assert breaker.name == "custom-breaker"
        assert breaker.failure_threshold == 10
        assert breaker.recovery_timeout == 60.0
        assert breaker.half_open_max_calls == 5
        assert breaker.success_threshold == 3
        assert breaker.failure_exceptions == (ValueError, TypeError)

    def test_initial_state_is_closed(self) -> None:
        """Circuit starts in closed state."""
        breaker = CircuitBreaker()
        assert breaker.state == CircuitState.CLOSED

    def test_initial_stats(self) -> None:
        """Stats are initially zero."""
        breaker = CircuitBreaker()
        stats = breaker.stats
        assert stats.total_calls == 0
        assert stats.successful_calls == 0


class TestCircuitBreakerClosedState:
    """Tests for circuit breaker in closed state."""

    @pytest.mark.asyncio
    async def test_successful_call_in_closed_state(self) -> None:
        """Successful calls pass through in closed state."""
        breaker = CircuitBreaker()

        async with breaker:
            pass

        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.successful_calls == 1
        assert breaker.stats.total_calls == 1

    @pytest.mark.asyncio
    async def test_multiple_successful_calls(self) -> None:
        """Multiple successful calls keep circuit closed."""
        breaker = CircuitBreaker()

        for _ in range(10):
            async with breaker:
                pass

        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.successful_calls == 10

    @pytest.mark.asyncio
    async def test_failures_below_threshold(self) -> None:
        """Failures below threshold keep circuit closed."""
        breaker = CircuitBreaker(failure_threshold=5)

        for _ in range(4):
            with pytest.raises(ValueError):
                async with breaker:
                    raise ValueError("test error")

        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.failed_calls == 4

    @pytest.mark.asyncio
    async def test_failure_at_threshold_opens_circuit(self) -> None:
        """Reaching failure threshold opens the circuit."""
        breaker = CircuitBreaker(failure_threshold=3)

        for _ in range(3):
            with pytest.raises(ValueError):
                async with breaker:
                    raise ValueError("test error")

        assert breaker.state == CircuitState.OPEN
        assert breaker.stats.failed_calls == 3
        assert breaker.stats.state_changes == 1

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self) -> None:
        """Successful call resets failure count."""
        breaker = CircuitBreaker(failure_threshold=5)

        # 4 failures
        for _ in range(4):
            with pytest.raises(ValueError):
                async with breaker:
                    raise ValueError("test")

        # 1 success resets count
        async with breaker:
            pass

        # 4 more failures (total 4, not 8)
        for _ in range(4):
            with pytest.raises(ValueError):
                async with breaker:
                    raise ValueError("test")

        # Should still be closed (only 4 failures since reset)
        assert breaker.state == CircuitState.CLOSED


class TestCircuitBreakerOpenState:
    """Tests for circuit breaker in open state."""

    @pytest.mark.asyncio
    async def test_calls_rejected_when_open(self) -> None:
        """Calls are rejected when circuit is open."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=60.0)

        # Trip the breaker
        with pytest.raises(ValueError):
            async with breaker:
                raise ValueError("trip")

        assert breaker.state == CircuitState.OPEN

        # Next call should be rejected
        with pytest.raises(CircuitBreakerError) as exc_info:
            async with breaker:
                pass

        assert exc_info.value.state == CircuitState.OPEN
        assert breaker.stats.rejected_calls == 1

    @pytest.mark.asyncio
    async def test_rejected_call_includes_remaining_timeout(self) -> None:
        """Rejected call error includes remaining timeout."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=30.0)

        with pytest.raises(ValueError):
            async with breaker:
                raise ValueError("trip")

        with pytest.raises(CircuitBreakerError) as exc_info:
            async with breaker:
                pass

        assert exc_info.value.remaining_timeout is not None
        assert exc_info.value.remaining_timeout > 0
        assert exc_info.value.remaining_timeout <= 30.0


class TestCircuitBreakerHalfOpenState:
    """Tests for circuit breaker in half-open state."""

    @pytest.mark.asyncio
    async def test_transitions_to_half_open_after_timeout(self) -> None:
        """Circuit transitions to half-open after recovery timeout."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)

        # Trip the breaker
        with pytest.raises(ValueError):
            async with breaker:
                raise ValueError("trip")

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.02)

        # Next call should be allowed (half-open)
        async with breaker:
            pass

        # State change happened during the call
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_success_in_half_open_closes_circuit(self) -> None:
        """Successful calls in half-open close the circuit."""
        breaker = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=0.01,
            success_threshold=2,
        )

        # Trip the breaker
        with pytest.raises(ValueError):
            async with breaker:
                raise ValueError("trip")

        await asyncio.sleep(0.02)

        # 2 successful calls should close circuit
        async with breaker:
            pass
        async with breaker:
            pass

        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failure_in_half_open_reopens_circuit(self) -> None:
        """Failure in half-open state reopens the circuit."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)

        # Trip the breaker
        with pytest.raises(ValueError):
            async with breaker:
                raise ValueError("trip")

        await asyncio.sleep(0.02)

        # Failure in half-open reopens
        with pytest.raises(ValueError):
            async with breaker:
                raise ValueError("still failing")

        assert breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_half_open_max_calls_limit(self) -> None:
        """Half-open state limits concurrent calls."""
        breaker = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=0.01,
            half_open_max_calls=2,
            success_threshold=3,  # Higher than max calls
        )

        # Trip the breaker
        with pytest.raises(ValueError):
            async with breaker:
                raise ValueError("trip")

        await asyncio.sleep(0.02)

        # First 2 calls should succeed
        async with breaker:
            pass
        async with breaker:
            pass

        # Third call should be rejected
        with pytest.raises(CircuitBreakerError) as exc_info:
            async with breaker:
                pass

        assert exc_info.value.state == CircuitState.HALF_OPEN


class TestCircuitBreakerProtectDecorator:
    """Tests for the protect decorator."""

    @pytest.mark.asyncio
    async def test_protect_successful_call(self) -> None:
        """Protect decorator allows successful calls."""
        breaker = CircuitBreaker()

        @breaker.protect
        async def my_func() -> str:
            return "success"

        result = await my_func()
        assert result == "success"
        assert breaker.stats.successful_calls == 1

    @pytest.mark.asyncio
    async def test_protect_failed_call(self) -> None:
        """Protect decorator records failures."""
        breaker = CircuitBreaker(failure_threshold=2)

        @breaker.protect
        async def failing_func() -> str:
            raise RuntimeError("failure")

        with pytest.raises(RuntimeError):
            await failing_func()

        assert breaker.stats.failed_calls == 1
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_protect_preserves_function_metadata(self) -> None:
        """Protect decorator preserves function name and docstring."""
        breaker = CircuitBreaker()

        @breaker.protect
        async def documented_func() -> str:
            """A documented function."""
            return "result"

        assert documented_func.__name__ == "documented_func"
        assert "documented" in documented_func.__doc__

    @pytest.mark.asyncio
    async def test_protect_with_arguments(self) -> None:
        """Protect decorator passes arguments correctly."""
        breaker = CircuitBreaker()

        @breaker.protect
        async def add(a: int, b: int) -> int:
            return a + b

        result = await add(3, 4)
        assert result == 7


class TestCircuitBreakerReset:
    """Tests for circuit breaker reset."""

    @pytest.mark.asyncio
    async def test_reset_from_open_state(self) -> None:
        """Reset closes the circuit from open state."""
        breaker = CircuitBreaker(failure_threshold=1)

        # Trip the breaker
        with pytest.raises(ValueError):
            async with breaker:
                raise ValueError("trip")

        assert breaker.state == CircuitState.OPEN

        # Reset the breaker
        breaker.reset()

        assert breaker.state == CircuitState.CLOSED

        # Calls should now be allowed
        async with breaker:
            pass

        assert breaker.stats.successful_calls == 1

    def test_reset_clears_failure_count(self) -> None:
        """Reset clears internal failure counters."""
        breaker = CircuitBreaker()
        breaker._failure_count = 10
        breaker._success_count = 5
        breaker._half_open_calls = 3
        breaker._last_failure_time = 12345.0

        breaker.reset()

        assert breaker._failure_count == 0
        assert breaker._success_count == 0
        assert breaker._half_open_calls == 0
        assert breaker._last_failure_time is None


class TestCircuitBreakerFailureExceptions:
    """Tests for custom failure exceptions."""

    @pytest.mark.asyncio
    async def test_only_specified_exceptions_count_as_failures(self) -> None:
        """Only specified exception types count as failures."""
        breaker = CircuitBreaker(
            failure_threshold=1,
            failure_exceptions=(ValueError,),
        )

        # ValueError should count as failure
        with pytest.raises(ValueError):
            async with breaker:
                raise ValueError("counted")

        assert breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_non_specified_exceptions_dont_count(self) -> None:
        """Non-specified exceptions don't count as failures."""
        breaker = CircuitBreaker(
            failure_threshold=1,
            failure_exceptions=(ValueError,),
        )

        # TypeError should not count as failure
        with pytest.raises(TypeError):
            async with breaker:
                raise TypeError("not counted")

        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.failed_calls == 0


class TestCircuitBreakerHelperMethods:
    """Tests for helper methods."""

    def test_should_try_half_open_when_closed(self) -> None:
        """Should not try half-open when closed."""
        breaker = CircuitBreaker()
        assert breaker._should_try_half_open() is False

    def test_should_try_half_open_when_no_failure_time(self) -> None:
        """Should try half-open when no failure time recorded."""
        breaker = CircuitBreaker()
        breaker._state = CircuitState.OPEN
        breaker._last_failure_time = None
        assert breaker._should_try_half_open() is True

    def test_should_try_half_open_after_timeout(self) -> None:
        """Should try half-open after recovery timeout."""
        breaker = CircuitBreaker(recovery_timeout=0.01)
        breaker._state = CircuitState.OPEN
        breaker._last_failure_time = time.monotonic() - 0.02
        assert breaker._should_try_half_open() is True

    def test_remaining_timeout_when_closed(self) -> None:
        """Remaining timeout is None when closed."""
        breaker = CircuitBreaker()
        assert breaker._remaining_timeout() is None

    def test_remaining_timeout_when_no_failure_time(self) -> None:
        """Remaining timeout is 0 when no failure time."""
        breaker = CircuitBreaker()
        breaker._state = CircuitState.OPEN
        breaker._last_failure_time = None
        assert breaker._remaining_timeout() == 0.0

    def test_remaining_timeout_calculation(self) -> None:
        """Remaining timeout calculates correctly."""
        breaker = CircuitBreaker(recovery_timeout=30.0)
        breaker._state = CircuitState.OPEN
        breaker._last_failure_time = time.monotonic() - 10.0
        remaining = breaker._remaining_timeout()
        assert remaining is not None
        assert 19.0 <= remaining <= 20.5  # Allow for timing variance

    def test_remaining_timeout_never_negative(self) -> None:
        """Remaining timeout is never negative."""
        breaker = CircuitBreaker(recovery_timeout=10.0)
        breaker._state = CircuitState.OPEN
        breaker._last_failure_time = time.monotonic() - 100.0  # Way past
        remaining = breaker._remaining_timeout()
        assert remaining == 0.0
