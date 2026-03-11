#!/usr/bin/env python3
import paramiko
import time
import re

# PE-2
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("100.64.0.220", username="dnroot", password="dnroot", timeout=30)
shell = client.invoke_shell(width=200, height=50)
shell.settimeout(180)
time.sleep(1)
shell.recv(65535)

print("=== PE-2 (100.64.0.220) ===", flush=True)

print("\nRunning 'show interfaces | no-more'...", flush=True)
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
up_count = 0
for line in output.split('\n'):
    # Match: | interface | admin | oper | ...
    match = re.match(r'\|\s*([\w\-/\.]+)\s*\|\s*(\w+)\s*\|\s*(\w+)', line)
    if match:
        iface, admin, oper = match.groups()
        if oper.lower() == 'up':
            print(f"  {iface}: admin={admin}, oper={oper}", flush=True)
            up_count += 1

print(f"\nTotal UP: {up_count}", flush=True)

# Check LLDP neighbors
print("\n=== LLDP NEIGHBORS ===", flush=True)
shell.send("show lldp neighbors | no-more\n")
time.sleep(3)
lldp_output = ""
while shell.recv_ready():
    lldp_output += shell.recv(65535).decode('utf-8', errors='ignore')
    time.sleep(0.2)
print(lldp_output[:3000], flush=True)

client.close()









