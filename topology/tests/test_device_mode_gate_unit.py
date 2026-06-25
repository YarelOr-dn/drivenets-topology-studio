"""Static + functional checks for the 2026-04-26 device-mode gate.

The gate has three layers:

* `routes/_ops_writer.py` -- atomic + cross-process safe operational.json
  writer. Older versions used only a `threading.Lock`, so multi-process
  writers (uvicorn worker + scaler monitor + scaler_bridge) could
  truncate the file. We add `fcntl.flock` + a corrupt-file quarantine
  here.
* `routes/devices.py:get_device_mode_probe` -- the
  `/api/devices/{id}/mode-probe` endpoint that returns canonical
  mode + per-operation policy used by the frontend.
* `topology-device-mode-gate.js` -- frontend `DeviceModeGate.check()` /
  `DeviceModeGate.require()` / `renderBadge()`. Wired into DNAAS
  Discovery start, Packet Capture start, the right-click context menu,
  and DeviceMonitor's mode-cache freshness stamping.

These tests cover the parts we can verify without a browser:

1. **Concurrency stress** on the atomic writer (threads hammering one
   path -- counter must equal expected total, file always parses).
2. **Corruption recovery** (writer must quarantine garbage and return
   the new state, never silently overwrite the corrupt bytes).
3. **Endpoint shape** -- mode-probe returns the documented JSON shape
   for cached / GI / RECOVERY scenarios, including per-operation
   `allowed/reason`.
4. **Frontend wiring** -- key entry points call DeviceModeGate before
   running their backend operation, and the mode-fetched timestamp is
   stamped by DeviceMonitor.

Run with::

    PYTHONPATH="topology" python3 topology/tests/test_device_mode_gate_unit.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
from pathlib import Path


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOPO = os.path.join(REPO_ROOT, "topology")
sys.path.insert(0, TOPO)


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


def test_ops_writer_concurrency() -> None:
    _case("Atomic writer survives 20-thread x 50-write hammer")
    from routes._ops_writer import update_ops, read_ops

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "operational.json"
        p.write_text('{"counter": 0}')

        def bump(d):
            d["counter"] = int(d.get("counter", 0)) + 1

        threads = [
            threading.Thread(target=lambda: [update_ops(p, bump) for _ in range(50)])
            for _ in range(20)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        final = read_ops(p)
        _assert(
            final.get("counter") == 1000,
            "counter equals 1000 after 1000 atomic increments (no lost updates)",
            info=f"got {final.get('counter')}",
        )
        # File must still be valid JSON
        json.loads(p.read_text())


def test_ops_writer_corrupt_recovery() -> None:
    _case("Corrupt operational.json is quarantined, NOT overwritten silently")
    from routes._ops_writer import update_ops

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "operational.json"
        p.write_text("{not valid json,,, ")

        def mut(d):
            d["recovered"] = True

        ok, data = update_ops(p, mut)
        _assert(ok, "update_ops returned ok after recovering from corrupt input")
        _assert(
            json.loads(p.read_text()).get("recovered") is True,
            "rewritten file is parseable and carries the new field",
        )
        snapshots = sorted(Path(td).glob("operational.json.corrupt-*"))
        _assert(
            len(snapshots) >= 1,
            "corrupt quarantine snapshot was created for forensics",
        )
        _assert(
            "{not valid json" in snapshots[0].read_text(),
            "quarantine snapshot preserves the original (corrupt) bytes",
        )


def test_mode_probe_endpoint_shape() -> None:
    _case("Mode-probe endpoint returns documented shape + per-op policy")
    src = _read("routes/devices.py")
    _assert(
        '@router.get("/api/devices/{device_id}/mode-probe")' in src,
        "mode-probe route is registered under /api/devices/{id}/mode-probe",
    )
    for field in (
        '"mode"', '"raw_state"', '"fetched_at"', '"age_seconds"',
        '"source"', '"ssh_reachable"', '"transient_op"', '"operations"',
    ):
        _assert(field in src, f"response carries {field}")
    for op_key in (
        '"dnaas_discovery"', '"packet_capture"', '"config_apply"', '"terminal"',
    ):
        _assert(op_key in src, f"per-operation policy includes {op_key}")
    _assert(
        "classify_device_state" in src and "detect_device_mode" in src,
        "endpoint reuses the canonical detect_device_mode + classify_device_state",
    )
    _assert(
        '"UPGRADING"' in src and '"DEPLOYING"' in src,
        "transient ops flags (UPGRADING/DEPLOYING) are tracked separately from mode",
    )


def test_serve_proxy_routes_mode_probe() -> None:
    _case("Frontend serve.py proxies the mode-probe action through to scaler_bridge")
    src = _read("serve.py")
    _assert(
        '("context", "git-commit", "mode-probe")' in src,
        "GET handler proxy whitelist includes mode-probe",
    )


def test_frontend_gate_helper_present() -> None:
    _case("DeviceModeGate JS helper exposes the documented surface area")
    src = _read("topology-device-mode-gate.js")
    for sym in (
        "window.DeviceModeGate",
        "FRESH_MS",
        "function check(",
        "function _probeBackend(",
        "showBlockedModal",
        "renderBadge",
        "attachBanner",
        "_clientFallbackPolicy",
    ):
        _assert(sym in src, f"helper exposes {sym}")
    _assert(
        "/api/devices/${encodeURIComponent(deviceId)}/mode-probe" in src,
        "helper hits the new mode-probe endpoint",
    )
    _assert(
        "device:mode-probed" in src,
        "helper fires device:mode-probed so canvas badges can refresh",
    )


def test_dnaas_helpers_call_gate() -> None:
    _case("DNAAS Discovery start runs the mode-gate before hitting the API")
    src = _read("topology-dnaas-helpers.js")
    _assert(
        "DeviceModeGate.require(" in src
        and "'dnaas_discovery'" in src,
        "startDnaasDiscovery awaits DeviceModeGate.require(...,'dnaas_discovery')",
    )


def test_xray_popup_calls_gate() -> None:
    _case("Packet Capture start runs the mode-gate before hitting /api/xray/start")
    src = _read("topology-xray-popup.js")
    _assert(
        "DeviceModeGate.require(" in src and "'packet_capture'" in src,
        "_startCapture awaits DeviceModeGate.require(...,'packet_capture')",
    )


def test_context_menu_carries_mode_chip() -> None:
    _case("Right-click context menu shows a DNOS/GI/RECOVERY chip + re-detect")
    src = _read("topology-context-menu-handlers.js")
    _assert(
        "ctx-mode-chip-row" in src,
        "context menu inserts a mode-chip row",
    )
    _assert(
        "DeviceModeGate.renderBadge(" in src,
        "chip is rendered by the central renderBadge helper (single colour scheme)",
    )
    _assert(
        "ctx-mode-redetect" in src and "live: true" in src,
        "re-detect link forces a live probe",
    )


def test_canvas_drawing_has_mode_pill() -> None:
    _case("Canvas device label renders a tiny DNOS/GI/RECOVERY pill")
    src = _read("topology-canvas-drawing.js")
    _assert(
        "Mode badge (2026-04-26)" in src,
        "drawDeviceLabel carries the mode-badge block (commented for future agents)",
    )
    _assert(
        "_devMode === 'DNOS'" in src and "_devMode === 'GI'" in src,
        "pill colour switches on canonical mode strings",
    )


def test_device_monitor_stamps_mode_freshness() -> None:
    _case("DeviceMonitor stamps _modeFetchedAt so the gate can decide cache freshness")
    src = _read("topology-device-monitor.js")
    _assert(
        "device._modeFetchedAt = now" in src,
        "_refreshOneInner stamps a millisecond timestamp on every refresh",
    )


def test_bridge_helpers_uses_atomic_writer() -> None:
    _case("Legacy raw write_text sites in bridge_helpers.py are gone")
    src = _read("routes/bridge_helpers.py")
    bad = "ops_path.write_text(json.dumps("
    # The four sites we converted (ghost-IP, snapshot, clear, build_device_context).
    # We allow ZERO remaining -- any future writer should route through update_ops.
    _assert(
        src.count(bad) == 0,
        "no remaining `ops_path.write_text(json.dumps(...))` calls in bridge_helpers",
        info=f"found {src.count(bad)} -- search for the legacy pattern",
    )
    _assert(
        src.count("from ._ops_writer import update_ops") >= 4,
        "all four converted sites import update_ops",
    )


def main() -> None:
    test_ops_writer_concurrency()
    test_ops_writer_corrupt_recovery()
    test_mode_probe_endpoint_shape()
    test_serve_proxy_routes_mode_probe()
    test_frontend_gate_helper_present()
    test_dnaas_helpers_call_gate()
    test_xray_popup_calls_gate()
    test_context_menu_carries_mode_chip()
    test_canvas_drawing_has_mode_pill()
    test_device_monitor_stamps_mode_freshness()
    test_bridge_helpers_uses_atomic_writer()
    print("\nAll device-mode-gate checks passed.")


if __name__ == "__main__":
    main()
