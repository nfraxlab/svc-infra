"""Tests for commerce webhook dispatcher."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from svc_infra.commerce.schemas import WebhookEventIn
from svc_infra.commerce.webhooks import WebhookDispatcher


@pytest.fixture
def dispatcher() -> WebhookDispatcher:
    return WebhookDispatcher()


class TestWebhookDispatcher:
    @pytest.mark.asyncio
    async def test_handle_routes_to_topic_handler(self, dispatcher, fake_adapter) -> None:
        handler = AsyncMock()
        dispatcher.on("orders/create", handler)

        event = WebhookEventIn(
            provider="fake",
            topic="orders/create",
            payload=b'{"id": "ord_1"}',
        )
        result = await dispatcher.handle(fake_adapter, event)

        handler.assert_awaited_once()
        assert result.verified is True
        assert result.topic == "orders/create"

    @pytest.mark.asyncio
    async def test_handle_invokes_catch_all(self, dispatcher, fake_adapter) -> None:
        catch_all = AsyncMock()
        dispatcher.on_any(catch_all)

        event = WebhookEventIn(
            provider="fake",
            topic="products/update",
            payload=b'{"id": "prod_1"}',
        )
        await dispatcher.handle(fake_adapter, event)

        catch_all.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_no_matching_topic(self, dispatcher, fake_adapter) -> None:
        handler = AsyncMock()
        dispatcher.on("products/delete", handler)

        # The fake adapter's verify_and_parse_webhook returns topic="orders/create"
        # so "products/delete" handler should NOT be invoked
        event = WebhookEventIn(
            provider="fake",
            topic="orders/create",
            payload=b'{"id": "ord_1"}',
        )
        result = await dispatcher.handle(fake_adapter, event)

        handler.assert_not_awaited()
        assert result is not None

    @pytest.mark.asyncio
    async def test_handler_exception_does_not_propagate(self, dispatcher, fake_adapter) -> None:
        handler = AsyncMock(side_effect=ValueError("boom"))
        dispatcher.on("orders/create", handler)

        event = WebhookEventIn(
            provider="fake",
            topic="orders/create",
            payload=b'{"id": "ord_1"}',
        )
        # Should not raise
        result = await dispatcher.handle(fake_adapter, event)
        assert result is not None

    @pytest.mark.asyncio
    async def test_catch_all_exception_does_not_propagate(self, dispatcher, fake_adapter) -> None:
        catch_all = AsyncMock(side_effect=RuntimeError("fail"))
        dispatcher.on_any(catch_all)

        event = WebhookEventIn(
            provider="fake",
            topic="orders/create",
            payload=b'{"id": "ord_1"}',
        )
        result = await dispatcher.handle(fake_adapter, event)
        assert result is not None

    @pytest.mark.asyncio
    async def test_multiple_handlers_for_same_topic(self, dispatcher, fake_adapter) -> None:
        h1 = AsyncMock()
        h2 = AsyncMock()
        dispatcher.on("orders/create", h1)
        dispatcher.on("orders/create", h2)

        event = WebhookEventIn(
            provider="fake",
            topic="orders/create",
            payload=b'{"id": "ord_1"}',
        )
        await dispatcher.handle(fake_adapter, event)

        h1.assert_awaited_once()
        h2.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_replay(self, dispatcher, fake_adapter) -> None:
        handler = AsyncMock()
        dispatcher.on("orders/create", handler)

        events = [
            WebhookEventIn(
                provider="fake",
                topic="orders/create",
                payload=b'{"id": "ord_1"}',
            ),
            WebhookEventIn(
                provider="fake",
                topic="orders/create",
                payload=b'{"id": "ord_2"}',
            ),
        ]
        results = await dispatcher.replay(fake_adapter, events)

        assert len(results) == 2
        assert handler.await_count == 2

    def test_registered_topics(self, dispatcher) -> None:
        assert dispatcher.registered_topics == []
        dispatcher.on("orders/create", AsyncMock())
        dispatcher.on("products/update", AsyncMock())
        assert dispatcher.registered_topics == ["orders/create", "products/update"]
