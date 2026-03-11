#!/usr/bin/env python3
"""Run BGP trace greps on PE-4 to diagnose ExaBGP Connect state. Output to stdout."""

import paramiko
import time
import json
import os

DEVICES_JSON = os.path.expanduser("~/SCALER/db/devices.json")

def get_pe4_creds():
    with open(DEVICES_JSON) as f:
        data = json.load(f)
    for d in data.get("devices", []):
        if "pe" in d.get("id", "").lower() and "4" in d.get("id", ""):
            return d["ip"], d["username"], d["password"]
    return "100.64.4.98", "dnroot", "ZG5yb290"

def run_cmd(shell, cmd, delay=3):
    shell.send(cmd + "\n")
    time.sleep(delay)
    buf = ""
    while shell.recv_ready():
        buf += shell.recv(65536).decode("utf-8", errors="replace")
    return buf

def main():
    host, user, pw = get_pe4_creds()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=22, username=user, password=pw, timeout=30, look_for_keys=False)
    shell = client.invoke_shell(width=200, height=100)
    shell.settimeout(60)
    time.sleep(2)
    while shell.recv_ready():
        shell.recv(65536)

    # Use 21:46 (device time Israel) - recent events from user paste
    ts = "21:46"
    cmds = [
        ("show system image", "Phase 0: Image"),
        ("show file traces routing_engine/bgpd_traces | include 100.64.6.134 | tail 50", "bgpd: 100.64.6.134"),
        ("show file traces routing_engine/bgpd_traces | include 100.70.0.206 | tail 50", "bgpd: 100.70.0.206"),
        ("show file traces routing_engine/bgpd_traces | include " + ts + " | include 100.64 | tail 80", "bgpd: timestamp+IP"),
        ("show file traces routing_engine/bgpd_traces | include Connect | tail 30", "bgpd: Connect"),
        ("show file traces routing_engine/bgpd_traces | include rst | tail 30", "bgpd: rst"),
        ("show file traces routing_engine/bgpd_traces | include refused | tail 30", "bgpd: refused"),
        ("show file traces routing_engine/bgpd_traces | include listener | tail 20", "bgpd: listener"),
        ("show file traces routing_engine/bgpd_traces | include 179 | tail 30", "bgpd: port 179"),
    ]

    for cmd, label in cmds:
        print(f"\n{'='*60}\n### [{label}]\n{cmd}\n{'-'*40}")
        out = run_cmd(shell, cmd, 4)
        # Strip ANSI and pagination prompts
        lines = [l for l in out.split("\n") if not l.strip().startswith("-- More --") and "Press" not in l]
        print("\n".join(lines[-120:]))  # last 120 lines

    run_cmd(shell, "exit", 1)
    client.close()

if __name__ == "__main__":
    main()
