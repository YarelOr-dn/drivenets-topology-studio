#!/usr/bin/env python3
"""Section 1: Baseline — 100 IPv4 + 50 IPv6, simple criteria, no VRF, all-drop.

Structure per FLOWSPEC_LOCAL_POLICIES_FULL_MAP.md:
- match-class definitions at ipv4/ipv6 level (with dest-ip, protocol, etc.)
- policy at ipv4/ipv6 level references match-classes with actions
- forwarding-options flowspec-local ipv4/ipv6 apply-policy-to-flowspec
"""

OUTPUT = "/home/dn/SCALER/FLOWSPEC_VPN/scale_test/s1_baseline.cfg"

with open(OUTPUT, "w") as f:
    f.write("routing-policy\n")
    f.write("  flowspec-local-policies\n")

    # --- IPv4 match-class definitions ---
    f.write("    ipv4\n")
    for i in range(1, 101):
        proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
        port = 1000 + i
        octet3 = (i - 1) // 256
        octet4 = (i - 1) % 256
        f.write(f"      match-class MC4-{i:04d}\n")
        f.write(f"        dest-ip 10.1.{octet3}.{octet4}/32\n")
        f.write(f"        protocol {proto}\n")
        f.write(f"        dest-ports {port}\n")
        f.write(f"      !\n")

    # --- IPv4 policy referencing match-classes ---
    f.write("      policy POL4-BASELINE\n")
    f.write("        description Baseline-100-IPv4-simple-drop\n")
    for i in range(1, 101):
        f.write(f"        match-class MC4-{i:04d}\n")
        f.write(f"          action rate-limit 0\n")
        f.write(f"        !\n")
    f.write("      !\n")
    f.write("    !\n")

    # --- IPv6 match-class definitions ---
    f.write("    ipv6\n")
    for i in range(1, 51):
        proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
        port = 2000 + i
        f.write(f"      match-class MC6-{i:04d}\n")
        f.write(f"        dest-ip 2001:db8:1::{i:x}/128\n")
        f.write(f"        protocol {proto}\n")
        f.write(f"        dest-ports {port}\n")
        f.write(f"      !\n")

    # --- IPv6 policy referencing match-classes ---
    f.write("      policy POL6-BASELINE\n")
    f.write("        description Baseline-50-IPv6-simple-drop\n")
    for i in range(1, 51):
        f.write(f"        match-class MC6-{i:04d}\n")
        f.write(f"          action rate-limit 0\n")
        f.write(f"        !\n")
    f.write("      !\n")
    f.write("    !\n")

    f.write("  !\n")
    f.write("!\n")

    # --- Forwarding-options: attach policies ---
    f.write("forwarding-options\n")
    f.write("  flowspec-local\n")
    f.write("    ipv4\n")
    f.write("      apply-policy-to-flowspec POL4-BASELINE\n")
    f.write("    !\n")
    f.write("    ipv6\n")
    f.write("      apply-policy-to-flowspec POL6-BASELINE\n")
    f.write("    !\n")
    f.write("  !\n")
    f.write("!\n")

print(f"Generated {OUTPUT}")
