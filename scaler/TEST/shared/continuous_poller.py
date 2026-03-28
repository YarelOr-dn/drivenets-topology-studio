#!/usr/bin/env python3
"""
Continuous high-frequency polling engine for DNOS test automation.

During trigger windows (e.g. HA recovery, MAC move propagation), polls
counters, BGP state, MAC tables, and events at configurable intervals.
Collects a time series for post-analysis.

Recipe JSON format (inside scenario):
    "poll_config": {
        "interval_sec": 2,
        "max_duration_sec": 120,
        "convergence_check": {
            "command": "show bgp l2vpn evpn summary | no-more",
            "pattern": "Established",
            "min_stable_polls": 3
        },
        "poll_commands": [
            {"label": "bgp_state", "command": "show bgp l2vpn evpn summary | no-more"},
            {"label": "mac_count", "command": "show evpn mac summary | no-more"},
            {"label": "mac_table", "command": "show evpn mac-table instance {evpn_name} | no-more"}
        ]
    }
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

RunShowFn = Callable[[str, str], str]

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text) if isinstance(text, str) else str(text)


@dataclass
class PollSample:
    """One poll iteration across all commands."""
    iteration: int
    timestamp: str = ""
    elapsed_sec: float = 0.0
    values: Dict[str, str] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    converged: bool = False


@dataclass
class PollTimeSeries:
    """Full time series of poll samples."""
    label: str
    interval_sec: float
    max_duration_sec: float
    samples: List[PollSample] = field(default_factory=list)
    converged_at: Optional[float] = None
    convergence_iterations: int = 0
    total_duration_sec: float = 0.0

    @property
    def converged(self) -> bool:
        return self.converged_at is not None

    def last_values(self) -> Dict[str, str]:
        if self.samples:
            return self.samples[-1].values
        return {}

    def summary(self) -> str:
        parts = [f"Poll series '{self.label}': {len(self.samples)} samples over {self.total_duration_sec:.1f}s"]
        if self.converged:
            parts.append(f"  Converged at {self.converged_at:.1f}s (iteration {self.convergence_iterations})")
        else:
            parts.append(f"  NOT converged after {self.total_duration_sec:.1f}s")
        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "interval_sec": self.interval_sec,
            "max_duration_sec": self.max_duration_sec,
            "total_duration_sec": round(self.total_duration_sec, 2),
            "sample_count": len(self.samples),
            "converged": self.converged,
            "converged_at_sec": round(self.converged_at, 2) if self.converged_at else None,
            "convergence_iterations": self.convergence_iterations,
            "samples": [
                {
                    "iteration": s.iteration,
                    "timestamp": s.timestamp,
                    "elapsed_sec": round(s.elapsed_sec, 2),
                    "converged": s.converged,
                    "values": {k: v[:200] for k, v in s.values.items()},
                    "errors": s.errors,
                }
                for s in self.samples
            ],
        }


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def poll_until_converged(
    device: str,
    label: str,
    run_show: RunShowFn,
    poll_commands: List[Dict[str, str]],
    interval_sec: float = 2.0,
    max_duration_sec: float = 120.0,
    convergence_command: Optional[str] = None,
    convergence_pattern: Optional[str] = None,
    min_stable_polls: int = 3,
    template_vars: Optional[Dict[str, str]] = None,
) -> PollTimeSeries:
    """Poll commands at regular intervals until convergence or timeout.

    Convergence is detected when the convergence_command output matches
    convergence_pattern for min_stable_polls consecutive iterations.
    """
    series = PollTimeSeries(
        label=label,
        interval_sec=interval_sec,
        max_duration_sec=max_duration_sec,
    )

    subs = template_vars or {}
    stable_count = 0
    t_start = time.monotonic()
    iteration = 0

    while True:
        elapsed = time.monotonic() - t_start
        if elapsed >= max_duration_sec:
            break

        iteration += 1
        sample = PollSample(
            iteration=iteration,
            timestamp=_iso_now(),
            elapsed_sec=elapsed,
        )

        for pc in poll_commands:
            cmd_label = pc.get("label", pc["command"][:30])
            cmd = pc["command"]
            for k, v in subs.items():
                cmd = cmd.replace(f"{{{k}}}", v)

            try:
                output = run_show(device, cmd)
                sample.values[cmd_label] = _strip_ansi(output)
            except Exception as exc:
                sample.errors[cmd_label] = str(exc)

        # Convergence check
        if convergence_command and convergence_pattern:
            conv_cmd = convergence_command
            for k, v in subs.items():
                conv_cmd = conv_cmd.replace(f"{{{k}}}", v)

            try:
                conv_output = _strip_ansi(
                    sample.values.get("convergence") or run_show(device, conv_cmd)
                )
                if re.search(convergence_pattern, conv_output, re.IGNORECASE):
                    stable_count += 1
                else:
                    stable_count = 0
            except Exception:
                stable_count = 0

            if stable_count >= min_stable_polls:
                sample.converged = True
                series.converged_at = elapsed
                series.convergence_iterations = iteration
                series.samples.append(sample)
                break
        else:
            # No convergence check -- just collect
            pass

        series.samples.append(sample)

        # Sleep for the remaining interval
        poll_duration = time.monotonic() - t_start - elapsed
        sleep_time = max(0, interval_sec - poll_duration)
        if sleep_time > 0 and (time.monotonic() - t_start + sleep_time) < max_duration_sec:
            time.sleep(sleep_time)

    series.total_duration_sec = time.monotonic() - t_start
    return series


def load_poll_config(recipe: Dict[str, Any], scenario: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Load poll configuration from recipe or scenario."""
    src = scenario or recipe
    return src.get("poll_config", {
        "interval_sec": 5,
        "max_duration_sec": 120,
        "convergence_check": None,
        "poll_commands": [],
    })
