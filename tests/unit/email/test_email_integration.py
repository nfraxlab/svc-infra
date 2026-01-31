"""Tests for FastAPI email integration."""

from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from svc_infra.email import (
    EmailBackend,
    EmailSender,
    add_email,
    add_sender,
    get_email,
    get_sender,
    health_check_email,
)
from svc_infra.email.backends.console import ConsoleBackend

# ─── add_email Tests ───────────────────────────────────────────────────────


class TestAddEmail:
    """Tests for add_email function."""

    def test_add_email_returns_backend(self) -> None:
        """Test add_email returns a backend."""
        app = FastAPI()
        backend = add_email(app)

        assert hasattr(backend, "send")
        assert hasattr(backend, "provider_name")

    def test_add_email_stores_in_app_state(self) -> None:
        """Test add_email stores backend in app.state."""
        app = FastAPI()
        backend = add_email(app)

        assert app.state.email is backend

    def test_add_email_with_explicit_backend(self) -> None:
        """Test add_email with explicit backend."""
        app = FastAPI()
        console = ConsoleBackend()
        backend = add_email(app, backend=console)

        assert backend is console
        assert app.state.email is console


# ─── add_sender Tests ──────────────────────────────────────────────────────


class TestAddSender:
    """Tests for add_sender function."""

    def test_add_sender_returns_sender(self) -> None:
        """Test add_sender returns an EmailSender."""
        app = FastAPI()
        sender = add_sender(app, app_name="TestApp")

        assert isinstance(sender, EmailSender)
        assert sender.app_name == "TestApp"

    def test_add_sender_stores_in_app_state(self) -> None:
        """Test add_sender stores sender in app.state."""
        app = FastAPI()
        sender = add_sender(app)

        assert app.state.email_sender is sender
        # Also stores backend for backward compat
        assert app.state.email is sender.backend

    def test_add_sender_with_branding(self) -> None:
        """Test add_sender with branding options."""
        app = FastAPI()
        sender = add_sender(
            app,
            app_name="MyApp",
            app_url="https://myapp.com",
            support_email="help@myapp.com",
        )

        assert sender.app_name == "MyApp"
        assert sender.app_url == "https://myapp.com"
        assert sender.support_email == "help@myapp.com"


# ─── get_email Dependency Tests ────────────────────────────────────────────


class TestGetEmail:
    """Tests for get_email dependency."""

    def test_get_email_in_route(self) -> None:
        """Test get_email as a route dependency."""
        app = FastAPI()
        add_email(app)

        @app.get("/test")
        async def test_route(email: EmailBackend = Depends(get_email)):
            return {"provider": email.provider_name}

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        assert response.json()["provider"] == "console"


# ─── get_sender Dependency Tests ───────────────────────────────────────────


class TestGetSender:
    """Tests for get_sender dependency."""

    def test_get_sender_in_route(self) -> None:
        """Test get_sender as a route dependency."""
        app = FastAPI()
        add_sender(app, app_name="TestApp")

        @app.get("/test")
        async def test_route(sender: EmailSender = Depends(get_sender)):
            return {"app_name": sender.app_name}

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        assert response.json()["app_name"] == "TestApp"


# ─── Health Check Tests ────────────────────────────────────────────────────


class TestHealthCheck:
    """Tests for health_check_email function."""

    @pytest.mark.asyncio
    async def test_health_check_unconfigured(self) -> None:
        """Test health check when email is not configured."""
        # Reset global state
        import svc_infra.email.add as add_module

        add_module._app_email_backend = None

        result = await health_check_email()

        assert result["status"] == "unconfigured"
        assert result["configured"] is False

    @pytest.mark.asyncio
    async def test_health_check_configured(self) -> None:
        """Test health check when email is configured."""
        app = FastAPI()
        add_email(app)

        result = await health_check_email()

        assert result["status"] == "healthy"
        assert result["configured"] is True
        assert result["provider"] == "console"

    def test_health_check_in_route(self) -> None:
        """Test health check as a route handler."""
        app = FastAPI()
        add_email(app)

        @app.get("/health/email")
        async def email_health():
            return await health_check_email()

        client = TestClient(app)
        response = client.get("/health/email")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["provider"] == "console"


# ─── Integration Tests ─────────────────────────────────────────────────────


class TestIntegration:
    """Integration tests for email module."""

    @pytest.mark.asyncio
    async def test_full_send_flow(self) -> None:
        """Test full send flow with FastAPI integration."""
        app = FastAPI()
        sender = add_sender(app, app_name="TestApp")

        # Send using sender directly with explicit from_addr
        result = await sender.send(
            to="user@example.com",
            subject="Test",
            html="<p>Hello</p>",
            from_addr="noreply@test.com",
        )

        assert result.status.value == "sent"
        assert result.provider == "console"

    def test_full_flow_with_route(self) -> None:
        """Test full flow with route handler."""
        app = FastAPI()
        add_sender(app, app_name="TestApp")

        @app.post("/send")
        async def send_email(sender: EmailSender = Depends(get_sender)):
            result = await sender.send(
                to="user@example.com",
                subject="Test",
                html="<p>Hello</p>",
                from_addr="noreply@test.com",
            )
            return {"message_id": result.message_id, "status": result.status.value}

        client = TestClient(app)
        response = client.post("/send")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"
        assert data["message_id"] is not None
