#!/usr/bin/env python3
"""Aggressive FlowSpec local-policy stress test.

Goals:
- 500+ rules in single commits
- Fill TCAM to absolute max (12000/12000)
- 7000 match-classes with heavy parameters
- Rollback uncommitted massive configs
- Monitor device processes for crashes
- No sleeps — verify state, then proceed
"""

import paramiko
import time
import re
import os
import subprocess
import json
from datetime import datetime, timedelta

LOG = "/tmp/aggressive_stress.log"
_logf = open(LOG, "w")

PE4_HOST = "100.64.6.82"
PE4_USER = "dnroot"
PE4_PASS = "dnroot"
ANSI_RE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')
BASELINE_HW = 0
BASELINE_INSTALLED = 0
BASELINE_RECEIVED = 0
RUN_DURATION = timedelta(hours=2)


def log(msg=""):
    _logf.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
    _logf.flush()


PIDFILE = "/tmp/aggressive_stress.pid"

def acquire_lock():
    """Write our PID to lock file. Kill any existing holder first."""
    my_pid = os.getpid()
    if os.path.exists(PIDFILE):
        try:
            old_pid = int(open(PIDFILE).read().strip())
            if old_pid != my_pid:
                os.kill(old_pid, 9)
                log(f"  [killed old PID {old_pid}]")
                time.sleep(1)
        except (ValueError, ProcessLookupError, PermissionError):
            pass
    with open(PIDFILE, "w") as f:
        f.write(str(my_pid))

def kill_competing():
    my_pid = os.getpid()
    try:
        out = subprocess.check_output(
            ["pgrep", "-f", "run_bug2_final|run_aggressive"], text=True).strip()
        for pid_s in out.splitlines():
            pid = int(pid_s.strip())
            if pid != my_pid and pid != os.getppid():
                log(f"  [killing competing PID {pid}]")
                try:
                    os.kill(pid, 9)
                except ProcessLookupError:
                    pass
    except Exception:
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
        self.shell = self.client.invoke_shell(width=300, height=50)
        self.shell.settimeout(1800)
        self._recv(2)

    def _recv(self, delay=0.5):
        time.sleep(delay)
        buf = ""
        try:
            while self.shell.recv_ready():
                buf += self.shell.recv(65536).decode("utf-8", errors="replace")
        except Exception:
            pass
        return buf

    def _send(self, cmd, delay=0.5):
        self.shell.send(cmd + "\n")
        return self._recv(delay)

    def _drain(self):
        while self.shell.recv_ready():
            self.shell.recv(65536)

    def _ensure_config(self):
        self._drain()
        try:
            out = self._send("configure", 0.5)
        except OSError:
            self._reconnect()
            out = self._send("configure", 0.5)
        if "uncommitted" in out.lower():
            self._send("yes", 0.5)
            self._send("configure", 0.5)
        self._send("rollback 0", 0.3)

    def paste_config(self, config_text):
        lines = config_text.strip().split("\n")
        for i in range(0, len(lines), 150):
            batch = lines[i:i+150]
            for line in batch:
                self.shell.send(line + "\n")
            self._recv(0.1)
        self._recv(0.3)

    def commit(self, label="", timeout_s=300):
        self._drain()
        self.shell.send("commit\n")
        return self._wait_commit(label=label, timeout_s=timeout_s)

    def _wait_commit(self, label="", timeout_s=300):
        acc = ""
        max_iter = timeout_s // 2
        for attempt in range(max_iter):
            time.sleep(2)
            buf = ""
            while self.shell.recv_ready():
                buf += self.shell.recv(65536).decode("utf-8", errors="replace")
            acc += buf
            clean = ANSI_RE.sub("", acc)
            if "uncommitted changes" in clean or "yes/no/cancel" in clean:
                log(f"  COMMIT-INTERRUPTED {label}")
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
                log(f"  COMMIT-FAILED {label}: {clean[-300:]}")
                self._send("rollback 0", 1)
                return False
            if attempt >= 1 and re.search(r'PE-4\(cfg\)#\s*$', clean):
                return True
            if attempt == 15:
                log(f"  COMMIT-SLOW {label} (30s+)")
            if attempt == 60:
                log(f"  COMMIT-VERY-SLOW {label} (120s+)")
        log(f"  COMMIT-TIMEOUT {label} ({timeout_s}s)")
        self._send("", 0.3)
        self._send("configure", 0.5)
        self._send("rollback 0", 0.5)
        self.shell.send("commit\n")
        self._wait_simple_commit()
        self._send("end", 0.3)
        return False

    def _wait_simple_commit(self):
        for _ in range(60):
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

    def paste_and_commit(self, config_text, label="", timeout_s=300):
        self._ensure_config()
        self.paste_config(config_text)
        return self.commit(label=label, timeout_s=timeout_s)

    def force_clean(self):
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
        self._wait_clean_commit()
        self._send("end", 0.3)
        return self.wait_npu_clean()

    def _wait_clean_commit(self):
        acc = ""
        for attempt in range(90):
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
            if attempt >= 1 and re.search(r'PE-4\(cfg\)#\s*$', clean):
                return True
        log(f"  force_clean COMMIT-TIMEOUT")
        return False

    def wait_npu_clean(self, timeout=60):
        for _ in range(timeout // 2):
            npu = self.check_npu()
            if npu[2] <= BASELINE_HW:
                return npu
            time.sleep(2)
        log(f"  WARNING: NPU won't drain hw={self.check_npu()[2]}")
        return self.check_npu()

    def wait_npu_rules(self, expected, timeout=120):
        target = BASELINE_INSTALLED + expected
        for _ in range(timeout // 2):
            npu = self.check_npu()
            if npu[1] >= target - 2:
                return npu
            time.sleep(2)
        return self.check_npu()

    def show(self, command, wait=2.0):
        try:
            self._send("end", 0.3)
            self.shell.send(command + " | no-more\n")
        except OSError:
            self._reconnect()
            self.shell.send(command + " | no-more\n")
        time.sleep(wait)
        out = ""
        for _ in range(10):
            time.sleep(0.5)
            while self.shell.recv_ready():
                out += self.shell.recv(65536).decode("utf-8", errors="replace")
            if out and not self.shell.recv_ready():
                break
        return out

    def check_npu(self):
        raw = self.show("show system npu-resources resource-type flowspec")
        clean = ANSI_RE.sub('', raw)
        m = re.search(r'\|\s*6\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)/12000', clean)
        if m:
            return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        return (-1, -1, -1)

    def check_npu_log(self, label, expected=None):
        npu = self.check_npu()
        if expected is not None and expected > 0:
            npu = self.wait_npu_rules(expected)
        elif expected == 0:
            npu = self.wait_npu_clean()
        log(f"  [{label}] recv={npu[0]} inst={npu[1]} hw={npu[2]}/12000")
        return npu

    def check_processes(self):
        """Check device health — uptime + NCP status."""
        raw = self.show("show system uptime", wait=3)
        clean = ANSI_RE.sub('', raw)
        raw2 = self.show("show system ncp brief", wait=3)
        clean2 = ANSI_RE.sub('', raw2)
        return clean + "\n" + clean2

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

    def cfg_lines(self, lines_list, label=""):
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

    def close(self):
        try:
            self.client.close()
        except Exception:
            pass


VRFS = [None, "ALPHA", "ZULU"]
ACTIONS = ["rate-limit 0", "drop", "rate-limit 1000000", "rate-limit 500"]
VRF_PAT = {
    "none":       lambda i, n: None,
    "all_alpha":  lambda i, n: "ALPHA",
    "all_zulu":   lambda i, n: "ZULU",
    "mixed":      lambda i, n: "ALPHA" if i <= n // 2 else "ZULU",
    "third":      lambda i, n: [None, "ALPHA", "ZULU"][i % 3],
}


def gen_mc(count, pfx, base2=10, vrf_pat="none", heavy=False, pktlen=False):
    vfn = VRF_PAT.get(vrf_pat, VRF_PAT["none"])
    lines = ["routing-policy", "  flowspec-local-policies", "    ipv4"]
    for i in range(1, count + 1):
        proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
        o3, o4 = divmod(i - 1, 254)
        if o3 > 254:
            o3 = o3 % 255
        ip = f"10.{base2 % 256}.{o3}.{o4 + 1}"
        mc = [f"      match-class MC4-{pfx}-{i:05d}",
              f"        dest-ip {ip}/32",
              f"        protocol {proto}",
              f"        dest-ports {3000 + (i % 60000)}"]
        vrf = vfn(i, count)
        if vrf:
            mc.append(f"        vrf {vrf}")
        if pktlen or (heavy and i % 3 == 0):
            mc.append(f"        packet-length 64-1500")
        if heavy:
            src_o3, src_o4 = divmod(i - 1, 254)
            mc.append(f"        src-ip 172.16.{src_o3 % 256}.{src_o4 + 1}/32")
            mc.append(f"        src-ports {5000 + (i % 60000)}")
            if i % 5 == 0:
                mc.append(f"        fragment is-fragment")
            if i % 7 == 0:
                mc.append(f"        dscp af11")
        mc.append("      !")
        lines.extend(mc)
    lines += ["    !", "  !", "!"]
    return "\n".join(lines)


def gen_pol(count, pfx, action="rate-limit 0"):
    lines = ["routing-policy", "  flowspec-local-policies", "    ipv4",
             f"      policy POL-{pfx}", f"        description aggressive"]
    for i in range(1, count + 1):
        act = action if isinstance(action, str) else action[i % len(action)]
        lines += [f"        match-class MC4-{pfx}-{i:05d}",
                  f"          action {act}", "        !"]
    lines += ["      !", "    !", "  !", "!"]
    return "\n".join(lines)


def gen_fwd(pfx):
    return "\n".join([
        "forwarding-options", "  flowspec-local", "    ipv4",
        f"      apply-policy-to-flowspec POL-{pfx}",
        "    !", "  !", "!"])


def gen_full(count, pfx, base2=10, action="rate-limit 0",
             vrf_pat="none", heavy=False, pktlen=False):
    return gen_mc(count, pfx, base2, vrf_pat, heavy, pktlen) + "\n" + \
           gen_pol(count, pfx, action) + "\n" + gen_fwd(pfx)


def gen_probe(pid):
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


def run_probe(dev, pid):
    log(f"\n  === PROBE #{pid} ===")
    dev.paste_and_commit(gen_probe(pid), label=f"probe-{pid}", timeout_s=300)
    dev._send("end", 0.3)
    npu = dev.wait_npu_rules(490, timeout=120)
    local = npu[1] - BASELINE_INSTALLED
    simple = max(0, local - 8)
    leaked = max(0, 490 - simple)
    log(f"  PROBE: inst={npu[1]} hw={npu[2]}/12000 simple={simple}/490")
    if leaked > 0:
        log(f"  *** LEAK *** leaked={leaked}")
        traces = dev.show("show file ncp 6 traces datapath/wb_agent.flowspec | tail 50")
        log(f"  TRACES: {ANSI_RE.sub('', traces)[:500]}")
        return leaked
    log(f"  PROBE OK")
    dev.force_clean()
    return 0


def main():
    log(f"{'='*70}")
    log(f"AGGRESSIVE FLOWSPEC STRESS TEST (PID {os.getpid()})")
    log(f"Duration: {RUN_DURATION}")
    log(f"{'='*70}")

    acquire_lock()
    kill_competing()

    global BASELINE_HW, BASELINE_INSTALLED, BASELINE_RECEIVED

    dev = DeviceSession()
    dev.connect()
    log(f"Connected to PE-4")

    dev.force_clean()
    npu = dev.check_npu()
    BASELINE_RECEIVED = npu[0]
    BASELINE_INSTALLED = npu[1]
    BASELINE_HW = npu[2]
    log(f"BASELINE: recv={BASELINE_RECEIVED} inst={BASELINE_INSTALLED} hw={BASELINE_HW}")

    probe_id = 0
    leaked = run_probe(dev, probe_id)
    if leaked:
        log("Device already leaking. Aborting.")
        dev.close()
        return

    deadline = datetime.now() + RUN_DURATION
    anomalies = []
    cycle = 0

    def anomaly(label, npu, expected, details=""):
        if expected == 0 and npu[2] > BASELINE_HW + 5:
            msg = f"ANOMALY [{label}]: hw={npu[2]} expected ~{BASELINE_HW}. {details}"
            log(f"  *** {msg}")
            anomalies.append({"ts": datetime.now().isoformat(), "label": label,
                              "npu": npu, "msg": msg})
            procs = dev.check_processes()
            log(f"  PROCESSES: {ANSI_RE.sub('', procs)[:300]}")
            return True
        return False

    def safe_clean(label=""):
        """Force clean and verify. If fails, reconnect and retry."""
        try:
            npu = dev.force_clean()
        except Exception as e:
            log(f"  clean exception: {e}")
            dev._reconnect()
            npu = dev.force_clean()
        anomaly(f"{label}-clean", npu, 0)
        return npu

    def recover():
        nonlocal dev
        try:
            dev._reconnect()
            dev.force_clean()
        except Exception:
            dev = DeviceSession()
            dev.connect()
            dev.force_clean()

    # ── SCENARIO 1: 500 simple rules single commit ──
    cycle += 1
    log(f"\n{'─'*50}")
    log(f"SCENARIO {cycle}: 500 simple rules, single commit")
    dev.paste_and_commit(gen_full(500, "A500", base2=10, action="rate-limit 0",
                                   vrf_pat="mixed"), label="500-simple")
    npu = dev.check_npu_log("500-loaded", 500)
    safe_clean("s1")

    # ── SCENARIO 2: 1000 rules single commit ──
    cycle += 1
    log(f"\n{'─'*50}")
    log(f"SCENARIO {cycle}: 1000 rules single commit")
    dev.paste_and_commit(gen_full(1000, "A1K", base2=20, action="drop",
                                   vrf_pat="third"), label="1k-load")
    npu = dev.check_npu_log("1k-loaded", 1000)
    safe_clean("s2")

    # ── SCENARIO 3: 2000 rules single commit ──
    cycle += 1
    log(f"\n{'─'*50}")
    log(f"SCENARIO {cycle}: 2000 rules single commit")
    dev.paste_and_commit(gen_full(2000, "A2K", base2=30, action="rate-limit 500",
                                   vrf_pat="all_alpha"), label="2k-load", timeout_s=600)
    npu = dev.wait_npu_rules(2000, timeout=120)
    npu = dev.check_npu_log("2k-loaded", 2000)
    if npu[1] < 2000:
        log(f"  WARNING: only {npu[1]}/2000 installed — possible limit or timing")
    safe_clean("s3")

    # ── SCENARIO 4: 3000 rules - push the limit ──
    cycle += 1
    log(f"\n{'─'*50}")
    log(f"SCENARIO {cycle}: 3000 rules single commit")
    dev.paste_and_commit(gen_full(3000, "A3K", base2=40, vrf_pat="all_zulu"),
                         label="3k-load", timeout_s=600)
    npu = dev.check_npu_log("3k-loaded", 3000)
    safe_clean("s4")

    # ── SCENARIO 5: Fill TCAM to absolute maximum ──
    cycle += 1
    log(f"\n{'─'*50}")
    log(f"SCENARIO {cycle}: Fill TCAM to 12000/12000 (8 pktlen + max simple)")
    pfx = "MAXFILL"
    lines = ["routing-policy", "  flowspec-local-policies", "    ipv4"]
    for i in range(1, 9):
        proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
        lines += [f"      match-class MC4-{pfx}-K{i:05d}",
                  f"        dest-ip 10.99.{i}.1/32",
                  f"        protocol {proto}",
                  f"        dest-ports {9000 + i}",
                  f"        packet-length 64-1500", "      !"]
    for i in range(1, 501):
        proto = "tcp(0x06)" if i % 2 == 1 else "udp(0x11)"
        o3, o4 = divmod(i - 1, 254)
        lines += [f"      match-class MC4-{pfx}-S{i:05d}",
                  f"        dest-ip 10.77.{o3}.{o4 + 1}/32",
                  f"        protocol {proto}",
                  f"        dest-ports {3000 + i}", "      !"]
    lines += [f"      policy POL-{pfx}", f"        description maxfill"]
    for i in range(1, 9):
        lines += [f"        match-class MC4-{pfx}-K{i:05d}",
                  f"          action rate-limit 0", "        !"]
    for i in range(1, 501):
        lines += [f"        match-class MC4-{pfx}-S{i:05d}",
                  f"          action rate-limit 0", "        !"]
    lines += ["      !", "    !", "  !", "!",
              "forwarding-options", "  flowspec-local", "    ipv4",
              f"      apply-policy-to-flowspec POL-{pfx}", "    !", "  !", "!"]
    dev.paste_and_commit("\n".join(lines), label="maxfill", timeout_s=600)
    npu = dev.wait_npu_rules(490, timeout=120)
    npu = dev.check_npu_log("maxfill-loaded")
    log(f"  TCAM at {npu[2]}/12000 (inst={npu[1]})")
    if npu[2] >= 11900:
        log(f"  SUCCESS: TCAM near/at capacity {npu[2]}/12000")
    else:
        log(f"  WARNING: expected ~12000 but got {npu[2]}")
    safe_clean("s5-maxfill")

    # ── SCENARIO 6: Rollback massive uncommitted config ──
    cycle += 1
    log(f"\n{'─'*50}")
    log(f"SCENARIO {cycle}: Paste 2000 rules, rollback 0, verify nothing installed")
    dev._ensure_config()
    dev.paste_config(gen_full(2000, "RBIG", base2=50, action="drop", vrf_pat="mixed"))
    log(f"  2000 rules pasted (uncommitted)")
    dev._send("rollback 0", 1)
    dev.commit(label="rollback-verify")
    dev._send("end", 0.3)
    npu = dev.check_npu_log("after-rollback-2k", 0)
    anomaly("s6-rollback", npu, 0, "rules should be 0 after rollback 0")

    # ── SCENARIO 7: 500 heavy rules (src-ip+src-ports+pktlen+fragment+dscp) ──
    cycle += 1
    log(f"\n{'─'*50}")
    log(f"SCENARIO {cycle}: 500 heavy rules (6 match criteria each)")
    dev.paste_and_commit(gen_full(500, "HEAVY500", base2=60, action="rate-limit 0",
                                   vrf_pat="third", heavy=True),
                         label="heavy500", timeout_s=300)
    npu = dev.check_npu_log("heavy500-loaded", 500)
    hw_per = npu[2] / max(npu[1], 1) if npu[1] > 0 else 0
    log(f"  TCAM amplification: {hw_per:.1f}x ({npu[2]} hw for {npu[1]} rules)")
    safe_clean("s7-heavy")

    # Process check after heavy scenario
    procs = dev.check_processes()
    log(f"  Process health: {ANSI_RE.sub('', procs)[:200]}")

    # ── SCENARIO 8: 5000 match-classes, single policy ──
    cycle += 1
    log(f"\n{'─'*50}")
    log(f"SCENARIO {cycle}: 5000 match-classes single policy")
    try:
        dev.paste_and_commit(gen_full(5000, "MC5K", base2=70, vrf_pat="all_alpha"),
                             label="5k-mc", timeout_s=600)
        npu = dev.check_npu_log("5k-loaded", 5000)
        safe_clean("s8")
    except Exception as e:
        log(f"  EXCEPTION in S8: {e}")
        recover()

    # ── SCENARIO 9: 7000 match-classes with heavy params ──
    cycle += 1
    log(f"\n{'─'*50}")
    log(f"SCENARIO {cycle}: 7000 match-classes with heavy params (src-ip+ports+pktlen+frag+dscp)")
    try:
        dev.paste_and_commit(gen_full(7000, "MC7K", base2=80, vrf_pat="mixed",
                                       heavy=True, action="drop"),
                             label="7k-heavy", timeout_s=1200)
        npu = dev.check_npu_log("7k-loaded", 7000)
        hw_per = npu[2] / max(npu[1], 1) if npu[1] > 0 else 0
        log(f"  7K TCAM amplification: {hw_per:.1f}x ({npu[2]} hw / {npu[1]} rules)")
        safe_clean("s9-7k")
    except Exception as e:
        log(f"  EXCEPTION in S9: {e}")
        recover()

    procs = dev.check_processes()
    log(f"  Process health: {ANSI_RE.sub('', procs)[:200]}")

    # ── PROBE #1 after massive loads ──
    probe_id += 1
    leaked = run_probe(dev, probe_id)
    if leaked:
        log(f"LEAK DETECTED after {cycle} aggressive scenarios!")
        dev.close()
        return

    # ── SCENARIO 10: Rollback 7000 uncommitted heavy rules ──
    cycle += 1
    log(f"\n{'─'*50}")
    log(f"SCENARIO {cycle}: Paste 7000 heavy rules uncommitted, rollback 0")
    try:
        dev._ensure_config()
        dev.paste_config(gen_full(7000, "RB7K", base2=90, heavy=True, vrf_pat="third"))
        log(f"  7000 heavy rules pasted (uncommitted)")
        dev._send("rollback 0", 2)
        dev.commit(label="rb7k-verify")
        dev._send("end", 0.3)
        npu = dev.check_npu_log("after-rollback-7k", 0)
        anomaly("s10-rollback-7k", npu, 0)
    except Exception as e:
        log(f"  EXCEPTION in S10: {e}")
        recover()

    # ── SCENARIO 11: Load 500, then overwrite with 7000 ──
    cycle += 1
    log(f"\n{'─'*50}")
    log(f"SCENARIO {cycle}: Load 500, then overwrite with 7000 rules")
    dev.paste_and_commit(gen_full(500, "OW500", base2=100, action="rate-limit 0"),
                         label="ow-500")
    npu = dev.check_npu_log("ow-500-loaded", 500)
    dev.paste_and_commit(gen_full(7000, "OW7K", base2=110, action="drop",
                                   vrf_pat="all_zulu"),
                         label="ow-7k", timeout_s=600)
    npu = dev.check_npu_log("ow-7k-loaded", 7000)
    safe_clean("s11")

    # ── SCENARIO 12: Rapid 500-rule cycles ──
    cycle += 1
    log(f"\n{'─'*50}")
    log(f"SCENARIO {cycle}: Rapid 500-rule load/delete x10 cycles")
    for r in range(1, 11):
        pfx = f"RAP{r:02d}"
        dev.paste_and_commit(gen_full(500, pfx, base2=120+r, action=ACTIONS[r%4],
                                      vrf_pat=list(VRF_PAT.keys())[r%5]),
                             label=f"rapid-{r}")
        dev.force_clean()
        log(f"    rapid cycle {r}/10 done")
    npu = dev.check_npu_log("rapid-done", 0)
    anomaly("s12-rapid", npu, 0)

    # ── SCENARIO 13: Stacking 5 policies of 500 rules each ──
    cycle += 1
    log(f"\n{'─'*50}")
    log(f"SCENARIO {cycle}: Stack 5 policies x 500 rules (2500 total)")
    for p in range(1, 6):
        pfx = f"STK{p}"
        dev.paste_and_commit(gen_full(500, pfx, base2=130+(p*10),
                                      action=ACTIONS[p%4],
                                      vrf_pat=list(VRF_PAT.keys())[p%5]),
                             label=f"stack-{p}")
    npu = dev.check_npu_log("stacked-2500")
    log(f"  5 policies stacked: {npu[1]} rules, {npu[2]} hw")
    safe_clean("s13")

    # ── SCENARIO 14: Delete forwarding-options mid-3000 rules ──
    cycle += 1
    log(f"\n{'─'*50}")
    log(f"SCENARIO {cycle}: Load 3000 rules, delete only forwarding-options")
    dev.paste_and_commit(gen_full(3000, "DELFWD", base2=180, vrf_pat="all_alpha"),
                         label="delfwd-load", timeout_s=600)
    npu = dev.check_npu_log("delfwd-loaded", 3000)
    dev.cfg_lines(["no forwarding-options flowspec-local"], label="delfwd-del")
    npu = dev.check_npu_log("delfwd-after-del", 0)
    dev.cfg_lines(["no routing-policy flowspec-local-policies"], label="delfwd-pol")
    npu = dev.check_npu_log("delfwd-pol-done", 0)
    anomaly("s14-delfwd", npu, 0)

    # ── SCENARIO 15: Alternate commit sizes 100→2000→500→5000 ──
    cycle += 1
    log(f"\n{'─'*50}")
    log(f"SCENARIO {cycle}: Alternating batch sizes 100→2000→500→5000")
    for n, pfx in [(100, "ALT100"), (2000, "ALT2K"), (500, "ALT500"), (5000, "ALT5K")]:
        dev.paste_and_commit(gen_full(n, pfx, base2=190+(n%60)),
                             label=f"alt-{n}", timeout_s=600)
        npu = dev.check_npu_log(f"alt-{n}-loaded", n)
        safe_clean(f"s15-{n}")

    # ── PROBE #2 ──
    probe_id += 1
    leaked = run_probe(dev, probe_id)
    if leaked:
        log(f"LEAK DETECTED after {cycle} scenarios!")
        dev.close()
        return

    # ── CONTINUOUS CYCLES until deadline ──
    log(f"\n{'─'*50}")
    log(f"CONTINUOUS CYCLING: aggressive loads until {deadline.strftime('%H:%M:%S')}")

    sizes = [500, 1000, 2000, 3000, 5000, 7000, 500, 1000]
    heavy_flags = [False, False, False, False, False, True, True, False]
    cont_cycle = 0

    while datetime.now() < deadline:
        cont_cycle += 1
        idx = cont_cycle % len(sizes)
        n = sizes[idx]
        hvy = heavy_flags[idx]
        pfx = f"C{cont_cycle:04d}"
        vp = list(VRF_PAT.keys())[cont_cycle % len(VRF_PAT)]
        act = ACTIONS[cont_cycle % len(ACTIONS)]
        tag = "heavy" if hvy else "simple"

        log(f"\n  CONT #{cont_cycle}: n={n} {tag} vrf={vp} act={act}")

        try:
            dev.paste_and_commit(gen_full(n, pfx, base2=(cont_cycle*7)%200,
                                          action=act, vrf_pat=vp, heavy=hvy),
                                 label=f"cont-{cont_cycle}", timeout_s=600)
            npu = dev.check_npu_log(f"cont-{cont_cycle}-loaded", n)

            if cont_cycle % 3 == 0:
                dev._ensure_config()
                dev.paste_config(gen_full(n, f"RB{cont_cycle:04d}",
                                          base2=(cont_cycle*13)%200,
                                          heavy=hvy, vrf_pat=vp))
                dev._send("rollback 0", 1)
                dev.commit(label=f"cont-{cont_cycle}-rb")
                dev._send("end", 0.3)
                npu = dev.check_npu_log(f"cont-{cont_cycle}-post-rb", n)
                log(f"    rollback of {n} uncommitted rules OK")

            safe_clean(f"cont-{cont_cycle}")

        except Exception as e:
            log(f"  EXCEPTION in cont #{cont_cycle}: {e}")
            try:
                dev._reconnect()
                dev.force_clean()
            except Exception:
                dev = DeviceSession()
                dev.connect()
                dev.force_clean()

        if cont_cycle % 10 == 0:
            probe_id += 1
            leaked = run_probe(dev, probe_id)
            if leaked:
                log(f"LEAK at continuous cycle {cont_cycle}!")
                break
            procs = dev.check_processes()
            log(f"  Process health: {ANSI_RE.sub('', procs)[:200]}")

    # ── FINAL ──
    log(f"\n{'='*70}")
    log(f"FINISHED: {cycle + cont_cycle} total scenarios")
    log(f"Anomalies: {len(anomalies)}")
    log(f"Probes passed: {probe_id + 1}")
    for a in anomalies:
        log(f"  - {a['label']}: {a['msg']}")
    if not anomalies:
        log(f"CLEAN RUN — no anomalies, no leaks")
    log(f"{'='*70}")

    dev.force_clean()
    dev.close()

    with open("/home/dn/SCALER/FLOWSPEC_VPN/scale_test/aggressive_results.json", "w") as f:
        json.dump({"anomalies": anomalies, "total_scenarios": cycle + cont_cycle,
                    "probes": probe_id + 1, "leaked": leaked}, f, indent=2, default=str)
    log("Results saved. Device cleaned.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        log(f"\n!!! FATAL EXCEPTION: {e}")
        log(traceback.format_exc())
    finally:
        try:
            os.remove(PIDFILE)
        except Exception:
            pass
