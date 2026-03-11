#!/usr/bin/env python3
"""Fix PE-4 ExaBGP neighbor config and restart ExaBGP. Then fix Spirent peers."""
import paramiko
import time
import subprocess
import sys

PE4_IP = "100.64.7.197"
PE4_USER = "dnroot"
PE4_PASS = "dnroot"
OUT = "/home/dn/CURSOR/pe4_fix_final_result.txt"

def log(msg):
    print(msg)
    with open(OUT, 'a') as f:
        f.write(msg + '\n')

def ssh_cli(host, user, password, commands, wait=2.0):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=10)
    chan = client.invoke_shell(width=250, height=50)
    time.sleep(2)
    chan.recv(65536)
    for cmd in commands:
        chan.send(cmd + '\n')
        time.sleep(wait)
    output = ""
    time.sleep(1)
    while chan.recv_ready():
        output += chan.recv(65536).decode('utf-8', errors='replace')
        time.sleep(0.3)
    chan.close()
    client.close()
    return output

def run(cmd, timeout=60):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.stdout + r.stderr

with open(OUT, 'w') as f:
    f.write(f"PE-4 Final Fix - {time.strftime('%Y-%m-%d %H:%M:%S')}\n{'='*60}\n\n")

# Step 1: Abort any pending config from the failed attempt
log("=== STEP 1: Clean up failed config on PE-4 ===")
try:
    o = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
        "configure",
        "rollback 0",
        "exit",
    ], wait=2)
    log(o)
except Exception as e:
    log(f"ERROR: {e}")

# Step 2: Create ExaBGP neighbor with CORRECT DNOS AFI names
# Using same AFI names as the existing RR neighbor (2.2.2.2)
log("\n=== STEP 2: Create ExaBGP neighbor with correct DNOS syntax ===")
try:
    o = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
        "configure",
        "protocols bgp 1234567 neighbor 100.64.6.134",
        "remote-as 65200",
        "admin-state enabled",
        "passive enabled",
        "description ExaBGP-server",
        "ebgp-multihop 10",
        "timers hold-time 180",
        # AFI: ipv4-flowspec (FlowSpec SAFI 133 + 134)
        "address-family ipv4-flowspec",
        "allow-as-in enabled",
        "send-community community-type both",
        "soft-reconfiguration inbound",
        "exit",
        # AFI: ipv4-vpn (L3VPN)
        "address-family ipv4-vpn",
        "allow-as-in enabled",
        "send-community community-type both",
        "soft-reconfiguration inbound",
        "exit",
        # AFI: ipv4-unicast
        "address-family ipv4-unicast",
        "send-community community-type both",
        "soft-reconfiguration inbound",
        "exit",
        # AFI: ipv6-flowspec
        "address-family ipv6-flowspec",
        "allow-as-in enabled",
        "send-community community-type both",
        "soft-reconfiguration inbound",
        "exit",
        # AFI: ipv6-vpn
        "address-family ipv6-vpn",
        "allow-as-in enabled",
        "send-community community-type both",
        "soft-reconfiguration inbound",
        "exit",
        # Back to top and commit
        "exit",  # exit neighbor
        "exit",  # exit bgp
        "exit",  # exit protocols
        "commit",
    ], wait=1.0)
    log(o)
except Exception as e:
    log(f"ERROR: {e}")

# Step 3: Verify the neighbor config was committed
log("\n=== STEP 3: Verify neighbor config ===")
try:
    o = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
        "show config protocols bgp 1234567 neighbor 100.64.6.134 | no-more",
    ], wait=3)
    log(o)
except Exception as e:
    log(f"ERROR: {e}")

# Step 4: Kill ExaBGP and wait for FortiGate
log("\n=== STEP 4: Kill ExaBGP and wait 120s for FortiGate ===")
run("pkill -f exabgp 2>/dev/null")
log("ExaBGP killed. Waiting 120s for FortiGate IDS quarantine to clear...")
for i in range(12):
    time.sleep(10)
    log(f"  Waited {(i+1)*10}s...")
log("120s wait complete.")

# Step 5: Verify path is clear
log("\n=== STEP 5: Verify inband path ===")
r = run("ping -c 2 -W 2 100.70.0.206")
log(r)

# Step 6: Start ExaBGP
log("\n=== STEP 6: Start ExaBGP ===")
r = run("python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py start --config /tmp/exabgp_pe_4.conf --session-id pe_4 2>&1", timeout=30)
log(r)

# Step 7: Wait and verify
log("\n=== STEP 7: Wait 30s and verify ExaBGP ===")
time.sleep(30)
r = run("python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py verify --session-id pe_4 2>&1")
log(r)

# Step 8: Check PE-4 BGP summary for ExaBGP neighbor
log("\n=== STEP 8: Check PE-4 BGP summary ===")
try:
    o = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
        "show bgp neighbor 100.64.6.134 | no-more",
    ], wait=3)
    log(o)
except Exception as e:
    log(f"ERROR: {e}")

# Step 9: Fix Spirent - ZULU peer (remove old, create with correct IP)
log("\n=== STEP 9: Fix Spirent ZULU peer ===")
log("PE-4 ZULU neighbor expects 50.50.50.2. Spirent must present as 50.50.50.2.")
r = run("python3 /home/dn/SCALER/SPIRENT/spirent_tool.py remove-device --name ZULU_CE_0 2>&1")
log(f"Remove old ZULU: {r}")

# ZULU is untagged port-mode (no VLAN tag), so don't specify --vlan
r = run("python3 /home/dn/SCALER/SPIRENT/spirent_tool.py create-device --ip 50.50.50.2 --gateway 50.50.50.1 --name ZULU_CE_0 2>&1")
log(f"Create ZULU: {r}")

# Step 10: Start Spirent protocols and check
log("\n=== STEP 10: Start Spirent protocols ===")
r = run("python3 /home/dn/SCALER/SPIRENT/spirent_tool.py protocol-start 2>&1", timeout=30)
log(f"Protocol start: {r}")

log("\nWaiting 15s for BGP establishment...")
time.sleep(15)

r = run("python3 /home/dn/SCALER/SPIRENT/spirent_tool.py bgp-status --json 2>&1", timeout=15)
log(f"Spirent BGP status: {r}")

# Step 11: Final VRF BGP check
log("\n=== STEP 11: Final PE-4 VRF BGP check ===")
try:
    o = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
        "show bgp instance vrf ALPHA summary | no-more",
        "show bgp instance vrf ZULU summary | no-more",
    ], wait=3)
    log(o)
except Exception as e:
    log(f"ERROR: {e}")

log("\n=== ALL DONE ===")
