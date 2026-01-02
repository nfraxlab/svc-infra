"""Tests for FastAPI billing setup - Coverage improvement."""

from __future__ import annotations

from unittest.mock import MagicMock

from svc_infra.api.fastapi.billing.setup import add_billing

# ─── add_billing Tests ─────────────────────────────────────────────────────


class TestAddBilling:
    """Tests for add_billing function."""

    def test_default_prefix(self) -> None:
        """Test add_billing with default prefix."""
        mock_app = MagicMock()

        add_billing(mock_app)

        mock_app.include_router.assert_called_once()

    def test_custom_prefix(self) -> None:
        """Test add_billing with custom prefix."""
        mock_app = MagicMock()

        add_billing(mock_app, prefix="/api/billing")

        mock_app.include_router.assert_called_once()

    def test_empty_prefix(self) -> None:
        """Test add_billing with empty prefix."""
        mock_app = MagicMock()

        add_billing(mock_app, prefix="")

        mock_app.include_router.assert_called_once()

    def test_same_as_default_prefix(self) -> None:
        """Test add_billing with explicitly set default prefix."""
        mock_app = MagicMock()

        add_billing(mock_app, prefix="/_billing")

        mock_app.include_router.assert_called_once()
