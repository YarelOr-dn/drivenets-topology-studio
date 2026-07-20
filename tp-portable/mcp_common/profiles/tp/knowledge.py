"""Feature knowledge seed import and degraded/strict gate."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from mcp_common.profiles.tp.tp_env import (
    resolve_knowledge_dir,
    resolve_knowledge_seed_dir,
    resolve_strict_knowledge,
)


def knowledge_list() -> list[dict[str, str]]:
    kdir = resolve_knowledge_dir()
    items: list[dict[str, str]] = []
    if not kdir.is_dir():
        return items
    for p in sorted(kdir.iterdir()):
        if not p.is_dir() or p.name.startswith("."):
            continue
        manifest = p / "manifest.json"
        title = p.name
        if manifest.is_file():
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                title = str(data.get("title") or data.get("feature_id") or p.name)
            except Exception:
                pass
        items.append({"feature_id": p.name, "title": title, "path": str(p)})
    return items


def knowledge_import(*, force: bool = False) -> dict[str, Any]:
    seed = resolve_knowledge_seed_dir()
    dest = resolve_knowledge_dir()
    if not seed.is_dir():
        return {"ok": False, "error": f"seed dir missing: {seed}"}
    dest.mkdir(parents=True, exist_ok=True)
    imported = 0
    skipped = 0
    for p in sorted(seed.iterdir()):
        if not p.is_dir() or p.name.startswith("."):
            continue
        target = dest / p.name
        if target.exists() and not force:
            skipped += 1
            continue
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(p, target)
        imported += 1
    return {"ok": True, "imported": imported, "skipped": skipped, "dest": str(dest)}


def resolve_feature_id(epic: str) -> str | None:
    epic_u = epic.upper()
    for item in knowledge_list():
        fid = item["feature_id"]
        if epic_u in fid.upper() or fid.upper().replace("SW", "SW-") == epic_u:
            return fid
        manifest = Path(item["path"]) / "manifest.json"
        if manifest.is_file():
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                keys = [str(k).upper() for k in (data.get("epic_keys") or [])]
                if epic_u in keys:
                    return fid
            except Exception:
                pass
    return None


def knowledge_gate(epic: str, *, strict: bool | None = None) -> dict[str, Any]:
    strict = resolve_strict_knowledge() if strict is None else strict
    fid = resolve_feature_id(epic)
    if fid:
        return {"ok": True, "verdict": "CACHED", "feature_id": fid, "strict": strict}
    if strict:
        return {
            "ok": False,
            "verdict": "NOT_CACHED",
            "message": (
                f"No feature knowledge for {epic}. Run debug_knowledge_capture or "
                f"`tp knowledge import` (seed) or drop --strict-knowledge."
            ),
            "strict": True,
        }
    return {
        "ok": True,
        "verdict": "DEGRADED",
        "message": (
            f"[WARN] No cached knowledge for {epic}; proceeding in degraded mode. "
            "Unvalidated syntax will be tagged DESIGN/EXPECTED_LIVE_VALIDATE."
        ),
        "strict": False,
    }
