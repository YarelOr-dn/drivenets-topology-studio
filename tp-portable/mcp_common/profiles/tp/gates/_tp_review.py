#!/usr/bin/env python3
"""/TP REVIEW - render a TC exactly as it will look in Jira.

Single source of truth is the per-TC `jira_wiki_body` already stored in
`manifest.json` (produced by the generator's `jira_wiki_body()`), so REVIEW
never re-authors content - it only re-presents it:

  --format jira  : the raw Jira wiki markup (what `--push` uploads, byte-for-byte)
  --format chat  : the same body converted to GitHub-flavored markdown so it
                   renders in the chat/IDE preview visually like the Jira page
                   (headings, real tables, fenced code, inline code)

Usage:
  python3 _tp_review.py --epic SW-211037 --list
  python3 _tp_review.py --epic SW-211037 --tc TC-IGMP-SAN-basic-snoop-selective-forwarding-flood
  python3 _tp_review.py --epic SW-211037 --tc <id> --format jira
  python3 _tp_review.py --epic SW-211037 --category "Basic Functionality"   # all TCs in matching categories
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from _tp_paths import resolve_data_dir, default_data_dir


def _manifest_path(epic: str, data_dir: str | None = None) -> Path:
    return resolve_data_dir(data_dir) / epic / "manifest.json"


def _iter_tcs(manifest: dict):
    """Yield (category_name, tc_dict) for every TC in the manifest, whatever the
    nesting shape (categories -> [testing_tasks ->] test_cases)."""
    seen = set()

    def walk(node, cat):
        if isinstance(node, dict):
            if node.get("id", "").startswith("TC-") and "jira_wiki_body" in node:
                if id(node) not in seen:
                    seen.add(id(node))
                    label = node.get("category") or node.get("jira_category") or cat
                    yield label, node
                return
            cat2 = node.get("name") or node.get("category") or cat
            for v in node.values():
                yield from walk(v, cat2)
        elif isinstance(node, list):
            for v in node:
                yield from walk(v, cat)

    yield from walk(manifest, "")


def _load_tcs(epic: str, data_dir: str | None = None):
    mp = _manifest_path(epic, data_dir)
    if not mp.exists():
        sys.exit(f"[ERROR] manifest not found: {mp} (run /TP {epic} first)")
    manifest = json.loads(mp.read_text())
    return list(_iter_tcs(manifest))


# --------------------------------------------------------------------------- #
# Jira wiki -> GitHub-flavored markdown (for the chat/IDE preview)
# --------------------------------------------------------------------------- #
def _inline(s: str) -> str:
    """Convert inline Jira wiki markup to GFM."""
    s = re.sub(r"\{\{(.+?)\}\}", r"`\1`", s)            # {{cmd}} -> `cmd`
    s = re.sub(r"(?<!\w)\*([^*\n]+?)\*(?!\w)", r"**\1**", s)  # *bold* -> **bold**
    return s


def _split_wiki_row(line: str, sep: str) -> list[str]:
    inner = line.strip()
    if inner.startswith(sep):
        inner = inner[len(sep):]
    if inner.endswith(sep):
        inner = inner[: -len(sep)]
    return [c.strip() for c in inner.split(sep)]


def jira_to_gfm(body: str) -> str:
    out: list[str] = []
    in_noformat = False
    for line in body.splitlines():
        st = line.strip()
        if st == "{noformat}":
            out.append("```")
            in_noformat = not in_noformat
            continue
        if in_noformat:
            out.append(line)
            continue
        if st.startswith("{expand:title=") and st.endswith("}"):
            title = st[len("{expand:title="):-1]
            out.append("")
            out.append("<details><summary><b>" + _inline(title) + "</b></summary>")
            out.append("")
            continue
        if st == "{expand}":
            out.append("")
            out.append("</details>")
            out.append("")
            continue
        if st.startswith("h1. "):
            out.append("# " + _inline(st[4:]))
        elif st.startswith("h2. "):
            out.append("## " + _inline(st[4:]))
        elif st.startswith("h3. "):
            out.append("### " + _inline(st[4:]))
        elif st.startswith("||"):
            cells = [_inline(c) for c in _split_wiki_row(st, "||")]
            out.append("| " + " | ".join(cells) + " |")
            out.append("|" + "|".join(["---"] * len(cells)) + "|")
        elif st.startswith("|"):
            cells = [_inline(c) for c in _split_wiki_row(st, "|")]
            out.append("| " + " | ".join(cells) + " |")
        elif st.startswith("# "):
            out.append("1. " + _inline(st[2:]))
        elif st.startswith("* "):
            out.append("- " + _inline(st[2:]))
        else:
            out.append(_inline(line))
    return "\n".join(out)


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description="/TP REVIEW - render a TC as it looks in Jira")
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    ap.add_argument("--tc", help="TC id (exact or unique substring)")
    ap.add_argument("--category", help="render all TCs whose category name contains this")
    ap.add_argument("--format", choices=["chat", "jira"], default="chat",
                    help="chat = GFM preview (default); jira = raw wiki markup")
    ap.add_argument("--list", action="store_true", help="list TC ids + categories and exit")
    args = ap.parse_args()

    tcs = _load_tcs(args.epic, args.dir)
    if args.list:
        for cat, tc in tcs:
            print(f"{tc['id']}\t[{cat}]")
        print(f"\n[INFO] {len(tcs)} TCs in {args.epic}")
        return

    if args.category:
        sel = [(c, t) for c, t in tcs if args.category.lower() in (c or "").lower()]
    elif args.tc:
        exact = [(c, t) for c, t in tcs if t["id"] == args.tc]
        sel = exact or [(c, t) for c, t in tcs if args.tc.lower() in t["id"].lower()]
    else:
        sel = tcs[:1]  # default: first TC as a sample

    if not sel:
        sys.exit(f"[ERROR] no TC matched (--tc {args.tc!r} / --category {args.category!r})")

    for i, (_cat, tc) in enumerate(sel):
        body = tc.get("jira_wiki_body", "")
        rendered = body if args.format == "jira" else jira_to_gfm(body)
        if i:
            print("\n---\n")
        print(rendered)


if __name__ == "__main__":
    main()
