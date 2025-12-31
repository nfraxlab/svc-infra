"""Tests for svc_infra.api.fastapi.routers module."""

from __future__ import annotations

from types import ModuleType
from unittest.mock import MagicMock

import pytest

from svc_infra.api.fastapi.routers import (
    _derive_docs_from_module,
    _normalize_environment,
    _should_force_include_in_schema,
    _should_skip_module,
    _validate_base_package,
)
from svc_infra.app.env import DEV_ENV, LOCAL_ENV, PROD_ENV, Environment


class TestShouldSkipModule:
    """Tests for _should_skip_module function."""

    def test_skips_private_module(self) -> None:
        """Skips modules starting with underscore."""
        assert _should_skip_module("package._private") is True

    def test_skips_dunder_module(self) -> None:
        """Skips dunder modules."""
        assert _should_skip_module("package.__init__") is True

    def test_allows_public_module(self) -> None:
        """Allows public modules."""
        assert _should_skip_module("package.public") is False

    def test_checks_last_segment(self) -> None:
        """Only checks the last segment."""
        assert _should_skip_module("_private.public.router") is False
        assert _should_skip_module("public.module._private") is True


class TestDeriveDocsFromModule:
    """Tests for _derive_docs_from_module function."""

    def test_explicit_constants_win(self) -> None:
        """Explicit ROUTER_SUMMARY and ROUTER_DESCRIPTION win."""
        mock_module = MagicMock(spec=ModuleType)
        mock_module.ROUTER_SUMMARY = "Custom Summary"
        mock_module.ROUTER_DESCRIPTION = "Custom Description"
        mock_module.__doc__ = "Docstring summary\nDocstring description"

        summary, description = _derive_docs_from_module(mock_module)
        assert summary == "Custom Summary"
        assert description == "Custom Description"

    def test_falls_back_to_docstring(self) -> None:
        """Falls back to docstring when no constants."""
        mock_module = MagicMock(spec=ModuleType)
        mock_module.ROUTER_SUMMARY = None
        mock_module.ROUTER_DESCRIPTION = None
        mock_module.__doc__ = "Summary line\nDescription line"

        summary, description = _derive_docs_from_module(mock_module)
        assert summary == "Summary line"
        assert description == "Description line"

    def test_single_line_docstring(self) -> None:
        """Single line docstring has no description."""
        mock_module = MagicMock(spec=ModuleType)
        mock_module.ROUTER_SUMMARY = None
        mock_module.ROUTER_DESCRIPTION = None
        mock_module.__doc__ = "Only summary"

        summary, description = _derive_docs_from_module(mock_module)
        assert summary == "Only summary"
        assert description is None

    def test_empty_docstring(self) -> None:
        """Empty docstring returns None for both."""
        mock_module = MagicMock(spec=ModuleType)
        mock_module.ROUTER_SUMMARY = None
        mock_module.ROUTER_DESCRIPTION = None
        mock_module.__doc__ = ""

        summary, description = _derive_docs_from_module(mock_module)
        assert summary is None
        assert description is None

    def test_no_docstring(self) -> None:
        """No docstring returns None for both."""
        mock_module = MagicMock(spec=ModuleType)
        mock_module.ROUTER_SUMMARY = None
        mock_module.ROUTER_DESCRIPTION = None
        mock_module.__doc__ = None

        summary, description = _derive_docs_from_module(mock_module)
        assert summary is None
        assert description is None


class TestValidateBasePackage:
    """Tests for _validate_base_package function."""

    def test_valid_package(self) -> None:
        """Validates a valid package."""
        # Use a known package
        module = _validate_base_package("json")
        assert module is not None

    def test_invalid_package_raises(self) -> None:
        """Invalid package raises RuntimeError."""
        with pytest.raises(RuntimeError, match="Could not import"):
            _validate_base_package("nonexistent_package_xyz")


class TestNormalizeEnvironment:
    """Tests for _normalize_environment function."""

    def test_none_uses_current(self) -> None:
        """None returns current environment."""
        result = _normalize_environment(None)
        assert isinstance(result, Environment)

    def test_string_converted(self) -> None:
        """String is converted to Environment."""
        result = _normalize_environment("prod")
        assert isinstance(result, Environment)

    def test_environment_passthrough(self) -> None:
        """Environment passes through unchanged."""
        result = _normalize_environment(PROD_ENV)
        assert result is PROD_ENV


class TestShouldForceIncludeInSchema:
    """Tests for _should_force_include_in_schema function."""

    def test_local_env_forces_include(self) -> None:
        """Local environment forces include."""
        result = _should_force_include_in_schema(LOCAL_ENV, None)
        assert result is True

    def test_dev_env_forces_include(self) -> None:
        """Dev environment forces include."""
        result = _should_force_include_in_schema(DEV_ENV, None)
        assert result is True

    def test_prod_env_does_not_force(self) -> None:
        """Production environment does not force include."""
        result = _should_force_include_in_schema(PROD_ENV, None)
        assert result is False

    def test_explicit_true_overrides(self) -> None:
        """Explicit True overrides environment."""
        result = _should_force_include_in_schema(PROD_ENV, True)
        assert result is True

    def test_explicit_false_overrides(self) -> None:
        """Explicit False overrides environment."""
        result = _should_force_include_in_schema(LOCAL_ENV, False)
        assert result is False
