"""Tests for webhooks and websocket modules - Coverage improvement."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

from svc_infra.webhooks import (
    add_webhooks,
    decrypt_secret,
    encrypt_secret,
    is_encrypted,
    trigger_webhook,
)

# ─── trigger_webhook Tests ─────────────────────────────────────────────────


class TestTriggerWebhook:
    """Tests for trigger_webhook function."""

    @pytest.mark.asyncio
    async def test_no_webhook_service(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test trigger_webhook with no service."""
        with caplog.at_level(logging.WARNING):
            result = await trigger_webhook("user.created", {"id": 1})

        assert result is None
        assert "No webhook_service provided" in caplog.text

    @pytest.mark.asyncio
    async def test_with_webhook_service(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test trigger_webhook with service."""
        mock_service = MagicMock()
        mock_service.publish.return_value = 42

        with caplog.at_level(logging.INFO):
            result = await trigger_webhook("user.created", {"id": 1}, webhook_service=mock_service)

        assert result == 42
        mock_service.publish.assert_called_once_with("user.created", {"id": 1})
        assert "Triggered webhook event" in caplog.text

    @pytest.mark.asyncio
    async def test_service_exception(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test trigger_webhook when service raises."""
        mock_service = MagicMock()
        mock_service.publish.side_effect = RuntimeError("publish failed")

        with caplog.at_level(logging.ERROR):
            result = await trigger_webhook("user.deleted", {"id": 2}, webhook_service=mock_service)

        assert result is None
        assert "Failed to trigger webhook event" in caplog.text


# ─── Webhook Module Exports Tests ──────────────────────────────────────────


class TestWebhookExports:
    """Tests for webhook module exports."""

    def test_add_webhooks_exported(self) -> None:
        """Test add_webhooks is exported."""
        assert callable(add_webhooks)

    def test_encryption_functions_exported(self) -> None:
        """Test encryption functions are exported."""
        assert callable(encrypt_secret)
        assert callable(decrypt_secret)
        assert callable(is_encrypted)
