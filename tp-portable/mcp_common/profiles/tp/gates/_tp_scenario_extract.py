#!/usr/bin/env python3
"""Source-agnostic scenario inventory extractor for /TP.

Hybrid design = DETERMINISTIC backbone + bounded AGENT layer:
  DETERMINISTIC (this script, no LLM at run time):
    - HLD / Confluence markdown (optional): Group A-N items, operational flows
    - must_requirements.json: MUST/SHALL clauses (deduped by id)
    - jira_user_stories.json (optional): first-class US-<key> items
    - jira_children.json (optional): Test Category / Testing Task issues
  AGENT (bounded, validated, reconciled):
    - scenario_inventory_agent.json: scenarios the agent found by READING the
      HLD that the regex missed. Every agent item is schema-validated and gets
      source="agent"; the coverage gate still hard-fails if unmapped.
    - scenario_inventory_overrides.json: explicit waive/patch/remove decisions.

The extractor also emits a deterministic SELF-AUDIT (`--audit` or
scenario_audit_<EPIC>.json) that flags HLD headings/regions which produced ZERO
scenarios, so the agent knows exactly where to look for blind spots.

Usage:
    python3 _tp_scenario_extract.py --epic SW-211037
    python3 _tp_scenario_extract.py --epic SW-211037 --hld-file /path/to/hld.md
    python3 _tp_scenario_extract.py --epic SW-211037 --audit   # print blind spots

Exit 0 = inventory written (may be empty -> graceful degrade for coverage gate).
Exit 2 = epic dir missing / unrecoverable error.
Exit 3 = agent-contributed file failed schema validation (fix and re-run).
"""

from __future__ import annotations

from _tp_paths import default_data_dir
import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


# Patterns for HLD-style scenario headings / bullets
_RE_GROUP = re.compile(r"^###\s+Group\s+([A-Z](?:\s*[/-]\s*[A-Z])?)\s*[—\-]", re.I | re.M)
_RE_GROUP_ITEM = re.compile(
    r"^[-*]\s+\*\*([A-Z]\d*[a-z]?)\*\*\s*(.+)$", re.M
)
_RE_HEADING_ITEM = re.compile(
    r"^####\s+([A-Z]\d*[a-z]?)\s*[:\-—]\s*(.+)$", re.M
)
_RE_OP_FLOW = re.compile(
    r"^#{2,3}\s+(?:Operational\s+Flow|Use-case|Use case)\s*[:\-—]?\s*(.+)$",
    re.I | re.M,
)
_RE_OP_SUB = re.compile(r"^####\s+(.+)$", re.M)
_RE_MUST_LINE = re.compile(
    r"\b(MUST|SHALL|REQUIRED|MANDATORY)\b", re.I
)
# Negative acceptance criteria / commit-validations frequently hide inside a
# user-story or HLD BODY (e.g. "VPLS and Proxy-IGMP snooping are mutually
# exclusive; a commit validation shall check ..."). Story-KEY-level inventory
# misses these, so mine them into first-class scenarios. (Root-cause fix for the
# SW-253861 VPLS-SI mutual-exclusion miss.)
_RE_VALIDATION_LINE = re.compile(
    r"\b(mutually exclusive|commit validation|shall (?:check|reject|not)|"
    r"is rejected|are rejected|not allowed together|must not .* together|"
    r"cannot .* together|rejected by commit)\b",
    re.I,
)
_WAIVE_MARKERS = re.compile(
    r"\b(TBD|no need|not needed|out of scope|waived|LLGR|NSR/LLGR)\b", re.I
)


def _atomic_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def _scenario(
    scenario_id: str,
    text: str,
    *,
    source: str,
    kind: str,
    group: str = "",
    status: str = "needs-coverage",
    waive_reason: str = "",
) -> dict[str, Any]:
    st = status
    wr = waive_reason
    if _WAIVE_MARKERS.search(text) and st == "needs-coverage":
        st = "waived"
        wr = wr or _WAIVE_MARKERS.search(text).group(0)  # type: ignore[union-attr]
    return {
        "scenario_id": scenario_id,
        "source": source,
        "kind": kind,
        "group": group,
        "text": text.strip(),
        "status": st,
        "waive_reason": wr if st == "waived" else "",
    }


def _slug_id(prefix: str, title: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", title.strip()).strip("-").upper()
    slug = slug[:48] if slug else "UNNAMED"
    return f"{prefix}-{slug}"


def extract_from_hld_markdown(text: str, source: str = "hld") -> list[dict[str, Any]]:
    """Parse HLD / test-matrix markdown into normalized scenarios."""
    if not text or not text.strip():
        return []

    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    current_group = ""

    for m in _RE_GROUP.finditer(text):
        current_group = m.group(1).replace(" ", "").split("/")[0].upper()

    # Group items like **A1** description
    for m in _RE_GROUP_ITEM.finditer(text):
        sid = m.group(1)  # preserve D2a/D2b casing
        body = m.group(2).strip()
        grp = sid[0] if sid else current_group
        if sid in seen:
            continue
        seen.add(sid)
        out.append(_scenario(sid, body, source=source, kind="hld_group_item", group=grp))

    # #### A1 - description
    for m in _RE_HEADING_ITEM.finditer(text):
        sid = m.group(1)
        body = m.group(2).strip()
        grp = sid[0] if sid else current_group
        if sid in seen:
            continue
        seen.add(sid)
        out.append(_scenario(sid, body, source=source, kind="hld_group_item", group=grp))

    # Operational flows / use-cases sections
    for m in _RE_OP_FLOW.finditer(text):
        title = m.group(1).strip()
        start = m.end()
        nxt = _RE_OP_FLOW.search(text, start)
        block = text[start : nxt.start() if nxt else len(text)]
        sid = _slug_id("OP", title)
        if sid in seen:
            continue
        seen.add(sid)
        # First non-empty line as summary
        summary = next((ln.strip() for ln in block.splitlines() if ln.strip()), title)
        out.append(
            _scenario(
                sid,
                f"{title}: {summary[:240]}",
                source=source,
                kind="operational_flow",
                group="OP",
            )
        )
        for sm in _RE_OP_SUB.finditer(block):
            sub_title = sm.group(1).strip()
            sub_id = _slug_id("OP", sub_title)
            if sub_id in seen:
                continue
            seen.add(sub_id)
            out.append(
                _scenario(
                    sub_id,
                    sub_title,
                    source=source,
                    kind="operational_flow",
                    group="OP",
                )
            )

    # MUST/SHALL lines embedded in HLD prose (skip group-item bullets — they
    # contain "must NOT" etc. and create false HLD-MUST-* duplicates)
    group_item_line_nos = set()
    for m in _RE_GROUP_ITEM.finditer(text):
        start_line = text[: m.start()].count("\n")
        group_item_line_nos.add(start_line)
    for m in _RE_HEADING_ITEM.finditer(text):
        start_line = text[: m.start()].count("\n")
        group_item_line_nos.add(start_line)

    for i, line in enumerate(text.splitlines()):
        if i in group_item_line_nos:
            continue
        if re.match(r"^[-*]\s+\*\*[A-Z]\d", line):
            continue
        if not _RE_MUST_LINE.search(line):
            continue
        clean = re.sub(r"^[-*#\s]+", "", line).strip()
        if len(clean) < 20:
            continue
        sid = f"HLD-MUST-{i+1:03d}"
        if sid in seen:
            continue
        seen.add(sid)
        out.append(
            _scenario(sid, clean, source=source, kind="hld_must", group="MUST")
        )

    return out


def extract_validation_scenarios(text: str, source: str = "story-body") -> list[dict[str, Any]]:
    """Mine negative acceptance criteria / commit-validations / mutual-exclusions
    from any available body text (HLD, epic_documentation, stored story text).
    Each becomes a first-class needs-coverage scenario so a validation buried in
    a story body cannot slip through the closure gate."""
    if not text or not text.strip():
        return []
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i, line in enumerate(text.splitlines()):
        if not _RE_VALIDATION_LINE.search(line):
            continue
        clean = re.sub(r"^[-*#>\s]+", "", line).strip()
        if len(clean) < 25:
            continue
        sid = f"VAL-{i+1:04d}"
        if sid in seen:
            continue
        seen.add(sid)
        out.append(
            _scenario(sid, clean[:240], source=source, kind="commit_validation", group="VAL")
        )
    return out


def extract_from_must_requirements(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    doc = json.loads(path.read_text(encoding="utf-8"))
    musts = doc.get("must_requirements") or doc.get("requirements") or []
    if isinstance(musts, dict):
        musts = list(musts.values())
    out: list[dict[str, Any]] = []
    for i, m in enumerate(musts):
        if not isinstance(m, dict):
            m = {"id": f"MUST-{i+1:03d}", "text": str(m)}
        mid = str(m.get("id") or f"MUST-{i+1:03d}")
        text = str(m.get("text") or "")
        src = str(m.get("source") or "must_requirements")
        st = "waived" if m.get("waived") else "needs-coverage"
        wr = str(m.get("waive_reason") or "")
        if st == "needs-coverage" and _WAIVE_MARKERS.search(text):
            st = "waived"
            wr = wr or "marked in requirement text"
        out.append(
            {
                "scenario_id": mid,
                "source": src,
                "kind": "must_requirement",
                "group": "MUST",
                "text": text,
                "status": st,
                "waive_reason": wr if st == "waived" else "",
            }
        )
    return out


def extract_from_jira_children(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    doc = json.loads(path.read_text(encoding="utf-8"))
    issues = doc if isinstance(doc, list) else doc.get("issues") or doc.get("children") or []
    out: list[dict[str, Any]] = []
    for iss in issues:
        if not isinstance(iss, dict):
            continue
        key = str(iss.get("key") or iss.get("id") or "")
        summary = str(iss.get("summary") or iss.get("name") or "")
        itype = str(iss.get("issuetype") or iss.get("type") or "jira_issue")
        if not key:
            continue
        text = summary or key
        st = "needs-coverage"
        wr = ""
        if _WAIVE_MARKERS.search(text):
            st = "waived"
            wr = "jira issue marked out of scope / TBD"
        out.append(
            {
                "scenario_id": key,
                "source": "jira",
                "kind": itype.lower().replace(" ", "_"),
                "group": "JIRA",
                "text": text,
                "status": st,
                "waive_reason": wr,
            }
        )
    return out


class AgentScenarioError(ValueError):
    """Raised when scenario_inventory_agent.json fails schema validation."""


_REJECTED_STATUS = re.compile(r"\b(reject|rejected|obsolete|duplicate)\b", re.I)


def extract_from_user_stories(path: Path) -> list[dict[str, Any]]:
    """First-class US-<key> scenarios from jira_user_stories.json.

    Accepts a list of {key, summary, status} or {"user_stories": [...]}.
    Rejected/obsolete stories are dropped; out-of-scope ones are waived.
    """
    if not path.exists():
        return []
    doc = json.loads(path.read_text(encoding="utf-8"))
    stories = doc if isinstance(doc, list) else doc.get("user_stories") or doc.get("stories") or []
    out: list[dict[str, Any]] = []
    for st in stories:
        if not isinstance(st, dict):
            continue
        key = str(st.get("key") or st.get("id") or "").strip()
        if not key:
            continue
        summary = str(st.get("summary") or st.get("name") or "").strip()
        status = str(st.get("status") or "").strip()
        if _REJECTED_STATUS.search(status):
            continue  # non-rejected only (mirrors Step 1 JQL)
        text = summary or key
        sid = f"US-{key}"
        scov = "needs-coverage"
        wr = ""
        if _WAIVE_MARKERS.search(text) or _WAIVE_MARKERS.search(status):
            scov = "waived"
            wr = "user story marked out of scope / TBD"
        out.append(
            {
                "scenario_id": sid,
                "source": "user_story",
                "kind": "user_story",
                "group": "US",
                "text": f"{key}: {text}"[:280],
                "status": scov,
                "waive_reason": wr,
            }
        )
    return out


def extract_from_must_source_stories(path: Path) -> list[dict[str, Any]]:
    """Derive US-<key> items from must_requirements source_story provenance,
    so user stories are first-class even without a jira_user_stories.json."""
    if not path.exists():
        return []
    doc = json.loads(path.read_text(encoding="utf-8"))
    musts = doc.get("must_requirements") or doc.get("requirements") or []
    if isinstance(musts, dict):
        musts = list(musts.values())
    seen: dict[str, str] = {}
    for m in musts:
        if not isinstance(m, dict):
            continue
        # source_story or source like "epic/SW-261643"
        cand = str(m.get("source_story") or "")
        if not cand:
            src = str(m.get("source") or "")
            mt = re.search(r"(SW-\d+)", src)
            cand = mt.group(1) if mt else ""
        for key in re.findall(r"SW-\d+", cand):
            seen.setdefault(key, str(m.get("text", "")))
    out: list[dict[str, Any]] = []
    for key, text in seen.items():
        # _scenario auto-waives when the story text carries out-of-scope/TBD.
        out.append(
            _scenario(
                f"US-{key}",
                f"{key}: {text}"[:280],
                source="user_story",
                kind="user_story",
                group="US",
            )
        )
    return out


_AGENT_REQUIRED = ("scenario_id", "text", "kind")
_AGENT_ALLOWED_STATUS = ("needs-coverage", "waived")


def extract_from_agent_file(path: Path) -> list[dict[str, Any]]:
    """Agent-authored scenarios (blind spots the regex missed).

    Strict schema: each item MUST carry scenario_id, text, kind. status defaults
    to needs-coverage; a waived item MUST carry a waive_reason. source is forced
    to 'agent' for provenance. Raises AgentScenarioError on any violation so a
    malformed hand-off fails loudly instead of silently dropping coverage.
    """
    if not path.exists():
        return []
    doc = json.loads(path.read_text(encoding="utf-8"))
    items = doc if isinstance(doc, list) else doc.get("scenarios") or doc.get("add") or []
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            raise AgentScenarioError(f"agent item #{i} is not an object")
        for field in _AGENT_REQUIRED:
            if not str(it.get(field) or "").strip():
                raise AgentScenarioError(
                    f"agent item #{i} missing required field '{field}'"
                )
        sid = str(it["scenario_id"]).strip()
        if sid in seen:
            raise AgentScenarioError(f"agent item duplicate scenario_id '{sid}'")
        seen.add(sid)
        status = str(it.get("status") or "needs-coverage").strip()
        if status not in _AGENT_ALLOWED_STATUS:
            raise AgentScenarioError(
                f"agent item '{sid}' bad status '{status}' "
                f"(allowed: {_AGENT_ALLOWED_STATUS})"
            )
        wr = str(it.get("waive_reason") or "").strip()
        if status == "waived" and not wr:
            raise AgentScenarioError(
                f"agent item '{sid}' is waived but has no waive_reason"
            )
        out.append(
            {
                "scenario_id": sid,
                "source": "agent",
                "kind": str(it["kind"]).strip(),
                "group": str(it.get("group") or "AGENT").strip(),
                "text": str(it["text"]).strip(),
                "status": status,
                "waive_reason": wr if status == "waived" else "",
            }
        )
    return out


def _dedupe_scenarios(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge by scenario_id; prefer earlier HLD entry, keep waived status."""
    by_id: dict[str, dict[str, Any]] = {}
    for it in items:
        sid = it["scenario_id"]
        if sid not in by_id:
            by_id[sid] = it
            continue
        prev = by_id[sid]
        # If either is waived, keep waived with reason
        if it.get("status") == "waived" or prev.get("status") == "waived":
            prev["status"] = "waived"
            prev["waive_reason"] = prev.get("waive_reason") or it.get("waive_reason") or ""
        # Prefer longer text
        if len(str(it.get("text", ""))) > len(str(prev.get("text", ""))):
            prev["text"] = it["text"]
    return sorted(by_id.values(), key=lambda x: x["scenario_id"])


def _hld_section_from_epic_doc(text: str) -> str:
    """Return HLD subsection from epic_documentation if present."""
    markers = (
        "## HLD",
        "### HLD",
        "## Test matrix",
        "### Test matrix",
        "### HLD and Related Design",
        "## Operational Flows",
    )
    for mk in markers:
        idx = text.find(mk)
        if idx >= 0:
            return text[idx:]
    return ""


_RE_ANY_HEADING = re.compile(r"^(#{2,4})\s+(.+?)\s*$", re.M)


def audit_hld_blind_spots(hld_text: str, scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    """Deterministic self-audit: which HLD headings produced ZERO scenarios.

    Bounds the agent layer: instead of "re-read everything", the agent only has
    to review the flagged zero-yield headings. Pure heuristic (no LLM).
    """
    if not hld_text.strip():
        return {"headings_total": 0, "headings_with_zero": [], "reviewed": 0}

    # Map each scenario's source text back to an approximate location so we can
    # tell which heading blocks yielded coverage.
    scen_texts = [str(s.get("text", "")).lower() for s in scenarios]

    headings = list(_RE_ANY_HEADING.finditer(hld_text))
    zero_yield: list[dict[str, Any]] = []
    for idx, m in enumerate(headings):
        title = m.group(2).strip()
        start = m.end()
        end = headings[idx + 1].start() if idx + 1 < len(headings) else len(hld_text)
        block = hld_text[start:end].lower()
        block_words = [w for w in re.split(r"\W+", block) if len(w) >= 5]
        if not block_words:
            continue
        # Did any scenario text overlap this block meaningfully?
        covered = False
        for st in scen_texts:
            if not st:
                continue
            hits = sum(1 for w in set(block_words[:40]) if w in st)
            if hits >= 3:
                covered = True
                break
        # Skip pure narrative headings (no testable verbs / bullets)
        has_testable = bool(
            re.search(r"[-*]\s+\*\*[A-Z]\d", block)
            or _RE_MUST_LINE.search(block)
            or re.search(r"\b(test|verify|scenario|case|expect|behavior)\b", block)
        )
        if not covered and has_testable:
            zero_yield.append({"heading": title, "line": hld_text[: m.start()].count("\n") + 1})

    return {
        "headings_total": len(headings),
        "headings_with_zero": zero_yield,
        "reviewed": len(headings),
    }


def _apply_overrides(inv: dict[str, Any], tp_dir: Path) -> dict[str, Any]:
    """Apply optional scenario_inventory_overrides.json (add/remove/patch)."""
    ovr_path = tp_dir / "scenario_inventory_overrides.json"
    if not ovr_path.exists():
        return inv
    ovr = json.loads(ovr_path.read_text(encoding="utf-8"))
    by_id = {s["scenario_id"]: s for s in inv.get("scenarios", [])}
    for rid in ovr.get("remove_ids") or []:
        by_id.pop(str(rid), None)
    for add in ovr.get("add") or []:
        sid = add["scenario_id"]
        by_id[sid] = add
    for patch in ovr.get("patch") or []:
        sid = patch["scenario_id"]
        if sid in by_id:
            by_id[sid].update(patch)
        else:
            by_id[sid] = patch
    scenarios = sorted(by_id.values(), key=lambda x: x["scenario_id"])
    inv["scenarios"] = scenarios
    inv["scenario_count"] = len(scenarios)
    inv["needs_coverage_count"] = sum(1 for s in scenarios if s["status"] == "needs-coverage")
    inv["waived_count"] = sum(1 for s in scenarios if s["status"] == "waived")
    inv["overrides_applied"] = str(ovr_path)
    return inv


def build_inventory(
    tp_dir: Path,
    epic: str,
    *,
    hld_file: Path | None = None,
) -> dict[str, Any]:
    sources_used: list[str] = []
    scenarios: list[dict[str, Any]] = []

    # 1) Explicit HLD file
    hld_text = ""
    if hld_file and hld_file.exists():
        hld_text = hld_file.read_text(encoding="utf-8")
        sources_used.append(str(hld_file))

    # 2) epic_documentation HLD section
    epic_doc = tp_dir / f"epic_documentation_{epic}.md"
    if epic_doc.exists():
        epic_text = epic_doc.read_text(encoding="utf-8")
        sec = _hld_section_from_epic_doc(epic_text)
        if sec:
            hld_text = hld_text + "\n\n" + sec if hld_text else sec
            sources_used.append(str(epic_doc))

    # 3) bundled skill test-matrix fallback for known epics (deterministic, no LLM)
    skill_matrix = Path.home() / ".cursor/skills/evpn-igmp-proxy-paths/references/test-matrix.md"
    if epic == "SW-211037" and skill_matrix.exists() and not hld_text.strip():
        hld_text = skill_matrix.read_text(encoding="utf-8")
        sources_used.append(str(skill_matrix))

    if hld_text.strip():
        scenarios.extend(extract_from_hld_markdown(hld_text, source="hld"))

    # NOTE: negative acceptance criteria / commit-validations buried in story or
    # HLD bodies are SURFACED by the per-story requirement auditor
    # (_tp_story_requirement_audit.py) + the deterministic extract_validation_
    # scenarios() helper, and then CURATED into scenario_inventory_agent.json so
    # the hard coverage gate stays on the curated inventory (auto-mined lines are
    # reported for triage, not hard-failed - avoids false gate explosions).

    # 4) MUST requirements (RFC + user-story + epic clauses; merge, dedup by id)
    must_path = tp_dir / "must_requirements.json"
    if must_path.exists():
        scenarios.extend(extract_from_must_requirements(must_path))
        # first-class US-<key> derived from MUST provenance
        scenarios.extend(extract_from_must_source_stories(must_path))
        sources_used.append(str(must_path))

    # 5) First-class user stories (jira_user_stories.json)
    us_path = tp_dir / "jira_user_stories.json"
    if us_path.exists():
        scenarios.extend(extract_from_user_stories(us_path))
        sources_used.append(str(us_path))

    # 6) Optional Jira children export
    jira_path = tp_dir / "jira_children.json"
    if jira_path.exists():
        scenarios.extend(extract_from_jira_children(jira_path))
        sources_used.append(str(jira_path))

    # 7) Agent-contributed blind-spot scenarios (validated; raises on bad schema)
    agent_path = tp_dir / "scenario_inventory_agent.json"
    agent_count = 0
    if agent_path.exists():
        agent_items = extract_from_agent_file(agent_path)
        agent_count = len(agent_items)
        scenarios.extend(agent_items)
        sources_used.append(str(agent_path))

    # Deterministic self-audit of the HLD BEFORE dedupe (uses raw scenarios)
    audit = audit_hld_blind_spots(hld_text, scenarios)

    scenarios = _dedupe_scenarios(scenarios)

    inv = {
        "epic": epic,
        "sources": sources_used,
        "scenario_count": len(scenarios),
        "needs_coverage_count": sum(1 for s in scenarios if s["status"] == "needs-coverage"),
        "waived_count": sum(1 for s in scenarios if s["status"] == "waived"),
        "source_breakdown": _source_breakdown(scenarios),
        "agent_contributed": agent_count,
        "hld_audit": audit,
        "scenarios": scenarios,
    }
    return _apply_overrides(inv, tp_dir)


def _source_breakdown(scenarios: list[dict[str, Any]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for s in scenarios:
        src = str(s.get("source") or "unknown")
        out[src] = out.get(src, 0) + 1
    return dict(sorted(out.items()))


def run_extract(
    tp_dir: Path,
    epic: str,
    *,
    hld_file: Path | None = None,
    audit_only: bool = False,
) -> int:
    if not tp_dir.is_dir():
        print(f"[FAIL] TP dir not found: {tp_dir}")
        return 2

    try:
        inv = build_inventory(tp_dir, epic, hld_file=hld_file)
    except AgentScenarioError as exc:
        print(f"[FAIL] scenario_inventory_agent.json invalid: {exc}")
        return 3

    # Always write the audit report so the agent has a stable artifact to read.
    audit = inv.get("hld_audit", {})
    _atomic_write_json(tp_dir / f"scenario_audit_{epic}.json", audit)

    if audit_only:
        _print_audit(audit)
        return 0

    out_path = tp_dir / "scenario_inventory.json"
    _atomic_write_json(out_path, inv)

    print(
        f"[OK] scenario_inventory.json: {inv['scenario_count']} scenarios "
        f"({inv['needs_coverage_count']} needs-coverage, {inv['waived_count']} waived) "
        f"-> {out_path}"
    )
    print(f"[INFO] source breakdown: {inv.get('source_breakdown', {})}")
    if inv.get("agent_contributed"):
        print(f"[INFO] agent-contributed scenarios: {inv['agent_contributed']}")
    zero = audit.get("headings_with_zero") or []
    if zero:
        print(
            f"[REVIEW] {len(zero)} HLD heading(s) yielded ZERO scenarios - "
            f"agent should review scenario_audit_{epic}.json and add missed "
            f"items to scenario_inventory_agent.json:"
        )
        for h in zero[:12]:
            print(f"  - L{h.get('line')}: {h.get('heading')}")
        if len(zero) > 12:
            print(f"  ... and {len(zero) - 12} more")
    if not inv["scenarios"]:
        print("[INFO] Empty inventory - coverage gate will INFO-skip (no false FAIL)")
    return 0


def _print_audit(audit: dict[str, Any]) -> None:
    zero = audit.get("headings_with_zero") or []
    print(
        f"HLD self-audit: {audit.get('headings_total', 0)} headings reviewed; "
        f"{len(zero)} zero-yield (potential blind spots)"
    )
    for h in zero:
        print(f"  - L{h.get('line')}: {h.get('heading')}")
    if not zero:
        print("  (no blind spots detected by the deterministic heuristic)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract /TP scenario inventory")
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    ap.add_argument("--hld-file", default="", help="Optional explicit HLD markdown path")
    ap.add_argument(
        "--audit",
        action="store_true",
        help="Print HLD blind-spot self-audit (zero-yield headings) and exit",
    )
    args = ap.parse_args()
    tp_dir = Path(args.dir).expanduser() / args.epic
    hld = Path(args.hld_file).expanduser() if args.hld_file else None
    return run_extract(tp_dir, args.epic, hld_file=hld, audit_only=args.audit)


if __name__ == "__main__":
    sys.exit(main())
