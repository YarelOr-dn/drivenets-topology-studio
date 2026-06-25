#!/usr/bin/env python3
"""
Verification helpers for MAC mobility outcomes.

Covers: presence, source, sequence, suppression, sticky, aging,
count comparison, and HA recovery checks.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from .mac_parsers import (
    parse_bgp_l2vpn_evpn_summary,
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
from .validators import poll_until

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
    expected_normalized = []
    peer_expectations = []
    for expected in expected_sources:
        value = str(expected).strip().lower()
        if not value:
            continue
        if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", value):
            peer_expectations.append(value)
            continue
        expected_normalized.append(value)
        if value == "l>":
            expected_normalized.extend(["local", "ac", "l"])
        elif value == "b>":
            expected_normalized.extend(["bgp", "evpn", "remote", "b"])
        elif value == "v>":
            expected_normalized.extend(["pw", "vpls", "pseudo", "v"])
    if not expected_normalized and expected_sources:
        expected_normalized = [str(e).strip().lower() for e in expected_sources if str(e).strip()]

    text_l = strip_ansi(mac_table_output).lower()
    entries = parse_evpn_mac_entries(mac_table_output)
    for e in entries:
        if e["mac"] == mac_l:
            hint = e["source_hint"]
            aliases = [str(a).lower() for a in e.get("source_aliases", [hint])]
            source_ok = any(a in expected_normalized for a in aliases) or (
                "unknown" in expected_normalized and hint == "unknown"
            )
            peer_ok = all(peer in text_l for peer in peer_expectations)
            ok = source_ok and peer_ok
            return {
                "pass": ok,
                "mac": mac_l,
                "source_hint": hint,
                "source_aliases": aliases,
                "expected": expected_sources,
                "expected_normalized": expected_normalized,
                "peer_expectations": peer_expectations,
                "line": e["line"],
            }
    return {"pass": False, "mac": mac_l, "detail": "no matching entry"}


def verify_mac_per_view(mac: str, views: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Verify one MAC across recipe-defined present/absent show-command views."""
    mac_l = mac.lower()
    results: List[Dict[str, Any]] = []
    for view in views:
        name = str(view.get("name") or view.get("command") or "view")
        expect = str(view.get("expect") or "present").lower()
        output = strip_ansi(str(view.get("output") or ""))
        present = mac_l in output.lower()
        should_be_present = expect != "absent"
        ok = present == should_be_present
        results.append({
            "name": name,
            "expect": expect,
            "present": present,
            "pass": ok,
        })
    failed = [r for r in results if not r["pass"]]
    return {
        "pass": not failed,
        "mac": mac_l,
        "results": results,
        "detail": (
            "all views matched"
            if not failed else
            "; ".join(f"{r['name']} expected {r['expect']} present={r['present']}" for r in failed)
        ),
    }


def parse_evi_moved_events(detail_output: str) -> int:
    """Extract `Number of moved events` from `show evpn instance ... detail`."""
    text = strip_ansi(detail_output)
    match = re.search(r"Number\s+of\s+moved\s+events\s*:\s*(\d+)", text, re.IGNORECASE)
    return int(match.group(1)) if match else 0


def verify_evi_moved_events_increment(
    before_output: str,
    after_output: str,
    expected_min_increment: int = 1,
) -> Dict[str, Any]:
    """Verify the EVI moved-events counter increased by the requested amount."""
    before = parse_evi_moved_events(before_output)
    after = parse_evi_moved_events(after_output)
    delta = after - before
    ok = delta >= expected_min_increment
    return {
        "pass": ok,
        "before": before,
        "after": after,
        "delta": delta,
        "expected_min_increment": expected_min_increment,
        "detail": f"moved_events {before} -> {after} (delta {delta}, expected >= {expected_min_increment})",
    }


def compare_mac_count(before: str, after: str) -> Dict[str, Any]:
    b = parse_evpn_mac_count(before)
    a = parse_evpn_mac_count(after)
    return {"before": b, "after": a, "delta": a - b}


# NOTE: previous helper `first_mac_from_output` was removed in PR7d
# (2026-04-14). It was a one-line wrapper around `extract_first_mac`; the
# orchestrator and other helpers already import `extract_first_mac` directly
# from `shared.mac_parsers`.


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
            s = e.get("sequence")
            seq_before = s if s is not None else extract_sequence_number(e["line"])
            break
    for e in after_entries:
        if e["mac"] == mac_l:
            s = e.get("sequence")
            seq_after = s if s is not None else extract_sequence_number(e["line"])
            break

    if seq_before is None and seq_after is not None:
        return {
            "pass": True,
            "seq_before": None,
            "seq_after": seq_after,
            "detail": f"seq None -> {seq_after} (initial learning, MAC not present before move)",
        }

    if seq_before is None and seq_after is None:
        mac_present_after = any(e["mac"] == mac_l for e in after_entries)
        if mac_present_after:
            return {
                "pass": True,
                "detail": "Sequence not available in CLI (DNOS version limitation). MAC present after move.",
                "seq_before": None,
                "seq_after": None,
                "warn": "sequence_not_exposed",
            }
        return {
            "pass": False,
            "detail": "Could not parse sequence and MAC not found after move",
            "seq_before": None,
            "seq_after": None,
        }

    if seq_after is None:
        return {
            "pass": False,
            "detail": f"Could not parse sequence: before={seq_before}, after={seq_after}",
            "seq_before": seq_before,
            "seq_after": seq_after,
        }

    if seq_before is None:
        seq_before = 0

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


# NOTE: `verify_suppression_cleared` was removed in PR7d (2026-04-14). Call
# sites should invert `verify_suppression_active` directly when needed -- the
# wrapper added no behaviour.


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


# NOTE: `verify_sticky_rejects_remote_move`, `verify_mac_aged_out`,
# `verify_static_mac_not_aged`, and `wait_and_verify_aging` were removed in
# PR7d (2026-04-14). They had no callers -- aging-related scenarios run
# through the shared `wait_for_mac_absent` validator (in
# `shared/validators.py`) and the orchestrator's per-scenario verify phase,
# both of which already cover the same checks without duplicate wrappers.


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
    Returns convergence time. Uses the shared `poll_until` validator -- exits
    the moment the count threshold is met instead of always sleeping the full
    `poll_interval`.
    """
    lower = int(expected_count * (1 - tolerance_pct / 100))
    cmd = f"show evpn mac-table instance {evpn_name} | no-more"

    def _recovered() -> Tuple[bool, Any]:
        out = run_show(device, cmd)
        cnt = parse_evpn_mac_count(out)
        return (cnt >= lower), {"count": cnt, "lower_bound": lower}

    val = poll_until(
        _recovered,
        timeout_sec=float(timeout_sec),
        interval_sec=float(poll_interval),
        progress_label=f"MAC count >= {lower} on {evpn_name}",
    )

    last_count = 0
    if isinstance(val.last_value, dict):
        last_count = int(val.last_value.get("count") or 0)

    if val.passed:
        return {
            "pass": True,
            "convergence_sec": round(val.elapsed_sec, 1),
            "final_count": last_count,
            "expected": expected_count,
            "polls": val.attempts,
            "detail": (
                f"Recovered to {last_count} (>= {lower}) in "
                f"{val.elapsed_sec:.1f}s ({val.attempts} polls)"
            ),
        }

    return {
        "pass": False,
        "convergence_sec": None,
        "final_count": last_count,
        "expected": expected_count,
        "polls": val.attempts,
        "detail": (
            f"Timeout {timeout_sec}s: only {last_count}/{expected_count} MACs "
            f"recovered after {val.attempts} polls"
        ),
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
    absent_is_pass: bool = False,
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
    return {
        "pass": bool(absent_is_pass),
        "mac": mac_l,
        "detail": "MAC not found in detail output",
    }


def verify_forwarding_state(
    fwd_table_output: str,
    mac: str,
    expected_state: str = "forwarding",
    absent_is_pass: bool = False,
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
    return {
        "pass": bool(absent_is_pass),
        "mac": mac_l,
        "detail": "MAC not found in forwarding table",
    }


# NOTE: `verify_mac_detail_sequence` was removed in PR7d (2026-04-14). The
# mainline `verify_sequence_incremented` already pulls the sequence number
# from `parse_mac_detail` via `parse_evpn_mac_entries` -- no caller needed
# the standalone single-MAC accessor.


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
    established_count = summary.get("established", 0)
    total_peers = summary.get("total", 0)
    peers = summary.get("neighbors", [])

    non_established = [p for p in peers if not p.get("established")]

    all_established = established_count > 0 and not non_established
    state = "healthy" if all_established else "degraded"

    return {
        "pass": all_established,
        "state": state,
        "established_count": established_count,
        "total_peers": total_peers,
        "non_established": [
            {"peer": p.get("ip", "?"), "state": p.get("state", "?")}
            for p in non_established[:5]
        ],
        "detail": (f"BGP L2VPN EVPN: {established_count}/{total_peers} peers Established"
                   if total_peers > 0 else "No BGP EVPN peers found"),
    }
