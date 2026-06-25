#!/usr/bin/env python3
"""Round-4: probe the deepest operational leaves and walk the CONFIG-MODE
menu under ``mac-handling local-loop-prevention`` (read-only -- enters
config mode, walks `?`, and rolls back without committing).

DEPRECATED 2026-04-30
=====================
Superseded by ``auto_find_syntax.py`` (same directory) which uses the
DNOS built-in ``cmd search <keyword>`` operator and is 700x faster.

This file is preserved only for archaeology -- to show how the syntax
was originally discovered before ``cmd search`` was found. New
discovery work should use ``auto_find_syntax.py`` and the
``CliSyntaxValidator.prewarm_with_cmd_search`` API.

To replicate the v4 round in 0.1s instead of 70s::

    python3 auto_find_syntax.py --device-ip 100.64.10.22 \\
            --keywords loop-prevention mac-handling restore-timer
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import List

_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[4]
sys.path.insert(0, str(_REPO_ROOT / "scaler"))
sys.path.insert(0, str(_HERE.parents[1]))

from scaler.dnos_session import DNOSSession                          # noqa: E402
from lib.cache_store import CacheStore, BuildInfo                     # noqa: E402


def _drain(ssh, idle_s=0.6):
    out = b""
    deadline = time.monotonic() + idle_s
    while time.monotonic() < deadline:
        if ssh._shell.recv_ready():                                  # noqa: SLF001
            out += ssh._shell.recv(65536)
            deadline = time.monotonic() + idle_s
        else:
            time.sleep(0.05)
    return out.decode("utf-8", errors="replace")


_ANSI = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")


def _harvest(ssh, prefix):
    _drain(ssh, 0.2)
    ssh.send_raw(f"{prefix} ?")
    time.sleep(0.9)
    raw = _ANSI.sub("", _drain(ssh, 0.7))
    ssh.send_raw("\x15")
    time.sleep(0.2)
    _drain(ssh, 0.3)

    keywords: List[str] = []
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("%") or s.startswith("---") or s.startswith("ERROR"):
            continue
        if s.startswith(prefix.split()[0]):
            continue
        toks = s.split()
        if not toks:
            continue
        token = toks[0].rstrip(",")
        if token in {"show", "Possible", "completions:", "<cr>"}:
            continue
        if token.replace("-", "").replace("_", "").isalnum() and 1 < len(token) < 40:
            keywords.append(token)
    seen = set()
    out_uniq: List[str] = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            out_uniq.append(k)
    return out_uniq


def _is_valid(text):
    return text and not any(m in text for m in (
        "% Unknown", "% Ambiguous", "% Invalid",
        "ERROR: Unknown", "ERROR: Ambiguous", "ERROR: Invalid",
        "Unknown word",
    ))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--device-ip", default="100.64.10.22")
    p.add_argument("--user", default="dnroot")
    p.add_argument("--password", default=os.environ.get("DNOS_PASSWORD", "dnroot"))
    p.add_argument("--device-label", default="PE-4")
    p.add_argument("--instance", default="EVPN_SI_VPLS_1")
    args = p.parse_args()

    print(f"[INFO] connecting to {args.device_label} ({args.device_ip})")
    ssh = DNOSSession(args.device_ip, args.user, args.password)
    print("[OK]   connected")

    build = BuildInfo(commit="8fd38d35a10a", branch="dev_v26_2", device=args.device_label)
    store = CacheStore(suite_id="discover_loop_prevention")
    inst = args.instance

    # ---------------------------------------------------------------
    # 1) Final operational leaves: ... interface local + ... mac-table local
    # ---------------------------------------------------------------
    leaves = [
        f"show evpn instance {inst} loop-prevention interface local",
        f"show evpn instance {inst} loop-prevention mac-table local",
        # Also explore mac-table with explicit MAC
        f"show evpn instance {inst} loop-prevention mac-table 00:00:00:00:00:00",
    ]
    print("\n[INFO] probing deep operational leaves...")
    for cmd in leaves:
        out = ssh.send_command(cmd)
        ok = _is_valid(out)
        first = (out or "").strip().splitlines()[:3]
        snippet = " | ".join(first)[:200]
        if ok:
            print(f"  [OK]   {cmd}")
            print(f"           -> {snippet}")
            store.record_valid(cmd, device=args.device_label, build=build,
                               notes="deep loop-prevention leaf")
        else:
            print(f"  [BAD]  {cmd}")
            print(f"           -> {snippet}")
            store.record_invalid(cmd, device=args.device_label, build=build,
                                 notes="rejected on round-4")

    # ---------------------------------------------------------------
    # 2) Enter CONFIG mode and walk `?` under mac-handling. This is
    #    READ-ONLY: we never `commit`, only `?`-walk + `abort` at the
    #    end so the candidate is clean.
    # ---------------------------------------------------------------
    print("\n[INFO] entering config mode to walk mac-handling sub-tree...")
    ssh.send_raw("configure\n")
    time.sleep(0.5)
    _drain(ssh, 0.4)

    cfg_prefixes = [
        f"network-services evpn instance {inst} mac-handling",
        f"network-services evpn instance {inst} mac-handling loop-prevention",
        f"network-services evpn instance {inst} mac-handling local-loop-prevention",
        f"network-services evpn instance {inst} mac-handling loop-prevention local-loop-prevention",
    ]
    for prefix in cfg_prefixes:
        kws = _harvest(ssh, prefix)
        print(f"[?cfg] {prefix}")
        print(f"         -> {len(kws)} keywords: {kws}")
        if kws:
            store.record_menu(prefix, kws, device=args.device_label, build=build)

    # ---------------------------------------------------------------
    # 3) Walk per-AC (under interface) loop prevention -- the rule
    #    file says LLP timers live under `interfaces ...
    #    local-loop-prevention`. Verify on real config tree.
    # ---------------------------------------------------------------
    cfg_ac_prefixes = [
        f"network-services evpn instance {inst} interface ge100-18/0/1",
        f"network-services evpn instance {inst} interface ge100-18/0/1 mac-handling",
        f"network-services evpn instance {inst} interface ge100-18/0/1 mac-handling loop-prevention",
        f"network-services evpn instance {inst} interface ge100-18/0/1 mac-handling local-loop-prevention",
    ]
    for prefix in cfg_ac_prefixes:
        kws = _harvest(ssh, prefix)
        print(f"[?cfg-ac] {prefix}")
        print(f"            -> {len(kws)} keywords: {kws}")
        if kws:
            store.record_menu(prefix, kws, device=args.device_label, build=build)

    # ---------------------------------------------------------------
    # 4) Roll back any candidate changes and exit config mode safely.
    # ---------------------------------------------------------------
    print("\n[INFO] rolling back candidate (we never committed)...")
    ssh.send_raw("rollback 0\n")
    time.sleep(0.7)
    _drain(ssh, 0.5)
    ssh.send_raw("end\n")
    time.sleep(0.5)
    _drain(ssh, 0.5)

    print(f"\n[OK] round-4 done. Cache root: {store.shared_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
