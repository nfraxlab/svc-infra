"""Unit tests for svc_infra.health module."""

from __future__ import annotations

import asyncio

import pytest

from svc_infra.health import (
    AggregatedHealthResult,
    HealthCheck,
    HealthCheckResult,
    HealthRegistry,
    HealthStatus,
)


class TestHealthStatus:
    """Tests for HealthStatus enum."""

    def test_status_values(self) -> None:
        """Test all status values."""
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.UNHEALTHY == "unhealthy"
        assert HealthStatus.DEGRADED == "degraded"
        assert HealthStatus.UNKNOWN == "unknown"


class TestHealthCheckResult:
    """Tests for HealthCheckResult dataclass."""

    def test_basic_result(self) -> None:
        """Test basic result creation."""
        result = HealthCheckResult(
            name="database",
            status=HealthStatus.HEALTHY,
            latency_ms=15.5,
        )
        assert result.name == "database"
        assert result.status == HealthStatus.HEALTHY
        assert result.latency_ms == 15.5
        assert result.message is None
        assert result.details is None

    def test_result_with_message(self) -> None:
        """Test result with message."""
        result = HealthCheckResult(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            latency_ms=1000.0,
            message="Connection refused",
        )
        assert result.message == "Connection refused"

    def test_result_with_details(self) -> None:
        """Test result with details."""
        result = HealthCheckResult(
            name="api",
            status=HealthStatus.HEALTHY,
            latency_ms=50.0,
            details={"version": "1.0", "connections": 10},
        )
        assert result.details["version"] == "1.0"

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        result = HealthCheckResult(
            name="test",
            status=HealthStatus.HEALTHY,
            latency_ms=25.567,
            message="All good",
            details={"key": "value"},
        )
        d = result.to_dict()
        assert d["name"] == "test"
        assert d["status"] == "healthy"
        assert d["latency_ms"] == 25.57  # Rounded
        assert d["message"] == "All good"
        assert d["details"] == {"key": "value"}

    def test_to_dict_minimal(self) -> None:
        """Test to_dict with no optional fields."""
        result = HealthCheckResult(
            name="test",
            status=HealthStatus.HEALTHY,
            latency_ms=10.0,
        )
        d = result.to_dict()
        assert "message" not in d
        assert "details" not in d


class TestHealthCheck:
    """Tests for HealthCheck dataclass."""

    def test_default_values(self) -> None:
        """Test default values."""

        async def dummy_check():
            return HealthCheckResult("test", HealthStatus.HEALTHY, 0)

        check = HealthCheck(name="test", check_fn=dummy_check)
        assert check.name == "test"
        assert check.critical is True
        assert check.timeout == 5.0

    def test_custom_values(self) -> None:
        """Test custom values."""

        async def dummy_check():
            return HealthCheckResult("test", HealthStatus.HEALTHY, 0)

        check = HealthCheck(
            name="optional",
            check_fn=dummy_check,
            critical=False,
            timeout=10.0,
        )
        assert check.critical is False
        assert check.timeout == 10.0


class TestHealthRegistry:
    """Tests for HealthRegistry class."""

    def test_empty_registry(self) -> None:
        """Test empty registry."""
        registry = HealthRegistry()
        assert len(registry.checks) == 0

    def test_add_check(self) -> None:
        """Test adding a health check."""
        registry = HealthRegistry()

        async def my_check():
            return HealthCheckResult("db", HealthStatus.HEALTHY, 1.0)

        registry.add("database", my_check)
        assert len(registry.checks) == 1
        assert registry.checks[0].name == "database"

    def test_add_duplicate_raises(self) -> None:
        """Test that adding duplicate name raises."""
        registry = HealthRegistry()

        async def my_check():
            return HealthCheckResult("db", HealthStatus.HEALTHY, 1.0)

        registry.add("database", my_check)

        with pytest.raises(ValueError, match="already registered"):
            registry.add("database", my_check)

    def test_remove_check(self) -> None:
        """Test removing a health check."""
        registry = HealthRegistry()

        async def my_check():
            return HealthCheckResult("db", HealthStatus.HEALTHY, 1.0)

        registry.add("database", my_check)
        result = registry.remove("database")
        assert result is True
        assert len(registry.checks) == 0

    def test_remove_nonexistent(self) -> None:
        """Test removing nonexistent check."""
        registry = HealthRegistry()
        result = registry.remove("nonexistent")
        assert result is False

    def test_clear(self) -> None:
        """Test clearing all checks."""
        registry = HealthRegistry()

        async def my_check():
            return HealthCheckResult("test", HealthStatus.HEALTHY, 1.0)

        registry.add("check1", my_check)
        registry.add("check2", my_check)
        registry.clear()
        assert len(registry.checks) == 0

    @pytest.mark.asyncio
    async def test_check_one(self) -> None:
        """Test running a single check."""
        registry = HealthRegistry()

        async def healthy_check():
            return HealthCheckResult("db", HealthStatus.HEALTHY, 5.0, message="Connected")

        registry.add("database", healthy_check)
        result = await registry.check_one("database")
        assert result.status == HealthStatus.HEALTHY
        assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_check_one_not_found(self) -> None:
        """Test running nonexistent check raises."""
        registry = HealthRegistry()

        with pytest.raises(KeyError, match="not found"):
            await registry.check_one("nonexistent")

    @pytest.mark.asyncio
    async def test_check_one_timeout(self) -> None:
        """Test check timeout handling."""
        registry = HealthRegistry()

        async def slow_check():
            await asyncio.sleep(10)
            return HealthCheckResult("slow", HealthStatus.HEALTHY, 0)

        registry.add("slow", slow_check, timeout=0.1)
        result = await registry.check_one("slow")
        assert result.status == HealthStatus.UNHEALTHY
        assert "timed out" in result.message.lower()

    @pytest.mark.asyncio
    async def test_check_one_exception(self) -> None:
        """Test check exception handling."""
        registry = HealthRegistry()

        async def failing_check():
            raise ConnectionError("Cannot connect")

        registry.add("failing", failing_check)
        result = await registry.check_one("failing")
        assert result.status == HealthStatus.UNHEALTHY
        assert "Cannot connect" in result.message

    @pytest.mark.asyncio
    async def test_check_all_empty(self) -> None:
        """Test check_all with no checks."""
        registry = HealthRegistry()
        result = await registry.check_all()
        assert result.status == HealthStatus.HEALTHY
        assert len(result.checks) == 0

    @pytest.mark.asyncio
    async def test_check_all_healthy(self) -> None:
        """Test check_all with all healthy checks."""
        registry = HealthRegistry()

        async def healthy():
            return HealthCheckResult("test", HealthStatus.HEALTHY, 1.0)

        registry.add("check1", healthy)
        registry.add("check2", healthy)

        result = await registry.check_all()
        assert result.status == HealthStatus.HEALTHY
        assert len(result.checks) == 2

    @pytest.mark.asyncio
    async def test_check_all_critical_failure(self) -> None:
        """Test check_all with critical failure."""
        registry = HealthRegistry()

        async def healthy():
            return HealthCheckResult("test", HealthStatus.HEALTHY, 1.0)

        async def unhealthy():
            return HealthCheckResult("test", HealthStatus.UNHEALTHY, 1.0)

        registry.add("healthy", healthy, critical=True)
        registry.add("unhealthy", unhealthy, critical=True)

        result = await registry.check_all()
        assert result.status == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_check_all_non_critical_failure(self) -> None:
        """Test check_all with only non-critical failure."""
        registry = HealthRegistry()

        async def healthy():
            return HealthCheckResult("test", HealthStatus.HEALTHY, 1.0)

        async def unhealthy():
            return HealthCheckResult("test", HealthStatus.UNHEALTHY, 1.0)

        registry.add("healthy", healthy, critical=True)
        registry.add("unhealthy", unhealthy, critical=False)

        result = await registry.check_all()
        assert result.status == HealthStatus.DEGRADED


class TestAggregatedHealthResult:
    """Tests for AggregatedHealthResult class."""

    def test_basic_creation(self) -> None:
        """Test basic creation."""
        result = AggregatedHealthResult(
            status=HealthStatus.HEALTHY,
            checks=[],
        )
        assert result.status == HealthStatus.HEALTHY
        assert len(result.checks) == 0

    def test_with_checks(self) -> None:
        """Test with check results."""
        checks = [
            HealthCheckResult("db", HealthStatus.HEALTHY, 10.0),
            HealthCheckResult("redis", HealthStatus.HEALTHY, 5.0),
        ]
        result = AggregatedHealthResult(
            status=HealthStatus.HEALTHY,
            checks=checks,
        )
        assert len(result.checks) == 2

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        result = AggregatedHealthResult(
            status=HealthStatus.HEALTHY,
            checks=[HealthCheckResult("db", HealthStatus.HEALTHY, 10.0)],
            message="All systems go",
        )
        d = result.to_dict()
        assert d["status"] == "healthy"
        assert len(d["checks"]) == 1
        assert d["message"] == "All systems go"
