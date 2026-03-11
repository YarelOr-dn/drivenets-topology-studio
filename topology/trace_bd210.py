#!/usr/bin/env python3
"""
Trace Bridge Domain VLAN 210 through DNAAS fabric
"""

import paramiko
import time
import re
import openpyxl

# Credentials
PE_USER, PE_PASS = "dnroot", "dnroot"
DNAAS_USER, DNAAS_PASS = "sisaev", "Drive1234!"

# Known devices in path
DEVICES = {
    "PE-1": ("100.64.2.33", PE_USER, PE_PASS),
    "PE-2": ("100.64.0.220", PE_USER, PE_PASS),
    "LEAF-D16": ("100.64.101.123", DNAAS_USER, DNAAS_PASS),
    "LEAF-B15": ("100.64.101.6", DNAAS_USER, DNAAS_PASS),
    "SPINE-D14": ("100.64.100.129", DNAAS_USER, DNAAS_PASS),
    "SPINE-B09": ("100.64.100.12", DNAAS_USER, DNAAS_PASS),
}

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

print("="*70, flush=True)
print("TRACING BRIDGE DOMAIN / VLAN 210", flush=True)
print("="*70, flush=True)

bd_info = {}

# Check PE-1 for VLAN 210 config
print("\n[1] Checking PE-1 for VLAN 210...", flush=True)
c, s = connect(*DEVICES["PE-1"])
# Check interfaces with vlan-id 210
output = send_cmd(s, "show running-config | include vlan-id.210 | no-more", timeout=30)
if "ERROR" in output:
    # Try alternative
    output = send_cmd(s, "show run | section 210 | no-more", timeout=30)
print(f"  Config search: {output[:500]}", flush=True)

# Check for any .210 subinterfaces
output = send_cmd(s, "show interfaces | no-more", timeout=60)
for line in output.split('\n'):
    if '.210' in line or 'vlan-id 210' in line.lower():
        print(f"  Found: {line.strip()}", flush=True)
c.close()

# Check PE-2 for VLAN 210 config
print("\n[2] Checking PE-2 for VLAN 210...", flush=True)
c, s = connect(*DEVICES["PE-2"])
output = send_cmd(s, "show interfaces | no-more", timeout=60)
for line in output.split('\n'):
    if '.210' in line:
        print(f"  Found: {line.strip()}", flush=True)
c.close()

# Check LEAF-D16 for BD 210
print("\n[3] Checking DNAAS-LEAF-D16 for BD 210...", flush=True)
c, s = connect(*DEVICES["LEAF-D16"])

# Try different commands for bridge domain
cmds = [
    "show network-services bridge-domain 210 | no-more",
    "show network-services bridge-domain | include 210 | no-more",
    "show evpn | no-more",
    "show running-config network-services | include 210 | no-more",
]

for cmd in cmds:
    print(f"  Trying: {cmd[:50]}...", flush=True)
    output = send_cmd(s, cmd, timeout=30)
    if "ERROR" not in output and len(output.strip()) > 50:
        print(f"  Output: {output[:1000]}", flush=True)
        break

c.close()

# Check LEAF-B15 for BD 210
print("\n[4] Checking DNAAS-LEAF-B15 for BD 210...", flush=True)
c, s = connect(*DEVICES["LEAF-B15"])

for cmd in cmds:
    print(f"  Trying: {cmd[:50]}...", flush=True)
    output = send_cmd(s, cmd, timeout=30)
    if "ERROR" not in output and len(output.strip()) > 50:
        print(f"  Output: {output[:1000]}", flush=True)
        break

# Also check running config for 210
print("\n  Checking running config for 210...", flush=True)
output = send_cmd(s, "show run network-services | no-more", timeout=60)
if "ERROR" in output:
    output = send_cmd(s, "show running-config | no-more", timeout=120)

# Find lines with 210
lines_210 = []
in_section = False
section_lines = []
for line in output.split('\n'):
    if '210' in line:
        lines_210.append(line)
    # Track network-services sections
    if 'bridge-domain' in line.lower() and '210' in line:
        in_section = True
        section_lines = [line]
    elif in_section:
        section_lines.append(line)
        if line.strip() == '!' or line.strip() == '':
            in_section = False
            if section_lines:
                print(f"  BD Section found:", flush=True)
                for sl in section_lines[:20]:
                    print(f"    {sl}", flush=True)

if lines_210:
    print(f"\n  Lines containing '210':", flush=True)
    for line in lines_210[:20]:
        print(f"    {line}", flush=True)

c.close()

print("\n" + "="*70, flush=True)
print("BD 210 TRACE COMPLETE", flush=True)
print("="*70, flush=True)









