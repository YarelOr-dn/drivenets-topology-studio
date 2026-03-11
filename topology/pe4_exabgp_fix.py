#!/usr/bin/env python3
"""Fix ExaBGP neighbor: add update-source, commit, restart ExaBGP."""
import paramiko
import time
import subprocess

PE4_IP = "100.64.7.197"
PE4_USER = "dnroot"
PE4_PASS = "dnroot"
OUT = "/home/dn/CURSOR/pe4_exabgp_fix_result.txt"

def log(msg):
    print(msg)
    with open(OUT, 'a') as f:
        f.write(msg + '\n')

def ssh_cli(host, user, password, commands, wait=1.5):
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
    f.write(f"ExaBGP Fix - {time.strftime('%Y-%m-%d %H:%M:%S')}\n{'='*60}\n\n")

# Step 1: Kill ExaBGP first (stop SYN attempts while we fix config)
log("=== STEP 1: Kill ExaBGP ===")
run("pkill -f exabgp 2>/dev/null")
time.sleep(2)
log("ExaBGP killed")

# Step 2: Rollback any pending config, then apply fresh neighbor with update-source
log("\n=== STEP 2: Create ExaBGP neighbor with update-source ===")
try:
    o = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
        "configure",
        "rollback 0",
        # Create neighbor
        "protocols bgp 1234567 neighbor 100.64.6.134",
        "remote-as 65200",
        "admin-state enabled",
        "passive enabled",
        "description ExaBGP-server",
        "ebgp-multihop 10",
        "update-source ge100-18/0/6.999",
        "timers hold-time 180",
        # AFIs
        "address-family ipv4-flowspec",
        "allow-as-in enabled",
        "send-community community-type both",
        "soft-reconfiguration inbound",
        "exit",
        "address-family ipv4-vpn",
        "allow-as-in enabled",
        "send-community community-type both",
        "soft-reconfiguration inbound",
        "exit",
        "address-family ipv4-unicast",
        "send-community community-type both",
        "soft-reconfiguration inbound",
        "exit",
        "address-family ipv6-flowspec",
        "allow-as-in enabled",
        "send-community community-type both",
        "soft-reconfiguration inbound",
        "exit",
        "address-family ipv6-vpn",
        "allow-as-in enabled",
        "send-community community-type both",
        "soft-reconfiguration inbound",
        "exit",
        # Exit neighbor scope and commit
        "exit",
        "exit",
        "exit",
        "commit",
    ], wait=1.0)
    log(o)
except Exception as e:
    log(f"ERROR: {e}")

# Step 3: Verify
log("\n=== STEP 3: Verify neighbor config committed ===")
try:
    o = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
        "show config protocols bgp 1234567 neighbor 100.64.6.134 | no-more",
    ], wait=3)
    log(o)
except Exception as e:
    log(f"ERROR: {e}")

# Step 4: Wait for FortiGate (ExaBGP was killed, give 90s)
log("\n=== STEP 4: Wait 90s for FortiGate ===")
for i in range(9):
    time.sleep(10)
    log(f"  Waited {(i+1)*10}s...")

# Step 5: Start ExaBGP
log("\n=== STEP 5: Start ExaBGP ===")
r = run("python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py start --config /tmp/exabgp_pe_4.conf --session-id pe_4 2>&1", timeout=30)
log(r)

# Step 6: Wait and verify
log("\n=== STEP 6: Wait 30s and verify ===")
time.sleep(30)
r = run("python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py verify --session-id pe_4 2>&1")
log(r)

# Step 7: Check neighbor on PE-4
log("\n=== STEP 7: Check PE-4 neighbor ===")
try:
    o = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
        "show bgp neighbor 100.64.6.134 | no-more",
    ], wait=4)
    log(o)
except Exception as e:
    log(f"ERROR: {e}")

# Step 8: If not established, run diagnose
log("\n=== STEP 8: ExaBGP diagnose ===")
r = run("python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py diagnose --session-id pe_4 2>&1")
log(r)

# Step 9: Check ExaBGP log
log("\n=== STEP 9: ExaBGP log tail ===")
r = run("tail -20 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/logs/pe_4_exabgp.log 2>&1")
log(r)

log("\n=== DONE ===")
