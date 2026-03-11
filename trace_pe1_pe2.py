#!/usr/bin/env python3
"""
Trace path from PE-1 to PE-2
"""

import paramiko
import time
import re
import openpyxl

# Credentials
PE_USER, PE_PASS = "dnroot", "dnroot"
DNAAS_USER, DNAAS_PASS = "sisaev", "Drive1234!"

# Device IPs
PE1_IP = "100.64.2.33"    # YOR_PE-1 (wk31d7vv00023)
PE2_IP = "100.64.0.220"   # YOR_PE-2

# Load DNAAS table
def load_dnaas_table():
    devices = {}
    try:
        wb = openpyxl.load_workbook('/home/dn/CURSOR/dnaas_table.xlsx')
        ws = wb.active
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[2] and row[4]:
                devices[str(row[2]).strip().lower()] = str(row[4]).strip()
    except Exception as e:
        print(f"Warning: {e}")
    return devices

DNAAS_TABLE = load_dnaas_table()

def connect(ip, user, passwd, name=""):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=passwd, timeout=30)
    shell = client.invoke_shell(width=200, height=50)
    shell.settimeout(60)
    time.sleep(1)
    shell.recv(65535)
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
    output = send_cmd(shell, "show lldp neighbors | no-more", timeout=30)
    neighbors = []
    for line in output.split('\n'):
        match = re.match(r'\|\s*([\w\-/\.]+)\s*\|\s*(\S+)\s*\|\s*([\w\-/\.]+)\s*\|\s*(\d+)', line)
        if match:
            local_if, neighbor, remote_if, ttl = match.groups()
            if neighbor and neighbor.strip():
                neighbors.append({'local_if': local_if, 'neighbor': neighbor, 'remote_if': remote_if})
    return neighbors

def get_dnaas_ip(name):
    # Try exact match first
    key = name.lower().strip()
    if key in DNAAS_TABLE:
        return DNAAS_TABLE[key]
    # Try with dashes replaced by underscores
    key2 = key.replace('-', '_')
    if key2 in DNAAS_TABLE:
        return DNAAS_TABLE[key2]
    # Try with underscores replaced by dashes
    key3 = key.replace('_', '-')
    if key3 in DNAAS_TABLE:
        return DNAAS_TABLE[key3]
    # Fuzzy match
    for k, v in DNAAS_TABLE.items():
        if key.replace('-', '').replace('_', '') == k.replace('-', '').replace('_', ''):
            return v
    return None

print("="*70, flush=True)
print("PATH TRACE: PE-1 (YOR_PE-1) --> PE-2 (YOR_PE-2)", flush=True)
print("="*70, flush=True)

path = []

# Step 1: PE-1
print(f"\n[1] PE-1 ({PE1_IP}):", flush=True)
c, s = connect(PE1_IP, PE_USER, PE_PASS, "PE-1")
neighbors = get_lldp_neighbors(s)
c.close()
pe1_leaf = None
for n in neighbors:
    print(f"    {n['local_if']} --> {n['neighbor']}:{n['remote_if']}", flush=True)
    if 'LEAF' in n['neighbor'].upper() or 'DNAAS' in n['neighbor'].upper():
        pe1_leaf = n['neighbor']
        pe1_leaf_port = n['remote_if']
        pe1_local_if = n['local_if']
path.append(("PE-1 (YOR_PE-1)", PE1_IP, pe1_local_if))

if not pe1_leaf:
    print("  ERROR: No DNAAS leaf found!", flush=True)
    exit(1)

# Step 2: PE-1's Leaf
pe1_leaf_ip = get_dnaas_ip(pe1_leaf)
print(f"\n[2] {pe1_leaf} ({pe1_leaf_ip}):", flush=True)
c, s = connect(pe1_leaf_ip, DNAAS_USER, DNAAS_PASS, pe1_leaf)
neighbors = get_lldp_neighbors(s)
c.close()

# Find spines connected to this leaf
spines = []
for n in neighbors:
    if 'SPINE' in n['neighbor'].upper():
        spines.append(n)
        print(f"    {n['local_if']} --> {n['neighbor']}:{n['remote_if']} (SPINE)", flush=True)
    elif 'PE-1' in n['neighbor'].upper() or 'YOR' in n['neighbor'].upper():
        print(f"    {n['local_if']} --> {n['neighbor']}:{n['remote_if']} (PE-1)", flush=True)

path.append((pe1_leaf, pe1_leaf_ip, pe1_leaf_port))

if not spines:
    print("  ERROR: No spines found!", flush=True)
    exit(1)

# Step 3: Spine (use first one)
spine = spines[0]
spine_name = spine['neighbor']
spine_ip = get_dnaas_ip(spine_name)
print(f"\n[3] {spine_name} ({spine_ip}):", flush=True)
c, s = connect(spine_ip, DNAAS_USER, DNAAS_PASS, spine_name)
neighbors = get_lldp_neighbors(s)
c.close()

# Find LEAF-B15 (where PE-2 is)
pe2_leaf = None
for n in neighbors:
    if 'LEAF-B15' in n['neighbor'].upper():
        pe2_leaf = n
        print(f"    {n['local_if']} --> {n['neighbor']}:{n['remote_if']} (PE-2's LEAF)", flush=True)
    elif pe1_leaf.upper() in n['neighbor'].upper():
        print(f"    {n['local_if']} --> {n['neighbor']}:{n['remote_if']} (PE-1's LEAF)", flush=True)

path.append((spine_name, spine_ip, spine['remote_if']))

# If no direct connection to LEAF-B15, check via SuperSpine
if not pe2_leaf:
    print("  LEAF-B15 not directly connected, checking for path...", flush=True)
    for n in neighbors:
        if 'SUPERSPINE' in n['neighbor'].upper() or 'SPINE' in n['neighbor'].upper():
            print(f"    {n['local_if']} --> {n['neighbor']}:{n['remote_if']}", flush=True)

# Step 4: PE-2's Leaf (LEAF-B15)
print(f"\n[4] DNAAS-LEAF-B15 (100.64.101.6):", flush=True)
c, s = connect("100.64.101.6", DNAAS_USER, DNAAS_PASS, "LEAF-B15")
neighbors = get_lldp_neighbors(s)
c.close()

for n in neighbors:
    if 'PE-2' in n['neighbor'].upper() or 'YOR' in n['neighbor'].upper():
        print(f"    {n['local_if']} --> {n['neighbor']}:{n['remote_if']} (PE-2)", flush=True)
        path.append(("DNAAS-LEAF-B15", "100.64.101.6", n['local_if']))
    elif spine_name.upper() in n['neighbor'].upper():
        print(f"    {n['local_if']} --> {n['neighbor']}:{n['remote_if']} (SPINE)", flush=True)

# Step 5: PE-2
print(f"\n[5] PE-2 ({PE2_IP}):", flush=True)
c, s = connect(PE2_IP, PE_USER, PE_PASS, "PE-2")
neighbors = get_lldp_neighbors(s)
c.close()

for n in neighbors:
    if 'LEAF' in n['neighbor'].upper():
        print(f"    {n['local_if']} --> {n['neighbor']}:{n['remote_if']}", flush=True)
        path.append(("PE-2 (YOR_PE-2)", PE2_IP, n['local_if']))

# Print path summary
print("\n" + "="*70, flush=True)
print("PATH SUMMARY: PE-1 --> PE-2", flush=True)
print("="*70, flush=True)
print("""
  PE-1 (YOR_PE-1) @ 100.64.2.33
       │
       │ ge400-0/0/4
       ▼
  DNAAS-LEAF-D16
       │
       │ ge100-0/0/X (to spine)
       ▼
  DNAAS-SPINE-??? 
       │
       │ ge100-0/0/X (to LEAF-B15)
       ▼
  DNAAS-LEAF-B15 @ 100.64.101.6
       │
       │ ge100-0/0/6, ge100-0/0/7
       ▼
  PE-2 (YOR_PE-2) @ 100.64.0.220
       │
       │ ge400-0/0/0, ge400-0/0/2
""", flush=True)

print("="*70, flush=True)
print("TRACE COMPLETE", flush=True)
print("="*70, flush=True)

