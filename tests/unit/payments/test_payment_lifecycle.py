"""
Tests for full payment lifecycle through PaymentsService.

Covers: customer creation -> intent -> confirmation -> success.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


class TestPaymentIntentLifecycle:
    """Tests for payment intent lifecycle."""

    @pytest.fixture
    def mock_session(self, mocker):
        """Create a mock async session."""
        session = mocker.Mock()
        session.add = mocker.Mock()
        session.scalar = AsyncMock(return_value=None)
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def mock_adapter(self, mocker):
        """Create a mock payment adapter."""
        from svc_infra.apf_payments.schemas import CustomerOut, IntentOut

        adapter = mocker.Mock()
        adapter.ensure_customer = AsyncMock(
            return_value=CustomerOut(
                id="cust_1",
                provider="stripe",
                provider_customer_id="cus_test123",
            )
        )
        adapter.create_intent = AsyncMock(
            return_value=IntentOut(
                id="pi_1",
                provider="stripe",
                provider_intent_id="pi_test123",
                status="requires_confirmation",
                amount=5000,
                currency="USD",
                client_secret="pi_test123_secret_xxx",
            )
        )
        adapter.confirm_intent = AsyncMock(
            return_value=IntentOut(
                id="pi_1",
                provider="stripe",
                provider_intent_id="pi_test123",
                status="succeeded",
                amount=5000,
                currency="USD",
            )
        )
        adapter.cancel_intent = AsyncMock(
            return_value=IntentOut(
                id="pi_1",
                provider="stripe",
                provider_intent_id="pi_test123",
                status="canceled",
                amount=5000,
                currency="USD",
            )
        )
        return adapter

    @pytest.mark.asyncio
    async def test_create_customer_and_intent(self, mock_session, mock_adapter, monkeypatch):
        """Should create customer and payment intent."""
        from svc_infra.apf_payments.schemas import CustomerUpsertIn, IntentCreateIn
        from svc_infra.apf_payments.service import PaymentsService

        # Mock the provider registry
        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            # Create customer
            customer = await service.ensure_customer(CustomerUpsertIn(email="test@example.com"))
            assert customer.provider_customer_id == "cus_test123"

            # Create intent
            intent = await service.create_intent(
                user_id="user_1",
                data=IntentCreateIn(
                    amount=5000,
                    currency="USD",
                    description=f"Payment for customer {customer.provider_customer_id}",
                ),
            )
            assert intent.provider_intent_id == "pi_test123"
            assert intent.status == "requires_confirmation"
            assert intent.client_secret == "pi_test123_secret_xxx"

    @pytest.mark.asyncio
    async def test_confirm_intent(self, mock_session, mock_adapter, monkeypatch):
        """Should confirm a payment intent."""
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            result = await service.confirm_intent("pi_test123")
            assert result.status == "succeeded"

    @pytest.mark.asyncio
    async def test_cancel_intent(self, mock_session, mock_adapter, monkeypatch):
        """Should cancel a payment intent."""
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            result = await service.cancel_intent("pi_test123")
            assert result.status == "canceled"

    @pytest.mark.asyncio
    async def test_full_payment_flow(self, mock_session, mock_adapter, monkeypatch):
        """Should complete full payment flow: customer -> intent -> confirm."""
        from svc_infra.apf_payments.schemas import CustomerUpsertIn, IntentCreateIn
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            # Step 1: Create customer
            customer = await service.ensure_customer(
                CustomerUpsertIn(email="customer@example.com", user_id="user_123")
            )
            assert customer.provider == "stripe"

            # Step 2: Create intent
            intent = await service.create_intent(
                user_id="user_123",
                data=IntentCreateIn(
                    amount=10000,
                    currency="USD",
                    description=f"Payment for {customer.provider_customer_id}",
                ),
            )
            assert intent.status == "requires_confirmation"

            # Step 3: Confirm intent
            confirmed = await service.confirm_intent(intent.provider_intent_id)
            assert confirmed.status == "succeeded"


class TestPaymentSubscriptionLifecycle:
    """Tests for subscription payment lifecycle."""

    @pytest.fixture
    def mock_session(self, mocker):
        """Create a mock async session."""
        session = mocker.Mock()
        session.add = mocker.Mock()
        session.scalar = AsyncMock(return_value=None)
        return session

    @pytest.fixture
    def mock_adapter(self, mocker):
        """Create a mock payment adapter with subscription support."""
        from svc_infra.apf_payments.schemas import (
            CustomerOut,
            PriceOut,
            ProductOut,
            SubscriptionOut,
        )

        adapter = mocker.Mock()
        adapter.ensure_customer = AsyncMock(
            return_value=CustomerOut(
                id="cust_1",
                provider="stripe",
                provider_customer_id="cus_sub_test",
            )
        )
        adapter.create_product = AsyncMock(
            return_value=ProductOut(
                id="prod_1",
                provider="stripe",
                provider_product_id="prod_test123",
                name="Pro Plan",
                active=True,
            )
        )
        adapter.create_price = AsyncMock(
            return_value=PriceOut(
                id="price_1",
                provider="stripe",
                provider_price_id="price_test123",
                provider_product_id="prod_test123",
                currency="USD",
                unit_amount=2999,
                interval="month",
            )
        )
        adapter.create_subscription = AsyncMock(
            return_value=SubscriptionOut(
                id="sub_1",
                provider="stripe",
                provider_subscription_id="sub_test123",
                provider_price_id="price_test123",
                status="active",
                quantity=1,
                cancel_at_period_end=False,
            )
        )
        return adapter

    @pytest.mark.asyncio
    async def test_subscription_flow(self, mock_session, mock_adapter, monkeypatch):
        """Should create product, price, and subscription."""
        from svc_infra.apf_payments.schemas import (
            CustomerUpsertIn,
            PriceCreateIn,
            ProductCreateIn,
            SubscriptionCreateIn,
        )
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            # Create customer
            customer = await service.ensure_customer(
                CustomerUpsertIn(email="subscriber@example.com")
            )

            # Create product
            product = await service.create_product(ProductCreateIn(name="Pro Plan", active=True))
            assert product.name == "Pro Plan"

            # Create price
            price = await service.create_price(
                PriceCreateIn(
                    provider_product_id=product.provider_product_id,
                    currency="USD",
                    unit_amount=2999,
                    interval="month",
                )
            )
            assert price.interval == "month"

            # Create subscription
            subscription = await service.create_subscription(
                SubscriptionCreateIn(
                    customer_provider_id=customer.provider_customer_id,
                    price_provider_id=price.provider_price_id,
                    quantity=1,
                )
            )
            assert subscription.status == "active"


class TestPaymentServiceTenantRequirement:
    """Tests for tenant_id requirement."""

    def test_tenant_id_required(self, mocker):
        """Should raise error when tenant_id is missing."""
        from svc_infra.apf_payments.service import PaymentsService

        session = mocker.Mock()

        with pytest.raises(ValueError, match="tenant_id is required"):
            PaymentsService(session, tenant_id="")

        with pytest.raises(ValueError, match="tenant_id is required"):
            PaymentsService(session, tenant_id=None)


class TestPaymentServiceProviderSelection:
    """Tests for provider selection."""

    @pytest.fixture
    def mock_session(self, mocker):
        """Create a mock async session."""
        session = mocker.Mock()
        session.add = mocker.Mock()
        session.scalar = AsyncMock(return_value=None)
        return session

    @pytest.mark.asyncio
    async def test_default_provider(self, mock_session, monkeypatch):
        """Should use default provider from settings."""
        from svc_infra.apf_payments.service import PaymentsService

        monkeypatch.setenv("APF_PAYMENTS_PROVIDER", "stripe")

        with patch("svc_infra.apf_payments.service.get_payments_settings") as mock_settings:
            mock_settings.return_value.default_provider = "stripe"

            service = PaymentsService(mock_session, tenant_id="tenant_1")
            assert service._provider_name == "stripe"

    @pytest.mark.asyncio
    async def test_explicit_provider(self, mock_session):
        """Should use explicitly passed provider."""
        from svc_infra.apf_payments.service import PaymentsService

        service = PaymentsService(mock_session, tenant_id="tenant_1", provider_name="aiydan")
        assert service._provider_name == "aiydan"

    @pytest.mark.asyncio
    async def test_provider_not_found(self, mock_session):
        """Should raise helpful error when provider not registered."""
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.side_effect = Exception("Not found")

            service = PaymentsService(mock_session, tenant_id="tenant_1", provider_name="unknown")

            with pytest.raises(RuntimeError, match="No payments adapter registered"):
                service._get_adapter()
