"""Tests for websocket/easy.py - Coverage improvement."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from svc_infra.websocket.easy import easy_websocket_client, websocket_client

# ─── websocket_client Tests ────────────────────────────────────────────────


class TestWebsocketClient:
    """Tests for websocket_client factory."""

    @patch("svc_infra.websocket.easy.get_default_config")
    @patch("svc_infra.websocket.easy.WebSocketClient")
    def test_basic_call(self, mock_client_cls: MagicMock, mock_get_config: MagicMock) -> None:
        """Test basic websocket_client call."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        websocket_client("wss://example.com/ws")

        mock_client_cls.assert_called_once_with(
            "wss://example.com/ws",
            config=mock_config,
            headers=None,
            subprotocols=None,
        )

    @patch("svc_infra.websocket.easy.get_default_config")
    @patch("svc_infra.websocket.easy.WebSocketClient")
    def test_with_headers(self, mock_client_cls: MagicMock, mock_get_config: MagicMock) -> None:
        """Test websocket_client with headers."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        headers = {"Authorization": "Bearer token"}
        websocket_client("wss://api.example.com", headers=headers)

        mock_client_cls.assert_called_once()
        call_kwargs = mock_client_cls.call_args.kwargs
        assert call_kwargs["headers"] == headers

    @patch("svc_infra.websocket.easy.get_default_config")
    @patch("svc_infra.websocket.easy.WebSocketClient")
    def test_with_subprotocols(
        self, mock_client_cls: MagicMock, mock_get_config: MagicMock
    ) -> None:
        """Test websocket_client with subprotocols."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        subprotocols = ["graphql-transport-ws"]
        websocket_client("wss://api.example.com", subprotocols=subprotocols)

        mock_client_cls.assert_called_once()
        call_kwargs = mock_client_cls.call_args.kwargs
        assert call_kwargs["subprotocols"] == subprotocols

    @patch("svc_infra.websocket.easy.WebSocketConfig")
    @patch("svc_infra.websocket.easy.get_default_config")
    @patch("svc_infra.websocket.easy.WebSocketClient")
    def test_with_config_overrides(
        self,
        mock_client_cls: MagicMock,
        mock_get_config: MagicMock,
        mock_config_cls: MagicMock,
    ) -> None:
        """Test websocket_client with config overrides."""
        mock_config = MagicMock()
        mock_config.model_dump.return_value = {"ping_interval": 30, "timeout": 60}
        mock_get_config.return_value = mock_config

        mock_new_config = MagicMock()
        mock_config_cls.return_value = mock_new_config

        websocket_client("wss://api.example.com", ping_interval=15, timeout=120)

        # Should create new config with overrides
        mock_config_cls.assert_called_once_with(ping_interval=15, timeout=120)
        mock_client_cls.assert_called_once()
        call_kwargs = mock_client_cls.call_args.kwargs
        assert call_kwargs["config"] == mock_new_config


# ─── Alias Tests ───────────────────────────────────────────────────────────


class TestAliases:
    """Tests for backward compatibility aliases."""

    def test_easy_websocket_client_alias(self) -> None:
        """Test easy_websocket_client is alias for websocket_client."""
        assert easy_websocket_client is websocket_client
