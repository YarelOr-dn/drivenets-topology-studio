#!/usr/bin/env python3
"""
Generic DNOS syslog line parser.

Parses lines from:
  - `show file log routing_engine/system-events.log`
  - Real-time `set logging terminal` output
  - Trace file greps

DNOS syslog format (typical):
  2026-03-20T14:23:45.123+00:00 PE-4 bgpd[1234]: [INFO] BGP neighbor 1.2.3.4 Up
  Mar 20 14:23:45 PE-4 evpn: L2_MAC_MOBILITY_MAC_ADDRESS_SUPPRESSED ...

Both ISO and traditional syslog timestamp formats are supported.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

_ISO_TS_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:?\d{2}|Z)?)"
)
_SYSLOG_TS_RE = re.compile(
    r"^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"
)

_SEVERITY_RE = re.compile(
    r"\[(INFO|WARN|WARNING|ERROR|CRITICAL|DEBUG|NOTICE|ALERT|EMERG)\]",
    re.IGNORECASE,
)

_DNOS_EVENT_RE = re.compile(
    r"(L2_[A-Z_]+|BGP_[A-Z_]+|EVPN_[A-Z_]+|SYSTEM_[A-Z_]+|HA_[A-Z_]+|"
    r"INTERFACE_[A-Z_]+|OSPF_[A-Z_]+|ISIS_[A-Z_]+|MPLS_[A-Z_]+|"
    r"FLOWSPEC_[A-Z_]+|NCP_[A-Z_]+|NCC_[A-Z_]+)"
)


@dataclass
class SyslogEntry:
    """One parsed syslog line."""
    raw_line: str
    timestamp: Optional[str] = None
    hostname: Optional[str] = None
    process: Optional[str] = None
    severity: Optional[str] = None
    event_name: Optional[str] = None
    message: str = ""

    def matches_pattern(self, pattern: str) -> bool:
        """Check if this entry matches a regex pattern (case-insensitive)."""
        return bool(re.search(pattern, self.raw_line, re.IGNORECASE))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "hostname": self.hostname,
            "process": self.process,
            "severity": self.severity,
            "event_name": self.event_name,
            "message": self.message[:500],
        }


def parse_syslog_line(line: str) -> SyslogEntry:
    """Parse a single syslog line into structured fields."""
    clean = _ANSI_RE.sub("", line).strip()
    entry = SyslogEntry(raw_line=clean, message=clean)

    # Timestamp
    m = _ISO_TS_RE.search(clean)
    if m:
        entry.timestamp = m.group(1)
        rest = clean[m.end():].strip()
    else:
        m = _SYSLOG_TS_RE.match(clean)
        if m:
            entry.timestamp = m.group(1)
            rest = clean[m.end():].strip()
        else:
            rest = clean

    # Hostname (first word after timestamp)
    parts = rest.split(None, 1)
    if len(parts) >= 2:
        if not parts[0].startswith("["):
            entry.hostname = parts[0]
            rest = parts[1]

    # Process (word ending with colon or bracketed PID)
    proc_m = re.match(r"(\S+?)(?:\[\d+\])?:\s*(.*)", rest)
    if proc_m:
        entry.process = proc_m.group(1)
        entry.message = proc_m.group(2)

    # Severity
    sev_m = _SEVERITY_RE.search(clean)
    if sev_m:
        entry.severity = sev_m.group(1).upper()

    # DNOS event name
    evt_m = _DNOS_EVENT_RE.search(clean)
    if evt_m:
        entry.event_name = evt_m.group(1)

    return entry


def parse_syslog_output(output: str) -> List[SyslogEntry]:
    """Parse multi-line syslog output into a list of entries."""
    entries = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("---") or line.startswith("==="):
            continue
        entries.append(parse_syslog_line(line))
    return entries


def filter_by_event(entries: List[SyslogEntry], event_pattern: str) -> List[SyslogEntry]:
    """Filter syslog entries by event name pattern (regex)."""
    pat = re.compile(event_pattern, re.IGNORECASE)
    return [e for e in entries if e.event_name and pat.search(e.event_name)]


def filter_by_severity(entries: List[SyslogEntry], min_severity: str = "WARN") -> List[SyslogEntry]:
    """Filter entries at or above a minimum severity level."""
    severity_order = {"DEBUG": 0, "INFO": 1, "NOTICE": 2, "WARN": 3, "WARNING": 3,
                      "ERROR": 4, "CRITICAL": 5, "ALERT": 6, "EMERG": 7}
    min_level = severity_order.get(min_severity.upper(), 3)
    return [e for e in entries if severity_order.get(e.severity or "", 0) >= min_level]


def filter_by_timestamp_range(
    entries: List[SyslogEntry],
    after_hhmm: str,
    before_hhmm: Optional[str] = None,
) -> List[SyslogEntry]:
    """Filter entries by HH:MM timestamp range (string comparison on time portion)."""
    result = []
    for e in entries:
        if not e.timestamp:
            continue
        ts_m = re.search(r"(\d{2}:\d{2})", e.timestamp)
        if not ts_m:
            continue
        hhmm = ts_m.group(1)
        if hhmm >= after_hhmm:
            if before_hhmm is None or hhmm <= before_hhmm:
                result.append(e)
    return result
