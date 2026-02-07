"""Metrics package public API.

Provides lightweight, overridable hooks for abuse heuristics so callers can
plug in logging or a metrics backend without a hard dependency.
"""

from __future__ import annotations

from collections.abc import Callable

# Function variables so applications/tests can replace them at runtime.
on_rate_limit_exceeded: Callable[[str, int, int], None] | None = None
"""
Called when a request is rate-limited.
Args:
    key: identifier used for rate limiting (e.g., API key or IP)
    limit: configured limit for the window
    retry_after: seconds until next allowed attempt
"""

on_suspect_payload: Callable[[str | None, int], None] | None = None
"""
Called when a request exceeds the configured size limit.
Args:
    path: request path if available
    size: reported content-length
"""


def emit_rate_limited(key: str, limit: int, retry_after: int) -> None:
    if on_rate_limit_exceeded:
        try:
            on_rate_limit_exceeded(key, limit, retry_after)
        except Exception:
            # Never break request flow on metrics exceptions
            pass


def emit_suspect_payload(path: str | None, size: int) -> None:
    if on_suspect_payload:
        try:
            on_suspect_payload(path, size)
        except Exception:
            pass


# Lazy submodule access so that dotted-path patching
# (e.g. ``mocker.patch("svc_infra.obs.metrics.sqlalchemy.bind...")``)
# resolves without an explicit prior import, while avoiding an eager
# dependency on prometheus_client for lightweight imports.
_SUBMODULES = frozenset({"asgi", "http", "sqlalchemy"})


def __getattr__(name: str) -> object:
    if name in _SUBMODULES:
        import importlib

        return importlib.import_module(f".{name}", __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "emit_rate_limited",
    "emit_suspect_payload",
    "on_rate_limit_exceeded",
    "on_suspect_payload",
]
