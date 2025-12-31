"""Tests for svc_infra.jobs.loader module."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from svc_infra.jobs.loader import _resolve_target, schedule_from_env
from svc_infra.jobs.scheduler import InMemoryScheduler


class TestResolveTarget:
    """Tests for _resolve_target function."""

    def test_resolve_async_function(self) -> None:
        """Resolves async function correctly."""
        target = "asyncio:sleep"
        fn = _resolve_target(target)
        assert callable(fn)
        # asyncio.sleep is a coroutine function
        import asyncio

        assert asyncio.iscoroutinefunction(fn)

    def test_resolve_sync_function_wraps_to_async(self) -> None:
        """Sync function is wrapped to async."""
        target = "json:loads"
        fn = _resolve_target(target)
        assert callable(fn)
        # Should be wrapped in async
        import asyncio

        assert asyncio.iscoroutinefunction(fn)

    def test_resolve_nested_module(self) -> None:
        """Can resolve function from nested module."""
        target = "os.path:join"
        fn = _resolve_target(target)
        assert callable(fn)

    def test_resolve_invalid_module_raises(self) -> None:
        """Invalid module raises ImportError."""
        with pytest.raises(ModuleNotFoundError):
            _resolve_target("nonexistent_module:func")

    def test_resolve_invalid_function_raises(self) -> None:
        """Invalid function name raises AttributeError."""
        with pytest.raises(AttributeError):
            _resolve_target("json:nonexistent_function")


class TestScheduleFromEnv:
    """Tests for schedule_from_env function."""

    def test_no_env_var_does_nothing(self) -> None:
        """No env var means no tasks added."""
        scheduler = InMemoryScheduler()

        with patch.dict("os.environ", {}, clear=True):
            schedule_from_env(scheduler, env_var="JOBS_SCHEDULE_JSON")

        assert len(scheduler._tasks) == 0

    def test_empty_env_var_does_nothing(self) -> None:
        """Empty env var means no tasks added."""
        scheduler = InMemoryScheduler()

        with patch.dict("os.environ", {"JOBS_SCHEDULE_JSON": ""}, clear=True):
            schedule_from_env(scheduler)

        assert len(scheduler._tasks) == 0

    def test_invalid_json_does_nothing(self) -> None:
        """Invalid JSON is ignored."""
        scheduler = InMemoryScheduler()

        with patch.dict("os.environ", {"JOBS_SCHEDULE_JSON": "not json"}, clear=True):
            schedule_from_env(scheduler)

        assert len(scheduler._tasks) == 0

    def test_non_list_json_does_nothing(self) -> None:
        """Non-list JSON is ignored."""
        scheduler = InMemoryScheduler()
        data = json.dumps({"name": "test"})

        with patch.dict("os.environ", {"JOBS_SCHEDULE_JSON": data}, clear=True):
            schedule_from_env(scheduler)

        assert len(scheduler._tasks) == 0

    def test_valid_task_is_added(self) -> None:
        """Valid task definition adds task to scheduler."""
        scheduler = InMemoryScheduler()
        tasks = [
            {
                "name": "test-task",
                "interval_seconds": 120,
                "target": "json:loads",
            }
        ]
        data = json.dumps(tasks)

        with patch.dict("os.environ", {"JOBS_SCHEDULE_JSON": data}, clear=True):
            schedule_from_env(scheduler)

        assert len(scheduler._tasks) == 1
        assert "test-task" in scheduler._tasks

    def test_default_interval_is_60(self) -> None:
        """Default interval is 60 seconds."""
        scheduler = InMemoryScheduler()
        tasks = [
            {
                "name": "test-task",
                "target": "json:loads",
            }
        ]
        data = json.dumps(tasks)

        with patch.dict("os.environ", {"JOBS_SCHEDULE_JSON": data}, clear=True):
            schedule_from_env(scheduler)

        assert len(scheduler._tasks) == 1

    def test_multiple_tasks_added(self) -> None:
        """Multiple valid tasks are all added."""
        scheduler = InMemoryScheduler()
        tasks = [
            {"name": "task-1", "target": "json:loads"},
            {"name": "task-2", "target": "json:dumps"},
        ]
        data = json.dumps(tasks)

        with patch.dict("os.environ", {"JOBS_SCHEDULE_JSON": data}, clear=True):
            schedule_from_env(scheduler)

        assert len(scheduler._tasks) == 2

    def test_invalid_task_skipped_others_added(self) -> None:
        """Invalid task is skipped, valid ones are added."""
        scheduler = InMemoryScheduler()
        tasks = [
            {"name": "valid-task", "target": "json:loads"},
            {"name": "invalid-task", "target": "nonexistent:func"},
            {"name": "another-valid", "target": "json:dumps"},
        ]
        data = json.dumps(tasks)

        with patch.dict("os.environ", {"JOBS_SCHEDULE_JSON": data}, clear=True):
            schedule_from_env(scheduler)

        # Only valid tasks should be added
        assert "valid-task" in scheduler._tasks
        assert "another-valid" in scheduler._tasks
        assert "invalid-task" not in scheduler._tasks

    def test_missing_name_skips_task(self) -> None:
        """Task without name is skipped."""
        scheduler = InMemoryScheduler()
        tasks = [
            {"target": "json:loads"},  # Missing name
            {"name": "valid-task", "target": "json:dumps"},
        ]
        data = json.dumps(tasks)

        with patch.dict("os.environ", {"JOBS_SCHEDULE_JSON": data}, clear=True):
            schedule_from_env(scheduler)

        assert len(scheduler._tasks) == 1
        assert "valid-task" in scheduler._tasks

    def test_missing_target_skips_task(self) -> None:
        """Task without target is skipped."""
        scheduler = InMemoryScheduler()
        tasks = [
            {"name": "no-target-task"},  # Missing target
            {"name": "valid-task", "target": "json:dumps"},
        ]
        data = json.dumps(tasks)

        with patch.dict("os.environ", {"JOBS_SCHEDULE_JSON": data}, clear=True):
            schedule_from_env(scheduler)

        assert len(scheduler._tasks) == 1
        assert "valid-task" in scheduler._tasks

    def test_custom_env_var_name(self) -> None:
        """Custom env var name is used."""
        scheduler = InMemoryScheduler()
        tasks = [{"name": "test", "target": "json:loads"}]
        data = json.dumps(tasks)

        with patch.dict("os.environ", {"CUSTOM_JOBS": data}, clear=True):
            schedule_from_env(scheduler, env_var="CUSTOM_JOBS")

        assert len(scheduler._tasks) == 1
