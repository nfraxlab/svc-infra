from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .leadership import SchedulerLeadership
from .targets import resolve_target

if TYPE_CHECKING:
    from collections.abc import Mapping

    from .queue import JobQueue

ScheduledFunc = Callable[[], Awaitable[None]]
RawScheduledFunc = Callable[[], object]

_MONTH_ALIASES = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

_WEEKDAY_ALIASES = {
    "sun": 0,
    "mon": 1,
    "tue": 2,
    "wed": 3,
    "thu": 4,
    "fri": 5,
    "sat": 6,
}

_CRON_MACROS = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}

_MAX_CRON_LOOKAHEAD_MINUTES = 60 * 24 * 366 * 5


def _coerce_callable(func: RawScheduledFunc) -> ScheduledFunc:
    async def _wrapped() -> None:
        result = func()
        if inspect.isawaitable(result):
            await cast("Awaitable[None]", result)

    return _wrapped


def _build_enqueue_func(
    job_queue: JobQueue,
    job_name: str,
    *,
    payload: Mapping[str, Any] | None = None,
    payload_factory: Callable[[], Mapping[str, Any]] | None = None,
    delay_seconds: int = 0,
) -> ScheduledFunc:
    if payload is not None and payload_factory is not None:
        raise ValueError("provide at most one of payload or payload_factory")
    if delay_seconds < 0:
        raise ValueError("delay_seconds must be greater than or equal to zero")

    async def _enqueue() -> None:
        current_payload = payload_factory() if payload_factory is not None else (payload or {})
        job_queue.enqueue(job_name, dict(current_payload), delay_seconds=delay_seconds)

    return _enqueue


def _normalize_weekday(value: int) -> int:
    return 0 if value == 7 else value


def _parse_cron_value(
    token: str,
    *,
    aliases: dict[str, int] | None,
    min_value: int,
    max_value: int,
    normalize: Callable[[int], int] | None = None,
) -> int:
    lowered = token.strip().lower()
    if aliases and lowered in aliases:
        value = aliases[lowered]
    else:
        value = int(lowered)
    if normalize is not None:
        value = normalize(value)
    if value < min_value or value > max_value:
        raise ValueError(f"cron value {token!r} must be within {min_value}..{max_value}")
    return value


def _expand_cron_part(
    part: str,
    *,
    aliases: dict[str, int] | None,
    min_value: int,
    max_value: int,
    normalize: Callable[[int], int] | None = None,
) -> set[int]:
    base, step_text = [*part.split("/", 1), "1"][:2]
    step = int(step_text)
    if step <= 0:
        raise ValueError("cron step must be greater than zero")

    if base == "*":
        start = min_value
        end = max_value
    elif "-" in base:
        start_text, end_text = base.split("-", 1)
        start = _parse_cron_value(
            start_text,
            aliases=aliases,
            min_value=min_value,
            max_value=max_value,
            normalize=normalize,
        )
        end = _parse_cron_value(
            end_text,
            aliases=aliases,
            min_value=min_value,
            max_value=max_value,
            normalize=normalize,
        )
        if start > end:
            raise ValueError(f"cron range {base!r} is invalid")
    else:
        start = _parse_cron_value(
            base,
            aliases=aliases,
            min_value=min_value,
            max_value=max_value,
            normalize=normalize,
        )
        end = max_value if "/" in part else start

    values = set(range(start, end + 1, step))
    if normalize is not None:
        values = {normalize(value) for value in values}
    return values


def _parse_cron_field(
    field: str,
    *,
    aliases: dict[str, int] | None,
    min_value: int,
    max_value: int,
    normalize: Callable[[int], int] | None = None,
) -> tuple[frozenset[int], bool]:
    text = field.strip()
    if not text:
        raise ValueError("cron field cannot be empty")
    if text == "*":
        return frozenset(range(min_value, max_value + 1)), True

    values: set[int] = set()
    for part in text.split(","):
        values.update(
            _expand_cron_part(
                part.strip(),
                aliases=aliases,
                min_value=min_value,
                max_value=max_value,
                normalize=normalize,
            )
        )
    return frozenset(values), False


@dataclass(frozen=True, slots=True)
class CronSchedule:
    expression: str
    timezone_name: str
    timezone: ZoneInfo
    minute_values: frozenset[int]
    hour_values: frozenset[int]
    day_values: frozenset[int]
    month_values: frozenset[int]
    weekday_values: frozenset[int]
    day_is_wildcard: bool
    weekday_is_wildcard: bool

    @classmethod
    def parse(cls, expression: str, *, timezone: str = "UTC") -> CronSchedule:
        text = expression.strip()
        if not text:
            raise ValueError("cron expression cannot be empty")
        normalized = _CRON_MACROS.get(text.lower(), text)
        parts = normalized.split()
        if len(parts) != 5:
            raise ValueError("cron expression must have 5 fields: minute hour day month weekday")
        try:
            tz = ZoneInfo(timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"unknown timezone {timezone!r}") from exc

        minute_values, _ = _parse_cron_field(
            parts[0],
            aliases=None,
            min_value=0,
            max_value=59,
        )
        hour_values, _ = _parse_cron_field(
            parts[1],
            aliases=None,
            min_value=0,
            max_value=23,
        )
        day_values, day_is_wildcard = _parse_cron_field(
            parts[2],
            aliases=None,
            min_value=1,
            max_value=31,
        )
        month_values, _ = _parse_cron_field(
            parts[3],
            aliases=_MONTH_ALIASES,
            min_value=1,
            max_value=12,
        )
        weekday_values, weekday_is_wildcard = _parse_cron_field(
            parts[4],
            aliases=_WEEKDAY_ALIASES,
            min_value=0,
            max_value=6,
            normalize=_normalize_weekday,
        )
        return cls(
            expression=normalized,
            timezone_name=timezone,
            timezone=tz,
            minute_values=minute_values,
            hour_values=hour_values,
            day_values=day_values,
            month_values=month_values,
            weekday_values=weekday_values,
            day_is_wildcard=day_is_wildcard,
            weekday_is_wildcard=weekday_is_wildcard,
        )

    def matches(self, dt: datetime) -> bool:
        local_dt = dt.astimezone(self.timezone)
        cron_weekday = (local_dt.weekday() + 1) % 7
        day_match = local_dt.day in self.day_values
        weekday_match = cron_weekday in self.weekday_values
        if self.day_is_wildcard and self.weekday_is_wildcard:
            date_match = True
        elif self.day_is_wildcard:
            date_match = weekday_match
        elif self.weekday_is_wildcard:
            date_match = day_match
        else:
            date_match = day_match or weekday_match
        return (
            local_dt.minute in self.minute_values
            and local_dt.hour in self.hour_values
            and local_dt.month in self.month_values
            and date_match
        )

    def next_run_after(self, after: datetime) -> datetime:
        if after.tzinfo is None:
            raise ValueError("scheduler datetimes must be timezone-aware")
        candidate = after.astimezone(self.timezone)
        if candidate.second or candidate.microsecond:
            candidate = candidate.replace(second=0, microsecond=0) + timedelta(minutes=1)
        else:
            candidate = candidate.replace(second=0, microsecond=0)

        for _ in range(_MAX_CRON_LOOKAHEAD_MINUTES):
            if self.matches(candidate):
                return candidate.astimezone(UTC)
            candidate += timedelta(minutes=1)
        raise ValueError(
            f"unable to find next run time for cron expression {self.expression!r} "
            f"within {_MAX_CRON_LOOKAHEAD_MINUTES} minutes"
        )


@dataclass(slots=True)
class ScheduledTask:
    name: str
    func: ScheduledFunc
    next_run_at: datetime
    interval_seconds: float | None = None
    cron: str | None = None
    timezone: str = "UTC"
    cron_schedule: CronSchedule | None = None
    job_name: str | None = None


class InMemoryScheduler:
    """In-process scheduler for interval and cron jobs.

    The scheduler keeps all task state in memory, which makes it a good default
    for local development, tests, and simple service processes.
    """

    def __init__(
        self,
        tick_interval: float = 60.0,
        *,
        timezone: str = "UTC",
        now_provider: Callable[[], datetime] | None = None,
        leader: SchedulerLeadership | None = None,
    ):
        self._tasks: dict[str, ScheduledTask] = {}
        self._tick_interval = tick_interval
        self._default_timezone = timezone
        self._now_provider = now_provider or (lambda: datetime.now(UTC))
        self._leader = leader

    def add_task(self, name: str, interval_seconds: int | float, func: RawScheduledFunc) -> None:
        self.add(name, interval_seconds=interval_seconds, func=func)

    def add_cron(
        self,
        name: str,
        cron: str,
        func: RawScheduledFunc,
        *,
        timezone: str | None = None,
    ) -> None:
        self.add(name, cron=cron, func=func, timezone=timezone)

    def add(
        self,
        name: str,
        *,
        interval_seconds: int | float | None = None,
        cron: str | None = None,
        func: RawScheduledFunc | None = None,
        target: str | None = None,
        job_queue: JobQueue | None = None,
        job_name: str | None = None,
        payload: Mapping[str, Any] | None = None,
        payload_factory: Callable[[], Mapping[str, Any]] | None = None,
        delay_seconds: int = 0,
        timezone: str | None = None,
    ) -> None:
        if (interval_seconds is None) == (cron is None):
            raise ValueError("provide exactly one of interval_seconds or cron")
        action_count = sum(value is not None for value in (func, target, job_name))
        if action_count != 1:
            raise ValueError("provide exactly one of func, target, or job_name")

        task_job_name = job_name
        if job_name is not None:
            if job_queue is None:
                raise ValueError("job_queue is required when job_name is provided")
            wrapped_func = _build_enqueue_func(
                job_queue,
                job_name,
                payload=payload,
                payload_factory=payload_factory,
                delay_seconds=delay_seconds,
            )
        else:
            if payload is not None or payload_factory is not None or delay_seconds:
                raise ValueError(
                    "payload, payload_factory, and delay_seconds are only valid for job_name schedules"
                )
            resolved = (
                func
                if func is not None
                else cast("RawScheduledFunc", resolve_target(cast("str", target)))
            )
            wrapped_func = _coerce_callable(resolved)
        now = self._now()

        if interval_seconds is not None:
            interval = float(interval_seconds)
            if interval < 0:
                raise ValueError("interval_seconds must be greater than or equal to zero")
            task = ScheduledTask(
                name=name,
                func=wrapped_func,
                interval_seconds=interval,
                next_run_at=now + timedelta(seconds=interval),
                job_name=task_job_name,
            )
        else:
            task_timezone = timezone or self._default_timezone
            cron_schedule = CronSchedule.parse(cast("str", cron), timezone=task_timezone)
            task = ScheduledTask(
                name=name,
                func=wrapped_func,
                next_run_at=cron_schedule.next_run_after(now),
                cron=cron_schedule.expression,
                timezone=task_timezone,
                cron_schedule=cron_schedule,
                job_name=task_job_name,
            )

        self._tasks[name] = task

    def add_job(
        self,
        name: str,
        *,
        job_queue: JobQueue,
        job_name: str,
        interval_seconds: int | float | None = None,
        cron: str | None = None,
        payload: Mapping[str, Any] | None = None,
        payload_factory: Callable[[], Mapping[str, Any]] | None = None,
        delay_seconds: int = 0,
        timezone: str | None = None,
    ) -> None:
        self.add(
            name,
            interval_seconds=interval_seconds,
            cron=cron,
            job_queue=job_queue,
            job_name=job_name,
            payload=payload,
            payload_factory=payload_factory,
            delay_seconds=delay_seconds,
            timezone=timezone,
        )

    async def tick(self, *, now: datetime | None = None) -> None:
        if self._leader is not None and not self._leader.ensure_leader():
            return
        current = now or self._now()
        for task in self._tasks.values():
            if task.next_run_at <= current:
                await self._run_task(task.func)
                if task.cron_schedule is not None:
                    task.next_run_at = task.cron_schedule.next_run_after(
                        current + timedelta(microseconds=1)
                    )
                else:
                    interval = task.interval_seconds or 0.0
                    task.next_run_at = current + timedelta(seconds=interval)

    async def run(self) -> None:
        """Run the scheduler loop indefinitely."""
        sleep_interval = self._tick_interval
        if self._leader is not None:
            sleep_interval = min(self._tick_interval, self._leader.heartbeat_interval_seconds)
        try:
            while True:
                await self.tick()
                await asyncio.sleep(sleep_interval)
        finally:
            self.close()

    def _now(self) -> datetime:
        current = self._now_provider()
        if current.tzinfo is None:
            raise ValueError("scheduler now_provider must return a timezone-aware datetime")
        return current.astimezone(UTC)

    def close(self) -> None:
        if self._leader is not None:
            self._leader.release()

    async def _run_task(self, func: ScheduledFunc) -> None:
        if self._leader is None:
            await func()
            return

        heartbeat = asyncio.create_task(self._heartbeat_while_running())
        try:
            await func()
        finally:
            heartbeat.cancel()
            with suppress(asyncio.CancelledError):
                await heartbeat

    async def _heartbeat_while_running(self) -> None:
        if self._leader is None:
            return
        while True:
            await asyncio.sleep(self._leader.heartbeat_interval_seconds)
            self._leader.ensure_leader()
