"""Tests for svc_infra.db.nosql.utils module."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from svc_infra.db.nosql.utils import (
    _read_secret_from_file,
    get_mongo_dbname_from_env,
    get_mongo_url_from_env,
    prepare_process_env,
)


class TestPrepareProcessEnv:
    """Tests for prepare_process_env function."""

    def test_returns_resolved_path(self) -> None:
        """Returns resolved path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = prepare_process_env(tmpdir)
            assert isinstance(result, Path)
            assert result.is_absolute()

    def test_sets_skip_app_init(self) -> None:
        """Sets SKIP_APP_INIT environment variable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("SKIP_APP_INIT", None)
                prepare_process_env(tmpdir)
                assert os.environ.get("SKIP_APP_INIT") == "1"

    def test_adds_src_dir_to_pythonpath(self) -> None:
        """Adds src directory to PYTHONPATH if it exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "src"
            src_dir.mkdir()

            with patch.dict(os.environ, {"PYTHONPATH": ""}, clear=False):
                prepare_process_env(tmpdir)
                assert str(src_dir) in os.environ["PYTHONPATH"]


class TestReadSecretFromFile:
    """Tests for _read_secret_from_file function."""

    def test_reads_file_content(self) -> None:
        """Reads content from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("my-secret-value\n")
            f.flush()
            try:
                result = _read_secret_from_file(f.name)
                assert result == "my-secret-value"
            finally:
                os.unlink(f.name)

    def test_strips_whitespace(self) -> None:
        """Strips whitespace from content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("  secret  \n\n")
            f.flush()
            try:
                result = _read_secret_from_file(f.name)
                assert result == "secret"
            finally:
                os.unlink(f.name)

    def test_returns_none_for_missing_file(self) -> None:
        """Returns None for non-existent file."""
        result = _read_secret_from_file("/nonexistent/path/to/file")
        assert result is None

    def test_returns_none_on_error(self) -> None:
        """Returns None on read error."""
        result = _read_secret_from_file("/dev/null/impossible")
        assert result is None


class TestGetMongoUrlFromEnv:
    """Tests for get_mongo_url_from_env function."""

    def test_reads_from_mongo_url(self) -> None:
        """Reads URL from MONGO_URL environment variable."""
        with patch.dict(
            os.environ,
            {"MONGO_URL": "mongodb://localhost:27017"},
            clear=False,
        ):
            result = get_mongo_url_from_env(required=False)
            assert result == "mongodb://localhost:27017"

    def test_reads_from_mongodb_url(self) -> None:
        """Reads URL from MONGODB_URL environment variable."""
        with patch.dict(
            os.environ,
            {"MONGO_URL": "", "MONGODB_URL": "mongodb://mongo:27017"},
            clear=False,
        ):
            result = get_mongo_url_from_env(required=False)
            assert result == "mongodb://mongo:27017"

    def test_reads_from_file_env(self) -> None:
        """Reads URL from file specified in *_FILE env var."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("mongodb://secret-host:27017")
            f.flush()
            try:
                with patch.dict(
                    os.environ,
                    {"MONGO_URL": "", "MONGO_URL_FILE": f.name},
                    clear=False,
                ):
                    result = get_mongo_url_from_env(required=False)
                    assert result == "mongodb://secret-host:27017"
            finally:
                os.unlink(f.name)

    def test_raises_when_required_and_missing(self) -> None:
        """Raises RuntimeError when required and no URL found."""
        with patch.dict(
            os.environ,
            {"MONGO_URL": "", "MONGODB_URL": "", "MONGO_URL_FILE": ""},
            clear=False,
        ):
            with pytest.raises(RuntimeError, match="Mongo URL not set"):
                get_mongo_url_from_env(required=True)

    def test_returns_none_when_not_required_and_missing(self) -> None:
        """Returns None when not required and no URL found."""
        with patch.dict(
            os.environ,
            {"MONGO_URL": "", "MONGODB_URL": "", "MONGO_URL_FILE": ""},
            clear=False,
        ):
            result = get_mongo_url_from_env(required=False)
            assert result is None

    def test_reads_from_file_prefix(self) -> None:
        """Reads URL from file when value starts with 'file:'."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("mongodb://from-file:27017")
            f.flush()
            try:
                with patch.dict(
                    os.environ,
                    {"MONGO_URL": f"file:{f.name}"},
                    clear=False,
                ):
                    result = get_mongo_url_from_env(required=False)
                    assert result == "mongodb://from-file:27017"
            finally:
                os.unlink(f.name)


class TestGetMongoDbNameFromEnv:
    """Tests for get_mongo_dbname_from_env function."""

    def test_reads_from_mongo_db(self) -> None:
        """Reads db name from MONGO_DB environment variable."""
        with patch.dict(
            os.environ,
            {"MONGO_DB": "mydb"},
            clear=False,
        ):
            result = get_mongo_dbname_from_env(required=False)
            assert result == "mydb"

    def test_reads_from_mongodb_db(self) -> None:
        """Reads db name from MONGODB_DB environment variable."""
        with patch.dict(
            os.environ,
            {"MONGO_DB": "", "MONGODB_DB": "otherdb", "MONGO_DATABASE": ""},
            clear=False,
        ):
            # Clear MONGO_DB to test fallback
            result = get_mongo_dbname_from_env(
                required=False,
                env_vars=["MONGO_DB", "MONGODB_DB", "MONGO_DATABASE"],
            )
            assert result == "otherdb"

    def test_raises_when_required_and_missing(self) -> None:
        """Raises RuntimeError when required and no db name found."""
        with patch.dict(
            os.environ,
            {"MONGO_DB": "", "MONGODB_DATABASE": ""},
            clear=False,
        ):
            with pytest.raises(RuntimeError, match="Mongo DB name not set"):
                get_mongo_dbname_from_env(required=True)

    def test_returns_none_when_not_required_and_missing(self) -> None:
        """Returns None when not required and no db name found."""
        with patch.dict(
            os.environ,
            {"MONGO_DB": "", "MONGODB_DATABASE": ""},
            clear=False,
        ):
            result = get_mongo_dbname_from_env(required=False)
            assert result is None

    def test_strips_whitespace(self) -> None:
        """Strips whitespace from db name."""
        with patch.dict(
            os.environ,
            {"MONGO_DB": "  mydb  "},
            clear=False,
        ):
            result = get_mongo_dbname_from_env(required=False)
            assert result == "mydb"
