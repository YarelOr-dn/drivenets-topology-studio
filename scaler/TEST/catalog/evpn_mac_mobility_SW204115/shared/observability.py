#!/usr/bin/env python3
"""
Full observability pipeline for EVPN MAC mobility tests (SW-204115).

Captures every show-command execution with timestamp, duration, raw output,
and parsed values.  Groups captures by phase.  Records a timeline of events.
Computes before/after diffs.  Writes intermediate results after each phase
so evidence is never lost even on crash.  Packages everything for /debug-dnos
handoff.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


@dataclass
class CommandCapture:
    """One CLI command execution with full provenance."""

    command: str
    output: str
    timestamp: str
    duration_ms: int
    phase: str
    parsed: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "command": self.command,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "phase": self.phase,
            "output_length": len(self.output),
            "output_preview": self.output[:500],
        }
        if self.parsed:
            d["parsed"] = self.parsed
        if self.error:
            d["error"] = self.error
        return d

    def to_full_dict(self) -> Dict[str, Any]:
        d = self.to_dict()
        d["output_full"] = self.output
        return d


@dataclass
class TimelineEvent:
    """Single point in the execution timeline."""

    timestamp: str
    event_type: str   # phase_start, phase_end, command, anomaly, trigger, traffic
    message: str
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "message": self.message,
        }
        if self.data:
            d["data"] = self.data
        return d


@dataclass
class PhaseSummary:
    """Aggregated data for one execution phase."""

    phase_name: str
    started_at: str = ""
    completed_at: str = ""
    duration_sec: float = 0.0
    commands: List[CommandCapture] = field(default_factory=list)
    parsed_values: Dict[str, Any] = field(default_factory=dict)
    anomalies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase_name": self.phase_name,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_sec": round(self.duration_sec, 3),
            "command_count": len(self.commands),
            "commands": [c.to_dict() for c in self.commands],
            "parsed_values": self.parsed_values,
            "anomalies": self.anomalies,
        }


@dataclass
class SnapshotDiff:
    """Before/after comparison for a specific metric."""

    label: str
    command: str
    before_value: Any
    after_value: Any
    delta: Any = None
    assessment: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "command": self.command,
            "before": self.before_value,
            "after": self.after_value,
            "delta": self.delta,
            "assessment": self.assessment,
        }


@dataclass
class TrafficSnapshot:
    """Traffic stats captured at a specific moment."""

    label: str
    timestamp: str
    tx_frames: int = 0
    rx_frames: int = 0
    loss_frames: int = 0
    loss_pct: float = 0.0
    rate_mbps: float = 0.0
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "timestamp": self.timestamp,
            "tx_frames": self.tx_frames,
            "rx_frames": self.rx_frames,
            "loss_frames": self.loss_frames,
            "loss_pct": round(self.loss_pct, 4),
            "rate_mbps": round(self.rate_mbps, 2),
            "raw": self.raw,
        }


class ObservabilityCollector:
    """
    Central collector that instruments every phase of test execution.

    Usage:
        obs = ObservabilityCollector("TEST_xxx", "scenario_yyy", "PE-4")
        obs.begin_phase("snapshot")
        out = obs.run_and_record(device, cmd, run_show)
        obs.record_parsed("mac_count", 42)
        obs.end_phase()
        ...
        obs.finalize()
        obs.write_all(run_dir)
    """

    def __init__(
        self,
        test_id: str,
        scenario_id: str,
        device: str,
    ) -> None:
        self.test_id = test_id
        self.scenario_id = scenario_id
        self.device = device
        self.started_at = _iso_now()
        self.completed_at = ""

        self._phases: List[PhaseSummary] = []
        self._current_phase: Optional[PhaseSummary] = None
        self._timeline: List[TimelineEvent] = []
        self._diffs: List[SnapshotDiff] = []
        self._traffic_snapshots: List[TrafficSnapshot] = []
        self._all_captures: List[CommandCapture] = []
        self._snapshots: Dict[str, Dict[str, Any]] = {}
        self._intermediate_dir: Optional[Path] = None

    # -- Phase lifecycle -------------------------------------------------

    def begin_phase(self, phase_name: str) -> None:
        if self._current_phase is not None:
            self.end_phase()

        now = _iso_now()
        self._current_phase = PhaseSummary(phase_name=phase_name, started_at=now)
        self._timeline.append(TimelineEvent(
            timestamp=now, event_type="phase_start",
            message=f"Phase '{phase_name}' started",
        ))

    def end_phase(self) -> Optional[PhaseSummary]:
        if self._current_phase is None:
            return None

        now = _iso_now()
        phase = self._current_phase
        phase.completed_at = now
        phase.duration_sec = (
            _parse_iso_epoch(now) - _parse_iso_epoch(phase.started_at)
        )
        self._phases.append(phase)
        self._timeline.append(TimelineEvent(
            timestamp=now, event_type="phase_end",
            message=f"Phase '{phase.phase_name}' completed ({phase.duration_sec:.2f}s, {len(phase.commands)} commands)",
            data={"duration_sec": phase.duration_sec, "command_count": len(phase.commands)},
        ))
        self._current_phase = None

        if self._intermediate_dir:
            self._write_intermediate_phase(phase)

        return phase

    # -- Command recording -----------------------------------------------

    def run_and_record(
        self,
        device: str,
        command: str,
        run_show: Callable[[str, str], str],
        parse_fn: Optional[Callable[[str], Any]] = None,
    ) -> str:
        phase_name = self._current_phase.phase_name if self._current_phase else "unphased"
        ts = _iso_now()
        t0 = time.monotonic()
        error = None

        try:
            output = run_show(device, command)
        except Exception as exc:
            output = ""
            error = str(exc)

        duration_ms = int((time.monotonic() - t0) * 1000)

        parsed = None
        if parse_fn and output and not error:
            try:
                parsed = parse_fn(output)
            except Exception:
                pass

        capture = CommandCapture(
            command=command,
            output=output,
            timestamp=ts,
            duration_ms=duration_ms,
            phase=phase_name,
            parsed=parsed if isinstance(parsed, dict) else ({"value": parsed} if parsed is not None else None),
            error=error,
        )
        self._all_captures.append(capture)

        if self._current_phase:
            self._current_phase.commands.append(capture)

        self._timeline.append(TimelineEvent(
            timestamp=ts, event_type="command",
            message=f"[{phase_name}] {command} ({duration_ms}ms, {len(output)} chars)",
            data={"command": command, "duration_ms": duration_ms, "output_length": len(output)},
        ))

        if error:
            self.record_anomaly(f"Command error: {command} -> {error}")

        return output

    def record_parsed(self, key: str, value: Any) -> None:
        if self._current_phase:
            self._current_phase.parsed_values[key] = value

    def record_anomaly(self, message: str) -> None:
        ts = _iso_now()
        if self._current_phase:
            self._current_phase.anomalies.append(f"[{ts}] {message}")
        self._timeline.append(TimelineEvent(
            timestamp=ts, event_type="anomaly",
            message=message,
        ))

    def record_event(self, event_type: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        self._timeline.append(TimelineEvent(
            timestamp=_iso_now(), event_type=event_type,
            message=message, data=data,
        ))

    # -- Snapshot & diff --------------------------------------------------

    def save_snapshot(self, label: str, data: Dict[str, Any]) -> None:
        self._snapshots[label] = data

    def compute_diff(
        self,
        label: str,
        command: str,
        before_key: str,
        after_key: str,
        before_val: Any,
        after_val: Any,
    ) -> SnapshotDiff:
        delta = None
        assessment = "changed"
        if isinstance(before_val, (int, float)) and isinstance(after_val, (int, float)):
            delta = after_val - before_val
            if delta == 0:
                assessment = "stable"
            elif delta > 0:
                assessment = "increased"
            else:
                assessment = "decreased"
        elif before_val == after_val:
            assessment = "unchanged"

        diff = SnapshotDiff(
            label=label, command=command,
            before_value=before_val, after_value=after_val,
            delta=delta, assessment=assessment,
        )
        self._diffs.append(diff)
        self.record_event("diff", f"Diff '{label}': {before_val} -> {after_val} ({assessment})", diff.to_dict())
        return diff

    # -- Traffic stats ---------------------------------------------------

    def capture_traffic_stats(
        self,
        label: str,
        tx_frames: int = 0,
        rx_frames: int = 0,
        rate_mbps: float = 0.0,
        raw: Optional[Dict[str, Any]] = None,
    ) -> TrafficSnapshot:
        loss = max(0, tx_frames - rx_frames)
        loss_pct = (loss / tx_frames * 100) if tx_frames > 0 else 0.0

        snap = TrafficSnapshot(
            label=label, timestamp=_iso_now(),
            tx_frames=tx_frames, rx_frames=rx_frames,
            loss_frames=loss, loss_pct=loss_pct,
            rate_mbps=rate_mbps, raw=raw or {},
        )
        self._traffic_snapshots.append(snap)
        self.record_event(
            "traffic", f"Traffic '{label}': TX={tx_frames} RX={rx_frames} loss={loss_pct:.2f}%",
            snap.to_dict(),
        )
        return snap

    def get_traffic_stats(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self._traffic_snapshots]

    # -- Extended recording (Tier 1 engine integration) ------------------

    def record_counter_snapshot(self, snapshot_data: Dict[str, Any]) -> None:
        """Record a counter snapshot from counter_tracker engine."""
        label = snapshot_data.get("label", "counters")
        self._snapshots[f"counters_{label}"] = snapshot_data
        self.record_event("counter_snapshot", f"Counter snapshot '{label}' recorded",
                          {"label": label, "counter_count": len(snapshot_data.get("counters", {}))})

    def record_counter_diff(self, diff_data: Dict[str, Any]) -> None:
        """Record a counter diff result from counter_tracker engine."""
        self._snapshots["counter_diff"] = diff_data
        passed = diff_data.get("passed", True)
        fail_count = diff_data.get("fail_count", 0)
        self.record_event("counter_diff",
                          f"Counter diff: {'PASS' if passed else f'FAIL ({fail_count} failures)'}",
                          diff_data)
        if not passed:
            self.record_anomaly(f"Counter diff FAIL: {fail_count} counter(s) violated expectations")

    def record_event_audit(self, audit_data: Dict[str, Any]) -> None:
        """Record an event audit result from event_tracker engine."""
        self._snapshots["event_audit"] = audit_data
        passed = audit_data.get("passed", True)
        fail_count = audit_data.get("fail_count", 0)
        self.record_event("event_audit",
                          f"Event audit: {'PASS' if passed else f'FAIL ({fail_count} mismatches)'}",
                          {"passed": passed, "fail_count": fail_count})
        if not passed:
            self.record_anomaly(f"Event audit FAIL: {fail_count} event expectation(s) violated")

    def record_xray_capture(self, xray_data: Dict[str, Any]) -> None:
        """Record an XRAY capture result."""
        self._snapshots["xray_capture"] = xray_data
        triggered = xray_data.get("triggered", False)
        self.record_event("xray", f"XRAY capture: {'triggered' if triggered else 'not triggered'}",
                          xray_data)

    def record_bgp_health(self, bgp_data: Dict[str, Any]) -> None:
        """Record BGP health check result."""
        self._snapshots["bgp_health"] = bgp_data
        state = bgp_data.get("state", "unknown")
        self.record_event("bgp_health", f"BGP health: {state}", bgp_data)
        if state not in ("Established", "established", "healthy"):
            self.record_anomaly(f"BGP health degraded: {state}")

    def record_spirent_crossref(self, crossref_data: Dict[str, Any]) -> None:
        """Record Spirent-DUT cross-reference result."""
        self._snapshots["spirent_crossref"] = crossref_data
        matched = crossref_data.get("matched", False)
        self.record_event("spirent_crossref",
                          f"Spirent-DUT crossref: {'MATCH' if matched else 'MISMATCH'}",
                          crossref_data)
        if not matched:
            self.record_anomaly(f"Spirent-DUT counter mismatch: {crossref_data.get('detail', '')}")

    # -- Finalization & output -------------------------------------------

    def finalize(self) -> Dict[str, Any]:
        if self._current_phase:
            self.end_phase()
        self.completed_at = _iso_now()
        return self.to_dict()

    def to_dict(self) -> Dict[str, Any]:
        total_commands = len(self._all_captures)
        total_anomalies = sum(len(p.anomalies) for p in self._phases)
        total_duration = sum(p.duration_sec for p in self._phases)

        result = {
            "meta": {
                "test_id": self.test_id,
                "scenario_id": self.scenario_id,
                "device": self.device,
                "started_at": self.started_at,
                "completed_at": self.completed_at,
                "total_duration_sec": round(total_duration, 3),
                "total_commands": total_commands,
                "total_anomalies": total_anomalies,
                "phase_count": len(self._phases),
            },
            "phases": [p.to_dict() for p in self._phases],
            "diffs": [d.to_dict() for d in self._diffs],
            "traffic_snapshots": [t.to_dict() for t in self._traffic_snapshots],
            "timeline": [e.to_dict() for e in self._timeline],
        }
        engine_keys = ["counters_before", "counters_after", "counter_diff",
                       "event_audit", "xray_capture", "bgp_health", "spirent_crossref"]
        engine_snapshots = {k: v for k, v in self._snapshots.items() if k in engine_keys or k.startswith("counters_")}
        if engine_snapshots:
            result["engine_data"] = engine_snapshots
        return result

    def to_debug_package(self) -> Dict[str, Any]:
        """Package for /debug-dnos handoff with full command outputs."""
        pkg = self.to_dict()
        pkg["full_captures"] = [c.to_full_dict() for c in self._all_captures]
        return pkg

    # -- File persistence ------------------------------------------------

    def set_intermediate_dir(self, run_dir: Path) -> None:
        self._intermediate_dir = run_dir
        run_dir.mkdir(parents=True, exist_ok=True)

    def _write_intermediate_phase(self, phase: PhaseSummary) -> None:
        if not self._intermediate_dir:
            return
        phase_file = self._intermediate_dir / f"phase_{phase.phase_name}.json"
        phase_file.write_text(json.dumps(phase.to_dict(), indent=2))

        full_captures_file = self._intermediate_dir / f"phase_{phase.phase_name}_full.json"
        full_data = []
        for c in phase.commands:
            full_data.append(c.to_full_dict())
        full_captures_file.write_text(json.dumps(full_data, indent=2))

    def write_all(self, run_dir: Path) -> Path:
        run_dir.mkdir(parents=True, exist_ok=True)

        (run_dir / "observability.json").write_text(
            json.dumps(self.to_dict(), indent=2)
        )

        timeline_lines = []
        for evt in self._timeline:
            prefix = evt.event_type.upper().ljust(12)
            timeline_lines.append(f"{evt.timestamp}  {prefix}  {evt.message}")
        (run_dir / "timeline.log").write_text("\n".join(timeline_lines))

        if self._diffs:
            (run_dir / "diffs.json").write_text(
                json.dumps([d.to_dict() for d in self._diffs], indent=2)
            )

        if self._traffic_snapshots:
            (run_dir / "traffic_stats.json").write_text(
                json.dumps([t.to_dict() for t in self._traffic_snapshots], indent=2)
            )

        debug_dir = run_dir / "debug_package"
        debug_dir.mkdir(exist_ok=True)
        (debug_dir / "full_evidence.json").write_text(
            json.dumps(self.to_debug_package(), indent=2)
        )

        return run_dir

    # -- Convenience: wrap an existing run_show with recording -----------

    def wrapping_run_show(
        self,
        run_show: Callable[[str, str], str],
    ) -> Callable[[str, str], str]:
        """
        Returns a new run_show function that transparently records every call.

        Usage:
            obs = ObservabilityCollector(...)
            recorded_run_show = obs.wrapping_run_show(original_run_show)
            # Now pass recorded_run_show to any function that expects run_show
        """

        def _wrapper(device: str, command: str) -> str:
            return self.run_and_record(device, command, run_show)

        return _wrapper


def _parse_iso_epoch(iso_str: str) -> float:
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.timestamp()
    except (ValueError, AttributeError):
        return time.time()
