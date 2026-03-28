#!/usr/bin/env python3
"""
Regression detection engine for DNOS test automation.

Compares current test run metrics against historical baselines from
prior RUN_* result directories.  Detects performance regressions,
timing changes, and newly failing scenarios.

Uses local files only -- never reads from or writes to Jira/Confluence.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class BaselineMetric:
    """One metric from a historical run."""
    label: str
    value: Any
    run_id: str
    timestamp: str = ""


@dataclass
class RegressionItem:
    """One detected regression or improvement."""
    metric: str
    current: Any
    baseline: Any
    delta: Any
    direction: str  # "regression", "improvement", "stable"
    detail: str


@dataclass
class RegressionResult:
    """Full regression analysis result."""
    current_run: str
    baseline_run: str
    items: List[RegressionItem] = field(default_factory=list)
    baseline_loaded: bool = False
    baseline_path: str = ""

    @property
    def has_regressions(self) -> bool:
        return any(i.direction == "regression" for i in self.items)

    @property
    def regression_count(self) -> int:
        return sum(1 for i in self.items if i.direction == "regression")

    @property
    def improvement_count(self) -> int:
        return sum(1 for i in self.items if i.direction == "improvement")

    def summary(self) -> str:
        if not self.baseline_loaded:
            return f"No baseline found for regression comparison (run: {self.current_run})"
        parts = [f"Regression check vs {self.baseline_run}:"]
        parts.append(f"  Regressions: {self.regression_count}, Improvements: {self.improvement_count}")
        for item in self.items:
            if item.direction != "stable":
                parts.append(f"  [{item.direction.upper()}] {item.metric}: {item.baseline} -> {item.current} (delta={item.delta})")
        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_run": self.current_run,
            "baseline_run": self.baseline_run,
            "baseline_loaded": self.baseline_loaded,
            "has_regressions": self.has_regressions,
            "regression_count": self.regression_count,
            "improvement_count": self.improvement_count,
            "items": [
                {
                    "metric": i.metric,
                    "current": i.current,
                    "baseline": i.baseline,
                    "delta": i.delta,
                    "direction": i.direction,
                    "detail": i.detail,
                }
                for i in self.items
            ],
        }


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def find_latest_baseline(results_dir: Path, current_run_id: str) -> Optional[Path]:
    """Find the most recent completed RUN_* directory (excluding current)."""
    if not results_dir.exists():
        return None

    run_dirs = sorted(
        [d for d in results_dir.iterdir()
         if d.is_dir() and d.name.startswith("RUN_") and d.name != current_run_id],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    for d in run_dirs:
        verdict_file = d / "verdict.json"
        if verdict_file.exists():
            return d

    return None


def load_baseline_metrics(baseline_dir: Path) -> Dict[str, Any]:
    """Load metrics from a baseline run's verdict.json."""
    verdict_file = baseline_dir / "verdict.json"
    if not verdict_file.exists():
        return {}
    try:
        return json.loads(verdict_file.read_text())
    except Exception:
        return {}


def extract_metrics(verdict_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract comparable metrics from verdict JSON."""
    metrics: Dict[str, Any] = {}

    # Overall verdict
    metrics["overall_verdict"] = verdict_data.get("overall", "unknown")
    metrics["total_scenarios"] = len(verdict_data.get("scenarios", []))

    passed = sum(1 for s in verdict_data.get("scenarios", []) if s.get("verdict") == "PASS")
    failed = sum(1 for s in verdict_data.get("scenarios", []) if s.get("verdict") == "FAIL")
    metrics["scenarios_passed"] = passed
    metrics["scenarios_failed"] = failed

    # Timing
    if "duration_sec" in verdict_data:
        metrics["total_duration_sec"] = verdict_data["duration_sec"]

    for scenario in verdict_data.get("scenarios", []):
        sid = scenario.get("id", "unknown")
        if "duration_sec" in scenario:
            metrics[f"scenario_{sid}_duration_sec"] = scenario["duration_sec"]
        if "verdict" in scenario:
            metrics[f"scenario_{sid}_verdict"] = scenario["verdict"]
        if "layer_verdicts" in scenario:
            for layer, v in scenario["layer_verdicts"].items():
                metrics[f"scenario_{sid}_{layer}"] = v

    return metrics


def compare_against_baseline(
    current_metrics: Dict[str, Any],
    baseline_metrics: Dict[str, Any],
    current_run: str,
    baseline_run: str,
    timing_threshold_pct: float = 50.0,
) -> RegressionResult:
    """Compare current metrics against baseline for regressions."""
    result = RegressionResult(
        current_run=current_run,
        baseline_run=baseline_run,
        baseline_loaded=True,
    )

    all_keys = set(list(current_metrics.keys()) + list(baseline_metrics.keys()))

    for key in sorted(all_keys):
        current_val = current_metrics.get(key)
        baseline_val = baseline_metrics.get(key)

        if current_val is None or baseline_val is None:
            continue

        # Verdict comparisons
        if key.endswith("_verdict") or key == "overall_verdict":
            if current_val != baseline_val:
                direction = "regression" if current_val == "FAIL" and baseline_val == "PASS" else "improvement"
                result.items.append(RegressionItem(
                    metric=key, current=current_val, baseline=baseline_val,
                    delta=f"{baseline_val}->{current_val}", direction=direction,
                    detail=f"Verdict changed from {baseline_val} to {current_val}",
                ))
            continue

        # Numeric comparisons
        if isinstance(current_val, (int, float)) and isinstance(baseline_val, (int, float)):
            delta = current_val - baseline_val
            if baseline_val == 0:
                continue

            pct_change = abs(delta / baseline_val * 100)

            if key.endswith("_duration_sec"):
                if delta > 0 and pct_change > timing_threshold_pct:
                    result.items.append(RegressionItem(
                        metric=key, current=current_val, baseline=baseline_val,
                        delta=round(delta, 2), direction="regression",
                        detail=f"Duration increased by {pct_change:.0f}%",
                    ))
                elif delta < 0 and pct_change > timing_threshold_pct:
                    result.items.append(RegressionItem(
                        metric=key, current=current_val, baseline=baseline_val,
                        delta=round(delta, 2), direction="improvement",
                        detail=f"Duration decreased by {pct_change:.0f}%",
                    ))
                continue

            if key.endswith("_failed") and delta > 0:
                result.items.append(RegressionItem(
                    metric=key, current=current_val, baseline=baseline_val,
                    delta=delta, direction="regression",
                    detail=f"Failures increased by {delta}",
                ))

    return result


def run_regression_check(
    results_dir: Path,
    current_run_id: str,
    current_verdict: Dict[str, Any],
) -> RegressionResult:
    """Full regression check pipeline: find baseline, extract, compare."""
    baseline_dir = find_latest_baseline(results_dir, current_run_id)

    if not baseline_dir:
        return RegressionResult(
            current_run=current_run_id,
            baseline_run="none",
            baseline_loaded=False,
        )

    baseline_data = load_baseline_metrics(baseline_dir)
    if not baseline_data:
        return RegressionResult(
            current_run=current_run_id,
            baseline_run=baseline_dir.name,
            baseline_loaded=False,
        )

    current_metrics = extract_metrics(current_verdict)
    baseline_metrics = extract_metrics(baseline_data)

    result = compare_against_baseline(
        current_metrics, baseline_metrics,
        current_run_id, baseline_dir.name,
    )
    result.baseline_path = str(baseline_dir)

    return result
