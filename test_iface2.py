#!/usr/bin/env python3
import paramiko
import time
import re

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("100.64.0.210", username="dnroot", password="dnroot", timeout=30)
shell = client.invoke_shell(width=200, height=50)
shell.settimeout(120)
time.sleep(1)
shell.recv(65535)

shell.send("terminal length 0\n")
time.sleep(0.5)
shell.recv(65535)

# Try different commands to find interface list
commands = [
    "show interfaces | include 'Interface\\|ge'",
    "show interfaces summary",
    "show configuration interfaces",
]

for cmd in commands:
    print(f"\n{'='*60}", flush=True)
    print(f"Trying: {cmd}", flush=True)
    print("="*60, flush=True)
    
    shell.send(cmd + "\n")
    output = ""
    end_time = time.time() + 30
    while time.time() < end_time:
        if shell.recv_ready():
            chunk = shell.recv(65535).decode('utf-8', errors='ignore')
            output += chunk
            if output.rstrip().endswith('#'):
                break
        else:
            time.sleep(0.2)
    
    print(output[:3000], flush=True)
    
    if "ERROR" in output:
        print("  -> Failed", flush=True)
    else:
        print("  -> Might work!", flush=True)
        break

client.close()









