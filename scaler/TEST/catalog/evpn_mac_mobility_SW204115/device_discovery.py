#!/usr/bin/env python3
"""
Discover device context for EVPN MAC mobility tests (SW-204115).

Callers supply run_show(device, command) -> str (e.g. MCP run_show_command).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared.mac_parsers import (
    parse_bgp_l2vpn_evpn_summary,
    parse_evpn_instance_names,
    parse_evpn_mac_count,
    parse_system_nodes,
    strip_ansi,
)

RunShowFn = Callable[[str, str], str]


def _has_keyword(text: str, *keywords: str) -> bool:
    t = strip_ansi(text).lower()
    return all(k.lower() in t for k in keywords)


def _parse_evpn_config_structure(cfg_text: str) -> Dict[str, Any]:
    """Parse EVPN config text into structured fields instead of keyword heuristics.

    Walks the config line-by-line tracking indentation depth to distinguish
    AC interfaces directly under the instance vs under seamless-integration.
    """
    result: Dict[str, Any] = {
        "ac_count": 0,
        "ac_interfaces": [],
        "mac_handling": False,
        "loop_prevention": False,
        "mac_aging": False,
        "site_ids": [],
        "label_block_size": None,
        "source_if": None,
    }

    in_si = False
    in_mac_handling = False
    si_depth = 0

    for raw_line in strip_ansi(cfg_text).splitlines():
        line = raw_line.strip()
        indent = len(raw_line) - len(raw_line.lstrip())

        if not line or line.startswith("#"):
            continue

        if "seamless-integration" in line and "!" not in line:
            in_si = True
            si_depth = indent
            continue

        if in_si:
            if line == "!" and indent <= si_depth:
                in_si = False
                continue

            m = re.match(r"site-id\s+(\d+)", line)
            if m:
                result["site_ids"].append(int(m.group(1)))

            m = re.match(r"label-block-size\s+(\d+)", line)
            if m:
                result["label_block_size"] = int(m.group(1))

            m = re.match(r"source-if\s+(\S+)", line)
            if m:
                result["source_if"] = m.group(1)
            continue

        m = re.match(r"interface\s+((?:ge|bundle|lag)\S+)", line)
        if m and not in_si:
            result["ac_count"] += 1
            result["ac_interfaces"].append(m.group(1))

        if "mac-handling" in line:
            result["mac_handling"] = True
            in_mac_handling = True
        if in_mac_handling:
            if "loop-prevention" in line:
                result["loop_prevention"] = True
            if "mac-table-aging-time" in line:
                result["mac_aging"] = True
            if line == "!":
                in_mac_handling = False

    return result


def discover_device_context(device: str, run_show: RunShowFn) -> Dict[str, Any]:
    """
    Build DeviceContext: cluster vs standalone, NCC id, EVPN names, flags.

    Best-effort parsing; unknown fields set to None or empty list.
    """
    ctx: Dict[str, Any] = {
        "device": device,
        "device_type": "unknown",
        "active_ncc_id": "0",
        "standby_ncc_id": None,
        "evpn_instances": [],
        "evpn_name_primary": None,
        "bridge_domain_hint": None,
        "bgp_evpn_established": 0,
        "bgp_evpn_total": 0,
        "mac_table_count": 0,
        "seamless_integration_configured": False,
        "sticky_configured": False,
        "esi_present": False,
        "pw_configured_hint": False,
        "ac_interface_hints": [],
        "raw_snippets": {},
    }

    try:
        sys_out = run_show(device, "show system | no-more")
        ctx["raw_snippets"]["show_system"] = sys_out[:8000]
        parsed_sys = parse_system_nodes(sys_out)
        ctx["active_ncc_id"] = parsed_sys.get("active_ncc") or "0"
        ctx["standby_ncc_id"] = parsed_sys.get("standby_ncc")
        ctx["device_type"] = "cluster" if parsed_sys.get("is_cluster_hint") else "standalone"
    except Exception as exc:  # noqa: BLE001
        ctx["discovery_errors"] = ctx.get("discovery_errors", []) + [f"show system: {exc}"]

    # Fetch EVPN config first -- we'll use it for instance name detection + structured parsing
    evpn_cfg_text = ""
    try:
        evpn_cfg_text = run_show(device, "show config network-services evpn | no-more")
        ctx["raw_snippets"]["show_config_network_services_evpn"] = evpn_cfg_text[:12000]
    except Exception:
        pass

    try:
        evpn_sum = run_show(device, "show evpn summary | no-more")
        ctx["raw_snippets"]["show_evpn_summary"] = evpn_sum[:8000]
        names = parse_evpn_instance_names(evpn_sum)
        if not names:
            # show evpn summary is a global view with no instance names.
            # Parse instance names from config (most reliable source).
            for line in strip_ansi(evpn_cfg_text).splitlines():
                m = re.search(r"^\s*instance\s+(\S+)", line)
                if m and m.group(1) not in ("!", ""):
                    names.append(m.group(1))
        ctx["evpn_instances"] = list(dict.fromkeys(names))
        ctx["evpn_name_primary"] = ctx["evpn_instances"][0] if ctx["evpn_instances"] else None
    except Exception as exc:  # noqa: BLE001
        ctx["discovery_errors"] = ctx.get("discovery_errors", []) + [f"show evpn summary: {exc}"]

    try:
        bgp_out = run_show(device, "show bgp l2vpn evpn summary | no-more")
        ctx["raw_snippets"]["show_bgp_l2vpn_evpn_summary"] = bgp_out[:8000]
        p = parse_bgp_l2vpn_evpn_summary(bgp_out)
        ctx["bgp_evpn_established"] = p.get("established", 0)
        ctx["bgp_evpn_total"] = p.get("total", 0)
    except Exception as exc:  # noqa: BLE001
        ctx["discovery_errors"] = ctx.get("discovery_errors", []) + [f"bgp l2vpn evpn summary: {exc}"]

    evpn_name = ctx["evpn_name_primary"] or "EVPN_INSTANCE"
    try:
        mac_out = run_show(device, f"show evpn mac-table instance {evpn_name} | no-more")
        ctx["raw_snippets"]["show_evpn_mac_table"] = mac_out[:8000]
        ctx["mac_table_count"] = parse_evpn_mac_count(mac_out)
    except Exception:
        try:
            mac_out = run_show(device, "show evpn mac-table | no-more")
            ctx["mac_table_count"] = parse_evpn_mac_count(mac_out)
        except Exception as exc:  # noqa: BLE001
            ctx["discovery_errors"] = ctx.get("discovery_errors", []) + [f"evpn mac-table: {exc}"]

    try:
        cfg = evpn_cfg_text or run_show(device, "show config network-services evpn | no-more")
        if not evpn_cfg_text:
            ctx["raw_snippets"]["show_config_network_services_evpn"] = cfg[:12000]
        cfg_clean = strip_ansi(cfg).lower()
        ctx["seamless_integration_configured"] = "seamless-integration" in cfg_clean
        ctx["sticky_configured"] = "sticky-mac" in cfg_clean
        ctx["pw_configured_hint"] = "pseudowire" in cfg_clean or re.search(
            r"\bpw\b", cfg_clean,
        ) is not None
        ctx["esi_present"] = "ethernet-segment" in cfg_clean

        # Structured parsing: count AC interfaces, detect mac-handling knobs,
        # extract site-ids, detect loop prevention -- not just keyword heuristics
        parsed = _parse_evpn_config_structure(cfg)
        ctx["evpn_ac_count"] = parsed.get("ac_count", 0)
        ctx["evpn_ac_interfaces"] = parsed.get("ac_interfaces", [])
        ctx["mac_handling_configured"] = parsed.get("mac_handling", False)
        ctx["loop_prevention_configured"] = parsed.get("loop_prevention", False)
        ctx["mac_aging_configured"] = parsed.get("mac_aging", False)
        ctx["site_ids_configured"] = parsed.get("site_ids", [])
        ctx["label_block_size"] = parsed.get("label_block_size")
        ctx["source_if"] = parsed.get("source_if")
    except Exception as exc:  # noqa: BLE001
        ctx["discovery_errors"] = ctx.get("discovery_errors", []) + [f"show config evpn: {exc}"]

    # BGP address-family config (separate from EVPN instance config)
    try:
        bgp_cfg = run_show(device, "show config protocols bgp | no-more")
        ctx["raw_snippets"]["show_config_protocols_bgp"] = bgp_cfg[:12000]
        ctx["bgp_l2vpn_evpn_af_configured"] = "address-family l2vpn-evpn" in strip_ansi(bgp_cfg).lower()
        ctx["bgp_l2vpn_vpls_af_configured"] = "address-family l2vpn-vpls" in strip_ansi(bgp_cfg).lower()
    except Exception as exc:  # noqa: BLE001
        ctx["discovery_errors"] = ctx.get("discovery_errors", []) + [f"show config bgp: {exc}"]

    try:
        bd = run_show(device, "show bridge-domain instance | no-more")
        ctx["raw_snippets"]["show_bridge_domain"] = bd[:4000]
        ctx["bridge_domain_hint"] = True if strip_ansi(bd).strip() else False
    except Exception:
        ctx["bridge_domain_hint"] = None

    try:
        ifdesc = run_show(device, "show interfaces description | no-more")
        ctx["raw_snippets"]["show_interfaces_description"] = ifdesc[:4000]
        for line in strip_ansi(ifdesc).splitlines():
            if "l2" in line.lower() or "evpn" in line.lower() or "bd" in line.lower():
                parts = line.split()
                if parts:
                    ctx["ac_interface_hints"].append(parts[0])
        ctx["ac_interface_hints"] = list(dict.fromkeys(ctx["ac_interface_hints"]))[:32]
    except Exception:
        pass

    return ctx


def format_context_summary(ctx: Dict[str, Any]) -> str:
    lines = [
        f"Device: {ctx.get('device')}",
        f"Type: {ctx.get('device_type')}  active_ncc={ctx.get('active_ncc_id')}",
        f"EVPN instances: {ctx.get('evpn_instances')}",
        f"Primary EVPN: {ctx.get('evpn_name_primary')}",
        f"BGP L2VPN EVPN: {ctx.get('bgp_evpn_established')}/{ctx.get('bgp_evpn_total')} Established",
        f"MAC table count (sample): {ctx.get('mac_table_count')}",
        f"seamless-integration: {ctx.get('seamless_integration_configured')}",
        f"  site-ids: {ctx.get('site_ids_configured', [])}",
        f"  label-block-size: {ctx.get('label_block_size')}",
        f"  source-if: {ctx.get('source_if')}",
        f"AC interfaces ({ctx.get('evpn_ac_count', 0)}): {ctx.get('evpn_ac_interfaces', [])}",
        f"MAC handling: {ctx.get('mac_handling_configured', False)}",
        f"  loop-prevention: {ctx.get('loop_prevention_configured', False)}",
        f"  mac-aging: {ctx.get('mac_aging_configured', False)}",
        f"sticky-mac: {ctx.get('sticky_configured')}",
        f"ESI: {ctx.get('esi_present')}  PW: {ctx.get('pw_configured_hint')}",
        f"BGP L2VPN EVPN AF: {ctx.get('bgp_l2vpn_evpn_af_configured', 'N/A')}",
        f"BGP L2VPN VPLS AF: {ctx.get('bgp_l2vpn_vpls_af_configured', 'N/A')}",
    ]
    errs = ctx.get("discovery_errors") or []
    if errs:
        lines.append("Errors: " + "; ".join(errs))
    return "\n".join(lines)
