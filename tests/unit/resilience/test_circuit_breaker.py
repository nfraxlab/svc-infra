"""Unit tests for svc_infra.resilience.circuit_breaker module."""

from __future__ import annotations

import asyncio

import pytest

from svc_infra.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitBreakerStats,
    CircuitState,
)


class TestCircuitState:
    """Tests for CircuitState enum."""

    def test_closed_state(self) -> None:
        """Test CLOSED state value."""
        assert CircuitState.CLOSED.value == "closed"

    def test_open_state(self) -> None:
        """Test OPEN state value."""
        assert CircuitState.OPEN.value == "open"

    def test_half_open_state(self) -> None:
        """Test HALF_OPEN state value."""
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestCircuitBreakerError:
    """Tests for CircuitBreakerError exception."""

    def test_basic_creation(self) -> None:
        """Test basic exception creation."""
        exc = CircuitBreakerError("test-breaker", state=CircuitState.OPEN)
        assert exc.name == "test-breaker"
        assert exc.state == CircuitState.OPEN
        assert exc.remaining_timeout is None
        assert "test-breaker" in str(exc)
        assert "open" in str(exc)

    def test_with_remaining_timeout(self) -> None:
        """Test exception with remaining timeout."""
        exc = CircuitBreakerError(
            "test-breaker",
            state=CircuitState.OPEN,
            remaining_timeout=15.5,
        )
        assert exc.remaining_timeout == 15.5
        assert "15.5s" in str(exc)


class TestCircuitBreakerStats:
    """Tests for CircuitBreakerStats dataclass."""

    def test_default_values(self) -> None:
        """Test default stats are zero."""
        stats = CircuitBreakerStats()
        assert stats.total_calls == 0
        assert stats.successful_calls == 0
        assert stats.failed_calls == 0
        assert stats.rejected_calls == 0
        assert stats.state_changes == 0

    def test_custom_values(self) -> None:
        """Test custom stats values."""
        stats = CircuitBreakerStats(
            total_calls=100,
            successful_calls=90,
            failed_calls=8,
            rejected_calls=2,
            state_changes=3,
        )
        assert stats.total_calls == 100
        assert stats.successful_calls == 90


class TestCircuitBreaker:
    """Tests for CircuitBreaker class."""

    def test_default_initialization(self) -> None:
        """Test default circuit breaker initialization."""
        breaker = CircuitBreaker()
        assert breaker.name == "default"
        assert breaker.failure_threshold == 5
        assert breaker.recovery_timeout == 30.0
        assert breaker.state == CircuitState.CLOSED

    def test_custom_initialization(self) -> None:
        """Test custom circuit breaker initialization."""
        breaker = CircuitBreaker(
            name="api-breaker",
            failure_threshold=3,
            recovery_timeout=10.0,
            half_open_max_calls=2,
            success_threshold=1,
        )
        assert breaker.name == "api-breaker"
        assert breaker.failure_threshold == 3
        assert breaker.recovery_timeout == 10.0

    @pytest.mark.asyncio
    async def test_successful_call_stays_closed(self) -> None:
        """Test that successful calls keep circuit closed."""
        breaker = CircuitBreaker(failure_threshold=3)

        async with breaker:
            pass  # Successful call

        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.successful_calls == 1
        assert breaker.stats.total_calls == 1

    @pytest.mark.asyncio
    async def test_failures_open_circuit(self) -> None:
        """Test that enough failures open the circuit."""
        breaker = CircuitBreaker(failure_threshold=3)

        for i in range(3):
            with pytest.raises(ValueError):
                async with breaker:
                    raise ValueError("Error")

        assert breaker.state == CircuitState.OPEN
        assert breaker.stats.failed_calls == 3

    @pytest.mark.asyncio
    async def test_open_circuit_rejects_calls(self) -> None:
        """Test that open circuit rejects new calls."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=100.0)

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                async with breaker:
                    raise ValueError("Error")

        assert breaker.state == CircuitState.OPEN

        # New calls should be rejected
        with pytest.raises(CircuitBreakerError) as exc_info:
            async with breaker:
                pass

        assert exc_info.value.state == CircuitState.OPEN
        assert breaker.stats.rejected_calls == 1

    @pytest.mark.asyncio
    async def test_half_open_after_timeout(self) -> None:
        """Test transition to half-open after recovery timeout."""
        breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.05,  # 50ms
        )

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                async with breaker:
                    raise ValueError("Error")

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.1)

        # Next call should transition to half-open
        async with breaker:
            pass  # Success in half-open

        # Should be half-open or closed now
        assert breaker.state in (CircuitState.HALF_OPEN, CircuitState.CLOSED)

    @pytest.mark.asyncio
    async def test_half_open_success_closes_circuit(self) -> None:
        """Test that successes in half-open close the circuit."""
        breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.01,
            success_threshold=2,
        )

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                async with breaker:
                    raise ValueError("Error")

        # Wait for recovery timeout
        await asyncio.sleep(0.02)

        # Successful calls in half-open
        for _ in range(2):
            async with breaker:
                pass

        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens_circuit(self) -> None:
        """Test that failure in half-open reopens circuit."""
        breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.01,
        )

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                async with breaker:
                    raise ValueError("Error")

        # Wait for recovery timeout
        await asyncio.sleep(0.02)

        # Failure in half-open
        with pytest.raises(ValueError):
            async with breaker:
                raise ValueError("Still broken")

        assert breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_protect_decorator(self) -> None:
        """Test the protect decorator."""
        breaker = CircuitBreaker(failure_threshold=3)
        call_count = 0

        @breaker.protect
        async def protected_fn():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await protected_fn()
        assert result == "success"
        assert call_count == 1
        assert breaker.stats.successful_calls == 1

    @pytest.mark.asyncio
    async def test_protect_decorator_with_failure(self) -> None:
        """Test the protect decorator with failures."""
        breaker = CircuitBreaker(failure_threshold=2)

        @breaker.protect
        async def always_fail():
            raise ValueError("Always fails")

        for _ in range(2):
            with pytest.raises(ValueError):
                await always_fail()

        assert breaker.state == CircuitState.OPEN

        with pytest.raises(CircuitBreakerError):
            await always_fail()

    def test_reset(self) -> None:
        """Test manual reset of circuit breaker."""
        breaker = CircuitBreaker()
        breaker._state = CircuitState.OPEN
        breaker._failure_count = 5

        breaker.reset()

        assert breaker.state == CircuitState.CLOSED
        assert breaker._failure_count == 0

    @pytest.mark.asyncio
    async def test_specific_failure_exceptions(self) -> None:
        """Test that only specified exceptions count as failures."""
        breaker = CircuitBreaker(
            failure_threshold=2,
            failure_exceptions=(ValueError,),
        )

        # TypeError should not count as failure
        with pytest.raises(TypeError):
            async with breaker:
                raise TypeError("Not a failure")

        assert breaker.stats.failed_calls == 0
        assert breaker.state == CircuitState.CLOSED

        # ValueError should count as failure
        for _ in range(2):
            with pytest.raises(ValueError):
                async with breaker:
                    raise ValueError("This is a failure")

        assert breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_stats_tracking(self) -> None:
        """Test that stats are tracked correctly."""
        breaker = CircuitBreaker(failure_threshold=5)

        # 3 successful calls
        for _ in range(3):
            async with breaker:
                pass

        # 2 failed calls
        for _ in range(2):
            with pytest.raises(ValueError):
                async with breaker:
                    raise ValueError("Error")

        stats = breaker.stats
        assert stats.total_calls == 5
        assert stats.successful_calls == 3
        assert stats.failed_calls == 2
        assert stats.rejected_calls == 0
