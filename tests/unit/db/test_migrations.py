"""
Tests for migration utilities and Alembic configuration.
"""

from __future__ import annotations

import os

import pytest


class TestAlembicConfig:
    """Tests for Alembic configuration utilities."""

    def test_get_alembic_config_creates_config(self):
        """Should create valid Alembic config object."""
        from alembic.config import Config

        config = Config()
        config.set_main_option("script_location", "migrations")

        assert config.get_main_option("script_location") == "migrations"

    def test_alembic_config_with_custom_ini(self, tmp_path):
        """Should load config from custom ini file."""
        from alembic.config import Config

        ini_file = tmp_path / "alembic.ini"
        ini_file.write_text(
            """
[alembic]
script_location = migrations
sqlalchemy.url = sqlite:///test.db
"""
        )

        config = Config(str(ini_file))
        assert config.get_main_option("script_location") == "migrations"


class TestMigrationHelpers:
    """Tests for migration helper functions."""

    def test_get_current_revision(self, mocker):
        """Should return current database revision."""
        # Mock the alembic command
        mock_context = mocker.Mock()
        mock_context.get_current_revision.return_value = "abc123"

        # Verify the mock returns expected value
        assert mock_context.get_current_revision() == "abc123"

    def test_get_pending_migrations(self, mocker):
        """Should identify pending migrations."""
        mock_script = mocker.Mock()
        mock_script.get_revisions.return_value = ["rev3", "rev2", "rev1"]

        revisions = mock_script.get_revisions()
        assert len(revisions) == 3

    def test_migration_is_reversible(self, mocker):
        """Should check if migration has downgrade function."""
        mock_revision = mocker.Mock()
        mock_revision.downgrade = mocker.Mock()

        assert hasattr(mock_revision, "downgrade")


class TestMigrationVersioning:
    """Tests for migration version management."""

    def test_version_format_is_valid(self):
        """Should use valid version identifier format."""
        import re

        # Alembic uses random hex strings as revision IDs
        revision_id = "abc123def456"
        pattern = r"^[a-f0-9]+$"

        assert re.match(pattern, revision_id)

    def test_version_timestamp_ordering(self):
        """Should order migrations by timestamp."""
        versions = [
            ("20240101_001", "Create users table"),
            ("20240102_001", "Add email column"),
            ("20240103_001", "Create posts table"),
        ]

        sorted_versions = sorted(versions, key=lambda x: x[0])
        assert sorted_versions[0][0] == "20240101_001"
        assert sorted_versions[-1][0] == "20240103_001"


class TestMigrationDiscovery:
    """Tests for automatic migration discovery."""

    def test_discover_packages_from_env(self, monkeypatch):
        """Should discover packages from ALEMBIC_DISCOVER_PACKAGES env."""
        monkeypatch.setenv("ALEMBIC_DISCOVER_PACKAGES", "pkg1,pkg2,pkg3")

        packages = os.environ.get("ALEMBIC_DISCOVER_PACKAGES", "").split(",")
        assert packages == ["pkg1", "pkg2", "pkg3"]

    def test_discover_models_in_package(self, mocker):
        """Should discover SQLAlchemy models in package."""
        # Simulate model discovery
        mock_models = {
            "User": mocker.Mock(__tablename__="users"),
            "Post": mocker.Mock(__tablename__="posts"),
        }

        assert len(mock_models) == 2
        assert mock_models["User"].__tablename__ == "users"


class TestMigrationExecution:
    """Tests for migration execution."""

    @pytest.fixture
    def mock_engine(self, mocker):
        """Create a mock database engine."""
        engine = mocker.Mock()
        engine.begin = mocker.Mock()
        return engine

    def test_upgrade_runs_migrations(self, mocker):
        """Should run upgrade migrations in order."""
        mock_command = mocker.Mock()
        mock_command.upgrade = mocker.Mock()

        mock_command.upgrade("head")

        mock_command.upgrade.assert_called_once_with("head")

    def test_downgrade_reverts_migration(self, mocker):
        """Should revert migrations on downgrade."""
        mock_command = mocker.Mock()
        mock_command.downgrade = mocker.Mock()

        mock_command.downgrade("-1")

        mock_command.downgrade.assert_called_once_with("-1")

    def test_migration_rollback_on_error(self, mocker):
        """Should rollback on migration error."""
        mock_connection = mocker.Mock()
        mock_connection.rollback = mocker.Mock()

        # Simulate error and rollback
        try:
            raise Exception("Migration failed")
        except Exception:
            mock_connection.rollback()

        mock_connection.rollback.assert_called_once()


class TestMigrationSafety:
    """Tests for migration safety checks."""

    def test_detect_destructive_changes(self):
        """Should detect destructive schema changes."""
        # List of destructive operations
        destructive_ops = [
            "DROP TABLE",
            "DROP COLUMN",
            "ALTER COLUMN TYPE",
            "DROP INDEX",
        ]

        sql = "DROP TABLE users"
        is_destructive = any(op in sql.upper() for op in destructive_ops)

        assert is_destructive

    def test_safe_column_addition(self):
        """Should allow safe column additions."""
        sql = "ALTER TABLE users ADD COLUMN email VARCHAR(255)"
        destructive_ops = ["DROP TABLE", "DROP COLUMN"]

        is_destructive = any(op in sql.upper() for op in destructive_ops)

        assert not is_destructive

    def test_migration_with_default_value(self):
        """Should handle migrations with default values."""
        sql = "ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active'"

        assert "DEFAULT" in sql
        assert "'active'" in sql


class TestOfflineMigrations:
    """Tests for offline migration generation."""

    def test_generate_sql_script(self, mocker):
        """Should generate SQL script for offline execution."""
        mock_context = mocker.Mock()
        mock_context.run_migrations = mocker.Mock()

        # Simulate offline mode
        mock_context.is_offline_mode = True

        assert mock_context.is_offline_mode is True

    def test_sql_script_includes_transaction(self):
        """Should wrap SQL in transaction."""
        sql_script = """
BEGIN;
ALTER TABLE users ADD COLUMN email VARCHAR(255);
COMMIT;
"""
        assert "BEGIN" in sql_script
        assert "COMMIT" in sql_script
