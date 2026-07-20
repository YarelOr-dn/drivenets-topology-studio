#!/usr/bin/env python3
"""Local TP knowledge database for the merged /TP pipeline.

The DB is a local source of truth for reusable TP inputs: source documents,
rubric rules, command catalog rows, flow patterns, generated TC objects,
dedup fingerprints, and coverage links. It intentionally uses only the Python
standard library so every Cursor agent can run it without setup.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


CURSOR_ROOT = Path.home() / ".cursor"
TP_REFERENCE = CURSOR_ROOT / "tp-reference"
DB_PATH = TP_REFERENCE / "db" / "tp_knowledge.sqlite"
EXPORT_DIR = TP_REFERENCE / "generated"


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;

CREATE TABLE IF NOT EXISTS source_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_key TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL,
    title TEXT NOT NULL,
    path_or_url TEXT,
    provenance_status TEXT NOT NULL,
    content_hash TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rubric_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_key TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    source_key TEXT NOT NULL,
    category TEXT,
    trigger_condition TEXT,
    rule_text TEXT NOT NULL,
    mandatory INTEGER NOT NULL DEFAULT 0,
    provenance_status TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS command_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command_key TEXT NOT NULL UNIQUE,
    command_text TEXT NOT NULL,
    command_type TEXT NOT NULL,
    feature TEXT,
    category TEXT,
    verification_status TEXT NOT NULL,
    source_key TEXT,
    notes TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS flow_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    feature TEXT,
    automation_type TEXT,
    setup_pattern TEXT,
    trigger_pattern TEXT,
    verification_pattern TEXT,
    provenance_status TEXT NOT NULL,
    source_key TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS test_case_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    primary_epic TEXT,
    linked_epics_json TEXT NOT NULL DEFAULT '[]',
    automation_type TEXT,
    test_object_json TEXT NOT NULL,
    dedup_fingerprint TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dedup_fingerprints (
    fingerprint TEXT PRIMARY KEY,
    normalized_summary TEXT NOT NULL,
    trigger_type TEXT,
    expected_behavior TEXT,
    verification_surface TEXT,
    test_keys_json TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS coverage_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_key TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_key TEXT NOT NULL,
    provenance_status TEXT NOT NULL,
    source_key TEXT,
    UNIQUE(test_key, target_type, target_key)
);
"""


PROVENANCE_LOCAL = "LOCAL_SKILL"
PROVENANCE_COSTAKE = "COSTAKE_RUBRIC"
PROVENANCE_TP = "TP_CHECKLIST"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def upsert_source(
    conn: sqlite3.Connection,
    *,
    source_key: str,
    source_type: str,
    title: str,
    path_or_url: str | None,
    provenance_status: str,
    content: str,
    metadata: dict | None = None,
) -> None:
    ts = now()
    conn.execute(
        """
        INSERT INTO source_documents
          (source_key, source_type, title, path_or_url, provenance_status,
           content_hash, metadata_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_key) DO UPDATE SET
          source_type=excluded.source_type,
          title=excluded.title,
          path_or_url=excluded.path_or_url,
          provenance_status=excluded.provenance_status,
          content_hash=excluded.content_hash,
          metadata_json=excluded.metadata_json,
          updated_at=excluded.updated_at
        """,
        (
            source_key,
            source_type,
            title,
            path_or_url,
            provenance_status,
            sha256_text(content),
            json.dumps(metadata or {}, sort_keys=True),
            ts,
            ts,
        ),
    )


def upsert_rule(
    conn: sqlite3.Connection,
    *,
    rule_key: str,
    title: str,
    source_key: str,
    category: str | None,
    trigger_condition: str | None,
    rule_text: str,
    mandatory: bool,
    provenance_status: str,
) -> None:
    conn.execute(
        """
        INSERT INTO rubric_rules
          (rule_key, title, source_key, category, trigger_condition, rule_text,
           mandatory, provenance_status, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(rule_key) DO UPDATE SET
          title=excluded.title,
          source_key=excluded.source_key,
          category=excluded.category,
          trigger_condition=excluded.trigger_condition,
          rule_text=excluded.rule_text,
          mandatory=excluded.mandatory,
          provenance_status=excluded.provenance_status,
          updated_at=excluded.updated_at
        """,
        (
            rule_key,
            title,
            source_key,
            category,
            trigger_condition,
            rule_text,
            1 if mandatory else 0,
            provenance_status,
            now(),
        ),
    )


def upsert_command(
    conn: sqlite3.Connection,
    *,
    command_text: str,
    command_type: str,
    feature: str | None,
    category: str | None,
    verification_status: str,
    source_key: str | None,
    notes: str | None = None,
) -> None:
    command_key = sha256_text("|".join([command_text, command_type, feature or "", category or ""]))[:24]
    conn.execute(
        """
        INSERT INTO command_catalog
          (command_key, command_text, command_type, feature, category,
           verification_status, source_key, notes, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(command_key) DO UPDATE SET
          command_text=excluded.command_text,
          command_type=excluded.command_type,
          feature=excluded.feature,
          category=excluded.category,
          verification_status=excluded.verification_status,
          source_key=excluded.source_key,
          notes=excluded.notes,
          updated_at=excluded.updated_at
        """,
        (
            command_key,
            command_text,
            command_type,
            feature,
            category,
            verification_status,
            source_key,
            notes,
            now(),
        ),
    )


def init_db(_: argparse.Namespace) -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
    print(f"[OK] initialized {DB_PATH}")


def iter_markdown_headings(text: str) -> Iterable[tuple[int, str]]:
    for line in text.splitlines():
        match = re.match(r"^(#{2,4})\s+(.+?)\s*$", line)
        if match:
            yield len(match.group(1)), match.group(2).strip()


def seed_costake_rules(conn: sqlite3.Connection) -> None:
    path = CURSOR_ROOT / "skills" / "generate-qa-test-plan" / "test-documentation" / "test_plan_requirements.md"
    if not path.exists():
        return
    content = read_text(path)
    source_key = "local:costake:test_plan_requirements"
    upsert_source(
        conn,
        source_key=source_key,
        source_type="local_skill_reference",
        title="Costake Test Plan Requirements",
        path_or_url=str(path),
        provenance_status=PROVENANCE_COSTAKE,
        content=content,
        metadata={"author": "Alexandru Costake"},
    )
    for index, (level, title) in enumerate(iter_markdown_headings(content), start=1):
        if level > 3:
            continue
        upsert_rule(
            conn,
            rule_key=f"costake:{index:03d}:{slug(title)}",
            title=title,
            source_key=source_key,
            category="Costake TP Requirements",
            trigger_condition=None,
            rule_text=title,
            mandatory="Always Required" in title or level == 2,
            provenance_status=PROVENANCE_COSTAKE,
        )


def seed_tp_checklist(conn: sqlite3.Connection) -> None:
    path = TP_REFERENCE / "tp_checklist.json"
    if not path.exists():
        return
    content = read_text(path)
    source_key = "local:tp_checklist"
    upsert_source(
        conn,
        source_key=source_key,
        source_type="local_tp_reference",
        title="TP Checklist Categories",
        path_or_url=str(path),
        provenance_status=PROVENANCE_TP,
        content=content,
    )
    data = json.loads(content)
    for name, value in data.items():
        if name.startswith("_"):
            continue
        desc = value.get("description", "") if isinstance(value, dict) else ""
        upsert_rule(
            conn,
            rule_key=f"tp_category:{slug(name)}",
            title=name,
            source_key=source_key,
            category="TP Checklist",
            trigger_condition=None,
            rule_text=desc or name,
            mandatory=True,
            provenance_status=PROVENANCE_TP,
        )


def seed_local_skill(conn: sqlite3.Connection, path: Path, feature: str) -> None:
    if not path.exists():
        return
    content = read_text(path)
    source_key = f"local_skill:{feature}:{path.stem}"
    upsert_source(
        conn,
        source_key=source_key,
        source_type="local_skill",
        title=f"{feature} {path.name}",
        path_or_url=str(path),
        provenance_status=PROVENANCE_LOCAL,
        content=content,
    )
    for command in extract_inline_commands(content):
        upsert_command(
            conn,
            command_text=command,
            command_type=classify_command(command),
            feature=feature,
            category="EVPN-SI IRB",
            verification_status=extract_status_near_command(content, command),
            source_key=source_key,
        )


def seed_core(_: argparse.Namespace) -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        seed_costake_rules(conn)
        seed_tp_checklist(conn)
        evpn_root = CURSOR_ROOT / "skills" / "evpn-si-irb-mobility"
        for path in [evpn_root / "SKILL.md", *sorted((evpn_root / "sections").glob("*.md"))]:
            seed_local_skill(conn, path, "evpn-si-irb-mobility")
    print("[OK] seeded core TP knowledge")


def extract_inline_commands(text: str) -> list[str]:
    commands: set[str] = set()
    for match in re.finditer(r"`([^`\n]*(?:show|sh|clear|xraycli|wbox-cli|ip monitor|arp)[^`\n]*)`", text, re.I):
        commands.add(match.group(1).strip())
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^(show|sh|clear|xraycli|wbox-cli|ip monitor|arp)\b", stripped, re.I):
            commands.add(stripped)
    return sorted(commands)


def extract_status_near_command(text: str, command: str) -> str:
    index = text.find(command)
    window = text[max(0, index - 300): index + len(command) + 300] if index >= 0 else ""
    for status in [
        "LIVE_VALIDATED",
        "CANONICAL",
        "CANONICAL-SW-194717",
        "CANONICAL-PARENT-SI",
        "EXPECTED-LIVE-VALIDATE",
        "INFERRED",
        "DEBUG-CHEATSHEET",
        "CHEATSHEET_DEBUG",
    ]:
        if status in window:
            return status.replace("-", "_")
    return "EXPECTED_LIVE_VALIDATE"


def classify_command(command: str) -> str:
    lower = command.lower()
    if lower.startswith(("show", "sh")):
        return "show"
    if lower.startswith("clear"):
        return "clear"
    if lower.startswith(("xraycli", "wbox-cli", "ip monitor", "arp")):
        return "debug"
    return "other"


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")[:80] or "item"


def ingest_sources(args: argparse.Namespace) -> None:
    tp_dir = Path(args.tp_dir).expanduser()
    if not tp_dir.exists():
        raise SystemExit(f"TP directory does not exist: {tp_dir}")
    with connect() as conn:
        conn.executescript(SCHEMA)
        for path in sorted(tp_dir.glob("*")):
            if path.suffix.lower() not in {".md", ".json"}:
                continue
            content = read_text(path)
            upsert_source(
                conn,
                source_key=f"tp_artifact:{tp_dir.name}:{path.name}",
                source_type="tp_artifact",
                title=path.name,
                path_or_url=str(path),
                provenance_status="LOCAL_GENERATED",
                content=content,
            )
    print(f"[OK] ingested TP artifacts from {tp_dir}")


def export(_: argparse.Namespace) -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        payload = {}
        for table in [
            "source_documents",
            "rubric_rules",
            "command_catalog",
            "flow_catalog",
            "test_case_catalog",
            "dedup_fingerprints",
            "coverage_links",
        ]:
            rows = [dict(row) for row in conn.execute(f"SELECT * FROM {table} ORDER BY 1")]
            payload[table] = rows
            (EXPORT_DIR / f"{table}.json").write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
        summary = build_summary(payload)
        (EXPORT_DIR / "summary.md").write_text(summary, encoding="utf-8")
    print(f"[OK] exported TP knowledge to {EXPORT_DIR}")


def build_summary(payload: dict[str, list[dict]]) -> str:
    lines = ["# TP Knowledge DB Export", ""]
    lines.append(f"Generated: {now()}")
    lines.append("")
    for table, rows in payload.items():
        lines.append(f"- `{table}`: {len(rows)} rows")
    lines.append("")
    lines.append("## Command Catalog Sample")
    for row in payload.get("command_catalog", [])[:30]:
        lines.append(f"- `{row['command_text']}` ({row['verification_status']})")
    lines.append("")
    return "\n".join(lines)


def integrity(_: argparse.Namespace) -> None:
    with connect() as conn:
        counts = {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in [
                "source_documents",
                "rubric_rules",
                "command_catalog",
                "flow_catalog",
                "test_case_catalog",
                "dedup_fingerprints",
                "coverage_links",
            ]
        }
        orphan_rules = conn.execute(
            """
            SELECT COUNT(*) FROM rubric_rules r
            LEFT JOIN source_documents s ON s.source_key = r.source_key
            WHERE s.source_key IS NULL
            """
        ).fetchone()[0]
        orphan_commands = conn.execute(
            """
            SELECT COUNT(*) FROM command_catalog c
            LEFT JOIN source_documents s ON s.source_key = c.source_key
            WHERE c.source_key IS NULL AND c.source_key IS NOT NULL
            """
        ).fetchone()[0]
    print(json.dumps({"ok": orphan_rules == 0 and orphan_commands == 0, "counts": counts, "orphans": {"rules": orphan_rules, "commands": orphan_commands}}, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init").set_defaults(func=init_db)
    sub.add_parser("seed-core").set_defaults(func=seed_core)
    ingest = sub.add_parser("ingest-sources")
    ingest.add_argument("--tp-dir", required=True)
    ingest.set_defaults(func=ingest_sources)
    sub.add_parser("export").set_defaults(func=export)
    sub.add_parser("integrity").set_defaults(func=integrity)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
