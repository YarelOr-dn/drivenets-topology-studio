#!/usr/bin/env python3
import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("100.64.0.210", username="dnroot", password="dnroot", timeout=30)
shell = client.invoke_shell(width=200, height=50)
shell.settimeout(60)
time.sleep(1)
shell.recv(65535)

shell.send("terminal length 0\n")
time.sleep(0.5)
shell.recv(65535)

print("Running show interfaces brief...", flush=True)
shell.send("show interfaces brief\n")

output = ""
end_time = time.time() + 60
while time.time() < end_time:
    if shell.recv_ready():
        chunk = shell.recv(65535).decode('utf-8', errors='ignore')
        output += chunk
        print(".", end="", flush=True)
        if output.rstrip().endswith('#'):
            break
    else:
        time.sleep(0.2)

print("\n\nOutput:", flush=True)
print(output[:5000], flush=True)
client.close()









