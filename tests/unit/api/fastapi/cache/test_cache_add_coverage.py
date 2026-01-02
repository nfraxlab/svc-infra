"""Tests for FastAPI cache setup - Coverage improvement."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from svc_infra.api.fastapi.cache.add import setup_caching

# ─── setup_caching Tests ───────────────────────────────────────────────────


class TestSetupCaching:
    """Tests for setup_caching function."""

    def test_attaches_lifespan(self) -> None:
        """Test that lifespan is attached to app."""
        mock_app = MagicMock()
        mock_app.router = MagicMock()

        setup_caching(mock_app)

        assert mock_app.router.lifespan_context is not None

    @pytest.mark.asyncio
    @patch("svc_infra.api.fastapi.cache.add.shutdown_cache")
    @patch("svc_infra.api.fastapi.cache.add.init_cache")
    async def test_lifespan_calls_init_and_shutdown(
        self, mock_init: MagicMock, mock_shutdown: AsyncMock
    ) -> None:
        """Test lifespan calls init and shutdown."""
        mock_shutdown.return_value = None

        mock_app = MagicMock()
        mock_app.router = MagicMock()

        setup_caching(mock_app)

        lifespan = mock_app.router.lifespan_context

        async with lifespan(mock_app):
            mock_init.assert_called_once()

        mock_shutdown.assert_awaited_once()
