"""
Tests for payment error handling scenarios.

Covers: provider errors, validation errors, database errors.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


class TestPaymentProviderErrors:
    """Tests for handling payment provider errors."""

    @pytest.fixture
    def mock_session(self, mocker):
        """Create a mock async session."""
        session = mocker.Mock()
        session.add = mocker.Mock()
        session.scalar = AsyncMock(return_value=None)
        return session

    @pytest.fixture
    def mock_adapter(self, mocker):
        """Create a mock payment adapter."""
        adapter = mocker.Mock()
        return adapter

    @pytest.mark.asyncio
    async def test_provider_not_configured(self, mock_session):
        """Should raise error when provider not configured."""
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.side_effect = Exception("Provider 'stripe' not found")

            service = PaymentsService(mock_session, tenant_id="tenant_1", provider_name="stripe")

            with pytest.raises(RuntimeError, match="No payments adapter registered"):
                service._get_adapter()

    @pytest.mark.asyncio
    async def test_provider_api_failure(self, mock_session, mock_adapter):
        """Should propagate provider API failures."""
        from svc_infra.apf_payments.schemas import CustomerUpsertIn
        from svc_infra.apf_payments.service import PaymentsService

        mock_adapter.ensure_customer = AsyncMock(side_effect=Exception("Stripe API unavailable"))

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            with pytest.raises(Exception, match="Stripe API unavailable"):
                await service.ensure_customer(CustomerUpsertIn(email="test@example.com"))

    @pytest.mark.asyncio
    async def test_intent_creation_failure(self, mock_session, mock_adapter):
        """Should propagate intent creation failures."""
        from svc_infra.apf_payments.schemas import IntentCreateIn
        from svc_infra.apf_payments.service import PaymentsService

        mock_adapter.create_intent = AsyncMock(side_effect=Exception("Card declined"))

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            with pytest.raises(Exception, match="Card declined"):
                await service.create_intent(
                    user_id="user_1",
                    data=IntentCreateIn(
                        amount=5000,
                        currency="USD",
                    ),
                )


class TestPaymentValidationErrors:
    """Tests for payment validation error scenarios."""

    @pytest.fixture
    def mock_session(self, mocker):
        """Create a mock async session."""
        session = mocker.Mock()
        session.add = mocker.Mock()
        session.scalar = AsyncMock(return_value=None)
        return session

    def test_empty_tenant_id(self, mock_session):
        """Should reject empty tenant_id."""
        from svc_infra.apf_payments.service import PaymentsService

        with pytest.raises(ValueError, match="tenant_id is required"):
            PaymentsService(mock_session, tenant_id="")

    def test_none_tenant_id(self, mock_session):
        """Should reject None tenant_id."""
        from svc_infra.apf_payments.service import PaymentsService

        with pytest.raises(ValueError, match="tenant_id is required"):
            PaymentsService(mock_session, tenant_id=None)

    @pytest.mark.asyncio
    async def test_provider_name_normalized(self, mock_session):
        """Should normalize provider name to lowercase."""
        from svc_infra.apf_payments.service import PaymentsService

        service = PaymentsService(mock_session, tenant_id="tenant_1", provider_name="STRIPE")
        assert service._provider_name == "stripe"

        service2 = PaymentsService(mock_session, tenant_id="tenant_1", provider_name="Aiydan")
        assert service2._provider_name == "aiydan"


class TestWebhookErrors:
    """Tests for webhook processing errors."""

    @pytest.fixture
    def mock_session(self, mocker):
        """Create a mock async session."""
        session = mocker.Mock()
        session.add = mocker.Mock()
        session.scalar = AsyncMock(return_value=None)
        return session

    @pytest.fixture
    def mock_adapter(self, mocker):
        """Create a mock payment adapter."""
        adapter = mocker.Mock()
        return adapter

    @pytest.mark.asyncio
    async def test_webhook_signature_invalid(self, mock_session, mock_adapter):
        """Should raise error for invalid webhook signature."""
        from svc_infra.apf_payments.service import PaymentsService

        mock_adapter.verify_and_parse_webhook = AsyncMock(
            side_effect=Exception("Invalid signature")
        )

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            with pytest.raises(Exception, match="Invalid signature"):
                await service.handle_webhook(
                    provider="stripe",
                    signature="invalid_sig",
                    payload=b"{}",
                )

    @pytest.mark.asyncio
    async def test_webhook_malformed_payload(self, mock_session, mock_adapter):
        """Should raise error for malformed webhook payload."""
        from svc_infra.apf_payments.service import PaymentsService

        mock_adapter.verify_and_parse_webhook = AsyncMock(
            side_effect=Exception("JSON decode error")
        )

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            with pytest.raises(Exception, match="JSON decode error"):
                await service.handle_webhook(
                    provider="stripe",
                    signature="sig_test",
                    payload=b"not json",
                )


class TestSubscriptionErrors:
    """Tests for subscription-related errors."""

    @pytest.fixture
    def mock_session(self, mocker):
        """Create a mock async session."""
        session = mocker.Mock()
        session.add = mocker.Mock()
        session.scalar = AsyncMock(return_value=None)
        return session

    @pytest.fixture
    def mock_adapter(self, mocker):
        """Create a mock payment adapter."""
        adapter = mocker.Mock()
        return adapter

    @pytest.mark.asyncio
    async def test_subscription_create_invalid_price(self, mock_session, mock_adapter):
        """Should propagate error for invalid price ID."""
        from svc_infra.apf_payments.schemas import SubscriptionCreateIn
        from svc_infra.apf_payments.service import PaymentsService

        mock_adapter.create_subscription = AsyncMock(
            side_effect=Exception("No such price: price_invalid")
        )

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            with pytest.raises(Exception, match="No such price"):
                await service.create_subscription(
                    SubscriptionCreateIn(
                        customer_provider_id="cus_test",
                        price_provider_id="price_invalid",
                        quantity=1,
                    )
                )

    @pytest.mark.asyncio
    async def test_subscription_cancel_not_found(self, mock_session, mock_adapter):
        """Should propagate error when subscription not found."""
        from svc_infra.apf_payments.service import PaymentsService

        mock_adapter.cancel_subscription = AsyncMock(
            side_effect=Exception("No such subscription: sub_invalid")
        )

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            with pytest.raises(Exception, match="No such subscription"):
                await service.cancel_subscription("sub_invalid")


class TestPaymentMethodErrors:
    """Tests for payment method errors."""

    @pytest.fixture
    def mock_session(self, mocker):
        """Create a mock async session."""
        session = mocker.Mock()
        session.add = mocker.Mock()
        session.scalar = AsyncMock(return_value=None)
        return session

    @pytest.fixture
    def mock_adapter(self, mocker):
        """Create a mock payment adapter."""
        adapter = mocker.Mock()
        return adapter

    @pytest.mark.asyncio
    async def test_attach_payment_method_invalid(self, mock_session, mock_adapter):
        """Should propagate error for invalid payment method."""
        from svc_infra.apf_payments.schemas import PaymentMethodAttachIn
        from svc_infra.apf_payments.service import PaymentsService

        mock_adapter.attach_payment_method = AsyncMock(
            side_effect=Exception("No such payment method: pm_invalid")
        )

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            with pytest.raises(Exception, match="No such payment method"):
                await service.attach_payment_method(
                    PaymentMethodAttachIn(
                        customer_provider_id="cus_test",
                        payment_method_token="pm_invalid",
                    )
                )

    @pytest.mark.asyncio
    async def test_detach_payment_method_not_attached(self, mock_session, mock_adapter):
        """Should propagate error when payment method not attached."""
        from svc_infra.apf_payments.service import PaymentsService

        mock_adapter.detach_payment_method = AsyncMock(
            side_effect=Exception("Payment method is not attached to any customer")
        )

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            with pytest.raises(Exception, match="not attached"):
                await service.detach_payment_method("pm_unattached")


class TestInvoiceErrors:
    """Tests for invoice-related errors."""

    @pytest.fixture
    def mock_session(self, mocker):
        """Create a mock async session."""
        session = mocker.Mock()
        session.add = mocker.Mock()
        session.scalar = AsyncMock(return_value=None)
        return session

    @pytest.fixture
    def mock_adapter(self, mocker):
        """Create a mock payment adapter."""
        adapter = mocker.Mock()
        return adapter

    @pytest.mark.asyncio
    async def test_invoice_finalize_already_finalized(self, mock_session, mock_adapter):
        """Should propagate error when invoice already finalized."""
        from svc_infra.apf_payments.service import PaymentsService

        mock_adapter.finalize_invoice = AsyncMock(
            side_effect=Exception("Invoice is already finalized")
        )

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            with pytest.raises(Exception, match="already finalized"):
                await service.finalize_invoice("in_finalized")

    @pytest.mark.asyncio
    async def test_invoice_pay_insufficient_balance(self, mock_session, mock_adapter):
        """Should propagate error when customer has insufficient balance."""
        from svc_infra.apf_payments.service import PaymentsService

        mock_adapter.pay_invoice = AsyncMock(side_effect=Exception("No payment method on file"))

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            with pytest.raises(Exception, match="No payment method"):
                await service.pay_invoice("in_unpaid")
