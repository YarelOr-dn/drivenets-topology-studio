"""Auto-monitor reference-counted device endpoints (Phase 2 MVP).

Companion design doc: ``topology/docs/AUTO_MONITOR_ON_ATTACH.md``.

Five HTTP endpoints, all behind the bridge's JWT middleware:

* ``POST /api/devices/verify-and-register``  -- the killer MVP endpoint.
  Verifies SSH credentials AND, on success, upserts the shared
  registry, attaches a per-user reference, mirrors the device into the
  curated SCALER ``devices.json``, and best-effort registers with the
  Network Mapper MCP. Returns a superset of the existing
  ``verify-credentials`` response so the frontend can keep its existing
  result-handling code unchanged while picking up the new fields
  (``key``, ``newly_registered``, ``monitor_started_subsystems``,
  ``references_count_total``, ``references_user_count``).

* ``GET /api/devices/monitored``       -- list THIS user's references +
  the (deduped) shared device records they cover. Used for the canvas
  smooth-ZTP hydrate so toolbars don't briefly flash truncated.

* ``GET /api/devices/monitored/{ip}``  -- single record + per-user
  reference state. Useful for the canvas detail tooltip and the
  detach modal's pre-flight ("you and 2 others are watching this").

* ``POST /api/devices/monitored/{ip}/attach``    -- idempotent reference
  create. Returns ``{ already_attached: bool, ... }``.

* ``DELETE /api/devices/monitored/{ip}/attach``  -- detach. Response
  includes ``would_stop_monitoring`` so the frontend knows whether to
  show the "Stop monitoring this device?" modal.

Multi-user safety
-----------------

Every handler resolves the caller's username via ``_get_request_user``
(set by the bridge's JWT middleware) and uses it as the ONLY scoping
key. The shared registry record is visible to every authenticated user
(it's deliberately one-record-per-device for cache efficiency), but
references are strictly per-user: user A's detach removes only user
A's row from ``references_tbl``, never user B's, and the
last-referencer-detected response only flips ``would_stop_monitoring``
to true when user A's removal brings ``references_count_total`` to 0.

Phase 4+ extensions (deferred OQ-1, OQ-4, OQ-5) -- topology-scope
references, auto-detach on canvas remove, sub-IF-level fan-out -- will
ride on the same DAL without needing schema changes (the
``scope_type`` / ``scope_id`` columns were sized for that future).
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Request

from api import monitored_registry as reg
try:
    from api.auth.user_store import user_store
except Exception:  # pragma: no cover - auth package may be absent in legacy dev mode
    user_store = None
from routes._state import _get_request_user
from routes import monitored_dispatch
from routes.devices import verify_credentials_inline


logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_IP_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")


def _require_user(request: Request) -> str:
    """Resolve and validate the caller's username.

    The bridge JWT middleware sets ``request.state.user`` to the JWT's
    ``sub`` claim. For tests / single-user dev mode the middleware
    falls back to ``"default"``. Production deployments always have
    JWT enabled (multi-user) so the cap on this helper is only
    sanity / defense-in-depth -- if the middleware was somehow
    bypassed and ``user`` is empty, raise 401 instead of silently
    attributing actions to ``"default"``.
    """
    user = _get_request_user(request) if request else ""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def _require_engineer(request: Request) -> str:
    """Require an authenticated caller with a mutating-device role.

    The JWT middleware has already validated the token and stamped the
    username. We still check the canonical user store so viewer tokens cannot
    register or detach backend device records.
    """
    user = _require_user(request)
    if user_store and user != "default":
        try:
            if not user_store.has_role_or_higher(user, "engineer"):
                raise HTTPException(status_code=403, detail="Engineer role required")
        except HTTPException:
            raise
        except Exception:
            role = (getattr(getattr(request, "state", None), "role", "") or "").strip().lower()
            if role not in ("engineer", "team_leader", "manager", "admin"):
                raise HTTPException(status_code=403, detail="Engineer role required")
    return user


def _redact_users(ref_summary: Dict[str, Any], requester: str) -> Dict[str, Any]:
    """Hide other users' usernames from the caller.

    The total reference count is exposed (so the UI can render
    "watched by you + 2 others"), but other usernames are redacted.
    Admin users would see the full list -- not implemented in MVP.
    """
    out = {
        "key": ref_summary.get("key", ""),
        "total": int(ref_summary.get("total") or 0),
        "user_count": 0,
        "scopes_for_caller": [],
    }
    for r in ref_summary.get("users") or []:
        if (r.get("username") or "").strip() == requester:
            out["user_count"] += 1
            out["scopes_for_caller"].append({
                "scope_type": r.get("scope_type"),
                "scope_id": r.get("scope_id"),
                "attached_at": r.get("attached_at"),
            })
    return out


def _normalize_scope(body: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """Extract / sanitize the optional scope fields from a request body.

    Defaults to ``scope_type='topology'`` + ``scope_id=''`` (the
    "device is on at least one of my topologies" reference). Phase 4
    will populate ``scope_id`` with the topology UUID so leaving the
    canvas can clean up automatically.
    """
    body = body or {}
    scope_type = (body.get("scope_type") or "topology").strip() or "topology"
    scope_id = (body.get("scope_id") or "").strip()
    if scope_type not in ("topology", "canvas", "global"):
        scope_type = "topology"
    return {"scope_type": scope_type, "scope_id": scope_id}


def _onboarding_context(record: Dict[str, Any],
                        dispatch_results: List[Dict[str, Any]],
                        *,
                        user_count: int = 0,
                        total_count: int = 0) -> Dict[str, Any]:
    """Return the canonical post-onboarding shape consumed by toolbars.

    The canonical identity remains DB-derived. Identity-bound metadata is
    attached separately under ``validated_metadata`` after a backend live
    context fetch proves it still belongs to this verified device.
    """
    subsystems = []
    for item in dispatch_results or []:
        if not isinstance(item, dict):
            continue
        name = item.get("subsystem") or item.get("name") or ""
        if not name:
            continue
        status = item.get("status")
        if not status:
            status = "ok" if item.get("ok") is True or item.get("skipped") is True else "failed"
        subsystems.append({
            "subsystem": name,
            "status": status,
            "detail": item.get("detail") or item.get("message") or "",
        })

    canonical = {
        "key": record.get("key") or "",
        "device_id": record.get("hostname") or "",
        "hostname": record.get("hostname") or "",
        "management_ip": record.get("management_ip") or "",
        "serial_number": record.get("serial_number") or "",
        "platform": record.get("platform") or "",
        "is_cluster": bool(record.get("is_cluster")),
        "cluster_ncc_ips": record.get("cluster_ncc_ips") or [],
    }
    capabilities = {
        "ssh": True,
        "device_context": True,
        "monitoring": True,
        "lldp": True,
        "link_details": True,
        "xray": True,
        "health": True,
        "system_stack": True,
    }
    monitoring_options = {
        "state": "ready",
        "phase": "api_ready",
        "subsystems": subsystems,
        "user_reference_count": int(user_count or 0),
        "total_reference_count": int(total_count or 0),
    }
    return {
        "canonical": canonical,
        "capabilities": capabilities,
        "monitoring_options": monitoring_options,
        "identity": canonical,
    }


def _norm_identity(value: Any) -> str:
    return str(value or "").strip().lower()


def _is_ip(value: Any) -> bool:
    return bool(_IP_RE.match(str(value or "").strip()))


def _fetch_live_onboarding_context(device_id: str, host: str, user: str,
                                   identity_guard: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Fetch the live backend context used as onboarding metadata truth.

    Split into a wrapper so unit tests can monkey-patch it without touching
    the heavier scaler bridge helpers.
    """
    from routes.bridge_helpers import _get_device_context

    return _get_device_context(
        device_id,
        live=True,
        ssh_host=host,
        app_user=user,
        bypass_cache=True,
        identity_guard=identity_guard or {},
    )


def _build_metadata_unknown(source_identity: Dict[str, Any],
                            status: str,
                            reason: str,
                            fetched_at: str = "") -> Dict[str, Any]:
    return {
        "status": status,
        "reliable": False,
        "reason": reason,
        "fetched_at": fetched_at,
        "source": "backend-onboarding",
        "source_identity": source_identity,
        "context": {},
        "lldp": [],
        "stack": [],
        "git_commit": None,
        "device_state": "unknown",
        "stamps": {},
    }


def _validate_live_context_identity(ctx: Dict[str, Any],
                                    source_identity: Dict[str, Any]) -> List[str]:
    """Return identity conflicts between verified onboarding and live context."""
    conflicts: List[str] = []
    identity = ctx.get("identity") or {}
    requested_host = source_identity.get("requested_host") or ""
    requested_device_id = source_identity.get("requested_device_id") or ""
    registry_ip = source_identity.get("registry_management_ip") or ""
    registry_hostname = source_identity.get("registry_hostname") or ""
    registry_serial = source_identity.get("registry_serial_number") or ""
    verified_hostname = source_identity.get("verified_hostname") or ""
    generated_request = bool(re.match(r"^(ncp|ncp\d+|s|s\d+)$", _norm_identity(requested_device_id)))

    ctx_ip = (
        ctx.get("resolved_ip")
        or ctx.get("mgmt_ip")
        or ctx.get("ip")
        or identity.get("mgmt_ip")
        or ""
    )
    ctx_serial = identity.get("serial") or ctx.get("serial_number") or ctx.get("serial") or ""
    ctx_names = {
        _norm_identity(identity.get("config_hostname")),
        _norm_identity(ctx.get("hostname")),
        _norm_identity(ctx.get("device_id")),
        *[_norm_identity(v) for v in (identity.get("scaler_ids") or [])],
        *[_norm_identity(v) for v in (identity.get("inventory_keys") or [])],
    }
    ctx_names.discard("")
    expected_names = {
        _norm_identity(requested_device_id),
        _norm_identity(registry_hostname),
        _norm_identity(verified_hostname),
    }
    expected_names.discard("")

    for conflict in ctx.get("cache_owner_conflicts") or []:
        if not isinstance(conflict, dict):
            continue
        owner = conflict.get("owner") or conflict.get("hostname") or "unknown"
        conflicts.append(f"cache owner {owner} did not match verified onboarding identity")

    if _is_ip(requested_host) and ctx_ip and _norm_identity(ctx_ip) != _norm_identity(requested_host):
        conflicts.append(f"live context resolved IP {ctx_ip}, requested host was {requested_host}")
    if registry_ip and ctx_ip and _norm_identity(ctx_ip) != _norm_identity(registry_ip):
        conflicts.append(f"live context resolved IP {ctx_ip}, registry IP is {registry_ip}")

    if not _is_ip(requested_host):
        requested_key = _norm_identity(requested_host)
        serial_or_name_matches = (
            not requested_key
            or requested_key == _norm_identity(ctx_serial)
            or requested_key in ctx_names
            or requested_key == _norm_identity(registry_serial)
            or requested_key == _norm_identity(registry_hostname)
        )
        if ctx_serial and requested_key and not serial_or_name_matches:
            conflicts.append(f"live context serial {ctx_serial}, requested identity was {requested_host}")

    if ctx_names and expected_names and not (ctx_names & expected_names):
        # A generated canvas label (NCP-1/S1) is intentionally weak; do not
        # conflict on names alone when the verified host/IP already matched.
        if not generated_request:
            conflicts.append(
                "live context names "
                + ", ".join(sorted(ctx_names))
                + " do not match verified identity "
                + ", ".join(sorted(expected_names))
            )

    if generated_request and bool(ctx.get("lldp") or ctx.get("stack") or ctx.get("git_commit")):
        strong_match = bool(
            (ctx_serial and registry_serial and _norm_identity(ctx_serial) == _norm_identity(registry_serial))
            or (verified_hostname and _norm_identity(verified_hostname) in ctx_names)
            or (registry_hostname and _norm_identity(registry_hostname) in ctx_names)
        )
        if not strong_match:
            conflicts.append(
                "generated canvas label requires serial or hostname match before trusting cached metadata"
            )

    return conflicts


def _backend_validated_metadata(record: Dict[str, Any],
                                verify_result: Dict[str, Any],
                                body: Dict[str, Any],
                                user: str) -> Dict[str, Any]:
    """Fetch and validate identity-bound LLDP/stack/git metadata for onboarding."""
    import time

    source_identity = {
        "requested_device_id": (body.get("device_id") or "").strip(),
        "requested_host": (body.get("host") or "").strip().split("/")[0],
        "verified_hostname": verify_result.get("actual_hostname") or "",
        "verified_serial": (
            (verify_result.get("raw_probe") or {}).get("serial")
            if isinstance(verify_result.get("raw_probe"), dict) else ""
        ) or (
            (verify_result.get("raw_verify") or {}).get("serial")
            if isinstance(verify_result.get("raw_verify"), dict) else ""
        ) or "",
        "registry_key": record.get("key") or "",
        "registry_hostname": record.get("hostname") or "",
        "registry_management_ip": record.get("management_ip") or "",
        "registry_serial_number": record.get("serial_number") or "",
        "cluster_ncc_ips": record.get("cluster_ncc_ips") or [],
    }
    fetched_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    try:
        ctx = _fetch_live_onboarding_context(
            record.get("hostname") or source_identity["requested_device_id"],
            record.get("management_ip") or source_identity["requested_host"],
            user,
            source_identity,
        )
    except Exception as exc:
        return _build_metadata_unknown(
            source_identity,
            "unknown",
            f"backend live metadata fetch failed: {exc}",
            fetched_at,
        )

    if not isinstance(ctx, dict):
        return _build_metadata_unknown(source_identity, "unknown", "backend live metadata returned non-dict", fetched_at)

    conflicts = _validate_live_context_identity(ctx, source_identity)
    if conflicts:
        out = _build_metadata_unknown(source_identity, "conflict", "; ".join(conflicts), fetched_at)
        out["context"] = {
            "identity": ctx.get("identity") or {},
            "resolved_ip": ctx.get("resolved_ip") or ctx.get("mgmt_ip") or ctx.get("ip") or "",
            "timestamp": ctx.get("timestamp") or "",
        }
        return out

    lldp = ctx.get("lldp") or ctx.get("lldp_neighbors") or []
    stack = ctx.get("stack") or []
    git_commit = ctx.get("git_commit")
    device_state = ctx.get("device_state") or "unknown"
    has_metadata = bool(lldp or stack or git_commit or (device_state and str(device_state).lower() != "unknown"))
    if not has_metadata:
        return _build_metadata_unknown(
            source_identity,
            "unknown",
            "backend live metadata returned no LLDP, stack, git, or mode evidence",
            fetched_at,
        )

    stamps = {
        "lldp": {
            "status": "ready",
            "source": "backend-onboarding",
            "fetched_at": fetched_at,
            "identity": source_identity,
        },
        "stack": {
            "status": "ready",
            "source": "backend-onboarding",
            "fetched_at": ctx.get("stack_fetched_at") or fetched_at,
            "identity": source_identity,
        },
        "git": {
            "status": "ready",
            "source": "backend-onboarding",
            "fetched_at": ctx.get("git_commit_fetched_at") or fetched_at,
            "identity": source_identity,
        },
    }
    return {
        "status": "reliable",
        "reliable": True,
        "reason": "",
        "fetched_at": fetched_at,
        "source": "backend-onboarding",
        "source_identity": source_identity,
        "context": ctx,
        "lldp": lldp,
        "stack": stack,
        "git_commit": git_commit,
        "device_state": device_state,
        "stack_fetched_at": ctx.get("stack_fetched_at") or "",
        "git_commit_fetched_at": ctx.get("git_commit_fetched_at") or "",
        "stamps": stamps,
    }


# ---------------------------------------------------------------------------
# POST /api/devices/verify-and-register
# ---------------------------------------------------------------------------

@router.post("/api/devices/verify-and-register")
def verify_and_register(body: Optional[dict] = Body(default=None),
                        request: Request = None):
    """Verify SSH credentials AND register the device in the shared
    monitor registry.

    Body shape::

        {
          "device_id": "PE-1",            # required (canonical id / hostname)
          "host": "100.64.4.200",         # required (mgmt IP, accepted as host)
          "user": "dnroot",               # optional; default 'dnroot'
          "password": "...",              # optional; default 'dnroot'
          "discovery_depth": "standard",  # optional
          "monitor_cadence": "fast_initial", # optional
          "scope_type": "topology",       # optional
          "scope_id": ""                  # optional
        }

    Behaviour::

        1. Calls ``verify_credentials_inline`` (exact same SSH path as
           ``/api/devices/{id}/verify-credentials``).
        2. If verify fails (auth_failed / port_closed / ghost_ip /
           timeout / etc.) -- returns the verify result UNCHANGED with
           an extra ``registered: false`` flag. Multi-user rule: a
           failed verify must NEVER add a row to the shared registry.
        3. On verify success:
              a. ``upsert_device`` (idempotent, merges fields).
              b. ``add_reference`` for the caller (idempotent).
              c. ``monitored_dispatch.bring_up`` (mirror + Network
                 Mapper + log other subsystems).
              d. Records ``registered: true``, ``key``,
                 ``newly_registered``, ``monitor_started_subsystems``,
                 ``references_count_total``, and the verify body fields
                 the dialog already consumes.

    The response is intentionally a SUPERSET of verify-credentials so the
    SSH dialog's existing happy-path code keeps working. The new fields
    are inert if the frontend ignores them.

    Hard "do nots":
      * Never silently retry verify on failure (per
        ``known-dnos-bugs.mdc``). The caller surfaces the verify reason.
      * Never log or echo the password.
      * Never write to the registry on a verify-failure path.
    """
    body = body or {}
    user = _require_engineer(request)

    device_id = (body.get("device_id") or "").strip()
    host = (body.get("host") or "").strip().split("/")[0]
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    if not host:
        raise HTTPException(status_code=400, detail="host required")

    scope = _normalize_scope(body)

    # -- Phase A: verify (reuses the live, proven SSH path) ----------
    verify_result = verify_credentials_inline(
        device_id,
        {
            "host": host,
            "user": body.get("user"),
            "password": body.get("password"),
            "discovery_depth": body.get("discovery_depth"),
            "monitor_cadence": body.get("monitor_cadence"),
        },
        user,
    )
    if not isinstance(verify_result, dict):
        verify_result = {"ok": False, "reason": "error", "message": "verify returned non-dict"}

    if not verify_result.get("ok"):
        # No registration on a failed verify. Surface the verify result
        # verbatim so the dialog can render its smart-by-reason actions.
        out = dict(verify_result)
        out.setdefault("registered", False)
        out.setdefault("monitor_started_subsystems", [])
        out.setdefault("key", "")
        out.setdefault("references_count_total", 0)
        out.setdefault("references_user_count", 0)
        out.setdefault("newly_registered", False)
        return out

    # -- Phase B: registry upsert ------------------------------------
    raw_verify = verify_result.get("raw_verify") or {}
    raw_probe = verify_result.get("raw_probe") or {}
    actual_hostname = (
        verify_result.get("actual_hostname")
        or (raw_verify.get("actual_hostname") if isinstance(raw_verify, dict) else None)
        or device_id
    )
    cluster = (raw_probe.get("cluster") or {}) if isinstance(raw_probe, dict) else {}
    serial = (
        (raw_probe.get("serial") if isinstance(raw_probe, dict) else None)
        or (raw_verify.get("serial") if isinstance(raw_verify, dict) else None)
        or ""
    )
    platform = (
        (raw_probe.get("platform") if isinstance(raw_probe, dict) else None)
        or (raw_verify.get("platform") if isinstance(raw_verify, dict) else None)
        or ""
    )
    is_cluster = bool(verify_result.get("is_cluster") or cluster.get("is_cluster"))
    cluster_ncc_ips: List[str] = []
    if is_cluster:
        for vm in cluster.get("ncc_vms") or []:
            ip = (vm or {}).get("ip") if isinstance(vm, dict) else None
            if ip and ip not in cluster_ncc_ips:
                cluster_ncc_ips.append(ip)
        active_ip = verify_result.get("active_ncc_ip")
        if active_ip and active_ip not in cluster_ncc_ips:
            cluster_ncc_ips.append(active_ip)

    record = reg.upsert_device(
        management_ip=host,
        serial_number=str(serial or ""),
        hostname=str(actual_hostname or device_id),
        platform=str(platform or ""),
        is_cluster=is_cluster,
        cluster_ncc_ips=cluster_ncc_ips,
        actor=user,
    )
    newly_registered = bool(record.get("newly_inserted"))

    # -- Phase C: per-user reference --------------------------------
    ref = reg.add_reference(
        key=record["key"],
        username=user,
        scope_type=scope["scope_type"],
        scope_id=scope["scope_id"],
    )

    # -- Phase D: subsystem dispatch (best-effort) ------------------
    dispatch_results = monitored_dispatch.bring_up(record)

    # -- Phase E: assemble response (SUPERSET of verify-credentials)
    summary = reg.reference_summary(record["key"])
    redacted = _redact_users(summary, user)
    onboarding_ctx = _onboarding_context(
        record,
        dispatch_results,
        user_count=redacted["user_count"],
        total_count=redacted["total"],
    )
    onboarding_metadata = _backend_validated_metadata(record, verify_result, body, user)
    onboarding_ctx["validated_metadata"] = onboarding_metadata

    out = dict(verify_result)
    out.update({
        "registered": True,
        "key": record["key"],
        "registered_device_id": record.get("hostname") or actual_hostname,
        "management_ip": record.get("management_ip") or host,
        "serial_number": record.get("serial_number") or serial,
        "hostname": record.get("hostname") or actual_hostname,
        "platform": record.get("platform") or platform,
        "is_cluster": is_cluster,
        "cluster_ncc_ips": record.get("cluster_ncc_ips") or cluster_ncc_ips,
        "newly_registered": newly_registered,
        "newly_attached_for_user": ref["newly_attached"],
        "monitor_started_subsystems": dispatch_results,
        "references_count_total": redacted["total"],
        "references_user_count": redacted["user_count"],
        "scope_type": ref["scope_type"],
        "scope_id": ref["scope_id"],
        "onboarding_phase": "api_ready",
        "device_context": onboarding_ctx,
        "onboarding_metadata": onboarding_metadata,
        "metadata_validation": {
            "status": onboarding_metadata.get("status"),
            "reliable": bool(onboarding_metadata.get("reliable")),
            "reason": onboarding_metadata.get("reason") or "",
            "source": onboarding_metadata.get("source") or "backend-onboarding",
            "fetched_at": onboarding_metadata.get("fetched_at") or "",
        },
        "capabilities": onboarding_ctx["capabilities"],
        "monitoring_options": onboarding_ctx["monitoring_options"],
    })
    return out


# ---------------------------------------------------------------------------
# GET /api/devices/monitored
# ---------------------------------------------------------------------------

@router.get("/api/devices/monitored")
def list_monitored(request: Request = None):
    """List devices the caller has a reference for.

    Each entry is the SHARED device record + a per-user
    ``references_user_count`` field. The shared ``last_seen_ok`` is
    exposed so the frontend smooth-ZTP hydrate can stamp
    ``device._sshReachable=true`` for the canvas card before the first
    toolbar paint.

    Response::

        {
          "devices": [
            {
              "key": "100.64.4.200|<sn>",
              "management_ip": "100.64.4.200",
              "hostname": "PE-1",
              "platform": "NCP",
              "is_cluster": true,
              "cluster_ncc_ips": [...],
              "last_seen_ok": "2026-05-05T12:34:56+00:00",
              "legacy_global": false,
              "references_user_count": 1,
              "references_count_total": 3
            },
            ...
          ],
          "count": <int>
        }
    """
    user = _require_engineer(request)
    devices = reg.list_devices(only_user=user)
    out: List[Dict[str, Any]] = []
    for d in devices:
        summary = reg.reference_summary(d["key"])
        redacted = _redact_users(summary, user)
        d_out = dict(d)
        d_out.pop("cluster_ncc_ips_json", None)
        d_out["references_user_count"] = redacted["user_count"]
        d_out["references_count_total"] = redacted["total"]
        out.append(d_out)
    return {"devices": out, "count": len(out)}


# ---------------------------------------------------------------------------
# GET /api/devices/monitored/{ip}
# ---------------------------------------------------------------------------

@router.get("/api/devices/monitored/{ip}")
def get_monitored(ip: str, request: Request = None):
    """Single-device monitored record + per-user reference state.

    The path parameter ``ip`` is matched against ``management_ip`` AND
    against ``cluster_ncc_ips_json`` membership (chassis IP keying per
    OQ-3) so a per-NCC IP also resolves to the chassis row.

    Returns 404 when the device is not in the registry. Returns
    403-equivalent JSON ``{ ok: false, reason: 'no_user_reference' }``
    when the caller has never attached a reference -- by design,
    user A should not see whether user B is monitoring something.
    """
    user = _require_engineer(request)
    ip = (ip or "").strip()
    if not ip:
        raise HTTPException(status_code=400, detail="ip required")
    record = reg.find_by_ip(ip)
    if not record:
        raise HTTPException(status_code=404, detail=f"no monitored device for {ip}")
    summary = reg.reference_summary(record["key"])
    redacted = _redact_users(summary, user)
    if redacted["user_count"] == 0 and not record.get("legacy_global"):
        # Don't leak existence of devices the caller hasn't attached to.
        # Legacy globals are an exception -- everyone is implicitly
        # attached to PE-1 / PE-4 / DNAAS-* baselines.
        raise HTTPException(status_code=404, detail=f"no monitored device for {ip}")
    record_out = dict(record)
    record_out.pop("cluster_ncc_ips_json", None)
    record_out["references_user_count"] = redacted["user_count"]
    record_out["references_count_total"] = redacted["total"]
    record_out["scopes_for_caller"] = redacted["scopes_for_caller"]
    record_out["subsystems"] = reg.list_subsystem_status(record["key"])
    return record_out


# ---------------------------------------------------------------------------
# POST /api/devices/monitored/{ip}/attach
# ---------------------------------------------------------------------------

@router.post("/api/devices/monitored/{ip}/attach")
def attach_reference(ip: str, body: Optional[dict] = Body(default=None),
                     request: Request = None):
    """Idempotent attach for the caller.

    Returns the freshly resolved registry state so the frontend can
    update its tooltip + toolbar without a follow-up GET. If the
    device is not in the registry yet, returns 404 -- callers should
    use ``/verify-and-register`` for the cold-start path.
    """
    user = _require_user(request)
    ip = (ip or "").strip()
    if not ip:
        raise HTTPException(status_code=400, detail="ip required")
    record = reg.find_by_ip(ip)
    if not record:
        raise HTTPException(status_code=404, detail=f"no monitored device for {ip}")
    scope = _normalize_scope(body)
    ref = reg.add_reference(
        key=record["key"],
        username=user,
        scope_type=scope["scope_type"],
        scope_id=scope["scope_id"],
    )
    summary = reg.reference_summary(record["key"])
    redacted = _redact_users(summary, user)
    return {
        "ok": True,
        "key": record["key"],
        "ip": record["management_ip"],
        "hostname": record["hostname"],
        "newly_attached": ref["newly_attached"],
        "scope_type": ref["scope_type"],
        "scope_id": ref["scope_id"],
        "references_user_count": redacted["user_count"],
        "references_count_total": redacted["total"],
    }


# ---------------------------------------------------------------------------
# DELETE /api/devices/monitored/{ip}/attach
# ---------------------------------------------------------------------------

@router.delete("/api/devices/monitored/{ip}/attach")
def detach_reference(ip: str, request: Request = None,
                     scope_type: str = "topology", scope_id: str = ""):
    """Remove the caller's reference.

    Query parameters mirror the body of attach so DELETE callers don't
    need a body (most fetch / urllib clients don't send DELETE bodies).
    Response::

        {
          "ok": true,
          "key": "...",
          "removed": bool,
          "references_user_count": int,
          "references_count_total": int,
          "is_last_reference": bool,
          "would_stop_monitoring": bool,
          "torn_down_subsystems": [{...}, ...]   # only when teardown ran
        }

    The frontend uses ``would_stop_monitoring`` to decide whether to
    show the "Stop monitoring this device?" modal. When tear_down
    runs (same call, atomic from the caller's POV), the per-subsystem
    results are returned.
    """
    user = _require_user(request)
    ip = (ip or "").strip()
    if not ip:
        raise HTTPException(status_code=400, detail="ip required")
    record = reg.find_by_ip(ip)
    if not record:
        raise HTTPException(status_code=404, detail=f"no monitored device for {ip}")
    scope_type_clean = (scope_type or "topology").strip() or "topology"
    scope_id_clean = (scope_id or "").strip()
    if scope_type_clean not in ("topology", "canvas", "global"):
        scope_type_clean = "topology"

    res = reg.remove_reference(
        key=record["key"],
        username=user,
        scope_type=scope_type_clean,
        scope_id=scope_id_clean,
    )
    out = dict(res)
    out.setdefault("ok", True)

    # Only run teardown when the LAST reference is now gone AND the
    # device is not legacy_global. The DAL already factors the legacy
    # check into ``would_stop_monitoring``.
    if res.get("would_stop_monitoring"):
        try:
            torn = monitored_dispatch.tear_down(record)
            out["torn_down_subsystems"] = torn
            reg.record_audit(
                actor=user, action=reg.ACTION_TEARDOWN,
                key=record["key"],
                payload={"reason": "last_reference_removed"},
            )
        except Exception as exc:
            logger.warning("[monitored_devices] tear_down raised: %s", exc)
            out["torn_down_subsystems"] = []
            out["teardown_error"] = str(exc)
    return out
