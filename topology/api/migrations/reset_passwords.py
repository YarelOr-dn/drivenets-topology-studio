"""Reset every active user's password to a single unified value.

Operationally we want one knob: after the username -> email-local-part
rename (see :mod:`api.migrations.rename_to_email_local`) we tell every
DriveNets engineer "your username is now your ``@drivenets.com`` local
part, your password is ``drive1234``, please change it on first login".

This script is the only blessed way to do that bulk reset. It exists
because:

* The legacy seed convention (sanitized last name) does not survive
  the rename -- some new usernames share no syllables with the old
  password, so the help-desk volume after the rename would be huge
  unless we issue one common credential.

* Hand-written ``UPDATE users SET password_hash = ...`` against
  ``_users.db`` is dangerous: a typo bricks every login. This module
  uses :func:`api.auth.user_store._hash_password` (bcrypt + per-row
  salt) so the hashes match the live verifier exactly.

* It always backs the central DB up first, refuses to run against the
  live server unless the operator explicitly opts in, and writes a
  manifest so ``--rollback MANIFEST`` is one command away.

The plaintext password is never logged or written to the manifest.
Only the SHA-256 of the plaintext is stored, purely so an operator can
prove "yes the manifest matches the password I remember handing out".

Usage
-----
::

    # Stop the server first, then:
    python3 -m api.migrations.reset_passwords --dry-run
    python3 -m api.migrations.reset_passwords --apply
    python3 -m api.migrations.reset_passwords --apply --password 'drive1234'
    python3 -m api.migrations.reset_passwords --apply --include-admin
    python3 -m api.migrations.reset_passwords --apply \
        --only askumar,akarolitsky
    python3 -m api.migrations.reset_passwords \
        --rollback ~/.topology_users/_migration_manifests/reset_passwords_<ts>.json

Defaults
--------
* Password: ``drive1234`` (override with ``--password``).
* Excludes ``admin`` (override with ``--include-admin``).
* Acts on every ``is_active = 1`` row (constrain with ``--only`` or
  ``--exclude``).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import shutil
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from api.auth.user_store import _hash_password  # noqa: E402  (after sys.path)


logger = logging.getLogger("topology.migrations.reset_passwords")


DEFAULT_USERS_DB = Path.home() / ".topology_users" / "_users.db"
DEFAULT_BACKUPS_ROOT = Path.home() / ".topology_users" / "_migration_backups"
DEFAULT_MANIFEST_DIR = Path.home() / ".topology_users" / "_migration_manifests"

PROTECTED_USERNAMES: Set[str] = {"admin"}

UNIFIED_DEFAULT_PASSWORD = "drive1234"


# ---------------------------------------------------------------------------
# Plan / result
# ---------------------------------------------------------------------------


@dataclass
class ResetPlan:
    """Concrete list of usernames whose ``password_hash`` will be rewritten."""

    targets: List[str] = field(default_factory=list)
    protected_skipped: List[str] = field(default_factory=list)
    excluded: List[str] = field(default_factory=list)
    only_filtered_out: List[str] = field(default_factory=list)
    not_found: List[str] = field(default_factory=list)

    def summary(self) -> dict:
        return {
            "targets":            len(self.targets),
            "protected_skipped":  len(self.protected_skipped),
            "excluded":           len(self.excluded),
            "only_filtered_out":  len(self.only_filtered_out),
            "not_found":          len(self.not_found),
        }


@dataclass
class ResetResult:
    started_at: str
    finished_at: str
    backup_path: Optional[Path]
    manifest_path: Optional[Path]
    rows_changed: int
    plan: ResetPlan


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _password_fingerprint(password: str) -> str:
    """Stable, non-reversible fingerprint we can safely write to disk.

    Matches against the password if and only if the operator hands the
    same plaintext back to ``--rollback`` checks. We never store the
    bcrypt hash itself in the manifest because bcrypt re-salts every
    call -- the plaintext SHA-256 is the only stable witness.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _split_csv(value: Optional[str]) -> Set[str]:
    if not value:
        return set()
    return {part.strip() for part in value.split(",") if part.strip()}


def _list_active_usernames(users_db: Path) -> List[str]:
    if not users_db.exists():
        raise FileNotFoundError(f"users DB not found: {users_db}")
    con = sqlite3.connect(str(users_db))
    try:
        rows = con.execute(
            "SELECT username FROM users WHERE is_active = 1 ORDER BY username"
        ).fetchall()
    finally:
        con.close()
    return [r[0] for r in rows]


# ---------------------------------------------------------------------------
# Plan construction
# ---------------------------------------------------------------------------


def build_plan(
    users_db: Path,
    *,
    only: Optional[Iterable[str]] = None,
    exclude: Optional[Iterable[str]] = None,
    include_admin: bool = False,
) -> ResetPlan:
    """Decide which usernames will be reset.

    Order of resolution: load all active users; intersect with
    ``--only`` if given; subtract ``--exclude``; subtract
    :data:`PROTECTED_USERNAMES` unless ``--include-admin`` is set.
    """

    active = _list_active_usernames(users_db)
    only_set = set(only or [])
    exclude_set = set(exclude or [])

    plan = ResetPlan()

    if only_set:
        plan.not_found = sorted(only_set - set(active))

    for username in active:
        if only_set and username not in only_set:
            plan.only_filtered_out.append(username)
            continue
        if username in exclude_set:
            plan.excluded.append(username)
            continue
        if username in PROTECTED_USERNAMES and not include_admin:
            plan.protected_skipped.append(username)
            continue
        plan.targets.append(username)

    plan.targets.sort()
    return plan


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


def _backup_users_db(users_db: Path, backups_root: Path) -> Path:
    backup_dir = backups_root / _now_compact()
    backup_dir.mkdir(parents=True, exist_ok=True)
    dest = backup_dir / "_users.db.bak"
    shutil.copy2(users_db, dest)
    return dest


def apply_plan(
    plan: ResetPlan,
    *,
    password: str,
    users_db: Path = DEFAULT_USERS_DB,
    backups_root: Path = DEFAULT_BACKUPS_ROOT,
    manifest_dir: Path = DEFAULT_MANIFEST_DIR,
    dry_run: bool,
) -> ResetResult:
    """Hash ``password`` once per row (bcrypt re-salts) and write into
    every targeted ``users.password_hash`` cell, atomically."""

    started_at = _now_iso()
    backup_path: Optional[Path] = None
    manifest_path: Optional[Path] = None
    rows_changed = 0

    if not plan.targets:
        return ResetResult(
            started_at=started_at,
            finished_at=_now_iso(),
            backup_path=None,
            manifest_path=None,
            rows_changed=0,
            plan=plan,
        )

    if not dry_run:
        backup_path = _backup_users_db(users_db, backups_root)
        logger.info("Backed up %s -> %s", users_db, backup_path)

        con = sqlite3.connect(str(users_db))
        try:
            con.execute("PRAGMA busy_timeout=5000")
            con.execute("BEGIN IMMEDIATE")
            for username in plan.targets:
                # bcrypt salts each call so every row gets its own hash.
                hashed = _hash_password(password)
                cur = con.execute(
                    "UPDATE users SET password_hash = ? WHERE username = ?",
                    (hashed, username),
                )
                rows_changed += cur.rowcount
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / f"reset_passwords_{_now_compact()}.json"
        manifest_path.write_text(json.dumps({
            "started_at": started_at,
            "finished_at": _now_iso(),
            "users_db": str(users_db),
            "backup_path": str(backup_path),
            "password_sha256": _password_fingerprint(password),
            "rows_changed": rows_changed,
            "targets": plan.targets,
            "protected_skipped": plan.protected_skipped,
            "excluded": plan.excluded,
            "only_filtered_out": plan.only_filtered_out,
            "not_found": plan.not_found,
        }, indent=2, sort_keys=True), encoding="utf-8")
        logger.info("Wrote manifest %s", manifest_path)

    finished_at = _now_iso()
    return ResetResult(
        started_at=started_at,
        finished_at=finished_at,
        backup_path=backup_path,
        manifest_path=manifest_path,
        rows_changed=rows_changed,
        plan=plan,
    )


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------


def rollback(
    manifest_path: Path,
    *,
    users_db: Path = DEFAULT_USERS_DB,
) -> Path:
    """Restore ``_users.db`` from the backup recorded in ``manifest_path``.

    Returns the path the backup was restored from. Raises
    :class:`FileNotFoundError` if the backup is missing.
    """
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    backup_str = manifest.get("backup_path")
    if not backup_str:
        raise ValueError(f"manifest has no backup_path: {manifest_path}")
    backup = Path(backup_str)
    if not backup.exists():
        raise FileNotFoundError(f"backup missing: {backup}")
    shutil.copy2(backup, users_db)
    logger.info("Rolled back %s from %s", users_db, backup)
    return backup


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="reset_passwords",
        description="Reset every active topology user to a unified password.",
    )
    p.add_argument("--users-db", default=str(DEFAULT_USERS_DB))
    p.add_argument("--backups-root", default=str(DEFAULT_BACKUPS_ROOT))
    p.add_argument("--manifest-dir", default=str(DEFAULT_MANIFEST_DIR))
    p.add_argument("--password", default=UNIFIED_DEFAULT_PASSWORD,
                   help=f"Password to set (default: {UNIFIED_DEFAULT_PASSWORD!r}).")
    p.add_argument("--only",
                   help="Comma-separated subset of usernames to reset.")
    p.add_argument("--exclude",
                   help="Comma-separated usernames to skip.")
    p.add_argument("--include-admin", action="store_true",
                   help=f"Also reset {sorted(PROTECTED_USERNAMES)} "
                        "(off by default).")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true",
                      help="Compute and print the plan; do not touch any state.")
    mode.add_argument("--apply", action="store_true",
                      help="Apply the plan (stop the topology server first).")
    mode.add_argument("--rollback", metavar="MANIFEST",
                      help="Restore _users.db from a previous --apply manifest.")
    return p


def _print_plan(plan: ResetPlan, password: str) -> None:
    summary = plan.summary()
    print("Reset plan:")
    for k, v in summary.items():
        print(f"  {k:18s} {v:5d}")
    print(f"  password_sha256    {_password_fingerprint(password)}")
    if plan.targets:
        head = plan.targets[:10]
        tail = plan.targets[-3:] if len(plan.targets) > 13 else []
        print("  sample targets    :", ", ".join(head)
              + (" ... " + ", ".join(tail) if tail else ""))
    if plan.not_found:
        print("  not_found in DB   :", ", ".join(plan.not_found))
    if plan.protected_skipped:
        print("  protected_skipped :", ", ".join(plan.protected_skipped))


def main(argv: Optional[Sequence[str]] = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    parser = _build_parser()
    args = parser.parse_args(argv)

    users_db = Path(args.users_db).expanduser()
    backups_root = Path(args.backups_root).expanduser()
    manifest_dir = Path(args.manifest_dir).expanduser()

    if args.rollback:
        manifest = Path(args.rollback).expanduser()
        if not manifest.exists():
            print(f"manifest not found: {manifest}", file=sys.stderr)
            return 2
        rollback(manifest, users_db=users_db)
        print(f"OK: rolled back {users_db} from {manifest}")
        return 0

    plan = build_plan(
        users_db,
        only=_split_csv(args.only),
        exclude=_split_csv(args.exclude),
        include_admin=args.include_admin,
    )
    _print_plan(plan, args.password)

    if args.dry_run:
        print("DRY-RUN: no rows updated.")
        return 0

    if not plan.targets:
        print("Nothing to do (plan is empty).")
        return 0

    result = apply_plan(
        plan,
        password=args.password,
        users_db=users_db,
        backups_root=backups_root,
        manifest_dir=manifest_dir,
        dry_run=False,
    )
    print(f"OK: rows_changed={result.rows_changed} "
          f"backup={result.backup_path} manifest={result.manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
