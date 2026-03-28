#!/usr/bin/env python3
"""
Generic 3-method system event engine for DNOS test automation.

Tracks system events using three independent collection methods:
  1. Real-time terminal logging: `set logging terminal` on SSH session
  2. Persistent syslog file: `show file log routing_engine/system-events.log`
  3. Trace file greps: `show file traces routing_engine/<process>_traces`

Recipe JSON format:
    "event_expectations": [
        {
            "event": "L2_MAC_MOBILITY_MAC_ADDRESS_SUPPRESSED",
            "expect": "present",       # present | absent | count_range
            "min_count": 1,
            "max_count": null,
            "severity": "WARN",
            "description": "MAC suppression should trigger on rapid flap"
        },
        {
            "event": "BGP_NOTIFICATION",
            "expect": "absent",
            "description": "No BGP notifications during MAC move"
        }
    ]
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from .syslog_parser import SyslogEntry, parse_syslog_output, filter_by_event

RunShowFn = Callable[[str, str], str]

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class EventExpectation:
    """What we expect to see (or not see) for a specific event."""
    event: str  # regex pattern or exact event name
    expect: str  # present, absent, count_range
    min_count: Optional[int] = None
    max_count: Optional[int] = None
    severity: Optional[str] = None
    description: str = ""

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EventExpectation":
        return cls(
            event=d["event"],
            expect=d.get("expect", "present"),
            min_count=d.get("min_count"),
            max_count=d.get("max_count"),
            severity=d.get("severity"),
            description=d.get("description", ""),
        )


@dataclass
class EventMatch:
    """One matched event occurrence."""
    event_name: str
    source: str  # "terminal", "syslog", "trace"
    timestamp: Optional[str] = None
    raw_line: str = ""
    severity: Optional[str] = None


@dataclass
class EventAuditItem:
    """Result of checking one event expectation."""
    event: str
    expect: str
    found_count: int
    passed: bool
    assessment: str
    matches: List[EventMatch] = field(default_factory=list)
    description: str = ""


@dataclass
class EventAuditResult:
    """Full event audit across all expectations."""
    scenario_id: str
    timestamp_start: str = ""
    timestamp_end: str = ""
    items: List[EventAuditItem] = field(default_factory=list)
    raw_syslog_lines: int = 0
    raw_trace_lines: int = 0
    collection_errors: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(i.passed for i in self.items)

    @property
    def fail_count(self) -> int:
        return sum(1 for i in self.items if not i.passed)

    def summary(self) -> str:
        parts = [f"Event audit for {self.scenario_id}: {'PASS' if self.passed else 'FAIL'}"]
        for item in self.items:
            status = "PASS" if item.passed else "FAIL"
            parts.append(f"  [{status}] {item.event}: expect={item.expect}, found={item.found_count} -- {item.assessment}")
        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "passed": self.passed,
            "fail_count": self.fail_count,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": self.timestamp_end,
            "raw_syslog_lines": self.raw_syslog_lines,
            "raw_trace_lines": self.raw_trace_lines,
            "collection_errors": self.collection_errors,
            "items": [
                {
                    "event": i.event,
                    "expect": i.expect,
                    "found_count": i.found_count,
                    "passed": i.passed,
                    "assessment": i.assessment,
                    "description": i.description,
                    "sample_matches": [
                        {"source": m.source, "timestamp": m.timestamp, "line": m.raw_line[:300]}
                        for m in i.matches[:5]
                    ],
                }
                for i in self.items
            ],
        }


# ---------------------------------------------------------------------------
# Collection methods
# ---------------------------------------------------------------------------

def collect_syslog_events(
    device: str,
    run_show: RunShowFn,
    timestamp_hhmm: Optional[str] = None,
) -> List[SyslogEntry]:
    """Method 2: Read persistent syslog file."""
    cmd = "show file log routing_engine/system-events.log | no-more"
    if timestamp_hhmm:
        cmd = f"show file log routing_engine/system-events.log | include {timestamp_hhmm} | no-more"
    try:
        output = run_show(device, cmd)
        return parse_syslog_output(output)
    except Exception:
        return []


def collect_trace_events(
    device: str,
    run_show: RunShowFn,
    trace_files: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    timestamp_hhmm: Optional[str] = None,
    ncp_id: str = "0",
) -> List[SyslogEntry]:
    """Method 3: Grep trace files for event patterns."""
    if trace_files is None:
        trace_files = ["bgpd_traces", "fibmgrd_traces", "rib-manager_traces"]
    if keywords is None:
        keywords = ["ERROR", "WARN", "NOTIFICATION", "suppress", "duplicate", "frozen"]

    entries: List[SyslogEntry] = []

    for tf in trace_files:
        for kw in keywords:
            if tf.startswith("ncp"):
                cmd = f"show file ncp {ncp_id} traces datapath/{tf} | include {kw} | no-more"
            else:
                ts_filter = f"| include {timestamp_hhmm} " if timestamp_hhmm else ""
                cmd = f"show file traces routing_engine/{tf} {ts_filter}| include {kw} | no-more"
            try:
                output = run_show(device, cmd)
                if output and output.strip():
                    for line in output.strip().splitlines():
                        line = line.strip()
                        if line and not line.startswith("--"):
                            entry = SyslogEntry(
                                raw_line=line,
                                process=tf.replace("_traces", ""),
                                message=line,
                            )
                            entry.event_name = kw
                            entries.append(entry)
            except Exception:
                pass

    return entries


def enable_terminal_logging(
    device: str,
    run_show: RunShowFn,
) -> bool:
    """Method 1: Enable real-time syslog to terminal."""
    try:
        output = run_show(device, "set logging terminal")
        return "error" not in output.lower()
    except Exception:
        return False


def disable_terminal_logging(
    device: str,
    run_show: RunShowFn,
) -> None:
    """Disable real-time syslog on terminal."""
    try:
        run_show(device, "no set logging terminal")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def audit_events(
    device: str,
    scenario_id: str,
    expectations: List[EventExpectation],
    run_show: RunShowFn,
    timestamp_hhmm: Optional[str] = None,
    trace_files: Optional[List[str]] = None,
    extra_keywords: Optional[List[str]] = None,
    ncp_id: str = "0",
) -> EventAuditResult:
    """Run full event audit: collect from syslog + traces, evaluate expectations."""
    result = EventAuditResult(
        scenario_id=scenario_id,
        timestamp_start=timestamp_hhmm or _iso_now(),
        timestamp_end=_iso_now(),
    )

    # Collect from both sources
    syslog_entries: List[SyslogEntry] = []
    trace_entries: List[SyslogEntry] = []

    try:
        syslog_entries = collect_syslog_events(device, run_show, timestamp_hhmm)
        result.raw_syslog_lines = len(syslog_entries)
    except Exception as exc:
        result.collection_errors.append(f"syslog: {exc}")

    all_keywords = list(set(e.event for e in expectations))
    if extra_keywords:
        all_keywords.extend(extra_keywords)

    try:
        trace_entries = collect_trace_events(
            device, run_show, trace_files, all_keywords, timestamp_hhmm, ncp_id,
        )
        result.raw_trace_lines = len(trace_entries)
    except Exception as exc:
        result.collection_errors.append(f"traces: {exc}")

    all_entries = syslog_entries + trace_entries

    # Evaluate each expectation
    for exp in expectations:
        matches: List[EventMatch] = []
        pat = re.compile(exp.event, re.IGNORECASE)

        for entry in all_entries:
            matched = False
            if entry.event_name and pat.search(entry.event_name):
                matched = True
            elif pat.search(entry.raw_line):
                matched = True

            if matched:
                source = "trace" if entry in trace_entries else "syslog"
                matches.append(EventMatch(
                    event_name=entry.event_name or exp.event,
                    source=source,
                    timestamp=entry.timestamp,
                    raw_line=entry.raw_line,
                    severity=entry.severity,
                ))

        found_count = len(matches)
        passed, assessment = _evaluate_event_rule(exp, found_count)

        result.items.append(EventAuditItem(
            event=exp.event,
            expect=exp.expect,
            found_count=found_count,
            passed=passed,
            assessment=assessment,
            matches=matches,
            description=exp.description,
        ))

    return result


def load_event_expectations(recipe: Dict[str, Any]) -> List[EventExpectation]:
    """Load event expectations from a recipe dict."""
    raw = recipe.get("event_expectations", [])
    return [EventExpectation.from_dict(d) for d in raw]


# ---------------------------------------------------------------------------
# Rule evaluation
# ---------------------------------------------------------------------------

def _evaluate_event_rule(
    exp: EventExpectation,
    found_count: int,
) -> Tuple[bool, str]:
    """Evaluate a single event expectation. Returns (passed, assessment)."""

    if exp.expect == "present":
        min_c = exp.min_count or 1
        if found_count >= min_c:
            if exp.max_count is not None and found_count > exp.max_count:
                return False, f"found {found_count}, exceeds max {exp.max_count}"
            return True, f"found {found_count} (>= {min_c})"
        return False, f"expected >= {min_c}, found {found_count}"

    if exp.expect == "absent":
        if found_count == 0:
            return True, "correctly absent"
        return False, f"expected absent, found {found_count}"

    if exp.expect == "count_range":
        lo = exp.min_count or 0
        hi = exp.max_count if exp.max_count is not None else float("inf")
        ok = lo <= found_count <= hi
        return ok, f"found {found_count}, range [{lo}, {hi}], {'in range' if ok else 'OUT OF RANGE'}"

    return True, f"unknown expect '{exp.expect}', defaulting PASS"
