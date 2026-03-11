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
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HA_DIR = Path(__file__).parent
TEST_DEFS = HA_DIR / "test_definitions" / "sw_236398.json"
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
        """Take snapshot of DUT state. Retries per-command on SSH timeout."""
        snap = {"label": label, "timestamp": datetime.now().isoformat(), "commands": {}}
        for cmd in commands:
            try:
                snap["commands"][cmd] = self.dut_run(cmd)
            except Exception as e:
                snap["commands"][cmd] = f"ERROR: {e}"
                self.log(f"  Snapshot command failed: {cmd[:50]}...")
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
        """Verify rules present, BGP Established, traffic path ready."""
        out = self.dut_run("show bgp ipv4 flowspec-vpn summary")
        n = parse_flowspec_route_count(out)
        if n < 0:
            n = len(re.findall(r"\d+\.\d+\.\d+\.\d+/\d+", out))
        self.log(f"FlowSpec routes on DUT: {n}")
        expected = getattr(self, "effective_rule_count", FLOWSPEC_RULE_COUNT)
        if n < expected * 0.9:
            self.log(f"WARNING: Expected ~{expected} rules, got {n}")
        out = self.dut_run("show bgp ipv4 flowspec-vpn summary")
        state = parse_bgp_state(out)
        self.log(f"BGP FlowSpec-VPN state: {state}")
        if state != "Established":
            self.log("WARNING: BGP not Established")
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
        """Trigger HA event via SSH. Returns True if triggered (may disconnect)."""
        # Sequential (test 15)
        commands = test_def.get("ha_commands")
        if commands:
            for i, cmd in enumerate(commands):
                cmd = self.resolve_template(cmd)
                self.log(f"Triggering ({i+1}/{len(commands)}): {cmd}")
                if not self.dry_run:
                    self.dut_shell([cmd])
                    time.sleep(3)
            return True

        # LOFD via NCF admin-disable (config-mode test)
        if test_def.get("requires_config_mode"):
            config_cmds = test_def.get("config_commands", [])
            if not config_cmds:
                self.log("SKIP: requires_config_mode but no config_commands defined")
                return False
            self.log(f"Triggering LOFD: disabling NCF via config mode")
            if not self.dry_run:
                self.dut_shell(["set cli-no-confirm"])
                self.dut_config(config_cmds)
            return True

        cmd = test_def.get("ha_command", "")
        if not cmd or "SEQUENTIAL" in cmd:
            self.log(f"SKIP: {cmd}")
            return False

        cmd = self.resolve_template(cmd)
        repeat = test_def.get("ha_command_repeat", 1)
        for i in range(repeat):
            self.log(f"Triggering ({i+1}/{repeat}): {cmd}")
            if not self.dry_run:
                self.dut_shell(["set cli-no-confirm", cmd])
                if repeat > 1:
                    time.sleep(5)
        return True

    def poll_recovery(self, test_def: dict, max_wait: int = None) -> dict:
        """Poll until recovered or timeout. Uses multi-IP reconnect for destructive tests.
        After 40% of max_wait, re-reads devices.json for DHCP-updated IPs."""
        max_wait = max_wait or test_def.get("max_recovery_sec", 120)
        kills_ssh = test_def.get("kills_ssh", False)
        start = time.time()
        last_state = {}
        spirent_polls = []
        poll_num = 0
        ssh_connected = not kills_ssh
        db_refreshed = False
        cmd = "show bgp ipv4 flowspec-vpn summary"

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

            last_state["bgp"] = parse_bgp_state(out)
            last_state["routes"] = parse_flowspec_route_count(out)

            if self.spirent_available:
                sp = self.spirent_poll_stats()
                if sp.get("error"):
                    self.spirent_reachable = False
                    self.log(f"  Poll #{poll_num} ({elapsed}s): Spirent unreachable — traffic stats unavailable")
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
                return {"recovered": True, "elapsed": elapsed_sec,
                        "state": last_state, "spirent_polls": spirent_polls,
                        "convergence_times": conv}
            time.sleep(5)
        return {"recovered": False, "elapsed": max_wait, "state": last_state,
                "spirent_polls": spirent_polls, "convergence_times": {}}

    def run_single_test(self, test_def: dict) -> dict:
        """Run one test: safety check, before snapshot, trigger, poll, after snapshot, diff.

        For config-mode tests (LOFD), recovery is guaranteed in a finally block.
        For NCC/NCP restart tests, node recovery is verified after FlowSpec recovery.
        """
        tid = test_def["id"]
        name = test_def["name"]
        ha_type = test_def.get("ha_type", "")
        self.log(f"=== {tid}: {name} ===")

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
            except Exception:
                before["ncp_counters"] = {"installed": 0, "packets": 0, "bytes": 0}
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
            except Exception:
                after["ncp_counters"] = {"installed": 0, "packets": 0, "bytes": 0}
            try:
                tcam_out = self.dut_run("show system npu-resources resource-type flowspec", timeout=15)
                after["tcam"] = parse_tcam_usage(tcam_out)
            except Exception:
                after["tcam"] = {"installed": 0, "total": 0, "percent": 0.0}

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

            overall = "PASS"
            if cp_verdict == "FAIL" or dp_verdict == "FAIL" or sp_verdict == "FAIL":
                overall = "FAIL"
            elif cp_verdict == "WARNING" or sp_verdict == "WARNING":
                overall = "WARNING"
            elif sp_verdict == "UNKNOWN (unreachable)" and cp_verdict == "PASS" and dp_verdict == "PASS":
                overall = "PASS WITH WARNINGS"

            result = {
                "id": tid, "name": name, "verdict": overall,
                "recovery_sec": recovery.get("elapsed"), "ha_type": ha_type,
                "cp_verdict": cp_verdict, "dp_verdict": dp_verdict,
                "sp_verdict": sp_verdict,
                "xray_verdict": xray_result.get("verdict", "SKIP"),
                "xray_packets": xray_result.get("packets_captured", 0),
                "ncp_before": ncp_before_inst, "ncp_after": ncp_after_inst,
                "tcam_before": tcam_before, "tcam_after": tcam_after,
                "spirent_loss": spirent_loss, "counter_delta": counter_delta,
                "before_routes": (before["commands"].get("show bgp ipv4 flowspec-vpn summary", ""))[:200],
                "after_routes": (after["commands"].get("show bgp ipv4 flowspec-vpn summary", ""))[:200],
            }
            self.log(f"Verdict: {overall} (CP={cp_verdict} DP={dp_verdict} "
                     f"Spirent={sp_verdict} XRAY={xray_result.get('verdict', 'SKIP')})")
            return result
        except Exception as exc:
            self.log(f"TEST ERROR: {exc}")
            return {"id": tid, "name": name, "verdict": "ERROR", "reason": str(exc)}
        finally:
            # CRITICAL: Always recover NCF for LOFD tests, even on crash/exception
            if lofd_recovery_needed:
                self.log("FINALLY: Ensuring LOFD recovery (NCF re-enable)...")
                self.ensure_lofd_recovery(test_def, ncf_id=lofd_ncf_id)
            if original_device:
                self.device = original_device

    def _is_datapath_affecting(self, test_def: dict) -> bool:
        """Tests that can cause transient SSH/management loss."""
        cmd = test_def.get("ha_command", "")
        return "wb_agent" in cmd or ("ncp" in cmd.lower() and "datapath" in cmd.lower())

    def run_all_tests(self, test_ids: list[str] = None) -> list[dict]:
        """Run tests and produce report."""
        defs = load_test_definitions()
        tests = defs.get("tests", [])
        if test_ids:
            tests = [t for t in tests if t["id"] in test_ids]
        results = []
        for i, t in enumerate(tests):
            if i > 0 and self._is_datapath_affecting(tests[i - 1]):
                self.log("Cooldown 15s after datapath-affecting test...")
                time.sleep(15)
            r = self.run_single_test(t)
            results.append(r)
            # Save per-test result
            (self.run_dir / f"{t['id']}_{t['name'].replace(' ', '_').lower()[:30]}.json").write_text(
                json.dumps(r, indent=2)
            )
            # Incremental run_log so progress visible if interrupted
            (self.run_dir / "run_log.md").write_text("\n".join(self.log_lines))
        try:
            if ACTIVE_SESSION.exists():
                with open(ACTIVE_SESSION) as f:
                    session_data = json.load(f)
                session_data["active"] = False
                session_data["flowspec_test_active"] = False
                session_data["closed_at"] = datetime.utcnow().isoformat()
                with open(ACTIVE_SESSION, "w") as f:
                    json.dump(session_data, f, indent=2)
        except Exception as e:
            self.log(f"WARNING: Could not close active_ha_session: {e}")
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
            "| Test | Name | Control-Plane | Datapath (NCP) | Traffic (Spirent) | Packet (XRAY) | Recovery | Verdict |",
            "|------|------|--------------|----------------|-------------------|---------------|----------|---------|",
        ]
        for r in results:
            if r.get("verdict") == "SKIP":
                lines.append(f"| {r['id']} | {r.get('name', '')} | - | - | - | - | - | SKIP |")
                continue
            cp = r.get("cp_verdict", r.get("verdict", "?"))
            ncp_b = r.get("ncp_before", "?")
            ncp_a = r.get("ncp_after", "?")
            dp = r.get("dp_verdict", "?")
            dp_detail = f"{dp} ({ncp_a}/{ncp_b})"
            sp = r.get("sp_verdict", "N/A")
            sp_loss = r.get("spirent_loss", 0)
            sp_detail = sp if sp == "N/A" else f"{sp} ({sp_loss} lost)"
            xr = r.get("xray_verdict", "SKIP")
            xr_pkts = r.get("xray_packets", 0)
            xr_detail = xr if xr in ("SKIP", "ERROR") else f"{xr} ({xr_pkts}pkts)"
            rec = r.get("recovery_sec")
            rec_str = f"{rec:.1f}s" if isinstance(rec, (int, float)) else "-"
            lines.append(f"| {r['id']} | {r.get('name', '')} | {cp} | {dp_detail} | "
                         f"{sp_detail} | {xr_detail} | {rec_str} | {r.get('verdict', '?')} |")

        passed = sum(1 for r in results if r.get("verdict") == "PASS")
        warned = sum(1 for r in results if r.get("verdict") == "WARNING")
        failed = sum(1 for r in results if r.get("verdict") == "FAIL")
        skipped = sum(1 for r in results if r.get("verdict") == "SKIP")
        lines.extend([
            "",
            f"**Result: {passed} PASS / {warned} WARNING / {failed} FAIL / {skipped} SKIP "
            f"(out of {len(results)} tests)**",
            "",
            f"Traffic verification: {'Spirent active during all tests' if self.spirent_available else 'Spirent not available (control-plane + datapath only)'}",
            "",
        ])
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
    args = parser.parse_args()

    acquire_lock()
    import atexit
    atexit.register(release_lock)

    test_ids = None
    if args.test:
        test_ids = [args.test]
    elif args.tests:
        test_ids = [t.strip() for t in args.tests.split(",")]

    run_dir = RESULTS_DIR / f"SW-236398_{datetime.now().strftime('%Y%m%d_%H%M')}"
    run_dir.mkdir(parents=True, exist_ok=True)

    orch = FlowSpecHATest(args.device, run_dir, dry_run=args.dry_run, standby_ncc_ip=args.standby_ip)
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
    with open(ACTIVE_SESSION, "w") as f:
        json.dump(session_data, f, indent=2)
    orch.verify_preflight()
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
