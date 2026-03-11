#!/usr/bin/env python3
"""BUG-2 Reproduction: FlowSpec TCAM m_reserved leak via file-merge cycles.

Automates repeated load/delete cycles using apply_config (SSH + paste + commit)
to trigger the m_reserved leak that rollback doesn't reproduce.

Checks NPU resources after each LOAD. When installed < expected, captures
wb_agent traces and documents the exact cycle that caused the leak.
"""

import sys
import time
import re
import json
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), "w", buffering=1)
sys.path.insert(0, "/home/dn/SCALER/FLOWSPEC_VPN/scale_test")
from apply_config import apply_config, delete_flowspec_local, run_show

BASELINE_IPV4_INSTALLED = 13
LOCAL_RULES = 100
EXPECTED_TOTAL_INSTALLED = BASELINE_IPV4_INSTALLED + LOCAL_RULES  # 113
MAX_CYCLES = 15
ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')
RESULTS_FILE = "/home/dn/SCALER/FLOWSPEC_VPN/scale_test/bug2_filemerge_results.json"


def parse_npu(text):
    """Parse NCP 6 flowspec row: returns (received, installed, hw_entries)."""
    clean = ANSI_RE.sub('', text)
    m = re.search(r'\|\s*6\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)/12000', clean)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return 0, 0, 0


def parse_npu_18(text):
    """Parse NCP 18 flowspec row."""
    clean = ANSI_RE.sub('', text)
    m = re.search(r'\|\s*18\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)/12000', clean)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return 0, 0, 0


def check_npu():
    """Get NPU resources for both NCPs."""
    raw = run_show("show system npu-resources resource-type flowspec")
    ncp6 = parse_npu(raw)
    ncp18 = parse_npu_18(raw)
    return ncp6, ncp18, raw


def get_traces(ncp_id, keyword, timeout=30):
    """Pull wb_agent.flowspec traces filtered by keyword."""
    cmd = f"show file ncp {ncp_id} traces datapath/wb_agent.flowspec | include {keyword}"
    return run_show(cmd, timeout=timeout)


def ts():
    return datetime.now().strftime("%H:%M:%S")


def main():
    print(f"\n{'='*70}")
    print(f"BUG-2 REPRODUCTION: File-Merge Create/Delete Cycles")
    print(f"Method: apply_config (SSH paste + commit) — NOT rollback")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"{'='*70}\n")

    with open("/home/dn/SCALER/FLOWSPEC_VPN/scale_test/bug2_load.cfg") as f:
        load_cfg = f.read()

    results = {
        "test": "BUG-2 file-merge reproduction",
        "started": datetime.now().isoformat(),
        "baseline_installed": BASELINE_IPV4_INSTALLED,
        "local_rules": LOCAL_RULES,
        "expected_total": EXPECTED_TOTAL_INSTALLED,
        "cycles": [],
        "leak_detected": False,
        "leak_cycle": None,
    }

    # Step 0: Verify clean baseline
    print(f"[{ts()}] STEP 0: Verify clean baseline")
    ncp6, ncp18, raw = check_npu()
    print(f"  NCP 6:  received={ncp6[0]}, installed={ncp6[1]}, hw={ncp6[2]}")
    print(f"  NCP 18: received={ncp18[0]}, installed={ncp18[1]}, hw={ncp18[2]}")

    if ncp6[1] > BASELINE_IPV4_INSTALLED:
        print(f"  Cleaning: {ncp6[1]} installed > baseline {BASELINE_IPV4_INSTALLED}, deleting first...")
        delete_flowspec_local(commit=True)
        time.sleep(10)
        ncp6, ncp18, raw = check_npu()
        print(f"  After clean: NCP 6 installed={ncp6[1]}")

    if ncp6[1] != BASELINE_IPV4_INSTALLED:
        print(f"  WARNING: Baseline is {ncp6[1]}, expected {BASELINE_IPV4_INSTALLED}")
        results["actual_baseline"] = ncp6[1]

    print(f"\n  Baseline confirmed: {ncp6[1]}/{ncp6[0]} (installed/received)")
    print()

    leak_found = False

    for cycle in range(1, MAX_CYCLES + 1):
        cycle_data = {"cycle": cycle, "timestamps": {}}

        # --- LOAD phase ---
        print(f"{'='*60}")
        print(f"[{ts()}] CYCLE {cycle}/{MAX_CYCLES} — LOAD (adding {LOCAL_RULES} rules via file-merge)")
        print(f"{'='*60}", flush=True)

        cycle_data["timestamps"]["load_start"] = datetime.now().isoformat()
        ok, _ = apply_config(load_cfg, commit=True)
        cycle_data["timestamps"]["load_end"] = datetime.now().isoformat()
        cycle_data["load_success"] = ok

        if not ok:
            print(f"  LOAD FAILED! Stopping test.")
            cycle_data["error"] = "load commit failed"
            results["cycles"].append(cycle_data)
            break

        time.sleep(8)

        ncp6, ncp18, raw = check_npu()
        cycle_data["after_load"] = {
            "ncp6": {"received": ncp6[0], "installed": ncp6[1], "hw": ncp6[2]},
            "ncp18": {"received": ncp18[0], "installed": ncp18[1], "hw": ncp18[2]},
        }

        local_inst_6 = ncp6[1] - BASELINE_IPV4_INSTALLED
        local_inst_18 = ncp18[1] - BASELINE_IPV4_INSTALLED
        leaked_6 = LOCAL_RULES - local_inst_6
        leaked_18 = LOCAL_RULES - local_inst_18

        status = "OK" if ncp6[1] >= EXPECTED_TOTAL_INSTALLED else f"LEAK! {leaked_6} rules missing"
        print(f"  NCP 6:  {ncp6[0]} received, {ncp6[1]} installed (local: {local_inst_6}/{LOCAL_RULES}) — {status}")

        status18 = "OK" if ncp18[1] >= EXPECTED_TOTAL_INSTALLED else f"LEAK! {leaked_18} rules missing"
        print(f"  NCP 18: {ncp18[0]} received, {ncp18[1]} installed (local: {local_inst_18}/{LOCAL_RULES}) — {status18}")

        if ncp6[1] < EXPECTED_TOTAL_INSTALLED or ncp18[1] < EXPECTED_TOTAL_INSTALLED:
            leak_found = True
            results["leak_detected"] = True
            results["leak_cycle"] = cycle
            cycle_data["leak"] = True
            cycle_data["leaked_count_ncp6"] = leaked_6
            cycle_data["leaked_count_ncp18"] = leaked_18

            print(f"\n  *** LEAK DETECTED AT CYCLE {cycle}! ***")
            print(f"  NCP 6:  {leaked_6} rules failed to install")
            print(f"  NCP 18: {leaked_18} rules failed to install")
            print(f"\n  Capturing evidence...\n")

            # Capture traces
            hhmm = datetime.now().strftime("%H:%M")
            print(f"  Pulling wb_agent traces (ERROR)...")
            err_traces_6 = get_traces(6, "ERROR")
            err_traces_18 = get_traces(18, "ERROR")

            print(f"  Pulling wb_agent traces (ReserveQualifiers)...")
            reserve_traces_6 = get_traces(6, "ReserveQualifiers")

            print(f"  Pulling wb_agent traces (Reshuffle)...")
            reshuffle_traces_6 = get_traces(6, "Reshuffle")

            print(f"  Pulling flowspec-local-policies ncp 6...")
            local_policies = run_show("show flowspec-local-policies ncp 6", timeout=60)

            cycle_data["evidence"] = {
                "error_traces_ncp6": ANSI_RE.sub('', err_traces_6)[-3000:],
                "error_traces_ncp18": ANSI_RE.sub('', err_traces_18)[-3000:],
                "reserve_traces_ncp6_tail": ANSI_RE.sub('', reserve_traces_6)[-3000:],
                "reshuffle_traces_ncp6": ANSI_RE.sub('', reshuffle_traces_6)[-3000:],
            }

            not_installed_count = sum(1 for l in local_policies.split('\n') if 'Not Installed' in l)
            cycle_data["not_installed_count"] = not_installed_count
            print(f"  'Not Installed' rules on NCP 6: {not_installed_count}")

            results["cycles"].append(cycle_data)
            break

        # --- DELETE phase ---
        print(f"\n[{ts()}] CYCLE {cycle}/{MAX_CYCLES} — DELETE (removing all local rules)")
        cycle_data["timestamps"]["delete_start"] = datetime.now().isoformat()
        delete_flowspec_local(commit=True)
        cycle_data["timestamps"]["delete_end"] = datetime.now().isoformat()
        time.sleep(8)

        ncp6_del, ncp18_del, _ = check_npu()
        cycle_data["after_delete"] = {
            "ncp6": {"received": ncp6_del[0], "installed": ncp6_del[1], "hw": ncp6_del[2]},
            "ncp18": {"received": ncp18_del[0], "installed": ncp18_del[1], "hw": ncp18_del[2]},
        }
        print(f"  NCP 6:  {ncp6_del[0]} received, {ncp6_del[1]} installed — {'OK' if ncp6_del[1] == BASELINE_IPV4_INSTALLED else 'UNEXPECTED'}")
        print()

        results["cycles"].append(cycle_data)

    # Final summary
    results["finished"] = datetime.now().isoformat()

    print(f"\n\n{'='*70}")
    print(f"BUG-2 FILE-MERGE TEST SUMMARY")
    print(f"{'='*70}")
    print(f"  Total cycles completed: {len(results['cycles'])}")
    print(f"  Leak detected: {results['leak_detected']}")
    if results['leak_detected']:
        print(f"  Leak first appeared: Cycle {results['leak_cycle']}")
        lc = results['cycles'][-1]
        print(f"  NCP 6 leaked:  {lc.get('leaked_count_ncp6', '?')} rules")
        print(f"  NCP 18 leaked: {lc.get('leaked_count_ncp18', '?')} rules")
    else:
        print(f"  No leak after {MAX_CYCLES} cycles — bug may need more cycles or different config")

    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Results saved to: {RESULTS_FILE}")
    print(f"  Finished: {datetime.now().isoformat()}\n")


if __name__ == "__main__":
    main()
