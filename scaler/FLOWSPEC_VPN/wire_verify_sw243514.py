#!/usr/bin/env python3
"""
Wire-level verification for SW-243514: Do IPv4 FlowSpec-VPN routes carry Extended Communities?

Uses parallel CP captures on PE-1 + RR-SA-2 while withdrawing/re-injecting
a small sample of routes. Also enables debug bgp updates-in on RR-SA-2 to
get parsed UPDATE content in traces.

Output:
  1. CP capture hex dump (verbose) showing BGP UPDATE wire content
  2. debug bgp updates-in traces showing parsed attributes
  3. debug bgp import traces showing RT lookup result
"""

import sys
import time
import threading

sys.path.insert(0, "/home/dn/SCALER/FLOWSPEC_VPN/exabgp")

import paramiko
from pathlib import Path
from builders.scale import build_flowspec_vpn_ipv4, inject_batch_fast, withdraw_all

RR_SA2_IP = "100.64.4.205"
PE1_IP = "100.64.1.35"
SSH_USER = "dnroot"
SSH_PASS = "dnroot"

SAMPLE_COUNT = 5
RD = "1.1.1.1:200"
RT = "300:300"
SAMPLE_BASE = "192.168.100.0"


def ssh_interactive(ip, commands, wait_after=1.0):
    """Run commands via paramiko invoke_shell."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=SSH_USER, password=SSH_PASS, timeout=10)
    shell = client.invoke_shell(width=250, height=50)
    time.sleep(1)
    shell.recv(65535)

    outputs = []
    for cmd in commands:
        shell.send(cmd + "\n")
        w = 2.5 if "commit" in cmd else wait_after
        time.sleep(w)
        out = shell.recv(65535 * 4).decode("utf-8", errors="replace")
        outputs.append(out)

    shell.close()
    client.close()
    return outputs


def cp_capture(ip, device_name, bpf_filter, count=80, timeout_sec=30):
    """Run packet-capture on device, return output. Blocks until count or timeout."""
    print(f"\n  [{device_name}] Starting CP capture: filter=\"{bpf_filter}\", count={count}")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=SSH_USER, password=SSH_PASS, timeout=10)
    shell = client.invoke_shell(width=250, height=80)
    time.sleep(1)
    shell.recv(65535)

    cmd = f'run packet-capture ncc interface any count {count} filter-expression "{bpf_filter}" verbose'
    shell.send(cmd + "\n")
    time.sleep(1)

    if shell.recv_ready():
        prompt_out = shell.recv(65535).decode("utf-8", errors="replace")
        if "Password" in prompt_out or "password" in prompt_out:
            shell.send(SSH_PASS + "\n")
            time.sleep(1)

    output = ""
    start = time.time()
    while time.time() - start < timeout_sec:
        if shell.recv_ready():
            chunk = shell.recv(65535 * 8).decode("utf-8", errors="replace")
            output += chunk
            if f"{count} packets captured" in output or "packets received" in output:
                break
        time.sleep(0.5)

    shell.send("\x03")
    time.sleep(0.5)
    if shell.recv_ready():
        output += shell.recv(65535).decode("utf-8", errors="replace")

    shell.close()
    client.close()
    print(f"  [{device_name}] Capture done ({len(output)} bytes)")
    return output


def main():
    print("=" * 70)
    print("SW-243514 Wire Verification (build 29)")
    print("  Question: Do IPv4 FlowSpec-VPN UPDATEs carry Extended Communities?")
    print("=" * 70)

    # Build sample routes
    sample_routes = build_flowspec_vpn_ipv4(
        count=SAMPLE_COUNT, base_prefix=SAMPLE_BASE, mask=24,
        rd=RD, rt=RT, action="rate-limit 0")
    print(f"\nSample routes ({SAMPLE_COUNT}):")
    for r in sample_routes:
        print(f"  {r}")

    # Step 1: Enable debug on RR-SA-2
    print("\n--- Step 1: Enable debug bgp updates-in + import on RR-SA-2 ---")
    ssh_interactive(RR_SA2_IP, [
        "configure", "debug", "bgp updates-in", "bgp import", "!", "commit", "exit", "exit",
    ])
    print("  [OK] debug enabled")

    # Step 2: Withdraw sample routes first (in case they exist)
    print("\n--- Step 2: Pre-withdraw sample routes ---")
    withdraw_all(sample_routes, batch_size=10, inter_batch_delay=0.1)
    time.sleep(3)

    # Step 3: Start CP captures on BOTH devices in parallel threads
    print("\n--- Step 3: Starting parallel CP captures ---")
    rr2_capture = {"output": ""}
    pe1_capture = {"output": ""}

    def capture_rr2():
        rr2_capture["output"] = cp_capture(
            RR_SA2_IP, "RR-SA-2", "host 1.1.1.1 and port 179", count=60, timeout_sec=25)

    def capture_pe1():
        pe1_capture["output"] = cp_capture(
            PE1_IP, "PE-1", "host 2.2.2.2 and port 179", count=60, timeout_sec=25)

    t_rr2 = threading.Thread(target=capture_rr2)
    t_pe1 = threading.Thread(target=capture_pe1)
    t_rr2.start()
    t_pe1.start()

    # Wait for captures to initialize
    time.sleep(5)

    # Step 4: Inject sample routes during capture window
    print("\n--- Step 4: Inject sample routes via ExaBGP ---")
    result = inject_batch_fast(sample_routes, batch_size=10, inter_batch_delay=0.1)
    print(f"  Injected: {result['injected']}/{result['total']}")

    # Wait for convergence (PE-1 receives from ExaBGP, re-advertises to RR-SA-2)
    print("  Waiting 8s for propagation: ExaBGP -> PE-1 -> RR-SA-2...")
    time.sleep(8)

    # Step 5: Withdraw to generate more UPDATE traffic
    print("\n--- Step 5: Withdraw sample routes ---")
    withdraw_all(sample_routes, batch_size=10, inter_batch_delay=0.1)
    time.sleep(5)

    # Wait for captures to finish
    print("\n  Waiting for captures to complete...")
    t_rr2.join(timeout=15)
    t_pe1.join(timeout=15)

    # Step 6: Collect debug traces
    print("\n--- Step 6: Collect debug bgp updates-in traces ---")

    print("\n  [RR-SA-2] updates-in traces (last 30 lines with 'update'):")
    trace_updates = ssh_interactive(RR_SA2_IP, [
        "show file traces routing_engine/bgpd_traces | include regex \"rcvd UPDATE|Extended|Community|ext.community|No import|rt_node|ATTR\" | tail 40 | no-more"
    ], wait_after=5)
    for line in trace_updates[-1].split("\n"):
        s = line.strip()
        if s and not s.startswith("RR-SA-2"):
            print(f"  {s}")

    print("\n  [RR-SA-2] import traces (rt_node / No import):")
    trace_import = ssh_interactive(RR_SA2_IP, [
        "show file traces routing_engine/bgpd_traces | include regex \"rt_node|No import|192.168.100\" | tail 20 | no-more"
    ], wait_after=5)
    for line in trace_import[-1].split("\n"):
        s = line.strip()
        if s and not s.startswith("RR-SA-2"):
            print(f"  {s}")

    # Step 7: Save CP capture outputs
    print("\n--- Step 7: Saving capture outputs ---")
    rr2_path = "/tmp/sw243514_wire_rr2.txt"
    pe1_path = "/tmp/sw243514_wire_pe1.txt"

    with open(rr2_path, "w") as f:
        f.write(rr2_capture["output"])
    print(f"  RR-SA-2 capture: {rr2_path} ({len(rr2_capture['output'])} bytes)")

    with open(pe1_path, "w") as f:
        f.write(pe1_capture["output"])
    print(f"  PE-1 capture: {pe1_path} ({len(pe1_capture['output'])} bytes)")

    # Print key lines from captures (look for BGP UPDATE indicators)
    for name, output in [("RR-SA-2", rr2_capture["output"]), ("PE-1", pe1_capture["output"])]:
        print(f"\n  [{name}] Capture summary:")
        lines = output.split("\n")
        for line in lines:
            s = line.strip()
            if any(kw in s.lower() for kw in ["packets captured", "packets received", "update", "0x00", "community"]):
                print(f"    {s}")

    # Step 8: Disable debug
    print("\n--- Step 8: Disable debug on RR-SA-2 ---")
    ssh_interactive(RR_SA2_IP, [
        "configure", "debug", "no bgp updates-in", "no bgp import", "!", "commit", "exit", "exit",
    ])
    print("  [OK] debug disabled")

    print("\n" + "=" * 70)
    print("DONE. Check:")
    print(f"  1. Traces above for 'Extended Community' or 'rt_node 300:300'")
    print(f"  2. {rr2_path} for raw hex of BGP UPDATEs received by RR-SA-2")
    print(f"  3. {pe1_path} for raw hex of BGP UPDATEs sent by PE-1")
    print("=" * 70)


if __name__ == "__main__":
    main()
