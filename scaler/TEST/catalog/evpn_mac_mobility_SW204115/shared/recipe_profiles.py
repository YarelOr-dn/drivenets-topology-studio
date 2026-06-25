#!/usr/bin/env python3
"""Recipe-type profiles for the EVPN MAC Mobility test suite.

A profile captures the per-test-type defaults that used to live as
hard-coded ``if recipe.type == "config-validation":`` branches scattered
across ``mac_mobility_orchestrator.py``. Keeping them here makes the
orchestrator declarative::

    profile = get_profile(recipe)
    if profile.skip_spirent_preflight:
        ...
    verdict.expected_warns |= profile.expected_benign_warnings

Adding a new recipe type (or a new recipe) becomes a ~10-line diff in this
file instead of a multi-location orchestrator patch.

Profiles are consulted, not enforced: unknown recipe types fall back to
``default_profile()`` which is equivalent to the legacy per-id behaviour.
So the existing 11 passing recipes keep working unchanged even if they
never add a ``recipe_type`` field.

Live-validated 2026-04-21 on PE-1 (DNOS 26.2.0 build 20_priv).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, Optional


@dataclass(frozen=True)
class RecipeProfile:
    """Per-recipe-type declarative config.

    Fields are intentionally conservative -- anything unset falls back to
    the orchestrator's existing defaults. A profile may only *relax* checks
    that are known-noise for a given test type; it must never *tighten*
    them (that would silently break existing passing recipes).
    """

    recipe_type: str

    skip_spirent_preflight: bool = False
    """When True, bypass spirent_run_preflight() entirely. Used for pure
    config-validation tests that never send traffic."""

    expected_benign_warnings: FrozenSet[str] = frozenset()
    """Verdict layers whose WARN status must NOT downgrade the overall
    verdict. Added to ``ScenarioVerdict.expected_warns`` in the orchestrator
    before layer evaluation."""

    skip_cross_layer_check: bool = False
    """When True, skip the MAC table vs FIB consistency check. Useful for
    tests that never learn a MAC."""

    required_fixtures: FrozenSet[str] = frozenset()
    """Infrastructure fixtures the profile expects. Informational only --
    the orchestrator's ``infra_required`` gate remains authoritative."""

    rollback_on_exit: bool = False
    """When True, force a 'rollback 0' / 'end' cleanup at scenario end even
    if the trigger handler aborted early. config_validation profile sets
    this so a failed handler never leaves the candidate pending."""

    description: str = ""


# ---------------------------------------------------------------------------
# Registered profiles
# ---------------------------------------------------------------------------

_PROFILES: Dict[str, RecipeProfile] = {
    "config_validation": RecipeProfile(
        recipe_type="config_validation",
        skip_spirent_preflight=True,
        expected_benign_warnings=frozenset({"bgp_session", "traces",
                                            "cross_layer", "timing"}),
        skip_cross_layer_check=True,
        required_fixtures=frozenset({"any_evpn_instance"}),
        rollback_on_exit=True,
        description=(
            "Pure CLI commit-check tests. No traffic, no L2 path, no BGP "
            "dependency. Always rolls back, never commits. Example: "
            "irb_si_rejection (G2)."
        ),
    ),

    "clear_matrix": RecipeProfile(
        recipe_type="clear_matrix",
        skip_spirent_preflight=False,
        expected_benign_warnings=frozenset({"bgp_session", "traces",
                                            "cross_layer"}),
        skip_cross_layer_check=False,
        required_fixtures=frozenset({"si_mode"}),
        rollback_on_exit=False,
        description=(
            "Tests that exercise 'clear' commands as active triggers. "
            "Spirent optional -- if suppressed MACs are not present, the "
            "clear command still executes and the handler asserts 'returns "
            "clean output'. Example: clear_operations (G5)."
        ),
    ),

    "move_matrix": RecipeProfile(
        recipe_type="move_matrix",
        skip_spirent_preflight=False,
        expected_benign_warnings=frozenset({"traces"}),
        skip_cross_layer_check=False,
        required_fixtures=frozenset({"si_mode", "spirent_evpn_peer"}),
        rollback_on_exit=False,
        description=(
            "Remote<->Remote or cross-domain MAC move tests using Spirent "
            "RT-2 injection. Example: evpn_evpn (G1)."
        ),
    ),

    "bulk_learn": RecipeProfile(
        recipe_type="bulk_learn",
        skip_spirent_preflight=False,
        expected_benign_warnings=frozenset({"traces", "cross_layer"}),
        skip_cross_layer_check=True,
        required_fixtures=frozenset({"si_mode", "spirent_evpn_peer"}),
        rollback_on_exit=False,
        description=(
            "Scale tests (64K MACs etc). Cross-layer check is disabled "
            "because it would iterate per-MAC. Example: scale_64k (G3)."
        ),
    ),

    "pw_suppression": RecipeProfile(
        recipe_type="pw_suppression",
        skip_spirent_preflight=False,
        expected_benign_warnings=frozenset({"traces"}),
        skip_cross_layer_check=False,
        required_fixtures=frozenset({"si_mode", "spirent_evpn_peer"}),
        rollback_on_exit=False,
        description=(
            "Cross-domain suppression sanction tests (drop/shutdown/"
            "suppress) via rapid AC<->RemoteEVPN flap. Example: "
            "pw_suppression_sanctions (G4)."
        ),
    ),

    "default": RecipeProfile(
        recipe_type="default",
        skip_spirent_preflight=False,
        expected_benign_warnings=frozenset(),
        skip_cross_layer_check=False,
        required_fixtures=frozenset(),
        rollback_on_exit=False,
        description="Legacy behaviour for recipes without an explicit recipe_type.",
    ),
}


# ---------------------------------------------------------------------------
# Backwards-compat: legacy "type" values map to new recipe_type names
# ---------------------------------------------------------------------------

_LEGACY_TYPE_MAP: Dict[str, str] = {
    # The old ``type: "config-validation"`` (dashed form) maps to the new
    # ``recipe_type: "config_validation"`` (underscored). Keeping this
    # mapping means irb_si_rejection continues to work without rewriting
    # its ``type`` field immediately.
    "config-validation": "config_validation",
    "config_validation": "config_validation",
    "clear-matrix": "clear_matrix",
    "move-matrix": "move_matrix",
    "bulk-learn": "bulk_learn",
    "pw-suppression": "pw_suppression",
}


def get_profile(recipe: Optional[Dict[str, Any]]) -> RecipeProfile:
    """Return the :class:`RecipeProfile` for ``recipe``.

    Resolution order:
      1. ``recipe.recipe_type`` (new canonical field).
      2. ``recipe.type`` mapped via ``_LEGACY_TYPE_MAP`` (back-compat).
      3. ``default`` profile.

    Never raises -- an unknown recipe_type falls back to ``default`` so
    the orchestrator never crashes on a stray recipe file.
    """
    if not isinstance(recipe, dict):
        return _PROFILES["default"]

    recipe_type = recipe.get("recipe_type")
    if isinstance(recipe_type, str) and recipe_type in _PROFILES:
        return _PROFILES[recipe_type]

    legacy_type = recipe.get("type")
    if isinstance(legacy_type, str):
        mapped = _LEGACY_TYPE_MAP.get(legacy_type.lower())
        if mapped and mapped in _PROFILES:
            return _PROFILES[mapped]

    return _PROFILES["default"]


def default_profile() -> RecipeProfile:
    """Public access to the default profile (used as fallback)."""
    return _PROFILES["default"]


def registered_profiles() -> Dict[str, RecipeProfile]:
    """Copy of the profile registry (useful for lint / documentation)."""
    return dict(_PROFILES)


__all__ = [
    "RecipeProfile",
    "default_profile",
    "get_profile",
    "registered_profiles",
]
