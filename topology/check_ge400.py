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
end_time = time.time() + 180
while time.time() < end_time:
    if shell.recv_ready():
        chunk = shell.recv(65535).decode('utf-8', errors='ignore')
        output += chunk
        lines = output.rstrip().split('\n')
        if lines and lines[-1].endswith('#'):
            break
    else:
        time.sleep(0.2)

print(f"Total lines: {len(output.split(chr(10)))}", flush=True)

# Find all ge* lines
print("\n=== Looking for ge400 ===", flush=True)
for line in output.split('\n'):
    if 'ge400' in line or 'ge400' in line.lower():
        print(line, flush=True)

# Also show the last 30 lines to see if there's more
print("\n=== LAST 30 LINES ===", flush=True)
for line in output.split('\n')[-30:]:
    print(line, flush=True)

# Count all interfaces by prefix
print("\n=== INTERFACE COUNTS ===", flush=True)
prefixes = {}
for line in output.split('\n'):
    match = re.match(r'\|\s*(ge\d+)-', line)
    if match:
        prefix = match.group(1)
        prefixes[prefix] = prefixes.get(prefix, 0) + 1
for prefix, count in sorted(prefixes.items()):
    print(f"  {prefix}: {count} interfaces", flush=True)

client.close()









