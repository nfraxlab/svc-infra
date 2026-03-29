from __future__ import annotations

import asyncio
import inspect
import os

import typer

from svc_infra.jobs.easy import easy_jobs
from svc_infra.jobs.loader import schedule_from_env
from svc_infra.jobs.registry import JobRegistry
from svc_infra.jobs.targets import resolve_target
from svc_infra.jobs.worker import process_one

app = typer.Typer(help="Background jobs and scheduler commands")


async def _noop_handler(job):
    # Default handler does nothing; users should write their own runners
    return None


def _load_job_handler(
    *,
    handler_target: str | None,
    registry_target: str | None,
):
    if handler_target and registry_target:
        raise typer.BadParameter("Provide at most one of --handler-target or --registry-target")
    if handler_target:
        resolved = resolve_target(handler_target)

        async def _handler(job):
            result = resolved(job)
            if inspect.isawaitable(result):
                await result

        return _handler
    if registry_target:
        resolved = resolve_target(registry_target)
        registry = (
            resolved() if callable(resolved) and not isinstance(resolved, JobRegistry) else resolved
        )
        if not isinstance(registry, JobRegistry):
            raise typer.BadParameter(
                "--registry-target must resolve to a JobRegistry instance or factory"
            )

        async def _handler(job):
            result = await registry.dispatch(job)
            if not result.success:
                raise RuntimeError(result.message)

        return _handler
    return _noop_handler


@app.command("run")
def run(
    poll_interval: float = typer.Option(0.5, help="Sleep seconds between loops when idle"),
    max_loops: int | None = typer.Option(None, help="Max loops before exit (for tests)"),
    handler_target: str | None = typer.Option(
        None,
        help="module:path target for a job handler function taking one job argument",
    ),
    registry_target: str | None = typer.Option(
        None,
        help="module:path target for a JobRegistry instance or factory",
    ),
):
    """Run scheduler ticks and process jobs in a simple loop."""

    queue, scheduler = easy_jobs()
    handler = _load_job_handler(
        handler_target=handler_target or os.getenv("JOBS_HANDLER_TARGET"),
        registry_target=registry_target or os.getenv("JOBS_REGISTRY_TARGET"),
    )
    # load schedule from env JSON if provided
    schedule_from_env(scheduler, queue=queue)

    async def _loop():
        loops = 0
        try:
            while True:
                await scheduler.tick()
                processed = await process_one(queue, handler)
                if not processed:
                    # idle
                    await asyncio.sleep(poll_interval)
                if max_loops is not None:
                    loops += 1
                    if loops >= max_loops:
                        break
        finally:
            scheduler.close()

    asyncio.run(_loop())
