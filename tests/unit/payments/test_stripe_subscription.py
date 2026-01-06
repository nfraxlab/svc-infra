"""
Tests for Stripe subscription operations: create, cancel, update.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestStripeSubscriptionCreate:
    """Tests for creating Stripe subscriptions."""

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

    @pytest.fixture
    def mock_subscription(self, mocker):
        """Create a mock subscription object."""
        mock_price = mocker.Mock()
        mock_price.id = "price_test123"

        mock_item = mocker.Mock()
        mock_item.price = mock_price
        mock_item.quantity = 1

        mock_items = mocker.Mock()
        mock_items.data = [mock_item]

        sub = mocker.Mock()
        sub.id = "sub_test123"
        sub.status = "active"
        sub.cancel_at_period_end = False
        sub.current_period_end = 1704067200
        sub.items = mock_items
        return sub

    @pytest.mark.asyncio
    async def test_create_subscription_basic(
        self, mock_stripe_settings, monkeypatch, mocker, mock_subscription
    ):
        """Should create a basic subscription."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        monkeypatch.setattr(stripe_sdk.Subscription, "create", lambda **kw: mock_subscription)

        from svc_infra.apf_payments.schemas import SubscriptionCreateIn

        result = await adapter.create_subscription(
            SubscriptionCreateIn(
                customer_provider_id="cus_test",
                price_provider_id="price_test123",
                quantity=1,
            )
        )

        assert result.provider_subscription_id == "sub_test123"
        assert result.status == "active"
        assert result.provider == "stripe"

    @pytest.mark.asyncio
    async def test_create_subscription_with_trial(
        self, mock_stripe_settings, monkeypatch, mocker, mock_subscription
    ):
        """Should create subscription with trial period."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        mock_subscription.status = "trialing"
        captured_kwargs = {}

        def capture_create(**kw):
            captured_kwargs.update(kw)
            return mock_subscription

        monkeypatch.setattr(stripe_sdk.Subscription, "create", capture_create)

        from svc_infra.apf_payments.schemas import SubscriptionCreateIn

        result = await adapter.create_subscription(
            SubscriptionCreateIn(
                customer_provider_id="cus_test",
                price_provider_id="price_test",
                trial_days=14,
            )
        )

        assert result.status == "trialing"
        assert captured_kwargs.get("trial_period_days") == 14

    @pytest.mark.asyncio
    async def test_create_subscription_with_quantity(
        self, mock_stripe_settings, monkeypatch, mocker, mock_subscription
    ):
        """Should create subscription with specific quantity."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        mock_subscription.items.data[0].quantity = 5
        monkeypatch.setattr(stripe_sdk.Subscription, "create", lambda **kw: mock_subscription)

        from svc_infra.apf_payments.schemas import SubscriptionCreateIn

        result = await adapter.create_subscription(
            SubscriptionCreateIn(
                customer_provider_id="cus_test",
                price_provider_id="price_test",
                quantity=5,
            )
        )

        assert result.quantity == 5


class TestStripeSubscriptionCancel:
    """Tests for canceling Stripe subscriptions."""

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

    @pytest.fixture
    def mock_subscription(self, mocker):
        """Create a mock subscription."""
        mock_price = mocker.Mock()
        mock_price.id = "price_test"

        mock_item = mocker.Mock()
        mock_item.price = mock_price
        mock_item.quantity = 1

        mock_items = mocker.Mock()
        mock_items.data = [mock_item]

        sub = mocker.Mock()
        sub.id = "sub_cancel"
        sub.status = "active"
        sub.cancel_at_period_end = False
        sub.current_period_end = 1704067200
        sub.items = mock_items
        return sub

    @pytest.mark.asyncio
    async def test_cancel_at_period_end(
        self, mock_stripe_settings, monkeypatch, mocker, mock_subscription
    ):
        """Should cancel subscription at period end."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        mock_subscription.cancel_at_period_end = True

        monkeypatch.setattr(stripe_sdk.Subscription, "modify", lambda sid, **kw: mock_subscription)

        result = await adapter.cancel_subscription("sub_cancel", at_period_end=True)

        assert result.cancel_at_period_end is True

    @pytest.mark.asyncio
    async def test_cancel_immediately(
        self, mock_stripe_settings, monkeypatch, mocker, mock_subscription
    ):
        """Should cancel subscription immediately."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        mock_subscription.status = "canceled"

        monkeypatch.setattr(stripe_sdk.Subscription, "cancel", lambda sid: mock_subscription)

        result = await adapter.cancel_subscription("sub_cancel", at_period_end=False)

        assert result.status == "canceled"


class TestStripeSubscriptionUpdate:
    """Tests for updating Stripe subscriptions."""

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

    @pytest.fixture
    def mock_subscription(self, mocker):
        """Create a mock subscription."""
        mock_price = mocker.Mock()
        mock_price.id = "price_new"

        mock_item = mocker.Mock()
        mock_item.id = "si_item1"
        mock_item.price = mock_price
        mock_item.quantity = 2

        mock_items = mocker.Mock()
        mock_items.data = [mock_item]

        sub = mocker.Mock()
        sub.id = "sub_update"
        sub.status = "active"
        sub.cancel_at_period_end = False
        sub.current_period_end = 1704067200
        sub.items = mock_items
        return sub

    @pytest.mark.asyncio
    async def test_update_quantity(
        self, mock_stripe_settings, monkeypatch, mocker, mock_subscription
    ):
        """Should update subscription quantity."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        monkeypatch.setattr(
            stripe_sdk.Subscription, "retrieve", lambda sid, **kw: mock_subscription
        )
        monkeypatch.setattr(stripe_sdk.Subscription, "modify", lambda sid, **kw: mock_subscription)

        from svc_infra.apf_payments.schemas import SubscriptionUpdateIn

        result = await adapter.update_subscription("sub_update", SubscriptionUpdateIn(quantity=10))

        assert result.provider_subscription_id == "sub_update"


class TestStripeSubscriptionRetrieve:
    """Tests for retrieving Stripe subscriptions."""

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

    @pytest.fixture
    def mock_subscription(self, mocker):
        """Create a mock subscription."""
        mock_price = mocker.Mock()
        mock_price.id = "price_test"

        mock_item = mocker.Mock()
        mock_item.price = mock_price
        mock_item.quantity = 1

        mock_items = mocker.Mock()
        mock_items.data = [mock_item]

        sub = mocker.Mock()
        sub.id = "sub_get"
        sub.status = "active"
        sub.cancel_at_period_end = False
        sub.current_period_end = 1704067200
        sub.items = mock_items
        return sub

    @pytest.mark.asyncio
    async def test_get_subscription(
        self, mock_stripe_settings, monkeypatch, mocker, mock_subscription
    ):
        """Should retrieve subscription by ID."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        monkeypatch.setattr(
            stripe_sdk.Subscription, "retrieve", lambda sid, **kw: mock_subscription
        )

        result = await adapter.get_subscription("sub_get")

        assert result.provider_subscription_id == "sub_get"
        assert result.status == "active"
