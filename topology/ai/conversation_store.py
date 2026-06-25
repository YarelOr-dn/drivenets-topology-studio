"""Per-user AI conversation store.

Each user gets their own SQLite DB under
``~/.topology_users/<username>/ai.db`` with two tables:

  * ``conversations`` -- one row per logical chat (title, provider/model,
    optional topology pin, timestamps).
  * ``messages`` -- the turn-by-turn transcript, one row per user or
    assistant turn (+ optional ``tool_calls_json`` and
    ``retry_info_json`` blobs for post-hoc UI rendering).

Design invariants (mirrors the pattern in ``api/auth/user_store.py``):

1. ``_open_db`` uses WAL + ``synchronous=NORMAL`` so concurrent
   writers (poller vs. user POSTs) don't serialise on a single lock.
2. Every public method takes ``username`` as the first arg and
   resolves its DB from that, so nothing else in the codebase needs
   to know where ``ai.db`` lives.
3. Ownership checks are implicit: a user can never even see another
   user's ``ai.db`` because we derive the path from their own
   username. The admin-audit entry-points are separate (see
   :func:`admin_list_conversations`).
4. ``conv_id`` is a uuid4 hex so it is stable across renames and
   safe to put in URLs without collision between users.

This module has ZERO runtime dependency on ``serve.py`` -- it is
imported only from there (and from unit tests). Keep it that way so
``python3 -c "from ai.conversation_store import ConversationStore"``
works in isolation.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional


# Filename inside each per-user directory. Symmetry with topologies.db.
AI_DB_FILENAME = "ai.db"

# Hard caps. These exist so a runaway client can't blow through the
# disk or memory budget of a small deployment. Every cap is generous
# for real use: you'd need 40k turns per conversation or 10k chats to
# hit them, and both numbers suggest a bug, not a legitimate workload.
MAX_CONVERSATIONS_PER_USER = 10_000
MAX_MESSAGES_PER_CONVERSATION = 40_000
MAX_CONTENT_BYTES = 1_000_000  # single message; anything bigger is a bug
MAX_TITLE_LEN = 120

# Used by the endpoints that want to ship a "lite" snapshot (list view
# doesn't need the full transcript of every conversation -- just the
# metadata). Full transcripts come back only from get_conversation().
DEFAULT_LIST_LIMIT = 200


@contextmanager
def _open_db(db_path: Path) -> Generator[sqlite3.Connection, None, None]:
    """Context-managed connection tuned for multi-user concurrency.

    Copies the pragmas from api/auth/user_store.py on purpose: we want
    both DBs to behave identically under load, and the proven
    combination (WAL + synchronous=NORMAL + busy_timeout=5s) is already
    battle-tested on the topology DBs.
    """
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    try:
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA wal_autocheckpoint=1000")
            conn.execute("PRAGMA foreign_keys=ON")
        except Exception:
            # Pragmas are best-effort; if the DB is corrupt the real
            # error still surfaces from the actual query below.
            pass
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        conn.close()


class ConversationStore:
    """Facade over every user's ``ai.db``.

    Construct once (serve.py keeps a module-level singleton) and call
    methods as needed -- there is no per-user in-memory state so the
    store is cheap to hold.

    ``users_base_dir`` MUST be the same directory used by
    ``api/auth/user_store.UserStore`` -- we keep everything for a user
    in one place so "delete user" remains a single ``rm -rf``.
    """

    def __init__(self, users_base_dir: str | Path):
        self.users_base_dir = Path(users_base_dir).expanduser()

    # ------------------------------------------------------------------
    #   Path + schema bootstrap
    # ------------------------------------------------------------------

    def _db_path(self, username: str) -> Path:
        if not username:
            raise ValueError("username is required")
        if "/" in username or ".." in username:
            raise ValueError("invalid username")
        return self.users_base_dir / username / AI_DB_FILENAME

    def _ensure_user_db(self, username: str) -> Path:
        path = self._db_path(username)
        path.parent.mkdir(parents=True, exist_ok=True)
        with _open_db(path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL DEFAULT 'New chat',
                    topology_domain TEXT,
                    topology_id TEXT,
                    provider TEXT,
                    model TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    archived INTEGER NOT NULL DEFAULT 0,
                    pinned INTEGER NOT NULL DEFAULT 0,
                    turn_count INTEGER NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_conv_updated
                    ON conversations(archived, updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_conv_topology
                    ON conversations(topology_domain, topology_id, updated_at DESC);

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conv_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_calls_json TEXT,
                    retry_info_json TEXT,
                    created_at INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_msg_conv
                    ON messages(conv_id, created_at);
                """
            )
            conn.commit()
        return path

    # ------------------------------------------------------------------
    #   Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

    @staticmethod
    def _new_conv_id() -> str:
        # ``uuid4`` so conversation ids are globally unique across
        # every user -- this lets the admin audit endpoint return
        # rows from many users without id collisions.
        return uuid.uuid4().hex

    @staticmethod
    def auto_title(first_message: str) -> str:
        """Pick a short human title from the first user message.

        We only truncate on a word boundary when possible so "add a
        small leaf-spine fabric with 4 leaves" doesn't end in the
        middle of "leaves".
        """
        if not first_message:
            return "New chat"
        s = " ".join(str(first_message).split())  # collapse whitespace
        if len(s) <= 60:
            return s[:MAX_TITLE_LEN]
        cut = s[:60]
        # back off to the last space to avoid mid-word truncation.
        last_space = cut.rfind(" ")
        if last_space >= 30:
            cut = cut[:last_space]
        return (cut + "\u2026")[:MAX_TITLE_LEN]  # horizontal ellipsis

    @staticmethod
    def _row_to_conv_dict(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "title": row["title"],
            "topology_domain": row["topology_domain"],
            "topology_id": row["topology_id"],
            "provider": row["provider"],
            "model": row["model"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "archived": bool(row["archived"]),
            "pinned": bool(row["pinned"]),
            "turn_count": row["turn_count"],
        }

    @staticmethod
    def _row_to_message_dict(row: sqlite3.Row) -> Dict[str, Any]:
        tool_calls = None
        retry_info = None
        try:
            if row["tool_calls_json"]:
                tool_calls = json.loads(row["tool_calls_json"])
        except Exception:
            tool_calls = None
        try:
            if row["retry_info_json"]:
                retry_info = json.loads(row["retry_info_json"])
        except Exception:
            retry_info = None
        out: Dict[str, Any] = {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "created_at": row["created_at"],
        }
        if tool_calls is not None:
            out["tool_calls"] = tool_calls
        if retry_info is not None:
            out["retry_info"] = retry_info
        return out

    # ------------------------------------------------------------------
    #   CRUD
    # ------------------------------------------------------------------

    def create_conversation(
        self,
        username: str,
        *,
        title: Optional[str] = None,
        topology_domain: Optional[str] = None,
        topology_id: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new empty conversation and return its metadata."""
        db = self._ensure_user_db(username)
        conv_id = self._new_conv_id()
        now = self._now_ms()
        title = (title or "New chat").strip()[:MAX_TITLE_LEN] or "New chat"
        with _open_db(db) as conn:
            # Enforce the soft cap. We can't just INSERT-then-maybe-cleanup
            # because that would race with a concurrent create on a
            # different request; the count check under a write tx is safe.
            cnt = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
            if cnt >= MAX_CONVERSATIONS_PER_USER:
                raise RuntimeError(
                    f"Too many conversations (limit {MAX_CONVERSATIONS_PER_USER}). "
                    "Archive or delete older ones."
                )
            conn.execute(
                """INSERT INTO conversations (
                    id, title, topology_domain, topology_id,
                    provider, model, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (conv_id, title, topology_domain, topology_id,
                 provider, model, now, now),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?",
                (conv_id,),
            ).fetchone()
        return self._row_to_conv_dict(row)

    def get_conversation(
        self,
        username: str,
        conv_id: str,
        *,
        include_messages: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Fetch a conversation (with full transcript by default).

        Returns ``None`` when the conversation does not exist or does
        not belong to ``username`` (same effect from the caller's POV
        so we never leak existence across users).
        """
        db = self._db_path(username)
        if not db.exists():
            return None
        with _open_db(db) as conn:
            row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?",
                (conv_id,),
            ).fetchone()
            if not row:
                return None
            out = self._row_to_conv_dict(row)
            if include_messages:
                msgs = conn.execute(
                    "SELECT * FROM messages WHERE conv_id = ? ORDER BY created_at ASC, id ASC",
                    (conv_id,),
                ).fetchall()
                out["messages"] = [self._row_to_message_dict(m) for m in msgs]
            return out

    def list_conversations(
        self,
        username: str,
        *,
        include_archived: bool = False,
        topology_domain: Optional[str] = None,
        topology_id: Optional[str] = None,
        limit: int = DEFAULT_LIST_LIMIT,
    ) -> List[Dict[str, Any]]:
        """List the user's conversations, most-recently-updated first.

        Filters:
          * ``include_archived`` -- default False hides the "X was
            archived when the user clicked New Chat" entries.
          * ``topology_domain`` / ``topology_id`` -- when both are
            provided, return only conversations pinned to that
            topology. Useful for the future per-topology drawer.
        """
        db = self._db_path(username)
        if not db.exists():
            return []
        sql = "SELECT * FROM conversations WHERE 1=1"
        params: List[Any] = []
        if not include_archived:
            sql += " AND archived = 0"
        if topology_domain is not None and topology_id is not None:
            sql += " AND topology_domain = ? AND topology_id = ?"
            params.extend([topology_domain, topology_id])
        sql += " ORDER BY pinned DESC, updated_at DESC LIMIT ?"
        params.append(int(max(1, min(limit, MAX_CONVERSATIONS_PER_USER))))
        with _open_db(db) as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
        return [self._row_to_conv_dict(r) for r in rows]

    def rename_conversation(
        self,
        username: str,
        conv_id: str,
        new_title: str,
    ) -> Optional[Dict[str, Any]]:
        new_title = (new_title or "").strip()[:MAX_TITLE_LEN] or "New chat"
        return self._patch_conversation(username, conv_id, {"title": new_title})

    def set_archived(
        self,
        username: str,
        conv_id: str,
        archived: bool,
    ) -> Optional[Dict[str, Any]]:
        return self._patch_conversation(
            username, conv_id, {"archived": 1 if archived else 0},
        )

    def set_pinned(
        self,
        username: str,
        conv_id: str,
        pinned: bool,
    ) -> Optional[Dict[str, Any]]:
        return self._patch_conversation(
            username, conv_id, {"pinned": 1 if pinned else 0},
        )

    def set_topology_pin(
        self,
        username: str,
        conv_id: str,
        topology_domain: Optional[str],
        topology_id: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Link or unlink this conversation to a topology.

        Pass ``None``/``None`` to unlink. Both must be either
        provided together or both omitted; we treat half-set values
        as unlinking on purpose (a domain without an id is useless).
        """
        if not topology_domain or not topology_id:
            topology_domain = None
            topology_id = None
        return self._patch_conversation(
            username, conv_id,
            {"topology_domain": topology_domain, "topology_id": topology_id},
        )

    def _patch_conversation(
        self,
        username: str,
        conv_id: str,
        fields: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        db = self._db_path(username)
        if not db.exists():
            return None
        if not fields:
            return self.get_conversation(username, conv_id, include_messages=False)
        now = self._now_ms()
        sets = ", ".join(f"{k} = ?" for k in fields.keys()) + ", updated_at = ?"
        params = list(fields.values()) + [now, conv_id]
        with _open_db(db) as conn:
            cur = conn.execute(
                f"UPDATE conversations SET {sets} WHERE id = ?",
                tuple(params),
            )
            conn.commit()
            if cur.rowcount == 0:
                return None
            row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?", (conv_id,),
            ).fetchone()
        return self._row_to_conv_dict(row) if row else None

    def delete_conversation(self, username: str, conv_id: str) -> bool:
        db = self._db_path(username)
        if not db.exists():
            return False
        with _open_db(db) as conn:
            cur = conn.execute(
                "DELETE FROM conversations WHERE id = ?", (conv_id,),
            )
            conn.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    #   Messages
    # ------------------------------------------------------------------

    def append_message(
        self,
        username: str,
        conv_id: str,
        role: str,
        content: str,
        *,
        tool_calls: Optional[Any] = None,
        retry_info: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Append one turn to a conversation.

        Returns the inserted message row (with id + created_at) so
        the caller can echo it back to the client without an extra
        SELECT. Returns ``None`` if the conversation doesn't exist.

        Also bumps the conversation's ``updated_at`` and
        ``turn_count`` so listing stays correctly sorted.
        """
        role = (role or "").strip()
        if role not in {"user", "assistant", "system"}:
            raise ValueError(f"unsupported role: {role!r}")
        content = content or ""
        if len(content.encode("utf-8")) > MAX_CONTENT_BYTES:
            raise ValueError(
                f"message too large ({len(content)} chars > "
                f"{MAX_CONTENT_BYTES} bytes)"
            )
        db = self._db_path(username)
        if not db.exists():
            return None
        now = self._now_ms()
        tc_json = json.dumps(tool_calls) if tool_calls else None
        ri_json = json.dumps(retry_info) if retry_info else None
        with _open_db(db) as conn:
            conv = conn.execute(
                "SELECT turn_count FROM conversations WHERE id = ?",
                (conv_id,),
            ).fetchone()
            if not conv:
                return None
            if conv["turn_count"] >= MAX_MESSAGES_PER_CONVERSATION:
                raise RuntimeError(
                    f"Conversation has hit the message cap "
                    f"({MAX_MESSAGES_PER_CONVERSATION}). Start a new chat."
                )
            cur = conn.execute(
                """INSERT INTO messages (
                    conv_id, role, content,
                    tool_calls_json, retry_info_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)""",
                (conv_id, role, content, tc_json, ri_json, now),
            )
            msg_id = cur.lastrowid
            conn.execute(
                "UPDATE conversations SET updated_at = ?, "
                "turn_count = turn_count + 1 WHERE id = ?",
                (now, conv_id),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM messages WHERE id = ?", (msg_id,),
            ).fetchone()
        return self._row_to_message_dict(row) if row else None

    # ------------------------------------------------------------------
    #   Admin audit (read-only cross-user view)
    # ------------------------------------------------------------------

    def admin_list_conversations(
        self,
        target_username: str,
        *,
        include_archived: bool = True,
        limit: int = DEFAULT_LIST_LIMIT,
    ) -> List[Dict[str, Any]]:
        """Admin-only: list any user's conversations.

        Callers MUST check the role themselves -- this module does not
        know about sessions. The function simply returns whatever is
        on disk for ``target_username`` (empty list if they've never
        used the AI).
        """
        return self.list_conversations(
            target_username,
            include_archived=include_archived,
            limit=limit,
        )

    def admin_get_conversation(
        self,
        target_username: str,
        conv_id: str,
    ) -> Optional[Dict[str, Any]]:
        return self.get_conversation(
            target_username,
            conv_id,
            include_messages=True,
        )

    # ------------------------------------------------------------------
    #   Stats (future admin panel, lightweight)
    # ------------------------------------------------------------------

    def user_stats(self, username: str) -> Dict[str, Any]:
        db = self._db_path(username)
        if not db.exists():
            return {
                "conversations": 0,
                "active_conversations": 0,
                "messages": 0,
                "last_activity": None,
            }
        with _open_db(db) as conn:
            total = conn.execute(
                "SELECT COUNT(*) AS c FROM conversations",
            ).fetchone()["c"]
            active = conn.execute(
                "SELECT COUNT(*) AS c FROM conversations WHERE archived = 0",
            ).fetchone()["c"]
            msgs = conn.execute(
                "SELECT COUNT(*) AS c FROM messages",
            ).fetchone()["c"]
            last = conn.execute(
                "SELECT MAX(updated_at) AS t FROM conversations",
            ).fetchone()["t"]
        return {
            "conversations": total,
            "active_conversations": active,
            "messages": msgs,
            "last_activity": last,
        }
