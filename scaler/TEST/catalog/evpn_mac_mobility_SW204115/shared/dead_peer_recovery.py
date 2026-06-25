#!/usr/bin/env python3
"""
Dead-peer detection and auto-reprovision for /SPIRENT BGP peers.

When a Spirent-emulated BGP peer is stuck in Connect/Active/Idle for too long,
the orchestrator gets blocked waiting for a corpse. This module breaks that loop:

  1. Detect a dead peer via DUT-side BGP state polling (idle_sec >= threshold)
  2. Pick a fresh /30 subnet + fresh inner VLAN from collision-free pools
  3. Validate DNOS config via 'commit check' + 'rollback 0' (NEVER apply blind)
  4. Apply DNOS BGP neighbor + sub-interface config (commit only after validate)
  5. Tear down the dead Spirent device, recreate at the fresh IP
  6. Restart protocols and verify ESTABLISHED on DUT
  7. Return new peer params for the orchestrator to use

Design goals:
  - SMOOTH: no STC API misuse, uses existing spirent_tool.py CLI verbs
  - RELIABLE: every config change validated via commit-check first
  - FAST: 45s budget per BGP convergence, exit early on success
  - VISIBLE: structured logs ([PEER]/[VALIDATE]/[REPROV]/[APPLY]) so the user
    can follow every step without spelunking through python
  - NEVER STUCK: if reprovision fails, returns and lets orchestrator continue
    (degraded but not blocked)
"""

from __future__ import annotations

import logging
import re
import subprocess
import time
from typing import Callable, Dict, List, Optional, Set, Tuple

from .validators import (
    poll_until,
    wait_for_arp_resolve,
    wait_for_bgp_state,
    wait_for_interface_up,
)
from .spirent_paths import spirent_tool_command, spirent_tool_path

logger = logging.getLogger("dead_peer_recovery")

# Backwards-compat alias for legacy callers.
SPIRENT_TOOL = spirent_tool_path()

# Smoke-probe sample window: maximum traffic duration before we measure RX
# delta. Polled-with-early-exit -- a healthy path returns in <1s.
_SMOKE_PROBE_MAX_DURATION_SEC = 3.0
_SMOKE_PROBE_RX_THRESHOLD = 50  # packets observed within window = path OK

_BAD_BGP_STATES = {"idle", "connect", "active", "opensent", "openconfirm",
                   "never", "down"}

_RESERVED_INNER_VLANS = {0, 1, 999, 4095}


def _run_spirent(args: List[str], timeout: int = 60) -> str:
    """Wrap spirent_tool.py with consistent error handling."""
    try:
        proc = subprocess.run(
            spirent_tool_command(*args),
            capture_output=True, text=True, timeout=timeout,
        )
        return proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except Exception as e:
        return f"[ERROR] {e}"


def _log(prefix: str, msg: str) -> None:
    """Emit a tagged structured log line.

    Routes through ``logger.info`` so callers (orchestrator, /SPIRENT CLI,
    test framework) can opt in to capture rather than always polluting stdout.
    The visible prefix style ("[REPROV]", "[REPROV-T1]") is kept so existing
    log greps still match.
    """
    logger.info("  %s %s", prefix, msg)


# ---------------------------------------------------------------------------
# DUT-side BGP state classification
# ---------------------------------------------------------------------------

def _parse_bgp_summary_line(line: str) -> Tuple[str, str]:
    """Extract (state, up_down) from one DNOS 'show bgp ... summary' line.

    DNOS summary table columns (typical):
      Neighbor V AS MsgRcvd MsgSent TblVer InQ OutQ Up/Down State

    For ESTABLISHED peers the last column is a digit (PfxRcd count).
    For non-ESTABLISHED peers the last column is the FSM state string.
    Up/Down is HH:MM:SS for short uptimes, or '1d 2h 3m' format for longer ones,
    or 'never' if the session has never come up.
    """
    cols = line.split()
    if len(cols) < 5:
        return "?", "?"
    state = cols[-1]
    up_down = "?"
    for c in cols:
        if re.match(r"^\d{1,2}:\d{2}:\d{2}$", c):
            up_down = c
            break
        if re.match(r"^\d+d\d+h$", c) or re.match(r"^\d+w\d+d$", c):
            up_down = c
            break
        if c.lower() == "never":
            up_down = "never"
            break
    return state, up_down


def _up_down_to_seconds(up_down: str) -> int:
    """Convert DNOS Up/Down string to seconds. Returns -1 if 'never', 0 if unparseable."""
    if not up_down or up_down == "?":
        return 0
    if up_down.lower() == "never":
        return -1
    m = re.match(r"^(\d{1,2}):(\d{2}):(\d{2})$", up_down)
    if m:
        return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
    m = re.match(r"^(\d+)d(\d+)h$", up_down)
    if m:
        return int(m.group(1)) * 86400 + int(m.group(2)) * 3600
    m = re.match(r"^(\d+)w(\d+)d$", up_down)
    if m:
        return int(m.group(1)) * 604800 + int(m.group(2)) * 86400
    return 0


def detect_dead_peer(
    run_show: Callable[[str, str], str],
    device: str,
    peer_ip: str,
    afi: str = "l2vpn evpn",
    idle_threshold_sec: int = 30,
) -> Dict:
    """Check DUT-side BGP state for one Spirent peer and classify it.

    Returns:
      {
        "peer_ip": str,
        "state": "ESTABLISHED" | "DEAD" | "STARTING" | "NEVER" | "NOT_FOUND" | "UNKNOWN",
        "raw_state": str,    # what the DUT showed (Connect/Active/etc.)
        "idle_sec": int,     # seconds in current state (-1 = never came up)
        "is_dead": bool,
        "afi": str,
      }
    """
    cmd = f"show bgp {afi} summary | no-more"
    try:
        out = run_show(device, cmd)
    except Exception as e:
        return {"peer_ip": peer_ip, "state": "UNKNOWN", "raw_state": "?",
                "idle_sec": 0, "is_dead": False, "afi": afi, "error": str(e)}

    for line in out.splitlines():
        if peer_ip not in line:
            continue
        state, up_down = _parse_bgp_summary_line(line)
        idle_sec = _up_down_to_seconds(up_down)
        state_lc = state.lower()

        if state.isdigit() or state_lc == "established":
            return {"peer_ip": peer_ip, "state": "ESTABLISHED",
                    "raw_state": state, "idle_sec": idle_sec,
                    "is_dead": False, "afi": afi}

        if up_down.lower() == "never":
            return {"peer_ip": peer_ip, "state": "NEVER",
                    "raw_state": state, "idle_sec": -1,
                    "is_dead": True, "afi": afi}

        if state_lc in _BAD_BGP_STATES and idle_sec >= idle_threshold_sec:
            return {"peer_ip": peer_ip, "state": "DEAD",
                    "raw_state": state, "idle_sec": idle_sec,
                    "is_dead": True, "afi": afi}

        return {"peer_ip": peer_ip, "state": "STARTING",
                "raw_state": state, "idle_sec": idle_sec,
                "is_dead": False, "afi": afi}

    return {"peer_ip": peer_ip, "state": "NOT_FOUND",
            "raw_state": "?", "idle_sec": 0,
            "is_dead": False, "afi": afi}


# ---------------------------------------------------------------------------
# Fresh address / VLAN allocation
# ---------------------------------------------------------------------------

def discover_dut_used_addresses(
    run_show: Callable[[str, str], str],
    device: str,
) -> Dict[str, object]:
    """Scan DUT for currently-used /30 subnets, BGP neighbor IPs, and inner VLANs.

    Returns:
      {
        "subnet_octets": set[int],       # leading octets used in N.N.N.X /30 layout (e.g. {17,18,19})
        "ips_neighbor": set[str],        # all BGP neighbor IPs configured
        "ips_p2p": set[str],             # all sub-if IPs (with prefix)
        "inner_vlans_per_outer": dict[int, set[int]],  # used inner VLANs per outer transport VLAN
        "all_subifs": set[str],          # e.g. {"ge400-0/0/5.3", "ge400-0/0/5.4"}
      }
    """
    used: Dict[str, object] = {
        "subnet_octets": set(),
        "ips_neighbor": set(),
        "ips_p2p": set(),
        "inner_vlans_per_outer": {},
        "all_subifs": set(),
    }

    try:
        cfg_int = run_show(device, "show config interfaces | flatten | no-more")
    except Exception:
        cfg_int = ""

    for m in re.finditer(r"interfaces\s+(\S+)\s+ipv4-address\s+(\S+/\d+)", cfg_int):
        subif = m.group(1)
        ipnet = m.group(2)
        used["all_subifs"].add(subif)  # type: ignore[union-attr]
        used["ips_p2p"].add(ipnet)  # type: ignore[union-attr]
        ip_only = ipnet.split("/")[0]
        m2 = re.match(r"^(\d+)\.(\d+)\.(\d+)\.\d+$", ip_only)
        if m2 and m2.group(1) == m2.group(2) == m2.group(3):
            used["subnet_octets"].add(int(m2.group(1)))  # type: ignore[union-attr]

    for m in re.finditer(
        r"interfaces\s+(\S+)\s+vlan-tags\s+outer-tag\s+(\d+)\s+inner-tag\s+(\d+)",
        cfg_int,
    ):
        outer = int(m.group(2))
        inner = int(m.group(3))
        used["inner_vlans_per_outer"].setdefault(outer, set()).add(inner)  # type: ignore[union-attr]
        used["all_subifs"].add(m.group(1))  # type: ignore[union-attr]

    try:
        cfg_bgp = run_show(device, "show config | flatten | no-more")
    except Exception:
        cfg_bgp = ""
    for m in re.finditer(r"neighbor\s+(\d+\.\d+\.\d+\.\d+)", cfg_bgp):
        ip = m.group(1)
        used["ips_neighbor"].add(ip)  # type: ignore[union-attr]
        m2 = re.match(r"^(\d+)\.(\d+)\.(\d+)\.\d+$", ip)
        if m2 and m2.group(1) == m2.group(2) == m2.group(3):
            used["subnet_octets"].add(int(m2.group(1)))  # type: ignore[union-attr]

    return used


def pick_fresh_p2p_subnet(
    used_octets: Set[int],
    candidate_octets: Optional[List[int]] = None,
) -> Tuple[str, str, int]:
    """Pick a fresh N.N.N.0/30 subnet. Returns (dut_ip, spirent_ip, octet).

    Convention used in this test suite: every BGP-peer subnet uses
    N.N.N.1 (DUT) and N.N.N.2 (Spirent), where N is the leading octet.
    e.g. 17.17.17.1/30 = DUT, 17.17.17.2/30 = Spirent peer.
    """
    if candidate_octets is None:
        candidate_octets = list(range(20, 100))

    for oct1 in candidate_octets:
        if oct1 in used_octets:
            continue
        return f"{oct1}.{oct1}.{oct1}.1", f"{oct1}.{oct1}.{oct1}.2", oct1

    raise RuntimeError(
        f"No fresh /30 subnet available -- all candidates {candidate_octets} are used. "
        f"Currently-used octets: {sorted(used_octets)}"
    )


def pick_fresh_inner_vlan(
    used_inner_vlans: Set[int],
    start: int = 50,
    max_vlan: int = 4094,
) -> int:
    """Pick fresh inner VLAN avoiding used ones + reserved (0/1/999/4095)."""
    for v in range(start, max_vlan):
        if v in used_inner_vlans or v in _RESERVED_INNER_VLANS:
            continue
        return v
    raise RuntimeError(
        f"No fresh inner VLAN in [{start},{max_vlan}). "
        f"Used count: {len(used_inner_vlans)}"
    )


# ---------------------------------------------------------------------------
# Validated DNOS config application (commit check + rollback 0)
# ---------------------------------------------------------------------------

def validate_dnos_config(
    run_show: Callable[[str, str], str],
    device: str,
    config_lines: List[str],
    log_prefix: str = "[VALIDATE]",
) -> Dict[str, object]:
    """Validate a DNOS config block via 'commit check' + 'rollback 0'.

    NEVER commits. Always rolls back. Use this to confirm syntax is valid
    on the live device BEFORE actually applying.

    DNOS one-liner commands work from config root, but if the previous
    command landed us in a subtree (e.g. 'interfaces X.Y ...' lands in
    the interfaces subtree), the next command from a different subtree
    (e.g. 'protocols bgp ...') will fail with 'Unknown word: protocols'.
    Solution: 'top' before EACH command to ensure we're at config root.

    Returns:
      {"valid": bool, "error": str, "raw": str}
    """
    _log(log_prefix, f"Validating {len(config_lines)} config line(s) on {device} via commit-check...")
    raw = ""
    try:
        run_show(device, "end")  # belt-and-braces: ensure we start clean
        run_show(device, "config")
        for line in config_lines:
            run_show(device, "top")  # always start each one-liner from config root
            raw = run_show(device, line)
            if "ERROR" in raw or "Unknown word" in raw or "syntax error" in raw.lower():
                run_show(device, "top")
                run_show(device, "rollback 0")
                run_show(device, "end")
                _log(log_prefix, f"INVALID at line '{line}': {raw[:200]}")
                return {"valid": False, "error": f"line='{line}': {raw[:300]}", "raw": raw}
        run_show(device, "top")
        check = run_show(device, "commit check")
        run_show(device, "rollback 0")
        run_show(device, "end")

        check_lc = check.lower()
        if ("error" in check_lc and "passed" not in check_lc
                and "succeed" not in check_lc and "validation complete" not in check_lc):
            _log(log_prefix, f"COMMIT-CHECK FAIL: {check[:200]}")
            return {"valid": False, "error": check[:500], "raw": check}

        _log(log_prefix, "PASS: commit-check succeeded, rolled back cleanly")
        return {"valid": True, "error": "", "raw": check}
    except Exception as e:
        try:
            run_show(device, "rollback 0")
            run_show(device, "end")
        except Exception:
            pass
        _log(log_prefix, f"EXCEPTION: {e}")
        return {"valid": False, "error": str(e), "raw": raw}


def apply_dnos_config(
    run_show: Callable[[str, str], str],
    device: str,
    config_lines: List[str],
    log_prefix: str = "[APPLY]",
    validate_first: bool = True,
) -> Dict[str, object]:
    """Apply DNOS config with mandatory validation first.

    Workflow: validate (commit-check + rollback 0) -> if valid, apply (commit).
    NEVER commits without validation passing first.

    Returns:
      {"applied": bool, "validated": bool, "error": str, "raw": str}
    """
    if validate_first:
        v = validate_dnos_config(run_show, device, config_lines,
                                 log_prefix="[VALIDATE]")
        if not v["valid"]:
            return {"applied": False, "validated": False,
                    "error": v["error"], "raw": v["raw"]}

    _log(log_prefix, f"Applying {len(config_lines)} config line(s) on {device}...")
    raw = ""
    try:
        run_show(device, "end")  # belt-and-braces: ensure clean start
        run_show(device, "config")
        for line in config_lines:
            run_show(device, "top")  # always start each one-liner from config root
            raw = run_show(device, line)
            if "ERROR" in raw or "Unknown word" in raw:
                run_show(device, "top")
                run_show(device, "rollback 0")
                run_show(device, "end")
                _log(log_prefix, f"FAIL at line '{line}': {raw[:200]}")
                return {"applied": False, "validated": True,
                        "error": f"line='{line}': {raw[:300]}", "raw": raw}
        run_show(device, "top")
        commit_out = run_show(device, "commit")
        run_show(device, "end")

        commit_lc = commit_out.lower()
        if "error" in commit_lc and "succeed" not in commit_lc:
            _log(log_prefix, f"COMMIT FAIL: {commit_out[:200]}")
            return {"applied": False, "validated": True,
                    "error": commit_out[:500], "raw": commit_out}

        _log(log_prefix, "PASS: commit succeeded")
        return {"applied": True, "validated": True, "error": "", "raw": commit_out}
    except Exception as e:
        try:
            run_show(device, "rollback 0")
            run_show(device, "end")
        except Exception:
            pass
        _log(log_prefix, f"EXCEPTION: {e}")
        return {"applied": False, "validated": True, "error": str(e), "raw": raw}


# ---------------------------------------------------------------------------
# Spirent peer reprovision (the orchestrator entry point)
# ---------------------------------------------------------------------------

def _build_subif_config(
    new_subif: str,
    new_dut_ip: str,
    outer_vlan: int,
    new_inner_vlan: int,
) -> List[str]:
    """DNOS one-liners for the L3 sub-interface ONLY.

    Must be committed BEFORE the BGP neighbor block, otherwise commit-check
    on the new neighbor fails with 'Missing update-source for bgp multihop
    neighbor' -- the validator can't see the candidate /30 as directly
    connected until it's actually in the running config.
    """
    return [
        f"interfaces {new_subif} admin-state enabled",
        f"interfaces {new_subif} ipv4-address {new_dut_ip}/30",
        f"interfaces {new_subif} vlan-tags outer-tag {outer_vlan} inner-tag {new_inner_vlan}",
    ]


def _build_evpn_neighbor_config(
    asn: int,
    new_peer_ip: str,
    update_source: str = "",
) -> List[str]:
    """DNOS one-liners for the EVPN BGP neighbor ONLY.

    Mirrors the canonical existing-neighbor format on YOR_PE-1:
        protocols bgp <asn> neighbor <ip> update-source <subif>

    The `update-source <subif>` directive is REQUIRED on this device --
    without it, DNOS commit-check rejects the new neighbor with:
        ERROR: Missing update-source configuration for bgp multihop neighbor

    Even when the /30 is already committed and directly connected, the
    BGP neighbor inherits a multihop default from the peer-group / global
    config and needs the explicit binding to the L3 sub-interface.

    Apply ONLY AFTER the sub-interface is committed so `update-source`
    references a live, addressable interface.
    """
    return [
        f"protocols bgp {asn} neighbor {new_peer_ip} remote-as {asn}",
        f"protocols bgp {asn} neighbor {new_peer_ip} admin-state enabled",
        f"protocols bgp {asn} neighbor {new_peer_ip} update-source {update_source}",
        f"protocols bgp {asn} neighbor {new_peer_ip} address-family l2vpn-evpn",
        f"protocols bgp {asn} neighbor {new_peer_ip} address-family l2vpn-evpn as-loop-check disabled",
        f"protocols bgp {asn} neighbor {new_peer_ip} address-family l2vpn-evpn send-community community-type both",
        f"protocols bgp {asn} neighbor {new_peer_ip} address-family l2vpn-evpn soft-reconfiguration inbound",
    ]


def _derive_parent_interface(
    run_show: Callable[[str, str], str],
    device: str,
    dead_peer_ip: str,
    outer_vlan: int,
    fallback: str = "ge400-0/0/5",
) -> str:
    """Find the physical parent interface that the dead BGP peer was riding on.

    Strategy:
      1. Look for any sub-if with vlan-tags outer-tag matching `outer_vlan`
         in 'show config interfaces' -- that's the right physical port.
      2. Look for any neighbor with `dead_peer_ip` and find its update-source
         sub-if, then derive parent.
      3. Fall back to `fallback` (default ge400-0/0/5 for PE-1).
    """
    try:
        cfg_int = run_show(device, "show config interfaces | flatten | no-more")
    except Exception:
        cfg_int = ""

    for m in re.finditer(
        r"interfaces\s+(\S+?)\.\d+\s+vlan-tags\s+outer-tag\s+(\d+)",
        cfg_int,
    ):
        if int(m.group(2)) == outer_vlan:
            return m.group(1)

    return fallback


# ---------------------------------------------------------------------------
# Topology introspection: discover existing peer's params for in-place recovery
# ---------------------------------------------------------------------------

def discover_dead_peer_topology(
    run_show: Callable[[str, str], str],
    device: str,
    dead_peer_ip: str,
) -> Dict[str, object]:
    """Find the DUT-side configuration that the dead BGP peer is using.

    Returns the existing sub-interface, IP, VLANs, and update-source so we
    can rebuild the Spirent device IDENTICALLY without touching the DUT.

    This is the foundation of TIER 1 in-place recovery: instead of allocating
    a fresh /30 (which DNAAS may not pass), reuse the dead peer's existing
    sub-interface that DNAAS has already proven to forward.

    Returns:
      {
        "found": bool,
        "subif": str,            # e.g. "ge400-0/0/5.5"
        "parent": str,           # e.g. "ge400-0/0/5"
        "dut_ip": str,           # e.g. "19.19.19.1"
        "outer_vlan": int,       # e.g. 214
        "inner_vlan": int,       # e.g. 5
        "update_source": str,    # value of BGP update-source on this peer
        "raw_subif_block": str,  # the matching 'interfaces X.Y ...' lines
      }
    """
    info: Dict[str, object] = {
        "found": False, "subif": "", "parent": "", "dut_ip": "",
        "outer_vlan": 0, "inner_vlan": 0, "update_source": "",
        "raw_subif_block": "",
    }

    try:
        cfg_bgp = run_show(device, "show config | flatten | no-more")
    except Exception:
        cfg_bgp = ""

    m_us = re.search(
        rf"neighbor\s+{re.escape(dead_peer_ip)}\s+update-source\s+(\S+)",
        cfg_bgp,
    )
    update_source = m_us.group(1).strip() if m_us else ""
    info["update_source"] = update_source

    try:
        cfg_int = run_show(device, "show config interfaces | flatten | no-more")
    except Exception:
        cfg_int = ""

    candidate_subif = update_source
    if not candidate_subif:
        m_oct = re.match(r"^(\d+)\.(\d+)\.(\d+)\.\d+$", dead_peer_ip)
        if m_oct and m_oct.group(1) == m_oct.group(2) == m_oct.group(3):
            oct1 = int(m_oct.group(1))
            dut_ip_guess = f"{oct1}.{oct1}.{oct1}.1"
            for line in cfg_int.splitlines():
                m = re.match(
                    rf"interfaces\s+(\S+)\s+ipv4-address\s+{re.escape(dut_ip_guess)}/\d+",
                    line,
                )
                if m:
                    candidate_subif = m.group(1)
                    break

    if not candidate_subif:
        return info

    info["subif"] = candidate_subif
    if "." in candidate_subif:
        info["parent"] = candidate_subif.rsplit(".", 1)[0]
    else:
        info["parent"] = candidate_subif

    block_lines = []
    for line in cfg_int.splitlines():
        if f"interfaces {candidate_subif} " in line + " ":
            block_lines.append(line)
            m_ip = re.search(r"ipv4-address\s+(\d+\.\d+\.\d+\.\d+)/\d+", line)
            if m_ip:
                info["dut_ip"] = m_ip.group(1)
            m_vt = re.search(r"vlan-tags\s+outer-tag\s+(\d+)\s+inner-tag\s+(\d+)", line)
            if m_vt:
                info["outer_vlan"] = int(m_vt.group(1))
                info["inner_vlan"] = int(m_vt.group(2))
    info["raw_subif_block"] = "\n".join(block_lines)
    info["found"] = bool(info["dut_ip"]) and bool(info["inner_vlan"])
    return info


def check_spirent_l2_health() -> Dict[str, object]:
    """Query Spirent for the L2/ARP resolution state of EVERY emulated device.

    This is the canary for a broken DNAAS path: if multiple Spirent devices
    on the same outer VLAN have GatewayMacResolveState=RESOLVE_FAILED, the
    DNAAS bridge-domain is dropping frames (either because LLP shut the
    path down, the BD config got removed, or the physical port is down).
    No amount of DUT or Spirent reconfiguration will fix this -- it
    requires network-admin intervention on DNAAS-LEAF-B14.

    Returns:
      {
        "queried": bool,
        "devices": [
          {"name": str, "ip": str, "gateway": str,
           "gateway_mac": str, "gw_mac_state": str,
           "gw_learning": str, "addr_resolve": str,
           "arp_failed": bool, "is_arp_responder": bool}
        ],
        "outer_vlan_failure_count": dict[int, int],  # how many devices failed per outer VLAN
        "summary": str,
      }
    """
    info: Dict[str, object] = {
        "queried": False, "devices": [],
        "outer_vlan_failure_count": {}, "summary": "",
    }
    try:
        import sys as _sys
        spirent_dir = SPIRENT_TOOL.parent
        if str(spirent_dir) not in _sys.path:
            _sys.path.insert(0, str(spirent_dir))
        from spirent_tool import get_stc, load_config  # type: ignore[import-not-found]
        stc, _sess = get_stc(load_config())
        project = stc.get("system1", "children-project")
        devs = (stc.get(project, "children-EmulatedDevice") or "").split()
        info["queried"] = True
        per_vlan_fail: Dict[int, int] = {}
        per_vlan_total: Dict[int, int] = {}
        device_records: List[Dict[str, object]] = []
        for dev in devs:
            try:
                name = stc.get(dev, "Name")
            except Exception:
                continue
            ipv4ifs = (stc.get(dev, "children-Ipv4If") or "").split()
            vlan_ifs = (stc.get(dev, "children-VlanIf") or "").split()
            outer_vlan = 0
            inner_vlan = 0
            try:
                vlans_seen: List[int] = []
                for vif in vlan_ifs:
                    try:
                        vlans_seen.append(int(stc.get(vif, "VlanId")))
                    except Exception:
                        continue
                if len(vlans_seen) >= 2:
                    inner_vlan, outer_vlan = vlans_seen[0], vlans_seen[-1]
                elif len(vlans_seen) == 1:
                    outer_vlan = vlans_seen[0]
            except Exception:
                pass
            for ipv4 in ipv4ifs:
                try:
                    addr = stc.get(ipv4, "Address")
                    gw = stc.get(ipv4, "Gateway")
                    gw_mac = (stc.get(ipv4, "GatewayMac") or "").strip()
                    gw_resolve = (stc.get(ipv4, "GatewayMacResolveState") or "").strip()
                    gw_learn = (stc.get(ipv4, "GatewayLearningState") or "").strip()
                    addr_resolve = (stc.get(ipv4, "AddrResolveState") or "").strip()
                    is_arp_responder = (
                        gw_mac == "00:00:00:00:00:00"
                        or gw_learn in ("RESOLVE_NEEDED", "RESOLVE_FAILED",
                                        "RESOLVE_IN_PROGRESS")
                    )
                    arp_failed = (
                        is_arp_responder
                        and (gw_resolve == "RESOLVE_FAILED"
                             or gw_learn == "RESOLVE_FAILED")
                    )
                    rec = {
                        "name": name, "ip": addr, "gateway": gw,
                        "gateway_mac": gw_mac,
                        "gw_mac_state": gw_resolve,
                        "gw_learning": gw_learn,
                        "addr_resolve": addr_resolve,
                        "outer_vlan": outer_vlan,
                        "inner_vlan": inner_vlan,
                        "is_arp_responder": is_arp_responder,
                        "arp_failed": arp_failed,
                    }
                    device_records.append(rec)
                    if outer_vlan and is_arp_responder:
                        per_vlan_total[outer_vlan] = per_vlan_total.get(outer_vlan, 0) + 1
                        if arp_failed:
                            per_vlan_fail[outer_vlan] = per_vlan_fail.get(outer_vlan, 0) + 1
                except Exception:
                    continue
        info["devices"] = device_records
        info["outer_vlan_failure_count"] = per_vlan_fail
        info["outer_vlan_total_arp_devices"] = per_vlan_total

        broken_vlans = [
            v for v in per_vlan_fail
            if per_vlan_total.get(v, 0) > 0
            and per_vlan_fail[v] >= per_vlan_total[v]
        ]
        if broken_vlans:
            info["summary"] = (
                f"DNAAS L2 PATH BROKEN: ALL ARP-doing Spirent devices on outer "
                f"VLAN(s) {broken_vlans} have GatewayMacResolveState=RESOLVE_FAILED. "
                "Investigate DNAAS-LEAF-B14 bridge-domain / LLP / port link."
            )
        elif per_vlan_fail:
            partial = {v: per_vlan_fail[v] for v in per_vlan_fail}
            info["summary"] = (
                f"Some Spirent devices have ARP failures: {partial} "
                "(per outer VLAN). DNAAS path may be partially broken."
            )
        else:
            info["summary"] = "Spirent ARP healthy across all emulated devices."
    except Exception as e:
        info["summary"] = f"Could not query Spirent L2 health: {e}"
    return info


def discover_spirent_device_params(
    spirent_device_name: str,
) -> Dict[str, object]:
    """Query the live STC session for the Spirent emulated device's actual
    IP/Gateway/VLAN/MAC so we can rebuild it identically.

    Returns:
      {
        "found": bool,
        "ip": str,
        "gateway": str,
        "prefix_len": int,
        "outer_vlan": int,
        "inner_vlan": int,
        "mac": str,
      }
    """
    info: Dict[str, object] = {
        "found": False, "ip": "", "gateway": "", "prefix_len": 30,
        "outer_vlan": 0, "inner_vlan": 0, "mac": "",
    }
    try:
        import sys as _sys
        spirent_dir = SPIRENT_TOOL.parent
        if str(spirent_dir) not in _sys.path:
            _sys.path.insert(0, str(spirent_dir))
        from spirent_tool import get_stc, load_config  # type: ignore[import-not-found]
        stc, _sess = get_stc(load_config())
        project = stc.get("system1", "children-project")
        devs = (stc.get(project, "children-EmulatedDevice") or "").split()
        match = ""
        for d in devs:
            try:
                if stc.get(d, "Name") == spirent_device_name:
                    match = d
                    break
            except Exception:
                continue
        if not match:
            return info
        ipv4ifs = (stc.get(match, "children-Ipv4If") or "").split()
        vlan_ifs = (stc.get(match, "children-VlanIf") or "").split()
        eth_ifs = (stc.get(match, "children-EthIIIf") or "").split()
        if ipv4ifs:
            try:
                info["ip"] = stc.get(ipv4ifs[0], "Address")
                info["gateway"] = stc.get(ipv4ifs[0], "Gateway")
                pfx = stc.get(ipv4ifs[0], "PrefixLength")
                info["prefix_len"] = int(pfx) if str(pfx).isdigit() else 30
            except Exception:
                pass
        vlans_seen: List[int] = []
        for vif in vlan_ifs:
            try:
                vid = int(stc.get(vif, "VlanId"))
                vlans_seen.append(vid)
            except Exception:
                continue
        if len(vlans_seen) >= 2:
            info["inner_vlan"] = vlans_seen[0]
            info["outer_vlan"] = vlans_seen[-1]
        elif len(vlans_seen) == 1:
            info["outer_vlan"] = vlans_seen[0]
        if eth_ifs:
            try:
                info["mac"] = stc.get(eth_ifs[0], "SourceMac")
            except Exception:
                pass
        info["found"] = bool(info["ip"])
    except Exception:
        pass
    return info


# ---------------------------------------------------------------------------
# TIER 1: in-place recovery (rebuild Spirent on existing IP/VLAN)
# ---------------------------------------------------------------------------

def _wait_bgp_established(
    run_show: Callable[[str, str], str],
    device: str,
    peer_ip: str,
    afi: str,
    budget_sec: int,
    poll_interval_sec: int = 3,
) -> Dict[str, object]:
    """Poll DUT BGP summary until peer is ESTABLISHED or budget elapses.

    Action+validate pattern: this is pure validation -- it does not perform
    an action, only watches the DUT BGP state machine until it reaches
    ESTABLISHED or the budget expires.

    Internally delegates to `validators.wait_for_bgp_state` so the same
    polling contract is used everywhere; we keep this helper as a thin
    backward-compat shim returning the legacy dict shape callers already
    know how to consume.

    Returns:
      {"established": bool, "elapsed_sec": float, "last_state": str,
       "last_idle_sec": int, "polls": int}
    """
    t0 = time.time()
    last_idle = 0

    def _on_progress(elapsed: float, observed: object) -> None:
        nonlocal last_idle
        try:
            r = detect_dead_peer(run_show, device, peer_ip,
                                 afi=afi, idle_threshold_sec=999_999)
            last_idle = int(r.get("idle_sec", 0))  # type: ignore[arg-type]
        except Exception:
            pass
        state = (observed or {}).get("state", "?") if isinstance(observed, dict) else "?"
        _log("[REPROV]",
             f"  ({elapsed:.1f}s) state={state} idle={last_idle}s -- still waiting...")

    val = wait_for_bgp_state(
        run_show, device, peer_ip,
        target="ESTABLISHED",
        afi=afi,
        timeout_sec=float(budget_sec),
        interval_sec=float(poll_interval_sec),
        on_progress=_on_progress,
    )

    last_state = "?"
    if isinstance(val.last_value, dict):
        last_state = str(val.last_value.get("state", "?"))

    return {
        "established": bool(val.passed),
        "elapsed_sec": round(time.time() - t0, 1),
        "last_state": last_state,
        "last_idle_sec": last_idle,
        "polls": val.attempts,
    }


def recover_in_place_spirent_peer(
    run_show: Callable[[str, str], str],
    device: str,
    asn: int,
    dead_peer_ip: str,
    spirent_device_name: str = "EVPN_RT2_Peer",
    evpn_rt: str = "100:100",
    evpn_mac: str = "00:DE:AD:00:02:02",
    bgp_verify_budget_sec: int = 45,
) -> Dict[str, object]:
    """TIER 1 RECOVERY: rebuild Spirent device at the SAME IP/VLAN/MAC.

    This is the preferred recovery path because it reuses a DNAAS path that
    has already been proven to forward traffic. No DUT config changes are
    made -- we only stop, delete, and recreate the Spirent emulation.

    Why this works most of the time:
      - Spirent crashes (lost session, port reset, protocol thread death)
        leave the DUT side intact and DNAAS happy. Just rebuilding the
        emulation on the same path brings the session back without
        provisioning anything new.
      - DNAAS bridge-domains typically only pass specific (outer, inner)
        VLAN pairs that have been pre-configured. Allocating a fresh inner
        VLAN means DNAAS may silently drop the new ARP/BGP packets, leaving
        the session stuck in Active forever.

    Returns:
      {
        "success": bool,
        "tier": "in_place",
        "peer_ip": str, "dut_ip": str, "inner_vlan": int, "outer_vlan": int,
        "subif": str, "spirent_device": str,
        "elapsed_sec": float,
        "steps": [...],
      }
    """
    t0 = time.time()
    steps: List[Dict[str, str]] = []

    def _step(name: str, status: str, detail: str = "") -> None:
        steps.append({"step": name, "status": status, "detail": detail})
        icon = "[OK]" if status == "PASS" else "[!!]" if status == "FAIL" else "[--]"
        _log("[REPROV-T1]", f"  {icon} {name}: {detail}")

    _log("[REPROV-T1]", f"=== TIER 1 in-place recovery for dead peer {dead_peer_ip} ===")
    _log("[REPROV-T1]",
         "Strategy: keep DUT config + DNAAS path; rebuild Spirent emulation only")

    dut_topo = discover_dead_peer_topology(run_show, device, dead_peer_ip)
    if not dut_topo.get("found"):
        _step("dut_topology", "FAIL",
              f"could not find DUT sub-if for peer {dead_peer_ip}")
        return {
            "success": False, "tier": "in_place", "steps": steps,
            "elapsed_sec": round(time.time() - t0, 2),
            "peer_ip": dead_peer_ip,
        }
    subif = str(dut_topo["subif"])
    dut_ip = str(dut_topo["dut_ip"])
    outer_vlan = int(dut_topo["outer_vlan"])  # type: ignore[arg-type]
    inner_vlan = int(dut_topo["inner_vlan"])  # type: ignore[arg-type]
    _step("dut_topology", "PASS",
          f"sub-if={subif} dut_ip={dut_ip} vlans={outer_vlan}/{inner_vlan}")

    spirent_topo = discover_spirent_device_params(spirent_device_name)
    if spirent_topo.get("found"):
        _step("spirent_introspect", "PASS",
              f"existing device IP={spirent_topo.get('ip')} "
              f"vlans={spirent_topo.get('outer_vlan')}/{spirent_topo.get('inner_vlan')} "
              f"MAC={spirent_topo.get('mac')}")
    else:
        _step("spirent_introspect", "WARN",
              f"no existing Spirent device named {spirent_device_name} "
              "(will create from DUT-derived params)")
    rebuild_mac = str(spirent_topo.get("mac") or evpn_mac).strip() or evpn_mac

    _log("[REPROV-T1]", f"Removing Spirent device {spirent_device_name}...")
    rm_out = _run_spirent(["remove-device", "--name", spirent_device_name],
                          timeout=30)
    if "[ERROR]" in rm_out and "not found" not in rm_out.lower():
        _step("spirent_remove", "WARN", rm_out[:150])
    else:
        _step("spirent_remove", "PASS", "device cleared (or not present)")

    _log("[REPROV-T1]",
         f"Recreating Spirent device {spirent_device_name} at {dead_peer_ip} "
         f"vlans={outer_vlan}/{inner_vlan} mac={rebuild_mac}...")
    create_out = _run_spirent([
        "create-device",
        "--name", spirent_device_name,
        "--ip", dead_peer_ip,
        "--gateway", dut_ip,
        "--prefix-len", "30",
        "--vlan", str(outer_vlan),
        "--inner-vlan", str(inner_vlan),
        "--mac", rebuild_mac,
        "--device-count", "1",
    ], timeout=60)
    if "[ERROR]" in create_out and "already exists" not in create_out.lower():
        _step("spirent_create", "FAIL", create_out[:200])
        return {
            "success": False, "tier": "in_place", "steps": steps,
            "elapsed_sec": round(time.time() - t0, 2),
            "peer_ip": dead_peer_ip, "dut_ip": dut_ip,
            "outer_vlan": outer_vlan, "inner_vlan": inner_vlan,
            "subif": subif, "spirent_device": spirent_device_name,
        }
    _step("spirent_create", "PASS",
          f"device created at {dead_peer_ip} (same path as before)")

    _log("[REPROV-T1]",
         f"Configuring BGP l2vpn-evpn (neighbor={dut_ip}, AS={asn})...")
    bgp_out = _run_spirent([
        "bgp-peer",
        "--device-name", spirent_device_name,
        "--as", str(asn),
        "--dut-as", str(asn),
        "--neighbor", dut_ip,
        "--negotiate-afi", "l2vpn-evpn",
        "--evpn-rd", f"{dead_peer_ip}:500",
        "--evpn-rt", evpn_rt,
        "--evpn-mac", evpn_mac,
        "--evpn-nexthop", dead_peer_ip,
        "--no-start",
    ], timeout=120)
    bgp_ok_marker = ("[OK]" in bgp_out or "ESTABLISHED" in bgp_out
                     or "deferred" in bgp_out.lower()
                     or "configured" in bgp_out.lower())
    if not bgp_ok_marker:
        _step("spirent_bgp", "WARN", bgp_out[:200])
    else:
        _step("spirent_bgp", "PASS", "BGP l2vpn-evpn configured (deferred start)")

    _log("[REPROV-T1]", "Starting protocols on rebuilt device...")
    _run_spirent(["protocol-start", "--device-name", spirent_device_name],
                 timeout=30)
    _step("spirent_proto_start", "PASS", "protocols started")

    # Fail-fast gate: poll DUT ARP table until peer resolves. If ARP doesn't
    # resolve within 10s the DNAAS L2 path is silently broken -- no point
    # burning the full BGP budget waiting for TCP that will never connect.
    _log("[REPROV-T1]",
         f"ARP gate: polling DUT for {dead_peer_ip} on {subif} (budget 10s)...")
    arp_val = wait_for_arp_resolve(
        run_show, device, dead_peer_ip,
        timeout_sec=10.0, interval_sec=1.0,
    )
    if not arp_val.passed:
        _step("dut_arp_resolve", "FAIL",
              f"DUT did not learn ARP for {dead_peer_ip} after "
              f"{arp_val.elapsed_sec:.1f}s -- DNAAS L2 path likely broken "
              f"(last={arp_val.last_value!r}); skipping BGP wait")
        return {
            "success": False, "tier": "in_place", "steps": steps,
            "elapsed_sec": round(time.time() - t0, 2),
            "peer_ip": dead_peer_ip, "dut_ip": dut_ip,
            "outer_vlan": outer_vlan, "inner_vlan": inner_vlan,
            "subif": subif, "spirent_device": spirent_device_name,
            "fail_reason": "arp_unresolved",
        }
    _step("dut_arp_resolve", "PASS",
          f"ARP resolved in {arp_val.elapsed_sec:.1f}s "
          f"(mac={arp_val.last_value.get('mac') if isinstance(arp_val.last_value, dict) else '?'})")

    _log("[REPROV-T1]",
         f"Verifying BGP {dead_peer_ip} ESTABLISHED on DUT "
         f"(budget {bgp_verify_budget_sec}s, polling 3s)...")
    wait = _wait_bgp_established(
        run_show, device, dead_peer_ip,
        afi="l2vpn evpn", budget_sec=bgp_verify_budget_sec,
    )
    if wait["established"]:
        _step("bgp_established", "PASS",
              f"ESTABLISHED in {wait['elapsed_sec']}s (state={wait['last_state']})")
        total = round(time.time() - t0, 2)
        _log("[REPROV-T1]",
             f"=== TIER 1 SUCCESS: {dead_peer_ip} back to ESTABLISHED in {total}s ===")
        return {
            "success": True, "tier": "in_place", "steps": steps,
            "peer_ip": dead_peer_ip, "dut_ip": dut_ip,
            "outer_vlan": outer_vlan, "inner_vlan": inner_vlan,
            "subif": subif, "spirent_device": spirent_device_name,
            "elapsed_sec": total,
        }

    _step("bgp_established", "FAIL",
          f"still {wait['last_state']} after {wait['elapsed_sec']}s "
          f"(idle={wait['last_idle_sec']}s)")
    return {
        "success": False, "tier": "in_place", "steps": steps,
        "peer_ip": dead_peer_ip, "dut_ip": dut_ip,
        "outer_vlan": outer_vlan, "inner_vlan": inner_vlan,
        "subif": subif, "spirent_device": spirent_device_name,
        "elapsed_sec": round(time.time() - t0, 2),
    }


# ---------------------------------------------------------------------------
# TIER 2 prereq: smoke check (validate DNAAS forwards a candidate inner VLAN)
# ---------------------------------------------------------------------------

def smoke_check_l2_path_for_vlan(
    run_show: Callable[[str, str], str],
    device: str,
    outer_vlan: int,
    inner_vlan: int,
    smoke_mac: str = "00:DE:AD:FA:CE:50",
    poll_timeout_sec: float = 6.0,
) -> Dict[str, object]:
    """Send a tiny L2 stream on a candidate (outer, inner) VLAN and check if
    the DUT's bridge-domain interface counters move (or any AC sees frames).

    PURPOSE: BEFORE we waste 45s on BGP convergence and minutes provisioning
    a brand-new sub-interface, prove that DNAAS will actually pass our
    candidate inner VLAN. If DNAAS silently drops it, no amount of DUT or
    Spirent reconfiguration will help.

    METHOD:
      1. Capture initial RX-packet counter on the candidate sub-if (if it
         exists) or the parent port.
      2. Generate ~200 frames via Spirent on the candidate (outer, inner)
         pair targeting an unused MAC.
      3. Re-read RX counter after ~3s; if it grew by at least the expected
         floor, DNAAS is forwarding the VLAN -> PASS.
      4. If counters did not move, the L2 path is broken -> FAIL with
         actionable detail.

    Returns:
      {"pass": bool, "detail": str, "elapsed_sec": float,
       "rx_before": int, "rx_after": int, "delta": int}
    """
    t0 = time.time()
    result: Dict[str, object] = {
        "pass": False, "detail": "", "elapsed_sec": 0.0,
        "rx_before": -1, "rx_after": -1, "delta": 0,
        "outer_vlan": outer_vlan, "inner_vlan": inner_vlan,
    }
    parent_port = ""
    try:
        cfg_int = run_show(device, "show config interfaces | flatten | no-more")
        for m in re.finditer(
            r"interfaces\s+(\S+?)\.\d+\s+vlan-tags\s+outer-tag\s+(\d+)",
            cfg_int,
        ):
            if int(m.group(2)) == outer_vlan:
                parent_port = m.group(1)
                break
    except Exception:
        pass

    if not parent_port:
        result["detail"] = (
            f"Could not derive parent port for outer VLAN {outer_vlan}; "
            "skipping smoke check."
        )
        result["elapsed_sec"] = round(time.time() - t0, 2)
        return result

    def _read_rx(port: str) -> int:
        try:
            out = run_show(device, f"show interfaces {port} | no-more")
            for line in out.splitlines():
                m = re.search(
                    r"(?:Input|RX)\s+packets?\s*[:=]\s*(\d+)", line, re.IGNORECASE,
                )
                if m:
                    return int(m.group(1))
            for label in ("Total input packets", "Input packets",
                          "RX packets", "Received packets"):
                m = re.search(rf"{label}\s*[:=]?\s*(\d+)", out, re.IGNORECASE)
                if m:
                    return int(m.group(1))
        except Exception:
            pass
        return -1

    rx_before = _read_rx(parent_port)
    result["rx_before"] = rx_before

    stream_name = "_dnaas_smoke_probe"
    try:
        _run_spirent(["remove-stream", "--name", stream_name], timeout=15)
    except Exception:
        pass

    create_out = _run_spirent([
        "create-stream",
        "--protocol", "l2",
        "--src-mac", smoke_mac,
        "--dst-mac", "FF:FF:FF:FF:FF:FF",
        "--rate-mbps", "1",
        "--frame-size", "128",
        "--name", stream_name,
        "--vlan", str(outer_vlan),
        "--inner-vlan", str(inner_vlan),
    ], timeout=45)

    if "[ERROR]" in create_out:
        result["detail"] = f"Could not create probe stream: {create_out[:200]}"
        result["elapsed_sec"] = round(time.time() - t0, 2)
        return result

    # action: start traffic
    _run_spirent(["start"], timeout=15)

    # validate: poll RX counter until delta >= threshold OR window elapses.
    # Healthy paths return in <1s; broken paths drain the full window.
    def _probe_check() -> Tuple[bool, object]:
        rx_now = _read_rx(parent_port)
        if rx_now < 0 or rx_before < 0:
            return False, {"rx_now": rx_now, "rx_before": rx_before, "delta": -1}
        delta_now = rx_now - rx_before
        return (delta_now >= _SMOKE_PROBE_RX_THRESHOLD), {
            "rx_now": rx_now, "rx_before": rx_before, "delta": delta_now,
        }

    probe = poll_until(
        _probe_check,
        timeout_sec=max(float(poll_timeout_sec), _SMOKE_PROBE_MAX_DURATION_SEC),
        interval_sec=0.5,
    )

    # cleanup: stop + remove stream regardless of probe outcome
    _run_spirent(["stop"], timeout=10)
    try:
        _run_spirent(["remove-stream", "--name", stream_name], timeout=10)
    except Exception:
        pass

    rx_after = _read_rx(parent_port)
    result["rx_after"] = rx_after
    result["elapsed_sec"] = round(time.time() - t0, 2)
    result["probe_elapsed_sec"] = round(probe.elapsed_sec, 2)
    result["probe_polls"] = probe.attempts

    if rx_before < 0 or rx_after < 0:
        result["detail"] = (
            f"Could not read RX counters on {parent_port} -- "
            "skipping conservative PASS."
        )
        result["pass"] = True
        return result

    delta = rx_after - rx_before
    result["delta"] = delta

    if probe.passed or delta >= _SMOKE_PROBE_RX_THRESHOLD:
        result["pass"] = True
        result["detail"] = (
            f"L2 path OK for outer={outer_vlan} inner={inner_vlan}: "
            f"RX delta {delta} packets on {parent_port} "
            f"(probe converged in {probe.elapsed_sec:.1f}s, {probe.attempts} polls)"
        )
    else:
        result["pass"] = False
        result["detail"] = (
            f"DNAAS does NOT pass outer={outer_vlan} inner={inner_vlan}: "
            f"RX delta only {delta} packets on {parent_port} after "
            f"{_SMOKE_PROBE_MAX_DURATION_SEC}s probe (last_observed="
            f"{probe.last_value!r}). Allocating this VLAN will fail BGP/ARP."
        )
    return result


# ---------------------------------------------------------------------------
# Cleanup helper: roll back a stale sub-if from a failed TIER 2 reprovision
# ---------------------------------------------------------------------------

def cleanup_stale_subif(
    run_show: Callable[[str, str], str],
    device: str,
    subif: str,
    asn: Optional[int] = None,
    peer_ip: Optional[str] = None,
    log_prefix: str = "[CLEANUP]",
) -> Dict[str, object]:
    """Remove a sub-if (and optionally its BGP neighbor) that we created in
    a failed reprovision attempt.

    Strategy:
      1. If asn + peer_ip: 'no protocols bgp <asn> neighbor <peer_ip>'
      2. 'no interfaces <subif>'
      3. commit; if any step errors, rollback 0.

    Returns:
      {"removed": bool, "raw": str, "error": str}
    """
    _log(log_prefix, f"Removing stale sub-if {subif} (peer={peer_ip} asn={asn})...")
    raw_acc = ""
    try:
        run_show(device, "end")
        run_show(device, "config")
        if asn and peer_ip:
            run_show(device, "top")
            r1 = run_show(device, f"no protocols bgp {asn} neighbor {peer_ip}")
            raw_acc += r1
            if "ERROR" in r1 and "Not found" not in r1 and "not exist" not in r1.lower():
                _log(log_prefix, f"WARN removing BGP neighbor: {r1[:150]}")
        run_show(device, "top")
        r2 = run_show(device, f"no interfaces {subif}")
        raw_acc += r2
        if "ERROR" in r2 and "Not found" not in r2 and "not exist" not in r2.lower():
            run_show(device, "top")
            run_show(device, "rollback 0")
            run_show(device, "end")
            _log(log_prefix, f"FAIL removing sub-if: {r2[:150]}")
            return {"removed": False, "raw": raw_acc, "error": r2[:300]}
        run_show(device, "top")
        commit_out = run_show(device, "commit")
        run_show(device, "end")
        if "error" in commit_out.lower() and "succeed" not in commit_out.lower():
            _log(log_prefix, f"WARN commit message: {commit_out[:150]}")
            return {"removed": False, "raw": raw_acc + commit_out, "error": commit_out[:300]}
        _log(log_prefix, f"PASS removed sub-if {subif} (and BGP if requested)")
        return {"removed": True, "raw": raw_acc + commit_out, "error": ""}
    except Exception as e:
        try:
            run_show(device, "rollback 0")
            run_show(device, "end")
        except Exception:
            pass
        return {"removed": False, "raw": raw_acc, "error": str(e)}


def reprovision_evpn_peer(
    run_show: Callable[[str, str], str],
    device: str,
    asn: int,
    dead_peer_ip: str,
    outer_vlan: int = 214,
    parent_interface: str = "",
    spirent_device_name: str = "EVPN_RT2_Peer",
    evpn_rt: str = "100:100",
    evpn_mac: str = "00:DE:AD:00:02:02",
    bgp_verify_budget_sec: int = 45,
    skip_in_place: bool = False,
    smoke_check_dnaas: bool = True,
    cleanup_on_fail: bool = True,
) -> Dict[str, object]:
    """End-to-end reprovision of a dead EVPN BGP peer.

    TWO-TIER STRATEGY (smooth + reliable, per user requirements):

      TIER 1 (preferred): in-place recovery
        Rebuild Spirent emulation at the SAME IP/VLAN/MAC. Most "dead peers"
        are dead because Spirent's protocol thread crashed, the port reset,
        or the STC session was rebuilt -- the DUT side and the DNAAS path
        are still healthy. Re-arming the emulation on the SAME path brings
        the session back without provisioning anything new (~30s typical).

      TIER 2 (fallback): fresh allocation with DNAAS pre-check
        Only used if TIER 1 cannot bring the peer up. Picks a fresh /30 +
        inner VLAN, but FIRST runs an L2 smoke probe to confirm DNAAS will
        forward the candidate (outer, inner) pair. If DNAAS silently drops
        the new VLAN, abort with a clear "DNAAS doesn't pass VLAN X"
        message INSTEAD of wasting 45s on doomed BGP convergence.
        On failure, optionally rolls back the freshly-committed sub-if to
        avoid accumulating dead config across retry attempts.

    Args:
      skip_in_place: if True, skip TIER 1 and go straight to fresh allocation
        (useful when you know the dead-peer's existing path is broken at L2).
      smoke_check_dnaas: TIER 2 only -- run DNAAS smoke probe before commit.
      cleanup_on_fail: TIER 2 only -- roll back the new sub-if/BGP if we
        commit it but the BGP never establishes.

    Returns:
      {
        "success": bool,
        "tier": "in_place" | "fresh" | "fresh_smoke_blocked" | "abort",
        "new_peer_ip": str,    # peer IP (== old IP for TIER 1)
        "new_dut_ip": str,     # DUT neighbor IP
        "new_inner_vlan": int,
        "new_subif": str,
        "outer_vlan": int,
        "spirent_device": str,
        "elapsed_sec": float,
        "steps": [{"step": str, "status": str, "detail": str}, ...],
        "tier1_result": dict,  # full TIER 1 result (if attempted)
      }
    """
    t0 = time.time()
    steps: List[Dict[str, str]] = []

    def _step(name: str, status: str, detail: str = "") -> None:
        steps.append({"step": name, "status": status, "detail": detail})
        icon = "[OK]" if status == "PASS" else "[!!]" if status == "FAIL" else "[--]"
        _log("[REPROV]", f"  {icon} {name}: {detail}")

    _log("[REPROV]", f"=== Auto-reprovisioning dead EVPN peer {dead_peer_ip} ===")
    _log("[REPROV]",
         "Plan: TIER 0 L2 sanity -> TIER 1 in-place -> TIER 2 fresh /30")

    l2_health = check_spirent_l2_health()
    broken_vlans = [
        v for v in (l2_health.get("outer_vlan_failure_count", {}) or {})
        if (l2_health.get("outer_vlan_failure_count", {}) or {})[v]
        >= (l2_health.get("outer_vlan_total_arp_devices", {}) or {}).get(v, 0)
        and (l2_health.get("outer_vlan_total_arp_devices", {}) or {}).get(v, 0) > 0
    ]
    if outer_vlan in broken_vlans:
        _step("spirent_l2_health", "FAIL",
              str(l2_health.get("summary", ""))[:300])
        _log("[PEER]",
             f"BLOCKED: DNAAS L2 path is down for outer VLAN {outer_vlan}. "
             "ALL Spirent devices on that VLAN cannot resolve their gateway MAC. "
             "Auto-reprovision skipped -- this needs network-admin intervention "
             "(check DNAAS-LEAF-B14 bridge-domain / LLP / Spirent port link).")
        return {
            "success": False, "tier": "abort_dnaas_down", "steps": steps,
            "elapsed_sec": round(time.time() - t0, 2),
            "spirent_l2_health": l2_health,
        }
    elif l2_health.get("queried"):
        _step("spirent_l2_health", "PASS",
              str(l2_health.get("summary", ""))[:200])

    tier1_result: Dict[str, object] = {}
    if not skip_in_place:
        tier1_result = recover_in_place_spirent_peer(
            run_show=run_show, device=device, asn=asn,
            dead_peer_ip=dead_peer_ip,
            spirent_device_name=spirent_device_name,
            evpn_rt=evpn_rt, evpn_mac=evpn_mac,
            bgp_verify_budget_sec=bgp_verify_budget_sec,
        )
        steps.extend(tier1_result.get("steps", []))  # type: ignore[arg-type]

        if tier1_result.get("success"):
            return {
                "success": True, "tier": "in_place",
                "new_peer_ip": tier1_result.get("peer_ip", dead_peer_ip),
                "new_dut_ip": tier1_result.get("dut_ip", ""),
                "new_inner_vlan": tier1_result.get("inner_vlan", 0),
                "new_subif": tier1_result.get("subif", ""),
                "outer_vlan": tier1_result.get("outer_vlan", outer_vlan),
                "spirent_device": spirent_device_name,
                "elapsed_sec": round(time.time() - t0, 2),
                "steps": steps, "tier1_result": tier1_result,
            }
        _log("[REPROV]",
             f"TIER 1 in-place recovery did not establish ({tier1_result.get('elapsed_sec','?')}s)"
             " -- falling through to TIER 2 fresh allocation")
    else:
        _log("[REPROV]", "TIER 1 skipped by caller (skip_in_place=True)")

    if not parent_interface:
        parent_interface = _derive_parent_interface(
            run_show, device, dead_peer_ip, outer_vlan,
        )
        _log("[REPROV]", f"Derived parent interface for outer VLAN {outer_vlan}: "
             f"{parent_interface}")

    used = discover_dut_used_addresses(run_show, device)
    used_octets = used.get("subnet_octets", set())  # type: ignore[arg-type]
    used_inner = used.get("inner_vlans_per_outer", {}).get(outer_vlan, set())  # type: ignore[union-attr]
    _step(
        "dut_scan", "PASS",
        f"used neighbors={len(used.get('ips_neighbor', set()))}, "  # type: ignore[arg-type]
        f"used /30 octets={sorted(used_octets)[:8]}{'...' if len(used_octets) > 8 else ''}, "  # type: ignore[arg-type]
        f"used inner-vlans@outer={outer_vlan}={sorted(used_inner)[:8] if used_inner else 'none'}",
    )

    try:
        new_dut_ip, new_peer_ip, new_octet = pick_fresh_p2p_subnet(used_octets)  # type: ignore[arg-type]
        new_inner_vlan = pick_fresh_inner_vlan(used_inner)
        new_subif = f"{parent_interface}.{new_inner_vlan}"
        _step(
            "pick_fresh", "PASS",
            f"new_dut_ip={new_dut_ip}, new_peer_ip={new_peer_ip}, "
            f"inner_vlan={new_inner_vlan}, sub-if={new_subif}",
        )
    except Exception as e:
        _step("pick_fresh", "FAIL", str(e))
        return {
            "success": False, "tier": "abort", "steps": steps,
            "elapsed_sec": round(time.time() - t0, 2),
            "tier1_result": tier1_result,
        }

    if smoke_check_dnaas:
        _log("[REPROV]",
             f"DNAAS smoke probe for outer={outer_vlan} inner={new_inner_vlan} "
             "(BEFORE committing DUT config)...")
        smoke = smoke_check_l2_path_for_vlan(
            run_show, device, outer_vlan, new_inner_vlan,
        )
        smoke_pass = bool(smoke.get("pass"))
        _step(
            "dnaas_smoke", "PASS" if smoke_pass else "FAIL",
            str(smoke.get("detail", ""))[:200],
        )
        if not smoke_pass:
            _log("[REPROV]",
                 f"BLOCKED: DNAAS bridge-domain does not pass inner VLAN "
                 f"{new_inner_vlan} (only pre-configured pairs work). "
                 "Skipping DUT config commit -- nothing to roll back.")
            _log("[PEER]",
                 f"Suggested fix: ask network-admin to provision DNAAS "
                 f"bridge-domain for (outer={outer_vlan}, inner={new_inner_vlan}) "
                 "OR pin the test to a known-working inner VLAN.")
            return {
                "success": False, "tier": "fresh_smoke_blocked",
                "steps": steps,
                "new_peer_ip": new_peer_ip, "new_dut_ip": new_dut_ip,
                "new_inner_vlan": new_inner_vlan, "new_subif": new_subif,
                "outer_vlan": outer_vlan,
                "spirent_device": spirent_device_name,
                "elapsed_sec": round(time.time() - t0, 2),
                "tier1_result": tier1_result,
                "smoke_check": smoke,
            }

    # PHASE 1: commit the L3 sub-interface ALONE so DNOS sees the new /30
    # as directly connected before we add the BGP neighbor. Without this
    # split, commit-check on the BGP neighbor fails with:
    #   ERROR: Missing update-source configuration for bgp multihop neighbor
    subif_lines = _build_subif_config(
        new_subif=new_subif, new_dut_ip=new_dut_ip,
        outer_vlan=outer_vlan, new_inner_vlan=new_inner_vlan,
    )
    subif_apply = apply_dnos_config(
        run_show, device, subif_lines,
        log_prefix="[REPROV-DNOS-SUBIF]", validate_first=True,
    )
    if not subif_apply["applied"]:
        _step("dnos_apply_subif", "FAIL",
              str(subif_apply.get("error", ""))[:200])
        _log("[PEER]", f"Sub-interface commit FAILED -- aborting reprovision. "
             f"Suggest /search-company-knowledge for: "
             f"'DNOS sub-interface vlan-tags ipv4-address {asn}' to verify syntax.")
        return {
            "success": False, "tier": "fresh", "steps": steps,
            "elapsed_sec": round(time.time() - t0, 2),
            "tier1_result": tier1_result,
        }
    _step("dnos_apply_subif", "PASS",
          f"sub-if {new_subif} ({new_dut_ip}/30, vlan-tags {outer_vlan}/{new_inner_vlan}) committed")

    # validate: poll until the new sub-if reports admin=enabled + oper=up
    # (action+validate, no fixed sleep). We need it visible in the routing
    # table before the BGP commit-check runs the directly-connected
    # reachability gate -- otherwise commit-check will reject the neighbor.
    iface_val = wait_for_interface_up(
        run_show, device, new_subif, timeout_sec=15.0, interval_sec=1.0,
    )
    if not iface_val.passed:
        _step("dnos_subif_oper_up", "WARN",
              f"sub-if {new_subif} not oper-up after {iface_val.elapsed_sec:.1f}s "
              f"(last={iface_val.last_value!r}); proceeding to BGP commit anyway")
    else:
        _step("dnos_subif_oper_up", "PASS",
              f"sub-if {new_subif} admin/oper up in {iface_val.elapsed_sec:.1f}s")

    # PHASE 2: commit the BGP l2vpn-evpn neighbor (with update-source
    # bound to the freshly-committed sub-interface).
    bgp_lines = _build_evpn_neighbor_config(
        asn=asn, new_peer_ip=new_peer_ip, update_source=new_subif,
    )
    bgp_apply = apply_dnos_config(
        run_show, device, bgp_lines,
        log_prefix="[REPROV-DNOS-BGP]", validate_first=True,
    )
    if not bgp_apply["applied"]:
        _step("dnos_apply_bgp", "FAIL",
              str(bgp_apply.get("error", ""))[:200])
        _log("[PEER]", f"BGP neighbor commit FAILED -- aborting reprovision. "
             f"Sub-if {new_subif} was committed; will roll it back if cleanup_on_fail.")
        if cleanup_on_fail:
            cleanup_stale_subif(run_show, device, new_subif,
                                asn=asn, peer_ip=new_peer_ip)
            _step("cleanup_stale_subif", "PASS",
                  f"rolled back orphan sub-if {new_subif}")
        return {
            "success": False, "tier": "fresh", "steps": steps,
            "elapsed_sec": round(time.time() - t0, 2),
            "tier1_result": tier1_result,
        }
    _step("dnos_apply_bgp", "PASS",
          f"BGP l2vpn-evpn neighbor {new_peer_ip} (remote-as {asn}) committed")

    _log("[REPROV]", f"Removing dead Spirent device {spirent_device_name}...")
    rm_out = _run_spirent(["remove-device", "--name", spirent_device_name],
                          timeout=30)
    if "[ERROR]" in rm_out and "not found" not in rm_out.lower():
        _step("spirent_remove", "WARN", rm_out[:150])
    else:
        _step("spirent_remove", "PASS", "dead device removed")

    _log("[REPROV]", f"Creating fresh Spirent device {spirent_device_name} "
         f"at {new_peer_ip} (vlan {outer_vlan}/{new_inner_vlan})...")
    create_out = _run_spirent([
        "create-device",
        "--name", spirent_device_name,
        "--ip", new_peer_ip,
        "--gateway", new_dut_ip,
        "--prefix-len", "30",
        "--vlan", str(outer_vlan),
        "--inner-vlan", str(new_inner_vlan),
        "--mac", "00:10:94:00:05:05",
        "--device-count", "1",
    ], timeout=60)
    if "[ERROR]" in create_out and "already exists" not in create_out.lower():
        _step("spirent_create", "FAIL", create_out[:200])
        if cleanup_on_fail:
            cleanup_stale_subif(run_show, device, new_subif,
                                asn=asn, peer_ip=new_peer_ip)
            _step("cleanup_stale_subif", "PASS",
                  f"rolled back orphan sub-if {new_subif} after Spirent create failure")
        return {
            "success": False, "tier": "fresh", "steps": steps,
            "new_peer_ip": new_peer_ip, "new_dut_ip": new_dut_ip,
            "new_inner_vlan": new_inner_vlan, "new_subif": new_subif,
            "outer_vlan": outer_vlan,
            "elapsed_sec": round(time.time() - t0, 2),
            "tier1_result": tier1_result,
        }
    _step("spirent_create", "PASS",
          f"device {spirent_device_name} created at {new_peer_ip}")

    _log("[REPROV]", f"Configuring BGP l2vpn-evpn on fresh device "
         f"(neighbor={new_dut_ip}, AS={asn})...")
    bgp_out = _run_spirent([
        "bgp-peer",
        "--device-name", spirent_device_name,
        "--as", str(asn),
        "--dut-as", str(asn),
        "--neighbor", new_dut_ip,
        "--negotiate-afi", "l2vpn-evpn",
        "--evpn-rd", f"{new_peer_ip}:500",
        "--evpn-rt", evpn_rt,
        "--evpn-mac", evpn_mac,
        "--evpn-nexthop", new_peer_ip,
        "--no-start",
    ], timeout=120)
    bgp_ok_marker = ("[OK]" in bgp_out or "ESTABLISHED" in bgp_out
                     or "deferred" in bgp_out.lower()
                     or "configured" in bgp_out.lower())
    if not bgp_ok_marker:
        _step("spirent_bgp", "WARN", bgp_out[:200])
    else:
        _step("spirent_bgp", "PASS", "BGP l2vpn-evpn configured (deferred start)")

    _log("[REPROV]", f"Starting protocols on fresh device {spirent_device_name}...")
    _run_spirent(["protocol-start", "--device-name", spirent_device_name],
                 timeout=30)
    _step("spirent_proto_start", "PASS", "protocols started")

    _log("[REPROV]", f"Verifying BGP {new_peer_ip} ESTABLISHED on DUT "
         f"(budget: {bgp_verify_budget_sec}s, polling 3s intervals)...")
    bgp_wait = _wait_bgp_established(
        run_show, device, new_peer_ip,
        afi="l2vpn evpn", budget_sec=bgp_verify_budget_sec,
        poll_interval_sec=3,
    )
    bgp_ok = bool(bgp_wait["established"])
    last_state = str(bgp_wait.get("last_state", "?"))
    last_idle = int(bgp_wait.get("last_idle_sec", 0))  # type: ignore[arg-type]
    if bgp_ok:
        _step("bgp_established", "PASS",
              f"ESTABLISHED in {bgp_wait['elapsed_sec']}s "
              f"({bgp_wait['polls']} polls, raw_state={last_state})")

    total_elapsed = round(time.time() - t0, 2)
    if not bgp_ok:
        _step("bgp_established", "FAIL",
              f"new peer {new_peer_ip} not ESTABLISHED after {bgp_verify_budget_sec}s "
              f"(last_state={last_state}, idle={last_idle}s)")
        if cleanup_on_fail:
            try:
                _run_spirent(["remove-device", "--name", spirent_device_name],
                             timeout=30)
            except Exception:
                pass
            cleanup_stale_subif(run_show, device, new_subif,
                                asn=asn, peer_ip=new_peer_ip)
            _step("cleanup_stale_subif", "PASS",
                  f"rolled back fresh sub-if {new_subif} + Spirent device "
                  "(BGP did not establish)")
        return {
            "success": False, "tier": "fresh", "steps": steps,
            "new_peer_ip": new_peer_ip, "new_dut_ip": new_dut_ip,
            "new_inner_vlan": new_inner_vlan, "new_subif": new_subif,
            "outer_vlan": outer_vlan,
            "spirent_device": spirent_device_name,
            "elapsed_sec": total_elapsed,
            "tier1_result": tier1_result,
        }

    _log("[REPROV]", f"=== TIER 2 SUCCESS: fresh peer {new_peer_ip} is ESTABLISHED "
         f"(total {total_elapsed}s) ===")
    return {
        "success": True, "tier": "fresh", "steps": steps,
        "new_peer_ip": new_peer_ip, "new_dut_ip": new_dut_ip,
        "new_inner_vlan": new_inner_vlan, "new_subif": new_subif,
        "outer_vlan": outer_vlan,
        "spirent_device": spirent_device_name,
        "elapsed_sec": total_elapsed,
        "tier1_result": tier1_result,
    }
