#!/usr/bin/env python3
"""Sticky auto-curve side selection guards.

These tests pin the contract of `topology-link-auto-curve-side.js` so that
future tweaks cannot silently bring back the curve-flip flicker users
reported when stretching an unbound link past a device.

The JS module is intentionally small and pure (no DOM access). We exercise
it via Node, which we treat as a baseline dev-host requirement (same as the
other JS-shape tests in this folder that grep static files).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "topology-link-auto-curve-side.js"
DRAWING = ROOT / "topology-link-drawing.js"
INDEX_HTML = ROOT / "index.html"


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)
    print(f"ok: {msg}")


def test_module_is_wired_in_html_before_drawing() -> None:
    html = _read("index.html")
    auto_idx = html.find("topology-link-auto-curve-side.js")
    drawing_idx = html.find("topology-link-drawing.js")
    _assert(auto_idx > 0, "topology-link-auto-curve-side.js is referenced in index.html")
    _assert(drawing_idx > 0, "topology-link-drawing.js is referenced in index.html")
    _assert(auto_idx < drawing_idx, "auto-curve-side helper loads before the drawing module")


def test_drawing_uses_sticky_helper_at_both_sites() -> None:
    src = _read("topology-link-drawing.js")
    occurrences = src.count("window.LinkAutoCurveSide")
    # Must be referenced in BOTH repulsion sites (drawLink for connected
    # links and drawUnboundLink for ULs) AND in the no-obstacle / curve-off
    # cleanup branches. We expect at least 6 occurrences:
    #   - 2 `LinkAutoCurveSide.choose(...)` calls (one per repulsion site)
    #   - 4 `LinkAutoCurveSide.clear(...)` calls (no-obstacle + curve-off,
    #     once per drawing path).
    _assert(occurrences >= 6,
            f"drawing module wires the sticky helper at every relevant branch (got {occurrences})")
    _assert(src.count("LinkAutoCurveSide.choose(") == 2,
            "two repulsion sites delegate side selection to the sticky helper")
    _assert(src.count("LinkAutoCurveSide.clear(") >= 4,
            "no-obstacle and curve-off branches clear the cached side")


def test_mouse_move_drives_pointer_side_during_stretch() -> None:
    move_src = _read("topology-mouse-move.js")
    up_src = _read("topology-mouse-up.js")
    _assert("LinkAutoCurveSide.beginStretch(" in move_src,
            "mouse-move captures the frozen anchor->pointer axis at stretch start")
    _assert("LinkAutoCurveSide.updateStretch(" in move_src,
            "mouse-move feeds raw pointer pos to the sticky-side tracker")
    _assert("LinkAutoCurveSide.endStretch(" in up_src,
            "mouse-up tears down per-stretch pointer tracking on release")
    # The updateStretch call MUST be fed the RAW pointer (`pos.x`, `pos.y`)
    # not the snapped `finalX`/`finalY`, otherwise stickiness pulls the
    # signal toward the device and the side decision becomes unreliable.
    _assert("updateStretch(editor.stretchingLink, pos.x, pos.y)" in move_src,
            "stretch tracker uses raw pointer (pre-snap) so user's hand path drives the side")


def test_helper_exposes_documented_constants() -> None:
    src = MODULE.read_text(encoding="utf-8")
    _assert("FLIP_PRESSURE_RATIO = 1.6" in src,
            "FLIP_PRESSURE_RATIO is pinned to 1.6 so casual movement cannot flip the curve")
    _assert("FLIP_ABS_DELTA = 12" in src,
            "FLIP_ABS_DELTA = 12 keeps near-zero pressure noise from flipping the side")
    _assert("EQUAL_EPSILON = 0.5" in src,
            "EQUAL_EPSILON = 0.5 prevents float-noise ties from picking a side")
    _assert("link._autoCurveSide" in src,
            "decision is cached on the link as _autoCurveSide")


def _run_helper_in_node(scenario_js: str) -> dict:
    """Load the helper in a Node sandbox and run a scenario script.

    The helper attaches to `window.LinkAutoCurveSide`, so we shim a minimal
    `window` global before requiring it.
    """
    if shutil.which("node") is None:
        print("skip: node not available")
        return {"_skipped": True}

    harness = textwrap.dedent(f"""
        global.window = {{}};
        global.console = {{ log: () => {{}} }};
        const fs = require('fs');
        const src = fs.readFileSync({json.dumps(str(MODULE))}, 'utf8');
        // The helper uses an IIFE that touches `window`. Eval directly so the
        // attachment happens against our shimmed global.
        eval(src);
        const LinkAutoCurveSide = global.window.LinkAutoCurveSide;
        const out = (function () {{ {scenario_js} }})();
        process.stdout.write(JSON.stringify(out));
    """)
    result = subprocess.run(
        ["node", "-e", harness],
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    return json.loads(result.stdout or "{}")


def test_initial_decision_picks_lower_pressure_side() -> None:
    out = _run_helper_in_node("""
        const link = {};
        // First frame: obstacle on +perp side dominates -> curve toward -perp.
        const a = LinkAutoCurveSide.choose(link, 50, 5);
        // Second frame, same scenario: must remember the side.
        const b = LinkAutoCurveSide.choose(link, 50, 5);
        return { a, b, cached: link._autoCurveSide };
    """)
    if out.get("_skipped"):
        return
    _assert(out["a"] == -1, "first decision curves toward the lower-pressure side")
    _assert(out["b"] == -1, "second decision keeps the cached side when the geometry is unchanged")
    _assert(out["cached"] == -1, "cached side persists on the link")


def test_small_drift_does_not_flip_the_side() -> None:
    out = _run_helper_in_node("""
        const link = {};
        // Strong initial preference for the -perp side.
        LinkAutoCurveSide.choose(link, 80, 10);
        // The user nudges the obstacle: pressures swap by a small margin.
        // 14 vs 12 is within both the ratio AND the absolute delta floor,
        // so the cached side MUST hold.
        const drift = LinkAutoCurveSide.choose(link, 12, 14);
        return { drift, cached: link._autoCurveSide };
    """)
    if out.get("_skipped"):
        return
    _assert(out["drift"] == -1,
            "a 2-unit pressure swap does not flip the curve side (this was the user-reported flicker)")
    _assert(out["cached"] == -1, "cached side is unchanged after small drift")


def test_clearly_dominant_opposite_side_does_flip() -> None:
    out = _run_helper_in_node("""
        const link = {};
        // Initial: bend toward -perp (positive pressure was higher).
        LinkAutoCurveSide.choose(link, 80, 10);
        // Now the user has dragged the link far past the obstacle: the
        // OPPOSITE side carries massively more pressure (>>1.6x AND
        // absolute delta >> 12). The curve must flip.
        const flipped = LinkAutoCurveSide.choose(link, 5, 200);
        return { flipped, cached: link._autoCurveSide };
    """)
    if out.get("_skipped"):
        return
    _assert(out["flipped"] == 1,
            "decisive opposite-side dominance still flips the curve when the user truly drags past")
    _assert(out["cached"] == 1, "flipped decision is cached for subsequent frames")


def test_clear_resets_so_re_entry_picks_fresh() -> None:
    out = _run_helper_in_node("""
        const link = {};
        LinkAutoCurveSide.choose(link, 80, 10);   // cache -1
        LinkAutoCurveSide.clear(link);            // simulate "no obstacles" frame
        // Now re-enter obstacle field with the OPPOSITE imbalance.
        const next = LinkAutoCurveSide.choose(link, 5, 80);
        return { next, cached: link._autoCurveSide };
    """)
    if out.get("_skipped"):
        return
    _assert(out["next"] == 1,
            "after clear() the next decision is taken fresh, not inherited from before")
    _assert(out["cached"] == 1, "fresh decision is cached afterwards")


def test_pointer_commit_locks_side_and_pressure_is_ignored() -> None:
    out = _run_helper_in_node("""
        const link = {};
        // User starts a stretch from anchor (0,0) with pointer at (100,0).
        LinkAutoCurveSide.beginStretch(link, 0, 0, 100, 0);
        // Tiny jiggle: 5px lateral -> not enough to commit.
        LinkAutoCurveSide.updateStretch(link, 100, -5);
        const beforeCommit = link._autoCurveSidePointerLocked === true;
        // User clearly drags 30px to one side -> must commit and lock.
        LinkAutoCurveSide.updateStretch(link, 100, -30);
        const afterCommit = link._autoCurveSidePointerLocked === true;
        const sideAfter = link._autoCurveSide;
        // Now pressure swings hard the OTHER way -- a pure pressure-based
        // hysteresis would flip, but pointer-lock must hold the side.
        const stillLocked = LinkAutoCurveSide.choose(link, 5, 200);
        return { beforeCommit, afterCommit, sideAfter, stillLocked };
    """)
    if out.get("_skipped"):
        return
    _assert(out["beforeCommit"] is False, "tiny jiggle does not commit a side prematurely")
    _assert(out["afterCommit"] is True, "clear pointer travel commits and engages the lock")
    # 30px lateral on the -refPerp axis -> committedSign = -1 -> auto curve side -1.
    _assert(out["sideAfter"] == -1, "committed pointer side maps to renderer convention (-1)")
    _assert(out["stillLocked"] == -1,
            "pressure cannot override the pointer lock (this is the user-reported bug fix)")


def test_end_stretch_releases_lock_but_keeps_side() -> None:
    out = _run_helper_in_node("""
        const link = {};
        LinkAutoCurveSide.beginStretch(link, 0, 0, 100, 0);
        LinkAutoCurveSide.updateStretch(link, 100, 40);   // commit +1
        const lockedDuring = link._autoCurveSidePointerLocked === true;
        const sideDuring = link._autoCurveSide;
        LinkAutoCurveSide.endStretch(link);
        const lockedAfter = link._autoCurveSidePointerLocked === true;
        const sideAfter = link._autoCurveSide;
        const stretchTrackingGone = link._stretchPointerSide === undefined;
        return { lockedDuring, sideDuring, lockedAfter, sideAfter, stretchTrackingGone };
    """)
    if out.get("_skipped"):
        return
    _assert(out["lockedDuring"] is True, "lock engages while stretch is committed")
    _assert(out["sideDuring"] == 1, "+ref-perp travel maps to side +1")
    _assert(out["lockedAfter"] is False, "endStretch releases the pointer lock")
    _assert(out["sideAfter"] == 1, "endStretch keeps the chosen side cached on the link")
    _assert(out["stretchTrackingGone"] is True, "endStretch tears down per-stretch state")


def test_uncommitted_stretch_does_not_overwrite_existing_side() -> None:
    out = _run_helper_in_node("""
        const link = { _autoCurveSide: -1 };  // existing cached side
        LinkAutoCurveSide.beginStretch(link, 0, 0, 100, 0);
        // User releases without ever committing (light tap).
        LinkAutoCurveSide.updateStretch(link, 100, 3);
        const sideMid = link._autoCurveSide;
        LinkAutoCurveSide.endStretch(link);
        return { sideMid, sideAfter: link._autoCurveSide };
    """)
    if out.get("_skipped"):
        return
    _assert(out["sideMid"] == -1,
            "uncommitted stretch must not overwrite the link's existing cached side")
    _assert(out["sideAfter"] == -1,
            "endStretch on an uncommitted stretch keeps the original cached side")


def test_low_noise_pressures_do_not_flip_on_ratio_alone() -> None:
    out = _run_helper_in_node("""
        const link = {};
        LinkAutoCurveSide.choose(link, 30, 5);    // cache -1, opposite side = positive
        // Wait -- cache convention: cached -1 means we bend toward -perp,
        // i.e. AWAY from positive obstacles. So oppositeSidePressure is
        // `positive`. Now both pressures collapse to noise: 1 vs 3 is 3x
        // ratio but absolute delta is only 2 -- must NOT flip.
        const noise = LinkAutoCurveSide.choose(link, 3, 1);
        return { noise, cached: link._autoCurveSide };
    """)
    if out.get("_skipped"):
        return
    _assert(out["noise"] == -1,
            "high ratio with tiny absolute delta does not flip the side (anti-noise guard)")


if __name__ == "__main__":
    test_module_is_wired_in_html_before_drawing()
    test_drawing_uses_sticky_helper_at_both_sites()
    test_mouse_move_drives_pointer_side_during_stretch()
    test_helper_exposes_documented_constants()
    test_initial_decision_picks_lower_pressure_side()
    test_small_drift_does_not_flip_the_side()
    test_clearly_dominant_opposite_side_does_flip()
    test_clear_resets_so_re_entry_picks_fresh()
    test_pointer_commit_locks_side_and_pressure_is_ignored()
    test_end_stretch_releases_lock_but_keeps_side()
    test_uncommitted_stretch_does_not_overwrite_existing_side()
    test_low_noise_pressures_do_not_flip_on_ratio_alone()
    print("All sticky auto-curve side checks passed.")
