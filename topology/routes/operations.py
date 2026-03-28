"""Scaler bridge routes: operations."""
from __future__ import annotations

import asyncio
import json
import threading
import time
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from routes.bridge_helpers import (
    _ACTIVE_BUILDS_PATH, _ACTIVE_UPGRADES_PATH, _INTERNAL_JOB_KEYS,
    _MAX_HISTORY_JOBS, _MAX_TERMINAL_LINES_IN_HISTORY, _PUSH_HISTORY_PATH,
    _build_job_name, _evict_stale_jobs_locked, _fetch_config_via_ssh,
    _get_cached_config, _get_credentials, _get_device_context, _iso_from_ts,
    _load_push_history, _persist_job_if_done, _remove_active_build,
    _remove_active_upgrade, _resolve_mgmt_ip, _sanitize_job, _save_active_build,
    _save_active_upgrade, _save_push_history,
)
from routes._state import _push_jobs, _push_jobs_lock

router = APIRouter()

@router.post("/api/operations/delete-hierarchy")
def delete_hierarchy_op(body: dict = None):
    """Delete a config hierarchy from a device. dry_run=True for preview only."""
    body = body or {}
    device_id = body.get("device_id")
    hierarchy = body.get("hierarchy")
    dry_run = bool(body.get("dry_run", True))
    ssh_host = body.get("ssh_host", "")
    sub_path = body.get("sub_path", "").strip()
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
    push_method = (body.get("push_method") or "terminal_paste").lower()
    load_mode = (body.get("load_mode") or "merge").lower()
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
            "_cancel_requested": False,
            "push_method": push_method,
            "load_mode": load_mode,
            "estimated_total_seconds": None,
        }

    def _cancel_check():
        with _push_jobs_lock:
            return _push_jobs.get(job_id, {}).get("_cancel_requested", False)

    def _run_push():
        import time as _time
        start_time = _time.time()
        try:
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
                            _push_jobs[job_id]["check_passed"] = True
                            _push_jobs[job_id]["_channel"] = channel
                            _push_jobs[job_id]["_client"] = client
                            _push_jobs[job_id]["_pusher"] = pusher
                            _push_jobs[job_id]["_live_output"] = _live_output
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


@router.get("/api/config/push/progress/{job_id}")
def push_progress(job_id: str):
    """SSE stream for push progress. Includes terminal lines for live display."""
    from fastapi.responses import StreamingResponse
    import asyncio
    import json

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


@router.post("/api/operations/push/{job_id}/cancel")
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
def list_jobs():
    """List all jobs: active (in-memory) and recent (from disk)."""
    with _push_jobs_lock:
        active = [_sanitize_job(j) for j in _push_jobs.values()]
    history = _load_push_history()
    seen = {j["job_id"] for j in active}
    for h in history:
        if h.get("job_id") not in seen:
            active.append(h)
            seen.add(h.get("job_id"))
    active.sort(key=lambda x: x.get("started_at", ""), reverse=True)
    return {"jobs": active[: _MAX_HISTORY_JOBS + 20]}


@router.get("/api/operations/jobs/{job_id}")
def get_job(job_id: str):
    """Get full job state including terminal output."""
    with _push_jobs_lock:
        job = _push_jobs.get(job_id)
    if job:
        return _sanitize_job(job)
    for h in _load_push_history():
        if h.get("job_id") == job_id:
            return h
    raise HTTPException(status_code=404, detail="Job not found")


@router.post("/api/operations/jobs/{job_id}/retry")
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


@router.delete("/api/operations/jobs/{job_id}")
def delete_job(job_id: str):
    """Remove job from history."""
    history = _load_push_history()
    history = [h for h in history if h.get("job_id") != job_id]
    _save_push_history(history)
    with _push_jobs_lock:
        _push_jobs.pop(job_id, None)
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
def multihoming_sync(body: dict = None):
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
def scale_updown(body: dict = None):
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
    job_id = str(uuid.uuid4())[:8]
    with _push_jobs_lock:
        _push_jobs[job_id] = {
            "job_id": job_id,
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

    threading.Thread(target=_run, daemon=True).start()
    return {"job_id": job_id, "status": "started", "message": f"Scale {operation} started"}

