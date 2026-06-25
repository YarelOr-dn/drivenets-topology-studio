#!/usr/bin/env python3
"""
Full audit of topology-app persisted state.
Schema mirrors what `routes.bridge_helpers._get_credentials` actually reads:

  ~/.topology_users/<u>/devices.json         # flat: {device_id: {user,password,updated_at}}
  ~/.topology_users/<u>/xray.json            # optional per-user DUT overrides
  ~/.topology_shared/_device_state.db        # shared SQLite (watchers + events + prefs)

Exit 0 on clean; exit 1 if any [CRIT] is raised.
"""
from __future__ import annotations

import json
import os
import sqlite3
import stat
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

SHARED_DB = Path.home() / '.topology_shared' / '_device_state.db'
USERS_ROOT = Path.home() / '.topology_users'

problems: list[str] = []
warnings: list[str] = []


def err(msg: str):
    print(f"[CRIT] {msg}")
    problems.append(msg)


def warn(msg: str):
    print(f"[WARN] {msg}")
    warnings.append(msg)


def ok(msg: str):
    print(f"[OK]   {msg}")


# ---------------------------------------------------------------- shared DB --
print("=" * 78)
print("PART 1: Shared SQLite state  (~/.topology_shared/_device_state.db)")
print("=" * 78)

if not SHARED_DB.exists():
    err(f"shared DB missing: {SHARED_DB}")
else:
    ok(f"found shared DB: {SHARED_DB}  ({SHARED_DB.stat().st_size} bytes)")

    con = sqlite3.connect(SHARED_DB)
    cur = con.cursor()

    required_tables = {'device_events', 'device_watchers', 'user_device_prefs'}
    have_tables = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing = required_tables - have_tables
    if missing:
        err(f"missing tables: {missing}")
    else:
        ok(f"all required tables present: {sorted(required_tables)}")

    events_n = cur.execute("SELECT COUNT(*) FROM device_events").fetchone()[0]
    watchers_n = cur.execute("SELECT COUNT(*) FROM device_watchers").fetchone()[0]
    prefs_n = cur.execute("SELECT COUNT(*) FROM user_device_prefs").fetchone()[0]
    ok(f"rows: events={events_n}  watchers={watchers_n}  prefs={prefs_n}")

    # Stale watchers (> 24h is truly stale; a watcher can legitimately idle for an hour)
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(hours=24)
    stale = []
    for (dev, user, last_seen) in cur.execute(
            "SELECT device_id, username, last_seen_at FROM device_watchers"):
        try:
            t = datetime.fromisoformat(last_seen)
        except Exception:
            err(f"unparseable last_seen for {dev}/{user}: {last_seen!r}")
            continue
        if t < threshold:
            stale.append((dev, user, last_seen))
    if stale:
        warn(f"{len(stale)} watcher(s) stale > 24h: {stale[:3]}")
    else:
        ok("no watchers stale > 24h")

    # prefs JSON integrity
    bad_prefs = 0
    for (user, dev, prefs_json, updated) in cur.execute(
            "SELECT username, device_id, prefs_json, updated_at FROM user_device_prefs"):
        try:
            obj = json.loads(prefs_json)
            if not isinstance(obj, dict):
                err(f"prefs row not a dict: user={user} dev={dev}")
                bad_prefs += 1
        except Exception as e:
            err(f"prefs row invalid json: user={user} dev={dev}: {e}")
            bad_prefs += 1
    if not bad_prefs:
        ok(f"all {prefs_n} user_device_prefs rows have valid dict JSON")

    # events.actor_user sanity
    bad_actors = list(cur.execute(
        "SELECT id, device_id, actor_user FROM device_events WHERE actor_user IS NULL OR actor_user=''"))
    if bad_actors:
        err(f"{len(bad_actors)} events with missing actor_user: {bad_actors[:3]}")
    else:
        ok(f"all {events_n} events have actor_user set")

    con.close()

# ---------------------------------------------------------------- per-user --
print()
print("=" * 78)
print("PART 2: Per-user state  (~/.topology_users/<u>)")
print("=" * 78)

if not USERS_ROOT.exists():
    err(f"users root missing: {USERS_ROOT}")
    sys.exit(1)

user_dirs = sorted(p for p in USERS_ROOT.iterdir() if p.is_dir())
ok(f"found {len(user_dirs)} user directories")

users_with_creds = 0
users_empty = 0
insecure_files: list[tuple[str, str]] = []
schema_issues = 0
total_device_entries = 0
default_entries = 0
users_with_xray = 0
device_id_counts: dict[str, int] = {}  # device_id -> how many users have a cred for it
expected_entry_keys = {'user', 'password', 'updated_at'}

def oct_perm(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)

for u_dir in user_dirs:
    creds = u_dir / 'devices.json'
    xray = u_dir / 'xray.json'
    if xray.exists():
        users_with_xray += 1

    if not creds.exists():
        users_empty += 1
        continue

    users_with_creds += 1
    file_perm = oct_perm(creds)
    if file_perm & 0o077:
        insecure_files.append((u_dir.name, oct(file_perm)))

    try:
        data = json.loads(creds.read_text())
    except Exception as e:
        err(f"{u_dir.name}/devices.json invalid JSON: {e}")
        continue

    if not isinstance(data, dict):
        err(f"{u_dir.name}/devices.json root not a dict")
        continue

    for dev_id, entry in data.items():
        if not isinstance(entry, dict):
            err(f"{u_dir.name}/devices.json dev={dev_id} row not a dict")
            schema_issues += 1
            continue
        total_device_entries += 1
        if dev_id == '_default':
            default_entries += 1
        else:
            device_id_counts[dev_id] = device_id_counts.get(dev_id, 0) + 1

        # Key sanity
        if 'user' not in entry and 'device_user' not in entry:
            warn(f"{u_dir.name}/devices.json dev={dev_id}: no user field")
            schema_issues += 1
        if 'password' not in entry and 'device_password' not in entry:
            warn(f"{u_dir.name}/devices.json dev={dev_id}: no password field")
            schema_issues += 1

        # Unknown-key detection helps us catch schema drift
        unknown = set(entry.keys()) - (expected_entry_keys | {'device_user', 'device_password'})
        if unknown:
            warn(f"{u_dir.name}/devices.json dev={dev_id}: unknown keys {sorted(unknown)}")

ok(f"{users_with_creds} users have devices.json  ({users_empty} have empty dir)")
ok(f"{users_with_xray} users have legacy xray.json")
ok(f"{total_device_entries} total credential entries  ({default_entries} _default)")

if insecure_files:
    err(f"{len(insecure_files)} devices.json with world/group-readable perms: {insecure_files[:5]}")
else:
    ok("all devices.json files are 0600 (no world/group access)")

if schema_issues:
    warn(f"{schema_issues} schema-light entries (missing user or password)")
else:
    ok("all device entries have user + password fields")

# ---------------------------------------------------------------- cross-ref --
print()
print("=" * 78)
print("PART 3: Cross-references  (shared DB <-> user dirs)")
print("=" * 78)

con = sqlite3.connect(SHARED_DB)
cur = con.cursor()
shared_users: set[str] = set()
shared_users |= {r[0] for r in cur.execute("SELECT DISTINCT username FROM device_watchers")}
shared_users |= {r[0] for r in cur.execute("SELECT DISTINCT actor_user FROM device_events")}
shared_users |= {r[0] for r in cur.execute("SELECT DISTINCT username FROM user_device_prefs")}

user_names = {p.name for p in user_dirs}
missing_dirs = shared_users - user_names
if missing_dirs:
    warn(f"{len(missing_dirs)} user(s) referenced in shared DB have no dir: {sorted(missing_dirs)[:10]}")
else:
    ok(f"all {len(shared_users)} users referenced in shared DB have a user dir")

# Any device that's been touched by the shared DB should ideally have at least
# ONE user with a credential -- if none, show/ssh/watchers will fall back to
# the hardcoded 'dnroot/dnroot' which is fine but worth flagging.
watched = {r[0] for r in cur.execute("SELECT DISTINCT device_id FROM device_watchers")}
with_cred = set(device_id_counts.keys())
unclaimed = watched - with_cred
if unclaimed and total_device_entries:
    warn(f"{len(unclaimed)} watched device(s) have NO user credential (falls back to lab profile): {sorted(unclaimed)[:5]}")
elif not total_device_entries:
    ok("no per-user credentials stored yet -- all SSH will use lab profile fallback")

con.close()

# ---------------------------------------------------------------- summary --
print()
print("=" * 78)
print(f"AUDIT SUMMARY: problems={len(problems)}  warnings={len(warnings)}")
print("=" * 78)
for p in problems:
    print(f"  [CRIT] {p}")
for w in warnings:
    print(f"  [WARN] {w}")

if problems:
    sys.exit(1)
