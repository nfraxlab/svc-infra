"""Tests for svc_infra.cache.keys module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from svc_infra.cache.keys import (
    build_key_template,
    build_key_variants_renderer,
    create_tags_function,
    resolve_tags,
)


class TestBuildKeyTemplate:
    """Tests for build_key_template function."""

    def test_string_key(self) -> None:
        """Should return string key unchanged."""
        result = build_key_template("user:123")
        assert result == "user:123"

    def test_tuple_key(self) -> None:
        """Should join tuple parts with colons."""
        result = build_key_template(("user", "123", "profile"))
        assert result == "user:123:profile"

    def test_tuple_with_empty_parts(self) -> None:
        """Should filter out empty parts."""
        result = build_key_template(("user", "", "profile"))
        assert result == "user:profile"

    def test_tuple_with_colons(self) -> None:
        """Should strip existing colons from parts."""
        result = build_key_template((":user:", ":123:"))
        assert result == "user:123"

    def test_empty_tuple(self) -> None:
        """Should handle empty tuple."""
        result = build_key_template(())
        assert result == ""


class TestCreateTagsFunction:
    """Tests for create_tags_function."""

    def test_none_returns_empty_list(self) -> None:
        """Should return function that returns empty list when None."""
        func = create_tags_function(None)
        assert func() == []
        assert func("arg1", key="value") == []

    def test_callable_returns_result(self) -> None:
        """Should call provided function and return result."""
        mock_tags = MagicMock(return_value=["tag1", "tag2"])
        func = create_tags_function(mock_tags)

        result = func("arg1", key="value")

        assert result == ["tag1", "tag2"]
        mock_tags.assert_called_once_with("arg1", key="value")

    def test_callable_handles_exception(self) -> None:
        """Should return empty list if callable raises."""
        mock_tags = MagicMock(side_effect=ValueError("error"))
        func = create_tags_function(mock_tags)

        result = func("arg1")

        assert result == []

    def test_callable_handles_none_return(self) -> None:
        """Should return empty list if callable returns None."""
        mock_tags = MagicMock(return_value=None)
        func = create_tags_function(mock_tags)

        result = func("arg1")

        assert result == []

    def test_static_tags(self) -> None:
        """Should return static tags list."""
        func = create_tags_function(["tag1", "tag2"])

        result = func("arg1", key="value")

        assert result == ["tag1", "tag2"]


class TestBuildKeyVariantsRenderer:
    """Tests for build_key_variants_renderer."""

    def test_renders_template(self) -> None:
        """Should render template with kwargs."""
        with patch("svc_infra.cache.keys._alias", return_value=""):
            renderer = build_key_variants_renderer("user:{user_id}")
            result = renderer(user_id=123)

            assert "user:123" in result

    def test_with_namespace(self) -> None:
        """Should add namespace prefix."""
        with patch("svc_infra.cache.keys._alias", return_value="myapp"):
            renderer = build_key_variants_renderer("user:{user_id}")
            result = renderer(user_id=123)

            assert "myapp:user:123" in result

    def test_missing_kwarg(self) -> None:
        """Should return empty list on missing kwarg."""
        with patch("svc_infra.cache.keys._alias", return_value=""):
            renderer = build_key_variants_renderer("user:{user_id}")
            result = renderer()  # missing user_id

            assert result == []

    def test_removes_duplicates(self) -> None:
        """Should remove duplicate variants."""
        with patch("svc_infra.cache.keys._alias", return_value=""):
            renderer = build_key_variants_renderer("user:123")
            result = renderer()

            # Should not have duplicates
            assert len(result) == len(set(result))


class TestResolveTags:
    """Tests for resolve_tags function."""

    def test_static_tags(self) -> None:
        """Should return static tags."""
        result = resolve_tags(["tag1", "tag2"])
        assert result == ["tag1", "tag2"]

    def test_callable_tags(self) -> None:
        """Should call callable and return result."""

        def tags_func(*args, **kwargs):
            return ["dynamic_tag"]

        result = resolve_tags(tags_func)
        assert result == ["dynamic_tag"]

    def test_template_tags(self) -> None:
        """Should render template tags with kwargs."""
        result = resolve_tags(["user:{user_id}"], user_id=123)
        assert "user:123" in result

    def test_mixed_tags(self) -> None:
        """Should handle mix of static and template tags."""
        result = resolve_tags(["static", "user:{id}"], id=456)
        assert "static" in result
        assert "user:456" in result

    def test_none_callable_result(self) -> None:
        """Should handle callable returning None."""

        def tags_func(*args, **kwargs):
            return None

        result = resolve_tags(tags_func)
        assert result == []
