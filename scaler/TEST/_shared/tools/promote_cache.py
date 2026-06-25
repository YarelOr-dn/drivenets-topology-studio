#!/usr/bin/env python3
"""Promote suite-local cache entries into the shared knowledge tree.

Three modes (combinable via flags):

* **Auto-promote ``--auto``**: walks every suite's ``cli_validation_cache.json``
  and lifts entries that meet ANY of:
  - ``pass_count >= PROMOTE_MIN_PASS_COUNT`` (default 3)
  - validated on ``PROMOTE_MIN_DEVICES`` distinct devices (default 2)
  - validated on ``PROMOTE_MIN_BUILDS`` distinct builds (default 2)

* **Manual ``--command "<cmd>"``**: promote one specific command from the
  named suite even if it doesn't meet the auto thresholds.

* **Dry-run ``--dry-run``**: print what *would* be promoted without writing.

Promoted entries are kept in the suite file (auditable) but also appear in
``~/SCALER/TEST/_shared/knowledge/by_protocol/<bucket>/...`` where every
future suite reads them.

Examples::

    # Run periodically (e.g. nightly cron) to lift mature entries
    python3 scaler/TEST/_shared/tools/promote_cache.py --auto --all

    # Promote one command from one suite manually
    python3 scaler/TEST/_shared/tools/promote_cache.py \
        --suite scaler/TEST/catalog/evpn_mac_mobility_SW204115 \
        --command "show evpn instance EVPN_SI_VPLS_1 mac-table"

    # See the plan without writing
    python3 scaler/TEST/_shared/tools/promote_cache.py --auto --all --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
sys.path.insert(0, str(_HERE.parent.parent))

from lib.cache_store import (  # noqa: E402
    CacheEntry,
    CacheStore,
    PROMOTE_MIN_BUILDS,
    PROMOTE_MIN_DEVICES,
    PROMOTE_MIN_PASS_COUNT,
)


def discover_suites(catalog_root: Path) -> list[Path]:
    if not catalog_root.exists():
        return []
    return [p for p in catalog_root.iterdir() if p.is_dir()]


def promote_auto(suite_dir: Path, shared_root: Path, dry_run: bool) -> dict:
    cache_path = suite_dir / "tools" / "cli_validation_cache.json"
    if not cache_path.exists():
        return {"suite": suite_dir.name, "skipped": "no cache file"}

    store = CacheStore(
        shared_root=shared_root,
        suite_cache=cache_path,
        suite_id=suite_dir.name,
    )

    if dry_run:
        # Inspect the suite cache directly without writing.
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        plan = {"validated_promotable": [], "invalid_promotable": []}
        for cmd, payload in (data.get("validated_commands") or {}).items():
            entry = CacheEntry.from_dict({**payload, "command": cmd})
            entry.valid = True
            if store.is_promotable(entry):
                plan["validated_promotable"].append(cmd)
        for cmd, payload in (data.get("known_invalid") or {}).items():
            entry = CacheEntry.from_dict({**payload, "command": cmd})
            entry.valid = False
            if store.is_promotable(entry):
                plan["invalid_promotable"].append(cmd)
        return {"suite": suite_dir.name, **plan}

    return {"suite": suite_dir.name, **store.promote_suite()}


def promote_one(suite_dir: Path, shared_root: Path, command: str) -> dict:
    cache_path = suite_dir / "tools" / "cli_validation_cache.json"
    if not cache_path.exists():
        return {"suite": suite_dir.name, "error": "no cache file"}
    data = json.loads(cache_path.read_text(encoding="utf-8"))
    found = None
    bucket = None
    for b in ("validated_commands", "known_invalid"):
        if command in (data.get(b) or {}):
            found = data[b][command]
            bucket = b
            break
    if not found:
        return {"suite": suite_dir.name, "error": f"command not found: {command}"}

    store = CacheStore(
        shared_root=shared_root,
        suite_cache=cache_path,
        suite_id=suite_dir.name,
    )
    entry = CacheEntry.from_dict({**found, "command": command})
    entry.valid = bucket == "validated_commands"
    store._merge_into_shared(entry)  # noqa: SLF001 (intentional)
    return {"suite": suite_dir.name, "promoted": command}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description="Promote suite-local /TEST cache entries to shared knowledge.",
    )
    p.add_argument("--auto", action="store_true",
                   help="Auto-promote entries meeting the thresholds.")
    p.add_argument("--command", default=None,
                   help="Promote one specific command (requires --suite).")
    p.add_argument("--suite", default=None,
                   help="Path to a single suite dir.")
    p.add_argument("--all", action="store_true",
                   help="With --auto, scan every suite under catalog/.")
    p.add_argument("--catalog-root", default=None)
    p.add_argument("--shared-root", default=None)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    catalog_root = (
        Path(args.catalog_root).expanduser()
        if args.catalog_root
        else _HERE.parents[2] / "catalog"
    )
    shared_root = (
        Path(args.shared_root).expanduser()
        if args.shared_root
        else _HERE.parents[1] / "knowledge"
    )

    print(f"thresholds: passes>={PROMOTE_MIN_PASS_COUNT}  "
          f"devices>={PROMOTE_MIN_DEVICES}  builds>={PROMOTE_MIN_BUILDS}")
    print(f"shared_root: {shared_root}")
    print(f"dry_run: {args.dry_run}")
    print()

    if args.command:
        if not args.suite:
            print("--command requires --suite", file=sys.stderr)
            return 2
        result = promote_one(Path(args.suite), shared_root, args.command)
        print(result)
        return 0 if "promoted" in result else 1

    if not args.auto:
        print("nothing to do (pass --auto or --command)", file=sys.stderr)
        return 2

    if args.all:
        suites = discover_suites(catalog_root)
    elif args.suite:
        suites = [Path(args.suite).expanduser()]
    else:
        print("--auto requires --all or --suite", file=sys.stderr)
        return 2

    for s in suites:
        result = promote_auto(s, shared_root, dry_run=args.dry_run)
        if "skipped" in result:
            print(f"  [skip] {result['suite']}  {result['skipped']}")
        elif args.dry_run:
            v = result.get("validated_promotable", [])
            i = result.get("invalid_promotable", [])
            print(f"  [plan] {result['suite']}  validated={len(v)}  invalid={len(i)}")
            for c in v:
                print(f"           + {c}")
            for c in i:
                print(f"           - {c}")
        else:
            print(
                f"  [ok]   {result['suite']}  "
                f"validated_promoted={result.get('validated_promoted', 0)}  "
                f"invalid_promoted={result.get('invalid_promoted', 0)}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
