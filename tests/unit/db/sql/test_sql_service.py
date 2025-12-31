"""Tests for svc_infra.db.sql.service module."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from svc_infra.db.sql.service import SqlService


class TestSqlServiceInit:
    """Tests for SqlService initialization."""

    def test_init_with_repo(self) -> None:
        """Should store repository reference."""
        mock_repo = MagicMock()
        service = SqlService(repo=mock_repo)
        assert service.repo is mock_repo

    def test_init_sets_repo_attribute(self) -> None:
        """Should make repo accessible as attribute."""
        mock_repo = MagicMock()
        service = SqlService(repo=mock_repo)
        assert hasattr(service, "repo")


class TestPreCreateHook:
    """Tests for pre_create hook."""

    @pytest.fixture
    def service(self) -> SqlService:
        return SqlService(repo=MagicMock())

    @pytest.mark.asyncio
    async def test_pre_create_returns_data_unchanged(self, service: SqlService) -> None:
        """Default pre_create should return data unchanged."""
        data = {"name": "test", "value": 123}
        result = await service.pre_create(data)
        assert result == data

    @pytest.mark.asyncio
    async def test_pre_create_returns_same_dict_instance(self, service: SqlService) -> None:
        """Default pre_create should return same dict instance."""
        data = {"foo": "bar"}
        result = await service.pre_create(data)
        assert result is data


class TestPreUpdateHook:
    """Tests for pre_update hook."""

    @pytest.fixture
    def service(self) -> SqlService:
        return SqlService(repo=MagicMock())

    @pytest.mark.asyncio
    async def test_pre_update_returns_data_unchanged(self, service: SqlService) -> None:
        """Default pre_update should return data unchanged."""
        data = {"name": "updated", "value": 456}
        result = await service.pre_update(data)
        assert result == data

    @pytest.mark.asyncio
    async def test_pre_update_returns_same_dict_instance(self, service: SqlService) -> None:
        """Default pre_update should return same dict instance."""
        data = {"baz": "qux"}
        result = await service.pre_update(data)
        assert result is data


class TestListMethod:
    """Tests for list method."""

    @pytest.mark.asyncio
    async def test_list_delegates_to_repo(self) -> None:
        """Should delegate to repository list method."""
        mock_repo = MagicMock()
        mock_repo.list = AsyncMock(return_value=["item1", "item2"])
        service = SqlService(repo=mock_repo)
        session = MagicMock()

        result = await service.list(session, limit=10, offset=0)

        mock_repo.list.assert_awaited_once_with(session, limit=10, offset=0, order_by=None)
        assert result == ["item1", "item2"]

    @pytest.mark.asyncio
    async def test_list_passes_order_by(self) -> None:
        """Should pass order_by parameter to repository."""
        mock_repo = MagicMock()
        mock_repo.list = AsyncMock(return_value=[])
        service = SqlService(repo=mock_repo)
        session = MagicMock()

        await service.list(session, limit=5, offset=10, order_by="created_at")

        mock_repo.list.assert_awaited_once_with(session, limit=5, offset=10, order_by="created_at")


class TestCountMethod:
    """Tests for count method."""

    @pytest.mark.asyncio
    async def test_count_delegates_to_repo(self) -> None:
        """Should delegate to repository count method."""
        mock_repo = MagicMock()
        mock_repo.count = AsyncMock(return_value=42)
        service = SqlService(repo=mock_repo)
        session = MagicMock()

        result = await service.count(session)

        mock_repo.count.assert_awaited_once_with(session)
        assert result == 42


class TestGetMethod:
    """Tests for get method."""

    @pytest.mark.asyncio
    async def test_get_delegates_to_repo(self) -> None:
        """Should delegate to repository get method."""
        mock_repo = MagicMock()
        expected = {"id": 1, "name": "test"}
        mock_repo.get = AsyncMock(return_value=expected)
        service = SqlService(repo=mock_repo)
        session = MagicMock()

        result = await service.get(session, 1)

        mock_repo.get.assert_awaited_once_with(session, 1)
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_with_string_id(self) -> None:
        """Should handle string ID values."""
        mock_repo = MagicMock()
        mock_repo.get = AsyncMock(return_value={"id": "uuid-123"})
        service = SqlService(repo=mock_repo)
        session = MagicMock()

        result = await service.get(session, "uuid-123")

        mock_repo.get.assert_awaited_once_with(session, "uuid-123")
        assert result == {"id": "uuid-123"}


class TestCreateMethod:
    """Tests for create method."""

    @pytest.mark.asyncio
    async def test_create_calls_pre_create_hook(self) -> None:
        """Should call pre_create hook before creating."""
        mock_repo = MagicMock()
        mock_repo.create = AsyncMock(return_value={"id": 1})
        service = SqlService(repo=mock_repo)
        service.pre_create = AsyncMock(return_value={"name": "modified"})
        session = MagicMock()

        await service.create(session, {"name": "original"})

        service.pre_create.assert_awaited_once_with({"name": "original"})
        mock_repo.create.assert_awaited_once_with(session, {"name": "modified"})

    @pytest.mark.asyncio
    async def test_create_returns_repo_result(self) -> None:
        """Should return result from repository."""
        mock_repo = MagicMock()
        expected = {"id": 1, "name": "test"}
        mock_repo.create = AsyncMock(return_value=expected)
        service = SqlService(repo=mock_repo)
        session = MagicMock()

        result = await service.create(session, {"name": "test"})

        assert result == expected

    @pytest.mark.asyncio
    async def test_create_duplicate_raises_409(self) -> None:
        """Should raise 409 on duplicate key violation."""
        mock_repo = MagicMock()
        error = IntegrityError("INSERT", {}, Exception("duplicate key value"))
        error.orig = Exception("duplicate key value violates unique")
        mock_repo.create = AsyncMock(side_effect=error)
        service = SqlService(repo=mock_repo)
        session = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await service.create(session, {"name": "test"})

        assert exc_info.value.status_code == 409
        assert "already exists" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_unique_violation_raises_409(self) -> None:
        """Should raise 409 on UniqueViolation."""
        mock_repo = MagicMock()
        error = IntegrityError("INSERT", {}, Exception("UniqueViolation"))
        error.orig = Exception("UniqueViolation")
        mock_repo.create = AsyncMock(side_effect=error)
        service = SqlService(repo=mock_repo)
        session = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await service.create(session, {"name": "test"})

        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_create_not_null_raises_400(self) -> None:
        """Should raise 400 on not-null violation."""
        mock_repo = MagicMock()
        error = IntegrityError("INSERT", {}, Exception("not-null"))
        error.orig = Exception("not-null constraint violation")
        mock_repo.create = AsyncMock(side_effect=error)
        service = SqlService(repo=mock_repo)
        session = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await service.create(session, {"name": None})

        assert exc_info.value.status_code == 400
        assert "Missing required field" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_not_null_violation_raises_400(self) -> None:
        """Should raise 400 on NotNullViolation."""
        mock_repo = MagicMock()
        error = IntegrityError("INSERT", {}, Exception("NotNullViolation"))
        error.orig = Exception("NotNullViolation")
        mock_repo.create = AsyncMock(side_effect=error)
        service = SqlService(repo=mock_repo)
        session = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await service.create(session, {"name": None})

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_create_unknown_integrity_error_reraises(self) -> None:
        """Should re-raise unknown IntegrityError."""
        mock_repo = MagicMock()
        error = IntegrityError("INSERT", {}, Exception("some other error"))
        error.orig = Exception("some other database error")
        mock_repo.create = AsyncMock(side_effect=error)
        service = SqlService(repo=mock_repo)
        session = MagicMock()

        with pytest.raises(IntegrityError):
            await service.create(session, {"name": "test"})

    @pytest.mark.asyncio
    async def test_create_integrity_error_without_orig(self) -> None:
        """Should handle IntegrityError without orig attribute."""
        mock_repo = MagicMock()
        error = IntegrityError("INSERT", {}, Exception("duplicate key value"))
        # Don't set error.orig
        mock_repo.create = AsyncMock(side_effect=error)
        service = SqlService(repo=mock_repo)
        session = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await service.create(session, {"name": "test"})

        assert exc_info.value.status_code == 409


class TestUpdateMethod:
    """Tests for update method."""

    @pytest.mark.asyncio
    async def test_update_calls_pre_update_hook(self) -> None:
        """Should call pre_update hook before updating."""
        mock_repo = MagicMock()
        mock_repo.update = AsyncMock(return_value={"id": 1, "name": "modified"})
        service = SqlService(repo=mock_repo)
        service.pre_update = AsyncMock(return_value={"name": "modified"})
        session = MagicMock()

        await service.update(session, 1, {"name": "original"})

        service.pre_update.assert_awaited_once_with({"name": "original"})
        mock_repo.update.assert_awaited_once_with(session, 1, {"name": "modified"})

    @pytest.mark.asyncio
    async def test_update_returns_repo_result(self) -> None:
        """Should return result from repository."""
        mock_repo = MagicMock()
        expected = {"id": 1, "name": "updated"}
        mock_repo.update = AsyncMock(return_value=expected)
        service = SqlService(repo=mock_repo)
        session = MagicMock()

        result = await service.update(session, 1, {"name": "updated"})

        assert result == expected


class TestDeleteMethod:
    """Tests for delete method."""

    @pytest.mark.asyncio
    async def test_delete_delegates_to_repo(self) -> None:
        """Should delegate to repository delete method."""
        mock_repo = MagicMock()
        mock_repo.delete = AsyncMock(return_value=True)
        service = SqlService(repo=mock_repo)
        session = MagicMock()

        result = await service.delete(session, 1)

        mock_repo.delete.assert_awaited_once_with(session, 1)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_returns_false_if_not_found(self) -> None:
        """Should return False if record not found."""
        mock_repo = MagicMock()
        mock_repo.delete = AsyncMock(return_value=False)
        service = SqlService(repo=mock_repo)
        session = MagicMock()

        result = await service.delete(session, 999)

        assert result is False


class TestSearchMethod:
    """Tests for search method."""

    @pytest.mark.asyncio
    async def test_search_delegates_to_repo(self) -> None:
        """Should delegate to repository search method."""
        mock_repo = MagicMock()
        expected = [{"id": 1, "name": "foo"}, {"id": 2, "name": "foobar"}]
        mock_repo.search = AsyncMock(return_value=expected)
        service = SqlService(repo=mock_repo)
        session = MagicMock()

        result = await service.search(session, q="foo", fields=["name"], limit=10, offset=0)

        mock_repo.search.assert_awaited_once_with(
            session, q="foo", fields=["name"], limit=10, offset=0, order_by=None
        )
        assert result == expected

    @pytest.mark.asyncio
    async def test_search_passes_order_by(self) -> None:
        """Should pass order_by parameter to repository."""
        mock_repo = MagicMock()
        mock_repo.search = AsyncMock(return_value=[])
        service = SqlService(repo=mock_repo)
        session = MagicMock()

        await service.search(
            session, q="test", fields=["name", "email"], limit=5, offset=0, order_by="name"
        )

        mock_repo.search.assert_awaited_once_with(
            session, q="test", fields=["name", "email"], limit=5, offset=0, order_by="name"
        )


class TestCountFilteredMethod:
    """Tests for count_filtered method."""

    @pytest.mark.asyncio
    async def test_count_filtered_delegates_to_repo(self) -> None:
        """Should delegate to repository count_filtered method."""
        mock_repo = MagicMock()
        mock_repo.count_filtered = AsyncMock(return_value=5)
        service = SqlService(repo=mock_repo)
        session = MagicMock()

        result = await service.count_filtered(session, q="foo", fields=["name"])

        mock_repo.count_filtered.assert_awaited_once_with(session, q="foo", fields=["name"])
        assert result == 5


class TestExistsMethod:
    """Tests for exists method."""

    @pytest.mark.asyncio
    async def test_exists_delegates_to_repo(self) -> None:
        """Should delegate to repository exists method."""
        mock_repo = MagicMock()
        mock_repo.exists = AsyncMock(return_value=True)
        service = SqlService(repo=mock_repo)
        session = MagicMock()

        result = await service.exists(session, where={"id": 1})

        mock_repo.exists.assert_awaited_once_with(session, where={"id": 1})
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_when_not_found(self) -> None:
        """Should return False when record doesn't exist."""
        mock_repo = MagicMock()
        mock_repo.exists = AsyncMock(return_value=False)
        service = SqlService(repo=mock_repo)
        session = MagicMock()

        result = await service.exists(session, where={"id": 999})

        assert result is False


class TestCustomServiceSubclass:
    """Tests for subclassing SqlService."""

    @pytest.mark.asyncio
    async def test_subclass_can_override_pre_create(self) -> None:
        """Subclass should be able to override pre_create."""

        class CustomService(SqlService):
            async def pre_create(self, data: dict[str, Any]) -> dict[str, Any]:
                data["created_by"] = "system"
                return data

        mock_repo = MagicMock()
        mock_repo.create = AsyncMock(return_value={"id": 1})
        service = CustomService(repo=mock_repo)
        session = MagicMock()

        await service.create(session, {"name": "test"})

        mock_repo.create.assert_awaited_once_with(session, {"name": "test", "created_by": "system"})

    @pytest.mark.asyncio
    async def test_subclass_can_override_pre_update(self) -> None:
        """Subclass should be able to override pre_update."""

        class CustomService(SqlService):
            async def pre_update(self, data: dict[str, Any]) -> dict[str, Any]:
                data["updated_by"] = "admin"
                return data

        mock_repo = MagicMock()
        mock_repo.update = AsyncMock(return_value={"id": 1})
        service = CustomService(repo=mock_repo)
        session = MagicMock()

        await service.update(session, 1, {"name": "updated"})

        mock_repo.update.assert_awaited_once_with(
            session, 1, {"name": "updated", "updated_by": "admin"}
        )
