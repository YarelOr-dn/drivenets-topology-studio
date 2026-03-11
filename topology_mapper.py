#!/usr/bin/env python3
"""
Full Topology Mapper
Maps PE devices through DNAAS fabric using LLDP
"""

import paramiko
import time
import re
import sys
import openpyxl

# Credentials
PE_USER, PE_PASS = "dnroot", "dnroot"
DNAAS_USER, DNAAS_PASS = "sisaev", "Drive1234!"

# Load DNAAS table
def load_dnaas_table():
    """Load DNAAS device IPs from Excel"""
    devices = {}
    try:
        wb = openpyxl.load_workbook('/home/dn/CURSOR/dnaas_table.xlsx')
        ws = wb.active
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[2] and row[4]:  # Name and IP
                name = str(row[2]).strip()
                ip = str(row[4]).strip()
                devices[name.lower()] = {"name": name, "ip": ip}
        print(f"[INFO] Loaded {len(devices)} DNAAS devices from table", flush=True)
    except Exception as e:
        print(f"[WARN] Could not load DNAAS table: {e}", flush=True)
    return devices

DNAAS_TABLE = load_dnaas_table()

def get_dnaas_ip(name):
    """Look up DNAAS device IP by name"""
    key = name.lower().strip()
    if key in DNAAS_TABLE:
        return DNAAS_TABLE[key]["ip"]
    return None

def connect(ip, user, passwd, name="", timeout=30):
    """Create SSH connection"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=passwd, timeout=timeout)
    shell = client.invoke_shell(width=200, height=50)
    shell.settimeout(60)
    time.sleep(1)
    shell.recv(65535)
    return client, shell

def send_cmd(shell, cmd, timeout=30):
    """Send command and get output"""
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
    """Parse LLDP neighbors"""
    output = send_cmd(shell, "show lldp neighbors | no-more", timeout=30)
    neighbors = []
    for line in output.split('\n'):
        match = re.match(r'\|\s*([\w\-/\.]+)\s*\|\s*(\S+)\s*\|\s*([\w\-/\.]+)\s*\|\s*(\d+)', line)
        if match:
            local_if, neighbor, remote_if, ttl = match.groups()
            if neighbor:  # Has a neighbor
                neighbors.append({
                    'local_if': local_if,
                    'neighbor': neighbor,
                    'remote_if': remote_if
                })
    return neighbors

def is_dnaas(name):
    """Check if device is DNAAS (leaf/spine)"""
    n = name.upper()
    return 'DNAAS' in n or 'LEAF' in n or 'SPINE' in n

def is_pe(name):
    """Check if device is a PE (not DNAAS)"""
    return not is_dnaas(name)

# Topology storage
topology = {
    "devices": {},      # device_name -> {type, ip, neighbors}
    "connections": [],  # [(dev1, if1, dev2, if2)]
    "pe_devices": [],   # List of PE device names
    "dnaas_devices": [] # List of DNAAS device names
}

visited = set()

def discover_device(name, ip, user, passwd, device_type="unknown"):
    """Discover a device and its neighbors"""
    if name in visited:
        return
    visited.add(name)
    
    print(f"\n  [{device_type.upper()}] {name} ({ip})", flush=True)
    
    try:
        client, shell = connect(ip, user, passwd, name)
        neighbors = get_lldp_neighbors(shell)
        client.close()
        
        # Store device info
        topology["devices"][name] = {
            "type": device_type,
            "ip": ip,
            "neighbors": neighbors
        }
        
        if device_type == "pe":
            topology["pe_devices"].append(name)
        elif device_type == "dnaas":
            topology["dnaas_devices"].append(name)
        
        # Store connections
        for n in neighbors:
            conn = (name, n['local_if'], n['neighbor'], n['remote_if'])
            topology["connections"].append(conn)
            print(f"      {n['local_if']} --> {n['neighbor']}:{n['remote_if']}", flush=True)
        
        return neighbors
        
    except Exception as e:
        print(f"      ERROR: {e}", flush=True)
        return []

def map_topology(start_ip, start_name):
    """Map full topology starting from a PE device"""
    print("="*70, flush=True)
    print("TOPOLOGY MAPPING", flush=True)
    print("="*70, flush=True)
    
    # Queue of devices to discover: (name, ip, user, pass, type)
    queue = [(start_name, start_ip, PE_USER, PE_PASS, "pe")]
    
    while queue:
        name, ip, user, passwd, dtype = queue.pop(0)
        
        if name in visited:
            continue
        
        neighbors = discover_device(name, ip, user, passwd, dtype)
        
        if not neighbors:
            continue
        
        # Add DNAAS neighbors to queue
        for n in neighbors:
            neighbor_name = n['neighbor']
            if neighbor_name in visited:
                continue
            
            if is_dnaas(neighbor_name):
                # Look up IP from table
                neighbor_ip = get_dnaas_ip(neighbor_name)
                if neighbor_ip:
                    queue.append((neighbor_name, neighbor_ip, DNAAS_USER, DNAAS_PASS, "dnaas"))
                else:
                    print(f"      [SKIP] {neighbor_name} - IP not in DNAAS table", flush=True)

def print_topology_report():
    """Print final topology report"""
    print("\n" + "="*70, flush=True)
    print("TOPOLOGY REPORT", flush=True)
    print("="*70, flush=True)
    
    # PE Devices
    print("\n[PE DEVICES]", flush=True)
    for pe in topology["pe_devices"]:
        dev = topology["devices"].get(pe, {})
        print(f"  • {pe} ({dev.get('ip', '?')})", flush=True)
        for n in dev.get("neighbors", []):
            print(f"      └─ {n['local_if']} --> {n['neighbor']}", flush=True)
    
    # DNAAS Fabric
    print("\n[DNAAS FABRIC]", flush=True)
    
    # Spines
    spines = [d for d in topology["dnaas_devices"] if 'SPINE' in d.upper()]
    leaves = [d for d in topology["dnaas_devices"] if 'LEAF' in d.upper()]
    
    print("  Spines:", flush=True)
    for spine in spines:
        dev = topology["devices"].get(spine, {})
        # Count connected leaves
        leaf_conns = [n for n in dev.get("neighbors", []) if 'LEAF' in n['neighbor'].upper()]
        print(f"    • {spine} ({len(leaf_conns)} leaf connections)", flush=True)
    
    print("  Leaves:", flush=True)
    for leaf in leaves:
        dev = topology["devices"].get(leaf, {})
        # Find connected PEs
        pe_conns = [n for n in dev.get("neighbors", []) if is_pe(n['neighbor'])]
        spine_conns = [n for n in dev.get("neighbors", []) if 'SPINE' in n['neighbor'].upper()]
        print(f"    • {leaf} ({len(spine_conns)} spine links, {len(pe_conns)} PE connections)", flush=True)
        for pe in pe_conns:
            print(f"        └─ {pe['neighbor']}", flush=True)
    
    # All discovered PEs (including those we didn't connect to)
    print("\n[ALL DISCOVERED PE DEVICES]", flush=True)
    all_pes = set()
    for dev_name, dev_info in topology["devices"].items():
        for n in dev_info.get("neighbors", []):
            if is_pe(n['neighbor']):
                all_pes.add(n['neighbor'])
    
    for pe in sorted(all_pes):
        in_our_list = "✓" if pe in topology["pe_devices"] else " "
        print(f"  [{in_our_list}] {pe}", flush=True)
    
    # Connection summary
    print("\n[CONNECTION PATHS]", flush=True)
    for pe in topology["pe_devices"]:
        dev = topology["devices"].get(pe, {})
        for n in dev.get("neighbors", []):
            if is_dnaas(n['neighbor']):
                print(f"  {pe} --> {n['neighbor']} (via {n['local_if']})", flush=True)

def main():
    if len(sys.argv) < 2:
        # Default to PE-2
        start_ip = "100.64.0.220"
        start_name = "PE-2"
    else:
        start_ip = sys.argv[1]
        start_name = sys.argv[2] if len(sys.argv) > 2 else start_ip
    
    print(f"Starting topology mapping from {start_name} ({start_ip})", flush=True)
    
    map_topology(start_ip, start_name)
    print_topology_report()
    
    print("\n" + "="*70, flush=True)
    print("MAPPING COMPLETE", flush=True)
    print("="*70, flush=True)

if __name__ == "__main__":
    main()









