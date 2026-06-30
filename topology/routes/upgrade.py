"""Scaler bridge routes: upgrade."""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from routes.bridge_helpers import (
    SCALER_ROOT, _ACTIVE_BUILDS_PATH, _ACTIVE_UPGRADES_PATH, _get_credentials,
    _get_lab_credential_chain, _persist_job_if_done, _remove_active_build,
    _remove_active_upgrade, _resolve_config_dir, _resolve_mgmt_ip,
    _safe_set_mgmt_ip, _save_active_build, _save_active_upgrade,
)
from routes._ops_writer import read_ops as _read_ops_safe
from routes._state import (
    _push_jobs, _push_jobs_lock,
    _get_request_user, _get_request_role, _is_job_owner_or_admin,
)
from routes._device_scheduler import scheduler as _device_scheduler

router = APIRouter()


def _atomic_write_text(path: Path, body: str, mode: int = 0o644) -> None:
    """Write text atomically for large upgrade artifacts and snapshots."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        prior_mode = os.stat(path).st_mode & 0o777
    except FileNotFoundError:
        prior_mode = mode
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp_path, prior_mode)
        os.replace(tmp_path, path)
    except BaseException:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass
        raise


def _upgrade_terminal_timestamp() -> str:
    """Human-readable UTC+3 timestamp for upgrade terminal lines."""
    from datetime import datetime, timedelta, timezone
    israel_tz = timezone(timedelta(hours=3))
    return datetime.now(israel_tz).strftime("%H:%M:%S")


def _format_upgrade_terminal_line(level: str, msg: str, device_id: str = "") -> str:
    """Format upgrade terminal output while preserving frontend parsing.

    Per-device upgrade cards parse lines as `[LEVEL] device: message`, so the
    timestamp belongs inside the message portion.
    """
    lvl = str(level or "INFO").strip().upper()
    text = str(msg or "")
    ts = _upgrade_terminal_timestamp()
    if device_id:
        return f"[{lvl}] {device_id}: [{ts}] {text}"
    return f"[{lvl}] [{ts}] {text}"

# =========================================================================
# Image Upgrade - Jenkins Build Browsing
# =========================================================================

@router.post("/api/operations/image-upgrade/branches")
def list_upgrade_branches(body: dict):
    """List dev or release branches from Jenkins."""
    branch_type = body.get("type", "dev")
    try:
        from scaler.jenkins_integration import JenkinsClient
        jenkins = JenkinsClient()
        if branch_type == "release":
            branches = jenkins.list_release_branches()
        elif branch_type == "dev":
            branches = jenkins.list_dev_branches()
        elif branch_type == "feature":
            branches = jenkins.list_feature_branches()
        else:
            dev = jenkins.list_dev_branches()
            rel = jenkins.list_release_branches()
            feat = jenkins.list_feature_branches()
            branches = dev + rel + feat
        return {
            "branches": [{"name": b.name, "url": getattr(b, "url", "")} for b in branches[:30]],
            "type": branch_type,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/operations/image-upgrade/branch-summaries")
def get_branch_summaries(body: dict):
    """Get lightweight build summary for multiple branches (latest build info only)."""
    import time
    branches = body.get("branches", [])
    if not branches or len(branches) > 20:
        raise HTTPException(status_code=400, detail="Provide 1-20 branches")
    try:
        from scaler.jenkins_integration import JenkinsClient
        jenkins = JenkinsClient()
        summaries = {}
        for branch_name in branches:
            try:
                encoded = jenkins._encode_branch(branch_name)
                data = jenkins._api_get(
                    f"{jenkins.CHEETAH_BASE}/job/{encoded}",
                    params={"tree": "builds[number,result,timestamp]{0,3}"}
                )
                if not data or "builds" not in data:
                    summaries[branch_name] = {"total": 0, "valid": 0, "latest": None}
                    continue
                builds_raw = data["builds"][:3]
                valid_count = 0
                latest_info = None
                for br in builds_raw:
                    ts = br.get("timestamp", 0)
                    age_hours = (time.time() * 1000 - ts) / 3600000 if ts else 9999
                    result = br.get("result") or "BUILDING"
                    is_valid = age_hours <= 48 and result == "SUCCESS"
                    if is_valid:
                        valid_count += 1
                    if latest_info is None:
                        latest_info = {
                            "build_number": br.get("number"),
                            "result": result,
                            "age_hours": round(age_hours, 1),
                            "is_valid": is_valid,
                        }
                summaries[branch_name] = {
                    "total": len(builds_raw),
                    "valid": valid_count,
                    "latest": latest_info,
                }
            except Exception:
                summaries[branch_name] = {"total": 0, "valid": 0, "latest": None}
        return {"summaries": summaries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/operations/image-upgrade/builds")
def get_builds_for_branch(body: dict):
    """List recent builds with image artifacts for a branch (includes failed + sanitizer detection)."""
    branch = body.get("branch", "")
    if not branch:
        raise HTTPException(status_code=400, detail="branch is required")
    
    limit = body.get("limit", 15)
    max_results = body.get("max_results", 10)
    include_failed = body.get("include_failed", False)
    
    try:
        from scaler.jenkins_integration import JenkinsClient
        jenkins = JenkinsClient()
        builds = jenkins.get_recent_builds_with_artifacts(branch, limit=limit, max_results=max_results)
        if not include_failed:
            builds = [b for b in builds if b["build"].result == "SUCCESS"]
        
        return {
            "branch": branch,
            "builds": [
                {
                    "build_number": b["build"].build_number,
                    "result": b["build"].result,
                    "display_name": b["display_name"],
                    "age_hours": round(b["build"].age_hours, 1),
                    "is_expired": b["build"].is_expired,
                    "is_sanitizer": b["is_sanitizer"],
                    "is_qa": str(b["build"].build_params.get("QA_VERSION", "")).lower() == "true",
                    "has_dnos": b["has_dnos"],
                    "has_gi": b["has_gi"],
                    "has_baseos": b["has_baseos"],
                    "url": b["build"].url,
                }
                for b in builds
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/operations/image-upgrade/resolve-url")
def resolve_jenkins_url(body: dict):
    """Resolve a Jenkins URL to build info with sanitizer detection."""
    url = body.get("url", "")
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    
    try:
        from scaler.jenkins_integration import JenkinsClient, get_stack_from_url
        stack = get_stack_from_url(url)
        
        from urllib.parse import unquote
        def _fully_decode(s):
            if not s:
                return s
            prev = s
            for _ in range(5):
                s = unquote(s)
                if s == prev:
                    break
                prev = s
            return s

        if stack.get("error"):
            parsed_branch = _fully_decode(stack.get("parsed_branch", ""))
            parsed_build = stack.get("parsed_build")
            if parsed_branch:
                return {
                    "branch": parsed_branch,
                    "build_number": parsed_build,
                    "dnos_url": None, "gi_url": None, "baseos_url": None,
                    "is_expired": True,
                    "error_detail": stack["error"],
                    "result": None, "is_sanitizer": False,
                }
            raise HTTPException(status_code=400, detail=stack["error"])
        
        branch = _fully_decode(stack.get("branch", ""))
        build_num = stack.get("build")
        
        result = {
            "branch": branch,
            "build_number": build_num,
            "dnos_url": stack.get("dnos_url"),
            "gi_url": stack.get("gi_url"),
            "baseos_url": stack.get("baseos_url"),
            "is_expired": stack.get("is_expired", False),
            "age_hours": round(stack.get("age_hours", 0), 1) if stack.get("age_hours") else None,
            "result": stack.get("result"),
            "is_sanitizer": False,
        }
        
        if build_num and branch:
            try:
                jenkins = JenkinsClient()
                resolved = jenkins.get_build_info(branch, build_num)
                if resolved:
                    result["is_sanitizer"] = resolved.is_sanitizer
                    result["result"] = resolved.result
            except Exception:
                pass
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/operations/image-upgrade/branch-switch")
def detect_branch_switch(body: dict):
    """Detect if upgrade switches between different dev branches (e.g. dev_v25 -> dev_v26)."""
    current_version = body.get("current_version", "")
    target_version = body.get("target_version", "")
    target_branch_name = body.get("target_branch_name", "")
    if not current_version or not target_version:
        raise HTTPException(status_code=400, detail="current_version and target_version are required")
    try:
        from scaler.stack_manager import StackManager
        is_switch, cur_br, tgt_br = StackManager.detect_branch_switch(
            current_version, target_version, target_branch_name
        )
        requires_delete_deploy = StackManager.requires_delete_deploy(
            current_version, target_version, target_branch_name
        )
        return {
            "is_switch": is_switch,
            "current_branch": cur_br,
            "target_branch": tgt_br,
            "requires_delete_deploy": requires_delete_deploy,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/operations/image-upgrade/compat")
def check_version_compat(body: dict):
    """Build compatibility report for source -> target version upgrade."""
    source_version = body.get("source_version", "")
    target_version = body.get("target_version", "")
    config_text = body.get("config_text", "")
    if not source_version or not target_version:
        raise HTTPException(status_code=400, detail="source_version and target_version are required")
    try:
        from scaler.version_compat import build_compatibility_report
        report = build_compatibility_report(source_version, target_version, config_text)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _extract_version_from_dnos_url(url: str) -> str:
    """Extract DNOS version from artifact URL (e.g. dnos-26.1.0.1_xxx.tar)."""
    if not url:
        return ""
    m = re.search(r"dnos[_-](\d+\.\d+\.\d+(?:\.\d+)?)", url, re.IGNORECASE)
    return m.group(1) if m else ""


def _dnos_url_to_version_label(url: str) -> str:
    """Convert a DNOS artifact URL into the full version label that carries the
    branch lineage, suitable for StackManager.extract_branch_name().

        http://.../drivenets_dnos_26.2.0.543_dev.dev_v26_2_1402.tar
            -> 26.2.0.543_dev.dev_v26_2_1402

    Returns "" if the URL is empty or not a recognizable DNOS artifact.
    """
    if not url:
        return ""
    base = str(url).rsplit("/", 1)[-1]
    base = re.sub(r"\.tar(?:\.gz)?$", "", base, flags=re.IGNORECASE)
    m = re.match(r"^drivenets_dnos_(.+)$", base, re.IGNORECASE)
    return m.group(1) if m else ""


def _infer_ncc_id_from_vm_name(vm_name: str):
    """Infer NCC ID from KVM VM name convention.

    VM naming convention: *-ncc0, *-ncc1 (e.g. kvm108-cl408d-ncc0 -> NCC-0).
    GI autodetects ncc-id from NCM LLDP port mapping, but the VM name convention
    follows the same numbering, making this a reliable inference.
    Returns int (0 or 1) or None if pattern not found.
    """
    import re
    m = re.search(r'ncc[_-]?(\d+)', vm_name, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def _safe_ncc_id(value, default=0):
    """Normalise any ncc_id candidate to a clean int in {0, 1}.

    Accepts int, str, None, or garbage. Anything that isn't 0 or 1
    falls back to ``default``. This is the SINGLE source of truth
    used everywhere the bridge is about to interpolate ``ncc-id X``
    into a DNOS/GI CLI command. Scaler CLI uses the same pattern
    inline (`conn.get('ncc_id') if conn.get('ncc_id') is not None
    else 0`); we wrap it so every call site is immune to the
    ``{"ncc_id": null}`` wizard payload and to `.get("ncc_id", 0)`
    returning ``None`` (the ``0`` default only fires on missing
    keys, NOT on a present-but-null value -- that's the trap that
    produced RR-SA-2's ``request system deploy ... ncc-id None``
    20-minute-timeout silent no-op).
    """
    if value is None:
        return int(default)
    if isinstance(value, bool):
        # Guard against surprising Python truthiness (True == 1).
        return int(default)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped or stripped.lower() == "none" or stripped.lower() == "null":
            return int(default)
        try:
            ival = int(stripped)
        except (TypeError, ValueError):
            return int(default)
        return ival if ival in (0, 1) else int(default)
    try:
        ival = int(value)
    except (TypeError, ValueError):
        return int(default)
    return ival if ival in (0, 1) else int(default)


def _normalize_deploy_params(deploy_params, op_data_cached=None,
                              scaler_hostname="", device_id="",
                              conn_ncc_id=None, _log=None):
    """Mutate ``deploy_params`` in place so every downstream deploy site
    can trust ``system_type``, ``deploy_name`` and ``ncc_id`` without
    having to re-derive them.

    The scaler CLI resolves these once right before ``request system
    deploy`` -- we do the same but earlier (at entry into
    ``_run_device_upgrade``) so the whole pipeline sees consistent
    values. Safe to call multiple times; it preserves explicit values
    except for the PE-4 CL-86 guard, where stale SA/empty values are
    more dangerous than overriding to the lab-known deploy contract.

    Sources of truth, in priority order:
      1. Explicit value already in ``deploy_params`` (wizard payload)
      2. Live connection snapshot (``conn_ncc_id``, virsh VM name)
      3. Operational JSON (``deploy_ncc_id`` then ``ncc_id``)
      4. ``0`` fallback (scaler CLI default for SA; CLI retry path
         flips to 1 automatically if the device says "doesn't match")

    Returns the same ``deploy_params`` dict for chaining.
    """
    if deploy_params is None:
        deploy_params = {}
    op_data_cached = op_data_cached or {}

    if not deploy_params.get("system_type"):
        deploy_params["system_type"] = (
            op_data_cached.get("system_type")
            or op_data_cached.get("deploy_system_type")
            or ""
        )

    raw_name = deploy_params.get("deploy_name") or deploy_params.get("name") or ""
    if not raw_name:
        raw_name = (
            op_data_cached.get("deploy_name")
            or scaler_hostname
            or device_id
            or ""
        )
    deploy_params["deploy_name"] = raw_name.rstrip(",").strip() if isinstance(raw_name, str) else raw_name

    current = deploy_params.get("ncc_id", None)
    # Present-but-null / present-but-garbage is treated as "not set".
    current_valid = (isinstance(current, int) and current in (0, 1) and not isinstance(current, bool))
    if not current_valid:
        candidates = [
            conn_ncc_id,
            op_data_cached.get("deploy_ncc_id"),
            op_data_cached.get("ncc_id"),
        ]
        picked = 0
        for cand in candidates:
            if cand is None:
                continue
            norm = _safe_ncc_id(cand, default=-1)
            if norm in (0, 1):
                picked = norm
                break
        deploy_params["ncc_id"] = picked
        if _log is not None and current is not None:
            _log("INFO",
                 f"Normalised ncc_id (was {current!r}, wizard sent it as "
                 f"present-but-invalid) -> {picked}. CLI retry will "
                 f"auto-flip to {1 - picked} if the device reports "
                 f"'doesn\\'t match / auto detected'.")
    else:
        deploy_params["ncc_id"] = int(current)

    labels = {
        str(device_id or "").strip().upper(),
        str(scaler_hostname or "").strip().upper(),
        str(deploy_params.get("deploy_name") or deploy_params.get("name") or "").strip().upper(),
        str(op_data_cached.get("hostname") or "").strip().upper(),
        str(op_data_cached.get("device_id") or "").strip().upper(),
    }
    if {"PE-4", "PE4", "YOR_CL_PE-4", "YOR_CL_PE_4"} & labels:
        # PE-4 chassis identity guards: system_type and deploy_name are
        # immutable facts about the cluster (CL-86 / YOR_CL_PE-4) and the
        # deploy command will syntactically reject any other value, so
        # backfilling them is safe.
        if str(deploy_params.get("system_type") or "").strip().upper() != "CL-86":
            deploy_params["system_type"] = "CL-86"
            if _log is not None:
                _log("INFO", "PE-4 deploy guard: forcing system_type=CL-86")
        if not str(deploy_params.get("deploy_name") or "").strip():
            deploy_params["deploy_name"] = "YOR_CL_PE-4"
        elif str(deploy_params.get("deploy_name") or "").strip().upper() in ("PE-4", "PE4"):
            deploy_params["deploy_name"] = "YOR_CL_PE-4"
        # ncc_id is NOT immutable -- `request system delete` reboots the
        # currently-active NCC and the cluster fails over to the other
        # one. Hardcoding ncc_id=1 here corrupted the post-reboot deploy
        # in the 2026-05-12 incident (script kept talking to NCC-1 while
        # NCC-0 was the new active). The trusted snapshot at upgrade
        # start (`upgrade_start_snapshot` / `kvm_*` / etc) is the only
        # safe source; if none is present the upstream Execute gate
        # `_assert_active_ncc_trusted_for_destructive_op` rejects the
        # job rather than letting a hardcoded value silently win.

    return deploy_params


# =================================================================
# 2026-05-12 incident hardening: PE-4 D+D failover + shell drift
# =================================================================
#
# Three independent failure modes co-occurred during the live PE-4
# Drain+Deploy upgrade on 2026-05-12:
#
#   1. `_normalize_deploy_params` hard-coded `ncc_id=1` for PE-4. The
#      `request system delete` reboot of NCC-1 caused the cluster to
#      fail over to NCC-0, but the script kept targeting NCC-1. The
#      live dncli error was: "either you are trying to connect to the
#      standby NCC or Drivenets CLI is N/A".
#
#   2. The wizard accepted Execute with `active_ncc_source =
#      'pe4_deploy_default'` -- a legacy sentinel that is NOT in
#      `_TRUSTED_ACTIVE_NCC_SOURCES`. Without a fresh trusted probe at
#      Execute time, we cannot know which NCC is currently active and
#      therefore cannot safely issue `request system delete`.
#
#   3. `_ensure_ncc_bash` returned True when the channel was actually
#      at the KVM host shell (kvm108), not the NCC bash shell. The
#      next `dncli` invocation ran on the host and produced confusing
#      "standby NCC" output because the host's diagnostic dncli wrapper
#      tries to reach the inactive NCC by default.
#
# The helpers below address all three: trust-gate, hostname fingerprint,
# and post-reboot active-NCC re-detection. They are intentionally small
# and additive so the existing battle-tested code path is unchanged for
# non-PE-4 / non-cluster devices.

# Prefix set used by the destructive-op trust gate. Mirrors
# `_TRUSTED_ACTIVE_NCC_SOURCES` in `routes/bridge_helpers.py` so a
# single source-of-truth update propagates everywhere. Imported lazily
# to avoid a top-level circular import.
def _trusted_active_ncc_prefixes() -> tuple:
    try:
        from routes.bridge_helpers import _TRUSTED_ACTIVE_NCC_SOURCES
        return tuple(_TRUSTED_ACTIVE_NCC_SOURCES)
    except Exception:
        return (
            "kvm_",
            "virsh_console_verified",
            "pre_upgrade_snapshot",
            "pre_upgrade_backup",
            "scaler_db_cache",
            "topology_virsh_probe",
            "upgrade_start_snapshot",
        )


def _is_trusted_active_ncc_source(source: str) -> bool:
    """Return True iff ``source`` starts with a trusted-prefix.

    Mirrors the frontend ``_isTrustedNccSrc`` helper exactly so both
    sides agree on which sources unlock destructive operations.
    """
    src = (source or "").strip()
    if not src:
        return False
    return any(src.startswith(p) for p in _trusted_active_ncc_prefixes())


def _assert_active_ncc_trusted_for_destructive_op(
        device_id: str, plan: dict, scaler_hostname: str = "") -> None:
    """Refuse a destructive upgrade (delete_deploy / gi_deploy) when the
    device's plan does not carry a trusted ``active_ncc_source``.

    Cluster devices (CL-* system types) are the high-risk case because
    `request system delete` reboots one NCC and the cluster fails over
    to the other -- if we don't have a trusted live probe at Execute
    time, every downstream `dncli` / `request system deploy` call may
    target the wrong NCC.

    Non-cluster devices (single NCP) are unaffected and skip this gate.
    Raises ``HTTPException(412)`` so the wizard surfaces a clear
    "Re-detect required" error instead of letting a silent default
    (``pe4_deploy_default``) drive a destructive command.
    """
    if not isinstance(plan, dict):
        return
    sys_type = str(plan.get("system_type")
                   or (plan.get("deploy_params") or {}).get("system_type")
                   or "").strip().upper()
    is_cluster = bool(plan.get("is_cluster")) or sys_type.startswith("CL-")
    if not is_cluster:
        return
    src = (
        str(plan.get("active_ncc_source") or "").strip()
        or str((plan.get("deploy_params") or {}).get("active_ncc_source") or "").strip()
    )
    if _is_trusted_active_ncc_source(src):
        return
    label = scaler_hostname or device_id or "(unknown)"
    raise HTTPException(
        status_code=412,
        detail=(
            f"Refusing destructive upgrade for cluster device {label}: "
            f"active_ncc_source={src!r} is not in the trusted set "
            f"{list(_trusted_active_ncc_prefixes())}. Click Re-detect "
            "in the upgrade wizard to refresh the live NCC probe and "
            "then retry Execute. This guard exists because "
            "`request system delete` reboots one NCC and the cluster "
            "fails over to the other -- without a trusted live snapshot "
            "we cannot know which NCC will answer dncli after the "
            "reboot, and a silent default has produced a stuck-in-GI "
            "incident before (2026-05-12)."
        ),
    )


def _assert_url_list_for_dd_upgrade(device_id: str, upgrade_type: str,
                                    url_list: list, deploy_params: dict,
                                    scaler_hostname: str = "") -> None:
    """Refuse a Drain+Deploy (delete+deploy / gi_deploy) when ``url_list`` is
    empty or carries no installable component.

    Rationale (2026-05-12 PE-4 stuck-in-GI incident, third bug):
    Phase 4 (``request system delete``) reboots one NCC and the device
    comes back in GI mode with the OLD ``target`` images still showing
    in ``show system stack``. Phase 6 (``_load_images_on_channel`` +
    ``_verify_stack_targets_for_urls``) is the ONLY step that pushes
    the operator-selected images into the GI target stack. If the
    wizard payload reached this function with an empty url_list, Phase
    6 becomes a silent no-op and Phase 7 (``request system deploy``)
    re-runs the same stale stack -- the device "deploys" back into
    its previous image and the user thinks the wizard chose a wrong
    target.

    The fix: refuse BEFORE the delete-reboot happens. The wizard MUST
    supply at least one component URL for a destructive upgrade. Pre-
    flight URL validation (HEAD 200) already runs in
    ``image_upgrade_execute``; this is the empty-list / wrong-shape
    gate.

    Raises ``HTTPException(412)`` from the API path and
    ``RuntimeError`` from the in-job path so the caller can branch on
    the exception class.
    """
    if upgrade_type not in ("delete_deploy", "gi_deploy"):
        return
    label = scaler_hostname or device_id or "(unknown)"
    if not isinstance(url_list, (list, tuple)):
        url_list = []
    real = [(c, u) for (c, u) in (url_list or []) if u and str(u).strip()]
    if real:
        return
    msg = (
        f"Refusing destructive upgrade for {label}: no component URLs "
        f"in the upgrade payload (url_list is empty after filtering). "
        f"The Drain+Deploy flow can only push images to the GI target "
        f"stack AFTER `request system delete` reboots the device into "
        f"GI mode (Phase 6 of `_run_delete_deploy_upgrade`). Without "
        f"at least one of (DNOS, GI, BaseOS) URL, Phase 6 becomes a "
        f"no-op and Phase 7 (`request system deploy`) re-runs the "
        f"OLD target stack -- the upgrade silently keeps the device "
        f"on its previous image. Select an image in the wizard's "
        f"Image dropdown and retry Execute. See 2026-05-12 PE-4 "
        f"stuck-in-GI incident in DEVELOPMENT_GUIDELINES.md."
    )
    raise HTTPException(status_code=412, detail=msg)


def _assert_url_list_in_job(device_id: str, upgrade_type: str,
                            url_list: list, scaler_hostname: str = "") -> None:
    """Same contract as ``_assert_url_list_for_dd_upgrade`` but raises
    ``RuntimeError`` (not ``HTTPException``) -- safe to call from the
    background job thread where FastAPI's HTTPException is not the
    right exception type.

    Defense-in-depth: this gate runs right after Phase 1 (connect)
    and right before Phase 2 (snapshot) inside
    ``_run_delete_deploy_upgrade``. The API-boundary gate
    (``_assert_url_list_for_dd_upgrade`` in ``image_upgrade_execute``)
    catches the empty payload at submission time; this in-job gate
    catches it again before the destructive command goes out, so a
    race where the URL list got cleared between submit and execute
    cannot reach ``request system delete``.
    """
    if upgrade_type not in ("delete_deploy", "gi_deploy"):
        return
    label = scaler_hostname or device_id or "(unknown)"
    if not isinstance(url_list, (list, tuple)):
        url_list = []
    real = [(c, u) for (c, u) in (url_list or []) if u and str(u).strip()]
    if real:
        return
    raise RuntimeError(
        f"Refusing destructive upgrade for {label} mid-job: empty "
        f"url_list (no DNOS / GI / BaseOS URL after filtering). Phase "
        f"6 would silently skip image push and Phase 7 would redeploy "
        f"the OLD target stack. Aborting before `request system "
        f"delete`. (2026-05-12 PE-4 incident defense-in-depth gate.)"
    )


# Match dncli's verbatim error when invoked on the standby NCC of a cluster,
# or when the local Drivenets CLI socket is not answering yet. Both variants
# are emitted by dncli verbatim, so a case-insensitive substring match on
# the post-2026-05-12 hardening is enough -- we re-probe libvirt and pivot.
_STANDBY_NCC_ERROR_RE = re.compile(
    r"either you are trying to connect to the standby NCC"
    r"|Drivenets\s+CLI\s+is\s+N\s*/\s*A",
    re.IGNORECASE,
)


def _looks_like_standby_ncc_error(output: str) -> bool:
    """Detect dncli's "standby NCC / CLI N/A" failure mode.

    Used by the upgrade orchestrator to trigger one retry-after-pivot
    when a dncli call lands on the wrong NCC. The pattern matches both
    of the observed wordings:

      * ``either you are trying to connect to the standby NCC``
      * ``Drivenets CLI is N/A``

    Returns True on a match. Safe to call on already-cleaned (no-ANSI)
    output or on raw recv-buffer text.
    """
    if not output:
        return False
    return bool(_STANDBY_NCC_ERROR_RE.search(output))


def _assert_both_nccs_reachable_for_destructive_op(
        device_id: str, scaler_hostname: str = "") -> None:
    """Refuse a Drain+Deploy / GI deploy when only ONE NCC VM is live.

    Rationale (2026-05-12 PE-4 hardening, pre-flight rule (d)):
    `request system delete` reboots the active NCC. The cluster fails
    over to the OTHER NCC and the wizard's Phase 5a-post re-probe
    pivots the SSH channel to that one. If the standby NCC is already
    shut off at execute time (only ``running`` -- ``shut off`` in the
    KVM ``virsh list``), the delete-reboot would take the WHOLE device
    offline: the active NCC reboots into GI mode but no surviving NCC
    can pick up the cluster control plane. Refuse before the
    destructive command goes out.

    Non-cluster devices (no KVM probe surface) are skipped. The probe
    runs through ``_cluster_preflight_check``, which already covers
    the libvirt enumeration + warning surface; this helper just
    enforces the result.

    Raises ``HTTPException(412)`` with a clear actionable message so
    the wizard surfaces a "Power on standby NCC and retry" gate
    instead of letting a half-dead cluster reach
    ``request system delete``.
    """
    try:
        result = _cluster_preflight_check(scaler_hostname or device_id)
    except Exception:
        return
    if not isinstance(result, dict) or not result:
        return
    vms_running = result.get("vms_running") or []
    vms_defined = result.get("vms_defined") or []
    vms_shut_off = result.get("vms_shut_off") or []
    blocked = bool(result.get("blocked"))
    label = scaler_hostname or device_id or "(unknown)"
    if blocked:
        raise HTTPException(
            status_code=412,
            detail=(
                f"Refusing destructive upgrade for cluster {label}: "
                f"pre-flight reports blocked "
                f"(reason={result.get('block_reason') or 'unknown'}). "
                f"Power on / repair the affected NCC VM(s) and click "
                f"Re-detect in the upgrade wizard before retrying."
            ),
        )
    if len(vms_defined) >= 2 and len(vms_running) < 2:
        missing = [vm for vm in vms_defined if vm not in vms_running]
        raise HTTPException(
            status_code=412,
            detail=(
                f"Refusing destructive upgrade for cluster {label}: "
                f"only {len(vms_running)} of {len(vms_defined)} NCC "
                f"VMs are running. `request system delete` reboots "
                f"the active NCC; without a live standby the device "
                f"would lose its control plane. Power on "
                f"{', '.join(missing or vms_shut_off)} and click "
                f"Re-detect in the upgrade wizard, then retry "
                f"Execute. (2026-05-12 PE-4 pre-flight rule (d).)"
            ),
        )


def _ncc_bash_fingerprint_via_hostname(chan, wait: float = 2.5) -> tuple[bool, str]:
    """Confirm the channel is at an NCC VM bash (not the KVM host shell).

    Runs ``hostname`` and matches the output against the
    ``*-ncc[01]`` convention used for CL-86 NCC VMs. Returns
    ``(at_ncc_bash, hostname_observed)``.

    Why this exists: `_probe_ncc_bash` only verifies that the channel
    answers a bash printf probe. The KVM host (``kvm108``) also runs
    bash and answers the printf probe identically -- so without this
    fingerprint we cannot tell host bash from NCC bash. The 2026-05-12
    incident triggered exactly this misclassification.

    Pure read-only; safe to call on any bash channel.
    """
    import time
    if _channel_is_closed(chan):
        return False, ""
    nonce = str(int(time.time() * 1000000))
    marker_prefix = f"__HOST_PROBE_{nonce}__"
    cmd = f"printf '{marker_prefix}_%s\\n' \"$(hostname)\"\n"
    try:
        while chan.recv_ready():
            chan.recv(65535)
        chan.send(cmd.encode())
    except Exception:
        return False, ""
    deadline = time.time() + wait
    buf = b""
    while time.time() < deadline:
        try:
            if chan.recv_ready():
                buf += chan.recv(65535)
        except Exception:
            break
        time.sleep(0.1)
    decoded = buf.decode("utf-8", errors="replace")
    m = re.search(
        rf"{re.escape(marker_prefix)}_([A-Za-z0-9._\-]+)",
        decoded,
    )
    if not m:
        return False, ""
    hostname = m.group(1).strip()
    # NCC VM convention: <kvm-host>-<cluster>-ncc[01] (e.g.
    # kvm108-cl408d-ncc0). Plain ``kvm108`` (no -ncc suffix) is the
    # host shell -- explicitly rejected.
    is_ncc = bool(re.search(r"-ncc[0-9]+$", hostname, re.IGNORECASE))
    return is_ncc, hostname


def _probe_libvirt_active_ncc_post_reboot(scaler_hostname: str,
                                           _log=None) -> tuple[str, str, int]:
    """Re-probe libvirt RIGHT NOW to find the active NCC VM.

    Returns ``(active_ncc_vm, source, ncc_id)`` -- e.g.
    ``("kvm108-cl408d-ncc0", "post_reboot_virsh_probe", 0)``. The
    ``source`` value is intentionally in
    ``_TRUSTED_ACTIVE_NCC_SOURCES`` (starts with ``kvm_`` is wrong
    here -- this is a NEW provenance, so we extend the trusted set
    via ``post_reboot_virsh_probe`` matching the existing
    ``topology_virsh_probe`` token convention -- kept here for the
    caller; the trust whitelist is updated below).

    On any failure returns ``("", "", -1)`` and the caller falls back
    to the pre-upgrade snapshot. This helper NEVER raises.
    """
    try:
        from scaler.connection_strategy import (
            get_console_config_for_device, _derive_kvm_host)
        cfg = get_console_config_for_device(scaler_hostname) or {}
        if not cfg:
            return "", "", -1
        kvm_host_raw = cfg.get("kvm_host", "")
        if not kvm_host_raw:
            return "", "", -1
        kvm_host = _derive_kvm_host(kvm_host_raw)
        kvm_creds = cfg.get("kvm_host_credentials", {}) or {}
        kvm_user = kvm_creds.get("username", "")
        kvm_pass = kvm_creds.get("password", "")
        ncc_vms = cfg.get("ncc_vms", []) or []
        if not (kvm_host and kvm_user and ncc_vms):
            return "", "", -1
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(kvm_host, username=kvm_user, password=kvm_pass,
                    timeout=8, allow_agent=False, look_for_keys=False)
        try:
            _, out, _ = ssh.exec_command(
                "sudo virsh list --all 2>/dev/null || virsh list --all 2>/dev/null",
                timeout=10)
            virsh_output = out.read().decode("utf-8", errors="replace")
        finally:
            try:
                ssh.close()
            except Exception:
                pass
        running = []
        for vm in ncc_vms:
            if vm not in virsh_output:
                continue
            vm_line = virsh_output.split(vm, 1)[1].split("\n", 1)[0].lower()
            if "running" in vm_line:
                running.append(vm)
        if not running:
            if _log is not None:
                _log("WARN",
                     "Post-reboot virsh probe found ZERO running NCC VMs "
                     f"on {kvm_host}. Cluster may still be rebooting.")
            return "", "", -1
        # When both VMs are running (normal cluster steady state), we
        # cannot tell active from standby via virsh alone -- the caller
        # MUST follow up with a per-NCC dncli probe. We return the
        # first running VM as a best-effort starting point; the caller
        # tries that one first, then falls back to the other if dncli
        # reports "connecting to the standby NCC".
        active_vm = running[0]
        ncc_id = _infer_ncc_id_from_vm_name(active_vm)
        if ncc_id is None:
            ncc_id = -1
        if _log is not None:
            _log("INFO",
                 f"Post-reboot virsh probe: {len(running)} running NCC "
                 f"VM(s) [{', '.join(running)}]; "
                 f"first candidate active = {active_vm}")
        return active_vm, "post_reboot_virsh_probe", ncc_id
    except Exception as exc:
        if _log is not None:
            _log("WARN", f"Post-reboot virsh probe failed: {exc}")
        return "", "", -1


def _cluster_preflight_check(scaler_id: str) -> dict:
    """Pre-deployment check for cluster devices: verify all NCC VMs are running on KVM host.

    Returns dict with: blocked (bool), vms_running, vms_defined, vms_shut_off,
    block_reason (str), warnings (list).
    Returns empty dict if not a cluster or KVM config unavailable.
    """
    import logging
    log = logging.getLogger(__name__)
    try:
        from scaler.connection_strategy import get_console_config_for_device, _derive_kvm_host
        console_cfg = get_console_config_for_device(scaler_id)
        if not console_cfg:
            return {}
        kvm_host_raw = console_cfg.get("kvm_host", "")
        if not kvm_host_raw:
            return {}
        kvm_host = _derive_kvm_host(kvm_host_raw)
        kvm_creds = console_cfg.get("kvm_host_credentials", {})
        kvm_user = kvm_creds.get("username", "")
        kvm_pass = kvm_creds.get("password", "")
        ncc_vms = console_cfg.get("ncc_vms", [])
        if not kvm_host or not kvm_user or not ncc_vms:
            return {}

        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(kvm_host, username=kvm_user, password=kvm_pass,
                    timeout=5, allow_agent=False, look_for_keys=False)
        _, out, _ = ssh.exec_command(
            "sudo virsh list --all 2>/dev/null || virsh list --all 2>/dev/null", timeout=8)
        virsh_output = out.read().decode("utf-8", errors="replace")
        ssh.close()

        running = []
        shut_off = []
        defined = []
        for vm in ncc_vms:
            if vm not in virsh_output:
                continue
            defined.append(vm)
            vm_line = virsh_output.split(vm)[1].split("\n")[0].lower()
            if "running" in vm_line:
                running.append(vm)
            elif "shut off" in vm_line or "shut" in vm_line:
                shut_off.append(vm)

        ncc_options = []
        for vm in running:
            ncc_id = _infer_ncc_id_from_vm_name(vm)
            ncc_options.append({
                "vm_name": vm,
                "ncc_id": ncc_id,
                "label": f"NCC-{ncc_id} ({vm})" if ncc_id is not None else vm,
                "state": "running",
            })
        ncc_options.sort(key=lambda x: x.get("ncc_id") if x.get("ncc_id") is not None else 99)

        result = {
            "kvm_host": kvm_host,
            "kvm_user": kvm_user,
            "ncc_vms_expected": ncc_vms,
            "vms_running": running,
            "vms_defined": defined,
            "vms_shut_off": shut_off,
            "ncc_options": ncc_options,
            "blocked": False,
            "warnings": [],
        }

        if shut_off:
            result["blocked"] = True
            result["block_reason"] = (
                f"NCC VMs shut off on {kvm_host}: {', '.join(shut_off)}. "
                f"Start all NCC VMs before deploying. "
                f"Run: virsh start {shut_off[0]}")
            result["warnings"] = [
                f"[CLUSTER PREFLIGHT FAIL] {len(shut_off)} NCC VM(s) shut off: {', '.join(shut_off)}",
                f"Only {len(running)}/{len(ncc_vms)} NCC VMs running -- deploy will fail or cause cluster instability",
            ]
            log.warning(f"[CLUSTER-PREFLIGHT] {scaler_id}: BLOCKED -- VMs shut off: {shut_off}")
        elif len(running) < len(ncc_vms):
            missing = [vm for vm in ncc_vms if vm not in running]
            result["warnings"] = [
                f"[CLUSTER PREFLIGHT WARN] {len(running)}/{len(ncc_vms)} NCC VMs running. Missing: {', '.join(missing)}",
            ]
            log.warning(f"[CLUSTER-PREFLIGHT] {scaler_id}: WARN -- missing VMs: {missing}")
        else:
            log.info(f"[CLUSTER-PREFLIGHT] {scaler_id}: OK -- all {len(running)} NCC VMs running")

        return result
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"[CLUSTER-PREFLIGHT] {scaler_id}: check failed: {e}")
        return {"blocked": False, "warnings": [f"Cluster preflight check failed: {e}"], "check_error": str(e)}


@router.post("/api/operations/image-upgrade/plan")
def image_upgrade_plan(body: dict):
    """Build per-device upgrade plan: SSH to each device, detect mode + version,
    auto-determine upgrade_type (normal vs delete_deploy), return plan for user review.
    """
    device_ids = body.get("device_ids", [])
    ssh_hosts = body.get("ssh_hosts", {}) or {}
    target_branch = body.get("target_branch", "")
    target_build_number = body.get("target_build_number")
    target_version = body.get("target_version", "")
    dnos_url = body.get("dnos_url", "")

    if not device_ids:
        raise HTTPException(status_code=400, detail="device_ids is required")

    if not target_version and not dnos_url and not (target_branch and target_build_number):
        raise HTTPException(
            status_code=400,
            detail="Provide target_version, dnos_url, or (target_branch + target_build_number)"
        )

    if not target_version:
        if dnos_url:
            target_version = _extract_version_from_dnos_url(dnos_url)
        elif target_branch and target_build_number:
            try:
                from scaler.jenkins_integration import JenkinsClient
                jenkins = JenkinsClient()
                urls = jenkins.get_stack_urls(target_branch, int(target_build_number))
                target_version = _extract_version_from_dnos_url(urls.get("dnos") or "")
            except Exception:
                pass

    if not target_version:
        target_version = "0.0.0"

    try:
        import re, json
        from pathlib import Path
        from scaler.stack_manager import StackManager
        from concurrent.futures import ThreadPoolExecutor, as_completed
        cwd = os.getcwd()
        try:
            os.chdir(SCALER_ROOT)
            from scaler.interactive_scale import _check_single_device_status

            def _check_device(did):
                ssh_host = ssh_hosts.get(did, "") if isinstance(ssh_hosts, dict) else ""
                mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(did, ssh_host)
                _ensure_operational_json(scaler_id or did, mgmt_ip)

                class _Dev:
                    hostname = scaler_id or did

                r = _check_single_device_status(_Dev())
                raw = {k: re.sub(r"\[/?[^\]]+\]", "", str(v)).strip() for k, v in r.items()}

                mode_raw = (raw.get("mode") or "?").upper()
                from scaler.connection_strategy import classify_device_state
                mode = classify_device_state(mode_raw) or "?"

                current_version = (raw.get("dnos_ver") or "-").strip()
                if current_version in ("-", "", "?"):
                    current_version = ""

                # PE-4 / CL-86 cluster fallback (2026-05-12):
                # `_check_single_device_status` can return mode="?" and
                # empty versions when the SSH probe times out before
                # the slow virsh-console path resolves -- which is
                # the canonical failure mode on cluster devices whose
                # mgmt_ip rejects password SSH (PE-4 NCC0 100.64.4.98
                # is the documented example, see DEVELOPMENT_GUIDELINES.md
                # "Image Upgrade Wizard -- PE-4 / CL-86 Cluster Detection
                # Fix"). When this happens, fall through to the fresh
                # operational.json record: every monitor refresh writes
                # device_state + stack_components there. If the cached
                # record is fresh (< 30 minutes) AND has DNOS state +
                # any cached DNOS version, use it instead of surfacing
                # the silent "?" / "-" the operator saw in the bug
                # report. The frontend can still call "Verify via SSH"
                # for a live re-probe.
                ops_cache_used = False
                ops_cache_age_sec = -1
                try:
                    _opf_fb = Path(SCALER_ROOT) / "db" / "configs" / (scaler_id or did) / "operational.json"
                    if _opf_fb.exists():
                        _opd_fb = _read_ops_safe(_opf_fb)
                        _dev_state_fb = (_opd_fb.get("device_state") or "").upper()
                        _fetched_at = _opd_fb.get("stack_fetched_at") or _opd_fb.get("last_updated") or ""
                        if _fetched_at:
                            try:
                                from datetime import datetime, timezone
                                _ts = datetime.strptime(_fetched_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                                ops_cache_age_sec = int((datetime.now(timezone.utc) - _ts).total_seconds())
                            except Exception:
                                ops_cache_age_sec = -1

                        # Only fall back when (a) the SSH probe gave us
                        # nothing usable AND (b) the cache record is
                        # fresh (<= 30 minutes) AND (c) the cache says
                        # DNOS (we never claim DNOS from a stale GI
                        # record). The 30-minute window matches the
                        # monitor refresh cadence + a safety margin.
                        _stack_components_fb = _opd_fb.get("stack_components", []) or []
                        if (
                            (mode in ("", "?") or not current_version)
                            and _dev_state_fb == "DNOS"
                            and 0 <= ops_cache_age_sec <= 1800
                            and _stack_components_fb
                        ):
                            # Parse stack components, then fall back
                            # to dnos_version field, then dnos_url.
                            _dnos_cached = ""
                            _gi_cached = ""
                            _baseos_cached = ""
                            for _comp in _stack_components_fb:
                                _name = (_comp.get("name") or _comp.get("component") or "").upper()
                                _ver = _comp.get("current") or _comp.get("version") or ""
                                if not _ver or _ver == "-":
                                    continue
                                if "DNOS" in _name or _name == "SYSTEM":
                                    _dnos_cached = _ver
                                elif "GI" in _name or "GENERIC" in _name:
                                    _gi_cached = _ver
                                elif "BASE" in _name:
                                    _baseos_cached = _ver
                            if not _dnos_cached:
                                _dv = _opd_fb.get("dnos_version", "")
                                if _dv:
                                    _m = re.match(r"(\d+\.\d+\.\d+[\.\d]*)", _dv)
                                    _dnos_cached = _m.group(1) if _m else _dv
                            if _dnos_cached:
                                mode = "DNOS"
                                current_version = _dnos_cached
                                ops_cache_used = True
                                # Stash for the frontend so it knows the
                                # value came from cache and the operator
                                # can click "Verify via SSH" if they want
                                # a live re-probe.
                                raw["dnos_ver"] = _dnos_cached
                                raw["gi_ver"] = _gi_cached or raw.get("gi_ver") or ""
                                raw["baseos_ver"] = _baseos_cached or raw.get("baseos_ver") or ""
                except Exception:
                    pass

                upgrade_type = "normal"
                reason = ""
                warnings = []

                if mode == "RECOVERY":
                    upgrade_type = "blocked"
                    reason = ("Device in RECOVERY mode -- restore to full GI "
                              "first, then delete+deploy")
                    warnings.append("Cannot upgrade from RECOVERY (recover to GI, then delete+deploy)")
                elif mode == "GI":
                    # GI -> full delete+deploy (NOT gi_deploy). delete_deploy is
                    # resume-safe: it skips `request system delete` when the
                    # device is already in GI/BASEOS_SHELL and loads+deploys
                    # directly, while a plain gi_deploy is refused by GI_RECOVERY
                    # for a NEW build (revert-only). (2026-06-28)
                    upgrade_type = "delete_deploy"
                    reason = "Device in GI mode -- full delete+deploy (resume-safe: skips the wipe when already in GI)"
                    warnings.append("GI mode uses delete+deploy")
                elif mode == "DNOS" and current_version and target_version and target_version != "0.0.0":
                    cv = re.match(r"(\d+\.\d+\.\d+\.\d+)", current_version)
                    tv = re.match(r"(\d+\.\d+\.\d+\.\d+)", target_version)
                    if cv and tv and cv.group(1) == tv.group(1):
                        upgrade_type = "skip"
                        reason = f"Already at target version ({cv.group(1)})"
                elif current_version:
                    requires_dd = StackManager.requires_delete_deploy(
                        current_version, target_version, target_branch
                    )
                    if requires_dd:
                        upgrade_type = "delete_deploy"
                        cur_maj, _ = StackManager.extract_major_version(current_version)
                        tgt_maj, _ = StackManager.extract_major_version(target_version)
                        is_switch, cur_br, tgt_br = StackManager.detect_branch_switch(
                            current_version, target_version, target_branch
                        )
                        if is_switch and cur_maj == tgt_maj:
                            reason = f"Branch switch: {cur_br} -> {tgt_br}"
                            warnings.append("Branch switch requires delete+deploy")
                        else:
                            reason = f"Major version change ({cur_maj} -> {tgt_maj})"
                            warnings.append("Major version jump requires delete+deploy")
                    else:
                        reason = "Same major version -- normal upgrade"
                else:
                    reason = "Unknown current version -- assuming normal"
                    warnings.append("Could not detect current DNOS version")

                # Private feature-branch target -> always delete+deploy, even
                # for a same-branch build bump or an unknown current version.
                # An in-DNOS `normal` install onto a private lineage has
                # repeatedly left devices stuck/non-converged. (2026-06-28)
                if upgrade_type == "normal" and StackManager.target_is_private_branch(target_version):
                    upgrade_type = "delete_deploy"
                    reason = "Private feature-branch build -- full delete+deploy (in-DNOS install across a private lineage is unsafe)"
                    warnings.append("Private-branch target forces delete+deploy")

                result_item = {
                    "mode": mode,
                    "current_version": current_version or "-",
                    "target_version": target_version,
                    "upgrade_type": upgrade_type,
                    "reason": reason,
                    "components": ["DNOS", "GI", "BaseOS"],
                    "warnings": warnings,
                }
                # Surface where Current came from so the frontend can
                # render a clear status (Live / Cached / Verify-required)
                # without re-fetching operational.json. Also lets the
                # wizard differentiate "SSH succeeded with no version"
                # (cluster bug) from "SSH worked but device is brand new".
                if ops_cache_used:
                    result_item["current_version_source"] = "operational_json_cache"
                    result_item["current_version_age_sec"] = ops_cache_age_sec
                    result_item["warnings"] = result_item.get("warnings", []) + [
                        f"Used cached operational.json data (age {ops_cache_age_sec}s). Click Verify via SSH for live state."
                    ]
                else:
                    result_item["current_version_source"] = "ssh_live"

                # Surface active-NCC info from operational.json for the
                # cluster row's "Deploy NCC" picker. The DOWNSTREAM
                # frontend mirrors `_TRUSTED_ACTIVE_NCC_SOURCES` from
                # `routes/bridge_helpers.py`; sources like
                # `kvm_first_running` / `kvm_virsh_*` / `topology_virsh_probe`
                # are trusted prefixes that suppress the orange
                # "Active NCC not detected -- verify" warning. Without
                # this surfacing, the frontend was forced to fall back
                # to the legacy `pe4_deploy_default` hardcoded NCC=1
                # path -- which is exactly what the bug screenshot
                # showed for PE-4.
                try:
                    _opf_ncc = Path(SCALER_ROOT) / "db" / "configs" / (scaler_id or did) / "operational.json"
                    if _opf_ncc.exists():
                        _opd_ncc = _read_ops_safe(_opf_ncc)
                        _ncc_vm = (_opd_ncc.get("active_ncc_vm") or "").strip()
                        _ncc_src = (_opd_ncc.get("active_ncc_source") or "").strip()
                        if _ncc_vm:
                            result_item["active_ncc_vm"] = _ncc_vm
                            # If `active_ncc_source` is absent (a legacy
                            # ops record), tag it `context_unverified`
                            # so the frontend can still render a
                            # specific "Re-detect" prompt instead of
                            # silently trusting the value.
                            result_item["active_ncc_source"] = _ncc_src or "context_unverified"
                            # Derive a numeric ncc_id from the VM name
                            # (e.g. "kvm108-cl408d-ncc1" -> 1). This is
                            # the value Execute passes to the scaler
                            # deploy CLI. Keep the existing scaler-CLI
                            # plan override path in `_normalize_deploy_params`
                            # in charge of the FINAL ncc_id, but seed
                            # the wizard with the trusted live value so
                            # the dropdown defaults are correct.
                            try:
                                _m = re.search(r"ncc[\s_-]*(\d+)", _ncc_vm, re.IGNORECASE)
                                if _m:
                                    result_item["ncc_id"] = int(_m.group(1))
                            except Exception:
                                pass
                        # Forward verification timestamp so the row can
                        # show e.g. "(active, 2 min ago)" if desired.
                        _ncc_seen = _opd_ncc.get("active_ncc_last_good_at") or ""
                        if _ncc_seen:
                            result_item["active_ncc_last_good_at"] = _ncc_seen
                except Exception:
                    pass

                if upgrade_type in ("delete_deploy", "gi_deploy"):
                    dp = {"system_type": "", "deploy_name": scaler_id or did, "ncc_id": 0}
                    try:
                        _opf = Path(SCALER_ROOT) / "db" / "configs" / (scaler_id or did) / "operational.json"
                        if _opf.exists():
                            _opd = _read_ops_safe(_opf)
                            dp["system_type"] = _opd.get("system_type") or _opd.get("deploy_system_type") or ""
                            dp["deploy_name"] = _opd.get("deploy_name") or (scaler_id or did)
                            # `_safe_ncc_id` clamps None / "None" / "" /
                            # out-of-range to 0 (same contract as
                            # `_normalize_deploy_params`). Previously
                            # `int(... or 0)` tripped on None OR-short-
                            # circuit in some edge cases; the helper
                            # is explicit about every bad input we've
                            # observed in the field.
                            dp["ncc_id"] = _safe_ncc_id(
                                _opd.get("deploy_ncc_id")
                                if _opd.get("deploy_ncc_id") is not None
                                else _opd.get("ncc_id")
                            )
                    except Exception:
                        pass
                    result_item["deploy_params"] = dp

                # --- Resolve system_type for the row (cluster + non-cluster) ---
                # Source order:
                #   1. deploy_params.system_type (from operational.json above).
                #   2. _get_device_context() -- scans devices.json + config
                #      backups + DNAAS inventory. CRITICAL for devices that
                #      had `request system delete` issued (operational.json
                #      now reads "N/A", but devices.json + backups still
                #      remember the chassis as e.g. SA-36CD-S).
                # User report 2026-04-24: PE-1 was "Ready" with full
                # DNOS/GI/BASEOS but the wizard rendered red "sys-type?"
                # because operational.json had "N/A". RR-SA-2 had the same
                # issue post-delete. The root cause was that the SSH path
                # only wrote `deploy_params.system_type` for delete_deploy
                # / gi_deploy and `result_item["system_type"]` ONLY for
                # cluster devices, leaving the row's primary field empty.
                _sys_type = result_item.get("deploy_params", {}).get("system_type", "")
                _sys_type_source = "operational_json" if _sys_type else ""
                if not _sys_type:
                    try:
                        _opf2 = Path(SCALER_ROOT) / "db" / "configs" / (scaler_id or did) / "operational.json"
                        if _opf2.exists():
                            _sys_type = _read_ops_safe(_opf2).get("system_type", "")
                            if _sys_type:
                                _sys_type_source = "operational_json"
                    except Exception:
                        pass
                if not _sys_type or _sys_type.strip().upper() in ("N/A", "", "NULL", "NONE"):
                    try:
                        # Reuse the resolver chain that survives `request
                        # system delete` (devices.json + scaler config
                        # backups + DNAAS inventory). Localized import to
                        # avoid a circular import with bridge_helpers.
                        from .bridge_helpers import _get_device_context as _gdc
                        _ctx = _gdc(scaler_id or did, live=False, ssh_host=ssh_host or "") or {}
                        _ctx_st = (_ctx.get("system_type") or "").strip()
                        if _ctx_st and _ctx_st.upper() not in ("N/A", "NULL", "NONE"):
                            _sys_type = _ctx_st
                            _sys_type_source = _ctx.get("system_type_source", "context_resolver")
                            # Also backfill deploy_params so Execute uses
                            # the recovered value, not the empty operational.json.
                            if "deploy_params" in result_item:
                                if not result_item["deploy_params"].get("system_type"):
                                    result_item["deploy_params"]["system_type"] = _sys_type
                    except Exception as _gdc_exc:
                        result_item.setdefault("warnings", []).append(
                            f"system_type resolve failed: {_gdc_exc}"
                        )

                # ALWAYS surface system_type at the top level (was previously
                # only set for cluster devices, which left SA-* rows red).
                if _sys_type:
                    result_item["system_type"] = _sys_type
                    if _sys_type_source:
                        result_item["system_type_source"] = _sys_type_source

                # --- Cluster preflight: check NCC VMs on KVM host ---
                is_cluster = (_sys_type or "").upper().startswith("CL-")
                if is_cluster:
                    result_item["is_cluster"] = True
                    preflight = _cluster_preflight_check(scaler_id or did)
                    if preflight:
                        result_item["cluster_preflight"] = preflight
                        if preflight.get("blocked"):
                            result_item["upgrade_type"] = "blocked"
                            result_item["reason"] = preflight.get("block_reason", "Cluster preflight failed")
                            result_item["warnings"] = preflight.get("warnings", [])

                return did, result_item

            devices = {}
            with ThreadPoolExecutor(max_workers=min(len(device_ids), 5)) as pool:
                futures = {pool.submit(_check_device, did): did for did in device_ids}
                for fut in as_completed(futures):
                    try:
                        did, result = fut.result()
                        devices[did] = result
                    except Exception as exc:
                        did = futures[fut]
                        # Last-ditch cached fallback when the SSH probe
                        # raised an exception (timeout, auth failure,
                        # ghost-IP, etc). If operational.json holds a
                        # fresh DNOS record, paint the row with cached
                        # data + a clear warning instead of leaving the
                        # operator staring at "Mode = ?" / "Current = -"
                        # with no explanation (the bug screenshot the
                        # 2026-05-12 fix landing addressed). The user
                        # can still click Verify via SSH for a live
                        # re-probe.
                        _exc_str = str(exc)
                        _fallback_item = {
                            "mode": "?", "current_version": "-",
                            "target_version": target_version,
                            "upgrade_type": "normal",
                            "reason": f"SSH check failed: {_exc_str}",
                            "components": ["DNOS", "GI", "BaseOS"],
                            "warnings": [_exc_str],
                            "current_version_source": "ssh_failed",
                        }
                        try:
                            _resolved = _resolve_mgmt_ip(did, ssh_hosts.get(did, "") if isinstance(ssh_hosts, dict) else "")
                            _sid_fb = _resolved[1] if _resolved else did
                            _opf_ex = Path(SCALER_ROOT) / "db" / "configs" / _sid_fb / "operational.json"
                            if _opf_ex.exists():
                                _opd_ex = _read_ops_safe(_opf_ex)
                                _ds_ex = (_opd_ex.get("device_state") or "").upper()
                                _stack_ex = _opd_ex.get("stack_components", []) or []
                                if _ds_ex == "DNOS" and _stack_ex:
                                    _dnos_ex = ""
                                    for _comp in _stack_ex:
                                        _name = (_comp.get("name") or "").upper()
                                        _ver = _comp.get("current") or ""
                                        if _ver and "DNOS" in _name:
                                            _dnos_ex = _ver
                                            break
                                    if _dnos_ex:
                                        _fallback_item["mode"] = "DNOS"
                                        _fallback_item["current_version"] = _dnos_ex
                                        _fallback_item["current_version_source"] = "operational_json_cache_after_ssh_fail"
                                        _fallback_item["warnings"] = [
                                            f"Live SSH probe failed ({_exc_str}); using cached operational.json (verify before Execute)."
                                        ]
                                # Active-NCC info even when SSH failed.
                                _ncc_vm_ex = (_opd_ex.get("active_ncc_vm") or "").strip()
                                _ncc_src_ex = (_opd_ex.get("active_ncc_source") or "").strip()
                                if _ncc_vm_ex:
                                    _fallback_item["active_ncc_vm"] = _ncc_vm_ex
                                    _fallback_item["active_ncc_source"] = _ncc_src_ex or "context_unverified"
                                    try:
                                        _m = re.search(r"ncc[\s_-]*(\d+)", _ncc_vm_ex, re.IGNORECASE)
                                        if _m:
                                            _fallback_item["ncc_id"] = int(_m.group(1))
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                        devices[did] = _fallback_item
        finally:
            os.chdir(cwd)

        return {"devices": devices, "target_version": target_version}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/operations/image-upgrade/stack")
def get_build_stack(body: dict):
    """Get DNOS/GI/BaseOS URLs for a specific branch + build number."""
    branch = body.get("branch", "")
    build_number = body.get("build_number")
    if not branch or not build_number:
        raise HTTPException(status_code=400, detail="branch and build_number are required")
    
    try:
        from scaler.jenkins_integration import JenkinsClient
        jenkins = JenkinsClient()
        
        build = jenkins.get_build_info(branch, int(build_number))
        if not build:
            raise HTTPException(status_code=404, detail=f"Build #{build_number} not found")
        
        urls = jenkins.get_stack_urls(branch, int(build_number))
        
        dnos_url = urls.get("dnos")
        gi_url = urls.get("gi")
        baseos_url = urls.get("baseos")

        url_status = {}
        try:
            from scaler.jenkins_integration import validate_artifact_url
            for label, u in [("dnos", dnos_url), ("gi", gi_url), ("baseos", baseos_url)]:
                if u:
                    ok, msg = validate_artifact_url(u, timeout=5)
                    url_status[label] = {"valid": ok, "status": msg}
        except Exception:
            pass

        return {
            "branch": branch,
            "build_number": build.build_number,
            "result": build.result,
            "is_sanitizer": build.is_sanitizer,
            "is_expired": build.is_expired,
            "age_hours": round(build.age_hours, 1),
            "dnos_url": dnos_url,
            "gi_url": gi_url,
            "baseos_url": baseos_url,
            "url_status": url_status,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/operations/image-upgrade")
def image_upgrade_execute(body: dict, request: Request = None):
    """Execute image upgrade on devices. Supports per-device plans and parallel execution."""
    import uuid
    import threading
    from datetime import datetime
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Owner is the JWT-authenticated user (or "default" in single-user mode).
    # MUST be set on the job dict so `/api/config/push/progress/{job_id}` SSE
    # can match ownership. Previously missing -> non-default users got 403 on
    # their own upgrade's progress stream.
    owner = _get_request_user(request) if request else "default"

    device_ids = body.get("device_ids", [])
    ssh_hosts = body.get("ssh_hosts", {}) or {}
    device_plans = body.get("device_plans", {}) or {}
    max_concurrent = max(1, min(int(body.get("max_concurrent", 3)), 10))
    branch = body.get("branch", "main")
    build_number = body.get("build_number")
    components = body.get("components", ["DNOS", "GI", "BaseOS"])
    upgrade_type = body.get("upgrade_type", "normal")
    dnos_url = body.get("dnos_url")
    gi_url = body.get("gi_url")
    baseos_url = body.get("baseos_url")

    if not device_ids:
        raise HTTPException(status_code=400, detail="device_ids is required")
    if not dnos_url and not gi_url and not baseos_url:
        raise HTTPException(status_code=400, detail="At least one of dnos_url, gi_url, baseos_url is required")

    # Refuse duplicate submissions. A double-click on "Upgrade" or a stale
    # retry from the wizard used to start a second job with a fresh job_id
    # targeting the same device -- two threads would then race on
    # `request system delete` / `request system deploy`, leaving the device
    # in an unpredictable state. The per-device scheduler (acquired later)
    # serialises *execution*, but by the time the second job reaches the
    # scheduler both have already been accepted as "running" and stream
    # confusing status to the UI. Reject here with 409 so the wizard can
    # either join the existing job or bail out cleanly.
    busy = []
    for _did in device_ids:
        try:
            _scaler_id = _resolve_config_dir(_did) or _did
        except Exception:
            _scaler_id = _did
        if _device_has_active_job(_did, _scaler_id):
            busy.append(_did)
    if busy:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Upgrade already in progress for: {', '.join(busy)}. "
                f"Wait for the current job to finish, or cancel it from the "
                f"operations panel before starting a new one."
            ),
        )

    # Validate wizard-controlled strings that end up INSIDE a CLI command on
    # the device (`request system deploy system-type <T> name <N> ncc-id N`).
    # Paramiko sends the command as raw text, so newlines / backticks / quotes
    # in operator-supplied values could split the line into an attacker-chosen
    # second command on the device CLI. Reject payloads whose deploy fields
    # don't match tight whitelists instead of trying to shell-escape them.
    _sys_type_re = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$")
    _deploy_name_re = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,62}$")
    _bad_plans = {}
    for _did, _plan in (device_plans or {}).items():
        if not isinstance(_plan, dict):
            continue
        _dp = _plan.get("deploy_params") or {}
        if not isinstance(_dp, dict):
            continue
        _st = str(_dp.get("system_type") or "").strip()
        _dn = str(_dp.get("deploy_name") or "").strip()
        _errs = []
        if _st and not _sys_type_re.match(_st):
            _errs.append(f"system_type={_st!r} (expected [A-Za-z0-9._-]{{1,32}})")
        if _dn and not _deploy_name_re.match(_dn):
            _errs.append(f"deploy_name={_dn!r} (expected hostname-safe [A-Za-z0-9._-]{{1,63}})")
        if _errs:
            _bad_plans[_did] = "; ".join(_errs)
    if _bad_plans:
        raise HTTPException(
            status_code=422,
            detail=(
                "Invalid deploy parameters (would break device CLI). "
                + "; ".join(f"{d}: {msg}" for d, msg in _bad_plans.items())
            ),
        )

    # Pre-validate URLs before starting upgrade -- fail fast if images are expired/404
    import requests as _req
    url_validation = {}
    for label, u in [("DNOS", dnos_url), ("GI", gi_url), ("BaseOS", baseos_url)]:
        if not u:
            continue
        try:
            head_resp = _req.head(u, timeout=10, allow_redirects=True)
            if head_resp.status_code == 200:
                url_validation[label] = {"valid": True, "status": head_resp.status_code}
            elif head_resp.status_code == 404:
                url_validation[label] = {"valid": False, "status": 404,
                                         "error": f"{label} image not found (HTTP 404) -- build artifacts may have expired"}
            else:
                url_validation[label] = {"valid": False, "status": head_resp.status_code,
                                         "error": f"{label} image returned HTTP {head_resp.status_code}"}
        except _req.exceptions.ConnectionError:
            url_validation[label] = {"valid": False, "status": 0,
                                     "error": f"{label} image server unreachable -- check network/DNS"}
        except _req.exceptions.Timeout:
            url_validation[label] = {"valid": False, "status": 0,
                                     "error": f"{label} image server timed out (10s)"}
        except Exception as e:
            url_validation[label] = {"valid": False, "status": 0, "error": f"{label} URL check failed: {e}"}

    # Active-NCC trust gate (2026-05-12 hardening). For each device whose
    # plan is a destructive upgrade flow (delete_deploy / gi_deploy), check
    # that the plan carries a trusted `active_ncc_source`. Cluster (CL-86
    # / multi-NCC) devices are gated; single-NCP devices are not. Raises
    # 412 with a clear "Re-detect required" message so the wizard can
    # surface a corrective action rather than letting a stale/legacy
    # `pe4_deploy_default` value drive a destructive command. See the
    # extended doctrine in `_assert_active_ncc_trusted_for_destructive_op`.
    if upgrade_type in ("delete_deploy", "gi_deploy"):
        for _did in device_ids:
            _plan = (device_plans or {}).get(_did) or {}
            if not isinstance(_plan, dict):
                _plan = {}
            try:
                _scaler_id_for_gate = _resolve_config_dir(_did) or _did
            except Exception:
                _scaler_id_for_gate = _did
            _assert_active_ncc_trusted_for_destructive_op(
                _did, _plan, scaler_hostname=_scaler_id_for_gate)

            # 2026-05-12 stuck-in-GI gate (Bug 3): per-device empty
            # url_list check. Per-device plans may override the
            # global url_list with per-device URLs; we honour the
            # per-device override first, then fall back to the
            # top-level URLs. Same component union as Phase 6 of
            # _run_delete_deploy_upgrade.
            _plan_dnos = _plan.get("dnos_url") or dnos_url
            _plan_gi = _plan.get("gi_url") or gi_url
            _plan_base = _plan.get("baseos_url") or baseos_url
            _plan_comps = _plan.get("components", components) or []
            _plan_url_list = []
            if "DNOS" in _plan_comps and _plan_dnos:
                _plan_url_list.append(("DNOS", _plan_dnos))
            if "GI" in _plan_comps and _plan_gi:
                _plan_url_list.append(("GI", _plan_gi))
            if "BaseOS" in _plan_comps and _plan_base:
                _plan_url_list.append(("BaseOS", _plan_base))
            _assert_url_list_for_dd_upgrade(
                _did, upgrade_type, _plan_url_list,
                deploy_params=(_plan.get("deploy_params") or {}),
                scaler_hostname=_scaler_id_for_gate)

            # 2026-05-12 pre-flight rule (d): both NCC VMs reachable.
            # The Phase-4 `request system delete` reboots the active
            # NCC and the cluster fails over to the standby. If the
            # standby is already shut off at execute time, the delete
            # would take the entire device offline. We refuse here so
            # the wizard surfaces an actionable "Power on standby NCC
            # and retry" error instead of bricking the device.
            _assert_both_nccs_reachable_for_destructive_op(
                _did, scaler_hostname=_scaler_id_for_gate)

    invalid_urls = {k: v for k, v in url_validation.items() if not v.get("valid")}
    if invalid_urls:
        errors = "; ".join(v["error"] for v in invalid_urls.values())
        raise HTTPException(status_code=422,
                            detail=f"Image URLs are not accessible: {errors}. "
                                   f"The build artifacts may have expired (48h bucket). "
                                   f"Trigger a new build or select a fresher build.")

    url_list = []
    if "DNOS" in components and dnos_url:
        url_list.append(("DNOS", dnos_url))
    if "GI" in components and gi_url:
        url_list.append(("GI", gi_url))
    if "BaseOS" in components and baseos_url:
        url_list.append(("BaseOS", baseos_url))

    job_id = str(uuid.uuid4())[:8]
    user, password = _get_credentials()

    device_state = {}
    for did in device_ids:
        plan = device_plans.get(did, {})
        up_type = plan.get("upgrade_type", upgrade_type)
        comps = plan.get("components", components)
        if up_type in ("blocked", "skip"):
            device_state[did] = {
                "status": "skipped",
                "phase": "blocked" if up_type == "blocked" else "at_target",
                "percent": 100 if up_type == "skip" else 0,
                "message": plan.get("reason", "Skipped"),
                "upgrade_type": up_type,
                "components": comps,
                "error": plan.get("reason"),
                "started_at": datetime.utcnow().isoformat() + "Z",
                "completed_at": datetime.utcnow().isoformat() + "Z",
            }
        else:
            device_state[did] = {
                "status": "pending",
                "phase": "queued",
                "percent": 0,
                "message": "Waiting...",
                "upgrade_type": up_type,
                "components": comps,
                "error": None,
                "started_at": None,
                "completed_at": None,
            }

    initial_est = None
    try:
        from scaler.config_pusher import get_upgrade_time_estimate
        est_total = 0
        for did in device_ids:
            if device_state.get(did, {}).get("status") == "pending":
                plan = device_plans.get(did, {})
                up_type = plan.get("upgrade_type", upgrade_type)
                dev_mode = plan.get("mode", "DNOS")
                dev_comps = plan.get("components", components)
                e = get_upgrade_time_estimate(up_type, dev_comps, dev_mode, did)
                est_total = max(est_total, e.get("total", 180))
        initial_est = est_total if est_total > 0 else 180
    except Exception:
        initial_est = 180

    # Atomic admission: re-check `_device_has_active_job` while holding
    # `_push_jobs_lock` and only then insert the new job. Without this
    # second check there's a TOCTOU window between the line ~821 admission
    # call and the dict insert below: two simultaneous POSTs from
    # different operators for the same device could both pass the early
    # check (no job exists yet) and both insert. The per-device
    # `_device_scheduler.exclusive(mgmt_ip)` lock further down would
    # still serialize the actual CLI work, but two "running" jobs would
    # show up in the UI for the same device and stream confusing
    # progress until the second one finally got the device lock.
    busy_now = []
    with _push_jobs_lock:
        for _did in device_ids:
            try:
                _scaler_id = _resolve_config_dir(_did) or _did
            except Exception:
                _scaler_id = _did
            cands = {c for c in (_did, _scaler_id) if c}
            for _j in _push_jobs.values():
                _st = (_j.get("status") or "").lower()
                if _st in ("completed", "failed", "cancelled", "canceled"):
                    continue
                _devs = set(_j.get("devices") or [])
                if not _devs:
                    _devs = set((_j.get("device_state") or {}).keys())
                if cands & _devs:
                    busy_now.append(_did)
                    break
        if busy_now:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Upgrade already in progress for: "
                    f"{', '.join(busy_now)}. Another operator just "
                    f"started one. Wait for it to finish, or cancel "
                    f"it from the operations panel."
                ),
            )
        _push_jobs[job_id] = {
            "job_id": job_id,
            "job_type": "upgrade",
            "owner": owner,
            "status": "running",
            "phase": "starting",
            "message": f"Upgrade queued for {len(device_ids)} devices",
            "percent": 0,
            "success": False,
            "done": False,
            "terminal_lines": [],
            "job_name": f"Image upgrade {', '.join(device_ids[:3])}{'...' if len(device_ids) > 3 else ''}",
            "device_id": device_ids[0] if len(device_ids) == 1 else "",
            "devices": device_ids,
            "device_state": device_state,
            "max_concurrent": max_concurrent,
            "components": components,
            "ssh_hosts": ssh_hosts,
            "device_plans": device_plans,
            "upgrade_type": upgrade_type,
            "dnos_url": dnos_url,
            "gi_url": gi_url,
            "baseos_url": baseos_url,
            "image_urls": {
                k: {"url": v, "valid": True}
                for k, v in {
                    "dnos": dnos_url,
                    "gi": gi_url,
                    "baseos": baseos_url,
                }.items()
                if v
            },
            "started_at": datetime.utcnow().isoformat() + "Z",
            "estimated_total_seconds": initial_est,
        }

    # Snapshot the pre-upgrade active NCC for every KVM cluster device
    # we're about to touch. This captures the "before state" the user
    # explicitly asked for: if the cluster state flips mid-upgrade
    # (one NCC goes down, the other takes over) we still know which
    # NCC was active when the operator hit Execute. The wizard and all
    # mid-upgrade UI reads will surface this snapshot until
    # ``_finalize_upgrade_job`` clears it. For non-cluster devices this
    # is a no-op (snapshot helper skips when ``active_ncc_vm`` is
    # missing).
    try:
        from routes.bridge_helpers import snapshot_active_ncc_for_upgrade
        for _did in device_ids:
            if device_state.get(_did, {}).get("status") == "skipped":
                continue
            try:
                _plan = device_plans.get(_did, {}) or {}
                _explicit_vm = ""
                _dp = _plan.get("deploy_params") or {}
                if isinstance(_dp, dict):
                    _explicit_vm = (_dp.get("active_ncc_vm")
                                    or _dp.get("deploy_ncc_vm")
                                    or "")
                snapshot_active_ncc_for_upgrade(
                    device_id=_did,
                    hostname=_did,
                    explicit_active_ncc_vm=_explicit_vm,
                )
            except Exception:
                pass
    except Exception:
        pass

    def _run_upgrade():
        from routes._state import app_user_context
        # Rebind current_app_user inside this daemon thread so every
        # `_get_credentials()` call inside _run_device_upgrade resolves to
        # the owner's per-user device store (not the default lab user).
        with app_user_context(owner):
            runnable = [d for d in device_ids if device_state.get(d, {}).get("status") == "pending"]
            if not runnable:
                _finalize_upgrade_job(job_id, device_ids)
                return

            def _do_one(did):
                with app_user_context(owner):
                    plan = device_plans.get(did, {})
                    up_type = plan.get("upgrade_type", upgrade_type)
                    comps = plan.get("components", components)
                    comps_upper = {x.upper() for x in comps}
                    dev_url_list = [(c, u) for c, u in url_list if c.upper() in comps_upper]
                    ssh_host = ssh_hosts.get(did, "") if isinstance(ssh_hosts, dict) else ""
                    mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(did, ssh_host)
                    deploy_params = plan.get("deploy_params", {})

                    # Wave 2.1: per-device serialization. If another user
                    # is pushing config or upgrading the same device we
                    # wait here rather than colliding on the CLI.
                    def _on_queued(holder):
                        holder_owner = (holder or {}).get("owner") or "another user"
                        holder_op = (holder or {}).get("op") or "operation"
                        msg = _format_upgrade_terminal_line(
                            "INFO",
                            f"({mgmt_ip}) busy: queued behind {holder_owner}'s {holder_op}...",
                            did,
                        )
                        with _push_jobs_lock:
                            if job_id in _push_jobs:
                                _push_jobs[job_id]["terminal_lines"].append(msg)
                                ds = _push_jobs[job_id].get("device_state", {})
                                if did in ds:
                                    ds[did]["status"] = "queued"

                    # Wave 4.3: periodic queue-position update while we wait.
                    def _on_progress(info):
                        pos = (info or {}).get("position", 0)
                        total = (info or {}).get("total", 0)
                        elapsed = (info or {}).get("elapsed_s", 0.0)
                        msg = _format_upgrade_terminal_line(
                            "INFO",
                            f"queue position {pos}/{total} (waiting {elapsed:.0f}s)",
                            did,
                        )
                        with _push_jobs_lock:
                            if job_id in _push_jobs:
                                _push_jobs[job_id]["terminal_lines"].append(msg)
                                ds = _push_jobs[job_id].get("device_state", {})
                                if did in ds:
                                    ds[did]["queue_position"] = pos
                                    ds[did]["queue_total"] = total

                    # Wave 4.1: gate on global upgrade slot BEFORE device lock.
                    def _on_global_queued(info):
                        qlen = (info or {}).get("queue_len", 0)
                        in_flight = (info or {}).get("in_flight", 0)
                        smax = (info or {}).get("slots_max", 0)
                        msg = _format_upgrade_terminal_line(
                            "INFO",
                            f"waiting for global upgrade slot ({qlen} ahead, {in_flight}/{smax} running)...",
                            did,
                        )
                        with _push_jobs_lock:
                            if job_id in _push_jobs:
                                _push_jobs[job_id]["terminal_lines"].append(msg)
                                ds = _push_jobs[job_id].get("device_state", {})
                                if did in ds:
                                    ds[did]["status"] = "queued_global"

                    with _device_scheduler.global_upgrade_slot(
                        op="upgrade", owner=owner, job_id=job_id,
                        on_queued=_on_global_queued,
                    ):
                        with _device_scheduler.exclusive(
                            mgmt_ip, "upgrade", owner, job_id,
                            on_queued=_on_queued,
                            on_progress=_on_progress,
                        ):
                            _run_device_upgrade(
                                job_id, did, mgmt_ip, user, password, dev_url_list,
                                upgrade_type=up_type, deploy_params=deploy_params,
                                scaler_hostname=scaler_id or did,
                            )

            with ThreadPoolExecutor(max_workers=max_concurrent) as pool:
                futures = {pool.submit(_do_one, did): did for did in runnable}
                for f in as_completed(futures):
                    try:
                        f.result()
                    except Exception as e:
                        did = futures[f]
                        with _push_jobs_lock:
                            if job_id in _push_jobs and did in _push_jobs[job_id].get("device_state", {}):
                                _push_jobs[job_id]["device_state"][did]["status"] = "failed"
                                _push_jobs[job_id]["device_state"][did]["error"] = str(e)
                                _push_jobs[job_id]["terminal_lines"].append(
                                    _format_upgrade_terminal_line("ERROR", str(e), did))

            _finalize_upgrade_job(job_id, device_ids)

    _save_active_upgrade(job_id, _push_jobs[job_id])

    # Wave 6.2: submit to the bounded upgrade pool instead of spawning
    # a fresh OS thread. Upgrades are long-running; the pool reuses
    # workers across jobs and caps total live threads.
    from routes._worker_pool import submit_upgrade
    submit_upgrade(_run_upgrade)

    return {
        "job_id": job_id,
        "status": "started",
        "message": f"Upgrade started on {len(device_ids)} devices",
        "devices": device_ids,
    }


def _find_existing_branch_job(branch: str, job_types=("wait_and_upgrade", "build_monitor")):
    """Find an active (non-done) job for the same branch to avoid duplicates."""
    from urllib.parse import unquote
    norm = branch
    for _ in range(5):
        d = unquote(norm)
        if d == norm:
            break
        norm = d
    with _push_jobs_lock:
        for jid, job in _push_jobs.items():
            if job.get("done") or job.get("status") in ("completed", "failed", "cancelled"):
                continue
            if job.get("job_type") not in job_types:
                continue
            jb = job.get("branch", "")
            jb_norm = jb
            for _ in range(5):
                d = unquote(jb_norm)
                if d == jb_norm:
                    break
                jb_norm = d
            if jb_norm == norm:
                return jid, job
    return None, None


@router.post("/api/operations/image-upgrade/trigger-build")
def image_upgrade_trigger_build(body: dict, request: Request = None):
    """Trigger a Jenkins build and start backend monitoring.

    Accepts optional device_ids + ssh_hosts for auto-push after build succeeds.
    The monitor thread polls Jenkins every 30s, updates a _push_jobs entry so
    the existing job watcher on the frontend sees it automatically.
    """
    import uuid
    import threading
    from datetime import datetime

    owner = _get_request_user(request) if request else "default"

    branch = body.get("branch", "").strip()
    with_baseos = body.get("with_baseos", True)
    qa_version = body.get("qa_version", False)
    with_sanitizer = body.get("with_sanitizer", False)
    device_ids = body.get("device_ids", [])
    ssh_hosts = body.get("ssh_hosts", {})
    auto_push = body.get("auto_push", False)
    components = body.get("components", ["DNOS", "GI", "BaseOS"])
    if not branch:
        raise HTTPException(status_code=400, detail="branch is required")

    existing_id, existing_job = _find_existing_branch_job(branch)
    if existing_id:
        existing_type = existing_job.get("job_type", "")
        with _push_jobs_lock:
            if existing_id in _push_jobs:
                _push_jobs[existing_id]["terminal_lines"].append(
                    f"[INFO] New build trigger requested -- reusing this job")
        return {
            "success": True,
            "message": f"Already monitoring this branch ({existing_type}: {existing_id})",
            "job_id": existing_id,
            "branch": branch,
            "reused": True,
        }

    from scaler.jenkins_integration import JenkinsClient
    try:
        jenkins = JenkinsClient()
        success, message = jenkins.trigger_build(
            branch, with_baseos=with_baseos, qa_version=qa_version,
            with_sanitizer=with_sanitizer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Jenkins connection failed: {e}")
    if not success:
        raise HTTPException(status_code=500, detail=message)

    job_id = f"build-{str(uuid.uuid4())[:8]}"
    from urllib.parse import unquote
    display_branch = branch
    for _ in range(5):
        decoded = unquote(display_branch)
        if decoded == display_branch:
            break
        display_branch = decoded
    with _push_jobs_lock:
        _push_jobs[job_id] = {
            "job_id": job_id,
            "job_type": "build_monitor",
            "owner": owner,
            "status": "running",
            "phase": "build_queued",
            "message": f"Build triggered for {display_branch}",
            "percent": 5,
            "success": False,
            "done": False,
            "terminal_lines": [f"[INFO] Build triggered for {display_branch}"],
            "job_name": f"Image build {display_branch}",
            "device_id": device_ids[0] if len(device_ids) == 1 else "",
            "devices": device_ids,
            "started_at": datetime.utcnow().isoformat() + "Z",
            "branch": branch,
            "with_baseos": with_baseos,
            "with_sanitizer": with_sanitizer,
            "auto_push": auto_push and len(device_ids) > 0,
            "ssh_hosts": ssh_hosts,
            "components": components,
            "build_number": None,
            "image_urls": {},
        }

    def _monitor_build():
        import time
        poll_interval = 30
        max_wait = 7200
        started = time.time()

        try:
            build_number = jenkins.wait_for_build_start(branch, timeout=300, poll_interval=10)
            if build_number:
                with _push_jobs_lock:
                    if job_id in _push_jobs:
                        _push_jobs[job_id]["build_number"] = build_number
                        _push_jobs[job_id]["phase"] = "building"
                        _push_jobs[job_id]["message"] = f"Build #{build_number} in progress"
                        _push_jobs[job_id]["percent"] = 10
                        _push_jobs[job_id]["terminal_lines"].append(
                            f"[INFO] Build #{build_number} started")
            else:
                with _push_jobs_lock:
                    if job_id in _push_jobs:
                        _push_jobs[job_id]["terminal_lines"].append(
                            "[WARN] Could not detect build number, polling latest")

            while time.time() - started < max_wait:
                try:
                    build = jenkins.get_build_info(branch, latest=True)
                    if not build:
                        time.sleep(poll_interval)
                        continue

                    elapsed_min = int((time.time() - started) / 60)
                    if build.building:
                        pct = min(10 + int(elapsed_min * 1.5), 85)
                        with _push_jobs_lock:
                            if job_id in _push_jobs:
                                _push_jobs[job_id]["phase"] = "building"
                                _push_jobs[job_id]["message"] = (
                                    f"Build #{build.build_number} running ({elapsed_min}m)")
                                _push_jobs[job_id]["percent"] = pct
                                _push_jobs[job_id]["build_number"] = build.build_number
                    else:
                        build_ok = build.result == "SUCCESS"
                        with _push_jobs_lock:
                            if job_id in _push_jobs:
                                _push_jobs[job_id]["build_number"] = build.build_number
                                _push_jobs[job_id]["percent"] = 90 if build_ok else 100
                                _push_jobs[job_id]["terminal_lines"].append(
                                    f"[{'OK' if build_ok else 'FAIL'}] Build #{build.build_number}"
                                    f" finished: {build.result}")

                        if build_ok:
                            _resolve_and_maybe_push(job_id, branch, build.build_number,
                                                    jenkins, components)
                        else:
                            with _push_jobs_lock:
                                if job_id in _push_jobs:
                                    _push_jobs[job_id]["status"] = "failed"
                                    _push_jobs[job_id]["phase"] = "build_failed"
                                    _push_jobs[job_id]["message"] = (
                                        f"Build #{build.build_number} failed: {build.result}")
                                    _push_jobs[job_id]["done"] = True
                            _persist_job_if_done(job_id)
                        return
                except Exception as poll_err:
                    with _push_jobs_lock:
                        if job_id in _push_jobs:
                            _push_jobs[job_id]["terminal_lines"].append(
                                f"[WARN] Poll error: {poll_err}")
                time.sleep(poll_interval)

            with _push_jobs_lock:
                if job_id in _push_jobs:
                    _push_jobs[job_id]["status"] = "failed"
                    _push_jobs[job_id]["phase"] = "timeout"
                    _push_jobs[job_id]["message"] = "Build monitor timed out (2h)"
                    _push_jobs[job_id]["done"] = True
            _persist_job_if_done(job_id)

        except Exception as e:
            import traceback
            traceback.print_exc()
            with _push_jobs_lock:
                if job_id in _push_jobs:
                    _push_jobs[job_id]["status"] = "failed"
                    _push_jobs[job_id]["phase"] = "error"
                    _push_jobs[job_id]["message"] = f"Monitor error: {e}"
                    _push_jobs[job_id]["done"] = True
                    _push_jobs[job_id]["terminal_lines"].append(f"[ERROR] {e}")
            _persist_job_if_done(job_id)

    with _push_jobs_lock:
        _save_active_build(job_id, _push_jobs[job_id])

    from routes._worker_pool import submit_upgrade
    submit_upgrade(_monitor_build)
    return {"success": True, "message": message, "job_id": job_id, "branch": branch}


def _resolve_and_maybe_push(job_id: str, branch: str, build_number: int,
                            jenkins, components: list):
    """After a successful build, resolve image URLs and optionally auto-push."""
    from scaler.jenkins_integration import validate_artifact_url

    urls = {}
    try:
        stack_urls = jenkins.get_stack_urls(branch, build_number)
        for comp in ["dnos", "gi", "baseos"]:
            url = stack_urls.get(comp)
            if url:
                ok, msg = validate_artifact_url(url, timeout=10)
                urls[comp] = {"url": url, "valid": ok, "detail": msg}
    except Exception as e:
        with _push_jobs_lock:
            if job_id in _push_jobs:
                _push_jobs[job_id]["terminal_lines"].append(
                    f"[WARN] Could not resolve image URLs: {e}")

    with _push_jobs_lock:
        job = _push_jobs.get(job_id)
        if not job:
            return
        job["image_urls"] = urls
        valid_urls = {k: v for k, v in urls.items() if v.get("valid")}
        url_summary = ", ".join(f"{k.upper()}" for k in valid_urls)
        job["terminal_lines"].append(
            f"[INFO] Valid images: {url_summary or 'none'}")

        if not valid_urls:
            job["status"] = "completed"
            job["phase"] = "build_complete_no_images"
            job["message"] = "Build succeeded but images expired or unavailable"
            job["done"] = True
            job["percent"] = 100
            _persist_job_if_done(job_id)
            return

        auto_push = job.get("auto_push", False)
        device_ids = job.get("devices", [])

        if auto_push and device_ids:
            job["phase"] = "auto_push_starting"
            job["message"] = f"Auto-pushing to {len(device_ids)} device(s)..."
            job["percent"] = 92
        else:
            job["status"] = "completed"
            job["phase"] = "build_complete"
            job["message"] = f"Build ready. Images: {url_summary}"
            job["done"] = True
            job["success"] = True
            job["percent"] = 100

    if auto_push and device_ids:
        try:
            _auto_push_upgrade(job_id, valid_urls, device_ids,
                               _push_jobs.get(job_id, {}).get("ssh_hosts", {}),
                               components)
        except Exception as e:
            import traceback
            traceback.print_exc()
            with _push_jobs_lock:
                if job_id in _push_jobs:
                    _push_jobs[job_id]["status"] = "failed"
                    _push_jobs[job_id]["phase"] = "auto_push_error"
                    _push_jobs[job_id]["message"] = f"Auto-push error: {e}"
                    _push_jobs[job_id]["done"] = True
                    _push_jobs[job_id]["terminal_lines"].append(f"[ERROR] Auto-push failed: {e}")
            _persist_job_if_done(job_id)
    else:
        _persist_job_if_done(job_id)


def _auto_push_upgrade(job_id: str, valid_urls: dict, device_ids: list,
                       ssh_hosts: dict, components: list,
                       device_plans: dict = None, max_concurrent: int = 3):
    """Push resolved images to devices. Supports per-device plans and parallel execution.

    Always runs inside a daemon thread (from `_monitor_build` or
    `_wait_then_upgrade`). We read `owner` from the job dict and re-bind
    `current_app_user` via `app_user_context` so `_get_credentials()`
    resolves to the owner's per-user device store.
    """
    from datetime import datetime
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from routes._state import app_user_context

    device_plans = device_plans or {}
    max_concurrent = max(1, min(max_concurrent, 10))

    # Resolve owner from the job dict -- set at job creation time by the
    # originating REST handler (see `image_upgrade_trigger_build` /
    # `wait_and_upgrade`).
    with _push_jobs_lock:
        owner = (_push_jobs.get(job_id, {}) or {}).get("owner", "default")

    with app_user_context(owner):
        user, password = _get_credentials()
        url_list = []
        for comp in ["dnos", "gi", "baseos"]:
            if comp.upper() in [c.upper() for c in components] and comp in valid_urls:
                url_list.append((comp.upper(), valid_urls[comp]["url"]))

        # Pre-validate URLs before pushing to devices
        import requests as _req
        for comp_name, comp_url in url_list:
            try:
                head_resp = _req.head(comp_url, timeout=10, allow_redirects=True)
                if head_resp.status_code == 404:
                    raise RuntimeError(
                        f"{comp_name} image not found (HTTP 404) -- build artifacts expired. "
                        f"Trigger a new build.")
                elif head_resp.status_code >= 400:
                    raise RuntimeError(
                        f"{comp_name} image returned HTTP {head_resp.status_code}")
            except _req.exceptions.ConnectionError:
                raise RuntimeError(f"{comp_name} image server unreachable")
            except _req.exceptions.Timeout:
                raise RuntimeError(f"{comp_name} image server timed out")
            except RuntimeError:
                raise
            except Exception:
                pass

        with _push_jobs_lock:
            if job_id in _push_jobs:
                url_names = ", ".join(f"{c}" for c, _ in url_list)
                _push_jobs[job_id]["terminal_lines"].append(
                    _format_upgrade_terminal_line(
                        "INFO",
                        f"Starting upgrade push to {len(device_ids)} device(s) ({url_names})",
                    ))
                if "device_state" not in _push_jobs[job_id]:
                    _push_jobs[job_id]["device_state"] = {}
                for did in device_ids:
                    plan = device_plans.get(did, {})
                    up_type = plan.get("upgrade_type", "normal")
                    comps = plan.get("components", components)
                    if up_type in ("blocked", "skip"):
                        _push_jobs[job_id]["device_state"][did] = {
                            "status": "skipped",
                            "phase": "blocked" if up_type == "blocked" else "at_target",
                            "percent": 100 if up_type == "skip" else 0,
                            "message": plan.get("reason", "Skipped"),
                            "upgrade_type": up_type, "components": comps,
                            "error": plan.get("reason") if up_type == "blocked" else None,
                            "started_at": datetime.utcnow().isoformat() + "Z",
                            "completed_at": datetime.utcnow().isoformat() + "Z",
                        }
                    else:
                        _push_jobs[job_id]["device_state"][did] = {
                            "status": "pending", "phase": "queued", "percent": 0,
                            "message": "Waiting...",
                            "upgrade_type": up_type, "components": comps,
                            "error": None, "started_at": None, "completed_at": None,
                        }

        runnable = [d for d in device_ids
                    if _push_jobs.get(job_id, {}).get("device_state", {}).get(d, {}).get("status") == "pending"]
        if not runnable:
            _finalize_upgrade_job(job_id, device_ids)
            return

        def _do_one(did):
            # ThreadPoolExecutor spawns worker threads with empty
            # ContextVars; re-enter the owner context per device.
            with app_user_context(owner):
                plan = device_plans.get(did, {})
                up_type = plan.get("upgrade_type", "normal")
                comps = plan.get("components", components)
                comps_upper = {x.upper() for x in comps}
                dev_url_list = [(c, u) for c, u in url_list if c.upper() in comps_upper]
                ssh_host = ssh_hosts.get(did, "") if isinstance(ssh_hosts, dict) else ""
                mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(did, ssh_host)
                deploy_params = plan.get("deploy_params", {})

                # Wave 2.1: per-device serialization (see image_upgrade_execute).
                def _on_queued(holder):
                    holder_owner = (holder or {}).get("owner") or "another user"
                    holder_op = (holder or {}).get("op") or "operation"
                    msg = _format_upgrade_terminal_line(
                        "INFO",
                        f"({mgmt_ip}) busy: queued behind {holder_owner}'s {holder_op}...",
                        did,
                    )
                    with _push_jobs_lock:
                        if job_id in _push_jobs:
                            _push_jobs[job_id]["terminal_lines"].append(msg)
                            ds = _push_jobs[job_id].get("device_state", {})
                            if did in ds:
                                ds[did]["status"] = "queued"

                # Wave 4.3: periodic queue-position update while we wait.
                def _on_progress(info):
                    pos = (info or {}).get("position", 0)
                    total = (info or {}).get("total", 0)
                    elapsed = (info or {}).get("elapsed_s", 0.0)
                    msg = _format_upgrade_terminal_line(
                        "INFO",
                        f"queue position {pos}/{total} (waiting {elapsed:.0f}s)",
                        did,
                    )
                    with _push_jobs_lock:
                        if job_id in _push_jobs:
                            _push_jobs[job_id]["terminal_lines"].append(msg)
                            ds = _push_jobs[job_id].get("device_state", {})
                            if did in ds:
                                ds[did]["queue_position"] = pos
                                ds[did]["queue_total"] = total

                # Wave 4.1: gate on global upgrade slot BEFORE device lock.
                def _on_global_queued(info):
                    qlen = (info or {}).get("queue_len", 0)
                    in_flight = (info or {}).get("in_flight", 0)
                    smax = (info or {}).get("slots_max", 0)
                    msg = _format_upgrade_terminal_line(
                        "INFO",
                        f"waiting for global upgrade slot ({qlen} ahead, {in_flight}/{smax} running)...",
                        did,
                    )
                    with _push_jobs_lock:
                        if job_id in _push_jobs:
                            _push_jobs[job_id]["terminal_lines"].append(msg)
                            ds = _push_jobs[job_id].get("device_state", {})
                            if did in ds:
                                ds[did]["status"] = "queued_global"

                with _device_scheduler.global_upgrade_slot(
                    op="upgrade", owner=owner, job_id=job_id,
                    on_queued=_on_global_queued,
                ):
                    with _device_scheduler.exclusive(
                        mgmt_ip, "upgrade", owner, job_id,
                        on_queued=_on_queued,
                        on_progress=_on_progress,
                    ):
                        _run_device_upgrade(
                            job_id, did, mgmt_ip, user, password, dev_url_list,
                            upgrade_type=up_type, deploy_params=deploy_params,
                            scaler_hostname=scaler_id or did,
                        )

        with ThreadPoolExecutor(max_workers=max_concurrent) as pool:
            futures = {pool.submit(_do_one, did): did for did in runnable}
            for f in as_completed(futures):
                try:
                    f.result()
                except Exception as e:
                    did = futures[f]
                    with _push_jobs_lock:
                        if job_id in _push_jobs and did in _push_jobs[job_id].get("device_state", {}):
                            _push_jobs[job_id]["device_state"][did]["status"] = "failed"
                            _push_jobs[job_id]["device_state"][did]["error"] = str(e)
                            _push_jobs[job_id]["terminal_lines"].append(
                                _format_upgrade_terminal_line("ERROR", str(e), did))

        _finalize_upgrade_job(job_id, device_ids)


def _update_device_state(job_id: str, device_id: str, **kwargs):
    """Thread-safe update of per-device state.

    Enforces monotonic progress on the ``percent`` field for jobs that
    remain in a running/pending phase. The recovery loop and the GI-deploy
    retry loop naturally step back (e.g. deploy failed, restart image
    load) -- the CLI counts each new attempt as a fresh phase, but in the
    UI a percent bar that suddenly drops from 97% to 55% looks broken.
    We only accept a percent decrease when:

    * a terminal status is being set (``completed`` / ``failed`` /
      ``cancelled`` -- these reset to 100 or stay as explicit values);
    * no prior percent exists (first write for that device).

    All other regressions are clamped to the previously-seen maximum.
    The device_state dict keeps both ``percent`` (displayed) and
    ``_percent_raw`` (the latest raw value for debugging).
    """
    should_persist = False
    with _push_jobs_lock:
        if job_id not in _push_jobs:
            return
        ds = _push_jobs[job_id].get("device_state", {})
        if device_id not in ds:
            return
        current = ds[device_id]
        new_kwargs = dict(kwargs)
        if "percent" in new_kwargs:
            incoming = new_kwargs["percent"]
            incoming_status = (new_kwargs.get("status") or "").lower()
            terminal = incoming_status in ("completed", "failed", "cancelled", "canceled", "skipped")
            try:
                incoming_int = int(incoming)
            except Exception:
                incoming_int = None
            if incoming_int is not None and not terminal:
                prev = current.get("percent", 0)
                try:
                    prev_int = int(prev)
                except Exception:
                    prev_int = 0
                if incoming_int < prev_int:
                    new_kwargs["_percent_raw"] = incoming_int
                    new_kwargs["percent"] = prev_int
                else:
                    new_kwargs["_percent_raw"] = incoming_int
        current.update(new_kwargs)
        job_type = (_push_jobs[job_id].get("job_type") or "").lower()
        should_persist = job_type in ("upgrade", "wait_and_upgrade", "build_monitor")
    if should_persist:
        _persist_active_job_snapshot(job_id)


def _persist_active_job_snapshot(job_id: str):
    """Persist an in-flight job snapshot so startup can resume monitoring.

    The bridge process can be killed while an upgrade is between deploy and
    config-repair. A lightweight snapshot after each phase change gives the
    startup recovery code the last known device phase without inventing a new
    state file.
    """
    try:
        with _push_jobs_lock:
            job = _push_jobs.get(job_id)
            if not job or job.get("done"):
                return
            job_type = (job.get("job_type") or "").lower()
            snapshot = dict(job)
        if job_type == "build_monitor":
            _save_active_build(job_id, snapshot)
        elif job_type in ("upgrade", "wait_and_upgrade"):
            _save_active_upgrade(job_id, snapshot)
    except Exception:
        pass


class _UpgradeCancelled(Exception):
    """Raised when an upgrade job is cancelled by the user."""
    pass


class _GiCliReconnectRequired(RuntimeError):
    """Raised when the virsh chain is back at the KVM host shell."""
    pass


def _check_upgrade_cancel(job_id: str):
    """Check if an upgrade job has been cancelled. Raises _UpgradeCancelled if so."""
    with _push_jobs_lock:
        job = _push_jobs.get(job_id, {})
        if job.get("_cancel_requested") or job.get("status") == "cancelling":
            raise _UpgradeCancelled(f"Upgrade cancelled by user")


def _run_device_upgrade(job_id: str, device_id: str, mgmt_ip: str,
                        user: str, password: str, url_list: list,
                        upgrade_type: str = "normal", deploy_params: dict = None,
                        scaler_hostname: str = ""):
    """SSH to a device and perform upgrade. Supports normal, delete_deploy, gi_deploy.

    delete_deploy flow:
      1. SSH connect, snapshot config, detect deploy params (system_type, ncc_id)
      2. request system delete + yes
      3. Wait for GI mode via connect_for_upgrade (console/virsh/SSH)
      4. Load images in GI mode
      5. request system deploy

    normal flow:
      1. SSH connect, snapshot config
      2. Load images via target-stack load
      3. Pre-check + install

    gi_deploy flow:
      1. Connect via connect_for_upgrade (device already in GI)
      2. Load images
      3. request system deploy

    scaler_hostname: canonical hostname for connect_for_upgrade (e.g. "RR-SA-2").
    Falls back to device_id if not provided.
    """
    import time
    import paramiko
    from datetime import datetime

    deploy_params = deploy_params or {}
    scaler_hostname = scaler_hostname or device_id
    if scaler_hostname:
        # Atomic identity canon: collapse aliases/serial to the single canonical
        # config-device dir so pre-config backups + operational.json are saved
        # under ONE identity (e.g. YOR_PE-1 -> PE-1), never a pseudo-identity dir.
        scaler_hostname = _resolve_config_dir(scaler_hostname) or scaler_hostname
    # --- Auto-detect device mode from operational.json ---
    # If upgrade_type is "normal" but device is actually in GI mode,
    # switch to gi_deploy so we use the correct flow (deploy instead of install).
    _op_data_cached = {}
    try:
        _dp_dir = _resolve_config_dir(scaler_hostname)
        _dp_path = Path(SCALER_ROOT) / "db" / "configs" / _dp_dir / "operational.json"
        if _dp_path.exists():
            _op_data_cached = _read_ops_safe(_dp_path)
        else:
            import logging
            logging.warning(f"[UPGRADE] {device_id}: operational.json not found at {_dp_path}")
    except Exception as _ope:
        import logging
        logging.error(f"[UPGRADE] {device_id}: Failed to load operational.json: {_ope}")
    if upgrade_type == "normal" and _op_data_cached:
        _detected_state = (_op_data_cached.get("device_state") or "").upper()
        from scaler.connection_strategy import classify_device_state
        _classified = classify_device_state(_detected_state)
        # GI / RECOVERY -> delete_deploy (NOT gi_deploy). delete_deploy is
        # resume-safe: it skips `request system delete` when the device is
        # already in GI/BASEOS_SHELL and goes straight to load+deploy, while a
        # plain gi_deploy is refused by GI_RECOVERY for a NEW build (it only
        # permits a revert to the on-box stack). Routing GI/RECOVERY through
        # delete_deploy therefore handles both a real in-DNOS wipe and the
        # already-in-GI resume, and avoids the "GI_RECOVERY won't load a new
        # build" dead-end. (2026-06-28)
        if _classified in ("GI", "RECOVERY"):
            upgrade_type = "delete_deploy"
    # --- Major version jump detection (v25->v26 etc) requires delete_deploy ---
    if upgrade_type == "normal" and _op_data_cached:
        _cur_dnos = _op_data_cached.get("dnos_version") or ""
        _cur_major_m = re.match(r"(\d+)\.", _cur_dnos)
        _tgt_dnos_url = next((u for c, u in url_list if c.upper() == "DNOS"), "")
        _tgt_ver = _extract_version_from_dnos_url(_tgt_dnos_url) if _tgt_dnos_url else ""
        _tgt_major_m = re.match(r"(\d+)\.", _tgt_ver)
        if _cur_major_m and _tgt_major_m:
            _cur_maj = int(_cur_major_m.group(1))
            _tgt_maj = int(_tgt_major_m.group(1))
            if _cur_maj != _tgt_maj:
                import logging
                logging.warning(
                    f"[UPGRADE] {device_id}: Major version jump detected "
                    f"(v{_cur_maj} -> v{_tgt_maj}), forcing delete_deploy")
                upgrade_type = "delete_deploy"
    # --- Branch-lineage change detection (same major train) requires
    #     delete_deploy. A private feature branch (e.g.
    #     26.2.0.9_priv.usirota_evpn_vpls_irb_9) forks off an OLDER base than
    #     mainline (26.2.0.543_dev.dev_v26_2_1402) and carries a different
    #     package/stack set, so a "normal" in-DNOS install ACROSS lineages is
    #     unsafe/inconsistent (mismatched packages, partial install). A wipe +
    #     deploy is the only clean cross-branch transition. Same-branch build
    #     bumps (priv 8 -> priv 9, dev 1402 -> dev 1500) stay "normal".
    #     Reuses StackManager.detect_branch_switch -- the SAME function the GUI
    #     planner (image_upgrade_plan) uses -- so preview and runtime agree. ---
    if upgrade_type == "normal" and _op_data_cached:
        try:
            from scaler.stack_manager import StackManager
            _cur_label = (_op_data_cached.get("dnos_version")
                          or _op_data_cached.get("git_commit") or "")
            _tgt_dnos_url2 = next((u for c, u in url_list if c.upper() == "DNOS"), "")
            _tgt_label = _dnos_url_to_version_label(_tgt_dnos_url2)
            if _cur_label and _tgt_label:
                _is_switch, _cur_br, _tgt_br = StackManager.detect_branch_switch(
                    _cur_label, _tgt_label, "")
                if _is_switch:
                    import logging
                    logging.warning(
                        f"[UPGRADE] {device_id}: Branch-lineage change detected "
                        f"('{_cur_br}' -> '{_tgt_br}'), forcing delete_deploy "
                        f"(cross-branch jump, not a same-branch build bump)")
                    upgrade_type = "delete_deploy"
        except Exception as _bse:
            import logging
            logging.warning(
                f"[UPGRADE] {device_id}: branch-lineage check skipped: {_bse}")
    # --- Private feature-branch target -> delete_deploy (2026-06-28) -------
    #     A private build (label contains `_priv.`, e.g.
    #     26.2.0.15_priv.usirota_evpn_vpls_irb_15) forks off an older base
    #     with a divergent package/stack set. An in-DNOS `normal` install onto
    #     a private lineage -- even a same-branch build bump -- has repeatedly
    #     left devices stuck/non-converged (build-12 incident, PE-1/PE-4/
    #     RR-SA-2). The clean transition onto ANY private build is a full
    #     delete+deploy (config taken pre-delete, restored post-deploy).
    #     Operators can still force another method with an explicit --method.
    if upgrade_type == "normal" and url_list:
        try:
            from scaler.stack_manager import StackManager
            _tgt_dnos_url3 = next((u for c, u in url_list if c.upper() == "DNOS"), "")
            _tgt_label3 = _dnos_url_to_version_label(_tgt_dnos_url3) if _tgt_dnos_url3 else ""
            if StackManager.target_is_private_branch(_tgt_label3):
                import logging
                logging.warning(
                    f"[UPGRADE] {device_id}: target '{_tgt_label3}' is a PRIVATE "
                    f"feature-branch build, forcing delete_deploy (in-DNOS "
                    f"install across a private lineage is unsafe)")
                upgrade_type = "delete_deploy"
        except Exception as _pbe:
            import logging
            logging.warning(
                f"[UPGRADE] {device_id}: private-branch check skipped: {_pbe}")
    # --- Fill deploy_params via the single shared normaliser ---
    # One call here replaces three previously-duplicated fill sites.
    # Crucially, ncc_id is normalised unconditionally -- the old code
    # gated that fill behind `if not deploy_params.get("system_type"):`,
    # so a wizard payload that supplied system_type but left
    # `ncc_id=null` skipped the fill and propagated None all the way
    # into `f"ncc-id {ncc_id}"`. Scaler CLI's pattern
    # (`conn.get('ncc_id') if conn.get('ncc_id') is not None else 0`)
    # is now centralised in `_normalize_deploy_params` + `_safe_ncc_id`.
    _normalize_deploy_params(
        deploy_params,
        op_data_cached=_op_data_cached,
        scaler_hostname=scaler_hostname,
        device_id=device_id,
    )
    components = [comp for comp, _ in url_list]
    device_mode = "DNOS"
    current_version = ""
    target_version = ""
    stage_times = {}
    t_start = time.time()

    with _push_jobs_lock:
        ds = _push_jobs.get(job_id, {}).get("device_state", {}).get(device_id, {})
        device_mode = ds.get("mode", "DNOS") or "DNOS"
        current_version = ds.get("current_version", "")
        target_version = ds.get("target_version", "")

    # Platform (system_type) comes from three possible sources, in
    # priority order: wizard-resolved deploy_params (authoritative for
    # deploy flows), scaler operational cache, and the in-progress job's
    # device_plan snapshot. Passed to the estimator so a brand-new
    # device of a known platform family gets a "same_platform" hint
    # instead of being averaged across cluster + single-box hardware.
    est_system_type = ""
    try:
        if isinstance(deploy_params, dict):
            est_system_type = str(deploy_params.get("system_type") or "").strip()
        if not est_system_type and isinstance(_op_data_cached, dict):
            est_system_type = str(_op_data_cached.get("system_type") or "").strip()
        if not est_system_type:
            with _push_jobs_lock:
                dp = (_push_jobs.get(job_id, {}) or {}).get("device_plans", {}).get(device_id, {}) or {}
                dp_sys = (dp.get("deploy_params") or {}).get("system_type") or dp.get("system_type") or ""
                est_system_type = str(dp_sys or "").strip()
        # "N/A" is operational.json's placeholder for "not detected";
        # treat it as unknown so the estimator falls back to the generic
        # pool rather than building a `platform|N/A|...` bucket.
        if est_system_type.upper() in ("", "N/A", "NONE"):
            est_system_type = ""
    except Exception:
        est_system_type = ""

    try:
        from scaler.config_pusher import get_upgrade_time_estimate
        est = get_upgrade_time_estimate(
            upgrade_type=upgrade_type,
            components=components,
            device_mode=device_mode,
            device_hostname=device_id,
            system_type=est_system_type,
        )
        est_seconds = est.get("total", 180)
        est_source = est.get("source", "default")
        est_confidence = est.get("confidence", "low")
        est_hint = ""
        if est_source == "same_platform" and est.get("platform"):
            est_hint = f", platform={est.get('platform')}"
        elif est_source == "same_device":
            est_hint = f", n={est.get('count', 0)}"
        with _push_jobs_lock:
            if job_id in _push_jobs:
                prev_est = _push_jobs[job_id].get("estimated_total_seconds")
                if prev_est is None:
                    _push_jobs[job_id]["estimated_total_seconds"] = est_seconds
                _push_jobs[job_id]["terminal_lines"].append(
                    f"[INFO] {device_id}: Estimated time: {int(est_seconds)}s ({est_source}, {est_confidence} confidence{est_hint})")
    except Exception:
        est_seconds = 180

    _update_device_state(job_id, device_id, status="running", phase="connecting",
                         message="Connecting...", started_at=datetime.utcnow().isoformat() + "Z")

    # Sync KVM cluster config from console_mappings into operational.json
    # so connect_for_upgrade has all connection paths available during upgrade
    try:
        import json as _json
        from scaler.connection_strategy import get_console_config_for_device, _load_console_mappings
        mappings = _load_console_mappings()
        ncc_info = mappings.get('cluster_ncc_access', {}).get(scaler_hostname)
        if ncc_info and ncc_info.get('ncc_type') == 'kvm':
            op_file = Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname / "operational.json"
            op_file.parent.mkdir(parents=True, exist_ok=True)
            from routes._ops_writer import update_ops as _uops_kvm

            def _mut_kvm(op_data, _ncc=ncc_info):
                if not op_data.get('ncc_type'):
                    op_data['ncc_type'] = _ncc.get('ncc_type')
                    op_data['kvm_host'] = _ncc.get('kvm_host')
                    op_data['kvm_host_ip'] = _ncc.get('kvm_host_ip')
                    op_data['kvm_host_credentials'] = _ncc.get('kvm_host_credentials', {})
                    op_data['ncc_vms'] = _ncc.get('ncc_vms', [])
                    op_data['ncc_console_credentials'] = _ncc.get('ncc_console_credentials', {})
                    op_data['dncli_credentials'] = _ncc.get('dncli_credentials', {})
                if not op_data.get('ncc_mgmt_ip'):
                    _vip = (_ncc.get('mgmt_vip') or '').strip()
                    _ssh = (op_data.get('ssh_host') or '').strip().split('/')[0]
                    op_data['ncc_mgmt_ip'] = _vip or _ssh or ''

            _uops_kvm(op_file, _mut_kvm, create_if_missing=True)
    except Exception:
        pass

    # Re-merge operational.json after console_mappings may have added ncc_type/kvm fields
    try:
        _seen_dirs = []
        _merged = dict(_op_data_cached)
        for _d in (_resolve_config_dir(scaler_hostname), scaler_hostname):
            if not _d or _d in _seen_dirs:
                continue
            _seen_dirs.append(_d)
            _op_r = Path(SCALER_ROOT) / "db" / "configs" / _d / "operational.json"
            if _op_r.exists():
                _merged.update(_read_ops_safe(_op_r))
        _op_data_cached = _merged
    except Exception:
        pass

    # Second normalisation pass: picks up `deploy_ncc_id` / `ncc_type`
    # /`ncc_mgmt_ip` entries that the re-merge just added. Idempotent,
    # so we can call it freely whenever op_data changes.
    _normalize_deploy_params(
        deploy_params,
        op_data_cached=_op_data_cached,
        scaler_hostname=scaler_hostname,
        device_id=device_id,
    )

    def _log(level, msg):
        with _push_jobs_lock:
            if job_id in _push_jobs:
                _push_jobs[job_id]["terminal_lines"].append(
                    _format_upgrade_terminal_line(level, msg, device_id))

    _log("INFO", f"upgrade_type={upgrade_type}, system_type={deploy_params.get('system_type','?')}, "
         f"deploy_name={deploy_params.get('deploy_name','?')}, ncc_id={deploy_params.get('ncc_id','?')}")

    success = False
    _update_operational_after_upgrade(scaler_hostname or device_id, "UPGRADING", success=False)
    # Clear any phase markers from a previous (successful or aborted)
    # upgrade attempt before stamping fresh ones. Without this, a
    # second upgrade on the same device could trip the orphan scanner
    # if it ever crashes -- the scanner would see stale
    # `gi_confirmed_at` from yesterday and try to "resume" a phase
    # that doesn't apply to the new run. The helper is idempotent and
    # safe to call even when there are no markers.
    try:
        _clear_upgrade_markers(scaler_hostname or device_id, _log)
    except Exception:
        pass
    try:
        _check_upgrade_cancel(job_id)

        if upgrade_type == "delete_deploy":
            _run_delete_deploy_upgrade(job_id, device_id, mgmt_ip, user, password,
                                       url_list, deploy_params, stage_times, _log,
                                       scaler_hostname=scaler_hostname)
        elif upgrade_type == "gi_deploy":
            _run_gi_deploy_upgrade(job_id, device_id, url_list, deploy_params,
                                    stage_times, _log, scaler_hostname=scaler_hostname)
        else:
            # Runtime mode detection for ALL devices (not just KVM clusters).
            # Prior behaviour called _ssh_connect_basic(mgmt_ip) directly for
            # non-KVM devices; if the device was actually sitting in GI (e.g.
            # a previous upgrade got stuck) or if mgmt_ip SSH was flaky, the
            # flow would hard-fail instead of auto-switching to gi_deploy /
            # escalating to console fallback. connect_for_upgrade handles all
            # that: SSH-SN -> SSH-MGMT -> virsh -> console, and returns the
            # live device_state.
            _check_upgrade_cancel(job_id)
            _is_cluster = (_op_data_cached.get("ncc_type") or "").lower() == "kvm"
            _log("INFO",
                 "Runtime mode detection via connect_for_upgrade "
                 f"({'KVM cluster' if _is_cluster else 'single-access'})")
            os.chdir(SCALER_ROOT)
            from scaler.connection_strategy import connect_for_upgrade
            conn = connect_for_upgrade(scaler_hostname, timeout=120)
            if not conn.get("connected"):
                # For non-KVM SA devices we still have a working mgmt_ip in
                # operational.json; fall back to the legacy direct-SSH path
                # so a transient connect_for_upgrade hiccup doesn't abort a
                # clean in-place upgrade. KVM clusters have no such fallback
                # because they strictly require the virsh-capable strategy.
                if _is_cluster:
                    raise RuntimeError(
                        f"Cannot connect to {device_id}: "
                        f"{conn.get('abort_reason', 'unknown')}"
                    )
                _log("WARN",
                     f"connect_for_upgrade failed ({conn.get('abort_reason', '?')}); "
                     f"falling back to direct SSH on {mgmt_ip}")
                _run_normal_upgrade(job_id, device_id, mgmt_ip, user, password,
                                    url_list, stage_times, _log)
            else:
                _runtime_state = (conn.get("device_state") or "").upper()
                _runtime_method = conn.get("method", "?")
                _log("INFO", f"Runtime mode: {_runtime_state} (via {_runtime_method})")
                # connect_for_upgrade's state classification can FLAP for KVM
                # clusters reached over a console/virsh path -- it may report
                # GI/BASEOS_SHELL on one connect and DNOS on the next (observed
                # on YOR_CL_PE-4 2026-06-22: routed to gi_deploy, then the GI
                # reconnect found DNOS and aborted "Expected GI/BASEOS_SHELL,
                # got DNOS"). When the cached operational.json device_state is
                # DNOS, trust that and use the in-DNOS `normal` flow (which
                # loads all 3 tarballs in DNOS and has its own GI-prompt guard
                # as a backstop) rather than a single, possibly-wrong runtime
                # GI claim. Only take gi_deploy when DNOS is NOT the cached state.
                _cached_is_dnos = False
                try:
                    from scaler.connection_strategy import classify_device_state as _cds_fn
                    _cached_is_dnos = _cds_fn(
                        (_op_data_cached.get("device_state") or "").upper()) == "DNOS"
                except Exception:
                    _cached_is_dnos = False
                if (_runtime_state == "GI" or _runtime_state == "BASEOS_SHELL") and _cached_is_dnos:
                    _log("WARN",
                         f"Runtime detection reported {_runtime_state} but cached device_state is "
                         f"DNOS (connect_for_upgrade state is flapping for this device). Trusting "
                         f"DNOS and using the in-DNOS normal flow (it loads DNOS+GI+BaseOS and has "
                         f"its own GI-prompt backstop).")
                    try:
                        conn["ssh"].close()
                    except Exception:
                        pass
                    _run_normal_upgrade(job_id, device_id, mgmt_ip, user, password,
                                        url_list, stage_times, _log)
                elif _runtime_state == "GI" or _runtime_state == "BASEOS_SHELL":
                    _log("WARN", f"Device is in {_runtime_state} -- switching to gi_deploy flow")
                    upgrade_type = "gi_deploy"
                    # Re-normalise deploy_params with the live connection
                    # snapshot: `conn.get("ncc_id")` may be populated when
                    # we reached the device via the virsh path (VM name
                    # parse) even if operational.json didn't have it
                    # cached. The shared normaliser handles all the
                    # present-but-null / present-but-invalid edge cases
                    # that used to propagate `ncc-id None` into the CLI.
                    _normalize_deploy_params(
                        deploy_params,
                        op_data_cached=_op_data_cached,
                        scaler_hostname=scaler_hostname,
                        device_id=device_id,
                        conn_ncc_id=conn.get("ncc_id"),
                        _log=_log,
                    )
                    try:
                        conn["ssh"].close()
                    except Exception:
                        pass
                    _run_gi_deploy_upgrade(job_id, device_id, url_list, deploy_params,
                                          stage_times, _log, scaler_hostname=scaler_hostname)
                else:
                    _run_normal_upgrade(
                        job_id, device_id, mgmt_ip, user, password,
                        url_list, stage_times, _log,
                        pre_connected=(conn["ssh"], conn["channel"]),
                    )

        success = True
        total_elapsed = round(time.time() - t_start, 1)
        _update_device_state(job_id, device_id, status="completed", phase="done", percent=100,
                             message=f"Upgrade complete ({total_elapsed}s)", completed_at=datetime.utcnow().isoformat() + "Z")
        _log("OK", f"upgrade complete in {total_elapsed}s")
        _update_operational_after_upgrade(scaler_hostname or device_id, "DNOS", success=True)
    except _UpgradeCancelled:
        total_elapsed = round(time.time() - t_start, 1)
        _log("WARN", f"Upgrade cancelled by user after {total_elapsed}s")
        # On cancel we MUST clear `upgrade_in_progress` and `upgrade_job_id`
        # in operational.json. Otherwise the next device refresh will still
        # see "upgrade in progress" even though no thread is actually
        # running, blocking every subsequent upgrade wizard preflight.
        #
        # `_delete_pending` is trickier: if `request system delete` already
        # went through, the device IS in transition and needs to come back
        # in GI mode before we can safely clear the quarantine flags. We
        # tag the flag with `_delete_pending_cancelled_at` so crash-recovery
        # can age it out after 2 hours if the device never resurfaced.
        try:
            _cancel_iso = datetime.utcnow().isoformat() + "Z"
            _canon = _resolve_config_dir(scaler_hostname or device_id) or (scaler_hostname or device_id)
            _op_path = Path(SCALER_ROOT) / "db" / "configs" / _canon / "operational.json"
            from routes._ops_writer import update_ops as _update_ops_c

            def _cancel_mutator(data):
                data["upgrade_in_progress"] = False
                data.pop("upgrade_job_id", None)
                data["upgrade_cancelled_at"] = _cancel_iso
                data["upgrade_last_cancel_reason"] = "user_cancel"
                if data.get("_delete_pending"):
                    data["_delete_pending_cancelled_at"] = _cancel_iso
                return True

            _update_ops_c(_op_path, _cancel_mutator)
            _log("INFO",
                 f"Cancel cleanup: cleared upgrade_in_progress in "
                 f"operational.json (device: {_canon})")
        except Exception as _cc_err:
            _log("WARN",
                 f"Cancel cleanup failed (operational.json may still show "
                 f"upgrade_in_progress): {_cc_err}")
        _update_device_state(job_id, device_id, status="cancelled",
                             phase="cancelled", percent=100,
                             message=f"Cancelled by user after {total_elapsed}s",
                             completed_at=datetime.utcnow().isoformat() + "Z")
        return
    except Exception as e:
        total_elapsed = round(time.time() - t_start, 1)
        _update_device_state(job_id, device_id, status="failed", phase="error", percent=100,
                             error=str(e), completed_at=datetime.utcnow().isoformat() + "Z")
        _log("ERROR", str(e))
        _update_operational_after_upgrade(scaler_hostname or device_id, upgrade_type.upper(), success=False, error=str(e))
        raise
    finally:
        total_elapsed = round(time.time() - t_start, 1)
        try:
            # Resolve the post-upgrade system_type for the timing
            # record. Priority: freshly-written operational.json (the
            # upgrade itself populates this for previously-"N/A" chassis
            # like the RR-SA-2 live test), deploy_params, then the
            # in-memory plan snapshot. Stored with every entry so future
            # estimates can key on hardware family, not just hostname.
            save_system_type = ""
            try:
                import json as _j
                op_path = Path(SCALER_ROOT) / "db" / "configs" / (scaler_hostname or device_id) / "operational.json"
                if op_path.exists():
                    save_system_type = str(_read_ops_safe(op_path).get("system_type") or "").strip()
            except Exception:
                pass
            if not save_system_type and isinstance(deploy_params, dict):
                save_system_type = str(deploy_params.get("system_type") or "").strip()
            if save_system_type.upper() in ("", "N/A", "NONE"):
                save_system_type = ""

            from scaler.config_pusher import save_upgrade_timing_record
            save_upgrade_timing_record(
                device_hostname=device_id,
                upgrade_type=upgrade_type,
                components=components,
                actual_time_seconds=total_elapsed,
                stage_times=stage_times,
                current_version=current_version,
                target_version=target_version,
                device_mode=device_mode,
                success=success,
                system_type=save_system_type,
            )
        except Exception:
            pass


def _update_operational_after_upgrade(hostname: str, state: str, success: bool = True, error: str = ""):
    """Update operational.json at upgrade start, completion, or failure.

    Resolves the canonical config directory via _resolve_config_dir
    and updates ALL known directories for this device.
    """
    try:
        canonical = _resolve_config_dir(hostname)
        dirs_to_update = list(dict.fromkeys([canonical, hostname]))
        for dir_name in dirs_to_update:
            _update_single_operational(dir_name, state, success, error)
    except Exception:
        pass


def _update_single_operational(dir_name: str, state: str, success: bool, error: str):
    try:
        ops_path = Path(SCALER_ROOT) / "db" / "configs" / dir_name / "operational.json"
        if not ops_path.exists():
            return
        from routes._ops_writer import update_ops as _update_ops_terminal
        _now_str = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        def _terminal_mutator(data):
            if state == "UPGRADING":
                data["device_state"] = "UPGRADING"
                data["upgrade_in_progress"] = True
                data["install_status"] = "IN_PROGRESS"
                data["install_start"] = _now_str
            elif success:
                data["device_state"] = state
                data["upgrade_in_progress"] = False
                data["install_status"] = "COMPLETED"
                data["install_finish"] = _now_str
                data.pop("recovery_mode_detected", None)
                data.pop("delete_initiated", None)
                data.pop("console_recovery_detected", None)
                data.pop("stack_components", None)
                data.pop("git_commit", None)
                data.pop("dnos_version", None)
                data.pop("baseos_version", None)
                data.pop("gi_version", None)
            else:
                data["upgrade_in_progress"] = False
                data["install_status"] = "FAILED"
                data["upgrade_error"] = error[:500] if error else ""
            return True

        _update_ops_terminal(ops_path, _terminal_mutator)
    except Exception:
        pass


def _make_send_wait(chan):
    """Create a send-and-wait helper bound to a shell channel.
    Works for DNOS prompts (hostname#), GI prompts (GI#/GI(ts)#), and FGI prompts ([FGI(ts)#).
    Raises OSError on socket close so callers (deploy/install) can handle it.
    """
    import time
    import re

    _prompt_re = re.compile(r'[#>]\s*$')

    def _send_wait(cmd: str, wait_s: int = 3):
        chan.send(cmd + "\n")
        time.sleep(wait_s)
        buf = ""
        for _ in range(60):
            try:
                if chan.recv_ready():
                    buf += chan.recv(65535).decode("utf-8", errors="replace")
            except (OSError, EOFError):
                if buf:
                    return buf
                raise
            time.sleep(0.5)
            stripped = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', buf).rstrip()
            if _prompt_re.search(stripped) or len(buf) > 5000:
                break
        return buf

    return _send_wait


def _strip_upgrade_ansi(text: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', str(text or ''))


def _dnos_show_system_ready(output: str, device_id: str = "", scaler_hostname: str = "") -> tuple[bool, str]:
    """Validate that DNOS is ready enough for config load/repair.

    ``connect_for_upgrade`` can identify a DNOS prompt before the full CLI
    back-end is ready. Config repair must wait until an authoritative
    ``show system | no-more`` returns real system content.
    """
    clean = _strip_upgrade_ansi(output)
    lower = clean.lower()
    if not clean.strip():
        return False, "empty show system output"
    bad_markers = (
        "unknown word", "syntax error", "error:", "command failed",
        "temporarily unavailable", "not ready", "connection refused",
        "traceback", "permission denied",
    )
    for marker in bad_markers:
        if marker in lower:
            return False, f"show system returned {marker}"

    has_system_fields = bool(
        re.search(r"\bsystem[- ]?type\s*:", clean, re.I)
        or re.search(r"\bncc[- ]?id\s*:", clean, re.I)
        or re.search(r"\bnode\s+type\b.*\bnode\s+id\b", clean, re.I | re.S)
        or re.search(r"\bcontrol\s+plane\b|\bdata\s+plane\b", clean, re.I)
    )
    if not has_system_fields:
        return False, "show system did not include system/node fields"

    expected = [x for x in (device_id, scaler_hostname) if x]
    if expected:
        norm_clean = re.sub(r"[^a-z0-9]", "", clean.lower())
        if any(re.sub(r"[^a-z0-9]", "", x.lower()) in norm_clean for x in expected):
            return True, "show system ready with expected device identity"
    return True, "show system ready"


def _canonical_upgrade_component(name: str) -> str:
    comp = re.sub(r"[^A-Za-z0-9]", "", str(name or "")).upper()
    if comp in ("BASEOS", "BASE"):
        return "BASEOS"
    if comp == "DNOS":
        return "DNOS"
    if comp == "GI":
        return "GI"
    return comp


def _upgrade_expected_stack_tokens(comp_name: str, url: str) -> list[str]:
    """Extract target-stack version tokens from an image URL.

    Feature builds include non-numeric suffixes such as
    ``26.2.0.4_priv.usirota_evpn_vpls_irb_4``. The old numeric-only regex
    truncated those suffixes and could miss an already-loaded target.
    """
    text = str(url or "")
    if not text:
        return []
    filename = text.rstrip("/").rsplit("/", 1)[-1].split("?", 1)[0]
    tokens: list[str] = []
    comp = _canonical_upgrade_component(comp_name).lower()
    patterns = [
        rf"drivenets[_-]{re.escape(comp)}[_-]([^/]+?)(?:\.tar(?:\.\w+)?|$)",
        r"(\d+\.\d+\.\d+(?:[A-Za-z0-9._-]*))",
        r"(\d+\.\d{5,}(?:[A-Za-z0-9._-]*))",
    ]
    for pattern in patterns:
        match = re.search(pattern, filename, re.I)
        if match:
            token = match.group(1).strip()
            token = re.sub(r"\.tar(?:\.\w+)?$", "", token, flags=re.I)
            if token and token not in tokens:
                tokens.append(token)
    return sorted(tokens, key=len, reverse=True)


def _parse_system_stack_targets(output: str) -> dict[str, dict[str, str]]:
    """Parse ``show system stack`` output by Target column.

    Returns ``{"DNOS": {"current": "...", "target": "...", "line": "..."}}``.
    The parser is header-aware but keeps the old 6-column fallback because GI
    stack tables vary slightly between builds.
    """
    clean = _strip_upgrade_ansi(output)
    result: dict[str, dict[str, str]] = {}
    header_map: dict[str, int] = {}
    for raw_line in clean.splitlines():
        line = raw_line.strip()
        if "|" not in line or not line:
            continue
        if set(line.replace("|", "").strip()) <= {"-"}:
            continue
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if not parts:
            continue
        lowered = [p.lower() for p in parts]
        if any(p == "component" for p in lowered):
            header_map = {p: i for i, p in enumerate(lowered)}
            continue

        comp = _canonical_upgrade_component(parts[0])
        if comp not in ("DNOS", "GI", "BASEOS"):
            continue
        current_idx = header_map.get("current", 2)
        target_idx = header_map.get("target", 5 if len(parts) > 5 else len(parts) - 1)
        current = parts[current_idx] if 0 <= current_idx < len(parts) else ""
        target = parts[target_idx] if 0 <= target_idx < len(parts) else ""
        result[comp] = {"current": current, "target": target, "line": line}
    return result


def _target_stack_has_expected_component(targets: dict[str, dict[str, str]],
                                         comp_name: str, url: str) -> bool:
    """Return True when the stack Target column already matches the selected URL."""
    comp = _canonical_upgrade_component(comp_name)
    info = targets.get(comp) or {}
    target = str(info.get("target") or "").strip()
    if not target or target == "-":
        return False
    tokens = _upgrade_expected_stack_tokens(comp, url)
    if not tokens:
        return False
    target_norm = target.lower()
    return any(token.lower() in target_norm for token in tokens)


def _verify_stack_targets_for_urls(output: str, url_list: list) -> tuple[set[str], list[str], dict[str, dict[str, str]]]:
    """Verify each selected image URL against the ``show system stack`` Target column."""
    targets = _parse_system_stack_targets(output)
    matched: set[str] = set()
    missing: list[str] = []
    for comp_name, url in url_list or []:
        if not url:
            continue
        comp_key = _canonical_upgrade_component(comp_name)
        if _target_stack_has_expected_component(targets, comp_key, url):
            matched.add(comp_key)
        else:
            missing.append(comp_key)
    return matched, missing, targets


def _gi_stack_probe_ok(output: str) -> bool:
    clean = _strip_upgrade_ansi(output)
    if _parse_system_stack_targets(clean):
        return True
    return bool(re.search(r"\bComponent\b.*\bTarget\b", clean, re.I | re.S)
                and re.search(r"F?GI(?:\([^)]*\))?[#>]", clean, re.I))


def _looks_like_ncc_shell_output(output: str) -> bool:
    clean = _strip_upgrade_ansi(output)
    if _looks_like_kvm_host_shell_output(clean):
        return False
    lower = clean.lower()
    shell_markers = (
        "command 'request' not found",
        "request: command not found",
        "show: command not found",
        "not found, did you mean",
    )
    if any(marker in lower for marker in shell_markers):
        return True
    return bool(
        re.search(r"(?:^|\n)[A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+:[^\n]*[$#]\s*$", clean)
        or re.search(r"(?:^|\n)ncc(?:-[A-Za-z0-9_.-]+)?(?::[^\n]*)?[$#]\s*$", clean, re.I)
    )


def _looks_like_kvm_host_shell_output(output: str) -> bool:
    """Return True for the outer KVM hypervisor host shell ONLY.

    The KVM host prompt is the bare hypervisor name, e.g. ``dn@kvm108:~$``.
    NCC *VM* hostnames in this lab are derived from the hypervisor name plus a
    cluster/NCC suffix -- e.g. ``dn@kvm108-cl408d-ncc1:~$`` -- and are NOT the
    KVM host: that is the (possibly standby) NCC routing VM where ``dncli``
    belongs. The old pattern ``kvm\\d+[A-Za-z0-9_.-]*`` greedily matched those
    NCC VM prompts too, so a standby-NCC ``dncli`` error was misread as a
    KVM-host-shell error and the standby->active pivot never fired
    (PE-4 2026-06-14). Exclude any prompt whose host contains ``ncc``.
    """
    clean = _strip_upgrade_ansi(output)
    m = re.search(
        r"(?:^|\n)(?:dn|root)@(kvm\d+[A-Za-z0-9_.-]*):[^\n]*[$#]\s*$",
        clean,
        re.I,
    )
    if not m:
        return False
    if "ncc" in m.group(1).lower():
        return False
    return True


def _gi_command_failed_due_to_shell(output: str) -> bool:
    """Detect the PE-4 failure mode: GI command was executed by Linux shell."""
    return _looks_like_kvm_host_shell_output(output) or _looks_like_ncc_shell_output(output)


def _probe_gi_stack_once(chan, wait: float = 6.0) -> tuple[bool, bool, str]:
    """Run a short ``show system stack`` probe.

    Returns ``(gi_ok, shell_seen, output)``. This avoids ``_make_send_wait``
    because bash prompts end in ``$`` and would otherwise wait for the long
    generic timeout before detecting shell drift.
    """
    import time

    if _channel_is_closed(chan):
        return False, False, "channel closed"
    try:
        while chan.recv_ready():
            chan.recv(65535)
            time.sleep(0.05)
        chan.send(b"\n")
        time.sleep(0.2)
        while chan.recv_ready():
            chan.recv(65535)
            time.sleep(0.05)
        chan.send(b"show system stack | no-more\n")
    except Exception as exc:
        return False, False, str(exc)

    deadline = time.time() + wait
    buf = b""
    while time.time() < deadline:
        try:
            if chan.recv_ready():
                buf += chan.recv(65535)
        except Exception as exc:
            return False, False, (buf.decode("utf-8", errors="replace") + str(exc))
        text = buf.decode("utf-8", errors="replace")
        if _gi_stack_probe_ok(text):
            return True, False, text
        if _looks_like_kvm_host_shell_output(text):
            return False, False, text
        if _looks_like_ncc_shell_output(text):
            return False, True, text
        time.sleep(0.2)
    text = buf.decode("utf-8", errors="replace")
    return _gi_stack_probe_ok(text), _looks_like_ncc_shell_output(text), text


def _ensure_gi_cli_for_command(chan, _log, context: str = "GI command",
                               probe_wait: float = 6.0) -> bool:
    """Prove the channel is at GI CLI before sending a GI target-stack command.

    KVM/virsh channels can drift from ``GI#`` back to the NCC bash shell after
    an earlier Ctrl+C or prompt transition. This helper treats ``show system
    stack`` target-table output as the authoritative proof, and re-enters
    ``dncli`` from NCC bash when shell drift is observed.
    """
    ok, shell_seen, output = _probe_gi_stack_once(chan, wait=probe_wait)
    if ok:
        return True

    if _looks_like_kvm_host_shell_output(output):
        excerpt = _upgrade_terminal_excerpt(
            output, ["show system stack | no-more"], limit=160)
        raise _GiCliReconnectRequired(
            f"GI CLI drifted to KVM host shell before {context}; "
            f"reconnect virsh console before retrying"
            f"{' (' + excerpt + ')' if excerpt else ''}"
        )

    if not shell_seen and _probe_ncc_bash(chan, wait=1.0):
        shell_seen = True

    if shell_seen:
        _log("WARN", f"GI CLI drifted to NCC shell before {context}; re-entering dncli")
        if not _ensure_ncc_bash(chan):
            raise RuntimeError(f"GI CLI unreachable before {context}: cannot reach NCC bash")
        if not _enter_dncli_from_bash(chan, _log):
            raise RuntimeError(f"GI CLI unreachable before {context}: dncli entry failed")
        ok, shell_seen, output = _probe_gi_stack_once(chan, wait=probe_wait)
        if ok:
            _log("OK", f"GI CLI confirmed before {context}")
            return True

    excerpt = _upgrade_terminal_excerpt(output, ["show system stack | no-more"], limit=220)
    raise RuntimeError(
        f"GI CLI unreachable before {context}: show system stack did not return a GI stack table"
        f"{' (' + excerpt + ')' if excerpt else ''}"
    )


def _wait_for_dnos_config_ready(job_id: str, device_id: str, scaler_hostname: str,
                                chan, _log, timeout: int = 300,
                                check_interval: int = 15) -> bool:
    """Poll ``show system | no-more`` before post-deploy config repair."""
    import time

    _update_device_state(
        job_id, device_id, phase="dnos-readiness", percent=94,
        message="Waiting for DNOS system readiness before config repair...")
    _log("INFO",
         f"DNOS prompt detected; polling show system before config repair "
         f"(timeout {timeout}s)")
    sw = _make_send_wait(chan)
    start = time.time()
    last_reason = "not checked"
    attempt = 0
    while time.time() - start < timeout:
        _check_upgrade_cancel(job_id)
        attempt += 1
        try:
            out = sw("show system | no-more", 5)
            ready, reason = _dnos_show_system_ready(out, device_id, scaler_hostname)
            last_reason = reason
            if ready:
                elapsed = int(time.time() - start)
                _log("OK", f"DNOS ready for config repair ({reason}, {elapsed}s)")
                return True
            if attempt == 1 or attempt % 4 == 0:
                _log("INFO", f"DNOS not ready for config repair yet: {reason}")
        except Exception as exc:
            last_reason = str(exc)
            if attempt == 1 or attempt % 4 == 0:
                _log("INFO", f"DNOS readiness probe failed: {exc}")
        elapsed = int(time.time() - start)
        _update_device_state(
            job_id, device_id, phase="dnos-readiness",
            percent=94 + min(elapsed // 60, 2),
            message=f"Waiting for DNOS readiness... ({elapsed}s)")
        time.sleep(check_interval)
    _log("WARN",
         f"DNOS readiness gate timed out after {timeout}s; last status: {last_reason}. "
         "Skipping config repair for now so it can be retried safely later.")
    _update_device_state(
        job_id, device_id, phase="dnos-readiness", percent=96,
        message=f"DNOS readiness timed out before config repair: {last_reason}",
        config_restored=False,
        config_repair_pending=True,
        config_repair_retryable=True,
        config_repair_error=f"DNOS readiness timeout: {last_reason}"[:500])
    return False


def _capture_current_install_task_id(chan, _log=None):
    """Snapshot the current `show system install` Task ID in GI mode.

    This is the pre-deploy baseline that `_post_deploy_verify` uses to
    tell a genuine new install from a stale previous-deploy record.
    Without this baseline we couldn't distinguish PE-2's state
    (Task ID 1776204261440, DONE, empty tables -- nothing happened)
    from a freshly-completed deploy.

    Returns ('', '') on any channel/parse error so callers can keep
    going with "no baseline" semantics.
    """
    import time
    try:
        sw = _make_send_wait(chan)
        out = sw("show system install | no-more", 5)
        info = _parse_task_status(out)
        if _log is not None:
            _log("INFO",
                 f"Pre-deploy install baseline: "
                 f"task_id={info['task_id'] or 'none'}, status={info['status']}, "
                 f"running={info['running_count']}, finished={info['finished_count']}")
        return info.get("task_id", "") or "", info.get("status", "") or ""
    except Exception as e:
        if _log is not None:
            _log("WARN", f"Could not capture pre-deploy install baseline: {e}")
        return "", ""


_DEPLOY_REJECT_PATTERNS = [
    # Substrings (lowercase) that mean the device REJECTED the deploy
    # outright -- no install task will ever appear, so retrying the
    # verify loop is pointless.
    "no target stack",
    "target stack is empty",
    "target stack not set",
    "cannot deploy",
    "deploy is not allowed",
    "invalid system-type",
    "no license",
    "system is already deployed",
    "already deployed",
    "deploy failed",
]


def _detect_deploy_rejection(deploy_out):
    """Return a human-readable reason if the deploy CLI output clearly
    indicates an immediate rejection, else ''.

    NOTE: "error" on its own is not enough -- leftover text from pre-
    check tables can include "Pre-check result: Failed" etc. which
    must NOT be treated as deploy rejection (the install might still
    start and correct itself). We only flag *explicit* reject phrases.
    """
    if not deploy_out:
        return ""
    lo = deploy_out.lower()
    for pat in _DEPLOY_REJECT_PATTERNS:
        if pat in lo:
            return pat
    return ""


# ---------------------------------------------------------------------------
# Crash-recovery phase markers
# ---------------------------------------------------------------------------
# Every critical CLI step in `_run_device_upgrade` stamps a wall-clock
# timestamp into operational.json BEFORE the channel command goes out.
# The resumer reads these markers on restart and skips already-completed
# steps instead of replaying from scratch (which would, for example,
# re-issue `request system delete` on a device already in GI).
#
# Marker order (chronological):
#
#   delete_sent_at            -- right before `request system delete`
#   delete_completed_at       -- after delete confirm prompt accepted
#   gi_confirmed_at           -- once GI mode is observed via SSH probe
#   images_loaded_at          -- after `system load image` completes for
#                                every component in url_list
#   deploy_sent_at            -- right before `request system deploy ...`
#   install_started_at        -- once a NEW install task ID appears
#                                (running_count > 0 OR Task ID rotated)
#   dnos_confirmed_at         -- once the device responds in DNOS via SSH
#   config_repair_started_at  -- right before push of pre-delete backup
#   config_repair_completed_at -- after config push reports success
#   upgrade_completed_at      -- end of post-deploy-verify success path
#
# All markers are ISO-8601 UTC strings. `_stamp_phase` is the SOLE writer
# (uses `_ops_writer.update_ops` for atomicity); resumers use
# `_get_phase_marker` to read.
#
# Failure semantics:
#   - If stamping fails (disk full, lock contention) we log WARN and
#     continue. The CLI command still goes through; the marker simply
#     won't help recovery for that one crash window. Better than aborting
#     the upgrade because we couldn't write a JSON file.
#   - Markers are NEVER cleared on a successful step. They monotonically
#     accumulate across the upgrade. Cancellation clears them via
#     `_clear_upgrade_markers` so the next attempt starts clean.
# ---------------------------------------------------------------------------

# All phase markers we recognise, in chronological order. The orphan
# scanner and resumer iterate this list to find "the latest step that
# completed" without hard-coding string lookups.
_UPGRADE_PHASE_MARKERS = (
    "delete_sent_at",
    "delete_completed_at",
    "gi_confirmed_at",
    "images_loaded_at",
    "deploy_sent_at",
    "install_started_at",
    "dnos_confirmed_at",
    "config_repair_started_at",
    "config_repair_completed_at",
    "upgrade_completed_at",
)


def _stamp_phase(scaler_hostname: str, marker: str, _log=None, **extra) -> bool:
    """Write a phase marker (and optional siblings) to operational.json.

    Args:
        scaler_hostname: the SCALER device dir name (matches
            ``db/configs/<name>``). May be empty -- we no-op gracefully
            so callers don't need their own try/except.
        marker: one of ``_UPGRADE_PHASE_MARKERS``. Unknown markers are
            still written (forward-compat) but a WARN is logged.
        _log: optional ``_log`` callable from the upgrade context.
        **extra: extra fields to write alongside the timestamp (e.g.
            ``deploy_command="request system deploy ..."``,
            ``ncc_id=1``, ``url_list=[("DNOS","http://...")]``). These
            help the orphan scanner reconstruct enough context to
            re-issue commands without re-discovering parameters.

    Returns:
        True on successful write, False otherwise.
    """
    from datetime import datetime
    if not scaler_hostname:
        return False
    if marker not in _UPGRADE_PHASE_MARKERS and _log:
        try:
            _log("WARN", f"Unknown phase marker '{marker}' (allowed: {_UPGRADE_PHASE_MARKERS})")
        except Exception:
            pass
    try:
        op_file = Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname / "operational.json"
        if not op_file.parent.exists():
            return False
        from routes._ops_writer import update_ops as _update_ops_phase
        _now_iso = datetime.utcnow().isoformat() + "Z"

        def _phase_mutator(op_data):
            op_data[marker] = _now_iso
            for k, v in extra.items():
                if v is not None:
                    op_data[k] = v
            # Always touch the bookkeeping field so downstream readers
            # know which step was last reached without scanning every
            # marker key.
            op_data["upgrade_last_phase"] = marker
            op_data["upgrade_last_phase_at"] = _now_iso
            return True

        _update_ops_phase(op_file, _phase_mutator, create_if_missing=True)
        return True
    except Exception as exc:
        if _log:
            try:
                _log("WARN", f"Phase marker '{marker}' not persisted ({exc})")
            except Exception:
                pass
        return False


def _get_phase_marker(op_data: dict, marker: str) -> str:
    """Return the timestamp for a phase marker, or empty string if unset."""
    if not isinstance(op_data, dict):
        return ""
    val = op_data.get(marker)
    return val if isinstance(val, str) else ""


def _latest_phase_reached(op_data: dict) -> str:
    """Return the name of the latest phase marker stamped (or '').

    Iterates ``_UPGRADE_PHASE_MARKERS`` in reverse chronological order so
    the first match is the furthest the upgrade got before the crash.
    """
    if not isinstance(op_data, dict):
        return ""
    for marker in reversed(_UPGRADE_PHASE_MARKERS):
        if _get_phase_marker(op_data, marker):
            return marker
    return ""


def _clear_upgrade_markers(scaler_hostname: str, _log=None) -> bool:
    """Remove all upgrade phase markers (called on cancel + on next start).

    Use this when the operator has explicitly cancelled or the upgrade
    has fully completed -- otherwise the next upgrade attempt would
    start with stale "last phase" data and the resumer might skip
    legitimate replay.

    IMPORTANT: ``_ops_writer.update_ops`` runs a *no-shrink invariant*
    that restores any key the mutator silently drops (this guards
    against scaler's legacy partial-write race that was eating
    ``stack_components`` / ``_identity``). Bare ``op_data.pop(key)``
    therefore has NO net effect; the popped key reappears after the
    invariant pass. The escape hatch is ``_drop_keys``: a list of key
    names whose deletions are *intentional* and must be honored. We
    populate ``_drop_keys`` with every marker we want gone.
    """
    if not scaler_hostname:
        return False
    try:
        op_file = Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname / "operational.json"
        if not op_file.exists():
            return False
        from routes._ops_writer import update_ops as _update_ops_clear

        _CLEAR_KEYS = list(_UPGRADE_PHASE_MARKERS) + [
            "upgrade_last_phase",
            "upgrade_last_phase_at",
            "upgrade_deploy_command",
            "upgrade_deploy_system_type",
            "upgrade_deploy_name",
            "upgrade_deploy_ncc_id",
            "upgrade_url_list",
        ]

        def _clear_mutator(op_data):
            for m in _CLEAR_KEYS:
                op_data.pop(m, None)
            # Tell the no-shrink invariant these deletions are intentional.
            op_data["_drop_keys"] = list(_CLEAR_KEYS)
            return True

        _update_ops_clear(op_file, _clear_mutator)
        return True
    except Exception as exc:
        if _log:
            try:
                _log("WARN", f"Phase marker clear failed ({exc})")
            except Exception:
                pass
        return False


def _send_deploy_command(chan, sys_type, d_name, ncc_id, _log):
    """Send 'request system deploy' with rapid confirmation-prompt handling,
    NCC-ID mismatch retry, and explicit rejection detection.

    Polls every 0.5s for the (yes/no) prompt and answers immediately.

    Returns (deploy_out, final_ncc_id, old_task_id):
      - deploy_out:   raw CLI output (may be partial if the socket closed)
      - final_ncc_id: ncc-id that was accepted (after auto-retry)
      - old_task_id:  pre-deploy `show system install` Task ID -- the
                      post-deploy verifier compares each new probe
                      against this so it can call out
                      "deploy never registered a new install task".

    Raises RuntimeError on hard rejection patterns (no target stack,
    cannot deploy, already deployed, etc.). Socket-close after deploy
    is EXPECTED (the device reboots) and is NOT an error.
    """
    import time, re

    _ensure_gi_cli_for_command(chan, _log, "deploy preparation")

    chan.send(b"\x03")
    time.sleep(1)
    while chan.recv_ready():
        chan.recv(65535)
        time.sleep(0.1)
    chan.send(b"\r")
    time.sleep(2)
    while chan.recv_ready():
        chan.recv(65535)
        time.sleep(0.1)
    _ensure_gi_cli_for_command(chan, _log, "pre-deploy install snapshot")

    # Pre-deploy snapshot must happen BEFORE the reboot-inducing
    # command so we capture the previous Task ID (if any). PE-2's live
    # output showed Task ID 1776204261440 with Task status DONE and
    # empty Running/Finished tables -- without this baseline we can't
    # tell that this was a stale record, not a just-finished install.
    old_task_id, _ = _capture_current_install_task_id(chan, _log)

    # Final-line-of-defence normalisation before we interpolate
    # `ncc_id` into the CLI f-string. `_normalize_deploy_params` at
    # `_run_device_upgrade` entry should already have given us a
    # clean 0/1, but we still re-run `_safe_ncc_id` here because:
    #   * callers from other entry points may have skipped the full
    #     normaliser (e.g. ad-hoc redeploy triggered by operator)
    #   * future regressions anywhere upstream would silently produce
    #     `ncc-id None` at THIS line again -- making the silent-no-op
    #     the GUI/scaler-CLI divergence we just root-caused.
    # Scaler CLI's equivalent is the inline
    #     _main_ncc = conn.get('ncc_id') if conn.get('ncc_id') is not None else 0
    # pattern. Our helper codifies it (+ handles string/"None"/"null"
    # garbage) so every site is immune.
    _original_ncc_id = ncc_id
    ncc_id = _safe_ncc_id(ncc_id)
    if _original_ncc_id != ncc_id:
        _log("WARN",
             f"ncc_id was {_original_ncc_id!r} at _send_deploy_command entry "
             f"(should have been normalised upstream) -- clamped to {ncc_id}. "
             f"CLI retry will auto-flip to {1 - ncc_id} if the device reports "
             f"'doesn\\'t match / auto detected'.")

    def _send_and_poll_confirm(cmd, tag=""):
        """Send command, poll rapidly for confirmation/error/prompt. Return output."""
        _ensure_gi_cli_for_command(chan, _log, f"{cmd}{tag}".strip())
        chan.send(cmd.encode() + b"\n")
        _log_upgrade_device_input(_log, cmd)
        buf = b""
        for _ in range(60):
            time.sleep(0.5)
            try:
                if chan.recv_ready():
                    buf += chan.recv(65535)
            except (OSError, EOFError) as e:
                es = str(e).lower()
                if "socket" in es or "eof" in es or "closed" in es:
                    _log("OK", f"Deploy sent{tag} -- device rebooting (connection closed)")
                    return buf.decode("utf-8", errors="replace"), True
                raise
            text = buf.decode("utf-8", errors="replace")
            lo = text.lower()
            if "yes/no" in lo or "y/n" in lo or "do you want" in lo or "continue" in lo:
                _log("INFO", f"Confirmation prompt detected{tag} -- answering 'yes'")
                chan.send(b"yes\n")
                _log_upgrade_device_input(_log, "yes", "confirmation")
                time.sleep(3)
                try:
                    if chan.recv_ready():
                        buf += chan.recv(65535)
                except (OSError, EOFError):
                    _log("OK", f"Deploy confirmed{tag} -- device rebooting")
                return buf.decode("utf-8", errors="replace"), False
            clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text).rstrip()
            if re.search(r'[#>]\s*$', clean):
                return text, False
        return buf.decode("utf-8", errors="replace"), False

    deploy_cmd = f"request system deploy system-type {sys_type} name {d_name} ncc-id {ncc_id}"
    _log("INFO", f"Deploying target system (system_type={sys_type}, ncc-id={ncc_id})")

    deploy_out, conn_closed = _send_and_poll_confirm(deploy_cmd)
    if conn_closed:
        return (deploy_out, ncc_id, old_task_id)

    lo = deploy_out.lower()

    if "doesn't match" in lo or "auto detected" in lo:
        ncc_id = 1 - ncc_id
        deploy_cmd = f"request system deploy system-type {sys_type} name {d_name} ncc-id {ncc_id}"
        _log("INFO", f"NCC mismatch detected, retrying deploy with ncc-id {ncc_id}")
        deploy_out, conn_closed = _send_and_poll_confirm(deploy_cmd, " (NCC retry)")
        if conn_closed:
            return (deploy_out, ncc_id, old_task_id)

    reject_reason = _detect_deploy_rejection(deploy_out)
    if reject_reason:
        # Scrape a short snippet around the reject phrase so the
        # operator sees why deploy was rejected without wading through
        # the full buffered CLI output.
        _lo = deploy_out.lower()
        idx = _lo.find(reject_reason)
        snippet = deploy_out[max(0, idx - 40): idx + 200].strip()
        snippet = _upgrade_terminal_excerpt(snippet, [deploy_cmd], limit=240)
        _log("ERROR", f"Deploy REJECTED by device: '{reject_reason}' in output")
        if snippet:
            _log("ERROR", f"  context: {snippet}")
        raise RuntimeError(
            f"Deploy rejected by device: {reject_reason}. "
            f"Verify target images are loaded, the system-type matches "
            f"the hardware, and the device is not already deployed."
        )

    if "error" in deploy_out.lower():
        clean_deploy = _upgrade_terminal_excerpt(deploy_out, [deploy_cmd], limit=300)
        if clean_deploy:
            _log("WARN", f"Deploy output: {clean_deploy}")

    return (deploy_out, ncc_id, old_task_id)


def _ssh_connect_basic(mgmt_ip, user, password):
    """Open paramiko SSH + shell channel, drain initial banner."""
    import time
    import paramiko
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(mgmt_ip, username=user, password=password, timeout=30, look_for_keys=False)
    chan = client.invoke_shell(width=250, height=50)
    chan.settimeout(120)
    time.sleep(2)
    while chan.recv_ready():
        chan.recv(65535)
        time.sleep(0.1)
    return client, chan


def _detect_deploy_params(chan, device_id, _send_wait, _log):
    """Detect system_type, hostname and ncc_id from a running DNOS device."""
    params = {"system_type": "", "deploy_name": device_id, "ncc_id": 0}
    try:
        out = _send_wait("show system | no-more", 5)
        import re
        st_match = re.search(r"system-type\s*:\s*(\S+)", out, re.I)
        if st_match:
            params["system_type"] = st_match.group(1)
        name_match = re.search(r"name\s*:\s*(\S+)", out, re.I)
        if name_match:
            params["deploy_name"] = name_match.group(1)
        ncc_match = re.search(r"ncc-id\s*:\s*(\d+)", out, re.I)
        if ncc_match:
            params["ncc_id"] = int(ncc_match.group(1))
        _log("INFO", f"Deploy params: system_type={params['system_type']}, "
             f"name={params['deploy_name']}, ncc_id={params['ncc_id']}")
    except Exception as e:
        _log("WARN", f"Could not auto-detect deploy params: {e}")
    return params


def _load_images_on_channel(job_id, device_id, chan, url_list, stage_times, _log,
                            pct_base=10, pct_range=50, ensure_gi_cli=False,
                            reconnect_gi_cli=None):
    """Load image URLs via target-stack load on an existing shell channel.

    Pre-checks target-stack to skip already-loaded images.
    Accumulates ALL output, checks for errors, confirms 100% completion,
    and verifies via 'show system target-stack' after loading.
    """
    import time
    import re

    _sw = _make_send_wait(chan)
    gi_reconnects = 0
    max_gi_reconnects = 3

    def _refresh_gi_channel_after_drift(reason: str):
        """Reconnect virsh/GI CLI after KVM host-shell drift without restarting the job."""
        nonlocal chan, _sw, gi_reconnects
        if not ensure_gi_cli:
            raise _GiCliReconnectRequired(reason)
        if reconnect_gi_cli is None:
            raise _GiCliReconnectRequired(reason)
        gi_reconnects += 1
        if gi_reconnects > max_gi_reconnects:
            raise RuntimeError(
                f"GI CLI drift repeated {gi_reconnects} times during image load; "
                "stopping retries to avoid looping forever"
            )
        _log("WARN", f"{reason}; reconnecting GI CLI and resuming target-stack polling "
                     f"({gi_reconnects}/{max_gi_reconnects})")
        new_chan = reconnect_gi_cli(reason)
        if new_chan is None:
            raise RuntimeError(f"GI CLI reconnect did not return a channel after {reason}")
        chan = new_chan
        _sw = _make_send_wait(chan)
        return chan

    # Pre-check: see what's already in target-stack to skip duplicates
    already_loaded = set()
    try:
        _update_device_state(job_id, device_id, phase="check-target-stack", percent=pct_base,
                             message="Checking existing target-stack...")
        while chan.recv_ready():
            chan.recv(65535)
            time.sleep(0.1)
        if ensure_gi_cli:
            try:
                _ensure_gi_cli_for_command(chan, _log, "target-stack pre-check")
            except _GiCliReconnectRequired as drift:
                _refresh_gi_channel_after_drift(f"target-stack pre-check failed after KVM shell drift: {drift}")
                _ensure_gi_cli_for_command(chan, _log, "target-stack pre-check after reconnect")
        ts_out = _sw("show system stack | no-more", 5)
        ts_clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', ts_out)
        stack_targets = _parse_system_stack_targets(ts_clean)
        for comp_name_check, url_check in url_list:
            comp_key = _canonical_upgrade_component(comp_name_check)
            if _target_stack_has_expected_component(stack_targets, comp_key, url_check):
                already_loaded.add(comp_key)
                target = stack_targets.get(comp_key, {}).get("target", "")
                _log("OK", f"{comp_name_check} already in target-stack "
                           f"(Target={target}) -- skipping load")
        if already_loaded:
            _log("INFO", f"Pre-loaded selected components for this load phase: "
                         f"{', '.join(sorted(already_loaded))}")
    except Exception as pre_err:
        if ensure_gi_cli:
            raise
        _log("WARN", f"Target-stack pre-check failed: {pre_err} -- loading all images")

    actual_url_list = [(c, u) for c, u in url_list if c.upper() not in already_loaded]
    if not actual_url_list:
        selected = ", ".join(_canonical_upgrade_component(c) for c, _ in url_list) or "none"
        _log("OK", f"All selected images for this load phase already in target-stack "
                   f"({selected}) -- no loading needed")
        return
    if already_loaded:
        remaining = ", ".join(_canonical_upgrade_component(c) for c, _ in actual_url_list)
        _log("INFO", f"Continuing target-stack load for missing selected components: {remaining}")

    def _send_load_cmd(load_url):
        """Send load command, handle yes/no prompt, Ctrl+C to background it, return output.

        In GI mode the load command shows inline progress and blocks the prompt.
        After answering 'yes', we send Ctrl+C to return the prompt while the
        download continues in the background.  We then poll via
        'show system target-stack load' for real progress.
        """
        while chan.recv_ready():
            chan.recv(65535)
            time.sleep(0.1)
        if ensure_gi_cli:
            _ensure_gi_cli_for_command(chan, _log, "target-stack load")
        chan.send(f"request system target-stack load {load_url}\n")
        _log_upgrade_device_input(_log, f"request system target-stack load {load_url}")
        time.sleep(3)
        buf = ""
        answered_yes = False
        for _ in range(40):
            if chan.recv_ready():
                buf += chan.recv(65535).decode("utf-8", errors="replace")
            bl = buf.lower()
            if not answered_yes and ("continue?" in bl or "(yes/no)" in bl or "overwrite" in bl):
                chan.send("yes\n")
                _log_upgrade_device_input(_log, "yes", "load confirmation")
                answered_yes = True
                time.sleep(3)
                buf = ""
                continue
            # Check for errors regardless of prompt state -- catches 404, timeout, DNS failures
            if "error" in bl and "downloading" not in bl:
                break
            if "timed out" in bl or "not found" in bl or "failed" in bl or "refused" in bl:
                break
            if answered_yes:
                if "download finished" in bl or "added" in bl:
                    break
                if "download in progress" in bl or "started target-stack load" in bl:
                    time.sleep(2)
                    chan.send("\x03")
                    time.sleep(2)
                    while chan.recv_ready():
                        buf += chan.recv(65535).decode("utf-8", errors="replace")
                    break
            # Prompt returned without download starting (command finished quickly)
            if "#" in buf and re.search(r'[#>]\s*$', buf.rstrip()):
                break
            time.sleep(1)
        # If no prompt returned yet, send Ctrl+C to unblock
        if "#" not in buf:
            chan.send("\x03")
            time.sleep(2)
            if chan.recv_ready():
                buf += chan.recv(65535).decode("utf-8", errors="replace")
        while chan.recv_ready():
            chan.recv(65535)
            time.sleep(0.1)
        return buf

    def _poll_load_progress(comp_name_upper="", comp_url=""):
        """Poll download progress via 'show system target-stack load' (real-time %),
        then confirm via 'show system stack' Target column.
        Returns (output, pct, status).
        status: 'progress', 'complete', 'failed', 'idle'.
        """
        try:
            if ensure_gi_cli:
                _ensure_gi_cli_for_command(chan, _log, "target-stack load status")
            load_out = _sw("show system target-stack load | no-more", 5)
        except _GiCliReconnectRequired as drift:
            _refresh_gi_channel_after_drift(f"{comp_name_upper or 'image'} load status poll lost GI CLI: {drift}")
            return "", 0, "progress"
        except Exception:
            load_out = ""
        load_clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', load_out)
        load_lower = load_clean.lower()

        if "task status" in load_lower:
            pct_match = re.search(r'progress[:\s]+(\d+)\s*%', load_lower)
            pct_val = int(pct_match.group(1)) if pct_match else 0
            if "complete" in load_lower and "in-progress" not in load_lower:
                return load_clean, 100, "complete"
            elif "failed" in load_lower or "canceled" in load_lower:
                return load_clean, 0, "failed"
            elif "in-progress" in load_lower:
                return load_clean, pct_val, "progress"
        elif "error" in load_lower:
            return load_clean, 0, "failed"

        try:
            if ensure_gi_cli:
                _ensure_gi_cli_for_command(chan, _log, "target-stack stack poll")
            stack_out = _sw("show system stack | no-more", 4)
        except _GiCliReconnectRequired as drift:
            _refresh_gi_channel_after_drift(f"{comp_name_upper or 'image'} stack poll lost GI CLI: {drift}")
            return load_clean, pct_val if 'pct_val' in locals() else 0, "progress"
        except Exception:
            return load_clean, 0, "idle"
        stack_clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', stack_out)
        stack_targets = _parse_system_stack_targets(stack_clean)
        if comp_name_upper and _target_stack_has_expected_component(stack_targets, comp_name_upper, comp_url):
            return stack_clean, 100, "complete"
        if "failed" in stack_clean.lower():
            return stack_clean, 0, "failed"
        return stack_clean or load_clean, 0, "idle"

    for idx, (comp_name, url) in enumerate(actual_url_list):
        _check_upgrade_cancel(job_id)
        t_phase = time.time()
        pct = pct_base + int(pct_range * idx / max(len(url_list), 1))
        # Log the actual URL so user can see what's being sent to device
        url_short = url.rsplit('/', 1)[-1] if '/' in url else url
        _log("INFO", f"Loading {comp_name}: {url_short}")
        _update_device_state(job_id, device_id, phase=f"load {comp_name}", percent=pct,
                             message=f"Loading {comp_name}...")

        load_ok = False
        load_error = None
        max_wait = 600
        stall_threshold = 120
        max_retries = 2
        shell_reentered_for_component = False

        for load_attempt in range(1, max_retries + 2):
            _check_upgrade_cancel(job_id)
            if load_attempt > 1:
                _log("INFO", f"Retrying {comp_name} load (attempt {load_attempt}/{max_retries + 1})...")
                time.sleep(10)

            send_out = _send_load_cmd(url)
            send_lower = send_out.lower()
            if ensure_gi_cli and _looks_like_kvm_host_shell_output(send_out):
                raise _GiCliReconnectRequired(
                    f"{comp_name} load command reached KVM host shell; reconnect virsh console"
                )
            if (ensure_gi_cli and _looks_like_ncc_shell_output(send_out)
                    and not shell_reentered_for_component):
                shell_reentered_for_component = True
                _log("WARN",
                     f"{comp_name} load command hit NCC shell instead of GI CLI -- "
                     "re-entering GI and retrying once")
                _ensure_gi_cli_for_command(chan, _log, f"retrying {comp_name} load")
                continue
            # Detect errors -- 404, timeout, connection refused, download failure
            _has_error = ("error" in send_lower and "downloading" not in send_lower)
            _has_fail = any(kw in send_lower for kw in ("timed out", "not found", "failed", "refused", "404"))
            if _has_error or _has_fail:
                if "upgrade in progress" in send_lower:
                    _log("INFO", f"{comp_name}: upgrade in progress, waiting 15s...")
                    time.sleep(15)
                    continue
                clean_out = _upgrade_terminal_excerpt(
                    send_out,
                    [f"request system target-stack load {url}"],
                    limit=200,
                )
                load_error = clean_out or f"{comp_name} load returned error"
                _log("ERROR", f"{comp_name} load command returned error: {clean_out}")
                break
            if "download finished" in send_lower or "added" in send_lower:
                load_ok = True
                _log("OK", f"{comp_name} download completed immediately")
                break

            last_pct = 0
            last_progress_at = time.time()
            for _ in range(max_wait // 5):
                _check_upgrade_cancel(job_id)
                elapsed = int(time.time() - t_phase)
                if elapsed > max_wait:
                    break

                time.sleep(5)
                out_clean, pct_val, status = _poll_load_progress(comp_name.upper(), url)

                if pct_val > last_pct:
                    _log("INFO", f"{comp_name}: {pct_val}%")
                    last_pct = pct_val
                    last_progress_at = time.time()
                    pct_sub = pct + int(pct_range / max(len(url_list), 1) * min(pct_val / 100.0, 0.9))
                    _update_device_state(job_id, device_id, phase=f"load {comp_name}", percent=pct_sub,
                                         message=f"Loading {comp_name}... ({pct_val}%)")

                if status == "complete":
                    load_ok = True
                    break
                elif status == "failed":
                    load_error = _upgrade_terminal_excerpt(out_clean, limit=200) or out_clean[:200]
                    break
                elif status == "progress":
                    last_progress_at = time.time()
                elif status == "idle" and last_pct > 0:
                    load_ok = True
                    break
                elif status == "idle":
                    idle_duration = int(time.time() - last_progress_at)
                    if idle_duration > stall_threshold:
                        _log("WARN", f"{comp_name} stalled at {last_pct}% ({elapsed}s, no progress for {idle_duration}s) -- URL may be unreachable from device")
                        break
                    elif idle_duration > 30 and last_pct == 0:
                        # Extra check: re-read the load output for error messages
                        try:
                            recheck = _sw("show system target-stack load | no-more", 5)
                            recheck_lower = recheck.lower()
                            if any(kw in recheck_lower for kw in ("error", "failed", "timed out", "canceled")):
                                load_error = _upgrade_terminal_excerpt(
                                    recheck,
                                    ["show system target-stack load | no-more"],
                                    limit=200,
                                )
                                _log("ERROR", f"{comp_name} download failed: {load_error}")
                                break
                        except Exception:
                            pass

            if load_ok or load_error:
                break

        elapsed = round(time.time() - t_phase, 1)
        stage_times[f"load_{comp_name}"] = elapsed

        if load_error:
            _log("ERROR", f"{comp_name} load failed ({elapsed}s): {load_error}")
            raise RuntimeError(f"{comp_name} image load failed: {load_error}")
        elif load_ok:
            _log("OK", f"{comp_name} image loaded ({elapsed}s)")
        else:
            _log("WARN", f"{comp_name} load finished ({elapsed}s) -- 100% not confirmed")

    # Verify images were actually loaded via show system stack (Target column)
    _update_device_state(job_id, device_id, phase="verify-load", percent=pct_base + pct_range,
                         message="Verifying loaded images...")
    try:
        while chan.recv_ready():
            chan.recv(65535)
            time.sleep(0.1)
        if ensure_gi_cli:
            try:
                _ensure_gi_cli_for_command(chan, _log, "target-stack final verify")
            except _GiCliReconnectRequired as drift:
                _refresh_gi_channel_after_drift(f"target-stack final verify lost GI CLI: {drift}")
                _ensure_gi_cli_for_command(chan, _log, "target-stack final verify after reconnect")
        verify_out = _sw("show system stack | no-more", 5)
        clean_verify = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', verify_out)

        found, missing, _targets = _verify_stack_targets_for_urls(clean_verify, url_list)

        if found and not missing:
            _log("OK", f"Target-stack verified: {', '.join(sorted(found))} match selected URLs")
        elif missing:
            _log("WARN", f"Target-stack verification incomplete -- selected URL mismatch/missing for: {', '.join(sorted(missing))}")
        else:
            clean_excerpt = _upgrade_terminal_excerpt(
                clean_verify,
                ["show system stack | no-more"],
                limit=300,
            )
            _log("WARN", f"Target-stack verification unclear -- "
                         f"expected selected URLs, output: {clean_excerpt}")
    except Exception as ve:
        _log("WARN", f"Target-stack verify failed: {ve}")


def _push_target_image_to_dnos_stack_pre_delete(
        job_id, device_id, chan, url_list, stage_times, _log,
        replicate_timeout: int = 600, poll_interval: int = 15):
    """DEPRECATED / UNUSED since 2026-06-14 -- DO NOT re-wire into the
    delete+deploy flow. Loading the target stack BEFORE `request system
    delete` contradicts the canonical DNOS flow (delete -> load 3 tarballs
    in GI -> deploy); `request system delete` wipes the DNOS target stack
    so this push is wasted. The stale-image protection it provided now
    lives in `_run_delete_deploy_upgrade` Phase 6b (post-delete GI load +
    `_verify_stack_targets_for_urls` gate before deploy). Kept only for
    reference / potential manual diagnostics.

    Pre-delete safety net: push the user-selected image(s) into the
    DNOS-mode target stack BEFORE issuing ``request system delete``.

    Why this existed (2026-05-12 PE-4 incident):
    The old Drain+Deploy state machine went straight from "Config
    backup saved" to ``request system delete`` with NO
    ``set system stack target`` / ``request system target-stack load``
    step in between. When the device rebooted into GI mode,
    ``show system stack`` showed the stale pre-existing image as both
    Current AND Target (REPLICATED). A subsequent
    ``request system deploy`` would have redeployed the OLD image. The
    user had to manually push the target image and re-launch.

    This helper closes that hole by:

    1. Calling ``_load_images_on_channel`` with ``ensure_gi_cli=False``
       (we are still in DNOS mode; dncli is up). The underlying load
       command (``request system target-stack load <url>``) is the
       documented DNOS norm and the active NCC auto-replicates the
       result to the standby NCC and all NCPs / NCFs (see
       ``~/SCALER/dnos_cheetah_docs/Request Commands/request system
       target-stack load.rst`` -- line 28 of that doc: "In a cluster,
       the active NCC replicates a target stack to the standby NCC").
    2. Polling ``show system stack`` with a generous timeout (default
       10 min) until ``_verify_stack_targets_for_urls`` reports zero
       missing components. The cluster replication usually completes
       within seconds because the package is already loaded on the
       active NCC; we wait up to ``replicate_timeout`` for the slow
       NCM/firmware paths.
    3. RAISING ``RuntimeError`` on persistent mismatch -- the caller
       MUST treat this as an abort and skip ``request system delete``.
       The whole point of this helper is to refuse delete-reboot on a
       device whose GI target is stale.

    NEVER issues a destructive command. Pure read+load. Safe to call
    multiple times -- the underlying load is idempotent (skips
    already-loaded images via its own pre-check).
    """
    import time
    import re

    if not url_list:
        raise RuntimeError(
            "Pre-delete target-image push called with empty url_list. "
            "The Drain+Deploy flow refuses to delete-reboot a device "
            "with no images to push (2026-05-12 PE-4 pre-flight gate)."
        )

    _log("INFO",
         "Pre-delete: pushing selected image(s) to DNOS target stack "
         "BEFORE `request system delete` (2026-05-12 hardening). "
         f"Selected: {', '.join(c for c, _ in url_list if _)}")
    _update_device_state(job_id, device_id, phase="pre-delete-load", percent=6,
                         message="Pre-delete: pushing target image(s)...")

    t_phase = time.time()
    try:
        _load_images_on_channel(
            job_id, device_id, chan, url_list, stage_times, _log,
            pct_base=6, pct_range=2, ensure_gi_cli=False)
    except Exception as load_err:
        elapsed = round(time.time() - t_phase, 1)
        raise RuntimeError(
            f"Pre-delete target-image push FAILED ({elapsed}s): {load_err}. "
            f"Refusing to issue `request system delete` -- the device's "
            f"GI target would be the OLD image, causing a re-deploy of "
            f"the stale stack. (2026-05-12 PE-4 pre-flight gate.)"
        ) from load_err

    deadline = time.time() + max(60, int(replicate_timeout))
    _sw = _make_send_wait(chan)
    last_missing: list[str] = []
    last_targets: dict = {}
    poll_count = 0
    while time.time() < deadline:
        poll_count += 1
        elapsed = int(time.time() - t_phase)
        _update_device_state(
            job_id, device_id, phase="pre-delete-verify", percent=8,
            message=(f"Verifying replicated target stack "
                     f"({elapsed}s, poll #{poll_count})..."))
        try:
            while chan.recv_ready():
                chan.recv(65535)
                time.sleep(0.1)
            verify_out = _sw("show system stack | no-more", 5)
            clean_verify = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', verify_out)
            found, missing, targets = _verify_stack_targets_for_urls(
                clean_verify, url_list)
            last_missing = list(missing or [])
            last_targets = targets or {}
            if found and not missing:
                wall = round(time.time() - t_phase, 1)
                stage_times["pre_delete_load"] = wall
                _log("OK",
                     f"Pre-delete target stack verified after {wall}s: "
                     f"{', '.join(sorted(found))} match selected URLs. "
                     "Safe to proceed with `request system delete`.")
                return
        except Exception as verify_err:
            _log("WARN",
                 f"Pre-delete stack verify poll #{poll_count} hiccupped: "
                 f"{verify_err} -- retrying after {poll_interval}s")
        time.sleep(max(1, int(poll_interval)))

    wall = round(time.time() - t_phase, 1)
    excerpt = "; ".join(
        f"{k}: target={v.get('target', '?')}"
        for k, v in (last_targets or {}).items()
    ) or "(no targets parsed)"
    raise RuntimeError(
        f"Pre-delete target-image push did NOT confirm replication "
        f"within {replicate_timeout}s (wall {wall}s). Missing/mismatch: "
        f"{', '.join(sorted(last_missing)) or 'unknown'}. Current "
        f"target stack: {excerpt}. Refusing to issue `request system "
        f"delete` -- the device's GI target stack is stale, the post-"
        f"reboot `request system deploy` would redeploy the OLD image. "
        f"Verify the image URL is reachable from the device and retry "
        f"(2026-05-12 PE-4 pre-flight gate (b))."
    )


def _send_install_command(chan, _log):
    """Send 'request system target-stack install' with yes/no prompt handling.

    Polls every 0.5s for the confirmation prompt and answers 'yes' immediately.
    Returns install output text.  Socket-close after install is EXPECTED (device reboots).
    """
    import time, re

    cmd = "request system target-stack install"
    # DNOS auto-runs a target-stack precheck after `target-stack load` (and our
    # explicit `pre-check` send returns before that async task finishes).
    # Issuing `install` while it is still running is rejected with
    # "Another precheck task is already in-progress" -- which previously caused
    # NO reboot and then a 600s post-install verify timeout (false failure).
    # Retry the install until the precheck clears, the confirmation prompt
    # appears, or the device reboots (socket closes).
    max_wait = 600          # total seconds to keep retrying past precheck collisions
    per_attempt = 30        # seconds to watch each attempt for prompt/reboot/collision
    retry_interval = 20     # wait between collision retries
    deadline = time.time() + max_wait
    attempt = 0
    last_buf = b""
    while True:
        attempt += 1
        try:
            chan.send(b"\x03"); time.sleep(1)
            while chan.recv_ready():
                chan.recv(65535); time.sleep(0.1)
            chan.send(b"\r"); time.sleep(1.5)
            while chan.recv_ready():
                chan.recv(65535); time.sleep(0.1)
        except (OSError, EOFError):
            _log("OK", "Channel closed before install send -- device may be rebooting")
            return last_buf.decode("utf-8", errors="replace")
        _log("INFO", f"Starting target-stack install (device will reboot)... [attempt {attempt}]")
        chan.send(cmd.encode() + b"\n")
        _log_upgrade_device_input(_log, cmd)
        buf = b""
        confirmed = False
        collision = False
        t_end = time.time() + per_attempt
        while time.time() < t_end:
            time.sleep(0.5)
            try:
                if chan.recv_ready():
                    buf += chan.recv(65535)
            except (OSError, EOFError) as e:
                es = str(e).lower()
                if "socket" in es or "eof" in es or "closed" in es:
                    _log("OK", "Install request accepted -- device rebooting (connection closed as expected)")
                    return buf.decode("utf-8", errors="replace")
                raise
            text = buf.decode("utf-8", errors="replace")
            lo = text.lower()
            if ("another precheck task is already in-progress" in lo
                    or ("precheck" in lo and "in-progress" in lo)
                    or ("pre-check" in lo and "in-progress" in lo)):
                collision = True
                break
            if not confirmed and ("yes/no" in lo or "y/n" in lo or "do you want" in lo or "continue" in lo):
                _log("INFO", "Install confirmation prompt detected -- answering 'yes'")
                chan.send(b"yes\n")
                _log_upgrade_device_input(_log, "yes", "install confirmation")
                confirmed = True
                time.sleep(3)
                try:
                    if chan.recv_ready():
                        buf += chan.recv(65535)
                except (OSError, EOFError):
                    _log("OK", "Install confirmed -- device rebooting (connection closed)")
                    return buf.decode("utf-8", errors="replace")
                continue
            if confirmed:
                clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text).rstrip()
                if re.search(r'[#>]\s*$', clean):
                    return buf.decode("utf-8", errors="replace")
        last_buf = buf
        if time.time() >= deadline:
            if collision:
                _log("WARN", f"Install still blocked by an in-progress precheck after {max_wait}s -- giving up retry")
            return buf.decode("utf-8", errors="replace")
        if collision:
            _log("INFO", f"Install blocked: a target-stack precheck is still in-progress; waiting {retry_interval}s then retrying...")
        else:
            _log("INFO", f"Install not yet accepted (no prompt/reboot); waiting {retry_interval}s then retrying...")
        time.sleep(retry_interval)


def _post_install_verify(job_id, device_id, mgmt_ip, user, password,
                          url_list, stage_times, _log, was_cluster=False,
                          verify_timeout=2400, check_interval=20):
    """After target-stack install, wait for device to reboot and verify new images.

    `request system target-stack install` runs a precheck, installs the stack,
    then REBOOTS (the box passes through GI and back to DNOS). A full
    DNOS+GI+BaseOS install + reboot routinely takes 20-40 min, so the window is
    generous (default 2400s). We poll until the TARGET versions actually appear
    -- a reachable device still on the OLD build (precheck still running, or
    mid-transition) is NOT success; we keep monitoring through the GI->DNOS
    transition until the full target stack matches or the window expires.
    Logs PASS/FAIL but does not raise (the install was already sent).
    """
    import time

    _update_device_state(job_id, device_id, phase="post-install-verify", percent=90,
                         message="Waiting for device to come back after install...")
    _log("INFO", f"Post-install verification (timeout {verify_timeout}s)")

    t_phase = time.time()
    time.sleep(60)

    # SERIAL-anchored reconnection: never trust a fixed mgmt IP across a reboot
    # (cluster failover / console flap / DHCP can all change it, and for KVM
    # clusters the configured IP may be the DOWN NCC). Each poll, re-resolve the
    # IP that ACTUALLY REPORTS THIS DEVICE'S SERIAL via the dnos-config SN
    # resolver (`_resolve_verified_ip` confirms `show system` serial before
    # trusting an IP, self-healing on churn). Fall back to the passed IP only if
    # the resolver is unavailable.
    def _sn_ip(default_ip):
        try:
            import sys as _sys
            if "/home/dn/dnos_config_mcp" not in _sys.path:
                _sys.path.insert(0, "/home/dn/dnos_config_mcp")
            from dnos_config_mcp.devices import resolve as _dns_resolve
            _rip, _u, _p, _m = _dns_resolve(device_id)
            return _rip or default_ip
        except Exception:
            return default_ip

    start = time.time()
    verified = False
    while time.time() - start < verify_timeout:
        try:
            _check_upgrade_cancel(job_id)
        except _UpgradeCancelled:
            raise
        elapsed = int(time.time() - start)
        _update_device_state(job_id, device_id, phase="post-install-verify",
                             percent=90 + min(elapsed // 30, 8),
                             message=f"Reconnecting after install... ({elapsed}s)")
        cli = None
        ch = None
        try:
            cur_ip = _sn_ip(mgmt_ip)
            cli, ch = _ssh_connect_basic(cur_ip, user, password)
            sw = _make_send_wait(ch)
            out = sw("show system install | no-more", 5)
            clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', out)
            _log("INFO", "Post-install status:\n"
                 f"{_upgrade_terminal_excerpt(clean, ['show system install | no-more'], limit=600)}")

            expected = {}
            for comp_name, url in url_list:
                ver = re.search(r'(\d+\.\d+\.\d+[\d._]*)', url)
                if ver:
                    expected[comp_name.upper()] = ver.group(1)

            matches = 0
            for comp, exp_ver in expected.items():
                if exp_ver in clean:
                    matches += 1
                    _log("OK", f"Post-install: {comp} version {exp_ver} confirmed")
                else:
                    _log("WARN", f"Post-install: {comp} version {exp_ver} NOT found in install output")

            if matches == len(expected) and expected:
                _log("OK", f"All {matches} component(s) verified after install ({elapsed}s)")
                verified = True
            elif matches > 0:
                # Partial match = the device is reachable but the stack is still
                # switching (e.g. DNOS already on target, BaseOS/GI not yet).
                # Keep monitoring until the FULL target stack matches; do NOT
                # declare success or give up here.
                _log("INFO", f"{matches}/{len(expected)} component(s) on target so far "
                             f"({elapsed}s) -- stack still switching, continuing to monitor")
            else:
                # Reachable but still on the OLD build (precheck/install not done,
                # or we caught it pre-reboot / in a transient GI->DNOS bounce).
                _log("INFO", f"Device reachable but not yet on the target build "
                             f"({elapsed}s) -- still installing/rebooting, continuing to monitor")
            if verified:
                break
        except Exception:
            # Swallow the per-iteration error; the device may still be
            # rebooting. The `finally` below guarantees we close whatever
            # Paramiko handed us, even when `_ssh_connect_basic` raised
            # after opening the transport (which used to leak one TCP
            # connection per retry and quickly starved the process FD
            # budget on a slow-rebooting chassis).
            pass
        finally:
            try:
                if ch is not None:
                    ch.close()
            except Exception:
                pass
            try:
                if cli is not None:
                    cli.close()
            except Exception:
                pass
        time.sleep(check_interval)

    stage_times["post_install_verify"] = round(time.time() - t_phase, 1)
    if not verified:
        _log("WARN", f"Post-install verification timed out ({verify_timeout}s) -- "
             f"device may still be rebooting. Check manually via SSH.")
    return verified


def _run_normal_upgrade(job_id, device_id, mgmt_ip, user, password,
                         url_list, stage_times, _log, pre_connected=None):
    """Standard upgrade: load images -> pre-check -> install.

    pre_connected: optional (ssh_client, channel) from connect_for_upgrade for KVM
    clusters when NCC mgmt IP is not cached (virsh console path).
    """
    import time

    t_phase = time.time()
    if pre_connected:
        client, chan = pre_connected
    else:
        client, chan = _ssh_connect_basic(mgmt_ip, user, password)
    stage_times["connect"] = round(time.time() - t_phase, 1)
    _send_wait = _make_send_wait(chan)

    try:
        import time as _t_mod
        chan.send("\n")
        _t_mod.sleep(1)
        _prompt_buf = ""
        while chan.recv_ready():
            _prompt_buf += chan.recv(65535).decode("utf-8", errors="replace")
        _prompt_clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', _prompt_buf).strip()
        if re.search(r'\bGI[#(]', _prompt_clean) or re.search(r'\bGI\s*\(', _prompt_clean):
            raise RuntimeError(
                f"Device is in GI mode (prompt: {_prompt_clean[-60:]}) -- "
                f"switch to the GI deploy flow for this upgrade.")

        pre_upgrade_config = ""
        try:
            t_phase = time.time()
            _update_device_state(job_id, device_id, phase="snapshot", percent=5)
            pre_upgrade_config = _send_wait("show config | no-more", 3)
            stage_times["snapshot"] = round(time.time() - t_phase, 1)
            _log("INFO", "Pre-upgrade config snapshot taken")
        except Exception as snap_err:
            _log("WARN", f"Config snapshot failed: {snap_err}")

        _update_device_state(job_id, device_id, phase="load", percent=10)
        _load_images_on_channel(job_id, device_id, chan, url_list, stage_times, _log)

        if pre_upgrade_config:
            t_phase = time.time()
            _update_device_state(job_id, device_id, phase="config-repair", percent=65)
            _post_upgrade_config_repair(job_id, device_id, chan, pre_upgrade_config)
            stage_times["config_repair"] = round(time.time() - t_phase, 1)

        t_phase = time.time()
        _update_device_state(job_id, device_id, phase="pre-check", percent=75)
        _log("INFO", "Running pre-check...")
        pre_out = _send_wait("request system target-stack pre-check", 15)
        stage_times["pre_check"] = round(time.time() - t_phase, 1)
        if "error" in pre_out.lower() and "status: ok" not in pre_out.lower():
            clean_pre = _upgrade_terminal_excerpt(
                pre_out,
                ["request system target-stack pre-check"],
                limit=200,
            )
            _log("WARN", f"Pre-check output: {clean_pre}")

        t_phase = time.time()
        _update_device_state(job_id, device_id, phase="install", percent=85)
        _log("INFO", "Installing (device will reboot)...")
        install_out = _send_install_command(chan, _log)
        stage_times["install"] = round(time.time() - t_phase, 1)
        clean_out = _upgrade_terminal_excerpt(
            install_out,
            ["request system target-stack install"],
            limit=400,
        )
        _log("INFO", f"Install output: {clean_out}")
    finally:
        try:
            client.close()
        except Exception:
            pass

    verified = _post_install_verify(job_id, device_id, mgmt_ip, user, password,
                                    url_list, stage_times, _log, pre_connected is not None)
    if not verified:
        raise RuntimeError(
            "Post-install verification failed -- device did not come back with expected "
            "versions. The device may still be rebooting or the install may have failed. "
            "Check device state manually via SSH.")


def _run_delete_deploy_upgrade(job_id, device_id, mgmt_ip, user, password,
                                url_list, deploy_params, stage_times, _log,
                                scaler_hostname=""):
    """Full delete+deploy: delete system -> wait GI -> load images -> deploy.
    Mirrors the CLI wizard's battle-tested flow from interactive_scale.py.

    scaler_hostname: canonical hostname for connect_for_upgrade and DB paths.
    """
    import time
    from pathlib import Path
    import json

    scaler_hostname = scaler_hostname or device_id
    if scaler_hostname:
        # Atomic identity canon: collapse aliases/serial to the single canonical
        # config-device dir so pre-config backups + operational.json are saved
        # under ONE identity (e.g. YOR_PE-1 -> PE-1), never a pseudo-identity dir.
        scaler_hostname = _resolve_config_dir(scaler_hostname) or scaler_hostname

    # Phase 1: Connect via connect_for_upgrade (handles SSH/console/virsh)
    t_phase = time.time()
    _update_device_state(job_id, device_id, phase="connecting", percent=2,
                         message="Connecting to device...")

    os.chdir(SCALER_ROOT)
    from scaler.connection_strategy import connect_for_upgrade
    conn = connect_for_upgrade(scaler_hostname, timeout=60)

    if not conn["connected"]:
        raise RuntimeError(f"Cannot connect to {scaler_hostname}: {conn.get('abort_reason', 'unknown')}")

    # 2026-05-12 PE-4 stuck-in-GI gate (in-job defense-in-depth). Refuse to
    # proceed with the destructive D+D flow if the wizard payload reached
    # this thread with no installable URLs. Phase 6 would silently skip
    # the image push and Phase 7 would redeploy the OLD target stack -- the
    # device "upgrades" back into its previous image. We hard-fail here
    # BEFORE Phase 2 snapshot + Phase 4 `request system delete` so the
    # device is left untouched.
    try:
        _assert_url_list_in_job(
            device_id, "delete_deploy", url_list,
            scaler_hostname=scaler_hostname)
    except RuntimeError as _empty_url_err:
        _log("ERROR", str(_empty_url_err))
        _update_device_state(
            job_id, device_id, phase="error", percent=2,
            message=("FAILED: empty url_list for Drain+Deploy -- refusing "
                     "to delete-reboot a device with no images to push."))
        try:
            conn["ssh"].close()
        except Exception:
            pass
        raise

    client = conn["ssh"]
    chan = conn["channel"]
    conn_method = conn.get("method", "unknown")
    conn_state = conn.get("device_state", "")
    # Capture the active NCC identity BEFORE `request system delete` wipes the
    # device. The SSH credentials panel consumes these fields via the push-job
    # device_state stream so it can pre-suggest "Clear host key-check" against
    # the same NCC the operator was just connected to -- otherwise the post-
    # delete reboot will serve a fresh host key and the next SSH attempt trips
    # the known_hosts mismatch warning.
    pre_delete_active_ncc_vm = conn.get("active_ncc_vm", "") or ""
    pre_delete_active_ncc_id = conn.get("ncc_id")
    pre_delete_mgmt_ip = conn.get("ip") or mgmt_ip or ""
    _log("INFO",
         f"Connected via {conn_method} (state={conn_state}"
         f"{', ncc=' + pre_delete_active_ncc_vm if pre_delete_active_ncc_vm else ''}"
         f"{', ncc_id=' + str(pre_delete_active_ncc_id) if pre_delete_active_ncc_id is not None else ''})")

    # If device is already in GI, skip delete and go straight to load+deploy
    if conn_state in ("GI", "BASEOS_SHELL"):
        _log("INFO", "Device already in GI mode, skipping delete -- loading images directly")
        stage_times["connect"] = round(time.time() - t_phase, 1)

        client, chan, recovered_ncc_id, recovered = _preflight_gi_health(
            job_id, device_id, chan, client, scaler_hostname, _log)
        if recovered and recovered_ncc_id is not None:
            deploy_params["ncc_id"] = recovered_ncc_id

        try:
            _update_device_state(job_id, device_id, phase="load", percent=35,
                                 message="Loading images (device already in GI)...")
            _load_images_on_channel(job_id, device_id, chan, url_list, stage_times, _log,
                                    pct_base=35, pct_range=40, ensure_gi_cli=True)
            try:
                _ensure_gi_cli_for_command(chan, _log, "pre-deploy stack verification")
                _sw_pre = _make_send_wait(chan)
                sv = _sw_pre("show system stack | no-more", 4)
                sc = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', sv)
                _log("INFO", "Pre-deploy stack:\n"
                     f"{_upgrade_terminal_excerpt(sc, ['show system stack | no-more'], limit=500)}")
                loaded_comps, missing_comps, _targets = _verify_stack_targets_for_urls(sc, url_list)
                if missing_comps:
                    _log("ERROR", f"Images NOT loaded or mismatched: {', '.join(sorted(missing_comps))}")
                    raise RuntimeError(f"Cannot deploy: target-stack target mismatch for {', '.join(sorted(missing_comps))}")
                _log("OK", f"All selected images verified: {', '.join(sorted(loaded_comps))}")
            except RuntimeError:
                raise
            except Exception:
                _log("WARN", "Stack verification skipped -- proceeding")
            t_deploy = time.time()
            sys_type = deploy_params.get("system_type") or ""
            d_name = deploy_params.get("deploy_name") or device_id
            # `_safe_ncc_id` handles the whole `None` / `"None"` / empty
            # / out-of-range menagerie in one place. `.get("ncc_id", 0)`
            # USED TO LOOK SAFE but the default only fires on missing
            # keys -- a wizard payload of {"ncc_id": null} propagates
            # None straight into `f"ncc-id {ncc_id}"`. See
            # `_safe_ncc_id` docstring for the full root-cause story.
            ncc_id = _safe_ncc_id(deploy_params.get("ncc_id"))
            if not sys_type:
                _resolved = _resolve_deploy_system_type(device_id, scaler_hostname, _log)
                if _resolved:
                    sys_type = _resolved
            if not sys_type:
                _log("ERROR", "Cannot deploy: system_type unknown. Select it in the upgrade wizard.")
                _update_device_state(job_id, device_id, phase="error", percent=80,
                                     message="FAILED: system_type unknown -- select it in the upgrade wizard",
                                     system_type_unknown=True)
                return
            _log("INFO", f"Deploy params resolved: system_type={sys_type}, name={d_name}, ncc_id={ncc_id}")
            _update_device_state(job_id, device_id, phase="deploying", percent=80,
                                 message=f"Deploying target system ({sys_type})...")
            deploy_out, ncc_id, old_install_task_id = _send_deploy_command(
                chan, sys_type, d_name, ncc_id, _log)
            stage_times["deploy"] = round(time.time() - t_deploy, 1)
            _log("OK", f"Deploy request accepted ({stage_times['deploy']}s)")
            if deploy_params is not None:
                deploy_params["old_install_task_id"] = old_install_task_id
                deploy_params["ncc_id"] = ncc_id
        finally:
            try:
                client.close()
            except Exception:
                pass
        return

    stage_times["connect"] = round(time.time() - t_phase, 1)
    _send_wait = _make_send_wait(chan)

    # Phase 2: Snapshot running config (for later restore if needed)
    #
    # CRITICAL: we must save the live config BEFORE `request system delete`
    # wipes the device. Post-deploy, the on-device rollback history will NOT
    # contain this config (delete flushes the stack), so a file-based restore
    # is the only reliable path.
    #
    # We write TWO files for backwards compatibility:
    #   - pre_delete_config.txt          -- stable name for the GUI restore API
    #   - pre_delete_backup_<ts>.txt     -- matches scaler CLI naming, keeps
    #                                       history of multiple attempts
    # Also register the latest path in operational.json so both the CLI's
    # "Restore Pre-Delete Configuration" menu and the GUI /restore-config API
    # can find it without guessing.
    pre_upgrade_config = ""
    pre_delete_backup_path = ""
    commit_list_out = ""
    try:
        t_phase = time.time()
        _update_device_state(job_id, device_id, phase="snapshot", percent=5,
                             message="Backing up configuration...")
        pre_upgrade_config = _send_wait("show config | no-more", 3)
        pre_upgrade_config = _maybe_repair_stripped_config_before_delete(
            job_id, device_id, scaler_hostname, chan, pre_upgrade_config, _log,
            mgmt_ip_hint=pre_delete_mgmt_ip)
        stage_times["snapshot"] = round(time.time() - t_phase, 1)
        _log("OK", "Pre-delete config snapshot taken")

        try:
            commit_list_out = _send_wait("show config commit list | no-more", 3)
        except Exception:
            commit_list_out = ""

        try:
            from datetime import datetime as _dt_bk
            ts = _dt_bk.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname
            backup_dir.mkdir(parents=True, exist_ok=True)
            fixed_path = backup_dir / "pre_delete_config.txt"
            ts_path = backup_dir / f"pre_delete_backup_{ts}.txt"
            _atomic_write_text(fixed_path, pre_upgrade_config)
            _atomic_write_text(ts_path, pre_upgrade_config)
            pre_delete_backup_path = str(ts_path)
            # Also preserve the pre-upgrade config in the timestamped device
            # HISTORY store (db/history/<device>/), matching the monitor's
            # naming, under the canonical identity. /repair now searches history
            # too, so this guarantees the COMPLETE pre-upgrade config is always
            # recoverable -- even if the monitor missed the snapshot moment
            # (root-caused 2026-06-24: PE-1's full pre-fail config with the
            # global BGP hierarchy lived only in db/history, not in the
            # db/configs pre_upgrade_backup that repair originally used).
            try:
                hist_dir = Path(SCALER_ROOT) / "db" / "history" / scaler_hostname
                hist_dir.mkdir(parents=True, exist_ok=True)
                hist_ts = _dt_bk.now().strftime("%Y-%m-%d_%H-%M")
                _atomic_write_text(hist_dir / f"{hist_ts}_{scaler_hostname}.txt",
                                   pre_upgrade_config)
                _log("INFO", f"Pre-upgrade config mirrored to history: "
                             f"{hist_ts}_{scaler_hostname}.txt")
            except Exception as _hist_err:
                _log("WARN", f"Saving pre-upgrade history snapshot failed: {_hist_err}")
            if commit_list_out:
                try:
                    _atomic_write_text(
                        backup_dir / f"pre_delete_commit_list_{ts}.txt",
                        commit_list_out,
                    )
                except Exception:
                    pass
            lines_count = len([l for l in pre_upgrade_config.splitlines() if l.strip()])
            _log("INFO",
                 f"Config backup saved to disk ({lines_count} lines, path={ts_path.name})")
        except Exception as _save_err:
            _log("WARN", f"Saving pre-delete backup file failed: {_save_err}")
    except Exception as snap_err:
        _log("WARN", f"Config snapshot failed: {snap_err}")
        try:
            backup_dir = Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname
            existing = sorted(
                list(backup_dir.glob("pre_delete_backup_*.txt"))
                + list(backup_dir.glob("pre_upgrade_backup_*.txt")),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if existing:
                pre_delete_backup_path = str(existing[0])
                _log("WARN",
                     f"Falling back to newest existing backup: {existing[0].name}")
        except Exception:
            pass

    # Phase 3: Detect deploy params from device if not provided
    if not deploy_params or not deploy_params.get("system_type"):
        deploy_params = _detect_deploy_params(chan, device_id, _send_wait, _log)
    else:
        _log("INFO", f"Using provided deploy params: {deploy_params}")

    # Phase 3.5: REMOVED (2026-06-14). The canonical DNOS delete+deploy flow
    # is exactly: `request system delete` -> reboot into GI -> load the 3
    # tarballs (DNOS, GI, BaseOS) IN GI -> `request system deploy`. Images
    # are NEVER loaded before delete: `request system delete` wipes the DNOS
    # target stack, so a pre-delete push is redundant work that contradicts
    # the documented flow. (Old behaviour: 2026-05-12 PE-4 hardening pushed
    # the target image into the DNOS-mode stack before delete -- removed.)
    #
    # Both safety goals the old pre-delete push served are preserved WITHOUT
    # loading before delete:
    #   * Empty url_list abort -- enforced at Phase 1 by
    #     `_assert_url_list_in_job`, which hard-fails BEFORE `request system
    #     delete` if there are no images to push.
    #   * Stale-image redeploy guard -- enforced at Phase 6b: after the GI
    #     load we run `show system stack` + `_verify_stack_targets_for_urls`
    #     and RAISE (blocking the Phase 7 deploy) if any selected component
    #     is missing/mismatched in the Target column. A stale target can
    #     therefore never reach `request system deploy`; worst case is a
    #     safe, blocked deploy that the operator retries.
    # See DEVELOPMENT_GUIDELINES.md "Canonical delete+deploy flow".

    # Save deploy params to operational.json for recovery AND quarantine the
    # stack versions. The device is about to wipe its current stack; any
    # Phase-1 / Phase-2 read between `request system delete` completing and
    # our Phase-5 GI detection would otherwise show the OLD current versions
    # as if they were still installed -- this is exactly the drift that
    # makes the upgrade wizard falsely offer "skip (at target)" for a
    # device that's actually sitting in GI with no stack at all.
    try:
        op_file = Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname / "operational.json"
        op_file.parent.mkdir(parents=True, exist_ok=True)
        from datetime import datetime as dt
        _dp_sys = deploy_params.get("system_type", "")
        _dp_name = deploy_params.get("deploy_name", device_id)
        _dp_ncc = _safe_ncc_id(deploy_params.get("ncc_id"))
        _delete_now_iso = dt.now().isoformat()
        _pre_ncc_int = (
            int(pre_delete_active_ncc_id)
            if pre_delete_active_ncc_id is not None
            else None
        )
        _pre_backup_path = pre_delete_backup_path

        from routes._ops_writer import update_ops as _update_ops_dd

        def _dd_mutator(op_data):
            # Carry pre_delete_backup forward if we don't have a new one
            _prior_backup = op_data.get("pre_delete_backup", "")
            _prior_ncc_ip = (op_data.get("ncc_mgmt_ip") or "").strip()
            op_data.update({
                "deploy_system_type": _dp_sys,
                "deploy_name": _dp_name,
                "deploy_ncc_id": str(_dp_ncc),
                "deploy_command": (
                    f"request system deploy system-type {_dp_sys} "
                    f"name {_dp_name} ncc-id {_dp_ncc}"
                ) if _dp_sys else "",
                "delete_initiated": _delete_now_iso,
                "delete_source": "wizard",
                "device_state": "GI",
                "recovery_mode_detected": True,
                "recovery_type": "GI",
                "upgrade_in_progress": True,
                "upgrade_job_id": job_id,
                "pre_delete_active_ncc_vm": pre_delete_active_ncc_vm,
                "pre_delete_active_ncc_id": _pre_ncc_int,
                "pre_delete_mgmt_ip": pre_delete_mgmt_ip,
                # Pre-delete mgmt IPs are at risk of becoming ghost once DHCP
                # reassigns them during the reboot. Stash a copy so any post-
                # delete monitor can cross-check and preempt a ghost landing.
                "pre_delete_ncc_mgmt_ip": _prior_ncc_ip,
                # Pre-delete backup file path -- consumed by both the CLI
                # "Restore Pre-Delete Configuration" menu and the GUI
                # /api/image-upgrade/restore-config endpoint. Falls back to
                # the previously-registered backup when today's snapshot
                # failed.
                "pre_delete_backup": _pre_backup_path or _prior_backup,
                "pre_delete_backup_at": _delete_now_iso,
                # Quarantine markers: Phase-1/Phase-2 readers use these to
                # suppress stale fields until Phase-5 confirms GI arrival.
                "_delete_pending": True,
                "_delete_pending_at": _delete_now_iso,
            })
            # Clear cached "current" versions -- they will become invalid
            # the moment `request system delete` completes. Readers should
            # see the device as version-less until post-deploy verify
            # restores them.
            op_data.pop("dnos_version", None)
            op_data.pop("gi_version", None)
            op_data.pop("baseos_version", None)
            _sc_q = op_data.get("stack_components")
            if isinstance(_sc_q, list):
                for _c_q in _sc_q:
                    if isinstance(_c_q, dict):
                        _c_q["current"] = "-"
            return True

        # create_if_missing=True because brand-new devices may not have an
        # operational.json yet; we still need to record quarantine state.
        _update_ops_dd(op_file, _dd_mutator, create_if_missing=True)
    except Exception as _op_err:
        _log("WARN", f"Could not persist pre-delete operational state: {_op_err}")

    # Phase 4: Execute system delete
    t_phase = time.time()
    from datetime import datetime as _dt_now
    _delete_iso = _dt_now.now().isoformat()
    # Publish the pre-delete NCC identity to the push-job device_state so the
    # frontend SSH credentials panel can surface "Clear host key-check on
    # NCC-<id> (<vm>)" the moment the user re-opens it after the delete. We
    # emit this BEFORE sending `request system delete` so the SSE snapshot
    # always has it, even if the delete later fails mid-flight.
    _pre_delete_int_id = (
        int(pre_delete_active_ncc_id)
        if pre_delete_active_ncc_id is not None
        else None
    )
    _update_device_state(
        job_id, device_id,
        phase="deleting", percent=10,
        message="Executing system delete...",
        suggest_clear_host_key=True,
        pre_delete_active_ncc_vm=pre_delete_active_ncc_vm,
        pre_delete_active_ncc_id=_pre_delete_int_id,
        pre_delete_mgmt_ip=pre_delete_mgmt_ip,
        delete_initiated_at=_delete_iso,
    )
    _log("INFO", "Starting system delete -- device will reboot into GI mode")
    # Phase marker: stamp BEFORE the channel send so a crash mid-send
    # is still recognisable on resume.
    try:
        _stamp_phase(scaler_hostname, "delete_sent_at", _log)
    except Exception:
        pass
    chan.send("request system delete\n")
    _log_upgrade_device_input(_log, "request system delete")
    time.sleep(3)
    while chan.recv_ready():
        chan.recv(65535)
        time.sleep(0.3)
    chan.send("yes\n")
    _log_upgrade_device_input(_log, "yes", "delete confirmation")
    time.sleep(2)
    while chan.recv_ready():
        chan.recv(65535)
    stage_times["delete"] = round(time.time() - t_phase, 1)
    try:
        _stamp_phase(scaler_hostname, "delete_completed_at", _log)
    except Exception:
        pass
    _log("OK", "System delete initiated, device will reboot into GI mode")

    # Close SSH -- device is rebooting
    try:
        client.close()
    except Exception:
        pass

    # Phase 5: Wait for GI mode via connect_for_upgrade
    t_phase = time.time()
    gi_mode_timeout = 420  # 7 minutes (delete can take a while)
    gi_check_interval = 30
    gi_start = time.time()
    gi_connected = False
    gi_ssh = None
    gi_chan = None

    _update_device_state(job_id, device_id, phase="waiting-for-gi", percent=15,
                         message="Waiting for device to reboot into GI mode...")
    _log("INFO", "Waiting for GI mode (checking every 30s, timeout 7min)...")

    while time.time() - gi_start < gi_mode_timeout:
        # Honour user cancel requests while we wait for the device to come
        # back in GI mode. Prior behaviour held a 30s `time.sleep` and only
        # checked cancel on entry to _run_device_upgrade, so a cancel sent
        # right after `request system delete` had no effect until +7 minutes.
        _check_upgrade_cancel(job_id)
        elapsed = int(time.time() - gi_start)
        _update_device_state(job_id, device_id, phase="waiting-for-gi", percent=15 + min(elapsed // 15, 15),
                             message=f"Waiting for GI mode... ({elapsed}s)")

        time.sleep(gi_check_interval)

        try:
            os.chdir(SCALER_ROOT)
            from scaler.connection_strategy import connect_for_upgrade
            conn = connect_for_upgrade(scaler_hostname, timeout=15)
            if conn["connected"]:
                state = conn.get("device_state") or ""
                method = conn.get("method", "unknown")
                if state in ("GI", "BASEOS_SHELL"):
                    gi_ssh = conn["ssh"]
                    gi_chan = conn["channel"]
                    gi_connected = True
                    _log("OK", f"Device in GI mode (via {method}, {elapsed}s)")

                    # Phase marker: GI confirmed live. Resumer uses this
                    # to know "skip replay of `request system delete`,
                    # the device is already in GI". We stamp BEFORE the
                    # operational.json mutation below so a crash between
                    # the two writes still leaves the marker in place.
                    try:
                        _stamp_phase(scaler_hostname, "gi_confirmed_at", _log,
                                     gi_state_observed=state)
                    except Exception:
                        pass

                    try:
                        op_file = Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname / "operational.json"
                        from routes._ops_writer import update_ops as _update_ops_gi

                        def _gi_mutator(op_data):
                            op_data["device_state"] = "GI"
                            op_data["recovery_mode_detected"] = False
                            op_data["install_type"] = "gi_deploy"
                            # Lift the pre-delete quarantine -- GI confirmed.
                            # connect_for_upgrade also does this, but we set
                            # it here explicitly because callers who hit
                            # this code path may have written fresh fields
                            # in between.
                            op_data.pop("_delete_pending", None)
                            op_data.pop("_delete_pending_at", None)
                            op_data.pop("_delete_pending_cancelled_at", None)
                            return True

                        _update_ops_gi(op_file, _gi_mutator)
                    except Exception:
                        pass
                    break
                else:
                    _log("INFO", f"Reachable via {method} but state={state}, not GI yet ({elapsed}s)")
                    try:
                        conn["ssh"].close()
                    except Exception:
                        pass
        except Exception:
            _log("INFO", f"Reconnect attempt ({elapsed}s)...")

    stage_times["wait_gi"] = round(time.time() - t_phase, 1)

    if not gi_connected:
        raise RuntimeError(f"Timeout ({gi_mode_timeout}s) waiting for GI mode after system delete")

    # Phase 5a-post: Re-detect active NCC AFTER the reboot. `request
    # system delete` rebooted the previously-active NCC (the one we
    # snapshotted into `pre_delete_active_ncc_vm`) and the cluster
    # almost always fails over to the other NCC. The 2026-05-12 PE-4
    # incident hit this exact case: pre-delete=NCC-1, post-reboot
    # active=NCC-0, but the script kept targeting NCC-1 and got
    # "either you are trying to connect to the standby NCC". The
    # live virsh probe here re-identifies the running NCC VM and
    # updates `deploy_params["ncc_id"]` so every subsequent dncli /
    # deploy command targets the correct half of the cluster.
    try:
        _post_vm, _post_src, _post_id = _probe_libvirt_active_ncc_post_reboot(
            scaler_hostname, _log)
        if _post_vm and _post_id in (0, 1):
            _prev_id = _safe_ncc_id(deploy_params.get("ncc_id"))
            if _prev_id != _post_id:
                _log("WARN",
                     f"Active NCC changed across delete-reboot: "
                     f"pre={pre_delete_active_ncc_vm or 'unknown'} -> "
                     f"post={_post_vm} (ncc_id {_prev_id} -> {_post_id}). "
                     "This is the expected cluster failover during "
                     "request system delete; updating deploy_params.")
                deploy_params["ncc_id"] = _post_id
            try:
                _op_file_post = (Path(SCALER_ROOT) / "db" / "configs"
                                 / scaler_hostname / "operational.json")
                from routes._ops_writer import update_ops as _update_ops_post
                from datetime import datetime as _dt_post
                def _post_mutator(op_data):
                    op_data["active_ncc_vm"] = _post_vm
                    op_data["active_ncc_source"] = _post_src
                    op_data["active_ncc_last_good_at"] = (
                        _dt_post.now().isoformat() + "Z")
                    op_data["deploy_ncc_id"] = str(_post_id)
                    return True
                _update_ops_post(_op_file_post, _post_mutator)
            except Exception:
                pass
    except Exception as _redet_err:
        _log("WARN", f"Post-reboot NCC re-detection skipped: {_redet_err}")

    # Phase 5b: Ensure GI CLI is functional (not just bash shell)
    gi_ssh, gi_chan, recovered_ncc_id, recovered = _preflight_gi_health(
        job_id, device_id, gi_chan, gi_ssh, scaler_hostname, _log)
    if recovered and recovered_ncc_id is not None:
        deploy_params["ncc_id"] = recovered_ncc_id

    # Phase 6: Load images in GI mode
    try:
        _update_device_state(job_id, device_id, phase="load", percent=35,
                             message="Loading images in GI mode...")
        _load_images_on_channel(job_id, device_id, gi_chan, url_list, stage_times, _log,
                                pct_base=35, pct_range=40, ensure_gi_cli=True)

        # Phase 6b: Pre-deploy validation -- verify target-stack has loaded images
        _images_verified = False
        try:
            _ensure_gi_cli_for_command(gi_chan, _log, "pre-deploy stack verification")
            gi_sw = _make_send_wait(gi_chan)
            stack_verify = gi_sw("show system stack | no-more", 4)
            stack_clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', stack_verify)
            _log("INFO", "Pre-deploy stack:\n"
                 f"{_upgrade_terminal_excerpt(stack_clean, ['show system stack | no-more'], limit=500)}")

            loaded_components, missing, _targets = _verify_stack_targets_for_urls(stack_clean, url_list)
            if missing:
                _log("ERROR", f"Images NOT loaded or mismatched in target-stack: {', '.join(sorted(missing))}")
                _update_device_state(job_id, device_id, phase="error", percent=78,
                                     message=f"BLOCKED: selected image mismatch ({', '.join(sorted(missing))}). Cannot deploy.")
                raise RuntimeError(
                    f"Cannot deploy: target-stack target mismatch for {', '.join(sorted(missing))}. "
                    f"Image load may have failed or URLs may be expired. "
                    f"Verify URLs are accessible and retry.")
            else:
                _log("OK", f"All selected images verified in target-stack: {', '.join(sorted(loaded_components))}")
                _images_verified = True
                # Phase marker: every requested image is loaded into the
                # target stack. Resume after this point can skip the
                # whole `_load_images_on_channel` block.
                try:
                    _stamp_phase(scaler_hostname, "images_loaded_at", _log,
                                 upgrade_url_list=[
                                     [c, u] for c, u in (url_list or []) if u
                                 ])
                except Exception:
                    pass
        except RuntimeError:
            raise
        except Exception as sv_err:
            _log("WARN", f"Stack pre-check failed: {sv_err} -- proceeding with caution")

        # Phase 7: Deploy -- socket close after deploy is EXPECTED (device reboots)
        t_phase = time.time()
        sys_type = deploy_params.get("system_type") or ""
        d_name = deploy_params.get("deploy_name") or device_id
        ncc_id = _safe_ncc_id(deploy_params.get("ncc_id"))
        if not sys_type:
            _resolved = _resolve_deploy_system_type(device_id, scaler_hostname, _log)
            if _resolved:
                sys_type = _resolved
        if not sys_type:
            _log("ERROR", "Cannot deploy: system_type unknown. Select it in the upgrade wizard.")
            _update_device_state(job_id, device_id, phase="error", percent=80,
                                 message="FAILED: system_type unknown -- select it in the upgrade wizard",
                                 system_type_unknown=True)
            return
        _check_system_type_change(device_id, scaler_hostname, sys_type, _log)
        _log("INFO", f"Deploy params resolved: system_type={sys_type}, name={d_name}, ncc_id={ncc_id}")
        _update_device_state(job_id, device_id, phase="deploying", percent=80,
                             message=f"Deploying target system ({sys_type})...")
        # Phase marker: stamp BEFORE the deploy command goes out so a
        # crash mid-send leaves an unambiguous "deploy was attempted"
        # signal. Persist enough parameters for the orphan scanner to
        # rebuild the deploy command on its own (no need to walk the
        # in-memory job snapshot, which may be lost on crash).
        try:
            _stamp_phase(
                scaler_hostname, "deploy_sent_at", _log,
                upgrade_deploy_command=(
                    f"request system deploy system-type {sys_type} "
                    f"name {d_name} ncc-id {ncc_id}"
                ),
                upgrade_deploy_system_type=sys_type,
                upgrade_deploy_name=d_name,
                upgrade_deploy_ncc_id=ncc_id,
            )
        except Exception:
            pass
        deploy_out, ncc_id, old_install_task_id = _send_deploy_command(
            gi_chan, sys_type, d_name, ncc_id, _log)
        stage_times["deploy"] = round(time.time() - t_phase, 1)
        _log("OK", f"Deploy request accepted ({stage_times['deploy']}s)")
        if deploy_params is not None:
            deploy_params["old_install_task_id"] = old_install_task_id
            deploy_params["ncc_id"] = ncc_id

        try:
            op_file = Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname / "operational.json"
            from routes._ops_writer import update_ops as _update_ops_dep1
            _deploy_now_ts = time.time()

            def _deploying_mutator(op_data):
                op_data["device_state"] = "DEPLOYING"
                op_data["deploy_initiated"] = _deploy_now_ts
                return True

            _update_ops_dep1(op_file, _deploying_mutator)
        except Exception:
            pass
    finally:
        try:
            if gi_ssh:
                gi_ssh.close()
        except Exception:
            pass

    # Phase 8: Post-deploy verification (with gi-manager recovery if stuck)
    verified = _post_deploy_verify(job_id, device_id, scaler_hostname, stage_times, _log,
                                   url_list=url_list, deploy_params=deploy_params)
    if not verified:
        raise RuntimeError(
            "Post-deploy verification/config repair did not complete. "
            "Device may still be booting or config repair may need retry.")


_LOGIN_PROMPT_RE = re.compile(r'(?:^|[\s\r\n])([a-zA-Z0-9_-]+ )?login:\s*$')
_PASSWORD_PROMPT_RE = re.compile(r'[Pp]assword\s*[:\uff1a]\s*$')
_LOGIN_INCORRECT_RE = re.compile(r'login incorrect', re.IGNORECASE)


def _upgrade_terminal_excerpt(text, sent_cmds=None, limit=300):
    """Return a GUI-safe excerpt from raw device output.

    Device channels echo commands and prompts. Those are useful for debugging
    locally, but the upgrade terminal should show operator-level evidence:
    table rows, progress, and real error messages.
    """
    if not text:
        return ""
    sent_cmds = [c.strip() for c in (sent_cmds or []) if c and c.strip()]
    clean = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', str(text))
    clean = clean.replace('\r', '\n')
    lines = []
    for raw in clean.split('\n'):
        line = raw.strip()
        if not line:
            continue
        lower = line.lower()
        if any(line == cmd or line.startswith(cmd) for cmd in sent_cmds):
            continue
        if "__BASH_PROBE_" in line or "__LOGIN_RECOVERED__" in line:
            continue
        if lower in ("yes", "y"):
            continue
        if _PASSWORD_PROMPT_RE.search(line) or _LOGIN_PROMPT_RE.search(line):
            continue
        if _LOGIN_INCORRECT_RE.search(line) or "maximum number of tries exceeded" in lower:
            continue
        if re.match(r'^[A-Za-z0-9_.:-]+(?:\([^)]*\))?[#>$]\s*$', line):
            continue
        lines.append(line)
    return "\n".join(lines)[:limit]


def _log_upgrade_device_input(_log, line, note=""):
    """Log an operator-visible input only after it was sent to the device."""
    clean = str(line).rstrip("\r\n")
    suffix = f" ({note})" if note else ""
    _log("INFO", f"Device input: {clean}{suffix}")


def _recover_from_login_prompt(chan, _log, max_attempts=2):
    """Re-login to a virsh console that has dropped back to a login prompt.

    The KVM host's `virsh console` occasionally re-issues the linux
    getty login prompt (e.g. after sudo's PAM timeout, after a
    docker-induced hiccup, or if someone else opened a second console to
    the same NCC). When that happens our subsequent commands are not
    run as shell commands -- they're treated as login usernames, which
    is how PE-4's recovery silently no-op'd:

        [INFO] Recovery: Leaving docker swarm
        [INFO] Login incorrect
        [INFO] kvm108-cl408d-ncc0 login:
        [INFO] Recovery: Pruning all docker data
        [INFO] sudo docker system prune -a -f --volumes
        [INFO] Password:

    Nothing on that channel was actually executed; the `sudo docker
    swarm leave` text became a bad username, the next `sudo ...` line
    a bad password, and so on until the reboot "command" also went
    into the void. That left gi-manager stuck forever and caused the
    `Timeout waiting for GI mode after gi-manager recovery` failure.

    This helper probes for the login prompt, logs in as dnroot/dnroot,
    and returns True once the channel is back at a bash shell.
    """
    import time

    def _drain(wait=1.5):
        buf = b""
        deadline = time.time() + wait
        while time.time() < deadline:
            if chan.recv_ready():
                buf += chan.recv(65535)
            time.sleep(0.2)
        return buf.decode("utf-8", errors="replace")

    try:
        chan.send(b"\r")
    except Exception:
        return False
    snapshot = _drain(wait=2)
    clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', snapshot).rstrip()
    if not clean:
        return None
    tail = clean[-200:]
    if not _LOGIN_PROMPT_RE.search(tail):
        return None

    _log("WARN", "Virsh console dropped to login prompt -- re-logging in as dnroot")

    for attempt in range(max_attempts):
        try:
            chan.send(b"dnroot\n")
        except Exception:
            return False
        after_user = _drain(wait=2)
        if _PASSWORD_PROMPT_RE.search(
                re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', after_user).rstrip()[-80:]):
            try:
                chan.send(b"dnroot\n")
            except Exception:
                return False
            after_pw = _drain(wait=3)
            if _LOGIN_INCORRECT_RE.search(after_pw):
                _log("WARN", f"dnroot/dnroot rejected (attempt {attempt + 1}) -- retrying")
                continue

        check_buf = _drain(wait=2)
        try:
            chan.send(b"echo __LOGIN_RECOVERED__\n")
        except Exception:
            return False
        time.sleep(1.2)
        buf = _drain(wait=2)
        if "__LOGIN_RECOVERED__" in buf:
            _log("OK", "Re-logged into virsh console as dnroot")
            while chan.recv_ready():
                try:
                    chan.recv(65535)
                except Exception:
                    break
                time.sleep(0.1)
            return True

    _log("ERROR", "Could not recover virsh console from login prompt after re-login attempts")
    return False


def _send_recovery_cmd(chan, cmd, wait_s, _log, *, sudo_password="dnroot", max_buf_s=45):
    """Send a command during gi-manager recovery, handling login + sudo prompts.

    This is the bug-resistant counterpart to the original inline send
    loop in `_run_gi_manager_recovery`. It:
      1. Re-logs in if the virsh console has dropped to a login prompt
         (see `_recover_from_login_prompt`).
      2. Sends the command and polls for a `Password:` prompt that
         `sudo` issues when PAM's 5-minute grace expired -- previously
         we ignored the prompt entirely and the sudo command never ran.
      3. Reads output until the channel is idle for >=`wait_s` seconds
         (or `max_buf_s` total) instead of a flat sleep, so heavy
         commands like `docker system prune` aren't truncated.

    Returns (decoded_output, ran_ok). `ran_ok` is False if we couldn't
    even get the channel into bash in the first place.
    """
    import time

    login_state = _recover_from_login_prompt(chan, _log)
    if login_state is False:
        return "", False

    try:
        chan.send((cmd + "\n").encode())
    except Exception as e:
        _log("ERROR", f"Failed to send recovery command '{cmd[:40]}': {e}")
        return "", False

    out = b""
    start = time.time()
    last_read_at = time.time()
    sudo_pw_sent = False
    while time.time() - start < max_buf_s:
        made_progress = False
        try:
            while chan.recv_ready():
                chunk = chan.recv(65535)
                if chunk:
                    out += chunk
                    made_progress = True
                    last_read_at = time.time()
                else:
                    break
        except (OSError, EOFError):
            break
        if made_progress:
            decoded = out.decode("utf-8", errors="replace")
            clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', decoded).rstrip()
            tail = clean[-120:]
            if not sudo_pw_sent and _PASSWORD_PROMPT_RE.search(tail):
                _log("INFO", f"sudo password prompt detected -- sending credentials")
                try:
                    chan.send((sudo_password + "\n").encode())
                except Exception:
                    break
                sudo_pw_sent = True
                last_read_at = time.time()
                time.sleep(0.5)
                continue
            if _LOGIN_PROMPT_RE.search(tail):
                _log("WARN", "Virsh console dropped to login mid-command -- recovering")
                if not _recover_from_login_prompt(chan, _log):
                    break
                try:
                    chan.send((cmd + "\n").encode())
                except Exception:
                    break
                last_read_at = time.time()
                continue
            idle = time.time() - last_read_at
            if idle >= wait_s and re.search(r'[#\$>]\s*$', clean):
                break
        else:
            idle = time.time() - last_read_at
            if idle >= wait_s:
                break
            time.sleep(0.25)

    return out.decode("utf-8", errors="replace"), True


def _parse_task_status(output):
    """Parse `show system install | no-more` OR
    `show system target-stack pre-check | no-more`.

    CORRECTED 2026-04-20: `show system install` IS available in GI
    mode -- live output from PE-2 (GI 26.1.1.10, 2026-04-23) confirms
    it returns the same Task ID / Task status / Running tasks /
    Finished tasks structure as in DNOS. The cheetah_docs omission
    (no `show system install.rst` in GI Mode Commands/) is a doc bug.

    The OLD `[INFO] Install status: GI#` forever-loop was caused by a
    combination of two unrelated bugs in the pre-fix code:
      1. A "last non-show-system line" heuristic that grabbed the CLI
         prompt when the install tables were empty.
      2. A row-counter that only matched DNOS-format rows
         (`NCC`/`NCP`/`NCF`/`NCM` prefix), so GI-format rows
         (`Task ID | Status | ...`) were silently under-counted as zero.
    Both are fixed. This parser now handles either command's output
    (same Task ID / Task status / Task elapsed time / Pre-check result
    header fields).

    Returns a dict with:
      status:        'in_progress' | 'completed' | 'failed' | 'idle' | 'unknown'
      task_id:       str (may be '')
      elapsed:       'H:MM:SS' (may be '')
      result:        'passed' | 'failed' | '' (only for pre-check output)
      running_count: int -- rows under "Running tasks:" (install only)
      finished_count: int -- rows under "Finished tasks:" (install only)
      raw_summary:   one-line human-readable tail for logs
    """
    if not output:
        return {"status": "unknown", "task_id": "", "elapsed": "", "result": "",
                "running_count": 0, "finished_count": 0, "raw_summary": ""}
    clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', output)
    lower = clean.lower()

    # "No installation task to show." (DNOS) and an empty pre-check
    # block (GI: only the header + prompt returned when no pre-check
    # has ever run on this device) both mean there is no task visible.
    if "no installation task to show" in lower:
        return {"status": "idle", "task_id": "", "elapsed": "", "result": "",
                "running_count": 0, "finished_count": 0,
                "raw_summary": "no installation task"}

    task_id = ""
    m = re.search(r'Task ID\s*:\s*(\S+)', clean)
    if m:
        task_id = m.group(1).strip()

    elapsed = ""
    m = re.search(r'Task elapsed time\s*:\s*(\S+)', clean)
    if m:
        elapsed = m.group(1).strip()

    status_str = ""
    m = re.search(r'Task status\s*:\s*(\S+)', clean)
    if m:
        status_str = m.group(1).strip().lower()

    result = ""
    m = re.search(r'Pre-check result\s*:\s*(\S+)', clean, re.IGNORECASE)
    if m:
        result = m.group(1).strip().lower()

    # Row counter works for BOTH documented formats:
    #
    # DNOS `show system install` (one column per node):
    #   | Node Type | Node ID | Serial Number | Package Type | ... |
    #   | NCP       | 2       | 234DEE        | DNOS         | ... |
    #
    # GI `show system install` (observed live on PE-2, 2026-04-20):
    #   | Task ID       | Status | Start Time       | Finish Time | ... |
    #   | 1776204261440 | DONE   | 2026-04-23 ...   | ...         | ... |
    #
    # The old detector only matched lines containing "NCC"/"NCP"/etc.,
    # so GI-mode rows were silently undercounted as zero, which was
    # part of why PE-2's output ("Task status: DONE" with empty
    # Running/Finished tables from a *previous* deploy) was
    # mis-classified as "completed" instead of "no new deploy task".
    running_count = 0
    finished_count = 0
    in_running = False
    in_finished = False
    # A table-border separator line such as `|----+----|` or `+----+`.
    _sep_re = re.compile(r'^[|+\-\s]+$')
    # Header-row signatures: first few words of each documented header.
    _hdr_signatures = (
        "|taskid|",         # GI show system install running/finished
        "|nodetype|",       # DNOS show system install running/finished
        "|type|version|",   # Installed Packages header
        "|component|",      # show system stack header
        "|testname|",       # pre-check Tests info header
    )
    for ln in clean.split("\n"):
        ls = ln.strip()
        if not ls:
            continue
        lsl = ls.lower()
        if lsl.startswith("running tasks"):
            in_running, in_finished = True, False
            continue
        if lsl.startswith("finished tasks"):
            in_running, in_finished = False, True
            continue
        if (lsl.startswith("installed packages")
                or lsl.startswith("reverted packages")
                or lsl.startswith("tests info")):
            in_running, in_finished = False, False
            continue
        if "|" not in ls:
            continue
        if _sep_re.match(ls):
            continue
        _packed = re.sub(r'\s+', '', lsl)
        if any(sig in _packed for sig in _hdr_signatures):
            continue
        if not (in_running or in_finished):
            continue
        # Genuine data row under Running/Finished tasks.
        if in_running:
            running_count += 1
        else:
            finished_count += 1

    # Any explicit failure indicator (Task status or Pre-check result)
    # wins over "completed" so we report the right terminal state.
    if "fail" in status_str or result == "failed":
        status = "failed"
    elif "progress" in status_str:
        status = "in_progress"
    elif "complete" in status_str or status_str == "done":
        # Pre-check "DONE" with Passed result means the deploy was
        # accepted and install is proceeding behind the scenes. We keep
        # "completed" here; the caller re-interprets as "still
        # progressing" for pre-check outputs.
        status = "completed"
    elif task_id and running_count > 0:
        status = "in_progress"
    elif task_id and finished_count > 0 and running_count == 0:
        status = "completed"
    elif task_id:
        status = "unknown"
    else:
        return {"status": "unknown", "task_id": "", "elapsed": "", "result": "",
                "running_count": 0, "finished_count": 0, "raw_summary": ""}

    parts = []
    if task_id:
        parts.append(f"task {task_id}")
    parts.append(status.replace("_", "-"))
    if elapsed:
        parts.append(f"elapsed {elapsed}")
    if result:
        parts.append(f"result {result}")
    if running_count:
        parts.append(f"{running_count} running")
    if finished_count:
        parts.append(f"{finished_count} finished")
    summary = ", ".join(parts)

    return {"status": status, "task_id": task_id, "elapsed": elapsed, "result": result,
            "running_count": running_count, "finished_count": finished_count,
            "raw_summary": summary}


# Backwards-compatible alias so any stale callers keep working.
_parse_install_status = _parse_task_status


def _channel_is_closed(chan):
    """Best-effort Paramiko channel closed check."""
    return bool(getattr(chan, "closed", False))


def _probe_ncc_bash(chan, wait=1.5):
    """Return True if the channel is currently an NCC bash shell.

    The probe uses a `printf` format string where the expected output is not
    present literally in the command. GI/DNOS CLIs echo typed commands, so a
    naive `echo TOKEN` probe can return a false positive from command echo.
    """
    import time

    if _channel_is_closed(chan):
        return False
    nonce = str(int(time.time() * 1000000))
    expected = f"__BASH_PROBE_{nonce}_OK__"
    cmd = f"printf '__BASH_PROBE_{nonce}_%s__\\n' OK\n"
    try:
        chan.send(cmd.encode())
    except Exception:
        return False
    deadline = time.time() + wait
    buf = b""
    while time.time() < deadline:
        try:
            if chan.recv_ready():
                buf += chan.recv(65535)
        except Exception:
            return False
        time.sleep(0.2)
    decoded = buf.decode("utf-8", errors="replace")
    return expected in decoded and not _looks_like_kvm_host_shell_output(decoded)


def _ensure_ncc_bash(chan):
    """Navigate to NCC bash shell from whatever CLI state the channel is in.

    Uses echo probe to safely detect bash vs GI/DNOS CLI without risking
    exiting too many shell layers in the virsh console chain
    (KVM SSH -> virsh console -> NCC bash -> gicli/dncli).

    Also runs a hostname fingerprint to distinguish NCC bash (hostname
    ends in -ncc[01]) from the KVM HOST bash (hostname is ``kvm108``
    or similar). The 2026-05-12 PE-4 incident triggered exactly this
    mis-classification: the channel landed at the KVM host shell after
    a virsh console drift, `_probe_ncc_bash` said True (printf
    succeeded), and the next dncli invocation ran on the host instead
    of the NCC -- producing the "Connection failure: either you are
    trying to connect to the standby NCC" message.
    """
    import time

    try:
        # Do not send Ctrl+C here: on KVM virsh sessions it can break out of
        # dncli back to the host shell, while buffered table output still makes
        # the probe look "GI functional". A newline is enough to surface the
        # current prompt before the stack probe.
        chan.send(b"\r")
        time.sleep(0.5)
        while chan.recv_ready():
            chan.recv(65535)
    except Exception:
        return False

    if _probe_ncc_bash(chan):
        ok, hostname = _ncc_bash_fingerprint_via_hostname(chan)
        if ok:
            return True
        # We saw a bash prompt that answered the printf probe but the
        # hostname is NOT *-ncc[01] -- almost certainly the KVM host
        # shell. Fall through to the exit-and-retry path; if the
        # channel is genuinely stuck at the host, the caller will see
        # `_ensure_ncc_bash` return False and abort with a clear
        # "unclassified channel" error instead of issuing dncli on
        # the host.
        if hostname:
            # Best-effort visibility into the host-shell case for ops.
            try:
                import logging
                logging.getLogger(__name__).warning(
                    "_ensure_ncc_bash: printf probe succeeded but "
                    "hostname=%r is NOT an NCC VM. Refusing to claim "
                    "NCC bash. Will attempt one more recovery step.",
                    hostname,
                )
            except Exception:
                pass

    # Before giving up, check if the reason we failed is that the
    # virsh console dropped to a login prompt (see
    # _recover_from_login_prompt for the full root-cause story).
    if _recover_from_login_prompt(chan, lambda *a, **k: None) is True:
        if _probe_ncc_bash(chan):
            ok2, _ = _ncc_bash_fingerprint_via_hostname(chan)
            if ok2:
                return True

    try:
        chan.send(b"exit\n")
        time.sleep(2)
        while chan.recv_ready():
            chan.recv(65535)
    except Exception:
        return False

    if _probe_ncc_bash(chan):
        ok3, _ = _ncc_bash_fingerprint_via_hostname(chan)
        return bool(ok3)
    return False


def _check_gi_manager_health(chan, _log):
    """Check gi-manager Docker service health on an NCC.

    Diagnoses the stuck gi-manager scenario where the NCC booted with
    old GI image and gi-manager service is at 0/0 replicas (Rejected).
    Must be called when channel is at NCC bash shell.
    """
    import time, re

    result = {
        "healthy": False,
        "needs_recovery": False,
        "gi_manager_replicas": "unknown",
        "gi_container_version": None,
        "diagnosis": "",
    }

    svc_text, ran_ok = _send_recovery_cmd(
        chan,
        "sudo docker service ls 2>/dev/null",
        2,
        _log,
        sudo_password="dnroot",
        max_buf_s=15,
    )
    if not ran_ok:
        result["diagnosis"] = "NCC bash unavailable for gi-manager health check"
        _log("WARN", result["diagnosis"])
        return result
    svc_clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', svc_text)
    svc_lower = svc_clean.lower()

    gi_mgr = re.search(r'gi-manager\s+\S+\s+(\d+)/(\d+)', svc_clean)
    if gi_mgr:
        current, desired = int(gi_mgr.group(1)), int(gi_mgr.group(2))
        result["gi_manager_replicas"] = f"{current}/{desired}"
        if current > 0:
            result["healthy"] = True
            result["diagnosis"] = f"gi-manager running ({current}/{desired})"
            _log("INFO", f"gi-manager health: {current}/{desired} -- OK")
            return result
        result["needs_recovery"] = True
        result["diagnosis"] = f"gi-manager stuck at {current}/{desired}"
        _log("WARN", f"gi-manager stuck at {current}/{desired} -- needs recovery")
    elif ("unknown command" in svc_lower or "unknown word" in svc_lower
          or "syntax error" in svc_lower):
        result["diagnosis"] = "not at NCC bash; refusing automatic gi-manager recovery"
        _log("WARN", result["diagnosis"])
        return result
    elif ("cannot connect to the docker daemon" in svc_lower
          or "this node is not a swarm manager" in svc_lower):
        result["needs_recovery"] = True
        result["diagnosis"] = "Docker swarm unavailable"
        _log("WARN", "Docker swarm unavailable -- needs recovery")
    else:
        # Only treat "service not found" as recoverable after proving the
        # Docker command really ran. A prompt echo or GI/DNOS CLI error must
        # never trigger the destructive cleaner.
        docker_listing_seen = bool(
            re.search(r'\bNAME\b.*\bREPLICAS\b', svc_clean, re.I | re.S)
            or re.search(r'\bID\b.*\bNAME\b', svc_clean, re.I | re.S)
        )
        if docker_listing_seen:
            result["needs_recovery"] = True
            result["diagnosis"] = "gi-manager service not found"
            _log("WARN", "gi-manager service not found -- needs recovery")
        else:
            result["diagnosis"] = "could not verify Docker service list; refusing automatic recovery"
            _log("WARN", result["diagnosis"])
            return result

    ps_text, _ = _send_recovery_cmd(
        chan,
        "sudo docker ps --format '{{.Image}}' 2>/dev/null",
        2,
        _log,
        sudo_password="dnroot",
        max_buf_s=10,
    )
    ver_match = re.search(r'gi[_:].*?:(\S+)', ps_text)
    if ver_match:
        result["gi_container_version"] = ver_match.group(1)
        _log("INFO", f"Running GI container version: {ver_match.group(1)}")

    return result


def _run_gi_manager_recovery(job_id, device_id, chan, _log):
    """Run the full Confluence cleaner to recover a stuck gi-manager.

    Steps (from Confluence QA "Deployed SA Instead of Cluster"):
    1. docker swarm leave --force
    2. docker system prune -a -f --volumes
    3. Clear NCC identity files (ncc_id, cluster_id, deploy-plans, node_flavor)
    4. Reboot NCC

    After reboot, gi-manager should start fresh and reach 1/1.
    The SSH connection will be lost. Caller must wait for reconnection.
    """
    import time

    _log("WARN", "Starting gi-manager recovery (full Confluence cleaner)...")
    _update_device_state(job_id, device_id, phase="gi-recovery", percent=45,
                         message="Recovering stuck gi-manager (cleanup + reboot)...")

    cmds = [
        ("sudo docker swarm leave --force", 8, "Leaving docker swarm"),
        ("sudo docker system prune -a -f --volumes", 30, "Pruning all docker data"),
        ("sudo rm -f /etc/drivenets/ncc_id /etc/drivenets/cluster_id "
         "/etc/drivenets/deploy-plans /etc/drivenets/node_flavor", 3,
         "Clearing NCC identity files"),
    ]
    # Before launching the sequence, make absolutely sure we're at
    # bash. If the channel drifted to a login prompt (see
    # _recover_from_login_prompt) the original sequence fired the
    # commands blindly and NOTHING ran -- PE-4's "Login incorrect"
    # cascade, which then timed out in the post-recovery GI wait.
    if not _ensure_ncc_bash(chan):
        _log("ERROR",
             "Recovery aborted: cannot reach NCC bash (channel stuck "
             "in an unknown CLI layer). The NCC will not be cleaned up.")
        raise RuntimeError(
            "gi-manager recovery failed: NCC bash shell unreachable before cleanup commands"
        )

    cleanup_failures = 0
    for cmd, wait_s, desc in cmds:
        _log("INFO", f"Recovery: {desc}")
        out_text, ran_ok = _send_recovery_cmd(chan, cmd, wait_s, _log,
                                              sudo_password="dnroot")
        if not ran_ok:
            cleanup_failures += 1
            _log("WARN", f"Recovery step '{desc}' could not execute (channel unhealthy)")
            continue
        if out_text:
            for line in out_text.strip().split("\n")[:5]:
                line = line.strip()
                if line and not line.startswith("$") and "__LOGIN_RECOVERED__" not in line:
                    cleaned_line = _upgrade_terminal_excerpt(line, [cmd], limit=120)
                    if cleaned_line:
                        _log("INFO", f"  {cleaned_line}")

    if cleanup_failures == len(cmds):
        _log("ERROR",
             "Recovery failed: none of the cleanup commands executed. "
             "Aborting reboot so the NCC is not rebooted from a dirty "
             "state (gi-manager would still be stuck).")
        raise RuntimeError(
            "gi-manager recovery failed: all cleanup commands blocked by console state"
        )

    _log("WARN", "Recovery: rebooting NCC...")
    _update_device_state(job_id, device_id, phase="gi-recovery", percent=48,
                         message="Rebooting NCC after cleanup...")
    # Reboot must also be protected against a login prompt drift --
    # otherwise `sudo reboot` becomes a rejected username and the NCC
    # never reboots, which was the PE-4 symptom.
    _send_recovery_cmd(chan, "sudo reboot", 3, _log, sudo_password="dnroot", max_buf_s=10)
    time.sleep(3)


def _seed_active_ncc_hint(scaler_hostname: str, ncc_id, _log) -> bool:
    """Persist an active-NCC hint so the NEXT connect_for_upgrade reconnect
    targets the chosen NCC half.

    ``connection_strategy._ordered_ncc_vms()`` consumes
    ``pre_upgrade_active_ncc_vm`` FIRST (unconditionally) and ``active_ncc_vm``
    next, so writing both pins the virsh console to the pivoted NCC -- without
    this, ``_reconnect_virsh_from_host_shell`` would just reconnect to the same
    standby NCC the stale hint pointed at (PE-4 2026-06-14). Atomic via
    ``routes._ops_writer.update_ops``. Best-effort; never raises.
    """
    try:
        nid = _safe_ncc_id(ncc_id)
    except Exception:
        return False
    if nid not in (0, 1):
        return False
    try:
        import json as _json
        op_file = (Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname
                   / "operational.json")
        if not op_file.exists():
            return False
        ncc_vms = (_json.loads(op_file.read_text()).get("ncc_vms") or [])
        target_vm = ""
        for vm in ncc_vms:
            _m = re.search(r'ncc(\d+)', (vm or ''))
            if _m and int(_m.group(1)) == nid:
                target_vm = vm
                break
        if not target_vm:
            return False
        from routes._ops_writer import update_ops as _update_ops
        from datetime import datetime as _dt

        def _mut(op):
            op["active_ncc_vm"] = target_vm
            op["pre_upgrade_active_ncc_vm"] = target_vm
            op["active_ncc_source"] = "dncli_standby_pivot"
            op["active_ncc_hint_at"] = _dt.now().isoformat() + "Z"
            return True

        _update_ops(op_file, _mut)
        _log("INFO",
             f"Seeded active-NCC hint -> {target_vm} (ncc_id={nid}) so the "
             "virsh reconnect targets the active NCC.")
        return True
    except Exception as exc:
        _log("WARN", f"Could not seed active-NCC hint (ncc_id={ncc_id}): {exc}")
        return False


def _dncli_pivot_after_standby_error(
        scaler_hostname: str, current_ncc_id, _log
) -> tuple[bool, int | None]:
    """Re-probe libvirt to decide whether to pivot the SSH channel
    after a ``STANDBY_NCC_REDIRECT_REQUIRED`` warning.

    Returns ``(needs_pivot, new_ncc_id)``:

      - ``needs_pivot = True`` and ``new_ncc_id in (0, 1)`` -- the live
        libvirt probe found the active NCC, and it is different from
        ``current_ncc_id``. The caller should close the current
        ``chan`` and open a fresh virsh console against the new VM.
      - ``needs_pivot = False`` and ``new_ncc_id is None`` -- the
        libvirt probe either failed, returned both NCCs as not running,
        or returned the same NCC we already had. No pivot would help;
        the caller should surface a clear error to the user instead of
        looping forever.

    Pure read-only. Never closes channels or touches deploy_params.
    """
    cur_id = -1
    if current_ncc_id is not None:
        try:
            cur_id = _safe_ncc_id(current_ncc_id)
        except Exception:
            cur_id = -1
    # When the caller does not know which NCC the channel is on (the common
    # case -- it just got a "standby NCC" dncli error and never tracked the
    # id), derive it from the NCC that connect_for_upgrade last recorded in
    # operational.json. Without this, cur_id stays -1 and the 2-NCC toggle
    # below cannot compute the other half.
    if cur_id not in (0, 1):
        try:
            import json as _json
            _op = (Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname
                   / "operational.json")
            if _op.exists():
                _d = _json.loads(_op.read_text())
                for _k in ("active_ncc_vm", "pre_upgrade_active_ncc_vm"):
                    _m = re.search(r'ncc(\d+)', (_d.get(_k) or ''))
                    if _m:
                        cur_id = int(_m.group(1))
                        break
        except Exception:
            pass
    toggle_id = (1 - cur_id) if cur_id in (0, 1) else None

    try:
        post_vm, post_src, post_id = _probe_libvirt_active_ncc_post_reboot(
            scaler_hostname, _log)
    except Exception as exc:
        _log("WARN", f"Standby-NCC pivot probe failed: {exc}")
        post_vm, post_src, post_id = "", "", -1

    # Trust the libvirt probe ONLY when it unambiguously names a running
    # active NCC that DIFFERS from the one we are on. When both NCC VMs are
    # running (the GI steady state) the probe just returns running[0] -- it
    # cannot tell active from standby -- so a result equal to cur_id, or a
    # failed probe, is NOT proof of "no pivot". The dncli "standby NCC" error
    # is itself proof that the CURRENT NCC is standby, so on a 2-NCC CL/SA
    # cluster the active half is 1 - cur_id. Toggle to it.
    if post_vm and post_id in (0, 1) and post_id != cur_id:
        _log("INFO",
             f"Standby-NCC pivot: probe says active NCC is {post_vm} "
             f"(ncc_id {cur_id} -> {post_id}, src={post_src}).")
        return True, post_id
    if toggle_id is not None:
        _log("WARN",
             "Standby-NCC pivot: libvirt probe could not disambiguate the "
             f"active NCC (probe={post_vm or 'none'}/{post_id}); dncli "
             f"already proved ncc_id={cur_id} is standby, so toggling to the "
             f"other half of the 2-NCC cluster (ncc_id {cur_id} -> "
             f"{toggle_id}).")
        return True, toggle_id
    _log("WARN",
         "Standby-NCC pivot: current NCC id is unknown and the libvirt "
         "probe failed; cannot decide which NCC is active. Operator action "
         "required (verify NCC VMs are running on the KVM host).")
    return False, None


def _enter_dncli_from_bash(chan, _log, signals: dict | None = None):
    """Enter GI CLI from NCC bash shell via dncli.

    Handles the full dncli flow: SSH password prompt, CLI loading time,
    and Ctrl+C+Enter dance to pop the GI prompt. Mirrors the logic in
    connection_strategy._connect_virsh_console but standalone.

    Returns True if GI CLI prompt is reached, False otherwise.
    Channel is left at GI CLI prompt on success, at bash on failure.

    ``signals`` is an optional caller-supplied dict that, when provided,
    is populated with non-empty keys describing WHY entry failed (or
    succeeded with caveats). The current keys are:

      * ``standby_redirect`` -- True iff dncli reported
        ``either you are trying to connect to the standby NCC`` or
        ``Drivenets CLI is N/A``. Caller can use this signal to drive
        an auto-pivot retry via ``_dncli_pivot_after_standby_error``.
      * ``host_shell`` -- True iff dncli was attempted from the KVM
        host shell (not an NCC VM). Caller should reconnect virsh
        before retrying.

    Keys are written ONLY when the corresponding condition fires --
    callers may rely on ``signals.get("standby_redirect")`` being
    falsy/absent on success.
    """
    import time

    _gi_prompt_re = re.compile(
        r'F?GI[#>]|F?GI\([^)]*\)[#>]|\[F?GI\(|Component',
        re.IGNORECASE
    )

    def _drain(wait=2):
        buf = b""
        deadline = time.time() + wait
        while time.time() < deadline:
            if chan.recv_ready():
                buf += chan.recv(65535)
            time.sleep(0.3)
        return buf.decode("utf-8", errors="replace")

    while chan.recv_ready():
        chan.recv(65535)

    chan.send(b"dncli\n")
    time.sleep(10)
    dncli_out = _drain(wait=8)
    dncli_lower = dncli_out.lower()

    if 'assword' in dncli_lower:
        _log("INFO", "GI CLI authentication prompt detected -- sending credentials")
        chan.send(b"dnroot\n")
        time.sleep(10)
        cli_out = _drain(wait=5)
        dncli_out += cli_out

    chan.send(b"\x03")
    time.sleep(1)
    chan.send(b"\n")
    time.sleep(3)
    dncli_out += _drain(wait=3)

    for _ in range(3):
        clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', dncli_out)
        if _looks_like_kvm_host_shell_output(clean):
            tail = _upgrade_terminal_excerpt(clean[-240:], ["dncli"], limit=120)
            _log("WARN", f"dncli attempted from KVM host shell, not NCC shell"
                         f"{': ' + tail if tail else ''}")
            if isinstance(signals, dict):
                signals["host_shell"] = True
            return False
        # 2026-05-12 PE-4 hardening: surface the "standby NCC" /
        # "Drivenets CLI is N/A" error as a clearly-parseable WARN so
        # the orchestrator (or a human operator) can pivot the channel
        # to the other NCC and retry. The actual pivot happens at the
        # caller level via _dncli_pivot_after_standby_error +
        # reconnect_gi_session; this branch is the detection surface.
        if _looks_like_standby_ncc_error(clean):
            tail = _upgrade_terminal_excerpt(clean[-240:], ["dncli"], limit=180)
            _log("WARN",
                 "STANDBY_NCC_REDIRECT_REQUIRED: dncli reports the "
                 "local NCC is the STANDBY (or Drivenets CLI is N/A). "
                 "The cluster has likely failed over since this "
                 "channel opened. Re-probe libvirt and pivot the SSH "
                 "channel to the OTHER NCC, then retry."
                 f"{': ' + tail if tail else ''}")
            if isinstance(signals, dict):
                signals["standby_redirect"] = True
            return False
        if _gi_prompt_re.search(clean):
            while chan.recv_ready():
                chan.recv(65535)
                time.sleep(0.1)
            return True
        chan.send(b"\x03")
        time.sleep(1)
        chan.send(b"\n")
        time.sleep(3)
        dncli_out += _drain(wait=2)

    clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', dncli_out)
    tail = _upgrade_terminal_excerpt(clean[-240:], ["dncli"], limit=120)
    # Final post-loop standby-NCC detection in case the error arrived
    # in the very last drain cycle (after the retry loop exited).
    if _looks_like_standby_ncc_error(clean):
        _log("WARN",
             "STANDBY_NCC_REDIRECT_REQUIRED: dncli post-loop reports "
             "standby NCC / CLI N/A. Pivot via libvirt and retry."
             f"{': ' + tail if tail else ''}")
        if isinstance(signals, dict):
            signals["standby_redirect"] = True
        return False
    _log("WARN", f"GI CLI did not become ready{': ' + tail if tail else ''}")

    try:
        chan.send(b"\x03")
        time.sleep(0.5)
        probe_buf = ""
        while chan.recv_ready():
            probe_buf += chan.recv(65535).decode("utf-8", errors="replace")
            time.sleep(0.1)
        try:
            chan.send(b"\r")
            time.sleep(0.8)
            while chan.recv_ready():
                probe_buf += chan.recv(65535).decode("utf-8", errors="replace")
                time.sleep(0.1)
        except Exception:
            pass
        if _looks_like_kvm_host_shell_output(probe_buf):
            _log("INFO", "GI CLI entry failed; channel is at KVM host shell")
            return False
        if _probe_ncc_bash(chan, wait=3):
            _log("INFO", "GI CLI entry failed; channel is back at NCC bash")
            return False
        # Only send `exit` if we are not already at bash. On KVM virsh
        # consoles the failed dncli path often lands back at `ncc:~$`; a
        # blind exit there closes the reusable console channel and makes the
        # next gi-manager health check fail with "Socket is closed".
        if not _channel_is_closed(chan):
            chan.send(b"exit\n")
            time.sleep(2)
            while chan.recv_ready():
                chan.recv(65535)
                time.sleep(0.1)
    except Exception:
        pass
    return False


def _preflight_gi_health(job_id, device_id, chan, ssh, scaler_hostname, _log,
                         _reconnect_attempted: bool = False):
    """Pre-flight check before loading images in GI mode.

    Verifies GI CLI is functional by running a test command. If GI CLI
    is broken (gi-manager stuck at 0/0, gicli missing), automatically
    runs the full Confluence cleaner, waits for reboot, and reconnects.

    Returns (ssh, chan, ncc_id, recovered):
      - recovered=False: GI CLI works, original ssh/chan returned unchanged
      - recovered=True: recovery was performed, new ssh/chan/ncc_id returned
    Raises RuntimeError if recovery fails or reconnection times out.
    """
    import time

    def _reconnect_virsh_from_host_shell(reason: str):
        if _reconnect_attempted:
            raise RuntimeError(
                f"{reason}; already reconnected once and still not inside the NCC VM"
            )
        _log("WARN", f"{reason}; reconnecting virsh console before GI CLI work")
        try:
            os.chdir(SCALER_ROOT)
            from scaler.connection_strategy import connect_for_upgrade
            conn = connect_for_upgrade(scaler_hostname, timeout=60)
        except Exception as reconnect_err:
            raise RuntimeError(
                f"Cannot reconnect virsh console for {device_id}: {reconnect_err}"
            ) from reconnect_err
        if not conn.get("connected"):
            raise RuntimeError(
                f"Cannot reconnect virsh console for {device_id}: "
                f"{conn.get('abort_reason') or conn.get('error') or 'unknown'}"
            )
        try:
            ssh.close()
        except Exception:
            pass
        new_state = (conn.get("device_state") or "UNKNOWN").upper()
        new_ncc = conn.get("active_ncc_vm") or conn.get("host") or "?"
        _log("INFO", f"Reconnected virsh console (state={new_state}, ncc={new_ncc})")
        return _preflight_gi_health(
            job_id, device_id, conn.get("channel"), conn.get("ssh"),
            scaler_hostname, _log, _reconnect_attempted=True)

    _gi_cli_ok = False
    _at_bash = False
    try:
        # Do not start preflight with Ctrl+C. On virsh-backed CL consoles that
        # can pop dncli all the way back to the KVM host shell; a stack probe
        # is enough to classify GI CLI vs NCC bash vs outer host shell.
        gi_ok, shell_seen, text = _probe_gi_stack_once(chan, wait=6.0)
        clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        if gi_ok:
            _gi_cli_ok = True
            _log("INFO", "GI CLI functional -- proceeding")
            while chan.recv_ready():
                chan.recv(65535)
                time.sleep(0.1)
        elif _looks_like_kvm_host_shell_output(clean):
            return _reconnect_virsh_from_host_shell(
                "Virsh channel is at KVM host shell, not NCC bash/GI CLI")
        elif shell_seen or "command not found" in clean or re.search(r'(dn|root)@[a-zA-Z0-9_-]+.*\$', clean):
            _at_bash = True
            _log("INFO", "Detected NCC bash shell -- entering GI CLI")
    except Exception:
        pass

    if _gi_cli_ok:
        return ssh, chan, None, False

    if _at_bash:
        _log("INFO", "Channel is at NCC bash -- entering GI CLI directly")
        _dncli_signals: dict = {}
        entered = _enter_dncli_from_bash(chan, _log, signals=_dncli_signals)
        if entered:
            _log("OK", "Entered GI CLI from NCC bash")
            return ssh, chan, None, False
        # 2026-05-12 PE-4 auto-pivot: if dncli reported the local NCC
        # is the STANDBY (or Drivenets CLI is N/A), the cluster has
        # failed over since this channel opened. Re-probe libvirt and,
        # if a different NCC is active, reconnect the virsh console
        # to it. _reconnect_virsh_from_host_shell already enforces the
        # "retry once" guard via _reconnect_attempted, so this auto-
        # pivot will not loop.
        if (_dncli_signals.get("standby_redirect")
                and not _reconnect_attempted):
            try:
                needs_pivot, new_id = _dncli_pivot_after_standby_error(
                    scaler_hostname, None, _log)
            except Exception:
                needs_pivot, new_id = False, None
            if needs_pivot:
                _log("INFO",
                     "Auto-pivoting to active NCC after dncli standby-"
                     f"redirect (target ncc_id={new_id}); reconnecting "
                     "virsh console once then retrying.")
                _seed_active_ncc_hint(scaler_hostname, new_id, _log)
                return _reconnect_virsh_from_host_shell(
                    "dncli reported standby NCC -- pivoting to active "
                    f"NCC (ncc_id={new_id})")
        # 2026-06-14 PE-4: dncli was attempted from the KVM hypervisor host
        # shell (not inside an NCC VM). Re-establish the virsh console into
        # the NCC VM once before giving up on an "unclassified channel".
        if (_dncli_signals.get("host_shell")
                and not _reconnect_attempted):
            return _reconnect_virsh_from_host_shell(
                "dncli ran from the KVM host shell, not inside an NCC VM")
        _log("WARN", "Direct GI CLI entry failed -- checking gi-manager health")
        if _channel_is_closed(chan):
            _log("WARN", "GI CLI entry closed the channel -- reconnecting before health check")
            try:
                os.chdir(SCALER_ROOT)
                from scaler.connection_strategy import connect_for_upgrade
                conn = connect_for_upgrade(scaler_hostname, timeout=30)
                if conn.get("connected"):
                    try:
                        ssh.close()
                    except Exception:
                        pass
                    ssh = conn.get("ssh")
                    chan = conn.get("channel")
                    st = conn.get("device_state", "")
                    _log("INFO", f"Reconnected for GI health check (state={st})")
                    if st in ("GI", "DNOS"):
                        return ssh, chan, conn.get("ncc_id"), False
            except Exception as reconnect_err:
                _log("WARN", f"Reconnect before gi-manager health failed: {reconnect_err}")

    _log("WARN", "GI CLI not responsive -- checking gi-manager health")
    _update_device_state(job_id, device_id, phase="gi-recovery", percent=7,
                         message="GI CLI unavailable -- checking gi-manager...")

    at_bash = _ensure_ncc_bash(chan)
    if not at_bash:
        raise RuntimeError(
            "GI CLI unavailable and NCC bash could not be verified; refusing to send "
            "target-stack commands on an unclassified channel"
        )

    health = _check_gi_manager_health(chan, _log)
    if health.get("healthy"):
        _log("INFO", f"gi-manager healthy ({health.get('diagnosis', '?')}) -- entering GI CLI")
        _gi_signals: dict = {}
        entered = _enter_dncli_from_bash(chan, _log, signals=_gi_signals)
        if entered:
            _log("OK", "Entered GI CLI")
            return ssh, chan, None, False
        # 2026-05-12 PE-4 auto-pivot (second attempt site). Same
        # logic as the bash-direct branch above: if dncli reported
        # standby NCC, pivot the virsh console once instead of
        # waiting 15s and retrying the same dead NCC.
        if (_gi_signals.get("standby_redirect")
                and not _reconnect_attempted):
            try:
                needs_pivot, new_id = _dncli_pivot_after_standby_error(
                    scaler_hostname, None, _log)
            except Exception:
                needs_pivot, new_id = False, None
            if needs_pivot:
                _log("INFO",
                     "Auto-pivoting to active NCC after gi-manager-"
                     "healthy dncli standby-redirect (target "
                     f"ncc_id={new_id}); reconnecting virsh console.")
                _seed_active_ncc_hint(scaler_hostname, new_id, _log)
                return _reconnect_virsh_from_host_shell(
                    "dncli reported standby NCC after gi-manager "
                    f"healthy -- pivoting (ncc_id={new_id})")
        _log("WARN", "GI CLI entry attempt 1 failed -- waiting for gi-manager init, retrying")
        time.sleep(15)
        _ensure_ncc_bash(chan)
        entered = _enter_dncli_from_bash(chan, _log)
        if entered:
            _log("OK", "Entered GI CLI (retry)")
            return ssh, chan, None, False
        _log("ERROR", "Cannot enter GI CLI despite healthy gi-manager")
        raise RuntimeError(
            "GI CLI unreachable: gi-manager is healthy but dncli cannot enter GI CLI. "
            "The NCC may need more time for GI CLI initialization."
        )

    if not health.get("needs_recovery"):
        diagnosis = health.get("diagnosis") or "health unknown"
        raise RuntimeError(
            f"GI CLI unavailable and gi-manager health is unverified ({diagnosis}); "
            "refusing automatic recovery or target-stack load"
        )

    _log("WARN", "gi-manager stuck -- running recovery before upgrade")
    _run_gi_manager_recovery(job_id, device_id, chan, _log)
    try:
        ssh.close()
    except Exception:
        pass

    _update_device_state(job_id, device_id, phase="gi-recovery", percent=15,
                         message="Waiting for NCC to reboot after recovery...")
    time.sleep(90)

    # Post-recovery wait:
    # - Timeout was 600s which is too tight for clusters; the scaler
    #   CLI waits 1200s for DNOS post-deploy and we should match it.
    # - When the NCC comes back reachable in BASEOS_SHELL state we used
    #   to just log "NCC reachable but GI CLI not ready yet" and keep
    #   passively sleeping. If gi-manager has initialised by then, the
    #   GI CLI is one `dncli` away -- we now actively drive the
    #   transition every probe instead of waiting for
    #   connect_for_upgrade's prompt detector to see the GI# prompt
    #   organically. On failure we still return to passive polling.
    gi_wait_timeout = 1200
    gi_wait_start = time.time()
    dncli_attempts = 0
    last_dncli_at = 0.0
    baseos_first_seen = None
    while time.time() - gi_wait_start < gi_wait_timeout:
        _check_upgrade_cancel(job_id)
        elapsed_r = int(time.time() - gi_wait_start)
        _update_device_state(job_id, device_id, phase="gi-recovery",
                             percent=15 + min(elapsed_r // 40, 15),
                             message=f"Waiting for GI CLI after recovery... ({elapsed_r}s)")
        try:
            os.chdir(SCALER_ROOT)
            from scaler.connection_strategy import connect_for_upgrade
            conn = connect_for_upgrade(scaler_hostname, timeout=15)
            if conn["connected"]:
                st = conn.get("device_state", "")
                if st in ("GI", "DNOS"):
                    _log("OK", f"Reconnected in {st} mode after recovery ({elapsed_r}s)")
                    return conn["ssh"], conn["channel"], conn.get("ncc_id"), True
                if st == "BASEOS_SHELL":
                    if baseos_first_seen is None:
                        baseos_first_seen = time.time()
                    baseos_elapsed = int(time.time() - baseos_first_seen)
                    # Give gi-manager ~120s after first NCC reachability
                    # to boot its services before trying dncli. Retry
                    # every 90s thereafter, capped at 4 attempts.
                    cand_ch = conn.get("channel")
                    should_try_dncli = (
                        cand_ch is not None
                        and baseos_elapsed > 120
                        and (time.time() - last_dncli_at) > 90
                        and dncli_attempts < 4
                    )
                    if should_try_dncli:
                        _log("INFO",
                             f"NCC in BASEOS_SHELL for {baseos_elapsed}s "
                             f"-- actively trying dncli to reach GI CLI")
                        last_dncli_at = time.time()
                        dncli_attempts += 1
                        try:
                            entered = _enter_dncli_from_bash(cand_ch, _log)
                        except Exception as de:
                            _log("WARN", f"GI CLI entry attempt {dncli_attempts} errored: {de}")
                            entered = False
                        if entered:
                            _log("OK",
                                 f"Reached GI CLI via dncli after recovery "
                                 f"(attempt {dncli_attempts}, {elapsed_r}s total)")
                            return conn["ssh"], cand_ch, conn.get("ncc_id"), True
                        # dncli didn't take yet -- gi-manager probably
                        # still initialising. Keep waiting.
                        _log("INFO",
                             f"dncli not ready yet (attempt {dncli_attempts}/4) "
                             f"-- will retry in 90s")
                    else:
                        _log("INFO", f"NCC reachable but GI CLI not ready yet ({elapsed_r}s)")
                try:
                    conn["ssh"].close()
                except Exception:
                    pass
        except Exception:
            pass
        time.sleep(30)

    raise RuntimeError(
        f"Timeout waiting for GI mode after gi-manager recovery "
        f"({gi_wait_timeout}s, {dncli_attempts} dncli attempts). "
        f"The NCC rebooted but gi-manager never produced a reachable GI CLI."
    )


def _post_deploy_verify(job_id, device_id, scaler_hostname, stage_times, _log,
                        verify_timeout=1800, check_interval=20,
                        url_list=None, deploy_params=None):
    """After deploy, wait for device to come back in DNOS mode and verify.

    This catches scenarios where deploy was sent but images weren't loaded,
    or the device got stuck in GI. Without this, deploy success is assumed
    just because the command was sent.

    When url_list and deploy_params are provided, enables automatic
    gi-manager recovery: if the device stays stuck in GI for >10min
    with no install progress, checks gi-manager Docker service health
    and runs the full Confluence cleaner (swarm leave, prune, clear
    identity files, reboot) if needed, then reloads images and
    re-deploys automatically.
    """
    import time

    _update_device_state(job_id, device_id, phase="post-deploy-verify", percent=85,
                         message="Waiting for device to come back after deploy...")
    _log("INFO", f"Post-deploy verification (timeout {verify_timeout}s, check every {check_interval}s)")

    t_phase = time.time()
    start = time.time()
    time.sleep(60)

    gi_first_seen_at = None
    gi_recovery_attempted = False
    gi_recovery_deploy_done = False
    GI_STALL_THRESHOLD = 600
    # Once `show system target-stack pre-check` reports Task status:
    # DONE (i.e. the deploy's pre-check completed and install has
    # started running silently behind the GI CLI) we start this timer.
    # If the device has not transitioned to DNOS within
    # POST_INSTALL_GRACE, the install phase finished but the NCC is
    # not handing off -- we surface that explicitly instead of looping
    # forever on "deploy in progress".
    POST_INSTALL_GRACE = 420  # 7 minutes
    _saw_gi_prompt = False
    _last_state_change_at = time.time()
    _prev_conn_state = None
    _install_completed_at = None
    _last_install_summary = None
    _last_install_summary_logged_at = 0.0
    _post_install_warned = False
    # Timestamp (monotonic) of the last "deploy never registered a new
    # install task" warning, so we only log it once every 60s instead
    # of spamming every check_interval. Detection logic (GI mode):
    #   observed Task ID == old_install_task_id (or empty)
    #   Task status == DONE/completed
    #   Running tasks == 0 AND Finished tasks == 0
    #   more than DEPLOY_REGISTER_GRACE seconds elapsed since verify
    #   loop started.
    # Matches the scaler CLI's `old_install_task_id` check (see
    # scaler/interactive_scale.py ~L7503-7705).
    _deploy_unregistered_warned_at = 0.0
    DEPLOY_REGISTER_GRACE = 120  # seconds to wait before flagging non-registration
    _pre_deploy_task_id = (deploy_params or {}).get("old_install_task_id", "") or ""
    # Latch: phase markers are append-once. After the first time we see
    # a real install task running we stamp `install_started_at`; this
    # local prevents repeated stamps every check_interval.
    _install_marker_stamped = False
    _dnos_marker_stamped = False
    _config_repair_started_stamped = False
    _repair_attempts = 0

    # NOTE: We intentionally do NOT set device_state to "DNOS" here.
    # A previous optimization did this to make connect_for_upgrade try SSH
    # first, but if the verify loop times out the stale "DNOS" persists in
    # operational.json and the frontend shows the wrong mode.
    # connect_for_upgrade already falls back to virsh when SSH fails.

    last_status = "rebooting"
    check_count = 0
    while time.time() - start < verify_timeout:
        _check_upgrade_cancel(job_id)
        elapsed = int(time.time() - start)
        elapsed_m = elapsed // 60
        elapsed_s = elapsed % 60
        est_remaining = max(0, 900 - elapsed)
        est_m = est_remaining // 60
        if last_status == "rebooting":
            msg = f"Device rebooting... ({elapsed_m}m {elapsed_s}s, typically 10-15min)"
        elif last_status == "gi":
            msg = f"Deploy in progress... ({elapsed_m}m {elapsed_s}s, ~{est_m}min remaining)"
        else:
            msg = f"Waiting for DNOS... ({elapsed_m}m {elapsed_s}s)"
        _update_device_state(job_id, device_id, phase="post-deploy-verify",
                             percent=85 + min(elapsed // 72, 12), message=msg)
        try:
            os.chdir(SCALER_ROOT)
            from scaler.connection_strategy import connect_for_upgrade
            conn = connect_for_upgrade(scaler_hostname, timeout=20)
            if conn["connected"]:
                state = conn.get("device_state", "")
                method = conn.get("method", "?")
                if state == "DNOS":
                    if last_status != "dnos":
                        _log("OK",
                             f"Device back in DNOS mode (via {method}, "
                             f"{elapsed_m}m {elapsed_s}s after deploy)")
                    last_status = "dnos"
                    # Phase marker: device is back in DNOS. Resumer
                    # uses this to know "skip waiting-for-deploy, jump
                    # straight to config repair".
                    if not _dnos_marker_stamped:
                        try:
                            _stamp_phase(scaler_hostname, "dnos_confirmed_at", _log)
                            _dnos_marker_stamped = True
                        except Exception:
                            pass
                    stage_times["post_deploy_verify"] = round(time.time() - t_phase, 1)
                    config_restored_ok = False
                    config_retryable = False
                    config_error = ""
                    try:
                        chan = conn.get("channel")
                        if chan:
                            remaining = int(verify_timeout - (time.time() - start))
                            if remaining <= 0:
                                try:
                                    conn["ssh"].close()
                                except Exception:
                                    pass
                                break
                            if not _wait_for_dnos_config_ready(
                                job_id, device_id, scaler_hostname, chan, _log,
                                timeout=min(300, max(30, remaining))):
                                try:
                                    conn["ssh"].close()
                                except Exception:
                                    pass
                                check_count += 1
                                time.sleep(check_interval)
                                continue
                            if not _config_repair_started_stamped:
                                try:
                                    _stamp_phase(scaler_hostname, "config_repair_started_at", _log)
                                    _config_repair_started_stamped = True
                                except Exception:
                                    pass
                            _repair_attempts += 1
                            _log("INFO",
                                 f"Config repair attempt {_repair_attempts} "
                                 "(SSH/auth readiness is retryable)")
                            _post_deploy_config_repair(
                                job_id, device_id, scaler_hostname, chan, _log,
                                mgmt_ip_hint=conn.get("ip") or "")
                            # Only stamp `config_repair_completed_at`
                            # when the repair actually succeeded.
                            # `_post_deploy_config_repair` writes
                            # `config_restored=True/False` into the
                            # job's device_state. A `False` here means
                            # the file push commit failed (or the
                            # rollback fallback also failed). Leaving
                            # the marker unset lets the next bridge
                            # restart re-run repair instead of treating
                            # the device as fully recovered.
                            try:
                                with _push_jobs_lock:
                                    _ds = ((_push_jobs.get(job_id) or {})
                                           .get("device_state") or {})
                                    _dev_state = _ds.get(device_id) or {}
                                    config_restored_ok = bool(
                                        _dev_state.get("config_restored"))
                                    config_retryable = bool(
                                        _dev_state.get("config_repair_retryable")
                                        or _dev_state.get("config_repair_pending"))
                                    config_error = (
                                        _dev_state.get("config_repair_error") or "")
                            except Exception:
                                config_restored_ok = False
                                config_retryable = False
                                config_error = ""
                            if config_restored_ok:
                                try:
                                    _stamp_phase(scaler_hostname,
                                                 "config_repair_completed_at",
                                                 _log)
                                except Exception:
                                    pass
                            else:
                                _log("WARN",
                                     "Config repair did not report "
                                     "config_restored=True; leaving "
                                     "config_repair_completed_at unset "
                                     "so the next restart can retry.")
                                if config_retryable:
                                    remaining = int(verify_timeout - (time.time() - start))
                                    _update_device_state(
                                        job_id, device_id,
                                        phase="config-repair-pending",
                                        percent=98,
                                        message=(
                                            "Config repair pending retry "
                                            f"({max(0, remaining)}s budget left)")
                                    )
                                    _log("INFO",
                                         "Config repair remains retryable "
                                         f"({config_error or 'no terminal error'}); "
                                         f"will retry in {check_interval}s while "
                                         "post-deploy verification budget remains.")
                                    try:
                                        conn["ssh"].close()
                                    except Exception:
                                        pass
                                    check_count += 1
                                    time.sleep(check_interval)
                                    continue
                    except Exception as cr_err:
                        _log("WARN", f"Post-deploy config repair skipped: {cr_err}")
                    # `upgrade_completed_at` is the sentinel the orphan
                    # scanner uses to skip "fully done" devices. Only
                    # stamp it when the WHOLE flow succeeded -- if
                    # config repair didn't confirm success we want the
                    # device to remain on the recovery radar.
                    if config_restored_ok:
                        try:
                            _stamp_phase(scaler_hostname,
                                         "upgrade_completed_at", _log)
                        except Exception:
                            pass
                    try:
                        conn["ssh"].close()
                    except Exception:
                        pass
                    return config_restored_ok
                elif state in ("GI", "BASEOS_SHELL"):
                    if gi_first_seen_at is None:
                        gi_first_seen_at = time.time()
                    if state != _prev_conn_state:
                        _last_state_change_at = time.time()
                        _prev_conn_state = state
                    if state == "GI":
                        _saw_gi_prompt = True
                    if last_status != "gi":
                        _log("INFO", f"Device reachable in {state} ({elapsed_m}m) -- deploy in progress")
                    last_status = "gi"
                    ch = conn.get("channel")

                    if (ch and gi_recovery_attempted and not gi_recovery_deploy_done
                            and url_list and deploy_params and state == "GI"):
                        try:
                            _log("INFO", "Post-recovery: reloading images and re-deploying...")
                            _update_device_state(job_id, device_id, phase="gi-recovery-reload",
                                                 percent=55, message="Reloading images after recovery...")
                            _load_images_on_channel(job_id, device_id, ch, url_list,
                                                    stage_times, _log, pct_base=55, pct_range=20,
                                                    ensure_gi_cli=True)
                            sys_type = deploy_params.get("system_type") or ""
                            d_name = deploy_params.get("deploy_name") or device_id
                            ncc_id = _safe_ncc_id(deploy_params.get("ncc_id"))
                            if not sys_type:
                                _resolved = _resolve_deploy_system_type(device_id, scaler_hostname, _log)
                                if _resolved:
                                    sys_type = _resolved
                            if not sys_type:
                                _log("ERROR", "Cannot re-deploy: system_type unknown")
                                _update_device_state(job_id, device_id, phase="error", percent=80,
                                                     message="FAILED: system_type unknown -- select in wizard",
                                                     system_type_unknown=True)
                                break
                            _log("INFO", f"Recovery deploy params: system_type={sys_type}, name={d_name}, ncc_id={ncc_id}")
                            _update_device_state(job_id, device_id, phase="deploying",
                                                 percent=80, message="Re-deploying after recovery...")
                            # Re-deploy must ALSO refresh the
                            # old_install_task_id baseline so the
                            # "deploy never registered" detector works
                            # for the recovered attempt too -- without
                            # this we'd forever compare against the
                            # pre-recovery snapshot.
                            _rd_out, _rd_ncc, _rd_old_task = _send_deploy_command(
                                ch, sys_type, d_name, ncc_id, _log)
                            _log("OK", "Deploy re-sent after gi-manager recovery")
                            if deploy_params is not None:
                                deploy_params["old_install_task_id"] = _rd_old_task
                                deploy_params["ncc_id"] = _rd_ncc
                            # Reset per-attempt probe state so the new
                            # install task isn't compared against
                            # stale summaries/timers from the first run.
                            _install_completed_at = None
                            _last_install_summary = None
                            _last_install_summary_logged_at = 0.0
                            _post_install_warned = False
                            _deploy_unregistered_warned_at = 0.0
                            gi_recovery_deploy_done = True
                            gi_first_seen_at = None
                            _saw_gi_prompt = False
                            start = time.time()
                        except Exception as rde:
                            _log("ERROR", f"Post-recovery deploy failed: {rde}")
                            gi_recovery_deploy_done = True
                    elif gi_recovery_attempted and not gi_recovery_deploy_done and state == "BASEOS_SHELL":
                        _log("INFO", f"NCC reachable but GI CLI not ready ({elapsed_m}m) -- waiting for gi-manager")
                    else:
                        # Probe the real deploy-task state. Based on
                        # live output captured from PE-2 on 2026-04-20,
                        # GI mode DOES support `show system install`
                        # with the same Task ID / Task status / Running
                        # tasks / Finished tasks structure as DNOS.
                        # The cheetah_docs omission was misleading.
                        #
                        # Using `show system install` (vs the earlier
                        # `show system target-stack pre-check` attempt)
                        # lets us compare the observed Task ID against
                        # the pre-deploy baseline captured inside
                        # `_send_deploy_command`. If the Task ID never
                        # changes AND Running/Finished tables stay
                        # empty, the deploy command was accepted by
                        # the CLI but no new install task was ever
                        # registered -- matching PE-2's state
                        # (Task ID 1776204261440, DONE, empty tables).
                        # The scaler CLI already does this check via
                        # `old_install_task_id` (interactive_scale.py).
                        install_running = False
                        install_status = "unknown"
                        install_info = {"status": "unknown", "raw_summary": "", "result": "",
                                         "task_id": "", "running_count": 0, "finished_count": 0}
                        try:
                            if ch and state == "GI":
                                _ensure_gi_cli_for_command(ch, _log, "post-deploy install status")
                                _sw_tmp = _make_send_wait(ch)
                                inst_out = _sw_tmp("show system install | no-more", 6)
                                install_info = _parse_task_status(inst_out)
                                install_status = install_info["status"]
                                result = (install_info.get("result") or "").lower()
                                observed_task_id = install_info.get("task_id", "") or ""
                                running_count = install_info.get("running_count", 0)
                                finished_count = install_info.get("finished_count", 0)
                                task_id_changed = bool(
                                    observed_task_id
                                    and observed_task_id != _pre_deploy_task_id
                                )
                                if install_status == "failed" or result == "failed":
                                    _log("ERROR",
                                         f"Install task FAILED on device: "
                                         f"{install_info['raw_summary']}")
                                    _update_device_state(
                                        job_id, device_id, phase="error", percent=97,
                                        message=f"Install failed: {install_info['raw_summary']}")
                                    try:
                                        conn["ssh"].close()
                                    except Exception:
                                        pass
                                    stage_times["post_deploy_verify"] = round(time.time() - t_phase, 1)
                                    return False
                                if install_status == "in_progress" or running_count > 0:
                                    # A new install task IS registered
                                    # and progressing. Even if the
                                    # Task ID header hasn't rotated
                                    # yet, running_count > 0 proves
                                    # work is happening.
                                    install_running = True
                                    # Phase marker (idempotent but file
                                    # IO isn't free; gate with the local
                                    # `_install_marker_stamped` so we
                                    # only write it once per call).
                                    if not _install_marker_stamped:
                                        try:
                                            _stamp_phase(scaler_hostname, "install_started_at", _log,
                                                         install_task_id=observed_task_id or "")
                                            _install_marker_stamped = True
                                        except Exception:
                                            pass
                                    summary = install_info["raw_summary"]
                                    if summary != _last_install_summary \
                                            or (time.time() - _last_install_summary_logged_at) > 60:
                                        _log("INFO", f"Install in-progress: {summary}")
                                        _last_install_summary = summary
                                        _last_install_summary_logged_at = time.time()
                                    _update_device_state(
                                        job_id, device_id, phase="installing",
                                        percent=85 + min(elapsed // 72, 12),
                                        message=f"Installing... ({summary})")
                                elif install_status == "completed" and task_id_changed:
                                    # A genuinely NEW install task
                                    # finished (Task ID differs from
                                    # pre-deploy baseline). Install is
                                    # done; NCC should flip to DNOS.
                                    install_running = True
                                    if _install_completed_at is None:
                                        _install_completed_at = time.time()
                                        _log("OK",
                                             f"Install completed: {install_info['raw_summary']} "
                                             f"-- waiting for NCC to boot DNOS")
                                    summary = install_info["raw_summary"]
                                    if summary != _last_install_summary \
                                            or (time.time() - _last_install_summary_logged_at) > 120:
                                        _last_install_summary = summary
                                        _last_install_summary_logged_at = time.time()
                                    _update_device_state(
                                        job_id, device_id, phase="installing",
                                        percent=85 + min(elapsed // 72, 12),
                                        message="Install completed -- waiting for DNOS hand-off")
                                elif install_status == "completed" and not task_id_changed:
                                    # SAME Task ID as pre-deploy +
                                    # DONE + empty Running/Finished.
                                    # The deploy command was accepted
                                    # but never created a new install
                                    # task. This is exactly PE-2's
                                    # case: Task ID 1776204261440
                                    # (previous deploy), DONE, nothing
                                    # else.
                                    if (elapsed > DEPLOY_REGISTER_GRACE
                                            and running_count == 0
                                            and finished_count == 0):
                                        if (time.time() - _deploy_unregistered_warned_at) > 60:
                                            _log("ERROR",
                                                 f"Deploy did NOT register a new install task "
                                                 f"(observed Task ID {observed_task_id or 'none'} is the "
                                                 f"pre-deploy baseline, Task status DONE, "
                                                 f"Running=0, Finished=0, {elapsed}s elapsed). "
                                                 f"The device accepted deploy, but no install started -- "
                                                 f"verify all target images are loaded and retry deploy.")
                                            _update_device_state(
                                                job_id, device_id, phase="error", percent=97,
                                                message="Deploy sent but no install task registered "
                                                        "(check target stack). Device still in GI.")
                                            _deploy_unregistered_warned_at = time.time()
                                    # Don't set install_running -- we
                                    # want the stall detector below to
                                    # potentially trigger gi-manager
                                    # recovery.
                                elif install_status == "idle":
                                    # No task recorded at all (fresh
                                    # wipe). Stall detector handles it.
                                    pass
                            elif state == "BASEOS_SHELL":
                                if last_status != "gi":
                                    _log("INFO", f"Device in BASEOS_SHELL ({elapsed_m}m) -- NCC rebooting")
                        except Exception as pe:
                            if check_count % 5 == 0:
                                _log("WARN", f"Deploy-progress probe failed ({pe})")

                        # If the new install finished long ago but the
                        # device still hasn't moved out of GI within
                        # POST_INSTALL_GRACE, the NCC isn't handing
                        # off to DNOS. Surface that explicitly.
                        if (_install_completed_at is not None
                                and state == "GI"
                                and not _post_install_warned):
                            since_complete = time.time() - _install_completed_at
                            if since_complete > POST_INSTALL_GRACE:
                                _log("WARN",
                                     f"Install completed {int(since_complete)}s ago but "
                                     f"device still in GI -- NCC did not hand off to DNOS. "
                                     f"Check cluster health manually. Continuing to wait for DNOS.")
                                _update_device_state(
                                    job_id, device_id, phase="post-deploy-verify",
                                    percent=96,
                                    message=f"Install done {int(since_complete // 60)}m ago "
                                            f"but stuck in GI -- waiting for DNOS hand-off")
                                _post_install_warned = True

                        gi_elapsed = time.time() - gi_first_seen_at if gi_first_seen_at else 0
                        time_in_same_state = time.time() - _last_state_change_at
                        deploy_progressing = install_running or install_status in ("in_progress", "completed")

                        if _saw_gi_prompt or deploy_progressing:
                            pass
                        elif (not gi_recovery_attempted
                                and gi_elapsed > GI_STALL_THRESHOLD
                                and time_in_same_state > GI_STALL_THRESHOLD
                                and not install_running
                                and not deploy_progressing
                                and url_list and deploy_params and ch):
                            _log("WARN", f"Device stuck in {state} for {int(gi_elapsed)}s "
                                 f"(same state {int(time_in_same_state)}s, never saw GI prompt, "
                                 f"no install task) -- checking gi-manager")
                            at_bash = _ensure_ncc_bash(ch)
                            if at_bash:
                                health = _check_gi_manager_health(ch, _log)
                                if health.get("needs_recovery"):
                                    gi_recovery_attempted = True
                                    _run_gi_manager_recovery(job_id, device_id, ch, _log)
                                    gi_first_seen_at = None
                                    _saw_gi_prompt = False
                                    last_status = "rebooting"
                                    start = time.time()
                                    try:
                                        conn["ssh"].close()
                                    except Exception:
                                        pass
                                    time.sleep(60)
                                    check_count += 1
                                    continue
                                else:
                                    _log("INFO", f"gi-manager OK: {health.get('diagnosis', '?')}")
                            else:
                                _log("WARN", "Cannot reach NCC bash for health check")
                elif state == "STANDALONE":
                    if last_status != "standalone":
                        _log("INFO", f"Device in STANDALONE ({elapsed_m}m) -- waiting for full cluster")
                    last_status = "standalone"
                else:
                    last_status = "unknown"
                try:
                    conn["ssh"].close()
                except Exception:
                    pass
            else:
                last_status = "rebooting"
        except Exception:
            last_status = "rebooting"

        check_count += 1
        time.sleep(check_interval)

    stage_times["post_deploy_verify"] = round(time.time() - t_phase, 1)
    _log("WARN", f"Post-deploy verify timed out ({verify_timeout}s) -- device may still be booting.")
    return False


def _restore_candidate_line_count(path: Path) -> int:
    """Return meaningful config line count after stripping prompt/header noise."""
    try:
        text = path.read_text(errors="ignore")
    except Exception:
        return 0
    return _meaningful_config_line_count(text)


def _locate_pre_delete_backup(scaler_hostname):
    """Find the best valid config restore file for a device.

    The GUI upgrade path must not blindly replay the registered
    ``pre_delete_backup``. In the PE-4 incident, that file was partial while
    ``running.txt`` still held the latest full config. Score candidates by
    meaningful config size and prefer a significantly fuller valid cache.

    Candidate priority, before scoring:
      1. running.txt (latest monitor cache, often the freshest full config)
      2. operational.json['pre_delete_backup'] (explicit delete_deploy snapshot)
      3. Newest pre_delete_backup_*.txt / pre_upgrade_backup_*.txt
      4. pre_delete_config.txt

    Returns Path or None.
    """
    device_dir = Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname
    op_file = device_dir / "operational.json"
    candidates = []
    seen = set()

    def _add(path):
        if not path:
            return
        p = Path(path)
        key = str(p)
        if key in seen or not p.exists():
            return
        seen.add(key)
        candidates.append(p)

    _add(device_dir / "running.txt")
    if op_file.exists():
        try:
            _op = _read_ops_safe(op_file)
            registered = (_op.get("pre_delete_backup") or "").strip()
            _add(registered)
        except Exception:
            pass
    ts_candidates = (
        list(device_dir.glob("pre_delete_backup_*.txt"))
        + list(device_dir.glob("pre_upgrade_backup_*.txt"))
    )
    ts_candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for path in ts_candidates:
        _add(path)
    _add(device_dir / "pre_delete_config.txt")

    scored = []
    for priority, path in enumerate(candidates):
        lines = _restore_candidate_line_count(path)
        if lines >= 5:
            scored.append((priority, path, lines))
    if not scored:
        return None

    selected = scored[0]
    for item in scored[1:]:
        # Prefer much fuller configs even if they are lower-priority. This is
        # the safety net for PE-4-style stripped/partial pre-delete snapshots.
        if item[2] > max(selected[2] * 1.20, selected[2] + 100):
            selected = item
    return selected[1]


def _clean_show_config_snapshot(config_text: str) -> str:
    """Remove CLI echo/prompt noise from a captured ``show config`` snapshot."""
    raw_lines = str(config_text or "").splitlines()
    config_start = None
    config_end = None
    for idx, raw_line in enumerate(raw_lines):
        line = raw_line.replace("\r", "")
        if " config-start " in line:
            config_start = idx + 1
            continue
        if config_start is not None and " config-end" in line:
            config_end = idx
            break
    if config_start is not None:
        raw_lines = raw_lines[config_start:config_end]
    else:
        for idx, raw_line in enumerate(raw_lines):
            if raw_line.strip() == "system":
                raw_lines = raw_lines[idx:]
                break

    cleaned_lines = []
    ansi = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
    prompt_or_command = re.compile(
        r"^\s*(?:[A-Za-z0-9_.-]+(?:\([^)]*\))?[#>]\s*)?"
        r"(?:show\s+config(?:uration)?(?:\s+\|\s*no-more)?|show\s+config\s+.*)\s*$",
        re.I,
    )
    prompt_only = re.compile(r"^\s*[A-Za-z0-9_.-]+(?:\([^)]*\))?[#>]\s*$")
    for raw_line in raw_lines:
        line = ansi.sub("", raw_line).replace("\r", "").rstrip()
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue
        lower = stripped.lower()
        if prompt_or_command.match(stripped) or prompt_only.match(stripped):
            continue
        if lower.startswith("--more--") or lower in ("configuration:", "current configuration:"):
            continue
        cleaned_lines.append(line)
    # Trim leading/trailing empty lines so the loader starts at real config.
    while cleaned_lines and not cleaned_lines[0].strip():
        cleaned_lines.pop(0)
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()
    return "\n".join(cleaned_lines) + ("\n" if cleaned_lines else "")


def _meaningful_config_line_count(config_text: str) -> int:
    """Count real DNOS config lines after prompt/header/comment cleanup."""
    cleaned = _clean_show_config_snapshot(config_text)
    return len([
        line for line in cleaned.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ])


_CONFIG_REPAIR_RETRYABLE_MARKERS = (
    "authentication failed",
    "connection timeout",
    "connection refused",
    "connection reset",
    "network error",
    "ssh error",
    "ssh channel closed",
    "channel closed",
    "no existing session",
    "timed out",
    "temporarily unavailable",
)


def _config_repair_message_retryable(message: str) -> bool:
    """Classify post-deploy restore errors that are safe to retry later."""
    lower = str(message or "").lower()
    return any(marker in lower for marker in _CONFIG_REPAIR_RETRYABLE_MARKERS)


def _config_repair_credential_candidates(device_id: str, scaler_hostname: str) -> list:
    """Return deduped credential candidates from saved config and lab profiles.

    The order is intentionally conservative: per-user/device saved credentials
    first, then the established lab credential chain from bridge_helpers. We do
    not invent extra guesses here; every candidate comes from an existing
    configured source or the bridge's documented DNOS fallback.
    """
    candidates = []
    seen = set()

    def _add(source: str, user: str, password: str):
        if not user or not password:
            return
        key = (user, password)
        if key in seen:
            return
        seen.add(key)
        candidates.append((source, user, password))

    try:
        user, password = _get_credentials(
            device_id=device_id, hostname=scaler_hostname)
        _add("saved/default credentials", user, password)
    except Exception:
        pass

    if scaler_hostname and scaler_hostname != device_id:
        try:
            user, password = _get_credentials(
                device_id=scaler_hostname, hostname=scaler_hostname)
            _add("canonical hostname credentials", user, password)
        except Exception:
            pass

    try:
        for profile, user, password in _get_lab_credential_chain(
                device_id=device_id, hostname=scaler_hostname):
            _add(f"lab profile {profile}", user, password)
    except Exception:
        pass

    if not candidates:
        try:
            user, password = _get_credentials()
            _add("fallback credentials", user, password)
        except Exception:
            pass
    return candidates


def _post_deploy_restore_from_file(
    job_id, device_id, scaler_hostname, _log, _term, mgmt_ip_hint: str = ""):
    """File-based config restore for delete+deploy / gi_deploy flows.

    After `request system delete` the device's rollback history is wiped --
    `show config compare rollback 1` will report no drift even though the
    user's entire configuration is gone. The ONLY reliable restore path is
    to replay the config snapshot we took BEFORE the delete.

    Returns:
      ("success", msg)   -- restore completed successfully
      ("retryable", msg) -- SSH/auth/transport is not ready yet
      ("failed", msg)    -- restore attempted and failed terminally
      ("skipped", msg)   -- no backup file or backup looks empty
      ("error", msg)     -- helper setup failed before pushing
    """
    backup_path = _locate_pre_delete_backup(scaler_hostname)
    if backup_path is None:
        return ("skipped", "no pre-delete backup file on disk")
    try:
        config_text = backup_path.read_text()
    except Exception as e:
        return ("error", f"reading {backup_path.name}: {e}")
    config_text = _clean_show_config_snapshot(config_text)
    meaningful_lines = [
        l for l in config_text.splitlines()
        if l.strip() and not l.strip().startswith("#")
    ]
    if len(meaningful_lines) < 5:
        return ("skipped",
                f"backup {backup_path.name} has only "
                f"{len(meaningful_lines)} meaningful lines")

    _update_device_state(job_id, device_id, phase="config-repair", percent=96,
                         message=f"Restoring config from {backup_path.name}...")
    _term(f"[INFO] {device_id}: Restoring from {backup_path.name} "
          f"({len(meaningful_lines)} lines)...")

    mgmt_ip = (mgmt_ip_hint or "").strip()
    if not mgmt_ip:
        mgmt_ip, _sc_id, _ = _resolve_mgmt_ip(device_id, "")
    if not mgmt_ip:
        return ("error", "could not resolve mgmt_ip for ConfigPusher")
    credential_candidates = _config_repair_credential_candidates(
        device_id, scaler_hostname)
    if not credential_candidates:
        return ("error", "no configured credentials available for ConfigPusher")

    class _DevStub:
        def __init__(self, hostname, ip, username, password):
            self.hostname = hostname
            self.ip = ip
            self.username = username
            self._password = password

        def get_password(self):
            return self._password

    try:
        from scaler.config_pusher import ConfigPusher
    except Exception as push_err:
        return ("error", f"ConfigPusher import: {push_err}")

    last_message = ""
    last_retryable = False
    for idx, (source, user, password) in enumerate(credential_candidates, start=1):
        dev = _DevStub(scaler_hostname, mgmt_ip, user, password)
        _log("INFO",
             f"File restore SSH attempt {idx}/{len(credential_candidates)} "
             f"using {source} (user={user}, host={mgmt_ip})")
        pusher = ConfigPusher()

        def _progress(msg, pct):
            try:
                _update_device_state(
                    job_id, device_id, phase="config-repair",
                    percent=96 + min(int(pct) // 33, 3),
                    message=f"Restore: {msg}"[:120])
            except Exception:
                pass
            try:
                _term(f"[INFO] {device_id}: restore {pct}%: {msg}")
            except Exception:
                pass

        try:
            success, message = pusher.push_config(
                dev, config_text,
                config_name=f"post_deploy_restore_{device_id}",
                dry_run=False,
                progress_callback=_progress,
            )
        except Exception as push_err:
            success = False
            message = f"ConfigPusher: {push_err}"

        last_message = message or "failed"
        last_retryable = _config_repair_message_retryable(last_message)
        if success:
            _log("OK",
                 f"File-based config restore succeeded from {backup_path.name}")
            _term(f"[OK] {device_id}: Config restored from {backup_path.name}")
            _update_device_state(job_id, device_id,
                                 config_restored=True,
                                 config_repair_pending=False,
                                 config_repair_retryable=False,
                                 config_repair_source="file",
                                 config_repair_file=str(backup_path),
                                 config_repair_error="")
            return ("success", message or "restored")
        if last_retryable and idx < len(credential_candidates):
            _log("WARN",
                 f"File restore auth/SSH readiness failed with {source}: "
                 f"{last_message}; trying next configured credential source")
            continue
        break

    if last_retryable:
        _log("WARN",
             f"File-based config restore pending retry: {last_message}")
        _term(f"[WARN] {device_id}: File restore pending retry: {last_message}")
        _update_device_state(job_id, device_id,
                             config_restored=False,
                             config_repair_pending=True,
                             config_repair_retryable=True,
                             config_repair_source="file",
                             config_repair_file=str(backup_path),
                             config_repair_error=(last_message or "")[:500])
        return ("retryable", last_message or "retryable restore failure")

    _log("WARN", f"File-based config restore failed: {last_message}")
    _term(f"[WARN] {device_id}: File restore failed: {last_message}")
    _update_device_state(job_id, device_id,
                         config_restored=False,
                         config_repair_pending=False,
                         config_repair_retryable=False,
                         config_repair_source="file",
                         config_repair_file=str(backup_path),
                         config_repair_error=(last_message or "")[:500])
    return ("failed", last_message or "failed")


def _maybe_repair_stripped_config_before_delete(
    job_id,
    device_id,
    scaler_hostname,
    chan,
    live_config,
    _log,
    mgmt_ip_hint: str = "",
):
    """Pick the best config to SAVE as the pre-delete snapshot. TAKE-ONLY.

    Canonical D+D flow: take config (pre-delete) -> delete -> load artifacts
    -> deploy -> device back in DNOS -> restore config. The pre-delete step
    therefore only SELECTS the config to persist as `pre_delete_backup`; the
    actual restore happens post-deploy (in DNOS mode). It must NEVER push a
    config to the live device before delete -- that is wasted work (a full
    commit of a config that `request system delete` is about to wipe) and was
    the root cause of multi-minute pre-delete stalls.

    If the live snapshot is clearly much smaller than the best cached full
    config (stripped/partial snapshot, or the box was reconfigured for an
    unrelated test), return the cached full config so it becomes the
    pre_delete_backup that post-deploy restores. Otherwise keep live.

    ``chan`` / ``mgmt_ip_hint`` are accepted for signature compatibility but
    are intentionally unused now -- no device interaction happens here.
    """
    try:
        live_lines = _meaningful_config_line_count(live_config)
        candidate = _locate_pre_delete_backup(scaler_hostname)
        if not candidate:
            return live_config
        candidate_lines = _restore_candidate_line_count(candidate)
        if candidate_lines < max(500, live_lines * 3, live_lines + 250):
            return live_config

        _log(
            "WARN",
            f"Live config snapshot is much smaller ({live_lines} lines) than "
            f"the cached full backup {candidate.name} ({candidate_lines} lines); "
            "saving the cached full config as the pre-delete snapshot "
            "(TAKE-ONLY -- no live push; restore happens post-deploy in DNOS).",
        )
        _update_device_state(
            job_id,
            device_id,
            phase="snapshot",
            percent=6,
            message=(
                "Live config looks stripped; using latest valid cached "
                "configuration as the pre-delete snapshot..."
            ),
        )
        try:
            cached_text = _clean_show_config_snapshot(candidate.read_text())
        except Exception as read_err:
            _log("WARN",
                 f"Could not read cached backup {candidate.name}: {read_err}; "
                 "keeping live snapshot")
            return live_config
        cached_lines = _meaningful_config_line_count(cached_text)
        _log("OK",
             f"Pre-delete snapshot selected from {candidate.name} "
             f"({cached_lines} lines); restore deferred to post-deploy")
        return cached_text
    except Exception as exc:
        _log("WARN", f"Pre-delete stripped-config check skipped: {exc}")
        return live_config


def _post_deploy_config_repair(
    job_id, device_id, scaler_hostname, chan, _log, mgmt_ip_hint: str = ""):
    """After delete+deploy or gi_deploy, restore saved config and detect failures.

    Flow:
    1. If we have a pre-delete backup FILE on disk -> push it via
       ConfigPusher (the device's rollback history is gone after
       `system delete`, so file-based restore is mandatory for this path).
    2. Otherwise (in-place install / no snapshot) fall back to the legacy
       `show config compare rollback 1` + `rollback 1 / commit` flow, with
       partial-repair analysis for version-incompatible hierarchies.
    """
    import time
    import re

    _update_device_state(job_id, device_id, phase="config-repair", percent=95,
                         message="Checking post-deploy config...")

    _sw = _make_send_wait(chan)
    _ansi = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

    def _term(msg):
        """Append a timestamped per-device terminal line visible in GUI."""
        text = str(msg or "")
        match = re.match(r"^\[([A-Za-z]+)\]\s+(?:(.+?):\s*)?(.*)$", text, re.S)
        if match:
            level = match.group(1)
            dev = match.group(2) or device_id
            body = match.group(3) or ""
            line = _format_upgrade_terminal_line(level, body, dev)
        else:
            line = _format_upgrade_terminal_line("INFO", text, device_id)
        with _push_jobs_lock:
            if job_id in _push_jobs:
                _push_jobs[job_id]["terminal_lines"].append(line)

    file_outcome = ("skipped", "not tried")
    try:
        file_outcome = _post_deploy_restore_from_file(
            job_id, device_id, scaler_hostname, _log, _term,
            mgmt_ip_hint=mgmt_ip_hint)
    except Exception as file_err:
        file_outcome = ("error", f"{file_err}")
        _log("WARN", f"File-based restore raised: {file_err}")

    if file_outcome[0] == "success":
        return True
    if file_outcome[0] == "retryable":
        return False
    if file_outcome[0] == "failed":
        return False

    _log("INFO",
         f"File-based restore not used ({file_outcome[0]}: {file_outcome[1]}); "
         f"falling back to on-device rollback repair")
    _term(f"[INFO] {device_id}: File restore skipped ({file_outcome[1]}); "
          f"trying rollback-based repair")

    try:
        time.sleep(3)
        diff_out = _sw("show config compare rollback 1 | no-more", 5)
        diff_clean = _ansi.sub('', diff_out)
        diff_lines = [l for l in diff_clean.split("\n")
                      if l.strip().startswith("+") or l.strip().startswith("-")]

        if len(diff_lines) == 0:
            _log("OK", "No config drift detected after deploy")
            _term(f"[OK] {device_id}: No config drift -- nothing to restore")
            _update_device_state(
                job_id, device_id, config_restored=True,
                config_repair_pending=False, config_repair_retryable=False)
            return True

        has_deleted = "Deleted:" in diff_clean
        _log("INFO", f"Config drift detected ({len(diff_lines)} lines changed)"
             f"{' -- deleted sections found' if has_deleted else ''}")
        _term(f"[INFO] {device_id}: Config drift: {len(diff_lines)} lines changed")

        if not has_deleted:
            _log("INFO", "Only additions detected, no repair needed")
            _term(f"[OK] {device_id}: Only additions -- no repair needed")
            _update_device_state(
                job_id, device_id, config_restored=True,
                config_repair_pending=False, config_repair_retryable=False)
            return True

        # Attempt full rollback + commit
        _update_device_state(job_id, device_id, phase="config-repair", percent=96,
                             message="Restoring configuration via rollback...")
        _term(f"[INFO] {device_id}: Restoring config via rollback 1...")
        _sw("rollback 1", 3)
        time.sleep(2)

        commit_out = _sw("commit", 15)
        commit_clean = _ansi.sub('', commit_out)
        commit_ok = "succeeded" in commit_clean.lower()

        if commit_ok:
            _log("OK", "Config rollback commit succeeded -- full config restored")
            _term(f"[OK] {device_id}: Config restored successfully via rollback")
            _update_device_state(
                job_id, device_id, config_restored=True,
                config_repair_pending=False, config_repair_retryable=False)
            return True

        # -- Commit FAILED -- extract which hierarchies/commands failed --
        _log("WARN", "Config rollback commit FAILED -- analyzing failures...")
        _term(f"[WARN] {device_id}: Config rollback commit failed -- analyzing which commands are unsupported...")
        _update_device_state(job_id, device_id, phase="config-repair", percent=96,
                             message="Analyzing config repair failures...")

        # Abort the failed commit candidate
        try:
            _sw("abort", 3)
        except Exception:
            pass
        time.sleep(1)

        # Parse error output for specific failure patterns
        failed_hierarchies = _parse_commit_failures(commit_clean)
        _log("INFO", f"Detected {len(failed_hierarchies)} failed config sections")

        # If we got failures, try selective repair: apply config minus failed sections
        repair_result = {
            "full_rollback_failed": True,
            "failed_hierarchies": failed_hierarchies,
            "partial_repair_attempted": False,
            "partial_repair_ok": False,
            "lines_restored": 0,
            "lines_failed": 0,
        }

        if failed_hierarchies:
            _term(f"[WARN] {device_id}: {len(failed_hierarchies)} config sections incompatible with this version:")
            for fh in failed_hierarchies:
                path_str = fh.get("path", "unknown")
                reason = fh.get("reason", "unknown error")
                _term(f"  [X] {path_str} -- {reason}")
            _log("INFO", "Attempting partial config repair (skipping failed sections)...")

            # Try selective rollback: load rollback, remove failed sections, commit
            _update_device_state(job_id, device_id, phase="config-repair", percent=97,
                                 message=f"Partial repair -- skipping {len(failed_hierarchies)} incompatible sections...")
            _term(f"[INFO] {device_id}: Attempting partial repair (skipping failed sections)...")

            partial_ok = _attempt_partial_config_repair(
                chan, _sw, failed_hierarchies, _log, _ansi)
            repair_result["partial_repair_attempted"] = True
            repair_result["partial_repair_ok"] = partial_ok

            if partial_ok:
                _log("OK", "Partial config repair succeeded")
                _term(f"[OK] {device_id}: Partial config restored (some sections skipped -- see list above)")
                _update_device_state(job_id, device_id,
                                     config_restored=True,
                                     config_repair_pending=False,
                                     config_repair_retryable=False,
                                     config_repair_partial=True,
                                     config_repair_failures=failed_hierarchies)
                return True
            else:
                _log("ERROR", "Partial config repair also failed")
                _term(f"[ERROR] {device_id}: Partial config repair also failed -- manual intervention needed")
                _update_device_state(job_id, device_id,
                                     config_restored=False,
                                     config_repair_pending=False,
                                     config_repair_retryable=False,
                                     config_repair_partial=False,
                                     config_repair_failures=failed_hierarchies)
        else:
            _term(f"[ERROR] {device_id}: Config rollback failed (could not parse specific failures)")
            _term(f"[ERROR] {device_id}: Commit output: {commit_clean[:300]}")
            _update_device_state(job_id, device_id,
                                 config_restored=False,
                                 config_repair_pending=False,
                                 config_repair_retryable=False,
                                 config_repair_failures=[{"path": "unknown", "reason": commit_clean[:200]}])

        # Save repair report
        try:
            report_path = Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname / "config_repair_report.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            import json as _json
            from datetime import datetime as _dt
            repair_result["device_id"] = device_id
            repair_result["timestamp"] = _dt.now().isoformat()
            repair_result["commit_output"] = commit_clean[:2000]
            report_path.write_text(_json.dumps(repair_result, indent=2, default=str))
            _log("INFO", f"Repair report saved: {report_path}")
        except Exception:
            pass

    except Exception as e:
        _log("WARN", f"Config repair check failed: {e}")
        _term(f"[ERROR] {device_id}: Config repair exception: {e}")
        retryable = _config_repair_message_retryable(str(e))
        _update_device_state(
            job_id, device_id,
            config_restored=False,
            config_repair_pending=retryable,
            config_repair_retryable=retryable,
            config_repair_error=str(e)[:500])
        return False

    return False


def _parse_commit_failures(commit_output: str) -> list:
    """Parse commit error output to identify which config hierarchies failed.

    DNOS commit errors typically look like:
      ERROR: configuration item 'protocols bgp 123 ...' is not supported
      ERROR: Unknown word 'flowspec-vpn' at ...
      Error: 'some-hierarchy' - invalid value
      Aborted: due to errors in configuration
    """
    failures = []
    seen_paths = set()

    patterns = [
        # "configuration item 'X' is not supported"
        (re.compile(r"configuration\s+item\s+'([^']+)'\s+is\s+not\s+supported", re.I),
         lambda m: {"path": m.group(1), "reason": "Not supported in this version"}),
        # "Unknown word 'X'"
        (re.compile(r"Unknown\s+word\s+'([^']+)'", re.I),
         lambda m: {"path": m.group(1), "reason": f"Unknown keyword '{m.group(1)}' -- syntax changed"}),
        # "invalid value" / "invalid keyword"
        (re.compile(r"['\"]([^'\"]+)['\"]\s*[-:]\s*(invalid\s+(?:value|keyword|argument))", re.I),
         lambda m: {"path": m.group(1), "reason": m.group(2).strip()}),
        # "'X' is not a valid value"
        (re.compile(r"['\"]([^'\"]+)['\"]\s+is\s+not\s+a\s+valid\s+value", re.I),
         lambda m: {"path": m.group(1), "reason": "Not a valid value in this version"}),
        # "Error: ... at line N"
        (re.compile(r"Error:\s*(.+?)(?:\s+at\s+line\s+\d+)?$", re.I | re.MULTILINE),
         lambda m: {"path": m.group(1).strip()[:120], "reason": "Configuration error"}),
        # "command failed" / "operation failed"
        (re.compile(r"(command|operation)\s+failed.*?:\s*(.+)", re.I),
         lambda m: {"path": m.group(2).strip()[:120], "reason": f"{m.group(1)} failed"}),
    ]

    for line in commit_output.split("\n"):
        line = line.strip()
        if not line:
            continue
        for pat, extract in patterns:
            match = pat.search(line)
            if match:
                entry = extract(match)
                path_key = entry["path"].lower()
                if path_key not in seen_paths:
                    seen_paths.add(path_key)
                    # Try to classify what kind of version issue
                    entry["category"] = _classify_config_failure(entry["path"], entry["reason"])
                    failures.append(entry)
                break

    return failures


def _classify_config_failure(path: str, reason: str) -> str:
    """Classify a config failure for user-friendly reporting."""
    pl = path.lower()
    if "flowspec" in pl:
        return "FlowSpec (may need different syntax in target version)"
    if "bgp" in pl:
        return "BGP (neighbor/address-family syntax may have changed)"
    if "interface" in pl or "sub-interface" in pl:
        return "Interface (interface naming may differ)"
    if "vrf" in pl or "network-services" in pl:
        return "VRF/Services (hierarchy restructured)"
    if "policy" in pl or "route-policy" in pl:
        return "Routing Policy (check new vs old policy language)"
    if "isis" in pl or "ospf" in pl or "ldp" in pl or "rsvp" in pl:
        return "IGP/MPLS (protocol config syntax changed)"
    if "system" in pl:
        return "System (system-level config changed)"
    if "unknown" in reason.lower():
        return "Keyword removed or renamed in target version"
    return "General config incompatibility"


def _attempt_partial_config_repair(chan, _sw, failed_hierarchies, _log, _ansi):
    """Attempt to apply rollback config minus the failed hierarchies.

    Strategy:
    1. Load rollback 1 candidate
    2. For each failed hierarchy, delete it from the candidate
    3. Commit the cleaned candidate
    """
    import time

    try:
        _sw("rollback 1", 3)
        time.sleep(2)

        failed_paths = [fh["path"] for fh in failed_hierarchies]
        for fp in failed_paths:
            try:
                _sw(f"delete {fp}", 2)
                time.sleep(0.5)
            except Exception:
                _log("WARN", f"Could not delete '{fp}' from candidate -- skipping")

        time.sleep(1)
        commit_out = _sw("commit", 15)
        commit_clean = _ansi.sub('', commit_out)
        if "succeeded" in commit_clean.lower():
            return True

        _log("WARN", f"Partial commit still failed: {commit_clean[:200]}")
        try:
            _sw("abort", 3)
        except Exception:
            pass
        return False
    except Exception as e:
        _log("ERROR", f"Partial repair exception: {e}")
        try:
            _sw("abort", 3)
        except Exception:
            pass
        return False


def _resolve_deploy_system_type(device_id, scaler_hostname, _log):
    """Multi-source fallback to resolve the correct system_type for deploy.
    Sources: 1) operational.json  2) console_mappings.json  3) None (caller uses default).
    """
    scaler_hostname = scaler_hostname or device_id
    if scaler_hostname:
        # Atomic identity canon: collapse aliases/serial to the single canonical
        # config-device dir so pre-config backups + operational.json are saved
        # under ONE identity (e.g. YOR_PE-1 -> PE-1), never a pseudo-identity dir.
        scaler_hostname = _resolve_config_dir(scaler_hostname) or scaler_hostname

    # Source 1: operational.json
    try:
        cfg_dir = _resolve_config_dir(scaler_hostname)
        op_path = Path(SCALER_ROOT) / "db" / "configs" / cfg_dir / "operational.json"
        if op_path.exists():
            op = _read_ops_safe(op_path)
            st = op.get("system_type") or op.get("deploy_system_type") or ""
            if st:
                _log("INFO", f"Resolved system_type '{st}' from operational.json ({op_path.name})")
                return st
    except Exception as e:
        _log("WARN", f"Failed reading operational.json for system_type: {e}")

    # Source 2: console_mappings.json cluster_ncc_access
    try:
        cm_path = Path(SCALER_ROOT) / "db" / "console_mappings.json"
        if cm_path.exists():
            cm = json.loads(cm_path.read_text())
            ncc_access = cm.get("cluster_ncc_access", {})
            for try_name in [scaler_hostname, device_id]:
                entry = ncc_access.get(try_name, {})
                st = entry.get("system_type", "")
                if st:
                    _log("INFO", f"Resolved system_type '{st}' from console_mappings.json (cluster_ncc_access.{try_name})")
                    return st
    except Exception as e:
        _log("WARN", f"Failed reading console_mappings.json for system_type: {e}")

    # Source 3: devices.json (scaler inventory)
    try:
        dev_json_path = Path(SCALER_ROOT) / "db" / "devices.json"
        if dev_json_path.exists():
            dev_list = json.loads(dev_json_path.read_text())
            for dj in dev_list:
                hn = (dj.get("hostname") or "").lower()
                if hn and (hn == device_id.lower() or hn == scaler_hostname.lower()):
                    st = dj.get("system_type") or dj.get("platform") or ""
                    if st:
                        _log("INFO", f"Resolved system_type '{st}' from devices.json ({hn})")
                        return st
    except Exception as e:
        _log("WARN", f"Failed reading devices.json for system_type: {e}")

    _log("WARN", f"Could not resolve system_type from any source for {device_id}")
    return None


def _check_system_type_change(device_id, scaler_hostname, new_sys_type, _log):
    """Detect and warn if the system_type is changing from what was previously deployed.
    SA<->CL changes are especially dangerous -- NCEs keep persistent config from old type.
    """
    if not new_sys_type:
        return
    scaler_hostname = scaler_hostname or device_id
    if scaler_hostname:
        # Atomic identity canon: collapse aliases/serial to the single canonical
        # config-device dir so pre-config backups + operational.json are saved
        # under ONE identity (e.g. YOR_PE-1 -> PE-1), never a pseudo-identity dir.
        scaler_hostname = _resolve_config_dir(scaler_hostname) or scaler_hostname
    prev_sys_type = ""
    try:
        cfg_dir = _resolve_config_dir(scaler_hostname)
        op_path = Path(SCALER_ROOT) / "db" / "configs" / cfg_dir / "operational.json"
        if op_path.exists():
            op = _read_ops_safe(op_path)
            prev_sys_type = (
                op.get("deploy_system_type")
                or op.get("system_type")
                or ""
            ).strip().upper()
    except Exception:
        pass

    if not prev_sys_type or prev_sys_type == new_sys_type.upper():
        return

    is_category_change = (
        (prev_sys_type.startswith("SA-") and new_sys_type.upper().startswith("CL-"))
        or (prev_sys_type.startswith("CL-") and new_sys_type.upper().startswith("SA-"))
    )

    _log("WARN", f"SYSTEM TYPE CHANGE DETECTED: {prev_sys_type} -> {new_sys_type}")
    if is_category_change:
        _log("WARN",
             f"[CRITICAL] SA<->CL system type change ({prev_sys_type} -> {new_sys_type}). "
             f"After deploy, ALL NCEs (NCPs, NCFs, standby NCC) will have stale "
             f"persistent config from the old type in /golden_data/cm/cluster_type. "
             f"They will NOT join the new cluster until the cleaner script is run on each one. "
             f"Recovery: clean each NCE from its host shell, remove stale cluster identity, "
             f"clean container state, and reboot. "
             f"Source: https://drivenets.atlassian.net/wiki/spaces/QA/pages/5186093236")
    else:
        _log("WARN",
             f"System type changed from {prev_sys_type} to {new_sys_type}. "
             f"If NCPs/NCFs don't join after deploy (stuck disconnected for >15min), "
             f"they may need the cleaner script to clear persistent GI config.")

    try:
        cfg_dir = _resolve_config_dir(scaler_hostname)
        op_path = Path(SCALER_ROOT) / "db" / "configs" / cfg_dir / "operational.json"
        if op_path.exists():
            from routes._ops_writer import update_ops as _uops_chg

            def _mut_chg(d, _prev=prev_sys_type):
                d["previous_system_type"] = _prev
                d["system_type_change_detected"] = True
                d["system_type_change_at"] = time.time()

            _uops_chg(op_path, _mut_chg, create_if_missing=False)
    except Exception:
        pass


def _run_gi_deploy_upgrade(job_id, device_id, url_list, deploy_params,
                            stage_times, _log, scaler_hostname=""):
    """GI deploy: device already in GI mode. Connect via connect_for_upgrade, load, deploy."""
    import time
    from pathlib import Path
    import json

    scaler_hostname = scaler_hostname or device_id
    if scaler_hostname:
        # Atomic identity canon: collapse aliases/serial to the single canonical
        # config-device dir so pre-config backups + operational.json are saved
        # under ONE identity (e.g. YOR_PE-1 -> PE-1), never a pseudo-identity dir.
        scaler_hostname = _resolve_config_dir(scaler_hostname) or scaler_hostname

    t_phase = time.time()
    _update_device_state(job_id, device_id, phase="connecting", percent=5,
                         message="Connecting to device in GI mode...")

    _check_upgrade_cancel(job_id)
    os.chdir(SCALER_ROOT)
    from scaler.connection_strategy import connect_for_upgrade
    conn = connect_for_upgrade(scaler_hostname, timeout=60)

    if not conn["connected"]:
        raise RuntimeError(f"Cannot connect to {device_id}: {conn.get('abort_reason', 'unknown')}")

    ssh = conn["ssh"]
    chan = conn["channel"]
    stage_times["connect"] = round(time.time() - t_phase, 1)
    conn_ncc_vm = conn.get("active_ncc_vm", "")
    conn_ncc_id = conn.get("ncc_id")
    _log("OK", f"Connected via {conn.get('method', 'unknown')} (state={conn.get('device_state', '?')}"
         f"{', ncc=' + conn_ncc_vm if conn_ncc_vm else ''})")

    _check_upgrade_cancel(job_id)
    ssh, chan, recovered_ncc_id, recovered = _preflight_gi_health(
        job_id, device_id, chan, ssh, scaler_hostname, _log)
    if recovered and recovered_ncc_id is not None:
        conn_ncc_id = recovered_ncc_id

    def _reconnect_gi_session(reason: str):
        """Refresh the virsh/GI CLI session after target-stack loads.

        Some KVM consoles drop back to the KVM host shell after a long
        target-stack load. Reconnect before the next component/deploy so
        `request system ...` is always sent to GI, not to `dn@kvm`.
        """
        nonlocal ssh, chan, conn_ncc_id
        try:
            ssh.close()
        except Exception:
            pass
        _log("INFO", f"Reconnecting GI CLI before {reason}...")
        new_conn = connect_for_upgrade(scaler_hostname, timeout=60)
        if not new_conn.get("connected"):
            raise RuntimeError(
                f"Cannot reconnect to {device_id} before {reason}: "
                f"{new_conn.get('abort_reason', 'unknown')}"
            )
        ssh = new_conn["ssh"]
        chan = new_conn["channel"]
        new_state = (new_conn.get("device_state") or "").upper()
        if new_state not in ("GI", "BASEOS_SHELL"):
            raise RuntimeError(
                f"Expected GI/BASEOS_SHELL before {reason}, got {new_state or '?'}"
            )
        new_ncc_id = new_conn.get("ncc_id")
        if new_ncc_id is not None:
            conn_ncc_id = new_ncc_id
        ssh, chan, recovered_ncc_id, recovered = _preflight_gi_health(
            job_id, device_id, chan, ssh, scaler_hostname, _log)
        if recovered and recovered_ncc_id is not None:
            conn_ncc_id = recovered_ncc_id
        return chan

    try:
        _check_upgrade_cancel(job_id)
        _update_device_state(job_id, device_id, phase="load", percent=10,
                             message="Loading images...")
        component_count = max(len(url_list), 1)
        per_component_range = max(1, int(55 / component_count))
        for idx, item in enumerate(url_list):
            if idx > 0:
                _reconnect_gi_session(f"loading {item[0]}")
            component_base = 10 + int(55 * idx / component_count)
            for attempt in range(2):
                try:
                    _load_images_on_channel(
                        job_id, device_id, chan, [item], stage_times, _log,
                        pct_base=component_base, pct_range=per_component_range,
                        ensure_gi_cli=True,
                        reconnect_gi_cli=_reconnect_gi_session)
                    break
                except _GiCliReconnectRequired as reconnect_err:
                    if attempt:
                        raise
                    _log("WARN", f"{reconnect_err}; reconnecting CL NCC console and retrying {item[0]}")
                    _reconnect_gi_session(f"retrying {item[0]} after KVM shell drift")
        _reconnect_gi_session("pre-deploy verification")

        try:
            _ensure_gi_cli_for_command(chan, _log, "pre-deploy stack verification")
            _sw_pre = _make_send_wait(chan)
            sv = _sw_pre("show system stack | no-more", 4)
            sc = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', sv)
            _log("INFO", "Pre-deploy stack:\n"
                 f"{_upgrade_terminal_excerpt(sc, ['show system stack | no-more'], limit=500)}")
            loaded_components, missing, _targets = _verify_stack_targets_for_urls(sc, url_list)
            if missing:
                _log("ERROR", f"Images NOT loaded or mismatched in target-stack: {', '.join(sorted(missing))}")
                _update_device_state(job_id, device_id, phase="error", percent=78,
                                     message=f"BLOCKED: selected image mismatch ({', '.join(sorted(missing))}). Cannot deploy.")
                raise RuntimeError(
                    f"Cannot deploy: target-stack target mismatch for {', '.join(sorted(missing))}. "
                    f"Image load may have failed or URLs may be expired. "
                    f"Verify URLs are accessible and retry.")
            _log("OK", f"All selected images verified in target-stack: {', '.join(sorted(loaded_components))}")
        except RuntimeError:
            raise
        except Exception as sv_err:
            _log("WARN", f"Stack pre-check failed: {sv_err} -- proceeding with caution")

        t_phase = time.time()
        sys_type = deploy_params.get("system_type") or ""
        d_name = deploy_params.get("deploy_name") or device_id
        # Prefer the live `conn_ncc_id` (only populated on the virsh
        # path where we parsed the VM name), otherwise fall through to
        # the already-normalised `deploy_params["ncc_id"]`. Either way
        # the result goes through `_safe_ncc_id` so a future regression
        # anywhere upstream still can't smuggle `None` into the CLI.
        ncc_id = _safe_ncc_id(
            conn_ncc_id if conn_ncc_id is not None else deploy_params.get("ncc_id")
        )

        if not sys_type:
            _log("WARN", f"deploy_params system_type is empty -- attempting fallback resolution")
            _resolved_type = _resolve_deploy_system_type(device_id, scaler_hostname, _log)
            if _resolved_type:
                sys_type = _resolved_type
        if not sys_type:
            _log("ERROR", "Cannot deploy: system_type unknown. Select it in the upgrade wizard.")
            _update_device_state(job_id, device_id, phase="error", percent=80,
                                 message="FAILED: system_type unknown -- select it in the upgrade wizard",
                                 system_type_unknown=True)
            return

        _check_system_type_change(device_id, scaler_hostname, sys_type, _log)

        if conn_ncc_id is not None and deploy_params.get("ncc_id") != conn_ncc_id:
            _log("INFO", f"Using NCC ID {conn_ncc_id} from live connection (was {deploy_params.get('ncc_id', 0)} in config)")
        _update_device_state(job_id, device_id, phase="deploying", percent=80,
                             message=f"Deploying target system ({sys_type})...")

        _log("INFO", f"Deploy params resolved: system_type={sys_type}, name={d_name}, ncc_id={ncc_id}")
        deploy_out, ncc_id, old_install_task_id = _send_deploy_command(
            chan, sys_type, d_name, ncc_id, _log)
        stage_times["deploy"] = round(time.time() - t_phase, 1)
        _log("OK", f"Deploy request accepted ({stage_times['deploy']}s)")
        if deploy_params is not None:
            deploy_params["old_install_task_id"] = old_install_task_id
            deploy_params["ncc_id"] = ncc_id

        try:
            op_file = Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname / "operational.json"
            from routes._ops_writer import update_ops as _update_ops_dep2
            _deploy_now_ts2 = time.time()

            def _deploying_mutator2(op_data):
                op_data["device_state"] = "DEPLOYING"
                op_data["deploy_initiated"] = _deploy_now_ts2
                return True

            _update_ops_dep2(op_file, _deploying_mutator2)
        except Exception:
            pass
    finally:
        try:
            ssh.close()
        except Exception:
            pass

    verified = _post_deploy_verify(job_id, device_id, scaler_hostname, stage_times, _log,
                                   url_list=url_list, deploy_params=deploy_params)
    if not verified:
        raise RuntimeError(
            "Post-deploy verification/config repair did not complete. "
            "Device may still be booting or config repair may need retry.")


def _post_upgrade_config_repair(job_id: str, device_id: str, chan, pre_config: str):
    """Pre-install config drift check: compare current config with pre-snapshot.

    This runs BEFORE install/deploy, so it must NOT set config_restored=True.
    That flag is only set by _post_deploy_config_repair after the device
    returns to DNOS mode post-deploy.
    """
    import time

    with _push_jobs_lock:
        if job_id in _push_jobs:
            _push_jobs[job_id]["terminal_lines"].append(
                f"[INFO] {device_id}: Pre-install config drift check...")

    try:
        time.sleep(5)
        while chan.recv_ready():
            chan.recv(65535)
            time.sleep(0.1)

        chan.send("show config compare rollback 1 | no-more\n")
        time.sleep(3)
        diff_buf = ""
        for _ in range(30):
            if chan.recv_ready():
                diff_buf += chan.recv(65535).decode("utf-8", errors="replace")
            time.sleep(0.5)
            if diff_buf.rstrip().endswith("#"):
                break

        has_deleted = "Deleted:" in diff_buf
        has_added = "Added:" in diff_buf
        diff_lines = [l for l in diff_buf.split("\n")
                      if l.strip().startswith("+") or l.strip().startswith("-")]
        diff_count = len(diff_lines)

        if diff_count == 0:
            with _push_jobs_lock:
                if job_id in _push_jobs:
                    _push_jobs[job_id]["terminal_lines"].append(
                        f"[OK] {device_id}: No config drift detected after image load")
            return

        with _push_jobs_lock:
            if job_id in _push_jobs:
                _push_jobs[job_id]["terminal_lines"].append(
                    f"[WARN] {device_id}: Config drift detected ({diff_count} lines changed)"
                    f"{' -- Deleted sections found' if has_deleted else ''}")

        if has_deleted:
            chan.send("rollback 1\n")
            time.sleep(3)
            out = ""
            while chan.recv_ready():
                out += chan.recv(65535).decode("utf-8", errors="replace")

            chan.send("commit\n")
            time.sleep(5)
            commit_out = ""
            for _ in range(30):
                if chan.recv_ready():
                    commit_out += chan.recv(65535).decode("utf-8", errors="replace")
                time.sleep(0.5)
                if "succeeded" in commit_out.lower() or "failed" in commit_out.lower():
                    break

            repair_ok = "succeeded" in commit_out.lower()
            with _push_jobs_lock:
                if job_id in _push_jobs:
                    _push_jobs[job_id]["terminal_lines"].append(
                        f"[{'OK' if repair_ok else 'ERROR'}] {device_id}: "
                        f"Pre-install config repair {'succeeded' if repair_ok else 'FAILED'}")
        else:
            with _push_jobs_lock:
                if job_id in _push_jobs:
                    _push_jobs[job_id]["terminal_lines"].append(
                        f"[INFO] {device_id}: Only additions detected, no repair needed")

    except Exception as e:
        with _push_jobs_lock:
            if job_id in _push_jobs:
                _push_jobs[job_id]["terminal_lines"].append(
                    f"[ERROR] {device_id}: Config repair failed: {e}")


def _finalize_upgrade_job(job_id: str, device_ids: list):
    """Mark upgrade job as done and persist. Uses device_state for overall status."""
    from datetime import datetime
    with _push_jobs_lock:
        if job_id in _push_jobs:
            if _push_jobs[job_id].get("status") == "cancelled":
                _persist_job_if_done(job_id)
                _remove_active_upgrade(job_id)
                return
            ds = _push_jobs[job_id].get("device_state", {})
            if ds:
                failed = sum(1 for d in device_ids if ds.get(d, {}).get("status") == "failed")
                skipped = sum(1 for d in device_ids if ds.get(d, {}).get("status") == "skipped")
                completed = sum(1 for d in device_ids if ds.get(d, {}).get("status") == "completed")
                all_ok = failed == 0
                msg_parts = []
                if completed:
                    msg_parts.append(f"{completed} completed")
                if failed:
                    msg_parts.append(f"{failed} failed")
                if skipped:
                    msg_parts.append(f"{skipped} skipped")
                _push_jobs[job_id]["message"] = "Upgrade: " + ", ".join(msg_parts)
            else:
                errors = [l for l in _push_jobs[job_id].get("terminal_lines", [])
                          if l.startswith("[ERROR]")]
                all_ok = len(errors) == 0
                _push_jobs[job_id]["message"] = (
                    f"Upgrade complete on {len(device_ids)} device(s)"
                    if all_ok else f"Upgrade finished with {len(errors)} error(s)")
            _push_jobs[job_id]["status"] = "completed" if all_ok else "failed"
            _push_jobs[job_id]["phase"] = "done"
            _push_jobs[job_id]["percent"] = 100
            _push_jobs[job_id]["done"] = True
            _push_jobs[job_id]["success"] = all_ok
            _push_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat() + "Z"
    _persist_job_if_done(job_id)
    _remove_active_upgrade(job_id)
    # Retire the pre-upgrade active-NCC snapshot so post-upgrade
    # wizard opens use live probes / scaler-DB cache again. Idempotent
    # on failure (clear helper is no-op when the file is missing).
    try:
        from routes.bridge_helpers import clear_active_ncc_upgrade_snapshot
        for _did in device_ids:
            try:
                clear_active_ncc_upgrade_snapshot(
                    device_id=_did,
                    hostname=_did,
                )
            except Exception:
                pass
    except Exception:
        pass


@router.get("/api/operations/image-upgrade/build-status/{job_id:path}")
def image_upgrade_build_status(job_id: str, latest: bool = False):
    """Poll build progress for a branch (job_id = branch name). latest=True uses lastBuild (for trigger monitoring)."""
    import urllib.parse
    decoded_id = urllib.parse.unquote(job_id)
    print(f"[BUILD-STATUS] job_id={job_id!r}  decoded={decoded_id!r}  latest={latest}")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")
    try:
        from scaler.jenkins_integration import JenkinsClient
        jenkins = JenkinsClient()
        build = jenkins.get_build_info(decoded_id, latest=latest)
        if not build:
            build = jenkins.get_build_info(job_id, latest=latest)
        if not build:
            print(f"[BUILD-STATUS] No build found for {decoded_id!r} or {job_id!r}")
            return {"branch": job_id, "building": False, "result": None, "build_number": None}
        print(f"[BUILD-STATUS] Found build #{build.build_number} building={build.building}")
        return {
            "branch": job_id,
            "build_number": build.build_number,
            "building": build.building,
            "result": build.result,
            "age_hours": round(build.age_hours, 1),
            "is_sanitizer": getattr(build, "is_sanitizer", False),
            "is_expired": getattr(build, "is_expired", False),
            "duration": getattr(build, "duration", 0),
            "build_params": getattr(build, "build_params", {}),
        }
    except Exception as e:
        print(f"[BUILD-STATUS] ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/operations/image-upgrade/build-log/{job_id:path}")
def image_upgrade_build_log(job_id: str, build_number: int = None):
    """Get Jenkins console log for a build. job_id=branch, build_number=query param (optional, uses latest)."""
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id (branch) is required")
    try:
        from scaler.jenkins_integration import JenkinsClient
        jenkins = JenkinsClient()
        if build_number is None:
            build = jenkins.get_build_info(job_id)
            build_number = build.build_number if build else None
        if not build_number:
            return {"log": "", "error": "No build found"}
        success, log = jenkins.get_console_log(job_id, build_number, tail_lines=500)
        return {"log": log or "", "success": success, "build_number": build_number}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/operations/image-upgrade/device-status")
def image_upgrade_device_status(device_ids: str = "", ssh_hosts: str = "", cached_only: bool = False, request: Request = None):
    """Get install/deploy progress per device.
    Query: device_ids=id1,id2&ssh_hosts=ip1,ip2&cached_only=true
    When cached_only=true, reads from operational.json + stack cache only (no SSH, ~10ms/device).
    When cached_only=false (default), performs parallel SSH for live status.

    Side effect: every live probe that reaches a device also auto-mirrors
    the KVM/NCC console-fallback info from ``operational.json`` into the
    caller's ``~/.topology_users/<user>/devices.json`` so the backup
    path survives operational.json wipes. See ``routes._console_fallback``.
    """
    ids = [x.strip() for x in (device_ids or "").split(",") if x.strip()]
    hosts_raw = (ssh_hosts or "").split(",")
    hosts = {ids[i] if i < len(ids) else "": h.strip() for i, h in enumerate(hosts_raw) if h.strip()}
    if not ids:
        raise HTTPException(status_code=400, detail="device_ids is required")

    app_user = _get_request_user(request) if request else ""

    if cached_only:
        return _device_status_from_cache(ids, hosts)

    try:
        import re
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from routes._live_coalescer import coalescer as _live_coalescer
        cwd = os.getcwd()
        os.chdir(SCALER_ROOT)
        try:
            from scaler.interactive_scale import _check_single_device_status
            strip_markup = re.compile(r"\[/?[^\]]+\]")

            def _check_one(did):
                ssh_host = hosts.get(did, "")
                mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(did, ssh_host)
                _ensure_operational_json(scaler_id or did, mgmt_ip)

                # Route through the unified resolver so the GUI status
                # endpoint, recovery, the orphan scanner, and the
                # in-flight poller all share the same TTL cache and
                # write-through path. The resolver does its own TCP
                # fast-probe, single-flight, persist, and event publish.
                # We pass max_age_s=3 so the wizard's polling stays
                # responsive (matches the prior LiveCoalescer 3s TTL).
                try:
                    from routes._device_mode_resolver import get_device_mode
                    res = get_device_mode(
                        did, scaler_id or did,
                        max_age_s=3.0,
                        scaler_root=SCALER_ROOT,
                    )
                    clean = {
                        "mode": res.get("mode") or "?",
                        "dnos_ver": res.get("dnos_ver") or "-",
                        "gi_ver": res.get("gi_ver") or "-",
                        "baseos_ver": res.get("baseos_ver") or "-",
                        "install_status": res.get("install_status") or "",
                    }
                    if not res.get("reachable"):
                        clean["install_status"] = clean["install_status"] or "TCP unreachable"
                except Exception:
                    clean = {"mode": "?", "dnos_ver": "-", "gi_ver": "-",
                             "baseos_ver": "-", "install_status": "SSH failed"}

                try:
                    if app_user:
                        from routes import _console_fallback as _cf
                        _cf.capture_from_ops(app_user, did, reason="device_status_probe")
                except Exception:
                    pass
                return did, clean

            results = {}
            with ThreadPoolExecutor(max_workers=min(len(ids), 6)) as pool:
                futures = {pool.submit(_check_one, did): did for did in ids}
                for fut in as_completed(futures):
                    did, status = fut.result()
                    results[did] = status
        finally:
            os.chdir(cwd)
        return {"devices": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _device_status_from_cache(ids: list, hosts: dict) -> dict:
    """Read device mode/versions from operational.json and stack cache. No SSH."""
    import re, json
    from pathlib import Path
    results = {}
    for did in ids:
        status = {"mode": "", "dnos_ver": "", "gi_ver": "", "baseos_ver": "", "install_status": "", "_cached": True}
        canonical = _resolve_config_dir(did)
        try_ids = list(dict.fromkeys([canonical, did]))
        for try_id in try_ids:
            ops_path = Path(SCALER_ROOT) / "db" / "configs" / try_id / "operational.json"
            if not ops_path.exists():
                continue
            try:
                ops = _read_ops_safe(ops_path)
                stack_comps = ops.get("stack_components", [])
                for comp in stack_comps:
                    name = (comp.get("name") or comp.get("component") or "").upper()
                    ver = comp.get("current") or comp.get("version") or ""
                    if not ver or ver == "-":
                        continue
                    if "DNOS" in name or name == "SYSTEM":
                        status["dnos_ver"] = ver
                    elif "GI" in name or "GENERIC" in name:
                        status["gi_ver"] = ver
                    elif "BASE" in name:
                        status["baseos_ver"] = ver

                if not status["dnos_ver"]:
                    dv = ops.get("dnos_version", "")
                    if dv:
                        m = re.match(r"(\d+\.\d+\.\d+[\.\d]*)", dv)
                        status["dnos_ver"] = m.group(1) if m else dv
                if not status["gi_ver"]:
                    gv = ops.get("gi_version", "")
                    if gv:
                        m = re.match(r"(\d+\.\d+\.\d+[\.\d]*)", gv)
                        status["gi_ver"] = m.group(1) if m else gv
                if not status["baseos_ver"]:
                    bv = ops.get("baseos_version", "")
                    if bv:
                        m = re.match(r"(\d+[\.\d]*)", bv)
                        status["baseos_ver"] = m.group(1) if m else bv

                if not status["dnos_ver"]:
                    dnos_url = ops.get("dnos_url", "")
                    m = re.search(r"dnos[_-](\d+\.\d+\.\d+\.\d+)", dnos_url)
                    if m:
                        status["dnos_ver"] = m.group(1)
                if not status["gi_ver"]:
                    gi_url = ops.get("gi_url", "")
                    m = re.search(r"gi[_-](\d+\.\d+\.\d+\.\d+)", gi_url)
                    if m:
                        status["gi_ver"] = m.group(1)
                if not status["baseos_ver"]:
                    baseos_url = ops.get("baseos_url", "")
                    m = re.search(r"base[_-]?os[_-](\d+\.\d+)", baseos_url, re.IGNORECASE)
                    if m:
                        status["baseos_ver"] = m.group(1)

                device_state = ops.get("device_state", "")
                if device_state:
                    from scaler.connection_strategy import classify_device_state
                    classified = classify_device_state(device_state)
                    if classified:
                        status["mode"] = classified

                if ops.get("console_recovery_detected") is True:
                    status["mode"] = "RECOVERY"

                # Stale UPGRADING/DEPLOYING in ops with no active job: treat as DNOS if we have DNOS version cached.
                if not status["mode"] and status["dnos_ver"]:
                    if not ops.get("upgrade_in_progress"):
                        status["mode"] = "DNOS"

                # Self-heal leaked upgrade_in_progress flag. A job that died or
                # was cancelled without cleaning up leaves this True forever; we
                # clear it if (a) no active job references the device AND (b)
                # the ops record is obviously stale (old fetched_at or old
                # install_start). Without this, the wizard shows "Upgrading..."
                # / "Target stack..." for days after the real job ended.
                is_upgrading = ops.get("upgrade_in_progress", False)
                if is_upgrading and not _device_has_active_job(try_id, canonical):
                    from datetime import datetime, timedelta, timezone
                    _stale = False
                    fetched_at = ops.get("stack_fetched_at") or ops.get("last_updated") or ""
                    if fetched_at:
                        try:
                            ts = datetime.strptime(fetched_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                            if datetime.now(timezone.utc) - ts > timedelta(minutes=30):
                                _stale = True
                        except Exception:
                            _stale = True
                    else:
                        _stale = True
                    inst_start = ops.get("install_start") or ""
                    if inst_start and not _stale:
                        try:
                            st = datetime.strptime(inst_start, "%Y-%m-%d %H:%M:%S")
                            if datetime.now() - st > timedelta(hours=2):
                                _stale = True
                        except Exception:
                            pass
                    if _stale:
                        ops["upgrade_in_progress"] = False
                        for k in ("install_start", "install_status"):
                            ops.pop(k, None)
                        try:
                            from routes._ops_writer import update_ops as _uo_stale

                            def _stale_mut(d):
                                d["upgrade_in_progress"] = False
                                for k in ("install_start", "install_status"):
                                    d.pop(k, None)
                                return True

                            _uo_stale(ops_path, _stale_mut)
                        except Exception:
                            pass
                        is_upgrading = False

                if status["mode"] or status["dnos_ver"]:
                    break

                if is_upgrading:
                    inst_status = (ops.get("install_status") or "").upper()
                    inst_finish = ops.get("install_finish", "")
                    if inst_status in ("COMPLETED", "FAILED", "ERROR"):
                        status["install_status"] = inst_status.capitalize()
                        ops["upgrade_in_progress"] = False
                        try:
                            from routes._ops_writer import update_ops as _uo_done

                            def _done_mut(d):
                                d["upgrade_in_progress"] = False
                                return True

                            _uo_done(ops_path, _done_mut)
                        except Exception:
                            pass
                    elif inst_finish:
                        from datetime import datetime, timedelta
                        try:
                            fin = datetime.strptime(inst_finish, "%Y-%m-%d %H:%M:%S")
                            if datetime.now() - fin > timedelta(hours=2):
                                status["install_status"] = "Stale"
                                ops["upgrade_in_progress"] = False
                                try:
                                    from routes._ops_writer import update_ops as _uo_stl

                                    def _stl_mut(d):
                                        d["upgrade_in_progress"] = False
                                        return True

                                    _uo_stl(ops_path, _stl_mut)
                                except Exception:
                                    pass
                            else:
                                status["install_status"] = "Upgrading..."
                        except ValueError:
                            status["install_status"] = "Upgrading..."
                    else:
                        status["install_status"] = "Upgrading..."

                break
            except Exception:
                continue

        results[did] = status
    return {"devices": results}


def _ensure_operational_json(hostname: str, mgmt_ip: str):
    """Ensure operational.json exists with mgmt_ip for connect_for_upgrade.

    Uses `_safe_set_mgmt_ip` (from routes.bridge_helpers) so Phase-2
    live probes cannot accidentally re-seed a reaped IP or a KVM host
    address into the device's record. Prior to this guard a
    ``ssh_hosts=<kvm_host_ip>`` query parameter from the frontend
    (cached before the system delete) would overwrite ``mgmt_ip``
    on every wizard refresh -- producing an endless GI<->DNOS flap.
    """
    ops_dir = Path(SCALER_ROOT) / "db" / "configs" / hostname
    ops_dir.mkdir(parents=True, exist_ok=True)
    ops_path = ops_dir / "operational.json"

    from routes._ops_writer import update_ops as _update_ops_e

    def _ensure_mutator(data):
        if mgmt_ip:
            _safe_set_mgmt_ip(data, mgmt_ip, source="_ensure_operational_json")
        return True

    _update_ops_e(ops_path, _ensure_mutator, create_if_missing=True)


def _device_has_active_job(device_id: str, scaler_id: str = "") -> bool:
    """Return True if any upgrade/push job is currently running for this device.

    Checks both the raw `device_id` (canvas label) and the resolved `scaler_id`
    (db/configs directory) to handle any naming divergence between frontend and
    scaler id spaces.
    """
    candidates = {c for c in (device_id, scaler_id) if c}
    if not candidates:
        return False
    try:
        with _push_jobs_lock:
            for job in _push_jobs.values():
                status = (job.get("status") or "").lower()
                if status in ("completed", "failed", "cancelled", "canceled"):
                    continue
                job_devs = set(job.get("devices") or [])
                job_state = job.get("device_state") or {}
                if not job_devs and isinstance(job_state, dict):
                    job_devs = set(job_state.keys())
                if candidates & job_devs:
                    return True
    except Exception:
        pass
    return False


def _persist_live_status_to_ops(device_id: str, scaler_id: str, status: dict) -> None:
    """Persist a freshly-observed live-SSH status into operational.json.

    This is the single source of database consistency for per-device state.
    Called after every Phase 2 live check so subsequent Phase 1 reads never
    return a stale classification. Writes authoritative ``device_state``,
    version fields, ``stack_fetched_at`` and ``last_updated``; clears stale
    ``upgrade_in_progress`` / ``install_start`` when no active job exists.

    `status` is the stripped (non-markup) dict returned by
    ``_check_single_device_status``: ``mode``, ``dnos_ver``, ``gi_ver``,
    ``baseos_ver``, ``install_status``.
    """
    from datetime import datetime, timezone

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    canonical = _resolve_config_dir(device_id) if device_id else (scaler_id or "")
    targets = [c for c in dict.fromkeys([canonical, scaler_id, device_id]) if c]
    if not targets:
        return

    raw_mode = (status.get("mode") or "").strip()
    upper_mode = raw_mode.upper()
    clean_modes = {"GI", "DNOS", "RECOVERY", "BASEOS_SHELL", "ONIE"}
    transient_modes = {"UPGRADING", "DEPLOYING"}
    # "GHOST" covers the connect_for_upgrade identity-guard trip: we
    # reached SSH but landed on a different device. Treat it as an SSH
    # error so we do NOT overwrite the last known good classification
    # with nonsense taken from the wrong host.
    ssh_error_hints = ("AUTH", "STARTING", "REBOOTING", "CONN:", "?", "GHOST")

    is_clean_mode = upper_mode in clean_modes
    is_transient_mode = upper_mode in transient_modes
    is_ssh_error = (not is_clean_mode and not is_transient_mode) and (
        not upper_mode or any(h in upper_mode for h in ssh_error_hints)
    )

    has_active_job = _device_has_active_job(device_id, scaler_id)

    from routes._ops_writer import update_ops as _update_ops

    def _mutate(data):
        # GI->DNOS downgrade guard. When the device is in GI/BASEOS_SHELL
        # (delete/upgrade in progress), any phantom "DNOS" detection from
        # a noisy probe would silently overwrite the legitimate GI state
        # in the DB. Refuse the write unless we ALSO have a corroborating
        # DNOS version string (which only appears once the stack is
        # actually installed). A plain mode==DNOS with dnos_ver "-"/"?"
        # is almost always a prompt-detection false positive; drop it.
        prev_state = (data.get("device_state") or "").upper()
        gi_like = {"GI", "BASEOS_SHELL", "DEPLOYING", "UPGRADING"}
        delete_in_flight = bool(
            data.get("_delete_pending") or data.get("delete_initiated")
        )
        incoming_dnos_ver = status.get("dnos_ver") or ""
        dnos_ver_trustworthy = bool(
            incoming_dnos_ver and incoming_dnos_ver not in ("-", "?", "")
        )
        suspected_phantom_dnos = (
            upper_mode == "DNOS"
            and (prev_state in gi_like or delete_in_flight)
            and not dnos_ver_trustworthy
        )

        if is_clean_mode and not suspected_phantom_dnos:
            data["device_state"] = upper_mode
        elif suspected_phantom_dnos:
            events = data.get("_phantom_dnos_events")
            if not isinstance(events, list):
                events = []
            events.append({
                "at": now_iso,
                "prev_state": prev_state,
                "probe_mode": upper_mode,
                "dnos_ver": incoming_dnos_ver,
                "delete_in_flight": delete_in_flight,
                "source": "_persist_live_status_to_ops",
            })
            data["_phantom_dnos_events"] = events[-10:]
        elif is_transient_mode and not has_active_job:
            if status.get("dnos_ver") and status["dnos_ver"] not in ("-", "?"):
                data["device_state"] = "DNOS"

        if is_clean_mode or is_transient_mode:
            for src_key, dst_key in (
                ("dnos_ver", "dnos_version"),
                ("gi_ver", "gi_version"),
                ("baseos_ver", "baseos_version"),
            ):
                val = status.get(src_key)
                if val and val not in ("-", "?"):
                    data[dst_key] = val
            data["stack_fetched_at"] = now_iso

        if is_ssh_error:
            data["last_ssh_error_at"] = now_iso
        else:
            data["last_updated"] = now_iso

        if not has_active_job:
            if data.get("upgrade_in_progress"):
                data["upgrade_in_progress"] = False
            for stale_key in ("install_start", "install_status"):
                if stale_key in data and upper_mode in ("GI", "DNOS"):
                    data.pop(stale_key, None)

    for target in targets:
        ops_path = Path(SCALER_ROOT) / "db" / "configs" / target / "operational.json"
        if not ops_path.exists():
            continue
        # Atomic + per-file-locked write so concurrent probes never
        # leave a truncated/corrupted operational.json on disk.
        try:
            _update_ops(ops_path, _mutate)
        except Exception:
            pass


@router.post("/api/operations/diagnose-recovery")
def diagnose_recovery(body: dict = None):
    """Run recovery diagnostic on device(s). Body: { device_ids: [...] }.
    Performs basic SSH connect and captures prompt/output."""
    body = body or {}
    ids = body.get("device_ids") or []
    if not ids:
        raise HTTPException(status_code=400, detail="device_ids required")
    output_lines = []
    for did in ids[:5]:
        try:
            mgmt_ip, _, _ = _resolve_mgmt_ip(did, "")
            user, password = _get_credentials()
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(mgmt_ip, username=user or "dnroot", password=password, timeout=10,
                        allow_agent=False, look_for_keys=False)
            channel = ssh.invoke_shell()
            channel.settimeout(5)
            import time
            time.sleep(0.8)
            out = channel.recv(8000).decode(errors="ignore")
            ssh.close()
            is_recovery = "RECOVERY" in out or "dnRouter(RECOVERY)" in out
            output_lines.append(f"{did}: {'RECOVERY confirmed' if is_recovery else 'Not in RECOVERY'}\n{out[:500]}")
        except Exception as e:
            output_lines.append(f"{did}: ERROR - {str(e)}")
    return {"output": "\n\n".join(output_lines), "devices": ids}


@router.post("/api/operations/image-upgrade/from-urls")
def image_upgrade_from_urls(body: dict, request: Request = None):
    """Upgrade from pasted Minio URLs. Same as image_upgrade_execute with dnos_url, gi_url, baseos_url.

    Forwards `request` so the underlying job is stamped with the caller's
    identity (Wave 1 owner tracking).
    """
    return image_upgrade_execute(body, request)


@router.post("/api/operations/image-upgrade/wait-and-upgrade")
def image_upgrade_wait_and_upgrade(body: dict, request: Request = None):
    """Monitor a running build in the backend, then auto-start upgrade when it finishes.

    Creates a single job that covers both phases:
      Phase 1: Poll Jenkins for build completion (progress 0-50%)
      Phase 2: Resolve URLs + run upgrade on devices (progress 50-100%)
    The frontend opens showProgress immediately and sees the whole lifecycle.
    """
    import uuid
    import threading
    from datetime import datetime

    owner = _get_request_user(request) if request else "default"

    branch = body.get("branch", "").strip()
    build_number = body.get("build_number")
    device_ids = body.get("device_ids", [])
    ssh_hosts = body.get("ssh_hosts", {}) or {}
    device_plans = body.get("device_plans", {}) or {}
    components = body.get("components", ["DNOS", "GI", "BaseOS"])
    max_concurrent = max(1, min(int(body.get("max_concurrent", 3)), 10))

    if not branch:
        raise HTTPException(status_code=400, detail="branch is required")
    if not device_ids:
        raise HTTPException(status_code=400, detail="device_ids is required")

    existing_id, existing_job = _find_existing_branch_job(
        branch, job_types=("wait_and_upgrade",))
    if existing_id:
        with _push_jobs_lock:
            if existing_id in _push_jobs:
                _push_jobs[existing_id]["terminal_lines"].append(
                    f"[INFO] Duplicate Wait & Upgrade request -- reusing this job")
        return {"success": True, "job_id": existing_id, "reused": True}

    job_id = f"wau-{str(uuid.uuid4())[:8]}"
    from urllib.parse import unquote
    display_branch = branch
    for _ in range(5):
        decoded = unquote(display_branch)
        if decoded == display_branch:
            break
        display_branch = decoded

    device_state = {}
    for did in device_ids:
        plan = device_plans.get(did, {})
        up_type = plan.get("upgrade_type", "normal")
        comps = plan.get("components", components)
        if up_type in ("blocked", "skip"):
            device_state[did] = {
                "status": "skipped",
                "phase": "blocked" if up_type == "blocked" else "at_target",
                "percent": 100 if up_type == "skip" else 0,
                "message": plan.get("reason", "Skipped"),
                "upgrade_type": up_type, "components": comps,
                "error": plan.get("reason") if up_type == "blocked" else None,
                "started_at": datetime.utcnow().isoformat() + "Z",
                "completed_at": datetime.utcnow().isoformat() + "Z",
            }
        else:
            device_state[did] = {
                "status": "pending", "phase": "waiting_for_build", "percent": 0,
                "message": f"Waiting for build #{build_number}...",
                "upgrade_type": up_type, "components": comps,
                "error": None, "started_at": None, "completed_at": None,
            }

    build_label = f"#{build_number}" if build_number else "latest"
    with _push_jobs_lock:
        _push_jobs[job_id] = {
            "job_id": job_id,
            "job_type": "wait_and_upgrade",
            "owner": owner,
            "status": "running",
            "phase": "waiting_for_build",
            "message": f"Waiting for build {build_label} ({display_branch})",
            "percent": 5,
            "success": False,
            "done": False,
            "terminal_lines": [
                f"[INFO] Wait & Upgrade started -- monitoring build {build_label} on {display_branch}",
                f"[INFO] {len(device_ids)} device(s) queued for upgrade after build completes",
            ],
            "job_name": f"Wait & Upgrade {display_branch} {build_label}",
            "device_id": device_ids[0] if len(device_ids) == 1 else "",
            "devices": device_ids,
            "device_state": device_state,
            "max_concurrent": max_concurrent,
            "started_at": datetime.utcnow().isoformat() + "Z",
            "branch": branch,
            "build_number": build_number,
            "components": components,
            "ssh_hosts": ssh_hosts,
            "device_plans": device_plans,
        }

    def _wait_then_upgrade():
        import time
        poll_interval = 30
        max_wait = 7200
        started = time.time()

        try:
            from scaler.jenkins_integration import JenkinsClient, validate_artifact_url
            jenkins = JenkinsClient()

            while time.time() - started < max_wait:
                try:
                    build = jenkins.get_build_info(branch, latest=True)
                    if not build:
                        time.sleep(poll_interval)
                        continue

                    elapsed_min = int((time.time() - started) / 60)
                    if build.building:
                        pct = min(5 + int(elapsed_min * 1.0), 45)
                        with _push_jobs_lock:
                            if job_id in _push_jobs:
                                _push_jobs[job_id]["phase"] = "building"
                                _push_jobs[job_id]["message"] = (
                                    f"Build #{build.build_number} running ({elapsed_min}m)")
                                _push_jobs[job_id]["percent"] = pct
                                _push_jobs[job_id]["build_number"] = build.build_number
                    else:
                        build_ok = build.result == "SUCCESS"
                        with _push_jobs_lock:
                            if job_id in _push_jobs:
                                _push_jobs[job_id]["build_number"] = build.build_number
                                _push_jobs[job_id]["terminal_lines"].append(
                                    f"[{'OK' if build_ok else 'FAIL'}] Build #{build.build_number}"
                                    f" finished: {build.result}")

                        if not build_ok:
                            with _push_jobs_lock:
                                if job_id in _push_jobs:
                                    _push_jobs[job_id]["status"] = "failed"
                                    _push_jobs[job_id]["phase"] = "build_failed"
                                    _push_jobs[job_id]["message"] = (
                                        f"Build #{build.build_number} failed: {build.result}")
                                    _push_jobs[job_id]["done"] = True
                                    _push_jobs[job_id]["percent"] = 100
                            _persist_job_if_done(job_id)
                            return

                        with _push_jobs_lock:
                            if job_id in _push_jobs:
                                _push_jobs[job_id]["phase"] = "resolving_urls"
                                _push_jobs[job_id]["message"] = "Build succeeded -- resolving image URLs"
                                _push_jobs[job_id]["percent"] = 48
                                _push_jobs[job_id]["terminal_lines"].append(
                                    "[INFO] Resolving image URLs...")

                        urls = {}
                        try:
                            stack_urls = jenkins.get_stack_urls(branch, build.build_number)
                            for comp in ["dnos", "gi", "baseos"]:
                                url = stack_urls.get(comp)
                                if url:
                                    ok, msg = validate_artifact_url(url, timeout=10)
                                    urls[comp] = {"url": url, "valid": ok, "detail": msg}
                        except Exception as e:
                            with _push_jobs_lock:
                                if job_id in _push_jobs:
                                    _push_jobs[job_id]["terminal_lines"].append(
                                        f"[WARN] URL resolution issue: {e}")

                        valid_urls = {k: v for k, v in urls.items() if v.get("valid")}
                        url_summary = ", ".join(f"{k.upper()}" for k in valid_urls)

                        with _push_jobs_lock:
                            if job_id in _push_jobs:
                                _push_jobs[job_id]["image_urls"] = urls
                                _push_jobs[job_id]["terminal_lines"].append(
                                    f"[INFO] Valid images: {url_summary or 'none'}")

                        if not valid_urls:
                            with _push_jobs_lock:
                                if job_id in _push_jobs:
                                    _push_jobs[job_id]["status"] = "failed"
                                    _push_jobs[job_id]["phase"] = "no_images"
                                    _push_jobs[job_id]["message"] = (
                                        "Build succeeded but images expired or unavailable")
                                    _push_jobs[job_id]["done"] = True
                                    _push_jobs[job_id]["percent"] = 100
                            _persist_job_if_done(job_id)
                            return

                        # Auto-generate per-device plans from operational.json
                        # so each device gets the correct upgrade_type (gi_deploy vs normal)
                        if not device_plans or not any(
                            device_plans.get(d, {}).get("upgrade_type") for d in device_ids
                        ):
                            with _push_jobs_lock:
                                if job_id in _push_jobs:
                                    _push_jobs[job_id]["terminal_lines"].append(
                                        "[INFO] Auto-detecting per-device upgrade plans...")
                            _auto_plans = {}
                            for did in device_ids:
                                try:
                                    _mgmt, _sid, _ = _resolve_mgmt_ip(did, ssh_hosts.get(did, ""))
                                    _h = _sid or did
                                    _cfg_dir = _resolve_config_dir(_h)
                                    _op_p = Path(SCALER_ROOT) / "db" / "configs" / _cfg_dir / "operational.json"
                                    if _op_p.exists():
                                        _od = _read_ops_safe(_op_p)
                                        _ds = (_od.get("device_state") or "").upper()
                                        from scaler.connection_strategy import classify_device_state
                                        _mode = classify_device_state(_ds)
                                        _ut = "normal"
                                        if _mode == "GI":
                                            _ut = "gi_deploy"
                                        elif _mode == "RECOVERY":
                                            _ut = "gi_deploy"
                                        if _ut == "normal":
                                            _cur_dnos = _od.get("dnos_version") or ""
                                            _cur_m = re.match(r"(\d+)\.", _cur_dnos)
                                            _tgt_url = (valid_urls.get("dnos") or {}).get("url", "")
                                            _tgt_v = _extract_version_from_dnos_url(_tgt_url)
                                            _tgt_m = re.match(r"(\d+)\.", _tgt_v)
                                            if _cur_m and _tgt_m and int(_cur_m.group(1)) != int(_tgt_m.group(1)):
                                                _ut = "delete_deploy"
                                                with _push_jobs_lock:
                                                    if job_id in _push_jobs:
                                                        _push_jobs[job_id]["terminal_lines"].append(
                                                            _format_upgrade_terminal_line(
                                                                "WARN",
                                                                f"Major version jump "
                                                                f"v{_cur_m.group(1)} -> "
                                                                f"v{_tgt_m.group(1)}, using delete_deploy",
                                                                did,
                                                            ))
                                        _dp = {
                                            "system_type": (
                                                _od.get("system_type")
                                                or _od.get("deploy_system_type")
                                                or ""
                                            ),
                                            "deploy_name": (
                                                _od.get("deploy_name") or _h
                                            ).rstrip(",").strip(),
                                            # Same `_safe_ncc_id` contract
                                            # as everywhere else the bridge
                                            # builds a deploy_params payload
                                            # (`int(... or 0)` tripped on
                                            # str "None" / "null" edge cases
                                            # and produced `ncc-id None` at
                                            # the downstream CLI site).
                                            "ncc_id": _safe_ncc_id(
                                                _od.get("deploy_ncc_id")
                                                if _od.get("deploy_ncc_id") is not None
                                                else _od.get("ncc_id")
                                            ),
                                        }
                                        _auto_plans[did] = {
                                            "upgrade_type": _ut,
                                            "mode": _mode or "?",
                                            "components": components,
                                            "deploy_params": _dp,
                                        }
                                        with _push_jobs_lock:
                                            if job_id in _push_jobs:
                                                _push_jobs[job_id]["terminal_lines"].append(
                                                    _format_upgrade_terminal_line(
                                                        "INFO",
                                                        f"mode={_mode}, type={_ut}, "
                                                        f"sys={_dp['system_type']}, name={_dp['deploy_name']}",
                                                        did,
                                                    ))
                                except Exception as _pe:
                                    with _push_jobs_lock:
                                        if job_id in _push_jobs:
                                            _push_jobs[job_id]["terminal_lines"].append(
                                                _format_upgrade_terminal_line(
                                                    "WARN", f"auto-plan failed: {_pe}", did))
                            if _auto_plans:
                                device_plans = _auto_plans

                        with _push_jobs_lock:
                            if job_id in _push_jobs:
                                _push_jobs[job_id]["phase"] = "upgrading"
                                _push_jobs[job_id]["message"] = (
                                    f"Starting upgrade on {len(device_ids)} device(s)")
                                _push_jobs[job_id]["percent"] = 50
                                _push_jobs[job_id]["terminal_lines"].append(
                                    f"[INFO] Starting upgrade push to {len(device_ids)} device(s)")

                        _auto_push_upgrade(
                            job_id, valid_urls, device_ids, ssh_hosts,
                            components, device_plans=device_plans,
                            max_concurrent=max_concurrent)
                        return

                except Exception as poll_err:
                    with _push_jobs_lock:
                        if job_id in _push_jobs:
                            _push_jobs[job_id]["terminal_lines"].append(
                                f"[WARN] Poll error: {poll_err}")
                time.sleep(poll_interval)

            with _push_jobs_lock:
                if job_id in _push_jobs:
                    _push_jobs[job_id]["status"] = "failed"
                    _push_jobs[job_id]["phase"] = "timeout"
                    _push_jobs[job_id]["message"] = "Build monitor timed out (2h)"
                    _push_jobs[job_id]["done"] = True
                    _push_jobs[job_id]["percent"] = 100
            _persist_job_if_done(job_id)

        except Exception as e:
            import traceback
            traceback.print_exc()
            with _push_jobs_lock:
                if job_id in _push_jobs:
                    _push_jobs[job_id]["status"] = "failed"
                    _push_jobs[job_id]["phase"] = "error"
                    _push_jobs[job_id]["message"] = f"Error: {e}"
                    _push_jobs[job_id]["done"] = True
                    _push_jobs[job_id]["percent"] = 100
                    _push_jobs[job_id]["terminal_lines"].append(f"[ERROR] {e}")
            _persist_job_if_done(job_id)

    _save_active_upgrade(job_id, _push_jobs[job_id])
    from routes._worker_pool import submit_upgrade
    submit_upgrade(_wait_then_upgrade)

    return {
        "job_id": job_id,
        "status": "started",
        "message": f"Monitoring build {build_label}, will auto-upgrade {len(device_ids)} devices",
        "devices": device_ids,
    }


@router.get("/api/operations/image-upgrade/stuck-devices")
def image_upgrade_stuck_devices():
    """List devices that need manual intervention to finish an upgrade.

    Surfaces every device with ``manual_intervention_required = True``
    in operational.json -- typically devices where the bridge crashed
    between ``request system delete`` and ``request system deploy`` and
    the orphan scanner couldn't auto-resume because critical
    parameters (system_type, ncc_id, image URLs) were never persisted.

    The frontend wizard renders this list with a "Resume Stuck Upgrade"
    button so the operator can complete the upgrade without manually
    SSH'ing to the GI shell to issue the deploy command.

    Response shape::

        {
          "stuck_devices": [
            {
              "device_id": "PE-4",
              "scaler_hostname": "PE-4",
              "live_mode": "GI",
              "reason": "Server crashed mid-upgrade with device in GI...",
              "missing": ["image_urls"],
              "suggested_deploy_command": "request system deploy ...",
              "last_phase": "gi_confirmed_at",
              "last_phase_at": "2026-04-27T10:18:55Z",
              "marked_at": "2026-04-27T10:32:18Z",
              "pre_delete_backup_at": "2026-04-27T10:14:02Z"
            },
            ...
          ]
        }
    """
    configs_root = Path(SCALER_ROOT) / "db" / "configs"
    if not configs_root.exists():
        return {"stuck_devices": []}

    stuck = []
    for device_dir in configs_root.iterdir():
        if not device_dir.is_dir():
            continue
        op_path = device_dir / "operational.json"
        if not op_path.exists():
            continue
        try:
            op_data = _read_ops_safe(op_path)
        except Exception:
            continue
        if not op_data.get("manual_intervention_required"):
            continue
        # Don't surface devices where the upgrade has since finished
        # or the operator already cleared the marker.
        if op_data.get("upgrade_completed_at"):
            continue
        stuck.append({
            "device_id": device_dir.name,
            "scaler_hostname": device_dir.name,
            "live_mode": op_data.get("manual_intervention_live_mode", ""),
            "reason": op_data.get("manual_intervention_reason", ""),
            "missing": op_data.get("manual_intervention_missing", []),
            "suggested_deploy_command":
                op_data.get("manual_intervention_deploy_command", ""),
            "last_phase": op_data.get("upgrade_last_phase", ""),
            "last_phase_at": op_data.get("upgrade_last_phase_at", ""),
            "marked_at": op_data.get("manual_intervention_at", ""),
            "pre_delete_backup_at": op_data.get("pre_delete_backup_at", ""),
            "system_type": op_data.get("upgrade_deploy_system_type", ""),
            "deploy_name": op_data.get("upgrade_deploy_name", ""),
            "ncc_id": op_data.get("upgrade_deploy_ncc_id"),
        })

    return {"stuck_devices": stuck}


@router.post("/api/operations/image-upgrade/resume-stuck")
def image_upgrade_resume_stuck(body: dict, request: Request = None):
    """Trigger orphan-in-GI recovery for one or more stuck devices.

    Body::

        {
          "device_ids": ["PE-4", ...],
          # Optional overrides for missing params (image_urls dict):
          "image_urls": {
            "PE-4": {
              "dnos": "http://...",
              "gi": "http://...",
              "baseos": "http://..."
            }
          },
          # Optional system_type / ncc_id overrides per device:
          "deploy_overrides": {
            "PE-4": {"system_type": "DNX-S04", "ncc_id": 1, "deploy_name": "PE-4"}
          }
        }

    For each device:
      1. Apply any provided overrides into operational.json (so the
         orphan scanner finds them in subsequent runs too).
      2. Clear ``manual_intervention_required`` so the same device
         doesn't get re-surfaced while the recovery job is running.
      3. Synthesise a recovery job and submit via
         ``_drive_orphan_in_gi``.

    Returns a per-device ``status`` map (queued / not_found /
    still_missing).
    """
    body = body or {}
    device_ids = body.get("device_ids") or []
    image_urls_overrides = body.get("image_urls") or {}
    deploy_overrides = body.get("deploy_overrides") or {}

    if not isinstance(device_ids, list) or not device_ids:
        raise HTTPException(status_code=400, detail="device_ids is required")

    results = {}
    configs_root = Path(SCALER_ROOT) / "db" / "configs"

    for did in device_ids:
        scaler_hostname = str(did).strip()
        if not scaler_hostname:
            continue
        op_path = configs_root / scaler_hostname / "operational.json"
        if not op_path.exists():
            results[scaler_hostname] = {"status": "not_found"}
            continue

        # Merge overrides into operational.json so the next read picks
        # them up. Use _ops_writer for atomicity.
        try:
            from routes._ops_writer import update_ops as _update_ops_resume

            urls_for_device = image_urls_overrides.get(scaler_hostname) or {}
            deploy_for_device = deploy_overrides.get(scaler_hostname) or {}

            _MI_KEYS = [
                "manual_intervention_required",
                "manual_intervention_reason",
                "manual_intervention_at",
                "manual_intervention_missing",
                "manual_intervention_live_mode",
            ]

            def _resume_mutator(op_data, _urls=urls_for_device, _dep=deploy_for_device):
                if _urls:
                    new_list = []
                    for comp in ("DNOS", "GI", "BaseOS", "dnos", "gi", "baseos"):
                        url = _urls.get(comp) or _urls.get(comp.lower()) or _urls.get(comp.upper())
                        if url:
                            new_list.append([comp.upper() if comp.upper() != "BASEOS" else "BaseOS", url])
                    if new_list:
                        op_data["upgrade_url_list"] = new_list
                if _dep.get("system_type"):
                    op_data["upgrade_deploy_system_type"] = _dep["system_type"]
                if _dep.get("deploy_name"):
                    op_data["upgrade_deploy_name"] = _dep["deploy_name"]
                if _dep.get("ncc_id") is not None:
                    op_data["upgrade_deploy_ncc_id"] = _dep["ncc_id"]
                # Rebuild the deploy command if everything is now known.
                _st = op_data.get("upgrade_deploy_system_type") or ""
                _dn = op_data.get("upgrade_deploy_name") or scaler_hostname
                _nid = op_data.get("upgrade_deploy_ncc_id")
                if _st and _nid is not None:
                    op_data["upgrade_deploy_command"] = (
                        f"request system deploy system-type {_st} "
                        f"name {_dn} ncc-id {_nid}"
                    )
                # Clear the manual-intervention latch (recovery starting).
                # Use `_drop_keys` so the no-shrink invariant in
                # _ops_writer doesn't silently restore them.
                for k in _MI_KEYS:
                    op_data.pop(k, None)
                op_data["_drop_keys"] = list(_MI_KEYS)
                return True

            _update_ops_resume(op_path, _resume_mutator)
        except Exception as exc:
            results[scaler_hostname] = {"status": "ops_write_failed", "error": str(exc)}
            continue

        # Re-read the merged op_data so _drive_orphan_in_gi sees the
        # overrides.
        try:
            op_data = _read_ops_safe(op_path)
        except Exception:
            results[scaler_hostname] = {"status": "ops_read_failed"}
            continue

        backup_path = _locate_pre_delete_backup(scaler_hostname)
        if backup_path is None:
            results[scaler_hostname] = {"status": "no_backup"}
            continue

        try:
            live = _live_probe_for_recovery(scaler_hostname, scaler_hostname) or {}
        except Exception as exc:
            results[scaler_hostname] = {"status": "probe_failed", "error": str(exc)}
            continue
        live_mode = (live.get("mode") or "").upper()
        if live_mode not in ("GI", "BASEOS_SHELL"):
            results[scaler_hostname] = {
                "status": "wrong_mode",
                "live_mode": live_mode,
                "hint": "Device is not in GI/BASEOS_SHELL; nothing to resume.",
            }
            continue

        try:
            _drive_orphan_in_gi(scaler_hostname, op_data, backup_path, live, live_mode)
            results[scaler_hostname] = {"status": "queued"}
        except Exception as exc:
            results[scaler_hostname] = {"status": "queue_failed", "error": str(exc)}

    return {"results": results}


@router.post("/api/operations/image-upgrade/clear-stuck")
def image_upgrade_clear_stuck(body: dict):
    """Manually clear the ``manual_intervention_required`` flag.

    Use when the operator finished the upgrade out-of-band (e.g.
    SSH'd to the GI shell and issued ``request system deploy``
    themselves) and just needs to clear the wizard banner.
    """
    body = body or {}
    device_ids = body.get("device_ids") or []
    if not isinstance(device_ids, list) or not device_ids:
        raise HTTPException(status_code=400, detail="device_ids is required")

    cleared = []
    for did in device_ids:
        scaler_hostname = str(did).strip()
        if not scaler_hostname:
            continue
        op_path = Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname / "operational.json"
        if not op_path.exists():
            continue
        try:
            from routes._ops_writer import update_ops as _update_ops_clr

            _CLR_KEYS = [
                "manual_intervention_required",
                "manual_intervention_reason",
                "manual_intervention_at",
                "manual_intervention_missing",
                "manual_intervention_live_mode",
                "manual_intervention_deploy_command",
            ]

            def _clr_mutator(op_data):
                for k in _CLR_KEYS:
                    op_data.pop(k, None)
                # Honour deletions through the no-shrink invariant.
                op_data["_drop_keys"] = list(_CLR_KEYS)
                return True

            _update_ops_clr(op_path, _clr_mutator)
            cleared.append(scaler_hostname)
        except Exception:
            continue

    return {"cleared": cleared}


@router.get("/api/operations/image-upgrade/recent-sources")
def image_upgrade_recent_sources():
    """Get recent branch/build selections from upgrade_sources_history.json."""
    hist_path = Path(SCALER_ROOT) / "db" / "upgrade_sources_history.json"
    if not hist_path.exists():
        return {"recent_urls": [], "recent_branches": []}
    try:
        data = json.loads(hist_path.read_text())
        return {
            "recent_urls": data.get("recent_urls", []),
            "recent_branches": data.get("recent_branches", []),
        }
    except Exception:
        return {"recent_urls": [], "recent_branches": []}


@router.post("/api/operations/image-upgrade/verify-stacks")
def image_upgrade_verify_stacks(body: dict):
    """SSH to devices and check current stack (show system stack)."""
    device_ids = body.get("device_ids", [])
    ssh_hosts = body.get("ssh_hosts", {})
    if not device_ids:
        raise HTTPException(status_code=400, detail="device_ids is required")
    try:
        cwd = os.getcwd()
        try:
            os.chdir(SCALER_ROOT)
            from scaler.wizard.multi_device import MultiDeviceContext
            devices = []
            for did in device_ids:
                ssh_host = ssh_hosts.get(did, "") if isinstance(ssh_hosts, dict) else ""
                mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(did, ssh_host)
                _ensure_operational_json(scaler_id or did, mgmt_ip)
                class _Dev:
                    hostname = scaler_id or did
                    ip = mgmt_ip
                devices.append(_Dev())
            ctx = MultiDeviceContext(devices)
            result = _verify_stacks_live_impl(ctx)
            return {"success": True, "result": result}
        finally:
            os.chdir(cwd)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _verify_stacks_live_impl(multi_ctx):
    """Wrapper that returns JSON-friendly stack data from devices."""
    from scaler.connection_strategy import connect_for_upgrade
    import paramiko
    user, password = _get_credentials()
    results = {}
    for dev in multi_ctx.devices:
        try:
            conn = connect_for_upgrade(dev.hostname, timeout=15)
            if not conn.get("connected"):
                results[dev.hostname] = {"error": conn.get("abort_reason", "Connection failed")}
                continue
            channel = conn["channel"]
            channel.settimeout(8)
            channel.send("show system stack | no-more\n")
            import time
            time.sleep(1.5)
            out = ""
            while channel.recv_ready():
                out += channel.recv(65535).decode("utf-8", errors="replace")
            conn["ssh"].close()
            results[dev.hostname] = {"stack_output": out}
        except Exception as e:
            results[dev.hostname] = {"error": str(e)}
    return results


@router.post("/api/operations/image-upgrade/restore-config")
def image_upgrade_restore_config(body: dict, request: Request = None):
    """Push backed-up pre-delete config to devices (non-interactive)."""
    device_ids = body.get("device_ids", [])
    ssh_hosts = body.get("ssh_hosts", {})
    if not device_ids:
        raise HTTPException(status_code=400, detail="device_ids is required")
    try:
        cwd = os.getcwd()
        try:
            os.chdir(SCALER_ROOT)
            results = {}
            owner = _get_request_user(request) if request else "default"
            from routes._state import app_user_context
            with app_user_context(owner):
                for did in device_ids:
                    ssh_host = ssh_hosts.get(did, "") if isinstance(ssh_hosts, dict) else ""
                    mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(did, ssh_host)
                    hostname = scaler_id or did
                    logs = []
                    terminal = []
                    try:
                        outcome, message = _post_deploy_restore_from_file(
                            f"manual-restore-{did}",
                            did,
                            hostname,
                            lambda level, msg, _logs=logs: _logs.append((level, msg)),
                            lambda msg, _terminal=terminal: _terminal.append(msg),
                            mgmt_ip_hint=mgmt_ip,
                        )
                        results[did] = {
                            "success": outcome == "success",
                            "status": outcome,
                            "message": message,
                            "hostname": hostname,
                            "management_ip": mgmt_ip,
                            "retryable": outcome == "retryable",
                            "logs": logs[-10:],
                            "terminal_lines": terminal[-20:],
                        }
                    except Exception as e:
                        import traceback
                        results[did] = {
                            "success": False,
                            "status": "error",
                            "message": f"{e}\n\nDetails:\n{traceback.format_exc()}",
                            "hostname": hostname,
                            "management_ip": mgmt_ip,
                            "retryable": _config_repair_message_retryable(str(e)),
                        }
            return {"success": True, "results": results}
        finally:
            os.chdir(cwd)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/operations/{job_id}/cancel")
def operations_cancel(job_id: str, request: Request = None):
    """Cancel a push or upgrade job. Upgrade jobs are marked done immediately;
    the background thread detects _cancel_requested and exits cleanly.

    Ownership is enforced -- only the user that started the job (or an
    admin) may cancel it. Previously `job.get("type")` was checked but the
    job dict actually stores `job_type`, so `is_upgrade` was always False
    and upgrade cancels fell through to the config-push abort path,
    leaving the upgrade running and the device_state stale.
    """
    with _push_jobs_lock:
        job = _push_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if not _is_job_owner_or_admin(request, job):
            raise HTTPException(status_code=403,
                                detail="Not authorized to cancel this job")
        status = job.get("status", "")
        # All upgrade-family jobs must be cancelled immediately -- they run
        # in daemon threads, not a config-push paste session.
        job_type = job.get("job_type", "")
        is_upgrade_like = job_type in ("upgrade", "build_monitor", "wait_and_upgrade")
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
        job["_cancel_requested"] = True

        if is_upgrade_like:
            job["status"] = "cancelled"
            job["done"] = True
            job["cancelled"] = True
            job["success"] = False
            job["message"] = "Cancelled by user"
            job["phase"] = "Cancelled"
            now_iso = __import__("datetime").datetime.utcnow().isoformat() + "Z"
            job["completed_at"] = now_iso
            if not job.get("terminal_lines"):
                job["terminal_lines"] = []
            job["terminal_lines"].append(
                f"[WARN] {job_type or 'Upgrade'} cancelled by user")
            ds = job.get("device_state", {})
            for did, dstate in ds.items():
                if dstate.get("status") in ("running", "pending", "connecting"):
                    dstate["status"] = "cancelled"
                    dstate["phase"] = "Cancelled"
        elif status in ("running", "pending") and not (channel and client and pusher):
            job["status"] = "cancelling"
            job["phase"] = "Aborting paste..."

    if is_upgrade_like:
        _persist_job_if_done(job_id)
        _remove_active_upgrade(job_id)
        return {"status": "cancelled", "success": False,
                "message": f"{job_type or 'Upgrade'} cancelled"}

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
    return {"status": "cancelling", "success": False, "message": "Cancel requested - aborting paste and cleaning device"}


def _upgrade_url_list_from_job(job_data: dict, components: list = None) -> list:
    """Rebuild ``[(COMPONENT, url)]`` from a persisted upgrade snapshot."""
    selected = {str(c).upper() for c in (components or job_data.get("components") or []) if c}
    image_urls = job_data.get("image_urls") or {}
    result = []
    for key, label in (("dnos", "DNOS"), ("gi", "GI"), ("baseos", "BaseOS")):
        if selected and label not in selected:
            continue
        raw = image_urls.get(key) or image_urls.get(label) or {}
        if isinstance(raw, dict):
            if raw.get("valid") is False:
                continue
            url = raw.get("url") or ""
        else:
            url = str(raw or "")
        if not url:
            url = job_data.get(f"{key}_url") or ""
        if url:
            result.append((label, url))
    return result


def _resume_log_fn(job_id: str, device_id: str):
    def _log(level, msg):
        with _push_jobs_lock:
            if job_id in _push_jobs:
                _push_jobs[job_id].setdefault("terminal_lines", []).append(
                    _format_upgrade_terminal_line(level, msg, device_id))
        _persist_active_job_snapshot(job_id)
    return _log


def _live_probe_for_recovery(device_id: str, scaler_hostname: str) -> dict:
    """Recovery-time live mode probe.

    Thin wrapper around the unified
    :mod:`routes._device_mode_resolver`. Returns the stripped status dict
    expected by ``_persist_live_status_to_ops`` (``mode``, ``dnos_ver``,
    ``gi_ver``, ``baseos_ver``, ``install_status``) or ``{}`` when the
    device is unreachable / probe failed -- callers fall back to the
    cached operational.json in that case.

    Uses ``force=True`` so recovery never trusts a stale cache, and
    disables ``persist=False`` because the resolver itself writes
    through to operational.json on a fresh probe.
    """
    try:
        from routes._device_mode_resolver import get_device_mode
        result = get_device_mode(
            device_id, scaler_hostname,
            force=True,
            persist=True,
            publish=True,
            scaler_root=SCALER_ROOT,
        )
    except Exception:
        return {}
    if not result or not result.get("reachable"):
        return {}
    if (result.get("mode") or "?") == "?":
        return {}
    return {
        "mode": result.get("mode") or "?",
        "dnos_ver": result.get("dnos_ver") or "-",
        "gi_ver": result.get("gi_ver") or "-",
        "baseos_ver": result.get("baseos_ver") or "-",
        "install_status": result.get("install_status") or "",
    }


def _resume_one_upgrade_device(job_id: str, job_data: dict, device_id: str):
    """Resume one device after bridge restart without assuming SSH state survived."""
    from datetime import datetime
    from routes._state import app_user_context

    owner = job_data.get("owner") or "default"
    state = (job_data.get("device_state") or {}).get(device_id, {}) or {}
    status = (state.get("status") or "").lower()
    if status in ("completed", "failed", "cancelled", "canceled", "skipped"):
        return

    with app_user_context(owner):
        _log = _resume_log_fn(job_id, device_id)
        components = state.get("components") or job_data.get("components") or ["DNOS", "GI", "BaseOS"]
        url_list = _upgrade_url_list_from_job(job_data, components)
        ssh_hosts = job_data.get("ssh_hosts", {}) if isinstance(job_data.get("ssh_hosts"), dict) else {}
        device_plans = job_data.get("device_plans", {}) if isinstance(job_data.get("device_plans"), dict) else {}
        plan = device_plans.get(device_id, {}) if isinstance(device_plans, dict) else {}
        upgrade_type = (
            state.get("upgrade_type")
            or plan.get("upgrade_type")
            or job_data.get("upgrade_type")
            or "normal"
        )
        deploy_params = dict(plan.get("deploy_params") or {})
        phase = (state.get("phase") or "").lower()

        try:
            user, password = _get_credentials()
        except Exception:
            user, password = "", ""

        ssh_host = ssh_hosts.get(device_id, "")
        try:
            mgmt_ip, scaler_hostname, _ = _resolve_mgmt_ip(device_id, ssh_host)
            scaler_hostname = scaler_hostname or device_id
        except Exception as resolve_err:
            mgmt_ip = ""
            scaler_hostname = _resolve_config_dir(device_id) or device_id
            _log("WARN", f"mgmt_ip resolve failed during recovery: {resolve_err}; using {scaler_hostname}")

        lock_key = mgmt_ip or scaler_hostname or device_id
        op_data = {}
        cfg_dir = _resolve_config_dir(scaler_hostname) or scaler_hostname
        op_path = Path(SCALER_ROOT) / "db" / "configs" / cfg_dir / "operational.json"
        try:
            if op_path.exists():
                op_data = _read_ops_safe(op_path)
        except Exception:
            op_data = {}

        # Re-probe live state on resume. The cached device_state in
        # operational.json can be hours/days stale (e.g. last poll caught
        # the device mid-reboot in GI, then the device finished installing
        # and rebooted into DNOS while the bridge was offline). Trusting
        # the cache here would skip the post-deploy config repair entirely.
        # _persist_live_status_to_ops writes the authoritative result back
        # to operational.json so subsequent reads are accurate.
        live_probe_failed = False
        try:
            live_status = _live_probe_for_recovery(device_id, scaler_hostname)
            if live_status:
                _persist_live_status_to_ops(device_id, scaler_hostname, live_status)
                if op_path.exists():
                    op_data = _read_ops_safe(op_path)
                _log("INFO", f"Live re-probe on resume: mode={live_status.get('mode') or '?'} "
                              f"dnos_ver={live_status.get('dnos_ver') or '-'}")
            else:
                live_probe_failed = True
                _log("WARN", "Live re-probe returned no status; falling back to cached operational.json")
        except Exception as probe_err:
            live_probe_failed = True
            _log("WARN", f"Live re-probe failed: {probe_err}; falling back to cached operational.json")

        op_state = str(op_data.get("device_state") or "").upper()
        legacy_post_deploy = bool(
            op_data.get("deploy_initiated")
            or (
                op_data.get("pre_delete_backup")
                and op_state in ("DNOS", "STANDALONE", "DEPLOYING", "GI", "BASEOS_SHELL")
            )
        )

        def _on_queued(holder):
            holder_owner = (holder or {}).get("owner") or "another user"
            holder_op = (holder or {}).get("op") or "operation"
            _log("INFO", f"Recovery queued behind {holder_owner}'s {holder_op}")

        with _device_scheduler.global_upgrade_slot(
            op="upgrade-recovery", owner=owner, job_id=job_id,
        ):
            with _device_scheduler.exclusive(
                lock_key, "upgrade-recovery", owner, job_id,
                on_queued=_on_queued,
            ):
                _log("INFO", f"Server restart recovery: last phase={phase or 'unknown'}, type={upgrade_type}")
                stage_times = {}
                post_deploy_phases = {
                    "deploying", "post-deploy-verify", "installing",
                    "gi-recovery-reload", "gi-recovery", "config-repair",
                }
                try:
                    if phase in post_deploy_phases or (
                        upgrade_type in ("delete_deploy", "gi_deploy")
                        and int(state.get("percent") or 0) >= 80
                    ) or (legacy_post_deploy and not url_list):
                        _update_device_state(
                            job_id, device_id, status="running",
                            phase="post-deploy-verify",
                            message="Resuming post-deploy monitor after server restart...")
                        ok = _post_deploy_verify(
                            job_id, device_id, scaler_hostname, stage_times, _log,
                            verify_timeout=1800, check_interval=20,
                            url_list=url_list, deploy_params=deploy_params)
                        if not ok:
                            raise RuntimeError(
                                "Post-deploy recovery timed out before DNOS/config repair completed")
                        _update_device_state(
                            job_id, device_id, status="completed", phase="done",
                            percent=100, message="Upgrade recovery complete",
                            completed_at=datetime.utcnow().isoformat() + "Z")
                        _update_operational_after_upgrade(scaler_hostname, "DNOS", success=True)
                        return

                    if phase in ("install", "post-install-verify"):
                        if not mgmt_ip or not url_list:
                            raise RuntimeError(
                                "Cannot resume post-install verification without mgmt_ip and image URLs")
                        ok = _post_install_verify(
                            job_id, device_id, mgmt_ip, user, password,
                            url_list, stage_times, _log, verify_timeout=1200)
                        if not ok:
                            raise RuntimeError("Post-install recovery verification failed")
                        _update_device_state(
                            job_id, device_id, status="completed", phase="done",
                            percent=100, message="Upgrade recovery complete",
                            completed_at=datetime.utcnow().isoformat() + "Z")
                        _update_operational_after_upgrade(scaler_hostname, "DNOS", success=True)
                        return

                    if not url_list:
                        raise RuntimeError(
                            "Cannot safely replay pre-deploy upgrade phase; persisted image URLs are missing")
                    _run_device_upgrade(
                        job_id, device_id, mgmt_ip, user, password, url_list,
                        upgrade_type=upgrade_type, deploy_params=deploy_params,
                        scaler_hostname=scaler_hostname)
                except Exception as exc:
                    _update_device_state(
                        job_id, device_id, status="failed", phase="error",
                        percent=100, error=str(exc),
                        message=f"Recovery failed: {exc}",
                        completed_at=datetime.utcnow().isoformat() + "Z")
                    _log("ERROR", f"Recovery failed: {exc}")
                    _update_operational_after_upgrade(
                        scaler_hostname, str(upgrade_type).upper(),
                        success=False, error=str(exc))
                    raise


def _resume_interrupted_upgrade_job(job_id: str, job_data: dict):
    """Resume monitoring/repair for an upgrade job interrupted by server restart."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from datetime import datetime
    from routes._state import app_user_context

    owner = job_data.get("owner") or "default"
    devices = job_data.get("devices") or list((job_data.get("device_state") or {}).keys())
    max_concurrent = max(1, min(int(job_data.get("max_concurrent") or 3), 10))

    with app_user_context(owner):
        with _push_jobs_lock:
            if job_id not in _push_jobs:
                return
            job = _push_jobs[job_id]
            job["status"] = "running"
            job["done"] = False
            job["phase"] = "restart_recovery"
            job["message"] = "Server restarted -- resuming upgrade monitor"
            job.setdefault("terminal_lines", []).append(
                "[INFO] Server restarted -- resuming upgrade monitor and config repair")
        _persist_active_job_snapshot(job_id)

        runnable = [
            d for d in devices
            if ((job_data.get("device_state") or {}).get(d, {}) or {}).get("status")
            not in ("completed", "failed", "cancelled", "canceled", "skipped")
        ]
        if not runnable:
            _finalize_upgrade_job(job_id, devices)
            return

        with ThreadPoolExecutor(max_workers=max_concurrent) as pool:
            futures = {pool.submit(_resume_one_upgrade_device, job_id, job_data, did): did for did in runnable}
            for fut in as_completed(futures):
                did = futures[fut]
                try:
                    fut.result()
                except Exception as exc:
                    with _push_jobs_lock:
                        if job_id in _push_jobs:
                            _push_jobs[job_id].setdefault("terminal_lines", []).append(
                                _format_upgrade_terminal_line(
                                    "ERROR", f"restart recovery failed: {exc}", did))
        with _push_jobs_lock:
            if job_id in _push_jobs:
                _push_jobs[job_id]["recovered_after_restart_at"] = datetime.utcnow().isoformat() + "Z"
        _finalize_upgrade_job(job_id, devices)


def _mark_manual_intervention_required(
    scaler_hostname: str,
    reason: str,
    *,
    suggested_deploy_command: str = "",
    missing_fields: list = None,
    live_mode: str = "",
) -> None:
    """Annotate operational.json so the wizard can surface a Resume button.

    The wizard (``/api/upgrade/stuck-devices``) reads
    ``manual_intervention_required`` and shows the operator a
    pre-filled "Resume Stuck Upgrade" panel with the deploy command and
    a list of missing parameters. This is the safety-net path for
    server-crash-mid-upgrade scenarios where the orphan scanner can't
    auto-resume (e.g. because the deploy URLs were never persisted, the
    system_type is unknown, or the device is in BASEOS_SHELL needing
    manual gi-manager attention).
    """
    if not scaler_hostname:
        return
    try:
        op_file = Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname / "operational.json"
        if not op_file.parent.exists():
            return
        from datetime import datetime
        from routes._ops_writer import update_ops as _update_ops_mi
        _now_iso = datetime.utcnow().isoformat() + "Z"

        def _mi_mutator(op_data):
            op_data["manual_intervention_required"] = True
            op_data["manual_intervention_reason"] = reason
            op_data["manual_intervention_at"] = _now_iso
            op_data["manual_intervention_live_mode"] = (live_mode or "").upper()
            if suggested_deploy_command:
                op_data["manual_intervention_deploy_command"] = suggested_deploy_command
            if missing_fields:
                op_data["manual_intervention_missing"] = list(missing_fields)
            return True

        _update_ops_mi(op_file, _mi_mutator, create_if_missing=True)
    except Exception as exc:
        print(f"[STARTUP] Could not mark {scaler_hostname} manual_intervention: {exc}")


def _drive_orphan_in_gi(
    scaler_hostname: str,
    op_data: dict,
    backup_path,
    live: dict,
    live_mode: str,
) -> None:
    """Recover a device that crashed BETWEEN delete and deploy.

    Two outcomes:

    1. Phase markers + persisted deploy parameters give us enough
       context to re-issue ``request system deploy`` automatically.
       We synthesize an upgrade job and let ``_run_device_upgrade``
       resume from the GI checkpoint (it reads the same phase markers
       and skips the already-completed ``request system delete``).

    2. We're missing one or more critical parameters
       (``system_type``, ``ncc_id``, image URLs). We mark
       ``manual_intervention_required`` with the deploy command we
       CAN reconstruct and the list of missing fields. The wizard's
       new "Resume Stuck Upgrade" panel surfaces this to the operator.
    """
    import threading
    import uuid
    from datetime import datetime
    from pathlib import Path as _Path

    last_phase = _latest_phase_reached(op_data)
    has_delete_marker = bool(_get_phase_marker(op_data, "delete_sent_at"))
    has_gi_marker = bool(_get_phase_marker(op_data, "gi_confirmed_at"))
    has_deploy_marker = bool(_get_phase_marker(op_data, "deploy_sent_at"))

    # Prefer markers persisted at deploy_sent_at (most authoritative)
    sys_type = op_data.get("upgrade_deploy_system_type") or ""
    deploy_name = op_data.get("upgrade_deploy_name") or scaler_hostname
    ncc_id = op_data.get("upgrade_deploy_ncc_id")
    suggested_deploy_command = op_data.get("upgrade_deploy_command") or ""

    # Image URL list (each element is [component, url])
    raw_url_list = op_data.get("upgrade_url_list") or []
    url_list = []
    if isinstance(raw_url_list, list):
        for item in raw_url_list:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                comp, url = item[0], item[1]
                if comp and url:
                    url_list.append((str(comp).upper(), str(url)))

    # Fallback: try resolving system_type from the live device tag if
    # we never persisted it (older upgrades pre-marker schema).
    if not sys_type:
        try:
            sys_type = (op_data.get("system_type") or "").strip()
        except Exception:
            sys_type = ""

    missing = []
    if not sys_type:
        missing.append("system_type")
    if ncc_id is None or ncc_id == "":
        missing.append("ncc_id")
    if not url_list:
        missing.append("image_urls")

    print(
        f"[STARTUP] Orphan-in-GI {scaler_hostname}: live_mode={live_mode}, "
        f"last_phase={last_phase or '?'}, has_delete_marker={has_delete_marker}, "
        f"has_gi_marker={has_gi_marker}, has_deploy_marker={has_deploy_marker}, "
        f"missing={missing or 'none'}"
    )

    # Reconstruct the deploy command for the wizard / operator even
    # when we don't auto-resume.
    if not suggested_deploy_command and sys_type and ncc_id is not None:
        suggested_deploy_command = (
            f"request system deploy system-type {sys_type} "
            f"name {deploy_name} ncc-id {ncc_id}"
        )

    if missing:
        # Cannot auto-resume safely; surface to the operator.
        reason = (
            f"Server crashed mid-upgrade with device in {live_mode}. "
            f"Cannot auto-resume: missing {', '.join(missing)}."
        )
        _mark_manual_intervention_required(
            scaler_hostname, reason,
            suggested_deploy_command=suggested_deploy_command,
            missing_fields=missing,
            live_mode=live_mode,
        )
        return

    # Have enough to auto-resume. Build a synthetic job that will
    # resume from the GI checkpoint via _resume_one_upgrade_device.
    # The resumer reads the same phase markers and skips the already-
    # completed `request system delete`.
    owner = op_data.get("upgrade_owner") or op_data.get("last_owner") or "default"
    upgrade_type = op_data.get("upgrade_type") or "delete_deploy"

    job_id = f"orphan-gi-resume-{scaler_hostname}-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.utcnow().isoformat() + "Z"
    synth = {
        "id": job_id,
        "job_type": "upgrade",
        "owner": owner,
        "status": "running",
        "phase": "gi_resume",
        "message": (
            f"Orphan recovery for {scaler_hostname} (crashed in {live_mode}; "
            f"resuming from {last_phase or 'unknown phase'})"
        ),
        "started_at": now_iso,
        "devices": [scaler_hostname],
        "components": [c for c, _ in url_list] or ["DNOS", "GI", "BaseOS"],
        # _upgrade_url_list_from_job reads `image_urls` as
        # {component: {"url": ...}}. Build that shape from url_list.
        "image_urls": {
            comp.lower(): {"url": url, "valid": True}
            for comp, url in url_list
        },
        "ssh_hosts": {},
        "device_plans": {
            scaler_hostname: {
                "deploy_params": {
                    "system_type": sys_type,
                    "deploy_name": deploy_name,
                    "ncc_id": ncc_id,
                },
                "upgrade_type": upgrade_type,
            }
        },
        "upgrade_type": upgrade_type,
        "max_concurrent": 1,
        "synthetic_recovery": True,
        "terminal_lines": [
            f"[INFO] Orphan-in-GI recovery synthesized for {scaler_hostname} "
            f"(backup={backup_path.name if hasattr(backup_path, 'name') else backup_path}, "
            f"live mode={live_mode}, last_phase={last_phase or '?'})",
            f"[INFO] Resume plan: {'skip delete (already done), ' if has_delete_marker else ''}"
            f"{'skip GI wait (already in GI), ' if has_gi_marker else ''}"
            f"{'replay deploy' if not has_deploy_marker else 'monitor existing deploy'}",
        ],
        "device_state": {
            scaler_hostname: {
                "status": "running",
                "phase": "gi_resume",
                "percent": 30,
                "components": [c for c, _ in url_list] or ["DNOS", "GI", "BaseOS"],
                "upgrade_type": upgrade_type,
                "message": f"Orphan-in-GI recovery -- resuming from {last_phase or 'unknown'}",
            }
        },
    }
    with _push_jobs_lock:
        _push_jobs[job_id] = synth
    _persist_active_job_snapshot(job_id)

    from routes._worker_pool import submit_upgrade
    submit_upgrade(lambda jid=job_id, jdata=synth: _resume_interrupted_upgrade_job(jid, jdata))
    print(
        f"[STARTUP] Orphan-in-GI recovery job {job_id} submitted for {scaler_hostname} "
        f"(sys_type={sys_type}, ncc_id={ncc_id}, components={[c for c, _ in url_list]})"
    )


def _scan_orphan_post_deploy_devices(already_handled: set = None):
    """Detect devices stranded mid-post-deploy after a server restart.

    Runs alongside the snapshot-based replay so devices that were upgraded
    BEFORE the snapshotting feature existed (or whose snapshots were lost)
    still get their config repaired. The scanner walks every device's
    ``operational.json``, looks for residual post-deploy markers
    (``pre_delete_backup`` registered, ``deploy_initiated`` set, or
    ``upgrade_in_progress`` true), live-probes the device, and -- only
    when the device is reachable in DNOS *and* a real backup file is on
    disk *and* no active job is already covering it -- synthesizes a
    one-shot recovery job that drives ``_resume_one_upgrade_device``
    through the post-deploy verify + config repair pipeline.

    ``already_handled`` is the set of device IDs covered by snapshot-based
    resume so we don't double-process them.
    """
    import threading
    import uuid
    from datetime import datetime

    already_handled = set(already_handled or ())
    configs_root = Path(SCALER_ROOT) / "db" / "configs"
    if not configs_root.exists():
        return

    candidates = []
    for device_dir in configs_root.iterdir():
        if not device_dir.is_dir():
            continue
        scaler_hostname = device_dir.name
        if scaler_hostname in already_handled:
            continue
        if _device_has_active_job(scaler_hostname, scaler_hostname):
            continue
        op_path = device_dir / "operational.json"
        if not op_path.exists():
            continue
        try:
            op_data = _read_ops_safe(op_path)
        except Exception:
            continue

        # Detect a stranded upgrade. Any of these markers indicates the
        # device entered some part of an upgrade flow that did not run
        # to completion. Phase markers (delete_sent_at etc.) are the
        # most reliable signal -- they're stamped by `_stamp_phase`
        # right before each critical CLI step.
        has_phase_marker = any(
            op_data.get(m) for m in _UPGRADE_PHASE_MARKERS
            if m != "upgrade_completed_at"
        )
        # ...but a device that has already stamped
        # `upgrade_completed_at` is fully done; don't reprocess it.
        if op_data.get("upgrade_completed_at"):
            continue
        has_marker = bool(
            has_phase_marker
            or op_data.get("upgrade_in_progress")
            or op_data.get("deploy_initiated")
            or op_data.get("pre_delete_backup")
            or op_data.get("install_status") in ("IN_PROGRESS", "DEPLOYING")
        )
        if not has_marker:
            continue

        backup_path = _locate_pre_delete_backup(scaler_hostname)
        if backup_path is None:
            continue
        try:
            txt = backup_path.read_text()
            meaningful = sum(
                1 for l in txt.splitlines()
                if l.strip() and not l.strip().startswith("#")
            )
        except Exception:
            meaningful = 0
        if meaningful < 5:
            continue
        candidates.append((scaler_hostname, op_data, backup_path))

    if not candidates:
        return

    print(f"[STARTUP] Orphan post-deploy scan found {len(candidates)} candidate(s): "
          f"{[c[0] for c in candidates]}")

    def _drive_orphan(scaler_hostname: str, op_data: dict, backup_path: Path):
        live = {}
        try:
            live = _live_probe_for_recovery(scaler_hostname, scaler_hostname) or {}
        except Exception as exc:
            print(f"[STARTUP] Orphan probe {scaler_hostname} failed: {exc}")
            return
        live_mode = (live.get("mode") or "").upper()

        # Crash-mid-upgrade recovery for GI / BASEOS_SHELL.
        #
        # Old behaviour: refuse to drive recovery when the device is in
        # GI/BASEOS_SHELL because the pre-existing flow assumed deploy
        # had already happened and only ran post-deploy verify. That
        # left the exact PE-4 case (server crashed BETWEEN delete and
        # deploy) requiring manual `request system deploy` from the
        # operator.
        #
        # New behaviour: when phase markers tell us the deploy was
        # never sent (`deploy_sent_at` missing) AND we have the full
        # deploy parameters persisted (system_type + ncc_id +
        # url_list), synthesize a job that drives the in-GI flow:
        # load images (idempotent) and issue `request system deploy`.
        # The post-deploy verify then drives the rest.
        #
        # When we DON'T have enough information to drive recovery
        # safely (no system_type or no image URLs) we mark the device
        # as ``manual_intervention_required`` -- the wizard surfaces
        # a "Resume Stuck Upgrade" button with the deploy command
        # pre-filled so the operator can complete the upgrade with
        # one click after providing whatever's missing.
        if live_mode in ("GI", "BASEOS_SHELL"):
            return _drive_orphan_in_gi(
                scaler_hostname, op_data, backup_path, live, live_mode
            )

        if live_mode not in ("DNOS", "STANDALONE", "DEPLOYING"):
            print(f"[STARTUP] Orphan {scaler_hostname}: skipping, live mode={live_mode or '?'}")
            return
        try:
            _persist_live_status_to_ops(scaler_hostname, scaler_hostname, live)
        except Exception:
            pass

        owner = op_data.get("upgrade_owner") or op_data.get("last_owner") or "default"
        upgrade_type = op_data.get("upgrade_type") or "delete_deploy"

        job_id = f"orphan-recover-{scaler_hostname}-{uuid.uuid4().hex[:8]}"
        now_iso = datetime.utcnow().isoformat() + "Z"
        synth = {
            "id": job_id,
            "job_type": "upgrade",
            "owner": owner,
            "status": "running",
            "phase": "restart_recovery",
            "message": f"Orphan post-deploy recovery for {scaler_hostname}",
            "started_at": now_iso,
            "devices": [scaler_hostname],
            "components": ["DNOS", "GI", "BaseOS"],
            "image_urls": {},
            "ssh_hosts": {},
            "device_plans": {},
            "upgrade_type": upgrade_type,
            "max_concurrent": 1,
            "synthetic_recovery": True,
            "terminal_lines": [
                f"[INFO] Orphan post-deploy recovery synthesized for {scaler_hostname} "
                f"(backup={backup_path.name}, live mode={live_mode})",
            ],
            "device_state": {
                scaler_hostname: {
                    "status": "running",
                    "phase": "post-deploy-verify",
                    "percent": 80,
                    "components": ["DNOS", "GI", "BaseOS"],
                    "upgrade_type": upgrade_type,
                    "message": "Orphan recovery -- resuming post-deploy",
                }
            },
        }
        with _push_jobs_lock:
            _push_jobs[job_id] = synth
        _persist_active_job_snapshot(job_id)

        from routes._worker_pool import submit_upgrade
        submit_upgrade(lambda jid=job_id, jdata=synth: _resume_interrupted_upgrade_job(jid, jdata))
        print(f"[STARTUP] Orphan recovery job {job_id} submitted for {scaler_hostname} "
              f"(backup={backup_path.name})")

    for scaler_hostname, op_data, backup_path in candidates:
        try:
            _drive_orphan(scaler_hostname, op_data, backup_path)
        except Exception as exc:
            print(f"[STARTUP] Orphan recovery for {scaler_hostname} failed: {exc}")


def _recover_active_upgrades():
    """On startup, recover in-flight upgrade jobs.

    wait_and_upgrade jobs in build-monitoring phase are fully resumable --
    the Jenkins build keeps running regardless of our server. Jobs that
    were already upgrading are resumed from the last persisted device
    phase so post-deploy monitoring and config repair continue. After the
    snapshot-based replay we run a live-probing orphan scan so devices
    whose snapshots were never saved (legacy upgrades) still get their
    post-deploy config repair driven to completion.
    """
    handled_devices: set = set()
    if not _ACTIVE_UPGRADES_PATH.exists():
        try:
            _scan_orphan_post_deploy_devices(handled_devices)
        except Exception as exc:
            print(f"[STARTUP] Orphan post-deploy scan failed: {exc}")
        return
    try:
        with open(_ACTIVE_UPGRADES_PATH) as f:
            upgrades = json.load(f)
    except Exception:
        try:
            _scan_orphan_post_deploy_devices(handled_devices)
        except Exception as exc:
            print(f"[STARTUP] Orphan post-deploy scan failed: {exc}")
        return

    import threading
    from datetime import datetime
    _RESUMABLE_PHASES = {
        "waiting_for_build", "building", "build_queued",
        "resolving_urls", "auto_push_starting",
    }

    for job_id, job_data in list(upgrades.items()):
        if job_data.get("done"):
            _remove_active_upgrade(job_id)
            continue

        # Defensive: snapshots saved before Wave 1 (2026-04-19) did not
        # include `owner`. Fall back to "default" so ownership checks and
        # per-user credential resolution don't break on restart.
        if not job_data.get("owner"):
            job_data["owner"] = "default"

        job_type = job_data.get("job_type", "")
        phase = job_data.get("phase", "")

        if job_type == "wait_and_upgrade" and phase in _RESUMABLE_PHASES:
            branch = job_data.get("branch")
            if not branch:
                _remove_active_upgrade(job_id)
                continue
            job_data["terminal_lines"] = job_data.get("terminal_lines", [])
            job_data["terminal_lines"].append(
                "[INFO] Server restarted -- resuming build monitor")
            with _push_jobs_lock:
                _push_jobs[job_id] = job_data

            def _resume_wau(jid, jdata):
                import time
                from scaler.jenkins_integration import JenkinsClient, validate_artifact_url

                br = jdata["branch"]
                device_ids = jdata.get("devices", [])
                ssh_hosts = jdata.get("ssh_hosts", {})
                device_plans = jdata.get("device_plans", {})
                components = jdata.get("components", ["DNOS", "GI", "BaseOS"])
                max_concurrent = jdata.get("max_concurrent", 3)
                poll_interval = 30
                max_wait = 7200
                started = time.time()

                try:
                    jenkins = JenkinsClient()
                    while time.time() - started < max_wait:
                        try:
                            build = jenkins.get_build_info(br, latest=True)
                            if not build:
                                time.sleep(poll_interval)
                                continue
                            elapsed_min = int((time.time() - started) / 60)
                            if build.building:
                                pct = min(5 + int(elapsed_min * 1.0), 45)
                                with _push_jobs_lock:
                                    if jid in _push_jobs:
                                        _push_jobs[jid]["phase"] = "building"
                                        _push_jobs[jid]["message"] = (
                                            f"Build #{build.build_number} running ({elapsed_min}m)")
                                        _push_jobs[jid]["percent"] = pct
                                        _push_jobs[jid]["build_number"] = build.build_number
                            else:
                                build_ok = build.result == "SUCCESS"
                                with _push_jobs_lock:
                                    if jid in _push_jobs:
                                        _push_jobs[jid]["build_number"] = build.build_number
                                        _push_jobs[jid]["terminal_lines"].append(
                                            f"[{'OK' if build_ok else 'FAIL'}] Build #{build.build_number}"
                                            f" finished: {build.result}")
                                if not build_ok:
                                    with _push_jobs_lock:
                                        if jid in _push_jobs:
                                            _push_jobs[jid]["status"] = "failed"
                                            _push_jobs[jid]["phase"] = "build_failed"
                                            _push_jobs[jid]["message"] = (
                                                f"Build #{build.build_number} failed: {build.result}")
                                            _push_jobs[jid]["done"] = True
                                    _persist_job_if_done(jid)
                                    _remove_active_upgrade(jid)
                                    return

                                urls = {}
                                try:
                                    stack_urls = jenkins.get_stack_urls(br, build.build_number)
                                    for comp in ["dnos", "gi", "baseos"]:
                                        url = stack_urls.get(comp)
                                        if url:
                                            ok, msg = validate_artifact_url(url, timeout=10)
                                            urls[comp] = {"url": url, "valid": ok, "detail": msg}
                                except Exception as e:
                                    with _push_jobs_lock:
                                        if jid in _push_jobs:
                                            _push_jobs[jid]["terminal_lines"].append(
                                                f"[WARN] URL resolution: {e}")

                                valid_urls = {k: v for k, v in urls.items() if v.get("valid")}
                                if not valid_urls:
                                    with _push_jobs_lock:
                                        if jid in _push_jobs:
                                            _push_jobs[jid]["status"] = "failed"
                                            _push_jobs[jid]["phase"] = "no_images"
                                            _push_jobs[jid]["message"] = "Build OK but images unavailable"
                                            _push_jobs[jid]["done"] = True
                                    _persist_job_if_done(jid)
                                    _remove_active_upgrade(jid)
                                    return

                                with _push_jobs_lock:
                                    if jid in _push_jobs:
                                        _push_jobs[jid]["phase"] = "upgrading"
                                        _push_jobs[jid]["percent"] = 50
                                        _push_jobs[jid]["message"] = (
                                            f"Starting upgrade on {len(device_ids)} device(s)")

                                _auto_push_upgrade(
                                    jid, valid_urls, device_ids, ssh_hosts,
                                    components, device_plans=device_plans,
                                    max_concurrent=max_concurrent)
                                return
                        except Exception as pe:
                            with _push_jobs_lock:
                                if jid in _push_jobs:
                                    _push_jobs[jid]["terminal_lines"].append(
                                        f"[WARN] Poll error: {pe}")
                        time.sleep(poll_interval)

                    with _push_jobs_lock:
                        if jid in _push_jobs:
                            _push_jobs[jid]["status"] = "failed"
                            _push_jobs[jid]["phase"] = "timeout"
                            _push_jobs[jid]["message"] = "Build monitor timed out (2h)"
                            _push_jobs[jid]["done"] = True
                    _persist_job_if_done(jid)
                    _remove_active_upgrade(jid)
                except Exception as e:
                    with _push_jobs_lock:
                        if jid in _push_jobs:
                            _push_jobs[jid]["status"] = "failed"
                            _push_jobs[jid]["phase"] = "error"
                            _push_jobs[jid]["message"] = f"Resume error: {e}"
                            _push_jobs[jid]["done"] = True
                            _push_jobs[jid]["terminal_lines"].append(f"[ERROR] {e}")
                    _persist_job_if_done(jid)
                    _remove_active_upgrade(jid)

            for _did in (job_data.get("devices") or []):
                handled_devices.add(_did)
            from routes._worker_pool import submit_upgrade
            _resume_jid = job_id
            _resume_data = job_data
            submit_upgrade(lambda: _resume_wau(_resume_jid, _resume_data))
            print(f"[STARTUP] Resumed wait_and_upgrade job {job_id} (phase={phase})")
            continue

        job_data["terminal_lines"] = job_data.get("terminal_lines", [])
        job_data["terminal_lines"].append(
            "[INFO] Server restarted while upgrade was running -- "
            "resuming monitor from persisted phase.")
        with _push_jobs_lock:
            _push_jobs[job_id] = job_data
        _persist_active_job_snapshot(job_id)
        for _did in (job_data.get("devices") or list((job_data.get("device_state") or {}).keys())):
            handled_devices.add(_did)
        from routes._worker_pool import submit_upgrade
        _resume_jid = job_id
        _resume_data = job_data
        submit_upgrade(lambda: _resume_interrupted_upgrade_job(_resume_jid, _resume_data))
        print(f"[STARTUP] Resumed upgrade job {job_id} (phase={phase})")

    try:
        _scan_orphan_post_deploy_devices(handled_devices)
    except Exception as exc:
        print(f"[STARTUP] Orphan post-deploy scan failed: {exc}")


def _recover_active_builds():
    """On startup, resume monitoring for any builds that were in-flight when server stopped."""
    if not _ACTIVE_BUILDS_PATH.exists():
        return
    try:
        with open(_ACTIVE_BUILDS_PATH) as f:
            builds = json.load(f)
    except Exception:
        return

    import threading
    from datetime import datetime
    for job_id, job_data in builds.items():
        if job_data.get("done"):
            _remove_active_build(job_id)
            continue
        branch = job_data.get("branch")
        if not branch:
            _remove_active_build(job_id)
            continue
        # Defensive: legacy snapshots had no owner -- default to "default"
        if not job_data.get("owner"):
            job_data["owner"] = "default"
        started = job_data.get("started_at", "")
        if started:
            try:
                age_h = (datetime.utcnow() - datetime.fromisoformat(
                    started.replace("Z", "+00:00").replace("+00:00", "")
                )).total_seconds() / 3600
                if age_h > 3:
                    job_data["status"] = "failed"
                    job_data["phase"] = "lost_on_restart"
                    job_data["message"] = "Server restarted -- build may still be on Jenkins"
                    job_data["done"] = True
                    with _push_jobs_lock:
                        _push_jobs[job_id] = job_data
                    _persist_job_if_done(job_id)
                    _remove_active_build(job_id)
                    continue
            except Exception:
                pass

        job_data["terminal_lines"] = job_data.get("terminal_lines", [])
        job_data["terminal_lines"].append("[INFO] Server restarted -- resuming build monitor")
        with _push_jobs_lock:
            _push_jobs[job_id] = job_data

        def _resume_monitor(jid, jdata):
            import time
            from scaler.jenkins_integration import JenkinsClient
            br = jdata["branch"]
            components = jdata.get("components", ["DNOS", "GI", "BaseOS"])
            try:
                jenkins = JenkinsClient()
                max_wait = 7200
                poll_interval = 30
                started_ts = time.time()
                while time.time() - started_ts < max_wait:
                    build = jenkins.get_build_info(br, latest=True)
                    if not build:
                        time.sleep(poll_interval)
                        continue
                    if build.building:
                        elapsed_min = int((time.time() - started_ts) / 60)
                        pct = min(10 + int(elapsed_min * 1.5), 85)
                        with _push_jobs_lock:
                            if jid in _push_jobs:
                                _push_jobs[jid]["phase"] = "building"
                                _push_jobs[jid]["message"] = f"Build #{build.build_number} running ({elapsed_min}m, recovered)"
                                _push_jobs[jid]["percent"] = pct
                                _push_jobs[jid]["build_number"] = build.build_number
                    else:
                        build_ok = build.result == "SUCCESS"
                        with _push_jobs_lock:
                            if jid in _push_jobs:
                                _push_jobs[jid]["build_number"] = build.build_number
                                _push_jobs[jid]["percent"] = 90 if build_ok else 100
                                _push_jobs[jid]["terminal_lines"].append(
                                    f"[{'OK' if build_ok else 'FAIL'}] Build #{build.build_number} finished: {build.result}")
                        if build_ok:
                            _resolve_and_maybe_push(jid, br, build.build_number, jenkins, components)
                        else:
                            with _push_jobs_lock:
                                if jid in _push_jobs:
                                    _push_jobs[jid]["status"] = "failed"
                                    _push_jobs[jid]["phase"] = "build_failed"
                                    _push_jobs[jid]["message"] = f"Build #{build.build_number} failed: {build.result}"
                                    _push_jobs[jid]["done"] = True
                            _persist_job_if_done(jid)
                        _remove_active_build(jid)
                        return
                    time.sleep(poll_interval)
                with _push_jobs_lock:
                    if jid in _push_jobs:
                        _push_jobs[jid]["status"] = "failed"
                        _push_jobs[jid]["phase"] = "timeout"
                        _push_jobs[jid]["message"] = "Build monitor timed out"
                        _push_jobs[jid]["done"] = True
                _persist_job_if_done(jid)
                _remove_active_build(jid)
            except Exception as e:
                with _push_jobs_lock:
                    if jid in _push_jobs:
                        _push_jobs[jid]["status"] = "failed"
                        _push_jobs[jid]["message"] = f"Recovery error: {e}"
                        _push_jobs[jid]["done"] = True
                        _push_jobs[jid]["terminal_lines"].append(f"[ERROR] {e}")
                _persist_job_if_done(jid)
                _remove_active_build(jid)

        from routes._worker_pool import submit_upgrade
        _resume_mid = job_id
        _resume_mdata = job_data
        submit_upgrade(lambda: _resume_monitor(_resume_mid, _resume_mdata))
        print(f"[STARTUP] Resumed build monitor for {job_id} (branch={branch})")

