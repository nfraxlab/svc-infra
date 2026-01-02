"""Tests for webhooks add module - targeting uncovered paths."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI

from svc_infra.db.inbox import InMemoryInboxStore
from svc_infra.db.outbox import InMemoryOutboxStore


class TestRedisOutboxStore:
    """Tests for RedisOutboxStore class."""

    def test_enqueue_creates_message(self) -> None:
        """Test enqueue creates a message in Redis."""
        from svc_infra.webhooks.add import RedisOutboxStore

        mock_client = MagicMock()
        mock_client.incr.return_value = 1

        store = RedisOutboxStore(mock_client, prefix="test:outbox")
        msg = store.enqueue("order.created", {"order_id": 123})

        assert msg.id == 1
        assert msg.topic == "order.created"
        assert msg.payload == {"order_id": 123}
        mock_client.hset.assert_called_once()
        mock_client.rpush.assert_called_once()

    def test_enqueue_handles_non_int_incr_result(self) -> None:
        """Test enqueue handles non-integer incr result."""
        from svc_infra.webhooks.add import RedisOutboxStore

        mock_client = MagicMock()
        mock_client.incr.return_value = "not_a_number"

        store = RedisOutboxStore(mock_client)
        msg = store.enqueue("test.topic", {"key": "value"})

        # Should fallback to 0
        assert msg.id == 0

    def test_fetch_next_returns_unprocessed_message(self) -> None:
        """Test fetch_next returns unprocessed message."""
        from svc_infra.webhooks.add import RedisOutboxStore

        mock_client = MagicMock()
        mock_client.lrange.return_value = [b"1"]
        mock_client.hgetall.return_value = {
            b"id": b"1",
            b"topic": b"order.created",
            b"payload": b'{"order_id": 123}',
            b"created_at": b"2024-01-01T00:00:00+00:00",
            b"attempts": b"0",
            b"processed_at": b"",
        }

        store = RedisOutboxStore(mock_client)
        msg = store.fetch_next()

        assert msg is not None
        assert msg.topic == "order.created"
        assert msg.payload == {"order_id": 123}

    def test_fetch_next_skips_processed_messages(self) -> None:
        """Test fetch_next skips already processed messages."""
        from svc_infra.webhooks.add import RedisOutboxStore

        mock_client = MagicMock()
        mock_client.lrange.return_value = [b"1"]
        mock_client.hgetall.return_value = {
            b"id": b"1",
            b"topic": b"order.created",
            b"payload": b"{}",
            b"created_at": b"2024-01-01T00:00:00+00:00",
            b"attempts": b"0",
            b"processed_at": b"2024-01-01T01:00:00+00:00",
        }

        store = RedisOutboxStore(mock_client)
        msg = store.fetch_next()

        assert msg is None

    def test_fetch_next_skips_retried_messages(self) -> None:
        """Test fetch_next skips messages with attempts > 0."""
        from svc_infra.webhooks.add import RedisOutboxStore

        mock_client = MagicMock()
        mock_client.lrange.return_value = [b"1"]
        mock_client.hgetall.return_value = {
            b"id": b"1",
            b"topic": b"order.created",
            b"payload": b"{}",
            b"created_at": b"",
            b"attempts": b"1",
            b"processed_at": b"",
        }

        store = RedisOutboxStore(mock_client)
        msg = store.fetch_next()

        assert msg is None

    def test_fetch_next_filters_by_topics(self) -> None:
        """Test fetch_next filters by allowed topics."""
        from svc_infra.webhooks.add import RedisOutboxStore

        mock_client = MagicMock()
        mock_client.lrange.return_value = [b"1"]
        mock_client.hgetall.return_value = {
            b"id": b"1",
            b"topic": b"order.created",
            b"payload": b"{}",
            b"created_at": b"",
            b"attempts": b"0",
            b"processed_at": b"",
        }

        store = RedisOutboxStore(mock_client)
        # Request only user.created topic
        msg = store.fetch_next(topics=["user.created"])

        assert msg is None

    def test_fetch_next_returns_none_for_empty_queue(self) -> None:
        """Test fetch_next returns None for empty queue."""
        from svc_infra.webhooks.add import RedisOutboxStore

        mock_client = MagicMock()
        mock_client.lrange.return_value = []

        store = RedisOutboxStore(mock_client)
        msg = store.fetch_next()

        assert msg is None

    def test_fetch_next_skips_missing_messages(self) -> None:
        """Test fetch_next skips messages that don't exist."""
        from svc_infra.webhooks.add import RedisOutboxStore

        mock_client = MagicMock()
        mock_client.lrange.return_value = [b"1"]
        mock_client.hgetall.return_value = {}

        store = RedisOutboxStore(mock_client)
        msg = store.fetch_next()

        assert msg is None

    def test_fetch_next_skips_messages_without_topic(self) -> None:
        """Test fetch_next skips messages without topic."""
        from svc_infra.webhooks.add import RedisOutboxStore

        mock_client = MagicMock()
        mock_client.lrange.return_value = [b"1"]
        mock_client.hgetall.return_value = {
            b"id": b"1",
            b"payload": b"{}",
        }

        store = RedisOutboxStore(mock_client)
        msg = store.fetch_next()

        assert msg is None

    def test_mark_processed_updates_message(self) -> None:
        """Test mark_processed updates message in Redis."""
        from svc_infra.webhooks.add import RedisOutboxStore

        mock_client = MagicMock()
        mock_client.exists.return_value = True

        store = RedisOutboxStore(mock_client)
        store.mark_processed(1)

        mock_client.hset.assert_called_once()
        call_args = mock_client.hset.call_args
        assert "processed_at" in call_args[0]

    def test_mark_processed_skips_nonexistent_message(self) -> None:
        """Test mark_processed skips nonexistent message."""
        from svc_infra.webhooks.add import RedisOutboxStore

        mock_client = MagicMock()
        mock_client.exists.return_value = False

        store = RedisOutboxStore(mock_client)
        store.mark_processed(999)

        mock_client.hset.assert_not_called()

    def test_mark_failed_increments_attempts(self) -> None:
        """Test mark_failed increments attempts counter."""
        from svc_infra.webhooks.add import RedisOutboxStore

        mock_client = MagicMock()

        store = RedisOutboxStore(mock_client)
        store.mark_failed(1)

        mock_client.hincrby.assert_called_once_with("webhooks:outbox:msg:1", "attempts", 1)


class TestRedisInboxStore:
    """Tests for RedisInboxStore class."""

    def test_mark_if_new_returns_true_for_new_key(self) -> None:
        """Test mark_if_new returns True for new key."""
        from svc_infra.webhooks.add import RedisInboxStore

        mock_client = MagicMock()
        mock_client.set.return_value = True

        store = RedisInboxStore(mock_client, prefix="test:inbox")
        result = store.mark_if_new("key123")

        assert result is True
        mock_client.set.assert_called_once()

    def test_mark_if_new_returns_false_for_existing_key(self) -> None:
        """Test mark_if_new returns False for existing key."""
        from svc_infra.webhooks.add import RedisInboxStore

        mock_client = MagicMock()
        mock_client.set.return_value = False

        store = RedisInboxStore(mock_client)
        result = store.mark_if_new("key123")

        assert result is False

    def test_purge_expired_returns_zero(self) -> None:
        """Test purge_expired returns 0 (Redis handles expiration)."""
        from svc_infra.webhooks.add import RedisInboxStore

        mock_client = MagicMock()

        store = RedisInboxStore(mock_client)
        result = store.purge_expired()

        assert result == 0

    def test_is_marked_returns_true_for_existing_key(self) -> None:
        """Test is_marked returns True for existing key."""
        from svc_infra.webhooks.add import RedisInboxStore

        mock_client = MagicMock()
        mock_client.exists.return_value = 1

        store = RedisInboxStore(mock_client)
        result = store.is_marked("key123")

        assert result is True

    def test_is_marked_returns_false_for_missing_key(self) -> None:
        """Test is_marked returns False for missing key."""
        from svc_infra.webhooks.add import RedisInboxStore

        mock_client = MagicMock()
        mock_client.exists.return_value = 0

        store = RedisInboxStore(mock_client)
        result = store.is_marked("key123")

        assert result is False


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_is_factory_returns_true_for_callable(self) -> None:
        """Test _is_factory returns True for callable."""
        from svc_infra.webhooks.add import _is_factory

        def my_factory():
            return "value"

        assert _is_factory(my_factory) is True

    def test_is_factory_returns_false_for_string(self) -> None:
        """Test _is_factory returns False for string."""
        from svc_infra.webhooks.add import _is_factory

        assert _is_factory("not a factory") is False

    def test_is_factory_returns_false_for_bytes(self) -> None:
        """Test _is_factory returns False for bytes."""
        from svc_infra.webhooks.add import _is_factory

        assert _is_factory(b"not a factory") is False

    def test_resolve_value_uses_default_when_none(self) -> None:
        """Test _resolve_value uses default factory when value is None."""
        from svc_infra.webhooks.add import _resolve_value

        result = _resolve_value(None, lambda: "default")
        assert result == "default"

    def test_resolve_value_calls_factory(self) -> None:
        """Test _resolve_value calls factory when value is callable."""
        from svc_infra.webhooks.add import _resolve_value

        result = _resolve_value(lambda: "from_factory", lambda: "default")
        assert result == "from_factory"

    def test_resolve_value_returns_value_directly(self) -> None:
        """Test _resolve_value returns value directly when not callable."""
        from svc_infra.webhooks.add import _resolve_value

        store = InMemoryOutboxStore()
        result = _resolve_value(store, lambda: InMemoryOutboxStore())
        assert result is store


class TestDefaultStoreFactories:
    """Tests for default store factory functions."""

    def test_default_outbox_returns_memory_store(self) -> None:
        """Test _default_outbox returns in-memory store by default."""
        from svc_infra.webhooks.add import _default_outbox

        result = _default_outbox({})
        assert isinstance(result, InMemoryOutboxStore)

    def test_default_outbox_returns_redis_store_when_configured(self) -> None:
        """Test _default_outbox returns Redis store when configured."""
        from svc_infra.webhooks.add import RedisOutboxStore, _default_outbox

        with patch("svc_infra.webhooks.add._build_redis_client") as mock_build:
            mock_build.return_value = MagicMock()

            result = _default_outbox({"WEBHOOKS_OUTBOX": "redis"})

            assert isinstance(result, RedisOutboxStore)

    def test_default_outbox_falls_back_when_redis_unavailable(self) -> None:
        """Test _default_outbox falls back when Redis unavailable."""
        from svc_infra.webhooks.add import _default_outbox

        with patch("svc_infra.webhooks.add._build_redis_client") as mock_build:
            mock_build.return_value = None

            result = _default_outbox({"WEBHOOKS_OUTBOX": "redis"})

            assert isinstance(result, InMemoryOutboxStore)

    def test_default_inbox_returns_memory_store(self) -> None:
        """Test _default_inbox returns in-memory store by default."""
        from svc_infra.webhooks.add import _default_inbox

        result = _default_inbox({})
        assert isinstance(result, InMemoryInboxStore)

    def test_default_inbox_returns_redis_store_when_configured(self) -> None:
        """Test _default_inbox returns Redis store when configured."""
        from svc_infra.webhooks.add import RedisInboxStore, _default_inbox

        with patch("svc_infra.webhooks.add._build_redis_client") as mock_build:
            mock_build.return_value = MagicMock()

            result = _default_inbox({"WEBHOOKS_INBOX": "redis"})

            assert isinstance(result, RedisInboxStore)


class TestBuildRedisClient:
    """Tests for _build_redis_client function."""

    def test_build_redis_client_returns_none_when_redis_not_installed(self) -> None:
        """Test _build_redis_client returns None when redis not installed."""
        from svc_infra.webhooks import add

        original_redis = add.Redis
        add.Redis = None

        try:
            result = add._build_redis_client({})
            assert result is None
        finally:
            add.Redis = original_redis

    def test_build_redis_client_uses_default_url(self) -> None:
        """Test _build_redis_client uses default URL."""
        from svc_infra.webhooks.add import _build_redis_client

        with patch("svc_infra.webhooks.add.Redis") as mock_redis:
            mock_redis.from_url.return_value = MagicMock()

            result = _build_redis_client({})

            mock_redis.from_url.assert_called_once_with("redis://localhost:6379/0")
            assert result is not None

    def test_build_redis_client_uses_env_url(self) -> None:
        """Test _build_redis_client uses URL from environment."""
        from svc_infra.webhooks.add import _build_redis_client

        with patch("svc_infra.webhooks.add.Redis") as mock_redis:
            mock_redis.from_url.return_value = MagicMock()

            _build_redis_client({"REDIS_URL": "redis://custom:6380/1"})

            mock_redis.from_url.assert_called_once_with("redis://custom:6380/1")


class TestSubscriptionLookup:
    """Tests for subscription lookup functions."""

    def test_subscription_lookup_returns_url(self) -> None:
        """Test _subscription_lookup returns correct URL."""
        from svc_infra.webhooks.add import _subscription_lookup
        from svc_infra.webhooks.service import InMemoryWebhookSubscriptions

        subs = InMemoryWebhookSubscriptions()
        subs.add("order.created", "https://example.com/webhook", "secret123")

        get_url, get_secret = _subscription_lookup(subs)

        assert get_url("order.created") == "https://example.com/webhook"
        assert get_secret("order.created") == "secret123"

    def test_subscription_lookup_raises_for_missing_topic(self) -> None:
        """Test _subscription_lookup raises for missing topic."""
        from svc_infra.webhooks.add import _subscription_lookup
        from svc_infra.webhooks.service import InMemoryWebhookSubscriptions

        subs = InMemoryWebhookSubscriptions()
        get_url, get_secret = _subscription_lookup(subs)

        with pytest.raises(LookupError, match="No webhook subscription"):
            get_url("missing.topic")

        with pytest.raises(LookupError, match="No webhook subscription"):
            get_secret("missing.topic")


class TestAddWebhooksIntegration:
    """Integration tests for add_webhooks function."""

    def test_add_webhooks_without_queue_logs_warning(self) -> None:
        """Test add_webhooks logs warning when scheduler provided without queue."""
        from svc_infra.jobs.scheduler import InMemoryScheduler
        from svc_infra.webhooks.add import add_webhooks

        app = FastAPI()
        scheduler = InMemoryScheduler()

        with patch("svc_infra.webhooks.add.logger") as mock_logger:
            add_webhooks(app, scheduler=scheduler, queue=None)

            mock_logger.warning.assert_called()

    def test_add_webhooks_with_custom_env(self) -> None:
        """Test add_webhooks uses custom env mapping."""
        from svc_infra.webhooks.add import add_webhooks

        app = FastAPI()
        custom_env = {"WEBHOOKS_OUTBOX": "memory"}

        add_webhooks(app, env=custom_env)

        assert hasattr(app.state, "webhooks_outbox")

    def test_add_webhooks_with_factory_functions(self) -> None:
        """Test add_webhooks accepts factory functions."""
        from svc_infra.webhooks.add import add_webhooks

        app = FastAPI()

        def outbox_factory() -> InMemoryOutboxStore:
            return InMemoryOutboxStore()

        def inbox_factory() -> InMemoryInboxStore:
            return InMemoryInboxStore()

        add_webhooks(app, outbox=outbox_factory, inbox=inbox_factory)

        assert isinstance(app.state.webhooks_outbox, InMemoryOutboxStore)
        assert isinstance(app.state.webhooks_inbox, InMemoryInboxStore)

    def test_add_webhooks_schedule_tick_false(self) -> None:
        """Test add_webhooks with schedule_tick=False."""
        from svc_infra.jobs.queue import InMemoryJobQueue
        from svc_infra.jobs.scheduler import InMemoryScheduler
        from svc_infra.webhooks.add import add_webhooks

        app = FastAPI()
        queue = InMemoryJobQueue()
        scheduler = InMemoryScheduler()

        add_webhooks(app, queue=queue, scheduler=scheduler, schedule_tick=False)

        # Tick should NOT be scheduled
        assert "webhooks.outbox" not in scheduler._tasks
        # But handler should still be registered
        assert hasattr(app.state, "webhooks_delivery_handler")
