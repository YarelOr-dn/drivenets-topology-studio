#!/usr/bin/env python3
"""Scenario coverage closure gate for /TP artifacts.

Every scenario in scenario_inventory.json with status=needs-coverage must be
referenced by >=1 TC covers_scenarios[] entry in full_result.json.
Every waived scenario must carry a waive_reason.

Usage:
    python3 _tp_scenario_coverage_gate.py --epic SW-211037
    python3 _tp_scenario_coverage_gate.py --epic SW-211037 --dir ~/SCALER/TEST/tp

Exit 0 = all needs-coverage scenarios mapped (or no inventory -> INFO skip).
Exit 1 = uncovered needs-coverage scenario(s) or invalid waived entry.
Exit 2 = missing required artifacts when inventory exists.
"""

from __future__ import annotations

from _tp_paths import default_data_dir
import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _collect_tc_coverage(full_result: dict[str, Any]) -> set[str]:
    covered: set[str] = set()
    for tc in full_result.get("test_cases") or []:
        for sid in tc.get("covers_scenarios") or []:
            if sid:
                covered.add(str(sid))
    return covered


def _uncovered_scenarios(tp_dir: Path) -> tuple[list[dict], list[dict], list[dict]]:
    inv_path = tp_dir / "scenario_inventory.json"
    fr_path = tp_dir / "full_result.json"
    if not inv_path.exists() or not fr_path.exists():
        return [], [], []
    inv = json.loads(inv_path.read_text(encoding="utf-8"))
    fr = json.loads(fr_path.read_text(encoding="utf-8"))
    scenarios = inv.get("scenarios") or []
    if not scenarios:
        return [], [], []
    covered = _collect_tc_coverage(fr)
    needs = [s for s in scenarios if s.get("status") == "needs-coverage"]
    waived = [s for s in scenarios if s.get("status") == "waived"]
    bad_waived = [s for s in waived if not str(s.get("waive_reason") or "").strip()]
    uncovered = [s for s in needs if s["scenario_id"] not in covered]
    return uncovered, bad_waived, needs


def collect_findings(tp_dir: Path, epic: str) -> list[dict]:
    uncovered, bad_waived, _needs = _uncovered_scenarios(tp_dir)
    out: list[dict] = []
    for s in bad_waived:
        sid = s.get("scenario_id", "?")
        out.append({
            "kind": "scenario-coverage",
            "target_id": sid,
            "what_missing": "waived scenario missing waive_reason",
            "source_ref": "scenario_inventory.json",
            "suggested_action": "Add waive_reason or change status to needs-coverage",
            "severity": "error",
        })
    for s in uncovered:
        sid = s.get("scenario_id", "?")
        out.append({
            "kind": "scenario-coverage",
            "target_id": sid,
            "what_missing": "needs-coverage scenario not referenced by any TC",
            "source_ref": str(s.get("source", "scenario_inventory")),
            "suggested_action": "Add TC with covers_scenarios[] ref or waive with reason",
            "severity": "error",
        })
    return out


def run_gate(tp_dir: Path, epic: str, *, verbose: bool = True) -> int:
    inv_path = tp_dir / "scenario_inventory.json"
    fr_path = tp_dir / "full_result.json"

    if not inv_path.exists():
        if verbose:
            print(f"[INFO] No scenario_inventory.json for {epic}; scenario coverage gate skipped")
        return 0

    if not fr_path.exists():
        print(f"[FAIL] Missing full_result.json: {fr_path}")
        return 2

    inv = json.loads(inv_path.read_text(encoding="utf-8"))
    fr = json.loads(fr_path.read_text(encoding="utf-8"))
    scenarios = inv.get("scenarios") or []
    if not scenarios:
        if verbose:
            print(f"[INFO] Empty scenario inventory for {epic}; gate skipped (graceful degrade)")
        return 0

    covered = _collect_tc_coverage(fr)
    needs = [s for s in scenarios if s.get("status") == "needs-coverage"]
    waived = [s for s in scenarios if s.get("status") == "waived"]

    bad_waived = [s for s in waived if not str(s.get("waive_reason") or "").strip()]
    uncovered = [s for s in needs if s["scenario_id"] not in covered]

    mapped = len(needs) - len(uncovered)
    if verbose:
        print(
            f"[INFO] Scenario coverage for {epic}: "
            f"{mapped}/{len(needs)} needs-coverage mapped; "
            f"{len(waived)} waived; {len(covered)} distinct TC refs"
        )

    fail = False
    if bad_waived:
        fail = True
        print("[FAIL] Waived scenarios missing waive_reason:")
        for s in bad_waived[:15]:
            print(f"  - {s.get('scenario_id')}: {str(s.get('text', ''))[:80]}")
        if len(bad_waived) > 15:
            print(f"  ... and {len(bad_waived) - 15} more")

    if uncovered:
        fail = True
        print("[FAIL] Uncovered needs-coverage scenarios:")
        for s in uncovered[:25]:
            sid = s.get("scenario_id", "?")
            snippet = str(s.get("text", ""))[:100]
            grp = s.get("group", "")
            print(f"  - {sid} ({grp}): {snippet}")
        if len(uncovered) > 25:
            print(f"  ... and {len(uncovered) - 25} more")

    if fail:
        return 1

    if verbose:
        print("[PASS] All needs-coverage scenarios mapped; waived entries have reasons")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="TP scenario coverage closure gate")
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    ap.add_argument("-q", "--quiet", action="store_true")
    args = ap.parse_args()
    tp_dir = Path(args.dir).expanduser() / args.epic
    return run_gate(tp_dir, args.epic, verbose=not args.quiet)


if __name__ == "__main__":
    sys.exit(main())
