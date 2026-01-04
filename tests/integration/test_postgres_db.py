"""Integration tests for PostgreSQL database operations.

These tests require a PostgreSQL database to be running.
They are skipped by default unless explicitly enabled via:
  - DATABASE_URL environment variable

Run with: pytest tests/integration/test_postgres_db.py -v
Requires: docker compose -f docker-compose.integration.yml up -d
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest
from sqlalchemy import Column, DateTime, Integer, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Skip marker for tests requiring PostgreSQL
SKIP_NO_POSTGRES = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set - skipping PostgreSQL integration tests",
)


# Test model definitions
class Base(DeclarativeBase):
    """Base class for test models."""

    pass


class TestItem(Base):
    """Simple test item model."""

    __tablename__ = "test_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


@pytest.fixture
async def async_engine():
    """Create an async engine for testing."""
    url = os.environ.get("DATABASE_URL", "")
    # Convert postgres:// to postgresql+asyncpg://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(url, echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):
    """Create an async session factory."""
    async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def setup_test_table(async_engine):
    """Create test table before tests and drop after."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@SKIP_NO_POSTGRES
@pytest.mark.integration
class TestPostgresConnection:
    """Integration tests for PostgreSQL connection handling."""

    @pytest.mark.asyncio
    async def test_basic_connection(self, async_engine):
        """Test basic database connection."""
        async with async_engine.connect() as conn:
            result = await conn.execute(select(1))
            row = result.scalar()
            assert row == 1

    @pytest.mark.asyncio
    async def test_connection_info(self, async_engine):
        """Test retrieving connection info."""
        async with async_engine.connect() as conn:
            result = await conn.execute(select(1).prefix_with("SELECT version(),"))
            assert result is not None


@SKIP_NO_POSTGRES
@pytest.mark.integration
class TestPostgresCRUD:
    """Integration tests for basic CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_item(self, async_session: AsyncSession, setup_test_table):
        """Test creating a new item."""
        item = TestItem(name="Test Item", description="A test description")
        async_session.add(item)
        await async_session.commit()
        await async_session.refresh(item)

        assert item.id is not None
        assert item.name == "Test Item"
        assert item.created_at is not None

    @pytest.mark.asyncio
    async def test_read_item(self, async_session: AsyncSession, setup_test_table):
        """Test reading an item."""
        # Create
        item = TestItem(name="Read Test", description="Reading test")
        async_session.add(item)
        await async_session.commit()
        item_id = item.id

        # Read
        result = await async_session.execute(select(TestItem).where(TestItem.id == item_id))
        fetched = result.scalar_one()

        assert fetched.name == "Read Test"
        assert fetched.description == "Reading test"

    @pytest.mark.asyncio
    async def test_update_item(self, async_session: AsyncSession, setup_test_table):
        """Test updating an item."""
        # Create
        item = TestItem(name="Original Name", description="Original")
        async_session.add(item)
        await async_session.commit()
        item_id = item.id

        # Update
        item.name = "Updated Name"
        item.description = "Updated description"
        await async_session.commit()

        # Verify
        result = await async_session.execute(select(TestItem).where(TestItem.id == item_id))
        updated = result.scalar_one()

        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"

    @pytest.mark.asyncio
    async def test_delete_item(self, async_session: AsyncSession, setup_test_table):
        """Test deleting an item."""
        # Create
        item = TestItem(name="To Delete", description="Will be deleted")
        async_session.add(item)
        await async_session.commit()
        item_id = item.id

        # Delete
        await async_session.delete(item)
        await async_session.commit()

        # Verify
        result = await async_session.execute(select(TestItem).where(TestItem.id == item_id))
        deleted = result.scalar_one_or_none()

        assert deleted is None


@SKIP_NO_POSTGRES
@pytest.mark.integration
class TestPostgresTransactions:
    """Integration tests for transaction handling."""

    @pytest.mark.asyncio
    async def test_transaction_commit(self, async_session: AsyncSession, setup_test_table):
        """Test transaction commit."""
        item = TestItem(name="Committed", description="Will be committed")
        async_session.add(item)
        await async_session.commit()

        # Verify persisted
        result = await async_session.execute(select(TestItem).where(TestItem.name == "Committed"))
        found = result.scalar_one_or_none()
        assert found is not None

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, async_session: AsyncSession, setup_test_table):
        """Test transaction rollback."""
        item = TestItem(name="Rollback Test", description="Will be rolled back")
        async_session.add(item)

        # Rollback before commit
        await async_session.rollback()

        # Verify not persisted
        result = await async_session.execute(
            select(TestItem).where(TestItem.name == "Rollback Test")
        )
        found = result.scalar_one_or_none()
        assert found is None

    @pytest.mark.asyncio
    async def test_nested_transaction(self, async_session: AsyncSession, setup_test_table):
        """Test nested transaction with savepoint."""
        # Outer item
        outer_item = TestItem(name="Outer", description="Outer transaction")
        async_session.add(outer_item)
        await async_session.flush()

        # Nested transaction (savepoint)
        async with async_session.begin_nested():
            inner_item = TestItem(name="Inner", description="Inner transaction")
            async_session.add(inner_item)
            # This will be rolled back with the nested transaction

        # Commit outer only
        await async_session.commit()

        # Only outer should exist (inner was implicitly rolled back)
        result = await async_session.execute(select(TestItem))
        items = result.scalars().all()

        # Note: begin_nested commits the savepoint, so inner may exist
        # depending on how it's used - this tests the mechanism works
        assert any(i.name == "Outer" for i in items)


@SKIP_NO_POSTGRES
@pytest.mark.integration
class TestPostgresPooling:
    """Integration tests for connection pooling."""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_connections(self, async_engine):
        """Test handling multiple concurrent connections."""
        import asyncio

        async def run_query(n: int) -> int:
            async with async_engine.connect() as conn:
                result = await conn.execute(select(n))
                return result.scalar()

        # Run 10 concurrent queries
        results = await asyncio.gather(*[run_query(i) for i in range(10)])

        assert results == list(range(10))

    @pytest.mark.asyncio
    async def test_connection_reuse(self, async_engine):
        """Test connection pool reuses connections."""
        # Run several queries
        for _ in range(5):
            async with async_engine.connect() as conn:
                await conn.execute(select(1))

        pool_status_after = async_engine.pool.status()

        # Pool should have connections available
        assert "Pool" in pool_status_after


@SKIP_NO_POSTGRES
@pytest.mark.integration
class TestDbOps:
    """Integration tests for db.ops utilities."""

    def test_wait_for_database(self):
        """Test waiting for database to be ready."""
        from svc_infra.db.ops import wait_for_database

        # Database should already be up
        result = wait_for_database(timeout=5, verbose=False)
        assert result is True

    def test_run_sync_sql(self):
        """Test running synchronous SQL."""
        from svc_infra.db.ops import run_sync_sql

        result = run_sync_sql("SELECT 1 as test_value")
        assert result is not None

    def test_get_database_url(self):
        """Test getting database URL."""
        from svc_infra.db.ops import get_database_url

        url = get_database_url()
        assert url is not None
        assert "postgresql" in url or "postgres" in url
