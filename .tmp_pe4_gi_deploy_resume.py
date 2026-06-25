#!/usr/bin/env python3
"""Resume PE-4 GI upgrade using existing topology upgrade helpers."""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/home/dn/drivenets-topology-studio")
SCALER_ROOT = Path(os.environ.get("SCALER_ROOT", "/home/dn/SCALER"))
os.environ["SCALER_ROOT"] = str(SCALER_ROOT)
sys.path.insert(0, str(REPO / "topology"))
sys.path.insert(0, str(REPO / "scaler"))
sys.path.insert(0, str(SCALER_ROOT))

from routes._ops_writer import read_ops, update_ops  # noqa: E402
from routes._state import _push_jobs, _push_jobs_lock  # noqa: E402
from routes.upgrade import _get_credentials, _run_device_upgrade  # noqa: E402


DEVICE = "YOR_CL_PE-4"
OPS_PATH = SCALER_ROOT / "db" / "configs" / DEVICE / "operational.json"
TARGET_VERSION = "26.2.0.4_priv.usirota_evpn_vpls_irb_4"
URL_LIST = [
    ("DNOS", f"http://minio-ssd-il.dev.drivenets.net:9000/dnpkg-48hrs/drivenets_dnos_{TARGET_VERSION}.tar"),
    ("GI", f"http://minio-ssd-il.dev.drivenets.net:9000/dnpkg-48hrs/drivenets_gi_{TARGET_VERSION}.tar"),
    ("BaseOS", "http://minio-ssd-il.dev.drivenets.net:9000/dnpkg-48hrs/drivenets_baseos_2.2620605002.tar"),
]


def _seed_resume_metadata() -> None:
    now = datetime.now(timezone.utc).isoformat()
    drop = [
        "manual_intervention_required",
        "manual_intervention_reason",
        "manual_intervention_at",
        "manual_intervention_missing",
        "manual_intervention_live_mode",
        "manual_intervention_deploy_command",
    ]

    def _mut(d: dict) -> bool:
        d["upgrade_url_list"] = [[comp, url] for comp, url in URL_LIST]
        d["upgrade_deploy_system_type"] = "CL-86"
        d["upgrade_deploy_name"] = DEVICE
        d["upgrade_deploy_ncc_id"] = 1
        d["upgrade_deploy_command"] = "request system deploy system-type CL-86 name YOR_CL_PE-4 ncc-id 1"
        d["upgrade_in_progress"] = True
        d["device_state"] = "GI"
        d["upgrade_resume_seeded_at"] = now
        d["upgrade_resume_seeded_by"] = ".tmp_pe4_gi_deploy_resume.py"
        for key in drop:
            d.pop(key, None)
        d["_drop_keys"] = drop
        return True

    update_ops(OPS_PATH, _mut, create_if_missing=True)


def main() -> int:
    if not OPS_PATH.exists():
        raise RuntimeError(f"Missing operational.json: {OPS_PATH}")

    backup = (read_ops(OPS_PATH).get("pre_delete_backup") or "").strip()
    if not backup or not Path(backup).exists():
        raise RuntimeError("PE-4 pre-delete backup is missing; refusing to deploy without repair snapshot")

    _seed_resume_metadata()

    user, password = _get_credentials()
    job_id = f"manual-pe4-resume-{int(time.time())}"
    now = datetime.now(timezone.utc).isoformat()
    deploy_params = {
        "system_type": "CL-86",
        "deploy_name": DEVICE,
        "ncc_id": 1,
    }
    with _push_jobs_lock:
        _push_jobs[job_id] = {
            "job_id": job_id,
            "job_type": "upgrade",
            "owner": "manual-agent",
            "status": "running",
            "phase": "gi_deploy",
            "message": "Manual agent PE-4 GI deploy resume",
            "percent": 0,
            "success": False,
            "done": False,
            "started_at": now,
            "devices": [DEVICE],
            "components": [comp for comp, _ in URL_LIST],
            "image_urls": {comp.lower(): {"url": url, "valid": True} for comp, url in URL_LIST},
            "device_plans": {DEVICE: {"upgrade_type": "gi_deploy", "deploy_params": deploy_params}},
            "upgrade_type": "gi_deploy",
            "max_concurrent": 1,
            "terminal_lines": [],
            "device_state": {
                DEVICE: {
                    "status": "running",
                    "phase": "gi_deploy",
                    "percent": 0,
                    "components": [comp for comp, _ in URL_LIST],
                    "upgrade_type": "gi_deploy",
                    "message": "Starting GI deploy resume",
                    "started_at": now,
                }
            },
        }

    def _log(level, message):
        line = f"[{str(level).upper()}] {DEVICE}: {message}"
        print(line, flush=True)
        with _push_jobs_lock:
            if job_id in _push_jobs:
                _push_jobs[job_id].setdefault("terminal_lines", []).append(line)

    try:
        _run_device_upgrade(
            job_id,
            DEVICE,
            "100.64.4.98",
            user,
            password,
            URL_LIST,
            upgrade_type="gi_deploy",
            deploy_params=deploy_params,
            scaler_hostname=DEVICE,
        )
    finally:
        with _push_jobs_lock:
            job = _push_jobs.get(job_id, {})
            print("final_job=" + json.dumps(job, indent=2, default=str), flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
