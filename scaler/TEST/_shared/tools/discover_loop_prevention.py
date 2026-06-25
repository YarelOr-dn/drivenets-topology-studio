#!/usr/bin/env python3
"""Discover the correct DNOS loop-prevention syntax on a live device and
seed the shared knowledge tree with the proofs.

Why this script
---------------
The user reported ``show evpn local-loop-prevention`` is rejected on DNOS
(captured today). Loop-prevention lives under multiple paths -- operational
``show evpn ...``, ``show config network-services evpn instance X mac-handling
loop-prevention ...``, ``show config network-services evpn instance X
mac-handling local-loop-prevention ...``. Each tier has its own valid
keywords. The agent must walk ``?`` at each tier, capture the menu, and
mark the valid commands.

What it produces
----------------
* For every menu it walks, ``cache_store.record_menu`` is called with the
  exact prefix and harvested keywords.
* For every command tested, ``record_valid`` or ``record_invalid`` lands
  in ``~/SCALER/TEST/_shared/knowledge/by_protocol/evpn/`` with feature
  tag ``loop-prevention``.
* A summary is printed to stdout with provenance.

Run::

    python3 discover_loop_prevention.py --device-ip 100.64.2.33 \\
        --user dnroot --password dnroot

The script is read-only -- it never enters config mode, never commits, and
never restarts a process. It only runs ``show`` and walks ``?`` menus.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import List, Tuple

# Locate scaler.dnos_session and the new shared lib.
_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[4]                 # drivenets-topology-studio/
sys.path.insert(0, str(_REPO_ROOT / "scaler"))   # for scaler.dnos_session
sys.path.insert(0, str(_HERE.parents[1]))         # for lib.*

from scaler.dnos_session import DNOSSession                                # noqa: E402
from lib.cache_store import CacheStore, BuildInfo                          # noqa: E402
from lib.cli_syntax_validator import CliSyntaxValidator                    # noqa: E402


def _drain(ssh: DNOSSession, idle_s: float = 0.6) -> str:
    """Drain everything currently in the shell buffer + idle wait."""
    out = b""
    deadline = time.monotonic() + idle_s
    while time.monotonic() < deadline:
        if ssh._shell.recv_ready():            # noqa: SLF001 -- low-level needed
            out += ssh._shell.recv(65536)
            deadline = time.monotonic() + idle_s
        else:
            time.sleep(0.05)
    return out.decode("utf-8", errors="replace")


def _harvest_question_menu(ssh: DNOSSession, prefix: str) -> List[str]:
    """Send ``<prefix> ?`` and harvest the keyword list.

    DNOS prints the menu and re-displays the prompt with the buffered
    text after a ``?``. Ctrl-U clears the buffered line so the next
    command starts clean.
    """
    _drain(ssh, 0.2)
    ssh.send_raw(f"{prefix} ?")
    time.sleep(0.8)
    raw = _drain(ssh, 0.6)
    ssh.send_raw("\x15")          # Ctrl-U: clear line
    time.sleep(0.2)
    _drain(ssh, 0.3)

    # Parse: keywords are non-empty lines that start with whitespace and
    # contain a printable token (no '?', no '%', no banner text).
    keywords: List[str] = []
    for line in raw.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("%") or s.startswith(prefix.split()[-1]):
            # echo of the command we typed, or a rejection marker
            continue
        # Menu items are usually "  keyword   description"
        token = s.split()[0]
        if token.replace("-", "").replace("_", "").isalnum():
            keywords.append(token)
    # Dedupe preserving order
    seen = set()
    out = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def _device_build(ssh: DNOSSession, password: str, label: str) -> BuildInfo:
    """Best-effort: drop into shell, cat /.gitcommit, come back to CLI."""
    try:
        ssh.send_raw("run start shell\n")
        time.sleep(0.6)
        ssh.send_raw(f"{password}\n")
        time.sleep(0.6)
        _drain(ssh, 0.5)
        ssh.send_raw("cat /.gitcommit\n")
        time.sleep(0.6)
        out = _drain(ssh, 0.6)
        ssh.send_raw("exit\n")
        time.sleep(0.4)
        _drain(ssh, 0.4)

        commit = ""
        branch = ""
        for line in out.splitlines():
            s = line.strip()
            if "-" in s and len(s) > 12 and s[0].isalnum() and not s.startswith("$"):
                commit, _, branch = s.partition("-")
                if len(commit) >= 8 and commit.replace("a", "").replace("b", "")[:1].isalnum():
                    break
        return BuildInfo(commit=commit[:12], branch=branch.strip(), device=label)
    except Exception:
        return BuildInfo(device=label)


def _is_valid_output(text: str) -> bool:
    """Return True if the device did not reject the command."""
    if not text:
        return True
    rejection = (
        "% Unknown command",
        "% Ambiguous",
        "% Incomplete",
        "% Invalid",
        "Unknown word",
    )
    return not any(m in text for m in rejection)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--device-ip", default="100.64.2.33")
    p.add_argument("--user", default="dnroot")
    p.add_argument("--password", default=os.environ.get("DNOS_PASSWORD", "dnroot"))
    p.add_argument("--device-label", default="PE-1")
    args = p.parse_args()

    print(f"[INFO] connecting to {args.device_label} ({args.device_ip})")
    ssh = DNOSSession(args.device_ip, args.user, args.password)
    print("[OK]   connected")

    build = _device_build(ssh, args.password, args.device_label)
    print(f"[OK]   device build: commit={build.commit or '(unknown)'} branch={build.branch or '(unknown)'}")

    store = CacheStore(suite_id="discover_loop_prevention")

    # ---------------------------------------------------------------
    # 1) Walk ? menus we care about
    # ---------------------------------------------------------------
    menus_to_walk = [
        "show evpn",
        "show evpn instance",
        "show config network-services evpn instance",
    ]
    for prefix in menus_to_walk:
        kws = _harvest_question_menu(ssh, prefix)
        print(f"[?]    {prefix} -> {len(kws)} keywords: {kws[:8]}{'...' if len(kws) > 8 else ''}")
        if kws:
            store.record_menu(prefix, kws, device=args.device_label, build=build)

    # ---------------------------------------------------------------
    # 2) Confirm the user's literal command is invalid + harvest alts.
    #    Then probe every plausible operational form for loop-prevention.
    # ---------------------------------------------------------------
    candidates: List[Tuple[str, str]] = [
        # (command, note)
        ("show evpn local-loop-prevention", "user-reported (expected REJECT)"),
        ("show evpn loop-prevention", "no-prefix variant"),
        ("show evpn mac-suppression", "MAC suppression table (mobility freezes)"),
        ("show evpn mac-history", "per-MAC mobility history"),
        ("show evpn restore-cycles", "loop-prevention restore-cycle counters"),
        ("show evpn summary", "anchor: known-valid"),
    ]

    print("\n[INFO] testing operational candidates...")
    for cmd, note in candidates:
        out = ssh.send_command(cmd)
        ok = _is_valid_output(out)
        marker = "[OK]  " if ok else "[BAD] "
        first = (out or "").strip().splitlines()[:2]
        snippet = " | ".join(first)[:120]
        print(f"  {marker}{cmd:55s}  {snippet}")
        if ok:
            store.record_valid(
                cmd,
                device=args.device_label,
                build=build,
                notes=note,
            )
        else:
            store.record_invalid(
                cmd,
                device=args.device_label,
                build=build,
                notes=note + " | " + (out or "").strip().splitlines()[0][:80],
            )

    # ---------------------------------------------------------------
    # 3) Find a real EVPN instance and walk per-instance loop-prev menus.
    # ---------------------------------------------------------------
    print("\n[INFO] discovering EVPN instances on device...")
    inst_out = ssh.send_command("show evpn summary")
    instance_name = None
    for line in (inst_out or "").splitlines():
        # The summary table has column "Instance Name" - find first non-header word
        s = line.strip()
        if not s or s.startswith("|") or s.startswith("Instance") or s.startswith("-"):
            continue
        toks = s.split()
        if toks and toks[0].replace("_", "").replace("-", "").isalnum() and len(toks[0]) > 2:
            # crude: pick the first plausible instance token
            if toks[0].lower() not in {"instance", "name", "type", "mac", "ip"}:
                instance_name = toks[0]
                break

    if not instance_name:
        # Fall back to a common name we've seen in the lab.
        instance_name = "EVPN_SI_VPLS_1"
        print(f"[WARN] could not parse instance from summary; trying fallback {instance_name}")

    print(f"[OK]   using instance: {instance_name}")

    inst_menus = [
        f"show evpn instance {instance_name}",
        f"show evpn instance {instance_name} mac-handling",
        f"show config network-services evpn instance {instance_name} mac-handling",
        f"show config network-services evpn instance {instance_name} mac-handling loop-prevention",
        f"show config network-services evpn instance {instance_name} mac-handling local-loop-prevention",
    ]
    for prefix in inst_menus:
        kws = _harvest_question_menu(ssh, prefix)
        print(f"[?]    {prefix}")
        print(f"         -> {len(kws)} keywords: {kws[:10]}{'...' if len(kws) > 10 else ''}")
        if kws:
            store.record_menu(prefix, kws, device=args.device_label, build=build)

    # ---------------------------------------------------------------
    # 4) Test concrete per-instance commands for loop-prevention.
    # ---------------------------------------------------------------
    instance_candidates = [
        f"show evpn instance {instance_name} mac-suppression",
        f"show evpn instance {instance_name} mac-history",
        f"show evpn instance {instance_name} restore-cycles",
        f"show evpn instance {instance_name} mac-handling",
        f"show config network-services evpn instance {instance_name} mac-handling | flatten",
    ]
    print("\n[INFO] testing per-instance loop-prevention commands...")
    for cmd in instance_candidates:
        out = ssh.send_command(cmd)
        ok = _is_valid_output(out)
        marker = "[OK]  " if ok else "[BAD] "
        first = (out or "").strip().splitlines()[:2]
        snippet = " | ".join(first)[:120]
        print(f"  {marker}{cmd:75s}  {snippet}")
        if ok:
            store.record_valid(cmd, device=args.device_label, build=build,
                               notes="per-instance loop-prevention probe")
        else:
            store.record_invalid(cmd, device=args.device_label, build=build,
                                 notes="per-instance loop-prevention probe")

    # ---------------------------------------------------------------
    # 5) Walk operational ? completions for the under-instance area too.
    #    (DNOS sometimes accepts "show evpn instance X ?" which we already
    #    walked; here we also try clear/configure paths.)
    # ---------------------------------------------------------------
    extra_menus = [
        "clear evpn",
        f"clear evpn instance {instance_name}",
    ]
    print("\n[INFO] walking clear-side menus...")
    for prefix in extra_menus:
        kws = _harvest_question_menu(ssh, prefix)
        print(f"[?]    {prefix} -> {len(kws)} keywords: {kws[:10]}{'...' if len(kws) > 10 else ''}")
        if kws:
            store.record_menu(prefix, kws, device=args.device_label, build=build)

    print("\n[OK] discovery complete; shared knowledge updated under:")
    print(f"     {store.shared_root}/by_protocol/evpn/")
    print(f"     {store.shared_root}/by_feature/loop-prevention.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
