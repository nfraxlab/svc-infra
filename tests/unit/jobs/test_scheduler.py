from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from svc_infra.jobs.queue import InMemoryJobQueue
from svc_infra.jobs.scheduler import InMemoryScheduler

pytestmark = pytest.mark.jobs


@pytest.mark.asyncio
async def test_scheduler_runs_task_on_tick():
    ran = False

    async def task():
        nonlocal ran
        ran = True

    scheduler = InMemoryScheduler()
    scheduler.add_task("t1", interval_seconds=0, func=task)

    await scheduler.tick()
    assert ran is True


@pytest.mark.asyncio
async def test_scheduler_runs_cron_task_and_advances_next_run():
    ran = 0
    now = datetime(2026, 3, 29, 9, 0, tzinfo=UTC)

    async def task():
        nonlocal ran
        ran += 1

    scheduler = InMemoryScheduler(now_provider=lambda: now)
    scheduler.add_cron("daily-digest", "0 9 * * *", task)

    await scheduler.tick(now=now)

    assert ran == 1
    assert scheduler._tasks["daily-digest"].next_run_at == datetime(2026, 3, 30, 9, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_scheduler_supports_cron_aliases_and_timezones():
    ran = 0
    now = datetime(2026, 3, 30, 12, 59, tzinfo=UTC)

    async def task():
        nonlocal ran
        ran += 1

    scheduler = InMemoryScheduler(now_provider=lambda: now)
    scheduler.add(
        "market-open",
        cron="0 9 * * mon-fri",
        func=task,
        timezone="America/New_York",
    )

    await scheduler.tick(now=datetime(2026, 3, 30, 13, 0, tzinfo=UTC))

    assert ran == 1


@pytest.mark.asyncio
async def test_scheduler_renews_leadership_while_task_runs():
    class CountingLeader:
        heartbeat_interval_seconds = 0.01

        def __init__(self) -> None:
            self.calls = 0

        def ensure_leader(self) -> bool:
            self.calls += 1
            return True

        def release(self) -> None:
            return None

    leader = CountingLeader()

    async def task():
        await asyncio.sleep(0.03)

    scheduler = InMemoryScheduler(leader=leader)
    scheduler.add_task("long-task", interval_seconds=0, func=task)

    await scheduler.tick()

    assert leader.calls >= 2


@pytest.mark.asyncio
async def test_scheduler_can_enqueue_jobs_durably():
    queue = InMemoryJobQueue()
    scheduler = InMemoryScheduler()
    scheduler.add_job(
        "daily-email",
        job_queue=queue,
        job_name="send_email",
        interval_seconds=0,
        payload={"to": "user@example.com"},
    )

    await scheduler.tick()

    job = queue.reserve_next()
    assert job is not None
    assert job.name == "send_email"
    assert job.payload == {"to": "user@example.com"}


def test_scheduler_add_rejects_invalid_schedule_configuration():
    scheduler = InMemoryScheduler()

    with pytest.raises(ValueError, match="exactly one of interval_seconds or cron"):
        scheduler.add("bad", func=lambda: None)

    with pytest.raises(ValueError, match="exactly one of interval_seconds or cron"):
        scheduler.add("bad", interval_seconds=60, cron="0 * * * *", func=lambda: None)

    with pytest.raises(ValueError, match="exactly one of func, target, or job_name"):
        scheduler.add("bad", interval_seconds=60)
