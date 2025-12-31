"""Tests for svc_infra.db.sql.repository module."""

from __future__ import annotations

from svc_infra.db.sql.repository import SqlRepository, _escape_ilike


class TestEscapeIlike:
    """Tests for _escape_ilike function."""

    def test_escapes_percent(self) -> None:
        """Escapes percent sign."""
        result = _escape_ilike("100%")
        assert result == "100\\%"

    def test_escapes_underscore(self) -> None:
        """Escapes underscore."""
        result = _escape_ilike("user_name")
        assert result == "user\\_name"

    def test_escapes_backslash(self) -> None:
        """Escapes backslash."""
        result = _escape_ilike("path\\to\\file")
        assert result == "path\\\\to\\\\file"

    def test_escapes_all_special_chars(self) -> None:
        """Escapes all special characters together."""
        result = _escape_ilike("100% user_name\\test")
        assert result == "100\\% user\\_name\\\\test"

    def test_plain_string_unchanged(self) -> None:
        """Plain string without special chars is unchanged."""
        result = _escape_ilike("hello world")
        assert result == "hello world"

    def test_empty_string(self) -> None:
        """Empty string returns empty string."""
        result = _escape_ilike("")
        assert result == ""


class TestSqlRepositoryInit:
    """Tests for SqlRepository initialization."""

    def test_default_values(self) -> None:
        """Default values are set correctly."""

        class MockModel:
            id = None

        repo = SqlRepository(model=MockModel)
        assert repo.model is MockModel
        assert repo.id_attr == "id"
        assert repo.soft_delete is False
        assert repo.soft_delete_field == "deleted_at"
        assert repo.soft_delete_flag_field is None
        assert repo.immutable_fields == {"id", "created_at", "updated_at"}

    def test_custom_id_attr(self) -> None:
        """Custom id attribute is set."""

        class MockModel:
            uuid = None

        repo = SqlRepository(model=MockModel, id_attr="uuid")
        assert repo.id_attr == "uuid"

    def test_soft_delete_enabled(self) -> None:
        """Soft delete can be enabled."""

        class MockModel:
            id = None

        repo = SqlRepository(model=MockModel, soft_delete=True)
        assert repo.soft_delete is True

    def test_custom_soft_delete_field(self) -> None:
        """Custom soft delete field is set."""

        class MockModel:
            id = None

        repo = SqlRepository(
            model=MockModel,
            soft_delete=True,
            soft_delete_field="removed_at",
        )
        assert repo.soft_delete_field == "removed_at"

    def test_soft_delete_flag_field(self) -> None:
        """Soft delete flag field can be set."""

        class MockModel:
            id = None

        repo = SqlRepository(
            model=MockModel,
            soft_delete=True,
            soft_delete_flag_field="is_active",
        )
        assert repo.soft_delete_flag_field == "is_active"

    def test_custom_immutable_fields(self) -> None:
        """Custom immutable fields are set."""

        class MockModel:
            id = None

        repo = SqlRepository(
            model=MockModel,
            immutable_fields={"id", "tenant_id"},
        )
        assert repo.immutable_fields == {"id", "tenant_id"}


class TestSqlRepositoryHelpers:
    """Tests for SqlRepository helper methods."""

    def test_model_columns_callable(self) -> None:
        """_model_columns is callable."""
        from sqlalchemy import Column, Integer, String
        from sqlalchemy.orm import declarative_base

        Base = declarative_base()

        class TestModel(Base):
            __tablename__ = "test"
            id = Column(Integer, primary_key=True)
            name = Column(String)

        repo = SqlRepository(model=TestModel)
        cols = repo._model_columns()
        assert "id" in cols
        assert "name" in cols

    def test_id_column_callable(self) -> None:
        """_id_column is callable."""
        from sqlalchemy import Column, Integer, String
        from sqlalchemy.orm import declarative_base

        Base = declarative_base()

        class TestModel(Base):
            __tablename__ = "test2"
            id = Column(Integer, primary_key=True)
            name = Column(String)

        repo = SqlRepository(model=TestModel)
        id_col = repo._id_column()
        assert id_col is not None
