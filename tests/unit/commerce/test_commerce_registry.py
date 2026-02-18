"""Tests for the commerce provider registry."""

from __future__ import annotations

import pytest

from svc_infra.commerce.provider.registry import CommerceRegistry, get_commerce_registry


class TestCommerceRegistry:
    def test_register_and_get(self, fake_adapter) -> None:
        reg = CommerceRegistry()
        reg.register(fake_adapter)
        assert reg.get("fake") is fake_adapter

    def test_get_case_insensitive(self, fake_adapter) -> None:
        reg = CommerceRegistry()
        reg.register(fake_adapter)
        assert reg.get("FAKE") is fake_adapter

    def test_get_missing_raises(self) -> None:
        reg = CommerceRegistry()
        with pytest.raises(RuntimeError, match="No commerce adapter registered"):
            reg.get("nonexistent")

    def test_get_default_from_settings(self, fake_adapter, monkeypatch) -> None:
        """When no name is passed, falls back to settings.default_provider."""
        import svc_infra.commerce.settings as settings_mod
        from svc_infra.commerce.settings import CommerceSettings

        # Explicitly construct settings with default_provider="fake"
        # because the module-level _PROVIDER is read at import time
        settings_mod._SETTINGS = CommerceSettings(default_provider="fake")

        reg = CommerceRegistry()
        reg.register(fake_adapter)
        assert reg.get() is fake_adapter

    def test_providers_property(self, fake_adapter) -> None:
        reg = CommerceRegistry()
        assert reg.providers == []
        reg.register(fake_adapter)
        assert reg.providers == ["fake"]

    def test_error_message_includes_registered(self, fake_adapter) -> None:
        reg = CommerceRegistry()
        reg.register(fake_adapter)
        with pytest.raises(RuntimeError, match="fake"):
            reg.get("missing")

    def test_singleton_accessor(self, monkeypatch) -> None:
        import svc_infra.commerce.provider.registry as mod

        mod._REGISTRY = None
        reg1 = get_commerce_registry()
        reg2 = get_commerce_registry()
        assert reg1 is reg2
