#!/usr/bin/env python3
"""Harvest **cmd syntax:** from user stories + CLI RSTs into cli_spec_inventory.json.

Caches RST index per cheetah branch SHA under ~/.cursor/tp_cache/.

Usage:
    python3 _tp_cli_spec_harvester.py --epic SW-211037

Exit 0 on success; exit 2 if epic dir missing.
"""
from __future__ import annotations

from _tp_paths import default_data_dir
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from _tp_syntax_common import (
    TP_CACHE_DIR,
    atomic_write_json,
    cmd_kind,
    normalize_cmd,
    parse_rst_syntax,
    parse_story_cmd_blocks,
)


def _load_epic_version(tp_dir: Path) -> dict:
    p = tp_dir / "epic_version.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def _rst_cache_path(branch: str, sha: str) -> Path:
    safe = re.sub(r"[^\w.-]", "_", f"{branch}_{sha}")
    return TP_CACHE_DIR / f"cli_spec_index_{safe}.json"


def _harvest_rst(rst_root: Path, branch: str, sha: str, *, force: bool = False) -> list[dict[str, Any]]:
    cache = _rst_cache_path(branch or "unknown", sha or "unknown")
    if not force and cache.is_file():
        try:
            cached = json.loads(cache.read_text(encoding="utf-8"))
            if cached.get("sha") == sha:
                return cached.get("entries") or []
        except (json.JSONDecodeError, OSError):
            pass

    entries: list[dict[str, Any]] = []
    if not rst_root.is_dir():
        return entries

    for rst in rst_root.rglob("*.rst"):
        try:
            text = rst.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(rst.relative_to(rst_root))
        for syntax in parse_rst_syntax(text, rel):
            entries.append({
                "cmd": syntax,
                "kind": cmd_kind(syntax),
                "source": f"SPEC_RST:{branch}:{rel}",
                "raw": syntax,
                "norm": normalize_cmd(syntax),
            })

    atomic_write_json(cache, {"branch": branch, "sha": sha, "entries": entries})
    return entries


def harvest_inventory(tp_dir: Path, epic: str, *, write: bool = True) -> dict[str, Any]:
    ver = _load_epic_version(tp_dir)
    bodies_path = tp_dir / "user_story_bodies.md"
    story_warn = None
    story_entries: list[dict[str, Any]] = []

    if bodies_path.is_file():
        text = bodies_path.read_text(encoding="utf-8")
        for row in parse_story_cmd_blocks(text):
            full = row["full"]
            story_entries.append({
                "cmd": full,
                "kind": cmd_kind(full),
                "source": f"SPEC_USER_STORY:{row['sw_key']}",
                "raw": row["raw"],
                "syntax_only": row["syntax"],
                "level": row["level"],
                "norm": normalize_cmd(full),
                "norm_syntax": normalize_cmd(row["syntax"]),
            })
    else:
        story_warn = "user_story_bodies.md missing; RST-only harvest"

    rst_entries: list[dict[str, Any]] = []
    rst_root = ver.get("rst_root")
    if rst_root:
        rst_entries = _harvest_rst(
            Path(rst_root),
            str(ver.get("cheetah_branch") or ver.get("fix_version") or ""),
            str(ver.get("cheetah_sha") or ""),
        )
    elif ver.get("blocker"):
        story_warn = (story_warn or "") + ("; " if story_warn else "") + "RST skipped (version BLOCKER)"

    inventory = story_entries + rst_entries
    out = {
        "epic": epic,
        "fix_version": ver.get("fix_version"),
        "story_count": len(story_entries),
        "rst_count": len(rst_entries),
        "total": len(inventory),
        "warn": story_warn,
        "blocker": ver.get("blocker"),
        "entries": inventory,
    }
    if write:
        atomic_write_json(tp_dir / "cli_spec_inventory.json", out)
    return out


def run_harvester(tp_dir: Path, epic: str) -> int:
    if not tp_dir.is_dir():
        print(f"[FAIL] Missing epic dir: {tp_dir}")
        return 2
    out = harvest_inventory(tp_dir, epic, write=True)
    print(f"[OK] cli_spec_inventory.json story={out['story_count']} rst={out['rst_count']} "
          f"total={out['total']}")
    if out.get("warn"):
        print(f"[WARN] {out['warn']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="/TP CLI spec harvester")
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    args = ap.parse_args()
    tp_dir = Path(args.dir).expanduser() / args.epic
    return run_harvester(tp_dir, args.epic)


if __name__ == "__main__":
    sys.exit(main())
