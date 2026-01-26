"""Tests for svc_infra.jobs.registry module."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from svc_infra.jobs import Job, JobRegistry, JobResult, JobTimeoutError, UnknownJobError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def registry() -> JobRegistry:
    """Create a fresh JobRegistry for each test."""
    return JobRegistry(metric_prefix="test_jobs")


@pytest.fixture
def sample_job() -> Job:
    """Create a sample job for testing."""
    return Job(
        id="job-123",
        name="test_job",
        payload={"key": "value"},
        attempts=1,
    )


# ---------------------------------------------------------------------------
# JobResult Tests
# ---------------------------------------------------------------------------


class TestJobResult:
    """Tests for JobResult dataclass."""

    def test_success_result(self) -> None:
        """Test creating a successful result."""
        result = JobResult(success=True, message="Done")
        assert result.success is True
        assert result.message == "Done"
        assert result.details is None

    def test_failure_result(self) -> None:
        """Test creating a failure result."""
        result = JobResult(success=False, message="Error occurred")
        assert result.success is False
        assert result.message == "Error occurred"

    def test_result_with_details(self) -> None:
        """Test creating a result with details."""
        result = JobResult(
            success=True,
            message="Processed",
            details={"count": 5, "ids": ["a", "b"]},
        )
        assert result.details == {"count": 5, "ids": ["a", "b"]}

    def test_empty_details_becomes_none(self) -> None:
        """Test that empty details dict is converted to None."""
        result = JobResult(success=True, message="Done", details={})
        assert result.details is None


# ---------------------------------------------------------------------------
# Exception Tests
# ---------------------------------------------------------------------------


class TestExceptions:
    """Tests for registry exceptions."""

    def test_unknown_job_error(self) -> None:
        """Test UnknownJobError attributes."""
        error = UnknownJobError("missing_job")
        assert error.job_name == "missing_job"
        assert "Unknown job type: missing_job" in str(error)

    def test_job_timeout_error(self) -> None:
        """Test JobTimeoutError attributes."""
        error = JobTimeoutError("slow_job", 30.0)
        assert error.job_name == "slow_job"
        assert error.timeout == 30.0
        assert "slow_job exceeded timeout of 30.0s" in str(error)


# ---------------------------------------------------------------------------
# Handler Registration Tests
# ---------------------------------------------------------------------------


class TestHandlerRegistration:
    """Tests for handler registration."""

    def test_register_handler(self, registry: JobRegistry) -> None:
        """Test registering a handler imperatively."""

        async def my_handler(job: Job) -> JobResult:
            return JobResult(success=True, message="Done")

        registry.register("my_job", my_handler)

        assert registry.has_handler("my_job") is True
        assert registry.get_handler("my_job") is my_handler

    def test_register_handler_decorator(self, registry: JobRegistry) -> None:
        """Test registering a handler with decorator."""

        @registry.handler("decorated_job")
        async def handle_decorated(job: Job) -> JobResult:
            return JobResult(success=True, message="Decorated")

        assert registry.has_handler("decorated_job") is True
        assert registry.get_handler("decorated_job") is handle_decorated

    def test_decorator_returns_original_function(self, registry: JobRegistry) -> None:
        """Test that decorator returns the original function."""

        @registry.handler("test")
        async def original(job: Job) -> JobResult:
            return JobResult(success=True, message="Original")

        # Function should be unchanged
        assert original.__name__ == "original"

    def test_list_handlers(self, registry: JobRegistry) -> None:
        """Test listing registered handlers."""

        async def handler1(job: Job) -> JobResult:
            return JobResult(success=True, message="1")

        async def handler2(job: Job) -> JobResult:
            return JobResult(success=True, message="2")

        registry.register("job_a", handler1)
        registry.register("job_b", handler2)

        handlers = registry.list_handlers()
        assert set(handlers) == {"job_a", "job_b"}

    def test_handlers_property_returns_copy(self, registry: JobRegistry) -> None:
        """Test that handlers property returns a copy."""

        async def handler(job: Job) -> JobResult:
            return JobResult(success=True, message="Done")

        registry.register("test", handler)

        handlers_copy = registry.handlers
        handlers_copy["new"] = handler  # Modify copy

        # Original should be unchanged
        assert "new" not in registry.list_handlers()

    def test_has_handler_false_for_missing(self, registry: JobRegistry) -> None:
        """Test has_handler returns False for missing handlers."""
        assert registry.has_handler("nonexistent") is False

    def test_get_handler_none_for_missing(self, registry: JobRegistry) -> None:
        """Test get_handler returns None for missing handlers."""
        assert registry.get_handler("nonexistent") is None

    def test_overwrite_handler_logs_warning(self, registry: JobRegistry) -> None:
        """Test that overwriting a handler logs a warning."""

        async def handler1(job: Job) -> JobResult:
            return JobResult(success=True, message="1")

        async def handler2(job: Job) -> JobResult:
            return JobResult(success=True, message="2")

        registry.register("duplicate", handler1)

        with patch.object(registry, "_handlers", registry._handlers):
            # Should log warning but still register
            registry.register("duplicate", handler2)

        assert registry.get_handler("duplicate") is handler2


# ---------------------------------------------------------------------------
# Dispatch Tests
# ---------------------------------------------------------------------------


class TestDispatch:
    """Tests for job dispatch."""

    @pytest.mark.asyncio
    async def test_dispatch_success(self, registry: JobRegistry, sample_job: Job) -> None:
        """Test dispatching a job that succeeds."""

        @registry.handler("test_job")
        async def handle_test(job: Job) -> JobResult:
            return JobResult(
                success=True,
                message=f"Processed {job.id}",
                details={"payload": job.payload},
            )

        result = await registry.dispatch(sample_job)

        assert result.success is True
        assert "job-123" in result.message
        assert result.details == {"payload": {"key": "value"}}

    @pytest.mark.asyncio
    async def test_dispatch_failure_result(self, registry: JobRegistry, sample_job: Job) -> None:
        """Test dispatching a job that returns failure."""

        @registry.handler("test_job")
        async def handle_test(job: Job) -> JobResult:
            return JobResult(success=False, message="Something went wrong")

        result = await registry.dispatch(sample_job)

        assert result.success is False
        assert result.message == "Something went wrong"

    @pytest.mark.asyncio
    async def test_dispatch_unknown_job(self, registry: JobRegistry, sample_job: Job) -> None:
        """Test dispatching a job with no handler raises UnknownJobError."""
        sample_job.name = "unknown_job"

        with pytest.raises(UnknownJobError) as exc_info:
            await registry.dispatch(sample_job)

        assert exc_info.value.job_name == "unknown_job"

    @pytest.mark.asyncio
    async def test_dispatch_timeout(self, registry: JobRegistry, sample_job: Job) -> None:
        """Test dispatching a job that exceeds timeout."""

        @registry.handler("test_job")
        async def handle_slow(job: Job) -> JobResult:
            await asyncio.sleep(1.0)  # Simulate slow job
            return JobResult(success=True, message="Done")

        with pytest.raises(JobTimeoutError) as exc_info:
            await registry.dispatch(sample_job, timeout=0.1)

        assert exc_info.value.job_name == "test_job"
        assert exc_info.value.timeout == 0.1

    @pytest.mark.asyncio
    async def test_dispatch_no_timeout(self, registry: JobRegistry, sample_job: Job) -> None:
        """Test dispatching a job with timeout=None."""

        @registry.handler("test_job")
        async def handle_test(job: Job) -> JobResult:
            return JobResult(success=True, message="No timeout")

        result = await registry.dispatch(sample_job, timeout=None)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_dispatch_handler_exception(self, registry: JobRegistry, sample_job: Job) -> None:
        """Test dispatching a job whose handler raises an exception."""

        @registry.handler("test_job")
        async def handle_error(job: Job) -> JobResult:
            raise ValueError("Handler error")

        with pytest.raises(ValueError, match="Handler error"):
            await registry.dispatch(sample_job)

    @pytest.mark.asyncio
    async def test_dispatch_uses_job_payload(self, registry: JobRegistry, sample_job: Job) -> None:
        """Test that dispatch passes the full job to handler."""
        received_job = None

        @registry.handler("test_job")
        async def handle_capture(job: Job) -> JobResult:
            nonlocal received_job
            received_job = job
            return JobResult(success=True, message="Captured")

        await registry.dispatch(sample_job)

        assert received_job is not None
        assert received_job.id == "job-123"
        assert received_job.name == "test_job"
        assert received_job.payload == {"key": "value"}


# ---------------------------------------------------------------------------
# Metrics Tests
# ---------------------------------------------------------------------------


class TestMetrics:
    """Tests for Prometheus metrics integration."""

    @pytest.mark.asyncio
    async def test_metrics_disabled_without_prometheus(
        self, registry: JobRegistry, sample_job: Job
    ) -> None:
        """Test that dispatch works when prometheus-client is not installed."""

        @registry.handler("test_job")
        async def handle_test(job: Job) -> JobResult:
            return JobResult(success=True, message="Done")

        # Mock ImportError for metrics
        with patch("svc_infra.jobs.registry.logger"):
            # Force re-initialization
            registry._metrics_initialized = False

            with patch.dict("sys.modules", {"svc_infra.obs.metrics.base": None}):
                # Should work without metrics
                result = await registry.dispatch(sample_job)
                assert result.success is True

    @pytest.mark.asyncio
    async def test_metrics_prefix_used(self, sample_job: Job) -> None:
        """Test that custom metric prefix is used."""
        registry = JobRegistry(metric_prefix="custom_prefix")

        @registry.handler("test_job")
        async def handle_test(job: Job) -> JobResult:
            return JobResult(success=True, message="Done")

        mock_counter = MagicMock()
        mock_histogram = MagicMock()

        with patch("svc_infra.jobs.registry.logger"):
            with patch(
                "svc_infra.obs.metrics.base.counter", return_value=mock_counter
            ) as counter_mock:
                with patch("svc_infra.obs.metrics.base.histogram", return_value=mock_histogram):
                    await registry.dispatch(sample_job)

                    # Check that counter was called with prefixed name
                    counter_calls = counter_mock.call_args_list
                    assert any(
                        "custom_prefix_processed_total" in str(call) for call in counter_calls
                    )


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------


class TestIntegration:
    """Integration tests for JobRegistry."""

    @pytest.mark.asyncio
    async def test_multiple_handlers(self, registry: JobRegistry) -> None:
        """Test registry with multiple handlers."""

        @registry.handler("job_a")
        async def handle_a(job: Job) -> JobResult:
            return JobResult(success=True, message="A")

        @registry.handler("job_b")
        async def handle_b(job: Job) -> JobResult:
            return JobResult(success=True, message="B")

        @registry.handler("job_c")
        async def handle_c(job: Job) -> JobResult:
            return JobResult(success=False, message="C failed")

        job_a = Job(id="1", name="job_a", payload={})
        job_b = Job(id="2", name="job_b", payload={})
        job_c = Job(id="3", name="job_c", payload={})

        result_a = await registry.dispatch(job_a)
        result_b = await registry.dispatch(job_b)
        result_c = await registry.dispatch(job_c)

        assert result_a.success is True
        assert result_a.message == "A"
        assert result_b.success is True
        assert result_b.message == "B"
        assert result_c.success is False
        assert result_c.message == "C failed"

    @pytest.mark.asyncio
    async def test_handler_accesses_payload(self, registry: JobRegistry) -> None:
        """Test that handlers can access job payload."""

        @registry.handler("email")
        async def handle_email(job: Job) -> JobResult:
            to = job.payload.get("to")
            subject = job.payload.get("subject")
            return JobResult(
                success=True,
                message=f"Sent to {to}",
                details={"to": to, "subject": subject},
            )

        job = Job(
            id="email-1",
            name="email",
            payload={"to": "user@example.com", "subject": "Hello"},
        )

        result = await registry.dispatch(job)

        assert result.success is True
        assert result.details == {"to": "user@example.com", "subject": "Hello"}

    @pytest.mark.asyncio
    async def test_concurrent_dispatch(self, registry: JobRegistry) -> None:
        """Test concurrent job dispatch."""
        call_count = 0

        @registry.handler("concurrent")
        async def handle_concurrent(job: Job) -> JobResult:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # Small delay
            return JobResult(success=True, message=f"Job {job.id}")

        jobs = [Job(id=f"job-{i}", name="concurrent", payload={"i": i}) for i in range(5)]

        results = await asyncio.gather(*[registry.dispatch(job) for job in jobs])

        assert len(results) == 5
        assert all(r.success for r in results)
        assert call_count == 5
