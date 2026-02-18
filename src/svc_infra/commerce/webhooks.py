"""Common webhook verification and event dispatch for commerce providers.

Provides a thin layer on top of each provider's ``verify_and_parse_webhook``
with event routing, logging, and replay support.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from svc_infra.logging import get_logger

from .provider.base import CommerceProvider
from .schemas import WebhookEventIn, WebhookEventOut

logger = get_logger(__name__)

# Type alias for event handler callbacks
EventHandler = Callable[[WebhookEventOut], Awaitable[None]]


class WebhookDispatcher:
    """Route verified webhook events to registered handlers.

    Usage::

        dispatcher = WebhookDispatcher()
        dispatcher.on("orders/create", handle_new_order)
        dispatcher.on("products/update", handle_product_update)

        # In your webhook endpoint:
        result = await dispatcher.handle(adapter, event_in)
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}
        self._catch_all: list[EventHandler] = []

    def on(self, topic: str, handler: EventHandler) -> None:
        """Register a handler for a specific webhook topic.

        Args:
            topic: The event topic (e.g. ``"orders/create"``, ``"products/update"``).
            handler: Async callable receiving a ``WebhookEventOut``.
        """
        self._handlers.setdefault(topic, []).append(handler)

    def on_any(self, handler: EventHandler) -> None:
        """Register a catch-all handler invoked for every verified event."""
        self._catch_all.append(handler)

    async def handle(self, adapter: CommerceProvider, event: WebhookEventIn) -> WebhookEventOut:
        """Verify, parse, and dispatch a webhook event.

        1. Delegates to the adapter's ``verify_and_parse_webhook``.
        2. Invokes matching topic handlers.
        3. Invokes catch-all handlers.

        Returns the parsed ``WebhookEventOut`` for caller use.

        Raises:
            RuntimeError: If signature verification fails.
        """
        parsed = await adapter.verify_and_parse_webhook(event)
        parsed.received_at = parsed.received_at or datetime.now(UTC)

        logger.info(
            "commerce.webhook.received",
            extra={
                "provider": parsed.provider,
                "topic": parsed.topic,
                "resource_id": parsed.resource_id,
                "verified": parsed.verified,
            },
        )

        # Dispatch to topic-specific handlers
        topic_handlers = self._handlers.get(parsed.topic, [])
        for handler in topic_handlers:
            try:
                await handler(parsed)
            except Exception:
                logger.exception(
                    "commerce.webhook.handler_error",
                    extra={
                        "provider": parsed.provider,
                        "topic": parsed.topic,
                        "resource_id": parsed.resource_id,
                    },
                )

        # Dispatch to catch-all handlers
        for handler in self._catch_all:
            try:
                await handler(parsed)
            except Exception:
                logger.exception(
                    "commerce.webhook.catchall_error",
                    extra={
                        "provider": parsed.provider,
                        "topic": parsed.topic,
                    },
                )

        return parsed

    async def replay(
        self,
        adapter: CommerceProvider,
        events: list[WebhookEventIn],
    ) -> list[WebhookEventOut]:
        """Re-dispatch a batch of stored events. Useful for recovery."""
        results: list[WebhookEventOut] = []
        for event in events:
            try:
                result = await self.handle(adapter, event)
                results.append(result)
            except Exception:
                logger.exception(
                    "commerce.webhook.replay_error",
                    extra={"provider": event.provider, "topic": event.topic},
                )
        return results

    @property
    def registered_topics(self) -> list[str]:
        """Return all topics with at least one handler."""
        return sorted(self._handlers)
