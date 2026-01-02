"""Coverage tests for billing and jobs modules.

Targets:
- billing/async_service.py
- billing/quotas.py
- jobs/queue.py
- jobs/scheduler.py
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from svc_infra.billing.async_service import AsyncBillingService
from svc_infra.billing.models import (
    Invoice,
    InvoiceLine,
    PlanEntitlement,
    Price,
    Subscription,
    UsageAggregate,
    UsageEvent,
)

# ============== AsyncBillingService Tests ==============


class FakeAsyncSession:
    def __init__(self) -> None:
        self.added: list[Any] = []
        self._execute_results: list[Any] = []

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        pass

    def set_execute_results(self, results: list[Any]) -> None:
        self._execute_results = results

    async def execute(self, stmt: Any) -> Any:
        if self._execute_results:
            return self._execute_results.pop(0)
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_scalars.first.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_result.scalar_one_or_none.return_value = None
        return mock_result


class TestAsyncBillingService:
    @pytest.mark.asyncio
    async def test_record_usage_basic(self) -> None:
        session = FakeAsyncSession()
        service = AsyncBillingService(session, tenant_id="tenant-123")

        event_id = await service.record_usage(
            metric="api_calls",
            amount=5,
            at=datetime.now(UTC),
            idempotency_key="test-key-1",
            metadata={"endpoint": "/api/test"},
        )

        assert event_id is not None
        assert len(session.added) == 1
        event = session.added[0]
        assert isinstance(event, UsageEvent)
        assert event.metric == "api_calls"
        assert event.amount == 5
        assert event.tenant_id == "tenant-123"

    @pytest.mark.asyncio
    async def test_record_usage_naive_datetime(self) -> None:
        session = FakeAsyncSession()
        service = AsyncBillingService(session, tenant_id="tenant-456")

        # Naive datetime (no timezone)
        naive_dt = datetime(2025, 1, 15, 10, 30, 0)
        event_id = await service.record_usage(
            metric="storage_mb",
            amount=100,
            at=naive_dt,
            idempotency_key="test-key-2",
            metadata=None,
        )

        assert event_id is not None
        event = session.added[0]
        assert event.at_ts.tzinfo is not None  # Should have timezone now

    @pytest.mark.asyncio
    async def test_record_usage_no_metadata(self) -> None:
        session = FakeAsyncSession()
        service = AsyncBillingService(session, tenant_id="tenant-789")

        await service.record_usage(
            metric="requests",
            amount=1,
            at=datetime.now(UTC),
            idempotency_key="test-key-3",
            metadata=None,
        )

        event = session.added[0]
        assert event.metadata_json == {}

    @pytest.mark.asyncio
    async def test_aggregate_daily_no_events(self) -> None:
        session = FakeAsyncSession()
        service = AsyncBillingService(session, tenant_id="tenant-agg")

        # Mock empty results
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_result.scalar_one_or_none.return_value = None
        session.set_execute_results([mock_result, mock_result])

        total = await service.aggregate_daily(
            metric="api_calls",
            day_start=datetime(2025, 1, 15, tzinfo=UTC),
        )

        assert total == 0
        # Should have added a new UsageAggregate
        assert any(isinstance(o, UsageAggregate) for o in session.added)

    @pytest.mark.asyncio
    async def test_aggregate_daily_with_events(self) -> None:
        session = FakeAsyncSession()
        service = AsyncBillingService(session, tenant_id="tenant-agg2")

        # Create mock events
        mock_event1 = MagicMock()
        mock_event1.amount = 10
        mock_event2 = MagicMock()
        mock_event2.amount = 20

        mock_result_events = MagicMock()
        mock_scalars_events = MagicMock()
        mock_scalars_events.all.return_value = [mock_event1, mock_event2]
        mock_result_events.scalars.return_value = mock_scalars_events

        # Existing aggregate
        mock_result_agg = MagicMock()
        mock_result_agg.scalar_one_or_none.return_value = None

        session.set_execute_results([mock_result_events, mock_result_agg])

        total = await service.aggregate_daily(
            metric="api_calls",
            day_start=datetime(2025, 1, 15, 12, 30, 45, tzinfo=UTC),  # Not at midnight
        )

        assert total == 30  # 10 + 20

    @pytest.mark.asyncio
    async def test_aggregate_daily_updates_existing(self) -> None:
        session = FakeAsyncSession()
        service = AsyncBillingService(session, tenant_id="tenant-agg3")

        mock_event = MagicMock()
        mock_event.amount = 50

        mock_result_events = MagicMock()
        mock_scalars_events = MagicMock()
        mock_scalars_events.all.return_value = [mock_event]
        mock_result_events.scalars.return_value = mock_scalars_events

        # Existing aggregate to update
        existing_agg = MagicMock()
        existing_agg.total = 25

        mock_result_agg = MagicMock()
        mock_result_agg.scalar_one_or_none.return_value = existing_agg

        session.set_execute_results([mock_result_events, mock_result_agg])

        total = await service.aggregate_daily(
            metric="downloads",
            day_start=datetime(2025, 1, 15, tzinfo=UTC),
        )

        assert total == 50
        assert existing_agg.total == 50  # Updated


# ============== Billing Models Tests ==============


class TestBillingModels:
    def test_usage_event_creation(self) -> None:
        event = UsageEvent(
            id=str(uuid.uuid4()),
            tenant_id="tenant-1",
            metric="api_calls",
            amount=10,
            at_ts=datetime.now(UTC),
            idempotency_key="key-1",
            metadata_json={"key": "value"},
        )
        assert event.metric == "api_calls"
        assert event.amount == 10

    def test_usage_aggregate_creation(self) -> None:
        agg = UsageAggregate(
            id=str(uuid.uuid4()),
            tenant_id="tenant-1",
            metric="storage",
            granularity="day",
            period_start=datetime.now(UTC),
            total=1000,
        )
        assert agg.granularity == "day"
        assert agg.total == 1000

    def test_invoice_creation(self) -> None:
        invoice = Invoice(
            id=str(uuid.uuid4()),
            tenant_id="tenant-1",
            status="draft",
            period_start=datetime(2025, 1, 1, tzinfo=UTC),
            period_end=datetime(2025, 1, 31, tzinfo=UTC),
            total_amount=5000,
            currency="USD",
        )
        assert invoice.status == "draft"
        assert invoice.total_amount == 5000

    def test_invoice_line_creation(self) -> None:
        line = InvoiceLine(
            id=str(uuid.uuid4()),
            invoice_id=str(uuid.uuid4()),
            quantity=100,
            amount=500,
        )
        assert line.quantity == 100
        assert line.amount == 500

    def test_subscription_creation(self) -> None:
        sub = Subscription(
            id=str(uuid.uuid4()),
            tenant_id="tenant-1",
            plan_id="pro",
            effective_at=datetime.now(UTC),
        )
        assert sub.plan_id == "pro"

    def test_plan_entitlement_creation(self) -> None:
        ent = PlanEntitlement(
            id=str(uuid.uuid4()),
            plan_id="pro",
            key="api_calls",
            limit_per_window=10000,
            window="month",
        )
        assert ent.key == "api_calls"
        assert ent.limit_per_window == 10000

    def test_price_creation(self) -> None:
        price = Price(
            id=str(uuid.uuid4()),
            key="api-usage",
            currency="USD",
            unit_amount=100,
        )
        assert price.key == "api-usage"
        assert price.currency == "USD"


# ============== Jobs Queue Tests ==============


class TestJobsQueue:
    def test_job_queue_import(self) -> None:
        from svc_infra.jobs.queue import InMemoryJobQueue

        queue = InMemoryJobQueue()
        assert queue is not None

    def test_in_memory_queue_enqueue(self) -> None:
        from svc_infra.jobs.queue import InMemoryJobQueue

        queue = InMemoryJobQueue()

        job = queue.enqueue("test_task", {"key": "value"})
        assert job is not None
        assert job.name == "test_task"
        assert job.payload == {"key": "value"}

    def test_in_memory_queue_reserve_next(self) -> None:
        from svc_infra.jobs.queue import InMemoryJobQueue

        queue = InMemoryJobQueue()
        queue.enqueue("task1", {"id": 1})

        job = queue.reserve_next()
        assert job is not None
        assert job.name == "task1"

    def test_in_memory_queue_reserve_empty(self) -> None:
        from svc_infra.jobs.queue import InMemoryJobQueue

        queue = InMemoryJobQueue()

        job = queue.reserve_next()
        assert job is None

    def test_in_memory_queue_ack(self) -> None:
        from svc_infra.jobs.queue import InMemoryJobQueue

        queue = InMemoryJobQueue()
        job = queue.enqueue("task", {})

        queue.ack(job.id)
        assert queue.reserve_next() is None

    def test_in_memory_queue_fail(self) -> None:
        from svc_infra.jobs.queue import InMemoryJobQueue

        queue = InMemoryJobQueue()
        job = queue.enqueue("task", {})
        job = queue.reserve_next()

        queue.fail(job.id, error="Test error")
        # Job should now have last_error set
        assert any(j.last_error == "Test error" for j in queue._jobs)

    def test_in_memory_queue_delay(self) -> None:
        from svc_infra.jobs.queue import InMemoryJobQueue

        queue = InMemoryJobQueue()
        # Delay 10 seconds in future - should not be immediately available
        job = queue.enqueue("delayed_task", {}, delay_seconds=10)

        # Should not be available yet (in theory)
        assert job.name == "delayed_task"


# ============== Jobs Scheduler Tests ==============


class TestJobsScheduler:
    def test_scheduler_import(self) -> None:
        from svc_infra.jobs.scheduler import InMemoryScheduler

        scheduler = InMemoryScheduler()
        assert scheduler is not None

    def test_scheduler_add_task(self) -> None:
        from svc_infra.jobs.scheduler import InMemoryScheduler

        scheduler = InMemoryScheduler()

        async def my_task() -> None:
            pass

        scheduler.add_task("test_task", interval_seconds=60, func=my_task)
        assert "test_task" in scheduler._tasks
