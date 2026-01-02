"""Tests for svc_infra.api.fastapi.auth.mfa.utils module."""

from __future__ import annotations

import hashlib

from svc_infra.api.fastapi.auth.mfa.utils import (
    _gen_numeric_code,
    _gen_recovery_codes,
    _hash,
    _now_utc_ts,
    _qr_svg_from_uri,
    _random_base32,
)


class TestRandomBase32:
    """Tests for TOTP secret generation."""

    def test_generates_base32_string(self) -> None:
        """Should generate a base32 encoded string."""
        secret = _random_base32()
        assert secret is not None
        assert len(secret) == 32  # default length

    def test_generates_unique_secrets(self) -> None:
        """Should generate unique secrets each time."""
        secrets = [_random_base32() for _ in range(10)]
        assert len(set(secrets)) == 10  # all unique

    def test_is_valid_base32(self) -> None:
        """Should be valid base32 characters only."""
        secret = _random_base32()
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
        assert all(c in valid_chars for c in secret)


class TestQrSvgFromUri:
    """Tests for QR code SVG generation."""

    def test_generates_svg(self) -> None:
        """Should generate SVG markup."""
        uri = "otpauth://totp/App:user@example.com?secret=ABC123&issuer=App"
        svg = _qr_svg_from_uri(uri)
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_includes_uri_in_svg(self) -> None:
        """Should include the URI in the SVG (placeholder behavior)."""
        uri = "otpauth://totp/MyApp:test@test.com?secret=TESTSECRET"
        svg = _qr_svg_from_uri(uri)
        assert "otpauth://" in svg

    def test_sets_svg_dimensions(self) -> None:
        """Should set SVG dimensions."""
        uri = "test-uri"
        svg = _qr_svg_from_uri(uri)
        assert "width='280'" in svg
        assert "height='280'" in svg


class TestGenRecoveryCodes:
    """Tests for recovery code generation."""

    def test_generates_correct_count(self) -> None:
        """Should generate the requested number of codes."""
        codes = _gen_recovery_codes(n=10, length=16)
        assert len(codes) == 10

    def test_generates_correct_length(self) -> None:
        """Should generate codes of the requested length."""
        codes = _gen_recovery_codes(n=5, length=12)
        for code in codes:
            assert len(code) == 12

    def test_generates_unique_codes(self) -> None:
        """Should generate unique codes."""
        codes = _gen_recovery_codes(n=10, length=16)
        assert len(set(codes)) == 10  # all unique

    def test_codes_are_url_safe(self) -> None:
        """Should generate URL-safe codes."""
        codes = _gen_recovery_codes(n=10, length=16)
        for code in codes:
            # URL-safe base64 uses alphanumeric, -, _
            assert all(c.isalnum() or c in "-_" for c in code)


class TestGenNumericCode:
    """Tests for numeric OTP code generation."""

    def test_generates_six_digits_by_default(self) -> None:
        """Should generate 6 digit code by default."""
        code = _gen_numeric_code()
        assert len(code) == 6
        assert code.isdigit()

    def test_generates_custom_length(self) -> None:
        """Should generate code of requested length."""
        code = _gen_numeric_code(n=8)
        assert len(code) == 8
        assert code.isdigit()

    def test_generates_only_digits(self) -> None:
        """Should generate only numeric characters."""
        for _ in range(20):
            code = _gen_numeric_code()
            assert code.isdigit()


class TestHash:
    """Tests for hashing utility."""

    def test_hashes_string(self) -> None:
        """Should hash a string using SHA256."""
        result = _hash("test")
        expected = hashlib.sha256(b"test").hexdigest()
        assert result == expected

    def test_produces_consistent_hash(self) -> None:
        """Should produce the same hash for the same input."""
        assert _hash("hello") == _hash("hello")

    def test_produces_different_hash_for_different_input(self) -> None:
        """Should produce different hashes for different inputs."""
        assert _hash("hello") != _hash("world")

    def test_hash_length(self) -> None:
        """Should produce 64 character hex digest."""
        result = _hash("test")
        assert len(result) == 64


class TestNowUtcTs:
    """Tests for UTC timestamp utility."""

    def test_returns_integer(self) -> None:
        """Should return an integer timestamp."""
        ts = _now_utc_ts()
        assert isinstance(ts, int)

    def test_returns_reasonable_timestamp(self) -> None:
        """Should return a reasonable Unix timestamp."""
        ts = _now_utc_ts()
        # Should be after 2024 and before 2100
        assert 1704067200 < ts < 4102444800

    def test_increases_over_time(self) -> None:
        """Should return increasing timestamps."""
        import time

        ts1 = _now_utc_ts()
        time.sleep(0.01)
        ts2 = _now_utc_ts()
        assert ts2 >= ts1
