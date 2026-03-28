#!/usr/bin/env python3
"""
Post-run learning engine for DNOS test automation.

After each test run, analyzes verdicts and failures to extract lessons:
  - New failure patterns to watch for
  - Timing baselines for regression detection
  - Command output patterns for smarter parsing
  - Device-specific quirks

Persists to ~/.test_learning.json and syncs to MD mirrors.
LOCAL ONLY -- never writes to Jira/Confluence.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

LEARNING_JSON = Path.home() / ".test_learning.json"
LEARNING_MD = Path.home() / ".cursor" / "test-reference" / "learned_rules.md"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _load_learning_db() -> Dict[str, Any]:
    """Load the learning database."""
    if LEARNING_JSON.exists():
        try:
            return json.loads(LEARNING_JSON.read_text())
        except Exception:
            pass
    return {
        "version": 1,
        "updated_at": "",
        "timing_baselines": {},
        "failure_patterns": [],
        "device_quirks": {},
        "command_patterns": {},
        "test_history": [],
    }


def _save_learning_db(db: Dict[str, Any]) -> None:
    """Save the learning database."""
    db["updated_at"] = _iso_now()
    LEARNING_JSON.parent.mkdir(parents=True, exist_ok=True)
    LEARNING_JSON.write_text(json.dumps(db, indent=2))


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def learn_from_run(
    test_id: str,
    device: str,
    verdict_data: Dict[str, Any],
    timing_data: Optional[Dict[str, float]] = None,
    failure_details: Optional[List[Dict[str, Any]]] = None,
) -> List[str]:
    """Analyze a test run and extract lessons. Returns list of learning updates."""
    db = _load_learning_db()
    updates: List[str] = []

    # Record test history
    history_entry = {
        "test_id": test_id,
        "device": device,
        "timestamp": _iso_now(),
        "overall_verdict": verdict_data.get("overall", "unknown"),
        "scenario_count": len(verdict_data.get("scenarios", [])),
        "passed": sum(1 for s in verdict_data.get("scenarios", []) if s.get("verdict") == "PASS"),
        "failed": sum(1 for s in verdict_data.get("scenarios", []) if s.get("verdict") == "FAIL"),
    }
    db["test_history"].append(history_entry)
    if len(db["test_history"]) > 100:
        db["test_history"] = db["test_history"][-100:]
    updates.append(f"Recorded test run: {test_id} on {device}")

    # Update timing baselines
    if timing_data:
        for key, value in timing_data.items():
            baseline_key = f"{test_id}:{key}"
            existing = db["timing_baselines"].get(baseline_key)
            if existing:
                db["timing_baselines"][baseline_key] = {
                    "last": value,
                    "avg": (existing.get("avg", value) + value) / 2,
                    "min": min(existing.get("min", value), value),
                    "max": max(existing.get("max", value), value),
                    "samples": existing.get("samples", 1) + 1,
                }
            else:
                db["timing_baselines"][baseline_key] = {
                    "last": value, "avg": value, "min": value, "max": value, "samples": 1,
                }
        updates.append(f"Updated {len(timing_data)} timing baselines")

    # Learn from failures
    if failure_details:
        for fail in failure_details:
            pattern = {
                "test_id": test_id,
                "scenario": fail.get("scenario_id", ""),
                "layer": fail.get("failed_layer", ""),
                "error_type": fail.get("error_type", ""),
                "detail": fail.get("detail", "")[:500],
                "first_seen": _iso_now(),
                "occurrences": 1,
                "device": device,
            }

            # Check for existing similar pattern
            merged = False
            for existing in db["failure_patterns"]:
                if (existing.get("layer") == pattern["layer"] and
                        existing.get("error_type") == pattern["error_type"]):
                    existing["occurrences"] = existing.get("occurrences", 1) + 1
                    existing["last_seen"] = _iso_now()
                    merged = True
                    break

            if not merged:
                db["failure_patterns"].append(pattern)
                updates.append(f"New failure pattern: {pattern['layer']}:{pattern['error_type']}")

        if len(db["failure_patterns"]) > 200:
            db["failure_patterns"] = db["failure_patterns"][-200:]

    # Device-specific quirks
    device_key = device.lower().replace("-", "_")
    if device_key not in db["device_quirks"]:
        db["device_quirks"][device_key] = {
            "first_test": _iso_now(),
            "test_count": 0,
            "known_issues": [],
        }
    db["device_quirks"][device_key]["test_count"] += 1
    db["device_quirks"][device_key]["last_test"] = _iso_now()

    _save_learning_db(db)

    # Try to sync MD mirror
    _sync_md_mirror()

    return updates


def get_timing_baseline(test_id: str, metric: str) -> Optional[Dict[str, Any]]:
    """Get timing baseline for a specific metric."""
    db = _load_learning_db()
    return db["timing_baselines"].get(f"{test_id}:{metric}")


def get_known_failure_patterns(layer: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get known failure patterns, optionally filtered by layer."""
    db = _load_learning_db()
    patterns = db.get("failure_patterns", [])
    if layer:
        patterns = [p for p in patterns if p.get("layer") == layer]
    return patterns


def get_test_history(test_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent test history."""
    db = _load_learning_db()
    history = db.get("test_history", [])
    if test_id:
        history = [h for h in history if h.get("test_id") == test_id]
    return history[-limit:]


def _sync_md_mirror() -> None:
    """Sync learning JSON to MD mirror if prune_learning.py exists."""
    prune_script = Path.home() / ".cursor" / "tools" / "prune_learning.py"
    if prune_script.exists():
        try:
            subprocess.run(
                ["python3", str(prune_script), "--command", "test", "--sync-only"],
                capture_output=True, timeout=10,
            )
        except Exception:
            pass
