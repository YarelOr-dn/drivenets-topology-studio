#!/usr/bin/env python3
import paramiko
import time

PE4_IP = "100.64.7.197"
PE4_USER = "dnroot"
PE4_PASS = "dnroot"

def ssh_cli(host, user, password, commands, wait=2.0):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=10)
    chan = client.invoke_shell(width=250, height=50)
    time.sleep(2)
    chan.recv(65536)

    for cmd in commands:
        chan.send(cmd + '\n')
        time.sleep(wait)

    output = ""
    while chan.recv_ready():
        output += chan.recv(65536).decode('utf-8', errors='replace')
    time.sleep(0.5)
    while chan.recv_ready():
        output += chan.recv(65536).decode('utf-8', errors='replace')

    chan.close()
    client.close()
    return output

out_file = "/home/dn/CURSOR/pe4_query_result.txt"
results = []

print("Query 1: VRF config (ALPHA + ZULU neighbors)")
try:
    o = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
        "show config network-services vrf | no-more",
    ], wait=3)
    results.append(("VRF CONFIG", o))
    print(f"  Got {len(o)} chars")
except Exception as e:
    results.append(("VRF CONFIG", f"ERROR: {e}"))
    print(f"  ERROR: {e}")

print("Query 2: Interface config (sub-interfaces)")
try:
    o = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
        "show interfaces | no-more",
    ], wait=3)
    results.append(("INTERFACES", o))
    print(f"  Got {len(o)} chars")
except Exception as e:
    results.append(("INTERFACES", f"ERROR: {e}"))
    print(f"  ERROR: {e}")

print("Query 3: BGP config (global neighbors)")
try:
    o = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
        "show config protocols bgp | no-more",
    ], wait=3)
    results.append(("BGP CONFIG", o))
    print(f"  Got {len(o)} chars")
except Exception as e:
    results.append(("BGP CONFIG", f"ERROR: {e}"))
    print(f"  ERROR: {e}")

print("Query 4: ge100-18 sub-interface config (DNAAS facing)")
try:
    o = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
        "show config interfaces ge100-18/0/6 | no-more",
    ], wait=3)
    results.append(("GE100-18 CONFIG", o))
    print(f"  Got {len(o)} chars")
except Exception as e:
    results.append(("GE100-18 CONFIG", f"ERROR: {e}"))
    print(f"  ERROR: {e}")

with open(out_file, 'w') as f:
    for title, content in results:
        f.write(f"\n{'='*60}\n=== {title} ===\n{'='*60}\n")
        f.write(content)
        f.write("\n")

print(f"\nAll saved to {out_file}")
