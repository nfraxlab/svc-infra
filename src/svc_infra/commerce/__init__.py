"""Commerce integration module for svc-infra.

Provider-agnostic commerce interface with capability-based design.
Ships Shopify as the first provider; others plug in via the registry.

Usage::

    from svc_infra.commerce import CommerceService

    svc = CommerceService.from_settings(provider="shopify")
    products = await svc.products.list(limit=20)
    order = await svc.orders.get("order-id-123")
"""

from .provider.base import CommerceProvider
from .provider.registry import get_commerce_registry
from .schemas import (
    Address,
    Customer,
    CustomerUpsertIn,
    FulfillmentCreateIn,
    FulfillmentOut,
    InventoryAdjustIn,
    InventoryLevel,
    Money,
    Order,
    OrderListFilter,
    Product,
    ProductListFilter,
    ProductUpsertIn,
    Variant,
    VariantUpsertIn,
    WebhookEventIn,
    WebhookEventOut,
)
from .service import CommerceService
from .settings import CommerceSettings, get_commerce_settings

__all__ = [
    # Service
    "CommerceService",
    # Provider
    "CommerceProvider",
    "get_commerce_registry",
    # Settings
    "CommerceSettings",
    "get_commerce_settings",
    # Schemas
    "Address",
    "Customer",
    "CustomerUpsertIn",
    "FulfillmentCreateIn",
    "FulfillmentOut",
    "InventoryAdjustIn",
    "InventoryLevel",
    "Money",
    "Order",
    "OrderListFilter",
    "Product",
    "ProductListFilter",
    "ProductUpsertIn",
    "Variant",
    "VariantUpsertIn",
    "WebhookEventIn",
    "WebhookEventOut",
]
