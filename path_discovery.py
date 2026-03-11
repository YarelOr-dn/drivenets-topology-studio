#!/usr/bin/env python3
"""
PE-to-PE Network Path Discovery

Discovers the full network path between PE devices by:
1. Verifying/configuring LLDP on PE devices
2. Waiting for LLDP neighbors to appear
3. Tracing through DNAAS fabric via LLDP
"""

import paramiko
import time
import re
import sys
import openpyxl

# =============================================================================
# Configuration
# =============================================================================

PE_USER = "dnroot"
PE_PASS = "dnroot"
DNAAS_USER = "sisaev"
DNAAS_PASS = "Drive1234!"

# Default PE IPs
PE1_IP = "100.64.0.210"
PE2_IP = "100.64.0.220"

DNAAS_TABLE_PATH = "/home/dn/CURSOR/dnaas_table.xlsx"

# Timing
NEIGHBOR_CHECK_INTERVAL = 10  # seconds
NEIGHBOR_MAX_WAIT = 120  # seconds (2 minutes)


# =============================================================================
# DNAAS Lookup
# =============================================================================

def load_dnaas_table():
    """Load DNAAS device info from Excel file."""
    dnaas = {}
    try:
        wb = openpyxl.load_workbook(DNAAS_TABLE_PATH)
        ws = wb.active
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[2] and row[4]:  # Name and IP columns
                name = str(row[2]).strip()
                ip = str(row[4]).strip()
                # Store with multiple key variants
                dnaas[name.lower()] = ip
                dnaas[name.split('.')[0].lower()] = ip
        print(f"[INFO] Loaded {len(dnaas)} DNAAS entries from table", flush=True)
    except Exception as e:
        print(f"[WARN] Could not load DNAAS table: {e}", flush=True)
    return dnaas


# =============================================================================
# SSH Connection
# =============================================================================

def connect_device(ip, user, passwd, name="device"):
    """Connect to a device and return (client, channel)."""
    print(f"  Connecting to {name} ({ip})...", flush=True)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=passwd, timeout=30)
    
    # Enable keepalive to prevent timeout during long operations
    transport = client.get_transport()
    transport.set_keepalive(30)
    
    channel = client.invoke_shell(width=200, height=50)
    channel.settimeout(300)  # 5 minute timeout
    time.sleep(2)
    
    # Clear buffer
    while channel.recv_ready():
        channel.recv(65535)
    
    # Disable pager
    channel.send("terminal length 0\n")
    time.sleep(1)
    while channel.recv_ready():
        channel.recv(65535)
    
    return client, channel


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
                channel.send(" ")
                time.sleep(0.2)
                continue
            
            # Check for prompts
            stripped = output.rstrip()
            if re.search(r'[A-Za-z0-9_-]+(\(cfg[^)]*\))?[#>]\s*$', stripped):
                break
        else:
            time.sleep(0.05)
    
    # Strip ANSI codes
    return re.sub(r'\x1b\[[0-9;]*m', '', output)


def send_cmd(channel, cmd, timeout=60):
    """Send command and wait for prompt."""
    channel.send(cmd + "\n")
    return read_until_prompt(channel, timeout)


# =============================================================================
# LLDP Functions
# =============================================================================

def check_lldp_config(channel):
    """
    Check if LLDP is configured on the device.
    Returns (is_configured, interface_count)
    """
    output = send_cmd(channel, "show configuration protocols lldp", timeout=30)
    
    # Check if LLDP section exists and has interfaces
    has_lldp = "protocols" in output and "lldp" in output
    
    # Count configured interfaces
    interface_pattern = r'interface\s+(ge\d+-\d+/\d+/\d+)'
    interfaces = re.findall(interface_pattern, output)
    
    return has_lldp and len(interfaces) > 0, len(interfaces)


def get_physical_interfaces(channel):
    """Get list of physical interfaces from show interfaces."""
    print("  Getting physical interfaces...", flush=True)
    output = send_cmd(channel, "show interfaces", timeout=180)
    
    # Parse interface table
    pattern = r"\|\s*(ge\d+-\d+/\d+/\d+)\s*\|\s*(enabled|disabled)\s*\|\s*(\S+)\s*\|"
    interfaces = []
    
    for match in re.finditer(pattern, output):
        iface_name = match.group(1)
        admin_state = match.group(2)
        oper_state = match.group(3)
        
        # Only physical interfaces (no sub-interfaces)
        if "." not in iface_name:
            interfaces.append({
                "name": iface_name,
                "admin": admin_state,
                "oper": oper_state
            })
    
    print(f"  Found {len(interfaces)} physical interfaces", flush=True)
    return interfaces


def push_lldp_config(channel, interfaces):
    """
    Push LLDP configuration for all interfaces via direct terminal.
    Uses fast batch sending without waiting for each prompt.
    """
    print(f"  Pushing LLDP config for {len(interfaces)} interfaces...", flush=True)
    
    # Enter config mode
    send_cmd(channel, "configure", timeout=10)
    send_cmd(channel, "terminal length 0", timeout=5)
    
    # Enable interfaces that are disabled - batch send
    disabled_ifs = [i for i in interfaces if i["admin"] != "enabled"]
    if disabled_ifs:
        channel.send("interfaces\n")
        time.sleep(0.1)
        for iface in disabled_ifs:
            channel.send(f"{iface['name']}\n")
            time.sleep(0.05)
            channel.send("admin-state enabled\n")
            time.sleep(0.05)
            channel.send("exit\n")
            time.sleep(0.05)
        channel.send("exit\n")
        time.sleep(1)
        # Clear buffer
        while channel.recv_ready():
            channel.recv(65535)
        print(f"    Enabled {len(disabled_ifs)} interfaces", flush=True)
    
    # Configure LLDP - batch send
    channel.send("protocols\n")
    time.sleep(0.1)
    channel.send("lldp\n")
    time.sleep(0.1)
    channel.send("admin-state enabled\n")
    time.sleep(0.1)
    
    # Send all interface configs fast
    for i, iface in enumerate(interfaces):
        channel.send(f"interface {iface['name']}\n")
        time.sleep(0.02)
        channel.send("exit\n")
        time.sleep(0.02)
        # Progress every 50 interfaces
        if (i + 1) % 50 == 0:
            print(f"    Configured {i + 1}/{len(interfaces)} interfaces...", flush=True)
            time.sleep(0.5)
            while channel.recv_ready():
                channel.recv(65535)
    
    channel.send("exit\n")  # exit lldp
    time.sleep(0.1)
    channel.send("exit\n")  # exit protocols
    time.sleep(1)
    
    # Clear buffer
    while channel.recv_ready():
        channel.recv(65535)
    
    print(f"    LLDP configured for all {len(interfaces)} interfaces", flush=True)
    
    # Commit
    print("  Committing...", flush=True)
    output = send_cmd(channel, "commit", timeout=180)
    
    if "succeeded" in output.lower():
        print("    Commit successful!", flush=True)
        success = True
    elif "not applicable" in output.lower():
        print("    No changes to commit (already configured)", flush=True)
        success = True
    elif "error" in output.lower():
        print(f"    Commit error: {output[-200:]}", flush=True)
        success = False
    else:
        print("    Commit completed", flush=True)
        success = True
    
    # Exit config mode
    send_cmd(channel, "end", timeout=10)
    
    return success


def get_lldp_neighbors(channel):
    """
    Get LLDP neighbors as a list of dicts.
    Returns: [{"local_if": str, "neighbor": str, "remote_if": str}, ...]
    """
    output = send_cmd(channel, "show lldp neighbors", timeout=60)
    neighbors = []
    
    for line in output.split("\n"):
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4 and parts[1] and re.match(r'ge\d+', parts[1]):
                neighbor_name = parts[2] if len(parts) > 2 else ""
                remote_if = parts[3] if len(parts) > 3 else ""
                
                if neighbor_name:  # Only include entries with actual neighbors
                    neighbors.append({
                        "local_if": parts[1],
                        "neighbor": neighbor_name,
                        "remote_if": remote_if
                    })
    
    return neighbors


def wait_for_neighbors(channel, max_wait=NEIGHBOR_MAX_WAIT, interval=NEIGHBOR_CHECK_INTERVAL):
    """
    Wait for LLDP neighbors to appear.
    Retries every interval seconds up to max_wait.
    Returns list of neighbors when found, or empty list on timeout.
    """
    start_time = time.time()
    attempt = 0
    
    while time.time() - start_time < max_wait:
        attempt += 1
        elapsed = int(time.time() - start_time)
        print(f"  Checking for neighbors (attempt {attempt}, {elapsed}s elapsed)...", flush=True)
        
        neighbors = get_lldp_neighbors(channel)
        
        if neighbors:
            print(f"    Found {len(neighbors)} neighbors!", flush=True)
            return neighbors
        
        print(f"    No neighbors yet, waiting {interval}s...", flush=True)
        time.sleep(interval)
    
    print(f"  Timeout after {max_wait}s, no neighbors found", flush=True)
    return []


# =============================================================================
# Path Tracing
# =============================================================================

def trace_path(source_neighbors, dest_ip, dest_name, dnaas_table):
    """
    Trace path through DNAAS fabric from source neighbors to destination PE.
    Returns list of path hops.
    """
    path = []
    visited = set()
    
    # Find DNAAS devices in source neighbors
    dnaas_to_check = []
    for n in source_neighbors:
        neighbor_lower = n['neighbor'].lower()
        for dnaas_name, dnaas_ip in dnaas_table.items():
            if dnaas_name in neighbor_lower or neighbor_lower.startswith(dnaas_name.split('-')[0]):
                if dnaas_ip not in visited:
                    dnaas_to_check.append({
                        "name": n['neighbor'],
                        "ip": dnaas_ip,
                        "from_if": n['local_if'],
                        "to_if": n['remote_if']
                    })
                    visited.add(dnaas_ip)
                break
    
    # Trace through DNAAS fabric
    for dnaas in dnaas_to_check:
        print(f"\n  Tracing through {dnaas['name']}...", flush=True)
        
        try:
            client, channel = connect_device(
                dnaas['ip'], DNAAS_USER, DNAAS_PASS, dnaas['name']
            )
            
            neighbors = get_lldp_neighbors(channel)
            
            hop = {
                "device": dnaas['name'],
                "from_if": dnaas['to_if'],
                "connections": []
            }
            
            # Check each neighbor
            for n in neighbors:
                conn = {
                    "local_if": n['local_if'],
                    "neighbor": n['neighbor'],
                    "remote_if": n['remote_if'],
                    "type": "unknown"
                }
                
                # Classify connection
                neighbor_lower = n['neighbor'].lower()
                if 'spine' in neighbor_lower:
                    conn['type'] = "spine"
                elif 'leaf' in neighbor_lower:
                    conn['type'] = "leaf"
                elif 'pe' in neighbor_lower:
                    conn['type'] = "pe"
                    # Check if this is our destination
                    if dest_name.lower() in neighbor_lower:
                        conn['type'] = "dest_pe"
                
                hop['connections'].append(conn)
            
            path.append(hop)
            client.close()
            
        except Exception as e:
            print(f"    Error connecting to {dnaas['name']}: {e}", flush=True)
    
    return path


# =============================================================================
# Output Generation
# =============================================================================

def generate_output(source_name, source_ip, source_neighbors, 
                   dest_name, dest_ip, dest_neighbors, fabric_path):
    """Generate both simple and detailed path output."""
    
    print("\n" + "=" * 60, flush=True)
    print("SIMPLE PATH:", flush=True)
    print("=" * 60, flush=True)
    
    # Build simple path
    simple_path = [source_name]
    
    for hop in fabric_path:
        simple_path.append(hop['device'])
        # Add spines in path
        for conn in hop['connections']:
            if conn['type'] == 'spine' and conn['neighbor'] not in simple_path:
                simple_path.append(conn['neighbor'])
    
    # Add destination PE's DNAAS connections
    for n in dest_neighbors:
        if n['neighbor'] and n['neighbor'] not in simple_path:
            simple_path.append(n['neighbor'])
    
    simple_path.append(dest_name)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_path = []
    for item in simple_path:
        if item not in seen:
            seen.add(item)
            unique_path.append(item)
    
    print(" -> ".join(unique_path), flush=True)
    
    print("\n" + "=" * 60, flush=True)
    print("DETAILED PATH:", flush=True)
    print("=" * 60, flush=True)
    
    # Source PE
    print(f"\n{source_name} ({source_ip})", flush=True)
    for n in source_neighbors:
        print(f"  {n['local_if']} --> {n['neighbor']}:{n['remote_if']}", flush=True)
    
    # DNAAS fabric
    for hop in fabric_path:
        print(f"\n{hop['device']}", flush=True)
        
        # Show spine connections
        for conn in hop['connections']:
            if conn['type'] in ('spine', 'dest_pe', 'pe'):
                print(f"  {conn['local_if']} --> {conn['neighbor']}:{conn['remote_if']} ({conn['type'].upper()})", flush=True)
    
    # Destination PE
    print(f"\n{dest_name} ({dest_ip})", flush=True)
    for n in dest_neighbors:
        print(f"  {n['local_if']} <-- {n['neighbor']}:{n['remote_if']}", flush=True)
    
    print("\n" + "=" * 60, flush=True)


# =============================================================================
# Main
# =============================================================================

def discover_path(source_ip, source_name, dest_ip, dest_name):
    """Main path discovery function."""
    
    print("=" * 60, flush=True)
    print(f"PATH DISCOVERY: {source_name} to {dest_name}", flush=True)
    print("=" * 60, flush=True)
    
    # Load DNAAS table
    dnaas_table = load_dnaas_table()
    
    # =========================================================================
    # Process Source PE
    # =========================================================================
    print(f"\n[1] Processing {source_name} ({source_ip})", flush=True)
    
    source_client, source_channel = connect_device(source_ip, PE_USER, PE_PASS, source_name)
    
    # Check LLDP config
    lldp_configured, iface_count = check_lldp_config(source_channel)
    
    if lldp_configured:
        print(f"  LLDP already configured ({iface_count} interfaces)", flush=True)
    else:
        print("  LLDP not configured, setting up...", flush=True)
        interfaces = get_physical_interfaces(source_channel)
        push_lldp_config(source_channel, interfaces)
    
    # Wait for neighbors
    print("\n  Waiting for LLDP neighbors...", flush=True)
    source_neighbors = wait_for_neighbors(source_channel)
    
    source_client.close()
    
    # =========================================================================
    # Process Destination PE
    # =========================================================================
    print(f"\n[2] Processing {dest_name} ({dest_ip})", flush=True)
    
    dest_client, dest_channel = connect_device(dest_ip, PE_USER, PE_PASS, dest_name)
    
    # Check LLDP config
    lldp_configured, iface_count = check_lldp_config(dest_channel)
    
    if lldp_configured:
        print(f"  LLDP already configured ({iface_count} interfaces)", flush=True)
    else:
        print("  LLDP not configured, setting up...", flush=True)
        interfaces = get_physical_interfaces(dest_channel)
        push_lldp_config(dest_channel, interfaces)
    
    # Wait for neighbors
    print("\n  Waiting for LLDP neighbors...", flush=True)
    dest_neighbors = wait_for_neighbors(dest_channel)
    
    dest_client.close()
    
    # =========================================================================
    # Trace Fabric Path
    # =========================================================================
    print(f"\n[3] Tracing DNAAS fabric path", flush=True)
    
    fabric_path = trace_path(source_neighbors, dest_ip, dest_name, dnaas_table)
    
    # =========================================================================
    # Generate Output
    # =========================================================================
    print(f"\n[4] Generating path report", flush=True)
    
    generate_output(
        source_name, source_ip, source_neighbors,
        dest_name, dest_ip, dest_neighbors,
        fabric_path
    )
    
    print("\nPath discovery complete!", flush=True)


def main():
    """Entry point."""
    # Parse arguments
    if len(sys.argv) >= 3:
        source_ip = sys.argv[1]
        dest_ip = sys.argv[2]
        source_name = sys.argv[3] if len(sys.argv) > 3 else "PE-1"
        dest_name = sys.argv[4] if len(sys.argv) > 4 else "PE-2"
    else:
        # Default: PE-1 to PE-2
        source_ip = PE1_IP
        dest_ip = PE2_IP
        source_name = "PE-1"
        dest_name = "PE-2"
    
    discover_path(source_ip, source_name, dest_ip, dest_name)


if __name__ == "__main__":
    main()

