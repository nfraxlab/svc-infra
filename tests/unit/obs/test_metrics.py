"""Unit tests for svc_infra.obs.metrics module."""

from __future__ import annotations

from svc_infra.obs import metrics


class TestEmitRateLimited:
    """Tests for emit_rate_limited function."""

    def test_no_op_when_handler_not_set(self) -> None:
        """Test that function does nothing when handler is not set."""
        original = metrics.on_rate_limit_exceeded
        try:
            metrics.on_rate_limit_exceeded = None
            # Should not raise
            metrics.emit_rate_limited("test_key", 100, 60)
        finally:
            metrics.on_rate_limit_exceeded = original

    def test_calls_handler_when_set(self) -> None:
        """Test that handler is called with correct arguments."""
        called_with = []

        def handler(key: str, limit: int, retry_after: int):
            called_with.append((key, limit, retry_after))

        original = metrics.on_rate_limit_exceeded
        try:
            metrics.on_rate_limit_exceeded = handler
            metrics.emit_rate_limited("api_key_123", 100, 30)
        finally:
            metrics.on_rate_limit_exceeded = original

        assert len(called_with) == 1
        assert called_with[0] == ("api_key_123", 100, 30)

    def test_swallows_handler_exceptions(self) -> None:
        """Test that exceptions in handler are swallowed."""

        def failing_handler(key: str, limit: int, retry_after: int):
            raise ValueError("Handler failed")

        original = metrics.on_rate_limit_exceeded
        try:
            metrics.on_rate_limit_exceeded = failing_handler
            # Should not raise
            metrics.emit_rate_limited("test_key", 100, 60)
        finally:
            metrics.on_rate_limit_exceeded = original


class TestEmitSuspectPayload:
    """Tests for emit_suspect_payload function."""

    def test_no_op_when_handler_not_set(self) -> None:
        """Test that function does nothing when handler is not set."""
        original = metrics.on_suspect_payload
        try:
            metrics.on_suspect_payload = None
            # Should not raise
            metrics.emit_suspect_payload("/api/upload", 1000000)
        finally:
            metrics.on_suspect_payload = original

    def test_calls_handler_when_set(self) -> None:
        """Test that handler is called with correct arguments."""
        called_with = []

        def handler(path: str | None, size: int):
            called_with.append((path, size))

        original = metrics.on_suspect_payload
        try:
            metrics.on_suspect_payload = handler
            metrics.emit_suspect_payload("/api/large", 5000000)
        finally:
            metrics.on_suspect_payload = original

        assert len(called_with) == 1
        assert called_with[0] == ("/api/large", 5000000)

    def test_handles_none_path(self) -> None:
        """Test that None path is handled correctly."""
        called_with = []

        def handler(path: str | None, size: int):
            called_with.append((path, size))

        original = metrics.on_suspect_payload
        try:
            metrics.on_suspect_payload = handler
            metrics.emit_suspect_payload(None, 1000)
        finally:
            metrics.on_suspect_payload = original

        assert called_with[0] == (None, 1000)

    def test_swallows_handler_exceptions(self) -> None:
        """Test that exceptions in handler are swallowed."""

        def failing_handler(path: str | None, size: int):
            raise RuntimeError("Handler crashed")

        original = metrics.on_suspect_payload
        try:
            metrics.on_suspect_payload = failing_handler
            # Should not raise
            metrics.emit_suspect_payload("/test", 100)
        finally:
            metrics.on_suspect_payload = original
