#!/usr/bin/env python3
"""Resolve epic Fix Version -> cheetah git checkout + lab implementation status.

Writes epic_version.json (atomic) under <tp_dir>/<EPIC>/.

Usage:
    python3 _tp_epic_version.py --epic SW-211037
    python3 _tp_epic_version.py --epic SW-211037 --probe-device PE-1

Exit 0 always (resolver report); BLOCKER is recorded in JSON, not exit code.
"""
from __future__ import annotations

from _tp_paths import default_data_dir
import argparse
import json
import sys
from pathlib import Path

from _tp_syntax_common import (
    atomic_write_json,
    parse_fix_versions,
    primary_dnos_version,
    resolve_cheetah_for_version,
)


def _read_epic_doc(tp_dir: Path, epic: str) -> str:
    p = tp_dir / f"epic_documentation_{epic}.md"
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def _probe_lab_device(device: str | None) -> dict:
    """Lightweight lab probe; shipped_in_lab only when explicitly probed and reachable."""
    if not device:
        return {"device": None, "reachable": False, "build": None}
    try:
        from _tp_live_syntax_probe import probe_device_reachable  # noqa: WPS433

        return probe_device_reachable(device)
    except Exception as exc:  # pragma: no cover - optional import path
        return {"device": device, "reachable": False, "build": None, "error": str(exc)}


def resolve_epic_version(
    tp_dir: Path,
    epic: str,
    *,
    probe_device: str | None = None,
    write: bool = True,
) -> dict:
    doc = _read_epic_doc(tp_dir, epic)
    fix_versions = parse_fix_versions(doc)
    primary = primary_dnos_version(fix_versions) or (fix_versions[0] if fix_versions else "")
    cheetah = resolve_cheetah_for_version(primary) if primary else {
        "fix_version": "",
        "matched": False,
        "repo": None,
        "rst_root": None,
        "branch": None,
        "sha": None,
        "blocker": {"message": "[BLOCKER] no Fix versions in epic doc"},
    }

    lab = _probe_lab_device(probe_device)
    implementation_status = "pending_build"
    if lab.get("reachable") and lab.get("build"):
        implementation_status = "shipped_in_lab"

    out = {
        "epic": epic,
        "fix_versions": fix_versions,
        "fix_version": primary,
        "rst_root": cheetah.get("rst_root"),
        "cheetah_repo": cheetah.get("repo"),
        "cheetah_branch": cheetah.get("branch"),
        "cheetah_sha": cheetah.get("sha"),
        "cheetah_matched": bool(cheetah.get("matched")),
        "implementation_status": implementation_status,
        "lab_device": lab.get("device"),
        "lab_build": lab.get("build"),
        "blocker": cheetah.get("blocker"),
    }
    if write:
        atomic_write_json(tp_dir / "epic_version.json", out)
    return out


def run_resolver(tp_dir: Path, epic: str, *, probe_device: str | None = None) -> int:
    if not tp_dir.is_dir():
        print(f"[FAIL] Missing epic dir: {tp_dir}")
        return 2
    out = resolve_epic_version(tp_dir, epic, probe_device=probe_device, write=True)
    print(f"[OK] epic_version.json fix_version={out.get('fix_version')} "
          f"implementation_status={out.get('implementation_status')} "
          f"rst_root={out.get('rst_root') or 'null'}")
    if out.get("blocker"):
        blk = out["blocker"]
        print(f"[BLOCKER] {blk.get('message')}")
        if blk.get("suggested_cmd"):
            print(f"  run: {blk['suggested_cmd']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="/TP epic version resolver")
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    ap.add_argument("--probe-device", default=None, help="Optional lab device for shipped_in_lab probe")
    args = ap.parse_args()
    tp_dir = Path(args.dir).expanduser() / args.epic
    return run_resolver(tp_dir, args.epic, probe_device=args.probe_device)


if __name__ == "__main__":
    sys.exit(main())
