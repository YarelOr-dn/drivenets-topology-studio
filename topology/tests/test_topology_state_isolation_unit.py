#!/usr/bin/env python3
"""Static guards for topology switch/session isolation.

Pins the regression where switching topologies left the previous canvas in the
undo stack or let a stale async load/save write after the active topology moved.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)
    print(f"ok: {msg}")


def test_loaded_topology_resets_history_to_single_baseline() -> None:
    src = _read("topology.js")
    _assert(
        "resetHistoryForTopologyLoad(reason = 'topology-load')" in src,
        "explicit topology-load history reset helper exists",
    )
    _assert(
        "this.history = [state];" in src and "this.historyIndex = 0;" in src,
        "history reset keeps only the loaded topology baseline",
    )
    load_start = src.find("loadTopologyFromData(data, opts = {})")
    assert load_start != -1, "loadTopologyFromData exists"
    load_end = src.find("_syncCanvasWatchers(opts)", load_start)
    block = src[load_start:load_end]
    _assert(
        "this.resetHistoryForTopologyLoad('topology load');" in block
        and "this.saveState();" not in block,
        "topology load does not append to the previous undo stack",
    )


def test_stale_async_loads_and_autosaves_are_generation_guarded() -> None:
    topo = _read("topology.js")
    ops = _read("topology-file-ops.js")
    sync = _read("topology-sync.js")
    _assert(
        "beginTopologySwitch(identity = {})" in topo
        and "isTopologySwitchCurrent(token)" in topo
        and "cancelTopologySwitch(token)" in topo,
        "editor exposes topology switch token guards",
    )
    _assert(
        "generation !== (this._topologyGeneration || 0)" in topo,
        "scheduled autosave checks the topology generation before writing",
    )
    _assert(
        "_beginTopologyLoad(editor, identity)" in ops
        and "_isTopologyLoadCurrent(editor, token)" in ops
        and "_cancelTopologyLoad(editor, token)" in ops,
        "FileOps load paths use switch tokens and cancellation",
    )
    _assert(
        "activeKey !== _activeKey()" in sync,
        "TopologySync ignores stale server refetches after active topology changes",
    )
    _assert(
        "window.TopologyAuth.getCurrentUser" in sync,
        "TopologySync uses the real auth API to identify self-save echoes",
    )
    _assert(
        "Our own save echoed back -- just refresh the base timestamp." in sync,
        "TopologySync suppresses canvas reloads for self-save echo events",
    )


def test_lldp_table_cleans_up_scan_visual_state() -> None:
    lldp = _read("topology-lldp-dialog.js")
    dnaas = _read("topology-dnaas-helpers.js")
    _assert(
        "_stopDeviceScanVisual(editor, device)" in lldp
        and "cleanupForTopologySwitch(editor)" in lldp,
        "LLDP dialog has guarded scan cleanup helpers",
    )
    _assert(
        "self._stopDeviceScanVisual(editor, device);" in lldp,
        "LLDP table render/failure paths stop the scan visual state",
    )
    _assert(
        "topologyGeneration = editor?._topologyGeneration || 0" in dnaas
        and "editor.isTopologySwitchCurrent(topologyGeneration)" in dnaas,
        "LLDP background completion cannot open a stale table after topology switch",
    )


if __name__ == "__main__":
    test_loaded_topology_resets_history_to_single_baseline()
    test_stale_async_loads_and_autosaves_are_generation_guarded()
    test_lldp_table_cleans_up_scan_visual_state()
    print("All topology state isolation checks passed.")
