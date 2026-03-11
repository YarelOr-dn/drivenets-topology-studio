#!/usr/bin/env python3
"""Section 4: Action Variations and Policer Limits.

Tests: 4a (drop), 4b (rate-limit 64), 4c (rate-limit 1000),
       4d (redirect-to-vrf), 4e (incremental policer), 4f (mixed actions)
"""

import sys
import time
import re
import json

sys.stdout = open(sys.stdout.fileno(), "w", buffering=1)
sys.path.insert(0, "/home/dn/SCALER/FLOWSPEC_VPN/scale_test")
from apply_config import apply_config, delete_flowspec_local, run_show

BASELINE_IPV4_INSTALLED = 13
ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def parse_npu(text):
    clean = ANSI_RE.sub('', text)
    m = re.search(r'\|\s*6\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)/12000', clean)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return 0, 0, 0


def count_not_installed(text):
    return sum(1 for l in text.split('\n') if 'Not Installed' in l)


def gen_config(mc_count, action, policy_name="POL4-S4"):
    """Generate IPv4-only config with specified action for all MCs."""
    lines = ["routing-policy", "  flowspec-local-policies", "    ipv4"]
    for i in range(1, mc_count + 1):
        proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
        o3, o4 = (i - 1) // 256, (i - 1) % 256
        lines.append(f"      match-class MC4-S4-{i:04d}")
        lines.append(f"        dest-ip 10.4.{o3}.{o4}/32")
        lines.append(f"        protocol {proto}")
        lines.append(f"        dest-ports {3000 + i}")
        lines.append(f"      !")

    lines.append(f"      policy {policy_name}")
    lines.append(f"        description S4-action-test")
    for i in range(1, mc_count + 1):
        lines.append(f"        match-class MC4-S4-{i:04d}")
        lines.append(f"          action {action}")
        lines.append(f"        !")
    lines.append("      !")
    lines.append("    !")
    lines.append("  !")
    lines.append("!")
    lines.append("forwarding-options")
    lines.append("  flowspec-local")
    lines.append("    ipv4")
    lines.append(f"      apply-policy-to-flowspec {policy_name}")
    lines.append("    !")
    lines.append("  !")
    lines.append("!")
    return "\n".join(lines)


def gen_mixed_config(drop_count, rl_count, policy_name="POL4-S4MIX"):
    """Generate config with first N rules as drop, next M as rate-limit 1000."""
    total = drop_count + rl_count
    lines = ["routing-policy", "  flowspec-local-policies", "    ipv4"]
    for i in range(1, total + 1):
        proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
        o3, o4 = (i - 1) // 256, (i - 1) % 256
        lines.append(f"      match-class MC4-MIX-{i:04d}")
        lines.append(f"        dest-ip 10.4.{o3}.{o4}/32")
        lines.append(f"        protocol {proto}")
        lines.append(f"        dest-ports {4000 + i}")
        lines.append(f"      !")

    lines.append(f"      policy {policy_name}")
    lines.append(f"        description S4-mixed-actions")
    for i in range(1, total + 1):
        action = "rate-limit 0" if i <= drop_count else "rate-limit 1000"
        lines.append(f"        match-class MC4-MIX-{i:04d}")
        lines.append(f"          action {action}")
        lines.append(f"        !")
    lines.append("      !")
    lines.append("    !")
    lines.append("  !")
    lines.append("!")
    lines.append("forwarding-options")
    lines.append("  flowspec-local")
    lines.append("    ipv4")
    lines.append(f"      apply-policy-to-flowspec {policy_name}")
    lines.append("    !")
    lines.append("  !")
    lines.append("!")
    return "\n".join(lines)


results = {}

# --- 4a: 100 MCs, rate-limit 0 (drop) ---
print("\n" + "=" * 50)
print("TEST 4a: 100 MCs, rate-limit 0 (drop)")
print("=" * 50, flush=True)
delete_flowspec_local(commit=True)
time.sleep(5)
cfg = gen_config(100, "rate-limit 0", "POL4-DROP")
ok, _ = apply_config(cfg, commit=True)
time.sleep(10)
rcv, inst, hw = parse_npu(run_show("show system npu-resources resource-type flowspec"))
ni = count_not_installed(run_show('show flowspec-local-policies ncp 6 | include "Not Installed"'))
local_inst = inst - BASELINE_IPV4_INSTALLED
print(f"  Received={rcv}, Installed={inst}, HW={hw}, Local installed={local_inst}, NI={ni}")
results["4a"] = {"action": "rate-limit 0", "count": 100, "local_installed": local_inst, "hw": hw, "ni": ni}

# --- 4b: 100 MCs, rate-limit 64 ---
print("\n" + "=" * 50)
print("TEST 4b: 100 MCs, rate-limit 64")
print("=" * 50, flush=True)
delete_flowspec_local(commit=True)
time.sleep(5)
cfg = gen_config(100, "rate-limit 64", "POL4-RL64")
ok, _ = apply_config(cfg, commit=True)
time.sleep(10)
rcv, inst, hw = parse_npu(run_show("show system npu-resources resource-type flowspec"))
ni = count_not_installed(run_show('show flowspec-local-policies ncp 6 | include "Not Installed"'))
local_inst = inst - BASELINE_IPV4_INSTALLED
print(f"  Received={rcv}, Installed={inst}, HW={hw}, Local installed={local_inst}, NI={ni}")
results["4b"] = {"action": "rate-limit 64", "count": 100, "local_installed": local_inst, "hw": hw, "ni": ni}

# --- 4c: 100 MCs, rate-limit 1000 ---
print("\n" + "=" * 50)
print("TEST 4c: 100 MCs, rate-limit 1000")
print("=" * 50, flush=True)
delete_flowspec_local(commit=True)
time.sleep(5)
cfg = gen_config(100, "rate-limit 1000", "POL4-RL1K")
ok, _ = apply_config(cfg, commit=True)
time.sleep(10)
rcv, inst, hw = parse_npu(run_show("show system npu-resources resource-type flowspec"))
ni = count_not_installed(run_show('show flowspec-local-policies ncp 6 | include "Not Installed"'))
local_inst = inst - BASELINE_IPV4_INSTALLED
print(f"  Received={rcv}, Installed={inst}, HW={hw}, Local installed={local_inst}, NI={ni}")
results["4c"] = {"action": "rate-limit 1000", "count": 100, "local_installed": local_inst, "hw": hw, "ni": ni}

# --- 4d: 100 MCs, redirect-to-vrf ZULU ---
print("\n" + "=" * 50)
print("TEST 4d: 100 MCs, redirect-to-vrf ZULU")
print("=" * 50, flush=True)
delete_flowspec_local(commit=True)
time.sleep(5)
cfg = gen_config(100, "redirect-to-vrf ZULU", "POL4-REDIR")
ok, _ = apply_config(cfg, commit=True)
time.sleep(10)
rcv, inst, hw = parse_npu(run_show("show system npu-resources resource-type flowspec"))
ni = count_not_installed(run_show('show flowspec-local-policies ncp 6 | include "Not Installed"'))
local_inst = inst - BASELINE_IPV4_INSTALLED
print(f"  Received={rcv}, Installed={inst}, HW={hw}, Local installed={local_inst}, NI={ni}")
results["4d"] = {"action": "redirect-to-vrf ZULU", "count": 100, "local_installed": local_inst, "hw": hw, "ni": ni}

# --- 4e: Incremental policer — add 10 rate-limit 1000 MCs at a time until exhaustion ---
print("\n" + "=" * 50)
print("TEST 4e: Incremental policer — find exact limit")
print("=" * 50, flush=True)
delete_flowspec_local(commit=True)
time.sleep(5)

policer_data = []
for batch_end in range(10, 510, 10):
    batch_start = batch_end - 9
    cfg = gen_config(batch_end, "rate-limit 1000", "POL4-POLICER")
    ok, _ = apply_config(cfg, commit=True)
    time.sleep(5)
    rcv, inst, hw = parse_npu(run_show("show system npu-resources resource-type flowspec"))
    local_inst = inst - BASELINE_IPV4_INSTALLED
    ni = count_not_installed(run_show('show flowspec-local-policies ncp 6 | include "Not Installed"'))
    print(f"  {batch_end} MCs: installed={local_inst}, HW={hw}, NI={ni}", flush=True)
    policer_data.append({"mcs": batch_end, "installed": local_inst, "hw": hw, "ni": ni})
    if local_inst < batch_end:
        print(f"  POLICER EXHAUSTION at {batch_end} MCs! Only {local_inst} installed.")
        break

results["4e"] = {"policer_data": policer_data}

# --- 4f: Mixed actions — 50 drop + 50 rate-limit 1000 ---
print("\n" + "=" * 50)
print("TEST 4f: Mixed — 50 drop + 50 rate-limit 1000")
print("=" * 50, flush=True)
delete_flowspec_local(commit=True)
time.sleep(5)
cfg = gen_mixed_config(50, 50, "POL4-MIXED")
ok, _ = apply_config(cfg, commit=True)
time.sleep(10)
rcv, inst, hw = parse_npu(run_show("show system npu-resources resource-type flowspec"))
ni = count_not_installed(run_show('show flowspec-local-policies ncp 6 | include "Not Installed"'))
local_inst = inst - BASELINE_IPV4_INSTALLED
print(f"  Received={rcv}, Installed={inst}, HW={hw}, Local installed={local_inst}, NI={ni}")
results["4f"] = {"drop": 50, "rate_limit": 50, "local_installed": local_inst, "hw": hw, "ni": ni}

# --- Summary ---
print(f"\n\n{'='*60}")
print("SECTION 4 SUMMARY")
print(f"{'='*60}")
for tid, r in results.items():
    if tid == "4e":
        print(f"  {tid}: Policer limit data — see s4_results.json")
    else:
        print(f"  {tid}: action={r.get('action','mixed')}, installed={r.get('local_installed','?')}, NI={r.get('ni','?')}")

with open("/home/dn/SCALER/FLOWSPEC_VPN/scale_test/s4_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nResults saved to s4_results.json")
