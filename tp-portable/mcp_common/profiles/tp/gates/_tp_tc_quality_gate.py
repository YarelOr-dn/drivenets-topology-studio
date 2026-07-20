#!/usr/bin/env python3
"""Per-TC assertion-quality floor for /TP (refines "coverage != correctness").

Coverage gates prove a requirement is REFERENCED by a TC; this raises the floor
on whether that TC actually ASSERTS something gradeable:
  - every step has a non-empty Expected result (verify steps only; stimulus
    steps may have an empty command with '- (stimulus...)' expected)
  - at least MIN_PASS pass_criteria
  - at least MIN_STEPS steps
  - at least one verify step carries a real show/verify command
  - functional TCs (move traffic/membership) carry >=1 observable assertion

It does NOT judge semantic correctness (that stays agent/human review) - it
catches empty/º placeholder TCs that "cover" a requirement without testing it.

Usage:
    python3 _tp_tc_quality_gate.py --epic SW-211037 [--strict]
Exit 0 = all pass (or non-strict). Exit 1 = (strict) a TC fails the floor.
"""
from __future__ import annotations

from _tp_paths import default_data_dir
import argparse
import json
import re
import sys
from pathlib import Path

MIN_STEPS = 2
MIN_PASS = 2
_ASSERT = re.compile(r"\b(show|verify|expect|no |single|0%|reject|accepted|present|absent|"
                     r"deliver|withdraw|treat-as-withdraw|no core|no crash)\b", re.I)


def _floor_findings(tcs: list[dict]) -> list[tuple[str, list[str]]]:
    findings: list[tuple[str, list[str]]] = []
    for tc in tcs:
        tid = tc.get("id", "?")
        steps = tc.get("steps") or []
        pcs = tc.get("pass_criteria") or []
        issues = []
        if len(steps) < MIN_STEPS:
            issues.append(f"<{MIN_STEPS} steps")
        if len(pcs) < MIN_PASS:
            issues.append(f"<{MIN_PASS} pass_criteria")
        # verify steps must have non-empty expected + at least one real command
        has_cmd = False
        empty_expected = 0
        for s in steps:
            if not isinstance(s, dict):
                continue
            cmd = str(s.get("command", "")).strip()
            exp = str(s.get("expected", "")).strip()
            if cmd:
                has_cmd = True
            if cmd and not exp:
                empty_expected += 1
        if not has_cmd:
            issues.append("no verify command in any step")
        if empty_expected:
            issues.append(f"{empty_expected} verify step(s) with empty Expected")
        blob = " ".join([str(p) for p in pcs] + [str(s.get("expected", "")) for s in steps if isinstance(s, dict)])
        if not _ASSERT.search(blob):
            issues.append("no gradeable assertion keyword")
        if issues:
            findings.append((tid, issues))
    return findings


def collect_findings(tp_dir: Path, epic: str) -> list[dict]:
    fr_path = tp_dir / "full_result.json"
    if not fr_path.exists():
        return []
    fr = json.loads(fr_path.read_text(encoding="utf-8"))
    out: list[dict] = []
    for tid, issues in _floor_findings(fr.get("test_cases", [])):
        out.append({
            "kind": "tc-quality",
            "target_id": tid,
            "what_missing": "; ".join(issues),
            "source_ref": "_tp_tc_quality_gate",
            "suggested_action": "Raise RICH_TC steps/pass_criteria to meet assertion floor (>=2 steps, >=2 pass, verify cmd, gradeable keyword)",
            "severity": "error",
        })
    return out


def run_gate(tp_dir: Path, epic: str, *, strict: bool = False) -> int:
    fr_path = tp_dir / "full_result.json"
    if not fr_path.exists():
        print(f"[FAIL] Missing full_result.json: {fr_path}")
        return 2
    fr = json.loads(fr_path.read_text(encoding="utf-8"))
    tcs = fr.get("test_cases", [])
    findings = _floor_findings(tcs)

    print(f"\nTC assertion-quality floor -- {epic}")
    print("=" * 70)
    print(f"TCs={len(tcs)}  passing_floor={len(tcs) - len(findings)}  below_floor={len(findings)}")
    for tid, issues in findings[:30]:
        print(f"  - {tid}: {'; '.join(issues)}")
    print("=" * 70)
    if strict and findings:
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="TP per-TC assertion-quality floor")
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    tp_dir = Path(args.dir).expanduser() / args.epic
    return run_gate(tp_dir, args.epic, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
