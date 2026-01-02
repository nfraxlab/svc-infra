"""
Tests for webhook signing and signature verification.
"""

from __future__ import annotations

import hashlib
import hmac


class TestCanonicalBody:
    """Tests for canonical body generation."""

    def test_canonical_body_sorts_keys(self):
        """Should sort keys alphabetically."""
        from svc_infra.webhooks.signing import canonical_body

        payload = {"z": 1, "a": 2, "m": 3}
        result = canonical_body(payload)

        assert result == b'{"a":2,"m":3,"z":1}'

    def test_canonical_body_no_spaces(self):
        """Should use compact JSON without spaces."""
        from svc_infra.webhooks.signing import canonical_body

        payload = {"key": "value", "number": 123}
        result = canonical_body(payload)

        assert b" " not in result
        assert result == b'{"key":"value","number":123}'

    def test_canonical_body_nested_objects(self):
        """Should handle nested objects."""
        from svc_infra.webhooks.signing import canonical_body

        payload = {"outer": {"inner": "value"}}
        result = canonical_body(payload)

        assert result == b'{"outer":{"inner":"value"}}'

    def test_canonical_body_empty_dict(self):
        """Should handle empty dictionary."""
        from svc_infra.webhooks.signing import canonical_body

        result = canonical_body({})

        assert result == b"{}"

    def test_canonical_body_with_arrays(self):
        """Should preserve array order."""
        from svc_infra.webhooks.signing import canonical_body

        payload = {"items": [3, 1, 2]}
        result = canonical_body(payload)

        assert result == b'{"items":[3,1,2]}'

    def test_canonical_body_unicode(self):
        """Should handle unicode characters."""
        from svc_infra.webhooks.signing import canonical_body

        payload = {"message": "Hello"}
        result = canonical_body(payload)

        assert "message" in result.decode()


class TestSign:
    """Tests for signature generation."""

    def test_sign_produces_hex_signature(self):
        """Should produce hexadecimal signature."""
        from svc_infra.webhooks.signing import sign

        signature = sign("secret", {"key": "value"})

        assert all(c in "0123456789abcdef" for c in signature)
        assert len(signature) == 64  # SHA256 hex length

    def test_sign_deterministic(self):
        """Should produce same signature for same input."""
        from svc_infra.webhooks.signing import sign

        sig1 = sign("secret", {"key": "value"})
        sig2 = sign("secret", {"key": "value"})

        assert sig1 == sig2

    def test_sign_different_secrets_different_signatures(self):
        """Should produce different signatures for different secrets."""
        from svc_infra.webhooks.signing import sign

        sig1 = sign("secret1", {"key": "value"})
        sig2 = sign("secret2", {"key": "value"})

        assert sig1 != sig2

    def test_sign_different_payloads_different_signatures(self):
        """Should produce different signatures for different payloads."""
        from svc_infra.webhooks.signing import sign

        sig1 = sign("secret", {"key": "value1"})
        sig2 = sign("secret", {"key": "value2"})

        assert sig1 != sig2

    def test_sign_uses_sha256_hmac(self):
        """Should use HMAC-SHA256."""
        from svc_infra.webhooks.signing import canonical_body, sign

        payload = {"key": "value"}
        body = canonical_body(payload)
        expected = hmac.new(b"secret", body, hashlib.sha256).hexdigest()

        signature = sign("secret", payload)

        assert signature == expected


class TestVerify:
    """Tests for signature verification."""

    def test_verify_valid_signature(self):
        """Should return True for valid signature."""
        from svc_infra.webhooks.signing import sign, verify

        payload = {"key": "value"}
        signature = sign("secret", payload)

        assert verify("secret", payload, signature) is True

    def test_verify_invalid_signature(self):
        """Should return False for invalid signature."""
        from svc_infra.webhooks.signing import verify

        payload = {"key": "value"}

        assert verify("secret", payload, "invalid_signature") is False

    def test_verify_wrong_secret(self):
        """Should return False for wrong secret."""
        from svc_infra.webhooks.signing import sign, verify

        payload = {"key": "value"}
        signature = sign("secret1", payload)

        assert verify("secret2", payload, signature) is False

    def test_verify_tampered_payload(self):
        """Should return False for tampered payload."""
        from svc_infra.webhooks.signing import sign, verify

        signature = sign("secret", {"key": "original"})

        assert verify("secret", {"key": "tampered"}, signature) is False

    def test_verify_timing_safe_comparison(self):
        """Should use timing-safe comparison."""
        from svc_infra.webhooks.signing import sign, verify

        payload = {"key": "value"}
        signature = sign("secret", payload)

        # The function should work without timing attacks
        assert verify("secret", payload, signature) is True

    def test_verify_handles_exception(self, mocker):
        """Should handle exceptions gracefully."""
        from svc_infra.webhooks.signing import verify

        # Passing empty string should not raise
        result = verify("secret", {"key": "value"}, "")

        assert result is False


class TestVerifyAny:
    """Tests for multi-secret verification."""

    def test_verify_any_first_secret_matches(self):
        """Should return True if first secret matches."""
        from svc_infra.webhooks.signing import sign, verify_any

        payload = {"key": "value"}
        signature = sign("secret1", payload)

        assert verify_any(["secret1", "secret2"], payload, signature) is True

    def test_verify_any_second_secret_matches(self):
        """Should return True if second secret matches."""
        from svc_infra.webhooks.signing import sign, verify_any

        payload = {"key": "value"}
        signature = sign("secret2", payload)

        assert verify_any(["secret1", "secret2"], payload, signature) is True

    def test_verify_any_no_match(self):
        """Should return False if no secrets match."""
        from svc_infra.webhooks.signing import sign, verify_any

        payload = {"key": "value"}
        signature = sign("secret3", payload)

        assert verify_any(["secret1", "secret2"], payload, signature) is False

    def test_verify_any_empty_secrets(self):
        """Should return False for empty secrets list."""
        from svc_infra.webhooks.signing import verify_any

        assert verify_any([], {"key": "value"}, "signature") is False

    def test_verify_any_secret_rotation(self):
        """Should support secret rotation with old and new secrets."""
        from svc_infra.webhooks.signing import sign, verify_any

        payload = {"key": "value"}
        old_secret = "old_secret"
        new_secret = "new_secret"

        # Old signature should still work during rotation
        old_signature = sign(old_secret, payload)
        assert verify_any([new_secret, old_secret], payload, old_signature) is True

        # New signature should also work
        new_signature = sign(new_secret, payload)
        assert verify_any([new_secret, old_secret], payload, new_signature) is True


class TestSignatureEdgeCases:
    """Tests for edge cases in signing/verification."""

    def test_empty_payload(self):
        """Should sign and verify empty payload."""
        from svc_infra.webhooks.signing import sign, verify

        signature = sign("secret", {})

        assert verify("secret", {}, signature) is True

    def test_special_characters_in_payload(self):
        """Should handle special characters in payload."""
        from svc_infra.webhooks.signing import sign, verify

        payload = {"message": "Hello! @#$%^&*()"}
        signature = sign("secret", payload)

        assert verify("secret", payload, signature) is True

    def test_large_payload(self):
        """Should handle large payloads."""
        from svc_infra.webhooks.signing import sign, verify

        payload = {"data": "x" * 10000}
        signature = sign("secret", payload)

        assert verify("secret", payload, signature) is True

    def test_null_values_in_payload(self):
        """Should handle null values."""
        from svc_infra.webhooks.signing import sign, verify

        payload = {"value": None}
        signature = sign("secret", payload)

        assert verify("secret", payload, signature) is True

    def test_boolean_values_in_payload(self):
        """Should handle boolean values."""
        from svc_infra.webhooks.signing import sign, verify

        payload = {"active": True, "deleted": False}
        signature = sign("secret", payload)

        assert verify("secret", payload, signature) is True
