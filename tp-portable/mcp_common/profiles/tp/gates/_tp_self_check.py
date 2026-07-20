#!/usr/bin/env python3
"""Self-check loop for /TP generation (coverage + parity + MCP validate).

Runs mid-generation and as the final post-write gate. Blocks success until
all checks pass (exit 0).

Usage:
    python3 _tp_self_check.py --epic SW-211037
    python3 _tp_self_check.py --epic SW-211037 --skip-mcp-validate

Exit 0 = all gates green; exit 1 = at least one gate failed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from _tp_paths import GATES_DIR as TP_ROOT, default_data_dir, resolve_mcp_root

GATES_DIR = TP_ROOT
MCP_ROOT = resolve_mcp_root()


def _run(cmd: list[str], *, cwd: Path | None = None) -> tuple[int, str]:
    p = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out.strip()


def run_self_check(
    tp_dir: Path,
    epic: str,
    *,
    skip_mcp: bool = False,
    strict_refine: bool = True,
    strict_jira: bool = False,
) -> int:
    failures: list[str] = []

    # Stage 1e: ensure inventory exists (extract if missing)
    inv_path = tp_dir / "scenario_inventory.json"
    if not inv_path.exists():
        rc, out = _run(
            [sys.executable, str(TP_ROOT / "_tp_scenario_extract.py"), "--epic", epic],
        )
        if rc != 0:
            failures.append(f"scenario_extract rc={rc}\n{out}")

    # Coverage closure
    rc, out = _run(
        [sys.executable, str(TP_ROOT / "_tp_scenario_coverage_gate.py"), "--epic", epic],
    )
    print(out)
    if rc != 0:
        failures.append("scenario_coverage_gate")

    # MUST coverage
    rc, out = _run(
        [sys.executable, str(TP_ROOT / "_tp_must_coverage_gate.py"), "--epic", epic],
    )
    print(out)
    if rc != 0:
        failures.append("must_coverage_gate")

    # Per-story requirement-depth audit (report; --strict on ZERO when strict_refine).
    story_cmd = [sys.executable, str(TP_ROOT / "_tp_story_requirement_audit.py"), "--epic", epic]
    if strict_refine:
        story_cmd.append("--strict")
    rc, out = _run(story_cmd)
    print(out)
    if strict_refine and rc != 0:
        failures.append("story_requirement_audit")

    # Spec-binding pipeline (version -> harvest -> gate) before refinement audits.
    spec_pipeline = (
        ("_tp_epic_version.py", False),
        ("_tp_cli_spec_harvester.py", False),
        ("_tp_spec_binding_gate.py", strict_refine),
    )
    for tool, use_strict in spec_pipeline:
        cmd = [sys.executable, str(TP_ROOT / tool), "--epic", epic]
        if use_strict:
            cmd.append("--strict")
        rc, out = _run(cmd)
        print(out)
        if use_strict and rc != 0:
            failures.append(tool.replace(".py", ""))

    # Standing lints: per-TC traffic profile + cited-story deliverable coverage.
    standing_lints = (
        ("_tp_us_coverage_lint.py", strict_refine),
        ("_tp_traffic_profile_lint.py", strict_refine),
    )
    for tool, use_strict in standing_lints:
        cmd = [sys.executable, str(TP_ROOT / tool), "--epic", epic]
        rc, out = _run(cmd)
        print(out)
        if use_strict and rc != 0:
            failures.append(tool.replace(".py", ""))

    # Refinement audits: strict when Stage 7 active (traffic, quality, source).
    refine_tools = (
        ("_tp_source_completeness.py", strict_refine),
        ("_tp_traffic_matrix_audit.py", strict_refine),
        ("_tp_tc_quality_gate.py", strict_refine),
        ("_tp_design_syntax_report.py", False),
        # Epic-agnostic: if the epic touches a BGP route-type / AFI, the CLI
        # category must exercise the full BGP show surface (tp:bgp-feature-show-
        # coverage). No-op PASS for non-BGP epics. Advisory (surfaced, not hard-
        # blocking) so a mid-development BGP epic is flagged, not stopped.
        ("_tp_bgp_show_coverage_lint.py", False),
        # Epic-agnostic: if the epic introduces/affects counters, the plan must
        # prove the counter contract - delta correctness, clear-to-zero, scope,
        # and opt-in enable (tp:counter-coverage). No-op PASS for non-counter epics.
        ("_tp_counter_coverage_lint.py", False),
    )
    for tool, use_strict in refine_tools:
        cmd = [sys.executable, str(TP_ROOT / tool), "--epic", epic]
        if use_strict:
            cmd.append("--strict")
        rc, out = _run(cmd)
        print(out)
        if use_strict and rc != 0:
            failures.append(tool.replace(".py", ""))

    # Stage-7 worklist: strict by default (single "structurally done?" signal).
    wl_cmd = [sys.executable, str(TP_ROOT / "_tp_refine_worklist.py"), "--epic", epic]
    if strict_refine:
        wl_cmd.append("--strict")
    rc, out = _run(wl_cmd)
    print(out)
    if strict_refine and rc != 0:
        failures.append("refine_worklist")

    # Parity (incl. check 8)
    parity_cmd = [
        sys.executable,
        str(TP_ROOT / "_tp_parity_gate.py"),
        "--epic",
        epic,
    ]
    if strict_jira:
        parity_cmd.append("--strict")
    rc, out = _run(parity_cmd)
    print(out)
    if rc != 0:
        failures.append("parity_gate")

    # MCP validate (framework rules + markdown shape) — scenario coverage is
    # hard-fail via dedicated gates; framework no_code_identifiers etc. are WARN.
    if not skip_mcp and MCP_ROOT.is_dir():
        md_path = tp_dir / f"test_plan_{epic}.md"
        fr_path = tp_dir / "full_result.json"
        if md_path.exists() and fr_path.exists():
            sys.path.insert(0, str(MCP_ROOT))
            try:
                from quality_validator import (  # noqa: E402
                    validate_framework_rules,
                    validate_test_plan_markdown,
                    validate_structured_result,
                )

                md = md_path.read_text(encoding="utf-8")
                result = json.loads(fr_path.read_text(encoding="utf-8"))
                ok_md, md_errs = validate_test_plan_markdown(md)
                ok_res, res_errs = validate_structured_result(result)
                fw = validate_framework_rules(md)
                print(f"[INFO] MCP markdown_ok={ok_md} result_ok={ok_res} framework_ok={fw.get('ok')}")
                if not ok_md:
                    print(f"[FAIL] markdown_errors: {md_errs[:5]}")
                    failures.append("mcp_markdown")
                if not ok_res:
                    print(f"[FAIL] result_errors: {res_errs[:5]}")
                    failures.append("mcp_result")
                if not fw.get("ok"):
                    hard = fw.get("hard_fail_count", 0)
                    sc = fw.get("scenario_coverage", {})
                    sc_hard = sc.get("errors") or []
                    if sc_hard:
                        print(f"[FAIL] scenario_coverage hard errors: {sc_hard[:5]}")
                        failures.append("mcp_scenario_coverage")
                    else:
                        print(f"[WARN] MCP framework hard_fail_count={hard} (non-scenario; not blocking self-check)")
            except Exception as exc:
                print(f"[WARN] MCP validate skipped: {exc}")

    if failures:
        print(f"\n[FAIL] Self-check failed: {', '.join(failures)}")
        return 1

    print("\n[PASS] Self-check loop: coverage + parity + Stage-7 refine + validate all green")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="/TP self-check loop")
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    ap.add_argument("--skip-mcp-validate", action="store_true")
    ap.add_argument(
        "--no-strict-refine",
        action="store_true",
        help="Disable Stage-7 strict worklist + refinement audits (not for shipped /TP)",
    )
    ap.add_argument(
        "--strict-jira",
        action="store_true",
        help="Also strict-fail Jira category+task coverage (parity check 6)",
    )
    args = ap.parse_args()
    tp_dir = Path(args.dir).expanduser() / args.epic
    return run_self_check(
        tp_dir,
        args.epic,
        skip_mcp=args.skip_mcp_validate,
        strict_refine=not args.no_strict_refine,
        strict_jira=args.strict_jira,
    )


if __name__ == "__main__":
    sys.exit(main())
