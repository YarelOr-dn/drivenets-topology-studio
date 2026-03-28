#!/usr/bin/env python3
"""
Cross-layer mismatch detection for EVPN MAC mobility tests (SW-204115).

After every trigger, collects outputs from 6 independent layers and
cross-references them to find inconsistencies that single-layer checks miss:

  Layer 1  mac-table          : MAC, source (local/bgp/pw), interface, sequence
  Layer 2  mac-table detail   : flags (L/R/K/F/D), sequence, ESI, next-hop
  Layer 3  forwarding-table   : NCP forwarding state, NCP flags, NCP interface
  Layer 4  FIB database       : fib_state (programmed/pending/error), interface
  Layer 5  ARP table          : IP-MAC binding, interface
  Layer 6  ghost MACs         : stale MACs that should have been cleaned up

Cross-reference rules (a mismatch on ANY = FAIL):
  - Interface agreement: layers 1-4 must report the same interface for a MAC
  - Source agreement:    mac-table source vs detail source vs FIB source
  - Sequence agreement:  mac-table seq vs detail seq
  - Forwarding sanity:   if mac-table shows local, NCP must be forwarding
  - ARP consistency:     if ARP has a binding for the MAC, interface must match
  - Ghost clean:         MAC must NOT appear in ghost table

XRAY integration:
  When mismatches are detected, optionally triggers a /XRAY CP capture to
  get packet-level evidence of the inconsistency.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .mac_parsers import (
    ArpTableEntry,
    FibMacEntry,
    FwdTableEntry,
    MacDetailEntry,
    parse_arp_table,
    parse_evpn_mac_entries,
    parse_fib_evpn_mac,
    parse_forwarding_table_flags,
    parse_ghost_macs,
    parse_mac_detail,
    strip_ansi,
)

RunShowFn = Callable[[str, str], str]

XRAY_SCRIPT_CANDIDATES = [
    Path.home() / "live_capture.py",
    Path.home() / "xray" / "live_capture.py",
    Path.home() / "CURSOR" / "live_capture.py",
    Path.home() / "drivenets-topology-studio" / "topology" / "live_capture.py",
]

BPF_FILTERS = {
    "cp": "ether proto 0x88cc or port 179",
    "evpn_dp": "udp port 4789 or port 179",
    "evpn_full": "ether proto 0x88cc or port 179 or udp port 4789",
}


def _find_xray_script() -> Optional[Path]:
    """Search known locations for the XRAY live_capture.py script."""
    for p in XRAY_SCRIPT_CANDIDATES:
        if p.exists():
            return p
    return None


# Show commands indexed by layer name, with {evpn_name} and {test_mac} placeholders
SHOW_COMMAND_MATRIX: Dict[str, str] = {
    "mac_table": "show evpn mac-table instance {evpn_name} mac {test_mac} | no-more",
    "mac_detail": "show evpn mac-table detail instance {evpn_name} | no-more",
    "forwarding_table": "show evpn forwarding-table mac-address-table instance {evpn_name} | no-more",
    "fib_database": "show dnos-internal routing fib-manager database evpn local-mac service-instance {evpn_name} | no-more",
    "arp_table": "show evpn arp-table instance {evpn_name} | no-more",
    "ghost_macs": "show dnos-internal routing evpn instance {evpn_name} mac-table-ghost | no-more",
}

# Trigger-type -> which layers are mandatory and which are optional
TRIGGER_LAYER_RELEVANCE: Dict[str, Dict[str, str]] = {
    "local_to_local": {
        "mac_table": "required", "mac_detail": "required",
        "forwarding_table": "required", "fib_database": "required",
        "arp_table": "optional", "ghost_macs": "required",
    },
    "rapid_flap": {
        "mac_table": "required", "mac_detail": "required",
        "forwarding_table": "required", "fib_database": "required",
        "arp_table": "optional", "ghost_macs": "required",
    },
    "spirent_ac_to_evpn": {
        "mac_table": "required", "mac_detail": "required",
        "forwarding_table": "required", "fib_database": "required",
        "arp_table": "required", "ghost_macs": "required",
    },
    "spirent_evpn_to_ac": {
        "mac_table": "required", "mac_detail": "required",
        "forwarding_table": "required", "fib_database": "required",
        "arp_table": "required", "ghost_macs": "required",
    },
    "spirent_ac_to_pw": {
        "mac_table": "required", "mac_detail": "required",
        "forwarding_table": "required", "fib_database": "optional",
        "arp_table": "required", "ghost_macs": "required",
    },
    "spirent_pw_to_pw": {
        "mac_table": "required", "mac_detail": "required",
        "forwarding_table": "required", "fib_database": "optional",
        "arp_table": "required", "ghost_macs": "required",
    },
    "ha_cli_command": {
        "mac_table": "required", "mac_detail": "required",
        "forwarding_table": "required", "fib_database": "required",
        "arp_table": "optional", "ghost_macs": "required",
    },
    "spirent_parallel_flap_ha": {
        "mac_table": "required", "mac_detail": "required",
        "forwarding_table": "required", "fib_database": "required",
        "arp_table": "optional", "ghost_macs": "required",
    },
    "default": {
        "mac_table": "required", "mac_detail": "required",
        "forwarding_table": "required", "fib_database": "required",
        "arp_table": "optional", "ghost_macs": "required",
    },
}


@dataclass
class MismatchItem:
    """One cross-layer mismatch."""
    rule: str
    severity: str  # "FAIL", "WARN"
    layers_involved: List[str]
    detail: str
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CrossLayerResult:
    """Full cross-layer check result."""
    mac: str
    layers_collected: List[str]
    layers_skipped: List[str]
    mismatches: List[MismatchItem] = field(default_factory=list)
    layer_outputs: Dict[str, str] = field(default_factory=dict)
    xray_triggered: bool = False
    xray_output: str = ""

    @property
    def passed(self) -> bool:
        return not any(m.severity == "FAIL" for m in self.mismatches)

    @property
    def fail_count(self) -> int:
        return sum(1 for m in self.mismatches if m.severity == "FAIL")

    @property
    def warn_count(self) -> int:
        return sum(1 for m in self.mismatches if m.severity == "WARN")

    def summary(self) -> str:
        if not self.mismatches:
            return f"Cross-layer check PASS: {len(self.layers_collected)} layers consistent for {self.mac}"
        parts = []
        for m in self.mismatches:
            parts.append(f"[{m.severity}] {m.rule}: {m.detail}")
        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mac": self.mac,
            "passed": self.passed,
            "fail_count": self.fail_count,
            "warn_count": self.warn_count,
            "layers_collected": self.layers_collected,
            "layers_skipped": self.layers_skipped,
            "mismatches": [
                {"rule": m.rule, "severity": m.severity, "detail": m.detail,
                 "layers": m.layers_involved, "evidence": m.evidence}
                for m in self.mismatches
            ],
            "xray_triggered": self.xray_triggered,
        }


def _normalize_interface(iface: Optional[str]) -> Optional[str]:
    """Normalize interface names for comparison (strip trailing whitespace, lowercase)."""
    if not iface:
        return None
    return iface.strip().lower()


def collect_all_layers(
    device: str,
    evpn_name: str,
    test_mac: str,
    run_show: RunShowFn,
    trigger_type: str = "default",
) -> CrossLayerResult:
    """Collect show command outputs from all relevant layers for one MAC.

    Returns CrossLayerResult with raw outputs and parsed data for comparison.
    """
    relevance = TRIGGER_LAYER_RELEVANCE.get(trigger_type,
                                            TRIGGER_LAYER_RELEVANCE["default"])
    result = CrossLayerResult(
        mac=test_mac.lower(),
        layers_collected=[],
        layers_skipped=[],
    )

    subs = {"evpn_name": evpn_name, "test_mac": test_mac}

    for layer_name, cmd_template in SHOW_COMMAND_MATRIX.items():
        req = relevance.get(layer_name, "optional")
        cmd = cmd_template.format(**subs)
        try:
            output = run_show(device, cmd)
            result.layer_outputs[layer_name] = output
            result.layers_collected.append(layer_name)
        except Exception as exc:
            if req == "required":
                result.mismatches.append(MismatchItem(
                    rule="layer_collection",
                    severity="FAIL",
                    layers_involved=[layer_name],
                    detail=f"Failed to collect {layer_name}: {exc}",
                ))
            result.layers_skipped.append(layer_name)

    return result


def compare_layers(result: CrossLayerResult) -> CrossLayerResult:
    """Run all cross-reference rules on collected layer outputs.

    Populates result.mismatches with any inconsistencies found.
    """
    mac = result.mac
    outputs = result.layer_outputs

    # Parse each layer
    mac_entries = parse_evpn_mac_entries(outputs.get("mac_table", ""))
    detail_entries = parse_mac_detail(outputs.get("mac_detail", ""))
    fwd_entries = parse_forwarding_table_flags(outputs.get("forwarding_table", ""))
    fib_entries = parse_fib_evpn_mac(outputs.get("fib_database", ""))
    arp_entries = parse_arp_table(outputs.get("arp_table", ""))
    ghost_list = parse_ghost_macs(outputs.get("ghost_macs", ""))

    # Find our MAC in each layer
    mac_entry = next((e for e in mac_entries if e["mac"] == mac), None)
    detail_entry = next((e for e in detail_entries if e.mac == mac), None)
    fwd_entry = next((e for e in fwd_entries if e.mac == mac), None)
    fib_entry = next((e for e in fib_entries if e.mac == mac), None)
    arp_entry = next((e for e in arp_entries if e.mac == mac), None)

    # RULE 1: MAC must exist in mac-table
    if not mac_entry:
        result.mismatches.append(MismatchItem(
            rule="mac_existence",
            severity="FAIL",
            layers_involved=["mac_table"],
            detail=f"MAC {mac} not found in mac-table",
        ))
        return result  # can't cross-reference without base entry

    # RULE 2: Interface agreement (mac_table vs forwarding_table vs FIB)
    # Remote/BGP-learned MACs use MPLS labels, not physical interfaces, so
    # mac_detail shows "label:..." while forwarding_table shows the MPLS tunnel
    # egress interface. These are at different abstraction layers and will never
    # match -- skip for remote MACs to avoid false positives.
    is_remote_mac = (
        mac_entry.get("source_hint", "unknown") in ("bgp", "pw")
        or (detail_entry and detail_entry.source in ("bgp", "pw"))
        or (detail_entry and detail_entry.interface and "label" in detail_entry.interface.lower())
    )
    interfaces: Dict[str, Optional[str]] = {}
    if detail_entry and detail_entry.interface:
        interfaces["mac_detail"] = _normalize_interface(detail_entry.interface)
    if fwd_entry and fwd_entry.interface:
        interfaces["forwarding_table"] = _normalize_interface(fwd_entry.interface)
    if fib_entry and fib_entry.interface:
        interfaces["fib_database"] = _normalize_interface(fib_entry.interface)

    unique_ifaces = set(v for v in interfaces.values() if v)
    if len(unique_ifaces) > 1 and not is_remote_mac:
        result.mismatches.append(MismatchItem(
            rule="interface_agreement",
            severity="FAIL",
            layers_involved=list(interfaces.keys()),
            detail=f"Interface mismatch across layers: {dict(interfaces)}",
            evidence=interfaces,
        ))

    # RULE 3: Source agreement (mac_table source vs detail source)
    if detail_entry:
        mac_source = mac_entry.get("source_hint", "unknown")
        detail_source = detail_entry.source
        if mac_source != "unknown" and detail_source != "unknown" and mac_source != detail_source:
            result.mismatches.append(MismatchItem(
                rule="source_agreement",
                severity="FAIL",
                layers_involved=["mac_table", "mac_detail"],
                detail=f"Source mismatch: mac_table={mac_source}, detail={detail_source}",
                evidence={"mac_table": mac_source, "detail": detail_source},
            ))

    # RULE 4: Sequence agreement (mac_table seq vs detail seq)
    if detail_entry and detail_entry.sequence is not None:
        from .mac_verifiers import extract_sequence_number
        mac_seq = extract_sequence_number(mac_entry.get("line", ""))
        if mac_seq is not None and mac_seq != detail_entry.sequence:
            result.mismatches.append(MismatchItem(
                rule="sequence_agreement",
                severity="WARN",
                layers_involved=["mac_table", "mac_detail"],
                detail=f"Sequence mismatch: mac_table={mac_seq}, detail={detail_entry.sequence}",
                evidence={"mac_table": mac_seq, "detail": detail_entry.sequence},
            ))

    # RULE 5: Forwarding sanity -- local MAC must be in forwarding state
    if mac_entry.get("source_hint") == "local" and fwd_entry:
        if fwd_entry.fwd_state not in ("forwarding", "unknown"):
            result.mismatches.append(MismatchItem(
                rule="forwarding_sanity",
                severity="FAIL",
                layers_involved=["mac_table", "forwarding_table"],
                detail=f"Local MAC in {fwd_entry.fwd_state} state (expected forwarding)",
                evidence={"source": "local", "fwd_state": fwd_entry.fwd_state},
            ))

    # RULE 6: FIB programming -- must be programmed/installed
    if fib_entry:
        if fib_entry.fib_state not in ("programmed", "installed", "unknown"):
            result.mismatches.append(MismatchItem(
                rule="fib_programming",
                severity="FAIL",
                layers_involved=["fib_database"],
                detail=f"FIB state '{fib_entry.fib_state}' (expected programmed/installed)",
                evidence={"fib_state": fib_entry.fib_state},
            ))

    # RULE 7: ARP consistency -- if ARP binding exists, interface must match mac-table
    if arp_entry:
        arp_iface = _normalize_interface(arp_entry.interface)
        mac_detail_iface = _normalize_interface(
            detail_entry.interface if detail_entry else None
        )
        if arp_iface and mac_detail_iface and arp_iface != mac_detail_iface:
            result.mismatches.append(MismatchItem(
                rule="arp_interface_match",
                severity="WARN",
                layers_involved=["arp_table", "mac_detail"],
                detail=f"ARP interface={arp_iface} vs MAC interface={mac_detail_iface}",
                evidence={"arp": arp_iface, "mac_detail": mac_detail_iface},
            ))

    # RULE 8: Ghost MAC detection -- MAC must NOT be a ghost
    if mac in ghost_list:
        result.mismatches.append(MismatchItem(
            rule="no_ghost",
            severity="FAIL",
            layers_involved=["ghost_macs"],
            detail=f"MAC {mac} found in ghost MAC table -- stale entry",
        ))

    # RULE 9: FIB vs NCP forwarding agreement
    if fib_entry and fwd_entry:
        fib_iface = _normalize_interface(fib_entry.interface)
        fwd_iface = _normalize_interface(fwd_entry.interface)
        if fib_iface and fwd_iface and fib_iface != fwd_iface:
            result.mismatches.append(MismatchItem(
                rule="fib_ncp_interface",
                severity="FAIL",
                layers_involved=["fib_database", "forwarding_table"],
                detail=f"FIB interface={fib_iface} vs NCP forwarding interface={fwd_iface}",
                evidence={"fib": fib_iface, "ncp": fwd_iface},
            ))

    return result


def trigger_xray_on_mismatch(
    device: str,
    result: CrossLayerResult,
    duration_sec: int = 5,
    capture_mode: str = "evpn_full",
) -> CrossLayerResult:
    """If mismatches found with FAIL severity, trigger a /XRAY capture.

    Captures EVPN/BGP traffic on the device for correlation with the
    detected mismatch.  Searches multiple known locations for the XRAY
    script and uses an EVPN-aware BPF filter (BGP + LLDP + VXLAN).

    Args:
        capture_mode: One of "cp" (BGP+LLDP only), "evpn_dp" (VXLAN+BGP),
                       or "evpn_full" (BGP+LLDP+VXLAN).  Default: evpn_full.
    """
    if result.passed:
        return result

    fail_mismatches = [m for m in result.mismatches if m.severity == "FAIL"]
    if not fail_mismatches:
        return result

    rules_hit = ", ".join(m.rule for m in fail_mismatches)

    xray_script = _find_xray_script()
    if not xray_script:
        searched = ", ".join(str(p) for p in XRAY_SCRIPT_CANDIDATES)
        result.xray_output = (
            f"XRAY script not found in any known location: {searched}; "
            f"skipping capture for rules: {rules_hit}"
        )
        return result

    bpf_filter = BPF_FILTERS.get(capture_mode, BPF_FILTERS["evpn_full"])

    try:
        cmd = [
            "python3", str(xray_script),
            "-m", "cp",
            "-d", device,
            "-t", str(duration_sec),
            "-f", bpf_filter,
            "-o", "screen",
            "-y",
        ]
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=duration_sec + 30,
        )
        result.xray_triggered = True
        result.xray_output = (proc.stdout or "")[:2000]
        if proc.returncode != 0 and proc.stderr:
            result.xray_output += f"\n[XRAY stderr]: {proc.stderr[:500]}"
    except Exception as exc:
        result.xray_output = f"XRAY capture failed ({rules_hit}): {exc}"

    return result


def run_cross_layer_check(
    device: str,
    evpn_name: str,
    test_mac: str,
    run_show: RunShowFn,
    trigger_type: str = "default",
    enable_xray: bool = False,
    xray_duration_sec: int = 5,
) -> CrossLayerResult:
    """Full cross-layer check pipeline: collect -> compare -> optionally XRAY.

    This is the single entry point for the orchestrator.
    """
    result = collect_all_layers(device, evpn_name, test_mac, run_show, trigger_type)
    result = compare_layers(result)

    if enable_xray and not result.passed:
        result = trigger_xray_on_mismatch(device, result, xray_duration_sec)

    return result


# ---------------------------------------------------------------------------
# Proactive XRAY: Background CP capture DURING triggers (not just on failure)
# ---------------------------------------------------------------------------

class ProactiveXray:
    """Start/stop background XRAY capture around trigger windows.

    Usage:
        xray = ProactiveXray(device, duration_sec=10)
        xray.start()
        # ... execute trigger ...
        output = xray.stop()
    """

    def __init__(
        self,
        device: str,
        duration_sec: int = 10,
        capture_mode: str = "evpn_full",
    ):
        self.device = device
        self.duration_sec = duration_sec
        self.capture_mode = capture_mode
        self._process: Optional[subprocess.Popen] = None
        self._output: str = ""

    def start(self) -> bool:
        """Start background XRAY capture. Returns True if started successfully."""
        xray_script = _find_xray_script()
        if not xray_script:
            self._output = "XRAY script not found"
            return False

        bpf_filter = BPF_FILTERS.get(self.capture_mode, BPF_FILTERS["evpn_full"])

        try:
            cmd = [
                "python3", str(xray_script),
                "-m", "cp",
                "-d", self.device,
                "-t", str(self.duration_sec),
                "-f", bpf_filter,
                "-o", "screen",
                "-y",
            ]
            self._process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            return True
        except Exception as exc:
            self._output = f"Failed to start XRAY: {exc}"
            return False

    def stop(self) -> str:
        """Stop capture and return output."""
        if not self._process:
            return self._output

        try:
            stdout, stderr = self._process.communicate(timeout=self.duration_sec + 15)
            self._output = (stdout or "")[:3000]
            if self._process.returncode != 0 and stderr:
                self._output += f"\n[stderr]: {stderr[:500]}"
        except subprocess.TimeoutExpired:
            self._process.kill()
            stdout, _ = self._process.communicate()
            self._output = f"[TIMEOUT] {(stdout or '')[:2000]}"
        except Exception as exc:
            self._output = f"[ERROR] {exc}"

        self._process = None
        return self._output

    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None
