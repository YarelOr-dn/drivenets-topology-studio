#!/usr/bin/env python3
"""
Simple Network Mapper - Enable interfaces and LLDP
Direct terminal config push (no files)
"""

import paramiko
import time
import re
import sys

PE_IP = sys.argv[1] if len(sys.argv) > 1 else "100.64.0.220"
PE_USER = "dnroot"
PE_PASS = "dnroot"


def read_until_prompt(channel, timeout=60):
    """Read output until we see a DNOS prompt, handling pager."""
    output = ""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if channel.recv_ready():
            chunk = channel.recv(65535).decode('utf-8', errors='ignore')
            output += chunk
            
            # Handle pager
            if "-- More --" in chunk:
                channel.send("q")
                time.sleep(0.2)
                continue
            
            # Check for prompts
            stripped = output.rstrip()
            if re.search(r'[A-Za-z0-9_-]+(\(cfg[^)]*\))?[#>]\s*$', stripped):
                break
            
            if "commit succeeded" in output.lower():
                time.sleep(0.3)
                while channel.recv_ready():
                    output += channel.recv(65535).decode('utf-8', errors='ignore')
                break
        else:
            time.sleep(0.05)
    
    return re.sub(r'\x1b\[[0-9;]*m', '', output)


def send_cmd(channel, cmd, timeout=60):
    """Send command and wait for prompt."""
    channel.send(cmd + "\n")
    return read_until_prompt(channel, timeout)


print("=== Simple Network Mapper ===", flush=True)
print(f"Target: {PE_IP}", flush=True)

# Connect
print("\n[1] Connecting...", flush=True)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(PE_IP, username=PE_USER, password=PE_PASS, timeout=30)

channel = client.invoke_shell(width=200, height=50)
channel.settimeout(60)
time.sleep(2)
read_until_prompt(channel, timeout=10)

# Disable pager
for _ in range(3):
    send_cmd(channel, "terminal length 0", timeout=5)
print("Connected!", flush=True)

# Get interfaces
print("\n[2] Getting interfaces...", flush=True)
output = send_cmd(channel, "show interfaces", timeout=180)

pattern = r"\|\s*(ge\d+-\d+/\d+/\d+)\s*\|\s*(enabled|disabled)\s*\|\s*(\S+)\s*\|"
interfaces = []
for m in re.finditer(pattern, output):
    if "." not in m.group(1):
        interfaces.append({"name": m.group(1), "admin": m.group(2), "oper": m.group(3)})

print(f"  Found {len(interfaces)} physical interfaces", flush=True)

# Generate config lines
disabled_ifs = [i for i in interfaces if i["admin"] != "enabled"]
print(f"  {len(disabled_ifs)} to enable, {len(interfaces)} for LLDP", flush=True)

# Enter config mode
print("\n[3] Pushing config directly to terminal...", flush=True)
send_cmd(channel, "configure", timeout=10)
send_cmd(channel, "terminal length 0", timeout=5)

# Push interface enables
if disabled_ifs:
    send_cmd(channel, "interfaces", timeout=5)
    for iface in disabled_ifs:
        send_cmd(channel, iface["name"], timeout=3)
        send_cmd(channel, "admin-state enabled", timeout=3)
        send_cmd(channel, "exit", timeout=3)
    send_cmd(channel, "exit", timeout=5)
    print(f"  Enabled {len(disabled_ifs)} interfaces", flush=True)

# Push LLDP config
send_cmd(channel, "protocols", timeout=5)
send_cmd(channel, "lldp", timeout=5)
send_cmd(channel, "admin-state enabled", timeout=3)
for iface in interfaces:
    send_cmd(channel, f"interface {iface['name']}", timeout=3)
    send_cmd(channel, "exit", timeout=3)
send_cmd(channel, "exit", timeout=5)  # exit lldp
send_cmd(channel, "exit", timeout=5)  # exit protocols
print(f"  Configured LLDP on {len(interfaces)} interfaces", flush=True)

# Commit
print("\n[4] Committing...", flush=True)
output = send_cmd(channel, "commit", timeout=180)

if "succeeded" in output.lower():
    print("  Commit successful!", flush=True)
elif "error" in output.lower():
    print(f"  Commit error: {output[-200:]}", flush=True)
else:
    print(f"  Commit done: {output[-100:]}", flush=True)

send_cmd(channel, "end", timeout=10)

# Check LLDP
print("\n[5] Checking LLDP neighbors (wait 10s)...", flush=True)
time.sleep(10)
send_cmd(channel, "terminal length 0", timeout=5)
output = send_cmd(channel, "show lldp neighbors", timeout=60)

neighbors = 0
for line in output.split("\n"):
    if "|" in line and "ge" in line.lower():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3 and parts[2]:  # Has neighbor name
            print(f"  {line.strip()}", flush=True)
            neighbors += 1

if neighbors == 0:
    print("  No neighbors yet (interfaces may be down)", flush=True)
else:
    print(f"  Found {neighbors} neighbors", flush=True)

client.close()
print("\nDone!", flush=True)
