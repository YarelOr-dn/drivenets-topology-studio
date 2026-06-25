"""REST endpoints for per-domain knowledge.

Mounted under ``/api/domains/{domain_id}/knowledge`` via ``router.py``.

Every endpoint is per-user-authenticated. The hybrid-sharing rules are
enforced inside ``user_store`` (``upsert_domain_knowledge`` raises
``PermissionError`` when a read-only viewer tries to write a public row).

Endpoints:
    GET  /{domain_id}/knowledge                      -- list all kinds
    POST /{domain_id}/knowledge                      -- add an item
    PUT  /{domain_id}/knowledge/{kind}/{key}         -- update an item
    DELETE /{domain_id}/knowledge/{kind}/{key}       -- delete
    POST /{domain_id}/knowledge/{kind}/{key}/refresh -- force live refresh
    POST /{domain_id}/knowledge/refresh-all          -- bulk-refresh all live items
    GET  /knowledge/kinds                            -- metadata for UI tabs
    GET  /knowledge/poller/status                    -- live poller health
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth.service import get_current_user
from ..auth.user_store import SHARED_WITH_ME_DOMAIN_ID, user_store
from . import knowledge as knowledge_module

logger = logging.getLogger(__name__)

router = APIRouter()

# -- Safety caps -------------------------------------------------------------

# Serialized payload size ceiling per row. Notes are the biggest legitimate
# payload and are unlikely to exceed a few KB; 64 KB is a comfortable upper
# bound that also protects against buggy/malicious clients.
MAX_PAYLOAD_BYTES = 64 * 1024

# Max simultaneous live-fetch HTTP calls per user during /refresh-all.
# Prevents one user with 50 attached branches from thundering-herd Jenkins
# when they click the global Refresh button.
REFRESH_ALL_CONCURRENCY = 4


# -- Schemas -----------------------------------------------------------------

class KnowledgeItem(BaseModel):
    domain_id: str
    visibility: str
    kind: str
    key: str
    payload: Dict[str, Any]
    pinned: bool = False
    sort_order: int = 0
    created_at: str = ""
    updated_at: str = ""
    scope_is_mine: bool = True
    editable: bool = True
    author: str = ""


class KnowledgeUpsert(BaseModel):
    kind: str = Field(..., description="Registered knowledge kind (see /knowledge/kinds)")
    key: Optional[str] = Field(None, description="Natural key; derived from payload when omitted")
    payload: Dict[str, Any] = Field(default_factory=dict)
    visibility: str = Field("public", description="'public' (travels with share) or 'private' (per-viewer)")
    pinned: Optional[bool] = None
    sort_order: Optional[int] = None


class KnowledgeListResponse(BaseModel):
    domain_id: str
    permission: str
    is_shared_in: bool
    owner: str
    items: List[KnowledgeItem]


class KindDescriptor(BaseModel):
    kind: str
    label: str
    description: str
    supports_live: bool
    allows_multiple: bool


# -- Helpers -----------------------------------------------------------------

def _validate_visibility(visibility: str) -> str:
    if visibility not in ("public", "private"):
        raise HTTPException(status_code=400, detail="visibility must be 'public' or 'private'")
    return visibility


def _reject_shared_with_me(domain_id: str) -> None:
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        raise HTTPException(
            status_code=400,
            detail="The 'Shared with me' inbox is synthetic and cannot hold knowledge",
        )


def _require_scope(username: str, domain_id: str) -> Dict[str, Any]:
    scope = user_store.resolve_domain_scope(username, domain_id)
    if not scope:
        raise HTTPException(status_code=404, detail="Domain not found or access denied")
    return scope


def _guard_payload_size(payload: Dict[str, Any]) -> None:
    """Refuse oversized payloads at the edge so one buggy client can't
    fill a user's DB. ``MAX_PAYLOAD_BYTES`` is generous for notes and
    tiny for anything malicious."""
    try:
        blob = json.dumps(payload or {})
    except (TypeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"payload is not JSON-serialisable: {e}")
    if len(blob.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"payload exceeds {MAX_PAYLOAD_BYTES // 1024} KB limit",
        )


def _to_item(row: Dict[str, Any]) -> KnowledgeItem:
    payload = row.get("payload")
    if isinstance(payload, str):
        try:
            payload = json.loads(payload) if payload else {}
        except Exception:
            payload = {}
    return KnowledgeItem(
        domain_id=row.get("domain_id", ""),
        visibility=row.get("visibility", "public"),
        kind=row.get("kind", ""),
        key=row.get("key", ""),
        payload=payload or {},
        pinned=bool(row.get("pinned") or 0),
        sort_order=int(row.get("sort_order") or 0),
        created_at=row.get("created_at") or "",
        updated_at=row.get("updated_at") or "",
        scope_is_mine=bool(row.get("scope_is_mine", True)),
        editable=bool(row.get("editable", True)),
        author=row.get("author") or "",
    )


# -- Kind discovery ---------------------------------------------------------

@router.get("/knowledge/kinds", response_model=List[KindDescriptor])
async def list_kinds(user=Depends(get_current_user)):
    """Metadata for every registered kind -- used by the frontend to render tabs."""
    return [KindDescriptor(**k) for k in knowledge_module.all_kinds()]


# -- Per-domain knowledge CRUD ---------------------------------------------

@router.get("/{domain_id}/knowledge", response_model=KnowledgeListResponse)
async def list_knowledge(domain_id: str, user=Depends(get_current_user)):
    _reject_shared_with_me(domain_id)
    scope = _require_scope(user["username"], domain_id)
    rows = user_store.list_domain_knowledge(user["username"], domain_id)
    return KnowledgeListResponse(
        domain_id=domain_id,
        permission=scope["permission"],
        is_shared_in=scope["is_shared_in"],
        owner=scope["owner"],
        items=[_to_item(r) for r in rows],
    )


@router.post("/{domain_id}/knowledge", response_model=KnowledgeItem, status_code=201)
async def add_knowledge(
    domain_id: str,
    req: KnowledgeUpsert,
    user=Depends(get_current_user),
):
    _reject_shared_with_me(domain_id)
    _validate_visibility(req.visibility)
    if not knowledge_module.get_spec(req.kind):
        raise HTTPException(status_code=400, detail=f"Unknown knowledge kind: {req.kind}")
    try:
        clean_payload = knowledge_module.validate_payload(req.kind, req.payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    _guard_payload_size(clean_payload)
    key = (req.key or knowledge_module.derive_key(req.kind, clean_payload)).strip()
    if not key:
        raise HTTPException(status_code=400, detail="Could not derive a natural key for this item")

    # Kinds with allows_multiple=False (bugs_scope, ai_scope) collapse onto a
    # single row per domain. Force the key so the UI can't accidentally create
    # two rows by picking different keys.
    spec = knowledge_module.get_spec(req.kind)
    allows_multiple = spec.kind not in {"bugs_scope", "ai_scope"}
    if not allows_multiple:
        key = "default"

    try:
        row = user_store.upsert_domain_knowledge(
            user["username"], domain_id, req.kind, key, clean_payload,
            visibility=req.visibility, pinned=req.pinned, sort_order=req.sort_order,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Schedule an inline live fetch so the UI sees status immediately without
    # having to poll /refresh. We use ``create_task`` instead of executor so
    # the coroutine is owned by the running loop (no warnings on shutdown).
    if spec and spec.supports_live:
        asyncio.create_task(
            _inline_refresh_async(
                user["username"], domain_id, req.kind, key, req.visibility,
            ),
            name=f"dk-inline-refresh:{req.kind}:{key[:16]}",
        )
    return _to_item(row)


@router.put("/{domain_id}/knowledge/{kind}/{key}", response_model=KnowledgeItem)
async def update_knowledge(
    domain_id: str,
    kind: str,
    key: str,
    req: KnowledgeUpsert,
    user=Depends(get_current_user),
):
    _reject_shared_with_me(domain_id)
    _validate_visibility(req.visibility)
    if not knowledge_module.get_spec(kind):
        raise HTTPException(status_code=400, detail=f"Unknown knowledge kind: {kind}")
    try:
        clean_payload = knowledge_module.validate_payload(kind, req.payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    _guard_payload_size(clean_payload)
    try:
        row = user_store.upsert_domain_knowledge(
            user["username"], domain_id, kind, key, clean_payload,
            visibility=req.visibility, pinned=req.pinned, sort_order=req.sort_order,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_item(row)


@router.delete("/{domain_id}/knowledge/{kind}/{key}")
async def delete_knowledge(
    domain_id: str,
    kind: str,
    key: str,
    visibility: str = "public",
    user=Depends(get_current_user),
):
    _reject_shared_with_me(domain_id)
    _validate_visibility(visibility)
    try:
        ok = user_store.delete_domain_knowledge(
            user["username"], domain_id, kind, key, visibility=visibility,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    if not ok:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "deleted", "kind": kind, "key": key, "visibility": visibility}


# -- Reordering helpers ----------------------------------------------------

class ReorderRequest(BaseModel):
    items: List[Dict[str, Any]]


@router.post("/{domain_id}/knowledge/reorder")
async def reorder_knowledge(
    domain_id: str,
    req: ReorderRequest,
    user=Depends(get_current_user),
):
    """Persist a drag-reorder from the UI. ``items`` is a list of
    ``{kind, key, visibility, sort_order, pinned?}`` in the new order."""
    _reject_shared_with_me(domain_id)
    updated = 0
    for entry in req.items:
        kind = (entry.get("kind") or "").strip()
        key = (entry.get("key") or "").strip()
        vis = entry.get("visibility") or "public"
        if vis not in ("public", "private") or not kind or not key:
            continue
        existing = user_store.get_domain_knowledge_item(
            user["username"], domain_id, kind, key, visibility=vis,
        )
        if not existing:
            continue
        try:
            user_store.upsert_domain_knowledge(
                user["username"], domain_id, kind, key, existing["payload"],
                visibility=vis,
                pinned=bool(entry.get("pinned", existing.get("pinned", False))),
                sort_order=int(entry.get("sort_order", 0)),
            )
            updated += 1
        except PermissionError:
            continue
    return {"status": "ok", "updated": updated}


# -- Live refresh ----------------------------------------------------------

@router.post("/{domain_id}/knowledge/{kind}/{key}/refresh", response_model=KnowledgeItem)
async def refresh_knowledge(
    domain_id: str,
    kind: str,
    key: str,
    visibility: str = "public",
    user=Depends(get_current_user),
):
    """Trigger the kind's live_fetcher synchronously and persist the new payload.

    For kinds without ``supports_live`` this is a no-op that returns the
    current row. The background poller covers the same path periodically;
    this endpoint exists so the user can force an on-demand refresh.
    """
    _reject_shared_with_me(domain_id)
    _validate_visibility(visibility)
    existing = user_store.get_domain_knowledge_item(
        user["username"], domain_id, kind, key, visibility=visibility,
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")
    spec = knowledge_module.get_spec(kind)
    if not spec or not spec.supports_live:
        return _to_item(existing)

    new_payload = await asyncio.to_thread(
        knowledge_module.refresh_payload,
        user["username"], kind, existing["payload"],
    )
    if not new_payload:
        return _to_item(existing)
    try:
        row = user_store.upsert_domain_knowledge(
            user["username"], domain_id, kind, key, new_payload,
            visibility=visibility,
            pinned=bool(existing.get("pinned", False)),
            sort_order=int(existing.get("sort_order", 0)),
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return _to_item(row)


@router.post("/{domain_id}/knowledge/refresh-all")
async def refresh_all(
    domain_id: str,
    kind: Optional[str] = None,
    user=Depends(get_current_user),
):
    """Refresh every live-capable row in the domain and return the merged
    post-refresh list.

    ``kind=branch`` restricts to a single kind (common case when the Jenkins
    dashboard wants just branches). Concurrency is capped at
    ``REFRESH_ALL_CONCURRENCY`` simultaneous fetches so a user with 50
    attached branches can't thundering-herd Jenkins.

    Returning the merged items list lets the frontend render the refreshed
    panel in a single round-trip instead of call + re-list.
    """
    _reject_shared_with_me(domain_id)
    rows = user_store.list_domain_knowledge(user["username"], domain_id)
    refreshed = 0
    errors: List[str] = []
    sem = asyncio.Semaphore(REFRESH_ALL_CONCURRENCY)

    async def _one(r: Dict[str, Any]) -> None:
        nonlocal refreshed
        if kind and r.get("kind") != kind:
            return
        spec = knowledge_module.get_spec(r.get("kind", ""))
        if not spec or not spec.supports_live:
            return
        async with sem:
            try:
                new_payload = await asyncio.to_thread(
                    knowledge_module.refresh_payload,
                    user["username"], r["kind"], r["payload"],
                )
            except Exception as exc:  # noqa: BLE001 -- live fetch is best-effort
                errors.append(f"{r['kind']}/{r['key']}: {exc}")
                return
        if not new_payload:
            return
        try:
            await asyncio.to_thread(
                user_store.upsert_domain_knowledge,
                user["username"], domain_id, r["kind"], r["key"], new_payload,
                r.get("visibility", "public"),
                bool(r.get("pinned", False)),
                int(r.get("sort_order", 0)),
            )
            refreshed += 1
        except PermissionError:
            # Read-only share: skip silently.
            return
        except Exception as exc:  # noqa: BLE001 -- DB write is best-effort
            errors.append(f"{r['kind']}/{r['key']}: {exc}")

    await asyncio.gather(*[_one(r) for r in rows], return_exceptions=True)

    # Re-read the merged list AFTER refresh so the response reflects the new
    # payloads. Cheap vs. the HTTP calls above.
    merged = await asyncio.to_thread(
        user_store.list_domain_knowledge, user["username"], domain_id,
    )
    scope = user_store.resolve_domain_scope(user["username"], domain_id) or {}
    return {
        "status": "ok",
        "refreshed": refreshed,
        "total": len(rows),
        "errors": errors[:10],  # cap to keep response small
        "items": [_to_item(r).model_dump() for r in merged],
        "permission": scope.get("permission", "read"),
        "is_shared_in": bool(scope.get("is_shared_in")),
        "owner": scope.get("owner", user["username"]),
    }


# -- Poller health ---------------------------------------------------------

@router.get("/knowledge/poller/status")
async def poller_status(user=Depends(get_current_user)):
    """Lightweight health endpoint for the background knowledge poller.

    Returns per-kind last cycle timestamp, rows fetched, and recent errors.
    Useful for the admin UI and for debugging "why didn't my branch refresh?"
    without digging through logs.
    """
    try:
        from .knowledge_poller import poller
        return poller.status()
    except Exception as exc:  # noqa: BLE001 -- status is purely diagnostic
        return {"status": "unavailable", "error": str(exc)}


# -- Internal: inline refresh helper --------------------------------------

async def _inline_refresh_async(
    viewer: str, domain_id: str, kind: str, key: str, visibility: str,
) -> None:
    """Run the live fetcher once after an add, then push a WS update.

    Unlike the previous executor-fire-and-forget pattern this:
      1. Verifies the row still exists before writing back (the user may
         have deleted it during the ~1 s live fetch).
      2. Respects the visibility the row was actually stored under.
      3. Surfaces errors through ``last_error`` on the payload so the UI
         can show ``sync error`` instead of staring at an empty pill.
      4. Owns the coroutine under the running loop (``asyncio.create_task``)
         so cancellation is clean on app shutdown.
    """
    try:
        # Re-read the just-inserted row to get the authoritative visibility
        # + payload (in case validators rewrote fields).
        existing = await asyncio.to_thread(
            user_store.get_domain_knowledge_item,
            viewer, domain_id, kind, key, visibility,
        )
        if not existing:
            return  # user deleted it before we got here
        new_payload = await asyncio.to_thread(
            knowledge_module.refresh_payload,
            viewer, kind, existing["payload"],
        )
        if not new_payload:
            return

        # Re-check existence AGAIN just before writing so we don't
        # resurrect a deleted row.
        still_there = await asyncio.to_thread(
            user_store.get_domain_knowledge_item,
            viewer, domain_id, kind, key, visibility,
        )
        if not still_there:
            return

        try:
            await asyncio.to_thread(
                user_store.upsert_domain_knowledge,
                viewer, domain_id, kind, key, new_payload, visibility,
            )
        except PermissionError:
            return
        except Exception as exc:  # noqa: BLE001 -- best effort
            logger.debug("[knowledge_router] inline refresh write failed: %s", exc)
            return

        # Fan out on WebSocket so open panels update immediately.
        try:
            from ..event_bus import event_bus
            scope = user_store.resolve_domain_scope(viewer, domain_id)
            if not scope:
                return
            if visibility == "private":
                viewers = [viewer]
            else:
                viewers = user_store.domain_viewers(
                    scope["owner"], scope["public_domain_id"],
                )
            event_bus.publish_to_users_sync(viewers, {
                "type": "domain.knowledge.updated",
                "domain_id": scope["public_domain_id"],
                "kind": kind,
                "key": key,
                "visibility": visibility,
                "payload": new_payload,
                "source": "inline",
            })
        except Exception as exc:  # noqa: BLE001
            logger.debug("[knowledge_router] inline refresh broadcast failed: %s", exc)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001 -- top-level fire-and-forget guard
        logger.debug("[knowledge_router] inline refresh task errored: %s", exc)
