"""
Job handler registry with dispatch and metrics.

This module provides a centralized registry for job handlers with:
- Handler registration by job name (imperative or decorator style)
- Dispatch with optional timeout and metrics
- Lazy Prometheus metrics (optional dependency)

Example:
    from svc_infra.jobs import JobRegistry, JobResult, Job

    registry = JobRegistry(metric_prefix="myapp_jobs")

    @registry.handler("send_email")
    async def handle_send_email(job: Job) -> JobResult:
        email = job.payload["to"]
        # send email...
        return JobResult(success=True, message=f"Email sent to {email}")

    # In worker loop:
    async def worker_handler(job: Job) -> None:
        result = await registry.dispatch(job)
        if not result.success:
            raise RuntimeError(result.message)

Environment Variables:
    JOB_DEFAULT_TIMEOUT_SECONDS: Override default timeout for all jobs
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from svc_infra.jobs.queue import Job

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result and Exceptions
# ---------------------------------------------------------------------------


@dataclass
class JobResult:
    """Result of a job execution.

    Attributes:
        success: Whether the job completed successfully
        message: Human-readable result message
        details: Optional additional details (e.g., counts, IDs)
    """

    success: bool
    message: str
    details: dict[str, Any] | None = field(default=None)

    def __post_init__(self) -> None:
        """Ensure details is None if empty dict."""
        if self.details == {}:
            self.details = None


class UnknownJobError(Exception):
    """Raised when a job has no registered handler."""

    def __init__(self, job_name: str) -> None:
        self.job_name = job_name
        super().__init__(f"Unknown job type: {job_name}")


class JobTimeoutError(Exception):
    """Raised when a job exceeds its timeout."""

    def __init__(self, job_name: str, timeout: float) -> None:
        self.job_name = job_name
        self.timeout = timeout
        super().__init__(f"Job {job_name} exceeded timeout of {timeout}s")


# ---------------------------------------------------------------------------
# Handler Type
# ---------------------------------------------------------------------------

# Handler function signature: takes a Job, returns a JobResult
HandlerFunc = Callable[["Job"], Awaitable[JobResult]]


# ---------------------------------------------------------------------------
# Job Registry
# ---------------------------------------------------------------------------


class JobRegistry:
    """Registry for job handlers with dispatch and metrics.

    Provides a centralized way to register job handlers and dispatch jobs
    to them with optional timeout and Prometheus metrics.

    Attributes:
        metric_prefix: Prefix for Prometheus metric names (default: "jobs")

    Example:
        registry = JobRegistry(metric_prefix="myapp_jobs")

        # Register with decorator
        @registry.handler("process_order")
        async def handle_order(job: Job) -> JobResult:
            order_id = job.payload["order_id"]
            return JobResult(success=True, message=f"Processed order {order_id}")

        # Register imperatively
        registry.register("send_notification", send_notification_handler)

        # Dispatch
        result = await registry.dispatch(job, timeout=60.0)
    """

    def __init__(self, metric_prefix: str = "jobs") -> None:
        """Initialize the job registry.

        Args:
            metric_prefix: Prefix for Prometheus metric names.
                           Metrics will be named: {prefix}_processed_total,
                           {prefix}_duration_seconds, {prefix}_failures_total
        """
        self._handlers: dict[str, HandlerFunc] = {}
        self._metric_prefix = metric_prefix

        # Lazy-initialized metrics
        self._metrics_initialized = False
        self._jobs_processed = None
        self._job_duration = None
        self._job_failures = None

    # -----------------------------------------------------------------------
    # Handler Registration
    # -----------------------------------------------------------------------

    def register(self, name: str, handler: HandlerFunc) -> None:
        """Register a handler for a job name.

        Args:
            name: Job name to register
            handler: Async function taking a Job and returning JobResult

        Example:
            async def my_handler(job: Job) -> JobResult:
                return JobResult(success=True, message="Done")

            registry.register("my_job", my_handler)
        """
        if name in self._handlers:
            logger.warning(f"Overwriting existing handler for job: {name}")
        self._handlers[name] = handler
        logger.debug(f"Registered handler for job: {name}")

    def handler(self, name: str) -> Callable[[HandlerFunc], HandlerFunc]:
        """Decorator to register a handler for a job name.

        Args:
            name: Job name to register

        Returns:
            Decorator function

        Example:
            @registry.handler("send_email")
            async def handle_send_email(job: Job) -> JobResult:
                return JobResult(success=True, message="Email sent")
        """

        def decorator(func: HandlerFunc) -> HandlerFunc:
            self.register(name, func)
            return func

        return decorator

    def get_handler(self, name: str) -> HandlerFunc | None:
        """Get the handler function for a job name.

        Args:
            name: Job name

        Returns:
            Handler function or None if not registered
        """
        return self._handlers.get(name)

    def has_handler(self, name: str) -> bool:
        """Check if a handler is registered for a job name.

        Args:
            name: Job name

        Returns:
            True if handler exists
        """
        return name in self._handlers

    def list_handlers(self) -> list[str]:
        """Get list of all registered job handler names.

        Returns:
            List of job names that have registered handlers
        """
        return list(self._handlers.keys())

    @property
    def handlers(self) -> dict[str, HandlerFunc]:
        """Get the internal handlers dictionary (read-only access)."""
        return self._handlers.copy()

    # -----------------------------------------------------------------------
    # Metrics (Lazy Initialization)
    # -----------------------------------------------------------------------

    def _init_metrics(self) -> bool:
        """Lazily initialize Prometheus metrics.

        Returns:
            True if metrics are available, False otherwise.
        """
        if self._metrics_initialized:
            return self._jobs_processed is not None

        self._metrics_initialized = True

        try:
            from svc_infra.obs.metrics.base import counter, histogram

            self._jobs_processed = counter(
                f"{self._metric_prefix}_processed_total",
                f"Total jobs processed (prefix: {self._metric_prefix})",
                labels=["job_name", "status"],
            )

            self._job_duration = histogram(
                f"{self._metric_prefix}_duration_seconds",
                f"Job processing duration in seconds (prefix: {self._metric_prefix})",
                labels=["job_name"],
                buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0),
            )

            self._job_failures = counter(
                f"{self._metric_prefix}_failures_total",
                f"Total job failures by error type (prefix: {self._metric_prefix})",
                labels=["job_name", "error_type"],
            )

            return True
        except ImportError:
            logger.debug("Prometheus metrics disabled: svc-infra[metrics] not installed")
            return False
        except Exception as e:
            logger.warning(f"Failed to initialize job metrics: {e}")
            return False

    # -----------------------------------------------------------------------
    # Job Dispatch
    # -----------------------------------------------------------------------

    async def dispatch(
        self,
        job: Job,
        *,
        timeout: float | None = 300.0,
    ) -> JobResult:
        """Dispatch a job to its registered handler.

        Looks up the handler by job name, executes it with optional timeout,
        and records Prometheus metrics for observability.

        Args:
            job: The job to dispatch (from queue.reserve_next())
            timeout: Maximum execution time in seconds (default: 5 minutes).
                     Set to None to disable timeout.

        Returns:
            JobResult from the handler

        Raises:
            UnknownJobError: If no handler is registered for the job name
            JobTimeoutError: If job exceeds timeout (when timeout is not None)
            Exception: Re-raised from handler on failure

        Example:
            async def worker_handler(job: Job) -> None:
                result = await registry.dispatch(job)
                if not result.success:
                    logger.error(f"Job failed: {result.message}")
        """
        # Initialize metrics (lazy, optional)
        metrics_enabled = self._init_metrics()

        handler = self._handlers.get(job.name)

        if handler is None:
            if metrics_enabled and self._job_failures:
                self._job_failures.labels(job_name=job.name, error_type="unknown_job").inc()
            raise UnknownJobError(job.name)

        # Structured logging if available
        log = (
            logger.bind(
                job_id=job.id,
                job_name=job.name,
                attempt=job.attempts,
            )
            if hasattr(logger, "bind")
            else logger
        )

        log.info(f"Dispatching job {job.id} to handler: {job.name}")

        start_time = time.monotonic()

        try:
            # Execute with optional timeout
            if timeout is not None:
                result = await asyncio.wait_for(
                    handler(job),
                    timeout=timeout,
                )
            else:
                result = await handler(job)

            # Record metrics (if available)
            duration = time.monotonic() - start_time

            if metrics_enabled:
                if self._job_duration:
                    self._job_duration.labels(job_name=job.name).observe(duration)

                if result.success:
                    if self._jobs_processed:
                        self._jobs_processed.labels(job_name=job.name, status="success").inc()
                else:
                    if self._jobs_processed:
                        self._jobs_processed.labels(job_name=job.name, status="failure").inc()
                    if self._job_failures:
                        self._job_failures.labels(
                            job_name=job.name,
                            error_type="handler_failure",
                        ).inc()

            if result.success:
                log.info(
                    f"Job {job.id} completed successfully in {duration:.2f}s",
                    extra={"duration": duration, "result_message": result.message},
                )
            else:
                log.warning(
                    f"Job {job.id} completed with failure: {result.message}",
                    extra={"duration": duration, "result_message": result.message},
                )

            return result

        except TimeoutError:
            duration = time.monotonic() - start_time

            if metrics_enabled:
                if self._jobs_processed:
                    self._jobs_processed.labels(job_name=job.name, status="timeout").inc()
                if self._job_failures:
                    self._job_failures.labels(job_name=job.name, error_type="timeout").inc()
                if self._job_duration:
                    self._job_duration.labels(job_name=job.name).observe(duration)

            log.error(
                f"Job {job.id} timed out after {duration:.2f}s (limit: {timeout}s)",
                extra={"duration": duration, "timeout": timeout},
            )
            raise JobTimeoutError(job.name, timeout) from None

        except Exception as e:
            duration = time.monotonic() - start_time

            if metrics_enabled:
                if self._jobs_processed:
                    self._jobs_processed.labels(job_name=job.name, status="error").inc()
                if self._job_failures:
                    self._job_failures.labels(
                        job_name=job.name,
                        error_type=type(e).__name__,
                    ).inc()
                if self._job_duration:
                    self._job_duration.labels(job_name=job.name).observe(duration)

            log.exception(
                f"Job {job.id} raised exception: {e}",
                extra={"duration": duration, "error": str(e)},
            )
            raise
