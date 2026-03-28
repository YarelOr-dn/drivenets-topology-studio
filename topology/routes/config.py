"""Scaler bridge routes: config."""
from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException

from routes._device_comm import DeviceCommHelper
from routes.bridge_helpers import (
    SCALER_ROOT, _build_config_summary, _build_scaler_ops_index,
    _get_cached_config,
    _get_device_context, _load_push_history, _resolve_device, _resolve_mgmt_ip,
)
from routes._state import _push_jobs, _push_jobs_lock

router = APIRouter()

@router.get("/api/config/{device_id}/running")
def get_running_config(device_id: str, live: bool = False, ssh_host: str = ""):
    """Get running config - cached or live fetch."""
    mgmt_ip, scaler_id, via = _resolve_mgmt_ip(device_id, ssh_host)
    config = _get_cached_config(scaler_id)
    if live or not config:
        try:
            config = DeviceCommHelper().fetch_running_config(
                device_id, ssh_host, mgmt_ip=mgmt_ip, scaler_id=scaler_id,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    if not config:
        raise HTTPException(status_code=404, detail="No config available")
    return {"config": config}


@router.get("/api/config/{device_id}/summary")
def get_config_summary(device_id: str, ssh_host: str = ""):
    """Get parsed config summary."""
    mgmt_ip, scaler_id, via = _resolve_mgmt_ip(device_id, ssh_host)
    config = _get_cached_config(scaler_id)
    if not config:
        try:
            config = DeviceCommHelper().fetch_running_config(
                device_id, ssh_host, mgmt_ip=mgmt_ip, scaler_id=scaler_id,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    if not config:
        raise HTTPException(status_code=404, detail="No config available")
    return _build_config_summary(config)


@router.post("/api/config/{device_id}/sync")
def sync_config(device_id: str, ssh_host: str = ""):
    """Fetch running config from device and cache it."""
    try:
        mgmt_ip, scaler_id, via = _resolve_mgmt_ip(device_id, ssh_host)
        config = DeviceCommHelper().fetch_running_config(
            device_id, ssh_host, mgmt_ip=mgmt_ip, scaler_id=scaler_id,
        )
        if not config:
            raise HTTPException(status_code=503, detail="No config received")
        config_dir = Path(SCALER_ROOT) / "db" / "configs" / scaler_id
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "running.txt").write_text(config)
        return {"status": "ok", "message": f"Synced {len(config.splitlines())} lines (via {via})", "lines": len(config.splitlines())}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/api/config/generate/interfaces")
def generate_interfaces(body: dict = None):
    """Generate interface config from GUI params. Uses scaler-wizard config_builders."""
    body = body or {}
    try:
        from scaler.wizard.config_builders import build_interface_config
        config = build_interface_config(body)
        return {"config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/config/generate/undo")
def generate_undo(body: dict = None):
    """Generate DNOS delete commands to undo a pushed config.
    Accepts config_text or job_id (to get config from push history).
    Returns {config: str} with delete commands. Caller wraps with configure/commit."""
    body = body or {}
    config_text = body.get("config_text") or body.get("config") or ""
    job_id = body.get("job_id") or ""
    if not config_text and job_id:
        with _push_jobs_lock:
            job = _push_jobs.get(job_id, {})
        if not job:
            history = _load_push_history()
            for h in (history or []):
                if h.get("job_id") == job_id:
                    config_text = h.get("config_text", "")
                    break
        else:
            config_text = job.get("config_text", "")
    if not config_text or not config_text.strip():
        raise HTTPException(status_code=400, detail="config_text or job_id with config required")
    try:
        from scaler.wizard.config_builders import build_undo_config
        undo = build_undo_config(config_text)
        return {"config": undo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/config/{device_id}/save")
def save_config_for_later(device_id: str, body: dict = None):
    """Save generated config to device's saved configs (for later push)."""
    body = body or {}
    config = body.get("config") or body.get("config_text") or ""
    if not config or not config.strip():
        raise HTTPException(status_code=400, detail="config required")
    try:
        from datetime import datetime
        from scaler.utils import get_device_config_dir, timestamp_filename
        config_dir = get_device_config_dir(device_id)
        filename = f"wizard_{timestamp_filename(prefix='', suffix='.txt')}"
        filepath = config_dir / filename
        filepath.write_text(config.strip(), encoding="utf-8")
        return {"status": "ok", "path": str(filepath), "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/config/{device_id}/saved-files")
def list_saved_files(device_id: str):
    """List saved config files for a device."""
    try:
        from scaler.utils import get_device_config_dir
        config_dir = get_device_config_dir(device_id)
        files = []
        for f in sorted(config_dir.glob("*.txt"), key=lambda p: p.stat().st_mtime, reverse=True):
            stat = f.stat()
            from datetime import datetime
            ts = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            line_count = sum(1 for _ in open(f, encoding="utf-8", errors="ignore"))
            files.append({
                "filename": f.name,
                "path": str(f),
                "timestamp": ts,
                "lines": line_count,
                "size": stat.st_size,
                "pushed": "_pushed" in f.name,
            })
        return {"files": files, "device_id": device_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/config/file")
def read_config_file(path: str = ""):
    """Read a saved config file by path."""
    if not path:
        raise HTTPException(status_code=400, detail="path parameter required")
    from starlette.responses import PlainTextResponse
    fp = Path(path)
    if not fp.exists():
        raise HTTPException(status_code=404, detail="File not found")
    from scaler.utils import CONFIGS_DIR
    try:
        resolved = fp.resolve()
        configs_resolved = CONFIGS_DIR.resolve()
        if not str(resolved).startswith(str(configs_resolved)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=403, detail="Access denied")
    return PlainTextResponse(fp.read_text(encoding="utf-8", errors="ignore"))


@router.delete("/api/config/file")
def delete_config_file(path: str = ""):
    """Delete a saved config file by path."""
    if not path:
        raise HTTPException(status_code=400, detail="path parameter required")
    fp = Path(path)
    if not fp.exists():
        raise HTTPException(status_code=404, detail="File not found")
    from scaler.utils import CONFIGS_DIR
    try:
        resolved = fp.resolve()
        configs_resolved = CONFIGS_DIR.resolve()
        if not str(resolved).startswith(str(configs_resolved)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=403, detail="Access denied")
    fp.unlink()
    return {"status": "ok", "deleted": str(fp)}


@router.post("/api/config/{device_id}/push")
def push_saved_config(device_id: str, body: dict = None):
    """Push a saved config to device -- delegates to the main push endpoint."""
    body = body or {}
    config = body.get("config", "")
    if not config:
        raise HTTPException(status_code=400, detail="config required")
    push_body = {
        "device_id": device_id,
        "config": config,
        "hierarchy": body.get("hierarchy", ""),
        "mode": body.get("mode", "merge"),
        "dry_run": body.get("dry_run", True),
    }
    return push_config(push_body)


@router.post("/api/config/scan-existing")
def scan_existing(body: dict = None):
    """Scan device config for existing sub-IDs, VRFs, EVIs, L3 conflicts. Uses scale_operations."""
    body = body or {}
    device_id = body.get("device_id") or ""
    ssh_host = body.get("ssh_host") or ""
    scan_type = body.get("scan_type") or "interfaces"
    parent_interface = body.get("parent_interface") or ""
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    try:
        mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(device_id, ssh_host)
        config = _get_cached_config(scaler_id)
        if not config:
            config = DeviceCommHelper().fetch_running_config(
                device_id, ssh_host, mgmt_ip=mgmt_ip, scaler_id=scaler_id,
            )
        if not config:
            raise HTTPException(status_code=404, detail="No config available")
        from scaler.wizard.scale_operations import (
            _scan_used_sub_ids,
            _scan_l3_sub_ids,
            _scan_l2_sub_ids,
            _scan_sub_id_details,
            _scan_outer_inner_map,
            _scan_used_vrf_numbers,
            _scan_used_route_targets,
            _find_free_numbers,
        )
        from datetime import datetime
        result = {
            "existing_sub_ids": [],
            "existing_vrfs": [],
            "existing_evis": [],
            "l3_conflicts": [],
            "l2_sub_ids": [],
            "sub_id_details": {},
            "outer_inner_map": {},
            "next_free": {},
            "config_fetched_at": None,
        }
        config_path = Path(SCALER_ROOT) / "db" / "configs" / scaler_id / "running.txt"
        if config_path.exists():
            try:
                result["config_fetched_at"] = datetime.fromtimestamp(config_path.stat().st_mtime).isoformat() + "Z"
            except Exception:
                result["config_fetched_at"] = datetime.utcnow().isoformat() + "Z"
        else:
            result["config_fetched_at"] = datetime.utcnow().isoformat() + "Z"
        if scan_type in ("interfaces", "all") and parent_interface:
            used_sub = _scan_used_sub_ids(config, parent_interface)
            l3_conflicts = _scan_l3_sub_ids(config, parent_interface)
            l2_sub_ids = _scan_l2_sub_ids(config, parent_interface)
            details = _scan_sub_id_details(config, parent_interface)
            outer_inner = _scan_outer_inner_map(config, parent_interface)
            result["existing_sub_ids"] = sorted(used_sub)
            result["l3_conflicts"] = sorted(l3_conflicts)
            result["l2_sub_ids"] = sorted(l2_sub_ids)
            result["sub_id_details"] = {str(k): v for k, v in details.items()}
            result["outer_inner_map"] = {str(k): v for k, v in outer_inner.items()}
            result["next_free"]["sub_id"] = next((n for n in range(1, 65536) if n not in used_sub), 1)
        if scan_type in ("services", "vrfs", "all"):
            vrf_used = _scan_used_vrf_numbers(config, "VRF-")
            result["existing_vrfs"] = [f"VRF-{n}" for n in sorted(vrf_used)]
            result["next_free"]["vrf_num"] = next((n for n in range(1, 65536) if n not in vrf_used), 1)
            rt_base = body.get("rt_base") or "65000"
            rt_used = _scan_used_route_targets(config, rt_base)
            result["existing_rts"] = [f"{rt_base}:{n}" for n in sorted(rt_used)]
            result["next_free"]["rt"] = next((n for n in range(1, 65536) if n not in rt_used), 1)
        return result
    except HTTPException:
        raise
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"scale_operations unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/api/config/scan-ips")
def scan_ips(body: dict = None):
    """Scan device config for used IPv4/IPv6 addresses. Returns used IPs and suggested non-overlapping ranges."""
    body = body or {}
    device_id = body.get("device_id") or ""
    ssh_host = body.get("ssh_host") or ""
    parent_interface = body.get("parent_interface") or ""
    ipv4_prefix = int(body.get("ipv4_prefix", 31))
    ipv6_prefix = int(body.get("ipv6_prefix", 127))
    count = int(body.get("count", 1))
    preferred_ipv4 = body.get("preferred_ipv4_base") or ""
    preferred_ipv6 = body.get("preferred_ipv6_base") or ""
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    try:
        mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(device_id, ssh_host)
        config = _get_cached_config(scaler_id)
        if not config:
            config = DeviceCommHelper().fetch_running_config(
                device_id, ssh_host, mgmt_ip=mgmt_ip, scaler_id=scaler_id,
            )
        if not config:
            raise HTTPException(status_code=404, detail="No config available")
        from scaler.wizard.config_builders import (
            scan_used_ips,
            suggest_next_ip_range,
            check_ip_overlap,
        )
        used = scan_used_ips(config)
        if parent_interface:
            used["ipv4"] = [u for u in used.get("ipv4", []) if parent_interface in (u.get("interface") or "")]
            used["ipv6"] = [u for u in used.get("ipv6", []) if parent_interface in (u.get("interface") or "")]
            used["ipv4_subnets"] = list({f"{u['address']}/{u['prefix']}" for u in used["ipv4"]})
            used["ipv6_subnets"] = list({f"{u['address']}/{u['prefix']}" for u in used["ipv6"]})
        suggestion = suggest_next_ip_range(
            used, count=count,
            ipv4_prefix=ipv4_prefix, ipv6_prefix=ipv6_prefix,
            preferred_ipv4_base=preferred_ipv4 or None,
            preferred_ipv6_base=preferred_ipv6 or None,
            ipv4_count=int(body.get("ipv4_count", 1)),
            ipv4_step_dotted=body.get("ipv4_step_dotted") or body.get("ipv4_step") or None,
            ipv6_count=int(body.get("ipv6_count", 1)),
        )
        result = {"used_ips": used, "suggestion": suggestion}
        check_ipv4 = body.get("check_ipv4") or body.get("ipv4_start") or ""
        check_ipv6 = body.get("check_ipv6") or body.get("ipv6_start") or ""
        if check_ipv4 or check_ipv6:
            overlap_result = check_ip_overlap(
                used,
                ipv4_start=check_ipv4 or None,
                ipv4_prefix=ipv4_prefix,
                ipv4_count=int(body.get("ipv4_count", 1)),
                ipv4_step_dotted=body.get("ipv4_step_dotted") or body.get("ipv4_step") or None,
                ipv6_start=check_ipv6 or None,
                ipv6_prefix=ipv6_prefix,
                ipv6_count=int(body.get("ipv6_count", 1)),
            )
            result["overlap_check"] = overlap_result
        return result
    except HTTPException:
        raise
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"config_builders unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/api/config/detect-pattern")
def detect_pattern(body: dict = None):
    """Detect interface pattern (vlan-tags vs vlan-id, stepping) from existing sub-interfaces."""
    body = body or {}
    device_id = body.get("device_id") or ""
    ssh_host = body.get("ssh_host") or ""
    parent_interface = body.get("parent_interface") or ""
    if not device_id or not parent_interface:
        raise HTTPException(status_code=400, detail="device_id and parent_interface required")
    try:
        mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(device_id, ssh_host)
        config = _get_cached_config(scaler_id)
        if not config:
            config = DeviceCommHelper().fetch_running_config(
                device_id, ssh_host, mgmt_ip=mgmt_ip, scaler_id=scaler_id,
            )
        if not config:
            raise HTTPException(status_code=404, detail="No config available")
        from scaler.wizard.scale_operations import (
            _detect_interface_pattern_from_config,
            _scan_used_sub_ids,
        )
        pattern = _detect_interface_pattern_from_config(config, parent_interface)
        used_sub = _scan_used_sub_ids(config, parent_interface)
        last_sub = max(used_sub) if used_sub else 0
        vlan_mode = "qinq" if pattern.get("uses_vlan_tags") else ("dot1q" if pattern.get("uses_vlan_id") else "dot1q")
        step_mode = pattern.get("step_mode") or "outer"
        last_vlan = last_sub
        detected_step = 1
        return {
            "vlan_mode": vlan_mode,
            "stepping_tag": step_mode,
            "last_vlan": last_vlan,
            "last_sub_id": last_sub,
            "suggested_next_vlan": last_vlan + detected_step,
            "interface_type": "l2ac" if "ge" in parent_interface or "bundle" in parent_interface else "pwhe",
            "pattern": {k: v for k, v in pattern.items() if isinstance(v, (str, int, float, bool, type(None)))},
        }
    except HTTPException:
        raise
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"scale_operations unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/api/config/detect/l2ac-parent")
def detect_l2ac_parent(body: dict = None):
    """Detect L2-AC parent interface from device config.
    Returns parent interface (e.g., ge100-18/0/0) or null if none found."""
    body = body or {}
    device_id = body.get("device_id") or ""
    ssh_host = body.get("ssh_host") or ""
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    try:
        mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(device_id, ssh_host)
        config = _get_cached_config(scaler_id)
        if not config:
            config = DeviceCommHelper().fetch_running_config(
                device_id, ssh_host, mgmt_ip=mgmt_ip, scaler_id=scaler_id,
            )
        if not config:
            raise HTTPException(status_code=404, detail="No config available")
        from scaler.wizard.scale_operations import _detect_l2ac_parent_from_config_str
        parent = _detect_l2ac_parent_from_config_str(config)
        return {"l2ac_parent": parent}
    except HTTPException:
        raise
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"scale_operations unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/api/config/detect/bgp-neighbors")
def detect_bgp_neighbors(body: dict = None):
    """Detect existing BGP neighbors from device config.
    Returns list of dicts with ip, remote_as, description, has_v4_fs_vpn, has_v6_fs_vpn."""
    body = body or {}
    device_id = body.get("device_id") or ""
    ssh_host = body.get("ssh_host") or ""
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    try:
        mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(device_id, ssh_host)
        config = _get_cached_config(scaler_id)
        if not config:
            config = DeviceCommHelper().fetch_running_config(
                device_id, ssh_host, mgmt_ip=mgmt_ip, scaler_id=scaler_id,
            )
        if not config:
            raise HTTPException(status_code=404, detail="No config available")
        from scaler.wizard.scale_operations import _detect_bgp_neighbors
        neighbors = _detect_bgp_neighbors(config)
        return {"neighbors": neighbors}
    except HTTPException:
        raise
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"scale_operations unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/api/config/menu-summary")
def get_menu_summary(device_ids: str = ""):
    """Aggregate device counts from cached configs for Config Menu badges.
    device_ids: comma-separated list of device IDs (from canvas). Limit 20, 8s timeout."""
    import time
    ids = [x.strip() for x in (device_ids or "").split(",") if x.strip()][:20]
    result = {"devices": 0, "interfaces": {"phys": 0, "bundle": 0, "subif": 0}, "services": {"fxc": 0, "l2vpn": 0, "evpn": 0, "vpws": 0, "vrf": 0}, "lldp_total": 0}
    if not ids:
        idx = _build_scaler_ops_index()
        result["devices"] = len(set(e.get("scaler_id", "") for e in (idx or {}).values() if e.get("scaler_id")))
        return result
    deadline = time.time() + 8
    for did in ids:
        if time.time() > deadline:
            break
        try:
            ctx = _get_device_context(did, live=False)
            if not ctx:
                continue
            result["devices"] = result.get("devices", 0) + 1
            ifc = ctx.get("interfaces") or {}
            result["interfaces"]["phys"] += len(ifc.get("physical") or [])
            result["interfaces"]["bundle"] += len(ifc.get("bundle") or [])
            result["interfaces"]["subif"] += len(ifc.get("subinterface") or [])
            svc = ctx.get("services") or {}
            result["services"]["fxc"] += svc.get("fxc_count", 0)
            result["services"]["vrf"] += svc.get("vrf_count", 0)
            cfg = ctx.get("config_summary") or {}
            evpn_svc = cfg.get("evpn_services") or {}
            if isinstance(evpn_svc, dict) and evpn_svc:
                vals = list(evpn_svc.values())
                result["services"]["evpn"] += sum(v for v in vals if isinstance(v, int))
            result["lldp_total"] += len(ctx.get("lldp") or [])
        except Exception:
            continue
    return result


@router.post("/api/config/detect/scale-suggestions")
def detect_scale_suggestions(body: dict = None):
    """Detect scale-up suggestions (peer match, continue pattern, MH sync)."""
    body = body or {}
    device_id = body.get("device_id") or ""
    ssh_host = body.get("ssh_host") or ""
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    try:
        mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(device_id, ssh_host)
        config = _get_cached_config(scaler_id)
        if not config:
            config = DeviceCommHelper().fetch_running_config(
                device_id, ssh_host, mgmt_ip=mgmt_ip, scaler_id=scaler_id,
            )
        if not config:
            raise HTTPException(status_code=404, detail="No config available")
        from scaler.wizard.scale_operations import (
            _generate_scale_up_suggestions,
            parse_services_from_config,
        )
        device_services = {scaler_id: parse_services_from_config(config)}
        # Minimal multi_ctx-like object
        class _MinimalCtx:
            configs = {scaler_id: config}
        suggestions = _generate_scale_up_suggestions(_MinimalCtx(), device_services)
        # Serialize suggestions (remove non-JSON fields like apply_func)
        out = []
        for s in suggestions:
            item = {k: v for k, v in s.items() if k != "apply_func" and not callable(v)}
            out.append(item)
        return {"suggestions": out}
    except HTTPException:
        raise
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"scale_operations unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/api/config/generate/system")
def generate_system(body: dict = None):
    """Generate system config (hostname, NTP, DNS, SSH, SNMP)."""
    body = body or {}
    try:
        from scaler.wizard.config_builders import build_system_config
        config = build_system_config(body)
        return {"config": config}
    except ImportError:
        raise HTTPException(status_code=501, detail="config_builders unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/config/validate/policy")
def validate_policy(body: dict = None):
    """Validate routing policy config (old rule-based). Returns validation result."""
    body = body or {}
    config_text = body.get("config_text") or body.get("config") or ""
    device_id = body.get("device_id")
    ssh_host = body.get("ssh_host") or ""
    if not config_text and device_id:
        try:
            mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(device_id, ssh_host)
            config = _get_cached_config(scaler_id)
            if not config:
                config = DeviceCommHelper().fetch_running_config(
                    device_id, ssh_host, mgmt_ip=mgmt_ip, scaler_id=scaler_id,
                )
            if config:
                config_text = config  # load_policies_from_config extracts routing-policy internally
        except Exception:
            pass
    if not config_text:
        raise HTTPException(status_code=400, detail="config_text or device_id required")
    try:
        from scaler.wizard.parsers import load_policies_from_config
        from scaler.wizard.policy_validator import validate_policy_manager
        manager = load_policies_from_config(config_text)
        result = validate_policy_manager(manager)
        issues = [
            {
                "severity": i.severity.value if hasattr(i.severity, "value") else str(i.severity),
                "component": i.component,
                "issue": i.issue,
                "suggestion": i.suggestion,
                "location": i.location,
            }
            for i in result.issues
        ]
        return {"valid": result.valid, "issues": issues}
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"policy modules unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/config/generate/route-policy-structured")
def generate_route_policy_structured(body: dict = None):
    """Generate route-policy config from structured params (new syntax SW-181332)."""
    body = body or {}
    try:
        from scaler.wizard.config_builders import build_routing_policy_config
        params = {"type": "route-policy", **{k: v for k, v in body.items() if k != "type"}}
        config = build_routing_policy_config(params)
        return {"config": config}
    except ImportError:
        raise HTTPException(status_code=501, detail="config_builders unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/config/generate/services")
def generate_services(body: dict = None):
    """Generate service config from GUI params. Uses scaler-wizard config_builders."""
    body = body or {}
    try:
        from scaler.wizard.config_builders import build_service_config
        config = build_service_config(body)
        return {"config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/config/generate/bgp")
def generate_bgp(body: dict = None):
    """Generate BGP peer config from GUI params. Uses scaler-wizard config_builders."""
    body = body or {}
    try:
        from scaler.wizard.config_builders import build_bgp_config
        config = build_bgp_config(body)
        return {"config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/config/compare")
def compare_configs(body: dict = None):
    """Compare configs of two devices. Returns unified diff."""
    body = body or {}
    device_ids = body.get("device_ids") or []
    ssh_hosts = body.get("ssh_hosts") or ["", ""]
    if len(device_ids) != 2:
        raise HTTPException(status_code=400, detail="Exactly 2 device_ids required")
    configs = []
    for i, did in enumerate(device_ids):
        mgmt_ip, scaler_id, via = _resolve_mgmt_ip(did, ssh_hosts[i] if i < len(ssh_hosts) else "")
        cfg = _get_cached_config(scaler_id)
        if not cfg:
            try:
                cfg = DeviceCommHelper().fetch_running_config(
                    did, ssh_hosts[i] if i < len(ssh_hosts) else "",
                    mgmt_ip=mgmt_ip, scaler_id=scaler_id,
                )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=503, detail=f"{did}: {e}")
        configs.append(cfg)
    try:
        from scaler.diff_generator import DiffGenerator
        dg = DiffGenerator()
        diff_text = dg.generate_unified_diff(configs[0], configs[1], device_ids[0], device_ids[1])
        added = sum(1 for l in diff_text.splitlines() if l.startswith("+") and not l.startswith("+++"))
        removed = sum(1 for l in diff_text.splitlines() if l.startswith("-") and not l.startswith("---"))
        return {
            "diff_text": diff_text,
            "device_a": device_ids[0],
            "device_b": device_ids[1],
            "lines_added": added,
            "lines_removed": removed,
        }
    except ImportError:
        diff_lines = []
        for i, (a, b) in enumerate(zip(configs[0].splitlines(), configs[1].splitlines())):
            if a != b:
                diff_lines.append(f"- {a}")
                diff_lines.append(f"+ {b}")
        return {
            "diff_text": "\n".join(diff_lines) or "(no diff)",
            "device_a": device_ids[0],
            "device_b": device_ids[1],
            "lines_added": 0,
            "lines_removed": 0,
        }


@router.get("/api/config/{device_id}/interfaces")
def get_config_interfaces(device_id: str, ssh_host: str = ""):
    """Parse interfaces from device config. Returns structured interface list."""
    mgmt_ip, scaler_id, via = _resolve_mgmt_ip(device_id, ssh_host)
    config = _get_cached_config(scaler_id)
    if not config:
        try:
            config = DeviceCommHelper().fetch_running_config(
                device_id, ssh_host, mgmt_ip=mgmt_ip, scaler_id=scaler_id,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))
    try:
        from scaler.wizard.parsers import extract_hierarchy_section, build_interface_to_vlan_mapping
        iface_section = extract_hierarchy_section(config, "interfaces")
        vlan_map = build_interface_to_vlan_mapping(config)
        interfaces = []
        if iface_section:
            for line in iface_section.splitlines():
                m = re.match(r"^\s*interfaces\s+(\S+)", line)
                if m:
                    name = m.group(1)
                    interfaces.append({"name": name, "vlan": vlan_map.get(name, "none")})
        return {"interfaces": interfaces, "count": len(interfaces)}
    except ImportError:
        interfaces = []
        for line in config.splitlines():
            if line.strip().startswith("interfaces ") and " " in line.strip()[10:]:
                parts = line.strip().split()
                if len(parts) >= 2:
                    interfaces.append({"name": parts[1], "vlan": "unknown"})
        return {"interfaces": interfaces, "count": len(interfaces)}


_LIMITS_DEFAULT = {"max_subifs": 20480}


def _load_limits(device_id: str) -> dict:
    """Load platform limits from ~/.scaler/limits.json or SCALER_ROOT/limits.json."""
    for p in [
        Path.home() / ".scaler" / "limits.json",
        SCALER_ROOT / "limits.json",
    ]:
        if p.exists():
            try:
                data = json.loads(p.read_text())
                dpl = data.get("dnos_platform_limits", {})
                pools = dpl.get("ifindex_pools", {})
                vlan = pools.get("vlan_pool", {})
                max_subifs = vlan.get("max_capacity", _LIMITS_DEFAULT["max_subifs"])
                return {"max_subifs": max_subifs}
            except Exception:
                pass
    return _LIMITS_DEFAULT.copy()


@router.get("/api/config/limits/{device_id}")
def get_config_limits(device_id: str):
    """Get platform limits for device. Returns max_subifs from limits.json or default 20480."""
    return _load_limits(device_id)


@router.get("/api/config/templates/smart-defaults/{device_id}")
def get_smart_defaults(device_id: str, ssh_host: str = ""):
    """Get smart defaults (ASN, router-id) for policy templates from device config."""
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    try:
        mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(device_id, ssh_host)
        config = _get_cached_config(scaler_id)
        if not config:
            config = DeviceCommHelper().fetch_running_config(
                device_id, ssh_host, mgmt_ip=mgmt_ip, scaler_id=scaler_id,
            )
        asn = None
        router_id = None
        if config:
            import re
            asn_match = re.search(r'local-as\s+(\d+)', config) or re.search(r'bgp\s+(\d+)', config)
            if asn_match:
                asn = int(asn_match.group(1))
            rid_match = re.search(r'router-id\s+(\d+\.\d+\.\d+\.\d+)', config)
            if rid_match:
                router_id = rid_match.group(1)
        return {
            "device_id": device_id,
            "asn": asn,
            "router_id": router_id,
            "defaults": {"asn": asn or 65000, "router_id": router_id or "1.1.1.1"},
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/api/config/templates")
def get_policy_templates():
    """List available policy templates from PolicyTemplateEngine."""
    try:
        from scaler.wizard.policy_templates import PolicyTemplateEngine
        engine = PolicyTemplateEngine()
        templates = []
        catalog = getattr(engine, "templates", {}) or getattr(engine, "catalog", []) or {}
        items = catalog.values() if isinstance(catalog, dict) else catalog
        for t in items:
            templates.append({
                "name": getattr(t, "name", str(t)),
                "description": getattr(t, "description", ""),
                "use_case": getattr(t, "use_case", ""),
                "variables": [{"name": getattr(v, "name", str(v))} for v in getattr(t, "variables", [])],
            })
        if not templates:
            templates = [
                {"name": "DENY_BOGONS_V4", "description": "Deny bogon prefixes IPv4", "use_case": "security", "variables": []},
                {"name": "CUSTOMER_IMPORT", "description": "Customer import policy", "use_case": "vpn", "variables": []},
            ]
        return {"templates": templates}
    except ImportError:
        return {"templates": [{"name": "DENY_BOGONS_V4", "description": "Deny bogon prefixes", "use_case": "security", "variables": []}]}


@router.post("/api/config/templates/generate")
def generate_from_template(body: dict = None):
    """Generate policy config from a template with variable values."""
    body = body or {}
    template_name = body.get("template_name")
    values = body.get("values") or {}
    if not template_name:
        raise HTTPException(status_code=400, detail="template_name required")
    try:
        from scaler.wizard.policy_templates import PolicyTemplateEngine
        engine = PolicyTemplateEngine(
            device_asn=int(values.get("asn", 65000)),
            device_router_id=values.get("router_id", "1.1.1.1"),
        )
        manager = engine.generate_from_template(template_name, values)
        if hasattr(manager, "to_dnos_config"):
            config = manager.to_dnos_config()
        elif hasattr(manager, "config"):
            config = manager.config
        else:
            config = str(manager)
        return {"config": config if isinstance(config, str) else str(config)}
    except ImportError:
        return {"config": f"! Template {template_name} - run scaler-wizard for full generation"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/config/{device_id}/diff")
def get_config_diff(device_id: str, ssh_host: str = ""):
    """Compare cached vs live config. Returns diff and in_sync status."""
    mgmt_ip, scaler_id, via = _resolve_mgmt_ip(device_id, ssh_host)
    cached = _get_cached_config(scaler_id)
    if not cached:
        raise HTTPException(status_code=404, detail="No cached config. Sync first.")
    try:
        live = DeviceCommHelper().fetch_running_config(
            device_id, ssh_host, mgmt_ip=mgmt_ip, scaler_id=scaler_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
    try:
        from scaler.diff_generator import DiffGenerator
        dg = DiffGenerator()
        diff_text = dg.generate_unified_diff(cached, live, "cached", "live")
        in_sync = cached.strip() == live.strip()
        cached_path = Path(SCALER_ROOT) / "db" / "configs" / device_id / "running.txt"
        cached_age = int(cached_path.stat().st_mtime) if cached_path.exists() else 0
        return {"in_sync": in_sync, "diff_text": diff_text, "cached_age": cached_age}
    except ImportError:
        in_sync = cached.strip() == live.strip()
        return {"in_sync": in_sync, "diff_text": "(diff unavailable)", "cached_age": 0}


@router.post("/api/config/generate/routing-policy")
def generate_routing_policy(body: dict = None):
    """Generate routing-policy config (prefix-list or route-policy new syntax)."""
    body = body or {}
    try:
        from scaler.wizard.config_builders import build_routing_policy_config
        config = build_routing_policy_config(body)
        return {"config": config}
    except ImportError:
        raise HTTPException(status_code=501, detail="config_builders unavailable")


@router.post("/api/config/generate/flowspec")
def generate_flowspec(body: dict = None):
    """Generate FlowSpec local policies config from GUI params."""
    body = body or {}
    try:
        from scaler.wizard.config_builders import build_flowspec_config
        config = build_flowspec_config(body)
        return {"config": config}
    except ImportError:
        raise HTTPException(status_code=501, detail="config_builders unavailable")


@router.post("/api/config/flowspec-dependency-check")
def flowspec_dependency_check(body: dict = None):
    """Run FlowSpec dependency check on device config. Returns issues with fix commands."""
    body = body or {}
    device_id = body.get("device_id") or ""
    ssh_host = body.get("ssh_host") or ""
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    try:
        config, _, _ = _fetch_config_for_device(device_id, ssh_host)
        from types import SimpleNamespace
        from scaler.interactive_scale import check_flowspec_dependencies
        state = SimpleNamespace(current_config="")
        issues = check_flowspec_dependencies(state, config_text=config)
        return {
            "issues": [
                {"component": i.component, "issue": i.issue, "severity": i.severity,
                 "fix_command": i.fix_command, "fix_description": i.fix_description}
                for i in issues
            ],
            "passed": len(issues) == 0,
        }
    except HTTPException:
        raise
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"flowspec dependency check unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/api/config/generate/igp")
def generate_igp(body: dict = None):
    """Generate IGP (ISIS/OSPF) config from GUI params. Uses config_builders.build_igp_config."""
    body = body or {}
    interfaces = body.get("interfaces") or []
    if isinstance(interfaces, str):
        interfaces = [x.strip() for x in interfaces.split(",") if x.strip()]
    params = {
        "protocol": (body.get("protocol") or "isis").lower(),
        "area_id": body.get("area_id", "49.0001"),
        "router_id": body.get("router_ip", body.get("router_id", "1.1.1.1")),
        "interfaces": interfaces,
        "level": body.get("level", "level-1-2"),
        "passive_for_all": bool(body.get("passive_for_all", False)),
        "default_metric": body.get("default_metric"),
        "interface_options": body.get("interface_options"),
    }
    try:
        from scaler.wizard.config_builders import build_igp_config
        config = build_igp_config(params)
        return {"config": config}
    except ImportError:
        raise HTTPException(status_code=501, detail="config_builders unavailable")


@router.post("/api/config/generate/batch")
def generate_batch(body: dict = None):
    """Batch generate config from multiple hierarchies.
    Accepts {items: [{hierarchy: string, params: object}, ...]}.
    Returns {config: string} with combined DNOS config.
    """
    body = body or {}
    items = body.get("items") or []
    if not items:
        return {"config": ""}
    configs = []
    try:
        from scaler.wizard.config_builders import (
            build_interface_config,
            build_service_config,
            build_bgp_config,
            build_igp_config,
            build_flowspec_config,
            build_routing_policy_config,
        )
        for item in items:
            h = (item.get("hierarchy") or "").lower()
            p = item.get("params") or {}
            if h == "interfaces":
                cfg = build_interface_config(p)
            elif h == "flowspec":
                cfg = build_flowspec_config(p)
            elif h in ("routing-policy", "policy"):
                cfg = build_routing_policy_config(p)
            elif h in ("services", "vrf", "bridge-domain"):
                p.setdefault("service_type", "evpn-vpws-fxc" if h == "services" else h)
                cfg = build_service_config(p)
            elif h == "bgp":
                cfg = build_bgp_config(p)
            elif h == "igp":
                p.setdefault("router_id", p.get("router_ip"))
                cfg = build_igp_config(p)
            else:
                continue
            if cfg and cfg.strip():
                configs.append(cfg.strip())
        return {"config": "\n\n".join(configs)}
    except ImportError:
        raise HTTPException(status_code=501, detail="config_builders unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/config/preview-diff")
def preview_config_diff(body: dict = None):
    """Preview diff of proposed config vs current running config.
    Accepts {device_id: string, config: string, ssh_host?: string}.
    Returns {diff_text: string, lines_added: int, lines_removed: int}.
    """
    body = body or {}
    device_id = body.get("device_id")
    proposed = body.get("config", "")
    ssh_host = body.get("ssh_host", "")
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    try:
        mgmt_ip, scaler_id, via = _resolve_mgmt_ip(device_id, ssh_host)
        running = _get_cached_config(scaler_id)
        if not running:
            try:
                running = DeviceCommHelper().fetch_running_config(
                    device_id, ssh_host, mgmt_ip=mgmt_ip, scaler_id=scaler_id,
                )
            except Exception:
                running = ""
        running = running or ""
        try:
            from scaler.diff_generator import DiffGenerator
            dg = DiffGenerator()
            diff_text = dg.generate_unified_diff(running, proposed, "running", "proposed")
        except ImportError:
            r_lines = running.splitlines()
            p_lines = proposed.splitlines()
            diff_lines = []
            for i, (a, b) in enumerate(zip(r_lines, p_lines)):
                if a != b:
                    diff_lines.append(f"- {a}")
                    diff_lines.append(f"+ {b}")
            for a in r_lines[len(p_lines):]:
                diff_lines.append(f"- {a}")
            for b in p_lines[len(r_lines):]:
                diff_lines.append(f"+ {b}")
            diff_text = "\n".join(diff_lines) or "(no diff)"
        added = sum(1 for l in diff_text.splitlines() if l.startswith("+") and not l.startswith("+++"))
        removed = sum(1 for l in diff_text.splitlines() if l.startswith("-") and not l.startswith("---"))
        return {"diff_text": diff_text, "lines_added": added, "lines_removed": removed}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


def _fetch_config_for_device(device_id: str, ssh_host: str) -> tuple:
    """Resolve device, fetch config. Returns (config, scaler_id, hostname)."""
    mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(device_id, ssh_host)
    config = _get_cached_config(scaler_id)
    if not config:
        config = DeviceCommHelper().fetch_running_config(
            device_id, ssh_host, mgmt_ip=mgmt_ip, scaler_id=scaler_id,
        )
    if not config:
        raise HTTPException(status_code=404, detail=f"No config for {device_id}")
    hostname = device_id
    try:
        resolved = _resolve_device(device_id)
        hostname = resolved.get("hostname") or resolved.get("name") or device_id
    except Exception:
        pass
    return config, scaler_id, hostname


@router.post("/api/mirror/analyze")
def mirror_analyze(body: dict = None):
    """Analyze source vs target for mirror. Returns summaries, smart_diff, interface mapping options."""
    body = body or {}
    source_id = body.get("source_device_id") or ""
    target_id = body.get("target_device_id") or ""
    ssh_hosts = body.get("ssh_hosts") or ["", ""]
    if not source_id or not target_id:
        raise HTTPException(status_code=400, detail="source_device_id and target_device_id required")
    try:
        src_config, _, src_host = _fetch_config_for_device(source_id, ssh_hosts[0] if len(ssh_hosts) > 0 else "")
        tgt_config, _, tgt_host = _fetch_config_for_device(target_id, ssh_hosts[1] if len(ssh_hosts) > 1 else "")
        from scaler.wizard.mirror_config import ConfigMirror
        mirror = ConfigMirror(src_config, tgt_config, src_host, tgt_host)
        mirror.map_interfaces_auto()
        smart_diff = mirror.analyze_smart_diff()
        lldp_neighbors = body.get("lldp_neighbors") or []
        smart_suggestions = mirror.get_smart_suggestions(lldp_neighbors)
        return {
            "source_summary": mirror.get_source_summary(),
            "target_summary": mirror.get_target_summary(),
            "smart_diff": smart_diff,
            "interface_map": mirror.interface_map,
            "requires_merge": mirror.requires_merge,
            "smart_suggestions": smart_suggestions,
        }
    except HTTPException:
        raise
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"mirror_config unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/api/mirror/generate")
def mirror_generate(body: dict = None):
    """Generate mirrored config. Accepts interface_map, section_selection, output_mode."""
    body = body or {}
    source_id = body.get("source_device_id") or ""
    target_id = body.get("target_device_id") or ""
    ssh_hosts = body.get("ssh_hosts") or ["", ""]
    interface_map = body.get("interface_map") or {}
    output_mode = body.get("output_mode") or "diff_only"
    if not source_id or not target_id:
        raise HTTPException(status_code=400, detail="source_device_id and target_device_id required")
    try:
        src_config, _, src_host = _fetch_config_for_device(source_id, ssh_hosts[0] if len(ssh_hosts) > 0 else "")
        tgt_config, _, tgt_host = _fetch_config_for_device(target_id, ssh_hosts[1] if len(ssh_hosts) > 1 else "")
        from scaler.wizard.mirror_config import ConfigMirror
        mirror = ConfigMirror(src_config, tgt_config, src_host, tgt_host)
        if interface_map:
            mirror.interface_map = interface_map
            mirror._compile_interface_pattern()
        else:
            mirror.map_interfaces_auto()
        ip_mapping = body.get("ip_mapping") or {}
        if ip_mapping:
            mirror.ip_mapping = ip_mapping
        if body.get("section_selection"):
            mirror.section_selection = body["section_selection"]
        elif body.get("section_actions"):
            # section_actions: { system: "keep", interfaces: "edit", ... } -> section_selection: { system: True, ... }
            actions = body["section_actions"]
            mirror.section_selection = {
                k: v in ("keep", "edit") for k, v in actions.items()
            }
        if output_mode == "full":
            config = mirror.generate_merged_config()
            summary = {"mode": "full", "line_count": len(config.splitlines())}
        else:
            config, summary = mirror.generate_diff_only_config()
        return {
            "config": config,
            "summary": summary,
            "line_count": len(config.splitlines()),
            "diff_stats": summary,
        }
    except HTTPException:
        raise
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"mirror_config unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/api/mirror/preview-diff")
def mirror_preview_diff(body: dict = None):
    """Preview diff of proposed mirrored config vs target running. Reuses preview_config_diff logic."""
    body = body or {}
    target_id = body.get("target_device_id") or ""
    proposed = body.get("config", "")
    ssh_host = body.get("ssh_host", "")
    if not target_id:
        raise HTTPException(status_code=400, detail="target_device_id required")
    return preview_config_diff({"device_id": target_id, "config": proposed, "ssh_host": ssh_host})


@router.get("/api/config/delete-hierarchy-options")
def get_delete_hierarchy_options():
    """Return hierarchy table for Delete Hierarchy GUI: display name, command, warning."""
    try:
        from scaler.wizard.push import HIERARCHY_DISPLAY_NAMES, HIERARCHY_DELETE_COMMANDS, CRITICAL_HIERARCHIES
        rows = []
        for hier in HIERARCHY_DELETE_COMMANDS.keys():
            cfg = HIERARCHY_DELETE_COMMANDS[hier]
            display = HIERARCHY_DISPLAY_NAMES.get(hier, hier)
            if cfg.get("smart_delete"):
                cmd = "(Smart: keeps physical, deletes service ifs)"
            elif "commands" in cfg:
                cmd = " / ".join(cfg["commands"])
            else:
                cmd = cfg.get("command") or "N/A"
            warning = cfg.get("warning", "")
            if hier in CRITICAL_HIERARCHIES and not cfg.get("smart_delete"):
                warning = "[CRITICAL] " + warning if warning else "[CRITICAL]"
            rows.append({"hierarchy": hier, "display": display, "command": cmd, "warning": warning})
        return {"hierarchies": rows}
    except ImportError:
        raise HTTPException(status_code=501, detail="push module unavailable")

