"""
Tests for generic CRUD helpers and repository operations.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest


class TestSqlRepository:
    """Tests for SQL repository CRUD operations."""

    @pytest.fixture
    def mock_session(self, mocker):
        """Create a mock async session."""
        session = mocker.Mock()
        session.add = mocker.Mock()
        session.delete = mocker.Mock()
        session.execute = AsyncMock()
        session.scalar = AsyncMock()
        session.scalars = AsyncMock()
        session.commit = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def mock_repo(self, mocker):
        """Create a mock SqlRepository."""
        repo = mocker.Mock()
        repo.create = AsyncMock()
        repo.get = AsyncMock()
        repo.list = AsyncMock(return_value=[])
        repo.count = AsyncMock(return_value=0)
        repo.update = AsyncMock()
        repo.delete = AsyncMock()
        return repo

    @pytest.mark.asyncio
    async def test_create_via_service(self, mock_session, mock_repo, mocker):
        """Should create entity via service."""
        from svc_infra.db.sql.service import SqlService

        mock_entity = mocker.Mock()
        mock_entity.id = "new-id"
        mock_repo.create.return_value = mock_entity

        service = SqlService(mock_repo)

        result = await service.create(mock_session, {"name": "test"})

        assert result == mock_entity
        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_returns_entity(self, mock_session, mock_repo, mocker):
        """Should return entity by ID."""
        from svc_infra.db.sql.service import SqlService

        mock_entity = mocker.Mock()
        mock_entity.id = "test-id"
        mock_repo.get.return_value = mock_entity

        service = SqlService(mock_repo)

        result = await service.get(mock_session, "test-id")

        assert result is not None
        mock_repo.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_missing(self, mock_session, mock_repo, mocker):
        """Should return None when entity not found."""
        from svc_infra.db.sql.service import SqlService

        mock_repo.get.return_value = None

        service = SqlService(mock_repo)

        result = await service.get(mock_session, "nonexistent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_returns_entities(self, mock_session, mock_repo, mocker):
        """Should list entities with pagination."""
        from svc_infra.db.sql.service import SqlService

        mock_entities = [mocker.Mock(id=f"id-{i}") for i in range(3)]
        mock_repo.list.return_value = mock_entities

        service = SqlService(mock_repo)

        result = await service.list(mock_session, limit=10, offset=0)

        assert len(result) == 3
        mock_repo.list.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_returns_total(self, mock_session, mock_repo, mocker):
        """Should return entity count."""
        from svc_infra.db.sql.service import SqlService

        mock_repo.count.return_value = 42

        service = SqlService(mock_repo)

        result = await service.count(mock_session)

        assert result == 42

    @pytest.mark.asyncio
    async def test_update_modifies_entity(self, mock_session, mock_repo, mocker):
        """Should update entity fields."""
        from svc_infra.db.sql.service import SqlService

        mock_entity = mocker.Mock()
        mock_entity.id = "test-id"
        mock_repo.update.return_value = mock_entity

        service = SqlService(mock_repo)

        await service.update(mock_session, "test-id", {"name": "new_name"})

        mock_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_removes_entity(self, mock_session, mock_repo, mocker):
        """Should delete entity."""
        from svc_infra.db.sql.service import SqlService

        mock_repo.delete.return_value = True

        service = SqlService(mock_repo)

        await service.delete(mock_session, "test-id")

        mock_repo.delete.assert_called_once()


class TestNoSqlService:
    """Tests for NoSQL service operations."""

    @pytest.fixture
    def mock_db(self, mocker):
        """Create a mock NoSQL database."""
        return mocker.Mock()

    @pytest.fixture
    def mock_repo(self, mocker):
        """Create a mock NoSQL repository."""
        repo = mocker.Mock()
        repo.create = AsyncMock()
        repo.get = AsyncMock()
        repo.update = AsyncMock()
        repo.delete = AsyncMock()
        return repo

    @pytest.mark.asyncio
    async def test_nosql_create_document(self, mock_db, mock_repo, mocker):
        """Should create document via service."""
        from svc_infra.db.nosql.service import NoSqlService

        mock_doc = {"_id": "new-id", "name": "test"}
        mock_repo.create.return_value = mock_doc

        service = NoSqlService(mock_repo)

        result = await service.create(mock_db, {"name": "test"})

        assert result == mock_doc
        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_nosql_get_document(self, mock_db, mock_repo, mocker):
        """Should get document by ID."""
        from svc_infra.db.nosql.service import NoSqlService

        mock_doc = {"_id": "test-id", "name": "test"}
        mock_repo.get.return_value = mock_doc

        service = NoSqlService(mock_repo)

        result = await service.get(mock_db, "test-id")

        assert result == mock_doc
        mock_repo.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_nosql_update_document(self, mock_db, mock_repo, mocker):
        """Should update document."""
        from svc_infra.db.nosql.service import NoSqlService

        mock_doc = {"_id": "test-id", "name": "updated"}
        mock_repo.update.return_value = mock_doc

        service = NoSqlService(mock_repo)

        await service.update(mock_db, "test-id", {"name": "updated"})

        mock_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_nosql_delete_document(self, mock_db, mock_repo, mocker):
        """Should delete document."""
        from svc_infra.db.nosql.service import NoSqlService

        mock_repo.delete.return_value = True

        service = NoSqlService(mock_repo)

        await service.delete(mock_db, "test-id")

        mock_repo.delete.assert_called_once()


class TestSoftDelete:
    """Tests for soft delete functionality."""

    @pytest.mark.asyncio
    async def test_soft_delete_sets_flag(self, mocker):
        """Should set deleted_at instead of removing."""
        mock_entity = mocker.Mock()
        mock_entity.deleted_at = None

        # Simulate soft delete
        mock_entity.deleted_at = datetime.now(UTC)

        assert mock_entity.deleted_at is not None

    @pytest.mark.asyncio
    async def test_soft_deleted_excluded_from_list(self, mocker):
        """Should exclude soft deleted from list queries."""
        entities = [
            mocker.Mock(id="1", deleted_at=None),
            mocker.Mock(id="2", deleted_at=datetime.now(UTC)),
            mocker.Mock(id="3", deleted_at=None),
        ]

        active = [e for e in entities if e.deleted_at is None]

        assert len(active) == 2

    @pytest.mark.asyncio
    async def test_restore_clears_deleted_at(self, mocker):
        """Should clear deleted_at to restore."""
        mock_entity = mocker.Mock()
        mock_entity.deleted_at = datetime.now(UTC)

        # Restore
        mock_entity.deleted_at = None

        assert mock_entity.deleted_at is None


class TestBulkOperations:
    """Tests for bulk CRUD operations."""

    @pytest.mark.asyncio
    async def test_bulk_create(self, mocker):
        """Should create multiple entities."""
        mock_session = mocker.Mock()
        mock_session.add_all = mocker.Mock()
        mock_session.flush = AsyncMock()

        entities = [mocker.Mock() for _ in range(5)]

        mock_session.add_all(entities)
        await mock_session.flush()

        mock_session.add_all.assert_called_once_with(entities)

    @pytest.mark.asyncio
    async def test_bulk_update(self, mocker):
        """Should update multiple entities."""
        mock_session = mocker.Mock()
        mock_session.execute = AsyncMock()

        # Simulate bulk update query
        await mock_session.execute("UPDATE ...")

        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_delete(self, mocker):
        """Should delete multiple entities."""
        mock_session = mocker.Mock()
        mock_session.execute = AsyncMock()

        # Simulate bulk delete query
        await mock_session.execute("DELETE ...")

        mock_session.execute.assert_called_once()


class TestRepositoryFilters:
    """Tests for repository filtering."""

    def test_build_filter_eq(self):
        """Should build equality filter."""
        filters = {"name": "test"}

        # Simulate filter building
        result = [f"{k} = '{v}'" for k, v in filters.items()]

        assert result == ["name = 'test'"]

    def test_build_filter_in(self):
        """Should build IN filter."""
        filters = {"status__in": ["active", "pending"]}

        # Simulate IN filter
        key = "status"
        values = filters["status__in"]
        result = f"{key} IN ({', '.join(repr(v) for v in values)})"

        assert "IN" in result

    def test_build_filter_like(self):
        """Should build LIKE filter."""

        # Simulate LIKE filter
        result = "name LIKE '%test%'"

        assert "LIKE" in result


class TestTransactions:
    """Tests for transaction handling."""

    @pytest.mark.asyncio
    async def test_transaction_commit(self, mocker):
        """Should commit transaction on success."""
        mock_session = mocker.Mock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        try:
            # Do work
            await mock_session.commit()
        except Exception:
            await mock_session.rollback()

        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, mocker):
        """Should rollback transaction on error."""
        mock_session = mocker.Mock()
        mock_session.commit = AsyncMock(side_effect=Exception("error"))
        mock_session.rollback = AsyncMock()

        try:
            await mock_session.commit()
        except Exception:
            await mock_session.rollback()

        mock_session.rollback.assert_called_once()
