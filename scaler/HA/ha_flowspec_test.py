#!/usr/bin/env python3
"""
ha_flowspec_test.py -- FlowSpec VPN HA Test Orchestrator (SW-236398)

Runs all 15 SW-236398 test cases: injects 200 FlowSpec rules via Spirent BGP (or ExaBGP fallback),
triggers HA events via SSH, polls recovery, produces before/after diffs and per-test reports.

Usage:
    python3 ha_flowspec_test.py --device PE-4 [--tests test_01,test_02] [--dry-run]
    python3 ha_flowspec_test.py --device PE-4 --test test_01   # Single test

Requires: paramiko, spirent_tool.py, SCALER db devices.json
"""

import argparse
import base64
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HA_DIR = Path(__file__).parent
TEST_DEFS = HA_DIR / "test_definitions" / "sw_236398.json"

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]|\x1b\[\d*F')


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences so saved evidence is plain text."""
    if not isinstance(text, str):
        return text
    return _ANSI_RE.sub('', text)
RESULTS_DIR = HA_DIR / "test_results"
SCALER_DB = Path.home() / "SCALER" / "db" / "devices.json"
SPIRENT_TOOL = Path.home() / "SCALER" / "SPIRENT" / "spirent_tool.py"
BGP_TOOL = Path.home() / "SCALER" / "FLOWSPEC_VPN" / "exabgp" / "bgp_tool.py"
ACTIVE_SESSION = Path.home() / "SCALER" / "HA" / "active_ha_session.json"

# Defaults for PE-4 — VLAN 219 has a working DNAAS BD path (fabric VLAN 213, g_yor_v213).
# VLAN 212 has NO BD and will fail unless dnaas fix is run first.
DEFAULT_VLAN = 219
SPIRENT_LEARNING = Path.home() / ".spirent_learning.json"
DEFAULT_SPIRENT_IP = "49.49.49.1"
DEFAULT_DUT_IP = "49.49.49.4"
DEFAULT_AS = 65200
# STC BgpRouterConfig DutAsNum supports 0-65535 only; use 64512 for Spirent test
DEFAULT_DUT_AS = 64512
FLOWSPEC_RULE_COUNT = 200


# Device alias: user says "PE-4" but DB has "YOR_CL_PE-4"
DEVICE_ALIASES = {"PE-4": "YOR_CL_PE-4", "PE4": "YOR_CL_PE-4"}

try:
    from .ha_ssh import run_ssh_shell, ssh_quick_check
except ImportError:
    from ha_ssh import run_ssh_shell, ssh_quick_check


def load_device(hostname: str) -> dict:
    """Load device from SCALER db (devices.json)."""
    if not SCALER_DB.exists():
        raise FileNotFoundError(f"SCALER db not found: {SCALER_DB}")
    hostname = DEVICE_ALIASES.get(hostname.upper(), hostname)
    with open(SCALER_DB) as f:
        data = json.load(f)
    for d in data.get("devices", []):
        if d.get("hostname", "").upper() == hostname.upper():
            pw = d.get("password", "dnroot")
            if pw:
                try:
                    pw = base64.b64decode(pw).decode("utf-8")
                except Exception:
                    pass
            return {
                "hostname": d["hostname"],
                "ip": d["ip"],
                "username": d.get("username", "dnroot"),
                "password": pw,
            }
    raise ValueError(f"Device {hostname} not found in {SCALER_DB}")


def load_test_definitions() -> dict:
    """Load SW-236398 test definitions."""
    if not TEST_DEFS.exists():
        raise FileNotFoundError(f"Test definitions not found: {TEST_DEFS}")
    with open(TEST_DEFS) as f:
        return json.load(f)


def run_ssh_command(ip: str, username: str, password: str, command: str, timeout: int = 30) -> tuple[str, str, int]:
    """Run a single command via SSH. Uses interactive shell (DNOS CLI requires it)."""
    out = run_ssh_shell(ip, username, password, [command], timeout=timeout)
    return out, "", 0


PID_LOCK = Path.home() / "SCALER" / "HA" / ".ha_orchestrator.pid"
PROGRESS_FILE = Path.home() / "SCALER" / "HA" / ".ha_progress.json"


def acquire_lock() -> bool:
    """Ensure only one orchestrator runs at a time. Kills stale instances."""
    if PID_LOCK.exists():
        try:
            old_pid = int(PID_LOCK.read_text().strip())
            if Path(f"/proc/{old_pid}").exists():
                print(f"[LOCK] Killing stale orchestrator PID {old_pid}")
                os.kill(old_pid, 9)
                time.sleep(1)
        except (ValueError, ProcessLookupError, PermissionError):
            pass
    PID_LOCK.parent.mkdir(parents=True, exist_ok=True)
    PID_LOCK.write_text(str(os.getpid()))
    return True


def release_lock():
    try:
        if PID_LOCK.exists() and PID_LOCK.read_text().strip() == str(os.getpid()):
            PID_LOCK.unlink()
    except Exception:
        pass


def detect_stale_session() -> dict | None:
    """Check if a previous session crashed (active_ha_session says active but PID is dead).
    Returns stale session data if found, None otherwise."""
    if not ACTIVE_SESSION.exists():
        return None
    try:
        with open(ACTIVE_SESSION) as f:
            sd = json.load(f)
        if not sd.get("active"):
            return None
        if PID_LOCK.exists():
            try:
                old_pid = int(PID_LOCK.read_text().strip())
                if Path(f"/proc/{old_pid}").exists():
                    return None
            except (ValueError, OSError):
                pass
        print(f"[STALE] Detected crashed session: {sd.get('flowspec_test_id', '?')} on {sd.get('system_name', '?')}")
        print(f"[STALE] Run dir: {sd.get('run_dir', '?')}")
        return sd
    except Exception:
        return None


def recover_stale_session(stale: dict) -> None:
    """Mark stale session as crashed. If LOFD test was in progress, warn about NCF."""
    stale["active"] = False
    stale["flowspec_test_active"] = False
    stale["crashed"] = True
    stale["crashed_at"] = datetime.utcnow().isoformat()
    try:
        with open(ACTIVE_SESSION, "w") as f:
            json.dump(stale, f, indent=2)
    except Exception:
        pass
    if stale.get("last_test_ha_type") == "lofd":
        print("[STALE] WARNING: Last test was LOFD (NCF admin-disable).")
        print("[STALE] NCF may still be disabled! Verify: show system | include NCF")
        print("[STALE] Recovery: configure -> system -> ncf 0 -> admin-state enabled -> commit")


def load_progress(run_dir: str) -> set:
    """Load set of completed test IDs from a previous run directory."""
    completed = set()
    if not PROGRESS_FILE.exists():
        return completed
    try:
        with open(PROGRESS_FILE) as f:
            data = json.load(f)
        if data.get("run_dir") == run_dir:
            completed = set(data.get("completed_tests", []))
    except Exception:
        pass
    return completed


def save_progress(run_dir: str, completed_tests: list[str], current_test: str = None) -> None:
    """Save progress for crash recovery. Written after each test completes."""
    try:
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        PROGRESS_FILE.write_text(json.dumps({
            "run_dir": run_dir,
            "completed_tests": completed_tests,
            "current_test": current_test,
            "updated_at": datetime.utcnow().isoformat(),
            "pid": os.getpid(),
        }, indent=2))
    except Exception:
        pass


def run_spirent(cmd: list[str], session_name: str = "ha_flowspec_pe4",
                timeout: int = 60) -> tuple[bool, str]:
    """Run spirent_tool.py. Returns (success, output).

    Default timeout reduced from 120s to 60s to avoid hanging on zombie sessions.
    Cleanup/connect operations get 30s; bgp-peer gets 90s (waits for ESTABLISHED).
    """
    if cmd and cmd[0] in ("cleanup", "list-sessions"):
        timeout = 30
    elif cmd and cmd[0] == "bgp-peer":
        timeout = 90
    full = [sys.executable, str(SPIRENT_TOOL)] + cmd
    try:
        r = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
        out = (r.stdout or "") + (r.stderr or "")
        return r.returncode == 0, out
    except subprocess.TimeoutExpired:
        return False, f"Timeout ({timeout}s) running: {' '.join(cmd[:3])}"
    except Exception as e:
        return False, str(e)


def run_bgp_tool(cmd: list[str]) -> tuple[bool, str]:
    """Run bgp_tool.py (ExaBGP). Returns (success, output)."""
    full = [sys.executable, str(BGP_TOOL)] + cmd
    try:
        r = subprocess.run(full, capture_output=True, text=True, timeout=30)
        out = (r.stdout or "") + (r.stderr or "")
        return r.returncode == 0, out
    except Exception as e:
        return False, str(e)


def parse_flowspec_route_count(output: str) -> int:
    """Extract FlowSpec route count from show bgp ipv4 flowspec-vpn (routes or summary) output."""
    m = re.search(r"\d+d\d+h\d+m\s+(\d+)\s*$", output, re.M)
    if m:
        return int(m.group(1))
    m = re.search(r"\d+:\d+:\d+\s+(\d+)\s*$", output, re.M)
    if m:
        return int(m.group(1))
    m = re.search(r"PfxAccepted\s*(\d+)", output, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s+routes?", output, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"Total.*?(\d+)", output, re.I)
    if m:
        return int(m.group(1))
    # Count prefix lines (*> or similar)
    prefixes = re.findall(r"\d+\.\d+\.\d+\.\d+/\d+", output)
    if prefixes:
        return len(prefixes)
    return -1


def parse_bgp_state(output: str) -> str:
    """Extract BGP session state (Established, Idle, etc.)."""
    if "Established" in output or "established" in output:
        return "Established"
    for s in ("Idle", "Active", "Connect", "OpenSent", "OpenConfirm"):
        if s in output:
            return s
    return "Unknown"


def parse_flowspec_ncp_counters(output: str) -> dict:
    """Parse show flowspec ncp <id> for installed count and aggregate packet/byte counters."""
    result = {"installed": 0, "packets": 0, "bytes": 0}
    m = re.search(r"Installed\s*:\s*(\d+)", output, re.I)
    if m:
        result["installed"] = int(m.group(1))
    else:
        result["installed"] = output.lower().count("status: installed")
    for m in re.finditer(r"Packets\s*:\s*(\d+)", output, re.I):
        result["packets"] += int(m.group(1))
    for m in re.finditer(r"Bytes\s*:\s*(\d+)", output, re.I):
        result["bytes"] += int(m.group(1))
    return result


def parse_tcam_usage(output: str) -> dict:
    """Parse show system npu-resources resource-type flowspec for TCAM capacity.
    Table format: | NCP | IPv4 Received | IPv4 Installed | IPv4 HW used/total | IPv6 ... |
    Data rows:    | 6   | 12000         | 12000          | 12000/12000        | ...      |
    """
    result = {"installed": 0, "total": 0, "percent": 0.0,
              "ipv6_installed": 0, "ipv6_total": 0}
    for line in output.split("\n"):
        if not re.match(r"\s*\|\s*\d+\s*\|", line):
            continue
        hw_match = re.search(r"(\d+)/(\d+)", line)
        if hw_match:
            inst = int(hw_match.group(1))
            total = int(hw_match.group(2))
            if result["total"] == 0 or inst > result["installed"]:
                result["installed"] = inst
                result["total"] = total
            hw_matches = re.findall(r"(\d+)/(\d+)", line)
            if len(hw_matches) >= 2:
                result["ipv6_installed"] = int(hw_matches[1][0])
                result["ipv6_total"] = int(hw_matches[1][1])
            break
    if result["total"] > 0:
        result["percent"] = round(result["installed"] / result["total"] * 100, 1)
    return result


def parse_system_type(output: str) -> dict:
    """Parse show system output. Returns device_mode, system_type, active_ncc_id, standby_ncc_id."""
    result = {"device_mode": "standalone", "system_type": "", "active_ncc_id": None, "standby_ncc_id": None}
    m = re.search(r"System Type:\s*(\S+)", output, re.I)
    if m:
        result["system_type"] = m.group(1).strip()
        if "CL-" in result["system_type"].upper():
            result["device_mode"] = "cluster"
            for line in output.split("\n"):
                if "active-up" in line or "standby-up" in line:
                    ncc_m = re.search(r"NCC-(\d+)", line)
                    if not ncc_m:
                        ncc_m = re.search(r"\|\s*NCC\s*\|\s*(\d+)\s*\|", line)
                    if ncc_m:
                        ncc_id = int(ncc_m.group(1))
                        if "active-up" in line:
                            result["active_ncc_id"] = ncc_id
                        elif "standby-up" in line:
                            result["standby_ncc_id"] = ncc_id
        elif "SA-" in result["system_type"].upper():
            result["device_mode"] = "standalone"
    return result


def parse_process_restart_counts(output: str) -> dict[str, dict]:
    """Parse 'show system details' output to extract per-process restart counts.
    Returns dict keyed by 'node_type-node_id/container/process' -> {restarts: int, state: str, pid: int}.

    Handles the hierarchical output format:
      Node: NCC-0 (active-up)
        Container: routing-engine
          Process: routing:bgpd  PID: 12345  State: running  Restarts: 0
    """
    result = {}
    current_node = ""
    current_container = ""

    for line in output.split("\n"):
        node_m = re.match(r"\s*(?:Node|Type)\s*:\s*(NCC|NCP|NCF|NCM)-?(\d+)", line, re.I)
        if not node_m:
            node_m = re.match(r"\s*\|\s*(NCC|NCP|NCF|NCM)\s*\|\s*(\d+)\s*\|", line, re.I)
        if node_m:
            current_node = f"{node_m.group(1).upper()}-{node_m.group(2)}"
            continue

        cont_m = re.match(r"\s*Container\s*:\s*(\S+)", line, re.I)
        if cont_m:
            current_container = cont_m.group(1)
            continue

        proc_m = re.search(
            r"Process\s*:\s*(\S+).*?Restarts?\s*:\s*(\d+)",
            line, re.I,
        )
        if not proc_m:
            proc_m = re.search(
                r"(\S+)\s+\d+\s+(running|stopped|starting)\s+\S+\s+(\d+)",
                line, re.I,
            )
        if proc_m:
            proc_name = proc_m.group(1)
            restarts = int(proc_m.group(2)) if proc_m.lastindex >= 2 else 0
            state = ""
            pid = 0
            state_m = re.search(r"State\s*:\s*(\S+)", line, re.I)
            if state_m:
                state = state_m.group(1)
            pid_m = re.search(r"PID\s*:\s*(\d+)", line, re.I)
            if pid_m:
                pid = int(pid_m.group(1))
            restart_m = re.search(r"Restarts?\s*:\s*(\d+)", line, re.I)
            if restart_m:
                restarts = int(restart_m.group(1))

            key = f"{current_node}/{current_container}/{proc_name}" if current_node else proc_name
            result[key] = {"restarts": restarts, "state": state, "pid": pid}

    return result


def detect_collateral_damage(before_procs: dict, after_procs: dict,
                              intentional_process: str, ha_type: str) -> list[dict]:
    """Compare process restart counts before/after HA event.
    Returns list of unexpectedly restarted processes (collateral damage).

    intentional_process: the process/component that was SUPPOSED to restart
                         (e.g. 'routing:bgpd', 'routing-engine', 'NCC-0')
    ha_type: test ha_type for context (process_restart, container_restart, ncc_cold_restart, etc.)
    """
    collateral = []
    for key, after_info in after_procs.items():
        before_info = before_procs.get(key)
        if not before_info:
            continue
        restart_delta = after_info["restarts"] - before_info["restarts"]
        if restart_delta <= 0:
            continue

        is_intentional = False
        key_lower = key.lower()
        intent_lower = intentional_process.lower()

        if intent_lower in key_lower:
            is_intentional = True
        elif ha_type in ("container_restart",) and intent_lower in key_lower:
            is_intentional = True
        elif ha_type in ("ncc_cold_restart", "ncc_failover", "ncc_switchover"):
            is_intentional = True
        elif ha_type in ("ncp_force_restart",) and "NCP" in key.upper():
            is_intentional = True
        elif ha_type == "system_restart":
            is_intentional = True
        elif ha_type == "lofd" and "NCF" in key.upper():
            is_intentional = True

        if not is_intentional:
            collateral.append({
                "process": key,
                "restart_delta": restart_delta,
                "before_restarts": before_info["restarts"],
                "after_restarts": after_info["restarts"],
                "state_after": after_info.get("state", ""),
            })

    return collateral


def parse_alarms(output: str) -> list[dict]:
    """Parse 'show system alarms' output. Returns list of {severity, source, description, timestamp}."""
    alarms = []
    for line in output.split("\n"):
        m = re.match(
            r"\s*(\w+)\s+(\S+)\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(.*)",
            line,
        )
        if m:
            alarms.append({
                "severity": m.group(1),
                "source": m.group(2),
                "timestamp": m.group(3),
                "description": m.group(4).strip(),
            })
            continue
        if re.search(r"(critical|major|minor|warning)", line, re.I) and "|" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 3:
                alarms.append({
                    "severity": parts[0],
                    "source": parts[1] if len(parts) > 1 else "",
                    "timestamp": parts[2] if len(parts) > 2 else "",
                    "description": parts[3] if len(parts) > 3 else "",
                })
    return alarms


def diff_alarms(before_alarms: list[dict], after_alarms: list[dict]) -> dict:
    """Compare alarm lists. Returns {new_alarms: [...], cleared_alarms: [...], verdict: PASS|WARNING|FAIL}."""
    before_set = {(a["severity"], a["source"], a["description"]) for a in before_alarms}
    after_set = {(a["severity"], a["source"], a["description"]) for a in after_alarms}

    new_keys = after_set - before_set
    cleared_keys = before_set - after_set

    new_alarms = [a for a in after_alarms if (a["severity"], a["source"], a["description"]) in new_keys]
    cleared_alarms = [a for a in before_alarms if (a["severity"], a["source"], a["description"]) in cleared_keys]

    verdict = "PASS"
    for a in new_alarms:
        if a["severity"].lower() in ("critical", "major"):
            verdict = "FAIL"
            break
        if a["severity"].lower() in ("minor", "warning"):
            verdict = "WARNING" if verdict == "PASS" else verdict

    return {"new_alarms": new_alarms, "cleared_alarms": cleared_alarms, "verdict": verdict}


def parse_core_dumps(output: str) -> list[dict]:
    """Parse 'show system core-dumps' or ls /var/crash output for core dump files.
    Returns list of {filename, timestamp, process}."""
    cores = []
    for line in output.split("\n"):
        m = re.search(r"(core\.\S+|.*\.core\S*)", line)
        if m:
            filename = m.group(1).strip()
            proc_m = re.search(r"core\.(\w+)", filename)
            ts_m = re.search(r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2})", line)
            cores.append({
                "filename": filename,
                "process": proc_m.group(1) if proc_m else "unknown",
                "timestamp": ts_m.group(1) if ts_m else "",
            })
    return cores


def parse_process_memory(output: str) -> dict[str, dict]:
    """Parse 'show system details' for per-process memory (PHY-Memory/Mem%).
    Returns dict keyed by same key format as parse_process_restart_counts -> {mem_kb: int, mem_pct: float}."""
    result = {}
    current_node = ""
    current_container = ""

    for line in output.split("\n"):
        node_m = re.match(r"\s*(?:Node|Type)\s*:\s*(NCC|NCP|NCF|NCM)-?(\d+)", line, re.I)
        if not node_m:
            node_m = re.match(r"\s*\|\s*(NCC|NCP|NCF|NCM)\s*\|\s*(\d+)\s*\|", line, re.I)
        if node_m:
            current_node = f"{node_m.group(1).upper()}-{node_m.group(2)}"
            continue
        cont_m = re.match(r"\s*Container\s*:\s*(\S+)", line, re.I)
        if cont_m:
            current_container = cont_m.group(1)
            continue

        proc_m = re.search(r"Process\s*:\s*(\S+)", line, re.I)
        if not proc_m:
            proc_m = re.search(r"^(\S+)\s+\d+\s+(?:running|stopped)", line, re.I)
        if proc_m:
            proc_name = proc_m.group(1)
            key = f"{current_node}/{current_container}/{proc_name}" if current_node else proc_name
            mem_kb = 0
            mem_pct = 0.0
            kb_m = re.search(r"(?:PHY-Memory|Memory)\s*:\s*(\d+)", line, re.I)
            if kb_m:
                mem_kb = int(kb_m.group(1))
            pct_m = re.search(r"Mem%?\s*:\s*([\d.]+)", line, re.I)
            if pct_m:
                mem_pct = float(pct_m.group(1))
            result[key] = {"mem_kb": mem_kb, "mem_pct": mem_pct}

    return result


def detect_memory_leaks(before_mem: dict, after_mem: dict,
                        threshold_pct: float = 25.0) -> list[dict]:
    """Compare per-process memory before/after. Flag processes with significant growth.
    threshold_pct: percentage increase that triggers a WARNING (default 25%)."""
    leaks = []
    for key, after_info in after_mem.items():
        before_info = before_mem.get(key)
        if not before_info or before_info["mem_kb"] == 0:
            continue
        delta_kb = after_info["mem_kb"] - before_info["mem_kb"]
        if delta_kb <= 0:
            continue
        growth_pct = (delta_kb / before_info["mem_kb"]) * 100
        if growth_pct >= threshold_pct:
            leaks.append({
                "process": key,
                "before_kb": before_info["mem_kb"],
                "after_kb": after_info["mem_kb"],
                "delta_kb": delta_kb,
                "growth_pct": round(growth_pct, 1),
            })
    leaks.sort(key=lambda x: x["growth_pct"], reverse=True)
    return leaks


def parse_bfd_sessions(output: str) -> list[dict]:
    """Parse 'show bfd sessions' output. Returns list of {neighbor, state, interface, uptime}."""
    sessions = []
    for line in output.split("\n"):
        m = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+(\S+)\s+(Up|Down|Init|AdminDown)", line, re.I)
        if m:
            sessions.append({
                "neighbor": m.group(1),
                "interface": m.group(2),
                "state": m.group(3),
            })
            continue
        if "|" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 3:
                ip_m = re.search(r"\d+\.\d+\.\d+\.\d+", parts[0])
                if ip_m:
                    state = "Unknown"
                    for p in parts:
                        if p.lower() in ("up", "down", "init", "admindown"):
                            state = p
                            break
                    sessions.append({
                        "neighbor": ip_m.group(0),
                        "interface": parts[1] if len(parts) > 1 else "",
                        "state": state,
                    })
    return sessions


def diff_bfd_sessions(before: list[dict], after: list[dict]) -> dict:
    """Compare BFD sessions. Returns {changed: [...], lost: [...], verdict: PASS|WARNING|FAIL}."""
    before_map = {s["neighbor"]: s for s in before}
    after_map = {s["neighbor"]: s for s in after}
    changed = []
    lost = []
    for nbr, b_info in before_map.items():
        a_info = after_map.get(nbr)
        if not a_info:
            lost.append({"neighbor": nbr, "before_state": b_info["state"], "after_state": "GONE"})
        elif b_info["state"] != a_info["state"]:
            changed.append({"neighbor": nbr, "before_state": b_info["state"], "after_state": a_info["state"]})

    verdict = "PASS"
    for c in changed + lost:
        if c.get("after_state") in ("Down", "GONE"):
            verdict = "FAIL"
            break
    if verdict == "PASS" and (changed or lost):
        verdict = "WARNING"
    return {"changed": changed, "lost": lost, "verdict": verdict}


def parse_interface_states(output: str) -> dict[str, dict]:
    """Parse 'show interfaces description'. Returns dict keyed by intf_name -> {admin, oper, description}."""
    result = {}
    for line in output.split("\n"):
        m = re.match(r"\s*(\S+)\s+(up|down|testing)\s+(up|down|testing|dormant)\s*(.*)", line, re.I)
        if m:
            result[m.group(1)] = {
                "admin": m.group(2).lower(),
                "oper": m.group(3).lower(),
                "description": m.group(4).strip(),
            }
            continue
        if "|" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 3 and not parts[0].lower().startswith("interface"):
                result[parts[0]] = {
                    "admin": parts[1].lower() if len(parts) > 1 else "",
                    "oper": parts[2].lower() if len(parts) > 2 else "",
                    "description": parts[3] if len(parts) > 3 else "",
                }
    return result


def diff_interface_states(before: dict, after: dict) -> dict:
    """Compare interface states. Returns {went_down: [...], came_up: [...], verdict}."""
    went_down = []
    came_up = []
    for intf, b_info in before.items():
        a_info = after.get(intf)
        if not a_info:
            continue
        if b_info["oper"] == "up" and a_info["oper"] != "up":
            went_down.append({"interface": intf, "before": b_info["oper"], "after": a_info["oper"]})
        elif b_info["oper"] != "up" and a_info["oper"] == "up":
            came_up.append({"interface": intf, "before": b_info["oper"], "after": a_info["oper"]})

    verdict = "PASS"
    if went_down:
        has_critical = any(
            not i["interface"].startswith("mgmt-") for i in went_down
        )
        verdict = "FAIL" if has_critical else "WARNING"
    return {"went_down": went_down, "came_up": came_up, "verdict": verdict}


def compute_ncp_content_hash(output: str) -> str:
    """Compute a hash of NCP flowspec rule content (not just counts).
    Strips counters/timestamps that change between runs, hashes the rule structure."""
    stable_lines = []
    for line in output.split("\n"):
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"Packets\s*:\s*\d+", "Packets: X", line)
        line = re.sub(r"Bytes\s*:\s*\d+", "Bytes: X", line)
        line = re.sub(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", "TIMESTAMP", line)
        stable_lines.append(line)
    content = "\n".join(stable_lines)
    return hashlib.md5(content.encode()).hexdigest()


def compute_config_hash(output: str) -> str:
    """Compute hash of running config for drift detection. Strips timestamps and session IDs."""
    lines = []
    for line in output.split("\n"):
        if re.match(r"\s*!?\s*Last commit", line, re.I):
            continue
        if re.match(r"\s*!?\s*commit-id", line, re.I):
            continue
        lines.append(line)
    return hashlib.md5("\n".join(lines).encode()).hexdigest()


def validate_test_definitions(defs: dict) -> list[str]:
    """Validate test definitions JSON. Returns list of error messages (empty = valid)."""
    errors = []
    if "tests" not in defs:
        errors.append("Missing 'tests' key in test definitions")
        return errors
    required_fields = {"id", "name", "ha_type"}
    recommended_fields = {"ha_command", "max_recovery_sec", "expected_recovery_sec"}
    for i, t in enumerate(defs["tests"]):
        for field in required_fields:
            if field not in t:
                errors.append(f"Test {i} missing required field '{field}'")
        for field in recommended_fields:
            if field not in t and not t.get("requires_manual") and not t.get("skip_reason"):
                errors.append(f"Test {i} ({t.get('id', '?')}) missing recommended field '{field}'")
        if "ha_command" not in t and "ha_commands" not in t and not t.get("requires_manual") and not t.get("requires_config_mode"):
            errors.append(f"Test {i} ({t.get('id', '?')}) has no ha_command, ha_commands, requires_manual, or requires_config_mode")
    return errors


class FlowSpecHATest:
    """Orchestrator for FlowSpec VPN HA tests."""

    def __init__(self, device_name: str, run_dir: Path, session_name: str = "ha_flowspec_pe4", dry_run: bool = False, standby_ncc_ip: str = None):
        self.device = load_device(device_name)
        self.run_dir = run_dir
        self.session_name = session_name
        self.dry_run = dry_run
        self.route_source = "spirent"  # or "exabgp" or "preexisting"
        self.effective_rule_count = FLOWSPEC_RULE_COUNT
        self.spirent_peer_ip = DEFAULT_SPIRENT_IP
        self.dut_neighbor_ip = DEFAULT_DUT_IP
        self.vlan = DEFAULT_VLAN
        self.log_lines = []
        self.device_mode = "standalone"  # cluster | standalone
        self.system_type = ""
        self.active_ncc_id = None
        self.standby_ncc_id = None
        self.standby_ncc_ip = standby_ncc_ip  # For CL: use when triggering NCC restart to avoid SSH loss
        self.spirent_baseline = {}
        self.spirent_available = False
        self.spirent_reachable = True  # False when spirent_poll_stats returns error after retries
        self.ncp_id_cached = None
        self.system_name = None  # Device Lock: captured at startup, verified after HA events
        self.image_version = "unknown"
        self._last_trigger_output = ""
        self._trigger_timestamp = ""
        self.stop_on_fail = False
        self._resolve_vlan_from_learning()

    def _resolve_vlan_from_learning(self) -> None:
        """Pick READY VLAN from spirent_learning.json for this device. Fall back to DEFAULT_VLAN."""
        if not SPIRENT_LEARNING.exists():
            return
        try:
            with open(SPIRENT_LEARNING) as f:
                data = json.load(f)
            profiles = data.get("known_stream_profiles", {})
            hostname = self.device.get("hostname", "").lower()
            device_core = (hostname.split("_")[-1] if "_" in hostname else hostname).replace("-", "")
            for key, prof in profiles.items():
                if prof.get("status") == "READY" and device_core in key.replace("_", "").replace("-", ""):
                    vlan = prof.get("user_vlan")
                    if vlan is not None:
                        self.vlan = int(vlan)
                        self.log(f"VLAN from spirent_learning: {self.vlan} (profile {key})")
                        return
        except Exception:
            pass

    def log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        self.log_lines.append(line)
        print(line, flush=True)

    def _all_ips(self) -> list[str]:
        """Return all known management IPs to try: primary first, then standby, then any extras."""
        ips = [self.device["ip"]]
        if self.standby_ncc_ip and self.standby_ncc_ip not in ips:
            ips.append(self.standby_ncc_ip)
        for extra in getattr(self, "_extra_ips", []):
            if extra not in ips:
                ips.append(extra)
        return ips

    def _refresh_ip_from_db(self):
        """Re-read devices.json for updated IP (DHCP may reassign after cold restart)."""
        try:
            with open(SCALER_DB) as f:
                data = json.load(f)
            hostname = self.device["hostname"].upper()
            for d in data.get("devices", []):
                if d.get("hostname", "").upper() == hostname:
                    new_ip = d.get("ip", "")
                    if new_ip and new_ip != self.device["ip"]:
                        self.log(f"  DB refresh: IP changed {self.device['ip']} -> {new_ip}")
                        if not hasattr(self, "_extra_ips"):
                            self._extra_ips = []
                        if self.device["ip"] not in self._extra_ips:
                            self._extra_ips.append(self.device["ip"])
                        self.device["ip"] = new_ip
                    return
        except Exception as e:
            self.log(f"  DB refresh failed: {e}")

    def _refresh_nce_ips(self):
        """After reconnect, parse 'show interfaces management' to refresh NCE IP map.
        Stores ALL NCC IPs in _extra_ips so _all_ips() covers every NCC after switchovers."""
        try:
            out = self.dut_run("show interfaces management", timeout=15, retries=1)
            nce_map = {}
            for line in out.split("\n"):
                m = re.search(r"(mgmt-ncc-\d+|mgmt-ncp-\d+|mgmt-ncf-\d+|mgmt0)\s+.*?(\d+\.\d+\.\d+\.\d+)", line)
                if m:
                    nce_map[m.group(1)] = m.group(2)
            if nce_map:
                self.log(f"  NCE IP map refreshed: {nce_map}")
                if not hasattr(self, "_extra_ips"):
                    self._extra_ips = []
                for k, v in nce_map.items():
                    if ("ncc" in k or k == "mgmt0") and v not in self._extra_ips:
                        self._extra_ips.append(v)
                    if "ncc" in k and v != self.device["ip"]:
                        self.standby_ncc_ip = v
                        self.log(f"  Updated standby NCC IP: {v} ({k})")
        except Exception as e:
            self.log(f"  NCE IP refresh failed (non-fatal): {e}")

    def _reconnect_any_ip(self, command: str, max_wait: int = 120, poll_interval: int = 5) -> tuple[str, str]:
        """Try SSH to any known IP until one responds. Returns (output, connected_ip).
        Rotates between primary and standby IPs. After half the wait time, re-reads
        devices.json for DHCP-updated IPs. After reconnect, refreshes NCE IP map."""
        ips = self._all_ips()
        start = time.time()
        attempt = 0
        db_refreshed = False
        while time.time() - start < max_wait:
            elapsed = time.time() - start
            if not db_refreshed and elapsed > max_wait * 0.4:
                self._refresh_ip_from_db()
                ips = self._all_ips()
                db_refreshed = True
            ip = ips[attempt % len(ips)]
            ok, out = ssh_quick_check(ip, self.device["username"], self.device["password"], command)
            if ok:
                if ip != self.device["ip"]:
                    self.log(f"  Reconnected via alternate IP {ip} (was {self.device['ip']})")
                    self.device["ip"] = ip
                self._refresh_nce_ips()
                return out, ip
            attempt += 1
            time.sleep(poll_interval)
        raise TimeoutError(f"Device unreachable on any IP ({ips}) after {max_wait}s")

    def capture_system_identity(self):
        """Capture the device's System Name at startup for identity verification (Device Lock)."""
        out = self.dut_run("show system version", timeout=15)
        m = re.search(r"System Name\s*:\s*(\S+)", out)
        if m:
            self.system_name = m.group(1).strip()
            self.log(f"Device Lock: System Name = {self.system_name}")
        else:
            sn_m = re.search(r"System Serial Number\s*:\s*(\S+)", out)
            if sn_m:
                self.system_name = sn_m.group(1).strip()
                self.log(f"Device Lock: Serial Number = {self.system_name}")
            else:
                self.log("WARNING: Could not extract System Name for device lock")

    def verify_device_identity(self) -> bool:
        """Verify we're still connected to the same device after HA events (DHCP IP change safety).
        Returns True if identity matches, False if mismatch detected."""
        if not self.system_name:
            return True
        try:
            out = self.dut_run("show system version", timeout=15, retries=1)
            m = re.search(r"System Name\s*:\s*(\S+)", out)
            if not m:
                m = re.search(r"System Serial Number\s*:\s*(\S+)", out)
            if m:
                current = m.group(1).strip()
                if current == self.system_name:
                    self.log(f"  Identity OK: {current}")
                    return True
                else:
                    self.log(f"  IDENTITY MISMATCH! Expected '{self.system_name}' got '{current}'")
                    self.log(f"  ABORT: Management IP may have been reassigned to a different device!")
                    return False
            else:
                self.log("  WARNING: Could not verify identity (parse failed)")
                return True
        except Exception as e:
            self.log(f"  Identity check failed (SSH error, will retry later): {e}")
            return True

    def dut_run(self, command: str, timeout: int = 30, retries: int = 3) -> str:
        """Run show command on DUT via SSH. Retries on timeout (HA events can cause transient loss)."""
        delays = [5, 10, 20]
        last_err = None
        for attempt in range(retries):
            try:
                out, err, rc = run_ssh_command(
                    self.device["ip"],
                    self.device["username"],
                    self.device["password"],
                    command,
                    timeout=timeout,
                )
                return out + ("\n" + err if err else "")
            except (TimeoutError, OSError, Exception) as e:
                last_err = e
                if attempt < retries - 1:
                    wait = delays[min(attempt, len(delays) - 1)]
                    self.log(f"  SSH retry {attempt + 1}/{retries} in {wait}s ({e})")
                    time.sleep(wait)
                else:
                    raise
        raise last_err

    def dut_shell(self, commands: list[str], timeout: int = 60) -> str:
        """Run commands in interactive shell (for operational commands)."""
        return run_ssh_shell(
            self.device["ip"],
            self.device["username"],
            self.device["password"],
            commands,
            timeout=timeout,
        )

    def take_snapshot(self, label: str, commands: list[str]) -> dict:
        """Take snapshot of DUT state. Retries per-command on SSH timeout.
        All outputs are ANSI-stripped for clean evidence storage.
        Auto-captures: process restart counts + memory, alarms, BFD, interfaces, config hash."""
        snap = {"label": label, "timestamp": datetime.now().isoformat(), "commands": {}}
        for cmd in commands:
            try:
                snap["commands"][cmd] = strip_ansi(self.dut_run(cmd))
            except Exception as e:
                snap["commands"][cmd] = f"ERROR: {e}"
                self.log(f"  Snapshot command failed: {cmd[:50]}...")

        try:
            details_out = strip_ansi(self.dut_run("show system details", timeout=30))
            snap["commands"]["show system details"] = details_out
            snap["process_restart_counts"] = parse_process_restart_counts(details_out)
            snap["process_memory"] = parse_process_memory(details_out)
        except Exception as e:
            self.log(f"  Process restart/memory capture failed: {e}")
            snap["process_restart_counts"] = {}
            snap["process_memory"] = {}

        try:
            alarm_out = strip_ansi(self.dut_run("show system alarms", timeout=15))
            snap["commands"]["show system alarms"] = alarm_out
            snap["alarms"] = parse_alarms(alarm_out)
        except Exception as e:
            self.log(f"  Alarm capture failed: {e}")
            snap["alarms"] = []

        try:
            bfd_out = strip_ansi(self.dut_run("show bfd sessions", timeout=15))
            snap["commands"]["show bfd sessions"] = bfd_out
            snap["bfd_sessions"] = parse_bfd_sessions(bfd_out)
        except Exception as e:
            self.log(f"  BFD capture failed: {e}")
            snap["bfd_sessions"] = []

        try:
            intf_out = strip_ansi(self.dut_run("show interfaces description", timeout=15))
            snap["commands"]["show interfaces description"] = intf_out
            snap["interface_states"] = parse_interface_states(intf_out)
        except Exception as e:
            self.log(f"  Interface state capture failed: {e}")
            snap["interface_states"] = {}

        try:
            cfg_out = strip_ansi(self.dut_run(
                "show config protocols bgp | no-more", timeout=20))
            snap["config_hash"] = compute_config_hash(cfg_out)
            snap["commands"]["show config protocols bgp"] = cfg_out
        except Exception as e:
            self.log(f"  Config hash capture failed: {e}")
            snap["config_hash"] = ""

        return snap

    def setup_spirent(self) -> bool:
        """Connect, reserve, create device, BGP peer, inject FlowSpec rules, start traffic."""
        self.log("Phase 0: Cleaning zombie sessions before Spirent setup")
        cleanup_ok, cleanup_out = run_spirent(["cleanup", "--session-name", self.session_name])
        if cleanup_ok:
            self.log(f"  Old session cleaned: {cleanup_out[:100]}")
        time.sleep(1)

        sess_dir = Path.home() / "SCALER" / "SPIRENT" / "sessions"
        sess_dir.mkdir(exist_ok=True)
        sess_file = sess_dir / f"{self.session_name}.json"
        sess_file.write_text(json.dumps({
            "session_name": self.session_name,
            "session_id_on_server": f"{self.session_name} - dn_spirent",
            "lab_server": "il-auto-containers",
            "active": False, "port_reserved": False,
            "streams": [], "devices": [],
        }, indent=2))

        self.log(f"Setting up Spirent: connect + reserve (VLAN={self.vlan})")
        ok, out = run_spirent(["connect", "--session-name", self.session_name])
        if not ok:
            self.log(f"ERROR: Spirent connect failed: {out[:300]}")
            return False
        ok, out = run_spirent(["reserve", "--session-name", self.session_name])
        if not ok:
            if "reserved" in out.lower() or "could not be brought online" in out.lower():
                self.log("Port already reserved (reusing existing session)")
            else:
                self.log(f"ERROR: Spirent reserve failed: {out[:300]}")
                return False

        self.log(f"Creating Spirent BGP device: {self.spirent_peer_ip} -> {self.dut_neighbor_ip}")
        ok, out = run_spirent([
            "create-device", "--ip", self.spirent_peer_ip, "--gateway", self.dut_neighbor_ip,
            "--vlan", str(self.vlan), "--name", "FlowSpecPeer",
            "--session-name", self.session_name,
        ])
        if not ok:
            self.log(f"ERROR: create-device failed: {out}")
            self.log(f"Hint: Current VLAN={self.vlan}. VLAN 219 uses existing BD g_yor_v213. "
                     f"Use --vlan 219 --spirent-ip 49.49.49.1 --dut-ip 49.49.49.4")
            return False

        self.log("Starting BGP peer")
        ok, out = run_spirent([
            "bgp-peer", "--device-name", "FlowSpecPeer",
            "--as", str(DEFAULT_AS), "--dut-as", str(DEFAULT_DUT_AS),
            "--neighbor", self.dut_neighbor_ip,
            "--session-name", self.session_name,
        ])
        if not ok:
            self.log(f"ERROR: bgp-peer failed: {out}")
            return False

        self.log(f"Injecting {FLOWSPEC_RULE_COUNT} FlowSpec rules")
        ok, out = run_spirent([
            "add-routes", "--device-name", "FlowSpecPeer", "--afi", "flowspec",
            "--prefix", "100.0.0.0", "--count", str(FLOWSPEC_RULE_COUNT),
            "--action", "redirect-ip", "--redirect-target", "10.0.0.230",
            "--session-name", self.session_name,
        ])
        if not ok:
            self.log(f"FlowSpec injection failed: {out}")
            self.log("Falling back to ExaBGP")
            self.route_source = "exabgp"
            if self.setup_exabgp_fallback():
                return True
            self.log("Falling back to pre-existing rules (workaround)")
            return self.setup_preexisting_rules()
        self.route_source = "spirent"
        self.effective_rule_count = FLOWSPEC_RULE_COUNT
        self._start_spirent_traffic()
        return True

    def _start_spirent_traffic(self) -> None:
        """Create a traffic stream and start generation for loss measurement."""
        self.log("Creating traffic stream for data-plane loss measurement")
        ok, out = run_spirent([
            "create-stream", "--vlan", str(self.vlan),
            "--dst-ip", "100.0.0.1", "--rate-mbps", "100",
            "--name", "ha_baseline",
            "--session-name", self.session_name,
        ])
        if not ok:
            self.log(f"WARNING: Traffic stream creation failed: {out[:200]}")
            self.log("Spirent BGP works, but no traffic loss measurement")
            return
        self.log("Starting traffic generation")
        run_spirent(["start", "--session-name", self.session_name])
        time.sleep(3)
        self.spirent_baseline = self.spirent_poll_stats()
        self.spirent_available = True
        baseline_tx = self.spirent_baseline.get("tx", {}).get("rate_fps", "?")
        baseline_rx = self.spirent_baseline.get("rx", {}).get("rate_fps", "?")
        self.log(f"Spirent baseline: TX={baseline_tx}fps RX={baseline_rx}fps")
        if not self.spirent_baseline.get("error") and ACTIVE_SESSION.exists():
            try:
                with open(ACTIVE_SESSION) as f:
                    session_data = json.load(f)
                session_data["spirent_expected_traffic"] = {
                    "vlan": self.vlan,
                    "dst_ip": "100.0.0.1",
                    "src_ip": "10.99.99.1",
                    "rate_mbps": 100,
                    "bpf_filter": f"vlan {self.vlan} and host 100.0.0.1",
                }
                session_data["spirent_baseline"] = {
                    "tx_fps": baseline_tx,
                    "rx_fps": baseline_rx,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                with open(ACTIVE_SESSION, "w") as f:
                    json.dump(session_data, f, indent=2)
            except Exception as e:
                self.log(f"WARNING: Could not update active_ha_session: {e}")

    def detect_device_mode(self) -> None:
        """Run show system, parse CL vs SA. Required for correct test selection and NCC connection strategy."""
        out = self.dut_run("show system")
        info = parse_system_type(out)
        self.device_mode = info["device_mode"]
        self.system_type = info["system_type"]
        self.active_ncc_id = info["active_ncc_id"]
        self.standby_ncc_id = info["standby_ncc_id"]
        self.log(f"Device mode: {self.device_mode} ({self.system_type})")
        if self.device_mode == "cluster":
            self.log(f"  Active NCC: {self.active_ncc_id}, Standby NCC: {self.standby_ncc_id}")
            if self.standby_ncc_ip:
                self.log(f"  Standby NCC IP provided: will use for NCC restart tests")
            else:
                self.log(f"  Hint: Use --standby-ip <standby_mgmt_ip> to connect to standby NCC during active NCC restart (avoids SSH loss)")

    def resolve_template(self, template: str) -> str:
        """Resolve {active_ncc_id}, {ncp_id}, {ncf_id}, {peer_ip} in command strings."""
        result = template
        if "{active_ncc_id}" in result:
            if self.active_ncc_id is None:
                raise RuntimeError("Cannot resolve {active_ncc_id}: run detect_device_mode first")
            result = result.replace("{active_ncc_id}", str(self.active_ncc_id))
        if "{standby_ncc_id}" in result:
            if self.standby_ncc_id is None:
                raise RuntimeError("Cannot resolve {standby_ncc_id}: no standby NCC detected")
            result = result.replace("{standby_ncc_id}", str(self.standby_ncc_id))
        if "{ncp_id}" in result:
            ncp_id = self._find_first_operational_ncp()
            result = result.replace("{ncp_id}", str(ncp_id))
        if "{ncf_id}" in result:
            ncf_id = self._find_first_operational_ncf()
            result = result.replace("{ncf_id}", str(ncf_id))
        if "{peer_ip}" in result:
            peer = self._find_fsvpn_peer() or self.spirent_peer_ip
            result = result.replace("{peer_ip}", peer)
        return result

    def _find_first_operational_ncp(self) -> int:
        """Find the first NCP with operational state 'up' from show system."""
        out = self.dut_run("show system")
        for line in out.split("\n"):
            m = re.search(r"\|\s*NCP\s*\|\s*(\d+)\s*\|.*?\|\s*up\s*\|", line)
            if m:
                return int(m.group(1))
        raise RuntimeError("No operational NCP found in show system")

    def _find_first_operational_ncf(self) -> int:
        """Find the first NCF with operational state 'up' from show system."""
        out = self.dut_run("show system")
        for line in out.split("\n"):
            m = re.search(r"\|\s*NCF\s*\|\s*(\d+)\s*\|.*?\|\s*up\s*\|", line)
            if m:
                return int(m.group(1))
        raise RuntimeError("No operational NCF found in show system")

    def _find_fsvpn_peer(self) -> str | None:
        """Find the BGP FlowSpec-VPN peer IP from show bgp ipv4 flowspec-vpn summary."""
        try:
            out = self.dut_run("show bgp ipv4 flowspec-vpn summary", timeout=15, retries=1)
            for line in out.split("\n"):
                m = re.match(r"\s*(\d+\.\d+\.\d+\.\d+)\s+\d+\s+\d+\s+.*Established", line)
                if not m:
                    m = re.match(r"\s*(\d+\.\d+\.\d+\.\d+)\s+\d+\s+\d+\s+\d+\s+\d+", line)
                if m:
                    return m.group(1)
        except Exception:
            pass
        return None

    def run_safety_checks(self, test_def: dict) -> tuple[bool, str]:
        """Run pre-test safety checks. Returns (safe_to_proceed, reason_if_not)."""
        checks = test_def.get("pre_safety_check", [])
        if not checks:
            return True, ""

        out = self.dut_run("show system")
        for check in checks:
            if check == "verify_standby_ncc_ready":
                if self.standby_ncc_id is None:
                    return False, "No standby NCC detected"
                if "standby-up" not in out:
                    return False, "Standby NCC is not in standby-up state (switchover would fail)"
                if not self.standby_ncc_ip:
                    return False, "No standby NCC IP provided (--standby-ip required for NCC cold restart)"
                self.log(f"  Safety: standby NCC-{self.standby_ncc_id} is ready")

            elif check == "verify_ncp_up":
                try:
                    ncp_id = self._find_first_operational_ncp()
                    self.log(f"  Safety: NCP-{ncp_id} is operational")
                except RuntimeError:
                    return False, "No operational NCP found"

            elif check == "verify_ncf_up":
                try:
                    ncf_id = self._find_first_operational_ncf()
                    self.log(f"  Safety: NCF-{ncf_id} is operational")
                except RuntimeError:
                    return False, "No operational NCF found"

            elif check == "verify_single_ncf_warning":
                ncf_up_count = len(re.findall(r"\|\s*NCF\s*\|\s*\d+\s*\|.*?\|\s*up\s*\|", out))
                if ncf_up_count <= 1:
                    self.log("  WARNING: Only 1 active NCF. Disabling it will sever ALL fabric connectivity.")
                    self.log("           System will lose NCP-to-NCC communication. This is expected for LOFD test.")

        return True, ""

    def dut_config(self, commands: list[str], timeout: int = 60) -> str:
        """Run config-mode commands via interactive shell. Handles confirm prompts."""
        resolved = [self.resolve_template(c) for c in commands]
        self.log(f"  Config commands: {resolved}")
        if self.dry_run:
            return "DRY-RUN: config skipped"
        full_cmds = []
        for cmd in resolved:
            full_cmds.append(cmd)
            if cmd == "commit":
                full_cmds.append("exit")
        return self.dut_shell(full_cmds, timeout=timeout)

    def ensure_lofd_recovery(self, test_def: dict, ncf_id: int = 0) -> bool:
        """Guarantee NCF is re-enabled after LOFD test. Returns True if recovery succeeded.
        ncf_id must be pre-resolved BEFORE disabling (cannot discover after NCF is down)."""
        recovery_cmds = [c.replace("{ncf_id}", str(ncf_id)) for c in test_def.get("recovery_commands", [])]
        fallback_cmds = [c.replace("{ncf_id}", str(ncf_id)) for c in test_def.get("recovery_fallback_commands", [])]

        self.log(f"LOFD Recovery: re-enabling NCF-{ncf_id}...")
        for cmds, label in [(recovery_cmds, "primary"), (fallback_cmds, "fallback")]:
            if not cmds:
                continue
            try:
                self.log(f"  Config commands: {cmds}")
                if not self.dry_run:
                    out = self.dut_shell(cmds, timeout=60)
                else:
                    out = "DRY-RUN: config skipped"
                if "Error" in out or "error" in out:
                    self.log(f"  Recovery {label} failed: {out[:200]}")
                    continue
                self.log(f"  NCF re-enable ({label}) committed")
                time.sleep(15)
                ok = self.verify_node_recovered("NCF", ncf_id, max_wait=120)
                if ok:
                    return True
                self.log(f"  NCF-{ncf_id} re-enabled but not yet 'up', continuing anyway")
                return True
            except Exception as e:
                self.log(f"  Recovery {label} exception: {e}")

        self.log(f"  CRITICAL: All recovery attempts failed for NCF-{ncf_id}")
        self.log(f"  MANUAL ACTION: 'configure → system → ncf {ncf_id} → admin-state enabled → commit'")
        return False

    def verify_node_recovered(self, node_type: str, node_id: int, max_wait: int = 180) -> bool:
        """Poll show system until a node returns to 'up' (NCP/NCF) or 'standby-up' (NCC)."""
        expected_state = "standby-up" if node_type == "NCC" else "up"
        start = time.time()
        while time.time() - start < max_wait:
            try:
                out = self.dut_run("show system", timeout=15)
                pattern = rf"\|\s*{node_type}\s*\|\s*{node_id}\s*\|.*?\|\s*{expected_state}\s*\|"
                if re.search(pattern, out):
                    elapsed = time.time() - start
                    self.log(f"  {node_type}-{node_id} recovered to {expected_state} in {elapsed:.0f}s")
                    return True
            except Exception:
                pass
            time.sleep(5)
        self.log(f"  WARNING: {node_type}-{node_id} did not reach {expected_state} within {max_wait}s")
        return False

    def _get_connection_target(self, test_def: dict) -> dict:
        """For CL: when restarting active NCC, use standby IP if available. Returns device dict for SSH."""
        if self.device_mode != "cluster" or not self.standby_ncc_ip:
            return self.device
        cmd = self.resolve_template(test_def.get("ha_command", ""))
        ha_type = test_def.get("ha_type", "")
        if ha_type in ("ncc_cold_restart", "ncc_failover") or (
            re.search(r"request\s+system\s+restart\s+ncc\s+\d+", cmd, re.I)
            and "process restart" not in cmd.lower()
            and "ncc switchover" not in cmd.lower()
        ):
            ncc_m = re.search(r"ncc\s+(\d+)", cmd, re.I)
            if ncc_m:
                target_ncc = int(ncc_m.group(1))
                if target_ncc == self.active_ncc_id:
                    return {**self.device, "ip": self.standby_ncc_ip, "hostname": f"{self.device['hostname']}-standby"}
        return self.device

    def setup_preexisting_rules(self) -> bool:
        """Workaround: Use FlowSpec rules already on DUT (from /BGP or prior session)."""
        self.log("Checking DUT for existing FlowSpec-VPN rules...")
        max_bgp_wait = 300
        start = time.time()
        n = 0
        while time.time() - start < max_bgp_wait:
            try:
                out = self.dut_run("show bgp ipv4 flowspec-vpn summary")
                bgp_state = parse_bgp_state(out)
                n = parse_flowspec_route_count(out)
                if n < 0:
                    n = len(re.findall(r"\d+\.\d+\.\d+\.\d+/\d+", out))
                if n >= 10:
                    break
                if bgp_state in ("Connect", "Active", "OpenSent", "OpenConfirm", "Idle"):
                    elapsed = int(time.time() - start)
                    self.log(f"  BGP state={bgp_state}, routes={n}, waiting... ({elapsed}s/{max_bgp_wait}s)")
                    time.sleep(10)
                    continue
                break
            except Exception as e:
                self.log(f"  SSH error during BGP wait: {e}")
                time.sleep(5)
        if n < 10:
            self.log(f"ERROR: Only {n} rules found after {int(time.time()-start)}s. Need >= 10. Inject via /BGP first.")
            return False
        self.log(f"Using {n} pre-existing FlowSpec rules (workaround)")
        self.route_source = "preexisting"
        self.effective_rule_count = n
        return True

    def setup_exabgp_fallback(self) -> bool:
        """Use ExaBGP for FlowSpec injection. Requires existing /BGP session."""
        # Check for active ExaBGP session
        ok, out = run_bgp_tool(["list"])
        if not ok:
            self.log("ERROR: bgp_tool list failed")
            return False
        try:
            data = json.loads(out)
            if isinstance(data, list):
                sessions = data
            else:
                sessions = data.get("sessions", [data]) if isinstance(data, dict) else []
            active = [s for s in sessions if s.get("exabgp_alive") or s.get("status") == "active"]
            if not active:
                self.log("ERROR: No active ExaBGP session. Start /BGP first with FlowSpec-VPN AFI.")
                return False
            self.log(f"Using ExaBGP session: {active[0].get('session_id', 'unknown')}")
            # ExaBGP inject would need route strings - for now, require Spirent
            self.log("ExaBGP FlowSpec batch inject not yet implemented in orchestrator.")
            return False
        except Exception as e:
            self.log(f"ERROR parsing bgp_tool list: {e}")
            return False

    def verify_preflight(self) -> bool:
        """Comprehensive pre-flight check. Returns False and blocks test start on any CRITICAL failure.
        Validates: SSH, image version, BGP session, FlowSpec rules, NCP, TCAM, cluster health."""
        checks_passed = 0
        checks_failed = 0
        warnings = 0

        self.log("=== PRE-FLIGHT CHECKS ===")

        # 1. SSH connectivity (already proven by reaching here, but verify response)
        try:
            ver_out = self.dut_run("show system image", timeout=15)
            m = re.search(r"Current Image\s*:\s*(\S+)", ver_out)
            if m:
                self.image_version = m.group(1).strip()
                self.log(f"  [OK] Image: {self.image_version}")
                checks_passed += 1
            else:
                m2 = re.search(r"(\d+\.\d+\.\d+\S*)", ver_out)
                self.image_version = m2.group(1) if m2 else "unknown"
                self.log(f"  [WARN] Image parse partial: {self.image_version}")
                warnings += 1
        except Exception as e:
            self.log(f"  [FAIL] SSH / show system image failed: {e}")
            checks_failed += 1
            return False

        # 2. BGP FlowSpec-VPN session state
        try:
            out = self.dut_run("show bgp ipv4 flowspec-vpn summary")
            state = parse_bgp_state(out)
            n = parse_flowspec_route_count(out)
            if n < 0:
                n = len(re.findall(r"\d+\.\d+\.\d+\.\d+/\d+", out))
            self.log(f"  [{'OK' if state == 'Established' else 'FAIL'}] BGP FlowSpec-VPN: {state}")
            if state != "Established":
                self.log("  CRITICAL: BGP FlowSpec-VPN peer not Established. Cannot run HA tests.")
                checks_failed += 1
            else:
                checks_passed += 1
        except Exception as e:
            self.log(f"  [FAIL] BGP check failed: {e}")
            checks_failed += 1

        # 3. FlowSpec rules present
        expected = getattr(self, "effective_rule_count", FLOWSPEC_RULE_COUNT)
        self.log(f"  [{'OK' if n >= expected * 0.5 else 'FAIL'}] FlowSpec routes: {n} (expected ~{expected})")
        if n < 10:
            self.log("  CRITICAL: < 10 FlowSpec rules. Inject via Spirent or /BGP first.")
            checks_failed += 1
        elif n < expected * 0.5:
            self.log(f"  WARNING: Only {n} rules (< 50% of expected {expected})")
            warnings += 1
        else:
            checks_passed += 1

        # 4. NCP operational + FlowSpec installed in datapath
        try:
            ncp_id = self._find_first_operational_ncp()
            self.ncp_id_cached = ncp_id
            ncp_out = self.dut_run(f"show flowspec ncp {ncp_id}", timeout=15)
            ncp_counters = parse_flowspec_ncp_counters(ncp_out)
            installed = ncp_counters.get("installed", 0)
            self.log(f"  [OK] NCP-{ncp_id} operational, {installed} rules in datapath")
            checks_passed += 1
        except RuntimeError:
            self.log("  [WARN] No operational NCP found (may be single-NCP system)")
            warnings += 1
        except Exception as e:
            self.log(f"  [WARN] NCP check failed: {e}")
            warnings += 1

        # 5. TCAM capacity
        try:
            tcam_out = self.dut_run("show system npu-resources resource-type flowspec", timeout=15)
            tcam = parse_tcam_usage(tcam_out)
            pct = tcam.get("percent", 0)
            self.log(f"  [{'OK' if pct < 95 else 'WARN'}] TCAM: {tcam.get('installed', 0)} installed ({pct:.0f}% used)")
            if pct >= 95:
                self.log("  WARNING: TCAM near full. Some tests may hit capacity limits.")
                warnings += 1
            else:
                checks_passed += 1
        except Exception as e:
            self.log(f"  [WARN] TCAM check failed: {e}")
            warnings += 1

        # 6. Cluster health (if cluster mode)
        if self.device_mode == "cluster":
            if self.standby_ncc_id is not None:
                self.log(f"  [OK] Cluster: Active NCC-{self.active_ncc_id}, Standby NCC-{self.standby_ncc_id}")
                checks_passed += 1
            else:
                self.log("  [WARN] Cluster mode but no standby NCC detected. Switchover tests will skip.")
                warnings += 1
            if self.standby_ncc_ip:
                try:
                    ok, _ = ssh_quick_check(self.standby_ncc_ip, self.device["username"],
                                            self.device["password"], "show system version", timeout=10)
                    self.log(f"  [{'OK' if ok else 'WARN'}] Standby NCC SSH ({self.standby_ncc_ip}): {'reachable' if ok else 'unreachable'}")
                    if ok:
                        checks_passed += 1
                    else:
                        warnings += 1
                except Exception:
                    self.log(f"  [WARN] Standby NCC SSH check failed")
                    warnings += 1

        self.log(f"=== PRE-FLIGHT: {checks_passed} OK / {warnings} WARN / {checks_failed} FAIL ===")

        if checks_failed > 0:
            self.log("ABORTING: Critical pre-flight checks failed. Fix issues above before running tests.")
            return False

        return True

    def spirent_poll_stats(self) -> dict:
        """Collect Spirent TX/RX/loss stats. Returns parsed dict or error.
        Retries up to 3 times on failure. Sets spirent_reachable=False on persistent failure."""
        if self.dry_run:
            return {"dry_run": True}
        last_err = None
        for attempt in range(3):
            ok, out = run_spirent(["stats", "--json", "--session-name", self.session_name])
            if ok and out.strip():
                try:
                    stats = json.loads(out)
                    if not stats.get("error"):
                        self.spirent_reachable = True
                        return stats
                except (json.JSONDecodeError, ValueError):
                    last_err = {"error": "JSON parse failed", "raw": out[:200]}
            else:
                last_err = {"error": out[:200] if out else "empty response", "unreachable": True}
            if attempt < 2:
                time.sleep(2)
        self.spirent_reachable = False
        return last_err or {"error": "Spirent unreachable after 3 retries", "unreachable": True}

    def xray_cp_capture(self, duration_sec: int = 5) -> dict:
        """Run CP packet capture on DUT to verify control-plane traffic post-recovery."""
        bpf = "tcp port 179"
        cmd = f'run packet-capture ncc count 20 filter-expression "{bpf}"'
        self.log(f"  XRAY CP capture: BGP traffic check")
        try:
            out = self.dut_shell(["set cli-no-confirm", cmd], timeout=duration_sec + 15)
            pkt_count = len(re.findall(r"\d+:\d+:\d+\.\d+", out))
            if pkt_count == 0:
                pkt_count = out.lower().count("packet")
            verdict = "PASS" if pkt_count > 0 else "NO_TRAFFIC"
            self.log(f"  XRAY: {pkt_count} packets captured -> {verdict}")
            return {"packets_captured": pkt_count, "verdict": verdict}
        except Exception as e:
            self.log(f"  XRAY capture failed: {e}")
            return {"packets_captured": 0, "verdict": "ERROR", "error": str(e)}

    def trigger_ha_event(self, test_def: dict) -> bool:
        """Trigger HA event via SSH. Returns True if triggered (may disconnect).
        Enables 'set logging terminal' to capture live syslog events during the trigger.
        Trigger output (including syslog) is saved in self._last_trigger_output."""
        self._last_trigger_output = ""
        self._trigger_timestamp = datetime.now().strftime("%H:%M")

        # Sequential (test 15)
        commands = test_def.get("ha_commands")
        if commands:
            outputs = []
            for i, cmd in enumerate(commands):
                cmd = self.resolve_template(cmd)
                self.log(f"Triggering ({i+1}/{len(commands)}): {cmd}")
                if not self.dry_run:
                    shell_cmds = ["set logging terminal", cmd] if i == 0 else [cmd]
                    out = self.dut_shell(shell_cmds)
                    outputs.append(strip_ansi(out))
                    time.sleep(3)
            self._last_trigger_output = "\n---\n".join(outputs)
            return True

        # LOFD via NCF admin-disable (config-mode test)
        if test_def.get("requires_config_mode"):
            config_cmds = test_def.get("config_commands", [])
            if not config_cmds:
                self.log("SKIP: requires_config_mode but no config_commands defined")
                return False
            self.log(f"Triggering LOFD: disabling NCF via config mode")
            if not self.dry_run:
                out = self.dut_shell(["set logging terminal", "set cli-no-confirm"])
                self._last_trigger_output = strip_ansi(out)
                self.dut_config(config_cmds)
            return True

        cmd = test_def.get("ha_command", "")
        if not cmd or "SEQUENTIAL" in cmd:
            self.log(f"SKIP: {cmd}")
            return False

        cmd = self.resolve_template(cmd)
        repeat = test_def.get("ha_command_repeat", 1)
        outputs = []
        for i in range(repeat):
            self.log(f"Triggering ({i+1}/{repeat}): {cmd}")
            if not self.dry_run:
                out = self.dut_shell(["set logging terminal", "set cli-no-confirm", cmd])
                outputs.append(strip_ansi(out))
                if repeat > 1:
                    time.sleep(5)
        self._last_trigger_output = "\n---\n".join(outputs)
        return True

    def poll_recovery(self, test_def: dict, max_wait: int = None) -> dict:
        """Poll until recovered or timeout. Uses multi-IP reconnect for destructive tests.
        Tracks BGP state transitions (flap count). After 40% of max_wait, re-reads devices.json."""
        max_wait = max_wait or test_def.get("max_recovery_sec", 120)
        kills_ssh = test_def.get("kills_ssh", False)
        start = time.time()
        last_state = {}
        spirent_polls = []
        poll_num = 0
        ssh_connected = not kills_ssh
        db_refreshed = False
        cmd = "show bgp ipv4 flowspec-vpn summary"

        bgp_state_history = []
        prev_bgp_state = None

        while time.time() - start < max_wait:
            poll_num += 1
            elapsed = int(time.time() - start)

            if not ssh_connected:
                if not db_refreshed and elapsed > max_wait * 0.4:
                    self.log(f"  Refreshing device IP from DB (DHCP may have changed after restart)")
                    self._refresh_ip_from_db()
                    db_refreshed = True
                ips = self._all_ips()
                ip = ips[(poll_num - 1) % len(ips)]
                ok, out = ssh_quick_check(ip, self.device["username"], self.device["password"], cmd)
                if not ok:
                    self.log(f"  Poll #{poll_num} ({elapsed}s): {ip} not ready")
                    time.sleep(5)
                    continue
                if ip != self.device["ip"]:
                    self.log(f"  Reconnected via {ip} (was {self.device['ip']})")
                    self.device["ip"] = ip
                ssh_connected = True
                self._refresh_nce_ips()
            else:
                try:
                    out = self.dut_run(cmd, timeout=10, retries=1)
                except Exception as e:
                    if kills_ssh:
                        self.log(f"  Poll #{poll_num} ({elapsed}s): SSH lost ({e})")
                        ssh_connected = False
                        time.sleep(3)
                        continue
                    raise

            current_bgp = parse_bgp_state(out)
            last_state["bgp"] = current_bgp
            last_state["routes"] = parse_flowspec_route_count(out)

            if current_bgp != prev_bgp_state:
                bgp_state_history.append({
                    "t": round(time.time() - start, 1),
                    "from": prev_bgp_state,
                    "to": current_bgp,
                })
                if prev_bgp_state is not None:
                    self.log(f"  BGP transition: {prev_bgp_state} -> {current_bgp} at {elapsed}s")
                prev_bgp_state = current_bgp

            if self.spirent_available:
                sp = self.spirent_poll_stats()
                if sp.get("error"):
                    self.spirent_reachable = False
                    self.log(f"  Poll #{poll_num} ({elapsed}s): Spirent unreachable -- traffic stats unavailable")
                else:
                    rx_fps = sp.get("rx", {}).get("rate_fps", "0")
                    loss = sp.get("loss", {}).get("frames", 0)
                    spirent_polls.append({"t": round(time.time() - start, 1), "rx_fps": rx_fps, "loss": loss})
                    last_state["spirent_rx_fps"] = rx_fps
                    last_state["spirent_loss"] = loss
                    self.log(f"  Poll #{poll_num} ({elapsed}s): BGP={last_state['bgp']} routes={last_state['routes']} "
                             f"RX={rx_fps}fps loss={loss}")
            else:
                self.log(f"  Poll #{poll_num} ({elapsed}s): BGP={last_state['bgp']} routes={last_state['routes']}")

            expected = getattr(self, "effective_rule_count", FLOWSPEC_RULE_COUNT)
            if last_state["bgp"] == "Established" and last_state["routes"] >= expected * 0.9:
                elapsed_sec = time.time() - start
                self.log(f"Recovered in {elapsed_sec:.1f}s")
                conv = {"control_plane_sec": elapsed_sec, "overall_sec": elapsed_sec}
                if spirent_polls:
                    conv["traffic_sec"] = elapsed_sec
                bgp_flaps = sum(1 for t in bgp_state_history
                                if t["from"] == "Established" and t["to"] != "Established")
                if bgp_flaps > 1:
                    self.log(f"  BGP flapped {bgp_flaps} times during recovery")
                return {"recovered": True, "elapsed": elapsed_sec,
                        "state": last_state, "spirent_polls": spirent_polls,
                        "convergence_times": conv,
                        "bgp_flap_count": bgp_flaps,
                        "bgp_state_history": bgp_state_history}
            time.sleep(5)

        bgp_flaps = sum(1 for t in bgp_state_history
                        if t["from"] == "Established" and t["to"] != "Established")
        return {"recovered": False, "elapsed": max_wait, "state": last_state,
                "spirent_polls": spirent_polls, "convergence_times": {},
                "bgp_flap_count": bgp_flaps,
                "bgp_state_history": bgp_state_history}

    def run_single_test(self, test_def: dict) -> dict:
        """Run one test: safety check, before snapshot, trigger, poll, after snapshot, diff.

        For config-mode tests (LOFD), recovery is guaranteed in a finally block.
        For NCC/NCP restart tests, node recovery is verified after FlowSpec recovery.
        Global timeout: max_recovery_sec * 3 + 300s (covers snapshot + trigger + polling + overhead).
        """
        tid = test_def["id"]
        name = test_def["name"]
        ha_type = test_def.get("ha_type", "")
        self.log(f"=== {tid}: {name} ===")

        max_sec = test_def.get("max_recovery_sec", 300)
        global_timeout = max_sec * 3 + 300
        timed_out = False

        def _timeout_handler(signum, frame):
            nonlocal timed_out
            timed_out = True
            raise TimeoutError(f"Test {tid} exceeded global timeout of {global_timeout}s")

        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(global_timeout)

        if test_def.get("requires_manual"):
            self.log("MANUAL: User must perform physical action")
            return {"id": tid, "verdict": "SKIP", "reason": "requires_manual"}
        if test_def.get("skip_reason"):
            self.log(f"SKIP: {test_def['skip_reason']}")
            return {"id": tid, "verdict": "SKIP", "reason": test_def.get("skip_reason")}
        if test_def.get("requires_cluster") and self.device_mode == "standalone":
            self.log(f"SKIP: requires cluster (DUT is standalone)")
            return {"id": tid, "verdict": "SKIP", "reason": "requires_cluster"}

        # Pre-test safety checks
        safe, reason = self.run_safety_checks(test_def)
        if not safe:
            self.log(f"SAFETY ABORT: {reason}")
            return {"id": tid, "verdict": "SKIP", "reason": f"safety_check_failed: {reason}"}

        # Re-detect NCC states (may have changed from previous test)
        if ha_type in ("ncc_cold_restart", "ncc_failover", "ncc_switchover"):
            self.detect_device_mode()

        # On CL: for NCC restart tests, prefer standby NCC to avoid SSH loss
        original_device = None
        if self.device_mode == "cluster" and self.standby_ncc_ip:
            target = self._get_connection_target(test_def)
            if target["ip"] != self.device["ip"]:
                ok, _ = ssh_quick_check(target["ip"], target.get("username", "dnroot"),
                                        target.get("password", "dnroot"),
                                        "show system version", timeout=10)
                if ok:
                    original_device = self.device
                    self.device = target
                    self.log(f"Using standby NCC ({self.standby_ncc_ip}) for NCC restart test")
                else:
                    self.log(f"Standby NCC ({self.standby_ncc_ip}) SSH down, using active NCC + multi-IP reconnect")

        lofd_recovery_needed = test_def.get("requires_config_mode", False)
        lofd_ncf_id = 0
        if lofd_recovery_needed:
            try:
                lofd_ncf_id = self._find_first_operational_ncf()
            except RuntimeError:
                lofd_ncf_id = 0
        try:
            try:
                ncp_id = self.ncp_id_cached or self._find_first_operational_ncp()
                self.ncp_id_cached = ncp_id
            except RuntimeError:
                ncp_id = 0

            before = self.take_snapshot("before", test_def.get("post_verify", []))
            before["spirent_stats"] = self.spirent_poll_stats() if self.spirent_available else "N/A"
            try:
                ncp_out = self.dut_run(f"show flowspec ncp {ncp_id}", timeout=15)
                before["ncp_counters"] = parse_flowspec_ncp_counters(ncp_out)
                before["ncp_content_hash"] = compute_ncp_content_hash(ncp_out)
            except Exception:
                before["ncp_counters"] = {"installed": 0, "packets": 0, "bytes": 0}
                before["ncp_content_hash"] = ""
            try:
                tcam_out = self.dut_run("show system npu-resources resource-type flowspec", timeout=15)
                before["tcam"] = parse_tcam_usage(tcam_out)
            except Exception:
                before["tcam"] = {"installed": 0, "total": 0, "percent": 0.0}

            triggered = self.trigger_ha_event(test_def)
            if not triggered and not test_def.get("ha_commands"):
                lofd_recovery_needed = False
                return {"id": tid, "verdict": "SKIP", "reason": "no_trigger"}

            # LOFD: wait the configured duration, then recover before polling
            if ha_type == "lofd" and lofd_recovery_needed:
                wait_sec = test_def.get("lofd_disable_duration_sec", 30)
                self.log(f"LOFD: fabric down, waiting {wait_sec}s to observe impact...")
                if not self.dry_run:
                    time.sleep(wait_sec)
                self.log("LOFD: re-enabling NCF now...")
                recovery_ok = self.ensure_lofd_recovery(test_def, ncf_id=lofd_ncf_id)
                lofd_recovery_needed = False
                if not recovery_ok:
                    self.log("CRITICAL: NCF recovery failed! Manual intervention needed.")
                    return {"id": tid, "name": name, "verdict": "FAIL",
                            "reason": "LOFD recovery failed - NCF stuck disabled"}

            if test_def.get("kills_ssh"):
                if ha_type == "system_restart":
                    self.log("System restart: waiting for device to go DOWN first...")
                    down_confirmed = False
                    for i in range(24):  # Try for 2 min to confirm device went down
                        ok, _ = ssh_quick_check(self.device["ip"], self.device["username"],
                                                self.device["password"], "show system version")
                        if not ok:
                            self.log(f"  Device confirmed DOWN after {(i+1)*5}s")
                            down_confirmed = True
                            break
                        self.log(f"  Still reachable ({(i+1)*5}s), waiting for shutdown...")
                        time.sleep(5)
                    if not down_confirmed:
                        self.log("  WARNING: Device never went unreachable after system restart cmd")
                else:
                    initial_wait = 10
                    self.log(f"SSH will drop. Initial wait {initial_wait}s, then multi-IP polling...")
                    time.sleep(initial_wait)

            recovery = self.poll_recovery(test_def)

            if recovery.get("convergence_times") and ACTIVE_SESSION.exists():
                try:
                    with open(ACTIVE_SESSION) as f:
                        session_data = json.load(f)
                    session_data["convergence_times"] = recovery["convergence_times"]
                    with open(ACTIVE_SESSION, "w") as f:
                        json.dump(session_data, f, indent=2)
                except Exception:
                    pass

            # Device Lock: verify identity after destructive HA events (DHCP may reassign IPs)
            if test_def.get("kills_ssh") and recovery["recovered"]:
                if not self.verify_device_identity():
                    return {"id": tid, "name": name, "verdict": "FAIL",
                            "reason": "Device identity mismatch after HA event - wrong device!"}

            # Verify node itself recovered (NCC comes back as standby, NCP comes back as up)
            if ha_type == "ncc_cold_restart" and self.active_ncc_id is not None:
                restarted_ncc = self.active_ncc_id if not original_device else int(
                    re.search(r"ncc\s+(\d+)", self.resolve_template(test_def.get("ha_command", "")), re.I).group(1)
                )
                self.verify_node_recovered("NCC", restarted_ncc, max_wait=test_def.get("max_recovery_sec", 300))
            elif ha_type == "ncp_force_restart":
                try:
                    ncp_id = self._find_first_operational_ncp()
                except RuntimeError:
                    ncp_id_m = re.search(r"ncp\s+(\d+)", self.resolve_template(test_def.get("ha_command", "")), re.I)
                    ncp_id = int(ncp_id_m.group(1)) if ncp_id_m else 0
                self.verify_node_recovered("NCP", ncp_id, max_wait=test_def.get("max_recovery_sec", 300))

            after = self.take_snapshot("after", test_def.get("post_verify", []))
            after["recovery"] = recovery
            after["spirent_stats"] = self.spirent_poll_stats() if self.spirent_available else "N/A"
            try:
                ncp_out = self.dut_run(f"show flowspec ncp {ncp_id}", timeout=15)
                after["ncp_counters"] = parse_flowspec_ncp_counters(ncp_out)
                after["ncp_content_hash"] = compute_ncp_content_hash(ncp_out)
            except Exception:
                after["ncp_counters"] = {"installed": 0, "packets": 0, "bytes": 0}
                after["ncp_content_hash"] = ""
            try:
                tcam_out = self.dut_run("show system npu-resources resource-type flowspec", timeout=15)
                after["tcam"] = parse_tcam_usage(tcam_out)
            except Exception:
                after["tcam"] = {"installed": 0, "total": 0, "percent": 0.0}

            trace_evidence = {}
            trigger_timestamp = getattr(self, "_trigger_timestamp", None)
            if recovery["recovered"] and not self.dry_run and trigger_timestamp:
                self.log(f"  Capturing trace evidence at {trigger_timestamp}...")
                trace_evidence = self.capture_trace_evidence(trigger_timestamp, test_def)

            xray_result = {"verdict": "SKIP"}
            if recovery["recovered"] and not self.dry_run:
                xray_result = self.xray_cp_capture()

            # Per-layer verdicts
            cp_verdict = "PASS" if recovery["recovered"] else "FAIL"
            expected = getattr(self, "effective_rule_count", FLOWSPEC_RULE_COUNT)
            if recovery["recovered"] and recovery.get("state", {}).get("routes", 0) < expected * 0.9:
                cp_verdict = "WARNING"

            dp_verdict = "PASS"
            ncp_before_inst = before.get("ncp_counters", {}).get("installed", 0)
            ncp_after_inst = after.get("ncp_counters", {}).get("installed", 0)
            tcam_before = before.get("tcam", {}).get("installed", 0)
            tcam_after = after.get("tcam", {}).get("installed", 0)
            if ncp_before_inst > 0 and ncp_after_inst < ncp_before_inst * 0.9:
                dp_verdict = "FAIL"
            counter_delta = (after.get("ncp_counters", {}).get("packets", 0)
                             - before.get("ncp_counters", {}).get("packets", 0))

            sp_verdict = "N/A"
            spirent_loss = 0
            if self.spirent_available:
                b_sp = before.get("spirent_stats")
                a_sp = after.get("spirent_stats")
                if (isinstance(b_sp, dict) and isinstance(a_sp, dict)
                        and not b_sp.get("error") and not a_sp.get("error")):
                    b_loss = b_sp.get("loss", {}).get("frames", 0)
                    a_loss = a_sp.get("loss", {}).get("frames", 0)
                    if isinstance(a_loss, (int, float)) and isinstance(b_loss, (int, float)):
                        spirent_loss = max(0, a_loss - b_loss)
                    sp_verdict = "PASS" if spirent_loss == 0 else ("WARNING" if spirent_loss < 1000 else "FAIL")
                elif (not self.spirent_reachable or
                        (isinstance(b_sp, dict) and b_sp.get("error")) or
                        (isinstance(a_sp, dict) and a_sp.get("error"))):
                    sp_verdict = "UNKNOWN (unreachable)"

            # Collateral damage: detect unexpected process/container crashes
            collateral_verdict = "PASS"
            collateral_list = []
            before_procs = before.get("process_restart_counts", {})
            after_procs = after.get("process_restart_counts", {})
            if before_procs and after_procs:
                intentional = test_def.get("ha_command", "")
                intent_proc = ""
                proc_m = re.search(r"(?:process restart|container restart)\s+\S+\s+\d+\s+(\S+)\s+(\S+)", intentional, re.I)
                if proc_m:
                    intent_proc = proc_m.group(2)
                elif re.search(r"restart\s+ncc", intentional, re.I):
                    intent_proc = "NCC"
                elif re.search(r"restart\s+ncp", intentional, re.I):
                    intent_proc = "NCP"
                elif re.search(r"restart\s+ncf", intentional, re.I):
                    intent_proc = "NCF"
                elif ha_type == "lofd":
                    intent_proc = "NCF"

                collateral_list = detect_collateral_damage(
                    before_procs, after_procs, intent_proc, ha_type)
                if collateral_list:
                    collateral_verdict = "FAIL"
                    self.log(f"  [COLLATERAL] {len(collateral_list)} unexpected process restart(s) detected:")
                    for cd in collateral_list:
                        self.log(f"    {cd['process']}: +{cd['restart_delta']} restarts "
                                 f"({cd['before_restarts']}->{cd['after_restarts']}), state={cd['state_after']}")

            # Alarm diff: detect new alarms raised by the HA event
            alarm_result = diff_alarms(before.get("alarms", []), after.get("alarms", []))
            alarm_verdict = alarm_result["verdict"]
            if alarm_result["new_alarms"]:
                self.log(f"  [ALARMS] {len(alarm_result['new_alarms'])} new alarm(s) after HA event:")
                for a in alarm_result["new_alarms"]:
                    self.log(f"    [{a['severity']}] {a['source']}: {a['description']}")

            # Core dump detection
            core_verdict = "PASS"
            core_dumps = []
            if not self.dry_run and recovery["recovered"]:
                try:
                    core_out = strip_ansi(self.dut_run("show system core-dumps", timeout=15))
                    trigger_ts = getattr(self, "_trigger_timestamp", "")
                    all_cores = parse_core_dumps(core_out)
                    core_dumps = [c for c in all_cores if trigger_ts and trigger_ts in c.get("timestamp", "")]
                    if core_dumps:
                        core_verdict = "FAIL"
                        self.log(f"  [CORE DUMP] {len(core_dumps)} core dump(s) found at trigger time:")
                        for cd in core_dumps:
                            self.log(f"    {cd['filename']} (process: {cd['process']})")
                except Exception as e:
                    self.log(f"  Core dump check failed: {e}")

            # Recovery timing: compare actual vs expected
            timing_verdict = "PASS"
            actual_recovery = recovery.get("elapsed")
            expected_recovery = test_def.get("expected_recovery_sec")
            max_recovery = test_def.get("max_recovery_sec")
            if actual_recovery is not None and expected_recovery is not None:
                if actual_recovery > expected_recovery * 2:
                    timing_verdict = "WARNING"
                    self.log(f"  [TIMING] Recovery took {actual_recovery:.1f}s "
                             f"(expected {expected_recovery}s, 2x threshold)")
            if actual_recovery is not None and max_recovery is not None:
                if actual_recovery > max_recovery:
                    timing_verdict = "FAIL"
                    self.log(f"  [TIMING] Recovery {actual_recovery:.1f}s exceeded max {max_recovery}s")

            # Syslog error scan: check for ERROR/CRITICAL in system-events around trigger time
            syslog_errors = []
            trigger_ts = getattr(self, "_trigger_timestamp", "")
            if trigger_ts and not self.dry_run:
                try:
                    syslog_out = strip_ansi(self.dut_run(
                        f"show file log routing_engine/system-events.log | include {trigger_ts} | include ERROR",
                        timeout=15))
                    for line in syslog_out.split("\n"):
                        line = line.strip()
                        if line and "ERROR" in line:
                            syslog_errors.append(line)
                    crit_out = strip_ansi(self.dut_run(
                        f"show file log routing_engine/system-events.log | include {trigger_ts} | include CRITICAL",
                        timeout=15))
                    for line in crit_out.split("\n"):
                        line = line.strip()
                        if line and "CRITICAL" in line:
                            syslog_errors.append(line)
                    if syslog_errors:
                        self.log(f"  [SYSLOG] {len(syslog_errors)} ERROR/CRITICAL entries at {trigger_ts}:")
                        for e in syslog_errors[:5]:
                            self.log(f"    {e[:120]}")
                except Exception:
                    pass

            # Memory leak detection
            memory_verdict = "PASS"
            memory_leaks = []
            before_mem = before.get("process_memory", {})
            after_mem = after.get("process_memory", {})
            if before_mem and after_mem:
                memory_leaks = detect_memory_leaks(before_mem, after_mem, threshold_pct=25.0)
                if memory_leaks:
                    memory_verdict = "WARNING"
                    self.log(f"  [MEMORY] {len(memory_leaks)} process(es) with significant memory growth:")
                    for ml in memory_leaks[:3]:
                        self.log(f"    {ml['process']}: {ml['before_kb']}KB -> {ml['after_kb']}KB "
                                 f"(+{ml['delta_kb']}KB, {ml['growth_pct']}%)")

            # BGP flap counting
            bgp_flap_verdict = "PASS"
            bgp_flap_count = recovery.get("bgp_flap_count", 0)
            expected_bgp_drop = test_def.get("expected_bgp_drop", False)
            if bgp_flap_count > 1:
                bgp_flap_verdict = "WARNING"
                self.log(f"  [BGP FLAP] Session flapped {bgp_flap_count} times during recovery")
            elif bgp_flap_count == 0 and expected_bgp_drop:
                pass

            # BFD session diff
            bfd_result = diff_bfd_sessions(before.get("bfd_sessions", []), after.get("bfd_sessions", []))
            bfd_verdict = bfd_result["verdict"]
            if bfd_result["changed"] or bfd_result["lost"]:
                self.log(f"  [BFD] {len(bfd_result['changed'])} changed, {len(bfd_result['lost'])} lost sessions")
                for c in bfd_result["changed"][:3]:
                    self.log(f"    {c['neighbor']}: {c['before_state']} -> {c['after_state']}")

            # Interface state diff
            intf_result = diff_interface_states(
                before.get("interface_states", {}), after.get("interface_states", {}))
            intf_verdict = intf_result["verdict"]
            if intf_result["went_down"]:
                self.log(f"  [INTERFACES] {len(intf_result['went_down'])} interface(s) went down:")
                for i in intf_result["went_down"][:5]:
                    self.log(f"    {i['interface']}: {i['before']} -> {i['after']}")

            # Config drift detection
            config_verdict = "PASS"
            before_cfg_hash = before.get("config_hash", "")
            after_cfg_hash = after.get("config_hash", "")
            if before_cfg_hash and after_cfg_hash and before_cfg_hash != after_cfg_hash:
                config_verdict = "WARNING"
                self.log("  [CONFIG DRIFT] BGP config changed after HA event")

            # NCP content verification (structural hash, not just counts)
            ncp_content_verdict = "PASS"
            before_ncp_hash = before.get("ncp_content_hash", "")
            after_ncp_hash = after.get("ncp_content_hash", "")
            if (before_ncp_hash and after_ncp_hash
                    and ncp_before_inst == ncp_after_inst
                    and before_ncp_hash != after_ncp_hash):
                ncp_content_verdict = "WARNING"
                self.log("  [NCP CONTENT] Rule structure changed despite same count (possible rule corruption)")

            overall = "PASS"
            if cp_verdict == "FAIL" or dp_verdict == "FAIL" or sp_verdict == "FAIL":
                overall = "FAIL"
            elif collateral_verdict == "FAIL" or core_verdict == "FAIL":
                overall = "FAIL"
            elif timing_verdict == "FAIL" or alarm_verdict == "FAIL":
                overall = "FAIL"
            elif bfd_verdict == "FAIL" or intf_verdict == "FAIL":
                overall = "FAIL"
            elif (cp_verdict == "WARNING" or sp_verdict == "WARNING"
                    or alarm_verdict == "WARNING" or timing_verdict == "WARNING"
                    or memory_verdict == "WARNING" or bgp_flap_verdict == "WARNING"
                    or bfd_verdict == "WARNING" or intf_verdict == "WARNING"
                    or config_verdict == "WARNING" or ncp_content_verdict == "WARNING"):
                overall = "WARNING"
            elif sp_verdict == "UNKNOWN (unreachable)" and cp_verdict == "PASS" and dp_verdict == "PASS":
                overall = "PASS WITH WARNINGS"

            # Escalation hint for /debug-dnos when FAIL detected
            escalation_hint = ""
            if overall == "FAIL":
                fail_layers = []
                if cp_verdict == "FAIL":
                    fail_layers.append("control-plane (BGP not recovered)")
                if dp_verdict == "FAIL":
                    fail_layers.append(f"datapath (NCP {ncp_after_inst}/{ncp_before_inst} rules)")
                if sp_verdict == "FAIL":
                    fail_layers.append(f"traffic ({spirent_loss} frames lost)")
                if collateral_verdict == "FAIL":
                    procs = ", ".join(c["process"] for c in collateral_list[:3])
                    fail_layers.append(f"collateral crash ({procs})")
                if core_verdict == "FAIL":
                    core_procs = ", ".join(c["process"] for c in core_dumps[:3])
                    fail_layers.append(f"core dumps ({core_procs})")
                if alarm_verdict == "FAIL":
                    alarm_descs = ", ".join(a["description"][:40] for a in alarm_result["new_alarms"][:2])
                    fail_layers.append(f"new alarms ({alarm_descs})")
                if timing_verdict == "FAIL":
                    fail_layers.append(f"recovery timeout ({actual_recovery:.1f}s > {max_recovery}s)")
                if bfd_verdict == "FAIL":
                    bfd_nbrs = ", ".join(c["neighbor"] for c in (bfd_result["changed"] + bfd_result["lost"])[:3])
                    fail_layers.append(f"BFD sessions ({bfd_nbrs})")
                if intf_verdict == "FAIL":
                    intfs = ", ".join(i["interface"] for i in intf_result["went_down"][:3])
                    fail_layers.append(f"interfaces down ({intfs})")
                trigger_ts = getattr(self, "_trigger_timestamp", "")
                escalation_hint = (
                    f"/debug-dnos {self.device.get('hostname', '')} -- "
                    f"HA test {tid} FAIL: {'; '.join(fail_layers)}. "
                    f"Trace timestamp: {trigger_ts}. "
                    f"Feature: FlowSpec-VPN. "
                    f"HA command: {test_def.get('ha_command', '')}"
                )
                self.log(f"  [ESCALATION] {escalation_hint}")

            result = {
                "id": tid, "name": name, "verdict": overall,
                "recovery_sec": recovery.get("elapsed"), "ha_type": ha_type,
                "expected_recovery_sec": expected_recovery,
                "timing_verdict": timing_verdict,
                "cp_verdict": cp_verdict, "dp_verdict": dp_verdict,
                "sp_verdict": sp_verdict, "collateral_verdict": collateral_verdict,
                "alarm_verdict": alarm_verdict, "core_verdict": core_verdict,
                "memory_verdict": memory_verdict, "bgp_flap_verdict": bgp_flap_verdict,
                "bfd_verdict": bfd_verdict, "intf_verdict": intf_verdict,
                "config_verdict": config_verdict, "ncp_content_verdict": ncp_content_verdict,
                "xray_verdict": xray_result.get("verdict", "SKIP"),
                "xray_packets": xray_result.get("packets_captured", 0),
                "ncp_before": ncp_before_inst, "ncp_after": ncp_after_inst,
                "tcam_before": tcam_before, "tcam_after": tcam_after,
                "spirent_loss": spirent_loss, "counter_delta": counter_delta,
                "bgp_flap_count": bgp_flap_count,
                "before_routes": before["commands"].get("show bgp ipv4 flowspec-vpn summary", ""),
                "after_routes": after["commands"].get("show bgp ipv4 flowspec-vpn summary", ""),
                "collateral_damage": collateral_list,
                "memory_leaks": memory_leaks,
                "new_alarms": alarm_result["new_alarms"],
                "core_dumps": core_dumps,
                "syslog_errors": syslog_errors[:10],
                "bfd_changes": bfd_result["changed"] + bfd_result["lost"],
                "interfaces_down": intf_result["went_down"],
                "config_drifted": config_verdict != "PASS",
                "ncp_content_changed": ncp_content_verdict != "PASS",
                "escalation_hint": escalation_hint,
            }

            evidence = {
                "id": tid, "name": name, "verdict": overall,
                "ha_command": test_def.get("ha_command", ""),
                "timestamp": datetime.now().isoformat(),
                "trigger_timestamp_hhmm": getattr(self, "_trigger_timestamp", ""),
                "device": self.device.get("hostname", ""),
                "before_snapshot": before,
                "after_snapshot": after,
                "trigger_output": getattr(self, "_last_trigger_output", ""),
                "trace_evidence": trace_evidence,
                "recovery_detail": {
                    "recovered": recovery.get("recovered"),
                    "elapsed_sec": recovery.get("elapsed"),
                    "expected_sec": expected_recovery,
                    "timing_verdict": timing_verdict,
                    "convergence_times": recovery.get("convergence_times"),
                    "final_state": recovery.get("state"),
                },
                "xray_detail": xray_result,
                "spirent_detail": {
                    "before": before.get("spirent_stats"),
                    "after": after.get("spirent_stats"),
                    "loss_frames": spirent_loss,
                },
                "alarm_detail": alarm_result,
                "core_dumps": core_dumps,
                "syslog_errors": syslog_errors[:20],
                "collateral_damage": {
                    "verdict": collateral_verdict,
                    "intentional_process": intent_proc if before_procs else "N/A",
                    "unexpected_restarts": collateral_list,
                },
                "memory_analysis": {
                    "verdict": memory_verdict,
                    "leaks": memory_leaks,
                },
                "bgp_stability": {
                    "verdict": bgp_flap_verdict,
                    "flap_count": bgp_flap_count,
                    "state_history": recovery.get("bgp_state_history", []),
                },
                "bfd_detail": bfd_result,
                "interface_detail": intf_result,
                "config_drift": {
                    "verdict": config_verdict,
                    "before_hash": before_cfg_hash,
                    "after_hash": after_cfg_hash,
                },
                "ncp_content": {
                    "verdict": ncp_content_verdict,
                    "before_hash": before_ncp_hash,
                    "after_hash": after_ncp_hash,
                },
                "layer_verdicts": {
                    "control_plane": cp_verdict,
                    "datapath": dp_verdict,
                    "spirent": sp_verdict,
                    "collateral": collateral_verdict,
                    "alarms": alarm_verdict,
                    "core_dumps": core_verdict,
                    "timing": timing_verdict,
                    "memory": memory_verdict,
                    "bgp_flaps": bgp_flap_verdict,
                    "bfd": bfd_verdict,
                    "interfaces": intf_verdict,
                    "config_drift": config_verdict,
                    "ncp_content": ncp_content_verdict,
                    "xray": xray_result.get("verdict", "SKIP"),
                    "overall": overall,
                },
                "escalation_hint": escalation_hint,
            }
            result["_evidence_file"] = f"{tid}_evidence.json"
            try:
                evidence_path = self.run_dir / f"{tid}_evidence.json"
                evidence_path.write_text(json.dumps(evidence, indent=2, default=str))
            except Exception as e:
                self.log(f"  WARNING: Could not save evidence file: {e}")

            non_pass = []
            for lbl, v in [("CP", cp_verdict), ("DP", dp_verdict), ("Collateral", collateral_verdict),
                           ("Alarms", alarm_verdict), ("CoreDump", core_verdict), ("Timing", timing_verdict),
                           ("Memory", memory_verdict), ("BGPflap", bgp_flap_verdict), ("BFD", bfd_verdict),
                           ("Intf", intf_verdict), ("CfgDrift", config_verdict), ("NCPcontent", ncp_content_verdict),
                           ("Spirent", sp_verdict), ("XRAY", xray_result.get("verdict", "SKIP"))]:
                if v not in ("PASS", "N/A", "SKIP"):
                    non_pass.append(f"{lbl}={v}")
            detail = ", ".join(non_pass) if non_pass else "all layers PASS"
            self.log(f"Verdict: {overall} ({detail})")
            return result
        except TimeoutError as exc:
            self.log(f"TEST TIMEOUT: {exc}")
            return {"id": tid, "name": name, "verdict": "FAIL",
                    "reason": f"Global timeout ({global_timeout}s)",
                    "escalation_hint": f"/debug-dnos {self.device.get('hostname', '')} -- "
                    f"HA test {tid} HUNG: exceeded {global_timeout}s. "
                    f"HA command: {test_def.get('ha_command', '')}"}
        except Exception as exc:
            self.log(f"TEST ERROR: {exc}")
            return {"id": tid, "name": name, "verdict": "ERROR", "reason": str(exc)}
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
            # CRITICAL: Always recover NCF for LOFD tests, even on crash/exception
            if lofd_recovery_needed:
                self.log("FINALLY: Ensuring LOFD recovery (NCF re-enable)...")
                self.ensure_lofd_recovery(test_def, ncf_id=lofd_ncf_id)
            if original_device:
                self.device = original_device

    def capture_trace_evidence(self, timestamp_hhmm: str, test_def: dict) -> dict:
        """Grep trace files for the HA event timestamp to capture what happened inside the system.
        Returns dict with per-layer trace output (ANSI-stripped)."""
        traces = {}
        ha_type = test_def.get("ha_type", "")

        trace_commands = [
            ("bgpd", f"show file traces routing_engine/bgpd_traces | include {timestamp_hhmm}"),
            ("rib_manager", f"show file traces routing_engine/rib-manager_traces | include {timestamp_hhmm}"),
            ("fibmgrd", f"show file traces routing_engine/fibmgrd_traces | include {timestamp_hhmm} | include FLOWSPEC"),
        ]

        if ha_type in ("process_restart", "container_restart"):
            trace_commands.append(
                ("system_events",
                 f"show file log routing_engine/system-events.log | include {timestamp_hhmm}"),
            )

        if "ncc" in ha_type or "switchover" in ha_type:
            trace_commands.append(
                ("ncc_events",
                 f"show file traces routing_engine/bgpd_traces | include {timestamp_hhmm} | include ADJCHANGE"),
            )

        for label, cmd in trace_commands:
            try:
                out = self.dut_run(cmd, timeout=20)
                traces[label] = strip_ansi(out)
            except Exception as e:
                traces[label] = f"ERROR: {e}"
                self.log(f"  Trace capture [{label}] failed: {e}")

        return traces

    def _is_datapath_affecting(self, test_def: dict) -> bool:
        """Tests that can cause transient SSH/management loss."""
        cmd = test_def.get("ha_command", "")
        return "wb_agent" in cmd or ("ncp" in cmd.lower() and "datapath" in cmd.lower())

    def inter_test_health_check(self, prev_test: dict) -> bool:
        """Quick health check between tests. Verifies BGP is Established and device is responsive.
        Returns False if device is unhealthy (next test should wait or abort)."""
        try:
            out = self.dut_run("show bgp ipv4 flowspec-vpn summary", timeout=15)
            state = parse_bgp_state(out)
            routes = parse_flowspec_route_count(out)
            if state != "Established":
                self.log(f"  Health check: BGP={state} -- waiting for recovery...")
                for wait_round in range(12):
                    time.sleep(10)
                    out = self.dut_run("show bgp ipv4 flowspec-vpn summary", timeout=15)
                    state = parse_bgp_state(out)
                    routes = parse_flowspec_route_count(out)
                    if state == "Established":
                        self.log(f"  Health check: BGP recovered after {(wait_round+1)*10}s ({routes} routes)")
                        return True
                self.log(f"  Health check: BGP still {state} after 120s. Next test may fail.")
                return False
            return True
        except Exception as e:
            self.log(f"  Health check failed: {e}")
            return False

    def run_all_tests(self, test_ids: list[str] = None) -> list[dict]:
        """Run tests and produce report. Supports resume from crashed session."""
        defs = load_test_definitions()

        validation_errors = validate_test_definitions(defs)
        if validation_errors:
            self.log("=== TEST DEFINITION VALIDATION ===")
            for err in validation_errors:
                self.log(f"  [WARN] {err}")
            self.log(f"  {len(validation_errors)} issue(s) found in test definitions")

        tests = defs.get("tests", [])
        if test_ids:
            tests = [t for t in tests if t["id"] in test_ids]

        already_done = load_progress(str(self.run_dir))
        if already_done:
            self.log(f"Resuming: {len(already_done)} tests already completed: {sorted(already_done)}")

        results = []
        completed_ids = list(already_done)

        for i, t in enumerate(tests):
            tid = t["id"]

            if tid in already_done:
                result_file = list(self.run_dir.glob(f"{tid}_*.json"))
                if result_file:
                    try:
                        r = json.loads(result_file[0].read_text())
                        results.append(r)
                        self.log(f"Skipping {tid} (already completed: {r.get('verdict', '?')})")
                        continue
                    except Exception:
                        pass

            if i > 0:
                prev_test_def = tests[i - 1]
                if self._is_datapath_affecting(prev_test_def):
                    self.log("Cooldown 15s after datapath-affecting test...")
                    time.sleep(15)
                if prev_test_def["id"] not in already_done:
                    self.inter_test_health_check(prev_test_def)

            try:
                if ACTIVE_SESSION.exists():
                    with open(ACTIVE_SESSION) as f:
                        sd = json.load(f)
                    sd["current_test"] = tid
                    sd["last_test_ha_type"] = t.get("ha_type", "")
                    with open(ACTIVE_SESSION, "w") as f:
                        json.dump(sd, f, indent=2)
            except Exception:
                pass

            save_progress(str(self.run_dir), completed_ids, current_test=tid)

            r = self.run_single_test(t)
            results.append(r)

            completed_ids.append(tid)
            save_progress(str(self.run_dir), completed_ids)

            (self.run_dir / f"{t['id']}_{t['name'].replace(' ', '_').lower()[:30]}.json").write_text(
                json.dumps(r, indent=2)
            )
            (self.run_dir / "run_log.md").write_text("\n".join(self.log_lines))

            if self.stop_on_fail and r.get("verdict") == "FAIL":
                self.log(f"=== STOP ON FAIL: {tid} returned FAIL ===")
                if r.get("escalation_hint"):
                    self.log(f"  Escalation: {r['escalation_hint']}")
                if r.get("collateral_damage"):
                    self.log(f"  Collateral: {len(r['collateral_damage'])} process(es) crashed unexpectedly")
                self.log("Remaining tests will not run. Fix the issue and --resume, or re-run without --stop-on-fail.")
                break

        try:
            if ACTIVE_SESSION.exists():
                with open(ACTIVE_SESSION) as f:
                    session_data = json.load(f)
                session_data["active"] = False
                session_data["flowspec_test_active"] = False
                session_data["current_test"] = None
                session_data["last_test_ha_type"] = None
                session_data["closed_at"] = datetime.utcnow().isoformat()
                with open(ACTIVE_SESSION, "w") as f:
                    json.dump(session_data, f, indent=2)
        except Exception as e:
            self.log(f"WARNING: Could not close active_ha_session: {e}")

        try:
            if PROGRESS_FILE.exists():
                PROGRESS_FILE.unlink()
        except Exception:
            pass

        return results

    def generate_report(self, results: list[dict]) -> str:
        """Generate Markdown summary with 4-layer evidence table."""
        lines = [
            "# FlowSpec VPN HA Test Report (SW-236398)",
            "",
            f"Device: {self.device['hostname']}",
            f"Mode: {self.device_mode} ({self.system_type})",
            f"Run: {datetime.now().isoformat()}",
            f"Route source: {self.route_source}",
            f"Spirent traffic: {'Active' if self.spirent_available else 'Not available'}",
            "",
            "## 4-Layer Summary",
            "",
            "| Test | Name | Control-Plane | Datapath (NCP) | Collateral | Traffic (Spirent) | Packet (XRAY) | Recovery | Verdict |",
            "|------|------|--------------|----------------|------------|-------------------|---------------|----------|---------|",
        ]
        for r in results:
            if r.get("verdict") == "SKIP":
                lines.append(f"| {r['id']} | {r.get('name', '')} | - | - | - | - | - | - | SKIP |")
                continue
            cp = r.get("cp_verdict", r.get("verdict", "?"))
            ncp_b = r.get("ncp_before", "?")
            ncp_a = r.get("ncp_after", "?")
            dp = r.get("dp_verdict", "?")
            dp_detail = f"{dp} ({ncp_a}/{ncp_b})"
            col = r.get("collateral_verdict", "PASS")
            col_count = len(r.get("collateral_damage", []))
            col_detail = col if col == "PASS" else f"FAIL ({col_count} crashed)"
            sp = r.get("sp_verdict", "N/A")
            sp_loss = r.get("spirent_loss", 0)
            sp_detail = sp if sp == "N/A" else f"{sp} ({sp_loss} lost)"
            xr = r.get("xray_verdict", "SKIP")
            xr_pkts = r.get("xray_packets", 0)
            xr_detail = xr if xr in ("SKIP", "ERROR") else f"{xr} ({xr_pkts}pkts)"
            rec = r.get("recovery_sec")
            rec_str = f"{rec:.1f}s" if isinstance(rec, (int, float)) else "-"
            lines.append(f"| {r['id']} | {r.get('name', '')} | {cp} | {dp_detail} | {col_detail} | "
                         f"{sp_detail} | {xr_detail} | {rec_str} | {r.get('verdict', '?')} |")

        passed = sum(1 for r in results if r.get("verdict") == "PASS")
        warned = sum(1 for r in results if r.get("verdict") == "WARNING")
        failed = sum(1 for r in results if r.get("verdict") == "FAIL")
        skipped = sum(1 for r in results if r.get("verdict") == "SKIP")
        errors = sum(1 for r in results if r.get("verdict") == "ERROR")
        lines.extend([
            "",
            f"**Result: {passed} PASS / {warned} WARNING / {failed} FAIL / {errors} ERROR / {skipped} SKIP "
            f"(out of {len(results)} tests)**",
            "",
            f"Traffic verification: {'Spirent active during all tests' if self.spirent_available else 'Spirent not available (control-plane + datapath only)'}",
            "",
        ])

        failed_tests = [r for r in results if r.get("verdict") == "FAIL"]
        if failed_tests:
            lines.extend(["## Failures & Escalation", ""])
            for r in failed_tests:
                lines.append(f"### {r['id']}: {r.get('name', '')}")
                fail_reasons = []
                if r.get("cp_verdict") == "FAIL":
                    fail_reasons.append("Control-plane: BGP not recovered")
                if r.get("dp_verdict") == "FAIL":
                    fail_reasons.append(f"Datapath: NCP {r.get('ncp_after', '?')}/{r.get('ncp_before', '?')} rules")
                if r.get("collateral_verdict") == "FAIL":
                    for cd in r.get("collateral_damage", []):
                        fail_reasons.append(f"Collateral: {cd['process']} +{cd['restart_delta']} restarts")
                if r.get("sp_verdict") == "FAIL":
                    fail_reasons.append(f"Traffic: {r.get('spirent_loss', 0)} frames lost")
                for reason in fail_reasons:
                    lines.append(f"- {reason}")
                if r.get("escalation_hint"):
                    lines.extend(["", f"**Escalation:** `{r['escalation_hint']}`", ""])
                lines.append("")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="FlowSpec VPN HA Test Orchestrator (SW-236398)")
    parser.add_argument("--device", default="YOR_CL_PE-4", help="DUT hostname")
    parser.add_argument("--vlan", type=int, default=None, help="Spirent BGP VLAN (default 212, use 219 if BD exists)")
    parser.add_argument("--spirent-ip", default=None, help="Spirent BGP peer IP")
    parser.add_argument("--dut-ip", default=None, help="DUT neighbor IP (gateway for Spirent)")
    parser.add_argument("--tests", default=None, help="Comma-separated test IDs (e.g. test_01,test_02)")
    parser.add_argument("--test", default=None, help="Single test ID")
    parser.add_argument("--dry-run", action="store_true", help="Do not trigger HA events")
    parser.add_argument("--standby-ip", default=None, help="[CL only] Standby NCC mgmt IP - use for NCC restart tests to avoid SSH loss")
    parser.add_argument("--resume", action="store_true", help="Resume from last crashed/interrupted run")
    parser.add_argument("--stop-on-fail", action="store_true", help="Abort after first FAIL verdict (with escalation hint)")
    args = parser.parse_args()

    stale = detect_stale_session()
    if stale:
        recover_stale_session(stale)

    acquire_lock()
    import atexit
    atexit.register(release_lock)

    test_ids = None
    if args.test:
        test_ids = [args.test]
    elif args.tests:
        test_ids = [t.strip() for t in args.tests.split(",")]

    if args.resume and PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE) as f:
                prog = json.load(f)
            prev_run_dir = prog.get("run_dir", "")
            if prev_run_dir and Path(prev_run_dir).exists():
                run_dir = Path(prev_run_dir)
                print(f"[RESUME] Resuming into: {run_dir}")
            else:
                run_dir = RESULTS_DIR / f"SW-236398_{datetime.now().strftime('%Y%m%d_%H%M')}"
                run_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            run_dir = RESULTS_DIR / f"SW-236398_{datetime.now().strftime('%Y%m%d_%H%M')}"
            run_dir.mkdir(parents=True, exist_ok=True)
    else:
        run_dir = RESULTS_DIR / f"SW-236398_{datetime.now().strftime('%Y%m%d_%H%M')}"
        run_dir.mkdir(parents=True, exist_ok=True)

    orch = FlowSpecHATest(args.device, run_dir, dry_run=args.dry_run, standby_ncc_ip=args.standby_ip)
    orch.stop_on_fail = args.stop_on_fail
    if args.vlan is not None:
        orch.vlan = args.vlan
    if args.spirent_ip:
        orch.spirent_peer_ip = args.spirent_ip
    if args.dut_ip:
        orch.dut_neighbor_ip = args.dut_ip
    orch.log(f"Starting FlowSpec HA tests on {args.device}")
    orch.log(f"VLAN={orch.vlan} Spirent={orch.spirent_peer_ip} DUT={orch.dut_neighbor_ip} standby_ip={args.standby_ip}")

    # Update active_ha_session for cross-command integration
    ACTIVE_SESSION.parent.mkdir(parents=True, exist_ok=True)
    session_data = {
        "version": 1,
        "active": True,
        "flowspec_test_active": True,
        "flowspec_test_id": "SW-236398",
        "device": {"network_mapper_name": args.device, "system_name": args.device},
        "device_mode": None,  # Set after detect_device_mode
        "spirent_session_name": orch.session_name,
        "flowspec_rules_injected": FLOWSPEC_RULE_COUNT,
        "traffic_baseline_mbps": 100,
        "run_dir": str(run_dir),
    }
    with open(ACTIVE_SESSION, "w") as f:
        json.dump(session_data, f, indent=2)
    orch.log(f"Results: {run_dir}")

    if not orch.setup_spirent():
        orch.log("Spirent setup failed. Trying pre-existing rules workaround...")
        if not orch.setup_preexisting_rules():
            orch.log("ERROR: Setup failed (Spirent + pre-existing). Exiting.")
            (run_dir / "run_log.md").write_text("\n".join(orch.log_lines))
            sys.exit(1)
        orch.log("Proceeding with pre-existing FlowSpec rules")
        sp_ok, sp_out = run_spirent(["stats", "--json", "--session-name", orch.session_name])
        if sp_ok and "tx" in sp_out:
            orch.spirent_available = True
            orch.spirent_baseline = orch.spirent_poll_stats()
            orch.log("Spirent traffic detected from external setup")

    orch.detect_device_mode()
    orch.capture_system_identity()
    if orch.device_mode == "cluster":
        orch._refresh_nce_ips()
    session_data["device_mode"] = orch.device_mode
    session_data["system_type"] = orch.system_type
    session_data["system_name"] = orch.system_name
    session_data["image_version"] = getattr(orch, "image_version", "unknown")
    with open(ACTIVE_SESSION, "w") as f:
        json.dump(session_data, f, indent=2)

    if not orch.verify_preflight():
        orch.log("ABORTING: Pre-flight checks failed.")
        (run_dir / "run_log.md").write_text("\n".join(orch.log_lines))
        (run_dir / "SUMMARY.md").write_text("# ABORTED\n\nPre-flight checks failed. See run_log.md.")
        sys.exit(1)

    results = []
    try:
        results = orch.run_all_tests(test_ids)
    finally:
        try:
            if ACTIVE_SESSION.exists():
                with open(ACTIVE_SESSION) as f:
                    sd = json.load(f)
                sd["active"] = False
                sd["flowspec_test_active"] = False
                sd["closed_at"] = datetime.utcnow().isoformat()
                with open(ACTIVE_SESSION, "w") as f:
                    json.dump(sd, f, indent=2)
        except Exception:
            pass
    report = orch.generate_report(results)
    (run_dir / "SUMMARY.md").write_text(report)
    (run_dir / "run_log.md").write_text("\n".join(orch.log_lines))
    orch.log(f"Done. Report: {run_dir / 'SUMMARY.md'}")
    print(report)


if __name__ == "__main__":
    main()
