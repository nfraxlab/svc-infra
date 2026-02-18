"""Commerce service facade.

Wraps a ``CommerceProvider`` with operational concerns:
- Structured logging on every call
- Graceful ``NotImplementedError`` surfacing
- Provider resolution via the registry
- Consistent error context

This is the primary public API. Consumers import ``CommerceService`` and call
its namespaced methods (``svc.products.list()``, ``svc.orders.get()``).
"""

from __future__ import annotations

from typing import Any

from svc_infra.logging import get_logger

from .provider.base import CommerceProvider
from .provider.registry import get_commerce_registry
from .schemas import (
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
from .settings import get_commerce_settings

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Capability namespaces
# ---------------------------------------------------------------------------


class _ProductOps:
    """Product operations namespace."""

    def __init__(self, adapter: CommerceProvider) -> None:
        self._a = adapter

    async def list(
        self,
        *,
        status: str | None = None,
        product_type: str | None = None,
        vendor: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[Product], str | None]:
        f = ProductListFilter(
            status=status,  # type: ignore[arg-type]
            product_type=product_type,
            vendor=vendor,
            limit=limit,
            cursor=cursor,
        )
        logger.debug("commerce.products.list", extra={"filter": f.model_dump(exclude_none=True)})
        return await self._a.list_products(f)

    async def get(self, provider_id: str) -> Product:
        logger.debug("commerce.products.get", extra={"provider_id": provider_id})
        return await self._a.get_product(provider_id)

    async def upsert(self, data: ProductUpsertIn) -> Product:
        logger.debug("commerce.products.upsert", extra={"title": data.title})
        return await self._a.upsert_product(data)

    async def delete(self, provider_id: str) -> None:
        logger.debug("commerce.products.delete", extra={"provider_id": provider_id})
        return await self._a.delete_product(provider_id)


class _InventoryOps:
    """Inventory operations namespace."""

    def __init__(self, adapter: CommerceProvider) -> None:
        self._a = adapter

    async def get(self, provider_variant_id: str) -> InventoryLevel:
        logger.debug(
            "commerce.inventory.get",
            extra={"provider_variant_id": provider_variant_id},
        )
        return await self._a.get_inventory(provider_variant_id)

    async def adjust(self, data: InventoryAdjustIn) -> InventoryLevel:
        logger.debug(
            "commerce.inventory.adjust",
            extra={
                "provider_variant_id": data.provider_variant_id,
                "adjustment": data.adjustment,
            },
        )
        return await self._a.adjust_inventory(data)


class _OrderOps:
    """Order operations namespace."""

    def __init__(self, adapter: CommerceProvider) -> None:
        self._a = adapter

    async def list(
        self,
        *,
        status: str | None = None,
        financial_status: str | None = None,
        fulfillment_status: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[Order], str | None]:
        f = OrderListFilter(
            status=status,  # type: ignore[arg-type]
            financial_status=financial_status,  # type: ignore[arg-type]
            fulfillment_status=fulfillment_status,  # type: ignore[arg-type]
            limit=limit,
            cursor=cursor,
        )
        logger.debug("commerce.orders.list", extra={"filter": f.model_dump(exclude_none=True)})
        return await self._a.list_orders(f)

    async def get(self, provider_id: str) -> Order:
        logger.debug("commerce.orders.get", extra={"provider_id": provider_id})
        return await self._a.get_order(provider_id)

    async def cancel(self, provider_id: str, *, reason: str | None = None) -> Order:
        logger.debug(
            "commerce.orders.cancel",
            extra={"provider_id": provider_id, "reason": reason},
        )
        return await self._a.cancel_order(provider_id, reason=reason)

    async def close(self, provider_id: str) -> Order:
        logger.debug("commerce.orders.close", extra={"provider_id": provider_id})
        return await self._a.close_order(provider_id)


class _FulfillmentOps:
    """Fulfillment operations namespace."""

    def __init__(self, adapter: CommerceProvider) -> None:
        self._a = adapter

    async def create(self, data: FulfillmentCreateIn) -> FulfillmentOut:
        logger.debug(
            "commerce.fulfillment.create",
            extra={"order_provider_id": data.order_provider_id},
        )
        return await self._a.create_fulfillment(data)


class _CustomerOps:
    """Customer operations namespace."""

    def __init__(self, adapter: CommerceProvider) -> None:
        self._a = adapter

    async def get(self, provider_id: str) -> Customer | None:
        logger.debug("commerce.customers.get", extra={"provider_id": provider_id})
        return await self._a.get_customer(provider_id)

    async def upsert(self, data: CustomerUpsertIn) -> Customer:
        logger.debug("commerce.customers.upsert", extra={"email": data.email})
        return await self._a.upsert_customer(data)


# ---------------------------------------------------------------------------
# Service facade
# ---------------------------------------------------------------------------


class CommerceService:
    """Unified commerce service facade.

    Usage::

        svc = CommerceService.from_settings(provider="shopify")
        products, cursor = await svc.products.list(limit=20)
        order = await svc.orders.get("12345")

    Or with explicit adapter::

        svc = CommerceService(adapter=my_adapter)
    """

    def __init__(
        self,
        *,
        adapter: CommerceProvider | None = None,
        provider_name: str | None = None,
    ) -> None:
        if adapter is not None:
            self._adapter = adapter
        else:
            name = (provider_name or get_commerce_settings().default_provider).lower()
            try:
                self._adapter = get_commerce_registry().get(name)
            except RuntimeError as exc:
                raise RuntimeError(
                    f"Cannot create CommerceService: {exc}. "
                    "Register a provider first or pass an explicit adapter."
                ) from exc

        # Expose capability namespaces
        self.products = _ProductOps(self._adapter)
        self.inventory = _InventoryOps(self._adapter)
        self.orders = _OrderOps(self._adapter)
        self.fulfillment = _FulfillmentOps(self._adapter)
        self.customers = _CustomerOps(self._adapter)

    @classmethod
    def from_settings(
        cls,
        *,
        provider: str | None = None,
    ) -> CommerceService:
        """Create a service using the provider registry + env-based settings."""
        return cls(provider_name=provider)

    @property
    def provider_name(self) -> str:
        """Return the name of the underlying provider."""
        return self._adapter.name

    async def verify_webhook(self, event: WebhookEventIn) -> WebhookEventOut:
        """Verify and parse a webhook using the underlying provider."""
        logger.debug(
            "commerce.webhook.verify",
            extra={"provider": event.provider, "topic": event.topic},
        )
        return await self._adapter.verify_and_parse_webhook(event)

    async def raw_request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Pass-through to the provider's escape-hatch raw request."""
        logger.debug(
            "commerce.raw_request",
            extra={"method": method, "path": path},
        )
        return await self._adapter.raw_request(method, path, json=json, params=params)
