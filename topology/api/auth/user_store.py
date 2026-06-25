"""User store with SQLite backend for the multi-user Topology Creator.

Each user gets their own directory (~/.topology_users/<username>/) with:
  - topologies.db: SQLite database with topology domains and topology files
  - uploads/: user-specific uploaded files

The central _users.db has the user registry (credentials, roles, metadata).
Shared topologies live in ~/.topology_shared/<domain_id>/.

All path construction is centralized here -- no other module touches file paths.
"""

from __future__ import annotations

import json
import hashlib
import hmac
import os
import secrets
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import bcrypt

from ..config import settings


USERS_DB_PATH = Path(settings.users_base_dir).expanduser() / "_users.db"
SHARED_DIR = Path(settings.shared_topologies_dir).expanduser()
DOMAIN_TOPOLOGY_LIMIT = 15


class TopologyConflictError(RuntimeError):
    """Raised by save_topology when the caller's ``base_updated_at``
    is older than the stored row's ``updated_at`` -- i.e. another
    user already saved newer content. The router translates this into
    an HTTP 409 so the client can surface a Merge / Overwrite / Cancel
    dialog instead of silently clobbering.

    ``current_updated_at`` / ``last_actor`` / ``last_actor_display`` are
    surfaced so the client can say "Alice saved this 4 minutes ago" in
    the dialog header without an extra round-trip.
    """

    def __init__(
        self,
        current_updated_at: str,
        last_actor: Optional[str] = None,
        last_actor_display: Optional[str] = None,
    ) -> None:
        super().__init__("Remote changed since you opened this topology")
        self.current_updated_at = current_updated_at
        self.last_actor = last_actor or ""
        self.last_actor_display = last_actor_display or last_actor or ""


class DomainTopologyLimitError(RuntimeError):
    """Raised when a create would exceed the per-user per-domain topology cap."""

    def __init__(
        self,
        domain_id: str,
        limit: int = DOMAIN_TOPOLOGY_LIMIT,
        topologies: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.domain_id = domain_id
        self.limit = int(limit)
        self.topologies = topologies or []
        self.topology_count = len(self.topologies)
        super().__init__(
            f"Domain contains {self.topology_count} topology file(s). "
            f"The limit is {self.limit}. Delete one or more topologies before creating another."
        )

    def to_detail(self) -> Dict[str, Any]:
        return {
            "error": str(self),
            "code": "domain-topology-limit",
            "domain_id": self.domain_id,
            "limit": self.limit,
            "topology_count": self.topology_count,
            "topologies": self.topologies,
        }

# Synthetic domain id surfaced to every user. Holds all topologies shared
# with them at file-level granularity (per-file shares). It is virtual --
# it lives nowhere in any user's DB; list_domains() injects it on the fly,
# and list_topologies() resolves it against the topology_shares table.
# Treated as undeletable + unmodifiable + un-resharable everywhere.
SHARED_WITH_ME_DOMAIN_ID = "__shared_with_me"
SHARED_WITH_ME_DOMAIN_NAME = "Shared with me"
SHARED_WITH_ME_DOMAIN_DESC = "Topologies shared directly with you"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


@contextmanager
def _open_db(db_path: str | Path, row_factory: bool = True) -> Generator[sqlite3.Connection, None, None]:
    """Thread-safe SQLite connection tuned for many simultaneous users.

    WAL + synchronous=NORMAL lets readers and writers run in parallel
    across separate connections (essential for the knowledge poller
    fanning out to every user's DB while that user is also editing).
    ``busy_timeout`` gives SQLite ~5 s to retry on a lock before raising,
    which is plenty for the tiny writes we do."""
    # ``timeout=5.0`` arms Python's own retry layer on SQLITE_BUSY. Combined
    # with PRAGMA busy_timeout below, concurrent writers from the poller and
    # user REST calls back off cleanly instead of raising "database is locked".
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA wal_autocheckpoint=1000")
    except Exception:
        # Pragmas are best-effort; if the DB is corrupt we still want the
        # caller to see the real error from the actual query below.
        pass
    if row_factory:
        conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class UserStore:
    """Central user registry + per-user topology domain management."""

    def __init__(self):
        self._ensure_central_db()
        self._ensure_admin()

    def _ensure_central_db(self):
        USERS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _open_db(USERS_DB_PATH, row_factory=False) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    email TEXT,
                    role TEXT NOT NULL DEFAULT 'engineer',
                    created_at TEXT NOT NULL,
                    last_login TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS shared_domains (
                    domain_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    owner TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (owner) REFERENCES users(username)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS domain_shares (
                    domain_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    permission TEXT NOT NULL DEFAULT 'read',
                    granted_at TEXT NOT NULL,
                    granted_by TEXT NOT NULL,
                    PRIMARY KEY (domain_id, username),
                    FOREIGN KEY (domain_id) REFERENCES shared_domains(domain_id),
                    FOREIGN KEY (username) REFERENCES users(username)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS share_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    action TEXT NOT NULL,
                    domain_id TEXT NOT NULL,
                    domain_name TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    target_user TEXT,
                    permission TEXT,
                    notes TEXT
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_share_activity_ts ON share_activity(ts DESC)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_share_activity_domain ON share_activity(domain_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_share_activity_owner ON share_activity(owner)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_share_activity_target ON share_activity(target_user)"
            )

            # -- Per-file (per-topology) sharing -------------------------
            # Mirrors the shared_domains / domain_shares pair, but at the
            # topology-file granularity. Composite key is
            # "owner:domain_id:topology_id" so two users can each share a
            # topology with the same id without collision.
            conn.execute("""
                CREATE TABLE IF NOT EXISTS shared_topologies (
                    composite_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    domain_id TEXT NOT NULL,
                    topology_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (owner) REFERENCES users(username)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS topology_shares (
                    composite_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    permission TEXT NOT NULL DEFAULT 'read',
                    granted_at TEXT NOT NULL,
                    granted_by TEXT NOT NULL,
                    PRIMARY KEY (composite_id, username),
                    FOREIGN KEY (composite_id) REFERENCES shared_topologies(composite_id),
                    FOREIGN KEY (username) REFERENCES users(username)
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_topology_shares_user ON topology_shares(username)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_shared_topologies_owner ON shared_topologies(owner)"
            )
            conn.commit()

    def _ensure_admin(self):
        if not self.get_user(settings.default_admin_username):
            self.create_user(
                username=settings.default_admin_username,
                password=settings.default_admin_password,
                display_name="Administrator",
                role="admin",
            )

    # -- User CRUD --

    def create_user(
        self,
        username: str,
        password: str,
        display_name: str,
        email: str = "",
        role: str = "engineer",
    ) -> Dict[str, Any]:
        with _open_db(USERS_DB_PATH) as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, display_name, email, role, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (username, _hash_password(password), display_name, email, role, _now_iso()),
            )
            conn.commit()

        user_dir = self.user_dir(username)
        user_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_user_db(username)
        self._create_default_domain(username)

        return self.get_user(username)

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        with _open_db(USERS_DB_PATH) as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ? AND is_active = 1",
                (username,),
            ).fetchone()
            return dict(row) if row else None

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        user = self.get_user(username)
        if not user:
            return None
        if not _check_password(password, user["password_hash"]):
            return None
        with _open_db(USERS_DB_PATH) as conn:
            conn.execute(
                "UPDATE users SET last_login = ? WHERE username = ?",
                (_now_iso(), username),
            )
            conn.commit()
        return user

    def update_user(self, username: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        allowed = {"display_name", "email", "role", "is_active"}
        fields = {k: v for k, v in updates.items() if k in allowed and v is not None}
        if "password" in updates and updates["password"]:
            fields["password_hash"] = _hash_password(updates["password"])
        if not fields:
            return self.get_user(username)
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        with _open_db(USERS_DB_PATH) as conn:
            conn.execute(
                f"UPDATE users SET {set_clause} WHERE username = ?",
                list(fields.values()) + [username],
            )
            conn.commit()
        return self.get_user(username)

    def list_users(self) -> List[Dict[str, Any]]:
        with _open_db(USERS_DB_PATH) as conn:
            rows = conn.execute(
                "SELECT username, display_name, email, role, created_at, last_login, is_active "
                "FROM users WHERE is_active = 1 ORDER BY username"
            ).fetchall()
            return [dict(r) for r in rows]

    def change_password(self, username: str, current: str, new: str) -> bool:
        user = self.get_user(username)
        if not user or not _check_password(current, user["password_hash"]):
            return False
        with _open_db(USERS_DB_PATH) as conn:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (_hash_password(new), username),
            )
            conn.commit()
        return True

    def delete_user(self, username: str) -> bool:
        with _open_db(USERS_DB_PATH) as conn:
            conn.execute(
                "UPDATE users SET is_active = 0 WHERE username = ?", (username,),
            )
            conn.commit()
        return True

    # -- Path resolution --

    def user_dir(self, username: str) -> Path:
        return Path(settings.users_base_dir).expanduser() / username

    def user_db_path(self, username: str) -> Path:
        return self.user_dir(username) / "topologies.db"

    # -- Per-user XRAY / capture / credentials paths --
    #
    # Layout under ~/.topology_users/<username>/:
    #   xray.json     - Mac IP, Wireshark path, pcap directory, per-user device creds
    #   client.json   - workstation profile (host_os, hostname, last seen IP, ...)
    #   devices.json  - optional per-user override for SSH credentials per device
    #   captures/     - server-side pcap files (live_capture is told to write here)

    def user_xray_config_path(self, username: str) -> Path:
        """Per-user XRAY config (Mac IP, Wireshark path, credentials)."""
        return self.user_dir(username) / settings.xray_per_user_config_filename

    def user_client_profile_path(self, username: str) -> Path:
        """Per-user workstation profile (host OS, hostname, last seen IP)."""
        return self.user_dir(username) / settings.xray_per_user_client_filename

    def user_devices_db_path(self, username: str) -> Path:
        """Optional per-user device-credentials DB (overrides global XRAY creds)."""
        return self.user_dir(username) / settings.xray_per_user_devices_filename

    def user_captures_dir(self, username: str) -> Path:
        """Per-user directory for server-side pcap captures (created on demand)."""
        path = self.user_dir(username) / settings.xray_per_user_captures_dirname
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        return path

    # -- Canonical "give me a per-user file path" helper --
    #
    # Use this for every NEW feature that needs a small state file under the
    # user's workspace (JSON blobs, small SQLite DBs, scratch caches). It is
    # the single choke point so we never hand-roll ``Path.home() / ".topology_users"``
    # in feature code, and it enforces:
    #   - the user workspace exists (mkdir -p, idempotent)
    #   - the resolved path NEVER escapes ``~/.topology_users/<username>/``
    #     even if ``filename`` is adversarial (e.g. ``../../etc/passwd``,
    #     absolute paths, ``..`` segments, etc.)
    #
    # See DEVELOPMENT_GUIDELINES.md "Multi-User is the Default" for the
    # project-wide rule this helper backs.
    def user_data_path(self, username: str, filename: str) -> Path:
        """Return a safe per-user path for ``filename``.

        The returned path is guaranteed to live inside the user's workspace
        directory (``~/.topology_users/<username>/``). The workspace is
        created on demand. Sub-directories inside ``filename`` are allowed
        (e.g. ``"reports/2026-04.json"``) -- any missing parent directory is
        created automatically.

        Raises:
            ValueError: if ``username`` is empty, if ``filename`` is empty,
                if ``filename`` is absolute, or if the resolved path would
                escape the user's workspace (``..`` traversal).
        """
        if not username or not isinstance(username, str):
            raise ValueError("user_data_path: username is required")
        if not filename or not isinstance(filename, str):
            raise ValueError("user_data_path: filename is required")
        # Reject absolute paths outright -- we only take relative filenames.
        fname_path = Path(filename)
        if fname_path.is_absolute():
            raise ValueError(
                f"user_data_path: filename must be relative, got {filename!r}"
            )
        base = self.ensure_user_workspace(username).resolve()
        target = (base / fname_path).resolve()
        # Make sure the resolved path still sits inside the user's workspace.
        try:
            target.relative_to(base)
        except ValueError as exc:
            raise ValueError(
                f"user_data_path: refusing to escape user workspace "
                f"(base={base}, resolved={target})"
            ) from exc
        # Auto-create parent directories so callers can just write().
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        return target

    def user_jira_config_path(self, username: str) -> Path:
        """Per-user Jira Cloud credentials (base_url, email, api_token).

        Thin convenience wrapper around :meth:`user_data_path` so new code
        can use a typed accessor instead of the raw filename. The storage
        filename (``jira_config.json``) is stable across serve.py and any
        future route-based implementation.
        """
        return self.user_data_path(username, "jira_config.json")

    def user_ai_config_path(self, username: str) -> Path:
        """Per-user AI assistant credentials (provider, model, api_key, base_url).

        Mirrors :meth:`user_jira_config_path`: the raw file always lives at
        ``~/.topology_users/<username>/ai_config.json`` (mode 0600), and the
        ``api_key`` is never echoed back through the GET endpoint -- only
        ``configured``, ``provider``, ``model``, and a masked token hint.
        """
        return self.user_data_path(username, "ai_config.json")

    def user_profile_prefs_path(self, username: str) -> Path:
        """Per-user visual profile preferences (avatar palette / face / accessory).

        Stored as ``~/.topology_users/<username>/profile_prefs.json`` so
        it survives the same lifecycle as every other per-user config.
        The companion ``/api/auth/me/profile`` endpoints round-trip it as
        ``{ avatar: { palette, face, accessory } }``. The frontend's
        CloudAvatar generator consults this preference set to render the
        user's top-bar pill, share dialog entries, and impersonation
        picker with the same custom face across every surface.
        """
        return self.user_data_path(username, "profile_prefs.json")

    def user_ai_chats_db_path(self, username: str) -> Path:
        """Per-user SQLite database for AI chat history (Phase B).

        Exposed alongside :meth:`user_ai_config_path` so anything that
        persists AI conversation state has a single canonical location.
        The DB itself is created lazily by the AI module via the same
        ``_open_db`` context manager used elsewhere in this store (WAL +
        ``busy_timeout=5000``).
        """
        return self.user_data_path(username, "ai_chats.db")

    def user_cursor_token_path(self, username: str) -> Path:
        """Per-user Cursor MCP token metadata.

        The raw token is only returned when issued/rotated. At rest we store a
        SHA-256 digest in the authenticated user's private workspace, with mode
        0600 because this file grants remote MCP access to the user's topology
        data.
        """
        return self.user_data_path(username, "cursor_mcp_token.json")

    def issue_cursor_token(self, username: str) -> Dict[str, Any]:
        """Create or rotate the user's Cursor MCP token.

        Returns the raw token once so the web app can place it in the copy-paste
        install prompt. Callers must not persist or log the raw token.
        """
        if not self.get_user(username):
            raise ValueError("user not found")
        token = "topo_" + secrets.token_urlsafe(32)
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        payload = {
            "version": 1,
            "username": username,
            "token_sha256": digest,
            "created_at": _now_iso(),
        }
        path = self.user_cursor_token_path(username)
        tmp = path.with_suffix(path.suffix + ".tmp")
        try:
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, sort_keys=True)
                f.flush()
                os.fsync(f.fileno())
            os.chmod(tmp, 0o600)
            os.replace(tmp, path)
        finally:
            try:
                tmp.unlink()
            except OSError:
                pass
        return {"token": token, "created_at": payload["created_at"]}

    def revoke_cursor_token(self, username: str) -> bool:
        """Remove the user's Cursor MCP token, if present."""
        if not self.get_user(username):
            return False
        path = self.user_cursor_token_path(username)
        try:
            path.unlink()
            return True
        except FileNotFoundError:
            return True
        except OSError:
            return False

    def cursor_token_status(self, username: str) -> Dict[str, Any]:
        """Return non-secret metadata for the user's Cursor MCP token."""
        path = self.user_cursor_token_path(username)
        try:
            with path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            digest = str(payload.get("token_sha256") or "")
            return {
                "configured": bool(digest),
                "created_at": payload.get("created_at") or "",
                "token_hint": digest[:8] if digest else "",
            }
        except (OSError, json.JSONDecodeError):
            return {"configured": False, "created_at": "", "token_hint": ""}

    def validate_cursor_token(self, token: str) -> Optional[str]:
        """Resolve a Cursor MCP bearer token to a username.

        Tokens are stored per-user, so validation intentionally scans active
        users and compares SHA-256 digests using constant-time comparison. The
        token count is tiny relative to normal request volume, and this keeps
        token state physically under each user's workspace.
        """
        raw = (token or "").strip()
        if not raw:
            return None
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        try:
            users = self.list_users()
        except Exception:
            return None
        for user in users:
            username = user.get("username") or ""
            if not username:
                continue
            try:
                path = self.user_cursor_token_path(username)
                with path.open("r", encoding="utf-8") as f:
                    payload = json.load(f)
                stored = str(payload.get("token_sha256") or "")
                if stored and hmac.compare_digest(stored, digest):
                    return username
            except (OSError, json.JSONDecodeError, ValueError):
                continue
        return None

    def user_monitored_devices_path(self, username: str) -> Path:
        """Per-user references file for the auto-monitor registry.

        Tracks WHICH monitored devices the caller has on their canvas
        (one row per ``{key, scope_type, scope_id}``). The shared registry
        DB at ``~/.topology_shared/monitored_registry.db`` is the source of
        truth for the device record itself; this file is just the
        per-user reference accounting so a different user's detach can
        never tear down a device this user is still watching.

        See ``topology/docs/AUTO_MONITOR_ON_ATTACH.md`` Section 3 / 8.
        """
        return self.user_data_path(username, "monitored_devices.json")

    def ensure_user_workspace(self, username: str) -> Path:
        """Create the per-user directory + captures sub-dir if missing.

        Returns the user dir path. Safe to call repeatedly; idempotent.
        Used by serve.py the first time it sees a JWT for a username so the
        workspace always exists even if the user predates this layout.
        """
        user_dir = self.user_dir(username)
        try:
            user_dir.mkdir(parents=True, exist_ok=True)
            self.user_captures_dir(username)  # also creates captures/
        except OSError:
            pass
        return user_dir

    # -- Per-user SQLite (topology domains + topologies) --

    def _ensure_user_db(self, username: str):
        db_path = self.user_db_path(username)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with _open_db(db_path, row_factory=False) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS domains (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS topologies (
                    id TEXT PRIMARY KEY,
                    domain_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    object_count INTEGER DEFAULT 0,
                    device_count INTEGER DEFAULT 0,
                    link_count INTEGER DEFAULT 0,
                    FOREIGN KEY (domain_id) REFERENCES domains(id)
                )
            """)
            # Domain Knowledge -- per-domain attached context (branches, Jira,
            # notes, CLI presets, test-suite links, bug filters, ...). See
            # `topology/api/domains/knowledge.py` for the kind registry.
            #
            # Hybrid visibility model:
            #   visibility='public'  -> travels with domain shares. Stored in
            #                           the OWNER's DB; recipients of a shared
            #                           domain see owner's public rows read-only
            #                           (unless their share permission is 'write').
            #   visibility='private' -> per-viewer annotations that NEVER travel.
            #                           Stored in the VIEWER's DB. For a shared-in
            #                           domain the row uses the composite id
            #                           "<owner>:<original_id>" as `domain_id` so
            #                           it can't collide with the viewer's own
            #                           domains.
            #
            # `payload` is JSON -- structure depends on `kind`. `pinned` lets
            # users bubble a few items to the top of the UI. `sort_order` is
            # used for manual reordering inside the knowledge panel.
            conn.execute("""
                CREATE TABLE IF NOT EXISTS domain_knowledge (
                    domain_id   TEXT NOT NULL,
                    visibility  TEXT NOT NULL,
                    kind        TEXT NOT NULL,
                    key         TEXT NOT NULL,
                    payload     TEXT NOT NULL,
                    pinned      INTEGER DEFAULT 0,
                    sort_order  INTEGER DEFAULT 0,
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL,
                    PRIMARY KEY (domain_id, visibility, kind, key)
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_dk_domain ON domain_knowledge(domain_id, visibility)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_dk_kind ON domain_knowledge(kind)"
            )
            # Per-topology activity log. Lives in the OWNER's DB so every
            # recipient of a per-file share transparently sees the same
            # history (we look it up through list_topology_events which
            # resolves the composite id -> owner). Pruned to the most
            # recent 500 rows per (domain_id, topology_id) on every
            # insert so DB growth stays bounded no matter how chatty
            # the canvas is.
            #
            # `details_json` is a free-form JSON blob that carries the
            # per-event payload (diff counts, added/removed device ids,
            # renamed-from/to, recipient, ...). Callers should keep it
            # small -- the summary column is what the UI displays by
            # default; details are for the expandable "More" row.
            conn.execute("""
                CREATE TABLE IF NOT EXISTS topology_events (
                    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain_id          TEXT NOT NULL,
                    topology_id        TEXT NOT NULL,
                    actor_user         TEXT NOT NULL,
                    actor_display_name TEXT NOT NULL,
                    event_type         TEXT NOT NULL,
                    summary            TEXT NOT NULL,
                    details_json       TEXT NOT NULL DEFAULT '{}',
                    created_at         TEXT NOT NULL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_topo_events_key "
                "ON topology_events(domain_id, topology_id, id DESC)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_topo_events_actor "
                "ON topology_events(actor_user)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_topo_events_type "
                "ON topology_events(event_type)"
            )
            conn.commit()

    def _create_default_domain(self, username: str):
        db_path = self.user_db_path(username)
        with _open_db(db_path, row_factory=False) as conn:
            existing = conn.execute("SELECT COUNT(*) FROM domains").fetchone()[0]
            if existing == 0:
                now = _now_iso()
                conn.execute(
                    "INSERT INTO domains (id, name, description, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    ("default", "My Topologies", "Default topology domain", now, now),
                )
                conn.commit()

    # -- Topology Domains --

    def list_domains(self, username: str) -> List[Dict[str, Any]]:
        self._ensure_user_db(username)
        with _open_db(self.user_db_path(username)) as conn:
            rows = conn.execute(
                "SELECT d.*, (SELECT COUNT(*) FROM topologies t WHERE t.domain_id = d.id) as topology_count "
                "FROM domains d ORDER BY d.name"
            ).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["owner"] = username
                d["is_shared"] = False
                d["is_built_in"] = (d["id"] == "default")
                d["is_locked"] = False
                result.append(d)

        shared = self._list_shared_domains_for_user(username)
        result.extend(shared)

        # Always inject the built-in "Shared with me" synthetic domain. It is
        # part of every user's view, can never be deleted, and exposes all
        # per-file shares targeting them. Place it last so own/shared domains
        # (which the user actively curates) stay near the top.
        result.append(self.shared_with_me_domain(username))
        return result

    def create_domain(self, username: str, name: str, description: str = "") -> Dict[str, Any]:
        domain_id = str(uuid.uuid4())[:8]
        now = _now_iso()
        self._ensure_user_db(username)
        with _open_db(self.user_db_path(username)) as conn:
            conn.execute(
                "INSERT INTO domains (id, name, description, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (domain_id, name, description, now, now),
            )
            conn.commit()
        return {
            "id": domain_id, "name": name, "description": description,
            "owner": username, "is_shared": False, "topology_count": 0,
            "created_at": now, "updated_at": now,
        }

    def update_domain(self, username: str, domain_id: str, name: str, description: str = "") -> bool:
        """Update an owned domain's display metadata."""
        if domain_id in ("default", SHARED_WITH_ME_DOMAIN_ID):
            return False
        now = _now_iso()
        self._ensure_user_db(username)
        with _open_db(self.user_db_path(username), row_factory=False) as conn:
            cursor = conn.execute(
                "UPDATE domains SET name = ?, description = ?, updated_at = ? WHERE id = ?",
                (name, description, now, domain_id),
            )
            conn.commit()
            return (cursor.rowcount or 0) > 0

    def delete_domain(self, username: str, domain_id: str) -> bool:
        # "default" is the personal home domain and "__shared_with_me" is the
        # synthetic, built-in cross-user inbox -- both are undeletable.
        if domain_id == "default" or domain_id == SHARED_WITH_ME_DOMAIN_ID:
            return False
        self._ensure_user_db(username)
        with _open_db(self.user_db_path(username)) as conn:
            topo_count = conn.execute(
                "SELECT COUNT(*) FROM topologies WHERE domain_id = ?",
                (domain_id,),
            ).fetchone()[0]
            if int(topo_count or 0) > 0:
                return False
            conn.execute("DELETE FROM topologies WHERE domain_id = ?", (domain_id,))
            # Cascade-drop the owner's public + any private knowledge on this
            # domain. Private rows authored by recipients of a past share are
            # cleaned below via sweep_orphan_private_knowledge so deletion is
            # genuinely idempotent and no stranded annotations linger.
            conn.execute("DELETE FROM domain_knowledge WHERE domain_id = ?", (domain_id,))
            conn.execute("DELETE FROM domains WHERE id = ?", (domain_id,))
            conn.commit()
        # Sweep orphan private annotations in every OTHER user's DB. This is
        # best-effort and never blocks the owner-side delete.
        try:
            self.sweep_orphan_private_knowledge(username, domain_id)
        except Exception:
            pass
        return True

    # -- Topologies within a Domain --

    def list_topologies(self, username: str, domain_id: str) -> List[Dict[str, Any]]:
        # The built-in "Shared with me" domain is virtual -- its rows live in
        # the central topology_shares table, not the user's own DB.
        if domain_id == SHARED_WITH_ME_DOMAIN_ID:
            return self.list_incoming_topology_shares(username)
        self._ensure_user_db(username)
        with _open_db(self.user_db_path(username)) as conn:
            rows = conn.execute(
                "SELECT id, domain_id, name, created_at, updated_at, "
                "object_count, device_count, link_count "
                "FROM topologies WHERE domain_id = ? ORDER BY updated_at DESC",
                (domain_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def save_topology(
        self, username: str, domain_id: str, name: str, data: Dict[str, Any],
        topology_id: Optional[str] = None,
        actor: Optional[str] = None,
        actor_display_name: Optional[str] = None,
        base_updated_at: Optional[str] = None,
        micro_events: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        # A user can SAVE INTO "Shared with me" only if they're updating a
        # specific shared file they have write permission on. New topologies
        # cannot be created there since no one owns that synthetic domain.
        actor = actor or username
        if domain_id == SHARED_WITH_ME_DOMAIN_ID:
            if not topology_id:
                raise PermissionError(
                    "Cannot create new topologies in the 'Shared with me' domain"
                )
            share = self.resolve_shared_topology(username, topology_id)
            if not share:
                raise PermissionError("Topology is not shared with you")
            if share["permission"] != "write":
                raise PermissionError("You only have read access to this shared topology")
            owner = share["owner"]
            real_domain_id = share["domain_id"]
            real_topology_id = share["topology_id"]
            return self._save_topology_in_owner_db(
                owner, real_domain_id, real_topology_id, name, data,
                public_id=topology_id, public_domain_id=SHARED_WITH_ME_DOMAIN_ID,
                actor=actor, actor_display_name=actor_display_name,
                base_updated_at=base_updated_at, micro_events=micro_events,
            )
        return self._save_topology_in_owner_db(
            username, domain_id, topology_id, name, data,
            actor=actor, actor_display_name=actor_display_name,
            base_updated_at=base_updated_at, micro_events=micro_events,
        )

    def _save_topology_in_owner_db(
        self,
        owner: str,
        domain_id: str,
        topology_id: Optional[str],
        name: str,
        data: Dict[str, Any],
        public_id: Optional[str] = None,
        public_domain_id: Optional[str] = None,
        actor: Optional[str] = None,
        actor_display_name: Optional[str] = None,
        base_updated_at: Optional[str] = None,
        micro_events: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        now = _now_iso()
        data_json = json.dumps(data)
        objects = data.get("objects", [])
        obj_count = len(objects)
        dev_count = sum(1 for o in objects if o.get("type") == "device")
        link_count = sum(1 for o in objects if o.get("type") in ("link", "unbound"))
        actor = actor or owner
        actor_display_name = actor_display_name or actor

        self._ensure_user_db(owner)
        with _open_db(self.user_db_path(owner)) as conn:
            is_create = not topology_id
            prev_row = None
            prev_objects: List[Dict[str, Any]] = []
            prev_name = name
            if topology_id:
                prev_row = conn.execute(
                    "SELECT id, name, data, updated_at FROM topologies "
                    "WHERE id = ? AND domain_id = ?",
                    (topology_id, domain_id),
                ).fetchone()
                if prev_row:
                    prev_name = prev_row["name"] or name
                    # Conflict guard: caller opened this topology at
                    # base_updated_at; if the DB moved on since, surface
                    # a 409 so the client can Merge / Overwrite / Cancel.
                    if base_updated_at and prev_row["updated_at"]:
                        if str(prev_row["updated_at"]) > str(base_updated_at):
                            last_actor = ""
                            last_actor_display = ""
                            last_evt = conn.execute(
                                "SELECT actor_user, actor_display_name "
                                "FROM topology_events "
                                "WHERE domain_id = ? AND topology_id = ? "
                                "  AND event_type IN ('topology.saved', 'topology.created') "
                                "ORDER BY id DESC LIMIT 1",
                                (domain_id, topology_id),
                            ).fetchone()
                            if last_evt:
                                last_actor = last_evt["actor_user"] or ""
                                last_actor_display = last_evt["actor_display_name"] or last_actor
                            raise TopologyConflictError(
                                current_updated_at=prev_row["updated_at"],
                                last_actor=last_actor,
                                last_actor_display=last_actor_display,
                            )
                    try:
                        prev_objects = (json.loads(prev_row["data"]) or {}).get("objects", []) or []
                    except Exception:
                        prev_objects = []

            if is_create:
                existing = conn.execute(
                    "SELECT id, domain_id, name, created_at, updated_at, "
                    "object_count, device_count, link_count "
                    "FROM topologies WHERE domain_id = ? ORDER BY updated_at DESC",
                    (domain_id,),
                ).fetchall()
                if len(existing) >= DOMAIN_TOPOLOGY_LIMIT:
                    raise DomainTopologyLimitError(
                        domain_id,
                        DOMAIN_TOPOLOGY_LIMIT,
                        [dict(r) for r in existing],
                    )

            if topology_id:
                conn.execute(
                    "UPDATE topologies SET name=?, data=?, updated_at=?, "
                    "object_count=?, device_count=?, link_count=? WHERE id=? AND domain_id=?",
                    (name, data_json, now, obj_count, dev_count, link_count, topology_id, domain_id),
                )
            else:
                topology_id = str(uuid.uuid4())[:12]
                conn.execute(
                    "INSERT INTO topologies (id, domain_id, name, data, created_at, updated_at, "
                    "object_count, device_count, link_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (topology_id, domain_id, name, data_json, now, now,
                     obj_count, dev_count, link_count),
                )
            conn.execute(
                "UPDATE domains SET updated_at = ? WHERE id = ?", (now, domain_id),
            )

            # Record the event in the same transaction so the log never
            # shows a save that isn't in the DB (or vice versa).
            summary, details = self._build_save_event_payload(
                is_create=is_create,
                prev_name=prev_name,
                new_name=name,
                prev_objects=prev_objects,
                new_objects=objects,
                micro_events=micro_events,
            )
            self.record_topology_event(
                owner=owner,
                domain_id=domain_id,
                topology_id=topology_id,
                actor_user=actor,
                actor_display_name=actor_display_name,
                event_type="topology.created" if is_create else "topology.saved",
                summary=summary,
                details=details,
                conn=conn,
            )
            conn.commit()

        return {
            "id": public_id or topology_id,
            "domain_id": public_domain_id or domain_id,
            "name": name,
            "created_at": now, "updated_at": now,
            "object_count": obj_count, "device_count": dev_count, "link_count": link_count,
            # Internal bookkeeping surfaced to the router so it can fan out a
            # live WebSocket frame to every collaborator of this topology.
            "__owner": owner,
            "__real_domain_id": domain_id,
            "__real_topology_id": topology_id,
            "__event_summary": summary,
            "__event_details": details,
            "__event_type": "topology.created" if is_create else "topology.saved",
            "__actor": actor,
            "__actor_display": actor_display_name,
        }

    # -- Diff summary for save events ---------------------------------------
    #
    # Collapses an object-list-vs-object-list diff into the kind of terse
    # human sentence that reads well inline in the Logs panel ("+3 devices,
    # -1 link, renamed NCP-1 -> Router-A, moved 4 objects"). Callers pass
    # the pre-save snapshot (already in the DB) and the post-save payload;
    # optional client-recorded micro_events get spliced into `details` so
    # the UI can expand the event and see fine-grained ops.

    @staticmethod
    def _build_save_event_payload(
        is_create: bool,
        prev_name: str,
        new_name: str,
        prev_objects: List[Dict[str, Any]],
        new_objects: List[Dict[str, Any]],
        micro_events: Optional[List[Dict[str, Any]]] = None,
    ) -> (str, Dict[str, Any]):
        def index(objs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
            out: Dict[str, Dict[str, Any]] = {}
            for o in objs or []:
                oid = o.get("id")
                if oid is not None:
                    out[str(oid)] = o
            return out

        prev_idx = index(prev_objects)
        new_idx = index(new_objects)
        prev_keys = set(prev_idx.keys())
        new_keys = set(new_idx.keys())
        added_keys = list(new_keys - prev_keys)
        removed_keys = list(prev_keys - new_keys)
        common_keys = prev_keys & new_keys

        def is_device(o: Dict[str, Any]) -> bool:
            return o.get("type") == "device"

        def is_link(o: Dict[str, Any]) -> bool:
            return o.get("type") in ("link", "unbound")

        added_devices = [new_idx[k] for k in added_keys if is_device(new_idx[k])]
        added_links = [new_idx[k] for k in added_keys if is_link(new_idx[k])]
        added_other = [
            new_idx[k] for k in added_keys
            if not is_device(new_idx[k]) and not is_link(new_idx[k])
        ]
        removed_devices = [prev_idx[k] for k in removed_keys if is_device(prev_idx[k])]
        removed_links = [prev_idx[k] for k in removed_keys if is_link(prev_idx[k])]
        removed_other = [
            prev_idx[k] for k in removed_keys
            if not is_device(prev_idx[k]) and not is_link(prev_idx[k])
        ]

        renames: List[Dict[str, str]] = []
        moved = 0
        relabelled = 0
        for k in common_keys:
            a = prev_idx[k]
            b = new_idx[k]
            if is_device(a) and is_device(b):
                old_label = str(a.get("label") or "")
                new_label = str(b.get("label") or "")
                if old_label != new_label and (old_label or new_label):
                    renames.append({
                        "id": str(k), "from": old_label, "to": new_label,
                    })
            else:
                if (a.get("text") or "") != (b.get("text") or ""):
                    relabelled += 1
            try:
                if abs(float(a.get("x") or 0) - float(b.get("x") or 0)) > 0.5 \
                        or abs(float(a.get("y") or 0) - float(b.get("y") or 0)) > 0.5:
                    moved += 1
            except Exception:
                pass

        parts: List[str] = []
        if is_create:
            parts.append(f"Created '{new_name}'")
        else:
            if prev_name != new_name:
                parts.append(f"Renamed '{prev_name}' -> '{new_name}'")
            else:
                parts.append(f"Saved '{new_name}'")

        def plus(n: int, label: str) -> Optional[str]:
            if n <= 0:
                return None
            return f"+{n} {label}{'s' if n != 1 else ''}"

        def minus(n: int, label: str) -> Optional[str]:
            if n <= 0:
                return None
            return f"-{n} {label}{'s' if n != 1 else ''}"

        bits = list(filter(None, [
            plus(len(added_devices), "device"),
            minus(len(removed_devices), "device"),
            plus(len(added_links), "link"),
            minus(len(removed_links), "link"),
            plus(len(added_other), "object"),
            minus(len(removed_other), "object"),
        ]))
        if bits:
            parts.append(", ".join(bits))
        if renames:
            shown = renames[:3]
            rename_bits = ", ".join(
                f"{r['from'] or '?'}->{r['to'] or '?'}" for r in shown
            )
            if len(renames) > 3:
                rename_bits += f", +{len(renames) - 3} more"
            parts.append("renamed " + rename_bits)
        if moved:
            parts.append(f"moved {moved}")
        if relabelled:
            parts.append(f"relabeled {relabelled}")

        summary = " | ".join(parts) if parts else f"Saved '{new_name}'"

        details: Dict[str, Any] = {
            "is_create": bool(is_create),
            "prev_name": prev_name,
            "new_name": new_name,
            "counts": {
                "prev_total": len(prev_objects or []),
                "new_total": len(new_objects or []),
                "added_devices": len(added_devices),
                "removed_devices": len(removed_devices),
                "added_links": len(added_links),
                "removed_links": len(removed_links),
                "added_other": len(added_other),
                "removed_other": len(removed_other),
                "moved": moved,
                "renamed_devices": len(renames),
                "relabeled_text": relabelled,
            },
            "renames": renames[:25],
            "added_ids": [str(k) for k in added_keys][:50],
            "removed_ids": [str(k) for k in removed_keys][:50],
        }
        if micro_events:
            details["micro_events"] = [
                e for e in micro_events if isinstance(e, dict)
            ][:200]
        return summary, details

    def load_topology(self, username: str, domain_id: str, topology_id: str) -> Optional[Dict[str, Any]]:
        # Shared-with-me inbox: the topology_id is the composite share id; we
        # have to look up the real owner+domain+topology and read THEIR DB.
        if domain_id == SHARED_WITH_ME_DOMAIN_ID:
            share = self.resolve_shared_topology(username, topology_id)
            if not share:
                return None
            owner_db = self.user_db_path(share["owner"])
            self._ensure_user_db(share["owner"])
            with _open_db(owner_db) as conn:
                row = conn.execute(
                    "SELECT * FROM topologies WHERE id = ? AND domain_id = ?",
                    (share["topology_id"], share["domain_id"]),
                ).fetchone()
                if not row:
                    return None
                result = dict(row)
                result["data"] = json.loads(result["data"])
                # Surface that this came through the shared inbox so the
                # frontend can render badges / disable destructive controls.
                result["id"] = topology_id  # keep the composite id for round-tripping
                result["domain_id"] = SHARED_WITH_ME_DOMAIN_ID
                result["__owner"] = share["owner"]
                result["__source_domain_id"] = share["domain_id"]
                result["__source_topology_id"] = share["topology_id"]
                result["__permission"] = share["permission"]
                result["__is_shared_with_me"] = True
                return result

        self._ensure_user_db(username)
        with _open_db(self.user_db_path(username)) as conn:
            row = conn.execute(
                "SELECT * FROM topologies WHERE id = ? AND domain_id = ?",
                (topology_id, domain_id),
            ).fetchone()
            if row:
                result = dict(row)
                result["data"] = json.loads(result["data"])
                return result
            return None

    def delete_topology(
        self,
        username: str,
        domain_id: str,
        topology_id: str,
        actor: Optional[str] = None,
        actor_display_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Delete a topology. Returns a dict with ``deleted`` + broadcast
        metadata (recipients that had the file shared, last known name)
        so the router can fan out a ``topology.deleted`` WebSocket frame
        before the event row is purged.
        """
        # You cannot delete a file someone shared with you. Use unshare instead.
        if domain_id == SHARED_WITH_ME_DOMAIN_ID:
            return {"deleted": False}
        actor = actor or username
        actor_display_name = actor_display_name or actor
        recipients = self.list_topology_recipients(username, domain_id, topology_id)
        meta = self._topology_meta(username, domain_id, topology_id)
        topo_name = (meta or {}).get("name") or topology_id

        self._ensure_user_db(username)
        with _open_db(self.user_db_path(username)) as conn:
            cur = conn.execute(
                "DELETE FROM topologies WHERE id = ? AND domain_id = ?",
                (topology_id, domain_id),
            )
            # Purge event history for the now-gone file. We rely on the
            # pre-delete broadcast (emitted by the caller) so UIs get one
            # last "deleted by <X>" signal before the log disappears.
            conn.execute(
                "DELETE FROM topology_events WHERE domain_id = ? AND topology_id = ?",
                (domain_id, topology_id),
            )
            conn.commit()
            deleted = (cur.rowcount or 0) > 0
        # Cascade: drop any per-file share rows that pointed at this file.
        composite = self._topology_composite(username, domain_id, topology_id)
        with _open_db(USERS_DB_PATH) as central:
            central.execute("DELETE FROM topology_shares WHERE composite_id = ?", (composite,))
            central.execute("DELETE FROM shared_topologies WHERE composite_id = ?", (composite,))
            central.commit()
        return {
            "deleted": deleted,
            "owner": username,
            "domain_id": domain_id,
            "topology_id": topology_id,
            "name": topo_name,
            "recipients": recipients,
            "actor_user": actor,
            "actor_display_name": actor_display_name,
            "event_type": "topology.deleted",
            "event_summary": f"Deleted '{topo_name}'",
            "event_details": {"name": topo_name},
        }

    def list_topology_recipients(
        self, owner: str, domain_id: str, topology_id: str,
    ) -> List[str]:
        """Usernames with ANY share permission on (owner, domain_id,
        topology_id). Used by the SSE broadcaster to decide which open
        client tabs to ping on mirror-save / rename / delete."""
        with _open_db(USERS_DB_PATH) as central:
            row = central.execute(
                "SELECT composite_id FROM shared_topologies "
                "WHERE owner = ? AND domain_id = ? AND topology_id = ?",
                (owner, domain_id, topology_id),
            ).fetchone()
            if not row:
                return []
            rs = central.execute(
                "SELECT username FROM topology_shares WHERE composite_id = ?",
                (row["composite_id"],),
            ).fetchall()
            return [r["username"] for r in rs]

    def get_topology_meta(
        self, username: str, domain_id: str, topology_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Cheap {id, name, updated_at, ...} lookup without the full topology
        JSON payload. Used by the stale-save guard so we can compare the
        mirror row's `updated_at` against the owner's legacy disk mtime in
        O(1) instead of loading the entire JSON blob.

        Also returns collaboration metadata used by the legacy
        `/api/sections/<sid>/save` stale-save guard:

        * `last_actor` / `last_actor_display_name` / `last_event_at` from the
          topology event log, so the UI can explain who last wrote.
        * per-file and per-domain share counts, split by write permission, so
          owner-only mirror rows do not trip false-positive 409s.
        """
        if domain_id == SHARED_WITH_ME_DOMAIN_ID:
            return None
        self._ensure_user_db(username)
        with _open_db(self.user_db_path(username)) as conn:
            row = conn.execute(
                "SELECT id, domain_id, name, created_at, updated_at, "
                "object_count, device_count, link_count "
                "FROM topologies WHERE id = ? AND domain_id = ?",
                (topology_id, domain_id),
            ).fetchone()
            if not row:
                return None
            meta = dict(row)
            last_evt = conn.execute(
                "SELECT actor_user, actor_display_name, event_type, summary, created_at "
                "FROM topology_events "
                "WHERE domain_id = ? AND topology_id = ? "
                "  AND event_type IN ('topology.saved', 'topology.created') "
                "ORDER BY id DESC LIMIT 1",
                (domain_id, topology_id),
            ).fetchone()
            if last_evt:
                meta["last_actor"] = last_evt["actor_user"] or ""
                meta["last_actor_display_name"] = (
                    last_evt["actor_display_name"] or last_evt["actor_user"] or ""
                )
                meta["last_event_type"] = last_evt["event_type"] or ""
                meta["last_event_summary"] = last_evt["summary"] or ""
                meta["last_event_at"] = last_evt["created_at"] or ""
            else:
                meta["last_actor"] = ""
                meta["last_actor_display_name"] = ""
                meta["last_event_type"] = ""
                meta["last_event_summary"] = ""
                meta["last_event_at"] = ""

        composite = self._topology_composite(username, domain_id, topology_id)
        domain_composite = f"{username}:{domain_id}"
        with _open_db(USERS_DB_PATH) as central:
            topo_counts = central.execute(
                "SELECT COUNT(*) AS total, "
                "       SUM(CASE WHEN permission = 'write' THEN 1 ELSE 0 END) AS writable "
                "FROM topology_shares WHERE composite_id = ?",
                (composite,),
            ).fetchone()
            domain_counts = central.execute(
                "SELECT COUNT(*) AS total, "
                "       SUM(CASE WHEN permission = 'write' THEN 1 ELSE 0 END) AS writable "
                "FROM domain_shares WHERE domain_id = ?",
                (domain_composite,),
            ).fetchone()

        topology_share_count = int(topo_counts["total"] or 0) if topo_counts else 0
        topology_write_share_count = int(topo_counts["writable"] or 0) if topo_counts else 0
        domain_share_count = int(domain_counts["total"] or 0) if domain_counts else 0
        domain_write_share_count = int(domain_counts["writable"] or 0) if domain_counts else 0
        meta["topology_share_count"] = topology_share_count
        meta["topology_write_share_count"] = topology_write_share_count
        meta["domain_share_count"] = domain_share_count
        meta["domain_write_share_count"] = domain_write_share_count
        meta["share_recipient_count"] = topology_share_count + domain_share_count
        meta["write_share_recipient_count"] = (
            topology_write_share_count + domain_write_share_count
        )
        return meta

    def rename_topology(
        self,
        username: str,
        domain_id: str,
        topology_id: str,
        new_name: str,
        actor: Optional[str] = None,
        actor_display_name: Optional[str] = None,
    ) -> bool:
        # Shared-with-me rows can't be renamed from the recipient side.
        if domain_id == SHARED_WITH_ME_DOMAIN_ID:
            return False
        if not new_name or not str(new_name).strip():
            return False
        clean = str(new_name).strip()
        now = _now_iso()
        actor = actor or username
        actor_display_name = actor_display_name or actor
        self._ensure_user_db(username)
        with _open_db(self.user_db_path(username)) as conn:
            prev = conn.execute(
                "SELECT name FROM topologies WHERE id = ? AND domain_id = ?",
                (topology_id, domain_id),
            ).fetchone()
            cursor = conn.execute(
                "UPDATE topologies SET name = ?, updated_at = ? "
                "WHERE id = ? AND domain_id = ?",
                (clean, now, topology_id, domain_id),
            )
            conn.execute(
                "UPDATE domains SET updated_at = ? WHERE id = ?", (now, domain_id),
            )
            if prev and cursor.rowcount > 0 and (prev["name"] or "") != clean:
                self.record_topology_event(
                    owner=username,
                    domain_id=domain_id,
                    topology_id=topology_id,
                    actor_user=actor,
                    actor_display_name=actor_display_name,
                    event_type="topology.renamed",
                    summary=f"Renamed '{prev['name']}' -> '{clean}'",
                    details={"from": prev["name"], "to": clean},
                    conn=conn,
                )
            conn.commit()
            return cursor.rowcount > 0

    # -- Per-topology activity log -------------------------------------------
    #
    # The UI's "Logs" panel reads this via
    # ``GET /api/domains/{domain_id}/topologies/{topology_id}/events`` and
    # shows a searchable, per-topology audit trail covering saves, renames,
    # share grants/revokes, deletes, domain ops that touch the topology,
    # and client-side micro-ops flushed at save time.
    #
    # Storage lives in the OWNER's per-user DB. Recipients of a per-file
    # share read it via the composite id; visibility = "all recipients see
    # the full log" (transparent collaboration). Pruned to the most recent
    # MAX_TOPO_EVENTS rows per (domain, topology) so growth is bounded
    # regardless of how chatty the canvas is.

    _MAX_TOPO_EVENTS = 500

    def record_topology_event(
        self,
        owner: str,
        domain_id: str,
        topology_id: str,
        actor_user: str,
        actor_display_name: str,
        event_type: str,
        summary: str,
        details: Optional[Dict[str, Any]] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Dict[str, Any]:
        """Persist one event row and return the inserted record.

        ``conn`` is an optional, already-open connection to the owner's
        DB. Passing it lets callers batch the event write inside the same
        transaction as the topology mutation (``save_topology`` uses this
        to avoid a second open). When omitted a fresh connection is used.
        """
        if not owner or not event_type or not summary:
            return {}
        actor_user = actor_user or owner
        actor_display_name = actor_display_name or actor_user
        details_json = json.dumps(details or {}, ensure_ascii=False)
        now = _now_iso()

        def _insert(c: sqlite3.Connection) -> int:
            cur = c.execute(
                "INSERT INTO topology_events "
                "(domain_id, topology_id, actor_user, actor_display_name, "
                " event_type, summary, details_json, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    domain_id, topology_id, actor_user, actor_display_name,
                    event_type, summary, details_json, now,
                ),
            )
            self._prune_topology_events(c, domain_id, topology_id)
            return cur.lastrowid or 0

        if conn is not None:
            event_id = _insert(conn)
        else:
            self._ensure_user_db(owner)
            with _open_db(self.user_db_path(owner)) as c:
                event_id = _insert(c)
                c.commit()

        return {
            "id": event_id,
            "domain_id": domain_id,
            "topology_id": topology_id,
            "actor_user": actor_user,
            "actor_display_name": actor_display_name,
            "event_type": event_type,
            "summary": summary,
            "details": details or {},
            "created_at": now,
        }

    def _prune_topology_events(
        self,
        conn: sqlite3.Connection,
        domain_id: str,
        topology_id: str,
        keep: Optional[int] = None,
    ) -> int:
        """Drop oldest rows beyond the retention ceiling. Returns deleted count."""
        keep = int(keep or self._MAX_TOPO_EVENTS)
        # Two-step so the DELETE uses the index without a subquery scan.
        cutoff = conn.execute(
            "SELECT id FROM topology_events "
            "WHERE domain_id = ? AND topology_id = ? "
            "ORDER BY id DESC LIMIT 1 OFFSET ?",
            (domain_id, topology_id, keep),
        ).fetchone()
        if not cutoff:
            return 0
        cur = conn.execute(
            "DELETE FROM topology_events "
            "WHERE domain_id = ? AND topology_id = ? AND id <= ?",
            (domain_id, topology_id, cutoff[0] if isinstance(cutoff, tuple) else cutoff["id"]),
        )
        return cur.rowcount or 0

    def list_topology_events(
        self,
        owner: str,
        domain_id: str,
        topology_id: str,
        limit: int = 200,
        offset: int = 0,
        q: Optional[str] = None,
        actor: Optional[str] = None,
        event_type: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return a filtered, paginated slice of the event log.

        ``q`` is matched case-insensitively against summary + details_json
        + actor_display_name + actor_user (so 'alice' matches events by
        Alice and 'ncp-3' matches events that renamed a device to NCP-3).
        ``since`` / ``until`` are ISO 8601 strings compared lexicographically
        (safe because we only ever write UTC isoformat).
        """
        limit = max(1, min(int(limit or 200), 1000))
        offset = max(0, int(offset or 0))
        if not owner:
            return {"items": [], "total": 0, "has_more": False,
                    "limit": limit, "offset": offset, "actors": [], "types": []}

        where = ["domain_id = ?", "topology_id = ?"]
        params: List[Any] = [domain_id, topology_id]
        if actor:
            where.append("actor_user = ?")
            params.append(actor)
        if event_type:
            where.append("event_type = ?")
            params.append(event_type)
        if since:
            where.append("created_at >= ?")
            params.append(since)
        if until:
            where.append("created_at <= ?")
            params.append(until)
        if q:
            where.append(
                "(LOWER(summary) LIKE ? OR LOWER(details_json) LIKE ? "
                "OR LOWER(actor_display_name) LIKE ? OR LOWER(actor_user) LIKE ? "
                "OR LOWER(event_type) LIKE ?)"
            )
            like = "%" + str(q).lower() + "%"
            params.extend([like, like, like, like, like])
        where_sql = " AND ".join(where)

        self._ensure_user_db(owner)
        with _open_db(self.user_db_path(owner)) as conn:
            total = conn.execute(
                f"SELECT COUNT(*) AS c FROM topology_events WHERE {where_sql}",
                params,
            ).fetchone()["c"]

            rows = conn.execute(
                f"SELECT * FROM topology_events WHERE {where_sql} "
                f"ORDER BY id DESC LIMIT ? OFFSET ?",
                params + [limit, offset],
            ).fetchall()

            actors = [dict(r) for r in conn.execute(
                "SELECT actor_user, actor_display_name, COUNT(*) AS event_count "
                "FROM topology_events WHERE domain_id = ? AND topology_id = ? "
                "GROUP BY actor_user, actor_display_name "
                "ORDER BY event_count DESC",
                (domain_id, topology_id),
            ).fetchall()]

            types = [r["event_type"] for r in conn.execute(
                "SELECT DISTINCT event_type FROM topology_events "
                "WHERE domain_id = ? AND topology_id = ? ORDER BY event_type",
                (domain_id, topology_id),
            ).fetchall()]

        items = []
        for r in rows:
            d = dict(r)
            try:
                d["details"] = json.loads(d.pop("details_json") or "{}")
            except Exception:
                d["details"] = {}
            items.append(d)

        return {
            "items": items,
            "total": int(total or 0),
            "has_more": (offset + len(items)) < int(total or 0),
            "limit": limit,
            "offset": offset,
            "actors": actors,
            "types": types,
        }

    def delete_topology_events(
        self, owner: str, domain_id: str, topology_id: str,
    ) -> int:
        """Purge every event row for one topology (called on topology delete)."""
        if not owner:
            return 0
        self._ensure_user_db(owner)
        with _open_db(self.user_db_path(owner)) as conn:
            cur = conn.execute(
                "DELETE FROM topology_events WHERE domain_id = ? AND topology_id = ?",
                (domain_id, topology_id),
            )
            conn.commit()
            return cur.rowcount or 0

    # -- Domain Knowledge -----------------------------------------------------
    #
    # The per-domain "workspace" -- attached feature branches (Jenkins),
    # Jira EPICs, test-suite links, device rosters, notes, CLI presets, etc.
    # The kind registry + payload schemas live in `api/domains/knowledge.py`.
    #
    # Visibility model recap (see `_ensure_user_db` for the schema):
    #   * 'public'  rows live in the OWNER's DB. They travel with a domain
    #               share: recipients can READ them always, WRITE them only
    #               if their share permission is 'write'.
    #   * 'private' rows live in the VIEWER's DB. They never travel. For a
    #               shared-in domain the row's `domain_id` column stores the
    #               composite "<owner>:<original_id>" so the viewer's private
    #               notes on someone else's domain can't collide with a
    #               same-id domain in the viewer's own workspace.
    #
    # Callers should NOT hand-roll these paths -- always go through
    # `resolve_domain_scope` below which encapsulates owner vs. shared logic.

    def resolve_domain_scope(
        self, viewer: str, domain_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Resolve where to read/write knowledge rows for (viewer, domain_id).

        Returns None when the viewer has no access, otherwise a dict with:

            owner            : username of the domain's owner
            is_own           : viewer == owner
            is_shared_in     : domain is shared INTO the viewer's workspace
            permission       : 'write' (for owner or write-share), 'read', or None
            public_db_user   : whose DB stores the public rows (always owner)
            public_domain_id : how `domain_id` is keyed in the public table
                               (= owner-local raw id)
            private_db_user  : whose DB stores viewer's private rows (= viewer)
            private_domain_id: how `domain_id` is keyed in the private table
                               (= raw id for own domains, composite for shared-in)
            can_write_public : True iff viewer can mutate public rows
            can_write_private: True (always, as long as viewer has any access)

        The synthetic "__shared_with_me" inbox is rejected (returns None) -- it
        has no single domain and does not hold knowledge.
        """
        if not viewer or not domain_id or domain_id == SHARED_WITH_ME_DOMAIN_ID:
            return None

        # Fast path: viewer's own domain.
        self._ensure_user_db(viewer)
        with _open_db(self.user_db_path(viewer)) as conn:
            own = conn.execute(
                "SELECT id FROM domains WHERE id = ?", (domain_id,),
            ).fetchone()
        if own:
            return {
                "owner": viewer,
                "is_own": True,
                "is_shared_in": False,
                "permission": "write",
                "public_db_user": viewer,
                "public_domain_id": domain_id,
                "private_db_user": viewer,
                "private_domain_id": domain_id,
                "can_write_public": True,
                "can_write_private": True,
            }

        # Shared-in path: look for a domain_shares row where username=viewer and
        # the composite owner:domain_id matches one of our candidate owners.
        with _open_db(USERS_DB_PATH) as central:
            rows = central.execute(
                "SELECT sd.domain_id AS composite, sd.owner, ds.permission "
                "FROM shared_domains sd "
                "JOIN domain_shares ds ON ds.domain_id = sd.domain_id "
                "WHERE ds.username = ?",
                (viewer,),
            ).fetchall()
        for r in rows:
            composite = r["composite"]
            parts = composite.split(":", 1)
            original = parts[1] if len(parts) > 1 else composite
            if original != domain_id:
                continue
            owner = r["owner"] or (parts[0] if len(parts) > 1 else viewer)
            permission = r["permission"] or "read"
            return {
                "owner": owner,
                "is_own": False,
                "is_shared_in": True,
                "permission": permission,
                "public_db_user": owner,
                "public_domain_id": original,
                "private_db_user": viewer,
                "private_domain_id": composite,
                "can_write_public": permission == "write",
                "can_write_private": True,
            }
        return None

    def list_domain_knowledge(
        self, viewer: str, domain_id: str,
    ) -> List[Dict[str, Any]]:
        """Return the merged (public + private) knowledge list for a domain.

        Each row is decorated with `visibility`, `scope_is_mine` (True if the
        viewer owns the row), `editable` (True if viewer can update it), and
        `payload` (parsed JSON). Sort order:
          1. pinned rows first
          2. then by sort_order ascending
          3. then by updated_at descending
        """
        scope = self.resolve_domain_scope(viewer, domain_id)
        if not scope:
            return []
        out: List[Dict[str, Any]] = []

        # -- public rows from the owner's DB ----------------------------------
        self._ensure_user_db(scope["public_db_user"])
        with _open_db(self.user_db_path(scope["public_db_user"])) as conn:
            for r in conn.execute(
                "SELECT domain_id, visibility, kind, key, payload, pinned, "
                "       sort_order, created_at, updated_at "
                "FROM domain_knowledge "
                "WHERE domain_id = ? AND visibility = 'public'",
                (scope["public_domain_id"],),
            ).fetchall():
                row = dict(r)
                try:
                    row["payload"] = json.loads(row["payload"]) if row["payload"] else {}
                except Exception:
                    row["payload"] = {}
                row["scope_is_mine"] = scope["is_own"]
                row["editable"] = scope["can_write_public"]
                row["author"] = scope["owner"]
                out.append(row)

        # -- private rows from the viewer's DB --------------------------------
        self._ensure_user_db(scope["private_db_user"])
        with _open_db(self.user_db_path(scope["private_db_user"])) as conn:
            for r in conn.execute(
                "SELECT domain_id, visibility, kind, key, payload, pinned, "
                "       sort_order, created_at, updated_at "
                "FROM domain_knowledge "
                "WHERE domain_id = ? AND visibility = 'private'",
                (scope["private_domain_id"],),
            ).fetchall():
                row = dict(r)
                try:
                    row["payload"] = json.loads(row["payload"]) if row["payload"] else {}
                except Exception:
                    row["payload"] = {}
                row["scope_is_mine"] = True
                row["editable"] = True
                row["author"] = viewer
                out.append(row)

        # Stable composite sort:
        #   1. pinned rows first (0 before 1)
        #   2. then by sort_order ascending
        #   3. then by updated_at DESCENDING (newest first) inside the bucket
        # ISO-8601 timestamps sort lexicographically, so for descending we
        # just negate the string by sorting on the reversed tuple flag.
        def _sort_key(x: Dict[str, Any]):
            pinned = 0 if x.get("pinned") else 1
            order = int(x.get("sort_order") or 0)
            updated = x.get("updated_at") or ""
            return (pinned, order, updated)
        # Two-pass: first by updated_at ascending, then stable-sort by
        # (pinned, sort_order) so newest surfaces when everything else is equal.
        out.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
        out.sort(key=_sort_key)
        return out

    def get_domain_knowledge_item(
        self, viewer: str, domain_id: str,
        kind: str, key: str, visibility: str = "public",
    ) -> Optional[Dict[str, Any]]:
        scope = self.resolve_domain_scope(viewer, domain_id)
        if not scope:
            return None
        visibility = "public" if visibility == "public" else "private"
        db_user = scope["public_db_user"] if visibility == "public" else scope["private_db_user"]
        row_domain = scope["public_domain_id"] if visibility == "public" else scope["private_domain_id"]
        self._ensure_user_db(db_user)
        with _open_db(self.user_db_path(db_user)) as conn:
            row = conn.execute(
                "SELECT domain_id, visibility, kind, key, payload, pinned, "
                "       sort_order, created_at, updated_at "
                "FROM domain_knowledge "
                "WHERE domain_id = ? AND visibility = ? AND kind = ? AND key = ?",
                (row_domain, visibility, kind, key),
            ).fetchone()
            if not row:
                return None
            out = dict(row)
            try:
                out["payload"] = json.loads(out["payload"]) if out["payload"] else {}
            except Exception:
                out["payload"] = {}
            out["scope_is_mine"] = (
                scope["is_own"] if visibility == "public" else True
            )
            out["editable"] = (
                scope["can_write_public"] if visibility == "public" else True
            )
            out["author"] = scope["owner"] if visibility == "public" else viewer
            return out

    def upsert_domain_knowledge(
        self, viewer: str, domain_id: str,
        kind: str, key: str, payload: Dict[str, Any],
        visibility: str = "public",
        pinned: Optional[bool] = None,
        sort_order: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Insert or update a knowledge row. Enforces the hybrid-sharing rules.

        Raises PermissionError when the viewer is trying to write a public
        row on a domain where they only have read share-permission.
        """
        if not kind or not key:
            raise ValueError("kind and key are required")
        scope = self.resolve_domain_scope(viewer, domain_id)
        if not scope:
            raise PermissionError("Domain not found or access denied")
        visibility = "public" if visibility == "public" else "private"
        if visibility == "public" and not scope["can_write_public"]:
            raise PermissionError(
                "You only have read access to this shared domain; use "
                "visibility='private' to save a personal annotation instead"
            )

        db_user = scope["public_db_user"] if visibility == "public" else scope["private_db_user"]
        row_domain = scope["public_domain_id"] if visibility == "public" else scope["private_domain_id"]
        now = _now_iso()
        payload_json = json.dumps(payload or {})
        self._ensure_user_db(db_user)
        # Atomic UPSERT via SQLite's native ON CONFLICT DO UPDATE (3.24+). The
        # previous implementation used SELECT-then-INSERT-or-UPDATE which is
        # a classic TOCTOU race: two simultaneous writers to the same
        # (domain, visibility, kind, key) both saw an empty SELECT, both
        # tried INSERT, and one hit a UNIQUE constraint violation. That
        # surfaced as a 500 in the REST layer and a lost write.
        #
        # With ON CONFLICT DO UPDATE the operation is atomic at the SQLite
        # page level; losers simply merge into the winner's row instead of
        # erroring.
        #
        # ``pinned``/``sort_order`` are preserved when the caller passed
        # ``None`` by COALESCE'ing against the existing column values via
        # ``excluded.*``-agnostic expressions.
        pinned_to_write = None if pinned is None else int(bool(pinned))
        order_to_write = None if sort_order is None else int(sort_order)
        with _open_db(self.user_db_path(db_user)) as conn:
            conn.execute(
                "INSERT INTO domain_knowledge "
                "(domain_id, visibility, kind, key, payload, pinned, sort_order, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(domain_id, visibility, kind, key) DO UPDATE SET "
                "    payload = excluded.payload, "
                "    pinned = CASE WHEN ? IS NULL THEN domain_knowledge.pinned ELSE ? END, "
                "    sort_order = CASE WHEN ? IS NULL THEN domain_knowledge.sort_order ELSE ? END, "
                "    updated_at = excluded.updated_at",
                (
                    row_domain, visibility, kind, key, payload_json,
                    pinned_to_write if pinned_to_write is not None else 0,
                    order_to_write if order_to_write is not None else 0,
                    now, now,
                    # ON CONFLICT parameters (repeated because CASE reads them twice)
                    pinned_to_write, pinned_to_write,
                    order_to_write, order_to_write,
                ),
            )
            conn.commit()
            # Fetch the authoritative row back so we return the true
            # created_at / pinned / sort_order (whether this call was a
            # fresh insert or an update).
            row = conn.execute(
                "SELECT created_at, pinned, sort_order FROM domain_knowledge "
                "WHERE domain_id = ? AND visibility = ? AND kind = ? AND key = ?",
                (row_domain, visibility, kind, key),
            ).fetchone()
            if row:
                created_at = row["created_at"] or now
                effective_pinned = int(row["pinned"] or 0)
                effective_order = int(row["sort_order"] or 0)
            else:  # pragma: no cover -- only if another thread deleted us mid-call
                created_at = now
                effective_pinned = pinned_to_write or 0
                effective_order = order_to_write or 0

        return {
            "domain_id": row_domain,
            "visibility": visibility,
            "kind": kind,
            "key": key,
            "payload": payload or {},
            "pinned": bool(effective_pinned),
            "sort_order": effective_order,
            "created_at": created_at,
            "updated_at": now,
            "author": scope["owner"] if visibility == "public" else viewer,
            "scope_is_mine": (
                scope["is_own"] if visibility == "public" else True
            ),
            "editable": True,
        }

    def delete_domain_knowledge(
        self, viewer: str, domain_id: str,
        kind: str, key: str, visibility: str = "public",
    ) -> bool:
        scope = self.resolve_domain_scope(viewer, domain_id)
        if not scope:
            return False
        visibility = "public" if visibility == "public" else "private"
        if visibility == "public" and not scope["can_write_public"]:
            raise PermissionError("Read-only access to this shared domain")
        db_user = scope["public_db_user"] if visibility == "public" else scope["private_db_user"]
        row_domain = scope["public_domain_id"] if visibility == "public" else scope["private_domain_id"]
        self._ensure_user_db(db_user)
        with _open_db(self.user_db_path(db_user)) as conn:
            cursor = conn.execute(
                "DELETE FROM domain_knowledge "
                "WHERE domain_id = ? AND visibility = ? AND kind = ? AND key = ?",
                (row_domain, visibility, kind, key),
            )
            conn.commit()
            return cursor.rowcount > 0

    def list_all_public_knowledge_rows(
        self, kind: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Cross-user iteration used by the background poller.

        Walks every user's DB and returns all visibility='public' rows
        (optionally filtered by kind). Each row is decorated with its
        owning user so the poller can fan updates back to the right
        viewers via _domain_viewers().
        """
        out: List[Dict[str, Any]] = []
        base = Path(settings.users_base_dir).expanduser()
        if not base.is_dir():
            return out
        for entry in base.iterdir():
            if not entry.is_dir():
                continue
            db_path = entry / "topologies.db"
            if not db_path.exists():
                continue
            try:
                with _open_db(db_path) as conn:
                    # `domain_knowledge` may not exist yet for ancient users
                    # whose DB was created before we introduced it. Guard.
                    has_tbl = conn.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='domain_knowledge'"
                    ).fetchone()
                    if not has_tbl:
                        continue
                    query = (
                        "SELECT domain_id, visibility, kind, key, payload, "
                        "       pinned, sort_order, created_at, updated_at "
                        "FROM domain_knowledge WHERE visibility = 'public'"
                    )
                    params: tuple = ()
                    if kind:
                        query += " AND kind = ?"
                        params = (kind,)
                    for r in conn.execute(query, params).fetchall():
                        row = dict(r)
                        row["owner"] = entry.name
                        try:
                            row["payload"] = json.loads(row["payload"]) if row["payload"] else {}
                        except Exception:
                            row["payload"] = {}
                        out.append(row)
            except Exception:
                continue
        return out

    def update_public_knowledge_payload(
        self, owner: str, domain_id: str,
        kind: str, key: str, payload: Dict[str, Any],
    ) -> bool:
        """Server-side poller path: overwrite a public row's payload without
        touching `pinned` / `sort_order` / `created_at`. Used to refresh live
        Jenkins/Jira status. Skips permission checks because the poller owns
        this operation; routes should use `upsert_domain_knowledge` instead."""
        self._ensure_user_db(owner)
        now = _now_iso()
        with _open_db(self.user_db_path(owner)) as conn:
            cursor = conn.execute(
                "UPDATE domain_knowledge "
                "SET payload = ?, updated_at = ? "
                "WHERE domain_id = ? AND visibility = 'public' "
                "      AND kind = ? AND key = ?",
                (json.dumps(payload or {}), now, domain_id, kind, key),
            )
            conn.commit()
            return cursor.rowcount > 0

    def domain_viewers(self, owner: str, domain_id: str) -> List[str]:
        """Usernames that currently have visibility onto (owner, domain_id):
        the owner plus every recipient of a domain_shares grant. Used by the
        Jenkins/Jira poller to fan delta events through event_bus."""
        viewers = {owner}
        composite = f"{owner}:{domain_id}"
        with _open_db(USERS_DB_PATH) as central:
            rows = central.execute(
                "SELECT username FROM domain_shares WHERE domain_id = ?",
                (composite,),
            ).fetchall()
            for r in rows:
                if r["username"]:
                    viewers.add(r["username"])
        return sorted(viewers)

    def sweep_orphan_private_knowledge(
        self, owner: str, domain_id: str,
    ) -> int:
        """Delete every *private* knowledge row in any user's DB that was
        keyed against "<owner>:<domain_id>". Called when the owner deletes
        the domain so we don't leave stranded annotations from past share
        recipients. Returns the number of rows removed.

        Safe to run even if no orphans exist: it no-ops per-user.
        """
        if not owner or not domain_id:
            return 0
        composite = f"{owner}:{domain_id}"
        removed = 0
        base = Path(settings.users_base_dir).expanduser()
        if not base.is_dir():
            return 0
        for entry in base.iterdir():
            if not entry.is_dir() or entry.name == owner:
                # Owner DB already had its rows cleaned by delete_domain.
                continue
            db_path = entry / "topologies.db"
            if not db_path.exists():
                continue
            try:
                with _open_db(db_path, row_factory=False) as conn:
                    has_tbl = conn.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='domain_knowledge'"
                    ).fetchone()
                    if not has_tbl:
                        continue
                    cursor = conn.execute(
                        "DELETE FROM domain_knowledge "
                        "WHERE domain_id = ? AND visibility = 'private'",
                        (composite,),
                    )
                    removed += cursor.rowcount or 0
                    conn.commit()
            except Exception:
                # Per-user DB errors never block owner-side delete.
                continue
        return removed

    # -- Shared Domains --

    def share_domain(
        self,
        owner: str,
        domain_id: str,
        target_users: List[str],
        permission: str = "read",
        actor: Optional[str] = None,
        notes: str = "",
    ) -> bool:
        """Share a user's domain with other users via the central shared_domains table.

        Records every grant/upgrade in the share_activity audit log so the Share
        Topology dialog can show full per-user history.
        """
        self._ensure_user_db(owner)
        with _open_db(self.user_db_path(owner)) as conn:
            domain = conn.execute(
                "SELECT * FROM domains WHERE id = ?", (domain_id,),
            ).fetchone()
            if not domain:
                return False
            domain = dict(domain)

        composite = f"{owner}:{domain_id}"
        now = _now_iso()
        actor = actor or owner

        with _open_db(USERS_DB_PATH) as central:
            central.execute(
                "INSERT OR REPLACE INTO shared_domains (domain_id, name, description, owner, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (composite, domain["name"], domain["description"], owner, now, now),
            )
            for user in target_users:
                if user == owner:
                    continue
                existing = central.execute(
                    "SELECT permission FROM domain_shares WHERE domain_id = ? AND username = ?",
                    (composite, user),
                ).fetchone()
                central.execute(
                    "INSERT OR REPLACE INTO domain_shares (domain_id, username, permission, granted_at, granted_by) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (composite, user, permission, now, actor),
                )
                if existing is None:
                    action = "share"
                elif existing["permission"] != permission:
                    action = "permission_change"
                else:
                    action = "reshare"
                central.execute(
                    "INSERT INTO share_activity (ts, action, domain_id, domain_name, owner, actor, target_user, permission, notes) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (now, action, composite, domain["name"], owner, actor, user, permission, notes),
                )
            central.commit()
        return True

    def unshare_domain(
        self,
        owner: str,
        domain_id: str,
        target_user: str,
        actor: Optional[str] = None,
        notes: str = "",
    ) -> bool:
        composite = f"{owner}:{domain_id}"
        actor = actor or owner
        domain_name = ""
        self._ensure_user_db(owner)
        with _open_db(self.user_db_path(owner)) as conn:
            row = conn.execute(
                "SELECT name FROM domains WHERE id = ?", (domain_id,),
            ).fetchone()
            if row:
                domain_name = row["name"]

        with _open_db(USERS_DB_PATH) as central:
            existed = central.execute(
                "SELECT 1 FROM domain_shares WHERE domain_id = ? AND username = ?",
                (composite, target_user),
            ).fetchone()
            central.execute(
                "DELETE FROM domain_shares WHERE domain_id = ? AND username = ?",
                (composite, target_user),
            )
            if existed:
                central.execute(
                    "INSERT INTO share_activity (ts, action, domain_id, domain_name, owner, actor, target_user, permission, notes) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (_now_iso(), "unshare", composite, domain_name, owner, actor, target_user, None, notes),
                )
            remaining = central.execute(
                "SELECT COUNT(*) FROM domain_shares WHERE domain_id = ?",
                (composite,),
            ).fetchone()[0]
            if remaining == 0:
                central.execute(
                    "DELETE FROM shared_domains WHERE domain_id = ?", (composite,),
                )
            central.commit()
        return True

    def _list_shared_domains_for_user(self, username: str) -> List[Dict[str, Any]]:
        with _open_db(USERS_DB_PATH) as central:
            rows = central.execute(
                "SELECT sd.*, ds.permission, ds.granted_at, ds.granted_by FROM shared_domains sd "
                "JOIN domain_shares ds ON sd.domain_id = ds.domain_id "
                "WHERE ds.username = ? ORDER BY sd.name",
                (username,),
            ).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                parts = d["domain_id"].split(":", 1)
                owner = parts[0] if len(parts) > 1 else d.get("owner") or ""
                original = parts[1] if len(parts) > 1 else d["domain_id"]
                # ``shared_domains`` stores the composite key ``<owner>:<id>``
                # as its primary key (column name ``domain_id``). The router +
                # Pydantic schema + frontend all expect an ``id`` field that
                # matches what ``_resolve_domain_access`` + ``_domain_owner``
                # can then bounce back to the owner's DB. So we publish the
                # ORIGINAL (owner-local) domain id here; ``owner`` on the dict
                # carries the attribution so URL handlers can route to the
                # right user's topologies DB. Prior to this, ``id`` was never
                # set and the schema built TopologyDomainInfo(id=d["id"]) which
                # raised KeyError -> 500 on /api/domains for any recipient
                # with an inbound domain share.
                d["id"] = original
                d["owner"] = owner
                d["original_domain_id"] = original
                d["is_shared"] = True
                d["shared_with"] = [username]
                d["topology_count"] = self._owner_domain_topology_count(owner, original)
                result.append(d)
            return result

    def _owner_domain_topology_count(self, owner: str, domain_id: str) -> int:
        try:
            self._ensure_user_db(owner)
            with _open_db(self.user_db_path(owner)) as conn:
                row = conn.execute(
                    "SELECT COUNT(*) FROM topologies WHERE domain_id = ?",
                    (domain_id,),
                ).fetchone()
                return row[0] if row else 0
        except Exception:
            return 0

    # -- Sharing Observability --

    def list_domain_shares(self, owner: str, domain_id: str) -> List[Dict[str, Any]]:
        """All users a given owner-domain is currently shared with."""
        composite = f"{owner}:{domain_id}"
        with _open_db(USERS_DB_PATH) as central:
            rows = central.execute(
                "SELECT ds.username, ds.permission, ds.granted_at, ds.granted_by, "
                "       u.display_name, u.role "
                "FROM domain_shares ds "
                "LEFT JOIN users u ON u.username = ds.username "
                "WHERE ds.domain_id = ? "
                "ORDER BY ds.granted_at DESC",
                (composite,),
            ).fetchall()
            return [dict(r) for r in rows]

    def list_outgoing_shares(self, owner: str) -> List[Dict[str, Any]]:
        """Every domain THIS user owns that is shared, with all recipients."""
        self._ensure_user_db(owner)
        with _open_db(self.user_db_path(owner)) as conn:
            own = {
                r["id"]: dict(r)
                for r in conn.execute(
                    "SELECT id, name, description, created_at, updated_at, "
                    "       (SELECT COUNT(*) FROM topologies t WHERE t.domain_id = d.id) AS topology_count "
                    "FROM domains d"
                ).fetchall()
            }

        result: List[Dict[str, Any]] = []
        with _open_db(USERS_DB_PATH) as central:
            sd_rows = central.execute(
                "SELECT sd.*, "
                "       (SELECT COUNT(*) FROM domain_shares ds WHERE ds.domain_id = sd.domain_id) AS recipient_count "
                "FROM shared_domains sd WHERE sd.owner = ? ORDER BY sd.name",
                (owner,),
            ).fetchall()
            for sd in sd_rows:
                d = dict(sd)
                parts = d["domain_id"].split(":", 1)
                original_id = parts[1] if len(parts) > 1 else d["domain_id"]
                local = own.get(original_id, {})
                recipients = central.execute(
                    "SELECT ds.username, ds.permission, ds.granted_at, ds.granted_by, "
                    "       u.display_name, u.role "
                    "FROM domain_shares ds LEFT JOIN users u ON u.username = ds.username "
                    "WHERE ds.domain_id = ? ORDER BY ds.granted_at DESC",
                    (d["domain_id"],),
                ).fetchall()
                topo_rows = []
                if local:
                    topo_rows = [
                        dict(t) for t in self._owner_topologies(owner, original_id)
                    ]
                result.append({
                    "domain_id": original_id,
                    "composite_id": d["domain_id"],
                    "name": local.get("name", d["name"]),
                    "description": local.get("description", d.get("description", "")),
                    "owner": owner,
                    "created_at": local.get("created_at", d["created_at"]),
                    "updated_at": local.get("updated_at", d["updated_at"]),
                    "topology_count": local.get("topology_count", 0),
                    "recipient_count": d["recipient_count"],
                    "recipients": [dict(r) for r in recipients],
                    "topologies": topo_rows,
                })
        return result

    def list_incoming_shares(self, username: str) -> List[Dict[str, Any]]:
        """Every domain shared WITH this user (read-only-style observability)."""
        with _open_db(USERS_DB_PATH) as central:
            rows = central.execute(
                "SELECT sd.*, ds.permission, ds.granted_at, ds.granted_by, "
                "       u.display_name AS owner_display_name, u.role AS owner_role "
                "FROM shared_domains sd "
                "JOIN domain_shares ds ON ds.domain_id = sd.domain_id "
                "LEFT JOIN users u ON u.username = sd.owner "
                "WHERE ds.username = ? ORDER BY ds.granted_at DESC",
                (username,),
            ).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                parts = d["domain_id"].split(":", 1)
                original_id = parts[1] if len(parts) > 1 else d["domain_id"]
                topo_rows = [
                    {k: v for k, v in dict(t).items() if k != "data"}
                    for t in self._owner_topologies(d["owner"], original_id)
                ]
                d["original_domain_id"] = original_id
                d["topologies"] = topo_rows
                d["topology_count"] = len(topo_rows)
                result.append(d)
            return result

    def _owner_topologies(self, owner: str, domain_id: str) -> List[sqlite3.Row]:
        try:
            self._ensure_user_db(owner)
            with _open_db(self.user_db_path(owner)) as conn:
                return conn.execute(
                    "SELECT id, domain_id, name, created_at, updated_at, "
                    "       object_count, device_count, link_count "
                    "FROM topologies WHERE domain_id = ? ORDER BY updated_at DESC",
                    (domain_id,),
                ).fetchall()
        except Exception:
            return []

    # -- Per-file (per-topology) sharing -----------------------------------
    #
    # Mirrors the per-domain sharing API but at file granularity. Every grant
    # is written to the central users DB so the synthetic "__shared_with_me"
    # domain can resolve recipients quickly without scanning per-user DBs.
    # ----------------------------------------------------------------------

    @staticmethod
    def _topology_composite(owner: str, domain_id: str, topology_id: str) -> str:
        return f"{owner}:{domain_id}:{topology_id}"

    @staticmethod
    def _split_topology_composite(composite: str) -> Optional[tuple]:
        """Inverse of _topology_composite. Returns (owner, domain_id, topology_id) or None."""
        parts = (composite or "").split(":", 2)
        if len(parts) != 3 or not all(parts):
            return None
        return (parts[0], parts[1], parts[2])

    def _topology_meta(self, owner: str, domain_id: str, topology_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single topology row (without data) from the owner's DB."""
        try:
            self._ensure_user_db(owner)
            with _open_db(self.user_db_path(owner)) as conn:
                row = conn.execute(
                    "SELECT id, domain_id, name, created_at, updated_at, "
                    "       object_count, device_count, link_count "
                    "FROM topologies WHERE id = ? AND domain_id = ?",
                    (topology_id, domain_id),
                ).fetchone()
                return dict(row) if row else None
        except Exception:
            return None

    def _domain_name(self, owner: str, domain_id: str) -> Optional[str]:
        """Fetch the human-readable name of an owner's domain (used when surfacing
        per-file shares so the recipient sees 'in My Topologies' instead of the
        raw uuid). Returns None if the domain no longer exists."""
        try:
            self._ensure_user_db(owner)
            with _open_db(self.user_db_path(owner)) as conn:
                row = conn.execute(
                    "SELECT name FROM domains WHERE id = ?", (domain_id,),
                ).fetchone()
                return row["name"] if row else None
        except Exception:
            return None

    def share_topology(
        self,
        owner: str,
        domain_id: str,
        topology_id: str,
        target_users: List[str],
        permission: str = "read",
        actor: Optional[str] = None,
        actor_display_name: Optional[str] = None,
        notes: str = "",
    ) -> Dict[str, Any]:
        """Share a single topology file with one or more users.

        Refuses synthetic / non-owned domains. Records every grant in the
        share_activity audit log AND in the per-topology event log so the
        UI can display a unified timeline. Returns a dict ``{ok, added,
        changed, unchanged, recipients, owner, name}`` so the router can
        broadcast the change to every newly-added / permission-changed
        recipient (so their "Shared with me" list refreshes live).
        """
        if domain_id == SHARED_WITH_ME_DOMAIN_ID:
            return {"ok": False, "reason": "synthetic_domain"}
        meta = self._topology_meta(owner, domain_id, topology_id)
        if not meta:
            return {"ok": False, "reason": "not_found"}
        composite = self._topology_composite(owner, domain_id, topology_id)
        now = _now_iso()
        actor = actor or owner
        actor_display_name = actor_display_name or actor
        added: List[str] = []
        changed: List[Dict[str, str]] = []
        unchanged: List[str] = []
        all_recipients: List[str] = []

        with _open_db(USERS_DB_PATH) as central:
            central.execute(
                "INSERT OR REPLACE INTO shared_topologies "
                "(composite_id, name, owner, domain_id, topology_id, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (composite, meta["name"], owner, domain_id, topology_id, now, now),
            )
            for user in target_users:
                if not user or user == owner:
                    continue
                existing = central.execute(
                    "SELECT permission FROM topology_shares WHERE composite_id = ? AND username = ?",
                    (composite, user),
                ).fetchone()
                central.execute(
                    "INSERT OR REPLACE INTO topology_shares "
                    "(composite_id, username, permission, granted_at, granted_by) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (composite, user, permission, now, actor),
                )
                if existing is None:
                    action = "share_topology"
                    added.append(user)
                elif existing["permission"] != permission:
                    action = "permission_change_topology"
                    changed.append({
                        "user": user,
                        "from": existing["permission"],
                        "to": permission,
                    })
                else:
                    action = "reshare_topology"
                    unchanged.append(user)
                # Reuse share_activity table -- the synthetic "domain_id"
                # carries the topology composite so audits are still queryable
                central.execute(
                    "INSERT INTO share_activity "
                    "(ts, action, domain_id, domain_name, owner, actor, target_user, permission, notes) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (now, action, composite, meta["name"], owner, actor, user, permission, notes),
                )
            all_recipients = [r["username"] for r in central.execute(
                "SELECT username FROM topology_shares WHERE composite_id = ?",
                (composite,),
            ).fetchall()]
            central.commit()

        # Per-topology event log entries -- one per distinct action so the
        # Logs panel can render them as separate rows.
        self._ensure_user_db(owner)
        with _open_db(self.user_db_path(owner)) as conn:
            if added:
                self.record_topology_event(
                    owner=owner, domain_id=domain_id, topology_id=topology_id,
                    actor_user=actor, actor_display_name=actor_display_name,
                    event_type="topology.shared",
                    summary=(
                        f"Shared with {added[0]}"
                        + (f" (+{len(added) - 1} more)" if len(added) > 1 else "")
                        + f" [{permission}]"
                    ),
                    details={"added": added, "permission": permission, "notes": notes},
                    conn=conn,
                )
            for ch in changed:
                self.record_topology_event(
                    owner=owner, domain_id=domain_id, topology_id=topology_id,
                    actor_user=actor, actor_display_name=actor_display_name,
                    event_type="topology.permission_changed",
                    summary=(
                        f"Changed {ch['user']} permission "
                        f"{ch['from']} -> {ch['to']}"
                    ),
                    details=ch,
                    conn=conn,
                )
            conn.commit()

        return {
            "ok": True,
            "added": added,
            "changed": changed,
            "unchanged": unchanged,
            "recipients": all_recipients,
            "owner": owner,
            "domain_id": domain_id,
            "topology_id": topology_id,
            "name": meta["name"],
            "permission": permission,
        }

    def unshare_topology(
        self,
        owner: str,
        domain_id: str,
        topology_id: str,
        target_user: str,
        actor: Optional[str] = None,
        actor_display_name: Optional[str] = None,
        notes: str = "",
    ) -> Dict[str, Any]:
        if domain_id == SHARED_WITH_ME_DOMAIN_ID:
            return {"ok": False, "reason": "synthetic_domain"}
        composite = self._topology_composite(owner, domain_id, topology_id)
        actor = actor or owner
        actor_display_name = actor_display_name or actor
        meta = self._topology_meta(owner, domain_id, topology_id)
        topo_name = meta["name"] if meta else topology_id
        did_remove = False

        with _open_db(USERS_DB_PATH) as central:
            existed = central.execute(
                "SELECT 1 FROM topology_shares WHERE composite_id = ? AND username = ?",
                (composite, target_user),
            ).fetchone()
            central.execute(
                "DELETE FROM topology_shares WHERE composite_id = ? AND username = ?",
                (composite, target_user),
            )
            if existed:
                did_remove = True
                central.execute(
                    "INSERT INTO share_activity "
                    "(ts, action, domain_id, domain_name, owner, actor, target_user, permission, notes) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (_now_iso(), "unshare_topology", composite, topo_name, owner, actor, target_user, None, notes),
                )
            remaining = central.execute(
                "SELECT COUNT(*) FROM topology_shares WHERE composite_id = ?",
                (composite,),
            ).fetchone()[0]
            if remaining == 0:
                central.execute(
                    "DELETE FROM shared_topologies WHERE composite_id = ?", (composite,),
                )
            central.commit()

        if did_remove:
            self.record_topology_event(
                owner=owner, domain_id=domain_id, topology_id=topology_id,
                actor_user=actor, actor_display_name=actor_display_name,
                event_type="topology.unshared",
                summary=f"Revoked access for {target_user}",
                details={"target_user": target_user, "notes": notes},
            )
        return {
            "ok": True,
            "removed": did_remove,
            "owner": owner,
            "domain_id": domain_id,
            "topology_id": topology_id,
            "name": topo_name,
            "target_user": target_user,
            "actor_user": actor,
            "actor_display_name": actor_display_name,
        }

    # -------------------------------------------------------------------
    # Recipient-side self-removal
    # -------------------------------------------------------------------
    # Pair to `unshare_*`, but callable by the TARGET user. Lets a
    # recipient prune a share row from their own "Shared with me" view
    # WITHOUT affecting the owner's copy or any other recipient. The
    # owner can always re-share if they want the recipient back.
    #
    # The central tables we touch:
    #   - `topology_shares (composite_id, username, ...)` for per-file
    #   - `domain_shares   (domain_id,    username, ...)` for per-domain
    # Both are cascade-safe: dropping a row here leaves the upstream
    # `shared_topologies` / `shared_domains` entry intact so other
    # grants keep working.
    # -------------------------------------------------------------------

    def remove_own_incoming_topology_share(
        self, username: str, composite_id: str, notes: str = "",
    ) -> Dict[str, Any]:
        """Recipient removes one per-file share from THEIR incoming list.

        Returns {"removed": True, "composite_id": ...} on success.
        If no matching row exists, returns {"removed": False} with the
        same composite id so callers can 200-ok idempotently without
        panicking about stale UI rows.
        """
        if not composite_id:
            return {"removed": False, "composite_id": composite_id}
        with _open_db(USERS_DB_PATH) as central:
            row = central.execute(
                "SELECT st.owner, st.name "
                "FROM topology_shares ts "
                "JOIN shared_topologies st ON st.composite_id = ts.composite_id "
                "WHERE ts.composite_id = ? AND ts.username = ?",
                (composite_id, username),
            ).fetchone()
            if not row:
                return {"removed": False, "composite_id": composite_id}
            owner = row["owner"]
            topo_name = row["name"]
            central.execute(
                "DELETE FROM topology_shares WHERE composite_id = ? AND username = ?",
                (composite_id, username),
            )
            # Audit trail: `actor = target = username` so the owner can
            # see "alice removed her own access" in share activity.
            central.execute(
                "INSERT INTO share_activity "
                "(ts, action, domain_id, domain_name, owner, actor, target_user, permission, notes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    _now_iso(), "remove_own_topology_share", composite_id,
                    topo_name, owner, username, username, None, notes,
                ),
            )
            # If no other recipient remains AND the owner has no
            # intent to keep the "shared" row around, we leave the
            # `shared_topologies` parent alone -- the owner may re-share
            # later. This matches how owner-side unshare_topology only
            # reaps the parent when every share is gone.
            central.commit()
        return {"removed": True, "composite_id": composite_id, "owner": owner}

    def remove_own_incoming_domain_share(
        self, username: str, domain_id: str, notes: str = "",
    ) -> Dict[str, Any]:
        """Recipient removes one whole domain share from their inbox.

        `domain_id` is the composite `<owner>:<original_domain_id>` that
        list_incoming_shares returns. Dropping this row hides every file
        in that domain from the recipient's dropdown without affecting
        the owner or any other target user.
        """
        if not domain_id:
            return {"removed": False, "domain_id": domain_id}
        with _open_db(USERS_DB_PATH) as central:
            row = central.execute(
                "SELECT sd.owner, sd.name "
                "FROM domain_shares ds "
                "JOIN shared_domains sd ON sd.domain_id = ds.domain_id "
                "WHERE ds.domain_id = ? AND ds.username = ?",
                (domain_id, username),
            ).fetchone()
            if not row:
                return {"removed": False, "domain_id": domain_id}
            owner = row["owner"]
            domain_name = row["name"]
            central.execute(
                "DELETE FROM domain_shares WHERE domain_id = ? AND username = ?",
                (domain_id, username),
            )
            central.execute(
                "INSERT INTO share_activity "
                "(ts, action, domain_id, domain_name, owner, actor, target_user, permission, notes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    _now_iso(), "remove_own_domain_share", domain_id,
                    domain_name, owner, username, username, None, notes,
                ),
            )
            central.commit()
        return {"removed": True, "domain_id": domain_id, "owner": owner}

    def list_topology_shares(self, owner: str, domain_id: str, topology_id: str) -> List[Dict[str, Any]]:
        composite = self._topology_composite(owner, domain_id, topology_id)
        with _open_db(USERS_DB_PATH) as central:
            rows = central.execute(
                "SELECT ts.username, ts.permission, ts.granted_at, ts.granted_by, "
                "       u.display_name, u.role "
                "FROM topology_shares ts "
                "LEFT JOIN users u ON u.username = ts.username "
                "WHERE ts.composite_id = ? "
                "ORDER BY ts.granted_at DESC",
                (composite,),
            ).fetchall()
            return [dict(r) for r in rows]

    def list_outgoing_topology_shares(self, owner: str) -> List[Dict[str, Any]]:
        """Every per-file share THIS user has handed out, with all recipients."""
        with _open_db(USERS_DB_PATH) as central:
            sd_rows = central.execute(
                "SELECT st.*, "
                "       (SELECT COUNT(*) FROM topology_shares ts WHERE ts.composite_id = st.composite_id) AS recipient_count "
                "FROM shared_topologies st WHERE st.owner = ? ORDER BY st.name",
                (owner,),
            ).fetchall()
            result: List[Dict[str, Any]] = []
            for sd in sd_rows:
                d = dict(sd)
                meta = self._topology_meta(owner, d["domain_id"], d["topology_id"]) or {}
                recipients = central.execute(
                    "SELECT ts.username, ts.permission, ts.granted_at, ts.granted_by, "
                    "       u.display_name, u.role "
                    "FROM topology_shares ts LEFT JOIN users u ON u.username = ts.username "
                    "WHERE ts.composite_id = ? ORDER BY ts.granted_at DESC",
                    (d["composite_id"],),
                ).fetchall()
                result.append({
                    "composite_id": d["composite_id"],
                    "owner": owner,
                    "domain_id": d["domain_id"],
                    "topology_id": d["topology_id"],
                    "name": meta.get("name", d["name"]),
                    "created_at": d["created_at"],
                    "updated_at": d["updated_at"],
                    "object_count": meta.get("object_count", 0),
                    "device_count": meta.get("device_count", 0),
                    "link_count": meta.get("link_count", 0),
                    "recipient_count": d["recipient_count"],
                    "recipients": [dict(r) for r in recipients],
                })
            return result

    def list_incoming_topology_shares(self, username: str) -> List[Dict[str, Any]]:
        """Every per-file share targeted AT this user.

        Each row carries the owner's display name + the live topology metadata
        (name / counts) re-read from the owner's DB so renames propagate.
        """
        with _open_db(USERS_DB_PATH) as central:
            rows = central.execute(
                "SELECT st.*, ts.permission, ts.granted_at, ts.granted_by, "
                "       u.display_name AS owner_display_name, u.role AS owner_role "
                "FROM shared_topologies st "
                "JOIN topology_shares ts ON ts.composite_id = st.composite_id "
                "LEFT JOIN users u ON u.username = st.owner "
                "WHERE ts.username = ? ORDER BY ts.granted_at DESC",
                (username,),
            ).fetchall()
            result: List[Dict[str, Any]] = []
            for r in rows:
                d = dict(r)
                meta = self._topology_meta(d["owner"], d["domain_id"], d["topology_id"]) or {}
                # Skip stale share rows whose source topology was deleted
                if not meta:
                    continue
                result.append({
                    "id": d["composite_id"],
                    "composite_id": d["composite_id"],
                    "domain_id": SHARED_WITH_ME_DOMAIN_ID,
                    "owner": d["owner"],
                    "owner_display_name": d.get("owner_display_name") or d["owner"],
                    "owner_role": d.get("owner_role"),
                    "source_domain_id": d["domain_id"],
                    "source_domain_name": self._domain_name(d["owner"], d["domain_id"]),
                    "source_topology_id": d["topology_id"],
                    "name": meta.get("name", d["name"]),
                    "created_at": meta.get("created_at", d["created_at"]),
                    "updated_at": meta.get("updated_at", d["updated_at"]),
                    "object_count": meta.get("object_count", 0),
                    "device_count": meta.get("device_count", 0),
                    "link_count": meta.get("link_count", 0),
                    "permission": d["permission"],
                    "granted_at": d["granted_at"],
                    "granted_by": d["granted_by"],
                    "is_shared_with_me": True,
                })
            return result

    def resolve_shared_topology(
        self, viewer: str, composite_id: str
    ) -> Optional[Dict[str, Any]]:
        """Return {owner, domain_id, topology_id, permission} if viewer can read this composite share."""
        with _open_db(USERS_DB_PATH) as central:
            row = central.execute(
                "SELECT st.owner, st.domain_id, st.topology_id, ts.permission "
                "FROM shared_topologies st "
                "JOIN topology_shares ts ON ts.composite_id = st.composite_id "
                "WHERE st.composite_id = ? AND ts.username = ?",
                (composite_id, viewer),
            ).fetchone()
            return dict(row) if row else None

    # -- Synthetic "Shared with me" domain ---------------------------------

    @staticmethod
    def is_shared_with_me_domain(domain_id: str) -> bool:
        return domain_id == SHARED_WITH_ME_DOMAIN_ID

    def shared_with_me_domain(self, username: str) -> Dict[str, Any]:
        """Build the synthetic domain payload for a user.

        Always present, undeletable, never owned by anyone. Topology count is
        the number of per-file shares currently targeting this user.
        """
        incoming = self.list_incoming_topology_shares(username)
        latest_update = ""
        for t in incoming:
            ts = t.get("updated_at") or t.get("granted_at") or ""
            if ts > latest_update:
                latest_update = ts
        return {
            "id": SHARED_WITH_ME_DOMAIN_ID,
            "name": SHARED_WITH_ME_DOMAIN_NAME,
            "description": SHARED_WITH_ME_DOMAIN_DESC,
            "owner": "",
            "is_shared": True,
            "is_built_in": True,
            "is_locked": True,
            "is_shared_with_me_domain": True,
            "topology_count": len(incoming),
            "created_at": "",
            "updated_at": latest_update,
            "permission": "read",
        }

    def list_share_activity(
        self,
        viewer: str,
        scope: str = "involving",
        domain_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Return audit-log entries.

        scope:
          - "owned"     -> activity on domains owned by viewer
          - "received"  -> activity on domains shared with viewer
          - "involving" -> either of the above (default)
          - "domain"    -> a single composite domain_id (admin/owner only)
        """
        with _open_db(USERS_DB_PATH) as central:
            params: List[Any] = []
            where = ""
            if scope == "domain" and domain_id:
                where = "WHERE domain_id = ?"
                params.append(domain_id)
            elif scope == "owned":
                where = "WHERE owner = ?"
                params.append(viewer)
            elif scope == "received":
                where = "WHERE target_user = ?"
                params.append(viewer)
            else:
                where = "WHERE owner = ? OR target_user = ? OR actor = ?"
                params.extend([viewer, viewer, viewer])
            params.append(int(limit))
            rows = central.execute(
                f"SELECT id, ts, action, domain_id, domain_name, owner, actor, target_user, "
                f"       permission, notes FROM share_activity {where} ORDER BY ts DESC, id DESC LIMIT ?",
                params,
            ).fetchall()
            return [dict(r) for r in rows]

    def share_overview(self, username: str) -> Dict[str, Any]:
        """One-shot summary used by the Share Topology dialog header."""
        outgoing = self.list_outgoing_shares(username)
        incoming = self.list_incoming_shares(username)
        outgoing_files = self.list_outgoing_topology_shares(username)
        incoming_files = self.list_incoming_topology_shares(username)
        recipients = set()
        for d in outgoing:
            for r in d.get("recipients", []):
                recipients.add(r["username"])
        for f in outgoing_files:
            for r in f.get("recipients", []):
                recipients.add(r["username"])
        topo_total = sum(d.get("topology_count", 0) for d in outgoing)
        return {
            "username": username,
            "domains_shared_out": len(outgoing),
            "topologies_shared_out": topo_total,
            "files_shared_out": len(outgoing_files),
            "unique_recipients": len(recipients),
            "domains_shared_with_me": len(incoming),
            "files_shared_with_me": len(incoming_files),
        }

    def list_share_targets(self, viewer: str) -> List[Dict[str, Any]]:
        """Active users eligible as share recipients.

        Excludes:
            * the viewer themselves (sharing with yourself is a no-op)
            * the bootstrap `admin` account (system/service identity, not a
              real person -- it should never appear in the typeahead)
        """
        system_usernames = {
            settings.default_admin_username,  # typically "admin"
            "default",                        # fallback/anon identity
        }
        with _open_db(USERS_DB_PATH) as central:
            rows = central.execute(
                "SELECT username, display_name, role FROM users "
                "WHERE is_active = 1 AND username != ? ORDER BY display_name COLLATE NOCASE",
                (viewer,),
            ).fetchall()
            return [dict(r) for r in rows if r["username"] not in system_usernames]

    # -- Role checks --

    def has_role_or_higher(self, username: str, min_role: str) -> bool:
        user = self.get_user(username)
        if not user:
            return False
        hierarchy = settings.role_hierarchy
        user_level = hierarchy.index(user["role"]) if user["role"] in hierarchy else -1
        min_level = hierarchy.index(min_role) if min_role in hierarchy else len(hierarchy)
        return user_level >= min_level

    def get_topology_count(self, username: str) -> int:
        self._ensure_user_db(username)
        with _open_db(self.user_db_path(username)) as conn:
            row = conn.execute("SELECT COUNT(*) FROM topologies").fetchone()
            return row[0] if row else 0


user_store = UserStore()
