"""Topology domain management: CRUD, sharing, topology file operations.

Every user has isolated domains. Domains can be shared with other users
(read or write permission). Shared domains appear in the recipient's
domain list with an [is_shared] flag.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request

from ..schemas import (
    IncomingShareInfo,
    IncomingTopologyShareInfo,
    OutgoingShareInfo,
    OutgoingTopologyShareInfo,
    ShareActivityEntry,
    ShareDomainRequest,
    ShareOverview,
    ShareRecipient,
    ShareTargetUser,
    ShareTopologyRequest,
    TopologyDomainCreate,
    TopologyDomainInfo,
    TopologyDomainUpdate,
    TopologyMeta,
    TopologyMetaLite,
    TopologySave,
    UnshareRequest,
)
from ..auth.service import get_current_user
from ..auth.user_store import (
    DomainTopologyLimitError,
    SHARED_WITH_ME_DOMAIN_ID,
    TopologyConflictError,
    user_store,
)
from ..event_bus import event_bus
from .knowledge_router import router as knowledge_subrouter

logger = logging.getLogger(__name__)


def _actor_display(user: Dict[str, Any]) -> str:
    return (user.get("display_name") or user.get("username") or "").strip()


def _raise_domain_limit(exc: DomainTopologyLimitError) -> None:
    raise HTTPException(status_code=409, detail=exc.to_detail())


def _broadcast_topology_event(
    *,
    owner: str,
    domain_id: str,
    topology_id: str,
    event_type: str,
    summary: str,
    details: Optional[Dict[str, Any]] = None,
    actor_user: str = "",
    actor_display_name: str = "",
    extra_recipients: Optional[List[str]] = None,
    created_at: str = "",
    composite_id: Optional[str] = None,
) -> None:
    """Fan a topology event out over the per-user WebSocket bus.

    Targets the owner + every recipient of a per-file share on this
    topology + any ``extra_recipients`` the caller supplies (used for
    share-granted events so the newly-added user also hears about it).
    Delivery is best-effort; a closed WS just drops the frame -- the
    client reconciles on its next poll / refetch.
    """
    recipients = set()
    if owner:
        recipients.add(owner)
    for r in user_store.list_topology_recipients(owner, domain_id, topology_id):
        if r:
            recipients.add(r)
    for r in (extra_recipients or []):
        if r:
            recipients.add(r)
    if not recipients:
        return
    payload = {
        "type": "topology_event",
        "owner": owner,
        "domain_id": domain_id,
        "topology_id": topology_id,
        "composite_id": composite_id or f"{owner}:{domain_id}:{topology_id}",
        "event_type": event_type,
        "summary": summary,
        "details": details or {},
        "actor_user": actor_user,
        "actor_display_name": actor_display_name or actor_user,
        "created_at": created_at,
    }
    try:
        event_bus.publish_to_users_sync(list(recipients), payload)
    except Exception as exc:  # noqa: BLE001 -- best effort
        logger.debug("[topology_event broadcast] %s", exc)


def _broadcast_deleted_topology(
    *,
    owner: str,
    domain_id: str,
    topology_id: str,
    result: Dict[str, Any],
    actor_user: str,
    actor_display_name: str,
) -> None:
    recipients = result.get("recipients") or []
    topo_name = result.get("name") or topology_id
    event_payload = {
        "type": "topology_event",
        "owner": owner,
        "domain_id": domain_id,
        "topology_id": topology_id,
        "composite_id": f"{owner}:{domain_id}:{topology_id}",
        "event_type": "topology.deleted",
        "summary": f"Deleted '{topo_name}'",
        "details": {"name": topo_name},
        "actor_user": actor_user,
        "actor_display_name": actor_display_name,
        "created_at": "",
    }
    try:
        event_bus.publish_to_users_sync([owner] + list(recipients), event_payload)
    except Exception as exc:  # noqa: BLE001
        logger.debug("[topology.deleted broadcast] %s", exc)

router = APIRouter()
# Per-domain "project workspace" knowledge (feature branches, Jira EPICs,
# notes, CLI presets, ...). Mounted on the same /api/domains prefix so
# paths look like /api/domains/{domain_id}/knowledge/*.
router.include_router(knowledge_subrouter)


# -- Domain CRUD --

@router.get("", response_model=List[TopologyDomainInfo])
async def list_domains(user=Depends(get_current_user)):
    domains = user_store.list_domains(user["username"])
    return [
        TopologyDomainInfo(
            id=d["id"],
            name=d["name"],
            description=d.get("description", ""),
            owner=d.get("owner", user["username"]),
            is_shared=d.get("is_shared", False),
            shared_with=d.get("shared_with", []),
            topology_count=d.get("topology_count", 0),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            is_built_in=d.get("is_built_in", False),
            is_locked=d.get("is_locked", False),
            is_shared_with_me_domain=d.get("is_shared_with_me_domain", False),
            permission=d.get("permission"),
            original_domain_id=d.get("original_domain_id"),
        )
        for d in domains
    ]


@router.post("", response_model=TopologyDomainInfo, status_code=201)
async def create_domain(req: TopologyDomainCreate, user=Depends(get_current_user)):
    domain = user_store.create_domain(user["username"], req.name, req.description)
    return TopologyDomainInfo(**domain)


@router.delete("/{domain_id}")
async def delete_domain(domain_id: str, user=Depends(get_current_user)):
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        raise HTTPException(
            status_code=400,
            detail="The 'Shared with me' domain is built-in and cannot be deleted",
        )
    topologies = user_store.list_topologies(user["username"], domain_id)
    if topologies:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Domain contains {len(topologies)} topology file(s). "
                "Delete or move individual topologies before deleting the domain."
            ),
        )
    ok = user_store.delete_domain(user["username"], domain_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Cannot delete default domain")
    return {"status": "deleted", "domain_id": domain_id}


# -- Sharing --

@router.post("/{domain_id}/share")
async def share_domain(domain_id: str, req: ShareDomainRequest, user=Depends(get_current_user)):
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        raise HTTPException(
            status_code=400,
            detail="The 'Shared with me' domain cannot be re-shared",
        )
    for target in req.target_users:
        if not user_store.get_user(target):
            raise HTTPException(status_code=404, detail=f"User '{target}' not found")
    ok = user_store.share_domain(
        user["username"], domain_id, req.target_users, req.permission,
        actor=user["username"],
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Domain not found")

    # Live-push a ``domain_share`` frame to every NEW / CHANGED recipient so
    # their Shared-with-me dropdown refreshes without a manual reload.
    # (Until 2026-04-24 only per-FILE shares broadcast, so adding a whole
    # domain silently left recipients on stale state. See
    # DEVELOPMENT_GUIDELINES.md "2026-04-24d: sharing/unsharing bugs".)
    actor_display = _actor_display(user)
    domain_name = ""
    try:
        _domains_all = user_store.list_domains(user["username"])
        _d = next((d for d in _domains_all if d["id"] == domain_id), None)
        if _d:
            domain_name = _d.get("name") or ""
    except Exception as _exc:  # noqa: BLE001 -- best effort for metadata
        logger.debug("[share_domain name lookup] %s", _exc)
    targets = [t for t in (req.target_users or []) if t and t != user["username"]]
    if targets:
        payload = {
            "type": "topology_event",
            "event_type": "domain.shared",
            "owner": user["username"],
            "domain_id": domain_id,
            "topology_id": "",
            "composite_id": f"{user['username']}:{domain_id}",
            "summary": (
                f"{actor_display or user['username']} shared "
                f"'{domain_name or domain_id}' with you [{req.permission}]"
            ),
            "details": {
                "name": domain_name,
                "permission": req.permission,
                "added": targets,
            },
            "actor_user": user["username"],
            "actor_display_name": actor_display,
        }
        try:
            # Owner + each target so both sides refresh live.
            event_bus.publish_to_users_sync([user["username"], *targets], payload)
        except Exception as exc:  # noqa: BLE001 -- best effort
            logger.debug("[share_domain broadcast] %s", exc)
    return {"status": "shared", "domain_id": domain_id, "shared_with": req.target_users}


@router.post("/{domain_id}/unshare")
async def unshare_domain(domain_id: str, req: UnshareRequest, user=Depends(get_current_user)):
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        raise HTTPException(
            status_code=400,
            detail="The 'Shared with me' domain cannot be unshared",
        )
    user_store.unshare_domain(
        user["username"], domain_id, req.target_user, actor=user["username"],
    )

    # Live-push ``domain.unshared`` to the revoked user + owner so both
    # sides drop the row without a manual refresh. Before this, the
    # owner's recipient chip and the recipient's "Shared with me" entry
    # both only updated on next poll / page reload.
    actor_display = _actor_display(user)
    domain_name = ""
    try:
        _domains_all = user_store.list_domains(user["username"])
        _d = next((d for d in _domains_all if d["id"] == domain_id), None)
        if _d:
            domain_name = _d.get("name") or ""
    except Exception as _exc:  # noqa: BLE001 -- best effort
        logger.debug("[unshare_domain name lookup] %s", _exc)
    if req.target_user and req.target_user != user["username"]:
        payload = {
            "type": "topology_event",
            "event_type": "domain.unshared",
            "owner": user["username"],
            "domain_id": domain_id,
            "topology_id": "",
            "composite_id": f"{user['username']}:{domain_id}",
            "summary": (
                f"{actor_display or user['username']} stopped sharing "
                f"'{domain_name or domain_id}' with you"
            ),
            "details": {
                "name": domain_name,
                "target_user": req.target_user,
            },
            "actor_user": user["username"],
            "actor_display_name": actor_display,
        }
        try:
            event_bus.publish_to_users_sync(
                [user["username"], req.target_user], payload,
            )
        except Exception as exc:  # noqa: BLE001 -- best effort
            logger.debug("[unshare_domain broadcast] %s", exc)
    return {"status": "unshared", "domain_id": domain_id, "user": req.target_user}


# -- Sharing Observability --

@router.get("/share/overview", response_model=ShareOverview)
async def share_overview(user=Depends(get_current_user)):
    """Header counters for the Share Topology dialog."""
    return ShareOverview(**user_store.share_overview(user["username"]))


@router.get("/share/targets", response_model=List[ShareTargetUser])
async def share_targets(user=Depends(get_current_user)):
    """All other active users -- visible to every authenticated user (sharing target picker)."""
    return [ShareTargetUser(**u) for u in user_store.list_share_targets(user["username"])]


@router.get("/share/outgoing", response_model=List[OutgoingShareInfo])
async def share_outgoing(user=Depends(get_current_user)):
    """All domains I own that are shared, with recipients + topologies inside each."""
    items = user_store.list_outgoing_shares(user["username"])
    return [
        OutgoingShareInfo(
            domain_id=i["domain_id"],
            composite_id=i["composite_id"],
            name=i["name"],
            description=i.get("description", "") or "",
            owner=i["owner"],
            created_at=i["created_at"],
            updated_at=i["updated_at"],
            topology_count=i.get("topology_count", 0),
            recipient_count=i.get("recipient_count", 0),
            recipients=[ShareRecipient(**r) for r in i.get("recipients", [])],
            topologies=[TopologyMetaLite(**t) for t in i.get("topologies", [])],
        )
        for i in items
    ]


@router.get("/share/incoming", response_model=List[IncomingShareInfo])
async def share_incoming(user=Depends(get_current_user)):
    """All domains shared WITH me, including the topologies inside each."""
    items = user_store.list_incoming_shares(user["username"])
    return [
        IncomingShareInfo(
            domain_id=i["domain_id"],
            original_domain_id=i["original_domain_id"],
            name=i["name"],
            description=i.get("description", "") or "",
            owner=i["owner"],
            owner_display_name=i.get("owner_display_name"),
            owner_role=i.get("owner_role"),
            permission=i["permission"],
            granted_at=i["granted_at"],
            granted_by=i["granted_by"],
            created_at=i["created_at"],
            updated_at=i["updated_at"],
            topology_count=i.get("topology_count", 0),
            topologies=[TopologyMetaLite(**t) for t in i.get("topologies", [])],
        )
        for i in items
    ]


@router.get("/share/activity", response_model=List[ShareActivityEntry])
async def share_activity(
    scope: str = "involving",
    domain_id: str = "",
    limit: int = 100,
    user=Depends(get_current_user),
):
    """Audit-log entries for share/unshare/permission_change events relevant to me."""
    items = user_store.list_share_activity(
        user["username"], scope=scope, domain_id=domain_id or None, limit=limit,
    )
    return [ShareActivityEntry(**i) for i in items]


@router.get("/{domain_id}/shares", response_model=List[ShareRecipient])
async def list_domain_shares(domain_id: str, user=Depends(get_current_user)):
    """All users a specific domain I own is currently shared with."""
    domains = user_store.list_domains(user["username"])
    target = next((d for d in domains if d["id"] == domain_id and not d.get("is_shared")), None)
    if not target:
        raise HTTPException(status_code=404, detail="Domain not found or not owned by you")
    return [ShareRecipient(**r) for r in user_store.list_domain_shares(user["username"], domain_id)]


# -- Per-file (per-topology) Sharing --

@router.get("/share/files/outgoing", response_model=List[OutgoingTopologyShareInfo])
async def share_files_outgoing(user=Depends(get_current_user)):
    """All individual topology files I have shared, with recipients."""
    items = user_store.list_outgoing_topology_shares(user["username"])
    return [
        OutgoingTopologyShareInfo(
            composite_id=i["composite_id"],
            owner=i["owner"],
            domain_id=i["domain_id"],
            topology_id=i["topology_id"],
            name=i["name"],
            created_at=i["created_at"],
            updated_at=i["updated_at"],
            object_count=i.get("object_count", 0),
            device_count=i.get("device_count", 0),
            link_count=i.get("link_count", 0),
            recipient_count=i.get("recipient_count", 0),
            recipients=[ShareRecipient(**r) for r in i.get("recipients", [])],
        )
        for i in items
    ]


@router.get("/share/files/incoming", response_model=List[IncomingTopologyShareInfo])
async def share_files_incoming(user=Depends(get_current_user)):
    """All individual topology files shared WITH me (populates the 'Shared with me' domain)."""
    items = user_store.list_incoming_topology_shares(user["username"])
    return [
        IncomingTopologyShareInfo(
            id=i["id"],
            composite_id=i["composite_id"],
            domain_id=i["domain_id"],
            owner=i["owner"],
            owner_display_name=i.get("owner_display_name"),
            owner_role=i.get("owner_role"),
            source_domain_id=i["source_domain_id"],
            source_topology_id=i["source_topology_id"],
            name=i["name"],
            created_at=i["created_at"],
            updated_at=i["updated_at"],
            object_count=i.get("object_count", 0),
            device_count=i.get("device_count", 0),
            link_count=i.get("link_count", 0),
            permission=i["permission"],
            granted_at=i["granted_at"],
            granted_by=i["granted_by"],
            is_shared_with_me=True,
        )
        for i in items
    ]


@router.post("/{domain_id}/topologies/{topology_id}/share")
async def share_topology(
    domain_id: str,
    topology_id: str,
    req: ShareTopologyRequest,
    user=Depends(get_current_user),
):
    """Share a single topology file with selected users."""
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        raise HTTPException(
            status_code=400,
            detail="You cannot reshare a topology that was shared with you",
        )
    for target in req.target_users:
        if not user_store.get_user(target):
            raise HTTPException(status_code=404, detail=f"User '{target}' not found")
    # Caller must actually own this topology -- domain access is checked first.
    domains = user_store.list_domains(user["username"])
    owned = next((d for d in domains if d["id"] == domain_id and not d.get("is_shared")), None)
    if not owned:
        raise HTTPException(status_code=403, detail="You can only share topologies you own")
    result = user_store.share_topology(
        user["username"], domain_id, topology_id,
        req.target_users, req.permission,
        actor=user["username"],
        actor_display_name=_actor_display(user),
    )
    if not result.get("ok"):
        reason = result.get("reason")
        if reason == "not_found":
            raise HTTPException(status_code=404, detail="Topology not found")
        raise HTTPException(status_code=400, detail="Cannot share this topology")

    actor_display = _actor_display(user)
    added_users: List[str] = result.get("added") or []
    changed_entries: List[Dict[str, Any]] = result.get("changed") or []
    topo_name = result.get("name") or ""
    if added_users:
        _broadcast_topology_event(
            owner=user["username"],
            domain_id=domain_id,
            topology_id=topology_id,
            event_type="topology.shared",
            summary=(
                f"Shared '{topo_name}' with {added_users[0]}"
                + (f" (+{len(added_users) - 1} more)" if len(added_users) > 1 else "")
                + f" [{req.permission}]"
            ),
            details={
                "added": added_users,
                "permission": req.permission,
                "name": topo_name,
            },
            actor_user=user["username"],
            actor_display_name=actor_display,
            extra_recipients=added_users,
        )
    for ch in changed_entries:
        _broadcast_topology_event(
            owner=user["username"],
            domain_id=domain_id,
            topology_id=topology_id,
            event_type="topology.permission_changed",
            summary=(
                f"Changed {ch.get('user')} access "
                f"{ch.get('from')} -> {ch.get('to')}"
            ),
            details=ch,
            actor_user=user["username"],
            actor_display_name=actor_display,
            extra_recipients=[ch.get("user")] if ch.get("user") else None,
        )
    return {
        "status": "shared",
        "domain_id": domain_id,
        "topology_id": topology_id,
        "shared_with": req.target_users,
        "added": added_users,
        "changed": changed_entries,
    }


@router.post("/{domain_id}/topologies/{topology_id}/unshare")
async def unshare_topology(
    domain_id: str,
    topology_id: str,
    req: UnshareRequest,
    user=Depends(get_current_user),
):
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        raise HTTPException(
            status_code=400,
            detail="Files in 'Shared with me' are not shared by you",
        )
    result = user_store.unshare_topology(
        user["username"], domain_id, topology_id, req.target_user,
        actor=user["username"],
        actor_display_name=_actor_display(user),
    )
    if result.get("removed"):
        topo_name = result.get("name") or topology_id
        _broadcast_topology_event(
            owner=user["username"],
            domain_id=domain_id,
            topology_id=topology_id,
            event_type="topology.unshared",
            summary=f"Revoked {req.target_user}'s access to '{topo_name}'",
            details={"target_user": req.target_user, "name": topo_name},
            actor_user=user["username"],
            actor_display_name=_actor_display(user),
            # Also fan the event to the now-removed recipient so their
            # "Shared with me" list can drop the row live instead of
            # waiting for the next poll.
            extra_recipients=[req.target_user],
        )
    return {
        "status": "unshared",
        "domain_id": domain_id,
        "topology_id": topology_id,
        "user": req.target_user,
    }


@router.get("/{domain_id}/topologies/{topology_id}/shares", response_model=List[ShareRecipient])
async def list_topology_shares(
    domain_id: str, topology_id: str, user=Depends(get_current_user),
):
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        raise HTTPException(
            status_code=400,
            detail="Files in 'Shared with me' are not shared by you",
        )
    domains = user_store.list_domains(user["username"])
    owned = next((d for d in domains if d["id"] == domain_id and not d.get("is_shared")), None)
    if not owned:
        raise HTTPException(status_code=403, detail="You can only inspect shares for topologies you own")
    rows = user_store.list_topology_shares(user["username"], domain_id, topology_id)
    return [ShareRecipient(**r) for r in rows]


# -- Recipient-side self-removal --
#
# Lets the target user evict a share from THEIR own "Shared with me"
# view without needing the owner to revoke. Affects only the caller's
# row in topology_shares / domain_shares -- the owner's original file
# and every other recipient are untouched. The owner can always
# re-share to the same user; the endpoint is idempotent (removing an
# already-removed share returns 200 with removed=false so the UI can
# drop the stale row without a modal error).

@router.post("/share/files/incoming/{composite_id:path}/remove")
async def remove_own_incoming_topology_share(
    composite_id: str, user=Depends(get_current_user),
):
    """Recipient self-removes one per-file share from their inbox."""
    result = user_store.remove_own_incoming_topology_share(
        user["username"], composite_id,
    )
    # Honest 404 when no matching share row exists for the caller -- the
    # frontend treats a 200 as "row gone" and optimistically strips the
    # UI entry, which would mask a silent failure caused by e.g. a
    # stale composite_id. The stricter status code lets the client
    # surface a real error toast instead of quietly succeeding.
    if not result.get("removed"):
        raise HTTPException(
            status_code=404,
            detail="Shared file not found in your inbox",
        )
    return {
        "status": "removed",
        "composite_id": composite_id,
        "removed": True,
        "owner": result.get("owner"),
    }


@router.post("/share/incoming/{domain_id:path}/remove")
async def remove_own_incoming_domain_share(
    domain_id: str, user=Depends(get_current_user),
):
    """Recipient self-removes a whole shared-in domain from their inbox.

    Accepts either form of `domain_id`:
    - Composite `<owner>:<raw_id>` (canonical key used by the share
      tables), or
    - Raw `<raw_id>` produced by `/api/domains` for shared-in rows
      (because list_domains rewrites the composite to just the raw id
      so it matches the owner-side topology table). If a raw id comes
      in and more than one owner has shared a domain with that id to
      this user, the router rejects the call and asks the client to
      disambiguate -- in practice the frontend always has the owner on
      hand and synthesizes the composite itself.
    """
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        raise HTTPException(
            status_code=400,
            detail="The 'Shared with me' inbox itself cannot be removed",
        )
    resolved_id = domain_id
    if ":" not in domain_id:
        # Raw id -> disambiguate against the caller's current inbox.
        # `list_incoming_shares` returns one row per (owner, domain)
        # and stores the composite in `domain_id`; matching on
        # `original_domain_id` narrows us back to the composite.
        candidates = [
            s for s in user_store.list_incoming_shares(user["username"])
            if s.get("original_domain_id") == domain_id
        ]
        if len(candidates) == 1:
            resolved_id = candidates[0]["domain_id"]
        elif len(candidates) > 1:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Multiple owners have shared a domain with id "
                    f"'{domain_id}'. Pass the composite '<owner>:<id>' form."
                ),
            )
        # len == 0 -> fall through, user_store will report not_found
        # and we'll raise 404 below.
    result = user_store.remove_own_incoming_domain_share(
        user["username"], resolved_id,
    )
    if not result.get("removed"):
        raise HTTPException(
            status_code=404,
            detail="Shared domain not found in your inbox",
        )
    return {
        "status": "removed",
        "domain_id": resolved_id,
        "removed": True,
        "owner": result.get("owner"),
    }


# -- Topologies within a Domain --

@router.get("/{domain_id}/topologies", response_model=List[TopologyMeta])
async def list_topologies(domain_id: str, user=Depends(get_current_user)):
    _resolve_domain_access(user["username"], domain_id)
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        # Synthetic inbox: rows come from the central per-file share table.
        rows = user_store.list_incoming_topology_shares(user["username"])
        return [_topology_meta_from_share(r) for r in rows]
    owner = _domain_owner(user["username"], domain_id)
    topos = user_store.list_topologies(owner, domain_id)
    return [TopologyMeta(**t) for t in topos]


@router.post("/{domain_id}/topologies/cleanup")
async def cleanup_domain_topologies(
    domain_id: str,
    body: Dict[str, Any] = Body(default_factory=dict),
    user=Depends(get_current_user),
):
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        raise HTTPException(
            status_code=400,
            detail="You cannot clean topologies from 'Shared with me'",
        )
    _resolve_domain_access(user["username"], domain_id, require_write=True)
    owner = _domain_owner(user["username"], domain_id)
    if owner != user["username"]:
        raise HTTPException(status_code=403, detail="Only the domain owner can clean domain topologies")
    existing = user_store.list_topologies(owner, domain_id)
    requested = body.get("topology_ids") or body.get("ids") or []
    delete_all = bool(body.get("delete_all"))
    requested_ids = {str(tid) for tid in requested if str(tid or "").strip()}
    if delete_all:
        targets = existing
    else:
        targets = [t for t in existing if str(t.get("id")) in requested_ids]
    if not targets:
        return {
            "ok": False,
            "error": "Select at least one topology to delete",
            "code": "empty-cleanup-selection",
            "domain_id": domain_id,
            "topologies": existing,
        }
    actor_display = _actor_display(user)
    deleted = []
    for topo in targets:
        topology_id = str(topo.get("id") or "")
        if not topology_id:
            continue
        result = user_store.delete_topology(
            owner, domain_id, topology_id,
            actor=user["username"], actor_display_name=actor_display,
        )
        if result.get("deleted"):
            deleted.append({"id": topology_id, "name": result.get("name") or topo.get("name") or topology_id})
            _broadcast_deleted_topology(
                owner=owner,
                domain_id=domain_id,
                topology_id=topology_id,
                result=result,
                actor_user=user["username"],
                actor_display_name=actor_display,
            )
    return {
        "ok": True,
        "domain_id": domain_id,
        "deleted_count": len(deleted),
        "deleted": deleted,
        "remaining": user_store.list_topologies(owner, domain_id),
    }


@router.post("/{domain_id}/topologies", response_model=TopologyMeta, status_code=201)
async def save_topology(
    domain_id: str,
    req: TopologySave,
    base_updated_at: Optional[str] = Query(None),
    user=Depends(get_current_user),
):
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        raise HTTPException(
            status_code=400,
            detail="You cannot create new topologies inside 'Shared with me'",
        )
    _resolve_domain_access(user["username"], domain_id, require_write=True)
    owner = _domain_owner(user["username"], domain_id)
    actor = user["username"]
    actor_display = _actor_display(user)
    micro_events = req.data.get("__micro_events") if isinstance(req.data, dict) else None
    if isinstance(req.data, dict) and "__micro_events" in req.data:
        # Strip the client-only payload before it gets persisted as part
        # of the topology JSON -- it's pure log metadata, not canvas state.
        req_data = dict(req.data)
        req_data.pop("__micro_events", None)
    else:
        req_data = req.data
    try:
        topo = user_store.save_topology(
            owner, domain_id, req.name, req_data,
            actor=actor, actor_display_name=actor_display,
            base_updated_at=base_updated_at,
            micro_events=micro_events if isinstance(micro_events, list) else None,
        )
    except TopologyConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "conflict",
                "current_updated_at": exc.current_updated_at,
                "last_actor": exc.last_actor,
                "last_actor_display_name": exc.last_actor_display,
            },
        )
    except DomainTopologyLimitError as exc:
        _raise_domain_limit(exc)
    _broadcast_topology_event(
        owner=topo.get("__owner") or owner,
        domain_id=topo.get("__real_domain_id") or domain_id,
        topology_id=topo.get("__real_topology_id") or topo.get("id"),
        event_type=topo.get("__event_type") or "topology.created",
        summary=topo.get("__event_summary") or f"Created '{req.name}'",
        details=topo.get("__event_details") or {},
        actor_user=actor,
        actor_display_name=actor_display,
        created_at=topo.get("updated_at") or "",
    )
    return TopologyMeta(**_strip_internal_topo_fields(topo))


@router.put("/{domain_id}/topologies/{topology_id}", response_model=TopologyMeta)
async def update_topology(
    domain_id: str,
    topology_id: str,
    req: TopologySave,
    base_updated_at: Optional[str] = Query(None),
    user=Depends(get_current_user),
):
    _resolve_domain_access(user["username"], domain_id, require_write=True)
    actor = user["username"]
    actor_display = _actor_display(user)
    micro_events = req.data.get("__micro_events") if isinstance(req.data, dict) else None
    if isinstance(req.data, dict) and "__micro_events" in req.data:
        req_data = dict(req.data)
        req_data.pop("__micro_events", None)
    else:
        req_data = req.data
    try:
        if domain_id == SHARED_WITH_ME_DOMAIN_ID:
            # The store inspects the share row + write permission for us.
            topo = user_store.save_topology(
                user["username"], domain_id, req.name, req_data,
                topology_id=topology_id,
                actor=actor, actor_display_name=actor_display,
                base_updated_at=base_updated_at,
                micro_events=micro_events if isinstance(micro_events, list) else None,
            )
        else:
            owner = _domain_owner(user["username"], domain_id)
            topo = user_store.save_topology(
                owner, domain_id, req.name, req_data, topology_id=topology_id,
                actor=actor, actor_display_name=actor_display,
                base_updated_at=base_updated_at,
                micro_events=micro_events if isinstance(micro_events, list) else None,
            )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except TopologyConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "conflict",
                "current_updated_at": exc.current_updated_at,
                "last_actor": exc.last_actor,
                "last_actor_display_name": exc.last_actor_display,
            },
        )
    except DomainTopologyLimitError as exc:
        _raise_domain_limit(exc)
    _broadcast_topology_event(
        owner=topo.get("__owner") or "",
        domain_id=topo.get("__real_domain_id") or domain_id,
        topology_id=topo.get("__real_topology_id") or topology_id,
        event_type=topo.get("__event_type") or "topology.saved",
        summary=topo.get("__event_summary") or f"Saved '{req.name}'",
        details=topo.get("__event_details") or {},
        actor_user=actor,
        actor_display_name=actor_display,
        created_at=topo.get("updated_at") or "",
    )
    return TopologyMeta(**_strip_internal_topo_fields(topo))


@router.get("/{domain_id}/topologies/{topology_id}")
async def load_topology(domain_id: str, topology_id: str, user=Depends(get_current_user)):
    _resolve_domain_access(user["username"], domain_id)
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        # The store resolves the composite id -> (owner, domain, topology) for us.
        topo = user_store.load_topology(user["username"], domain_id, topology_id)
        if not topo:
            raise HTTPException(status_code=404, detail="Topology not found or no longer shared with you")
        # Synthetic-domain loads ALWAYS strip passwords (they came from someone else).
        _strip_passwords(topo)
        return topo
    owner = _domain_owner(user["username"], domain_id)
    topo = user_store.load_topology(owner, domain_id, topology_id)
    if not topo:
        raise HTTPException(status_code=404, detail="Topology not found")
    if owner != user["username"]:
        _strip_passwords(topo)
    return topo


@router.delete("/{domain_id}/topologies/{topology_id}")
async def delete_topology(domain_id: str, topology_id: str, user=Depends(get_current_user)):
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        raise HTTPException(
            status_code=400,
            detail="You cannot delete a topology that was shared with you",
        )
    _resolve_domain_access(user["username"], domain_id, require_write=True)
    owner = _domain_owner(user["username"], domain_id)
    actor_display = _actor_display(user)
    result = user_store.delete_topology(
        owner, domain_id, topology_id,
        actor=user["username"], actor_display_name=actor_display,
    )
    if result.get("deleted"):
        # Fan a final "deleted by X" frame to every user who had this file
        # shared (the owner and the per-file recipients). We broadcast
        # BEFORE the next /events poll so clients drop the file from
        # their UI immediately instead of staring at a ghost row.
        _broadcast_deleted_topology(
            owner=owner,
            domain_id=domain_id,
            topology_id=topology_id,
            result=result,
            actor_user=user["username"],
            actor_display_name=actor_display,
        )
    return {"status": "deleted", "topology_id": topology_id}


# -- Per-topology activity log -----------------------------------------------
#
# Read via the "Logs" button in the left toolbar. Scoped to the CURRENTLY
# opened topology; the frontend passes the domain + topology id (or the
# composite id for a shared-in file -- the store transparently resolves
# either shape).

@router.get("/{domain_id}/topologies/{topology_id}/events")
async def list_topology_events(
    domain_id: str,
    topology_id: str,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None, alias="type"),
    since: Optional[str] = Query(None),
    until: Optional[str] = Query(None),
    user=Depends(get_current_user),
):
    owner, real_domain_id, real_topology_id = _resolve_log_target(
        user["username"], domain_id, topology_id,
    )
    payload = user_store.list_topology_events(
        owner=owner,
        domain_id=real_domain_id,
        topology_id=real_topology_id,
        limit=limit, offset=offset,
        q=q, actor=actor, event_type=event_type,
        since=since, until=until,
    )
    # Echo the composite identity back so the frontend can cache the log
    # per (composite_id) and not remount on every refresh.
    payload["composite_id"] = f"{owner}:{real_domain_id}:{real_topology_id}"
    payload["owner"] = owner
    payload["domain_id"] = real_domain_id
    payload["topology_id"] = real_topology_id
    return payload


@router.post("/{domain_id}/topologies/{topology_id}/events", status_code=201)
async def record_topology_event(
    domain_id: str,
    topology_id: str,
    body: Dict[str, Any] = Body(...),
    user=Depends(get_current_user),
):
    """Client-emitted event (used for canvas micro-ops that don't pass
    through save_topology, e.g. renames applied between saves).
    Rate-limited implicitly by the 500-per-topology prune window.
    """
    owner, real_domain_id, real_topology_id = _resolve_log_target(
        user["username"], domain_id, topology_id, require_write=True,
    )
    event_type = str(body.get("event_type") or "").strip() or "client.event"
    summary = str(body.get("summary") or "").strip()
    if not summary:
        raise HTTPException(status_code=400, detail="summary is required")
    details = body.get("details") if isinstance(body.get("details"), dict) else {}
    actor_display = _actor_display(user)
    row = user_store.record_topology_event(
        owner=owner,
        domain_id=real_domain_id,
        topology_id=real_topology_id,
        actor_user=user["username"],
        actor_display_name=actor_display,
        event_type=event_type,
        summary=summary[:500],
        details=details,
    )
    _broadcast_topology_event(
        owner=owner,
        domain_id=real_domain_id,
        topology_id=real_topology_id,
        event_type=event_type,
        summary=summary[:500],
        details=details,
        actor_user=user["username"],
        actor_display_name=actor_display,
        created_at=row.get("created_at") or "",
    )
    return row


@router.get("/{domain_id}/topologies/{topology_id}/events/export")
async def export_topology_events(
    domain_id: str,
    topology_id: str,
    format: str = Query("json"),
    q: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None, alias="type"),
    since: Optional[str] = Query(None),
    until: Optional[str] = Query(None),
    user=Depends(get_current_user),
):
    """Dump the currently filtered log as JSON or CSV. Same filters as
    the list endpoint; we pull a larger page (up to 1000 rows) and
    stream it back with a friendly filename so the browser presents a
    download dialog. Useful for sharing audit data out-of-band.
    """
    from fastapi.responses import Response, StreamingResponse
    import csv
    import io
    import json as _json

    owner, real_domain_id, real_topology_id = _resolve_log_target(
        user["username"], domain_id, topology_id,
    )
    payload = user_store.list_topology_events(
        owner=owner, domain_id=real_domain_id, topology_id=real_topology_id,
        limit=1000, offset=0,
        q=q, actor=actor, event_type=event_type, since=since, until=until,
    )
    items = payload.get("items", [])

    fmt = (format or "json").lower().strip()
    fname_base = f"topology-log_{real_topology_id}"
    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "created_at", "event_type", "actor_user", "actor_display_name",
            "summary", "details",
        ])
        for it in items:
            writer.writerow([
                it.get("created_at", ""),
                it.get("event_type", ""),
                it.get("actor_user", ""),
                it.get("actor_display_name", ""),
                it.get("summary", ""),
                _json.dumps(it.get("details", {}), ensure_ascii=False),
            ])
        return Response(
            content=buf.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{fname_base}.csv"',
            },
        )
    return Response(
        content=_json.dumps(payload, ensure_ascii=False, indent=2),
        media_type="application/json; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{fname_base}.json"',
        },
    )


def _resolve_log_target(
    username: str,
    domain_id: str,
    topology_id: str,
    require_write: bool = False,
):
    """Translate (viewer, domain_id, topology_id) into the canonical
    (owner, real_domain_id, real_topology_id) under which the event log
    is stored. Handles the 'Shared with me' composite-id case and
    enforces read/write access.
    """
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        share = user_store.resolve_shared_topology(username, topology_id)
        if not share:
            raise HTTPException(
                status_code=404,
                detail="Topology not found or no longer shared with you",
            )
        if require_write and share.get("permission") != "write":
            raise HTTPException(
                status_code=403,
                detail="You only have read access to this shared topology",
            )
        return share["owner"], share["domain_id"], share["topology_id"]
    _resolve_domain_access(username, domain_id, require_write=require_write)
    owner = _domain_owner(username, domain_id)
    return owner, domain_id, topology_id


def _strip_internal_topo_fields(topo: Dict[str, Any]) -> Dict[str, Any]:
    """Remove the ``__owner`` / ``__event_*`` markers we used to shuttle
    broadcast metadata from user_store.save_topology back up to the
    route so they don't leak into the TopologyMeta response shape."""
    return {k: v for k, v in (topo or {}).items() if not k.startswith("__")}


# -- Helpers --

def _domain_owner(username: str, domain_id: str) -> str:
    """For shared domains, return the actual owner; for own domains, return username."""
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        # Synthetic domain has no single owner -- callers must dispatch by viewer.
        return username
    domains = user_store.list_domains(username)
    for d in domains:
        if d["id"] == domain_id:
            return d.get("owner", username)
    return username


def _strip_passwords(topo: dict) -> None:
    """Remove SSH passwords from topology data when serving shared topologies."""
    data = topo.get("data")
    if not isinstance(data, dict):
        return
    for device in data.get("devices", []):
        ssh_cfg = device.get("sshConfig")
        if isinstance(ssh_cfg, dict) and "password" in ssh_cfg:
            ssh_cfg["password"] = ""


def _resolve_domain_access(username: str, domain_id: str, require_write: bool = False):
    """Verify the user has access to this domain (own or shared)."""
    domains = user_store.list_domains(username)
    for d in domains:
        if d["id"] == domain_id:
            # The synthetic "Shared with me" inbox is always readable. Per-file
            # write permissions are enforced inside the storage layer.
            if d.get("is_shared_with_me_domain"):
                return
            if require_write and d.get("is_shared") and d.get("permission") == "read":
                raise HTTPException(
                    status_code=403,
                    detail="Read-only access to this shared domain",
                )
            return
    raise HTTPException(status_code=404, detail="Domain not found or access denied")


def _topology_meta_from_share(row: Dict[str, Any]) -> TopologyMeta:
    """Adapt an IncomingTopologyShare row to the TopologyMeta payload the dropdown expects."""
    return TopologyMeta(
        id=row["id"],
        name=row["name"],
        domain_id=row["domain_id"],
        created_at=row.get("created_at", ""),
        updated_at=row.get("updated_at", ""),
        object_count=row.get("object_count", 0),
        device_count=row.get("device_count", 0),
        link_count=row.get("link_count", 0),
        is_shared_with_me=True,
        owner=row.get("owner"),
        owner_display_name=row.get("owner_display_name"),
        permission=row.get("permission"),
        source_domain_id=row.get("source_domain_id"),
        source_topology_id=row.get("source_topology_id"),
        # Expose the share key so the UI's "Remove from my list" button
        # can POST to /api/domains/share/files/incoming/<composite_id>/
        # remove without re-synthesizing it on the client.
        composite_id=row.get("composite_id") or row.get("id"),
    )
