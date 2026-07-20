#!/usr/bin/env python3
"""
_tp_topology_usage_lint.py - epic-agnostic gate that enforces TOPOLOGY-USAGE
consistency for the optional external-mrouter actor across ALL sections of a /TP
TC (anchor: tp:topology-only-what-tc-uses).

The sibling _tp_actor_consistency_lint.py checks actor-NAME drift (same token
everywhere). THIS gate checks the orthogonal invariant: a TC must not depict, in
ANY section, an MR-IF / MROUTER actor it does not actually use, and a TC that
does list the actor must depict it. It exists because a per-section conditional
(apply_topology_mrouter_conditional) once scrubbed the diagram + actor list but
MISSED the Devices-Under-Test 'Notes' cell and shared Topology notes, leaving a
drop-TC whose diagram/actors said 'no mrouter' while its DUT Notes still read
'... ; optional MROUTER on MR-IF' - cosmetically inconsistent.

Invariant (self-consistent; the primary depiction = diagram + Traffic-Actors is
the source of truth, the secondary sections must AGREE):

  A (drop-consistency, HARD): if a TC does NOT depict the mrouter in its diagram
     AND does NOT list MROUTER as a Traffic-Actor (i.e. it is presented as a
     non-mrouter TC), then NONE of {Devices-Under-Test Notes, Topology notes,
     Topology Prerequisite Steps} may affirmatively name an MR-IF / MROUTER
     actor. (This is the class the missed-DUT-cell bug produced.)

  B (keep-consistency, HARD): if a TC DOES list MROUTER as a Traffic-Actor, it
     MUST be depicted in the topology (diagram or notes).

  C (real-usage, HARD): if a TC DEPICTS the mrouter (MR-IF in its diagram OR
     MROUTER listed as a Traffic-Actor), it MUST contain at least ONE AFFIRMATIVE
     mrouter-USAGE trigger (a step/purpose/objective/prereq that promotes/queries
     an mrouter, an mrouter OIF/port, host-only/router-guard, static mrouter, PIM,
     or a knob SET WITH A VALUE like 'mrouter-timeout 180'). This catches the
     OVER-KEEP that A and B (pure consistency) cannot: a TC that DRAWS MR-IF while
     its only 'mrouter' mention is a bare knob NAME in a ?-help / knob-enumeration
     menu ('?-help lists ... mrouter-timeout ...') or a negation of absence
     ('receivers only (no external mrouter)') - internally CONSISTENT but WRONG.
     It mirrors the generator's _tc_uses_mrouter classifier so lint and generator
     agree.

An AFFIRMATIVE reference (checks A/B) is the interface token 'mr-if' (any case)
or the caps actor token 'MROUTER'. Generic lower-case snooping prose ('mrouter
ports are OIFs...') and negations ('no mrouter', 'without mrouter') are NOT actor
references and never trip the gate - only text that implies THIS TC HAS an
MR-IF/MROUTER does.

Read-only. Exits 1 on any violation (a real gate), 0 when clean. Reads the
epic's full_result.json. Prints the offending TC ids.

Usage:
    python3 _tp_topology_usage_lint.py --epic SW-XXXXX [--json]
"""
import argparse, json, re, sys
from pathlib import Path

from _tp_paths import resolve_data_dir, default_data_dir


# Negation / absence phrasing that must be PRESERVED (not an actor reference).
_NEG_RE = re.compile(
    r"\bno\s+mr(outer|-if)\b|\bwithout\s+mr(outer|-if)\b|\bnot\s+an?\s+mrouter\b",
    re.I)
# Lenient depiction tokens for check B (how MROUTER may be drawn): the interface,
# the actor, or its role keywords (a PIM/querier label depicts an mrouter).
_DEPICT_TOKENS = ("mr-if", "mrouter", "querier", "pim", "general query",
                  "general-query")


def affirms_mrouter(text):
    """True when a fragment affirmatively names the MR-IF/MROUTER actor."""
    f = str(text)
    if _NEG_RE.search(f):
        return False
    if "mr-if" in f.lower():
        return True
    return "MROUTER" in f  # caps actor token only, never lower-case prose


def any_affirm(fragments):
    return any(affirms_mrouter(x) for x in fragments)


def actor_listed(tc):
    return any(str(a).split(" -", 1)[0].strip() == "MROUTER"
               for a in (tc.get("traffic_actors") or []))


def diagram_depicts(tc):
    return affirms_mrouter(tc.get("topology_diagram", ""))


def depicted_lenient(tc):
    blob = (str(tc.get("topology_diagram", "")) + " "
            + " ".join(str(n) for n in (tc.get("topology_notes") or []))).lower()
    if _NEG_RE.search(blob) and "mr-if" not in blob and "mrouter" not in blob:
        return False
    return any(tok in blob for tok in _DEPICT_TOKENS)


def dut_note_frags(tc):
    return [r[4] for r in (tc.get("devices") or []) if len(r) >= 5]


# --- check C: real-usage detector (mirrors the generator's _tc_uses_mrouter). ---
# An mrouter is USED only via an AFFIRMATIVE trigger; a bare knob NAME in a
# ?-help/menu and a negation of absence are NOT usage.
_MR_TIMEOUT_SET_RE = re.compile(r"mrouter-timeout\s+\d", re.I)   # SET w/ value
_MR_STATIC_SET_RE = re.compile(r"interface\s+\S+\s+mrouter\b(?!\s*[-?])", re.I)
_MR_KNOB_TOKEN_RE = re.compile(r"mrouter-timeout", re.I)         # bare knob NAME
_MR_NEG_USE_RE = re.compile(
    r"\bno\s+(?:\w+\s+){0,2}mr(?:outer|-if)\b"
    r"|\bwithout\s+(?:an?\s+)?mr(?:outer|-if)\b"
    r"|\bnot\s+an?\s+mrouter\b", re.I)
_MR_PROSE_RE = re.compile(r"mrouter|multicast[- ]router", re.I)
_MR_PIM_RE = re.compile(r"\bpim\b", re.I)
_MR_ROLE_TOKENS = ("mr-if", "host-only", "router-guard", "router guard")


def has_real_mrouter_usage(tc):
    """True when a step / purpose / objective / prereq / rubric AFFIRMATIVELY
    exercises an mrouter (role/guard token, PIM, a knob SET WITH A VALUE, static
    mrouter config, or behavioral mrouter/multicast-router prose). A bare knob
    NAME in a ?-help / enumeration menu ('mrouter-timeout' listed among knobs) and
    a negation of absence ('no external mrouter') are NOT usage. Mirrors the
    generator's _tc_uses_mrouter so this lint and the generator stay in lock-step
    (anchor: tp:topology-only-what-tc-uses)."""
    prose = [str(tc.get("purpose", "")), str(tc.get("objective", ""))]
    prose += [str(x) for x in (tc.get("topology_prereq") or [])]
    prose += [str(x) for x in (tc.get("covers_rubric_rules") or [])]
    cmds = []
    for s in (tc.get("steps") or []):
        prose += [str(s.get("action", "")), str(s.get("expected", ""))]
        cmds.append(str(s.get("command", "")))
    prose_blob = " ".join(prose).lower()
    cmd_blob = " ".join(cmds).lower()
    # 1. Knob SET WITH A VALUE / static mrouter leaf in a configure command.
    if _MR_TIMEOUT_SET_RE.search(cmd_blob) or _MR_STATIC_SET_RE.search(cmd_blob):
        return True
    # Strip negations so a bare 'mrouter' inside 'no external mrouter' never counts.
    role_blob = _MR_NEG_USE_RE.sub(" ", prose_blob + " " + cmd_blob)
    # 2. An mrouter role/guard token or PIM.
    if any(tok in role_blob for tok in _MR_ROLE_TOKENS):
        return True
    if _MR_PIM_RE.search(role_blob):
        return True
    # 3. Behavioral mrouter prose surviving once the bare knob NAME is neutralized.
    residual = _MR_KNOB_TOKEN_RE.sub(" ", role_blob)
    return bool(_MR_PROSE_RE.search(residual))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="accepted for CLI parity; the gate fails on any "
                         "violation regardless")
    a = ap.parse_args()

    fr = json.loads((resolve_data_dir(getattr(a, 'dir', None)) / a.epic / "full_result.json").read_text())
    tcs = fr.get("test_cases") or []

    a_dut = []    # (id) drop-TC still names MR-IF/MROUTER in a DUT Notes cell
    a_note = []   # (id) drop-TC still names MR-IF/MROUTER in Topology notes
    a_prq = []    # (id) drop-TC still names MR-IF/MROUTER in Topology prereq
    b_undrawn = []  # (id) lists MROUTER actor but topology does not depict it
    c_no_usage = []  # (id) depicts MR-IF/MROUTER but no affirmative mrouter-usage

    for t in tcs:
        listed = actor_listed(t)
        drawn = diagram_depicts(t)
        # A: presented as a non-mrouter TC -> secondary sections must agree.
        if not listed and not drawn:
            if any_affirm(dut_note_frags(t)):
                a_dut.append(t.get("id"))
            if any_affirm(t.get("topology_notes") or []):
                a_note.append(t.get("id"))
            if any_affirm(t.get("topology_prereq") or []):
                a_prq.append(t.get("id"))
        # B: lists the actor -> must be depicted somewhere in the topology.
        if listed and not depicted_lenient(t):
            b_undrawn.append(t.get("id"))
        # C: depicts the mrouter (MR-IF in diagram OR MROUTER actor listed) ->
        # must actually USE it (>=1 affirmative usage trigger). Catches the
        # over-keep that consistency (A/B) misses: MR-IF drawn while the only
        # 'mrouter' mention is a ?-help/knob-enumeration name or a negation.
        if (listed or drawn) and not has_real_mrouter_usage(t):
            c_no_usage.append(t.get("id"))

    viol = len(a_dut) + len(a_note) + len(a_prq) + len(b_undrawn) + len(c_no_usage)

    if a.json:
        print(json.dumps({
            "epic": a.epic, "tcs": len(tcs),
            "drop_tc_mrif_in_dut_notes": a_dut,
            "drop_tc_mrif_in_topology_notes": a_note,
            "drop_tc_mrif_in_topology_prereq": a_prq,
            "actor_listed_not_depicted": b_undrawn,
            "depicts_mrouter_no_real_usage": c_no_usage,
            "violations": viol,
        }, indent=2))
    else:
        print(f"topology-usage consistency lint -- {a.epic} ({len(tcs)} TC(s))")
        print(f"  [{'OK  ' if not a_dut else 'FAIL'}] A1 non-mrouter TC has no MR-IF/MROUTER in Devices-Under-Test Notes")
        for tid in a_dut[:20]:
            print(f"         {tid}")
        print(f"  [{'OK  ' if not a_note else 'FAIL'}] A2 non-mrouter TC has no MR-IF/MROUTER in Topology notes")
        for tid in a_note[:20]:
            print(f"         {tid}")
        print(f"  [{'OK  ' if not a_prq else 'FAIL'}] A3 non-mrouter TC has no MR-IF/MROUTER in Topology Prerequisite Steps")
        for tid in a_prq[:20]:
            print(f"         {tid}")
        print(f"  [{'OK  ' if not b_undrawn else 'FAIL'}] B  every listed MROUTER actor is depicted in the topology")
        for tid in b_undrawn[:20]:
            print(f"         {tid}")
        print(f"  [{'OK  ' if not c_no_usage else 'FAIL'}] C  every TC that depicts MR-IF/MROUTER has a real mrouter-usage step (not just a ?-help/knob-name or negation)")
        for tid in c_no_usage[:20]:
            print(f"         {tid}")
        if viol == 0:
            print("\n[PASS] topology-usage is consistent: no TC depicts an MR-IF/MROUTER "
                  "actor it does not use, every listed MROUTER is drawn, and every "
                  "depicted mrouter is actually exercised (0 violations).")
        else:
            print(f"\n[FAIL] {viol} topology-usage violation(s). Fix: extend "
                  "apply_topology_mrouter_conditional() to scrub the MR-IF/MROUTER "
                  "actor from EVERY section (diagram, actors, notes, DUT Notes) of a "
                  "non-mrouter TC; for check C, fix _tc_uses_mrouter() so a bare "
                  "knob-name (?-help/menu) or a negation ('no external mrouter') does "
                  "NOT count as mrouter usage (see tp:topology-only-what-tc-uses).")

    if viol:
        sys.exit(1)


if __name__ == "__main__":
    main()
