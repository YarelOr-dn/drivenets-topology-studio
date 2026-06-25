#!/usr/bin/env python3
"""One-shot PE-1 post-upgrade config repair using existing bridge helpers."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/home/dn/drivenets-topology-studio")
SCALER_ROOT = Path(os.environ.get("SCALER_ROOT", "/home/dn/SCALER"))
os.environ["SCALER_ROOT"] = str(SCALER_ROOT)
sys.path.insert(0, str(REPO / "topology"))
sys.path.insert(0, str(REPO / "scaler"))
sys.path.insert(0, str(SCALER_ROOT))

from routes._ops_writer import read_ops, update_ops  # noqa: E402
from routes.upgrade import _clean_show_config_snapshot, _get_credentials, _resolve_mgmt_ip  # noqa: E402
from scaler.config_pusher import ConfigPusher  # noqa: E402


DEVICE_ID = "PE-1"
CONFIG_DIR = SCALER_ROOT / "db" / "configs" / DEVICE_ID
OPS_PATH = CONFIG_DIR / "operational.json"


def _candidate_paths() -> list[Path]:
    paths = []
    paths.extend(CONFIG_DIR.glob("pre_delete_backup_*.txt"))
    paths.extend(CONFIG_DIR.glob("pre_upgrade_backup_*.txt"))
    fixed = CONFIG_DIR / "pre_delete_config.txt"
    if fixed.exists():
        paths.append(fixed)
    registered = (read_ops(OPS_PATH).get("pre_delete_backup") or "").strip()
    if registered and Path(registered).exists():
        paths.insert(0, Path(registered))
    unique = []
    seen = set()
    for p in paths:
        rp = str(p.resolve())
        if rp not in seen:
            unique.append(p)
            seen.add(rp)
    unique.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return unique


def _score_snapshot(path: Path) -> tuple[int, str]:
    text = path.read_text(errors="replace")
    cleaned = _clean_show_config_snapshot(text)
    meaningful = [
        line for line in cleaned.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    has_identity = "name YOR_PE-1" in cleaned or "name PE-1" in cleaned
    has_core = all(token in cleaned for token in ("system\n", "interfaces\n", "protocols\n"))
    has_bad_echo = any(
        line.strip().lower().startswith("show config")
        for line in cleaned.splitlines()
    )
    if len(meaningful) < 50:
        return 0, f"too few meaningful lines ({len(meaningful)})"
    if has_bad_echo:
        return 0, "cleaned snapshot still contains show config echo"
    score = len(meaningful)
    if has_identity:
        score += 100000
    if has_core:
        score += 10000
    return score, f"{len(meaningful)} meaningful lines"


def _select_snapshot() -> tuple[Path, str]:
    results = []
    for p in _candidate_paths():
        try:
            score, reason = _score_snapshot(p)
        except Exception as exc:
            score, reason = 0, f"read/score failed: {exc}"
        results.append({"path": str(p), "score": score, "reason": reason})
    valid = [r for r in results if r["score"] > 0]
    if not valid:
        raise RuntimeError("No valid PE-1 pre-delete/pre-upgrade snapshot found: " + json.dumps(results, indent=2))
    valid.sort(key=lambda r: r["score"], reverse=True)
    selected = Path(valid[0]["path"])
    return selected, json.dumps(results[:8], indent=2)


class _Device:
    def __init__(self, hostname: str, ip: str, username: str, password: str):
        self.hostname = hostname
        self.ip = ip
        self.username = username
        self._password = password

    def get_password(self) -> str:
        return self._password


def main() -> int:
    selected, audit = _select_snapshot()
    raw = selected.read_text(errors="replace")
    config_text = _clean_show_config_snapshot(raw)
    meaningful = [
        line for line in config_text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    now = datetime.now(timezone.utc).isoformat()

    def _mark_selected(d: dict) -> bool:
        d["pre_delete_backup"] = str(selected)
        d["pre_delete_backup_source"] = "pe1_explicit_repair_selection"
        d["pre_delete_backup_validation"] = {
            "selected_at": now,
            "meaningful_lines": len(meaningful),
            "note": "Selected and cleaned by .tmp_pe1_config_repair.py before ConfigPusher load override",
        }
        d["config_repair_started_at"] = now
        d["upgrade_in_progress"] = False
        return True

    update_ops(OPS_PATH, _mark_selected, create_if_missing=True)

    user, password = _get_credentials()
    mgmt_ip, scaler_id, via = _resolve_mgmt_ip(DEVICE_ID, "")
    if not mgmt_ip:
        raise RuntimeError("Could not resolve PE-1 management IP")
    hostname = scaler_id or DEVICE_ID
    device = _Device(hostname, mgmt_ip, user, password)
    pusher = ConfigPusher()

    progress_lines = []

    def _progress(message, percent):
        line = f"{percent}% {message}"
        progress_lines.append(line)
        print(f"[PE-1 repair] {line}", flush=True)

    print(f"selected_snapshot={selected}", flush=True)
    print(f"snapshot_audit={audit}", flush=True)
    print(f"target={hostname} ip={mgmt_ip} via={via}", flush=True)
    print(f"cleaned_meaningful_lines={len(meaningful)}", flush=True)

    success, message = pusher.push_config(
        device,
        config_text,
        config_name=f"post_deploy_restore_{DEVICE_ID}_cleaned",
        dry_run=False,
        progress_callback=_progress,
    )

    result = {
        "success": bool(success),
        "message": message,
        "selected_snapshot": str(selected),
        "meaningful_lines": len(meaningful),
        "progress_tail": progress_lines[-10:],
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }

    def _mark_result(d: dict, _result=result) -> bool:
        d["config_repair_file"] = _result["selected_snapshot"]
        d["config_repair_message"] = _result["message"]
        d["config_repair_finished_at"] = _result["finished_at"]
        d["upgrade_in_progress"] = False
        if _result["success"]:
            d["config_repair_completed_at"] = _result["finished_at"]
            d["config_restored"] = True
        else:
            d["config_restored"] = False
            d["config_repair_error"] = str(_result["message"])[:500]
        return True

    update_ops(OPS_PATH, _mark_result, create_if_missing=True)
    print("repair_result=" + json.dumps(result, indent=2), flush=True)
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
