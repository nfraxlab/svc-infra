"""Benchmarks for cache operations.

Run with:
    make benchmark
    pytest benchmarks/bench_cache.py --benchmark-only
"""

from __future__ import annotations


class TestCacheImport:
    """Benchmark cache module imports."""

    def test_cache_import(self, benchmark):
        """Benchmark cache module import time."""

        def import_cache():
            import importlib

            import svc_infra.cache

            importlib.reload(svc_infra.cache)

        benchmark(import_cache)


class TestCacheDecorators:
    """Benchmark cache decorator operations."""

    def test_cache_decorator_application(self, benchmark):
        """Benchmark applying cache_read decorator."""
        from svc_infra.cache import cache_read

        def apply_decorator():
            @cache_read(ttl=300)
            def sample_function(x: int) -> int:
                return x * 2

            return sample_function

        result = benchmark(apply_decorator)
        assert callable(result)

    def test_cache_write_decorator_application(self, benchmark):
        """Benchmark applying cache_write decorator."""
        from svc_infra.cache import cache_write

        def apply_decorator():
            @cache_write(invalidates=["items"])
            def update_item(item_id: int, data: dict) -> dict:
                return {"id": item_id, **data}

            return update_item

        result = benchmark(apply_decorator)
        assert callable(result)


class TestResourceDefinition:
    """Benchmark resource-based caching."""

    def test_resource_definition(self, benchmark):
        """Benchmark resource decorator application."""
        from svc_infra.cache import resource

        def define_resource():
            @resource("user")
            class UserResource:
                @staticmethod
                def get_cache_key(user_id: int) -> str:
                    return f"user:{user_id}"

            return UserResource

        result = benchmark(define_resource)
        assert result is not None


class TestRecachePlan:
    """Benchmark recache planning operations."""

    def test_recache_plan_creation(self, benchmark):
        """Benchmark RecachePlan creation."""
        from svc_infra.cache import RecachePlan

        def create_plan():
            return RecachePlan(
                keys=["user:1", "user:2", "user:3"],
                ttl=3600,
            )

        result = benchmark(create_plan)
        assert len(result.keys) == 3
