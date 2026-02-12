"""Tests for the auto-mounted /status endpoint."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from svc_infra.api.fastapi.routers.status import (
    ROUTER_EXCLUDED_ENVIRONMENTS,
    _format_uptime,
    _get_commit,
)
from svc_infra.app.env import PROD_ENV


class TestStatusRouterConfig:
    """Verify module-level configuration constants."""

    def test_excluded_from_production(self) -> None:
        assert PROD_ENV in ROUTER_EXCLUDED_ENVIRONMENTS


class TestFormatUptime:
    """Tests for _format_uptime helper."""

    def test_seconds_only(self) -> None:
        assert _format_uptime(45) == "45s"

    def test_minutes_and_seconds(self) -> None:
        assert _format_uptime(125) == "2m 5s"

    def test_hours_minutes_seconds(self) -> None:
        assert _format_uptime(3661) == "1h 1m 1s"

    def test_days(self) -> None:
        assert _format_uptime(90061) == "1d 1h 1m 1s"

    def test_zero(self) -> None:
        assert _format_uptime(0) == "0s"


class TestGetCommit:
    """Tests for _get_commit CI/CD env var detection."""

    def test_returns_none_locally(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No commit shown when no CI/CD env vars are set."""
        for var in (
            "GIT_COMMIT",
            "RAILWAY_GIT_COMMIT_SHA",
            "VERCEL_GIT_COMMIT_SHA",
            "RENDER_GIT_COMMIT",
            "HEROKU_SLUG_COMMIT",
        ):
            monkeypatch.delenv(var, raising=False)
        assert _get_commit() is None

    def test_reads_git_commit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GIT_COMMIT", "abc123def456789")
        assert _get_commit() == "abc123def456"

    def test_reads_railway_sha(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GIT_COMMIT", raising=False)
        monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "deadbeef12345678")
        assert _get_commit() == "deadbeef1234"

    def test_truncates_to_12_chars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GIT_COMMIT", "a" * 40)
        assert _get_commit() == "a" * 12


class TestStatusEndpoint:
    """Integration tests for the /status route via TestClient."""

    _PATCH_ROOT = "svc_infra.api.fastapi.setup.get_root_app"

    def _make_app(self):
        """Create a minimal app with the status router."""
        from fastapi import FastAPI

        from svc_infra.api.fastapi.routers.status import router

        app = FastAPI(title="test-svc", version="1.2.3")
        app.include_router(router)
        return app

    def test_returns_200(self) -> None:
        app = self._make_app()
        with patch(self._PATCH_ROOT, return_value=app):
            with TestClient(app) as c:
                r = c.get("/status")
                assert r.status_code == 200

    def test_response_has_required_fields(self) -> None:
        app = self._make_app()
        with patch(self._PATCH_ROOT, return_value=app):
            with TestClient(app) as c:
                data = c.get("/status").json()
                assert data["status"] == "ok"
                assert data["service"] == "test-svc"
                assert data["version"] == "1.2.3"
                assert "env" in data
                assert "python" in data
                assert "uptime" in data
                assert "started_at" in data
                assert "timestamp" in data

    def test_includes_commit_when_ci_env_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "abc123456789abcdef")
        app = self._make_app()
        with patch(self._PATCH_ROOT, return_value=app):
            with TestClient(app) as c:
                data = c.get("/status").json()
                assert data["commit"] == "abc123456789"

    def test_no_commit_field_locally(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for var in (
            "GIT_COMMIT",
            "RAILWAY_GIT_COMMIT_SHA",
            "VERCEL_GIT_COMMIT_SHA",
            "RENDER_GIT_COMMIT",
            "HEROKU_SLUG_COMMIT",
        ):
            monkeypatch.delenv(var, raising=False)
        app = self._make_app()
        with patch(self._PATCH_ROOT, return_value=app):
            with TestClient(app) as c:
                data = c.get("/status").json()
                assert "commit" not in data

    def test_fallback_when_no_root_app(self) -> None:
        app = self._make_app()
        with patch(self._PATCH_ROOT, return_value=None):
            with TestClient(app) as c:
                data = c.get("/status").json()
                assert data["service"] == "unknown"
                assert data["version"] == "unknown"
