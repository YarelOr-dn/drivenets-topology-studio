#!/usr/bin/env python3
"""
SW-243514 Reproduction v2: IPv4+IPv6 SAFI 133 → SAFI 134 transition.

Sequence:
  1. Enable debug bgp import on RR-SA-2
  2. Withdraw ALL current routes
  3. Inject 12K IPv4 SAFI 133 + 4K IPv6 SAFI 133
  4. Verify all installed on RR-SA-2
  5. Withdraw all 16K SAFI 133 routes
  6. Re-inject as SAFI 134 (FlowSpec-VPN) with DIFFERENT IP ranges
     IPv4: 172.16.0.0/24 base, IPv6: 2001:db9::/48 base
     RD 1.1.1.1:200, RT 300:300 (VRF ZULU)
  7. Verify import into VRF ZULU + collect traces
  8. Disable debug bgp import

Theory: mixing IPv4+IPv6 SAFI 133 then switching to SAFI 134 may
corrupt bgpd's internal RT import table for IPv4 FlowSpec-VPN.
"""

import sys
import time
import argparse

sys.path.insert(0, "/home/dn/SCALER/FLOWSPEC_VPN/exabgp")
from builders.scale import (
    build_flowspec_ipv4,
    build_flowspec_ipv6,
    build_flowspec_vpn_ipv4,
    build_flowspec_vpn_ipv6,
    inject_batch_fast,
    withdraw_all,
)

PIPE_IN = "/run/exabgp/exabgp.in"
RR_SA2_IP = "100.64.4.205"
SSH_USER = "dnroot"
SSH_PASS = "dnroot"

IPV4_COUNT = 12000
IPV6_COUNT = 4000

SAFI133_IPV4_BASE = "10.0.0.0"
SAFI133_IPV6_BASE = "2001:db8::"

SAFI134_IPV4_BASE = "172.16.0.0"
SAFI134_IPV6_BASE = "2001:db9::"

RD = "1.1.1.1:200"
RT = "300:300"


def ssh_cmd(ip, commands, timeout=30):
    """Run commands on DNOS device via SSH."""
    import paramiko
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=SSH_USER, password=SSH_PASS, timeout=10)

    shell = client.invoke_shell(width=200, height=50)
    time.sleep(1)
    shell.recv(65535)

    outputs = []
    for cmd in commands:
        shell.send(cmd + "\n")
        time.sleep(2.0 if "commit" in cmd else 0.8)
        out = shell.recv(65535).decode("utf-8", errors="replace")
        outputs.append(out)
        print(f"  > {cmd}")

    shell.close()
    client.close()
    return outputs


def ssh_show(ip, command, wait=3):
    """Run a single show command and return output."""
    import paramiko
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=SSH_USER, password=SSH_PASS, timeout=10)

    shell = client.invoke_shell(width=200, height=50)
    time.sleep(1)
    shell.recv(65535)

    shell.send(command + " | no-more\n")
    time.sleep(wait)
    out = shell.recv(65535 * 4).decode("utf-8", errors="replace")

    shell.close()
    client.close()
    return out


def enable_debug_import():
    print("\n=== Step 1: Enable debug bgp import on RR-SA-2 ===")
    ssh_cmd(RR_SA2_IP, [
        "configure", "debug", "bgp import", "!", "commit", "exit", "exit",
    ])
    print("  [OK] debug bgp import enabled")


def disable_debug_import():
    print("\n=== Step 8: Disable debug bgp import on RR-SA-2 ===")
    ssh_cmd(RR_SA2_IP, [
        "configure", "debug", "no bgp import", "!", "commit", "exit", "exit",
    ])
    print("  [OK] debug bgp import disabled")


def verify_npu(label=""):
    """Check NPU FlowSpec resources on RR-SA-2."""
    print(f"\n  --- NPU check{' (' + label + ')' if label else ''} ---")
    out = ssh_show(RR_SA2_IP, "show system npu-resources resource-type flowspec")
    for line in out.split("\n"):
        if "0" in line and "|" in line and "NCP" not in line:
            print(f"  {line.strip()}")
    return out


def verify_bgp_summary(afi_safi):
    """Check BGP summary for a given AFI/SAFI."""
    cmd = f"show bgp {afi_safi} summary"
    print(f"\n  --- {cmd} ---")
    out = ssh_show(RR_SA2_IP, cmd)
    for line in out.split("\n"):
        stripped = line.strip()
        if stripped and ("1.1.1.1" in stripped or "Neighbor" in stripped or "Total" in stripped):
            print(f"  {stripped}")
    return out


def collect_traces():
    """Collect debug bgp import traces from RR-SA-2."""
    print("\n=== Step 7: Collecting debug bgp import traces ===")
    traces = {}
    for keyword in ["rt_node", "Import", "bgp_service_import"]:
        cmd = f"show file traces routing_engine/bgpd_traces | include {keyword} | tail 20"
        print(f"\n  --- {keyword} traces ---")
        out = ssh_show(RR_SA2_IP, cmd, wait=5)
        traces[keyword] = out
        for line in out.split("\n"):
            stripped = line.strip()
            if stripped and keyword.lower() in stripped.lower():
                print(f"  {stripped}")
    return traces


def main():
    parser = argparse.ArgumentParser(description="SW-243514 Repro v2: IPv4+IPv6 SAFI 133→134")
    parser.add_argument("--skip-debug", action="store_true")
    parser.add_argument("--step", type=int, help="Run only a specific step (1-8)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("SW-243514 Reproduction v2")
    print(f"  IPv4: {IPV4_COUNT} routes | IPv6: {IPV6_COUNT} routes")
    print(f"  SAFI 133 ranges: {SAFI133_IPV4_BASE}/24, {SAFI133_IPV6_BASE}/48")
    print(f"  SAFI 134 ranges: {SAFI134_IPV4_BASE}/24, {SAFI134_IPV6_BASE}/48")
    print(f"  RD: {RD}, RT: {RT} (VRF ZULU)")
    print(f"  Target: RR-SA-2 ({RR_SA2_IP})")
    print()

    # --- Build all route sets ---
    print("Building route sets...")

    old_vpn_ipv4 = build_flowspec_vpn_ipv4(
        count=IPV4_COUNT, base_prefix=SAFI133_IPV4_BASE, rd=RD, rt=RT)
    old_test_route = [
        "announce flow route rd 1.1.1.1:200 destination 99.99.1.0/24 "
        "rate-limit 0 extended-community [ target:1234567:301 ]"
    ]

    safi133_ipv4 = build_flowspec_ipv4(
        count=IPV4_COUNT, base_prefix=SAFI133_IPV4_BASE, action="rate-limit 0")
    safi133_ipv6 = build_flowspec_ipv6(
        count=IPV6_COUNT, base_prefix=SAFI133_IPV6_BASE, action="rate-limit 0")

    safi134_ipv4 = build_flowspec_vpn_ipv4(
        count=IPV4_COUNT, base_prefix=SAFI134_IPV4_BASE, rd=RD, rt=RT, action="rate-limit 0")
    safi134_ipv6 = build_flowspec_vpn_ipv6(
        count=IPV6_COUNT, base_prefix=SAFI134_IPV6_BASE, rd=RD, rt=RT, action="rate-limit 0")

    print(f"  SAFI 133 IPv4 sample: {safi133_ipv4[0]}")
    print(f"  SAFI 133 IPv6 sample: {safi133_ipv6[0]}")
    print(f"  SAFI 134 IPv4 sample: {safi134_ipv4[0]}")
    print(f"  SAFI 134 IPv6 sample: {safi134_ipv6[0]}")
    print(f"  Total SAFI 133: {len(safi133_ipv4) + len(safi133_ipv6)}")
    print(f"  Total SAFI 134: {len(safi134_ipv4) + len(safi134_ipv6)}")

    if args.dry_run:
        print("\n[DRY RUN] Exiting.")
        return

    run_step = args.step

    # === Step 1: Enable debug ===
    if not args.skip_debug and (not run_step or run_step == 1):
        enable_debug_import()

    # === Step 2: Withdraw all current routes ===
    if not run_step or run_step == 2:
        print(f"\n=== Step 2: Withdraw ALL current routes ===")
        print(f"  Withdrawing {len(old_vpn_ipv4)} old SAFI 134 IPv4 routes...")
        r1 = withdraw_all(old_vpn_ipv4, batch_size=200, inter_batch_delay=0.05)
        print(f"  Done: {r1['injected']}/{r1['total']} in {r1['elapsed_sec']}s")

        print(f"  Withdrawing 1 old test route...")
        r2 = withdraw_all(old_test_route)
        print(f"  Done: {r2['injected']}/{r2['total']}")

        print("  Waiting 20s for withdrawal convergence...")
        time.sleep(20)
        verify_npu("after withdraw")

    # === Step 3: Inject SAFI 133 (IPv4 + IPv6) ===
    if not run_step or run_step == 3:
        print(f"\n=== Step 3: Inject {IPV4_COUNT} IPv4 + {IPV6_COUNT} IPv6 SAFI 133 ===")

        print(f"  Injecting {IPV4_COUNT} IPv4 FlowSpec SAFI 133...")
        r1 = inject_batch_fast(safi133_ipv4, batch_size=200, inter_batch_delay=0.05)
        print(f"  IPv4: {r1['injected']}/{r1['total']} in {r1['elapsed_sec']}s ({r1['routes_per_sec']} rps)")

        print(f"  Injecting {IPV6_COUNT} IPv6 FlowSpec SAFI 133...")
        r2 = inject_batch_fast(safi133_ipv6, batch_size=200, inter_batch_delay=0.05)
        print(f"  IPv6: {r2['injected']}/{r2['total']} in {r2['elapsed_sec']}s ({r2['routes_per_sec']} rps)")

        print("  Waiting 30s for SAFI 133 convergence...")
        time.sleep(30)

    # === Step 4: Verify SAFI 133 installed ===
    if not run_step or run_step == 4:
        print(f"\n=== Step 4: Verify SAFI 133 installed ===")
        verify_npu("SAFI 133 installed")
        verify_bgp_summary("ipv4 flowspec")
        verify_bgp_summary("ipv6 flowspec")

    # === Step 5: Withdraw all SAFI 133 ===
    if not run_step or run_step == 5:
        print(f"\n=== Step 5: Withdraw all SAFI 133 routes ===")

        print(f"  Withdrawing {IPV4_COUNT} IPv4 SAFI 133...")
        r1 = withdraw_all(safi133_ipv4, batch_size=200, inter_batch_delay=0.05)
        print(f"  IPv4: {r1['injected']}/{r1['total']} in {r1['elapsed_sec']}s")

        print(f"  Withdrawing {IPV6_COUNT} IPv6 SAFI 133...")
        r2 = withdraw_all(safi133_ipv6, batch_size=200, inter_batch_delay=0.05)
        print(f"  IPv6: {r2['injected']}/{r2['total']} in {r2['elapsed_sec']}s")

        print("  Waiting 20s for withdrawal convergence...")
        time.sleep(20)
        verify_npu("after SAFI 133 withdraw")

    # === Step 6: Re-inject as SAFI 134 (different IP ranges) ===
    if not run_step or run_step == 6:
        print(f"\n=== Step 6: Inject SAFI 134 (FlowSpec-VPN) with different IP ranges ===")
        print(f"  IPv4: {SAFI134_IPV4_BASE}/24, IPv6: {SAFI134_IPV6_BASE}/48")
        print(f"  RD: {RD}, RT: {RT}")

        print(f"\n  Injecting {IPV4_COUNT} IPv4 FlowSpec-VPN SAFI 134...")
        r1 = inject_batch_fast(safi134_ipv4, batch_size=200, inter_batch_delay=0.05)
        print(f"  IPv4: {r1['injected']}/{r1['total']} in {r1['elapsed_sec']}s ({r1['routes_per_sec']} rps)")

        print(f"  Injecting {IPV6_COUNT} IPv6 FlowSpec-VPN SAFI 134...")
        r2 = inject_batch_fast(safi134_ipv6, batch_size=200, inter_batch_delay=0.05)
        print(f"  IPv6: {r2['injected']}/{r2['total']} in {r2['elapsed_sec']}s ({r2['routes_per_sec']} rps)")

        print("  Waiting 45s for SAFI 134 injection + VRF import convergence...")
        time.sleep(45)

        print("\n  --- Verification ---")
        verify_npu("SAFI 134 installed")
        verify_bgp_summary("ipv4 flowspec-vpn")
        verify_bgp_summary("ipv6 flowspec-vpn")

    # === Step 7: Collect traces ===
    if not run_step or run_step == 7:
        collect_traces()

    # === Step 8: Disable debug ===
    if not args.skip_debug and (not run_step or run_step == 8):
        disable_debug_import()

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
