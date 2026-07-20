#!/usr/bin/env python3
"""Per-story requirement-depth auditor for /TP.

Root-cause guard for "a user story hides many tests": our coverage is credited
at story-KEY granularity (US-<key> is 'covered' if ANY TC references it), which
masks multiple discrete requirements inside a rich story body. This tool
decomposes each user-story body into discrete requirements and cross-checks how
many TCs actually reference the story, flagging:

  - THIN   : a behavior/CLI story with >=THIN_REQS discrete requirements but
             < ceil(reqs/REQ_PER_TC) covering TCs  (likely hidden tests)
  - ZERO   : a behavior/CLI story with requirements but 0 covering TCs
  - WAIVED : implementation-only stories (zebra/libigmp/proto3/Part X/BGP-plumbing)
             -> not QA-E2E; reported as waived, not a gap

Inputs (per epic dir):
  - user_story_bodies.md   (## <KEY> [status] summary  +  body)
  - full_result.json       (test_cases[].covers_user_stories[])

Usage:
  python3 _tp_story_requirement_audit.py --epic SW-211037
  python3 _tp_story_requirement_audit.py --epic SW-211037 --strict   # nonzero on ZERO gaps

Exit 0 = no ZERO-coverage behavior gaps (or no story-bodies file -> INFO skip).
Exit 1 = at least one behavior story with extractable requirements and 0 TCs (strict).
"""
from __future__ import annotations

from _tp_paths import default_data_dir
import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

THIN_REQS = 3      # a story with >= this many requirement signals is "rich"
REQ_PER_TC = 3     # expect ~1 TC per this many discrete requirements

# Implementation-only stories are plumbing, not QA-E2E behavior; auto-waived.
_IMPL_RE = re.compile(
    r"\bzebra\b|\blibigmp\b|proto3|IsInitialized|Part\s+[A-Z0-9]|"
    r"\[LIBIGMP\]|\[zebra\]|outbound to FIBMGR|inbound path|C\+\+ counters|"
    r"EvpnEthTagSet|uninstalls in|EvpnBgpProxy|Import/Export and Installation",
    re.I,
)

_REQ_SIGNALS = [
    re.compile(r"cmd syntax|command syntax", re.I),
    re.compile(r"\b(must|shall|required|mandatory)\b", re.I),
    re.compile(r"mutually exclusive|commit validation|rejected|not allowed", re.I),
    re.compile(r"support the following", re.I),
]
_ENUM_LINE = re.compile(r"(?m)^\s*(?:[\*\-]\s+\S|\d+[\.\)]\s+\S)")


def _parse_story_bodies(text: str) -> dict[str, dict]:
    """Return {key: {status, summary, body}} parsed from user_story_bodies.md."""
    out: dict[str, dict] = {}
    cur = None
    buf: list[str] = []
    hdr = re.compile(r"^##\s+(SW-\d+)\s*(?:\[([^\]]*)\])?\s*(.*)$")
    for line in text.splitlines():
        m = hdr.match(line)
        if m:
            if cur:
                out[cur]["body"] = "\n".join(buf).strip()
            cur = m.group(1)
            out[cur] = {"status": (m.group(2) or "").strip(), "summary": (m.group(3) or "").strip(), "body": ""}
            buf = []
        elif cur:
            buf.append(line)
    if cur:
        out[cur]["body"] = "\n".join(buf).strip()
    return out


def _requirement_count(body: str) -> int:
    if not body:
        return 0
    n = 0
    for rx in _REQ_SIGNALS:
        n += len(rx.findall(body))
    n += len(_ENUM_LINE.findall(body)) // 2
    return n


def _audit_stories(tp_dir: Path, epic: str) -> tuple[list, list, list, list, dict, int]:
    """Return (thin, zero, waived, ok, stories, story_count)."""
    bodies_path = tp_dir / "user_story_bodies.md"
    fr_path = tp_dir / "full_result.json"
    if not bodies_path.exists():
        return [], [], [], [], {}, 0
    if not fr_path.exists():
        raise FileNotFoundError(f"Missing full_result.json: {fr_path}")

    stories = _parse_story_bodies(bodies_path.read_text(encoding="utf-8"))
    fr = json.loads(fr_path.read_text(encoding="utf-8"))
    cov = Counter()
    for tc in fr.get("test_cases", []):
        for s in tc.get("covers_user_stories") or []:
            cov[str(s)] += 1

    thin, zero, waived, ok = [], [], [], []
    for key, meta in stories.items():
        body = meta["body"]
        reqs = _requirement_count(body)
        ntc = cov.get(key, 0)
        if _IMPL_RE.search(meta["summary"] + " " + body[:200]):
            waived.append((key, reqs, ntc))
            continue
        if reqs < THIN_REQS:
            continue
        expected = max(1, math.ceil(reqs / REQ_PER_TC))
        if ntc == 0:
            zero.append((key, reqs, ntc, meta["summary"]))
        elif ntc < expected:
            thin.append((key, reqs, ntc, expected, meta["summary"]))
        else:
            ok.append(key)
    return thin, zero, waived, ok, stories, len(stories)


def collect_findings(tp_dir: Path, epic: str) -> list[dict]:
    thin, zero, _waived, _ok, _stories, n_stories = _audit_stories(tp_dir, epic)
    if n_stories == 0:
        return []
    out: list[dict] = []
    for k, r, _n, s in sorted(zero, key=lambda x: -x[1]):
        out.append({
            "kind": "story-deepener",
            "target_id": k,
            "what_missing": f"rich behavior story with {r} req-signals and ZERO covering TCs",
            "source_ref": f"user_story_bodies.md; summary={s[:80]}",
            "suggested_action": "Author per-requirement TC(s) + covers_user_stories + agent scenarios",
            "severity": "error",
        })
    for k, r, n, e, s in sorted(thin, key=lambda x: -(x[1] - x[2])):
        out.append({
            "kind": "story-deepener",
            "target_id": k,
            "what_missing": f"thin coverage: {r} req-signals, {n} TCs (expected ~{e})",
            "source_ref": f"user_story_bodies.md; summary={s[:80]}",
            "suggested_action": "Decompose story body into additional TCs (SW-259157/259496 pattern)",
            "severity": "warn",
        })
    return out


def run_audit(tp_dir: Path, epic: str, *, strict: bool = False) -> int:
    bodies_path = tp_dir / "user_story_bodies.md"
    fr_path = tp_dir / "full_result.json"
    if not bodies_path.exists():
        print(f"[INFO] No user_story_bodies.md for {epic}; story-requirement audit skipped")
        return 0
    if not fr_path.exists():
        print(f"[FAIL] Missing full_result.json: {fr_path}")
        return 2

    try:
        thin, zero, waived, ok, stories, _ = _audit_stories(tp_dir, epic)
    except FileNotFoundError as exc:
        print(f"[FAIL] {exc}")
        return 2

    print(f"\nStory-requirement depth audit -- {epic}")
    print("=" * 70)
    print(f"stories={len(stories)}  rich_ok={len(ok)}  thin={len(thin)}  "
          f"zero={len(zero)}  impl_waived={len(waived)}")
    if zero:
        print("\n[GAP] rich behavior/CLI stories with ZERO covering TCs (review!):")
        for k, r, n, s in sorted(zero, key=lambda x: -x[1]):
            print(f"  - {k}: {r} req-signals, 0 TCs | {s[:60]}")
    if thin:
        print("\n[WARN] rich stories thinly covered (reqs >> TCs; hidden tests likely):")
        for k, r, n, e, s in sorted(thin, key=lambda x: -(x[1]-x[2])):
            print(f"  - {k}: {r} req-signals, {n} TCs (expected ~{e}) | {s[:55]}")
    print("=" * 70)

    if strict and zero:
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Per-story requirement-depth audit")
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    tp_dir = Path(args.dir).expanduser() / args.epic
    return run_audit(tp_dir, args.epic, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
