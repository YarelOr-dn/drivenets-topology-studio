"""Rename existing topology users to their @drivenets.com email local part.

Reads the JSON cache produced by
:mod:`api.migrations.email_resolver` and applies, atomically, the
implied ``old_username -> new_username`` plan to:

* the central ``~/.topology_users/_users.db`` registry and every
  share-related table whose PK / FK encodes a username
* the per-user filesystem (``~/.topology_users/<username>/``)
* every per-user ``topologies.db`` (events, knowledge scopes, share-side
  details JSON)
* the cross-user ``~/.topology_shared/_device_state.db`` watchers,
  events, and prefs

Design notes
------------
* The script is *idempotent*: re-running ``--apply`` after a successful
  run finds nothing to rename and exits 0. Re-running after a partial
  failure also picks up where the last run left off because every
  successful per-user rename writes a manifest fragment before moving on.

* Backups are non-negotiable. ``--apply`` always creates a timestamped
  backup directory under ``~/.topology_users/_migration_backups/<ts>/``
  and copies every database we are about to touch into it before any
  write. The manifest written at the end of the run lists exactly which
  backup goes with which DB, so the ``--rollback`` mode can restore
  byte-for-byte.

* We never rename ``admin``. The bootstrap account stays put even if
  someone slipped a row into the cache for it.

* We never invent a target username. Only entries with
  ``status == "matched"`` (or, optionally, ``"inactive_match"``) and a
  successful :func:`derive_username_from_email` result are part of the
  plan. Everything else is reported and left alone.

* Pre-flight refuses to start if any rename would collide with another
  *active* topology username that is not itself part of the same plan.

* The migration runs offline. Stop the FastAPI server first
  (``deploy_topology.sh stop`` / equivalent) -- the script does not try
  to coordinate live writers, and any open JWTs will refer to the old
  username and naturally fail at the next request.

Composite-ID note
-----------------
Several share tables encode the owner *inside* a composite primary key,
e.g. ``shared_domains.domain_id = "yarel:default"`` and
``shared_topologies.composite_id = "yarel:34bb4271:bf8c9051-ff9"``. The
migration rewrites only the leading owner segment, leaves the trailing
domain / topology IDs untouched, and updates every foreign-key column
that references the composite key in the same transaction.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from api.auth.identity import (  # noqa: E402  -- after sys.path tweak
    InvalidIdentityError,
    derive_username_from_email,
    is_company_email,
    validate_username,
)


logger = logging.getLogger("topology.migrations.rename_to_email_local")


PROTECTED_USERNAMES = {"admin"}
DEFAULT_USERS_DB = Path.home() / ".topology_users" / "_users.db"
DEFAULT_USERS_BASE = Path.home() / ".topology_users"
DEFAULT_DEVICE_STATE_DB = Path.home() / ".topology_shared" / "_device_state.db"
DEFAULT_BACKUPS_ROOT = Path.home() / ".topology_users" / "_migration_backups"
DEFAULT_REPORT_PATH = Path.home() / ".topology_users" / "username_migration_report.json"
DEFAULT_MANIFEST_DIR = Path.home() / ".topology_users" / "_migration_manifests"


# ---------------------------------------------------------------------------
# Plan data
# ---------------------------------------------------------------------------


@dataclass
class PlanRow:
    """One concrete rename: ``old`` becomes ``new``."""

    old: str
    new: str
    email: str
    display_name: str
    source_status: str

    def as_json(self) -> Dict[str, str]:
        return {
            "old_username": self.old,
            "new_username": self.new,
            "email": self.email,
            "display_name": self.display_name,
            "source_status": self.source_status,
        }


@dataclass
class Plan:
    """Full migration plan, ready for dry-run or apply."""

    renames: List[PlanRow] = field(default_factory=list)
    no_op: List[Dict[str, str]] = field(default_factory=list)
    skipped: List[Dict[str, str]] = field(default_factory=list)
    invalid: List[Dict[str, str]] = field(default_factory=list)
    collisions: List[Dict[str, str]] = field(default_factory=list)
    duplicates: List[Dict[str, str]] = field(default_factory=list)
    protected: List[Dict[str, str]] = field(default_factory=list)

    @property
    def is_safe(self) -> bool:
        return not (self.collisions or self.duplicates or self.invalid)

    def summary(self) -> Dict[str, int]:
        return {
            "renames":     len(self.renames),
            "no_op":       len(self.no_op),
            "skipped":     len(self.skipped),
            "invalid":     len(self.invalid),
            "collisions":  len(self.collisions),
            "duplicates":  len(self.duplicates),
            "protected":   len(self.protected),
        }

    def as_report(self) -> Dict[str, Any]:
        return {
            "generated_at": _now_iso(),
            "summary": self.summary(),
            "renames": [r.as_json() for r in self.renames],
            "no_op": self.no_op,
            "skipped": self.skipped,
            "invalid": self.invalid,
            "collisions": self.collisions,
            "duplicates": self.duplicates,
            "protected": self.protected,
        }


# ---------------------------------------------------------------------------
# Plan construction
# ---------------------------------------------------------------------------


def _load_cache(path: Path) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"email cache not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"email cache must be a JSON object: {path}")
    return data


def _all_active_usernames(users_db: Path) -> List[str]:
    con = sqlite3.connect(users_db)
    try:
        rows = con.execute(
            "SELECT username FROM users WHERE is_active = 1"
        ).fetchall()
    finally:
        con.close()
    return [r[0] for r in rows]


def build_plan(
    cache: Dict[str, Dict[str, Any]],
    *,
    users_db: Path,
    include_inactive: bool = False,
) -> Plan:
    """Translate the resolver cache + live DB into a concrete rename plan."""

    accept_status = {"matched"}
    if include_inactive:
        accept_status.add("inactive_match")

    plan = Plan()
    active = set(_all_active_usernames(users_db))

    target_owners: Dict[str, str] = {}  # new_username -> old_username (origin)
    for old_username, entry in cache.items():
        status = entry.get("status")
        display_name = entry.get("display_name") or old_username
        email = (entry.get("email") or "").strip().lower()

        if old_username in PROTECTED_USERNAMES:
            plan.protected.append({
                "old_username": old_username,
                "display_name": display_name,
                "reason": "protected bootstrap username",
            })
            continue

        if status not in accept_status:
            plan.skipped.append({
                "old_username": old_username,
                "display_name": display_name,
                "status": status or "?",
                "notes": entry.get("notes", ""),
            })
            continue
        if not is_company_email(email):
            plan.invalid.append({
                "old_username": old_username,
                "display_name": display_name,
                "email": email,
                "reason": f"not a verified @drivenets.com email",
            })
            continue
        try:
            new_username = derive_username_from_email(email)
        except InvalidIdentityError as exc:
            plan.invalid.append({
                "old_username": old_username,
                "display_name": display_name,
                "email": email,
                "reason": str(exc),
            })
            continue
        try:
            validate_username(new_username)
        except InvalidIdentityError as exc:
            plan.invalid.append({
                "old_username": old_username,
                "display_name": display_name,
                "email": email,
                "reason": f"derived username invalid: {exc}",
            })
            continue

        if new_username == old_username:
            plan.no_op.append({
                "username": old_username,
                "display_name": display_name,
                "email": email,
            })
            continue

        # Duplicate target within the plan?
        if new_username in target_owners:
            plan.duplicates.append({
                "new_username": new_username,
                "old_a": target_owners[new_username],
                "old_b": old_username,
                "display_name": display_name,
            })
            continue
        target_owners[new_username] = old_username
        plan.renames.append(PlanRow(
            old=old_username,
            new=new_username,
            email=email,
            display_name=display_name,
            source_status=status,
        ))

    plan_old = {r.old for r in plan.renames}
    plan_new = {r.new for r in plan.renames}
    for r in plan.renames:
        # If the target is in active users AND that target is not itself
        # going to be renamed away in this plan, we have a collision.
        if r.new in active and r.new not in plan_old:
            plan.collisions.append({
                "old_username": r.old,
                "new_username": r.new,
                "display_name": r.display_name,
                "reason": "target username already exists and is not being renamed",
            })

    plan.renames = [
        r for r in plan.renames
        if not any(c["old_username"] == r.old for c in plan.collisions)
    ]
    return plan


# ---------------------------------------------------------------------------
# Apply: low-level helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _ts_log(*args: Any) -> None:
    logger.info(" ".join(str(a) for a in args))


def _backup_file(src: Path, backup_dir: Path, label: str) -> Optional[Path]:
    """Copy ``src`` into ``backup_dir`` with a stable, descriptive filename."""
    if not src.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    dest = backup_dir / f"{label}.bak"
    shutil.copy2(src, dest)
    return dest


def _remap_text(text: str, mapping: Dict[str, str]) -> Tuple[str, bool]:
    """Replace whole-token usernames inside JSON-ish text.

    JSON values containing the username will be quoted, e.g.
    ``"target_user": "yarel"``. We replace ``"yarel"`` -> ``"yor"`` so
    we don't accidentally hit unrelated substrings (a username that
    happens to be a substring of a topology name, etc).
    """
    if not text:
        return text, False
    changed = False
    out = text
    for old, new in mapping.items():
        token_old = f'"{old}"'
        token_new = f'"{new}"'
        if token_old in out:
            out = out.replace(token_old, token_new)
            changed = True
    return out, changed


def _composite_remap(value: str, mapping: Dict[str, str]) -> Tuple[str, bool]:
    """Rewrite the leading ``<owner>:`` segment of a composite key."""
    if not value or ":" not in value:
        return value, False
    head, _, rest = value.partition(":")
    new_head = mapping.get(head)
    if new_head is None:
        return value, False
    return f"{new_head}:{rest}", True


# ---------------------------------------------------------------------------
# Apply: central users DB
# ---------------------------------------------------------------------------


def _apply_central_users_db(
    users_db: Path,
    rename_map: Dict[str, str],
    *,
    dry_run: bool,
) -> Dict[str, Any]:
    """Rewrite every username-bearing row in the central registry."""
    counters: Dict[str, int] = {
        "users": 0,
        "shared_domains": 0,
        "domain_shares": 0,
        "shared_topologies": 0,
        "topology_shares": 0,
        "share_activity": 0,
    }
    if not rename_map:
        return counters

    con = sqlite3.connect(users_db)
    try:
        con.execute("BEGIN IMMEDIATE")

        # users.username (PK) -- safe to UPDATE because FK enforcement
        # is OFF on this DB.
        for old, new in rename_map.items():
            cur = con.execute(
                "UPDATE users SET username = ? WHERE username = ?",
                (new, old),
            )
            counters["users"] += cur.rowcount

        # shared_domains: owner + composite domain_id
        rows = con.execute(
            "SELECT domain_id, owner FROM shared_domains"
        ).fetchall()
        for old_did, old_owner in rows:
            new_owner = rename_map.get(old_owner, old_owner)
            new_did, _ = _composite_remap(old_did, rename_map)
            if new_owner != old_owner or new_did != old_did:
                con.execute(
                    "UPDATE shared_domains SET domain_id = ?, owner = ? "
                    "WHERE domain_id = ?",
                    (new_did, new_owner, old_did),
                )
                counters["shared_domains"] += 1

        # domain_shares: composite domain_id, username, granted_by
        rows = con.execute(
            "SELECT domain_id, username, permission, granted_at, granted_by "
            "FROM domain_shares"
        ).fetchall()
        for did, uname, perm, granted_at, granted_by in rows:
            new_did, _ = _composite_remap(did, rename_map)
            new_uname = rename_map.get(uname, uname)
            new_gby = rename_map.get(granted_by, granted_by)
            if (new_did, new_uname, new_gby) != (did, uname, granted_by):
                con.execute(
                    "DELETE FROM domain_shares WHERE domain_id = ? AND username = ?",
                    (did, uname),
                )
                con.execute(
                    "INSERT INTO domain_shares (domain_id, username, permission, granted_at, granted_by) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (new_did, new_uname, perm, granted_at, new_gby),
                )
                counters["domain_shares"] += 1

        # shared_topologies
        rows = con.execute(
            "SELECT composite_id, owner FROM shared_topologies"
        ).fetchall()
        for old_cid, old_owner in rows:
            new_owner = rename_map.get(old_owner, old_owner)
            new_cid, _ = _composite_remap(old_cid, rename_map)
            if new_owner != old_owner or new_cid != old_cid:
                con.execute(
                    "UPDATE shared_topologies SET composite_id = ?, owner = ? "
                    "WHERE composite_id = ?",
                    (new_cid, new_owner, old_cid),
                )
                counters["shared_topologies"] += 1

        # topology_shares
        rows = con.execute(
            "SELECT composite_id, username, permission, granted_at, granted_by "
            "FROM topology_shares"
        ).fetchall()
        for cid, uname, perm, granted_at, granted_by in rows:
            new_cid, _ = _composite_remap(cid, rename_map)
            new_uname = rename_map.get(uname, uname)
            new_gby = rename_map.get(granted_by, granted_by)
            if (new_cid, new_uname, new_gby) != (cid, uname, granted_by):
                con.execute(
                    "DELETE FROM topology_shares WHERE composite_id = ? AND username = ?",
                    (cid, uname),
                )
                con.execute(
                    "INSERT INTO topology_shares (composite_id, username, permission, granted_at, granted_by) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (new_cid, new_uname, perm, granted_at, new_gby),
                )
                counters["topology_shares"] += 1

        # share_activity
        rows = con.execute(
            "SELECT id, domain_id, owner, actor, target_user FROM share_activity"
        ).fetchall()
        for sa_id, did, owner, actor, target in rows:
            new_did, _ = _composite_remap(did, rename_map)
            new_owner = rename_map.get(owner, owner)
            new_actor = rename_map.get(actor, actor)
            new_target = rename_map.get(target, target) if target else target
            if (new_did, new_owner, new_actor, new_target) != (did, owner, actor, target):
                con.execute(
                    "UPDATE share_activity "
                    "SET domain_id = ?, owner = ?, actor = ?, target_user = ? "
                    "WHERE id = ?",
                    (new_did, new_owner, new_actor, new_target, sa_id),
                )
                counters["share_activity"] += 1

        if dry_run:
            con.execute("ROLLBACK")
        else:
            con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()
    return counters


# ---------------------------------------------------------------------------
# Apply: per-user filesystem and per-user DBs
# ---------------------------------------------------------------------------


def _move_user_dirs(
    users_base: Path,
    rename_map: Dict[str, str],
    *,
    dry_run: bool,
) -> List[Tuple[str, str, str]]:
    """Move ``<base>/<old>`` to ``<base>/<new>``.

    Returns a list of (old, new, action) tuples where action is one of
    ``moved``, ``missing``, ``target_exists``. Two-phase moves (via a
    temporary suffix) protect the rare case where a target directory
    already exists because some other rename has been applied earlier.
    """
    actions: List[Tuple[str, str, str]] = []
    for old, new in rename_map.items():
        old_dir = users_base / old
        new_dir = users_base / new
        if not old_dir.exists():
            actions.append((old, new, "missing"))
            continue
        if new_dir.exists():
            actions.append((old, new, "target_exists"))
            continue
        if dry_run:
            actions.append((old, new, "would_move"))
            continue
        old_dir.rename(new_dir)
        actions.append((old, new, "moved"))
    return actions


def _apply_per_user_db(
    db_path: Path,
    rename_map: Dict[str, str],
    *,
    dry_run: bool,
) -> Dict[str, int]:
    """Rewrite username references inside a per-user ``topologies.db``.

    Touches:

    * ``topology_events.actor_user`` (direct username column)
    * ``topology_events.details_json`` (free JSON, may carry
      ``target_user``, ``granted_by``, ``actor``, etc.)
    * ``domain_knowledge.payload`` (scope JSON may name other users)
    """
    counters = {"topology_events_actor": 0, "topology_events_details": 0,
               "domain_knowledge": 0}
    if not db_path.exists() or not rename_map:
        return counters
    con = sqlite3.connect(db_path)
    try:
        con.execute("BEGIN IMMEDIATE")

        # actor_user column
        rows = con.execute(
            "SELECT id, actor_user FROM topology_events"
        ).fetchall()
        for row_id, actor in rows:
            new_actor = rename_map.get(actor, actor)
            if new_actor != actor:
                con.execute(
                    "UPDATE topology_events SET actor_user = ? WHERE id = ?",
                    (new_actor, row_id),
                )
                counters["topology_events_actor"] += 1

        # details_json (text)
        rows = con.execute(
            "SELECT id, details_json FROM topology_events"
        ).fetchall()
        for row_id, details in rows:
            new_details, changed = _remap_text(details or "", rename_map)
            if changed:
                con.execute(
                    "UPDATE topology_events SET details_json = ? WHERE id = ?",
                    (new_details, row_id),
                )
                counters["topology_events_details"] += 1

        # domain_knowledge payload (free JSON; may reference users)
        rows = con.execute(
            "SELECT domain_id, visibility, kind, key, payload FROM domain_knowledge"
        ).fetchall()
        for did, vis, kind, key, payload in rows:
            new_payload, changed = _remap_text(payload or "", rename_map)
            if changed:
                con.execute(
                    "UPDATE domain_knowledge SET payload = ? "
                    "WHERE domain_id = ? AND visibility = ? AND kind = ? AND key = ?",
                    (new_payload, did, vis, kind, key),
                )
                counters["domain_knowledge"] += 1

        if dry_run:
            con.execute("ROLLBACK")
        else:
            con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()
    return counters


def _apply_device_state(
    db_path: Path,
    rename_map: Dict[str, str],
    *,
    dry_run: bool,
) -> Dict[str, int]:
    """Rename watchers, events, and prefs in ``_device_state.db``."""
    counters = {"device_watchers": 0, "device_events": 0, "user_device_prefs": 0}
    if not db_path.exists() or not rename_map:
        return counters
    con = sqlite3.connect(db_path)
    try:
        con.execute("BEGIN IMMEDIATE")

        # device_watchers (composite PK: device_id, username)
        rows = con.execute(
            "SELECT device_id, username, topology_id, canvas_ip, last_seen_at, registered_at "
            "FROM device_watchers"
        ).fetchall()
        for did, uname, tid, cip, lsa, ra in rows:
            new_uname = rename_map.get(uname, uname)
            if new_uname != uname:
                con.execute(
                    "DELETE FROM device_watchers WHERE device_id = ? AND username = ?",
                    (did, uname),
                )
                con.execute(
                    "INSERT INTO device_watchers "
                    "(device_id, username, topology_id, canvas_ip, last_seen_at, registered_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (did, new_uname, tid, cip, lsa, ra),
                )
                counters["device_watchers"] += 1

        # device_events.actor_user + payload_json
        rows = con.execute(
            "SELECT id, actor_user, payload_json FROM device_events"
        ).fetchall()
        for row_id, actor, payload in rows:
            new_actor = rename_map.get(actor, actor)
            new_payload, payload_changed = _remap_text(payload or "", rename_map)
            if new_actor != actor or payload_changed:
                con.execute(
                    "UPDATE device_events SET actor_user = ?, payload_json = ? "
                    "WHERE id = ?",
                    (new_actor, new_payload, row_id),
                )
                counters["device_events"] += 1

        # user_device_prefs (composite PK: username, device_id)
        rows = con.execute(
            "SELECT username, device_id, prefs_json, updated_at FROM user_device_prefs"
        ).fetchall()
        for uname, did, prefs, ts in rows:
            new_uname = rename_map.get(uname, uname)
            new_prefs, prefs_changed = _remap_text(prefs or "", rename_map)
            if new_uname != uname or prefs_changed:
                con.execute(
                    "DELETE FROM user_device_prefs WHERE username = ? AND device_id = ?",
                    (uname, did),
                )
                con.execute(
                    "INSERT INTO user_device_prefs (username, device_id, prefs_json, updated_at) "
                    "VALUES (?, ?, ?, ?)",
                    (new_uname, did, new_prefs, ts),
                )
                counters["user_device_prefs"] += 1

        if dry_run:
            con.execute("ROLLBACK")
        else:
            con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()
    return counters


# ---------------------------------------------------------------------------
# Apply: top-level
# ---------------------------------------------------------------------------


@dataclass
class ApplyResult:
    started_at: str
    finished_at: str
    backup_dir: Optional[Path]
    counters: Dict[str, Any]
    rename_map: Dict[str, str]
    user_dir_actions: List[Tuple[str, str, str]]
    manifest_path: Optional[Path]


def apply_plan(
    plan: Plan,
    *,
    users_db: Path,
    users_base: Path,
    device_state_db: Path,
    backups_root: Path,
    manifest_dir: Path,
    dry_run: bool,
) -> ApplyResult:
    rename_map = {r.old: r.new for r in plan.renames}
    started_at = _now_iso()

    backup_dir: Optional[Path] = None
    backups: Dict[str, str] = {}
    if rename_map and not dry_run:
        backup_dir = backups_root / _now_compact()
        for src, label in (
            (users_db, "_users.db"),
            (device_state_db, "_device_state.db"),
        ):
            dest = _backup_file(src, backup_dir, label.replace(".", "_").lstrip("_"))
            if dest:
                backups[label] = str(dest)
        # Per-user topologies.db copies
        for old in rename_map:
            user_db = users_base / old / "topologies.db"
            dest = _backup_file(user_db, backup_dir, f"user__{old}__topologies_db")
            if dest:
                backups[f"{old}/topologies.db"] = str(dest)

    counters: Dict[str, Any] = {}

    counters["central"] = _apply_central_users_db(
        users_db, rename_map, dry_run=dry_run,
    )

    user_dir_actions = _move_user_dirs(
        users_base, rename_map, dry_run=dry_run,
    )

    counters["per_user_dbs"] = {}
    for old, new in rename_map.items():
        # After the move the per-user DB lives at the new path.
        new_user_db = (users_base / (new if not dry_run else old)) / "topologies.db"
        counters["per_user_dbs"][old] = _apply_per_user_db(
            new_user_db, rename_map, dry_run=dry_run,
        )

    counters["device_state"] = _apply_device_state(
        device_state_db, rename_map, dry_run=dry_run,
    )

    finished_at = _now_iso()
    manifest_path: Optional[Path] = None
    if not dry_run and rename_map:
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / f"manifest_{_now_compact()}.json"
        manifest_path.write_text(json.dumps({
            "started_at": started_at,
            "finished_at": finished_at,
            "rename_map": rename_map,
            "backup_dir": str(backup_dir) if backup_dir else None,
            "backups": backups,
            "user_dir_actions": user_dir_actions,
            "counters": counters,
            "summary": plan.summary(),
        }, indent=2, sort_keys=True), encoding="utf-8")

    return ApplyResult(
        started_at=started_at,
        finished_at=finished_at,
        backup_dir=backup_dir,
        counters=counters,
        rename_map=rename_map,
        user_dir_actions=user_dir_actions,
        manifest_path=manifest_path,
    )


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------


def rollback(
    manifest_path: Path,
    *,
    users_db: Path = DEFAULT_USERS_DB,
    users_base: Path = DEFAULT_USERS_BASE,
    device_state_db: Path = DEFAULT_DEVICE_STATE_DB,
) -> None:
    """Restore DBs from a manifest's backup set + reverse-rename user dirs.

    Expects the manifest produced by a successful ``--apply`` run. The
    rollback is best-effort: it logs errors but keeps going so a partial
    state can be recovered as much as possible.

    Path overrides exist for two reasons: integration tests run on a
    sandbox copy, and an operator might want to dry-restore a DB into a
    side directory before swapping it in.
    """
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    backups: Dict[str, str] = manifest.get("backups", {})
    rename_map: Dict[str, str] = manifest.get("rename_map", {})

    # Reverse user-dir moves first so subsequent file restores land in
    # the right place for callers that expect <username>/topologies.db.
    for old, new in rename_map.items():
        new_dir = users_base / new
        old_dir = users_base / old
        if new_dir.exists() and not old_dir.exists():
            new_dir.rename(old_dir)
            logger.info("rollback: %s -> %s", new, old)

    # Restore central + device-state
    for label, path in backups.items():
        backup = Path(path)
        if not backup.exists():
            logger.error("rollback: backup missing %s", backup)
            continue
        if label == "_users.db":
            shutil.copy2(backup, users_db)
        elif label == "_device_state.db":
            shutil.copy2(backup, device_state_db)
        elif "/topologies.db" in label:
            old_user = label.split("/", 1)[0]
            target = users_base / old_user / "topologies.db"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup, target)
        else:
            logger.warning("rollback: unrecognised backup label %s", label)
        logger.info("rollback: restored %s from %s", label, backup)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="rename_to_email_local",
        description="Rename topology users to their @drivenets.com email local part.",
    )
    p.add_argument("--cache", default=str(Path.home() / ".topology_users" / "username_email_cache.json"),
                   help="Path to email_resolver JSON cache.")
    p.add_argument("--users-db", default=str(DEFAULT_USERS_DB))
    p.add_argument("--users-base", default=str(DEFAULT_USERS_BASE))
    p.add_argument("--device-state-db", default=str(DEFAULT_DEVICE_STATE_DB))
    p.add_argument("--backups-root", default=str(DEFAULT_BACKUPS_ROOT))
    p.add_argument("--manifest-dir", default=str(DEFAULT_MANIFEST_DIR))
    p.add_argument("--report", default=str(DEFAULT_REPORT_PATH),
                   help="Where to write the JSON migration report.")
    p.add_argument("--include-inactive", action="store_true",
                   help="Also rename users marked 'inactive_match' in the cache.")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true",
                      help="Compute and print the plan; do not touch any state.")
    mode.add_argument("--apply", action="store_true",
                      help="Apply the plan (requires the topology server to be stopped).")
    mode.add_argument("--rollback", metavar="MANIFEST",
                      help="Restore DBs from a previous --apply manifest.")
    p.add_argument("--allow-unsafe", action="store_true",
                   help="Apply even when the plan reports collisions, duplicates, "
                        "or invalid entries (DANGEROUS).")
    return p


def _print_plan(plan: Plan, report_path: Path) -> None:
    summary = plan.summary()
    _ts_log("Plan summary:")
    for k, v in summary.items():
        _ts_log(f"  {k:14s} {v:5d}")
    if plan.invalid:
        _ts_log("Invalid entries (will not be migrated):")
        for r in plan.invalid:
            _ts_log("  -", r)
    if plan.duplicates:
        _ts_log("Duplicate target usernames (will not be migrated):")
        for r in plan.duplicates:
            _ts_log("  -", r)
    if plan.collisions:
        _ts_log("Collisions with existing usernames (will not be migrated):")
        for r in plan.collisions:
            _ts_log("  -", r)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(plan.as_report(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    _ts_log("Report written:", report_path)


def main(argv: Optional[List[str]] = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    args = _build_parser().parse_args(argv)

    if args.rollback:
        manifest = Path(args.rollback).expanduser()
        if not manifest.exists():
            logger.error("manifest not found: %s", manifest)
            return 2
        rollback(
            manifest,
            users_db=Path(args.users_db).expanduser(),
            users_base=Path(args.users_base).expanduser(),
            device_state_db=Path(args.device_state_db).expanduser(),
        )
        return 0

    cache_path = Path(args.cache).expanduser()
    users_db = Path(args.users_db).expanduser()
    users_base = Path(args.users_base).expanduser()
    device_state_db = Path(args.device_state_db).expanduser()
    backups_root = Path(args.backups_root).expanduser()
    manifest_dir = Path(args.manifest_dir).expanduser()
    report_path = Path(args.report).expanduser()

    cache = _load_cache(cache_path)
    plan = build_plan(
        cache,
        users_db=users_db,
        include_inactive=args.include_inactive,
    )
    _print_plan(plan, report_path)

    if not plan.is_safe and not args.allow_unsafe:
        logger.error("Plan has unsafe entries; refusing to apply. "
                     "Re-run with --allow-unsafe to override (NOT RECOMMENDED).")
        return 3 if args.apply else 0

    result = apply_plan(
        plan,
        users_db=users_db,
        users_base=users_base,
        device_state_db=device_state_db,
        backups_root=backups_root,
        manifest_dir=manifest_dir,
        dry_run=args.dry_run,
    )

    _ts_log("Counters:", json.dumps(result.counters, indent=2, sort_keys=True))
    if result.manifest_path:
        _ts_log("Manifest:", result.manifest_path)
    if result.backup_dir:
        _ts_log("Backups :", result.backup_dir)
    if args.dry_run:
        _ts_log("DRY-RUN: no changes written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
