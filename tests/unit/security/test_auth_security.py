"""Auth Security tests for Phase 0.8 Priority 5.

Coverage targets:
- hibp.py: range_query, is_breached, caching
- lockout.py: record_attempt, get_lockout_status async
- jwt_rotation.py: read_token with user_manager
- permissions.py: register_role, extend_role, ABAC, RequirePermission
"""

from __future__ import annotations

import hashlib
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi_users.authentication.strategy.jwt import JWTStrategy

from svc_infra.security.hibp import CacheEntry, HIBPClient, sha1_hex
from svc_infra.security.jwt_rotation import RotatingJWTStrategy
from svc_infra.security.lockout import (
    LockoutConfig,
    compute_lockout,
    get_lockout_status,
    record_attempt,
)
from svc_infra.security.permissions import (
    PERMISSION_REGISTRY,
    RequireABAC,
    RequireAnyPermission,
    RequirePermission,
    _maybe_await,
    enforce_abac,
    extend_role,
    owns_resource,
    principal_permissions,
    register_role,
)

# ============== HIBP Tests ==============


class TestSha1Hex:
    def test_sha1_hex_basic(self) -> None:
        result = sha1_hex("password")
        expected = hashlib.sha1(b"password").hexdigest().upper()
        assert result == expected

    def test_sha1_hex_unicode(self) -> None:
        result = sha1_hex("paSSw0rd!")
        assert len(result) == 40
        assert result.isupper()


class TestCacheEntry:
    def test_cache_entry_creation(self) -> None:
        entry = CacheEntry(body="test_body", expires_at=time.time() + 100)
        assert entry.body == "test_body"
        assert entry.expires_at > time.time()


class TestHIBPClient:
    def test_init_defaults(self) -> None:
        client = HIBPClient()
        assert client.base_url == "https://api.pwnedpasswords.com"
        assert client.ttl_seconds == 3600
        assert client.timeout == 5.0

    def test_init_custom(self) -> None:
        client = HIBPClient(
            base_url="https://custom.api.com/",
            ttl_seconds=1800,
            timeout=10.0,
            user_agent="test-agent",
        )
        assert client.base_url == "https://custom.api.com"
        assert client.ttl_seconds == 1800
        assert client.timeout == 10.0
        assert client.user_agent == "test-agent"

    def test_get_cached_miss(self) -> None:
        client = HIBPClient()
        assert client._get_cached("ABCDE") is None

    def test_get_cached_hit(self) -> None:
        client = HIBPClient()
        client._cache["ABCDE"] = CacheEntry(body="cached_body", expires_at=time.time() + 100)
        assert client._get_cached("ABCDE") == "cached_body"

    def test_get_cached_expired(self) -> None:
        client = HIBPClient()
        client._cache["ABCDE"] = CacheEntry(body="expired_body", expires_at=time.time() - 100)
        assert client._get_cached("ABCDE") is None

    def test_set_cache(self) -> None:
        client = HIBPClient(ttl_seconds=60)
        client._set_cache("FGHIJ", "new_body")
        assert "FGHIJ" in client._cache
        assert client._cache["FGHIJ"].body == "new_body"
        assert client._cache["FGHIJ"].expires_at > time.time()

    def test_range_query_uses_cache(self) -> None:
        client = HIBPClient()
        client._cache["ABCDE"] = CacheEntry(body="cached_response", expires_at=time.time() + 100)
        result = client.range_query("ABCDE")
        assert result == "cached_response"

    def test_range_query_network_call(self) -> None:
        client = HIBPClient()
        mock_response = MagicMock()
        mock_response.text = "SUFFIX1:10\nSUFFIX2:5"
        mock_response.raise_for_status = MagicMock()
        client._http = MagicMock()
        client._http.get.return_value = mock_response

        result = client.range_query("ABCDE")
        assert result == "SUFFIX1:10\nSUFFIX2:5"
        client._http.get.assert_called_once()
        # Should be cached now
        assert "ABCDE" in client._cache

    def test_is_breached_found(self) -> None:
        client = HIBPClient()
        password = "password123"
        full_hash = sha1_hex(password)
        _, suffix = full_hash[:5], full_hash[5:]
        # Mock range_query to return the suffix
        client.range_query = MagicMock(return_value=f"{suffix}:42\nOTHER:1")
        result = client.is_breached(password)
        assert result is True

    def test_is_breached_not_found(self) -> None:
        client = HIBPClient()
        client.range_query = MagicMock(return_value="NOTMATCH:5\nALSONOT:2")
        result = client.is_breached("unique_password_abc123")
        assert result is False

    def test_is_breached_fail_open(self) -> None:
        client = HIBPClient()
        client.range_query = MagicMock(side_effect=Exception("Network error"))
        # Should fail open (return False on error)
        result = client.is_breached("any_password")
        assert result is False

    def test_is_breached_empty_line(self) -> None:
        client = HIBPClient()
        client.range_query = MagicMock(return_value="SUFFIX:10\n\nANOTHER:5")
        result = client.is_breached("test_password")
        assert isinstance(result, bool)

    def test_is_breached_malformed_line(self) -> None:
        client = HIBPClient()
        client.range_query = MagicMock(return_value="INVALID_LINE\nSUFFIX:10")
        result = client.is_breached("test_password")
        assert isinstance(result, bool)

    def test_is_breached_count_zero(self) -> None:
        client = HIBPClient()
        password = "test"
        full_hash = sha1_hex(password)
        suffix = full_hash[5:]
        client.range_query = MagicMock(return_value=f"{suffix}:0")
        # Count 0 should return False
        result = client.is_breached(password)
        assert result is False

    def test_is_breached_invalid_count(self) -> None:
        client = HIBPClient()
        password = "test"
        full_hash = sha1_hex(password)
        suffix = full_hash[5:]
        client.range_query = MagicMock(return_value=f"{suffix}:invalid")
        # Invalid count should return True (fail safe)
        result = client.is_breached(password)
        assert result is True


# ============== Lockout Tests ==============


class MockFailedAuthAttempt:
    def __init__(self, user_id: uuid.UUID | None, ip_hash: str | None, success: bool) -> None:
        self.user_id = user_id
        self.ip_hash = ip_hash
        self.success = success
        self.ts = datetime.now(UTC)


class TestRecordAttempt:
    @pytest.mark.asyncio
    async def test_record_attempt_adds_to_session(self) -> None:
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        user_id = uuid.uuid4()
        await record_attempt(mock_session, user_id=user_id, ip_hash="abc123", success=False)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_record_attempt_success(self) -> None:
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        await record_attempt(mock_session, user_id=None, ip_hash="xyz789", success=True)

        mock_session.add.assert_called_once()


class TestGetLockoutStatus:
    @pytest.mark.asyncio
    async def test_get_lockout_status_no_failures(self) -> None:
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        status = await get_lockout_status(mock_session, user_id=uuid.uuid4(), ip_hash="test_hash")

        assert status.locked is False
        assert status.failure_count == 0

    @pytest.mark.asyncio
    async def test_get_lockout_status_at_threshold(self) -> None:
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        # Return 5 failures (at threshold)
        mock_scalars.all.return_value = [MagicMock() for _ in range(5)]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        cfg = LockoutConfig(threshold=5)
        status = await get_lockout_status(
            mock_session, user_id=uuid.uuid4(), ip_hash="test_hash", cfg=cfg
        )

        assert status.locked is True
        assert status.failure_count == 5

    @pytest.mark.asyncio
    async def test_get_lockout_status_user_id_only(self) -> None:
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        status = await get_lockout_status(mock_session, user_id=uuid.uuid4(), ip_hash=None)

        assert status.locked is False

    @pytest.mark.asyncio
    async def test_get_lockout_status_ip_hash_only(self) -> None:
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        status = await get_lockout_status(mock_session, user_id=None, ip_hash="hash123")

        assert status.locked is False

    @pytest.mark.asyncio
    async def test_get_lockout_status_no_filters(self) -> None:
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        status = await get_lockout_status(mock_session, user_id=None, ip_hash=None)

        assert status.locked is False


class TestComputeLockoutEdgeCases:
    def test_compute_lockout_uses_current_time_if_none(self) -> None:
        cfg = LockoutConfig(threshold=3, base_cooldown_seconds=10)
        before = datetime.now(UTC)
        status = compute_lockout(3, cfg=cfg, now=None)
        after = datetime.now(UTC)

        assert status.locked is True
        assert status.next_allowed_at is not None
        # next_allowed_at should be between before + 10s and after + 10s
        assert status.next_allowed_at >= before + timedelta(seconds=10)
        assert status.next_allowed_at <= after + timedelta(seconds=10)


# ============== JWT Rotation Tests ==============


class TestRotatingJWTStrategyReadToken:
    @pytest.mark.asyncio
    async def test_read_token_none_returns_none(self) -> None:
        rot = RotatingJWTStrategy(secret="secret", lifetime_seconds=60, token_audience="test")
        result = await rot.read_token(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_read_token_with_audience_list(self) -> None:
        rot = RotatingJWTStrategy(
            secret="secret", lifetime_seconds=60, token_audience=["aud1", "aud2"]
        )
        user = type("U", (), {"id": "user-test"})()
        token = await rot.write_token(user)
        claims = await rot.read_token(token, audience=["aud1", "aud2"])
        assert claims is not None

    @pytest.mark.asyncio
    async def test_read_token_with_user_manager_primary(self) -> None:
        secret = "test-secret"
        rot = RotatingJWTStrategy(secret=secret, lifetime_seconds=60, token_audience="test")
        user = type("U", (), {"id": str(uuid.uuid4())})()
        token = await rot.write_token(user)

        # Mock user_manager
        mock_user_manager = AsyncMock()
        mock_user = MagicMock(id=user.id)
        # Patch parent's read_token to return user
        with patch.object(JWTStrategy, "read_token", new_callable=AsyncMock) as mock_parent:
            mock_parent.return_value = mock_user
            result = await rot.read_token(token, mock_user_manager)
            assert result is not None

    @pytest.mark.asyncio
    async def test_read_token_with_user_manager_old_secret(self) -> None:
        old_secret = "old-secret"
        new_secret = "new-secret"

        # Issue with old secret
        issuer = JWTStrategy(secret=old_secret, lifetime_seconds=60, token_audience="test")
        user = type("U", (), {"id": str(uuid.uuid4())})()
        token = await issuer.write_token(user)

        rot = RotatingJWTStrategy(
            secret=new_secret,
            lifetime_seconds=60,
            old_secrets=[old_secret],
            token_audience="test",
        )

        # Mock user_manager
        mock_user_manager = AsyncMock()
        mock_user = MagicMock(id=user.id)

        # First call (primary) returns None, second (old) returns user
        with patch.object(JWTStrategy, "read_token", new_callable=AsyncMock) as mock_parent:
            mock_parent.side_effect = [None, mock_user]
            result = await rot.read_token(token, mock_user_manager)
            assert result is not None

    @pytest.mark.asyncio
    async def test_read_token_with_user_manager_all_fail(self) -> None:
        rot = RotatingJWTStrategy(
            secret="new-secret",
            lifetime_seconds=60,
            old_secrets=["old-secret"],
            token_audience="test",
        )

        mock_user_manager = AsyncMock()

        with patch.object(JWTStrategy, "read_token", new_callable=AsyncMock) as mock_parent:
            mock_parent.return_value = None
            result = await rot.read_token("invalid-token", mock_user_manager)
            assert result is None

    @pytest.mark.asyncio
    async def test_rotating_jwt_no_old_secrets(self) -> None:
        rot = RotatingJWTStrategy(secret="only-secret", lifetime_seconds=60, token_audience=None)
        assert rot._verify_secrets == ["only-secret"]


# ============== Permissions Tests ==============


class DummyUser:
    def __init__(self, roles: list[str], uid: uuid.UUID | None = None) -> None:
        self.id = uid or uuid.uuid4()
        self.roles = roles


class DummyPrincipal:
    def __init__(self, user: DummyUser) -> None:
        self.user = user


class TestRegisterRole:
    def test_register_role_new(self) -> None:
        register_role("test_role_1", {"perm.a", "perm.b"})
        assert "test_role_1" in PERMISSION_REGISTRY
        assert PERMISSION_REGISTRY["test_role_1"] == {"perm.a", "perm.b"}
        # Cleanup
        del PERMISSION_REGISTRY["test_role_1"]

    def test_register_role_overwrite(self) -> None:
        register_role("test_role_2", {"old.perm"})
        register_role("test_role_2", {"new.perm"})
        assert PERMISSION_REGISTRY["test_role_2"] == {"new.perm"}
        del PERMISSION_REGISTRY["test_role_2"]


class TestExtendRole:
    def test_extend_role_existing(self) -> None:
        register_role("test_role_3", {"base.perm"})
        extend_role("test_role_3", {"extra.perm"})
        assert PERMISSION_REGISTRY["test_role_3"] == {"base.perm", "extra.perm"}
        del PERMISSION_REGISTRY["test_role_3"]

    def test_extend_role_new(self) -> None:
        extend_role("test_role_4", {"new.perm"})
        assert PERMISSION_REGISTRY["test_role_4"] == {"new.perm"}
        del PERMISSION_REGISTRY["test_role_4"]


class TestPrincipalPermissions:
    def test_principal_permissions_with_roles(self) -> None:
        user = DummyUser(roles=["admin"])
        principal = DummyPrincipal(user)
        perms = principal_permissions(principal)
        assert "user.read" in perms
        assert "admin.impersonate" in perms

    def test_principal_permissions_no_roles_attr(self) -> None:
        user = type("U", (), {"id": uuid.uuid4()})()  # No roles attr
        principal = DummyPrincipal(user)
        perms = principal_permissions(principal)
        assert perms == set()

    def test_principal_permissions_none_roles(self) -> None:
        user = type("U", (), {"id": uuid.uuid4(), "roles": None})()
        principal = DummyPrincipal(user)
        perms = principal_permissions(principal)
        assert perms == set()


class TestMaybeAwait:
    @pytest.mark.asyncio
    async def test_maybe_await_sync_value(self) -> None:
        result = await _maybe_await(42)
        assert result == 42

    @pytest.mark.asyncio
    async def test_maybe_await_async_value(self) -> None:
        async def async_fn() -> int:
            return 100

        result = await _maybe_await(async_fn())
        assert result == 100


class TestOwnsResource:
    def test_owns_resource_match(self) -> None:
        uid = uuid.uuid4()
        user = DummyUser(roles=[], uid=uid)
        principal = DummyPrincipal(user)
        resource = type("R", (), {"owner_id": uid})()
        predicate = owns_resource()
        assert predicate(principal, resource) is True

    def test_owns_resource_no_match(self) -> None:
        user = DummyUser(roles=[], uid=uuid.uuid4())
        principal = DummyPrincipal(user)
        resource = type("R", (), {"owner_id": uuid.uuid4()})()
        predicate = owns_resource()
        assert predicate(principal, resource) is False

    def test_owns_resource_custom_attr(self) -> None:
        uid = uuid.uuid4()
        user = DummyUser(roles=[], uid=uid)
        principal = DummyPrincipal(user)
        resource = type("R", (), {"author_id": uid})()
        predicate = owns_resource("author_id")
        assert predicate(principal, resource) is True

    def test_owns_resource_fallback_user_id(self) -> None:
        uid = uuid.uuid4()
        user = DummyUser(roles=[], uid=uid)
        principal = DummyPrincipal(user)
        # No owner_id attr, but has user_id
        resource = type("R", (), {"user_id": uid})()
        predicate = owns_resource()
        assert predicate(principal, resource) is True

    def test_owns_resource_missing_attrs(self) -> None:
        user = DummyUser(roles=[], uid=uuid.uuid4())
        principal = DummyPrincipal(user)
        resource = type("R", (), {})()  # No owner_id or user_id
        predicate = owns_resource()
        assert predicate(principal, resource) is False

    def test_owns_resource_none_user_id(self) -> None:
        user = type("U", (), {"id": None, "roles": []})()
        principal = DummyPrincipal(user)
        resource = type("R", (), {"owner_id": uuid.uuid4()})()
        predicate = owns_resource()
        assert predicate(principal, resource) is False


class TestEnforceABAC:
    def test_enforce_abac_success(self) -> None:
        user = DummyUser(roles=["admin"])
        principal = DummyPrincipal(user)
        resource = type("R", (), {"owner_id": user.id})()

        result = enforce_abac(
            principal,
            permission="user.read",
            resource=resource,
            predicate=owns_resource(),
        )
        assert result is principal

    def test_enforce_abac_missing_permission(self) -> None:
        user = DummyUser(roles=[])  # No roles
        principal = DummyPrincipal(user)
        resource = type("R", (), {"owner_id": user.id})()

        with pytest.raises(HTTPException) as exc:
            enforce_abac(
                principal,
                permission="user.read",
                resource=resource,
                predicate=owns_resource(),
            )
        assert exc.value.status_code == 403
        assert "missing_permissions" in exc.value.detail

    def test_enforce_abac_predicate_fails(self) -> None:
        user = DummyUser(roles=["admin"])
        principal = DummyPrincipal(user)
        resource = type("R", (), {"owner_id": uuid.uuid4()})()  # Different owner

        with pytest.raises(HTTPException) as exc:
            enforce_abac(
                principal,
                permission="user.read",
                resource=resource,
                predicate=owns_resource(),
            )
        assert exc.value.status_code == 403
        assert "forbidden" in exc.value.detail

    def test_enforce_abac_async_predicate_raises(self) -> None:
        user = DummyUser(roles=["admin"])
        principal = DummyPrincipal(user)
        resource = type("R", (), {})()

        async def async_predicate(p: Any, r: Any) -> bool:
            return True

        with pytest.raises(RuntimeError) as exc:
            enforce_abac(
                principal,
                permission="user.read",
                resource=resource,
                predicate=async_predicate,
            )
        assert "async predicate" in str(exc.value)


class TestRequirePermission:
    @pytest.mark.asyncio
    async def test_require_permission_success(self) -> None:
        user = DummyUser(roles=["admin"])
        principal = DummyPrincipal(user)

        guard = RequirePermission("user.read")
        # Extract the dependency callable
        dep = guard.dependency

        result = await dep(principal)
        assert result is principal

    @pytest.mark.asyncio
    async def test_require_permission_missing(self) -> None:
        user = DummyUser(roles=[])
        principal = DummyPrincipal(user)

        guard = RequirePermission("user.read")
        dep = guard.dependency

        with pytest.raises(HTTPException) as exc:
            await dep(principal)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_multiple_permissions(self) -> None:
        user = DummyUser(roles=["admin"])
        principal = DummyPrincipal(user)

        guard = RequirePermission("user.read", "user.write")
        dep = guard.dependency

        result = await dep(principal)
        assert result is principal

    @pytest.mark.asyncio
    async def test_require_any_permission_success(self) -> None:
        user = DummyUser(roles=["support"])  # Has user.read, billing.read
        principal = DummyPrincipal(user)

        guard = RequireAnyPermission("user.read", "admin.impersonate")
        dep = guard.dependency

        result = await dep(principal)
        assert result is principal

    @pytest.mark.asyncio
    async def test_require_any_permission_none_match(self) -> None:
        user = DummyUser(roles=["support"])
        principal = DummyPrincipal(user)

        guard = RequireAnyPermission("admin.impersonate", "security.session.revoke")
        dep = guard.dependency

        with pytest.raises(HTTPException) as exc:
            await dep(principal)
        assert exc.value.status_code == 403


class TestRequireABAC:
    @pytest.mark.asyncio
    async def test_require_abac_success(self) -> None:
        uid = uuid.uuid4()
        user = DummyUser(roles=["admin"], uid=uid)
        principal = DummyPrincipal(user)
        resource = type("R", (), {"owner_id": uid})()

        def getter() -> Any:
            return resource

        guard = RequireABAC(
            permission="user.read", predicate=owns_resource(), resource_getter=getter
        )
        dep = guard.dependency

        result = await dep(principal, resource)
        assert result is principal

    @pytest.mark.asyncio
    async def test_require_abac_missing_permission(self) -> None:
        user = DummyUser(roles=[])
        principal = DummyPrincipal(user)
        resource = type("R", (), {"owner_id": user.id})()

        def getter() -> Any:
            return resource

        guard = RequireABAC(
            permission="user.read", predicate=owns_resource(), resource_getter=getter
        )
        dep = guard.dependency

        with pytest.raises(HTTPException) as exc:
            await dep(principal, resource)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_abac_predicate_fails(self) -> None:
        user = DummyUser(roles=["admin"])
        principal = DummyPrincipal(user)
        resource = type("R", (), {"owner_id": uuid.uuid4()})()

        def getter() -> Any:
            return resource

        guard = RequireABAC(
            permission="user.read", predicate=owns_resource(), resource_getter=getter
        )
        dep = guard.dependency

        with pytest.raises(HTTPException) as exc:
            await dep(principal, resource)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_abac_async_predicate(self) -> None:
        uid = uuid.uuid4()
        user = DummyUser(roles=["admin"], uid=uid)
        principal = DummyPrincipal(user)
        resource = type("R", (), {"owner_id": uid})()

        async def async_predicate(p: Any, r: Any) -> bool:
            return str(p.user.id) == str(r.owner_id)

        def getter() -> Any:
            return resource

        guard = RequireABAC(
            permission="user.read", predicate=async_predicate, resource_getter=getter
        )
        dep = guard.dependency

        result = await dep(principal, resource)
        assert result is principal
