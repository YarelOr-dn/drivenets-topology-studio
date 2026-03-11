#!/usr/bin/env python3
import paramiko
import time
import sys
import json

PE4_IP = "100.64.7.197"
PE4_USER = "dnroot"
PE4_PASS = "dnroot"
BGP_AS = "1234567"
EXABGP_PEER = "100.64.6.134"

def ssh_cli(host, user, password, commands, timeout=15):
    """Send commands to DNOS CLI via interactive SSH channel."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=10)

    chan = client.invoke_shell(width=200, height=50)
    time.sleep(2)

    output = chan.recv(65536).decode('utf-8', errors='replace')

    for cmd in commands:
        chan.send(cmd + '\n')
        time.sleep(1.5)
        while chan.recv_ready():
            output += chan.recv(65536).decode('utf-8', errors='replace')

    time.sleep(1)
    while chan.recv_ready():
        output += chan.recv(65536).decode('utf-8', errors='replace')

    chan.close()
    client.close()
    return output

def main():
    out_file = "/home/dn/CURSOR/pe4_fix_result.txt"
    results = []

    print("Step 1: Show BGP summary on PE-4")
    try:
        output = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
            "show bgp summary | no-more",
            "exit"
        ])
        results.append(("BGP SUMMARY", output))
        print(output[-500:] if len(output) > 500 else output)
    except Exception as e:
        results.append(("BGP SUMMARY", f"ERROR: {e}"))
        print(f"ERROR: {e}")

    print("\nStep 2: Check ExaBGP neighbor state")
    try:
        output = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
            f"show bgp neighbor {EXABGP_PEER} | no-more",
            "exit"
        ])
        results.append(("EXABGP NEIGHBOR", output))
        print(output[-500:] if len(output) > 500 else output)
    except Exception as e:
        results.append(("EXABGP NEIGHBOR", f"ERROR: {e}"))
        print(f"ERROR: {e}")

    print("\nStep 3: Admin-disable ExaBGP neighbor")
    try:
        output = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
            "configure",
            f"protocols bgp {BGP_AS} neighbor {EXABGP_PEER} admin-state disabled",
            "commit",
            "exit",
            "exit"
        ], timeout=20)
        results.append(("ADMIN-DISABLE", output))
        print(output[-500:] if len(output) > 500 else output)
    except Exception as e:
        results.append(("ADMIN-DISABLE", f"ERROR: {e}"))
        print(f"ERROR: {e}")

    print("\nStep 4: Show VRF ALPHA BGP")
    try:
        output = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
            "show bgp instance vrf ALPHA summary | no-more",
            "exit"
        ])
        results.append(("VRF ALPHA BGP", output))
        print(output[-500:] if len(output) > 500 else output)
    except Exception as e:
        results.append(("VRF ALPHA BGP", f"ERROR: {e}"))
        print(f"ERROR: {e}")

    print("\nStep 5: Show VRF ZULU BGP")
    try:
        output = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
            "show bgp instance vrf ZULU summary | no-more",
            "exit"
        ])
        results.append(("VRF ZULU BGP", output))
        print(output[-500:] if len(output) > 500 else output)
    except Exception as e:
        results.append(("VRF ZULU BGP", f"ERROR: {e}"))
        print(f"ERROR: {e}")

    print("\nStep 6: Show bundle-100 sub-interfaces")
    try:
        output = ssh_cli(PE4_IP, PE4_USER, PE4_PASS, [
            "show interfaces bundle-100 | no-more",
            "exit"
        ])
        results.append(("BUNDLE-100 SUBIFS", output))
        print(output[-500:] if len(output) > 500 else output)
    except Exception as e:
        results.append(("BUNDLE-100 SUBIFS", f"ERROR: {e}"))
        print(f"ERROR: {e}")

    with open(out_file, 'w') as f:
        for title, content in results:
            f.write(f"=== {title} ===\n")
            f.write(content)
            f.write("\n\n")

    print(f"\nAll results saved to {out_file}")

if __name__ == "__main__":
    main()
