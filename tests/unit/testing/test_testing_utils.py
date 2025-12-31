"""Unit tests for svc_infra.testing module."""

from __future__ import annotations

import time
from datetime import UTC, datetime

from svc_infra.testing import (
    CacheEntry,
    MockCache,
    MockJob,
    MockJobQueue,
)


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_not_expired_when_no_expiry(self) -> None:
        """Test that entry without expiry is never expired."""
        entry = CacheEntry(value="test")
        assert entry.is_expired() is False

    def test_not_expired_when_future(self) -> None:
        """Test that entry with future expiry is not expired."""
        entry = CacheEntry(value="test", expires_at=time.time() + 100)
        assert entry.is_expired() is False

    def test_expired_when_past(self) -> None:
        """Test that entry with past expiry is expired."""
        entry = CacheEntry(value="test", expires_at=time.time() - 1)
        assert entry.is_expired() is True


class TestMockCache:
    """Tests for MockCache class."""

    def test_get_set(self) -> None:
        """Test basic get/set operations."""
        cache = MockCache()
        cache.set("key", "value")
        assert cache.get("key") == "value"

    def test_get_missing_key(self) -> None:
        """Test getting a missing key returns None."""
        cache = MockCache()
        assert cache.get("nonexistent") is None

    def test_set_with_ttl(self) -> None:
        """Test setting a value with TTL."""
        cache = MockCache()
        cache.set("key", "value", ttl=3600)
        assert cache.get("key") == "value"

    def test_expired_key_returns_none(self) -> None:
        """Test that expired keys return None."""
        cache = MockCache()
        # Set with very short TTL
        cache.set("key", "value", ttl=-1)  # Already expired
        assert cache.get("key") is None

    def test_delete(self) -> None:
        """Test deleting a key."""
        cache = MockCache()
        cache.set("key", "value")
        result = cache.delete("key")
        assert result is True
        assert cache.get("key") is None

    def test_delete_missing_key(self) -> None:
        """Test deleting a missing key returns False."""
        cache = MockCache()
        result = cache.delete("nonexistent")
        assert result is False

    def test_delete_pattern(self) -> None:
        """Test pattern-based deletion."""
        cache = MockCache()
        cache.set("user:1", "alice")
        cache.set("user:2", "bob")
        cache.set("session:1", "sess1")

        deleted = cache.delete_pattern("user:*")
        assert deleted == 2
        assert cache.get("user:1") is None
        assert cache.get("user:2") is None
        assert cache.get("session:1") == "sess1"

    def test_set_with_tags(self) -> None:
        """Test setting values with tags."""
        cache = MockCache()
        cache.set("item:1", "value1", tags=["category:a"])
        cache.set("item:2", "value2", tags=["category:a"])
        cache.set("item:3", "value3", tags=["category:b"])

        deleted = cache.delete_by_tag("category:a")
        assert deleted == 2
        assert cache.get("item:1") is None
        assert cache.get("item:2") is None
        assert cache.get("item:3") == "value3"

    def test_delete_by_nonexistent_tag(self) -> None:
        """Test deleting by nonexistent tag."""
        cache = MockCache()
        cache.set("key", "value")
        deleted = cache.delete_by_tag("nonexistent")
        assert deleted == 0

    def test_exists(self) -> None:
        """Test checking key existence."""
        cache = MockCache()
        cache.set("key", "value")
        assert cache.exists("key") is True
        assert cache.exists("nonexistent") is False

    def test_clear(self) -> None:
        """Test clearing all cached values."""
        cache = MockCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_keys(self) -> None:
        """Test listing keys."""
        cache = MockCache()
        cache.set("user:1", "alice")
        cache.set("user:2", "bob")
        cache.set("session:1", "sess1")

        all_keys = cache.keys()
        assert len(all_keys) == 3

        user_keys = cache.keys("user:*")
        assert len(user_keys) == 2
        assert "user:1" in user_keys
        assert "user:2" in user_keys

    def test_size(self) -> None:
        """Test getting cache size."""
        cache = MockCache()
        assert cache.size() == 0

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert cache.size() == 2

    def test_prefix_isolation(self) -> None:
        """Test that different prefixes are isolated."""
        cache1 = MockCache(prefix="app1")
        cache2 = MockCache(prefix="app2")

        cache1.set("key", "value1")
        cache2.set("key", "value2")

        assert cache1.get("key") == "value1"
        assert cache2.get("key") == "value2"


class TestMockJob:
    """Tests for MockJob dataclass."""

    def test_default_values(self) -> None:
        """Test default job values."""
        job = MockJob(id="job-1", name="test", payload={})
        assert job.status == "pending"
        assert job.attempts == 0
        assert job.max_attempts == 5
        assert job.result is None
        assert job.error is None

    def test_custom_values(self) -> None:
        """Test custom job values."""
        job = MockJob(
            id="job-1",
            name="send_email",
            payload={"to": "test@example.com"},
            max_attempts=3,
            status="processing",
        )
        assert job.name == "send_email"
        assert job.payload["to"] == "test@example.com"
        assert job.max_attempts == 3
        assert job.status == "processing"


class TestMockJobQueue:
    """Tests for MockJobQueue class."""

    def test_enqueue_job(self) -> None:
        """Test enqueueing a job."""
        queue = MockJobQueue()
        job = queue.enqueue("test_job", {"key": "value"})

        assert job.id.startswith("job-")
        assert job.name == "test_job"
        assert job.payload == {"key": "value"}
        assert job.status == "pending"

    def test_register_handler(self) -> None:
        """Test registering a handler."""
        queue = MockJobQueue()
        results = []

        def handler(payload):
            results.append(payload)

        queue.register_handler("my_job", handler)
        queue.enqueue("my_job", {"data": 123})
        queue.process_all()

        assert len(results) == 1
        assert results[0] == {"data": 123}

    def test_handler_decorator(self) -> None:
        """Test handler decorator."""
        queue = MockJobQueue()
        results = []

        @queue.handler("decorated_job")
        def handle(payload):
            results.append(payload["value"])
            return "done"

        queue.enqueue("decorated_job", {"value": 42})
        queue.process_all()

        assert results == [42]

    def test_sync_mode(self) -> None:
        """Test sync mode executes immediately."""
        queue = MockJobQueue(sync_mode=True)
        results = []

        queue.register_handler("sync_job", lambda p: results.append(p))
        queue.enqueue("sync_job", {"immediate": True})

        # Should be executed immediately
        assert len(results) == 1
        assert results[0] == {"immediate": True}

    def test_jobs_property(self) -> None:
        """Test accessing pending jobs."""
        queue = MockJobQueue()
        queue.enqueue("job1", {})
        queue.enqueue("job2", {})

        assert len(queue.jobs) == 2

    def test_delayed_job(self) -> None:
        """Test delayed job scheduling."""
        queue = MockJobQueue()
        job = queue.enqueue("delayed", {"data": 1}, delay_seconds=60)

        # Job should have future available_at
        assert job.available_at > datetime.now(UTC)

    def test_clear_jobs(self) -> None:
        """Test clearing all jobs."""
        queue = MockJobQueue()
        queue.enqueue("job1", {})
        queue.enqueue("job2", {})
        queue.clear()

        assert len(queue.jobs) == 0
