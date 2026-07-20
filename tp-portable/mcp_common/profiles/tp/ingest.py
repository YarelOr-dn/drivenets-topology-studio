"""Epic ingest from Jira via REST client."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from mcp_common.profiles.tp.jira_client import JiraClientError, resolve_backend
from mcp_common.profiles.tp.tp_env import atomic_write_json, resolve_epic_dir


_ENABLER_LINK_TYPES = re.compile(
    r"is blocked by|blocks|depends on|is cloned by|clones",
    re.I,
)


def _is_enabler(summary: str, link_type: str) -> bool:
    if "enabler" in summary.lower():
        return True
    return bool(_ENABLER_LINK_TYPES.search(link_type or ""))


def _fetch_epic(backend, key: str) -> dict[str, Any]:
    return backend.get_issue(key, fields=["summary", "description", "issuelinks", "issuetype"])


def _fetch_user_stories(backend, epic_key: str) -> list[dict[str, Any]]:
    jql = (
        f'parent in ({epic_key}) AND issuetype = "User story" '
        f'AND status not in (Reject, Rejected)'
    )
    data = backend.search_jql(jql, max_results=200, fields=["summary", "description", "status"])
    return list(data.get("issues") or [])


def _discover_enablers(backend, epic_issue: dict[str, Any]) -> list[str]:
    enablers: list[str] = []
    fields = epic_issue.get("fields") or {}
    for link in fields.get("issuelinks") or []:
        outward = link.get("outwardIssue") or {}
        inward = link.get("inwardIssue") or {}
        ltype = (link.get("type") or {}).get("name") or ""
        for issue in (outward, inward):
            key = issue.get("key")
            if not key or key == epic_issue.get("key"):
                continue
            summary = (issue.get("fields") or {}).get("summary") or ""
            itype = ((issue.get("fields") or {}).get("issuetype") or {}).get("name") or ""
            if itype == "Epic" and _is_enabler(summary, ltype):
                enablers.append(key)
    return sorted(set(enablers))


def ingest_epic(epic: str, linked: list[str] | None = None) -> dict[str, Any]:
    epic = epic.upper()
    backend = resolve_backend()
    if not backend.available():
        return {"ok": False, "error": "No Jira backend available; set JIRA_API_TOKEN + JIRA_USER_EMAIL"}

    epic_dir = resolve_epic_dir(epic)
    epic_dir.mkdir(parents=True, exist_ok=True)

    try:
        epic_issue = _fetch_epic(backend, epic)
    except JiraClientError as exc:
        return {"ok": False, "error": str(exc)}

    enablers = _discover_enablers(backend, epic_issue)
    if linked:
        enablers = sorted(set(enablers + [k.upper() for k in linked]))

    stories: list[dict[str, Any]] = []
    story_bodies: list[str] = []
    ingested_epics = [epic]

    for ek in [epic] + enablers:
        if ek not in ingested_epics:
            ingested_epics.append(ek)
        for story in _fetch_user_stories(backend, ek):
            key = story.get("key", "")
            fields = story.get("fields") or {}
            body = fields.get("description") or ""
            stories.append({"key": key, "epic": ek, "summary": fields.get("summary"), "body": body})
            story_bodies.append(f"## {key}\n{body}\n")

    enabler_sweep = {"enablers": [{"key": k, "source": "auto-discovery"} for k in enablers]}
    sources = {"ingested_epics": ingested_epics, "primary": epic}
    epic_doc = f"# Epic {epic}\n\n{(epic_issue.get('fields') or {}).get('description') or ''}\n"

    atomic_write_json(epic_dir / "enabler_sweep.json", enabler_sweep)
    atomic_write_json(epic_dir / "sources_ingested.json", sources)
    (epic_dir / "epic_documentation_{}.md".format(epic)).write_text(epic_doc, encoding="utf-8")
    (epic_dir / "user_story_bodies.md").write_text("\n".join(story_bodies), encoding="utf-8")
    atomic_write_json(epic_dir / "must_requirements.json", {"requirements": [], "stories": stories})

    return {
        "ok": True,
        "epic": epic,
        "enablers": enablers,
        "story_count": len(stories),
        "epic_dir": str(epic_dir),
        "backend": backend.name,
    }
