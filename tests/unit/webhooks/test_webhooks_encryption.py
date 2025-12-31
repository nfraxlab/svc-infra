"""Unit tests for svc_infra.webhooks.encryption module."""

from __future__ import annotations

from svc_infra.webhooks.encryption import (
    _ENCRYPTED_PREFIX,
    decrypt_secret,
    encrypt_secret,
)


class TestEncryptSecret:
    """Tests for encrypt_secret function."""

    def test_encrypts_secret(self) -> None:
        """Test that secret gets encrypted."""
        result = encrypt_secret("my_secret")
        assert result.startswith(_ENCRYPTED_PREFIX)
        assert result != "my_secret"

    def test_encrypted_value_is_different_each_time(self) -> None:
        """Test that encryption includes random component (nonce)."""
        encrypted1 = encrypt_secret("same_secret")
        encrypted2 = encrypt_secret("same_secret")
        # Fernet uses random IV so same plaintext produces different ciphertext
        assert encrypted1 != encrypted2

    def test_different_secrets_different_ciphertext(self) -> None:
        """Test different secrets produce different ciphertext."""
        enc1 = encrypt_secret("secret1")
        enc2 = encrypt_secret("secret2")
        assert enc1 != enc2


class TestDecryptSecret:
    """Tests for decrypt_secret function."""

    def test_decrypts_encrypted_secret(self) -> None:
        """Test roundtrip encryption/decryption."""
        original = "my_secret_key"
        encrypted = encrypt_secret(original)
        decrypted = decrypt_secret(encrypted)
        assert decrypted == original

    def test_returns_unencrypted_as_is(self) -> None:
        """Test unencrypted values are returned unchanged."""
        unencrypted = "plain_secret"
        result = decrypt_secret(unencrypted)
        assert result == unencrypted

    def test_backwards_compatibility(self) -> None:
        """Test that old unencrypted secrets still work."""
        old_secret = "legacy_unencrypted_secret"
        result = decrypt_secret(old_secret)
        assert result == old_secret


class TestEncryptionRoundtrip:
    """Tests for encryption/decryption roundtrip."""

    def test_roundtrip_simple_string(self) -> None:
        """Test roundtrip with simple string."""
        secret = "simple_secret"
        assert decrypt_secret(encrypt_secret(secret)) == secret

    def test_roundtrip_complex_string(self) -> None:
        """Test roundtrip with complex string."""
        secret = "complex-secret_with.special/chars!@#$%^&*()"
        assert decrypt_secret(encrypt_secret(secret)) == secret

    def test_roundtrip_unicode(self) -> None:
        """Test roundtrip with unicode characters."""
        secret = "secret-with-unicode-\u2764-emoji"
        assert decrypt_secret(encrypt_secret(secret)) == secret

    def test_roundtrip_empty_string(self) -> None:
        """Test roundtrip with empty string."""
        secret = ""
        assert decrypt_secret(encrypt_secret(secret)) == secret

    def test_roundtrip_long_string(self) -> None:
        """Test roundtrip with long string."""
        secret = "a" * 1000
        assert decrypt_secret(encrypt_secret(secret)) == secret


class TestEncryptedPrefix:
    """Tests for encrypted prefix handling."""

    def test_prefix_is_added(self) -> None:
        """Test encrypted values have correct prefix."""
        encrypted = encrypt_secret("secret")
        assert encrypted.startswith("enc:v1:")

    def test_only_prefixed_values_decrypted(self) -> None:
        """Test only prefixed values attempt decryption."""
        # Value without prefix should be returned as-is
        no_prefix = "not_encrypted_value"
        assert decrypt_secret(no_prefix) == no_prefix
