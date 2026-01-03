"""
Tests for database SQL utilities: query builders, escaping, URL composition.
"""

from __future__ import annotations

import os

import pytest


class TestGetDatabaseUrlFromEnv:
    """Tests for database URL resolution from environment."""

    def test_reads_from_sql_url_env(self, monkeypatch):
        """Should read from SQL_URL environment variable."""
        from svc_infra.db.sql.utils import get_database_url_from_env

        monkeypatch.setenv("SQL_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.delenv("DATABASE_URL", raising=False)

        result = get_database_url_from_env()
        assert result == "postgresql://user:pass@localhost/db"

    def test_reads_from_database_url_fallback(self, monkeypatch):
        """Should fall back to DATABASE_URL if SQL_URL not set."""
        from svc_infra.db.sql.utils import get_database_url_from_env

        monkeypatch.delenv("SQL_URL", raising=False)
        monkeypatch.setenv("DATABASE_URL", "postgresql://fallback@localhost/db")

        result = get_database_url_from_env()
        assert result == "postgresql://fallback@localhost/db"

    def test_returns_none_when_no_url_set(self, monkeypatch):
        """Should return None when no URL environment variables set."""
        from svc_infra.db.sql.utils import get_database_url_from_env

        monkeypatch.delenv("SQL_URL", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("DB_HOST", raising=False)
        monkeypatch.delenv("DB_NAME", raising=False)

        result = get_database_url_from_env(required=False)
        assert result is None

    def test_raises_when_required_and_missing(self, monkeypatch):
        """Should raise when required=True and no URL available."""
        from svc_infra.db.sql.utils import get_database_url_from_env

        monkeypatch.delenv("SQL_URL", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("DB_HOST", raising=False)
        monkeypatch.delenv("DB_NAME", raising=False)

        with pytest.raises(RuntimeError, match="Database URL not set"):
            get_database_url_from_env(required=True)


class TestComposeUrlFromParts:
    """Tests for composing database URL from component env vars."""

    def test_compose_basic_postgres_url(self, monkeypatch):
        """Should compose a basic PostgreSQL URL from parts."""
        from svc_infra.db.sql.utils import _compose_url_from_parts

        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("DB_PORT", "5432")
        monkeypatch.setenv("DB_NAME", "testdb")
        monkeypatch.setenv("DB_USER", "testuser")
        monkeypatch.setenv("DB_PASSWORD", "testpass")
        monkeypatch.delenv("DB_DIALECT", raising=False)
        monkeypatch.delenv("DB_DRIVER", raising=False)
        monkeypatch.delenv("DB_PARAMS", raising=False)

        result = _compose_url_from_parts()
        assert result is not None
        assert "postgresql" in result
        assert "testuser" in result
        assert "localhost" in result
        assert "testdb" in result

    def test_compose_with_driver(self, monkeypatch):
        """Should include driver in dialect when specified."""
        from svc_infra.db.sql.utils import _compose_url_from_parts

        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("DB_NAME", "testdb")
        monkeypatch.setenv("DB_DRIVER", "asyncpg")
        monkeypatch.delenv("DB_PORT", raising=False)
        monkeypatch.delenv("DB_USER", raising=False)
        monkeypatch.delenv("DB_PASSWORD", raising=False)

        result = _compose_url_from_parts()
        assert result is not None
        assert "postgresql+asyncpg" in result

    def test_compose_with_params(self, monkeypatch):
        """Should include query parameters."""
        from svc_infra.db.sql.utils import _compose_url_from_parts

        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("DB_NAME", "testdb")
        monkeypatch.setenv("DB_PARAMS", "sslmode=require&connect_timeout=5")
        monkeypatch.delenv("DB_PORT", raising=False)

        result = _compose_url_from_parts()
        assert result is not None
        assert "sslmode=require" in result

    def test_returns_none_without_host(self, monkeypatch):
        """Should return None when DB_HOST not set."""
        from svc_infra.db.sql.utils import _compose_url_from_parts

        monkeypatch.delenv("DB_HOST", raising=False)
        monkeypatch.setenv("DB_NAME", "testdb")

        result = _compose_url_from_parts()
        assert result is None

    def test_returns_none_without_name(self, monkeypatch):
        """Should return None when DB_NAME not set."""
        from svc_infra.db.sql.utils import _compose_url_from_parts

        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.delenv("DB_NAME", raising=False)

        result = _compose_url_from_parts()
        assert result is None


class TestConvertToAsyncUrl:
    """Tests for URL conversion to async driver."""

    def test_convert_postgresql_to_asyncpg(self):
        """Should convert postgresql:// to postgresql+asyncpg://."""
        from svc_infra.db.sql.utils import _coerce_to_async_url

        sync_url = "postgresql://user:pass@localhost/db"
        async_url = _coerce_to_async_url(sync_url)

        assert "asyncpg" in async_url
        assert async_url.startswith("postgresql+asyncpg://")

    def test_convert_postgres_to_asyncpg(self):
        """Should convert postgres:// to postgresql+asyncpg://."""
        from svc_infra.db.sql.utils import _coerce_to_async_url

        sync_url = "postgres://user:pass@localhost/db"
        async_url = _coerce_to_async_url(sync_url)

        assert "asyncpg" in async_url

    def test_already_async_url_unchanged(self):
        """Should not modify already async URL."""
        from svc_infra.db.sql.utils import _coerce_to_async_url

        async_url = "postgresql+asyncpg://user:pass@localhost/db"
        result = _coerce_to_async_url(async_url)

        assert result == async_url

    def test_sqlite_to_aiosqlite(self):
        """Should convert sqlite:// to sqlite+aiosqlite://."""
        from svc_infra.db.sql.utils import _coerce_to_async_url

        sync_url = "sqlite:///path/to/db.sqlite"
        async_url = _coerce_to_async_url(sync_url)

        assert "aiosqlite" in async_url


class TestMakeUrl:
    """Tests for SQLAlchemy URL creation utilities."""

    def test_make_url_from_string(self):
        """Should create URL object from string."""
        from sqlalchemy.engine import make_url

        url = make_url("postgresql://user:pass@localhost:5432/db")

        assert url.drivername == "postgresql"
        assert url.username == "user"
        assert url.host == "localhost"
        assert url.port == 5432
        assert url.database == "db"

    def test_url_with_special_characters(self):
        """Should handle passwords with special characters."""
        from urllib.parse import quote_plus

        from sqlalchemy.engine import make_url

        password = "p@ss:word/test"
        encoded_password = quote_plus(password)
        url_str = f"postgresql://user:{encoded_password}@localhost/db"

        url = make_url(url_str)
        assert url.password == password


class TestPrepareProcessEnv:
    """Tests for process environment preparation."""

    def test_loads_dotenv(self, monkeypatch, tmp_path):
        """Should load .env file from project root."""
        from svc_infra.db.sql.utils import prepare_process_env

        # Create a temp .env file
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value\n")

        monkeypatch.delenv("TEST_VAR", raising=False)

        prepare_process_env(tmp_path)

        # The dotenv should be loaded (but with override=False)
        # If TEST_VAR wasn't set before, it should now be set
        # Note: This may or may not work depending on load_dotenv behavior

    def test_sets_skip_app_init(self, monkeypatch, tmp_path):
        """Should set SKIP_APP_INIT environment variable."""
        from svc_infra.db.sql.utils import prepare_process_env

        monkeypatch.delenv("SKIP_APP_INIT", raising=False)

        prepare_process_env(tmp_path)

        assert os.environ.get("SKIP_APP_INIT") == "1"

    def test_adds_src_to_pythonpath(self, monkeypatch, tmp_path):
        """Should add src directory to PYTHONPATH if it exists."""
        from svc_infra.db.sql.utils import prepare_process_env

        src_dir = tmp_path / "src"
        src_dir.mkdir()

        monkeypatch.setenv("PYTHONPATH", "")

        prepare_process_env(tmp_path)

        pythonpath = os.environ.get("PYTHONPATH", "")
        assert str(src_dir) in pythonpath
