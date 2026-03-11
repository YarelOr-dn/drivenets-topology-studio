#!/usr/bin/env python3
"""
sw_234480_scale_test.py -- FlowSpec VPN Scale Test Orchestrator (SW-234480)

Runs 6 quick-win scale tests: injects bulk FlowSpec-VPN routes via ExaBGP (/BGP),
polls DUT convergence/DP via SSH, measures timing, produces per-test reports.

Usage:
    python3 sw_234480_scale_test.py --device PE-4 [--tests test_01,test_03] [--dry-run]

Requires: paramiko, bgp_tool.py with active ExaBGP session for the device.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HA_DIR = Path(__file__).parent
TEST_DEFS = HA_DIR / "test_definitions" / "sw_234480.json"
RESULTS_DIR = HA_DIR / "test_results"
BGP_TOOL = Path.home() / "SCALER" / "FLOWSPEC_VPN" / "exabgp" / "bgp_tool.py"
SPIRENT_TOOL = Path.home() / "SCALER" / "SPIRENT" / "spirent_tool.py"
PID_LOCK = HA_DIR / ".scale_orchestrator.pid"

try:
    from ha_ssh import run_ssh_shell
except ImportError:
    sys.path.insert(0, str(HA_DIR))
    from ha_ssh import run_ssh_shell

from ha_flowspec_test import (
    load_device,
    parse_bgp_state,
    parse_flowspec_ncp_counters,
    parse_flowspec_route_count,
    parse_tcam_usage,
    run_ssh_command,
)


def acquire_lock() -> bool:
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


def load_scale_defs() -> dict:
    if not TEST_DEFS.exists():
        raise FileNotFoundError(f"Test definitions not found: {TEST_DEFS}")
    with open(TEST_DEFS) as f:
        return json.load(f)


class FlowSpecScaleTest:
    """Orchestrator for FlowSpec VPN scale tests (SW-234480)."""

    def __init__(self, device_name: str, run_dir: Path, dry_run: bool = False):
        self.device = load_device(device_name)
        self.run_dir = run_dir
        self.dry_run = dry_run
        self.log_lines: list[str] = []
        self.ncp_id: int | None = None
        self.peer_ip: str | None = None
        self.defs = load_scale_defs()
        self.session_id = self.defs.get("bgp_session_id", "pe_4")
        self.default_rt = self.defs.get("default_rt", "1234567:301")
        self.default_rd = self.defs.get("default_rd", "1.1.1.1:200")
        self.rt_overrides = self.defs.get("rt_overrides", {
            "flowspec-vpn-ipv6": "1234567:401",
        })

    def log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        self.log_lines.append(line)
        print(line, flush=True)

    def dut_run(self, command: str, timeout: int = 30, retries: int = 3) -> str:
        delays = [5, 10, 20]
        last_err: Exception | None = None
        for attempt in range(retries):
            try:
                out, _, _ = run_ssh_command(
                    self.device["ip"], self.device["username"],
                    self.device["password"], command, timeout=timeout,
                )
                return out
            except Exception as e:
                last_err = e
                if attempt < retries - 1:
                    wait = delays[min(attempt, len(delays) - 1)]
                    self.log(f"  SSH retry {attempt + 1}/{retries} in {wait}s ({e})")
                    time.sleep(wait)
                else:
                    raise
        raise last_err  # type: ignore[misc]

    def dut_shell(self, commands: list[str], timeout: int = 60) -> str:
        return run_ssh_shell(
            self.device["ip"], self.device["username"],
            self.device["password"], commands, timeout=timeout,
        )

    # ── BGP Tool helpers ──────────────────────────────────────────────

    def _run_bgp_tool(self, args: list[str], timeout: int = 300) -> tuple[bool, str]:
        full = [sys.executable, str(BGP_TOOL)] + args
        self.log(f"  bgp_tool: {' '.join(args[:6])}")
        if self.dry_run and args[0] not in ("status",):
            return True, '{"dry_run": true}'
        try:
            r = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
            out = (r.stdout or "") + (r.stderr or "")
            return r.returncode == 0, out
        except subprocess.TimeoutExpired:
            return False, f"Timeout ({timeout}s)"
        except Exception as e:
            return False, str(e)

    def _run_spirent(self, args: list[str], timeout: int = 60) -> tuple[bool, str]:
        full = [sys.executable, str(SPIRENT_TOOL)] + args
        if self.dry_run:
            return True, '{"dry_run": true}'
        try:
            r = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
            out = (r.stdout or "") + (r.stderr or "")
            return r.returncode == 0, out
        except subprocess.TimeoutExpired:
            return False, f"Timeout ({timeout}s)"
        except Exception as e:
            return False, str(e)

    def inject_routes(self, mode: str, count: int, fast: bool = True,
                      timeout: int = 600) -> tuple[bool, dict]:
        rt = self.rt_overrides.get(mode, self.default_rt)
        args = [
            "scale", "--session-id", self.session_id,
            "--mode", mode, "--count", str(count),
            "--rt", rt, "--rd", self.default_rd,
        ]
        if fast:
            args.append("--fast")
        ok, out = self._run_bgp_tool(args, timeout=timeout)
        result: dict = {}
        if ok:
            try:
                result = json.loads(out.strip().split("\n")[-1])
            except (json.JSONDecodeError, IndexError):
                result = {"raw": out[:500]}
        else:
            result = {"error": out[:500]}
        return ok, result

    def withdraw_routes(self, mode: str, keep: int = 0,
                        timeout: int = 300) -> tuple[bool, dict]:
        args = [
            "scale", "--session-id", self.session_id,
            "--mode", mode, "--withdraw",
        ]
        if keep > 0:
            args.extend(["--keep", str(keep)])
        ok, out = self._run_bgp_tool(args, timeout=timeout)
        result: dict = {}
        if ok:
            try:
                result = json.loads(out.strip().split("\n")[-1])
            except (json.JSONDecodeError, IndexError):
                result = {"raw": out[:500]}
        else:
            result = {"error": out[:500]}
        return ok, result

    # ── DUT Polling ───────────────────────────────────────────────────

    def poll_bgp_convergence(self, target_pfx: int, timeout_sec: int = 180,
                             poll_interval: int = 2) -> dict:
        """Poll show bgp ipv4 flowspec-vpn summary until PfxRcd reaches target."""
        t0 = time.time()
        last_count = 0
        converged = False
        session_dropped = False
        polls: list[dict] = []

        while time.time() - t0 < timeout_sec:
            try:
                out = self.dut_run("show bgp ipv4 flowspec-vpn summary", timeout=15, retries=1)
                count = parse_flowspec_route_count(out)
                state = parse_bgp_state(out)
                elapsed = round(time.time() - t0, 1)
                polls.append({"t": elapsed, "pfxrcd": count, "state": state})

                if state != "Established":
                    session_dropped = True

                if count != last_count:
                    self.log(f"  PfxRcd={count} state={state} t={elapsed}s")
                last_count = count

                if count >= target_pfx:
                    converged = True
                    self.log(f"  Converged: PfxRcd={count} in {elapsed}s")
                    break
            except Exception as e:
                self.log(f"  Poll error: {e}")

            time.sleep(poll_interval)

        convergence_sec = round(time.time() - t0, 1)
        return {
            "converged": converged,
            "convergence_sec": convergence_sec,
            "final_pfxrcd": last_count,
            "session_dropped": session_dropped,
            "polls": polls[-10:],
        }

    def check_dp_installed(self) -> dict:
        """Read NCP flowspec installed count and TCAM usage.
        Uses device-side pipe count for accuracy at scale (avoids SSH truncation)."""
        ncp_id = self._get_ncp_id()

        try:
            count_out = self.dut_run(
                f'show flowspec ncp {ncp_id} | include "status: installed" | count',
                timeout=30)
            m = re.search(r"Count:\s*(\d+)", count_out)
            ncp_installed = int(m.group(1)) if m else 0
        except Exception:
            ncp_installed = 0

        tcam_out = self.dut_run("show system npu-resources resource-type flowspec", timeout=20)
        tcam = parse_tcam_usage(tcam_out)

        if ncp_installed == 0 and tcam.get("installed", 0) > 0:
            ncp_installed = tcam["installed"]

        return {"ncp_installed": ncp_installed, "tcam": tcam}

    def check_capacity_warning(self) -> bool:
        """Check if flowspec capacity warning appears in logging."""
        try:
            out = self.dut_run("show logging | include flowspec", timeout=15)
            return bool(re.search(r"capacity|limit|exceed|full", out, re.I))
        except Exception:
            return False

    def _get_ncp_id(self) -> int:
        if self.ncp_id is not None:
            return self.ncp_id
        out = self.dut_run("show system")
        for line in out.split("\n"):
            m = re.search(r"\|\s*NCP\s*\|\s*(\d+)\s*\|.*?\|\s*up\s*\|", line)
            if m:
                self.ncp_id = int(m.group(1))
                return self.ncp_id
        self.ncp_id = 6
        return self.ncp_id

    def _find_fsvpn_peer(self) -> str | None:
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

    def ensure_clean_state(self, mode: str) -> None:
        """Withdraw any existing routes from this mode so test starts clean."""
        self.log("  Ensuring clean state (withdraw existing routes)...")
        ok, result = self.withdraw_routes(mode)
        if ok:
            self.log(f"  Cleaned: {result.get('withdrawn', 0)} routes withdrawn")
        else:
            self.log("  No existing routes to withdraw (clean)")

    # ── Pre-flight ────────────────────────────────────────────────────

    def preflight(self) -> bool:
        self.log("=== Pre-flight Checks ===")

        self.log("Checking DUT SSH connectivity...")
        try:
            out = self.dut_run("show system version", timeout=15)
            if "System Name" in out or "System" in out:
                self.log("  DUT reachable")
            else:
                self.log("  WARNING: Unexpected output from show system version")
        except Exception as e:
            self.log(f"  FAIL: DUT unreachable ({e})")
            return False

        self.log("Checking BGP FlowSpec-VPN session...")
        out = self.dut_run("show bgp ipv4 flowspec-vpn summary")
        state = parse_bgp_state(out)
        self.log(f"  BGP state: {state}")
        if state != "Established":
            self.log("  WARNING: BGP FlowSpec-VPN not Established")

        self.peer_ip = self._find_fsvpn_peer()
        if self.peer_ip:
            self.log(f"  Peer IP: {self.peer_ip}")
        else:
            self.log("  WARNING: Could not discover FlowSpec-VPN peer IP")

        self.log("Detecting NCP ID...")
        ncp_id = self._get_ncp_id()
        self.log(f"  NCP ID: {ncp_id}")

        self.log("Checking ExaBGP session...")
        ok, out = self._run_bgp_tool(["status", "--session-id", self.session_id], timeout=15)
        if ok and "active" in out.lower():
            self.log(f"  ExaBGP session '{self.session_id}' active")
        else:
            self.log(f"  WARNING: ExaBGP session '{self.session_id}' may not be active")
            self.log(f"  Start it: python3 bgp_tool.py start --session-id {self.session_id} --peer-ip <RR_IP>")

        return True

    # ── Test Runners ──────────────────────────────────────────────────

    def run_test_01(self, test_def: dict) -> dict:
        """Test 1: Max BGP Routes (20K) + Convergence < 60s."""
        tid = test_def["id"]
        count = test_def["inject_count"]
        mode = test_def["inject_mode"]
        limit = test_def["convergence_limit_sec"]

        self.ensure_clean_state("stress")
        self.ensure_clean_state("flowspec-vpn-ipv4")

        self.log(f"Injecting {count} routes (mode={mode})...")
        t_inject_start = time.time()
        ok, inj = self.inject_routes(mode, count, fast=True, timeout=900)
        t_inject_end = time.time()
        inject_sec = round(t_inject_end - t_inject_start, 1)
        self.log(f"  Injection: ok={ok} time={inject_sec}s result={inj.get('injected', '?')}")

        if not ok:
            return {"id": tid, "name": test_def["name"], "verdict": "FAIL",
                    "reason": f"injection_failed: {inj.get('error', '')[:200]}"}

        self.log(f"Polling convergence (target={count}, timeout={limit + 120}s)...")
        conv = self.poll_bgp_convergence(count, timeout_sec=limit + 120)

        dp = self.check_dp_installed()
        self.log(f"  DP: NCP installed={dp['ncp_installed']} TCAM={dp['tcam']}")

        verdict = "PASS"
        reasons = []
        if not conv["converged"]:
            verdict = "FAIL"
            reasons.append(f"not_converged (got {conv['final_pfxrcd']}/{count})")
        elif conv["convergence_sec"] > limit:
            verdict = "FAIL"
            reasons.append(f"convergence {conv['convergence_sec']}s > {limit}s limit")
        if conv["session_dropped"]:
            verdict = "FAIL"
            reasons.append("session_dropped_during_injection")

        self.log(f"  Verdict: {verdict} ({', '.join(reasons) if reasons else 'OK'})")

        return {
            "id": tid, "name": test_def["name"], "verdict": verdict,
            "inject_time_sec": inject_sec,
            "convergence_sec": conv["convergence_sec"],
            "final_pfxrcd": conv["final_pfxrcd"],
            "dp_installed": dp["ncp_installed"],
            "tcam": dp["tcam"],
            "session_dropped": conv["session_dropped"],
            "reason": "; ".join(reasons) if reasons else None,
        }

    def run_test_03(self, test_def: dict) -> dict:
        """Test 3: Route Churn -- Bulk Add/Remove x5."""
        tid = test_def["id"]
        count = test_def["inject_count"]
        mode = test_def["inject_mode"]
        cycles = test_def.get("churn_cycles", 5)
        delay = test_def.get("churn_delay_sec", 5)

        self.ensure_clean_state(mode)

        session_stable = True
        cycle_results: list[dict] = []

        for cycle in range(1, cycles + 1):
            self.log(f"  Churn cycle {cycle}/{cycles}: injecting {count}...")
            ok, inj = self.inject_routes(mode, count, fast=True, timeout=600)
            if not ok:
                cycle_results.append({"cycle": cycle, "action": "inject", "ok": False})
                session_stable = False
                continue

            conv = self.poll_bgp_convergence(count, timeout_sec=120)
            out = self.dut_run("show bgp ipv4 flowspec-vpn summary", timeout=15)
            state = parse_bgp_state(out)
            if state != "Established":
                session_stable = False

            cycle_results.append({
                "cycle": cycle, "action": "inject", "ok": ok,
                "pfxrcd": conv["final_pfxrcd"], "state": state,
                "convergence_sec": conv["convergence_sec"],
            })

            self.log(f"  Churn cycle {cycle}/{cycles}: withdrawing...")
            time.sleep(delay)
            ok_w, wd = self.withdraw_routes(mode)
            time.sleep(delay)

            out = self.dut_run("show bgp ipv4 flowspec-vpn summary", timeout=15)
            pfx_after = parse_flowspec_route_count(out)
            state_after = parse_bgp_state(out)
            if state_after != "Established":
                session_stable = False

            cycle_results.append({
                "cycle": cycle, "action": "withdraw", "ok": ok_w,
                "pfxrcd": pfx_after, "state": state_after,
            })

            self.log(f"  Cycle {cycle} done: inject_pfx={conv['final_pfxrcd']} "
                     f"withdraw_pfx={pfx_after} state={state_after}")

        verdict = "PASS" if session_stable else "FAIL"
        reason = None if session_stable else "session_dropped_during_churn"
        self.log(f"  Verdict: {verdict}")

        return {
            "id": tid, "name": test_def["name"], "verdict": verdict,
            "cycles_completed": cycles,
            "session_stable": session_stable,
            "cycle_results": cycle_results,
            "reason": reason,
        }

    def run_test_08(self, test_def: dict) -> dict:
        """Test 8: Exceed DP Limit -- Incremental (14K)."""
        tid = test_def["id"]
        mode = test_def["inject_mode"]
        phases = test_def.get("inject_phases", [])
        expected_bgp = test_def["expected_bgp_accepted"]
        expected_dp = test_def["expected_dp_installed"]

        self.ensure_clean_state(mode)

        # Phase 1: Fill DP
        p1_count = phases[0]["count"] if phases else 12000
        self.log(f"  Phase 1: Injecting {p1_count} (fill DP)...")
        ok1, inj1 = self.inject_routes(mode, p1_count, fast=True, timeout=600)
        if not ok1:
            return {"id": tid, "name": test_def["name"], "verdict": "FAIL",
                    "reason": f"phase1_injection_failed: {inj1.get('error', '')[:200]}"}

        conv1 = self.poll_bgp_convergence(p1_count, timeout_sec=180)
        self.log(f"  Phase 1 converged: PfxRcd={conv1['final_pfxrcd']}")

        # Phase 2: Exceed
        p2_count = phases[1]["count"] if len(phases) > 1 else 2000
        self.log(f"  Phase 2: Injecting {p2_count} more (exceed)...")
        ok2, inj2 = self.inject_routes(mode, p1_count + p2_count, fast=True, timeout=600)
        if not ok2:
            self.log(f"  Phase 2 injection result: {inj2}")

        conv2 = self.poll_bgp_convergence(expected_bgp, timeout_sec=180)

        dp = self.check_dp_installed()
        cap_warn = self.check_capacity_warning()
        self.log(f"  DP: installed={dp['ncp_installed']} TCAM={dp['tcam']}")
        self.log(f"  Capacity warning in logs: {cap_warn}")

        verdict = "PASS"
        reasons = []
        if conv2["final_pfxrcd"] < expected_bgp * 0.95:
            verdict = "FAIL"
            reasons.append(f"BGP accepted {conv2['final_pfxrcd']}/{expected_bgp}")
        if dp["ncp_installed"] > expected_dp + 100:
            verdict = "FAIL"
            reasons.append(f"DP exceeded cap: {dp['ncp_installed']} > {expected_dp}")

        self.log(f"  Verdict: {verdict}")

        return {
            "id": tid, "name": test_def["name"], "verdict": verdict,
            "bgp_accepted": conv2["final_pfxrcd"],
            "dp_installed": dp["ncp_installed"],
            "dp_capped": dp["ncp_installed"] <= expected_dp + 100,
            "capacity_warning": cap_warn,
            "tcam": dp["tcam"],
            "reason": "; ".join(reasons) if reasons else None,
        }

    def run_test_09(self, test_def: dict) -> dict:
        """Test 9: Exceed DP Limit -- Bulk (15K)."""
        tid = test_def["id"]
        mode = test_def["inject_mode"]
        count = test_def["inject_count"]
        expected_bgp = test_def["expected_bgp_accepted"]
        expected_dp = test_def["expected_dp_installed"]

        self.ensure_clean_state("stress")
        self.ensure_clean_state("flowspec-vpn-ipv4")

        self.log(f"  Bulk injecting {count} routes (mode={mode})...")
        ok, inj = self.inject_routes(mode, count, fast=True, timeout=900)
        if not ok:
            return {"id": tid, "name": test_def["name"], "verdict": "FAIL",
                    "reason": f"injection_failed: {inj.get('error', '')[:200]}"}

        conv = self.poll_bgp_convergence(expected_bgp, timeout_sec=240)

        dp = self.check_dp_installed()
        cap_warn = self.check_capacity_warning()
        self.log(f"  BGP accepted: {conv['final_pfxrcd']}  DP installed: {dp['ncp_installed']}")
        self.log(f"  Capacity warning: {cap_warn}")

        # Stability check: wait 15s, verify no crash
        self.log("  Stability check (15s)...")
        time.sleep(15)
        try:
            out = self.dut_run("show system version", timeout=15)
            stable = "System" in out
        except Exception:
            stable = False

        verdict = "PASS"
        reasons = []
        if conv["final_pfxrcd"] < expected_bgp * 0.95:
            verdict = "FAIL"
            reasons.append(f"BGP accepted {conv['final_pfxrcd']}/{expected_bgp}")
        if dp["ncp_installed"] > expected_dp + 100:
            verdict = "FAIL"
            reasons.append(f"DP exceeded cap: {dp['ncp_installed']} > {expected_dp}")
        if not stable:
            verdict = "FAIL"
            reasons.append("DUT unstable/crash after bulk injection")

        self.log(f"  Verdict: {verdict}")

        return {
            "id": tid, "name": test_def["name"], "verdict": verdict,
            "bgp_accepted": conv["final_pfxrcd"],
            "dp_installed": dp["ncp_installed"],
            "dp_capped": dp["ncp_installed"] <= expected_dp + 100,
            "capacity_warning": cap_warn,
            "stable": stable,
            "tcam": dp["tcam"],
            "reason": "; ".join(reasons) if reasons else None,
        }

    def run_test_12(self, test_def: dict) -> dict:
        """Test 12: Session Flap Recovery at Scale (20K < 90s)."""
        tid = test_def["id"]
        mode = test_def["inject_mode"]
        count = test_def["inject_count"]
        limit = test_def["convergence_limit_sec"]
        expected_dp = test_def["expected_dp_installed"]

        self.ensure_clean_state("stress")
        self.ensure_clean_state("flowspec-vpn-ipv4")

        # Pre-load 20K routes
        self.log(f"  Pre-loading {count} routes...")
        ok, inj = self.inject_routes(mode, count, fast=True, timeout=900)
        if not ok:
            return {"id": tid, "name": test_def["name"], "verdict": "FAIL",
                    "reason": f"preload_failed: {inj.get('error', '')[:200]}"}

        conv_pre = self.poll_bgp_convergence(count, timeout_sec=240)
        if not conv_pre["converged"]:
            return {"id": tid, "name": test_def["name"], "verdict": "FAIL",
                    "reason": f"preload_not_converged (got {conv_pre['final_pfxrcd']}/{count})"}

        dp_wait = min(30, max(10, count // 1000))
        self.log(f"  Waiting {dp_wait}s for TCAM programming...")
        time.sleep(dp_wait)

        dp_pre = self.check_dp_installed()
        self.log(f"  Pre-flap: PfxRcd={conv_pre['final_pfxrcd']} DP={dp_pre['ncp_installed']}")

        # Flap
        peer = self.peer_ip
        if not peer:
            peer = self._find_fsvpn_peer()
        if not peer:
            return {"id": tid, "name": test_def["name"], "verdict": "FAIL",
                    "reason": "cannot_find_peer_ip_for_flap"}

        flap_cmd = test_def.get("flap_command", "clear bgp neighbor {peer_ip}")
        flap_cmd = flap_cmd.replace("{peer_ip}", peer)
        self.log(f"  Flapping session: {flap_cmd}")
        t_flap = time.time()

        if not self.dry_run:
            try:
                self.dut_shell([flap_cmd])
            except Exception as e:
                self.log(f"  Flap command error (expected): {e}")

        # Wait for drop and recovery
        time.sleep(3)
        self.log(f"  Polling recovery (target={count}, timeout={limit + 60}s)...")
        conv_post = self.poll_bgp_convergence(count, timeout_sec=limit + 60)
        recovery_sec = round(time.time() - t_flap, 1)

        # Allow TCAM programming to catch up after BGP convergence
        dp_wait = min(30, max(10, count // 1000))
        self.log(f"  Waiting {dp_wait}s for TCAM programming...")
        time.sleep(dp_wait)

        dp_post = self.check_dp_installed()
        self.log(f"  Post-flap: PfxRcd={conv_post['final_pfxrcd']} DP={dp_post['ncp_installed']} recovery={recovery_sec}s")

        verdict = "PASS"
        reasons = []
        if not conv_post["converged"]:
            verdict = "FAIL"
            reasons.append(f"not_recovered (got {conv_post['final_pfxrcd']}/{count})")
        elif recovery_sec > limit:
            verdict = "FAIL"
            reasons.append(f"recovery {recovery_sec}s > {limit}s limit")
        if dp_post["ncp_installed"] < expected_dp * 0.9:
            verdict = "FAIL"
            reasons.append(f"DP not restored: {dp_post['ncp_installed']}/{expected_dp}")

        self.log(f"  Verdict: {verdict}")

        return {
            "id": tid, "name": test_def["name"], "verdict": verdict,
            "recovery_sec": recovery_sec,
            "final_pfxrcd": conv_post["final_pfxrcd"],
            "dp_installed": dp_post["ncp_installed"],
            "dp_pre_flap": dp_pre["ncp_installed"],
            "tcam": dp_post["tcam"],
            "reason": "; ".join(reasons) if reasons else None,
        }

    # ── IPv6 polling helper ────────────────────────────────────────────

    def poll_bgp_convergence_ipv6(self, target_pfx: int, timeout_sec: int = 180,
                                  poll_interval: int = 2) -> dict:
        """Poll show bgp ipv6 flowspec-vpn summary until PfxRcd reaches target."""
        t0 = time.time()
        last_count = 0
        converged = False
        session_dropped = False
        polls: list[dict] = []

        while time.time() - t0 < timeout_sec:
            try:
                out = self.dut_run("show bgp ipv6 flowspec-vpn summary", timeout=15, retries=1)
                count = parse_flowspec_route_count(out)
                state = parse_bgp_state(out)
                elapsed = round(time.time() - t0, 1)
                polls.append({"t": elapsed, "pfxrcd": count, "state": state})

                if state != "Established":
                    session_dropped = True

                if count != last_count:
                    self.log(f"  IPv6 PfxRcd={count} state={state} t={elapsed}s")
                last_count = count

                if count >= target_pfx:
                    converged = True
                    self.log(f"  IPv6 converged: PfxRcd={count} in {elapsed}s")
                    break
            except Exception as e:
                self.log(f"  IPv6 poll error: {e}")

            time.sleep(poll_interval)

        convergence_sec = round(time.time() - t0, 1)
        return {
            "converged": converged,
            "convergence_sec": convergence_sec,
            "final_pfxrcd": last_count,
            "session_dropped": session_dropped,
            "polls": polls[-10:],
        }

    def check_dp_installed_full(self) -> dict:
        """Read TCAM for both IPv4 and IPv6 installed counts."""
        tcam_out = self.dut_run("show system npu-resources resource-type flowspec", timeout=20)
        tcam = parse_tcam_usage(tcam_out)
        return {
            "ipv4_installed": tcam.get("installed", 0),
            "ipv4_total": tcam.get("total", 0),
            "ipv6_installed": tcam.get("ipv6_installed", 0),
            "ipv6_total": tcam.get("ipv6_total", 0),
        }

    # ── Test 10: Withdraw All at Once ─────────────────────────────────

    def run_test_10(self, test_def: dict) -> dict:
        """Test 10: Withdraw All at Once (20K bulk)."""
        tid = test_def["id"]
        mode = test_def["inject_mode"]
        count = test_def["inject_count"]
        expected_dp = test_def["expected_dp_installed"]

        self.ensure_clean_state("stress")
        self.ensure_clean_state("flowspec-vpn-ipv4")

        self.log(f"  Injecting {count} routes (mode={mode})...")
        ok, inj = self.inject_routes(mode, count, fast=True, timeout=900)
        if not ok:
            return {"id": tid, "name": test_def["name"], "verdict": "FAIL",
                    "reason": f"injection_failed: {inj.get('error', '')[:200]}"}

        conv = self.poll_bgp_convergence(count, timeout_sec=240)
        if not conv["converged"]:
            return {"id": tid, "name": test_def["name"], "verdict": "FAIL",
                    "reason": f"pre_withdraw_not_converged (got {conv['final_pfxrcd']}/{count})"}

        dp_wait = min(30, max(10, count // 1000))
        self.log(f"  Waiting {dp_wait}s for TCAM programming...")
        time.sleep(dp_wait)

        dp_pre = self.check_dp_installed()
        self.log(f"  Pre-withdraw: PfxRcd={conv['final_pfxrcd']} DP={dp_pre['ncp_installed']}")

        self.log("  Withdrawing ALL routes in one shot...")
        t_withdraw = time.time()
        ok_w, res_w = self.withdraw_routes(mode)
        if not ok_w:
            self.log(f"  Withdraw returned error (continuing): {res_w}")

        self.log("  Polling until PfxRcd drops to 0...")
        t0 = time.time()
        pfxrcd_zero = False
        while time.time() - t0 < 120:
            try:
                out = self.dut_run("show bgp ipv4 flowspec-vpn summary", timeout=15, retries=1)
                pfx = parse_flowspec_route_count(out)
                state = parse_bgp_state(out)
                elapsed = round(time.time() - t0, 1)
                self.log(f"  Withdraw poll: PfxRcd={pfx} state={state} t={elapsed}s")
                if pfx == 0 and state == "Established":
                    pfxrcd_zero = True
                    break
            except Exception as e:
                self.log(f"  Poll error: {e}")
            time.sleep(3)

        withdraw_sec = round(time.time() - t_withdraw, 1)

        time.sleep(10)
        dp_post = self.check_dp_installed()
        self.log(f"  Post-withdraw: DP={dp_post['ncp_installed']} TCAM={dp_post['tcam']}")

        try:
            out = self.dut_run("show system version", timeout=15)
            stable = "System" in out
        except Exception:
            stable = False

        verdict = "PASS"
        reasons = []
        if not pfxrcd_zero:
            verdict = "FAIL"
            reasons.append("PfxRcd did not reach 0 within 120s")
        if dp_post["ncp_installed"] > 10:
            verdict = "FAIL"
            reasons.append(f"TCAM not drained: {dp_post['ncp_installed']} still installed")
        if not stable:
            verdict = "FAIL"
            reasons.append("DUT crash/unreachable after bulk withdraw")

        self.log(f"  Verdict: {verdict} (withdraw took {withdraw_sec}s)")

        return {
            "id": tid, "name": test_def["name"], "verdict": verdict,
            "withdraw_sec": withdraw_sec,
            "dp_pre_withdraw": dp_pre["ncp_installed"],
            "dp_post_withdraw": dp_post["ncp_installed"],
            "pfxrcd_zero": pfxrcd_zero,
            "stable": stable,
            "tcam": dp_post["tcam"],
            "reason": "; ".join(reasons) if reasons else None,
        }

    # ── Test 11: Exceed BGP Limit (25K) ───────────────────────────────

    def run_test_11(self, test_def: dict) -> dict:
        """Test 11: Exceed BGP Limit (25K) -- beyond max_rules_total."""
        tid = test_def["id"]
        mode = test_def["inject_mode"]
        count = test_def["inject_count"]
        expected_dp = test_def["expected_dp_installed"]

        self.ensure_clean_state("stress")
        self.ensure_clean_state("flowspec-vpn-ipv4")

        self.log(f"  Injecting {count} routes (mode={mode}) -- exceeding 20K limit...")
        ok, inj = self.inject_routes(mode, count, fast=True, timeout=1200)
        if not ok:
            self.log(f"  Injection returned error (may be expected): {inj}")

        self.log("  Polling BGP convergence (may cap below 25K)...")
        conv = self.poll_bgp_convergence(count, timeout_sec=240)
        final_pfxrcd = conv["final_pfxrcd"]

        dp_wait = min(30, max(10, final_pfxrcd // 1000))
        self.log(f"  Waiting {dp_wait}s for TCAM programming...")
        time.sleep(dp_wait)

        dp = self.check_dp_installed()
        cap_warn = self.check_capacity_warning()
        self.log(f"  BGP accepted: {final_pfxrcd}  DP installed: {dp['ncp_installed']}")
        self.log(f"  Capacity warning: {cap_warn}")

        self.log("  Stability check (15s)...")
        time.sleep(15)
        try:
            out = self.dut_run("show system version", timeout=15)
            stable = "System" in out
        except Exception:
            stable = False

        out = self.dut_run("show bgp ipv4 flowspec-vpn summary", timeout=15)
        post_state = parse_bgp_state(out)
        self.log(f"  Post-test BGP state: {post_state}")

        verdict = "PASS"
        reasons = []
        if not stable:
            verdict = "FAIL"
            reasons.append("DUT crash/unreachable after 25K injection")
        if post_state != "Established":
            verdict = "FAIL"
            reasons.append(f"BGP session dropped to {post_state}")
        if dp["ncp_installed"] > expected_dp + 100:
            verdict = "FAIL"
            reasons.append(f"DP exceeded TCAM cap: {dp['ncp_installed']} > {expected_dp}")

        self.log(f"  Verdict: {verdict}")

        return {
            "id": tid, "name": test_def["name"], "verdict": verdict,
            "bgp_accepted": final_pfxrcd,
            "bgp_tried": count,
            "dp_installed": dp["ncp_installed"],
            "dp_capped": dp["ncp_installed"] <= expected_dp + 100,
            "capacity_warning": cap_warn,
            "session_state": post_state,
            "stable": stable,
            "tcam": dp["tcam"],
            "reason": "; ".join(reasons) if reasons else None,
        }

    # ── Test 02: IPv4 + IPv6 Combined ─────────────────────────────────

    def run_test_02(self, test_def: dict) -> dict:
        """Test 2: IPv4 + IPv6 Combined (12K + 4K)."""
        tid = test_def["id"]
        ipv4_count = test_def.get("ipv4_count", 12000)
        ipv6_count = test_def.get("ipv6_count", 4000)
        expected_ipv4_tcam = test_def["pass_criteria"].get("ipv4_tcam_installed", 12000)
        expected_ipv6_tcam = test_def["pass_criteria"].get("ipv6_tcam_installed", 4000)

        self.ensure_clean_state("stress")
        self.ensure_clean_state("flowspec-vpn-ipv4")
        self.ensure_clean_state("flowspec-vpn-ipv6")

        # Inject IPv6 FIRST to avoid triggering burst bug
        self.log(f"  Injecting {ipv6_count} IPv6 FlowSpec-VPN routes...")
        ok6, inj6 = self.inject_routes("flowspec-vpn-ipv6", ipv6_count, fast=True, timeout=600)
        if not ok6:
            return {"id": tid, "name": test_def["name"], "verdict": "FAIL",
                    "reason": f"ipv6_injection_failed: {inj6.get('error', '')[:200]}"}

        conv6 = self.poll_bgp_convergence_ipv6(ipv6_count, timeout_sec=180)
        self.log(f"  IPv6 BGP: converged={conv6['converged']} PfxRcd={conv6['final_pfxrcd']}")

        dp_wait = min(20, max(5, ipv6_count // 1000))
        self.log(f"  Waiting {dp_wait}s for IPv6 TCAM programming...")
        time.sleep(dp_wait)

        # Inject IPv4
        self.log(f"  Injecting {ipv4_count} IPv4 FlowSpec-VPN routes...")
        ok4, inj4 = self.inject_routes("stress", ipv4_count, fast=True, timeout=900)
        if not ok4:
            return {"id": tid, "name": test_def["name"], "verdict": "FAIL",
                    "reason": f"ipv4_injection_failed: {inj4.get('error', '')[:200]}"}

        conv4 = self.poll_bgp_convergence(ipv4_count, timeout_sec=240)
        self.log(f"  IPv4 BGP: converged={conv4['converged']} PfxRcd={conv4['final_pfxrcd']}")

        dp_wait = min(30, max(10, ipv4_count // 1000))
        self.log(f"  Waiting {dp_wait}s for IPv4 TCAM programming...")
        time.sleep(dp_wait)

        tcam = self.check_dp_installed_full()
        self.log(f"  TCAM: IPv4={tcam['ipv4_installed']}/{tcam['ipv4_total']}  "
                 f"IPv6={tcam['ipv6_installed']}/{tcam['ipv6_total']}")

        try:
            out = self.dut_run("show system version", timeout=15)
            stable = "System" in out
        except Exception:
            stable = False

        verdict = "PASS"
        reasons = []
        if tcam["ipv4_installed"] < expected_ipv4_tcam * 0.9:
            verdict = "FAIL"
            reasons.append(f"IPv4 TCAM: {tcam['ipv4_installed']}/{expected_ipv4_tcam}")
        if tcam["ipv6_installed"] < expected_ipv6_tcam * 0.9:
            verdict = "FAIL"
            reasons.append(f"IPv6 TCAM: {tcam['ipv6_installed']}/{expected_ipv6_tcam}")
        if not conv4["converged"]:
            verdict = "FAIL"
            reasons.append(f"IPv4 not converged: {conv4['final_pfxrcd']}/{ipv4_count}")
        if not conv6["converged"]:
            verdict = "FAIL"
            reasons.append(f"IPv6 not converged: {conv6['final_pfxrcd']}/{ipv6_count}")
        if not stable:
            verdict = "FAIL"
            reasons.append("DUT crash/unreachable")

        self.log(f"  Verdict: {verdict}")

        return {
            "id": tid, "name": test_def["name"], "verdict": verdict,
            "ipv4_pfxrcd": conv4["final_pfxrcd"],
            "ipv6_pfxrcd": conv6["final_pfxrcd"],
            "ipv4_tcam": tcam["ipv4_installed"],
            "ipv6_tcam": tcam["ipv6_installed"],
            "ipv4_convergence_sec": conv4["convergence_sec"],
            "ipv6_convergence_sec": conv6["convergence_sec"],
            "stable": stable,
            "reason": "; ".join(reasons) if reasons else None,
        }

    # ── Dispatch ──────────────────────────────────────────────────────

    TEST_RUNNERS = {
        "test_01": "run_test_01",
        "test_02": "run_test_02",
        "test_03": "run_test_03",
        "test_08": "run_test_08",
        "test_09": "run_test_09",
        "test_10": "run_test_10",
        "test_11": "run_test_11",
        "test_12": "run_test_12",
    }

    def run_single_test(self, test_def: dict) -> dict:
        tid = test_def["id"]
        name = test_def["name"]
        self.log(f"\n{'='*60}")
        self.log(f"=== {tid}: {name} ===")
        self.log(f"{'='*60}")

        if test_def.get("needs_traffic"):
            self.log(f"  SKIP: Test {tid} requires /SPIRENT (agent-driven)")
            return {"id": tid, "name": name, "verdict": "SKIP",
                    "reason": "requires_spirent_traffic (agent-driven)"}

        runner_name = self.TEST_RUNNERS.get(tid)
        if not runner_name:
            self.log(f"  SKIP: No automated runner for {tid}")
            return {"id": tid, "name": name, "verdict": "SKIP",
                    "reason": "no_automated_runner"}

        runner = getattr(self, runner_name)
        try:
            result = runner(test_def)
        except Exception as e:
            self.log(f"  ERROR: {e}")
            result = {"id": tid, "name": name, "verdict": "ERROR", "reason": str(e)}

        # Save per-test JSON
        fname = f"{tid}_{re.sub(r'[^a-z0-9_]', '_', name.lower())[:40]}.json"
        (self.run_dir / fname).write_text(json.dumps(result, indent=2))
        (self.run_dir / "run_log.md").write_text("\n".join(self.log_lines))

        return result

    def run_all_tests(self, test_ids: list[str] | None = None) -> list[dict]:
        tests = self.defs.get("tests", [])
        if test_ids:
            tests = [t for t in tests if t["id"] in test_ids]

        results: list[dict] = []
        for i, t in enumerate(tests):
            if i > 0:
                self.log("Cooldown: withdrawing + 10s settle...")
                mode = tests[i - 1].get("inject_mode", "flowspec-vpn-ipv4")
                self.ensure_clean_state(mode)
                if mode == "stress":
                    self.ensure_clean_state("flowspec-vpn-ipv4")
                if mode == "combined":
                    self.ensure_clean_state("stress")
                    self.ensure_clean_state("flowspec-vpn-ipv4")
                    self.ensure_clean_state("flowspec-vpn-ipv6")
                time.sleep(10)

            r = self.run_single_test(t)
            results.append(r)

        # Final cleanup
        self.log("Final cleanup: withdrawing all routes...")
        self.ensure_clean_state("stress")
        self.ensure_clean_state("flowspec-vpn-ipv4")
        self.ensure_clean_state("flowspec-vpn-ipv6")

        return results

    def generate_report(self, results: list[dict]) -> str:
        lines = [
            "# FlowSpec VPN Scale Test Report (SW-234480)",
            "",
            f"Device: {self.device['hostname']}",
            f"Run: {datetime.now().isoformat()}",
            f"ExaBGP session: {self.session_id}",
            f"RT: {self.default_rt} | RD: {self.default_rd}",
            "",
            "## Results Summary",
            "",
            "| Test | Name | BGP Routes | DP Installed | Convergence | Verdict |",
            "|------|------|-----------|-------------|-------------|---------|",
        ]

        for r in results:
            if r.get("verdict") == "SKIP":
                lines.append(f"| {r['id']} | {r.get('name', '')} | - | - | - | SKIP |")
                continue

            bgp = r.get("final_pfxrcd", r.get("bgp_accepted", "-"))
            dp = r.get("dp_installed", "-")
            conv = r.get("convergence_sec", r.get("recovery_sec", "-"))
            conv_str = f"{conv}s" if isinstance(conv, (int, float)) else str(conv)
            lines.append(f"| {r['id']} | {r.get('name', '')} | {bgp} | {dp} | "
                         f"{conv_str} | {r.get('verdict', '?')} |")

        passed = sum(1 for r in results if r.get("verdict") == "PASS")
        failed = sum(1 for r in results if r.get("verdict") == "FAIL")
        skipped = sum(1 for r in results if r.get("verdict") == "SKIP")
        errors = sum(1 for r in results if r.get("verdict") == "ERROR")
        lines.extend([
            "",
            f"**Result: {passed} PASS / {failed} FAIL / {skipped} SKIP / {errors} ERROR "
            f"(out of {len(results)} tests)**",
            "",
        ])

        # Per-test details
        for r in results:
            if r.get("verdict") in ("SKIP",):
                continue
            lines.append(f"### {r['id']}: {r.get('name', '')}")
            lines.append("")
            lines.append(f"- **Verdict**: {r.get('verdict')}")
            if r.get("reason"):
                lines.append(f"- **Reason**: {r['reason']}")
            if r.get("convergence_sec"):
                lines.append(f"- **Convergence**: {r['convergence_sec']}s")
            if r.get("recovery_sec"):
                lines.append(f"- **Recovery**: {r['recovery_sec']}s")
            if r.get("final_pfxrcd") or r.get("bgp_accepted"):
                lines.append(f"- **BGP PfxRcd**: {r.get('final_pfxrcd', r.get('bgp_accepted'))}")
            if r.get("dp_installed"):
                lines.append(f"- **DP Installed**: {r['dp_installed']}")
            if r.get("tcam"):
                lines.append(f"- **TCAM**: {r['tcam']}")
            if r.get("cycle_results"):
                lines.append(f"- **Churn Cycles**: {len(r['cycle_results']) // 2} completed")
                lines.append(f"- **Session Stable**: {r.get('session_stable')}")
            lines.append("")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="FlowSpec VPN Scale Test Orchestrator (SW-234480)")
    parser.add_argument("--device", default="PE-4", help="DUT hostname (default: PE-4)")
    parser.add_argument("--tests", default=None, help="Comma-separated test IDs (e.g. test_01,test_03)")
    parser.add_argument("--test", default=None, help="Single test ID")
    parser.add_argument("--dry-run", action="store_true", help="Do not inject routes or trigger events")
    parser.add_argument("--session-id", default=None, help="ExaBGP session ID (default: from test_defs)")
    parser.add_argument("--rt", default=None, help="Route-target override")
    args = parser.parse_args()

    acquire_lock()
    import atexit
    atexit.register(release_lock)

    test_ids = None
    if args.test:
        test_ids = [args.test]
    elif args.tests:
        test_ids = [t.strip() for t in args.tests.split(",")]

    run_dir = RESULTS_DIR / f"SW-234480_{datetime.now().strftime('%Y%m%d_%H%M')}"
    run_dir.mkdir(parents=True, exist_ok=True)

    orch = FlowSpecScaleTest(args.device, run_dir, dry_run=args.dry_run)
    if args.session_id:
        orch.session_id = args.session_id
    if args.rt:
        orch.default_rt = args.rt
    orch.log(f"Starting FlowSpec Scale tests on {args.device}")
    orch.log(f"Session: {orch.session_id} | RT: {orch.default_rt} | RD: {orch.default_rd}")
    orch.log(f"Results: {run_dir}")

    if not orch.preflight():
        orch.log("Pre-flight checks failed. Exiting.")
        (run_dir / "run_log.md").write_text("\n".join(orch.log_lines))
        sys.exit(1)

    results = []
    try:
        results = orch.run_all_tests(test_ids)
    except KeyboardInterrupt:
        orch.log("Interrupted by user")
    except Exception as e:
        orch.log(f"FATAL: {e}")
        import traceback
        orch.log(traceback.format_exc())
    finally:
        report = orch.generate_report(results)
        (run_dir / "SUMMARY.md").write_text(report)
        (run_dir / "run_log.md").write_text("\n".join(orch.log_lines))
        orch.log(f"Done. Report: {run_dir / 'SUMMARY.md'}")
        print("\n" + report)


if __name__ == "__main__":
    main()
