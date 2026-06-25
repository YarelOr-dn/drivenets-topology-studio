"""Single source of truth for translating dnos_dnaas_teach_plan.frame_recipe
into spirent_tool.py create-stream arguments.

This module exists to fix a bug class observed on 2026-05-01:
  - The /TEST recipe declared a `mcp_dnaas_teach_plan` prerequisite intended
    to surface the canonical Spirent encapsulation (untagged / single-tagged /
    double-tagged) for the DUT AC.
  - The prerequisite handler did not exist, so the prereq was a silent no-op.
  - The SC02 runner hard-coded `outer_vlan=211` and sent VLAN-tagged frames
    to a port-mode AC that expected untagged. Frames were dropped at the
    fabric ingress; the test failed with no obvious indication that the
    tagging was wrong.

After the fix, two independent guarantees hold:

  1. The prerequisite engine (prerequisite_engine._check_mcp_dnaas_teach_plan)
     calls dnos_dnaas_teach_plan, validates frame_recipe.recipe_blockers, and
     writes the canonical recipe + dut_target into
     ~/SCALER/TEST/active_test_session.json under `expected_traffic`.

  2. spirent_create_l2_stream() in mac_trigger.py calls
     `apply_frame_recipe_overrides()` BEFORE building the spirent_tool argv.
     If active_test_session.expected_traffic.frame_recipe targets the same
     transport VLAN that the caller is about to inject AND the encapsulation
     differs, the override wins and the caller's hardcoded outer_vlan is
     silently corrected.

The override logs every correction so users can see exactly what changed and
why. This module never raises on missing/malformed input; it always returns
a usable (vlan, outer_vlan, no_qinq, source_note) tuple so callers can
proceed even when the MCP/teach_plan layer is unavailable.

Static lint helper: `iter_frame_recipe_violations(recipe_dict)` -- yields
human-readable strings for any phase that hard-codes a VLAN that contradicts
a prerequisite-declared teach_plan flag. Used by tools/lint_recipes.py.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger("frame_recipe_consumer")

ACTIVE_SESSION = Path.home() / "SCALER" / "TEST" / "active_test_session.json"


@dataclass
class StreamOverride:
    """Result of consulting active_test_session.expected_traffic.

    Fields mirror the keyword arguments that callers pass to
    `spirent_create_l2_stream()` so the override is drop-in.

    `source_note` is a short human-readable string describing where the
    decision came from -- callers should log it for traceability.
    """
    vlan: int
    outer_vlan: Optional[int]
    no_qinq: bool
    spirent_extra_flags: List[str]
    source_note: str
    overridden: bool


def _read_expected_traffic() -> Dict[str, Any]:
    """Best-effort read of active_test_session.expected_traffic.

    Returns {} on any failure. Never raises.
    """
    if not ACTIVE_SESSION.exists():
        return {}
    try:
        data = json.loads(ACTIVE_SESSION.read_text())
    except Exception:
        return {}
    et = data.get("expected_traffic")
    return et if isinstance(et, dict) else {}


def _iter_expected_traffic(et: Dict[str, Any]) -> Iterable[Tuple[str, Dict[str, Any]]]:
    """Yield flat and keyed expected-traffic entries.

    Newer /TEST recipes validate multiple DNAAS teach plans in one gate
    (for example L/B/v sources). Older sessions stored a single flat
    `expected_traffic.frame_recipe`. Support both shapes.
    """
    if isinstance(et.get("frame_recipe"), dict):
        yield "default", et
    for key, value in et.items():
        if isinstance(value, dict) and isinstance(value.get("frame_recipe"), dict):
            yield str(key), value


def apply_frame_recipe_overrides(
    name: str,
    vlan: int,
    outer_vlan: Optional[int],
    no_qinq: bool,
) -> StreamOverride:
    """Consult active_test_session.expected_traffic and return final stream params.

    Decision tree:
      1. If active_test_session is absent or has no expected_traffic     -> no override
      2. If frame_recipe.recipe_blockers is non-empty                     -> no override
         (the gate already failed; downstream code should be aborted, but
          we don't want to silently inject correct frames into a broken path)
      3. If expected_traffic.vlan does NOT match the caller's transport VLAN
         (vlan or outer_vlan, whichever is truthy)                        -> no override
         This is the cross-test isolation guarantee: SC01 talking to PE-1 must
         NOT be silently rewritten just because the prereq teach_plan was
         scoped to PE-4.
      4. Otherwise, translate frame_recipe.encapsulation into stream params:
           - "untagged"      -> vlan=expected.vlan, outer_vlan=None, no_qinq=True
           - "single-tagged" -> vlan=expected.outer_vlan, outer_vlan=None
           - "double-tagged" -> vlan=expected.inner_vlan, outer_vlan=expected.outer_vlan
         If the caller already matches the encapsulation, no override is logged
         (return overridden=False) but spirent_extra_flags are still propagated.

    Suppression hook: setting EVPN_MM_DISABLE_FRAME_RECIPE=1 in the environment
    bypasses the entire override path. Useful for unit tests that want to
    exercise the legacy hardcoded-VLAN path.
    """
    if os.environ.get("EVPN_MM_DISABLE_FRAME_RECIPE") == "1":
        return StreamOverride(
            vlan=vlan,
            outer_vlan=outer_vlan,
            no_qinq=no_qinq,
            spirent_extra_flags=[],
            source_note="EVPN_MM_DISABLE_FRAME_RECIPE=1; legacy path",
            overridden=False,
        )

    et = _read_expected_traffic()
    caller_vlan = outer_vlan if outer_vlan is not None else vlan
    matched_key = ""
    matched_entry: Dict[str, Any] = {}
    for key, candidate in _iter_expected_traffic(et):
        expected_vlan = candidate.get("vlan")
        if expected_vlan is None:
            continue
        try:
            if int(expected_vlan) == int(caller_vlan):
                matched_key = key
                matched_entry = candidate
                break
        except (TypeError, ValueError):
            continue

    fr = (matched_entry.get("frame_recipe") or {}) if matched_entry else {}
    if not fr:
        return StreamOverride(
            vlan=vlan,
            outer_vlan=outer_vlan,
            no_qinq=no_qinq,
            spirent_extra_flags=[],
            source_note=(
                "active_test_session.expected_traffic has no entry matching "
                f"caller vlan={caller_vlan}; legacy path"
            ),
            overridden=False,
        )

    if fr.get("recipe_blockers"):
        codes = ",".join(
            b.get("code", "?") for b in fr["recipe_blockers"]
            if isinstance(b, dict)
        )
        logger.warning(
            "frame_recipe has unresolved blockers [%s] -- not overriding "
            "stream %s; downstream verification will likely fail",
            codes,
            name,
        )
        return StreamOverride(
            vlan=vlan,
            outer_vlan=outer_vlan,
            no_qinq=no_qinq,
            spirent_extra_flags=[],
            source_note=f"frame_recipe has blockers [{codes}]; not overriding",
            overridden=False,
        )

    expected_vlan = matched_entry.get("vlan")

    encap = fr.get("encapsulation")
    spirent_flags = list(fr.get("spirent_flags") or [])

    if encap == "untagged":
        # Sentinel consumed by mac_trigger.spirent_create_l2_stream():
        # untagged port-mode traffic must omit --vlan entirely.
        new_vlan = 0
        new_outer = None
        new_no_qinq = True
    elif encap == "single-tagged":
        new_vlan = int(fr.get("outer_vlan") or expected_vlan)
        new_outer = None
        new_no_qinq = no_qinq
    elif encap == "double-tagged":
        outer = fr.get("outer_vlan")
        inner = fr.get("inner_vlan")
        if outer is None or inner is None:
            return StreamOverride(
                vlan=vlan,
                outer_vlan=outer_vlan,
                no_qinq=no_qinq,
                spirent_extra_flags=spirent_flags,
                source_note=f"encap=double-tagged but outer/inner missing (outer={outer}, inner={inner})",
                overridden=False,
            )
        new_vlan = int(inner)
        new_outer = int(outer)
        new_no_qinq = False
    else:
        return StreamOverride(
            vlan=vlan,
            outer_vlan=outer_vlan,
            no_qinq=no_qinq,
            spirent_extra_flags=spirent_flags,
            source_note=f"unknown encapsulation={encap!r}; legacy path",
            overridden=False,
        )

    matches_caller = (
        new_vlan == int(vlan)
        and (new_outer == outer_vlan)
        and (new_no_qinq == no_qinq)
    )
    overridden = not matches_caller
    if overridden:
        logger.warning(
            "[FRAME-RECIPE] stream %s -- caller asked for "
            "(vlan=%s, outer_vlan=%s, no_qinq=%s); teach_plan says "
            "(encap=%s, vlan=%s, outer_vlan=%s, no_qinq=%s); applying override",
            name, vlan, outer_vlan, no_qinq,
            encap, new_vlan, new_outer, new_no_qinq,
        )

    return StreamOverride(
        vlan=new_vlan,
        outer_vlan=new_outer,
        no_qinq=new_no_qinq,
        spirent_extra_flags=spirent_flags,
        source_note=(
            f"teach_plan[{matched_key}] vlan={expected_vlan} encap={encap} "
            f"({'OVERRIDE' if overridden else 'matches caller'})"
        ),
        overridden=overridden,
    )


# ---------------------------------------------------------------------------
# Static lint -- used by tools/lint_recipes.py
# ---------------------------------------------------------------------------

def iter_frame_recipe_violations(recipe: Dict[str, Any]) -> Iterable[str]:
    """Yield human-readable lint messages for any recipe phase that
    hard-codes a transport VLAN despite declaring an mcp_dnaas_teach_plan
    prerequisite.

    Pass conditions (no violations):
      - Recipe does NOT declare mcp_dnaas_teach_plan -> nothing to enforce
      - All trigger phases use action='spirent_or_manual' / 'remote_pe_traffic'
        / 'traffic_via_pw' (high-level actions that go through mac_trigger
        which already calls apply_frame_recipe_overrides)

    Violation conditions:
      - A phase has a `spirent_args` block with explicit `outer_vlan` or `vlan`
        that does NOT reference {_si_outer_vlan} / runtime params
      - A phase comment contains "outer_vlan=" with a literal integer
        (catches comments documenting hardcoded VLAN injection)
    """
    declares_teach_plan = any(
        (p.get("check") == "mcp_dnaas_teach_plan")
        for p in (recipe.get("prerequisites") or [])
    )
    if not declares_teach_plan:
        return

    for sc in recipe.get("scenarios") or []:
        sc_id = sc.get("id", "<unknown>")
        for phase_name, phase in (sc.get("phases") or {}).items():
            if not isinstance(phase, dict):
                continue
            spirent_args = phase.get("spirent_args")
            if isinstance(spirent_args, dict):
                ov = spirent_args.get("outer_vlan")
                if isinstance(ov, int):
                    yield (
                        f"{sc_id}.{phase_name}: spirent_args.outer_vlan={ov} is a literal "
                        f"integer; recipe declares mcp_dnaas_teach_plan -- the value MUST come "
                        f"from active_test_session.expected_traffic.frame_recipe.outer_vlan "
                        f"or be a templated runtime param (e.g. {{_si_outer_vlan}})"
                    )
                v = spirent_args.get("vlan")
                if isinstance(v, int):
                    yield (
                        f"{sc_id}.{phase_name}: spirent_args.vlan={v} is a literal "
                        f"integer; recipe declares mcp_dnaas_teach_plan -- prefer "
                        f"a templated runtime param so the override path can be applied"
                    )


__all__ = [
    "StreamOverride",
    "apply_frame_recipe_overrides",
    "iter_frame_recipe_violations",
    "ACTIVE_SESSION",
]
