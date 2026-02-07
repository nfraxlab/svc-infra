from __future__ import annotations

import json
import os
from urllib.parse import urlparse

from pydantic import AnyHttpUrl, BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class OIDCProvider(BaseModel):
    name: str
    issuer: str
    client_id: str
    client_secret: SecretStr
    scope: str = "openid email profile"


class JWTSettings(BaseModel):
    secret: SecretStr
    lifetime_seconds: int = 60 * 60 * 24 * 7
    # Optional older secrets accepted for verification during rotation window
    old_secrets: list[SecretStr] = Field(default_factory=list)


class PasswordClient(BaseModel):
    client_id: str
    client_secret: SecretStr


class AuthSettings(BaseSettings):
    # ---- JWT ----
    jwt: JWTSettings | None = None

    # ---- Password login ----
    password_clients: list[PasswordClient] = Field(default_factory=list)
    require_client_secret_on_password_login: bool = False

    # ---- MFA / TOTP ----
    mfa_default_enabled_for_new_users: bool = False
    mfa_enforce_for_all_users: bool = False
    mfa_enforce_for_tenants: list[str] = []
    mfa_issuer: str = "svc-infra"
    mfa_pre_token_lifetime_seconds: int = 300
    mfa_recovery_codes: int = 8
    mfa_recovery_code_length: int = 10

    # ---- Email OTP ----
    email_otp_ttl_seconds: int = 5 * 60
    email_otp_cooldown_seconds: int = 60
    email_otp_attempts: int = 5

    # ---- Email/SMTP (verification, reset, etc.) ----
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from: str | None = None

    # Dev convenience: auto-verify users without sending email
    auto_verify_in_dev: bool = True

    # ---- Built-in provider creds (optional) ----
    google_client_id: str | None = None
    google_client_secret: SecretStr | None = None
    github_client_id: str | None = None
    github_client_secret: SecretStr | None = None
    ms_client_id: str | None = None
    ms_client_secret: SecretStr | None = None
    ms_tenant: str | None = None
    li_client_id: str | None = None
    li_client_secret: SecretStr | None = None
    oidc_providers: list[OIDCProvider] = Field(default_factory=list)

    # ---- Redirect + cookie settings ----
    post_login_redirect: AnyHttpUrl | str = "http://localhost:3000/app"
    # Empty default allows CORS_ORIGINS fallback; set explicitly to override
    redirect_allow_hosts_raw: str = ""

    session_cookie_name: str = "svc_session"
    auth_cookie_name: str = "svc_auth"
    session_cookie_secure: bool = False
    session_cookie_samesite: str = "lax"
    session_cookie_domain: str | None = None
    session_cookie_max_age_seconds: int = 60 * 60 * 4

    model_config = SettingsConfigDict(
        env_prefix="AUTH_",
        env_file=".env",
        extra="ignore",
        env_nested_delimiter="__",
    )


_settings: AuthSettings | None = None


def get_auth_settings() -> AuthSettings:
    global _settings
    if _settings is None:
        _settings = AuthSettings()
    return _settings


def resolve_jwt_secret(*, dev_default: str = "dev-only-jwt-secret-not-for-production") -> str:
    """Return the JWT secret, checking multiple sources.

    Resolution order:
      1. ``AuthSettings.jwt.secret``  (``AUTH_JWT__SECRET`` with double-underscore)
      2. ``AUTH_JWT_SECRET`` env var   (single-underscore — common user expectation)
      3. ``JWT_SECRET`` env var        (bare name)
      4. ``require_secret`` (raises in production, returns *dev_default* otherwise)
    """
    from svc_infra.app.env import require_secret  # deferred to avoid circular import

    st = get_auth_settings()
    jwt_block = getattr(st, "jwt", None)
    if jwt_block and getattr(jwt_block, "secret", None):
        return str(jwt_block.secret.get_secret_value())

    env_secret = os.getenv("AUTH_JWT_SECRET") or os.getenv("JWT_SECRET")
    return str(
        require_secret(
            env_secret,
            "JWT_SECRET (via auth settings jwt.secret)",
            dev_default=dev_default,
        )
    )


def parse_redirect_allow_hosts(raw: str | None) -> list[str]:
    """
    Parse allowed hosts for OAuth redirects.

    Priority:
    1. AUTH_REDIRECT_ALLOW_HOSTS_RAW if explicitly set
    2. Extract hosts from CORS_ORIGINS / CORS_ALLOW_ORIGINS (shared config)
    3. Default to localhost only

    This allows reusing CORS origins for redirect validation, avoiding
    the need to configure both separately.
    """
    base_hosts = ["localhost", "127.0.0.1"]

    # 1. Explicit redirect hosts take priority
    if raw and raw.strip():
        s = raw.strip()
        if s.startswith("["):
            try:
                val = json.loads(s)
                if isinstance(val, list):
                    return base_hosts + [str(x).strip() for x in val if str(x).strip()]
            except Exception:
                pass
        return base_hosts + [h.strip() for h in s.split(",") if h.strip()]

    # 2. Fallback to CORS origins (extract hostnames from URLs)
    cors_raw = os.getenv("CORS_ORIGINS") or os.getenv("CORS_ALLOW_ORIGINS") or ""
    if cors_raw.strip():
        cors_hosts: list[str] = []
        for origin in cors_raw.split(","):
            origin = origin.strip()
            if origin and origin != "*":
                parsed = urlparse(origin)
                if parsed.hostname:
                    cors_hosts.append(parsed.hostname)
        if cors_hosts:
            return base_hosts + cors_hosts

    # 3. Default: localhost only
    return base_hosts
