"""Unit tests for svc_infra.websocket.easy module."""

from __future__ import annotations

from svc_infra.websocket.client import WebSocketClient
from svc_infra.websocket.easy import easy_websocket_client, websocket_client


class TestWebsocketClient:
    """Tests for websocket_client function."""

    def test_basic_creation(self) -> None:
        """Test basic client creation with URL."""
        client = websocket_client("wss://example.com/ws")
        assert isinstance(client, WebSocketClient)
        assert client.url == "wss://example.com/ws"

    def test_with_headers(self) -> None:
        """Test client creation with custom headers."""
        headers = {"Authorization": "Bearer token123"}
        client = websocket_client("wss://example.com/ws", headers=headers)
        assert client.headers == headers

    def test_with_subprotocols(self) -> None:
        """Test client creation with subprotocols."""
        subprotocols = ["graphql-ws", "subscriptions-transport-ws"]
        client = websocket_client("wss://example.com/ws", subprotocols=subprotocols)
        assert client.subprotocols == subprotocols

    def test_with_config_overrides(self) -> None:
        """Test client creation with config overrides."""
        client = websocket_client(
            "wss://example.com/ws",
            ping_interval=30,
            max_message_size=1024 * 1024,
        )
        assert client.config.ping_interval == 30
        assert client.config.max_message_size == 1024 * 1024

    def test_combined_options(self) -> None:
        """Test client with all options combined."""
        client = websocket_client(
            "wss://example.com/ws",
            headers={"X-Custom": "value"},
            subprotocols=["custom-protocol"],
            open_timeout=10,
        )
        assert isinstance(client, WebSocketClient)
        assert client.headers == {"X-Custom": "value"}
        assert client.subprotocols == ["custom-protocol"]
        assert client.config.open_timeout == 10

    def test_no_config_overrides(self) -> None:
        """Test client with no config overrides uses defaults."""
        client = websocket_client("wss://example.com/ws")
        # Should use default config values
        assert client.config is not None


class TestEasyWebsocketClientAlias:
    """Tests for backward compatibility alias."""

    def test_alias_is_same_function(self) -> None:
        """Test easy_websocket_client is alias for websocket_client."""
        assert easy_websocket_client is websocket_client

    def test_alias_works(self) -> None:
        """Test alias creates client correctly."""
        client = easy_websocket_client("wss://example.com/ws")
        assert isinstance(client, WebSocketClient)
