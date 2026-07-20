"""
EPIC pre-fetch module -- retrieves Jira EPIC data via REST API.

Pre-fetches EPIC details, user stories, comments, issue links, and related
SW-* keys for multi-epic / enabler correlation (QA TP pipeline).
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import httpx

JIRA_URL = os.getenv("JIRA_URL", "https://drivenets.atlassian.net").rstrip("/")
JIRA_USERNAME = os.getenv("JIRA_USERNAME", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")

CACHE_DIR = Path.home() / "SCALER" / "TEST" / "tp" / ".cache"

# Child search fields (description + labels for TP generation)
_CHILD_FIELDS = [
    "summary",
    "status",
    "issuetype",
    "description",
    "assignee",
    "labels",
    "parent",
]
_EPIC_FIELDS = [
    "summary",
    "status",
    "issuetype",
    "description",
    "labels",
    "issuelinks",
    "attachment",
    "parent",
    "components",
    "fixVersions",
    "reporter",
]


def extract_epic_ids(text: str) -> List[str]:
    """Extract Jira SW epic/issue IDs from text."""
    if not text:
        return []
    return list(dict.fromkeys(re.findall(r"SW-\d{4,6}", text)))


def _flatten_adf(node: Any) -> str:
    """Recursively flatten Atlassian Document Format to plain text."""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        if node.get("type") == "text":
            return node.get("text", "")
        content = node.get("content", [])
        parts = [_flatten_adf(c) for c in content]
        sep = "\n" if node.get("type") in (
            "paragraph",
            "heading",
            "bulletList",
            "orderedList",
            "listItem",
        ) else ""
        return sep.join(parts)
    if isinstance(node, list):
        return "\n".join(_flatten_adf(item) for item in node)
    return ""


def _issue_description_plain(fields: Dict[str, Any]) -> str:
    desc = fields.get("description")
    if not desc:
        return ""
    return _flatten_adf(desc).strip()


def _classify_enabler(link_type: str, inward: str, outward: str, summary: str) -> Optional[str]:
    t = f"{link_type} {inward} {outward} {summary}".lower()
    if "dp" in t and "enabl" in t:
        return "dp_enabler"
    if "infra" in t and "enabl" in t:
        return "infra_enabler"
    if "qos" in t and "enabl" in t:
        return "qos_enabler"
    if "neighbor" in t or "nm" in t:
        if "enabl" in t:
            return "nm_enabler"
    if "depend" in t:
        return "dependent"
    if "parent" in link_type.lower() or "child" in link_type.lower():
        return "hierarchy"
    if "blocks" in link_type.lower() or "block" in link_type.lower():
        return "blocks"
    if "relates" in link_type.lower():
        return "relates"
    return None


async def _jira_get_json(client: httpx.AsyncClient, path: str, **kwargs) -> Any:
    auth = (JIRA_USERNAME, JIRA_API_TOKEN) if JIRA_USERNAME and JIRA_API_TOKEN else None
    headers = {"Accept": "application/json"}
    resp = await client.get(f"{JIRA_URL}{path}", auth=auth, headers=headers, **kwargs)
    resp.raise_for_status()
    return resp.json()


async def _jira_post_json(client: httpx.AsyncClient, path: str, body: dict) -> Any:
    auth = (JIRA_USERNAME, JIRA_API_TOKEN) if JIRA_USERNAME and JIRA_API_TOKEN else None
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    resp = await client.post(
        f"{JIRA_URL}{path}", json=body, auth=auth, headers=headers
    )
    resp.raise_for_status()
    return resp.json()


async def _fetch_comments(
    client: httpx.AsyncClient, issue_key: str, max_results: int = 40
) -> List[Dict[str, Any]]:
    """Fetch newest comments first (bounded)."""
    try:
        data = await _jira_get_json(
            client,
            f"/rest/api/3/issue/{issue_key}/comment",
            params={
                "maxResults": max_results,
                "orderBy": "-created",
                "expand": "renderedBody",
            },
        )
    except httpx.HTTPStatusError:
        return []
    out: List[Dict[str, Any]] = []
    for c in data.get("comments", []) or []:
        body = c.get("body")
        text = _flatten_adf(body) if body else ""
        author = (c.get("author") or {}).get("displayName", "")
        out.append(
            {
                "id": c.get("id"),
                "author": author,
                "created": c.get("created"),
                "body_plain": text[:8000],
            }
        )
    return out


async def _fetch_issue_brief(client: httpx.AsyncClient, key: str) -> Dict[str, Any]:
    try:
        data = await _jira_get_json(
            client,
            f"/rest/api/3/issue/{key}",
            params={"fields": "summary,status,issuetype,description"},
        )
    except httpx.HTTPStatusError:
        return {"key": key, "error": "not_found_or_forbidden"}
    f = data.get("fields", {})
    return {
        "key": key,
        "summary": f.get("summary", ""),
        "status": (f.get("status") or {}).get("name", ""),
        "type": (f.get("issuetype") or {}).get("name", ""),
        "description_plain": _issue_description_plain(f)[:12000],
    }


async def fetch_epic(epic_id: str) -> Dict[str, Any]:
    """Fetch EPIC details, children, comments, links, and related SW keys."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{epic_id}_v2.json"

    if cache_file.exists():
        cached = json.loads(cache_file.read_text())
        cached_at = cached.get("fetched_at", "")
        if cached_at:
            try:
                age = (datetime.now() - datetime.fromisoformat(cached_at)).total_seconds()
                if age < 3600:
                    return cached
            except ValueError:
                pass

    if not JIRA_USERNAME or not JIRA_API_TOKEN:
        return {
            "epic_id": epic_id,
            "error": "JIRA_USERNAME and JIRA_API_TOKEN must be set for epic prefetch",
            "name": "",
            "fetched_at": datetime.now().isoformat(),
        }

    fields_param = ",".join(_EPIC_FIELDS)
    auth = (JIRA_USERNAME, JIRA_API_TOKEN)
    headers = {"Accept": "application/json"}

    async with httpx.AsyncClient(timeout=90.0) as client:
        epic_resp = await client.get(
            f"{JIRA_URL}/rest/api/3/issue/{epic_id}",
            auth=auth,
            headers=headers,
            params={"fields": fields_param},
        )
        epic_resp.raise_for_status()
        epic_data = epic_resp.json()

        jql = f'"Epic Link" = {epic_id} OR parent = {epic_id} ORDER BY key ASC'
        try:
            children_data = await _jira_post_json(
                client,
                "/rest/api/3/search/jql",
                {
                    "jql": jql,
                    "maxResults": 200,
                    "fields": _CHILD_FIELDS,
                },
            )
        except httpx.HTTPStatusError:
            children_resp = await client.get(
                f"{JIRA_URL}/rest/api/2/search",
                auth=auth,
                headers=headers,
                params={
                    "jql": jql,
                    "maxResults": 200,
                    "fields": ",".join(_CHILD_FIELDS),
                },
            )
            children_resp.raise_for_status()
            children_data = children_resp.json()

        epic_comments_task = asyncio.create_task(_fetch_comments(client, epic_id, 50))
        fields = epic_data.get("fields", {})
        description_full = _issue_description_plain(fields)

        user_stories: List[Dict[str, Any]] = []
        sub_tasks: List[Dict[str, Any]] = []
        for issue in children_data.get("issues", []) or []:
            f = issue.get("fields", {})
            itype = (f.get("issuetype") or {}).get("name", "")
            desc_plain = _issue_description_plain(f)
            item = {
                "key": issue["key"],
                "summary": f.get("summary", ""),
                "status": (f.get("status") or {}).get("name", "Unknown"),
                "type": itype,
                "assignee": (f.get("assignee") or {}).get("displayName", "Unassigned"),
                "labels": f.get("labels", []),
                "description_plain": desc_plain,
                "description_preview": desc_plain[:2000],
            }
            if itype in ("Story", "User story", "User Story"):
                user_stories.append(item)
            else:
                sub_tasks.append(item)

        # Comments on user stories (bounded concurrency)
        sem = asyncio.Semaphore(6)

        async def _us_comments(us: Dict[str, Any]) -> None:
            async with sem:
                us["comments"] = await _fetch_comments(client, us["key"], 15)

        await asyncio.gather(*[_us_comments(us) for us in user_stories[:40]])

        epic_comments = await epic_comments_task

        # Issue links -> related keys + enabler hints
        issuelinks_raw = fields.get("issuelinks") or []
        linked_issues: List[Dict[str, Any]] = []
        linked_keys: Set[str] = set()
        for link in issuelinks_raw:
            lt = (link.get("type") or {}).get("name", "")
            inward = (link.get("type") or {}).get("inward", "")
            outward = (link.get("type") or {}).get("outward", "")
            other = link.get("outwardIssue") or link.get("inwardIssue")
            if not other:
                continue
            okey = other.get("key")
            if not okey or not str(okey).startswith("SW-"):
                continue
            osum = (other.get("fields") or {}).get("summary", "")
            linked_keys.add(okey)
            role = _classify_enabler(lt, inward, outward, osum or "")
            linked_issues.append(
                {
                    "key": okey,
                    "summary": osum,
                    "link_type": lt,
                    "inward": inward,
                    "outward": outward,
                    "enabler_role_guess": role,
                }
            )

        # Fetch brief details for linked SW issues (cap)
        brief_tasks = []
        for k in list(linked_keys)[:20]:
            brief_tasks.append(_fetch_issue_brief(client, k))
        linked_brief = await asyncio.gather(*brief_tasks) if brief_tasks else []

        related_sw: Set[str] = set(extract_epic_ids(description_full))
        for c in epic_comments:
            related_sw.update(extract_epic_ids(c.get("body_plain", "")))
        for us in user_stories:
            related_sw.update(extract_epic_ids(us.get("description_plain", "")))
            for c in us.get("comments") or []:
                related_sw.update(extract_epic_ids(c.get("body_plain", "")))
        for li in linked_issues:
            related_sw.add(li["key"])
            related_sw.update(extract_epic_ids(li.get("summary", "")))
        related_sw.discard(epic_id)

        attachments = []
        for a in fields.get("attachment") or []:
            attachments.append(
                {
                    "filename": a.get("filename"),
                    "size": a.get("size"),
                    "mimeType": a.get("mimeType"),
                    "content": a.get("content"),
                }
            )

        parent = fields.get("parent")
        parent_info = None
        if parent:
            parent_info = {
                "key": parent.get("key"),
                "summary": (parent.get("fields") or {}).get("summary", ""),
            }

        components = [
            (c or {}).get("name", "") for c in (fields.get("components") or [])
        ]
        fix_versions = [
            (v or {}).get("name", "") for v in (fields.get("fixVersions") or [])
        ]

        result: Dict[str, Any] = {
            "epic_id": epic_id,
            "name": fields.get("summary", ""),
            "description": description_full[:5000],
            "description_full": description_full,
            "description_preview": description_full[:5000],
            "status": (fields.get("status") or {}).get("name", "Unknown"),
            "labels": fields.get("labels", []),
            "components": components,
            "fix_versions": fix_versions,
            "parent": parent_info,
            "attachments": attachments,
            "epic_comments": epic_comments,
            "issuelinks": linked_issues,
            "linked_issues_brief": list(linked_brief),
            "related_sw_keys": sorted(related_sw),
            "user_stories": user_stories,
            "sub_tasks": sub_tasks,
            "total_children": len(user_stories) + len(sub_tasks),
            "fetched_at": datetime.now().isoformat(),
            "cache_schema_version": 2,
        }

    cache_file.write_text(json.dumps(result, indent=2))
    # Keep legacy cache name for older consumers
    legacy = CACHE_DIR / f"{epic_id}.json"
    try:
        legacy.write_text(json.dumps(result, indent=2))
    except OSError:
        pass
    return result
