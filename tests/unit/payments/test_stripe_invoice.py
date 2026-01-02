"""
Tests for Stripe invoice operations: generation and payment.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestStripeInvoiceCreate:
    """Tests for creating Stripe invoices."""

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
    def mock_invoice(self, mocker):
        """Create a mock invoice object."""
        inv = mocker.Mock()
        inv.id = "in_test123"
        inv.customer = "cus_test"
        inv.status = "draft"
        inv.amount_due = 5000
        inv.currency = "usd"
        inv.hosted_invoice_url = "https://invoice.stripe.com/test"
        inv.invoice_pdf = "https://invoice.stripe.com/test.pdf"
        return inv

    @pytest.mark.asyncio
    async def test_create_invoice_basic(
        self, mock_stripe_settings, monkeypatch, mocker, mock_invoice
    ):
        """Should create a basic invoice."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        monkeypatch.setattr(stripe_sdk.Invoice, "create", lambda **kw: mock_invoice)

        from svc_infra.apf_payments.schemas import InvoiceCreateIn

        result = await adapter.create_invoice(InvoiceCreateIn(customer_provider_id="cus_test"))

        assert result.provider_invoice_id == "in_test123"
        assert result.status == "draft"
        assert result.provider == "stripe"

    @pytest.mark.asyncio
    async def test_create_invoice_auto_advance(
        self, mock_stripe_settings, monkeypatch, mocker, mock_invoice
    ):
        """Should create invoice with auto_advance setting."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        captured_kwargs = {}

        def capture_create(**kw):
            captured_kwargs.update(kw)
            return mock_invoice

        monkeypatch.setattr(stripe_sdk.Invoice, "create", capture_create)

        from svc_infra.apf_payments.schemas import InvoiceCreateIn

        await adapter.create_invoice(
            InvoiceCreateIn(customer_provider_id="cus_test", auto_advance=True)
        )

        assert captured_kwargs.get("auto_advance") is True


class TestStripeInvoiceFinalize:
    """Tests for finalizing Stripe invoices."""

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
    def mock_invoice(self, mocker):
        """Create a mock finalized invoice."""
        inv = mocker.Mock()
        inv.id = "in_final"
        inv.customer = "cus_test"
        inv.status = "open"
        inv.amount_due = 10000
        inv.currency = "usd"
        inv.hosted_invoice_url = "https://invoice.stripe.com/final"
        inv.invoice_pdf = "https://invoice.stripe.com/final.pdf"
        return inv

    @pytest.mark.asyncio
    async def test_finalize_invoice(self, mock_stripe_settings, monkeypatch, mocker, mock_invoice):
        """Should finalize a draft invoice."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        monkeypatch.setattr(stripe_sdk.Invoice, "finalize_invoice", lambda inv_id: mock_invoice)

        result = await adapter.finalize_invoice("in_draft")

        assert result.status == "open"


class TestStripeInvoicePay:
    """Tests for paying Stripe invoices."""

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
    def mock_invoice(self, mocker):
        """Create a mock paid invoice."""
        inv = mocker.Mock()
        inv.id = "in_paid"
        inv.customer = "cus_test"
        inv.status = "paid"
        inv.amount_due = 0
        inv.currency = "usd"
        inv.hosted_invoice_url = "https://invoice.stripe.com/paid"
        inv.invoice_pdf = "https://invoice.stripe.com/paid.pdf"
        return inv

    @pytest.mark.asyncio
    async def test_pay_invoice(self, mock_stripe_settings, monkeypatch, mocker, mock_invoice):
        """Should pay an open invoice."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        monkeypatch.setattr(stripe_sdk.Invoice, "pay", lambda inv_id: mock_invoice)

        result = await adapter.pay_invoice("in_open")

        assert result.status == "paid"


class TestStripeInvoiceVoid:
    """Tests for voiding Stripe invoices."""

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
    def mock_invoice(self, mocker):
        """Create a mock voided invoice."""
        inv = mocker.Mock()
        inv.id = "in_void"
        inv.customer = "cus_test"
        inv.status = "void"
        inv.amount_due = 0
        inv.currency = "usd"
        inv.hosted_invoice_url = None
        inv.invoice_pdf = None
        return inv

    @pytest.mark.asyncio
    async def test_void_invoice(self, mock_stripe_settings, monkeypatch, mocker, mock_invoice):
        """Should void an open invoice."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        monkeypatch.setattr(stripe_sdk.Invoice, "void_invoice", lambda inv_id: mock_invoice)

        result = await adapter.void_invoice("in_open")

        assert result.status == "void"


class TestStripeInvoiceLineItems:
    """Tests for invoice line items."""

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
    def mock_invoice(self, mocker):
        """Create a mock invoice with line items."""
        inv = mocker.Mock()
        inv.id = "in_lines"
        inv.customer = "cus_test"
        inv.status = "draft"
        inv.amount_due = 2500
        inv.currency = "usd"
        inv.hosted_invoice_url = None
        inv.invoice_pdf = None
        return inv

    @pytest.mark.asyncio
    async def test_add_line_item(self, mock_stripe_settings, monkeypatch, mocker, mock_invoice):
        """Should add a line item to invoice."""
        self._skip_if_no_stripe()
        from svc_infra.apf_payments.provider.stripe import StripeAdapter
        from svc_infra.apf_payments.provider.stripe import stripe as stripe_sdk

        adapter = StripeAdapter()

        mock_line = mocker.Mock()
        mock_line.id = "ii_line1"

        monkeypatch.setattr(stripe_sdk.InvoiceItem, "create", lambda **kw: mock_line)
        monkeypatch.setattr(stripe_sdk.Invoice, "retrieve", lambda inv_id: mock_invoice)

        from svc_infra.apf_payments.schemas import InvoiceLineItemIn

        result = await adapter.add_invoice_line_item(
            "in_draft",
            InvoiceLineItemIn(
                customer_provider_id="cus_test",
                description="Test Item",
                unit_amount=2500,
                quantity=1,
                currency="USD",
            ),
        )

        assert result.provider_invoice_id == "in_lines"
