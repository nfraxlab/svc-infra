"""Tests for svc_infra.db.sql.constants module."""

from __future__ import annotations

import re

from svc_infra.db.sql.constants import (
    ALEMBIC_INI_TEMPLATE,
    ALEMBIC_SCRIPT_TEMPLATE,
    ASYNC_DRIVER_HINT,
    DEFAULT_DB_ENV_VARS,
)


class TestDefaultDBEnvVars:
    """Tests for DEFAULT_DB_ENV_VARS constant."""

    def test_is_sequence(self) -> None:
        """Should be a sequence."""
        assert hasattr(DEFAULT_DB_ENV_VARS, "__iter__")

    def test_contains_sql_url(self) -> None:
        """Should contain SQL_URL."""
        assert "SQL_URL" in DEFAULT_DB_ENV_VARS

    def test_contains_db_url(self) -> None:
        """Should contain DB_URL."""
        assert "DB_URL" in DEFAULT_DB_ENV_VARS

    def test_contains_database_url(self) -> None:
        """Should contain DATABASE_URL for Heroku compatibility."""
        assert "DATABASE_URL" in DEFAULT_DB_ENV_VARS

    def test_sql_url_is_first(self) -> None:
        """SQL_URL should be first (canonical name)."""
        assert DEFAULT_DB_ENV_VARS[0] == "SQL_URL"

    def test_has_multiple_entries(self) -> None:
        """Should have multiple fallback entries."""
        assert len(DEFAULT_DB_ENV_VARS) >= 3

    def test_all_are_strings(self) -> None:
        """All entries should be strings."""
        for var in DEFAULT_DB_ENV_VARS:
            assert isinstance(var, str)


class TestAsyncDriverHint:
    """Tests for ASYNC_DRIVER_HINT regex pattern."""

    def test_is_compiled_regex(self) -> None:
        """Should be a compiled regex."""
        assert isinstance(ASYNC_DRIVER_HINT, re.Pattern)

    def test_matches_asyncpg(self) -> None:
        """Should match +asyncpg driver."""
        url = "postgresql+asyncpg://user:pass@host/db"
        assert ASYNC_DRIVER_HINT.search(url)

    def test_matches_aiosqlite(self) -> None:
        """Should match +aiosqlite driver."""
        url = "sqlite+aiosqlite:///path/to/db.sqlite"
        assert ASYNC_DRIVER_HINT.search(url)

    def test_matches_aiomysql(self) -> None:
        """Should match +aiomysql driver."""
        url = "mysql+aiomysql://user:pass@host/db"
        assert ASYNC_DRIVER_HINT.search(url)

    def test_matches_asyncmy(self) -> None:
        """Should match +asyncmy driver."""
        url = "mysql+asyncmy://user:pass@host/db"
        assert ASYNC_DRIVER_HINT.search(url)

    def test_matches_generic_async(self) -> None:
        """Should match generic +async driver."""
        url = "postgresql+async://user:pass@host/db"
        assert ASYNC_DRIVER_HINT.search(url)

    def test_does_not_match_psycopg2(self) -> None:
        """Should not match sync psycopg2 driver."""
        url = "postgresql+psycopg2://user:pass@host/db"
        assert not ASYNC_DRIVER_HINT.search(url)

    def test_does_not_match_plain_postgresql(self) -> None:
        """Should not match plain postgresql."""
        url = "postgresql://user:pass@host/db"
        assert not ASYNC_DRIVER_HINT.search(url)

    def test_does_not_match_pymysql(self) -> None:
        """Should not match sync pymysql driver."""
        url = "mysql+pymysql://user:pass@host/db"
        assert not ASYNC_DRIVER_HINT.search(url)

    def test_does_not_match_pysqlite(self) -> None:
        """Should not match sync pysqlite driver."""
        url = "sqlite+pysqlite:///path/to/db.sqlite"
        assert not ASYNC_DRIVER_HINT.search(url)


class TestAlembicIniTemplate:
    """Tests for ALEMBIC_INI_TEMPLATE constant."""

    def test_is_string(self) -> None:
        """Should be a string."""
        assert isinstance(ALEMBIC_INI_TEMPLATE, str)

    def test_contains_alembic_section(self) -> None:
        """Should contain [alembic] section."""
        assert "[alembic]" in ALEMBIC_INI_TEMPLATE

    def test_contains_script_location_placeholder(self) -> None:
        """Should contain script_location placeholder."""
        assert "script_location" in ALEMBIC_INI_TEMPLATE

    def test_contains_sqlalchemy_url_placeholder(self) -> None:
        """Should contain sqlalchemy.url or placeholder."""
        assert "sqlalchemy" in ALEMBIC_INI_TEMPLATE.lower()

    def test_not_empty(self) -> None:
        """Should not be empty."""
        assert len(ALEMBIC_INI_TEMPLATE) > 10


class TestAlembicScriptTemplate:
    """Tests for ALEMBIC_SCRIPT_TEMPLATE constant."""

    def test_is_string(self) -> None:
        """Should be a string."""
        assert isinstance(ALEMBIC_SCRIPT_TEMPLATE, str)

    def test_contains_revision(self) -> None:
        """Should contain revision variable."""
        assert "revision" in ALEMBIC_SCRIPT_TEMPLATE

    def test_contains_down_revision(self) -> None:
        """Should contain down_revision variable."""
        assert "down_revision" in ALEMBIC_SCRIPT_TEMPLATE

    def test_contains_upgrade_function(self) -> None:
        """Should contain upgrade function."""
        assert "upgrade" in ALEMBIC_SCRIPT_TEMPLATE

    def test_contains_downgrade_function(self) -> None:
        """Should contain downgrade function."""
        assert "downgrade" in ALEMBIC_SCRIPT_TEMPLATE

    def test_contains_alembic_import(self) -> None:
        """Should import from alembic."""
        assert "alembic" in ALEMBIC_SCRIPT_TEMPLATE

    def test_not_empty(self) -> None:
        """Should not be empty."""
        assert len(ALEMBIC_SCRIPT_TEMPLATE) > 50


class TestModuleExports:
    """Tests for module __all__ exports."""

    def test_default_db_env_vars_exported(self) -> None:
        """DEFAULT_DB_ENV_VARS should be importable."""
        from svc_infra.db.sql.constants import DEFAULT_DB_ENV_VARS

        assert DEFAULT_DB_ENV_VARS is not None

    def test_async_driver_hint_exported(self) -> None:
        """ASYNC_DRIVER_HINT should be importable."""
        from svc_infra.db.sql.constants import ASYNC_DRIVER_HINT

        assert ASYNC_DRIVER_HINT is not None
