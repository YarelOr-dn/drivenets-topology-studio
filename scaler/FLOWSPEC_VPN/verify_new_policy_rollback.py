#!/usr/bin/env python3
"""
Test: Does new route-policy language survive delete+rollback?

SW-242121 verified that legacy route-map knobs survive.
This test checks the NEW syntax: policy ALLOW_REDIRECT_IP() in
"""
import paramiko
import time
import sys
import re

HOSTS = ["100.64.2.33", "100.64.5.56"]
USER = "dnroot"
PASS = "dnroot"
ASN = "1234567"
NEIGHBOR = "2.2.2.2"
POLICY_NAME = "ALLOW_REDIRECT_IP()"
AF = "ipv4-flowspec-vpn"

def connect():
    for host in HOSTS:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, username=USER, password=PASS, timeout=15)
            chan = client.invoke_shell(width=300, height=1000)
            time.sleep(2)
            chan.recv(65535)
            print(f"Connected to {host}")
            return client, chan
        except Exception as e:
            print(f"Failed {host}: {e}")
    sys.exit(1)

def send(chan, cmd, wait=3):
    chan.send(cmd + "\n")
    time.sleep(wait)
    out = ""
    while chan.recv_ready():
        out += chan.recv(65535).decode("utf-8", errors="replace")
        time.sleep(0.5)
    ansi_escape = re.compile(r'\x1B\[[0-9;]*[a-zA-Z]')
    clean = ansi_escape.sub('', out)
    return clean

def run_test():
    client, chan = connect()

    print("\n" + "="*60)
    print("STEP 1: Add policy ALLOW_REDIRECT_IP() in to ipv4-flowspec-vpn")
    print("="*60)
    send(chan, "configure")
    send(chan, f"protocols bgp {ASN} neighbor {NEIGHBOR} address-family {AF}")
    out = send(chan, f"policy {POLICY_NAME} in")
    print(out)
    send(chan, "top")
    out = send(chan, "commit", wait=10)
    print("COMMIT:", out)

    print("\n" + "="*60)
    print("STEP 2: Verify policy in show config (ATTACHED state)")
    print("="*60)
    send(chan, "exit")
    out = send(chan, f"show config protocols bgp | include policy", wait=5)
    print("CONFIG POLICIES:", out)

    print("\n" + "="*60)
    print("STEP 3: Verify in show bgp (vtysh reflection)")
    print("="*60)
    out = send(chan, f"show bgp ipv4 flowspec-vpn neighbors {NEIGHBOR} | include policy", wait=5)
    print("BGP POLICY:", out)
    out = send(chan, f"show bgp ipv4 flowspec-vpn neighbors {NEIGHBOR} | include route-map", wait=5)
    print("BGP ROUTE-MAP:", out)
    out = send(chan, f"show bgp ipv4 flowspec-vpn neighbors {NEIGHBOR} | include REDIRECT", wait=5)
    print("BGP REDIRECT:", out)

    print("\n" + "="*60)
    print("STEP 4: Delete neighbor, commit")
    print("="*60)
    send(chan, "configure")
    send(chan, f"no protocols bgp {ASN} neighbor {NEIGHBOR}")
    out = send(chan, "commit", wait=15)
    print("DELETE COMMIT:", out)

    print("\n" + "="*60)
    print("STEP 5: Verify neighbor is gone")
    print("="*60)
    send(chan, "exit")
    out = send(chan, f"show bgp ipv4 flowspec-vpn summary | include {NEIGHBOR}", wait=5)
    print("NEIGHBOR GONE?:", out)

    print("\n" + "="*60)
    print("STEP 6: Rollback 1 (restore previous config), commit")
    print("="*60)
    send(chan, "configure")
    send(chan, "rollback 1")
    out = send(chan, "commit", wait=15)
    print("ROLLBACK COMMIT:", out)

    print("\n" + "="*60)
    print("STEP 7: AFTER - Check if new-syntax policy survived")
    print("="*60)
    send(chan, "exit")
    time.sleep(5)

    out = send(chan, f"show config protocols bgp | include policy", wait=5)
    print("AFTER CONFIG POLICIES:", out)

    out = send(chan, f"show bgp ipv4 flowspec-vpn neighbors {NEIGHBOR} | include policy", wait=5)
    print("AFTER BGP POLICY:", out)

    out = send(chan, f"show bgp ipv4 flowspec-vpn neighbors {NEIGHBOR} | include route-map", wait=5)
    print("AFTER BGP ROUTE-MAP:", out)

    out = send(chan, f"show bgp ipv4 flowspec-vpn neighbors {NEIGHBOR} | include REDIRECT", wait=5)
    print("AFTER BGP REDIRECT:", out)

    out = send(chan, f"show bgp ipv4 flowspec-vpn neighbors {NEIGHBOR} | include allowas", wait=5)
    print("AFTER ALLOWAS:", out)

    out = send(chan, f"show bgp ipv4 flowspec-vpn neighbors {NEIGHBOR} | include Community", wait=5)
    print("AFTER COMMUNITY:", out)

    print("\n" + "="*60)
    print("STEP 8: Cleanup - remove test policy, commit")
    print("="*60)
    send(chan, "configure")
    send(chan, f"protocols bgp {ASN} neighbor {NEIGHBOR} address-family {AF}")
    send(chan, f"no policy {POLICY_NAME} in")
    send(chan, "top")
    out = send(chan, "commit", wait=10)
    print("CLEANUP COMMIT:", out)
    send(chan, "exit")

    out = send(chan, f"show config protocols bgp | include policy", wait=5)
    print("FINAL CONFIG POLICIES:", out)

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

    client.close()

if __name__ == "__main__":
    run_test()
