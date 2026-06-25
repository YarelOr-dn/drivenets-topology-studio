"""Scaler bridge routes: operations."""
from __future__ import annotations

import asyncio
import json
import threading
import time
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from routes.bridge_helpers import (
    _ACTIVE_BUILDS_PATH, _ACTIVE_UPGRADES_PATH, _INTERNAL_JOB_KEYS,
    _MAX_HISTORY_JOBS, _MAX_TERMINAL_LINES_IN_HISTORY, _PUSH_HISTORY_PATH,
    _build_job_name, _evict_stale_jobs_locked, _fetch_config_via_ssh,
    _get_cached_config, _get_credentials, _get_device_context,
    _invalidate_device_context_cache, _iso_from_ts,
    _load_push_history, _persist_job_if_done, _remove_active_build,
    _remove_active_upgrade, _resolve_mgmt_ip, _sanitize_job, _save_active_build,
    _save_active_upgrade, _save_push_history,
)
from routes._state import (
    _push_jobs, _push_jobs_lock,
    _get_request_user, _get_request_role, _is_job_owner_or_admin,
    normalize_owner_lax,
)
from routes._device_scheduler import (
    scheduler as _device_scheduler,
    DeviceBusyError,
    PerUserLimitError,
)
from routes._authz import authorize_push
from routes._audit_log import record_event as _audit_event


# Wave 7.4: per-user job-store quota. The in-memory ``_push_jobs`` dict
# grows unboundedly as long as the user keeps pushing. A malicious or
# retry-happy client can pollute it with thousands of completed rows,
# slowing down SSE endpoints and admin views. This helper caps per-user
# footprint to ``TP_PER_USER_JOB_MAX`` (default 100) and evicts the
# OLDEST COMPLETED entries for that same owner before admitting the
# next push. If every slot is held by an in-flight job (dry-run hold
# included), we reject with 429 so the user can tidy up their sessions.
def _env_positive_int(name: str, default: int) -> int:
    import os as _os
    try:
        return max(1, int(_os.environ.get(name, default)))
    except (TypeError, ValueError):
        return default


_PER_USER_JOB_MAX = _env_positive_int("TP_PER_USER_JOB_MAX", 100)


def _enforce_per_user_job_quota(owner: str) -> None:
    """Cap the number of rows ``owner`` holds in ``_push_jobs``.

    Evicts oldest-completed rows for ``owner``. Raises 429 only if
    every row is a still-running job (no terminal rows to evict).
    Safe to call with arbitrary owner; anonymous callers share the
    ``default`` bucket which is governed by the same cap.
    """
    owner_norm = normalize_owner_lax(owner)
    from routes._state import _push_jobs, _push_jobs_lock

    with _push_jobs_lock:
        owned = [
            (jid, job) for jid, job in _push_jobs.items()
            if isinstance(job, dict)
            and normalize_owner_lax(job.get("owner", "default")) == owner_norm
        ]
        if len(owned) < _PER_USER_JOB_MAX:
            return

        # Evict oldest-DONE rows first. Sort by started_at_ts (falls
        # back to started_at ISO string for older jobs).
        def _age_key(item):
            jid, j = item
            t = j.get("started_at_ts")
            if isinstance(t, (int, float)):
                return float(t)
            return 0.0

        owned.sort(key=_age_key)
        evictable = [
            (jid, j) for jid, j in owned
            if j.get("done") and not j.get("awaiting_decision")
        ]
        while len(owned) >= _PER_USER_JOB_MAX and evictable:
            jid, _ = evictable.pop(0)
            _push_jobs.pop(jid, None)
            owned = [(j, job) for j, job in owned if j != jid]

        if len(owned) >= _PER_USER_JOB_MAX:
            in_flight = sum(
                1 for _, j in owned
                if not j.get("done") or j.get("awaiting_decision")
            )
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "per_user_job_quota",
                    "message": (
                        f"You have {in_flight} active jobs and "
                        f"{len(owned) - in_flight} recent job rows -- "
                        f"cap is {_PER_USER_JOB_MAX}. Wait for in-flight "
                        f"jobs to finish or DELETE completed ones."
                    ),
                    "in_flight": in_flight,
                    "total": len(owned),
                    "max_per_user": _PER_USER_JOB_MAX,
                    "retry_after_s": 10,
                },
                headers={"Retry-After": "10"},
            )


router = APIRouter()

@router.post("/api/operations/delete-hierarchy")
def delete_hierarchy_op(body: dict = None, request: Request = None):
    """Delete a config hierarchy from a device. dry_run=True for preview only."""
    body = body or {}
    device_id = body.get("device_id")
    hierarchy = body.get("hierarchy")
    dry_run = bool(body.get("dry_run", True))
    ssh_host = body.get("ssh_host", "")
    sub_path = body.get("sub_path", "").strip()
    if not device_id or not hierarchy:
        raise HTTPException(status_code=400, detail="device_id and hierarchy required")

    # Wave 7.6: delete-hierarchy is a write action -- require the same
    # role/user checks the regular push endpoint uses. We resolve the
    # mgmt_ip first so the authz layer can emit an accurate audit
    # event (and 404 cleanly on unknown device).
    _owner = _get_request_user(request) if request else "default"
    _role = _get_request_role(request) if request else "admin"
    try:
        _mgmt_ip_pre, _, _ = _resolve_mgmt_ip(device_id, ssh_host)
    except Exception:
        _mgmt_ip_pre = ""
    authorize_push(
        owner=normalize_owner_lax(_owner), role=_role,
        device_id=device_id, mgmt_ip=_mgmt_ip_pre or "",
        action="delete_hierarchy",
    )

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

        if sub_path:
            from scaler.config_pusher import ConfigPusher
            hier_map = {
                "interfaces": "interfaces interface",
                "services": "network-services",
                "bgp": "protocols bgp",
                "igp": "protocols",
                "vrf": "network-services vrf",
            }
            prefix = hier_map.get(hierarchy, hierarchy)
            delete_cmd = f"no {prefix} {sub_path}"
            commands = [delete_cmd]
            pusher = ConfigPusher()
            success, message, _ = pusher.run_cli_commands(
                device=device, commands=commands, dry_run=dry_run
            )
            return {"success": success, "message": message, "commands_preview": commands}

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


@router.post("/api/operations/validate")
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

@router.post("/api/config/push/estimate")
def push_estimate(body: dict = None):
    """Get push time estimates for config (terminal paste, file upload, lofd). Uses timing_history.json."""
    body = body or {}
    config_text = body.get("config") or body.get("config_text") or ""
    device_id = body.get("device_id") or ""
    ssh_host = body.get("ssh_host") or ""
    if not config_text and device_id:
        try:
            mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(device_id, ssh_host)
            config_text = _get_cached_config(scaler_id)
            if not config_text:
                user, password = _get_credentials()
                config_text = _fetch_config_via_ssh(scaler_id, mgmt_ip, user, password)
        except Exception:
            pass
    if not config_text:
        raise HTTPException(status_code=400, detail="config or device_id required")
    try:
        from scaler.config_pusher import get_accurate_push_estimates, ConfigPusher
        platform = ConfigPusher.extract_platform_from_config(config_text)
        include_delete = "\nno " in config_text
        estimates = get_accurate_push_estimates(
            config_text=config_text,
            platform=platform,
            include_delete=include_delete,
            device_hostname=device_id or None,
        )
        return estimates
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"config_pusher unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/operations/push")
def push_config(body: dict = None, request: Request = None):
    """Push config to device using ConfigPusher. Returns job_id for progress streaming."""
    import uuid
    from datetime import datetime

    body = body or {}
    device_id = body.get("device_id")
    config_text = body.get("config", "")
    mode = (body.get("mode") or "merge").lower()
    dry_run = bool(body.get("dry_run", False))
    ssh_host = body.get("ssh_host", "")
    push_method = (body.get("push_method") or "terminal_paste").lower()
    load_mode = (body.get("load_mode") or "merge").lower()
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    if not config_text or not config_text.strip():
        raise HTTPException(status_code=400, detail="config required")

    owner = _get_request_user(request) if request else "default"
    role = _get_request_role(request) if request else "admin"
    # Wave 7.2: canonicalise once here so EVERY downstream component
    # (scheduler counters, SSH pool key, audit log, job dict) sees the
    # same string. Prior to this, case/whitespace drift across JWT
    # middleware could split a single user into multiple counter buckets.
    owner = normalize_owner_lax(owner)

    # Wave 7.6: resolve mgmt_ip first, then gate on authorization BEFORE
    # touching any scheduler state. Resolution failure collapses to
    # mgmt_ip="" which the authz helper turns into 404 (without leaking
    # whether the user was otherwise allowed).
    try:
        _mgmt_ip_for_cap, _, _ = _resolve_mgmt_ip(device_id, ssh_host)
    except Exception:
        _mgmt_ip_for_cap = None
    authorize_push(
        owner=owner,
        role=role,
        device_id=device_id,
        mgmt_ip=_mgmt_ip_for_cap or "",
        action="push",
    )

    # Wave 6.5: pre-queue rejection. If the device queue is already deep,
    # return 503 + Retry-After BEFORE creating a job row -- the client can
    # back off cleanly instead of waiting minutes for a serialized slot.
    if _mgmt_ip_for_cap:
        try:
            _device_scheduler.check_device_queue_capacity(_mgmt_ip_for_cap)
        except DeviceBusyError as exc:
            _audit_event(
                action="push_rejected", owner=owner, role=role,
                device_id=device_id, mgmt_ip=_mgmt_ip_for_cap,
                result="device_busy",
                detail={"queue_depth": exc.queue_depth},
            )
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "device_busy",
                    "message": str(exc),
                    "device_id": device_id,
                    "queue_depth": exc.queue_depth,
                    "retry_after_s": exc.retry_after_s,
                },
                headers={"Retry-After": str(exc.retry_after_s)},
            )

    # Wave 7.4: per-user job-store quota. Before burning a per-user
    # reservation, make sure this user hasn't already filled the in-
    # memory job dict with stale rows. Evicts oldest-COMPLETED rows
    # owned by ``owner`` to make room; returns 429 only if every slot
    # is held by an in-flight job for this user.
    try:
        _enforce_per_user_job_quota(owner)
    except HTTPException:
        _audit_event(
            action="push_rejected", owner=owner, role=role,
            device_id=device_id, mgmt_ip=_mgmt_ip_for_cap or "",
            result="per_user_job_quota",
        )
        raise

    # Wave 6.4: per-user push cap. Reject before creating the job row; the
    # counter is released in the worker's finally block.
    try:
        _device_scheduler.reserve_user_push(owner)
    except PerUserLimitError as exc:
        _audit_event(
            action="push_rejected", owner=owner, role=role,
            device_id=device_id, mgmt_ip=_mgmt_ip_for_cap or "",
            result="per_user_push_cap",
            detail={
                "in_flight": exc.in_flight,
                "max_per_user": exc.max_per_user,
            },
        )
        raise HTTPException(
            status_code=429,
            detail={
                "error": "too_many_pushes",
                "message": str(exc),
                "in_flight": exc.in_flight,
                "max_per_user": exc.max_per_user,
                "retry_after_s": exc.retry_after_s,
            },
            headers={"Retry-After": str(exc.retry_after_s)},
        )

    job_id = str(uuid.uuid4())
    job_name = _build_job_name(body, device_id, config_text)
    _now_ts = time.time()
    with _push_jobs_lock:
        _push_jobs[job_id] = {
            "job_id": job_id,
            "owner": owner,
            "role": role,
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
            "mgmt_ip": _mgmt_ip_for_cap or "",
            "ssh_host": ssh_host,
            "started_at": datetime.utcnow().isoformat() + "Z",
            # Wave 7.1: epoch timestamp so the reaper can do fast math
            # without re-parsing ISO strings on every scan pass.
            "started_at_ts": _now_ts,
            "config_text": config_text,
            "mode": mode,
            "dry_run": dry_run,
            "_cancel_requested": False,
            "push_method": push_method,
            "load_mode": load_mode,
            "estimated_total_seconds": None,
        }

    def _cancel_check():
        with _push_jobs_lock:
            return _push_jobs.get(job_id, {}).get("_cancel_requested", False)

    # Wave 7.12: snapshot the pre-queue resolution so the worker uses
    # the SAME mgmt_ip that authz / Wave 6 caps were evaluated against.
    # If the DB / DNS flips between pre-queue and worker, authz could
    # have green-lit device A while the worker would target device B,
    # subtly bypassing the policy. Re-resolve in the worker only when
    # the pre-queue hint was empty.
    _prequeued_mgmt_ip = _mgmt_ip_for_cap

    def _run_push():
        import time as _time
        start_time = _time.time()
        sched_token = None
        push_slot_handle = None
        user_push_reserved = True  # reserved in the HTTP handler above
        try:
            if _prequeued_mgmt_ip:
                mgmt_ip = _prequeued_mgmt_ip
                try:
                    _, scaler_id, via = _resolve_mgmt_ip(device_id, ssh_host)
                except Exception:
                    scaler_id, via = device_id, "cached"
            else:
                mgmt_ip, scaler_id, via = _resolve_mgmt_ip(device_id, ssh_host)
            user, password = _get_credentials()
            from scaler.models import Device
            from scaler.config_pusher import ConfigPusher, get_accurate_push_estimates

            device = Device(
                id=device_id,
                hostname=device_id,
                ip=mgmt_ip,
                username=user,
                password=Device.encode_password(password),
            )
            pusher = ConfigPusher()
            est_method = "file_upload" if push_method == "file_upload" else "terminal_paste"
            try:
                est = get_accurate_push_estimates(config_text, device_hostname=device_id)
                est_data = est.get("estimates", {}).get(est_method, {})
                total_est = est_data.get("total", 60)
                with _push_jobs_lock:
                    if job_id in _push_jobs:
                        _push_jobs[job_id]["estimated_total_seconds"] = total_est
            except Exception:
                pass

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

            # Wave 2.1: per-device serialization. Two concurrent pushes to
            # the SAME mgmt_ip get queued; pushes to DIFFERENT devices run
            # in parallel. Surfaces a "Queued behind X" line in the live
            # terminal while waiting.
            def _on_queued(holder):
                try:
                    holder_owner = (holder or {}).get("owner") or "another user"
                    holder_op = (holder or {}).get("op") or "operation"
                    _live_output(
                        f"[INFO] Device {mgmt_ip} busy: queued behind "
                        f"{holder_owner}'s {holder_op}..."
                    )
                    _progress(f"Queued behind {holder_owner}'s {holder_op}", 2)
                except Exception:
                    pass

            # Wave 4.3: stream queue position updates while the caller waits.
            def _on_progress(info):
                try:
                    pos = (info or {}).get("position", 0)
                    total = (info or {}).get("total", 0)
                    elapsed = (info or {}).get("elapsed_s", 0.0)
                    _live_output(
                        f"[INFO] Device {mgmt_ip}: queue position {pos}/{total} "
                        f"(waiting {elapsed:.0f}s)"
                    )
                    _progress(f"Queued {pos}/{total} ({elapsed:.0f}s)", 2)
                    with _push_jobs_lock:
                        if job_id in _push_jobs:
                            _push_jobs[job_id]["queue_position"] = pos
                            _push_jobs[job_id]["queue_total"] = total
                except Exception:
                    pass

            # Wave 6.1: global push-slot cap. Acquired OUTSIDE the per-
            # device lock so 100 users pushing to 100 different devices
            # still throttle through the configured slot count instead of
            # spawning 100 simultaneous SSH sessions. Released in the
            # matching branch below (or in finally as safety net).
            def _on_push_slot_queued(info):
                try:
                    qlen = (info or {}).get("queue_len", 0)
                    slots_max = (info or {}).get("slots_max", 0)
                    _live_output(
                        f"[INFO] Global push slots full ({slots_max} in-flight); "
                        f"queued at position {qlen}..."
                    )
                    _progress(f"Waiting for global push slot (q={qlen})", 1)
                except Exception:
                    pass

            push_slot_handle = _device_scheduler.acquire_global_push_slot(
                op="push", owner=owner, job_id=job_id,
                on_queued=_on_push_slot_queued,
            )
            slot_wait = push_slot_handle.get("wait_s", 0.0) if push_slot_handle else 0.0
            if slot_wait > 0.5:
                _live_output(
                    f"[INFO] Global push slot acquired after {slot_wait:.1f}s."
                )

            sched_token = _device_scheduler.acquire(
                mgmt_ip, "push", owner, job_id,
                on_queued=_on_queued,
                on_progress=_on_progress,
            )
            if sched_token is not None and sched_token.wait_s > 0.5:
                _live_output(
                    f"[INFO] Device {mgmt_ip} acquired after "
                    f"{sched_token.wait_s:.1f}s wait."
                )

            if push_method == "file_upload":
                if load_mode == "override":
                    success, message = pusher.push_config(
                        device, config_text, dry_run=dry_run,
                        progress_callback=_progress, live_output_callback=_live_output)
                else:
                    success, message = pusher.push_config_merge(
                        device, config_text, dry_run=dry_run,
                        progress_callback=_progress, live_output_callback=_live_output)
                elapsed = _time.time() - start_time
                with _push_jobs_lock:
                    if job_id in _push_jobs:
                        _push_jobs[job_id]["completed_at"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
                        _push_jobs[job_id]["elapsed_seconds"] = elapsed
                        _push_jobs[job_id]["success"] = success
                        _push_jobs[job_id]["message"] = message
                        _push_jobs[job_id]["status"] = "completed" if success else "failed"
                        _push_jobs[job_id]["done"] = True
                # file_upload completes in one pass -- release device lock.
                _device_scheduler.release(sched_token)
                sched_token = None
                _device_scheduler.release_global_push_slot(push_slot_handle)
                push_slot_handle = None
                if success:
                    _invalidate_device_context_cache(device_id=device_id,
                                                    mgmt_ip=mgmt_ip)
                try:
                    from scaler.config_pusher import save_timing_record
                    save_timing_record(
                        platform=ConfigPusher.extract_platform_from_config(config_text),
                        line_count=len(config_text.splitlines()),
                        actual_time_seconds=elapsed,
                        device_hostname=device_id,
                        push_method="file_upload",
                        push_type=job_name,
                    )
                except Exception:
                    pass
                _persist_job_if_done(job_id)
            elif dry_run:
                success, message, channel, client = pusher.push_config_terminal_check_and_hold(
                    device, config_text,
                    progress_callback=_progress, live_output_callback=_live_output,
                    cancel_check=_cancel_check)
                with _push_jobs_lock:
                    if job_id in _push_jobs:
                        if success:
                            _push_jobs[job_id]["phase"] = "awaiting_decision"
                            _push_jobs[job_id]["message"] = "Commit check passed - Commit or Cancel"
                            _push_jobs[job_id]["percent"] = 70
                            _push_jobs[job_id]["status"] = "awaiting_decision"
                            _push_jobs[job_id]["awaiting_decision"] = True
                            # Wave 7.1: stamp when the user became
                            # responsible for committing/cancelling so
                            # the reaper can measure abandonment age
                            # precisely (not from job creation).
                            _push_jobs[job_id]["awaiting_since_ts"] = _time.time()
                            _push_jobs[job_id]["check_passed"] = True
                            _push_jobs[job_id]["_channel"] = channel
                            _push_jobs[job_id]["_client"] = client
                            _push_jobs[job_id]["_pusher"] = pusher
                            _push_jobs[job_id]["_live_output"] = _live_output
                            # Dry-run held session keeps the device busy until
                            # the user decides Commit / Cancel. Transfer lock
                            # ownership from this thread to the job dict; the
                            # push_commit / push_cancel endpoints release it.
                            # Wave 6.1: also transfer the global push slot
                            # so the cap stays in effect for the full
                            # dry_run -> commit/cancel round-trip.
                            _push_jobs[job_id]["_sched_token"] = sched_token
                            sched_token = None
                            _push_jobs[job_id]["_push_slot_handle"] = push_slot_handle
                            push_slot_handle = None
                        else:
                            elapsed = _time.time() - start_time
                            cancelled = "cancelled" in message.lower() or "discarded" in message.lower()
                            _push_jobs[job_id]["success"] = False
                            _push_jobs[job_id]["message"] = message
                            _push_jobs[job_id]["status"] = "cancelled" if cancelled else "failed"
                            _push_jobs[job_id]["done"] = True
                            _push_jobs[job_id]["check_passed"] = False
                            _push_jobs[job_id]["completed_at"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
                            _push_jobs[job_id]["elapsed_seconds"] = elapsed
                            if cancelled:
                                _push_jobs[job_id]["cancelled"] = True
                _persist_job_if_done(job_id)
            else:
                success, message = pusher.push_config_terminal_paste(
                    device, config_text, dry_run=False,
                    progress_callback=_progress, live_output_callback=_live_output,
                    cancel_check=_cancel_check)
                elapsed = _time.time() - start_time
                with _push_jobs_lock:
                    if job_id in _push_jobs:
                        cancelled = not success and ("cancelled" in (message or "").lower() or "discarded" in (message or "").lower())
                        _push_jobs[job_id]["success"] = success
                        _push_jobs[job_id]["message"] = message
                        _push_jobs[job_id]["status"] = "cancelled" if cancelled else ("completed" if success else "failed")
                        _push_jobs[job_id]["done"] = True
                        _push_jobs[job_id]["completed_at"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
                        _push_jobs[job_id]["elapsed_seconds"] = elapsed
                        if cancelled:
                            _push_jobs[job_id]["cancelled"] = True
                _device_scheduler.release(sched_token)
                sched_token = None
                _device_scheduler.release_global_push_slot(push_slot_handle)
                push_slot_handle = None
                if success:
                    _invalidate_device_context_cache(device_id=device_id,
                                                    mgmt_ip=mgmt_ip)
                try:
                    from scaler.config_pusher import save_timing_record
                    save_timing_record(
                        platform=ConfigPusher.extract_platform_from_config(config_text),
                        line_count=len(config_text.splitlines()),
                        actual_time_seconds=elapsed,
                        device_hostname=device_id,
                        push_method="terminal_paste",
                        push_type=job_name,
                    )
                except Exception:
                    pass
                _persist_job_if_done(job_id)
        except Exception as e:
            # Wave 7.8: if the exception happened AFTER awaiting_decision
            # was flipped True (dry-run success stashed resources, then a
            # later line raised -- very rare but possible), force the
            # job back to a terminal state so the reaper doesn't treat
            # it as a live held session. This also ensures the finally
            # block below sees ``awaiting=False`` and releases the
            # per-user counter instead of stashing it indefinitely.
            with _push_jobs_lock:
                if job_id in _push_jobs:
                    j = _push_jobs[job_id]
                    j["success"] = False
                    j["message"] = str(e)
                    j["status"] = "failed"
                    j["done"] = True
                    j["awaiting_decision"] = False
                    # Re-claim locally any handles we had stashed so the
                    # finally block can release them via the canonical
                    # scheduler APIs.
                    if j.get("_sched_token") and sched_token is None:
                        sched_token = j.pop("_sched_token", None)
                    if j.get("_push_slot_handle") and push_slot_handle is None:
                        push_slot_handle = j.pop("_push_slot_handle", None)
                    j.pop("_user_push_reserved", None)
            _persist_job_if_done(job_id)
            try:
                _audit_event(
                    action="push_failed", owner=owner, role=role,
                    device_id=device_id, mgmt_ip=mgmt_ip or "",
                    job_id=job_id, result="exception",
                    detail={"error": str(e)[:256]},
                )
            except Exception:
                pass
        finally:
            # Safety net: if we crashed before the branch-specific release
            # ran, give the device back. release(None) is a no-op.
            _device_scheduler.release(sched_token)
            # Wave 6.1: safety-net release for the global push slot.
            _device_scheduler.release_global_push_slot(push_slot_handle)
            # Wave 6.4: release the per-user reservation unless this job
            # is still awaiting a user decision (dry_run path) -- in that
            # case the commit/cancel endpoint releases it.
            if user_push_reserved:
                try:
                    with _push_jobs_lock:
                        j = _push_jobs.get(job_id) or {}
                        awaiting = bool(j.get("awaiting_decision"))
                        is_done = bool(j.get("done"))
                except Exception:
                    awaiting = False
                    is_done = True
                # Wave 7.8: a job can be marked done (failed / cancelled)
                # even if awaiting_decision was flipped True earlier --
                # in that case we MUST release the counter here, never
                # stash it, otherwise the reaper + the commit/cancel
                # endpoints all no-op and the counter leaks.
                if (not awaiting) or is_done:
                    _device_scheduler.release_user_push(owner)
                    user_push_reserved = False
                else:
                    with _push_jobs_lock:
                        if job_id in _push_jobs:
                            _push_jobs[job_id]["_user_push_reserved"] = True

            # Wave 7.5: audit terminal state. We emit exactly once per
            # job from the worker -- commit/cancel/reaper audit their
            # own events. The awaiting-decision path deliberately does
            # NOT audit here because the session is still live.
            try:
                with _push_jobs_lock:
                    j = _push_jobs.get(job_id) or {}
                    if j.get("done") and not j.get("_audited_terminal"):
                        j["_audited_terminal"] = True
                        _final_status = j.get("status", "")
                        _success = bool(j.get("success"))
                        _elapsed = j.get("elapsed_seconds")
                _audit_event(
                    action="push_complete" if _success else "push_failed",
                    owner=owner, role=role,
                    device_id=device_id, mgmt_ip=mgmt_ip or "",
                    job_id=job_id,
                    result=_final_status or ("ok" if _success else "failed"),
                    detail={"elapsed_s": _elapsed, "mode": mode,
                            "dry_run": dry_run},
                )
            except Exception:
                pass

    # Wave 6.2: submit to bounded push pool instead of spawning a fresh
    # OS thread per job. The owner ContextVar is re-bound inside the
    # worker so _get_credentials() sees the right user even when the
    # pool thread is reused across jobs.
    from routes._state import app_user_context
    from routes._worker_pool import submit_push
    def _run_push_with_user():
        with app_user_context(owner):
            _run_push()

    # Wave 7.12: emit ``push_start`` BEFORE submit_push so the audit log
    # is always ordered start -> complete/failed even if the pool runs
    # the worker synchronously in a race-free window (CPython will yield
    # the GIL between submit and return). If the submit itself fails we
    # also emit ``push_rejected`` in the except branch, which pairs with
    # the start if the start had already been written.
    _audit_event(
        action="push_start", owner=owner, role=role,
        device_id=device_id, mgmt_ip=_mgmt_ip_for_cap or "",
        job_id=job_id, result="accepted",
        detail={"mode": mode, "dry_run": dry_run,
                "push_method": push_method,
                "config_bytes": len(config_text)},
    )

    # Wave 7.3: roll back the user reservation and the job row if the
    # executor refuses the task (pool shut down, queue saturated, etc.)
    # so the HTTP caller sees a clean 503 and no hidden state lingers.
    try:
        submit_push(_run_push_with_user)
    except Exception as exc:
        with _push_jobs_lock:
            _push_jobs.pop(job_id, None)
        try:
            _device_scheduler.release_user_push(owner)
        except Exception:
            pass
        _audit_event(
            action="push_rejected", owner=owner, role=role,
            device_id=device_id, mgmt_ip=_mgmt_ip_for_cap or "",
            result="submit_failed", detail={"error": str(exc)[:256]},
        )
        raise HTTPException(
            status_code=503,
            detail={
                "error": "push_queue_saturated",
                "message": "Push worker pool is unavailable; retry shortly.",
                "retry_after_s": 5,
            },
            headers={"Retry-After": "5"},
        )

    return {"job_id": job_id, "status": "started"}


@router.get("/api/config/push/progress/{job_id}")
def push_progress(job_id: str, request: Request = None, token: str = None):
    """SSE stream for push progress. Includes terminal lines for live display.
    Accepts JWT via ?token= query param (EventSource doesn't support headers)."""
    from fastapi.responses import StreamingResponse
    import asyncio
    import json

    _multiuser_on = False
    try:
        from api.auth.service import decode_token
        _multiuser_on = True
    except ImportError:
        decode_token = None

    if _multiuser_on:
        if not token:
            return StreamingResponse(
                iter([f'data: {json.dumps({"error": "Authentication required"})}\n\n']),
                media_type="text/event-stream",
                status_code=401,
            )
        payload = None
        try:
            payload = decode_token(token)
        except Exception:
            pass
        if not payload:
            return StreamingResponse(
                iter([f'data: {json.dumps({"error": "Invalid or expired token"})}\n\n']),
                media_type="text/event-stream",
                status_code=401,
            )
        req_user = payload.get("sub", "default")
        req_role = payload.get("role", "viewer")
        with _push_jobs_lock:
            job_check = _push_jobs.get(job_id, {})
        if job_check and req_role != "admin" and job_check.get("owner", "default") != req_user:
            return StreamingResponse(
                iter([f'data: {json.dumps({"error": "Not your job"})}\n\n']),
                media_type="text/event-stream",
                status_code=403,
            )

    async def _event_stream():
        last_cursor = 0
        _not_found_count = 0
        while True:
            with _push_jobs_lock:
                job = dict(_push_jobs.get(job_id, {}))
            if not job:
                _not_found_count += 1
                if _not_found_count >= 3:
                    gone = {"done": True, "status": "completed", "percent": 100,
                            "message": "Job finished or was cleaned up",
                            "terminal": [], "terminal_full": []}
                    yield f"data: {json.dumps(gone)}\n\n"
                    break
                await asyncio.sleep(1)
                continue
            _not_found_count = 0
            lines = job.get("terminal_lines", [])
            new_lines = lines[last_cursor:]
            last_cursor = len(lines)
            job["terminal"] = new_lines
            job["terminal_full"] = lines[-500:] if len(lines) > 500 else lines
            ds = job.get("device_state", {})
            if ds:
                percents = [s.get("percent", 0) for s in ds.values() if s.get("status") != "skipped"]
                if percents:
                    job["percent"] = int(sum(percents) / len(percents))
            from datetime import datetime, timezone
            started = job.get("started_at")
            if started:
                try:
                    dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                    elapsed = (datetime.now(timezone.utc) - dt).total_seconds()
                    job["elapsed_seconds"] = max(0, elapsed)
                    est_total = job.get("estimated_total_seconds") or 60
                    pct = job.get("percent") or 0
                    if pct > 0:
                        naive_total = elapsed / (pct / 100.0)
                        naive_remaining = max(0, naive_total - elapsed)
                        budget_remaining = max(0, est_total - elapsed)
                        remaining = min(naive_remaining, budget_remaining * 1.2)
                    else:
                        remaining = max(0, est_total - elapsed)
                    job["estimated_remaining_seconds"] = remaining
                except Exception:
                    job["elapsed_seconds"] = 0
                    job["estimated_remaining_seconds"] = job.get("estimated_total_seconds") or 60
            sse_job = {k: v for k, v in job.items() if not k.startswith("_")}
            if job.get("done"):
                yield f"data: {json.dumps(sse_job)}\n\n"
                break
            yield f"data: {json.dumps(sse_job)}\n\n"
            await asyncio.sleep(0.5)

    return StreamingResponse(_event_stream(), media_type="text/event-stream")


@router.post("/api/operations/push/{job_id}/commit")
def push_commit(job_id: str, request: Request = None):
    """Commit held config on the same SSH session. Call after dry_run push when check passed."""
    sched_token = None
    req_user = _get_request_user(request) if request else "default"
    req_role = _get_request_role(request) if request else "admin"
    with _push_jobs_lock:
        job = _push_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if request and not _is_job_owner_or_admin(request, job):
            _audit_event(
                action="push_commit_rejected", owner=req_user, role=req_role,
                job_id=job_id, result="forbidden",
                detail={"job_owner": job.get("owner", "")},
            )
            raise HTTPException(status_code=403, detail="Not your job")
        # Wave 7.1 interlock: the reaper may have flipped the job to a
        # terminal state milliseconds before this commit arrived. Treat
        # that as 410 Gone so the client learns the session is dead.
        if job.get("reaped") or job.get("status") == "reaped":
            raise HTTPException(
                status_code=410,
                detail={
                    "error": "session_reaped",
                    "message": (
                        "This dry-run was auto-released after being idle; "
                        "no state remains to commit. Start a new push."
                    ),
                },
            )
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
        # Wave 7.12: ``.pop`` instead of ``del`` — if a racing reaper or
        # retried commit already cleared one of these keys, ``del`` would
        # KeyError and leak the remaining resources.
        job.pop("_channel", None)
        job.pop("_client", None)
        job.pop("_pusher", None)
        job.pop("_live_output", None)
        sched_token = job.pop("_sched_token", None)
        push_slot_handle = job.pop("_push_slot_handle", None)
        had_user_reservation = bool(job.pop("_user_push_reserved", False))
        commit_owner = normalize_owner_lax(job.get("owner", "default"))
        commit_device_id = job.get("device_id", "")
        commit_mgmt_ip = job.get("mgmt_ip", "")
        job["awaiting_decision"] = False

    try:
        success, message = pusher.commit_held_session(channel, client, live_output_callback=live_output)
    finally:
        # Release the per-device lock + global push slot + per-user
        # reservation obtained during the dry_run phase.
        _device_scheduler.release(sched_token)
        _device_scheduler.release_global_push_slot(push_slot_handle)
        if had_user_reservation:
            _device_scheduler.release_user_push(commit_owner)
    with _push_jobs_lock:
        if job_id in _push_jobs:
            _push_jobs[job_id]["success"] = success
            _push_jobs[job_id]["message"] = message
            _push_jobs[job_id]["status"] = "completed" if success else "failed"
            _push_jobs[job_id]["done"] = True
            _push_jobs[job_id]["_audited_terminal"] = True
    if success and commit_device_id:
        _invalidate_device_context_cache(device_id=commit_device_id)
    _audit_event(
        action="push_commit", owner=commit_owner, role=req_role,
        device_id=commit_device_id, mgmt_ip=commit_mgmt_ip,
        job_id=job_id, result="ok" if success else "failed",
        detail={"message": (message or "")[:256],
                "by": req_user if req_user != commit_owner else None},
    )
    _persist_job_if_done(job_id)
    return {"status": "completed" if success else "failed", "success": success, "message": message}


@router.post("/api/operations/push/{job_id}/cancel")
def push_cancel(job_id: str, request: Request = None):
    """Cancel held config (discard candidate) and close SSH session."""
    sched_token = None
    req_user = _get_request_user(request) if request else "default"
    req_role = _get_request_role(request) if request else "admin"
    with _push_jobs_lock:
        job = _push_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if request and not _is_job_owner_or_admin(request, job):
            _audit_event(
                action="push_cancel_rejected", owner=req_user, role=req_role,
                job_id=job_id, result="forbidden",
                detail={"job_owner": job.get("owner", "")},
            )
            raise HTTPException(status_code=403, detail="Not your job")
        # Wave 7.1: if the reaper already released this job, the cancel
        # endpoint has nothing to do. Return 200 so the client UI can
        # collapse the dialog without error.
        if job.get("reaped") or job.get("status") == "reaped":
            return {"status": "cancelled", "success": False,
                    "message": "Session was already auto-released (reaped)."}
        channel = job.get("_channel")
        client = job.get("_client")
        pusher = job.get("_pusher")
        live_output = job.get("_live_output")
        if channel and client and pusher:
            job["status"] = "cancelling"
            job["phase"] = "Cancelling..."
            # Wave 7.12: defensive pop (see push_commit rationale).
            job.pop("_channel", None)
            job.pop("_client", None)
            job.pop("_pusher", None)
            job.pop("_live_output", None)
        sched_token = job.pop("_sched_token", None)
        push_slot_handle = job.pop("_push_slot_handle", None)
        had_user_reservation = bool(job.pop("_user_push_reserved", False))
        cancel_owner = normalize_owner_lax(job.get("owner", "default"))
        cancel_device_id = job.get("device_id", "")
        cancel_mgmt_ip = job.get("mgmt_ip", "")
        job["awaiting_decision"] = False

    try:
        if channel and client and pusher:
            pusher.cancel_held_session(channel, client, live_output_callback=live_output)
    finally:
        _device_scheduler.release(sched_token)
        _device_scheduler.release_global_push_slot(push_slot_handle)
        if had_user_reservation:
            _device_scheduler.release_user_push(cancel_owner)
    with _push_jobs_lock:
        if job_id in _push_jobs:
            _push_jobs[job_id]["success"] = False
            _push_jobs[job_id]["message"] = "Cancelled (config discarded)"
            _push_jobs[job_id]["status"] = "cancelled"
            _push_jobs[job_id]["done"] = True
            _push_jobs[job_id]["cancelled"] = True
            _push_jobs[job_id]["_audited_terminal"] = True
    _audit_event(
        action="push_cancel", owner=cancel_owner, role=req_role,
        device_id=cancel_device_id, mgmt_ip=cancel_mgmt_ip,
        job_id=job_id, result="cancelled",
        detail={"by": req_user if req_user != cancel_owner else None},
    )
    _persist_job_if_done(job_id)
    return {"status": "cancelled", "success": False, "message": "Cancelled"}


@router.post("/api/operations/push/{job_id}/cleanup")
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




@router.get("/api/operations/jobs")
def list_jobs(request: Request):
    """List jobs scoped to the requesting user (admin sees all)."""
    user = _get_request_user(request)
    role = _get_request_role(request)
    is_admin = role == "admin"
    with _push_jobs_lock:
        active = [_sanitize_job(j) for j in _push_jobs.values()
                  if is_admin or j.get("owner", "default") == user]
    history = _load_push_history()
    seen = {j.get("job_id") or j.get("id") for j in active
            if j.get("job_id") or j.get("id")}
    for h in history:
        sanitized = _sanitize_job(h)
        hid = sanitized.get("job_id") or sanitized.get("id")
        if hid and hid not in seen:
            if is_admin or sanitized.get("owner", "default") == user:
                active.append(sanitized)
                seen.add(hid)
    active.sort(key=lambda x: x.get("started_at", ""), reverse=True)
    return {"jobs": active[: _MAX_HISTORY_JOBS + 20]}


@router.get("/api/operations/jobs/{job_id}")
def get_job(job_id: str, request: Request = None):
    """Get full job state including terminal output."""
    with _push_jobs_lock:
        job = _push_jobs.get(job_id)
    if job:
        if request and not _is_job_owner_or_admin(request, job):
            raise HTTPException(status_code=403, detail="Not your job")
        return _sanitize_job(job)
    for h in _load_push_history():
        if h.get("job_id") == job_id:
            if request and not _is_job_owner_or_admin(request, h):
                raise HTTPException(status_code=403, detail="Not your job")
            return h
    raise HTTPException(status_code=404, detail="Job not found")


@router.post("/api/operations/jobs/{job_id}/retry")
def retry_job(job_id: str, request: Request = None):
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
    if request and not _is_job_owner_or_admin(request, job):
        raise HTTPException(status_code=403, detail="Not your job")
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
    return push_config(body, request=request)


@router.delete("/api/operations/jobs/{job_id}")
def delete_job(job_id: str, request: Request = None):
    """Remove job from history (owner or admin only).

    Wave 7 hardened: also tears down any held SSH session (the Wave 6
    version only released scheduler-side resources, which meant an
    abandoned-then-deleted dry-run leaked the paramiko channel + client
    until process exit).
    """
    leaked_sched_token = None
    leaked_push_slot = None
    leaked_user_push = False
    leaked_owner = "default"
    leaked_channel = None
    leaked_client = None
    leaked_pusher = None
    leaked_device_id = ""
    leaked_mgmt_ip = ""
    was_awaiting = False
    req_user = _get_request_user(request) if request else "default"
    req_role = _get_request_role(request) if request else "admin"
    with _push_jobs_lock:
        job = _push_jobs.get(job_id)
        if job and request and not _is_job_owner_or_admin(request, job):
            _audit_event(
                action="push_delete_rejected", owner=req_user, role=req_role,
                job_id=job_id, result="forbidden",
                detail={"job_owner": job.get("owner", "")},
            )
            raise HTTPException(status_code=403, detail="Not your job")
        # Wave 6: if the job is being deleted while still holding scheduler
        # resources (e.g. abandoned dry-run), reclaim them here.
        if job is not None:
            leaked_sched_token = job.pop("_sched_token", None)
            leaked_push_slot = job.pop("_push_slot_handle", None)
            leaked_user_push = bool(job.pop("_user_push_reserved", False))
            leaked_owner = normalize_owner_lax(job.get("owner", "default"))
            leaked_device_id = job.get("device_id", "")
            leaked_mgmt_ip = job.get("mgmt_ip", "")
            was_awaiting = bool(job.get("awaiting_decision"))
            # Wave 7 addition: tear down held SSH resources too.
            leaked_channel = job.pop("_channel", None)
            leaked_client = job.pop("_client", None)
            leaked_pusher = job.pop("_pusher", None)
            job.pop("_live_output", None)
            job["awaiting_decision"] = False
    history = _load_push_history()
    for h in history:
        if h.get("job_id") == job_id:
            if request and not _is_job_owner_or_admin(request, h):
                _audit_event(
                    action="push_delete_rejected", owner=req_user,
                    role=req_role, job_id=job_id, result="forbidden",
                    detail={"job_owner": h.get("owner", "")},
                )
                raise HTTPException(status_code=403, detail="Not your job")
            break
    history = [h for h in history if h.get("job_id") != job_id]
    _save_push_history(history)
    with _push_jobs_lock:
        _push_jobs.pop(job_id, None)
    # Try a graceful abort on the held SSH channel so the device isn't
    # left with a half-parsed candidate config. Errors are swallowed --
    # delete must succeed even if the device is gone.
    try:
        if leaked_pusher and hasattr(leaked_pusher, "abort_held_session"):
            leaked_pusher.abort_held_session(leaked_channel, leaked_client)
        else:
            if leaked_channel:
                try:
                    leaked_channel.send("abort\n")
                except Exception:
                    pass
                try:
                    leaked_channel.close()
                except Exception:
                    pass
            if leaked_client:
                try:
                    leaked_client.close()
                except Exception:
                    pass
    except Exception:
        pass
    _device_scheduler.release(leaked_sched_token)
    _device_scheduler.release_global_push_slot(leaked_push_slot)
    if leaked_user_push:
        _device_scheduler.release_user_push(leaked_owner)
    _audit_event(
        action="push_delete", owner=leaked_owner, role=req_role,
        device_id=leaked_device_id, mgmt_ip=leaked_mgmt_ip,
        job_id=job_id, result="deleted",
        detail={"had_held_session": bool(leaked_channel),
                "was_awaiting_decision": was_awaiting,
                "by": req_user if req_user != leaked_owner else None},
    )
    return {"status": "deleted"}


@router.post("/api/operations/multihoming/compare")
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


@router.post("/api/operations/multihoming/sync")
def multihoming_sync(body: dict = None, request: Request = None):
    """Sync multihoming between two devices. Pushes config via ConfigPusher. Returns job_id."""
    body = body or {}
    device_ids = body.get("device_ids") or []
    if len(device_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 device_ids required")
    esi_prefix = body.get("esi_prefix", "00:11:22:33:44")
    redundancy_mode = body.get("redundancy_mode", "single-active")
    match_neighbor = body.get("match_neighbor", True)
    ssh_hosts = body.get("ssh_hosts") or {}
    try:
        src_ssh = ssh_hosts.get(device_ids[0], "")
        tgt_ssh = ssh_hosts.get(device_ids[1], "")
        mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(device_ids[0], src_ssh)
        config = _get_cached_config(scaler_id)
        if not config:
            user, password = _get_credentials()
            config = _fetch_config_via_ssh(scaler_id, mgmt_ip, user, password)
        from scaler.wizard.parsers import parse_existing_multihoming
        mh = parse_existing_multihoming(config or "")
        if not mh:
            raise HTTPException(status_code=400, detail="No multihoming config on first device to sync")
        lines = ["network-services", "  multihoming"]
        for iface, esi in (mh.items() if isinstance(mh, dict) else []):
            lines.append(f"    interface {iface}")
            lines.append(f"      esi arbitrary value {esi}")
            if redundancy_mode == "all-active":
                lines.append(f"      redundancy-mode all-active")
            lines.append(f"    !")
        lines.append("  !")
        lines.append("!")
        config_text = "\n".join(lines)
        import uuid
        from datetime import datetime
        owner = _get_request_user(request) if request else "default"
        job_id = str(uuid.uuid4())
        with _push_jobs_lock:
            _push_jobs[job_id] = {
                "job_id": job_id, "owner": owner,
                "status": "pending", "phase": "starting", "message": "",
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
        from routes._state import app_user_context
        from routes._worker_pool import submit_push
        def _run_with_user():
            with app_user_context(owner):
                _run()
        submit_push(_run_with_user)
        return {"job_id": job_id, "status": "started"}
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"Multihoming sync unavailable: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/api/operations/stag-check")
def stag_check(body: dict):
    """Check QinQ Stag pool usage on devices."""
    device_ids = body.get("device_ids", [])
    if not device_ids:
        raise HTTPException(status_code=400, detail="device_ids required")

    results = []
    for did in device_ids:
        dev_ctx = _get_device_context(did)
        hostname = dev_ctx.get("hostname", did)
        ssh_host = dev_ctx.get("ssh_host") or dev_ctx.get("ip", "")
        if not ssh_host:
            results.append({
                "device_id": did, "hostname": hostname,
                "total_stags": 0, "limit": 4000, "percentage": 0,
                "exceeded": False, "at_risk": False,
                "error": "No SSH host configured"
            })
            continue
        try:
            from scaler.stag_pool_checker import check_pool_status
            user, password = _get_credentials()
            status = check_pool_status(ssh_host, user, password)
            stag_pool = None
            for pool in (status.pools if hasattr(status, 'pools') else []):
                if 'stag' in pool.name.lower():
                    stag_pool = pool
                    break
            if stag_pool:
                pct = round(stag_pool.usage_percent, 1)
                results.append({
                    "device_id": did, "hostname": hostname,
                    "total_stags": stag_pool.used,
                    "limit": stag_pool.max_capacity,
                    "percentage": pct,
                    "exceeded": pct >= 100,
                    "at_risk": 80 <= pct < 100,
                })
            else:
                results.append({
                    "device_id": did, "hostname": hostname,
                    "total_stags": 0, "limit": 4000, "percentage": 0,
                    "exceeded": False, "at_risk": False,
                    "error": "Stag pool not found in device response"
                })
        except Exception as e:
            results.append({
                "device_id": did, "hostname": hostname,
                "total_stags": 0, "limit": 4000, "percentage": 0,
                "exceeded": False, "at_risk": False,
                "error": str(e)
            })

    return {"devices": results}


@router.post("/api/operations/scale-updown")
def scale_updown(body: dict = None, request: Request = None):
    """Scale up or down services. Uses scale_operations for parsing and analysis."""
    import uuid
    import threading
    body = body or {}
    device_ids = body.get("device_ids") or []
    operation = body.get("operation", "down")
    service_type = body.get("service_type", "fxc")
    range_spec = body.get("range_spec") or "last 100"
    include_interfaces = body.get("include_interfaces", True)
    dry_run = body.get("dry_run", True)
    if not device_ids:
        raise HTTPException(status_code=400, detail="device_ids required")
    if operation not in ("up", "down"):
        raise HTTPException(status_code=400, detail="operation must be 'up' or 'down'")
    valid_types = ["fxc", "l2vpn", "evpn", "vpws", "vrf", "flowspec-vpn"]
    if service_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"service_type must be one of {valid_types}")
    owner = _get_request_user(request) if request else "default"
    job_id = str(uuid.uuid4())[:8]
    with _push_jobs_lock:
        _push_jobs[job_id] = {
            "job_id": job_id,
            "owner": owner,
            "status": "pending",
            "phase": "starting",
            "message": "Analyzing...",
            "percent": 0,
            "success": False,
            "done": False,
            "terminal_lines": [],
            "terminal_cursor": 0,
            "job_name": f"Scale {operation} {service_type}",
        }

    def _run():
        try:
            from scaler.wizard.scale_operations import parse_services_from_config, parse_range_spec
            all_services = []
            all_interfaces = []
            with _push_jobs_lock:
                _push_jobs[job_id].update(percent=10, message="Parsing services...", status="running")
                _push_jobs[job_id]["terminal_lines"].append(f"> Operation: scale {operation}")
                _push_jobs[job_id]["terminal_lines"].append(f"> Service type: {service_type}")
                _push_jobs[job_id]["terminal_lines"].append(f"> Range: {range_spec}")
            for device_id in device_ids:
                config = _get_cached_config(device_id)
                if not config:
                    with _push_jobs_lock:
                        _push_jobs[job_id]["terminal_lines"].append(f"> [WARN] No cached config for {device_id}")
                    continue
                try:
                    services = parse_services_from_config(config)
                    svc_list = services.get(service_type, [])
                    if svc_list:
                        max_num = max(s.service_number for s in svc_list)
                        target_nums = parse_range_spec(range_spec, max_num)
                        for svc in svc_list:
                            if svc.service_number in target_nums:
                                all_services.append(svc.service_name)
                                if include_interfaces:
                                    all_interfaces.extend(svc.interfaces)
                except Exception as e:
                    with _push_jobs_lock:
                        _push_jobs[job_id]["terminal_lines"].append(f"> [ERROR] {device_id}: {str(e)}")
            with _push_jobs_lock:
                _push_jobs[job_id].update(percent=40, message=f"Found {len(all_services)} services")
                _push_jobs[job_id]["terminal_lines"].append(f"> Services affected: {len(all_services)}")
                _push_jobs[job_id]["terminal_lines"].append(f"> Interfaces affected: {len(all_interfaces)}")
            if dry_run:
                with _push_jobs_lock:
                    _push_jobs[job_id].update(
                        percent=100, message="Dry run complete", status="completed",
                        success=True, done=True
                    )
                    _push_jobs[job_id]["terminal_lines"].append("> Dry run - no changes applied")
            else:
                if operation == "down":
                    with _push_jobs_lock:
                        _push_jobs[job_id].update(percent=60, message="Scale down - use scaler-wizard for full apply")
                    with _push_jobs_lock:
                        _push_jobs[job_id].update(
                            percent=100, message=f"Would delete {len(all_services)} services",
                            status="completed", success=True, done=True
                        )
                        _push_jobs[job_id]["terminal_lines"].append("> Scale down: use scaler-wizard CLI for full apply")
                else:
                    with _push_jobs_lock:
                        _push_jobs[job_id].update(
                            percent=100, message="Scale up: use scaler-wizard CLI",
                            status="completed", success=True, done=True
                        )
                        _push_jobs[job_id]["terminal_lines"].append("> Scale up: use scaler-wizard CLI for interactive flow")
            _persist_job_if_done(job_id)
        except Exception as e:
            with _push_jobs_lock:
                if job_id in _push_jobs:
                    _push_jobs[job_id].update(
                        success=False, message=str(e), status="failed", done=True, percent=100
                    )
                    _push_jobs[job_id]["terminal_lines"].append(f"> [ERROR] {str(e)}")
            _persist_job_if_done(job_id)

    from routes._worker_pool import submit_push
    submit_push(_run)
    return {"job_id": job_id, "status": "started", "message": f"Scale {operation} started"}

