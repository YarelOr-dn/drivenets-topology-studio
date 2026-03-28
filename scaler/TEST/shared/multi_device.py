#!/usr/bin/env python3
"""
Cross-device command execution and output correlation engine.

Runs the same (or different) commands across multiple devices and
cross-references their outputs using correlation rules from the recipe.

Recipe JSON format:
    "multi_device": {
        "devices": ["PE-1", "PE-2", "RR-1"],
        "correlation_commands": [
            {
                "label": "bgp_evpn_peers",
                "command": "show bgp l2vpn evpn summary | no-more",
                "correlation": "peer_count_match",
                "description": "All devices should see the same number of EVPN peers"
            }
        ],
        "per_device_commands": {
            "PE-1": ["show evpn mac-table instance EVPN1 | no-more"],
            "PE-2": ["show evpn mac-table instance EVPN1 | no-more"]
        }
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


@dataclass
class DeviceOutput:
    """Output from one command on one device."""
    device: str
    command: str
    output: str
    timestamp: str = ""
    error: Optional[str] = None


@dataclass
class CorrelationResult:
    """Result of correlating outputs across devices."""
    label: str
    rule: str
    passed: bool
    detail: str
    device_outputs: Dict[str, str] = field(default_factory=dict)
    device_values: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiDeviceResult:
    """Full cross-device execution and correlation result."""
    devices: List[str]
    correlations: List[CorrelationResult] = field(default_factory=list)
    device_outputs: Dict[str, List[DeviceOutput]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.correlations)

    @property
    def fail_count(self) -> int:
        return sum(1 for c in self.correlations if not c.passed)

    def summary(self) -> str:
        parts = [f"Multi-device check ({len(self.devices)} devices): {'PASS' if self.passed else 'FAIL'}"]
        for c in self.correlations:
            status = "PASS" if c.passed else "FAIL"
            parts.append(f"  [{status}] {c.label}: {c.detail}")
        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "devices": self.devices,
            "passed": self.passed,
            "fail_count": self.fail_count,
            "errors": self.errors,
            "correlations": [
                {
                    "label": c.label,
                    "rule": c.rule,
                    "passed": c.passed,
                    "detail": c.detail,
                    "device_values": c.device_values,
                }
                for c in self.correlations
            ],
        }


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def run_across_devices(
    devices: List[str],
    command: str,
    run_show_map: Dict[str, RunShowFn],
) -> Dict[str, DeviceOutput]:
    """Run same command across multiple devices."""
    results: Dict[str, DeviceOutput] = {}
    for dev in devices:
        run_show = run_show_map.get(dev)
        if not run_show:
            results[dev] = DeviceOutput(dev, command, "", error="No runner for device")
            continue
        try:
            output = run_show(dev, command)
            results[dev] = DeviceOutput(dev, command, _strip_ansi(output), timestamp=_iso_now())
        except Exception as exc:
            results[dev] = DeviceOutput(dev, command, "", error=str(exc), timestamp=_iso_now())
    return results


def correlate_outputs(
    label: str,
    rule: str,
    device_outputs: Dict[str, DeviceOutput],
) -> CorrelationResult:
    """Apply a correlation rule to outputs from multiple devices."""
    values: Dict[str, Any] = {}

    for dev, do in device_outputs.items():
        if do.error:
            values[dev] = f"ERROR: {do.error}"
        else:
            values[dev] = _extract_value(do.output, rule)

    passed, detail = _evaluate_correlation(rule, values)

    return CorrelationResult(
        label=label,
        rule=rule,
        passed=passed,
        detail=detail,
        device_outputs={d: do.output[:500] for d, do in device_outputs.items()},
        device_values=values,
    )


def run_multi_device_check(
    devices: List[str],
    correlation_commands: List[Dict[str, Any]],
    run_show_map: Dict[str, RunShowFn],
    per_device_commands: Optional[Dict[str, List[str]]] = None,
) -> MultiDeviceResult:
    """Full multi-device execution + correlation pipeline."""
    result = MultiDeviceResult(devices=devices)

    for cc in correlation_commands:
        command = cc["command"]
        label = cc.get("label", command[:40])
        rule = cc.get("correlation", "all_match")

        outputs = run_across_devices(devices, command, run_show_map)

        for dev, do in outputs.items():
            if dev not in result.device_outputs:
                result.device_outputs[dev] = []
            result.device_outputs[dev].append(do)
            if do.error:
                result.errors.append(f"{dev}: {do.error}")

        corr = correlate_outputs(label, rule, outputs)
        result.correlations.append(corr)

    if per_device_commands:
        for dev, cmds in per_device_commands.items():
            run_show = run_show_map.get(dev)
            if not run_show:
                continue
            for cmd in cmds:
                try:
                    output = run_show(dev, cmd)
                    do = DeviceOutput(dev, cmd, _strip_ansi(output), timestamp=_iso_now())
                except Exception as exc:
                    do = DeviceOutput(dev, cmd, "", error=str(exc))
                if dev not in result.device_outputs:
                    result.device_outputs[dev] = []
                result.device_outputs[dev].append(do)

    return result


# ---------------------------------------------------------------------------
# Value extraction and correlation rules
# ---------------------------------------------------------------------------

def _extract_value(output: str, rule: str) -> Any:
    """Extract a comparable value from command output based on the rule type."""
    if rule in ("peer_count_match", "line_count_match"):
        lines = [l for l in output.strip().splitlines()
                 if l.strip() and not l.strip().startswith("---")]
        return len(lines)

    if rule in ("first_integer_match", "counter_match"):
        m = re.search(r"\b(\d+)\b", output)
        return int(m.group(1)) if m else None

    if rule == "all_match":
        return output.strip()

    if rule == "all_contain":
        return output.strip()

    return output.strip()[:200]


def _evaluate_correlation(rule: str, values: Dict[str, Any]) -> tuple:
    """Evaluate a correlation rule across device values."""
    non_error = {k: v for k, v in values.items() if not isinstance(v, str) or not v.startswith("ERROR")}

    if not non_error:
        return False, "all devices returned errors"

    if rule in ("peer_count_match", "line_count_match", "first_integer_match", "counter_match"):
        unique_vals = set(non_error.values())
        if len(unique_vals) == 1:
            return True, f"all devices agree: {unique_vals.pop()}"
        return False, f"mismatch: {dict(non_error)}"

    if rule == "all_match":
        unique_vals = set(str(v)[:100] for v in non_error.values())
        if len(unique_vals) == 1:
            return True, "all outputs match"
        return False, f"outputs differ across {len(unique_vals)} unique values"

    if rule == "all_non_empty":
        empty = [k for k, v in non_error.items() if not v or (isinstance(v, str) and not v.strip())]
        if empty:
            return False, f"empty output from: {empty}"
        return True, "all devices returned non-empty output"

    return True, f"unknown rule '{rule}', defaulting PASS"
