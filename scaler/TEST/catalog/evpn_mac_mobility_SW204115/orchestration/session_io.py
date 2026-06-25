"""Session / runtime-correction I/O utilities.

Extracted from ``mac_mobility_orchestrator.py`` to isolate filesystem chatter
(active-session JSON, runtime_corrections.json self-healing cache) and tiny
timestamp helpers from the orchestration core.

Public API:
    now_iso, now_hhmm
    write_active_session(payload)
    load_manifest(), load_recipe(rel_path)
    _apply_corrections(command), _record_runtime_failure(cmd, err),
    _record_runtime_success(cmd)
    _default_run_show(device, command) -- resilient device command runner
                                           with self-healing syntax layer
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from shared.device_runner import create_device_runner

from .constants import ACTIVE_SESSION, CORRECTIONS_PATH, MANIFEST_PATH, SUITE_ROOT


# ---------------------------------------------------------------------------
# Timestamps
# ---------------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def now_hhmm() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M")


# ---------------------------------------------------------------------------
# Active session file (read by sub-commands for cross-command context)
# ---------------------------------------------------------------------------

def write_active_session(payload: Dict[str, Any]) -> None:
    ACTIVE_SESSION.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_SESSION.write_text(json.dumps(payload, indent=2))


# ---------------------------------------------------------------------------
# Recipe / manifest loaders
# ---------------------------------------------------------------------------

def load_manifest() -> Dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text())


def load_recipe(rel_path: str) -> Dict[str, Any]:
    return json.loads((SUITE_ROOT / rel_path).read_text())


# ---------------------------------------------------------------------------
# Self-healing command correction layer
# ---------------------------------------------------------------------------

_corrections_cache: Optional[Dict[str, Any]] = None


def _load_corrections() -> Dict[str, Any]:
    global _corrections_cache
    if _corrections_cache is None and CORRECTIONS_PATH.exists():
        _corrections_cache = json.loads(CORRECTIONS_PATH.read_text())
    return _corrections_cache or {}


def _apply_corrections(command: str) -> str:
    """Apply known DNOS syntax corrections before sending to device."""
    corrections = _load_corrections()
    original = command
    for entry in corrections.get("command_corrections", []):
        if "wrong_pattern" in entry:
            command = re.sub(entry["wrong_pattern"], entry["correct_pattern"], command)
        elif "wrong" in entry:
            command = command.replace(entry["wrong"], entry["correct"])
    if command != original:
        print(f"  [SELF-HEAL] Corrected: {original!r} -> {command!r}")
    return command


def _record_runtime_failure(command: str, error_output: str) -> None:
    """Record a command failure for future self-healing."""
    corrections = _load_corrections()
    learning = corrections.setdefault("runtime_learning", {})
    failed = learning.setdefault("failed_commands", [])
    failed.append({
        "command": command,
        "error": error_output[:200],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    learning["last_updated"] = datetime.now(timezone.utc).isoformat()
    CORRECTIONS_PATH.write_text(json.dumps(corrections, indent=2))


def _record_runtime_success(command: str) -> None:
    """Record a command that worked for future reference."""
    corrections = _load_corrections()
    learning = corrections.setdefault("runtime_learning", {})
    successful = learning.setdefault("successful_commands", [])
    if command not in successful:
        successful.append(command)
        if len(successful) > 100:
            successful[:] = successful[-100:]
        learning["last_updated"] = datetime.now(timezone.utc).isoformat()
        CORRECTIONS_PATH.write_text(json.dumps(corrections, indent=2))


# ---------------------------------------------------------------------------
# Resilient device command runner (self-healing -> helper -> SSH)
# ---------------------------------------------------------------------------

_device_runners: Dict[str, Any] = {}


def _default_run_show(device: str, command: str) -> str:
    """Resilient device command runner with self-healing syntax correction.

    Strategy chain:
      1. Apply known corrections from runtime_corrections.json
      2. Run via device runner (helper -> SSH)
      3. If DNOS error detected, record failure for future learning
      4. On success, record validated command
    """
    command = _apply_corrections(command)
    if device not in _device_runners:
        _device_runners[device] = create_device_runner(device)
    result = _device_runners[device](device, command)
    error_markers = ("ERROR:", "Unknown word", "Incomplete command", "Invalid input")
    if any(marker in result for marker in error_markers):
        _record_runtime_failure(command, result)
    else:
        _record_runtime_success(command)
    return result


__all__ = [
    "now_iso", "now_hhmm", "write_active_session",
    "load_manifest", "load_recipe",
    "_load_corrections", "_apply_corrections",
    "_record_runtime_failure", "_record_runtime_success",
    "_default_run_show",
]
