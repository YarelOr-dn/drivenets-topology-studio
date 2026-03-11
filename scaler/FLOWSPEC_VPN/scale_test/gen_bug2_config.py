#!/usr/bin/env python3
"""Generate FlowSpec local-policy config for BUG-2 reproduction.
100 simple match-classes with rate-limit 0 (drop).
"""

def generate_config():
    lines = []
    lines.append("routing-policy")
    lines.append("  flowspec-local-policies")
    lines.append("    ipv4")

    for i in range(1, 101):
        mc_name = f"MC4-BUG2-{i:04d}"
        proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
        lines.append(f"      match-class {mc_name}")
        lines.append(f"        dest-ip 10.2.0.{i}/32")
        lines.append(f"        protocol {proto}")
        lines.append(f"        dest-ports {5000 + i}")
        lines.append("      !")

    lines.append("      policy POL-BUG2-DROP")
    lines.append("        description BUG2-repro-all-drop")
    for i in range(1, 101):
        mc_name = f"MC4-BUG2-{i:04d}"
        lines.append(f"        match-class {mc_name}")
        lines.append("          action rate-limit 0")
        lines.append("        !")
    lines.append("      !")

    lines.append("    !")
    lines.append("  !")
    lines.append("!")
    lines.append("forwarding-options")
    lines.append("  flowspec-local")
    lines.append("    ipv4")
    lines.append("      apply-policy-to-flowspec POL-BUG2-DROP")
    lines.append("    !")
    lines.append("  !")
    lines.append("!")

    return "\n".join(lines)


def generate_delete():
    lines = []
    lines.append("routing-policy")
    lines.append("  flowspec-local-policies")
    lines.append("    no ipv4")
    lines.append("  !")
    lines.append("!")
    lines.append("forwarding-options")
    lines.append("  no flowspec-local")
    lines.append("!")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "delete":
        cfg = generate_delete()
        outfile = "/home/dn/SCALER/FLOWSPEC_VPN/scale_test/bug2_delete.cfg"
    else:
        cfg = generate_config()
        outfile = "/home/dn/SCALER/FLOWSPEC_VPN/scale_test/bug2_load.cfg"

    with open(outfile, "w") as f:
        f.write(cfg + "\n")
    print(f"Written to {outfile}")
    print(f"Lines: {len(cfg.splitlines())}")
