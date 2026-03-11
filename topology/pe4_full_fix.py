#!/usr/bin/env python3
"""Fix PE-4 BGP: create ExaBGP neighbor, kill+restart ExaBGP, fix Spirent peers."""
import paramiko
import time
import subprocess
import json
import sys

PE4_IP = "100.64.7.197"
PE4_USER = "dnroot"
PE4_PASS = "dnroot"
BGP_AS = "1234567"
EXABGP_PEER = "100.64.6.134"
OUT = "/home/dn/CURSOR/pe4_full_fix_result.txt"

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

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return r.stdout + r.stderr

with open(OUT, 'w') as f:
    f.write(f"PE-4 Full Fix - {time.strftime('%Y-%m-%d %H:%M:%S')}\n{'='*60}\n\n")

# Step 1: Kill ExaBGP to stop feeding FortiGate IDS
log("=== STEP 1: Kill ExaBGP (stop SYN flood to FortiGate) ===")
r = run("pkill -f exabgp 2>/dev/null; sleep 2; ps aux | grep exabgp | grep -v grep || echo 'ExaBGP killed successfully'")
log(r)

# Step 2: Check current global BGP config on PE-4
log("\n=== STEP 2: Check current global BGP neighbors ===")
try:
    o = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
        "show config protocols bgp 1234567 | no-more",
    ], wait=3)
    log(o)
except Exception as e:
    log(f"ERROR: {e}")

# Step 3: Create ExaBGP neighbor on PE-4
log("\n=== STEP 3: Create ExaBGP neighbor 100.64.6.134 on PE-4 ===")
config_cmds = [
    "configure",
    f"protocols bgp {BGP_AS} neighbor {EXABGP_PEER}",
    "remote-as 65200",
    "admin-state enabled",
    "passive enabled",
    "description ExaBGP-server",
    "ebgp-multihop 10",
    "timers hold-time 180",
    "timers keepalive-interval 60",
    "address-family ipv4-flowspec-vpn",
    "send-community community-type both",
    "soft-reconfiguration inbound",
    "exit",
    "address-family ipv6-flowspec-vpn",
    "send-community community-type both",
    "soft-reconfiguration inbound",
    "exit",
    "exit",
    "commit",
]
try:
    o = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, config_cmds, wait=1.5)
    log(o)
except Exception as e:
    log(f"ERROR: {e}")

# Step 4: Verify neighbor was created
log("\n=== STEP 4: Verify neighbor created ===")
try:
    o = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
        f"show config protocols bgp {BGP_AS} neighbor {EXABGP_PEER} | no-more",
    ], wait=3)
    log(o)
except Exception as e:
    log(f"ERROR: {e}")

# Step 5: Wait for FortiGate IDS quarantine to clear
log("\n=== STEP 5: Wait 90s for FortiGate IDS quarantine to clear ===")
log("ExaBGP was killed in Step 1 (no more SYNs), PE-4 has passive enabled (no SYNs from device).")
log("FortiGate quarantine should expire in 2-5 minutes.")
for i in range(9):
    time.sleep(10)
    log(f"  Waited {(i+1)*10}s...")
log("90s wait complete.")

# Step 6: Verify ping still works
log("\n=== STEP 6: Verify inband connectivity ===")
r = run("ping -c 2 -W 2 100.70.0.206")
log(r)

# Step 7: Start ExaBGP fresh
log("\n=== STEP 7: Start ExaBGP ===")
r = run("python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py start --config /tmp/exabgp_pe_4.conf --session-id pe_4 2>&1")
log(r)

# Step 8: Wait for BGP to establish
log("\n=== STEP 8: Wait 25s for BGP establishment ===")
time.sleep(25)

# Step 9: Verify ExaBGP
log("\n=== STEP 9: Verify ExaBGP session ===")
r = run("python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py verify --session-id pe_4 2>&1")
log(r)

# Step 10: Check BGP on PE-4
log("\n=== STEP 10: Check PE-4 BGP summary ===")
try:
    o = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
        "show bgp summary | no-more",
    ], wait=3)
    log(o)
except Exception as e:
    log(f"ERROR: {e}")

# Step 11: Fix Spirent ALPHA peer (needs IP 49.49.49.9, gw 49.49.49.4, VLAN 219)
log("\n=== STEP 11: Fix Spirent ALPHA peer ===")
log("Current ALPHA_CE_0 has wrong IP (10.99.219.1). PE-4 expects CE at 49.49.49.9.")
log("Removing old device and creating new one with correct IP.")
r = run("python3 /home/dn/SCALER/SPIRENT/spirent_tool.py remove-device --name ALPHA_CE_0 2>&1")
log(f"Remove old: {r}")

r = run("python3 /home/dn/SCALER/SPIRENT/spirent_tool.py create-device --ip 49.49.49.9 --gateway 49.49.49.4 --vlan 219 --name ALPHA_CE_0 2>&1")
log(f"Create new: {r}")

r = run("python3 /home/dn/SCALER/SPIRENT/spirent_tool.py bgp-peer --device-name ALPHA_CE_0 --as 65100 --dut-as 1234567 --neighbor 49.49.49.4 2>&1")
log(f"BGP peer: {r}")

# Step 12: Fix Spirent ZULU peer
log("\n=== STEP 12: Fix Spirent ZULU peer ===")
log("PE-4 ZULU: ge100-18/0/1 (untagged, IP 50.50.50.1/30), neighbor expects 50.50.50.2")
log("Current ZULU_CE_0 has IP 50.50.50.1 - should be 50.50.50.2 (the neighbor PE-4 expects)")
r = run("python3 /home/dn/SCALER/SPIRENT/spirent_tool.py remove-device --name ZULU_CE_0 2>&1")
log(f"Remove old: {r}")

r = run("python3 /home/dn/SCALER/SPIRENT/spirent_tool.py create-device --ip 50.50.50.2 --gateway 50.50.50.1 --name ZULU_CE_0 2>&1")
log(f"Create new (no VLAN - untagged): {r}")

r = run("python3 /home/dn/SCALER/SPIRENT/spirent_tool.py bgp-peer --device-name ZULU_CE_0 --as 4500 --dut-as 1234567 --neighbor 50.50.50.1 2>&1")
log(f"BGP peer: {r}")

# Step 13: Start protocols
log("\n=== STEP 13: Start Spirent protocols ===")
r = run("python3 /home/dn/SCALER/SPIRENT/spirent_tool.py protocol-start 2>&1")
log(f"Protocol start: {r}")

# Step 14: Wait and check Spirent BGP
log("\n=== STEP 14: Wait 15s and check Spirent BGP ===")
time.sleep(15)
r = run("python3 /home/dn/SCALER/SPIRENT/spirent_tool.py bgp-status --json 2>&1")
log(f"BGP status: {r}")

# Step 15: Check VRF peers on PE-4
log("\n=== STEP 15: Check VRF BGP peers on PE-4 ===")
try:
    o = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
        "show bgp instance vrf ALPHA summary | no-more",
        "show bgp instance vrf ZULU summary | no-more",
    ], wait=3)
    log(o)
except Exception as e:
    log(f"ERROR: {e}")

log("\n=== ALL DONE ===")
