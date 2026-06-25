#!/usr/bin/env python3
"""Mirror MCP-created topologies into legacy section files for current UI visibility."""

from __future__ import annotations

import argparse
import sys
from typing import Any, Dict

from api.auth.user_store import user_store
from mcp.access import _mirror_owned_topology_to_sections


def _matches(name: str, needle: str) -> bool:
    return needle.lower() in (name or "").lower()


def repair(name_contains: str, username: str = "") -> int:
    users = [user_store.get_user(username)] if username else user_store.list_users()
    repaired = 0
    for user in users:
        if not user:
            continue
        owner = user["username"]
        for domain in user_store.list_domains(owner):
            if domain.get("is_shared") or domain.get("is_shared_with_me_domain"):
                continue
            domain_id = domain.get("id") or ""
            for topo in user_store.list_topologies(owner, domain_id):
                topo_name = topo.get("name") or ""
                if not _matches(topo_name, name_contains):
                    continue
                loaded = user_store.load_topology(owner, domain_id, topo.get("id") or "")
                if not loaded:
                    continue
                data: Dict[str, Any] = dict(loaded.get("data") or {})
                result = {
                    "id": loaded.get("id"),
                    "__real_topology_id": loaded.get("id"),
                    "name": loaded.get("name") or topo_name,
                }
                _mirror_owned_topology_to_sections(owner, domain_id, result, data)
                repaired += 1
                print(
                    f"[OK] {owner}/{domain.get('name')} -> {loaded.get('name')} "
                    f"({result.get('legacy_section_id')}/{result.get('legacy_filename')})"
                )
    if repaired == 0:
        print(f"[WARN] no topologies matched {name_contains!r}", file=sys.stderr)
        return 1
    print(f"[OK] repaired {repaired} topology visibility mirror(s)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("name_contains")
    parser.add_argument("--user", default="")
    args = parser.parse_args()
    return repair(args.name_contains, args.user)


if __name__ == "__main__":
    raise SystemExit(main())
