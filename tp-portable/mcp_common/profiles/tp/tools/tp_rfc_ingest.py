#!/usr/bin/env python3
"""Fetch RFC normative clauses and merge into TP must_requirements.json.

Read-only fetch from rfc-editor.org. Does not mutate devices.

Usage:
    python3 tp_rfc_ingest.py --epic SW-228552 --rfc 7606
    python3 tp_rfc_ingest.py --epic SW-228552 --rfc 7606 --epic-scope-text "RFC7606 malformed NLRI handling only"
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import urllib.request
from pathlib import Path


NORMATIVE_RE = re.compile(
    r"(?im)^\s*(?:\d+\.)*\d*\s*.+\b(MUST|SHALL|SHOULD|MUST NOT|SHALL NOT|SHOULD NOT)\b.+$"
)


def atomic_write_json(path: Path, data: object) -> None:
    try:
        mode = os.stat(path).st_mode & 0o777
    except FileNotFoundError:
        mode = 0o644
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, sort_keys=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def fetch_rfc_text(rfc_num: int) -> str:
    url = f"https://www.rfc-editor.org/rfc/rfc{rfc_num}.txt"
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_clauses(text: str, rfc_num: int) -> list[dict]:
    clauses: list[dict] = []
    for i, line in enumerate(text.splitlines()):
        if not NORMATIVE_RE.match(line):
            continue
        clause_id = f"RFC{rfc_num}-L{i+1}"
        clauses.append(
            {
                "id": clause_id,
                "text": line.strip(),
                "rfc": rfc_num,
                "line": i + 1,
                "source": f"rfc:{rfc_num}",
                "normative": True,
            }
        )
    return clauses


def epic_scope_delta(clauses: list[dict], epic_scope: str | None) -> dict:
    if not epic_scope:
        return {
            "epic_claimed_scope": None,
            "full_rfc_clause_count": len(clauses),
            "in_scope_count": len(clauses),
            "note": "No epic scope text provided; all normative clauses treated in-scope",
        }
    scope_lower = epic_scope.lower()
    in_scope = [c for c in clauses if any(w in c["text"].lower() for w in scope_lower.split() if len(w) > 4)]
    return {
        "epic_claimed_scope": epic_scope,
        "full_rfc_clause_count": len(clauses),
        "in_scope_count": len(in_scope),
        "out_of_scope_count": len(clauses) - len(in_scope),
        "whole_rfc_implied": "whole rfc" in scope_lower or "entire rfc" in scope_lower,
    }


def merge_musts(tp_dir: Path, clauses: list[dict], delta: dict) -> Path:
    must_path = tp_dir / "must_requirements.json"
    if must_path.exists():
        doc = json.loads(must_path.read_text())
    else:
        doc = {"must_requirements": [], "rfc_deltas": []}

    existing_ids = {m.get("id") for m in doc.get("must_requirements", [])}
    for c in clauses:
        if c["id"] not in existing_ids:
            doc.setdefault("must_requirements", []).append(c)
    doc.setdefault("rfc_deltas", []).append(delta)
    atomic_write_json(must_path, doc)
    return must_path


def main() -> int:
    ap = argparse.ArgumentParser(description="RFC clause ingest for /TP")
    ap.add_argument("--epic", required=True)
    ap.add_argument("--rfc", type=int, required=True)
    ap.add_argument("--tp-dir", default=str(Path.home() / "SCALER/TEST/tp"))
    ap.add_argument("--epic-scope-text", default="")
    args = ap.parse_args()

    tp_dir = Path(args.tp_dir) / args.epic
    tp_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Fetching RFC {args.rfc}...")
    text = fetch_rfc_text(args.rfc)
    clauses = extract_clauses(text, args.rfc)
    delta = epic_scope_delta(clauses, args.epic_scope_text or None)

    rfc_path = tp_dir / f"rfc_{args.rfc}_clauses.json"
    atomic_write_json(rfc_path, {"rfc": args.rfc, "clauses": clauses, "delta": delta})
    must_path = merge_musts(tp_dir, clauses, delta)

    print(f"[OK] RFC {args.rfc}: {len(clauses)} normative clauses")
    print(f"[OK] Epic-vs-RFC delta: {json.dumps(delta)}")
    print(f"[OK] Wrote {rfc_path}")
    print(f"[OK] Updated {must_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
