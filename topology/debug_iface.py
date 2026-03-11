#!/usr/bin/env python3
import paramiko
import time

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
dots = 0
while time.time() < end_time:
    if shell.recv_ready():
        chunk = shell.recv(65535).decode('utf-8', errors='ignore')
        output += chunk
        dots += 1
        if dots % 10 == 0:
            print(".", end="", flush=True)
        lines = output.rstrip().split('\n')
        if lines and lines[-1].endswith('#'):
            break
    else:
        time.sleep(0.2)

print(f"\n\nTotal output length: {len(output)} chars, {len(output.split(chr(10)))} lines", flush=True)
print("\n=== FIRST 100 LINES ===", flush=True)
for i, line in enumerate(output.split('\n')[:100]):
    print(f"{i:3d}: [{line}]", flush=True)

# Find lines with 'ge' in them
print("\n=== LINES WITH 'ge' ===", flush=True)
for i, line in enumerate(output.split('\n')):
    if 'ge' in line.lower():
        print(f"{i:3d}: [{line}]", flush=True)

client.close()









