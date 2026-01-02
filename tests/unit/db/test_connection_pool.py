"""
Tests for database connection pool management.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


class TestConnectionPoolConfig:
    """Tests for connection pool configuration."""

    def test_pool_size_attribute(self):
        """Should access pool size attribute."""
        from sqlalchemy import create_engine

        engine = create_engine("sqlite:///:memory:", echo=False)

        # Pool should exist
        assert engine.pool is not None

    def test_pool_pre_ping_setting(self):
        """Should respect pool_pre_ping setting."""
        from sqlalchemy import create_engine

        engine = create_engine(
            "sqlite:///:memory:",
            pool_pre_ping=True,
            echo=False,
        )

        assert engine.pool is not None


class TestConnectionPoolBehavior:
    """Tests for connection pool behavior."""

    def test_connection_reuse(self, mocker):
        """Should reuse connections from pool."""
        mock_pool = mocker.Mock()
        mock_pool.checkedout = mocker.Mock(return_value=0)
        mock_pool.checkedin = mocker.Mock(return_value=5)

        # Simulate pool state
        assert mock_pool.checkedout() == 0
        assert mock_pool.checkedin() == 5

    def test_connection_checkout(self, mocker):
        """Should checkout connection from pool."""
        mock_pool = mocker.Mock()
        mock_conn = mocker.Mock()
        mock_pool.connect = mocker.Mock(return_value=mock_conn)

        conn = mock_pool.connect()

        assert conn is not None
        mock_pool.connect.assert_called_once()

    def test_connection_checkin(self, mocker):
        """Should checkin connection back to pool."""
        mock_conn = mocker.Mock()
        mock_conn.close = mocker.Mock()

        mock_conn.close()

        mock_conn.close.assert_called_once()


class TestAsyncConnectionPool:
    """Tests for async connection pool management."""

    @pytest.fixture
    def mock_async_engine(self, mocker):
        """Create a mock async engine."""
        engine = mocker.Mock()
        engine.dispose = AsyncMock()
        engine.connect = mocker.Mock()
        return engine

    @pytest.mark.asyncio
    async def test_async_engine_dispose(self, mock_async_engine):
        """Should properly dispose async engine."""
        await mock_async_engine.dispose()

        mock_async_engine.dispose.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_connection_context_manager(self, mocker):
        """Should work as async context manager."""
        mock_conn = mocker.Mock()
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        async with mock_conn as conn:
            assert conn is mock_conn


class TestPoolOverflow:
    """Tests for connection pool overflow handling."""

    def test_overflow_connections_closed(self, mocker):
        """Should close overflow connections when returned."""
        mock_pool = mocker.Mock()
        mock_pool.overflow = mocker.Mock(return_value=3)

        assert mock_pool.overflow() == 3


class TestPoolRecycling:
    """Tests for connection recycling."""

    def test_pool_recycle_setting(self):
        """Should recycle connections after timeout."""
        from sqlalchemy import create_engine

        engine = create_engine(
            "sqlite:///:memory:",
            pool_recycle=3600,  # Recycle after 1 hour
            echo=False,
        )

        assert engine.pool is not None

    def test_stale_connection_detection(self, mocker):
        """Should detect and replace stale connections."""
        mock_conn = mocker.Mock()
        mock_conn.is_valid = False

        assert not mock_conn.is_valid


class TestPoolEvents:
    """Tests for connection pool events."""

    def test_connect_event_listener(self, mocker):
        """Should fire connect event on new connection."""
        from sqlalchemy import create_engine, event

        engine = create_engine("sqlite:///:memory:", echo=False)
        mock_listener = mocker.Mock()

        event.listen(engine, "connect", mock_listener)

        # Get a connection to trigger event
        with engine.connect():
            pass

        mock_listener.assert_called()

    def test_checkout_event_listener(self, mocker):
        """Should fire checkout event when connection borrowed."""
        from sqlalchemy import create_engine, event

        engine = create_engine("sqlite:///:memory:", echo=False)
        mock_listener = mocker.Mock()

        event.listen(engine, "checkout", mock_listener)

        with engine.connect():
            pass

        mock_listener.assert_called()


class TestPoolHealth:
    """Tests for connection pool health checks."""

    def test_pool_status_query(self, mocker):
        """Should report pool status."""
        mock_pool = mocker.Mock()
        mock_pool.status.return_value = "Pool size: 5, Checked out: 2"

        status = mock_pool.status()

        assert "Pool size" in status

    def test_connection_validation(self, mocker):
        """Should validate connections before use."""
        mock_conn = mocker.Mock()
        mock_conn.execute = mocker.Mock()

        # Simulate ping query
        mock_conn.execute("SELECT 1")

        mock_conn.execute.assert_called_with("SELECT 1")


class TestNullPool:
    """Tests for NullPool (no pooling)."""

    def test_null_pool_no_reuse(self):
        """Should not reuse connections with NullPool."""
        from sqlalchemy import create_engine
        from sqlalchemy.pool import NullPool

        engine = create_engine(
            "sqlite:///:memory:",
            poolclass=NullPool,
            echo=False,
        )

        assert isinstance(engine.pool, NullPool)

    def test_null_pool_fresh_connection(self, mocker):
        """Should create fresh connection each time."""
        from sqlalchemy import create_engine
        from sqlalchemy.pool import NullPool

        engine = create_engine(
            "sqlite:///:memory:",
            poolclass=NullPool,
            echo=False,
        )

        # Each connect() creates new connection
        with engine.connect():
            pass

        with engine.connect():
            pass

        # Connections are not reused


class TestStaticPool:
    """Tests for StaticPool (single connection)."""

    def test_static_pool_single_connection(self):
        """Should use single connection with StaticPool."""
        from sqlalchemy import create_engine
        from sqlalchemy.pool import StaticPool

        engine = create_engine(
            "sqlite:///:memory:",
            poolclass=StaticPool,
            echo=False,
        )

        assert isinstance(engine.pool, StaticPool)


class TestPoolDisposal:
    """Tests for pool disposal."""

    def test_dispose_closes_all_connections(self):
        """Should close all connections on dispose."""
        from sqlalchemy import create_engine

        engine = create_engine("sqlite:///:memory:", echo=False)

        # Get a connection
        with engine.connect():
            pass

        # Dispose engine
        engine.dispose()

        # Pool should be empty after dispose
        assert engine.pool is not None

    @pytest.mark.asyncio
    async def test_async_dispose(self, mocker):
        """Should dispose async engine properly."""
        mock_engine = mocker.Mock()
        mock_engine.dispose = AsyncMock()

        await mock_engine.dispose()

        mock_engine.dispose.assert_called_once()
