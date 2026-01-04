"""Benchmarks for authentication and security operations.

Run with:
    make benchmark
    pytest benchmarks/bench_auth.py --benchmark-only
"""

from __future__ import annotations


class TestSecurityImport:
    """Benchmark security module imports."""

    def test_security_import(self, benchmark):
        """Benchmark security module import time."""

        def import_security():
            import importlib

            import svc_infra.security

            importlib.reload(svc_infra.security)

        benchmark(import_security)


class TestPasswordOperations:
    """Benchmark password validation operations."""

    def test_password_policy_creation(self, benchmark):
        """Benchmark PasswordPolicy instantiation."""
        from svc_infra.security import PasswordPolicy

        def create_policy():
            return PasswordPolicy(
                min_length=12,
                require_uppercase=True,
                require_lowercase=True,
                require_digit=True,
                require_symbol=True,
            )

        result = benchmark(create_policy)
        assert result.min_length == 12

    def test_password_validation(self, benchmark):
        """Benchmark password validation (without HIBP)."""
        from svc_infra.security import PasswordPolicy, validate_password

        policy = PasswordPolicy(
            min_length=8,
            require_uppercase=True,
            require_lowercase=True,
            require_digit=True,
        )

        def validate():
            return validate_password("SecureP@ss123", policy)

        result = benchmark(validate)
        assert result is True


class TestLockoutOperations:
    """Benchmark lockout computation."""

    def test_lockout_computation(self, benchmark):
        """Benchmark lockout status computation."""
        from svc_infra.security import LockoutConfig, compute_lockout

        config = LockoutConfig(
            max_attempts=5,
            lockout_duration_seconds=300,
            base_backoff_seconds=60,
        )

        def compute():
            return compute_lockout(
                failed_attempts=3,
                last_attempt_at=None,
                config=config,
            )

        result = benchmark(compute)
        assert result is not None


class TestAuditOperations:
    """Benchmark audit logging operations."""

    def test_audit_hash_computation(self, benchmark):
        """Benchmark audit hash chain computation."""
        from svc_infra.security import compute_audit_hash

        prev_hash = "abc123def456"
        event_data = "user:123:login:success:2024-01-01T00:00:00Z"

        def compute_hash():
            return compute_audit_hash(prev_hash, event_data)

        result = benchmark(compute_hash)
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex


class TestJWTOperations:
    """Benchmark JWT operations."""

    def test_jwt_rotation_strategy_init(self, benchmark):
        """Benchmark RotatingJWTStrategy initialization."""
        from svc_infra.security import RotatingJWTStrategy

        def create_strategy():
            return RotatingJWTStrategy(
                secret_key="test_secret_key_for_benchmarks",
                algorithm="HS256",
            )

        result = benchmark(create_strategy)
        assert result is not None
