#!/usr/bin/env python3
"""BUG-2 Reproduction: Packet-Length Range Leak Trigger.

The key insight: packet-length range rules (BUG-1) pass ReserveQualifiers()
but FAIL at WriteRuleInTcam(). This leaks m_reserved in FlowspecTcamManager.
Over many create/delete cycles, leaked m_reserved accumulates until simple
rules can no longer reserve TCAM entries despite 99%+ TCAM being free.

Phases:
  1. Verify clean baseline (100/100 simple rules)
  2. Seed leak: 30 cycles of packet-length range rules (BUG-1 failures)
  3. Mix: interleave packet-length range + simple rule cycles
  4. Probe: load 100 simple rules → check for leak
  5. Escalate: increase scale/cycles if probe passes
  6. Confirm: capture evidence, restart NCP to verify recovery
"""

import sys
import time
import re
import json
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), "w", buffering=1)
sys.path.insert(0, "/home/dn/SCALER/FLOWSPEC_VPN/scale_test")
from apply_config import apply_config, delete_flowspec_local, run_show

PE4_HOST = "100.64.6.82"
BASELINE = 13
ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def parse_npu(text):
    clean = ANSI_RE.sub('', text)
    out = {}
    for ncp_id in [6, 18]:
        m = re.search(rf'\|\s*{ncp_id}\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)/12000', clean)
        out[ncp_id] = (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else (0, 0, 0)
    return out


def check_npu():
    return parse_npu(run_show("show system npu-resources resource-type flowspec"))


def wait_npu(target, timeout=90):
    prev = None
    deadline = time.time() + timeout
    while time.time() < deadline:
        npu = check_npu()
        i6 = npu[6][1]
        if i6 >= target:
            return npu, "ok"
        if prev is not None and prev == i6:
            return npu, "stuck"
        prev = i6
        time.sleep(3)
    return check_npu(), "timeout"


def ts():
    return datetime.now().strftime("%H:%M:%S")


def gen_pktlen_range(count, prefix, pkt_range="64-1500"):
    """Generate config with packet-length range (BUG-1 trigger = leak source)."""
    lines = ["routing-policy", "  flowspec-local-policies", "    ipv4"]
    for i in range(1, count + 1):
        proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
        o3, o4 = divmod(i - 1, 254)
        ip = f"10.50.{o3}.{o4 + 1}"
        lines += [f"      match-class MC4-{prefix}-{i:04d}",
                  f"        dest-ip {ip}/32",
                  f"        protocol {proto}",
                  f"        dest-ports {3000 + i}",
                  f"        packet-length {pkt_range}", "      !"]
    lines.append(f"      policy POL-{prefix}")
    lines.append(f"        description pktlen-range-leak-trigger")
    for i in range(1, count + 1):
        lines += [f"        match-class MC4-{prefix}-{i:04d}",
                  f"          action rate-limit 0", "        !"]
    lines += ["      !", "    !", "  !", "!",
              "forwarding-options", "  flowspec-local", "    ipv4",
              f"      apply-policy-to-flowspec POL-{prefix}", "    !", "  !", "!"]
    return "\n".join(lines)


def gen_combined_worst(count, prefix):
    """Section 3n variant: packet-length range + src-ip + tcp-flag (all fail)."""
    lines = ["routing-policy", "  flowspec-local-policies", "    ipv4"]
    for i in range(1, count + 1):
        proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
        o3, o4 = divmod(i - 1, 254)
        ip = f"10.60.{o3}.{o4 + 1}"
        lines += [f"      match-class MC4-{prefix}-{i:04d}",
                  f"        dest-ip {ip}/32",
                  f"        src-ip 192.168.{o3}.{o4 + 1}/32",
                  f"        protocol {proto}",
                  f"        dest-ports {4000 + i}",
                  f"        packet-length 64-1500",
                  f"        tcp-flag syn", "      !"]
    lines.append(f"      policy POL-{prefix}")
    lines.append(f"        description combined-worst-case")
    for i in range(1, count + 1):
        lines += [f"        match-class MC4-{prefix}-{i:04d}",
                  f"          action rate-limit 0", "        !"]
    lines += ["      !", "    !", "  !", "!",
              "forwarding-options", "  flowspec-local", "    ipv4",
              f"      apply-policy-to-flowspec POL-{prefix}", "    !", "  !", "!"]
    return "\n".join(lines)


def gen_simple(count, prefix, base_ip2=70):
    """Generate simple rules for leak probe (rate-limit 0, no packet-length)."""
    lines = ["routing-policy", "  flowspec-local-policies", "    ipv4"]
    for i in range(1, count + 1):
        proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
        o3, o4 = divmod(i - 1, 254)
        ip = f"10.{base_ip2}.{o3}.{o4 + 1}"
        lines += [f"      match-class MC4-{prefix}-{i:04d}",
                  f"        dest-ip {ip}/32",
                  f"        protocol {proto}",
                  f"        dest-ports {7000 + i}", "      !"]
    lines.append(f"      policy POL-{prefix}")
    lines.append(f"        description simple-leak-probe")
    for i in range(1, count + 1):
        lines += [f"        match-class MC4-{prefix}-{i:04d}",
                  f"          action rate-limit 0", "        !"]
    lines += ["      !", "    !", "  !", "!",
              "forwarding-options", "  flowspec-local", "    ipv4",
              f"      apply-policy-to-flowspec POL-{prefix}", "    !", "  !", "!"]
    return "\n".join(lines)


def delete_method(method_id):
    """Rotate deletion methods to stress different cleanup paths."""
    if method_id == 0:
        apply_config("no routing-policy flowspec-local-policies\nno forwarding-options flowspec-local", commit=True)
    elif method_id == 1:
        apply_config("no forwarding-options flowspec-local", commit=True)
        apply_config("no routing-policy flowspec-local-policies", commit=True)
    elif method_id == 2:
        delete_flowspec_local(commit=True)
    else:
        apply_config("no forwarding-options flowspec-local\nno routing-policy flowspec-local-policies", commit=True)


def probe_leak(probe_id, results):
    """Load 100 simple rules and check if all install."""
    print(f"\n  --- LEAK PROBE #{probe_id} ---")
    npu_before = check_npu()
    i6_before = npu_before[6][1]
    print(f"  Before: NCP6 installed={i6_before} (expect {BASELINE})")

    cfg = gen_simple(100, f"PROBE{probe_id}", base_ip2=70 + (probe_id % 10))
    apply_config(cfg, commit=True)

    npu, how = wait_npu(BASELINE + 100, timeout=60)
    i6 = npu[6][1]
    local6 = i6 - BASELINE

    probe_result = {"probe": probe_id, "installed": local6, "expected": 100,
                    "npu6": npu[6], "how": how}
    results["probes"].append(probe_result)

    if local6 < 100:
        missing = 100 - local6
        print(f"  *** LEAK DETECTED *** {local6}/100 installed (-{missing} missing)")
        results["leak_detected"] = True
        results["leak_probe"] = probe_id
        results["leak_missing"] = missing

        print(f"  Capturing evidence...")
        results["evidence"] = {
            "npu": run_show("show system npu-resources resource-type flowspec"),
            "syslog_tail": run_show("show flowspec-local-policies ncp 6 | tail 50"),
        }
        return True
    else:
        print(f"  OK: {local6}/100 installed")
        delete_method(probe_id % 4)
        return False


def main():
    print(f"\n{'#'*70}")
    print(f"  BUG-2 PKTLEN LEAK REPRODUCTION")
    print(f"  Trigger: packet-length range rules (BUG-1) leak m_reserved")
    print(f"  Started: {datetime.now().isoformat()}")
    print(f"{'#'*70}\n")

    results = {"test": "BUG-2 pktlen-leak", "started": datetime.now().isoformat(),
               "cycles": [], "probes": [], "leak_detected": False}

    # ─── PHASE 1: CLEAN BASELINE ───
    print(f"{'='*70}")
    print(f"  PHASE 1: Verify clean baseline")
    print(f"{'='*70}")

    delete_flowspec_local(commit=True)
    npu = check_npu()
    print(f"[{ts()}] Baseline: NCP6={npu[6]}")

    cfg = gen_simple(100, "BASELINE", base_ip2=80)
    apply_config(cfg, commit=True)
    npu, how = wait_npu(BASELINE + 100, timeout=60)
    local6 = npu[6][1] - BASELINE
    print(f"[{ts()}] Baseline probe: {local6}/100 installed ({how})")
    if local6 < 100:
        print(f"  NCP already dirty! Leak present before testing.")
        results["ncp_dirty_at_start"] = True
    delete_flowspec_local(commit=True)
    print(f"[{ts()}] Baseline cleaned.\n")

    # ─── PHASE 2: SEED LEAK — PACKET-LENGTH RANGE CYCLES ───
    print(f"{'='*70}")
    print(f"  PHASE 2: Seed leak with packet-length range rules (30 cycles)")
    print(f"  Each cycle: load rules with packet-length 64-1500 (BUG-1 = fail at BCM)")
    print(f"  Failed WriteRuleInTcam leaks m_reserved in FlowspecTcamManager")
    print(f"{'='*70}\n")

    pktlen_counts = [100, 100, 100, 100, 100,
                     50, 50, 50, 50, 50,
                     200, 200, 200, 100, 100,
                     100, 100, 100, 100, 100,
                     100, 100, 100, 100, 100,
                     100, 100, 100, 100, 100]

    for cycle in range(1, 31):
        count = pktlen_counts[cycle - 1] if cycle <= len(pktlen_counts) else 100
        pkt_range = "64-1500" if cycle <= 20 else "64-500"
        prefix = f"PL{cycle:02d}"
        method = (cycle - 1) % 4

        if cycle % 5 == 0:
            cfg = gen_combined_worst(count, prefix)
            kind = "combined-worst"
        else:
            cfg = gen_pktlen_range(count, prefix, pkt_range)
            kind = f"pktlen-{pkt_range}"

        print(f"[{ts()}] Cycle {cycle}/30: {count} rules ({kind}), delete method {method}")
        apply_config(cfg, commit=True)

        npu = check_npu()
        i6 = npu[6][1]
        local6 = i6 - BASELINE
        print(f"  NCP6: {local6}/{count} installed (expect 0 = all failed)")

        cd = {"cycle": cycle, "count": count, "kind": kind, "installed": local6,
              "method": method}
        results["cycles"].append(cd)

        delete_method(method)
        print(f"  Deleted (method {method}).")

        if cycle % 10 == 0:
            leaked = probe_leak(cycle // 10, results)
            if leaked:
                break

    # ─── PHASE 3: MIX — INTERLEAVE PKTLEN + SIMPLE CYCLES ───
    if not results["leak_detected"]:
        print(f"\n{'='*70}")
        print(f"  PHASE 3: Mix packet-length range + simple rule cycles (20 cycles)")
        print(f"{'='*70}\n")

        for cycle in range(31, 51):
            prefix = f"MX{cycle:02d}"
            method = (cycle - 1) % 4

            if cycle % 2 == 1:
                cfg = gen_pktlen_range(100, prefix, "64-1500")
                kind = "pktlen-64-1500"
            else:
                cfg = gen_simple(100, prefix, base_ip2=30 + (cycle % 10))
                kind = "simple-100"

            print(f"[{ts()}] Cycle {cycle}/50: {kind}, delete method {method}")
            apply_config(cfg, commit=True)

            npu = check_npu()
            i6 = npu[6][1]
            local6 = i6 - BASELINE
            expected = 0 if "pktlen" in kind else 100
            print(f"  NCP6: {local6}/100 installed (expect ~{expected})")

            cd = {"cycle": cycle, "kind": kind, "installed": local6, "method": method}
            results["cycles"].append(cd)

            delete_method(method)

            if cycle % 10 == 0:
                leaked = probe_leak(cycle // 10, results)
                if leaked:
                    break

    # ─── PHASE 4: ESCALATION — HIGHER SCALE ───
    if not results["leak_detected"]:
        print(f"\n{'='*70}")
        print(f"  PHASE 4: Escalation — 500 pktlen-range rules x 20 cycles")
        print(f"{'='*70}\n")

        for cycle in range(51, 71):
            prefix = f"ES{cycle:02d}"
            method = (cycle - 1) % 4

            if cycle % 3 == 0:
                cfg = gen_combined_worst(500, prefix)
                kind = "combined-worst-500"
            elif cycle % 3 == 1:
                cfg = gen_pktlen_range(500, prefix, "64-1500")
                kind = "pktlen-500"
            else:
                cfg = gen_pktlen_range(200, prefix, "64-147")
                kind = "pktlen-64-147-200"

            print(f"[{ts()}] Cycle {cycle}/70: {kind}, delete method {method}")
            apply_config(cfg, commit=True)

            npu = check_npu()
            local6 = npu[6][1] - BASELINE
            print(f"  NCP6: {local6} installed")

            cd = {"cycle": cycle, "kind": kind, "installed": local6, "method": method}
            results["cycles"].append(cd)

            delete_method(method)

            if cycle % 5 == 0:
                leaked = probe_leak(cycle // 5, results)
                if leaked:
                    break

    # ─── FINAL REPORT ───
    results["finished"] = datetime.now().isoformat()
    t0 = datetime.fromisoformat(results["started"])
    t1 = datetime.fromisoformat(results["finished"])
    duration = (t1 - t0).total_seconds()

    print(f"\n{'#'*70}")
    if results["leak_detected"]:
        print(f"  *** BUG-2 REPRODUCED ***")
        print(f"  Leak detected at probe #{results['leak_probe']}")
        print(f"  Missing rules: {results['leak_missing']}")
    else:
        print(f"  NO LEAK DETECTED after {len(results['cycles'])} cycles")
    print(f"  Duration: {duration:.0f}s")
    print(f"{'#'*70}\n")

    out = "/home/dn/SCALER/FLOWSPEC_VPN/scale_test/bug2_pktlen_leak_results.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
