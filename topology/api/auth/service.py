"""JWT authentication service and FastAPI dependency for route protection.

Usage in routers:
    from api.auth.service import get_current_user, require_role, require_owner
    
    @router.get("/protected")
    async def protected(user: dict = Depends(get_current_user)):
        return {"hello": user["username"]}
    
    @router.post("/admin-only")
    async def admin_only(user: dict = Depends(require_role("admin"))):
        ...

    @router.post("/owner-only")
    async def owner_only(user: dict = Depends(require_owner())):
        # Only the deployment owner (Yarel Or by default) can reach this.
        ...
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import settings
from .user_store import user_store

security = HTTPBearer(auto_error=False)


# ----------------------------------------------------------------
# Deployment "owner" detection
# ----------------------------------------------------------------
# The owner tier is a super-admin who sees every admin menu item
# PLUS destructive controls (reset-configs / restart-server /
# impersonate). We identify the owner via three sources, in
# priority order:
#   1. OWNER_USERNAME env var (case-insensitive exact match)
#   2. Canonical hard-coded usernames -- includes the legacy
#      ``yarel`` / ``yarel-or`` / ``yarelor`` names AND the
#      post-migration email-local-part identity ``yor`` (from
#      ``yor@drivenets.com``). When the username migration runs the
#      DB row gets re-keyed from ``yarel`` to ``yor``; without
#      ``yor`` in this list the deployment owner would silently
#      lose owner-tier UI on first login after the migration.
#   3. display_name literally equal to "Yarel Or"
# All three are cheap string checks -- no DB lookup, so it's safe to
# call on every request. `is_owner` is returned in /auth/me and /login
# so the frontend can show the owner-only menu tier + gold badge.
_DEFAULT_OWNER_USERNAMES = ("yor", "yarel", "yarel-or", "yarelor")
_DEFAULT_OWNER_DISPLAY = "yarel or"


def is_owner_user(username: str, display_name: str = "") -> bool:
    """Return True iff the given user is the deployment owner.

    Used by:
      - routes/router.py:/me to stamp `is_owner` on UserInfo
      - serve.py owner-only endpoints to gate destructive actions
      - require_owner() dependency below
    """
    u = (username or "").strip().lower()
    d = (display_name or "").strip().lower()
    env_owner = (os.environ.get("OWNER_USERNAME") or "").strip().lower()
    if env_owner and u == env_owner:
        return True
    if u in _DEFAULT_OWNER_USERNAMES:
        return True
    if d == _DEFAULT_OWNER_DISPLAY:
        return True
    return False


def create_access_token(username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": username,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """FastAPI dependency: extracts and validates JWT from Authorization header.
    
    When multiuser is disabled, returns a default user dict without auth.
    That default user is effectively the deployment operator, so we also
    flag them as the owner (is_owner=True) -- this unlocks owner-tier UI
    (reset-configs / restart / impersonate) in single-user deployments,
    matching the behavior every multiuser deployment gets via the
    OWNER_USERNAME env var or the "Yarel Or" canonical user.
    """
    if not settings.multiuser_enabled:
        return {
            "username": "default",
            "display_name": "Default User",
            "role": "admin",
            "is_owner": True,
        }

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = user_store.get_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return {
        "username": user["username"],
        "display_name": user["display_name"],
        "role": user["role"],
        "email": user.get("email", ""),
    }


def require_role(min_role: str) -> Callable:
    """Factory for FastAPI dependency that enforces minimum role level.
    
    Usage: Depends(require_role("admin"))
    """
    async def _check(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if not user_store.has_role_or_higher(user["username"], min_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role '{min_role}' or higher (you have '{user['role']}')",
            )
        return user
    return _check


def require_owner() -> Callable:
    """Factory for FastAPI dependency that enforces deployment-owner status.

    An owner is either:
      - the username set in the OWNER_USERNAME env var,
      - one of the canonical owner usernames (yarel / yarel-or / yarelor),
      - or a user whose display_name is literally "Yarel Or".

    Owners automatically also satisfy the 'admin' role requirement; this
    dependency is only used to gate the *extra* destructive endpoints that
    even other admins don't get (reset-configs, restart-server, impersonate).
    """
    async def _check(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        # In single-user mode, get_current_user pre-flags the default user
        # as is_owner=True; honor that before falling through to the string
        # matching, otherwise single-user deployments couldn't reach their
        # own owner-only endpoints.
        if user.get("is_owner") is True:
            return user
        if not is_owner_user(user.get("username", ""), user.get("display_name", "")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Owner-only endpoint. Contact the deployment owner.",
            )
        return user
    return _check
