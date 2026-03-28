#!/usr/bin/env python3
"""Search Jira for known bugs matching test failure symptoms.

Uses a callback pattern for the MCP call so the module stays testable
without a live MCP connection. The orchestrator provides the callback
that wraps `atlassian_jira_search`.

Typical flow:
  1. Orchestrator detects FAIL verdict
  2. Calls search_known_bugs() with failed layers + error keywords
  3. Module builds JQL, calls the Jira callback
  4. Parses results, scores by keyword overlap
  5. Returns ranked BugMatch list attached to the verdict
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

JiraSearchFn = Callable[[str, str, int], str]

LAYER_KEYWORDS: Dict[str, str] = {
    "control_plane": "mac-table source local remote evpn learning",
    "sequencing": "sequence number mac mobility RFC 8560",
    "rt2": "RT-2 type-2 update withdraw mac evpn",
    "suppression": "mac suppress frozen duplicate loop detection flap",
    "sticky": "sticky mac enforcement reject move static",
    "scale": "mac scale 64k performance count",
    "timing": "mac convergence slow timeout timer",
    "ha": "mac recovery switchover restart HA warm ncc",
    "datapath": "forwarding mac traffic loss datapath NCP wb_agent",
    "bgp_session": "bgp session notification established clear",
    "traces": "crash error core dump fatal",
}


@dataclass
class BugMatch:
    jira_key: str
    title: str
    status: str
    priority: str
    match_score: float
    matching_keywords: List[str] = field(default_factory=list)
    url: str = ""


def _build_jql(
    failed_layers: List[str],
    feature: str,
    extra_keywords: Optional[List[str]] = None,
) -> str:
    """Build a JQL query from failure context."""
    kw_parts: List[str] = []
    for layer in failed_layers:
        layer_kws = LAYER_KEYWORDS.get(layer, layer)
        top_words = layer_kws.split()[:3]
        kw_parts.extend(top_words)

    if extra_keywords:
        kw_parts.extend(extra_keywords[:5])

    kw_parts = list(dict.fromkeys(kw_parts))[:8]
    text_query = " ".join(kw_parts)

    jql = (
        f'text ~ "{text_query}" AND type = Bug '
        f'AND status not in (Closed, Done) '
        f'ORDER BY updated DESC'
    )
    return jql


def _score_result(
    summary: str,
    description: str,
    failed_layers: List[str],
    error_keywords: List[str],
) -> tuple:
    """Score a Jira result by keyword overlap. Returns (score, matching_keywords)."""
    haystack = (summary + " " + description).lower()
    matching: List[str] = []

    all_keywords: List[str] = []
    for layer in failed_layers:
        all_keywords.extend(LAYER_KEYWORDS.get(layer, "").split())
    all_keywords.extend(error_keywords)

    for kw in set(all_keywords):
        if kw.lower() in haystack:
            matching.append(kw)

    score = len(matching) / max(len(set(all_keywords)), 1)
    return score, matching


def search_known_bugs(
    failed_layers: List[str],
    feature: str,
    error_keywords: List[str],
    jira_search_fn: JiraSearchFn,
    max_results: int = 5,
) -> List[BugMatch]:
    """Search Jira for bugs matching failure symptoms.

    Args:
        failed_layers: List of verdict layer names that failed.
        feature: Feature area (e.g. "evpn-mac-mobility").
        error_keywords: Keywords from trace analysis (e.g. ["NOTIFICATION", "frozen"]).
        jira_search_fn: Callback(jql, fields, limit) -> JSON string of results.
        max_results: Max bugs to return.

    Returns:
        List of BugMatch sorted by match_score descending.
    """
    jql = _build_jql(failed_layers, feature, error_keywords)
    fields = "summary,status,priority,description"

    try:
        raw = jira_search_fn(jql, fields, max_results * 2)
    except Exception:
        return []

    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return []

    issues = data.get("issues", [])
    if not issues and isinstance(data, list):
        issues = data

    matches: List[BugMatch] = []
    for issue in issues:
        if isinstance(issue, str):
            continue
        key = issue.get("key", "")
        fields_data = issue.get("fields", issue)
        summary = fields_data.get("summary", "")
        status_obj = fields_data.get("status", {})
        status = status_obj.get("name", str(status_obj)) if isinstance(status_obj, dict) else str(status_obj)
        prio_obj = fields_data.get("priority", {})
        priority = prio_obj.get("name", str(prio_obj)) if isinstance(prio_obj, dict) else str(prio_obj)
        desc = fields_data.get("description", "") or ""
        if isinstance(desc, dict):
            desc = json.dumps(desc)

        score, matching = _score_result(summary, desc, failed_layers, error_keywords)

        if score > 0.05:
            matches.append(BugMatch(
                jira_key=key,
                title=summary,
                status=status,
                priority=priority,
                match_score=round(score, 3),
                matching_keywords=matching,
                url=f"https://drivenets.atlassian.net/browse/{key}",
            ))

    matches.sort(key=lambda m: m.match_score, reverse=True)
    return matches[:max_results]


def format_bug_matches(matches: List[BugMatch]) -> str:
    """Format bug matches for human-readable output."""
    if not matches:
        return "No matching known bugs found in Jira."

    lines = [f"Found {len(matches)} potentially related bug(s):"]
    for i, m in enumerate(matches, 1):
        lines.append(
            f"  {i}. {m.jira_key}: {m.title} "
            f"[{m.status}] [{m.priority}] "
            f"(score: {m.match_score:.1%}, keywords: {', '.join(m.matching_keywords[:5])})"
        )
        lines.append(f"     {m.url}")
    return "\n".join(lines)
