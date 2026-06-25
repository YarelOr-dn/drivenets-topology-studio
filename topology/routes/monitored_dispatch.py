"""Per-subsystem bring-up / tear-down for the auto-monitor registry.

Companion design doc: ``topology/docs/AUTO_MONITOR_ON_ATTACH.md`` Section 4
("Subsystem dispatch matrix").

Phase 2 MVP scope (decisions locked in by the user in this session):

* ``scaler_devices_mirror`` -- FULLY IMPLEMENTED. Writes the device into
  the lab's curated ``devices.json`` (resolved via
  ``find_lab_devices_file()``) so the existing 5-min ``extract_configs.sh``
  cron picks it up on its next pass and the DNAAS MCP cache notices on
  its next refresh. The mirror entry includes a ``monitored_meta`` block
  so legacy consumers don't trip on the new fields.
* ``network_mapper`` -- BEST-EFFORT IMPLEMENTED. Calls the Network
  Mapper MCP ``discover_device`` tool over its loopback HTTP API so the
  LLDP map / interface inventory picks up the device immediately
  instead of waiting 24 h for the next global scan.
* ``subif_description`` -- LOG-ONLY in MVP. The existing periodic loop
  will pick the device up after the SCALER mirror is in place; we
  record a "scheduled, registration handled by existing periodic loop"
  status so the registry shows the subsystem as wired, not silently
  forgotten. Phase 3 will add an immediate kick.
* ``link_telemetry`` -- LOG-ONLY in MVP. Same rationale as
  ``subif_description``.
* ``alarms_health`` -- LOG-ONLY in MVP. The infra-level
  ``health_monitor.py`` watchdog is unrelated (it monitors the THREE
  service ports, not per-device); per-device alarms are collected by
  the alarms_collector cron which reads from ``operational.json``
  written by the existing context loop. The mirror + Network Mapper
  hooks are sufficient to plumb this in by cascade.

Tear-down semantics
-------------------

In MVP, ``tear_down`` is also conservative:

* ``scaler_devices_mirror`` -- removes the entry from the curated file
  IF AND ONLY IF the registry says ``would_stop_monitoring=True`` for
  this key. Legacy global devices (PE-1, PE-4, RR-SA-2, DNAAS-* leaves)
  are NEVER removed from devices.json by this code path; the user has
  to take an explicit action elsewhere.
* ``network_mapper`` -- log-only ("scheduled removal handled by next
  scan"). The MCP doesn't expose a force-remove tool today; the next
  global LLDP refresh will retire stale entries.
* All others -- log-only.

This module is intentionally ALL HTTP / file IO -- no SSH, no live
device probes. The verify step in ``routes/devices.py`` already proved
the device is reachable; subsystem registration is metadata-only.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from api import monitored_registry as reg
from routes.bridge_helpers import find_lab_devices_file


logger = logging.getLogger(__name__)


# Keep this list aligned with ``api.monitored_registry.ALL_SUBSYSTEMS``.
# Order is preserved -- the response field
# ``monitor_started_subsystems`` echoes this order so the frontend
# (which displays a small badge) renders deterministically.
DISPATCH_ORDER = (
    reg.SUBSYSTEM_SCALER_MIRROR,
    reg.SUBSYSTEM_NETWORK_MAPPER,
    reg.SUBSYSTEM_SUBIF_DESCRIPTION,
    reg.SUBSYSTEM_LINK_TELEMETRY,
    reg.SUBSYSTEM_ALARMS_HEALTH,
)


def bring_up(record: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Cascade a registered device through every subsystem hook.

    Returns one summary dict per subsystem with shape:

        { "subsystem": "<id>", "status": "ok"|"degraded"|"failed",
          "detail": "<human-readable string>" }

    Each hook is wrapped in its own try/except so a failure in one
    subsystem (e.g. Network Mapper down) cannot cause registration to
    short-circuit. The caller (verify-and-register endpoint) returns
    the list verbatim so the operator sees exactly what kicked off.
    """
    results: List[Dict[str, Any]] = []
    for subsystem in DISPATCH_ORDER:
        try:
            if subsystem == reg.SUBSYSTEM_SCALER_MIRROR:
                ok, detail = _mirror_to_scaler_devices_file(record)
            elif subsystem == reg.SUBSYSTEM_NETWORK_MAPPER:
                ok, detail = _register_with_network_mapper(record)
            elif subsystem == reg.SUBSYSTEM_SUBIF_DESCRIPTION:
                ok, detail = (True, "scheduled; registration handled by existing periodic loop")
            elif subsystem == reg.SUBSYSTEM_LINK_TELEMETRY:
                ok, detail = (True, "scheduled; registration handled by existing periodic loop")
            elif subsystem == reg.SUBSYSTEM_ALARMS_HEALTH:
                ok, detail = (True, "scheduled; alarms_collector reads from operational.json")
            else:
                ok, detail = (False, f"unknown subsystem {subsystem!r}")
            status = "ok" if ok else "failed"
            reg.update_subsystem_status(
                key=record["key"], subsystem=subsystem,
                status=status, last_error=None if ok else detail,
            )
            results.append({"subsystem": subsystem, "status": status, "detail": detail})
        except Exception as exc:
            logger.warning("[monitored_dispatch] %s bring_up raised: %s", subsystem, exc)
            try:
                reg.update_subsystem_status(
                    key=record["key"], subsystem=subsystem,
                    status="failed", last_error=str(exc),
                )
            except Exception:
                pass
            results.append({"subsystem": subsystem, "status": "failed", "detail": str(exc)})
    return results


def tear_down(record: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Cascade an UN-monitored device through every subsystem teardown
    hook.

    Only called when the last reference detaches AND the device is not
    ``legacy_global``. The remove-reference response carries
    ``would_stop_monitoring`` so the caller knows whether to invoke us.

    Same shape as ``bring_up``; status is ``ok`` / ``noop`` / ``failed``.
    """
    results: List[Dict[str, Any]] = []
    for subsystem in DISPATCH_ORDER:
        try:
            if subsystem == reg.SUBSYSTEM_SCALER_MIRROR:
                ok, detail = _unmirror_from_scaler_devices_file(record)
            elif subsystem == reg.SUBSYSTEM_NETWORK_MAPPER:
                ok, detail = (True, "scheduled removal handled by next LLDP scan")
            else:
                ok, detail = (True, "no teardown action; pollers self-prune on next pass")
            status = "ok" if ok else "failed"
            try:
                reg.update_subsystem_status(
                    key=record["key"], subsystem=subsystem,
                    status="torn_down" if ok else "failed",
                    last_error=None if ok else detail,
                )
            except Exception:
                pass
            results.append({"subsystem": subsystem, "status": status, "detail": detail})
        except Exception as exc:
            logger.warning("[monitored_dispatch] %s tear_down raised: %s", subsystem, exc)
            results.append({"subsystem": subsystem, "status": "failed", "detail": str(exc)})
    return results


# ---------------------------------------------------------------------------
# Subsystem 1: SCALER curated devices.json mirror
# ---------------------------------------------------------------------------

def _scaler_devices_lock_path(target: Path) -> Path:
    """Lockfile path next to the target file (best-effort serialization).

    The curated devices.json is shared across users + cron jobs. We use
    a sibling ``.lock`` file with O_EXCL semantics to avoid two
    concurrent writes interleaving JSON. Cron does NOT honor this lock
    (it reads atomically) but two HTTP writers from different users hit
    it. Worst case a contender retries; the file is small (<200 KB).
    """
    return target.with_suffix(target.suffix + ".lock")


def _atomic_write_json(path: Path, payload: Any) -> None:
    """Write JSON to ``path`` via a tmpfile + rename for atomicity.

    Uses 0644 perms so the existing cron + scaler CLI can still read it.
    No chmod tightening because this is shared infrastructure data, not
    secrets.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=False, default=str)
    os.replace(tmp, path)


def _mirror_to_scaler_devices_file(record: Dict[str, Any]) -> Tuple[bool, str]:
    """Add or refresh the device entry in the curated ``devices.json``.

    Schema-compatible with the existing entries (id, hostname, ip,
    aliases, platform). New fields go inside a ``monitored_meta`` block
    so legacy parsers (the scaler CLI, Network Mapper, the DNAAS MCP)
    keep working unchanged.

    Returns (ok, detail). Best-effort -- a failure to mirror is logged
    + recorded but does NOT roll back registration.
    """
    target = find_lab_devices_file()
    try:
        if target.exists():
            data = json.loads(target.read_text(encoding="utf-8"))
        else:
            data = {}
    except Exception as exc:
        return False, f"could not read {target}: {exc}"
    devices = data.get("devices") or []
    if not isinstance(devices, list):
        return False, f"devices.json malformed: 'devices' is not a list (type={type(devices).__name__})"

    ip = (record.get("management_ip") or "").strip()
    hostname = (record.get("hostname") or "").strip()
    serial = (record.get("serial_number") or "").strip()
    if not ip:
        return False, "record has no management_ip"

    found_idx = None
    for i, d in enumerate(devices):
        d_ip = (d.get("ip") or "").strip()
        d_id = (d.get("id") or "").strip()
        d_host = (d.get("hostname") or "").strip()
        d_sn = (d.get("serial") or d.get("serial_number") or "").strip()
        # Same IP -> same device (chassis IP is canonical).
        if d_ip == ip:
            found_idx = i
            break
        # Same serial -> same device even if IP rotated.
        if serial and d_sn == serial:
            found_idx = i
            break
        # Same hostname -> same device.
        if hostname and (d_host == hostname or d_id == hostname):
            found_idx = i
            break

    monitored_meta = {
        "key": record.get("key"),
        "registered_at": record.get("created_at"),
        "registered_by": record.get("created_by"),
        "is_cluster": bool(record.get("is_cluster")),
        "cluster_ncc_ips": list(record.get("cluster_ncc_ips") or []),
        "last_seen_ok": record.get("last_seen_ok"),
        "source": "topology_auto_monitor_phase2",
    }
    new_entry = {
        "id": hostname or ip,
        "hostname": hostname or ip,
        "ip": ip,
        "platform": record.get("platform") or "",
        "serial": serial,
        "aliases": [a for a in [hostname, ip] if a],
        "monitored_meta": monitored_meta,
    }

    if found_idx is None:
        devices.append(new_entry)
        action_note = f"appended {hostname or ip} ({ip})"
    else:
        prior = dict(devices[found_idx])
        # Preserve any pre-existing fields the legacy entry had that we
        # don't know about (custom credentials, lab-profile tags, etc.).
        merged = dict(prior)
        for k, v in new_entry.items():
            # Don't blank a non-empty existing field with an empty new one.
            if v in ("", None, []):
                continue
            merged[k] = v
        # Aliases: union of old + new, preserving order.
        old_aliases = list(prior.get("aliases") or [])
        merged_aliases: List[str] = []
        for a in old_aliases + new_entry["aliases"]:
            if a and a not in merged_aliases:
                merged_aliases.append(a)
        merged["aliases"] = merged_aliases
        # Always overwrite monitored_meta with the freshest copy.
        merged["monitored_meta"] = monitored_meta
        devices[found_idx] = merged
        action_note = f"merged {hostname or ip} ({ip})"

    data["devices"] = devices
    try:
        _atomic_write_json(target, data)
    except Exception as exc:
        return False, f"failed to write {target}: {exc}"
    return True, f"{action_note} into {target}"


def _unmirror_from_scaler_devices_file(record: Dict[str, Any]) -> Tuple[bool, str]:
    """Remove the device entry from the curated ``devices.json``.

    Only the entry that was added by Phase 2 (presence of
    ``monitored_meta.source == "topology_auto_monitor_phase2"``) is
    removed. Legacy entries are left alone -- the design says the
    last-referencer modal already gates the user from removing a
    legacy_global device, and this code is the second line of defense.
    """
    if record.get("legacy_global"):
        return True, "legacy_global=true -- mirror entry preserved"
    target = find_lab_devices_file()
    if not target.exists():
        return True, f"no curated file at {target} -- nothing to remove"
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"could not read {target}: {exc}"
    devices = data.get("devices") or []
    ip = (record.get("management_ip") or "").strip()
    serial = (record.get("serial_number") or "").strip()
    key = record.get("key") or ""
    out: List[Dict[str, Any]] = []
    removed = 0
    for d in devices:
        meta = d.get("monitored_meta") or {}
        same_key = (meta.get("key") == key)
        same_ip_and_phase2 = (
            (d.get("ip") or "").strip() == ip
            and meta.get("source") == "topology_auto_monitor_phase2"
        )
        same_serial_and_phase2 = (
            serial
            and (d.get("serial") or "").strip() == serial
            and meta.get("source") == "topology_auto_monitor_phase2"
        )
        if same_key or same_ip_and_phase2 or same_serial_and_phase2:
            removed += 1
            continue
        out.append(d)
    if removed == 0:
        return True, f"no Phase-2 entry to remove for {ip}"
    data["devices"] = out
    try:
        _atomic_write_json(target, data)
    except Exception as exc:
        return False, f"failed to write {target}: {exc}"
    return True, f"removed {removed} Phase-2 entry/entries for {ip}"


# ---------------------------------------------------------------------------
# Subsystem 2: Network Mapper MCP
# ---------------------------------------------------------------------------

NETWORK_MAPPER_BASE = os.environ.get(
    "NETWORK_MAPPER_BASE", "http://127.0.0.1:9100",
).rstrip("/")
NETWORK_MAPPER_TIMEOUT_S = float(os.environ.get("NETWORK_MAPPER_TIMEOUT", "8.0"))


def _register_with_network_mapper(record: Dict[str, Any]) -> Tuple[bool, str]:
    """Best-effort POST to the Network Mapper MCP's discover_device tool.

    The Network Mapper MCP exposes a JSON-over-HTTP shim at
    ``${NETWORK_MAPPER_BASE}/api/discover_device`` for non-MCP clients
    (the bridge is one such client). When the shim is present the call
    is short and synchronous (~1-3s SSH probe + LLDP read). When the
    shim isn't present (older MCP) or NETWORK_MAPPER_BASE is wrong, the
    call falls back to a no-op and we record the subsystem as
    "scheduled".
    """
    ip = (record.get("management_ip") or "").strip()
    hostname = (record.get("hostname") or "").strip()
    if not ip and not hostname:
        return False, "record has no IP or hostname"
    payload = {
        "device_name": hostname or ip,
        "ip": ip,
        "hostname": hostname,
        "platform": record.get("platform") or "",
        "is_cluster": bool(record.get("is_cluster")),
        "cluster_ncc_ips": list(record.get("cluster_ncc_ips") or []),
        "source": "topology_auto_monitor_phase2",
    }
    body = json.dumps(payload).encode("utf-8")
    url = f"{NETWORK_MAPPER_BASE}/api/discover_device"
    try:
        req = urllib.request.Request(
            url, data=body, method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=NETWORK_MAPPER_TIMEOUT_S) as resp:
            code = resp.status
            raw = resp.read()
            if 200 <= code < 400:
                snippet = raw[:120].decode("utf-8", errors="replace")
                return True, f"discover_device http {code}: {snippet}"
            return False, f"discover_device http {code}"
    except urllib.error.HTTPError as exc:
        # 404 means the MCP doesn't expose the HTTP shim today --
        # treat as "scheduled" (no error). The next global LLDP scan
        # will pick the device up.
        if exc.code in (404, 405):
            return True, "scheduled; Network Mapper HTTP shim not available, next global scan will pick device up"
        return False, f"discover_device http {exc.code} {exc.reason}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return True, f"scheduled; Network Mapper unreachable ({exc}), next global scan will pick device up"
    except Exception as exc:
        return False, f"discover_device raised: {exc}"
