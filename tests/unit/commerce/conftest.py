"""Shared fixtures for commerce module tests."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from svc_infra.commerce.provider.registry import CommerceRegistry
from svc_infra.commerce.schemas import (
    Address,
    Customer,
    FulfillmentOut,
    InventoryLevel,
    LineItem,
    Money,
    Order,
    Product,
    Variant,
    WebhookEventOut,
)

# ---------------------------------------------------------------------------
# Fake adapter
# ---------------------------------------------------------------------------


class FakeCommerceAdapter:
    """In-memory commerce adapter for unit tests."""

    name: str = "fake"

    def __init__(self) -> None:
        self.list_products = AsyncMock(return_value=([], None))
        self.get_product = AsyncMock(
            return_value=Product(
                provider_id="prod_1",
                title="Test Product",
                handle="test-product",
                status="active",
                variants=[
                    Variant(
                        provider_id="var_1",
                        title="Default",
                        sku="TST-001",
                        price=Money(amount=2999, currency="USD"),
                    )
                ],
                created_at=datetime(2025, 1, 1, tzinfo=UTC),
            )
        )
        self.upsert_product = AsyncMock(
            return_value=Product(
                provider_id="prod_new",
                title="Created Product",
                handle="created-product",
                status="active",
            )
        )
        self.delete_product = AsyncMock(return_value=None)

        self.get_inventory = AsyncMock(
            return_value=InventoryLevel(
                provider_variant_id="var_1",
                location_id="loc_1",
                available=42,
            )
        )
        self.adjust_inventory = AsyncMock(
            return_value=InventoryLevel(
                provider_variant_id="var_1",
                location_id="loc_1",
                available=40,
            )
        )

        self.list_orders = AsyncMock(return_value=([], None))
        self.get_order = AsyncMock(
            return_value=Order(
                provider_id="ord_1",
                order_number="1001",
                email="test@example.com",
                status="open",
                financial_status="paid",
                total=Money(amount=5999, currency="USD"),
                line_items=[
                    LineItem(
                        provider_id="li_1",
                        title="Test Product",
                        quantity=2,
                        price=Money(amount=2999, currency="USD"),
                    )
                ],
                created_at=datetime(2025, 6, 15, tzinfo=UTC),
            )
        )
        self.cancel_order = AsyncMock(
            return_value=Order(
                provider_id="ord_1",
                order_number="1001",
                status="cancelled",
                financial_status="refunded",
            )
        )
        self.close_order = AsyncMock(
            return_value=Order(
                provider_id="ord_1",
                order_number="1001",
                status="closed",
                financial_status="paid",
            )
        )

        self.create_fulfillment = AsyncMock(
            return_value=FulfillmentOut(
                provider_id="ful_1",
                order_provider_id="ord_1",
                status="success",
                tracking_number="1Z999AA10123456784",
                created_at=datetime(2025, 6, 16, tzinfo=UTC),
            )
        )

        self.get_customer = AsyncMock(
            return_value=Customer(
                provider_id="cust_1",
                email="jane@example.com",
                first_name="Jane",
                last_name="Doe",
                orders_count=5,
                total_spent=Money(amount=45000, currency="USD"),
                default_address=Address(
                    address1="123 Main St",
                    city="New York",
                    province_code="NY",
                    country_code="US",
                    zip="10001",
                ),
            )
        )
        self.upsert_customer = AsyncMock(
            return_value=Customer(
                provider_id="cust_new",
                email="new@example.com",
                first_name="New",
                last_name="Customer",
            )
        )

        self.verify_and_parse_webhook = AsyncMock(
            return_value=WebhookEventOut(
                provider="fake",
                topic="orders/create",
                resource_id="ord_1",
                data={"id": "ord_1"},
                verified=True,
                received_at=datetime(2025, 6, 15, tzinfo=UTC),
            )
        )

        self.raw_request = AsyncMock(return_value={"ok": True})


@pytest.fixture
def fake_adapter() -> FakeCommerceAdapter:
    """Return a fresh fake commerce adapter with mocked methods."""
    return FakeCommerceAdapter()


@pytest.fixture
def registry(fake_adapter: FakeCommerceAdapter) -> CommerceRegistry:
    """Return a registry with the fake adapter registered."""
    reg = CommerceRegistry()
    reg.register(fake_adapter)
    return reg


@pytest.fixture(autouse=True)
def _commerce_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set minimal env vars for commerce settings."""
    monkeypatch.setenv("COMMERCE_PROVIDER", "fake")
    monkeypatch.setenv("SHOPIFY_ACCESS_TOKEN", "shpat_test_token")
    monkeypatch.setenv("SHOPIFY_SHOP_DOMAIN", "test-store.myshopify.com")
    monkeypatch.setenv("SHOPIFY_WEBHOOK_SECRET", "whsec_test_secret")

    # Reset singletons between tests
    import svc_infra.commerce.provider.registry as registry_mod
    import svc_infra.commerce.settings as settings_mod

    settings_mod._SETTINGS = None
    registry_mod._REGISTRY = None
