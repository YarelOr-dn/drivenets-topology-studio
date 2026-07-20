#!/usr/bin/env python3
"""Non-deterministic TP rendering helpers.

Validates role-based device names, placeholder IPs/MACs, and step shape.
"""

from __future__ import annotations

import re
from typing import Any

# Lab hostnames that must NOT appear in TP prose
LAB_DEVICE_RE = re.compile(
    r"\b(PE-[0-9]+|RR-SA-[0-9]+|YOR[_-]CL[_-]PE-[0-9]+)\b",
    re.I,
)

# Allowed role patterns
ROLE_DEVICE_RE = re.compile(
    r"\b(PE|RR|P|CE|NCC-ACTIVE|NCC-STANDBY|NCP|NCM|NCF|AC-IF|IRB-IF|PW-IF|CORE-IF)-[A-Z0-9]+\b"
)

PLACEHOLDER_IP_RE = re.compile(r"\bIP-[A-Z0-9]+\b")
PLACEHOLDER_MAC_RE = re.compile(r"\bMAC-[A-Z0-9]+\b")

LITERAL_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
LITERAL_MAC_RE = re.compile(r"\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b")


def substitute_placeholders(text: str, mapping: dict[str, str] | None = None) -> str:
    """Replace IP-X / MAC-X placeholders with mapping values (for /TEST bind time)."""
    out = text
    for key, val in (mapping or {}).items():
        out = out.replace(key, val)
    return out


def validate_tc_prose(tc: dict[str, Any]) -> list[str]:
    """Return list of validation violations for a normalized TC object."""
    violations: list[str] = []
    blob_parts: list[str] = []
    for field in ("name", "description", "purpose"):
        blob_parts.append(str(tc.get(field, "")))
    for step in tc.get("steps") or []:
        blob_parts.append(str(step))
    for pc in tc.get("pass_criteria") or []:
        blob_parts.append(str(pc))
    blob = " ".join(blob_parts)

    if LAB_DEVICE_RE.search(blob):
        violations.append("contains hard-coded lab device name (use role names PE-X, RR-Y)")

    steps = tc.get("steps") or []
    pass_criteria = tc.get("pass_criteria") or []
    if steps and len(pass_criteria) != len(steps):
        violations.append(
            f"pass_criteria count ({len(pass_criteria)}) != steps count ({len(steps)})"
        )
    if len(steps) > 15:
        violations.append(f"step count {len(steps)} exceeds 15")

    # Literal addresses in description are discouraged unless explicitly mapped
    if LITERAL_IPV4_RE.search(blob) and not PLACEHOLDER_IP_RE.search(blob):
        violations.append("contains literal IPv4; prefer IP-X placeholders")
    if LITERAL_MAC_RE.search(blob) and not PLACEHOLDER_MAC_RE.search(blob):
        violations.append("contains literal MAC; prefer MAC-X placeholders")

    return violations


def validate_traffic_has_src_dst(tc: dict[str, Any]) -> bool:
    blob = " ".join(str(s) for s in (tc.get("steps") or [])).lower()
    if "traffic" not in blob and "spirent" not in blob:
        return True
    return "->" in blob or " to " in blob or "from" in blob


# --- Human-POV readability contract (anchor: tp:human-pov-readability) --------
# Additive checks; safe for existing callers. A TP is INCOMPLETE if these fail.

DOC_REQUIRED_SECTIONS = (
    ("role map / glossary", re.compile(r"role\s*map|glossary", re.I)),
    ("reference topologies", re.compile(r"reference topolog", re.I)),
    ("base setup", re.compile(r"base setup", re.I)),
    ("stimulus & tooling", re.compile(r"stimulus\s*&?\s*tooling|stimulus / tooling", re.I)),
)


def validate_doc_readability(md_text: str) -> list[str]:
    """Return missing top-level human-POV sections in a rendered test_plan_*.md."""
    return [f"missing section: {label}" for label, rx in DOC_REQUIRED_SECTIONS
            if not rx.search(md_text)]


def validate_tc_human_pov(tc: dict[str, Any]) -> list[str]:
    """Per-TC human-POV completeness: stimulus, teardown, and a topology link.

    Accepts either structured keys (stimulus_tooling/teardown/topology_ref) or a
    rendered 'markdown' blob containing the equivalent lines.
    """
    v: list[str] = []
    blob = str(tc.get("markdown", ""))
    has_stim = bool(tc.get("stimulus_tooling")) or "stimulus / tooling" in blob.lower()
    has_tear = bool(tc.get("teardown")) or "teardown / restore" in blob.lower()
    has_topo = bool(tc.get("topology_ref")) or bool(re.search(r"topology:\s*t\d", blob, re.I))
    if not has_stim:
        v.append("missing *Stimulus / tooling:* line")
    if not has_tear:
        v.append("missing *Teardown / restore baseline:* line")
    if not has_topo:
        v.append("missing 'Topology: T#' reference")
    return v


# --- Positive-activates + negative/no-harm contract -------------------------
# Anchor: tp:positive-activates-negative-noharm. Every config-mutating TC must
# prove the knob DOES something (positive expected-behavior) AND that nothing
# breaks (negative reject + unrelated-object no-harm). Additive; safe default.

_CONFIG_STEP_RE = re.compile(
    r"\b(configure|commit|rollback|admin-state)\b|\bno\s+network-services\b", re.I
)
_POSITIVE_RE = re.compile(
    r"expected[- ]behavio|activat|actually|proves?\b|takes effect|is applied|"
    r"ignored before|learned (?:only )?after|after enable|does something",
    re.I,
)
_NEGATIVE_RE = re.compile(
    r"\bnegative\b|no-harm|reject|malformed|invalid|must not|commit check|"
    r"rollback 0|unchanged|isolation|no dirty|not flooded|treated as withdraw",
    re.I,
)

_CONFIG_AUTOMATION = {
    "cli_config_verify", "cli_negative", "cli_clear", "negative_control",
}


def tc_is_config_mutating(tc: dict[str, Any]) -> bool:
    """True when a TC runs configure/commit/no/rollback (CLI/Defaults/Negative/clear)."""
    if str(tc.get("automation_type", "")).lower() in _CONFIG_AUTOMATION:
        return True
    for step in tc.get("steps") or []:
        cmd = step.get("command", "") if isinstance(step, dict) else str(step)
        if _CONFIG_STEP_RE.search(str(cmd)):
            return True
    return False


def validate_tc_rich_anatomy(tc: dict[str, Any]) -> list[str]:
    """RICH_TC-style contract (tp:every-tc-rich-anatomy): a FINISHED TC must be
    authored in the curated rich anatomy - rich=True, has procedure steps, every
    step is node-scoped (Dev names the acting node, never a bare '-'), and it
    carries an objective or purpose. The generic auto-derived fallback (Dev='-')
    is NOT acceptable for a shipped TP. Returns [] when satisfied."""
    v: list[str] = []
    steps = tc.get("steps") or []
    if not tc.get("rich"):
        v.append("not rich (generic auto-derive is not acceptable for a finished TP)")
    if not steps:
        v.append("no procedure steps")
    for i, s in enumerate(steps, 1):
        dev = s.get("dev") if isinstance(s, dict) else None
        if dev is None or str(dev).strip() in ("", "-"):
            v.append(f"step {i} has no node-scoped Dev (bare '-')")
    if not str(tc.get("objective") or tc.get("purpose") or tc.get("description") or "").strip():
        v.append("missing objective/purpose")
    return v


def validate_tc_positive_negative(tc: dict[str, Any]) -> list[str]:
    """For config-mutating TCs, require a positive expected-behavior signal AND
    a negative/no-harm guard. Returns [] when not applicable or satisfied."""
    if not tc_is_config_mutating(tc):
        return []
    parts = [str(tc.get("purpose", "")), str(tc.get("description", ""))]
    for s in tc.get("steps") or []:
        parts.append(str(s))
    for pc in tc.get("pass_criteria") or []:
        parts.append(str(pc))
    blob = " ".join(parts)
    v: list[str] = []
    if not _POSITIVE_RE.search(blob):
        v.append("config TC missing explicit positive expected-behavior step "
                 "(prove the knob DOES something, not just that it parses)")
    if not _NEGATIVE_RE.search(blob):
        v.append("config TC missing negative/no-harm guard "
                 "(reject malformed with clean rollback + prove an unrelated object unchanged)")
    return v


# --- Zero-to-hero ladder + control-plane + no-internal-jargon contracts ------
# Epic-AGNOSTIC framework anchors enforced here so every /TP run inherits them:
#   tp:no-internal-jargon-in-render - the human-facing plan carries NO design
#       -group tags (HLD, "HLD alias" column, "HLD use-case 1:" prefixes).
#       Tags stay in the manifest (hld_group) for traceability only.
#   tp:topology-build-steps - a category's Topology Prerequisite Steps are a
#       numbered DNOS BUILD sequence (config actions), each paired with a
#       verify show -- not free prose.
#   tp:zero-to-hero-steps - every functional TC walks the full ladder:
#       baseline -> stimulus -> control-plane (BGP) -> RIB/oper-db ->
#       datapath/forwarding -> counters -> negative/no-harm -> teardown.
#   tp:control-plane-show-required - every functional TC carries >=1
#       "show bgp l2vpn evpn ..." even in Basic Functionality.

# Design-group jargon that must never reach the rendered plan.
_JARGON_TOKEN_RE = re.compile(r"\b(HLD|high[- ]level design|design[- ]group)\b", re.I)
# Leading/inline design-group prefix in prose, e.g. "HLD use-case 1:",
# "HLD B2/I2:", "HLD A1/A2:". Bounded so it never eats across a far colon.
_JARGON_PREFIX_RE = re.compile(r"\bHLD\b[^:]{0,40}:\s*", re.I)


def strip_internal_jargon(text: str) -> str:
    """Remove design-group jargon (HLD ...:) from human-facing prose.

    The generator calls this at RENDER time so the rendered plan never carries
    an internal HLD tag, while the manifest keeps hld_group for traceability.
    Epic-agnostic: matches the tag shape, not any epic's specific group names."""
    if not text:
        return text
    s = str(text)
    s = _JARGON_PREFIX_RE.sub("", s)          # drop "HLD <tag>:" prefixes
    s = re.sub(r"\bHLD\b\s*", "", s)          # drop any bare leftover token
    return s.strip()


def validate_no_internal_jargon(md_text: str) -> list[str]:
    """Render-level reject (anchor: tp:no-internal-jargon-in-render): the
    rendered test_plan must contain NO design-group jargon. Returns a bounded,
    de-duplicated list of offending contexts."""
    v: list[str] = []
    for m in _JARGON_TOKEN_RE.finditer(md_text or ""):
        i = m.start()
        ctx = (md_text[max(0, i - 28):i + 28]).replace("\n", " ")
        v.append(f"internal jargon '{m.group(0)}' in rendered plan: ...{ctx}...")
    return sorted(set(v))[:20]


_BUILD_VERB_RE = re.compile(
    r"\b(configure|commit|enable|enabled|attach|create|set|admin-state|"
    r"activate|add|bind|assign)\b", re.I
)
_SHOW_RE = re.compile(r"\bshow\b", re.I)


def validate_category_build_steps(steps: list) -> list[str]:
    """A category's Topology Prerequisite Steps must be a numbered DNOS BUILD
    sequence with >=1 verify `show` (anchor: tp:topology-build-steps).

    `steps` is a list mixing plain-string goal notes and structured build-step
    dicts ({title, why, config, verify}). At least one step MUST carry a real
    config block or build verb, and at least one verify `show` must be present.
    Inline `configure ... ; commit` jammed into prose is discouraged: a build
    step that needs config MUST expose it as a `config` block, not mid-sentence."""
    if not steps:
        return ["empty topology prerequisite steps"]
    parts: list[str] = []
    has_config_block = False
    inline_config_in_prose = False
    for s in steps:
        if isinstance(s, dict):
            parts.append(str(s.get("title", "")))
            parts.append(str(s.get("why", "")))
            cfg = s.get("config", "") or ""
            if cfg.strip():
                has_config_block = True
            parts.append(cfg)
            for v in s.get("verify", []) or []:
                parts.append(" ".join(map(str, v)) if isinstance(v, (list, tuple)) else str(v))
        else:
            txt = str(s)
            parts.append(txt)
            if re.search(r"`configure\b", txt) or re.search(r";\s*commit\b", txt):
                inline_config_in_prose = True
    blob = " ".join(parts)
    v: list[str] = []
    if not (has_config_block or _BUILD_VERB_RE.search(blob)):
        v.append("topology prereq is prose, not a DNOS build sequence "
                 "(no config block / build verb)")
    if not _SHOW_RE.search(blob):
        v.append("topology prereq has no verify `show` step")
    if inline_config_in_prose:
        v.append("topology prereq has inline `configure ... ; commit` in prose; "
                 "move it into a structured config block")
    return v


_BGP_EVPN_SHOW_RE = re.compile(r"show\s+bgp\s+l2vpn\s+evpn", re.I)


def _tc_command_blob(tc: dict[str, Any]) -> str:
    parts: list[str] = []
    for s in tc.get("steps") or []:
        parts.append(s.get("command", "") if isinstance(s, dict) else str(s))
    for vc in tc.get("verification_commands") or []:
        parts.append(vc.get("command", "") if isinstance(vc, dict) else str(vc))
    return " ".join(parts)


def validate_tc_control_plane_show(tc: dict[str, Any]) -> list[str]:
    """Functional TC must carry >=1 'show bgp l2vpn evpn ...' control-plane
    proof (anchor: tp:control-plane-show-required). Returns [] when satisfied."""
    if _BGP_EVPN_SHOW_RE.search(_tc_command_blob(tc)):
        return []
    return ["functional TC has no 'show bgp l2vpn evpn ...' control-plane proof"]


_LADDER_PHASES = {
    "baseline/precondition": re.compile(
        r"baseline|default|precondition|clean start|before enable|"
        r"confirm.*(empty|disabled|established)", re.I),
    "stimulus": re.compile(
        r"report|join|leave|\bsend\b|stream|traffic|inject|restart|"
        r"switchover|commit|configure|enable|withdraw|flap|receiver|source|"
        r"querier|membership|\(s,g\)|\(\*,g\)", re.I),
    "control-plane (BGP)": re.compile(
        r"show\s+bgp|route-type|\bRT-[3678]\b|\bsmet\b|\bimet\b", re.I),
    "datapath/RIB/oper-db": re.compile(
        r"multicast-db|forwarding-table|inclusive-multicast|\bfib\b|"
        r"\boif\b|oper-?db|multicast route", re.I),
}


def validate_tc_zero_to_hero(tc: dict[str, Any]) -> list[str]:
    """Every functional TC must walk the full ladder (anchor:
    tp:zero-to-hero-steps): baseline -> stimulus -> control-plane (BGP) ->
    datapath/RIB/oper-db -> teardown. Returns the missing ladder phases so a
    half-step TC is never declared complete."""
    parts = [str(tc.get("purpose", ""))]
    for s in tc.get("steps") or []:
        parts.append(" ".join(str(x) for x in s.values())
                     if isinstance(s, dict) else str(s))
    for pc in tc.get("pass_criteria") or []:
        parts.append(str(pc))
    blob = " ".join(parts)
    v = [f"missing ladder phase: {phase}"
         for phase, rx in _LADDER_PHASES.items() if not rx.search(blob)]
    if not (tc.get("teardown") or "teardown" in blob.lower()):
        v.append("missing ladder phase: teardown/restore")
    return v


# --- Rich-TC anatomy (anchor: tp:tc-rich-anatomy) ----------------------------
# Epic-AGNOSTIC engine: render every TC in the expanded anatomy and derive the
# presentation fields from per-epic topology metadata. An epic generator passes
# its own topo_meta (devices/tokenmap/diagram/notes/actors keyed by topology
# ref); the engine here is shared so every future epic inherits the format.
#
# Anatomy: What this tests (1 sentence) -> Purpose (remainder) -> Devices
# (numbered) -> Traffic actors (bulleted) -> Topology diagram -> Topology notes
# -> Procedure (Step/Dev/Action/Command(s)/Expected) -> Pass criteria.
# Addresses stay placeholder tokens; operational language only (component names
# like FIBMGR/Zebra/BGP/PIM are fine, internal code identifiers are not).

# Internal code identifiers that must NEVER appear in human-facing TC prose
# (components are fine; struct/DB/enum/library names are not). Hard finding.
CODE_IDENTIFIER_RE = re.compile(
    r"\bmrt_hold[s]?\b|\bblock_mode\b|\blibigmp\b|\bBLOCK_(?:NONE|BUM|ALL)\b|"
    r"\b[A-Z][A-Za-z]*Db\b|\bEvpnMc[A-Za-z]*\b|\bIgmpInstance\b|"
    r"\bDownstreamNotifier\b",
)


def _identity(x: Any) -> str:
    return str(x or "")


def first_sentence(text: str, clean=None) -> str:
    s = (clean or _identity)(text).strip()
    m = re.search(r"\.\s", s)
    return s[:m.start() + 1] if m else s


_RICH_TRAFFIC_RE = re.compile(
    r"report|join|leave|\bsend\b|stream|traffic|receiver|source|querier|"
    r"mrouter|multicast|\(s,g\)|\(\*,g\)|rt-6|smet|igmp", re.I)


def tc_has_traffic(tc: dict[str, Any]) -> bool:
    if (tc.get("test_hints") or {}).get("requires_traffic"):
        return True
    if str(tc.get("automation_type", "")).lower() in {
            "traffic_snoop", "traffic_control", "topology_scenario", "ha"}:
        return True
    blob = " ".join(str(s) for s in (tc.get("steps") or [])) + " " + str(tc.get("purpose", ""))
    return bool(_RICH_TRAFFIC_RE.search(blob))


def derive_step_dev(step: dict[str, Any], tokenmap: dict[str, str]) -> str:
    """Best-effort device attribution for a step from a per-topology token map."""
    if not tokenmap:
        return "-"
    action = str(step.get("action", ""))
    al = action.lower()
    if any(k in al for k in ("datapath", "data plane", "data-plane", "forwarding proof")):
        return "traffic"
    blob = " ".join([action, str(step.get("expected", "")), str(step.get("command", ""))])
    seen: set[str] = set()
    out: list[str] = []
    for tok in sorted(tokenmap, key=len, reverse=True):
        if re.search(r"\b" + re.escape(tok) + r"\b", blob):
            lab = tokenmap[tok]
            if lab not in seen:
                seen.add(lab)
                out.append(lab)
    return " / ".join(out) if out else "-"


def derive_rich_presentation(tcs: list, topo_meta: dict[str, Any], clean=None) -> int:
    """Attach the rich anatomy to every TC not already hand-curated (t['rich']).

    topo_meta keys (each a dict keyed by topology ref, e.g. 'T1'):
      devices, tokenmap, diagram, notes, actors.
    Run AFTER the epic's step-augmentation so the ladder steps already exist.
    Returns the count of TCs the format was derived onto."""
    clean = clean or _identity
    dev_t = topo_meta.get("devices", {})
    tok_t = topo_meta.get("tokenmap", {})
    dia_t = topo_meta.get("diagram", {})
    not_t = topo_meta.get("notes", {})
    act_t = topo_meta.get("actors", {})
    n = 0
    for t in tcs:
        if t.get("rich"):
            continue
        ref = t.get("topology_ref", "")
        t["rich"] = True
        full_p = clean(t.get("purpose", ""))
        obj = first_sentence(full_p)
        t["objective"] = obj
        t["purpose_render"] = full_p[len(obj):].strip() if full_p.startswith(obj) else full_p
        t["devices"] = dev_t.get(ref, [])
        t["traffic_actors"] = act_t.get(ref, []) if tc_has_traffic(t) else []
        t["topo_diagram"] = dia_t.get(ref, "")
        t["topo_notes"] = not_t.get(ref, [])
        for s in t.get("steps", []):
            if isinstance(s, dict):
                s["dev"] = derive_step_dev(s, tok_t.get(ref, {}))
        n += 1
    return n


def _cell(text: str) -> str:
    return str(text).replace("|", "\\|")


def _concise(text: str, max_chars: int = 180) -> str:
    """Render-side concision for the What-this-tests / Purpose headlines
    (tp:concise-what-purpose). The full text stays in the structured artifacts;
    the rendered plan shows only the crisp lead clause: cut at the first
    sentence/clause boundary ('.' or ';'), else soft-cap at max_chars. Detail
    lives in the Procedure + Pass criteria below."""
    s = str(text or "").strip()
    if not s:
        return s
    m = re.search(r"[.;]\s", s)
    if m and m.start() + 1 <= max_chars:
        return s[: m.start()].strip().rstrip(",;:") + "."
    if len(s) > max_chars:
        return s[:max_chars].rsplit(" ", 1)[0].rstrip(",;:") + " ..."
    return s


def render_rich_tc(t: dict[str, Any], L: list, clean=None, topo_titles=None) -> None:
    """Render one TC in the rich anatomy. `clean` strips jargon (epic supplies
    its _clean); `topo_titles` maps topology ref -> title for the diagram header."""
    clean = clean or _identity
    topo_titles = topo_titles or {}
    L.append(f"#### {t['id']} - {t['name']}")
    L.append("")
    L.append(f"_Stories:_ {', '.join(t.get('covers_user_stories', []))}  |  "
             f"_Jira category:_ {t.get('jira_category','')}  |  "
             f"_IGMP ver:_ {t.get('igmp_version','agnostic')}  |  "
             f"_AF:_ {t.get('address_family','')}")
    if t.get("jira_test_category"):
        L.append(f"_Aligns to Jira Test Category:_ {t['jira_test_category']}")
    ref = t.get("topology_ref", "")
    if ref:
        title = topo_titles.get(ref, "")
        L.append(f"_Topology:_ {ref} - {title} (see Reference Topologies)" if title
                 else f"_Topology:_ {ref} (see Reference Topologies)")
    L.append("")
    # "What this tests" must be COMPLETE and understandable (never a truncated
    # lead clause -- objectives often open with setup context, so a naive cut
    # surfaces the setup, not the tested behavior). Prefer an authored minimal
    # one-liner (`what`) when present; otherwise show the full objective.
    what = str(t.get("what") or "").strip() or clean(t.get("objective", ""))
    L.append(f"**What this tests:** {what}")
    L.append("")
    pr = _concise(clean(t.get("purpose_render", t.get("purpose", ""))))
    if pr.strip():
        L.append(f"**Purpose:** {pr}")
        L.append("")
    if t.get("devices"):
        L.append("**Devices under test:**")
        L.append("")
        L.append("| # | Role | Device in topology | Loopback / service RD | Notes |")
        L.append("|---|------|--------------------|------------------------|-------|")
        for d in t["devices"]:
            L.append("| " + " | ".join(_cell(x) for x in d) + " |")
        L.append("")
    if t.get("traffic_actors"):
        L.append("**Traffic actors:**")
        for a in t["traffic_actors"]:
            L.append(f"- {a}")
        L.append("")
    if t.get("traffic_flow"):
        L.append(f"**Traffic flow (ingress -> egress):** {t['traffic_flow']}")
        L.append("")
    if t.get("topo_diagram"):
        title = topo_titles.get(ref, "")
        L.append(f"**Topology ({ref} - {title}):**" if title else "**Topology:**")
        L.append("")
        L.append("```")
        for line in t["topo_diagram"].splitlines():
            L.append(line)
        L.append("```")
        L.append("")
    if t.get("topo_notes"):
        L.append("**Topology notes:**")
        for nline in t["topo_notes"]:
            L.append(f"- {nline}")
        L.append("")
    # Per-DUT configuration suggestions (tp:tc-authoring-rigor). Real, validated
    # DNOS syntax; flatten one-liners are allowed to save eye-space. Each entry:
    # {"dev": "#1 PE-X", "config": <str|list-of-flatten-lines>}.
    if t.get("config_suggestions"):
        L.append("**Configuration suggestions (per DUT, flatten):**")
        L.append("")
        for c in t["config_suggestions"]:
            L.append(f"- *{c.get('dev','')}:*")
            secs = c.get("sections")
            if secs:
                for sec in secs:
                    L.append("")
                    L.append(f"  _{sec['title']}:_")
                    L.append("")
                    L.append("  ```")
                    for ln in sec["lines"]:
                        L.append(f"  {ln}")
                    L.append("  ```")
            else:
                lines = c.get("config") or []
                if isinstance(lines, str):
                    lines = lines.splitlines()
                if lines:
                    L.append("")
                    L.append("  ```")
                    for ln in lines:
                        L.append(f"  {ln}")
                    L.append("  ```")
        L.append("")
    L.append("**Procedure:**")
    L.append("")
    L.append("_Dev = the acting device, by # from the Devices table above "
             "(e.g. `#1 PE-X`); `traffic` = data-plane traffic; `all` = every listed device._")
    L.append("")
    ie_col = bool(t.get("traffic_ie"))
    if ie_col:
        L.append("| Step | Action | Dev | Verification | Ingress -> Egress | Expected Result |")
        L.append("|---|---|---|---|---|---|")
    else:
        L.append("| Step | Action | Dev | Verification | Expected Result |")
        L.append("|---|---|---|---|---|")
    for s in t.get("steps", []):
        cmds = (s.get("command", "") or "").strip()
        parts = [c.strip() for c in cmds.split(" ; ") if c.strip()]
        # backtick each command; escape DNOS pipe-filters so they don't break the
        # markdown column count. When a step runs >1 command, NUMBER them so a
        # multi-check step is followable (they stack on their own lines).
        if len(parts) > 1:
            cmd_cell = "<br>".join(
                f"({i}) `{c.replace('|', chr(92) + '|')}`" for i, c in enumerate(parts, 1))
        elif parts:
            cmd_cell = f"`{parts[0].replace('|', chr(92) + '|')}`"
        else:
            cmd_cell = "-"
        # Split a compound Expected into clauses so each asserted outcome is its
        # own line; number them 1:1 with the commands when counts match, else
        # render as a bullet checklist.
        exp = (s.get("expected", "") or "").strip()
        clauses = [c.strip() for c in exp.split("; ") if c.strip()]
        if len(clauses) > 1 and len(clauses) == len(parts):
            exp_cell = "<br>".join(f"({i}) {_cell(c)}" for i, c in enumerate(clauses, 1))
        elif len(clauses) > 1:
            exp_cell = "<br>".join(f"- {_cell(c)}" for c in clauses)
        else:
            exp_cell = _cell(exp)
        if ie_col:
            dev_l = str(s.get("dev", "")).lower()
            ie = s.get("ie") or (t["traffic_ie"] if dev_l.startswith("traffic") else "-")
            L.append(f"| {s.get('step','')} | {_cell(s.get('action',''))} | "
                     f"{_cell(s.get('dev','-'))} | {cmd_cell} | {_cell(ie)} | {exp_cell} |")
        else:
            L.append(f"| {s.get('step','')} | {_cell(s.get('action',''))} | "
                     f"{_cell(s.get('dev','-'))} | {cmd_cell} | {exp_cell} |")
    L.append("")
    L.append("**Pass criteria:**")
    for pc in t.get("pass_criteria", []):
        L.append(f"- {pc}")
    L.append("")


def render_prerequisites_block(prereqs: dict[str, Any] | None, L: list,
                               clean=None) -> bool:
    """Render a SW-265228-style category-level functional Prerequisites block
    (anchor: tp:category-functional-prerequisites). Distinct from the
    Topology Prerequisite Steps (the DNOS BUILD ladder): this is the
    role/ownership + required-state + consolidated-validate + out-of-scope
    framing that makes a category self-contained for a tester.

    `prereqs` schema (all keys optional; the block renders only the parts
    supplied, so it is backward-compatible - an epic that passes None or {}
    gets nothing):
        {
          "intro":        "<one-line scope sentence>",
          "roles":        [("PE-X", "owns the local AC + snoop-DB ..."), ...],
          "required_state":["`l2vpn-evpn` AFI established before ...", ...],
          "validate":     "EVPN state, RT-6/7/8, forwarding-table, ..."  # str or list
          "out_of_scope": ["MLD/IPv6 (SW-245193)", ...],
        }
    Returns True when it emitted anything, else False.
    """
    clean = clean or _identity
    if not prereqs:
        return False
    roles = prereqs.get("roles") or []
    req = prereqs.get("required_state") or []
    val = prereqs.get("validate")
    oos = prereqs.get("out_of_scope") or []
    intro = prereqs.get("intro")
    if not (roles or req or val or oos or intro):
        return False
    L.append("#### Prerequisites")
    L.append("")
    if intro:
        L.append(f"_{clean(intro)}_")
        L.append("")
    if roles:
        L.append("**Roles & ownership:**")
        L.append("")
        for name, own in roles:
            L.append(f"- `{name}` - {clean(own)}")
        L.append("")
    if req:
        L.append("**Required state:**")
        L.append("")
        for r in req:
            L.append(f"- {clean(r)}")
        L.append("")
    if val:
        if isinstance(val, (list, tuple)):
            L.append("**Validate (every task in this category):**")
            L.append("")
            for v in val:
                L.append(f"- {clean(v)}")
        else:
            L.append(f"**Validate (every task in this category):** {clean(val)}")
        L.append("")
    if oos:
        L.append(f"**Out of scope for this category:** {clean('; '.join(oos)) if all(isinstance(o, str) for o in oos) else ''}")
        L.append("")
    return True


def validate_no_code_identifiers(md_text: str) -> list[str]:
    """Hard check (anchor: tp:no-code-identifiers): human-facing TC prose must
    not carry internal struct/DB/enum/library names (mrt_hold, block_mode,
    libigmp, BLOCK_*, *Db, EvpnMc*, ...). Component/process names are allowed."""
    v: list[str] = []
    for m in CODE_IDENTIFIER_RE.finditer(md_text or ""):
        i = m.start()
        ctx = (md_text[max(0, i - 24):i + 24]).replace("\n", " ")
        v.append(f"internal code identifier '{m.group(0)}': ...{ctx}...")
    # de-dup by token, keep bounded
    seen: set[str] = set()
    out: list[str] = []
    for line in v:
        if line not in seen:
            seen.add(line)
            out.append(line)
    return out[:20]


def self_check() -> int:
    good = {
        "id": "TC-TEST-01",
        "name": "Basic IPv4 on PE-X",
        "steps": ["Configure IRB on PE-X", "Verify show evpn instance SVC-X"],
        "pass_criteria": ["IRB present", "EVPN instance shows router-interface"],
    }
    bad = {
        "id": "TC-TEST-02",
        "name": "On PE-4",
        "steps": ["x"] * 16,
        "pass_criteria": ["y"],
    }
    assert not validate_tc_prose(good), "good TC should pass"
    assert validate_tc_prose(bad), "bad TC should fail"
    # human-POV checks
    assert validate_doc_readability("# plan"), "empty doc should report missing sections"
    assert not validate_doc_readability(
        "Role Map\nReference Topologies\nBase Setup\nStimulus & Tooling"
    ), "doc with all sections should pass"
    assert validate_tc_human_pov({"stimulus_tooling": "x", "teardown": "y", "topology_ref": "T1"}) == []
    assert validate_tc_human_pov({"markdown": "no extras"}), "bare TC should fail human-pov"
    # positive-activates + negative/no-harm contract
    assert validate_tc_positive_negative({"automation_type": "traffic_snoop"}) == [], \
        "non-config TC is not subject to the config contract"
    weak_cfg = {
        "automation_type": "cli_config_verify",
        "steps": [{"command": "configure ... ; commit", "expected": "accepted"}],
        "pass_criteria": ["config accepted"],
    }
    assert len(validate_tc_positive_negative(weak_cfg)) == 2, \
        "weak config TC should miss BOTH positive and negative"
    strong_cfg = {
        "automation_type": "cli_config_verify",
        "steps": [
            {"command": "configure ... ; commit", "expected": "enable activates snooping; report learned after enable"},
            {"command": "commit check", "expected": "malformed rejected; rollback 0 clean; SVC-2 unchanged"},
        ],
        "pass_criteria": ["takes effect", "no-harm to sibling service"],
    }
    assert validate_tc_positive_negative(strong_cfg) == [], "thorough config TC should pass"
    # no-internal-jargon contract
    assert strip_internal_jargon("HLD use-case 1: source inside fabric") == \
        "source inside fabric", "leading HLD prefix should be stripped"
    assert strip_internal_jargon("HLD B2/I2: union semantics apply") == \
        "union semantics apply", "HLD group prefix should be stripped"
    assert strip_internal_jargon("plain purpose text") == "plain purpose text"
    assert validate_no_internal_jargon("| Role | Meaning | HLD alias |"), \
        "HLD alias column should be rejected at render level"
    assert not validate_no_internal_jargon("clean human-facing plan with no jargon")
    # topology-build-steps contract (structured build steps)
    assert validate_category_build_steps(["just some prose with no build verbs"]), \
        "prose-only prereq should fail build-steps lint"
    good_steps = [
        "Goal: minimal 2-PE service.",
        {"title": "EVPN instance", "why": "create the service",
         "config": "network-services\n  evpn\n    instance SVC\n    !\n  !\n!",
         "verify": [("show evpn instance SVC", "instance Up")]},
    ]
    assert validate_category_build_steps(good_steps) == [], \
        "structured config-block prereq should pass"
    inline_steps = [
        "Underlay: `configure protocols isis instance IGP ; commit` then verify show isis neighbors",
    ]
    assert any("inline" in x for x in validate_category_build_steps(inline_steps)), \
        "inline configure-in-prose should be flagged"
    # control-plane-show contract
    assert validate_tc_control_plane_show({
        "verification_commands": [{"command": "show bgp l2vpn evpn route-type 6"}]
    }) == [], "TC with bgp l2vpn evpn show should pass"
    assert validate_tc_control_plane_show({
        "verification_commands": [{"command": "show evpn instance SVC"}]
    }), "TC without a bgp l2vpn evpn show should fail"
    # zero-to-hero ladder contract
    full_ladder = {
        "purpose": "prove forwarding",
        "steps": [
            {"command": "show evpn instance SVC", "expected": "baseline empty before enable"},
            {"command": "send IGMPv2 report", "expected": "stimulus applied"},
            {"command": "show bgp l2vpn evpn route-type 6", "expected": "RT-6 present"},
            {"command": "show multicast forwarding-table group G", "expected": "OIF correct"},
        ],
        "pass_criteria": ["delivered only to interested OIF"],
        "teardown": "rollback 0",
    }
    assert validate_tc_zero_to_hero(full_ladder) == [], "full ladder TC should pass"
    assert validate_tc_zero_to_hero({"purpose": "x", "steps": [], "pass_criteria": []}), \
        "empty TC should report missing ladder phases"
    # rich-anatomy engine
    assert first_sentence("One thing. Two thing.") == "One thing.", "first_sentence split"
    assert first_sentence("No period here") == "No period here"
    assert tc_has_traffic({"automation_type": "traffic_snoop"}) is True
    assert tc_has_traffic({"automation_type": "cli_config_verify",
                           "steps": [], "purpose": "config only"}) is False
    tmap = {"PE-GW": "#1 PE-GW", "PE-X": "#2 PE-X"}
    assert derive_step_dev({"action": "on PE-GW do x"}, tmap) == "#1 PE-GW"
    assert derive_step_dev({"action": "Datapath / forwarding proof"}, tmap) == "traffic"
    assert derive_step_dev({"action": "generic"}, tmap) == "-"
    rich_tcs = [{"id": "TC-A", "name": "sample", "topology_ref": "T1",
                 "purpose": "First. Second.",
                 "steps": [{"step": 1, "action": "on PE-X send report",
                            "command": "show x", "expected": "ok"}],
                 "pass_criteria": ["p"], "covers_user_stories": ["SW-1"]}]
    meta = {"devices": {"T1": [["1", "PE", "PE-X", "<lo>", "n"]]},
            "tokenmap": {"T1": {"PE-X": "#1 PE-X"}},
            "diagram": {"T1": "PE-X --- PE-Y"}, "notes": {"T1": ["a note"]},
            "actors": {"T1": ["R1 - receiver"]}}
    nd = derive_rich_presentation(rich_tcs, meta)
    assert nd == 1 and rich_tcs[0]["rich"] and rich_tcs[0]["objective"] == "First."
    assert rich_tcs[0]["purpose_render"] == "Second."
    assert rich_tcs[0]["steps"][0]["dev"] == "#1 PE-X"
    out_lines: list[str] = []
    render_rich_tc(rich_tcs[0], out_lines, topo_titles={"T1": "Single-homed 2-PE"})
    md = "\n".join(out_lines)
    assert "**What this tests:**" in md and "**Devices under test:**" in md
    assert "| Step | Action | Dev | Verification | Expected Result |" in md
    # code-identifier denylist
    assert validate_no_code_identifiers("the mrt_hold timer") , "mrt_hold must be flagged"
    assert validate_no_code_identifiers("GroupDb merged state"), "GroupDb must be flagged"
    assert validate_no_code_identifiers("BLOCK_BUM on non-DF"), "BLOCK_BUM must be flagged"
    assert not validate_no_code_identifiers("FIBMGR owns the group state"), \
        "component name FIBMGR must NOT be flagged"
    assert not validate_no_code_identifiers("run spirent_loss_verify for 0% loss"), \
        "tool token spirent_loss_verify must NOT be flagged"
    print("[OK] _tp_render_lib self_check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(self_check())
