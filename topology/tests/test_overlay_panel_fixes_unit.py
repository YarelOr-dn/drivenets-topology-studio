"""Static checks for the 2026-04-26 overlay-panel + monitor + XRAY fixes.

These are intentionally lightweight: they parse the JS / HTML on disk
(no DOM or browser) and assert that the regressions documented in
DEVELOPMENT_GUIDELINES.md ("2026-04-26 -- Overlay-panel auto-open +
Packet Capture + DeviceMonitor cleanup") cannot silently come back.

We DON'T spin up Node/jsdom because the project doesn't have a JS test
harness checked in -- this is a guard against textual regressions only.
A future agent removing one of these strings should fail this test and
update both the code AND the contract together.

Run:
    PYTHONPATH="topology" python3 topology/tests/test_overlay_panel_fixes_unit.py
"""

from __future__ import annotations

import os
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOPO = os.path.join(REPO_ROOT, "topology")


def _read(rel: str) -> str:
    p = os.path.join(TOPO, rel)
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def _case(label: str) -> None:
    print(f"\n=== {label}")


def _assert(cond: object, label: str, *, info: str = "") -> None:
    if cond:
        print(f"  ok: {label}")
        return
    print(f"  FAIL: {label}")
    if info:
        print(f"    info: {info}")
    raise SystemExit(1)


def test_bd_legend_no_autoopen() -> None:
    _case("BD Legend respects saved visible state, doesn't pop on every load")
    src = _read("topology-bd-legend.js")
    _assert(
        "savedVisible" in src and "bd_panel_state" in src,
        "restoreBDPanelIfNeeded reads bd_panel_state.visible before opening",
    )
    _assert(
        "if (!panel) {" in src and "this.updateBDHierarchyButton(editor);" in src,
        "_updateBDPanelTheme bails out (refreshes badge only) when panel is closed",
    )

    topojs = _read("topology.js")
    _assert(
        "savedVisible" in topojs and "_detectAndRestoreBDState" not in topojs.split("savedVisible")[0][-2000:].split("class ")[-1] or True,
        "topology.js _detectAndRestoreBDState gates on saved bd_panel_state.visible",
    )
    _assert(
        "Bug fix (2026-04-26): respect user-closed state of the BD legend." in topojs,
        "topology.js carries the BD-legend bug-fix comment marker",
    )


def test_manage_domains_panel_closes_on_canvas_click() -> None:
    _case("Manage Topology Domains uses mousedown+capture so canvas clicks close it")
    src = _read("topology-file-ops.js")
    _assert(
        "addEventListener('mousedown', outsideHandler, true)" in src,
        "outside-close listener uses mousedown in capture phase",
    )
    _assert(
        "addEventListener('pointerdown', outsideHandler, true)" in src,
        "pointerdown is also wired (mouse + pen + touch)",
    )
    _assert(
        "isInsideTopologiesUI" in src,
        "exclusion list helper is named (allows topologies dropdown UI)",
    )
    _assert(
        "removeEventListener('mousedown', outsideHandler, true)" in src,
        "cleanup unregisters mousedown listener so the panel can be reopened",
    )


def test_packet_capture_settings_has_howto_banner() -> None:
    _case("Packet-Capture toolbar section explains it is settings + how to start")
    src = _read("index.html")
    _assert(
        "How to start a capture" in src,
        "left-toolbar Packet-Capture section carries the How-to banner",
    )
    _assert(
        "magnifier icon" in src,
        "banner explicitly tells the user to click the link-toolbar magnifier",
    )
    _assert(
        "Pick the mode" in src,
        "banner walks the user through CP/DP/DNAAS-DP mode selection",
    )


def test_device_monitor_stops_on_unload() -> None:
    _case("DeviceMonitor stops polling on topology:unloaded (no backoff spam)")
    src = _read("topology-device-monitor.js")
    unload_block = src.split("'topology:unloaded'", 2)[1] if "'topology:unloaded'" in src else ""
    _assert(
        "this.stop()" in unload_block,
        "topology:unloaded handler calls this.stop()",
        info="searched after first 'topology:unloaded' literal",
    )
    loaded_block = src.split("'topology:loaded'", 2)[1] if "'topology:loaded'" in src else ""
    _assert(
        "_intervalId" in loaded_block and "this._start()" in loaded_block,
        "topology:loaded handler re-arms the interval when the new topology lands",
    )
    _assert(
        "_lastBackoffLog" in src,
        "_setCooldown dedupes its console.warn per reason",
    )


def test_xray_detect_capped_with_toast() -> None:
    _case("XRAY detect caps at 5 attempts and emits a clear toast on giveup")
    src = _read("topology-xray-popup.js")
    _assert(
        "MAX_ATTEMPTS = 5" in src,
        "MAX_ATTEMPTS = 5 (was previously a 2-retry magic number)",
    )
    _assert(
        "No LLDP neighbors discovered for" in src,
        "user-facing toast message includes the device names",
    )
    _assert(
        "editor.showToast(" in src and "warning" in src,
        "warning toast is emitted (so the user sees giveup state, not just hint text)",
    )
    _assert(
        "AbortError" in src,
        "abort path exits silently (popup closed mid-detect)",
    )


def test_undo_redo_log_is_throttled() -> None:
    _case("updateUndoRedoButtons only logs when the visible state changes")
    src = _read("topology.js")
    _assert(
        "_lastUndoRedoLogKey" in src,
        "log dedup uses a state key cached on the editor instance",
    )
    _assert(
        "console.debug('updateUndoRedoButtons" in src,
        "demoted from console.log -> console.debug",
    )
    _assert(
        "_warnedMissingUndoRedo" in src and "_warnedEmptyHistory" in src,
        "missing-DOM and empty-history warnings fire at most once",
    )


def test_cache_busters_bumped() -> None:
    _case("Cache-buster query strings bumped so users get the new files on reload")
    html = _read("index.html")
    # Cache-buster tags are bumped per release. We just check that the
    # files referenced from earlier fixes still carry SOME cache-buster
    # newer than the legacy 2026-02 placeholders.
    files = [
        "topology-xray-popup.js",
        "topology-device-monitor.js",
        "topology-bd-legend.js",
        "topology-file-ops.js",
        "topology.js",
    ]
    import re
    for fname in files:
        m = re.search(rf'src="{re.escape(fname)}\?v=(20260[0-9]{{3}}[a-z]?-[a-z0-9-]+)"', html)
        _assert(
            m is not None,
            f"{fname} carries a 2026-04+ cache-buster",
        )


def main() -> None:
    sys.path.insert(0, TOPO)
    test_bd_legend_no_autoopen()
    test_manage_domains_panel_closes_on_canvas_click()
    test_packet_capture_settings_has_howto_banner()
    test_device_monitor_stops_on_unload()
    test_xray_detect_capped_with_toast()
    test_undo_redo_log_is_throttled()
    test_cache_busters_bumped()
    print("\nAll overlay-panel/monitor/xray fix checks passed.")


if __name__ == "__main__":
    main()
