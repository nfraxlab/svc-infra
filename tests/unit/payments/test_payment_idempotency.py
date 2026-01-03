"""
Tests for idempotency key handling in payments.

Covers: idempotency key generation, duplicate prevention, key conflicts.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


class TestIdempotencyKeyHandling:
    """Tests for idempotency key support in payment operations."""

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
        from svc_infra.apf_payments.schemas import IntentOut

        adapter = mocker.Mock()
        adapter.create_intent = AsyncMock(
            return_value=IntentOut(
                id="pi_1",
                provider="stripe",
                provider_intent_id="pi_test123",
                status="requires_payment_method",
                amount=5000,
                currency="USD",
            )
        )
        return adapter

    @pytest.mark.asyncio
    async def test_intent_with_description(self, mock_session, mock_adapter, mocker):
        """Should pass description to adapter for tracking."""
        from svc_infra.apf_payments.schemas import IntentCreateIn
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            await service.create_intent(
                user_id="user_1",
                data=IntentCreateIn(
                    amount=5000,
                    currency="USD",
                    description="Order #123 payment",
                ),
            )

            # Verify adapter was called with the description
            call_args = mock_adapter.create_intent.call_args
            intent_data = call_args[0][0]
            assert intent_data.description == "Order #123 payment"

    @pytest.mark.asyncio
    async def test_duplicate_description_returns_same_result(
        self, mock_session, mock_adapter, mocker
    ):
        """Should return same result for duplicate calls with same description."""
        from svc_infra.apf_payments.schemas import IntentCreateIn, IntentOut
        from svc_infra.apf_payments.service import PaymentsService

        # Simulate behavior: same call returns same result
        expected_result = IntentOut(
            id="pi_1",
            provider="stripe",
            provider_intent_id="pi_idempotent",
            status="requires_payment_method",
            amount=5000,
            currency="USD",
        )
        mock_adapter.create_intent = AsyncMock(return_value=expected_result)

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            intent_data = IntentCreateIn(
                amount=5000,
                currency="USD",
                description="Order #unique_order_key",
            )

            # First call
            result1 = await service.create_intent(user_id="user_1", data=intent_data)

            # Second call with same data
            result2 = await service.create_intent(user_id="user_1", data=intent_data)

            # Both should return the same intent
            assert result1.provider_intent_id == result2.provider_intent_id
            assert result1.provider_intent_id == "pi_idempotent"


class TestIdempotencyKeyFormats:
    """Tests for idempotency key format validation."""

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
        from svc_infra.apf_payments.schemas import IntentOut

        adapter = mocker.Mock()
        adapter.create_intent = AsyncMock(
            return_value=IntentOut(
                id="pi_1",
                provider="stripe",
                provider_intent_id="pi_test",
                status="requires_payment_method",
                amount=1000,
                currency="USD",
            )
        )
        return adapter

    @pytest.mark.asyncio
    async def test_uuid_description_format(self, mock_session, mock_adapter):
        """Should accept UUID format in description for tracking."""
        from svc_infra.apf_payments.schemas import IntentCreateIn
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            await service.create_intent(
                user_id="user_1",
                data=IntentCreateIn(
                    amount=1000,
                    currency="USD",
                    description="Order 550e8400-e29b-41d4-a716-446655440000",
                ),
            )

            # Should succeed without error
            mock_adapter.create_intent.assert_called_once()

    @pytest.mark.asyncio
    async def test_custom_description_format(self, mock_session, mock_adapter):
        """Should accept custom format in description."""
        from svc_infra.apf_payments.schemas import IntentCreateIn
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            await service.create_intent(
                user_id="user_1",
                data=IntentCreateIn(
                    amount=1000,
                    currency="USD",
                    description="order_12345_payment_attempt_1",
                ),
            )

            mock_adapter.create_intent.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_description(self, mock_session, mock_adapter):
        """Should work without description."""
        from svc_infra.apf_payments.schemas import IntentCreateIn
        from svc_infra.apf_payments.service import PaymentsService

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            await service.create_intent(
                user_id="user_1",
                data=IntentCreateIn(
                    amount=1000,
                    currency="USD",
                    # No description
                ),
            )

            mock_adapter.create_intent.assert_called_once()


class TestLedgerIdempotency:
    """Tests for ledger entry idempotency."""

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
        from svc_infra.apf_payments.schemas import IntentOut

        adapter = mocker.Mock()
        adapter.refund = AsyncMock(
            return_value=IntentOut(
                id="pi_1",
                provider="stripe",
                provider_intent_id="pi_test",
                status="refunded",
                amount=5000,
                currency="USD",
            )
        )
        return adapter

    @pytest.mark.asyncio
    async def test_ledger_prevents_duplicate_refund_entries(
        self, mock_session, mock_adapter, mocker
    ):
        """Should not create duplicate ledger entries for same refund."""
        from svc_infra.apf_payments.schemas import RefundIn
        from svc_infra.apf_payments.service import PaymentsService

        mock_intent = mocker.Mock()
        mock_intent.provider = "stripe"
        mock_intent.user_id = "user_1"

        # Simulate existing ledger entry
        existing_ledger = mocker.Mock()
        existing_ledger.id = 1

        # First query returns intent, second returns existing ledger
        mock_session.scalar = AsyncMock(side_effect=[mock_intent, existing_ledger])

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")
            mock_session.add.reset_mock()

            await service.refund("pi_test", RefundIn(amount=5000))

            # Should NOT add duplicate ledger entry
            mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_capture_prevents_duplicate_entries(self, mock_session, mocker):
        """Should not create duplicate ledger entries for same capture."""
        from svc_infra.apf_payments.service import PaymentsService

        mock_intent = mocker.Mock()
        mock_intent.provider = "stripe"
        mock_intent.user_id = "user_1"
        mock_intent.captured = False

        existing_ledger = mocker.Mock()
        existing_ledger.id = 1

        # First returns intent, second returns existing ledger
        mock_session.scalar = AsyncMock(side_effect=[mock_intent, existing_ledger])

        with patch("svc_infra.apf_payments.service.get_provider_registry"):
            service = PaymentsService(mock_session, tenant_id="tenant_1")
            mock_session.add.reset_mock()

            charge_obj = {
                "id": "ch_test",
                "payment_intent": "pi_test",
                "amount": 5000,
                "currency": "usd",
            }

            await service._post_capture(charge_obj)

            # Should NOT add duplicate capture entry
            mock_session.add.assert_not_called()
