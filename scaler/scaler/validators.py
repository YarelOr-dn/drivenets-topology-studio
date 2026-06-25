#!/usr/bin/env python3
"""
scaler.validators -- canonical action+validate primitives library.

Every long-running operation in /TEST orchestration AND /SPIRENT tooling MUST
replace `time.sleep(N)` with a `poll_until(condition, timeout, interval)` call
that returns ASAP when the condition is met and fails fast with a clear
reason on timeout.

Design contract:
  - Each validator returns a `ValidationResult` with `.passed`, `.elapsed_sec`,
    `.attempts`, `.last_value`, `.reason`. Callers should never have to "guess"
    why a wait completed.
  - No fixed sleeps. Every wait is condition-driven.
  - No hardcoded device specifics. Validators take a `run_show(device, cmd)` callable
    and let the caller decide which device to interrogate.
  - Generic `poll_until` accepts ANY zero-arg condition callable, so callers
    that need to poll non-DNOS sources (Spirent STC API, Lab Server health
    checks, file watchers) can compose them without coupling to DNOS.
  - Every validator has a sensible default `interval` and `timeout`, but the caller
    is encouraged to override based on the operation's expected SLA.

Layered consumers:
  - `/TEST` orchestrators (scaler/TEST/catalog/<suite>/shared/validators.py)
    re-export from this module and add suite-specific extensions
    (e.g. `wait_for_mac_in_table` depends on the suite's `mac_parsers.py`).
  - `/SPIRENT` (scaler/SPIRENT/spirent_tool.py) imports `poll_until` and
    composes Spirent-specific conditions (BGP block state, lab health, etc.).

Usage:
    from scaler.validators import poll_until, wait_for_bgp_state

    res = wait_for_bgp_state(run_show, "PE-1", "19.19.19.2",
                             target="ESTABLISHED", timeout_sec=60)
    if not res.passed:
        print(f"BGP did not converge: {res.reason} (last={res.last_value})")
    else:
        print(f"BGP up in {res.elapsed_sec}s after {res.attempts} polls")
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

RunShowFn = Callable[[str, str], str]
ConditionFn = Callable[[], Tuple[bool, Any]]


@dataclass
class ValidationResult:
    """Outcome of a poll-until-condition validator.

    Attributes:
        passed: True if the condition was met before timeout.
        elapsed_sec: Wall-clock seconds spent polling.
        attempts: Number of condition evaluations performed.
        last_value: The most recent observed value (state string, dict, etc.)
            so callers can print useful diagnostics on timeout.
        reason: Human-readable explanation -- "ESTABLISHED in 4.2s" on PASS,
            "still in Active after 60s (last_idle=900s)" on FAIL.
        timeline: Compact list of (elapsed_sec, observed) pairs for evidence.
    """
    passed: bool
    elapsed_sec: float
    attempts: int
    last_value: Any = None
    reason: str = ""
    timeline: List[Tuple[float, Any]] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "elapsed_sec": round(self.elapsed_sec, 2),
            "attempts": self.attempts,
            "last_value": self.last_value,
            "reason": self.reason,
            "timeline_size": len(self.timeline),
        }


def poll_until(
    condition: ConditionFn,
    timeout_sec: float,
    interval_sec: float = 2.0,
    on_progress: Optional[Callable[[float, Any], None]] = None,
    capture_timeline: bool = False,
    progress_every: int = 4,
    progress_label: Optional[str] = None,
) -> ValidationResult:
    """Generic event-driven wait. Returns ASAP when `condition()` returns
    `(True, value)`. Returns FAIL when `timeout_sec` elapses.

    Args:
        condition: Zero-arg callable returning `(bool, observed_value)`.
            The bool is the pass/fail decision; observed_value is captured
            verbatim into the result so callers can diagnose on failure.
        timeout_sec: Total budget. Hard cap; we will not exceed by more than
            one `interval_sec`.
        interval_sec: Sleep between condition evaluations. Smaller = faster
            wake-up but more device load. 2.0s is a reasonable default for
            DNOS show commands.
        on_progress: Optional callback invoked every `progress_every` polls
            with `(elapsed_sec, last_value)`. Use this to emit log lines
            like `"  ... still polling (12s, last_state=Active)"`.
        capture_timeline: If True, store every (elapsed, observed) pair.
            Off by default to keep the result small.
        progress_every: How often to invoke `on_progress` (every Nth poll).
        progress_label: Optional label used by the default auto-progress
            printer when `on_progress` is None. Lets callers get
            `[label] still polling (12s, last=...)` lines for free without
            writing a callback. Pass None to suppress auto-progress.

    Returns:
        ValidationResult.
    """
    t0 = time.time()
    attempts = 0
    last_value: Any = None
    timeline: List[Tuple[float, Any]] = []
    deadline = t0 + max(0.001, timeout_sec)

    if on_progress is None and progress_label:
        _label = progress_label

        def _auto(elapsed: float, observed: Any) -> None:
            print(f"    [{_label}] still polling ({elapsed:.0f}s elapsed, "
                  f"last={_truncate_repr(observed)})", flush=True)
        on_progress_eff: Optional[Callable[[float, Any], None]] = _auto
    else:
        on_progress_eff = on_progress

    while True:
        attempts += 1
        try:
            ok, observed = condition()
        except Exception as exc:
            observed = f"[ERROR] {exc.__class__.__name__}: {exc}"
            ok = False
        last_value = observed
        elapsed = time.time() - t0
        if capture_timeline:
            timeline.append((round(elapsed, 2), observed))
        if ok:
            return ValidationResult(
                passed=True,
                elapsed_sec=elapsed,
                attempts=attempts,
                last_value=observed,
                reason=f"condition met in {elapsed:.1f}s after {attempts} poll(s)",
                timeline=timeline,
            )

        if on_progress_eff is not None and attempts % max(1, progress_every) == 0:
            try:
                on_progress_eff(elapsed, observed)
            except Exception:
                pass

        if time.time() >= deadline:
            return ValidationResult(
                passed=False,
                elapsed_sec=elapsed,
                attempts=attempts,
                last_value=observed,
                reason=f"timeout after {elapsed:.1f}s ({attempts} poll(s)) -- "
                       f"last observed: {observed!r}",
                timeline=timeline,
            )
        remaining = deadline - time.time()
        time.sleep(max(0.05, min(interval_sec, remaining)))


def _truncate_repr(value: Any, limit: int = 80) -> str:
    """Compact one-line repr for progress output."""
    try:
        s = repr(value)
    except Exception:
        s = "<unrepr-able>"
    if len(s) > limit:
        s = s[: limit - 3] + "..."
    return s


# ---------------------------------------------------------------------------
# DNOS-aware validators (no hardcoded device assumptions -- caller passes
# `run_show` and `device` so the same validators work on PE-1, PE-4, R7-Natan,
# RR-SA-2, etc.)
# ---------------------------------------------------------------------------

_GOOD_BGP_STATES = {"established"}
_BAD_BGP_STATES = {
    "idle", "connect", "active", "opensent", "openconfirm",
    "never", "down",
}


def _normalize_bgp_state(token: str) -> str:
    """Map summary-line token to a normalized state.

    DNOS prints the FSM state for non-ESTABLISHED peers (Idle / Connect / Active /
    OpenSent / OpenConfirm) and a numeric prefix count for ESTABLISHED peers.
    Returns: "established" | "<lowercased FSM state>" | "?".
    """
    t = token.strip().lower()
    if not t:
        return "?"
    if t.isdigit():
        return "established"
    return t


def _parse_bgp_summary_for_neighbor(
    summary_text: str,
    neighbor: str,
) -> Tuple[str, Dict[str, Any]]:
    """Find the line matching `neighbor` in a `show bgp ... summary` table.

    Returns `(normalized_state, line_fields)`. If the neighbor is not present,
    returns `("?", {})`.
    """
    for line in summary_text.splitlines():
        line = line.rstrip()
        if not line or line.lstrip().startswith(("BGP", "Neighbor", "Total",
                                                 "  Neighbor")):
            continue
        cols = line.split()
        if not cols or neighbor not in cols:
            continue
        if cols[0] != neighbor:
            continue
        state = _normalize_bgp_state(cols[-1])
        return state, {"raw": line, "cols": cols, "state": state}
    return "?", {}


def wait_for_bgp_state(
    run_show: RunShowFn,
    device: str,
    neighbor: str,
    target: str = "ESTABLISHED",
    afi: str = "l2vpn evpn",
    timeout_sec: float = 60.0,
    interval_sec: float = 3.0,
    on_progress: Optional[Callable[[float, Any], None]] = None,
) -> ValidationResult:
    """Poll until a BGP neighbor reaches `target` state (default ESTABLISHED).

    Device-agnostic: caller supplies `run_show(device, cmd)` and the AFI
    namespace ('l2vpn evpn', 'ipv4 unicast', 'ipv4 flowspec', etc.).

    Reaches PASS as soon as the summary line for `neighbor` shows the target
    state. Reaches FAIL on timeout; returns the last observed FSM state so
    the caller can decide whether to retry, abort, or escalate.
    """
    target_norm = target.strip().lower()
    cmd = f"show bgp {afi} summary | no-more"

    def _check() -> Tuple[bool, Any]:
        out = run_show(device, cmd)
        state, fields = _parse_bgp_summary_for_neighbor(out, neighbor)
        observed = {"state": state, "neighbor": neighbor}
        if fields:
            observed["raw"] = fields["raw"][:160]
        if state == target_norm:
            return True, observed
        return False, observed

    return poll_until(_check, timeout_sec=timeout_sec,
                      interval_sec=interval_sec, on_progress=on_progress)


def wait_for_bgp_state_in(
    run_show: RunShowFn,
    device: str,
    neighbor: str,
    accept_states: List[str],
    afi: str = "l2vpn evpn",
    timeout_sec: float = 60.0,
    interval_sec: float = 3.0,
    on_progress: Optional[Callable[[float, Any], None]] = None,
) -> ValidationResult:
    """Like `wait_for_bgp_state` but accepts ANY of `accept_states`.

    Useful when 'good enough' is not a single state, e.g. transitioning from
    Idle -> Connect -> Active -> OpenSent -> Established and we want to know
    when we're past the Idle stage.
    """
    accept_norm = {s.strip().lower() for s in accept_states}
    cmd = f"show bgp {afi} summary | no-more"

    def _check() -> Tuple[bool, Any]:
        out = run_show(device, cmd)
        state, _ = _parse_bgp_summary_for_neighbor(out, neighbor)
        return (state in accept_norm), {"state": state, "accept": list(accept_norm)}

    return poll_until(_check, timeout_sec=timeout_sec,
                      interval_sec=interval_sec, on_progress=on_progress)


_ARP_LINE_RE = re.compile(
    r"\|\s*([\d\.]+)\s*\|\s*([0-9a-fA-F:]{17}|local|incomplete)\s*\|"
)


def wait_for_arp_resolve(
    run_show: RunShowFn,
    device: str,
    neighbor_ip: str,
    timeout_sec: float = 30.0,
    interval_sec: float = 2.0,
    on_progress: Optional[Callable[[float, Any], None]] = None,
) -> ValidationResult:
    """Poll DUT ARP table until `neighbor_ip` resolves to a real MAC.

    PASS when the ARP entry has a unicast MAC (not 'incomplete', not 'local').
    FAIL on timeout, with the last observed entry text in `last_value` so
    callers can distinguish "no ARP entry at all" vs "ARP entry incomplete".
    """
    cmd = f'show arp | include "{neighbor_ip}"'

    def _check() -> Tuple[bool, Any]:
        out = run_show(device, cmd)
        for ln in out.splitlines():
            if neighbor_ip not in ln:
                continue
            m = _ARP_LINE_RE.search(ln)
            if not m:
                continue
            ip, mac = m.group(1), m.group(2).lower()
            if ip != neighbor_ip:
                continue
            if mac in ("incomplete", "local"):
                return False, {"ip": ip, "mac": mac, "raw": ln.strip()[:160]}
            return True, {"ip": ip, "mac": mac, "raw": ln.strip()[:160]}
        return False, {"ip": neighbor_ip, "mac": "no_entry", "raw": ""}

    return poll_until(_check, timeout_sec=timeout_sec,
                      interval_sec=interval_sec, on_progress=on_progress)


_OPER_RE = re.compile(r"Operational state:\s*(\S+)", re.IGNORECASE)
_ADMIN_RE = re.compile(r"Admin state:\s*(\S+)", re.IGNORECASE)


def wait_for_interface_up(
    run_show: RunShowFn,
    device: str,
    interface: str,
    timeout_sec: float = 15.0,
    interval_sec: float = 2.0,
    on_progress: Optional[Callable[[float, Any], None]] = None,
) -> ValidationResult:
    """Poll until `interface` shows admin=enabled AND operational=up."""
    cmd = f"show interfaces {interface} | no-more"

    def _check() -> Tuple[bool, Any]:
        out = run_show(device, cmd)
        out_lower = out.lower()
        out_upper = out.upper()
        if ("Unknown word" in out) or ("ERROR" in out_upper and "no such" in out_lower):
            return False, {"error": "interface not found", "iface": interface}
        admin_m = _ADMIN_RE.search(out)
        oper_m = _OPER_RE.search(out)
        admin = admin_m.group(1).lower() if admin_m else "?"
        oper = oper_m.group(1).lower() if oper_m else "?"
        observed = {"iface": interface, "admin": admin, "oper": oper}
        if admin in ("enabled", "up") and oper == "up":
            return True, observed
        return False, observed

    return poll_until(_check, timeout_sec=timeout_sec,
                      interval_sec=interval_sec, on_progress=on_progress)


def wait_for_mac_absent(
    run_show: RunShowFn,
    device: str,
    instance: str,
    mac: str,
    timeout_sec: float = 30.0,
    interval_sec: float = 2.0,
    on_progress: Optional[Callable[[float, Any], None]] = None,
) -> ValidationResult:
    """Poll EVPN MAC table until `mac` is NO LONGER in `instance`.

    Used after withdraw / clear / aging operations. Substring check only --
    no MAC parser dependency, so safe to call from any consumer.
    """
    mac_l = mac.lower().replace("-", ":")
    cmd = f"show evpn mac-table instance {instance} | no-more"

    def _check() -> Tuple[bool, Any]:
        out = run_show(device, cmd).lower()
        return (mac_l not in out), {"mac": mac_l, "instance": instance,
                                    "present": (mac_l in out)}

    return poll_until(_check, timeout_sec=timeout_sec,
                      interval_sec=interval_sec, on_progress=on_progress)


_LABEL_POOL_RE = re.compile(
    r"\bbgp-vpls\b\s*[:|]\s*(\d+)\s+labels", re.IGNORECASE
)


def wait_for_evi_label_pool(
    run_show: RunShowFn,
    device: str,
    min_labels: int = 1,
    timeout_sec: float = 30.0,
    interval_sec: float = 3.0,
    on_progress: Optional[Callable[[float, Any], None]] = None,
) -> ValidationResult:
    """Poll until `show mpls label-allocation tables` reports >=min_labels for bgp-vpls.

    Detects the SW-253359 known bug: bgp-vpls label pool stuck at 0.
    """
    cmd = "show mpls label-allocation tables | no-more"

    def _check() -> Tuple[bool, Any]:
        out = run_show(device, cmd)
        m = _LABEL_POOL_RE.search(out)
        observed = {"raw_match": m.group(0) if m else "no bgp-vpls row"}
        if not m:
            return False, observed
        in_use = int(m.group(1))
        observed["in_use"] = in_use
        return (in_use >= min_labels), observed

    return poll_until(_check, timeout_sec=timeout_sec,
                      interval_sec=interval_sec, on_progress=on_progress)


def wait_for_route_in_rib(
    run_show: RunShowFn,
    device: str,
    prefix: str,
    afi: str = "ipv4 unicast",
    timeout_sec: float = 20.0,
    interval_sec: float = 2.0,
    on_progress: Optional[Callable[[float, Any], None]] = None,
) -> ValidationResult:
    """Poll until `prefix` appears in the BGP RIB for the given AFI."""
    cmd = f"show bgp {afi} {prefix} | no-more"

    def _check() -> Tuple[bool, Any]:
        out = run_show(device, cmd)
        present = ("Local Router ID" in out) or ("Best path" in out) or \
                  re.search(rf"\b{re.escape(prefix)}\b", out) is not None
        return present, {"prefix": prefix, "afi": afi, "present": present}

    return poll_until(_check, timeout_sec=timeout_sec,
                      interval_sec=interval_sec, on_progress=on_progress)


def wait_for_pw_installed(
    run_show: RunShowFn,
    device: str,
    instance: Optional[str] = None,
    timeout_sec: float = 60.0,
    interval_sec: float = 3.0,
    on_progress: Optional[Callable[[float, Any], None]] = None,
) -> ValidationResult:
    """Poll until VPLS PW is in 'Installed' state."""
    cmd = (f"show evpn instance {instance} vpls-pw | no-more"
           if instance else "show evpn vpls-pw | no-more")

    def _check() -> Tuple[bool, Any]:
        out = run_show(device, cmd)
        installed = "Installed" in out
        return installed, {"installed": installed, "instance": instance or "all"}

    return poll_until(_check, timeout_sec=timeout_sec,
                      interval_sec=interval_sec, on_progress=on_progress)


# ---------------------------------------------------------------------------
# Compose: pre-condition + action + post-validate. Returns a single dict
# describing the whole operation.
# ---------------------------------------------------------------------------

def action_then_validate(
    name: str,
    action: Callable[[], Any],
    validate: Callable[[], ValidationResult],
    on_action_fail: Optional[Callable[[Any], None]] = None,
) -> Dict[str, Any]:
    """Run an action, then validate its effect. Always returns a dict.

    Use this in orchestrators/recipes when you want the structured
    `{action_result, validation, passed, elapsed_sec}` record per step.

    Args:
        name: Step identifier ('apply_subif', 'spirent_create', etc.).
        action: Zero-arg callable that performs the side effect. Its return
            value is captured into `action_result`. May raise.
        validate: Zero-arg callable returning a ValidationResult. Called
            UNCONDITIONALLY after `action` (even if action raised), so we
            can detect "the action threw but the side effect happened".
        on_action_fail: Optional callback invoked with the action's exception
            for cleanup / logging.

    Returns:
        {
            "name": str, "passed": bool, "elapsed_sec": float,
            "action_result": Any, "action_error": Optional[str],
            "validation": ValidationResult.as_dict(),
            "reason": str,
        }
    """
    t0 = time.time()
    action_result: Any = None
    action_error: Optional[str] = None
    try:
        action_result = action()
    except Exception as exc:
        action_error = f"{exc.__class__.__name__}: {exc}"
        if on_action_fail is not None:
            try:
                on_action_fail(exc)
            except Exception:
                pass

    val = validate()
    elapsed = time.time() - t0

    if action_error and not val.passed:
        reason = f"action errored ({action_error}) AND validation failed: {val.reason}"
    elif action_error and val.passed:
        reason = (f"action errored ({action_error}) but validation passed -- "
                  f"side effect succeeded anyway: {val.reason}")
    else:
        reason = val.reason

    return {
        "name": name,
        "passed": val.passed,
        "elapsed_sec": round(elapsed, 2),
        "action_result": action_result,
        "action_error": action_error,
        "validation": val.as_dict(),
        "reason": reason,
    }


__all__ = [
    "ValidationResult",
    "ConditionFn",
    "RunShowFn",
    "poll_until",
    "wait_for_bgp_state",
    "wait_for_bgp_state_in",
    "wait_for_arp_resolve",
    "wait_for_interface_up",
    "wait_for_mac_absent",
    "wait_for_evi_label_pool",
    "wait_for_route_in_rib",
    "wait_for_pw_installed",
    "action_then_validate",
]
