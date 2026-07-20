#!/usr/bin/env python3
"""/TP syntax-divergence store (anchor: tp:sa-syntax-sot-and-divergence-capture).

Records + renders per-epic CLI syntax divergences among the three sources for the
SAME command:
  SPEC_USER_STORY  -- the system-architect CLI user story (the spec / authority)
  SPEC_CODE        -- branch RST/VTY/autogen on the version-matched checkout
  LIVE             -- device / knowledge-cache (what the running build accepts)

Store: ~/SCALER/TEST/tp/<EPIC>/syntax_divergences.json (atomic write).
The `render` output is embedded into quality_audit.md under a
"Syntax divergences (verify on first build)" heading so a human sees it.

Subcommands:
  record  --epic SW-XXXXX --command-role <role> --story-value <v> --story-key SW-YYYYY
          [--sa-owner <name>] [--code-value <v>] [--branch <b>] [--commit <c>]
          [--live-value <v>] [--status <S>] [--first-build-action "<cmd(s)>"]
          [--blast-radius <n>] [--note <text>]
  list    --epic SW-XXXXX [--format json|text]
  render  --epic SW-XXXXX          # markdown block for quality_audit.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from _tp_paths import resolve_data_dir, default_data_dir


_VALID_STATUS = {
    "STORY_ONLY", "CODE_RENAMED", "LIVE_CONFIRMED_STORY",
    "LIVE_CONFIRMED_CODE", "UNRESOLVED",
}


def _store_path(epic: str) -> Path:
    return resolve_data_dir(data_dir) / epic / "syntax_divergences.json"


def _load(epic: str) -> dict:
    p = _store_path(epic)
    if not p.exists():
        return {"epic": epic, "records": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"epic": epic, "records": []}


def _atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".sd_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _dedup_key(rec: dict) -> tuple:
    return (str(rec.get("command_role", "")).lower(),
            str(rec.get("story_value", "")).lower(),
            str(rec.get("code_value", "")).lower())


def cmd_record(args) -> int:
    if args.status and args.status not in _VALID_STATUS:
        print(f"[ERROR] --status must be one of {sorted(_VALID_STATUS)}")
        return 2
    store = _load(args.epic)
    rec = {
        "command_role": args.command_role,
        "story_value": args.story_value,
        "story_key": args.story_key,
        "sa_owner": args.sa_owner or "UNKNOWN",
        "code_value": args.code_value or None,
        "branch": args.branch or None,
        "commit": args.commit or None,
        "live_value": args.live_value or "UNKNOWN",
        "status": args.status or ("CODE_RENAMED" if args.code_value else "STORY_ONLY"),
        "first_build_action": args.first_build_action or "",
        "blast_radius": int(args.blast_radius) if args.blast_radius else 0,
        "note": args.note or "",
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    recs = store.setdefault("records", [])
    key = _dedup_key(rec)
    recs[:] = [r for r in recs if _dedup_key(r) != key]  # upsert
    recs.append(rec)
    _atomic_write_json(_store_path(args.epic), store)
    print(f"[OK] recorded divergence for {args.epic}: {rec['command_role']} "
          f"(story={rec['story_value']!r} vs code={rec['code_value']!r}) status={rec['status']}")
    print(f"     store: {_store_path(args.epic)}  total records: {len(recs)}")
    return 0


def cmd_list(args) -> int:
    store = _load(args.epic)
    recs = store.get("records", [])
    if args.format == "json":
        print(json.dumps(store, indent=2, ensure_ascii=False))
        return 0
    if not recs:
        print(f"[INFO] no syntax divergences recorded for {args.epic}")
        return 0
    print(f"Syntax divergences for {args.epic}: {len(recs)}")
    for r in recs:
        print(f"- [{r.get('status')}] {r.get('command_role')}: "
              f"story={r.get('story_value')!r} ({r.get('story_key')}, {r.get('sa_owner')}) "
              f"vs code={r.get('code_value')!r} | live={r.get('live_value')} "
              f"| blast={r.get('blast_radius')} | first_build: {r.get('first_build_action')}")
    return 0


def render_block(epic: str) -> str:
    """Markdown block for quality_audit.md. Empty string if no records."""
    store = _load(epic)
    recs = store.get("records", [])
    if not recs:
        return ""
    lines = [
        "## Syntax divergences (verify on first build)",
        "",
        "_System-architect CLI user story is the syntax source of truth; these commands "
        "diverge across SPEC_USER_STORY / SPEC_CODE / LIVE. TP keeps the SA-story syntax "
        "(marked EXPECTED_LIVE_VALIDATE) until the first lab build resolves it._",
        "",
        "| Command role | SA story (spec) | Code (branch) | Live | Status | Blast | First-build action |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in recs:
        lines.append(
            f"| {r.get('command_role','-')} "
            f"| `{r.get('story_value','-')}` ({r.get('story_key','-')}, {r.get('sa_owner','-')}) "
            f"| `{r.get('code_value') or '-'}`{(' @'+r['branch']) if r.get('branch') else ''} "
            f"| {r.get('live_value','UNKNOWN')} "
            f"| {r.get('status','-')} "
            f"| {r.get('blast_radius',0)} "
            f"| {r.get('first_build_action','-')} |"
        )
    lines.append("")
    return "\n".join(lines)


def cmd_render(args) -> int:
    block = render_block(args.epic)
    if not block:
        print(f"[INFO] no syntax divergences recorded for {args.epic}")
        return 0
    print(block)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="/TP syntax-divergence store")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("record")
    r.add_argument("--epic", required=True)
    r.add_argument("--command-role", dest="command_role", required=True)
    r.add_argument("--story-value", dest="story_value", required=True)
    r.add_argument("--story-key", dest="story_key", required=True)
    r.add_argument("--sa-owner", dest="sa_owner")
    r.add_argument("--code-value", dest="code_value")
    r.add_argument("--branch")
    r.add_argument("--commit")
    r.add_argument("--live-value", dest="live_value")
    r.add_argument("--status")
    r.add_argument("--first-build-action", dest="first_build_action")
    r.add_argument("--blast-radius", dest="blast_radius")
    r.add_argument("--note")
    r.set_defaults(func=cmd_record)

    l = sub.add_parser("list")
    l.add_argument("--epic", required=True)
    l.add_argument("--format", choices=["json", "text"], default="text")
    l.set_defaults(func=cmd_list)

    rn = sub.add_parser("render")
    rn.add_argument("--epic", required=True)
    rn.set_defaults(func=cmd_render)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
