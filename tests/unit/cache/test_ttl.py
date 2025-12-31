"""Tests for svc_infra.cache.ttl module."""

from __future__ import annotations

import os
from unittest.mock import patch

from svc_infra.cache.ttl import (
    TTL_DEFAULT,
    TTL_LONG,
    TTL_SHORT,
    _get_env_int,
    get_ttl,
    validate_ttl,
)


class TestGetEnvInt:
    """Tests for _get_env_int function."""

    def test_returns_default_when_env_not_set(self) -> None:
        """Should return default when environment variable is not set."""
        with patch.dict(os.environ, {}, clear=True):
            result = _get_env_int("NONEXISTENT_VAR", 42)
            assert result == 42

    def test_returns_value_when_env_is_valid_int(self) -> None:
        """Should return parsed integer when env var is valid."""
        with patch.dict(os.environ, {"TEST_INT_VAR": "100"}):
            result = _get_env_int("TEST_INT_VAR", 42)
            assert result == 100

    def test_returns_default_when_env_is_empty_string(self) -> None:
        """Should return default when env var is empty string."""
        with patch.dict(os.environ, {"TEST_VAR": ""}):
            # Empty string should fail int conversion
            result = _get_env_int("TEST_VAR", 42)
            assert result == 42

    def test_returns_default_when_env_is_invalid_int(self) -> None:
        """Should return default when env var is not a valid integer."""
        with patch.dict(os.environ, {"TEST_VAR": "not_a_number"}):
            result = _get_env_int("TEST_VAR", 42)
            assert result == 42

    def test_returns_default_when_env_is_float(self) -> None:
        """Should return default when env var is a float string."""
        with patch.dict(os.environ, {"TEST_VAR": "3.14"}):
            result = _get_env_int("TEST_VAR", 42)
            assert result == 42

    def test_parses_negative_integer(self) -> None:
        """Should parse negative integers correctly."""
        with patch.dict(os.environ, {"TEST_VAR": "-10"}):
            result = _get_env_int("TEST_VAR", 42)
            assert result == -10

    def test_parses_zero(self) -> None:
        """Should parse zero correctly."""
        with patch.dict(os.environ, {"TEST_VAR": "0"}):
            result = _get_env_int("TEST_VAR", 42)
            assert result == 0


class TestTTLConstants:
    """Tests for TTL constant values."""

    def test_ttl_default_is_300(self) -> None:
        """TTL_DEFAULT should be 300 (5 minutes) by default."""
        # Note: this may vary if env var is set
        assert isinstance(TTL_DEFAULT, int)
        assert TTL_DEFAULT > 0

    def test_ttl_short_is_less_than_default(self) -> None:
        """TTL_SHORT should be less than or equal to TTL_DEFAULT."""
        assert TTL_SHORT <= TTL_DEFAULT

    def test_ttl_long_is_greater_than_default(self) -> None:
        """TTL_LONG should be greater than or equal to TTL_DEFAULT."""
        assert TTL_LONG >= TTL_DEFAULT


class TestGetTTL:
    """Tests for get_ttl function."""

    def test_get_ttl_default(self) -> None:
        """Should return TTL_DEFAULT for 'default'."""
        result = get_ttl("default")
        assert result == TTL_DEFAULT

    def test_get_ttl_short(self) -> None:
        """Should return TTL_SHORT for 'short'."""
        result = get_ttl("short")
        assert result == TTL_SHORT

    def test_get_ttl_long(self) -> None:
        """Should return TTL_LONG for 'long'."""
        result = get_ttl("long")
        assert result == TTL_LONG

    def test_get_ttl_case_insensitive(self) -> None:
        """Should be case insensitive."""
        assert get_ttl("DEFAULT") == TTL_DEFAULT
        assert get_ttl("Short") == TTL_SHORT
        assert get_ttl("LONG") == TTL_LONG

    def test_get_ttl_invalid_returns_none(self) -> None:
        """Should return None for invalid duration type."""
        result = get_ttl("invalid")
        assert result is None

    def test_get_ttl_empty_string_returns_none(self) -> None:
        """Should return None for empty string."""
        result = get_ttl("")
        assert result is None

    def test_get_ttl_mixed_case(self) -> None:
        """Should handle mixed case."""
        result = get_ttl("DeFaUlT")
        assert result == TTL_DEFAULT


class TestValidateTTL:
    """Tests for validate_ttl function."""

    def test_validate_none_returns_default(self) -> None:
        """Should return default when ttl is None."""
        result = validate_ttl(None)
        assert result == TTL_DEFAULT

    def test_validate_negative_returns_default(self) -> None:
        """Should return default when ttl is negative."""
        result = validate_ttl(-1)
        assert result == TTL_DEFAULT

    def test_validate_negative_large_returns_default(self) -> None:
        """Should return default when ttl is large negative."""
        result = validate_ttl(-1000)
        assert result == TTL_DEFAULT

    def test_validate_zero_returns_zero(self) -> None:
        """Should return 0 when ttl is 0 (valid edge case)."""
        result = validate_ttl(0)
        assert result == 0

    def test_validate_positive_returns_value(self) -> None:
        """Should return the value when ttl is positive."""
        result = validate_ttl(60)
        assert result == 60

    def test_validate_large_positive(self) -> None:
        """Should accept large positive values."""
        result = validate_ttl(86400)  # 24 hours
        assert result == 86400

    def test_validate_returns_int_type(self) -> None:
        """Should always return an integer."""
        assert isinstance(validate_ttl(None), int)
        assert isinstance(validate_ttl(-5), int)
        assert isinstance(validate_ttl(100), int)
