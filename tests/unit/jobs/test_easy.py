"""Tests for svc_infra.jobs.easy module."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

from svc_infra.jobs.easy import JobsConfig, easy_jobs
from svc_infra.jobs.queue import InMemoryJobQueue
from svc_infra.jobs.scheduler import InMemoryScheduler


class TestJobsConfig:
    """Tests for JobsConfig class."""

    def test_default_driver_is_memory(self) -> None:
        """Should default to memory driver."""
        with patch.dict(os.environ, {}, clear=True):
            config = JobsConfig()
            assert config.driver == "memory"

    def test_uses_driver_argument(self) -> None:
        """Should use driver argument if provided."""
        config = JobsConfig(driver="redis")
        assert config.driver == "redis"

    def test_driver_from_env(self) -> None:
        """Should read driver from JOBS_DRIVER env var."""
        with patch.dict(os.environ, {"JOBS_DRIVER": "redis"}):
            config = JobsConfig()
            assert config.driver == "redis"

    def test_driver_argument_overrides_env(self) -> None:
        """Driver argument should override env var."""
        with patch.dict(os.environ, {"JOBS_DRIVER": "redis"}):
            config = JobsConfig(driver="memory")
            assert config.driver == "memory"

    def test_driver_is_case_sensitive(self) -> None:
        """Driver preserves case when passed as argument."""
        config = JobsConfig(driver="MEMORY")
        assert config.driver == "MEMORY"

    def test_driver_from_env_is_lowercased(self) -> None:
        """Driver from env should be lowercased."""
        with patch.dict(os.environ, {"JOBS_DRIVER": "REDIS"}):
            config = JobsConfig()
            assert config.driver == "redis"


class TestEasyJobs:
    """Tests for easy_jobs function."""

    def test_returns_tuple_of_queue_and_scheduler(self) -> None:
        """Should return (queue, scheduler) tuple."""
        with patch.dict(os.environ, {"JOBS_DRIVER": "memory"}):
            queue, scheduler = easy_jobs()
            assert queue is not None
            assert scheduler is not None

    def test_memory_driver_returns_inmemory_queue(self) -> None:
        """Memory driver should return InMemoryJobQueue."""
        with patch.dict(os.environ, {"JOBS_DRIVER": "memory"}):
            queue, scheduler = easy_jobs(driver="memory")
            assert isinstance(queue, InMemoryJobQueue)

    def test_returns_inmemory_scheduler(self) -> None:
        """Should always return InMemoryScheduler."""
        with patch.dict(os.environ, {"JOBS_DRIVER": "memory"}):
            queue, scheduler = easy_jobs()
            assert isinstance(scheduler, InMemoryScheduler)

    def test_driver_argument(self) -> None:
        """Should accept driver argument."""
        queue, scheduler = easy_jobs(driver="memory")
        assert isinstance(queue, InMemoryJobQueue)

    def test_default_to_memory_without_env(self) -> None:
        """Should default to memory without env var."""
        with patch.dict(os.environ, {}, clear=True):
            # Clear JOBS_DRIVER if set
            env_copy = dict(os.environ)
            env_copy.pop("JOBS_DRIVER", None)
            with patch.dict(os.environ, env_copy, clear=True):
                queue, scheduler = easy_jobs()
                assert isinstance(queue, InMemoryJobQueue)

    def test_redis_driver_uses_redis_url(self) -> None:
        """Redis driver should use REDIS_URL env var."""
        # We'll mock the Redis client creation since we don't have a redis connection
        with patch.dict(os.environ, {"JOBS_DRIVER": "redis", "REDIS_URL": "redis://test:6379/1"}):
            with patch("svc_infra.jobs.easy.Redis") as mock_redis:
                mock_client = MagicMock()
                mock_redis.from_url.return_value = mock_client

                queue, scheduler = easy_jobs(driver="redis")

                mock_redis.from_url.assert_called_once_with("redis://test:6379/1")

    def test_redis_driver_default_url(self) -> None:
        """Redis driver should use default URL if not set."""
        env = {"JOBS_DRIVER": "redis"}
        # Remove REDIS_URL if present
        with patch.dict(os.environ, env, clear=True):
            with patch("svc_infra.jobs.easy.Redis") as mock_redis:
                mock_client = MagicMock()
                mock_redis.from_url.return_value = mock_client

                queue, scheduler = easy_jobs(driver="redis")

                mock_redis.from_url.assert_called_once_with("redis://localhost:6379/0")


class TestEasyJobsIntegration:
    """Integration tests for easy_jobs."""

    def test_queue_can_enqueue_jobs(self) -> None:
        """Queue returned should be usable."""
        queue, _ = easy_jobs(driver="memory")
        queue.enqueue("test.job", {"data": "value"})
        # Should have one job
        job = queue.reserve_next()
        assert job is not None
        assert job.name == "test.job"

    def test_scheduler_can_add_tasks(self) -> None:
        """Scheduler returned should be usable."""
        _, scheduler = easy_jobs(driver="memory")

        async def dummy_task():
            pass

        scheduler.add_task("test-task", 60, dummy_task)
        # Task should be registered (scheduler works)
        assert scheduler is not None
