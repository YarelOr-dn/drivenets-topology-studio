#!/usr/bin/env python3
"""Section 3: TCAM Expansion Map — 14 match-field variants.

Each variant creates 10 IPv4 MCs with specific match criteria to measure
how many HW entries each rule type consumes. One config file per variant.
"""

import os

OUT_DIR = "/home/dn/SCALER/FLOWSPEC_VPN/scale_test"

VARIANTS = {
    "3a": {"desc": "dest-ip only", "fields": lambda i: [f"dest-ip 10.3.0.{i}/32"]},
    "3b": {"desc": "dest-ip + protocol tcp", "fields": lambda i: [f"dest-ip 10.3.0.{i}/32", "protocol tcp(0x06)"]},
    "3c": {"desc": "dest-ip + protocol tcp + dest-ports 80", "fields": lambda i: [f"dest-ip 10.3.0.{i}/32", "protocol tcp(0x06)", "dest-ports 80"]},
    "3d": {"desc": "dest-ip + protocol tcp + dest-ports 80 + dscp 0", "fields": lambda i: [f"dest-ip 10.3.0.{i}/32", "protocol tcp(0x06)", "dest-ports 80", "dscp 0"]},
    "3e": {"desc": "dest-ip + src-ip", "fields": lambda i: [f"dest-ip 10.3.0.{i}/32", f"src-ip 192.168.0.{i}/32"]},
    "3f": {"desc": "dest-ip + src-ports 1024 (single)", "fields": lambda i: [f"dest-ip 10.3.0.{i}/32", "protocol tcp(0x06)", "src-ports 1024"]},
    "3g": {"desc": "dest-ip + src-ports 1024-2048 (range)", "fields": lambda i: [f"dest-ip 10.3.0.{i}/32", "protocol tcp(0x06)", "src-ports 1024-2048"]},
    "3h": {"desc": "dest-ip + packet-length 64 (single)", "fields": lambda i: [f"dest-ip 10.3.0.{i}/32", "protocol tcp(0x06)", "packet-length 64"]},
    "3i": {"desc": "dest-ip + packet-length 64-1500 (range)", "fields": lambda i: [f"dest-ip 10.3.0.{i}/32", "protocol tcp(0x06)", "packet-length 64-1500"]},
    "3j": {"desc": "dest-ip + tcp-flag syn", "fields": lambda i: [f"dest-ip 10.3.0.{i}/32", "protocol tcp(0x06)", "tcp-flag syn"]},
    "3k": {"desc": "dest-ip + tcp-flag syn,ack", "fields": lambda i: [f"dest-ip 10.3.0.{i}/32", "protocol tcp(0x06)", "tcp-flag syn,ack"]},
    "3l": {"desc": "dest-ip + fragmented", "fields": lambda i: [f"dest-ip 10.3.0.{i}/32", "protocol tcp(0x06)", "fragmented"]},
    "3m": {"desc": "dest-ip + protocol icmp + icmp echo-request", "fields": lambda i: [f"dest-ip 10.3.0.{i}/32", "protocol icmp(0x01)", "icmp echo-request"]},
    "3n": {"desc": "Combined worst-case", "fields": lambda i: [f"dest-ip 10.3.0.{i}/32", f"src-ip 192.168.0.{i}/32", "protocol tcp(0x06)", "src-ports 80-443", "packet-length 64-1500", "tcp-flag syn"]},
}


def gen_variant(variant_id, spec):
    filename = f"s3{variant_id[1:]}_tcam.cfg"
    path = os.path.join(OUT_DIR, filename)
    pol_name = f"POL4-S3{variant_id[1:].upper()}"

    with open(path, "w") as f:
        f.write("routing-policy\n")
        f.write("  flowspec-local-policies\n")
        f.write("    ipv4\n")

        for i in range(1, 11):
            mc_name = f"MC4-S3{variant_id[1:]}-{i:02d}"
            fields = spec["fields"](i)
            f.write(f"      match-class {mc_name}\n")
            for field in fields:
                f.write(f"        {field}\n")
            f.write(f"      !\n")

        f.write(f"      policy {pol_name}\n")
        f.write(f"        description {spec['desc'][:60]}\n")
        for i in range(1, 11):
            mc_name = f"MC4-S3{variant_id[1:]}-{i:02d}"
            f.write(f"        match-class {mc_name}\n")
            f.write(f"          action rate-limit 0\n")
            f.write(f"        !\n")
        f.write("      !\n")
        f.write("    !\n")
        f.write("  !\n")
        f.write("!\n")

        f.write("forwarding-options\n")
        f.write("  flowspec-local\n")
        f.write("    ipv4\n")
        f.write(f"      apply-policy-to-flowspec {pol_name}\n")
        f.write("    !\n")
        f.write("  !\n")
        f.write("!\n")

    print(f"  {filename}: {spec['desc']}")
    return path


print("Generating Section 3 configs:")
for vid, spec in VARIANTS.items():
    gen_variant(vid, spec)
print("Done.")
