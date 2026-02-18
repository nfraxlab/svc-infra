"""Commerce settings loaded from environment variables.

Pattern mirrors ``apf_payments.settings``: pydantic models with ``SecretStr``,
env-var defaults at import time, lazy singleton accessor.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, SecretStr

# ---------------------------------------------------------------------------
# Environment variable reads (at import time, like apf_payments)
# ---------------------------------------------------------------------------

_PROVIDER = (
    os.getenv("COMMERCE_PROVIDER") or os.getenv("SVC_COMMERCE_PROVIDER", "shopify")
).lower()  # type: ignore[union-attr]  # always str due to default

# Shopify
_SHOPIFY_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN") or os.getenv("SHOPIFY_ADMIN_TOKEN")
_SHOPIFY_SHOP = os.getenv("SHOPIFY_SHOP_DOMAIN") or os.getenv("SHOPIFY_SHOP")
_SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-10")
_SHOPIFY_WH_SECRET = os.getenv("SHOPIFY_WEBHOOK_SECRET")


# ---------------------------------------------------------------------------
# Per-provider config models
# ---------------------------------------------------------------------------


class ShopifyConfig(BaseModel):
    """Configuration for the Shopify provider."""

    access_token: SecretStr
    shop_domain: str
    api_version: str = "2024-10"
    webhook_secret: SecretStr | None = None
    max_retries: int = 3
    timeout: float = 30.0


# ---------------------------------------------------------------------------
# Aggregated settings
# ---------------------------------------------------------------------------


class CommerceSettings(BaseModel):
    """Top-level commerce configuration."""

    default_provider: str = _PROVIDER

    shopify: ShopifyConfig | None = (
        ShopifyConfig(
            access_token=SecretStr(_SHOPIFY_TOKEN),
            shop_domain=_SHOPIFY_SHOP or "",
            api_version=_SHOPIFY_API_VERSION,
            webhook_secret=SecretStr(_SHOPIFY_WH_SECRET) if _SHOPIFY_WH_SECRET else None,
        )
        if _SHOPIFY_TOKEN and _SHOPIFY_SHOP
        else None
    )


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_SETTINGS: CommerceSettings | None = None


def get_commerce_settings() -> CommerceSettings:
    """Return the module-level singleton settings instance."""
    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = CommerceSettings()
    return _SETTINGS
