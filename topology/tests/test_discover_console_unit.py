"""Unit tests for ``_discover_console`` (the console-path discoverer).

Pins the "SN is source of truth" behavior for console discovery: when the
canvas carries a label variant whose literal dir name doesn't exist
(e.g. ``YOR-PE-1`` when only ``PE-1`` exists on disk), the discoverer must
fall back through the canonical-dir resolver to read the serial, and then
use that serial to find the console mapping.

Regression: before the April 2026 fix, ``_discover_console`` would raise
``ValueError("No console mapping found for YOR-PE-1.")`` because:

  * ``configs/YOR-PE-1/operational.json`` doesn't exist (only ``YOR_PE-1``
    with underscore, and even that is empty).
  * ``configs/100.64.4.200/operational.json`` doesn't exist (IPs aren't
    dir names).
  * ``get_console_config_for_device("YOR-PE-1")`` does a case-insensitive
    **exact** match so the ``YOR_PE-1`` alias (underscore) doesn't match
    the hyphen variant.

After the fix, ``_resolve_config_dir("YOR-PE-1")`` finds ``PE-1`` via
partial-match, reads the serial ``WK31D7VV00023`` from it, and the
``serial_to_console`` entry in ``console_mappings.json`` resolves the
console.

Covered cases (all must pass or the script exits 1):

  1. Label with hyphen + no IP: ``YOR-PE-1`` -> ``console-d16`` port 1,
     and ``resolved_via == sn_via_canonical_dir:YOR-PE-1->PE-1``.
  2. Label with hyphen + stale IP: same outcome; stale IP is ignored
     for console purposes since the serial wins.
  3. Label with underscore: ``YOR_PE-1`` -> ``console-d16`` port 1.
     Uses canonical-dir fallback too (dir is empty on disk).
  4. Canonical label: ``PE-1`` -> ``console-d16`` port 1, and
     ``resolved_via is None`` (no fallback was needed).
  5. Unregistered device: raises ``ValueError`` (unchanged).
  6. Serial ``-P<N>`` suffix is displayed as a serial hint, not as a
     DNOS NCP slot/interface number.

Run:

    PYTHONPATH="topology:scaler" python3 topology/tests/test_discover_console_unit.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


def _case(label: str) -> None:
    print(f"\n=== {label}")


def _make_scaler_root(tmp: Path) -> Path:
    """Mint a minimal SCALER_ROOT tree matching the lab state on 2026-04-24.

    - PE-1/operational.json: fresh serial/IP (source of truth).
    - YOR_PE-1/: empty dir (looks like a stale device dir).
    - console_mappings.json: has ``YOR_PE-1`` (underscore) as an alias
      AND ``serial_to_console[WK31D7VV00023]``. Notably does NOT have
      ``YOR-PE-1`` (hyphen) as an alias -- that's the exact gap the
      canonical-dir fallback is meant to bridge.
    """
    cfg = tmp / "db" / "configs"
    cfg.mkdir(parents=True, exist_ok=True)

    (cfg / "PE-1").mkdir(parents=True, exist_ok=True)
    (cfg / "PE-1" / "operational.json").write_text(json.dumps({
        "serial_number": "WK31D7VV00023",
        "mgmt_ip": "100.64.3.9/20",
        "ssh_host": "100.64.3.9",
        "device_state": "DNOS",
        "dnos_version": "25.4.13.151_dev.dev_v25_4_13_596",
    }))

    # Stale empty sibling dir (mirrors the real on-disk state).
    (cfg / "YOR_PE-1").mkdir(parents=True, exist_ok=True)

    # Minimal console_mappings.json. The 'YOR_PE-1' hostname_aliases entry
    # is underscore -- hyphen variant must go via the SN fallback.
    (tmp / "db" / "console_mappings.json").write_text(json.dumps({
        "console_servers": {
            "console-d16": {
                "host": "console-d16.dev.drivenets.net",
                "user": "root",
                "password": "dn123!@#",
                "ports": {
                    "1": {
                        "hostname": "PE-1",
                        "serial_number": "WK31D7VV00023",
                        "hostname_aliases": ["YOR_PE-1"],
                    },
                },
            },
        },
        "device_to_console": {
            "PE-1":     {"console_server": "console-d16", "port": "1"},
            "YOR_PE-1": {"console_server": "console-d16", "port": "1"},
        },
        "serial_to_console": {
            "WK31D7VV00023": {"console_server": "console-d16", "port": "1"},
        },
    }))
    # Empty devices.json so legacy fallbacks don't muddy things.
    (tmp / "db" / "devices.json").write_text(json.dumps({"devices": []}))
    return tmp


def main() -> int:
    tmp = Path("/tmp/discover_console_unit")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    _make_scaler_root(tmp)
    os.environ["SCALER_ROOT"] = str(tmp)

    topology_root = Path(__file__).resolve().parents[1]
    repo_root = topology_root.parent
    sys.path.insert(0, str(topology_root))
    sys.path.insert(0, str(repo_root))

    from routes import bridge_helpers as bh

    bh.SCALER_ROOT = str(tmp)
    bh._invalidate_scaler_ops_cache()

    # connection_strategy.py hardcodes /home/dn/SCALER/db/console_mappings.json
    # in _load_console_mappings(), so redirect via monkey-patch rather than
    # touching production code.
    from scaler import connection_strategy as cs

    _fake_mappings_path = tmp / "db" / "console_mappings.json"

    def _fake_load_console_mappings() -> dict:
        if not _fake_mappings_path.exists():
            return {}
        return json.loads(_fake_mappings_path.read_text())

    cs._load_console_mappings = _fake_load_console_mappings

    # Stub out the discovery API shim so we don't reach the real lab.
    def _stub_resolve_device(did: str) -> dict:
        return {}
    bh._resolve_device = _stub_resolve_device

    passed = 0
    failed = 0

    def _expect(label: str, cond: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if cond:
            print(f"  [OK] {label}")
            passed += 1
        else:
            print(f"  [FAIL] {label} -- {detail}")
            failed += 1

    _case("1. YOR-PE-1 (hyphen) + no IP -> console via SN fallback")
    r = bh._discover_console("YOR-PE-1", "", "")
    _expect("console == console-d16.dev.drivenets.net",
            r.get("console_server") == "console-d16.dev.drivenets.net",
            str(r.get("console_server")))
    _expect("port == 1", str(r.get("port")) == "1", str(r.get("port")))
    _expect("serial == WK31D7VV00023",
            r.get("serial_no") == "WK31D7VV00023", str(r.get("serial_no")))
    _expect("resolved_via == sn_via_canonical_dir:YOR-PE-1->PE-1",
            r.get("resolved_via") == "sn_via_canonical_dir:YOR-PE-1->PE-1",
            str(r.get("resolved_via")))

    _case("2. YOR-PE-1 + stale ssh_host IP -> same outcome (IP is ignored)")
    r = bh._discover_console("YOR-PE-1", "", "100.64.4.200")
    _expect("console == console-d16.dev.drivenets.net",
            r.get("console_server") == "console-d16.dev.drivenets.net",
            str(r.get("console_server")))
    _expect("port == 1", str(r.get("port")) == "1", str(r.get("port")))
    _expect("serial == WK31D7VV00023",
            r.get("serial_no") == "WK31D7VV00023", str(r.get("serial_no")))
    _expect("resolved_via == sn_via_canonical_dir:YOR-PE-1->PE-1",
            r.get("resolved_via") == "sn_via_canonical_dir:YOR-PE-1->PE-1",
            str(r.get("resolved_via")))

    _case("3. YOR_PE-1 (underscore, empty dir) -> console via SN fallback")
    r = bh._discover_console("YOR_PE-1", "", "")
    _expect("console == console-d16.dev.drivenets.net",
            r.get("console_server") == "console-d16.dev.drivenets.net",
            str(r.get("console_server")))
    _expect("port == 1", str(r.get("port")) == "1", str(r.get("port")))
    _expect("serial == WK31D7VV00023",
            r.get("serial_no") == "WK31D7VV00023", str(r.get("serial_no")))
    _expect("resolved_via == sn_via_canonical_dir:YOR_PE-1->PE-1",
            r.get("resolved_via") == "sn_via_canonical_dir:YOR_PE-1->PE-1",
            str(r.get("resolved_via")))

    _case("4. PE-1 (canonical) -> no fallback needed, resolved_via is None")
    r = bh._discover_console("PE-1", "", "")
    _expect("console == console-d16.dev.drivenets.net",
            r.get("console_server") == "console-d16.dev.drivenets.net",
            str(r.get("console_server")))
    _expect("port == 1", str(r.get("port")) == "1", str(r.get("port")))
    _expect("serial == WK31D7VV00023",
            r.get("serial_no") == "WK31D7VV00023", str(r.get("serial_no")))
    _expect("resolved_via is None (no override needed)",
            r.get("resolved_via") is None, str(r.get("resolved_via")))

    _case("5. Unregistered device still raises ValueError")
    raised = False
    try:
        bh._discover_console("UNKNOWN-PE-99", "", "")
    except ValueError as exc:
        raised = True
        _expect("error message mentions the unknown device",
                "UNKNOWN-PE-99" in str(exc), str(exc))
    _expect("ValueError raised", raised)

    _case("6. Serial -P suffix is a data-plane hint, not an NCP slot label")
    inferred = bh._infer_console_ncp_target("WDY19C7M00013-P3", {})
    _expect(
        "label == NCP data-plane (serial P3)",
        inferred.get("label") == "NCP data-plane (serial P3)",
        str(inferred),
    )
    _expect(
        "source == serial_suffix",
        inferred.get("source") == "serial_suffix",
        str(inferred),
    )
    explicit = bh._infer_console_ncp_target("", {"ncp_id": "18"})
    _expect(
        "explicit mapping can still show NCP-18",
        explicit.get("label") == "NCP-18",
        str(explicit),
    )

    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
