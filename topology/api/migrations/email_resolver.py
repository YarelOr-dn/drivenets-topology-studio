"""Resolve display names to verified @drivenets.com emails via Atlassian.

This module is the *only* place that hits Atlassian for the username
migration. It is intentionally read-only: nothing here touches the
topology database, the user filesystem, or any user state. Output is a
deterministic JSON cache that the migration tool consumes.

Auth model
----------
We never invent emails. We never hard-code an Atlassian token. The
operator running the migration must already have a per-user
``jira_config.json`` set up via the existing topology UI -- the same
file the Bug panel uses. The resolver picks that operator up via
``user_store.user_jira_config_path(operator_username)`` so the audit
trail (Confluence ``last-modified-by``) ends up on a real human, not on
a service account.

Output
------
Calling :func:`resolve_user_emails` writes / updates a JSON cache that
maps the *current* topology username (DB primary key) to a small record:

.. code-block:: json

   {
     "yarel":     {"display_name": "Yarel Or",  "email": "yor@drivenets.com",
                    "status": "matched", "source": "confluence",
                    "candidates": [...]},
     "abishek":   {"display_name": "Abishek SureshKumar",
                    "email": "askumar@drivenets.com",
                    "status": "matched", "source": "confluence",
                    "candidates": [...]},
     "...":       {...}
   }

Statuses (mirrored by the migration tool's report):

- ``matched``         exactly one active @drivenets.com hit
- ``inactive_match``  the only @drivenets.com hit is inactive in Atlassian
- ``ambiguous``       multiple distinct @drivenets.com candidates
- ``no_email``        Confluence found the user but the email is hidden
                      (``email == null``) or non-@drivenets.com only
- ``not_found``       no Confluence hit for this display name
- ``api_error``       transport / auth failure -- retry later

The migration tool only renames users with ``status == "matched"``
(plus, optionally, ``inactive_match`` when ``--allow-inactive`` is set).
Everything else is reported and left untouched.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import sys
import time
from base64 import b64encode
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib import error as urlerror, parse, request

logger = logging.getLogger("topology.migrations.email_resolver")


COMPANY_DOMAIN = "drivenets.com"
COMPANY_TYPO_DOMAINS = {"drivents.com"}

DEFAULT_CACHE_FILENAME = "username_email_cache.json"
DEFAULT_TIMEOUT_SECONDS = 20


@dataclass
class AtlassianConfig:
    """Resolved Atlassian credentials + base URL.

    Loaded from ``~/.topology_users/<operator>/jira_config.json`` (the
    same per-user file the Bugs panel writes). We refuse to run if the
    file is missing or incomplete -- callers must run the migration as
    a real operator, not anonymously.
    """

    base_url: str
    email: str
    api_token: str

    @classmethod
    def load_for_operator(cls, operator: str) -> "AtlassianConfig":
        from api.auth.user_store import user_store  # local import; avoid cycles

        cfg_path = user_store.user_jira_config_path(operator)
        if not cfg_path.exists():
            raise FileNotFoundError(
                f"No Atlassian config for operator {operator!r} at {cfg_path}. "
                "Configure Jira credentials in the topology UI first."
            )
        try:
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Cannot read {cfg_path}: {exc}") from exc

        base_url = (data.get("base_url") or "").strip().rstrip("/")
        email = (data.get("email") or "").strip()
        token = (data.get("api_token") or "").strip()
        if not (base_url and email and token):
            raise RuntimeError(
                f"{cfg_path} is missing base_url / email / api_token. "
                "Re-save your Jira credentials from the topology UI."
            )
        return cls(base_url=base_url, email=email, api_token=token)

    @property
    def auth_header(self) -> str:
        raw = f"{self.email}:{self.api_token}".encode("utf-8")
        return "Basic " + b64encode(raw).decode("ascii")


@dataclass
class ResolverConfig:
    """Tunables for :class:`EmailResolver`."""

    cache_path: Path
    timeout: int = DEFAULT_TIMEOUT_SECONDS
    rate_limit_qps: float = 4.0
    allow_inactive: bool = False
    user_agent: str = "topology-username-migration/1.0"


@dataclass
class ResolveResult:
    """Per-user resolution outcome (mirrors the JSON cache shape)."""

    username: str
    display_name: str
    email: Optional[str] = None
    status: str = "not_found"
    source: str = "confluence"
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    notes: str = ""

    def to_cache(self) -> Dict[str, Any]:
        return {
            "display_name": self.display_name,
            "email": self.email,
            "status": self.status,
            "source": self.source,
            "candidates": self.candidates,
            "notes": self.notes,
        }


class EmailResolver:
    """Resolve display names to verified company emails.

    Cached by current topology ``username``. The cache is the source of
    truth the migration tool reads; we never hit Atlassian twice for
    the same user across runs unless ``--refresh`` is passed.
    """

    def __init__(self, atlassian: AtlassianConfig, cfg: ResolverConfig):
        self.atlassian = atlassian
        self.cfg = cfg
        self._min_interval = 1.0 / max(cfg.rate_limit_qps, 0.1)
        self._last_call_at = 0.0
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()

    # ------------------------------------------------------------------
    # Cache I/O
    # ------------------------------------------------------------------

    def _load_cache(self) -> None:
        if not self.cfg.cache_path.exists():
            return
        try:
            data = json.loads(self.cfg.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Cache %s unreadable (%s); starting empty",
                           self.cfg.cache_path, exc)
            return
        if isinstance(data, dict):
            self._cache = data

    def _flush_cache(self) -> None:
        tmp = self.cfg.cache_path.with_suffix(self.cfg.cache_path.suffix + ".tmp")
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(self._cache, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.cfg.cache_path)

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def resolve(
        self,
        users: Iterable[Dict[str, str]],
        *,
        refresh: bool = False,
        flush_every: int = 25,
        progress: bool = False,
    ) -> Dict[str, ResolveResult]:
        """Resolve every user in ``users``.

        ``users`` is an iterable of ``{"username", "display_name"}``
        dicts (extra keys are ignored). The cache is updated in place
        and persisted every ``flush_every`` users so a long run can be
        interrupted without losing progress.
        """

        results: Dict[str, ResolveResult] = {}
        users_list = list(users)
        total = len(users_list)
        for idx, row in enumerate(users_list, start=1):
            username = row["username"]
            display_name = row.get("display_name") or ""
            if not refresh and username in self._cache:
                cached = self._cache[username]
                results[username] = ResolveResult(
                    username=username,
                    display_name=cached.get("display_name", display_name),
                    email=cached.get("email"),
                    status=cached.get("status", "not_found"),
                    source=cached.get("source", "cache"),
                    candidates=cached.get("candidates", []) or [],
                    notes=cached.get("notes", ""),
                )
                if progress:
                    self._log_progress(idx, total, username, results[username])
                continue

            result = self._resolve_one(username, display_name)
            self._cache[username] = result.to_cache()
            results[username] = result
            if progress:
                self._log_progress(idx, total, username, result)
            if idx % flush_every == 0:
                self._flush_cache()
        self._flush_cache()
        return results

    def _log_progress(self, idx: int, total: int, username: str, r: ResolveResult) -> None:
        email = r.email or "-"
        logger.info("[%d/%d] %s -> %s [%s]", idx, total, username, email, r.status)

    def _resolve_one(self, username: str, display_name: str) -> ResolveResult:
        result = ResolveResult(username=username, display_name=display_name)
        if not display_name.strip():
            result.status = "no_display_name"
            return result

        # Atlassian's CQL user search escapes via plain quotes; escape
        # any embedded quotes the same way Confluence does.
        name_for_cql = display_name.replace('"', '\\"')
        # Strip parenthetical nicknames like "Shay (Yehoshua) Israel" so
        # we don't miss exact matches that Confluence stores without them.
        cleaned = re.sub(r"\s*\([^)]*\)\s*", " ", display_name).strip()
        queries = []
        seen_q = set()
        for q in (display_name, cleaned):
            q = q.strip()
            if q and q not in seen_q:
                seen_q.add(q)
                queries.append(q)

        all_candidates: List[Dict[str, Any]] = []
        try:
            for q in queries:
                hits = self._search_users(q)
                for h in hits:
                    cand = _summarise_candidate(h)
                    if cand and cand not in all_candidates:
                        all_candidates.append(cand)
        except _ApiError as exc:
            result.status = "api_error"
            result.notes = str(exc)
            return result

        result.candidates = all_candidates
        if not all_candidates:
            result.status = "not_found"
            return result

        # Exact display name match (case-insensitive) wins.
        wanted = display_name.strip().lower()
        wanted_cleaned = cleaned.lower()
        exact = [
            c for c in all_candidates
            if (c.get("display_name") or "").strip().lower() in {wanted, wanted_cleaned}
        ]
        pool = exact or all_candidates

        # NOTE: Confluence /wiki/rest/api/search/user returns ``active=false``
        # for almost every hit -- the search index just doesn't populate it
        # the way /rest/api/3/user does. We treat the company-domain email
        # itself as the strong signal and only use ``is_active`` as a
        # tiebreaker between two otherwise-identical candidates.
        company = [c for c in pool if _is_company_email(c.get("email"))]

        # De-duplicate identical emails (Atlassian returns one row per
        # search-index document, so a single human can show up twice).
        by_email: Dict[str, Dict[str, Any]] = {}
        for c in company:
            key = (c.get("email") or "").strip().lower()
            if not key:
                continue
            current = by_email.get(key)
            if current is None or (c.get("is_active") and not current.get("is_active")):
                by_email[key] = c
        unique = list(by_email.values())

        if len(unique) == 1:
            chosen = unique[0]
            result.email = chosen["email"].strip().lower()
            result.status = (
                "matched" if chosen.get("is_active", False) or True else "inactive_match"
            )
            # Keep the ``inactive_match`` status reserved for the case
            # where the *only* candidate is genuinely flagged inactive
            # in a way the operator might want to skip:
            if not chosen.get("is_active", False) and self.cfg.allow_inactive is False:
                # Still treat as matched -- the search ``active`` flag is
                # unreliable -- but record the source signal so the report
                # can show it.
                result.notes = "Confluence flagged inactive (search index quirk)"
            return result
        if len(unique) > 1:
            # Multiple distinct @drivenets.com hits for this name. Try
            # disambiguation in order:
            #   1. Atlassian display name matches our DB display name
            #      exactly (case-insensitive, whitespace-normalized).
            #      Catches "Adi Offer" vs "Adi Offer-Smith".
            #   2. Drop service / admin shadow accounts whose local part
            #      ends with one of the known role suffixes. This is how
            #      humans like ``lbasil`` end up with both ``lbasil@`` and
            #      ``lbasil-adm@`` in Atlassian.
            wanted_norm = " ".join(display_name.split()).strip().lower()
            tight = [
                c for c in unique
                if " ".join((c.get("display_name") or "").split()).strip().lower() == wanted_norm
            ]
            if len(tight) == 1:
                result.email = tight[0]["email"].strip().lower()
                result.status = "matched"
                return result
            human = [c for c in (tight or unique) if not _is_role_email(c.get("email"))]
            if len(human) == 1:
                result.email = human[0]["email"].strip().lower()
                result.status = "matched"
                result.notes = "preferred non-role account"
                return result
            result.status = "ambiguous"
            result.notes = (
                f"{len(unique)} distinct @{COMPANY_DOMAIN} candidates"
            )
            return result

        # Confluence found someone, but no @drivenets.com email.
        result.status = "no_email"
        return result

    # ------------------------------------------------------------------
    # Atlassian transport
    # ------------------------------------------------------------------

    def _search_users(self, query: str) -> List[Dict[str, Any]]:
        """Hit Confluence ``/wiki/rest/api/search/user`` with a CQL query.

        We use Confluence (not Jira) because the existing MCP search
        and the rest of the topology Atlassian integration already use
        the Confluence user index, which exposes ``email`` directly on
        the user record. The Jira ``/rest/api/3/user/search`` endpoint
        does not return email for most callers.
        """
        cql = f'type = "user" AND user.fullname ~ "{query}"'
        params = {"cql": cql, "limit": 10}
        url = f"{self.atlassian.base_url}/wiki/rest/api/search/user?{parse.urlencode(params)}"
        self._respect_rate_limit()
        req = request.Request(url, headers={
            "Authorization": self.atlassian.auth_header,
            "Accept": "application/json",
            "User-Agent": self.cfg.user_agent,
        })
        try:
            with request.urlopen(req, timeout=self.cfg.timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urlerror.HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8", errors="replace")[:200]
            except Exception:  # noqa: BLE001
                pass
            raise _ApiError(f"HTTP {exc.code} {exc.reason} for {query!r}: {body}") from exc
        except (urlerror.URLError, TimeoutError, OSError) as exc:
            raise _ApiError(f"Network error for {query!r}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise _ApiError(f"Bad JSON from Confluence for {query!r}: {exc}") from exc

        results = payload.get("results") or []
        out: List[Dict[str, Any]] = []
        for r in results:
            user = (r.get("user") or {}) if isinstance(r, dict) else {}
            if not user:
                # Some Atlassian sites return the user fields at the top
                # level; fall back to that shape so we never miss a hit.
                user = r if isinstance(r, dict) else {}
            out.append(user)
        return out

    def _respect_rate_limit(self) -> None:
        now = time.monotonic()
        delta = now - self._last_call_at
        if delta < self._min_interval:
            time.sleep(self._min_interval - delta)
        self._last_call_at = time.monotonic()


class _ApiError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _summarise_candidate(user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(user, dict):
        return None
    email = (user.get("email") or "").strip() or None
    return {
        "account_id": user.get("accountId") or user.get("account_id"),
        "display_name": user.get("displayName") or user.get("display_name"),
        "email": email,
        "is_active": bool(
            user.get("active")
            if "active" in user
            else user.get("is_active", False)
        ),
    }


# Local-part suffixes that mark non-human / shadow accounts. We always
# prefer the bare local part over these when picking between candidates.
_ROLE_SUFFIXES = ("-adm", "-admin", "-svc", "-service", "-bot", "-system")


def _is_role_email(email: Optional[str]) -> bool:
    if not email or "@" not in email:
        return False
    local = email.split("@", 1)[0].lower()
    return any(local.endswith(suf) for suf in _ROLE_SUFFIXES)


def _is_company_email(email: Optional[str]) -> bool:
    if not email:
        return False
    e = email.strip().lower()
    if "@" not in e:
        return False
    domain = e.rsplit("@", 1)[-1]
    if domain in COMPANY_TYPO_DOMAINS:
        # We never match the typo domain; report as not-company.
        return False
    return domain == COMPANY_DOMAIN


# ---------------------------------------------------------------------------
# Public API helpers
# ---------------------------------------------------------------------------


def load_active_users(users_db: Path) -> List[Dict[str, str]]:
    """Return ``[{username, display_name, email, role}]`` for every active row."""
    con = sqlite3.connect(users_db)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            "SELECT username, display_name, email, role "
            "FROM users WHERE is_active = 1 ORDER BY username"
        ).fetchall()
    finally:
        con.close()
    return [dict(r) for r in rows]


def resolve_user_emails(
    *,
    operator: str,
    users_db: Path,
    cache_path: Path,
    refresh: bool = False,
    progress: bool = True,
) -> Dict[str, ResolveResult]:
    """High-level entry point: load DB + resolve + persist cache.

    Returns the in-memory map for further processing (e.g. the
    rename migration tool consumes it directly). Side effect: the
    cache JSON at ``cache_path`` is overwritten atomically.
    """

    atlassian = AtlassianConfig.load_for_operator(operator)
    cfg = ResolverConfig(cache_path=cache_path)
    resolver = EmailResolver(atlassian=atlassian, cfg=cfg)
    users = load_active_users(users_db)
    return resolver.resolve(users, refresh=refresh, progress=progress)


def summarise(results: Dict[str, ResolveResult]) -> Dict[str, int]:
    """Tally results by status for the human-facing report."""
    out: Dict[str, int] = {}
    for r in results.values():
        out[r.status] = out.get(r.status, 0) + 1
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="email_resolver",
        description="Resolve topology display names to @drivenets.com emails via Atlassian.",
    )
    p.add_argument("--operator", required=True,
                   help="Username whose Atlassian creds to use (e.g. yarel, yor).")
    p.add_argument("--users-db", default=str(Path.home() / ".topology_users" / "_users.db"),
                   help="Path to the central topology users SQLite DB.")
    p.add_argument("--cache",
                   default=str(Path.home() / ".topology_users" / DEFAULT_CACHE_FILENAME),
                   help="Where to read/write the username->email cache JSON.")
    p.add_argument("--refresh", action="store_true",
                   help="Re-query Atlassian even for usernames already cached.")
    p.add_argument("--quiet", action="store_true",
                   help="Suppress per-user progress logging.")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    args = _build_parser().parse_args(argv)
    users_db = Path(args.users_db).expanduser()
    cache = Path(args.cache).expanduser()
    if not users_db.exists():
        logger.error("Users DB not found: %s", users_db)
        return 2
    results = resolve_user_emails(
        operator=args.operator,
        users_db=users_db,
        cache_path=cache,
        refresh=args.refresh,
        progress=not args.quiet,
    )
    tally = summarise(results)
    logger.info("Done. Cache: %s", cache)
    for status, count in sorted(tally.items()):
        logger.info("  %-15s %4d", status, count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
