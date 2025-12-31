"""Tests for svc_infra.billing.async_service module."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from svc_infra.billing.async_service import AsyncBillingService
from svc_infra.billing.models import Invoice, InvoiceLine, UsageEvent


class TestAsyncBillingServiceInit:
    """Tests for AsyncBillingService initialization."""

    def test_init_sets_session_and_tenant(self) -> None:
        """Session and tenant_id are stored."""
        mock_session = MagicMock()
        service = AsyncBillingService(mock_session, tenant_id="test-tenant")

        assert service.session is mock_session
        assert service.tenant_id == "test-tenant"


class TestRecordUsage:
    """Tests for record_usage method."""

    @pytest.mark.asyncio
    async def test_record_usage_creates_event(self) -> None:
        """record_usage creates a UsageEvent."""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        service = AsyncBillingService(mock_session, tenant_id="tenant-123")

        result = await service.record_usage(
            metric="api_calls",
            amount=5,
            at=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
            idempotency_key="unique-key-1",
            metadata={"endpoint": "/api/users"},
        )

        assert isinstance(result, str)
        assert len(result) == 36  # UUID format
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

        # Verify the event was created with correct values
        call_args = mock_session.add.call_args[0][0]
        assert isinstance(call_args, UsageEvent)
        assert call_args.tenant_id == "tenant-123"
        assert call_args.metric == "api_calls"
        assert call_args.amount == 5
        assert call_args.idempotency_key == "unique-key-1"

    @pytest.mark.asyncio
    async def test_record_usage_adds_utc_to_naive_datetime(self) -> None:
        """Naive datetime gets UTC timezone."""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        service = AsyncBillingService(mock_session, tenant_id="tenant-123")

        naive_dt = datetime(2024, 1, 15, 10, 30)  # No tzinfo
        await service.record_usage(
            metric="test",
            amount=1,
            at=naive_dt,
            idempotency_key="key",
            metadata=None,
        )

        call_args = mock_session.add.call_args[0][0]
        assert call_args.at_ts.tzinfo is not None

    @pytest.mark.asyncio
    async def test_record_usage_with_none_metadata(self) -> None:
        """None metadata becomes empty dict."""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        service = AsyncBillingService(mock_session, tenant_id="tenant-123")

        await service.record_usage(
            metric="test",
            amount=1,
            at=datetime.now(UTC),
            idempotency_key="key",
            metadata=None,
        )

        call_args = mock_session.add.call_args[0][0]
        assert call_args.metadata_json == {}


class TestAggregateDaily:
    """Tests for aggregate_daily method."""

    @pytest.mark.asyncio
    async def test_aggregate_daily_sums_events(self) -> None:
        """Aggregates events for the day."""
        mock_session = AsyncMock()

        # Create mock events
        events = [
            MagicMock(amount=10),
            MagicMock(amount=20),
            MagicMock(amount=30),
        ]

        # Mock execute for events query
        mock_execute = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = events
        mock_execute.scalars.return_value = mock_scalars

        # Mock execute for aggregate query (returns None = new aggregate)
        mock_agg_result = MagicMock()
        mock_agg_result.scalar_one_or_none.return_value = None

        mock_session.execute = AsyncMock(side_effect=[mock_execute, mock_agg_result])
        mock_session.add = MagicMock()

        service = AsyncBillingService(mock_session, tenant_id="tenant-123")

        result = await service.aggregate_daily(
            metric="api_calls",
            day_start=datetime(2024, 1, 15, tzinfo=UTC),
        )

        assert result == 60  # 10 + 20 + 30
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_aggregate_daily_updates_existing(self) -> None:
        """Updates existing aggregate instead of creating new."""
        mock_session = AsyncMock()

        # Create mock events
        events = [MagicMock(amount=50)]

        mock_execute = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = events
        mock_execute.scalars.return_value = mock_scalars

        # Existing aggregate
        existing_agg = MagicMock()
        existing_agg.total = 100

        mock_agg_result = MagicMock()
        mock_agg_result.scalar_one_or_none.return_value = existing_agg

        mock_session.execute = AsyncMock(side_effect=[mock_execute, mock_agg_result])
        mock_session.add = MagicMock()

        service = AsyncBillingService(mock_session, tenant_id="tenant-123")

        result = await service.aggregate_daily(
            metric="api_calls",
            day_start=datetime(2024, 1, 15, tzinfo=UTC),
        )

        assert result == 50
        assert existing_agg.total == 50  # Updated
        mock_session.add.assert_not_called()


class TestListDailyAggregates:
    """Tests for list_daily_aggregates method."""

    @pytest.mark.asyncio
    async def test_list_daily_aggregates_returns_list(self) -> None:
        """Returns list of aggregates."""
        mock_session = AsyncMock()

        aggs = [
            MagicMock(total=100),
            MagicMock(total=200),
        ]

        mock_execute = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = aggs
        mock_execute.scalars.return_value = mock_scalars
        mock_session.execute = mock_execute

        service = AsyncBillingService(mock_session, tenant_id="tenant-123")

        result = await service.list_daily_aggregates(
            metric="api_calls",
            date_from=None,
            date_to=None,
        )

        assert len(result) == 2
        assert result[0].total == 100

    @pytest.mark.asyncio
    async def test_list_daily_aggregates_with_date_filters(self) -> None:
        """Date filters are applied."""
        mock_session = AsyncMock()

        aggs = [MagicMock(total=150)]

        mock_execute = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = aggs
        mock_execute.scalars.return_value = mock_scalars
        mock_session.execute = mock_execute

        service = AsyncBillingService(mock_session, tenant_id="tenant-123")

        result = await service.list_daily_aggregates(
            metric="api_calls",
            date_from=datetime(2024, 1, 1, tzinfo=UTC),
            date_to=datetime(2024, 1, 31, tzinfo=UTC),
        )

        assert len(result) == 1
        mock_session.execute.assert_called_once()


class TestGenerateMonthlyInvoice:
    """Tests for generate_monthly_invoice method."""

    @pytest.mark.asyncio
    async def test_generate_invoice_creates_invoice(self) -> None:
        """Creates invoice with total from aggregates."""
        mock_session = AsyncMock()

        # Mock aggregates
        aggs = [
            MagicMock(total=100),
            MagicMock(total=200),
            MagicMock(total=50),
        ]

        mock_execute = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = aggs
        mock_execute.scalars.return_value = mock_scalars
        mock_session.execute = mock_execute
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        service = AsyncBillingService(mock_session, tenant_id="tenant-123")

        result = await service.generate_monthly_invoice(
            period_start=datetime(2024, 1, 1, tzinfo=UTC),
            period_end=datetime(2024, 2, 1, tzinfo=UTC),
            currency="USD",
        )

        assert isinstance(result, str)
        assert len(result) == 36  # UUID format
        # Should add both invoice and line
        assert mock_session.add.call_count == 2
        mock_session.flush.assert_called_once()

        # Check invoice was created with correct values
        first_add = mock_session.add.call_args_list[0][0][0]
        assert isinstance(first_add, Invoice)
        assert first_add.total_amount == 350  # 100 + 200 + 50
        assert first_add.currency == "USD"
        assert first_add.status == "created"

    @pytest.mark.asyncio
    async def test_generate_invoice_creates_invoice_line(self) -> None:
        """Creates invoice line with total amount."""
        mock_session = AsyncMock()

        aggs = [MagicMock(total=500)]

        mock_execute = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = aggs
        mock_execute.scalars.return_value = mock_scalars
        mock_session.execute = mock_execute
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        service = AsyncBillingService(mock_session, tenant_id="tenant-123")

        await service.generate_monthly_invoice(
            period_start=datetime(2024, 1, 1, tzinfo=UTC),
            period_end=datetime(2024, 2, 1, tzinfo=UTC),
            currency="EUR",
        )

        # Second add call should be InvoiceLine
        second_add = mock_session.add.call_args_list[1][0][0]
        assert isinstance(second_add, InvoiceLine)
        assert second_add.amount == 500
        assert second_add.quantity == 1
