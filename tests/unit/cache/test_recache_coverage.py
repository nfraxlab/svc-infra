"""Tests for cache recache functionality - Coverage improvement."""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from svc_infra.cache.recache import (
    RecachePlan,
    build_getter_kwargs,
    execute_recache,
    generate_key_variants,
    recache,
)

# ─── RecachePlan Tests ───────────────────────────────────────────────────────


class TestRecachePlan:
    """Tests for RecachePlan dataclass."""

    def test_create_minimal(self) -> None:
        """Test creating plan with minimal args."""

        async def getter():
            pass

        plan = RecachePlan(getter=getter)
        assert plan.getter is getter
        assert plan.include is None
        assert plan.rename is None
        assert plan.extra is None
        assert plan.key is None

    def test_create_full(self) -> None:
        """Test creating plan with all args."""

        async def getter():
            pass

        plan = RecachePlan(
            getter=getter,
            include=["a", "b"],
            rename={"x": "y"},
            extra={"z": 1},
            key="cache:{id}",
        )
        assert plan.include == ["a", "b"]
        assert plan.rename == {"x": "y"}
        assert plan.extra == {"z": 1}
        assert plan.key == "cache:{id}"

    def test_frozen(self) -> None:
        """Test that RecachePlan is immutable."""

        async def getter():
            pass

        plan = RecachePlan(getter=getter)
        with pytest.raises(AttributeError):  # FrozenInstanceError
            plan.key = "new_key"  # type: ignore


# ─── recache() Factory Tests ────────────────────────────────────────────────


class TestRecacheFactory:
    """Tests for recache() factory function."""

    def test_creates_plan(self) -> None:
        """Test that recache() returns a RecachePlan."""

        async def getter():
            pass

        plan = recache(getter)
        assert isinstance(plan, RecachePlan)
        assert plan.getter is getter

    def test_with_include(self) -> None:
        """Test recache with include parameter."""

        async def getter():
            pass

        plan = recache(getter, include=["id", "name"])
        assert plan.include == ["id", "name"]

    def test_with_rename(self) -> None:
        """Test recache with rename parameter."""

        async def getter():
            pass

        plan = recache(getter, rename={"user_id": "id"})
        assert plan.rename == {"user_id": "id"}

    def test_with_extra(self) -> None:
        """Test recache with extra parameters."""

        async def getter():
            pass

        plan = recache(getter, extra={"limit": 10})
        assert plan.extra == {"limit": 10}

    def test_with_key_string(self) -> None:
        """Test recache with string key."""

        async def getter():
            pass

        plan = recache(getter, key="user:{id}")
        assert plan.key == "user:{id}"

    def test_with_key_tuple(self) -> None:
        """Test recache with tuple key."""

        async def getter():
            pass

        plan = recache(getter, key=("user", "{id}"))
        assert plan.key == ("user", "{id}")


# ─── generate_key_variants Tests ───────────────────────────────────────────


class TestGenerateKeyVariants:
    """Tests for generate_key_variants function."""

    @patch("svc_infra.cache.recache._alias")
    @patch("svc_infra.cache.recache.normalize_cache_key")
    @patch("svc_infra.cache.recache.validate_cache_key")
    def test_with_namespace(
        self, mock_validate: MagicMock, mock_normalize: MagicMock, mock_alias: MagicMock
    ) -> None:
        """Test key variants with namespace."""
        mock_alias.return_value = "ns"
        mock_normalize.return_value = "user:123"
        mock_validate.return_value = "user:123"

        variants = generate_key_variants("user:{id}", {"id": 123})
        assert "ns:user:123" in variants
        assert "user:123" in variants

    @patch("svc_infra.cache.recache._alias")
    @patch("svc_infra.cache.recache.normalize_cache_key")
    @patch("svc_infra.cache.recache.validate_cache_key")
    def test_without_namespace(
        self, mock_validate: MagicMock, mock_normalize: MagicMock, mock_alias: MagicMock
    ) -> None:
        """Test key variants without namespace."""
        mock_alias.return_value = ""
        mock_normalize.return_value = "user:123"
        mock_validate.return_value = "user:123"

        variants = generate_key_variants("user:{id}", {"id": 123})
        assert "user:123" in variants

    @patch("svc_infra.cache.recache._alias")
    @patch("svc_infra.cache.recache.normalize_cache_key")
    def test_key_error_returns_empty(
        self, mock_normalize: MagicMock, mock_alias: MagicMock
    ) -> None:
        """Test that KeyError returns empty list."""
        mock_alias.return_value = "ns"
        mock_normalize.side_effect = KeyError("missing_key")

        variants = generate_key_variants("user:{missing}", {})
        assert variants == []

    @patch("svc_infra.cache.recache._alias")
    @patch("svc_infra.cache.recache.normalize_cache_key")
    def test_value_error_returns_empty(
        self, mock_normalize: MagicMock, mock_alias: MagicMock
    ) -> None:
        """Test that ValueError returns empty list."""
        mock_alias.return_value = "ns"
        mock_normalize.side_effect = ValueError("invalid key")

        variants = generate_key_variants("invalid:{}", {})
        assert variants == []

    @patch("svc_infra.cache.recache._alias")
    @patch("svc_infra.cache.recache.normalize_cache_key")
    @patch("svc_infra.cache.recache.validate_cache_key")
    def test_removes_duplicates(
        self, mock_validate: MagicMock, mock_normalize: MagicMock, mock_alias: MagicMock
    ) -> None:
        """Test that duplicates are removed."""
        mock_alias.return_value = ""
        mock_normalize.return_value = "key"
        mock_validate.return_value = "key"

        variants = generate_key_variants("key", {})
        # Should only have one copy of "key"
        assert variants.count("key") == 1

    @patch("svc_infra.cache.recache._alias")
    @patch("svc_infra.cache.recache.normalize_cache_key")
    @patch("svc_infra.cache.recache.validate_cache_key")
    def test_key_already_has_namespace(
        self, mock_validate: MagicMock, mock_normalize: MagicMock, mock_alias: MagicMock
    ) -> None:
        """Test key that already includes namespace prefix."""
        mock_alias.return_value = "ns"
        mock_normalize.return_value = "ns:user:123"
        mock_validate.return_value = "ns:user:123"

        variants = generate_key_variants("ns:user:{id}", {"id": 123})
        # Should strip namespace and include both versions
        assert "ns:user:123" in variants or "user:123" in variants


# ─── build_getter_kwargs Tests ─────────────────────────────────────────────


class TestBuildGetterKwargs:
    """Tests for build_getter_kwargs function."""

    def test_simple_function(self) -> None:
        """Test with simple function as spec."""

        async def getter(user_id: int) -> str:
            return f"user:{user_id}"

        fn, kwargs = build_getter_kwargs(getter, (), {"user_id": 123})
        assert fn is getter
        assert kwargs == {"user_id": 123}

    def test_recache_plan_basic(self) -> None:
        """Test with RecachePlan - basic parameter matching."""

        async def getter(id: int) -> str:
            return f"item:{id}"

        plan = RecachePlan(getter=getter)
        fn, kwargs = build_getter_kwargs(plan, (), {"id": 42})
        assert fn is getter
        assert kwargs == {"id": 42}

    def test_recache_plan_with_include(self) -> None:
        """Test RecachePlan with include filter."""

        async def getter(id: int, name: str = "") -> str:
            return f"{name}:{id}"

        plan = RecachePlan(getter=getter, include=["id"])
        _fn, kwargs = build_getter_kwargs(plan, (), {"id": 1, "name": "test", "extra": "ignored"})
        assert kwargs == {"id": 1}

    def test_recache_plan_with_rename(self) -> None:
        """Test RecachePlan with parameter renaming."""

        async def getter(target_id: int) -> str:
            return f"target:{target_id}"

        plan = RecachePlan(getter=getter, rename={"user_id": "target_id"})
        _fn, kwargs = build_getter_kwargs(plan, (), {"user_id": 999})
        assert kwargs == {"target_id": 999}

    def test_recache_plan_with_extra(self) -> None:
        """Test RecachePlan with extra parameters."""

        async def getter(id: int, limit: int = 10) -> str:
            return f"id:{id}:limit:{limit}"

        plan = RecachePlan(getter=getter, extra={"limit": 50})
        _fn, kwargs = build_getter_kwargs(plan, (), {"id": 5})
        assert kwargs == {"id": 5, "limit": 50}

    def test_recache_plan_filters_invalid_params(self) -> None:
        """Test that invalid parameters are filtered out."""

        async def getter(a: int) -> str:
            return str(a)

        plan = RecachePlan(getter=getter)
        _fn, kwargs = build_getter_kwargs(plan, (), {"a": 1, "b": 2, "c": 3})
        assert kwargs == {"a": 1}

    def test_legacy_tuple_with_dict_mapping(self) -> None:
        """Test legacy tuple format with dict mapping."""

        async def getter(item_id: int) -> str:
            return f"item:{item_id}"

        spec = (getter, {"item_id": "id"})
        fn, kwargs = build_getter_kwargs(spec, (), {"id": 777})
        assert fn is getter
        assert kwargs == {"item_id": 777}

    def test_legacy_tuple_with_callable_mapping(self) -> None:
        """Test legacy tuple format with callable mapping."""

        async def getter(computed: int) -> str:
            return f"computed:{computed}"

        def mapper(*args, **kwargs):
            return {"computed": kwargs.get("x", 0) * 2}

        spec = (getter, mapper)
        fn, kwargs = build_getter_kwargs(spec, (), {"x": 10})
        assert fn is getter
        assert kwargs == {"computed": 20}

    def test_legacy_tuple_callable_returns_none(self) -> None:
        """Test legacy tuple with callable returning None."""

        async def getter(id: int) -> str:
            return str(id)

        def mapper(*args, **kwargs):
            return None

        spec = (getter, mapper)
        _fn, kwargs = build_getter_kwargs(spec, (), {"id": 5})
        # Should fall back to direct parameter matching
        assert kwargs == {"id": 5}

    def test_legacy_tuple_callable_raises(self) -> None:
        """Test legacy tuple with callable that raises."""

        async def getter(id: int) -> str:
            return str(id)

        def mapper(*args, **kwargs):
            raise ValueError("oops")

        spec = (getter, mapper)
        # Should not raise, just log warning
        _fn, kwargs = build_getter_kwargs(spec, (), {"id": 5})
        assert kwargs == {"id": 5}

    def test_legacy_tuple_dict_with_callable_value(self) -> None:
        """Test legacy dict mapping with callable value."""

        async def getter(result: int) -> str:
            return str(result)

        def compute(*args, **kwargs):
            return kwargs.get("a", 0) + kwargs.get("b", 0)

        spec = (getter, {"result": compute})
        _fn, kwargs = build_getter_kwargs(spec, (), {"a": 3, "b": 4})
        assert kwargs == {"result": 7}

    def test_legacy_tuple_dict_callable_raises(self) -> None:
        """Test legacy dict mapping with callable that raises."""

        async def getter(value: int) -> str:
            return str(value)

        def bad_compute(*args, **kwargs):
            raise RuntimeError("failed")

        spec = (getter, {"value": bad_compute})
        _fn, kwargs = build_getter_kwargs(spec, (), {})
        # Should not include the failed mapping
        assert "value" not in kwargs


# ─── execute_recache Tests ─────────────────────────────────────────────────


class TestExecuteRecache:
    """Tests for execute_recache function."""

    @pytest.mark.asyncio
    async def test_empty_specs(self) -> None:
        """Test with empty specs list."""
        # Should not raise
        await execute_recache([])

    @pytest.mark.asyncio
    async def test_single_spec(self) -> None:
        """Test with single spec."""
        called = []

        async def getter(id: int):
            called.append(id)

        await execute_recache([getter], id=42)
        assert called == [42]

    @pytest.mark.asyncio
    async def test_multiple_specs(self) -> None:
        """Test with multiple specs."""
        calls = []

        async def getter1(x: int):
            calls.append(("g1", x))

        async def getter2(x: int):
            calls.append(("g2", x))

        await execute_recache([getter1, getter2], x=10)
        assert ("g1", 10) in calls
        assert ("g2", 10) in calls

    @pytest.mark.asyncio
    async def test_concurrency_control(self) -> None:
        """Test that max_concurrency is respected."""
        active = 0
        max_active = 0

        async def getter(id: int):
            nonlocal active, max_active
            active += 1
            max_active = max(max_active, active)
            await asyncio.sleep(0.01)
            active -= 1

        specs = [recache(getter) for _ in range(10)]
        await execute_recache(specs, max_concurrency=3, id=1)
        assert max_active <= 3

    @pytest.mark.asyncio
    @patch("svc_infra.cache.recache._cache")
    async def test_with_key_template(self, mock_cache: MagicMock) -> None:
        """Test that cache keys are deleted before recache."""
        mock_cache.delete = AsyncMock()

        async def getter(id: int):
            pass

        with patch("svc_infra.cache.recache.generate_key_variants") as mock_gen:
            mock_gen.return_value = ["key1", "key2"]
            plan = RecachePlan(getter=getter, key="item:{id}")
            await execute_recache([plan], id=5)

        assert mock_cache.delete.await_count == 2

    @pytest.mark.asyncio
    async def test_getter_exception_logged(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that getter exceptions are logged."""

        async def failing_getter(id: int):
            raise ValueError("getter failed")

        with caplog.at_level(logging.ERROR):
            await execute_recache([failing_getter], id=1)

        assert "Recache operation failed" in caplog.text

    @pytest.mark.asyncio
    @patch("svc_infra.cache.recache._cache")
    async def test_delete_exception_handled(self, mock_cache: MagicMock) -> None:
        """Test that cache delete exceptions don't break recache."""
        mock_cache.delete = AsyncMock(side_effect=Exception("delete failed"))
        called = []

        async def getter(id: int):
            called.append(id)

        with patch("svc_infra.cache.recache.generate_key_variants") as mock_gen:
            mock_gen.return_value = ["key1"]
            plan = RecachePlan(getter=getter, key="item:{id}")
            await execute_recache([plan], id=7)

        # Getter should still be called despite delete failure
        assert called == [7]
