#!/usr/bin/env python3
"""
Simple Network Mapper - Enable interfaces and LLDP

1. Run 'show interfaces' 
2. Find all physical interfaces
3. Enable them (admin-state enabled)
4. Configure LLDP hierarchy
"""

import paramiko
import time
import re
import sys

def connect(ip, user="dnroot", password="dnroot"):
    """Connect to device"""
    print(f"Connecting to {ip}...", flush=True)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password, timeout=30)
    
    shell = client.invoke_shell(width=200, height=50)
    time.sleep(2)
    
    # Clear buffer and disable pager
    while shell.recv_ready():
        shell.recv(65535)
    shell.send("terminal length 0\n")
    time.sleep(1)
    while shell.recv_ready():
        shell.recv(65535)
    
    print("Connected!", flush=True)
    return client, shell


def run_command(shell, cmd, timeout=180):
    """Run command and return output"""
    while shell.recv_ready():
        shell.recv(65535)
    
    shell.send(cmd + "\n")
    time.sleep(0.5)
    
    output = ""
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        if shell.recv_ready():
            output += shell.recv(65535).decode('utf-8', errors='ignore')
            if re.search(r'[#>]\s*$', output.strip()):
                break
        else:
            time.sleep(0.1)
    
    # Clean ANSI codes
    output = re.sub(r'\x1b\[[0-9;]*m', '', output)
    return output


def get_physical_interfaces(shell):
    """Get list of physical interfaces from show interfaces"""
    print("Running 'show interfaces'...", flush=True)
    output = run_command(shell, "show interfaces", timeout=180)
    
    # Parse table: | ge400-0/0/0 | enabled/disabled | up/down | ...
    interfaces = []
    pattern = r'\|\s*(ge\d+-\d+/\d+/\d+)\s*\|\s*(enabled|disabled)\s*\|\s*(\S+)\s*\|'
    
    for match in re.finditer(pattern, output):
        name = match.group(1)
        admin = match.group(2)
        oper = match.group(3)
        # Only parent interfaces (no dot)
        if '.' not in name:
            interfaces.append({'name': name, 'admin': admin, 'oper': oper})
    
    print(f"Found {len(interfaces)} physical interfaces", flush=True)
    return interfaces


def generate_config(interfaces):
    """Generate DNOS config to enable interfaces and LLDP"""
    lines = []
    
    # Enable interfaces
    lines.append("interfaces")
    for iface in interfaces:
        if iface['admin'] != 'enabled':
            lines.append(f"  {iface['name']}")
            lines.append("    admin-state enabled")
            lines.append("  !")
    lines.append("!")
    
    # LLDP config  
    lines.append("protocols")
    lines.append("  lldp")
    lines.append("    admin-state enabled")
    for iface in interfaces:
        lines.append(f"    interface {iface['name']}")
        lines.append("    !")
    lines.append("  !")
    lines.append("!")
    
    return "\n".join(lines)


def apply_config(shell, config):
    """Apply config and commit"""
    print("Entering config mode...", flush=True)
    run_command(shell, "configure", timeout=10)
    
    print("Applying config...", flush=True)
    for line in config.split('\n'):
        if line.strip():
            run_command(shell, line.strip(), timeout=5)
    
    print("Committing...", flush=True)
    output = run_command(shell, "commit", timeout=120)
    
    if "ERROR" in output:
        print(f"Commit error: {output}", flush=True)
        return False
    
    run_command(shell, "exit", timeout=5)
    print("Config applied!", flush=True)
    return True


def main(ip):
    client, shell = connect(ip)
    
    # Get interfaces
    interfaces = get_physical_interfaces(shell)
    for iface in interfaces[:5]:
        print(f"  {iface['name']}: admin={iface['admin']}, oper={iface['oper']}", flush=True)
    if len(interfaces) > 5:
        print(f"  ... and {len(interfaces) - 5} more", flush=True)
    
    # Generate config
    config = generate_config(interfaces)
    print("\nGenerated config:", flush=True)
    print(config, flush=True)
    
    # Ask to apply
    print("\nApply this config? (y/n): ", end="", flush=True)
    answer = input().strip().lower()
    
    if answer == 'y':
        apply_config(shell, config)
        
        # Wait and check LLDP
        print("\nWaiting 10s for LLDP...", flush=True)
        time.sleep(10)
        
        output = run_command(shell, "show lldp neighbors", timeout=30)
        print("\nLLDP Neighbors:", flush=True)
        print(output, flush=True)
    
    client.close()
    print("Done!", flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_mapper.py <PE_IP>")
        sys.exit(1)
    
    main(sys.argv[1])











