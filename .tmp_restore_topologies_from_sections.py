#!/usr/bin/env python3
"""Restore owner topologies.db visibility from legacy per-section JSON files.

This is an incident-recovery script for the 2026-05-13 Cmd+X topology visibility
loss. It snapshots the SQLite DB first, then inserts or repairs topology rows
from the user's existing non-empty section JSON files. It also updates the small
legacy mirror maps atomically so future section saves keep the same IDs.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


USER = "yor"
BASE = Path.home() / ".topology_users" / USER
SECTIONS = BASE / "sections"
DB = BASE / "topologies.db"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_id(*parts: str, domain: bool = False) -> str:
    h = hashlib.sha1("/".join(parts).encode("utf-8")).hexdigest()
    if domain:
        return h[:8]
    return f"{h[:8]}-{h[8:11]}"


def atomic_write_json(path: Path, data: Any) -> None:
    try:
        prior_mode = path.stat().st_mode & 0o777
    except FileNotFoundError:
        prior_mode = 0o644
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, prior_mode)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def object_counts(data: dict[str, Any]) -> tuple[int, int, int]:
    objects = data.get("objects") or []
    obj_count = len(objects) if isinstance(objects, list) else 0
    dev_count = sum(1 for o in objects if isinstance(o, dict) and o.get("type") == "device")
    link_count = sum(
        1 for o in objects
        if isinstance(o, dict) and o.get("type") in ("link", "unbound")
    )
    return obj_count, dev_count, link_count


def topology_name(path: Path) -> str:
    return path.stem.replace("_", " ")


def main() -> None:
    if not DB.exists():
        raise SystemExit(f"missing DB: {DB}")
    if not SECTIONS.exists():
        raise SystemExit(f"missing sections dir: {SECTIONS}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = BASE / f".backup_cmdx_restore_{stamp}"
    backup_dir.mkdir(mode=0o755, exist_ok=False)

    # SQLite online backup keeps a consistent snapshot even if WAL is active.
    with sqlite3.connect(str(DB)) as src, sqlite3.connect(str(backup_dir / "topologies.db")) as dst:
        src.backup(dst)
    for extra in (DB.with_suffix(DB.suffix + "-wal"), DB.with_suffix(DB.suffix + "-shm")):
        if extra.exists():
            shutil.copy2(extra, backup_dir / extra.name)

    sections = read_json(SECTIONS / "_sections.json")
    section_meta: dict[str, dict[str, Any]] = {
        str(s.get("id")): s for s in sections if isinstance(s, dict) and s.get("id")
    }

    mirror_paths = {p.name[len("_multiuser_mirror__"):-5]: p for p in SECTIONS.glob("_multiuser_mirror__*.json")}
    mirrors: dict[str, dict[str, Any]] = {}
    for sid, path in mirror_paths.items():
        try:
            mirrors[sid] = read_json(path)
        except Exception:
            mirrors[sid] = {}

    restored_domains = 0
    restored_topologies = 0
    repaired_topologies = 0
    skipped = 0

    conn = sqlite3.connect(str(DB), timeout=5.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")
        existing_domains = {
            str(r["name"]).lower(): dict(r)
            for r in conn.execute("SELECT * FROM domains").fetchall()
        }

        section_to_domain: dict[str, str] = {}
        for section_id, meta in section_meta.items():
            section_name = str(meta.get("name") or section_id)
            mirror = mirrors.get(section_id) or {}
            domain_id = ""
            for item in mirror.values():
                if isinstance(item, dict) and item.get("domain_id"):
                    domain_id = str(item["domain_id"])
                    break
            if not domain_id:
                match = existing_domains.get(section_name.lower())
                if match:
                    domain_id = str(match["id"])
            if not domain_id:
                domain_id = stable_id(USER, section_id, section_name, domain=True)
                created = now_iso()
                conn.execute(
                    "INSERT OR IGNORE INTO domains (id, name, description, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (domain_id, section_name, "", created, created),
                )
                restored_domains += conn.total_changes
                existing_domains[section_name.lower()] = {
                    "id": domain_id,
                    "name": section_name,
                }
            section_to_domain[section_id] = domain_id

        for section_dir in sorted(p for p in SECTIONS.iterdir() if p.is_dir()):
            section_id = section_dir.name
            domain_id = section_to_domain.get(section_id)
            if not domain_id:
                meta = section_meta.get(section_id, {})
                section_name = str(meta.get("name") or section_id)
                match = existing_domains.get(section_name.lower())
                if match:
                    domain_id = str(match["id"])
                else:
                    domain_id = stable_id(USER, section_id, section_name, domain=True)
                    created = now_iso()
                    conn.execute(
                        "INSERT OR IGNORE INTO domains (id, name, description, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (domain_id, section_name, "", created, created),
                    )
                section_to_domain[section_id] = domain_id

            mirror = mirrors.setdefault(section_id, {})
            changed_mirror = False
            latest_domain_mtime = 0.0
            for topo_file in sorted(section_dir.glob("*.json")):
                if topo_file.name.startswith("_"):
                    continue
                try:
                    data = read_json(topo_file)
                except Exception:
                    skipped += 1
                    continue
                if not isinstance(data, dict):
                    skipped += 1
                    continue
                obj_count, dev_count, link_count = object_counts(data)
                if obj_count <= 0:
                    skipped += 1
                    continue

                latest_domain_mtime = max(latest_domain_mtime, topo_file.stat().st_mtime)
                mapped = mirror.get(topo_file.name) if isinstance(mirror, dict) else None
                topo_id = ""
                if isinstance(mapped, dict) and mapped.get("topology_id"):
                    topo_id = str(mapped["topology_id"])

                row = None
                if topo_id:
                    row = conn.execute(
                        "SELECT * FROM topologies WHERE id = ? AND domain_id = ?",
                        (topo_id, domain_id),
                    ).fetchone()
                if row is None:
                    row = conn.execute(
                        "SELECT * FROM topologies WHERE domain_id = ? AND name = ?",
                        (domain_id, topology_name(topo_file)),
                    ).fetchone()
                    if row:
                        topo_id = str(row["id"])
                if not topo_id:
                    topo_id = stable_id(USER, section_id, topo_file.name)

                mtime_iso = datetime.fromtimestamp(topo_file.stat().st_mtime, timezone.utc).isoformat()
                data_json = json.dumps(data)
                if row is None:
                    conn.execute(
                        "INSERT INTO topologies "
                        "(id, domain_id, name, data, created_at, updated_at, object_count, device_count, link_count) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            topo_id,
                            domain_id,
                            topology_name(topo_file),
                            data_json,
                            mtime_iso,
                            mtime_iso,
                            obj_count,
                            dev_count,
                            link_count,
                        ),
                    )
                    restored_topologies += 1
                elif int(row["object_count"] or 0) < obj_count:
                    conn.execute(
                        "UPDATE topologies SET name = ?, data = ?, updated_at = ?, "
                        "object_count = ?, device_count = ?, link_count = ? "
                        "WHERE id = ? AND domain_id = ?",
                        (
                            topology_name(topo_file),
                            data_json,
                            mtime_iso,
                            obj_count,
                            dev_count,
                            link_count,
                            topo_id,
                            domain_id,
                        ),
                    )
                    repaired_topologies += 1

                current_map = mirror.get(topo_file.name)
                if not isinstance(current_map, dict) or current_map.get("domain_id") != domain_id or current_map.get("topology_id") != topo_id:
                    mirror[topo_file.name] = {"domain_id": domain_id, "topology_id": topo_id}
                    changed_mirror = True

            if latest_domain_mtime:
                latest_iso = datetime.fromtimestamp(latest_domain_mtime, timezone.utc).isoformat()
                conn.execute("UPDATE domains SET updated_at = ? WHERE id = ?", (latest_iso, domain_id))
            if changed_mirror:
                mirrors[section_id] = mirror

        conn.commit()

        for section_id, mirror in mirrors.items():
            if not mirror:
                continue
            path = SECTIONS / f"_multiuser_mirror__{section_id}.json"
            if not path.exists() or read_json(path) != mirror:
                atomic_write_json(path, mirror)

        print(f"backup_dir={backup_dir}")
        print(f"restored_domains={restored_domains}")
        print(f"restored_topologies={restored_topologies}")
        print(f"repaired_topologies={repaired_topologies}")
        print(f"skipped={skipped}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
