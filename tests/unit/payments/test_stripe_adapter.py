"""Tests for svc_infra.apf_payments.provider.stripe module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestStripeAdapterInit:
    """Tests for StripeAdapter initialization."""

    def test_raises_without_settings(self, monkeypatch) -> None:
        """Should raise RuntimeError if Stripe settings not configured."""
        monkeypatch.delenv("STRIPE_SECRET", raising=False)

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock_settings:
            mock_settings.return_value.stripe = None

            with pytest.raises(RuntimeError) as exc_info:
                from svc_infra.apf_payments.provider.stripe import StripeAdapter

                StripeAdapter()

            assert "Stripe settings not configured" in str(exc_info.value)

    def test_initializes_with_valid_settings(self, monkeypatch, mocker) -> None:
        """Should initialize with valid Stripe settings."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")

        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock_settings:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock_settings.return_value.stripe = mock_stripe

            from svc_infra.apf_payments.provider.stripe import StripeAdapter

            adapter = StripeAdapter()
            assert adapter.name == "stripe"


class TestStripeCustomers:
    """Tests for Stripe customer operations."""

    @pytest.mark.asyncio
    async def test_ensure_customer_creates_new(self, monkeypatch, mocker) -> None:
        """Should create new customer when email not found."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock_settings:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock_settings.return_value.stripe = mock_stripe

            adapter = StripeAdapter()

        mock_list_result = mocker.Mock()
        mock_list_result.data = []

        mock_customer = mocker.Mock()
        mock_customer.id = "cus_new123"
        mock_customer.get = lambda k: {"email": "new@example.com", "name": "New User"}.get(k)

        monkeypatch.setattr(stripe_sdk.Customer, "list", lambda **kw: mock_list_result)
        monkeypatch.setattr(stripe_sdk.Customer, "create", lambda **kw: mock_customer)

        from svc_infra.apf_payments.schemas import CustomerUpsertIn

        result = await adapter.ensure_customer(
            CustomerUpsertIn(email="new@example.com", name="New User", user_id="user-1")
        )

        assert result.provider_customer_id == "cus_new123"
        assert result.provider == "stripe"

    @pytest.mark.asyncio
    async def test_ensure_customer_finds_existing(self, monkeypatch, mocker) -> None:
        """Should return existing customer when email found."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock_settings:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock_settings.return_value.stripe = mock_stripe

            adapter = StripeAdapter()

        mock_customer = mocker.Mock()
        mock_customer.id = "cus_existing123"
        mock_customer.get = lambda k: {"email": "existing@example.com", "name": "Existing"}.get(k)

        mock_list_result = mocker.Mock()
        mock_list_result.data = [mock_customer]

        monkeypatch.setattr(stripe_sdk.Customer, "list", lambda **kw: mock_list_result)

        from svc_infra.apf_payments.schemas import CustomerUpsertIn

        result = await adapter.ensure_customer(CustomerUpsertIn(email="existing@example.com"))

        assert result.provider_customer_id == "cus_existing123"


class TestStripePaymentMethods:
    """Tests for Stripe payment method operations."""

    @pytest.mark.asyncio
    async def test_attach_payment_method(self, monkeypatch, mocker) -> None:
        """Should attach payment method to customer."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock_settings:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock_settings.return_value.stripe = mock_stripe

            adapter = StripeAdapter()

        mock_pm = mocker.Mock()
        mock_pm.id = "pm_123"
        mock_pm.customer = "cus_123"
        mock_pm.card = {"brand": "visa", "last4": "4242", "exp_month": 12, "exp_year": 2025}

        mock_customer = mocker.Mock()
        mock_customer.invoice_settings = mocker.Mock()
        mock_customer.invoice_settings.default_payment_method = "pm_123"

        monkeypatch.setattr(stripe_sdk.PaymentMethod, "attach", lambda pm_id, **kw: mock_pm)
        monkeypatch.setattr(stripe_sdk.Customer, "modify", lambda cust_id, **kw: mock_customer)

        from svc_infra.apf_payments.schemas import PaymentMethodAttachIn

        result = await adapter.attach_payment_method(
            PaymentMethodAttachIn(
                customer_provider_id="cus_123",
                payment_method_token="pm_123",
                make_default=True,
            )
        )

        assert result.provider_method_id == "pm_123"
        assert result.brand == "visa"
        assert result.last4 == "4242"

    @pytest.mark.asyncio
    async def test_list_payment_methods(self, monkeypatch, mocker) -> None:
        """Should list customer payment methods."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock_settings:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock_settings.return_value.stripe = mock_stripe

            adapter = StripeAdapter()

        mock_pm = mocker.Mock()
        mock_pm.id = "pm_123"
        mock_pm.customer = "cus_123"
        mock_pm.card = {"brand": "mastercard", "last4": "5555"}

        mock_customer = mocker.Mock()
        mock_customer.invoice_settings = mocker.Mock()
        mock_customer.invoice_settings.default_payment_method = "pm_123"

        mock_list_result = mocker.Mock()
        mock_list_result.data = [mock_pm]

        monkeypatch.setattr(stripe_sdk.Customer, "retrieve", lambda cust_id: mock_customer)
        monkeypatch.setattr(stripe_sdk.PaymentMethod, "list", lambda **kw: mock_list_result)

        result = await adapter.list_payment_methods("cus_123")

        assert len(result) == 1
        assert result[0].brand == "mastercard"


class TestStripeIntents:
    """Tests for Stripe payment intent operations."""

    @pytest.mark.asyncio
    async def test_create_intent(self, monkeypatch, mocker) -> None:
        """Should create payment intent."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock_settings:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock_settings.return_value.stripe = mock_stripe

            adapter = StripeAdapter()

        mock_pi = mocker.Mock()
        mock_pi.id = "pi_123"
        mock_pi.status = "requires_payment_method"
        mock_pi.amount = 5000
        mock_pi.currency = "usd"
        mock_pi.client_secret = "pi_123_secret"
        mock_pi.next_action = None

        monkeypatch.setattr(stripe_sdk.PaymentIntent, "create", lambda **kw: mock_pi)

        from svc_infra.apf_payments.schemas import IntentCreateIn

        result = await adapter.create_intent(
            IntentCreateIn(amount=5000, currency="USD"),
            user_id="user-1",
        )

        assert result.provider_intent_id == "pi_123"
        assert result.amount == 5000
        assert result.currency == "USD"

    @pytest.mark.asyncio
    async def test_confirm_intent(self, monkeypatch, mocker) -> None:
        """Should confirm payment intent."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock_settings:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock_settings.return_value.stripe = mock_stripe

            adapter = StripeAdapter()

        mock_pi = mocker.Mock()
        mock_pi.id = "pi_123"
        mock_pi.status = "succeeded"
        mock_pi.amount = 5000
        mock_pi.currency = "usd"
        mock_pi.client_secret = "pi_123_secret"
        mock_pi.next_action = None

        monkeypatch.setattr(stripe_sdk.PaymentIntent, "confirm", lambda pi_id: mock_pi)

        result = await adapter.confirm_intent("pi_123")

        assert result.status == "succeeded"

    @pytest.mark.asyncio
    async def test_cancel_intent(self, monkeypatch, mocker) -> None:
        """Should cancel payment intent."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock_settings:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock_settings.return_value.stripe = mock_stripe

            adapter = StripeAdapter()

        mock_pi = mocker.Mock()
        mock_pi.id = "pi_123"
        mock_pi.status = "canceled"
        mock_pi.amount = 5000
        mock_pi.currency = "usd"
        mock_pi.client_secret = None
        mock_pi.next_action = None

        monkeypatch.setattr(stripe_sdk.PaymentIntent, "cancel", lambda pi_id: mock_pi)

        result = await adapter.cancel_intent("pi_123")

        assert result.status == "canceled"


class TestStripeRefunds:
    """Tests for Stripe refund operations."""

    @pytest.mark.asyncio
    async def test_refund_full(self, monkeypatch, mocker) -> None:
        """Should process full refund."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock_settings:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock_settings.return_value.stripe = mock_stripe

            adapter = StripeAdapter()

        # Mock PaymentIntent with latest_charge
        mock_charge = mocker.Mock()
        mock_charge.id = "ch_123"

        mock_pi = mocker.Mock()
        mock_pi.id = "pi_123"
        mock_pi.status = "succeeded"
        mock_pi.amount = 5000
        mock_pi.currency = "usd"
        mock_pi.client_secret = "secret_123"
        mock_pi.latest_charge = mock_charge
        mock_pi.next_action = None
        mock_pi.payment_method = None
        mock_pi.get = lambda k, d=None: None

        mock_refund = mocker.Mock()
        mock_refund.id = "re_123"

        monkeypatch.setattr(stripe_sdk.PaymentIntent, "retrieve", lambda pid, **kw: mock_pi)
        monkeypatch.setattr(stripe_sdk.Refund, "create", lambda **kw: mock_refund)

        from svc_infra.apf_payments.schemas import RefundIn

        result = await adapter.refund("pi_123", RefundIn())

        assert result.provider_intent_id == "pi_123"
        assert result.status == "succeeded"

    @pytest.mark.asyncio
    async def test_refund_partial(self, monkeypatch, mocker) -> None:
        """Should process partial refund."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock_settings:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock_settings.return_value.stripe = mock_stripe

            adapter = StripeAdapter()

        # Mock PaymentIntent with latest_charge
        mock_charge = mocker.Mock()
        mock_charge.id = "ch_123"

        mock_pi = mocker.Mock()
        mock_pi.id = "pi_123"
        mock_pi.status = "succeeded"
        mock_pi.amount = 5000
        mock_pi.currency = "usd"
        mock_pi.client_secret = "secret_123"
        mock_pi.latest_charge = mock_charge
        mock_pi.next_action = None
        mock_pi.payment_method = None
        mock_pi.get = lambda k, d=None: None

        mock_refund = mocker.Mock()
        mock_refund.id = "re_456"

        monkeypatch.setattr(stripe_sdk.PaymentIntent, "retrieve", lambda pid, **kw: mock_pi)
        monkeypatch.setattr(stripe_sdk.Refund, "create", lambda **kw: mock_refund)

        from svc_infra.apf_payments.schemas import RefundIn

        result = await adapter.refund(
            "pi_123", RefundIn(amount=2500, reason="requested_by_customer")
        )

        assert result.provider_intent_id == "pi_123"
        assert result.status == "succeeded"


class TestStripeWebhooks:
    """Tests for Stripe webhook handling."""

    @pytest.mark.asyncio
    async def test_verify_webhook_valid(self, monkeypatch, mocker) -> None:
        """Should verify valid webhook signature."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")
        monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test123")

        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock_settings:
            mock_stripe_settings = MagicMock()
            mock_stripe_settings.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe_settings.webhook_secret.get_secret_value.return_value = "whsec_test123"
            mock_settings.return_value.stripe = mock_stripe_settings

            adapter = StripeAdapter()

        mock_event = mocker.Mock()
        mock_event.id = "evt_123"
        mock_event.type = "payment_intent.succeeded"
        mock_event.data.object = {"id": "pi_123"}

        monkeypatch.setattr(
            stripe_sdk.Webhook, "construct_event", lambda payload, sig_header, secret: mock_event
        )

        result = await adapter.verify_and_parse_webhook("sig_header", b'{"test": true}')

        assert result["type"] == "payment_intent.succeeded"


class TestStripeSubscriptions:
    """Tests for Stripe subscription operations."""

    @pytest.mark.asyncio
    async def test_create_subscription(self, monkeypatch, mocker) -> None:
        """Should create subscription."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock_settings:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock_settings.return_value.stripe = mock_stripe

            adapter = StripeAdapter()

        mock_item = mocker.Mock()
        mock_item.price = mocker.Mock(id="price_123")
        mock_item.quantity = 1

        mock_sub = mocker.Mock()
        mock_sub.id = "sub_123"
        mock_sub.status = "active"
        mock_sub.cancel_at_period_end = False
        mock_sub.current_period_end = 1704067200
        mock_sub.items = mocker.Mock(data=[mock_item])

        monkeypatch.setattr(stripe_sdk.Subscription, "create", lambda **kw: mock_sub)

        from svc_infra.apf_payments.schemas import SubscriptionCreateIn

        result = await adapter.create_subscription(
            SubscriptionCreateIn(
                customer_provider_id="cus_123",
                price_provider_id="price_123",
            )
        )

        assert result.provider_subscription_id == "sub_123"
        assert result.status == "active"

    @pytest.mark.asyncio
    async def test_cancel_subscription(self, monkeypatch, mocker) -> None:
        """Should cancel subscription at period end."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock_settings:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock_settings.return_value.stripe = mock_stripe

            adapter = StripeAdapter()

        mock_item = mocker.Mock()
        mock_item.price = mocker.Mock(id="price_123")
        mock_item.quantity = 1

        mock_sub = mocker.Mock()
        mock_sub.id = "sub_123"
        mock_sub.status = "active"
        mock_sub.cancel_at_period_end = True
        mock_sub.current_period_end = 1704067200
        mock_sub.items = mocker.Mock(data=[mock_item])

        monkeypatch.setattr(stripe_sdk.Subscription, "modify", lambda sub_id, **kw: mock_sub)

        result = await adapter.cancel_subscription("sub_123", at_period_end=True)

        assert result.cancel_at_period_end is True


class TestStripeInvoices:
    """Tests for Stripe invoice operations."""

    @pytest.mark.asyncio
    async def test_create_invoice(self, monkeypatch, mocker) -> None:
        """Should create invoice."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock_settings:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock_settings.return_value.stripe = mock_stripe

            adapter = StripeAdapter()

        mock_inv = mocker.Mock()
        mock_inv.id = "in_123"
        mock_inv.customer = "cus_123"
        mock_inv.status = "draft"
        mock_inv.amount_due = 5000
        mock_inv.currency = "usd"
        mock_inv.hosted_invoice_url = "https://invoice.stripe.com/i/..."
        mock_inv.invoice_pdf = None

        monkeypatch.setattr(stripe_sdk.Invoice, "create", lambda **kw: mock_inv)

        from svc_infra.apf_payments.schemas import InvoiceCreateIn

        result = await adapter.create_invoice(InvoiceCreateIn(customer_provider_id="cus_123"))

        assert result.provider_invoice_id == "in_123"
        assert result.status == "draft"

    @pytest.mark.asyncio
    async def test_finalize_invoice(self, monkeypatch, mocker) -> None:
        """Should finalize invoice."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock_settings:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock_settings.return_value.stripe = mock_stripe

            adapter = StripeAdapter()

        mock_inv = mocker.Mock()
        mock_inv.id = "in_123"
        mock_inv.customer = "cus_123"
        mock_inv.status = "open"
        mock_inv.amount_due = 5000
        mock_inv.currency = "usd"
        mock_inv.hosted_invoice_url = "https://invoice.stripe.com/i/..."
        mock_inv.invoice_pdf = "https://invoice.stripe.com/pdf/..."

        monkeypatch.setattr(stripe_sdk.Invoice, "finalize_invoice", lambda inv_id: mock_inv)

        result = await adapter.finalize_invoice("in_123")

        assert result.status == "open"

    @pytest.mark.asyncio
    async def test_pay_invoice(self, monkeypatch, mocker) -> None:
        """Should pay invoice."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock_settings:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None
            mock_settings.return_value.stripe = mock_stripe

            adapter = StripeAdapter()

        mock_inv = mocker.Mock()
        mock_inv.id = "in_123"
        mock_inv.customer = "cus_123"
        mock_inv.status = "paid"
        mock_inv.amount_due = 0
        mock_inv.currency = "usd"
        mock_inv.hosted_invoice_url = "https://invoice.stripe.com/i/..."
        mock_inv.invoice_pdf = "https://invoice.stripe.com/pdf/..."

        monkeypatch.setattr(stripe_sdk.Invoice, "pay", lambda inv_id: mock_inv)

        result = await adapter.pay_invoice("in_123")

        assert result.status == "paid"
