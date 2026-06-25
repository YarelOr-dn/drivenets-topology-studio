#!/usr/bin/env python3
"""
Validators for the EVPN MAC mobility SW-204115 test suite.

Canonical implementations of generic primitives (poll_until, BGP/ARP/interface
waits, action_then_validate) live in `scaler.validators`. This module:

  1. Re-exports those generic primitives so existing imports
     `from .validators import poll_until` keep working.
  2. Adds suite-specific extensions whose dependencies are local to this
     test catalog (e.g. `wait_for_mac_in_table` uses `.mac_parsers`).

Single source of truth: any change to `poll_until`, `wait_for_bgp_state*`,
`wait_for_arp_resolve`, etc. should be made in `scaler/scaler/validators.py`
so it propagates to /TEST AND /SPIRENT in one place.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, Optional, Tuple

from scaler.validators import (
    ValidationResult,
    ConditionFn,
    RunShowFn,
    poll_until,
    wait_for_bgp_state,
    wait_for_bgp_state_in,
    wait_for_arp_resolve,
    wait_for_interface_up,
    wait_for_mac_absent,
    wait_for_evi_label_pool,
    wait_for_route_in_rib,
    wait_for_pw_installed,
    action_then_validate,
)


def _canonical_mac(mac: str) -> str:
    """Strip every separator, lowercase. Yields a 12-hex-char canonical key.

    Handles: 'aa:bb:cc:dd:ee:ff', 'aa-bb-cc-dd-ee-ff', 'aabb.ccdd.eeff',
    'AABBCC-DDEEFF', 'AABBCCDDEEFF'. Returns "" for malformed input.
    """
    if not mac:
        return ""
    cleaned = re.sub(r"[^0-9a-fA-F]", "", mac).lower()
    return cleaned if len(cleaned) == 12 else cleaned


def _mac_in_text(needle_canonical: str, haystack: str) -> bool:
    """Substring search across MAC formats DNOS may emit.

    Compares the canonical (no-separator) form against the canonical form of
    the haystack, so 'aabbccddeeff' matches 'AA:BB:CC:DD:EE:FF',
    'aa-bb-cc-dd-ee-ff' and 'aabb.ccdd.eeff' alike.
    """
    if not needle_canonical or not haystack:
        return False
    haystack_canonical = re.sub(r"[^0-9a-fA-F]", "", haystack).lower()
    return needle_canonical in haystack_canonical


def wait_for_mac_in_table(
    run_show: RunShowFn,
    device: str,
    instance: str,
    mac: str,
    timeout_sec: float = 10.0,
    interval_sec: float = 1.0,
    on_progress: Optional[Callable[[float, Any], None]] = None,
    require_source: Optional[str] = None,
) -> ValidationResult:
    """Poll EVPN MAC table for `mac` in `instance`. PASS when present.

    Suite-specific: depends on `mac_parsers.parse_evpn_mac_entries` to extract
    the MAC's source flag (local-AC / remote-EVPN / PW). Lives in this catalog
    rather than in `scaler.validators` because the MAC parsers are tied to the
    EVPN MAC mobility test catalog.

    Args:
        require_source: If provided, also requires the parsed `source_hint`
            field of the MAC entry to equal this string (e.g. "remote-evpn",
            "ac", "pw"). Used by mobility tests that want to verify the MAC
            moved to the EXPECTED source, not just appears anywhere.
            When None, presence in the table is sufficient.

    `last_value` is a dict with: mac, instance, present, source_hint, raw.
    """
    from .mac_parsers import parse_evpn_mac_entries

    mac_canonical = _canonical_mac(mac)
    mac_colon = ":".join(mac_canonical[i:i+2] for i in range(0, 12, 2)) if len(mac_canonical) == 12 else mac.lower()
    cmd = f"show evpn mac-table instance {instance} mac {mac} | no-more"

    def _check() -> Tuple[bool, Any]:
        out = run_show(device, cmd)
        observed: Dict[str, Any] = {
            "mac": mac_colon, "mac_canonical": mac_canonical,
            "instance": instance,
            "present": False, "source_hint": "",
            "raw": out[:500],
        }
        try:
            entries = parse_evpn_mac_entries(out)
        except Exception:
            entries = []
        for e in entries:
            entry_canonical = _canonical_mac(e.get("mac", ""))
            if entry_canonical and entry_canonical == mac_canonical:
                observed["present"] = True
                observed["source_hint"] = e.get("source_hint", "")
                if require_source is None:
                    return True, observed
                if e.get("source_hint") == require_source:
                    return True, observed
        # Fallback: separator-agnostic substring scan over the raw show output.
        # Catches formats the parser does not yet recognise (Cisco-dash,
        # Juniper-dot, no-separator) without false positives.
        if require_source is None and _mac_in_text(mac_canonical, out):
            observed["present"] = True
            return True, observed
        return False, observed

    return poll_until(_check, timeout_sec=timeout_sec,
                      interval_sec=interval_sec, on_progress=on_progress)


__all__ = [
    "ValidationResult",
    "ConditionFn",
    "RunShowFn",
    "poll_until",
    "wait_for_bgp_state",
    "wait_for_bgp_state_in",
    "wait_for_arp_resolve",
    "wait_for_interface_up",
    "wait_for_mac_in_table",
    "wait_for_mac_absent",
    "wait_for_evi_label_pool",
    "wait_for_route_in_rib",
    "wait_for_pw_installed",
    "action_then_validate",
    "_canonical_mac",
    "_mac_in_text",
]
