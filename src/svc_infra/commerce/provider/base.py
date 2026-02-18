"""Capability-based commerce provider protocol.

Providers implement whichever capabilities they support. Unsupported capabilities
raise ``NotImplementedError`` at the protocol default level, so consumers can
gracefully degrade or feature-detect via ``hasattr`` / try-except.

The interface is intentionally thin. Each method maps to a single,
well-defined platform operation. Orchestration lives in ``CommerceService``.
"""

from __future__ import annotations

from typing import Any, Protocol

from ..schemas import (
    Customer,
    CustomerUpsertIn,
    FulfillmentCreateIn,
    FulfillmentOut,
    InventoryAdjustIn,
    InventoryLevel,
    Order,
    OrderListFilter,
    Product,
    ProductListFilter,
    ProductUpsertIn,
    WebhookEventIn,
    WebhookEventOut,
)


class CommerceProvider(Protocol):
    """Structural protocol for commerce platform adapters.

    Providers MUST set ``name`` to their registry key (e.g. ``"shopify"``).
    All methods are async. Pagination returns ``(items, next_cursor | None)``.
    """

    name: str

    # --- Products -----------------------------------------------------------

    async def list_products(self, f: ProductListFilter) -> tuple[list[Product], str | None]:
        """List products with optional filters + cursor pagination."""
        raise NotImplementedError

    async def get_product(self, provider_id: str) -> Product:
        """Fetch a single product by its provider-side ID."""
        raise NotImplementedError

    async def upsert_product(self, data: ProductUpsertIn) -> Product:
        """Create or update a product."""
        raise NotImplementedError

    async def delete_product(self, provider_id: str) -> None:
        """Delete / archive a product."""
        raise NotImplementedError

    # --- Inventory ----------------------------------------------------------

    async def get_inventory(self, provider_variant_id: str) -> InventoryLevel:
        """Get current inventory level for a variant."""
        raise NotImplementedError

    async def adjust_inventory(self, data: InventoryAdjustIn) -> InventoryLevel:
        """Atomically adjust inventory quantity (delta)."""
        raise NotImplementedError

    # --- Orders -------------------------------------------------------------

    async def list_orders(self, f: OrderListFilter) -> tuple[list[Order], str | None]:
        """List orders with filters + cursor pagination."""
        raise NotImplementedError

    async def get_order(self, provider_id: str) -> Order:
        """Fetch a single order by its provider-side ID."""
        raise NotImplementedError

    async def cancel_order(self, provider_id: str, *, reason: str | None = None) -> Order:
        """Request order cancellation."""
        raise NotImplementedError

    async def close_order(self, provider_id: str) -> Order:
        """Mark an order as closed / completed."""
        raise NotImplementedError

    # --- Fulfillment --------------------------------------------------------

    async def create_fulfillment(self, data: FulfillmentCreateIn) -> FulfillmentOut:
        """Create a fulfillment (ship items) for an order."""
        raise NotImplementedError

    # --- Customers ----------------------------------------------------------

    async def get_customer(self, provider_id: str) -> Customer | None:
        """Fetch a customer by provider-side ID. Returns ``None`` if not found."""
        raise NotImplementedError

    async def upsert_customer(self, data: CustomerUpsertIn) -> Customer:
        """Create or update a customer."""
        raise NotImplementedError

    # --- Webhooks -----------------------------------------------------------

    async def verify_and_parse_webhook(self, event: WebhookEventIn) -> WebhookEventOut:
        """Verify signature and normalise webhook payload."""
        raise NotImplementedError

    # --- Raw / escape hatch -------------------------------------------------

    async def raw_request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make an arbitrary authenticated request to the provider API.

        Useful for one-off operations not covered by the typed interface.
        """
        raise NotImplementedError
