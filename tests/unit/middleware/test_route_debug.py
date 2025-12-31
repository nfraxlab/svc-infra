"""Unit tests for svc_infra.api.fastapi.middleware.debug module."""

from __future__ import annotations

import logging

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from svc_infra.api.fastapi.middleware.debug import RouteDebugMiddleware


@pytest.fixture
def app() -> FastAPI:
    """Create a test FastAPI app with debug middleware."""
    app = FastAPI()
    app.add_middleware(RouteDebugMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    @app.post("/items")
    async def create_item():
        return {"created": True}

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client."""
    return TestClient(app)


class TestRouteDebugMiddleware:
    """Tests for RouteDebugMiddleware."""

    def test_logs_matched_route(self, client: TestClient, caplog) -> None:
        """Test that middleware logs the matched route."""
        with caplog.at_level(logging.INFO, logger="route.debug"):
            response = client.get("/test")

        assert response.status_code == 200
        # Check log was created
        assert any("MATCHED" in record.message for record in caplog.records)

    def test_logs_endpoint_name(self, client: TestClient, caplog) -> None:
        """Test that middleware logs the endpoint function name."""
        with caplog.at_level(logging.INFO, logger="route.debug"):
            response = client.get("/test")

        assert response.status_code == 200
        # Check endpoint name was logged
        assert any("test_endpoint" in record.message for record in caplog.records)

    def test_logs_method_and_path(self, client: TestClient, caplog) -> None:
        """Test that middleware logs HTTP method and path."""
        with caplog.at_level(logging.INFO, logger="route.debug"):
            response = client.post("/items")

        assert response.status_code == 200
        # Check method and path logged
        log_messages = [r.message for r in caplog.records]
        assert any("POST" in msg and "/items" in msg for msg in log_messages)

    def test_passes_through_response(self, client: TestClient) -> None:
        """Test that middleware passes through the response unchanged."""
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_handles_404_gracefully(self, client: TestClient, caplog) -> None:
        """Test that middleware handles non-existent routes."""
        with caplog.at_level(logging.INFO, logger="route.debug"):
            response = client.get("/nonexistent")

        assert response.status_code == 404
        # Should still log, even if no route matched
        # (route will be None in this case)
