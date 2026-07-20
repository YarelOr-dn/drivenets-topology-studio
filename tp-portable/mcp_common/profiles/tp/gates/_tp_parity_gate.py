#!/usr/bin/env python3
"""TP Post-Write Parity Gate -- the canonical /TP self-check.

Runs the 5 invariants from /TP.md "Post-Write Parity Gate" against any
TP folder. Exit 0 = all checks pass; exit 1 = at least one FAIL.

Usage:
    python3 _tp_parity_gate.py --epic SW-228552
    python3 _tp_parity_gate.py --epic SW-228552 --dir ~/SCALER/TEST/tp

Invariants (FAIL on red):
  1. TC count parity: full_result == manifest == markdown unique TC IDs
  2. TC ID set parity: full_result and manifest share the exact same id set
  3a. Local-anchor health: every defined local rule_anchor is referenced
  4. Markdown TC presence: every full_result TC ID appears in markdown
  5. No leftover .tmp files (would indicate partial atomic write)
  7. Rich anatomy: every TC is RICH_TC-styled (rich + node-scoped steps);
     legacy plans without any rich signal degrade to INFO-skip
  8. Scenario coverage closed: every needs-coverage inventory item mapped
     via TC covers_scenarios[] (INFO-skip when no scenario_inventory.json)

INFO (always PASS, emits visibility metric):
  3b. External reference inventory: refs not in local rule_anchors are
      treated as upstream (e.g., from tp-generator-command.mdc) and
      allowed without local resolution. The gate just emits the count.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from _tp_paths import default_data_dir

# Resolve Jira keys through the SAME contract the /TEST selector uses, so the
# parity gate's coverage check can never drift from how /TEST matches TCs.
# portable: mcp_common on PYTHONPATH
try:
    from mcp_common.profiles.test import tp_traceability as _tt
except Exception:  # contract unavailable -> coverage check degrades to INFO-skip
    _tt = None


def run_gate(tp_dir: Path, epic: str, strict: bool = False) -> int:
    fr_path = tp_dir / "full_result.json"
    mf_path = tp_dir / "manifest.json"
    md_path = tp_dir / f"test_plan_{epic}.md"

    for p in (fr_path, mf_path, md_path):
        if not p.exists():
            print(f"[FAIL] Missing artifact: {p}")
            return 2

    fr = json.loads(fr_path.read_text())
    mf = json.loads(mf_path.read_text())
    md = md_path.read_text()

    fr_tcs = fr.get("test_cases", [])
    mf_tcs = mf.get("test_cases", [])
    fr_ids = {tc["id"] for tc in fr_tcs}
    mf_ids = {tc["id"] for tc in mf_tcs}

    # Support both historical ID-first headings:
    #   #### TC-FOO-01 - Human readable name
    # and the newer title-first presentation:
    #   #### Human readable name
    #   _Test ID: `TC-FOO-01`_
    md_tc_ids = set(re.findall(r"^#### (TC-[A-Za-z0-9_-]+)", md, flags=re.M))
    md_tc_ids.update(re.findall(r"^_Test ID: `(TC-[A-Za-z0-9_-]+)`_$", md, flags=re.M))

    local_anchors = set(mf.get("tp_rules", {}).get("rule_anchors", {}).keys())
    all_refs = set()
    for tc in fr_tcs:
        for ref in (tc.get("covers_rubric_rules") or []):
            all_refs.add(ref)
    local_refs = {r for r in all_refs if r.startswith("tp:")}
    external_refs = all_refs - local_refs

    results = []

    def chk(name, ok, detail=""):
        results.append((name, ok, detail))

    chk(
        "1. TC count parity (full_result == manifest == markdown unique)",
        len(fr_tcs) == len(mf_tcs) == len(md_tc_ids),
        f"full_result={len(fr_tcs)} manifest={len(mf_tcs)} markdown={len(md_tc_ids)}",
    )

    chk(
        "2. TC ID set parity (full_result == manifest)",
        fr_ids == mf_ids,
        f"only-in-full={sorted(fr_ids - mf_ids)[:3]} "
        f"only-in-manifest={sorted(mf_ids - fr_ids)[:3]}",
    )

    dead_anchors = local_anchors - local_refs
    chk(
        "3a. Local-anchor health (FAIL): every defined local anchor referenced",
        not dead_anchors,
        f"dead_anchors={sorted(dead_anchors)[:5]}",
    )

    upstream_tp_refs = local_refs - local_anchors
    chk(
        "3b. External reference inventory (INFO): upstream refs allowed",
        True,
        f"upstream_tp:*={len(upstream_tp_refs)} other_namespaces={len(external_refs)}",
    )

    missing_in_md = fr_ids - md_tc_ids
    chk(
        "4. Every full_result TC ID present in markdown",
        not missing_in_md,
        f"missing_in_markdown={sorted(missing_in_md)[:5]}",
    )

    tmp_files = list(tp_dir.glob(".*.tmp"))
    chk(
        "5. No leftover .tmp files in TP folder",
        not tmp_files,
        f"leftovers={[p.name for p in tmp_files]}",
    )

    # 6. Jira coverage: every TC carries a Test Category key + Testing Task key
    #    (resolved via the shared traceability contract), or is explicitly waived.
    #    This is the /TP-side mirror of the /TEST seam fix: an unstamped TC cannot
    #    be imported by jira_category_key. INFO by default; --strict makes it FAIL.
    tp_rules = mf.get("tp_rules", {}) if isinstance(mf.get("tp_rules"), dict) else {}
    waived = {str(w) for w in (tp_rules.get("jira_coverage_waiver") or [])}
    unlinked = []
    if _tt is None:
        chk("6. Jira coverage (INFO): contract unavailable - check skipped", True,
            "mcp_common.profiles.test.tp_traceability not importable")
    else:
        for tc in fr_tcs:
            tcid = tc.get("id")
            if tcid in waived:
                continue
            if not _tt.case_is_jira_linked(tc):
                unlinked.append(tcid)
        cov_ok = (not unlinked) if strict else True
        chk(
            "6. Jira coverage (FAIL): every TC has category+task key or waiver" if strict
            else "6. Jira coverage (INFO): TCs linked to a Jira category+task key",
            cov_ok,
            f"unlinked={len(unlinked)}/{len(fr_tcs)} waived={len(waived)} "
            f"sample={sorted(x for x in unlinked if x)[:5]}",
        )

    # 7. Rich anatomy: EVERY TC must be authored in the RICH_TC style
    #    (tp:every-tc-rich-anatomy) - rich=True with node-scoped procedure steps
    #    (Dev names the acting node, never a bare '-'). Legacy-safe: if the plan
    #    carries NO rich signal at all (pre-standard), emit INFO-skip instead of
    #    failing retroactively; regenerate with the RICH_TC template to enforce.
    def _step_dev_ok(step):
        if not isinstance(step, dict):
            return False
        return str(step.get("dev", "")).strip() not in ("", "-")

    has_rich_signal = any(tc.get("rich") for tc in fr_tcs) or any(
        _step_dev_ok(s) for tc in fr_tcs for s in (tc.get("steps") or [])
    )
    if not has_rich_signal:
        chk("7. Rich anatomy (INFO): legacy plan without rich signal - not assessed", True,
            "no rich/dev fields present; regenerate with the RICH_TC template to enforce")
    else:
        not_rich = []
        for tc in fr_tcs:
            steps = tc.get("steps") or []
            if (not tc.get("rich")) or (not steps) or any(not _step_dev_ok(s) for s in steps):
                not_rich.append(tc.get("id"))
        chk(
            "7. Rich anatomy (FAIL): every TC RICH_TC-styled + node-scoped steps",
            not not_rich,
            f"not_rich_styled={sorted(x for x in not_rich if x)[:8]} ({len(not_rich)}/{len(fr_tcs)})",
        )

    # 8. Scenario coverage closure (needs-coverage -> >=1 TC covers_scenarios ref).
    inv_path = tp_dir / "scenario_inventory.json"
    if not inv_path.exists():
        chk(
            "8. Scenario coverage closed (INFO): no scenario_inventory.json - skipped",
            True,
            "run _tp_scenario_extract.py during Stage 1e to enable",
        )
    else:
        try:
            from _tp_scenario_coverage_gate import run_gate as _scov_gate  # noqa: WPS433
        except ImportError:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from _tp_scenario_coverage_gate import run_gate as _scov_gate  # noqa: WPS433
        scov_rc = _scov_gate(tp_dir, epic, verbose=False)
        inv = json.loads(inv_path.read_text())
        n_need = sum(1 for s in inv.get("scenarios", []) if s.get("status") == "needs-coverage")
        covered_ids = set()
        for tc in fr_tcs:
            for sid in tc.get("covers_scenarios") or []:
                covered_ids.add(str(sid))
        n_mapped = sum(
            1 for s in inv.get("scenarios", [])
            if s.get("status") == "needs-coverage" and s.get("scenario_id") in covered_ids
        )
        chk(
            "8. Scenario coverage closed (FAIL): needs-coverage scenarios mapped",
            scov_rc == 0,
            f"mapped={n_mapped}/{n_need} distinct_tc_refs={len(covered_ids)}",
        )

    # 9. Topology illustration present for every TC that declares a topology_ref
    #    (per-test topology accuracy). A future epic that ships a TC with a
    #    topology_ref but no rendered "Topology Illustration" block FAILS the
    #    mandatory gate. INFO-skip for legacy plans where no TC carries one.
    tcs_with_topo = [tc for tc in fr_tcs if str(tc.get("topology_ref") or "").strip()]
    # The full test_plan markdown renders the per-TC illustration as a bold
    # heading "**Topology (Tn - ...):**"; the per-TC chat/jira render uses a
    # "### Topology Illustration" heading. Accept either form.
    illus_headings = (
        len(re.findall(r"(?mi)^#+\s*Topology Illustration", md))
        + len(re.findall(r"(?m)^\*\*Topology \(", md))
    )
    if not tcs_with_topo:
        chk("9. Topology illustration (INFO): no TC declares a topology_ref - skipped",
            True, "assign a topology_ref per TC to enable per-test topology art")
    else:
        chk(
            "9. Topology illustration present per topology-bearing TC (FAIL)",
            illus_headings >= len(tcs_with_topo),
            f"illustrations={illus_headings} topology_tcs={len(tcs_with_topo)}",
        )

    print(f"\nTP Post-Write Parity Gate -- {epic}")
    print("=" * 70)
    fail = 0
    for name, ok, detail in results:
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {name}")
        if not ok and detail:
            print(f"         {detail}")
        elif "INFO" in name and detail:
            print(f"         {detail}")
    print("=" * 70)
    fail = sum(1 for _, ok, _ in results if not ok)
    passed = len(results) - fail
    print(f"Result: {passed}/{len(results)} checks passed")
    print(
        f"Anchors: {len(local_anchors)} local | "
        f"{len(local_refs)} local refs | "
        f"{len(external_refs)} external refs (allowed)"
    )
    print(
        f"TCs:     {len(fr_tcs)} full_result | "
        f"{len(mf_tcs)} manifest | {len(md_tc_ids)} markdown"
    )
    return 0 if fail == 0 else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--epic", required=True, help="Epic ID (e.g., SW-228552)")
    ap.add_argument(
        "--dir",
        default=default_data_dir(),
        help="Parent dir containing per-epic folders (default: ~/SCALER/TEST/tp)",
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Make check 6 (Jira coverage) a FAIL on unwaived gaps (default: INFO).",
    )
    args = ap.parse_args()
    tp_dir = Path(args.dir).expanduser() / args.epic
    sys.exit(run_gate(tp_dir, args.epic, strict=args.strict))


if __name__ == "__main__":
    main()
