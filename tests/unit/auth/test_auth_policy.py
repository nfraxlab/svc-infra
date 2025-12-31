"""Unit tests for svc_infra.api.fastapi.auth.policy module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from svc_infra.api.fastapi.auth.policy import DefaultAuthPolicy


class TestAuthPolicyProtocol:
    """Tests for AuthPolicy protocol."""

    def test_default_policy_conforms_to_protocol(self) -> None:
        """Test DefaultAuthPolicy implements AuthPolicy protocol."""
        settings = MagicMock()
        policy = DefaultAuthPolicy(settings)

        # Protocol conformance check
        assert hasattr(policy, "should_require_mfa")
        assert hasattr(policy, "on_login_success")
        assert hasattr(policy, "on_mfa_challenge")


class TestDefaultAuthPolicy:
    """Tests for DefaultAuthPolicy class."""

    def test_initialization(self) -> None:
        """Test policy initialization with settings."""
        settings = MagicMock()
        policy = DefaultAuthPolicy(settings)

        assert policy.settings is settings

    @pytest.mark.asyncio
    async def test_should_require_mfa_when_user_has_mfa_enabled(self) -> None:
        """Test MFA required when user has mfa_enabled=True."""
        settings = MagicMock()
        policy = DefaultAuthPolicy(settings)

        user = MagicMock()
        user.mfa_enabled = True

        result = await policy.should_require_mfa(user)

        assert result is True

    @pytest.mark.asyncio
    async def test_should_not_require_mfa_when_user_has_mfa_disabled(self) -> None:
        """Test MFA not required when user has mfa_enabled=False."""
        settings = MagicMock()
        policy = DefaultAuthPolicy(settings)

        user = MagicMock()
        user.mfa_enabled = False

        result = await policy.should_require_mfa(user)

        assert result is False

    @pytest.mark.asyncio
    async def test_should_not_require_mfa_when_attribute_missing(self) -> None:
        """Test MFA not required when mfa_enabled attribute is missing."""
        settings = MagicMock()
        policy = DefaultAuthPolicy(settings)

        # User without mfa_enabled attribute
        user = MagicMock(spec=[])

        result = await policy.should_require_mfa(user)

        assert result is False

    @pytest.mark.asyncio
    async def test_on_login_success_returns_none(self) -> None:
        """Test on_login_success is a no-op returning None."""
        settings = MagicMock()
        policy = DefaultAuthPolicy(settings)

        user = MagicMock()

        result = await policy.on_login_success(user)

        assert result is None

    @pytest.mark.asyncio
    async def test_on_mfa_challenge_returns_none(self) -> None:
        """Test on_mfa_challenge is a no-op returning None."""
        settings = MagicMock()
        policy = DefaultAuthPolicy(settings)

        user = MagicMock()

        result = await policy.on_mfa_challenge(user)

        assert result is None


class TestCustomAuthPolicy:
    """Tests for custom AuthPolicy implementations."""

    @pytest.mark.asyncio
    async def test_custom_policy_can_override_mfa_logic(self) -> None:
        """Test custom policy can override MFA requirement logic."""

        class TenantMfaPolicy:
            """Custom policy that requires MFA for all users in tenant."""

            def __init__(self, tenant_requires_mfa: bool):
                self.tenant_requires_mfa = tenant_requires_mfa

            async def should_require_mfa(self, user) -> bool:
                # Tenant-level override
                return self.tenant_requires_mfa or bool(getattr(user, "mfa_enabled", False))

            async def on_login_success(self, user) -> None:
                pass

            async def on_mfa_challenge(self, user) -> None:
                pass

        # Test tenant requires MFA
        policy = TenantMfaPolicy(tenant_requires_mfa=True)
        user = MagicMock()
        user.mfa_enabled = False

        result = await policy.should_require_mfa(user)

        assert result is True  # Tenant overrides user setting

    @pytest.mark.asyncio
    async def test_custom_policy_can_audit_logins(self) -> None:
        """Test custom policy can implement audit logging."""

        class AuditPolicy:
            """Custom policy that audits login events."""

            def __init__(self):
                self.login_count = 0
                self.challenge_count = 0

            async def should_require_mfa(self, user) -> bool:
                return False

            async def on_login_success(self, user) -> None:
                self.login_count += 1

            async def on_mfa_challenge(self, user) -> None:
                self.challenge_count += 1

        policy = AuditPolicy()
        user = MagicMock()

        await policy.on_login_success(user)
        await policy.on_login_success(user)
        await policy.on_mfa_challenge(user)

        assert policy.login_count == 2
        assert policy.challenge_count == 1
