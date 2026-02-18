"""Tests for commerce schemas (Pydantic models)."""

from __future__ import annotations

import pytest

from svc_infra.commerce.schemas import (
    Address,
    Customer,
    CustomerUpsertIn,
    FinancialStatus,
    FulfillmentCreateIn,
    FulfillmentOut,
    FulfillmentStatus,
    InventoryAdjustIn,
    InventoryLevel,
    LineItem,
    Money,
    Order,
    OrderListFilter,
    OrderStatus,
    Product,
    ProductListFilter,
    ProductStatus,
    ProductUpsertIn,
    TaxLine,
    Variant,
    VariantUpsertIn,
    WebhookEventIn,
    WebhookEventOut,
)


class TestMoney:
    def test_defaults(self) -> None:
        m = Money(amount=100)
        assert m.amount == 100
        assert m.currency == "USD"

    def test_custom_currency(self) -> None:
        m = Money(amount=500, currency="CAD")
        assert m.currency == "CAD"

    def test_rejects_negative(self) -> None:
        with pytest.raises(ValueError):
            Money(amount=-1)

    def test_rejects_invalid_currency(self) -> None:
        with pytest.raises(ValueError):
            Money(amount=100, currency="usd")  # must be uppercase


class TestAddress:
    def test_all_optional(self) -> None:
        a = Address()
        assert a.city is None
        assert a.country_code is None

    def test_full_address(self) -> None:
        a = Address(
            first_name="Jane",
            last_name="Doe",
            address1="123 Main St",
            city="New York",
            province_code="NY",
            country_code="US",
            zip="10001",
        )
        assert a.city == "New York"
        assert a.zip == "10001"


class TestProduct:
    def test_minimal(self) -> None:
        p = Product(provider_id="123", title="Widget")
        assert p.provider_id == "123"
        assert p.status == ProductStatus.ACTIVE
        assert p.variants == []
        assert p.images == []

    def test_with_variants(self) -> None:
        v = Variant(
            provider_id="v1",
            title="Large",
            sku="WDG-LG",
            price=Money(amount=1999),
        )
        p = Product(provider_id="123", title="Widget", variants=[v])
        assert len(p.variants) == 1
        assert p.variants[0].sku == "WDG-LG"


class TestProductUpsertIn:
    def test_minimal(self) -> None:
        inp = ProductUpsertIn(title="New Product")
        assert inp.title == "New Product"
        assert inp.status == ProductStatus.ACTIVE

    def test_with_variants(self) -> None:
        v = VariantUpsertIn(title="Small", sku="SM", price=Money(amount=999))
        inp = ProductUpsertIn(title="T-Shirt", variants=[v])
        assert len(inp.variants) == 1


class TestProductListFilter:
    def test_defaults(self) -> None:
        f = ProductListFilter()
        assert f.limit == 50
        assert f.cursor is None

    def test_limit_bounds(self) -> None:
        with pytest.raises(ValueError):
            ProductListFilter(limit=0)
        with pytest.raises(ValueError):
            ProductListFilter(limit=251)


class TestOrder:
    def test_minimal(self) -> None:
        o = Order(provider_id="ord_1")
        assert o.status == OrderStatus.OPEN
        assert o.financial_status == FinancialStatus.PENDING
        assert o.line_items == []

    def test_with_line_items(self) -> None:
        li = LineItem(
            provider_id="li_1",
            title="Widget",
            quantity=2,
            price=Money(amount=1999),
            tax_lines=[
                TaxLine(title="Tax", rate=0.08, price=Money(amount=160)),
            ],
        )
        o = Order(provider_id="ord_1", line_items=[li])
        assert len(o.line_items) == 1
        assert len(o.line_items[0].tax_lines) == 1


class TestOrderListFilter:
    def test_defaults(self) -> None:
        f = OrderListFilter()
        assert f.limit == 50
        assert f.status is None


class TestInventory:
    def test_level(self) -> None:
        lv = InventoryLevel(provider_variant_id="v1", available=10)
        assert lv.available == 10

    def test_adjust_in(self) -> None:
        adj = InventoryAdjustIn(provider_variant_id="v1", adjustment=-3)
        assert adj.adjustment == -3


class TestFulfillment:
    def test_create_in(self) -> None:
        f = FulfillmentCreateIn(
            order_provider_id="ord_1",
            tracking_number="1Z999",
            notify_customer=False,
        )
        assert f.order_provider_id == "ord_1"
        assert f.notify_customer is False

    def test_out(self) -> None:
        f = FulfillmentOut(
            provider_id="ful_1",
            order_provider_id="ord_1",
            status="success",
        )
        assert f.status == "success"


class TestCustomer:
    def test_minimal(self) -> None:
        c = Customer(provider_id="cust_1")
        assert c.orders_count == 0
        assert c.tags == []

    def test_upsert_in(self) -> None:
        u = CustomerUpsertIn(email="jane@example.com", first_name="Jane")
        assert u.email == "jane@example.com"


class TestWebhookSchemas:
    def test_event_in(self) -> None:
        e = WebhookEventIn(
            provider="shopify",
            topic="orders/create",
            payload=b'{"id": 123}',
            signature="abc123",
        )
        assert e.provider == "shopify"

    def test_event_out(self) -> None:
        e = WebhookEventOut(
            provider="shopify",
            topic="orders/create",
            resource_id="123",
            data={"id": 123},
            verified=True,
        )
        assert e.verified is True


class TestEnums:
    def test_product_status_values(self) -> None:
        assert ProductStatus.ACTIVE.value == "active"
        assert ProductStatus.ARCHIVED.value == "archived"
        assert ProductStatus.DRAFT.value == "draft"

    def test_order_status_values(self) -> None:
        assert OrderStatus.OPEN.value == "open"
        assert OrderStatus.ANY.value == "any"

    def test_financial_status_values(self) -> None:
        assert FinancialStatus.PAID.value == "paid"
        assert FinancialStatus.REFUNDED.value == "refunded"

    def test_fulfillment_status_values(self) -> None:
        assert FulfillmentStatus.FULFILLED.value == "fulfilled"
        assert FulfillmentStatus.PARTIAL.value == "partial"
