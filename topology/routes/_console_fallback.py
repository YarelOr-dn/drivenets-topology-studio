"""Console / KVM Fallback Store.

Every DNOS device has at least one connection path that works when the
primary management SSH is down:

  * KVM cluster devices (``ncc_type == "kvm"``): virsh console on the
    hypervisor, then either direct SSH to the NCC VM or a bash shell
    inside the NCC to issue ``dncli`` commands.
  * Physical devices: a serial console server (ACS, Digi, Opengear)
    with a dedicated port per router.
  * Any device: the serial-number hostname resolved via lab DNS
    (``WDY1A17E00011-P3`` -> NCC IP); this is stable across upgrades,
    reinstalls and ghost-IP reaps because the SN never changes.
  * Cluster devices: per-NCC management IPs when the cluster VIP is
    down but an individual NCC can still be reached.

Historically these details lived ONLY in
``<SCALER>/db/configs/<device>/operational.json``. That file is
wiped by the ``request system delete`` flow, truncated by ghost-IP
reaps, and rebuilt from scratch by every Phase 2 live probe. When it
disappeared we lost every backup path along with the primary -- the
operator had to rediscover the hypervisor IP and KVM credentials by
hand, while a production upgrade sat broken.

This module is the durable, user-owned fallback store. A single dict
per (user, device_id) holds everything needed to reach the device when
the primary SSH path is down. It lives under
``~/.topology_users/<user>/devices.json`` (same file as SSH creds,
0600, atomic rename, already read by ``_get_credentials``) and is
auto-captured on every successful probe/connect so the user never
has to enter it manually. A shared global default can also be
stamped into ``<SCALER>/db/devices.json`` for lab-wide devices.

Design rules:

  * **Per-user primary, global fallback.** Read order is user ->
    global -> operational.json. Write only ever touches per-user.
  * **Never loses information.** A partial fallback (e.g. just a
    KVM host without an active-NCC hint) is kept as-is; the caller
    decides what to do with the missing fields.
  * **Redacted outputs.** ``sanitize`` blanks every password and
    replaces it with ``"***"`` so this module is safe to return
    through the public API without leaking credentials.
  * **Atomic writes.** Same rename-in-place pattern already used by
    ``routes.api.auth.router`` for per-user SSH creds.
  * **No direct import cycles.** This module imports from the stdlib
    only, plus a lazy import of ``routes.bridge_helpers.SCALER_ROOT``
    inside ``read_fallback`` -- callers can live inside bridge_helpers,
    upgrade.py, ssh.py, or anywhere else without circularity.
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_LOG = logging.getLogger(__name__)

PASSWORD_FIELDS = (
    "kvm_pass",
    "ncc_console_pass",
    "console_server_pass",
    "dncli_pass",
)

_write_lock = threading.Lock()


@dataclass
class ConsoleFallback:
    """Durable per-device backup-connection config.

    Every field is optional. An entirely empty instance (all fields
    ``None`` / ``[]``) means "no fallback information known"; callers
    should still attempt a fresh probe before giving up.
    """
    device_id: str = ""
    hostname: str = ""
    serial_number: str = ""

    ncc_type: Optional[str] = None

    kvm_host_ip: str = ""
    kvm_host_name: str = ""
    kvm_user: str = ""
    kvm_pass: str = ""
    ncc_vms: List[str] = field(default_factory=list)
    active_ncc_vm_hint: str = ""
    ncc_console_user: str = ""
    ncc_console_pass: str = ""
    ncc_mgmt_ip: str = ""

    console_server_host: str = ""
    console_server_port: Optional[int] = None
    console_server_user: str = ""
    console_server_pass: str = ""

    serial_hostname: str = ""

    dncli_user: str = ""
    dncli_pass: str = ""

    last_working_method: str = ""
    auto_captured_at: str = ""
    validated_at: str = ""
    validated_method: str = ""
    notes: str = ""
    source: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict (passwords included) suitable for persistence."""
        data = asdict(self)
        data["ncc_vms"] = list(data.get("ncc_vms") or [])
        return data

    def is_empty(self) -> bool:
        """True when no meaningful fallback info is stored."""
        populated = any((
            self.kvm_host_ip,
            self.ncc_mgmt_ip,
            self.console_server_host,
            self.serial_hostname,
            self.ncc_vms,
        ))
        return not populated

    def best_method(self) -> str:
        """Heuristic ranking of which backup path is most likely to work.

        Mirrors the priority list in
        ``scaler.connection_strategy.DeviceConnector``. Returns one of
        ``"virsh_console"``, ``"ssh_ncc"``, ``"console_server"``,
        ``"ssh_sn"`` or ``""``.
        """
        if self.ncc_type == "kvm" and self.kvm_host_ip and self.ncc_vms:
            return "virsh_console"
        if self.ncc_mgmt_ip:
            return "ssh_ncc"
        if self.console_server_host and self.console_server_port:
            return "console_server"
        if self.serial_hostname:
            return "ssh_sn"
        return ""


def _user_base_dir() -> Path:
    """Same resolution as ``api.auth.router._user_dir``."""
    return Path(os.environ.get(
        "TOPOLOGY_USERS_BASE",
        str(Path.home() / ".topology_users"),
    ))


def _user_devices_file(username: str) -> Path:
    return _user_base_dir() / username / "devices.json"


def _scaler_root() -> Path:
    try:
        from routes.bridge_helpers import SCALER_ROOT
        return Path(SCALER_ROOT)
    except Exception:
        return Path(os.environ.get("SCALER_ROOT", "/home/dn/SCALER"))


def _read_user_devices(username: str) -> Dict[str, Any]:
    """Load ``~/.topology_users/<user>/devices.json`` as a dict.

    Returns an empty dict on any error so callers can treat "no user
    overrides" identically to "file missing".
    """
    if not username:
        return {}
    path = _user_devices_file(username)
    if not path.exists():
        return {}
    try:
        with open(path) as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        _LOG.warning("[console_fallback] read %s failed: %s", path, exc)
        return {}


def _write_user_devices(username: str, data: Dict[str, Any]) -> None:
    """Atomic write to ``~/.topology_users/<user>/devices.json`` (0600)."""
    udir = _user_base_dir() / username
    udir.mkdir(parents=True, exist_ok=True)
    path = udir / "devices.json"
    tmp = path.with_suffix(".tmp")
    payload = json.dumps(data, indent=2, sort_keys=True)
    with _write_lock:
        tmp.write_text(payload)
        try:
            os.chmod(tmp, 0o600)
        except Exception:
            pass
        os.replace(tmp, path)
        try:
            os.chmod(path, 0o600)
        except Exception:
            pass


def _read_ops_for_device(device_id: str) -> Dict[str, Any]:
    """Pull ``operational.json`` for a device if we can find it.

    Uses the bridge's canonical ``_resolve_config_dir`` when available
    so we honour ``scaler_id`` redirects and inventory aliases.
    """
    if not device_id:
        return {}
    try:
        from routes.bridge_helpers import _resolve_config_dir
        canon = _resolve_config_dir(device_id) or device_id
    except Exception:
        canon = device_id
    path = _scaler_root() / "db" / "configs" / canon / "operational.json"
    if not path.exists():
        return {}
    try:
        from routes._ops_writer import read_ops as _r
        return _r(path) or {}
    except Exception:
        return {}


def _read_global_devices() -> Dict[str, Any]:
    """Load ``<SCALER>/db/devices.json`` and index it by id, hostname, alias."""
    path = _scaler_root() / "db" / "devices.json"
    if not path.exists():
        return {}
    try:
        with open(path) as fh:
            raw = json.load(fh) or {}
    except Exception:
        return {}
    out: Dict[str, Any] = {}
    for dev in raw.get("devices", []) or []:
        if not isinstance(dev, dict):
            continue
        for key in (
            dev.get("id"), dev.get("hostname"), *dev.get("aliases", []),
        ):
            if key:
                out[str(key).lower()] = dev
    return out


_PLACEHOLDER_VALUES = {"", "n/a", "null", "none", "-", "undefined", "unknown"}


def _real(value: Optional[str]) -> str:
    """Return a cleaned string, or ``""`` if the value is a known placeholder.

    Several fields in ``operational.json`` are populated with literal
    placeholder tokens (``"N/A"``, ``"null"``, ``"-"``) when the probe
    could not resolve the real value. Treating those as real data
    causes false-positive availability flags (``best_method='ssh_sn'``
    even though the serial is literally ``"N/A"``) and misleads the UI.
    Normalize them to the empty string so downstream logic (is_empty,
    best_method, describe_availability) stays honest.
    """
    if value is None:
        return ""
    s = str(value).strip()
    if s.lower() in _PLACEHOLDER_VALUES:
        return ""
    return s


def _from_ops(ops: Dict[str, Any], device_id: str) -> ConsoleFallback:
    """Project ``operational.json`` into a ``ConsoleFallback``.

    Returns an empty instance when there's nothing usable (so callers
    can use ``is_empty()`` to decide whether to persist).
    """
    if not isinstance(ops, dict):
        return ConsoleFallback(device_id=device_id)

    kvm_creds = ops.get("kvm_host_credentials") or {}
    ncc_creds = ops.get("ncc_console_credentials") or {}
    dnc_creds = ops.get("dncli_credentials") or {}

    raw_ncc_mgmt = _real(ops.get("ncc_mgmt_ip")).split("/")[0]
    if not re.match(r"^\d+\.\d+\.\d+\.\d+$", raw_ncc_mgmt or ""):
        raw_ncc_mgmt = ""

    raw_kvm = _real(ops.get("kvm_host_ip")).split("/")[0]
    if not re.match(r"^\d+\.\d+\.\d+\.\d+$", raw_kvm or ""):
        raw_kvm = ""

    cs_port_raw = ops.get("console_server_port")
    try:
        cs_port = int(cs_port_raw) if cs_port_raw else None
    except Exception:
        cs_port = None

    serial = _real(ops.get("serial_number"))

    return ConsoleFallback(
        device_id=device_id or _real(ops.get("hostname")),
        hostname=_real(ops.get("hostname")),
        serial_number=serial,
        ncc_type=_real(ops.get("ncc_type")) or None,
        kvm_host_ip=raw_kvm,
        kvm_host_name=_real(ops.get("kvm_host")),
        kvm_user=kvm_creds.get("username", ""),
        kvm_pass=kvm_creds.get("password", ""),
        ncc_vms=list(ops.get("ncc_vms") or []),
        active_ncc_vm_hint=_real(ops.get("active_ncc_vm")),
        ncc_console_user=ncc_creds.get("username", ""),
        ncc_console_pass=ncc_creds.get("password", ""),
        ncc_mgmt_ip=raw_ncc_mgmt,
        console_server_host=_real(ops.get("console_server_host")),
        console_server_port=cs_port,
        console_server_user=_real(ops.get("console_server_user")),
        console_server_pass=(ops.get("console_server_pass") or "").strip(),
        serial_hostname=serial,
        dncli_user=dnc_creds.get("username", ""),
        dncli_pass=dnc_creds.get("password", ""),
        last_working_method=_real(ops.get("last_working_method")),
        source="operational.json",
    )


def _from_user_entry(entry: Dict[str, Any], device_id: str) -> ConsoleFallback:
    """Project a per-user ``devices.json[device_id]["console_fallback"]``
    block into a ``ConsoleFallback``. Missing fields stay empty."""
    if not isinstance(entry, dict):
        return ConsoleFallback(device_id=device_id, source="user")
    cf = entry.get("console_fallback")
    if not isinstance(cf, dict):
        return ConsoleFallback(device_id=device_id, source="user")
    cs_port_raw = cf.get("console_server_port")
    try:
        cs_port = int(cs_port_raw) if cs_port_raw else None
    except Exception:
        cs_port = None
    return ConsoleFallback(
        device_id=device_id,
        hostname=cf.get("hostname", ""),
        serial_number=cf.get("serial_number", ""),
        ncc_type=cf.get("ncc_type"),
        kvm_host_ip=cf.get("kvm_host_ip", ""),
        kvm_host_name=cf.get("kvm_host_name", ""),
        kvm_user=cf.get("kvm_user", ""),
        kvm_pass=cf.get("kvm_pass", ""),
        ncc_vms=list(cf.get("ncc_vms") or []),
        active_ncc_vm_hint=cf.get("active_ncc_vm_hint", ""),
        ncc_console_user=cf.get("ncc_console_user", ""),
        ncc_console_pass=cf.get("ncc_console_pass", ""),
        ncc_mgmt_ip=cf.get("ncc_mgmt_ip", ""),
        console_server_host=cf.get("console_server_host", ""),
        console_server_port=cs_port,
        console_server_user=cf.get("console_server_user", ""),
        console_server_pass=cf.get("console_server_pass", ""),
        serial_hostname=cf.get("serial_hostname", ""),
        dncli_user=cf.get("dncli_user", ""),
        dncli_pass=cf.get("dncli_pass", ""),
        last_working_method=cf.get("last_working_method", ""),
        auto_captured_at=cf.get("auto_captured_at", ""),
        validated_at=cf.get("validated_at", ""),
        validated_method=cf.get("validated_method", ""),
        notes=cf.get("notes", ""),
        source="user",
    )


def _from_global_entry(entry: Dict[str, Any], device_id: str) -> ConsoleFallback:
    """Project the shared global devices.json entry into a ConsoleFallback.

    The global file is a simple dev-entry list. Only a few console
    fields are ever going to live there (by convention, only lab-wide
    constants like a console-server IP that every device behind that
    server shares). Missing fields stay empty so the caller can merge
    with a richer per-user record.
    """
    if not isinstance(entry, dict):
        return ConsoleFallback(device_id=device_id, source="global")
    cf = entry.get("console_fallback")
    if isinstance(cf, dict):
        projected = _from_user_entry({"console_fallback": cf}, device_id)
        projected.source = "global"
        return projected
    return ConsoleFallback(
        device_id=device_id,
        hostname=entry.get("hostname", ""),
        source="global",
    )


def _merge(primary: ConsoleFallback, fallback: ConsoleFallback) -> ConsoleFallback:
    """Field-by-field merge, preferring non-empty values from primary.

    Used to overlay per-user > global > operational.json. Lists are
    unioned (keeps any NCC VM we already knew about, even if the newer
    source has a shorter list).

    Implementation note: the union step tracks seen items via a running
    set initialized from ``merged["ncc_vms"]`` AFTER the main field-by-
    field pass, not from ``primary.ncc_vms``. If primary has an empty
    ``ncc_vms`` and fallback has a non-empty one, the main loop already
    overwrote ``merged["ncc_vms"]`` with fallback's list (because empty
    lists are falsy under ``if merged.get(key): continue``); seeding
    ``seen`` from the post-pass list prevents the union loop from
    re-appending those same items and producing duplicates.
    """
    if primary.is_empty() and not fallback.is_empty():
        out = ConsoleFallback(**asdict(fallback))
        out.source = fallback.source
        return out
    if fallback.is_empty():
        return primary
    merged = asdict(primary)
    for key, value in asdict(fallback).items():
        if key == "source":
            continue
        if merged.get(key):
            continue
        merged[key] = value
    seen_vms = set(merged.get("ncc_vms") or [])
    for vm in fallback.ncc_vms or []:
        if vm and vm not in seen_vms:
            merged["ncc_vms"].append(vm)
            seen_vms.add(vm)
    return ConsoleFallback(**merged)


def read_fallback(username: str, device_id: str) -> ConsoleFallback:
    """Resolve the best-known fallback config for (user, device).

    Read order: per-user devices.json -> global devices.json ->
    operational.json. Non-empty fields from earlier sources win.
    Always returns a ConsoleFallback (possibly empty); callers use
    ``.is_empty()`` to decide whether to surface it to the user.
    """
    if not device_id:
        return ConsoleFallback()

    user_data = _read_user_devices(username) if username else {}
    user_entry = user_data.get(device_id) if isinstance(user_data, dict) else None
    user_cf = _from_user_entry(user_entry or {}, device_id)

    global_idx = _read_global_devices()
    gkey = device_id.lower()
    global_entry = global_idx.get(gkey)
    if global_entry is None:
        norm = re.sub(r"[_\-\s]", "", gkey)
        for k, v in global_idx.items():
            if re.sub(r"[_\-\s]", "", k) == norm:
                global_entry = v
                break
    global_cf = _from_global_entry(global_entry or {}, device_id)

    ops = _read_ops_for_device(device_id)
    ops_cf = _from_ops(ops, device_id)

    merged = _merge(user_cf, global_cf)
    merged = _merge(merged, ops_cf)
    if not merged.source:
        merged.source = user_cf.source or global_cf.source or ops_cf.source or "empty"
    return merged


def write_fallback(
    username: str,
    device_id: str,
    fallback: ConsoleFallback,
    *,
    merge_with_existing: bool = True,
) -> ConsoleFallback:
    """Persist ``fallback`` to the per-user devices.json under ``device_id``.

    By default, merges with any pre-existing console_fallback record
    so we never blank out a field the user set manually just because
    auto-capture didn't rediscover it. Pass
    ``merge_with_existing=False`` for explicit overwrites.

    Never writes to the global SCALER devices.json.

    Returns the final ConsoleFallback that was persisted.
    """
    if not username or not device_id:
        return fallback
    data = _read_user_devices(username)
    entry = data.get(device_id)
    if not isinstance(entry, dict):
        entry = {}

    if merge_with_existing:
        existing = _from_user_entry(entry, device_id)
        fallback = _merge(fallback, existing)

    fallback.device_id = device_id
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not fallback.auto_captured_at:
        fallback.auto_captured_at = now_iso
    entry["console_fallback"] = fallback.to_dict()
    data[device_id] = entry
    _write_user_devices(username, data)
    return fallback


def capture_from_ops(
    username: str,
    device_id: str,
    *,
    reason: str = "auto",
) -> ConsoleFallback:
    """Read operational.json for ``device_id`` and persist a fallback
    record under the user's devices.json.

    No-op (returns an empty fallback) when the user is missing, the
    device has no operational.json, or the ops file has no
    backup-relevant fields.

    ``reason`` is stored in the ``notes`` field for forensics
    (e.g. ``"probe_success"`` or ``"upgrade_complete"``).
    """
    if not username or not device_id:
        return ConsoleFallback()
    ops = _read_ops_for_device(device_id)
    cf = _from_ops(ops, device_id)
    if cf.is_empty():
        return cf
    if reason:
        cf.notes = reason
    return write_fallback(username, device_id, cf, merge_with_existing=True)


def capture_from_probe_result(
    username: str,
    device_id: str,
    probe_result: Dict[str, Any],
    *,
    reason: str = "probe_success",
) -> ConsoleFallback:
    """Mirror a probe's ``methods`` list into a per-user fallback record.

    ``probe_result`` is expected to follow the shape returned by
    ``/api/ssh/probe``: a dict with ``methods: [{method, host, port,
    reachable, kvm_host_name, kvm_credentials, ncc_vms, ...}]`` and
    an optional ``cluster: {active_ncc_vm, ...}``.
    """
    if not username or not device_id or not isinstance(probe_result, dict):
        return ConsoleFallback()

    methods = probe_result.get("methods") or []
    cluster = probe_result.get("cluster") or {}

    cf = ConsoleFallback(device_id=device_id)
    cf.active_ncc_vm_hint = (cluster.get("active_ncc_vm") or "").strip()
    cf.serial_number = (cluster.get("serial_number") or probe_result.get("serial") or "").strip()
    cf.serial_hostname = cf.serial_number
    cf.ncc_type = cluster.get("ncc_type") or probe_result.get("ncc_type")

    for m in methods:
        if not isinstance(m, dict):
            continue
        meth = m.get("method")
        host = (m.get("host") or "").strip().split("/")[0]
        port = m.get("port")
        try:
            port_int = int(port) if port else None
        except Exception:
            port_int = None

        if meth == "virsh_console":
            cf.kvm_host_ip = cf.kvm_host_ip or host
            cf.kvm_host_name = cf.kvm_host_name or (m.get("kvm_host_name") or "").strip()
            creds = m.get("kvm_credentials") or {}
            cf.kvm_user = cf.kvm_user or creds.get("username", "")
            cf.kvm_pass = cf.kvm_pass or creds.get("password", "")
            for vm in m.get("ncc_vms") or []:
                if vm and vm not in cf.ncc_vms:
                    cf.ncc_vms.append(vm)
            vms_running = m.get("vms_running") or []
            for vm in vms_running:
                if vm and vm not in cf.ncc_vms:
                    cf.ncc_vms.append(vm)
            if not cf.active_ncc_vm_hint and vms_running:
                cf.active_ncc_vm_hint = vms_running[0]
        elif meth == "ssh_ncc":
            if host and re.match(r"^\d+\.\d+\.\d+\.\d+$", host):
                cf.ncc_mgmt_ip = cf.ncc_mgmt_ip or host
        elif meth == "console":
            cf.console_server_host = cf.console_server_host or host
            cf.console_server_port = cf.console_server_port or port_int
            creds = m.get("console_credentials") or {}
            cf.console_server_user = cf.console_server_user or creds.get("username", "")
            cf.console_server_pass = cf.console_server_pass or creds.get("password", "")
        elif meth == "ssh_sn":
            cf.serial_hostname = cf.serial_hostname or host

    if cf.is_empty():
        return cf
    cf.notes = reason
    return write_fallback(username, device_id, cf, merge_with_existing=True)


def sanitize(fallback: ConsoleFallback) -> Dict[str, Any]:
    """Return a dict with passwords redacted, safe to return from APIs."""
    data = fallback.to_dict()
    for key in PASSWORD_FIELDS:
        if data.get(key):
            data[key] = "***"
        else:
            data[key] = ""
    return data


def delete_fallback(username: str, device_id: str) -> bool:
    """Remove the ``console_fallback`` block from the user's record.

    Keeps the surrounding SSH-credential entry intact. Returns True
    when something was removed, False when no record existed.
    """
    if not username or not device_id:
        return False
    data = _read_user_devices(username)
    entry = data.get(device_id)
    if not isinstance(entry, dict) or "console_fallback" not in entry:
        return False
    entry.pop("console_fallback", None)
    data[device_id] = entry
    _write_user_devices(username, data)
    return True


def describe_availability(fallback: ConsoleFallback) -> Dict[str, bool]:
    """Return a flags-dict describing which fallback paths are configured.

    Handy for the GUI to render "have we got KVM info? what about a
    console server?" without exposing raw credentials.
    """
    return {
        "virsh_console": bool(
            fallback.kvm_host_ip
            and fallback.kvm_user
            and fallback.ncc_vms
        ),
        "ssh_ncc": bool(
            fallback.ncc_mgmt_ip
            and re.match(r"^\d+\.\d+\.\d+\.\d+$", fallback.ncc_mgmt_ip or "")
        ),
        "console_server": bool(
            fallback.console_server_host and fallback.console_server_port
        ),
        "ssh_sn": bool(fallback.serial_hostname),
    }


__all__ = [
    "ConsoleFallback",
    "capture_from_ops",
    "capture_from_probe_result",
    "delete_fallback",
    "describe_availability",
    "read_fallback",
    "sanitize",
    "write_fallback",
]
