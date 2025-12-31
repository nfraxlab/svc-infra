"""Unit tests for svc_infra.api.fastapi.versioned module."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, FastAPI

from svc_infra.api.fastapi.versioned import extract_router


class TestExtractRouter:
    """Tests for extract_router function."""

    def test_basic_extraction(self) -> None:
        """Test basic router extraction from an add function."""

        def add_feature(app: FastAPI, *, prefix: str, **kwargs: Any) -> str:
            router = APIRouter()

            @router.get("/items")
            def get_items() -> list[str]:
                return ["item1", "item2"]

            app.include_router(router, prefix=prefix)
            return "feature_provider"

        router, result = extract_router(add_feature, prefix="/feature")

        assert router is not None
        assert isinstance(router, APIRouter)
        assert result == "feature_provider"

    def test_router_has_routes(self) -> None:
        """Test that extracted router has the defined routes."""

        def add_api(app: FastAPI, *, prefix: str, **kwargs: Any) -> dict[str, str]:
            router = APIRouter()

            @router.get("/health")
            def health() -> dict[str, str]:
                return {"status": "ok"}

            @router.post("/data")
            def create_data() -> dict[str, str]:
                return {"id": "123"}

            app.include_router(router, prefix=prefix)
            return {"version": "1.0"}

        router, result = extract_router(add_api, prefix="/api")

        assert len(router.routes) == 2
        assert result == {"version": "1.0"}

    def test_preserves_return_value_types(self) -> None:
        """Test that various return value types are preserved."""

        class Provider:
            def __init__(self, name: str) -> None:
                self.name = name

        def add_with_provider(
            app: FastAPI, *, prefix: str, name: str = "default", **kwargs: Any
        ) -> Provider:
            router = APIRouter()

            @router.get("/status")
            def status() -> dict[str, str]:
                return {"provider": name}

            app.include_router(router, prefix=prefix)
            return Provider(name=name)

        router, provider = extract_router(add_with_provider, prefix="/provider", name="custom")

        assert isinstance(provider, Provider)
        assert provider.name == "custom"
        assert router is not None

    def test_passes_kwargs_to_add_function(self) -> None:
        """Test that kwargs are passed through to the add function."""
        received_kwargs: dict[str, Any] = {}

        def add_configurable(app: FastAPI, *, prefix: str, **kwargs: Any) -> dict[str, Any]:
            nonlocal received_kwargs
            received_kwargs = kwargs.copy()
            router = APIRouter()

            @router.get("/")
            def root() -> dict[str, str]:
                return {}

            app.include_router(router, prefix=prefix)
            return {"configured": True}

        extract_router(
            add_configurable,
            prefix="/test",
            cache_ttl=60,
            enable_metrics=True,
            rate_limit=100,
        )

        assert received_kwargs == {
            "cache_ttl": 60,
            "enable_metrics": True,
            "rate_limit": 100,
        }

    def test_handles_none_return_value(self) -> None:
        """Test extraction when add function returns None."""

        def add_simple(app: FastAPI, *, prefix: str, **kwargs: Any) -> None:
            router = APIRouter()

            @router.get("/ping")
            def ping() -> str:
                return "pong"

            app.include_router(router, prefix=prefix)
            return None

        router, result = extract_router(add_simple, prefix="/simple")

        assert router is not None
        assert result is None

    def test_multiple_route_methods(self) -> None:
        """Test extraction with various HTTP methods."""

        def add_crud(app: FastAPI, *, prefix: str, **kwargs: Any) -> None:
            router = APIRouter()

            @router.get("/items")
            def list_items() -> list[str]:
                return []

            @router.post("/items")
            def create_item() -> dict[str, str]:
                return {"id": "new"}

            @router.get("/items/{item_id}")
            def get_item(item_id: str) -> dict[str, str]:
                return {"id": item_id}

            @router.put("/items/{item_id}")
            def update_item(item_id: str) -> dict[str, str]:
                return {"id": item_id, "updated": True}

            @router.delete("/items/{item_id}")
            def delete_item(item_id: str) -> None:
                pass

            app.include_router(router, prefix=prefix)

        router, _ = extract_router(add_crud, prefix="/crud")

        assert router is not None
        assert len(router.routes) == 5
