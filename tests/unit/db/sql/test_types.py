"""Tests for svc_infra.db.sql.types module."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import CHAR

from svc_infra.db.sql.types import GUID


class MockDialect:
    """Mock dialect for testing."""

    def __init__(self, name: str):
        self.name = name

    def type_descriptor(self, type_):
        return type_


class TestGUIDBasics:
    """Tests for GUID type basic properties."""

    def test_impl_is_char_type(self) -> None:
        """Implementation should be CHAR type."""
        guid = GUID()
        assert isinstance(guid.impl, CHAR)

    def test_cache_ok_is_true(self) -> None:
        """cache_ok should be True."""
        guid = GUID()
        assert guid.cache_ok is True


class TestLoadDialectImpl:
    """Tests for load_dialect_impl method."""

    def test_postgresql_uses_uuid_type(self) -> None:
        """PostgreSQL should use native UUID type."""
        guid = GUID()
        pg_dialect = MockDialect("postgresql")
        result = guid.load_dialect_impl(pg_dialect)
        # Should return PostgreSQL UUID type
        assert isinstance(result, postgresql.UUID)

    def test_sqlite_uses_char36(self) -> None:
        """SQLite should use CHAR(36)."""
        guid = GUID()
        sqlite_dialect = MockDialect("sqlite")
        result = guid.load_dialect_impl(sqlite_dialect)
        assert isinstance(result, CHAR)

    def test_mysql_uses_char36(self) -> None:
        """MySQL should use CHAR(36)."""
        guid = GUID()
        mysql_dialect = MockDialect("mysql")
        result = guid.load_dialect_impl(mysql_dialect)
        assert isinstance(result, CHAR)

    def test_unknown_dialect_uses_char36(self) -> None:
        """Unknown dialects should fall back to CHAR(36)."""
        guid = GUID()
        unknown_dialect = MockDialect("unknown")
        result = guid.load_dialect_impl(unknown_dialect)
        assert isinstance(result, CHAR)


class TestProcessBindParam:
    """Tests for process_bind_param method."""

    def test_none_returns_none(self) -> None:
        """Should return None for None value."""
        guid = GUID()
        result = guid.process_bind_param(None, None)
        assert result is None

    def test_uuid_object_returns_string(self) -> None:
        """Should convert UUID object to string."""
        guid = GUID()
        test_uuid = uuid.uuid4()
        result = guid.process_bind_param(test_uuid, None)
        assert result == str(test_uuid)
        assert isinstance(result, str)

    def test_uuid_string_returns_string(self) -> None:
        """Should accept and validate UUID string."""
        guid = GUID()
        test_uuid = uuid.uuid4()
        result = guid.process_bind_param(str(test_uuid), None)
        assert result == str(test_uuid)

    def test_uuid_with_dashes(self) -> None:
        """Should handle UUID with dashes."""
        guid = GUID()
        uuid_str = "12345678-1234-5678-1234-567812345678"
        result = guid.process_bind_param(uuid_str, None)
        assert result == uuid_str

    def test_uuid_without_dashes(self) -> None:
        """Should handle UUID without dashes."""
        guid = GUID()
        uuid_no_dash = "12345678123456781234567812345678"
        result = guid.process_bind_param(uuid_no_dash, None)
        # Should normalize to dashed format
        assert "-" in result

    def test_invalid_uuid_raises_error(self) -> None:
        """Should raise error for invalid UUID."""
        guid = GUID()
        with pytest.raises(ValueError):
            guid.process_bind_param("not-a-uuid", None)

    def test_uuid_v4(self) -> None:
        """Should handle UUID v4."""
        guid = GUID()
        test_uuid = uuid.uuid4()
        result = guid.process_bind_param(test_uuid, None)
        assert len(result) == 36
        assert result.count("-") == 4


class TestProcessResultValue:
    """Tests for process_result_value method."""

    def test_none_returns_none(self) -> None:
        """Should return None for None value."""
        guid = GUID()
        result = guid.process_result_value(None, None)
        assert result is None

    def test_string_returns_uuid_object(self) -> None:
        """Should convert string to UUID object."""
        guid = GUID()
        uuid_str = "12345678-1234-5678-1234-567812345678"
        result = guid.process_result_value(uuid_str, None)
        assert isinstance(result, uuid.UUID)
        assert str(result) == uuid_str

    def test_uuid_object_returns_uuid_object(self) -> None:
        """Should handle UUID object input."""
        guid = GUID()
        test_uuid = uuid.uuid4()
        result = guid.process_result_value(test_uuid, None)
        assert isinstance(result, uuid.UUID)
        assert result == test_uuid

    def test_uuid_string_roundtrip(self) -> None:
        """Should roundtrip UUID string -> UUID object."""
        guid = GUID()
        original = uuid.uuid4()
        bound = guid.process_bind_param(original, None)
        result = guid.process_result_value(bound, None)
        assert result == original

    def test_invalid_string_raises_error(self) -> None:
        """Should raise error for invalid UUID string."""
        guid = GUID()
        with pytest.raises(ValueError):
            guid.process_result_value("invalid", None)


class TestGUIDIntegration:
    """Integration tests for GUID type."""

    def test_bind_and_result_roundtrip(self) -> None:
        """Should roundtrip through bind and result processing."""
        guid = GUID()
        original = uuid.uuid4()

        # Simulate writing to DB
        bound = guid.process_bind_param(original, None)
        assert isinstance(bound, str)

        # Simulate reading from DB
        result = guid.process_result_value(bound, None)
        assert isinstance(result, uuid.UUID)
        assert result == original

    def test_multiple_uuids_unique(self) -> None:
        """Multiple UUIDs should be unique after processing."""
        guid = GUID()
        uuids = [uuid.uuid4() for _ in range(10)]
        processed = [guid.process_bind_param(u, None) for u in uuids]
        assert len(set(processed)) == 10

    def test_nil_uuid(self) -> None:
        """Should handle nil UUID (all zeros)."""
        guid = GUID()
        nil = uuid.UUID("00000000-0000-0000-0000-000000000000")
        bound = guid.process_bind_param(nil, None)
        result = guid.process_result_value(bound, None)
        assert result == nil
