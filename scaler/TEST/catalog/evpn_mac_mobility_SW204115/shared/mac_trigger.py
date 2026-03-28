#!/usr/bin/env python3
"""
MAC move trigger execution for EVPN MAC mobility tests (SW-204115).

Three automation tiers:
  1. SPIRENT -- L2 device blocks with MAC stepping + stream VLAN swap for moves
  2. MCP_SHOW -- run_show_command to clear/manipulate MACs on the DUT directly
  3. MANUAL  -- print operator steps and wait

Key insight from SW-204115 meeting notes:
  - A MAC "move" = the same src-MAC appearing on a different AC/PW/remote.
  - Spirent achieves this by having TWO L2 device groups on different VLANs (= different ACs),
    each configured with the SAME src-MAC pool. Start traffic on device-group-1 (MAC learned
    on AC1), stop it, start traffic on device-group-2 (same MAC now seen on AC2). The DUT
    detects a Local->Local move.
  - For scale (64K MACs), use spirent_tool.py create-device --device-count 65536
    with --mac-step 1. One REST call creates the full block.

Spirent tool path: ~/SCALER/SPIRENT/spirent_tool.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

SPIRENT_TOOL = Path.home() / "SCALER" / "SPIRENT" / "spirent_tool.py"


class TrafficMethod(str, Enum):
    SPIRENT = "spirent"
    MCP_SHOW = "mcp_show"
    MANUAL = "manual"


def detect_traffic_methods() -> List[TrafficMethod]:
    methods: List[TrafficMethod] = []
    if SPIRENT_TOOL.is_file() or shutil.which("spirent_tool.py") or os.environ.get("SPIRENT_HOME"):
        methods.append(TrafficMethod.SPIRENT)
    if os.environ.get("DNOS_USE_MCP", "").lower() in ("1", "true", "yes"):
        methods.append(TrafficMethod.MCP_SHOW)
    methods.append(TrafficMethod.MANUAL)
    return list(dict.fromkeys(methods))


def _run_spirent(args: List[str], timeout: int = 60) -> str:
    tool = str(SPIRENT_TOOL)
    cmd = ["python3", tool] + args
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return (proc.stdout or "") + (proc.stderr or "")


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
) -> Dict[str, Any]:
    """
    Create an L2 device block on a VLAN (= one DUT AC).

    Uses spirent_tool.py create-device with --device-count for scale.
    64K MACs = one REST call (~5s).
    """
    ip = base_ip.replace("{vlan}", str(vlan))
    gw = gateway.replace("{vlan}", str(vlan))
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
    output = _run_spirent(args)
    return {
        "name": name,
        "vlan": vlan,
        "mac_count": mac_count,
        "base_mac": base_mac,
        "output": output[:2000],
    }


def spirent_create_l2_stream(
    name: str,
    vlan: int,
    src_mac: str = "00:DE:AD:00:01:01",
    dst_mac: str = "FF:FF:FF:FF:FF:FF",
    rate_mbps: int = 1,
    no_qinq: bool = True,
) -> str:
    args = [
        "create-stream",
        "--protocol", "l2",
        "--vlan", str(vlan),
        "--src-mac", src_mac,
        "--dst-mac", dst_mac,
        "--rate-mbps", str(rate_mbps),
        "--frame-size", "64",
        "--name", name,
    ]
    if no_qinq:
        args.append("--no-qinq")
    return _run_spirent(args)


def spirent_start() -> str:
    return _run_spirent(["start"])


def spirent_stop() -> str:
    return _run_spirent(["stop"])


def spirent_remove_stream(name: str) -> str:
    return _run_spirent(["remove-stream", "--name", name])


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
        r1 = spirent_create_mac_block(
            f"mac_mob_ac1_v{ac1_vlan}", ac1_vlan, mac_count, base_mac,
        )
        result["steps"].append({"action": "create_device_ac1", "detail": r1})

        r2 = spirent_create_mac_block(
            f"mac_mob_ac2_v{ac2_vlan}", ac2_vlan, mac_count, base_mac,
        )
        result["steps"].append({"action": "create_device_ac2", "detail": r2})

        s1 = spirent_create_l2_stream(
            f"learn_ac1_v{ac1_vlan}", ac1_vlan, base_mac, rate_mbps=rate_mbps,
        )
        result["steps"].append({"action": "stream_ac1", "output": s1[:1000]})

        result["steps"].append({"action": "start_traffic_ac1", "output": spirent_start()[:500]})
        result["steps"].append({"action": "wait_learn", "seconds": 5})
        result["steps"].append({"action": "stop_traffic_ac1", "output": spirent_stop()[:500]})

        spirent_remove_stream(f"learn_ac1_v{ac1_vlan}")

        s2 = spirent_create_l2_stream(
            f"learn_ac2_v{ac2_vlan}", ac2_vlan, base_mac, rate_mbps=rate_mbps,
        )
        result["steps"].append({"action": "stream_ac2", "output": s2[:1000]})
        result["steps"].append({"action": "start_traffic_ac2", "output": spirent_start()[:500]})
        result["steps"].append({"action": "wait_move_detect", "seconds": 3})

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
) -> Dict[str, Any]:
    """Rapid back-and-forth flapping to trigger suppression (FREEZE/DROP/SHUT).

    Actually executes the start/stop loop -- alternates traffic between two
    streams on different VLANs (same src-MAC) to trigger MAC moves.
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
        s1_name = f"flap_s1_v{ac1_vlan}"
        s2_name = f"flap_s2_v{ac2_vlan}"

        spirent_create_mac_block(f"flap_ac1_v{ac1_vlan}", ac1_vlan, mac_count, base_mac)
        spirent_create_mac_block(f"flap_ac2_v{ac2_vlan}", ac2_vlan, mac_count, base_mac)

        t_start = time.time()
        for i in range(flap_count):
            if i % 2 == 0:
                spirent_create_l2_stream(s1_name, ac1_vlan, base_mac, rate_mbps=rate_mbps)
                spirent_start()
                time.sleep(interval_sec)
                spirent_stop()
                spirent_remove_stream(s1_name)
                result["timestamps"].append({"flap": i, "side": "ac1", "time": time.time() - t_start})
            else:
                spirent_create_l2_stream(s2_name, ac2_vlan, base_mac, rate_mbps=rate_mbps)
                spirent_start()
                time.sleep(interval_sec)
                spirent_stop()
                spirent_remove_stream(s2_name)
                result["timestamps"].append({"flap": i, "side": "ac2", "time": time.time() - t_start})

            result["steps"].append({
                "action": f"flap_{i}_{'ac1' if i % 2 == 0 else 'ac2'}",
                "detail": f"Executed start/stop on {'ac1' if i % 2 == 0 else 'ac2'}",
            })

        result["total_elapsed_sec"] = round(time.time() - t_start, 2)
    else:
        result["steps"] = _manual_steps("AC1", "AC2", mac_count, note=f"Repeat {flap_count}x rapidly")

    return result


def execute_scale_mac_move(
    ac1_vlan: int,
    ac2_vlan: int,
    mac_count: int = 65536,
    base_mac: str = "00:DE:AD:00:00:01",
    rate_mbps: int = 100,
    method: TrafficMethod = TrafficMethod.SPIRENT,
) -> Dict[str, Any]:
    """
    Scale test: move mac_count MACs simultaneously (SW-204115 meeting: 64K, ~5s delay).

    Spirent strategy: same as local_to_local but with device-count=65536.
    One create-device REST call handles the full block via STC Device Block multiplier.
    """
    result: Dict[str, Any] = {
        "type": "scale_mac_move",
        "mac_count": mac_count,
        "from_vlan": ac1_vlan,
        "to_vlan": ac2_vlan,
        "method": method.value,
        "steps": [],
        "expected_delay_sec": 5,
    }

    if method == TrafficMethod.SPIRENT:
        r1 = spirent_create_mac_block(
            f"scale_ac1_v{ac1_vlan}", ac1_vlan, mac_count, base_mac,
        )
        result["steps"].append({"action": "create_64k_devices_ac1", "detail": r1})

        r2 = spirent_create_mac_block(
            f"scale_ac2_v{ac2_vlan}", ac2_vlan, mac_count, base_mac,
        )
        result["steps"].append({"action": "create_64k_devices_ac2", "detail": r2})

        s1 = spirent_create_l2_stream(
            f"scale_learn_v{ac1_vlan}", ac1_vlan, base_mac, rate_mbps=rate_mbps,
        )
        result["steps"].append({"action": "stream_learn_ac1", "output": s1[:1000]})
        result["steps"].append({"action": "start_and_learn", "output": spirent_start()[:500]})
        result["steps"].append({"action": "wait_learn_64k", "seconds": 10})
        result["steps"].append({"action": "stop_ac1", "output": spirent_stop()[:500]})

        spirent_remove_stream(f"scale_learn_v{ac1_vlan}")

        s2 = spirent_create_l2_stream(
            f"scale_move_v{ac2_vlan}", ac2_vlan, base_mac, rate_mbps=rate_mbps,
        )
        result["steps"].append({"action": "stream_move_ac2", "output": s2[:1000]})
        result["steps"].append({"action": "start_move_64k", "output": spirent_start()[:500]})
        result["steps"].append({
            "action": "wait_move_propagate",
            "seconds": 10,
            "note": "64K MACs move may take ~5s on DUT (chip/usync)",
        })
    else:
        result["steps"] = _manual_steps("AC1", "AC2", mac_count, note="64K scale test")

    return result


def execute_back_and_forth(
    ac1_vlan: int,
    ac2_vlan: int,
    ac3_vlan: Optional[int] = None,
    mac_count: int = 1,
    base_mac: str = "00:DE:AD:00:01:01",
    learn_sec: float = 3.0,
    method: TrafficMethod = TrafficMethod.SPIRENT,
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
        spirent_create_mac_block(f"bf_ac1_v{ac1_vlan}", ac1_vlan, mac_count, base_mac)
        spirent_create_mac_block(f"bf_ac2_v{ac2_vlan}", ac2_vlan, mac_count, base_mac)
        if ac3_vlan:
            spirent_create_mac_block(f"bf_ac3_v{ac3_vlan}", ac3_vlan, mac_count, base_mac)

        t_start = time.time()
        vlan_map = {
            "ac1->ac2": ac2_vlan,
            "ac2->ac1": ac1_vlan,
            "ac2->ac3": ac3_vlan or ac1_vlan,
        }

        for step_label in result["sequence"]:
            vlan = vlan_map.get(step_label, ac1_vlan)
            stream_name = f"bf_{step_label.replace('->', '_')}"

            spirent_create_l2_stream(stream_name, vlan, base_mac, rate_mbps=1)
            spirent_start()
            time.sleep(learn_sec)
            spirent_stop()
            spirent_remove_stream(stream_name)

            phase_time = round(time.time() - t_start, 2)
            result["phase_timestamps"].append({
                "phase": step_label, "vlan": vlan, "elapsed": phase_time,
            })
            result["steps"].append({
                "action": f"executed_{step_label}",
                "detail": f"Traffic on vlan {vlan} for {learn_sec}s, then stopped",
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

    dev = spirent_create_mac_block(dev_name, vlan, mac_count, base_mac)
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
    raw = _run_spirent(["stats", "--json"], timeout=15)
    try:
        stats = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return {
            "tx_frames": 0, "rx_frames": 0,
            "loss_frames": 0, "loss_pct": 0.0,
            "error": f"Could not parse stats: {raw[:300]}",
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
) -> Dict[str, Any]:
    """Inject an EVPN RT-2 (MAC/IP) route via a Spirent BGP peer.

    Uses spirent_tool.py add-routes --afi l2vpn-evpn.
    Falls back gracefully if the tool doesn't support EVPN routes yet.
    """
    args = [
        "add-routes",
        "--device-name", bgp_device_name,
        "--afi", "l2vpn-evpn",
        "--mac", mac,
        "--count", "1",
    ]
    if ip:
        args.extend(["--prefix", ip])
    if evi:
        args.extend(["--evi", str(evi)])
    if rd:
        args.extend(["--rd", rd])
    if rt:
        args.extend(["--rt", rt])
    if label:
        args.extend(["--label", str(label)])

    output = _run_spirent(args, timeout=30)
    ok = "error" not in output.lower() and "unsupported" not in output.lower()

    return {
        "pass": ok,
        "device": bgp_device_name,
        "mac": mac,
        "ip": ip,
        "output": output[:1000],
        "detail": f"RT-2 inject {'OK' if ok else 'FAILED'}: MAC {mac}" + (f" IP {ip}" if ip else ""),
        "fallback_needed": not ok,
    }


def spirent_withdraw_evpn_mac_route(
    bgp_device_name: str,
    mac: str,
) -> Dict[str, Any]:
    """Withdraw an EVPN RT-2 route via Spirent BGP peer."""
    args = [
        "withdraw-routes",
        "--device-name", bgp_device_name,
        "--afi", "l2vpn-evpn",
        "--mac", mac,
    ]
    output = _run_spirent(args, timeout=30)
    ok = "error" not in output.lower()
    return {
        "pass": ok,
        "mac": mac,
        "output": output[:500],
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
) -> Dict[str, Any]:
    """Local AC -> Remote EVPN move.

    Strategy:
      1. Spirent L2: learn MAC on local AC via L2 traffic
      2. Spirent BGP: inject same MAC via EVPN RT-2 (DUT sees remote advertisement)
      3. DUT should withdraw its local RT-2 for this MAC
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
        time.sleep(5)
        spirent_stop()
        result["steps"].append({"action": "mac_learned_locally", "detail": f"MAC {mac} learned on VLAN {ac_vlan}"})

        rt2 = spirent_inject_evpn_mac_route(
            bgp_device_name, mac, evi=evi, rd=rd, rt=rt,
        )
        result["steps"].append({"action": "inject_rt2", "detail": rt2})

        if rt2.get("fallback_needed"):
            result["steps"].append({
                "action": "fallback",
                "detail": "EVPN RT-2 injection not available via spirent_tool.py. "
                          "Use ExaBGP or manual RT-2 advertisement.",
            })

        time.sleep(3)
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
) -> Dict[str, Any]:
    """Remote EVPN -> Local AC move.

    Strategy:
      1. Spirent BGP: inject MAC via EVPN RT-2 (DUT installs as remote)
      2. Spirent L2: start traffic with same MAC on local AC
      3. DUT detects local learning overrides remote RT-2 -> advertises its own RT-2
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
            bgp_device_name, mac, evi=evi, rd=rd, rt=rt,
        )
        result["steps"].append({"action": "inject_rt2_remote", "detail": rt2})
        time.sleep(3)

        spirent_create_mac_block(f"evpn2ac_v{ac_vlan}", ac_vlan, 1, mac)
        s = spirent_create_l2_stream(f"evpn2ac_learn_v{ac_vlan}", ac_vlan, mac, rate_mbps=1)
        result["steps"].append({"action": "learn_locally", "output": s[:500]})
        spirent_start()
        time.sleep(5)
        result["steps"].append({"action": "mac_moved_to_local", "detail": f"MAC {mac} now local on VLAN {ac_vlan}"})

        if rt2.get("fallback_needed"):
            result["steps"].append({
                "action": "fallback",
                "detail": "RT-2 injection not available. Manual remote EVPN advertisement needed first.",
            })
    else:
        result["steps"] = _manual_steps("Remote EVPN", "Local AC", 1)

    return result


def execute_mac_move_ac_to_pw_via_spirent(
    ac_vlan: int,
    pw_vlan: int,
    mac: str = "00:DE:AD:00:01:01",
    mac_count: int = 1,
    method: TrafficMethod = TrafficMethod.SPIRENT,
) -> Dict[str, Any]:
    """Local AC -> PW move via VLAN-based path.

    Works when both the local AC and the PW-facing interface are reachable
    via different VLANs on the same Spirent port (through DNAAS).
    The PW VLAN maps to the PW-side AC of the EVPN service.
    """
    result: Dict[str, Any] = {
        "type": "ac_to_pw",
        "ac_vlan": ac_vlan,
        "pw_vlan": pw_vlan,
        "mac": mac,
        "method": method.value,
        "steps": [],
    }

    if method == TrafficMethod.SPIRENT and pw_vlan > 0:
        spirent_create_mac_block(f"pw_ac_v{ac_vlan}", ac_vlan, mac_count, mac)
        spirent_create_mac_block(f"pw_pw_v{pw_vlan}", pw_vlan, mac_count, mac)

        s1 = spirent_create_l2_stream(f"pw_learn_ac_v{ac_vlan}", ac_vlan, mac, rate_mbps=1)
        result["steps"].append({"action": "learn_on_ac", "output": s1[:500]})
        spirent_start()
        time.sleep(5)
        spirent_stop()
        spirent_remove_stream(f"pw_learn_ac_v{ac_vlan}")
        result["steps"].append({"action": "mac_learned_on_ac", "detail": f"MAC {mac} on VLAN {ac_vlan}"})

        s2 = spirent_create_l2_stream(f"pw_move_v{pw_vlan}", pw_vlan, mac, rate_mbps=1)
        result["steps"].append({"action": "move_to_pw", "output": s2[:500]})
        spirent_start()
        time.sleep(3)
        result["steps"].append({"action": "mac_on_pw", "detail": f"MAC {mac} now via PW VLAN {pw_vlan}"})
    else:
        result["steps"] = _manual_steps("Local AC", "PW", mac_count)
        result["steps"].append({"action": "note", "detail": "PW move requires pw_vlan or manual intervention"})

    return result


def execute_remote_pe_traffic(
    bgp_device_name: str,
    mac: str = "00:DE:AD:00:01:01",
    evi: int = 0,
    rd: str = "",
    rt: str = "",
    method: TrafficMethod = TrafficMethod.SPIRENT,
) -> Dict[str, Any]:
    """Simulate traffic from a remote PE via Spirent BGP EVPN RT-2 injection.

    Spirent BGP peer advertises EVPN RT-2 with the MAC, making the DUT
    think a remote PE has learned the MAC. Equivalent to remote_pe_traffic.
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
        )
        result["steps"].append({"action": "inject_rt2_as_remote_pe", "detail": rt2})
        time.sleep(3)
        result["steps"].append({"action": "remote_mac_installed", "detail": f"MAC {mac} via remote EVPN RT-2"})
    else:
        result["steps"] = _manual_steps("Remote PE", "DUT", 1)

    return result


def execute_traffic_via_pw(
    pw_vlan: int,
    mac: str = "00:DE:AD:00:01:01",
    mac_count: int = 1,
    rate_mbps: int = 1,
    method: TrafficMethod = TrafficMethod.SPIRENT,
) -> Dict[str, Any]:
    """Send traffic via a PW-mapped VLAN through DNAAS.

    Works when the PW-side AC is reachable through a DNAAS bridge-domain on
    a specific VLAN. Spirent sends L2 frames on that VLAN -- the DUT receives
    them on the PW-facing interface and learns the MAC as a PW-learned MAC.
    """
    result: Dict[str, Any] = {
        "type": "traffic_via_pw",
        "pw_vlan": pw_vlan,
        "mac": mac,
        "method": method.value,
        "steps": [],
    }

    if method == TrafficMethod.SPIRENT and pw_vlan > 0:
        spirent_create_mac_block(f"pw_traffic_v{pw_vlan}", pw_vlan, mac_count, mac)
        s = spirent_create_l2_stream(
            f"pw_traffic_stream_v{pw_vlan}", pw_vlan, mac, rate_mbps=rate_mbps,
        )
        result["steps"].append({"action": "create_pw_stream", "output": s[:500]})
        spirent_start()
        time.sleep(5)
        result["steps"].append({"action": "mac_learned_via_pw", "detail": f"MAC {mac} on PW VLAN {pw_vlan}"})
    else:
        result["steps"] = _manual_steps("PW", "DUT", mac_count)
        result["steps"].append({"action": "note", "detail": "Requires pw_vlan mapped in DNAAS"})

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


def execute_mac_move_pw_to_pw(
    pw1_vlan: int,
    pw2_vlan: int,
    mac: str = "00:DE:AD:00:01:01",
    mac_count: int = 1,
    rate_mbps: int = 1,
    method: TrafficMethod = TrafficMethod.SPIRENT,
) -> Dict[str, Any]:
    """PW1 -> PW2 move via Spirent VLAN swap.

    Same technique as local_to_local but using two PW-mapped VLANs.
    Learn MAC on PW1 VLAN, stop, start on PW2 VLAN -- DUT sees the MAC
    move from one PW to another PW.
    """
    result: Dict[str, Any] = {
        "type": "pw_to_pw",
        "from_vlan": pw1_vlan,
        "to_vlan": pw2_vlan,
        "mac": mac,
        "method": method.value,
        "steps": [],
    }

    if method == TrafficMethod.SPIRENT and pw1_vlan > 0 and pw2_vlan > 0:
        spirent_create_mac_block(f"pw1_v{pw1_vlan}", pw1_vlan, mac_count, mac)
        spirent_create_mac_block(f"pw2_v{pw2_vlan}", pw2_vlan, mac_count, mac)

        s1 = spirent_create_l2_stream(f"pw1_learn_v{pw1_vlan}", pw1_vlan, mac, rate_mbps=rate_mbps)
        result["steps"].append({"action": "learn_on_pw1", "output": s1[:500]})
        spirent_start()
        time.sleep(5)
        spirent_stop()
        spirent_remove_stream(f"pw1_learn_v{pw1_vlan}")
        result["steps"].append({"action": "mac_on_pw1", "detail": f"MAC {mac} learned via PW1 VLAN {pw1_vlan}"})

        s2 = spirent_create_l2_stream(f"pw2_move_v{pw2_vlan}", pw2_vlan, mac, rate_mbps=rate_mbps)
        result["steps"].append({"action": "move_to_pw2", "output": s2[:500]})
        spirent_start()
        time.sleep(3)
        result["steps"].append({"action": "mac_on_pw2", "detail": f"MAC {mac} moved to PW2 VLAN {pw2_vlan}"})
    else:
        result["steps"] = _manual_steps("PW1", "PW2", mac_count)
        result["steps"].append({"action": "note", "detail": "Requires pw1_vlan and pw2_vlan in DNAAS"})

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


def poll_mac_state_after_move(
    device: str,
    evpn_name: str,
    test_mac: str,
    expected_source: str,
    run_show: RunShowFn,
    timeout_sec: int = 10,
    poll_interval: float = 1.0,
) -> Dict[str, Any]:
    """Poll MAC table after a move until the MAC appears with expected source.

    Returns convergence time and the final MAC table output.
    """
    from .mac_parsers import parse_evpn_mac_entries, strip_ansi

    mac_l = test_mac.lower()
    t_start = time.time()
    elapsed = 0.0
    last_output = ""

    while elapsed < timeout_sec:
        last_output = run_show(
            device, f"show evpn mac-table instance {evpn_name} mac {test_mac} | no-more"
        )
        entries = parse_evpn_mac_entries(last_output)
        for e in entries:
            if e["mac"] == mac_l and e["source_hint"] == expected_source:
                convergence = round(time.time() - t_start, 3)
                return {
                    "pass": True,
                    "convergence_sec": convergence,
                    "source": e["source_hint"],
                    "mac": mac_l,
                    "output": last_output[:1000],
                    "detail": f"MAC appeared as {expected_source} after {convergence}s",
                }
        time.sleep(poll_interval)
        elapsed = time.time() - t_start

    return {
        "pass": False,
        "convergence_sec": None,
        "mac": mac_l,
        "timeout_sec": timeout_sec,
        "output": last_output[:1000],
        "detail": f"MAC did not appear as {expected_source} within {timeout_sec}s",
    }


def execute_mac_move_evpn_to_pw(
    pw_vlan: int,
    bgp_device_name: str,
    mac: str = "00:DE:AD:00:01:01",
    mac_count: int = 1,
    evi: int = 0,
    rd: str = "",
    rt: str = "",
    method: TrafficMethod = TrafficMethod.SPIRENT,
) -> Dict[str, Any]:
    """EVPN -> PW move: MAC starts on remote EVPN (RT-2), then moves to PW.

    Phase 1: Inject EVPN RT-2 via Spirent BGP to establish MAC as remote-EVPN.
    Phase 2: Send L2 traffic on PW-mapped VLAN so DUT learns MAC from PW side.
    Phase 3: Withdraw EVPN RT-2 so the only path is PW.
    """
    result: Dict[str, Any] = {
        "type": "evpn_to_pw",
        "mac": mac,
        "pw_vlan": pw_vlan,
        "method": method.value,
        "steps": [],
    }

    if method != TrafficMethod.SPIRENT or not bgp_device_name:
        result["steps"].append({"action": "skip", "reason": "Requires SPIRENT + BGP device"})
        return result

    inject_ok = spirent_inject_evpn_mac_route(bgp_device_name, mac, evi=evi, rd=rd, rt=rt)
    result["steps"].append({"action": "inject_rt2", "ok": inject_ok})
    time.sleep(3)

    block_name = f"evpn_pw_v{pw_vlan}"
    spirent_create_mac_block(block_name, pw_vlan, mac_count, mac)
    stream_name = f"evpn_pw_s_v{pw_vlan}"
    spirent_create_l2_stream(stream_name, pw_vlan, mac, rate_mbps=1)
    spirent_start()
    result["steps"].append({"action": "pw_traffic_start", "vlan": pw_vlan})
    time.sleep(5)
    spirent_stop()
    result["steps"].append({"action": "pw_traffic_stop"})

    withdraw_ok = spirent_withdraw_evpn_mac_route(bgp_device_name, mac)
    result["steps"].append({"action": "withdraw_rt2", "ok": withdraw_ok})
    time.sleep(2)

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
) -> Dict[str, Any]:
    """PW -> EVPN move: MAC starts on PW, then moves to remote EVPN.

    Phase 1: Send L2 traffic on PW-mapped VLAN so DUT learns MAC from PW side.
    Phase 2: Stop PW traffic, inject EVPN RT-2 via Spirent BGP so MAC moves
             to remote-EVPN.
    """
    result: Dict[str, Any] = {
        "type": "pw_to_evpn",
        "mac": mac,
        "pw_vlan": pw_vlan,
        "method": method.value,
        "steps": [],
    }

    if method != TrafficMethod.SPIRENT or not bgp_device_name:
        result["steps"].append({"action": "skip", "reason": "Requires SPIRENT + BGP device"})
        return result

    block_name = f"pw_evpn_v{pw_vlan}"
    spirent_create_mac_block(block_name, pw_vlan, mac_count, mac)
    stream_name = f"pw_evpn_s_v{pw_vlan}"
    spirent_create_l2_stream(stream_name, pw_vlan, mac, rate_mbps=1)
    spirent_start()
    result["steps"].append({"action": "pw_traffic_start", "vlan": pw_vlan})
    time.sleep(5)
    spirent_stop()
    result["steps"].append({"action": "pw_traffic_stop"})

    inject_ok = spirent_inject_evpn_mac_route(bgp_device_name, mac, evi=evi, rd=rd, rt=rt)
    result["steps"].append({"action": "inject_rt2", "ok": inject_ok})
    time.sleep(3)

    return result
