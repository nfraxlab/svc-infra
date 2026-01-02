"""Tests for websocket/add.py - Coverage improvement."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from svc_infra.websocket.add import (
    add_websocket_manager,
    get_ws_manager,
    get_ws_manager_dependency,
)
from svc_infra.websocket.manager import ConnectionManager

# ─── add_websocket_manager Tests ───────────────────────────────────────────


class TestAddWebsocketManager:
    """Tests for add_websocket_manager function."""

    def test_creates_manager(self) -> None:
        """Test that manager is created when not provided."""
        mock_app = MagicMock()
        mock_app.state = MagicMock()

        manager = add_websocket_manager(mock_app)

        assert isinstance(manager, ConnectionManager)

    def test_uses_provided_manager(self) -> None:
        """Test that provided manager is used."""
        mock_app = MagicMock()
        mock_app.state = MagicMock()
        custom_manager = ConnectionManager()

        manager = add_websocket_manager(mock_app, manager=custom_manager)

        assert manager is custom_manager

    def test_stores_on_app_state(self) -> None:
        """Test that manager is stored on app state."""
        mock_app = MagicMock()
        mock_app.state = MagicMock()

        add_websocket_manager(mock_app)

        # Check that setattr was called
        assert hasattr(mock_app.state, "_svc_infra_ws_manager")


# ─── get_ws_manager Tests ──────────────────────────────────────────────────


class TestGetWsManager:
    """Tests for get_ws_manager function."""

    def test_from_app(self) -> None:
        """Test getting manager from FastAPI app."""
        mock_app = MagicMock()
        mock_app.state = MagicMock()
        expected_manager = ConnectionManager()
        mock_app.state._svc_infra_ws_manager = expected_manager
        # Ensure app doesn't have .app attribute
        del mock_app.app

        manager = get_ws_manager(mock_app)

        assert manager is expected_manager

    def test_from_request(self) -> None:
        """Test getting manager from Request object."""
        mock_manager = ConnectionManager()
        mock_app = MagicMock()
        mock_app.state._svc_infra_ws_manager = mock_manager

        mock_request = MagicMock()
        mock_request.app = mock_app

        manager = get_ws_manager(mock_request)

        assert manager is mock_manager

    def test_raises_when_not_configured(self) -> None:
        """Test raises RuntimeError when manager not configured."""
        mock_app = MagicMock()
        mock_app.state._svc_infra_ws_manager = None
        del mock_app.app  # Ensure it's treated as app not request

        with pytest.raises(RuntimeError) as exc_info:
            get_ws_manager(mock_app)

        assert "WebSocket manager not found" in str(exc_info.value)


# ─── get_ws_manager_dependency Tests ───────────────────────────────────────


class TestGetWsManagerDependency:
    """Tests for get_ws_manager_dependency function."""

    def test_returns_manager(self) -> None:
        """Test dependency returns manager."""
        mock_manager = ConnectionManager()
        mock_app = MagicMock()
        mock_app.state._svc_infra_ws_manager = mock_manager

        mock_request = MagicMock()
        mock_request.app = mock_app

        manager = get_ws_manager_dependency(mock_request)

        assert manager is mock_manager
