"""Tests for the Shopify adapter (unit tests with mocked HTTP)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from pydantic import SecretStr

from svc_infra.commerce.provider.shopify import ShopifyAdapter, _parse_money
from svc_infra.commerce.schemas import (
    CustomerUpsertIn,
    FulfillmentCreateIn,
    InventoryAdjustIn,
    Money,
    OrderListFilter,
    ProductListFilter,
    ProductStatus,
    ProductUpsertIn,
    VariantUpsertIn,
    WebhookEventIn,
)
from svc_infra.commerce.settings import ShopifyConfig


@pytest.fixture
def shopify_config() -> ShopifyConfig:
    return ShopifyConfig(
        access_token=SecretStr("shpat_test_token"),
        shop_domain="test-store.myshopify.com",
        api_version="2024-10",
        webhook_secret=SecretStr("whsec_test"),
        max_retries=1,
        timeout=5.0,
    )


@pytest.fixture
def adapter(shopify_config) -> ShopifyAdapter:
    return ShopifyAdapter(config=shopify_config)


class TestParseHelpers:
    def test_parse_money_normal(self) -> None:
        m = _parse_money("29.99", "USD")
        assert m is not None
        assert m.amount == 2999
        assert m.currency == "USD"

    def test_parse_money_none(self) -> None:
        assert _parse_money(None) is None

    def test_parse_money_zero(self) -> None:
        m = _parse_money("0.00")
        assert m is not None
        assert m.amount == 0

    def test_parse_money_invalid(self) -> None:
        assert _parse_money("not-a-number") is None


class TestShopifyAdapterInit:
    def test_creates_with_config(self, shopify_config) -> None:
        adapter = ShopifyAdapter(config=shopify_config)
        assert adapter.name == "shopify"
        assert adapter._base_url == "https://test-store.myshopify.com/admin/api/2024-10"

    def test_raises_without_config(self, monkeypatch) -> None:
        import svc_infra.commerce.settings as mod

        mod._SETTINGS = None
        monkeypatch.delenv("SHOPIFY_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("SHOPIFY_SHOP_DOMAIN", raising=False)
        monkeypatch.delenv("SHOPIFY_ADMIN_TOKEN", raising=False)
        monkeypatch.delenv("SHOPIFY_SHOP", raising=False)

        with pytest.raises(RuntimeError, match="Shopify settings not configured"):
            ShopifyAdapter(config=None)


class TestShopifyProducts:
    @pytest.mark.asyncio
    async def test_list_products(self, adapter) -> None:
        mock_response = {
            "products": [
                {
                    "id": 123,
                    "title": "Test Widget",
                    "handle": "test-widget",
                    "status": "active",
                    "tags": "sale, new",
                    "variants": [
                        {
                            "id": 456,
                            "title": "Default",
                            "sku": "WDG-001",
                            "price": "29.99",
                            "inventory_quantity": 10,
                        }
                    ],
                    "images": [{"src": "https://cdn.shopify.com/img.jpg"}],
                    "created_at": "2025-01-01T00:00:00Z",
                }
            ]
        }
        adapter._request = AsyncMock(return_value=mock_response)

        products, cursor = await adapter.list_products(ProductListFilter(limit=10))

        assert len(products) == 1
        p = products[0]
        assert p.provider_id == "123"
        assert p.title == "Test Widget"
        assert p.handle == "test-widget"
        assert len(p.variants) == 1
        assert p.variants[0].sku == "WDG-001"
        assert p.variants[0].price.amount == 2999
        assert p.tags == ["sale", "new"]
        assert len(p.images) == 1

    @pytest.mark.asyncio
    async def test_get_product(self, adapter) -> None:
        mock_response = {
            "product": {
                "id": 789,
                "title": "Single Product",
                "handle": "single",
                "status": "draft",
                "tags": "",
                "variants": [],
                "images": [],
            }
        }
        adapter._request = AsyncMock(return_value=mock_response)

        product = await adapter.get_product("789")
        assert product.provider_id == "789"
        assert product.status == ProductStatus.DRAFT
        assert product.tags == []

    @pytest.mark.asyncio
    async def test_upsert_product(self, adapter) -> None:
        mock_response = {
            "product": {
                "id": 999,
                "title": "New Product",
                "handle": "new-product",
                "status": "active",
                "tags": "tag1",
                "variants": [],
                "images": [],
            }
        }
        adapter._request = AsyncMock(return_value=mock_response)

        data = ProductUpsertIn(
            title="New Product",
            tags=["tag1"],
            variants=[VariantUpsertIn(title="Default", price=Money(amount=1999))],
        )
        product = await adapter.upsert_product(data)
        assert product.provider_id == "999"
        adapter._request.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_product(self, adapter) -> None:
        adapter._request = AsyncMock(return_value={})
        await adapter.delete_product("123")
        adapter._request.assert_awaited_once_with("DELETE", "/products/123.json")


class TestShopifyOrders:
    @pytest.mark.asyncio
    async def test_list_orders(self, adapter) -> None:
        mock_response = {
            "orders": [
                {
                    "id": 1001,
                    "order_number": "1001",
                    "email": "customer@test.com",
                    "status": "open",
                    "financial_status": "paid",
                    "fulfillment_status": None,
                    "currency": "USD",
                    "subtotal_price": "50.00",
                    "total_tax": "4.00",
                    "total_price": "54.00",
                    "line_items": [
                        {
                            "id": 101,
                            "variant_id": 201,
                            "product_id": 301,
                            "title": "Widget",
                            "quantity": 2,
                            "price": "25.00",
                            "sku": "WDG",
                            "tax_lines": [{"title": "Tax", "rate": "0.08", "price": "2.00"}],
                        }
                    ],
                    "tags": "vip",
                    "created_at": "2025-06-15T10:00:00Z",
                }
            ]
        }
        adapter._request = AsyncMock(return_value=mock_response)

        orders, cursor = await adapter.list_orders(OrderListFilter(status="open"))
        assert len(orders) == 1
        o = orders[0]
        assert o.provider_id == "1001"
        assert o.email == "customer@test.com"
        assert o.total.amount == 5400
        assert len(o.line_items) == 1
        assert o.line_items[0].quantity == 2
        assert len(o.line_items[0].tax_lines) == 1

    @pytest.mark.asyncio
    async def test_get_order(self, adapter) -> None:
        mock_response = {
            "order": {
                "id": 1001,
                "order_number": "1001",
                "status": "open",
                "financial_status": "pending",
                "currency": "USD",
                "line_items": [],
                "tags": "",
            }
        }
        adapter._request = AsyncMock(return_value=mock_response)
        order = await adapter.get_order("1001")
        assert order.provider_id == "1001"

    @pytest.mark.asyncio
    async def test_cancel_order(self, adapter) -> None:
        mock_response = {
            "order": {
                "id": 1001,
                "order_number": "1001",
                "status": "cancelled",
                "financial_status": "refunded",
                "currency": "USD",
                "line_items": [],
                "tags": "",
                "cancelled_at": "2025-06-16T00:00:00Z",
            }
        }
        adapter._request = AsyncMock(return_value=mock_response)
        order = await adapter.cancel_order("1001", reason="customer request")
        assert order.cancelled_at is not None


class TestShopifyInventory:
    @pytest.mark.asyncio
    async def test_get_inventory(self, adapter) -> None:
        mock_response = {
            "inventory_levels": [
                {
                    "inventory_item_id": 555,
                    "location_id": 1,
                    "available": 42,
                    "updated_at": "2025-01-01T00:00:00Z",
                }
            ]
        }
        adapter._request = AsyncMock(return_value=mock_response)
        level = await adapter.get_inventory("555")
        assert level.available == 42

    @pytest.mark.asyncio
    async def test_get_inventory_empty(self, adapter) -> None:
        adapter._request = AsyncMock(return_value={"inventory_levels": []})
        with pytest.raises(RuntimeError, match="No inventory level found"):
            await adapter.get_inventory("999")

    @pytest.mark.asyncio
    async def test_adjust_inventory(self, adapter) -> None:
        mock_response = {
            "inventory_level": {
                "inventory_item_id": 555,
                "location_id": 1,
                "available": 40,
            }
        }
        adapter._request = AsyncMock(return_value=mock_response)
        data = InventoryAdjustIn(provider_variant_id="555", adjustment=-2)
        level = await adapter.adjust_inventory(data)
        assert level.available == 40


class TestShopifyCustomers:
    @pytest.mark.asyncio
    async def test_get_customer(self, adapter) -> None:
        mock_response = {
            "customer": {
                "id": 777,
                "email": "jane@test.com",
                "first_name": "Jane",
                "last_name": "Doe",
                "orders_count": 3,
                "total_spent": "150.00",
                "tags": "vip, loyal",
                "default_address": {
                    "address1": "123 Main St",
                    "city": "NYC",
                    "country_code": "US",
                },
                "created_at": "2025-01-01T00:00:00Z",
            }
        }
        adapter._request = AsyncMock(return_value=mock_response)
        customer = await adapter.get_customer("777")
        assert customer is not None
        assert customer.email == "jane@test.com"
        assert customer.tags == ["vip", "loyal"]

    @pytest.mark.asyncio
    async def test_get_customer_not_found(self, adapter) -> None:
        adapter._request = AsyncMock(side_effect=RuntimeError("404"))
        customer = await adapter.get_customer("999")
        assert customer is None

    @pytest.mark.asyncio
    async def test_upsert_customer_new(self, adapter) -> None:
        adapter._request = AsyncMock(
            side_effect=[
                {"customers": []},  # search returns empty
                {
                    "customer": {
                        "id": 888,
                        "email": "new@test.com",
                        "first_name": "New",
                        "tags": "",
                    }
                },  # create
            ]
        )
        data = CustomerUpsertIn(email="new@test.com", first_name="New")
        customer = await adapter.upsert_customer(data)
        assert customer.provider_id == "888"

    @pytest.mark.asyncio
    async def test_upsert_customer_existing(self, adapter) -> None:
        adapter._request = AsyncMock(
            side_effect=[
                {"customers": [{"id": 777}]},  # search finds existing
                {
                    "customer": {
                        "id": 777,
                        "email": "existing@test.com",
                        "first_name": "Updated",
                        "tags": "",
                    }
                },  # update
            ]
        )
        data = CustomerUpsertIn(email="existing@test.com", first_name="Updated")
        customer = await adapter.upsert_customer(data)
        assert customer.provider_id == "777"


class TestShopifyFulfillment:
    @pytest.mark.asyncio
    async def test_create_fulfillment(self, adapter) -> None:
        mock_response = {
            "fulfillment": {
                "id": 333,
                "status": "success",
                "tracking_number": "1Z999",
                "created_at": "2025-06-16T00:00:00Z",
            }
        }
        adapter._request = AsyncMock(return_value=mock_response)
        data = FulfillmentCreateIn(
            order_provider_id="1001",
            tracking_number="1Z999",
        )
        result = await adapter.create_fulfillment(data)
        assert result.provider_id == "333"
        assert result.tracking_number == "1Z999"


class TestShopifyWebhooks:
    @pytest.mark.asyncio
    async def test_verify_valid_signature(self, adapter) -> None:
        import base64
        import hashlib
        import hmac as hmac_mod

        payload = b'{"id": 123, "email": "test@test.com"}'
        secret = "whsec_test"
        sig = base64.b64encode(
            hmac_mod.new(secret.encode(), payload, hashlib.sha256).digest()
        ).decode()

        event = WebhookEventIn(
            provider="shopify",
            topic="orders/create",
            payload=payload,
            signature=sig,
        )
        result = await adapter.verify_and_parse_webhook(event)
        assert result.verified is True
        assert result.topic == "orders/create"
        assert result.resource_id == "123"

    @pytest.mark.asyncio
    async def test_verify_invalid_signature(self, adapter) -> None:
        event = WebhookEventIn(
            provider="shopify",
            topic="orders/create",
            payload=b'{"id": 123}',
            signature="invalid_sig",
        )
        with pytest.raises(RuntimeError, match="signature verification failed"):
            await adapter.verify_and_parse_webhook(event)

    @pytest.mark.asyncio
    async def test_verify_no_secret_configured(self, shopify_config) -> None:
        shopify_config.webhook_secret = None
        adapter = ShopifyAdapter(config=shopify_config)

        event = WebhookEventIn(
            provider="shopify",
            topic="orders/create",
            payload=b'{"id": 456}',
        )
        result = await adapter.verify_and_parse_webhook(event)
        # No secret = skip verification
        assert result.verified is True

    @pytest.mark.asyncio
    async def test_verify_bad_json_payload(self, adapter) -> None:
        import base64
        import hashlib
        import hmac as hmac_mod

        payload = b"not valid json"
        secret = "whsec_test"
        sig = base64.b64encode(
            hmac_mod.new(secret.encode(), payload, hashlib.sha256).digest()
        ).decode()

        event = WebhookEventIn(
            provider="shopify",
            topic="orders/create",
            payload=payload,
            signature=sig,
        )
        with pytest.raises(RuntimeError, match="Failed to parse"):
            await adapter.verify_and_parse_webhook(event)


class TestShopifyRawRequest:
    @pytest.mark.asyncio
    async def test_raw_request(self, adapter) -> None:
        adapter._request = AsyncMock(return_value={"shop": {"name": "Test"}})
        result = await adapter.raw_request("GET", "/shop.json")
        assert result["shop"]["name"] == "Test"
