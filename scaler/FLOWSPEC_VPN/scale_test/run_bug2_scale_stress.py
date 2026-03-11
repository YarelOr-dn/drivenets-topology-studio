#!/usr/bin/env python3
"""BUG-2 Scale Stress Reproduction.

Strategy: stress TCAM with high-scale operations (2000+ rules, mixed actions,
rapid create/delete) to dirty the BCM state, then verify whether m_reserved
leaks prevent 100 simple rules from installing.

Phases:
  1. Load 2000 simple rules (rate-limit 0) → verify all install
  2. Delete all → reload 2000 with different IPs → repeat 3x (reshuffle stress at scale)
  3. Load 2000 with mixed actions (500 rate-limit 1000 + 1500 rate-limit 0) → policer + reshuffle
  4. Bulk action change: swap to all rate-limit 0 → delete → reload with rate-limit 1000
  5. Delete everything → load 100 simple rules → CHECK FOR LEAK
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


def wait_npu(target, timeout=120):
    """Wait until NCP6 installed >= target or converged."""
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


def gen_bulk(count, action, prefix, base_ip2=10, base_port=3000):
    """Generate config for `count` match-classes."""
    lines = ["routing-policy", "  flowspec-local-policies", "    ipv4"]
    for i in range(1, count + 1):
        proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
        o3, o4 = divmod(i - 1, 254)
        ip = f"10.{base_ip2}.{o3}.{o4 + 1}"
        lines += [f"      match-class MC4-{prefix}-{i:04d}",
                  f"        dest-ip {ip}/32",
                  f"        protocol {proto}",
                  f"        dest-ports {base_port + (i % 60000)}", "      !"]
    lines.append(f"      policy POL-{prefix}")
    lines.append(f"        description scale-stress")
    for i in range(1, count + 1):
        if isinstance(action, str):
            act = action
        elif callable(action):
            act = action(i)
        else:
            act = action
        lines += [f"        match-class MC4-{prefix}-{i:04d}",
                  f"          action {act}", "        !"]
    lines += ["      !", "    !", "  !", "!",
              "forwarding-options", "  flowspec-local", "    ipv4",
              f"      apply-policy-to-flowspec POL-{prefix}", "    !", "  !", "!"]
    return "\n".join(lines)


def ts():
    return datetime.now().strftime("%H:%M:%S")


def phase_header(num, title):
    print(f"\n{'='*70}")
    print(f"  PHASE {num}: {title}")
    print(f"{'='*70}\n")


def main():
    print(f"\n{'#'*70}")
    print(f"  BUG-2 SCALE STRESS TEST")
    print(f"  Strategy: stress TCAM at 2000+ rules, then check 100-rule install")
    print(f"  Started: {datetime.now().isoformat()}")
    print(f"{'#'*70}\n")

    results = {"test": "BUG-2 scale-stress", "started": datetime.now().isoformat(),
               "phases": [], "leak_detected": False}
    SCALE = 2000

    # ── CLEAN START ──
    print(f"[{ts()}] Clean start...")
    delete_flowspec_local(commit=True)
    time.sleep(5)
    npu = check_npu()
    print(f"  Baseline: NCP6={npu[6]}, NCP18={npu[18]}")

    # ── PHASE 1: Load 2000 simple rules ──
    phase_header(1, f"Load {SCALE} simple rules (rate-limit 0)")
    cfg = gen_bulk(SCALE, "rate-limit 0", "SC1", base_ip2=20, base_port=10000)
    print(f"[{ts()}] Pasting {SCALE} match-classes...")
    ok, _ = apply_config(cfg, commit=True)
    expected = BASELINE + SCALE
    npu, how = wait_npu(expected, timeout=180)
    i6 = npu[6][1]
    local6 = i6 - BASELINE
    print(f"[{ts()}] Phase 1: {local6}/{SCALE} installed ({how})")
    results["phases"].append({"phase": 1, "action": f"{SCALE}x rate-limit 0",
                              "inst6": i6, "local6": local6, "how": how})

    # ── PHASE 2: Rapid scale cycles (delete + reload different IPs) x3 ──
    phase_header(2, f"Rapid scale cycles: delete + reload {SCALE} rules x3")
    for cycle in range(1, 4):
        delete_flowspec_local(commit=True)
        time.sleep(3)
        prefix = f"SC2C{cycle}"
        cfg = gen_bulk(SCALE, "rate-limit 0", prefix, base_ip2=30 + cycle, base_port=20000)
        print(f"[{ts()}] Cycle {cycle}: loading {SCALE} rules (prefix={prefix})...")
        ok, _ = apply_config(cfg, commit=True)
        npu, how = wait_npu(expected, timeout=180)
        i6 = npu[6][1]
        local6 = i6 - BASELINE
        status = "OK" if local6 >= SCALE else f"PARTIAL {local6}/{SCALE}"
        print(f"[{ts()}] Cycle {cycle}: {status} ({how})")
        results["phases"].append({"phase": 2, "cycle": cycle, "inst6": i6,
                                  "local6": local6, "how": how})

    # ── PHASE 3: Mixed actions at scale (policer stress) ──
    phase_header(3, f"Mixed actions: {SCALE//4}x rate-limit 1000 + {SCALE*3//4}x rate-limit 0")
    delete_flowspec_local(commit=True)
    time.sleep(3)

    def mixed_action(i):
        return "rate-limit 1000" if i <= SCALE // 4 else "rate-limit 0"

    cfg = gen_bulk(SCALE, mixed_action, "SC3MIX", base_ip2=40, base_port=30000)
    print(f"[{ts()}] Loading {SCALE} mixed rules...")
    ok, _ = apply_config(cfg, commit=True)
    npu, how = wait_npu(expected, timeout=180)
    i6 = npu[6][1]
    local6 = i6 - BASELINE
    print(f"[{ts()}] Phase 3: {local6}/{SCALE} installed ({how})")
    results["phases"].append({"phase": 3, "action": "mixed rl1k+rl0",
                              "inst6": i6, "local6": local6, "how": how})

    # ── PHASE 4: Bulk action change → all rate-limit 1000 (max policer stress) ──
    phase_header(4, f"Bulk action change: {SCALE}x rate-limit 1000 (policer exhaustion)")
    delete_flowspec_local(commit=True)
    time.sleep(3)
    cfg = gen_bulk(SCALE, "rate-limit 1000", "SC4RL", base_ip2=50, base_port=40000)
    print(f"[{ts()}] Loading {SCALE}x rate-limit 1000...")
    ok, _ = apply_config(cfg, commit=True)
    npu, how = wait_npu(expected, timeout=180)
    i6 = npu[6][1]
    local6 = i6 - BASELINE
    print(f"[{ts()}] Phase 4: {local6}/{SCALE} installed ({how})")

    if local6 < SCALE:
        print(f"  >>> POLICER EXHAUSTION DETECTED: only {local6}/{SCALE} installed!")
        print(f"  >>> This is EXPECTED and may be the leak trigger.")
    results["phases"].append({"phase": 4, "action": f"{SCALE}x rate-limit 1000",
                              "inst6": i6, "local6": local6, "how": how})

    # ── PHASE 5: Delete + rapid cycles with rate-limit 1000 (accumulate leak) ──
    phase_header(5, "Rapid policer-stress cycles x3")
    for cycle in range(1, 4):
        delete_flowspec_local(commit=True)
        time.sleep(3)
        cfg = gen_bulk(SCALE, "rate-limit 1000", f"SC5C{cycle}", base_ip2=60 + cycle, base_port=50000)
        print(f"[{ts()}] Cycle {cycle}: loading {SCALE}x rate-limit 1000...")
        ok, _ = apply_config(cfg, commit=True)
        npu, how = wait_npu(expected, timeout=180)
        i6 = npu[6][1]
        local6 = i6 - BASELINE
        status = "OK" if local6 >= SCALE else f"PARTIAL {local6}/{SCALE}"
        print(f"[{ts()}] Cycle {cycle}: {status} ({how})")
        results["phases"].append({"phase": 5, "cycle": cycle, "inst6": i6,
                                  "local6": local6, "how": how})

    # ── PHASE 6: THE CHECK — delete all, load 100 simple rules ──
    phase_header(6, "LEAK CHECK: delete all → load 100 simple rules (rate-limit 0)")
    delete_flowspec_local(commit=True)
    time.sleep(5)
    npu_clean = check_npu()
    print(f"[{ts()}] After delete: NCP6={npu_clean[6]}")

    cfg100 = gen_bulk(100, "rate-limit 0", "LEAK", base_ip2=99, base_port=9000)
    print(f"[{ts()}] Loading 100 simple rules...")
    ok, _ = apply_config(cfg100, commit=True)
    expected100 = BASELINE + 100
    npu, how = wait_npu(expected100, timeout=60)
    i6 = npu[6][1]
    local6 = i6 - BASELINE

    if local6 >= 100:
        print(f"[{ts()}] RESULT: {local6}/100 installed — NO LEAK")
    else:
        missing = 100 - local6
        print(f"[{ts()}] RESULT: *** LEAK DETECTED *** {local6}/100 installed (-{missing} missing)")
        results["leak_detected"] = True
        results["leak_missing"] = missing

        # Capture evidence
        print(f"\n  Capturing traces...")
        errs = run_show("show file ncp 6 traces datapath/wb_agent.flowspec | include ERROR", timeout=30)
        warns = run_show("show file ncp 6 traces datapath/wb_agent.flowspec | include WARNING", timeout=30)
        reserves = run_show("show file ncp 6 traces datapath/wb_agent.flowspec | include ReserveQualifiers | tail 30", timeout=30)
        local_pol = run_show("show flowspec-local-policies ncp 6", timeout=60)
        ni = sum(1 for l in local_pol.split('\n') if 'Not Installed' in l)
        print(f"  Not Installed: {ni}")
        results["evidence"] = {
            "errors": ANSI_RE.sub('', errs)[-3000:],
            "warnings": ANSI_RE.sub('', warns)[-2000:],
            "reserves": ANSI_RE.sub('', reserves)[-3000:],
            "not_installed": ni,
        }

    results["phases"].append({"phase": 6, "action": "100x rate-limit 0 (leak check)",
                              "inst6": i6, "local6": local6, "how": how})

    # ── FINAL ──
    results["finished"] = datetime.now().isoformat()
    t0 = datetime.fromisoformat(results["started"])
    t1 = datetime.fromisoformat(results["finished"])

    print(f"\n{'#'*70}")
    print(f"  RESULT: {'*** LEAK DETECTED ***' if results['leak_detected'] else 'NO LEAK'}")
    print(f"  Duration: {(t1-t0).total_seconds():.0f}s")
    print(f"{'#'*70}\n")

    out = "/home/dn/SCALER/FLOWSPEC_VPN/scale_test/bug2_scale_stress_results.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
