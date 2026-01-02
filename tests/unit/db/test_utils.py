"""Tests for svc_infra.db.utils module."""

from __future__ import annotations

from pathlib import Path

from svc_infra.db.utils import (
    KeySpec,
    as_tuple,
    normalize_dir,
    pascal,
    plural_snake,
    snake,
)


class TestAsTuple:
    """Tests for as_tuple function."""

    def test_string_becomes_single_element_tuple(self) -> None:
        """String should become single-element tuple."""
        result = as_tuple("id")
        assert result == ("id",)

    def test_list_becomes_tuple(self) -> None:
        """List should become tuple."""
        result = as_tuple(["id", "name"])
        assert result == ("id", "name")

    def test_tuple_stays_tuple(self) -> None:
        """Tuple should stay tuple."""
        result = as_tuple(("a", "b", "c"))
        assert result == ("a", "b", "c")

    def test_empty_string(self) -> None:
        """Empty string should become single-element tuple."""
        result = as_tuple("")
        assert result == ("",)

    def test_empty_list(self) -> None:
        """Empty list should become empty tuple."""
        result = as_tuple([])
        assert result == ()


class TestNormalizeDir:
    """Tests for normalize_dir function."""

    def test_absolute_path_stays_absolute(self) -> None:
        """Absolute path should stay as-is."""
        p = Path("/usr/local/bin")
        result = normalize_dir(p)
        assert result == p
        assert result.is_absolute()

    def test_string_absolute_path(self) -> None:
        """String absolute path should become Path."""
        result = normalize_dir("/tmp/test")
        assert isinstance(result, Path)
        assert result == Path("/tmp/test")

    def test_relative_path_becomes_absolute(self) -> None:
        """Relative path should become absolute."""
        result = normalize_dir("relative/path")
        assert result.is_absolute()
        assert result.parts[-2:] == ("relative", "path")

    def test_dot_path(self) -> None:
        """Dot path should resolve to cwd."""
        result = normalize_dir(".")
        assert result.is_absolute()
        assert result == Path.cwd().resolve()

    def test_path_object_returned(self) -> None:
        """Should always return Path object."""
        assert isinstance(normalize_dir("/tmp"), Path)
        assert isinstance(normalize_dir("relative"), Path)


class TestSnake:
    """Tests for snake function."""

    def test_camel_case(self) -> None:
        """CamelCase should become snake_case."""
        assert snake("CamelCase") == "camel_case"

    def test_pascal_case(self) -> None:
        """PascalCase should become snake_case."""
        assert snake("PascalCase") == "pascal_case"

    def test_already_snake(self) -> None:
        """Already snake_case should stay the same."""
        assert snake("already_snake") == "already_snake"

    def test_mixed_case(self) -> None:
        """Mixed case should be converted."""
        assert snake("XMLParser") == "xml_parser"

    def test_with_numbers(self) -> None:
        """Should handle numbers."""
        assert snake("OAuth2Token") == "o_auth2_token"

    def test_consecutive_caps(self) -> None:
        """Should handle consecutive capitals."""
        assert snake("HTTPServer") == "http_server"

    def test_special_characters(self) -> None:
        """Special characters should become underscores."""
        assert snake("hello-world") == "hello_world"
        assert snake("hello.world") == "hello_world"

    def test_trailing_special_chars(self) -> None:
        """Trailing special chars should be stripped."""
        result = snake("test__")
        assert not result.endswith("_")

    def test_leading_special_chars(self) -> None:
        """Leading special chars should be stripped."""
        result = snake("__test")
        assert not result.startswith("_")

    def test_empty_string(self) -> None:
        """Empty string should return empty."""
        assert snake("") == ""

    def test_single_word(self) -> None:
        """Single lowercase word should stay the same."""
        assert snake("hello") == "hello"

    def test_single_cap_word(self) -> None:
        """Single capitalized word should become lowercase."""
        assert snake("Hello") == "hello"


class TestPascal:
    """Tests for pascal function."""

    def test_snake_case(self) -> None:
        """snake_case should become PascalCase."""
        assert pascal("snake_case") == "SnakeCase"

    def test_already_pascal(self) -> None:
        """Already PascalCase should be normalized via snake conversion."""
        result = pascal("PascalCase")
        assert result == "PascalCase"

    def test_single_word(self) -> None:
        """Single word should be capitalized."""
        assert pascal("hello") == "Hello"

    def test_empty_string_returns_item(self) -> None:
        """Empty string should return 'Item'."""
        assert pascal("") == "Item"

    def test_with_numbers(self) -> None:
        """Should handle numbers."""
        result = pascal("user_v2")
        assert result.startswith("User")

    def test_multi_word(self) -> None:
        """Multiple words should all be capitalized."""
        assert pascal("user_profile_data") == "UserProfileData"


class TestPluralSnake:
    """Tests for plural_snake function."""

    def test_singular_gets_s(self) -> None:
        """Singular word should get 's' added."""
        assert plural_snake("User") == "users"

    def test_already_plural(self) -> None:
        """Words ending in 's' should stay the same."""
        assert plural_snake("Users") == "users"

    def test_pascal_to_plural_snake(self) -> None:
        """PascalCase should become plural_snake_case."""
        assert plural_snake("UserProfile") == "user_profiles"

    def test_word_ending_in_s(self) -> None:
        """Word ending in 's' should not add another 's'."""
        assert plural_snake("Status") == "status"

    def test_single_char(self) -> None:
        """Single character should get 's'."""
        assert plural_snake("X") == "xs"


class TestKeySpec:
    """Tests for KeySpec type alias."""

    def test_string_is_valid_keyspec(self) -> None:
        """String should be valid KeySpec."""
        spec: KeySpec = "id"
        assert as_tuple(spec) == ("id",)

    def test_list_is_valid_keyspec(self) -> None:
        """List should be valid KeySpec."""
        spec: KeySpec = ["id", "name"]
        assert as_tuple(spec) == ("id", "name")

    def test_tuple_is_valid_keyspec(self) -> None:
        """Tuple should be valid KeySpec."""
        spec: KeySpec = ("a", "b")
        assert as_tuple(spec) == ("a", "b")
