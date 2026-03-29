from __future__ import annotations

import logging
import uuid
from typing import Protocol

from redis import Redis

logger = logging.getLogger(__name__)

_RENEW_LUA = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('EXPIRE', KEYS[1], ARGV[2])
end
return 0
"""

_RELEASE_LUA = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
"""


class SchedulerLeadership(Protocol):
    @property
    def heartbeat_interval_seconds(self) -> float: ...

    def ensure_leader(self) -> bool: ...

    def release(self) -> None: ...


class RedisSchedulerLeader:
    """Redis-backed leadership lease for cloud-safe scheduler coordination."""

    def __init__(
        self,
        client: Redis,
        *,
        key: str = "jobs:scheduler:leader",
        lease_seconds: int = 180,
        owner_id: str | None = None,
    ):
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be greater than zero")
        self._client = client
        self._key = key
        self._lease_seconds = lease_seconds
        self._owner_id = owner_id or str(uuid.uuid4())
        self._renew_script = None
        self._release_script = None
        try:
            self._renew_script = client.register_script(_RENEW_LUA)
            self._release_script = client.register_script(_RELEASE_LUA)
        except Exception as exc:
            logger.debug("Redis scripting unavailable for scheduler leadership: %s", exc)

    @property
    def heartbeat_interval_seconds(self) -> float:
        return max(1.0, self._lease_seconds / 3)

    def ensure_leader(self) -> bool:
        if self._renew():
            return True
        return bool(self._client.set(self._key, self._owner_id, nx=True, ex=self._lease_seconds))

    def release(self) -> None:
        if self._release_script is not None:
            try:
                self._release_script(keys=[self._key], args=[self._owner_id])
                return
            except Exception as exc:
                logger.debug("Redis release script failed for scheduler leadership: %s", exc)
        if self._read_owner() == self._owner_id:
            self._client.delete(self._key)

    def _renew(self) -> bool:
        if self._renew_script is not None:
            try:
                return bool(
                    self._renew_script(
                        keys=[self._key],
                        args=[self._owner_id, self._lease_seconds],
                    )
                )
            except Exception as exc:
                logger.debug("Redis renew script failed for scheduler leadership: %s", exc)
        if self._read_owner() != self._owner_id:
            return False
        return bool(self._client.expire(self._key, self._lease_seconds))

    def _read_owner(self) -> str | None:
        value = self._client.get(self._key)
        if value is None:
            return None
        return value.decode() if isinstance(value, (bytes, bytearray)) else str(value)
