#!/usr/bin/env python3
"""
Generic before/after counter snapshot + diff engine.

Reads counter commands and expectations from recipe JSON.  Parses DNOS CLI
counter output into numeric values, compares before/after snapshots, and
reports deltas with PASS/FAIL assessment.

Recipe JSON format (inside scenario or top-level):
    "counter_commands": [
        {"label": "evpn_mac_count", "command": "show evpn mac summary | no-more",
         "parser": "first_integer", "description": "Total EVPN MACs"},
        ...
    ],
    "counter_expectations": [
        {"label": "evpn_mac_count", "rule": "no_decrease",
         "description": "MAC count must not drop"},
        {"label": "error_drops", "rule": "zero", "description": "No new error drops"},
        ...
    ]

Parser types:
    first_integer   -- extract first integer from output
    key_value       -- parse "key: value" lines into dict
    table_sum       -- sum all integers in a column
    line_count      -- count non-empty output lines
    regex           -- use custom regex pattern from "regex" field
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

RunShowFn = Callable[[str, str], str]

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text) if isinstance(text, str) else str(text)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CounterCommand:
    """One counter to track: the CLI command, a label, and how to parse it."""
    label: str
    command: str
    parser: str = "first_integer"
    regex: str = ""
    description: str = ""

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CounterCommand":
        return cls(
            label=d["label"],
            command=d["command"],
            parser=d.get("parser", "first_integer"),
            regex=d.get("regex", ""),
            description=d.get("description", ""),
        )


@dataclass
class CounterValue:
    """Parsed value from one counter command execution."""
    label: str
    raw_output: str
    value: Any  # int, float, dict, or None on parse failure
    timestamp: str = ""
    duration_ms: int = 0
    error: Optional[str] = None


@dataclass
class CounterSnapshot:
    """All counters at a single point in time."""
    label: str  # e.g. "before_trigger", "after_recovery"
    timestamp: str = ""
    values: Dict[str, CounterValue] = field(default_factory=dict)

    def get_value(self, counter_label: str) -> Any:
        cv = self.values.get(counter_label)
        return cv.value if cv else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "timestamp": self.timestamp,
            "counters": {
                k: {
                    "value": v.value,
                    "timestamp": v.timestamp,
                    "duration_ms": v.duration_ms,
                    "error": v.error,
                }
                for k, v in self.values.items()
            },
        }


@dataclass
class CounterExpectation:
    """Rule for how a counter should behave between before/after."""
    label: str
    rule: str  # no_decrease, no_increase, zero, stable, increase, range
    min_val: Optional[int] = None
    max_val: Optional[int] = None
    description: str = ""

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CounterExpectation":
        return cls(
            label=d["label"],
            rule=d["rule"],
            min_val=d.get("min_val"),
            max_val=d.get("max_val"),
            description=d.get("description", ""),
        )


@dataclass
class CounterDiffItem:
    """Result of comparing one counter between before and after."""
    label: str
    before: Any
    after: Any
    delta: Any
    rule: str
    passed: bool
    assessment: str
    description: str = ""


@dataclass
class CounterDiffResult:
    """Full diff result across all tracked counters."""
    before_label: str
    after_label: str
    items: List[CounterDiffItem] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(i.passed for i in self.items)

    @property
    def fail_count(self) -> int:
        return sum(1 for i in self.items if not i.passed)

    def summary(self) -> str:
        parts = []
        for item in self.items:
            status = "PASS" if item.passed else "FAIL"
            parts.append(f"  [{status}] {item.label}: {item.before} -> {item.after} (delta={item.delta}, rule={item.rule})")
        header = f"Counter diff {self.before_label} -> {self.after_label}: {'PASS' if self.passed else 'FAIL'}"
        return header + "\n" + "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "before_label": self.before_label,
            "after_label": self.after_label,
            "passed": self.passed,
            "fail_count": self.fail_count,
            "items": [
                {
                    "label": i.label,
                    "before": i.before,
                    "after": i.after,
                    "delta": i.delta,
                    "rule": i.rule,
                    "passed": i.passed,
                    "assessment": i.assessment,
                    "description": i.description,
                }
                for i in self.items
            ],
        }


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def _parse_first_integer(output: str) -> Optional[int]:
    """Extract the first integer found in the output."""
    cleaned = _strip_ansi(output)
    m = re.search(r"\b(\d+)\b", cleaned)
    return int(m.group(1)) if m else None


def _parse_key_value(output: str) -> Dict[str, Any]:
    """Parse 'key: value' or 'key = value' lines into a dict."""
    result: Dict[str, Any] = {}
    for line in _strip_ansi(output).splitlines():
        line = line.strip()
        m = re.match(r"^(.+?)\s*[:=]\s*(.+)$", line)
        if m:
            key = m.group(1).strip().lower().replace(" ", "_")
            val_str = m.group(2).strip()
            try:
                result[key] = int(val_str)
            except ValueError:
                try:
                    result[key] = float(val_str)
                except ValueError:
                    result[key] = val_str
    return result


def _parse_table_sum(output: str) -> int:
    """Sum all integers found in the output (for counter/table aggregation)."""
    total = 0
    for m in re.finditer(r"\b(\d+)\b", _strip_ansi(output)):
        total += int(m.group(1))
    return total


def _parse_line_count(output: str) -> int:
    """Count non-empty, non-header lines."""
    lines = _strip_ansi(output).strip().splitlines()
    return len([l for l in lines if l.strip() and not l.strip().startswith("---")])


def _parse_regex(output: str, pattern: str) -> Optional[Any]:
    """Extract value using a custom regex pattern."""
    m = re.search(pattern, _strip_ansi(output))
    if not m:
        return None
    try:
        return int(m.group(1))
    except (ValueError, IndexError):
        try:
            return m.group(1)
        except IndexError:
            return m.group(0)


PARSERS = {
    "first_integer": lambda out, _: _parse_first_integer(out),
    "key_value": lambda out, _: _parse_key_value(out),
    "table_sum": lambda out, _: _parse_table_sum(out),
    "line_count": lambda out, _: _parse_line_count(out),
    "regex": lambda out, regex: _parse_regex(out, regex),
}


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def snapshot_counters(
    device: str,
    snapshot_label: str,
    counter_commands: List[CounterCommand],
    run_show: RunShowFn,
) -> CounterSnapshot:
    """Execute all counter commands and return a timestamped snapshot."""
    snap = CounterSnapshot(label=snapshot_label, timestamp=_iso_now())

    for cc in counter_commands:
        ts = _iso_now()
        t0 = time.monotonic()
        error = None
        raw = ""
        value: Any = None

        try:
            raw = run_show(device, cc.command)
        except Exception as exc:
            error = str(exc)

        duration_ms = int((time.monotonic() - t0) * 1000)

        if not error:
            parser_fn = PARSERS.get(cc.parser, PARSERS["first_integer"])
            try:
                value = parser_fn(raw, cc.regex)
            except Exception as exc:
                error = f"Parse error: {exc}"

        snap.values[cc.label] = CounterValue(
            label=cc.label,
            raw_output=raw,
            value=value,
            timestamp=ts,
            duration_ms=duration_ms,
            error=error,
        )

    return snap


def diff_counters(
    before: CounterSnapshot,
    after: CounterSnapshot,
    expectations: List[CounterExpectation],
) -> CounterDiffResult:
    """Compare two snapshots against expectation rules."""
    result = CounterDiffResult(
        before_label=before.label,
        after_label=after.label,
    )

    for exp in expectations:
        before_val = before.get_value(exp.label)
        after_val = after.get_value(exp.label)

        delta: Any = None
        if isinstance(before_val, (int, float)) and isinstance(after_val, (int, float)):
            delta = after_val - before_val

        passed, assessment = _evaluate_rule(exp.rule, before_val, after_val, delta, exp)

        result.items.append(CounterDiffItem(
            label=exp.label,
            before=before_val,
            after=after_val,
            delta=delta,
            rule=exp.rule,
            passed=passed,
            assessment=assessment,
            description=exp.description,
        ))

    return result


def load_counter_commands(recipe: Dict[str, Any]) -> List[CounterCommand]:
    """Load counter commands from a recipe dict."""
    raw = recipe.get("counter_commands", [])
    return [CounterCommand.from_dict(d) for d in raw]


def load_counter_expectations(recipe: Dict[str, Any]) -> List[CounterExpectation]:
    """Load counter expectations from a recipe dict."""
    raw = recipe.get("counter_expectations", [])
    return [CounterExpectation.from_dict(d) for d in raw]


# ---------------------------------------------------------------------------
# Rule evaluation
# ---------------------------------------------------------------------------

def _evaluate_rule(
    rule: str,
    before: Any,
    after: Any,
    delta: Any,
    exp: CounterExpectation,
) -> Tuple[bool, str]:
    """Evaluate a single expectation rule. Returns (passed, assessment)."""

    if before is None and after is None:
        return False, "both values missing"
    if after is None:
        return False, "after value missing"

    if rule == "no_decrease":
        if not isinstance(delta, (int, float)):
            return False, "non-numeric, cannot compare"
        return delta >= 0, f"delta={delta}, {'stable/increased' if delta >= 0 else 'DECREASED'}"

    if rule == "no_increase":
        if not isinstance(delta, (int, float)):
            return False, "non-numeric, cannot compare"
        return delta <= 0, f"delta={delta}, {'stable/decreased' if delta <= 0 else 'INCREASED'}"

    if rule == "zero":
        if isinstance(delta, (int, float)):
            return delta == 0, f"delta={delta}, {'zero' if delta == 0 else 'NON-ZERO'}"
        return after == before, f"{'unchanged' if after == before else 'CHANGED'}"

    if rule == "stable":
        return after == before, f"{'stable' if after == before else 'CHANGED'}"

    if rule == "increase":
        if not isinstance(delta, (int, float)):
            return False, "non-numeric, cannot compare"
        return delta > 0, f"delta={delta}, {'increased' if delta > 0 else 'NOT increased'}"

    if rule == "range":
        if not isinstance(after, (int, float)):
            return False, "non-numeric for range check"
        lo = exp.min_val if exp.min_val is not None else float("-inf")
        hi = exp.max_val if exp.max_val is not None else float("inf")
        ok = lo <= after <= hi
        return ok, f"value={after}, range=[{lo}, {hi}], {'in range' if ok else 'OUT OF RANGE'}"

    if rule == "non_zero":
        if isinstance(after, (int, float)):
            return after != 0, f"value={after}"
        return bool(after), f"value={after}"

    return True, f"unknown rule '{rule}', defaulting PASS"
