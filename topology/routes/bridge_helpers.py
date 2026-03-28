"""Shared helpers for scaler bridge routers (extracted from scaler_bridge)."""
from __future__ import annotations

from fastapi import HTTPException

from routes._state import _push_jobs, _push_jobs_lock

__all__ = [
    "DEVICE_INVENTORY_JSON", "DISCOVERY_API", "INVENTORY_FILE",
    "LOCAL_CONSOLE_CSV", "LOCAL_PDU_CLI_CFG", "LOCAL_PDU_MAP",
    "SCALER_ROOT", "SSHConnectionPool", "XRAY_CONFIG_PATH",
    "ZOHAR_CACHE_TTL", "ZOHAR_CSV_REMOTE", "ZOHAR_DB_PASS",
    "ZOHAR_DB_SERVER", "ZOHAR_DB_USER", "ZOHAR_PDU_CLI_REMOTE",
    "ZOHAR_PDU_REMOTE",
    "_ACTIVE_BUILDS_PATH", "_ACTIVE_UPGRADES_PATH",
    "_INTERNAL_JOB_KEYS", "_KNOWN_CONSOLE_SERVERS",
    "_MAX_HISTORY_JOBS", "_MAX_TERMINAL_LINES_IN_HISTORY",
    "_PUSH_HISTORY_PATH",
    "_build_config_summary", "_build_device_identity", "_build_job_name",
    "_build_scaler_ops_index", "_cache_resolve",
    "_compute_wizard_suggestions", "_connect_virsh_console_sync",
    "_detect_cli_mode_from_buffer", "_discover_console",
    "_discover_ncc_mgmt_ip_sync", "_evict_stale_jobs_locked",
    "_fetch_all_operational_via_ssh", "_fetch_config_via_ssh",
    "_fetch_git_commit_via_ssh", "_fetch_stack_via_ssh",
    "_fetch_zohar_db", "_find_cached_config_by_ip",
    "_find_inventory_device", "_get_cached_config", "_get_credentials",
    "_get_device_context", "_get_known_console_servers",
    "_get_pdu_cli_type", "_iso_from_ts", "_load_push_history",
    "_lookup_zohar_console", "_lookup_zohar_pdu",
    "_open_virsh_ncc_shell_channel", "_parse_mgmt_ip_from_show_interfaces",
    "_pdu_power_action", "_persist_job_if_done", "_probe_console_server",
    "_probe_single_port", "_recv_until", "_remove_active_build",
    "_remove_active_upgrade", "_resolve_config_dir", "_resolve_device",
    "_resolve_mgmt_ip", "_sanitize_job", "_save_active_build",
    "_save_active_upgrade",     "_save_discovered_console",
    "_save_push_history", "_ssh_pool", "_strip_ansi",
]

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
import logging
import os
import re
import sys
import threading
import time
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


_discovery_breaker = {"failures": 0, "open_until": 0}

def _resolve_device(device_id: str) -> dict:
    """Resolve device to mgmt_ip via discovery_api.
    
    Circuit breaker: after 3 consecutive failures, skip for 30s to avoid
    10-second timeout blocking every context/stack call.
    """
    import time
    now = time.time()
    if _discovery_breaker["failures"] >= 3 and now < _discovery_breaker["open_until"]:
        raise ConnectionError("discovery_api circuit breaker open")
    url = f"{DISCOVERY_API}/api/device/{urllib.parse.quote(device_id)}/resolve"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            _discovery_breaker["failures"] = 0
            return json.loads(resp.read())
    except Exception:
        _discovery_breaker["failures"] += 1
        _discovery_breaker["open_until"] = now + 30
        raise


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


class SSHConnectionPool:
    """Persistent SSH connection pool for faster operations.
    When enabled, reuses connections instead of connect/disconnect per request.
    Thread-safe; uses fresh invoke_shell() per use to avoid dirty channel state."""
    def __init__(self):
        self.enabled = False
        self._pool = {}  # ip -> { client, user, last_used, created_at }
        self._lock = threading.Lock()
        self._keepalive_thread = None
        self._stop_keepalive = threading.Event()
        self._max_idle_s = 300
        self._keepalive_s = 30
        self._max_connections = 50

    def toggle(self, on: bool) -> dict:
        with self._lock:
            self.enabled = bool(on)
            if not on:
                for ip, entry in list(self._pool.items()):
                    try:
                        entry.get("client") and entry["client"].close()
                    except Exception:
                        pass
                self._pool.clear()
                self._stop_keepalive.set()
                if self._keepalive_thread and self._keepalive_thread.is_alive():
                    self._keepalive_thread.join(timeout=2)
                self._keepalive_thread = None
            else:
                self._stop_keepalive.clear()
                self._keepalive_thread = threading.Thread(target=self._keepalive_loop, daemon=True)
                self._keepalive_thread.start()
            return {"enabled": self.enabled, "count": len(self._pool)}

    def get_client(self, ip: str, user: str, password: str):
        """Return a pooled or fresh SSHClient. If pool disabled, caller must close."""
        import paramiko
        ip = (ip or "").strip().split("/")[0]
        if not ip:
            return None
        with self._lock:
            if not self.enabled:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(ip, username=user, password=password, timeout=15,
                              look_for_keys=False, allow_agent=False)
                transport = client.get_transport()
                if transport:
                    transport.set_keepalive(self._keepalive_s)
                return client
            entry = self._pool.get(ip)
            if entry:
                client = entry.get("client")
                if client and client.get_transport() and client.get_transport().is_active():
                    entry["last_used"] = time.monotonic()
                    return client
                try:
                    client and client.close()
                except Exception:
                    pass
                del self._pool[ip]
            if len(self._pool) >= self._max_connections:
                self._evict_lru()
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ip, username=user, password=password, timeout=15,
                          look_for_keys=False, allow_agent=False)
            transport = client.get_transport()
            if transport:
                transport.set_keepalive(self._keepalive_s)
            self._pool[ip] = {"client": client, "user": user, "last_used": time.monotonic(),
                             "created_at": time.monotonic()}
            return client

    def release(self, ip: str):
        """Mark connection as idle for reuse."""
        ip = (ip or "").strip().split("/")[0]
        with self._lock:
            if ip in self._pool:
                self._pool[ip]["last_used"] = time.monotonic()

    def evict(self, ip: str):
        """Force-close and remove connection."""
        ip = (ip or "").strip().split("/")[0]
        with self._lock:
            entry = self._pool.pop(ip, None)
            if entry:
                try:
                    entry.get("client") and entry["client"].close()
                except Exception:
                    pass

    def _evict_lru(self):
        """Evict least recently used connection."""
        if not self._pool:
            return
        lru_ip = min(self._pool.items(), key=lambda x: x[1]["last_used"])[0]
        entry = self._pool.pop(lru_ip, None)
        if entry:
            try:
                entry.get("client") and entry["client"].close()
            except Exception:
                pass

    def _keepalive_loop(self):
        while not self._stop_keepalive.wait(self._keepalive_s):
            with self._lock:
                if not self.enabled:
                    break
                now = time.monotonic()
                to_remove = []
                for ip, entry in self._pool.items():
                    if now - entry["last_used"] > self._max_idle_s:
                        to_remove.append(ip)
                    else:
                        client = entry.get("client")
                        if not client or not client.get_transport() or not client.get_transport().is_active():
                            to_remove.append(ip)
                for ip in to_remove:
                    entry = self._pool.pop(ip, None)
                    if entry:
                        try:
                            entry.get("client") and entry["client"].close()
                        except Exception:
                            pass

    def status(self) -> dict:
        with self._lock:
            entries = []
            for ip, e in self._pool.items():
                client = e.get("client")
                active = bool(client and client.get_transport() and client.get_transport().is_active())
                entries.append({"ip": ip, "active": active, "last_used": e.get("last_used", 0)})
            return {"enabled": self.enabled, "count": len(self._pool), "entries": entries}


_ssh_pool = SSHConnectionPool()


_resolve_cache = {}
_scaler_ops_index = None
_scaler_ops_ip_map = None  # ip -> [entry] for fast IP-based lookups
_scaler_ops_index_ts = 0


def _build_scaler_ops_index():
    """Build an in-memory index of all SCALER operational.json files.
    Maps: serial, hostname, mgmt_ip, dir_name -> {ip, scaler_id, serial}
    Cached for 60 seconds.
    """
    global _scaler_ops_index, _scaler_ops_ip_map, _scaler_ops_index_ts
    import time
    now = time.time()
    if _scaler_ops_index and (now - _scaler_ops_index_ts) < 60:
        return _scaler_ops_index

    index = {}
    ip_map = {}
    configs_dir = Path(SCALER_ROOT) / "db" / "configs"
    if not configs_dir.exists():
        _scaler_ops_index = index
        _scaler_ops_ip_map = {}
        _scaler_ops_index_ts = now
        return index

    # Phase 1: Read all config directories and find the richest entry per serial
    serial_to_best = {}
    all_entries = []
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
            hostname = (ops.get("hostname") or dev_dir.name).strip()
            has_state = bool(ops.get("device_state"))
            has_version = bool(ops.get("dnos_version") or ops.get("dnos_url"))
            richness = (1 if has_state else 0) + (1 if has_version else 0) + (1 if serial else 0)
            entry = {"ip": ip, "scaler_id": dev_dir.name, "serial": serial, "hostname": hostname}
            all_entries.append((dev_dir.name, entry, richness, serial))

            if serial and serial != "N/A":
                prev = serial_to_best.get(serial)
                if prev is None or richness > prev[1]:
                    serial_to_best[serial] = (entry, richness)
        except Exception:
            continue

    # Phase 2: Build index, preferring the richest entry per serial
    for dir_name, entry, richness, serial in all_entries:
        if serial and serial in serial_to_best:
            best_entry = serial_to_best[serial][0]
            if best_entry["scaler_id"] != dir_name:
                entry = {**best_entry, "scaler_id": best_entry["scaler_id"]}

        index[dir_name.lower()] = entry
        hostname = entry.get("hostname", dir_name)
        if hostname and hostname.lower() not in index:
            index[hostname.lower()] = entry
        if serial:
            index[serial.lower()] = entry
        ip = entry.get("ip", "")
        if ip:
            index[ip] = entry
            if ip not in ip_map:
                ip_map[ip] = []
            if entry not in ip_map[ip]:
                ip_map[ip].append(entry)
        raw_ssh = entry.get("ssh_host", "")
        if raw_ssh and raw_ssh.lower() not in index:
            index[raw_ssh.lower()] = entry

    _scaler_ops_index = index
    _scaler_ops_ip_map = ip_map
    _scaler_ops_index_ts = now
    return index


def _resolve_config_dir(device_id: str) -> str:
    """Find the canonical config directory name for a device.

    Resolves through: exact match -> index lookup -> partial name match.
    Returns the directory name (e.g. 'PE-1') under SCALER_ROOT/db/configs/.
    Falls back to device_id if no match found.
    """
    configs_dir = Path(SCALER_ROOT) / "db" / "configs"

    if (configs_dir / device_id / "operational.json").exists():
        ops = json.loads((configs_dir / device_id / "operational.json").read_text())
        if ops.get("device_state") or ops.get("dnos_version") or ops.get("serial_number"):
            return device_id

    idx = _build_scaler_ops_index()
    entry = idx.get(device_id.lower())
    if entry:
        sid = entry["scaler_id"]
        if (configs_dir / sid / "operational.json").exists():
            return sid

    norm = re.sub(r'[_\-\s]', '', device_id.lower())
    best_dir = None
    best_richness = -1
    for d in configs_dir.iterdir():
        if not d.is_dir() or not (d / "operational.json").exists():
            continue
        norm_d = re.sub(r'[_\-\s]', '', d.name.lower())
        if norm in norm_d or norm_d in norm:
            try:
                ops = json.loads((d / "operational.json").read_text())
                richness = sum(1 for k in ("device_state", "dnos_version", "serial_number") if ops.get(k))
                if richness > best_richness:
                    best_richness = richness
                    best_dir = d.name
            except Exception:
                if best_dir is None:
                    best_dir = d.name

    return best_dir or device_id


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
        # Always dial the literal ssh_host IP. The ops index can map the same serial to
        # multiple dirs (e.g. PE-1 vs YOR_PE-1); merged entry["ip"] may not match this key.
        if entry and entry.get("scaler_id"):
            result = (ssh, entry["scaler_id"], f"ssh_ip_literal:{ssh}")
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
    if inv_dev is None:
        inv_dev = {}
    ip = (inv_dev.get("mgmt_ip") or inv_dev.get("ip") or "").strip().split("/")[0]
    if ip:
        idx_entry = idx.get(ip)
        sid = idx_entry["scaler_id"] if idx_entry else device_id
        result = (ip, sid, "device_inventory")
        _cache_resolve(cache_key, result)
        return result

    norm_did = re.sub(r'[_\-\s]', '', device_id.lower())
    for key, entry in idx.items():
        if not entry["ip"]:
            continue
        norm_key = re.sub(r'[_\-\s]', '', key)
        if norm_did in norm_key or norm_key in norm_did:
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


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from terminal output."""
    return re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text)


def _parse_stack_table_lines(raw: str) -> list:
    """Parse ``show system stack`` table text into component dicts."""
    components = []
    for line in raw.split("\n"):
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 7:
            continue
        name = parts[1]
        if not name or name.upper() in ("COMPONENT", "---", ""):
            continue
        if name.startswith("-"):
            continue
        components.append({
            "name": name,
            "hw_model": parts[2] if len(parts) > 2 else "-",
            "revert": parts[4] if len(parts) > 4 else "-",
            "current": parts[5] if len(parts) > 5 else "-",
            "target": parts[6] if len(parts) > 6 else "-",
        })
    return components


def _fetch_stack_via_ssh(mgmt_ip: str, user: str, password: str) -> list:
    """SSH to device, run 'show system stack | no-more', parse and return components."""
    from routes._device_comm import DeviceCommHelper

    comm = DeviceCommHelper()
    raw = comm.run_show_ip(mgmt_ip, user, password, "show system stack", timeout=60)
    if "[SSH ERROR]" in raw:
        return []
    return _parse_stack_table_lines(_strip_ansi(raw))


def _recv_until(channel, markers, timeout_s=15):
    """Read channel until any marker string is found in output, or timeout.
    Polls at 50ms intervals -- no wasted time on fixed sleeps."""
    import time
    buf = ""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if channel.recv_ready():
            buf += channel.recv(65535).decode("utf-8", errors="replace")
            for m in markers:
                if m in buf:
                    return buf
        time.sleep(0.05)
    return buf


def _fetch_git_commit_via_ssh(mgmt_ip: str, user: str, password: str,
                              scaler_device_id: str = "") -> str | None:
    """SSH to device, run start shell + cat /.gitcommit, return hash.
    Falls back to virsh console for cluster devices when direct SSH fails."""
    from scaler.dnos_session import DNOSSession

    try:
        client = _ssh_pool.get_client(mgmt_ip, user, password)
    except Exception:
        client = None
    if not client:
        if scaler_device_id:
            result = _fetch_ops_via_virsh_fallback(scaler_device_id, user, password)
            gc = result.get("git_commit")
            if gc:
                try:
                    _ops_path = Path(SCALER_ROOT) / "db" / "configs" / scaler_device_id / "operational.json"
                    if _ops_path.exists():
                        _ops = json.loads(_ops_path.read_text())
                        _ops["git_commit"] = gc
                        if result.get("stack"):
                            _ops["stack_components"] = result["stack"]
                        import tempfile
                        _fd, _tp = tempfile.mkstemp(dir=str(_ops_path.parent), suffix=".tmp")
                        with os.fdopen(_fd, "w") as _f:
                            json.dump(_ops, _f, indent=2)
                        os.replace(_tp, str(_ops_path))
                except Exception:
                    pass
            return gc
        return None
    owns = not _ssh_pool.enabled
    try:
        with DNOSSession(
            mgmt_ip, user, password, client=client, owns_client=owns,
        ) as sess:
            sess.send_raw("run start shell\r\n")
            sess.recv_until_markers(["assword"], timeout_s=8)
            sess.send_raw(password + "\r\n")
            shell_out = sess.recv_until_markers(
                ["root@", "$ ", "denied", "ERROR"], timeout_s=8,
            )
            if "denied" in shell_out.lower() or "ERROR" in shell_out:
                return None
            sess.send_raw("cat /.gitcommit\r\n")
            raw = _strip_ansi(sess.recv_until_markers(["#", "$ "], timeout_s=5))
            for line in raw.split("\n"):
                line = line.strip()
                if not line or line.startswith("cat ") or line.endswith("#") or line.endswith("$"):
                    continue
                if "No such file" in line or "Permission denied" in line:
                    continue
                m = re.match(r"^([a-fA-F0-9]{7,40}(?:-\S+)?)$", line)
                if m:
                    return m.group(1)
            return None
    except Exception:
        return None
    finally:
        if _ssh_pool.enabled:
            _ssh_pool.release(mgmt_ip)
        elif owns:
            try:
                client.close()
            except Exception:
                pass


def _fetch_all_operational_via_ssh(mgmt_ip: str, user: str, password: str,
                                   scaler_device_id: str = "") -> dict:
    """Single SSH session for LLDP + stack + git_commit + device_state.
    Uses DNOSSession. Uses pool when enabled.
    Falls back to virsh console for cluster (KVM) devices when direct SSH fails."""
    import time as _time

    from scaler.connection_strategy import detect_device_mode
    from scaler.dnos_session import DNOSSession

    result = {"lldp": [], "stack": [], "git_commit": None, "device_state": None}
    try:
        client = _ssh_pool.get_client(mgmt_ip, user, password)
    except Exception:
        client = None
    if not client:
        if scaler_device_id:
            return _fetch_ops_via_virsh_fallback(scaler_device_id, user, password)
        return result
    owns = not _ssh_pool.enabled
    try:
        with DNOSSession(
            mgmt_ip, user, password, client=client, owns_client=owns,
        ) as sess:
            sess.send_raw("\r\n")
            mode_buf = sess.recv_until_markers(["#", ">"], timeout_s=5)
            detected = detect_device_mode(mode_buf)
            if detected:
                result["device_state"] = detected

            raw_lldp = sess.send_command("show lldp neighbors", timeout=10)
            raw_lldp = _strip_ansi(raw_lldp)
            for line in raw_lldp.split("\n"):
                if "|" in line and "Local" not in line and "Interface" not in line and "---" not in line:
                    parts = [p.strip() for p in line.split("|") if p.strip()]
                    if len(parts) >= 3:
                        result["lldp"].append({
                            "local": parts[0], "neighbor": parts[1], "remote": parts[2],
                        })

            raw_stack = sess.send_command("show system stack", timeout=10)
            result["stack"] = _parse_stack_table_lines(_strip_ansi(raw_stack))

            sess.send_raw("run start shell\r\n")
            sess.recv_until_markers(["assword"], timeout_s=8)
            sess.send_raw(password + "\r\n")
            shell_out = sess.recv_until_markers(
                ["root@", "$ ", "denied", "ERROR"], timeout_s=8,
            )
            if "denied" not in shell_out.lower() and "ERROR" not in shell_out:
                sess.send_raw("cat /.gitcommit\r\n")
                raw = _strip_ansi(sess.recv_until_markers(["#", "$ "], timeout_s=5))
                for line in raw.split("\n"):
                    line = line.strip()
                    if not line or line.startswith("cat ") or line.endswith("#") or line.endswith("$"):
                        continue
                    if "No such file" in line or "Permission denied" in line:
                        continue
                    m = re.match(r"^([a-fA-F0-9]{7,40}(?:-\S+)?)$", line)
                    if m:
                        result["git_commit"] = m.group(1)
                        break

            return result
    except Exception:
        return result
    finally:
        if _ssh_pool.enabled:
            _ssh_pool.release(mgmt_ip)
        elif owns:
            try:
                client.close()
            except Exception:
                pass


def _fetch_ops_via_virsh_fallback(scaler_device_id: str, user: str, password: str) -> dict:
    """Fetch LLDP/stack/git_commit via virsh console when direct SSH is unavailable.
    Used for cluster (KVM) devices where the NCC doesn't accept direct SSH.
    Tries each NCC VM until one has an active CLI (handles stale active_ncc_vm)."""
    import time as _time

    from scaler.connection_strategy import detect_device_mode

    result = {"lldp": [], "stack": [], "git_commit": None, "device_state": None}
    ops_path = Path(SCALER_ROOT) / "db" / "configs" / scaler_device_id / "operational.json"
    if not ops_path.exists():
        return result
    try:
        ops = json.loads(ops_path.read_text())
    except Exception:
        return result
    if ops.get("ncc_type") != "kvm":
        return result

    kvm_host = ops.get("kvm_host_ip") or ops.get("kvm_host") or ""
    kvm_creds = ops.get("kvm_host_credentials") or {}
    kvm_user = kvm_creds.get("username", "dn")
    kvm_pass = kvm_creds.get("password", "drive1234!")
    ncc_vms = ops.get("ncc_vms") or []
    stored_active = ops.get("active_ncc_vm") or ""

    if not kvm_host:
        return result

    # Build ordered NCC list: stored active first, then others
    try_order = []
    if stored_active and stored_active in ncc_vms:
        try_order.append(stored_active)
    for vm in ncc_vms:
        if vm not in try_order:
            try_order.append(vm)
    if not try_order:
        try_order = [""]

    for ncc_vm in try_order:
        logging.info("[virsh-ops] Trying NCC %s for %s via KVM %s",
                     ncc_vm or "(auto)", scaler_device_id, kvm_host)
        ssh = None
        try:
            ssh, channel, buf = _open_virsh_ncc_shell_channel(
                kvm_host, kvm_user, kvm_pass, ncc_vms, ncc_vm
            )
            channel.settimeout(15)

            initial_text = buf.decode("utf-8", errors="replace") if isinstance(buf, (bytes, bytearray)) else str(buf)
            last_line = initial_text.rstrip().split("\n")[-1].strip() if initial_text.rstrip() else ""
            if last_line.endswith("$") and "#" not in last_line:
                logging.info("[virsh-ops] NCC %s is in bash (standby?), skipping", ncc_vm)
                ssh.close()
                ssh = None
                continue

            detected = detect_device_mode(initial_text)
            if detected:
                result["device_state"] = detected

            def _send_and_recv(ch, cmd, wait=10):
                ch.send(cmd + " | no-more\n")
                _time.sleep(1.5)
                out = b""
                deadline = _time.time() + wait
                while _time.time() < deadline:
                    if ch.recv_ready():
                        out += ch.recv(65535)
                    full_text = out.decode("utf-8", errors="replace")
                    lines = full_text.rstrip().split("\n")
                    last_line = lines[-1].strip() if lines else ""
                    if len(lines) > 2 and (last_line.endswith("#") or last_line.endswith(">")):
                        if "More" not in last_line:
                            _time.sleep(0.3)
                            if ch.recv_ready():
                                out += ch.recv(65535)
                            break
                    _time.sleep(0.3)
                return _strip_ansi(out.decode("utf-8", errors="replace"))

            raw_stack = _send_and_recv(channel, "show system stack", wait=12)
            result["stack"] = _parse_stack_table_lines(raw_stack)

            if not result["stack"]:
                logging.info("[virsh-ops] No stack from NCC %s, trying next", ncc_vm)
                ssh.close()
                ssh = None
                continue

            if not result["device_state"]:
                detected = detect_device_mode(raw_stack)
                if detected:
                    result["device_state"] = detected

            raw_lldp = _send_and_recv(channel, "show lldp neighbors", wait=20)
            for line in raw_lldp.split("\n"):
                if "|" in line and "Local" not in line and "Interface" not in line and "---" not in line:
                    parts = [p.strip() for p in line.split("|") if p.strip()]
                    if len(parts) >= 3:
                        result["lldp"].append({
                            "local": parts[0], "neighbor": parts[1], "remote": parts[2],
                        })

            try:
                channel.send("run start shell\r\n")
                _time.sleep(2)
                shell_buf = b""
                shell_deadline = _time.time() + 10
                while _time.time() < shell_deadline:
                    if channel.recv_ready():
                        shell_buf += channel.recv(65535)
                    shell_text = shell_buf.decode("utf-8", errors="replace").lower()
                    if "assword" in shell_text or "root@" in shell_text or "$ " in shell_text:
                        break
                    _time.sleep(0.3)
                shell_decoded = shell_buf.decode("utf-8", errors="replace").lower()
                if "assword" in shell_decoded:
                    cli_pass = password or "dnroot"
                    channel.send(cli_pass + "\r\n")
                    _time.sleep(2)
                    shell_buf2 = b""
                    sd2 = _time.time() + 8
                    while _time.time() < sd2:
                        if channel.recv_ready():
                            shell_buf2 += channel.recv(65535)
                        t2 = shell_buf2.decode("utf-8", errors="replace")
                        if "root@" in t2 or "$ " in t2:
                            break
                        _time.sleep(0.3)
                channel.send("cat /.gitcommit 2>/dev/null\r\n")
                _time.sleep(1.5)
                gc_buf = b""
                gc_deadline = _time.time() + 5
                while _time.time() < gc_deadline:
                    if channel.recv_ready():
                        gc_buf += channel.recv(65535)
                    gc_text = gc_buf.decode("utf-8", errors="replace")
                    if "root@" in gc_text or "$ " in gc_text or "#" in gc_text:
                        break
                    _time.sleep(0.3)
                gc_decoded = _strip_ansi(gc_buf.decode("utf-8", errors="replace"))
                for gc_line in gc_decoded.split("\n"):
                    gc_line = gc_line.strip()
                    if not gc_line or gc_line.startswith("cat ") or gc_line.endswith("#") or gc_line.endswith("$"):
                        continue
                    if "No such file" in gc_line or "Permission" in gc_line:
                        continue
                    gc_match = re.match(r"^([a-fA-F0-9]{7,40}(?:-\S+)?)$", gc_line)
                    if gc_match:
                        result["git_commit"] = gc_match.group(1)
                        break
                channel.send("exit\r\n")
                _time.sleep(0.5)
            except Exception as gc_err:
                logging.warning("[virsh-ops] git_commit fetch failed for %s: %s", scaler_device_id, gc_err)

            # Update active_ncc_vm if it changed
            if ncc_vm and ncc_vm != stored_active:
                try:
                    ops["active_ncc_vm"] = ncc_vm
                    import tempfile
                    tmp_fd, tmp_path = tempfile.mkstemp(dir=str(ops_path.parent), suffix=".tmp")
                    with os.fdopen(tmp_fd, "w") as f:
                        json.dump(ops, f, indent=2)
                    os.replace(tmp_path, str(ops_path))
                    logging.info("[virsh-ops] Updated active_ncc_vm to %s", ncc_vm)
                except Exception:
                    pass

            logging.info("[virsh-ops] Got %d LLDP, %d stack, git=%s from NCC %s for %s",
                         len(result["lldp"]), len(result["stack"]),
                         result.get("git_commit", "N/A"), ncc_vm, scaler_device_id)
            return result
        except Exception as e:
            logging.warning("[virsh-ops] NCC %s failed: %s", ncc_vm, e)
            if ssh:
                try:
                    ssh.close()
                except Exception:
                    pass
            continue

    logging.warning("[virsh-ops] All NCC VMs failed for %s", scaler_device_id)
    return result


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
    system_name = ""
    try:
        from scaler.wizard.parsers import extract_hierarchy_section
        sys_section = extract_hierarchy_section(config, "system")
        if sys_section:
            nm = re.search(r"^\s+name\s+(\S+)", sys_section, re.MULTILINE)
            if nm:
                system_name = nm.group(1)
    except Exception:
        pass
    summary = {
        "lines": len(config.splitlines()),
        "system_name": system_name,
        "hostname": system_name or "",
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

ZOHAR_DB_SERVER = "zkeiserman-dev"
ZOHAR_DB_USER = "dn"
ZOHAR_DB_PASS = "Drive1234!"
ZOHAR_CSV_REMOTE = "/home/dn/console_db/console_devices.csv"
ZOHAR_PDU_REMOTE = "/home/dn/console_db/pdu_mapping.json"
ZOHAR_PDU_CLI_REMOTE = "/home/dn/console_db/pdu_cli_config.json"
LOCAL_CONSOLE_CSV = "/tmp/console_devices_cache.csv"
LOCAL_PDU_MAP = "/tmp/pdu_mapping_cache.json"
LOCAL_PDU_CLI_CFG = "/tmp/pdu_cli_config_cache.json"
_zohar_db_fetched_at = 0.0
ZOHAR_CACHE_TTL = 3600


def _fetch_zohar_db(force: bool = False):
    """Fetch Zohar's console DB from zkeiserman-dev via SFTP. Caches for 1 hour."""
    global _zohar_db_fetched_at
    if not force and (time.time() - _zohar_db_fetched_at) < ZOHAR_CACHE_TTL:
        if os.path.exists(LOCAL_CONSOLE_CSV) and os.path.exists(LOCAL_PDU_MAP):
            return
    import paramiko as _pmk
    try:
        c = _pmk.SSHClient()
        c.set_missing_host_key_policy(_pmk.AutoAddPolicy())
        c.connect(ZOHAR_DB_SERVER, username=ZOHAR_DB_USER, password=ZOHAR_DB_PASS,
                  timeout=10, look_for_keys=False, allow_agent=False)
        sftp = c.open_sftp()
        try:
            sftp.get(ZOHAR_CSV_REMOTE, LOCAL_CONSOLE_CSV)
        except (FileNotFoundError, IOError):
            pass
        try:
            sftp.get(ZOHAR_PDU_REMOTE, LOCAL_PDU_MAP)
        except (FileNotFoundError, IOError):
            pass
        try:
            sftp.get(ZOHAR_PDU_CLI_REMOTE, LOCAL_PDU_CLI_CFG)
        except (FileNotFoundError, IOError):
            pass
        sftp.close()
        c.close()
        _zohar_db_fetched_at = time.time()
    except Exception as e:
        logging.warning(f"[ConsoleDB] Failed to fetch from {ZOHAR_DB_SERVER}: {e}")


def _lookup_zohar_console(serial: str) -> tuple:
    """Look up console server and port from Zohar's CSV by serial. Returns (server, port) or (None, None)."""
    import csv
    if not os.path.exists(LOCAL_CONSOLE_CSV):
        return None, None
    serial_upper = serial.strip().upper()
    with open(LOCAL_CONSOLE_CSV, newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) >= 3 and row[2].strip().upper() == serial_upper:
                return row[0].strip(), row[1].strip()
    return None, None


def _lookup_zohar_pdu(serial: str) -> list:
    """Look up PDU mapping from Zohar's DB. Returns list of {pdu, outlet} dicts or []."""
    if not os.path.exists(LOCAL_PDU_MAP):
        return []
    serial_upper = serial.strip().upper()
    try:
        with open(LOCAL_PDU_MAP) as f:
            data = json.load(f)
        entry = data.get(serial_upper)
        if not entry:
            return []
        if isinstance(entry, list):
            return entry
        return [entry]
    except Exception:
        return []


def _get_pdu_cli_type(pdu_host: str) -> str:
    """Return CLI type for PDU: 'dev_outlet' (newer) or 'ol' (legacy)."""
    pdu_host = pdu_host.strip().lower()
    if not pdu_host.startswith("pdu-"):
        pdu_host = "pdu-" + pdu_host
    try:
        if os.path.exists(LOCAL_PDU_CLI_CFG):
            with open(LOCAL_PDU_CLI_CFG) as f:
                cfg = json.load(f)
            for mode, hosts in cfg.items():
                if pdu_host in [x.lower() for x in hosts]:
                    return mode
    except Exception:
        pass
    return "dev_outlet"


def _discover_console(device_id: str, serial_number: str = "", ssh_host: str = "") -> dict:
    """Discover console path for a device.
    Priority: 1) console_mappings.json  2) Zohar's CSV DB  3) Device42 API.
    Returns { console_server, port, pdu_entries, source, serial_no }."""
    serial = (serial_number or "").strip().upper()
    result = {"source": None, "console_server": None, "port": None,
              "pdu_entries": [], "serial_no": serial or None}

    if not serial:
        for try_id in [device_id, ssh_host]:
            if not try_id:
                continue
            try:
                ops_path = Path(SCALER_ROOT) / "db" / "configs" / try_id / "operational.json"
                if ops_path.exists():
                    ops = json.loads(ops_path.read_text())
                    s = ops.get("serial_number") or ops.get("serial") or ""
                    if s:
                        serial = s.strip().upper()
                        result["serial_no"] = serial
                        break
            except Exception:
                continue

    # 1) Check console_mappings.json (local DB -- same source the probe uses)
    try:
        from scaler.connection_strategy import get_console_config_for_device
        for try_name in [device_id, ssh_host]:
            if not try_name:
                continue
            cfg = get_console_config_for_device(try_name)
            if cfg and cfg.get("host"):
                cs_host = cfg["host"]
                cs_port = cfg.get("port")
                if "." not in cs_host and "dev.drivenets.net" not in cs_host:
                    cs_host = f"{cs_host}.dev.drivenets.net"
                result["console_server"] = cs_host
                result["port"] = str(cs_port) if cs_port else None
                result["source"] = cfg.get("_source", "console_mappings")
                if not result["serial_no"] and serial:
                    result["serial_no"] = serial
                break
    except Exception:
        pass

    # Also check serial_to_console in console_mappings.json
    if not result["console_server"] and serial:
        try:
            mappings_path = Path(SCALER_ROOT) / "db" / "console_mappings.json"
            if mappings_path.exists():
                cm = json.loads(mappings_path.read_text())
                s2c = cm.get("serial_to_console", {})
                entry = s2c.get(serial) or s2c.get(serial.upper())
                if entry and entry.get("console_server"):
                    cs_host = entry["console_server"]
                    if "." not in cs_host:
                        cs_host = f"{cs_host}.dev.drivenets.net"
                    result["console_server"] = cs_host
                    result["port"] = str(entry.get("port", ""))
                    result["source"] = "console_mappings"
        except Exception:
            pass

    # 2) Zohar's CSV DB
    if not result["console_server"] and serial:
        try:
            _fetch_zohar_db()
        except Exception:
            pass
        cs, port = _lookup_zohar_console(serial)
        if cs:
            result["console_server"] = cs
            result["port"] = port
            result["source"] = "zohar_db"
            result["pdu_entries"] = _lookup_zohar_pdu(serial)

    # 3) Device42 API
    if not result["console_server"]:
        try:
            config_path = Path.home() / ".device42_config.json"
            if config_path.exists():
                cfg = json.loads(config_path.read_text())
                base_url = (cfg.get("url") or "https://device42.dev.drivenets.net").rstrip("/")
                user = cfg.get("username", "")
                password = cfg.get("password", "")
                if user and password:
                    import base64
                    auth = base64.b64encode(f"{user}:{password}".encode()).decode()
                    headers = {"Authorization": f"Basic {auth}", "Accept": "application/json"}
                    if serial:
                        url = f"{base_url}/api/1.0/devices/?serial_no={urllib.parse.quote(serial)}"
                    else:
                        url = f"{base_url}/api/1.0/devices/?name={urllib.parse.quote(device_id)}"
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        d42_data = json.loads(resp.read())
                    devs = d42_data.get("devices", [])
                    if devs:
                        dev = devs[0]
                        result["source"] = "device42"
                        if dev.get("serial_no"):
                            result["serial_no"] = dev["serial_no"]
                        ports = dev.get("ports", [])
                        for p_entry in (ports if isinstance(ports, list) else []):
                            if isinstance(p_entry, dict) and p_entry.get("type") == "console":
                                result["console_server"] = p_entry.get("remote_device") or p_entry.get("name")
                                result["port"] = p_entry.get("remote_port") or p_entry.get("port")
                                break
                        pdus = dev.get("pdus", [])
                        if pdus:
                            result["pdu_entries"] = [
                                {"pdu": (p.get("name") or p.get("ip") or ""), "outlet": str(p.get("outlet") or p.get("port") or "")}
                                for p in pdus if isinstance(p, dict)
                            ]
        except Exception:
            pass

    if not result["console_server"] and not result["serial_no"]:
        raise ValueError(f"No console mapping found for {device_id}. Provide a serial number or add to Zohar's DB.")

    # Detect cluster devices: console reaches NCP (data plane), NOT NCC (control plane)
    if result["console_server"]:
        try:
            mappings_path = Path(SCALER_ROOT) / "db" / "console_mappings.json"
            if mappings_path.exists():
                cm = json.loads(mappings_path.read_text())
                ncc_access = cm.get("cluster_ncc_access", {})
                import re as _re
                norm_id = _re.sub(r'[_\-\s]', '', device_id.lower())
                for key in ncc_access:
                    norm_k = _re.sub(r'[_\-\s]', '', key.lower())
                    if norm_id == norm_k:
                        entry = ncc_access[key]
                        result["is_cluster"] = True
                        result["console_target"] = "NCP"
                        kvm_host = entry.get("kvm_host", "")
                        ncc_vms = entry.get("ncc_vms", [])
                        result["cluster_note"] = (
                            f"This console reaches the NCP (data plane), NOT the NCC (control plane). "
                            f"For NCC access use Virsh Console via KVM host {kvm_host} "
                            f"or SSH to {', '.join(ncc_vms) if ncc_vms else 'the NCC VMs'}."
                        )
                        break
        except Exception:
            pass

    return result


# ---- Console port-scan fallback (ATEN SN9116CO) ----

_KNOWN_CONSOLE_SERVERS = None

def _get_known_console_servers() -> list:
    """Load known console servers from console_mappings.json + hardcoded defaults."""
    global _KNOWN_CONSOLE_SERVERS
    if _KNOWN_CONSOLE_SERVERS is not None:
        return _KNOWN_CONSOLE_SERVERS
    servers = []
    try:
        mp = Path(SCALER_ROOT) / "db" / "console_mappings.json"
        if mp.exists():
            data = json.loads(mp.read_text())
            for name, info in data.get("console_servers", {}).items():
                servers.append({
                    "name": name,
                    "host": info.get("host", f"{name}.dev.drivenets.net"),
                    "user": info.get("user", "dn"),
                    "password": info.get("password", "drive1234"),
                    "total_ports": info.get("total_ports", 16),
                    "rack_hint": info.get("rack_hint", ""),
                })
    except Exception:
        pass
    if not servers:
        for rack in ["b10", "b15", "d16"]:
            servers.append({
                "name": f"console-{rack}",
                "host": f"console-{rack}.dev.drivenets.net",
                "user": "dn", "password": "drive1234",
                "total_ports": 16, "rack_hint": rack.upper(),
            })
    _KNOWN_CONSOLE_SERVERS = servers
    return servers


def _probe_single_port(ssh_client, port_num: int, look_for: str = "", timeout_per_port: float = 6) -> dict:
    """Navigate ATEN menu to a port, read output, exit cleanly.
    Returns {port, output, hostname_guess, matched}."""
    import paramiko
    result = {"port": port_num, "output": "", "hostname_guess": "", "matched": False}
    try:
        chan = ssh_client.invoke_shell(width=200, height=50)
        chan.settimeout(timeout_per_port)
        time.sleep(1)
        if chan.recv_ready():
            chan.recv(8192)

        chan.send("3\r\n")
        time.sleep(1.5)
        if chan.recv_ready():
            chan.recv(8192)

        chan.send(f"{port_num}\r\n")
        time.sleep(2)
        chan.send("\x03")
        time.sleep(0.5)
        chan.send("\r\n")
        time.sleep(2)
        out = ""
        for _ in range(5):
            if chan.recv_ready():
                out += chan.recv(16384).decode("utf-8", errors="replace")
            time.sleep(0.3)
        result["output"] = out[-500:] if len(out) > 500 else out

        import re
        hostname = ""
        for line in out.splitlines():
            stripped = line.strip()
            m = re.match(r'^([A-Za-z0-9_\-]+)[\(#>$]', stripped)
            if m:
                hostname = m.group(1)
                break
            if "login:" in stripped:
                hostname = "_login_prompt_"
                break

        result["hostname_guess"] = hostname
        if look_for and hostname:
            lf = look_for.lower()
            if lf in hostname.lower() or hostname.lower() in lf:
                result["matched"] = True

        chan.send("\x07")
        time.sleep(0.5)
        chan.send("q\r\n")
        time.sleep(0.5)
        chan.close()
    except Exception as e:
        result["output"] = f"[probe error: {e}]"
        try:
            chan.close()
        except Exception:
            pass
    return result


def _probe_console_server(server: dict, look_for: str = "", skip_ports: list = None) -> list:
    """Probe all ports on a console server, looking for a specific device.
    Returns list of {port, hostname_guess, matched, output_snippet}."""
    import paramiko
    skip = set(skip_ports or [])
    found = []
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server["host"], username=server["user"],
                    password=server["password"], timeout=15,
                    look_for_keys=False, allow_agent=False)
        total = server.get("total_ports", 16)
        for p in range(1, total + 1):
            if p in skip:
                continue
            res = _probe_single_port(ssh, p, look_for)
            found.append({
                "port": p,
                "hostname_guess": res["hostname_guess"],
                "matched": res["matched"],
                "output_snippet": res["output"][:200],
            })
            if res["matched"]:
                break
        ssh.close()
    except Exception as e:
        found.append({"port": 0, "hostname_guess": "", "matched": False,
                       "output_snippet": f"[connection failed: {e}]"})
    return found


def _save_discovered_console(device_id: str, serial_number: str, server_name: str,
                              server_host: str, port: int):
    """Save a discovered console mapping to console_mappings.json."""
    mp = Path(SCALER_ROOT) / "db" / "console_mappings.json"
    mp.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if mp.exists():
        try:
            data = json.loads(mp.read_text())
        except Exception:
            data = {}
    if "console_servers" not in data:
        data["console_servers"] = {}
    srv = data["console_servers"].get(server_name, {})
    if "ports" not in srv:
        srv["ports"] = {}
    srv.setdefault("host", server_host)
    srv["ports"][str(port)] = {
        "hostname": device_id,
        "serial_number": serial_number.upper() if serial_number else "",
        "last_verified": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source": "port_scan",
    }
    data["console_servers"][server_name] = srv
    if "device_to_console" not in data:
        data["device_to_console"] = {}
    data["device_to_console"][device_id] = {
        "console_server": server_name,
        "host": server_host,
        "port": port,
        "serial_number": serial_number.upper() if serial_number else "",
        "source": "port_scan",
        "discovered_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    mp.write_text(json.dumps(data, indent=2))


def _pdu_power_action(pdu_host: str, outlet: int, action: str = "reboot") -> dict:
    """Perform PDU power action via SSH. action: 'reboot' | 'off' | 'on' | 'status'.
    Returns { success, status_output, error? }."""
    import paramiko as _pmk
    pdu_host = pdu_host.strip().lower()
    if not pdu_host.startswith("pdu-"):
        pdu_host = "pdu-" + pdu_host
    cli_type = _get_pdu_cli_type(pdu_host)
    passwords = ["drive1234!", "drive1234"]
    last_err = None
    for pwd in passwords:
        try:
            client = _pmk.SSHClient()
            client.set_missing_host_key_policy(_pmk.AutoAddPolicy())
            client.connect(pdu_host, username="dn", password=pwd, timeout=15,
                           look_for_keys=False, allow_agent=False)
            shell = client.invoke_shell()
            time.sleep(2)
            if shell.recv_ready():
                shell.recv(10000)

            def _run(cmd, wait=2.5):
                shell.send(cmd + "\n")
                time.sleep(wait)
                out = b""
                for _ in range(15):
                    if shell.recv_ready():
                        out += shell.recv(5000)
                        time.sleep(0.2)
                    elif out:
                        break
                    else:
                        time.sleep(0.2)
                return out.decode("utf-8", errors="replace")

            def _off():
                if cli_type == "dev_outlet":
                    return _run(f"dev outlet 1 {outlet} off")
                return _run(f"olOff {outlet}")

            def _on():
                if cli_type == "dev_outlet":
                    return _run(f"dev outlet 1 {outlet} on")
                return _run(f"olOn {outlet}")

            def _status():
                if cli_type == "dev_outlet":
                    return _run(f"dev outlet 1 {outlet} get status")
                return _run(f"olStatus {outlet}")

            output_lines = []
            if action == "off":
                _off()
                time.sleep(1)
                st = _status()
                output_lines.append(f"OFF sent -> status: {st.strip()}")
            elif action == "on":
                _on()
                time.sleep(1)
                st = _status()
                output_lines.append(f"ON sent -> status: {st.strip()}")
            elif action == "status":
                st = _status()
                output_lines.append(f"Status: {st.strip()}")
            else:
                _off()
                time.sleep(2)
                st1 = _status()
                output_lines.append(f"OFF -> {st1.strip()}")
                time.sleep(3)
                _on()
                time.sleep(2)
                st2 = _status()
                output_lines.append(f"ON -> {st2.strip()}")

            client.get_transport().close()
            return {"success": True, "status_output": "\n".join(output_lines), "pdu_host": pdu_host, "outlet": outlet, "cli_type": cli_type}
        except _pmk.ssh_exception.AuthenticationException as e:
            last_err = str(e)
            continue
        except Exception as e:
            return {"success": False, "error": str(e), "pdu_host": pdu_host, "outlet": outlet}
    return {"success": False, "error": f"Auth failed on {pdu_host}: {last_err}", "pdu_host": pdu_host, "outlet": outlet}


def _open_virsh_ncc_shell_channel(kvm_host: str, kvm_user: str, kvm_pass: str, ncc_vms: list, active_ncc: str = None):
    """Blocking: SSH to KVM, virsh console to NCC, auto-login. Returns (ssh, channel, initial_buf).
    Caller must set channel.settimeout as needed (0 for streaming WS, >0 for discovery).
    """
    import paramiko
    import time

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(kvm_host, username=kvm_user, password=kvm_pass, timeout=20, allow_agent=False, look_for_keys=False)
    try:
        channel = ssh.invoke_shell(width=200, height=50)
    except Exception:
        ssh.close()
        raise
    channel.settimeout(30)
    time.sleep(1)

    def _drain(ch, wait=3):
        buf = b""
        deadline = time.time() + wait
        while time.time() < deadline:
            if ch.recv_ready():
                buf += ch.recv(65535)
                deadline = time.time() + 1
            time.sleep(0.2)
        return buf.decode("utf-8", errors="replace")

    _drain(channel, wait=2)

    if not active_ncc:
        channel.send("sudo virsh list --all\n")
        time.sleep(3)
        virsh_output = _drain(channel, wait=3)
        if "running" not in virsh_output.lower() and "Id" not in virsh_output:
            channel.send("virsh list --all\n")
            time.sleep(3)
            virsh_output = _drain(channel, wait=3)
        if ncc_vms:
            for line in virsh_output.split("\n"):
                line_lower = line.lower()
                if "running" in line_lower:
                    for vm_name in ncc_vms:
                        if vm_name in line:
                            active_ncc = vm_name
                            break
                if active_ncc:
                    break
        else:
            for line in virsh_output.split("\n"):
                parts = line.split()
                if len(parts) >= 3 and parts[-1].lower() == "running":
                    vm_candidate = parts[1] if parts[0].isdigit() else parts[0]
                    if "ncc" in vm_candidate.lower():
                        active_ncc = vm_candidate
                        break

    if not active_ncc:
        ssh.close()
        raise ValueError("No running NCC VM found")

    channel.send(f"sudo virsh console --force {active_ncc}\n")
    time.sleep(3)
    deadline = time.time() + 6
    buf = b""
    while time.time() < deadline:
        if channel.recv_ready():
            buf += channel.recv(65535)
            if b"Escape character" in buf:
                break
        time.sleep(0.3)
    time.sleep(0.5)
    channel.send("\n")
    time.sleep(2)
    if channel.recv_ready():
        buf += channel.recv(65535)
    text = buf.decode("utf-8", errors="replace").lower()
    last_line = text.rstrip().split("\n")[-1].strip() if text.rstrip() else ""

    def _try_login_from_login_prompt(ch, cred_pairs, buf_ref):
        """Handle 'login:' prompt -- send user, wait for password:, send pass."""
        for cred_user, cred_pass in cred_pairs:
            ch.send(f"{cred_user}\n".encode())
            time.sleep(1)
            login_buf = b""
            for _ in range(15):
                time.sleep(0.3)
                if ch.recv_ready():
                    login_buf += ch.recv(4096)
                lo = login_buf.decode("utf-8", errors="replace").lower()
                ll = lo.rstrip().split("\n")[-1].strip() if lo.rstrip() else ""
                if ll.endswith("password:") or ll.endswith("password :"):
                    ch.send(f"{cred_pass}\n".encode())
                    buf_ref[0] += login_buf
                    time.sleep(3)
                    post_buf = b""
                    if ch.recv_ready():
                        post_buf = ch.recv(65535)
                    buf_ref[0] += post_buf
                    post_text = post_buf.decode("utf-8", errors="replace").lower()
                    if "incorrect" in post_text or "login:" in post_text.rstrip().split("\n")[-1].strip():
                        logging.info(f"[virsh] {cred_user}/{cred_pass} rejected, trying next")
                        break
                    return True
                if "#" in ll or ">" in ll or "$" in ll:
                    buf_ref[0] += login_buf
                    return True
            else:
                continue
        return False

    def _try_login_from_password_prompt(ch, passwords, buf_ref):
        """Handle bare 'Password:' prompt (stale virsh --force detach)."""
        for pw in passwords:
            ch.send(f"{pw}\n".encode())
            time.sleep(3)
            post = b""
            if ch.recv_ready():
                post = ch.recv(65535)
            buf_ref[0] += post
            pt = post.decode("utf-8", errors="replace").lower()
            ll = pt.rstrip().split("\n")[-1].strip() if pt.rstrip() else ""
            if "#" in ll or ">" in ll or "$" in ll or "last login" in pt:
                return True
            if ll.endswith("login:") and "last login" not in ll:
                ok = _try_login_from_login_prompt(ch, [("dn", "drivenets"), ("dnroot", "dnroot")], buf_ref)
                if ok:
                    return True
        return False

    buf_ref = [buf]
    cred_pairs = [("dn", "drivenets"), ("dnroot", "dnroot")]

    if last_line.endswith("login:") and "last login" not in last_line:
        _try_login_from_login_prompt(channel, cred_pairs, buf_ref)
    elif last_line.endswith("password:") or last_line.endswith("password :"):
        _try_login_from_password_prompt(channel, ["drivenets", "dnroot", "drive1234!"], buf_ref)
    elif not any(c in last_line for c in ("#", ">", "$")):
        channel.send("\n")
        time.sleep(2)
        extra = b""
        if channel.recv_ready():
            extra = channel.recv(65535)
        buf_ref[0] += extra
        et = extra.decode("utf-8", errors="replace").lower()
        el = et.rstrip().split("\n")[-1].strip() if et.rstrip() else ""
        if el.endswith("login:") and "last login" not in el:
            _try_login_from_login_prompt(channel, cred_pairs, buf_ref)
        elif el.endswith("password:") or el.endswith("password :"):
            _try_login_from_password_prompt(channel, ["drivenets", "dnroot", "drive1234!"], buf_ref)

    buf = buf_ref[0]

    # If we landed on a BaseOS bash shell ($), auto-enter DNOS CLI via dncli
    final_text = buf.decode("utf-8", errors="replace") if isinstance(buf, (bytes, bytearray)) else str(buf)
    final_last = final_text.rstrip().split("\n")[-1].strip() if final_text.rstrip() else ""
    if final_last.endswith("$") and "#" not in final_last and ">" not in final_last:
        logging.info("[virsh] Detected BaseOS shell ($), entering DNOS CLI via dncli")
        channel.send("dncli\n")
        dncli_buf = b""
        dncli_deadline = time.time() + 12
        entered_cli = False
        while time.time() < dncli_deadline:
            time.sleep(0.5)
            if channel.recv_ready():
                dncli_buf += channel.recv(65535)
            dncli_text = dncli_buf.decode("utf-8", errors="replace").lower()
            dncli_last = dncli_text.rstrip().split("\n")[-1].strip() if dncli_text.rstrip() else ""
            if dncli_last.endswith("#") or dncli_last.endswith(">"):
                entered_cli = True
                break
            if "password" in dncli_last and ("sudo" in dncli_text or "password" in dncli_last):
                logging.info("[virsh] dncli requires sudo password, sending credentials")
                for pw in ["dnroot", "drivenets", "drive1234!"]:
                    channel.send(f"{pw}\n")
                    time.sleep(3)
                    if channel.recv_ready():
                        dncli_buf += channel.recv(65535)
                    dt = dncli_buf.decode("utf-8", errors="replace").lower()
                    dl = dt.rstrip().split("\n")[-1].strip() if dt.rstrip() else ""
                    if dl.endswith("#") or dl.endswith(">"):
                        entered_cli = True
                        break
                    if "sorry" in dt.split(pw.lower())[-1] if pw.lower() in dt else "":
                        continue
                    if dl.endswith("#") or dl.endswith(">"):
                        entered_cli = True
                        break
                break
        buf += dncli_buf
        if entered_cli:
            logging.info("[virsh] Successfully entered DNOS CLI via dncli")
        else:
            logging.warning("[virsh] dncli may not have entered CLI -- last output: %s",
                            dncli_buf.decode("utf-8", errors="replace")[-200:])

    return ssh, channel, buf


def _connect_virsh_console_sync(kvm_host: str, kvm_user: str, kvm_pass: str, ncc_vms: list, active_ncc: str = None):
    """Blocking: SSH to KVM, run virsh console to active NCC, return (ssh_client, channel).
    Call from thread when method=virsh_console.
    """
    ssh, channel, buf = _open_virsh_ncc_shell_channel(
        kvm_host, kvm_user, kvm_pass, ncc_vms, active_ncc
    )
    channel.settimeout(0)
    return ssh, channel, buf


def _parse_mgmt_ip_from_show_interfaces(text: str) -> str:
    """Extract management IPv4 from 'show interfaces management' output.
    Handles both key-value ('ipv4-address 10.x.x.x/20') and DNOS table format
    ('| mgmt0 | enabled | up | 100.64.11.118/20 (d) |').
    Prefers mgmt0 row; falls back to any mgmt-ncc-* row with an IP.
    """
    import re

    mgmt0_ip = ""
    ncc_mgmt_ip = ""
    for line in text.split("\n"):
        m = re.search(r"\|\s*(mgmt[^\|]*?)\s*\|.*?\|\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?:/\d+)?", line)
        if m:
            iface_name = m.group(1).strip().lower()
            ip = m.group(2).strip()
            if iface_name == "mgmt0" and not mgmt0_ip:
                mgmt0_ip = ip
            elif iface_name.startswith("mgmt-ncc") and not ncc_mgmt_ip:
                ncc_mgmt_ip = ip
    if mgmt0_ip:
        return mgmt0_ip
    if ncc_mgmt_ip:
        return ncc_mgmt_ip

    m = re.search(
        r"(?:ipv4-address|ip-address|ip\s+address)\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?:/\d+)?",
        text,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    for pat in (
        r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*/\s*\d+",
        r"\b(100\.(?:6[4-9]|[7-9]\d|\d{3})\.\d{1,3}\.\d{1,3})\b",
    ):
        m2 = re.search(pat, text)
        if m2:
            return m2.group(1).strip()
    return ""


def _detect_cli_mode_from_buffer(text: str) -> str:
    if "GI(" in text:
        return "GI"
    if "DNOS(" in text:
        return "DNOS"
    return ""


def _discover_ncc_mgmt_ip_sync(
    kvm_host: str, kvm_user: str, kvm_pass: str, ncc_vms: list, active_ncc: str = None
) -> dict:
    """Blocking: virsh console to NCC, run show interfaces management, parse IP, verify SSH dnroot."""
    import paramiko
    import time

    result = {
        "ncc_mgmt_ip": "",
        "device_mode": "",
        "ssh_reachable": False,
        "ssh_auth_ok": False,
        "error": "",
    }
    ssh = None
    channel = None

    def _drain(ch, wait=4):
        buf = b""
        deadline = time.time() + wait
        while time.time() < deadline:
            if ch.recv_ready():
                buf += ch.recv(65535)
                deadline = time.time() + 1
            time.sleep(0.15)
        return buf.decode("utf-8", errors="replace")

    try:
        ssh, channel, initial = _open_virsh_ncc_shell_channel(
            kvm_host, kvm_user, kvm_pass, ncc_vms, active_ncc
        )
        channel.settimeout(8)
        combined = (
            initial.decode("utf-8", errors="replace")
            if isinstance(initial, (bytes, bytearray))
            else str(initial)
        )

        device_mode = _detect_cli_mode_from_buffer(combined)
        result["device_mode"] = device_mode

        channel.send("show interfaces management | no-more\n")
        time.sleep(2)
        combined += _drain(channel, wait=5)

        mgmt_ip = _parse_mgmt_ip_from_show_interfaces(combined)
        if not mgmt_ip:
            channel.send("show interfaces management\n")
            time.sleep(2)
            combined += _drain(channel, wait=5)
            mgmt_ip = _parse_mgmt_ip_from_show_interfaces(combined)

        if not mgmt_ip and "$" in combined[-500:]:
            channel.send("dncli\n")
            time.sleep(2)
            combined += _drain(channel, wait=4)
            channel.send("show interfaces management | no-more\n")
            time.sleep(2)
            combined += _drain(channel, wait=6)
            mgmt_ip = _parse_mgmt_ip_from_show_interfaces(combined)

        result["ncc_mgmt_ip"] = mgmt_ip

        # Exit virsh: Ctrl+] then quit
        try:
            channel.send("\x1d")
            time.sleep(0.4)
            channel.send("quit\n")
            time.sleep(0.5)
            _drain(channel, wait=2)
        except Exception:
            pass
        try:
            channel.close()
        except Exception:
            pass
        try:
            ssh.close()
        except Exception:
            pass
        ssh = None
        channel = None

        if not mgmt_ip:
            result["error"] = "Could not parse management IP from CLI output"
            return result

        sock = __import__("socket").socket(__import__("socket").AF_INET, __import__("socket").SOCK_STREAM)
        sock.settimeout(3.0)
        try:
            sock.connect((mgmt_ip, 22))
            result["ssh_reachable"] = True
        except Exception:
            result["ssh_reachable"] = False
        finally:
            try:
                sock.close()
            except Exception:
                pass

        if result["ssh_reachable"]:
            vssh = paramiko.SSHClient()
            vssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                vssh.connect(
                    mgmt_ip,
                    username="dnroot",
                    password="dnroot",
                    timeout=8,
                    banner_timeout=8,
                    allow_agent=False,
                    look_for_keys=False,
                )
                result["ssh_auth_ok"] = True
                vssh.close()
            except Exception:
                result["ssh_auth_ok"] = False
                try:
                    vssh.close()
                except Exception:
                    pass

    except Exception as e:
        result["error"] = str(e)
        logging.warning(f"[discover_ncc_mgmt] {e}")
    finally:
        if channel:
            try:
                channel.close()
            except Exception:
                pass
        if ssh:
            try:
                ssh.close()
            except Exception:
                pass

    return result

def _build_job_name(body: dict, device_id: str, config_text: str) -> str:
    """Build a descriptive job name from push params."""
    name = body.get("job_name", "").strip()
    if name:
        return name
    lines = len(config_text.strip().split("\n"))
    mode_label = "Commit check" if body.get("dry_run") else (body.get("mode") or "merge").capitalize()
    return f"{lines} lines {mode_label} on {device_id}"

_PUSH_HISTORY_PATH = Path.home() / ".scaler_push_history.json"
_ACTIVE_BUILDS_PATH = Path.home() / ".scaler_active_builds.json"
_ACTIVE_UPGRADES_PATH = Path.home() / ".scaler_active_upgrades.json"
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
    """If job is done, add to history and persist. Evicts stale done jobs from memory."""
    with _push_jobs_lock:
        job = _push_jobs.get(job_id, {})
        if not job.get("done"):
            return
        jobs = _load_push_history()
        jobs.insert(0, _sanitize_job(job))
        jobs = jobs[:_MAX_HISTORY_JOBS]
        _save_push_history(jobs)
        _evict_stale_jobs_locked()
    if job.get("job_type") == "build_monitor":
        _remove_active_build(job_id)


def _evict_stale_jobs_locked():
    """Remove done jobs older than 30 minutes from memory. Must hold _push_jobs_lock."""
    import time
    cutoff = time.time() - 1800
    stale = [jid for jid, j in _push_jobs.items()
             if j.get("done") and j.get("started_at", "") < _iso_from_ts(cutoff)]
    for jid in stale:
        _push_jobs.pop(jid, None)


def _iso_from_ts(ts):
    """Convert unix timestamp to ISO string for comparison."""
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


_INTERNAL_JOB_KEYS = {"_channel", "_client", "_pusher", "_live_output", "_cancel_requested", "_cancel_check"}


def _sanitize_job(job: dict) -> dict:
    """Strip non-serializable internal fields from a job dict for API responses."""
    return {k: v for k, v in job.items() if k not in _INTERNAL_JOB_KEYS}


def _save_active_build(job_id: str, job_data: dict):
    """Persist an active build-monitor job to disk so it survives server restarts."""
    try:
        builds = {}
        if _ACTIVE_BUILDS_PATH.exists():
            with open(_ACTIVE_BUILDS_PATH) as f:
                builds = json.load(f)
        safe = {k: v for k, v in job_data.items() if k not in _INTERNAL_JOB_KEYS}
        builds[job_id] = safe
        with open(_ACTIVE_BUILDS_PATH, "w") as f:
            json.dump(builds, f, indent=2)
    except Exception:
        pass


def _remove_active_build(job_id: str):
    """Remove a completed/failed build from the active builds file."""
    try:
        if not _ACTIVE_BUILDS_PATH.exists():
            return
        with open(_ACTIVE_BUILDS_PATH) as f:
            builds = json.load(f)
        builds.pop(job_id, None)
        with open(_ACTIVE_BUILDS_PATH, "w") as f:
            json.dump(builds, f, indent=2)
    except Exception:
        pass


def _save_active_upgrade(job_id: str, job_data: dict):
    """Persist a running upgrade job to disk so it can be recovered on restart."""
    try:
        upgrades = {}
        if _ACTIVE_UPGRADES_PATH.exists():
            with open(_ACTIVE_UPGRADES_PATH) as f:
                upgrades = json.load(f)
        safe = {k: v for k, v in job_data.items() if k not in _INTERNAL_JOB_KEYS}
        upgrades[job_id] = safe
        with open(_ACTIVE_UPGRADES_PATH, "w") as f:
            json.dump(upgrades, f, indent=2)
    except Exception:
        pass


def _remove_active_upgrade(job_id: str):
    """Remove a completed/failed upgrade from the active upgrades file."""
    try:
        if not _ACTIVE_UPGRADES_PATH.exists():
            return
        with open(_ACTIVE_UPGRADES_PATH) as f:
            upgrades = json.load(f)
        upgrades.pop(job_id, None)
        with open(_ACTIVE_UPGRADES_PATH, "w") as f:
            json.dump(upgrades, f, indent=2)
    except Exception:
        pass


INVENTORY_FILE = Path(__file__).resolve().parent.parent / "device_inventory.json"
DEVICE_INVENTORY_JSON = Path(__file__).resolve().parent.parent / "device_inventory.json"


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


def _build_device_identity(
    device_id: str,
    ssh_host: str,
    mgmt_ip: str,
    scaler_device_id: str,
    hostname: str,
    serial: str,
    config_hostname: str,
    try_ids: list,
    inv_dev: dict | None,
) -> dict:
    """Build unified device identity from all known qualifiers.
    Two devices with same mgmt_ip are considered the same (even if names differ).
    """
    identity = {
        "canvas_label": device_id or "",
        "config_hostname": config_hostname or "",
        "serial": serial or "",
        "mgmt_ip": mgmt_ip or "",
        "ssh_host": (ssh_host or mgmt_ip or "").strip(),
        "scaler_ids": list(dict.fromkeys(i for i in try_ids if i)),
        "inventory_keys": [],
    }
    if inv_dev and DEVICE_INVENTORY_JSON.exists():
        try:
            inv_data = json.loads(DEVICE_INVENTORY_JSON.read_text())
            devices = inv_data.get("devices", {})
            inv_ip = (inv_dev.get("mgmt_ip") or inv_dev.get("ip") or "").strip()
            inv_host = (inv_dev.get("hostname") or "").lower()
            inv_ser = (inv_dev.get("serial") or "").lower()
            for key, dev in devices.items():
                d_ip = (dev.get("mgmt_ip") or dev.get("ip") or "").strip()
                dh = (dev.get("hostname") or "").lower()
                ds = (dev.get("serial") or "").lower()
                if inv_ip and d_ip == inv_ip:
                    identity["inventory_keys"].append(key)
                elif inv_host and dh == inv_host:
                    identity["inventory_keys"].append(key)
                elif inv_ser and ds == inv_ser:
                    identity["inventory_keys"].append(key)
        except Exception:
            pass
    identity["hostname_mismatch"] = bool(
        config_hostname and device_id and config_hostname.lower() != device_id.lower()
    )
    return identity


def _find_inventory_device(device_id: str, ssh_host: str = "") -> dict | None:
    """Find device in device_inventory.json by label, hostname, IP, or serial.
    Returns None when not found (callers use `if inv_dev:` which is falsy for None).
    """
    if not DEVICE_INVENTORY_JSON.exists():
        return None
    try:
        inv_data = json.loads(DEVICE_INVENTORY_JSON.read_text())
        devices = inv_data.get("devices", {})
    except Exception:
        return None

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
        dev_serial = (dev.get("serial") or dev.get("deviceSerial") or "").lower()
        if did_lower and (did_lower in k or k in did_lower or
                          did_lower == dev_hostname or did_lower == dev_serial):
            return dev
    return None


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
        "scale_suggestions": [],
        "policy_suggestions": [],
        "lo0_isis_net": "",
        "detected_l2ac_parent": None,
        "detected_bgp_neighbors": [],
        "existing_route_targets": [],
        "next_free": {"vrf_number": 1, "rt": 1},
        "stack": [],
        "git_commit": None,
        "active_ncc_ip": None,
        "device_state": None,
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
    if ctx["resolved_via"] not in ("failed",) and mgmt_ip:
        idx = _build_scaler_ops_index()
        entry = idx.get(mgmt_ip) or idx.get(device_id.lower())
        if entry:
            hostname = entry.get("hostname", device_id)
            serial = entry.get("serial", "")
    config = _get_cached_config(scaler_device_id)
    if not config and scaler_device_id != device_id:
        config = _get_cached_config(device_id)
    if not config and hostname != device_id:
        config = _get_cached_config(hostname)

    live_ops = {"lldp": [], "stack": [], "git_commit": None}
    if live and mgmt_ip:
        from concurrent.futures import ThreadPoolExecutor
        try:
            user, password = _get_credentials()
            with ThreadPoolExecutor(max_workers=2) as pool:
                config_future = pool.submit(_fetch_config_via_ssh, scaler_device_id, mgmt_ip, user, password)
                ops_future = pool.submit(_fetch_all_operational_via_ssh, mgmt_ip, user, password, scaler_device_id)
                try:
                    config = config_future.result(timeout=25)
                    ctx["cached"] = False
                    ctx["resolved_via"] = f"live_ssh:{mgmt_ip}"
                except Exception:
                    pass
                try:
                    live_ops = ops_future.result(timeout=45)
                except Exception:
                    pass
        except Exception:
            pass

    config_hostname = ""
    if config:
        try:
            from scaler.wizard.parsers import extract_hierarchy_section
            sys_section = extract_hierarchy_section(config, "system")
            if sys_section:
                nm = re.search(r"^\s+name\s+(\S+)", sys_section, re.MULTILINE)
                if nm:
                    config_hostname = (nm.group(1) or "").strip()
        except Exception:
            pass

    base_try_ids = list(dict.fromkeys(i for i in [scaler_device_id, hostname, device_id] if i))
    try_ids = list(base_try_ids)
    if config_hostname and config_hostname not in try_ids:
        try_ids.insert(0, config_hostname)

    if mgmt_ip:
        _build_scaler_ops_index()
        seen_ids = set(i.lower() for i in try_ids)
        for ie in (_scaler_ops_ip_map or {}).get(mgmt_ip, []):
            if ie["scaler_id"].lower() not in seen_ids:
                try_ids.append(ie["scaler_id"])
                seen_ids.add(ie["scaler_id"].lower())
            hn = ie.get("hostname", "")
            if hn and hn.lower() not in seen_ids:
                try_ids.append(hn)
                seen_ids.add(hn.lower())

    inv_dev = _find_inventory_device(device_id, mgmt_ip)
    if not inv_dev and ssh_host:
        inv_dev = _find_inventory_device(ssh_host, mgmt_ip)
    if inv_dev:
        ctx["system_type"] = inv_dev.get("system_type", "")

    if not ctx["system_type"]:
        for _st_try_id in try_ids:
            if not _st_try_id:
                continue
            _st_op = Path(SCALER_ROOT) / "db" / "configs" / _st_try_id / "operational.json"
            if _st_op.exists():
                try:
                    _st_data = json.loads(_st_op.read_text())
                    _st_val = (
                        _st_data.get("system_type")
                        or _st_data.get("deploy_system_type")
                        or ""
                    )
                    if _st_val:
                        ctx["system_type"] = _st_val
                        break
                except Exception:
                    pass

    identity = _build_device_identity(
        device_id=device_id,
        ssh_host=ssh_host or "",
        mgmt_ip=mgmt_ip or "",
        scaler_device_id=scaler_device_id or "",
        hostname=hostname or "",
        serial=serial or "",
        config_hostname=config_hostname or "",
        try_ids=try_ids,
        inv_dev=inv_dev,
    )
    ctx["identity"] = identity

    # LLDP: prefer live SSH data (from parallel fetch), then cached operational.json, then inventory
    if live_ops.get("lldp"):
        ctx["lldp"] = list(live_ops["lldp"])

    if not ctx["lldp"]:
        for try_id in try_ids:
            if not try_id:
                continue
            ops_path = Path(SCALER_ROOT) / "db" / "configs" / try_id / "operational.json"
            if ops_path.exists():
                try:
                    ops = json.loads(ops_path.read_text())
                    for n in ops.get("lldp_neighbors", []):
                        ctx["lldp"].append({
                            "local": n.get("local_interface", n.get("interface", "")),
                            "neighbor": n.get("neighbor_name", n.get("neighbor", "")),
                            "remote": n.get("neighbor_interface", n.get("remote_port", "")),
                        })
                    if ctx["lldp"]:
                        break
                except Exception:
                    pass

    if not ctx["lldp"] and inv_dev:
        lldp_raw = inv_dev.get("lldp_neighbors", [])
        for n in lldp_raw:
            ctx["lldp"].append({
                "local": n.get("local_interface", n.get("interface", "")),
                "neighbor": n.get("neighbor_name", n.get("neighbor_device", n.get("neighbor", ""))),
                "remote": n.get("neighbor_interface", n.get("neighbor_port", n.get("remote_port", ""))),
            })

    # Stack/git/device_state: prefer live SSH data (from parallel fetch), then cached operational.json
    if live_ops.get("stack"):
        ctx["stack"] = list(live_ops["stack"])
    if live_ops.get("git_commit"):
        ctx["git_commit"] = live_ops["git_commit"]
    if live_ops.get("device_state"):
        ctx["device_state"] = live_ops["device_state"]

    for try_id in try_ids:
        if not try_id:
            continue
        if ctx["stack"] and ctx["git_commit"] is not None:
            break
        ops_path = Path(SCALER_ROOT) / "db" / "configs" / try_id / "operational.json"
        if ops_path.exists():
            try:
                ops = json.loads(ops_path.read_text())
                stack_comps = ops.get("stack_components", [])
                if stack_comps and not ctx["stack"]:
                    ctx["stack"] = [
                        {
                            "name": c.get("name", c.get("component", "")),
                            "hw_model": c.get("hw_model", "-"),
                            "revert": c.get("revert", "-"),
                            "current": c.get("current", "-"),
                            "target": c.get("target", "-"),
                        }
                        for c in stack_comps
                    ]
                if ctx["git_commit"] is None and ops.get("git_commit"):
                    ctx["git_commit"] = ops["git_commit"]
                if not ctx.get("active_ncc_ip") and ops.get("mgmt_ip"):
                    ctx["active_ncc_ip"] = ops["mgmt_ip"]
                if ops.get("device_state") and not ctx.get("device_state"):
                    ctx["device_state"] = ops["device_state"]
            except Exception:
                pass

    if live and mgmt_ip and (ctx["stack"] or ctx["git_commit"] or live_ops.get("lldp")):
        try:
            ops_dir = Path(SCALER_ROOT) / "db" / "configs" / scaler_device_id
            ops_dir.mkdir(parents=True, exist_ok=True)
            ops_path = ops_dir / "operational.json"
            ops_data = {}
            if ops_path.exists():
                try:
                    ops_data = json.loads(ops_path.read_text())
                except Exception:
                    pass
            if ctx["stack"]:
                ops_data["stack_components"] = ctx["stack"]
                for comp in ctx["stack"]:
                    cname = (comp.get("name") or "").upper()
                    cver = comp.get("current") or ""
                    if cname == "DNOS" and cver and cver != "-":
                        ops_data["dnos_version"] = cver
                    elif cname == "BASEOS" and cver and cver != "-":
                        ops_data["baseos_version"] = cver
                    elif cname == "GI" and cver and cver != "-":
                        ops_data["gi_version"] = cver
            if ctx["git_commit"]:
                ops_data["git_commit"] = ctx["git_commit"]
            if live_ops.get("lldp"):
                ops_data["lldp_neighbors"] = [
                    {"local_interface": n["local"], "neighbor_name": n["neighbor"], "neighbor_interface": n["remote"]}
                    for n in live_ops["lldp"]
                ]
            ops_data["mgmt_ip"] = mgmt_ip
            ops_data["ssh_host"] = mgmt_ip
            if config_hostname:
                ops_data["hostname"] = config_hostname
            if ctx.get("device_state"):
                ops_data["device_state"] = ctx["device_state"]
            ops_data["_identity"] = identity
            ops_path.write_text(json.dumps(ops_data, indent=2))
        except Exception:
            pass

    iface_details = (inv_dev or {}).get("interface_details", {})

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

            # Phase 2B: Enhanced context fields
            try:
                from scaler.wizard.scale_operations import (
                    _detect_l2ac_parent_from_config_str,
                    _detect_bgp_neighbors,
                    _generate_scale_up_suggestions,
                    parse_services_from_config,
                    _scan_used_route_targets,
                    _scan_used_vrf_numbers,
                )
                ctx["detected_l2ac_parent"] = _detect_l2ac_parent_from_config_str(config)
                ctx["detected_bgp_neighbors"] = _detect_bgp_neighbors(config)
                rt_used = _scan_used_route_targets(config, "65000")
                ctx["existing_route_targets"] = [f"65000:{n}" for n in sorted(rt_used)]
                ctx["next_free"]["rt"] = next((n for n in range(1, 65536) if n not in rt_used), 1)
                vrf_used = _scan_used_vrf_numbers(config, "VRF-")
                ctx["next_free"]["vrf_number"] = next((n for n in range(1, 65536) if n not in vrf_used), 1)
                device_services = {scaler_device_id: parse_services_from_config(config)}
                class _MinimalCtx:
                    configs = {scaler_device_id: config}
                suggestions = _generate_scale_up_suggestions(_MinimalCtx(), device_services)
                ctx["scale_suggestions"] = [{k: v for k, v in s.items() if k != "apply_func" and not callable(v)} for s in suggestions]
                lo0_ip = next((lb["ip"] for lb in ctx["loopbacks"] if lb.get("name") == "lo0"), None)
                if lo0_ip:
                    from scaler.wizard.igp import ip_to_isis_net
                    ctx["lo0_isis_net"] = ip_to_isis_net(lo0_ip, "49.0001")
                rp = ctx.get("routing_policies") or {}
                policy_names = [p.get("name") for p in rp.get("policies", []) if p.get("name")]
                ctx["policy_suggestions"] = policy_names
            except ImportError:
                pass
            except Exception:
                pass

        except ImportError as e:
            ctx["config_summary"] = {"error": str(e)}
        except Exception as e:
            ctx["config_summary"] = {"error": str(e)}

    return ctx


def _compute_wizard_suggestions(device_id: str, completed_wizard: str, created_data: dict, ctx: dict) -> list:
    """Compute next-wizard suggestions from completed wizard and created data."""
    suggestions = []
    interfaces = created_data.get("interfaces") or []
    loopback_ip = created_data.get("loopback_ip") or created_data.get("loopback")
    vrfs = created_data.get("vrfs") or []
    has_interfaces = bool(interfaces)
    has_loopback = bool(loopback_ip)
    has_vrfs = bool(vrfs)

    if completed_wizard == "interfaces":
        if has_interfaces:
            suggestions.append({
                "wizard": "vrf",
                "reason": "Attach new sub-interfaces to VRFs",
                "prefill": {"attachInterfaces": True, "interfaceList": interfaces},
            })
            suggestions.append({
                "wizard": "service",
                "reason": "Create FXC/VPWS with these interfaces",
                "prefill": {"attachInterfaces": True, "interfaceList": interfaces},
            })
        if has_loopback or has_interfaces:
            igp_ifaces = (["lo0"] if has_loopback else []) + list(interfaces)
            suggestions.append({
                "wizard": "igp",
                "reason": "Add loopback + interfaces to IGP",
                "prefill": {"interfaces": igp_ifaces, "router_ip": loopback_ip},
            })
            suggestions.append({
                "wizard": "bgp",
                "reason": "Configure BGP with loopback as update-source",
                "prefill": {"update_source": "lo0", "router_id": loopback_ip},
            })
    elif completed_wizard in ("services", "bridge-domain"):
        if has_interfaces:
            suggestions.append({
                "wizard": "multihoming",
                "reason": "Add multihoming ESI to L2 interfaces",
                "prefill": {"interfaces": interfaces},
            })
        suggestions.append({"wizard": "flowspec", "reason": "Add FlowSpec local policy", "prefill": {}})
    elif completed_wizard == "vrf":
        if has_vrfs:
            suggestions.append({
                "wizard": "bgp",
                "reason": "Add BGP VRF instance for new VRFs",
                "prefill": {"vrfs": vrfs},
            })
        suggestions.append({"wizard": "flowspec-vpn", "reason": "Add FlowSpec VPN policy", "prefill": {"vrfs": vrfs}})
    elif completed_wizard == "igp":
        suggestions.append({"wizard": "bgp", "reason": "Configure BGP peers", "prefill": {"update_source": "lo0"}})
    elif completed_wizard == "bgp":
        suggestions.append({"wizard": "flowspec", "reason": "Enable BGP FlowSpec AFI on neighbors", "prefill": {}})
    elif completed_wizard in ("flowspec", "flowspec-vpn"):
        suggestions.append({"wizard": "routing-policy", "reason": "Create routing policy for BGP attach", "prefill": {}})

    return suggestions

