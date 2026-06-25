"""Bug-explanation topology creation tools.

The GUI already owns the Jira parsing and simplified canvas schema through
``POST /api/bugs/from-jira``.  Keep the MCP path on that same backend contract
so the orange ``+ Bug`` button and the Topology MCP produce identical files in
the authenticated user's built-in ``__bugs`` domain.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from api.auth.service import create_access_token
from api.auth.user_store import user_store


def _serve_base_url() -> str:
    return os.environ.get("TOPOLOGY_SERVE_URL", "http://127.0.0.1:8080").rstrip("/")


def _add_optional(payload: Dict[str, Any], key: str, value: Any) -> None:
    if value is None:
        return
    if isinstance(value, str) and not value.strip():
        return
    if isinstance(value, (list, dict)) and not value:
        return
    payload[key] = value


def _read_json_error(exc: urllib.error.HTTPError) -> Dict[str, Any]:
    try:
        body = exc.read().decode("utf-8", errors="replace")
        parsed = json.loads(body) if body else {}
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    return {"error": str(exc)}


def topology_create_bug_topology(
    username: str,
    sw_id: str,
    title: str = "",
    summary: str = "",
    devices: Optional[List[Dict[str, Any]]] = None,
    vrfs: Optional[List[Dict[str, Any]]] = None,
    route: Optional[Dict[str, Any]] = None,
    failure_device: str = "",
    force_placeholder: bool = False,
    force_non_bug: bool = False,
) -> Dict[str, Any]:
    """Create a simplified Jira bug explanation topology in the user's Bugs domain.

    ``sw_id`` is the only required input. Optional overrides match the GUI
    endpoint: title, summary, devices, VRFs, route, failure device, and the
    explicit force flags for placeholder/non-bug tickets.
    """
    normalized = (sw_id or "").strip().upper()
    if not normalized:
        raise ValueError("sw_id is required")
    user = user_store.get_user(username)
    if not user:
        return {"ok": False, "error": "authenticated MCP user was not found"}

    payload: Dict[str, Any] = {
        "sw_id": normalized,
        "force_placeholder": bool(force_placeholder),
        "force_non_bug": bool(force_non_bug),
    }
    _add_optional(payload, "title", title)
    _add_optional(payload, "summary", summary)
    _add_optional(payload, "devices", devices)
    _add_optional(payload, "vrfs", vrfs)
    _add_optional(payload, "route", route)
    _add_optional(payload, "failure_device", failure_device)

    token = create_access_token(username, str(user.get("role") or "engineer"))
    req = urllib.request.Request(
        _serve_base_url() + "/api/bugs/from-jira",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = _read_json_error(exc)
        return {
            "ok": False,
            "status": exc.code,
            "code": detail.get("code") or "",
            "error": detail.get("error") or detail.get("detail") or str(exc),
            "result": detail,
        }
    except Exception as exc:  # noqa: BLE001 - MCP should return structured errors
        return {
            "ok": False,
            "error": f"bug topology generator unavailable: {exc}",
            "serve_url": _serve_base_url(),
        }

    return {
        "ok": bool(result.get("ok")),
        "section_id": result.get("section_id") or "__bugs",
        "filename": result.get("filename") or "",
        "name": result.get("name") or "",
        "sw_id": result.get("sw_id") or normalized,
        "source": result.get("source") or "",
        "issue_type": result.get("issue_type") or "",
        "is_bug_like": bool(result.get("is_bug_like")),
        "forced_non_bug": bool(result.get("forced_non_bug")),
        "jira_error": result.get("jira_error") or "",
        "message": "Saved simplified bug topology in the Bugs domain.",
        "result": result,
    }
