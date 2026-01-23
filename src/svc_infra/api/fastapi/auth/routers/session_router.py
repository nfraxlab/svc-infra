from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from svc_infra.api.fastapi.auth.security import Identity
from svc_infra.api.fastapi.db.sql.session import SqlSessionDep
from svc_infra.security.models import AuthSession
from svc_infra.security.permissions import RequirePermission


def build_session_router() -> APIRouter:
    router = APIRouter(prefix="/sessions", tags=["sessions"])

    @router.get(
        "/me",
        response_model=list[dict],
        dependencies=[RequirePermission("security.session.list")],
    )
    async def list_my_sessions(identity: Identity, session: SqlSessionDep) -> list[dict]:
        stmt = select(AuthSession).where(AuthSession.user_id == identity.user.id)
        rows = (await session.execute(stmt)).scalars().all()
        return [
            {
                "id": str(r.id),
                "user_agent": r.user_agent,
                "ip_hash": r.ip_hash,
                "location": r.location,
                "revoked": bool(r.revoked_at),
                # Use last_seen_at if available, otherwise fall back to created_at
                "last_seen_at": (
                    r.last_seen_at.isoformat()
                    if r.last_seen_at
                    else (r.created_at.isoformat() if r.created_at else None)
                ),
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    # NOTE: /me/all must be defined BEFORE /{session_id} routes to avoid "me" being matched as session_id
    @router.delete(
        "/me/all",
        status_code=204,
        dependencies=[RequirePermission("security.session.revoke")],
    )
    async def delete_all_sessions(identity: Identity, db: SqlSessionDep):
        """Revoke and delete all sessions for the current user (clears history)."""
        stmt = select(AuthSession).where(AuthSession.user_id == identity.user.id)
        rows = (await db.execute(stmt)).scalars().all()
        now = datetime.now(UTC)
        for s in rows:
            # Revoke first if not already revoked
            if not s.revoked_at:
                s.revoked_at = now
                s.revoke_reason = "user_cleared_history"
                for rt in s.refresh_tokens:
                    if not rt.revoked_at:
                        rt.revoked_at = now
                        rt.revoke_reason = "session_deleted"
            await db.delete(s)
        await db.flush()

    @router.post(
        "/{session_id}/revoke",
        status_code=204,
        dependencies=[RequirePermission("security.session.revoke")],
    )
    async def revoke_session(session_id: str, identity: Identity, db: SqlSessionDep):
        # Load session and ensure it belongs to the user (non-admin users cannot revoke others)
        s = await db.get(AuthSession, session_id)
        if not s:
            raise HTTPException(404, "session_not_found")
        # Basic ownership check; could extend for admin bypass later
        if s.user_id != identity.user.id:
            raise HTTPException(403, "forbidden")
        if s.revoked_at:
            return  # already revoked
        s.revoked_at = datetime.now(UTC)
        s.revoke_reason = "user_revoked"
        # Revoke all refresh tokens for this session
        for rt in s.refresh_tokens:
            if not rt.revoked_at:
                rt.revoked_at = s.revoked_at
                rt.revoke_reason = "session_revoked"
        await db.flush()

    @router.delete(
        "/{session_id}",
        status_code=204,
        dependencies=[RequirePermission("security.session.revoke")],
    )
    async def delete_session(session_id: str, identity: Identity, db: SqlSessionDep):
        """Revoke and permanently delete a session from history."""
        s = await db.get(AuthSession, session_id)
        if not s:
            raise HTTPException(404, "session_not_found")
        if s.user_id != identity.user.id:
            raise HTTPException(403, "forbidden")
        # Revoke first if not already revoked
        if not s.revoked_at:
            s.revoked_at = datetime.now(UTC)
            s.revoke_reason = "user_deleted"
            for rt in s.refresh_tokens:
                if not rt.revoked_at:
                    rt.revoked_at = s.revoked_at
                    rt.revoke_reason = "session_deleted"
        await db.delete(s)
        await db.flush()

    return router


__all__ = ["build_session_router"]
