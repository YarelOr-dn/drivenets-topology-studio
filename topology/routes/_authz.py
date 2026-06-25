"""
Request-side authorization helpers (Wave 7.6).

The Wave 6 admission chain -- device-queue cap, per-user cap, global push
slot, device lock -- protects the system from resource exhaustion once a
push has been accepted. It does NOT answer the policy question::

    "Is this authenticated user permitted to push to THIS device?"

Prior to Wave 7 any caller holding a valid JWT could POST /api/config/push
with ANY ``device_id`` and reach the pre-queue cap check. That meant a
viewer could:

    * Enumerate device IDs and harvest their mgmt_ip via the cap error
      response.
    * DoS another user's device by spamming it until Wave 6.5's queue
      cap returns 503 -- rejecting the rightful owner too.
    * Push arbitrary config if no extra RBAC layer was installed
      downstream.

This module adds a single centralized policy hook, called BEFORE any
scheduler reservations happen. The policy is deliberately conservative:

    * Role "admin"        -> push / upgrade allowed.
    * Role "user"         -> push / upgrade allowed for any device that
                              resolves to a real management IP (i.e.
                              exists in the global DB or user's private
                              ``~/.topology_users/<user>/devices.json``).
    * Role "viewer" or "" -> rejected with 403.
    * Unauthenticated     -> rejected with 401 when multi-user auth is
                              active; allowed through in legacy single-
                              user mode (``request.state.user`` missing).

If a per-tenant ownership model is introduced later (e.g. "device X
belongs to tenant T"), this module is the single place to extend the
policy -- every write endpoint routes through ``authorize_push``.

All rejection branches call the audit log so forensic tooling can see
"alice tried to push to PE-4, rejected (viewer role)" without having to
correlate web server access logs with JWT payloads.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def _multiuser_mode_on() -> bool:
    """True when authorization policy is in force.

    Resolution order:
        1. ``TP_AUTH_ENFORCE`` env override (``always`` / ``never`` / ``auto``).
        2. ``scaler_bridge._multiuser_available`` -- the authoritative flag set
           at bridge startup. When the bridge successfully installed its JWT
           middleware this is True; when it deliberately fell back to
           single-user mode (or is not the process root) this is False.
        3. Importability of ``api.auth.service`` as a last-resort heuristic for
           isolated router unit tests.

    This three-step probe fixes a bug where a bridge intentionally started in
    single-user mode (``_multiuser_available=False``) would still get rejected
    by authorize_push() merely because the ``api.auth`` package happens to
    exist on disk. The authoritative signal is what the bridge process actually
    wired up, not what's importable.
    """
    override = (os.environ.get("TP_AUTH_ENFORCE") or "").strip().lower()
    if override == "always":
        return True
    if override == "never":
        return False

    try:
        import scaler_bridge  # type: ignore
        flag = getattr(scaler_bridge, "_multiuser_available", None)
        if flag is True:
            return True
        if flag is False:
            return False
    except Exception:
        pass

    try:
        from api.auth.service import decode_token  # noqa: F401
        return True
    except Exception:
        return False


_WRITE_ROLES = {"user", "admin"}


def _canon_role(role: Optional[str]) -> str:
    return (role or "").strip().lower() or "viewer"


def authorize_push(
    *,
    owner: str,
    role: str,
    device_id: str,
    mgmt_ip: str,
    action: str = "push",
) -> None:
    """Policy gate for push / upgrade / delete-hierarchy write actions.

    Raises ``HTTPException`` with the right status code on failure; on
    success returns silently.

    Parameters
    ----------
    owner   : normalized username (from ``_get_request_user``)
    role    : normalized role string (from ``_get_request_role``)
    device_id : caller-supplied device identifier (pre-resolution)
    mgmt_ip : resolved management IP (or empty if resolution failed)
    action  : short tag for audit log ("push", "upgrade", "delete", ...)
    """
    from routes._state import normalize_owner
    from routes._audit_log import record_event

    canon_owner = normalize_owner(owner)
    canon_role = _canon_role(role)
    multiuser = _multiuser_mode_on()

    # 1) Single-user / dev mode: permit silently (no JWT middleware is
    #    even installed, so there's nobody to authorize).
    if not multiuser:
        return

    # 2) Multi-user mode REQUIRES an authenticated user. ``default`` is
    #    the legacy sentinel and MUST NOT grant write access when auth
    #    is on -- otherwise a forgotten middleware would open a gaping
    #    hole.
    if not canon_owner or canon_owner == "default":
        record_event(
            action=f"{action}_rejected",
            owner="",
            role=canon_role,
            device_id=device_id or "",
            mgmt_ip=mgmt_ip or "",
            result="unauthenticated",
            detail={"reason": "missing or default owner"},
        )
        raise HTTPException(
            status_code=401,
            detail={
                "error": "auth_required",
                "message": "Authenticated user required for this action.",
            },
        )

    # 3) Role gate. Viewer (and unknown roles) cannot write.
    if canon_role not in _WRITE_ROLES:
        record_event(
            action=f"{action}_rejected",
            owner=canon_owner,
            role=canon_role,
            device_id=device_id or "",
            mgmt_ip=mgmt_ip or "",
            result="forbidden_role",
            detail={"allowed_roles": sorted(_WRITE_ROLES)},
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "insufficient_role",
                "message": f"Role '{canon_role}' cannot perform {action}.",
                "required_role": "user",
            },
        )

    # 4) Device resolution gate. No mgmt_ip means the device does not
    #    exist -- reject with 404 rather than 400 so probing callers
    #    can't distinguish "device exists but you're blocked" from
    #    "device does not exist at all" (reduces enumeration signal).
    if not mgmt_ip:
        record_event(
            action=f"{action}_rejected",
            owner=canon_owner,
            role=canon_role,
            device_id=device_id or "",
            mgmt_ip="",
            result="unknown_device",
            detail={"reason": "device_id did not resolve"},
        )
        raise HTTPException(
            status_code=404,
            detail={
                "error": "unknown_device",
                "message": f"Device '{device_id}' not found.",
                "device_id": device_id,
            },
        )

    # 5) Accepted. We intentionally do NOT emit an audit event here --
    #    the caller emits ``{action}_start`` with richer detail right
    #    after reservations succeed, so logging twice would double the
    #    audit volume without adding information.
    return
