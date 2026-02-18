"""Singleton provider registry for commerce adapters.

Mirrors the pattern established by ``apf_payments.provider.registry``.
"""

from __future__ import annotations

from ..settings import get_commerce_settings
from .base import CommerceProvider


class CommerceRegistry:
    """In-process registry of commerce provider adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, CommerceProvider] = {}

    def register(self, adapter: CommerceProvider) -> None:
        """Register an adapter keyed by ``adapter.name``."""
        self._adapters[adapter.name.lower()] = adapter

    def get(self, name: str | None = None) -> CommerceProvider:
        """Resolve an adapter by name (falls back to default from settings)."""
        settings = get_commerce_settings()
        key = (name or settings.default_provider).lower()
        if key not in self._adapters:
            registered = ", ".join(sorted(self._adapters)) or "(none)"
            raise RuntimeError(
                f"No commerce adapter registered for '{key}'. "
                f"Registered adapters: {registered}. "
                "Install and register a provider (e.g. Shopify) or pass a custom adapter."
            )
        return self._adapters[key]

    @property
    def providers(self) -> list[str]:
        """Return names of all registered providers."""
        return sorted(self._adapters)


_REGISTRY: CommerceRegistry | None = None


def get_commerce_registry() -> CommerceRegistry:
    """Return the module-level singleton registry."""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = CommerceRegistry()
    return _REGISTRY
