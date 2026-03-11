#!/usr/bin/env python3
import paramiko
import time
import re

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("100.64.0.210", username="dnroot", password="dnroot", timeout=30)
shell = client.invoke_shell(width=200, height=50)
shell.settimeout(180)
time.sleep(1)
shell.recv(65535)

print("Running 'show interfaces | no-more'...", flush=True)
shell.send("show interfaces | no-more\n")

output = ""
end_time = time.time() + 60
while time.time() < end_time:
    if shell.recv_ready():
        chunk = shell.recv(65535).decode('utf-8', errors='ignore')
        output += chunk
        lines = output.rstrip().split('\n')
        if lines and lines[-1].endswith('#'):
            break
    else:
        time.sleep(0.2)

# Find all interfaces that are UP (operational)
print("\n=== INTERFACES THAT ARE OPERATIONALLY UP ===", flush=True)
for line in output.split('\n'):
    # Match: | interface | admin | oper | ...
    # Look for 'up' in the operational column (not 'down' or 'not-present')
    match = re.match(r'\|\s*([\w\-/\.]+)\s*\|\s*(\w+)\s*\|\s*(\w+)', line)
    if match:
        iface, admin, oper = match.groups()
        if oper.lower() == 'up':
            print(f"  {iface}: admin={admin}, oper={oper}", flush=True)

# Also check what's in the running config
print("\n=== CHECKING LLDP CONFIG ===", flush=True)
shell.send("show run protocols lldp | no-more\n")
time.sleep(2)
lldp_output = ""
while shell.recv_ready():
    lldp_output += shell.recv(65535).decode('utf-8', errors='ignore')
print(lldp_output, flush=True)

client.close()









