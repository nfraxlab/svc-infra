"""Tests for CommerceService facade."""

from __future__ import annotations

import pytest

from svc_infra.commerce.provider.registry import CommerceRegistry
from svc_infra.commerce.schemas import (
    CustomerUpsertIn,
    FulfillmentCreateIn,
    InventoryAdjustIn,
    ProductUpsertIn,
    WebhookEventIn,
)
from svc_infra.commerce.service import CommerceService


class TestCommerceServiceInit:
    def test_with_explicit_adapter(self, fake_adapter) -> None:
        svc = CommerceService(adapter=fake_adapter)
        assert svc.provider_name == "fake"

    def test_with_registry(self, fake_adapter, monkeypatch) -> None:
        import svc_infra.commerce.provider.registry as reg_mod

        reg = CommerceRegistry()
        reg.register(fake_adapter)
        reg_mod._REGISTRY = reg

        svc = CommerceService(provider_name="fake")
        assert svc.provider_name == "fake"

    def test_from_settings(self, fake_adapter, monkeypatch) -> None:
        import svc_infra.commerce.provider.registry as reg_mod

        reg = CommerceRegistry()
        reg.register(fake_adapter)
        reg_mod._REGISTRY = reg
        monkeypatch.setenv("COMMERCE_PROVIDER", "fake")

        import svc_infra.commerce.settings as settings_mod

        settings_mod._SETTINGS = None

        svc = CommerceService.from_settings(provider="fake")
        assert svc.provider_name == "fake"

    def test_missing_provider_raises(self) -> None:
        with pytest.raises(RuntimeError, match="Cannot create CommerceService"):
            CommerceService(provider_name="nonexistent")


class TestProductOps:
    @pytest.fixture
    def svc(self, fake_adapter) -> CommerceService:
        return CommerceService(adapter=fake_adapter)

    @pytest.mark.asyncio
    async def test_list(self, svc, fake_adapter) -> None:
        products, cursor = await svc.products.list(limit=10)
        fake_adapter.list_products.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get(self, svc, fake_adapter) -> None:
        product = await svc.products.get("prod_1")
        fake_adapter.get_product.assert_awaited_once_with("prod_1")
        assert product.provider_id == "prod_1"
        assert product.title == "Test Product"

    @pytest.mark.asyncio
    async def test_upsert(self, svc, fake_adapter) -> None:
        data = ProductUpsertIn(title="New Widget")
        product = await svc.products.upsert(data)
        fake_adapter.upsert_product.assert_awaited_once_with(data)
        assert product.provider_id == "prod_new"

    @pytest.mark.asyncio
    async def test_delete(self, svc, fake_adapter) -> None:
        await svc.products.delete("prod_1")
        fake_adapter.delete_product.assert_awaited_once_with("prod_1")


class TestInventoryOps:
    @pytest.fixture
    def svc(self, fake_adapter) -> CommerceService:
        return CommerceService(adapter=fake_adapter)

    @pytest.mark.asyncio
    async def test_get(self, svc, fake_adapter) -> None:
        level = await svc.inventory.get("var_1")
        fake_adapter.get_inventory.assert_awaited_once_with("var_1")
        assert level.available == 42

    @pytest.mark.asyncio
    async def test_adjust(self, svc, fake_adapter) -> None:
        data = InventoryAdjustIn(provider_variant_id="var_1", adjustment=-2)
        level = await svc.inventory.adjust(data)
        fake_adapter.adjust_inventory.assert_awaited_once_with(data)
        assert level.available == 40


class TestOrderOps:
    @pytest.fixture
    def svc(self, fake_adapter) -> CommerceService:
        return CommerceService(adapter=fake_adapter)

    @pytest.mark.asyncio
    async def test_list(self, svc, fake_adapter) -> None:
        orders, cursor = await svc.orders.list(status="open", limit=25)
        fake_adapter.list_orders.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get(self, svc, fake_adapter) -> None:
        order = await svc.orders.get("ord_1")
        fake_adapter.get_order.assert_awaited_once_with("ord_1")
        assert order.order_number == "1001"
        assert order.total.amount == 5999

    @pytest.mark.asyncio
    async def test_cancel(self, svc, fake_adapter) -> None:
        order = await svc.orders.cancel("ord_1", reason="customer request")
        fake_adapter.cancel_order.assert_awaited_once_with("ord_1", reason="customer request")
        assert order.status == "cancelled"

    @pytest.mark.asyncio
    async def test_close(self, svc, fake_adapter) -> None:
        order = await svc.orders.close("ord_1")
        fake_adapter.close_order.assert_awaited_once_with("ord_1")
        assert order.status == "closed"


class TestFulfillmentOps:
    @pytest.fixture
    def svc(self, fake_adapter) -> CommerceService:
        return CommerceService(adapter=fake_adapter)

    @pytest.mark.asyncio
    async def test_create(self, svc, fake_adapter) -> None:
        data = FulfillmentCreateIn(
            order_provider_id="ord_1",
            tracking_number="1Z999",
        )
        result = await svc.fulfillment.create(data)
        fake_adapter.create_fulfillment.assert_awaited_once_with(data)
        assert result.provider_id == "ful_1"
        assert result.tracking_number == "1Z999AA10123456784"


class TestCustomerOps:
    @pytest.fixture
    def svc(self, fake_adapter) -> CommerceService:
        return CommerceService(adapter=fake_adapter)

    @pytest.mark.asyncio
    async def test_get(self, svc, fake_adapter) -> None:
        customer = await svc.customers.get("cust_1")
        fake_adapter.get_customer.assert_awaited_once_with("cust_1")
        assert customer.email == "jane@example.com"

    @pytest.mark.asyncio
    async def test_upsert(self, svc, fake_adapter) -> None:
        data = CustomerUpsertIn(email="new@example.com", first_name="New")
        customer = await svc.customers.upsert(data)
        fake_adapter.upsert_customer.assert_awaited_once_with(data)
        assert customer.provider_id == "cust_new"


class TestWebhookAndRaw:
    @pytest.fixture
    def svc(self, fake_adapter) -> CommerceService:
        return CommerceService(adapter=fake_adapter)

    @pytest.mark.asyncio
    async def test_verify_webhook(self, svc, fake_adapter) -> None:
        event = WebhookEventIn(
            provider="fake",
            topic="orders/create",
            payload=b'{"id": "ord_1"}',
        )
        result = await svc.verify_webhook(event)
        fake_adapter.verify_and_parse_webhook.assert_awaited_once_with(event)
        assert result.verified is True

    @pytest.mark.asyncio
    async def test_raw_request(self, svc, fake_adapter) -> None:
        result = await svc.raw_request("GET", "/custom/endpoint.json")
        fake_adapter.raw_request.assert_awaited_once_with(
            "GET", "/custom/endpoint.json", json=None, params=None
        )
        assert result == {"ok": True}
