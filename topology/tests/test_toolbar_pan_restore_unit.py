#!/usr/bin/env python3
"""Static guards for selection toolbar behavior during canvas panning."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)
    print(f"ok: {msg}")


def test_pan_hides_and_restores_object_toolbars() -> None:
    core = _read("topology.js")
    mouse_down = _read("topology-mouse-down.js")
    mouse_up = _read("topology-mouse-up.js")
    keyboard = _read("topology-keyboard.js")
    _assert("beginCanvasPanInteraction()" in core, "central pan-start toolbar helper exists")
    _assert("restoreToolbarAfterCanvasPan()" in core, "central pan-end toolbar restore helper exists")
    _assert("_toolbarHiddenForPan" in core, "selected object is remembered while toolbar is hidden")
    _assert("showDeviceSelectionToolbar(current)" in core, "device toolbar restores after panning")
    _assert("showLinkSelectionToolbar(current)" in core, "link toolbar restores after panning")
    _assert("showTextSelectionToolbar(current)" in core, "text toolbar restores after panning")
    _assert("showShapeSelectionToolbar(current)" in core, "shape toolbar restores after panning")
    _assert("XrayPopup.temporaryHide" in core, "central pan-start helper hides active XRAY popup immediately")
    _assert("editor.beginCanvasPanInteraction()" in mouse_down, "mouse pan start hides toolbar through helper")
    _assert("!editor._toolbarHiddenForPan" in _read("topology-mouse-move.js"), "first actual pan movement defensively hides toolbar")
    _assert("editor.restoreToolbarAfterCanvasPan()" in mouse_up, "mouse pan release restores toolbar")
    _assert("editor.beginCanvasPanInteraction()" in keyboard, "keyboard pan start hides toolbar through helper")
    _assert("editor.restoreToolbarAfterCanvasPan()" in keyboard, "keyboard pan release/blur restores toolbar")


def test_refresh_shortcut_preserves_browser_reload_keys() -> None:
    keyboard = _read("topology-keyboard.js")
    _assert("!e.metaKey && !e.ctrlKey && !e.altKey && !e.shiftKey" in keyboard, "plain R refresh does not intercept browser Ctrl/Cmd+R")
    _assert("window.location.reload();" in keyboard, "plain R uses standard reload API")
    _assert("window.location.reload(true)" not in keyboard, "deprecated forced reload API is not used")


if __name__ == "__main__":
    test_pan_hides_and_restores_object_toolbars()
    test_refresh_shortcut_preserves_browser_reload_keys()
    print("All toolbar pan restore checks passed.")
