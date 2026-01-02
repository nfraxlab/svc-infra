"""Tests for svc_infra.apf_payments.service.PaymentsService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestPaymentsServiceInit:
    """Tests for PaymentsService initialization."""

    def test_raises_without_tenant_id(self) -> None:
        """Should raise ValueError if tenant_id not provided."""
        with pytest.raises(ValueError) as exc_info:
            from svc_infra.apf_payments.service import PaymentsService

            PaymentsService(session=MagicMock(), tenant_id="")

        assert "tenant_id is required" in str(exc_info.value)

    def test_initializes_with_valid_tenant_id(self) -> None:
        """Should initialize with valid tenant_id."""
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_payments_settings") as mock_settings:
            mock_settings.return_value.default_provider = "stripe"

            service = PaymentsService(
                session=MagicMock(),
                tenant_id="tenant-1",
            )

            assert service.tenant_id == "tenant-1"
            assert service._provider_name == "stripe"

    def test_accepts_custom_provider(self) -> None:
        """Should accept custom provider name."""
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_payments_settings") as mock_settings:
            mock_settings.return_value.default_provider = "stripe"

            service = PaymentsService(
                session=MagicMock(),
                tenant_id="tenant-1",
                provider_name="custom",
            )

            assert service._provider_name == "custom"


class TestPaymentsServiceGetAdapter:
    """Tests for adapter resolution."""

    def test_raises_if_adapter_not_found(self) -> None:
        """Should raise RuntimeError if adapter not registered."""
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_payments_settings") as mock_settings:
            mock_settings.return_value.default_provider = "unknown_provider"

            service = PaymentsService(
                session=MagicMock(),
                tenant_id="tenant-1",
            )

            with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_reg:
                mock_reg.return_value.get.side_effect = KeyError("not found")

                with pytest.raises(RuntimeError) as exc_info:
                    service._get_adapter()

                assert "No payments adapter registered" in str(exc_info.value)

    def test_caches_adapter(self) -> None:
        """Should cache adapter after first resolution."""
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_payments_settings") as mock_settings:
            mock_settings.return_value.default_provider = "stripe"

            service = PaymentsService(
                session=MagicMock(),
                tenant_id="tenant-1",
            )

            mock_adapter = MagicMock()
            with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_reg:
                mock_reg.return_value.get.return_value = mock_adapter

                adapter1 = service._get_adapter()
                adapter2 = service._get_adapter()

                assert adapter1 is adapter2
                mock_reg.return_value.get.assert_called_once()


class TestPaymentsServiceCustomers:
    """Tests for customer operations."""

    @pytest.fixture
    def service(self):
        """Create a PaymentsService with mocked dependencies."""
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_payments_settings") as mock_settings:
            mock_settings.return_value.default_provider = "stripe"

            session = AsyncMock()
            svc = PaymentsService(session=session, tenant_id="tenant-1")
            svc._adapter = AsyncMock()
            return svc

    @pytest.mark.asyncio
    async def test_ensure_customer_creates_new(self, service) -> None:
        """Should create new customer and persist locally."""
        from svc_infra.apf_payments.schemas import CustomerOut, CustomerUpsertIn

        mock_out = CustomerOut(
            id="cust-uuid",
            provider="stripe",
            provider_customer_id="cus_123",
            email="test@example.com",
            name="Test User",
        )
        service._adapter.ensure_customer.return_value = mock_out
        service.session.scalar.return_value = None  # No existing customer

        result = await service.ensure_customer(
            CustomerUpsertIn(email="test@example.com", name="Test User")
        )

        assert result.provider_customer_id == "cus_123"
        service.session.add.assert_called_once()


class TestPaymentsServiceIntents:
    """Tests for payment intent operations."""

    @pytest.fixture
    def service(self):
        """Create a PaymentsService with mocked dependencies."""
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_payments_settings") as mock_settings:
            mock_settings.return_value.default_provider = "stripe"

            session = AsyncMock()
            svc = PaymentsService(session=session, tenant_id="tenant-1")
            svc._adapter = AsyncMock()
            return svc

    @pytest.mark.asyncio
    async def test_create_intent(self, service) -> None:
        """Should create intent and persist locally."""
        from svc_infra.apf_payments.schemas import IntentCreateIn, IntentOut

        mock_out = IntentOut(
            id="intent-uuid",
            provider="stripe",
            provider_intent_id="pi_123",
            amount=5000,
            currency="USD",
            status="requires_payment_method",
            client_secret="pi_123_secret",
        )
        service._adapter.create_intent.return_value = mock_out

        result = await service.create_intent(
            user_id="user-1",
            data=IntentCreateIn(amount=5000, currency="USD"),
        )

        assert result.provider_intent_id == "pi_123"
        service.session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_confirm_intent(self, service) -> None:
        """Should confirm intent and update local record."""
        from svc_infra.apf_payments.schemas import IntentOut

        mock_out = IntentOut(
            id="intent-uuid",
            provider="stripe",
            provider_intent_id="pi_123",
            amount=5000,
            currency="USD",
            status="succeeded",
            client_secret="pi_123_secret",
        )
        service._adapter.confirm_intent.return_value = mock_out

        mock_intent = MagicMock()
        mock_intent.status = "requires_confirmation"
        service.session.scalar.return_value = mock_intent

        result = await service.confirm_intent("pi_123")

        assert result.status == "succeeded"
        assert mock_intent.status == "succeeded"

    @pytest.mark.asyncio
    async def test_cancel_intent(self, service) -> None:
        """Should cancel intent and update local record."""
        from svc_infra.apf_payments.schemas import IntentOut

        mock_out = IntentOut(
            id="intent-uuid",
            provider="stripe",
            provider_intent_id="pi_123",
            amount=5000,
            currency="USD",
            status="canceled",
        )
        service._adapter.cancel_intent.return_value = mock_out

        mock_intent = MagicMock()
        mock_intent.status = "requires_payment_method"
        service.session.scalar.return_value = mock_intent

        result = await service.cancel_intent("pi_123")

        assert result.status == "canceled"
        assert mock_intent.status == "canceled"


class TestPaymentsServiceRefunds:
    """Tests for refund operations."""

    @pytest.fixture
    def service(self):
        """Create a PaymentsService with mocked dependencies."""
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_payments_settings") as mock_settings:
            mock_settings.return_value.default_provider = "stripe"

            session = AsyncMock()
            svc = PaymentsService(session=session, tenant_id="tenant-1")
            svc._adapter = AsyncMock()
            return svc

    @pytest.mark.asyncio
    async def test_refund_creates_ledger_entry(self, service) -> None:
        """Should create ledger entry for refund."""
        from svc_infra.apf_payments.schemas import IntentOut, RefundIn

        mock_out = IntentOut(
            id="intent-uuid",
            provider="stripe",
            provider_intent_id="pi_123",
            amount=5000,
            currency="USD",
            status="succeeded",
        )
        service._adapter.refund.return_value = mock_out

        mock_intent = MagicMock()
        mock_intent.provider = "stripe"
        mock_intent.user_id = "user-1"

        # First call returns intent, second returns None (no existing entry)
        service.session.scalar.side_effect = [mock_intent, None]

        result = await service.refund("pi_123", RefundIn(amount=5000))

        assert result.status == "succeeded"
        # Should add ledger entry
        assert service.session.add.called


class TestPaymentsServiceWebhooks:
    """Tests for webhook handling."""

    @pytest.fixture
    def service(self):
        """Create a PaymentsService with mocked dependencies."""
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_payments_settings") as mock_settings:
            mock_settings.return_value.default_provider = "stripe"

            session = AsyncMock()
            svc = PaymentsService(session=session, tenant_id="tenant-1")
            svc._adapter = AsyncMock()
            return svc

    @pytest.mark.asyncio
    async def test_handle_webhook_persists_event(self, service) -> None:
        """Should persist webhook event."""
        parsed = {
            "id": "evt_123",
            "type": "payment_intent.succeeded",
            "data": {"id": "pi_123", "amount": 5000, "currency": "usd"},
        }
        service._adapter.verify_and_parse_webhook.return_value = parsed
        service.session.scalar.return_value = None  # No existing intent

        result = await service.handle_webhook(
            provider="stripe",
            signature="sig_123",
            payload=b'{"test": true}',
        )

        assert result["ok"] is True
        service.session.add.assert_called()


class TestPaymentsServiceEventDispatch:
    """Tests for internal event dispatch."""

    @pytest.fixture
    def service(self):
        """Create a PaymentsService with mocked dependencies."""
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_payments_settings") as mock_settings:
            mock_settings.return_value.default_provider = "stripe"

            session = AsyncMock()
            svc = PaymentsService(session=session, tenant_id="tenant-1")
            svc._adapter = AsyncMock()
            return svc

    @pytest.mark.asyncio
    async def test_dispatch_payment_succeeded(self, service) -> None:
        """Should dispatch payment_intent.succeeded event."""
        parsed = {
            "type": "payment_intent.succeeded",
            "data": {"id": "pi_123", "amount": 5000, "currency": "usd"},
        }

        mock_intent = MagicMock()
        mock_intent.provider = "stripe"
        mock_intent.user_id = "user-1"
        mock_intent.status = "requires_payment_method"
        service.session.scalar.return_value = mock_intent

        await service._dispatch_event("stripe", parsed)

        assert mock_intent.status == "succeeded"
        service.session.add.assert_called()

    @pytest.mark.asyncio
    async def test_dispatch_charge_refunded(self, service) -> None:
        """Should dispatch charge.refunded event."""
        parsed = {
            "type": "charge.refunded",
            "data": {
                "id": "ch_123",
                "payment_intent": "pi_123",
                "amount_refunded": 2500,
                "currency": "usd",
            },
        }

        mock_intent = MagicMock()
        mock_intent.provider = "stripe"
        mock_intent.user_id = "user-1"
        # First scalar returns intent, second returns None (no existing entry)
        service.session.scalar.side_effect = [mock_intent, None]

        await service._dispatch_event("stripe", parsed)

        service.session.add.assert_called()

    @pytest.mark.asyncio
    async def test_dispatch_charge_captured(self, service) -> None:
        """Should dispatch charge.captured event."""
        parsed = {
            "type": "charge.captured",
            "data": {
                "id": "ch_123",
                "payment_intent": "pi_123",
                "amount": 5000,
                "currency": "usd",
            },
        }

        mock_intent = MagicMock()
        mock_intent.provider = "stripe"
        mock_intent.user_id = "user-1"
        mock_intent.captured = False
        # First scalar returns intent, second returns None (no existing entry)
        service.session.scalar.side_effect = [mock_intent, None]

        await service._dispatch_event("stripe", parsed)

        assert mock_intent.captured is True
        service.session.add.assert_called()


class TestPaymentsServicePaymentMethods:
    """Tests for payment method operations."""

    @pytest.fixture
    def service(self):
        """Create a PaymentsService with mocked dependencies."""
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_payments_settings") as mock_settings:
            mock_settings.return_value.default_provider = "stripe"

            session = AsyncMock()
            svc = PaymentsService(session=session, tenant_id="tenant-1")
            svc._adapter = AsyncMock()
            return svc

    @pytest.mark.asyncio
    async def test_attach_payment_method(self, service) -> None:
        """Should attach payment method and persist locally."""
        from svc_infra.apf_payments.schemas import (
            PaymentMethodAttachIn,
            PaymentMethodOut,
        )

        mock_out = PaymentMethodOut(
            id="pm-uuid",
            provider="stripe",
            provider_customer_id="cus_123",
            provider_method_id="pm_123",
            brand="visa",
            last4="4242",
            exp_month=12,
            exp_year=2025,
            is_default=True,
        )
        service._adapter.attach_payment_method.return_value = mock_out

        result = await service.attach_payment_method(
            PaymentMethodAttachIn(
                customer_provider_id="cus_123",
                payment_method_token="pm_123",
                make_default=True,
            )
        )

        assert result.provider_method_id == "pm_123"
        service.session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_payment_methods(self, service) -> None:
        """Should list payment methods from adapter."""
        from svc_infra.apf_payments.schemas import PaymentMethodOut

        mock_out = [
            PaymentMethodOut(
                id="pm-uuid",
                provider="stripe",
                provider_customer_id="cus_123",
                provider_method_id="pm_123",
                brand="visa",
                last4="4242",
            )
        ]
        service._adapter.list_payment_methods.return_value = mock_out

        result = await service.list_payment_methods("cus_123")

        assert len(result) == 1
        assert result[0].brand == "visa"

    @pytest.mark.asyncio
    async def test_detach_payment_method(self, service) -> None:
        """Should detach payment method."""
        from svc_infra.apf_payments.schemas import PaymentMethodOut

        mock_out = PaymentMethodOut(
            id="pm-uuid",
            provider="stripe",
            provider_customer_id="cus_123",
            provider_method_id="pm_123",
            brand="visa",
            last4="4242",
        )
        service._adapter.detach_payment_method.return_value = mock_out

        result = await service.detach_payment_method("pm_123")

        assert result.provider_method_id == "pm_123"


class TestPaymentsServiceSubscriptions:
    """Tests for subscription operations."""

    @pytest.fixture
    def service(self):
        """Create a PaymentsService with mocked dependencies."""
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_payments_settings") as mock_settings:
            mock_settings.return_value.default_provider = "stripe"

            session = AsyncMock()
            svc = PaymentsService(session=session, tenant_id="tenant-1")
            svc._adapter = AsyncMock()
            return svc

    @pytest.mark.asyncio
    async def test_create_subscription(self, service) -> None:
        """Should create subscription and persist locally."""
        from svc_infra.apf_payments.schemas import SubscriptionCreateIn, SubscriptionOut

        mock_out = SubscriptionOut(
            id="sub-uuid",
            provider="stripe",
            provider_subscription_id="sub_123",
            provider_price_id="price_123",
            status="active",
            quantity=1,
            cancel_at_period_end=False,
        )
        service._adapter.create_subscription.return_value = mock_out

        result = await service.create_subscription(
            SubscriptionCreateIn(
                customer_provider_id="cus_123",
                price_provider_id="price_123",
            )
        )

        assert result.provider_subscription_id == "sub_123"
        service.session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_subscription(self, service) -> None:
        """Should cancel subscription."""
        from svc_infra.apf_payments.schemas import SubscriptionOut

        mock_out = SubscriptionOut(
            id="sub-uuid",
            provider="stripe",
            provider_subscription_id="sub_123",
            provider_price_id="price_123",
            status="active",
            quantity=1,
            cancel_at_period_end=True,
        )
        service._adapter.cancel_subscription.return_value = mock_out

        result = await service.cancel_subscription("sub_123", at_period_end=True)

        assert result.cancel_at_period_end is True


class TestPaymentsServiceProducts:
    """Tests for product operations."""

    @pytest.fixture
    def service(self):
        """Create a PaymentsService with mocked dependencies."""
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_payments_settings") as mock_settings:
            mock_settings.return_value.default_provider = "stripe"

            session = AsyncMock()
            svc = PaymentsService(session=session, tenant_id="tenant-1")
            svc._adapter = AsyncMock()
            return svc

    @pytest.mark.asyncio
    async def test_create_product(self, service) -> None:
        """Should create product and persist locally."""
        from svc_infra.apf_payments.schemas import ProductCreateIn, ProductOut

        mock_out = ProductOut(
            id="prod-uuid",
            provider="stripe",
            provider_product_id="prod_123",
            name="Test Product",
            active=True,
        )
        service._adapter.create_product.return_value = mock_out

        result = await service.create_product(ProductCreateIn(name="Test Product"))

        assert result.provider_product_id == "prod_123"
        service.session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_price(self, service) -> None:
        """Should create price and persist locally."""
        from svc_infra.apf_payments.schemas import PriceCreateIn, PriceOut

        mock_out = PriceOut(
            id="price-uuid",
            provider="stripe",
            provider_price_id="price_123",
            provider_product_id="prod_123",
            currency="USD",
            unit_amount=1000,
            interval="month",
            active=True,
        )
        service._adapter.create_price.return_value = mock_out

        result = await service.create_price(
            PriceCreateIn(
                provider_product_id="prod_123",
                currency="USD",
                unit_amount=1000,
                interval="month",
            )
        )

        assert result.provider_price_id == "price_123"
        service.session.add.assert_called_once()
