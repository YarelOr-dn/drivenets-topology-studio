#!/usr/bin/env python3
"""MC traffic-flow matrix audit for /TP (refines "coverage != correctness" for
forwarding). Every E2 (DP-forwarding) TC MUST assert BOTH:
  - POSITIVE delivery: reaches every interested OIF (single copy / 0% loss), AND
  - NEGATIVE no-leak: nothing to non-interested ports / non-SMET peers / no dup.
Optionally the IMET/BUM gate + mrouter delivery.

E2 TCs are identified by full_result exec_tier == 'E2' (set by the generator),
falling back to a keyword heuristic if the field is absent.

Usage:
    python3 _tp_traffic_matrix_audit.py --epic SW-211037
    python3 _tp_traffic_matrix_audit.py --epic SW-211037 --strict   # nonzero on gaps

Exit 0 = every E2 TC has both positive + negative (or --strict off).
Exit 1 = (strict) an E2 TC missing a side.
"""
from __future__ import annotations

from _tp_paths import default_data_dir
import argparse
import json
import re
import sys
from pathlib import Path

_POS = re.compile(r"deliver|single[- ]copy|received by|0% loss|forwarded to|reaches|one copy per", re.I)
_NEG = re.compile(r"no flood|not flood|non-interested|uninterested|not deliver|no deliver|"
                  r"excluded|no duplicat|nothing|non-member|non-smet|black-hole|not to", re.I)
_E2 = re.compile(r"0% loss|single[- ]copy|replicat|forwarding-table|delivered|delivery|"
                 r"black-hole|no flood|one copy|duplicat|egress-ac|show interfaces", re.I)


def _blob(tc: dict) -> str:
    parts = [tc.get("purpose", ""), tc.get("objective", "")]
    for s in tc.get("steps") or []:
        if isinstance(s, dict):
            parts += [str(s.get("action", "")), str(s.get("expected", ""))]
        else:
            parts.append(str(s))
    parts += [str(x) for x in (tc.get("pass_criteria") or [])]
    return " ".join(parts)


def _is_e2(tc: dict, blob: str) -> bool:
    et = tc.get("exec_tier")
    if et:
        return et == "E2"
    return bool(_E2.search(blob))


def _audit_miss(tp_dir: Path) -> tuple[int, int, list[tuple[str, str, str]]]:
    fr_path = tp_dir / "full_result.json"
    if not fr_path.exists():
        raise FileNotFoundError(f"Missing full_result.json: {fr_path}")
    fr = json.loads(fr_path.read_text(encoding="utf-8"))
    tcs = fr.get("test_cases", [])

    e2, both, miss = 0, 0, []
    for tc in tcs:
        blob = _blob(tc)
        if not _is_e2(tc, blob):
            continue
        e2 += 1
        p, n = bool(_POS.search(blob)), bool(_NEG.search(blob))
        if p and n:
            both += 1
        else:
            miss.append((tc.get("id"), "pos" if not p else "", "neg" if not n else ""))
    return e2, both, miss


def collect_findings(tp_dir: Path, epic: str) -> list[dict]:
    """Return worklist rows for E2 TCs missing positive/negative flow assertions."""
    try:
        _e2, _both, miss = _audit_miss(tp_dir)
    except FileNotFoundError:
        return []
    out: list[dict] = []
    for tid, mp, mn in miss:
        if mp:
            out.append({
                "kind": "traffic-matrix",
                "target_id": tid,
                "what_missing": "positive delivery assertion (reach interested OIF, 0% loss)",
                "source_ref": f"exec_tier=E2; _tp_traffic_matrix_audit",
                "suggested_action": "Add a datapath step + pass criterion asserting delivery to interested OIF(s)",
                "severity": "error",
            })
        if mn:
            out.append({
                "kind": "traffic-matrix",
                "target_id": tid,
                "what_missing": "negative no-leak assertion (non-interested ports / no duplicate)",
                "source_ref": f"exec_tier=E2; _tp_traffic_matrix_audit",
                "suggested_action": "Add a step + pass criterion asserting no flood to non-interested ports",
                "severity": "error",
            })
    return out


def run_audit(tp_dir: Path, epic: str, *, strict: bool = False) -> int:
    fr_path = tp_dir / "full_result.json"
    if not fr_path.exists():
        print(f"[FAIL] Missing full_result.json: {fr_path}")
        return 2
    try:
        e2, both, miss = _audit_miss(tp_dir)
    except FileNotFoundError as exc:
        print(f"[FAIL] {exc}")
        return 2

    print(f"\nMC traffic-flow matrix audit -- {epic}")
    print("=" * 70)
    print(f"E2 (DP-forwarding) TCs={e2}  with positive+negative={both}  missing={len(miss)}")
    for tid, mp, mn in miss:
        need = [x for x in (mp, mn) if x]
        print(f"  - {tid}: missing {need}")
    print("=" * 70)
    if strict and miss:
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="MC traffic-flow matrix audit")
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    tp_dir = Path(args.dir).expanduser() / args.epic
    return run_audit(tp_dir, args.epic, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
