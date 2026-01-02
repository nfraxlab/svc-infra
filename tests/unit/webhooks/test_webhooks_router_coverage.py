"""Tests for webhooks router - Coverage improvement."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from svc_infra.webhooks.router import (
    add_subscription,
    get_outbox,
    get_service,
    get_subs,
)
from svc_infra.webhooks.router import (
    test_fire as fire_webhook,
)

# ─── Dependency Tests ──────────────────────────────────────────────────────


class TestDependencies:
    """Tests for router dependencies."""

    def test_get_outbox(self) -> None:
        """Test get_outbox returns store."""
        outbox = get_outbox()
        assert outbox is not None

    def test_get_subs(self) -> None:
        """Test get_subs returns subscriptions."""
        subs = get_subs()
        assert subs is not None

    def test_get_service(self) -> None:
        """Test get_service returns WebhookService."""
        outbox = get_outbox()
        subs = get_subs()
        service = get_service(outbox=outbox, subs=subs)
        assert service is not None


# ─── add_subscription Tests ────────────────────────────────────────────────


class TestAddSubscription:
    """Tests for add_subscription endpoint."""

    def test_success(self) -> None:
        """Test successful subscription."""
        subs = get_subs()
        body = {"topic": "user.created", "url": "https://example.com/hook", "secret": "abc123"}

        result = add_subscription(body, subs=subs)

        assert result == {"ok": True}

    def test_missing_topic(self) -> None:
        """Test raises when topic missing."""
        subs = get_subs()
        body = {"url": "https://example.com/hook", "secret": "abc123"}

        with pytest.raises(HTTPException) as exc_info:
            add_subscription(body, subs=subs)

        assert exc_info.value.status_code == 400
        assert "Missing topic/url/secret" in exc_info.value.detail

    def test_missing_url(self) -> None:
        """Test raises when url missing."""
        subs = get_subs()
        body = {"topic": "user.created", "secret": "abc123"}

        with pytest.raises(HTTPException) as exc_info:
            add_subscription(body, subs=subs)

        assert exc_info.value.status_code == 400

    def test_missing_secret(self) -> None:
        """Test raises when secret missing."""
        subs = get_subs()
        body = {"topic": "user.created", "url": "https://example.com/hook"}

        with pytest.raises(HTTPException) as exc_info:
            add_subscription(body, subs=subs)

        assert exc_info.value.status_code == 400


# ─── test_fire Tests ───────────────────────────────────────────────────────


class TestTestFire:
    """Tests for test_fire endpoint."""

    def test_success(self) -> None:
        """Test successful fire."""
        outbox = get_outbox()
        subs = get_subs()
        svc = get_service(outbox=outbox, subs=subs)
        body = {"topic": "user.created", "payload": {"user_id": 123}}

        result = fire_webhook(body, svc=svc)

        assert result["ok"] is True
        assert "outbox_id" in result

    def test_with_empty_payload(self) -> None:
        """Test fire with no payload."""
        outbox = get_outbox()
        subs = get_subs()
        svc = get_service(outbox=outbox, subs=subs)
        body = {"topic": "user.created"}

        result = fire_webhook(body, svc=svc)

        assert result["ok"] is True

    def test_missing_topic(self) -> None:
        """Test raises when topic missing."""
        outbox = get_outbox()
        subs = get_subs()
        svc = get_service(outbox=outbox, subs=subs)
        body = {"payload": {"data": "value"}}

        with pytest.raises(HTTPException) as exc_info:
            fire_webhook(body, svc=svc)

        assert exc_info.value.status_code == 400
        assert "Missing topic" in exc_info.value.detail
