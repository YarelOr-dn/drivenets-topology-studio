#!/usr/bin/env python3
"""Browse the shared /TEST knowledge tree.

Use cases:

* Quickly answer "what EVPN commands does the agent already know?":
  ``python3 browse_knowledge.py --protocol evpn``

* Find every command tagged with a feature (works across protocol buckets):
  ``python3 browse_knowledge.py --feature evpn-vpls-si``

* Dump everything the agent has proven, grouped by protocol:
  ``python3 browse_knowledge.py --tree``

* See the cross-suite contribution map (who proved what):
  ``python3 browse_knowledge.py --provenance``
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

_HERE = Path(__file__).resolve()
sys.path.insert(0, str(_HERE.parent.parent))

from lib.cache_store import CacheStore  # noqa: E402


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def show_protocol(shared_root: Path, protocol: str) -> int:
    proto_dir = shared_root / "by_protocol" / protocol
    if not proto_dir.exists():
        print(f"no such protocol bucket: {protocol}", file=sys.stderr)
        return 2
    validated = _load(proto_dir / "validated_commands.json")
    invalid = _load(proto_dir / "known_invalid.json")
    menus = _load(proto_dir / "completion_menus.json")

    print(f"== {protocol} == ({proto_dir})")
    print(f"  validated: {len(validated)}, invalid: {len(invalid)}, menus: {len(menus)}")
    print()
    if validated:
        print("  Validated commands:")
        for cmd, p in sorted(validated.items()):
            tags = ",".join(p.get("feature_tags", []))
            devices = ",".join(p.get("seen_devices", []))
            suites = ",".join(p.get("suites_seen", []))
            print(f"    [OK]  {cmd}")
            print(f"            passes={p.get('pass_count', '?')}  "
                  f"devices=[{devices}]  suites=[{suites}]  tags=[{tags}]")
    if invalid:
        print()
        print("  Known invalid:")
        for cmd, p in sorted(invalid.items()):
            alts = ", ".join(p.get("alternatives", []))
            print(f"    [BAD] {cmd}")
            print(f"            alts: {alts}")
    if menus:
        print()
        print("  Completion menus:")
        for prefix, p in sorted(menus.items()):
            kw = p.get("keywords", []) if isinstance(p, dict) else p
            print(f"    [?]  {prefix!r}  -> {len(kw)} keywords")
    return 0


def show_feature(shared_root: Path, feature: str) -> int:
    f = shared_root / "by_feature" / f"{feature}.json"
    if not f.exists():
        print(f"no such feature index: {feature}", file=sys.stderr)
        return 2
    data = _load(f)
    cmds = data.get("commands", {})
    print(f"== feature: {feature} == ({f})")
    print(f"  commands: {len(cmds)}")
    print()
    for cmd, p in sorted(cmds.items()):
        marker = "[OK]" if p.get("valid") else "[BAD]"
        proto = p.get("protocol", "?")
        print(f"  {marker}  ({proto}) {cmd}")
    return 0


def show_tree(shared_root: Path) -> int:
    proto_root = shared_root / "by_protocol"
    if not proto_root.exists():
        print("no by_protocol dir", file=sys.stderr)
        return 2
    print(f"shared root: {shared_root}")
    print()
    for d in sorted(proto_root.iterdir()):
        if not d.is_dir():
            continue
        v = _load(d / "validated_commands.json")
        i = _load(d / "known_invalid.json")
        m = _load(d / "completion_menus.json")
        if not (v or i or m):
            continue
        print(f"  {d.name:14s}  validated={len(v):3d}  invalid={len(i):2d}  menus={len(m):2d}")
    print()
    feat_root = shared_root / "by_feature"
    if feat_root.exists():
        print("feature index:")
        for f in sorted(feat_root.glob("*.json")):
            data = _load(f)
            print(f"  {f.stem:30s}  commands={len(data.get('commands', {}))}")
    return 0


def show_provenance(shared_root: Path) -> int:
    """Aggregate which suites contributed which commands."""
    proto_root = shared_root / "by_protocol"
    if not proto_root.exists():
        print("no by_protocol dir", file=sys.stderr)
        return 2
    by_suite: dict[str, list[str]] = defaultdict(list)
    for d in sorted(proto_root.iterdir()):
        if not d.is_dir():
            continue
        v = _load(d / "validated_commands.json")
        for cmd, payload in v.items():
            for s in payload.get("suites_seen", []):
                by_suite[s].append(f"({d.name}) {cmd}")
    print("contribution map:")
    for suite, items in sorted(by_suite.items()):
        print(f"  {suite}  ({len(items)} contributions)")
        for it in sorted(items)[:10]:
            print(f"    - {it}")
        if len(items) > 10:
            print(f"    ... +{len(items) - 10} more")
    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Browse shared /TEST knowledge.")
    p.add_argument("--shared-root", default=None)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--tree", action="store_true",
                   help="Top-level tree (counts per protocol + feature).")
    g.add_argument("--protocol", default=None,
                   help="List everything in one protocol bucket.")
    g.add_argument("--feature", default=None,
                   help="List every command tagged with FEATURE.")
    g.add_argument("--provenance", action="store_true",
                   help="Show which suites contributed which commands.")
    g.add_argument("--stats", action="store_true",
                   help="Numeric snapshot.")
    args = p.parse_args(argv)

    if args.shared_root:
        shared_root = Path(args.shared_root).expanduser()
    else:
        # Honor the same env var that lib.cache_store reads, so
        # ``DNOS_TEST_SHARED_ROOT=/home/dn/SCALER/TEST/_shared/knowledge``
        # (or a future runtime override) flows through here. Falls back
        # to the worktree's local copy only if neither env var nor the
        # canonical ``~/SCALER/TEST/_shared/knowledge`` exists.
        env_root = os.environ.get("DNOS_TEST_SHARED_ROOT")
        canonical = Path.home() / "SCALER" / "TEST" / "_shared" / "knowledge"
        if env_root:
            shared_root = Path(env_root).expanduser()
        elif canonical.exists():
            shared_root = canonical
        else:
            shared_root = _HERE.parents[1] / "knowledge"

    if args.tree:
        return show_tree(shared_root)
    if args.protocol:
        return show_protocol(shared_root, args.protocol)
    if args.feature:
        return show_feature(shared_root, args.feature)
    if args.provenance:
        return show_provenance(shared_root)
    if args.stats:
        store = CacheStore(shared_root=shared_root, suite_id="browse_tool")
        print(json.dumps(store.snapshot_stats(), indent=2))
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
