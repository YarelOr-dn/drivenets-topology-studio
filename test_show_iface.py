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

shell.send("terminal length 0\n")
time.sleep(0.5)
shell.recv(65535)

print("Running show interfaces...")
shell.send("show interfaces\n")

output = ""
end_time = time.time() + 180
while time.time() < end_time:
    if shell.recv_ready():
        chunk = shell.recv(65535).decode('utf-8', errors='ignore')
        output += chunk
        if output.rstrip().endswith('#'):
            break
    else:
        time.sleep(0.2)

# Print first 100 lines to see format
lines = output.split('\n')
for i, line in enumerate(lines[:100]):
    print(f"{i:3d}: {line}")

client.close()










