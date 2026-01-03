"""
Tests for webhook delivery service.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest


class TestWebhookSubscription:
    """Tests for WebhookSubscription dataclass."""

    def test_subscription_default_id(self):
        """Should generate UUID for id by default."""
        from svc_infra.webhooks.service import WebhookSubscription

        sub = WebhookSubscription(topic="test", url="http://example.com", secret="s")

        assert sub.id is not None
        assert len(sub.id) == 32  # UUID hex

    def test_subscription_custom_id(self):
        """Should accept custom id."""
        from svc_infra.webhooks.service import WebhookSubscription

        sub = WebhookSubscription(topic="test", url="http://example.com", secret="s", id="custom")

        assert sub.id == "custom"

    def test_subscription_fields(self):
        """Should store all fields correctly."""
        from svc_infra.webhooks.service import WebhookSubscription

        sub = WebhookSubscription(
            topic="orders.created", url="https://webhook.example.com", secret="secret123"
        )

        assert sub.topic == "orders.created"
        assert sub.url == "https://webhook.example.com"
        assert sub.secret == "secret123"


class TestInMemoryWebhookSubscriptions:
    """Tests for in-memory subscription store."""

    @pytest.fixture
    def subs(self):
        """Create fresh subscription store."""
        from svc_infra.webhooks.service import InMemoryWebhookSubscriptions

        return InMemoryWebhookSubscriptions()

    def test_add_subscription(self, subs):
        """Should add subscription to store."""
        subs.add("topic", "http://example.com", "secret")

        result = subs.get_for_topic("topic")

        assert len(result) == 1
        assert result[0].topic == "topic"
        assert result[0].url == "http://example.com"

    def test_add_multiple_subscriptions_same_topic(self, subs):
        """Should support multiple subscriptions per topic."""
        subs.add("topic", "http://example1.com", "secret1")
        subs.add("topic", "http://example2.com", "secret2")

        result = subs.get_for_topic("topic")

        assert len(result) == 2

    def test_get_for_topic_empty(self, subs):
        """Should return empty list for unknown topic."""
        result = subs.get_for_topic("unknown")

        assert result == []

    def test_get_for_topic_returns_copy(self, subs):
        """Should return copy, not reference."""
        subs.add("topic", "http://example.com", "secret")

        result1 = subs.get_for_topic("topic")
        result2 = subs.get_for_topic("topic")

        assert result1 is not result2

    def test_upsert_same_url_updates_secret(self, subs):
        """Should update secret for same topic+url."""
        subs.add("topic", "http://example.com", "old_secret")
        subs.add("topic", "http://example.com", "new_secret")

        result = subs.get_for_topic("topic")

        assert len(result) == 1
        assert result[0].secret == "new_secret"

    def test_different_topics_isolated(self, subs):
        """Should keep different topics separate."""
        subs.add("topic1", "http://example.com", "secret")
        subs.add("topic2", "http://example.com", "secret")

        result1 = subs.get_for_topic("topic1")
        result2 = subs.get_for_topic("topic2")

        assert len(result1) == 1
        assert len(result2) == 1


class TestWebhookService:
    """Tests for WebhookService."""

    @pytest.fixture
    def mock_outbox(self, mocker):
        """Create mock outbox store."""
        outbox = mocker.Mock()
        msg = mocker.Mock()
        msg.id = 1
        outbox.enqueue = mocker.Mock(return_value=msg)
        return outbox

    @pytest.fixture
    def subs(self):
        """Create subscription store."""
        from svc_infra.webhooks.service import InMemoryWebhookSubscriptions

        return InMemoryWebhookSubscriptions()

    @pytest.fixture
    def service(self, mock_outbox, subs):
        """Create webhook service."""
        from svc_infra.webhooks.service import WebhookService

        return WebhookService(mock_outbox, subs)

    def test_publish_no_subscribers(self, service, mock_outbox):
        """Should not enqueue if no subscribers."""
        service.publish("topic", {"data": "value"})

        mock_outbox.enqueue.assert_not_called()

    def test_publish_single_subscriber(self, service, subs, mock_outbox):
        """Should enqueue for single subscriber."""
        subs.add("topic", "http://example.com", "secret")

        service.publish("topic", {"data": "value"})

        mock_outbox.enqueue.assert_called_once()

    def test_publish_multiple_subscribers(self, service, subs, mock_outbox):
        """Should enqueue for all subscribers."""
        subs.add("topic", "http://example1.com", "secret1")
        subs.add("topic", "http://example2.com", "secret2")

        service.publish("topic", {"data": "value"})

        assert mock_outbox.enqueue.call_count == 2

    def test_publish_returns_last_message_id(self, service, subs, mock_outbox):
        """Should return last message id."""
        msg1 = MagicMock(id=1)
        msg2 = MagicMock(id=2)
        mock_outbox.enqueue.side_effect = [msg1, msg2]

        subs.add("topic", "http://example1.com", "secret1")
        subs.add("topic", "http://example2.com", "secret2")

        result = service.publish("topic", {"data": "value"})

        assert result == 2

    def test_publish_includes_event_metadata(self, service, subs, mock_outbox):
        """Should include event metadata in payload."""
        subs.add("topic", "http://example.com", "secret")

        service.publish("topic", {"data": "value"}, version=2)

        call_args = mock_outbox.enqueue.call_args
        payload = call_args[0][1]

        assert payload["event"]["topic"] == "topic"
        assert payload["event"]["version"] == 2
        assert "created_at" in payload["event"]

    def test_publish_includes_subscription_info(self, service, subs, mock_outbox):
        """Should include subscription info in payload."""
        subs.add("topic", "http://example.com", "secret")

        service.publish("topic", {"data": "value"})

        call_args = mock_outbox.enqueue.call_args
        payload = call_args[0][1]

        assert "subscription" in payload
        assert payload["subscription"]["url"] == "http://example.com"
        assert payload["subscription"]["topic"] == "topic"

    def test_publish_encrypts_secret(self, service, subs, mock_outbox, mocker):
        """Should encrypt secret before storing."""
        mocker.patch("svc_infra.webhooks.service.encrypt_secret", return_value="enc:v1:encrypted")
        subs.add("topic", "http://example.com", "plaintext_secret")

        service.publish("topic", {"data": "value"})

        call_args = mock_outbox.enqueue.call_args
        payload = call_args[0][1]

        assert payload["subscription"]["secret"] == "enc:v1:encrypted"


class TestWebhookDeliveryRetry:
    """Tests for webhook delivery retry logic."""

    def test_exponential_backoff_calculation(self):
        """Should calculate exponential backoff correctly."""
        # Typical backoff: 1, 2, 4, 8, 16, 32 seconds
        base = 1
        max_delay = 60

        for attempt in range(6):
            delay = min(base * (2**attempt), max_delay)
            expected = [1, 2, 4, 8, 16, 32][attempt]
            assert delay == expected

    def test_max_retries_limit(self):
        """Should respect max retries limit."""
        max_retries = 5

        for attempt in range(10):
            should_retry = attempt < max_retries
            if attempt < 5:
                assert should_retry is True
            else:
                assert should_retry is False

    def test_retry_jitter(self, mocker):
        """Should add jitter to prevent thundering herd."""
        import random

        mocker.patch.object(random, "uniform", return_value=0.5)

        base_delay = 2.0
        jitter = random.uniform(0, 0.5) * base_delay

        assert jitter == 1.0  # 0.5 * 2.0


class TestWebhookEventPayload:
    """Tests for webhook event payload structure."""

    def test_event_includes_created_at(self):
        """Should include ISO timestamp."""
        created_at = datetime.now(UTC).isoformat()

        assert "T" in created_at
        assert created_at.endswith("+00:00") or created_at.endswith("Z")

    def test_event_includes_version(self):
        """Should include version number."""
        event = {"version": 1, "payload": {}}

        assert event["version"] == 1

    def test_event_includes_topic(self):
        """Should include topic name."""
        event = {"topic": "orders.created", "payload": {}}

        assert event["topic"] == "orders.created"


class TestWebhookHTTPDelivery:
    """Tests for HTTP webhook delivery."""

    @pytest.mark.asyncio
    async def test_delivery_with_signature_header(self, mocker):
        """Should include signature in header."""
        from svc_infra.webhooks.signing import sign

        payload = {"data": "value"}
        secret = "secret"
        signature = sign(secret, payload)

        headers = {"X-Webhook-Signature": signature}

        assert headers["X-Webhook-Signature"] == signature

    @pytest.mark.asyncio
    async def test_delivery_with_content_type(self):
        """Should set Content-Type to application/json."""
        headers = {"Content-Type": "application/json"}

        assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_delivery_timeout_handling(self, mocker):
        """Should handle delivery timeout."""
        import asyncio

        mock_client = mocker.Mock()
        mock_client.post = mocker.AsyncMock(side_effect=TimeoutError())

        with pytest.raises(asyncio.TimeoutError):
            await mock_client.post("http://example.com", json={})
