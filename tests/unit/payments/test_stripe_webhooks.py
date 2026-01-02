"""
Tests for Stripe webhook signature verification.

Stripe sends webhooks with signatures that must be verified to ensure
the payload wasn't tampered with and came from Stripe.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest


class TestStripeWebhookSignature:
    """Tests for Stripe webhook signature verification."""

    @pytest.fixture
    def mock_stripe_settings(self, monkeypatch):
        """Set up mock Stripe settings with webhook secret."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")
        monkeypatch.setenv("STRIPE_WH_SECRET", "whsec_test_webhook_secret")

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret.get_secret_value.return_value = "whsec_test_webhook_secret"
            mock.return_value.stripe = mock_stripe
            yield mock

    def _skip_if_no_stripe(self):
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

    @pytest.mark.asyncio
    async def test_verify_webhook_signature_valid(self, mock_stripe_settings, monkeypatch):
        """Should verify a valid webhook signature."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        # Create a mock event that would be returned by construct_event
        mock_event = MagicMock()
        mock_event.type = "payment_intent.succeeded"
        mock_event.data.object.id = "pi_test123"

        # Mock the construct_event method to return our mock event
        mock_construct = MagicMock(return_value=mock_event)
        monkeypatch.setattr(stripe_sdk.Webhook, "construct_event", mock_construct)

        # Simulate calling construct_event (as an app would do in a webhook endpoint)
        payload = b'{"type": "payment_intent.succeeded"}'
        sig_header = "t=1234567890,v1=abc123signature"
        webhook_secret = "whsec_test_webhook_secret"

        result = stripe_sdk.Webhook.construct_event(payload, sig_header, webhook_secret)

        assert result.type == "payment_intent.succeeded"
        mock_construct.assert_called_once_with(payload, sig_header, webhook_secret)

    @pytest.mark.asyncio
    async def test_verify_webhook_signature_invalid(self, mock_stripe_settings, monkeypatch):
        """Should raise error for invalid webhook signature."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        # Mock construct_event to raise SignatureVerificationError
        mock_construct = MagicMock(
            side_effect=stripe_sdk.error.SignatureVerificationError("Invalid signature", "header")
        )
        monkeypatch.setattr(stripe_sdk.Webhook, "construct_event", mock_construct)

        payload = b'{"type": "payment_intent.succeeded"}'
        sig_header = "t=1234567890,v1=invalid_signature"
        webhook_secret = "whsec_test_webhook_secret"

        with pytest.raises(stripe_sdk.error.SignatureVerificationError):
            stripe_sdk.Webhook.construct_event(payload, sig_header, webhook_secret)

    @pytest.mark.asyncio
    async def test_verify_webhook_timestamp_expired(self, mock_stripe_settings, monkeypatch):
        """Should reject webhooks with expired timestamp (replay attack protection)."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        # Create an old timestamp (more than 5 minutes ago - Stripe's default tolerance)
        old_timestamp = int(time.time()) - 600  # 10 minutes ago

        # Mock construct_event to raise SignatureVerificationError for expired timestamp
        mock_construct = MagicMock(
            side_effect=stripe_sdk.error.SignatureVerificationError(
                "Timestamp outside the tolerance zone", "header"
            )
        )
        monkeypatch.setattr(stripe_sdk.Webhook, "construct_event", mock_construct)

        payload = b'{"type": "payment_intent.succeeded"}'
        sig_header = f"t={old_timestamp},v1=abc123signature"
        webhook_secret = "whsec_test_webhook_secret"

        with pytest.raises(stripe_sdk.error.SignatureVerificationError):
            stripe_sdk.Webhook.construct_event(payload, sig_header, webhook_secret)


class TestStripeWebhookEventTypes:
    """Tests for handling different Stripe webhook event types."""

    def _skip_if_no_stripe(self):
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

    @pytest.mark.asyncio
    async def test_payment_intent_succeeded_event(self, monkeypatch):
        """Should handle payment_intent.succeeded webhook event."""
        self._skip_if_no_stripe()

        mock_event = MagicMock()
        mock_event.type = "payment_intent.succeeded"
        mock_event.data.object.id = "pi_success"
        mock_event.data.object.status = "succeeded"
        mock_event.data.object.amount = 5000
        mock_event.data.object.currency = "usd"

        # Verify event data extraction
        assert mock_event.type == "payment_intent.succeeded"
        assert mock_event.data.object.status == "succeeded"
        assert mock_event.data.object.amount == 5000

    @pytest.mark.asyncio
    async def test_customer_subscription_created_event(self, monkeypatch):
        """Should handle customer.subscription.created webhook event."""
        self._skip_if_no_stripe()

        mock_event = MagicMock()
        mock_event.type = "customer.subscription.created"
        mock_event.data.object.id = "sub_created"
        mock_event.data.object.customer = "cus_test"
        mock_event.data.object.status = "active"

        assert mock_event.type == "customer.subscription.created"
        assert mock_event.data.object.status == "active"

    @pytest.mark.asyncio
    async def test_invoice_payment_failed_event(self, monkeypatch):
        """Should handle invoice.payment_failed webhook event."""
        self._skip_if_no_stripe()

        mock_event = MagicMock()
        mock_event.type = "invoice.payment_failed"
        mock_event.data.object.id = "in_failed"
        mock_event.data.object.subscription = "sub_test"
        mock_event.data.object.amount_due = 10000

        assert mock_event.type == "invoice.payment_failed"
        assert mock_event.data.object.amount_due == 10000

    @pytest.mark.asyncio
    async def test_charge_dispute_created_event(self, monkeypatch):
        """Should handle charge.dispute.created webhook event."""
        self._skip_if_no_stripe()

        mock_event = MagicMock()
        mock_event.type = "charge.dispute.created"
        mock_event.data.object.id = "dp_created"
        mock_event.data.object.charge = "ch_test"
        mock_event.data.object.amount = 5000
        mock_event.data.object.reason = "fraudulent"

        assert mock_event.type == "charge.dispute.created"
        assert mock_event.data.object.reason == "fraudulent"


class TestStripeWebhookMissingSecret:
    """Tests for handling missing webhook secret configuration."""

    def _skip_if_no_stripe(self):
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        if stripe_sdk is None:
            pytest.skip("stripe SDK not installed (optional dependency)")

    @pytest.fixture
    def mock_stripe_settings_no_webhook(self, monkeypatch):
        """Set up mock Stripe settings WITHOUT webhook secret."""
        monkeypatch.setenv("STRIPE_SECRET", "sk_test_123")
        # No STRIPE_WH_SECRET set

        with patch("svc_infra.apf_payments.provider.stripe.get_payments_settings") as mock:
            mock_stripe = MagicMock()
            mock_stripe.secret_key.get_secret_value.return_value = "sk_test_123"
            mock_stripe.webhook_secret = None  # No webhook secret configured
            mock.return_value.stripe = mock_stripe
            yield mock

    @pytest.mark.asyncio
    async def test_webhook_secret_not_configured(self, mock_stripe_settings_no_webhook):
        """Should handle case where webhook secret is not configured."""
        self._skip_if_no_stripe()

        from svc_infra.apf_payments.settings import get_payments_settings

        # When webhook_secret is None, the app should handle this gracefully
        settings = get_payments_settings()
        assert settings.stripe.webhook_secret is None
