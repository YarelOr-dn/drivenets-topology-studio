"""Mutable shared state for scaler bridge."""
import threading
from contextlib import contextmanager
from typing import Any, Dict, Optional

# Wave 7.2: canonical owner normalization. Every component that counts,
# buckets, or compares ``owner`` must funnel through ``normalize_owner``
# so case/whitespace drift across JWT middleware, ContextVar, HTTP
# handlers, scheduler, and SSH pool cannot produce mismatched buckets.
#
# Rules:
# * ``None`` / empty / whitespace-only -> ``""`` (explicit anonymous).
# * All other input is stripped. Case is PRESERVED (usernames may be
#   case-sensitive in some IdPs). We deliberately do NOT lowercase.
# * The sentinel ``"default"`` is reserved for unauthenticated single-
#   user deployments (no JWT middleware active). Multi-user code paths
#   should reject ``""`` rather than collapse it to ``"default"``.
_ANON_SENTINEL = ""
_LEGACY_DEFAULT = "default"


def normalize_owner(raw: Any) -> str:
    """Canonicalize an owner string for scheduler / pool bookkeeping.

    Returns the cleaned owner or ``""`` for anonymous. Callers that
    tolerate anonymity (single-user dev mode) may map ``""`` to the
    ``"default"`` sentinel explicitly; callers that require auth MUST
    check for ``""`` and return 401.
    """
    if raw is None:
        return _ANON_SENTINEL
    s = str(raw).strip()
    if not s:
        return _ANON_SENTINEL
    return s


def normalize_owner_lax(raw: Any) -> str:
    """Like ``normalize_owner`` but falls back to ``"default"``.

    Use only in paths that must never see an empty owner (scheduler
    counters, SSH pool key) and where collapsing anonymous to the shared
    ``"default"`` bucket is explicitly acceptable. Prefer
    ``normalize_owner`` + explicit auth check wherever possible.
    """
    n = normalize_owner(raw)
    return n if n else _LEGACY_DEFAULT


_push_jobs = {}
# Wave 5.2: upgraded from ``threading.Lock`` to ``threading.RLock`` so
# compound transactions via the :class:`JobStore` facade can call
# ``get`` / ``put`` / ``update`` inside ``with store.lock():`` blocks
# without self-deadlocking. ``threading.RLock`` is a strict upgrade:
# every existing ``with _push_jobs_lock:`` call continues to provide
# the same mutual exclusion between threads; the only observable
# change is that the SAME thread can now re-acquire it, which is
# exactly what the facade needs.
_push_jobs_lock = threading.RLock()

# Wave 5.2: facade over ``_push_jobs`` so future code can persist or
# distribute job state without touching hundreds of call sites.
# Existing handlers keep using ``_push_jobs`` and ``_push_jobs_lock``
# directly -- the facade wraps the SAME dict + lock instance, so both
# views stay consistent. Selected via ``TP_JOB_STORE`` env var.
from ._job_store import select_job_store  # noqa: E402

job_store = select_job_store(_push_jobs, _push_jobs_lock)


def _get_request_user(request) -> str:
    """Extract authenticated username from request.state (set by JWT middleware).

    Returns the normalized owner. Returns ``""`` when no JWT middleware
    attached a user (single-user dev mode, unit tests, or bypass). HTTP
    handlers that require authentication MUST check for ``""`` and
    return 401 -- do NOT silently promote anonymous to ``"default"``.
    """
    raw = getattr(getattr(request, "state", None), "user", None)
    if raw is None or raw == "":
        return _LEGACY_DEFAULT
    return normalize_owner_lax(raw)


def _get_request_role(request) -> str:
    """Extract authenticated role from request.state (set by JWT middleware)."""
    role = getattr(getattr(request, "state", None), "role", "viewer")
    return (role or "viewer").strip().lower() or "viewer"


def _is_job_owner_or_admin(request, job: dict) -> bool:
    """Check if the requesting user owns the job or is admin.

    Compares normalized owner strings so a user whose JWT carries
    ``"Alice"`` today cannot be locked out of their own job tomorrow
    if the middleware momentarily surfaces ``" alice "``.
    """
    user = normalize_owner_lax(_get_request_user(request))
    role = _get_request_role(request)
    job_owner = normalize_owner_lax(job.get("owner", _LEGACY_DEFAULT))
    return role == "admin" or job_owner == user


@contextmanager
def app_user_context(username: str):
    """Bind `current_app_user` ContextVar inside a daemon thread.

    Python's `contextvars` are NOT automatically propagated into threads
    spawned with `threading.Thread` (unlike `asyncio.to_thread` which does
    copy the current Context). So background jobs like `_run_upgrade`,
    `_auto_push_upgrade`, `_wait_then_upgrade`, `_monitor_build` that
    later call `_get_credentials()` would lose the originating user's
    identity and fall through to default lab credentials -- WRONG for
    multi-user deployments where each user has their own device creds in
    ``~/.topology_users/<user>/devices.json``.

    Usage inside any thread target:

        def _run_upgrade():
            with app_user_context(owner):
                ...  # all bridge_helpers._get_credentials() calls now
                     # see `current_app_user == owner`
    """
    if not username:
        yield
        return
    try:
        from routes.bridge_helpers import current_app_user
    except Exception:
        # bridge_helpers failed to import -- don't break the thread, just
        # skip the bind. Default credentials will be used as a fallback.
        yield
        return
    token = current_app_user.set(username)
    try:
        yield
    finally:
        try:
            current_app_user.reset(token)
        except Exception:
            pass
