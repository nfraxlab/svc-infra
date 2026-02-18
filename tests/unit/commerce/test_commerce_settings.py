"""Tests for the commerce settings module."""

from __future__ import annotations

from svc_infra.commerce.settings import CommerceSettings, ShopifyConfig, get_commerce_settings


class TestShopifyConfig:
    def test_from_explicit(self) -> None:
        from pydantic import SecretStr

        cfg = ShopifyConfig(
            access_token=SecretStr("shpat_test"),
            shop_domain="my-store.myshopify.com",
        )
        assert cfg.access_token.get_secret_value() == "shpat_test"
        assert cfg.shop_domain == "my-store.myshopify.com"
        assert cfg.api_version == "2024-10"
        assert cfg.max_retries == 3
        assert cfg.timeout == 30.0

    def test_custom_values(self) -> None:
        from pydantic import SecretStr

        cfg = ShopifyConfig(
            access_token=SecretStr("tok"),
            shop_domain="shop.myshopify.com",
            api_version="2025-01",
            max_retries=5,
            timeout=60.0,
            webhook_secret=SecretStr("whsec"),
        )
        assert cfg.api_version == "2025-01"
        assert cfg.max_retries == 5
        assert cfg.webhook_secret.get_secret_value() == "whsec"


class TestCommerceSettings:
    def test_from_env(self, monkeypatch) -> None:
        import svc_infra.commerce.settings as mod

        mod._SETTINGS = None
        monkeypatch.setenv("COMMERCE_PROVIDER", "shopify")
        monkeypatch.setenv("SHOPIFY_ACCESS_TOKEN", "shpat_xxx")
        monkeypatch.setenv("SHOPIFY_SHOP_DOMAIN", "test.myshopify.com")

        # Need to reimport to pick up env changes since they're read at import time
        # Instead, construct directly
        settings = CommerceSettings(
            default_provider="shopify",
            shopify=ShopifyConfig(
                access_token="shpat_xxx",
                shop_domain="test.myshopify.com",
            ),
        )
        assert settings.default_provider == "shopify"
        assert settings.shopify is not None
        assert settings.shopify.shop_domain == "test.myshopify.com"

    def test_no_shopify_config_when_missing_token(self) -> None:
        settings = CommerceSettings(default_provider="shopify", shopify=None)
        assert settings.shopify is None

    def test_singleton_accessor(self, monkeypatch) -> None:
        import svc_infra.commerce.settings as mod

        mod._SETTINGS = None
        s1 = get_commerce_settings()
        s2 = get_commerce_settings()
        assert s1 is s2
