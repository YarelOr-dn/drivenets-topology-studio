"""
Lightweight QA quality gates for TP markdown and structured MCP results.

Full rules live in cheetah `test_plan_requirements.md`; this module enforces
cheap, automatable checks so CI/agents can fail fast before Jira push.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


TC_HEADER_RE = re.compile(r"^###\s+\*\*TC-(\d{3,})\s*:", re.MULTILINE)


def extract_tc_blocks(markdown: str) -> Dict[str, str]:
    """Split markdown into TC-NNN -> block text."""
    if not markdown:
        return {}
    headers = list(TC_HEADER_RE.finditer(markdown))
    blocks: Dict[str, str] = {}
    for i, m in enumerate(headers):
        tc_id = f"TC-{m.group(1)}"
        start = m.start()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(markdown)
        blocks[tc_id] = markdown[start:end]
    return blocks


def _segment_between(block: str, start_marker: str, end_marker: str) -> Optional[str]:
    a = block.find(start_marker)
    if a < 0:
        return None
    a = block.find("\n", a)
    if a < 0:
        return None
    b = block.find(end_marker, a)
    if b < 0:
        return block[a:]
    return block[a:b]


def _count_numbered_list_items(segment: str) -> int:
    if segment is None:
        return -1
    return len(re.findall(r"(?m)^\d+\.\s+", segment))


def _validate_presentation_markdown(blocks: Dict[str, str]) -> Tuple[bool, List[str]]:
    """Lighter structural validation for the newer `#### TC-...` presentation
    format (title-first, table steps, *Pass criteria:* bullets). Used when the
    plan does NOT use the legacy `### **TC-NNN:` numbered-section template."""
    errors: List[str] = []
    for tc_id, block in blocks.items():
        low = block.lower()
        if "pass criteria" not in low and "pass criteria:" not in low:
            errors.append(f"{tc_id}: missing Pass criteria")
        has_steps = bool(re.search(r"(?m)^\|\s*\d+\s*\|", block)) or \
            bool(re.search(r"(?m)^\s*\d+\.\s+", block))
        if not has_steps:
            errors.append(f"{tc_id}: missing Test Steps")
    return len(errors) == 0, errors


def validate_test_plan_markdown(markdown: str) -> Tuple[bool, List[str]]:
    """Return (ok, errors) for TC template shape. Format-tolerant: validates the
    legacy `### **TC-NNN:` template when present, otherwise the newer
    `#### TC-...` presentation format."""
    errors: List[str] = []
    if not markdown:
        return False, ["empty markdown"]

    blocks = extract_tc_blocks(markdown)  # legacy `### **TC-NNN:`
    if not blocks:
        # Newer presentation format (`#### TC-...` / title-first). Validate it
        # structurally instead of failing on the legacy pattern.
        any_blocks = extract_tc_blocks_any(markdown)
        if any_blocks:
            return _validate_presentation_markdown(any_blocks)
        errors.append("no TC blocks found ('### **TC-NNN:' or '#### TC-...')")
        return False, errors

    if "## Test Cases" not in markdown:
        errors.append("missing ## Test Cases section")

    nums = sorted(int(k.split("-")[1]) for k in blocks)
    for prev, cur in zip(nums, nums[1:]):
        if cur != prev + 1:
            errors.append(f"TC numbering gap or non-sequential: {prev} -> {cur}")
            break

    for tc_id, block in blocks.items():
        if "1. **Test Name:**" not in block:
            errors.append(f"{tc_id}: missing Test Name section")
        if "2. **Test Description:**" not in block:
            errors.append(f"{tc_id}: missing Test Description section")
        name_seg = _segment_between(block, "1. **Test Name:**", "2. **Test Description:**")
        if name_seg and "negative" in block.lower() and "negative" not in name_seg.lower():
            errors.append(f"{tc_id}: negative scenario should include 'Negative' in Test Name")

        step_seg = _segment_between(block, "3. **Test Steps:**", "4. **Pass Criteria:**")
        crit_seg = _segment_between(block, "4. **Pass Criteria:**", "5. **Variants:**")
        steps = _count_numbered_list_items(step_seg or "")
        crit = _count_numbered_list_items(crit_seg or "")
        if step_seg is None:
            errors.append(f"{tc_id}: missing Test Steps section")
            steps = -1
        if crit_seg is None:
            errors.append(f"{tc_id}: missing Pass Criteria section")
            crit = -1
        if steps >= 0 and crit >= 0 and steps != crit:
            errors.append(f"{tc_id}: Test Steps count ({steps}) != Pass Criteria count ({crit})")
        if steps > 15:
            errors.append(f"{tc_id}: more than 15 Test Steps ({steps})")

    return len(errors) == 0, errors


def validate_structured_result(result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate tp_submit_result envelope (schema_version >= 2 preferred)."""
    errors: List[str] = []
    if not isinstance(result, dict):
        return False, ["result must be an object"]

    schema = result.get("schema_version", 1)
    if schema >= 2:
        if "quality_gate" not in result:
            errors.append("schema_version>=2 requires quality_gate object")
        if "artifacts" not in result:
            errors.append("schema_version>=2 requires artifacts map")
    if "test_count" in result and not isinstance(result["test_count"], int):
        errors.append("test_count must be int")

    md = result.get("test_plan_markdown")
    if isinstance(md, str) and md.strip():
        ok, merrs = validate_test_plan_markdown(md)
        if not ok:
            errors.extend(merrs)

    return len(errors) == 0, errors


# ===========================================================================
# Framework rules + DNOS syntax-validation layer (epic-AGNOSTIC).
#
# These promote the per-epic render lints into the shared MCP validator so
# `tp_validate_plan` / `tp_validate_syntax` enforce them for EVERY epic, not a
# single hand-edited generator. All checks are format-tolerant (work on both
# the `### **TC-NNN:` template and the `#### TC-...` presentation) and operate
# on the raw rendered markdown.
# ===========================================================================

# --- TC block extraction (format-tolerant) --------------------------------
_TC_ANY_HEADER_RE = re.compile(
    r"^#{3,4}\s+(?:\*\*)?(TC-[A-Za-z0-9_-]+)", re.MULTILINE
)


def extract_tc_blocks_any(markdown: str) -> Dict[str, str]:
    """Split markdown into TC-id -> block, tolerant of both heading styles."""
    if not markdown:
        return {}
    headers = list(_TC_ANY_HEADER_RE.finditer(markdown))
    blocks: Dict[str, str] = {}
    for i, m in enumerate(headers):
        tc_id = m.group(1).rstrip(":")
        start = m.start()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(markdown)
        blocks[tc_id] = markdown[start:end]
    return blocks


def _fenced_blocks(markdown: str) -> List[str]:
    """Return the bodies of ``` fenced code blocks."""
    return re.findall(r"```[^\n]*\n(.*?)```", markdown or "", flags=re.DOTALL)


def _nonfence_lines(markdown: str) -> List[str]:
    """Lines that are NOT inside a fenced code block."""
    out: List[str] = []
    in_fence = False
    for line in (markdown or "").splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return out


# --- 1. No internal/design-group jargon (anchor: tp:no-internal-jargon) ----
_JARGON_RE = re.compile(r"\b(HLD|high[- ]level design|design[- ]group)\b", re.I)


def check_no_internal_jargon(markdown: str) -> List[str]:
    return [
        f"internal jargon '{m.group(0)}' in rendered plan (keep in manifest only)"
        for m in _JARGON_RE.finditer(markdown or "")
    ][:10]


# --- 2. Config must be a fenced block, never inline mid-sentence -----------
# (anchor: tp:topology-build-steps / tp:config-as-block)
_INLINE_CFG_RE = re.compile(r"`[^`]*\bconfigure\b[^`]*;\s*commit[^`]*`")


def check_config_blocks(markdown: str) -> List[str]:
    v: List[str] = []
    for line in _nonfence_lines(markdown):
        if line.lstrip().startswith("|"):
            continue  # TC procedure-table Command cells are tabular, allowed
        if _INLINE_CFG_RE.search(line):
            v.append("inline `configure ... ; commit` in prose; move it into a "
                     "fenced DNOS config block")
    return v[:10]


# --- 3. DNOS syntax-validation layer (no other-vendor / made-up syntax) ----
# (anchor: tp:dnos-syntax-validated). Each pattern flags a clear non-DNOS form.
_VENDOR_PATTERNS: List[Tuple[str, "re.Pattern[str]"]] = [
    ("Juniper-style loopback unit (use 'lo0', not 'lo0.N')", re.compile(r"\blo0\.\d")),
    ("Cisco/Junos 'address-family ... activate' (DNOS uses 'neighbor <x> address-family <afi>')",
     re.compile(r"address-family\s+\S+\s+activate", re.I)),
    ("IOS 'ip igmp/pim ...' style (DNOS uses 'protocols igmp|pim' hierarchy)",
     re.compile(r"\bip\s+(?:igmp|pim)\b", re.I)),
    ("Junos 'set protocols ...' style", re.compile(r"\bset\s+protocols\b", re.I)),
    ("IOS 'switchport' (no DNOS equivalent)", re.compile(r"\bswitchport\b", re.I)),
    ("'| save <file>' config-save (DNOS uses commit/rollback, not file save)",
     re.compile(r"\|\s*save\s+\S+\.(?:cfg|conf|txt)", re.I)),
    ("EVPN 'evi <n>' as a config leaf (DNOS scopes the service via route-distinguisher/route-target)",
     re.compile(r"(?m)^\s*evi\s+\d+\s*$")),
]


def check_dnos_syntax_shape(markdown: str) -> List[str]:
    """Static shape checks for obvious non-DNOS / other-vendor CLI."""
    v: List[str] = []
    for why, rx in _VENDOR_PATTERNS:
        if rx.search(markdown or ""):
            v.append(f"non-DNOS syntax: {why}")
    return v


_CFG_CMD_RE = re.compile(r"`(configure\b[^`]+|show\b[^`]+|clear\b[^`]+)`")


def extract_cli_commands(markdown: str) -> List[str]:
    """Pull every configure/show/clear command appearing in inline code spans."""
    seen: List[str] = []
    for m in _CFG_CMD_RE.finditer(markdown or ""):
        cmd = m.group(1).strip()
        if cmd not in seen:
            seen.append(cmd)
    return seen


def classify_cli_command(
    cmd: str,
    live_terms: Optional[List[str]] = None,
    design_terms: Optional[List[str]] = None,
) -> Tuple[str, str]:
    """Classify one command as ok|design|suspect.

    - suspect: matches a known other-vendor shape -> likely made up.
    - design: contains a token from the epic's CLI user-stories (design_terms)
      or is already tagged DESIGN in prose -> acceptable, not-yet-live.
    - ok: otherwise (assumed live-validated; the agent confirms via cmd search).
    `live_terms`/`design_terms` come from dnos-config cmd search and the epic
    CLI user-stories respectively, passed in by the caller.
    """
    for why, rx in _VENDOR_PATTERNS:
        if rx.search(cmd):
            return "suspect", why
    low = cmd.lower()
    for t in (design_terms or []):
        if t and t.lower() in low:
            return "design", f"matches epic CLI user-story token '{t}'"
    return "ok", "no non-DNOS shape detected"


# --- Pre-release provenance: derive DESIGN tokens from the epic user-stories --
# When a /TP is written BEFORE the epic ships, the feature's CLI/show/clear
# commands are NOT yet on any live build, so `cmd search` returns nothing. The
# source of truth is then the EPIC user-stories / cli-reference. This extractor
# turns that raw epic text into design tokens so the syntax layer classifies the
# not-yet-live feature commands as DESIGN (acceptable) instead of suspect, with
# zero hand-typing. (anchor: tp:pre-release-syntax-from-epic)
_EPIC_CMD_SPAN_RE = re.compile(
    r"`([^`]*\b(?:configure|show|clear|set|request|no)\b[^`]*)`", re.I)
_EPIC_LEAF_RE = re.compile(r"\b([a-z][a-z0-9]+(?:-[a-z0-9]+)+)\b")
# hyphenated English that is NOT DNOS CLI - excluded to avoid over-permissive matches
_EPIC_LEAF_STOP = {
    "high-level", "low-level", "real-time", "end-to-end", "control-plane",
    "data-plane", "use-case", "use-cases", "byte-for-byte", "round-trip",
    "out-of-scope", "in-scope", "per-service", "per-port", "per-vendor",
    "non-blocking", "well-known", "first-try", "source-of-truth",
}


def extract_epic_cli_terms(epic_text: Optional[str]) -> List[str]:
    """Extract candidate DNOS CLI tokens from raw epic user-story / cli-reference
    text: whole backticked command fragments + hyphenated CLI leaves
    (igmp-snooping, route-type, admin-state, static-group, ...)."""
    if not epic_text:
        return []
    terms: set[str] = set()
    for m in _EPIC_CMD_SPAN_RE.finditer(epic_text):
        frag = m.group(1).strip()
        if frag:
            terms.add(frag)
    for m in _EPIC_LEAF_RE.finditer(epic_text):
        leaf = m.group(1).lower()
        if leaf not in _EPIC_LEAF_STOP:
            terms.add(leaf)
    return sorted(terms)


def validate_cli_syntax(
    markdown: str,
    live_terms: Optional[List[str]] = None,
    design_terms: Optional[List[str]] = None,
    epic_cli_text: Optional[str] = None,
) -> Dict[str, Any]:
    """The syntax-validation layer: classify every CLI command in the plan.

    design_terms may be passed explicitly AND/OR auto-derived from
    `epic_cli_text` (the epic user-stories / cli-reference). This is how a
    pre-release /TP sources not-yet-live feature syntax from the epic instead of
    the live device."""
    epic_terms = extract_epic_cli_terms(epic_cli_text)
    merged_design = list(dict.fromkeys((design_terms or []) + epic_terms))
    cmds = extract_cli_commands(markdown)
    suspect, design, ok = [], [], []
    for c in cmds:
        verdict, why = classify_cli_command(c, live_terms, merged_design)
        (suspect if verdict == "suspect" else design if verdict == "design" else ok).append(
            {"command": c, "reason": why}
        )
    return {
        "total_commands": len(cmds),
        "suspect": suspect,   # likely made up / other-vendor -> must fix
        "design": design,     # epic-sourced not-yet-live -> ok
        "ok_count": len(ok),
        "epic_terms_derived": len(epic_terms),
        "design_terms_used": len(merged_design),
    }


# --- 4. Service config hierarchy (RD + import/export route-target) ----------
# (anchor: tp:service-config-full-hierarchy)
def check_service_config_hierarchy(markdown: str) -> List[str]:
    v: List[str] = []
    saw_evpn_instance = False
    for body in _fenced_blocks(markdown):
        low = body.lower()
        if "evpn" in low and re.search(r"^\s*instance\s+\S", body, re.M):
            if "protocols" in low and re.search(r"\bbgp\b", low):
                saw_evpn_instance = True
                has_rd = "route-distinguisher" in low
                has_rt = "route-target" in low
                if has_rd and not has_rt:
                    v.append("evpn instance config block has route-distinguisher "
                             "but no route-target (export/import) - incomplete hierarchy")
                if has_rt and not has_rd:
                    v.append("evpn instance config block has route-target but no "
                             "route-distinguisher - incomplete hierarchy")
                if not has_rd and not has_rt:
                    v.append("evpn instance config block under 'protocols bgp' is "
                             "missing route-distinguisher + route-target hierarchy")
    if not saw_evpn_instance:
        # informational, not a hard error (non-EVPN epics exist)
        return []
    return v[:10]


# --- 5. Concise pass criteria (anchor: tp:concise-pass-criteria) -----------
def _pass_criteria_bullets(block: str) -> List[str]:
    seg = _segment_between(block, "Pass Criteria", "Variants")
    if seg is None:
        seg = _segment_between(block, "Pass criteria", "Teardown")
    if seg is None:
        # presentation style: *Pass criteria:* ... up to *Teardown or *Verification
        m = re.search(r"\*Pass criteria:\*(.*?)(\*Teardown|\*Verification|\Z)",
                      block, re.S | re.I)
        seg = m.group(1) if m else None
    if not seg:
        return []
    return [b.strip(" -*\t") for b in re.findall(r"(?m)^\s*(?:[-*]|\d+\.)\s+(.*)$", seg)]


def check_concise_pass_criteria(markdown: str, max_chars: int = 110) -> List[str]:
    v: List[str] = []
    for tc_id, block in extract_tc_blocks_any(markdown).items():
        for b in _pass_criteria_bullets(block):
            if len(b) > max_chars:
                v.append(f"{tc_id}: pass-criterion too verbose ({len(b)} chars > "
                         f"{max_chars}); tighten: \"{b[:48]}...\"")
    return v[:15]


# --- 6. Enough steps for flow (anchor: tp:enough-steps) --------------------
def _count_step_rows(block: str) -> int:
    # table rows like |1|...|...|...|  (skip header/separator)
    rows = re.findall(r"(?m)^\|\s*\d+\s*\|", block)
    if rows:
        return len(rows)
    seg = _segment_between(block, "Test Steps", "Pass Criteria")
    return _count_numbered_list_items(seg or "")


def check_enough_steps(markdown: str, min_steps: int = 4) -> List[str]:
    v: List[str] = []
    for tc_id, block in extract_tc_blocks_any(markdown).items():
        n = _count_step_rows(block)
        if 0 <= n < min_steps:
            v.append(f"{tc_id}: only {n} step(s); add granularity "
                     f"(target >= {min_steps} for clear flow)")
    return v[:15]


# --- 7. Control-plane show on functional TCs (anchor: tp:control-plane-show) -
# A TC is "functional" (needs control-plane proof) when it drives membership or
# traffic - not merely because the feature name (e.g. "snooping") appears. Pure
# config/clear/CLI knob TCs are excluded.
_FUNCTIONAL_RE = re.compile(r"\breport\b|\bjoin\b|\bleave\b|\btraffic\b|\bstream\b|"
                            r"forward|deliver|learned|\(s,g\)|\(\*,g\)|receiver", re.I)
_BGP_EVPN_RE = re.compile(r"show\s+bgp\s+l2vpn\s+evpn", re.I)


def check_control_plane_show(markdown: str) -> List[str]:
    v: List[str] = []
    for tc_id, block in extract_tc_blocks_any(markdown).items():
        if _FUNCTIONAL_RE.search(block) and not _BGP_EVPN_RE.search(block):
            v.append(f"{tc_id}: functional TC has no 'show bgp l2vpn evpn ...' "
                     f"control-plane proof")
    return v[:15]


# --- 8. No internal code identifiers (anchor: tp:no-code-identifiers) -------
# Human-facing TC prose must not carry internal struct/DB/enum/library names.
# Component / process names (FIBMGR, Zebra, EVPN-MNG, BGP, PIM, DataPath) ARE
# allowed. Hard finding. Epic-agnostic (these are DNOS-internal symbols).
_CODE_IDENTIFIER_RE = re.compile(
    r"\bmrt_hold[s]?\b|\bblock_mode\b|\blibigmp\b|\bBLOCK_(?:NONE|BUM|ALL)\b|"
    r"\b[A-Z][A-Za-z]*Db\b|\bEvpnMc[A-Za-z]*\b|\bIgmpInstance\b|"
    r"\bDownstreamNotifier\b"
)


def check_no_code_identifiers(markdown: str) -> List[str]:
    v: List[str] = []
    seen: set[str] = set()
    for m in _CODE_IDENTIFIER_RE.finditer(markdown or ""):
        tok = m.group(0)
        i = m.start()
        ctx = (markdown[max(0, i - 24):i + 24]).replace("\n", " ")
        line = f"internal code identifier '{tok}': ...{ctx}..."
        if line not in seen:
            seen.add(line)
            v.append(line)
    return v[:20]


# --- 9. Rich-TC anatomy present (anchor: tp:tc-rich-anatomy) ----------------
# Soft (reported, not hard-fail): every TC should render in the expanded
# anatomy (What this tests + Devices + Topology + per-step Dev column). Reported
# so partially-converted epics are visible without breaking the build.
def check_rich_anatomy(markdown: str) -> List[str]:
    v: List[str] = []
    for tc_id, block in extract_tc_blocks_any(markdown).items():
        low = block.lower()
        if "**what this tests:**" not in low:
            v.append(f"{tc_id}: missing '**What this tests:**' (rich anatomy)")
        elif "**devices under test:**" not in low and "**topology" not in low:
            v.append(f"{tc_id}: missing Devices/Topology block (rich anatomy)")
    return v[:15]


# --- 10. Placeholder addresses in TC steps (anchor: tp:placeholder-addresses) -
# Soft: TC step/expected prose should use placeholder tokens, not literal
# addresses. Allowed literals: 0.0.0.0 (default querier) and 224.0.0.X
# (RFC4541 non-IGMP flood exception). The reference/addressing-plan preamble is
# exempt (it is not a TC block).
_LITERAL_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_ALLOWED_LITERAL_RE = re.compile(r"^(?:0\.0\.0\.0|224\.0\.0\.\d{1,3})$")


def check_placeholder_addresses(markdown: str) -> List[str]:
    v: List[str] = []
    for tc_id, block in extract_tc_blocks_any(markdown).items():
        # only scan non-fenced lines (config blocks already use <placeholders>)
        bad: set[str] = set()
        for line in _nonfence_lines(block):
            # RFC section references (e.g. "RFC4541 2.1.2.2") look like dotted
            # quads but are not addresses - skip RFC-reference lines.
            if "rfc" in line.lower():
                continue
            for m in _LITERAL_IPV4_RE.finditer(line):
                lit = m.group(0)
                if not _ALLOWED_LITERAL_RE.match(lit):
                    bad.add(lit)
        if bad:
            v.append(f"{tc_id}: literal address(es) in TC prose {sorted(bad)[:4]}; "
                     f"use placeholder tokens (IP-X / <lo-*> / G / S)")
    return v[:15]


# --- 11. Scenario coverage closure (anchor: tp:scenario-coverage-closed) ----
# WARN-first rollout: set SCENARIO_COVERAGE_HARD_FAIL=True after regression
# fixtures pass (see ~/SCALER/TEST/tp/tests/run_tests.sh).
SCENARIO_COVERAGE_HARD_FAIL = True


def check_scenario_coverage(
    result: Optional[Dict[str, Any]] = None,
    inventory: Optional[Dict[str, Any]] = None,
) -> Tuple[List[str], List[str], Dict[str, Any]]:
    """Validate scenario_inventory closure against structured result TCs.

    Returns (hard_errors, warnings, summary_dict).
    When SCENARIO_COVERAGE_HARD_FAIL is False, uncovered scenarios are warnings.
    """
    hard: List[str] = []
    warn: List[str] = []
    summary: Dict[str, Any] = {"skipped": True}
    if not inventory or not inventory.get("scenarios"):
        summary["reason"] = "no scenario inventory"
        return hard, warn, summary

    tcs = (result or {}).get("test_cases") or []
    covered: set[str] = set()
    for tc in tcs:
        for sid in tc.get("covers_scenarios") or []:
            if sid:
                covered.add(str(sid))

    needs = [s for s in inventory["scenarios"] if s.get("status") == "needs-coverage"]
    waived = [s for s in inventory["scenarios"] if s.get("status") == "waived"]
    bad_waived = [s for s in waived if not str(s.get("waive_reason") or "").strip()]
    uncovered = [s for s in needs if s.get("scenario_id") not in covered]

    summary = {
        "skipped": False,
        "needs_coverage": len(needs),
        "mapped": len(needs) - len(uncovered),
        "waived": len(waived),
        "distinct_tc_refs": len(covered),
        "uncovered_ids": [s.get("scenario_id") for s in uncovered[:20]],
    }

    for s in bad_waived:
        msg = f"waived scenario {s.get('scenario_id')} missing waive_reason"
        (hard if SCENARIO_COVERAGE_HARD_FAIL else warn).append(msg)

    for s in uncovered:
        sid = s.get("scenario_id", "?")
        msg = f"uncovered scenario {sid}: {str(s.get('text', ''))[:80]}"
        (hard if SCENARIO_COVERAGE_HARD_FAIL else warn).append(msg)

    return hard, warn, summary


def validate_framework_rules(
    markdown: str,
    live_terms: Optional[List[str]] = None,
    design_terms: Optional[List[str]] = None,
    epic_cli_text: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None,
    scenario_inventory: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run all epic-agnostic framework checks + the syntax layer on a plan.

    Returns a structured findings map. `suspect` syntax and `vendor_syntax`
    are the only hard-fail categories; the rest are quality warnings.
    `epic_cli_text` (epic user-stories / cli-reference) lets a pre-release /TP
    source not-yet-live feature syntax from the epic (classified DESIGN).
    """
    findings = {
        "no_internal_jargon": check_no_internal_jargon(markdown),
        "config_as_block": check_config_blocks(markdown),
        "vendor_syntax": check_dnos_syntax_shape(markdown),
        "service_config_hierarchy": check_service_config_hierarchy(markdown),
        "concise_pass_criteria": check_concise_pass_criteria(markdown),
        "enough_steps": check_enough_steps(markdown),
        "control_plane_show": check_control_plane_show(markdown),
        "no_code_identifiers": check_no_code_identifiers(markdown),
        "rich_anatomy": check_rich_anatomy(markdown),          # soft
        "placeholder_addresses": check_placeholder_addresses(markdown),  # soft
        "cli_syntax": validate_cli_syntax(markdown, live_terms, design_terms, epic_cli_text),
    }
    sc_errs, sc_warns, sc_summary = check_scenario_coverage(result, scenario_inventory)
    findings["scenario_coverage"] = {
        "errors": sc_errs,
        "warnings": sc_warns,
        "summary": sc_summary,
        "hard_fail_mode": SCENARIO_COVERAGE_HARD_FAIL,
    }
    hard = (
        findings["no_internal_jargon"]
        + findings["config_as_block"]
        + findings["vendor_syntax"]
        + findings["no_code_identifiers"]
        + [s["command"] for s in findings["cli_syntax"]["suspect"]]
        + sc_errs
    )
    findings["ok"] = not hard
    findings["hard_fail_count"] = len(hard)
    return findings


def summarize_coverage(
    epic_data: Dict[str, Any], result: Dict[str, Any]
) -> Dict[str, Any]:
    """Attach user-story coverage hints (best-effort)."""
    us_keys = [u.get("key") for u in epic_data.get("user_stories") or [] if u.get("key")]
    md = result.get("test_plan_markdown") or ""
    covered = [k for k in us_keys if k and k in md]
    missing = [k for k in us_keys if k and k not in md]
    return {
        "user_story_keys_in_epic": us_keys,
        "user_stories_mentioned_in_plan": covered,
        "user_stories_not_mentioned_in_plan": missing,
    }
