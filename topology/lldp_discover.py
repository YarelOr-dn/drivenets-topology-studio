#!/usr/bin/env python3
"""
LLDP Discovery Script
1. Get all physical interfaces that are OPERATIONALLY UP
2. Push LLDP config only for UP interfaces
3. Wait 30 seconds
4. Show LLDP neighbors
"""

import paramiko
import time
import re
import sys

# Device credentials
PE_CREDS = {"user": "dnroot", "pass": "dnroot"}

def create_ssh(ip):
    """Create SSH connection and return shell channel"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=PE_CREDS["user"], password=PE_CREDS["pass"], timeout=30)
    shell = client.invoke_shell(width=200, height=50)
    shell.settimeout(180)
    time.sleep(1)
    shell.recv(65535)  # Clear banner
    return client, shell

def send_cmd(shell, cmd, timeout=180):
    """Send command and wait for output"""
    shell.send(cmd + "\n")
    time.sleep(0.3)
    
    output = ""
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        if shell.recv_ready():
            chunk = shell.recv(65535).decode('utf-8', errors='ignore')
            output += chunk
            lines = output.rstrip().split('\n')
            if lines and (lines[-1].endswith('#') or lines[-1].endswith('>')):
                break
        else:
            time.sleep(0.2)
    
    return output

def get_up_physical_interfaces(shell):
    """Get physical ge* interfaces that are OPERATIONALLY UP (no subinterfaces)"""
    print("  Running 'show interfaces | no-more'...", flush=True)
    output = send_cmd(shell, "show interfaces | no-more", timeout=60)
    
    # Parse interface table:
    # | ge400-0/0/0  | enabled  | up  | ...
    interfaces = []
    for line in output.split('\n'):
        # Match: | interface | admin | oper | ...
        match = re.match(r'\|\s*(ge\d+-\d+/\d+/\d+)\s*\|\s*(\w+)\s*\|\s*(\w+)', line)
        if match:
            iface, admin, oper = match.groups()
            # Only physical (no dot) AND operationally UP
            if '.' not in iface and oper.lower() == 'up':
                interfaces.append(iface)
    
    return sorted(interfaces)

def push_lldp_config(shell, interfaces):
    """Push LLDP config for interfaces"""
    if not interfaces:
        print("  No interfaces to configure!", flush=True)
        return
    
    print(f"  Pushing LLDP config for {len(interfaces)} interfaces...", flush=True)
    
    # Build config block
    config_lines = [
        "protocols lldp",
        "  admin-state enabled",
    ]
    for iface in interfaces:
        config_lines.append(f"  interface {iface}")
    config_lines.append("!")
    config_lines.append("!")
    
    # Enter config mode
    print("  Entering config mode...", flush=True)
    output = send_cmd(shell, "configure", timeout=10)
    
    # Send all config lines
    for line in config_lines:
        shell.send(line + "\n")
        time.sleep(0.05)
    
    time.sleep(1)
    shell.recv(65535)  # Clear buffer
    
    # Commit
    print("  Committing...", flush=True)
    output = send_cmd(shell, "commit", timeout=60)
    
    if "succeeded" in output.lower():
        print("  Commit succeeded!", flush=True)
    elif "no configuration changes" in output.lower():
        print("  LLDP already configured!", flush=True)
    elif "error" in output.lower() or "failed" in output.lower():
        print(f"  Commit issue: {output[-500:]}", flush=True)
    else:
        print(f"  Commit done.", flush=True)
    
    # Exit config mode
    send_cmd(shell, "end", timeout=10)

def show_lldp_neighbors(shell):
    """Show LLDP neighbors"""
    print("  Running 'show lldp neighbors | no-more'...", flush=True)
    output = send_cmd(shell, "show lldp neighbors | no-more", timeout=30)
    return output

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 lldp_discover.py <PE_IP> [PE_NAME]")
        print("Example: python3 lldp_discover.py 100.64.0.220 PE-2")
        sys.exit(1)
    
    pe_ip = sys.argv[1]
    pe_name = sys.argv[2] if len(sys.argv) > 2 else pe_ip
    
    print(f"\n{'='*60}", flush=True)
    print(f"LLDP Discovery on {pe_name} ({pe_ip})", flush=True)
    print(f"{'='*60}\n", flush=True)
    
    try:
        # Connect
        print("[1] Connecting...", flush=True)
        client, shell = create_ssh(pe_ip)
        print("  Connected!", flush=True)
        
        # Get UP physical interfaces only
        print("\n[2] Getting physical interfaces that are UP...", flush=True)
        interfaces = get_up_physical_interfaces(shell)
        
        if not interfaces:
            print("  No physical interfaces are operationally UP!", flush=True)
            print("  (Nothing connected to this device)", flush=True)
            
            # Still check for existing LLDP neighbors
            print("\n[3] Checking existing LLDP neighbors anyway...", flush=True)
            neighbors = show_lldp_neighbors(shell)
            print(neighbors, flush=True)
            client.close()
            return
        
        print(f"  Found {len(interfaces)} UP physical interfaces:", flush=True)
        for iface in interfaces:
            print(f"    - {iface}", flush=True)
        
        # Push LLDP config
        print("\n[3] Configuring LLDP...", flush=True)
        push_lldp_config(shell, interfaces)
        
        # Wait for neighbors
        print("\n[4] Waiting 30 seconds for neighbors to appear...", flush=True)
        for i in range(30, 0, -5):
            print(f"    {i}s remaining...", flush=True)
            time.sleep(5)
        
        # Show neighbors
        print("\n[5] Checking LLDP neighbors...", flush=True)
        neighbors = show_lldp_neighbors(shell)
        print("\n" + "="*60, flush=True)
        print("LLDP NEIGHBORS:", flush=True)
        print("="*60, flush=True)
        print(neighbors, flush=True)
        
        client.close()
        print("\nDone!", flush=True)
        
    except Exception as e:
        print(f"\nERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
