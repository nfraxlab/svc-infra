"""Additional Security Coverage Tests for Phase 0.8.

Targets remaining uncovered lines in:
- signed_cookies.py: scope binding, edge cases
- audit.py: InMemoryAuditLogStore, append_audit_event without prev_event
- add.py: security configuration helpers
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from svc_infra.security.audit import (
    AuditEvent,
    InMemoryAuditLogStore,
    append_audit_event,
    verify_audit_chain,
)
from svc_infra.security.signed_cookies import (
    _b64d,
    _b64e,
    _now,
    _sign,
    sign_cookie,
    verify_cookie,
)

# ============== Signed Cookies Additional Tests ==============


class TestBase64Helpers:
    def test_b64e_basic(self) -> None:
        result = _b64e(b"hello")
        assert isinstance(result, str)
        assert result  # non-empty

    def test_b64d_basic(self) -> None:
        encoded = _b64e(b"hello")
        result = _b64d(encoded)
        assert result == b"hello"

    def test_b64d_padding_correction(self) -> None:
        # Test with different padding requirements
        for s in [b"a", b"ab", b"abc", b"abcd", b"abcde"]:
            encoded = _b64e(s)
            decoded = _b64d(encoded)
            assert decoded == s


class TestSign:
    def test_sign_produces_string(self) -> None:
        result = _sign(b"data", b"key")
        assert isinstance(result, str)
        assert result  # non-empty

    def test_sign_consistent(self) -> None:
        result1 = _sign(b"data", b"key")
        result2 = _sign(b"data", b"key")
        assert result1 == result2


class TestNow:
    def test_now_returns_int(self) -> None:
        result = _now()
        assert isinstance(result, int)
        assert result > 0


class TestSignCookieEdgeCases:
    def test_sign_cookie_with_path(self) -> None:
        val = sign_cookie({"user": "u1"}, key="k1", path="/api")
        ok, payload = verify_cookie(val, key="k1", expected_path="/api")
        assert ok
        assert payload is not None
        assert payload["_path"] == "/api"

    def test_sign_cookie_with_domain(self) -> None:
        val = sign_cookie({"user": "u1"}, key="k1", domain="example.com")
        ok, payload = verify_cookie(val, key="k1", expected_domain="example.com")
        assert ok
        assert payload is not None
        assert payload["_domain"] == "example.com"

    def test_sign_cookie_with_path_and_domain(self) -> None:
        val = sign_cookie({"user": "u1"}, key="k1", path="/api", domain="example.com")
        ok, _payload = verify_cookie(
            val, key="k1", expected_path="/api", expected_domain="example.com"
        )
        assert ok

    def test_verify_cookie_wrong_path(self) -> None:
        val = sign_cookie({"user": "u1"}, key="k1", path="/api")
        ok, payload = verify_cookie(val, key="k1", expected_path="/other")
        assert not ok
        assert payload is None

    def test_verify_cookie_wrong_domain(self) -> None:
        val = sign_cookie({"user": "u1"}, key="k1", domain="example.com")
        ok, payload = verify_cookie(val, key="k1", expected_domain="other.com")
        assert not ok
        assert payload is None

    def test_verify_cookie_empty_value(self) -> None:
        ok, payload = verify_cookie("", key="k1")
        assert not ok
        assert payload is None

    def test_verify_cookie_no_dot(self) -> None:
        ok, payload = verify_cookie("nodotvalue", key="k1")
        assert not ok
        assert payload is None

    def test_verify_cookie_exception_handling(self) -> None:
        # Malformed base64
        ok, payload = verify_cookie("!!!.sig", key="k1")
        assert not ok
        assert payload is None

    def test_verify_cookie_with_old_key(self) -> None:
        val = sign_cookie({"sub": "u"}, key="old_key")
        ok, payload = verify_cookie(val, key="new_key", old_keys=["old_key"])
        assert ok
        assert payload is not None

    def test_verify_cookie_none_old_keys(self) -> None:
        val = sign_cookie({"sub": "u"}, key="correct_key")
        ok, _payload = verify_cookie(val, key="correct_key", old_keys=None)
        assert ok


# ============== InMemoryAuditLogStore Tests ==============


class TestInMemoryAuditLogStore:
    def test_append_basic(self) -> None:
        store = InMemoryAuditLogStore()
        event = store.append(event_type="test_event")
        assert event.event_type == "test_event"
        assert event.ts is not None
        assert event.metadata == {}

    def test_append_with_all_fields(self) -> None:
        store = InMemoryAuditLogStore()
        ts = datetime.now(UTC)
        actor_id = uuid.uuid4()
        event = store.append(
            actor_id=actor_id,
            tenant_id="t1",
            event_type="login",
            resource_ref="user:123",
            metadata={"ip": "1.2.3.4"},
            ts=ts,
        )
        assert event.actor_id == actor_id
        assert event.tenant_id == "t1"
        assert event.event_type == "login"
        assert event.resource_ref == "user:123"
        assert event.metadata == {"ip": "1.2.3.4"}
        assert event.ts == ts

    def test_list_all(self) -> None:
        store = InMemoryAuditLogStore()
        store.append(event_type="e1")
        store.append(event_type="e2")
        store.append(event_type="e3")
        events = store.list()
        assert len(events) == 3

    def test_list_by_tenant(self) -> None:
        store = InMemoryAuditLogStore()
        store.append(event_type="e1", tenant_id="t1")
        store.append(event_type="e2", tenant_id="t2")
        store.append(event_type="e3", tenant_id="t1")
        events = store.list(tenant_id="t1")
        assert len(events) == 2
        assert all(e.tenant_id == "t1" for e in events)

    def test_list_with_limit(self) -> None:
        store = InMemoryAuditLogStore()
        for i in range(5):
            store.append(event_type=f"e{i}")
        events = store.list(limit=3)
        assert len(events) == 3
        # Should return last 3 events
        assert events[0].event_type == "e2"
        assert events[1].event_type == "e3"
        assert events[2].event_type == "e4"

    def test_list_tenant_and_limit(self) -> None:
        store = InMemoryAuditLogStore()
        for i in range(5):
            store.append(event_type=f"e{i}", tenant_id="t1")
        store.append(event_type="other", tenant_id="t2")
        events = store.list(tenant_id="t1", limit=2)
        assert len(events) == 2
        assert all(e.tenant_id == "t1" for e in events)


class TestAuditEvent:
    def test_audit_event_dataclass(self) -> None:
        ts = datetime.now(UTC)
        event = AuditEvent(
            ts=ts,
            actor_id=uuid.uuid4(),
            tenant_id="t1",
            event_type="test",
            resource_ref="ref",
            metadata={"key": "value"},
        )
        assert event.ts == ts
        assert event.tenant_id == "t1"
        assert event.event_type == "test"


# ============== Append Audit Event Additional Tests ==============


class FakeDB:
    def __init__(self) -> None:
        self.added: list[Any] = []

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        pass


class FakeDBWithExecute:
    def __init__(self, return_event: Any = None) -> None:
        self.added: list[Any] = []
        self.return_event = return_event

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        pass

    async def execute(self, stmt: Any) -> Any:
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = self.return_event
        mock_result.scalars.return_value = mock_scalars
        return mock_result


class TestAppendAuditEventEdgeCases:
    @pytest.mark.asyncio
    async def test_append_without_prev_event_no_db_lookup(self) -> None:
        db = FakeDB()
        event = await append_audit_event(
            db,
            event_type="test",
            metadata=None,  # Test None metadata
        )
        assert event.event_type == "test"
        assert event.prev_hash == "0" * 64  # Genesis event

    @pytest.mark.asyncio
    async def test_append_with_custom_ts(self) -> None:
        db = FakeDB()
        custom_ts = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        event = await append_audit_event(db, event_type="test", ts=custom_ts)
        assert event.ts == custom_ts

    @pytest.mark.asyncio
    async def test_append_with_all_fields(self) -> None:
        db = FakeDB()
        actor_id = uuid.uuid4()
        event = await append_audit_event(
            db,
            actor_id=actor_id,
            tenant_id="tenant_1",
            event_type="user_action",
            resource_ref="resource:abc",
            metadata={"action": "update"},
        )
        assert event.actor_id == actor_id
        assert event.tenant_id == "tenant_1"
        assert event.resource_ref == "resource:abc"
        assert event.event_metadata == {"action": "update"}


# ============== Verify Audit Chain Additional Tests ==============


class MockAuditLog:
    def __init__(
        self,
        ts: datetime,
        actor_id: Any,
        tenant_id: str | None,
        event_type: str,
        resource_ref: str | None,
        event_metadata: dict,
        prev_hash: str,
        hash_value: str,
    ) -> None:
        self.ts = ts
        self.actor_id = actor_id
        self.tenant_id = tenant_id
        self.event_type = event_type
        self.resource_ref = resource_ref
        self.event_metadata = event_metadata
        self.prev_hash = prev_hash
        self.hash = hash_value


class TestVerifyAuditChainEdgeCases:
    def test_verify_empty_chain(self) -> None:
        ok, broken = verify_audit_chain([])
        assert ok is True
        assert broken == []

    def test_verify_genesis_with_wrong_prev_hash(self) -> None:
        from svc_infra.security.models import compute_audit_hash

        ts = datetime.now(UTC)
        # Genesis should have prev_hash of zeros
        correct_hash = compute_audit_hash(
            "0" * 64,
            ts=ts,
            actor_id=None,
            tenant_id=None,
            event_type="test",
            resource_ref=None,
            metadata={},
        )
        # Create event with wrong prev_hash (not zeros)
        event = MockAuditLog(
            ts=ts,
            actor_id=None,
            tenant_id=None,
            event_type="test",
            resource_ref=None,
            event_metadata={},
            prev_hash="1" * 64,  # Wrong - should be zeros
            hash_value=correct_hash,
        )
        ok, broken = verify_audit_chain([event])
        assert ok is False
        assert 0 in broken

    def test_verify_chain_with_broken_link(self) -> None:
        from svc_infra.security.models import compute_audit_hash

        ts1 = datetime.now(UTC)
        hash1 = compute_audit_hash(
            "0" * 64,
            ts=ts1,
            actor_id=None,
            tenant_id=None,
            event_type="e1",
            resource_ref=None,
            metadata={},
        )
        event1 = MockAuditLog(
            ts=ts1,
            actor_id=None,
            tenant_id=None,
            event_type="e1",
            resource_ref=None,
            event_metadata={},
            prev_hash="0" * 64,
            hash_value=hash1,
        )

        ts2 = datetime.now(UTC)
        hash2 = compute_audit_hash(
            hash1,
            ts=ts2,
            actor_id=None,
            tenant_id=None,
            event_type="e2",
            resource_ref=None,
            metadata={},
        )
        # Create event2 with wrong prev_hash
        event2 = MockAuditLog(
            ts=ts2,
            actor_id=None,
            tenant_id=None,
            event_type="e2",
            resource_ref=None,
            event_metadata={},
            prev_hash="wrong" + "0" * 59,  # Wrong prev_hash
            hash_value=hash2,
        )

        ok, broken = verify_audit_chain([event1, event2])
        assert ok is False
        assert 1 in broken
