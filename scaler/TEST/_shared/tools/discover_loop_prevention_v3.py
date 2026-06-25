#!/usr/bin/env python3
"""Round-3 loop-prevention discovery: walk every leaf we found in v2.

After v2, we know:
  * `show evpn instance <I> loop-prevention` has 4 sub-keywords:
      interface, local, mac-ip-table, mac-table
  * Config tree is mac-handling > loop-prevention > local-loop-prevention.

Round-3 probes:
  * Every leaf under `show evpn instance <I> loop-prevention <leaf>`.
  * Walks `?` under each of those to find the next level (e.g. does
    `show evpn instance <I> loop-prevention mac-table` need an MAC?).
  * Walks the FULL config sub-tree under
    `show config network-services evpn instance <I> mac-handling
     local-loop-prevention` to capture the entire timer/cycle vocabulary.
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

from scaler.dnos_session import DNOSSession                            # noqa: E402
from lib.cache_store import CacheStore, BuildInfo                       # noqa: E402


def _drain(ssh: DNOSSession, idle_s: float = 0.6) -> str:
    out = b""
    deadline = time.monotonic() + idle_s
    while time.monotonic() < deadline:
        if ssh._shell.recv_ready():                                    # noqa: SLF001
            out += ssh._shell.recv(65536)
            deadline = time.monotonic() + idle_s
        else:
            time.sleep(0.05)
    return out.decode("utf-8", errors="replace")


_ANSI = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")


def _harvest(ssh: DNOSSession, prefix: str) -> List[str]:
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


def _is_valid(text: str) -> bool:
    if not text:
        return True
    return not any(m in text for m in (
        "% Unknown", "% Ambiguous", "% Invalid",
        "ERROR: Unknown", "ERROR: Ambiguous", "ERROR: Invalid",
        "Unknown word",
    ))


def _is_incomplete(text: str) -> bool:
    return "Incomplete command" in (text or "")


def main() -> int:
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
    # 1) Walk under each of the 4 known leaves of `show evpn instance
    #    <I> loop-prevention`.
    # ---------------------------------------------------------------
    op_leaves = ["interface", "local", "mac-ip-table", "mac-table"]
    op_prefixes = []
    for leaf in op_leaves:
        prefix = f"show evpn instance {inst} loop-prevention {leaf}"
        op_prefixes.append(prefix)

    print("\n[INFO] walking ? menus under operational loop-prevention leaves...")
    for prefix in op_prefixes:
        kws = _harvest(ssh, prefix)
        print(f"[?]    {prefix}")
        print(f"         -> {len(kws)} keywords: {kws}")
        if kws:
            store.record_menu(prefix, kws, device=args.device_label, build=build)

    # ---------------------------------------------------------------
    # 2) Probe each leaf as an actual command (with no further args).
    # ---------------------------------------------------------------
    leaf_cmds = [
        f"show evpn instance {inst} loop-prevention interface",
        f"show evpn instance {inst} loop-prevention local",
        f"show evpn instance {inst} loop-prevention mac-ip-table",
        f"show evpn instance {inst} loop-prevention mac-table",
    ]

    print("\n[INFO] probing operational loop-prevention leaves as commands...")
    for cmd in leaf_cmds:
        out = ssh.send_command(cmd)
        ok = _is_valid(out)
        incomplete = _is_incomplete(out)
        first = (out or "").strip().splitlines()[:3]
        snippet = " | ".join(first)[:160]
        if ok and not incomplete:
            print(f"  [OK]    {cmd}")
            print(f"            -> {snippet}")
            store.record_valid(cmd, device=args.device_label, build=build,
                               notes="operational loop-prevention leaf")
        elif incomplete:
            print(f"  [PART]  {cmd} (incomplete: needs more args)")
            store.record_invalid(cmd, device=args.device_label, build=build,
                                 notes="prefix valid; more args required")
        else:
            print(f"  [BAD]   {cmd}")
            print(f"            -> {snippet}")
            store.record_invalid(cmd, device=args.device_label, build=build,
                                 notes="rejected on round-3")

    # ---------------------------------------------------------------
    # 3) Walk the FULL config sub-tree under local-loop-prevention.
    # ---------------------------------------------------------------
    cfg_root = (
        f"show config network-services evpn instance {inst} "
        f"mac-handling local-loop-prevention"
    )
    cfg_kws = _harvest(ssh, cfg_root)
    print(f"\n[?]    {cfg_root}")
    print(f"         -> {len(cfg_kws)} keywords: {cfg_kws}")
    if cfg_kws:
        store.record_menu(cfg_root, cfg_kws, device=args.device_label, build=build)

    # If menu came back empty under "show config" but parent menu showed
    # local-loop-prevention as a leaf, try the | flatten variant which
    # actually emits the configured timer values.
    cmd = cfg_root + " | flatten"
    out = ssh.send_command(cmd)
    ok = _is_valid(out)
    snippet = " | ".join((out or "").strip().splitlines()[:5])[:240]
    if ok:
        print(f"\n[OK]    {cmd}")
        print(f"          -> {snippet}")
        store.record_valid(cmd, device=args.device_label, build=build,
                           notes="config view of local-loop-prevention sub-tree")
    else:
        print(f"\n[BAD]   {cmd}")
        print(f"          -> {snippet}")
        store.record_invalid(cmd, device=args.device_label, build=build)

    # ---------------------------------------------------------------
    # 4) Also walk the parent sub-tree config so the cache has the
    #    sibling 'loop-prevention' menu (per-EVI rather than per-AC).
    # ---------------------------------------------------------------
    cfg_parent = f"show config network-services evpn instance {inst} mac-handling loop-prevention"
    out_p = ssh.send_command(cfg_parent + " | flatten")
    print(f"\n[INFO] dump of config under {cfg_parent} | flatten:")
    print((out_p or "").strip()[:600])
    if _is_valid(out_p):
        store.record_valid(cfg_parent + " | flatten", device=args.device_label, build=build,
                           notes="full per-EVI loop-prevention config dump")

    # ---------------------------------------------------------------
    # 5) Probe the documented timer keywords from the rule
    #    `~/.cursor/rules/test-live-device-validation.mdc`
    #    in CONFIG MODE through `commit check` -> `rollback 0`.
    #    NOTE: this script is read-only by design; instead of entering
    #    config mode, we just record what the rule says vs what the
    #    `?` walk shows so the next agent sees the gap.
    # ---------------------------------------------------------------
    documented_ll_keywords = {
        "restore-timer": "<seconds, 30..86400>",
        "restore-max-cycles": "<int>",
        "reset-restore-cycles-interval": "<seconds>",
    }
    print("\n[INFO] documented LLP keywords from validation rule (per current docs):")
    for kw, hint in documented_ll_keywords.items():
        print(f"       {kw} {hint}")

    print(f"\n[OK] round-3 done; menus + leaves recorded under "
          f"{store.shared_root}/by_protocol/evpn/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
