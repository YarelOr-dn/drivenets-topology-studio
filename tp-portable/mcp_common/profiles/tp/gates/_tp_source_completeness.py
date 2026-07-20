#!/usr/bin/env python3
"""Source-completeness gate for /TP (refines "we only gate what Stage 1
ingests"). Scans the ingested text (epic_documentation + user_story_bodies) for
REFERENCED sources - linked epics (SW-\\d+) and Confluence page ids - and flags
any that are referenced but NOT recorded as ingested in sources_ingested.json.

sources_ingested.json (written by Stage 1) shape:
  {"epic": "SW-211037",
   "ingested_epics": ["SW-211037", ...],
   "ingested_confluence": ["6236536930", ...],
   "comments_scanned": true,
   "notes": "..."}

Usage:
    python3 _tp_source_completeness.py --epic SW-211037
    python3 _tp_source_completeness.py --epic SW-211037 --strict

Exit 0 = no un-ingested referenced source (or no sources_ingested.json -> INFO).
Exit 1 = (strict) referenced-but-not-ingested source found.
"""
from __future__ import annotations

from _tp_paths import default_data_dir
import argparse
import json
import re
import sys
from pathlib import Path

_SW = re.compile(r"\bSW-\d{4,6}\b")
_CONF = re.compile(r"/wiki/spaces/[^/]+/pages/(\d{6,})|confluence[:/](\d{6,})|pages/(\d{6,})")


def _read(*paths: Path) -> str:
    out = []
    for p in paths:
        if p.exists():
            out.append(p.read_text(encoding="utf-8"))
    return "\n".join(out)


def _source_gaps(tp_dir: Path, epic: str) -> tuple[bool, list[str], list[str], bool]:
    """Return (has_ingested_file, missing_epics, missing_conf, comments_scanned)."""
    ing_path = tp_dir / "sources_ingested.json"
    if not ing_path.exists():
        return False, [], [], False

    ing = json.loads(ing_path.read_text(encoding="utf-8"))
    ing_epics = {str(x) for x in ing.get("ingested_epics", [])}
    ing_conf = {str(x) for x in ing.get("ingested_confluence", [])}
    comments_scanned = bool(ing.get("comments_scanned"))

    text = _read(
        tp_dir / f"epic_documentation_{epic}.md",
        tp_dir / "user_story_bodies.md",
    )
    referenced_epics = {m for m in _SW.findall(text)} - {epic}
    referenced_conf = set()
    for a, b, c in _CONF.findall(text):
        referenced_conf.add(a or b or c)

    missing_epics = sorted(e for e in referenced_epics if e not in ing_epics)
    missing_conf = sorted(c for c in referenced_conf if c not in ing_conf)
    return True, missing_epics, missing_conf, comments_scanned


def _enabler_gaps(tp_dir: Path, epic: str) -> tuple[bool, list[str], list[str]]:
    """Return (has_sweep_file, enablers_not_ingested, enablers_without_children).

    Enforces the always-on enabler auto-discovery: enabler_sweep.json must exist,
    every discovered enabler epic must be recorded in sources_ingested.json's
    ingested_epics, and each enabler must have at least one mined child."""
    sweep_path = tp_dir / "enabler_sweep.json"
    if not sweep_path.exists():
        return False, [], []
    try:
        sweep = json.loads(sweep_path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return False, [], []
    enablers = sweep.get("enablers", sweep) if isinstance(sweep, dict) else sweep
    if isinstance(enablers, dict):
        enablers = list(enablers.values())

    ing_path = tp_dir / "sources_ingested.json"
    ing_epics: set[str] = set()
    if ing_path.exists():
        try:
            ing_epics = {str(x) for x in json.loads(
                ing_path.read_text(encoding="utf-8")).get("ingested_epics", [])}
        except (ValueError, OSError):
            ing_epics = set()

    not_ingested: list[str] = []
    no_children: list[str] = []
    for en in enablers if isinstance(enablers, list) else []:
        if not isinstance(en, dict):
            continue
        key = str(en.get("key", "")).strip()
        if not key:
            continue
        if ing_epics and key not in ing_epics:
            not_ingested.append(key)
        children = en.get("child_keys") or []
        if not children and int(en.get("child_count", 0) or 0) == 0:
            no_children.append(key)
    return True, sorted(not_ingested), sorted(no_children)


def collect_findings(tp_dir: Path, epic: str) -> list[dict]:
    has_file, missing_epics, missing_conf, comments_scanned = _source_gaps(tp_dir, epic)
    out: list[dict] = []
    has_sweep, en_not_ingested, en_no_children = _enabler_gaps(tp_dir, epic)
    if not has_sweep:
        out.append({
            "kind": "source-syntax",
            "target_id": epic,
            "what_missing": "enabler_sweep.json (Stage-1 enabler auto-discovery log)",
            "source_ref": "_tp_source_completeness",
            "suggested_action": "Run always-on enabler auto-discovery (Step 1 item 3a): "
                                "classify linked 'Enabler' epics, recurse into their children, "
                                "and write enabler_sweep.json (empty enablers[] if none exist)",
            "severity": "warn",
        })
    for e in en_not_ingested:
        out.append({
            "kind": "source-syntax",
            "target_id": e,
            "what_missing": "discovered enabler epic not recorded as ingested",
            "source_ref": "enabler_sweep.json",
            "suggested_action": f"Fetch enabler {e} + its children and add {e} to ingested_epics",
            "severity": "error",
        })
    for e in en_no_children:
        out.append({
            "kind": "source-syntax",
            "target_id": e,
            "what_missing": "enabler epic has no mined child stories",
            "source_ref": "enabler_sweep.json",
            "suggested_action": f"Fetch children of {e} via 'parent in ({e})' and mine their bodies",
            "severity": "warn",
        })
    if not has_file:
        out.append({
            "kind": "source-syntax",
            "target_id": epic,
            "what_missing": "sources_ingested.json (Stage-1 fetch log)",
            "source_ref": "_tp_source_completeness",
            "suggested_action": "Produce sources_ingested.json with ingested_epics, ingested_confluence, comments_scanned",
            "severity": "error",
        })
        return out
    if not comments_scanned:
        out.append({
            "kind": "source-syntax",
            "target_id": epic,
            "what_missing": "comments_scanned=false in sources_ingested.json",
            "source_ref": "sources_ingested.json",
            "suggested_action": "Re-fetch Jira comments and set comments_scanned=true",
            "severity": "warn",
        })
    for e in missing_epics:
        out.append({
            "kind": "source-syntax",
            "target_id": e,
            "what_missing": "referenced epic not recorded as ingested",
            "source_ref": "epic_documentation / user_story_bodies",
            "suggested_action": f"Add {e} to ingested_epics after Stage-1 fetch",
            "severity": "error",
        })
    for c in missing_conf:
        out.append({
            "kind": "source-syntax",
            "target_id": c,
            "what_missing": "referenced Confluence page not recorded as ingested",
            "source_ref": "epic_documentation / user_story_bodies",
            "suggested_action": f"Add {c} to ingested_confluence after fetch",
            "severity": "error",
        })
    return out


def run_gate(tp_dir: Path, epic: str, *, strict: bool = False) -> int:
    ing_path = tp_dir / "sources_ingested.json"
    if not ing_path.exists():
        print(f"[INFO] No sources_ingested.json for {epic}; source-completeness gate skipped "
              f"(Stage 1 should write it: ingested_epics / ingested_confluence / comments_scanned)")
        return 0

    has_file, missing_epics, missing_conf, comments_scanned = _source_gaps(tp_dir, epic)
    ing = json.loads(ing_path.read_text(encoding="utf-8"))
    ing_epics = {str(x) for x in ing.get("ingested_epics", [])}
    ing_conf = {str(x) for x in ing.get("ingested_confluence", [])}
    text = _read(
        tp_dir / f"epic_documentation_{epic}.md",
        tp_dir / "user_story_bodies.md",
    )
    referenced_epics = {m for m in _SW.findall(text)} - {epic}
    referenced_conf = set()
    for a, b, c in _CONF.findall(text):
        referenced_conf.add(a or b or c)

    print(f"\nSource-completeness gate -- {epic}")
    print("=" * 70)
    print(f"ingested_epics={len(ing_epics)}  ingested_confluence={len(ing_conf)}  "
          f"comments_scanned={comments_scanned}")
    print(f"referenced_epics={len(referenced_epics)}  referenced_confluence={len(referenced_conf)}")
    has_sweep, en_not_ingested, en_no_children = _enabler_gaps(tp_dir, epic)
    fail = False
    if not has_sweep:
        print("[WARN] enabler_sweep.json MISSING - always-on enabler auto-discovery "
              "(Step 1 item 3a) not proven; write it (empty enablers[] if the epic has none)")
    else:
        print(f"enabler_sweep present; enablers_not_ingested={len(en_not_ingested)}  "
              f"enablers_without_children={len(en_no_children)}")
        if en_not_ingested:
            print(f"[REVIEW] enabler epics NOT recorded as ingested ({len(en_not_ingested)}):")
            for e in en_not_ingested[:30]:
                print(f"  - {e}")
            fail = True
        if en_no_children:
            print(f"[WARN] enabler epics with no mined children ({len(en_no_children)}):")
            for e in en_no_children[:30]:
                print(f"  - {e}")
    if not comments_scanned:
        print("[WARN] comments_scanned=false - Jira comments not confirmed ingested")
    if missing_epics:
        print(f"[REVIEW] referenced epics NOT recorded as ingested ({len(missing_epics)}):")
        for e in missing_epics[:30]:
            print(f"  - {e}")
        fail = True
    if missing_conf:
        print(f"[REVIEW] referenced Confluence pages NOT recorded as ingested ({len(missing_conf)}):")
        for c in missing_conf[:30]:
            print(f"  - {c}")
        fail = True
    if not fail:
        print("[PASS] all referenced epics/pages are recorded as ingested")
    print("=" * 70)
    if strict and fail:
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="TP source-completeness gate")
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    tp_dir = Path(args.dir).expanduser() / args.epic
    return run_gate(tp_dir, args.epic, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
