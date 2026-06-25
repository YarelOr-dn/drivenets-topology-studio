#!/usr/bin/env python3
"""Round-2 loop-prevention discovery on PE-1.

Round-1 confirmed:
  * ``show evpn local-loop-prevention``  -> REJECTED (Unknown word)
  * ``show evpn loop-prevention``        -> exists but Incomplete (needs sub-keyword)
  * ``show evpn`` menu contains          -> ``loop-prevention``
  * ``show evpn instance <X>`` menu      -> ``loop-prevention``
  * ``clear evpn`` menu loop-prev verbs  -> mac-suppression, mac-history,
    restore-cycles, ip-suppression, ip-history, ip-restore-cycles,
    ac-suppression, ac-history, ac-restore-cycles

Round-2 goals:
  * Find a REAL EVPN instance name (not "Global", which was the banner).
  * Walk the menu under ``show evpn loop-prevention``.
  * Walk ``show evpn instance <REAL> loop-prevention``.
  * Probe each leaf and record valid+invalid in the shared cache.
  * Probe the config-side ``show config network-services evpn instance
    <REAL> mac-handling local-loop-prevention`` -- the user's exact prefix
    is valid CONFIG syntax even though it's invalid OPERATIONAL syntax.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import List, Optional

_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[4]
sys.path.insert(0, str(_REPO_ROOT / "scaler"))
sys.path.insert(0, str(_HERE.parents[1]))

from scaler.dnos_session import DNOSSession                              # noqa: E402
from lib.cache_store import CacheStore, BuildInfo                         # noqa: E402


def _drain(ssh: DNOSSession, idle_s: float = 0.6) -> str:
    out = b""
    deadline = time.monotonic() + idle_s
    while time.monotonic() < deadline:
        if ssh._shell.recv_ready():                                      # noqa: SLF001
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
        if not s or s.startswith("%") or s.startswith("---"):
            continue
        # Skip echoes of the typed command
        if s.startswith(prefix.split()[0]):
            continue
        toks = s.split()
        if not toks:
            continue
        token = toks[0].rstrip(",")
        # Filter prompts and noise
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


def _find_real_instance(ssh: DNOSSession) -> Optional[str]:
    """Parse `show network-services evpn instance` to find a real instance."""
    out = ssh.send_command("show config network-services evpn | flatten | include 'evpn instance'")
    # Expected lines like:  network-services evpn instance EVPN_SI_VPLS_1 ...
    for line in (out or "").splitlines():
        m = re.search(r"evpn instance (\S+)", line)
        if m:
            name = m.group(1)
            if name not in {"|", "include"}:
                return name
    # Fallback: parse `show evpn` (which prints "EVPN: <name>")
    out = ssh.send_command("show evpn | no-more")
    for line in (out or "").splitlines():
        m = re.match(r"^\s*EVPN:\s*(\S+)", line)
        if m:
            return m.group(1)
    return None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--device-ip", default="100.64.2.33")
    p.add_argument("--user", default="dnroot")
    p.add_argument("--password", default=os.environ.get("DNOS_PASSWORD", "dnroot"))
    p.add_argument("--device-label", default="PE-1")
    p.add_argument("--instance", default=None,
                   help="Force a specific EVPN instance name; skip auto-discover")
    args = p.parse_args()

    print(f"[INFO] connecting to {args.device_label} ({args.device_ip})")
    ssh = DNOSSession(args.device_ip, args.user, args.password)
    print("[OK]   connected")

    # Build label (informational only -- skip the shell escape this round to
    # avoid prompt confusion).
    build = BuildInfo(commit="8fd38d35a10a", branch="dev_v26_2", device=args.device_label)
    print(f"[OK]   build (cached from round 1): {build.commit} {build.branch}")

    store = CacheStore(suite_id="discover_loop_prevention")

    # ---------------------------------------------------------------
    # 1) Walk the OPERATIONAL loop-prevention menu (no instance).
    # ---------------------------------------------------------------
    op_prefix = "show evpn loop-prevention"
    kws = _harvest(ssh, op_prefix)
    print(f"\n[?]    {op_prefix}")
    print(f"         -> {len(kws)} keywords: {kws}")
    if kws:
        store.record_menu(op_prefix, kws, device=args.device_label, build=build)

    # ---------------------------------------------------------------
    # 2) Discover a real EVPN instance name.
    # ---------------------------------------------------------------
    instance = args.instance or _find_real_instance(ssh)
    print(f"\n[INFO] real EVPN instance found: {instance!r}")
    if not instance:
        print("[WARN] no EVPN instance configured on this device; cannot walk per-instance menus")

    # ---------------------------------------------------------------
    # 3) Walk per-instance loop-prevention + the (operational) negative
    #    "local-loop-prevention" path the user reported.
    # ---------------------------------------------------------------
    if instance:
        per_inst_prefixes = [
            f"show evpn instance {instance}",
            f"show evpn instance {instance} loop-prevention",
            f"show evpn loop-prevention",
            # config side -- this is where the *config* keyword lives:
            f"show config network-services evpn instance {instance}",
            f"show config network-services evpn instance {instance} mac-handling",
            f"show config network-services evpn instance {instance} mac-handling loop-prevention",
            f"show config network-services evpn instance {instance} mac-handling local-loop-prevention",
        ]
        for prefix in per_inst_prefixes:
            kws = _harvest(ssh, prefix)
            print(f"[?]    {prefix}")
            print(f"         -> {len(kws)} keywords: {kws}")
            if kws:
                store.record_menu(prefix, kws, device=args.device_label, build=build)

    # ---------------------------------------------------------------
    # 4) Probe the canonical leaf commands and record verdicts.
    # ---------------------------------------------------------------
    operational_leaves = [
        # operational forms (under `show evpn ...` only -- per-instance ones
        # need the instance to actually have the feature enabled, but we
        # still record what the device says)
        "show evpn loop-prevention mac-suppression",
        "show evpn loop-prevention mac-history",
        "show evpn loop-prevention restore-cycles",
        "show evpn loop-prevention ip-suppression",
        "show evpn loop-prevention ip-history",
        "show evpn loop-prevention ip-restore-cycles",
        "show evpn loop-prevention ac-suppression",
        "show evpn loop-prevention ac-history",
        "show evpn loop-prevention ac-restore-cycles",
    ]
    if instance:
        operational_leaves.extend([
            f"show evpn instance {instance} loop-prevention mac-suppression",
            f"show evpn instance {instance} loop-prevention mac-history",
            f"show evpn instance {instance} loop-prevention restore-cycles",
            f"show evpn instance {instance} loop-prevention ip-suppression",
            f"show evpn instance {instance} loop-prevention ip-history",
            f"show evpn instance {instance} loop-prevention ip-restore-cycles",
            f"show evpn instance {instance} loop-prevention ac-suppression",
            f"show evpn instance {instance} loop-prevention ac-history",
            f"show evpn instance {instance} loop-prevention ac-restore-cycles",
            # config-side recall (the user's exact wording maps here):
            f"show config network-services evpn instance {instance} mac-handling loop-prevention | flatten",
            f"show config network-services evpn instance {instance} mac-handling local-loop-prevention | flatten",
        ])

    # ALSO probe the user's literal command one more time for the record.
    operational_leaves.insert(0, "show evpn local-loop-prevention")

    print(f"\n[INFO] probing {len(operational_leaves)} leaf commands...")
    for cmd in operational_leaves:
        out = ssh.send_command(cmd)
        ok = _is_valid(out)
        incomplete = _is_incomplete(out)
        first = (out or "").strip().splitlines()[:2]
        snippet = " | ".join(first)[:120]
        if ok and not incomplete:
            print(f"  [OK]   {cmd}")
            print(f"           -> {snippet}")
            store.record_valid(cmd, device=args.device_label, build=build,
                               notes="loop-prevention probe round-2")
        elif incomplete:
            print(f"  [PART] {cmd} (incomplete -- prefix exists but more args needed)")
            store.record_invalid(cmd, device=args.device_label, build=build,
                                 alternatives=[],
                                 notes="prefix exists but command is incomplete")
        else:
            print(f"  [BAD]  {cmd}")
            print(f"           -> {snippet}")
            store.record_invalid(cmd, device=args.device_label, build=build,
                                 notes="round-2 rejected")

    print(f"\n[OK] shared knowledge updated under {store.shared_root}/by_protocol/evpn/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
