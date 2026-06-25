#!/usr/bin/env python3
"""
Simple API server for running DNAAS discovery from the web UI.
Run this alongside your web server.
"""

import subprocess
import threading
import json
import os
import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import queue

# Pre-import MCP client in main thread (signal.SIGALRM only works in main thread)
try:
    from scaler.network_mapper_client import NetworkMapperClient, MCP_AVAILABLE
    print(f"[Init] MCP client loaded: available={MCP_AVAILABLE}")
except Exception as e:
    MCP_AVAILABLE = False
    print(f"[Init] MCP client import failed: {e}")

SCRIPT_DIR = Path(__file__).parent
# Use main discovery script which supports --multi-bd flag
DISCOVERY_SCRIPT = SCRIPT_DIR / "dnaas_path_discovery.py"
OUTPUT_DIR = SCRIPT_DIR / "output"
DNOS_MCP_CLI = Path(os.path.expanduser(os.environ.get(
    "DNOS_MCP_CLI",
    "~/.cursor/tools/dnos_mcp.py",
)))
DNOS_MCP_DISCOVERY_ENABLED = (
    os.environ.get("DNAAS_DNOS_MCP_DISCOVERY", "1").strip().lower()
    not in {"0", "false", "no", "off"}
)

# Salvage-tolerant reader / atomic writer for SCALER operational.json.
# Imported lazily inside helpers so the module can still load when the
# topology code is run from outside the topology package directory.
def _safe_read_ops(path):
    try:
        from routes._ops_writer import read_ops as _r
        return _r(Path(path))
    except Exception:
        try:
            with open(path) as fh:
                return json.load(fh)
        except Exception:
            return {}


def _safe_update_ops(path, mutator, create_if_missing=True):
    try:
        from routes._ops_writer import update_ops as _u
        return _u(Path(path), mutator, create_if_missing=create_if_missing)
    except Exception:
        return False, None
# Per-user output isolation:
#   <OUTPUT_DIR>/users/<username>/  -> authenticated user (X-User header)
#   <OUTPUT_DIR>/global/            -> unauthenticated callers (no X-User)
#
# /api/discovery/start spawns the discovery script with DNAAS_OUTPUT_DIR set
# to the caller's per-user dir. /api/discovery/list and /api/discovery/file/*
# (and the multi-bd equivalents) only return files that live under the
# caller's per-user dir, so user A's discovery results never appear in user
# B's listing or downloads.
USERS_OUTPUT_ROOT = OUTPUT_DIR / "users"
GLOBAL_OUTPUT_DIR = OUTPUT_DIR / "global"
# Inheritor for the legacy global ``output/*.json`` discovery dump.
# Pre-username-migration this was "yarel"; post-migration the same human
# logs in as "yor". The default accepts either so the one-shot legacy
# move still finds a home regardless of which DB row first triggers it.
_LEGACY_OUTPUT_OWNERS_DEFAULT = ("yor", "yarel")
_legacy_output_owner_env = (os.environ.get("LEGACY_OUTPUT_OWNER") or "").strip()
LEGACY_OUTPUT_OWNERS = (
    tuple(u.strip() for u in _legacy_output_owner_env.split(",") if u.strip())
    if _legacy_output_owner_env
    else _LEGACY_OUTPUT_OWNERS_DEFAULT
)
LEGACY_OUTPUT_OWNER = LEGACY_OUTPUT_OWNERS[0]  # back-compat alias for old refs
_legacy_output_migrated = False


def _safe_user_segment(name: str) -> str:
    """Sanitize a username so it is safe to use as a single path component."""
    if not name:
        return ""
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name)


def _user_output_dir(username: str) -> Path:
    """Return the per-user output directory, creating it on demand.

    Anonymous callers (no X-User header) get the shared GLOBAL_OUTPUT_DIR so
    legacy CLI / direct integrations keep working, but they only see files
    inside that bucket and never another user's per-user dir.
    """
    safe = _safe_user_segment(username)
    if not safe or safe in ("default", "unknown"):
        target = GLOBAL_OUTPUT_DIR
    else:
        target = USERS_OUTPUT_ROOT / safe
    target.mkdir(parents=True, exist_ok=True)
    return target


def _maybe_migrate_legacy_output():
    """Move pre-multiuser discovery files from OUTPUT_DIR/*.json into the
    founder's per-user dir on first request, so they don't leak into every
    user's listing.
    """
    global _legacy_output_migrated
    if _legacy_output_migrated:
        return
    _legacy_output_migrated = True
    try:
        if not OUTPUT_DIR.exists():
            return
        target = _user_output_dir(LEGACY_OUTPUT_OWNER)
        moved = 0
        for entry in OUTPUT_DIR.iterdir():
            if entry.is_file() and entry.suffix.lower() in {".json", ".txt", ".xlsx"}:
                dst = target / entry.name
                if dst.exists():
                    continue
                try:
                    entry.rename(dst)
                    moved += 1
                except Exception:
                    pass
        if moved:
            print(f"[discovery_api] Migrated {moved} legacy output files -> {target}")
    except Exception as e:
        print(f"[discovery_api] Legacy output migration FAILED: {e}")


def _request_owner(handler) -> str:
    """Extract the X-User header forwarded by serve.py. Empty string for
    unauthenticated callers (mapped to the shared global bucket)."""
    return (handler.headers.get("X-User") or "").strip()


def _owner_or_global(owner: str) -> str:
    owner = (owner or "").strip()
    return owner if owner else "global"


def _inventory_path() -> Path:
    """Resolve device_inventory.json from env / co-located fallback.

    Priority:
      1. $TOPOLOGY_INVENTORY_PATH    (full path override)
      2. /home/dn/CURSOR/device_inventory.json (legacy live deploy)
      3. <script_dir>/device_inventory.json    (worktree fallback)
    """
    env_path = os.environ.get('TOPOLOGY_INVENTORY_PATH', '').strip()
    if env_path:
        return Path(env_path).expanduser()
    legacy = Path('/home/dn/CURSOR/device_inventory.json')
    if legacy.exists():
        return legacy
    return SCRIPT_DIR / 'device_inventory.json'

# Store running jobs
jobs = {}
job_counter = 0
job_lock = threading.Lock()
job_processes = {}  # Store subprocess handles for cancellation
lldp_device_current = {}
lldp_device_queues = {}

# Network Mapper jobs (separate from discovery jobs)
nm_jobs = {}
nm_job_counter = 0
nm_job_lock = threading.Lock()

# MCP client singleton (reused across requests to avoid repeated SSE handshakes)
_mcp_client = None
_mcp_client_lock = threading.Lock()
_server_start_time = time.time()


def _get_mcp_client():
    """Get or create the shared NetworkMapperClient instance (thread-safe)."""
    global _mcp_client
    import sys
    if '/home/dn/SCALER' not in sys.path:
        sys.path.insert(0, '/home/dn/SCALER')
    with _mcp_client_lock:
        if _mcp_client is None:
            from scaler.network_mapper_client import NetworkMapperClient
            _mcp_client = NetworkMapperClient()
        return _mcp_client


def _reset_mcp_client():
    """Reset the MCP client (call when connection is known dead)."""
    global _mcp_client
    with _mcp_client_lock:
        if _mcp_client is not None:
            try:
                _mcp_client.close()
            except Exception:
                pass
            _mcp_client = None
            print("[MCP] Client reset -- will reconnect on next call")


def _mcp_call(fn_name, *args, **kwargs):
    """Execute an MCP client method with auto-reset on failure.

    NetworkMapperClient now serializes all MCP calls on a dedicated event
    loop thread, so the 'cancel scope in different task' crash cannot happen.
    This wrapper still provides retry-with-reset for network-level failures.
    """
    for attempt in range(2):
        try:
            nm = _get_mcp_client()
            method = getattr(nm, fn_name)
            return method(*args, **kwargs)
        except (TimeoutError, OSError, ConnectionError) as e:
            if attempt == 0:
                print(f"[MCP] {fn_name} failed ({e}), resetting client and retrying...")
                _reset_mcp_client()
            else:
                print(f"[MCP] {fn_name} failed after retry: {e}")
                raise
        except Exception as e:
            if attempt == 0:
                print(f"[MCP] {fn_name} error ({e}), resetting client and retrying...")
                _reset_mcp_client()
            else:
                raise


def _call_dnos_config_mcp(tool_name: str, arguments: dict, timeout: int = 45) -> dict:
    """Call dnos-config through the documented MCP CLI fallback.

    discovery_api runs outside Cursor's native CallMcpTool surface, so the
    supported boundary is ~/.cursor/tools/dnos_mcp.py. Do not import
    dnos_config_mcp internals here.
    """
    if not DNOS_MCP_CLI.exists():
        raise RuntimeError(f"dnos-config MCP CLI not found: {DNOS_MCP_CLI}")
    cmd = [
        "python3",
        str(DNOS_MCP_CLI),
        tool_name,
        json.dumps(arguments or {}),
    ]
    proc = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(detail or f"{tool_name} failed with exit {proc.returncode}")
    output = (proc.stdout or "").strip()
    if not output:
        raise RuntimeError(f"{tool_name} returned empty output")
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{tool_name} returned non-JSON output: {output[:200]}") from exc


_DNOS_MCP_BD_COLORS = [
    "#3498db", "#e74c3c", "#2ecc71", "#9b59b6", "#f39c12",
    "#1abc9c", "#e91e63", "#00bcd4", "#ff5722", "#8bc34a",
]


def _dnaas_mcp_role(name: str) -> str:
    upper = (name or "").upper()
    if "SUPERSPINE" in upper or "SUPER-SPINE" in upper:
        return "SUPERSPINE"
    if "SPINE" in upper:
        return "SPINE"
    if "LEAF" in upper:
        return "LEAF"
    if "SPIRENT" in upper or "IXIA" in upper or "TEST" in upper:
        return "TEST_EQUIPMENT"
    return "PE"


def _dnaas_mcp_device_style(role: str) -> tuple:
    if role == "SUPERSPINE":
        return "#c0392b", "server"
    if role == "SPINE":
        return "#9b59b6", "server"
    if role == "LEAF":
        return "#e67e22", "server"
    if role == "TEST_EQUIPMENT":
        return "#16a085", "server"
    return "#3498db", "classic"


def _dnaas_mcp_vlan_from_link(link: dict) -> int:
    for key in ("vlan", "global_vlan", "vlan_id"):
        try:
            if link.get(key) is not None:
                return int(link.get(key))
        except Exception:
            pass
    for encap_key in ("wire_encap_out", "bd_encap_in", "starting_bd_encap"):
        encap = link.get(encap_key) or {}
        try:
            if encap.get("outer") is not None:
                return int(encap.get("outer"))
        except Exception:
            pass
    return None


def _dnos_mcp_walk_to_topology(payload: dict, source_name: str) -> dict:
    """Convert dnos_dnaas_walk_from_dut JSON into the existing DNAAS canvas shape."""
    if not payload or not payload.get("ok"):
        raise ValueError("dnos-config walk returned no usable data")

    source_label = payload.get("dut") or source_name
    devices = {}
    links = []
    bridge_domains = {}
    device_bd_mapping = {}
    device_index_meta = payload.get("device_index_meta") or {}

    def add_device(name: str):
        if not name or name in devices:
            return
        role = _dnaas_mcp_role(name)
        color, visual_style = _dnaas_mcp_device_style(role)
        meta = device_index_meta.get(name) or {}
        dev = {
            "name": name,
            "role": role,
            "color": color,
            "visualStyle": visual_style,
            "sshConfig": None,
        }
        ip = meta.get("device_ip") or meta.get("ip") or ""
        if role in {"SUPERSPINE", "SPINE", "LEAF"}:
            dev["sshConfig"] = {
                "host": ip or name,
                "hostBackup": name,
                "user": "sisaev",
                "password": "Drive1234!",
            }
        elif role == "PE":
            dev["sshConfig"] = {
                "host": ip or "",
                "hostBackup": name,
                "user": "dnroot",
                "password": "dnroot",
            }
        devices[name] = dev

    def add_bd(name: str, vlan=None):
        if not name:
            return
        if name not in bridge_domains:
            bridge_domains[name] = {
                "name": name,
                "type": "DNAAS_MCP",
                "vlan": vlan,
                "color": _DNOS_MCP_BD_COLORS[len(bridge_domains) % len(_DNOS_MCP_BD_COLORS)],
                "source": "dnos-config-mcp",
            }
        elif bridge_domains[name].get("vlan") is None and vlan is not None:
            bridge_domains[name]["vlan"] = vlan

    def map_bd(device: str, bd_name: str):
        if not device or not bd_name:
            return
        entry = device_bd_mapping.setdefault(device, {
            "bridge_domains": [],
            "bd_count": 0,
            "device_type": _dnaas_mcp_role(device),
        })
        if bd_name not in entry["bridge_domains"]:
            entry["bridge_domains"].append(bd_name)
            entry["bd_count"] = len(entry["bridge_domains"])

    def add_link(from_dev: str, to_dev: str, from_if: str, to_if: str,
                 bd_name: str, vlan=None, is_termination=False):
        if not from_dev or not to_dev:
            return
        add_device(from_dev)
        add_device(to_dev)
        add_bd(bd_name, vlan)
        map_bd(from_dev, bd_name)
        map_bd(to_dev, bd_name)
        links.append({
            "from": from_dev,
            "to": to_dev,
            "from_if": from_if or "",
            "to_if": to_if or "",
            "bd_name": bd_name or "",
            "global_vlan": vlan,
            "is_termination": bool(is_termination),
        })

    add_device(source_label)

    for ac in payload.get("dut_acs") or []:
        lldp = ac.get("lldp_to_dnaas") or {}
        dnaas_ac = ac.get("dnaas_ac") or {}
        leaf = dnaas_ac.get("device") or lldp.get("neighbor_device")
        bd_name = dnaas_ac.get("bd_name") or ac.get("bd_chain_id", "").split("::")[-1]
        chain = (payload.get("bd_chains") or {}).get(ac.get("bd_chain_id") or "") or {}
        vlan = None
        for hop in chain.get("hops") or []:
            vlan = _dnaas_mcp_vlan_from_link(hop)
            if vlan is not None:
                break
        add_link(
            source_label,
            leaf,
            ac.get("dut_interface") or "",
            lldp.get("neighbor_port") or dnaas_ac.get("interface") or "",
            bd_name,
            vlan,
            is_termination=True,
        )

    for chain in (payload.get("bd_chains") or {}).values():
        chain_bd = chain.get("bd_name") or ""
        for hop in chain.get("hops") or []:
            next_info = hop.get("lldp_to_next") or {}
            add_link(
                hop.get("device") or chain.get("starting_leaf"),
                next_info.get("neighbor_device"),
                hop.get("uplink_ac") or "",
                next_info.get("neighbor_port") or "",
                hop.get("bd_name") or chain_bd,
                _dnaas_mcp_vlan_from_link(hop),
            )
        if chain.get("reaches_spirent_ingress"):
            spirent_leaf = chain.get("terminus") or payload.get("spirent_ingress_leaf")
            add_link(
                spirent_leaf,
                "Spirent 6/13",
                "ge100-0/0/15",
                "//100.64.3.238/6/13",
                chain_bd,
                _dnaas_mcp_vlan_from_link(chain),
                is_termination=True,
            )

    tier_y = {
        "SUPERSPINE": 220,
        "SPINE": 520,
        "LEAF": 820,
        "PE": 1120,
        "TEST_EQUIPMENT": 1120,
    }
    tier_order = ["SUPERSPINE", "SPINE", "LEAF", "PE", "TEST_EQUIPMENT"]
    device_ids = {}
    objects = []
    idx = 0
    for role in tier_order:
        names = sorted([name for name, info in devices.items() if info["role"] == role])
        if not names:
            continue
        spacing = 420 if len(names) <= 5 else 320
        start_x = 1200 - ((len(names) - 1) * spacing / 2)
        for pos, name in enumerate(names):
            info = devices[name]
            dev_id = f"device_{idx}"
            device_ids[name] = dev_id
            obj = {
                "id": dev_id,
                "type": "device",
                "deviceType": "router",
                "x": start_x + pos * spacing,
                "y": tier_y.get(role, 900),
                "radius": 50,
                "rotation": 0,
                "color": info["color"],
                "label": name,
                "locked": False,
                "visualStyle": info["visualStyle"],
            }
            if info.get("sshConfig"):
                obj["sshConfig"] = info["sshConfig"]
            objects.append(obj)
            idx += 1

    link_idx = 0
    for link in links:
        dev1 = device_ids.get(link["from"])
        dev2 = device_ids.get(link["to"])
        if not dev1 or not dev2:
            continue
        bd = bridge_domains.get(link["bd_name"], {})
        vlan = link.get("global_vlan")
        vlan_text = str(vlan) if vlan is not None else ""
        objects.append({
            "id": f"link_{link_idx}",
            "type": "link",
            "device1": dev1,
            "device2": dev2,
            "color": bd.get("color") or "#2c3e50",
            "style": "solid",
            "width": 2,
            "_bdName": link.get("bd_name") or "",
            "linkDetails": {
                "interfaceA": link.get("from_if") or "",
                "interfaceB": link.get("to_if") or "",
                "physicalInterfaceA": (link.get("from_if") or "").split(".")[0],
                "physicalInterfaceB": (link.get("to_if") or "").split(".")[0],
                "description": f"{link['from']} <-> {link['to']} ({link.get('bd_name') or 'DNAAS'})",
                "bd_name": link.get("bd_name") or "",
                "bd_type": bd.get("type") or "DNAAS_MCP",
                "vlan_id": vlan,
                "global_vlan": vlan,
                "vlanIdA": vlan_text,
                "vlanIdB": vlan_text,
                "is_termination": bool(link.get("is_termination")),
                "source": "dnos-config-mcp",
            },
        })
        link_idx += 1

    return {
        "version": "1.0",
        "objects": objects,
        "metadata": {
            "name": "DNAAS dnos-config MCP Discovery",
            "created": datetime.now().isoformat(),
            "source": source_label,
            "source_backend": "dnos-config-mcp",
            "bridge_domains": list(bridge_domains.values()),
            "device_bd_mapping": device_bd_mapping,
            "view_mode": "combined",
            "dnos_config_mcp": {
                "tool": "dnos_dnaas_walk_from_dut",
                "summary": payload.get("summary") or {},
                "cache": payload.get("cache") or {},
                "spirent_ingress_leaf": payload.get("spirent_ingress_leaf"),
            },
        },
    }


def _try_dnos_mcp_discovery(serial: str, owner_dir: Path, prefix: str, log=None) -> Path:
    """Try cached/config-derived dnos-config DNAAS discovery; return saved JSON path."""
    if not DNOS_MCP_DISCOVERY_ENABLED:
        raise RuntimeError("dnos-config MCP discovery disabled by DNAAS_DNOS_MCP_DISCOVERY")
    if not serial:
        raise RuntimeError("missing source device")

    def emit(msg):
        if log:
            log(msg)

    emit("[INFO] Trying dnos-config MCP DNAAS discovery...")
    payload = _call_dnos_config_mcp(
        "dnos_dnaas_walk_from_dut",
        {
            "device_name": serial,
            "caller_intent": "general",
            "freshness": "prefer_cached",
            "format": "json",
        },
        timeout=int(os.environ.get("DNAAS_DNOS_MCP_TIMEOUT", "75")),
    )
    summary = payload.get("summary") or {}
    if not payload.get("ok") or int(summary.get("total_dut_acs") or 0) <= 0:
        raise RuntimeError(payload.get("error") or payload.get("errors") or "no DUT ACs returned")
    topology = _dnos_mcp_walk_to_topology(payload, serial)
    filename = f"{prefix}_mcp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path = owner_dir / filename
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(topology, fh, indent=2)
    emit(
        "[OK] dnos-config MCP discovery saved "
        f"{filename}: {summary.get('reachable', 0)}/{summary.get('total_dut_acs', 0)} reachable ACs"
    )
    return out_path


def _nm_cleanup_old_jobs():
    """Remove completed nm_jobs older than 30 minutes."""
    cutoff = time.time() - 1800
    with nm_job_lock:
        to_remove = [jid for jid, j in nm_jobs.items()
                     if j.get('status') in ('completed', 'cancelled', 'failed')
                     and j.get('created_at', 0) < cutoff]
        for jid in to_remove:
            nm_jobs.pop(jid, None)


def _cleanup_old_discovery_jobs():
    """Remove completed DNAAS discovery jobs older than 30 minutes."""
    cutoff = time.time() - 1800
    with job_lock:
        to_remove = [jid for jid, j in jobs.items()
                     if j.get('status') in ('completed', 'failed', 'cancelled')
                     and j.get('created_at', 0) < cutoff]
        for jid in to_remove:
            jobs.pop(jid, None)


_job_store_lock = threading.Lock()


def _job_store_path(owner: str) -> Path:
    """Per-user durable discovery job DB path."""
    owner = _owner_or_global(owner)
    if owner == "global":
        GLOBAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        return GLOBAL_OUTPUT_DIR / "discovery_jobs.db"
    try:
        from api.auth.user_store import user_store
        return user_store.user_data_path(owner, "discovery_jobs.db")
    except Exception:
        # Fallback for standalone discovery_api runs outside the package setup.
        fallback = USERS_OUTPUT_ROOT / _safe_user_segment(owner)
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback / "discovery_jobs.db"


def _open_job_store(owner: str):
    db_path = _job_store_path(owner)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            owner TEXT NOT NULL,
            type TEXT NOT NULL,
            device_key TEXT,
            status TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            payload TEXT NOT NULL
        )
    """)
    return conn


def _serializable_job(job: dict) -> dict:
    out = {}
    for key, value in (job or {}).items():
        if key.startswith("_"):
            continue
        try:
            json.dumps(value)
            out[key] = value
        except Exception:
            out[key] = str(value)
    out["updated_at"] = time.time()
    return out


def _persist_job(job_id: str, job: dict):
    if not job_id or not job:
        return
    owner = _owner_or_global(job.get("owner", "global"))
    payload = _serializable_job(job)
    with _job_store_lock:
        try:
            conn = _open_job_store(owner)
            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO jobs
                      (job_id, owner, type, device_key, status, created_at, updated_at, payload)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job_id,
                        owner,
                        payload.get("type", "unknown"),
                        payload.get("device_key") or payload.get("resolved_target") or payload.get("serial") or "",
                        payload.get("status", "unknown"),
                        float(payload.get("created_at") or time.time()),
                        float(payload.get("updated_at") or time.time()),
                        json.dumps(payload, ensure_ascii=False),
                    ),
                )
                conn.commit()
            finally:
                conn.close()
        except Exception as exc:
            print(f"[Jobs] persist failed for {job_id}: {exc}")


def _set_job_fields(job_id: str, **updates):
    with job_lock:
        job = jobs.get(job_id)
        if not job:
            return None
        job.update(updates)
        snapshot = dict(job)
    _persist_job(job_id, snapshot)
    return snapshot


def _append_job_line(job_id: str, line: str):
    with job_lock:
        job = jobs.get(job_id)
        if not job:
            return
        job.setdefault("output_lines", []).append(line)
        snapshot = dict(job)
    _persist_job(job_id, snapshot)


def _load_recent_jobs():
    """Rehydrate recent durable jobs as interrupted/readable after API restart."""
    roots = [GLOBAL_OUTPUT_DIR]
    users_root = Path.home() / ".topology_users"
    if users_root.exists():
        try:
            roots.extend([p for p in users_root.iterdir() if p.is_dir()])
        except Exception:
            pass
    cutoff = time.time() - 86400
    restored = 0
    with job_lock:
        for root in roots:
            db_path = root / "discovery_jobs.db"
            if not db_path.exists():
                continue
            try:
                conn = sqlite3.connect(str(db_path), timeout=2.0)
                try:
                    for job_id, payload_text in conn.execute(
                        "SELECT job_id, payload FROM jobs WHERE updated_at >= ?", (cutoff,)
                    ):
                        payload = json.loads(payload_text or "{}")
                        if payload.get("status") in ("running", "starting", "queued"):
                            payload["status"] = "interrupted"
                            payload["error"] = "Discovery API restarted while this job was active"
                            payload.setdefault("output_lines", []).append("[WARN] Discovery API restarted; job state was restored as interrupted")
                        jobs[job_id] = payload
                        restored += 1
                finally:
                    conn.close()
            except Exception as exc:
                print(f"[Jobs] rehydrate skipped {db_path}: {exc}")
    if restored:
        print(f"[Jobs] Rehydrated {restored} recent discovery jobs")


# ANSI escape code pattern for stripping colors
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text for cleaner output."""
    return ANSI_ESCAPE.sub('', text)


def _parse_lldp_output(output: str) -> list:
    """
    Parse 'show lldp neighbor(s)' table output (DNOS style).
    Accepts pipe-separated table or space-aligned columns.
    Returns list of dicts: local_interface, neighbor_device, neighbor_port, capability.
    """
    neighbors = []
    in_table = False
    lines = output.split('\n')
    for line in lines:
        # Detect table header (pipes or Interface + Neighbor)
        if 'Interface' in line and 'Neighbor' in line:
            in_table = True
            continue
        if '---' in line or '|-' in line or '-|' in line:
            continue
        # Stop at CLI prompt
        if re.match(r'^[A-Za-z0-9_.-]+#', line.strip()) or re.match(r'^[A-Za-z0-9_.-]+\(', line.strip()):
            in_table = False
            continue
        # Pipe-separated table
        if in_table and '|' in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 3:
                local_iface = parts[0]
                neighbor_dev = parts[1]
                neighbor_port = parts[2]
                capability = parts[3] if len(parts) > 3 else ''
                if neighbor_dev and neighbor_dev not in ('Neighbor', 'Neighbor System Name', '-', ''):
                    if local_iface and not local_iface.lower().startswith('interface'):
                        neighbors.append({
                            'local_interface': local_iface,
                            'neighbor_device': neighbor_dev,
                            'neighbor_port': neighbor_port,
                            'capability': capability or ''
                        })
            continue
        # Space-aligned table (no pipes): at least 2 spaces between columns
        if in_table and line.strip():
            # Split on 2+ spaces to get columns
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) >= 3:
                local_iface = parts[0]
                neighbor_dev = parts[1]
                neighbor_port = parts[2]
                capability = parts[3] if len(parts) > 3 else ''
                if neighbor_dev and neighbor_dev not in ('Neighbor', '-', ''):
                    if local_iface and not local_iface.lower().startswith('interface'):
                        neighbors.append({
                            'local_interface': local_iface,
                            'neighbor_device': neighbor_dev,
                            'neighbor_port': neighbor_port,
                            'capability': capability or ''
                        })
    return neighbors


def _lldp_device_match(search: str, hostname: str, dir_name: str, serial: str, connection_ip: str, raw_serial: str) -> bool:
    """Match a search term to a device using word-boundary-aware logic.

    Prevents false positives like "PE" matching "PE-1" and "PE-2".
    Exact match on hostname/serial/IP always wins. For substring matching,
    requires the match to sit on a word boundary (separated by ``-``, ``_``,
    or start/end of string) so "PE-4" matches "YOR_CL_PE-4" but not "PE-40".
    """
    s = search.lower()
    h = hostname.lower()
    d = dir_name.lower()

    if s == h or s == d:
        return True
    if serial and serial.lower() == s:
        return True
    if connection_ip and connection_ip == raw_serial:
        return True

    def _boundary_match(needle: str, haystack: str) -> bool:
        idx = haystack.find(needle)
        if idx < 0:
            return False
        before_ok = idx == 0 or haystack[idx - 1] in ("-", "_", ".")
        end = idx + len(needle)
        after_ok = end == len(haystack) or haystack[end] in ("-", "_", ".")
        return before_ok and after_ok

    return _boundary_match(s, h) or _boundary_match(s, d)


def _resolve_discovery_target(name: str, ssh_hint: str = None, known_devices: list = None) -> dict:
    """Resolve a label/serial/IP to the best connect target for discovery API.

    Returns {target, source, input, ssh_hint, reachable?}. The resolver is
    intentionally read-only; mutating operations may run a follow-up preflight.
    """
    import socket
    raw = (name or "").strip()
    hint = (ssh_hint or "").strip()
    if hint:
        return {"input": raw, "target": hint, "source": "ssh_hint", "ssh_hint": hint}
    if not raw:
        return {"input": raw, "target": "", "source": "empty", "ssh_hint": ""}
    if re.match(r'^\d+\.\d+\.\d+\.\d+$', raw):
        return {"input": raw, "target": raw, "source": "ip_literal", "ssh_hint": ""}

    search_lower = raw.lower()
    if known_devices:
        for kd in known_devices:
            candidates = [
                kd.get("name"), kd.get("label"), kd.get("hostname"),
                kd.get("serial"), kd.get("host"), kd.get("hostBackup"),
            ]
            cand_lower = [str(c or "").lower() for c in candidates if c]
            if search_lower in cand_lower or any(search_lower in c or c in search_lower for c in cand_lower if c):
                for key in ("hostBackup", "host", "serial"):
                    value = (kd.get(key) or "").strip()
                    if value:
                        return {"input": raw, "target": value, "source": f"known_devices.{key}", "ssh_hint": ""}

    domain_suffixes = ['', '.dev.drivenets.net', '.drivenets.net', '.local']
    for suffix in domain_suffixes:
        try_host = raw + suffix
        try:
            resolved = socket.gethostbyname(try_host)
            return {"input": raw, "target": resolved, "source": f"dns:{try_host}", "ssh_hint": ""}
        except socket.gaierror:
            continue
    if raw != raw.upper():
        try:
            resolved = socket.gethostbyname(raw.upper())
            return {"input": raw, "target": resolved, "source": "dns:uppercase", "ssh_hint": ""}
        except socket.gaierror:
            pass

    db_configs = Path('/home/dn/SCALER/db/configs')
    if db_configs.exists():
        input_norm = raw.upper().replace('L', '1')
        for device_dir in db_configs.iterdir():
            if not device_dir.is_dir():
                continue
            op_file = device_dir / 'operational.json'
            if not op_file.exists():
                continue
            try:
                op_data = _safe_read_ops(op_file)
                dev_serial = (op_data.get('serial_number', '') or '').upper()
                dev_ip = op_data.get('connection_ip', '') or ''
                dev_hostname = op_data.get('hostname', device_dir.name) or device_dir.name
                dev_norm = dev_serial.replace('L', '1')
                exact = (
                    raw.lower() == dev_hostname.lower()
                    or raw.lower() == device_dir.name.lower()
                    or (dev_serial and raw.lower() == dev_serial.lower())
                    or raw.lower() in dev_hostname.lower()
                    or dev_hostname.lower() in raw.lower()
                )
                fuzzy = bool(dev_serial) and __import__('difflib').SequenceMatcher(None, input_norm, dev_norm).ratio() >= 0.75
                if exact or fuzzy:
                    target = dev_ip or dev_serial or dev_hostname
                    return {"input": raw, "target": target, "source": "scaler-db", "ssh_hint": ""}
            except Exception:
                continue

    inventory_file = _inventory_path()
    if inventory_file.exists():
        try:
            with open(inventory_file, 'r') as f:
                inventory = json.load(f)
            for key, dev in inventory.get('devices', {}).items():
                dev_hostname = (dev.get('hostname') or key)
                dev_mgmt = dev.get('mgmt_ip', '') or ''
                dev_serial = str(dev.get('serial') or '')
                key_value = str(key)
                lower_values = [dev_hostname.lower(), dev_serial.lower(), key_value.lower()]
                if search_lower in lower_values or any(search_lower in v or v in search_lower for v in lower_values if v):
                    for candidate in (dev_mgmt, dev_serial, key_value):
                        if candidate and re.match(r'^\d+\.\d+\.\d+\.\d+$', str(candidate)):
                            return {"input": raw, "target": str(candidate), "source": "device_inventory", "ssh_hint": ""}
                    for candidate in (dev_serial, key_value, dev_hostname):
                        if candidate:
                            return {"input": raw, "target": str(candidate), "source": "device_inventory_name", "ssh_hint": ""}
        except Exception:
            pass

    return {"input": raw, "target": raw, "source": "unresolved", "ssh_hint": ""}


def _tcp_preflight(host: str, port: int = 22, timeout: float = 3.0) -> dict:
    import socket
    started = time.time()
    try:
        sock = socket.socket()
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        return {"reachable": True, "port": port, "latency_ms": int((time.time() - started) * 1000)}
    except Exception as exc:
        return {"reachable": False, "port": port, "error": str(exc), "latency_ms": int((time.time() - started) * 1000)}


# ========================================================================
# Network Mapper — Recursive LLDP Discovery Engine
# ========================================================================

def _nm_resolve_host(name: str, known_devices: list = None) -> str:
    """Resolve a device name/serial/IP to a connectable target.
    known_devices: list of dicts from canvas with {name, host, hostBackup, serial}
    """
    return _resolve_discovery_target(name, known_devices=known_devices).get("target") or name
    # Legacy implementation kept below as unreachable reference during the
    # resolver consolidation migration. Remove after the new resolver is
    # exercised across LLDP/DNAAS/Network Mapper for a release cycle.
    import socket
    if re.match(r'^\d+\.\d+\.\d+\.\d+$', name):
        return name
    # Check canvas/DNAAS known devices first — these have verified IPs
    if known_devices:
        name_lower = name.lower()
        for kd in known_devices:
            kd_name = (kd.get('name') or '').lower()
            kd_backup = (kd.get('hostBackup') or '').lower()
            kd_serial = (kd.get('serial') or '').lower()
            if name_lower in (kd_name, kd_backup, kd_serial) or kd_name in name_lower or name_lower in kd_name:
                resolved = kd.get('host') or kd.get('serial') or ''
                if resolved:
                    return resolved
    domain_suffixes = ['', '.dev.drivenets.net', '.drivenets.net', '.local']
    for suffix in domain_suffixes:
        try:
            return socket.gethostbyname(name + suffix)
        except socket.gaierror:
            continue
    if name != name.upper():
        try:
            return socket.gethostbyname(name.upper())
        except socket.gaierror:
            pass
    # Try SCALER DB
    db_configs = Path('/home/dn/SCALER/db/configs')
    if db_configs.exists():
        for device_dir in db_configs.iterdir():
            if device_dir.is_dir():
                op_file = device_dir / 'operational.json'
                if op_file.exists():
                    try:
                        op_data = _safe_read_ops(op_file)
                        dev_hostname = (op_data.get('hostname', '') or '').lower()
                        dev_ip = op_data.get('connection_ip', '') or ''
                        if dev_hostname and (name.lower() == dev_hostname or
                                             name.lower() in dev_hostname or
                                             dev_hostname in name.lower()):
                            if dev_ip:
                                return dev_ip
                    except Exception:
                        pass
    # Try device_inventory.json
    inv_file = _inventory_path()
    if inv_file.exists():
        try:
            with open(inv_file, 'r') as f:
                inv_data = json.load(f)
            devices = inv_data.get('devices', {})
            for key, dev in devices.items():
                dev_hostname = (dev.get('hostname', '') or '').lower()
                if dev_hostname == name.lower() or name.lower() in dev_hostname:
                    mgmt_ip = dev.get('mgmt_ip', '') or ''
                    if mgmt_ip:
                        return mgmt_ip
        except Exception:
            pass
    return name


def _nm_ssh_discover_device(host: str, username: str, password: str, timeout: int = 30,
                            cancel_check=None) -> dict:
    """SSH to a device and collect hostname, system info, LLDP neighbors, mgmt interfaces.

    cancel_check: optional zero-arg callable returning True when the caller wants
    us to abort. Polled between shell commands so the user's Stop button takes
    effect within a couple of seconds instead of the full 15-20s command loop.
    """
    import paramiko
    result = {
        'hostname': host,
        'mgmt_ip': host if re.match(r'^\d+\.\d+\.\d+\.\d+$', host) else '',
        'serial': '',
        'system_type': '',
        'dnos_version': '',
        'lldp_neighbors': [],
        'error': None
    }

    def _cancelled():
        try:
            return bool(cancel_check()) if cancel_check else False
        except Exception:
            return False

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=username, password=password,
                       timeout=timeout, look_for_keys=False, allow_agent=False)
    except Exception as e:
        result['error'] = str(e)
        return result

    try:
        if _cancelled():
            result['error'] = 'cancelled'
            try:
                client.close()
            except Exception:
                pass
            return result

        shell = client.invoke_shell(width=250, height=50)
        shell.settimeout(timeout)
        import time as _time
        # Banner drain: poll cancel every 0.25s instead of blocking 3s
        _banner_end = _time.time() + 3
        while _time.time() < _banner_end:
            if _cancelled():
                result['error'] = 'cancelled'
                try:
                    client.close()
                except Exception:
                    pass
                return result
            _time.sleep(0.25)
        while shell.recv_ready():
            shell.recv(65535)
            _time.sleep(0.2)

        def _run_cmd(cmd, wait=4, max_wait=15):
            shell.send(cmd + ' | no-more\r\n')
            # Poll-wait instead of a single blocking sleep so cancellation lands fast
            wait_end = _time.time() + wait
            while _time.time() < wait_end:
                if _cancelled():
                    return ''
                _time.sleep(0.25)
            output = ''
            end = _time.time() + max_wait
            while _time.time() < end:
                if _cancelled():
                    return strip_ansi(output)
                if shell.recv_ready():
                    output += shell.recv(65535).decode('utf-8', errors='replace')
                    if '#' in output.split('\n')[-1]:
                        _time.sleep(0.3)
                        if shell.recv_ready():
                            output += shell.recv(65535).decode('utf-8', errors='replace')
                        break
                _time.sleep(0.3)
            return strip_ansi(output)

        # Hostname from prompt
        shell.send('\r\n')
        _time.sleep(1)
        prompt_out = ''
        if shell.recv_ready():
            prompt_out = shell.recv(65535).decode('utf-8', errors='replace')
        prompt_clean = strip_ansi(prompt_out).strip()
        # Use the LAST "word#" match -- the actual prompt is at the end of the
        # output, while MOTD/banner text may contain earlier "foo#" noise.
        prompt_matches = re.findall(r'([A-Za-z0-9_.-]+)#', prompt_clean)
        if prompt_matches:
            result['hostname'] = prompt_matches[-1]

        if _cancelled():
            result['error'] = 'cancelled'
            return result

        # System info
        sys_output = _run_cmd('show system', wait=3)
        for line in sys_output.split('\n'):
            line_s = line.strip()
            if 'serial' in line_s.lower() and ':' in line_s:
                result['serial'] = line_s.split(':', 1)[1].strip()
            elif 'type' in line_s.lower() and ':' in line_s and not result['system_type']:
                result['system_type'] = line_s.split(':', 1)[1].strip()
            elif 'version' in line_s.lower() and 'dnos' in line_s.lower():
                result['dnos_version'] = line_s.strip()

        if _cancelled():
            result['error'] = 'cancelled'
            return result

        # LLDP neighbors
        lldp_output = _run_cmd('show lldp neighbors', wait=3)
        result['lldp_neighbors'] = _parse_lldp_output(lldp_output)

        if _cancelled():
            result['error'] = 'cancelled'
            return result

        # Management interfaces (for mgmt IP)
        if not result['mgmt_ip']:
            mgmt_output = _run_cmd('show interfaces management', wait=3)
            for line in mgmt_output.split('\n'):
                ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)/\d+', line)
                if ip_match and not ip_match.group(1).startswith('127.'):
                    result['mgmt_ip'] = ip_match.group(1)
                    break

        if _cancelled():
            result['error'] = 'cancelled'
            return result

        # Interface brief for speed/state (lightweight — no detail)
        result['interfaces'] = {}
        try:
            iface_output = _run_cmd('show interfaces brief', wait=3)
            for line in iface_output.split('\n'):
                parts = line.split()
                if len(parts) >= 3 and re.match(r'(ge|hu|ce|eth|bundle)', parts[0]):
                    iface_name = parts[0]
                    iface_data = {}
                    for p in parts[1:]:
                        if re.match(r'\d+[GMK]', p):
                            iface_data['speed'] = p
                        elif p.lower() in ('up', 'down'):
                            iface_data['oper_state'] = p.lower()
                    if 'bundle' in iface_name.lower():
                        iface_data['is_bundle'] = True
                    result['interfaces'][iface_name] = iface_data
        except Exception:
            pass

        client.close()
    except Exception as e:
        result['error'] = str(e)
        try:
            client.close()
        except Exception:
            pass
    return result


def _nm_try_network_mapper_mcp(name: str) -> dict:
    """Try to get enriched device data from Network Mapper MCP server.
    Returns dict with lldp_neighbors, system_type, dnos_version, serial, interfaces.
    Returns None if MCP has no data for this device.
    Auto-resets MCP client on SSE/connection failures.
    """
    for attempt in range(2):
        try:
            nm = _get_mcp_client()

            nm_neighbors = nm.get_device_lldp(name)
            if not nm_neighbors:
                return None

            lldp = [{
                'local_interface': n.local_interface,
                'neighbor_device': n.neighbor_name,
                'neighbor_port': n.neighbor_interface
            } for n in nm_neighbors]

            result = {'lldp_neighbors': lldp, 'system_type': '', 'dnos_version': '', 'serial': '', 'interfaces': {}}

            try:
                sys_info = nm.get_device_system_info(name)
                if sys_info:
                    result['system_type'] = sys_info.get('system_type', '') or sys_info.get('platform', '') or ''
                    result['dnos_version'] = sys_info.get('version', '') or sys_info.get('software_version', '') or ''
                    result['serial'] = sys_info.get('serial_number', '') or sys_info.get('serial', '') or ''
            except Exception:
                pass

            try:
                iface_raw = nm._call_tool("get_device_interfaces_detail", {"device_name": name})
                if iface_raw:
                    result['interfaces'] = _parse_mcp_interfaces_detail(iface_raw)
            except Exception:
                pass

            return result
        except (RuntimeError, OSError, ConnectionError) as e:
            if attempt == 0:
                print(f"[MCP] _nm_try_network_mapper_mcp failed ({e}), resetting client...")
                _reset_mcp_client()
            else:
                return None
        except Exception as e:
            if attempt == 0 and ('cancel scope' in str(e).lower() or 'task' in str(e).lower()):
                print(f"[MCP] _nm_try_network_mapper_mcp SSE error ({e}), resetting client...")
                _reset_mcp_client()
            else:
                return None
    return None


def _parse_mcp_interfaces_detail(text: str) -> dict:
    """Parse MCP get_device_interfaces_detail markdown into {ifname: {speed, bundle, mtu}}."""
    interfaces = {}
    if not text:
        return interfaces

    current_iface = None
    for line in text.split('\n'):
        line = line.strip()
        # Interface header like "### ge400-0/0/1" or "**ge400-0/0/1**"
        if line.startswith('###') or (line.startswith('**') and line.endswith('**')):
            iface_name = re.sub(r'[#*\s]+', '', line).strip()
            if iface_name:
                current_iface = iface_name
                interfaces[current_iface] = {}
        elif current_iface and ':' in line:
            key, _, val = line.partition(':')
            key = key.strip().lower().replace(' ', '_').replace('**', '')
            val = val.strip()
            if key in ('speed', 'mtu', 'bundle', 'bundle_membership', 'fec', 'mac_address'):
                interfaces[current_iface][key] = val
        elif line.startswith('|') and '---' not in line and current_iface is None:
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 2:
                iface_name = parts[0]
                if iface_name and not iface_name.lower().startswith('interface'):
                    interfaces[iface_name] = {}
                    for i, val in enumerate(parts[1:]):
                        if val:
                            interfaces[iface_name][f'col_{i}'] = val

    return interfaces


def _nm_discover_one(name: str, host: str, use_mcp: bool,
                     ssh_user: str, ssh_pass: str,
                     ssh_timeout: int = 12,
                     cancel_check=None) -> dict:
    """Worker: try MCP first, then fall back to SSH. Runs inside ThreadPoolExecutor
    so hangs in either MCP (SSE) or SSH (paramiko) can be abandoned at cancellation
    without blocking the main BFS loop.

    cancel_check: optional callable returning True when the worker should abort.
    Checked between the MCP call and the SSH fallback, and forwarded into the
    SSH function so it can bail between shell commands.
    """
    def _cancelled():
        try:
            return bool(cancel_check()) if cancel_check else False
        except Exception:
            return False

    if _cancelled():
        return {
            'hostname': name,
            'mgmt_ip': host if re.match(r'^\d+\.\d+\.\d+\.\d+$', host) else '',
            'serial': '', 'system_type': '', 'dnos_version': '',
            'lldp_neighbors': [], 'interfaces': {},
            'error': 'cancelled',
        }

    if use_mcp:
        try:
            mcp_result = _nm_try_network_mapper_mcp(name)
        except Exception:
            mcp_result = None
        if mcp_result and mcp_result.get('lldp_neighbors'):
            return {
                'hostname': name,
                'mgmt_ip': host if re.match(r'^\d+\.\d+\.\d+\.\d+$', host) else '',
                'serial': mcp_result.get('serial', ''),
                'system_type': mcp_result.get('system_type', ''),
                'dnos_version': mcp_result.get('dnos_version', ''),
                'lldp_neighbors': mcp_result['lldp_neighbors'],
                'interfaces': mcp_result.get('interfaces', {}),
                'error': None,
                'source': 'mcp',
            }

    if _cancelled():
        return {
            'hostname': name,
            'mgmt_ip': host if re.match(r'^\d+\.\d+\.\d+\.\d+$', host) else '',
            'serial': '', 'system_type': '', 'dnos_version': '',
            'lldp_neighbors': [], 'interfaces': {},
            'error': 'cancelled',
        }

    return _nm_ssh_discover_device(
        host, ssh_user, ssh_pass,
        timeout=ssh_timeout,
        cancel_check=cancel_check,
    )


def _nm_bfs_crawl(job_id: str, seeds: list, max_depth: int, max_devices: int,
                  username: str, password: str, use_mcp: bool, known_devices: list = None):
    """BFS crawl from seed devices using LLDP to discover the network graph.
    known_devices: canvas/DNAAS devices with SSH info for smarter resolution.

    Cancellation is polled (a) at the top of each BFS iteration, and (b) after
    every completed future inside a batch. When cancel is observed we abandon
    outstanding futures (they run to their own timeout in their own threads but
    we stop collecting their results) and exit immediately so the UI unblocks.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    known_devices = known_devices or []
    known_creds = {}
    for kd in known_devices:
        for key in [kd.get('name', ''), kd.get('hostBackup', ''), kd.get('serial', '')]:
            if key:
                known_creds[key.lower()] = kd

    devices = {}      # hostname -> device_info
    links = []        # [{from_device, to_device, from_interface, to_interface}]
    link_set = set()  # dedup key for bidirectional links
    errors = []
    visited = set()   # normalized hostnames
    bfs_queue = queue.Queue()

    def normalize(name):
        return (name or '').strip().upper()

    def log(msg):
        print(f"[NM-{job_id}] {msg}")
        with nm_job_lock:
            if job_id in nm_jobs:
                nm_jobs[job_id]['log'].append(msg)

    def is_cancelled():
        with nm_job_lock:
            return bool(nm_jobs.get(job_id, {}).get('cancelled'))

    def update_progress(snapshot_devices=False):
        with nm_job_lock:
            if job_id not in nm_jobs:
                return
            if snapshot_devices:
                nm_jobs[job_id]['devices'] = dict(devices)
            nm_jobs[job_id]['links'] = list(links)
            nm_jobs[job_id]['errors'] = list(errors)
            nm_jobs[job_id]['progress']['discovered'] = len(devices)
            nm_jobs[job_id]['progress']['queued'] = bfs_queue.qsize()
            nm_jobs[job_id]['progress']['failed'] = len(errors)

    # Seed the queue
    for seed in seeds:
        seed = seed.strip()
        if seed:
            resolved = _nm_resolve_host(seed, known_devices)
            bfs_queue.put((seed, resolved, 0))
            log(f"Seed: {seed} -> {resolved}")

    with nm_job_lock:
        nm_jobs[job_id]['status'] = 'running'

    batch_size = 5        # concurrent SSH/MCP workers
    ssh_timeout = 12      # per-device SSH connect timeout (keep stop-responsive)

    while not bfs_queue.empty():
        if is_cancelled():
            with nm_job_lock:
                nm_jobs[job_id]['status'] = 'cancelled'
            log("Discovery cancelled by user")
            return

        # Collect a batch from the queue
        batch = []
        while not bfs_queue.empty() and len(batch) < batch_size:
            name, host, depth = bfs_queue.get()
            norm = normalize(name)
            if norm in visited:
                continue
            if len(devices) >= max_devices:
                log(f"Reached max devices limit ({max_devices})")
                break
            if depth > max_depth:
                continue
            visited.add(norm)
            batch.append((name, host, depth))

        if not batch:
            break

        # Show activity in the "queued" counter while this batch is in flight
        with nm_job_lock:
            nm_jobs[job_id]['progress']['queued'] = bfs_queue.qsize() + len(batch)

        executor = ThreadPoolExecutor(max_workers=min(batch_size, len(batch)))
        try:
            futures = {}
            for name, host, depth in batch:
                ssh_user = username
                ssh_pass = password
                kd = known_creds.get(name.lower()) or known_creds.get(host.lower())
                if kd:
                    ssh_user = kd.get('user') or username
                    ssh_pass = kd.get('password') or password
                log(f"Discovering {name} ({host}) at depth {depth}...")
                fut = executor.submit(
                    _nm_discover_one, name, host, use_mcp,
                    ssh_user, ssh_pass, ssh_timeout,
                    is_cancelled,
                )
                futures[fut] = (name, host, depth)

            cancelled_mid_batch = False
            for future in as_completed(futures):
                if is_cancelled():
                    cancelled_mid_batch = True
                    break

                name, host, depth = futures[future]
                try:
                    dev_info = future.result()
                except Exception as e:
                    errors.append({'device': name, 'host': host, 'error': str(e)})
                    log(f"  FAILED {name}: {e}")
                    update_progress()
                    continue

                # If the worker self-aborted because Stop was pressed, don't
                # count it as a failure and don't add a partial device.
                if dev_info.get('error') == 'cancelled':
                    cancelled_mid_batch = True
                    break

                if dev_info.get('error'):
                    errors.append({'device': name, 'host': host, 'error': dev_info['error']})
                    log(f"  FAILED {name}: {dev_info['error']}")
                    dev_info['_failed'] = True

                actual_hostname = dev_info.get('hostname', name) or name
                dev_info['hostname'] = actual_hostname
                dev_info['_connect_host'] = host
                dev_info['_depth'] = depth
                devices[actual_hostname] = dev_info
                update_progress(snapshot_devices=True)

                log(f"  OK {actual_hostname}: {len(dev_info.get('lldp_neighbors', []))} LLDP neighbors")

                # Process LLDP neighbors -- add links and enqueue new devices
                for neighbor in dev_info.get('lldp_neighbors', []):
                    neighbor_name = neighbor.get('neighbor_device', '')
                    if not neighbor_name:
                        continue
                    local_if = neighbor.get('local_interface', '')
                    remote_if = neighbor.get('neighbor_port', '')

                    link_key = frozenset([
                        f"{actual_hostname}:{local_if}",
                        f"{neighbor_name}:{remote_if}",
                    ])
                    if link_key not in link_set:
                        link_set.add(link_key)
                        links.append({
                            'from_device': actual_hostname,
                            'to_device': neighbor_name,
                            'from_interface': local_if,
                            'to_interface': remote_if,
                        })

                    norm_neighbor = normalize(neighbor_name)
                    if norm_neighbor not in visited and len(devices) < max_devices:
                        resolved_neighbor = _nm_resolve_host(neighbor_name, known_devices)
                        bfs_queue.put((neighbor_name, resolved_neighbor, depth + 1))
        finally:
            # Abandon any still-running futures on shutdown. They will finish
            # in background threads but we stop waiting for them.
            try:
                for f in list(futures):
                    f.cancel()
            except Exception:
                pass
            executor.shutdown(wait=False)

        update_progress()

        if cancelled_mid_batch or is_cancelled():
            with nm_job_lock:
                nm_jobs[job_id]['status'] = 'cancelled'
            log("Discovery cancelled by user (during batch)")
            return

    # Finalize
    with nm_job_lock:
        nm_jobs[job_id]['status'] = 'completed'
        nm_jobs[job_id]['devices'] = dict(devices)
        nm_jobs[job_id]['links'] = list(links)
        nm_jobs[job_id]['errors'] = list(errors)
        nm_jobs[job_id]['progress']['discovered'] = len(devices)
        nm_jobs[job_id]['progress']['queued'] = 0

    log(f"Discovery complete: {len(devices)} devices, {len(links)} links, {len(errors)} errors")


def _nm_mcp_full_map(job_id):
    """Build complete topology from MCP data — no SSH needed.

    Uses batch calls for efficiency: one SSE session per device.
    """
    import asyncio

    def log(msg):
        print(f"[MCPMap-{job_id}] {msg}")
        with nm_job_lock:
            if job_id in nm_jobs:
                nm_jobs[job_id]['log'].append(msg)

    def run_async(coro):
        """Run async coroutine safely from any thread."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    with nm_job_lock:
        nm_jobs[job_id]['status'] = 'running'

    try:
        nm = _get_mcp_client()
    except Exception as e:
        with nm_job_lock:
            nm_jobs[job_id]['status'] = 'completed'
            nm_jobs[job_id]['errors'] = [{'device': 'MCP', 'error': str(e)}]
        log(f"MCP init failed: {e}")
        return

    # --- Step 1: list all devices ---
    log("Listing devices from MCP...")
    try:
        raw_list = run_async(nm._call_tool_async("list_devices"))
        all_mcp_devices = nm._parse_devices_markdown(raw_list)
    except (RuntimeError, OSError, ConnectionError) as e:
        log(f"list_devices failed ({e}), resetting MCP client...")
        _reset_mcp_client()
        try:
            nm = _get_mcp_client()
            raw_list = run_async(nm._call_tool_async("list_devices"))
            all_mcp_devices = nm._parse_devices_markdown(raw_list)
        except Exception as e2:
            with nm_job_lock:
                nm_jobs[job_id]['status'] = 'completed'
                nm_jobs[job_id]['errors'] = [{'device': 'MCP', 'error': f"list_devices: {e2}"}]
            log(f"list_devices failed after retry: {e2}")
            return
    except Exception as e:
        with nm_job_lock:
            nm_jobs[job_id]['status'] = 'completed'
            nm_jobs[job_id]['errors'] = [{'device': 'MCP', 'error': f"list_devices: {e}"}]
        log(f"list_devices failed: {e}")
        return

    total = len(all_mcp_devices)
    log(f"MCP knows {total} devices")

    if total == 0:
        with nm_job_lock:
            nm_jobs[job_id]['status'] = 'completed'
        log("No devices found")
        return

    # hostname normalization
    clean_name_map = {}
    full_to_clean = {}
    for d in all_mcp_devices:
        clean = nm._extract_hostname(d.name)
        full_to_clean[d.name] = clean
        key = clean.lower()
        if key not in clean_name_map:
            clean_name_map[key] = clean

    # --- Step 2: per-device LLDP + system_info + mgmt_ip ---
    devices = {}
    links = []
    link_set = set()
    errors = []

    for idx, d in enumerate(all_mcp_devices):
        clean = full_to_clean[d.name]
        log(f"[{idx+1}/{total}] {clean}")

        with nm_job_lock:
            nm_jobs[job_id]['progress']['discovered'] = idx + 1

        batch_calls = [
            ("get_device_lldp", {"device_name": d.name}),
            ("get_device_system_info", {"device_name": d.name}),
            ("get_device_management_interfaces", {"device_name": d.name}),
        ]
        batch_results = [None, None, None]
        try:
            batch_results = run_async(nm._call_tools_batch_async(batch_calls))
        except (RuntimeError, OSError, ConnectionError) as e:
            log(f"  MCP error for {clean} ({e}), resetting client and retrying...")
            _reset_mcp_client()
            try:
                nm = _get_mcp_client()
                batch_results = run_async(nm._call_tools_batch_async(batch_calls))
            except Exception as e2:
                errors.append({'device': clean, 'error': f"batch: {e2}"})
                log(f"  Error fetching {clean} after retry: {e2}")
        except Exception as e:
            errors.append({'device': clean, 'error': f"batch: {e}"})
            log(f"  Error fetching {clean}: {e}")

        lldp_text = batch_results[0] or ''
        sys_text = batch_results[1] or ''
        mgmt_text = batch_results[2] or ''

        lldp_raw = nm._parse_lldp_markdown(lldp_text)
        sys_info = nm._parse_system_info_markdown(sys_text)

        # Parse mgmt IP from management interfaces text
        mgmt_ip = ''
        ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', mgmt_text)
        if ip_match:
            mgmt_ip = ip_match.group(1)

        # Clean up version: "DNOS [26.2.0] build [2_priv], Copyright..." -> "26.2.0"
        raw_ver = sys_info.get('version', sys_info.get('software_version', d.version if d.version != 'unknown' else ''))
        ver_match = re.search(r'(\d+\.\d+\.\d+)', raw_ver)
        clean_ver = ver_match.group(1) if ver_match else raw_ver

        # Clean system_type: "SA-36CD-S (NCR)" -> "SA-36CD-S"
        raw_sys = sys_info.get('system_type', sys_info.get('platform', ''))
        sys_match = re.match(r'^([A-Za-z0-9_-]+)', raw_sys)
        clean_sys = sys_match.group(1) if sys_match else raw_sys

        dev_entry = {
            'hostname': clean,
            'mgmt_ip': mgmt_ip,
            'serial': sys_info.get('serial', sys_info.get('serial_number', '')),
            'system_type': clean_sys,
            'dnos_version': clean_ver,
            'lldp_neighbors': [],
            'source': 'mcp',
            '_connect_host': mgmt_ip
        }

        for n in lldp_raw:
            nb_clean = clean_name_map.get(n.neighbor_name.lower(), n.neighbor_name)
            dev_entry['lldp_neighbors'].append({
                'local_interface': n.local_interface,
                'neighbor_device': nb_clean,
                'neighbor_port': n.neighbor_interface
            })
            lk = frozenset([f"{clean}:{n.local_interface}", f"{nb_clean}:{n.neighbor_interface}"])
            if lk not in link_set:
                link_set.add(lk)
                links.append({
                    'from_device': clean,
                    'to_device': nb_clean,
                    'from_interface': n.local_interface,
                    'to_interface': n.neighbor_interface
                })

        devices[clean] = dev_entry

        with nm_job_lock:
            nm_jobs[job_id]['devices'] = dict(devices)
            nm_jobs[job_id]['links'] = list(links)

    # --- Step 3: stubs for LLDP neighbors not in device list ---
    known_lower = {k.lower() for k in devices}
    stubs_added = 0
    for link in links:
        for field in ('from_device', 'to_device'):
            dn = link[field]
            if dn.lower() not in known_lower:
                devices[dn] = {
                    'hostname': dn, 'mgmt_ip': '', 'serial': '',
                    'system_type': '', 'dnos_version': '',
                    'lldp_neighbors': [], 'source': 'lldp_stub', '_connect_host': ''
                }
                known_lower.add(dn.lower())
                stubs_added += 1

    if stubs_added:
        log(f"Added {stubs_added} stub device(s) from LLDP neighbor references")

    with nm_job_lock:
        nm_jobs[job_id]['status'] = 'completed'
        nm_jobs[job_id]['devices'] = dict(devices)
        nm_jobs[job_id]['links'] = list(links)
        nm_jobs[job_id]['errors'] = errors
        nm_jobs[job_id]['progress']['discovered'] = len(devices)
        nm_jobs[job_id]['progress']['queued'] = 0

    log(f"MCP map complete: {len(devices)} devices ({stubs_added} stubs), {len(links)} links")


def _extract_mgmt_ip(mgmt_text: str) -> str:
    """Parse MCP management interfaces markdown, prefer mgmt0/mgmt-ncc-0 IPs."""
    import re as _re
    best_ip = ''
    for line in str(mgmt_text).split('\n'):
        line_lower = line.lower()
        ip_match = _re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
        if not ip_match:
            continue
        ip = ip_match.group(1)
        if 'mgmt0' in line_lower or 'mgmt-ncc-0 ' in line_lower:
            best_ip = ip
            break
        if ('mgmt' in line_lower) and not best_ip:
            best_ip = ip
        if not best_ip and 'ipmi' not in line_lower and 'console' not in line_lower:
            best_ip = ip
    return best_ip


def _resolve_device_mgmt(device_name: str) -> dict:
    """Resolve a device LLDP name to its management IP using MCP + inventory.
    Strategy:
      1. get_full_device_info_with_mgmt (fast, handles partial names)
      2. _call_tool('get_device_management_interfaces') if #1 gives no IP
      3. _nm_resolve_host for inventory/DNS fallback
    """
    import re as _re
    result = {'name': device_name, 'mgmt_ip': '', 'serial': '', 'hostname': '', 'source': ''}

    try:
        info = _mcp_call('get_full_device_info_with_mgmt', device_name)
        if info:
            result['hostname'] = info.get('hostname') or info.get('full_name') or device_name
            result['serial'] = info.get('serial') or ''
            result['source'] = 'network-mapper'
            if info.get('mgmt_ip'):
                result['mgmt_ip'] = info['mgmt_ip']
            elif info.get('connection_target'):
                ct = info['connection_target']
                if _re.match(r'^\d+\.\d+\.\d+\.\d+$', ct):
                    result['mgmt_ip'] = ct
    except Exception as e:
        print(f"[Resolve] MCP info lookup failed for {device_name}: {e}")

    if not result['mgmt_ip']:
        try:
            nm = _get_mcp_client()
            mgmt_text = nm._call_tool('get_device_management_interfaces', {'device_name': device_name})
            if mgmt_text and 'not found' not in str(mgmt_text).lower():
                ip = _extract_mgmt_ip(mgmt_text)
                if ip:
                    result['mgmt_ip'] = ip
                    result['source'] = 'network-mapper'
                    if not result['hostname']:
                        result['hostname'] = device_name
        except Exception as e:
            print(f"[Resolve] MCP mgmt interfaces failed for {device_name}: {e}")

    if not result['mgmt_ip']:
        resolved = _nm_resolve_host(device_name)
        if resolved and resolved != device_name and _re.match(r'^\d+\.\d+\.\d+\.\d+$', resolved):
            result['mgmt_ip'] = resolved
            result['source'] = result['source'] or 'inventory'

    print(f"[Resolve] {device_name} -> mgmt={result['mgmt_ip']} serial={result['serial']} src={result['source']}")
    return result


def _find_active_lldp_for_device(device_key: str):
    if not device_key:
        return None
    for jid in [lldp_device_current.get(device_key)] + list(lldp_device_queues.get(device_key, [])):
        if not jid:
            continue
        job = jobs.get(jid)
        if job and job.get("status") in ("running", "queued", "starting"):
            return jid, job
    return None


def _mark_lldp_current(device_key: str, job_id: str):
    if device_key:
        lldp_device_current[device_key] = job_id


def _clear_lldp_current(device_key: str, job_id: str):
    if device_key and lldp_device_current.get(device_key) == job_id:
        lldp_device_current.pop(device_key, None)


def _launch_lldp_job(handler, job_id: str):
    def run_enable_lldp():
        with job_lock:
            job = jobs.get(job_id)
            if not job:
                return
            job['status'] = 'running'
            job['started_at'] = datetime.now().isoformat()
            job['progress'] = max(job.get('progress', 0), 1)
            device_key = job.get('device_key', '')
            serial = job.get('serial', '')
            username = job.get('_runtime_username', 'dnroot')
            password = job.get('_runtime_password', 'dnroot')
            skip_host_key = job.get('_runtime_skip_host_key', False)
            ssh_host = job.get('resolved_target') or job.get('_runtime_ssh_host') or None
            _mark_lldp_current(device_key, job_id)
            snapshot = dict(job)
        _persist_job(job_id, snapshot)
        try:
            result = handler._enable_lldp_on_device(
                serial, job_id, username, password, skip_host_key, ssh_host=ssh_host
            )
            _set_job_fields(
                job_id,
                status='completed' if result.get('success') else 'failed',
                progress=100,
                interfaces_enabled=result.get('interfaces_enabled', 0),
                interfaces=result.get('interfaces', []),
                already_configured=result.get('already_configured', False),
                error=None if result.get('success') else result.get('error', 'Unknown error'),
            )
        except Exception as e:
            _append_job_line(job_id, f"✗ Error: {str(e)}")
            _set_job_fields(job_id, status='failed', progress=100, error=str(e))
        finally:
            with job_lock:
                job = jobs.get(job_id, {})
                device_key = job.get('device_key', '')
                _clear_lldp_current(device_key, job_id)
                next_id = None
                q = lldp_device_queues.get(device_key, [])
                while q:
                    candidate = q.pop(0)
                    candidate_job = jobs.get(candidate)
                    if candidate_job and candidate_job.get('status') == 'queued':
                        next_id = candidate
                        break
                if not q:
                    lldp_device_queues.pop(device_key, None)
            if next_id:
                _append_job_line(next_id, "[INFO] Previous LLDP operation finished; starting queued job")
                _launch_lldp_job(handler, next_id)

    thread = threading.Thread(target=run_enable_lldp, daemon=True)
    thread.start()
    return thread


class DiscoveryHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _enable_lldp_on_device(self, serial: str, job_id: str = None, username: str = 'dnroot', password: str = 'dnroot', skip_host_key: bool = False, ssh_host: str = None) -> dict:
        """
        Enable LLDP and admin-state on all PHYSICAL interfaces of a device.
        Only enables on ge*, eth*, hu*, ce*, qsfp* - NOT on loopbacks, management, or sub-interfaces.
        Uses SSH to configure the device.

        If job_id is provided, updates the job's output_lines for real-time feedback.
        If skip_host_key is True, ignores all host key verification (like ssh -o StrictHostKeyChecking=no).
        If ssh_host is provided (mgmt IP), use it directly instead of resolving serial.
        """
        import paramiko
        import re
        import time
        
        def log(msg: str):
            """Log message to job output and print"""
            print(msg)
            if job_id and job_id in jobs:
                jobs[job_id]['output_lines'].append(msg)
        
        try:
            log(f"Connecting to {serial}...")
            if skip_host_key:
                log(f"Host key verification: DISABLED (lab/test mode)")
            
            import socket
            connect_host = None
            resolved_ip = None
            
            # Use ssh_host directly only when the frontend has an explicit
            # transport target. Otherwise use the shared resolver instead of
            # SSHing to a canvas label like "RR-SA-2".
            if ssh_host and ssh_host.strip():
                connect_host = ssh_host.strip()
                resolved_ip = connect_host
                log(f"Using ssh_host {connect_host} for {serial}")
            else:
                connect_host = self._resolve_serial_to_host(serial)
                if connect_host and connect_host != serial:
                    log(f"Resolved {serial} -> {connect_host}")
                else:
                    log(f"[WARN] Could not resolve {serial} from DNS/cache/inventory")
                    log(f"Trying direct connection to {serial}...")
            
            # Connect to device
            client = paramiko.SSHClient()
            
            # Host key policy: AutoAddPolicy for normal, WarningPolicy that accepts all for skip mode
            if skip_host_key:
                # Create a policy that accepts ANY host key (like -o StrictHostKeyChecking=no)
                class AcceptAllPolicy(paramiko.MissingHostKeyPolicy):
                    def missing_host_key(self, client, hostname, key):
                        pass  # Accept all keys silently
                client.set_missing_host_key_policy(AcceptAllPolicy())
                # Also load system host keys but don't fail on mismatch
                try:
                    client.load_system_host_keys()
                except:
                    pass
            else:
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                client.connect(
                    connect_host,
                    username=username,
                    password=password,
                    timeout=30,
                    look_for_keys=False,
                    allow_agent=False
                )
            except paramiko.ssh_exception.NoValidConnectionsError as conn_err:
                log(f"✗ Cannot connect to {connect_host}: No route to host or connection refused")
                raise Exception(f"Cannot connect to {connect_host}: {conn_err}")
            except paramiko.ssh_exception.AuthenticationException as auth_err:
                log(f"✗ Authentication failed for {connect_host}")
                raise Exception(f"SSH auth failed for {connect_host}: {auth_err}")
            except socket.timeout:
                log(f"✗ Connection timed out for {connect_host}")
                raise Exception(f"SSH connection timed out for {connect_host}")
            except socket.error as sock_err:
                log(f"✗ Socket error connecting to {connect_host}: {sock_err}")
                raise Exception(f"Cannot reach {connect_host}: {sock_err}")
            
            log(f"✓ Connected to {connect_host} (serial: {serial})")
            
            # Store SSH client in job for cancellation support
            if job_id and job_id in jobs:
                jobs[job_id]['_ssh_client'] = client
            
            # Helper to check if cancelled
            def is_cancelled():
                return job_id and job_id in jobs and jobs[job_id].get('cancelled', False)
            
            # Set up transport with keepalive
            transport = client.get_transport()
            transport.set_keepalive(10)  # Send keepalive every 10 seconds (more frequent)
            
            # Get interactive shell
            try:
                shell = client.invoke_shell(width=250, height=50)
                shell.settimeout(180)  # Increase timeout to 3 minutes for slow devices
            except Exception as shell_err:
                log(f"✗ Failed to open shell: {shell_err}")
                raise Exception(f"Failed to open SSH shell on {serial}: {shell_err}")
            
            log("⏳ Waiting for CLI to load...")
            
            # Helper to safely send command
            def safe_send(cmd):
                try:
                    # Check if connection is still alive
                    transport = client.get_transport()
                    if not transport or not transport.is_active():
                        log(f"✗ SSH transport is no longer active")
                        raise Exception(f"SSH connection to {serial} was closed")
                    return shell.send(cmd)
                except BrokenPipeError as e:
                    log(f"✗ Broken pipe - connection closed by remote: {e}")
                    raise Exception(f"SSH connection to {serial} was closed by remote host (broken pipe)")
                except socket.error as e:
                    log(f"✗ Connection lost: {e}")
                    raise Exception(f"SSH connection lost to {serial}: {e}")
                except OSError as e:
                    log(f"✗ OS error: {e}")
                    raise Exception(f"SSH error on {serial}: {e}")
                except Exception as e:
                    log(f"✗ Error: {e}")
                    raise Exception(f"SSH error on {serial}: {e}")
            
            # Helper to safely receive with prompt detection
            def safe_recv(timeout_seconds=10, wait_for_prompt=True):
                output = ""
                end_time = time.time() + timeout_seconds
                idle_since = None
                try:
                    while time.time() < end_time:
                        if shell.recv_ready():
                            output += shell.recv(65535).decode('utf-8', errors='ignore')
                            idle_since = None
                            if wait_for_prompt and output.rstrip():
                                last_line = output.rstrip().split('\n')[-1].strip()
                                if last_line.endswith('#') or last_line.endswith('>'):
                                    time.sleep(0.15)
                                    if shell.recv_ready():
                                        output += shell.recv(65535).decode('utf-8', errors='ignore')
                                    break
                        else:
                            if idle_since is None:
                                idle_since = time.time()
                            elif output and (time.time() - idle_since) > 1.0:
                                break
                            time.sleep(0.1)
                except socket.error as e:
                    log(f"[WARN] Connection issue while receiving: {e}")
                return output
            
            time.sleep(2)
            
            initial_output = ""
            try:
                while shell.recv_ready():
                    initial_output += shell.recv(65535).decode('utf-8', errors='ignore')
                    time.sleep(0.1)
            except:
                pass
            
            if initial_output:
                # Check for auth failure or error messages
                if 'denied' in initial_output.lower() or 'invalid' in initial_output.lower():
                    log(f"✗ Authentication may have failed: {initial_output[:200]}")
                else:
                    log(f"📝 CLI ready ({len(initial_output)} bytes initial output)")
            else:
                log("📝 CLI ready (no initial output)")
            
            # Verify channel is still active
            if not shell.get_transport() or not shell.get_transport().is_active():
                log("✗ SSH transport closed unexpectedly")
                raise Exception(f"SSH channel to {serial} closed unexpectedly after CLI load")
            
            log("[INFO] Getting interface list...")
            safe_send("\n")
            time.sleep(0.5)
            
            safe_send("show interfaces description | no-more\n")
            time.sleep(1)
            
            output = safe_recv(15)
            
            log(f"📊 Raw output length: {len(output)} chars")
            
            # Check for cancellation
            if is_cancelled():
                log("⚠ Cancelled by user")
                client.close()
                return {'success': False, 'error': 'Cancelled by user'}
            
            # Parse ONLY physical NIF interfaces (no sub-interfaces with dots, no loopbacks, no management)
            # Match patterns:
            # - Standard: ge400-0/0/1, ge100-0/0/12, hu0-0/0/1, ce0-0/0/0, qsfp0-0/0/0
            # - Cluster NCP NIF: ge100-0/0/0, ge400-1/0/0 (nodeId is 0 or 1 for NCP-A/NCP-B)
            # Exclude: lo0, mgmt0, *.1 (sub-interfaces), bundle-*, lag-*, ctrl-*, ice*, fab*
            physical_interface_pattern = re.compile(
                r'\b((?:ge|xe|et|hu|ce|qsfp)\d*-\d+/\d+/\d+)\b',
                re.MULTILINE
            )
            
            # Find all matches and filter out sub-interfaces (containing dots)
            all_matches = physical_interface_pattern.findall(output)
            physical_interfaces = [iface for iface in all_matches if '.' not in iface]
            
            # Remove duplicates while preserving order
            seen = set()
            unique_interfaces = []
            for iface in physical_interfaces:
                if iface.lower() not in seen:
                    seen.add(iface.lower())
                    unique_interfaces.append(iface)
            
            # Detect if this is a cluster (DNAAS) device by checking for NCP patterns
            # Cluster devices have BOTH ge100-* and ge400-* interfaces (NCP + NCF)
            # PE devices typically have only ge400-* interfaces
            has_ge100 = any(iface.startswith('ge100-') for iface in unique_interfaces)
            has_ge400 = any(iface.startswith('ge400-') for iface in unique_interfaces)
            is_cluster = has_ge100 and has_ge400  # True cluster has BOTH types
            
            if is_cluster:
                log(f"📊 Detected CLUSTER device - Found {len(unique_interfaces)} NCP NIF interfaces")
                log(f"   ℹ️  Cluster has both ge100-* ({sum(1 for i in unique_interfaces if i.startswith('ge100-'))}) and ge400-* ({sum(1 for i in unique_interfaces if i.startswith('ge400-'))}) interfaces")
            else:
                log(f"📊 Found {len(unique_interfaces)} physical interfaces (PE/standalone device)")
                if has_ge400:
                    log(f"   ℹ️  Will configure speed 100 + fec none on {sum(1 for i in unique_interfaces if i.startswith('ge400-'))} ge400-* interfaces")
            
            # If no interfaces found, show what we got
            if not unique_interfaces:
                # Try to extract any interface-like patterns for debugging
                any_iface_pattern = re.compile(r'\b(\S*\d+[-/]\d+[/\d]*)\b')
                any_matches = any_iface_pattern.findall(output)[:10]
                log(f"⚠ No ge/hu/ce/qsfp/eth interfaces found. Sample patterns: {any_matches[:5]}")
            
            # ================================================================
            # CHECK IF LLDP IS ALREADY CONFIGURED ON ALL INTERFACES
            # ================================================================
            if unique_interfaces:
                log("[INFO] Checking existing LLDP configuration...")
                safe_send("show config protocols lldp | no-more\n")
                time.sleep(0.5)
                lldp_config_output = safe_recv(8)
                
                # Parse interfaces that already have LLDP configured
                # DNOS format: "interface ge400-0/0/1" under protocols lldp
                lldp_configured_pattern = re.compile(r'interface\s+((?:ge|xe|et|hu|ce|qsfp)\d*-\d+/\d+/\d+)', re.MULTILINE)
                already_configured = set(lldp_configured_pattern.findall(lldp_config_output))
                
                # Check if admin-state is enabled globally
                lldp_admin_enabled = 'admin-state enabled' in lldp_config_output.lower()
                
                # Compare: which interfaces need LLDP configuration?
                interfaces_needing_lldp = [iface for iface in unique_interfaces if iface not in already_configured]
                
                if lldp_admin_enabled and len(interfaces_needing_lldp) == 0:
                    # LLDP is already fully configured!
                    log(f"✅ LLDP is already configured on all {len(unique_interfaces)} interfaces!")
                    log(f"   Admin-state: enabled")
                    log(f"   Interfaces with LLDP: {len(already_configured)}")
                    
                    log("[INFO] Verifying interface admin-state...")
                    safe_send("show interfaces description | no-more\n")
                    time.sleep(0.5)
                    iface_status_output = safe_recv(10)
                    
                    # Count interfaces that are admin-down
                    admin_down_count = 0
                    for iface in unique_interfaces:
                        # Look for interface line with "down" or "admin-down" status
                        iface_pattern = re.compile(rf'{re.escape(iface)}\s+.*?(?:admin-down|down)', re.IGNORECASE)
                        if iface_pattern.search(iface_status_output):
                            admin_down_count += 1
                    
                    if admin_down_count == 0:
                        log(f"✅ All {len(unique_interfaces)} interfaces have admin-state enabled!")
                        client.close()
                        return {
                            'success': True,
                            'message': f'LLDP already configured on all {len(unique_interfaces)} interfaces',
                            'interfaces_enabled': len(unique_interfaces),
                            'interfaces': unique_interfaces[:20],
                            'already_configured': True
                        }
                    else:
                        log(f"⚠ LLDP configured but {admin_down_count} interfaces are admin-down")
                        log(f"   Will enable admin-state on those interfaces...")
                        # Continue to enable admin-state only
                        interfaces_needing_lldp = []  # LLDP is done, just need admin-state
                
                elif len(already_configured) > 0:
                    log(f"📊 LLDP partially configured: {len(already_configured)}/{len(unique_interfaces)} interfaces")
                    log(f"   Need to configure: {len(interfaces_needing_lldp)} more interfaces")
                else:
                    log(f"📊 LLDP not configured - will configure all {len(unique_interfaces)} interfaces")
            
            interfaces_enabled = 0
            
            if unique_interfaces:
                log("[INFO] Entering configuration mode...")
                safe_send("configure\n")
                time.sleep(0.5)
                
                log("[INFO] Enabling LLDP globally...")
                safe_send("protocols lldp\nadmin-state enabled\n")
                time.sleep(0.3)
                
                # Step 2: Configure LLDP on all interfaces using batch mode
                # Sends multi-line config blocks instead of one-at-a-time with per-line sleeps
                total = len(unique_interfaces)
                log(f"[FAST] Configuring LLDP on {total} interfaces (batch mode)...")
                
                lldp_lines = []
                for iface in unique_interfaces:
                    lldp_lines.extend([f"interface {iface}", "!"])
                lldp_lines.append("!")  # Exit protocols lldp -> cfg-protocols
                lldp_lines.append("!")  # Exit protocols -> cfg
                
                LLDP_BATCH = 30
                for i in range(0, len(lldp_lines), LLDP_BATCH):
                    if is_cancelled():
                        log("[WARN] Cancelled by user")
                        safe_send("!\n!\n!\nexit\n")
                        client.close()
                        return {'success': False, 'error': 'Cancelled by user'}
                    batch = "\n".join(lldp_lines[i:i+LLDP_BATCH]) + "\n"
                    safe_send(batch)
                    time.sleep(0.3)
                
                safe_recv(2)
                log(f"[OK] LLDP configured on all {total} interfaces")
                
                # Step 3: Enable admin-state on all interfaces using batch mode
                ge400_interfaces = [iface for iface in unique_interfaces if iface.startswith('ge400-')]
                has_400g = len(ge400_interfaces) > 0
                
                if has_400g:
                    log(f"[INFO] Detected {len(ge400_interfaces)} 400G interfaces - will set FEC none + speed 100")
                
                log(f"[FAST] Enabling admin-state on {total} interfaces (batch mode)...")
                
                admin_lines = ["interfaces"]
                ge400_count = 0
                for iface in unique_interfaces:
                    admin_lines.append(iface)
                    admin_lines.append("admin-state enabled")
                    if iface.startswith('ge400-') and not is_cluster:
                        admin_lines.append("fec none")
                        admin_lines.append("speed 100")
                        ge400_count += 1
                    admin_lines.append("!")
                admin_lines.append("!")  # Exit interfaces hierarchy
                
                ADMIN_BATCH = 20
                for i in range(0, len(admin_lines), ADMIN_BATCH):
                    if is_cancelled():
                        log("[WARN] Cancelled by user")
                        safe_send("!\n!\nexit\n")
                        client.close()
                        return {'success': False, 'error': 'Cancelled by user'}
                    batch = "\n".join(admin_lines[i:i+ADMIN_BATCH]) + "\n"
                    safe_send(batch)
                    time.sleep(0.3)
                
                interfaces_enabled = len(unique_interfaces)
                safe_recv(2)
                if ge400_count > 0:
                    log(f"[OK] Admin-state enabled on {total} interfaces ({ge400_count}x 400G: speed 100 + fec none)")
                else:
                    log(f"[OK] Admin-state enabled on {total} interfaces")
                
                log("[INFO] Committing configuration...")
                safe_send("commit\n")
                time.sleep(1)
                commit_output = safe_recv(20)
                
                # Log the full commit output for debugging
                if commit_output:
                    log(f"📄 Commit output ({len(commit_output)} chars):")
                    for line in commit_output.splitlines()[:20]:  # Show first 20 lines
                        if line.strip():
                            log(f"   {line[:120]}")  # Truncate long lines
                
                if 'error' in commit_output.lower() or 'failed' in commit_output.lower() or 'invalid' in commit_output.lower():
                    log("[ERROR] LLDP commit failed; configuration was not applied")
                    safe_send("exit\n")
                    time.sleep(0.3)
                    client.close()
                    return {
                        'success': False,
                        'error': f"LLDP commit failed: {strip_ansi(commit_output)[-500:]}",
                        'interfaces_enabled': 0,
                        'interfaces': unique_interfaces[:20],
                    }
                elif 'commit complete' in commit_output.lower():
                    log("✅ Configuration committed successfully!")
                elif not commit_output.strip():
                    log("✅ Configuration committed (no output = success in DNOS)")
                else:
                    log(f"✅ Configuration committed (output: {len(commit_output)} bytes)")
                
                safe_send("exit\n")
                time.sleep(0.3)
                
                # LLDP PDUs are sent immediately on enable; neighbors appear within 5s
                log("[INFO] Waiting for LLDP neighbor discovery (5 seconds)...")
                for wait_sec in range(5):
                    if is_cancelled():
                        log("[WARN] Cancelled during LLDP wait")
                        client.close()
                        return {'success': False, 'error': 'Cancelled by user'}
                    time.sleep(1)
                
                log("[OK] LLDP hello wait completed!")
            else:
                log("[WARN] No physical interfaces detected - enabling LLDP globally anyway...")
                safe_send("configure\n")
                time.sleep(0.5)
                safe_send("protocols lldp\nadmin-state enabled\n!\ncommit\n")
                time.sleep(1)
                safe_recv(10)
                safe_send("exit\n")
                time.sleep(0.3)
                log("✓ LLDP enabled globally (interfaces may need manual configuration)")
            
            client.close()
            
            # Build success message
            ge400_count = len([iface for iface in unique_interfaces if iface.startswith('ge400-')])
            if ge400_count > 0:
                log(f"✅ LLDP enabled on {interfaces_enabled} interfaces! ({ge400_count}x 400G set to 100g speed)")
                msg = f'LLDP + admin-state on {interfaces_enabled} interfaces, {ge400_count}x 400G→100g for DNAAS'
            else:
                log(f"✅ LLDP enabled on {interfaces_enabled} interfaces!")
                msg = f'LLDP enabled globally + admin-state enabled on {interfaces_enabled} physical interfaces'
            
            return {
                'success': True,
                'message': msg,
                'interfaces_enabled': interfaces_enabled,
                'interfaces': unique_interfaces[:20]  # Return first 20 for display
            }
            
        except Exception as e:
            error_msg = f"✗ Error: {str(e)}"
            log(error_msg)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _resolve_serial_to_host(self, serial: str) -> str:
        """Resolve a serial/hostname to a connectable IP or hostname.
        Tries: DNS with suffixes -> Scaler DB (fuzzy match) -> uppercase serial.
        """
        resolved = _resolve_discovery_target(serial)
        target = resolved.get("target") or serial
        if target != serial:
            print(f"[Resolve] {serial} -> {target} ({resolved.get('source')})")
        return target
        # Legacy implementation kept below as unreachable reference during the
        # resolver consolidation migration.
        import socket
        from difflib import SequenceMatcher
        
        # Already an IP?
        import re
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', serial):
            return serial
        
        # Try DNS resolution with domain suffixes
        domain_suffixes = ['', '.dev.drivenets.net', '.drivenets.net', '.local']
        for suffix in domain_suffixes:
            try_host = serial + suffix
            try:
                resolved_ip = socket.gethostbyname(try_host)
                print(f"[Resolve] {serial} -> {resolved_ip} (DNS: {try_host})")
                return resolved_ip
            except socket.gaierror:
                continue
        
        # Try uppercase (DNOS serials resolve in uppercase)
        if serial != serial.upper():
            try:
                resolved_ip = socket.gethostbyname(serial.upper())
                print(f"[Resolve] {serial} -> {resolved_ip} (DNS uppercase)")
                return resolved_ip
            except socket.gaierror:
                pass
        
        # Fuzzy match against Scaler DB serials
        db_configs = Path('/home/dn/SCALER/db/configs')
        if db_configs.exists():
            input_norm = serial.upper().replace('L', '1')
            for device_dir in db_configs.iterdir():
                if device_dir.is_dir():
                    op_file = device_dir / 'operational.json'
                    if op_file.exists():
                        try:
                            op_data = _safe_read_ops(op_file)
                            dev_serial = (op_data.get('serial_number', '') or '').upper()
                            dev_ip = op_data.get('connection_ip', '') or ''
                            dev_hostname = op_data.get('hostname', device_dir.name) or device_dir.name
                            
                            if not dev_serial:
                                continue
                            
                            # Fuzzy match (handles l/1 confusion, typos)
                            dev_norm = dev_serial.replace('L', '1')
                            ratio = SequenceMatcher(None, input_norm, dev_norm).ratio()
                            exact = (serial.lower() in dev_hostname.lower() or
                                     dev_hostname.lower() in serial.lower())
                            
                            if ratio >= 0.75 or exact:
                                if dev_ip:
                                    print(f"[Resolve] {serial} -> {dev_ip} (Scaler DB)")
                                    return dev_ip
                                try:
                                    resolved_ip = socket.gethostbyname(dev_serial)
                                    print(f"[Resolve] {serial} -> {resolved_ip} (DNS via DB serial {dev_serial})")
                                    return resolved_ip
                                except socket.gaierror:
                                    pass
                                print(f"[Resolve] {serial} -> {dev_serial} (Scaler DB serial, no IP)")
                                return dev_serial
                        except Exception:
                            pass
        
        # Check device_inventory.json for mgmt_ip
        inventory_file = _inventory_path()
        if inventory_file.exists():
            try:
                with open(inventory_file, 'r') as f:
                    inventory = json.load(f)
                search_lower = serial.lower()
                for key, dev in inventory.get('devices', {}).items():
                    dev_hostname = (dev.get('hostname') or key).lower()
                    dev_mgmt = dev.get('mgmt_ip', '') or ''
                    dev_serial = str(dev.get('serial') or '')
                    key_value = str(key)
                    if (search_lower == dev_hostname or
                        search_lower in dev_hostname or
                        dev_hostname in search_lower or
                        search_lower == key.lower()):
                        for candidate in (dev_mgmt, dev_serial, key_value):
                            if candidate and re.match(r'^\d+\.\d+\.\d+\.\d+$', candidate):
                                print(f"[Resolve] {serial} -> {candidate} (device_inventory)")
                                return candidate
            except Exception:
                pass
        
        return serial

    def _fetch_device_stack_live(self, host: str, username: str = 'dnroot', password: str = 'dnroot') -> dict:
        """SSH to device, run 'show system stack | no-more', parse and return components."""
        import paramiko
        import socket

        connect_host = self._resolve_serial_to_host(host)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            connect_host, username=username, password=password,
            timeout=30, look_for_keys=False, allow_agent=False
        )
        try:
            shell = client.invoke_shell(width=250, height=50)
            shell.settimeout(30)
            time.sleep(2)
            while shell.recv_ready():
                shell.recv(65535)
                time.sleep(0.1)

            shell.send('show system stack | no-more\n')
            time.sleep(3)
            output = ''
            for _ in range(20):
                if shell.recv_ready():
                    output += shell.recv(65535).decode('utf-8', errors='replace')
                    time.sleep(0.3)
                else:
                    time.sleep(0.5)
            raw = strip_ansi(output)

            components = []
            for line in raw.split('\n'):
                if '|' not in line:
                    continue
                parts = [p.strip() for p in line.split('|')]
                if len(parts) < 7:
                    continue
                name = parts[1]
                if not name or name.upper() in ('COMPONENT', '---', ''):
                    continue
                if name.startswith('-'):
                    continue
                components.append({
                    'name': name,
                    'hw_model': parts[2] if len(parts) > 2 else '-',
                    'revert': parts[4] if len(parts) > 4 else '-',
                    'current': parts[5] if len(parts) > 5 else '-',
                    'target': parts[6] if len(parts) > 6 else '-',
                })
            return {'components': components, 'raw_output': raw if not components else ''}
        finally:
            client.close()

    def _fetch_device_gitcommit(self, host: str, username: str = 'dnroot', password: str = 'dnroot') -> dict:
        """
        SSH to device, run 'run start shell' -> password -> 'cat .gitcommit', return hash.
        Falls back to direct SSH on port 2222 if run start shell fails.
        """
        import paramiko

        connect_host = self._resolve_serial_to_host(host)

        def try_port(port: int, use_cli_shell: bool) -> str | None:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(
                    connect_host, port=port, username=username, password=password,
                    timeout=30, look_for_keys=False, allow_agent=False
                )
            except Exception:
                return None
            try:
                shell = client.invoke_shell(width=250, height=50)
                shell.settimeout(30)
                time.sleep(2)
                while shell.recv_ready():
                    shell.recv(65535)
                    time.sleep(0.1)

                if use_cli_shell:
                    shell.send('run start shell\n')
                    # Wait specifically for Password: prompt (not #)
                    output = ''
                    for _ in range(30):
                        if shell.recv_ready():
                            output += shell.recv(65535).decode('utf-8', errors='replace')
                        time.sleep(0.3)
                        if 'assword' in output:
                            break
                    shell.send(password + '\n')
                    time.sleep(3)
                    # Drain post-login output (shell prompt)
                    while shell.recv_ready():
                        shell.recv(65535)
                        time.sleep(0.1)

                for git_path in ('/.gitcommit', '.gitcommit'):
                    shell.send(f'cat {git_path}\n')
                    time.sleep(1)
                    out = ''
                    for _ in range(12):
                        if shell.recv_ready():
                            out += shell.recv(65535).decode('utf-8', errors='replace')
                            time.sleep(0.2)
                        else:
                            time.sleep(0.25)
                    raw = strip_ansi(out)
                    for line in raw.split('\n'):
                        line = line.strip()
                        if not line or line.startswith('cat ') or line.endswith('#'):
                            continue
                        if 'No such file' in line or 'Permission denied' in line or 'ERROR' in line:
                            continue
                        m = re.match(r'^([a-fA-F0-9]{7,40}(?:-\S+)?)$', line)
                        if m:
                            return m.group(1)
                return None
            finally:
                client.close()

        result = try_port(22, use_cli_shell=True)
        if result:
            return {'git_commit': result}
        result = try_port(2222, use_cli_shell=False)
        if result:
            return {'git_commit': result}
        return {'git_commit': None, 'error': 'Could not fetch gitcommit from device'}

    def _fetch_lldp_neighbors(self, serial: str, ssh_host: str = None) -> dict:
        """
        SSH to device, run 'show lldp neighbors | no-more', parse and return neighbors.
        Returns { lldp_neighbors: [...], error?: str }.
        When ssh_host is provided, use it directly; otherwise resolve serial to host.
        """
        import paramiko
        import socket
        import time
        serial = (serial or '').strip()
        if not serial and not ssh_host:
            return {'lldp_neighbors': [], 'error': 'serial or ssh_host is required'}
        connect_host = (ssh_host or '').strip() or self._resolve_serial_to_host(serial)
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                connect_host,
                username='dnroot',
                password='dnroot',
                timeout=30,
                look_for_keys=False,
                allow_agent=False
            )
        except Exception as e:
            return {'lldp_neighbors': [], 'error': str(e)}
        try:
            shell = client.invoke_shell(width=250, height=50)
            shell.settimeout(30)
            time.sleep(2)
            while shell.recv_ready():
                shell.recv(65535)
                time.sleep(0.1)
            shell.send("show lldp neighbors | no-more\r\n")
            time.sleep(0.5)
            output = ""
            end_time = time.time() + 10
            idle_since = None
            while time.time() < end_time:
                if shell.recv_ready():
                    output += shell.recv(65535).decode('utf-8', errors='replace')
                    idle_since = None
                    last_line = output.rstrip().split('\n')[-1].strip() if output.rstrip() else ''
                    if last_line.endswith('#') or last_line.endswith('>'):
                        time.sleep(0.15)
                        if shell.recv_ready():
                            output += shell.recv(65535).decode('utf-8', errors='replace')
                        break
                else:
                    if idle_since is None:
                        idle_since = time.time()
                    elif output and (time.time() - idle_since) > 1.0:
                        break
                    time.sleep(0.1)
            raw_clean = strip_ansi(output)
            neighbors = _parse_lldp_output(raw_clean)
            client.close()
            return {'lldp_neighbors': neighbors, 'raw_output': raw_clean}
            client.close()
            return {'lldp_neighbors': [], 'raw_output': raw_clean}
        except Exception as e:
            try:
                client.close()
            except Exception:
                pass
            return {'lldp_neighbors': [], 'error': str(e)}
    
    def _save_lldp_to_cache(self, serial: str, lldp_neighbors: list):
        """
        Save LLDP neighbors to scaler-monitor cache (operational.json).
        Uses bidirectional matching to find the right device folder.
        """
        from datetime import datetime
        db_configs = Path('/home/dn/SCALER/db/configs')
        if not db_configs.exists():
            print(f"Cache dir not found: {db_configs}")
            return False
        
        search_term_lower = serial.lower()
        
        for device_dir in db_configs.iterdir():
            if device_dir.is_dir():
                dev_hostname = device_dir.name.lower()
                if _lldp_device_match(search_term_lower, dev_hostname, dev_hostname, '', '', ''):
                    op_file = device_dir / 'operational.json'
                    try:
                        _now_iso = datetime.now().isoformat()

                        def _mut_lldp(d, _n=lldp_neighbors, _ts=_now_iso):
                            d['lldp_neighbors'] = _n
                            d['lldp_neighbor_count'] = len(_n)
                            d['lldp_last_updated'] = _ts

                        ok, _ = _safe_update_ops(op_file, _mut_lldp, create_if_missing=True)
                        if ok:
                            print(f"✓ Saved {len(lldp_neighbors)} LLDP neighbors to cache: {op_file}")
                            return True
                        return False
                    except Exception as e:
                        print(f"Failed to save cache: {e}")
                        return False
        
        print(f"No matching device folder found for {serial}")
        return False
    
    def do_GET(self):
        try:
            self._do_GET_inner()
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                self._send_json({'error': f'Internal error: {e}'}, 500)
            except Exception:
                pass

    def _do_GET_inner(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/health':
            nm_health = {}
            try:
                nm = _get_mcp_client()
                if hasattr(nm, 'health'):
                    nm_health = nm.health()
                else:
                    nm_health = {'state': 'connected' if nm else 'disconnected'}
            except Exception as e:
                nm_health = {'state': 'error', 'last_error': str(e)}
            self._send_json({
                'status': 'ok',
                'network_mapper': nm_health,
                'uptime_s': int(time.time() - _server_start_time)
            })
            return

        elif parsed.path == '/api/discovery/status':
            # Get status of a job (per-user: caller can only see their own jobs)
            params = parse_qs(parsed.query)
            job_id = params.get('job_id', [None])[0]
            
            if job_id and job_id in jobs:
                job = jobs[job_id]
                requester = _request_owner(self) or 'global'
                if job.get('owner', 'global') != requester:
                    self._send_json({'error': 'Job not found'}, 404)
                    return
                self._send_json({
                    'job_id': job_id,
                    'status': job['status'],
                    'progress': job['progress'],
                    'output_lines': job['output_lines'][-20:],  # Last 20 lines
                    'result_file': job.get('result_file'),
                    'error': job.get('error')
                })
            else:
                self._send_json({'error': 'Job not found'}, 404)
        
        elif parsed.path == '/api/multi-bd/status':
            # Get status of a multi-BD job (per-user: caller can only see their own jobs)
            params = parse_qs(parsed.query)
            job_id = params.get('job_id', [None])[0]
            
            if job_id and job_id in jobs:
                job = jobs[job_id]
                requester = _request_owner(self) or 'global'
                if job.get('owner', 'global') != requester:
                    self._send_json({'error': 'Job not found'}, 404)
                    return
                # Strip ANSI codes for clean text matching in UI
                clean_lines = [strip_ansi(line) for line in job['output_lines']]
                self._send_json({
                    'job_id': job_id,
                    'status': job['status'],
                    'progress': job['progress'],
                    'message': clean_lines[-1] if clean_lines else '',
                    'output_lines': clean_lines,  # Include all lines for LLDP detection
                    'bd_count': job.get('bd_count', 0),
                    'result_file': job.get('result_file'),
                    'error': job.get('error')
                })
            else:
                self._send_json({'error': 'Job not found'}, 404)

        elif parsed.path in ('/api/discovery/find', '/api/multi-bd/find'):
            params = parse_qs(parsed.query)
            serial = (params.get('serial', [''])[0] or params.get('serial1', [''])[0] or '').strip()
            if not serial:
                self._send_json({'error': 'serial is required'}, 400)
                return
            requester = _request_owner(self) or 'global'
            desired_type = 'multi_bd' if parsed.path == '/api/multi-bd/find' else 'dnaas_discovery'
            latest = None
            with job_lock:
                for jid, j in jobs.items():
                    if j.get('type') != desired_type:
                        continue
                    if j.get('owner', 'global') != requester:
                        continue
                    if (j.get('serial') or '') != serial and (j.get('serial1') or '') != serial:
                        continue
                    if not latest or j.get('created_at', 0) > latest[1].get('created_at', 0):
                        latest = (jid, j)
            if not latest:
                self._send_json({'job_id': None, 'status': 'none'})
                return
            jid, j = latest
            self._send_json({
                'job_id': jid,
                'status': j.get('status', 'unknown'),
                'progress': j.get('progress', 0),
                'output_lines': [strip_ansi(line) for line in j.get('output_lines', [])],
                'result_file': j.get('result_file'),
                'bd_count': j.get('bd_count', 0),
                'error': j.get('error'),
                'created_at': j.get('created_at', 0),
            })
        
        elif parsed.path == '/api/enable-lldp/status':
            # Get status of an LLDP enable job (per-user: caller can only see their own jobs)
            params = parse_qs(parsed.query)
            job_id = params.get('job_id', [None])[0]
            
            if job_id and job_id in jobs:
                job = jobs[job_id]
                requester = _request_owner(self) or 'global'
                if job.get('owner', 'global') != requester:
                    # Never leak the existence of another user's job
                    self._send_json({'error': 'Job not found'}, 404)
                    return
                self._send_json({
                    'job_id': job_id,
                    'status': job['status'],
                    'progress': job['progress'],
                    'output_lines': job['output_lines'],  # Send all lines for detailed feedback
                    'interfaces_enabled': job.get('interfaces_enabled', 0),
                    'interfaces': job.get('interfaces', []),
                    'already_configured': job.get('already_configured', False),
                    'queued_behind': job.get('queued_behind'),
                    'device_key': job.get('device_key'),
                    'resolve': job.get('resolve'),
                    'preflight': job.get('preflight'),
                    'error': job.get('error')
                })
            else:
                self._send_json({'error': 'Job not found'}, 404)
        
        elif parsed.path == '/api/enable-lldp/find':
            # Reconnect helper: given a serial, return the latest LLDP job
            # for THIS user (owner) and that serial. Lets the client
            # transparently re-attach to an in-flight job after a tab
            # reload, or skip resubmission if the job is still running.
            params = parse_qs(parsed.query)
            serial = (params.get('serial', [''])[0] or '').strip()
            if not serial:
                self._send_json({'error': 'serial is required'}, 400)
                return
            requester = _request_owner(self) or 'global'
            latest = None
            with job_lock:
                for jid, j in jobs.items():
                    if j.get('type') != 'enable_lldp':
                        continue
                    if j.get('owner', 'global') != requester:
                        continue
                    if (j.get('serial') or '') != serial:
                        continue
                    if not latest or j.get('created_at', 0) > latest[1].get('created_at', 0):
                        latest = (jid, j)
            if not latest:
                self._send_json({'job_id': None, 'status': 'none'})
                return
            jid, j = latest
            self._send_json({
                'job_id': jid,
                'status': j.get('status', 'unknown'),
                'progress': j.get('progress', 0),
                'output_lines': j.get('output_lines', []),
                'interfaces_enabled': j.get('interfaces_enabled', 0),
                'interfaces': j.get('interfaces', []),
                'already_configured': j.get('already_configured', False),
                'error': j.get('error'),
                'created_at': j.get('created_at', 0),
                'queued_behind': j.get('queued_behind'),
                'device_key': j.get('device_key'),
                'resolve': j.get('resolve'),
                'preflight': j.get('preflight'),
            })

        elif parsed.path == '/api/enable-lldp/cancel':
            # Cancel an LLDP enable job and close SSH session (per-user)
            params = parse_qs(parsed.query)
            job_id = params.get('job_id', [None])[0]
            
            if job_id and job_id in jobs:
                job = jobs[job_id]
                requester = _request_owner(self) or 'global'
                if job.get('owner', 'global') != requester:
                    self._send_json({'error': 'Job not found'}, 404)
                    return
                job['cancelled'] = True
                job['status'] = 'cancelled'
                job['error'] = 'Cancelled by user'
                job['output_lines'].append('⚠ LLDP enable cancelled by user')
                device_key = job.get('device_key', '')
                if device_key in lldp_device_queues:
                    lldp_device_queues[device_key] = [jid for jid in lldp_device_queues[device_key] if jid != job_id]
                _clear_lldp_current(device_key, job_id)
                
                # Close SSH client if stored - be aggressive
                if '_ssh_client' in job:
                    try:
                        ssh_client = job['_ssh_client']
                        # Close the transport first to interrupt any pending I/O
                        if ssh_client.get_transport():
                            ssh_client.get_transport().close()
                        ssh_client.close()
                        job['output_lines'].append('✓ SSH session closed')
                    except Exception as e:
                        job['output_lines'].append(f'⚠ SSH close error: {e}')
                
                _persist_job(job_id, dict(job))
                self._send_json({'job_id': job_id, 'status': 'cancelled', 'message': 'LLDP enable cancelled'})
            else:
                self._send_json({'error': 'Job not found'}, 404)
        
        elif parsed.path.startswith('/api/multi-bd/file/'):
            # Serve a multi-BD result file by name -- ONLY from caller's bucket.
            filename = parsed.path.replace('/api/multi-bd/file/', '')
            if '/' in filename or '\\' in filename or '..' in filename:
                self._send_json({'error': 'Invalid filename'}, 400)
                return
            if (filename.startswith('multi_bd_') or filename.startswith('dnaas_')) and filename.endswith('.json'):
                _maybe_migrate_legacy_output()
                owner = _request_owner(self)
                owner_dir = _user_output_dir(owner)
                filepath = owner_dir / filename
                if filepath.exists() and filepath.is_file():
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                        self._send_json(data)
                    except Exception as e:
                        self._send_json({'error': f'Failed to read file: {str(e)}'}, 500)
                else:
                    self._send_json({'error': 'File not found'}, 404)
            else:
                self._send_json({'error': 'Invalid filename'}, 400)
        
        elif parsed.path == '/api/devices/list':
            devices = []
            try:
                all_nm = _mcp_call('list_devices')
                for dev in (all_nm or []):
                    dev_name = getattr(dev, 'name', str(dev))
                    hostname = dev_name.split('_dev_')[0] if '_dev_' in dev_name else dev_name.split('_priv_')[0] if '_priv_' in dev_name else dev_name
                    devices.append({
                        'id': hostname,
                        'hostname': hostname,
                        'full_name': dev_name,
                        'ip': '',
                        'platform': 'dnos'
                    })
            except Exception as e:
                print(f"[devices/list] MCP list failed: {e}")
            if not devices:
                inv_file = _inventory_path()
                if inv_file.exists():
                    try:
                        with open(inv_file) as f:
                            inv = json.load(f)
                        for key, dev in inv.get('devices', {}).items():
                            devices.append({
                                'id': key,
                                'hostname': dev.get('hostname', key),
                                'ip': dev.get('mgmt_ip', ''),
                                'platform': 'dnos'
                            })
                    except Exception:
                        pass
            self._send_json({'devices': devices, 'count': len(devices)})

        elif parsed.path.startswith('/api/device/') and '/resolve' in parsed.path:
            path_parts = parsed.path.split('/')
            if len(path_parts) >= 5:
                from urllib.parse import unquote
                device_name = unquote(path_parts[3])
                result = _resolve_device_mgmt(device_name)
                self._send_json(result)
            else:
                self._send_json({'error': 'Invalid path'}, 400)

        elif parsed.path.startswith('/api/device/') and '/management-interfaces' in parsed.path:
            # GET /api/device/<name>/management-interfaces
            # Returns parsed management interface data, including ipv4_addresses[]
            # the XRAY capture flow needs to resolve a DUT host without prompting.
            path_parts = parsed.path.split('/')
            if len(path_parts) < 5:
                self._send_json({'error': 'Invalid path'}, 400)
                return
            from urllib.parse import unquote
            device_name = unquote(path_parts[3])
            mgmt_text = ''
            mgmt_ip = ''
            interfaces = []
            source = ''
            try:
                nm = _get_mcp_client()
                mgmt_text = nm._call_tool('get_device_management_interfaces',
                                          {'device_name': device_name}) or ''
            except Exception as e:
                print(f"[mgmt-iface] MCP lookup failed for {device_name}: {e}")

            if mgmt_text and 'not found' not in str(mgmt_text).lower():
                source = 'network-mapper'
                mgmt_ip = _extract_mgmt_ip(mgmt_text)
                # Build a structured interfaces[] view from the raw markdown so
                # serve.py / xray-popup can consume {name, ipv4_addresses[]}.
                current_iface = None
                import re as _re
                for line in str(mgmt_text).split('\n'):
                    stripped = line.strip()
                    if not stripped:
                        continue
                    m_name = _re.match(r'^[*\-+]?\s*(?:interface\s*[:=]?\s*)?'
                                       r'([A-Za-z0-9_\-]+(?:\d+/\d+/\d+(?:\.\d+)?)?)'
                                       r'\s*[:\-]?\s*$', stripped)
                    if 'mgmt' in stripped.lower() and not _re.search(r'\d+\.\d+\.\d+\.\d+', stripped):
                        for tok in stripped.split():
                            if 'mgmt' in tok.lower() and len(tok) < 40:
                                current_iface = {'name': tok.strip('*-+:'), 'ipv4_addresses': []}
                                interfaces.append(current_iface)
                                break
                    ip_match = _re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d{1,2})?)', stripped)
                    if ip_match:
                        if current_iface is None:
                            current_iface = {'name': 'mgmt0', 'ipv4_addresses': []}
                            interfaces.append(current_iface)
                        current_iface['ipv4_addresses'].append(ip_match.group(1))

            if not mgmt_ip:
                # Inventory fallback so the endpoint never returns 404 for
                # devices we have a recorded mgmt_ip for.
                try:
                    inv_file = _inventory_path()
                    if inv_file.exists():
                        with open(inv_file) as f:
                            inv = json.load(f)
                        search_lower = device_name.lower()
                        for key, dev in inv.get('devices', {}).items():
                            host_lower = (dev.get('hostname') or key).lower()
                            if (search_lower == host_lower or
                                search_lower in host_lower or
                                host_lower in search_lower or
                                search_lower == key.lower()):
                                ip = (dev.get('mgmt_ip') or '').split('/')[0]
                                if ip:
                                    mgmt_ip = ip
                                    if not interfaces:
                                        interfaces.append({'name': 'mgmt0',
                                                           'ipv4_addresses': [ip]})
                                    source = source or 'inventory'
                                    break
                except Exception:
                    pass

            if not interfaces and mgmt_ip:
                interfaces.append({'name': 'mgmt0', 'ipv4_addresses': [mgmt_ip]})

            self._send_json({
                'device': device_name,
                'mgmt_ip': mgmt_ip,
                'interfaces': interfaces,
                'source': source or 'unknown',
                'raw': mgmt_text if isinstance(mgmt_text, str) else str(mgmt_text),
            })
            return

        elif parsed.path.startswith('/api/device/') and '/lldp' in parsed.path:
            # GET endpoint: /api/device/<serial>/lldp - fetch LLDP from scaler-monitor cache
            # Optional query: ?ssh_host=IP for direct SSH when serial does not resolve
            # Extract serial from path: /api/device/SERIAL/lldp
            path_parts = parsed.path.split('/')
            # path_parts = ['', 'api', 'device', 'SERIAL', 'lldp']
            if len(path_parts) >= 5:
                from urllib.parse import unquote
                serial = unquote(path_parts[3])
                qs = parse_qs(parsed.query or '')
                ssh_host = (qs.get('ssh_host', [None]) or [None])[0]
                
                # Priority: NetworkMapper (freshest) > Scaler DB > device_inventory > SSH
                found_device = None
                neighbors = []
                raw_output = ""
                search_term_lower = serial.lower()
                lldp_source = None
                
                # 1. Try NetworkMapper MCP first (auto-reset on SSE/connection failure)
                try:
                    nm_neighbors = _mcp_call('get_device_lldp', serial)
                    if nm_neighbors:
                        found_device = serial
                    else:
                        # Fuzzy: find NM device whose name contains the search term
                        # Normalize underscores/hyphens for matching (CL-PE-4 vs CL_PE-4)
                        import re as _re
                        norm = lambda s: _re.sub(r'[-_]', '', s.lower())
                        search_norm = norm(serial)
                        try:
                            all_nm = _mcp_call('list_devices')
                            for dev in (all_nm or []):
                                dev_name = getattr(dev, 'name', str(dev))
                                dev_norm = norm(dev_name)
                                if search_norm in dev_norm or dev_norm in search_norm:
                                    nm_neighbors = _mcp_call('get_device_lldp', dev_name)
                                    if nm_neighbors:
                                        found_device = dev_name
                                        print(f"[LLDP] Fuzzy match: '{serial}' -> '{dev_name}'")
                                        break
                        except Exception:
                            pass
                    if nm_neighbors:
                        lldp_source = 'network-mapper'
                        for n in nm_neighbors:
                            neighbors.append({
                                'interface': n.local_interface,
                                'neighbor': n.neighbor_name,
                                'remote_port': n.neighbor_interface
                            })
                        print(f"[LLDP] Found {len(neighbors)} neighbors via NetworkMapper for {found_device or serial}")
                except Exception as e:
                    print(f"[LLDP] NetworkMapper lookup skipped: {e}")
                
                # 2. Fallback: SCALER operational.json
                if not neighbors:
                    db_configs = Path('/home/dn/SCALER/db/configs')
                    if db_configs.exists():
                        for device_dir in db_configs.iterdir():
                            if device_dir.is_dir():
                                op_file = device_dir / 'operational.json'
                                if op_file.exists():
                                    try:
                                        op_data = _safe_read_ops(op_file)
                                        dev_hostname = op_data.get('hostname') or device_dir.name
                                        dev_serial = op_data.get('serial_number') or ''
                                        dev_connection_ip = op_data.get('connection_ip') or ''
                                        dir_name = device_dir.name.lower()

                                        if _lldp_device_match(search_term_lower, dev_hostname, dir_name, dev_serial, dev_connection_ip, serial):
                                            found_device = dev_hostname
                                            lldp_source = 'scaler-db'
                                            lldp_data = op_data.get('lldp_neighbors', [])
                                            raw_output = op_data.get('lldp_raw', '')
                                            for n in lldp_data:
                                                neighbors.append({
                                                    'interface': n.get('local_interface') or n.get('interface', ''),
                                                    'neighbor': n.get('neighbor_device') or n.get('neighbor', ''),
                                                    'remote_port': n.get('neighbor_port') or n.get('remote_port', '')
                                                })
                                            break
                                    except Exception as e:
                                        print(f"Error reading {op_file}: {e}")
                
                # 3. Fallback: device_inventory.json
                if not neighbors:
                    inventory_file = _inventory_path()
                    if inventory_file.exists():
                        try:
                            with open(inventory_file, 'r') as f:
                                inventory = json.load(f)
                            devices = inventory.get('devices', {})
                            for device_key, device_data in devices.items():
                                dev_hostname = device_data.get('hostname', device_key)
                                if _lldp_device_match(search_term_lower, dev_hostname, device_key, '', '', ''):
                                    found_device = dev_hostname
                                    lldp_source = 'device-inventory'
                                    for n in device_data.get('lldp_neighbors', []):
                                        neighbors.append({
                                            'interface': n.get('local_interface') or n.get('interface', ''),
                                            'neighbor': n.get('neighbor_device') or n.get('neighbor', ''),
                                            'remote_port': n.get('neighbor_port') or n.get('remote_port', '')
                                        })
                                    break
                        except Exception as e:
                            print(f"Error reading device_inventory.json: {e}")
                
                # If no cached data found, try live SSH and SAVE to cache
                if not neighbors and serial:
                    print(f"No cached LLDP for {serial}, trying live SSH + cache update...")
                    try:
                        live_result = self._fetch_lldp_neighbors(serial, ssh_host=ssh_host)
                        if live_result.get('lldp_neighbors'):
                            lldp_list = live_result['lldp_neighbors']
                            
                            # Save to scaler cache (operational.json)
                            self._save_lldp_to_cache(serial, lldp_list)
                            
                            for n in lldp_list:
                                neighbors.append({
                                    'interface': n.get('local_interface') or n.get('interface', ''),
                                    'neighbor': n.get('neighbor_device') or n.get('neighbor', ''),
                                    'remote_port': n.get('neighbor_port') or n.get('remote_port', '')
                                })
                            raw_output = live_result.get('raw_output', '')
                            found_device = serial
                            self._send_json({
                                'neighbors': neighbors,
                                'raw_output': raw_output,
                                'device': found_device,
                                'cached': False,
                                'live': True,
                                'source': 'live-ssh',
                                'cache_updated': True
                            })
                            return
                    except Exception as e:
                        print(f"Live SSH fallback failed: {e}")
                
                self._send_json({
                    'neighbors': neighbors,
                    'raw_output': raw_output,
                    'device': found_device or serial,
                    'cached': True,
                    'source': lldp_source or 'unknown'
                })
            else:
                self._send_json({'error': 'Invalid path format'}, 400)
        
        elif parsed.path == '/api/discovery/list':
            # List output files (both dnaas_path and multi_bd) -- per-user only.
            # Caller sees ONLY files inside their own bucket (or the global
            # bucket when unauthenticated). No cross-user listing.
            _maybe_migrate_legacy_output()
            owner = _request_owner(self)
            owner_dir = _user_output_dir(owner)
            files = []
            if owner_dir.exists():
                dnaas_files = list(owner_dir.glob('dnaas_path_*.json'))
                multi_bd_files = list(owner_dir.glob('multi_bd_*.json'))
                all_files = dnaas_files + multi_bd_files
                # Sort by modification time (newest first) and take top 20
                for f in sorted(all_files, key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
                    files.append({
                        'name': f.name,
                        'path': str(f),
                        'size': f.stat().st_size,
                        'modified': f.stat().st_mtime
                    })
            self._send_json({'files': files})
        
        elif parsed.path.startswith('/api/discovery/file/'):
            # Serve a result file by name -- ONLY if it lives in the caller's bucket.
            filename = parsed.path.replace('/api/discovery/file/', '')
            # Security: allow both dnaas_path_*.json and multi_bd_*.json files
            valid_prefix = filename.startswith('dnaas_path_') or filename.startswith('multi_bd_') or filename.startswith('dnaas_')
            # Also reject path traversal
            if '/' in filename or '\\' in filename or '..' in filename:
                self._send_json({'error': 'Invalid filename'}, 400)
                return
            if valid_prefix and filename.endswith('.json'):
                _maybe_migrate_legacy_output()
                owner = _request_owner(self)
                owner_dir = _user_output_dir(owner)
                filepath = owner_dir / filename
                if filepath.exists() and filepath.is_file():
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                        self._send_json(data)
                    except Exception as e:
                        self._send_json({'error': f'Failed to read file: {str(e)}'}, 500)
                else:
                    self._send_json({'error': 'File not found'}, 404)
            else:
                self._send_json({'error': 'Invalid filename'}, 400)
        
        # ================================================================
        # Network Mapper — status endpoint (per-user)
        # ================================================================
        elif parsed.path == '/api/network-mapper/status':
            params = parse_qs(parsed.query)
            jid = params.get('job_id', [None])[0]
            if not jid or jid not in nm_jobs:
                self._send_json({'error': 'Job not found'}, 404)
                return
            with nm_job_lock:
                job = nm_jobs[jid]
                requester = self.headers.get('X-User', 'default') or 'default'
                if job.get('owner', 'default') != requester:
                    self._send_json({'error': 'Job not found'}, 404)
                    return
                self._send_json({
                    'status': job['status'],
                    'progress': job['progress'],
                    'devices': job.get('devices', {}),
                    'links': job.get('links', []),
                    'errors': job.get('errors', []),
                    'log': job.get('log', [])[-50:]  # last 50 log lines
                })

        else:
            self._send_json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        try:
            self._do_POST_inner()
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                self._send_json({'error': f'Internal error: {e}'}, 500)
            except Exception:
                pass

    def _do_POST_inner(self):
        global job_counter, nm_job_counter
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/devices/resolve-batch':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return
            names = data.get('names', [])
            if not names:
                self._send_json({'error': 'names array required'}, 400)
                return

            results = {}
            for device_name in names:
                results[device_name] = _resolve_device_mgmt(device_name)

            self._send_json({'resolved': results})
            return

        if parsed.path == '/api/discovery/start':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return
            
            serial1 = (data.get('serial1') or '').strip()
            serial2 = (data.get('serial2') or '').strip()
            
            if not serial1:
                self._send_json({'error': 'serial1 is required'}, 400)
                return
            
            owner = _request_owner(self)
            owner_dir = _user_output_dir(owner)

            # Create job
            _cleanup_old_discovery_jobs()
            with job_lock:
                job_counter += 1
                job_id = f"job_{job_counter}"
                jobs[job_id] = {
                    'id': job_id,
                    'type': 'dnaas_discovery',
                    'serial': serial1,
                    'serial2': serial2,
                    'status': 'starting',
                    'progress': 0,
                    'output_lines': [],
                    'result_file': None,
                    'error': None,
                    'owner': owner or 'global',
                    'output_dir': str(owner_dir),
                    'created_at': time.time()
                }
                snapshot = dict(jobs[job_id])
            _persist_job(job_id, snapshot)
            
            # Start discovery in background thread
            def run_discovery():
                job = jobs[job_id]
                job['status'] = 'running'
                job['progress'] = 10
                job['output_lines'].append(f"Starting hybrid discovery for {serial1}...")
                _persist_job(job_id, dict(job))

                def _job_log(message: str):
                    job['output_lines'].append(message)
                    _persist_job(job_id, dict(job))

                requested_backend = (data.get('backend') or data.get('discovery_backend') or '').strip().lower()
                use_dnos_mcp = data.get('use_dnos_mcp', True) is not False and requested_backend != 'legacy'
                if use_dnos_mcp and not serial2:
                    try:
                        job['progress'] = 15
                        mcp_file = _try_dnos_mcp_discovery(
                            serial1,
                            owner_dir,
                            "dnaas_path",
                            log=_job_log,
                        )
                        job['status'] = 'completed'
                        job['progress'] = 100
                        job['result_file'] = f"/api/discovery/file/{mcp_file.name}"
                        job['output_lines'].append("[OK] Discovery completed through dnos-config MCP")
                        _persist_job(job_id, dict(job))
                        return
                    except Exception as mcp_exc:
                        job['output_lines'].append(
                            f"[WARN] dnos-config MCP discovery unavailable, falling back to legacy script: {mcp_exc}"
                        )
                        _persist_job(job_id, dict(job))
                
                # Use NEW hybrid script: cached PE data + live DNAAS SSH only
                cmd = ['python3', str(DISCOVERY_SCRIPT), serial1]
                if serial2:
                    cmd.append(serial2)
                    job['output_lines'].append(f"Second device: {serial2}")
                job['output_lines'].append(f"Using hybrid mode: cached PE + minimal DNAAS SSH (owner={owner or 'global'})...")
                
                # Per-user output isolation: tell the discovery script to
                # write JSON/XLSX/TXT into THIS user's bucket only.
                env = os.environ.copy()
                env['DNAAS_OUTPUT_DIR'] = str(owner_dir)

                try:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        env=env,
                    )
                    
                    # Store process handle for cancellation
                    job_processes[job_id] = process
                    job['progress'] = 20
                    
                    for line in iter(process.stdout.readline, ''):
                        line = line.strip()
                        if line:
                            job['output_lines'].append(line)
                            # Update progress based on output
                            if 'Connecting' in line:
                                job['progress'] = min(job['progress'] + 10, 80)
                            elif 'LLDP' in line:
                                job['progress'] = min(job['progress'] + 5, 85)
                            elif 'saved' in line.lower():
                                job['progress'] = 90
                            if len(job['output_lines']) % 10 == 0:
                                _persist_job(job_id, dict(job))
                    
                    process.wait()
                    
                    if process.returncode == 0:
                        job['status'] = 'completed'
                        job['progress'] = 100
                        # Find the latest output file (only inside owner's bucket)
                        latest = max(owner_dir.glob('dnaas_path_*.json'), key=lambda f: f.stat().st_mtime, default=None)
                        if latest:
                            # Return web-accessible URL instead of filesystem path
                            job['result_file'] = f"/api/discovery/file/{latest.name}"
                            job['output_lines'].append(f"[OK] Output saved: {latest.name}")
                    else:
                        job['status'] = 'failed'
                        # Check output lines for specific error messages
                        error_msg = f"Process exited with code {process.returncode}"
                        for line in job['output_lines'][-10:]:
                            if 'Failed to connect' in line or 'Connection failed' in line:
                                error_msg = f"Connection failed to device"
                                break
                            elif 'No devices discovered' in line:
                                error_msg = "No devices discovered - connection may have failed"
                                break
                        job['error'] = error_msg
                        job['output_lines'].append(f"✗ Discovery failed: {error_msg}")
                
                except Exception as e:
                    job['status'] = 'failed'
                    job['error'] = str(e)
                    job['output_lines'].append(f"✗ Error: {e}")
                finally:
                    _persist_job(job_id, dict(job))
                    # Clean up process handle
                    if job_id in job_processes:
                        del job_processes[job_id]
            
            thread = threading.Thread(target=run_discovery, daemon=True)
            thread.start()
            
            self._send_json({'job_id': job_id, 'status': 'started'})
        
        elif parsed.path == '/api/discovery/cancel':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return
            
            job_id = data.get('job_id', '').strip()
            
            if not job_id:
                self._send_json({'error': 'job_id is required'}, 400)
                return
            
            if job_id not in jobs:
                self._send_json({'error': 'Job not found'}, 404)
                return
            
            job = jobs[job_id]

            # Owner gate: only the user who started the job can cancel it.
            requester = _request_owner(self) or 'global'
            if job.get('owner', 'global') != requester:
                self._send_json({'error': 'Job not found'}, 404)
                return

            # Try to terminate the process
            if job_id in job_processes:
                try:
                    process = job_processes[job_id]
                    process.terminate()
                    process.wait(timeout=2)
                except:
                    try:
                        process.kill()
                    except:
                        pass
                finally:
                    if job_id in job_processes:
                        del job_processes[job_id]
            
            job['status'] = 'cancelled'
            job['error'] = 'Cancelled by user'
            job['output_lines'].append('[CANCELLED] Discovery cancelled by user')
            _persist_job(job_id, dict(job))
            
            self._send_json({'job_id': job_id, 'status': 'cancelled', 'message': 'Discovery cancelled'})
        
        elif parsed.path == '/api/multi-bd/start':
            # Start Multi-BD discovery
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return
            
            serial = (data.get('serial') or '').strip()
            
            if not serial:
                self._send_json({'error': 'serial is required'}, 400)
                return

            owner = _request_owner(self)
            owner_dir = _user_output_dir(owner)

            # Create job
            _cleanup_old_discovery_jobs()
            with job_lock:
                job_counter += 1
                job_id = f"multibd_{job_counter}"
                jobs[job_id] = {
                    'id': job_id,
                    'type': 'multi_bd',
                    'serial': serial,
                    'status': 'starting',
                    'progress': 0,
                    'output_lines': [],
                    'result_file': None,
                    'error': None,
                    'bd_count': 0,
                    'owner': owner or 'global',
                    'output_dir': str(owner_dir),
                    'created_at': time.time()
                }
                snapshot = dict(jobs[job_id])
            _persist_job(job_id, snapshot)
            
            # Start multi-BD discovery in background thread
            def run_multi_bd_discovery():
                job = jobs[job_id]
                job['status'] = 'running'
                job['progress'] = 10
                job['output_lines'].append(f"Starting Multi-BD discovery for {serial} (owner={owner or 'global'})...")
                start_ts = time.time()
                _persist_job(job_id, dict(job))

                def _job_log(message: str):
                    job['output_lines'].append(message)
                    _persist_job(job_id, dict(job))

                requested_backend = (data.get('backend') or data.get('discovery_backend') or '').strip().lower()
                use_dnos_mcp = data.get('use_dnos_mcp', True) is not False and requested_backend != 'legacy'
                if use_dnos_mcp:
                    try:
                        job['progress'] = 15
                        mcp_file = _try_dnos_mcp_discovery(
                            serial,
                            owner_dir,
                            "multi_bd",
                            log=_job_log,
                        )
                        with open(mcp_file, "r", encoding="utf-8") as fh:
                            mcp_topology = json.load(fh)
                        job['status'] = 'completed'
                        job['progress'] = 100
                        job['bd_count'] = len(mcp_topology.get('metadata', {}).get('bridge_domains') or [])
                        job['result_file'] = f"/api/multi-bd/file/{mcp_file.name}"
                        job['output_lines'].append("[OK] Multi-BD discovery completed through dnos-config MCP")
                        _persist_job(job_id, dict(job))
                        return
                    except Exception as mcp_exc:
                        job['output_lines'].append(
                            f"[WARN] dnos-config MCP Multi-BD discovery unavailable, falling back to legacy script: {mcp_exc}"
                        )
                        _persist_job(job_id, dict(job))
                
                # Use --multi-bd flag for multi-BD discovery (MUST come before positional args)
                cmd = ['python3', str(DISCOVERY_SCRIPT), '--multi-bd', serial]
                job['output_lines'].append("Discovering ALL Bridge Domains...")

                env = os.environ.copy()
                env['DNAAS_OUTPUT_DIR'] = str(owner_dir)

                try:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        env=env,
                    )
                    
                    job_processes[job_id] = process
                    job['progress'] = 20
                    
                    for line in iter(process.stdout.readline, ''):
                        line = line.strip()
                        if line:
                            job['output_lines'].append(line)
                            # Update progress based on output
                            if 'Connecting' in line:
                                job['progress'] = min(job['progress'] + 5, 40)
                            elif 'Bridge Domain' in line or 'BD:' in line:
                                job['progress'] = min(job['progress'] + 5, 60)
                            elif 'LLDP' in line:
                                job['progress'] = min(job['progress'] + 3, 75)
                            elif 'Discovered' in line:
                                # Try to extract BD count
                                bd_match = re.search(r'Discovered\s+(\d+)\s+Bridge', line)
                                if bd_match:
                                    job['bd_count'] = int(bd_match.group(1))
                                job['progress'] = 85
                            elif 'saved' in line.lower():
                                job['progress'] = 95
                            if len(job['output_lines']) % 10 == 0:
                                _persist_job(job_id, dict(job))
                    
                    process.wait()
                    
                    if process.returncode == 0:
                        job['status'] = 'completed'
                        job['progress'] = 100
                        # Find output file created during THIS run (after start_ts) inside owner's bucket
                        multi_bd_files = list(owner_dir.glob('multi_bd_*.json'))
                        dnaas_files = list(owner_dir.glob('dnaas_path_*.json'))
                        all_files = multi_bd_files + dnaas_files
                        recent = [f for f in all_files if f.stat().st_mtime >= start_ts]
                        latest = max(recent, key=lambda f: f.stat().st_mtime, default=None)
                        if not latest:
                            latest = max(all_files, key=lambda f: f.stat().st_mtime, default=None)
                        if latest:
                            job['result_file'] = f"/api/multi-bd/file/{latest.name}"
                            job['output_lines'].append(f"[OK] Multi-BD output saved: {latest.name}")
                    else:
                        job['status'] = 'failed'
                        job['error'] = f"Process exited with code {process.returncode}"
                        job['output_lines'].append(f"✗ Multi-BD discovery failed")
                
                except Exception as e:
                    job['status'] = 'failed'
                    job['error'] = str(e)
                    job['output_lines'].append(f"✗ Error: {e}")
                finally:
                    _persist_job(job_id, dict(job))
                    if job_id in job_processes:
                        del job_processes[job_id]
            
            thread = threading.Thread(target=run_multi_bd_discovery, daemon=True)
            thread.start()
            
            self._send_json({'job_id': job_id, 'status': 'started', 'message': 'Multi-BD discovery started'})
        
        elif parsed.path == '/api/multi-bd/cancel':
            # Cancel a Multi-BD discovery job
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return
            
            job_id = data.get('job_id', '').strip()
            
            if not job_id:
                self._send_json({'error': 'job_id is required'}, 400)
                return
            
            if job_id not in jobs:
                self._send_json({'error': 'Job not found'}, 404)
                return
            
            job = jobs[job_id]

            # Owner gate: only the user who started the job can cancel it.
            requester = _request_owner(self) or 'global'
            if job.get('owner', 'global') != requester:
                self._send_json({'error': 'Job not found'}, 404)
                return

            # Try to terminate the process
            if job_id in job_processes:
                try:
                    process = job_processes[job_id]
                    process.terminate()
                    process.wait(timeout=2)
                except:
                    try:
                        process.kill()
                    except:
                        pass
                finally:
                    if job_id in job_processes:
                        del job_processes[job_id]
            
            job['status'] = 'cancelled'
            job['error'] = 'Cancelled by user'
            job['output_lines'].append('⚠ Multi-BD discovery cancelled by user')
            _persist_job(job_id, dict(job))
            
            self._send_json({'job_id': job_id, 'status': 'cancelled', 'message': 'Multi-BD discovery cancelled'})
        
        elif parsed.path == '/api/enable-lldp':
            # Enable LLDP and admin-state on all interfaces of a device (job-based for real-time updates)
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return
            
            serial = data.get('serial', '').strip()
            ssh_host = (data.get('ssh_host') or '').strip()
            username = data.get('username', 'dnroot')
            password = data.get('password', 'dnroot')
            skip_host_key = data.get('skipHostKey', False)
            conflict_action = (data.get('conflict_action') or '').strip().lower()
            
            if not serial:
                self._send_json({'error': 'serial is required'}, 400)
                return
            
            owner = _request_owner(self) or 'global'
            resolve_info = _resolve_discovery_target(serial, ssh_hint=ssh_host or None)
            resolved_target = resolve_info.get('target') or serial
            device_key = resolved_target.lower()
            preflight = _tcp_preflight(resolved_target, timeout=3.0) if resolved_target else {'reachable': False, 'error': 'no target'}
            if not preflight.get('reachable'):
                self._send_json({
                    'error': f"Cannot reach {serial} via {resolved_target}: {preflight.get('error', 'unreachable')}",
                    'preflight': preflight,
                    'resolve': resolve_info,
                }, 400)
                return
            _cleanup_old_discovery_jobs()
            with job_lock:
                conflict = _find_active_lldp_for_device(device_key)
                if conflict and conflict_action not in ('watch', 'queue'):
                    conflict_id, conflict_job = conflict
                    self._send_json({
                        'error': 'LLDP operation already running for this device',
                        'conflict': True,
                        'existing_job_id': conflict_id,
                        'existing_status': conflict_job.get('status'),
                        'existing_owner': conflict_job.get('owner', 'global'),
                        'same_owner': conflict_job.get('owner', 'global') == owner,
                        'device_key': device_key,
                        'resolve': resolve_info,
                        'preflight': preflight,
                        'options': ['watch', 'queue'],
                    }, 409)
                    return
                if conflict and conflict_action == 'watch':
                    conflict_id, conflict_job = conflict
                    self._send_json({
                        'job_id': conflict_id,
                        'status': conflict_job.get('status', 'running'),
                        'message': f'Watching existing LLDP job for {serial}',
                        'conflict': True,
                        'watching': True,
                        'resolve': resolve_info,
                    })
                    return
                # User-scoped job id: prevents collision across concurrent
                # users clicking Enable LLDP in the same millisecond and
                # makes the id self-describing for debugging.
                # Sanitize owner for id: alnum + dot/underscore/dash only.
                safe_owner = re.sub(r'[^a-zA-Z0-9._-]', '_', owner)[:32] or 'global'
                job_id = f"lldp_{safe_owner}_{int(time.time() * 1000)}"
                # Extra collision guard (two requests in the same ms).
                suffix = 0
                while job_id in jobs:
                    suffix += 1
                    job_id = f"lldp_{safe_owner}_{int(time.time() * 1000)}_{suffix}"
                jobs[job_id] = {
                    'id': job_id,
                    'type': 'enable_lldp',
                    'serial': serial,
                    'owner': owner,
                    'status': 'queued' if conflict and conflict_action == 'queue' else 'running',
                    'progress': 0,
                    'output_lines': [],
                    'started_at': datetime.now().isoformat(),
                    'interfaces_enabled': 0,
                    'created_at': time.time(),
                    'device_key': device_key,
                    'resolved_target': resolved_target,
                    'resolve': resolve_info,
                    'preflight': preflight,
                    '_runtime_username': username,
                    '_runtime_password': password,
                    '_runtime_skip_host_key': skip_host_key,
                    '_runtime_ssh_host': ssh_host or None,
                }
                if conflict and conflict_action == 'queue':
                    jobs[job_id]['queued_behind'] = conflict[0]
                    jobs[job_id]['output_lines'].append(f"[INFO] Queued behind LLDP job {conflict[0]}")
                    lldp_device_queues.setdefault(device_key, []).append(job_id)
                snapshot = dict(jobs[job_id])
            _persist_job(job_id, snapshot)
            if snapshot.get('status') != 'queued':
                _launch_lldp_job(self, job_id)
            
            self._send_json({
                'job_id': job_id,
                'status': 'queued' if snapshot.get('status') == 'queued' else 'started',
                'message': f"LLDP enable {'queued' if snapshot.get('status') == 'queued' else 'started'} for {serial}",
                'resolve': resolve_info,
                'preflight': preflight,
                'queued_behind': snapshot.get('queued_behind'),
            })
        
        elif parsed.path == '/api/device-stack-live':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return
            serial = (data.get('serial') or '').strip()
            ssh_host = (data.get('ssh_host') or serial).strip()
            ssh_user = data.get('ssh_user', 'dnroot')
            ssh_password = data.get('ssh_password', 'dnroot')
            if not serial:
                self._send_json({'error': 'serial is required'}, 400)
                return
            try:
                result = self._fetch_device_stack_live(ssh_host, ssh_user, ssh_password)
                self._send_json(result)
            except Exception as e:
                self._send_json({'error': str(e), 'components': []}, 500)

        elif parsed.path == '/api/device-gitcommit':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return
            serial = (data.get('serial') or '').strip()
            ssh_host = (data.get('ssh_host') or serial).strip()
            ssh_user = data.get('ssh_user', 'dnroot')
            ssh_password = data.get('ssh_password', 'dnroot')
            if not serial:
                self._send_json({'error': 'serial is required'}, 400)
                return
            try:
                result = self._fetch_device_gitcommit(ssh_host, ssh_user, ssh_password)
                self._send_json(result)
            except Exception as e:
                self._send_json({'error': str(e), 'git_commit': None}, 500)

        elif parsed.path == '/api/lldp-neighbors':
            # Fetch LLDP neighbor table from device (show lldp neighbors)
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return
            serial = (data.get('serial') or '').strip()
            hostname = (data.get('hostname') or '').strip()
            ssh_host = (data.get('ssh_host') or '').strip()
            use_cache = data.get('use_cache', True)
            if not serial and not hostname:
                self._send_json({'error': 'serial or hostname is required'}, 400)
                return
            
            # Priority: NetworkMapper (freshest) > device_inventory > Scaler DB > SSH
            cached_device_info = None
            all_devices = []
            search_term = serial or hostname
            search_term_lower = search_term.lower()
            
            if use_cache:
                # FIRST: Try NetworkMapper MCP (auto-reset on SSE/connection failure)
                try:
                    nm_neighbors = _mcp_call('get_device_lldp', search_term)
                    if nm_neighbors:
                        nm_list = [{
                            'local_interface': n.local_interface,
                            'neighbor_device': n.neighbor_name,
                            'neighbor_port': n.neighbor_interface
                        } for n in nm_neighbors]
                        self._send_json({
                            'lldp_neighbors': nm_list,
                            'cached': True,
                            'source': 'network-mapper',
                            'hostname': search_term
                        })
                        return
                except Exception as e:
                    print(f"[LLDP] NetworkMapper lookup skipped: {e}")
                
                # SECOND: Check device_inventory.json
                inventory_file = _inventory_path()
                if inventory_file.exists():
                    try:
                        with open(inventory_file, 'r') as f:
                            inventory = json.load(f)
                        devices = inventory.get('devices', {})
                        
                        for device_key, device_data in devices.items():
                            dev_hostname = device_data.get('hostname', '')
                            dev_serial = device_data.get('serial', '')
                            dev_mgmt_ip = device_data.get('mgmt_ip', '')
                            
                            all_devices.append({
                                'hostname': dev_hostname or device_key,
                                'serial': dev_serial,
                                'ip': dev_mgmt_ip or device_key
                            })
                            
                            if device_key.lower() == search_term_lower or \
                               (dev_hostname and dev_hostname.lower() == search_term_lower) or \
                               (dev_serial and dev_serial.lower() == search_term_lower) or \
                               search_term_lower in device_key.lower() or \
                               (dev_hostname and search_term_lower in dev_hostname.lower()):
                                neighbors = device_data.get('lldp_neighbors', [])
                                last_updated = device_data.get('last_seen', '')
                                if neighbors:
                                    self._send_json({
                                        'lldp_neighbors': neighbors,
                                        'cached': True,
                                        'last_updated': last_updated,
                                        'hostname': dev_hostname or device_key,
                                        'source': 'device-inventory'
                                    })
                                    return
                                break
                    except Exception as e:
                        print(f"Error reading device_inventory.json: {e}")
                
                # THIRD: Check SCALER operational.json files
                db_configs = Path('/home/dn/SCALER/db/configs')
                if db_configs.exists():
                    search_clean = re.sub(r'[^a-z0-9]', '', search_term_lower)
                    
                    for device_dir in db_configs.iterdir():
                        if device_dir.is_dir():
                            op_file = device_dir / 'operational.json'
                            if op_file.exists():
                                try:
                                    op_data = _safe_read_ops(op_file)
                                    dev_hostname = op_data.get('hostname', device_dir.name)
                                    dev_serial = op_data.get('serial_number', '')
                                    dev_connection_ip = op_data.get('connection_ip', '')
                                    
                                    all_devices.append({
                                        'hostname': dev_hostname,
                                        'serial': dev_serial,
                                        'ip': dev_connection_ip
                                    })
                                    
                                    if dev_hostname.lower() == search_term_lower or \
                                       (dev_serial and dev_serial.lower() == search_term_lower) or \
                                       (dev_connection_ip and dev_connection_ip == search_term):
                                        cached_device_info = (op_data, dev_hostname, dev_connection_ip)
                                        break
                                    
                                    if search_term_lower in dev_hostname.lower() or \
                                       (dev_serial and search_term_lower in dev_serial.lower()):
                                        cached_device_info = (op_data, dev_hostname, dev_connection_ip)
                                        break
                                    
                                    dev_hostname_clean = re.sub(r'[^a-z0-9]', '', dev_hostname.lower())
                                    if search_clean and search_clean in dev_hostname_clean:
                                        cached_device_info = (op_data, dev_hostname, dev_connection_ip)
                                        break
                                except Exception:
                                    pass
            
            if cached_device_info:
                op_data, dev_hostname, dev_connection_ip = cached_device_info
                neighbors = op_data.get('lldp_neighbors', [])
                last_updated = op_data.get('lldp_last_updated', '')
                
                if neighbors:
                    self._send_json({
                        'lldp_neighbors': neighbors,
                        'cached': True,
                        'last_updated': last_updated,
                        'hostname': dev_hostname,
                        'source': 'scaler-db'
                    })
                    return
                else:
                    target = dev_connection_ip or dev_hostname
                    result = self._fetch_lldp_neighbors(target, ssh_host=ssh_host or None)
                    result['cached'] = False
                    result['hostname'] = dev_hostname
                    result['note'] = f'Fetched live from {target} (cached data was empty)'
                    self._send_json(result)
                    return
            
            # No cached data found - try live SSH with original search term
            target = serial or hostname
            result = self._fetch_lldp_neighbors(target, ssh_host=ssh_host or None)
            result['cached'] = False
            
            # If live fetch failed and we have similar device names, suggest them
            if result.get('error') and all_devices:
                # Find similar device names using fuzzy matching
                import difflib
                search_term = serial or hostname
                device_names = [d['hostname'] for d in all_devices if d['hostname']]
                matches = difflib.get_close_matches(search_term, device_names, n=3, cutoff=0.4)
                if matches:
                    result['suggestions'] = matches
                    result['error'] = f"{result.get('error')}. Did you mean: {', '.join(matches)}?"
            
            self._send_json(result)
        
        
        elif parsed.path == '/api/lldp-neighbors-live':
            # Fetch LLDP neighbor table LIVE (NetworkMapper first, SSH fallback)
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return
            serial = (data.get('serial') or '').strip()
            if not serial:
                self._send_json({'error': 'serial is required'}, 400)
                return
            
            # Try NetworkMapper first (auto-reset on SSE/connection failure)
            try:
                nm_neighbors = _mcp_call('get_device_lldp', serial)
                if nm_neighbors:
                    nm_list = [{
                        'local_interface': n.local_interface,
                        'neighbor_device': n.neighbor_name,
                        'neighbor_port': n.neighbor_interface
                    } for n in nm_neighbors]
                    self._send_json({
                        'lldp_neighbors': nm_list,
                        'cached': False,
                        'source': 'network-mapper',
                        'hostname': serial
                    })
                    print(f"[LLDP-Live] Served {len(nm_list)} neighbors from NetworkMapper for {serial}")
                    return
            except Exception as e:
                print(f"[LLDP-Live] NetworkMapper failed, falling back to SSH: {e}")
            
            ssh_host = (data.get('ssh_host') or '').strip()
            result = self._fetch_lldp_neighbors(serial, ssh_host=ssh_host or None)
            result['source'] = 'ssh-live'
            self._send_json(result)
        
        # ================================================================
        # Network Mapper — start discovery
        # ================================================================
        elif parsed.path == '/api/network-mapper/start':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return

            seeds = data.get('seeds', [])
            use_inventory = data.get('use_inventory', False)

            # If use_inventory, load seeds from device_inventory.json
            if use_inventory:
                inv_file = _inventory_path()
                if inv_file.exists():
                    try:
                        with open(inv_file, 'r') as f:
                            inv_data = json.load(f)
                        for key, dev in inv_data.get('devices', {}).items():
                            mgmt_ip = dev.get('mgmt_ip', '') or ''
                            hostname = dev.get('hostname', '') or ''
                            seed = mgmt_ip or hostname or key
                            if seed and seed not in seeds:
                                seeds.append(seed)
                    except Exception as e:
                        print(f"[NM] Failed to load inventory: {e}")

            if not seeds:
                self._send_json({'error': 'No seeds provided. Supply seeds[] or set use_inventory=true'}, 400)
                return

            max_depth = min(int(data.get('max_depth', 10)), 20)
            max_devices = min(int(data.get('max_devices', 50)), 200)
            creds = data.get('credentials', {})
            username = creds.get('username', 'dnroot')
            password = creds.get('password', 'dnroot')
            use_mcp = data.get('use_network_mapper_mcp', True)
            known_devices = data.get('known_devices', [])

            _nm_cleanup_old_jobs()
            req_owner = self.headers.get('X-User', 'default')
            with nm_job_lock:
                nm_job_counter += 1
                job_id = f"nm_{nm_job_counter}_{int(time.time())}"
                nm_jobs[job_id] = {
                    'status': 'starting',
                    'owner': req_owner,
                    'progress': {'discovered': 0, 'queued': len(seeds), 'failed': 0, 'max': max_devices},
                    'devices': {},
                    'links': [],
                    'errors': [],
                    'log': [f"Starting network mapper with {len(seeds)} seed(s), max_depth={max_depth}, max_devices={max_devices}"],
                    'cancelled': False,
                    'created_at': time.time()
                }

            thread = threading.Thread(
                target=_nm_bfs_crawl,
                args=(job_id, seeds, max_depth, max_devices, username, password, use_mcp, known_devices),
                daemon=True
            )
            thread.start()
            self._send_json({'job_id': job_id, 'status': 'starting', 'seeds': seeds})

        # Network Mapper — stop discovery
        elif parsed.path == '/api/network-mapper/stop':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return
            jid = data.get('job_id', '')
            if jid and jid in nm_jobs:
                with nm_job_lock:
                    job = nm_jobs[jid]
                    requester = self.headers.get('X-User', 'default') or 'default'
                    if job.get('owner', 'default') != requester:
                        self._send_json({'error': 'Job not found'}, 404)
                        return
                    job['cancelled'] = True
                self._send_json({'status': 'cancelling', 'job_id': jid})
            else:
                self._send_json({'error': 'Job not found'}, 404)

        # Network Mapper -- full MCP-based topology (no SSH, queries MCP for all devices)
        elif parsed.path == '/api/network-mapper/mcp-map':
            _nm_cleanup_old_jobs()
            req_owner = self.headers.get('X-User', 'default')
            with nm_job_lock:
                nm_job_counter += 1
                job_id = f"mcp_{nm_job_counter}_{int(time.time())}"
                nm_jobs[job_id] = {
                    'status': 'starting',
                    'owner': req_owner,
                    'progress': {'discovered': 0, 'queued': 0, 'failed': 0, 'max': 200},
                    'devices': {},
                    'links': [],
                    'errors': [],
                    'log': ['Starting MCP full-map...'],
                    'cancelled': False,
                    'created_at': time.time()
                }
            thread = threading.Thread(target=_nm_mcp_full_map, args=(job_id,), daemon=True)
            thread.start()
            self._send_json({'job_id': job_id, 'status': 'starting'})

        else:
            self._send_json({'error': 'Not found'}, 404)
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def main():
    port = 8765
    _load_recent_jobs()
    server = HTTPServer(('0.0.0.0', port), DiscoveryHandler)
    print(f"Discovery API server running on http://localhost:{port}")
    print("Endpoints:")
    print("  POST /api/discovery/start  - Start discovery (body: {serial1, serial2?})")
    print("  GET  /api/discovery/status?job_id=X  - Get job status")
    print("  GET  /api/discovery/list   - List output files")
    server.serve_forever()

if __name__ == '__main__':
    main()


