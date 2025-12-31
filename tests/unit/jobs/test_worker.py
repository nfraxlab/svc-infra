"""Tests for svc_infra.jobs.worker module."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest

from svc_infra.jobs.queue import InMemoryJobQueue
from svc_infra.jobs.worker import (
    _get_job_timeout_seconds,
    process_one,
)


class TestGetJobTimeoutSeconds:
    """Tests for _get_job_timeout_seconds function."""

    def test_returns_none_when_not_set(self) -> None:
        """Should return None when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove JOB_DEFAULT_TIMEOUT_SECONDS if set
            env = dict(os.environ)
            env.pop("JOB_DEFAULT_TIMEOUT_SECONDS", None)
            with patch.dict(os.environ, env, clear=True):
                result = _get_job_timeout_seconds()
                assert result is None

    def test_returns_float_value(self) -> None:
        """Should return float from env var."""
        with patch.dict(os.environ, {"JOB_DEFAULT_TIMEOUT_SECONDS": "30.0"}):
            result = _get_job_timeout_seconds()
            assert result == 30.0

    def test_returns_integer_as_float(self) -> None:
        """Should convert integer string to float."""
        with patch.dict(os.environ, {"JOB_DEFAULT_TIMEOUT_SECONDS": "60"}):
            result = _get_job_timeout_seconds()
            assert result == 60.0

    def test_returns_none_for_invalid_value(self) -> None:
        """Should return None for invalid value."""
        with patch.dict(os.environ, {"JOB_DEFAULT_TIMEOUT_SECONDS": "not-a-number"}):
            result = _get_job_timeout_seconds()
            assert result is None

    def test_returns_none_for_empty_string(self) -> None:
        """Should return None for empty string."""
        with patch.dict(os.environ, {"JOB_DEFAULT_TIMEOUT_SECONDS": ""}):
            result = _get_job_timeout_seconds()
            assert result is None


class TestProcessOne:
    """Tests for process_one function."""

    @pytest.mark.asyncio
    async def test_returns_false_when_no_job(self) -> None:
        """Should return False when queue is empty."""
        queue = InMemoryJobQueue()
        handler = AsyncMock()

        result = await process_one(queue, handler)

        assert result is False
        handler.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_processes_job_successfully(self) -> None:
        """Should process job and ack on success."""
        queue = InMemoryJobQueue()
        queue.enqueue("test.job", {"key": "value"})
        handler = AsyncMock()

        with patch.dict(os.environ, {}, clear=True):
            result = await process_one(queue, handler)

        assert result is True
        handler.assert_awaited_once()
        # Job should be acked (queue empty now)
        assert queue.reserve_next() is None

    @pytest.mark.asyncio
    async def test_passes_job_to_handler(self) -> None:
        """Should pass job object to handler."""
        queue = InMemoryJobQueue()
        queue.enqueue("my.job", {"data": 123})
        captured_job = None

        async def capture_handler(job):
            nonlocal captured_job
            captured_job = job

        with patch.dict(os.environ, {}, clear=True):
            await process_one(queue, capture_handler)

        assert captured_job is not None
        assert captured_job.name == "my.job"
        assert captured_job.payload == {"data": 123}

    @pytest.mark.asyncio
    async def test_fails_job_on_exception(self) -> None:
        """Should fail job when handler raises exception."""
        queue = InMemoryJobQueue()
        queue.enqueue("failing.job", {})

        async def failing_handler(job):
            raise ValueError("Handler error")

        with patch.dict(os.environ, {}, clear=True):
            result = await process_one(queue, failing_handler)

        assert result is True
        # Job should be failed, not acked

    @pytest.mark.asyncio
    async def test_uses_timeout_from_env(self) -> None:
        """Should use timeout from environment variable."""
        queue = InMemoryJobQueue()
        queue.enqueue("test.job", {})
        handler = AsyncMock()

        with patch.dict(os.environ, {"JOB_DEFAULT_TIMEOUT_SECONDS": "5.0"}):
            with patch("svc_infra.jobs.worker.asyncio.wait_for") as mock_wait_for:
                mock_wait_for.return_value = None
                result = await process_one(queue, handler)

        assert result is True
        mock_wait_for.assert_awaited_once()
        # Check timeout was passed
        call_args = mock_wait_for.call_args
        assert call_args.kwargs.get("timeout") == 5.0 or call_args[1].get("timeout") == 5.0

    @pytest.mark.asyncio
    async def test_no_timeout_when_not_configured(self) -> None:
        """Should not use timeout when not configured."""
        queue = InMemoryJobQueue()
        queue.enqueue("test.job", {})
        handler = AsyncMock()

        with patch.dict(os.environ, {}, clear=True):
            env = dict(os.environ)
            env.pop("JOB_DEFAULT_TIMEOUT_SECONDS", None)
            with patch.dict(os.environ, env, clear=True):
                with patch("svc_infra.jobs.worker.asyncio.wait_for") as mock_wait_for:
                    await process_one(queue, handler)

        # wait_for should not be called
        mock_wait_for.assert_not_awaited()


class TestProcessOneIntegration:
    """Integration tests for process_one."""

    @pytest.mark.asyncio
    async def test_multiple_jobs_processed_sequentially(self) -> None:
        """Should process multiple jobs one at a time."""
        queue = InMemoryJobQueue()
        queue.enqueue("job.1", {"num": 1})
        queue.enqueue("job.2", {"num": 2})
        queue.enqueue("job.3", {"num": 3})

        processed = []

        async def handler(job):
            processed.append(job.name)

        with patch.dict(os.environ, {}, clear=True):
            await process_one(queue, handler)
            await process_one(queue, handler)
            await process_one(queue, handler)
            # Fourth call should return False
            result = await process_one(queue, handler)

        assert len(processed) == 3
        assert result is False

    @pytest.mark.asyncio
    async def test_job_with_empty_payload(self) -> None:
        """Should handle job with empty payload."""
        queue = InMemoryJobQueue()
        queue.enqueue("empty.job", {})
        handler = AsyncMock()

        with patch.dict(os.environ, {}, clear=True):
            result = await process_one(queue, handler)

        assert result is True
