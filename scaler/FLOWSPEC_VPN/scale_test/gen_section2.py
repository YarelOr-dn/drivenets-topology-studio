#!/usr/bin/env python3
"""Section 2: VRF Behavior — ALPHA, no-VRF, ZULU, mixed, nonexistent.

4 sub-tests, each 100 IPv4 + 50 IPv6 MCs, clean slate per sub-test.
"""

import os

OUT_DIR = "/home/dn/SCALER/FLOWSPEC_VPN/scale_test"


def gen_config(filename, ipv4_vrf_map, ipv6_vrf_map, pol4_name, pol6_name):
    """Generate FlowSpec config with per-MC VRF assignment.
    
    ipv4_vrf_map: dict {mc_index: vrf_name or None}
    ipv6_vrf_map: dict {mc_index: vrf_name or None}
    """
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w") as f:
        f.write("routing-policy\n")
        f.write("  flowspec-local-policies\n")

        f.write("    ipv4\n")
        for i in range(1, 101):
            proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
            port = 1000 + i
            o3, o4 = (i - 1) // 256, (i - 1) % 256
            f.write(f"      match-class MC4-{i:04d}\n")
            f.write(f"        dest-ip 10.1.{o3}.{o4}/32\n")
            f.write(f"        protocol {proto}\n")
            f.write(f"        dest-ports {port}\n")
            vrf = ipv4_vrf_map.get(i)
            if vrf:
                f.write(f"        vrf {vrf}\n")
            f.write(f"      !\n")

        f.write(f"      policy {pol4_name}\n")
        f.write(f"        description VRF-test-IPv4\n")
        for i in range(1, 101):
            f.write(f"        match-class MC4-{i:04d}\n")
            f.write(f"          action rate-limit 0\n")
            f.write(f"        !\n")
        f.write("      !\n")
        f.write("    !\n")

        f.write("    ipv6\n")
        for i in range(1, 51):
            proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
            port = 2000 + i
            f.write(f"      match-class MC6-{i:04d}\n")
            f.write(f"        dest-ip 2001:db8:1::{i:x}/128\n")
            f.write(f"        protocol {proto}\n")
            f.write(f"        dest-ports {port}\n")
            vrf = ipv6_vrf_map.get(i)
            if vrf:
                f.write(f"        vrf {vrf}\n")
            f.write(f"      !\n")

        f.write(f"      policy {pol6_name}\n")
        f.write(f"        description VRF-test-IPv6\n")
        for i in range(1, 51):
            f.write(f"        match-class MC6-{i:04d}\n")
            f.write(f"          action rate-limit 0\n")
            f.write(f"        !\n")
        f.write("      !\n")
        f.write("    !\n")

        f.write("  !\n")
        f.write("!\n")

        f.write("forwarding-options\n")
        f.write("  flowspec-local\n")
        f.write("    ipv4\n")
        f.write(f"      apply-policy-to-flowspec {pol4_name}\n")
        f.write("    !\n")
        f.write("    ipv6\n")
        f.write(f"      apply-policy-to-flowspec {pol6_name}\n")
        f.write("    !\n")
        f.write("  !\n")
        f.write("!\n")

    print(f"Generated {path}")


# 2a: vrf ALPHA on all MCs
v4_alpha = {i: "ALPHA" for i in range(1, 101)}
v6_alpha = {i: "ALPHA" for i in range(1, 51)}
gen_config("s2a_vrf_alpha.cfg", v4_alpha, v6_alpha, "POL4-ALPHA", "POL6-ALPHA")

# 2b: No VRF (same as Section 1 structure but different policy names)
gen_config("s2b_no_vrf.cfg", {}, {}, "POL4-NOVRF", "POL6-NOVRF")

# 2c: Mixed — half ALPHA, half ZULU
v4_mixed = {}
v6_mixed = {}
for i in range(1, 101):
    v4_mixed[i] = "ALPHA" if i <= 50 else "ZULU"
for i in range(1, 51):
    v6_mixed[i] = "ALPHA" if i <= 25 else "ZULU"
gen_config("s2c_vrf_mixed.cfg", v4_mixed, v6_mixed, "POL4-MIXED", "POL6-MIXED")

# 2d: vrf NONEXISTENT on all MCs
v4_nonexist = {i: "NONEXISTENT" for i in range(1, 101)}
v6_nonexist = {i: "NONEXISTENT" for i in range(1, 51)}
gen_config("s2d_vrf_nonexist.cfg", v4_nonexist, v6_nonexist, "POL4-NOEXIST", "POL6-NOEXIST")

print("All Section 2 configs generated.")
