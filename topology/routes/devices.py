"""Scaler bridge routes: devices."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Body, HTTPException, Request

from routes.bridge_helpers import (
    INVENTORY_FILE, SCALER_ROOT, _clean_system_type,
    _build_scaler_ops_index, _identity_guard_matches_entry,
    _compute_wizard_suggestions, _fetch_all_operational_via_ssh,
    _fetch_git_commit_via_ssh, _get_credentials, _get_device_context,
    _get_lab_credential_chain, _resolve_device, _resolve_mgmt_ip,
    _save_user_sys_type_override, _ssh_pool, _strip_ansi,
)
from routes._state import _push_jobs, _push_jobs_lock, _get_request_user
from routes._ops_writer import read_ops as _read_ops_safe

router = APIRouter()


def _parse_identity_guard(raw: str = "") -> dict:
    """Parse optional frontend identity guard from query parameters."""
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _safe_identity_id(device_id: str, guard: dict) -> str:
    """Pick a non-empty identity for writing fresh data when IP cache owner differs."""
    for key in (
        "registry_hostname",
        "verified_hostname",
        "hostname",
        "registered_device_id",
        "registry_serial_number",
        "verified_serial",
        "serial_number",
        "requested_device_id",
    ):
        val = str((guard or {}).get(key) or "").strip()
        if val:
            return val
    return device_id

@router.post("/api/wizard/suggestions")
def wizard_suggestions(body: dict = None, request: Request = None):
    """Backend-driven next-wizard suggestions with pre-fill data.

    Request: { device_id, completed_wizard, created_data: { interfaces, loopback_ip, vrfs, ... },
               ssh_host?, domain_id?, topology_id? }
    Response: { suggestions: [{ wizard, reason, prefill }, ...] }

    ``domain_id`` / ``topology_id`` scope the per-user system_type
    override (same layer as ``GET .../context``) so suggestions reflect
    what the operator explicitly picked earlier in the same topology.
    """
    body = body or {}
    device_id = body.get("device_id") or ""
    completed_wizard = body.get("completed_wizard") or ""
    created_data = body.get("created_data") or {}
    ssh_host = body.get("ssh_host") or ""
    domain_id = str(body.get("domain_id") or "").strip()
    topology_id = str(body.get("topology_id") or "").strip()

    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")

    try:
        app_user = _get_request_user(request) if request else "default"
        ctx = _get_device_context(device_id, live=False, ssh_host=ssh_host,
                                  app_user=app_user,
                                  domain_id=domain_id,
                                  topology_id=topology_id)
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
def get_device_context(device_id: str, live: bool = False, ssh_host: str = "",
                       domain_id: str = "", topology_id: str = "",
                       bypass_cache: bool = False,
                       identity_guard: str = "",
                       request: Request = None):
    """Unified device context for wizard suggestions.

    Query params:
        live: Force live SSH fetch instead of cached
        ssh_host: SSH IP/hostname from canvas device (primary resolution key)
        bypass_cache: When true together with ``live=true`` the live-fetch
            coalescer key for this (device, user) is invalidated BEFORE the
            fetch runs so the manual "Refresh" path always issues a real
            SSH probe and we get fresh STACK-TIMING evidence in the bridge
            log. Background pollers and other tabs keep using the 90-s
            coalescer cache so we still avoid a thundering herd.
        domain_id / topology_id: optional multi-user scope so a per-user
            system_type override stored under
            ``~/.topology_users/<user>/device_overrides.json`` takes
            precedence over the global scaler curated cache. The frontend
            should pass both whenever ``TopologySync.getActive()`` has a
            value so operator A's "PE-4 = CL-86" pick never leaks into
            operator B's topology that happens to label a different
            physical device "PE-4".
    """
    try:
        app_user = _get_request_user(request) if request else "default"
        guard = _parse_identity_guard(identity_guard)
        return _get_device_context(device_id, live=live, ssh_host=ssh_host,
                                   app_user=app_user,
                                   domain_id=domain_id,
                                   topology_id=topology_id,
                                   bypass_cache=bypass_cache,
                                   identity_guard=guard or None)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/api/devices/{device_id}/mode-probe")
def get_device_mode_probe(device_id: str, ssh_host: str = "",
                          live: bool = False, request: Request = None):
    """Lightweight device-mode probe used by the topology-app gate layer.

    Returns the canonical mode (DNOS / GI / RECOVERY / unknown) for a
    device along with the freshness of the answer so the frontend can
    decide whether to allow operations like DNAAS discovery, packet
    capture, or AI config apply.

    Resolution order (cheapest first):
      1. ``operational.json`` cache. We read ``device_state`` and the
         most recent ``stack_fetched_at`` / ``connection_probe_at`` /
         ``ncc_mgmt_verified_at`` timestamp to derive a freshness
         age. UPGRADING/DEPLOYING are *never* returned as a stable
         mode -- they are ops-flow flags, not CLI state.
      2. If ``live=true`` (or the cache is empty), open a 6s SSH
         session and read one prompt line -- ``detect_device_mode``
         on the buffer is the SAME helper the wizard, scaler monitor,
         and DeviceMonitor all share, so the answer can never drift.

    Response shape (always 200, never 503):

    ::

        {
          "device_id": str,
          "mode": "DNOS" | "GI" | "RECOVERY" | "unknown",
          "raw_state": str,           # untouched value from ops_data
          "fetched_at": iso8601 | "", # when the mode was last refreshed
          "age_seconds": int | null,  # how stale the cache is, null if no fetched_at
          "source": "cache" | "live" | "live_failed_cache",
          "ssh_reachable": bool,
          "transient_op": str,        # "UPGRADING"/"DEPLOYING"/"" -- never returned as mode
          "operations": {
            "dnaas_discovery": { allowed: bool, reason: str },
            "packet_capture":  { allowed: bool, reason: str },
            "config_apply":    { allowed: bool, reason: str },
            "terminal":        { allowed: bool, reason: str }
          }
        }
    """
    import json as _json
    import time as _time
    from datetime import datetime, timezone

    from scaler.connection_strategy import detect_device_mode, classify_device_state

    def _norm_mode(m: str) -> str:
        return m if m in ("DNOS", "GI", "RECOVERY") else "unknown"

    def _age_seconds(iso: str):
        if not iso:
            return None
        try:
            s = iso.rstrip("Z")
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return max(0, int((datetime.now(timezone.utc) - dt).total_seconds()))
        except Exception:
            return None

    def _gate_for(mode: str, ssh_ok: bool, transient: str) -> dict:
        is_dnos = mode == "DNOS"
        gi = mode == "GI"
        rec = mode == "RECOVERY"
        unk = mode == "unknown"

        def _R(msg: str) -> dict:
            return {"allowed": False, "reason": msg}

        ops = {}
        if rec:
            why = "Device is in RECOVERY mode -- DNOS CLI is not running."
            ops = {
                "dnaas_discovery": _R(why),
                "packet_capture":  _R(why),
                "config_apply":    _R(why),
                "terminal":        {"allowed": True, "reason": "Console-only; expect a recovery prompt."},
            }
        elif gi:
            why = "Device is in GI mode -- DNOS CLI not yet active. Run an upgrade/deploy first."
            ops = {
                "dnaas_discovery": _R(why),
                "packet_capture":  _R("Packet capture requires DNOS CLI on the device."),
                "config_apply":    _R(why),
                "terminal":        {"allowed": True, "reason": "Console-only; you'll see the GI shell."},
            }
        elif unk:
            if transient in ("UPGRADING", "DEPLOYING"):
                why = f"An image {transient.lower()} job is in progress. Wait for completion."
                ops = {
                    "dnaas_discovery": _R(why),
                    "packet_capture":  _R(why),
                    "config_apply":    _R(why),
                    "terminal":        {"allowed": True, "reason": "May land on a transient prompt during upgrade."},
                }
            else:
                why = "Device mode is unknown. Re-detect (live probe) before running this operation."
                ops = {
                    "dnaas_discovery": _R(why),
                    "packet_capture":  _R(why),
                    "config_apply":    _R(why),
                    "terminal":        {"allowed": True, "reason": "Will attempt connection; outcome depends on real state."},
                }
        elif is_dnos and not ssh_ok:
            why = "Device is in DNOS but SSH is currently unreachable. Check management IP / firewall."
            ops = {
                "dnaas_discovery": _R(why),
                "packet_capture":  _R(why),
                "config_apply":    _R(why),
                "terminal":        {"allowed": True, "reason": "Console may still work even if SSH is down."},
            }
        else:
            ops = {
                "dnaas_discovery": {"allowed": True, "reason": ""},
                "packet_capture":  {"allowed": True, "reason": ""},
                "config_apply":    {"allowed": True, "reason": ""},
                "terminal":        {"allowed": True, "reason": ""},
            }
        return ops

    raw_state = ""
    fetched_at = ""
    cached_mgmt_ip = ""
    ssh_reachable = False
    source = "cache"
    transient_op = ""

    try:
        ops_path = Path(SCALER_ROOT) / "db" / "configs" / device_id / "operational.json"
        if ops_path.exists():
            try:
                ops = _read_ops_safe(ops_path)
            except Exception:
                ops = {}
            raw_state = (ops.get("device_state") or "").strip()
            fetched_at = (
                ops.get("stack_fetched_at")
                or ops.get("connection_probe_at")
                or ops.get("ncc_mgmt_verified_at")
                or ""
            )
            cached_mgmt_ip = (ops.get("mgmt_ip") or "").strip()
            if (ops.get("ssh_reachable") in (True, "true", "True")
                    or ops.get("ssh_auth_ok") in (True, "true", "True")):
                ssh_reachable = True
            up = raw_state.upper()
            if up in ("UPGRADING", "DEPLOYING"):
                transient_op = up
    except Exception:
        pass

    mode = _norm_mode(classify_device_state(raw_state))

    if live:
        try:
            target_ip, _scaler_id, _via = _resolve_mgmt_ip(device_id, ssh_host or cached_mgmt_ip)
        except Exception:
            target_ip = ""

        if target_ip:
            try:
                from scaler.dnos_session import DNOSSession
                user, password = _get_credentials(device_id=device_id)
                buf = ""
                try:
                    with DNOSSession(target_ip, user, password, connect_timeout=6) as sess:
                        ssh_reachable = bool(sess.is_alive())
                        if ssh_reachable:
                            try:
                                buf = sess.send_and_receive("\n", timeout=4) or ""
                            except Exception:
                                buf = ""
                except Exception:
                    ssh_reachable = False
                live_mode = _norm_mode(detect_device_mode(buf)) if buf else "unknown"
                if live_mode != "unknown":
                    mode = live_mode
                    raw_state = live_mode
                    fetched_at = _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())
                    source = "live"
                    transient_op = ""
                    try:
                        from ._ops_writer import update_ops as _uops_probe

                        def _persist_probe(d: dict, _state=live_mode, _ts=fetched_at) -> None:
                            d["device_state"] = _state
                            d["connection_probe_at"] = _ts
                            d["ssh_reachable"] = True

                        _uops_probe(ops_path, _persist_probe, create_if_missing=True)
                    except Exception:
                        pass
                else:
                    source = "live_failed_cache"
            except Exception:
                source = "live_failed_cache"

    return {
        "device_id": device_id,
        "mode": mode,
        "raw_state": raw_state,
        "fetched_at": fetched_at,
        "age_seconds": _age_seconds(fetched_at),
        "source": source,
        "ssh_reachable": ssh_reachable,
        "transient_op": transient_op,
        "operations": _gate_for(mode, ssh_reachable, transient_op),
    }


@router.get("/api/devices/{device_id}/git-commit")
def get_device_git_commit(device_id: str, ssh_host: str = "", ssh_user: str = "",
                          ssh_password: str = "", request: Request = None):
    """Lightweight endpoint: SSH only for git_commit. Use when context fetch returns null git_commit.
    Returns {git_commit: null} instead of 503 on SSH failure -- this is a best-effort call.
    Checks operational.json cache first to avoid slow virsh roundtrip."""
    import time as _time
    from pathlib import Path
    def _candidate_config_ids() -> list[str]:
        ids = []
        seen = set()

        def add(value: str) -> None:
            clean = str(value or "").strip()
            if not clean:
                return
            key = clean.lower()
            if key not in seen:
                seen.add(key)
                ids.append(clean)

        add(device_id)
        add(ssh_host)
        try:
            idx = _build_scaler_ops_index()
            for value in (device_id, ssh_host):
                entry = idx.get(str(value or "").strip().lower())
                if entry:
                    add(entry.get("scaler_id", ""))
        except Exception:
            pass
        return ids

    for candidate_id in _candidate_config_ids():
        try:
            ops_path = Path(SCALER_ROOT) / "db" / "configs" / candidate_id / "operational.json"
            if ops_path.exists():
                ops = _read_ops_safe(ops_path)
                cached_gc = ops.get("git_commit")
                if cached_gc:
                    return {
                        "git_commit": cached_gc,
                        "git_commit_fetched_at": ops.get("git_commit_fetched_at") or "",
                        "source": "cache",
                        "cache_device_id": candidate_id,
                    }
        except Exception:
            pass
    try:
        mgmt_ip, _, _ = _resolve_mgmt_ip(device_id, ssh_host)
    except Exception:
        return {"git_commit": None}
    try:
        default_user, default_password = _get_credentials(device_id=device_id)
        user = ssh_user or default_user
        password = ssh_password or default_password
        app_user = _get_request_user(request) if request else "default"
        git_hash = _fetch_git_commit_via_ssh(mgmt_ip, user, password,
                                               scaler_device_id=device_id,
                                               app_user=app_user)
        return {"git_commit": git_hash, "source": "live"}
    except Exception:
        return {"git_commit": None, "source": "unavailable"}


@router.get("/api/devices/{device_id}/stack-fast")
def get_device_stack_fast(device_id: str, ssh_host: str = "",
                          bypass_cache: bool = False,
                          identity_guard: str = "",
                          request: Request = None):
    """Fast stack-only refresh for the Stack dialog Refresh button.

    Single SSH session that runs ONLY ``show system stack`` and ``show
    system`` (~4-8 s on a healthy active NCC). Returns the data the
    dialog actually renders -- stack components, device_state, the
    active NCC node, and a fresh ISO timestamp -- nothing else.

    The same data is persisted into the device's ``operational.json``
    by :func:`_fetch_stack_only_via_ssh` so the next page-load cached
    read is also fresh. The persistence step also refreshes the
    cluster LKG memo (``active_ncc_last_good_at``) so the next
    cluster refresh can skip the standby-NCC dance.

    Concurrency: per-(device, user) coalescer with a 30-s TTL. Within
    that window successive clicks share the same SSH probe. Pass
    ``bypass_cache=true`` when the user clicks Refresh and wants a
    real fresh probe (the dialog does this by default).

    Response::

        {
            "components":         [{name, hw_model, revert, current, target}, ...],
            "device_state":       "DNOS" | "GI" | "RECOVERY" | null,
            "active_ncc_node":    "ncc0" | "ncc1" | null,
            "stack_fetched_at":   "2026-04-29T15:30:00Z",
            "source":             "stack_fast",
            "raw_output":         "..."         # only when components is empty
        }
    """
    from routes._live_coalescer import coalescer as _live_coalescer

    try:
        mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(device_id, ssh_host)
    except Exception:
        return {"components": [], "error": "Cannot resolve device"}

    app_user = _get_request_user(request) if request else "default"
    user, password = _get_credentials(device_id=device_id)
    guard = _parse_identity_guard(identity_guard)
    cache_owner_conflicts = []
    cache_device_id = scaler_id or device_id
    if guard and mgmt_ip:
        try:
            idx = _build_scaler_ops_index()
            entry = idx.get(str(cache_device_id or "").lower()) or idx.get(mgmt_ip)
            if entry and not _identity_guard_matches_entry(entry, guard):
                cache_owner_conflicts.append({
                    "owner": entry.get("scaler_id") or "",
                    "hostname": entry.get("hostname") or "",
                    "serial": entry.get("serial") or "",
                    "ip": entry.get("ip") or "",
                    "reason": "stack_fast_same_ip_owner_did_not_match_current_identity",
                })
                cache_device_id = _safe_identity_id(device_id, guard)
        except Exception:
            pass

    coalesce_key = (
        f"stackfast:{cache_device_id}:{mgmt_ip}:{app_user}"
    )
    if bypass_cache:
        try:
            _live_coalescer.invalidate(coalesce_key)
        except Exception:
            pass

    def _do_fetch():
        return _fetch_stack_only_via_ssh(
            mgmt_ip, user, password,
            scaler_device_id=cache_device_id,
            app_user=app_user,
        )

    try:
        ops, origin = _live_coalescer.get(
            coalesce_key, _do_fetch, ttl_seconds=30.0,
        )
    except Exception as e:
        return {"components": [], "error": str(e)}

    components = ops.get("stack") or []
    resp = {
        "components": components,
        "source": f"stack_fast:{origin}",
        "stack_fetched_at": ops.get("stack_fetched_at") or "",
        "cache_owner_conflicts": cache_owner_conflicts,
        "resolved_ip": mgmt_ip,
        "device_id": cache_device_id,
    }
    if ops.get("device_state"):
        resp["device_state"] = ops["device_state"]
    if ops.get("active_ncc_node"):
        resp["active_ncc_node"] = ops["active_ncc_node"]
    if not components and ops.get("raw_output"):
        resp["raw_output"] = ops["raw_output"]
    return resp


@router.post("/api/devices/{device_id}/stack-live")
def get_device_stack_live(device_id: str, body: dict = Body(default={}),
                          request: Request = None):
    """Fetch live stack via SSH (with virsh fallback for cluster devices).
    Body: { ssh_host?: str, ssh_user?: str, ssh_password?: str }"""
    ssh_host = (body.get("ssh_host") or "").strip()
    try:
        mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(device_id, ssh_host)
    except Exception:
        return {"components": [], "error": "Cannot resolve device"}
    try:
        app_user = _get_request_user(request) if request else "default"
        default_user, default_password = _get_credentials(device_id=device_id)
        user = (body.get("ssh_user") or "").strip() or default_user
        password = (body.get("ssh_password") or "").strip() or default_password
        ops = _fetch_all_operational_via_ssh(mgmt_ip, user, password,
                                             scaler_device_id=scaler_id or device_id,
                                             app_user=app_user)
        stack = ops.get("stack") or []
        raw = ""
        if not stack:
            raw = "No stack data returned from device"
        resp = {"components": stack, "raw_output": raw}
        if ops.get("active_ncc_node"):
            resp["active_ncc_node"] = ops["active_ncc_node"]
        if ops.get("device_state"):
            resp["device_state"] = ops["device_state"]
        return resp
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
    user, password = _get_credentials(device_id=device_id)

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


@router.post("/api/devices/{device_id}/system-type")
def persist_device_system_type(device_id: str, body: dict = None,
                               request: Request = None):
    """Persist a manually-chosen ``system_type`` under the authenticated
    user's workspace (``~/.topology_users/<user>/device_overrides.json``).

    Scope model (most-specific first):

      1. ``per_topology[<domain_id>:<topology_id>][<key>]`` -- only applies
         to the topology the operator is currently working on.
      2. ``per_user[<key>]`` -- cross-topology carry-over for the same user
         so the pick still helps after opening another topology that
         references the same physical device.

    Both layers take precedence over the global scaler curated cache
    (``SCALER/db/devices.json``). A subsequent live DNOS probe still
    rewrites ``operational.json`` with the hardware truth, but it no
    longer overwrites the user override -- the user's pick wins until
    explicitly cleared or until a live probe returns a *matching* value
    that makes the override redundant.

    By default this endpoint does NOT touch ``db/devices.json``:
    that file is shared across every user and every topology on the host
    (first-match-wins lookup), so writing a user-specific correction into
    it leaked one operator's pick into everyone else's wizard. See
    ``.cursor/rules/multiuser-by-default.mdc`` for the full rationale.

    The optional ``commit_global`` flag (added 2026-04-24 for the PE-4
    cluster drift) lets the operator deliberately promote a cluster
    correction (``CL-*``) into ``db/devices.json`` with the
    ``operator_pinned`` provenance tag. This is the affordance the
    scaler CLI plan-builder needs, because its deploy command reads
    ``system_type`` straight from that file -- per-user overrides never
    reach the CLI. Guard rails:

      * Only accepted for cluster targets (``CL-*``). Non-cluster picks
        stay per-user; they never touch the global file.
      * The write is tagged ``system_type_source = operator_pinned`` so
        subsequent auto-heals from stale DNAAS inventory or config
        backups cannot downgrade the value back to the bogus ``SA-*``
        NCP-1 snapshot (see ``_persist_system_type_to_scaler_db``).
      * A live DNOS probe IS still allowed to refine the pin to a
        different ``CL-*`` code -- hardware is the authority once the
        cluster is back from GI.

    Body::

        {
            "system_type": "CL-86",       # required; any value in
                                          # ScalerGUI._WIZARD_KNOWN_SYS_TYPES
            "ssh_host": "10.0.0.1",       # optional, helps resolve mgmt_ip
            "domain_id": "net-ops",       # optional, TopologySync.getActive().domain_id
            "topology_id": "prod-core",   # optional, TopologySync.getActive().topology_id
            "commit_global": true         # optional; when true AND value is CL-*,
                                          # also pin into SCALER/db/devices.json
                                          # so the scaler CLI deploy plan picks
                                          # up the cluster system_type
        }

    401 when no JWT is attached (see the multi-user rule); the global
    fallback path is deliberately unreachable.
    """
    if not body or not body.get("system_type"):
        raise HTTPException(status_code=400, detail="Missing 'system_type' in request body")

    raw_st = str(body["system_type"]).strip()
    cleaned = _clean_system_type(raw_st)
    if not cleaned:
        raise HTTPException(
            status_code=400,
            detail=f"Unrecognised system_type '{raw_st}'. Expected a value like CL-86 / SA-40C8CD.",
        )

    app_user = _get_request_user(request) if request else ""
    if not app_user or app_user == "default":
        raise HTTPException(
            status_code=401,
            detail="authentication required to persist per-user device overrides",
        )

    ssh_host = body.get("ssh_host", "")
    domain_id = str(body.get("domain_id") or "").strip()
    topology_id = str(body.get("topology_id") or "").strip()
    commit_global = bool(body.get("commit_global"))

    mgmt_ip = ""
    hostname = device_id
    try:
        mgmt_ip, _scaler_id, _via = _resolve_mgmt_ip(device_id, ssh_host)
    except Exception:
        pass
    try:
        resolved = _resolve_device(device_id)
        hostname = resolved.get("hostname") or resolved.get("name") or device_id
    except Exception:
        pass

    persisted = _save_user_sys_type_override(
        app_user=app_user,
        device_id=device_id,
        system_type=cleaned,
        mgmt_ip=mgmt_ip or "",
        hostname=hostname or "",
        domain_id=domain_id,
        topology_id=topology_id,
    )
    scope = "per_topology" if (topology_id or domain_id) else "per_user"

    global_pinned = False
    global_skipped_reason = ""
    if commit_global:
        if cleaned.upper().startswith("CL-"):
            # Cluster-only safeguard: non-cluster picks stay per-user to
            # preserve the multi-user isolation guarantee. Cluster picks
            # are promoted because the scaler CLI's deploy command only
            # reads system_type from db/devices.json, so without this
            # hop the plan keeps emitting the stale NCP-1 SA-* code.
            from .bridge_helpers import _persist_system_type_to_scaler_db
            try:
                global_pinned = _persist_system_type_to_scaler_db(
                    device_id=device_id,
                    system_type=cleaned,
                    mgmt_ip=mgmt_ip or "",
                    hostname=hostname or "",
                    source="operator_pinned",
                )
            except Exception as exc:
                global_skipped_reason = f"persist_failed: {exc}"
        else:
            global_skipped_reason = "non_cluster_value_rejected"

    return {
        "status": "ok",
        "device_id": device_id,
        "system_type": cleaned,
        "persisted": persisted,
        "scope": scope,
        "domain_id": domain_id,
        "topology_id": topology_id,
        "mgmt_ip": mgmt_ip,
        "hostname": hostname,
        "commit_global": commit_global,
        "global_pinned": global_pinned,
        "global_skipped_reason": global_skipped_reason,
    }


@router.post("/api/devices/{device_id}/test")
def test_device_connection(device_id: str, ssh_host: str = ""):
    """Test SSH connectivity to a device. Uses DNOSSession + central _resolve_mgmt_ip.

    Walks the lab credential chain (DUT -> DNAAS -> Arista) so a connection
    test against a DNAAS LEAF doesn't fail just because dnroot/dnroot was
    tried first. Returns the profile that succeeded so the UI can show
    "Connected as <user> (DNAAS profile)".
    """
    mgmt_ip, scaler_id, via = _resolve_mgmt_ip(device_id, ssh_host)
    from scaler.dnos_session import DNOSSession

    chain = _get_lab_credential_chain(device_id=device_id)
    if not chain:
        chain = [("dut", "dnroot", "dnroot")]

    last_err = None
    for profile_name, user, password in chain:
        try:
            with DNOSSession(mgmt_ip, user, password, connect_timeout=8) as sess:
                if sess.is_alive():
                    return {
                        "status": "ok",
                        "message": f"Connection OK ({mgmt_ip}, via {via})",
                        "credential_profile": profile_name,
                        "username": user,
                    }
        except Exception as e:
            last_err = str(e)
            err_low = last_err.lower()
            transient = ("auth" in err_low or "permission" in err_low or
                         "password" in err_low or "denied" in err_low)
            if not transient:
                # Network / DNS / timeout -- next profile won't help.
                raise HTTPException(status_code=503, detail=f"SSH to {mgmt_ip} failed: {e}")

    raise HTTPException(
        status_code=503,
        detail=f"SSH to {mgmt_ip} failed for all {len(chain)} credential profile(s): {last_err}",
    )


class _SyntheticRequest:
    """Minimal stand-in for FastAPI's ``Request`` for in-process calls.

    The route helpers in ``routes/ssh.py`` (``verify_ssh_identity``,
    ``probe_connection``) read ``request.state.user`` via
    ``_get_request_user``. When ``verify_credentials_inline`` is called
    from another router (no real ``Request`` available) we build this
    shim so the inner helpers see the SAME authenticated username
    instead of silently falling back to ``"default"`` -- which would be
    a multi-user attribution bug per ``multiuser-by-default.mdc``.
    """
    __slots__ = ("state",)

    def __init__(self, app_user: str):
        # Mimic FastAPI's request.state which is just an object with attrs.
        ns = type("State", (), {})()
        ns.user = app_user or ""
        ns.role = "engineer"
        self.state = ns


def verify_credentials_inline(device_id: str, body: Optional[dict],
                              app_user: str) -> dict:
    """Programmatic entry point for the verify-credentials flow.

    Identical behaviour to the FastAPI route immediately below, but
    callable from any in-process code without an HTTP round-trip. Used by
    ``routes/monitored_devices.py::verify_and_register`` so the new
    auto-monitor endpoint reuses the proven verify path instead of
    duplicating SSH handshake logic.

    ``app_user`` is passed in (already resolved via JWT middleware) so
    this helper does not need a real ``request`` object. We build a
    minimal synthetic stand-in so the inner ``routes/ssh.py`` helpers
    see the right ``state.user`` for credential lookup.

    Returns the same structured dict as the route. Never raises on
    routine credential failures; ``HTTPException`` only on bad input
    (missing device_id / host).
    """
    fake_req = _SyntheticRequest(app_user or "")
    return _verify_credentials_impl(device_id, body, fake_req)


@router.post("/api/devices/{device_id}/verify-credentials")
def verify_device_credentials(device_id: str, body: dict = None,
                              request: Request = None):
    """HTTP wrapper -- see ``_verify_credentials_impl`` for the full docstring."""
    return _verify_credentials_impl(device_id, body, request)


def _verify_credentials_impl(device_id: str, body: Optional[dict],
                             request) -> dict:
    """Verify operator-entered SSH credentials, capture cluster identity,
    and (optionally) register the device for fast-initial monitoring.

    Called by the SSH dialog Save button BEFORE persisting the
    credentials into the topology JSON. The verification is a single
    composed call that piggy-backs on existing endpoints so we don't
    duplicate behaviour:

      1. ``/api/ssh/verify-identity`` -- short-lived SSH that reads the
         remote hostname banner. Returns one of:
            ``ok`` (identity matches)
            ``auth_failed``        (paramiko AuthenticationException)
            ``port_closed``        (TCP 22 unreachable)
            ``ghost_ip``           (banner says a DIFFERENT hostname)
            ``identity_mismatch``  (synonym of ghost_ip, no auto-reap)
            ``generic_prompt``     (recovery / login -- ambiguous)
            ``timeout`` / ``error: <message>``
      2. ``/api/ssh/probe`` (only on identity OK) -- collects cluster
         identity (active NCC, KVM host, NCC VMs), per-node DNS map,
         and reachable connection methods. Result is folded back into
         ``operational.json`` via the same writer path the live
         monitor uses, so the next ``/api/devices/:id/context`` call
         already reflects this device's verified state.

    Body shape::

        {
          "host": "100.64.4.98",        # required (IP or hostname)
          "user": "dnroot",             # optional; default 'dnroot'
          "password": "...",            # optional; default 'dnroot'
          "discovery_depth":            # optional; "minimal"|"standard"|"full"
              "standard",               # default 'standard'
          "monitor_cadence":            # optional; "default"|"fast_initial"|"aggressive"
              "fast_initial",           # default 'fast_initial'
          "skip_probe": false           # optional debug knob
        }

    Returns::

        {
          "ok": bool,
          "reason": "ok" | "auth_failed" | "port_closed"
                    | "ghost_ip" | "identity_mismatch"
                    | "generic_prompt" | "timeout" | "error",
          "message": str,                  # human-readable summary
          "verified_at": iso8601 | "",
          "expected_hostname": str,
          "actual_hostname": str,
          "device_state": str,             # DNOS / GI / RECOVERY / unknown
          "is_cluster": bool,
          "active_ncc_vm": str,
          "active_ncc_host": str,
          "active_ncc_ip": str | None,
          "kvm_host": str,
          "kvm_host_ip": str,
          "ncc_vms": list,
          "monitor_policy": {              # what the backend is now using
              "cadence": str,
              "discovery_depth": str
          },
          "raw_verify": {...},             # full /api/ssh/verify-identity result
          "raw_probe": {...} | null,       # /api/ssh/probe result if run
        }

    Never raises 5xx for routine credential failures -- those return a
    structured ``{ok: false, reason: ...}`` so the dialog can render
    an inline error block. 5xx is reserved for "the bridge itself
    couldn't run the verification at all" (resolver bug, IO error,
    auth backend down, etc.).
    """
    from datetime import datetime, timezone

    body = body or {}
    raw_host = (body.get("host") or "").strip().split("/")[0]
    raw_user = (body.get("user") or "dnroot").strip() or "dnroot"
    raw_pass = body.get("password")
    if not raw_pass:
        raw_pass = "dnroot"
    discovery_depth = (body.get("discovery_depth") or "standard").strip().lower()
    if discovery_depth not in ("minimal", "standard", "full"):
        discovery_depth = "standard"
    monitor_cadence = (body.get("monitor_cadence") or "fast_initial").strip().lower()
    if monitor_cadence not in ("default", "fast_initial", "aggressive"):
        monitor_cadence = "fast_initial"
    skip_probe = bool(body.get("skip_probe"))

    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    if not raw_host:
        raise HTTPException(status_code=400, detail="host required")

    app_user = _get_request_user(request) if request else "default"
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # --- Step 1: identity verification --------------------------------
    is_ip = bool(re.match(r"^\d+\.\d+\.\d+\.\d+$", raw_host))
    raw_verify = None
    if is_ip:
        # Re-use the existing endpoint logic by calling it as a function;
        # we explicitly construct the body dict so the helper's own
        # validation runs. It NEVER raises on routine identity errors.
        try:
            from routes.ssh import verify_ssh_identity as _verify_fn
            raw_verify = _verify_fn(
                {
                    "device_id": device_id,
                    "ip": raw_host,
                    "user": raw_user,
                    "password": raw_pass,
                    "auto_reap": True,
                },
                request,
            )
        except HTTPException:
            raise
        except Exception as exc:
            return {
                "ok": False,
                "reason": "error",
                "message": f"verify-identity raised: {exc}",
                "verified_at": "",
                "expected_hostname": device_id,
                "actual_hostname": "",
                "device_state": "unknown",
                "is_cluster": False,
                "active_ncc_vm": "",
                "active_ncc_host": "",
                "active_ncc_ip": None,
                "kvm_host": "",
                "kvm_host_ip": "",
                "ncc_vms": [],
                "monitor_policy": {
                    "cadence": monitor_cadence,
                    "discovery_depth": discovery_depth,
                },
                "raw_verify": None,
                "raw_probe": None,
            }
    else:
        # Hostname target -- the verify-identity endpoint is IP-only by
        # design (it parses IPs strictly). For hostnames we fall back to
        # the credential test which uses DNOSSession (resolves hostname
        # internally and tries the lab credential chain). The result is
        # less rich (no banner hostname capture) but still tells us
        # whether dnroot/dnroot is accepted.
        try:
            from scaler.dnos_session import DNOSSession
            with DNOSSession(raw_host, raw_user, raw_pass,
                             connect_timeout=8) as sess:
                if not sess.is_alive():
                    raise RuntimeError("session_not_alive")
            raw_verify = {
                "reachable": True,
                "identity_verified": True,
                "actual_hostname": "",
                "expected_hostname": device_id,
                "ip": raw_host,
                "port": 22,
                "reason": "hostname_target_no_banner",
            }
        except Exception as exc:
            err_low = str(exc).lower()
            if "auth" in err_low or "denied" in err_low or "password" in err_low:
                _reason = "auth_failed"
            elif "timeout" in err_low or "timed out" in err_low:
                _reason = "timeout"
            elif "name or service" in err_low or "resolve" in err_low:
                _reason = "port_closed"
            else:
                _reason = "error"
            raw_verify = {
                "reachable": False,
                "identity_verified": False,
                "actual_hostname": "",
                "expected_hostname": device_id,
                "ip": raw_host,
                "port": 22,
                "reason": _reason,
                "error": str(exc),
            }

    verify_reason = (raw_verify or {}).get("reason") or ""
    identity_ok = bool((raw_verify or {}).get("identity_verified"))

    # Map verify reasons to our public reason codes.
    if identity_ok:
        public_reason = "ok"
    elif verify_reason == "auth_failed":
        public_reason = "auth_failed"
    elif verify_reason == "port_closed":
        public_reason = "port_closed"
    elif verify_reason == "ghost_ip":
        public_reason = "ghost_ip"
    elif verify_reason == "generic_prompt":
        public_reason = "generic_prompt"
    elif verify_reason == "timeout":
        public_reason = "timeout"
    elif verify_reason == "hostname_target_no_banner" and (raw_verify or {}).get("reachable"):
        public_reason = "ok"
        identity_ok = True
    else:
        public_reason = "error"

    # --- Step 2: probe (only if identity OK and discovery wants it) ---
    raw_probe = None
    if identity_ok and not skip_probe and discovery_depth in ("standard", "full"):
        try:
            from routes.ssh import probe_connection as _probe_fn
            raw_probe = _probe_fn(
                {"device_id": device_id, "ssh_host": raw_host},
                request,
            )
        except HTTPException:
            # Probe failure is non-fatal; we just won't have cluster
            # identity. The caller still gets a verified=true response
            # with whatever the verify step captured.
            raw_probe = None
        except Exception:
            raw_probe = None

    cluster = (raw_probe or {}).get("cluster") or {}
    is_cluster = bool(cluster.get("is_cluster"))
    active_ncc_vm = (cluster.get("active_ncc_vm") or "").strip()
    active_ncc_host = (cluster.get("active_ncc_host") or "").strip()
    active_ncc_ip = cluster.get("active_ncc_ip")
    kvm_host = (cluster.get("kvm_host") or "").strip()
    kvm_host_ip = (cluster.get("kvm_host") or "").strip() if re.match(
        r"^\d+\.\d+\.\d+\.\d+$", cluster.get("kvm_host") or "") else ""
    ncc_vms = list(cluster.get("ncc_vms") or [])
    device_state = ((raw_probe or {}).get("device_state") or "unknown").upper()

    # --- Step 3: persist verification + monitor policy ----------------
    if identity_ok:
        try:
            from routes._ops_writer import update_ops as _update_ops
            ops_path = Path(SCALER_ROOT) / "db" / "configs" / device_id / "operational.json"
            ops_path.parent.mkdir(parents=True, exist_ok=True)

            def _mut_verify(ops):
                ops["credentials_verified_at"] = now_iso
                ops["credentials_verified_by"] = app_user
                ops["credentials_verified_host"] = raw_host
                ops["credentials_verified_user"] = raw_user
                ops["monitor_policy"] = {
                    "cadence": monitor_cadence,
                    "discovery_depth": discovery_depth,
                    "set_at": now_iso,
                    "set_by": app_user,
                }
                if device_state and device_state != "UNKNOWN":
                    ops["device_state"] = device_state
                return ops

            _update_ops(ops_path, _mut_verify, create_if_missing=True)
        except Exception:
            pass

    # --- Step 4: build human-readable message -------------------------
    if identity_ok:
        if is_cluster and active_ncc_vm:
            message = (f"Verified -- {device_state} cluster, active NCC = "
                       f"{active_ncc_vm}. Monitoring with {monitor_cadence}.")
        elif device_state and device_state != "UNKNOWN":
            message = (f"Verified -- {device_state}. Monitoring with "
                       f"{monitor_cadence}.")
        else:
            message = "Verified."
    elif public_reason == "auth_failed":
        message = (f"Authentication failed for {raw_user}@{raw_host}. "
                   f"Check the password or use a different credential "
                   f"profile.")
    elif public_reason == "port_closed":
        message = (f"{raw_host}:22 is unreachable. Verify the IP / hostname "
                   f"and that the device is powered on and on the lab VPN.")
    elif public_reason == "ghost_ip":
        actual = (raw_verify or {}).get("actual_hostname") or "?"
        message = (f"Ghost IP -- {raw_host} now answers as '{actual}', "
                   f"not '{device_id}'. The stale record was reaped; "
                   f"point the device at its new IP or override.")
    elif public_reason == "generic_prompt":
        message = (f"{raw_host} answered with an ambiguous (login / "
                   f"recovery) prompt. The device may be in BASEOS / "
                   f"GI / RECOVERY mode -- save anyway if expected.")
    elif public_reason == "timeout":
        message = f"{raw_host} did not respond within the timeout."
    else:
        message = (f"Verification could not complete: "
                   f"{(raw_verify or {}).get('error') or verify_reason or 'unknown'}")

    return {
        "ok": identity_ok,
        "reason": public_reason,
        "message": message,
        "verified_at": now_iso if identity_ok else "",
        "expected_hostname": (raw_verify or {}).get("expected_hostname") or device_id,
        "actual_hostname": (raw_verify or {}).get("actual_hostname") or "",
        "device_state": device_state,
        "is_cluster": is_cluster,
        "active_ncc_vm": active_ncc_vm,
        "active_ncc_host": active_ncc_host,
        "active_ncc_ip": active_ncc_ip,
        "kvm_host": kvm_host,
        "kvm_host_ip": kvm_host_ip or kvm_host,
        "ncc_vms": ncc_vms,
        "monitor_policy": {
            "cadence": monitor_cadence,
            "discovery_depth": discovery_depth,
        },
        "raw_verify": raw_verify,
        "raw_probe": raw_probe,
    }


@router.post("/api/devices/discover")
def discover_device(body: dict = None):
    """SSH to device by IP, discover hostname, add to device_inventory.json.

    Credential resolution:
      - If the request body explicitly supplies user/password, use ONLY those
        (no fallback chain -- the user is asserting they know the right creds).
      - Otherwise, build a credential chain via `_get_lab_credential_chain()`
        based on the optional hint hostname/label, and try each profile in
        order. This is what fixes "API discovery fails on some devices":
        a DNAAS LEAF won't accept dnroot/dnroot, but the chain will fall
        back to sisaev/Drive1234! after the first auth failure -- without
        the user having to know which credential set the device wants.
    """
    body = body or {}
    ip = (body.get("ip") or "").strip()
    if not ip:
        raise HTTPException(status_code=400, detail="ip required")

    explicit_user = (body.get("user") or "").strip()
    explicit_password = body.get("password") or ""
    hint_label = (body.get("label") or body.get("hostname") or "").strip()

    if explicit_user and explicit_password:
        chain = [("explicit", explicit_user, explicit_password)]
    else:
        chain = _get_lab_credential_chain(device_id=ip, hostname=hint_label)
        if not chain:
            chain = [("dut", "dnroot", "dnroot")]

    from scaler.models import Device
    from scaler.config_extractor import InteractiveExtractor

    config_dir = Path(SCALER_ROOT) / "db" / "configs" / ip
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "operational.json").write_text(json.dumps({"mgmt_ip": ip}, indent=2))

    last_error = None
    tried = []
    for profile_name, user, password in chain:
        tried.append({"profile": profile_name, "user": user})
        try:
            device = Device(
                id=ip,
                hostname=ip,
                ip=ip,
                username=user,
                password=Device.encode_password(password),
            )
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
                "credential_profile": profile_name,
            }
            INVENTORY_FILE.write_text(json.dumps(inv, indent=2))
            return {
                "status": "ok",
                "hostname": hostname,
                "ip": ip,
                "key": key,
                "credential_profile": profile_name,
                "credentials_tried": tried,
            }
        except Exception as e:
            last_error = str(e)
            # Retry with the next profile only on auth/connection failures.
            # Don't waste cycles on "no route to host"-style errors.
            err_low = last_error.lower()
            transient = ("auth" in err_low or "permission" in err_low or
                         "password" in err_low or "denied" in err_low)
            if not transient:
                break
            continue

    raise HTTPException(
        status_code=503,
        detail=f"SSH discovery failed for {ip} after trying "
               f"{len(tried)} credential profile(s): {last_error}",
    )

