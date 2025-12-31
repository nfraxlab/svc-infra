"""Tests for svc_infra.db.nosql.types module."""

from __future__ import annotations

import pytest

# Skip entire module if pymongo/bson is not installed
pytest.importorskip("bson", reason="pymongo not installed")

from bson import ObjectId

from svc_infra.db.nosql.types import PyObjectId


class TestPyObjectIdInheritance:
    """Tests for PyObjectId inheritance."""

    def test_inherits_from_objectid(self) -> None:
        """Should inherit from bson.ObjectId."""
        assert issubclass(PyObjectId, ObjectId)

    def test_instance_is_objectid(self) -> None:
        """Instances should be ObjectId instances."""
        oid = PyObjectId()
        assert isinstance(oid, ObjectId)
        assert isinstance(oid, PyObjectId)


class TestPyObjectIdCreation:
    """Tests for creating PyObjectId instances."""

    def test_create_new_objectid(self) -> None:
        """Should create new ObjectId when no args."""
        oid = PyObjectId()
        assert oid is not None
        assert len(str(oid)) == 24  # ObjectId hex is 24 chars

    def test_create_from_string(self) -> None:
        """Should create from valid ObjectId string."""
        hex_str = "507f1f77bcf86cd799439011"
        oid = PyObjectId(hex_str)
        assert str(oid) == hex_str

    def test_create_from_objectid(self) -> None:
        """Should create from existing ObjectId."""
        original = ObjectId()
        oid = PyObjectId(original)
        assert str(oid) == str(original)


class TestPyObjectIdPydanticSchema:
    """Tests for Pydantic v2 schema integration."""

    def test_has_pydantic_schema_method(self) -> None:
        """Should have __get_pydantic_core_schema__ method."""
        assert hasattr(PyObjectId, "__get_pydantic_core_schema__")
        assert callable(PyObjectId.__get_pydantic_core_schema__)

    def test_schema_method_returns_schema(self) -> None:
        """Schema method should return a core schema."""
        from pydantic_core import core_schema

        def handler(x):
            return core_schema.any_schema()

        # Call the method (it takes source_type and handler args)
        result = PyObjectId.__get_pydantic_core_schema__(None, handler)
        assert result is not None


class TestPyObjectIdValidation:
    """Tests for validation behavior through Pydantic."""

    def test_validate_objectid_instance(self) -> None:
        """Should validate ObjectId instance."""
        from pydantic import BaseModel

        class TestModel(BaseModel):
            id: PyObjectId

        original = ObjectId()
        model = TestModel(id=original)
        assert isinstance(model.id, ObjectId)
        assert str(model.id) == str(original)

    def test_validate_string(self) -> None:
        """Should validate ObjectId string."""
        from pydantic import BaseModel

        class TestModel(BaseModel):
            id: PyObjectId

        hex_str = "507f1f77bcf86cd799439011"
        model = TestModel(id=hex_str)
        assert str(model.id) == hex_str

    def test_validate_invalid_string_raises(self) -> None:
        """Should raise for invalid ObjectId string."""
        from pydantic import BaseModel, ValidationError

        class TestModel(BaseModel):
            id: PyObjectId

        with pytest.raises(ValidationError):
            TestModel(id="not-a-valid-objectid")

    def test_validate_invalid_type_raises(self) -> None:
        """Should raise for invalid type."""
        from pydantic import BaseModel, ValidationError

        class TestModel(BaseModel):
            id: PyObjectId

        with pytest.raises(ValidationError):
            TestModel(id=12345)

    def test_validate_empty_string_raises(self) -> None:
        """Should raise for empty string."""
        from pydantic import BaseModel, ValidationError

        class TestModel(BaseModel):
            id: PyObjectId

        with pytest.raises(ValidationError):
            TestModel(id="")


class TestPyObjectIdSerialization:
    """Tests for serialization behavior."""

    def test_converts_to_string(self) -> None:
        """Should convert to string representation."""
        oid = PyObjectId()
        assert isinstance(str(oid), str)
        assert len(str(oid)) == 24

    def test_string_is_hex(self) -> None:
        """String representation should be hex."""
        oid = PyObjectId()
        hex_str = str(oid)
        # Should be valid hex
        int(hex_str, 16)

    def test_json_serialization_in_model(self) -> None:
        """Should serialize to string in JSON."""
        from pydantic import BaseModel

        class TestModel(BaseModel):
            id: PyObjectId

            model_config = {"json_encoders": {ObjectId: str}}

        oid = ObjectId()
        model = TestModel(id=oid)
        # model_dump should work
        dumped = model.model_dump()
        assert "id" in dumped
