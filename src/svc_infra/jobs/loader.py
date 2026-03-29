from __future__ import annotations

import json
import logging
import os

from .queue import JobQueue
from .scheduler import InMemoryScheduler

logger = logging.getLogger(__name__)


def schedule_from_env(
    scheduler: InMemoryScheduler,
    queue: JobQueue | None = None,
    env_var: str = "JOBS_SCHEDULE_JSON",
) -> None:
    data = os.getenv(env_var)
    if not data:
        return
    try:
        tasks = json.loads(data)
    except json.JSONDecodeError:
        return
    if not isinstance(tasks, list):
        return
    for t in tasks:
        try:
            name = t["name"]
            interval_seconds = t.get("interval_seconds")
            if interval_seconds is None and "cron" not in t:
                interval_seconds = 60
            kwargs = {
                "interval_seconds": interval_seconds,
                "cron": t.get("cron"),
                "timezone": t.get("timezone"),
            }
            if "job_name" in t:
                scheduler.add(
                    name,
                    job_queue=queue,
                    job_name=t["job_name"],
                    payload=t.get("payload"),
                    delay_seconds=int(t.get("delay_seconds", 0)),
                    **kwargs,
                )
            else:
                scheduler.add(
                    name,
                    target=t["target"],
                    **kwargs,
                )
        except Exception as e:
            logger.warning("Failed to load scheduled job entry %s: %s", t, e)
            continue
