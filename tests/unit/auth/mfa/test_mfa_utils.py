"""Unit tests for svc_infra.api.fastapi.auth.mfa.utils module."""

from __future__ import annotations


class TestQrSvgFromUri:
    """Tests for _qr_svg_from_uri function."""

    def test_generates_svg_with_uri(self) -> None:
        """Test SVG generation contains the URI."""
        from svc_infra.api.fastapi.auth.mfa.utils import _qr_svg_from_uri

        uri = "otpauth://totp/MyApp:user@example.com?secret=JBSWY3DPEHPK3PXP"
        svg = _qr_svg_from_uri(uri)

        assert "<svg" in svg
        assert "</svg>" in svg
        assert uri in svg

    def test_generates_valid_svg_structure(self) -> None:
        """Test SVG has valid structure."""
        from svc_infra.api.fastapi.auth.mfa.utils import _qr_svg_from_uri

        svg = _qr_svg_from_uri("test-uri")

        assert "xmlns='http://www.w3.org/2000/svg'" in svg
        assert "width='280'" in svg
        assert "height='280'" in svg


class TestRandomBase32:
    """Tests for _random_base32 function."""

    def test_generates_32_char_string(self) -> None:
        """Test generates 32-character base32 string."""
        from svc_infra.api.fastapi.auth.mfa.utils import _random_base32

        result = _random_base32()

        assert len(result) == 32
        # Base32 alphabet
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for c in result)

    def test_generates_unique_values(self) -> None:
        """Test generates unique values on each call."""
        from svc_infra.api.fastapi.auth.mfa.utils import _random_base32

        results = [_random_base32() for _ in range(10)]

        # All should be unique
        assert len(set(results)) == 10


class TestGenRecoveryCodes:
    """Tests for _gen_recovery_codes function."""

    def test_generates_correct_number_of_codes(self) -> None:
        """Test generates requested number of codes."""
        from svc_infra.api.fastapi.auth.mfa.utils import _gen_recovery_codes

        codes = _gen_recovery_codes(n=8, length=12)

        assert len(codes) == 8

    def test_generates_codes_of_correct_length(self) -> None:
        """Test codes have correct length."""
        from svc_infra.api.fastapi.auth.mfa.utils import _gen_recovery_codes

        codes = _gen_recovery_codes(n=5, length=16)

        for code in codes:
            assert len(code) == 16

    def test_generates_unique_codes(self) -> None:
        """Test all generated codes are unique."""
        from svc_infra.api.fastapi.auth.mfa.utils import _gen_recovery_codes

        codes = _gen_recovery_codes(n=10, length=20)

        assert len(set(codes)) == 10

    def test_codes_are_url_safe(self) -> None:
        """Test codes use URL-safe characters."""
        from svc_infra.api.fastapi.auth.mfa.utils import _gen_recovery_codes

        codes = _gen_recovery_codes(n=5, length=20)

        for code in codes:
            # URL-safe base64 alphabet (minus padding)
            assert all(
                c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
                for c in code
            )


class TestGenNumericCode:
    """Tests for _gen_numeric_code function."""

    def test_generates_6_digit_code_by_default(self) -> None:
        """Test generates 6-digit code by default."""
        from svc_infra.api.fastapi.auth.mfa.utils import _gen_numeric_code

        code = _gen_numeric_code()

        assert len(code) == 6
        assert code.isdigit()

    def test_generates_custom_length_code(self) -> None:
        """Test generates code of custom length."""
        from svc_infra.api.fastapi.auth.mfa.utils import _gen_numeric_code

        code = _gen_numeric_code(n=8)

        assert len(code) == 8
        assert code.isdigit()

    def test_generates_numeric_only(self) -> None:
        """Test code contains only digits."""
        from svc_infra.api.fastapi.auth.mfa.utils import _gen_numeric_code

        for _ in range(10):
            code = _gen_numeric_code()
            assert code.isdigit()


class TestHash:
    """Tests for _hash function."""

    def test_returns_sha256_hex(self) -> None:
        """Test returns SHA256 hex digest."""
        from svc_infra.api.fastapi.auth.mfa.utils import _hash

        result = _hash("test")

        # SHA256 produces 64-char hex string
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_consistent_hashing(self) -> None:
        """Test same input produces same hash."""
        from svc_infra.api.fastapi.auth.mfa.utils import _hash

        hash1 = _hash("my-secret-code")
        hash2 = _hash("my-secret-code")

        assert hash1 == hash2

    def test_different_inputs_different_hashes(self) -> None:
        """Test different inputs produce different hashes."""
        from svc_infra.api.fastapi.auth.mfa.utils import _hash

        hash1 = _hash("code1")
        hash2 = _hash("code2")

        assert hash1 != hash2


class TestNowUtcTs:
    """Tests for _now_utc_ts function."""

    def test_returns_integer_timestamp(self) -> None:
        """Test returns integer Unix timestamp."""
        from svc_infra.api.fastapi.auth.mfa.utils import _now_utc_ts

        ts = _now_utc_ts()

        assert isinstance(ts, int)
        assert ts > 0

    def test_returns_current_time(self) -> None:
        """Test returns approximately current time."""
        import time

        from svc_infra.api.fastapi.auth.mfa.utils import _now_utc_ts

        expected = int(time.time())
        actual = _now_utc_ts()

        # Should be within 2 seconds
        assert abs(actual - expected) < 2
