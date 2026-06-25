#!/usr/bin/env python3
"""Auto-find DNOS syntax for one or more keywords -- the fast path.

Replaces the four-script ``discover_loop_prevention_v{1..4}.py`` chain with
a single tool driven by the built-in DNOS ``cmd search`` operator.

Usage
-----

    # Discover and cache every command containing 'loop-prevention':
    python3 auto_find_syntax.py --device-ip 100.64.10.22 \\
            --keywords loop-prevention mac-handling

    # Optional: validate a list of concrete commands against the discovered
    # templates (no live device round-trips for matched ones):
    python3 auto_find_syntax.py --device-ip 100.64.10.22 \\
            --keywords loop-prevention \\
            --validate-cmds "show evpn instance EVPN_SI_VPLS_1 loop-prevention mac-table"

What it does
------------

1. Connects to the device once via :class:`DNOSSession`.
2. For each keyword, runs ``cmd search <keyword>`` (one round-trip ~3s).
3. Parses every line into ``{show, clear, configure, request}`` buckets.
4. Records every template into the shared knowledge tier
   (``~/SCALER/TEST/_shared/knowledge/``):

   * ``record_valid`` per template (placeholders preserved).
   * ``record_menu`` keyed by ``cmd_search:<keyword>`` for fast browsing.

5. (Optional) For each ``--validate-cmds`` item, prints whether it matches
   any discovered template (so the agent can confirm a recipe will be
   accepted before pushing it to the device).

The tool is **read-only**: it never enters config mode and never
commits. It is also **build-aware** -- the build commit is read from
``/.gitcommit`` so cache entries are stamped with the correct image.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import List

_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[4]
sys.path.insert(0, str(_REPO_ROOT / "scaler"))     # for scaler.dnos_session
sys.path.insert(0, str(_HERE.parents[1]))            # for lib.*

from scaler.dnos_session import DNOSSession                                # noqa: E402
from lib.cache_store import CacheStore, BuildInfo                          # noqa: E402
from lib.cmd_search import (                                                # noqa: E402
    CmdSearch,
    template_matches_command,
)
import re                                                                   # noqa: E402

_PLACEHOLDER_RE = re.compile(r"<<?[A-Za-z_][A-Za-z0-9_]*>?>|\{[^}]+\}")
_REJECT_RE = re.compile(r"ERROR:\s*Unknown word", re.IGNORECASE)
_STOP_TOKENS = {
    "show", "clear", "no", "set", "|", "no-more", "include",
    "route-type", "route", "route-types",
}


def _discriminator_keywords(command: str, top_n: int = 3) -> List[str]:
    """Pick the top-N most-specific tokens from a command for cmd_search.

    Sorts by (-len, -hyphen_count) so multi-hyphen compounds like
    'mac-address-table' are tried before generic words like 'instance'.
    """
    no_pipes = re.sub(r"\s*\|.*$", "", command).strip()
    toks = []
    for t in no_pipes.split():
        if _PLACEHOLDER_RE.fullmatch(t):
            continue
        if t in _STOP_TOKENS:
            continue
        toks.append(t)
    seen = set()
    uniq = []
    for t in toks:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return sorted(uniq, key=lambda t: (-len(t), -t.count("-")))[:top_n]


def _safe_literal(command: str) -> str:
    """Substitute placeholders with concrete sentinels for a live read probe."""
    s = command
    s = re.sub(r"\{evpn_name\}|\{name\}|\{evi\}|\{pw_evpn_name\}", "TEST_EVI", s)
    s = re.sub(r"\{test_mac\}|\{mac\}", "00:de:ad:00:01:01", s)
    s = re.sub(r"<peer>", "1.2.3.4", s)
    s = re.sub(r"\{[^}]+\}", "TEST_VALUE", s)
    s = re.sub(r"<[^>]+>", "TEST_VALUE", s)
    s = re.sub(r"\s*\|\s*include[^|]*", "", s).strip()
    return s


def _auto_investigate(
    command: str,
    finder: "CmdSearch",
    store: CacheStore,
    build: BuildInfo,
    feature_tag: str | None,
) -> dict:
    """Step 1-5 chain. Returns {'status': str, 'evidence': [str, ...]}."""
    evidence: List[str] = []

    # ----- Step 1: cmd_search with top-3 discriminator keywords ----------
    keywords = _discriminator_keywords(command)
    evidence.append(f"step1 keywords: {keywords}")
    for kw in keywords:
        try:
            res = finder.search_and_record(
                kw, store, build=build, feature_tag_hint=feature_tag,
            )
        except Exception as exc:                                # noqa: BLE001
            evidence.append(f"  cmd_search '{kw}' failed: {exc}")
            continue
        templates = res.templates
        evidence.append(f"  cmd_search '{kw}' -> {len(templates)} templates")
        for t in templates:
            if template_matches_command(t, command):
                evidence.append(f"  matched template: {t}")
                return {"status": "RESOLVED", "evidence": evidence}

    # ----- Step 2: live read probe (only for show forms) -----------------
    if command.lstrip().startswith("show "):
        literal = _safe_literal(command)
        evidence.append(f"step2 literal probe: {literal}")
        try:
            ssh = finder._ssh                                   # noqa: SLF001
            output = ssh.send_command(literal)
        except Exception as exc:                                # noqa: BLE001
            evidence.append(f"  probe failed: {exc}")
        else:
            if _REJECT_RE.search(output):
                evidence.append("  device rejected: ERROR Unknown word")
            else:
                first = next((ln for ln in output.splitlines() if ln.strip()), "")
                evidence.append(f"  device accepted; sample: {first[:120]}")
                return {"status": "RESOLVED-LIVE", "evidence": evidence}

    # ----- Step 3: negation positive form --------------------------------
    if command.lstrip().startswith("no "):
        positive = command.lstrip()[3:]
        evidence.append(f"step3 negation positive form: {positive}")
        sub = _auto_investigate(positive, finder, store, build, feature_tag)
        if sub["status"].startswith("RESOLVED"):
            evidence.extend(["  " + e for e in sub["evidence"]])
            return {"status": "RESOLVED-NEGATION", "evidence": evidence}

    # ----- Step 4 (commit-check) is left to validate_config integration --
    # ----- Step 5: confirmed invalid --------------------------------------
    return {"status": "CONFIRMED-INVALID", "evidence": evidence}


def _read_build(ssh: DNOSSession, password: str, label: str) -> BuildInfo:
    """Best-effort: drop into shell, cat /.gitcommit, return BuildInfo."""
    try:
        ssh.send_raw("run start shell\n")
        time.sleep(0.6)
        ssh.send_raw(f"{password}\n")
        time.sleep(0.6)
        # drain
        if ssh._shell.recv_ready():                                        # noqa: SLF001
            ssh._shell.recv(65536)
        ssh.send_raw("cat /.gitcommit\n")
        time.sleep(0.6)
        out = b""
        deadline = time.monotonic() + 1.5
        while time.monotonic() < deadline:
            if ssh._shell.recv_ready():                                    # noqa: SLF001
                out += ssh._shell.recv(65536)
                deadline = time.monotonic() + 0.6
            else:
                time.sleep(0.05)
        ssh.send_raw("exit\n")
        time.sleep(0.4)
        if ssh._shell.recv_ready():                                        # noqa: SLF001
            ssh._shell.recv(65536)
        text = out.decode("utf-8", errors="replace")

        commit = ""
        branch = ""
        for line in text.splitlines():
            s = line.strip()
            # /.gitcommit always looks like <hex>-<branch>
            if "-" in s and len(s) > 16 and s.split("-")[0].isalnum():
                commit, _, branch = s.partition("-")
                if len(commit) >= 8:
                    break
        return BuildInfo(commit=commit[:12], branch=branch.strip(), device=label)
    except Exception:
        return BuildInfo(device=label)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Discover DNOS syntax for one or more keywords using "
                    "the built-in `cmd search` operator + shared cache.",
    )
    p.add_argument("--device-ip", default="100.64.10.22",
                   help="Device management IP (default: PE-4)")
    p.add_argument("--user", default="dnroot")
    p.add_argument("--password", default=os.environ.get("DNOS_PASSWORD", "dnroot"))
    p.add_argument("--device-label", default="PE-4")
    p.add_argument("--keywords", nargs="+", required=True,
                   help="One or more single-token keywords to search (e.g. "
                        "loop-prevention mac-handling restore-timer)")
    p.add_argument("--feature-tag", default=None,
                   help="Optional feature tag stored in the cache for "
                        "provenance (e.g. 'evpn-loop-prevention')")
    p.add_argument("--suite-id", default="auto_find_syntax",
                   help="Suite id stamped on every cache write")
    p.add_argument("--validate-cmds", nargs="*", default=[],
                   help="Concrete commands to test against the discovered "
                        "templates (offline -- no device round-trip)")
    p.add_argument("--show-only", action="store_true",
                   help="Print only the 'show' commands (useful for grep-aside)")
    p.add_argument("--limit-per-surface", type=int, default=0,
                   help="If > 0, print at most N templates per surface")
    args = p.parse_args()

    print(f"[INFO] connecting to {args.device_label} ({args.device_ip})")
    ssh = DNOSSession(args.device_ip, args.user, args.password)
    print("[OK]   connected")

    build = _read_build(ssh, args.password, args.device_label)
    print(f"[OK]   build: commit={build.commit or '(unknown)'} branch={build.branch or '(unknown)'}")

    store = CacheStore(suite_id=args.suite_id)
    finder = CmdSearch(ssh, label=args.device_label, default_timeout=30)

    grand_total = 0
    surface_totals = {"show": 0, "clear": 0, "configure": 0, "request": 0, "run": 0, "set": 0}

    for kw in args.keywords:
        print(f"\n[?]    cmd search {kw}")
        result = finder.search_and_record(
            kw, store, build=build, feature_tag_hint=args.feature_tag,
        )
        if result.error and not result.templates:
            print(f"  [BAD] {result.error}")
            continue
        print(f"  [OK]  {result.total_count} templates in {result.elapsed_s:.2f}s "
              f"(show={len(result.by_surface.get('show', []))}  "
              f"clear={len(result.by_surface.get('clear', []))}  "
              f"configure={len(result.by_surface.get('configure', []))}  "
              f"request={len(result.by_surface.get('request', []))})")
        grand_total += result.total_count
        for s, group in result.by_surface.items():
            surface_totals[s] = surface_totals.get(s, 0) + len(group)

        if args.show_only:
            for tmpl in result.by_surface.get("show", []):
                if args.limit_per_surface and surface_totals["show"] > args.limit_per_surface:
                    break
                print(f"     [SHOW] {tmpl}")
        else:
            for surface in ("show", "clear", "configure", "request"):
                items = result.by_surface.get(surface, [])
                limit = args.limit_per_surface or len(items)
                for tmpl in items[:limit]:
                    print(f"     [{surface.upper():9s}] {tmpl}")
                if items and limit < len(items):
                    print(f"     [{surface.upper():9s}] ... +{len(items) - limit} more")

    if args.validate_cmds:
        print("\n[INFO] validating concrete commands against discovered templates...")
        # Build template index from store + memory
        all_templates: List[str] = []
        for kw in args.keywords:
            menu = store.menu_for_prefix(f"cmd_search:{kw}") or []
            all_templates.extend(menu)
        all_templates = sorted(set(all_templates))

        # Auto-investigation chain (rule: test-mcp-auto-investigate-miss).
        # No command may be reported as MISS without first running the full
        # chain: Step 1 (broader cmd_search keywords) -> Step 2 (live read
        # probe) -> Step 3 (negation positive form). Only after all three
        # gates fail does the verdict become CONFIRMED-INVALID.
        for cmd in args.validate_cmds:
            cmd_clean = cmd.strip()
            matches = [t for t in all_templates if template_matches_command(t, cmd_clean)]
            if matches:
                print(f"  [RESOLVED] {cmd_clean!r}")
                for m in matches[:3]:
                    print(f"             matches template: {m}")
                continue

            # ----- Step 1: broaden cmd_search to top-3 specific tokens -----
            verdict = _auto_investigate(
                cmd_clean, finder, store, build, args.feature_tag,
            )
            tag = verdict["status"]
            print(f"  [{tag}] {cmd_clean!r}")
            for line in verdict["evidence"]:
                print(f"             {line}")

    print(f"\n[OK] grand total: {grand_total} templates discovered across {len(args.keywords)} keyword(s)")
    print(f"     surfaces: {surface_totals}")
    print(f"     cache root: {store.shared_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
