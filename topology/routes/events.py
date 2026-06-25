"""Per-user device-state watcher + events API + WebSocket bus.

All routes here are mounted under the scaler bridge. The contract is:

- A *watcher* is a ``(device_id, username)`` pair. The frontend registers
  one whenever a user loads a topology that contains that device on the
  canvas; it deregisters on tab close / topology unload. Heartbeats keep
  the watcher row alive -- rows older than ``WATCHER_IDLE_TTL_SECONDS``
  are pruned automatically on the next heartbeat or read.

- An *event* is any maintenance action that mutates the shared device
  record (ghost-IP reap, mgmt-ip update, cluster-state change, manual
  note). The backend records every event in the shared audit log and
  pushes a WebSocket frame to every active watcher + the actor.

- Endpoints are deliberately cheap so the frontend can call them
  frequently without overloading the bridge.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect

from api.device_state import device_state
from api.event_bus import event_bus
from routes._state import _get_request_role, _get_request_user


router = APIRouter()
logger = logging.getLogger(__name__)


# ----------------------------------------------------------------- watcher API


@router.post("/api/devices/{device_id}/watch")
async def register_watcher(device_id: str, body: Optional[Dict[str, Any]] = None, request: Request = None):
    """Register the current user as a watcher of this device.

    Body may carry ``{topology_id, canvas_ip}`` so the backend can log
    which topology opened the watch and which IP the user's canvas
    thinks the device is at (handy for drift diagnosis).
    """
    body = body or {}
    device_id = (device_id or "").strip()
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    username = _get_request_user(request) if request else "default"
    try:
        result = device_state.register_watcher(
            device_id=device_id,
            username=username,
            topology_id=(body.get("topology_id") or "").strip() or None,
            canvas_ip=(body.get("canvas_ip") or "").strip() or None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if result.get("newly_registered"):
        # Fire a light event so other users watching this device get a
        # presence hint ("N users are watching this device"). The payload
        # intentionally omits sensitive info; listeners can call the
        # watchers endpoint for the full list if they need it.
        try:
            await event_bus.publish_to_device_watchers(
                device_id=device_id,
                event_type="watcher_added",
                payload={"username": username},
                extra_users=[username],
            )
        except Exception as exc:
            logger.debug("[watcher_added broadcast] %s", exc)
    return {"ok": True, **result}


@router.post("/api/devices/{device_id}/unwatch")
async def unregister_watcher(device_id: str, request: Request = None):
    device_id = (device_id or "").strip()
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    username = _get_request_user(request) if request else "default"
    removed = device_state.unregister_watcher(device_id, username)
    if removed:
        try:
            await event_bus.publish_to_device_watchers(
                device_id=device_id,
                event_type="watcher_removed",
                payload={"username": username},
            )
        except Exception as exc:
            logger.debug("[watcher_removed broadcast] %s", exc)
    return {"ok": True, "removed": removed, "device_id": device_id, "username": username}


@router.post("/api/devices/watch-heartbeat")
async def heartbeat(body: Optional[Dict[str, Any]] = None, request: Request = None):
    """Bulk-refresh the watcher list for the caller's canvas.

    Body: ``{device_ids: [str, ...]}``. Returns which rows were added,
    kept, or pruned. Clients call this every 30s so stale tabs drop off
    quickly when a laptop goes to sleep.
    """
    body = body or {}
    username = _get_request_user(request) if request else "default"
    device_ids = body.get("device_ids") or []
    if not isinstance(device_ids, list):
        raise HTTPException(status_code=400, detail="device_ids must be a list")
    try:
        result = device_state.heartbeat(username, device_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"ok": True, **result}


@router.get("/api/devices/{device_id}/watchers")
async def list_watchers(device_id: str, active_only: bool = True, request: Request = None):
    """Return everyone currently watching this device.

    Visibility rule: ANY authenticated user may see who else is watching
    a device they can see. This matches the topology-sharing model --
    watcher presence is social info, not secret.
    """
    device_id = (device_id or "").strip()
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    rows = device_state.list_watchers_for_device(device_id, active_only=active_only)
    return {"device_id": device_id, "watchers": rows, "count": len(rows)}


@router.get("/api/devices/watched")
async def my_watched_devices(active_only: bool = True, request: Request = None):
    """List devices the current user is watching."""
    username = _get_request_user(request) if request else "default"
    rows = device_state.list_watched_devices(username, active_only=active_only)
    return {"username": username, "devices": rows, "count": len(rows)}


# ---------------------------------------------------------------- events API


@router.get("/api/devices/{device_id}/events")
async def list_device_events(
    device_id: str,
    since_id: Optional[int] = None,
    since_iso: Optional[str] = None,
    limit: int = 50,
    request: Request = None,
):
    """Polling fallback for the WebSocket events channel.

    Use when the WS is unavailable (proxy strips upgrades, browser tab
    suspended, etc.) or to backfill history on reconnect. ``since_id``
    is the preferred cursor -- monotonic, DB-assigned.
    """
    device_id = (device_id or "").strip()
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    rows = device_state.list_events(
        device_id=device_id, since_id=since_id, since_iso=since_iso, limit=limit,
    )
    return {"device_id": device_id, "events": rows, "count": len(rows)}


@router.get("/api/devices/events/recent")
async def list_recent_events(limit: int = 100, request: Request = None):
    """Cross-device recent activity feed, scoped to devices the caller watches."""
    username = _get_request_user(request) if request else "default"
    watched = device_state.list_watched_devices(username, active_only=True)
    watched_ids = {w["device_id"] for w in watched}
    if not watched_ids:
        return {"username": username, "events": [], "count": 0}
    all_events: List[Dict[str, Any]] = []
    for dev_id in watched_ids:
        all_events.extend(device_state.list_events(device_id=dev_id, limit=limit))
    all_events.sort(key=lambda e: e["id"], reverse=True)
    all_events = all_events[:limit]
    return {"username": username, "events": all_events, "count": len(all_events)}


# ----------------------------------------------------------- per-user prefs


@router.get("/api/devices/{device_id}/user-prefs")
async def get_user_pref(device_id: str, request: Request = None):
    username = _get_request_user(request) if request else "default"
    return {
        "username": username,
        "device_id": device_id,
        "prefs": device_state.get_user_pref(username, device_id),
    }


@router.put("/api/devices/{device_id}/user-prefs")
async def set_user_pref(device_id: str, body: Optional[Dict[str, Any]] = None, request: Request = None):
    body = body or {}
    username = _get_request_user(request) if request else "default"
    patch = body.get("prefs") if isinstance(body.get("prefs"), dict) else body
    # Shallow-merge so partial updates don't clobber unrelated keys.
    return device_state.merge_user_pref(username, device_id, patch or {})


# -------------------------------------------------------------- WebSocket bus


@router.websocket("/api/events/ws")
async def events_websocket(websocket: WebSocket, token: str = ""):
    """Per-user event WebSocket.

    The browser connects on app init and stays subscribed for the life
    of the tab. Incoming frames (from client to server) are advisory
    (``ping``, ``hello``). Server-to-client frames are the broadcast
    ``{type: "event", event: {...}}`` envelopes.
    """
    username = ""
    if token:
        try:
            from api.auth.service import decode_token
            payload = decode_token(token)
            if payload:
                username = (payload.get("sub") or "").strip()
        except Exception as exc:
            logger.warning("[events_ws] token decode failed: %s", exc)
    if not username:
        # When multiuser auth is disabled (dev mode), fall back to
        # "default" so local smoke tests still work.
        try:
            from api.config import settings as _settings
            if not _settings.multiuser_enabled:
                username = "default"
        except Exception:
            pass
    if not username:
        await websocket.close(code=4001, reason="Authentication required")
        return

    await websocket.accept()
    await event_bus.subscribe(username, websocket)
    hello = {
        "type": "hello",
        "username": username,
        "watched": [w["device_id"] for w in device_state.list_watched_devices(username)],
    }
    # Wave 3.2: every outbound frame goes through the per-WS writer task
    # to prevent concurrent send_json() races with the broadcast writer.
    event_bus.enqueue_raw_to_ws(username, websocket, hello)

    # Wave 3.3: server-side keepalive. We send a __ping__ every
    # PING_INTERVAL seconds when the receive loop is idle. If two
    # consecutive pings pass with no inbound frame at all, the peer is
    # considered dead and the socket is closed. The client library
    # already emits a `heartbeat` every ~30s so a healthy tab will
    # always reset the miss counter well within the 40s budget.
    PING_INTERVAL = 20.0
    MAX_MISSED = 2
    missed = 0
    try:
        while True:
            try:
                msg = await asyncio.wait_for(
                    websocket.receive_json(), timeout=PING_INTERVAL
                )
                missed = 0
            except asyncio.TimeoutError:
                missed += 1
                if missed >= MAX_MISSED:
                    logger.info(
                        "[events_ws] closing idle user=%s after %d missed pings",
                        username, missed,
                    )
                    break
                # Probe the client so a healthy tab pushes a pong back.
                if not event_bus.enqueue_raw_to_ws(
                    username, websocket, {"type": "__ping__"}
                ):
                    break
                continue
            except Exception:
                break
            mtype = (msg.get("type") or "").strip()
            if mtype in ("ping", "__ping__"):
                if not event_bus.enqueue_raw_to_ws(
                    username, websocket, {"type": "pong"}
                ):
                    break
            elif mtype == "pong":
                # Client responded to our probe -- nothing else to do.
                pass
            elif mtype == "heartbeat":
                # Optional: client sends its full canvas device list and
                # we refresh the watcher rows in one round-trip instead
                # of requiring a separate HTTP call.
                dev_ids = msg.get("device_ids") or []
                if isinstance(dev_ids, list):
                    try:
                        device_state.heartbeat(username, dev_ids)
                    except Exception as exc:
                        logger.debug("[events_ws heartbeat] %s", exc)
    except WebSocketDisconnect:
        pass
    finally:
        await event_bus.unsubscribe(username, websocket)


# ---------------------------------------------------------- admin / diagnostics


@router.get("/api/events/status")
async def events_status(request: Request = None):
    """Diagnostic snapshot of the event bus + watcher tables.

    Admin sees everything. Non-admin sees only their own connection count
    and their own watched devices.
    """
    username = _get_request_user(request) if request else "default"
    role = _get_request_role(request) if request else "viewer"
    stats: Dict[str, Any] = {
        "username": username,
        "my_connections": event_bus.subscriber_count(username),
        "my_watched": device_state.list_watched_devices(username),
    }
    if role == "admin":
        stats["total_connections"] = event_bus.subscriber_count()
        stats["connected_users"] = event_bus.connected_users()
        stats["recent_events"] = device_state.list_events(limit=20)
    return stats
