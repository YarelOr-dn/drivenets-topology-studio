#!/usr/bin/env python3
"""Migrate existing topology files from ~/.topology_sections into the multi-user database.

Each section becomes a domain in the target user's DB.
Each .json file in a section becomes a topology entry.

Usage:
    python3 migrate.py                   # migrate into admin user
    python3 migrate.py --user yarel      # migrate into specific user
    python3 migrate.py --dry-run         # show what would be migrated
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.auth.user_store import UserStore

SECTIONS_DIR = Path.home() / ".topology_sections"
SECTIONS_INDEX = SECTIONS_DIR / "_sections.json"


def migrate(target_user: str = "admin", dry_run: bool = False):
    if not SECTIONS_DIR.exists():
        print(f"[INFO] No sections directory at {SECTIONS_DIR} -- nothing to migrate")
        return

    store = UserStore()

    user = store.get_user(target_user)
    if not user:
        print(f"[ERROR] User '{target_user}' not found in database. Run seed_users.py first.")
        return

    sections = []
    if SECTIONS_INDEX.exists():
        try:
            sections = json.loads(SECTIONS_INDEX.read_text())
        except json.JSONDecodeError as e:
            print(f"[WARN] Failed to parse {SECTIONS_INDEX}: {e}")

    section_map = {s["id"]: s for s in sections if "id" in s}

    migrated_domains = 0
    migrated_topos = 0
    skipped = 0

    section_dirs = sorted(SECTIONS_DIR.iterdir())
    for section_dir in section_dirs:
        if not section_dir.is_dir():
            continue

        sec_id = section_dir.name
        sec_info = section_map.get(sec_id, {})
        sec_name = sec_info.get("name", sec_id)

        topo_files = sorted(section_dir.glob("*.json"))
        if not topo_files:
            continue

        print(f"\n[SECTION] {sec_name} ({sec_id}) -- {len(topo_files)} topologies")

        if dry_run:
            for tf in topo_files:
                print(f"  [DRY-RUN] Would import: {tf.name}")
                migrated_topos += 1
            migrated_domains += 1
            continue

        existing_domains = store.list_domains(target_user)
        existing_names = {d["name"] for d in existing_domains}

        if sec_name in existing_names:
            domain = next(d for d in existing_domains if d["name"] == sec_name)
            domain_id = domain["id"]
            print(f"  [REUSE] Domain '{sec_name}' already exists (id={domain_id})")
        else:
            domain = store.create_domain(target_user, sec_name, f"Migrated from {sec_id}")
            domain_id = domain["id"]
            migrated_domains += 1
            print(f"  [OK] Created domain '{sec_name}' (id={domain_id})")

        existing_topos = store.list_topologies(target_user, domain_id)
        existing_topo_names = {t["name"] for t in existing_topos}

        for tf in topo_files:
            topo_name = tf.stem
            if topo_name in existing_topo_names:
                skipped += 1
                print(f"  [SKIP] '{topo_name}' already exists in domain")
                continue

            try:
                data = json.loads(tf.read_text())
            except (json.JSONDecodeError, OSError) as e:
                print(f"  [ERROR] Failed to read {tf.name}: {e}")
                continue

            store.save_topology(target_user, domain_id, topo_name, data)
            migrated_topos += 1
            obj_count = len(data.get("objects", []))
            print(f"  [OK] Imported '{topo_name}' ({obj_count} objects)")

    print(f"\n[DONE] Domains created: {migrated_domains}, "
          f"Topologies imported: {migrated_topos}, Skipped: {skipped}")


def main():
    parser = argparse.ArgumentParser(description="Migrate topology sections to multi-user DB")
    parser.add_argument("--user", default="admin", help="Target username (default: admin)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated")
    args = parser.parse_args()
    migrate(target_user=args.user, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
