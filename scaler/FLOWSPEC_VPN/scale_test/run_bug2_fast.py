#!/usr/bin/env python3
"""BUG-2 Fast Reproduction: uses working apply_config + fast persistent show.

Config changes: apply_config (proven SSH paste, works reliably)
NPU checks: persistent SSH session with prompt detection (instant)
"""

import sys
import time
import re
import json
import paramiko
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), "w", buffering=1)
sys.path.insert(0, "/home/dn/SCALER/FLOWSPEC_VPN/scale_test")
from apply_config import apply_config, delete_flowspec_local

PE4_HOST = "100.64.6.82"
PE4_USER = "dnroot"
PE4_PASS = "dnroot"
BASELINE = 13
MC_COUNT = 100
EXPECTED = BASELINE + MC_COUNT
ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')
MAX_ROUNDS = 5


class FastShow:
    """Persistent SSH for show commands only. No sleeps — prompt detection."""

    def __init__(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(PE4_HOST, port=22, username=PE4_USER,
                            password=PE4_PASS, timeout=15, look_for_keys=False)
        self.shell = self.client.invoke_shell(width=250, height=50)
        self.shell.settimeout(1)
        time.sleep(1.5)
        self._drain()

    def _drain(self):
        buf = ""
        try:
            while True:
                buf += self.shell.recv(65536).decode("utf-8", errors="replace")
        except Exception:
            pass
        return buf

    def run(self, cmd, timeout=20):
        self._drain()
        self.shell.send(cmd + " | no-more\n")
        buf = ""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                chunk = self.shell.recv(65536).decode("utf-8", errors="replace")
                if chunk:
                    buf += chunk
                    clean = ANSI_RE.sub('', buf)
                    if re.search(r'PE-4[^\n]*#\s*$', clean):
                        return buf
            except Exception:
                pass
            time.sleep(0.05)
        return buf

    def close(self):
        try:
            self.client.close()
        except Exception:
            pass


def parse_npu(text):
    clean = ANSI_RE.sub('', text)
    out = {}
    for ncp_id in [6, 18]:
        m = re.search(rf'\|\s*{ncp_id}\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)/12000', clean)
        out[ncp_id] = (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else (0, 0, 0)
    return out


def poll_npu(show_ssh, target, timeout=30):
    prev = None
    deadline = time.time() + timeout
    while time.time() < deadline:
        npu = parse_npu(show_ssh.run("show system npu-resources resource-type flowspec"))
        i6 = npu[6][1]
        if i6 >= target:
            return npu, "ok"
        if prev is not None and prev == i6:
            return npu, "stuck"
        prev = i6
    return parse_npu(show_ssh.run("show system npu-resources resource-type flowspec")), "timeout"


def gen_config(action, prefix="S4"):
    lines = ["routing-policy", "  flowspec-local-policies", "    ipv4"]
    for i in range(1, MC_COUNT + 1):
        proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
        o3, o4 = divmod(i, 256)
        lines += [f"      match-class MC4-{prefix}-{i:04d}",
                  f"        dest-ip 10.4.{o3}.{o4}/32",
                  f"        protocol {proto}",
                  f"        dest-ports {3000 + i}", "      !"]
    lines.append(f"      policy POL-{prefix}")
    lines.append(f"        description bug2")
    for i in range(1, MC_COUNT + 1):
        lines += [f"        match-class MC4-{prefix}-{i:04d}",
                  f"          action {action}", "        !"]
    lines += ["      !", "    !", "  !", "!",
              "forwarding-options", "  flowspec-local", "    ipv4",
              f"      apply-policy-to-flowspec POL-{prefix}", "    !", "  !", "!"]
    return "\n".join(lines)


def gen_mixed(prefix="MIX"):
    lines = ["routing-policy", "  flowspec-local-policies", "    ipv4"]
    for i in range(1, MC_COUNT + 1):
        proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
        o3, o4 = divmod(i, 256)
        lines += [f"      match-class MC4-{prefix}-{i:04d}",
                  f"        dest-ip 10.5.{o3}.{o4}/32",
                  f"        protocol {proto}",
                  f"        dest-ports {4000 + i}", "      !"]
    lines.append(f"      policy POL-{prefix}")
    lines.append(f"        description bug2mix")
    for i in range(1, MC_COUNT + 1):
        action = "rate-limit 0" if i <= 50 else "rate-limit 1000"
        lines += [f"        match-class MC4-{prefix}-{i:04d}",
                  f"          action {action}", "        !"]
    lines += ["      !", "    !", "  !", "!",
              "forwarding-options", "  flowspec-local", "    ipv4",
              f"      apply-policy-to-flowspec POL-{prefix}", "    !", "  !", "!"]
    return "\n".join(lines)


ACTIONS = [
    ("rate-limit 0",         "D"),
    ("rate-limit 64",        "R64"),
    ("rate-limit 1000",      "R1K"),
    ("redirect-to-vrf ZULU", "VRF"),
    ("MIXED",                "MIX"),
    ("rate-limit 0",         "D2"),
    ("rate-limit 1000",      "R1K2"),
    ("MIXED",                "MIX2"),
]


def ts():
    return datetime.now().strftime("%H:%M:%S")


def main():
    print(f"\n{'='*70}")
    print(f"BUG-2 FAST REPRO (apply_config + fast persistent show)")
    print(f"{len(ACTIONS)} actions x {MAX_ROUNDS} rounds = {len(ACTIONS)*MAX_ROUNDS} cycles")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"{'='*70}\n")

    fshow = FastShow()
    results = {"test": "BUG-2 fast-v3", "started": datetime.now().isoformat(),
               "cycles": [], "leak_detected": False}

    # Clean
    print(f"[{ts()}] Clean...", end=" ", flush=True)
    delete_flowspec_local(commit=True)
    npu, _ = poll_npu(fshow, 0, timeout=10)
    print(f"NCP6={npu[6]}")

    cycle_num = 0
    leak = False

    for rnd in range(1, MAX_ROUNDS + 1):
        if leak:
            break
        for action_str, short in ACTIONS:
            if leak:
                break
            cycle_num += 1

            # DELETE (using proven apply_config method)
            delete_flowspec_local(commit=True)

            # LOAD
            cfg = gen_mixed(short) if action_str == "MIXED" else gen_config(action_str, short)
            ok, _ = apply_config(cfg, commit=True)
            if not ok:
                print(f"[{ts()}] C{cycle_num:02d} R{rnd}/{short:4s}: COMMIT FAIL")
                results["cycles"].append({"cycle": cycle_num, "action": action_str, "error": True})
                continue

            # FAST POLL via persistent SSH
            npu, how = poll_npu(fshow, EXPECTED, timeout=30)
            i6, i18 = npu[6][1], npu[18][1]
            local6 = i6 - BASELINE

            cd = {"cycle": cycle_num, "round": rnd, "action": action_str,
                  "inst6": i6, "local6": local6, "inst18": i18, "how": how}

            if i6 >= EXPECTED and i18 >= EXPECTED:
                print(f"[{ts()}] C{cycle_num:02d} R{rnd}/{short:4s}: OK {local6}/{MC_COUNT} ({how})")
            else:
                missing = MC_COUNT - local6
                print(f"[{ts()}] C{cycle_num:02d} R{rnd}/{short:4s}: *** LEAK *** {local6}/{MC_COUNT} (-{missing})")
                leak = True
                results["leak_detected"] = True
                results["leak_cycle"] = cycle_num
                results["leak_action"] = action_str

                print(f"  Capturing traces...")
                cd["evidence"] = {
                    "errors": ANSI_RE.sub('', fshow.run("show file ncp 6 traces datapath/wb_agent.flowspec | include ERROR"))[-3000:],
                    "warnings": ANSI_RE.sub('', fshow.run("show file ncp 6 traces datapath/wb_agent.flowspec | include WARNING"))[-3000:],
                    "reserves": ANSI_RE.sub('', fshow.run("show file ncp 6 traces datapath/wb_agent.flowspec | include ReserveQualifiers | tail 30"))[-3000:],
                    "reshuffles": ANSI_RE.sub('', fshow.run("show file ncp 6 traces datapath/wb_agent.flowspec | include Reshuffle | tail 20"))[-2000:],
                }
                local_pol = fshow.run("show flowspec-local-policies ncp 6", timeout=60)
                cd["not_installed"] = sum(1 for l in local_pol.split('\n') if 'Not Installed' in l)
                print(f"  Not Installed: {cd['not_installed']}")

            results["cycles"].append(cd)

    if not leak:
        print(f"\n[{ts()}] All {cycle_num} OK. Final: delete + load rate-limit 0...")
        delete_flowspec_local(commit=True)
        cfg = gen_config("rate-limit 0", "FIN")
        apply_config(cfg, commit=True)
        npu, how = poll_npu(fshow, EXPECTED, timeout=30)
        local6 = npu[6][1] - BASELINE
        print(f"  Final: {local6}/{MC_COUNT} ({how})")
        if npu[6][1] < EXPECTED:
            leak = True
            results["leak_detected"] = True
            results["leak_cycle"] = "final"

    fshow.close()
    results["finished"] = datetime.now().isoformat()
    results["total_cycles"] = cycle_num
    t0 = datetime.fromisoformat(results["started"])
    t1 = datetime.fromisoformat(results["finished"])

    print(f"\n{'='*70}")
    print(f"RESULT: {'LEAK' if leak else 'NO LEAK'} after {cycle_num} cycles ({(t1-t0).total_seconds():.0f}s)")
    if leak:
        print(f"  Cycle {results.get('leak_cycle')}, action={results.get('leak_action')}")
    print(f"{'='*70}\n")

    out = "/home/dn/SCALER/FLOWSPEC_VPN/scale_test/bug2_fast_results.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
