"""Unit tests for svc_infra.webhooks.service module."""

from __future__ import annotations

from svc_infra.db.outbox import InMemoryOutboxStore
from svc_infra.webhooks.service import (
    InMemoryWebhookSubscriptions,
    WebhookService,
    WebhookSubscription,
)


class TestWebhookSubscription:
    """Tests for WebhookSubscription dataclass."""

    def test_basic_creation(self) -> None:
        """Test basic subscription creation."""
        sub = WebhookSubscription(
            topic="order.created",
            url="https://example.com/webhook",
            secret="test_secret",
        )
        assert sub.topic == "order.created"
        assert sub.url == "https://example.com/webhook"
        assert sub.secret == "test_secret"
        assert sub.id  # Should have auto-generated ID

    def test_id_is_generated(self) -> None:
        """Test that ID is auto-generated."""
        sub = WebhookSubscription(topic="test", url="https://example.com", secret="secret")
        assert len(sub.id) == 32  # UUID hex format

    def test_custom_id(self) -> None:
        """Test custom ID can be provided."""
        sub = WebhookSubscription(
            topic="test", url="https://example.com", secret="secret", id="custom_id"
        )
        assert sub.id == "custom_id"


class TestInMemoryWebhookSubscriptions:
    """Tests for InMemoryWebhookSubscriptions."""

    def test_add_subscription(self) -> None:
        """Test adding a subscription."""
        subs = InMemoryWebhookSubscriptions()
        subs.add("order.created", "https://example.com/hook", "secret123")

        result = subs.get_for_topic("order.created")
        assert len(result) == 1
        assert result[0].topic == "order.created"
        assert result[0].url == "https://example.com/hook"
        assert result[0].secret == "secret123"

    def test_add_multiple_subscriptions_same_topic(self) -> None:
        """Test adding multiple subscriptions to same topic."""
        subs = InMemoryWebhookSubscriptions()
        subs.add("order.created", "https://example1.com/hook", "secret1")
        subs.add("order.created", "https://example2.com/hook", "secret2")

        result = subs.get_for_topic("order.created")
        assert len(result) == 2

    def test_add_subscriptions_different_topics(self) -> None:
        """Test adding subscriptions to different topics."""
        subs = InMemoryWebhookSubscriptions()
        subs.add("order.created", "https://example.com/hook", "secret1")
        subs.add("order.updated", "https://example.com/hook", "secret2")

        assert len(subs.get_for_topic("order.created")) == 1
        assert len(subs.get_for_topic("order.updated")) == 1

    def test_upsert_rotates_secret(self) -> None:
        """Test that adding same topic+url rotates secret."""
        subs = InMemoryWebhookSubscriptions()
        subs.add("order.created", "https://example.com/hook", "old_secret")
        subs.add("order.created", "https://example.com/hook", "new_secret")

        result = subs.get_for_topic("order.created")
        assert len(result) == 1
        assert result[0].secret == "new_secret"

    def test_get_for_missing_topic(self) -> None:
        """Test getting subscriptions for missing topic returns empty."""
        subs = InMemoryWebhookSubscriptions()
        result = subs.get_for_topic("nonexistent")
        assert result == []

    def test_get_returns_copy(self) -> None:
        """Test get_for_topic returns a copy, not original list."""
        subs = InMemoryWebhookSubscriptions()
        subs.add("test", "https://example.com", "secret")

        result = subs.get_for_topic("test")
        result.clear()  # Modify the returned list

        # Original should still have the subscription
        assert len(subs.get_for_topic("test")) == 1


class TestWebhookService:
    """Tests for WebhookService."""

    def test_publish_creates_outbox_message(self) -> None:
        """Test publish creates message in outbox."""
        outbox = InMemoryOutboxStore()
        subs = InMemoryWebhookSubscriptions()
        subs.add("order.created", "https://example.com/hook", "secret")
        service = WebhookService(outbox, subs)

        msg_id = service.publish("order.created", {"order_id": "123"})
        assert msg_id > 0

    def test_publish_includes_event_data(self) -> None:
        """Test published message includes event data."""
        outbox = InMemoryOutboxStore()
        subs = InMemoryWebhookSubscriptions()
        subs.add("test", "https://example.com", "secret")
        service = WebhookService(outbox, subs)

        service.publish("test", {"key": "value"}, version=2)

        msg = outbox.fetch_next()
        assert msg is not None
        assert msg.payload["event"]["topic"] == "test"
        assert msg.payload["event"]["payload"] == {"key": "value"}
        assert msg.payload["event"]["version"] == 2
        assert "created_at" in msg.payload["event"]

    def test_publish_includes_subscription_info(self) -> None:
        """Test published message includes subscription info."""
        outbox = InMemoryOutboxStore()
        subs = InMemoryWebhookSubscriptions()
        subs.add("test", "https://example.com/hook", "my_secret")
        service = WebhookService(outbox, subs)

        service.publish("test", {"data": 1})

        msg = outbox.fetch_next()
        assert msg is not None
        assert msg.payload["subscription"]["topic"] == "test"
        assert msg.payload["subscription"]["url"] == "https://example.com/hook"
        # Secret should be encrypted
        assert "secret" in msg.payload["subscription"]

    def test_publish_to_multiple_subscribers(self) -> None:
        """Test publishing to topic with multiple subscribers."""
        outbox = InMemoryOutboxStore()
        subs = InMemoryWebhookSubscriptions()
        subs.add("test", "https://example1.com", "secret1")
        subs.add("test", "https://example2.com", "secret2")
        service = WebhookService(outbox, subs)

        service.publish("test", {"data": 1})

        # Should have enqueued 2 messages
        msg1 = outbox.fetch_next()
        assert msg1 is not None
        outbox.mark_processed(msg1.id)

        msg2 = outbox.fetch_next()
        assert msg2 is not None

    def test_publish_no_subscribers(self) -> None:
        """Test publishing to topic with no subscribers."""
        outbox = InMemoryOutboxStore()
        subs = InMemoryWebhookSubscriptions()
        service = WebhookService(outbox, subs)

        msg_id = service.publish("test", {"data": 1})
        assert msg_id == 0

        # Nothing should be in outbox
        assert outbox.fetch_next() is None

    def test_publish_returns_last_message_id(self) -> None:
        """Test publish returns the last created message ID."""
        outbox = InMemoryOutboxStore()
        subs = InMemoryWebhookSubscriptions()
        subs.add("test", "https://example1.com", "secret1")
        subs.add("test", "https://example2.com", "secret2")
        service = WebhookService(outbox, subs)

        msg_id = service.publish("test", {"data": 1})
        # With 2 subscribers, should return ID of last message (2)
        assert msg_id == 2

    def test_default_version(self) -> None:
        """Test default version is 1."""
        outbox = InMemoryOutboxStore()
        subs = InMemoryWebhookSubscriptions()
        subs.add("test", "https://example.com", "secret")
        service = WebhookService(outbox, subs)

        service.publish("test", {"data": 1})

        msg = outbox.fetch_next()
        assert msg is not None
        assert msg.payload["event"]["version"] == 1
