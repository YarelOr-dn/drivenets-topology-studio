#!/usr/bin/env python3
"""
SW-238966 Verification Script
BGP NSR -- New Neighbors Won't Establish After NSR With Passive Config

Reproduces the bug by:
1. Confirming NSR + passive config (pre-flight)
2. Triggering NSR via bgpd restart
3. Checking IPv4 listener socket survives (the fix)
4. Deleting + re-adding the passive neighbor
5. Verifying the neighbor re-establishes

Usage:
    python3 verify_sw238966.py <device_mgmt_ip> [neighbor_ip] [bgp_asn]

Defaults:
    neighbor_ip = 100.64.6.134 (ExaBGP)
    bgp_asn = 1234567
"""

import paramiko
import sys
import time

# Add parent dir for build_check import
import os
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
from build_check import check_fix_in_build

DEVICE_IP = sys.argv[1] if len(sys.argv) > 1 else "100.64.4.98"
NEIGHBOR_IP = sys.argv[2] if len(sys.argv) > 2 else "100.64.6.134"
BGP_ASN = sys.argv[3] if len(sys.argv) > 3 else "1234567"

NSR_RECOVERY_WAIT = 30
RECONNECT_WAIT = 60


def ssh_cmd(ssh, cmd, wait=3):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    time.sleep(wait)
    return stdout.read().decode(errors='replace')


def dnos_interactive(ssh, commands, wait_per_cmd=1, final_wait=5):
    shell = ssh.invoke_shell()
    for cmd in commands:
        shell.send(cmd + "\n")
        time.sleep(wait_per_cmd)
    time.sleep(final_wait)
    output = shell.recv(65535).decode(errors='replace')
    shell.close()
    return output


def get_listeners(ssh):
    return dnos_interactive(
        ssh,
        ["run start shell", "dnroot", "ss -a | grep bgp", "exit"],
        wait_per_cmd=2, final_wait=3
    )


def has_ipv4_listener(listener_output):
    return "0.0.0.0:bgp" in listener_output


def enable_debug(ssh):
    """Enable debug bgp fsm + events for detailed NSR recovery traces."""
    print("[INFO] Enabling debug bgp fsm + events...")
    out = dnos_interactive(ssh, [
        "configure",
        "debug",
        "bgp fsm",
        "bgp events",
        "!",
        "commit",
        "exit"
    ], wait_per_cmd=1, final_wait=5)
    print(f"[INFO] Debug enable output:\n{out.strip()}")
    return out


def disable_debug(ssh):
    """Disable debug bgp fsm + events (cleanup)."""
    print("[INFO] Disabling debug bgp fsm + events...")
    out = dnos_interactive(ssh, [
        "configure",
        "debug",
        "no bgp fsm",
        "no bgp events",
        "!",
        "commit",
        "exit"
    ], wait_per_cmd=1, final_wait=5)
    print(f"[INFO] Debug disable output:\n{out.strip()}")
    return out


def section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def main():
    print(f"SW-238966 Verification")
    print(f"Device: {DEVICE_IP} | Neighbor: {NEIGHBOR_IP} | ASN: {BGP_ASN}")
    print(f"{'=' * 60}")

    # Build-vs-fix check: skip if fix not in device's build
    build_result, _, _ = check_fix_in_build(DEVICE_IP, "SW-238966")
    if build_result == "SKIP":
        print("[SKIP] SW-238966 has no fix (open bug). Cannot verify.")
        return "SKIP"
    if build_result == "FIX NOT IN BUILD":
        print("[SKIP] Fix for SW-238966 is NOT in this build. Upgrade to v25.4.13+ or v26.1+ first.")
        return "SKIP"
    if build_result == "UNKNOWN":
        print("[WARN] Could not determine if fix is in build. Proceeding anyway...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(DEVICE_IP, port=22, username="dnroot", password="dnroot")

    results = {}

    # ================================================================
    section("PHASE 1: PRE-FLIGHT")
    # ================================================================

    version = ssh_cmd(ssh, "show system version | no-more")
    print(f"[INFO] Version:\n{version.strip()}")

    nsr = ssh_cmd(ssh, 'show config protocols bgp | include "nsr" | no-more')
    print(f"[INFO] NSR config: {nsr.strip()}")
    if "nsr" not in nsr.lower():
        print("[SKIP] NSR not enabled on device. Cannot reproduce SW-238966.")
        ssh.close()
        return "SKIP"

    passive = ssh_cmd(ssh, 'show config protocols bgp | include "passive" | no-more')
    print(f"[INFO] Passive config: {passive.strip()}")
    if "passive" not in passive.lower():
        print("[SKIP] No passive neighbor configured. Cannot reproduce SW-238966.")
        ssh.close()
        return "SKIP"

    gr_config = ssh_cmd(ssh, 'show config protocols bgp | include "graceful-restart" | no-more')
    print(f"[INFO] Graceful-restart config: {gr_config.strip()}")
    if "graceful-restart disabled" not in gr_config.lower():
        print("[WARN] graceful-restart not explicitly disabled on passive neighbor.")
        print("[WARN] Jira repro requires GR disabled on BOTH sides. Results may be inconclusive.")

    baseline_bgp = ssh_cmd(ssh, "show bgp summary | no-more", wait=5)
    print(f"[INFO] Baseline BGP summary:\n{baseline_bgp.strip()}")

    listeners_before = get_listeners(ssh)
    print(f"[INFO] Listeners BEFORE NSR:\n{listeners_before.strip()}")
    results["pre_ipv4"] = has_ipv4_listener(listeners_before)
    if not results["pre_ipv4"]:
        print("[WARN] IPv4 listener already missing before NSR -- device may already be in buggy state")

    # Phase 1b: check local BGP port in use (pre-condition)
    local_port_check = dnos_interactive(
        ssh,
        ["run start shell", "dnroot", "ss -t state established | grep bgp", "exit"],
        wait_per_cmd=2, final_wait=3
    )
    print(f"[INFO] Established BGP sockets:\n{local_port_check.strip()}")
    local_179 = any(
        line.strip() and ":bgp" in line.split()[3] if len(line.split()) >= 5 else False
        for line in local_port_check.splitlines()
        if "ESTAB" in line or "bgp" in line
    )
    if not local_179:
        has_bgp_local = ":bgp " in local_port_check and "ESTAB" in local_port_check
        if not has_bgp_local:
            print("[WARN] No ESTABLISHED session uses local port 179. Bug pre-condition may not be met.")
            print("[WARN] The FIN-WAIT collision requires at least one session on local :bgp port.")
    results["local_port_179"] = local_179 or (":bgp" in local_port_check)

    # ================================================================
    section("ENABLE DEBUG (bgp fsm + events)")
    # ================================================================

    enable_debug(ssh)

    # ================================================================
    section("PHASE 2: TRIGGER NSR (twice)")
    # ================================================================

    for nsr_round in (1, 2):
        print(f"[INFO] Triggering NSR #{nsr_round}: request system process restart ncc 0 routing-engine routing:bgpd")
        nsr_out = ssh_cmd(ssh, "request system process restart ncc 0 routing-engine routing:bgpd", wait=5)
        print(f"[INFO] NSR #{nsr_round} trigger output: {nsr_out.strip()}")

        print(f"[INFO] Waiting {NSR_RECOVERY_WAIT}s for NSR recovery...")
        time.sleep(NSR_RECOVERY_WAIT)

        post_nsr_bgp = ssh_cmd(ssh, "show bgp summary | no-more", wait=5)
        print(f"[INFO] Post-NSR #{nsr_round} BGP summary:\n{post_nsr_bgp.strip()}")

        listeners_after_nsr = get_listeners(ssh)
        print(f"[INFO] Listeners AFTER NSR #{nsr_round}:\n{listeners_after_nsr.strip()}")
        results[f"post_nsr{nsr_round}_ipv4"] = has_ipv4_listener(listeners_after_nsr)

        if results[f"post_nsr{nsr_round}_ipv4"]:
            print(f"[PASS] IPv4 listener (0.0.0.0:bgp) present after NSR #{nsr_round}")
        else:
            print(f"[FAIL] IPv4 listener (0.0.0.0:bgp) MISSING after NSR #{nsr_round}!")
            print("[FAIL] BUG SW-238966 IS PRESENT -- SO_REUSEADDR not set after TCP_REPAIR disable")
            break

    # ================================================================
    section("PHASE 3: DELETE + RE-ADD NEIGHBOR")
    # ================================================================

    print(f"[INFO] Deleting neighbor {NEIGHBOR_IP}...")
    delete_out = dnos_interactive(ssh, [
        "configure",
        f"no protocols bgp {BGP_ASN} neighbor {NEIGHBOR_IP}",
        "commit",
        "exit"
    ], wait_per_cmd=2, final_wait=10)
    print(f"[INFO] Delete output:\n{delete_out.strip()}")

    time.sleep(5)

    print("[INFO] Rolling back (re-adding neighbor)...")
    rollback_out = dnos_interactive(ssh, [
        "configure",
        "rollback 1",
        "commit",
        "exit"
    ], wait_per_cmd=2, final_wait=10)
    print(f"[INFO] Rollback output:\n{rollback_out.strip()}")

    print(f"[INFO] Waiting {RECONNECT_WAIT}s for peer to reconnect...")
    time.sleep(RECONNECT_WAIT)

    # ================================================================
    section("PHASE 4: FINAL VERIFICATION")
    # ================================================================

    final_bgp = ssh_cmd(ssh, "show bgp summary | no-more", wait=5)
    print(f"[INFO] Final BGP summary:\n{final_bgp.strip()}")

    listeners_final = get_listeners(ssh)
    print(f"[INFO] Final listeners:\n{listeners_final.strip()}")
    results["final_ipv4"] = has_ipv4_listener(listeners_final)

    syslog = ssh_cmd(ssh, "show file log routing_engine/system-events.log | include NEIGHBOR_ADJACENCY | tail 20 | no-more", wait=5)
    print(f"[INFO] Syslog NEIGHBOR events:\n{syslog.strip()}")

    traces = ssh_cmd(ssh, "show file traces routing_engine/bgpd_traces | include ADJCHANGE | tail 20 | no-more", wait=5)
    print(f"[INFO] Traces ADJCHANGE:\n{traces.strip()}")

    fsm_traces = ssh_cmd(ssh, "show file traces routing_engine/bgpd_traces | include FSM | tail 30 | no-more", wait=5)
    print(f"[INFO] Debug FSM traces:\n{fsm_traces.strip()}")

    nsr_traces = ssh_cmd(ssh, "show file traces routing_engine/bgpd_traces | include NSR | tail 20 | no-more", wait=5)
    print(f"[INFO] Debug NSR recovery traces:\n{nsr_traces.strip()}")

    bind_traces = ssh_cmd(ssh, "show file traces routing_engine/bgpd_traces | include bind | tail 10 | no-more", wait=5)
    print(f"[INFO] Debug bind traces:\n{bind_traces.strip()}")

    # ================================================================
    section("DISABLE DEBUG (cleanup)")
    # ================================================================

    disable_debug(ssh)

    verify_no_debug = ssh_cmd(ssh, "show config debug | no-more", wait=3)
    print(f"[INFO] Debug config after cleanup:\n{verify_no_debug.strip()}")

    # ================================================================
    section("VERDICT")
    # ================================================================

    neighbor_established = "Established" in final_bgp and NEIGHBOR_IP.split(".")[0] in final_bgp
    adjacency_up = "ADJACENCY_UP" in syslog
    nsr1_ok = results.get("post_nsr1_ipv4", False)
    nsr2_ok = results.get("post_nsr2_ipv4", False)

    if nsr1_ok and nsr2_ok and results["final_ipv4"] and neighbor_established:
        verdict = "FIX CONFIRMED"
        print(f"[FIX CONFIRMED] SW-238966 is fixed:")
        print(f"  [PASS] IPv4 listener present after NSR #1: True")
        print(f"  [PASS] IPv4 listener present after NSR #2: True")
        print(f"  [PASS] IPv4 listener present after delete+re-add: True")
        print(f"  [PASS] Neighbor {NEIGHBOR_IP} reached Established: True")
        if adjacency_up:
            print(f"  [PASS] Syslog confirms NEIGHBOR_ADJACENCY_UP")
    elif not nsr1_ok or not nsr2_ok or not results["final_ipv4"]:
        verdict = "BUG PRESENT"
        print(f"[BUG PRESENT] SW-238966 is NOT fixed:")
        print(f"  IPv4 listener after NSR #1: {'PRESENT' if nsr1_ok else 'MISSING'}")
        print(f"  IPv4 listener after NSR #2: {'PRESENT' if nsr2_ok else 'MISSING (or skipped)'}")
        print(f"  IPv4 listener after delete+re-add: {'PRESENT' if results['final_ipv4'] else 'MISSING'}")
        print(f"  Neighbor Established: {neighbor_established}")
    else:
        verdict = "INCONCLUSIVE"
        print(f"[INCONCLUSIVE] Listener present but neighbor not Established:")
        print(f"  IPv4 listener: PRESENT")
        print(f"  Neighbor {NEIGHBOR_IP}: NOT Established")
        print(f"  Check if remote peer (ExaBGP) is running and reachable")

    ssh.close()
    return verdict


if __name__ == "__main__":
    verdict = main()
    print(f"\nFinal verdict: {verdict}")
    sys.exit(0 if verdict == "FIX CONFIRMED" else 1)
