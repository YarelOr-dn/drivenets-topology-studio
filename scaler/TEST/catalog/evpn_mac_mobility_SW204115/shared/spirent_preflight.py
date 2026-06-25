#!/usr/bin/env python3
"""
Spirent pre-flight checks for EVPN test execution.

Verifies Spirent session is alive, port connectivity is healthy,
DNAAS path is ready, BGP peers are ESTABLISHED, and (critically)
the L2 traffic path actually works -- before starting tests.

The smoke_test_l2_path() function creates a temporary Spirent L2 stream
(no EmulatedDevice), sends a few frames, and checks if the MAC appears
on the DUT. This catches broken DNAAS/infra in ~10 seconds without
disrupting existing BGP sessions via stc.apply().
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .validators import poll_until, wait_for_mac_in_table

# Path resolution is delegated to shared.spirent_paths so that this module,
# mac_trigger, dead_peer_recovery, and spirent_vpls_provisioner all agree on
# the location of spirent_tool.py and respect the same env overrides
# (EVPN_MM_SPIRENT_TOOL, SPIRENT_HOME, SCALER_HOME).
from .spirent_paths import all_candidate_paths, spirent_tool_available, spirent_tool_path

logger = logging.getLogger("spirent_preflight")

RunShowFn = Callable[[str, str], str]

# Last-ditch fallbacks if the orchestrator failed to discover the AC
# interface AND the device profile didn't yield a candidate. These are
# legacy hardcoded names from the original PE-4 test path; they will be
# tried only AFTER `ac_interface` (passed in) and any sub-interface
# discovered from the live config of `device`.
_LEGACY_INTERFACE_HINTS: List[str] = ["ge400-0/0/5"]

SPIRENT_TOOL_PATHS = all_candidate_paths()


# ---------------------------------------------------------------------------
# AC encapsulation auto-detection (single source of truth, 2026-05-01)
#
# Reference: ~/.cursor/spirent-reference/dnaas-port-mode-untagged-ac.md
# ---------------------------------------------------------------------------

def detect_ac_encapsulation(
    device: str,
    ac_interface: str,
    run_show: RunShowFn,
) -> Dict[str, Any]:
    """Look at the live DUT config and classify the AC's encapsulation.

    Returns a dict with one of three shapes:
      port-mode (untagged):
        {"mode": "port_mode", "vlan": None, "inner_vlan": None,
         "spirent_args": ["--no-qinq"], "evidence": {...}}
      single-tag:
        {"mode": "single_tag", "vlan": <vid>, "inner_vlan": None,
         "spirent_args": ["--vlan", "<vid>", "--no-qinq"], ...}
      qinq (double-tag):
        {"mode": "qinq", "vlan": <outer>, "inner_vlan": <inner>,
         "spirent_args": ["--vlan", "<outer>", "--inner-vlan", "<inner>"], ...}
      unknown (raise-on-use):
        {"mode": "unknown", ..., "spirent_args": [], "error": "..."}

    The `spirent_args` list is the EXACT flag set that should be passed to
    spirent_tool.py create-stream. NEVER add `--vlan` outside this helper.
    """
    try:
        cfg_raw = run_show(
            device,
            f"show config interfaces {ac_interface} | flatten | no-more",
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "mode": "unknown", "vlan": None, "inner_vlan": None,
            "spirent_args": [], "error": f"run_show failed: {exc}",
            "evidence": {},
        }

    try:
        from shared.mac_parsers import strip_ansi as _strip
        cfg = _strip(cfg_raw)
    except Exception:
        cfg = cfg_raw

    last_token = ac_interface.split("/")[-1]
    has_dot_subif = "." in last_token
    has_vlan_id = bool(re.search(r"\bvlan-id\s+(\d+)", cfg))
    qinq_match = re.search(
        r"vlan-tags\s+outer-tag\s+(\d+)\s+inner-tag\s+(\d+)", cfg,
    )
    has_l2_service = bool(re.search(r"\bl2-service\s+enabled\b", cfg))

    evidence = {
        "ac_interface": ac_interface,
        "has_dot_subif": has_dot_subif,
        "has_vlan_id": has_vlan_id,
        "has_qinq": bool(qinq_match),
        "has_l2_service": has_l2_service,
        "config_dump": cfg[:1500],
    }

    if qinq_match:
        return {
            "mode": "qinq",
            "vlan": int(qinq_match.group(1)),
            "inner_vlan": int(qinq_match.group(2)),
            "spirent_args": [
                "--vlan", qinq_match.group(1),
                "--inner-vlan", qinq_match.group(2),
            ],
            "evidence": evidence,
        }

    if has_vlan_id:
        m = re.search(r"\bvlan-id\s+(\d+)", cfg)
        return {
            "mode": "single_tag",
            "vlan": int(m.group(1)),
            "inner_vlan": None,
            "spirent_args": ["--vlan", m.group(1), "--no-qinq"],
            "evidence": evidence,
        }

    # No qinq, no vlan-id. Port-mode requires l2-service enabled AND no .<sub>
    # in the interface name. (Some sub-interfaces have l2-service enabled +
    # vlan-id; those are caught above.)
    if has_l2_service and not has_dot_subif:
        return {
            "mode": "port_mode",
            "vlan": None,
            "inner_vlan": None,
            "spirent_args": ["--no-qinq"],
            "evidence": evidence,
        }

    return {
        "mode": "unknown",
        "vlan": None,
        "inner_vlan": None,
        "spirent_args": [],
        "error": (
            f"AC {ac_interface} on {device} has ambiguous encap. "
            f"Pass --evpn-instance + --ac-interface + --fabric-vlan flags "
            f"explicitly, or fix the AC config."
        ),
        "evidence": evidence,
    }


def _find_spirent_tool() -> Optional[Path]:
    if spirent_tool_available():
        return spirent_tool_path()
    return None


def _run_spirent_cmd(
    tool_path: Path, args: List[str], timeout: int = 30,
) -> Dict[str, Any]:
    try:
        cmd = ["python3", str(tool_path)] + args
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if proc.returncode == 0:
            try:
                return json.loads(proc.stdout)
            except json.JSONDecodeError:
                return {"status": "ok", "raw": proc.stdout[:1000]}
        return {"status": "error", "stderr": proc.stderr[:500], "rc": proc.returncode}
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def check_spirent_session(
    tool_path: Optional[Path] = None,
    auto_reconnect: bool = True,
) -> Dict[str, Any]:
    """Check if Spirent session is alive, port is reserved, and handles are valid.

    Goes beyond surface-level status to check:
    1. Session file exists and is active
    2. port_handle is not null
    3. Lab Server responds
    4. If unhealthy and auto_reconnect, attempts connect+reserve
    """
    tool = tool_path or _find_spirent_tool()
    if not tool:
        return {
            "available": False,
            "reason": "spirent_tool.py not found",
            "searched": [str(p) for p in all_candidate_paths()],
        }

    sess_path = Path.home() / "SCALER" / "SPIRENT" / "sessions" / "dn_spirent_main.json"
    if sess_path.exists():
        try:
            sess_data = json.loads(sess_path.read_text())
            if not sess_data.get("active", False):
                if auto_reconnect:
                    return _attempt_reconnect(tool, "Session marked inactive")
                return {
                    "available": False,
                    "reason": "Session exists but marked inactive (cleaned up)",
                    "tool_path": str(tool),
                    "fix": "Run spirent_tool.py connect && reserve",
                }
            if not sess_data.get("port_handle"):
                if auto_reconnect:
                    return _attempt_reconnect(tool, "port_handle is null")
                return {
                    "available": False,
                    "reason": "Session active but port_handle is null (stale session)",
                    "tool_path": str(tool),
                    "fix": "Run spirent_tool.py connect --force-new && reserve",
                }
        except (json.JSONDecodeError, OSError):
            pass

    result = _run_spirent_cmd(tool, ["status", "--json"])
    if result.get("status") in ("timeout", "error"):
        detail = result.get("detail", result.get("stderr", "unknown"))
        if auto_reconnect:
            return _attempt_reconnect(tool, f"Status check failed: {detail}")
        return {
            "available": False,
            "reason": f"Spirent status check failed: {detail}",
            "tool_path": str(tool),
        }

    return {
        "available": True,
        "tool_path": str(tool),
        "session": result,
    }


def _attempt_reconnect(tool: Path, reason: str) -> Dict[str, Any]:
    """Try connect + reserve to recover a broken session."""
    logger.info("Spirent session unhealthy (%s), attempting reconnect...", reason)
    connect_result = _run_spirent_cmd(tool, ["connect"], timeout=45)
    if connect_result.get("status") in ("timeout", "error"):
        return {
            "available": False,
            "reason": f"Auto-reconnect failed (connect): {reason}",
            "tool_path": str(tool),
        }
    reserve_result = _run_spirent_cmd(tool, ["reserve"], timeout=30)
    if reserve_result.get("status") in ("timeout", "error"):
        return {
            "available": False,
            "reason": f"Auto-reconnect failed (reserve): {reason}",
            "tool_path": str(tool),
        }
    logger.info("Spirent auto-reconnect succeeded")
    return {
        "available": True,
        "tool_path": str(tool),
        "session": reserve_result,
        "reconnected": True,
        "reconnect_reason": reason,
    }


def check_dnaas_path(
    vlan: int, tool_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Check if DNAAS bridge-domain path is ready for the specified VLAN.

    The 'dnaas' subcommand may not exist in spirent_tool.py. When unavailable,
    assume the path is ready (DNAAS was already configured in prior sessions).
    """
    tool = tool_path or _find_spirent_tool()
    if not tool:
        return {"ready": True, "reason": "spirent_tool.py not found; assuming DNAAS ready", "vlan": vlan}

    result = _run_spirent_cmd(tool, ["dnaas", "check", "--vlan", str(vlan)])
    if result.get("status") in ("timeout", "error"):
        detail = result.get("detail", result.get("stderr", "unknown"))
        if "invalid choice" in detail or "unrecognized arguments" in detail:
            return {"ready": True, "reason": "dnaas command not available; assuming path ready", "vlan": vlan}
        return {
            "ready": False,
            "reason": f"DNAAS check failed: {detail}",
            "vlan": vlan,
        }

    return {"ready": True, "vlan": vlan, "detail": result}


def check_bgp_peers_established(
    run_show: RunShowFn,
    device: str,
    address_family: str = "l2vpn evpn",
) -> Dict[str, Any]:
    """Check that BGP peers for the given AF are ESTABLISHED on the DUT.

    Runs 'show bgp <af> summary' and parses state. Returns structured
    result with per-peer status.
    """
    from .mac_parsers import parse_bgp_l2vpn_evpn_summary

    cmd = f"show bgp {address_family} summary | no-more"
    try:
        raw = run_show(device, cmd)
    except Exception as exc:
        return {
            "pass": False,
            "total": 0,
            "established": 0,
            "peers": [],
            "error": str(exc),
        }

    parsed = parse_bgp_l2vpn_evpn_summary(raw)
    not_established = [
        n for n in parsed.get("neighbors", []) if not n.get("established")
    ]
    return {
        "pass": len(not_established) == 0 and parsed.get("total", 0) > 0,
        "total": parsed.get("total", 0),
        "established": parsed.get("established", 0),
        "not_established": not_established,
        "peers": parsed.get("neighbors", []),
        "raw": raw[:500],
    }


def _discover_subif_from_live_config(
    run_show: RunShowFn,
    device: str,
    ac_vlan: int,
    outer_vlan: Optional[int] = None,
) -> List[str]:
    """Query the live DUT config to find sub-interfaces that match the
    AC vlan tags. This is the preferred device-agnostic path -- no
    interface naming convention is assumed.

    Returns up to 3 candidate sub-interface names ordered by best match:
      1. Sub-if whose outer-tag == outer_vlan AND inner-tag == ac_vlan (Q-in-Q exact match)
      2. Sub-if whose outer-tag == ac_vlan (single-tagged AC)
      3. Sub-if whose outer-tag == outer_vlan (any inner)
    """
    candidates: List[str] = []
    try:
        cfg = run_show(device, "show config interfaces | flatten | no-more")
    except Exception:
        return candidates

    qinq_pat = re.compile(
        r"interfaces\s+(\S+?\.\d+)\s+vlan-tags\s+outer-tag\s+(\d+)\s+inner-tag\s+(\d+)"
    )
    single_pat = re.compile(
        r"interfaces\s+(\S+?\.\d+)\s+vlan-tags\s+vlan-id\s+(\d+)"
    )
    outer_only_pat = re.compile(
        r"interfaces\s+(\S+?\.\d+)\s+vlan-tags\s+outer-tag\s+(\d+)(?!\s+inner-tag)"
    )

    if outer_vlan is not None:
        for m in qinq_pat.finditer(cfg):
            if int(m.group(2)) == outer_vlan and int(m.group(3)) == ac_vlan:
                candidates.append(m.group(1))
                break

    for m in single_pat.finditer(cfg):
        if int(m.group(2)) == ac_vlan:
            cand = m.group(1)
            if cand not in candidates:
                candidates.append(cand)
            break

    if outer_vlan is not None:
        for m in outer_only_pat.finditer(cfg):
            if int(m.group(2)) == outer_vlan:
                cand = m.group(1)
                if cand not in candidates:
                    candidates.append(cand)
                break

    return candidates


def _discover_dut_interface_mac(
    run_show: RunShowFn,
    device: str,
    ac_vlan: int,
    outer_vlan: Optional[int] = None,
    ac_interface: Optional[str] = None,
) -> str:
    """Discover the DUT's interface MAC for the AC sub-interface.

    DNAAS SPINE-D14 has LLP enabled -- broadcast dst-mac causes loop
    detection and shuts down the BD path.  Unicast dst-mac avoids this.

    Discovery order (device-agnostic):
      1. Caller-provided ac_interface (and its base port) -- highest trust
      2. Sub-interfaces matched from live config by VLAN tag pair
      3. Legacy hardcoded hints (`ge400-0/0/5.*`) -- LAST resort only,
         keep working with old PE-4 sessions where discovery returns nothing
    """
    candidates: List[str] = []

    if ac_interface:
        ac_if = ac_interface.strip()
        if ac_if:
            candidates.append(ac_if)
            base = ac_if.rsplit(".", 1)[0]
            if base != ac_if:
                candidates.append(base)

    for cand in _discover_subif_from_live_config(
        run_show, device, ac_vlan, outer_vlan,
    ):
        if cand not in candidates:
            candidates.append(cand)
        base = cand.rsplit(".", 1)[0]
        if base not in candidates:
            candidates.append(base)

    for legacy in _LEGACY_INTERFACE_HINTS:
        if outer_vlan is not None:
            for sub in (f"{legacy}.{ac_vlan}", f"{legacy}.{outer_vlan}"):
                if sub not in candidates:
                    candidates.append(sub)
        else:
            sub = f"{legacy}.{ac_vlan}"
            if sub not in candidates:
                candidates.append(sub)
        if legacy not in candidates:
            candidates.append(legacy)

    seen: set = set()
    for iface in candidates:
        if iface in seen:
            continue
        seen.add(iface)
        try:
            out = run_show(device, f"show interfaces {iface} | no-more")
            m = re.search(r"MAC Address:\s+([\da-fA-F:]+)", out)
            if m:
                return m.group(1).lower()
        except Exception:
            continue
    return ""


def _verify_stream_gone(tool: Path, stream_name: str) -> bool:
    """B4: After remove-stream, verify the stream truly disappeared.

    cmd_create_stream has a duplicate-name guard that returns "already
    exists -- reusing", which means a stale handle from a crashed prior
    run will silently shadow our new params (wrong src/dst-mac, etc).
    """
    status = _run_spirent_cmd(tool, ["status", "--json"], timeout=15)
    if status.get("status") in ("timeout", "error"):
        return True  # cannot verify -- assume removed and move on
    streams = status.get("streams") or []
    for s in streams:
        if s.get("name") == stream_name:
            return False
    return True


def _lab_server_responsive(tool: Path, max_secs: float = 8.0) -> bool:
    """B1: probe Lab Server responsiveness before doing destructive things.

    A loaded session with active BGP/ISIS/LDP can take 25-40s to apply()
    a brand-new stream. The smoke test's create-stream timeout used to be
    20s, which is hostile to that reality. Before kicking off the smoke
    test, we time how long `status --json` takes; if it's slow we either
    skip the smoke (declare PASS-UNVERIFIED) or use a longer timeout.
    """
    t0 = time.time()
    res = _run_spirent_cmd(tool, ["status", "--json"], timeout=int(max_secs * 2))
    if res.get("status") in ("timeout", "error"):
        return False
    elapsed = time.time() - t0
    return elapsed <= max_secs


def smoke_test_l2_path(
    run_show: RunShowFn,
    device: str,
    evpn_name: str,
    ac_vlan: int,
    outer_vlan: Optional[int] = None,
    smoke_mac: str = "00:DE:AD:FF:FF:01",
    dut_mac: Optional[str] = None,
    timeout: float = 10.0,
    poll_interval: float = 1.0,
    ac_interface: Optional[str] = None,
    skip_post_cleanup: bool = False,
    port_mode: bool = False,
    fabric_vlan: Optional[int] = None,
) -> Dict[str, Any]:
    """Send a few L2 frames via Spirent and check if MAC appears on DUT.

    This is the REAL infrastructure test -- it proves the full path:
      Spirent -> DNAAS BD -> DUT sub-interface -> EVPN mac-table

    Creates a temporary device + stream, starts traffic, polls the MAC
    table, then cleans up. Takes ~10 seconds total.

    IMPORTANT: Uses unicast dst-mac (DUT interface MAC) instead of
    broadcast to avoid triggering DNAAS LLP on SPINE-D14.

    If skip_post_cleanup is True, traffic is stopped and the smoke stream is
    removed, but the DUT's EVPN MAC table is not cleared (handy for manual
    follow-up; default False matches legacy preflight behavior).

    Returns:
        {"pass": bool, "elapsed_sec": float, "detail": str, ...}
    """
    tool = _find_spirent_tool()
    if not tool:
        return {"pass": False, "detail": "spirent_tool.py not found", "elapsed_sec": 0}

    if not dut_mac:
        dut_mac = _discover_dut_interface_mac(
            run_show, device, ac_vlan, outer_vlan, ac_interface=ac_interface,
        )
    if not dut_mac:
        logger.warning("Could not discover DUT MAC -- falling back to broadcast (LLP risk!)")
        dut_mac = "FF:FF:FF:FF:FF:FF"

    stream_name = "_smoke_test_stream"
    t0 = time.time()
    result: Dict[str, Any] = {
        "pass": False,
        "elapsed_sec": 0,
        "mac": smoke_mac,
        "evpn_name": evpn_name,
        "ac_vlan": ac_vlan,
        "ac_interface": ac_interface or "",
        "dut_mac": dut_mac,
        "steps": [],
    }

    try:
        # B4: remove any stale smoke stream from a prior crashed run, then
        # verify it's actually gone before re-creating. Otherwise the
        # cmd_create_stream duplicate-name guard ("already exists -- reusing")
        # silently shadows our params with a stale handle that points at the
        # wrong src/dst-mac.
        try:
            _run_spirent_cmd(tool, ["remove-stream", "--name", stream_name], timeout=15)
        except Exception:
            pass
        if not _verify_stream_gone(tool, stream_name):
            # Poll-based retry: poll up to 3s for the stream to disappear.
            # If it doesn't, attempt a second remove and re-verify.
            def _stream_gone_check():
                gone = _verify_stream_gone(tool, stream_name)
                return bool(gone), {"gone": bool(gone), "stream": stream_name}

            stale_val = poll_until(
                _stream_gone_check,
                timeout_sec=3.0,
                interval_sec=0.5,
                progress_label=f"smoke stream {stream_name} cleared",
            )
            if not stale_val.passed:
                _run_spirent_cmd(tool, ["remove-stream", "--name", stream_name], timeout=15)
                if not _verify_stream_gone(tool, stream_name):
                    result["detail"] = (
                        f"Stale smoke stream '{stream_name}' could not be removed "
                        f"(STC handle leaked from prior run). Run "
                        f"'spirent_tool.py reset' or restart the session."
                    )
                    result["steps"].append({"action": "stale_cleanup", "result": "leaked"})
                    return result

        # B1: probe Lab Server responsiveness. If status takes >8s, the
        # session is loaded (active BGP/ISIS/LDP) and stc.apply() on a new
        # stream will routinely take 25-40s. Use a generous create-stream
        # timeout (60s) and skip the misleading "L2 path BROKEN" verdict.
        lab_fast = _lab_server_responsive(tool, max_secs=8.0)
        create_timeout = 30 if lab_fast else 60
        result["steps"].append({
            "action": "lab_probe",
            "fast": lab_fast,
            "create_timeout_sec": create_timeout,
        })

        # Stream-only: no EmulatedDevice creation.
        # Creating a device while BGP protocols run causes stc.apply() failures.
        # Raw L2 streams work without a device and are sufficient for MAC learning.
        frame_size = "128" if (outer_vlan is not None or port_mode) else "96"
        stream_args = [
            "create-stream",
            "--protocol", "l2",
            "--src-mac", smoke_mac,
            "--dst-mac", dut_mac,
            "--rate-mbps", "1",
            "--frame-size", frame_size,
            "--name", stream_name,
        ]
        if port_mode:
            # True untagged port-mode AC: NO frame VLAN at all. Fabric prepends
            # its own VLAN (fabric_vlan) on the DNAAS path; the DUT receives
            # the frame untagged after fabric strip. spirent_tool.py does NOT
            # need any --vlan flag in this mode.
            #
            # Reference: ~/.cursor/spirent-reference/dnaas-port-mode-untagged-ac.md
            stream_args += ["--no-qinq"]
            # Port-mode learns are slower: DNAAS LLP on the ingress leaf
            # filters first-time-seen source MACs for ~12-15s of sustained
            # traffic before letting them through. A bare 10s smoke window
            # routinely fails for fresh sessions even though the path works.
            # Bump the poll timeout so the smoke is conclusive.
            if timeout < 25.0:
                _bumped_timeout = 25.0
                print(
                    f"  [SMOKE] port-mode AC: bumping poll timeout {timeout}s -> "
                    f"{_bumped_timeout}s (DNAAS LLP needs sustained traffic)",
                    flush=True,
                )
                timeout = _bumped_timeout
            print(
                f"  [SMOKE] port-mode AC: untagged stream, fabric_vlan={fabric_vlan}, "
                f"ac_interface={ac_interface or '?'}",
                flush=True,
            )
        elif outer_vlan is not None:
            stream_args += ["--vlan", str(outer_vlan), "--inner-vlan", str(ac_vlan)]
        else:
            stream_args += ["--vlan", str(ac_vlan), "--no-qinq"]

        stream_out = _run_spirent_cmd(tool, stream_args, timeout=create_timeout)
        stream_status = stream_out.get("status", "ok")
        result["steps"].append({"action": "create_stream", "result": stream_status})
        # B1: timeout must be a HARD FAIL (not silently fall through to
        # start+poll, which then misreports "L2 path BROKEN: MAC never
        # appeared" when in reality no stream ever existed).
        if stream_status in ("error", "timeout"):
            err_detail = stream_out.get("stderr") or stream_out.get("detail") or ""
            if stream_status == "timeout":
                result["detail"] = (
                    f"Spirent create-stream TIMED OUT after {create_timeout}s "
                    f"(Lab Server slow / stc.apply hung). NOT a DNAAS path "
                    f"failure -- the stream was never created. Try: "
                    f"spirent_tool.py status, then re-run."
                )
            else:
                result["detail"] = f"Failed to create smoke test stream: {err_detail}"
            return result

        # Start traffic (no protocol-start needed without a device)
        _run_spirent_cmd(tool, ["start"], timeout=15)
        result["steps"].append({"action": "traffic_start"})

        # Poll DUT MAC table for the smoke MAC using the shared validator.
        # This avoids the race where a fixed sleep interval misses a fast-arriving
        # MAC and exits early on first detection (instead of always waiting full timeout).
        mac_val = wait_for_mac_in_table(
            run_show, device, evpn_name, smoke_mac,
            timeout_sec=float(timeout),
            interval_sec=float(poll_interval),
        )
        result["steps"].append({
            "action": "poll_mac",
            "found": mac_val.passed,
            "poll_elapsed_sec": round(mac_val.elapsed_sec, 2),
            "polls": mac_val.attempts,
        })

        result["pass"] = mac_val.passed
        if mac_val.passed:
            result["detail"] = (
                f"L2 path verified: MAC {smoke_mac} learned on "
                f"{evpn_name} in {mac_val.elapsed_sec:.2f}s "
                f"({mac_val.attempts} polls)"
            )
        else:
            result["detail"] = (
                f"L2 path BROKEN: MAC {smoke_mac} never appeared in "
                f"{evpn_name} mac-table after {mac_val.elapsed_sec:.1f}s "
                f"({mac_val.attempts} polls). "
                f"Check: DNAAS BD, DUT AC state, VLAN tags, Spirent port link."
            )

    except Exception as exc:
        result["detail"] = f"Smoke test exception: {exc}"
        result["steps"].append({"action": "exception", "error": str(exc)})

    finally:
        try:
            _run_spirent_cmd(tool, ["stop"], timeout=10)
        except Exception:
            pass
        try:
            _run_spirent_cmd(tool, ["remove-stream", "--name", stream_name], timeout=10)
        except Exception:
            pass
        if not skip_post_cleanup:
            try:
                out = run_show(device, "clear evpn mac-table")
                _fail = ("ERROR", "Unknown", "Invalid", "Ambiguous", "Incomplete")
                if any(m in out for m in _fail):
                    run_show(device, f"clear evpn mac-table instance {evpn_name}")
            except Exception:
                pass

        result["elapsed_sec"] = round(time.time() - t0, 2)

    return result


def run_preflight(
    vlans: Optional[List[int]] = None,
    require_spirent: bool = False,
    run_show: Optional[RunShowFn] = None,
    device: Optional[str] = None,
    evpn_name: Optional[str] = None,
    ac_vlan: Optional[int] = None,
    outer_vlan: Optional[int] = None,
    skip_smoke_test: bool = False,
    dut_mac: Optional[str] = None,
    require_evpn_peers: bool = True,
    ac_interface: Optional[str] = None,
    port_mode: bool = False,
    fabric_vlan: Optional[int] = None,
) -> Dict[str, Any]:
    """Full Spirent pre-flight: session + DNAAS paths + BGP peers + L2 smoke test.

    Args:
        vlans: VLANs to check DNAAS path readiness for.
        require_spirent: If True, preflight fails when Spirent is unavailable.
                         If False, warnings are issued but tests can proceed
                         with TrafficMethod.MANUAL fallback.
        run_show: Device SSH function (required for BGP + smoke test).
        device: DUT device name (required for BGP + smoke test).
        evpn_name: EVPN instance name for MAC table check.
        ac_vlan: Inner VLAN for the AC (smoke test sends on this VLAN).
        outer_vlan: Outer VLAN for Q-in-Q (DNAAS transport).
        skip_smoke_test: Skip the L2 smoke test (e.g., during dry-run).
        dut_mac: DUT interface MAC for unicast dst (avoids DNAAS LLP).
        require_evpn_peers: If True, block when zero EVPN peers ESTABLISHED.
                            If False, downgrade to WARN (for PW-only tests).

    Returns:
        {
            "pass": bool,
            "spirent_available": bool,
            "spirent": {...session check...},
            "dnaas_paths": [...per-vlan results...],
            "bgp_check": {...peer status...},
            "smoke_test": {...L2 path result...},
            "warnings": [...],
            "traffic_method": "spirent" | "manual",
        }
    """
    result: Dict[str, Any] = {
        "pass": True,
        "spirent_available": False,
        "warnings": [],
        "traffic_method": "manual",
    }

    # -- Layer 1: Session health --
    session = check_spirent_session()
    result["spirent"] = session
    result["spirent_available"] = session.get("available", False)

    if not session.get("available"):
        msg = f"Spirent unavailable: {session.get('reason')}"
        if require_spirent:
            result["pass"] = False
            result["warnings"].append(f"[FAIL] {msg}")
        else:
            result["warnings"].append(
                f"[WARN] {msg}; tests will use MANUAL traffic method"
            )
        return result
    else:
        result["traffic_method"] = "spirent"

    # -- Layer 2: DNAAS path check --
    if vlans and session.get("available"):
        tool = Path(session["tool_path"])
        dnaas_results = []
        for vlan in vlans:
            dnaas = check_dnaas_path(vlan, tool)
            dnaas_results.append(dnaas)
            if not dnaas.get("ready"):
                result["warnings"].append(
                    f"[WARN] DNAAS path not ready for VLAN {vlan}: "
                    f"{dnaas.get('reason', 'unknown')}"
                )
        result["dnaas_paths"] = dnaas_results

    # -- Layer 3: BGP peer state (needs run_show + device) --
    # BLOCK if ZERO EVPN peers are established.
    # WARN (but allow) if some peers are down but at least one is up.
    if run_show and device:
        bgp_check = check_bgp_peers_established(run_show, device)
        result["bgp_check"] = bgp_check
        est = bgp_check.get("established", 0)
        total = bgp_check.get("total", 0)
        not_est = bgp_check.get("not_established", [])
        result["bgp_established_count"] = est
        result["bgp_total_count"] = total

        if total == 0 and require_evpn_peers:
            result["pass"] = False
            result["warnings"].append(
                "[FAIL] No BGP L2VPN EVPN peers configured -- test BLOCKED"
            )
        elif total == 0:
            result["warnings"].append(
                "[WARN] No BGP L2VPN EVPN peers configured (not required for this test)"
            )
        elif est == 0 and require_evpn_peers:
            result["pass"] = False
            down_list = ", ".join(
                f"{n['ip']}={n.get('state', '?')}" for n in not_est[:3]
            )
            result["warnings"].append(
                f"[FAIL] Zero EVPN peers ESTABLISHED ({total} configured): "
                f"{down_list} -- test BLOCKED"
            )
        elif est == 0:
            down_list = ", ".join(
                f"{n['ip']}={n.get('state', '?')}" for n in not_est[:3]
            )
            result["warnings"].append(
                f"[WARN] Zero EVPN peers ESTABLISHED ({total} configured): "
                f"{down_list} (not required for this test)"
            )
        elif not_est:
            down_list = ", ".join(
                f"{n['ip']}={n.get('state', '?')}" for n in not_est[:3]
            )
            result["warnings"].append(
                f"[WARN] {est}/{total} EVPN peers ESTABLISHED "
                f"(down: {down_list})"
            )
            result["bgp_partial"] = True

    # -- Layer 4: L2 smoke test (the real proof) --
    if (
        run_show and device and evpn_name and ac_vlan
        and not skip_smoke_test
        and session.get("available")
    ):
        smoke = smoke_test_l2_path(
            run_show, device, evpn_name, ac_vlan,
            outer_vlan=outer_vlan,
            dut_mac=dut_mac,
            ac_interface=ac_interface,
            port_mode=port_mode,
            fabric_vlan=fabric_vlan,
        )
        result["smoke_test"] = smoke
        if not smoke["pass"]:
            result["pass"] = False
            result["warnings"].append(
                f"[FAIL] L2 smoke test FAILED: {smoke['detail']}"
            )
        else:
            result["warnings"].append(
                f"[OK] L2 smoke test passed: MAC learned in "
                f"{smoke.get('elapsed_sec', '?')}s"
            )

    return result
