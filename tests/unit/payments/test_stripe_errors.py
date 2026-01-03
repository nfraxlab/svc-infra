"""
Tests for Stripe API errors and network failures.

Covers various error scenarios: authentication, rate limiting,
card errors, network issues, and other API failures.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestStripeAuthenticationErrors:
    """Tests for Stripe API authentication errors."""

    @pytest.fixture
    def mock_stripe_settings(self, monkeypatch):
        """Set up mock Stripe settings."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock.return_value.stripe = mock_stripe
            yield mock

    def _skip_if_no_stripe(self):
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

    @pytest.mark.asyncio
    async def test_invalid_api_key(self, mock_stripe_settings, monkeypatch):
        """Should raise AuthenticationError for invalid API key."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        # Mock Customer.create to raise AuthenticationError
        monkeypatch.setattr(
            stripe_sdk.Customer,
            "create",
            MagicMock(side_effect=stripe_sdk.error.AuthenticationError("Invalid API key provided")),
        )

        from svc_infra.apf_payments.schemas import CustomerUpsertIn

        with pytest.raises(stripe_sdk.error.AuthenticationError):
            await adapter.ensure_customer(CustomerUpsertIn(email="test@example.com"))

    @pytest.mark.asyncio
    async def test_api_key_expired(self, mock_stripe_settings, monkeypatch):
        """Should handle expired API keys."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        monkeypatch.setattr(
            stripe_sdk.Customer,
            "create",
            MagicMock(
                side_effect=stripe_sdk.error.AuthenticationError(
                    "API key has been revoked or expired"
                )
            ),
        )

        from svc_infra.apf_payments.schemas import CustomerUpsertIn

        with pytest.raises(stripe_sdk.error.AuthenticationError):
            await adapter.ensure_customer(CustomerUpsertIn(email="test@example.com"))


class TestStripeRateLimitErrors:
    """Tests for Stripe API rate limiting."""

    @pytest.fixture
    def mock_stripe_settings(self, monkeypatch):
        """Set up mock Stripe settings."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock.return_value.stripe = mock_stripe
            yield mock

    def _skip_if_no_stripe(self):
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, mock_stripe_settings, monkeypatch):
        """Should raise RateLimitError when rate limit exceeded."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        monkeypatch.setattr(
            stripe_sdk.Customer,
            "list",
            MagicMock(
                side_effect=stripe_sdk.error.RateLimitError(
                    "Rate limit exceeded, please slow down requests"
                )
            ),
        )

        with pytest.raises(stripe_sdk.error.RateLimitError):
            await adapter.list_customers()


class TestStripeCardErrors:
    """Tests for Stripe card-related errors."""

    @pytest.fixture
    def mock_stripe_settings(self, monkeypatch):
        """Set up mock Stripe settings."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock.return_value.stripe = mock_stripe
            yield mock

    def _skip_if_no_stripe(self):
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

    @pytest.mark.asyncio
    async def test_card_declined(self, mock_stripe_settings, monkeypatch):
        """Should handle card declined error."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        # Create a CardError with proper attributes
        card_error = stripe_sdk.error.CardError(
            message="Your card was declined",
            param="card_number",
            code="card_declined",
        )
        card_error.decline_code = "generic_decline"

        monkeypatch.setattr(
            stripe_sdk.PaymentIntent,
            "create",
            MagicMock(side_effect=card_error),
        )

        from svc_infra.apf_payments.schemas import IntentCreateIn

        with pytest.raises(stripe_sdk.error.CardError):
            await adapter.create_intent(
                IntentCreateIn(amount=5000, currency="USD", customer_provider_id="cus_test")
            )

    @pytest.mark.asyncio
    async def test_insufficient_funds(self, mock_stripe_settings, monkeypatch):
        """Should handle insufficient funds error."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        card_error = stripe_sdk.error.CardError(
            message="Your card has insufficient funds",
            param="card_number",
            code="card_declined",
        )
        card_error.decline_code = "insufficient_funds"

        monkeypatch.setattr(
            stripe_sdk.PaymentIntent,
            "create",
            MagicMock(side_effect=card_error),
        )

        from svc_infra.apf_payments.schemas import IntentCreateIn

        with pytest.raises(stripe_sdk.error.CardError) as exc_info:
            await adapter.create_intent(
                IntentCreateIn(amount=5000, currency="USD", customer_provider_id="cus_test")
            )

        assert exc_info.value.decline_code == "insufficient_funds"

    @pytest.mark.asyncio
    async def test_expired_card(self, mock_stripe_settings, monkeypatch):
        """Should handle expired card error."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        card_error = stripe_sdk.error.CardError(
            message="Your card has expired",
            param="exp_month",
            code="expired_card",
        )

        monkeypatch.setattr(
            stripe_sdk.PaymentIntent,
            "create",
            MagicMock(side_effect=card_error),
        )

        from svc_infra.apf_payments.schemas import IntentCreateIn

        with pytest.raises(stripe_sdk.error.CardError):
            await adapter.create_intent(
                IntentCreateIn(amount=5000, currency="USD", customer_provider_id="cus_test")
            )


class TestStripeInvalidRequestErrors:
    """Tests for invalid request errors."""

    @pytest.fixture
    def mock_stripe_settings(self, monkeypatch):
        """Set up mock Stripe settings."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock.return_value.stripe = mock_stripe
            yield mock

    def _skip_if_no_stripe(self):
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

    @pytest.mark.asyncio
    async def test_invalid_customer_id(self, mock_stripe_settings, monkeypatch):
        """Should raise InvalidRequestError for invalid customer ID."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        monkeypatch.setattr(
            stripe_sdk.Customer,
            "retrieve",
            MagicMock(
                side_effect=stripe_sdk.error.InvalidRequestError(
                    message="No such customer: cus_invalid",
                    param="customer",
                )
            ),
        )

        with pytest.raises(stripe_sdk.error.InvalidRequestError):
            await adapter.get_customer("cus_invalid")

    @pytest.mark.asyncio
    async def test_invalid_subscription_id(self, mock_stripe_settings, monkeypatch):
        """Should raise InvalidRequestError for invalid subscription ID."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        monkeypatch.setattr(
            stripe_sdk.Subscription,
            "retrieve",
            MagicMock(
                side_effect=stripe_sdk.error.InvalidRequestError(
                    message="No such subscription: sub_invalid",
                    param="subscription",
                )
            ),
        )

        with pytest.raises(stripe_sdk.error.InvalidRequestError):
            await adapter.get_subscription("sub_invalid")

    @pytest.mark.asyncio
    async def test_missing_required_param(self, mock_stripe_settings, monkeypatch):
        """Should raise InvalidRequestError for missing required parameters."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        monkeypatch.setattr(
            stripe_sdk.Subscription,
            "create",
            MagicMock(
                side_effect=stripe_sdk.error.InvalidRequestError(
                    message="Missing required param: items",
                    param="items",
                )
            ),
        )

        from svc_infra.apf_payments.schemas import SubscriptionCreateIn

        with pytest.raises(stripe_sdk.error.InvalidRequestError):
            await adapter.create_subscription(
                SubscriptionCreateIn(customer_provider_id="cus_test", items=[])
            )


class TestStripeNetworkErrors:
    """Tests for network and connectivity errors."""

    @pytest.fixture
    def mock_stripe_settings(self, monkeypatch):
        """Set up mock Stripe settings."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock.return_value.stripe = mock_stripe
            yield mock

    def _skip_if_no_stripe(self):
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

    @pytest.mark.asyncio
    async def test_network_connection_error(self, mock_stripe_settings, monkeypatch):
        """Should handle network connection failures."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        monkeypatch.setattr(
            stripe_sdk.Customer,
            "list",
            MagicMock(
                side_effect=stripe_sdk.error.APIConnectionError(
                    "Failed to establish a connection to Stripe"
                )
            ),
        )

        with pytest.raises(stripe_sdk.error.APIConnectionError):
            await adapter.list_customers()

    @pytest.mark.asyncio
    async def test_stripe_api_error(self, mock_stripe_settings, monkeypatch):
        """Should handle Stripe API errors (5xx responses)."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        monkeypatch.setattr(
            stripe_sdk.Customer,
            "create",
            MagicMock(side_effect=stripe_sdk.error.APIError("Stripe API is currently unavailable")),
        )

        from svc_infra.apf_payments.schemas import CustomerUpsertIn

        with pytest.raises(stripe_sdk.error.APIError):
            await adapter.ensure_customer(CustomerUpsertIn(email="test@example.com"))


class TestStripeIdempotencyErrors:
    """Tests for idempotency-related errors."""

    @pytest.fixture
    def mock_stripe_settings(self, monkeypatch):
        """Set up mock Stripe settings."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock.return_value.stripe = mock_stripe
            yield mock

    def _skip_if_no_stripe(self):
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

    @pytest.mark.asyncio
    async def test_idempotency_key_in_use(self, mock_stripe_settings, monkeypatch):
        """Should handle idempotency key conflicts."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        # IdempotencyError is a subclass of InvalidRequestError in Stripe SDK
        monkeypatch.setattr(
            stripe_sdk.PaymentIntent,
            "create",
            MagicMock(
                side_effect=stripe_sdk.error.IdempotencyError(
                    "Keys for idempotent requests must be unique"
                )
            ),
        )

        from svc_infra.apf_payments.schemas import IntentCreateIn

        with pytest.raises(stripe_sdk.error.IdempotencyError):
            await adapter.create_intent(
                IntentCreateIn(
                    amount=5000,
                    currency="USD",
                    customer_provider_id="cus_test",
                    idempotency_key="dup_key_123",
                )
            )
