#!/usr/bin/env python3
"""
Full path trace from PE-2 through DNAAS fabric
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
        match = re.match(r'\|\s*([\w\-/\.]+)\s*\|\s*(\S+)\s*\|\s*([\w\-/\.]+)\s*\|\s*(\d+)', line)
        if match:
            local_if, neighbor, remote_if, ttl = match.groups()
            neighbors.append({
                'local_if': local_if,
                'neighbor': neighbor,
                'remote_if': remote_if
            })
    return neighbors

print("="*70, flush=True)
print("FULL PATH TRACE: PE-2 --> DNAAS --> ?", flush=True)
print("="*70, flush=True)

# Collect all connections
topology = {}

# Step 1: PE-2
print("\n[1] PE-2 (100.64.0.220):", flush=True)
c, s = connect("100.64.0.220", PE_USER, PE_PASS, "PE-2")
neighbors = get_lldp_neighbors(s)
topology["PE-2"] = neighbors
for n in neighbors:
    print(f"    {n['local_if']} --> {n['neighbor']}:{n['remote_if']}", flush=True)
c.close()

# Step 2: DNAAS-LEAF-B15
print("\n[2] DNAAS-LEAF-B15 (100.64.101.6):", flush=True)
c, s = connect("100.64.101.6", DNAAS_USER, DNAAS_PASS, "DNAAS-LEAF-B15")
neighbors = get_lldp_neighbors(s)
topology["DNAAS-LEAF-B15"] = neighbors
# Group by type
spines = [n for n in neighbors if 'SPINE' in n['neighbor'].upper()]
pes = [n for n in neighbors if 'PE' in n['neighbor'].upper() or 'SPINE' not in n['neighbor'].upper()]
print("  Connected to PEs/Devices:", flush=True)
for n in pes:
    if 'SPINE' not in n['neighbor'].upper():
        print(f"    {n['local_if']} --> {n['neighbor']}:{n['remote_if']}", flush=True)
print("  Connected to Spines:", flush=True)
for n in spines:
    print(f"    {n['local_if']} --> {n['neighbor']}:{n['remote_if']}", flush=True)
c.close()

# Step 3: DNAAS-SPINE-B09
print("\n[3] DNAAS-SPINE-B09 (100.64.100.12):", flush=True)
c, s = connect("100.64.100.12", DNAAS_USER, DNAAS_PASS, "DNAAS-SPINE-B09")
neighbors = get_lldp_neighbors(s)
topology["DNAAS-SPINE-B09"] = neighbors
# Group by leaf
leaves = {}
for n in neighbors:
    if n['neighbor'] not in leaves:
        leaves[n['neighbor']] = []
    leaves[n['neighbor']].append(n)
print("  Connected Leaves:", flush=True)
for leaf, conns in sorted(leaves.items()):
    ports = ', '.join([c['local_if'] for c in conns])
    print(f"    {leaf}: {len(conns)} links ({ports})", flush=True)
c.close()

# Summary
print("\n" + "="*70, flush=True)
print("TOPOLOGY SUMMARY", flush=True)
print("="*70, flush=True)
print("""
Physical Topology from PE-2:

  PE-2 (YOR_PE-2)
    |
    +-- ge400-0/0/0 --> DNAAS-LEAF-B15:ge100-0/0/6
    +-- ge400-0/0/2 --> DNAAS-LEAF-B15:ge100-0/0/7
    
  DNAAS-LEAF-B15 (Leaf in DNAAS fabric)
    |
    +-- ge100-0/0/36-39 --> DNAAS-SPINE-B09 (4 links)
    |
    +-- Other PEs attached to this leaf:
""", flush=True)

# List other devices on LEAF-B15
for n in topology.get("DNAAS-LEAF-B15", []):
    if n['neighbor'] not in ['YOR_PE-2', 'DNAAS-SPINE-B09']:
        print(f"        - {n['neighbor']} via {n['local_if']}", flush=True)

print("""
  DNAAS-SPINE-B09 (Spine in DNAAS fabric)
    |
    +-- Connected to multiple Leaves:""", flush=True)

for leaf in sorted(leaves.keys()):
    print(f"        - {leaf} ({len(leaves[leaf])} links)", flush=True)

print("\n" + "="*70, flush=True)









