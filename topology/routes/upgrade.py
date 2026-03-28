"""Scaler bridge routes: upgrade."""
from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from routes.bridge_helpers import (
    SCALER_ROOT, _ACTIVE_BUILDS_PATH, _ACTIVE_UPGRADES_PATH, _get_credentials,
    _persist_job_if_done, _remove_active_build, _remove_active_upgrade,
    _resolve_config_dir, _resolve_mgmt_ip, _save_active_build,
    _save_active_upgrade,
)
from routes._state import _push_jobs, _push_jobs_lock

router = APIRouter()

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
    if not current_version or not target_version:
        raise HTTPException(status_code=400, detail="current_version and target_version are required")
    try:
        from scaler.stack_manager import StackManager
        is_switch, cur_br, tgt_br = StackManager.detect_branch_switch(current_version, target_version)
        requires_delete_deploy = StackManager.requires_delete_deploy(current_version, target_version)
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

                upgrade_type = "normal"
                reason = ""
                warnings = []

                if mode == "RECOVERY":
                    upgrade_type = "blocked"
                    reason = "Device in RECOVERY mode -- restore first"
                    warnings.append("Cannot upgrade from RECOVERY")
                elif mode == "GI":
                    upgrade_type = "gi_deploy"
                    reason = "Device in GI mode -- deploy flow"
                    warnings.append("GI mode requires deploy flow")
                elif mode == "DNOS" and current_version and target_version and target_version != "0.0.0":
                    cv = re.match(r"(\d+\.\d+\.\d+\.\d+)", current_version)
                    tv = re.match(r"(\d+\.\d+\.\d+\.\d+)", target_version)
                    if cv and tv and cv.group(1) == tv.group(1):
                        upgrade_type = "skip"
                        reason = f"Already at target version ({cv.group(1)})"
                elif current_version:
                    requires_dd = StackManager.requires_delete_deploy(current_version, target_version)
                    if requires_dd:
                        upgrade_type = "delete_deploy"
                        cur_maj, _ = StackManager.extract_major_version(current_version)
                        tgt_maj, _ = StackManager.extract_major_version(target_version)
                        reason = f"Major version change ({cur_maj} -> {tgt_maj})"
                        warnings.append("Major version jump requires delete+deploy")
                    else:
                        reason = "Same major version -- normal upgrade"
                else:
                    reason = "Unknown current version -- assuming normal"
                    warnings.append("Could not detect current DNOS version")

                result_item = {
                    "mode": mode,
                    "current_version": current_version or "-",
                    "target_version": target_version,
                    "upgrade_type": upgrade_type,
                    "reason": reason,
                    "components": ["DNOS", "GI", "BaseOS"],
                    "warnings": warnings,
                }

                if upgrade_type in ("delete_deploy", "gi_deploy"):
                    dp = {"system_type": "", "deploy_name": scaler_id or did, "ncc_id": 0}
                    try:
                        _opf = Path(SCALER_ROOT) / "db" / "configs" / (scaler_id or did) / "operational.json"
                        if _opf.exists():
                            with open(_opf) as f:
                                _opd = json.load(f)
                            dp["system_type"] = _opd.get("system_type") or _opd.get("deploy_system_type") or ""
                            dp["deploy_name"] = _opd.get("deploy_name") or (scaler_id or did)
                            dp["ncc_id"] = int(_opd.get("deploy_ncc_id") or _opd.get("ncc_id") or 0)
                    except Exception:
                        pass
                    result_item["deploy_params"] = dp

                # --- Cluster preflight: check NCC VMs on KVM host ---
                _sys_type = result_item.get("deploy_params", {}).get("system_type", "")
                if not _sys_type:
                    try:
                        _opf2 = Path(SCALER_ROOT) / "db" / "configs" / (scaler_id or did) / "operational.json"
                        if _opf2.exists():
                            _sys_type = json.loads(_opf2.read_text()).get("system_type", "")
                    except Exception:
                        pass
                is_cluster = _sys_type.upper().startswith("CL-")
                if is_cluster:
                    result_item["is_cluster"] = True
                    result_item["system_type"] = _sys_type
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
                        devices[did] = {
                            "mode": "?", "current_version": "-",
                            "target_version": target_version,
                            "upgrade_type": "normal",
                            "reason": f"SSH check failed: {exc}",
                            "components": ["DNOS", "GI", "BaseOS"],
                            "warnings": [str(exc)],
                        }
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
def image_upgrade_execute(body: dict):
    """Execute image upgrade on devices. Supports per-device plans and parallel execution."""
    import uuid
    import threading
    from datetime import datetime
    from concurrent.futures import ThreadPoolExecutor, as_completed

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

    with _push_jobs_lock:
        _push_jobs[job_id] = {
            "job_id": job_id,
            "job_type": "upgrade",
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
            "started_at": datetime.utcnow().isoformat() + "Z",
            "estimated_total_seconds": initial_est,
        }

    def _run_upgrade():
        runnable = [d for d in device_ids if device_state.get(d, {}).get("status") == "pending"]
        if not runnable:
            _finalize_upgrade_job(job_id, device_ids)
            return

        def _do_one(did):
            plan = device_plans.get(did, {})
            up_type = plan.get("upgrade_type", upgrade_type)
            comps = plan.get("components", components)
            comps_upper = {x.upper() for x in comps}
            dev_url_list = [(c, u) for c, u in url_list if c.upper() in comps_upper]
            ssh_host = ssh_hosts.get(did, "") if isinstance(ssh_hosts, dict) else ""
            mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(did, ssh_host)
            deploy_params = plan.get("deploy_params", {})
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
                            _push_jobs[job_id]["terminal_lines"].append(f"[ERROR] {did}: {e}")

        _finalize_upgrade_job(job_id, device_ids)

    _save_active_upgrade(job_id, _push_jobs[job_id])

    t = threading.Thread(target=_run_upgrade, daemon=True)
    t.start()

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
def image_upgrade_trigger_build(body: dict):
    """Trigger a Jenkins build and start backend monitoring.

    Accepts optional device_ids + ssh_hosts for auto-push after build succeeds.
    The monitor thread polls Jenkins every 30s, updates a _push_jobs entry so
    the existing job watcher on the frontend sees it automatically.
    """
    import uuid
    import threading
    from datetime import datetime

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

    t = threading.Thread(target=_monitor_build, daemon=True)
    t.start()
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
    """Push resolved images to devices. Supports per-device plans and parallel execution."""
    from datetime import datetime
    from concurrent.futures import ThreadPoolExecutor, as_completed

    device_plans = device_plans or {}
    max_concurrent = max(1, min(max_concurrent, 10))

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
                f"[INFO] Starting upgrade push to {len(device_ids)} device(s) ({url_names})")
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
        plan = device_plans.get(did, {})
        up_type = plan.get("upgrade_type", "normal")
        comps = plan.get("components", components)
        comps_upper = {x.upper() for x in comps}
        dev_url_list = [(c, u) for c, u in url_list if c.upper() in comps_upper]
        ssh_host = ssh_hosts.get(did, "") if isinstance(ssh_hosts, dict) else ""
        mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(did, ssh_host)
        deploy_params = plan.get("deploy_params", {})
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
                        _push_jobs[job_id]["terminal_lines"].append(f"[ERROR] {did}: {e}")

    _finalize_upgrade_job(job_id, device_ids)


def _update_device_state(job_id: str, device_id: str, **kwargs):
    """Thread-safe update of per-device state."""
    with _push_jobs_lock:
        if job_id in _push_jobs:
            ds = _push_jobs[job_id].get("device_state", {})
            if device_id in ds:
                ds[device_id].update(kwargs)


class _UpgradeCancelled(Exception):
    """Raised when an upgrade job is cancelled by the user."""
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
    # --- Auto-detect device mode from operational.json ---
    # If upgrade_type is "normal" but device is actually in GI mode,
    # switch to gi_deploy so we use the correct flow (deploy instead of install).
    _op_data_cached = {}
    try:
        _dp_dir = _resolve_config_dir(scaler_hostname)
        _dp_path = Path(SCALER_ROOT) / "db" / "configs" / _dp_dir / "operational.json"
        if _dp_path.exists():
            _op_data_cached = json.loads(_dp_path.read_text())
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
        if _classified == "GI":
            upgrade_type = "gi_deploy"
        elif _classified == "RECOVERY":
            upgrade_type = "gi_deploy"
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
    # --- Fill deploy_params from operational.json ---
    if not deploy_params.get("system_type") and _op_data_cached:
        deploy_params["system_type"] = (
            _op_data_cached.get("system_type")
            or _op_data_cached.get("deploy_system_type")
            or ""
        )
    if upgrade_type in ("gi_deploy", "delete_deploy") and _op_data_cached:
        if not deploy_params.get("deploy_name"):
            raw_name = _op_data_cached.get("deploy_name") or scaler_hostname
            deploy_params["deploy_name"] = raw_name.rstrip(",").strip()
        if "ncc_id" not in deploy_params:
            deploy_params["ncc_id"] = int(
                _op_data_cached.get("deploy_ncc_id")
                or _op_data_cached.get("ncc_id")
                or 0
            )
    # Final safety: deploy_name must be clean (no trailing commas/whitespace)
    if deploy_params.get("deploy_name"):
        deploy_params["deploy_name"] = deploy_params["deploy_name"].rstrip(",").strip()
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

    try:
        from scaler.config_pusher import get_upgrade_time_estimate
        est = get_upgrade_time_estimate(
            upgrade_type=upgrade_type,
            components=components,
            device_mode=device_mode,
            device_hostname=device_id,
        )
        est_seconds = est.get("total", 180)
        est_source = est.get("source", "default")
        est_confidence = est.get("confidence", "low")
        with _push_jobs_lock:
            if job_id in _push_jobs:
                prev_est = _push_jobs[job_id].get("estimated_total_seconds")
                if prev_est is None:
                    _push_jobs[job_id]["estimated_total_seconds"] = est_seconds
                _push_jobs[job_id]["terminal_lines"].append(
                    f"[INFO] {device_id}: Estimated time: {int(est_seconds)}s ({est_source}, {est_confidence} confidence)")
    except Exception:
        est_seconds = 180

    _update_device_state(job_id, device_id, status="running", phase="connecting",
                         message="Connecting...", started_at=datetime.utcnow().isoformat() + "Z")

    # Sync KVM cluster config from console_mappings into operational.json
    # so connect_for_upgrade has all connection paths available during upgrade
    try:
        from pathlib import Path
        import json as _json
        from scaler.connection_strategy import get_console_config_for_device, _load_console_mappings
        mappings = _load_console_mappings()
        ncc_info = mappings.get('cluster_ncc_access', {}).get(scaler_hostname)
        if ncc_info and ncc_info.get('ncc_type') == 'kvm':
            op_file = Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname / "operational.json"
            op_file.parent.mkdir(parents=True, exist_ok=True)
            op_data = {}
            if op_file.exists():
                try:
                    op_data = _json.loads(op_file.read_text())
                except Exception:
                    pass
            changed = False
            if not op_data.get('ncc_type'):
                op_data['ncc_type'] = ncc_info.get('ncc_type')
                op_data['kvm_host'] = ncc_info.get('kvm_host')
                op_data['kvm_host_ip'] = ncc_info.get('kvm_host_ip')
                op_data['kvm_host_credentials'] = ncc_info.get('kvm_host_credentials', {})
                op_data['ncc_vms'] = ncc_info.get('ncc_vms', [])
                op_data['ncc_console_credentials'] = ncc_info.get('ncc_console_credentials', {})
                op_data['dncli_credentials'] = ncc_info.get('dncli_credentials', {})
                changed = True
            if not op_data.get('ncc_mgmt_ip'):
                _vip = (ncc_info.get('mgmt_vip') or '').strip()
                _ssh = (op_data.get('ssh_host') or '').strip().split('/')[0]
                op_data['ncc_mgmt_ip'] = _vip or _ssh or ''
                if op_data['ncc_mgmt_ip']:
                    changed = True
            if changed:
                op_file.write_text(_json.dumps(op_data, indent=4))
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
                _merged.update(json.loads(_op_r.read_text()))
        _op_data_cached = _merged
    except Exception:
        pass

    def _log(level, msg):
        with _push_jobs_lock:
            if job_id in _push_jobs:
                _push_jobs[job_id]["terminal_lines"].append(f"[{level}] {device_id}: {msg}")

    _log("INFO", f"upgrade_type={upgrade_type}, system_type={deploy_params.get('system_type','?')}, "
         f"deploy_name={deploy_params.get('deploy_name','?')}, ncc_id={deploy_params.get('ncc_id','?')}")

    success = False
    _update_operational_after_upgrade(scaler_hostname or device_id, "UPGRADING", success=False)
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
            _is_cluster = (_op_data_cached.get("ncc_type") or "").lower() == "kvm"
            if _is_cluster:
                _check_upgrade_cancel(job_id)
                _log("INFO", "KVM cluster -- using connect_for_upgrade for runtime mode detection")
                os.chdir(SCALER_ROOT)
                from scaler.connection_strategy import connect_for_upgrade
                conn = connect_for_upgrade(scaler_hostname, timeout=120)
                if not conn.get("connected"):
                    raise RuntimeError(
                        f"Cannot connect to {device_id}: {conn.get('abort_reason', 'unknown')}"
                    )
                _runtime_state = (conn.get("device_state") or "").upper()
                _runtime_method = conn.get("method", "?")
                _log("INFO", f"Runtime mode: {_runtime_state} (via {_runtime_method})")
                if _runtime_state == "GI" or _runtime_state == "BASEOS_SHELL":
                    _log("WARN", f"Device is in {_runtime_state} -- switching to gi_deploy flow")
                    upgrade_type = "gi_deploy"
                    if not deploy_params.get("system_type"):
                        deploy_params["system_type"] = (
                            _op_data_cached.get("system_type")
                            or _op_data_cached.get("deploy_system_type")
                            or ""
                        )
                        deploy_params["deploy_name"] = (
                            _op_data_cached.get("deploy_name") or scaler_hostname
                        ).rstrip(",").strip()
                        if "ncc_id" not in deploy_params:
                            deploy_params["ncc_id"] = int(
                                _op_data_cached.get("deploy_ncc_id")
                                or _op_data_cached.get("ncc_id")
                                or conn.get("ncc_id") or 0
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
            else:
                _run_normal_upgrade(job_id, device_id, mgmt_ip, user, password,
                                    url_list, stage_times, _log)

        success = True
        total_elapsed = round(time.time() - t_start, 1)
        _update_device_state(job_id, device_id, status="completed", phase="done", percent=100,
                             message=f"Upgrade complete ({total_elapsed}s)", completed_at=datetime.utcnow().isoformat() + "Z")
        _log("OK", f"upgrade complete in {total_elapsed}s")
        _update_operational_after_upgrade(scaler_hostname or device_id, "DNOS", success=True)
    except _UpgradeCancelled:
        total_elapsed = round(time.time() - t_start, 1)
        _log("WARN", f"Upgrade cancelled by user after {total_elapsed}s")
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
        data = json.loads(ops_path.read_text())
        if state == "UPGRADING":
            data["device_state"] = "UPGRADING"
            data["upgrade_in_progress"] = True
            data["install_status"] = "IN_PROGRESS"
            data["install_start"] = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif success:
            data["device_state"] = state
            data["upgrade_in_progress"] = False
            data["install_status"] = "COMPLETED"
            data["install_finish"] = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        ops_path.write_text(json.dumps(data, indent=2))
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


def _send_deploy_command(chan, sys_type, d_name, ncc_id, _log):
    """Send 'request system deploy' with rapid confirmation-prompt handling and
    NCC-ID mismatch retry.

    Polls every 0.5s for the (yes/no) prompt and answers immediately.
    Returns (deploy_out, final_ncc_id).  Raises on hard errors.
    Socket-close after deploy is EXPECTED (device reboots).
    """
    import time, re

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

    def _send_and_poll_confirm(cmd, tag=""):
        """Send command, poll rapidly for confirmation/error/prompt. Return output."""
        chan.send(cmd.encode() + b"\n")
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
    _log("INFO", f"Deploying: {deploy_cmd}")

    deploy_out, conn_closed = _send_and_poll_confirm(deploy_cmd)
    if conn_closed:
        return (deploy_out, ncc_id)

    lo = deploy_out.lower()

    if "doesn't match" in lo or "auto detected" in lo:
        ncc_id = 1 - ncc_id
        deploy_cmd = f"request system deploy system-type {sys_type} name {d_name} ncc-id {ncc_id}"
        _log("INFO", f"NCC mismatch, retrying with ncc-id {ncc_id}: {deploy_cmd}")
        deploy_out, conn_closed = _send_and_poll_confirm(deploy_cmd, " (NCC retry)")
        if conn_closed:
            return (deploy_out, ncc_id)

    if "error" in deploy_out.lower():
        _log("WARN", f"Deploy output: {deploy_out[:300]}")

    return (deploy_out, ncc_id)


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


def _load_images_on_channel(job_id, device_id, chan, url_list, stage_times, _log, pct_base=10, pct_range=50):
    """Load image URLs via target-stack load on an existing shell channel.

    Pre-checks target-stack to skip already-loaded images.
    Accumulates ALL output, checks for errors, confirms 100% completion,
    and verifies via 'show system target-stack' after loading.
    """
    import time
    import re

    # Pre-check: see what's already in target-stack to skip duplicates
    already_loaded = set()
    try:
        _update_device_state(job_id, device_id, phase="check-target-stack", percent=pct_base,
                             message="Checking existing target-stack...")
        while chan.recv_ready():
            chan.recv(65535)
            time.sleep(0.1)
        _sw = _make_send_wait(chan)
        ts_out = _sw("show system stack | no-more", 5)
        ts_clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', ts_out)
        for line in ts_clean.split('\n'):
            upper = line.upper()
            for comp_name_check, url_check in url_list:
                if comp_name_check.upper() in upper:
                    # Try 3-segment version (DNOS/GI: 26.2.0.20_...)
                    ver_from_url = re.search(r'(\d+\.\d+\.\d+[\d._]*)', url_check)
                    if not ver_from_url:
                        # Fallback: 2-segment version (BASEOS: 2.2620259015)
                        ver_from_url = re.search(r'(\d+\.\d{5,})', url_check)
                    if ver_from_url and ver_from_url.group(1) in line:
                        already_loaded.add(comp_name_check.upper())
                        _log("OK", f"{comp_name_check} already in target-stack (version match) -- skipping load")
                    elif not ver_from_url:
                        # Last resort: extract filename stem and check Target column
                        fname = re.search(r'drivenets_\w+_([\d._]+\w*)\.tar', url_check)
                        if fname and fname.group(1) in line:
                            already_loaded.add(comp_name_check.upper())
                            _log("OK", f"{comp_name_check} already in target-stack (filename match) -- skipping load")
        if already_loaded:
            _log("INFO", f"Pre-loaded components: {', '.join(sorted(already_loaded))}")
    except Exception as pre_err:
        _log("WARN", f"Target-stack pre-check failed: {pre_err} -- loading all images")

    actual_url_list = [(c, u) for c, u in url_list if c.upper() not in already_loaded]
    if not actual_url_list:
        _log("OK", "All images already in target-stack -- no loading needed")
        return

    _sw = _make_send_wait(chan)

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
        chan.send(f"request system target-stack load {load_url}\n")
        time.sleep(3)
        buf = ""
        answered_yes = False
        for _ in range(40):
            if chan.recv_ready():
                buf += chan.recv(65535).decode("utf-8", errors="replace")
            bl = buf.lower()
            if not answered_yes and ("continue?" in bl or "(yes/no)" in bl or "overwrite" in bl):
                chan.send("yes\n")
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
            load_out = _sw("show system target-stack load | no-more", 5)
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
            stack_out = _sw("show system stack | no-more", 4)
        except Exception:
            return load_clean, 0, "idle"
        stack_clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', stack_out)
        for line in stack_clean.split('\n'):
            if '|' not in line or '---' in line:
                continue
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 6 and comp_name_upper and comp_name_upper in parts[0].upper():
                target_ver = parts[5] if len(parts) > 5 else ""
                if target_ver and target_ver != "-":
                    ver_from_url = re.search(r'(\d+\.\d+\.\d+[\d._]*)', comp_url) if comp_url else None
                    if ver_from_url and ver_from_url.group(1) in target_ver:
                        return stack_clean, 100, "complete"
                    elif target_ver.strip():
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

        for load_attempt in range(1, max_retries + 2):
            _check_upgrade_cancel(job_id)
            if load_attempt > 1:
                _log("INFO", f"Retrying {comp_name} load (attempt {load_attempt}/{max_retries + 1})...")
                time.sleep(10)

            send_out = _send_load_cmd(url)
            send_lower = send_out.lower()
            # Detect errors -- 404, timeout, connection refused, download failure
            _has_error = ("error" in send_lower and "downloading" not in send_lower)
            _has_fail = any(kw in send_lower for kw in ("timed out", "not found", "failed", "refused", "404"))
            if _has_error or _has_fail:
                if "upgrade in progress" in send_lower:
                    _log("INFO", f"{comp_name}: upgrade in progress, waiting 15s...")
                    time.sleep(15)
                    continue
                clean_out = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', send_out).strip()[:200]
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
                    load_error = out_clean[:200]
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
                                load_error = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', recheck).strip()[:200]
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
        verify_out = _sw("show system stack | no-more", 5)
        clean_verify = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', verify_out)

        expected_names = {name.upper() for name, _ in url_list}
        found = set()
        for line in clean_verify.split('\n'):
            if '|' not in line or '---' in line:
                continue
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) < 6:
                continue
            comp = parts[0].upper()
            target_ver = parts[5] if len(parts) > 5 else ""
            for name in expected_names:
                if name in comp and target_ver and target_ver != "-":
                    found.add(name)

        if found:
            _log("OK", f"Target-stack verified: {', '.join(sorted(found))} present")
        else:
            _log("WARN", f"Target-stack verification unclear -- "
                         f"expected {expected_names}, output: {clean_verify[:300]}")
    except Exception as ve:
        _log("WARN", f"Target-stack verify failed: {ve}")


def _send_install_command(chan, _log):
    """Send 'request system target-stack install' with yes/no prompt handling.

    Polls every 0.5s for the confirmation prompt and answers 'yes' immediately.
    Returns install output text.  Socket-close after install is EXPECTED (device reboots).
    """
    import time, re

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

    cmd = "request system target-stack install"
    _log("INFO", f"Sending: {cmd}")
    chan.send(cmd.encode() + b"\n")
    buf = b""
    confirmed = False
    for _ in range(120):
        time.sleep(0.5)
        try:
            if chan.recv_ready():
                buf += chan.recv(65535)
        except (OSError, EOFError) as e:
            es = str(e).lower()
            if "socket" in es or "eof" in es or "closed" in es:
                _log("OK", "Install command sent -- device rebooting (connection closed as expected)")
                return buf.decode("utf-8", errors="replace")
            raise
        text = buf.decode("utf-8", errors="replace")
        lo = text.lower()
        if not confirmed and ("yes/no" in lo or "y/n" in lo or "do you want" in lo or "continue" in lo):
            _log("INFO", "Install confirmation prompt detected -- answering 'yes'")
            chan.send(b"yes\n")
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
                break
    return buf.decode("utf-8", errors="replace")


def _post_install_verify(job_id, device_id, mgmt_ip, user, password,
                          url_list, stage_times, _log, was_cluster=False,
                          verify_timeout=600, check_interval=20):
    """After target-stack install, wait for device to reboot and verify new images.

    Reconnects via SSH, runs 'show system install' and checks that installed
    package versions match the target URLs.  Logs PASS/FAIL but does not raise
    (the install was already sent; this is observational).
    """
    import time

    _update_device_state(job_id, device_id, phase="post-install-verify", percent=90,
                         message="Waiting for device to come back after install...")
    _log("INFO", f"Post-install verification (timeout {verify_timeout}s)")

    t_phase = time.time()
    time.sleep(60)

    start = time.time()
    verified = False
    while time.time() - start < verify_timeout:
        elapsed = int(time.time() - start)
        _update_device_state(job_id, device_id, phase="post-install-verify",
                             percent=90 + min(elapsed // 30, 8),
                             message=f"Reconnecting after install... ({elapsed}s)")
        try:
            cli, ch = _ssh_connect_basic(mgmt_ip, user, password)
            sw = _make_send_wait(ch)
            out = sw("show system install | no-more", 5)
            clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', out)
            _log("INFO", f"Post-install 'show system install':\n{clean[:600]}")

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
                _log("WARN", f"{matches}/{len(expected)} components verified after install")
                verified = True
            else:
                _log("WARN", "No target versions found in post-install output -- install may have failed")

            try:
                cli.close()
            except Exception:
                pass
            break
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
                f"cannot use 'request system install'. "
                f"Need gi_deploy flow with 'request system deploy'.")

        pre_upgrade_config = ""
        try:
            t_phase = time.time()
            _update_device_state(job_id, device_id, phase="snapshot", percent=5)
            pre_upgrade_config = _send_wait("show config running | no-more", 3)
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
            _log("WARN", f"Pre-check output: {pre_out[:200]}")

        t_phase = time.time()
        _update_device_state(job_id, device_id, phase="install", percent=85)
        _log("INFO", "Installing (device will reboot)...")
        install_out = _send_install_command(chan, _log)
        stage_times["install"] = round(time.time() - t_phase, 1)
        clean_out = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', install_out[:400])
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

    # Phase 1: Connect via connect_for_upgrade (handles SSH/console/virsh)
    t_phase = time.time()
    _update_device_state(job_id, device_id, phase="connecting", percent=2,
                         message="Connecting to device...")

    os.chdir(SCALER_ROOT)
    from scaler.connection_strategy import connect_for_upgrade
    conn = connect_for_upgrade(scaler_hostname, timeout=60)

    if not conn["connected"]:
        raise RuntimeError(f"Cannot connect to {scaler_hostname}: {conn.get('abort_reason', 'unknown')}")

    client = conn["ssh"]
    chan = conn["channel"]
    conn_method = conn.get("method", "unknown")
    conn_state = conn.get("device_state", "")
    _log("INFO", f"Connected via {conn_method} (state={conn_state})")

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
                                    pct_base=35, pct_range=40)
            try:
                _sw_pre = _make_send_wait(chan)
                sv = _sw_pre("show system stack | no-more", 4)
                sc = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', sv)
                _log("INFO", f"Pre-deploy stack:\n{sc[:500]}")
                loaded_comps = set()
                for _line in sc.split('\n'):
                    if '|' not in _line or '---' in _line:
                        continue
                    _parts = [p.strip() for p in _line.split('|') if p.strip()]
                    if len(_parts) >= 6:
                        _tv = _parts[5] if len(_parts) > 5 else ""
                        if _tv and _tv != "-":
                            loaded_comps.add(_parts[0].upper())
                expected_comps = {c.upper() for c, u in url_list if u}
                missing_comps = expected_comps - loaded_comps
                if missing_comps:
                    _log("ERROR", f"Images NOT loaded: {', '.join(sorted(missing_comps))}")
                    raise RuntimeError(f"Cannot deploy: target-stack missing {', '.join(sorted(missing_comps))}")
                _log("OK", f"All images verified: {', '.join(sorted(loaded_comps))}")
            except RuntimeError:
                raise
            except Exception:
                _log("WARN", "Stack verification skipped -- proceeding")
            t_deploy = time.time()
            sys_type = deploy_params.get("system_type") or ""
            d_name = deploy_params.get("deploy_name") or device_id
            ncc_id = deploy_params.get("ncc_id", 0)
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
                                 message=f"Deploying: request system deploy system-type {sys_type} ...")
            deploy_out, ncc_id = _send_deploy_command(chan, sys_type, d_name, ncc_id, _log)
            stage_times["deploy"] = round(time.time() - t_deploy, 1)
            _log("OK", f"Deploy command sent ({stage_times['deploy']}s)")
        finally:
            try:
                client.close()
            except Exception:
                pass
        return

    stage_times["connect"] = round(time.time() - t_phase, 1)
    _send_wait = _make_send_wait(chan)

    # Phase 2: Snapshot running config (for later restore if needed)
    pre_upgrade_config = ""
    try:
        t_phase = time.time()
        _update_device_state(job_id, device_id, phase="snapshot", percent=5,
                             message="Backing up configuration...")
        pre_upgrade_config = _send_wait("show config running | no-more", 3)
        stage_times["snapshot"] = round(time.time() - t_phase, 1)
        _log("OK", "Pre-delete config snapshot taken")

        try:
            backup_dir = Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname
            backup_dir.mkdir(parents=True, exist_ok=True)
            with open(backup_dir / "pre_delete_config.txt", "w") as f:
                f.write(pre_upgrade_config)
            _log("INFO", "Config backup saved to disk")
        except Exception:
            pass
    except Exception as snap_err:
        _log("WARN", f"Config snapshot failed: {snap_err}")

    # Phase 3: Detect deploy params from device if not provided
    if not deploy_params or not deploy_params.get("system_type"):
        deploy_params = _detect_deploy_params(chan, device_id, _send_wait, _log)
    else:
        _log("INFO", f"Using provided deploy params: {deploy_params}")

    # Save deploy params to operational.json for recovery
    try:
        op_file = Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname / "operational.json"
        op_file.parent.mkdir(parents=True, exist_ok=True)
        op_data = {}
        if op_file.exists():
            with open(op_file) as f:
                op_data = json.load(f)
        from datetime import datetime as dt
        _dp_sys = deploy_params.get("system_type", "")
        _dp_name = deploy_params.get("deploy_name", device_id)
        _dp_ncc = deploy_params.get("ncc_id", 0)
        op_data.update({
            "deploy_system_type": _dp_sys,
            "deploy_name": _dp_name,
            "deploy_ncc_id": str(_dp_ncc),
            "deploy_command": (
                f"request system deploy system-type {_dp_sys} "
                f"name {_dp_name} ncc-id {_dp_ncc}"
            ) if _dp_sys else "",
            "delete_initiated": dt.now().isoformat(),
            "device_state": "GI",
            "recovery_mode_detected": True,
            "recovery_type": "GI",
            "upgrade_in_progress": True,
            "upgrade_job_id": job_id,
        })
        with open(op_file, "w") as f:
            json.dump(op_data, f, indent=4)
    except Exception:
        pass

    # Phase 4: Execute system delete
    t_phase = time.time()
    _update_device_state(job_id, device_id, phase="deleting", percent=10,
                         message="Executing system delete...")
    _log("INFO", "Executing 'request system delete'...")
    chan.send("request system delete\n")
    time.sleep(3)
    while chan.recv_ready():
        chan.recv(65535)
        time.sleep(0.3)
    chan.send("yes\n")
    time.sleep(2)
    while chan.recv_ready():
        chan.recv(65535)
    stage_times["delete"] = round(time.time() - t_phase, 1)
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

                    try:
                        op_file = Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname / "operational.json"
                        if op_file.exists():
                            with open(op_file) as f:
                                op_data = json.load(f)
                            op_data["device_state"] = "GI"
                            op_data["recovery_mode_detected"] = False
                            op_data["install_type"] = "gi_deploy"
                            with open(op_file, "w") as f:
                                json.dump(op_data, f, indent=4)
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

    # Phase 6: Load images in GI mode
    try:
        _update_device_state(job_id, device_id, phase="load", percent=35,
                             message="Loading images in GI mode...")
        _load_images_on_channel(job_id, device_id, gi_chan, url_list, stage_times, _log,
                                pct_base=35, pct_range=40)

        # Phase 6b: Pre-deploy validation -- verify target-stack has loaded images
        _images_verified = False
        try:
            gi_sw = _make_send_wait(gi_chan)
            stack_verify = gi_sw("show system stack | no-more", 4)
            stack_clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', stack_verify)
            _log("INFO", f"Pre-deploy stack:\n{stack_clean[:500]}")

            loaded_components = set()
            for line in stack_clean.split('\n'):
                if '|' not in line or '---' in line:
                    continue
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 6:
                    comp = parts[0].upper()
                    target_ver = parts[5] if len(parts) > 5 else ""
                    if target_ver and target_ver != "-":
                        loaded_components.add(comp)

            expected = {c.upper() for c, u in url_list if u}
            missing = expected - loaded_components
            if missing:
                _log("ERROR", f"Images NOT loaded in target-stack: {', '.join(sorted(missing))}")
                _update_device_state(job_id, device_id, phase="error", percent=78,
                                     message=f"BLOCKED: images not loaded ({', '.join(sorted(missing))}). Cannot deploy.")
                raise RuntimeError(
                    f"Cannot deploy: target-stack is missing {', '.join(sorted(missing))}. "
                    f"Image load may have failed or URLs may be expired. "
                    f"Verify URLs are accessible and retry.")
            else:
                _log("OK", f"All images verified in target-stack: {', '.join(sorted(loaded_components))}")
                _images_verified = True
        except RuntimeError:
            raise
        except Exception as sv_err:
            _log("WARN", f"Stack pre-check failed: {sv_err} -- proceeding with caution")

        # Phase 7: Deploy -- socket close after deploy is EXPECTED (device reboots)
        t_phase = time.time()
        sys_type = deploy_params.get("system_type") or ""
        d_name = deploy_params.get("deploy_name") or device_id
        ncc_id = deploy_params.get("ncc_id", 0)
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
                             message=f"Deploying: request system deploy system-type {sys_type} ...")
        deploy_out, ncc_id = _send_deploy_command(gi_chan, sys_type, d_name, ncc_id, _log)
        stage_times["deploy"] = round(time.time() - t_phase, 1)
        _log("OK", f"Deploy command sent ({stage_times['deploy']}s)")

        try:
            op_file = Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname / "operational.json"
            if op_file.exists():
                with open(op_file) as f:
                    op_data = json.load(f)
                op_data["device_state"] = "DEPLOYING"
                op_data["deploy_initiated"] = time.time()
                with open(op_file, "w") as f:
                    json.dump(op_data, f, indent=4)
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
        raise RuntimeError(f"Device did not return to DNOS mode after deploy (timed out). "
                           f"Device may still be deploying -- check manually via SSH.")


def _ensure_ncc_bash(chan):
    """Navigate to NCC bash shell from whatever CLI state the channel is in.

    Uses echo probe to safely detect bash vs GI/DNOS CLI without risking
    exiting too many shell layers in the virsh console chain
    (KVM SSH -> virsh console -> NCC bash -> gicli/dncli).
    """
    import time

    chan.send(b"\x03")
    time.sleep(0.5)
    while chan.recv_ready():
        chan.recv(65535)

    chan.send(b"echo __BASH_PROBE_OK__\n")
    time.sleep(1.5)
    buf = b""
    for _ in range(10):
        if chan.recv_ready():
            buf += chan.recv(65535)
        time.sleep(0.3)

    if b"__BASH_PROBE_OK__" in buf:
        return True

    chan.send(b"exit\n")
    time.sleep(2)
    while chan.recv_ready():
        chan.recv(65535)

    chan.send(b"echo __BASH_PROBE_OK__\n")
    time.sleep(1.5)
    buf = b""
    for _ in range(10):
        if chan.recv_ready():
            buf += chan.recv(65535)
        time.sleep(0.3)

    return b"__BASH_PROBE_OK__" in buf


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

    chan.send(b"sudo docker service ls 2>/dev/null\n")
    time.sleep(4)
    svc_buf = b""
    for _ in range(10):
        if chan.recv_ready():
            svc_buf += chan.recv(65535)
        time.sleep(0.3)
    svc_text = svc_buf.decode("utf-8", errors="replace")
    svc_clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', svc_text)

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
    elif "error" in svc_clean.lower() or not svc_clean.strip():
        result["needs_recovery"] = True
        result["diagnosis"] = "Docker swarm unavailable"
        _log("WARN", "Docker swarm unavailable -- needs recovery")
    else:
        result["needs_recovery"] = True
        result["diagnosis"] = "gi-manager service not found"
        _log("WARN", "gi-manager service not found -- needs recovery")

    chan.send(b"sudo docker ps --format '{{.Image}}' 2>/dev/null\n")
    time.sleep(2)
    ps_buf = b""
    for _ in range(10):
        if chan.recv_ready():
            ps_buf += chan.recv(65535)
        time.sleep(0.3)
    ps_text = ps_buf.decode("utf-8", errors="replace")
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
    for cmd, wait_s, desc in cmds:
        _log("INFO", f"Recovery: {desc}")
        chan.send((cmd + "\n").encode())
        time.sleep(wait_s)
        out = b""
        while chan.recv_ready():
            out += chan.recv(65535)
            time.sleep(0.2)
        if out:
            text = out.decode("utf-8", errors="replace").strip()
            for line in text.split("\n")[:5]:
                line = line.strip()
                if line and not line.startswith("$"):
                    _log("INFO", f"  {line[:120]}")

    _log("WARN", "Recovery: rebooting NCC...")
    _update_device_state(job_id, device_id, phase="gi-recovery", percent=48,
                         message="Rebooting NCC after cleanup...")
    chan.send(b"sudo reboot\n")
    time.sleep(3)


def _preflight_gi_health(job_id, device_id, chan, ssh, scaler_hostname, _log):
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

    _gi_cli_ok = False
    try:
        chan.send(b"\x03")
        time.sleep(0.5)
        while chan.recv_ready():
            chan.recv(65535)

        chan.send(b"show system stack | no-more\n")
        time.sleep(6)
        buf = b""
        for _ in range(10):
            if chan.recv_ready():
                buf += chan.recv(65535)
            time.sleep(0.3)

        text = buf.decode("utf-8", errors="replace")
        clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        if "Component" in clean or ("GI" in clean and "|" in clean):
            _gi_cli_ok = True
            _log("INFO", "GI CLI functional -- proceeding")
            while chan.recv_ready():
                chan.recv(65535)
                time.sleep(0.1)
    except Exception:
        pass

    if _gi_cli_ok:
        return ssh, chan, None, False

    _log("WARN", "GI CLI not responsive -- checking gi-manager health")
    _update_device_state(job_id, device_id, phase="gi-recovery", percent=7,
                         message="GI CLI unavailable -- checking gi-manager...")

    at_bash = _ensure_ncc_bash(chan)
    if not at_bash:
        _log("WARN", "Cannot reach NCC bash for health check -- trying load anyway")
        return ssh, chan, None, False

    health = _check_gi_manager_health(chan, _log)
    if not health.get("needs_recovery"):
        _log("INFO", f"gi-manager healthy ({health.get('diagnosis', '?')}) -- retrying")
        return ssh, chan, None, False

    _log("WARN", "gi-manager stuck -- running recovery before upgrade")
    _run_gi_manager_recovery(job_id, device_id, chan, _log)
    try:
        ssh.close()
    except Exception:
        pass

    _update_device_state(job_id, device_id, phase="gi-recovery", percent=15,
                         message="Waiting for NCC to reboot after recovery...")
    time.sleep(90)

    gi_wait_timeout = 600
    gi_wait_start = time.time()
    while time.time() - gi_wait_start < gi_wait_timeout:
        elapsed_r = int(time.time() - gi_wait_start)
        _update_device_state(job_id, device_id, phase="gi-recovery",
                             percent=15 + min(elapsed_r // 20, 15),
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
                    _log("INFO", f"NCC reachable but GI CLI not ready yet ({elapsed_r}s)")
                try:
                    conn["ssh"].close()
                except Exception:
                    pass
        except Exception:
            pass
        time.sleep(30)

    raise RuntimeError("Timeout waiting for GI mode after gi-manager recovery")


def _post_deploy_verify(job_id, device_id, scaler_hostname, stage_times, _log,
                        verify_timeout=1200, check_interval=20,
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
    _saw_gi_prompt = False
    _last_state_change_at = time.time()
    _prev_conn_state = None

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
                    _log("OK", f"Device back in DNOS mode (via {method}, {elapsed_m}m {elapsed_s}s after deploy)")
                    stage_times["post_deploy_verify"] = round(time.time() - t_phase, 1)
                    try:
                        chan = conn.get("channel")
                        if chan:
                            _post_deploy_config_repair(job_id, device_id, scaler_hostname, chan, _log)
                    except Exception as cr_err:
                        _log("WARN", f"Post-deploy config repair skipped: {cr_err}")
                    try:
                        conn["ssh"].close()
                    except Exception:
                        pass
                    return True
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
                                                    stage_times, _log, pct_base=55, pct_range=20)
                            sys_type = deploy_params.get("system_type") or ""
                            d_name = deploy_params.get("deploy_name") or device_id
                            ncc_id = deploy_params.get("ncc_id", 0)
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
                            _send_deploy_command(ch, sys_type, d_name, ncc_id, _log)
                            _log("OK", "Deploy re-sent after gi-manager recovery")
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
                        install_running = False
                        deploy_progressing = False
                        try:
                            if ch:
                                _sw_tmp = _make_send_wait(ch)
                                if state == "GI":
                                    stack_out = _sw_tmp("show system stack | no-more", 5)
                                    stack_clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', stack_out)
                                    has_current = bool(re.search(
                                        r'\|\s*(?:DNOS|GI|BASEOS)\s*\|.*\|.*\|.*\|[^-|]+\|',
                                        stack_clean))
                                    has_target = "Target" in stack_clean or bool(re.search(
                                        r'\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^-\s|]', stack_clean))
                                    if has_current:
                                        deploy_progressing = True
                                        _log("INFO", f"Stack shows Current populated -- deploy progressing")
                                    elif has_target:
                                        deploy_progressing = True
                                    install_out = _sw_tmp("show system install | no-more", 4)
                                else:
                                    install_out = ""
                                    _log("INFO", f"Device in BASEOS_SHELL ({elapsed_m}m) -- NCC rebooting")
                                if install_out:
                                    install_clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', install_out)
                                    install_lines = [l.strip() for l in install_clean.split('\n')
                                                     if l.strip() and 'show system' not in l.lower()]
                                    if install_lines:
                                        install_summary = install_lines[-1][:100]
                                        _log("INFO", f"Install status: {install_summary}")
                                        _update_device_state(job_id, device_id, phase="installing",
                                                             percent=85 + min(elapsed // 72, 12),
                                                             message=f"Installing... {install_summary}")
                                    lo = install_clean.lower()
                                    if ("in_progress" in lo or "in progress" in lo
                                            or "running" in lo or "started" in lo):
                                        install_running = True
                        except Exception:
                            pass

                        gi_elapsed = time.time() - gi_first_seen_at if gi_first_seen_at else 0
                        time_in_same_state = time.time() - _last_state_change_at

                        if _saw_gi_prompt or deploy_progressing:
                            pass
                        elif (not gi_recovery_attempted
                                and gi_elapsed > GI_STALL_THRESHOLD
                                and time_in_same_state > GI_STALL_THRESHOLD
                                and not install_running
                                and not deploy_progressing
                                and url_list and deploy_params and ch):
                            _log("WARN", f"Device stuck in {state} for {int(gi_elapsed)}s "
                                 f"(same state {int(time_in_same_state)}s, never saw GI prompt) "
                                 f"-- checking gi-manager")
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


def _post_deploy_config_repair(job_id, device_id, scaler_hostname, chan, _log):
    """After delete+deploy or gi_deploy, restore saved config and detect failures.

    Flow:
    1. Check config drift via 'show config compare rollback 1'
    2. Attempt rollback + commit
    3. If commit fails, parse error output to extract unsupported hierarchies
    4. Attempt line-by-line repair to isolate exactly which config blocks fail
    5. Report failed hierarchies with version-aware analysis to GUI
    """
    import time
    import re

    _update_device_state(job_id, device_id, phase="config-repair", percent=95,
                         message="Checking post-deploy config...")

    _sw = _make_send_wait(chan)
    _ansi = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

    def _term(msg):
        """Append a line to the job terminal output visible in GUI."""
        with _push_jobs_lock:
            if job_id in _push_jobs:
                _push_jobs[job_id]["terminal_lines"].append(msg)

    try:
        time.sleep(3)
        diff_out = _sw("show config compare rollback 1 | no-more", 5)
        diff_clean = _ansi.sub('', diff_out)
        diff_lines = [l for l in diff_clean.split("\n")
                      if l.strip().startswith("+") or l.strip().startswith("-")]

        if len(diff_lines) == 0:
            _log("OK", "No config drift detected after deploy")
            _term(f"[OK] {device_id}: No config drift -- nothing to restore")
            _update_device_state(job_id, device_id, config_restored=True)
            return

        has_deleted = "Deleted:" in diff_clean
        _log("INFO", f"Config drift detected ({len(diff_lines)} lines changed)"
             f"{' -- deleted sections found' if has_deleted else ''}")
        _term(f"[INFO] {device_id}: Config drift: {len(diff_lines)} lines changed")

        if not has_deleted:
            _log("INFO", "Only additions detected, no repair needed")
            _term(f"[OK] {device_id}: Only additions -- no repair needed")
            _update_device_state(job_id, device_id, config_restored=True)
            return

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
            _update_device_state(job_id, device_id, config_restored=True)
            return

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
                                     config_repair_partial=True,
                                     config_repair_failures=failed_hierarchies)
            else:
                _log("ERROR", "Partial config repair also failed")
                _term(f"[ERROR] {device_id}: Partial config repair also failed -- manual intervention needed")
                _update_device_state(job_id, device_id,
                                     config_restored=False,
                                     config_repair_partial=False,
                                     config_repair_failures=failed_hierarchies)
        else:
            _term(f"[ERROR] {device_id}: Config rollback failed (could not parse specific failures)")
            _term(f"[ERROR] {device_id}: Commit output: {commit_clean[:300]}")
            _update_device_state(job_id, device_id,
                                 config_restored=False,
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

    # Source 1: operational.json
    try:
        cfg_dir = _resolve_config_dir(scaler_hostname)
        op_path = Path(SCALER_ROOT) / "db" / "configs" / cfg_dir / "operational.json"
        if op_path.exists():
            op = json.loads(op_path.read_text())
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
    prev_sys_type = ""
    try:
        cfg_dir = _resolve_config_dir(scaler_hostname)
        op_path = Path(SCALER_ROOT) / "db" / "configs" / cfg_dir / "operational.json"
        if op_path.exists():
            op = json.loads(op_path.read_text())
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
             f"Recovery: SSH to each NCE (port 2222, dn/drivenets), run the full cleaner "
             f"(docker swarm leave --force, docker system prune, rm nce_id/cluster_id/node_flavor, reboot). "
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
            op = json.loads(op_path.read_text())
            op["previous_system_type"] = prev_sys_type
            op["system_type_change_detected"] = True
            op["system_type_change_at"] = time.time()
            with open(op_path, "w") as f:
                json.dump(op, f, indent=4)
    except Exception:
        pass


def _run_gi_deploy_upgrade(job_id, device_id, url_list, deploy_params,
                            stage_times, _log, scaler_hostname=""):
    """GI deploy: device already in GI mode. Connect via connect_for_upgrade, load, deploy."""
    import time
    from pathlib import Path
    import json

    scaler_hostname = scaler_hostname or device_id

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

    try:
        _check_upgrade_cancel(job_id)
        _update_device_state(job_id, device_id, phase="load", percent=10,
                             message="Loading images...")
        _load_images_on_channel(job_id, device_id, chan, url_list, stage_times, _log,
                                pct_base=10, pct_range=55)

        try:
            _sw_pre = _make_send_wait(chan)
            sv = _sw_pre("show system stack | no-more", 4)
            sc = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', sv)
            _log("INFO", f"Pre-deploy stack:\n{sc[:500]}")
        except Exception:
            pass

        t_phase = time.time()
        sys_type = deploy_params.get("system_type") or ""
        d_name = deploy_params.get("deploy_name") or device_id
        ncc_id = conn_ncc_id if conn_ncc_id is not None else deploy_params.get("ncc_id", 0)

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
                             message=f"Deploying: request system deploy system-type {sys_type} ...")

        _log("INFO", f"Deploy params resolved: system_type={sys_type}, name={d_name}, ncc_id={ncc_id}")
        deploy_out, ncc_id = _send_deploy_command(chan, sys_type, d_name, ncc_id, _log)
        stage_times["deploy"] = round(time.time() - t_phase, 1)
        _log("OK", f"Deploy command sent ({stage_times['deploy']}s)")

        try:
            op_file = Path(SCALER_ROOT) / "db" / "configs" / scaler_hostname / "operational.json"
            if op_file.exists():
                with open(op_file) as f:
                    op_data = json.load(f)
                op_data["device_state"] = "DEPLOYING"
                op_data["deploy_initiated"] = time.time()
                with open(op_file, "w") as f:
                    json.dump(op_data, f, indent=4)
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
        raise RuntimeError(f"Device did not return to DNOS mode after deploy (timed out). "
                           f"Device may still be deploying -- check manually via SSH.")


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
def image_upgrade_device_status(device_ids: str = "", ssh_hosts: str = "", cached_only: bool = False):
    """Get install/deploy progress per device.
    Query: device_ids=id1,id2&ssh_hosts=ip1,ip2&cached_only=true
    When cached_only=true, reads from operational.json + stack cache only (no SSH, ~10ms/device).
    When cached_only=false (default), performs parallel SSH for live status."""
    ids = [x.strip() for x in (device_ids or "").split(",") if x.strip()]
    hosts_raw = (ssh_hosts or "").split(",")
    hosts = {ids[i] if i < len(ids) else "": h.strip() for i, h in enumerate(hosts_raw) if h.strip()}
    if not ids:
        raise HTTPException(status_code=400, detail="device_ids is required")

    if cached_only:
        return _device_status_from_cache(ids, hosts)

    try:
        import re
        from concurrent.futures import ThreadPoolExecutor, as_completed
        cwd = os.getcwd()
        os.chdir(SCALER_ROOT)
        try:
            from scaler.interactive_scale import _check_single_device_status
            strip_markup = re.compile(r"\[/?[^\]]+\]")

            def _check_one(did):
                ssh_host = hosts.get(did, "")
                mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(did, ssh_host)
                _ensure_operational_json(scaler_id or did, mgmt_ip)
                class _Dev:
                    hostname = scaler_id or did
                try:
                    r = _check_single_device_status(_Dev())
                    return did, {k: strip_markup.sub("", str(v)) for k, v in r.items()}
                except Exception:
                    return did, {"mode": "?", "dnos_ver": "-", "gi_ver": "-", "baseos_ver": "-", "install_status": "SSH failed"}

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
    import re
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
                ops = json.loads(ops_path.read_text())
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

                if status["mode"] or status["dnos_ver"]:
                    break

                is_upgrading = ops.get("upgrade_in_progress", False)
                if is_upgrading:
                    inst_status = (ops.get("install_status") or "").upper()
                    inst_finish = ops.get("install_finish", "")
                    if inst_status in ("COMPLETED", "FAILED", "ERROR"):
                        status["install_status"] = inst_status.capitalize()
                        ops["upgrade_in_progress"] = False
                        try:
                            ops_path.write_text(json.dumps(ops, indent=2))
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
                                    ops_path.write_text(json.dumps(ops, indent=2))
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
    """Ensure operational.json exists with mgmt_ip for connect_for_upgrade."""
    ops_dir = Path(SCALER_ROOT) / "db" / "configs" / hostname
    ops_dir.mkdir(parents=True, exist_ok=True)
    ops_path = ops_dir / "operational.json"
    data = {}
    if ops_path.exists():
        try:
            data = json.loads(ops_path.read_text())
        except Exception:
            pass
    if mgmt_ip:
        data["mgmt_ip"] = mgmt_ip
        data["ssh_host"] = mgmt_ip
    ops_path.write_text(json.dumps(data, indent=2))


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
def image_upgrade_from_urls(body: dict):
    """Upgrade from pasted Minio URLs. Same as image_upgrade_execute with dnos_url, gi_url, baseos_url."""
    return image_upgrade_execute(body)


@router.post("/api/operations/image-upgrade/wait-and-upgrade")
def image_upgrade_wait_and_upgrade(body: dict):
    """Monitor a running build in the backend, then auto-start upgrade when it finishes.

    Creates a single job that covers both phases:
      Phase 1: Poll Jenkins for build completion (progress 0-50%)
      Phase 2: Resolve URLs + run upgrade on devices (progress 50-100%)
    The frontend opens showProgress immediately and sees the whole lifecycle.
    """
    import uuid
    import threading
    from datetime import datetime

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
                                        _od = json.loads(_op_p.read_text())
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
                                                            f"[WARN] {did}: Major version jump "
                                                            f"v{_cur_m.group(1)} -> v{_tgt_m.group(1)}, "
                                                            f"using delete_deploy")
                                        _dp = {
                                            "system_type": (
                                                _od.get("system_type")
                                                or _od.get("deploy_system_type")
                                                or ""
                                            ),
                                            "deploy_name": (
                                                _od.get("deploy_name") or _h
                                            ).rstrip(",").strip(),
                                            "ncc_id": int(
                                                _od.get("deploy_ncc_id")
                                                or _od.get("ncc_id")
                                                or 0
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
                                                    f"[INFO] {did}: mode={_mode}, type={_ut}, "
                                                    f"sys={_dp['system_type']}, name={_dp['deploy_name']}")
                                except Exception as _pe:
                                    with _push_jobs_lock:
                                        if job_id in _push_jobs:
                                            _push_jobs[job_id]["terminal_lines"].append(
                                                f"[WARN] {did}: auto-plan failed: {_pe}")
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
    t = threading.Thread(target=_wait_then_upgrade, daemon=True)
    t.start()

    return {
        "job_id": job_id,
        "status": "started",
        "message": f"Monitoring build {build_label}, will auto-upgrade {len(device_ids)} devices",
        "devices": device_ids,
    }


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
def image_upgrade_restore_config(body: dict):
    """Push backed-up pre-delete config to devices (non-interactive)."""
    device_ids = body.get("device_ids", [])
    ssh_hosts = body.get("ssh_hosts", {})
    if not device_ids:
        raise HTTPException(status_code=400, detail="device_ids is required")
    try:
        cwd = os.getcwd()
        try:
            os.chdir(SCALER_ROOT)
            user, password = _get_credentials()
            results = {}
            for did in device_ids:
                ssh_host = ssh_hosts.get(did, "") if isinstance(ssh_hosts, dict) else ""
                mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(did, ssh_host)
                hostname = scaler_id or did
                device_dir = Path(SCALER_ROOT) / "db" / "configs" / hostname
                backup_files = list(device_dir.glob("pre_delete_backup_*.txt")) + list(device_dir.glob("pre_upgrade_backup_*.txt"))
                backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                if not backup_files:
                    results[did] = {"success": False, "message": "No backup found"}
                    continue
                backup_path = backup_files[0]
                config_text = backup_path.read_text()
                class _Dev:
                    def __init__(self, hostname, ip, username, password):
                        self.hostname = hostname
                        self.ip = ip
                        self.username = username
                        self._password = password
                    def get_password(self):
                        return self._password
                dev = _Dev(hostname, mgmt_ip, user, password)
                try:
                    from scaler.config_pusher import ConfigPusher
                    pusher = ConfigPusher()
                    success, message = pusher.push_config(dev, config_text, dry_run=False)
                    results[did] = {"success": success, "message": message}
                except Exception as e:
                    import traceback
                    results[did] = {"success": False, "message": f"{e}\n\nDetails:\n{traceback.format_exc()}"}
            return {"success": True, "results": results}
        finally:
            os.chdir(cwd)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/operations/{job_id}/cancel")
def operations_cancel(job_id: str):
    """Cancel a push or upgrade job. Upgrade jobs are marked done immediately;
    the background thread detects _cancel_requested and exits cleanly."""
    is_upgrade = False
    with _push_jobs_lock:
        job = _push_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        status = job.get("status", "")
        is_upgrade = job.get("type") == "upgrade"
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

        if is_upgrade:
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
            job["terminal_lines"].append("[WARN] Upgrade cancelled by user")
            ds = job.get("device_state", {})
            for did, dstate in ds.items():
                if dstate.get("status") in ("running", "pending", "connecting"):
                    dstate["status"] = "cancelled"
                    dstate["phase"] = "Cancelled"
        elif status in ("running", "pending") and not (channel and client and pusher):
            job["status"] = "cancelling"
            job["phase"] = "Aborting paste..."

    if is_upgrade:
        _persist_job_if_done(job_id)
        _remove_active_upgrade(job_id)
        return {"status": "cancelled", "success": False, "message": "Upgrade cancelled"}

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

def _recover_active_upgrades():
    """On startup, recover or mark interrupted any in-flight upgrade jobs.

    wait_and_upgrade jobs in build-monitoring phase are fully resumable --
    the Jenkins build keeps running regardless of our server. Only jobs
    that had active SSH sessions (upgrading phase) are marked interrupted.
    """
    if not _ACTIVE_UPGRADES_PATH.exists():
        return
    try:
        with open(_ACTIVE_UPGRADES_PATH) as f:
            upgrades = json.load(f)
    except Exception:
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

            t = threading.Thread(target=_resume_wau, args=(job_id, job_data), daemon=True)
            t.start()
            print(f"[STARTUP] Resumed wait_and_upgrade job {job_id} (phase={phase})")
            continue

        ds = job_data.get("device_state", {})
        for did, state in ds.items():
            if state.get("status") == "running":
                state["status"] = "failed"
                state["error"] = "Server restarted during upgrade"
                state["phase"] = "interrupted"
                state["message"] = "Interrupted -- server restarted. Check device state manually."

        job_data["status"] = "failed"
        job_data["done"] = True
        job_data["phase"] = "interrupted"
        job_data["message"] = "Server restarted during upgrade -- check device state"
        job_data["completed_at"] = datetime.utcnow().isoformat() + "Z"
        job_data["terminal_lines"] = job_data.get("terminal_lines", [])
        job_data["terminal_lines"].append(
            "[WARN] Server restarted while upgrade was running. "
            "Devices may be in GI mode. Use the Image Upgrade wizard to reconnect and resume.")

        with _push_jobs_lock:
            _push_jobs[job_id] = job_data
        _persist_job_if_done(job_id)
        _remove_active_upgrade(job_id)


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

        threading.Thread(target=_resume_monitor, args=(job_id, job_data), daemon=True).start()
        print(f"[STARTUP] Resumed build monitor for {job_id} (branch={branch})")

