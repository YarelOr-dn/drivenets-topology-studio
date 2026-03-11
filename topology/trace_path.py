#!/usr/bin/env python3
"""
Trace network path from PE-1 to PE-2 via LLDP and Bridge Domains
"""

import paramiko
import time
import re
import sys
import openpyxl

# Device credentials
PE_USER = "dnroot"
PE_PASS = "dnroot"
DNAAS_USER = "sisaev"
DNAAS_PASS = "Drive1234!"

PE1_IP = "100.64.0.210"
PE2_IP = "100.64.0.220"

# Load DNAAS table
def load_dnaas_table():
    """Load DNAAS device info from Excel."""
    dnaas = {}
    try:
        wb = openpyxl.load_workbook("/home/dn/CURSOR/dnaas_table.xlsx")
        ws = wb.active
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[2] and row[4]:  # Name and IP
                name = str(row[2]).strip()
                ip = str(row[4]).strip()
                dnaas[name.lower()] = ip
                # Also store without domain
                short = name.split('.')[0].lower()
                dnaas[short] = ip
        print(f"Loaded {len(dnaas)} DNAAS entries", flush=True)
    except Exception as e:
        print(f"Warning: Could not load DNAAS table: {e}", flush=True)
    return dnaas


def connect_device(ip, user, passwd, name="device"):
    """Connect to a device and return shell channel."""
    print(f"  Connecting to {name} ({ip})...", flush=True)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=passwd, timeout=30)
    
    channel = client.invoke_shell(width=200, height=50)
    channel.settimeout(60)
    time.sleep(2)
    
    # Clear buffer and disable pager
    while channel.recv_ready():
        channel.recv(65535)
    channel.send("terminal length 0\n")
    time.sleep(1)
    while channel.recv_ready():
        channel.recv(65535)
    
    return client, channel


def read_until_prompt(channel, timeout=60):
    """Read output until prompt."""
    output = ""
    start = time.time()
    
    while time.time() - start < timeout:
        if channel.recv_ready():
            chunk = channel.recv(65535).decode('utf-8', errors='ignore')
            output += chunk
            if "-- More --" in chunk:
                channel.send("q")
                time.sleep(0.2)
                continue
            if re.search(r'[A-Za-z0-9_-]+(\(cfg[^)]*\))?[#>]\s*$', output.rstrip()):
                break
        else:
            time.sleep(0.05)
    
    return re.sub(r'\x1b\[[0-9;]*m', '', output)


def send_cmd(channel, cmd, timeout=60):
    """Send command and get output."""
    channel.send(cmd + "\n")
    return read_until_prompt(channel, timeout)


def get_lldp_neighbors(channel):
    """Get LLDP neighbors as list of dicts."""
    output = send_cmd(channel, "show lldp neighbors", timeout=60)
    neighbors = []
    
    for line in output.split("\n"):
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4 and parts[1] and "ge" in parts[1].lower():
                neighbors.append({
                    "local_if": parts[1],
                    "neighbor": parts[2] if len(parts) > 2 else "",
                    "remote_if": parts[3] if len(parts) > 3 else ""
                })
    
    return neighbors


def get_bridge_domains(channel):
    """Get bridge domain info."""
    output = send_cmd(channel, "show network-services bridge-domain", timeout=120)
    return output


# Main
print("=== Path Discovery: PE-1 to PE-2 ===\n", flush=True)

dnaas_table = load_dnaas_table()

# Step 1: Get PE-1 LLDP neighbors
print("\n[1] PE-1 LLDP Neighbors:", flush=True)
pe1_client, pe1_channel = connect_device(PE1_IP, PE_USER, PE_PASS, "PE-1")
pe1_neighbors = get_lldp_neighbors(pe1_channel)

print(f"  Found {len(pe1_neighbors)} neighbors:", flush=True)
for n in pe1_neighbors:
    print(f"    {n['local_if']} -> {n['neighbor']} ({n['remote_if']})", flush=True)

# Find DNAAS connections
dnaas_connections = []
for n in pe1_neighbors:
    neighbor_lower = n['neighbor'].lower()
    # Check if this is a DNAAS device
    for dnaas_name, dnaas_ip in dnaas_table.items():
        if dnaas_name in neighbor_lower or neighbor_lower in dnaas_name:
            dnaas_connections.append({
                "pe_if": n['local_if'],
                "dnaas_name": n['neighbor'],
                "dnaas_if": n['remote_if'],
                "dnaas_ip": dnaas_ip
            })
            break

print(f"\n  DNAAS connections: {len(dnaas_connections)}", flush=True)
for d in dnaas_connections[:5]:
    print(f"    PE-1:{d['pe_if']} -> {d['dnaas_name']}:{d['dnaas_if']}", flush=True)

pe1_client.close()

# Step 2: Trace through first DNAAS
if dnaas_connections:
    first_dnaas = dnaas_connections[0]
    print(f"\n[2] Tracing through {first_dnaas['dnaas_name']}:", flush=True)
    
    try:
        dnaas_client, dnaas_channel = connect_device(
            first_dnaas['dnaas_ip'], DNAAS_USER, DNAAS_PASS, first_dnaas['dnaas_name']
        )
        
        # Get LLDP from DNAAS
        dnaas_neighbors = get_lldp_neighbors(dnaas_channel)
        print(f"  DNAAS has {len(dnaas_neighbors)} LLDP neighbors", flush=True)
        
        # Find PE-2 connection
        pe2_direct = None
        for n in dnaas_neighbors:
            if "pe-2" in n['neighbor'].lower() or "pe2" in n['neighbor'].lower():
                pe2_direct = n
                break
        
        if pe2_direct:
            print(f"  Direct path to PE-2 found!", flush=True)
            print(f"    DNAAS:{pe2_direct['local_if']} -> PE-2:{pe2_direct['remote_if']}", flush=True)
        else:
            # Check bridge domains
            print("  Checking bridge domains...", flush=True)
            bd_output = get_bridge_domains(dnaas_channel)
            print(f"  Got {len(bd_output)} chars of BD info", flush=True)
            
            # Show relevant BDs
            current_bd = ""
            for line in bd_output.split("\n")[:50]:
                if "bridge-domain" in line.lower() or first_dnaas['dnaas_if'].split('.')[0] in line:
                    print(f"    {line.strip()}", flush=True)
        
        dnaas_client.close()
        
    except Exception as e:
        print(f"  Error connecting to DNAAS: {e}", flush=True)

# Step 3: Get PE-2 LLDP to verify
print(f"\n[3] PE-2 LLDP Neighbors:", flush=True)
pe2_client, pe2_channel = connect_device(PE2_IP, PE_USER, PE_PASS, "PE-2")
pe2_neighbors = get_lldp_neighbors(pe2_channel)

print(f"  Found {len(pe2_neighbors)} neighbors:", flush=True)
for n in pe2_neighbors[:10]:
    print(f"    {n['local_if']} -> {n['neighbor']} ({n['remote_if']})", flush=True)

pe2_client.close()

# Summary
print("\n" + "="*50, flush=True)
print("PATH SUMMARY:", flush=True)
print("="*50, flush=True)
print(f"PE-1 ({PE1_IP})", flush=True)
if dnaas_connections:
    print(f"  | via {dnaas_connections[0]['pe_if']}", flush=True)
    print(f"  v", flush=True)
    print(f"{dnaas_connections[0]['dnaas_name']} (DNAAS)", flush=True)
    print(f"  | (bridge domain path)", flush=True)
    print(f"  v", flush=True)
print(f"PE-2 ({PE2_IP})", flush=True)
print("="*50, flush=True)










