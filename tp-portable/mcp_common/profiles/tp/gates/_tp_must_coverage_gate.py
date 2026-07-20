#!/usr/bin/env python3
"""MUST traceability gate for /TP artifacts.

Ensures every MUST/SHALL/required statement in must_requirements.json maps to
at least one TC in full_result.json.

Usage:
    python3 _tp_must_coverage_gate.py --epic SW-228552
    python3 _tp_must_coverage_gate.py --epic SW-228552 --dir ~/SCALER/TEST/tp

Exit 0 = all MUSTs covered (or no must_requirements.json -> INFO skip).
Exit 1 = at least one uncovered MUST.
Exit 2 = missing required artifacts.
"""

from __future__ import annotations

from _tp_paths import default_data_dir
import argparse
import json
import re
import sys
from pathlib import Path


def _tc_text_blob(tc: dict) -> str:
    parts: list[str] = [
        str(tc.get("id", "")),
        str(tc.get("name", "")),
        str(tc.get("description", "")),
        str(tc.get("purpose", "")),
    ]
    for step in tc.get("steps") or []:
        if isinstance(step, dict):
            parts.extend(str(v) for v in step.values())
        else:
            parts.append(str(step))
    for pc in tc.get("pass_criteria") or []:
        parts.append(str(pc))
    for cmd in tc.get("verification_commands") or []:
        if isinstance(cmd, dict):
            parts.append(str(cmd.get("command", "")))
        else:
            parts.append(str(cmd))
    return " ".join(parts).lower()


def _must_covered(must: dict, tc_blobs: list[str]) -> bool:
    must_id = str(must.get("id", "")).lower()
    text = str(must.get("text", "")).lower()
    keywords = [w for w in re.split(r"\W+", text) if len(w) >= 5][:8]
    for blob in tc_blobs:
        if must_id and must_id in blob:
            return True
        if text and text[:80] in blob:
            return True
        if keywords and sum(1 for k in keywords if k in blob) >= max(2, len(keywords) // 2):
            return True
    return False


def collect_findings(tp_dir: Path, epic: str) -> list[dict]:
    fr_path = tp_dir / "full_result.json"
    must_path = tp_dir / "must_requirements.json"
    if not fr_path.exists() or not must_path.exists():
        return []
    fr = json.loads(fr_path.read_text())
    must_doc = json.loads(must_path.read_text())
    musts = must_doc.get("must_requirements") or must_doc.get("requirements") or []
    if isinstance(musts, dict):
        musts = list(musts.values())
    blobs = [_tc_text_blob(tc) for tc in fr.get("test_cases", [])]
    out: list[dict] = []
    for i, must in enumerate(musts):
        if not isinstance(must, dict):
            must = {"id": f"MUST-{i+1:03d}", "text": str(must)}
        if not _must_covered(must, blobs):
            mid = must.get("id", f"MUST-{i+1:03d}")
            out.append({
                "kind": "must-coverage",
                "target_id": str(mid),
                "what_missing": "MUST requirement not covered by any TC",
                "source_ref": str(must.get("source", "must_requirements.json"))[:120],
                "suggested_action": "Add or extend TC to cover this MUST",
                "severity": "error",
            })
    return out


def run_gate(tp_dir: Path, epic: str) -> int:
    fr_path = tp_dir / "full_result.json"
    must_path = tp_dir / "must_requirements.json"

    if not fr_path.exists():
        print(f"[FAIL] Missing full_result.json: {fr_path}")
        return 2

    if not must_path.exists():
        print(f"[INFO] No must_requirements.json for {epic}; MUST gate skipped")
        return 0

    fr = json.loads(fr_path.read_text())
    must_doc = json.loads(must_path.read_text())
    musts = must_doc.get("must_requirements") or must_doc.get("requirements") or []
    if isinstance(musts, dict):
        musts = list(musts.values())

    tcs = fr.get("test_cases", [])
    blobs = [_tc_text_blob(tc) for tc in tcs]

    uncovered: list[dict] = []
    for i, must in enumerate(musts):
        if not isinstance(must, dict):
            must = {"id": f"MUST-{i+1:03d}", "text": str(must)}
        if not _must_covered(must, blobs):
            uncovered.append(must)

    covered = len(musts) - len(uncovered)
    print(f"[INFO] MUST coverage for {epic}: {covered}/{len(musts)} covered")

    if uncovered:
        print("[FAIL] Uncovered MUST requirements:")
        for m in uncovered[:20]:
            mid = m.get("id", "?")
            snippet = str(m.get("text", ""))[:120]
            print(f"  - {mid}: {snippet}")
        if len(uncovered) > 20:
            print(f"  ... and {len(uncovered) - 20} more")
        return 1

    print("[PASS] All MUST requirements have TC coverage")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="TP MUST traceability gate")
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    args = ap.parse_args()
    tp_dir = Path(args.dir) / args.epic
    return run_gate(tp_dir, args.epic)


if __name__ == "__main__":
    sys.exit(main())
