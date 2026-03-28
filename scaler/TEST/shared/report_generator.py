#!/usr/bin/env python3
"""
Unified local report generator for DNOS test automation.

Produces a single FULL_REPORT.md combining all scenarios, counters,
events, health checks, regressions, and repro steps.

LOCAL ONLY -- never writes to Jira, Confluence, or any external system.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


@dataclass
class ScenarioReport:
    """Report data for one scenario."""
    scenario_id: str
    scenario_name: str = ""
    verdict: str = "PENDING"
    duration_sec: float = 0.0
    layer_verdicts: Dict[str, str] = field(default_factory=dict)
    counter_diff: Optional[Dict[str, Any]] = None
    event_audit: Optional[Dict[str, Any]] = None
    health_check: Optional[Dict[str, Any]] = None
    cross_layer: Optional[Dict[str, Any]] = None
    poll_data: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    repro_steps: str = ""
    notes: List[str] = field(default_factory=list)


@dataclass
class FullReport:
    """Complete test run report."""
    test_id: str
    test_name: str = ""
    device: str = ""
    image_version: str = ""
    started_at: str = ""
    completed_at: str = ""
    overall_verdict: str = "PENDING"
    scenarios: List[ScenarioReport] = field(default_factory=list)
    config_baseline: Optional[Dict[str, Any]] = None
    regression: Optional[Dict[str, Any]] = None
    health_before: Optional[Dict[str, Any]] = None
    health_after: Optional[Dict[str, Any]] = None
    learning_updates: List[str] = field(default_factory=list)
    cleanup_result: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def generate_full_report(report: FullReport, output_dir: Path) -> Path:
    """Generate FULL_REPORT.md and return its path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / "FULL_REPORT.md"

    lines: List[str] = []
    _header(lines, report)
    _verdict_summary(lines, report)
    _scenario_details(lines, report)
    _config_baseline_section(lines, report)
    _health_section(lines, report)
    _regression_section(lines, report)
    _cleanup_section(lines, report)
    _learning_section(lines, report)
    _footer(lines, report)

    md_path.write_text("\n".join(lines))

    # Also write structured JSON
    json_path = output_dir / "FULL_REPORT.json"
    json_path.write_text(json.dumps(_report_to_dict(report), indent=2))

    return md_path


def generate_summary_md(report: FullReport) -> str:
    """Generate a short summary (for chat display)."""
    lines: List[str] = []
    _header(lines, report)
    _verdict_summary(lines, report)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section generators
# ---------------------------------------------------------------------------

def _header(lines: List[str], r: FullReport) -> None:
    lines.append(f"# {r.test_name or r.test_id} -- Full Report")
    lines.append("")
    lines.append(f"**Device:** {r.device} | **Image:** {r.image_version}")
    lines.append(f"**Started:** {r.started_at} | **Completed:** {r.completed_at}")
    lines.append(f"**Overall Verdict:** **{r.overall_verdict}**")
    lines.append("")


def _verdict_summary(lines: List[str], r: FullReport) -> None:
    lines.append("## Scenario Verdicts")
    lines.append("")
    lines.append("| # | Scenario | Verdict | Duration |")
    lines.append("|---|----------|---------|----------|")
    for i, s in enumerate(r.scenarios, 1):
        verdict_mark = "[PASS]" if s.verdict == "PASS" else "[FAIL]" if s.verdict == "FAIL" else "[SKIP]"
        lines.append(f"| {i} | {s.scenario_name or s.scenario_id} | {verdict_mark} | {s.duration_sec:.1f}s |")

    passed = sum(1 for s in r.scenarios if s.verdict == "PASS")
    failed = sum(1 for s in r.scenarios if s.verdict == "FAIL")
    total = len(r.scenarios)
    lines.append("")
    lines.append(f"**Total:** {total} scenarios, {passed} PASS, {failed} FAIL")
    lines.append("")


def _scenario_details(lines: List[str], r: FullReport) -> None:
    lines.append("## Scenario Details")
    lines.append("")

    for s in r.scenarios:
        lines.append(f"### {s.scenario_name or s.scenario_id}")
        lines.append("")
        lines.append(f"**Verdict:** {s.verdict} | **Duration:** {s.duration_sec:.1f}s")
        lines.append("")

        if s.layer_verdicts:
            lines.append("**Layer Verdicts:**")
            lines.append("")
            for layer, v in s.layer_verdicts.items():
                mark = "[PASS]" if v == "PASS" else "[FAIL]"
                lines.append(f"- {layer}: {mark}")
            lines.append("")

        if s.counter_diff:
            _counter_diff_section(lines, s.counter_diff)

        if s.event_audit:
            _event_audit_section(lines, s.event_audit)

        if s.cross_layer:
            lines.append("**Cross-Layer Check:**")
            cl_pass = s.cross_layer.get("passed", True)
            lines.append(f"- Result: {'PASS' if cl_pass else 'FAIL'}")
            for m in s.cross_layer.get("mismatches", [])[:5]:
                lines.append(f"  - [{m.get('severity', 'FAIL')}] {m.get('rule', '?')}: {m.get('detail', '')}")
            lines.append("")

        if s.poll_data:
            lines.append(f"**Recovery Polling:** {s.poll_data.get('sample_count', 0)} samples, "
                         f"converged={'YES' if s.poll_data.get('converged') else 'NO'} "
                         f"at {s.poll_data.get('converged_at_sec', 'N/A')}s")
            lines.append("")

        if s.errors:
            lines.append("**Errors:**")
            for err in s.errors[:10]:
                lines.append(f"- {err}")
            lines.append("")

        if s.repro_steps:
            lines.append("**Reproduction Steps:**")
            lines.append("")
            lines.append(s.repro_steps)
            lines.append("")

        lines.append("---")
        lines.append("")


def _counter_diff_section(lines: List[str], diff: Dict[str, Any]) -> None:
    lines.append("**Counter Diff:**")
    lines.append("")
    items = diff.get("items", [])
    if items:
        lines.append("| Counter | Before | After | Delta | Rule | Result |")
        lines.append("|---------|--------|-------|-------|------|--------|")
        for item in items:
            status = "[PASS]" if item.get("passed") else "[FAIL]"
            lines.append(f"| {item['label']} | {item['before']} | {item['after']} | {item['delta']} | {item['rule']} | {status} |")
    lines.append("")


def _event_audit_section(lines: List[str], audit: Dict[str, Any]) -> None:
    lines.append("**Event Audit:**")
    lines.append("")
    items = audit.get("items", [])
    if items:
        lines.append("| Event | Expect | Found | Result |")
        lines.append("|-------|--------|-------|--------|")
        for item in items:
            status = "[PASS]" if item.get("passed") else "[FAIL]"
            lines.append(f"| {item['event']} | {item['expect']} | {item['found_count']} | {status} |")
    lines.append("")


def _config_baseline_section(lines: List[str], r: FullReport) -> None:
    if not r.config_baseline:
        return
    lines.append("## Config Baseline")
    lines.append("")
    clean = r.config_baseline.get("clean", True)
    lines.append(f"**Status:** {'CLEAN -- no config debris' if clean else 'DEBRIS DETECTED'}")
    if not clean:
        for diff in r.config_baseline.get("diffs", []):
            if diff.get("has_changes"):
                lines.append(f"- {diff['section']}: +{diff.get('added_count', 0)} -{diff.get('removed_count', 0)} lines")
    lines.append("")


def _health_section(lines: List[str], r: FullReport) -> None:
    if not r.health_before and not r.health_after:
        return
    lines.append("## Device Health")
    lines.append("")
    if r.health_before:
        lines.append(f"**Before:** System uptime: {r.health_before.get('system_uptime', 'N/A')}")
    if r.health_after:
        lines.append(f"**After:** System uptime: {r.health_after.get('system_uptime', 'N/A')}")
        procs = r.health_after.get("processes", {})
        for name, state in procs.items():
            running = "running" if state.get("running") else "STOPPED"
            lines.append(f"  - {name}: {running} (restarts={state.get('restart_count', 0)})")
    lines.append("")


def _regression_section(lines: List[str], r: FullReport) -> None:
    if not r.regression:
        return
    lines.append("## Regression Check")
    lines.append("")
    if not r.regression.get("baseline_loaded"):
        lines.append("No baseline available for regression comparison.")
    else:
        lines.append(f"**Baseline:** {r.regression.get('baseline_run', 'N/A')}")
        lines.append(f"**Regressions:** {r.regression.get('regression_count', 0)}")
        lines.append(f"**Improvements:** {r.regression.get('improvement_count', 0)}")
        for item in r.regression.get("items", []):
            if item.get("direction") != "stable":
                mark = "[REGR]" if item["direction"] == "regression" else "[IMPR]"
                lines.append(f"  {mark} {item['metric']}: {item['baseline']} -> {item['current']}")
    lines.append("")


def _cleanup_section(lines: List[str], r: FullReport) -> None:
    if not r.cleanup_result:
        return
    lines.append("## Cleanup")
    lines.append("")
    success = r.cleanup_result.get("cleanup_successful", True)
    lines.append(f"**Status:** {'Successful' if success else 'ERRORS during cleanup'}")
    for err in r.cleanup_result.get("errors", [])[:5]:
        lines.append(f"- {err}")
    lines.append("")


def _learning_section(lines: List[str], r: FullReport) -> None:
    if not r.learning_updates:
        return
    lines.append("## Learning Updates")
    lines.append("")
    for update in r.learning_updates:
        lines.append(f"- {update}")
    lines.append("")


def _footer(lines: List[str], r: FullReport) -> None:
    lines.append("---")
    lines.append(f"*Generated by /TEST QA Framework at {_iso_now()}*")
    lines.append("*LOCAL ONLY -- this report is not pushed to any external system*")


def _report_to_dict(r: FullReport) -> Dict[str, Any]:
    """Convert full report to JSON-serializable dict."""
    return {
        "test_id": r.test_id,
        "test_name": r.test_name,
        "device": r.device,
        "image_version": r.image_version,
        "started_at": r.started_at,
        "completed_at": r.completed_at,
        "overall_verdict": r.overall_verdict,
        "scenario_count": len(r.scenarios),
        "scenarios": [
            {
                "id": s.scenario_id,
                "name": s.scenario_name,
                "verdict": s.verdict,
                "duration_sec": s.duration_sec,
                "layer_verdicts": s.layer_verdicts,
                "counter_diff": s.counter_diff,
                "event_audit": s.event_audit,
                "health_check": s.health_check,
                "cross_layer": s.cross_layer,
                "poll_data": s.poll_data,
                "errors": s.errors,
            }
            for s in r.scenarios
        ],
        "config_baseline": r.config_baseline,
        "regression": r.regression,
        "cleanup": r.cleanup_result,
        "learning_updates": r.learning_updates,
    }
