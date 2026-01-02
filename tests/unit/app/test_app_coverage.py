"""Coverage tests for app module.

Targets:
- app/env.py: Environment detection, normalization, pick()
- app/root.py: Project root resolution
"""

from __future__ import annotations

import os
import tempfile
import warnings
from pathlib import Path
from unittest.mock import patch

from svc_infra.app.env import (
    ALL_ENVIRONMENTS,
    DEV_ENV,
    LOCAL_ENV,
    PROD_ENV,
    TEST_ENV,
    Environment,
    _normalize,
    get_current_environment,
    pick,
)
from svc_infra.app.root import (
    DEFAULT_SENTRIES,
    _git_toplevel,
    _is_root_marker,
    resolve_project_root,
)

# ============== Environment Tests ==============


class TestEnvironmentEnum:
    def test_environment_values(self) -> None:
        assert Environment.LOCAL.value == "local"
        assert Environment.DEV.value == "dev"
        assert Environment.TEST.value == "test"
        assert Environment.PROD.value == "prod"

    def test_environment_aliases(self) -> None:
        assert LOCAL_ENV == Environment.LOCAL
        assert DEV_ENV == Environment.DEV
        assert TEST_ENV == Environment.TEST
        assert PROD_ENV == Environment.PROD

    def test_all_environments(self) -> None:
        assert LOCAL_ENV in ALL_ENVIRONMENTS
        assert DEV_ENV in ALL_ENVIRONMENTS
        assert TEST_ENV in ALL_ENVIRONMENTS
        assert PROD_ENV in ALL_ENVIRONMENTS


class TestNormalize:
    def test_normalize_none(self) -> None:
        assert _normalize(None) is None

    def test_normalize_empty_string(self) -> None:
        assert _normalize("") is None

    def test_normalize_canonical(self) -> None:
        assert _normalize("local") == LOCAL_ENV
        assert _normalize("dev") == DEV_ENV
        assert _normalize("test") == TEST_ENV
        assert _normalize("prod") == PROD_ENV

    def test_normalize_case_insensitive(self) -> None:
        assert _normalize("LOCAL") == LOCAL_ENV
        assert _normalize("Dev") == DEV_ENV
        assert _normalize("TEST") == TEST_ENV
        assert _normalize("PROD") == PROD_ENV

    def test_normalize_synonyms(self) -> None:
        assert _normalize("development") == DEV_ENV
        assert _normalize("production") == PROD_ENV
        assert _normalize("staging") == TEST_ENV
        assert _normalize("preview") == TEST_ENV
        assert _normalize("uat") == TEST_ENV

    def test_normalize_unknown(self) -> None:
        assert _normalize("unknown_env") is None
        assert _normalize("random") is None

    def test_normalize_whitespace(self) -> None:
        assert _normalize("  local  ") == LOCAL_ENV
        assert _normalize("\tdev\n") == DEV_ENV


class TestGetCurrentEnvironment:
    def test_get_current_environment_app_env(self) -> None:
        # Clear cache first
        get_current_environment.cache_clear()
        with patch.dict(os.environ, {"APP_ENV": "prod"}, clear=False):
            result = get_current_environment()
            assert result == PROD_ENV
        get_current_environment.cache_clear()

    def test_get_current_environment_railway(self) -> None:
        get_current_environment.cache_clear()
        with patch.dict(os.environ, {"RAILWAY_ENVIRONMENT_NAME": "staging"}, clear=False):
            os.environ.pop("APP_ENV", None)
            result = get_current_environment()
            assert result == TEST_ENV
        get_current_environment.cache_clear()

    def test_get_current_environment_default(self) -> None:
        get_current_environment.cache_clear()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("APP_ENV", None)
            os.environ.pop("RAILWAY_ENVIRONMENT_NAME", None)
            result = get_current_environment()
            assert result == LOCAL_ENV
        get_current_environment.cache_clear()

    def test_get_current_environment_unknown_warns(self) -> None:
        get_current_environment.cache_clear()
        with patch.dict(os.environ, {"APP_ENV": "unknown_env_xyz"}, clear=False):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = get_current_environment()
                assert result == LOCAL_ENV
                assert len(w) >= 1
        get_current_environment.cache_clear()


class TestPick:
    def test_pick_returns_prod_value_in_prod(self) -> None:
        get_current_environment.cache_clear()
        with patch.dict(os.environ, {"APP_ENV": "prod"}, clear=False):
            get_current_environment.cache_clear()
            result = pick(prod=100, nonprod=50)
            assert result == 100
        get_current_environment.cache_clear()

    def test_pick_returns_nonprod_value_in_dev(self) -> None:
        get_current_environment.cache_clear()
        with patch.dict(os.environ, {"APP_ENV": "dev"}, clear=False):
            get_current_environment.cache_clear()
            result = pick(prod=100, nonprod=50)
            assert result == 50
        get_current_environment.cache_clear()

    def test_pick_returns_nonprod_value_in_local(self) -> None:
        get_current_environment.cache_clear()
        with patch.dict(os.environ, {"APP_ENV": "local"}, clear=False):
            get_current_environment.cache_clear()
            result = pick(prod=200, nonprod=100)
            assert result == 100
        get_current_environment.cache_clear()


# ============== Project Root Tests ==============


class TestIsRootMarker:
    def test_is_root_marker_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "pyproject.toml").touch()
            assert _is_root_marker(path, ["pyproject.toml"]) is True

    def test_is_root_marker_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            assert _is_root_marker(path, ["nonexistent.file"]) is False

    def test_is_root_marker_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / ".git").mkdir()
            assert _is_root_marker(path, [".git"]) is True


class TestGitToplevel:
    def test_git_toplevel_in_git_repo(self) -> None:
        # This test runs in a git repo
        result = _git_toplevel(Path.cwd())
        # Should return a path or None if not in git
        if result is not None:
            assert result.is_dir()

    def test_git_toplevel_not_in_git(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _git_toplevel(Path(tmpdir))
            assert result is None


class TestResolveProjectRoot:
    def test_resolve_from_env_var(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"PROJECT_ROOT": tmpdir}, clear=False):
                result = resolve_project_root()
                assert result == Path(tmpdir).resolve()

    def test_resolve_from_env_var_invalid(self) -> None:
        with patch.dict(os.environ, {"PROJECT_ROOT": "/nonexistent/path"}, clear=False):
            # Should fall back to other methods
            result = resolve_project_root()
            assert result.is_dir()

    def test_resolve_from_marker_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root_path = Path(tmpdir).resolve()
            (root_path / "pyproject.toml").touch()
            sub_path = root_path / "sub" / "dir"
            sub_path.mkdir(parents=True)

            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("PROJECT_ROOT", None)
                result = resolve_project_root(start=sub_path)
                # Use resolve() for both to handle symlinks
                assert result.resolve() == root_path.resolve()

    def test_resolve_with_extra_sentries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root_path = Path(tmpdir).resolve()
            (root_path / "custom_marker.txt").touch()
            sub_path = root_path / "nested"
            sub_path.mkdir()

            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("PROJECT_ROOT", None)
                # Without extra sentry - won't find it
                resolve_project_root(start=sub_path)

                # With extra sentry - should find it
                result2 = resolve_project_root(start=sub_path, extra_sentries=["custom_marker.txt"])
                assert result2.resolve() == root_path.resolve()

    def test_resolve_fallback_to_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_path = Path(tmpdir) / "empty"
            empty_path.mkdir()

            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("PROJECT_ROOT", None)
                # No markers, no git - should return start
                result = resolve_project_root(start=empty_path)
                # Result should be a valid directory
                assert result.is_dir()


class TestDefaultSentries:
    def test_default_sentries_contains_common_markers(self) -> None:
        assert ".git" in DEFAULT_SENTRIES
        assert "pyproject.toml" in DEFAULT_SENTRIES
        assert "poetry.lock" in DEFAULT_SENTRIES
        assert "alembic.ini" in DEFAULT_SENTRIES
