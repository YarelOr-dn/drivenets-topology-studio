#!/usr/bin/env python3
"""
MAC move trigger execution for EVPN MAC mobility tests (SW-204115).

Three automation tiers:
  1. SPIRENT -- EmulatedDevice with protocol-start (ARP/GARP) for MAC learning
  2. MCP_SHOW -- run_show_command to clear/manipulate MACs on the DUT directly
  3. MANUAL  -- print operator steps and wait

MAC learning strategy (validated on PE-1 2026-03-27):
  L2 streams alone are unreliable for Q-in-Q MAC learning. EmulatedDevice
  protocol-start (ARP/GARP) is the reliable method. Sequence for a move:
    1. Create EmulatedDevice on AC1 with MAC X, protocol-start -> learned
    2. Protocol-stop, remove device
    3. Create EmulatedDevice on AC2 with same MAC X, protocol-start -> MOVE
  This ensures only one device exists at a time, giving deterministic control.

Spirent tool path is resolved by ``shared.spirent_paths`` -- see PR6.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
import time
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .validators import (
    wait_for_mac_absent,
    wait_for_mac_in_table,
)
from .spirent_paths import (
    spirent_tool_available,
    spirent_tool_command,
    spirent_tool_path,
)

logger = logging.getLogger("mac_trigger")


def _spirent_tool() -> Path:
    """Resolved spirent_tool.py path (kept as a function so env overrides apply)."""
    return spirent_tool_path()


# Backwards-compatible alias used by older code paths and external scripts
# that imported ``SPIRENT_TOOL`` directly from this module.
SPIRENT_TOOL = _spirent_tool()

RunShowFn = Callable[[str, str], str]

_SPIRENT_SESSION_HEALTHY = True
_SPIRENT_FAIL_COUNT = 0
_MAX_CONSECUTIVE_FAILS = 3

# Optional shared watchdog (e2e_lite.SpirentWatchdog) installed by the
# scenario_runner. When set, `_run_spirent` delegates to it for healing +
# retry. Legacy callers without a watchdog still get the built-in retry.
_SHARED_WATCHDOG: Optional["Any"] = None  # type: ignore[assignment]


def set_shared_watchdog(watchdog: Optional[Any]) -> None:
    """Install (or clear) a shared SpirentWatchdog for this process.

    Called by the scenario_runner / orchestrator. If set, every call to
    `_run_spirent` will go through `watchdog.guarded_run()` so FSM-aware
    heal + retry replaces the embedded retry loop.
    """
    global _SHARED_WATCHDOG
    _SHARED_WATCHDOG = watchdog


def get_shared_watchdog() -> Optional[Any]:
    return _SHARED_WATCHDOG


# Module-level device poller -- set by orchestrator before running triggers.
# Allows trigger functions to poll the DUT MAC table via persistent SSH
# instead of using fixed time.sleep() calls.
_device_poll_fn: Optional[RunShowFn] = None
_device_poll_target: str = ""
_device_poll_evpn: str = ""

# DUT interface MAC cache -- avoids broadcast dst-mac that triggers DNAAS LLP.
_dut_interface_mac: str = ""


def set_dut_mac(mac: str) -> None:
    """Set the DUT interface MAC for unicast stream destinations."""
    global _dut_interface_mac
    _dut_interface_mac = mac.lower().strip()


def _get_dut_mac_for_stream() -> str:
    """Return cached DUT MAC, or empty string if not set."""
    return _dut_interface_mac


def set_device_poller(
    run_show: RunShowFn,
    device: str,
    evpn_name: str,
) -> None:
    """Set the module-level device poller. Called once by the orchestrator."""
    global _device_poll_fn, _device_poll_target, _device_poll_evpn
    _device_poll_fn = run_show
    _device_poll_target = device
    _device_poll_evpn = evpn_name


def poll_until_mac_present(
    mac: str,
    timeout: float = 8.0,
    poll_interval: float = 0.5,
    evpn_name: str = "",
    fallback_sleep: float = 2.0,
) -> float:
    """Poll DUT MAC table until *mac* appears.

    Return-value contract (used by orchestrator to distinguish PASS from TIMEOUT):
      *  ``> 0``  --> MAC observed; value is wall-clock seconds spent polling.
      *  ``== 0`` --> reserved (never returned by this function).
      *  ``< 0``  --> EITHER the device poller is not configured (returned
        ``-fallback_sleep``) OR the MAC never appeared before ``timeout``
        elapsed (returned ``-elapsed_sec``).  Use ``abs(val)`` for elapsed
        time and ``val > 0`` to check for verified presence.

    Delegates to shared ``wait_for_mac_in_table`` validator -- no fixed sleeps
    in the poll loop, exits the moment the MAC is observed.
    """
    inst = evpn_name or _device_poll_evpn
    if not _device_poll_fn or not _device_poll_target or not inst:
        logger.warning(
            "[poll] device poller not configured -- sleeping %.1fs without MAC verification",
            fallback_sleep,
        )
        time.sleep(fallback_sleep)
        return -fallback_sleep

    val = wait_for_mac_in_table(
        _device_poll_fn, _device_poll_target, inst, mac,
        timeout_sec=float(timeout),
        interval_sec=float(poll_interval),
    )
    elapsed = round(val.elapsed_sec, 3)
    if not val.passed:
        # Surface failure with a tag so log greps catch unverified MACs.
        logger.warning(
            "[poll] MAC %s not present after %.1fs (instance=%s)",
            mac, elapsed, inst,
        )
        return -elapsed if elapsed > 0 else -timeout
    return elapsed


def poll_until_mac_absent(
    mac: str,
    timeout: float = 15.0,
    poll_interval: float = 1.0,
    evpn_name: str = "",
    fallback_sleep: float = 5.0,
) -> float:
    """Poll DUT MAC table until *mac* disappears.

    Return-value contract (mirror of ``poll_until_mac_present``):
      *  ``> 0``  --> MAC absent; value is wall-clock seconds spent polling.
      *  ``< 0``  --> EITHER the device poller is not configured (returned
        ``-fallback_sleep``) OR the MAC was still present when ``timeout``
        elapsed (returned ``-elapsed_sec``).
    """
    inst = evpn_name or _device_poll_evpn
    if not _device_poll_fn or not _device_poll_target or not inst:
        logger.warning(
            "[poll] device poller not configured -- sleeping %.1fs without MAC verification",
            fallback_sleep,
        )
        time.sleep(fallback_sleep)
        return -fallback_sleep

    val = wait_for_mac_absent(
        _device_poll_fn, _device_poll_target, inst, mac,
        timeout_sec=float(timeout),
        interval_sec=float(poll_interval),
    )
    elapsed = round(val.elapsed_sec, 3)
    if not val.passed:
        logger.warning(
            "[poll] MAC %s still present after %.1fs (instance=%s)",
            mac, elapsed, inst,
        )
        return -elapsed if elapsed > 0 else -timeout
    return elapsed


class SpirentError(Exception):
    pass


class TrafficMethod(str, Enum):
    SPIRENT = "spirent"
    MCP_SHOW = "mcp_show"
    MANUAL = "manual"


def detect_traffic_methods() -> List[TrafficMethod]:
    methods: List[TrafficMethod] = []
    if spirent_tool_available():
        methods.append(TrafficMethod.SPIRENT)
    if os.environ.get("DNOS_USE_MCP", "").lower() in ("1", "true", "yes"):
        methods.append(TrafficMethod.MCP_SHOW)
    methods.append(TrafficMethod.MANUAL)
    return list(dict.fromkeys(methods))


_MUTATING_COMMANDS = {
    "create-device", "create-stream", "vpls-stream", "remove-device",
    "remove-stream", "protocol-start", "protocol-stop",
    "bgp-peer", "ecmp", "evpn-routes", "add-routes",
}


def _run_spirent(args: List[str], timeout: int = 60, retries: int = 1,
                 raise_on_error: bool = False,
                 return_streams: bool = False) -> Any:
    """Run spirent_tool.py with error detection, retry, and health tracking.

    Mutating commands auto-get retries=2 if the caller did not specify retries.
    On retry, the session is reconnected without destroying infrastructure.

    When an FSM-aware shared watchdog is installed (via `set_shared_watchdog`),
    this function delegates to it for healing + retry instead of the embedded
    retry loop. Legacy callers without a watchdog get the original behavior.

    By default returns ``stdout`` (string). Callers that parse JSON should set
    ``return_streams=True`` to receive a dict ``{"stdout","stderr","rc"}`` so a
    stderr line like ``Warning: ...`` does not corrupt ``json.loads(stdout)``.
    """
    global _SPIRENT_SESSION_HEALTHY, _SPIRENT_FAIL_COUNT

    # Shared-watchdog fast path ------------------------------------------------
    if _SHARED_WATCHDOG is not None:
        try:
            res = _SHARED_WATCHDOG.guarded_run(
                args,
                timeout=timeout,
                retries=retries,
                raise_on_error=raise_on_error,
            )
            if res.ok:
                _SPIRENT_FAIL_COUNT = 0
                _SPIRENT_SESSION_HEALTHY = True
            else:
                _SPIRENT_FAIL_COUNT += 1
                if _SPIRENT_FAIL_COUNT >= _MAX_CONSECUTIVE_FAILS:
                    _SPIRENT_SESSION_HEALTHY = False
            if return_streams:
                return {
                    "stdout": res.stdout,
                    "stderr": res.stderr,
                    "rc": res.rc,
                    "combined": res.combined,
                }
            return res.combined
        except Exception as exc:
            # If the watchdog raises SpirentUnrecoverableError and caller asked
            # to raise, re-raise. Otherwise fall through to legacy path as a
            # last-resort best-effort.
            if raise_on_error:
                raise
            logger.warning("Shared watchdog raised, falling back to legacy retry: %s", exc)

    last_stdout = ""
    last_stderr = ""
    last_rc = -1

    if retries <= 1 and args and args[0] in _MUTATING_COMMANDS:
        retries = 2

    for attempt in range(max(1, retries)):
        try:
            cmd = spirent_tool_command(*args)
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, timeout=timeout,
            )
            last_stdout = proc.stdout or ""
            last_stderr = proc.stderr or ""
            last_rc = proc.returncode
            combined = last_stdout + last_stderr

            if proc.returncode != 0:
                is_session_dead = any(s in combined for s in [
                    "No active session", "Port not reserved",
                    "Stale handles", "Session not found",
                    "Session marked inactive", "Connection refused",
                    "timed out", "HTTPError", "ConnectionError",
                ])
                if is_session_dead and attempt < retries - 1:
                    _try_reconnect()
                    continue
                _SPIRENT_FAIL_COUNT += 1
                if _SPIRENT_FAIL_COUNT >= _MAX_CONSECUTIVE_FAILS:
                    _SPIRENT_SESSION_HEALTHY = False
                if raise_on_error:
                    raise SpirentError(
                        f"spirent_tool.py {' '.join(args[:2])} failed (rc={proc.returncode}): "
                        f"{combined[:300]}"
                    )
                if return_streams:
                    return {"stdout": last_stdout, "stderr": last_stderr,
                            "rc": last_rc, "combined": combined}
                return combined

            _SPIRENT_FAIL_COUNT = 0
            _SPIRENT_SESSION_HEALTHY = True
            if return_streams:
                return {"stdout": last_stdout, "stderr": last_stderr,
                        "rc": last_rc, "combined": combined}
            return combined

        except subprocess.TimeoutExpired:
            _SPIRENT_FAIL_COUNT += 1
            last_stderr = f"TIMEOUT after {timeout}s: {' '.join(args[:3])}"
            last_rc = -1
            if _SPIRENT_FAIL_COUNT >= _MAX_CONSECUTIVE_FAILS:
                _SPIRENT_SESSION_HEALTHY = False

    if raise_on_error:
        raise SpirentError(f"spirent_tool.py failed after {retries} attempts: {last_stderr[:300]}")
    if return_streams:
        return {"stdout": last_stdout, "stderr": last_stderr,
                "rc": last_rc, "combined": last_stdout + last_stderr}
    return last_stdout + last_stderr


def _try_reconnect() -> bool:
    """Attempt to reconnect to Spirent Lab Server WITHOUT destroying the session.

    Previous version ran cleanup --confirm first, which destroyed all devices
    (EVPN_RT2_Peer, VPLS_PW_Peer, etc.). Now we just reconnect to the existing
    session, preserving all devices and BGP peers.
    """
    global _SPIRENT_SESSION_HEALTHY, _SPIRENT_FAIL_COUNT
    try:
        proc = subprocess.run(
            spirent_tool_command("connect"),
            capture_output=True, text=True, timeout=45,
        )
        if proc.returncode == 0:
            proc2 = subprocess.run(
                spirent_tool_command("reserve"),
                capture_output=True, text=True, timeout=30,
            )
            if proc2.returncode == 0:
                _SPIRENT_SESSION_HEALTHY = True
                _SPIRENT_FAIL_COUNT = 0
                return True
    except Exception:
        pass
    return False


def is_spirent_healthy() -> bool:
    return _SPIRENT_SESSION_HEALTHY


def ensure_spirent_ready() -> bool:
    """Verify Spirent session is alive, reconnect if needed."""
    global _SPIRENT_SESSION_HEALTHY, _SPIRENT_FAIL_COUNT
    streams = _run_spirent(["status", "--json"], timeout=15, return_streams=True)
    try:
        status = json.loads(streams.get("stdout", "") if isinstance(streams, dict) else streams)
        sess = status.get("session", {})
        if sess.get("port_reserved") and sess.get("active"):
            _SPIRENT_SESSION_HEALTHY = True
            _SPIRENT_FAIL_COUNT = 0
            return True
    except (json.JSONDecodeError, ValueError):
        pass
    return _try_reconnect()


_SCENARIO_OBJECT_REGISTRY: List[Dict[str, str]] = []

_EXISTING_DEVICES_CACHE: Optional[List[str]] = None
_EXISTING_DEVICES_CACHE_TIME: float = 0.0


def _get_existing_device_names(force_refresh: bool = False) -> List[str]:
    """Query Spirent session for existing device names. Cached for 30s.

    Uses ``spirent_tool.py list-devices --names-only`` (one name per line on
    stdout). The CLI verb is guaranteed by the post-PR1 surface; callers do not
    need to fall back to ``status --json`` parsing any more.
    """
    global _EXISTING_DEVICES_CACHE, _EXISTING_DEVICES_CACHE_TIME
    if (not force_refresh
            and _EXISTING_DEVICES_CACHE is not None
            and (time.time() - _EXISTING_DEVICES_CACHE_TIME) < 30.0):
        return _EXISTING_DEVICES_CACHE

    try:
        proc = subprocess.run(
            spirent_tool_command("list-devices", "--names-only"),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=15,
        )
        if proc.returncode == 0:
            names = [n.strip() for n in (proc.stdout or "").splitlines() if n.strip()]
            _EXISTING_DEVICES_CACHE = names
            _EXISTING_DEVICES_CACHE_TIME = time.time()
            return names
        logger.debug("list-devices --names-only failed (rc=%s): %s",
                     proc.returncode, (proc.stderr or proc.stdout or "")[:200])
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.debug("list-devices --names-only invocation error: %s", exc)

    return []


def _invalidate_device_cache() -> None:
    global _EXISTING_DEVICES_CACHE, _EXISTING_DEVICES_CACHE_TIME
    _EXISTING_DEVICES_CACHE = None
    _EXISTING_DEVICES_CACHE_TIME = 0.0


def _vlan_to_ip(vlan: int, host: int = 10) -> str:
    """Generate a valid IPv4 address from a VLAN number.

    For VLAN <= 255: 10.99.{vlan}.{host}
    For VLAN > 255:  10.{hi_byte}.{lo_byte}.{host} where hi/lo split the 16-bit VLAN.
    """
    if vlan <= 255:
        return f"10.99.{vlan}.{host}"
    hi = (vlan >> 8) & 0xFF
    lo = vlan & 0xFF
    return f"10.{hi}.{lo}.{host}"


def _safe_ip_from_template(template: str, vlan: int) -> str:
    """Replace {vlan} in an IP template, validating the result.

    Falls back to _vlan_to_ip() if the substitution produces an invalid address
    (e.g., VLAN 1000 -> 10.99.1000.10 which has an octet > 255).
    """
    result = template.replace("{vlan}", str(vlan))
    try:
        parts = result.split(".")
        if len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts):
            return result
    except (ValueError, TypeError):
        pass
    host_part = template.rsplit(".", 1)[-1]
    try:
        host = int(host_part) if host_part != "{vlan}" else 10
    except ValueError:
        host = 10
    return _vlan_to_ip(vlan, host)


def _register_spirent_object(name: str, obj_type: str) -> None:
    _SCENARIO_OBJECT_REGISTRY.append({"name": name, "type": obj_type})


def cleanup_current_scenario(destroy: bool = True) -> None:
    """Remove Spirent objects created during the current scenario.

    When destroy=False, only resets the registry without issuing
    remove-device / remove-stream calls.  Use destroy=False when
    pre-created devices and streams should persist across scenarios
    (avoids stc.apply() while protocols are active).
    """
    global _SCENARIO_OBJECT_REGISTRY
    if destroy:
        for obj in reversed(_SCENARIO_OBJECT_REGISTRY):
            if obj["type"] == "stream":
                _run_spirent(["remove-stream", "--name", obj["name"]], timeout=10)
            elif obj["type"] == "device":
                _run_spirent(["remove-device", "--name", obj["name"]], timeout=10)
        _invalidate_device_cache()
    _SCENARIO_OBJECT_REGISTRY = []


def reset_scenario_registry() -> None:
    global _SCENARIO_OBJECT_REGISTRY
    _SCENARIO_OBJECT_REGISTRY = []


# ---------------------------------------------------------------------------
# Spirent L2 device-group helpers
# ---------------------------------------------------------------------------

def spirent_create_mac_block(
    name: str,
    vlan: int,
    mac_count: int,
    base_mac: str = "00:DE:AD:00:01:01",
    base_ip: str = "10.99.{vlan}.10",
    gateway: str = "10.99.{vlan}.1",
    no_qinq: bool = True,
    outer_vlan: Optional[int] = None,
) -> Dict[str, Any]:
    """Create an L2 device block on a VLAN (= one DUT AC).

    When outer_vlan is provided, Q-in-Q tagging is used (outer=DNAAS BD VLAN,
    inner=AC VLAN on DUT).

    DRY check: if a device with this name already exists on the Spirent session,
    remove it first to avoid STC name conflicts (stale devices from prior runs).
    """
    if not is_spirent_healthy():
        if not ensure_spirent_ready():
            return {"name": name, "vlan": vlan, "error": "Spirent session unhealthy"}

    existing = _get_existing_device_names()
    if name in existing:
        logger.info(f"Device '{name}' already exists -- reusing (no recreate)")
        _register_spirent_object(name, "device")
        return {"name": name, "vlan": vlan, "mac_count": mac_count, "reused": True}

    ip = _safe_ip_from_template(base_ip, vlan)
    gw = _safe_ip_from_template(gateway, vlan)

    if outer_vlan is not None:
        args = [
            "create-device",
            "--name", name,
            "--ip", ip,
            "--gateway", gw,
            "--prefix-len", "24",
            "--vlan", str(outer_vlan),
            "--inner-vlan", str(vlan),
            "--mac", base_mac,
            "--mac-step", "00:00:00:00:00:01",
            "--ip-step", "1",
            "--device-count", str(mac_count),
        ]
    else:
        args = [
            "create-device",
            "--name", name,
            "--ip", ip,
            "--gateway", gw,
            "--prefix-len", "24",
            "--vlan", str(vlan),
            "--mac", base_mac,
            "--mac-step", "00:00:00:00:00:01",
            "--ip-step", "1",
            "--device-count", str(mac_count),
        ]
        if no_qinq:
            args.append("--no-qinq")

    output = _run_spirent(args, retries=2)
    _register_spirent_object(name, "device")
    return {
        "name": name,
        "vlan": vlan,
        "mac_count": mac_count,
        "base_mac": base_mac,
        "outer_vlan": outer_vlan,
        "output": output[:2000],
    }


def spirent_create_l2_stream(
    name: str,
    vlan: int,
    src_mac: str = "00:DE:AD:00:01:01",
    dst_mac: Optional[str] = None,
    rate_mbps: int = 1,
    no_qinq: bool = True,
    outer_vlan: Optional[int] = None,
) -> str:
    if not is_spirent_healthy():
        if not ensure_spirent_ready():
            return "Spirent session unhealthy"

    if dst_mac is None:
        dst_mac = _get_dut_mac_for_stream()
    if not dst_mac:
        logger.warning("No DUT MAC for unicast dst -- using broadcast (LLP risk!)")
        dst_mac = "FF:FF:FF:FF:FF:FF"

    # Consult active_test_session.expected_traffic.frame_recipe (populated by
    # prerequisite_engine._check_mcp_dnaas_teach_plan). When the caller is
    # about to inject into the same transport VLAN that the recipe targets
    # AND the encapsulation differs, the override silently corrects vlan/
    # outer_vlan/no_qinq -- catching the bug class where a hardcoded VLAN
    # was sent to a port-mode AC. Cross-test isolation: only overrides when
    # the caller's VLAN matches expected_traffic.vlan; SC01 against PE-1 is
    # untouched if the prereq teach_plan was scoped to PE-4.
    try:
        from .frame_recipe_consumer import apply_frame_recipe_overrides
        override = apply_frame_recipe_overrides(name, vlan, outer_vlan, no_qinq)
        if override.overridden:
            logger.warning(
                "[FRAME-RECIPE] %s -- %s",
                name,
                override.source_note,
            )
        vlan = override.vlan
        outer_vlan = override.outer_vlan
        no_qinq = override.no_qinq
        extra_flags = override.spirent_extra_flags
    except Exception as exc:
        logger.debug("frame_recipe consumer unavailable (%s); legacy path", exc)
        extra_flags = []

    try:
        vlan_int = int(vlan)
    except (TypeError, ValueError):
        vlan_int = 0
    untagged = outer_vlan is None and vlan_int <= 0
    frame_size = "128" if outer_vlan is not None or untagged else "96"

    if outer_vlan is not None:
        args = [
            "create-stream",
            "--protocol", "l2",
            "--vlan", str(outer_vlan),
            "--inner-vlan", str(vlan),
            "--src-mac", src_mac,
            "--dst-mac", dst_mac,
            "--rate-mbps", str(rate_mbps),
            "--frame-size", frame_size,
            "--name", name,
        ]
    elif untagged:
        args = [
            "create-stream",
            "--protocol", "l2",
            "--src-mac", src_mac,
            "--dst-mac", dst_mac,
            "--rate-mbps", str(rate_mbps),
            "--frame-size", frame_size,
            "--name", name,
        ]
        if no_qinq:
            args.append("--no-qinq")
    else:
        args = [
            "create-stream",
            "--protocol", "l2",
            "--vlan", str(vlan_int),
            "--src-mac", src_mac,
            "--dst-mac", dst_mac,
            "--rate-mbps", str(rate_mbps),
            "--frame-size", frame_size,
            "--name", name,
        ]
        if no_qinq:
            args.append("--no-qinq")

    # Append spirent_flags from frame_recipe (deduped vs args already present).
    for flag in extra_flags:
        if flag and flag not in args:
            args.append(flag)

    output = _run_spirent(args, retries=2)
    _register_spirent_object(name, "stream")
    return output


def spirent_start() -> str:
    return _run_spirent(["start"], timeout=15)


def spirent_stop() -> str:
    return _run_spirent(["stop"], timeout=15)


def spirent_protocol_start(device_name: Optional[str] = None) -> str:
    """Start EmulatedDevice protocols (ARP/GARP).

    When device_name is provided, only that device's protocols are started,
    preventing disruption to infrastructure devices (VPLS_PW_Peer, EVPN_RT2_Peer).
    When None, starts all devices (used only for initial infra setup).
    """
    args = ["protocol-start"]
    if device_name:
        args.extend(["--device-name", device_name])
    return _run_spirent(args, timeout=30)


def spirent_protocol_stop(device_name: Optional[str] = None) -> str:
    """Stop EmulatedDevice protocols.

    When device_name is provided, only that device's protocols are stopped.
    When None, stops all devices (used only for full teardown).
    """
    args = ["protocol-stop"]
    if device_name:
        args.extend(["--device-name", device_name])
    return _run_spirent(args, timeout=15)


def spirent_remove_stream(name: str) -> str:
    return _run_spirent(["remove-stream", "--name", name])


def spirent_remove_device(name: str) -> str:
    result = _run_spirent(["remove-device", "--name", name], retries=2)
    _invalidate_device_cache()
    return result


# ---------------------------------------------------------------------------
# MAC move execution strategies
# ---------------------------------------------------------------------------

def execute_mac_move_local_to_local(
    ac1_vlan: int,
    ac2_vlan: int,
    mac_count: int = 1,
    base_mac: str = "00:DE:AD:00:01:01",
    rate_mbps: int = 1,
    method: TrafficMethod = TrafficMethod.SPIRENT,
    ac1_outer_vlan: Optional[int] = None,
    ac2_outer_vlan: Optional[int] = None,
    **_kwargs,  # extra params from recipe dispatch (rate, custom MACs, ...)
) -> Dict[str, Any]:
    """
    Local AC -> Local AC move.

    Spirent strategy:
      1. Create device-group A on ac1_vlan with mac_count MACs
      2. Create device-group B on ac2_vlan with the SAME base_mac / count
      3. Create + start stream on ac1_vlan  -> DUT learns MACs on AC1
      4. Stop stream on ac1_vlan
      5. Create + start stream on ac2_vlan  -> DUT sees same MACs on AC2 = MOVE
    """
    result: Dict[str, Any] = {
        "type": "local_to_local",
        "from_vlan": ac1_vlan,
        "to_vlan": ac2_vlan,
        "mac_count": mac_count,
        "method": method.value,
        "steps": [],
    }

    if method == TrafficMethod.SPIRENT:
        ac1_dev = f"mac_mob_ac1_v{ac1_vlan}"
        ac2_dev = f"mac_mob_ac2_v{ac2_vlan}"

        r1 = spirent_create_mac_block(
            ac1_dev, ac1_vlan, mac_count, base_mac,
            outer_vlan=ac1_outer_vlan,
        )
        result["steps"].append({"action": "create_device_ac1", "detail": r1})

        result["steps"].append({
            "action": "protocol_start_learn",
            "output": spirent_protocol_start(device_name=ac1_dev)[:500],
        })
        waited = poll_until_mac_present(base_mac, timeout=8.0, fallback_sleep=3.0)
        result["steps"].append({"action": "wait_learn_arp", "seconds": waited})

        result["steps"].append({
            "action": "protocol_stop",
            "output": spirent_protocol_stop(device_name=ac1_dev)[:500],
        })

        result["steps"].append({
            "action": "remove_device_ac1",
            "output": spirent_remove_device(ac1_dev)[:500],
        })

        r2 = spirent_create_mac_block(
            ac2_dev, ac2_vlan, mac_count, base_mac,
            outer_vlan=ac2_outer_vlan,
        )
        result["steps"].append({"action": "create_device_ac2", "detail": r2})

        result["steps"].append({
            "action": "protocol_start_move",
            "output": spirent_protocol_start(device_name=ac2_dev)[:500],
        })
        waited = poll_until_mac_present(base_mac, timeout=8.0, fallback_sleep=3.0)
        result["steps"].append({"action": "wait_move_detect", "seconds": waited})

    elif method == TrafficMethod.MCP_SHOW:
        result["steps"].append({
            "action": "mcp_note",
            "detail": "Use run_show_command to verify MAC table after manual traffic shift.",
        })
    else:
        result["steps"] = _manual_steps("AC1", "AC2", mac_count)

    return result


def execute_rapid_flap(
    ac1_vlan: int,
    ac2_vlan: int,
    flap_count: int = 10,
    mac_count: int = 1,
    base_mac: str = "00:DE:AD:00:01:01",
    rate_mbps: int = 10,
    interval_sec: float = 0.5,
    method: TrafficMethod = TrafficMethod.SPIRENT,
    ac1_outer_vlan: Optional[int] = None,
    ac2_outer_vlan: Optional[int] = None,
) -> Dict[str, Any]:
    """Rapid back-and-forth flapping to trigger suppression.

    Strategy: create device on AC1, learn MAC, then alternate between AC1/AC2
    by destroying the current device and creating on the other AC. Each cycle
    is one create-device + protocol-start + protocol-stop + remove-device.

    The interval_sec controls the poll timeout (how long we wait for MAC to appear).
    Shorter poll = faster flaps = more likely to trigger suppression.
    """
    result: Dict[str, Any] = {
        "type": "rapid_flap",
        "flap_count": flap_count,
        "interval_sec": interval_sec,
        "mac_count": mac_count,
        "method": method.value,
        "steps": [],
        "timestamps": [],
    }

    if method == TrafficMethod.SPIRENT:
        if not is_spirent_healthy():
            if not ensure_spirent_ready():
                result["error"] = "Spirent session unhealthy"
                return result

        ac1_dev = f"flap_ac1_v{ac1_vlan}"

        spirent_create_mac_block(
            ac1_dev, ac1_vlan, mac_count, base_mac,
            outer_vlan=ac1_outer_vlan,
        )
        spirent_protocol_start(device_name=ac1_dev)
        poll_until_mac_present(base_mac, timeout=5.0, fallback_sleep=2.0)
        spirent_protocol_stop(device_name=ac1_dev)
        spirent_remove_device(ac1_dev)
        result["steps"].append({
            "action": "initial_learn",
            "detail": f"MAC {base_mac} learned on AC1 via protocol-start",
        })

        t_start = time.time()
        for i in range(flap_count):
            target_vlan = ac2_vlan if i % 2 == 0 else ac1_vlan
            target_outer = ac2_outer_vlan if i % 2 == 0 else ac1_outer_vlan
            dev_name = f"flap_v{target_vlan}"

            spirent_create_mac_block(
                dev_name, target_vlan, mac_count, base_mac,
                outer_vlan=target_outer,
            )
            spirent_protocol_start(device_name=dev_name)
            poll_until_mac_present(base_mac, timeout=max(interval_sec, 1.5),
                                  fallback_sleep=min(interval_sec, 1.0))
            spirent_protocol_stop(device_name=dev_name)
            spirent_remove_device(dev_name)

            result["timestamps"].append({
                "flap": i,
                "side": "ac2" if i % 2 == 0 else "ac1",
                "time": round(time.time() - t_start, 3),
            })
            result["steps"].append({
                "action": f"flap_{i}",
                "detail": f"protocol-start cycle {i + 1}/{flap_count} on vlan {target_vlan}",
            })

        result["total_elapsed_sec"] = round(time.time() - t_start, 2)
    else:
        result["steps"] = _manual_steps("AC1", "AC2", mac_count, note=f"Repeat {flap_count}x rapidly")

    return result


# NOTE: previous helper `execute_scale_mac_move` (64K MAC simultaneous scale
# test) was removed in PR7d (2026-04-14). No recipe action mapped to it; the
# orchestrator never invoked it. The same scale path can be exercised by
# calling `execute_mac_move_local_to_local` with `mac_count=65536` once a
# real scale recipe lands.


def execute_back_and_forth(
    ac1_vlan: int,
    ac2_vlan: int,
    ac3_vlan: Optional[int] = None,
    mac_count: int = 1,
    base_mac: str = "00:DE:AD:00:01:01",
    learn_sec: float = 3.0,
    method: TrafficMethod = TrafficMethod.SPIRENT,
    ac1_outer_vlan: Optional[int] = None,
    ac2_outer_vlan: Optional[int] = None,
    **_kwargs,  # extra params from recipe dispatch (rate, target_pe, ...)
) -> Dict[str, Any]:
    """A->B then B->A then (optionally) B->C.

    Actually executes each phase: create stream, start, wait, stop, remove.
    Records timestamps for sequence counting verification.
    """
    result: Dict[str, Any] = {
        "type": "back_and_forth",
        "mac_count": mac_count,
        "method": method.value,
        "sequence": ["ac1->ac2", "ac2->ac1"],
        "steps": [],
        "phase_timestamps": [],
    }
    if ac3_vlan:
        result["sequence"].append("ac2->ac3")

    if method == TrafficMethod.SPIRENT:
        vlan_map = {
            "ac1->ac2": ac2_vlan,
            "ac2->ac1": ac1_vlan,
            "ac2->ac3": ac3_vlan or ac1_vlan,
        }
        outer_map = {
            "ac1->ac2": ac2_outer_vlan,
            "ac2->ac1": ac1_outer_vlan,
            "ac2->ac3": None,
        }

        initial_dev = f"bf_init_v{ac1_vlan}"
        spirent_create_mac_block(
            initial_dev, ac1_vlan, mac_count, base_mac,
            outer_vlan=ac1_outer_vlan,
        )
        spirent_protocol_start(device_name=initial_dev)
        poll_until_mac_present(base_mac, timeout=learn_sec + 5, fallback_sleep=learn_sec)
        spirent_protocol_stop(device_name=initial_dev)
        spirent_remove_device(initial_dev)
        result["steps"].append({
            "action": "initial_learn_ac1",
            "detail": f"MAC {base_mac} learned on AC1 (VLAN {ac1_vlan})",
        })

        t_start = time.time()
        for step_label in result["sequence"]:
            vlan = vlan_map.get(step_label, ac1_vlan)
            outer = outer_map.get(step_label)
            dev_name = f"bf_{step_label.replace('->', '_')}"

            spirent_create_mac_block(
                dev_name, vlan, mac_count, base_mac,
                outer_vlan=outer,
            )
            spirent_protocol_start(device_name=dev_name)
            poll_until_mac_present(base_mac, timeout=learn_sec + 5, fallback_sleep=learn_sec)
            spirent_protocol_stop(device_name=dev_name)
            spirent_remove_device(dev_name)

            phase_time = round(time.time() - t_start, 2)
            result["phase_timestamps"].append({
                "phase": step_label, "vlan": vlan, "elapsed": phase_time,
            })
            result["steps"].append({
                "action": f"executed_{step_label}",
                "detail": f"MAC moved via protocol-start on vlan {vlan}",
            })

        result["total_elapsed_sec"] = round(time.time() - t_start, 2)
    else:
        result["steps"] = _manual_steps("AC1", "AC2", mac_count, note="Then reverse + optional AC3")

    return result


# ---------------------------------------------------------------------------
# Spirent HA traffic baseline and loss measurement
# ---------------------------------------------------------------------------

def spirent_start_ha_baseline(
    vlan: int,
    base_mac: str = "00:DE:AD:00:01:01",
    rate_mbps: int = 10,
    mac_count: int = 1,
) -> Dict[str, Any]:
    """Start baseline L2 traffic before an HA event for loss measurement.

    Creates a device group + stream, starts traffic. Call
    spirent_capture_ha_loss() after the HA event + recovery to measure loss.
    """
    dev_name = f"ha_baseline_v{vlan}"
    stream_name = f"ha_baseline_stream_v{vlan}"

    spirent_create_mac_block(dev_name, vlan, mac_count, base_mac)
    spirent_create_l2_stream(
        stream_name, vlan, base_mac, rate_mbps=rate_mbps,
    )
    spirent_start()

    return {
        "device_name": dev_name,
        "stream_name": stream_name,
        "vlan": vlan,
        "rate_mbps": rate_mbps,
        "mac_count": mac_count,
        "started": True,
        "detail": f"HA baseline: {mac_count} MAC(s) on VLAN {vlan} at {rate_mbps} Mbps",
    }


def spirent_capture_ha_loss() -> Dict[str, Any]:
    """Capture Spirent traffic stats after HA recovery.

    Returns TX/RX/loss data for the HA traffic verdict layer.
    """
    streams = _run_spirent(["stats", "--json"], timeout=15, return_streams=True)
    raw_stdout = streams.get("stdout", "") if isinstance(streams, dict) else streams
    try:
        stats = json.loads(raw_stdout)
    except (json.JSONDecodeError, ValueError):
        return {
            "tx_frames": 0, "rx_frames": 0,
            "loss_frames": 0, "loss_pct": 0.0,
            "error": f"Could not parse stats: {raw_stdout[:300]}",
        }

    tx = int(stats.get("tx_frames", 0))
    rx = int(stats.get("rx_frames", 0))
    loss = max(0, tx - rx)
    loss_pct = (loss / tx * 100) if tx > 0 else 0.0

    return {
        "tx_frames": tx,
        "rx_frames": rx,
        "loss_frames": loss,
        "loss_pct": round(loss_pct, 4),
        "raw": stats,
    }


def spirent_stop_ha_baseline(stream_name: Optional[str] = None) -> str:
    """Stop HA baseline traffic and optionally remove the stream."""
    out = spirent_stop()
    if stream_name:
        out += spirent_remove_stream(stream_name)
    return out


# ---------------------------------------------------------------------------
# Spirent BGP EVPN RT-2 MAC injection (for remote EVPN scenarios)
# ---------------------------------------------------------------------------

def spirent_inject_evpn_mac_route(
    bgp_device_name: str,
    mac: str,
    ip: str = "",
    evi: int = 0,
    rd: str = "",
    rt: str = "",
    label: int = 0,
    sticky: bool = False,
    allow_restart_fallback: bool = True,
    next_hop: str = "",
    seq: int = 0,
    count: int = 1,
) -> Dict[str, Any]:
    """Inject an EVPN RT-2 (MAC/IP) route via a Spirent BGP peer.

    Primary path: --no-restart (stc.apply + BgpReadvertiseRouteCommand).
    If the primary path output shows the readvertise failed AND
    allow_restart_fallback is True, retries with a full device restart.

    next_hop: BGP next-hop to advertise. CRITICAL: must be MPLS-reachable
    on DUT (i.e. an LDP-bound loopback). If the BGP peer's own IP has no
    LDP label binding on DUT, the EVPN MAC route will be valid in BGP RIB
    but never imported into the EVPN MAC table. Pass the Spirent's LDP
    loopback (e.g. 17.17.17.2) instead of its BGP loopback (19.19.19.2).

    seq: MAC mobility sequence number (BgpEvpnRoute.MacMobilitySequenceNumber).
    Default 0 keeps the legacy behavior. Recipes that exercise the sequence
    counter (e.g. multiple advertisements for the same MAC) MUST pass an
    incrementing seq -- otherwise the receiving PE keeps the existing route
    because it has the same (or higher) sequence number.
    """
    safe_count = max(1, int(count) if count else 1)
    base_args = [
        "evpn-routes",
        "--device-name", bgp_device_name,
        "--mac", mac,
        "--count", str(safe_count),
    ]
    if ip:
        base_args.extend(["--ip", ip])
    if rt:
        base_args.extend(["--rt", rt])
    if rd:
        base_args.extend(["--rd", rd])
    if label:
        base_args.extend(["--label", str(label)])
    if evi is not None:
        base_args.extend(["--ethernet-tag", "0"])
    if sticky:
        base_args.append("--sticky")
    if next_hop:
        base_args.extend(["--next-hop", next_hop])
    if seq and int(seq) > 0:
        base_args.extend(["--seq-num", str(int(seq))])

    args = base_args + ["--no-restart"]
    output = _run_spirent(args, timeout=30)
    ok = "error" not in output.lower() and "unsupported" not in output.lower()

    readvertise_failed = "readvertiseroutecommand failed" in output.lower()
    restart_fallback_used = False

    if ok and readvertise_failed and allow_restart_fallback:
        logger.warning("RT-2 BgpReadvertise failed; retrying with device restart")
        args_restart = base_args[:]
        output = _run_spirent(args_restart, timeout=30)
        ok = "error" not in output.lower() and "unsupported" not in output.lower()
        restart_fallback_used = True

    # NOTE: removed `time.sleep(3)` after success. The caller is expected to
    # call `poll_until_mac_present()` (or use `wait_for_mac_in_table` directly)
    # immediately after this returns -- those polls handle the BGP UPDATE
    # propagation window without burning a fixed 3 sec on the happy path.

    return {
        "pass": ok,
        "device": bgp_device_name,
        "mac": mac,
        "ip": ip,
        "seq": int(seq or 0),
        "count": safe_count,
        "output": output[:1000],
        "detail": f"RT-2 inject {'OK' if ok else 'FAILED'}: MAC {mac}"
                  + (f" x{safe_count}" if safe_count > 1 else "")
                  + (f" IP {ip}" if ip else "")
                  + (f" seq={seq}" if seq else "")
                  + (" (restart fallback)" if restart_fallback_used else ""),
        "fallback_needed": not ok,
    }


def spirent_withdraw_evpn_mac_route(
    bgp_device_name: str,
    mac: str,
    rd: str = "",
    allow_protocol_stop_fallback: bool = True,
) -> Dict[str, Any]:
    """Withdraw an EVPN RT-2 route via Spirent BGP peer.

    Strategy (in order):
      1. ``spirent_tool.py withdraw-routes`` per-route via STC
         ``BgpWithdrawRouteCommand``. Filters by RD + MAC when provided.
      2. If withdraw-routes fails AND ``allow_protocol_stop_fallback`` is True,
         falls back to ``spirent_tool.py protocol-stop --device-name <peer>``.
         This is a coarser hammer -- it tears down ALL routes from that BGP
         peer -- but it guarantees the tested MAC stops being advertised, which
         is the only thing the verdict layer cares about.

    The returned dict records ``method`` so the verdict engine can attribute
    correctly when a recipe expected a per-MAC withdraw but got the coarse one.
    """
    primary_args = ["withdraw-routes", "--device-name", bgp_device_name,
                    "--afi", "l2vpn-evpn", "--mac", mac]
    if rd:
        primary_args.extend(["--rd", rd])

    output = _run_spirent(primary_args, timeout=30)
    lower = output.lower()
    no_error = (
        "error" not in lower
        and "unknown command" not in lower
        and "invalid choice" not in lower
    )
    positive = (
        "withdrew" in lower
        or "[ok] withdraw" in lower
        or "withdrawn" in lower
        or "no tracked" in lower
    )
    ok = no_error and positive
    method = "withdraw-routes"
    fallback_output = ""

    if not ok and allow_protocol_stop_fallback:
        logger.warning("withdraw-routes failed for MAC %s on device %s -- falling back to "
                       "protocol-stop. NOTE: this withdraws ALL routes from this peer, "
                       "not just %s.", mac, bgp_device_name, mac)
        fallback_output = _run_spirent(
            ["protocol-stop", "--device-name", bgp_device_name],
            timeout=30,
        )
        flower = fallback_output.lower()
        ok = "error" not in flower and "no active session" not in flower
        method = "protocol-stop-fallback"

    return {
        "pass": bool(ok),
        "mac": mac,
        "rd": rd,
        "method": method,
        "output": output[:500],
        "fallback_output": fallback_output[:500] if fallback_output else "",
    }


# ---------------------------------------------------------------------------
# Cross-service MAC move execution (AC <-> EVPN, AC <-> PW via Spirent)
# ---------------------------------------------------------------------------

def execute_mac_move_ac_to_evpn(
    ac_vlan: int,
    bgp_device_name: str,
    mac: str = "00:DE:AD:00:01:01",
    evi: int = 0,
    rd: str = "",
    rt: str = "",
    method: TrafficMethod = TrafficMethod.SPIRENT,
    next_hop: str = "",
) -> Dict[str, Any]:
    """Local AC -> Remote EVPN move.

    Strategy:
      1. Spirent L2: learn MAC on local AC via L2 traffic
      2. Spirent BGP: inject same MAC via EVPN RT-2 (DUT sees remote advertisement)
      3. DUT should withdraw its local RT-2 for this MAC

    next_hop: BGP next-hop for the RT-2; must be MPLS-reachable on DUT.
    """
    result: Dict[str, Any] = {
        "type": "ac_to_evpn",
        "ac_vlan": ac_vlan,
        "mac": mac,
        "method": method.value,
        "steps": [],
    }

    if method == TrafficMethod.SPIRENT:
        spirent_create_mac_block(f"evpn_ac_v{ac_vlan}", ac_vlan, 1, mac)
        s = spirent_create_l2_stream(f"evpn_learn_v{ac_vlan}", ac_vlan, mac, rate_mbps=1)
        result["steps"].append({"action": "learn_on_ac", "output": s[:500]})
        spirent_start()
        poll_until_mac_present(mac, timeout=5.0, fallback_sleep=2.0)
        spirent_stop()
        result["steps"].append({"action": "mac_learned_locally", "detail": f"MAC {mac} learned on VLAN {ac_vlan}"})

        rt2 = spirent_inject_evpn_mac_route(
            bgp_device_name, mac, evi=evi, rd=rd, rt=rt, next_hop=next_hop,
        )
        result["steps"].append({"action": "inject_rt2", "detail": rt2})

        if rt2.get("fallback_needed"):
            result["steps"].append({
                "action": "fallback",
                "detail": "EVPN RT-2 injection not available via spirent_tool.py. "
                          "Use ExaBGP or manual RT-2 advertisement.",
            })

        poll_until_mac_present(mac, timeout=5.0, fallback_sleep=1.5)
    else:
        result["steps"] = _manual_steps("Local AC", "Remote EVPN", 1)

    return result


def execute_mac_move_evpn_to_ac(
    ac_vlan: int,
    bgp_device_name: str,
    mac: str = "00:DE:AD:00:01:01",
    evi: int = 0,
    rd: str = "",
    rt: str = "",
    method: TrafficMethod = TrafficMethod.SPIRENT,
    next_hop: str = "",
) -> Dict[str, Any]:
    """Remote EVPN -> Local AC move.

    Strategy:
      1. Spirent BGP: inject MAC via EVPN RT-2 (DUT installs as remote)
      2. Spirent L2: start traffic with same MAC on local AC
      3. DUT detects local learning overrides remote RT-2 -> advertises its own RT-2

    next_hop: BGP next-hop for the RT-2; must be MPLS-reachable on DUT.
    """
    result: Dict[str, Any] = {
        "type": "evpn_to_ac",
        "ac_vlan": ac_vlan,
        "mac": mac,
        "method": method.value,
        "steps": [],
    }

    if method == TrafficMethod.SPIRENT:
        rt2 = spirent_inject_evpn_mac_route(
            bgp_device_name, mac, evi=evi, rd=rd, rt=rt, next_hop=next_hop,
        )
        result["steps"].append({"action": "inject_rt2_remote", "detail": rt2})
        poll_until_mac_present(mac, timeout=5.0, fallback_sleep=1.5)

        spirent_create_mac_block(f"evpn2ac_v{ac_vlan}", ac_vlan, 1, mac)
        s = spirent_create_l2_stream(f"evpn2ac_learn_v{ac_vlan}", ac_vlan, mac, rate_mbps=1)
        result["steps"].append({"action": "learn_locally", "output": s[:500]})
        spirent_start()
        poll_until_mac_present(mac, timeout=5.0, fallback_sleep=2.0)
        result["steps"].append({"action": "mac_moved_to_local", "detail": f"MAC {mac} now local on VLAN {ac_vlan}"})

        if rt2.get("fallback_needed"):
            result["steps"].append({
                "action": "fallback",
                "detail": "RT-2 injection not available. Manual remote EVPN advertisement needed first.",
            })
    else:
        result["steps"] = _manual_steps("Remote EVPN", "Local AC", 1)

    return result


# NOTE: previous helper `execute_mac_move_ac_to_pw_via_spirent` was removed in
# PR7d (2026-04-14). It used a VLAN-only path that pre-dates the MPLS-based
# spirent_create_vpls_stream pipeline; the supported AC->PW path now goes
# through `execute_mac_move_local_to_local` + `execute_traffic_via_pw` with
# explicit `mpls_label`. See ACTION_TRIGGER_MAP "spirent_ac_to_pw".


def execute_remote_pe_traffic(
    bgp_device_name: str,
    mac: str = "00:DE:AD:00:01:01",
    evi: int = 0,
    rd: str = "",
    rt: str = "",
    method: TrafficMethod = TrafficMethod.SPIRENT,
    next_hop: str = "",
) -> Dict[str, Any]:
    """Simulate traffic from a remote PE via Spirent BGP EVPN RT-2 injection.

    Spirent BGP peer advertises EVPN RT-2 with the MAC, making the DUT
    think a remote PE has learned the MAC. Equivalent to remote_pe_traffic.

    next_hop: BGP next-hop the EVPN RT-2 advertises. MUST be MPLS-reachable
    on the DUT (LDP-bound loopback). When the Spirent BGP peer's own IP has
    no LDP path, the route ends in the BGP RIB but is never imported into
    the EVPN MAC table.
    """
    result: Dict[str, Any] = {
        "type": "remote_pe_traffic",
        "mac": mac,
        "method": method.value,
        "steps": [],
    }

    if method == TrafficMethod.SPIRENT and bgp_device_name:
        rt2 = spirent_inject_evpn_mac_route(
            bgp_device_name, mac, evi=evi, rd=rd, rt=rt,
            allow_restart_fallback=False, next_hop=next_hop,
        )
        result["steps"].append({"action": "inject_rt2_as_remote_pe", "detail": rt2})

        elapsed = poll_until_mac_present(mac, timeout=15.0, fallback_sleep=2.0)

        if elapsed >= 14.5:
            logger.info(
                "[RT2-RETRY] MAC %s not found after 15s quick poll, retrying with device restart...",
                mac,
            )
            rt2_retry = spirent_inject_evpn_mac_route(
                bgp_device_name, mac, evi=evi, rd=rd, rt=rt,
                allow_restart_fallback=True, next_hop=next_hop,
            )
            result["steps"].append({"action": "inject_rt2_retry", "detail": rt2_retry})
            elapsed = poll_until_mac_present(mac, timeout=45.0, fallback_sleep=2.0)

        result["steps"].append({
            "action": "remote_mac_installed",
            "detail": f"MAC {mac} via remote EVPN RT-2 (polled {elapsed:.1f}s)",
        })
    else:
        result["steps"] = _manual_steps("Remote PE", "DUT", 1)

    return result


def spirent_create_vpls_stream(
    name: str,
    mpls_label: int,
    inner_src_mac: str = "00:DE:AD:00:01:01",
    inner_dst_mac: Optional[str] = None,
    outer_vlan: Optional[int] = None,
    inner_vlan: Optional[int] = None,
    dst_mac_outer: Optional[str] = None,
    rate_mbps: int = 1,
) -> str:
    """Create an MPLS-encapsulated L2 stream for VPLS PW MAC learning.

    Uses spirent_tool.py vpls-stream to send traffic that PE receives on
    the MPLS tunnel interface and decapsulates as VPLS PW traffic.
    The inner_src_mac is the MAC the DUT will learn as a PW-sourced MAC.
    """
    if not is_spirent_healthy():
        if not ensure_spirent_ready():
            return "Spirent session unhealthy"

    if inner_dst_mac is None:
        inner_dst_mac = _get_dut_mac_for_stream() or "FF:FF:FF:FF:FF:FF"

    args = [
        "vpls-stream",
        "--mpls-label", str(mpls_label),
        "--inner-src-mac", inner_src_mac,
        "--inner-dst-mac", inner_dst_mac,
        "--rate-mbps", str(rate_mbps),
        "--frame-size", "128",
        "--name", name,
    ]
    if outer_vlan is not None:
        args.extend(["--outer-vlan", str(outer_vlan)])
    if inner_vlan is not None:
        args.extend(["--inner-vlan", str(inner_vlan)])
    if dst_mac_outer:
        args.extend(["--dst-mac", dst_mac_outer])

    output = _run_spirent(args, retries=2)
    _register_spirent_object(name, "stream")
    return output


def execute_traffic_via_pw(
    pw_vlan: int,
    mac: str = "00:DE:AD:00:01:01",
    mac_count: int = 1,
    rate_mbps: int = 1,
    method: TrafficMethod = TrafficMethod.SPIRENT,
    mpls_label: int = 0,
    pw_outer_vlan: int = 0,
    pw_inner_vlan: int = 0,
    dut_mac: str = "",
    pw_evpn_name: str = "",
) -> Dict[str, Any]:
    """Send traffic via VPLS PW using MPLS encapsulation.

    When mpls_label is provided (>0), uses vpls-stream to create an
    MPLS-encapsulated L2 stream. The DUT receives the MPLS packet on
    its MPLS-enabled sub-interface, decapsulates it, and learns the
    inner source MAC as a VPLS PW-sourced MAC.

    Falls back to raw L2 (legacy) when mpls_label is 0.
    """
    result: Dict[str, Any] = {
        "type": "traffic_via_pw",
        "pw_vlan": pw_vlan,
        "mac": mac,
        "mpls_label": mpls_label,
        "method": method.value,
        "steps": [],
    }

    if method == TrafficMethod.SPIRENT and mpls_label > 0:
        s = spirent_create_vpls_stream(
            f"vpls_pw_label_{mpls_label}",
            mpls_label=mpls_label,
            inner_src_mac=mac,
            outer_vlan=pw_outer_vlan if pw_outer_vlan > 0 else None,
            inner_vlan=pw_inner_vlan if pw_inner_vlan > 0 else None,
            dst_mac_outer=dut_mac or None,
            rate_mbps=rate_mbps,
        )
        result["steps"].append({
            "action": "create_vpls_pw_stream",
            "detail": f"MPLS label={mpls_label}, inner_src_mac={mac}",
            "output": s[:500],
        })
        spirent_start()
        elapsed = poll_until_mac_present(
            mac, timeout=15.0, fallback_sleep=3.0,
            evpn_name=pw_evpn_name or "",
        )
        result["steps"].append({
            "action": "mac_learned_via_pw",
            "detail": f"MAC {mac} via VPLS PW (MPLS label {mpls_label}, "
                      f"instance={pw_evpn_name or 'default'}, polled {elapsed:.1f}s)",
        })
    elif method == TrafficMethod.SPIRENT and pw_vlan > 0:
        spirent_create_mac_block(f"pw_traffic_v{pw_vlan}", pw_vlan, mac_count, mac)
        s = spirent_create_l2_stream(
            f"pw_traffic_stream_v{pw_vlan}", pw_vlan, mac, rate_mbps=rate_mbps,
        )
        result["steps"].append({"action": "create_pw_stream", "output": s[:500]})
        spirent_start()
        poll_until_mac_present(mac, timeout=5.0, fallback_sleep=2.0)
        result["steps"].append({"action": "mac_learned_via_pw", "detail": f"MAC {mac} on PW VLAN {pw_vlan}"})
    else:
        result["steps"] = _manual_steps("PW", "DUT", mac_count)
        result["steps"].append({"action": "note", "detail": "Requires mpls_label or pw_vlan"})

    return result


def execute_parallel_flap_and_restart(
    ac1_vlan: int,
    ac2_vlan: int,
    ha_command: str,
    run_show: Callable[[str, str], str],
    device: str,
    flap_count: int = 10,
    mac_count: int = 1,
    base_mac: str = "00:DE:AD:00:01:01",
    interval_sec: float = 0.5,
    method: TrafficMethod = TrafficMethod.SPIRENT,
) -> Dict[str, Any]:
    """Rapid MAC flapping WHILE simultaneously triggering an HA process restart.

    Runs two operations in parallel:
      1. Thread A: execute_rapid_flap (Spirent L2 VLAN swaps)
      2. Thread B: HA CLI command (process restart via run_show)
    Both start at the same time. The test verifies that the DUT doesn't enter
    a stuck state (no ghost MACs, no permanent suppression).
    """
    result: Dict[str, Any] = {
        "type": "parallel_flap_and_restart",
        "ha_command": ha_command,
        "flap_count": flap_count,
        "mac_count": mac_count,
        "method": method.value,
        "steps": [],
        "flap_result": None,
        "ha_result": None,
    }

    if method != TrafficMethod.SPIRENT:
        result["steps"] = _manual_steps("AC1", "AC2", mac_count,
                                        note=f"Flap {flap_count}x while running: {ha_command}")
        return result

    flap_output: Dict[str, Any] = {}
    ha_output: Dict[str, Any] = {"command": ha_command, "output": ""}

    def _run_flap() -> None:
        nonlocal flap_output
        flap_output = execute_rapid_flap(
            ac1_vlan, ac2_vlan, flap_count=flap_count,
            mac_count=mac_count, base_mac=base_mac,
            interval_sec=interval_sec, method=method,
        )

    def _run_ha() -> None:
        # Intentional 1s offset: the flap thread starts emitting traffic immediately
        # but Spirent's `start streams` returns ~500-1000ms before the first packet
        # hits the wire. Waiting 1s ensures the HA `show` snapshot reflects an
        # already-flapping bridge-domain, not the pre-flap baseline.
        time.sleep(1)
        ha_output["output"] = run_show(device, ha_command)

    t_flap = threading.Thread(target=_run_flap, name="flap_thread", daemon=True)
    t_ha = threading.Thread(target=_run_ha, name="ha_thread", daemon=True)

    t_start = time.time()
    t_flap.start()
    t_ha.start()

    t_flap.join(timeout=120)
    t_ha.join(timeout=120)
    elapsed = round(time.time() - t_start, 2)

    result["flap_result"] = flap_output
    result["ha_result"] = ha_output
    result["total_elapsed_sec"] = elapsed
    result["steps"].append({
        "action": "parallel_complete",
        "detail": f"Flap ({flap_count}x) + HA ({ha_command}) ran in parallel for {elapsed}s",
    })

    return result


def execute_admin_flap_during_move(
    ac1_vlan: int,
    ac2_vlan: int,
    ac1_interface: str,
    run_show: Callable[[str, str], str],
    device: str,
    flap_count: int = 6,
    mac_count: int = 1,
    base_mac: str = "00:DE:AD:00:01:01",
    interval_sec: float = 0.5,
    method: TrafficMethod = TrafficMethod.SPIRENT,
) -> Dict[str, Any]:
    """ac_ac SC10: race the AC1 admin-state flap against an in-flight MAC move.

    Two parallel threads:
      Thread A: Spirent rapid_flap moves the source MAC between AC1 and AC2.
      Thread B: After a 1s warmup, disables AC1 admin-state, waits ~3s, re-enables.

    The verdict layer the recipe should add asserts:
      - No ghost MAC entries on the BD after the dust settles.
      - MAC table converges to a single owner (typically AC2 once AC1 is admin-up).
      - LLP did not permanently shut the AC.

    Returns a structured result with both per-thread outcomes plus elapsed time.
    """
    result: Dict[str, Any] = {
        "type": "admin_flap_during_move",
        "ac1_vlan": ac1_vlan,
        "ac2_vlan": ac2_vlan,
        "ac1_interface": ac1_interface,
        "flap_count": flap_count,
        "mac_count": mac_count,
        "method": method.value,
        "steps": [],
        "flap_result": None,
        "admin_flap_result": {"interface": ac1_interface, "events": []},
    }

    if method != TrafficMethod.SPIRENT:
        result["steps"] = _manual_steps("AC1", "AC2", mac_count,
                                        note=f"Flap {flap_count}x while admin-flapping {ac1_interface}")
        return result

    flap_output: Dict[str, Any] = {}
    admin_events = result["admin_flap_result"]["events"]

    def _run_flap() -> None:
        nonlocal flap_output
        flap_output = execute_rapid_flap(
            ac1_vlan, ac2_vlan, flap_count=flap_count,
            mac_count=mac_count, base_mac=base_mac,
            interval_sec=interval_sec, method=method,
        )

    def _run_admin_flap() -> None:
        # Intentional 1s offset so the flap thread has Spirent traffic moving
        # before we yank the AC. A faster flap risks racing the protocol-start.
        time.sleep(1)
        try:
            run_show(device, "config")
            disable_out = run_show(device, f"interfaces {ac1_interface} admin-state disabled")
            commit_disable = run_show(device, "commit")
            run_show(device, "end")
            admin_events.append({
                "step": "admin_disable",
                "output": (disable_out + "\n" + commit_disable)[:500],
            })
        except (OSError, IOError, ConnectionError, TimeoutError, RuntimeError) as exc:
            admin_events.append({"step": "admin_disable_error", "detail": f"{exc}"})

        # Hold disabled long enough for the rapid flap to either retry or give
        # up. 3s mirrors the worst-case Spirent stream-toggle interval.
        time.sleep(3)

        try:
            run_show(device, "config")
            enable_out = run_show(device, f"interfaces {ac1_interface} admin-state enabled")
            commit_enable = run_show(device, "commit")
            run_show(device, "end")
            admin_events.append({
                "step": "admin_enable",
                "output": (enable_out + "\n" + commit_enable)[:500],
            })
        except (OSError, IOError, ConnectionError, TimeoutError, RuntimeError) as exc:
            admin_events.append({"step": "admin_enable_error", "detail": f"{exc}"})

    t_flap = threading.Thread(target=_run_flap, name="flap_thread", daemon=True)
    t_admin = threading.Thread(target=_run_admin_flap, name="admin_flap_thread", daemon=True)

    t_start = time.time()
    t_flap.start()
    t_admin.start()
    t_flap.join(timeout=180)
    t_admin.join(timeout=180)
    elapsed = round(time.time() - t_start, 2)

    result["flap_result"] = flap_output
    result["total_elapsed_sec"] = elapsed
    result["steps"].append({
        "action": "parallel_complete",
        "detail": (f"Rapid flap ({flap_count}x) raced admin disable/enable on "
                   f"{ac1_interface} for {elapsed}s"),
    })
    return result


def execute_mac_move_pw_to_pw(
    pw1_vlan: int,
    pw2_vlan: int,
    mac: str = "00:DE:AD:00:01:01",
    mac_count: int = 1,
    rate_mbps: int = 1,
    method: TrafficMethod = TrafficMethod.SPIRENT,
    pw1_mpls_label: int = 0,
    pw2_mpls_label: int = 0,
    pw_outer_vlan: Optional[int] = None,
    pw1_inner_vlan: Optional[int] = None,
    pw2_inner_vlan: Optional[int] = None,
    pw_dst_mac: Optional[str] = None,
) -> Dict[str, Any]:
    """PW1 -> PW2 move via MPLS-encapsulated traffic through VPLS pseudowires.

    Uses spirent_tool.py vpls-stream to create MPLS frames with the ingress
    label for each PW. The DUT pops the MPLS label and learns the inner src
    MAC from the PW. To move, send same inner MAC on different PW label.

    If MPLS labels are provided (pw1_mpls_label, pw2_mpls_label), uses the
    MPLS path (correct for real VPLS PW testing). Falls back to L2 VLAN swap
    if labels are not provided (legacy mode).
    """
    use_mpls = pw1_mpls_label > 0 and pw2_mpls_label > 0
    result: Dict[str, Any] = {
        "type": "pw_to_pw",
        "from_vlan": pw1_vlan,
        "to_vlan": pw2_vlan,
        "mac": mac,
        "method": method.value,
        "mode": "mpls" if use_mpls else "l2_vlan_swap",
        "steps": [],
    }

    if method == TrafficMethod.SPIRENT and use_mpls:
        pw1_name = f"pw1_mpls_{pw1_mpls_label}"
        pw2_name = f"pw2_mpls_{pw2_mpls_label}"

        s1 = spirent_create_vpls_stream(
            pw1_name, pw1_mpls_label, inner_src_mac=mac,
            outer_vlan=pw_outer_vlan, inner_vlan=pw1_inner_vlan,
            dst_mac_outer=pw_dst_mac, rate_mbps=rate_mbps,
        )
        result["steps"].append({"action": "create_pw1_mpls_stream", "output": s1[:500]})

        spirent_start()
        poll_until_mac_present(mac, timeout=5.0, fallback_sleep=2.0)
        spirent_stop()
        spirent_remove_stream(pw1_name)
        result["steps"].append({
            "action": "mac_on_pw1",
            "detail": f"MAC {mac} learned via PW1 (MPLS label {pw1_mpls_label})",
        })

        s2 = spirent_create_vpls_stream(
            pw2_name, pw2_mpls_label, inner_src_mac=mac,
            outer_vlan=pw_outer_vlan, inner_vlan=pw2_inner_vlan,
            dst_mac_outer=pw_dst_mac, rate_mbps=rate_mbps,
        )
        result["steps"].append({"action": "create_pw2_mpls_stream", "output": s2[:500]})

        spirent_start()
        poll_until_mac_present(mac, timeout=5.0, fallback_sleep=2.0)
        spirent_stop()
        spirent_remove_stream(pw2_name)
        result["steps"].append({
            "action": "mac_on_pw2",
            "detail": f"MAC {mac} moved to PW2 (MPLS label {pw2_mpls_label})",
        })

    elif method == TrafficMethod.SPIRENT and pw1_vlan > 0 and pw2_vlan > 0:
        spirent_create_mac_block(f"pw1_v{pw1_vlan}", pw1_vlan, mac_count, mac)
        spirent_create_mac_block(f"pw2_v{pw2_vlan}", pw2_vlan, mac_count, mac)

        s1 = spirent_create_l2_stream(f"pw1_learn_v{pw1_vlan}", pw1_vlan, mac, rate_mbps=rate_mbps)
        result["steps"].append({"action": "learn_on_pw1", "output": s1[:500]})
        spirent_start()
        poll_until_mac_present(mac, timeout=5.0, fallback_sleep=2.0)
        spirent_stop()
        spirent_remove_stream(f"pw1_learn_v{pw1_vlan}")
        result["steps"].append({"action": "mac_on_pw1", "detail": f"MAC {mac} learned via PW1 VLAN {pw1_vlan}"})

        s2 = spirent_create_l2_stream(f"pw2_move_v{pw2_vlan}", pw2_vlan, mac, rate_mbps=rate_mbps)
        result["steps"].append({"action": "move_to_pw2", "output": s2[:500]})
        spirent_start()
        poll_until_mac_present(mac, timeout=5.0, fallback_sleep=1.5)
        result["steps"].append({"action": "mac_on_pw2", "detail": f"MAC {mac} moved to PW2 VLAN {pw2_vlan}"})
    else:
        result["steps"] = _manual_steps("PW1", "PW2", mac_count)
        result["steps"].append({"action": "note", "detail": "Requires pw1/pw2 MPLS labels or VLANs"})

    return result


# ---------------------------------------------------------------------------
# Plan (dry-run) and manual helpers
# ---------------------------------------------------------------------------

def plan_mac_move(
    scenario_id: str,
    from_source: str,
    to_source: str,
    methods: Optional[List[TrafficMethod]] = None,
) -> Dict[str, Any]:
    """Build a plan dict without executing anything."""
    m = methods or detect_traffic_methods()
    primary = m[0] if m else TrafficMethod.MANUAL
    return {
        "scenario_id": scenario_id,
        "from": from_source,
        "to": to_source,
        "primary_method": primary.value,
        "available_methods": [x.value for x in m],
        "operator_steps": _manual_steps(from_source, to_source, 1),
        "spirent_strategy": (
            f"Create L2 device blocks with same MAC pool on VLANs mapped to "
            f"{from_source} and {to_source}. Start traffic on {from_source} VLAN "
            f"to learn, stop, start on {to_source} VLAN to trigger move."
        ),
        "scale_note": (
            "For 64K MACs: spirent_tool.py create-device --device-count 65536 "
            "--mac-step 1. One REST call via STC Device Block multiplier (~5s)."
        ),
    }


def _manual_steps(from_label: str, to_label: str, count: int, note: str = "") -> List[Dict[str, str]]:
    steps = [
        {"action": "ensure_learned", "detail": f"Verify {count} MAC(s) learned on {from_label}"},
        {"action": "shift_traffic", "detail": f"Move traffic so same MAC(s) appear on {to_label}"},
        {"action": "verify_move", "detail": "show evpn mac-table instance {evpn_name} mac {test_mac} | no-more"},
    ]
    if note:
        steps.append({"action": "note", "detail": note})
    return steps


# ---------------------------------------------------------------------------
# F3: Post-move MAC table polling with flag verification
# ---------------------------------------------------------------------------

RunShowFn = Callable[[str, str], str]


# NOTE: previous helper `poll_mac_state_after_move` was removed in PR7d
# (2026-04-14). Callers should use `wait_for_mac_in_table` (shared.validators)
# directly with `require_source=` -- it provides the same semantic check
# without the extra wrapper layer.


def execute_mac_move_evpn_to_pw(
    pw_vlan: int,
    bgp_device_name: str,
    mac: str = "00:DE:AD:00:01:01",
    mac_count: int = 1,
    evi: int = 0,
    rd: str = "",
    rt: str = "",
    method: TrafficMethod = TrafficMethod.SPIRENT,
    sticky: bool = False,
    next_hop: str = "",
) -> Dict[str, Any]:
    """EVPN -> PW move: MAC starts on remote EVPN (RT-2), then moves to PW.

    Phase 1: Inject EVPN RT-2 via Spirent BGP to establish MAC as remote-EVPN.
    Phase 2: Send L2 traffic on PW-mapped VLAN so DUT learns MAC from PW side.
    Phase 3: Withdraw EVPN RT-2 so the only path is PW.

    When sticky=True: RT-2 is injected with the sticky flag. The DUT should
    IGNORE the PW move and keep the sticky EVPN entry.
    """
    result: Dict[str, Any] = {
        "type": "sticky_evpn_to_pw" if sticky else "evpn_to_pw",
        "mac": mac,
        "pw_vlan": pw_vlan,
        "method": method.value,
        "sticky": sticky,
        "steps": [],
    }

    if method != TrafficMethod.SPIRENT or not bgp_device_name:
        result["steps"].append({"action": "skip", "reason": "Requires SPIRENT + BGP device"})
        return result

    inject_ok = spirent_inject_evpn_mac_route(
        bgp_device_name, mac, evi=evi, rd=rd, rt=rt, sticky=sticky, next_hop=next_hop,
    )
    result["steps"].append({"action": "inject_rt2", "ok": inject_ok})
    poll_until_mac_present(mac, timeout=5.0, fallback_sleep=1.5)

    block_name = f"pw_test_v{pw_vlan}"
    spirent_create_mac_block(block_name, pw_vlan, mac_count, mac)
    stream_name = f"pw_test_s_v{pw_vlan}"
    spirent_create_l2_stream(stream_name, pw_vlan, mac, rate_mbps=1)
    spirent_start()
    result["steps"].append({"action": "pw_traffic_start", "vlan": pw_vlan})
    poll_until_mac_present(mac, timeout=5.0, fallback_sleep=2.0)
    spirent_stop()
    result["steps"].append({"action": "pw_traffic_stop"})

    withdraw_ok = spirent_withdraw_evpn_mac_route(bgp_device_name, mac)
    result["steps"].append({"action": "withdraw_rt2", "ok": withdraw_ok})
    # Brief poll to give the BGP withdrawal time to propagate, but exit
    # early if the MAC source flips back to PW. Replaces a fixed 1s sleep.
    poll_until_mac_present(mac, timeout=2.0, fallback_sleep=0.5)

    return result


def execute_mac_move_pw_to_evpn(
    pw_vlan: int,
    bgp_device_name: str,
    mac: str = "00:DE:AD:00:01:01",
    mac_count: int = 1,
    evi: int = 0,
    rd: str = "",
    rt: str = "",
    method: TrafficMethod = TrafficMethod.SPIRENT,
    sticky: bool = False,
    next_hop: str = "",
) -> Dict[str, Any]:
    """PW -> EVPN move: MAC starts on PW, then moves to remote EVPN.

    Phase 1: Send L2 traffic on PW-mapped VLAN so DUT learns MAC from PW side.
    Phase 2: Stop PW traffic, inject EVPN RT-2 via Spirent BGP so MAC moves
             to remote-EVPN. When sticky=True, the RT-2 carries the sticky flag.
    """
    result: Dict[str, Any] = {
        "type": "sticky_pw_to_evpn" if sticky else "pw_to_evpn",
        "mac": mac,
        "pw_vlan": pw_vlan,
        "method": method.value,
        "sticky": sticky,
        "steps": [],
    }

    if method != TrafficMethod.SPIRENT or not bgp_device_name:
        result["steps"].append({"action": "skip", "reason": "Requires SPIRENT + BGP device"})
        return result

    block_name = f"pw_test_v{pw_vlan}"
    spirent_create_mac_block(block_name, pw_vlan, mac_count, mac)
    stream_name = f"pw_test_s_v{pw_vlan}"
    spirent_create_l2_stream(stream_name, pw_vlan, mac, rate_mbps=1)
    spirent_start()
    result["steps"].append({"action": "pw_traffic_start", "vlan": pw_vlan})
    poll_until_mac_present(mac, timeout=5.0, fallback_sleep=2.0)
    spirent_stop()
    result["steps"].append({"action": "pw_traffic_stop"})

    inject_ok = spirent_inject_evpn_mac_route(
        bgp_device_name, mac, evi=evi, rd=rd, rt=rt, sticky=sticky, next_hop=next_hop,
    )
    result["steps"].append({"action": "inject_rt2", "ok": inject_ok, "sticky": sticky})
    poll_until_mac_present(mac, timeout=5.0, fallback_sleep=1.5)

    return result


# ---------------------------------------------------------------------------
# Infrastructure detection: SI mode and PW data-plane checks
# ---------------------------------------------------------------------------

def _slice_vpls_pw_output_for_instance(output: str, evpn_name: str) -> str:
    """DNOS has no `show evpn vpls-pw instance <name>`; narrow full output to one instance."""
    if not evpn_name or evpn_name not in output:
        return output
    idx = output.index(evpn_name)
    chunk = output[idx:]
    lines_out: List[str] = []
    seen_non_empty = False
    for line in chunk.splitlines():
        stripped = line.strip()
        if seen_non_empty and stripped.startswith("Instance ") and evpn_name not in line:
            break
        lines_out.append(line)
        if stripped:
            seen_non_empty = True
    return "\n".join(lines_out)


def check_si_mode(
    device: str,
    evpn_name: str,
    run_show: RunShowFn,
) -> Dict[str, Any]:
    """Check if seamless-integration is enabled on the EVPN instance.

    Returns:
        {"si_active": bool, "detail": str, "output": str}
    """
    cmd = f"show config network-services evpn instance {evpn_name} | flatten | include seamless-integration"
    output = run_show(device, cmd)
    si_active = "seamless-integration" in output.lower()
    return {
        "si_active": si_active,
        "detail": (
            f"SI {'ACTIVE' if si_active else 'NOT active'} on {evpn_name}. "
            f"{'PW data plane is BNI -- PW tests blocked.' if si_active else 'PW tests can proceed.'}"
        ),
        "output": output[:500],
    }


def check_pw_data_plane(
    device: str,
    evpn_name: str,
    run_show: RunShowFn,
) -> Dict[str, Any]:
    """Check if VPLS PW data plane is active (not BNI).

    Returns:
        {"pw_active": bool, "pw_count": int, "bni_count": int, "detail": str}
    """
    cmd = "show evpn vpls-pw | no-more"
    raw = run_show(device, cmd)
    output = _slice_vpls_pw_output_for_instance(raw, evpn_name)

    pw_count = 0
    bni_count = 0
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("Instance") or stripped.startswith("---"):
            continue
        pw_count += 1
        if "BNI" in line or "Best but Not Installed" in line or "not installed" in line.lower():
            bni_count += 1

    pw_active = pw_count > 0 and bni_count < pw_count
    return {
        "pw_active": pw_active,
        "pw_count": pw_count,
        "bni_count": bni_count,
        "detail": (
            f"{pw_count} PW(s) found, {bni_count} BNI. "
            f"{'Data plane ACTIVE.' if pw_active else 'NO active PW data plane.'}"
        ),
        "output": output[:1000],
    }


# NOTE: previous helper `evaluate_test_infrastructure` was removed in PR7d
# (2026-04-14). It returned a static "valid/blocked tests" dict that no caller
# consumed -- recipes carry their own `infra_required` field and the
# orchestrator routes infrastructure decisions through `check_si_mode` /
# `check_pw_data_plane` directly. Re-add a slimmer version if a future
# infra-self-discovery path needs it.


# ---------------------------------------------------------------------------
# Multihoming: EVPN RT-1 and RT-4 injection via Spirent
# ---------------------------------------------------------------------------

def spirent_inject_evpn_rt1_route(
    bgp_device_name: str,
    esi: str,
    evi: int = 0,
    rd: str = "",
    rt: str = "",
    sub_type: str = "per_evi",
    label: int = 0,
) -> Dict[str, Any]:
    """Inject EVPN RT-1 (Ethernet Auto-Discovery) route via Spirent BGP peer.

    sub_type: "per_evi" (AD per-EVI for aliasing) or "per_es" (AD per-ES for mass-withdraw).
    Uses spirent_tool.py evpn-rt1 command (if available) or STC REST API directly.
    """
    args = [
        "evpn-rt1",
        "--device-name", bgp_device_name,
        "--esi", esi,
        "--sub-type", sub_type,
    ]
    if evi:
        args.extend(["--evi", str(evi)])
    if rd:
        args.extend(["--rd", rd])
    if rt:
        args.extend(["--rt", rt])
    if label:
        args.extend(["--label", str(label)])

    output = _run_spirent(args, timeout=30)
    ok = "error" not in output.lower() and "unrecognized" not in output.lower()

    if not ok and "unrecognized" in output.lower():
        return {
            "pass": False,
            "device": bgp_device_name,
            "esi": esi,
            "sub_type": sub_type,
            "output": output[:500],
            "detail": "evpn-rt1 command not yet implemented in spirent_tool.py. "
                      "Requires BgpEvpnAdRouteConfig STC object (ESI: 9 hex-byte format XX:XX:XX:XX:XX:XX:XX:XX:XX).",
            "needs_implementation": True,
        }

    return {
        "pass": ok,
        "device": bgp_device_name,
        "esi": esi,
        "sub_type": sub_type,
        "output": output[:500],
        "detail": f"RT-1 ({sub_type}) inject {'OK' if ok else 'FAILED'}",
    }


def spirent_inject_evpn_rt4_route(
    bgp_device_name: str,
    esi: str,
    rd: str = "",
    rt: str = "",
    originator_ip: str = "",
) -> Dict[str, Any]:
    """Inject EVPN RT-4 (Ethernet Segment) route via Spirent BGP peer.

    This tells the DUT that a remote PE participates in the same Ethernet Segment,
    triggering DF election on the DUT.
    """
    args = [
        "evpn-rt4",
        "--device-name", bgp_device_name,
        "--esi", esi,
    ]
    if rd:
        args.extend(["--rd", rd])
    if rt:
        args.extend(["--rt", rt])
    if originator_ip:
        args.extend(["--originator-ip", originator_ip])

    output = _run_spirent(args, timeout=30)
    ok = "error" not in output.lower() and "unrecognized" not in output.lower()

    if not ok and "unrecognized" in output.lower():
        return {
            "pass": False,
            "device": bgp_device_name,
            "esi": esi,
            "output": output[:500],
            "detail": "evpn-rt4 command not yet implemented in spirent_tool.py. "
                      "Requires BgpEvpnEthernetSegmentRouteConfig STC object (ESI: 9 hex-byte format XX:XX:XX:XX:XX:XX:XX:XX:XX).",
            "needs_implementation": True,
        }

    return {
        "pass": ok,
        "device": bgp_device_name,
        "esi": esi,
        "output": output[:500],
        "detail": f"RT-4 (ES route) inject {'OK' if ok else 'FAILED'}",
    }


# NOTE: previous helpers `execute_mh_df_election_test` and
# `execute_mh_mass_withdraw_test` were removed in PR7d (2026-04-14) because no
# call site or recipe action dispatched them. Multihoming RT-1/RT-4 injection
# is driven directly via `spirent_inject_evpn_rt1_route` /
# `spirent_inject_evpn_rt4_route` from the orchestrator and recipes.
