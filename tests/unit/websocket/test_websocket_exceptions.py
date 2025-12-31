"""Tests for svc_infra.websocket.exceptions module."""

from __future__ import annotations

import pytest

from svc_infra.websocket.exceptions import (
    AuthenticationError,
    ConnectionClosedError,
    ConnectionFailedError,
    MessageTooLargeError,
    WebSocketError,
)


class TestWebSocketError:
    """Tests for WebSocketError base exception."""

    def test_is_exception(self) -> None:
        """Should be an Exception subclass."""
        assert issubclass(WebSocketError, Exception)

    def test_can_be_raised(self) -> None:
        """Should be raisable."""
        with pytest.raises(WebSocketError):
            raise WebSocketError("test error")

    def test_message_is_preserved(self) -> None:
        """Should preserve error message."""
        error = WebSocketError("test message")
        assert str(error) == "test message"

    def test_empty_message(self) -> None:
        """Should handle empty message."""
        error = WebSocketError("")
        assert str(error) == ""

    def test_no_args(self) -> None:
        """Should handle no arguments."""
        error = WebSocketError()
        assert str(error) == ""


class TestConnectionClosedError:
    """Tests for ConnectionClosedError exception."""

    def test_inherits_websocket_error(self) -> None:
        """Should inherit from WebSocketError."""
        assert issubclass(ConnectionClosedError, WebSocketError)

    def test_default_code_is_none(self) -> None:
        """Should have None code by default."""
        error = ConnectionClosedError()
        assert error.code is None

    def test_default_reason_is_empty(self) -> None:
        """Should have empty reason by default."""
        error = ConnectionClosedError()
        assert error.reason == ""

    def test_stores_code(self) -> None:
        """Should store close code."""
        error = ConnectionClosedError(code=1000)
        assert error.code == 1000

    def test_stores_reason(self) -> None:
        """Should store reason."""
        error = ConnectionClosedError(reason="Normal closure")
        assert error.reason == "Normal closure"

    def test_stores_code_and_reason(self) -> None:
        """Should store both code and reason."""
        error = ConnectionClosedError(code=1006, reason="Abnormal closure")
        assert error.code == 1006
        assert error.reason == "Abnormal closure"

    def test_message_includes_code(self) -> None:
        """Should include code in message."""
        error = ConnectionClosedError(code=1000)
        assert "1000" in str(error)

    def test_message_includes_reason(self) -> None:
        """Should include reason in message."""
        error = ConnectionClosedError(reason="Server shutdown")
        assert "Server shutdown" in str(error)

    def test_message_format_with_both(self) -> None:
        """Should format message with code and reason."""
        error = ConnectionClosedError(code=1001, reason="Going away")
        message = str(error)
        assert "1001" in message
        assert "Going away" in message
        assert "Connection closed" in message

    def test_catch_as_websocket_error(self) -> None:
        """Should be catchable as WebSocketError."""
        with pytest.raises(WebSocketError):
            raise ConnectionClosedError(code=1000)

    def test_normal_close_code(self) -> None:
        """Should handle normal close code 1000."""
        error = ConnectionClosedError(code=1000, reason="Normal closure")
        assert error.code == 1000

    def test_abnormal_close_code(self) -> None:
        """Should handle abnormal close code 1006."""
        error = ConnectionClosedError(code=1006, reason="Connection lost")
        assert error.code == 1006


class TestConnectionFailedError:
    """Tests for ConnectionFailedError exception."""

    def test_inherits_websocket_error(self) -> None:
        """Should inherit from WebSocketError."""
        assert issubclass(ConnectionFailedError, WebSocketError)

    def test_can_be_raised(self) -> None:
        """Should be raisable."""
        with pytest.raises(ConnectionFailedError):
            raise ConnectionFailedError("Failed to connect")

    def test_message_is_preserved(self) -> None:
        """Should preserve error message."""
        error = ConnectionFailedError("Connection refused")
        assert str(error) == "Connection refused"

    def test_catch_as_websocket_error(self) -> None:
        """Should be catchable as WebSocketError."""
        with pytest.raises(WebSocketError):
            raise ConnectionFailedError("Network error")


class TestAuthenticationError:
    """Tests for AuthenticationError exception."""

    def test_inherits_websocket_error(self) -> None:
        """Should inherit from WebSocketError."""
        assert issubclass(AuthenticationError, WebSocketError)

    def test_can_be_raised(self) -> None:
        """Should be raisable."""
        with pytest.raises(AuthenticationError):
            raise AuthenticationError("Invalid token")

    def test_message_is_preserved(self) -> None:
        """Should preserve error message."""
        error = AuthenticationError("JWT expired")
        assert str(error) == "JWT expired"

    def test_catch_as_websocket_error(self) -> None:
        """Should be catchable as WebSocketError."""
        with pytest.raises(WebSocketError):
            raise AuthenticationError("Missing credentials")


class TestMessageTooLargeError:
    """Tests for MessageTooLargeError exception."""

    def test_inherits_websocket_error(self) -> None:
        """Should inherit from WebSocketError."""
        assert issubclass(MessageTooLargeError, WebSocketError)

    def test_can_be_raised(self) -> None:
        """Should be raisable."""
        with pytest.raises(MessageTooLargeError):
            raise MessageTooLargeError("Message exceeds 1MB limit")

    def test_message_is_preserved(self) -> None:
        """Should preserve error message."""
        error = MessageTooLargeError("Size: 5MB, Max: 1MB")
        assert str(error) == "Size: 5MB, Max: 1MB"

    def test_catch_as_websocket_error(self) -> None:
        """Should be catchable as WebSocketError."""
        with pytest.raises(WebSocketError):
            raise MessageTooLargeError("Too large")


class TestExceptionHierarchy:
    """Tests for the exception hierarchy."""

    def test_all_inherit_from_websocket_error(self) -> None:
        """All exceptions should inherit from WebSocketError."""
        exceptions = [
            ConnectionClosedError,
            ConnectionFailedError,
            AuthenticationError,
            MessageTooLargeError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, WebSocketError)
            assert issubclass(exc_class, Exception)

    def test_different_exception_types(self) -> None:
        """Different exception types should not be identical."""
        assert ConnectionClosedError is not ConnectionFailedError
        assert AuthenticationError is not MessageTooLargeError
        assert ConnectionClosedError is not WebSocketError

    def test_can_catch_all_with_base_class(self) -> None:
        """Should be able to catch all with WebSocketError."""
        exceptions = [
            ConnectionClosedError(code=1000),
            ConnectionFailedError("Failed"),
            AuthenticationError("Auth failed"),
            MessageTooLargeError("Too large"),
        ]
        for exc in exceptions:
            with pytest.raises(WebSocketError):
                raise exc
