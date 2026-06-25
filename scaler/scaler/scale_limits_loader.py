"""scale_limits_loader - single read path for the reconciled scale-limits DB.

``scaler/scale_limits.json`` (built by ``scripts/build_scale_limits.py``) is the
single source of truth that reconciles ``limits.json`` + ``validator.py`` +
``cli_rules_db.py``.  This loader lets those consumers read THROUGH the DB so the
three can no longer silently drift.

CRITICAL SAFETY CONTRACT (matches the plan):
* ``reconcile_consumer(literal, consumer)`` PRESERVES each consumer's current
  effective value by default - it overlays only the per-consumer ``value`` the DB
  recorded, which equals the literal today.  So repointing changes NO behavior;
  it just routes the value through one SoT.
* If the DB is missing/unreadable, the literal dict is returned unchanged
  (fail-safe: a consumer never breaks because the DB file is absent).
* A future intentional change to a consumer value is made ONCE in the DB (with an
  explicit override), not by editing scattered literals.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any


def _candidate_paths() -> list[Path]:
    cands: list[Path] = []
    env = os.environ.get("SCALE_LIMITS_DB")
    if env:
        cands.append(Path(env))
    # repo: scaler/scale_limits.json (parent of this package dir)
    cands.append(Path(__file__).resolve().parents[1] / "scale_limits.json")
    # live deploy mirror
    cands.append(Path("/home/dn/SCALER/scale_limits.json"))
    return cands


@lru_cache(maxsize=1)
def load_db() -> dict[str, Any] | None:
    for p in _candidate_paths():
        try:
            if p.is_file():
                return json.loads(p.read_text())
        except Exception:  # noqa: BLE001 - a bad DB must not break the consumer
            continue
    return None


def reload() -> None:
    load_db.cache_clear()


def reconcile_consumer(literal: dict[str, Any], consumer: str) -> dict[str, Any]:
    """Return ``literal`` overlaid with the DB's preserved values for ``consumer``.

    Preserves behavior (DB records the same value today).  Returns a NEW dict so
    the caller's literal stays intact as the fallback.
    """
    db = load_db()
    out = dict(literal)
    if not db:
        return out
    for canon, spec in (db.get("limits") or {}).items():
        cons = (spec.get("consumers") or {}).get(consumer)
        if not cons:
            continue
        key = cons.get("key")
        val = cons.get("value")
        if key is not None and val is not None and key in out:
            out[key] = val  # equals the literal today; SoT-driven going forward
    return out


def get(canonical_key: str, default: Any = None) -> Any:
    """Authoritative value for a canonical limit (e.g. 'max_fxc_instances')."""
    db = load_db()
    if not db:
        return default
    spec = (db.get("limits") or {}).get(canonical_key)
    return spec.get("value", default) if spec else default


def scope_of(canonical_key: str) -> str | None:
    db = load_db()
    if not db:
        return None
    spec = (db.get("limits") or {}).get(canonical_key)
    return spec.get("scope") if spec else None


def per_ncp_limit(canonical_key: str, ncp_model: str | None) -> Any:
    """Per-NCP value (e.g. flowspec TCAM); falls back to _default then global."""
    db = load_db()
    if not db:
        return None
    per_ncp = db.get("per_ncp") or {}
    if ncp_model and ncp_model in per_ncp and canonical_key in per_ncp[ncp_model]:
        return per_ncp[ncp_model][canonical_key]
    if "_default" in per_ncp and canonical_key in per_ncp["_default"]:
        return per_ncp["_default"][canonical_key]
    return get(canonical_key)


def disagreements() -> list[dict[str, Any]]:
    db = load_db()
    if not db:
        return []
    return [
        {"canonical": k, **{kk: spec[kk] for kk in ("sources", "value", "confidence", "reconciliation_notes")}}
        for k, spec in (db.get("limits") or {}).items()
        if spec.get("disagreement")
    ]
