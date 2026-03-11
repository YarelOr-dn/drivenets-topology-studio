#!/usr/bin/env python3
"""
SW-239537 Part 2: Verify excess-discard actually discards the over-limit prefix.
Apply max-prefix limit 1, hard reset BGP session, check if only 1 prefix accepted.
"""
import paramiko
import time
import sys
import re

HOSTS = ["100.64.2.33", "100.64.5.56"]
USER = "dnroot"
PASS = "dnroot"
ASN = "1234567"
NEIGHBOR = "100.64.6.134"

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
    return ansi_escape.sub('', out)

def run_test():
    client, chan = connect()

    print("="*70)
    print("STEP 1: Apply max-prefix limit 1, excess-discard under flowspec-vpn")
    print("="*70)
    send(chan, "configure")
    send(chan, f"protocols bgp {ASN} neighbor {NEIGHBOR} address-family ipv4-flowspec-vpn")
    send(chan, "maximum-prefix")
    send(chan, "limit 1")
    send(chan, "threshold 80")
    send(chan, "exceed-action excess-discard")
    send(chan, "!")
    send(chan, "top")
    out = send(chan, "commit", wait=15)
    print("COMMIT:", out)
    send(chan, "exit")

    print("\n" + "="*70)
    print("STEP 2: BEFORE hard reset — 2 prefixes still accepted")
    print("="*70)
    out = send(chan, f"show bgp neighbors {NEIGHBOR} | include regex \"address family:|Maximum|prefixes\"", wait=8)
    print("BEFORE RESET:", out)

    print("\n" + "="*70)
    print("STEP 3: Hard reset BGP session (drops and re-establishes)")
    print("="*70)
    out = send(chan, f"clear bgp neighbor {NEIGHBOR}", wait=5)
    print("HARD RESET:", out)

    print("Waiting 30s for BGP to re-establish and routes to arrive...")
    time.sleep(30)

    print("\n" + "="*70)
    print("STEP 4: AFTER hard reset — check prefix count")
    print("        EXPECT: Only 1 prefix accepted (limit is 1, was 2)")
    print("="*70)
    out = send(chan, f"show bgp ipv4 flowspec-vpn summary | include {NEIGHBOR}", wait=5)
    print("SUMMARY AFTER RESET:", out)

    out = send(chan, f"show bgp neighbors {NEIGHBOR} | include regex \"address family:|Maximum|prefixes\"", wait=8)
    print("FULL AF VIEW AFTER RESET:", out)

    print("\n" + "="*70)
    print("STEP 5: Check bgpd traces for discard evidence")
    print("="*70)
    out = send(chan, "show file traces routing_engine/bgpd_traces | include MAXPFX | tail 10", wait=5)
    print("MAXPFX traces:", out)
    out = send(chan, "show file traces routing_engine/bgpd_traces | include excess | tail 10", wait=5)
    print("EXCESS traces:", out)

    print("\n" + "="*70)
    print("STEP 6: Show the accepted routes")
    print("="*70)
    out = send(chan, f"show bgp ipv4 flowspec-vpn neighbors {NEIGHBOR} received-routes", wait=5)
    print("RECEIVED ROUTES:", out)

    print("\n" + "="*70)
    print("STEP 7: CLEANUP — remove max-prefix, restore all routes")
    print("="*70)
    send(chan, "configure")
    send(chan, f"protocols bgp {ASN} neighbor {NEIGHBOR} address-family ipv4-flowspec-vpn")
    send(chan, "no maximum-prefix")
    send(chan, "top")
    out = send(chan, "commit", wait=15)
    print("CLEANUP COMMIT:", out)
    send(chan, "exit")

    time.sleep(3)
    out = send(chan, f"clear bgp neighbor {NEIGHBOR} soft in", wait=10)
    print("RESTORE SOFT IN:", out)
    time.sleep(10)

    out = send(chan, f"show bgp ipv4 flowspec-vpn summary | include {NEIGHBOR}", wait=5)
    print("FINAL RESTORED SUMMARY:", out)

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    client.close()

if __name__ == "__main__":
    run_test()
