#!/usr/bin/env python3
"""
SW-239537: maximum-prefix exceed-action excess-discard for FlowSpec-VPN
Test that:
  1. max-prefix config applies to correct AF (flowspec-vpn, NOT ipv4-unicast)
  2. excess-discard actually discards the over-limit prefix
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

    print("\n" + "="*70)
    print("STEP 1: BEFORE — current prefix counts & max-prefix state")
    print("="*70)
    out = send(chan, f"show bgp ipv4 flowspec-vpn neighbors {NEIGHBOR} | include prefix", wait=5)
    print("BEFORE flowspec-vpn prefixes:", out)
    out = send(chan, f"show bgp ipv4 unicast neighbors {NEIGHBOR} | include prefix", wait=5)
    print("BEFORE unicast prefixes:", out)
    out = send(chan, f"show bgp neighbors {NEIGHBOR} | include maximum", wait=5)
    print("BEFORE max-prefix (all AFs):", out)

    print("\n" + "="*70)
    print("STEP 2: Apply maximum-prefix limit 1, exceed-action excess-discard")
    print("        under ipv4-flowspec-vpn AF for neighbor " + NEIGHBOR)
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
    print("STEP 3: Verify max-prefix shows in CORRECT AF (flowspec-vpn)")
    print("="*70)
    out = send(chan, f"show bgp ipv4 flowspec-vpn neighbors {NEIGHBOR} | include maximum", wait=5)
    print("flowspec-vpn max-prefix:", out)

    print("\n" + "="*70)
    print("STEP 4: Verify NO leak to ipv4-unicast AF")
    print("="*70)
    out = send(chan, f"show bgp ipv4 unicast neighbors {NEIGHBOR} | include maximum", wait=5)
    print("unicast max-prefix (should be EMPTY):", out)

    print("\n" + "="*70)
    print("STEP 5: Check prefix count BEFORE clear (still 2 accepted)")
    print("="*70)
    out = send(chan, f"show bgp ipv4 flowspec-vpn neighbors {NEIGHBOR} | include prefix", wait=5)
    print("flowspec-vpn prefixes before clear:", out)

    print("\n" + "="*70)
    print("STEP 6: Clear BGP soft in to trigger excess-discard evaluation")
    print("="*70)
    out = send(chan, f"clear bgp ipv4 flowspec-vpn neighbor {NEIGHBOR} soft in", wait=10)
    print("CLEAR result:", out)

    time.sleep(5)

    print("\n" + "="*70)
    print("STEP 7: AFTER clear — check if excess was discarded")
    print("        Expect: 1 prefix accepted (was 2, limit is 1)")
    print("="*70)
    out = send(chan, f"show bgp ipv4 flowspec-vpn neighbors {NEIGHBOR} | include prefix", wait=5)
    print("AFTER flowspec-vpn prefixes:", out)
    out = send(chan, f"show bgp ipv4 flowspec-vpn neighbors {NEIGHBOR} | include Maximum", wait=5)
    print("AFTER max-prefix display:", out)

    print("\n" + "="*70)
    print("STEP 8: Verify ipv4-unicast NOT affected")
    print("="*70)
    out = send(chan, f"show bgp ipv4 unicast neighbors {NEIGHBOR} | include prefix", wait=5)
    print("unicast prefix count (should be unchanged):", out)
    out = send(chan, f"show bgp ipv4 unicast neighbors {NEIGHBOR} | include maximum", wait=5)
    print("unicast max-prefix (should be EMPTY):", out)

    print("\n" + "="*70)
    print("STEP 9: Check syslog for correct AF in EXCEEDED message")
    print("="*70)
    out = send(chan, "show logging | include MAXIMUM_PREFIX | tail 5", wait=5)
    print("SYSLOG max-prefix:", out)

    print("\n" + "="*70)
    print("STEP 10: Show full flowspec-vpn AF section for proof")
    print("="*70)
    out = send(chan, f"show bgp ipv4 flowspec-vpn neighbors {NEIGHBOR} | find Flowspec-VPN", wait=5)
    print("Full flowspec-vpn AF section:", out)

    print("\n" + "="*70)
    print("STEP 11: CLEANUP — remove maximum-prefix config")
    print("="*70)
    send(chan, "configure")
    send(chan, f"protocols bgp {ASN} neighbor {NEIGHBOR} address-family ipv4-flowspec-vpn")
    send(chan, "no maximum-prefix")
    send(chan, "top")
    out = send(chan, "commit", wait=15)
    print("CLEANUP COMMIT:", out)
    send(chan, "exit")

    time.sleep(3)
    out = send(chan, f"clear bgp ipv4 flowspec-vpn neighbor {NEIGHBOR} soft in", wait=10)
    print("RESTORE CLEAR:", out)
    time.sleep(5)

    print("\n" + "="*70)
    print("STEP 12: VERIFY CLEANUP — prefixes restored, no max-prefix")
    print("="*70)
    out = send(chan, f"show bgp ipv4 flowspec-vpn neighbors {NEIGHBOR} | include prefix", wait=5)
    print("RESTORED prefixes:", out)
    out = send(chan, f"show bgp ipv4 flowspec-vpn neighbors {NEIGHBOR} | include maximum", wait=5)
    print("RESTORED max-prefix (should be EMPTY):", out)

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    client.close()

if __name__ == "__main__":
    run_test()
