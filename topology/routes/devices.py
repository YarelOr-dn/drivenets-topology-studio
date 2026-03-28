"""Scaler bridge routes: devices."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from fastapi import APIRouter, Body, HTTPException

from routes.bridge_helpers import (
    INVENTORY_FILE, SCALER_ROOT, _compute_wizard_suggestions,
    _fetch_all_operational_via_ssh, _fetch_git_commit_via_ssh,
    _get_credentials, _get_device_context,
    _resolve_device, _resolve_mgmt_ip, _ssh_pool, _strip_ansi,
)
from routes._state import _push_jobs, _push_jobs_lock

router = APIRouter()

@router.post("/api/wizard/suggestions")
def wizard_suggestions(body: dict = None):
    """Backend-driven next-wizard suggestions with pre-fill data.
    
    Request: { device_id, completed_wizard, created_data: { interfaces, loopback_ip, vrfs, ... } }
    Response: { suggestions: [{ wizard, reason, prefill }, ...] }
    """
    body = body or {}
    device_id = body.get("device_id") or ""
    completed_wizard = body.get("completed_wizard") or ""
    created_data = body.get("created_data") or {}
    ssh_host = body.get("ssh_host") or ""

    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")

    try:
        ctx = _get_device_context(device_id, live=False, ssh_host=ssh_host)
        suggestions = _compute_wizard_suggestions(device_id, completed_wizard, created_data, ctx)
        return {"suggestions": suggestions}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/api/devices/{device_id}/resolve")
def resolve_device(device_id: str, ssh_host: str = ""):
    """Lightweight device resolution for terminal/SSH. Uses _resolve_mgmt_ip when discovery_api is down.
    Returns {id, hostname, ip, serial, source} compatible with GET /api/devices/{id}."""
    try:
        mgmt_ip, scaler_id, via = _resolve_mgmt_ip(device_id, ssh_host)
        hostname = device_id
        serial = ""
        try:
            resolved = _resolve_device(device_id)
            hostname = resolved.get("hostname") or resolved.get("name") or device_id
            serial = resolved.get("serial", "")
        except Exception:
            pass
        return {
            "id": device_id,
            "hostname": hostname,
            "ip": mgmt_ip,
            "mgmt_ip": mgmt_ip,
            "serial": serial,
            "source": via,
            "username": "dnroot",
            "password": "dnroot"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/api/devices/{device_id}/context")
def get_device_context(device_id: str, live: bool = False, ssh_host: str = ""):
    """Unified device context for wizard suggestions.
    
    Query params:
        live: Force live SSH fetch instead of cached
        ssh_host: SSH IP/hostname from canvas device (primary resolution key)
    """
    try:
        return _get_device_context(device_id, live=live, ssh_host=ssh_host)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/api/devices/{device_id}/git-commit")
def get_device_git_commit(device_id: str, ssh_host: str = "", ssh_user: str = "", ssh_password: str = ""):
    """Lightweight endpoint: SSH only for git_commit. Use when context fetch returns null git_commit.
    Returns {git_commit: null} instead of 503 on SSH failure -- this is a best-effort call.
    Checks operational.json cache first to avoid slow virsh roundtrip."""
    import time as _time
    from pathlib import Path
    try:
        ops_path = Path(SCALER_ROOT) / "db" / "configs" / device_id / "operational.json"
        if ops_path.exists():
            import json
            ops = json.loads(ops_path.read_text())
            cached_gc = ops.get("git_commit")
            if cached_gc:
                return {"git_commit": cached_gc}
    except Exception:
        pass
    try:
        mgmt_ip, _, _ = _resolve_mgmt_ip(device_id, ssh_host)
    except Exception:
        return {"git_commit": None}
    try:
        default_user, default_password = _get_credentials()
        user = ssh_user or default_user
        password = ssh_password or default_password
        git_hash = _fetch_git_commit_via_ssh(mgmt_ip, user, password,
                                               scaler_device_id=device_id)
        return {"git_commit": git_hash}
    except Exception:
        return {"git_commit": None}


@router.post("/api/devices/{device_id}/stack-live")
def get_device_stack_live(device_id: str, body: dict = Body(default={})):
    """Fetch live stack via SSH (with virsh fallback for cluster devices).
    Body: { ssh_host?: str, ssh_user?: str, ssh_password?: str }"""
    ssh_host = (body.get("ssh_host") or "").strip()
    try:
        mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(device_id, ssh_host)
    except Exception:
        return {"components": [], "error": "Cannot resolve device"}
    try:
        default_user, default_password = _get_credentials()
        user = (body.get("ssh_user") or "").strip() or default_user
        password = (body.get("ssh_password") or "").strip() or default_password
        ops = _fetch_all_operational_via_ssh(mgmt_ip, user, password,
                                             scaler_device_id=scaler_id or device_id)
        stack = ops.get("stack") or []
        raw = ""
        if not stack:
            raw = "No stack data returned from device"
        return {"components": stack, "raw_output": raw}
    except Exception as e:
        return {"components": [], "error": str(e)}


@router.post("/api/devices/{device_id}/set-hostname")
def set_device_hostname(device_id: str, body: dict = None):
    """Fast direct-SSH hostname change. Bypasses the scaler job pipeline entirely.
    Body: { hostname: str, ssh_host?: str }
    Uses DNOSSession.send_config_set for prompt-based config + commit."""
    if not body or not body.get("hostname"):
        raise HTTPException(status_code=400, detail="Missing 'hostname' in request body")

    new_hostname = body["hostname"].strip()
    ssh_host = body.get("ssh_host", "")
    mgmt_ip, scaler_id, via = _resolve_mgmt_ip(device_id, ssh_host)
    user, password = _get_credentials()

    client = _ssh_pool.get_client(mgmt_ip, user, password)
    if not client:
        raise HTTPException(status_code=503, detail="SSH connection failed")
    owns = not _ssh_pool.enabled
    try:
        from scaler.dnos_session import DNOSSession

        with DNOSSession(
            mgmt_ip, user, password, client=client, owns_client=owns,
        ) as sess:
            commit_out = sess.send_config_set(
                [f"system name {new_hostname}"],
                commit=True,
            )
        success = "failed" not in commit_out.lower() and "error" not in commit_out.lower()
        return {
            "status": "ok" if success else "error",
            "hostname": new_hostname,
            "device_ip": mgmt_ip,
            "commit_output": commit_out.strip()[-300:] if commit_out else "",
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"SSH hostname change failed: {e}")
    finally:
        if _ssh_pool.enabled:
            _ssh_pool.release(mgmt_ip)
        elif owns:
            try:
                client.close()
            except Exception:
                pass


@router.post("/api/devices/{device_id}/test")
def test_device_connection(device_id: str, ssh_host: str = ""):
    """Test SSH connectivity to a device. Uses DNOSSession + central _resolve_mgmt_ip."""
    mgmt_ip, scaler_id, via = _resolve_mgmt_ip(device_id, ssh_host)
    try:
        user, password = _get_credentials()
        from scaler.dnos_session import DNOSSession

        with DNOSSession(mgmt_ip, user, password, connect_timeout=8) as sess:
            if sess.is_alive():
                return {"status": "ok", "message": f"Connection OK ({mgmt_ip}, via {via})"}
        raise HTTPException(status_code=503, detail=f"SSH to {mgmt_ip} failed: session not alive")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"SSH to {mgmt_ip} failed: {e}")


@router.post("/api/devices/discover")
def discover_device(body: dict = None):
    """SSH to device by IP, discover hostname, add to device_inventory.json."""
    body = body or {}
    ip = (body.get("ip") or "").strip()
    if not ip:
        raise HTTPException(status_code=400, detail="ip required")
    user, password = _get_credentials()
    try:
        from scaler.models import Device
        from scaler.config_extractor import InteractiveExtractor
        device = Device(
            id=ip,
            hostname=ip,
            ip=ip,
            username=user,
            password=Device.encode_password(password),
        )
        config_dir = Path(SCALER_ROOT) / "db" / "configs" / ip
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "operational.json").write_text(json.dumps({"mgmt_ip": ip}, indent=2))
        with InteractiveExtractor(device, timeout=60) as ext:
            raw = ext.get_running_config(fetch_lldp=False)
        if not isinstance(raw, str):
            raw = str(raw)
        hostname = ip
        for line in raw.splitlines():
            if "hostname" in line.lower() and not line.strip().startswith("#"):
                m = re.search(r"hostname\s+(\S+)", line, re.I)
                if m:
                    hostname = m.group(1).strip()
                    break
        inv = {}
        if INVENTORY_FILE.exists():
            inv = json.loads(INVENTORY_FILE.read_text())
        inv.setdefault("devices", {})
        key = hostname or ip
        from datetime import datetime
        inv["devices"][key] = {
            "hostname": hostname,
            "mgmt_ip": ip,
            "serial": key,
            "last_seen": datetime.now().isoformat(),
        }
        INVENTORY_FILE.write_text(json.dumps(inv, indent=2))
        return {"status": "ok", "hostname": hostname, "ip": ip, "key": key}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

