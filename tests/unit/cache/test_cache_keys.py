"""Unit tests for svc_infra.cache.keys module."""

from __future__ import annotations

from unittest.mock import patch

from svc_infra.cache.keys import (
    build_key_template,
    build_key_variants_renderer,
    create_tags_function,
    resolve_tags,
)


class TestBuildKeyTemplate:
    """Tests for build_key_template function."""

    def test_string_key(self) -> None:
        """Test building template from string key."""
        assert build_key_template("users:123") == "users:123"

    def test_tuple_key(self) -> None:
        """Test building template from tuple key."""
        result = build_key_template(("users", "123", "profile"))
        assert result == "users:123:profile"

    def test_tuple_with_empty_parts(self) -> None:
        """Test that empty parts are filtered out."""
        result = build_key_template(("users", "", "profile"))
        assert result == "users:profile"

    def test_tuple_strips_colons(self) -> None:
        """Test that leading/trailing colons are stripped."""
        result = build_key_template((":users:", ":123:"))
        assert result == "users:123"

    def test_empty_tuple(self) -> None:
        """Test empty tuple returns empty string."""
        result = build_key_template(())
        assert result == ""

    def test_single_item_tuple(self) -> None:
        """Test single item tuple."""
        result = build_key_template(("cache",))
        assert result == "cache"


class TestCreateTagsFunction:
    """Tests for create_tags_function."""

    def test_none_tags_returns_empty(self) -> None:
        """Test None tags param returns empty list function."""
        fn = create_tags_function(None)
        assert fn() == []
        assert fn("arg", kwarg="value") == []

    def test_callable_tags(self) -> None:
        """Test callable tags are invoked."""

        def dynamic_tags(resource_type: str) -> list[str]:
            return [f"type:{resource_type}"]

        fn = create_tags_function(dynamic_tags)
        assert fn("users") == ["type:users"]

    def test_callable_tags_with_kwargs(self) -> None:
        """Test callable tags receive kwargs."""

        def dynamic_tags(**kwargs) -> list[str]:
            return [f"id:{kwargs.get('id', 'none')}"]

        fn = create_tags_function(dynamic_tags)
        assert fn(id=123) == ["id:123"]

    def test_callable_tags_returning_none(self) -> None:
        """Test callable returning None returns empty list."""

        def nullable_tags() -> list[str] | None:
            return None

        fn = create_tags_function(nullable_tags)
        assert fn() == []

    def test_callable_tags_with_exception(self) -> None:
        """Test exception in callable returns empty list."""

        def failing_tags() -> list[str]:
            raise ValueError("oops")

        fn = create_tags_function(failing_tags)
        # Should not raise, should return empty list
        assert fn() == []

    def test_static_list_tags(self) -> None:
        """Test static list is returned."""
        fn = create_tags_function(["tag1", "tag2"])
        assert fn() == ["tag1", "tag2"]
        # Static tags ignore arguments
        assert fn("ignored", kwarg="also_ignored") == ["tag1", "tag2"]

    def test_static_tuple_tags(self) -> None:
        """Test static tuple is converted to list."""
        fn = create_tags_function(("tag1", "tag2"))
        assert fn() == ["tag1", "tag2"]

    def test_static_set_tags(self) -> None:
        """Test static set is converted to list."""
        fn = create_tags_function({"tag1", "tag2"})
        result = fn()
        assert sorted(result) == ["tag1", "tag2"]


class TestBuildKeyVariantsRenderer:
    """Tests for build_key_variants_renderer."""

    @patch("svc_infra.cache.keys._alias", return_value="")
    def test_no_namespace(self, mock_alias) -> None:
        """Test variant generation without namespace."""
        renderer = build_key_variants_renderer("users:{user_id}")
        variants = renderer(user_id=123)
        assert "users:123" in variants

    @patch("svc_infra.cache.keys._alias", return_value="myapp")
    def test_with_namespace(self, mock_alias) -> None:
        """Test variant generation with namespace."""
        renderer = build_key_variants_renderer("users:{user_id}")
        variants = renderer(user_id=123)
        assert "myapp:users:123" in variants
        assert "users:123" in variants

    @patch("svc_infra.cache.keys._alias", return_value="")
    def test_missing_key_returns_empty(self, mock_alias) -> None:
        """Test missing template key returns empty variants."""
        renderer = build_key_variants_renderer("users:{user_id}")
        variants = renderer()  # Missing user_id
        assert variants == []

    @patch("svc_infra.cache.keys._alias", return_value="")
    def test_multiple_placeholders(self, mock_alias) -> None:
        """Test template with multiple placeholders."""
        renderer = build_key_variants_renderer("org:{org_id}:user:{user_id}")
        variants = renderer(org_id="acme", user_id=456)
        assert "org:acme:user:456" in variants

    @patch("svc_infra.cache.keys._alias", return_value="")
    def test_static_key(self, mock_alias) -> None:
        """Test static key without placeholders."""
        renderer = build_key_variants_renderer("static:key")
        variants = renderer()
        assert "static:key" in variants


class TestResolveTags:
    """Tests for resolve_tags function."""

    def test_static_list(self) -> None:
        """Test resolving static list of tags."""
        result = resolve_tags(["tag1", "tag2"])
        assert result == ["tag1", "tag2"]

    def test_callable_tags(self) -> None:
        """Test resolving callable tags."""

        def get_tags() -> list[str]:
            return ["dynamic1", "dynamic2"]

        result = resolve_tags(get_tags)
        assert result == ["dynamic1", "dynamic2"]

    def test_template_tags(self) -> None:
        """Test resolving template tags with kwargs."""
        result = resolve_tags(["user:{user_id}", "org:{org_id}"], user_id=123, org_id="acme")
        assert "user:123" in result
        assert "org:acme" in result

    def test_template_missing_key(self) -> None:
        """Test template with missing key is skipped."""
        result = resolve_tags(["user:{user_id}", "static_tag"], org_id="acme")
        # Missing user_id should be skipped, static_tag should remain
        assert "static_tag" in result
        assert len([r for r in result if "user:" in r]) == 0

    def test_mixed_static_and_template(self) -> None:
        """Test mix of static and template tags."""
        result = resolve_tags(["static", "dynamic:{id}"], id=42)
        assert "static" in result
        assert "dynamic:42" in result

    def test_non_string_tags(self) -> None:
        """Test non-string tags are converted to strings."""
        result = resolve_tags([123, True, "normal"])
        assert "123" in result
        assert "True" in result
        assert "normal" in result

    def test_empty_tags_list(self) -> None:
        """Test empty tags list returns empty."""
        result = resolve_tags([])
        assert result == []

    def test_callable_returning_none(self) -> None:
        """Test callable returning None."""

        def nullable() -> list[str] | None:
            return None

        result = resolve_tags(nullable)
        assert result == []

    def test_exception_returns_empty(self) -> None:
        """Test exception in resolution returns empty list."""

        def failing() -> list[str]:
            raise RuntimeError("fail")

        result = resolve_tags(failing)
        assert result == []

    def test_callable_with_args(self) -> None:
        """Test callable receives args."""

        def with_args(a, b) -> list[str]:
            return [f"sum:{a + b}"]

        result = resolve_tags(with_args, 1, 2)
        assert result == ["sum:3"]
