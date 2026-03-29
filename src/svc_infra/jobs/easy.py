from __future__ import annotations

import os

from redis import Redis

from svc_infra.deploy import get_redis_url

from .leadership import RedisSchedulerLeader
from .queue import InMemoryJobQueue, JobQueue
from .redis_queue import RedisJobQueue
from .scheduler import InMemoryScheduler


class JobsConfig:
    def __init__(
        self,
        driver: str | None = None,
        *,
        scheduler_coordination: str | None = None,
        scheduler_lease_seconds: int | None = None,
        scheduler_lease_key: str | None = None,
    ):
        # Future: support redis/sql drivers via extras
        driver_value = driver if driver is not None else os.getenv("JOBS_DRIVER", "memory")
        coordination_value = (
            scheduler_coordination
            if scheduler_coordination is not None
            else os.getenv("JOBS_SCHEDULER_COORDINATION", "auto")
        )
        lease_seconds_value = (
            scheduler_lease_seconds
            if scheduler_lease_seconds is not None
            else int(os.getenv("JOBS_SCHEDULER_LEASE_SECONDS", "180"))
        )
        lease_key_value = (
            scheduler_lease_key
            if scheduler_lease_key is not None
            else os.getenv("JOBS_SCHEDULER_LEASE_KEY", "jobs:scheduler:leader")
        )
        self.driver = driver_value if driver is not None else driver_value.lower()
        self.scheduler_coordination = coordination_value.lower()
        self.scheduler_lease_seconds = lease_seconds_value
        self.scheduler_lease_key = lease_key_value


def _resolve_jobs_redis_url() -> str:
    url = (
        os.getenv("JOBS_REDIS_URL")
        or get_redis_url(prefer_private=True)
        or "redis://localhost:6379/0"
    )
    if not url.startswith(("redis://", "rediss://", "unix://")):
        raise ValueError(
            "Jobs Redis coordination requires a redis://, rediss://, or unix:// URL. "
            "REST-style Redis URLs are not supported by redis-py."
        )
    return url


def easy_jobs(
    *,
    driver: str | None = None,
    scheduler_coordination: str | None = None,
    scheduler_lease_seconds: int | None = None,
    scheduler_lease_key: str | None = None,
) -> tuple[JobQueue, InMemoryScheduler]:
    """One-call wiring for jobs: returns (queue, scheduler).

    Defaults to in-memory implementations for local/dev. ENV override via JOBS_DRIVER.
    """
    cfg = JobsConfig(
        driver=driver,
        scheduler_coordination=scheduler_coordination,
        scheduler_lease_seconds=scheduler_lease_seconds,
        scheduler_lease_key=scheduler_lease_key,
    )
    # Choose backend
    queue: JobQueue
    redis_client: Redis | None = None
    if cfg.driver == "redis":
        redis_client = Redis.from_url(_resolve_jobs_redis_url())
        queue = RedisJobQueue(redis_client)
    else:
        queue = InMemoryJobQueue()
    leader = None
    if cfg.scheduler_coordination not in {"auto", "off", "none", "redis"}:
        raise ValueError("scheduler_coordination must be one of: auto, redis, off, none")
    use_redis_coordination = cfg.scheduler_coordination == "redis" or (
        cfg.scheduler_coordination == "auto" and cfg.driver == "redis"
    )
    if use_redis_coordination:
        redis_client = redis_client or Redis.from_url(_resolve_jobs_redis_url())
        leader = RedisSchedulerLeader(
            redis_client,
            key=cfg.scheduler_lease_key,
            lease_seconds=cfg.scheduler_lease_seconds,
        )
    scheduler = InMemoryScheduler(leader=leader)
    return queue, scheduler
