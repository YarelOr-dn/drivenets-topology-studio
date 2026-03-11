#!/usr/bin/env python3
"""
Trace path through DNAAS fabric from PE-2
"""
import paramiko
import time
import re

# Credentials
PE_USER, PE_PASS = "dnroot", "dnroot"
DNAAS_USER, DNAAS_PASS = "sisaev", "Drive1234!"

def connect(ip, user, passwd, name=""):
    print(f"  Connecting to {name} ({ip})...", flush=True)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=passwd, timeout=30)
    shell = client.invoke_shell(width=200, height=50)
    shell.settimeout(60)
    time.sleep(1)
    shell.recv(65535)
    print(f"  Connected!", flush=True)
    return client, shell

def send_cmd(shell, cmd, timeout=30):
    shell.send(cmd + "\n")
    output = ""
    end_time = time.time() + timeout
    while time.time() < end_time:
        if shell.recv_ready():
            output += shell.recv(65535).decode('utf-8', errors='ignore')
            if output.rstrip().endswith('#') or output.rstrip().endswith('>'):
                break
        else:
            time.sleep(0.2)
    return output

def get_lldp_neighbors(shell):
    """Get LLDP neighbors"""
    output = send_cmd(shell, "show lldp neighbors | no-more", timeout=30)
    neighbors = []
    for line in output.split('\n'):
        # Format: | interface | neighbor_name | neighbor_if | ttl |
        match = re.match(r'\|\s*([\w\-/\.]+)\s*\|\s*(\S+)\s*\|\s*([\w\-/\.]+)\s*\|\s*(\d+)', line)
        if match:
            local_if, neighbor, remote_if, ttl = match.groups()
            neighbors.append({
                'local_if': local_if,
                'neighbor': neighbor,
                'remote_if': remote_if
            })
    return neighbors

print("="*60, flush=True)
print("TRACING PATH FROM PE-2 THROUGH DNAAS", flush=True)
print("="*60, flush=True)

# Step 1: Connect to PE-2
print("\n[1] PE-2 (100.64.0.220):", flush=True)
pe2_client, pe2_shell = connect("100.64.0.220", PE_USER, PE_PASS, "PE-2")
pe2_neighbors = get_lldp_neighbors(pe2_shell)
print("  LLDP Neighbors:", flush=True)
for n in pe2_neighbors:
    print(f"    {n['local_if']} --> {n['neighbor']}:{n['remote_if']}", flush=True)
pe2_client.close()

# Step 2: Connect to DNAAS-LEAF-B15
print("\n[2] DNAAS-LEAF-B15 (100.64.101.6):", flush=True)
leaf_client, leaf_shell = connect("100.64.101.6", DNAAS_USER, DNAAS_PASS, "DNAAS-LEAF-B15")
leaf_neighbors = get_lldp_neighbors(leaf_shell)
print("  LLDP Neighbors:", flush=True)
for n in leaf_neighbors:
    print(f"    {n['local_if']} --> {n['neighbor']}:{n['remote_if']}", flush=True)

# Check bridge domains for PE-2 facing ports
print("\n  Checking Bridge Domains for PE-2 ports...", flush=True)
bd_output = send_cmd(leaf_shell, "show network-services bridge domain | no-more", timeout=30)
print("  Bridge Domain output (first 2000 chars):", flush=True)
print(bd_output[:2000], flush=True)

leaf_client.close()

print("\n" + "="*60, flush=True)
print("TRACE COMPLETE", flush=True)
print("="*60, flush=True)









