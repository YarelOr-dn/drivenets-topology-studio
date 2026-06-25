"""Scaler bridge routes: ssh."""
from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path

from fastapi import APIRouter, Body, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from routes.bridge_helpers import (
    SCALER_ROOT, _connect_virsh_console_sync, _discover_console,
    _discover_ncc_mgmt_ip_sync, _fetch_zohar_db, _get_credentials,
    _get_known_console_servers, _lookup_zohar_pdu, _mark_device_ip_stale,
    _pdu_power_action, _probe_active_ncc_via_kvm, _probe_console_server,
    _resolve_active_ncc_host, _resolve_mgmt_ip, _save_discovered_console,
    _seed_cluster_metadata_from_mappings, _ssh_pool,
)
from routes._state import _push_jobs, _push_jobs_lock, _get_request_user
from routes._ops_writer import read_ops as _read_ops_safe, update_ops as _update_ops

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Ghost-IP identity guard helpers
# ---------------------------------------------------------------------------
# After an SSH connect succeeds we read the login banner/prompt buffer and
# compare the remote hostname against the device_id the user clicked on.
# If they disagree we treat it as a ghost-IP incident: the IP was likely
# reassigned after a device upgrade. The session is closed before the user
# gets a shell on the wrong DUT, the stale record is reaped, and the
# frontend shows a "released its IP" notice so the user can re-discover.

# Matches DNOS CLI prompt lines like "YOR_PE-1#", "PE-4>", "RR-SA-2(cfg)#"
# and bash prompts like "dn@kvm108:~$" or "root@r7-natan:/$".
_PROMPT_RE = re.compile(
    r"""(?mx)
    (?:
        (?P<bash>[\w.-]+)@(?P<host_bash>[\w.-]+?)(?::[^\#\$]*)?\s*[\#\$]\s*$
      |
        (?P<host_cli>[A-Za-z][\w.-]*)
        (?:\([^)]*\))?
        \s*[>\#]\s*$
    )
    """
)


def _extract_remote_hostname(buf_text: str) -> str:
    """Pull the remote device hostname from a banner/prompt buffer.

    Returns the cleanest hostname we can see, or "" when we cannot
    identify one (in which case callers MUST NOT fail the identity check).
    """
    if not buf_text:
        return ""
    cleaned = re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", buf_text)
    last = ""
    for m in _PROMPT_RE.finditer(cleaned):
        host = m.group("host_cli") or m.group("host_bash") or ""
        host = host.strip()
        # Ignore noise: "login", "password", very short or pure-digit
        if not host or host.lower() in {"login", "password", "last"}:
            continue
        if len(host) < 2:
            continue
        if host.isdigit():
            continue
        last = host
    return last


def _normalize_identity(name: str) -> str:
    """Strip delimiters + lowercase so 'YOR_CL_PE-4' ~= 'pe4' after boiling down."""
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


# Generic / recovery-mode prompts that appear on many different DNOS
# devices and carry no identity information. When we see one of these
# we must NOT fail the identity check (they could legitimately be the
# target device in a degraded state), but we also must not trust them
# as proof of identity. Callers should treat these as "unknown".
_GENERIC_PROMPT_HOSTS = frozenset({
    "gi", "recovery", "baseos", "baseosshell", "grub",
    "login", "loginas", "user", "root",
    "linux", "localhost", "unknown",
    "dnos", "ncc", "ncp",
})


def _is_generic_prompt(actual_hostname: str) -> bool:
    """True when the captured hostname is a non-identifying recovery prompt."""
    n = _normalize_identity(actual_hostname)
    return n in _GENERIC_PROMPT_HOSTS


def _identity_matches(expected_id: str, expected_hostname: str, actual_hostname: str) -> bool:
    """Fuzzy identity check. True when we cannot disprove identity.

    Rules:
      * No actual hostname captured -> TRUE (don't false-alarm).
      * Generic recovery-mode prompt (GI/RECOVERY/BASEOS/...) -> TRUE
        (could be our device, just in a degraded state).
      * Normalized strings share a >=2-char substring in either direction -> TRUE.
      * Otherwise -> FALSE (ghost IP candidate).
    """
    actual_norm = _normalize_identity(actual_hostname)
    if not actual_norm or len(actual_norm) < 2:
        return True
    if _is_generic_prompt(actual_hostname):
        return True
    candidates = []
    for src in (expected_id, expected_hostname):
        n = _normalize_identity(src)
        if n and len(n) >= 2:
            candidates.append(n)
    if not candidates:
        return True
    for want in candidates:
        if want in actual_norm or actual_norm in want:
            return True
        # Numeric-core match: "pe4" vs "r7pe4core" - check common >=3 substrings
        if len(want) >= 3:
            for i in range(len(want) - 2):
                if want[i:i + 3] in actual_norm:
                    return True
    return False


def _expected_hostname_for_device(device_id: str) -> str:
    """Best-effort lookup of the hostname we expect at device_id."""
    if not device_id:
        return ""
    try:
        ops_path = Path(SCALER_ROOT) / "db" / "configs" / device_id / "operational.json"
        if ops_path.exists():
            ops = _read_ops_safe(ops_path)
            hn = (ops.get("hostname") or "").strip()
            if hn:
                return hn
    except Exception:
        pass
    return ""

router = APIRouter()

@router.post("/api/ssh-pool/toggle")
def ssh_pool_toggle(body: dict = None, request: Request = None):
    """Toggle SSH connection pool on/off. Body: { enabled: true/false }"""
    body = body or {}
    on = body.get("enabled", False)
    app_user = _get_request_user(request) if request else "default"
    result = _ssh_pool.toggle(on, app_user=app_user)
    return result


@router.get("/api/ssh-pool/status")
def ssh_pool_status(request: Request = None):
    """Return pool state: enabled, count, per-device connection age/state (scoped to user)."""
    app_user = _get_request_user(request) if request else None
    return _ssh_pool.status(app_user=app_user)


@router.post("/api/ssh-pool/evict")
def ssh_pool_evict(body: dict = None, request: Request = None):
    """Force-close pooled SSH client(s). Body: { ip: str, device_id?: str }

    Pool entries are keyed by (app_user, management IPv4). The canvas ``ip``
    field may be a serial or hostname; optional ``device_id`` is passed to
    ``_resolve_mgmt_ip`` to find the real mgmt IP.
    """
    body = body or {}
    raw = (body.get("ip") or "").strip()
    device_id = (body.get("device_id") or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="ip required")

    app_user = _get_request_user(request) if request else "default"
    evicted_keys = []

    def _do_evict(addr: str) -> None:
        addr = (addr or "").strip().split("/")[0]
        if not addr:
            return
        _ssh_pool.evict(addr, app_user=app_user)
        if addr not in evicted_keys:
            evicted_keys.append(addr)

    _do_evict(raw)

    is_ipv4 = bool(raw and re.match(r"^\d+\.\d+\.\d+\.\d+$", raw))
    if not is_ipv4:
        did = device_id or raw
        ssh_h = raw
        try:
            mgmt_ip, _, _ = _resolve_mgmt_ip(did, ssh_h)
            mgmt_ip = (mgmt_ip or "").strip().split("/")[0]
            if mgmt_ip:
                _do_evict(mgmt_ip)
        except HTTPException:
            pass
        except Exception:
            pass

    primary = evicted_keys[-1] if evicted_keys else raw
    return {"status": "ok", "evicted": primary, "evicted_keys": evicted_keys}


@router.post("/api/ssh/clear-ghost-ip")
def clear_ghost_ip(body: dict = None, request: Request = None):
    """Explicit cleanup for a stale / ghost IP.

    Body: {
        device_id: str,          # canvas / scaler id we thought we were dialling
        ip?: str,                # the IP that turned out to be wrong
        actual_hostname?: str,   # what answered when we did dial it
        reason?: str,            # machine tag (default: "user_cleared")
    }

    Flags the operational.json as stale, evicts the pool, drops the resolve
    cache, and prunes the legacy devices.json entry. Idempotent: calling it
    twice on an already-reaped device just confirms the state.
    """
    body = body or {}
    device_id = (body.get("device_id") or "").strip()
    ip = (body.get("ip") or "").strip()
    actual_hostname = (body.get("actual_hostname") or "").strip()
    reason = (body.get("reason") or "user_cleared").strip() or "user_cleared"
    if not device_id and not ip:
        raise HTTPException(status_code=400, detail="device_id or ip required")
    app_user = _get_request_user(request) if request else "default"
    # Permission: only an active watcher of this device OR an admin may
    # reap. Prevents a random logged-in user from nuking another team's
    # canvas state.
    try:
        from api.device_state import device_state
        from routes._state import _get_request_role
        role = _get_request_role(request) if request else "viewer"
        if role != "admin" and device_id:
            if not device_state.is_watcher(device_id, app_user):
                raise HTTPException(
                    status_code=403,
                    detail=(
                        f"User '{app_user}' is not an active watcher of "
                        f"'{device_id}'. Only watchers or admins may reap ghost IPs."
                    ),
                )
    except HTTPException:
        raise
    except Exception as perm_exc:
        logger.warning("[clear-ghost-ip] permission check skipped: %s", perm_exc)
    try:
        summary = _mark_device_ip_stale(
            scaler_id=device_id,
            stale_ip=ip,
            reason=reason,
            actual_hostname=actual_hostname,
            acting_user=app_user,
        )
    except Exception as exc:
        logger.exception("[clear-ghost-ip] failed device=%s ip=%s", device_id, ip)
        raise HTTPException(status_code=500, detail=f"ghost-ip cleanup failed: {exc}")
    summary["app_user"] = app_user
    return summary


@router.post("/api/ssh/verify-identity")
def verify_ssh_identity(body: dict = None, request: Request = None):
    """Lightweight SSH identity pre-flight.

    Opens a short-lived SSH connection to (ip:port) with default DNOS creds,
    reads the login banner + initial prompt, then closes the channel before
    dropping the user into it. Compares the captured hostname against the
    expected device_id using the same fuzzy matcher as the terminal WS guard.

    Body: {
        device_id: str,    # canvas / scaler hostname we expect (e.g. "YOR_CL_PE-4")
        ip: str,           # IPv4 we're about to SSH to
        port?: int,        # default 22
        user?: str,        # default "dnroot"
        password?: str,    # default "dnroot"
        auto_reap?: bool,  # default true: reap stale record when mismatch
    }

    Returns:
        {
          reachable: bool,              # TCP 22 open?
          identity_verified: bool,      # True when hostname matches (or we
                                        #   could not capture one -- we never
                                        #   false-alarm).
          actual_hostname: str,         # what the remote advertised (may be "")
          expected_hostname: str,
          reason?: str,                 # "port_closed", "auth_failed",
                                        #   "ghost_ip", "timeout"
          reaped?: dict,                # _mark_device_ip_stale summary, if fired
        }

    This endpoint never raises on identity mismatch -- it simply returns
    identity_verified=false so the caller (SSH button fast path) can decide
    to fall through to the dialog / probe / cluster recovery path.
    """
    import socket
    import paramiko

    body = body or {}
    device_id = (body.get("device_id") or "").strip()
    ip = (body.get("ip") or "").strip().split("/")[0]
    port = int(body.get("port") or 22)
    user = (body.get("user") or "dnroot").strip() or "dnroot"
    password = body.get("password")
    if not password:
        password = "dnroot"
    auto_reap = body.get("auto_reap")
    if auto_reap is None:
        auto_reap = True
    if not ip or not re.match(r"^\d+\.\d+\.\d+\.\d+$", ip):
        raise HTTPException(status_code=400, detail="ip (IPv4) required")

    app_user = _get_request_user(request) if request else "default"
    expected_hostname = _expected_hostname_for_device(device_id) or device_id

    result = {
        "reachable": False,
        "identity_verified": False,
        "actual_hostname": "",
        "expected_hostname": expected_hostname,
        "ip": ip,
        "port": port,
    }

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.5)
    try:
        s.connect((ip, port))
        result["reachable"] = True
    except Exception:
        result["reason"] = "port_closed"
        return result
    finally:
        try:
            s.close()
        except Exception:
            pass

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    chan = None
    try:
        client.connect(
            ip, port=port, username=user, password=password,
            timeout=4.0, banner_timeout=4.0, auth_timeout=4.0,
            allow_agent=False, look_for_keys=False,
        )
        chan = client.invoke_shell(term="xterm", width=160, height=40)
        # Drain for up to ~3s, with a gentle nudge if the remote is silent.
        deadline = time.time() + 3.0
        buf = b""
        nudged = False
        last_recv = time.time()
        while time.time() < deadline:
            if chan.recv_ready():
                try:
                    chunk = chan.recv(4096)
                    if not chunk:
                        break
                    buf += chunk
                    last_recv = time.time()
                    if len(buf) > 32768:
                        break
                    if buf.rstrip().endswith((b"#", b"$", b">")):
                        # Got a prompt -- give a short grace period for trailing output
                        time.sleep(0.15)
                        if chan.recv_ready():
                            buf += chan.recv(4096)
                        break
                except Exception:
                    break
            else:
                # Send a harmless newline once if the remote has been silent
                # (some DNOS/baseos shells don't emit a prompt until input).
                if not nudged and (time.time() - last_recv) > 0.7:
                    try:
                        chan.send(b"\r")
                        nudged = True
                    except Exception:
                        pass
                time.sleep(0.08)
        text = buf.decode("utf-8", errors="replace")
        actual = _extract_remote_hostname(text)
        result["actual_hostname"] = actual
        generic = _is_generic_prompt(actual)
        result["generic_prompt"] = generic
        matches = _identity_matches(device_id, expected_hostname, actual)
        result["identity_verified"] = bool(matches)
        if generic:
            # Ambiguous recovery/login prompt -- don't reap, but tell the
            # caller this wasn't a confirmed positive identity either.
            result["reason"] = "generic_prompt"
            result["identity_verified"] = False
        elif not matches:
            result["reason"] = "ghost_ip"
            if auto_reap:
                try:
                    summary = _mark_device_ip_stale(
                        scaler_id=device_id,
                        stale_ip=ip,
                        reason="ghost_ip_preflight",
                        actual_hostname=actual,
                        acting_user=app_user,
                    )
                    result["reaped"] = summary
                except Exception as exc:
                    logger.warning("[verify-identity] reap failed: %s", exc)
    except paramiko.AuthenticationException:
        result["reason"] = "auth_failed"
    except Exception as exc:
        result["reason"] = f"error: {exc}"
    finally:
        try:
            if chan:
                chan.close()
        except Exception:
            pass
        try:
            client.close()
        except Exception:
            pass
    return result


@router.post("/api/ssh/probe")
def probe_connection(body: dict = None, request: Request = None):
    """Probe available connection methods for a device.
    Body: { device_id: str, ssh_host?: str }
    Returns: { methods: [{ method: str, host: str, port: int, reachable: bool, latency_ms?: int }],
               recommended: str, device_state: str, stale_note?: str }

    Graceful degradation for ghost-IP reaped devices: if the mgmt IP cannot
    be resolved (e.g. released after an upgrade) we still return cluster
    recovery paths -- virsh_console via the stored KVM host + per-NCC SSH
    targets -- so the user can recover without needing to manually dig up
    the new mgmt IP.

    Side effect (auto-capture): on any probe that succeeds in building
    ``cluster_info`` with real KVM / NCC data, we mirror that data into
    the requesting user's
    ``~/.topology_users/<user>/devices.json[<device_id>].console_fallback``.
    This is the durable backup-connection store used when
    ``operational.json`` gets wiped by a system delete or a ghost-IP
    reap; the user never has to manually re-enter their KVM creds or
    the NCC VM names because the last successful probe has already
    stamped them into the per-user devices.json.
    """
    import socket
    body = body or {}
    device_id = (body.get("device_id") or "").strip()
    ssh_host = (body.get("ssh_host") or "").strip()
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    stale_note = ""
    # Self-heal cluster metadata BEFORE resolving mgmt_ip / reading ops.
    # If operational.json was wiped by a hostile writer, this restores
    # ncc_type/kvm_host/ncc_vms/ncc_mgmt_ip/is_cluster from
    # console_mappings.json so the probe can still detect the cluster
    # recovery path instead of falling back to a dead VIP.
    try:
        from routes.bridge_helpers import _resolve_config_dir as _rcd
        _candidate_scaler_id = _rcd(device_id) or device_id
    except Exception:
        _candidate_scaler_id = device_id
    for _cid in (_candidate_scaler_id, device_id):
        try:
            _seed_cluster_metadata_from_mappings(_cid)
        except Exception:
            pass
    try:
        mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(device_id, ssh_host)
    except HTTPException as resolve_err:
        # Try to preserve cluster recovery even when no mgmt IP is known.
        try:
            from routes.bridge_helpers import _resolve_config_dir
            scaler_id = _resolve_config_dir(device_id) or device_id
        except Exception:
            scaler_id = device_id
        ops_path = Path(SCALER_ROOT) / "db" / "configs" / scaler_id / "operational.json"
        if not ops_path.exists():
            raise resolve_err
        try:
            ops_for_fallback = _read_ops_safe(ops_path)
        except Exception:
            raise resolve_err
        if not (ops_for_fallback.get("_stale")
                or ops_for_fallback.get("kvm_host")
                or ops_for_fallback.get("ncc_mgmt_ip")):
            raise resolve_err
        mgmt_ip = ""
        if ops_for_fallback.get("_stale"):
            stale_note = (
                f"Management IP released (was {ops_for_fallback.get('_stale_last_mgmt_ip', '?')}"
                f", reason: {ops_for_fallback.get('_stale_reason', 'ghost_ip')}). "
                "Use virsh console or per-NCC SSH to re-discover the new IP."
            )
        else:
            stale_note = "No mgmt IP known -- falling back to cluster recovery paths."
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
    ip = ssh_host or mgmt_ip
    if not ip and not stale_note:
        raise HTTPException(status_code=400, detail="Could not resolve device IP")
    try:
        from scaler.connection_strategy import DeviceConnector, ConnectionMethod, get_console_config_for_device, _derive_kvm_host
        class _TempDevice:
            pass
        dev = _TempDevice()
        dev.hostname = scaler_id
        dev.ip = ip
        dev.serial_number = None
        dev.username = "dnroot"
        dev.password = "dnroot"
        dev.loopback_ip = None
        try:
            ops_path = Path(SCALER_ROOT) / "db" / "configs" / scaler_id / "operational.json"
            if ops_path.exists():
                ops = _read_ops_safe(ops_path)
                dev.serial_number = ops.get("serial_number") or ops.get("serial")
                dev.loopback_ip = (ops.get("loopback_ip") or "").split("/")[0] or None
        except Exception:
            pass
        console_config = get_console_config_for_device(scaler_id)
        connector = DeviceConnector(dev, console_config)
        targets = connector.get_probe_targets()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Connection strategy: {e}")
    method_map = {
        ConnectionMethod.SSH_SN: "ssh_sn",
        ConnectionMethod.SSH_MGMT: "ssh_mgmt",
        ConnectionMethod.SSH_NCC: "ssh_ncc",
        ConnectionMethod.VIRSH_CONSOLE: "virsh_console",
        ConnectionMethod.CONSOLE: "console",
        ConnectionMethod.SSH_LOOPBACK: "ssh_loopback",
    }
    results = []
    recommended = None
    for method, host, port in targets:
        if not host:
            continue
        t0 = time.perf_counter()
        reachable = False
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        try:
            sock.connect((host, port))
            reachable = True
        except Exception:
            pass
        finally:
            try:
                sock.close()
            except Exception:
                pass
        latency_ms = int((time.perf_counter() - t0) * 1000) if reachable else None
        mname = method_map.get(method, str(method))
        entry = {"method": mname, "host": host, "port": port, "reachable": reachable, "latency_ms": latency_ms}
        if method == ConnectionMethod.VIRSH_CONSOLE:
            try:
                kvm_cfg = connector._get_kvm_host_config() or {}
                entry["kvm_host_name"] = kvm_cfg.get("kvm_host", "")
                entry["kvm_credentials"] = kvm_cfg.get("kvm_host_credentials", {})
                entry["ncc_vms"] = kvm_cfg.get("ncc_vms", [])
                if reachable and kvm_cfg.get("kvm_host_credentials", {}).get("username"):
                    try:
                        import paramiko as _pmk2
                        _kssh = _pmk2.SSHClient()
                        _kssh.set_missing_host_key_policy(_pmk2.AutoAddPolicy())
                        _kc = kvm_cfg["kvm_host_credentials"]
                        _kssh.connect(host, username=_kc["username"],
                                      password=_kc.get("password", ""),
                                      timeout=5, allow_agent=False, look_for_keys=False)
                        _, _out, _ = _kssh.exec_command("sudo virsh list --all 2>/dev/null || virsh list --all 2>/dev/null", timeout=5)
                        _virsh = _out.read().decode("utf-8", errors="replace")
                        _kssh.close()
                        running = [vm for vm in kvm_cfg.get("ncc_vms", [])
                                   if vm in _virsh and "running" in _virsh.split(vm)[1].split("\n")[0].lower()]
                        defined = [vm for vm in kvm_cfg.get("ncc_vms", []) if vm in _virsh]
                        entry["vms_running"] = running
                        entry["vms_defined"] = defined
                        if not running and not defined:
                            entry["reachable"] = True
                            entry["vm_warning"] = "No NCC VMs exist on KVM host -- device needs redeployment"
                        elif not running:
                            entry["vm_warning"] = f"NCC VMs defined but not running: {', '.join(defined)}"
                    except Exception:
                        pass
            except Exception:
                pass
        results.append(entry)
        if reachable and not recommended:
            recommended = mname
    device_state = ""
    cluster_info = None
    ncc_mgmt_ip_out = ""
    ncc_mgmt_verified_at_out = ""
    _early_res = None
    ops_path = Path(SCALER_ROOT) / "db" / "configs" / scaler_id / "operational.json"
    try:
        if ops_path.exists():
            ops = _read_ops_safe(ops_path)
            device_state = ops.get("device_state", "") or ""
            _nip = (ops.get("ncc_mgmt_ip") or "").strip()
            if _nip:
                ncc_mgmt_ip_out = _nip
                ncc_mgmt_verified_at_out = (ops.get("ncc_mgmt_verified_at") or "").strip()
            needs_ops_write = False
            if recommended:
                ops["last_working_method"] = recommended
                ops["connection_probe_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                needs_ops_write = True
            # DNS-based active-NCC self-heal runs BEFORE the ops write so the
            # corrected active_ncc_vm persists to disk on every probe.
            # When DNS is inconclusive (source != "dns_match"), fall back to
            # querying the KVM host directly via virsh. This is critical for
            # GI/RECOVERY mode where the cluster VIP is unclaimed and DNS
            # returns the same IP for both NCCs.
            if ops.get("ncc_type") == "kvm":
                try:
                    _early_vms = ops.get("ncc_vms") or ops.get("ncc_hosts") or []
                    _early_res = _resolve_active_ncc_host(
                        _early_vms,
                        ops.get("ncc_mgmt_ip", ""),
                        ops.get("active_ncc_vm", ""),
                    )
                    _early_active = _early_res.get("active_ncc_host", "")
                    _early_source = _early_res.get("source", "")
                    if _early_source != "dns_match":
                        try:
                            _kvm_host = (
                                ops.get("kvm_host_ip")
                                or ops.get("kvm_host")
                                or ""
                            ) or ""
                            _kvm_host = _kvm_host.split("/")[0].strip()
                            _kvm_cfg = (
                                ops.get("kvm_host_credentials")
                                or ops.get("kvm_credentials")
                                or {}
                            )
                            _kvm_user = (_kvm_cfg.get("username") or "dn") or "dn"
                            _kvm_pass = (_kvm_cfg.get("password") or "drive1234!") or "drive1234!"
                            if _kvm_host and _early_vms:
                                _kvm_res = _probe_active_ncc_via_kvm(
                                    _kvm_host, _kvm_user, _kvm_pass,
                                    _early_vms, ops.get("ncc_mgmt_ip", ""),
                                )
                                _kvm_active = _kvm_res.get("active_ncc_host", "")
                                _kvm_source = _kvm_res.get("source", "")
                                if _kvm_active and _kvm_source.startswith("kvm_"):
                                    _early_active = _kvm_active
                                    _early_source = _kvm_source
                                    _early_res["active_ncc_host"] = _kvm_active
                                    _early_res["active_ncc_ip"] = _kvm_res.get("active_ncc_ip") or _early_res.get("active_ncc_ip")
                                    _early_res["source"] = _kvm_source
                                    _early_res["dns_map"] = {**(_early_res.get("dns_map") or {}),
                                                             **(_kvm_res.get("dns_map") or {})}
                        except Exception:
                            pass

                    # When our live signals are inconclusive (kvm_first_running
                    # just picks index 0 when both NCCs are running), trust the
                    # virsh-console probe's ``active_ncc_vm`` if it wrote a
                    # value to ops recently -- virsh_console only updates that
                    # field after SUCCESSFULLY attaching to the VM's console,
                    # which is a MUCH stronger signal than "both VMs are
                    # running". This read happens after the virsh-console
                    # probe above (it wrote ops on disk; we re-read here to
                    # pick up that write in the same probe cycle).
                    if _early_source in ("kvm_first_running", "fallback", "cached"):
                        try:
                            _fresh_ops = _read_ops_safe(ops_path)
                            _virsh_verified_vm = (_fresh_ops.get("active_ncc_vm") or "").strip()
                            _fresh_vms = _fresh_ops.get("ncc_vms") or []
                            _virsh_success = any(
                                (m.get("method") == "virsh_console" and m.get("reachable"))
                                for m in results
                            )
                            if (
                                _virsh_verified_vm
                                and _virsh_verified_vm in _fresh_vms
                                and _virsh_success
                                and _virsh_verified_vm != _early_active
                            ):
                                _early_active = _virsh_verified_vm
                                _early_source = "virsh_console_verified"
                                _early_res["active_ncc_host"] = _virsh_verified_vm
                                _early_res["source"] = _early_source
                                try:
                                    ops["active_ncc_vm"] = _virsh_verified_vm
                                except Exception:
                                    pass
                        except Exception:
                            pass
                    if (
                        _early_active
                        and _early_active in (ops.get("ncc_vms") or ops.get("ncc_hosts") or [])
                        and ops.get("active_ncc_vm", "") != _early_active
                        and _early_source in ("dns_match", "kvm_domifaddr_match",
                                              "kvm_arp_mac_match", "kvm_only_running",
                                              "virsh_console_verified")
                    ):
                        ops["active_ncc_vm"] = _early_active
                        ops["active_ncc_source"] = _early_source
                        needs_ops_write = True
                    elif (
                        _early_source
                        and ops.get("active_ncc_source") != _early_source
                    ):
                        ops["active_ncc_source"] = _early_source
                        needs_ops_write = True
                except Exception:
                    pass
            if ops.get("ncc_type") == "kvm":
                _ipv4_re = re.compile(r"^\d+\.\d+\.\d+\.\d+$")
                best_ssh = None
                for m in results:
                    if not m.get("reachable"):
                        continue
                    if m.get("method") not in ("ssh_mgmt", "ssh_ncc"):
                        continue
                    h = (m.get("host") or "").strip().split("/")[0]
                    if _ipv4_re.match(h):
                        best_ssh = m
                        break
                if best_ssh:
                    new_ip = (best_ssh.get("host") or "").strip().split("/")[0]
                    old_ip = (ops.get("mgmt_ip") or "").strip().split("/")[0]
                    if new_ip and new_ip != old_ip:
                        ops["mgmt_ip"] = new_ip
                        ops["ssh_host"] = new_ip
                        needs_ops_write = True
            if needs_ops_write:
                # Atomic + flocked write through the canonical helper. The
                # mutator overlays the in-memory ``ops`` we just edited
                # onto whatever's on disk, so a concurrent scaler write
                # between our read and our write is preserved (the
                # no-shrink invariant additionally protects keys we
                # didn't touch).
                def _mut_probe(d, _src=ops):
                    for k, v in _src.items():
                        d[k] = v

                try:
                    _update_ops(ops_path, _mut_probe, create_if_missing=False)
                except Exception:
                    pass
            if ops.get("ncc_type") == "kvm":
                ncc_vms = ops.get("ncc_vms", [])
                ncc_hosts = ops.get("ncc_hosts", [])
                # Cluster devices typically carry DNS-resolvable hostnames
                # only in `ncc_vms` (console_mappings.json).
                # `ncc_hosts` is populated by the scaler DeviceConnector
                # when SSH→NCC succeeds, but in GI / RECOVERY mode SSH is
                # dead so that list stays empty. For the frontend
                # active-NCC iTerm path we prefer `ncc_hosts[0]` -- when
                # empty we MUST fall back to `ncc_vms` otherwise the
                # active-NCC target resolution returns "" and the
                # browser skips the iTerm launch path entirely.
                _resolve_source = list(ncc_hosts) if ncc_hosts else list(ncc_vms or [])
                kvm_host = _derive_kvm_host(ops.get("kvm_host", "") or "")
                console_cfg = ops.get("ncc_console_credentials", {})
                # Reuse the already-resolved active NCC from the early
                # self-heal step above when it yielded a live/definitive
                # source (dns_match or any kvm_*). This avoids a second
                # expensive KVM SSH probe per `/api/ssh/probe` call.
                try:
                    _reuse_ok = (
                        _early_res
                        and _early_res.get("active_ncc_host")
                        and _early_res.get("source", "").startswith(("dns_match", "kvm_"))
                    )
                except Exception:
                    _reuse_ok = False
                if _reuse_ok:
                    _ncc_resolve = _early_res
                else:
                    _ncc_resolve = _resolve_active_ncc_host(
                        _resolve_source,
                        ops.get("ncc_mgmt_ip", ""),
                        ops.get("active_ncc_vm", ""),
                    )
                active_host = _ncc_resolve.get("active_ncc_host", "")
                # Re-order ncc_hosts so the active NCC is first (frontend uses [0] as primary)
                _ordered_ncc_hosts = list(ncc_hosts) if ncc_hosts else list(ncc_vms or [])
                if active_host and active_host in _ordered_ncc_hosts and _ordered_ncc_hosts[0] != active_host:
                    _ordered_ncc_hosts = [active_host] + [h for h in _ordered_ncc_hosts if h != active_host]
                # Rewrite the ssh_ncc probe entry host to match the DNS-detected active NCC
                # (the DeviceConnector used stale active_ncc_vm when ordering probe targets)
                try:
                    for _m in results:
                        if _m.get("method") == "ssh_ncc" and active_host:
                            _m["host"] = active_host
                            _m["active_ncc_source"] = _ncc_resolve.get("source", "")
                            break
                except Exception:
                    pass
                # Pick the IP the FRONTEND should use for ``ssh://dnroot@<ip>``.
                #
                # Key insight (from 2026-04-23 field test): in GI /
                # BASEOS_SHELL / RECOVERY mode the cluster VIP is
                # ``ssh_mgmt`` TCP-reachable but **does NOT accept
                # dnroot**. Something else (baseos sshd, stale lease
                # owner, ghost device) is answering on :22. Launching
                # iTerm to the VIP therefore drops the operator on
                # three ``Permission denied`` prompts with no clue
                # that the path is wrong. The correct target in those
                # modes is the ACTIVE NCC's per-node hostname / IP,
                # which the NCC's own baseos has sshd accepting the
                # usual lab creds; the DEFINITIVE path is virsh
                # console via the KVM host.
                #
                # Priority (by device_state):
                #   DNOS / unknown:
                #     1. DNS-resolved PER-NODE IP   (active NCC's own sshd
                #        always accepts the universal lab dnroot/dnroot
                #        credential pair, and lab routing reaches it via
                #        VPN even when the operator's Mac has no lab DNS)
                #     2. VIP if ``ssh_mgmt`` reachable
                #        (kept as fallback for legacy clusters whose VIP
                #        listener does accept dnroot)
                #     3. VIP (last resort)
                #   GI / BASEOS_SHELL / RECOVERY:
                #     1. DNS-resolved per-node IP       (NCC's own sshd)
                #     2. ncc_hosts[0] hostname          (lab DNS route)
                #     3. None                           (frontend -> virsh)
                #
                # 27-Apr-2026 inversion (was VIP-first for DNOS):
                # the YOR_CL_PE-4 cluster's VIP listener rejects
                # dnroot/dnroot even though the per-node sshds accept it.
                # Sending the SSH button to the VIP loops the operator
                # on a "Permission denied" prompt while the working path
                # (per-node IP) sits in ncc_dns_map[active_ncc_host].
                _vip_candidate = (ops.get("ncc_mgmt_ip") or "").strip().split("/")[0]
                _dev_state_upper = (device_state or "").upper()
                _is_recovery = _dev_state_upper in ("GI", "BASEOS_SHELL", "RECOVERY")
                _vip_ssh_reachable = False
                try:
                    for _rm in results:
                        if (_rm.get("method") == "ssh_mgmt"
                                and _rm.get("reachable")
                                and (_rm.get("host") or "").strip().split("/")[0] == _vip_candidate):
                            _vip_ssh_reachable = True
                            break
                except Exception:
                    pass
                _dns_active_ip = _ncc_resolve.get("active_ncc_ip")
                if _is_recovery:
                    # GI / BASEOS_SHELL / RECOVERY: NEVER return the VIP.
                    # The VIP in these modes is either unclaimed or held
                    # by a baseos sshd that rejects dnroot. The only
                    # direct-SSH target that might work is the active
                    # NCC's own per-node IP.
                    _active_ip_out = _dns_active_ip or None
                elif _dns_active_ip:
                    _active_ip_out = _dns_active_ip
                elif _vip_candidate and _vip_ssh_reachable:
                    _active_ip_out = _vip_candidate
                else:
                    _active_ip_out = _vip_candidate or None
                cluster_info = {
                    "is_cluster": True,
                    "ncc_type": "kvm",
                    "kvm_host": kvm_host,
                    "ncc_vms": ncc_vms,
                    "ncc_hosts": _ordered_ncc_hosts,
                    # `active_ncc_vm` is what the frontend badge, virsh row
                    # and terminal launcher use as the suggested NCC. Use the
                    # resolver result when present; `ops.active_ncc_vm` may be
                    # stale (classic PE-4: ops still said ncc0 while monitored
                    # active NCC was ncc1).
                    "active_ncc_vm": active_host or ops.get("active_ncc_vm", ""),
                    "active_ncc_host": active_host,
                    "active_ncc_ip": _active_ip_out,
                    "active_ncc_source": _ncc_resolve.get("source", ""),
                    "ncc_dns_map": _ncc_resolve.get("dns_map", {}),
                    "ncp_console": None,
                }
                try:
                    from scaler.connection_strategy import get_console_config_for_device as _gcc
                    mappings_path = Path(SCALER_ROOT) / "db" / "configs" / "console_mappings.json"
                    if mappings_path.exists():
                        cdata = json.loads(mappings_path.read_text())
                        d2c = cdata.get("device_to_console", {})
                        for dname, dmapping in d2c.items():
                            if dname.lower() == scaler_id.lower():
                                cluster_info["ncp_console"] = {
                                    "console_server": dmapping.get("console_server"),
                                    "port": dmapping.get("port"),
                                    "source": dmapping.get("source", "cached"),
                                }
                                break
                except Exception:
                    pass
    except Exception:
        pass
    if not cluster_info:
        try:
            cm_path = Path(SCALER_ROOT) / "db" / "console_mappings.json"
            if cm_path.exists():
                cm_data = json.loads(cm_path.read_text())
                ncc_entry = cm_data.get("cluster_ncc_access", {}).get(scaler_id)
                if ncc_entry and ncc_entry.get("ncc_type") == "kvm":
                    _cm_kvm = _derive_kvm_host(ncc_entry.get("kvm_host_ip") or ncc_entry.get("kvm_host") or "")
                    _cm_vms = ncc_entry.get("ncc_vms", [])
                    _cm_resolve = _resolve_active_ncc_host(
                        _cm_vms,
                        ncc_entry.get("ncc_mgmt_ip", "") or ncc_entry.get("active_ncc_ip", ""),
                        ncc_entry.get("active_ncc_vm", ""),
                    )
                    _cm_active = _cm_resolve.get("active_ncc_host", "")
                    _cm_ordered = list(_cm_vms or [])
                    if _cm_active and _cm_active in _cm_ordered and _cm_ordered[0] != _cm_active:
                        _cm_ordered = [_cm_active] + [h for h in _cm_ordered if h != _cm_active]
                    try:
                        for _m in results:
                            if _m.get("method") == "ssh_ncc" and _cm_active:
                                _m["host"] = _cm_active
                                _m["active_ncc_source"] = _cm_resolve.get("source", "")
                                break
                    except Exception:
                        pass
                    cluster_info = {
                        "is_cluster": True,
                        "ncc_type": "kvm",
                        "kvm_host": _cm_kvm,
                        "ncc_vms": _cm_vms,
                        "ncc_hosts": _cm_ordered,
                        "active_ncc_vm": _cm_active or ncc_entry.get("active_ncc_vm", ""),
                        "active_ncc_host": _cm_active,
                        "active_ncc_ip": _cm_resolve.get("active_ncc_ip"),
                        "active_ncc_source": _cm_resolve.get("source", ""),
                        "ncc_dns_map": _cm_resolve.get("dns_map", {}),
                        "ncp_console": None,
                    }
                    d2c = cm_data.get("device_to_console", {})
                    for dname, dmapping in d2c.items():
                        if dname.lower() == scaler_id.lower():
                            cluster_info["ncp_console"] = {
                                "console_server": dmapping.get("console_server"),
                                "port": dmapping.get("port"),
                                "source": dmapping.get("source", "cached"),
                            }
                            break
        except Exception:
            pass
    resp = {
        "methods": results,
        "recommended": recommended or (results[0]["method"] if results else None),
        "device_state": device_state,
    }
    if cluster_info:
        resp["cluster"] = cluster_info
    if ncc_mgmt_ip_out:
        resp["ncc_mgmt_ip"] = ncc_mgmt_ip_out
        resp["ncc_mgmt_verified_at"] = ncc_mgmt_verified_at_out
    if stale_note:
        resp["stale_note"] = stale_note

    # Auto-capture: persist the durable console-fallback record under
    # the caller's per-user devices.json so a later ghost-IP reap or
    # system delete can't take the backup paths down with it.
    try:
        app_user = _get_request_user(request) if request else ""
        if app_user and device_id:
            from routes import _console_fallback as _cf
            probe_payload = {
                "methods": results,
                "cluster": cluster_info or {},
                "serial": (cluster_info or {}).get("serial_number"),
                "ncc_type": (cluster_info or {}).get("ncc_type"),
            }
            _cf.capture_from_probe_result(
                app_user, device_id, probe_payload, reason="probe_success",
            )
            _cf.capture_from_ops(
                app_user, device_id, reason="probe_followup",
            )
    except Exception as _cap_err:
        logger.debug("[console_fallback] probe auto-capture skipped: %s", _cap_err)

    return resp


@router.get("/api/ssh/check-port")
def check_ssh_port(host: str = "", port: int = 22):
    """Single TCP connect for quick reachability (e.g. NCC mgmt before iTerm)."""
    import socket as _sock
    host = (host or "").strip()
    if not host:
        raise HTTPException(status_code=400, detail="host required")
    if port < 1 or port > 65535:
        raise HTTPException(status_code=400, detail="invalid port")
    s = _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM)
    s.settimeout(2.0)
    try:
        s.connect((host, port))
        return {"reachable": True, "host": host, "port": port}
    except Exception:
        return {"reachable": False, "host": host, "port": port}
    finally:
        try:
            s.close()
        except Exception:
            pass


@router.post("/api/ssh/discover-ncc-mgmt")
def discover_ncc_mgmt_ip_endpoint(body: dict = None):
    """Background: virsh console to NCC, show interfaces management, verify SSH dnroot; persist if ok."""
    body = body or {}
    device_id = (body.get("device_id") or "").strip()
    kvm_host = (body.get("kvm_host") or "").strip()
    kvm_user = (body.get("kvm_user") or "dn").strip()
    kvm_pass = body.get("kvm_pass") or ""
    ncc_vms = body.get("ncc_vms") or []
    if isinstance(ncc_vms, str):
        ncc_vms = [v.strip() for v in ncc_vms.split(",") if v.strip()]
    active_ncc = (body.get("active_ncc") or "").strip() or None
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    if not kvm_host:
        raise HTTPException(status_code=400, detail="kvm_host required")
    if not kvm_pass:
        raise HTTPException(status_code=400, detail="kvm_pass required")

    try:
        _, scaler_id, _ = _resolve_mgmt_ip(device_id, "")
    except HTTPException:
        scaler_id = device_id
    except Exception:
        scaler_id = device_id

    result = _discover_ncc_mgmt_ip_sync(kvm_host, kvm_user, kvm_pass, ncc_vms, active_ncc)
    result["device_id"] = device_id
    result["scaler_id"] = scaler_id

    ops_path = Path(SCALER_ROOT) / "db" / "configs" / scaler_id / "operational.json"
    if result.get("ncc_mgmt_ip") and result.get("ssh_auth_ok") and ops_path.exists():
        try:
            _nip = (result["ncc_mgmt_ip"] or "").strip().split("/")[0]
            _ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            def _mut_ncc(d, _ip=_nip, _ts=_ts, _full=result["ncc_mgmt_ip"]):
                d["ncc_mgmt_ip"] = _full
                d["ncc_mgmt_verified_at"] = _ts
                if _ip:
                    d["mgmt_ip"] = _ip
                    d["ssh_host"] = _ip

            _update_ops(ops_path, _mut_ncc, create_if_missing=False)
        except Exception as e:
            logging.warning(f"[discover_ncc_mgmt] could not save operational.json: {e}")

    return result

@router.post("/api/ssh/discover-console")
def discover_console_path(body: dict = None):
    """Discover console path via Zohar's CSV DB (primary) or Device42 (fallback).
    Auto-saves to console_mappings.json. Returns console_server, port, pdu_entries, source."""
    body = body or {}
    device_id = (body.get("device_id") or "").strip()
    serial_number = (body.get("serial_number") or "").strip()
    ssh_host = (body.get("ssh_host") or "").strip()
    if not device_id and not serial_number:
        raise HTTPException(status_code=400, detail="device_id or serial_number required")
    try:
        result = _discover_console(device_id or "unknown", serial_number, ssh_host)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

    try:
        mappings_path = Path(SCALER_ROOT) / "db" / "console_mappings.json"
        mappings_path.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if mappings_path.exists():
            data = json.loads(mappings_path.read_text())
        key = device_id or result.get("serial_no", "unknown")
        if "device_to_console" not in data:
            data["device_to_console"] = {}
        entry = {
            "console_server": result.get("console_server"),
            "port": str(result["port"]) if result.get("port") is not None else None,
            "source": result.get("source", "unknown"),
            "discovered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        if result.get("serial_no"):
            entry["serial_number"] = result["serial_no"]
        if result.get("pdu_entries"):
            entry["pdu_entries"] = result["pdu_entries"]
        data["device_to_console"][key] = entry

        if result.get("serial_no"):
            data.setdefault("serial_to_console", {})[result["serial_no"]] = {
                "console_server": result.get("console_server"),
                "port": str(result["port"]) if result.get("port") is not None else None,
                "hostname": key,
            }
        mappings_path.write_text(json.dumps(data, indent=2))
    except Exception:
        pass
    return result


@router.post("/api/ssh/console-scan")
def console_port_scan(body: dict = None):
    """Scan console server ports to find a device by hostname.
    Tries all known console servers unless a specific one is given.
    Excludes KVM cluster devices (those use virsh console, not serial).
    Body: { device_id, serial_number?, console_server? (optional hint) }
    Returns: { found, console_server, port, scanned, all_results }"""
    body = body or {}
    device_id = (body.get("device_id") or "").strip()
    serial_number = (body.get("serial_number") or "").strip()
    hint = (body.get("console_server") or "").strip().lower()
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")

    is_cluster = False
    try:
        ops_path = Path(SCALER_ROOT) / "db" / "configs" / device_id / "operational.json"
        if ops_path.exists():
            ops = _read_ops_safe(ops_path)
            if ops.get("ncc_type") == "kvm":
                is_cluster = True
            if not serial_number:
                serial_number = (ops.get("serial_number") or ops.get("serial") or "").strip()
    except Exception:
        pass
    if is_cluster:
        return {"found": False, "error": "KVM cluster device -- use virsh console instead of serial console",
                "console_server": None, "port": None, "scanned": 0, "all_results": []}

    servers = _get_known_console_servers()
    if hint:
        servers = sorted(servers, key=lambda s: (0 if hint in s["name"] else 1))

    mp = Path(SCALER_ROOT) / "db" / "console_mappings.json"
    known_ports = {}
    if mp.exists():
        try:
            data = json.loads(mp.read_text())
            for sname, sinfo in data.get("console_servers", {}).items():
                known_ports[sname] = [int(p) for p in sinfo.get("ports", {}).keys()]
        except Exception:
            pass

    total_scanned = 0
    all_results = []
    for srv in servers:
        skip = known_ports.get(srv["name"], [])
        results = _probe_console_server(srv, look_for=device_id, skip_ports=skip)
        for r in results:
            r["console_server"] = srv["name"]
            r["console_host"] = srv["host"]
            total_scanned += 1
        all_results.extend(results)
        match = next((r for r in results if r["matched"]), None)
        if match:
            _save_discovered_console(device_id, serial_number, srv["name"],
                                      srv["host"], match["port"])
            return {
                "found": True,
                "console_server": srv["name"],
                "console_host": srv["host"],
                "port": match["port"],
                "scanned": total_scanned,
                "all_results": all_results,
            }

    return {"found": False, "console_server": None, "port": None,
            "scanned": total_scanned, "all_results": all_results}


@router.post("/api/ssh/pdu-power")
def pdu_power_action_endpoint(body: dict = None):
    """Power cycle / power off / power on a device via its PDU.
    Body: { serial_number?, device_id?, action: reboot|off|on|status, pdu_host?, outlet? }
    If pdu_host+outlet not given, looks up from Zohar's PDU mapping by serial."""
    body = body or {}
    action = (body.get("action") or "status").strip().lower()
    if action not in ("reboot", "off", "on", "status"):
        raise HTTPException(status_code=400, detail="action must be reboot, off, on, or status")

    pdu_host = (body.get("pdu_host") or "").strip()
    outlet = body.get("outlet")
    serial = (body.get("serial_number") or "").strip().upper()
    device_id = (body.get("device_id") or "").strip()

    if not pdu_host or outlet is None:
        if not serial and device_id:
            try:
                ops_path = Path(SCALER_ROOT) / "db" / "configs" / device_id / "operational.json"
                if ops_path.exists():
                    ops = _read_ops_safe(ops_path)
                    serial = (ops.get("serial_number") or ops.get("serial") or "").strip().upper()
            except Exception:
                pass
        if serial:
            try:
                _fetch_zohar_db()
            except Exception:
                pass
            entries = _lookup_zohar_pdu(serial)
            if entries:
                pdu_host = entries[0].get("pdu", "")
                outlet = entries[0].get("outlet")
    if not pdu_host or outlet is None:
        raise HTTPException(status_code=404, detail=f"No PDU mapping for serial={serial or 'unknown'}, device={device_id or 'unknown'}")
    try:
        outlet = int(outlet)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid outlet: {outlet}")

    result = _pdu_power_action(pdu_host, outlet, action)
    if not result["success"]:
        raise HTTPException(status_code=503, detail=result.get("error", "PDU action failed"))
    return result
@router.websocket("/api/terminal/ws")
async def terminal_websocket(
    websocket: WebSocket,
    device_id: str = "",
    ssh_host: str = "",
    method: str = "ssh_mgmt",
    kvm_host: str = "",
    kvm_user: str = "",
    ncc_vms: str = "",
    token: str = "",
):
    """Interactive terminal via WebSocket. Streams stdin/stdout between browser and device.
    Query params: device_id, ssh_host, method (ssh_mgmt|virsh_console|...)
    For virsh_console: kvm_host, kvm_user, ncc_vms (comma-separated). kvm_pass sent in first message.
    Auth: pass JWT via ?token= query param (WebSocket can't set headers).
    """
    app_user = "default"
    try:
        from api.auth.service import decode_token
        if not token:
            await websocket.close(code=4001, reason="Authentication required")
            return
        payload = decode_token(token)
        if not payload:
            await websocket.close(code=4001, reason="Invalid or expired token")
            return
        app_user = (payload.get("sub") or "default").strip() or "default"
    except ImportError:
        pass
    await websocket.accept()
    channel = None
    ssh_client = None
    import asyncio

    try:
        logging.info(f"[terminal_ws] New connection: device={device_id} host={ssh_host} method={method}")
        if method == "virsh_console":
            # Backfill any missing KVM parameters from the durable
            # console-fallback store. If the frontend has been
            # reloaded in a fresh browser session and devices.json
            # cache is gone, the user can still open a virsh console
            # just by picking the device -- we rediscover the KVM
            # host, user and VM list from either operational.json or
            # the per-user devices.json console_fallback block.
            ncc_list = [v.strip() for v in ncc_vms.split(",") if v.strip()]
            fallback_notice_sent = False
            if device_id and (not kvm_host or not kvm_user or not ncc_list):
                try:
                    from routes import _console_fallback as _cf
                    fb = _cf.read_fallback(app_user, device_id)
                    if not kvm_host and fb.kvm_host_ip:
                        kvm_host = fb.kvm_host_ip
                    if not kvm_user and fb.kvm_user:
                        kvm_user = fb.kvm_user
                    if not ncc_list and fb.ncc_vms:
                        ncc_list = list(fb.ncc_vms)
                    if fb.kvm_host_ip or fb.ncc_vms:
                        await websocket.send_json({
                            "type": "data",
                            "text": "[INFO] Reusing durable console-fallback "
                                    f"(KVM {fb.kvm_host_ip or '?'}, {len(fb.ncc_vms)} NCCs) from {fb.source}\r\n",
                        })
                        fallback_notice_sent = True
                except Exception as fb_err:
                    logging.warning(f"[terminal_ws] console-fallback read failed: {fb_err}")

            if not kvm_host or not kvm_user:
                await websocket.send_json({
                    "type": "error",
                    "message": (
                        "virsh_console requires kvm_host and kvm_user. "
                        "No fallback config found for this device either -- "
                        "run a probe first (SSH dialog -> Probe) so the "
                        "KVM info auto-captures to your user store."
                    ),
                })
                return
            kvm_pass = None
            active_ncc_hint = None
            first_msg = await websocket.receive_json()
            if first_msg.get("type") == "virsh_auth":
                kvm_pass = first_msg.get("kvm_pass") or first_msg.get("password") or ""
                active_ncc_hint = first_msg.get("active_ncc") or None
            elif first_msg.get("type") == "auth":
                kvm_pass = first_msg.get("password") or ""

            # Try persisted password as a last resort before giving up.
            # This lets an operator reconnect right after a reboot without
            # having to paste drive1234! every single time.
            if not kvm_pass and device_id:
                try:
                    from routes import _console_fallback as _cf
                    fb = _cf.read_fallback(app_user, device_id)
                    if fb.kvm_pass:
                        kvm_pass = fb.kvm_pass
                        if not fallback_notice_sent:
                            await websocket.send_json({
                                "type": "data",
                                "text": f"[INFO] Using stored KVM password from {fb.source}\r\n",
                            })
                        if not active_ncc_hint and fb.active_ncc_vm_hint:
                            active_ncc_hint = fb.active_ncc_vm_hint
                except Exception:
                    pass

            if not kvm_pass:
                await websocket.send_json({"type": "error", "message": "KVM password required"})
                return
            await websocket.send_json({"type": "data", "text": "[INFO] Connecting via KVM virsh console...\r\n"})
            loop = asyncio.get_event_loop()
            ssh_client, channel, virsh_initial = await loop.run_in_executor(
                None,
                lambda: _connect_virsh_console_sync(kvm_host, kvm_user, kvm_pass, ncc_list, active_ncc_hint),
            )
            if virsh_initial:
                await websocket.send_json({"type": "data", "text": virsh_initial.decode("utf-8", errors="replace")})
            # After a successful virsh connect, refresh the
            # fallback record so the most recent active NCC hint and
            # any updated password stay fresh for next time.
            try:
                if device_id:
                    from routes import _console_fallback as _cf
                    existing = _cf.read_fallback(app_user, device_id)
                    updated = _cf.ConsoleFallback(
                        device_id=device_id,
                        kvm_host_ip=kvm_host,
                        kvm_user=kvm_user,
                        kvm_pass=kvm_pass,
                        ncc_vms=ncc_list,
                        active_ncc_vm_hint=active_ncc_hint or existing.active_ncc_vm_hint,
                        ncc_console_user=existing.ncc_console_user,
                        ncc_console_pass=existing.ncc_console_pass,
                        ncc_type="kvm",
                        last_working_method="virsh->NCC",
                        validated_method="virsh_console",
                        notes="ws_terminal_success",
                    )
                    _cf.write_fallback(app_user, device_id, updated, merge_with_existing=True)
            except Exception as cap_err:
                logging.debug(f"[console_fallback] ws capture skipped: {cap_err}")
        else:
            host = ssh_host
            if not host and device_id:
                try:
                    mgmt_ip, _, _ = _resolve_mgmt_ip(device_id, ssh_host)
                    host = mgmt_ip
                except Exception:
                    pass
            if not host:
                await websocket.send_json({"type": "error", "message": "Could not resolve device IP"})
                return
            user, password = _get_credentials(
                app_user=app_user,
                device_id=device_id,
                hostname=device_id,
            )
            try:
                first_msg = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
                if first_msg.get("type") == "auth":
                    if first_msg.get("user"):
                        user = first_msg["user"]
                    if first_msg.get("password"):
                        password = first_msg["password"]
            except asyncio.TimeoutError:
                logging.warning("[terminal_ws] Auth message timeout -- using default credentials")
            except Exception as auth_err:
                logging.warning(f"[terminal_ws] Auth message error: {auth_err} -- using default credentials")
            import paramiko
            pw = password

            def _ssh_connect_sync(h, u, p):
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(h, username=u, password=p, timeout=15, banner_timeout=15,
                            allow_agent=False, look_for_keys=False)
                chan = ssh.invoke_shell(width=120, height=40)
                chan.settimeout(0)
                return ssh, chan

            await websocket.send_json({"type": "data", "text": f"[INFO] Connecting to {host}...\r\n"})
            loop = asyncio.get_event_loop()
            ssh_client, channel = await loop.run_in_executor(
                None, lambda: _ssh_connect_sync(host, user, pw)
            )

            def _auto_login_if_needed(chan, u, p):
                import time as _t
                buf = b""
                for _ in range(30):
                    _t.sleep(0.2)
                    if chan.recv_ready():
                        buf += chan.recv(4096)
                    text = buf.decode("utf-8", errors="replace")
                    stripped = text.rstrip()
                    last_line = stripped.split("\n")[-1].strip().lower() if stripped else ""
                    if "#" in last_line or ">" in last_line or "dncli" in text.lower():
                        return buf
                    is_login_prompt = last_line.endswith("login:") and "last login" not in last_line
                    if is_login_prompt:
                        chan.send(u.encode() + b"\n")
                        buf = b""
                        for __ in range(20):
                            _t.sleep(0.2)
                            if chan.recv_ready():
                                buf += chan.recv(4096)
                            lo2 = buf.decode("utf-8", errors="replace").lower()
                            ll2 = lo2.rstrip().split("\n")[-1].strip() if lo2.rstrip() else ""
                            if ll2.endswith("password:") or ll2.endswith("password :"):
                                chan.send(p.encode() + b"\n")
                                return buf
                            if "#" in ll2 or ">" in ll2:
                                return buf
                        return buf
                    if last_line.endswith("password:") or last_line.endswith("password :"):
                        chan.send(p.encode() + b"\n")
                        return buf
                return buf

            initial_buf = await loop.run_in_executor(None, lambda: _auto_login_if_needed(channel, user, pw))
            if initial_buf:
                await websocket.send_json({"type": "data", "text": initial_buf.decode("utf-8", errors="replace")})

            # ---- Ghost-IP identity guard ------------------------------------
            # Only run for direct SSH methods where the prompt reflects the
            # DUT. Console/virsh first land on a console server or KVM host,
            # which would produce false positives.
            if device_id and method in {"ssh_mgmt", "ssh_sn", "ssh_ncc", "ssh_loopback"}:
                banner_text = initial_buf.decode("utf-8", errors="replace") if initial_buf else ""
                actual_hostname = _extract_remote_hostname(banner_text)
                expected_hostname = _expected_hostname_for_device(device_id)
                if actual_hostname and not _identity_matches(device_id, expected_hostname, actual_hostname):
                    logging.warning(
                        "[terminal_ws] GHOST-IP detected: device=%s ip=%s expected_host=%s actual_host=%s",
                        device_id, host, expected_hostname or device_id, actual_hostname,
                    )
                    try:
                        summary = _mark_device_ip_stale(
                            scaler_id=device_id,
                            stale_ip=host,
                            reason="identity_mismatch_on_connect",
                            actual_hostname=actual_hostname,
                            acting_user=app_user,
                        )
                    except Exception as reap_err:
                        logging.error("[terminal_ws] ghost-ip reaper failed: %s", reap_err)
                        summary = {"scaler_id": device_id, "cleared_ip": host,
                                   "actual_hostname": actual_hostname,
                                   "reason": "identity_mismatch_on_connect",
                                   "acting_user": app_user}
                    await websocket.send_json({
                        "type": "data",
                        "text": (
                            "\r\n[WARN] Ghost IP detected: this address answers to "
                            f"'{actual_hostname}', not '{expected_hostname or device_id}'.\r\n"
                            "[INFO] Stale record cleared. Closing session -- click SSH again to re-discover.\r\n"
                        ),
                    })
                    await websocket.send_json({
                        "type": "ghost_ip_detected",
                        "device_id": device_id,
                        "expected": expected_hostname or device_id,
                        "actual": actual_hostname,
                        "ip": host,
                        "summary": summary,
                    })
                    try:
                        channel.close()
                    except Exception:
                        pass
                    try:
                        ssh_client.close()
                    except Exception:
                        pass
                    try:
                        await websocket.close(code=4002, reason="ghost_ip_detected")
                    except Exception:
                        pass
                    return
            # -----------------------------------------------------------------

        logging.info(f"[terminal_ws] Connected: device={device_id} host={ssh_host or host} method={method}")

        # Wave 3.1: event-driven reader. Replaces a 30ms poll loop that
        # burned ~33 wakes/sec per open terminal (1000/sec for 30 users).
        # A dedicated thread blocks in select() until data arrives (or
        # 1s elapses so we can honor shutdown). Data is pushed to a
        # bounded asyncio.Queue; on backpressure we drop the oldest
        # chunks so a slow WebSocket client cannot exhaust memory.
        import select as _select
        import threading as _threading

        WS_READ_QUEUE_SIZE = 256  # ~1 MB of 4K chunks, plenty of headroom
        out_queue: "asyncio.Queue[bytes | None]" = asyncio.Queue(maxsize=WS_READ_QUEUE_SIZE)
        stop_event = _threading.Event()
        loop = asyncio.get_event_loop()

        def _put_with_drop(q, item):
            """Runs on the event loop. Drops oldest on backpressure."""
            if q.full():
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                q.put_nowait(item)
            except asyncio.QueueFull:
                pass

        def _reader_thread():
            try:
                while not stop_event.is_set():
                    try:
                        ready, _, _ = _select.select([channel], [], [], 1.0)
                    except (ValueError, OSError):
                        break
                    if not ready:
                        if channel.closed or channel.exit_status_ready():
                            break
                        continue
                    try:
                        data = channel.recv(4096)
                    except Exception:
                        break
                    if not data:
                        break  # EOF
                    try:
                        loop.call_soon_threadsafe(_put_with_drop, out_queue, data)
                    except RuntimeError:
                        break  # loop closed
            finally:
                try:
                    loop.call_soon_threadsafe(_put_with_drop, out_queue, None)
                except Exception:
                    pass

        reader_thread = _threading.Thread(
            target=_reader_thread,
            name=f"ws-reader:{device_id or host}",
            daemon=True,
        )
        reader_thread.start()

        async def send_output():
            try:
                while True:
                    data = await out_queue.get()
                    if data is None:
                        try:
                            await websocket.send_json({
                                "type": "closed",
                                "message": "Remote session ended",
                            })
                        except Exception:
                            pass
                        break
                    try:
                        await websocket.send_text(json.dumps({
                            "type": "data",
                            "text": data.decode("utf-8", errors="replace"),
                        }))
                    except Exception:
                        break
            finally:
                stop_event.set()

        recv_task = asyncio.create_task(send_output())

        # Wave 3.3: server-side keepalive for the terminal WS. A broken
        # TCP connection (laptop lid closed mid-session, flaky Wi-Fi,
        # proxy idle-timeout) looks exactly like an idle user on the
        # server side. By sending a __ping__ every 20s and closing
        # after two consecutive silent intervals, we reclaim channels
        # + SSH transports within ~40s of a peer going dark, instead
        # of keeping them open until the next inbound frame (which may
        # never come).
        TERM_PING_INTERVAL = 20.0
        TERM_MAX_MISSED = 2
        term_missed = 0

        while True:
            try:
                msg = await asyncio.wait_for(
                    websocket.receive_json(), timeout=TERM_PING_INTERVAL
                )
                term_missed = 0
            except asyncio.TimeoutError:
                term_missed += 1
                if term_missed >= TERM_MAX_MISSED:
                    logging.info(
                        "[terminal_ws] closing idle device=%s after %d missed pings",
                        device_id, term_missed,
                    )
                    break
                try:
                    await websocket.send_json({"type": "__ping__"})
                except Exception:
                    break
                continue
            except WebSocketDisconnect:
                break
            except Exception as e:
                if "disconnect" not in str(e).lower():
                    try:
                        await websocket.send_json({"type": "error", "message": str(e)})
                    except Exception:
                        pass
                break

            msg_type = msg.get("type")
            if msg_type == "input" and msg.get("data"):
                if channel and not channel.closed:
                    channel.send(msg["data"])
            elif msg_type == "ping":
                try:
                    await websocket.send_json({"type": "pong"})
                except Exception:
                    break
            elif msg_type == "pong":
                # Client replied to our __ping__ probe; nothing to do.
                pass
            elif msg_type == "resize":
                cols = msg.get("cols", 120)
                rows = msg.get("rows", 40)
                if channel and not channel.closed:
                    try:
                        channel.resize_pty(width=cols, height=rows)
                    except Exception:
                        pass
            elif msg_type == "disconnect":
                break

        # Signal the reader thread to exit (Wave 3.1).
        stop_event.set()
        recv_task.cancel()
        try:
            await recv_task
        except (asyncio.CancelledError, Exception):
            pass

        logging.info(f"[terminal_ws] Disconnected: device={device_id}")
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        if channel:
            try:
                channel.close()
            except Exception:
                pass
        if ssh_client:
            try:
                ssh_client.close()
            except Exception:
                pass
        try:
            await websocket.close()
        except Exception:
            pass

