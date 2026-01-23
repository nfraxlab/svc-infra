from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore[misc,assignment]

try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
except Exception:  # pragma: no cover
    AsyncSession = object  # type: ignore[misc,assignment]
    select = None  # type: ignore[misc,assignment]

from svc_infra.security.models import (
    AuthSession,
    RefreshToken,
    RefreshTokenRevocation,
    generate_refresh_token,
    hash_refresh_token,
    rotate_refresh_token,
)

DEFAULT_REFRESH_TTL_MINUTES = 60 * 24 * 7  # 7 days


async def lookup_ip_location(ip_address: str) -> str | None:
    """Look up approximate location from IP address using ip-api.com (free tier).

    Returns city + country string, or None if lookup fails.
    This is fire-and-forget - failures are silently ignored.
    """
    if not httpx or not ip_address:
        return None

    # Skip private/local IPs
    if ip_address.startswith(("127.", "10.", "192.168.", "172.16.", "::1", "localhost")):
        return None

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            # Using ip-api.com free tier (45 req/min limit, no key needed)
            resp = await client.get(
                f"http://ip-api.com/json/{ip_address}?fields=city,country,status"
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    city = data.get("city", "")
                    country = data.get("country", "")
                    if city and country:
                        return f"{city}, {country}"
                    return country or city or None
    except Exception:
        pass  # Ignore all errors - this is best-effort
    return None


def _normalize_user_agent(user_agent: str | None) -> str | None:
    """Normalize user agent to a device fingerprint for matching.

    Extracts OS + browser family to group logins from the same device,
    even if browser version changes slightly.
    """
    if not user_agent:
        return None

    # Simple normalization: take first 256 chars and lowercase
    # More sophisticated: parse with user-agents library
    # For now, just normalize to enable matching
    return user_agent[:256].strip()


async def find_existing_session(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    user_agent: str | None = None,
    ip_hash: str | None = None,
) -> AuthSession | None:
    """Find an existing active session for the same device.

    Matches on user_id + user_agent (device fingerprint).
    Only returns sessions that are not revoked.
    """
    if not user_agent:
        return None

    normalized_ua = _normalize_user_agent(user_agent)

    stmt = (
        select(AuthSession)
        .where(
            AuthSession.user_id == user_id,
            AuthSession.user_agent == normalized_ua,
            AuthSession.revoked_at.is_(None),  # Only active sessions
        )
        .order_by(AuthSession.created_at.desc())
        .limit(1)
    )

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def issue_session_and_refresh(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    tenant_id: str | None = None,
    user_agent: str | None = None,
    ip_hash: str | None = None,
    location: str | None = None,
    ttl_minutes: int = DEFAULT_REFRESH_TTL_MINUTES,
) -> tuple[str, RefreshToken]:
    """Persist or update AuthSession + RefreshToken and return raw refresh token.

    If an active session exists for the same device (user_agent), reuses it
    and updates last_seen_at. Otherwise creates a new session.

    Returns: (raw_refresh_token, RefreshToken model instance)
    """
    normalized_ua = _normalize_user_agent(user_agent)

    # Try to find existing session for this device
    existing_session = await find_existing_session(
        db,
        user_id=user_id,
        user_agent=normalized_ua,
        ip_hash=ip_hash,
    )

    if existing_session:
        # Reuse existing session, update last_seen
        session_row = existing_session
        session_row.last_seen_at = datetime.now(UTC)
        # Update IP if changed (user on different network)
        if ip_hash and session_row.ip_hash != ip_hash:
            session_row.ip_hash = ip_hash
        # Update location if provided and changed
        if location and session_row.location != location:
            session_row.location = location
    else:
        # Create new session for this device
        session_row = AuthSession(
            user_id=user_id,
            tenant_id=tenant_id,
            user_agent=normalized_ua,
            ip_hash=ip_hash,
            location=location,
            last_seen_at=datetime.now(UTC),
        )
        db.add(session_row)

    # Always create a new refresh token for the session
    raw = generate_refresh_token()
    token_hash = hash_refresh_token(raw)
    expires_at = datetime.now(UTC) + timedelta(minutes=ttl_minutes)
    rt = RefreshToken(
        session=session_row,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(rt)
    await db.flush()
    return raw, rt


async def rotate_session_refresh(
    db: AsyncSession,
    *,
    current: RefreshToken,
    ttl_minutes: int = DEFAULT_REFRESH_TTL_MINUTES,
) -> tuple[str, RefreshToken]:
    """Rotate a session's refresh token: mark current rotated, create new, add revocation record.

    Returns: (new_raw_refresh_token, new_refresh_token_model)
    """
    rotation_ts = datetime.now(UTC)
    if current.revoked_at:
        raise ValueError("refresh token already revoked")
    if current.expires_at and current.expires_at <= rotation_ts:
        raise ValueError("refresh token expired")
    new_raw, new_hash, expires_at = rotate_refresh_token(
        current.token_hash, ttl_minutes=ttl_minutes
    )
    current.rotated_at = rotation_ts
    current.revoked_at = rotation_ts
    current.revoke_reason = "rotated"
    if current.expires_at is None or current.expires_at > rotation_ts:
        current.expires_at = rotation_ts
    # create revocation entry for old hash
    db.add(
        RefreshTokenRevocation(
            token_hash=current.token_hash,
            revoked_at=rotation_ts,
            reason="rotated",
        )
    )
    new_row = RefreshToken(
        session=current.session,
        token_hash=new_hash,
        expires_at=expires_at,
    )
    db.add(new_row)
    await db.flush()
    return new_raw, new_row


__all__ = [
    "issue_session_and_refresh",
    "rotate_session_refresh",
    "find_existing_session",
    "lookup_ip_location",
]
