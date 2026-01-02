"""Tests for obs/metrics.py - Coverage improvement."""

from __future__ import annotations

from unittest.mock import MagicMock

import svc_infra.obs.metrics as metrics_module

# ─── emit_rate_limited Tests ───────────────────────────────────────────────


class TestEmitRateLimited:
    """Tests for emit_rate_limited function."""

    def test_no_handler(self) -> None:
        """Test emit_rate_limited when no handler is set."""
        original = metrics_module.on_rate_limit_exceeded
        try:
            metrics_module.on_rate_limit_exceeded = None
            # Should not raise
            metrics_module.emit_rate_limited("key123", 100, 60)
        finally:
            metrics_module.on_rate_limit_exceeded = original

    def test_with_handler(self) -> None:
        """Test emit_rate_limited calls handler."""
        original = metrics_module.on_rate_limit_exceeded
        handler = MagicMock()
        try:
            metrics_module.on_rate_limit_exceeded = handler
            metrics_module.emit_rate_limited("api-key-xyz", 50, 30)
            handler.assert_called_once_with("api-key-xyz", 50, 30)
        finally:
            metrics_module.on_rate_limit_exceeded = original

    def test_handler_exception_swallowed(self) -> None:
        """Test that handler exceptions are swallowed."""
        original = metrics_module.on_rate_limit_exceeded

        def bad_handler(key: str, limit: int, retry_after: int) -> None:
            raise RuntimeError("handler failed")

        try:
            metrics_module.on_rate_limit_exceeded = bad_handler
            # Should not raise
            metrics_module.emit_rate_limited("key", 10, 5)
        finally:
            metrics_module.on_rate_limit_exceeded = original


# ─── emit_suspect_payload Tests ────────────────────────────────────────────


class TestEmitSuspectPayload:
    """Tests for emit_suspect_payload function."""

    def test_no_handler(self) -> None:
        """Test emit_suspect_payload when no handler is set."""
        original = metrics_module.on_suspect_payload
        try:
            metrics_module.on_suspect_payload = None
            # Should not raise
            metrics_module.emit_suspect_payload("/api/upload", 10_000_000)
        finally:
            metrics_module.on_suspect_payload = original

    def test_with_handler(self) -> None:
        """Test emit_suspect_payload calls handler."""
        original = metrics_module.on_suspect_payload
        handler = MagicMock()
        try:
            metrics_module.on_suspect_payload = handler
            metrics_module.emit_suspect_payload("/api/data", 5_000_000)
            handler.assert_called_once_with("/api/data", 5_000_000)
        finally:
            metrics_module.on_suspect_payload = original

    def test_with_none_path(self) -> None:
        """Test emit_suspect_payload with None path."""
        original = metrics_module.on_suspect_payload
        handler = MagicMock()
        try:
            metrics_module.on_suspect_payload = handler
            metrics_module.emit_suspect_payload(None, 1_000_000)
            handler.assert_called_once_with(None, 1_000_000)
        finally:
            metrics_module.on_suspect_payload = original

    def test_handler_exception_swallowed(self) -> None:
        """Test that handler exceptions are swallowed."""
        original = metrics_module.on_suspect_payload

        def bad_handler(path: str | None, size: int) -> None:
            raise ValueError("handler exploded")

        try:
            metrics_module.on_suspect_payload = bad_handler
            # Should not raise
            metrics_module.emit_suspect_payload("/path", 999)
        finally:
            metrics_module.on_suspect_payload = original


# ─── Module Exports Tests ──────────────────────────────────────────────────


class TestModuleExports:
    """Tests for module __all__ exports."""

    def test_all_exports(self) -> None:
        """Test that __all__ contains expected exports."""
        assert "emit_rate_limited" in metrics_module.__all__
        assert "emit_suspect_payload" in metrics_module.__all__
        assert "on_rate_limit_exceeded" in metrics_module.__all__
        assert "on_suspect_payload" in metrics_module.__all__
