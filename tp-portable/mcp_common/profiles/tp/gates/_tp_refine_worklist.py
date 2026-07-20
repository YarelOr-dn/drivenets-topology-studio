#!/usr/bin/env python3
"""Stage-7 worklist aggregator for /TP critic-refine loop.

Runs all gates/audits programmatically, aggregates actionable findings into
refine_worklist.json, and appends a score row to refine_history.json.

Usage:
    python3 _tp_refine_worklist.py --epic SW-211037
    python3 _tp_refine_worklist.py --epic SW-211037 --strict   # exit 1 if findings
    python3 _tp_refine_worklist.py --epic SW-211037 --record-iter 0

Exit 0 = no actionable error-severity findings (or non-strict report).
Exit 1 = (--strict) at least one error-severity finding remains.
Exit 2 = missing required artifacts.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _tp_paths import GATES_DIR as TP_ROOT, default_data_dir, resolve_mcp_root

GATES_DIR = TP_ROOT

sys.path.insert(0, str(TP_ROOT))

import _tp_must_coverage_gate as must_gate  # noqa: E402
import _tp_parity_gate as parity_gate  # noqa: E402
import _tp_scenario_coverage_gate as scov_gate  # noqa: E402
import _tp_source_completeness as source_gate  # noqa: E402
import _tp_spec_binding_gate as spec_gate  # noqa: E402
import _tp_story_requirement_audit as story_audit  # noqa: E402
import _tp_tc_quality_gate as quality_gate  # noqa: E402
import _tp_traffic_matrix_audit as traffic_audit  # noqa: E402


def _atomic_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def _scenario_score(tp_dir: Path, epic: str) -> str:
    inv_path = tp_dir / "scenario_inventory.json"
    fr_path = tp_dir / "full_result.json"
    if not inv_path.exists() or not fr_path.exists():
        return "skip"
    inv = json.loads(inv_path.read_text(encoding="utf-8"))
    fr = json.loads(fr_path.read_text(encoding="utf-8"))
    needs = [s for s in inv.get("scenarios", []) if s.get("status") == "needs-coverage"]
    covered: set[str] = set()
    for tc in fr.get("test_cases", []):
        for sid in tc.get("covers_scenarios") or []:
            covered.add(str(sid))
    mapped = sum(1 for s in needs if s.get("scenario_id") in covered)
    return f"{mapped}/{len(needs)}"


def _must_score(tp_dir: Path) -> str:
    must_path = tp_dir / "must_requirements.json"
    fr_path = tp_dir / "full_result.json"
    if not must_path.exists() or not fr_path.exists():
        return "skip"
    must_doc = json.loads(must_path.read_text(encoding="utf-8"))
    musts = must_doc.get("must_requirements") or must_doc.get("requirements") or []
    if isinstance(musts, dict):
        musts = list(musts.values())
    findings = must_gate.collect_findings(tp_dir, "")
    covered = len(musts) - len(findings)
    return f"{covered}/{len(musts)}"


def _parity_score(tp_dir: Path, epic: str) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = parity_gate.run_gate(tp_dir, epic, strict=False)
    # Count PASS/FAIL lines from captured output
    out = buf.getvalue()
    passed = out.count("[PASS]")
    failed = out.count("[FAIL]")
    total = passed + failed
    if total == 0:
        return "skip"
    return f"{passed}/{total}" if rc == 0 else f"{passed}/{total} FAIL"


def _count_e2_missing(tp_dir: Path) -> int:
    return len(traffic_audit.collect_findings(tp_dir, ""))


def _count_below_floor(tp_dir: Path) -> int:
    return len(quality_gate.collect_findings(tp_dir, ""))


def _count_story_thin(tp_dir: Path, epic: str) -> int:
    return sum(1 for f in story_audit.collect_findings(tp_dir, epic) if f.get("severity") == "warn")


def _count_story_zero(tp_dir: Path, epic: str) -> int:
    return sum(1 for f in story_audit.collect_findings(tp_dir, epic) if f.get("severity") == "error")


def _count_spec_unbound(tp_dir: Path, epic: str) -> int:
    return sum(
        1 for f in spec_gate.collect_findings(tp_dir, epic)
        if f.get("severity") == "error"
    )


def build_worklist(tp_dir: Path, epic: str) -> dict[str, Any]:
    """Aggregate findings from all gates/audits."""
    if not (tp_dir / "full_result.json").exists():
        raise FileNotFoundError(f"Missing full_result.json under {tp_dir}")

    findings: list[dict] = []
    for mod in (
        scov_gate,
        must_gate,
        traffic_audit,
        quality_gate,
        story_audit,
        source_gate,
        spec_gate,
    ):
        findings.extend(mod.collect_findings(tp_dir, epic))

    # Parity: run gate; on failure add a rollup finding (details in gate stdout when run standalone)
    buf = io.StringIO()
    with redirect_stdout(buf):
        parity_rc = parity_gate.run_gate(tp_dir, epic, strict=False)
    if parity_rc != 0:
        findings.append({
            "kind": "parity",
            "target_id": epic,
            "what_missing": "post-write parity gate has failing checks",
            "source_ref": "_tp_parity_gate",
            "suggested_action": "Fix TC count/ID/anatomy/scenario parity; run _tp_parity_gate.py for details",
            "severity": "error",
        })

    errors = [f for f in findings if f.get("severity") == "error"]
    warns = [f for f in findings if f.get("severity") == "warn"]

    summary = {
        "scenario": _scenario_score(tp_dir, epic),
        "must": _must_score(tp_dir),
        "parity": _parity_score(tp_dir, epic),
        "e2_missing": _count_e2_missing(tp_dir),
        "below_floor": _count_below_floor(tp_dir),
        "story_thin": _count_story_thin(tp_dir, epic),
        "story_zero": _count_story_zero(tp_dir, epic),
        "spec_unbound": _count_spec_unbound(tp_dir, epic),
        "worklist_count": len(errors),
        "warn_count": len(warns),
    }

    return {
        "epic": epic,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "findings": findings,
        "actionable_errors": errors,
    }


def append_history(tp_dir: Path, epic: str, *, iter_num: int, summary: dict) -> None:
    hist_path = tp_dir / "refine_history.json"
    if hist_path.exists():
        hist = json.loads(hist_path.read_text(encoding="utf-8"))
    else:
        hist = {"epic": epic, "iterations": []}
    row = {"iter": iter_num, **summary}
    # Replace same iter if re-recording
    hist["iterations"] = [r for r in hist.get("iterations", []) if r.get("iter") != iter_num]
    hist["iterations"].append(row)
    hist["iterations"].sort(key=lambda r: r.get("iter", 0))
    hist["epic"] = epic
    hist["updated_at"] = datetime.now(timezone.utc).isoformat()
    _atomic_write_json(hist_path, hist)


def run_worklist(
    tp_dir: Path,
    epic: str,
    *,
    strict: bool = False,
    record_iter: int | None = None,
    write: bool = True,
) -> int:
    try:
        wl = build_worklist(tp_dir, epic)
    except FileNotFoundError as exc:
        print(f"[FAIL] {exc}")
        return 2

    if write:
        _atomic_write_json(tp_dir / "refine_worklist.json", wl)

    s = wl["summary"]
    print(f"\nRefine worklist -- {epic}")
    print("=" * 70)
    print(
        f"scenario={s['scenario']}  must={s['must']}  parity={s['parity']}  "
        f"e2_missing={s['e2_missing']}  below_floor={s['below_floor']}  "
        f"story_zero={s['story_zero']}  story_thin={s['story_thin']}  "
        f"spec_unbound={s.get('spec_unbound', 0)}"
    )
    print(f"actionable_errors={s['worklist_count']}  warnings={s['warn_count']}")
    for f in wl["actionable_errors"][:25]:
        print(f"  [{f['kind']}] {f['target_id']}: {f['what_missing']}")
    if s["worklist_count"] > 25:
        print(f"  ... and {s['worklist_count'] - 25} more")
    print("=" * 70)

    if record_iter is not None:
        append_history(tp_dir, epic, iter_num=record_iter, summary=s)
        print(f"[INFO] Recorded iter {record_iter} to refine_history.json")

    if strict and s["worklist_count"] > 0:
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="/TP Stage-7 refine worklist")
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--record-iter", type=int, default=None, help="Append summary row to refine_history.json")
    ap.add_argument("--no-write", action="store_true", help="Report only; do not write refine_worklist.json")
    args = ap.parse_args()
    tp_dir = Path(args.dir).expanduser() / args.epic
    return run_worklist(
        tp_dir,
        args.epic,
        strict=args.strict,
        record_iter=args.record_iter,
        write=not args.no_write,
    )


if __name__ == "__main__":
    sys.exit(main())
