#!/usr/bin/env python3
"""
Generate incremental DNOS config snippets for EVPN ELAN + seamless-integration.

Does NOT push config. Caller must validate via validate_config (MCP) before commit.

Rules from SW-204115:
- IRB must NOT be configured with seamless-integration (reject if irb + si together).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


def detect_irb_conflict(evpn_config_text: str) -> bool:
    """Return True if both IRB-like and seamless-integration appear (invalid combo)."""
    t = evpn_config_text.lower()
    has_si = "seamless-integration" in t or ("seamless" in t and "integration" in t)
    has_irb = bool(re.search(r"\birb\b", t)) or "integrated-routing" in t
    return has_si and has_irb


def build_minimal_si_evpn_snippet(
    evpn_instance_name: str,
    bridge_domain_name: str,
    ac_interfaces: List[str],
    note: str = "",
) -> str:
    """
    Minimal illustrative config block. Adjust to match lab naming and DNOS version.

    Flat interface style per SCALER guidelines (siblings under interfaces).
    """
    lines = [
        f"! {note}".strip(),
        f"! EVPN ELAN + seamless-integration skeleton for {evpn_instance_name}",
        "network-services",
        " evpn",
        f"  instance {evpn_instance_name}",
        "   seamless-integration",
        "   !",
        "  !",
        " !",
        " bridge-domain",
        f"  instance {bridge_domain_name}",
        "   admin-state enabled",
    ]
    for iface in ac_interfaces:
        lines.append(f"   attachment-circuit {iface}")
        lines.append("    admin-state enabled")
        lines.append("   !")
    lines.extend(
        [
            "  !",
            " !",
            "!",
            "! Validate with: validate_config(device, text) before commit",
        ]
    )
    return "\n".join(line for line in lines if line is not None)


def suggest_suppression_snippet(evpn_instance_name: str) -> str:
    """Placeholder for MAC mobility suppression tuning; confirm syntax on device."""
    return (
        f"! TBD: confirm exact CLI for MAC move suppression under instance {evpn_instance_name}\n"
        "! Use search_cli_docs('evpn mac') and ? completion on device.\n"
    )


def plan_config_delta(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Given DeviceContext from device_discovery, propose what to add (not applied).
    """
    proposals: List[Dict[str, str]] = []
    if not ctx.get("seamless_integration_configured"):
        proposals.append(
            {
                "id": "add_seamless_integration",
                "description": "Add seamless-integration under EVPN instance (no IRB).",
                "risk": "medium",
            }
        )
    if ctx.get("bgp_evpn_established", 0) == 0:
        proposals.append(
            {
                "id": "bgp_peering",
                "description": "Establish BGP L2VPN EVPN neighbors (manual / lab).",
                "risk": "high",
            }
        )
    ac_hints = ctx.get("ac_interface_hints") or []
    if len(ac_hints) < 2:
        proposals.append(
            {
                "id": "second_ac",
                "description": "Add second attachment-circuit for AC<->AC mobility tests.",
                "risk": "medium",
            }
        )
    if not ctx.get("pw_configured_hint"):
        proposals.append(
            {
                "id": "pseudowire",
                "description": "Add VPLS PW for PW-related scenarios (SW-205162/198/199).",
                "risk": "high",
            }
        )
    return {"proposals": proposals, "irb_forbidden_with_si": True}


def validate_generated_text(text: str) -> Tuple[bool, List[str]]:
    """Local sanity check before MCP validate_config."""
    errors: List[str] = []
    if detect_irb_conflict(text):
        errors.append("IRB + seamless-integration combination is not allowed (SW-204115).")
    if not text.strip():
        errors.append("Empty config snippet.")
    return (len(errors) == 0, errors)
