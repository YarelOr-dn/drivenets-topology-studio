"""Live Link Telemetry routes.

Read-only device facts for the topology Link Table. Device access flows through
``DeviceCommHelper`` so SSH credentials and pool keys stay per-user.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request

from routes._state import _get_request_user
from telemetry import cache as telemetry_cache
from telemetry.dispatcher import provider_for
from telemetry.lldp_correlator import correlate_canvas_edges, correlate_link_full
from telemetry.provider_base import CanvasDevice, DeviceTelemetry, LinkTelemetryPayload

try:
    from api.auth.user_store import user_store
except Exception:  # pragma: no cover
    user_store = None


router = APIRouter()


def _request_user(request: Request) -> str:
    user = _get_request_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def _require_engineer(request: Request) -> str:
    user = _request_user(request)
    if user_store and user != "default" and not user_store.has_role_or_higher(user, "engineer"):
        raise HTTPException(status_code=403, detail="Engineer role required")
    return user


def _device_from_payload(payload: Any, fallback_id: str = "") -> CanvasDevice:
    if isinstance(payload, dict):
        raw = dict(payload)
        did = str(raw.get("device_id") or raw.get("id") or raw.get("label") or fallback_id or "").strip()
        return CanvasDevice(
            device_id=did,
            label=str(raw.get("label") or raw.get("name") or raw.get("hostname") or did),
            ssh_host=str(raw.get("ssh_host") or raw.get("sshHost") or (raw.get("sshConfig") or {}).get("host") or ""),
            raw=raw,
        )
    did = str(payload or fallback_id or "").strip()
    return CanvasDevice(device_id=did, label=did)


def _fetch_device(device: CanvasDevice, app_user: str, *, force: bool = False) -> DeviceTelemetry:
    provider = provider_for(device, app_user=app_user)
    return provider.fetch_device(device, force=force)


def _fetch_link_sides(
    dev_a: CanvasDevice,
    dev_b: CanvasDevice,
    app_user: str,
    *,
    force: bool = False,
) -> tuple[DeviceTelemetry, DeviceTelemetry, List[str]]:
    warnings: List[str] = []

    def fetch_one(label: str, dev: CanvasDevice) -> DeviceTelemetry:
        try:
            return _fetch_device(dev, app_user, force=force)
        except Exception as exc:
            warnings.append(f"{dev.device_id or dev.label}: {exc}")
            return DeviceTelemetry(provider="ssh-cli", warnings=[str(exc)])

    with ThreadPoolExecutor(max_workers=2) as pool:
        fut_a = pool.submit(fetch_one, "A", dev_a)
        fut_b = pool.submit(fetch_one, "B", dev_b)
        return fut_a.result(), fut_b.result(), warnings


@router.post("/api/link-telemetry/refresh")
def refresh_link_telemetry(body: dict = None, request: Request = None):
    """Fetch live interface facts for one or more canvas links."""
    app_user = _request_user(request)
    body = body or {}
    links = body.get("links") or []
    if not isinstance(links, list) or not links:
        raise HTTPException(status_code=400, detail="links[] required")
    force = bool(body.get("force"))
    results: List[Dict[str, Any]] = []
    for item in links:
        if not isinstance(item, dict):
            continue
        link_id = str(item.get("linkId") or item.get("link_id") or "").strip()
        dev_a = _device_from_payload(item.get("deviceA") or item.get("device_a") or item.get("device1"), item.get("deviceAId") or item.get("device1Id") or "")
        dev_b = _device_from_payload(item.get("deviceB") or item.get("device_b") or item.get("device2"), item.get("deviceBId") or item.get("device2Id") or "")
        side_a, side_b, warnings = _fetch_link_sides(
            dev_a,
            dev_b,
            app_user,
            force=force or bool(item.get("force")),
        )
        correlation = correlate_link_full(
            item,
            side_a,
            side_b,
            device_a=dev_a.device_id or dev_a.label,
            device_b=dev_b.device_id or dev_b.label,
        )
        payload = LinkTelemetryPayload(
            link_id=link_id,
            side_a=side_a,
            side_b=side_b,
            lldp=correlation,
            warnings=warnings + side_a.warnings + side_b.warnings,
        )
        row = payload.dict()
        row["correlation"] = correlation
        results.append(row)
    return {"results": results}


@router.get("/api/link-telemetry/healthz")
def link_telemetry_healthz(request: Request):
    _request_user(request)
    return {"ok": True, "provider": "ssh-cli"}


@router.post("/api/link-telemetry/correlate")
def correlate_canvas(body: dict = None, request: Request = None):
    """Build an LLDP interface map for the visible canvas devices."""
    app_user = _request_user(request)
    body = body or {}
    devices = body.get("devices") or []
    if not isinstance(devices, list) or not devices:
        raise HTTPException(status_code=400, detail="devices[] required")
    force = bool(body.get("force"))
    telemetry: Dict[str, DeviceTelemetry] = {}
    normalized_devices: List[Dict[str, Any]] = []
    warnings: List[str] = []
    for entry in devices:
        dev = _device_from_payload(entry)
        did = dev.device_id or dev.label
        if not did:
            continue
        normalized_devices.append({"device_id": did, "label": dev.label, **(dev.raw or {})})
        try:
            telemetry[did] = _fetch_device(dev, app_user, force=force)
        except Exception as exc:
            warnings.append(f"{did}: {exc}")
    return {"edges": correlate_canvas_edges(normalized_devices, telemetry), "warnings": warnings}


@router.get("/api/link-telemetry/{device_id}/interfaces")
def get_device_interfaces(device_id: str, request: Request, ssh_host: str = "", force: int = 0):
    """Fetch physical, bundle, and sub-interface tables for a single device."""
    app_user = _request_user(request)
    dev = CanvasDevice(device_id=device_id, label=device_id, ssh_host=ssh_host or "")
    telemetry = _fetch_device(dev, app_user, force=bool(force))
    return telemetry.dict()


@router.post("/api/link-telemetry/cache/invalidate")
def invalidate_link_telemetry_cache(body: dict = None, request: Request = None):
    """Drop this user's cached telemetry rows."""
    app_user = _require_engineer(request)
    body = body or {}
    device_ids = body.get("device_ids") or body.get("deviceIds")
    if device_ids is not None and not isinstance(device_ids, list):
        raise HTTPException(status_code=400, detail="device_ids must be a list")
    evicted = telemetry_cache.invalidate(app_user, device_ids=device_ids)
    return {"ok": True, "evicted": evicted}
