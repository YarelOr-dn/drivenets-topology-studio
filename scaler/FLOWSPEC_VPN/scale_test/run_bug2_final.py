#!/usr/bin/env python3
"""BUG-2 Reproduction: Comprehensive FlowSpec stress test.

Scenario-based testing with:
- Exact NPU state tracking after every operation
- Diverse hierarchy deletions (individual MC, policy, ipv4 container, fwd-options)
- Split commits, mid-batch commits, action modifications
- Anomaly detection (unexpected NPU values)
- 1-hour hard timeout
- Competing process detection and kill
"""

import paramiko
import time
import re
import json
import os
import subprocess
from datetime import datetime, timedelta

LOG = "/tmp/bug2_final.log"
CONTINUE_FROM = int(os.environ.get("CONTINUE_FROM", "0"))
_logf = open(LOG, "a" if CONTINUE_FROM else "w")

def log(msg=""):
    _logf.write(msg + "\n")
    _logf.flush()

PE4_HOST = "100.64.6.82"
PE4_USER = "dnroot"
PE4_PASS = "dnroot"
BASELINE_HW = 0
BASELINE_INSTALLED = 0
BASELINE_RECEIVED = 0
ANSI_RE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')
RUN_DURATION = timedelta(hours=1)


def ts():
    return datetime.now().strftime("%H:%M:%S")


def kill_competing():
    """Kill other python processes touching this script or the device."""
    my_pid = os.getpid()
    try:
        out = subprocess.check_output(
            ["pgrep", "-f", "run_bug2_final"], text=True).strip()
        for pid_s in out.splitlines():
            pid = int(pid_s.strip())
            if pid != my_pid and pid != os.getppid():
                log(f"  [killing competing PID {pid}]")
                os.kill(pid, 9)
    except (subprocess.CalledProcessError, Exception):
        pass


class DeviceSession:
    def __init__(self):
        self.client = None
        self.shell = None

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(PE4_HOST, port=22, username=PE4_USER,
                            password=PE4_PASS, timeout=30, look_for_keys=False)
        self.shell = None
        self._new_shell()

    def _new_shell(self):
        if self.shell:
            try:
                self.shell.close()
            except Exception:
                pass
        self.shell = self.client.invoke_shell(width=200, height=50)
        self.shell.settimeout(300)
        self._recv(2)

    def _recv(self, delay=0.5):
        time.sleep(delay)
        buf = ""
        while self.shell.recv_ready():
            buf += self.shell.recv(65536).decode("utf-8", errors="replace")
        return buf

    def _send(self, cmd, delay=0.5):
        self.shell.send(cmd + "\n")
        return self._recv(delay)

    def _ensure_config(self):
        try:
            self._send("configure", 0.5)
        except OSError:
            self._reconnect()
            self._send("configure", 0.5)
        self._send("rollback 0", 0.3)

    def paste_config(self, config_text):
        """Paste config lines into config mode (no commit)."""
        lines = config_text.strip().split("\n")
        for i in range(0, len(lines), 100):
            for line in lines[i:i+100]:
                self.shell.send(line + "\n")
            self._recv(0.15)
        self._recv(0.5)

    def commit(self, label=""):
        while self.shell.recv_ready():
            self.shell.recv(65536)
        self.shell.send("commit\n")
        return self._wait_commit(label=label)

    def paste_and_commit(self, config_text, label=""):
        self._ensure_config()
        self.paste_config(config_text)
        return self.commit(label=label)

    def _wait_commit(self, label=""):
        acc = ""
        for attempt in range(90):
            time.sleep(2)
            buf = ""
            while self.shell.recv_ready():
                buf += self.shell.recv(65536).decode("utf-8", errors="replace")
            acc += buf
            clean = ANSI_RE.sub("", acc)
            if "uncommitted changes" in clean or "yes/no/cancel" in clean:
                log(f"  COMMIT INTERRUPTED {label}")
                self._send("no", 0.5)
                self._send("configure", 0.5)
                self._send("rollback 0", 0.5)
                self.shell.send("commit\n")
                self._wait_simple_commit()
                self._send("end", 0.3)
                return False
            if "Commit complete" in clean or "ommit complete" in clean:
                return True
            if "Nothing to commit" in clean:
                return True
            if "COMMIT CHECK FAILED" in clean or "Unable to commit" in clean:
                log(f"  COMMIT FAILED {label}: {clean[-200:]}")
                self._send("rollback 0", 1)
                return False
            if attempt >= 1 and re.search(r'PE-4\(cfg\)#\s*$', clean):
                return True
            if attempt == 10:
                log(f"  COMMIT SLOW {label} (20s+)")
            if attempt == 30:
                log(f"  COMMIT VERY SLOW {label} (60s+)")
        log(f"  COMMIT TIMEOUT {label}")
        self._send("", 0.3)
        self._send("configure", 0.5)
        self._send("rollback 0", 0.5)
        self.shell.send("commit\n")
        self._wait_simple_commit()
        self._send("end", 0.3)
        return False

    def _wait_simple_commit(self):
        for _ in range(30):
            time.sleep(2)
            buf = ""
            while self.shell.recv_ready():
                buf += self.shell.recv(65536).decode("utf-8", errors="replace")
            clean = ANSI_RE.sub("", buf)
            if "ommit complete" in clean or "Nothing to commit" in clean:
                return True
            if re.search(r'PE-4\(cfg\)#\s*$', clean):
                return True
        return False

    def rollback_commit(self, label=""):
        self._send("rollback 0", 0.3)
        self.shell.send("commit\n")
        return self._wait_commit(label=label)

    def force_clean(self):
        """Hard cleanup: delete all flowspec + commit. Always returns to baseline."""
        try:
            self._send("end", 0.3)
        except OSError:
            self._reconnect()
        try:
            self._send("configure", 0.5)
        except OSError:
            self._reconnect()
            self._send("configure", 0.5)
        self.shell.send("no routing-policy flowspec-local-policies\n")
        self._recv(0.1)
        self.shell.send("no forwarding-options flowspec-local\n")
        self._recv(0.1)
        self.shell.send("commit\n")
        ok = self._wait_clean_commit()
        self._send("end", 0.3)
        for attempt in range(25):
            time.sleep(2)
            try:
                npu = self.check_npu()
            except Exception:
                self._reconnect()
                npu = self.check_npu()
            if npu[2] <= BASELINE_HW:
                return npu
            if attempt == 24:
                log(f"  WARNING: force_clean timeout hw={npu[2]}")
        return self.check_npu()

    def _wait_clean_commit(self):
        """Commit wait for cleanup operations - never rolls back on interruption."""
        acc = ""
        for attempt in range(60):
            time.sleep(2)
            buf = ""
            while self.shell.recv_ready():
                buf += self.shell.recv(65536).decode("utf-8", errors="replace")
            acc += buf
            clean = ANSI_RE.sub("", acc)
            if "uncommitted changes" in clean or "yes/no/cancel" in clean:
                self._send("yes", 1)
                acc = ""
                continue
            if "Commit complete" in clean or "ommit complete" in clean:
                return True
            if "Nothing to commit" in clean:
                return True
            if "COMMIT CHECK FAILED" in clean:
                log(f"  force_clean COMMIT FAILED: {clean[-200:]}")
                return False
            if attempt >= 1 and re.search(r'PE-4\(cfg\)#\s*$', clean):
                return True
        log(f"  force_clean COMMIT TIMEOUT")
        return False

    def send_cfg_lines(self, lines_list, label=""):
        """Enter config, send lines, commit, exit config. No rollback."""
        try:
            self._send("end", 0.3)
        except Exception:
            pass
        try:
            out = self._send("configure", 1.0)
        except OSError:
            self._reconnect()
            out = self._send("configure", 1.0)
        if "uncommitted" in out.lower():
            self._send("yes", 0.5)
            self._send("configure", 1.0)
        for line in lines_list:
            self.shell.send(line + "\n")
        self._recv(0.3)
        ok = self.commit(label=label)
        self._send("end", 0.3)
        return ok

    def exit_config(self):
        self._send("end", 0.3)

    def show(self, command):
        try:
            self._send("end", 0.3)
            self.shell.send(command + " | no-more\n")
        except OSError:
            self._reconnect()
            self.shell.send(command + " | no-more\n")
        time.sleep(1.5)
        out = ""
        for _ in range(8):
            time.sleep(0.5)
            while self.shell.recv_ready():
                out += self.shell.recv(65536).decode("utf-8", errors="replace")
            if out and not self.shell.recv_ready():
                break
        return out

    def _reconnect(self):
        log(f"  [reconnecting SSH]")
        try:
            self.client.close()
        except Exception:
            pass
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(PE4_HOST, port=22, username=PE4_USER,
                            password=PE4_PASS, timeout=30, look_for_keys=False)
        self._new_shell()

    def check_npu(self):
        raw = self.show("show system npu-resources resource-type flowspec")
        clean = ANSI_RE.sub('', raw)
        m = re.search(r'\|\s*6\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)/12000', clean)
        if m:
            return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        log(f"  WARNING: check_npu parse failed")
        return (0, 0, 0)

    def check_npu_raw(self):
        """Returns (recv, installed, hw) + raw NCP6 line."""
        raw = self.show("show system npu-resources resource-type flowspec")
        clean = ANSI_RE.sub('', raw)
        ncp6_line = ""
        for line in clean.splitlines():
            if '6' in line and '12000' in line:
                ncp6_line = line.strip()
                break
        m = re.search(r'\|\s*6\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)/12000', clean)
        if m:
            return (int(m.group(1)), int(m.group(2)), int(m.group(3))), ncp6_line
        return (0, 0, 0), ncp6_line

    def close(self):
        try:
            self.client.close()
        except Exception:
            pass


VRFS = [None, "ALPHA", "ZULU"]
ACTIONS = ["rate-limit 0", "drop", "rate-limit 1000000", "rate-limit 500"]
VRF_PATTERNS = {
    "none":       lambda i, n: None,
    "all_alpha":  lambda i, n: "ALPHA",
    "all_zulu":   lambda i, n: "ZULU",
    "mixed_az":   lambda i, n: "ALPHA" if i <= n // 2 else "ZULU",
    "third_each": lambda i, n: [None, "ALPHA", "ZULU"][i % 3],
    "alpha_some": lambda i, n: "ALPHA" if i % 4 == 0 else None,
    "zulu_some":  lambda i, n: "ZULU" if i % 5 == 0 else None,
    "swap":       lambda i, n: "ZULU" if i <= n // 2 else "ALPHA",
}


def gen_match_classes(count, prefix, base_ip2=10, vrf_pattern="none",
                      pktlen_some=False, heavy=False):
    """Generate match-class definitions. heavy=True adds extra match criteria for TCAM explosion."""
    vrf_fn = VRF_PATTERNS.get(vrf_pattern, VRF_PATTERNS["none"])
    lines = ["routing-policy", "  flowspec-local-policies", "    ipv4"]
    for i in range(1, count + 1):
        proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
        o3, o4 = divmod(i - 1, 254)
        ip = f"10.{base_ip2}.{o3}.{o4 + 1}"
        mc = [f"      match-class MC4-{prefix}-{i:04d}",
              f"        dest-ip {ip}/32",
              f"        protocol {proto}",
              f"        dest-ports {3000 + (i % 60000)}"]
        vrf = vrf_fn(i, count)
        if vrf:
            mc.append(f"        vrf {vrf}")
        if pktlen_some and i % 20 == 0:
            mc.append(f"        packet-length 64-1500")
        if heavy:
            src_o3, src_o4 = divmod(i - 1, 254)
            mc.append(f"        src-ip 172.16.{src_o3}.{src_o4 + 1}/32")
            mc.append(f"        src-ports {5000 + (i % 60000)}")
            if i % 3 == 0:
                mc.append(f"        packet-length 64-1500")
            if i % 5 == 0:
                mc.append(f"        fragment is-fragment")
        mc.append("      !")
        lines.extend(mc)
    lines += ["    !", "  !", "!"]
    return "\n".join(lines)


def gen_policy(count, prefix, action="rate-limit 0"):
    """Generate only the policy (references existing match-classes)."""
    lines = ["routing-policy", "  flowspec-local-policies", "    ipv4",
             f"      policy POL-{prefix}", f"        description stress"]
    for i in range(1, count + 1):
        act = action if isinstance(action, str) else action[i % len(action)]
        lines += [f"        match-class MC4-{prefix}-{i:04d}",
                  f"          action {act}", "        !"]
    lines += ["      !", "    !", "  !", "!"]
    return "\n".join(lines)


def gen_fwd_options(prefix):
    """Generate only the forwarding-options apply."""
    return "\n".join([
        "forwarding-options", "  flowspec-local", "    ipv4",
        f"      apply-policy-to-flowspec POL-{prefix}",
        "    !", "  !", "!"])


def gen_full(count, prefix, base_ip2=10, action="rate-limit 0",
             vrf_pattern="none", pktlen_some=False, heavy=False):
    """Generate complete config: match-classes + policy + fwd-options."""
    mc = gen_match_classes(count, prefix, base_ip2, vrf_pattern, pktlen_some, heavy)
    pol = gen_policy(count, prefix, action)
    fwd = gen_fwd_options(prefix)
    return mc + "\n" + pol + "\n" + fwd


def gen_probe(pid):
    """8 pktlen-range (TCAM amp) + 490 simple rules."""
    lines = ["routing-policy", "  flowspec-local-policies", "    ipv4"]
    for i in range(1, 9):
        proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
        lines += [f"      match-class MC4-P{pid}-K{i:04d}",
                  f"        dest-ip 10.99.{i}.{(pid % 250) + 1}/32",
                  f"        protocol {proto}",
                  f"        dest-ports {9000 + i}",
                  f"        packet-length 64-1500", "      !"]
    for i in range(1, 491):
        proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
        o3, o4 = divmod(i - 1, 254)
        lines += [f"      match-class MC4-P{pid}-S{i:04d}",
                  f"        dest-ip 10.88.{o3}.{o4 + 1}/32",
                  f"        protocol {proto}",
                  f"        dest-ports {3000 + i}", "      !"]
    lines.append(f"      policy POL-P{pid}")
    lines.append(f"        description probe")
    for i in range(1, 9):
        lines += [f"        match-class MC4-P{pid}-K{i:04d}",
                  f"          action rate-limit 0", "        !"]
    for i in range(1, 491):
        lines += [f"        match-class MC4-P{pid}-S{i:04d}",
                  f"          action rate-limit 0", "        !"]
    lines += ["      !", "    !", "  !", "!",
              "forwarding-options", "  flowspec-local", "    ipv4",
              f"      apply-policy-to-flowspec POL-P{pid}", "    !", "  !", "!"]
    return "\n".join(lines)


def verify_npu(dev, expect_label, expected_rules=None):
    """Check NPU state, wait for convergence, log the raw line."""
    time.sleep(2)
    npu, raw = dev.check_npu_raw()
    if expected_rules is not None and expected_rules > 0:
        target = BASELINE_INSTALLED + expected_rules
        for _ in range(10):
            if npu[1] >= target - 2:
                break
            time.sleep(2)
            npu, raw = dev.check_npu_raw()
    elif expected_rules == 0:
        for _ in range(10):
            if npu[2] <= BASELINE_HW + 2:
                break
            time.sleep(2)
            npu, raw = dev.check_npu_raw()
    log(f"    [{expect_label}] recv={npu[0]} inst={npu[1]} hw={npu[2]}/12000  | {raw}")
    return npu


def check_anomaly(npu, expected_rules, label, anomalies):
    """Flag if NPU state doesn't match expectations."""
    expected_recv = BASELINE_RECEIVED + expected_rules
    expected_inst_min = BASELINE_INSTALLED + expected_rules - 2  # allow small margin
    expected_inst_max = BASELINE_INSTALLED + expected_rules + 2

    issues = []
    if expected_rules == 0:
        if npu[2] > BASELINE_HW + 5:
            issues.append(f"hw={npu[2]} expected ~{BASELINE_HW}")
        if npu[1] > BASELINE_INSTALLED + 2:
            issues.append(f"installed={npu[1]} expected ~{BASELINE_INSTALLED}")
    else:
        if npu[0] < BASELINE_RECEIVED:
            issues.append(f"received={npu[0]} below baseline {BASELINE_RECEIVED}")

    if issues:
        msg = f"ANOMALY [{label}]: {', '.join(issues)} | npu={npu}"
        log(f"  *** {msg}")
        anomalies.append({"ts": ts(), "label": label, "npu": npu,
                          "expected_rules": expected_rules, "issues": issues})
        return True
    return False


def run_probe(dev, pid, results):
    """Sensitive probe: detects m_reserved leak >= 1."""
    log(f"\n  --- PROBE #{pid} ---")
    dev.paste_and_commit(gen_probe(pid), label=f"probe-{pid}")
    dev.exit_config()

    for _ in range(20):
        time.sleep(3)
        npu = dev.check_npu()
        if npu[1] >= BASELINE_INSTALLED + 490:
            break
    local = npu[1] - BASELINE_INSTALLED
    simple = max(0, local - 8)
    leaked = max(0, 490 - simple)

    npu, raw = dev.check_npu_raw()
    log(f"  NPU-RAW: {raw}")
    results["probes"].append({"probe": pid, "npu6": npu, "simple": simple, "leaked": leaked})

    if leaked > 0:
        log(f"  *** LEAK *** simple={simple}/490 leaked={leaked} hw={npu[2]}")
        results["leak_detected"] = True
        results["leak_amount"] = leaked
        results["evidence"] = {
            "npu": raw,
            "traces": dev.show("show file ncp 6 traces datapath/wb_agent.flowspec | tail 50"),
        }
        return leaked
    log(f"  OK: {simple}/490 hw={npu[2]}/12000")
    dev.force_clean()
    return 0


# ── SCENARIOS ──

def scenario_load_rollback(dev, c, anomalies):
    """Paste rules WITHOUT committing, then rollback 0 to discard uncommitted config.
    Also tests: commit, then force_clean to remove committed config."""
    n = [50, 100, 200, 300][c % 4]
    pat = list(VRF_PATTERNS.keys())[c % len(VRF_PATTERNS)]
    act = ACTIONS[c % len(ACTIONS)]
    pfx = f"S{c:04d}"
    log(f"[{ts()}] #{c} LOAD_ROLLBACK n={n} vrf={pat} act={act}")

    dev._ensure_config()
    dev.paste_config(gen_full(n, pfx, base_ip2=10+(c%40), action=act,
                              vrf_pattern=pat))
    dev._send("rollback 0", 0.5)
    dev.commit(label=f"s{c}-rb-uncommitted")
    dev.exit_config()
    npu = verify_npu(dev, "after-rollback-uncommitted", 0)
    check_anomaly(npu, 0, f"#{c} post-rollback-uncommitted", anomalies)

    dev.paste_and_commit(gen_full(n, pfx, base_ip2=10+(c%40), action=act,
                                  vrf_pattern=pat), label=f"s{c}-commit")
    npu = verify_npu(dev, "after-commit", n)
    dev.force_clean()
    npu = verify_npu(dev, "after-clean", 0)
    check_anomaly(npu, 0, f"#{c} post-clean", anomalies)


def scenario_load_full_delete(dev, c, anomalies):
    """Load rules then delete both hierarchies."""
    n = [100, 200, 400][c % 3]
    pat = list(VRF_PATTERNS.keys())[c % len(VRF_PATTERNS)]
    act = ACTIONS[c % len(ACTIONS)]
    pfx = f"S{c:04d}"
    log(f"[{ts()}] #{c} LOAD_FULL_DELETE n={n} vrf={pat} act={act}")
    dev.paste_and_commit(gen_full(n, pfx, base_ip2=10+(c%40), action=act,
                                  vrf_pattern=pat), label=f"s{c}-load")
    npu = verify_npu(dev, "after-load", n)
    dev.force_clean()
    npu = verify_npu(dev, "after-clean", 0)
    check_anomaly(npu, 0, f"#{c} post-full-delete", anomalies)


def scenario_delete_fwd_then_pol(dev, c, anomalies):
    """Load, delete fwd-options (rules drain), then delete routing-policy."""
    n = [100, 200][c % 2]
    pat = list(VRF_PATTERNS.keys())[c % len(VRF_PATTERNS)]
    pfx = f"S{c:04d}"
    log(f"[{ts()}] #{c} DEL_FWD_THEN_POL n={n} vrf={pat}")
    dev.paste_and_commit(gen_full(n, pfx, base_ip2=10+(c%40),
                                  vrf_pattern=pat), label=f"s{c}-load")
    npu = verify_npu(dev, "after-load", n)

    dev.send_cfg_lines(["no forwarding-options flowspec-local"], label=f"s{c}-del-fwd")
    time.sleep(3)
    npu = verify_npu(dev, "after-del-fwd")

    dev.send_cfg_lines(["no routing-policy flowspec-local-policies"], label=f"s{c}-del-pol")
    time.sleep(2)
    npu = verify_npu(dev, "after-del-pol", 0)
    check_anomaly(npu, 0, f"#{c} post-fwd-then-pol", anomalies)


def scenario_delete_pol_then_fwd(dev, c, anomalies):
    """Load, delete routing-policy first, then fwd-options."""
    n = [100, 200, 300][c % 3]
    pat = list(VRF_PATTERNS.keys())[c % len(VRF_PATTERNS)]
    pfx = f"S{c:04d}"
    log(f"[{ts()}] #{c} DEL_POL_THEN_FWD n={n} vrf={pat}")
    dev.paste_and_commit(gen_full(n, pfx, base_ip2=10+(c%40),
                                  vrf_pattern=pat), label=f"s{c}-load")
    npu = verify_npu(dev, "after-load", n)

    dev.send_cfg_lines(["no routing-policy flowspec-local-policies"], label=f"s{c}-del-pol")
    time.sleep(2)
    npu = verify_npu(dev, "after-del-pol")

    dev.send_cfg_lines(["no forwarding-options flowspec-local"], label=f"s{c}-del-fwd")
    time.sleep(3)
    npu = verify_npu(dev, "after-del-fwd", 0)
    check_anomaly(npu, 0, f"#{c} post-pol-then-fwd", anomalies)


def scenario_delete_ipv4_container(dev, c, anomalies):
    """Load rules then delete the ipv4 container inside flowspec-local-policies."""
    n = [100, 150][c % 2]
    pfx = f"S{c:04d}"
    log(f"[{ts()}] #{c} DEL_IPV4_CONTAINER n={n}")
    dev.paste_and_commit(gen_full(n, pfx, base_ip2=10+(c%40)), label=f"s{c}-load")
    npu = verify_npu(dev, "after-load", n)

    dev.send_cfg_lines([
        "no forwarding-options flowspec-local",
        "no routing-policy flowspec-local-policies ipv4",
    ], label=f"s{c}-del-ipv4")
    time.sleep(3)
    npu = verify_npu(dev, "after-del-ipv4", 0)
    dev.force_clean()
    npu = verify_npu(dev, "after-force-clean", 0)
    check_anomaly(npu, 0, f"#{c} post-del-ipv4", anomalies)


def scenario_delete_individual_mc(dev, c, anomalies):
    """Load rules, then delete specific match-classes one by one."""
    n = 50
    pfx = f"S{c:04d}"
    log(f"[{ts()}] #{c} DEL_INDIVIDUAL_MC n={n}")
    dev.paste_and_commit(gen_full(n, pfx, base_ip2=10+(c%40)), label=f"s{c}-load")
    npu = verify_npu(dev, "after-load", n)

    del_lines = ["routing-policy", "  flowspec-local-policies", "    ipv4"]
    for i in [1, 10, 25, 50]:
        del_lines.append(f"      no match-class MC4-{pfx}-{i:04d}")
    del_lines += ["    !", "  !", "!"]
    dev.send_cfg_lines(del_lines, label=f"s{c}-del-mc")
    npu = verify_npu(dev, "after-del-4mc")

    dev.force_clean()
    npu = verify_npu(dev, "after-clean", 0)
    check_anomaly(npu, 0, f"#{c} post-del-individual-mc", anomalies)


def scenario_split_commit(dev, c, anomalies):
    """Load half the rules, commit, then load the rest and commit again."""
    n = [100, 200][c % 2]
    half = n // 2
    pfx = f"S{c:04d}"
    pat = list(VRF_PATTERNS.keys())[c % len(VRF_PATTERNS)]
    log(f"[{ts()}] #{c} SPLIT_COMMIT n={n} (2x{half}) vrf={pat}")

    mc1 = gen_match_classes(half, pfx, base_ip2=10+(c%40), vrf_pattern=pat)
    pol1 = gen_policy(half, pfx)
    fwd1 = gen_fwd_options(pfx)
    dev.paste_and_commit(mc1 + "\n" + pol1 + "\n" + fwd1, label=f"s{c}-half1")
    npu = verify_npu(dev, "after-half1", half)

    mc2_lines = ["routing-policy", "  flowspec-local-policies", "    ipv4"]
    for i in range(half + 1, n + 1):
        proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
        o3, o4 = divmod(i - 1, 254)
        ip = f"10.{10+(c%40)}.{o3}.{o4 + 1}"
        mc2_lines += [f"      match-class MC4-{pfx}-{i:04d}",
                      f"        dest-ip {ip}/32",
                      f"        protocol {proto}",
                      f"        dest-ports {3000 + (i % 60000)}", "      !"]
    mc2_lines += ["    !", "  !", "!"]
    pol2_lines = ["routing-policy", "  flowspec-local-policies", "    ipv4",
                  f"      policy POL-{pfx}"]
    for i in range(half + 1, n + 1):
        pol2_lines += [f"        match-class MC4-{pfx}-{i:04d}",
                       f"          action rate-limit 0", "        !"]
    pol2_lines += ["      !", "    !", "  !", "!"]
    dev.paste_and_commit("\n".join(mc2_lines) + "\n" + "\n".join(pol2_lines),
                         label=f"s{c}-half2")
    npu = verify_npu(dev, "after-half2", n)

    dev.force_clean()
    npu = verify_npu(dev, "after-clean", 0)
    check_anomaly(npu, 0, f"#{c} post-split-commit", anomalies)


def scenario_modify_action(dev, c, anomalies):
    """Load rules with one action, then modify the action on all rules."""
    n = [100, 150][c % 2]
    pfx = f"S{c:04d}"
    log(f"[{ts()}] #{c} MODIFY_ACTION n={n}")
    dev.paste_and_commit(gen_full(n, pfx, base_ip2=10+(c%40), action="rate-limit 0"),
                         label=f"s{c}-load")
    npu = verify_npu(dev, "after-load-rl0", n)

    new_pol = gen_policy(n, pfx, action="drop")
    dev.paste_and_commit(new_pol, label=f"s{c}-modify")
    npu = verify_npu(dev, "after-modify-drop", n)

    new_pol2 = gen_policy(n, pfx, action="rate-limit 1000000")
    dev.paste_and_commit(new_pol2, label=f"s{c}-modify2")
    npu = verify_npu(dev, "after-modify-rl1m", n)

    dev.force_clean()
    npu = verify_npu(dev, "after-clean", 0)
    check_anomaly(npu, 0, f"#{c} post-modify-action", anomalies)


def scenario_overwrite_different_rules(dev, c, anomalies):
    """Load set A, commit, then load set B (different IPs) overwriting."""
    n = [100, 200][c % 2]
    pfx_a = f"S{c:04d}A"
    pfx_b = f"S{c:04d}B"
    log(f"[{ts()}] #{c} OVERWRITE_RULES n={n}")
    dev.paste_and_commit(gen_full(n, pfx_a, base_ip2=10+(c%40), action="rate-limit 0"),
                         label=f"s{c}-setA")
    npu = verify_npu(dev, "after-setA", n)

    dev.paste_and_commit(gen_full(n, pfx_b, base_ip2=20+(c%40), action="drop"),
                         label=f"s{c}-setB")
    npu = verify_npu(dev, "after-setB")

    dev.force_clean()
    npu = verify_npu(dev, "after-clean", 0)
    check_anomaly(npu, 0, f"#{c} post-overwrite", anomalies)


def scenario_pktlen_stress(dev, c, anomalies):
    """Load rules with packet-length on every rule (TCAM amplifier)."""
    n = 8
    pfx = f"S{c:04d}"
    log(f"[{ts()}] #{c} PKTLEN_STRESS n={n} (all pktlen)")
    dev.paste_and_commit(gen_full(n, pfx, base_ip2=10+(c%40), pktlen_some=False,
                                  action="rate-limit 0"),
                         label=f"s{c}-load")
    npu = verify_npu(dev, "after-load")

    dev.force_clean()
    npu = verify_npu(dev, "after-clean", 0)
    check_anomaly(npu, 0, f"#{c} post-pktlen-stress", anomalies)


def scenario_multi_policy(dev, c, anomalies):
    """Load 2 policies referencing different match-classes, same commit."""
    n = 50
    pfx_a = f"S{c:04d}A"
    pfx_b = f"S{c:04d}B"
    pat_a = list(VRF_PATTERNS.keys())[c % len(VRF_PATTERNS)]
    pat_b = list(VRF_PATTERNS.keys())[(c+3) % len(VRF_PATTERNS)]
    log(f"[{ts()}] #{c} MULTI_POLICY 2x{n} vrf={pat_a}+{pat_b}")
    cfg_a = gen_full(n, pfx_a, base_ip2=10+(c%40), action="rate-limit 0",
                     vrf_pattern=pat_a)
    cfg_b = gen_full(n, pfx_b, base_ip2=20+(c%40), action="drop",
                     vrf_pattern=pat_b)
    dev.paste_and_commit(cfg_a + "\n" + cfg_b, label=f"s{c}-2pol")
    npu = verify_npu(dev, "after-2pol")

    dev.force_clean()
    npu = verify_npu(dev, "after-clean", 0)
    check_anomaly(npu, 0, f"#{c} post-multi-policy", anomalies)


def scenario_delete_readd(dev, c, anomalies):
    """Load rules, commit, delete all, re-add different rules, commit."""
    n = [100, 150][c % 2]
    pfx1 = f"S{c:04d}X"
    pfx2 = f"S{c:04d}Y"
    log(f"[{ts()}] #{c} DELETE_READD n={n}")
    dev.paste_and_commit(gen_full(n, pfx1, base_ip2=10+(c%40)), label=f"s{c}-first")
    npu = verify_npu(dev, "after-first", n)

    dev._ensure_config()
    dev.shell.send("no routing-policy flowspec-local-policies\n")
    dev._recv(0.1)
    dev.shell.send("no forwarding-options flowspec-local\n")
    dev._recv(0.1)
    dev.paste_config(gen_full(n, pfx2, base_ip2=20+(c%40), action="drop"))
    ok = dev.commit(label=f"s{c}-del-readd")
    dev.exit_config()
    npu = verify_npu(dev, "after-del-readd", n)

    dev.force_clean()
    npu = verify_npu(dev, "after-clean", 0)
    check_anomaly(npu, 0, f"#{c} post-delete-readd", anomalies)


def scenario_vrf_change(dev, c, anomalies):
    """Load rules with VRF ALPHA, then change them to VRF ZULU."""
    n = [50, 100][c % 2]
    pfx = f"S{c:04d}"
    log(f"[{ts()}] #{c} VRF_CHANGE n={n} ALPHA->ZULU")
    dev.paste_and_commit(gen_full(n, pfx, base_ip2=10+(c%40), vrf_pattern="all_alpha"),
                         label=f"s{c}-alpha")
    npu = verify_npu(dev, "after-alpha", n)

    mc_zulu = gen_match_classes(n, pfx, base_ip2=10+(c%40), vrf_pattern="all_zulu")
    dev.paste_and_commit(mc_zulu, label=f"s{c}-to-zulu")
    npu = verify_npu(dev, "after-zulu", n)

    mc_none = gen_match_classes(n, pfx, base_ip2=10+(c%40), vrf_pattern="none")
    dev.paste_and_commit(mc_none, label=f"s{c}-to-none")
    npu = verify_npu(dev, "after-no-vrf", n)

    dev.force_clean()
    npu = verify_npu(dev, "after-clean", 0)
    check_anomaly(npu, 0, f"#{c} post-vrf-change", anomalies)


def scenario_heavy_match_classes(dev, c, anomalies):
    """Load rules with complex match criteria (src-ip, src-ports, pktlen, fragment).
    Each heavy rule consumes many more TCAM entries due to cross-product expansion."""
    n = [20, 30, 50][c % 3]
    pfx = f"S{c:04d}"
    pat = list(VRF_PATTERNS.keys())[c % len(VRF_PATTERNS)]
    log(f"[{ts()}] #{c} HEAVY_MC n={n} vrf={pat} (src-ip+src-ports+pktlen+fragment)")
    mc = gen_match_classes(n, pfx, base_ip2=10+(c%40), vrf_pattern=pat, heavy=True)
    pol = gen_policy(n, pfx, action="rate-limit 0")
    fwd = gen_fwd_options(pfx)
    dev.paste_and_commit(mc + "\n" + pol + "\n" + fwd, label=f"s{c}-heavy")
    npu = verify_npu(dev, "after-heavy-load", n)
    hw_per_rule = npu[2] / max(n, 1)
    log(f"    TCAM amplification: {hw_per_rule:.1f}x per rule ({npu[2]} hw for {n} rules)")
    dev.force_clean()
    npu = verify_npu(dev, "after-clean", 0)
    check_anomaly(npu, 0, f"#{c} post-heavy-mc", anomalies)


def scenario_sequential_stacking(dev, c, anomalies):
    """Load multiple batches on top of each other without cleanup.
    Forces continuous priority allocation and potential reshuffles."""
    batch_n = [50, 100][c % 2]
    num_batches = 5
    log(f"[{ts()}] #{c} SEQ_STACK {num_batches}x{batch_n} rules stacked")
    total = 0
    for b in range(1, num_batches + 1):
        pfx = f"S{c:04d}B{b}"
        pat = list(VRF_PATTERNS.keys())[(c + b) % len(VRF_PATTERNS)]
        act = ACTIONS[(c + b) % len(ACTIONS)]
        dev.paste_and_commit(
            gen_full(batch_n, pfx, base_ip2=10+((c*10+b) % 40), action=act,
                     vrf_pattern=pat),
            label=f"s{c}-stk{b}")
        total += batch_n
    npu = verify_npu(dev, f"after-{num_batches}-stacks")
    log(f"    Stacked {total} rules across {num_batches} policies")
    dev.force_clean()
    npu = verify_npu(dev, "after-clean", 0)
    check_anomaly(npu, 0, f"#{c} post-seq-stack", anomalies)


def scenario_near_capacity(dev, c, anomalies):
    """Fill TCAM to near-capacity with pktlen amplifiers, then add/delete at the edge."""
    log(f"[{ts()}] #{c} NEAR_CAPACITY filling TCAM to ~11,900/12,000")
    pfx = f"S{c:04d}"
    lines = ["routing-policy", "  flowspec-local-policies", "    ipv4"]
    for i in range(1, 9):
        proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
        lines += [f"      match-class MC4-{pfx}-K{i:04d}",
                  f"        dest-ip 10.99.{i}.{(c % 250) + 1}/32",
                  f"        protocol {proto}",
                  f"        dest-ports {9000 + i}",
                  f"        packet-length 64-1500", "      !"]
    for i in range(1, 401):
        proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
        o3, o4 = divmod(i - 1, 254)
        lines += [f"      match-class MC4-{pfx}-S{i:04d}",
                  f"        dest-ip 10.88.{o3}.{o4 + 1}/32",
                  f"        protocol {proto}",
                  f"        dest-ports {3000 + i}", "      !"]
    lines += [f"      policy POL-{pfx}", f"        description near-cap"]
    for i in range(1, 9):
        lines += [f"        match-class MC4-{pfx}-K{i:04d}",
                  f"          action rate-limit 0", "        !"]
    for i in range(1, 401):
        lines += [f"        match-class MC4-{pfx}-S{i:04d}",
                  f"          action rate-limit 0", "        !"]
    lines += ["      !", "    !", "  !", "!",
              "forwarding-options", "  flowspec-local", "    ipv4",
              f"      apply-policy-to-flowspec POL-{pfx}", "    !", "  !", "!"]
    dev.paste_and_commit("\n".join(lines), label=f"s{c}-fill")
    npu = verify_npu(dev, "after-fill")
    log(f"    Filled to {npu[2]}/12000")

    extra_pfx = f"S{c:04d}X"
    extra = gen_full(10, extra_pfx, base_ip2=50+(c%10), action="drop")
    dev.paste_and_commit(extra, label=f"s{c}-edge-add")
    npu = verify_npu(dev, "after-edge-add")
    log(f"    After +10 at edge: {npu[2]}/12000")

    dev.send_cfg_lines([
        "routing-policy", "  flowspec-local-policies", "    ipv4",
        f"      no match-class MC4-{extra_pfx}-0001",
        f"      no match-class MC4-{extra_pfx}-0005",
        f"      no match-class MC4-{extra_pfx}-0010",
        "    !", "  !", "!",
    ], label=f"s{c}-edge-del")
    npu = verify_npu(dev, "after-edge-del")
    log(f"    After -3 at edge: {npu[2]}/12000")

    dev.force_clean()
    npu = verify_npu(dev, "after-clean", 0)
    check_anomaly(npu, 0, f"#{c} post-near-cap", anomalies)


def scenario_delete_middle(dev, c, anomalies):
    """Load 300 rules, delete rules 100-200 from the middle, creating TCAM fragmentation."""
    n = 300
    pfx = f"S{c:04d}"
    log(f"[{ts()}] #{c} DELETE_MIDDLE n={n} (delete 100-200)")
    dev.paste_and_commit(gen_full(n, pfx, base_ip2=10+(c%40)), label=f"s{c}-load")
    npu = verify_npu(dev, "after-load", n)

    del_lines = ["routing-policy", "  flowspec-local-policies", "    ipv4"]
    for i in range(100, 201):
        del_lines.append(f"      no match-class MC4-{pfx}-{i:04d}")
    del_lines += ["    !", "  !", "!"]
    dev.send_cfg_lines(del_lines, label=f"s{c}-del-mid")
    npu = verify_npu(dev, "after-del-middle")
    log(f"    After deleting 101 middle rules: {npu[1]} installed, {npu[2]} hw")

    dev.force_clean()
    npu = verify_npu(dev, "after-clean", 0)
    check_anomaly(npu, 0, f"#{c} post-delete-middle", anomalies)


def scenario_max_batch(dev, c, anomalies):
    """Load maximum rules in a single commit to force large priority allocation."""
    n = [1000, 1500, 2000][c % 3]
    pfx = f"S{c:04d}"
    pat = list(VRF_PATTERNS.keys())[c % len(VRF_PATTERNS)]
    log(f"[{ts()}] #{c} MAX_BATCH n={n} vrf={pat}")
    dev.paste_and_commit(gen_full(n, pfx, base_ip2=10+(c%40), vrf_pattern=pat),
                         label=f"s{c}-maxbatch")
    npu = verify_npu(dev, "after-max-load", n)
    dev.force_clean()
    npu = verify_npu(dev, "after-clean", 0)
    check_anomaly(npu, 0, f"#{c} post-max-batch", anomalies)


def scenario_rapid_micro(dev, c, anomalies):
    """Rapid micro-cycles: 10 rules load/delete repeated 20 times. Maximizes commit count."""
    log(f"[{ts()}] #{c} RAPID_MICRO 20x10-rule cycles")
    for micro in range(1, 21):
        pfx = f"S{c:04d}M{micro:02d}"
        dev.paste_and_commit(gen_full(10, pfx, base_ip2=10+((c*20+micro)%40),
                                      action=ACTIONS[micro % len(ACTIONS)]),
                             label=f"s{c}-m{micro}")
        dev.force_clean()
    npu = verify_npu(dev, "after-rapid-clean", 0)
    check_anomaly(npu, 0, f"#{c} post-rapid-micro", anomalies)
    log(f"    Completed 20 micro-cycles")


def scenario_stack_then_partial_delete(dev, c, anomalies):
    """Stack 3 policies, delete the middle one, re-add a different one."""
    n = 50
    log(f"[{ts()}] #{c} STACK_PARTIAL_DEL 3x{n} policies, delete middle, re-add")
    for b in range(1, 4):
        pfx = f"S{c:04d}P{b}"
        dev.paste_and_commit(gen_full(n, pfx, base_ip2=10+(b*5)+(c%20),
                                      action=ACTIONS[b % len(ACTIONS)]),
                             label=f"s{c}-p{b}")
    npu = verify_npu(dev, "after-3-policies")

    mid_pfx = f"S{c:04d}P2"
    dev.send_cfg_lines([
        "routing-policy", "  flowspec-local-policies", "    ipv4",
        f"      no policy POL-{mid_pfx}",
    ] + [f"      no match-class MC4-{mid_pfx}-{i:04d}" for i in range(1, n+1)]
    + ["    !", "  !", "!",
       "forwarding-options", "  flowspec-local", "    ipv4",
       f"      no apply-policy-to-flowspec POL-{mid_pfx}", "    !", "  !", "!"],
    label=f"s{c}-del-mid-pol")
    npu = verify_npu(dev, "after-del-mid-policy")

    new_pfx = f"S{c:04d}P4"
    dev.paste_and_commit(gen_full(n, new_pfx, base_ip2=35+(c%10),
                                  action="drop", vrf_pattern="all_zulu"),
                         label=f"s{c}-readd")
    npu = verify_npu(dev, "after-readd")

    dev.force_clean()
    npu = verify_npu(dev, "after-clean", 0)
    check_anomaly(npu, 0, f"#{c} post-stack-partial-del", anomalies)


SCENARIOS = [
    scenario_load_rollback,
    scenario_load_full_delete,
    scenario_delete_fwd_then_pol,
    scenario_delete_pol_then_fwd,
    scenario_delete_ipv4_container,
    scenario_delete_individual_mc,
    scenario_heavy_match_classes,
    scenario_split_commit,
    scenario_modify_action,
    scenario_overwrite_different_rules,
    scenario_pktlen_stress,
    scenario_multi_policy,
    scenario_delete_readd,
    scenario_vrf_change,
    scenario_sequential_stacking,
    scenario_near_capacity,
    scenario_delete_middle,
    scenario_max_batch,
    scenario_rapid_micro,
    scenario_stack_then_partial_delete,
]


def main():
    log(f"\n{'#'*60}")
    log(f"  BUG-2 COMPREHENSIVE STRESS TEST")
    log(f"  {datetime.now().isoformat()}")
    log(f"  Duration: {RUN_DURATION}")
    log(f"  Scenarios: {len(SCENARIOS)}")
    log(f"{'#'*60}\n")

    kill_competing()

    results = {"started": datetime.now().isoformat(),
               "probes": [], "anomalies": [], "leak_detected": False}

    global BASELINE_HW, BASELINE_INSTALLED, BASELINE_RECEIVED

    dev = DeviceSession()
    dev.connect()
    log(f"[{ts()}] Connected to PE-4")

    dev.force_clean()
    time.sleep(5)
    npu = verify_npu(dev, "detecting-baseline", 0)
    BASELINE_RECEIVED = npu[0]
    BASELINE_INSTALLED = npu[1]
    BASELINE_HW = npu[2]
    log(f"  AUTO-BASELINE: recv={BASELINE_RECEIVED} inst={BASELINE_INSTALLED} hw={BASELINE_HW}")

    pn = 0
    if not CONTINUE_FROM:
        if run_probe(dev, pn, results):
            log("Device already dirty! Aborting.")
            dev.close()
            return
    else:
        log(f"  CONTINUING from cycle {CONTINUE_FROM}, skipping initial probe")

    deadline = datetime.now() + RUN_DURATION
    cycle = CONTINUE_FROM
    anomalies = []
    PROBE_EVERY = 20

    log(f"\n[{ts()}] Starting scenario cycles until {deadline.strftime('%H:%M:%S')}")
    log(f"  {len(SCENARIOS)} scenarios, probe every {PROBE_EVERY}\n")

    while datetime.now() < deadline:
        cycle += 1
        scenario_fn = SCENARIOS[cycle % len(SCENARIOS)]

        kill_competing()

        try:
            scenario_fn(dev, cycle, anomalies)
        except Exception as e:
            log(f"  EXCEPTION in #{cycle} {scenario_fn.__name__}: {e}")
            try:
                dev._reconnect()
                dev.force_clean()
            except Exception:
                dev = DeviceSession()
                dev.connect()
                dev.force_clean()

        if anomalies and len(anomalies) > results.get("_last_anom_count", 0):
            results["_last_anom_count"] = len(anomalies)
            last = anomalies[-1]
            log(f"\n  !!! ANOMALY DETECTED at cycle {cycle} !!!")
            log(f"  {last}")
            log(f"  Collecting evidence...")
            evidence_npu = dev.show("show system npu-resources resource-type flowspec")
            evidence_traces = dev.show(
                "show file ncp 6 traces datapath/wb_agent.flowspec | tail 50")
            last["evidence_npu"] = ANSI_RE.sub('', evidence_npu)
            last["evidence_traces"] = ANSI_RE.sub('', evidence_traces)

            dev.force_clean()
            npu_after = verify_npu(dev, "post-anomaly-clean", 0)
            if npu_after[2] > BASELINE_HW + 5:
                log(f"  CRITICAL: device won't clean after anomaly hw={npu_after[2]}")

        if cycle % PROBE_EVERY == 0:
            dev.force_clean()
            pn += 1
            if run_probe(dev, pn, results):
                results["leak_cycle"] = cycle
                results["leak_scenario"] = SCENARIOS[cycle % len(SCENARIOS)].__name__
                break

        if datetime.now() >= deadline:
            break

    results["anomalies"] = anomalies
    results["total_cycles"] = cycle
    results["finished"] = datetime.now().isoformat()
    dur = (datetime.fromisoformat(results["finished"]) -
           datetime.fromisoformat(results["started"])).total_seconds()

    log(f"\n{'#'*60}")
    if results["leak_detected"]:
        log(f"  *** BUG-2 REPRODUCED *** leaked={results['leak_amount']} at cycle {cycle}")
    elif anomalies:
        log(f"  {len(anomalies)} ANOMALIES detected (no TCAM leak)")
        for a in anomalies:
            log(f"    - {a['label']}: {a['issues']}")
    else:
        log(f"  CLEAN RUN: {cycle} cycles, no anomalies, no leaks")
    log(f"  Duration: {dur:.0f}s ({dur/60:.1f}m)")
    log(f"  Probes passed: {len(results['probes'])}")
    log(f"{'#'*60}")

    dev.force_clean()
    dev.close()
    with open("/home/dn/SCALER/FLOWSPEC_VPN/scale_test/bug2_final_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    log("Results saved. Device cleaned.")


if __name__ == "__main__":
    main()
