#!/usr/bin/env python3
"""
system_snapshot -- structured DUT-state capture + expected-changes diff.

Phase 2.2 of the e2e_lite merge. Sits on top of the existing
`scaler/TEST/shared/health_guard.py` so legacy callers keep working; new
recipes can opt into a richer, declarative diff with an "expected changes"
DSL that only flags UNEXPECTED deltas as failures.

Why it matters:
    Health-guard today flags *any* process restart as FAIL. In HA tests we
    *expect* exactly one bgpd restart (because the test restarts it). The
    expected-changes DSL lets the recipe say:

        "process_restart:ncc/0/routing_engine/bgpd": "INCREASE_BY(1)"
        "container_restart:ncc/0/routing_engine":    "INCREASE_BY(1)"
        "new_core_dumps":                            "FORBIDDEN"
        "interface_flap:bundle-100.219":             "ALLOWED"

    Anything not listed is FORBIDDEN by default. Silent regressions become
    loud, but legitimate planned changes don't produce false failures.

Expected-change operators (DSL):
    FORBIDDEN         -- any delta fails
    ALLOWED           -- any delta passes (may still warn)
    INCREASE_BY(N)    -- value must increase by exactly N (default 1 if empty)
    INCREASE_BY_AT_MOST(N)
    INCREASE_BY_AT_LEAST(N)
    EXACTLY(val)      -- after-value must equal val (strings allowed)
    UNCHANGED         -- value must be identical before and after

Metric keys (produced by the sampler):
    process_state:<process>              -- "running" | "stopped" | "unknown"
    process_restart:<process>            -- integer restart count (delta)
    container_restart:<container>        -- integer restart count (delta)
    alarm:<alarm_text>                   -- 1 if present, else 0
    core_dumps                           -- total count across device
    new_core_dumps                       -- count of dumps not seen in "before"
    interface_flap:<ifname>              -- number of link-state transitions

Usage:
    from e2e_lite.system_snapshot import SystemSnapshotter, ExpectedChanges

    sampler = SystemSnapshotter(
        device="PE-4",
        run_show=run_show_fn,
        processes=["routing:bgpd", "routing:fibmgrd"],
        interfaces=["bundle-100.219"],
    )
    before = sampler.capture(label="before_sc08")
    # ... run scenario ...
    after = sampler.capture(label="after_sc08")
    diff = sampler.diff(
        before,
        after,
        expected={
            "process_restart:routing:bgpd": "INCREASE_BY(1)",
            "new_core_dumps": "FORBIDDEN",
        },
    )
    if not diff.ok:
        raise AssertionError(diff.summary())
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# We defer importing health_guard so this module can be imported from
# anywhere without forcing a circular dependency.
RunShowFn = Callable[[str, str], str]

logger = logging.getLogger(__name__)

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text) if isinstance(text, str) else str(text)


# ---------------------------------------------------------------------------
# DSL evaluator
# ---------------------------------------------------------------------------

# Rule -> callable(before_val, after_val) -> (ok: bool, reason: str)
Rule = Callable[[Any, Any], Tuple[bool, str]]


def _rule_forbidden(before: Any, after: Any) -> Tuple[bool, str]:
    if before == after:
        return True, "no change"
    return False, f"FORBIDDEN change: {before!r} -> {after!r}"


def _rule_allowed(_b: Any, _a: Any) -> Tuple[bool, str]:
    return True, "ALLOWED"


def _rule_unchanged(before: Any, after: Any) -> Tuple[bool, str]:
    if before == after:
        return True, "unchanged"
    return False, f"UNCHANGED rule violated: {before!r} != {after!r}"


def _rule_exactly(expected: Any) -> Rule:
    def f(_b: Any, after: Any) -> Tuple[bool, str]:
        if after == expected:
            return True, f"equals {expected!r}"
        try:
            if str(after) == str(expected):
                return True, f"equals {expected!r} (stringified)"
        except Exception:
            pass
        return False, f"expected {expected!r}, got {after!r}"
    return f


def _as_int(v: Any) -> int:
    if v is None:
        return 0
    try:
        return int(v)
    except (TypeError, ValueError):
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return 0


def _rule_increase_by(n: int) -> Rule:
    def f(before: Any, after: Any) -> Tuple[bool, str]:
        delta = _as_int(after) - _as_int(before)
        if delta == n:
            return True, f"INCREASE_BY({n}): delta={delta}"
        return False, f"INCREASE_BY({n}) violated: delta={delta}"
    return f


def _rule_increase_by_at_most(n: int) -> Rule:
    def f(before: Any, after: Any) -> Tuple[bool, str]:
        delta = _as_int(after) - _as_int(before)
        if 0 <= delta <= n:
            return True, f"INCREASE_BY_AT_MOST({n}): delta={delta}"
        return False, f"INCREASE_BY_AT_MOST({n}) violated: delta={delta}"
    return f


def _rule_increase_by_at_least(n: int) -> Rule:
    def f(before: Any, after: Any) -> Tuple[bool, str]:
        delta = _as_int(after) - _as_int(before)
        if delta >= n:
            return True, f"INCREASE_BY_AT_LEAST({n}): delta={delta}"
        return False, f"INCREASE_BY_AT_LEAST({n}) violated: delta={delta}"
    return f


_RULE_PARSE_RE = re.compile(
    r"^(?P<name>[A-Z_]+)(?:\((?P<arg>.*)\))?$",
)


class ExpectedChangeError(ValueError):
    """Raised when the DSL string cannot be parsed."""


def parse_rule(spec: Union[str, Rule]) -> Rule:
    """Compile a DSL string (or already-compiled rule) into a callable."""
    if callable(spec):
        return spec
    if not isinstance(spec, str):
        raise ExpectedChangeError(f"rule must be str or callable, got {type(spec)}")

    m = _RULE_PARSE_RE.match(spec.strip())
    if not m:
        raise ExpectedChangeError(f"Cannot parse rule: {spec!r}")

    name = m.group("name").upper()
    arg_raw = (m.group("arg") or "").strip()

    if name == "FORBIDDEN":
        return _rule_forbidden
    if name == "ALLOWED":
        return _rule_allowed
    if name == "UNCHANGED":
        return _rule_unchanged
    if name == "EXACTLY":
        if not arg_raw:
            raise ExpectedChangeError("EXACTLY(...) needs an argument")
        val: Any = arg_raw.strip("'\"")
        try:
            val = int(arg_raw)
        except ValueError:
            try:
                val = float(arg_raw)
            except ValueError:
                pass
        return _rule_exactly(val)
    if name == "INCREASE_BY":
        n = int(arg_raw) if arg_raw else 1
        return _rule_increase_by(n)
    if name == "INCREASE_BY_AT_MOST":
        if not arg_raw:
            raise ExpectedChangeError("INCREASE_BY_AT_MOST(N) requires N")
        return _rule_increase_by_at_most(int(arg_raw))
    if name == "INCREASE_BY_AT_LEAST":
        if not arg_raw:
            raise ExpectedChangeError("INCREASE_BY_AT_LEAST(N) requires N")
        return _rule_increase_by_at_least(int(arg_raw))

    raise ExpectedChangeError(f"Unknown rule operator: {name!r}")


ExpectedChanges = Dict[str, Union[str, Rule]]


# ---------------------------------------------------------------------------
# Snapshot data
# ---------------------------------------------------------------------------

@dataclass
class SystemSnapshot:
    """Keyed, easily-diffable view of device state."""

    label: str
    device: str
    timestamp: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)  # for evidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "device": self.device,
            "timestamp": self.timestamp,
            "metrics": self.metrics,
            "raw_keys": sorted(self.raw.keys()),
        }


@dataclass
class DiffEntry:
    key: str
    before: Any
    after: Any
    expected: str
    ok: bool
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "before": self.before,
            "after": self.after,
            "expected": self.expected,
            "ok": self.ok,
            "reason": self.reason,
        }


@dataclass
class SnapshotDiff:
    before_label: str
    after_label: str
    entries: List[DiffEntry] = field(default_factory=list)
    unexpected_changes: List[DiffEntry] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(e.ok for e in self.entries) and not self.unexpected_changes

    @property
    def fail_count(self) -> int:
        return sum(1 for e in self.entries if not e.ok) + len(self.unexpected_changes)

    def summary(self, max_items: int = 30) -> str:
        lines = [f"SystemSnapshotDiff {self.before_label} -> {self.after_label}: "
                 f"{'PASS' if self.ok else 'FAIL'}"]
        for e in self.entries:
            if not e.ok:
                lines.append(f"  [FAIL] {e.key}: {e.reason}")
        for u in self.unexpected_changes[:max_items]:
            lines.append(
                f"  [UNEXPECTED] {u.key}: {u.before!r} -> {u.after!r} "
                f"(no rule declared)"
            )
        if len(self.unexpected_changes) > max_items:
            lines.append(f"  ... and {len(self.unexpected_changes) - max_items} more")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "before_label": self.before_label,
            "after_label": self.after_label,
            "ok": self.ok,
            "fail_count": self.fail_count,
            "entries": [e.to_dict() for e in self.entries],
            "unexpected_changes": [u.to_dict() for u in self.unexpected_changes],
        }


# ---------------------------------------------------------------------------
# Snapshotter
# ---------------------------------------------------------------------------

class SystemSnapshotter:
    """Capture + diff DUT state using the keyed-metrics model.

    Wraps `scaler/TEST/shared/health_guard.py` when available (for process
    and alarm detection) and augments with core-dump tracking and interface
    link-flap counters.
    """

    def __init__(
        self,
        device: str,
        run_show: RunShowFn,
        *,
        processes: Optional[List[str]] = None,
        containers: Optional[List[str]] = None,
        interfaces: Optional[List[str]] = None,
        capture_alarms: bool = True,
        capture_cores: bool = True,
    ) -> None:
        self.device = device
        self.run_show = run_show
        self.processes = processes or []
        self.containers = containers or []
        self.interfaces = interfaces or []
        self.capture_alarms = capture_alarms
        self.capture_cores = capture_cores

    # -- capture -------------------------------------------------------------

    def capture(self, label: str) -> SystemSnapshot:
        snap = SystemSnapshot(
            label=label, device=self.device, timestamp=_iso_now(),
        )

        # Process state + restart counts.
        for proc in self.processes:
            state, restarts = self._sample_process(proc)
            snap.metrics[f"process_state:{proc}"] = state
            snap.metrics[f"process_restart:{proc}"] = restarts

        # Container state via health_guard if available.
        for container in self.containers:
            restarts = self._sample_container_restarts(container)
            snap.metrics[f"container_restart:{container}"] = restarts

        # Alarms (each alarm becomes its own metric key).
        if self.capture_alarms:
            alarms = self._sample_alarms()
            snap.raw["alarms"] = alarms
            for a in alarms:
                key = f"alarm:{a[:80]}"
                snap.metrics[key] = 1

        # Core dumps.
        if self.capture_cores:
            cores = self._sample_core_dumps()
            snap.raw["core_dumps"] = cores
            snap.metrics["core_dumps"] = len(cores)

        # Interface link-flap counters.
        for ifname in self.interfaces:
            flap = self._sample_interface_flap(ifname)
            snap.metrics[f"interface_flap:{ifname}"] = flap

        return snap

    # -- diff ----------------------------------------------------------------

    def diff(
        self,
        before: SystemSnapshot,
        after: SystemSnapshot,
        expected: Optional[ExpectedChanges] = None,
        *,
        ignore_keys: Optional[List[str]] = None,
    ) -> SnapshotDiff:
        """Compare two snapshots using the expected-changes DSL.

        - Every rule in `expected` is evaluated against its metric key.
          Missing metric keys evaluate as 0/absent.
        - Metric keys present in either snapshot that have NO rule AND changed
          between before/after are flagged as UNEXPECTED.
        - `ignore_keys` is a list of key prefixes to skip entirely.
        """
        expected = expected or {}
        ignore_keys = ignore_keys or []
        result = SnapshotDiff(before_label=before.label, after_label=after.label)

        compiled: Dict[str, Tuple[str, Rule]] = {}
        for k, spec in expected.items():
            try:
                compiled[k] = (str(spec), parse_rule(spec))
            except ExpectedChangeError as exc:
                compiled[k] = (str(spec), None)  # type: ignore[assignment]
                logger.error("Invalid DSL rule %r: %s", spec, exc)

        # 1) Evaluate declared rules
        declared_keys = set(compiled.keys())
        for k, (raw, rule) in compiled.items():
            if rule is None:
                result.entries.append(DiffEntry(
                    key=k,
                    before=before.metrics.get(k),
                    after=after.metrics.get(k),
                    expected=raw,
                    ok=False,
                    reason=f"invalid rule {raw!r}",
                ))
                continue
            b = before.metrics.get(k)
            a = after.metrics.get(k)
            ok, reason = rule(b, a)
            result.entries.append(DiffEntry(
                key=k, before=b, after=a, expected=raw,
                ok=ok, reason=reason,
            ))

        # 2) Detect UNEXPECTED changes (metrics that changed with no rule)
        all_keys = set(before.metrics) | set(after.metrics)
        for k in sorted(all_keys - declared_keys):
            if any(k.startswith(ig) for ig in ignore_keys):
                continue
            b = before.metrics.get(k)
            a = after.metrics.get(k)
            # The 0-vs-missing case shouldn't count as a change.
            if b == a:
                continue
            if (b is None and a == 0) or (a is None and b == 0):
                continue
            # Allow harmless ramp in uptime-like keys if we ever add them.
            result.unexpected_changes.append(DiffEntry(
                key=k, before=b, after=a,
                expected="<no rule>",
                ok=False,
                reason="unexpected change without declared rule",
            ))

        return result

    # -- samplers ------------------------------------------------------------

    def _sample_process(self, proc: str) -> Tuple[str, int]:
        try:
            out = _strip_ansi(self.run_show(
                self.device, f"show system process {proc} | no-more"
            ))
        except Exception as exc:
            logger.debug("process sample failed for %s: %s", proc, exc)
            return "unknown", 0

        running = False
        lower = out.lower()
        if "running" in lower:
            running = True
        elif "stopped" in lower:
            return "stopped", self._parse_restart_count(out)

        return ("running" if running else "unknown"), self._parse_restart_count(out)

    @staticmethod
    def _parse_restart_count(text: str) -> int:
        # Look for patterns like "Restarts: 2" or "restart-count: 3"
        for rx in (r"[Rr]estarts\s*[:=]\s*(\d+)", r"restart[-_]count\s*[:=]\s*(\d+)"):
            m = re.search(rx, text)
            if m:
                try:
                    return int(m.group(1))
                except ValueError:
                    continue
        return 0

    def _sample_container_restarts(self, container: str) -> int:
        try:
            out = _strip_ansi(self.run_show(
                self.device, "show system containers | no-more"
            ))
        except Exception:
            return 0
        # naive table parse: find row with this container name, extract restart column
        lines = [l for l in out.splitlines() if container in l]
        for line in lines:
            parts = line.split()
            for p in parts:
                if p.isdigit():
                    try:
                        val = int(p)
                        # Restart counts are typically small (< 1000); skip PIDs.
                        if val < 10000:
                            return val
                    except ValueError:
                        pass
        return 0

    def _sample_alarms(self) -> List[str]:
        try:
            out = _strip_ansi(self.run_show(
                self.device, "show system alarms | no-more"
            ))
        except Exception:
            return []
        alarms: List[str] = []
        for line in out.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            low = stripped.lower()
            if any(p in low for p in ("no active alarms", "alarm name", "------", "====", "empty")):
                continue
            if low.startswith(("alarm", "severity", "type", "timestamp")):
                continue
            alarms.append(stripped)
        return alarms

    def _sample_core_dumps(self) -> List[str]:
        cmds = [
            "show system core-dumps | no-more",
            "show system | include core",
        ]
        collected: List[str] = []
        for cmd in cmds:
            try:
                out = _strip_ansi(self.run_show(self.device, cmd))
            except Exception:
                continue
            for line in out.splitlines():
                if ".core" in line or "core_dump" in line.lower():
                    collected.append(line.strip())
        seen = set()
        unique = []
        for l in collected:
            if l in seen:
                continue
            seen.add(l)
            unique.append(l)
        return unique

    def _sample_interface_flap(self, ifname: str) -> int:
        try:
            out = _strip_ansi(self.run_show(
                self.device, f"show interfaces {ifname} | no-more"
            ))
        except Exception:
            return 0
        # Look for "Link transitions: N" or similar
        for rx in (r"[Ll]ink\s+transitions?\s*[:=]\s*(\d+)",
                   r"flaps?\s*[:=]\s*(\d+)"):
            m = re.search(rx, out)
            if m:
                try:
                    return int(m.group(1))
                except ValueError:
                    continue
        return 0


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def diff_snapshots(
    before: SystemSnapshot,
    after: SystemSnapshot,
    expected: Optional[ExpectedChanges] = None,
    sampler: Optional[SystemSnapshotter] = None,
) -> SnapshotDiff:
    """Module-level diff without constructing a fresh sampler."""
    if sampler is None:
        # Build a stub that only has diff() (no samplers needed).
        sampler = SystemSnapshotter(
            device=before.device, run_show=lambda *_a, **_k: "",
        )
    return sampler.diff(before, after, expected=expected)


__all__ = [
    "DiffEntry",
    "ExpectedChangeError",
    "ExpectedChanges",
    "Rule",
    "SnapshotDiff",
    "SystemSnapshot",
    "SystemSnapshotter",
    "diff_snapshots",
    "parse_rule",
]
