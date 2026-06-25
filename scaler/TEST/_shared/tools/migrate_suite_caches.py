#!/usr/bin/env python3
"""Migrate per-suite ``cli_validation_cache.json`` files into the shared
knowledge tree under ``~/SCALER/TEST/_shared/knowledge/``.

Run once per suite to lift its accumulated proofs (validated commands,
known-invalid commands, completion menus) into the cross-suite layer.
After migration, every future /TEST suite (any feature, any ticket) starts
with the same knowledge for free.

Usage::

    python3 scaler/TEST/_shared/tools/migrate_suite_caches.py --all
    python3 scaler/TEST/_shared/tools/migrate_suite_caches.py \
            --suite scaler/TEST/catalog/evpn_mac_mobility_SW204115

The migration is **non-destructive**: the suite-local file stays untouched.
Re-running is safe -- merging into existing shared entries just bumps
counters / appends devices.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

# Locate the _shared/lib package regardless of CWD.
_HERE = Path(__file__).resolve()
_LIB = _HERE.parent.parent / "lib"
sys.path.insert(0, str(_LIB.parent))

from lib.cache_store import CacheStore, CacheEntry, BuildInfo  # noqa: E402


def discover_suites(catalog_root: Path) -> Iterable[Path]:
    if not catalog_root.exists():
        return []
    return [p for p in catalog_root.iterdir() if p.is_dir()]


def migrate_one(
    suite_dir: Path,
    shared_root: Path,
    dry_run: bool = False,
) -> dict:
    cache_path = suite_dir / "tools" / "cli_validation_cache.json"
    if not cache_path.exists():
        return {"suite": suite_dir.name, "skipped": "no cache file"}

    raw = json.loads(cache_path.read_text(encoding="utf-8"))
    suite_id = suite_dir.name

    store = CacheStore(
        shared_root=shared_root,
        suite_cache=cache_path,           # so we don't re-write a copy
        suite_id=suite_id,
    )

    stats = {
        "suite": suite_id,
        "validated": 0,
        "invalid": 0,
        "menus": 0,
        "feature_index_entries": 0,
    }

    # 1) validated_commands -> shared
    for cmd, payload in (raw.get("validated_commands") or {}).items():
        if dry_run:
            stats["validated"] += 1
            continue
        devices = payload.get("validated_on_devices") or []
        device = devices[0] if devices else ""
        binfo = BuildInfo(
            device=device,
            commit="",
            branch=str(payload.get("build_seen", "")),
        )
        # Use record_valid; merge_proof handles dup-friendly counters.
        # passes>1 in the suite file should propagate -- so call N times.
        passes = max(1, int(payload.get("passes", 1) or 1))
        for _ in range(passes):
            store.record_valid(
                cmd,
                device=device,
                build=binfo,
                notes=payload.get("note", "") or payload.get("notes", ""),
            )
        stats["validated"] += 1

    # 2) known_invalid -> shared
    for cmd, payload in (raw.get("known_invalid") or {}).items():
        if dry_run:
            stats["invalid"] += 1
            continue
        store.record_invalid(
            cmd,
            alternatives=payload.get("valid_alternatives") or [],
            notes=payload.get("rejection", "") or "",
        )
        stats["invalid"] += 1

    # 3) completion_menus -> shared
    for prefix, tokens in (raw.get("completion_menus") or {}).items():
        if dry_run:
            stats["menus"] += 1
            continue
        if isinstance(tokens, dict):
            tokens_list = list(tokens.get("keywords", []))
        else:
            tokens_list = list(tokens)
        store.record_menu(prefix, tokens_list, device="")
        stats["menus"] += 1

    return stats


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Migrate suite caches to shared knowledge.")
    p.add_argument("--suite", action="append", default=[],
                   help="Path to a single suite dir; can be repeated.")
    p.add_argument("--all", action="store_true",
                   help="Discover and migrate every suite under "
                        "scaler/TEST/catalog/.")
    p.add_argument("--catalog-root", default=None,
                   help="Override the catalog root (default: auto-detect).")
    p.add_argument("--shared-root", default=None,
                   help="Override the shared knowledge root.")
    p.add_argument("--dry-run", action="store_true",
                   help="Print what would be migrated, but write nothing.")
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

    suites: list[Path]
    if args.all:
        suites = list(discover_suites(catalog_root))
    else:
        suites = [Path(s).expanduser() for s in args.suite]

    if not suites:
        print("no suites to migrate", file=sys.stderr)
        return 2

    print(f"shared_root: {shared_root}")
    print(f"catalog_root: {catalog_root}")
    print(f"dry_run: {args.dry_run}")
    print()

    total = {"validated": 0, "invalid": 0, "menus": 0, "suites_with_data": 0}
    for s in suites:
        stats = migrate_one(s, shared_root, dry_run=args.dry_run)
        if "skipped" in stats:
            print(f"  [skip] {stats['suite']:50s}  {stats['skipped']}")
            continue
        print(
            f"  [ok]   {stats['suite']:50s}  "
            f"valid={stats['validated']:3d}  "
            f"invalid={stats['invalid']:3d}  "
            f"menus={stats['menus']:3d}"
        )
        total["validated"] += stats["validated"]
        total["invalid"] += stats["invalid"]
        total["menus"] += stats["menus"]
        if stats["validated"] or stats["invalid"] or stats["menus"]:
            total["suites_with_data"] += 1

    print()
    print(
        f"summary: {total['suites_with_data']} suite(s) had data, "
        f"validated={total['validated']}, "
        f"invalid={total['invalid']}, "
        f"menus={total['menus']}"
    )

    # Snapshot final state.
    if not args.dry_run:
        store = CacheStore(shared_root=shared_root, suite_id="migrate_tool")
        snap = store.snapshot_stats()
        print()
        print("shared knowledge after migration:")
        for proto, counts in sorted(snap["by_protocol"].items()):
            print(
                f"  by_protocol/{proto:12s}  validated={counts['validated']:3d}  "
                f"invalid={counts['invalid']:2d}  menus={counts['menus']:2d}"
            )
        print()
        for feature, n in sorted(snap["by_feature"].items()):
            print(f"  by_feature/{feature:30s}  commands={n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
