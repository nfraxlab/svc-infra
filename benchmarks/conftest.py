"""Benchmark fixtures and configuration for svc-infra."""

from __future__ import annotations

import pytest
from fastapi import FastAPI


@pytest.fixture
def base_app() -> FastAPI:
    """Minimal FastAPI app for baseline comparison."""
    return FastAPI(title="Benchmark")


@pytest.fixture
def sample_cache_data() -> dict[str, str]:
    """Sample data for cache benchmarks."""
    return {f"key_{i}": f"value_{i}" for i in range(100)}


@pytest.fixture
def sample_jwt_payload() -> dict:
    """Sample JWT payload for auth benchmarks."""
    return {
        "sub": "user_123",
        "email": "user@example.com",
        "exp": 9999999999,
        "iat": 1700000000,
        "roles": ["user"],
    }


@pytest.fixture
def sample_request_headers() -> dict[str, str]:
    """Sample headers for middleware benchmarks."""
    return {
        "Authorization": "Bearer test_token",
        "Content-Type": "application/json",
        "X-Request-ID": "req_123",
    }
