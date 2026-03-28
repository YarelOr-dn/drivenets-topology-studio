#!/usr/bin/env python3
"""
Device health guard engine for DNOS test automation.

Checks device health before and after each scenario:
  - Process state (running/crashed/restarted)
  - Crash detection (core dumps, process restarts)
  - CPU and memory utilization
  - System error counters
  - Alarm state

Recipe JSON format:
    "health_checks": {
        "processes": ["routing:bgpd", "routing:fibmgrd", "routing:rib_manager",
                      "neighbour_manager"],
        "check_crashes": true,
        "check_cpu_memory": true,
        "check_alarms": true,
        "cpu_threshold_pct": 90,
        "memory_threshold_pct": 90,
        "error_counter_commands": [
            "show interfaces counters errors | no-more"
        ]
    }
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

RunShowFn = Callable[[str, str], str]

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text) if isinstance(text, str) else str(text)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ProcessState:
    """State of one DNOS process."""
    name: str
    running: bool = False
    pid: Optional[int] = None
    uptime: str = ""
    restart_count: int = 0
    cpu_pct: float = 0.0
    mem_pct: float = 0.0
    raw_output: str = ""


@dataclass
class HealthSnapshot:
    """Device health at one point in time."""
    label: str
    timestamp: str = ""
    processes: Dict[str, ProcessState] = field(default_factory=dict)
    system_uptime: str = ""
    active_alarms: List[str] = field(default_factory=list)
    crash_files: List[str] = field(default_factory=list)
    error_counters: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "timestamp": self.timestamp,
            "system_uptime": self.system_uptime,
            "processes": {
                k: {
                    "running": v.running, "pid": v.pid, "uptime": v.uptime,
                    "restart_count": v.restart_count, "cpu_pct": v.cpu_pct,
                    "mem_pct": v.mem_pct,
                }
                for k, v in self.processes.items()
            },
            "active_alarms": self.active_alarms,
            "crash_count": len(self.crash_files),
            "crash_files": self.crash_files[:10],
            "error_counter_count": len(self.error_counters),
        }


@dataclass
class HealthCheckItem:
    """One health check result."""
    check: str
    passed: bool
    detail: str
    severity: str = "FAIL"  # FAIL or WARN


@dataclass
class HealthGuardResult:
    """Full health guard comparison result."""
    before_label: str
    after_label: str
    checks: List[HealthCheckItem] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(c.severity == "FAIL" and not c.passed for c in self.checks)

    @property
    def fail_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed and c.severity == "FAIL")

    @property
    def warn_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed and c.severity == "WARN")

    def summary(self) -> str:
        parts = [f"Health guard {self.before_label} -> {self.after_label}: {'PASS' if self.passed else 'FAIL'}"]
        for c in self.checks:
            if not c.passed:
                parts.append(f"  [{c.severity}] {c.check}: {c.detail}")
        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "before_label": self.before_label,
            "after_label": self.after_label,
            "passed": self.passed,
            "fail_count": self.fail_count,
            "warn_count": self.warn_count,
            "checks": [
                {"check": c.check, "passed": c.passed, "detail": c.detail, "severity": c.severity}
                for c in self.checks
            ],
        }


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def snapshot_health(
    device: str,
    label: str,
    run_show: RunShowFn,
    processes: Optional[List[str]] = None,
    check_crashes: bool = True,
    check_alarms: bool = True,
    error_counter_commands: Optional[List[str]] = None,
) -> HealthSnapshot:
    """Capture device health state."""
    snap = HealthSnapshot(label=label, timestamp=_iso_now())

    # System uptime
    try:
        output = _strip_ansi(run_show(device, "show system version | no-more"))
        for line in output.splitlines():
            if "uptime" in line.lower():
                snap.system_uptime = line.strip()
                break
    except Exception:
        pass

    # Process states
    if processes:
        for proc in processes:
            ps = _check_process(device, proc, run_show)
            snap.processes[proc] = ps

    # Crash/core dump files
    if check_crashes:
        snap.crash_files = _check_crash_files(device, run_show)

    # Alarms
    if check_alarms:
        snap.active_alarms = _check_alarms(device, run_show)

    # Error counters
    if error_counter_commands:
        for cmd in error_counter_commands:
            try:
                output = run_show(device, cmd)
                snap.error_counters[cmd] = _strip_ansi(output)
            except Exception:
                snap.error_counters[cmd] = ""

    return snap


def compare_health(
    before: HealthSnapshot,
    after: HealthSnapshot,
    cpu_threshold: float = 90.0,
    mem_threshold: float = 90.0,
) -> HealthGuardResult:
    """Compare before/after health snapshots for degradation."""
    result = HealthGuardResult(
        before_label=before.label,
        after_label=after.label,
    )

    # Check each process: still running, no new restarts
    for proc_name, before_ps in before.processes.items():
        after_ps = after.processes.get(proc_name)
        if not after_ps:
            result.checks.append(HealthCheckItem(
                check=f"process_{proc_name}",
                passed=False,
                detail=f"Process {proc_name} missing from after snapshot",
            ))
            continue

        if before_ps.running and not after_ps.running:
            result.checks.append(HealthCheckItem(
                check=f"process_{proc_name}_running",
                passed=False,
                detail=f"Process {proc_name} was running, now stopped",
            ))
        elif after_ps.running:
            result.checks.append(HealthCheckItem(
                check=f"process_{proc_name}_running",
                passed=True,
                detail=f"Process {proc_name} running (PID={after_ps.pid})",
            ))

        restart_delta = after_ps.restart_count - before_ps.restart_count
        if restart_delta > 0:
            result.checks.append(HealthCheckItem(
                check=f"process_{proc_name}_restarts",
                passed=False,
                detail=f"Process {proc_name} restarted {restart_delta} time(s) during test",
            ))

        if after_ps.cpu_pct > cpu_threshold:
            result.checks.append(HealthCheckItem(
                check=f"process_{proc_name}_cpu",
                passed=False,
                detail=f"CPU {after_ps.cpu_pct}% exceeds threshold {cpu_threshold}%",
                severity="WARN",
            ))

        if after_ps.mem_pct > mem_threshold:
            result.checks.append(HealthCheckItem(
                check=f"process_{proc_name}_mem",
                passed=False,
                detail=f"Memory {after_ps.mem_pct}% exceeds threshold {mem_threshold}%",
                severity="WARN",
            ))

    # New crashes
    new_crashes = set(after.crash_files) - set(before.crash_files)
    if new_crashes:
        result.checks.append(HealthCheckItem(
            check="new_crashes",
            passed=False,
            detail=f"New crash files: {', '.join(list(new_crashes)[:5])}",
        ))
    else:
        result.checks.append(HealthCheckItem(
            check="new_crashes",
            passed=True,
            detail="No new crash files",
        ))

    # New alarms
    new_alarms = set(after.active_alarms) - set(before.active_alarms)
    if new_alarms:
        result.checks.append(HealthCheckItem(
            check="new_alarms",
            passed=False,
            detail=f"New alarms: {', '.join(list(new_alarms)[:5])}",
            severity="WARN",
        ))

    return result


def load_health_config(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """Load health check configuration from recipe."""
    return recipe.get("health_checks", {
        "processes": [],
        "check_crashes": True,
        "check_cpu_memory": True,
        "check_alarms": True,
        "cpu_threshold_pct": 90,
        "memory_threshold_pct": 90,
        "error_counter_commands": [],
    })


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _check_process(device: str, proc_name: str, run_show: RunShowFn) -> ProcessState:
    """Check one process state via show system process."""
    ps = ProcessState(name=proc_name)
    try:
        output = _strip_ansi(run_show(device, f"show system process {proc_name} | no-more"))
        ps.raw_output = output

        if "not found" in output.lower() or "error" in output.lower():
            ps.running = False
            return ps

        ps.running = True

        pid_m = re.search(r"PID\s*[:=]\s*(\d+)", output, re.IGNORECASE)
        if pid_m:
            ps.pid = int(pid_m.group(1))

        uptime_m = re.search(r"uptime\s*[:=]\s*(.+)", output, re.IGNORECASE)
        if uptime_m:
            ps.uptime = uptime_m.group(1).strip()

        restart_m = re.search(r"restart[s]?\s*[:=]\s*(\d+)", output, re.IGNORECASE)
        if restart_m:
            ps.restart_count = int(restart_m.group(1))

        cpu_m = re.search(r"CPU\s*[:=]?\s*([\d.]+)\s*%", output, re.IGNORECASE)
        if cpu_m:
            ps.cpu_pct = float(cpu_m.group(1))

        mem_m = re.search(r"(?:MEM|Memory)\s*[:=]?\s*([\d.]+)\s*%", output, re.IGNORECASE)
        if mem_m:
            ps.mem_pct = float(mem_m.group(1))

    except Exception:
        ps.running = False

    return ps


def _check_crash_files(device: str, run_show: RunShowFn) -> List[str]:
    """Check for crash/core dump files."""
    crash_files: List[str] = []
    try:
        output = _strip_ansi(run_show(device, "show system alarms | no-more"))
        for line in output.splitlines():
            if "core" in line.lower() or "crash" in line.lower():
                crash_files.append(line.strip()[:200])
    except Exception:
        pass
    return crash_files


def _check_alarms(device: str, run_show: RunShowFn) -> List[str]:
    """Get active system alarms."""
    alarms: List[str] = []
    try:
        output = _strip_ansi(run_show(device, "show system alarms | no-more"))
        for line in output.splitlines():
            line = line.strip()
            if line and not line.startswith("---") and not line.startswith("==="):
                alarms.append(line[:200])
    except Exception:
        pass
    return alarms
