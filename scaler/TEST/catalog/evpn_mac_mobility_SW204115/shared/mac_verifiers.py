#!/usr/bin/env python3
"""
Verification helpers for MAC mobility outcomes.

Covers: presence, source, sequence, suppression, sticky, aging,
count comparison, and HA recovery checks.
"""

from __future__ import annotations

import re
import time
from typing import Any, Callable, Dict, List, Optional

from .mac_parsers import (
    MAC_ADDR_RE,
    extract_first_mac,
    parse_evpn_mac_count,
    parse_evpn_mac_entries,
    parse_fib_evpn_mac,
    parse_forwarding_table_flags,
    parse_ghost_macs,
    parse_loop_prevention_interface,
    parse_loop_prevention_mac_table,
    parse_mac_detail,
    parse_mac_mobility_redis_count,
    parse_mac_suppress,
    strip_ansi,
)

RunShowFn = Callable[[str, str], str]


# ---------------------------------------------------------------------------
# Basic checks (original, kept intact)
# ---------------------------------------------------------------------------

def verify_mac_present(mac_table_output: str, mac: str) -> Dict[str, Any]:
    mac_l = mac.lower()
    text = strip_ansi(mac_table_output)
    ok = mac_l in text.lower()
    return {"pass": ok, "mac": mac_l, "detail": "found in output" if ok else "not found"}


def verify_mac_source(
    mac_table_output: str,
    mac: str,
    expected_sources: List[str],
) -> Dict[str, Any]:
    mac_l = mac.lower()
    entries = parse_evpn_mac_entries(mac_table_output)
    for e in entries:
        if e["mac"] == mac_l:
            hint = e["source_hint"]
            aliases = e.get("source_aliases", [hint])
            ok = any(a in expected_sources for a in aliases) or (
                "unknown" in expected_sources and hint == "unknown"
            )
            return {
                "pass": ok,
                "mac": mac_l,
                "source_hint": hint,
                "source_aliases": aliases,
                "expected": expected_sources,
                "line": e["line"],
            }
    return {"pass": False, "mac": mac_l, "detail": "no matching entry"}


def compare_mac_count(before: str, after: str) -> Dict[str, Any]:
    b = parse_evpn_mac_count(before)
    a = parse_evpn_mac_count(after)
    return {"before": b, "after": a, "delta": a - b}


def first_mac_from_output(output: str) -> Optional[str]:
    return extract_first_mac(output)


# ---------------------------------------------------------------------------
# Sequence number verification (RFC 8560)
# ---------------------------------------------------------------------------

_SEQ_RE = re.compile(r"seq(?:uence)?[\s:=]+(\d+)", re.IGNORECASE)


def extract_sequence_number(mac_entry_line: str) -> Optional[int]:
    m = _SEQ_RE.search(strip_ansi(mac_entry_line))
    return int(m.group(1)) if m else None


def verify_sequence_incremented(
    before_output: str,
    after_output: str,
    mac: str,
) -> Dict[str, Any]:
    """After a MAC move, the sequence number must be strictly greater."""
    mac_l = mac.lower()
    before_entries = parse_evpn_mac_entries(before_output)
    after_entries = parse_evpn_mac_entries(after_output)

    seq_before: Optional[int] = None
    seq_after: Optional[int] = None

    for e in before_entries:
        if e["mac"] == mac_l:
            seq_before = extract_sequence_number(e["line"])
            break
    for e in after_entries:
        if e["mac"] == mac_l:
            seq_after = extract_sequence_number(e["line"])
            break

    if seq_before is None or seq_after is None:
        return {
            "pass": False,
            "detail": f"Could not parse sequence: before={seq_before}, after={seq_after}",
            "seq_before": seq_before,
            "seq_after": seq_after,
        }

    ok = seq_after > seq_before
    return {
        "pass": ok,
        "seq_before": seq_before,
        "seq_after": seq_after,
        "detail": f"seq {seq_before} -> {seq_after}" + (" (incremented)" if ok else " (NOT incremented)"),
    }


# ---------------------------------------------------------------------------
# Suppression / sanction detection
# ---------------------------------------------------------------------------

SUPPRESSION_KEYWORDS = ["FROZEN", "SUPPRESSED", "BLOCKED", "SHUT", "DROP", "DUPLICATE"]


def verify_suppression_active(
    mac_table_output: str,
    mac: str,
) -> Dict[str, Any]:
    """Check if any suppression/sanction keyword appears for this MAC."""
    mac_l = mac.lower()
    entries = parse_evpn_mac_entries(mac_table_output)
    for e in entries:
        if e["mac"] == mac_l:
            upper = e["line"].upper()
            found = [kw for kw in SUPPRESSION_KEYWORDS if kw in upper]
            if found:
                return {
                    "pass": True,
                    "mac": mac_l,
                    "sanctions": found,
                    "detail": f"Sanctions active: {', '.join(found)}",
                    "line": e["line"],
                }
            return {
                "pass": False,
                "mac": mac_l,
                "detail": "No suppression keywords found",
                "line": e["line"],
            }
    return {"pass": False, "mac": mac_l, "detail": "MAC not found in table"}


def verify_suppression_cleared(
    mac_table_output: str,
    mac: str,
) -> Dict[str, Any]:
    """After suppression timeout, sanctions should be removed."""
    result = verify_suppression_active(mac_table_output, mac)
    if result["pass"]:
        return {
            "pass": False,
            "mac": mac,
            "detail": f"Sanctions still active: {result.get('sanctions')}",
        }
    return {
        "pass": True,
        "mac": mac,
        "detail": "No suppression -- cleared or never applied",
    }


# ---------------------------------------------------------------------------
# Sticky MAC enforcement
# ---------------------------------------------------------------------------

def verify_sticky_mac(
    mac_table_output: str,
    mac: str,
    expected_local: bool = True,
) -> Dict[str, Any]:
    """
    Sticky MAC: must remain local, must be marked sticky.
    If expected_local=True, fail if source is not local.
    """
    mac_l = mac.lower()
    entries = parse_evpn_mac_entries(mac_table_output)
    for e in entries:
        if e["mac"] == mac_l:
            is_sticky = e.get("sticky", "false") == "true"
            is_local = e["source_hint"] == "local"
            if not is_sticky:
                return {"pass": False, "mac": mac_l, "detail": "Not marked as sticky", "line": e["line"]}
            if expected_local and not is_local:
                return {"pass": False, "mac": mac_l, "detail": "Sticky MAC moved from local", "line": e["line"]}
            return {"pass": True, "mac": mac_l, "detail": "Sticky MAC enforced", "line": e["line"]}
    return {"pass": False, "mac": mac_l, "detail": "MAC not found"}


def verify_sticky_rejects_remote_move(
    before_output: str,
    after_move_attempt_output: str,
    sticky_mac: str,
) -> Dict[str, Any]:
    """
    After attempting to move a sticky MAC via remote/PW, it must remain local.
    Per SW-194578 matrix: moves from PW/EVPN to sticky AC are ignored.
    """
    before = verify_mac_source(before_output, sticky_mac, ["local"])
    after = verify_mac_source(after_move_attempt_output, sticky_mac, ["local"])

    if before["pass"] and after["pass"]:
        return {
            "pass": True,
            "mac": sticky_mac,
            "detail": "Sticky MAC stayed local despite remote move attempt",
        }
    if not before["pass"]:
        return {
            "pass": False,
            "mac": sticky_mac,
            "detail": f"MAC was not local before move attempt: {before.get('source_hint')}",
        }
    return {
        "pass": False,
        "mac": sticky_mac,
        "detail": f"Sticky MAC moved to {after.get('source_hint')} -- enforcement failed",
    }


# ---------------------------------------------------------------------------
# Aging timer verification
# ---------------------------------------------------------------------------

def verify_mac_aged_out(
    mac_table_output: str,
    mac: str,
) -> Dict[str, Any]:
    """After aging timer expires, MAC should NOT be in the table."""
    result = verify_mac_present(mac_table_output, mac)
    if result["pass"]:
        return {"pass": False, "mac": mac, "detail": "MAC still present -- did not age out"}
    return {"pass": True, "mac": mac, "detail": "MAC aged out (not found)"}


def verify_static_mac_not_aged(
    mac_table_output: str,
    mac: str,
) -> Dict[str, Any]:
    """Static/sticky MACs must NOT age out."""
    result = verify_mac_present(mac_table_output, mac)
    if not result["pass"]:
        return {"pass": False, "mac": mac, "detail": "Static MAC disappeared -- should not age"}
    return {"pass": True, "mac": mac, "detail": "Static MAC present (did not age)"}


def wait_and_verify_aging(
    device: str,
    evpn_name: str,
    mac: str,
    aging_sec: int,
    run_show: RunShowFn,
    poll_interval: int = 10,
) -> Dict[str, Any]:
    """
    Wait for aging_sec + margin, then check if MAC disappeared.
    Returns timing info for convergence measurement.
    """
    margin = max(5, aging_sec // 4)
    total_wait = aging_sec + margin
    elapsed = 0

    while elapsed < total_wait:
        wait = min(poll_interval, total_wait - elapsed)
        time.sleep(wait)
        elapsed += wait
        output = run_show(device, f"show evpn mac-table instance {evpn_name} mac {mac} | no-more")
        if mac.lower() not in strip_ansi(output).lower():
            return {
                "pass": True,
                "mac": mac,
                "aged_after_sec": elapsed,
                "expected_sec": aging_sec,
                "detail": f"MAC aged out after {elapsed}s (expected {aging_sec}s)",
            }

    output = run_show(device, f"show evpn mac-table instance {evpn_name} mac {mac} | no-more")
    still_present = mac.lower() in strip_ansi(output).lower()
    return {
        "pass": not still_present,
        "mac": mac,
        "aged_after_sec": elapsed if not still_present else None,
        "expected_sec": aging_sec,
        "detail": "MAC did not age out within expected window" if still_present else f"Aged after ~{elapsed}s",
    }


# ---------------------------------------------------------------------------
# HA recovery checks
# ---------------------------------------------------------------------------

def verify_mac_table_recovered(
    before_count: int,
    after_output: str,
    tolerance_pct: float = 5.0,
) -> Dict[str, Any]:
    """After HA event, MAC count should recover to within tolerance of pre-event count."""
    after_count = parse_evpn_mac_count(after_output)
    lower = int(before_count * (1 - tolerance_pct / 100))
    ok = after_count >= lower
    return {
        "pass": ok,
        "before": before_count,
        "after": after_count,
        "delta": after_count - before_count,
        "detail": f"Recovered {after_count}/{before_count} MACs" + (" (within tolerance)" if ok else " (LOSS)"),
    }


def poll_mac_recovery(
    device: str,
    evpn_name: str,
    expected_count: int,
    timeout_sec: int,
    run_show: RunShowFn,
    poll_interval: int = 10,
    tolerance_pct: float = 5.0,
) -> Dict[str, Any]:
    """
    Poll MAC table until count recovers to expected (within tolerance) or timeout.
    Returns convergence time.
    """
    lower = int(expected_count * (1 - tolerance_pct / 100))
    elapsed = 0
    last_count = 0

    while elapsed < timeout_sec:
        time.sleep(poll_interval)
        elapsed += poll_interval
        output = run_show(device, f"show evpn mac-table instance {evpn_name} | no-more")
        last_count = parse_evpn_mac_count(output)
        if last_count >= lower:
            return {
                "pass": True,
                "convergence_sec": elapsed,
                "final_count": last_count,
                "expected": expected_count,
                "detail": f"Recovered to {last_count} in {elapsed}s",
            }

    return {
        "pass": False,
        "convergence_sec": None,
        "final_count": last_count,
        "expected": expected_count,
        "detail": f"Timeout {timeout_sec}s: only {last_count}/{expected_count} MACs recovered",
    }


# ---------------------------------------------------------------------------
# Spirent traffic loss check
# ---------------------------------------------------------------------------

def verify_spirent_no_loss(stats_json: Dict[str, Any], threshold_pct: float = 0.01) -> Dict[str, Any]:
    """Check Spirent stats for traffic loss during MAC move."""
    tx = stats_json.get("tx_frames", 0)
    rx = stats_json.get("rx_frames", 0)
    if tx == 0:
        return {"pass": False, "detail": "No TX frames -- Spirent not sending"}
    loss = tx - rx
    loss_pct = (loss / tx) * 100 if tx > 0 else 0
    ok = loss_pct <= threshold_pct
    return {
        "pass": ok,
        "tx": tx,
        "rx": rx,
        "loss": loss,
        "loss_pct": round(loss_pct, 4),
        "detail": f"Loss {loss_pct:.4f}% ({loss} frames)" + (" <= threshold" if ok else " > threshold"),
    }


# ---------------------------------------------------------------------------
# A2: Deep MAC flag verification (detail output)
# ---------------------------------------------------------------------------

def verify_mac_flags(
    detail_output: str,
    mac: str,
    expected_flags: Optional[List[str]] = None,
    forbidden_flags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Check MAC flags from 'show evpn mac-table detail instance <name>'.

    expected_flags: flags that MUST be present (e.g. ["L", "K"] for local+sticky)
    forbidden_flags: flags that MUST NOT be present (e.g. ["F", "D"] for not frozen/dup)
    """
    mac_l = mac.lower()
    entries = parse_mac_detail(detail_output)
    for e in entries:
        if e.mac == mac_l:
            missing = [f for f in (expected_flags or []) if f not in e.flags]
            present_forbidden = [f for f in (forbidden_flags or []) if f in e.flags]
            ok = not missing and not present_forbidden
            return {
                "pass": ok,
                "mac": mac_l,
                "flags": e.flags,
                "sequence": e.sequence,
                "source": e.source,
                "missing_expected": missing,
                "present_forbidden": present_forbidden,
                "detail": (
                    f"Flags {e.flags}"
                    + (f", missing {missing}" if missing else "")
                    + (f", forbidden {present_forbidden}" if present_forbidden else "")
                ),
            }
    return {"pass": False, "mac": mac_l, "detail": "MAC not found in detail output"}


def verify_forwarding_state(
    fwd_table_output: str,
    mac: str,
    expected_state: str = "forwarding",
) -> Dict[str, Any]:
    """Verify NCP forwarding state from 'show evpn forwarding-table mac-address-table'."""
    mac_l = mac.lower()
    entries = parse_forwarding_table_flags(fwd_table_output)
    for e in entries:
        if e.mac == mac_l:
            ok = e.fwd_state == expected_state
            return {
                "pass": ok,
                "mac": mac_l,
                "fwd_state": e.fwd_state,
                "expected": expected_state,
                "ncp_flags": e.flags,
                "ncp_id": e.ncp_id,
                "detail": f"NCP state: {e.fwd_state} (expected {expected_state})",
            }
    return {"pass": False, "mac": mac_l, "detail": "MAC not found in forwarding table"}


def verify_mac_detail_sequence(
    detail_output: str,
    mac: str,
) -> Optional[int]:
    """Extract sequence number from detail output (more reliable than basic table)."""
    mac_l = mac.lower()
    for e in parse_mac_detail(detail_output):
        if e.mac == mac_l:
            return e.sequence
    return None


def verify_suppress_list(
    suppress_output: str,
    mac: str,
    expect_suppressed: bool = True,
) -> Dict[str, Any]:
    """Verify a MAC appears (or does NOT appear) in the suppress list."""
    mac_l = mac.lower()
    entries = parse_mac_suppress(suppress_output)
    found = [e for e in entries if e.mac == mac_l]

    if expect_suppressed:
        if found:
            e = found[0]
            return {
                "pass": True,
                "mac": mac_l,
                "reason": e.reason,
                "timer": e.timer_remaining,
                "detail": f"Suppressed: reason={e.reason}, timer={e.timer_remaining}",
            }
        return {"pass": False, "mac": mac_l, "detail": "MAC not in suppress list"}
    else:
        if found:
            return {
                "pass": False,
                "mac": mac_l,
                "detail": f"MAC still suppressed: reason={found[0].reason}",
            }
        return {"pass": True, "mac": mac_l, "detail": "MAC not in suppress list (expected)"}


# ---------------------------------------------------------------------------
# B2: Loop prevention verifiers
# ---------------------------------------------------------------------------

def verify_loop_prevention_state(
    lp_output: str,
    mac: str,
    expected_state: str = "suppressed",
) -> Dict[str, Any]:
    """Verify per-MAC loop-prevention state."""
    mac_l = mac.lower()
    entries = parse_loop_prevention_mac_table(lp_output)
    for e in entries:
        if e.mac == mac_l:
            ok = e.state == expected_state
            return {
                "pass": ok,
                "mac": mac_l,
                "state": e.state,
                "expected": expected_state,
                "move_count": e.move_count,
                "restore_timer": e.restore_timer,
                "detail": f"State: {e.state} (expected {expected_state}), moves: {e.move_count}",
            }
    return {"pass": False, "mac": mac_l, "detail": "MAC not in loop-prevention table"}


def verify_loop_count_incremented(
    before_lp_output: str,
    after_lp_output: str,
    interface: str,
) -> Dict[str, Any]:
    """Compare per-interface local-loop counts before/after."""
    before = parse_loop_prevention_interface(before_lp_output)
    after = parse_loop_prevention_interface(after_lp_output)

    iface_l = interface.lower()
    before_cnt = next(
        (e.local_loop_count for e in before if e.interface.lower() == iface_l), None
    )
    after_cnt = next(
        (e.local_loop_count for e in after if e.interface.lower() == iface_l), None
    )

    if before_cnt is None or after_cnt is None:
        return {
            "pass": False,
            "detail": f"Interface {interface} not found. before={before_cnt}, after={after_cnt}",
        }

    ok = after_cnt > before_cnt
    return {
        "pass": ok,
        "interface": interface,
        "before": before_cnt,
        "after": after_cnt,
        "delta": after_cnt - before_cnt,
        "detail": f"Loop count {before_cnt} -> {after_cnt}" + (" (incremented)" if ok else " (NOT incremented)"),
    }


def verify_restore_timer_reset(
    lp_output: str,
    mac: str,
) -> Dict[str, Any]:
    """After 'clear evpn restore-cycles', verify restore timer is reset/absent."""
    mac_l = mac.lower()
    entries = parse_loop_prevention_mac_table(lp_output)
    for e in entries:
        if e.mac == mac_l:
            ok = e.restore_timer is None or e.restore_timer == 0
            return {
                "pass": ok,
                "mac": mac_l,
                "restore_timer": e.restore_timer,
                "state": e.state,
                "detail": f"Restore timer: {e.restore_timer}" + (" (reset)" if ok else " (still active)"),
            }
    return {"pass": True, "mac": mac_l, "detail": "MAC not in LP table (cleared)"}


# ---------------------------------------------------------------------------
# C2: dnos-internal verifiers (mobility counter, ghost, FIB)
# ---------------------------------------------------------------------------

def verify_mobility_counter(
    before_output: str,
    after_output: str,
    expected_increment: int = 1,
) -> Dict[str, Any]:
    """Verify mac-mobility-redis-count increased by expected amount."""
    before = parse_mac_mobility_redis_count(before_output)
    after = parse_mac_mobility_redis_count(after_output)
    delta = after["total_moves"] - before["total_moves"]
    ok = delta >= expected_increment
    return {
        "pass": ok,
        "before": before["total_moves"],
        "after": after["total_moves"],
        "delta": delta,
        "expected_increment": expected_increment,
        "local_delta": after["local_moves"] - before["local_moves"],
        "remote_delta": after["remote_moves"] - before["remote_moves"],
        "detail": f"Mobility counter {before['total_moves']} -> {after['total_moves']} (delta {delta})",
    }


def verify_no_ghost_macs(
    ghost_output: str,
) -> Dict[str, Any]:
    """Verify no ghost MACs exist (clean state)."""
    ghosts = parse_ghost_macs(ghost_output)
    ok = len(ghosts) == 0
    return {
        "pass": ok,
        "ghost_count": len(ghosts),
        "ghost_macs": ghosts[:10],
        "detail": "No ghost MACs" if ok else f"{len(ghosts)} ghost MAC(s): {', '.join(ghosts[:5])}",
    }


def verify_fib_mac_state(
    fib_output: str,
    mac: str,
    expected_state: str = "programmed",
) -> Dict[str, Any]:
    """Verify FIB programming state for a MAC."""
    mac_l = mac.lower()
    entries = parse_fib_evpn_mac(fib_output)
    for e in entries:
        if e.mac == mac_l:
            ok = e.fib_state == expected_state
            return {
                "pass": ok,
                "mac": mac_l,
                "fib_state": e.fib_state,
                "expected": expected_state,
                "interface": e.interface,
                "detail": f"FIB state: {e.fib_state} (expected {expected_state})",
            }
    return {"pass": False, "mac": mac_l, "detail": "MAC not found in FIB database"}


# ---------------------------------------------------------------------------
# C3: Spirent-DUT cross-reference
# ---------------------------------------------------------------------------

def verify_spirent_dut_crossref(
    spirent_stats: Dict[str, Any],
    dut_mac_output: str,
    evpn_name: str = "",
) -> Dict[str, Any]:
    """Cross-reference Spirent TX/RX counts with DUT MAC table entries.

    Compares the number of unique MACs Spirent claims to have sent against
    the number of MACs appearing in the DUT's mac-table.
    """
    spirent_mac_count = spirent_stats.get("tx_mac_count", 0) or spirent_stats.get("unique_macs", 0)
    dut_entries = parse_evpn_mac_entries(dut_mac_output)
    dut_mac_count = len(dut_entries)

    if spirent_mac_count == 0:
        return {
            "pass": True,
            "matched": True,
            "spirent_macs": 0,
            "dut_macs": dut_mac_count,
            "detail": "No Spirent MACs to cross-reference",
        }

    match_pct = (dut_mac_count / spirent_mac_count * 100) if spirent_mac_count > 0 else 0
    ok = match_pct >= 90

    return {
        "pass": ok,
        "matched": ok,
        "spirent_macs": spirent_mac_count,
        "dut_macs": dut_mac_count,
        "match_pct": round(match_pct, 1),
        "detail": (f"Spirent sent {spirent_mac_count} MACs, DUT has {dut_mac_count} "
                   f"({match_pct:.1f}% match, threshold 90%)"),
    }


# ---------------------------------------------------------------------------
# C4: BGP health monitoring during poll loops
# ---------------------------------------------------------------------------

def check_bgp_health_during_poll(
    bgp_summary_output: str,
) -> Dict[str, Any]:
    """Check BGP L2VPN EVPN health from summary output.

    Returns state info for use during continuous polling loops.
    """
    summary = parse_bgp_l2vpn_evpn_summary(bgp_summary_output)
    established_count = summary.get("established_count", 0)
    total_peers = summary.get("total_peers", 0)
    peers = summary.get("peers", [])

    non_established = [p for p in peers if p.get("state") != "Established"]

    all_established = established_count > 0 and not non_established
    state = "healthy" if all_established else "degraded"

    return {
        "pass": all_established,
        "state": state,
        "established_count": established_count,
        "total_peers": total_peers,
        "non_established": [
            {"peer": p.get("peer", "?"), "state": p.get("state", "?")}
            for p in non_established[:5]
        ],
        "detail": (f"BGP L2VPN EVPN: {established_count}/{total_peers} peers Established"
                   if total_peers > 0 else "No BGP EVPN peers found"),
    }
