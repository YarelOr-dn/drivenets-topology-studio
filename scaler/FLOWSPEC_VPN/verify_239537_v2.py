#!/usr/bin/env python3
"""
SW-239537 v2: Apply max-prefix, get full neighbor output to check AF placement,
try correct clear syntax, verify excess-discard, cleanup.
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
    print("STEP 1: Apply max-prefix config under ipv4-flowspec-vpn")
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
    print("STEP 2: Full neighbor output — find which AF has max-prefix")
    print("        Look for 'For address family:' + 'Maximum prefixes'")
    print("="*70)
    out = send(chan, f"show bgp neighbors {NEIGHBOR} | include regex \"address family|Maximum|prefixes\"", wait=8)
    print("FULL NEIGHBOR (filtered):", out)

    print("\n" + "="*70)
    print("STEP 3: Show config to confirm it's under flowspec-vpn")
    print("="*70)
    out = send(chan, f"show config protocols bgp | find maximum-prefix", wait=5)
    print("CONFIG:", out)

    print("\n" + "="*70)
    print("STEP 4: Try different clear syntaxes")
    print("="*70)
    # Try clear bgp neighbor X soft in (no AF qualifier)
    out = send(chan, f"clear bgp neighbor {NEIGHBOR} soft in", wait=8)
    print("clear bgp neighbor X soft in:", out)

    time.sleep(5)

    print("\n" + "="*70)
    print("STEP 5: Check prefix count after clear")
    print("="*70)
    out = send(chan, f"show bgp neighbors {NEIGHBOR} | include regex \"address family|Maximum|prefixes\"", wait=8)
    print("AFTER CLEAR:", out)

    print("\n" + "="*70)
    print("STEP 6: Check syslog for MAXIMUM_PREFIX events")
    print("="*70)
    out = send(chan, "show file traces routing_engine/bgpd_traces | include MAXIMUM", wait=5)
    print("BGPD TRACES MAXIMUM:", out)
    out = send(chan, "show file traces routing_engine/bgpd_traces | include maximum", wait=5)
    print("BGPD TRACES maximum:", out)
    out = send(chan, "show file traces routing_engine/bgpd_traces | include excess", wait=5)
    print("BGPD TRACES excess:", out)

    print("\n" + "="*70)
    print("STEP 7: Check system-event for BGP_NEIGHBOR_MAXIMUM_PREFIX")
    print("="*70)
    out = send(chan, "show system-event-log | include MAXIMUM_PREFIX | tail 10", wait=5)
    print("SYSTEM EVENT LOG:", out)

    print("\n" + "="*70)
    print("STEP 8: CLEANUP — remove max-prefix config")
    print("="*70)
    send(chan, "configure")
    send(chan, f"protocols bgp {ASN} neighbor {NEIGHBOR} address-family ipv4-flowspec-vpn")
    send(chan, "no maximum-prefix")
    send(chan, "top")
    out = send(chan, "commit", wait=15)
    print("CLEANUP COMMIT:", out)
    send(chan, "exit")

    time.sleep(3)
    out = send(chan, f"clear bgp neighbor {NEIGHBOR} soft in", wait=8)
    print("RESTORE CLEAR:", out)
    time.sleep(5)

    print("\n" + "="*70)
    print("STEP 9: Verify restored — 2 prefixes, no max-prefix")
    print("="*70)
    out = send(chan, f"show bgp neighbors {NEIGHBOR} | include regex \"address family|Maximum|prefixes\"", wait=8)
    print("RESTORED:", out)

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    client.close()

if __name__ == "__main__":
    run_test()
