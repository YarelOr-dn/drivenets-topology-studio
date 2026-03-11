#!/usr/bin/env python3
"""Run Section 2: VRF Behavior tests (2a through 2d).
For each sub-test: delete previous, apply config, wait, collect results.
"""

import time
import sys
sys.path.insert(0, "/home/dn/SCALER/FLOWSPEC_VPN/scale_test")
from apply_config import apply_config, delete_flowspec_local, run_show

TESTS = [
    ("s2a", "s2a_vrf_alpha.cfg", "vrf ALPHA on all MCs"),
    ("s2b", "s2b_no_vrf.cfg", "No VRF at all"),
    ("s2c", "s2c_vrf_mixed.cfg", "Mixed: half ALPHA, half ZULU"),
    ("s2d", "s2d_vrf_nonexist.cfg", "vrf NONEXISTENT on all MCs"),
]

results = {}

for test_id, cfg_file, desc in TESTS:
    print(f"\n{'='*60}")
    print(f"TEST {test_id}: {desc}")
    print(f"{'='*60}")

    print(f"\n[{test_id}] Step 1: Cleanup previous config...")
    ok, _ = delete_flowspec_local(commit=True)
    if not ok:
        print(f"  WARNING: delete may have had issues, checking TCAM...")
    time.sleep(10)

    npu_out = run_show("show system npu-resources resource-type flowspec")
    print(f"  TCAM after cleanup: {npu_out[-200:]}")

    print(f"\n[{test_id}] Step 2: Apply {cfg_file}...")
    cfg_path = f"/home/dn/SCALER/FLOWSPEC_VPN/scale_test/{cfg_file}"
    with open(cfg_path) as f:
        cfg = f.read()

    ok, out = apply_config(cfg, commit=True)
    time.sleep(15)

    print(f"\n[{test_id}] Step 3: Collect results...")
    npu_out = run_show("show system npu-resources resource-type flowspec")
    vrf_out = run_show("show flowspec-local-policies ncp 6 | include Vrf")
    tail_out = run_show("show flowspec-local-policies ncp 6 | tail 15")
    not_inst = run_show('show flowspec-local-policies ncp 6 | include "Not Installed"')

    results[test_id] = {
        "desc": desc,
        "npu": npu_out,
        "vrf_lines": vrf_out,
        "tail": tail_out,
        "not_installed": not_inst,
        "paste_ok": ok,
    }

    print(f"\n--- NPU Resources ---")
    for line in npu_out.split("\n"):
        if "6 " in line or "18 " in line or "NCP" in line:
            print(f"  {line.strip()}")

    vrf_vals = set()
    import re
    for line in vrf_out.split("\n"):
        clean = re.sub(r'\x1b\[[0-9;]*m', '', line)
        if "Vrf" in clean:
            m = re.search(r'Vrf:\s*(\S+)', clean)
            if m:
                vrf_vals.add(m.group(1))
    print(f"  Vrf values seen: {vrf_vals}")

    ni_count = sum(1 for l in not_inst.split("\n") if "Not Installed" in l)
    print(f"  'Not Installed' count: {ni_count}")

print("\n\n" + "=" * 60)
print("SECTION 2 SUMMARY")
print("=" * 60)
for tid, r in results.items():
    print(f"\n{tid} ({r['desc']}):")
    print(f"  Config applied: {r['paste_ok']}")
    vrf_vals = set()
    for line in r['vrf_lines'].split("\n"):
        clean = re.sub(r'\x1b\[[0-9;]*m', '', line)
        m = re.search(r'Vrf:\s*(\S+)', clean)
        if m:
            vrf_vals.add(m.group(1))
    print(f"  Vrf values: {vrf_vals}")
    ni_count = sum(1 for l in r['not_installed'].split("\n") if "Not Installed" in l)
    print(f"  Not Installed: {ni_count}")
