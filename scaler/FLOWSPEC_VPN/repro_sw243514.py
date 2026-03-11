#!/usr/bin/env python3
"""
Reproduction script for SW-243514: IPv4 FlowSpec-VPN routes not imported into VRF.

Sequence:
  1. Enable debug bgp import on RR-SA-2
  2. Withdraw current 12K SAFI 134 (FlowSpec-VPN) routes
  3. Inject 12K SAFI 133 (plain FlowSpec) routes -- same prefixes, no RD/RT
  4. Withdraw SAFI 133
  5. Re-inject 12K SAFI 134 with RD 1.1.1.1:200, RT 300:300
  6. Check if VRF ZULU imports (collect debug bgp import traces)
  7. Disable debug bgp import

Theory: SAFI 133 processing may corrupt bgpd's internal RT import table,
causing subsequent SAFI 134 import to silently skip RT lookup.
"""

import sys
import time
import argparse
import subprocess

sys.path.insert(0, "/home/dn/SCALER/FLOWSPEC_VPN/exabgp")
from builders.scale import (
    build_flowspec_ipv4,
    build_flowspec_vpn_ipv4,
    inject_batch_fast,
    withdraw_all,
)

PIPE_IN = "/run/exabgp/exabgp.in"
RR_SA2_IP = "100.64.4.205"
RR_SA2_USER = "dnroot"
RR_SA2_PASS = "dnroot"


def ssh_cmd(ip, user, password, commands, timeout=30):
    """Run commands on DNOS device via SSH."""
    import paramiko
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password, timeout=10)
    
    shell = client.invoke_shell(width=200, height=50)
    time.sleep(1)
    shell.recv(65535)
    
    outputs = []
    for cmd in commands:
        shell.send(cmd + "\n")
        time.sleep(1.5 if "commit" in cmd else 0.8)
        out = shell.recv(65535).decode("utf-8", errors="replace")
        outputs.append(out)
        print(f"  > {cmd}")
    
    shell.close()
    client.close()
    return outputs


def enable_debug_import(ip=RR_SA2_IP):
    """Enable debug bgp import on RR-SA-2."""
    print("\n=== Step 1: Enable debug bgp import on RR-SA-2 ===")
    commands = [
        "configure",
        "debug",
        "bgp import",
        "!",
        "commit",
        "exit",
        "exit",
    ]
    outputs = ssh_cmd(ip, RR_SA2_USER, RR_SA2_PASS, commands)
    print("  [OK] debug bgp import enabled")
    return outputs


def disable_debug_import(ip=RR_SA2_IP):
    """Disable debug bgp import on RR-SA-2."""
    print("\n=== Step 8: Disable debug bgp import on RR-SA-2 ===")
    commands = [
        "configure",
        "debug",
        "no bgp import",
        "!",
        "commit",
        "exit",
        "exit",
    ]
    outputs = ssh_cmd(ip, RR_SA2_USER, RR_SA2_PASS, commands)
    print("  [OK] debug bgp import disabled")
    return outputs


def show_cmd(device_name, command):
    """Run show command via MCP tool (subprocess call to avoid MCP dep)."""
    print(f"  > {command}")


def wait_and_verify(description, seconds=10):
    """Wait for convergence."""
    print(f"  Waiting {seconds}s for {description}...")
    time.sleep(seconds)


def main():
    parser = argparse.ArgumentParser(description="Reproduce SW-243514")
    parser.add_argument("--count", type=int, default=12000, help="Number of routes (default: 12000)")
    parser.add_argument("--skip-debug", action="store_true", help="Skip enabling/disabling debug bgp import")
    parser.add_argument("--step", type=int, help="Run only a specific step (1-8)")
    parser.add_argument("--dry-run", action="store_true", help="Print routes without injecting")
    args = parser.parse_args()

    count = args.count
    rd = "1.1.1.1:200"
    rt = "300:300"

    print(f"SW-243514 Reproduction Script")
    print(f"  Routes: {count}")
    print(f"  RD: {rd}, RT: {rt}")
    print(f"  Target: RR-SA-2 ({RR_SA2_IP})")
    print()

    # Build route sets
    print("Building route sets...")
    safi133_routes = build_flowspec_ipv4(count=count, action="rate-limit 0")
    safi134_routes = build_flowspec_vpn_ipv4(count=count, rd=rd, rt=rt, action="rate-limit 0")
    print(f"  SAFI 133 sample: {safi133_routes[0]}")
    print(f"  SAFI 134 sample: {safi134_routes[0]}")

    if args.dry_run:
        print("\n[DRY RUN] Would inject/withdraw these routes. Exiting.")
        return

    # Step 1: Enable debug
    if not args.skip_debug:
        if not args.step or args.step == 1:
            enable_debug_import()

    # Step 2: Withdraw current SAFI 134 routes
    if not args.step or args.step == 2:
        print(f"\n=== Step 2: Withdraw current {count} SAFI 134 routes ===")
        result = withdraw_all(safi134_routes, batch_size=200, inter_batch_delay=0.05)
        print(f"  Withdrawn: {result['injected']}/{result['total']} in {result['elapsed_sec']}s")
        wait_and_verify("SAFI 134 withdrawal convergence", 15)

    # Step 3: Inject SAFI 133 routes
    if not args.step or args.step == 3:
        print(f"\n=== Step 3: Inject {count} SAFI 133 (plain FlowSpec) routes ===")
        result = inject_batch_fast(safi133_routes, batch_size=200, inter_batch_delay=0.05)
        print(f"  Injected: {result['injected']}/{result['total']} in {result['elapsed_sec']}s ({result['routes_per_sec']} rps)")
        wait_and_verify("SAFI 133 injection convergence", 20)
        print("  >>> CHECK: show bgp ipv4 flowspec summary on RR-SA-2 -- should show PfxAccepted > 0")

    # Step 4: Withdraw SAFI 133 routes
    if not args.step or args.step == 4:
        print(f"\n=== Step 4: Withdraw {count} SAFI 133 routes ===")
        result = withdraw_all(safi133_routes, batch_size=200, inter_batch_delay=0.05)
        print(f"  Withdrawn: {result['injected']}/{result['total']} in {result['elapsed_sec']}s")
        wait_and_verify("SAFI 133 withdrawal convergence", 15)
        print("  >>> CHECK: show bgp ipv4 flowspec summary on RR-SA-2 -- should show PfxAccepted = 0")

    # Step 5: Re-inject SAFI 134 routes
    if not args.step or args.step == 5:
        print(f"\n=== Step 5: Re-inject {count} SAFI 134 (FlowSpec-VPN) with RD={rd} RT={rt} ===")
        result = inject_batch_fast(safi134_routes, batch_size=200, inter_batch_delay=0.05)
        print(f"  Injected: {result['injected']}/{result['total']} in {result['elapsed_sec']}s ({result['routes_per_sec']} rps)")
        wait_and_verify("SAFI 134 injection + VRF import convergence", 30)

    # Step 6: Check results
    if not args.step or args.step == 6:
        print(f"\n=== Step 6: Verification (run these on RR-SA-2) ===")
        print("  1. show bgp ipv4 flowspec-vpn summary")
        print("     Expected: PfxAccepted = 12000 from 1.1.1.1")
        print("  2. show system npu-resources resource-type flowspec")
        print("     If bug repro'd: IPv4 Received = 0, Installed = 0")
        print("     If bug NOT repro'd: IPv4 Received > 0, Installed > 0")
        print("  3. show dnos-internal routing rib-manager database flowspec")
        print("     If bug repro'd: IPv4 table size = 0")
        print("     If bug NOT repro'd: IPv4 table size > 0")
        print("  4. show file traces routing_engine/bgpd_traces | include rt_node | tail 20")
        print("     If bug repro'd: NO 'Found rt_node' lines for IPv4")
        print("     If bug NOT repro'd: 'Found rt_node' lines present")

    # Step 7: Collect traces
    if not args.step or args.step == 7:
        print(f"\n=== Step 7: Collect debug bgp import traces ===")
        print("  show file traces routing_engine/bgpd_traces | include import | tail 50")
        print("  show file traces routing_engine/bgpd_traces | include rt_node | tail 50")
        print("  show file traces routing_engine/bgpd_traces | include bgp_service | tail 50")

    # Step 8: Disable debug
    if not args.skip_debug:
        if not args.step or args.step == 8:
            disable_debug_import()

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
