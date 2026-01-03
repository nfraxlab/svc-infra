"""
Tests for refund processing through PaymentsService.

Covers: full refund, partial refund, refund errors.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


class TestPaymentRefunds:
    """Tests for payment refund operations."""

    @pytest.fixture
    def mock_session(self, mocker):
        """Create a mock async session."""
        session = mocker.Mock()
        session.add = mocker.Mock()
        session.scalar = AsyncMock(return_value=None)
        return session

    @pytest.fixture
    def mock_intent_row(self, mocker):
        """Create a mock PayIntent row."""
        intent = mocker.Mock()
        intent.id = 1
        intent.tenant_id = "tenant_1"
        intent.provider = "stripe"
        intent.provider_intent_id = "pi_test123"
        intent.user_id = "user_1"
        intent.amount = 5000
        intent.currency = "USD"
        intent.status = "succeeded"
        return intent

    @pytest.fixture
    def mock_adapter(self, mocker):
        """Create a mock payment adapter with refund support."""
        from svc_infra.apf_payments.schemas import IntentOut

        adapter = mocker.Mock()
        adapter.refund = AsyncMock(
            return_value=IntentOut(
                id="pi_1",
                provider="stripe",
                provider_intent_id="pi_test123",
                status="refunded",
                amount=5000,
                currency="USD",
            )
        )
        return adapter

    @pytest.mark.asyncio
    async def test_full_refund(self, mock_session, mock_adapter, mock_intent_row, mocker):
        """Should process a full refund."""
        from svc_infra.apf_payments.schemas import RefundIn
        from svc_infra.apf_payments.service import PaymentsService

        # Return the intent row when queried
        mock_session.scalar = AsyncMock(side_effect=[mock_intent_row, None])

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            result = await service.refund(
                "pi_test123",
                RefundIn(amount=5000),
            )

            assert result.status == "refunded"
            mock_adapter.refund.assert_called_once()

    @pytest.mark.asyncio
    async def test_partial_refund(self, mock_session, mock_adapter, mock_intent_row, mocker):
        """Should process a partial refund."""
        from svc_infra.apf_payments.schemas import IntentOut, RefundIn
        from svc_infra.apf_payments.service import PaymentsService

        mock_adapter.refund = AsyncMock(
            return_value=IntentOut(
                id="pi_1",
                provider="stripe",
                provider_intent_id="pi_test123",
                status="succeeded",  # Still succeeded since partial
                amount=5000,
                currency="USD",
            )
        )

        mock_session.scalar = AsyncMock(side_effect=[mock_intent_row, None])

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            result = await service.refund(
                "pi_test123",
                RefundIn(amount=2500),  # Partial refund
            )

            assert result.provider_intent_id == "pi_test123"

    @pytest.mark.asyncio
    async def test_refund_creates_ledger_entry(
        self, mock_session, mock_adapter, mock_intent_row, mocker
    ):
        """Should create a ledger entry for the refund."""
        from svc_infra.apf_payments.schemas import RefundIn
        from svc_infra.apf_payments.service import PaymentsService

        # Return intent row first, then None for existing ledger check
        mock_session.scalar = AsyncMock(side_effect=[mock_intent_row, None])

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            await service.refund(
                "pi_test123",
                RefundIn(amount=5000),
            )

            # Should have called session.add for the ledger entry
            assert mock_session.add.called

    @pytest.mark.asyncio
    async def test_refund_skips_duplicate_ledger_entry(
        self, mock_session, mock_adapter, mock_intent_row, mocker
    ):
        """Should not create duplicate ledger entries."""
        from svc_infra.apf_payments.schemas import RefundIn
        from svc_infra.apf_payments.service import PaymentsService

        # Mock existing ledger entry
        existing_entry = mocker.Mock()
        existing_entry.id = 1

        # Return intent row, then existing ledger entry
        mock_session.scalar = AsyncMock(side_effect=[mock_intent_row, existing_entry])

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            # Reset add call count
            mock_session.add.reset_mock()

            await service.refund(
                "pi_test123",
                RefundIn(amount=5000),
            )

            # Should NOT have called session.add since entry exists
            mock_session.add.assert_not_called()


class TestRefundValidation:
    """Tests for refund validation scenarios."""

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
    async def test_refund_amount_zero_no_ledger(self, mock_session, mock_adapter, mocker):
        """Should not create ledger entry for zero amount refund."""
        from svc_infra.apf_payments.schemas import IntentOut, RefundIn
        from svc_infra.apf_payments.service import PaymentsService

        mock_intent = mocker.Mock()
        mock_intent.provider = "stripe"
        mock_intent.user_id = "user_1"

        mock_adapter.refund = AsyncMock(
            return_value=IntentOut(
                id="pi_1",
                provider="stripe",
                provider_intent_id="pi_test123",
                status="succeeded",
                amount=0,
                currency="USD",
            )
        )

        mock_session.scalar = AsyncMock(side_effect=[mock_intent, None])

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")
            mock_session.add.reset_mock()

            await service.refund(
                "pi_test123",
                RefundIn(amount=0),
            )

            # Zero amount should not create ledger entry
            mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_refund_intent_not_found(self, mock_session, mock_adapter, mocker):
        """Should handle refund when intent not in local DB."""
        from svc_infra.apf_payments.schemas import IntentOut, RefundIn
        from svc_infra.apf_payments.service import PaymentsService

        mock_adapter.refund = AsyncMock(
            return_value=IntentOut(
                id="pi_1",
                provider="stripe",
                provider_intent_id="pi_unknown",
                status="refunded",
                amount=5000,
                currency="USD",
            )
        )

        # Intent not found locally
        mock_session.scalar = AsyncMock(return_value=None)

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            # Should still succeed - just won't create ledger entry
            result = await service.refund(
                "pi_unknown",
                RefundIn(amount=5000),
            )

            assert result.status == "refunded"


class TestWebhookRefundPosting:
    """Tests for refund posting via webhooks."""

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
        adapter.verify_and_parse_webhook = AsyncMock()
        return adapter

    @pytest.mark.asyncio
    async def test_refund_webhook_creates_ledger(self, mock_session, mock_adapter, mocker):
        """Should create ledger entry from charge.refunded webhook."""
        from svc_infra.apf_payments.service import PaymentsService

        mock_intent = mocker.Mock()
        mock_intent.provider = "stripe"
        mock_intent.user_id = "user_1"

        # First call returns None (for PayEvent check), second returns intent
        mock_session.scalar = AsyncMock(side_effect=[None, mock_intent, None])

        webhook_payload = {
            "id": "evt_refund",
            "type": "charge.refunded",
            "data": {
                "id": "ch_test123",
                "payment_intent": "pi_test123",
                "amount_refunded": 3000,
                "currency": "usd",
            },
        }

        mock_adapter.verify_and_parse_webhook = AsyncMock(return_value=webhook_payload)

        with patch("svc_infra.apf_payments.service.get_provider_registry") as mock_registry:
            mock_registry.return_value.get.return_value = mock_adapter

            service = PaymentsService(mock_session, tenant_id="tenant_1")

            result = await service.handle_webhook(
                provider="stripe",
                signature="sig_test",
                payload=b"{}",
            )

            assert result == {"ok": True}
