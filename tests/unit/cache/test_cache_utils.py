"""Tests for svc_infra.cache.utils module."""

from __future__ import annotations

import pytest

from svc_infra.cache.utils import (
    format_tuple_key,
    join_key,
    normalize_cache_key,
    stable_hash,
    validate_cache_key,
)


class TestStableHash:
    """Tests for stable_hash function."""

    def test_returns_hex_string(self) -> None:
        """Returns a hexadecimal string."""
        result = stable_hash("test")
        assert isinstance(result, str)
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic(self) -> None:
        """Same input produces same output."""
        result1 = stable_hash("test", 123, key="value")
        result2 = stable_hash("test", 123, key="value")
        assert result1 == result2

    def test_different_args_different_hash(self) -> None:
        """Different args produce different hash."""
        result1 = stable_hash("test")
        result2 = stable_hash("other")
        assert result1 != result2

    def test_different_kwargs_different_hash(self) -> None:
        """Different kwargs produce different hash."""
        result1 = stable_hash("test", key="a")
        result2 = stable_hash("test", key="b")
        assert result1 != result2

    def test_handles_complex_types(self) -> None:
        """Handles complex types like dicts and lists."""
        result = stable_hash({"key": "value"}, [1, 2, 3])
        assert isinstance(result, str)
        assert len(result) > 0

    def test_handles_non_json_serializable(self) -> None:
        """Falls back to repr for non-JSON-serializable objects."""

        class CustomObj:
            pass

        result = stable_hash(CustomObj())
        assert isinstance(result, str)
        assert len(result) > 0


class TestJoinKey:
    """Tests for join_key function."""

    def test_joins_strings(self) -> None:
        """Joins string parts with colons."""
        result = join_key(["user", "123", "profile"])
        assert result == "user:123:profile"

    def test_converts_integers(self) -> None:
        """Converts integers to strings."""
        result = join_key(["user", 123, "profile"])
        assert result == "user:123:profile"

    def test_filters_none_values(self) -> None:
        """Filters out None values."""
        result = join_key(["user", None, "profile"])
        assert result == "user:profile"

    def test_filters_empty_strings(self) -> None:
        """Filters out empty strings."""
        result = join_key(["user", "", "profile"])
        assert result == "user:profile"

    def test_strips_colons_from_parts(self) -> None:
        """Strips leading/trailing colons from parts."""
        result = join_key([":user:", ":123:", "profile:"])
        assert result == "user:123:profile"

    def test_empty_parts_return_empty(self) -> None:
        """Empty parts list returns empty string."""
        result = join_key([])
        assert result == ""

    def test_all_none_returns_empty(self) -> None:
        """All None parts returns empty string."""
        result = join_key([None, None])
        assert result == ""


class TestFormatTupleKey:
    """Tests for format_tuple_key function."""

    def test_formats_with_kwargs(self) -> None:
        """Formats template with keyword arguments."""
        result = format_tuple_key(("user", "{user_id}", "profile"), user_id=123)
        assert result == "user:123:profile"

    def test_multiple_placeholders(self) -> None:
        """Handles multiple placeholders."""
        result = format_tuple_key(
            ("{tenant}", "user", "{user_id}"),
            tenant="acme",
            user_id=456,
        )
        assert result == "acme:user:456"

    def test_raises_on_missing_variable(self) -> None:
        """Raises KeyError when variable is missing."""
        with pytest.raises(KeyError):
            format_tuple_key(("user", "{user_id}"), wrong_key=123)

    def test_no_placeholders(self) -> None:
        """Works without placeholders."""
        result = format_tuple_key(("static", "key", "parts"))
        assert result == "static:key:parts"


class TestNormalizeCacheKey:
    """Tests for normalize_cache_key function."""

    def test_string_key_passthrough(self) -> None:
        """String key passes through unchanged."""
        result = normalize_cache_key("user:123:profile")
        assert result == "user:123:profile"

    def test_string_with_format_kwargs(self) -> None:
        """String key with format kwargs."""
        result = normalize_cache_key("user:{user_id}:profile", user_id=123)
        assert result == "user:123:profile"

    def test_tuple_key_formatted(self) -> None:
        """Tuple key is formatted."""
        result = normalize_cache_key(("user", "{user_id}"), user_id=456)
        assert result == "user:456"

    def test_string_missing_kwargs_returns_original(self) -> None:
        """String with missing kwargs returns original string."""
        result = normalize_cache_key("user:{user_id}", wrong_var=123)
        assert result == "user:{user_id}"

    def test_invalid_type_raises(self) -> None:
        """Invalid key type raises TypeError."""
        with pytest.raises(TypeError, match="must be string or tuple"):
            normalize_cache_key(123)  # type: ignore


class TestValidateCacheKey:
    """Tests for validate_cache_key function."""

    def test_valid_key_returns_unchanged(self) -> None:
        """Valid key returns unchanged."""
        result = validate_cache_key("user:123:profile")
        assert result == "user:123:profile"

    def test_empty_key_raises(self) -> None:
        """Empty key raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            validate_cache_key("")

    def test_none_key_raises(self) -> None:
        """None key raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            validate_cache_key(None)  # type: ignore

    def test_long_key_is_hashed(self) -> None:
        """Long key is hashed to stay under limit."""
        long_key = "x" * 300
        result = validate_cache_key(long_key)
        assert result.startswith("hashed:")
        assert len(result) <= 250

    def test_custom_max_length(self) -> None:
        """Custom max_length is respected."""
        key = "x" * 100
        result = validate_cache_key(key, max_length=50)
        assert result.startswith("hashed:")

    def test_removes_newlines(self) -> None:
        """Removes newlines from key."""
        result = validate_cache_key("user\n123\rprofile\tdata")
        assert "\n" not in result
        assert "\r" not in result
        assert "\t" not in result

    def test_whitespace_only_after_sanitization_raises(self) -> None:
        """Key that becomes empty after sanitization raises."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_cache_key("\n\r\t")
