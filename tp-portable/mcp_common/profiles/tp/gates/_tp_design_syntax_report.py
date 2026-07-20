#!/usr/bin/env python3
"""DESIGN-syntax live-validation tracker for /TP (refines "pre-release syntax may
be wrong until live-validated"). Collects every verification/config command
tagged DESIGN / EXPECTED_LIVE_VALIDATE across the plan into one checklist so the
not-yet-live leaves are explicitly tracked for `cmd search` validation when the
build implements them. Writes design_syntax_to_validate.json (atomic).

Usage:
    python3 _tp_design_syntax_report.py --epic SW-211037
Exit 0 always (report/tracker, never blocks).
"""
from __future__ import annotations

from _tp_paths import default_data_dir
import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

_DESIGN = re.compile(r"DESIGN|EXPECTED_LIVE_VALIDATE", re.I)


def _atomic_write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.chmod(tmp, 0o644); os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def run_report(tp_dir: Path, epic: str) -> int:
    fr_path = tp_dir / "full_result.json"
    if not fr_path.exists():
        print(f"[FAIL] Missing full_result.json: {fr_path}")
        return 2
    fr = json.loads(fr_path.read_text(encoding="utf-8"))
    design_cmds: dict[str, list[str]] = {}
    for tc in fr.get("test_cases", []):
        for v in tc.get("verification_commands") or []:
            if not isinstance(v, dict):
                continue
            if _DESIGN.search(str(v.get("provenance", ""))):
                cmd = str(v.get("command", "")).strip()
                if cmd:
                    design_cmds.setdefault(cmd, [])
                    if tc.get("id") not in design_cmds[cmd]:
                        design_cmds[cmd].append(tc.get("id"))
    out = {
        "epic": epic,
        "design_command_count": len(design_cmds),
        "note": "Each command must be `cmd search`/CLI-doc validated on a build that "
                "implements the feature before its TCs are executed; until then they "
                "are DESIGN/EXPECTED_LIVE_VALIDATE.",
        "commands": {c: sorted(ids) for c, ids in sorted(design_cmds.items())},
    }
    _atomic_write_json(tp_dir / "design_syntax_to_validate.json", out)
    print(f"[OK] design_syntax_to_validate.json: {len(design_cmds)} DESIGN command(s) "
          f"to live-validate -> {tp_dir / 'design_syntax_to_validate.json'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="TP DESIGN-syntax live-validation tracker")
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    args = ap.parse_args()
    tp_dir = Path(args.dir).expanduser() / args.epic
    return run_report(tp_dir, args.epic)


if __name__ == "__main__":
    sys.exit(main())
