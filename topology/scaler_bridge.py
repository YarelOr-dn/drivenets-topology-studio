#!/usr/bin/env python3
"""
Scaler Bridge API - REST wrapper for scaler-wizard modules.

Exposes device config fetch, sync, and summary endpoints for the topology app.
Runs on port 8766. The main serve.py proxies /api/config/* to this service.

Usage:
    python3 scaler_bridge.py
    # Or: python3 -m uvicorn scaler_bridge:app --host 0.0.0.0 --port 8766
"""
import json
import os
import re
import sys
from pathlib import Path

# Ensure SCALER is on path
SCALER_ROOT = Path(os.environ.get("SCALER_ROOT", str(Path.home() / "SCALER")))
if str(SCALER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCALER_ROOT))

import urllib.error
import urllib.parse
import urllib.request

DISCOVERY_API = os.environ.get("DISCOVERY_API", "http://localhost:8765")
XRAY_CONFIG_PATH = os.path.expanduser("~/.xray_config.json")


def _resolve_device(device_id: str) -> dict:
    """Resolve device to mgmt_ip via discovery_api."""
    url = f"{DISCOVERY_API}/api/device/{urllib.parse.quote(device_id)}/resolve"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def _get_credentials() -> tuple:
    """Get device SSH credentials from XRAY config."""
    try:
        with open(XRAY_CONFIG_PATH) as f:
            cfg = json.load(f)
        creds = cfg.get("credentials", {})
        user = creds.get("device_user", "dnroot")
        password = creds.get("device_password", "dnroot")
        return user, password
    except Exception:
        return "dnroot", "dnroot"


_resolve_cache = {}
_scaler_ops_index = None
_scaler_ops_index_ts = 0


def _build_scaler_ops_index():
    """Build an in-memory index of all SCALER operational.json files.
    Maps: serial, hostname, mgmt_ip, dir_name -> {ip, scaler_id, serial}
    Cached for 60 seconds.
    """
    global _scaler_ops_index, _scaler_ops_index_ts
    import time
    now = time.time()
    if _scaler_ops_index and (now - _scaler_ops_index_ts) < 60:
        return _scaler_ops_index

    index = {}
    configs_dir = Path(SCALER_ROOT) / "db" / "configs"
    if not configs_dir.exists():
        _scaler_ops_index = index
        _scaler_ops_index_ts = now
        return index

    for dev_dir in configs_dir.iterdir():
        if not dev_dir.is_dir():
            continue
        ops_path = dev_dir / "operational.json"
        if not ops_path.exists():
            continue
        try:
            ops = json.loads(ops_path.read_text())
            raw_ssh = (ops.get("ssh_host") or "").strip()
            raw_mgmt = (ops.get("mgmt_ip") or "").strip().split("/")[0]
            is_ssh_ip = bool(raw_ssh and re.match(r"^\d+\.\d+\.\d+\.\d+$", raw_ssh))
            ip = raw_mgmt if raw_mgmt and re.match(r"^\d+\.\d+\.\d+\.\d+$", raw_mgmt) else (raw_ssh if is_ssh_ip else raw_mgmt or raw_ssh)
            serial = (ops.get("serial_number") or "").strip()
            entry = {"ip": ip, "scaler_id": dev_dir.name, "serial": serial}
            index[dev_dir.name.lower()] = entry
            if serial:
                index[serial.lower()] = entry
            if ip:
                index[ip] = entry
            if raw_ssh and raw_ssh.lower() not in index:
                index[raw_ssh.lower()] = entry
        except Exception:
            continue

    _scaler_ops_index = index
    _scaler_ops_index_ts = now
    return index


def _resolve_mgmt_ip(device_id: str, ssh_host: str = "") -> tuple:
    """Central device IP resolution. Returns (mgmt_ip, scaler_device_id, resolved_via).
    
    Resolution chain (fast, uses cached SCALER index):
    1. ssh_host is an IP -> match directly in SCALER ops index
    2. ssh_host is a serial/hostname -> match in SCALER ops index
    3. device_id exact match in SCALER ops index
    4. Discovery API _resolve_device()
    5. device_inventory.json fuzzy match
    6. Partial name match in SCALER ops index (PE-1 in YOR_PE-1)
    
    Raises HTTPException(503) if no IP can be found.
    """
    cache_key = f"{device_id}|{ssh_host}"
    if cache_key in _resolve_cache:
        cached = _resolve_cache[cache_key]
        import time
        if time.time() - cached[3] < 120:
            return cached[0], cached[1], cached[2]

    ssh = ssh_host.strip() if ssh_host else ""
    idx = _build_scaler_ops_index()

    is_ip = bool(ssh and re.match(r"^\d+\.\d+\.\d+\.\d+$", ssh))

    if is_ip:
        entry = idx.get(ssh)
        if entry and entry["ip"]:
            result = (entry["ip"], entry["scaler_id"], f"ssh_ip:{ssh}")
            _cache_resolve(cache_key, result)
            return result
        result = (ssh, device_id, f"ssh_ip_direct:{ssh}")
        _cache_resolve(cache_key, result)
        return result

    if ssh:
        entry = idx.get(ssh.lower())
        if entry and entry["ip"]:
            result = (entry["ip"], entry["scaler_id"], f"ssh_serial:{ssh}->{entry['scaler_id']}")
            _cache_resolve(cache_key, result)
            return result

    entry = idx.get(device_id.lower())
    if entry and entry["ip"]:
        result = (entry["ip"], entry["scaler_id"], f"scaler_index:{device_id}")
        _cache_resolve(cache_key, result)
        return result

    try:
        resolved = _resolve_device(device_id)
        ip = resolved.get("mgmt_ip", "").strip()
        if ip:
            idx_entry = idx.get(ip)
            sid = idx_entry["scaler_id"] if idx_entry else device_id
            result = (ip, sid, "discovery_api")
            _cache_resolve(cache_key, result)
            return result
    except Exception:
        pass

    inv_dev = _find_inventory_device(device_id, ssh)
    ip = (inv_dev.get("mgmt_ip") or inv_dev.get("ip") or "").strip().split("/")[0]
    if ip:
        idx_entry = idx.get(ip)
        sid = idx_entry["scaler_id"] if idx_entry else device_id
        result = (ip, sid, "device_inventory")
        _cache_resolve(cache_key, result)
        return result

    for key, entry in idx.items():
        if entry["ip"] and (device_id.lower() in key or key in device_id.lower()):
            result = (entry["ip"], entry["scaler_id"], f"partial:{key}")
            _cache_resolve(cache_key, result)
            return result

    raise HTTPException(
        status_code=503,
        detail=f"Could not resolve IP for '{device_id}'"
               f"{' (ssh_host=' + ssh + ')' if ssh else ''}. "
               "Set SSH address (IP) on the canvas device (right-click > Set SSH)."
    )


def _cache_resolve(key, result):
    import time
    _resolve_cache[key] = (result[0], result[1], result[2], time.time())


def _fetch_config_via_ssh(device_id: str, mgmt_ip: str, user: str, password: str) -> str:
    """Fetch running config via SSH using scaler ConfigExtractor."""
    from scaler.models import Device
    from scaler.config_extractor import InteractiveExtractor

    device = Device(
        id=device_id,
        hostname=device_id,
        ip=mgmt_ip,
        username=user,
        password=Device.encode_password(password),
    )
    # Ensure operational.json has mgmt_ip for get_ssh_hostname
    config_dir = Path(SCALER_ROOT) / "db" / "configs" / device_id
    config_dir.mkdir(parents=True, exist_ok=True)
    ops_file = config_dir / "operational.json"
    ops_data = {}
    if ops_file.exists():
        with open(ops_file) as f:
            ops_data = json.load(f)
    ops_data["mgmt_ip"] = mgmt_ip
    with open(ops_file, "w") as f:
        json.dump(ops_data, f, indent=2)

    with InteractiveExtractor(device, timeout=180) as extractor:
        return extractor.get_running_config(fetch_lldp=False)


def _get_cached_config(device_id: str) -> str | None:
    """Read cached running config from SCALER db."""
    config_path = Path(SCALER_ROOT) / "db" / "configs" / device_id / "running.txt"
    if config_path.exists():
        return config_path.read_text()
    return None


def _build_config_summary(config: str) -> dict:
    """Parse config and build structured summary using scaler parsers."""
    try:
        from scaler.wizard.parsers import (
            parse_existing_evpn_services,
            parse_existing_multihoming,
            parse_route_targets,
            get_lo0_ip_from_config,
            get_as_number_from_config,
            get_router_id_from_config,
        )
        from scaler.wizard.parsers import extract_lldp_section, extract_lacp_section
    except ImportError as e:
        return {"error": f"Parser import failed: {e}", "raw_lines": len(config.splitlines())}

    as_num = get_as_number_from_config(config)
    summary = {
        "lines": len(config.splitlines()),
        "loopback0_ip": get_lo0_ip_from_config(config) or "",
        "as_number": str(as_num) if as_num is not None else "",
        "router_id": get_router_id_from_config(config) or "",
        "route_targets": list(parse_route_targets(config)),
        "evpn_services": {},
        "multihoming_interfaces": 0,
    }

    try:
        evpn = parse_existing_evpn_services(config)
        summary["evpn_services"] = {k: len(v) for k, v in evpn.items()}
    except Exception:
        pass

    try:
        mh = parse_existing_multihoming(config)
        summary["multihoming_interfaces"] = len(mh)
    except Exception:
        pass

    return summary


# FastAPI app
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
except ImportError:
    print("Install fastapi and uvicorn: pip install fastapi uvicorn")
    sys.exit(1)

app = FastAPI(title="Scaler Bridge", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/config/{device_id}/running")
def get_running_config(device_id: str, live: bool = False, ssh_host: str = ""):
    """Get running config - cached or live fetch."""
    mgmt_ip, scaler_id, via = _resolve_mgmt_ip(device_id, ssh_host)
    config = _get_cached_config(scaler_id)
    if live or not config:
        try:
            user, password = _get_credentials()
            config = _fetch_config_via_ssh(scaler_id, mgmt_ip, user, password)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    if not config:
        raise HTTPException(status_code=404, detail="No config available")
    return {"config": config}


@app.get("/api/config/{device_id}/summary")
def get_config_summary(device_id: str, ssh_host: str = ""):
    """Get parsed config summary."""
    mgmt_ip, scaler_id, via = _resolve_mgmt_ip(device_id, ssh_host)
    config = _get_cached_config(scaler_id)
    if not config:
        try:
            user, password = _get_credentials()
            config = _fetch_config_via_ssh(scaler_id, mgmt_ip, user, password)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    if not config:
        raise HTTPException(status_code=404, detail="No config available")
    return _build_config_summary(config)


@app.post("/api/config/{device_id}/sync")
def sync_config(device_id: str, ssh_host: str = ""):
    """Fetch running config from device and cache it."""
    try:
        mgmt_ip, scaler_id, via = _resolve_mgmt_ip(device_id, ssh_host)
        user, password = _get_credentials()
        config = _fetch_config_via_ssh(scaler_id, mgmt_ip, user, password)
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


@app.post("/api/config/generate/interfaces")
def generate_interfaces(body: dict = None):
    """Generate interface config from GUI params. Uses scaler-wizard config_builders."""
    body = body or {}
    try:
        from scaler.wizard.config_builders import build_interface_config
        config = build_interface_config(body)
        return {"config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/scan-existing")
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
            user, password = _get_credentials()
            config = _fetch_config_via_ssh(scaler_id, mgmt_ip, user, password)
        if not config:
            raise HTTPException(status_code=404, detail="No config available")
        from scaler.wizard.scale_operations import (
            _scan_used_sub_ids,
            _scan_l3_sub_ids,
            _scan_used_vrf_numbers,
            _scan_used_route_targets,
            _find_free_numbers,
        )
        result = {
            "existing_sub_ids": [],
            "existing_vrfs": [],
            "existing_evis": [],
            "l3_conflicts": [],
            "next_free": {},
        }
        if scan_type in ("interfaces", "all") and parent_interface:
            used_sub = _scan_used_sub_ids(config, parent_interface)
            l3_conflicts = _scan_l3_sub_ids(config, parent_interface)
            result["existing_sub_ids"] = sorted(used_sub)
            result["l3_conflicts"] = sorted(l3_conflicts)
            result["next_free"]["sub_id"] = next((n for n in range(1, 65536) if n not in used_sub), 1)
        if scan_type in ("services", "vrfs", "all"):
            vrf_used = _scan_used_vrf_numbers(config, "VRF-")
            result["existing_vrfs"] = [f"VRF-{n}" for n in sorted(vrf_used)]
            result["next_free"]["vrf_num"] = next((n for n in range(1, 65536) if n not in vrf_used), 1)
        return result
    except HTTPException:
        raise
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"scale_operations unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/config/detect-pattern")
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
            user, password = _get_credentials()
            config = _fetch_config_via_ssh(scaler_id, mgmt_ip, user, password)
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
        return {
            "vlan_mode": vlan_mode,
            "stepping_tag": step_mode,
            "last_vlan": last_vlan,
            "last_sub_id": last_sub,
            "interface_type": "l2ac" if "ge" in parent_interface or "bundle" in parent_interface else "pwhe",
            "pattern": {k: v for k, v in pattern.items() if isinstance(v, (str, int, float, bool, type(None)))},
        }
    except HTTPException:
        raise
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"scale_operations unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/config/generate/services")
def generate_services(body: dict = None):
    """Generate service config from GUI params. Uses scaler-wizard config_builders."""
    body = body or {}
    try:
        from scaler.wizard.config_builders import build_service_config
        config = build_service_config(body)
        return {"config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/generate/bgp")
def generate_bgp(body: dict = None):
    """Generate BGP peer config from GUI params. Uses scaler-wizard config_builders."""
    body = body or {}
    try:
        from scaler.wizard.config_builders import build_bgp_config
        config = build_bgp_config(body)
        return {"config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/compare")
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
                user, password = _get_credentials()
                cfg = _fetch_config_via_ssh(scaler_id, mgmt_ip, user, password)
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


@app.get("/api/config/{device_id}/interfaces")
def get_config_interfaces(device_id: str, ssh_host: str = ""):
    """Parse interfaces from device config. Returns structured interface list."""
    mgmt_ip, scaler_id, via = _resolve_mgmt_ip(device_id, ssh_host)
    config = _get_cached_config(scaler_id)
    if not config:
        try:
            user, password = _get_credentials()
            config = _fetch_config_via_ssh(scaler_id, mgmt_ip, user, password)
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


@app.get("/api/config/limits/{device_id}")
def get_config_limits(device_id: str):
    """Get platform limits for device. Returns max_subifs from limits.json or default 20480."""
    return _load_limits(device_id)


@app.get("/api/config/templates")
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


@app.post("/api/config/templates/generate")
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


@app.get("/api/config/{device_id}/diff")
def get_config_diff(device_id: str, ssh_host: str = ""):
    """Compare cached vs live config. Returns diff and in_sync status."""
    mgmt_ip, scaler_id, via = _resolve_mgmt_ip(device_id, ssh_host)
    cached = _get_cached_config(scaler_id)
    if not cached:
        raise HTTPException(status_code=404, detail="No cached config. Sync first.")
    try:
        user, password = _get_credentials()
        live = _fetch_config_via_ssh(scaler_id, mgmt_ip, user, password)
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


@app.post("/api/config/generate/routing-policy")
def generate_routing_policy(body: dict = None):
    """Generate routing-policy config (prefix-list or route-policy new syntax)."""
    body = body or {}
    try:
        from scaler.wizard.config_builders import build_routing_policy_config
        config = build_routing_policy_config(body)
        return {"config": config}
    except ImportError:
        raise HTTPException(status_code=501, detail="config_builders unavailable")


@app.post("/api/config/generate/flowspec")
def generate_flowspec(body: dict = None):
    """Generate FlowSpec local policies config from GUI params."""
    body = body or {}
    try:
        from scaler.wizard.config_builders import build_flowspec_config
        config = build_flowspec_config(body)
        return {"config": config}
    except ImportError:
        raise HTTPException(status_code=501, detail="config_builders unavailable")


@app.post("/api/config/generate/igp")
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


@app.post("/api/config/generate/batch")
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


@app.post("/api/config/preview-diff")
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
                user, password = _get_credentials()
                running = _fetch_config_via_ssh(scaler_id, mgmt_ip, user, password)
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
        user, password = _get_credentials()
        config = _fetch_config_via_ssh(scaler_id, mgmt_ip, user, password)
    if not config:
        raise HTTPException(status_code=404, detail=f"No config for {device_id}")
    hostname = device_id
    try:
        resolved = _resolve_device(device_id)
        hostname = resolved.get("hostname") or resolved.get("name") or device_id
    except Exception:
        pass
    return config, scaler_id, hostname


@app.post("/api/mirror/analyze")
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
        return {
            "source_summary": mirror.get_source_summary(),
            "target_summary": mirror.get_target_summary(),
            "smart_diff": smart_diff,
            "interface_map": mirror.interface_map,
            "requires_merge": mirror.requires_merge,
        }
    except HTTPException:
        raise
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"mirror_config unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/mirror/generate")
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
        if body.get("section_selection"):
            mirror.section_selection = body["section_selection"]
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


@app.post("/api/mirror/preview-diff")
def mirror_preview_diff(body: dict = None):
    """Preview diff of proposed mirrored config vs target running. Reuses preview_config_diff logic."""
    body = body or {}
    target_id = body.get("target_device_id") or ""
    proposed = body.get("config", "")
    ssh_host = body.get("ssh_host", "")
    if not target_id:
        raise HTTPException(status_code=400, detail="target_device_id required")
    return preview_config_diff({"device_id": target_id, "config": proposed, "ssh_host": ssh_host})


@app.post("/api/operations/delete-hierarchy")
def delete_hierarchy_op(body: dict = None):
    """Delete a config hierarchy from a device. dry_run=True for preview only."""
    body = body or {}
    device_id = body.get("device_id")
    hierarchy = body.get("hierarchy")
    dry_run = bool(body.get("dry_run", True))
    ssh_host = body.get("ssh_host", "")
    if not device_id or not hierarchy:
        raise HTTPException(status_code=400, detail="device_id and hierarchy required")
    try:
        mgmt_ip, scaler_id, via = _resolve_mgmt_ip(device_id, ssh_host)
        user, password = _get_credentials()
        from scaler.models import Device
        from scaler.wizard.push import delete_hierarchy, HIERARCHY_DELETE_COMMANDS
        if hierarchy not in HIERARCHY_DELETE_COMMANDS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown hierarchy. Valid: {', '.join(HIERARCHY_DELETE_COMMANDS.keys())}"
            )
        device = Device(
            id=device_id,
            hostname=device_id,
            ip=mgmt_ip,
            username=user,
            password=Device.encode_password(password),
        )
        config_text = _get_cached_config(device_id)
        success, message = delete_hierarchy(device, hierarchy, dry_run=dry_run, config_text=config_text, quiet=True)
        hier_config = HIERARCHY_DELETE_COMMANDS.get(hierarchy, {})
        commands = hier_config.get("commands", [hier_config.get("command")] if hier_config.get("command") else [])
        return {"success": success, "message": message, "commands_preview": commands}
    except HTTPException:
        raise
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"Scaler push module unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/operations/validate")
def validate_config(body: dict = None):
    """Validate DNOS config using CLIValidator and scale limits.
    Accepts {config: string, hierarchy?: string, check_limits?: bool, check_interface_order?: bool}.
    Returns {valid: bool, errors: [], warnings: [], suggestions: []}.
    """
    body = body or {}
    config_text = body.get("config", "")
    check_limits = body.get("check_limits", True)
    check_interface_order = body.get("check_interface_order", True)
    if not config_text or not config_text.strip():
        return {"valid": True, "errors": [], "warnings": [], "suggestions": []}
    try:
        from scaler.cli_validator import validate_generated_config
        result = validate_generated_config(
            config_text,
            check_limits=check_limits,
            check_interface_order=check_interface_order,
        )
        errors = []
        warnings = []
        suggestions = []
        for issue in result.issues:
            item = {
                "line_number": issue.line_number,
                "message": issue.message,
                "suggestion": issue.suggestion,
                "hierarchy": issue.hierarchy,
            }
            sev = issue.severity.value if hasattr(issue.severity, "value") else str(issue.severity)
            if sev == "error":
                errors.append(item)
            elif sev == "warning":
                warnings.append(item)
            else:
                suggestions.append(item)
        return {
            "valid": result.is_valid,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
        }
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"CLIValidator unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Push job state for SSE progress
# job_id -> {status, phase, message, percent, success, done, terminal_lines, terminal_cursor,
#            job_name, device_id, started_at, config_text, mode, dry_run}
_push_jobs = {}
_push_jobs_lock = __import__("threading").Lock()


def _build_job_name(body: dict, device_id: str, config_text: str) -> str:
    """Build a descriptive job name from push params."""
    name = body.get("job_name", "").strip()
    if name:
        return name
    lines = len(config_text.strip().split("\n"))
    mode_label = "Commit check" if body.get("dry_run") else (body.get("mode") or "merge").capitalize()
    return f"{lines} lines {mode_label} on {device_id}"


@app.post("/api/operations/push")
def push_config(body: dict = None):
    """Push config to device using ConfigPusher. Returns job_id for progress streaming."""
    import uuid
    from datetime import datetime

    body = body or {}
    device_id = body.get("device_id")
    config_text = body.get("config", "")
    mode = (body.get("mode") or "merge").lower()
    dry_run = bool(body.get("dry_run", False))
    ssh_host = body.get("ssh_host", "")
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    if not config_text or not config_text.strip():
        raise HTTPException(status_code=400, detail="config required")

    job_id = str(uuid.uuid4())
    job_name = _build_job_name(body, device_id, config_text)
    with _push_jobs_lock:
        _push_jobs[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "phase": "starting",
            "message": "",
            "percent": 0,
            "success": False,
            "done": False,
            "terminal_lines": [],
            "terminal_cursor": 0,
            "job_name": job_name,
            "device_id": device_id,
            "ssh_host": ssh_host,
            "started_at": datetime.utcnow().isoformat() + "Z",
            "config_text": config_text,
            "mode": mode,
            "dry_run": dry_run,
        }

    def _run_push():
        try:
            mgmt_ip, scaler_id, via = _resolve_mgmt_ip(device_id, ssh_host)
            user, password = _get_credentials()
            from scaler.models import Device
            from scaler.config_pusher import ConfigPusher

            device = Device(
                id=device_id,
                hostname=device_id,
                ip=mgmt_ip,
                username=user,
                password=Device.encode_password(password),
            )
            pusher = ConfigPusher()

            def _progress(msg: str, pct: int):
                with _push_jobs_lock:
                    if job_id in _push_jobs:
                        _push_jobs[job_id]["phase"] = msg
                        _push_jobs[job_id]["message"] = msg
                        _push_jobs[job_id]["percent"] = pct
                        _push_jobs[job_id]["status"] = "running"

            def _live_output(chunk: str):
                with _push_jobs_lock:
                    if job_id in _push_jobs:
                        _push_jobs[job_id]["terminal_lines"].append(chunk)

            if dry_run:
                success, message, channel, client = pusher.push_config_terminal_check_and_hold(
                    device, config_text,
                    progress_callback=_progress, live_output_callback=_live_output)
                with _push_jobs_lock:
                    if job_id in _push_jobs:
                        if success:
                            _push_jobs[job_id]["phase"] = "awaiting_decision"
                            _push_jobs[job_id]["message"] = "Commit check passed - Commit or Cancel"
                            _push_jobs[job_id]["percent"] = 70
                            _push_jobs[job_id]["status"] = "awaiting_decision"
                            _push_jobs[job_id]["awaiting_decision"] = True
                            _push_jobs[job_id]["check_passed"] = True
                            _push_jobs[job_id]["_channel"] = channel
                            _push_jobs[job_id]["_client"] = client
                            _push_jobs[job_id]["_pusher"] = pusher
                            _push_jobs[job_id]["_live_output"] = _live_output
                        else:
                            _push_jobs[job_id]["success"] = False
                            _push_jobs[job_id]["message"] = message
                            _push_jobs[job_id]["status"] = "failed"
                            _push_jobs[job_id]["done"] = True
                            _push_jobs[job_id]["check_passed"] = False
                _persist_job_if_done(job_id)
            else:
                success, message = pusher.push_config_terminal_paste(
                    device, config_text, dry_run=False,
                    progress_callback=_progress, live_output_callback=_live_output)
                with _push_jobs_lock:
                    if job_id in _push_jobs:
                        _push_jobs[job_id]["success"] = success
                        _push_jobs[job_id]["message"] = message
                        _push_jobs[job_id]["status"] = "completed" if success else "failed"
                        _push_jobs[job_id]["done"] = True
                _persist_job_if_done(job_id)
        except Exception as e:
            with _push_jobs_lock:
                if job_id in _push_jobs:
                    _push_jobs[job_id]["success"] = False
                    _push_jobs[job_id]["message"] = str(e)
                    _push_jobs[job_id]["status"] = "failed"
                    _push_jobs[job_id]["done"] = True
            _persist_job_if_done(job_id)

    import threading
    threading.Thread(target=_run_push, daemon=True).start()
    return {"job_id": job_id, "status": "started"}


@app.get("/api/config/push/progress/{job_id}")
def push_progress(job_id: str):
    """SSE stream for push progress. Includes terminal lines for live display."""
    from fastapi.responses import StreamingResponse
    import asyncio
    import json

    async def _event_stream():
        last_cursor = 0
        while True:
            with _push_jobs_lock:
                job = dict(_push_jobs.get(job_id, {}))
            lines = job.get("terminal_lines", [])
            new_lines = lines[last_cursor:]
            last_cursor = len(lines)
            job["terminal"] = new_lines
            job["terminal_full"] = lines[-500:] if len(lines) > 500 else lines
            sse_job = {k: v for k, v in job.items() if not k.startswith("_")}
            if job.get("done"):
                yield f"data: {json.dumps(sse_job)}\n\n"
                break
            yield f"data: {json.dumps(sse_job)}\n\n"
            await asyncio.sleep(0.5)

    return StreamingResponse(_event_stream(), media_type="text/event-stream")


@app.post("/api/operations/push/{job_id}/commit")
def push_commit(job_id: str):
    """Commit held config on the same SSH session. Call after dry_run push when check passed."""
    with _push_jobs_lock:
        job = _push_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if not job.get("awaiting_decision"):
            raise HTTPException(status_code=400, detail="Job is not awaiting commit decision")
        channel = job.get("_channel")
        client = job.get("_client")
        pusher = job.get("_pusher")
        live_output = job.get("_live_output")
        if not channel or not client or not pusher:
            raise HTTPException(status_code=400, detail="Held session lost")
        job["status"] = "committing"
        job["phase"] = "Committing..."
        del job["_channel"]
        del job["_client"]
        del job["_pusher"]
        del job["_live_output"]
        job["awaiting_decision"] = False

    success, message = pusher.commit_held_session(channel, client, live_output_callback=live_output)
    with _push_jobs_lock:
        if job_id in _push_jobs:
            _push_jobs[job_id]["success"] = success
            _push_jobs[job_id]["message"] = message
            _push_jobs[job_id]["status"] = "completed" if success else "failed"
            _push_jobs[job_id]["done"] = True
    _persist_job_if_done(job_id)
    return {"status": "completed" if success else "failed", "success": success, "message": message}


@app.post("/api/operations/push/{job_id}/cancel")
def push_cancel(job_id: str):
    """Cancel held config (discard candidate) and close SSH session."""
    with _push_jobs_lock:
        job = _push_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        channel = job.get("_channel")
        client = job.get("_client")
        pusher = job.get("_pusher")
        live_output = job.get("_live_output")
        if channel and client and pusher:
            job["status"] = "cancelling"
            job["phase"] = "Cancelling..."
            del job["_channel"]
            del job["_client"]
            del job["_pusher"]
            del job["_live_output"]
        job["awaiting_decision"] = False

    if channel and client and pusher:
        pusher.cancel_held_session(channel, client, live_output_callback=live_output)
    with _push_jobs_lock:
        if job_id in _push_jobs:
            _push_jobs[job_id]["success"] = False
            _push_jobs[job_id]["message"] = "Cancelled (config discarded)"
            _push_jobs[job_id]["status"] = "cancelled"
            _push_jobs[job_id]["done"] = True
            _push_jobs[job_id]["cancelled"] = True
    _persist_job_if_done(job_id)
    return {"status": "cancelled", "success": False, "message": "Cancelled"}


@app.post("/api/operations/push/{job_id}/cleanup")
def push_cleanup(job_id: str):
    """Cleanup dirty candidate on device after failed commit check. Connects fresh and runs cancel."""
    with _push_jobs_lock:
        job = _push_jobs.get(job_id)
        if not job:
            for h in _load_push_history():
                if h.get("job_id") == job_id:
                    job = h
                    break
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        device_id = job.get("device_id")
        ssh_host = job.get("ssh_host", "")
    if not device_id:
        raise HTTPException(status_code=400, detail="Job missing device_id")
    try:
        mgmt_ip, _, _ = _resolve_mgmt_ip(device_id, ssh_host)
        user, password = _get_credentials()
        from scaler.models import Device
        from scaler.config_pusher import ConfigPusher
        device = Device(
            id=device_id,
            hostname=device_id,
            ip=mgmt_ip,
            username=user,
            password=Device.encode_password(password),
        )
        pusher = ConfigPusher()
        success, message = pusher.cleanup_device_candidate(device)
        with _push_jobs_lock:
            if job_id in _push_jobs:
                _push_jobs[job_id]["message"] = (_push_jobs[job_id].get("message") or "") + " Cleanup: " + message
        return {"status": "ok" if success else "error", "success": success, "message": message}
    except Exception as e:
        return {"status": "error", "success": False, "message": str(e)}


_PUSH_HISTORY_PATH = Path.home() / ".scaler_push_history.json"
_MAX_HISTORY_JOBS = 50
_MAX_TERMINAL_LINES_IN_HISTORY = 200


def _load_push_history() -> list:
    """Load persisted push jobs from disk."""
    if not _PUSH_HISTORY_PATH.exists():
        return []
    try:
        with open(_PUSH_HISTORY_PATH) as f:
            data = json.load(f)
        return data.get("jobs", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    except Exception:
        return []


def _save_push_history(jobs: list):
    """Persist completed push jobs to disk. Cap at 50, truncate terminal to 200 lines."""
    to_save = []
    for j in jobs[: _MAX_HISTORY_JOBS]:
        jcopy = dict(j)
        lines = jcopy.get("terminal_lines", [])
        if len(lines) > _MAX_TERMINAL_LINES_IN_HISTORY:
            jcopy["terminal_lines"] = lines[-_MAX_TERMINAL_LINES_IN_HISTORY:]
        to_save.append(jcopy)
    try:
        _PUSH_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_PUSH_HISTORY_PATH, "w") as f:
            json.dump({"jobs": to_save}, f, indent=2)
    except Exception:
        pass


def _persist_job_if_done(job_id: str):
    """If job is done, add to history and persist."""
    with _push_jobs_lock:
        job = _push_jobs.get(job_id, {})
        if not job.get("done"):
            return
        jobs = _load_push_history()
        jobs.insert(0, dict(job))
        jobs = jobs[:_MAX_HISTORY_JOBS]
        _save_push_history(jobs)


@app.get("/api/operations/jobs")
def list_jobs():
    """List all jobs: active (in-memory) and recent (from disk)."""
    with _push_jobs_lock:
        active = [dict(j) for j in _push_jobs.values()]
    history = _load_push_history()
    seen = {j["job_id"] for j in active}
    for h in history:
        if h.get("job_id") not in seen:
            active.append(h)
            seen.add(h.get("job_id"))
    active.sort(key=lambda x: x.get("started_at", ""), reverse=True)
    return {"jobs": active[: _MAX_HISTORY_JOBS + 20]}


@app.get("/api/operations/jobs/{job_id}")
def get_job(job_id: str):
    """Get full job state including terminal output."""
    with _push_jobs_lock:
        job = _push_jobs.get(job_id)
    if job:
        return dict(job)
    for h in _load_push_history():
        if h.get("job_id") == job_id:
            return h
    raise HTTPException(status_code=404, detail="Job not found")


@app.post("/api/operations/jobs/{job_id}/retry")
def retry_job(job_id: str):
    """Re-submit job with same config. Returns new job_id."""
    job = None
    with _push_jobs_lock:
        job = _push_jobs.get(job_id)
    if not job:
        for h in _load_push_history():
            if h.get("job_id") == job_id:
                job = h
                break
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    config_text = job.get("config_text", "")
    device_id = job.get("device_id", "")
    if not config_text or not device_id:
        raise HTTPException(status_code=400, detail="Job missing config or device_id")
    body = {
        "device_id": device_id,
        "config": config_text,
        "mode": job.get("mode", "merge"),
        "dry_run": job.get("dry_run", False),
        "job_name": job.get("job_name", ""),
    }
    return push_config(body)


@app.delete("/api/operations/jobs/{job_id}")
def delete_job(job_id: str):
    """Remove job from history."""
    history = _load_push_history()
    history = [h for h in history if h.get("job_id") != job_id]
    _save_push_history(history)
    with _push_jobs_lock:
        _push_jobs.pop(job_id, None)
    return {"status": "deleted"}


@app.post("/api/operations/multihoming/compare")
def multihoming_compare(body: dict = None):
    """Compare multihoming config between two devices. Returns matching ESI count and per-device counts."""
    body = body or {}
    device_ids = body.get("device_ids") or []
    if len(device_ids) != 2:
        raise HTTPException(status_code=400, detail="Exactly 2 device_ids required")
    try:
        from scaler.wizard.parsers import parse_existing_multihoming
        configs = []
        for did in device_ids:
            try:
                mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(did, "")
                cfg = _get_cached_config(scaler_id)
                if not cfg:
                    user, password = _get_credentials()
                    cfg = _fetch_config_via_ssh(scaler_id, mgmt_ip, user, password)
            except Exception:
                cfg = ""
            configs.append(cfg or "")
        mh1 = parse_existing_multihoming(configs[0])
        mh2 = parse_existing_multihoming(configs[1])
        esi1 = set(mh1.values()) if isinstance(mh1, dict) else set()
        esi2 = set(mh2.values()) if isinstance(mh2, dict) else set()
        matching = len(esi1 & esi2)
        d1_only = len(esi1 - esi2)
        d2_only = len(esi2 - esi1)
        return {
            "device1": device_ids[0],
            "device2": device_ids[1],
            "matching": matching,
            "device1_only": d1_only,
            "device2_only": d2_only,
        }
    except ImportError:
        raise HTTPException(status_code=501, detail="Parser unavailable")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/operations/multihoming/sync")
def multihoming_sync(body: dict = None):
    """Sync multihoming between two devices. Pushes config via ConfigPusher. Returns job_id."""
    body = body or {}
    device_ids = body.get("device_ids") or []
    if len(device_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 device_ids required")
    esi_prefix = body.get("esi_prefix", "00:11:22:33:44")
    redundancy_mode = body.get("redundancy_mode", "single-active")
    match_neighbor = body.get("match_neighbor", True)
    try:
        mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(device_ids[0], "")
        config = _get_cached_config(scaler_id)
        if not config:
            user, password = _get_credentials()
            config = _fetch_config_via_ssh(scaler_id, mgmt_ip, user, password)
        from scaler.wizard.multihoming import generate_esi
        from scaler.wizard.parsers import parse_existing_multihoming
        mh = parse_existing_multihoming(config or "")
        if not mh:
            raise HTTPException(status_code=400, detail="No multihoming config on first device to sync")
        lines = ["network-services", "  multihoming"]
        for iface, esi in (mh.items() if isinstance(mh, dict) else []):
            lines.append(f"    interface {iface}")
            lines.append(f"      ethernet-segment")
            lines.append(f"        esi {esi}")
            lines.append(f"      !")
            lines.append(f"    !")
        lines.append("  !")
        lines.append("!")
        config_text = "\n".join(lines)
        import uuid
        from datetime import datetime
        job_id = str(uuid.uuid4())
        with _push_jobs_lock:
            _push_jobs[job_id] = {
                "job_id": job_id, "status": "pending", "phase": "starting", "message": "",
                "percent": 0, "success": False, "done": False, "terminal_lines": [],
                "terminal_cursor": 0, "job_name": f"MH sync {device_ids[0]} -> {device_ids[1]}",
                "device_id": device_ids[1], "started_at": datetime.utcnow().isoformat() + "Z",
                "config_text": config_text, "mode": "merge", "dry_run": False,
            }
        def _run():
            try:
                user, password = _get_credentials()
                target_ip, _, _ = _resolve_mgmt_ip(device_ids[1], "")
                from scaler.models import Device
                from scaler.config_pusher import ConfigPusher
                dev = Device(id=device_ids[1], hostname=device_ids[1], ip=target_ip,
                    username=user, password=Device.encode_password(password))
                pusher = ConfigPusher()
                ok, msg = pusher.push_config_merge(dev, config_text)
                with _push_jobs_lock:
                    if job_id in _push_jobs:
                        _push_jobs[job_id].update(success=ok, message=msg, status="completed" if ok else "failed", done=True, percent=100)
            except Exception as e:
                with _push_jobs_lock:
                    if job_id in _push_jobs:
                        _push_jobs[job_id].update(success=False, message=str(e), status="failed", done=True)
        import threading
        threading.Thread(target=_run, daemon=True).start()
        return {"job_id": job_id, "status": "started"}
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"Multihoming sync unavailable: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.api_route("/api/operations/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
def operations_stub(path: str):
    """Stub for operations - use scaler-wizard for full functionality."""
    raise HTTPException(
        status_code=501,
        detail="Operation not implemented in bridge. Use scaler-wizard CLI for scale up/down, mirror, multihoming sync, image upgrade."
    )


INVENTORY_FILE = Path(__file__).resolve().parent / "device_inventory.json"
DEVICE_INVENTORY_JSON = Path(__file__).resolve().parent / "device_inventory.json"


def _find_cached_config_by_ip(ssh_host: str) -> tuple:
    """Search SCALER db/configs for a device matching this SSH IP. Returns (device_id, config_text)."""
    configs_dir = Path(SCALER_ROOT) / "db" / "configs"
    if not configs_dir.exists():
        return None, None
    for dev_dir in configs_dir.iterdir():
        if not dev_dir.is_dir():
            continue
        ops_file = dev_dir / "operational.json"
        if ops_file.exists():
            try:
                ops = json.loads(ops_file.read_text())
                if ops.get("mgmt_ip", "").strip() == ssh_host:
                    config_file = dev_dir / "running.txt"
                    config = config_file.read_text() if config_file.exists() else None
                    return dev_dir.name, config
            except Exception:
                continue
    return None, None


def _find_inventory_device(device_id: str, ssh_host: str = "") -> dict:
    """Find device in device_inventory.json by label, hostname, IP, or serial."""
    if not DEVICE_INVENTORY_JSON.exists():
        return {}
    try:
        inv_data = json.loads(DEVICE_INVENTORY_JSON.read_text())
        devices = inv_data.get("devices", {})
    except Exception:
        return {}

    did_lower = device_id.lower()
    for key, dev in devices.items():
        k = key.lower()
        dev_ip = (dev.get("mgmt_ip") or dev.get("ip") or "").strip()
        if ssh_host and dev_ip == ssh_host:
            return dev
        if k == did_lower:
            return dev
    for key, dev in devices.items():
        k = key.lower()
        dev_hostname = (dev.get("hostname") or "").lower()
        dev_serial = (dev.get("serial") or "").lower()
        if did_lower and (did_lower in k or k in did_lower or
                          did_lower == dev_hostname or did_lower == dev_serial):
            return dev
    return {}


def _get_device_context(device_id: str, live: bool = False, ssh_host: str = "") -> dict:
    """Build unified device context for wizard suggestions.
    
    Resolution order:
    1. If ssh_host provided, use it to find cached config and inventory by IP
    2. Try _resolve_device(device_id) via discovery API
    3. Fuzzy match in device_inventory.json and SCALER db/configs
    """
    from datetime import datetime
    ctx = {
        "device_id": device_id,
        "interfaces": {
            "physical": [],
            "bundle": [],
            "subinterface": [],
            "pwhe": [],
            "free_physical": [],
        },
        "lldp": [],
        "config_summary": {},
        "wan_interfaces": [],
        "igp": {"protocol": "", "area": "", "interfaces": []},
        "services": {"fxc_count": 0, "vrf_count": 0, "next_evi": 1000},
        "next_bundle_number": 1,
        "system_type": "",
        "cached": not live,
        "timestamp": datetime.now().isoformat(),
        "resolved_via": "",
        "loopbacks": [],
        "vrfs": [],
        "bridge_domains": [],
        "flowspec_policies": [],
        "routing_policies": {},
        "bgp_peers": [],
        "multihoming": {},
        "platform_limits": {},
    }

    try:
        mgmt_ip, scaler_device_id, via = _resolve_mgmt_ip(device_id, ssh_host)
        ctx["resolved_via"] = via
        ctx["resolved_ip"] = mgmt_ip
        ctx["mgmt_ip"] = mgmt_ip
        ctx["ip"] = mgmt_ip
    except Exception:
        mgmt_ip = ""
        scaler_device_id = device_id
        ctx["resolved_via"] = "failed"

    hostname = device_id
    serial = ""
    try:
        resolved = _resolve_device(device_id)
        hostname = resolved.get("hostname") or resolved.get("name") or device_id
        serial = resolved.get("serial", "")
    except Exception:
        pass

    config = _get_cached_config(scaler_device_id)
    if not config and scaler_device_id != device_id:
        config = _get_cached_config(device_id)
    if not config and hostname != device_id:
        config = _get_cached_config(hostname)

    if (live or not config) and mgmt_ip:
        try:
            user, password = _get_credentials()
            config = _fetch_config_via_ssh(scaler_device_id, mgmt_ip, user, password)
            ctx["cached"] = False
            ctx["resolved_via"] = f"live_ssh:{mgmt_ip}"
        except Exception:
            pass

    inv_dev = _find_inventory_device(device_id, mgmt_ip)
    if not inv_dev and ssh_host:
        inv_dev = _find_inventory_device(ssh_host, mgmt_ip)
    if inv_dev:
        ctx["system_type"] = inv_dev.get("system_type", "")

    lldp_raw = inv_dev.get("lldp_neighbors", [])
    for n in lldp_raw:
        ctx["lldp"].append({
            "local": n.get("local_interface", n.get("interface", "")),
            "neighbor": n.get("neighbor_name", n.get("neighbor_device", n.get("neighbor", ""))),
            "remote": n.get("neighbor_interface", n.get("neighbor_port", n.get("remote_port", ""))),
        })

    if not ctx["lldp"]:
        for try_name in [hostname, serial, device_id]:
            if not try_name:
                continue
            try:
                url = f"{DISCOVERY_API}/api/device/{urllib.parse.quote(try_name)}/lldp"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read())
                for n in data.get("neighbors", []):
                    ctx["lldp"].append({
                        "local": n.get("interface", ""),
                        "neighbor": n.get("neighbor", ""),
                        "remote": n.get("remote_port", ""),
                    })
                if ctx["lldp"]:
                    break
            except Exception:
                continue

    if not ctx["lldp"] and mgmt_ip and live:
        try:
            user, password = _get_credentials()
            import paramiko
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(mgmt_ip, username=user, password=password, timeout=10, banner_timeout=10)
            channel = client.invoke_shell()
            import time
            time.sleep(1)
            while channel.recv_ready():
                channel.recv(65535)
            channel.send("show lldp neighbors | no-more\r\n")
            time.sleep(3)
            output = ""
            start = time.time()
            while time.time() - start < 8:
                if channel.recv_ready():
                    output += channel.recv(65535).decode("utf-8", errors="replace")
                time.sleep(0.3)
            client.close()
            for line in output.split("\n"):
                if "|" in line and "Local" not in line and "Interface" not in line and "---" not in line:
                    parts = [p.strip() for p in line.split("|") if p.strip()]
                    if len(parts) >= 3:
                        ctx["lldp"].append({"local": parts[0], "neighbor": parts[1], "remote": parts[2]})
        except Exception:
            pass

    if not ctx["lldp"] and mgmt_ip:
        ops_path = Path(SCALER_ROOT) / "db" / "configs" / scaler_device_id / "operational.json"
        if ops_path.exists():
            try:
                ops = json.loads(ops_path.read_text())
                for n in ops.get("lldp_neighbors", []):
                    ctx["lldp"].append({
                        "local": n.get("local_interface", n.get("interface", "")),
                        "neighbor": n.get("neighbor_name", n.get("neighbor", "")),
                        "remote": n.get("neighbor_interface", n.get("remote_port", "")),
                    })
            except Exception:
                pass

    iface_details = inv_dev.get("interface_details", {})

    if config:
        try:
            from scaler.wizard.interfaces import _get_all_interfaces_from_config, categorize_interfaces_by_type, get_bundle_members
            from scaler.wizard.parsers import get_wan_interfaces, parse_existing_evpn_services

            all_ifaces = _get_all_interfaces_from_config(config)
            cats = categorize_interfaces_by_type(all_ifaces)

            for name in cats.get("physical", []):
                det = iface_details.get(name, {})
                ctx["interfaces"]["physical"].append({
                    "name": name,
                    "speed": (det.get("speed") or "").strip(",") or "",
                    "bundle": det.get("bundle", ""),
                    "oper": "up" if any(s.get("oper") == "up" for s in det.get("sub_interfaces", [{}])) else "",
                })

            max_bundle_num = 0
            for name in cats.get("bundle", []):
                try:
                    members = get_bundle_members(name, config)
                except Exception:
                    members = []
                ctx["interfaces"]["bundle"].append({"name": name, "members": members})
                m = re.search(r"bundle-?(?:ether)?(\d+)", name, re.I)
                if m:
                    max_bundle_num = max(max_bundle_num, int(m.group(1)))
            ctx["next_bundle_number"] = max_bundle_num + 1

            for name in (cats.get("bundle_subif", []) + cats.get("physical_subif", [])):
                ctx["interfaces"]["subinterface"].append({"name": name, "vlan": name.split(".")[-1] if "." in name else ""})

            for name in cats.get("pwhe", []):
                ctx["interfaces"]["pwhe"].append({"name": name})

            used = set()
            for b in ctx["interfaces"]["bundle"]:
                used.update(b.get("members", []))
            for p in ctx["interfaces"]["physical"]:
                if p["name"] not in used and not p.get("bundle"):
                    ctx["interfaces"]["free_physical"].append(p["name"])

            ctx["wan_interfaces"] = get_wan_interfaces(config)

            protocols = config
            if "isis" in protocols.lower():
                ctx["igp"]["protocol"] = "isis"
            elif "ospf" in protocols.lower():
                ctx["igp"]["protocol"] = "ospf"
            ctx["igp"]["interfaces"] = list(ctx["wan_interfaces"])

            ctx["config_summary"] = _build_config_summary(config)

            evpn = parse_existing_evpn_services(config)
            fxc = evpn.get("fxc", [])
            vpls = evpn.get("vpls", [])
            ctx["services"]["fxc_count"] = len(fxc)
            ctx["services"]["vrf_count"] = len(evpn.get("mpls", []))
            max_evi = 999
            for s in fxc + vpls:
                rd = s.get("rd", "")
                if rd and ":" in rd:
                    try:
                        max_evi = max(max_evi, int(rd.split(":")[-1]))
                    except ValueError:
                        pass
            ctx["services"]["next_evi"] = max_evi + 1

            from scaler.wizard.parsers import (
                parse_vrf_instances,
                parse_l2vpn_bridge_domains,
                parse_all_routing_policies,
                parse_existing_multihoming,
            )
            ctx["vrfs"] = parse_vrf_instances(config)
            ctx["bridge_domains"] = parse_l2vpn_bridge_domains(config)
            ctx["routing_policies"] = parse_all_routing_policies(config)
            ctx["multihoming"] = parse_existing_multihoming(config)

            flp = re.findall(r"flowspec-local-policies.*?policy\s+(\S+)", config, re.DOTALL)
            ctx["flowspec_policies"] = list(dict.fromkeys(flp))

            nbr_pattern = re.compile(r"neighbor\s+(\d+\.\d+\.\d+\.\d+)\s*\n\s*remote-as\s+(\d+)")
            seen = set()
            for m in nbr_pattern.finditer(config):
                ip_as = (m.group(1), m.group(2))
                if ip_as not in seen:
                    seen.add(ip_as)
                    ctx["bgp_peers"].append({"ip": m.group(1), "remote_as": int(m.group(2))})

            lo_pattern = re.compile(r"^\s*(lo\d+)\s*$.*?ipv4-address\s+(\S+)", re.MULTILINE | re.DOTALL)
            for m in lo_pattern.finditer(config):
                ctx["loopbacks"].append({"name": m.group(1), "ip": m.group(2)})

            ctx["platform_limits"] = _load_limits(device_id)

        except ImportError as e:
            ctx["config_summary"] = {"error": str(e)}
        except Exception as e:
            ctx["config_summary"] = {"error": str(e)}

    return ctx


@app.get("/api/devices/{device_id}/context")
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


@app.post("/api/devices/{device_id}/test")
def test_device_connection(device_id: str, ssh_host: str = ""):
    """Test SSH connectivity to a device. Uses central _resolve_mgmt_ip."""
    mgmt_ip, scaler_id, via = _resolve_mgmt_ip(device_id, ssh_host)
    try:
        user, password = _get_credentials()
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(mgmt_ip, username=user, password=password, timeout=8, banner_timeout=8)
        client.close()
        return {"status": "ok", "message": f"Connection OK ({mgmt_ip}, via {via})"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"SSH to {mgmt_ip} failed: {e}")


@app.post("/api/devices/discover")
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


@app.get("/api/health")
def health():
    """Health check."""
    return {"status": "ok", "service": "scaler-bridge"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8766)
