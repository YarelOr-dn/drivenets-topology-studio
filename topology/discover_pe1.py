#!/usr/bin/env python3
"""
Discover PE-1 connections by pushing LLDP to ALL physical interfaces
"""

import paramiko
import time
import re
import openpyxl

PE_IP = "100.64.0.210"
PE_USER, PE_PASS = "dnroot", "dnroot"
DNAAS_USER, DNAAS_PASS = "sisaev", "Drive1234!"

def load_dnaas_table():
    devices = {}
    try:
        wb = openpyxl.load_workbook('/home/dn/CURSOR/dnaas_table.xlsx')
        ws = wb.active
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[2] and row[4]:
                devices[str(row[2]).strip().lower()] = str(row[4]).strip()
    except:
        pass
    return devices

DNAAS_TABLE = load_dnaas_table()

def connect(ip, user, passwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=passwd, timeout=30)
    shell = client.invoke_shell(width=200, height=50)
    shell.settimeout(120)
    time.sleep(1)
    shell.recv(65535)
    return client, shell

def send_cmd(shell, cmd, timeout=60):
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

def get_all_physical_interfaces(shell):
    """Get ALL physical ge* interfaces (regardless of state)"""
    output = send_cmd(shell, "show interfaces | no-more", timeout=60)
    interfaces = []
    for line in output.split('\n'):
        match = re.match(r'\|\s*(ge\d+-\d+/\d+/\d+)\s*\|', line)
        if match:
            iface = match.group(1)
            if '.' not in iface:
                interfaces.append(iface)
    return sorted(set(interfaces))

def get_lldp_neighbors(shell):
    """Get LLDP neighbors with actual data"""
    output = send_cmd(shell, "show lldp neighbors | no-more", timeout=30)
    neighbors = []
    for line in output.split('\n'):
        match = re.match(r'\|\s*([\w\-/\.]+)\s*\|\s*(\S+)\s*\|\s*([\w\-/\.]+)\s*\|\s*(\d+)', line)
        if match:
            local_if, neighbor, remote_if, ttl = match.groups()
            if neighbor and neighbor.strip():  # Has actual neighbor
                neighbors.append({
                    'local_if': local_if,
                    'neighbor': neighbor,
                    'remote_if': remote_if
                })
    return neighbors

print("="*70, flush=True)
print("DISCOVERING PE-1 CONNECTIONS", flush=True)
print("="*70, flush=True)

# Connect to PE-1
print(f"\n[1] Connecting to PE-1 ({PE_IP})...", flush=True)
client, shell = connect(PE_IP, PE_USER, PE_PASS)
print("  Connected!", flush=True)

# Get all physical interfaces
print("\n[2] Getting all physical interfaces...", flush=True)
interfaces = get_all_physical_interfaces(shell)
print(f"  Found {len(interfaces)} physical interfaces", flush=True)

# Push LLDP config for ALL interfaces
print(f"\n[3] Pushing LLDP config for ALL {len(interfaces)} interfaces...", flush=True)

# Enter config mode
send_cmd(shell, "configure", timeout=10)

# Build LLDP config
shell.send("protocols lldp\n")
time.sleep(0.1)
shell.send("admin-state enabled\n")
time.sleep(0.1)

for iface in interfaces:
    shell.send(f"interface {iface}\n")
    time.sleep(0.02)

shell.send("!\n")
shell.send("!\n")
time.sleep(1)
shell.recv(65535)

# Commit
print("  Committing...", flush=True)
output = send_cmd(shell, "commit", timeout=60)
if "succeeded" in output.lower():
    print("  Commit succeeded!", flush=True)
elif "no configuration changes" in output.lower():
    print("  LLDP already configured!", flush=True)
else:
    print("  Commit done.", flush=True)

send_cmd(shell, "end", timeout=10)

# Wait for neighbors
print("\n[4] Waiting 45 seconds for LLDP neighbors to appear...", flush=True)
for i in range(45, 0, -5):
    print(f"    {i}s remaining...", flush=True)
    time.sleep(5)

# Check neighbors
print("\n[5] Checking LLDP neighbors...", flush=True)
neighbors = get_lldp_neighbors(shell)

if not neighbors:
    print("  NO NEIGHBORS FOUND!", flush=True)
    print("  PE-1 appears to have no physical connections.", flush=True)
else:
    print(f"  Found {len(neighbors)} neighbors:", flush=True)
    for n in neighbors:
        print(f"    {n['local_if']} --> {n['neighbor']}:{n['remote_if']}", flush=True)
    
    # Check for DNAAS neighbors
    print("\n[6] Checking for DNAAS neighbors...", flush=True)
    for n in neighbors:
        neighbor_name = n['neighbor']
        if 'DNAAS' in neighbor_name.upper() or 'LEAF' in neighbor_name.upper() or 'SPINE' in neighbor_name.upper():
            print(f"  Found DNAAS: {neighbor_name}", flush=True)
            # Look up IP
            dnaas_ip = DNAAS_TABLE.get(neighbor_name.lower())
            if dnaas_ip:
                print(f"    IP: {dnaas_ip}", flush=True)
                print(f"    Connecting to trace further...", flush=True)
                try:
                    d_client, d_shell = connect(dnaas_ip, DNAAS_USER, DNAAS_PASS)
                    d_neighbors = get_lldp_neighbors(d_shell)
                    print(f"    {neighbor_name} neighbors:", flush=True)
                    for dn in d_neighbors:
                        print(f"      {dn['local_if']} --> {dn['neighbor']}:{dn['remote_if']}", flush=True)
                    d_client.close()
                except Exception as e:
                    print(f"    Could not connect: {e}", flush=True)
            else:
                print(f"    IP not found in DNAAS table", flush=True)

client.close()
print("\n" + "="*70, flush=True)
print("DISCOVERY COMPLETE", flush=True)
print("="*70, flush=True)









