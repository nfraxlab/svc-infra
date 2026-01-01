"""Tests for svc_infra.api.fastapi.auth.mfa.security module."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from svc_infra.api.fastapi.auth.mfa.security import RequireMFAIfEnabled
from svc_infra.api.fastapi.auth.mfa.verify import MFAProof, MFAResult


class FakeUser:
    """Fake user for testing."""

    def __init__(self, mfa_enabled: bool = False):
        self.id = "user-123"
        self.mfa_enabled = mfa_enabled


class FakeIdentity:
    """Fake identity principal."""

    def __init__(self, user: FakeUser):
        self.user = user


class TestRequireMFAIfEnabled:
    """Tests for RequireMFAIfEnabled dependency."""

    def test_returns_depends(self) -> None:
        """Should return a Depends object."""
        from fastapi import Depends

        result = RequireMFAIfEnabled()
        assert isinstance(result, type(Depends(lambda: None)))

    def test_custom_body_field(self) -> None:
        """Should accept custom body field name."""
        result = RequireMFAIfEnabled(body_field="mfa_proof")
        assert result is not None


class TestRequireMFAIfEnabledDependency:
    """Integration tests for the MFA dependency behavior."""

    @pytest.mark.asyncio
    async def test_mfa_disabled_passes(self) -> None:
        """Should pass through when MFA is disabled."""
        user = FakeUser(mfa_enabled=False)
        identity = FakeIdentity(user)
        session = AsyncMock()

        # Extract the actual dependency function
        dep = RequireMFAIfEnabled()
        # The dependency is wrapped in Depends, extract the callable
        dep_func = dep.dependency

        result = await dep_func(
            p=identity,
            sess=session,
            mfa=None,
            mfa_code=None,
            mfa_pre_token=None,
        )

        assert result == identity

    @pytest.mark.asyncio
    async def test_mfa_enabled_valid_code(self) -> None:
        """Should pass with valid MFA code when enabled."""
        user = FakeUser(mfa_enabled=True)
        identity = FakeIdentity(user)
        session = AsyncMock()

        with patch("svc_infra.api.fastapi.auth.mfa.security.verify_mfa_for_user") as mock_verify:
            mock_verify.return_value = MFAResult(ok=True, method="totp")

            dep_func = RequireMFAIfEnabled().dependency

            result = await dep_func(
                p=identity,
                sess=session,
                mfa=MFAProof(code="123456"),
                mfa_code=None,
                mfa_pre_token=None,
            )

            assert result == identity
            mock_verify.assert_called_once()

    @pytest.mark.asyncio
    async def test_mfa_enabled_invalid_code_raises(self) -> None:
        """Should raise HTTPException with invalid MFA code."""
        user = FakeUser(mfa_enabled=True)
        identity = FakeIdentity(user)
        session = AsyncMock()

        with patch("svc_infra.api.fastapi.auth.mfa.security.verify_mfa_for_user") as mock_verify:
            mock_verify.return_value = MFAResult(ok=False, method="none")

            dep_func = RequireMFAIfEnabled().dependency

            with pytest.raises(HTTPException) as exc_info:
                await dep_func(
                    p=identity,
                    sess=session,
                    mfa=MFAProof(code="000000"),
                    mfa_code=None,
                    mfa_pre_token=None,
                )

            assert exc_info.value.status_code == 400
            assert "Invalid code" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_mfa_from_query_params(self) -> None:
        """Should accept MFA from query parameters."""
        user = FakeUser(mfa_enabled=True)
        identity = FakeIdentity(user)
        session = AsyncMock()

        with patch("svc_infra.api.fastapi.auth.mfa.security.verify_mfa_for_user") as mock_verify:
            mock_verify.return_value = MFAResult(ok=True, method="totp")

            dep_func = RequireMFAIfEnabled().dependency

            result = await dep_func(
                p=identity,
                sess=session,
                mfa=None,  # No body MFA
                mfa_code="123456",  # Query param
                mfa_pre_token=None,
            )

            assert result == identity
            # Should have constructed proof from query params
            call_args = mock_verify.call_args
            proof = call_args.kwargs.get("proof") or call_args[1].get("proof")
            assert proof is not None
            assert proof.code == "123456"

    @pytest.mark.asyncio
    async def test_mfa_enabled_no_proof_raises(self) -> None:
        """Should raise when MFA enabled but no proof provided."""
        user = FakeUser(mfa_enabled=True)
        identity = FakeIdentity(user)
        session = AsyncMock()

        with patch("svc_infra.api.fastapi.auth.mfa.security.verify_mfa_for_user") as mock_verify:
            mock_verify.return_value = MFAResult(ok=False, method="none")

            dep_func = RequireMFAIfEnabled().dependency

            with pytest.raises(HTTPException) as exc_info:
                await dep_func(
                    p=identity,
                    sess=session,
                    mfa=None,
                    mfa_code=None,
                    mfa_pre_token=None,
                )

            assert exc_info.value.status_code == 400
