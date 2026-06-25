"""Domain Knowledge -- per-domain attached context (kind registry + live status).

A "topology domain" used to be just a folder of topology files. The knowledge
layer turns each domain into a small project workspace that can hold:

    branch        - Jenkins feature/dev/release branch to monitor (build status,
                    sanitizer flag, latest SUCCESS, one-click upgrade-to-device)
    jira_epic     - Jira EPIC/ticket to pin (summary, status, assignee)
    test_suite    - Link into scaler/TEST/catalog/<suite>/ (last-5 RUN_* results)
    spirent       - Spirent session file (stream count, last run)
    device        - Explicit device roster for this domain (orthogonal to canvas)
    note          - Markdown runbook/scratchpad
    confluence    - Confluence or external spec URL
    cli_preset    - Pinned search_cli_docs query or show-command snippet
    bugs_scope    - Filter scoping the existing __bugs section to this domain
    ai_scope      - Pinned AI-assistant context prompt + chats

Each row lives in the `domain_knowledge` table (see user_store._ensure_user_db)
with a typed `kind` column and a free-form JSON `payload`. Kind handlers here
validate the payload shape and, where applicable, refresh it from external
sources (Jenkins, Jira, filesystem) during on-demand and background pollers.

The hybrid-sharing model (public travels with the domain, private stays per
user) is implemented in user_store -- this module is agnostic to it.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

# -- Kind registry -----------------------------------------------------------

@dataclass
class KnowledgeKindSpec:
    """Definition of a single knowledge kind (see module docstring)."""

    kind: str
    label: str
    description: str = ""
    supports_live: bool = False
    # (viewer_username, payload) -> updated_payload or None on failure.
    live_fetcher: Optional[Callable[[str, Dict[str, Any]], Optional[Dict[str, Any]]]] = None
    # Ops hook for sanity check: raises ValueError on bad payload, returns the
    # cleaned payload (stripped, trimmed, defaulted) that should be stored.
    validator: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    # (payload) -> natural key string. Lets us reject "same branch added twice".
    key_extractor: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None


REGISTRY: Dict[str, KnowledgeKindSpec] = {}


def register(spec: KnowledgeKindSpec) -> KnowledgeKindSpec:
    REGISTRY[spec.kind] = spec
    return spec


def get_spec(kind: str) -> Optional[KnowledgeKindSpec]:
    return REGISTRY.get(kind or "")


def kind_ids() -> List[str]:
    return sorted(REGISTRY.keys())


def validate_payload(kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Run the registered validator (if any) and return the cleaned payload."""
    spec = get_spec(kind)
    if not spec:
        raise ValueError(f"Unknown knowledge kind: {kind!r}")
    payload = payload or {}
    if spec.validator:
        return spec.validator(payload)
    return payload


def derive_key(kind: str, payload: Dict[str, Any], fallback: str = "") -> str:
    """Best-effort natural key for a kind. Falls back to `fallback` (or a
    short hash of payload) when the kind has no key_extractor."""
    spec = get_spec(kind)
    if spec and spec.key_extractor:
        k = spec.key_extractor(payload or {})
        if k:
            return k
    if fallback:
        return fallback
    # last-resort: hash of payload so duplicate pasting doesn't overwrite
    import hashlib
    return hashlib.sha1(json.dumps(payload or {}, sort_keys=True).encode()).hexdigest()[:10]


# -- Validators --------------------------------------------------------------

def _require_str(d: Dict[str, Any], key: str, label: Optional[str] = None) -> str:
    val = d.get(key)
    if val is None or not isinstance(val, str) or not val.strip():
        raise ValueError(f"{label or key} is required")
    return val.strip()


def _opt_str(d: Dict[str, Any], key: str, default: str = "") -> str:
    val = d.get(key, default)
    if not isinstance(val, str):
        return default
    return val.strip()


def _validate_branch(payload: Dict[str, Any]) -> Dict[str, Any]:
    name = _require_str(payload, "branch_name", "branch_name")
    category = _opt_str(payload, "category") or "other"
    if category not in ("dev", "release", "feature", "other"):
        category = "other"
    return {
        "branch_name": name,
        "category": category,
        "notes": _opt_str(payload, "notes"),
        "last_build": payload.get("last_build") if isinstance(payload.get("last_build"), dict) else None,
        "last_checked_at": _opt_str(payload, "last_checked_at"),
        "watch_sanitizer": bool(payload.get("watch_sanitizer", True)),
    }


_JIRA_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]+-\d+$")


def _validate_jira_epic(payload: Dict[str, Any]) -> Dict[str, Any]:
    key = _require_str(payload, "issue_key", "issue_key").upper()
    if not _JIRA_KEY_RE.match(key):
        raise ValueError(f"issue_key must look like SW-1234 (got {key!r})")
    return {
        "issue_key": key,
        "summary": _opt_str(payload, "summary"),
        "status": _opt_str(payload, "status"),
        "assignee": _opt_str(payload, "assignee"),
        "priority": _opt_str(payload, "priority"),
        "url": _opt_str(payload, "url"),
        "last_checked_at": _opt_str(payload, "last_checked_at"),
        "notes": _opt_str(payload, "notes"),
    }


def _validate_test_suite(payload: Dict[str, Any]) -> Dict[str, Any]:
    path = _require_str(payload, "suite_path", "suite_path")
    # Reject obvious traversal tricks; the actual scan is sandboxed to SCALER_ROOT.
    if ".." in path.split("/"):
        raise ValueError("suite_path must not contain '..' segments")
    return {
        "suite_path": path,
        "label": _opt_str(payload, "label") or path.split("/")[-1],
        "last_runs": payload.get("last_runs") if isinstance(payload.get("last_runs"), list) else [],
        "last_checked_at": _opt_str(payload, "last_checked_at"),
        "notes": _opt_str(payload, "notes"),
    }


def _validate_spirent(payload: Dict[str, Any]) -> Dict[str, Any]:
    path = _require_str(payload, "session_path", "session_path")
    if ".." in path.split("/"):
        raise ValueError("session_path must not contain '..' segments")
    return {
        "session_path": path,
        "label": _opt_str(payload, "label") or Path(path).stem,
        "stream_count": int(payload.get("stream_count") or 0),
        "device_count": int(payload.get("device_count") or 0),
        "last_run_at": _opt_str(payload, "last_run_at"),
        "last_checked_at": _opt_str(payload, "last_checked_at"),
        "notes": _opt_str(payload, "notes"),
    }


def _validate_device(payload: Dict[str, Any]) -> Dict[str, Any]:
    dev_id = _require_str(payload, "device_id", "device_id")
    return {
        "device_id": dev_id,
        "label": _opt_str(payload, "label") or dev_id,
        "mgmt_ip": _opt_str(payload, "mgmt_ip"),
        "role": _opt_str(payload, "role"),
        "notes": _opt_str(payload, "notes"),
    }


def _validate_note(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": _opt_str(payload, "title") or "Note",
        "markdown": str(payload.get("markdown") or ""),
    }


def _validate_confluence(payload: Dict[str, Any]) -> Dict[str, Any]:
    url = _require_str(payload, "url", "url")
    if not url.startswith(("http://", "https://")):
        raise ValueError("url must be http:// or https://")
    return {
        "url": url,
        "title": _opt_str(payload, "title") or url,
        "description": _opt_str(payload, "description"),
    }


def _validate_cli_preset(payload: Dict[str, Any]) -> Dict[str, Any]:
    query = _require_str(payload, "query", "query")
    return {
        "query": query,
        "category": _opt_str(payload, "category") or "general",
        "description": _opt_str(payload, "description"),
    }


def _validate_bugs_scope(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "jql": _opt_str(payload, "jql"),
        "status_in": [s for s in (payload.get("status_in") or []) if isinstance(s, str)],
        "project": _opt_str(payload, "project"),
        "tags": [t for t in (payload.get("tags") or []) if isinstance(t, str)],
    }


def _validate_ai_scope(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "context_prompt": str(payload.get("context_prompt") or ""),
        "pinned_chat_ids": [c for c in (payload.get("pinned_chat_ids") or []) if isinstance(c, str)],
        "auto_attach_bugs": bool(payload.get("auto_attach_bugs", True)),
    }


# -- Key extractors ----------------------------------------------------------
#
# For most kinds the "natural key" is obvious (branch name, issue key, device
# id). The ones that allow many arbitrary entries per domain (notes, confluence
# links, CLI presets) use a caller-supplied key instead -- we return None here
# to signal "let the caller pick or hash it".

def _k(key: str) -> Callable[[Dict[str, Any]], Optional[str]]:
    return lambda p: (p.get(key) or "").strip() or None


# -- Live-status fetchers ----------------------------------------------------
#
# These run from the REST refresh endpoint AND from the background poller.
# Failures must be non-fatal: return None to mean "couldn't refresh, keep the
# old payload". Each fetcher accepts `viewer` so per-user config (Jira tokens)
# can be consulted.

# Shared Jenkins client singleton.
# The JenkinsClient constructor reads JENKINS_URL / credentials from env on
# first call; there is no per-user state, so we can keep a process-wide
# instance. Access is guarded by a lock because multiple poller tasks and
# REST requests can hit this code path concurrently from different threads
# (asyncio.to_thread dispatches onto the default executor).
_JENKINS_CLIENT_LOCK = threading.Lock()
_JENKINS_CLIENT: Optional[Any] = None
_JENKINS_CLIENT_FAILED = False


def _get_jenkins_client() -> Optional[Any]:
    """Return the shared JenkinsClient, or None if the scaler module is
    unavailable (dev environments without scaler/ on sys.path)."""
    global _JENKINS_CLIENT, _JENKINS_CLIENT_FAILED
    if _JENKINS_CLIENT is not None:
        return _JENKINS_CLIENT
    if _JENKINS_CLIENT_FAILED:
        return None
    with _JENKINS_CLIENT_LOCK:
        if _JENKINS_CLIENT is not None:
            return _JENKINS_CLIENT
        try:
            from scaler.jenkins_integration import JenkinsClient  # type: ignore
        except Exception:
            try:
                from jenkins_integration import JenkinsClient  # type: ignore
            except Exception:
                _JENKINS_CLIENT_FAILED = True
                return None
        try:
            _JENKINS_CLIENT = JenkinsClient()
        except Exception:
            _JENKINS_CLIENT_FAILED = True
            return None
    return _JENKINS_CLIENT


def _fetch_branch_status(viewer: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Resolve latest Jenkins build state for a branch. Uses the shared
    JenkinsClient so 100 attached branches = 100 HTTP calls, not 100
    client constructions."""
    name = (payload or {}).get("branch_name", "")
    if not name:
        return None
    client = _get_jenkins_client()
    if client is None:
        return None
    try:
        build = client.get_build_info(name, latest=True)
        if not build:
            # Branch exists but has never built yet, OR Jenkins doesn't know
            # this branch. Persist "last_checked" so the UI can render
            # "no builds yet" vs. "never synced".
            return {
                **payload,
                "last_build": None,
                "last_checked_at": _now_iso(),
                "last_error": "",
            }
        return {
            **payload,
            "last_build": {
                "number": build.build_number,
                "result": build.result,
                "building": bool(build.building),
                "timestamp": int(build.timestamp or 0),
                "url": build.url,
                "duration_ms": int(build.duration or 0),
                "sanitizer": bool(getattr(build, "is_sanitizer", False)),
                "has_images": bool(getattr(build, "has_image_artifacts", False)),
                "age_hours": float(getattr(build, "age_hours", 0.0)),
                "expired": bool(getattr(build, "is_expired", False)),
            },
            "last_checked_at": _now_iso(),
            "last_error": "",
        }
    except Exception as exc:
        # Return payload + error so the UI can say "sync error" instead of
        # pretending the status is fresh.
        return {
            **payload,
            "last_checked_at": _now_iso(),
            "last_error": str(exc)[:200],
        }


# Per-viewer Jira session cache. Stores:
#   viewer -> {"expires_at": float, "base_url": str, "email": str, "token": str,
#              "session": requests.Session}
# TTL is short so credential rotations take effect within a minute.
_JIRA_CACHE_LOCK = threading.Lock()
_JIRA_CACHE: Dict[str, Dict[str, Any]] = {}
_JIRA_CACHE_TTL_S = 60.0


def _get_jira_context(viewer: str) -> Optional[Dict[str, Any]]:
    """Return a cached (config + HTTP session) bundle for the viewer, or
    None when Jira is not configured. Caches for ``_JIRA_CACHE_TTL_S``
    seconds so 50 rapid /refresh calls reuse a single keepalive socket."""
    if not viewer:
        return None
    now = time.monotonic()
    with _JIRA_CACHE_LOCK:
        entry = _JIRA_CACHE.get(viewer)
        if entry and entry.get("expires_at", 0) > now:
            return entry
        cfg_path = Path.home() / ".topology_users" / viewer / "jira_config.json"
        if not cfg_path.exists():
            _JIRA_CACHE.pop(viewer, None)
            return None
        try:
            cfg = json.loads(cfg_path.read_text())
        except Exception:
            return None
        base_url = (cfg.get("base_url") or "").rstrip("/")
        email = cfg.get("email") or ""
        token = cfg.get("api_token") or ""
        if not base_url or not email or not token:
            _JIRA_CACHE.pop(viewer, None)
            return None
        try:
            import requests  # noqa: WPS433 -- lazy import
            from requests.auth import HTTPBasicAuth
        except Exception:
            return None
        session = requests.Session()
        session.auth = HTTPBasicAuth(email, token)
        session.headers.update({"Accept": "application/json"})
        new_entry = {
            "expires_at": now + _JIRA_CACHE_TTL_S,
            "base_url": base_url,
            "email": email,
            "token": token,
            "session": session,
        }
        # Close the old session if we're replacing it, to free the pool.
        if entry and entry.get("session") is not None:
            try:
                entry["session"].close()
            except Exception:
                pass
        _JIRA_CACHE[viewer] = new_entry
        return new_entry


def _fetch_jira_status(viewer: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Look up a single Jira issue using the viewer's per-user jira_config.

    Jira config location:  ~/.topology_users/<viewer>/jira_config.json
    Expected keys:         base_url, email, api_token
    If missing or the request fails, we leave the payload untouched except
    for `last_checked_at` and `last_error` so the UI can show "sync error"
    instead of pretending the status is fresh.
    """
    issue_key = (payload or {}).get("issue_key", "")
    if not issue_key or not viewer:
        return None
    ctx = _get_jira_context(viewer)
    if not ctx:
        # Preserve whatever state the payload already has and stamp the
        # check time so the freshness indicator ticks over.
        return {
            **payload,
            "last_checked_at": _now_iso(),
            "last_error": "Jira not configured",
        }
    base_url = ctx["base_url"]
    session = ctx["session"]
    try:
        resp = session.get(
            f"{base_url}/rest/api/3/issue/{issue_key}"
            f"?fields=summary,status,assignee,priority,issuetype",
            timeout=10,
        )
        if resp.status_code == 404:
            return {
                **payload,
                "last_checked_at": _now_iso(),
                "last_error": "Issue not found",
            }
        if resp.status_code == 401:
            # Credentials rotated -- invalidate the cache so the next call
            # re-reads jira_config.json.
            with _JIRA_CACHE_LOCK:
                _JIRA_CACHE.pop(viewer, None)
            return {
                **payload,
                "last_checked_at": _now_iso(),
                "last_error": "Jira auth failed (rotate token?)",
            }
        resp.raise_for_status()
        data = resp.json() or {}
        fields = data.get("fields") or {}
        status = (fields.get("status") or {}).get("name") or ""
        assignee_field = fields.get("assignee") or {}
        assignee = assignee_field.get("displayName") or assignee_field.get("emailAddress") or ""
        priority = (fields.get("priority") or {}).get("name") or ""
        summary = fields.get("summary") or ""
        return {
            **payload,
            "summary": summary,
            "status": status,
            "assignee": assignee,
            "priority": priority,
            "url": f"{base_url}/browse/{issue_key}",
            "last_checked_at": _now_iso(),
            "last_error": "",
        }
    except Exception as e:
        return {**payload, "last_checked_at": _now_iso(), "last_error": str(e)[:200]}


def _fetch_test_suite_status(viewer: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Scan `scaler/TEST/catalog/<suite>/results/` for the last 5 RUN_* folders."""
    suite_path = (payload or {}).get("suite_path", "")
    if not suite_path:
        return None
    base = _scaler_root()
    if not base:
        return None
    target = (base / suite_path).resolve()
    try:
        target.relative_to(base.resolve())
    except ValueError:
        return None
    if not target.is_dir():
        return {**payload, "last_checked_at": _now_iso(), "last_error": "Suite not found"}
    results_dir = target / "results"
    runs: List[Dict[str, Any]] = []
    if results_dir.is_dir():
        entries = sorted(
            [p for p in results_dir.iterdir() if p.is_dir() and p.name.startswith("RUN_")],
            key=lambda p: p.name, reverse=True,
        )[:5]
        for r in entries:
            verdict = _read_suite_verdict(r)
            runs.append({
                "run_id": r.name,
                "verdict": verdict,
                "mtime": int(r.stat().st_mtime) if r.exists() else 0,
            })
    return {
        **payload,
        "last_runs": runs,
        "last_checked_at": _now_iso(),
        "last_error": "",
    }


def _read_suite_verdict(run_dir: Path) -> str:
    """Very light verdict parser -- we look for a top-level verdict.json or
    summary.json and extract .verdict / .status. Anything else shows 'unknown'."""
    for name in ("verdict.json", "summary.json", "result.json"):
        p = run_dir / name
        if not p.is_file():
            continue
        try:
            data = json.loads(p.read_text())
            v = data.get("verdict") or data.get("status") or ""
            if isinstance(v, str) and v:
                return v
        except Exception:
            continue
    return "unknown"


def _fetch_spirent_status(viewer: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Open the Spirent session JSON and count streams/devices."""
    path = (payload or {}).get("session_path", "")
    if not path:
        return None
    base = _scaler_root()
    if not base:
        return None
    target = (base / path).resolve()
    try:
        target.relative_to(base.resolve())
    except ValueError:
        return None
    if not target.is_file():
        return {**payload, "last_checked_at": _now_iso(), "last_error": "Session not found"}
    try:
        data = json.loads(target.read_text())
    except Exception as e:
        return {**payload, "last_checked_at": _now_iso(), "last_error": str(e)[:200]}

    streams = data.get("streams") or data.get("stream_blocks") or []
    devices = data.get("devices") or data.get("emulated_devices") or []
    return {
        **payload,
        "stream_count": len(streams) if isinstance(streams, list) else 0,
        "device_count": len(devices) if isinstance(devices, list) else 0,
        "last_run_at": data.get("last_run_at") or data.get("last_run") or "",
        "last_checked_at": _now_iso(),
        "last_error": "",
    }


# -- Helpers -----------------------------------------------------------------

def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _scaler_root() -> Optional[Path]:
    """Where the scaler/ subtree lives at runtime. Tries (in order):
      1. $SCALER_ROOT env var (set by scaler_bridge on boot)
      2. ~/SCALER (deploy target for the live server)
      3. sibling `scaler/` next to this package root (dev checkout)
    Returns None if nothing exists.
    """
    from_env = os.environ.get("SCALER_ROOT", "").strip()
    candidates = []
    if from_env:
        candidates.append(Path(from_env))
    candidates.append(Path.home() / "SCALER")
    here = Path(__file__).resolve()
    repo = here.parents[3]  # topology/api/domains/knowledge.py -> topology -> repo root
    candidates.append(repo / "scaler")
    for c in candidates:
        if c and c.is_dir():
            return c
    return None


# -- Register all kinds ------------------------------------------------------

register(KnowledgeKindSpec(
    kind="branch", label="Feature Branch",
    description="Jenkins branch -- build status, sanitizer flag, one-click upgrade",
    supports_live=True, live_fetcher=_fetch_branch_status,
    validator=_validate_branch, key_extractor=_k("branch_name"),
))

register(KnowledgeKindSpec(
    kind="jira_epic", label="Jira Issue",
    description="Jira EPIC or ticket -- live summary, status, assignee",
    supports_live=True, live_fetcher=_fetch_jira_status,
    validator=_validate_jira_epic, key_extractor=_k("issue_key"),
))

register(KnowledgeKindSpec(
    kind="test_suite", label="Test Suite",
    description="Link to scaler/TEST/catalog/<suite>/ -- last 5 RUN_* results",
    supports_live=True, live_fetcher=_fetch_test_suite_status,
    validator=_validate_test_suite, key_extractor=_k("suite_path"),
))

register(KnowledgeKindSpec(
    kind="spirent", label="Spirent Session",
    description="scaler/SPIRENT/sessions/*.json -- stream count, last run",
    supports_live=True, live_fetcher=_fetch_spirent_status,
    validator=_validate_spirent, key_extractor=_k("session_path"),
))

register(KnowledgeKindSpec(
    kind="device", label="Device",
    description="Explicit device roster (orthogonal to canvas devices)",
    supports_live=False, validator=_validate_device, key_extractor=_k("device_id"),
))

register(KnowledgeKindSpec(
    kind="note", label="Note",
    description="Markdown runbook or scratchpad",
    supports_live=False, validator=_validate_note,
))

register(KnowledgeKindSpec(
    kind="confluence", label="Confluence Link",
    description="Confluence / external spec URL",
    supports_live=False, validator=_validate_confluence, key_extractor=_k("url"),
))

register(KnowledgeKindSpec(
    kind="cli_preset", label="DNOS CLI Preset",
    description="Pinned search_cli_docs query or show-command snippet",
    supports_live=False, validator=_validate_cli_preset, key_extractor=_k("query"),
))

register(KnowledgeKindSpec(
    kind="bugs_scope", label="Bug Filter",
    description="Scope __bugs section to this domain (JQL / status filter)",
    supports_live=False, validator=_validate_bugs_scope,
))

register(KnowledgeKindSpec(
    kind="ai_scope", label="AI Context",
    description="AI-assistant context prompt + pinned chats for this domain",
    supports_live=False, validator=_validate_ai_scope,
))


# -- Public API --------------------------------------------------------------

def all_kinds() -> List[Dict[str, Any]]:
    """Serialize the registry for the frontend (UI uses this to render tabs)."""
    return [
        {
            "kind": s.kind,
            "label": s.label,
            "description": s.description,
            "supports_live": s.supports_live,
            "allows_multiple": s.kind not in {"bugs_scope", "ai_scope"},
        }
        for s in sorted(REGISTRY.values(), key=lambda x: x.kind)
    ]


def refresh_payload(viewer: str, kind: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Run the live fetcher for a kind (if any). Returns the new payload or
    None if the kind does not support live refresh."""
    spec = get_spec(kind)
    if not spec or not spec.supports_live or not spec.live_fetcher:
        return None
    try:
        return spec.live_fetcher(viewer, payload or {})
    except Exception:
        return None
