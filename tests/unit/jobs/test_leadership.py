from __future__ import annotations

import pytest

from svc_infra.jobs.leadership import RedisSchedulerLeader
from svc_infra.jobs.scheduler import InMemoryScheduler

pytestmark = pytest.mark.jobs


@pytest.fixture()
def fakeredis():
    try:
        import fakeredis
    except Exception:  # pragma: no cover - dependency may not exist
        pytest.skip("fakeredis not installed")
    return fakeredis.FakeRedis()


def test_redis_scheduler_leader_enforces_single_owner(fakeredis):
    leader_a = RedisSchedulerLeader(
        fakeredis,
        key="jobs:test:leader",
        lease_seconds=30,
        owner_id="worker-a",
    )
    leader_b = RedisSchedulerLeader(
        fakeredis,
        key="jobs:test:leader",
        lease_seconds=30,
        owner_id="worker-b",
    )

    assert leader_a.ensure_leader() is True
    assert leader_b.ensure_leader() is False

    leader_a.release()

    assert leader_b.ensure_leader() is True


@pytest.mark.asyncio
async def test_scheduler_tick_only_runs_on_active_leader(fakeredis):
    ran = 0

    async def task():
        nonlocal ran
        ran += 1

    leader_a = RedisSchedulerLeader(
        fakeredis,
        key="jobs:test:scheduler",
        lease_seconds=30,
        owner_id="scheduler-a",
    )
    leader_b = RedisSchedulerLeader(
        fakeredis,
        key="jobs:test:scheduler",
        lease_seconds=30,
        owner_id="scheduler-b",
    )

    scheduler_a = InMemoryScheduler(leader=leader_a)
    scheduler_b = InMemoryScheduler(leader=leader_b)
    scheduler_a.add_task("tick", interval_seconds=0, func=task)
    scheduler_b.add_task("tick", interval_seconds=0, func=task)

    await scheduler_a.tick()
    await scheduler_b.tick()

    assert ran == 1
