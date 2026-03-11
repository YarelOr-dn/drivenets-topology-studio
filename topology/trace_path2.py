#!/usr/bin/env python3
"""
Trace from PE-2 backwards to find PE-1 path
"""

import paramiko
import time
import re
import openpyxl

PE_USER = "dnroot"
PE_PASS = "dnroot"
DNAAS_USER = "sisaev"
DNAAS_PASS = "Drive1234!"

PE2_IP = "100.64.0.220"

def load_dnaas_table():
    dnaas = {}
    wb = openpyxl.load_workbook("/home/dn/CURSOR/dnaas_table.xlsx")
    ws = wb.active
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[2] and row[4]:
            name = str(row[2]).strip()
            ip = str(row[4]).strip()
            dnaas[name.lower()] = ip
            short = name.split('.')[0].lower()
            dnaas[short] = ip
    return dnaas


def connect(ip, user, passwd, name=""):
    print(f"  Connecting to {name} ({ip})...", flush=True)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=passwd, timeout=30)
    ch = client.invoke_shell(width=200, height=50)
    ch.settimeout(60)
    time.sleep(2)
    while ch.recv_ready(): ch.recv(65535)
    ch.send("terminal length 0\n")
    time.sleep(1)
    while ch.recv_ready(): ch.recv(65535)
    return client, ch


def read_prompt(ch, timeout=60):
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


def cmd(ch, c, t=60):
    ch.send(c + "\n")
    return read_prompt(ch, t)


dnaas_table = load_dnaas_table()
print(f"Loaded {len(dnaas_table)} DNAAS entries\n", flush=True)

# PE-2 LLDP
print("[1] PE-2 LLDP Neighbors:", flush=True)
pe2_client, pe2_ch = connect(PE2_IP, PE_USER, PE_PASS, "PE-2")
lldp_out = cmd(pe2_ch, "show lldp neighbors")
print(lldp_out, flush=True)
pe2_client.close()

# Connect to DNAAS-LEAF-B15
dnaas_name = "dnaas-leaf-b15"
if dnaas_name in dnaas_table:
    dnaas_ip = dnaas_table[dnaas_name]
    print(f"\n[2] DNAAS-LEAF-B15 ({dnaas_ip}):", flush=True)
    
    try:
        dnaas_client, dnaas_ch = connect(dnaas_ip, DNAAS_USER, DNAAS_PASS, "DNAAS-LEAF-B15")
        
        # LLDP on this DNAAS
        print("\n  LLDP Neighbors:", flush=True)
        lldp_out = cmd(dnaas_ch, "show lldp neighbors")
        for line in lldp_out.split("\n"):
            if "|" in line and ("ge" in line.lower() or "Local" in line):
                print(f"  {line}", flush=True)
        
        # Bridge domains  
        print("\n  Bridge Domains with attachments:", flush=True)
        bd_out = cmd(dnaas_ch, "show network-services bridge-domain detail", timeout=120)
        
        # Find BDs that have PE connections
        lines = bd_out.split("\n")
        current_bd = ""
        for i, line in enumerate(lines):
            if "bridge-domain" in line.lower() and "name" in line.lower():
                current_bd = line
            elif "ge400" in line or "ge100" in line:
                if current_bd:
                    print(f"\n  {current_bd}", flush=True)
                    current_bd = ""
                print(f"    {line.strip()}", flush=True)
        
        dnaas_client.close()
        
    except Exception as e:
        print(f"  Error: {e}", flush=True)
else:
    print(f"DNAAS-LEAF-B15 not found in table", flush=True)
    print(f"Available: {list(dnaas_table.keys())[:10]}", flush=True)










