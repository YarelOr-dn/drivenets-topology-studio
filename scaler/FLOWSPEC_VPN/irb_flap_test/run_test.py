#!/usr/bin/env python3
"""SW-211921 IRB Flap Twice verification test on RR-SA-2.

Applies base EVPN/VRF/IRB config, captures baseline, triggers IRB swap,
and collects traces to prove whether IRBs flap once (fix works) or twice (bug present).

Device: RR-SA-2 (DNOS 26.1.0 build 24_priv, NCP-36CD-S)
SSH: 100.64.4.205 (mgmt-ncc-0), fallback 100.64.5.15 (mgmt0)
"""

import paramiko
import time
import re
import sys
import json
from datetime import datetime
from pathlib import Path

HOSTS = ["100.64.4.205", "100.64.5.15"]
USER = "dnroot"
PASS = "dnroot"
PORT = 22

RESULT_DIR = Path(__file__).parent / "results"
RESULT_DIR.mkdir(exist_ok=True)

ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def clean(text):
    return ANSI_RE.sub("", text)


class DNOSSession:
    def __init__(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.host = None
        for h in HOSTS:
            try:
                print(f"  Trying SSH to {h}...")
                self.client.connect(h, port=PORT, username=USER, password=PASS,
                                    timeout=15, look_for_keys=False)
                self.host = h
                print(f"  Connected to {h}")
                break
            except Exception as e:
                print(f"  Failed {h}: {e}")
                continue
        if not self.host:
            raise ConnectionError(f"Cannot reach any of: {HOSTS}")
        self.shell = self.client.invoke_shell(width=250, height=50)
        self.shell.settimeout(300)
        self.full_output = ""
        self._recv(3)

    def _recv(self, delay=1.0):
        time.sleep(delay)
        buf = ""
        while self.shell.recv_ready():
            chunk = self.shell.recv(65536).decode("utf-8", errors="replace")
            buf += chunk
            self.full_output += chunk
        return buf

    def send(self, cmd, delay=1.0):
        self.shell.send(cmd + "\n")
        return self._recv(delay)

    def show(self, command, timeout=30):
        """Run a show command, return clean output."""
        self.shell.send(command + " | no-more\n")
        accumulated = ""
        for _ in range(timeout):
            time.sleep(1)
            while self.shell.recv_ready():
                accumulated += self.shell.recv(65536).decode("utf-8", errors="replace")
            if accumulated and not self.shell.recv_ready():
                time.sleep(0.5)
                if not self.shell.recv_ready():
                    break
        return clean(accumulated)

    def apply_config(self, config_text):
        """Enter config mode, paste config, commit."""
        print(f"  Applying {len(config_text.splitlines())} lines of config...")
        self.send("configure", 2)
        self.send("rollback 0", 1)

        lines = config_text.strip().split("\n")
        for line in lines:
            self.shell.send(line + "\n")
        self._recv(2)

        paste_output = clean(self.full_output)
        errors = [l.strip() for l in paste_output.split("\n") if "ERROR:" in l]
        if errors:
            print(f"  PASTE ERRORS: {len(errors)}")
            for e in errors[:5]:
                print(f"    {e}")
            self.send("rollback 0", 1)
            self.send("exit", 1)
            return False, errors

        print("  Committing...", flush=True)
        self.shell.send("commit\n")
        commit_done = False
        accumulated = ""
        for attempt in range(60):
            time.sleep(5)
            buf = ""
            while self.shell.recv_ready():
                chunk = self.shell.recv(65536).decode("utf-8", errors="replace")
                buf += chunk
                self.full_output += chunk
            accumulated += buf
            c = clean(accumulated)
            if "Commit complete" in c or "ommit complete" in c:
                print("  COMMIT COMPLETE")
                commit_done = True
                break
            if "Nothing to commit" in c:
                print("  NOTHING TO COMMIT")
                commit_done = True
                break
            if "COMMIT CHECK FAILED" in c or "Unable to commit" in c:
                print("  COMMIT FAILED")
                self.send("rollback 0", 1)
                self.send("exit", 1)
                return False, ["COMMIT FAILED"]
            if attempt > 0 and attempt % 6 == 0:
                print(f"    ... waiting ({attempt * 5}s)...")

        if not commit_done:
            print("  COMMIT TIMEOUT")
            self.send("rollback 0", 2)
            self.send("exit", 1)
            return False, ["TIMEOUT"]

        self.send("exit", 1)
        return True, []

    def close(self):
        self.client.close()


def run_test():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {"timestamp": timestamp, "device": "RR-SA-2", "phases": {}}

    base_config = (Path(__file__).parent / "base_config.txt").read_text()
    swap_config = (Path(__file__).parent / "swap_config.txt").read_text()

    # Phase 2: Apply base config
    print("=" * 70)
    print("PHASE 2: Apply base EVPN/VRF/IRB config")
    print("=" * 70)
    sess = DNOSSession()
    ok, errs = sess.apply_config(base_config)
    if not ok:
        print(f"FATAL: Base config failed: {errs}")
        sess.close()
        return
    results["phases"]["base_config"] = {"status": "applied", "errors": errs}

    print("\n  Waiting 15s for services to initialize...")
    time.sleep(15)

    # Phase 3: Verify operational + capture baseline
    print("\n" + "=" * 70)
    print("PHASE 3: Verify services + capture baseline")
    print("=" * 70)

    baseline = {}
    for cmd_name, cmd in [
        ("evpn_summary", "show evpn summary"),
        ("evpn_detail", "show evpn detail"),
        ("interfaces_irb", "show interfaces ip"),
        ("system_event_log", "show system-event-log"),
    ]:
        print(f"  Running: {cmd}")
        baseline[cmd_name] = sess.show(cmd)

    results["phases"]["baseline"] = baseline

    irb_up_count = baseline["interfaces_irb"].count("irb")
    print(f"\n  IRB interfaces found in output: {irb_up_count}")

    # Phase 4: Capture pre-swap timestamp and traces
    print("\n" + "=" * 70)
    print("PHASE 4: Capture pre-swap traces")
    print("=" * 70)

    pre_swap_traces = {}
    for cmd_name, cmd in [
        ("cluster_mgr_irb", "show file traces cluster-engine/cluster_manager_protocols | include irb | tail 20"),
        ("fibmgrd_crit", "show file traces routing_engine/fibmgrd_traces | include CRIT | tail 10"),
        ("rib_mgr_evpn", "show file traces routing_engine/rib-manager_traces | include EVPN | tail 20"),
        ("fibmgrd_attach", "show file traces routing_engine/fibmgrd_traces | include EVPN_ATTACH | tail 20"),
    ]:
        print(f"  Running: {cmd}")
        pre_swap_traces[cmd_name] = sess.show(cmd, timeout=15)

    results["phases"]["pre_swap_traces"] = pre_swap_traces
    sess.close()

    # Note the swap timestamp
    swap_time = datetime.now().strftime("%H:%M")
    print(f"\n  Swap timestamp (approx): {swap_time}")

    # Phase 5: Apply the swap
    print("\n" + "=" * 70)
    print("PHASE 5: Apply IRB swap config (TRIGGER)")
    print("=" * 70)
    sess = DNOSSession()
    ok, errs = sess.apply_config(swap_config)
    if not ok:
        print(f"FATAL: Swap config failed: {errs}")
        sess.close()
        return
    results["phases"]["swap"] = {"status": "applied", "errors": errs, "swap_time": swap_time}

    print("\n  Waiting 10s for flap events to settle...")
    time.sleep(10)

    # Phase 6: Collect post-swap traces (THE PROOF)
    print("\n" + "=" * 70)
    print("PHASE 6: Collect post-swap traces (PROOF)")
    print("=" * 70)

    post_swap_traces = {}
    for cmd_name, cmd in [
        ("cluster_mgr_irb", "show file traces cluster-engine/cluster_manager_protocols | include irb | tail 40"),
        ("system_event_log", "show system-event-log | include irb | tail 40"),
        ("fibmgrd_crit", "show file traces routing_engine/fibmgrd_traces | include CRIT | tail 10"),
        ("fibmgrd_attach", "show file traces routing_engine/fibmgrd_traces | include EVPN_ATTACH | tail 20"),
        ("fibmgrd_detach", "show file traces routing_engine/fibmgrd_traces | include EVPN_DETACH | tail 20"),
        ("rib_mgr_attach", "show file traces routing_engine/rib-manager_traces | include attachIrb | tail 20"),
        ("rib_mgr_detach", "show file traces routing_engine/rib-manager_traces | include detachIrb | tail 20"),
        ("rib_mgr_irb_state", "show file traces routing_engine/rib-manager_traces | include irb | tail 40"),
        ("evpn_summary", "show evpn summary"),
        ("interfaces_irb", "show interfaces ip"),
    ]:
        print(f"  Running: {cmd}")
        post_swap_traces[cmd_name] = sess.show(cmd, timeout=15)

    results["phases"]["post_swap_traces"] = post_swap_traces

    connected_host = sess.host
    sess.close()

    # Phase 7: Analyze results
    print("\n" + "=" * 70)
    print("PHASE 7: ANALYSIS")
    print("=" * 70)

    cluster_trace = clean(post_swap_traces.get("cluster_mgr_irb", ""))
    system_events = clean(post_swap_traces.get("system_event_log", ""))
    fibmgrd_crit = clean(post_swap_traces.get("fibmgrd_crit", ""))

    down_events_irb1 = len(re.findall(r"irb1.*new_state down|Bringing down IRB irb1", cluster_trace))
    down_events_irb2 = len(re.findall(r"irb2.*new_state down|Bringing down IRB irb2", cluster_trace))
    up_events_irb1 = len(re.findall(r"irb1.*new_state up", cluster_trace))
    up_events_irb2 = len(re.findall(r"irb2.*new_state up", cluster_trace))

    sys_down_irb1 = len(re.findall(r"irb1.*down", system_events))
    sys_down_irb2 = len(re.findall(r"irb2.*down", system_events))
    sys_up_irb1 = len(re.findall(r"irb1.*up", system_events))
    sys_up_irb2 = len(re.findall(r"irb2.*up", system_events))

    has_crit = "CRIT" in fibmgrd_crit and "assert" in fibmgrd_crit.lower()

    analysis = {
        "cluster_mgr": {
            "irb1_down_events": down_events_irb1,
            "irb1_up_events": up_events_irb1,
            "irb2_down_events": down_events_irb2,
            "irb2_up_events": up_events_irb2,
        },
        "system_events": {
            "irb1_down": sys_down_irb1,
            "irb1_up": sys_up_irb1,
            "irb2_down": sys_down_irb2,
            "irb2_up": sys_up_irb2,
        },
        "fibmgrd_crash": has_crit,
    }

    results["phases"]["analysis"] = analysis

    print(f"\n  --- CLUSTER_MANAGER_PROTOCOLS (IRB flap events) ---")
    print(f"  irb1: {down_events_irb1} down, {up_events_irb1} up")
    print(f"  irb2: {down_events_irb2} down, {up_events_irb2} up")
    print(f"\n  --- SYSTEM-EVENT-LOG (IRB events) ---")
    print(f"  irb1: {sys_down_irb1} down, {sys_up_irb1} up")
    print(f"  irb2: {sys_down_irb2} down, {sys_up_irb2} up")
    print(f"\n  --- FIB_MANAGER CRASH ---")
    print(f"  CRIT assertion: {'YES - BUG PRESENT' if has_crit else 'NO - fix verified'}")

    if down_events_irb1 <= 1 and down_events_irb2 <= 1:
        verdict = "FIX CONFIRMED - IRB flaps once (single down/up cycle)"
    elif down_events_irb1 >= 2 or down_events_irb2 >= 2:
        verdict = "BUG PRESENT - IRB flaps twice (double down/up cycle)"
    else:
        verdict = "INCONCLUSIVE - check raw traces"

    if has_crit:
        verdict += " + FIB_MANAGER CRASH DETECTED"

    results["verdict"] = verdict
    print(f"\n  *** VERDICT: {verdict} ***")

    # Save results
    result_file = RESULT_DIR / f"irb_flap_test_{timestamp}.json"
    with open(result_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Results saved to: {result_file}")

    # Save raw traces as readable text
    trace_file = RESULT_DIR / f"irb_flap_traces_{timestamp}.txt"
    with open(trace_file, "w") as f:
        f.write(f"SW-211921 IRB Flap Twice Verification\n")
        f.write(f"Device: RR-SA-2 ({connected_host})\n")
        f.write(f"DNOS: 26.1.0.24_priv\n")
        f.write(f"Date: {timestamp}\n")
        f.write(f"Verdict: {verdict}\n")
        f.write(f"{'=' * 70}\n\n")

        for phase_name, phase_data in results["phases"].items():
            f.write(f"\n{'=' * 70}\n")
            f.write(f"PHASE: {phase_name}\n")
            f.write(f"{'=' * 70}\n\n")
            if isinstance(phase_data, dict):
                for key, val in phase_data.items():
                    f.write(f"--- {key} ---\n")
                    f.write(f"{val}\n\n")

    print(f"  Traces saved to: {trace_file}")

    # Phase 8: Cleanup
    print("\n" + "=" * 70)
    print("PHASE 8: Cleanup (remove test config)")
    print("=" * 70)
    cleanup_config = """no network-services evpn instance evpn_scale_1
no network-services evpn instance evpn_scale_2
no network-services vrf instance scale_1
no network-services vrf instance scale_2
no interfaces irb1
no interfaces irb2
no interfaces bundle-100.500
no interfaces bundle-100.501"""

    try:
        sess = DNOSSession()
        ok, errs = sess.apply_config(cleanup_config)
        if ok:
            print("  Cleanup DONE - all test config removed")
            results["phases"]["cleanup"] = {"status": "success"}
        else:
            print(f"  Cleanup FAILED: {errs}")
            results["phases"]["cleanup"] = {"status": "failed", "errors": errs}
        sess.close()
    except Exception as e:
        print(f"  Cleanup error: {e}")
        results["phases"]["cleanup"] = {"status": "error", "message": str(e)}

    return results


if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
