"""Tests for svc_infra.db.sql.apikey module."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from svc_infra.db.sql import apikey as apikey_module


class TestGetApikeySecret:
    """Tests for _get_apikey_secret function."""

    def test_returns_env_secret(self) -> None:
        """Returns secret from environment variable."""
        with patch.dict(os.environ, {"APIKEY_HASH_SECRET": "my-secret-key"}):
            result = apikey_module._get_apikey_secret()
            assert result == "my-secret-key"

    def test_returns_dev_default_when_missing_in_dev(self) -> None:
        """Returns dev default when missing in development."""
        # In non-production without secret, should use dev default
        with patch.dict(os.environ, {"APIKEY_HASH_SECRET": ""}, clear=False):
            with patch.dict(os.environ, {"ENV": "development"}):
                result = apikey_module._get_apikey_secret()
                assert "dev-only" in result


class TestHmacSha256:
    """Tests for _hmac_sha256 function."""

    def test_produces_64_char_hex(self) -> None:
        """Produces 64 character hex string."""
        with patch.object(apikey_module, "_get_apikey_secret", return_value="test-secret"):
            result = apikey_module._hmac_sha256("test-input")
            assert len(result) == 64
            assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic_output(self) -> None:
        """Same input produces same output."""
        with patch.object(apikey_module, "_get_apikey_secret", return_value="test-secret"):
            result1 = apikey_module._hmac_sha256("test-input")
            result2 = apikey_module._hmac_sha256("test-input")
            assert result1 == result2

    def test_different_inputs_different_outputs(self) -> None:
        """Different inputs produce different outputs."""
        with patch.object(apikey_module, "_get_apikey_secret", return_value="test-secret"):
            result1 = apikey_module._hmac_sha256("input-a")
            result2 = apikey_module._hmac_sha256("input-b")
            assert result1 != result2


class TestNow:
    """Tests for _now function."""

    def test_returns_utc_datetime(self) -> None:
        """Returns datetime with UTC timezone."""
        result = apikey_module._now()
        assert result.tzinfo == UTC

    def test_returns_current_time(self) -> None:
        """Returns approximately current time."""
        before = datetime.now(UTC)
        result = apikey_module._now()
        after = datetime.now(UTC)
        assert before <= result <= after


class TestGetApikeyModel:
    """Tests for get_apikey_model function."""

    def test_raises_when_not_bound(self) -> None:
        """Raises RuntimeError when model not bound."""
        # Reset the global
        original = apikey_module._ApiKeyModel
        try:
            apikey_module._ApiKeyModel = None
            with pytest.raises(RuntimeError, match="not enabled"):
                apikey_module.get_apikey_model()
        finally:
            apikey_module._ApiKeyModel = original

    def test_returns_model_when_bound(self) -> None:
        """Returns model when bound."""
        original = apikey_module._ApiKeyModel
        mock_model = MagicMock()
        try:
            apikey_module._ApiKeyModel = mock_model
            result = apikey_module.get_apikey_model()
            assert result is mock_model
        finally:
            apikey_module._ApiKeyModel = original


class TestTryAutobindApikeyModel:
    """Tests for try_autobind_apikey_model function."""

    def test_returns_existing_model_if_bound(self) -> None:
        """Returns existing model if already bound."""
        original = apikey_module._ApiKeyModel
        mock_model = MagicMock()
        try:
            apikey_module._ApiKeyModel = mock_model
            result = apikey_module.try_autobind_apikey_model()
            assert result is mock_model
        finally:
            apikey_module._ApiKeyModel = original

    def test_returns_none_when_env_required_but_missing(self) -> None:
        """Returns None when require_env=True but env var missing."""
        original = apikey_module._ApiKeyModel
        try:
            apikey_module._ApiKeyModel = None
            with patch.dict(os.environ, {"AUTH_ENABLE_API_KEYS": ""}, clear=False):
                result = apikey_module.try_autobind_apikey_model(require_env=True)
                assert result is None
        finally:
            apikey_module._ApiKeyModel = original

    def test_returns_none_when_env_required_and_false(self) -> None:
        """Returns None when require_env=True and env var is false."""
        original = apikey_module._ApiKeyModel
        try:
            apikey_module._ApiKeyModel = None
            for val in ["0", "false", "no", "FALSE", "No"]:
                with patch.dict(os.environ, {"AUTH_ENABLE_API_KEYS": val}):
                    result = apikey_module.try_autobind_apikey_model(require_env=True)
                    assert result is None
        finally:
            apikey_module._ApiKeyModel = original
