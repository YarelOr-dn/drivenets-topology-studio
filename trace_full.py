#!/usr/bin/env python3
"""
Full path trace: PE-1 to PE-2 through DNAAS fabric
"""

import paramiko
import time
import re
import openpyxl

PE_USER = "dnroot"
PE_PASS = "dnroot"
DNAAS_USER = "sisaev"
DNAAS_PASS = "Drive1234!"

PE1_IP = "100.64.0.210"
PE2_IP = "100.64.0.220"

def load_dnaas():
    dnaas = {}
    wb = openpyxl.load_workbook("/home/dn/CURSOR/dnaas_table.xlsx")
    for row in wb.active.iter_rows(min_row=2, values_only=True):
        if row[2] and row[4]:
            name = str(row[2]).strip()
            ip = str(row[4]).strip()
            dnaas[name.lower()] = ip
            dnaas[name.split('.')[0].lower()] = ip
    return dnaas


def connect(ip, user, passwd, name=""):
    print(f"  -> {name} ({ip})", flush=True)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=passwd, timeout=30)
    ch = client.invoke_shell(width=200, height=50)
    ch.settimeout(120)
    time.sleep(2)
    while ch.recv_ready(): ch.recv(65535)
    ch.send("terminal length 0\n")
    time.sleep(1)
    while ch.recv_ready(): ch.recv(65535)
    return client, ch


def cmd(ch, c, timeout=60):
    ch.send(c + "\n")
    out = ""
    start = time.time()
    while time.time() - start < timeout:
        if ch.recv_ready():
            chunk = ch.recv(65535).decode('utf-8', errors='ignore')
            out += chunk
            if "-- More --" in chunk:
                ch.send(" ")
                continue
            if re.search(r'[#>]\s*$', out.rstrip()):
                break
        else:
            time.sleep(0.05)
    return re.sub(r'\x1b\[[0-9;]*m', '', out)


def get_lldp(ch):
    """Get LLDP neighbors as dict {local_if: {neighbor, remote_if}}"""
    out = cmd(ch, "show lldp neighbors")
    neighbors = {}
    for line in out.split("\n"):
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4 and parts[1] and re.match(r'ge\d+', parts[1]):
                neighbors[parts[1]] = {"neighbor": parts[2], "remote_if": parts[3]}
    return neighbors


dnaas = load_dnaas()
print(f"DNAAS table: {len(dnaas)} entries\n", flush=True)

print("="*60, flush=True)
print("NETWORK PATH DISCOVERY: PE-1 to PE-2", flush=True)
print("="*60, flush=True)

# Step 1: PE-1 neighbors
print("\n[PE-1]", flush=True)
pe1_client, pe1_ch = connect(PE1_IP, PE_USER, PE_PASS, "PE-1")
pe1_lldp = get_lldp(pe1_ch)
pe1_client.close()

pe1_dnaas = []
for iface, info in pe1_lldp.items():
    if info['neighbor']:
        pe1_dnaas.append((iface, info['neighbor'], info['remote_if']))
        print(f"  {iface} --> {info['neighbor']}:{info['remote_if']}", flush=True)

if not pe1_dnaas:
    print("  No LLDP neighbors found on PE-1!", flush=True)
    print("  (Interfaces may not be connected)", flush=True)

# Step 2: PE-2 neighbors
print("\n[PE-2]", flush=True)
pe2_client, pe2_ch = connect(PE2_IP, PE_USER, PE_PASS, "PE-2")
pe2_lldp = get_lldp(pe2_ch)
pe2_client.close()

pe2_dnaas = []
for iface, info in pe2_lldp.items():
    if info['neighbor']:
        pe2_dnaas.append((iface, info['neighbor'], info['remote_if']))
        print(f"  {iface} --> {info['neighbor']}:{info['remote_if']}", flush=True)

# Step 3: Trace DNAAS path
print("\n[DNAAS FABRIC PATH]", flush=True)

# PE-2 is connected to DNAAS-LEAF-B15
if pe2_dnaas:
    leaf_name = pe2_dnaas[0][1].lower()
    if leaf_name in dnaas:
        leaf_ip = dnaas[leaf_name]
        print(f"\n  DNAAS-LEAF-B15:", flush=True)
        leaf_client, leaf_ch = connect(leaf_ip, DNAAS_USER, DNAAS_PASS, "DNAAS-LEAF-B15")
        leaf_lldp = get_lldp(leaf_ch)
        
        # Show spine connections
        for iface, info in leaf_lldp.items():
            if info['neighbor'] and 'spine' in info['neighbor'].lower():
                print(f"    {iface} --> {info['neighbor']}:{info['remote_if']} (SPINE)", flush=True)
        
        leaf_client.close()

# Check known DNAAS connected to PE-1 area
print("\n  Checking DNAAS-LEAF-A01 (PE-1 area):", flush=True)
a01_ip = dnaas.get("fdnaas-leaf-a01") or dnaas.get("dnaas-leaf-a01")
if a01_ip:
    a01_client, a01_ch = connect(a01_ip, DNAAS_USER, DNAAS_PASS, "DNAAS-LEAF-A01")
    a01_lldp = get_lldp(a01_ch)
    
    for iface, info in a01_lldp.items():
        if info['neighbor']:
            ntype = ""
            if 'spine' in info['neighbor'].lower():
                ntype = "(SPINE)"
            elif 'pe' in info['neighbor'].lower():
                ntype = "(PE)"
            print(f"    {iface} --> {info['neighbor']}:{info['remote_if']} {ntype}", flush=True)
    
    a01_client.close()

# Summary
print("\n" + "="*60, flush=True)
print("PATH SUMMARY:", flush=True)
print("="*60, flush=True)
print(f"""
PE-1 (100.64.0.210) - hostname: b2b2b2b2
  |
  | (interfaces ge10-0/0/x - no LLDP neighbors detected)
  | (may need cabling or DNAAS LLDP config)
  |
  ?-- [DNAAS Fabric] --?
  |
  | DNAAS-LEAF-B15
  |   ge100-0/0/36-39 --> DNAAS-SPINE-B09 (fabric uplinks)
  |   ge100-0/0/6,7   --> PE-2
  |
PE-2 (100.64.0.220) - hostname: YOR_PE-2
  ge400-0/0/0 --> DNAAS-LEAF-B15:ge100-0/0/6
  ge400-0/0/2 --> DNAAS-LEAF-B15:ge100-0/0/7
""", flush=True)

print("NOTE: PE-1 shows no LLDP neighbors. This means:", flush=True)
print("  1. Cables not connected, or", flush=True)
print("  2. Far-end DNAAS doesn't have LLDP enabled, or", flush=True)
print("  3. PE-1 is on a different DNAAS leaf (not directly visible)", flush=True)
print("="*60, flush=True)










