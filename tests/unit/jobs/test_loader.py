from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from svc_infra.jobs.loader import schedule_from_env
from svc_infra.jobs.queue import InMemoryJobQueue
from svc_infra.jobs.scheduler import InMemoryScheduler

pytestmark = pytest.mark.jobs

_CALLS: list[str] = []


def loader_sync_task() -> None:
    _CALLS.append("sync")


async def loader_async_task() -> None:
    _CALLS.append("async")


@pytest.mark.asyncio
async def test_schedule_from_env_loads_interval_and_cron_tasks(monkeypatch: pytest.MonkeyPatch):
    _CALLS.clear()
    start = datetime(2026, 3, 29, 9, 0, tzinfo=UTC)
    scheduler = InMemoryScheduler(now_provider=lambda: start)
    monkeypatch.setenv(
        "JOBS_SCHEDULE_JSON",
        json.dumps(
            [
                {
                    "name": "interval-task",
                    "interval_seconds": 0,
                    "target": f"{__name__}:loader_sync_task",
                },
                {
                    "name": "cron-task",
                    "cron": "0 9 * * *",
                    "target": f"{__name__}:loader_async_task",
                },
            ]
        ),
    )

    schedule_from_env(scheduler)
    await scheduler.tick(now=start)

    assert _CALLS == ["sync", "async"]


def test_schedule_from_env_defaults_to_60_second_intervals(monkeypatch: pytest.MonkeyPatch):
    scheduler = InMemoryScheduler(now_provider=lambda: datetime(2026, 3, 29, 9, 0, tzinfo=UTC))
    monkeypatch.setenv(
        "JOBS_SCHEDULE_JSON",
        json.dumps(
            [
                {
                    "name": "default-interval",
                    "target": f"{__name__}:loader_sync_task",
                }
            ]
        ),
    )

    schedule_from_env(scheduler)

    assert scheduler._tasks["default-interval"].interval_seconds == 60


@pytest.mark.asyncio
async def test_schedule_from_env_loads_scheduled_job_entries(monkeypatch: pytest.MonkeyPatch):
    queue = InMemoryJobQueue()
    start = datetime(2026, 3, 29, 9, 0, tzinfo=UTC)
    scheduler = InMemoryScheduler(now_provider=lambda: start)
    monkeypatch.setenv(
        "JOBS_SCHEDULE_JSON",
        json.dumps(
            [
                {
                    "name": "scheduled-email",
                    "interval_seconds": 0,
                    "job_name": "send_email",
                    "payload": {"to": "queue@example.com"},
                }
            ]
        ),
    )

    schedule_from_env(scheduler, queue=queue)
    await scheduler.tick(now=start)

    job = queue.reserve_next()
    assert job is not None
    assert job.name == "send_email"
    assert job.payload == {"to": "queue@example.com"}
