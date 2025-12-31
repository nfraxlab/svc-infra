"""Unit tests for svc_infra.db.nosql.base module."""

from __future__ import annotations

from pydantic import BaseModel

from svc_infra.db.nosql.base import DocumentBase


class TestDocumentBase:
    """Tests for DocumentBase class."""

    def test_inherits_from_base_model(self) -> None:
        """Test that DocumentBase inherits from Pydantic BaseModel."""
        assert issubclass(DocumentBase, BaseModel)

    def test_from_attributes_config(self) -> None:
        """Test that from_attributes config is set."""
        assert DocumentBase.model_config.get("from_attributes") is True

    def test_can_create_subclass(self) -> None:
        """Test that subclasses can be created."""

        class MyDocument(DocumentBase):
            name: str
            value: int

        doc = MyDocument(name="test", value=42)
        assert doc.name == "test"
        assert doc.value == 42

    def test_subclass_inherits_config(self) -> None:
        """Test that subclasses inherit config."""

        class MyDocument(DocumentBase):
            name: str

        assert MyDocument.model_config.get("from_attributes") is True

    def test_can_create_from_dict(self) -> None:
        """Test that documents can be created from dict."""

        class MyDocument(DocumentBase):
            name: str
            count: int = 0

        data = {"name": "test", "count": 5}
        doc = MyDocument(**data)
        assert doc.name == "test"
        assert doc.count == 5

    def test_model_dump(self) -> None:
        """Test that model_dump works on subclasses."""

        class MyDocument(DocumentBase):
            title: str
            active: bool = True

        doc = MyDocument(title="Test Doc")
        dumped = doc.model_dump()
        assert dumped == {"title": "Test Doc", "active": True}

    def test_model_json_schema(self) -> None:
        """Test that JSON schema can be generated."""

        class MyDocument(DocumentBase):
            name: str
            description: str | None = None

        schema = MyDocument.model_json_schema()
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "description" in schema["properties"]
