"""Tests for SQL core module - Alembic commands and database setup."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestInitAlembic:
    """Tests for init_alembic function."""

    def test_init_alembic_creates_directories(self, tmp_path: Path) -> None:
        """Test init_alembic creates migrations directory structure."""
        from svc_infra.db.sql.core import init_alembic

        with patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path):
            result = init_alembic()

            assert result.exists()
            assert result.is_dir()
            assert (result / "versions").exists()

    def test_init_alembic_creates_alembic_ini(self, tmp_path: Path) -> None:
        """Test init_alembic creates alembic.ini file."""
        from svc_infra.db.sql.core import init_alembic

        with patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path):
            init_alembic()

            alembic_ini = tmp_path / "alembic.ini"
            assert alembic_ini.exists()

    def test_init_alembic_creates_script_template(self, tmp_path: Path) -> None:
        """Test init_alembic creates script.py.mako template."""
        from svc_infra.db.sql.core import init_alembic

        with patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path):
            result = init_alembic()

            script_template = result / "script.py.mako"
            assert script_template.exists()

    def test_init_alembic_creates_env_py(self, tmp_path: Path) -> None:
        """Test init_alembic creates env.py file."""
        from svc_infra.db.sql.core import init_alembic

        with patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path):
            result = init_alembic()

            env_py = result / "env.py"
            assert env_py.exists()

    def test_init_alembic_with_custom_script_location(self, tmp_path: Path) -> None:
        """Test init_alembic with custom script location."""
        from svc_infra.db.sql.core import init_alembic

        with patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path):
            result = init_alembic(script_location="custom_migrations")

            assert result == tmp_path / "custom_migrations"
            assert result.exists()

    def test_init_alembic_overwrite_true_rewrites_files(self, tmp_path: Path) -> None:
        """Test init_alembic with overwrite=True rewrites existing files."""
        from svc_infra.db.sql.core import init_alembic

        with patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path):
            # First call
            init_alembic()

            # Modify alembic.ini
            alembic_ini = tmp_path / "alembic.ini"
            alembic_ini.write_text("modified content")

            # Second call with overwrite
            init_alembic(overwrite=True)

            # Should be rewritten
            content = alembic_ini.read_text()
            assert "modified content" not in content

    def test_init_alembic_with_discover_packages(self, tmp_path: Path) -> None:
        """Test init_alembic with discover_packages option."""
        from svc_infra.db.sql.core import init_alembic

        with patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path):
            result = init_alembic(discover_packages=["myapp.models", "myapp.db"])

            env_py = result / "env.py"
            assert env_py.exists()


class TestRevision:
    """Tests for revision function."""

    def test_revision_calls_alembic_command(self, tmp_path: Path) -> None:
        """Test revision calls alembic command.revision."""
        from svc_infra.db.sql.core import revision

        with (
            patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path),
            patch("svc_infra.db.sql.core.build_alembic_config") as mock_config,
            patch("svc_infra.db.sql.core.repair_alembic_state_if_needed"),
            patch("svc_infra.db.sql.core.command") as mock_command,
        ):
            mock_cfg = MagicMock()
            mock_config.return_value = mock_cfg

            result = revision("test migration")

            assert result["ok"] is True
            assert result["action"] == "revision"
            mock_command.revision.assert_called_once()

    def test_revision_with_autogenerate(self, tmp_path: Path) -> None:
        """Test revision with autogenerate option."""
        from svc_infra.db.sql.core import revision

        with (
            patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path),
            patch("svc_infra.db.sql.core.build_alembic_config") as mock_config,
            patch("svc_infra.db.sql.core.repair_alembic_state_if_needed"),
            patch("svc_infra.db.sql.core.command"),
            patch("svc_infra.db.sql.core._ensure_db_at_head"),
            patch.dict(os.environ, {"SQL_URL": "postgresql://test/db"}),
        ):
            mock_cfg = MagicMock()
            mock_cfg.get_main_option.return_value = "postgresql://test/db"
            mock_config.return_value = mock_cfg

            result = revision("autogen migration", autogenerate=True)

            assert result["autogenerate"] is True

    def test_revision_raises_without_sql_url_for_autogenerate(self, tmp_path: Path) -> None:
        """Test revision raises error when SQL_URL not set for autogenerate."""
        from svc_infra.db.sql.core import revision

        with (
            patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path),
            patch("svc_infra.db.sql.core.build_alembic_config") as mock_config,
            patch("svc_infra.db.sql.core.repair_alembic_state_if_needed"),
            patch.dict(os.environ, {}, clear=True),
        ):
            mock_cfg = MagicMock()
            mock_cfg.get_main_option.return_value = None
            mock_config.return_value = mock_cfg

            # Clear SQL_URL from environment
            if "SQL_URL" in os.environ:
                del os.environ["SQL_URL"]

            with pytest.raises(RuntimeError, match="SQL_URL is not set"):
                revision("test", autogenerate=True)


class TestUpgrade:
    """Tests for upgrade function."""

    def test_upgrade_calls_alembic_upgrade(self, tmp_path: Path) -> None:
        """Test upgrade calls alembic command.upgrade."""
        from svc_infra.db.sql.core import upgrade

        with (
            patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path),
            patch("svc_infra.db.sql.core.build_alembic_config") as mock_config,
            patch("svc_infra.db.sql.core.repair_alembic_state_if_needed"),
            patch("svc_infra.db.sql.core.command") as mock_command,
        ):
            mock_cfg = MagicMock()
            mock_config.return_value = mock_cfg

            result = upgrade()

            assert result["ok"] is True
            assert result["action"] == "upgrade"
            assert result["target"] == "head"
            mock_command.upgrade.assert_called_once_with(mock_cfg, "head")

    def test_upgrade_with_specific_revision(self, tmp_path: Path) -> None:
        """Test upgrade with specific revision target."""
        from svc_infra.db.sql.core import upgrade

        with (
            patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path),
            patch("svc_infra.db.sql.core.build_alembic_config") as mock_config,
            patch("svc_infra.db.sql.core.repair_alembic_state_if_needed"),
            patch("svc_infra.db.sql.core.command") as mock_command,
        ):
            mock_cfg = MagicMock()
            mock_config.return_value = mock_cfg

            result = upgrade("abc123")

            assert result["target"] == "abc123"
            mock_command.upgrade.assert_called_once_with(mock_cfg, "abc123")


class TestDowngrade:
    """Tests for downgrade function."""

    def test_downgrade_calls_alembic_downgrade(self, tmp_path: Path) -> None:
        """Test downgrade calls alembic command.downgrade."""
        from svc_infra.db.sql.core import downgrade

        with (
            patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path),
            patch("svc_infra.db.sql.core.build_alembic_config") as mock_config,
            patch("svc_infra.db.sql.core.repair_alembic_state_if_needed"),
            patch("svc_infra.db.sql.core.command") as mock_command,
        ):
            mock_cfg = MagicMock()
            mock_config.return_value = mock_cfg

            result = downgrade()

            assert result["ok"] is True
            assert result["action"] == "downgrade"
            assert result["target"] == "-1"
            mock_command.downgrade.assert_called_once_with(mock_cfg, "-1")

    def test_downgrade_with_specific_revision(self, tmp_path: Path) -> None:
        """Test downgrade with specific revision target."""
        from svc_infra.db.sql.core import downgrade

        with (
            patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path),
            patch("svc_infra.db.sql.core.build_alembic_config") as mock_config,
            patch("svc_infra.db.sql.core.repair_alembic_state_if_needed"),
            patch("svc_infra.db.sql.core.command") as mock_command,
        ):
            mock_cfg = MagicMock()
            mock_config.return_value = mock_cfg

            result = downgrade(revision_target="base")

            assert result["target"] == "base"
            mock_command.downgrade.assert_called_once_with(mock_cfg, "base")


class TestCurrent:
    """Tests for current function."""

    def test_current_returns_output(self, tmp_path: Path) -> None:
        """Test current returns stdout output."""
        from svc_infra.db.sql.core import current

        with (
            patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path),
            patch("svc_infra.db.sql.core.build_alembic_config") as mock_config,
            patch("svc_infra.db.sql.core.repair_alembic_state_if_needed"),
            patch("svc_infra.db.sql.core.command") as mock_command,
        ):
            mock_cfg = MagicMock()
            mock_config.return_value = mock_cfg

            # Simulate command output
            def mock_current(cfg, verbose=False):
                print("abc123 (head)")

            mock_command.current.side_effect = mock_current

            result = current()

            assert result["ok"] is True
            assert result["action"] == "current"
            assert "abc123" in result["stdout"]


class TestHistory:
    """Tests for history function."""

    def test_history_returns_output(self, tmp_path: Path) -> None:
        """Test history returns stdout output."""
        from svc_infra.db.sql.core import history

        with (
            patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path),
            patch("svc_infra.db.sql.core.build_alembic_config") as mock_config,
            patch("svc_infra.db.sql.core.repair_alembic_state_if_needed"),
            patch("svc_infra.db.sql.core.command") as mock_command,
        ):
            mock_cfg = MagicMock()
            mock_config.return_value = mock_cfg

            def mock_history(cfg, verbose=False):
                print("abc123 -> def456 (head), initial")

            mock_command.history.side_effect = mock_history

            result = history()

            assert result["ok"] is True
            assert result["action"] == "history"
            assert "abc123" in result["stdout"]


class TestStamp:
    """Tests for stamp function."""

    def test_stamp_calls_alembic_stamp(self, tmp_path: Path) -> None:
        """Test stamp calls alembic command.stamp."""
        from svc_infra.db.sql.core import stamp

        with (
            patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path),
            patch("svc_infra.db.sql.core.build_alembic_config") as mock_config,
            patch("svc_infra.db.sql.core.repair_alembic_state_if_needed"),
            patch("svc_infra.db.sql.core.command") as mock_command,
        ):
            mock_cfg = MagicMock()
            mock_config.return_value = mock_cfg

            result = stamp()

            assert result["ok"] is True
            assert result["action"] == "stamp"
            assert result["target"] == "head"
            mock_command.stamp.assert_called_once_with(mock_cfg, "head")

    def test_stamp_with_specific_revision(self, tmp_path: Path) -> None:
        """Test stamp with specific revision target."""
        from svc_infra.db.sql.core import stamp

        with (
            patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path),
            patch("svc_infra.db.sql.core.build_alembic_config") as mock_config,
            patch("svc_infra.db.sql.core.repair_alembic_state_if_needed"),
            patch("svc_infra.db.sql.core.command") as mock_command,
        ):
            mock_cfg = MagicMock()
            mock_config.return_value = mock_cfg

            result = stamp(revision_target="abc123")

            assert result["target"] == "abc123"
            mock_command.stamp.assert_called_once_with(mock_cfg, "abc123")


class TestMergeHeads:
    """Tests for merge_heads function."""

    def test_merge_heads_calls_alembic_merge(self, tmp_path: Path) -> None:
        """Test merge_heads calls alembic command.merge."""
        from svc_infra.db.sql.core import merge_heads

        with (
            patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path),
            patch("svc_infra.db.sql.core.build_alembic_config") as mock_config,
            patch("svc_infra.db.sql.core.command") as mock_command,
        ):
            mock_cfg = MagicMock()
            mock_config.return_value = mock_cfg

            result = merge_heads(message="merge branches")

            assert result["ok"] is True
            assert result["action"] == "merge_heads"
            assert result["message"] == "merge branches"
            mock_command.merge.assert_called_once_with(mock_cfg, "heads", message="merge branches")


class TestSetupAndMigrateResult:
    """Tests for SetupAndMigrateResult dataclass."""

    def test_to_dict_returns_all_fields(self, tmp_path: Path) -> None:
        """Test to_dict returns all fields as dict."""
        from svc_infra.db.sql.core import SetupAndMigrateResult

        result = SetupAndMigrateResult(
            project_root=tmp_path,
            migrations_dir=tmp_path / "migrations",
            alembic_ini=tmp_path / "alembic.ini",
            created_initial_revision=True,
            created_followup_revision=False,
            upgraded=True,
        )

        result_dict = result.to_dict()

        assert "project_root" in result_dict
        assert "migrations_dir" in result_dict
        assert "alembic_ini" in result_dict
        assert result_dict["created_initial_revision"] is True
        assert result_dict["created_followup_revision"] is False
        assert result_dict["upgraded"] is True


class TestSetupAndMigrate:
    """Tests for setup_and_migrate function."""

    def test_setup_and_migrate_creates_db_if_missing(self, tmp_path: Path) -> None:
        """Test setup_and_migrate creates database if missing."""
        from svc_infra.db.sql.core import setup_and_migrate

        with (
            patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path),
            patch(
                "svc_infra.db.sql.core.get_database_url_from_env",
                return_value="postgresql://test/db",
            ),
            patch("svc_infra.db.sql.core.ensure_database_exists") as mock_ensure,
            patch("svc_infra.db.sql.core.init_alembic") as mock_init,
            patch("svc_infra.db.sql.core.build_alembic_config"),
            patch("svc_infra.db.sql.core.repair_alembic_state_if_needed"),
            patch("svc_infra.db.sql.core.upgrade"),
            patch("svc_infra.db.sql.core.revision"),
        ):
            mock_init.return_value = tmp_path / "migrations"
            (tmp_path / "migrations" / "versions").mkdir(parents=True)

            setup_and_migrate(create_db_if_missing=True)

            mock_ensure.assert_called_once_with("postgresql://test/db")

    def test_setup_and_migrate_skips_db_creation_when_disabled(self, tmp_path: Path) -> None:
        """Test setup_and_migrate skips database creation when disabled."""
        from svc_infra.db.sql.core import setup_and_migrate

        with (
            patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path),
            patch(
                "svc_infra.db.sql.core.get_database_url_from_env",
                return_value="postgresql://test/db",
            ),
            patch("svc_infra.db.sql.core.ensure_database_exists") as mock_ensure,
            patch("svc_infra.db.sql.core.init_alembic") as mock_init,
            patch("svc_infra.db.sql.core.build_alembic_config"),
            patch("svc_infra.db.sql.core.repair_alembic_state_if_needed"),
            patch("svc_infra.db.sql.core.upgrade"),
            patch("svc_infra.db.sql.core.revision"),
        ):
            mock_init.return_value = tmp_path / "migrations"
            (tmp_path / "migrations" / "versions").mkdir(parents=True)

            setup_and_migrate(create_db_if_missing=False)

            mock_ensure.assert_not_called()

    def test_setup_and_migrate_creates_initial_revision(self, tmp_path: Path) -> None:
        """Test setup_and_migrate creates initial revision if none exist."""
        from svc_infra.db.sql.core import setup_and_migrate

        with (
            patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path),
            patch(
                "svc_infra.db.sql.core.get_database_url_from_env",
                return_value="postgresql://test/db",
            ),
            patch("svc_infra.db.sql.core.ensure_database_exists"),
            patch("svc_infra.db.sql.core.init_alembic") as mock_init,
            patch("svc_infra.db.sql.core.build_alembic_config"),
            patch("svc_infra.db.sql.core.repair_alembic_state_if_needed"),
            patch("svc_infra.db.sql.core.upgrade"),
            patch("svc_infra.db.sql.core.revision") as mock_revision,
        ):
            mock_init.return_value = tmp_path / "migrations"
            (tmp_path / "migrations" / "versions").mkdir(parents=True)
            # No .py files in versions = no revisions

            result = setup_and_migrate()

            assert result["ok"] is True
            mock_revision.assert_called()

    def test_setup_and_migrate_returns_result_dict(self, tmp_path: Path) -> None:
        """Test setup_and_migrate returns proper result dict."""
        from svc_infra.db.sql.core import setup_and_migrate

        with (
            patch("svc_infra.db.sql.core.prepare_env", return_value=tmp_path),
            patch(
                "svc_infra.db.sql.core.get_database_url_from_env",
                return_value="postgresql://test/db",
            ),
            patch("svc_infra.db.sql.core.ensure_database_exists"),
            patch("svc_infra.db.sql.core.init_alembic") as mock_init,
            patch("svc_infra.db.sql.core.build_alembic_config"),
            patch("svc_infra.db.sql.core.repair_alembic_state_if_needed"),
            patch("svc_infra.db.sql.core.upgrade"),
            patch("svc_infra.db.sql.core.revision"),
        ):
            mock_init.return_value = tmp_path / "migrations"
            (tmp_path / "migrations" / "versions").mkdir(parents=True)

            result = setup_and_migrate()

            assert result["action"] == "setup_and_migrate"
            assert "project_root" in result
            assert "migrations_dir" in result
            assert "alembic_ini" in result


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports_are_importable(self) -> None:
        """Test all __all__ exports are importable."""
        from svc_infra.db.sql import core

        for name in core.__all__:
            assert hasattr(core, name), f"Missing export: {name}"

    def test_main_functions_are_callable(self) -> None:
        """Test main functions are callable."""
        from svc_infra.db.sql.core import (
            current,
            downgrade,
            history,
            init_alembic,
            merge_heads,
            revision,
            setup_and_migrate,
            stamp,
            upgrade,
        )

        assert callable(init_alembic)
        assert callable(revision)
        assert callable(upgrade)
        assert callable(downgrade)
        assert callable(current)
        assert callable(history)
        assert callable(stamp)
        assert callable(merge_heads)
        assert callable(setup_and_migrate)
