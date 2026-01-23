"""Background jobs module providing queue abstraction and worker utilities.

This module provides a flexible background job system with multiple backends:

- **InMemoryJobQueue**: Simple in-memory queue for tests and local development
- **RedisJobQueue**: Production-ready Redis-backed queue with visibility timeout
- **InMemoryScheduler**: Interval-based scheduler for periodic tasks
- **JobRegistry**: Handler registry with dispatch and metrics

Example:
    from svc_infra.jobs import easy_jobs, Job

    # Initialize queue and scheduler (auto-detects Redis or uses memory)
    queue, scheduler = easy_jobs()

    # Enqueue a job
    job = queue.enqueue("send_email", {"to": "user@example.com"})
    print(f"Enqueued job: {job.id}")

    # Process jobs with a worker
    from svc_infra.jobs import process_one

    async def handler(job: Job):
        if job.name == "send_email":
            await send_email(job.payload["to"])

    await process_one(queue, handler)

Using JobRegistry (recommended for larger applications):
    from svc_infra.jobs import JobRegistry, JobResult, Job

    registry = JobRegistry(metric_prefix="myapp_jobs")

    @registry.handler("send_email")
    async def handle_send_email(job: Job) -> JobResult:
        await send_email(job.payload["to"])
        return JobResult(success=True, message="Email sent")

    # In worker loop:
    async def worker_handler(job: Job) -> None:
        result = await registry.dispatch(job)
        if not result.success:
            raise RuntimeError(result.message)

Environment Variables:
    JOBS_DRIVER: Backend driver ("memory" or "redis"), defaults to "memory"
    REDIS_URL: Redis connection URL for redis driver
    JOB_DEFAULT_TIMEOUT_SECONDS: Per-job execution timeout
    JOBS_SCHEDULE_JSON: JSON array of scheduled task definitions

See Also:
    - docs/jobs.md for detailed documentation
    - svc_infra.jobs.builtins for webhook delivery and outbox processing
"""

from __future__ import annotations

# Easy setup function
from .easy import easy_jobs

# Loader for schedule configuration
from .loader import schedule_from_env

# Core queue abstractions
from .queue import InMemoryJobQueue, Job, JobQueue

# Redis-backed queue for production
from .redis_queue import RedisJobQueue

# Job registry with dispatch and metrics
from .registry import JobRegistry, JobResult, JobTimeoutError, UnknownJobError

# Runner for long-lived workers
from .runner import WorkerRunner

# Scheduler for periodic tasks
from .scheduler import InMemoryScheduler, ScheduledTask

# Worker utilities
from .worker import process_one

__all__ = [
    # Core types
    "Job",
    "JobQueue",
    # Queue implementations
    "InMemoryJobQueue",
    "RedisJobQueue",
    # Scheduler
    "InMemoryScheduler",
    "ScheduledTask",
    # Easy setup
    "easy_jobs",
    # Worker utilities
    "process_one",
    "WorkerRunner",
    # Configuration loader
    "schedule_from_env",
    # Job registry
    "JobRegistry",
    "JobResult",
    "UnknownJobError",
    "JobTimeoutError",
]
