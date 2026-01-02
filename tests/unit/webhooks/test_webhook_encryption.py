"""
Tests for webhook secret encryption.
"""

from __future__ import annotations

import os

import pytest


class TestEncryptSecret:
    """Tests for secret encryption."""

    def test_encrypt_returns_prefixed_string(self, mocker):
        """Should return string with enc:v1: prefix."""
        mocker.patch.dict(os.environ, {"WEBHOOK_ENCRYPTION_KEY": "test-key"})

        from svc_infra.webhooks.encryption import _get_fernet, encrypt_secret

        # Clear the cache
        _get_fernet.cache_clear()

        result = encrypt_secret("my_secret")

        assert result.startswith("enc:v1:")

    def test_encrypt_different_inputs_different_outputs(self, mocker):
        """Should produce different ciphertext for different inputs."""
        mocker.patch.dict(os.environ, {"WEBHOOK_ENCRYPTION_KEY": "test-key"})

        from svc_infra.webhooks.encryption import _get_fernet, encrypt_secret

        _get_fernet.cache_clear()

        result1 = encrypt_secret("secret1")
        result2 = encrypt_secret("secret2")

        assert result1 != result2

    def test_encrypt_same_input_different_outputs(self, mocker):
        """Should produce different ciphertext each time (due to IV)."""
        mocker.patch.dict(os.environ, {"WEBHOOK_ENCRYPTION_KEY": "test-key"})

        from svc_infra.webhooks.encryption import _get_fernet, encrypt_secret

        _get_fernet.cache_clear()

        result1 = encrypt_secret("same_secret")
        result2 = encrypt_secret("same_secret")

        # Fernet uses random IV, so outputs should differ
        assert result1 != result2


class TestDecryptSecret:
    """Tests for secret decryption."""

    def test_decrypt_encrypted_value(self, mocker):
        """Should decrypt encrypted value correctly."""
        mocker.patch.dict(os.environ, {"WEBHOOK_ENCRYPTION_KEY": "test-key"})

        from svc_infra.webhooks.encryption import _get_fernet, decrypt_secret, encrypt_secret

        _get_fernet.cache_clear()

        original = "my_secret_value"
        encrypted = encrypt_secret(original)
        decrypted = decrypt_secret(encrypted)

        assert decrypted == original

    def test_decrypt_unencrypted_value(self, mocker):
        """Should return unencrypted value as-is."""
        mocker.patch.dict(os.environ, {"WEBHOOK_ENCRYPTION_KEY": "test-key"})

        from svc_infra.webhooks.encryption import _get_fernet, decrypt_secret

        _get_fernet.cache_clear()

        result = decrypt_secret("plain_text_value")

        assert result == "plain_text_value"

    def test_decrypt_empty_string(self, mocker):
        """Should handle empty string."""
        mocker.patch.dict(os.environ, {"WEBHOOK_ENCRYPTION_KEY": "test-key"})

        from svc_infra.webhooks.encryption import _get_fernet, decrypt_secret

        _get_fernet.cache_clear()

        result = decrypt_secret("")

        assert result == ""


class TestIsEncrypted:
    """Tests for encryption detection."""

    def test_is_encrypted_with_prefix(self):
        """Should return True for prefixed values."""
        from svc_infra.webhooks.encryption import is_encrypted

        assert is_encrypted("enc:v1:some_encrypted_data") is True

    def test_is_encrypted_without_prefix(self):
        """Should return False for non-prefixed values."""
        from svc_infra.webhooks.encryption import is_encrypted

        assert is_encrypted("plain_text") is False

    def test_is_encrypted_empty_string(self):
        """Should return False for empty string."""
        from svc_infra.webhooks.encryption import is_encrypted

        assert is_encrypted("") is False

    def test_is_encrypted_partial_prefix(self):
        """Should return False for partial prefix."""
        from svc_infra.webhooks.encryption import is_encrypted

        assert is_encrypted("enc:") is False
        assert is_encrypted("enc:v1") is False


class TestGetEncryptionKey:
    """Tests for encryption key derivation."""

    def test_key_from_env_variable(self, mocker):
        """Should read key from environment."""
        mocker.patch.dict(os.environ, {"WEBHOOK_ENCRYPTION_KEY": "my-test-key"})

        from svc_infra.webhooks.encryption import _get_encryption_key

        key = _get_encryption_key()

        assert key is not None
        assert len(key) == 32  # SHA256 output

    def test_fernet_key_used_directly(self, mocker):
        """Should use Fernet key directly if valid format."""
        # A valid Fernet key is 32 bytes base64-encoded (44 chars with padding)
        from cryptography.fernet import Fernet

        valid_key = Fernet.generate_key().decode()
        mocker.patch.dict(os.environ, {"WEBHOOK_ENCRYPTION_KEY": valid_key})

        from svc_infra.webhooks.encryption import _get_encryption_key

        key = _get_encryption_key()

        assert len(key) == 32

    def test_arbitrary_string_derived(self, mocker):
        """Should derive key from arbitrary string."""
        mocker.patch.dict(os.environ, {"WEBHOOK_ENCRYPTION_KEY": "short"})

        from svc_infra.webhooks.encryption import _get_encryption_key

        key = _get_encryption_key()

        # SHA256 always produces 32 bytes
        assert len(key) == 32


class TestGetFernet:
    """Tests for Fernet cipher management."""

    def test_fernet_cached(self, mocker):
        """Should cache Fernet instance."""
        mocker.patch.dict(os.environ, {"WEBHOOK_ENCRYPTION_KEY": "test-key"})

        from svc_infra.webhooks.encryption import _get_fernet

        _get_fernet.cache_clear()

        fernet1 = _get_fernet()
        fernet2 = _get_fernet()

        assert fernet1 is fernet2

    def test_fernet_not_none_with_cryptography(self, mocker):
        """Should return Fernet instance when cryptography installed."""
        mocker.patch.dict(os.environ, {"WEBHOOK_ENCRYPTION_KEY": "test-key"})

        from svc_infra.webhooks.encryption import _get_fernet

        _get_fernet.cache_clear()

        fernet = _get_fernet()

        assert fernet is not None


class TestEncryptionRoundTrip:
    """Tests for complete encrypt/decrypt cycle."""

    def test_roundtrip_ascii(self, mocker):
        """Should roundtrip ASCII text."""
        mocker.patch.dict(os.environ, {"WEBHOOK_ENCRYPTION_KEY": "test-key"})

        from svc_infra.webhooks.encryption import _get_fernet, decrypt_secret, encrypt_secret

        _get_fernet.cache_clear()

        original = "hello_world_123"
        encrypted = encrypt_secret(original)
        decrypted = decrypt_secret(encrypted)

        assert decrypted == original

    def test_roundtrip_unicode(self, mocker):
        """Should roundtrip unicode text."""
        mocker.patch.dict(os.environ, {"WEBHOOK_ENCRYPTION_KEY": "test-key"})

        from svc_infra.webhooks.encryption import _get_fernet, decrypt_secret, encrypt_secret

        _get_fernet.cache_clear()

        original = "hello world 123"
        encrypted = encrypt_secret(original)
        decrypted = decrypt_secret(encrypted)

        assert decrypted == original

    def test_roundtrip_special_characters(self, mocker):
        """Should roundtrip special characters."""
        mocker.patch.dict(os.environ, {"WEBHOOK_ENCRYPTION_KEY": "test-key"})

        from svc_infra.webhooks.encryption import _get_fernet, decrypt_secret, encrypt_secret

        _get_fernet.cache_clear()

        original = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        encrypted = encrypt_secret(original)
        decrypted = decrypt_secret(encrypted)

        assert decrypted == original

    def test_roundtrip_long_secret(self, mocker):
        """Should roundtrip long secrets."""
        mocker.patch.dict(os.environ, {"WEBHOOK_ENCRYPTION_KEY": "test-key"})

        from svc_infra.webhooks.encryption import _get_fernet, decrypt_secret, encrypt_secret

        _get_fernet.cache_clear()

        original = "x" * 1000
        encrypted = encrypt_secret(original)
        decrypted = decrypt_secret(encrypted)

        assert decrypted == original


class TestEncryptionSecurity:
    """Tests for encryption security properties."""

    def test_different_keys_cannot_decrypt(self, mocker):
        """Should fail to decrypt with different key."""
        from cryptography.fernet import InvalidToken

        mocker.patch.dict(os.environ, {"WEBHOOK_ENCRYPTION_KEY": "key1"})

        from svc_infra.webhooks.encryption import _get_fernet, encrypt_secret

        _get_fernet.cache_clear()

        encrypted = encrypt_secret("secret")

        # Change the key
        mocker.patch.dict(os.environ, {"WEBHOOK_ENCRYPTION_KEY": "key2"})
        _get_fernet.cache_clear()

        from svc_infra.webhooks.encryption import decrypt_secret

        with pytest.raises(InvalidToken):
            decrypt_secret(encrypted)

    def test_tampered_ciphertext_fails(self, mocker):
        """Should fail on tampered ciphertext."""
        from cryptography.fernet import InvalidToken

        mocker.patch.dict(os.environ, {"WEBHOOK_ENCRYPTION_KEY": "test-key"})

        from svc_infra.webhooks.encryption import _get_fernet, decrypt_secret, encrypt_secret

        _get_fernet.cache_clear()

        encrypted = encrypt_secret("secret")

        # Tamper with the ciphertext
        tampered = encrypted[:-5] + "XXXXX"

        with pytest.raises((InvalidToken, Exception)):
            decrypt_secret(tampered)
