#!/usr/bin/env python3
"""Run Section 3: TCAM Expansion Map — 14 variants, measure HW entries per rule."""

import sys
import time
import re
import json

sys.stdout = open(sys.stdout.fileno(), "w", buffering=1)
sys.path.insert(0, "/home/dn/SCALER/FLOWSPEC_VPN/scale_test")
from apply_config import apply_config, delete_flowspec_local, run_show

BASELINE_IPV4 = 13
ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

VARIANTS = [
    ("3a", "s3a_tcam.cfg", "dest-ip only"),
    ("3b", "s3b_tcam.cfg", "dest-ip + protocol tcp"),
    ("3c", "s3c_tcam.cfg", "dest-ip + protocol + dest-ports"),
    ("3d", "s3d_tcam.cfg", "dest-ip + protocol + dest-ports + dscp"),
    ("3e", "s3e_tcam.cfg", "dest-ip + src-ip"),
    ("3f", "s3f_tcam.cfg", "dest-ip + src-ports single"),
    ("3g", "s3g_tcam.cfg", "dest-ip + src-ports range"),
    ("3h", "s3h_tcam.cfg", "dest-ip + packet-length single"),
    ("3i", "s3i_tcam.cfg", "dest-ip + packet-length range"),
    ("3j", "s3j_tcam.cfg", "dest-ip + tcp-flag syn"),
    ("3k", "s3k_tcam.cfg", "dest-ip + tcp-flag syn,ack"),
    ("3l", "s3l_tcam.cfg", "dest-ip + fragmented"),
    ("3m", "s3m_tcam.cfg", "dest-ip + icmp echo-request"),
    ("3n", "s3n_tcam.cfg", "Combined worst-case"),
]

results = {}

for vid, cfg_file, desc in VARIANTS:
    print(f"\n{'='*50}")
    print(f"TEST {vid}: {desc}")
    print(f"{'='*50}", flush=True)

    print(f"  Cleaning up...", flush=True)
    delete_flowspec_local(commit=True)
    time.sleep(5)

    npu = run_show("show system npu-resources resource-type flowspec")
    m = re.search(r'\|\s*6\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)/12000', ANSI_RE.sub('', npu))
    pre_hw = int(m.group(3)) if m else BASELINE_IPV4
    print(f"  Pre-test HW: {pre_hw}", flush=True)

    cfg_path = f"/home/dn/SCALER/FLOWSPEC_VPN/scale_test/{cfg_file}"
    with open(cfg_path) as f:
        cfg = f.read()
    print(f"  Applying {cfg_file}...", flush=True)
    ok, out = apply_config(cfg, commit=True)
    time.sleep(8)

    npu = run_show("show system npu-resources resource-type flowspec")
    clean_npu = ANSI_RE.sub('', npu)
    m = re.search(r'\|\s*6\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)/12000', clean_npu)
    if m:
        received = int(m.group(1))
        installed = int(m.group(2))
        hw_entries = int(m.group(3))
        local_hw = hw_entries - BASELINE_IPV4
        local_rules = installed - BASELINE_IPV4 + (1 if received > installed else 0)
        local_installed = installed - BASELINE_IPV4 + (1 if received > installed else 0)
        ratio = local_hw / 10 if local_hw > 0 else 0
        print(f"  Received: {received}, Installed: {installed}, HW: {hw_entries}")
        print(f"  LOCAL: {local_hw} HW entries for 10 rules = {ratio:.1f}:1")
        results[vid] = {"desc": desc, "hw": local_hw, "rules": 10, "ratio": ratio,
                        "received": received, "installed": installed}
    else:
        print(f"  FAILED to parse NPU output")
        results[vid] = {"desc": desc, "hw": 0, "rules": 10, "ratio": 0, "error": True}

    # Check not-installed
    ni = run_show('show flowspec-local-policies ncp 6 | include "Not Installed"')
    ni_count = sum(1 for l in ni.split('\n') if 'Not Installed' in l)
    results[vid]["not_installed"] = ni_count
    if ni_count > 0:
        print(f"  WARNING: {ni_count} Not Installed!", flush=True)

print(f"\n\n{'='*60}")
print("SECTION 3 — TCAM EXPANSION MAP")
print(f"{'='*60}")
print(f"{'Variant':<6} {'Match Criteria':<45} {'HW/10':>6} {'Ratio':>6}")
print("-" * 65)
for vid, r in results.items():
    print(f"{vid:<6} {r['desc']:<45} {r['hw']:>6} {r['ratio']:>5.1f}:1")

with open("/home/dn/SCALER/FLOWSPEC_VPN/scale_test/s3_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nResults saved to s3_results.json")
