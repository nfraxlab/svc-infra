"""Commerce domain schemas.

Minimal, provider-agnostic Pydantic models that map cleanly to Shopify,
WooCommerce, BigCommerce, and Square without pretending they are identical.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, Field, StringConstraints

# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
"""ISO 4217 currency code (e.g. USD, CAD, EUR)."""


class Money(BaseModel):
    """Monetary amount in minor units (cents) with currency."""

    amount: int = Field(ge=0, description="Amount in minor units (cents)")
    currency: Currency = "USD"


class Address(BaseModel):
    """Postal address used for shipping / billing."""

    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    address1: str | None = None
    address2: str | None = None
    city: str | None = None
    province: str | None = None
    province_code: str | None = None
    country: str | None = None
    country_code: str | None = None
    zip: str | None = None
    phone: str | None = None


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------


class ProductStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"


class Variant(BaseModel):
    """A purchasable variant of a product (size, colour, etc.)."""

    provider_id: str
    title: str = ""
    sku: str | None = None
    price: Money | None = None
    compare_at_price: Money | None = None
    inventory_quantity: int | None = None
    weight: float | None = None
    weight_unit: str | None = None
    barcode: str | None = None
    position: int = 1
    requires_shipping: bool = True
    taxable: bool = True


class Product(BaseModel):
    """Normalised product representation."""

    provider_id: str
    title: str
    handle: str | None = None
    body_html: str | None = None
    vendor: str | None = None
    product_type: str | None = None
    status: ProductStatus = ProductStatus.ACTIVE
    tags: list[str] = Field(default_factory=list)
    variants: list[Variant] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list, description="Image URLs")
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class VariantUpsertIn(BaseModel):
    """Input schema for creating or updating a variant."""

    title: str = ""
    sku: str | None = None
    price: Money | None = None
    compare_at_price: Money | None = None
    inventory_quantity: int | None = None
    weight: float | None = None
    weight_unit: str | None = None
    barcode: str | None = None
    requires_shipping: bool = True
    taxable: bool = True


class ProductUpsertIn(BaseModel):
    """Input schema for creating or updating a product."""

    title: str
    body_html: str | None = None
    vendor: str | None = None
    product_type: str | None = None
    status: ProductStatus = ProductStatus.ACTIVE
    tags: list[str] = Field(default_factory=list)
    variants: list[VariantUpsertIn] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProductListFilter(BaseModel):
    """Filter for product listing."""

    status: ProductStatus | None = None
    product_type: str | None = None
    vendor: str | None = None
    limit: int = Field(default=50, ge=1, le=250)
    cursor: str | None = None


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


class InventoryLevel(BaseModel):
    """Stock level for a variant at a location."""

    provider_variant_id: str
    location_id: str | None = None
    available: int = 0
    updated_at: datetime | None = None


class InventoryAdjustIn(BaseModel):
    """Input for adjusting inventory quantity."""

    provider_variant_id: str
    location_id: str | None = None
    adjustment: int = Field(description="Delta; negative to decrement")


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------


class OrderStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    ANY = "any"


class FinancialStatus(str, Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    PARTIALLY_REFUNDED = "partially_refunded"
    REFUNDED = "refunded"
    VOIDED = "voided"


class FulfillmentStatus(str, Enum):
    UNFULFILLED = "unfulfilled"
    PARTIAL = "partial"
    FULFILLED = "fulfilled"


class TaxLine(BaseModel):
    """Tax applied to a line item."""

    title: str
    rate: float
    price: Money


class LineItem(BaseModel):
    """A single line item in an order."""

    provider_id: str
    variant_id: str | None = None
    product_id: str | None = None
    title: str = ""
    quantity: int = 1
    price: Money | None = None
    sku: str | None = None
    requires_shipping: bool = True
    taxable: bool = True
    tax_lines: list[TaxLine] = Field(default_factory=list)


class Order(BaseModel):
    """Normalised order representation."""

    provider_id: str
    order_number: str | None = None
    email: str | None = None
    status: OrderStatus = OrderStatus.OPEN
    financial_status: FinancialStatus = FinancialStatus.PENDING
    fulfillment_status: FulfillmentStatus | None = None
    currency: Currency = "USD"
    subtotal: Money | None = None
    total_tax: Money | None = None
    total: Money | None = None
    line_items: list[LineItem] = Field(default_factory=list)
    shipping_address: Address | None = None
    billing_address: Address | None = None
    customer_id: str | None = None
    note: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    cancelled_at: datetime | None = None
    closed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OrderListFilter(BaseModel):
    """Filter for order listing."""

    status: OrderStatus | None = None
    financial_status: FinancialStatus | None = None
    fulfillment_status: FulfillmentStatus | None = None
    since_id: str | None = None
    created_at_min: datetime | None = None
    created_at_max: datetime | None = None
    limit: int = Field(default=50, ge=1, le=250)
    cursor: str | None = None


# ---------------------------------------------------------------------------
# Fulfillment
# ---------------------------------------------------------------------------


class FulfillmentCreateIn(BaseModel):
    """Input for creating a fulfillment against an order."""

    order_provider_id: str
    tracking_company: str | None = None
    tracking_number: str | None = None
    tracking_url: str | None = None
    line_item_ids: list[str] = Field(
        default_factory=list,
        description="Specific line items to fulfill; empty = fulfill all",
    )
    notify_customer: bool = True


class FulfillmentOut(BaseModel):
    """Fulfillment result from the provider."""

    provider_id: str
    order_provider_id: str
    status: str = ""
    tracking_company: str | None = None
    tracking_number: str | None = None
    tracking_url: str | None = None
    created_at: datetime | None = None


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------


class Customer(BaseModel):
    """Normalised customer representation."""

    provider_id: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    orders_count: int = 0
    total_spent: Money | None = None
    default_address: Address | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CustomerUpsertIn(BaseModel):
    """Input for creating or updating a customer."""

    email: str
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    tags: list[str] = Field(default_factory=list)
    default_address: Address | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------


class WebhookEventIn(BaseModel):
    """Raw inbound webhook payload."""

    provider: str
    topic: str
    payload: bytes
    signature: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)


class WebhookEventOut(BaseModel):
    """Parsed + verified webhook result."""

    provider: str
    topic: str
    resource_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    received_at: datetime | None = None
    verified: bool = False
