#!/usr/bin/env python3
"""Epic-agnostic Stage-7 critic-refine loop driver for /TP.

Python side of the gated-autonomous loop: snapshot, score (worklist), record
history, and no-regression checks. Subagent fixers are spawned by the /TP agent
per tp-generator-command.mdc; this tool applies/regenerates and re-scores.

Usage:
    # Baseline snapshot + initial score (iter 0)
    python3 _tp_refine_loop.py --epic SW-211037 snapshot --iter 0
    python3 _tp_refine_loop.py --epic SW-211037 score --iter 0

    # After SoT fixes + regen, re-score and check no regression vs iter 0
    python3 _tp_refine_loop.py --epic SW-211037 score --iter 1
    python3 _tp_refine_loop.py --epic SW-211037 check-regression --prev 0 --curr 1

    # Full tail: score strict; exit 0 only when worklist clean
    python3 _tp_refine_loop.py --epic SW-211037 gate --strict

SoT files (never rendered markdown or gates):
    <tp_dir>/_gen_<EPIC>.py
    <tp_dir>/_enrich_data.py
    <tp_dir>/_scenario_coverage.py
    <tp_dir>/scenario_inventory_agent.json
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from _tp_paths import GATES_DIR as TP_ROOT, default_data_dir, resolve_mcp_root

GATES_DIR = TP_ROOT

sys.path.insert(0, str(TP_ROOT))
import _tp_refine_worklist as worklist  # noqa: E402


def _tp_dir(base: Path, epic: str) -> Path:
    return base.expanduser() / epic


def _gen_script(tp_dir: Path, epic: str) -> Path | None:
    p = tp_dir / f"_gen_{epic}.py"
    return p if p.exists() else None


def _snapshot(tp_dir: Path, epic: str, iter_num: int) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dest = tp_dir / f".backup_refine{iter_num}_{ts}"
    dest.mkdir(parents=True)
    patterns = (
        "_gen_*.py",
        "_enrich_data.py",
        "_scenario_coverage.py",
        "scenario_inventory_agent.json",
        "full_result.json",
        "manifest.json",
        f"test_plan_{epic}.md",
        "refine_worklist.json",
        "refine_history.json",
        "sources_ingested.json",
    )
    for pat in patterns:
        for src in tp_dir.glob(pat):
            if src.is_file():
                shutil.copy2(src, dest / src.name)
    print(f"[OK] Snapshot iter {iter_num} -> {dest}")
    return dest


def _regenerate(tp_dir: Path, epic: str) -> int:
    gen = _gen_script(tp_dir, epic)
    if not gen:
        print(f"[FAIL] No generator script: _gen_{epic}.py")
        return 2
    p = subprocess.run([sys.executable, str(gen)], cwd=str(tp_dir))
    return p.returncode


def _load_history_row(tp_dir: Path, iter_num: int) -> dict | None:
    hist_path = tp_dir / "refine_history.json"
    if not hist_path.exists():
        return None
    hist = json.loads(hist_path.read_text(encoding="utf-8"))
    for row in hist.get("iterations", []):
        if row.get("iter") == iter_num:
            return row
    return None


def _score_improved(prev: dict, curr: dict) -> bool:
    """True when curr is >= prev on all tracked metrics (no regression)."""
    keys = ("e2_missing", "below_floor", "story_zero", "story_thin", "worklist_count")
    for k in keys:
        if curr.get(k, 0) > prev.get(k, 0):
            return False
    # scenario/must/parity: string compare - curr should not lose ground
    for k in ("scenario", "must", "parity"):
        ps, cs = str(prev.get(k, "")), str(curr.get(k, ""))
        if ps == "skip" or cs == "skip":
            continue
        if "FAIL" in cs and "FAIL" not in ps:
            return False
        if "/" in ps and "/" in cs:
            pm, pt = ps.split("/", 1)
            cm, ct = cs.split("/", 1)
            try:
                if int(cm) < int(pm):
                    return False
            except ValueError:
                pass
    return True


def cmd_snapshot(args: argparse.Namespace) -> int:
    tp_dir = _tp_dir(Path(args.dir), args.epic)
    if not tp_dir.is_dir():
        print(f"[FAIL] Missing epic dir: {tp_dir}")
        return 2
    _snapshot(tp_dir, args.epic, args.iter)
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    tp_dir = _tp_dir(Path(args.dir), args.epic)
    return worklist.run_worklist(
        tp_dir,
        args.epic,
        strict=args.strict,
        record_iter=args.iter,
        write=True,
    )


def cmd_regen(args: argparse.Namespace) -> int:
    tp_dir = _tp_dir(Path(args.dir), args.epic)
    rc = _regenerate(tp_dir, args.epic)
    if rc != 0:
        print(f"[FAIL] Generator exit {rc}")
        return rc
    print("[OK] Regenerated artifacts")
    return 0


def cmd_check_regression(args: argparse.Namespace) -> int:
    tp_dir = _tp_dir(Path(args.dir), args.epic)
    prev = _load_history_row(tp_dir, args.prev)
    curr = _load_history_row(tp_dir, args.curr)
    if not prev or not curr:
        print(f"[FAIL] Missing history row prev={args.prev} curr={args.curr}")
        return 2
    if _score_improved(prev, curr):
        print(f"[OK] No regression: iter {args.prev} -> {args.curr}")
        print(f"  worklist_count {prev.get('worklist_count')} -> {curr.get('worklist_count')}")
        return 0
    print(f"[FAIL] Regression detected: iter {args.prev} -> {args.curr}")
    print(f"  prev={prev}")
    print(f"  curr={curr}")
    return 1


def cmd_gate(args: argparse.Namespace) -> int:
    """Strict worklist + self_check parity tail."""
    tp_dir = _tp_dir(Path(args.dir), args.epic)
    rc = worklist.run_worklist(tp_dir, args.epic, strict=True, write=True)
    if rc != 0:
        return rc
    p = subprocess.run(
        [sys.executable, str(TP_ROOT / "_tp_self_check.py"), "--epic", args.epic, "--dir", args.dir],
    )
    return p.returncode


def cmd_auto(args: argparse.Namespace) -> int:
    """Agent checklist: snapshot iter 0, score strict, print worklist slice summary."""
    tp_dir = _tp_dir(Path(args.dir), args.epic)
    if not tp_dir.is_dir():
        print(f"[FAIL] Missing epic dir: {tp_dir}")
        return 2
    _snapshot(tp_dir, args.epic, 0)
    rc = worklist.run_worklist(tp_dir, args.epic, strict=True, record_iter=0, write=True)
    wl_path = tp_dir / "refine_worklist.json"
    if wl_path.exists():
        wl = json.loads(wl_path.read_text(encoding="utf-8"))
        kinds = {}
        for f in wl.get("actionable_errors", []):
            kinds[f.get("kind", "?")] = kinds.get(f.get("kind", "?"), 0) + 1
        if kinds:
            print("[INFO] Spawn fixer subagents (parallel, one per kind):")
            for k, n in sorted(kinds.items()):
                print(f"  - {k}: {n} finding(s)")
        else:
            print("[OK] Worklist clean — present for human sign-off")
    if rc == 0:
        print("[OK] Stage 7 auto-check: structurally green")
    else:
        print("[INFO] Stage 7 auto-check: enter fixer loop (max-N=3); see tp-generator-command.mdc")
    return rc


def main() -> int:
    ap = argparse.ArgumentParser(description="/TP Stage-7 critic-refine loop driver")
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    ap.add_argument("--strict", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_snap = sub.add_parser("snapshot", help="Backup SoT + artifacts before an iteration")
    p_snap.add_argument("--iter", type=int, default=0)

    p_score = sub.add_parser("score", help="Build worklist + optional history row")
    p_score.add_argument("--iter", type=int, default=None)

    sub.add_parser("regen", help="Run _gen_<EPIC>.py")

    p_chk = sub.add_parser("check-regression", help="Compare refine_history rows")
    p_chk.add_argument("--prev", type=int, required=True)
    p_chk.add_argument("--curr", type=int, required=True)

    sub.add_parser("gate", help="Strict worklist + _tp_self_check")

    sub.add_parser("auto", help="Stage-7 agent entry: snapshot iter 0 + strict score + fixer hints")

    args = ap.parse_args()
    handlers = {
        "snapshot": cmd_snapshot,
        "score": cmd_score,
        "regen": cmd_regen,
        "check-regression": cmd_check_regression,
        "gate": cmd_gate,
        "auto": cmd_auto,
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
