#!/usr/bin/env python3
"""Per-run command transcript logger for /TEST.

Every device-touching command issued during a /TEST run flows through
``device_runner.create_device_runner()``. This module hooks the choke point
so EVERY command -- regardless of which strategy executed it (MCP, helper,
SSH, agent callback) -- is captured with:

    - timestamp (UTC, ISO + monotonic delta)
    - device name
    - command (verbatim)
    - output (verbatim, ANSI-stripped)
    - method used (mcp / helper / ssh_session / agent / error)
    - phase / scenario / role tag (set by the caller via set_context)
    - verdict (rejected / accepted / informational)

Two artifacts are written into the run results directory:

    EXECUTION_LOG.md        -- human-readable, ordered log per DUT and phase
    execution_log.jsonl     -- one JSON record per command (machine-readable)

Usage from the orchestrator
---------------------------

    from shared.run_transcript import (
        start_transcript, set_context, finalize_transcript,
    )

    start_transcript(run_dir=Path(".../results/RUN_<ts>_<device>/<test>"),
                     test_id="TEST_mac_mob_basic_SW205160",
                     primary_device="PE-1",
                     dry_run=False)

    set_context(phase="prerequisite_gate", scenario=None, role="DUT")
    # ... runner now records every show command automatically ...

    set_context(phase="SC01:snapshot", scenario="SC01_learn_local_ac")
    # ... etc

    finalize_transcript(verdict="PASS")

All capture happens inside device_runner.run_show via the transcript hook;
no per-test wiring is required after start_transcript() is called once.

Markdown layout
---------------

EXECUTION_LOG.md is grouped by phase; each phase section contains an ordered
list of (timestamp, device, role) -> command -> output blocks. Output is
fenced and trimmed to MAX_OUTPUT_LINES_PER_CMD (default 200) with the last
20 lines included to keep big tables (mac-table dumps) readable. The full
untrimmed output is always in execution_log.jsonl.
"""
from __future__ import annotations

import json
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
_REJECT_RE = re.compile(
    r"ERROR:\s*Unknown word|Incomplete command|Invalid input|% Invalid",
    re.IGNORECASE,
)

# How much output to keep in the human-readable EXECUTION_LOG.md per command.
# The full output always lands in execution_log.jsonl.
MAX_OUTPUT_LINES_HEAD = 200
MAX_OUTPUT_LINES_TAIL = 20


# ---------------------------------------------------------------------------
# Module state
# ---------------------------------------------------------------------------

@dataclass
class _State:
    enabled: bool = False
    run_dir: Optional[Path] = None
    test_id: str = ""
    primary_device: str = ""
    dry_run: bool = False
    started_at: float = 0.0
    started_iso: str = ""
    # Current capture context (mutable through set_context())
    phase: str = "init"
    scenario: Optional[str] = None
    role: str = "DUT"
    # Records buffered in memory + flushed to JSONL on every record_command()
    records: List[Dict[str, Any]] = field(default_factory=list)
    counters: Dict[str, int] = field(default_factory=lambda: {
        "total_cmds": 0,
        "rejected_cmds": 0,
        "by_method": {},
    })
    lock: threading.Lock = field(default_factory=threading.Lock)


_S = _State()


# ---------------------------------------------------------------------------
# Public API: lifecycle
# ---------------------------------------------------------------------------

def start_transcript(
    run_dir: Path,
    test_id: str,
    primary_device: str,
    dry_run: bool = False,
) -> None:
    """Open a transcript for the run. Idempotent within a process."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    with _S.lock:
        _S.enabled = True
        _S.run_dir = run_dir
        _S.test_id = test_id
        _S.primary_device = primary_device
        _S.dry_run = bool(dry_run)
        _S.started_at = time.monotonic()
        _S.started_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        _S.phase = "init"
        _S.scenario = None
        _S.role = "DUT"
        _S.records = []
        _S.counters = {"total_cmds": 0, "rejected_cmds": 0, "by_method": {}}
        # Truncate any prior JSONL from a re-run.
        (run_dir / "execution_log.jsonl").write_text("")


def set_context(
    *, phase: Optional[str] = None,
    scenario: Optional[str] = None,
    role: Optional[str] = None,
) -> None:
    """Set the current phase/scenario/role tag attached to subsequent records."""
    with _S.lock:
        if phase is not None:
            _S.phase = phase
        if scenario is not None:
            _S.scenario = scenario
        if role is not None:
            _S.role = role


def is_active() -> bool:
    return _S.enabled and _S.run_dir is not None


def record_command(
    device: str,
    command: str,
    output: str,
    method: str,
    *,
    elapsed_ms: Optional[float] = None,
) -> None:
    """Record one command + output in the transcript. Called by device_runner."""
    if not is_active():
        return
    with _S.lock:
        clean_out = _ANSI_RE.sub("", output or "")
        rejected = bool(_REJECT_RE.search(clean_out))
        record = {
            "ts_iso": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "ts_delta_ms": int((time.monotonic() - _S.started_at) * 1000),
            "elapsed_ms": int(elapsed_ms) if elapsed_ms is not None else None,
            "device": device,
            "role": _S.role,
            "phase": _S.phase,
            "scenario": _S.scenario,
            "method": method,
            "command": command,
            "rejected": rejected,
            "output": clean_out,
            "output_lines": clean_out.count("\n") + (1 if clean_out else 0),
        }
        _S.records.append(record)
        _S.counters["total_cmds"] += 1
        if rejected:
            _S.counters["rejected_cmds"] += 1
        _S.counters["by_method"][method] = _S.counters["by_method"].get(method, 0) + 1
        # Stream to JSONL so a kill -9 doesn't lose the log.
        try:
            with (_S.run_dir / "execution_log.jsonl").open("a") as fp:
                fp.write(json.dumps(record, default=str) + "\n")
        except Exception:
            pass  # never fail a test because logging failed


def finalize_transcript(verdict: str = "UNKNOWN", extra: Optional[Dict[str, Any]] = None) -> Optional[Path]:
    """Emit EXECUTION_LOG.md and seal the transcript. Returns the markdown path."""
    if not is_active():
        return None
    with _S.lock:
        run_dir = _S.run_dir
        md_path = run_dir / "EXECUTION_LOG.md"
        md_path.write_text(_render_markdown(verdict=verdict, extra=extra or {}))
        # Header file with quick stats.
        stats = {
            "test_id": _S.test_id,
            "primary_device": _S.primary_device,
            "dry_run": _S.dry_run,
            "started_at": _S.started_iso,
            "ended_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "verdict": verdict,
            "totals": dict(_S.counters),
        }
        (run_dir / "execution_log_stats.json").write_text(
            json.dumps(stats, indent=2, default=str) + "\n"
        )
        _S.enabled = False
        return md_path


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def _render_markdown(verdict: str, extra: Dict[str, Any]) -> str:
    out: List[str] = []
    out.append(f"# Execution Log -- {_S.test_id}")
    out.append("")
    out.append(
        f"**Run started:** {_S.started_iso}  |  "
        f"**Primary DUT:** `{_S.primary_device}`  |  "
        f"**Dry run:** {_S.dry_run}  |  **Verdict:** **{verdict}**"
    )
    out.append("")
    # Totals
    by_method = _S.counters.get("by_method", {})
    by_method_str = ", ".join(
        f"`{k}`={v}" for k, v in sorted(by_method.items())
    ) or "-"
    out.append("## Totals")
    out.append("")
    out.append(f"- Total commands issued: **{_S.counters['total_cmds']}**")
    out.append(f"- DNOS-rejected commands: **{_S.counters['rejected_cmds']}**")
    out.append(f"- By method: {by_method_str}")
    if extra:
        out.append("")
        for k, v in extra.items():
            out.append(f"- **{k}:** {v}")
    out.append("")
    # Per-DUT command count summary
    per_dut: Dict[str, int] = {}
    for r in _S.records:
        per_dut[r["device"]] = per_dut.get(r["device"], 0) + 1
    if per_dut:
        out.append("## Commands per DUT")
        out.append("")
        out.append("| Device | Commands |")
        out.append("|---|---|")
        for d, n in sorted(per_dut.items(), key=lambda x: -x[1]):
            out.append(f"| `{d}` | {n} |")
        out.append("")

    # Group records by phase, preserving first-seen order.
    phase_order: List[str] = []
    by_phase: Dict[str, List[Dict[str, Any]]] = {}
    for r in _S.records:
        ph = r["phase"]
        if ph not in by_phase:
            phase_order.append(ph)
            by_phase[ph] = []
        by_phase[ph].append(r)

    for ph in phase_order:
        recs = by_phase[ph]
        scen = recs[0].get("scenario")
        title = f"## Phase: `{ph}`"
        if scen:
            title += f" -- scenario `{scen}`"
        out.append(title)
        out.append("")
        out.append(f"_{len(recs)} command(s) in this phase._")
        out.append("")
        for i, r in enumerate(recs, 1):
            tag_dut = f"`{r['device']}`"
            if r.get("role") and r["role"] != "DUT":
                tag_dut += f" ({r['role']})"
            verdict_tag = " **REJECTED**" if r["rejected"] else ""
            elapsed = ""
            if r.get("elapsed_ms") is not None:
                elapsed = f" -- {r['elapsed_ms']} ms"
            out.append(
                f"### {i}. [{r['ts_iso']}] {tag_dut} via `{r['method']}`{elapsed}{verdict_tag}"
            )
            out.append("")
            out.append("**Command:**")
            out.append("")
            out.append("```dnos")
            out.append(r["command"])
            out.append("```")
            out.append("")
            out.append("**Output:**")
            out.append("")
            out.append("```")
            lines = (r["output"] or "").splitlines()
            if len(lines) <= MAX_OUTPUT_LINES_HEAD + MAX_OUTPUT_LINES_TAIL:
                out.extend(lines if lines else ["(empty)"])
            else:
                out.extend(lines[:MAX_OUTPUT_LINES_HEAD])
                trimmed = len(lines) - MAX_OUTPUT_LINES_HEAD - MAX_OUTPUT_LINES_TAIL
                out.append("")
                out.append(f"... [truncated: {trimmed} lines omitted; "
                           f"see execution_log.jsonl for full output] ...")
                out.append("")
                out.extend(lines[-MAX_OUTPUT_LINES_TAIL:])
            out.append("```")
            out.append("")

    out.append("---")
    out.append("")
    out.append(
        "_Full untrimmed outputs are in `execution_log.jsonl` (one JSON record per "
        "command). Quick stats are in `execution_log_stats.json`._"
    )
    out.append("")
    return "\n".join(out)


__all__ = [
    "start_transcript",
    "set_context",
    "is_active",
    "record_command",
    "finalize_transcript",
]
