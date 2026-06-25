"""Unit tests for ``_resolve_mgmt_ip`` (the central device-IP resolver).

Pins the "SN is source of truth" behavior: when the canvas carries a stale
``ssh_host`` IP from a previous session (classic ghost-IP after an upgrade),
the resolver must prefer the live ``operational.json`` match (keyed by
serial/hostname/dir) over the stale IP.

Regression: before the April 2026 fix, ``_resolve_mgmt_ip`` short-circuited
on ``is_ip=True`` and returned the stale IP without ever trying the
device_id / serial / partial-name chain. That made devices like
``YOR-PE-1`` appear unreachable on the canvas even though the serial
``WK31D7VV00023`` in ``operational.json`` already pointed at the fresh
mgmt IP.

Covered cases (all must pass or the script exits 1):

  1. Happy path: ``ssh_host`` IP is the live mgmt IP in operational.json
     -> returned as ``ssh_ip_literal:<ip>``.
  2. Ghost-IP override via partial-name match: ``device_id='YOR-PE-1'``
     with stale ``ssh_host='100.64.4.200'`` resolves to the fresh
     ``100.64.3.9`` via ``partial:pe-1`` and ``resolved_via`` carries
     the ``sn_over_stale_ip:`` prefix.
  3. Ghost-IP override via serial match: ``device_id='WK31D7VV00023'``
     with stale ssh_host resolves to the fresh IP via ``scaler_index``
     and carries the override tag.
  4. Last-resort fallback: ``device_id`` unknown AND ssh_host IP not in
     index -> returns the ssh_host as ``ssh_ip_direct:<ip>``. (Avoids
     regression where unregistered devices could no longer SSH.)
  5. No ssh_host + no resolution -> raises HTTPException(503) as before.

Run:
    PYTHONPATH="topology" python3 topology/tests/test_resolve_mgmt_ip_unit.py
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
    """Mint a minimal SCALER_ROOT tree with two devices.

    - PE-1 dir with a rich operational.json (serial WK31D7VV00023,
      mgmt_ip 100.64.3.9/20). The canvas label 'YOR-PE-1' has no dir
      of its own, mirroring the real lab state on 2026-04-24.
    - YOR_CL_PE-4 dir with a cluster-style operational.json so the
      index has more than one entry.
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
    (cfg / "YOR_CL_PE-4").mkdir(parents=True, exist_ok=True)
    (cfg / "YOR_CL_PE-4" / "operational.json").write_text(json.dumps({
        "hostname": "YOR_CL_PE-4",
        "serial_number": "WDY1A17E00011-P3",
        "mgmt_ip": "100.64.4.122",
        "ssh_host": "100.64.4.122",
        "device_state": "DNOS",
        "ncc_type": "kvm",
    }))
    # Empty sibling dir (mirrors the stale /YOR_PE-1/ on-disk state).
    (cfg / "YOR_PE-1").mkdir(parents=True, exist_ok=True)
    # Empty device_inventory + devices.json so fallbacks don't muddy.
    (tmp / "db" / "devices.json").write_text(json.dumps({"devices": []}))
    return tmp


def main() -> int:
    tmp = Path("/tmp/resolve_mgmt_ip_unit")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    _make_scaler_root(tmp)
    os.environ["SCALER_ROOT"] = str(tmp)

    topology_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(topology_root))

    from fastapi import HTTPException
    from routes import bridge_helpers as bh

    # Force the module to see our fake SCALER_ROOT. The module caches
    # SCALER_ROOT at import time, so patch it and clear every cache.
    bh.SCALER_ROOT = str(tmp)
    try:
        bh.DEVICE_INVENTORY_JSON = tmp / "nonexistent_inventory.json"
    except Exception:
        pass
    bh._invalidate_scaler_ops_cache()

    # Kill the lru-cached discovery API shim so it doesn't return real
    # lab data during the test. The test only cares about ops index /
    # inventory / partial-match paths.
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

    _case("1. Happy path: ssh_host is the live mgmt IP")
    ip, sid, via = bh._resolve_mgmt_ip("YOR-PE-1", "100.64.3.9")
    _expect("ip == 100.64.3.9", ip == "100.64.3.9", ip)
    _expect("scaler_id == PE-1", sid == "PE-1", sid)
    _expect("via starts with ssh_ip_literal", via.startswith("ssh_ip_literal:"), via)

    _case("2. Ghost-IP override: YOR-PE-1 + stale 100.64.4.200 -> 100.64.3.9")
    bh._invalidate_scaler_ops_cache()
    ip, sid, via = bh._resolve_mgmt_ip("YOR-PE-1", "100.64.4.200")
    _expect("ip == 100.64.3.9 (fresh, from operational.json)", ip == "100.64.3.9", ip)
    _expect("scaler_id == PE-1", sid == "PE-1", sid)
    _expect(
        "via carries sn_over_stale_ip prefix",
        via.startswith("sn_over_stale_ip:100.64.4.200->100.64.3.9:"),
        via,
    )
    _expect(
        "inner via is partial:pe-1 (YOR-PE-1 normalizes to YORPE1, contains PE1)",
        via.endswith(":partial:pe-1"),
        via,
    )

    _case("3. Ghost-IP override via serial: WK31D7VV00023 + stale IP")
    bh._invalidate_scaler_ops_cache()
    ip, sid, via = bh._resolve_mgmt_ip("WK31D7VV00023", "100.64.4.200")
    _expect("ip == 100.64.3.9 via serial index hit", ip == "100.64.3.9", ip)
    _expect("scaler_id == PE-1", sid == "PE-1", sid)
    _expect(
        "via carries sn_over_stale_ip prefix with scaler_index inner",
        via.startswith("sn_over_stale_ip:100.64.4.200->100.64.3.9:")
        and "scaler_index" in via,
        via,
    )

    _case("4. Unregistered device: ssh_host IP returned as last resort")
    bh._invalidate_scaler_ops_cache()
    ip, sid, via = bh._resolve_mgmt_ip("brand-new-lab-dut", "203.0.113.77")
    _expect("ip == 203.0.113.77 (user-provided)", ip == "203.0.113.77", ip)
    _expect("scaler_id == device_id (fallback)", sid == "brand-new-lab-dut", sid)
    _expect("via == ssh_ip_direct:<ip>", via == "ssh_ip_direct:203.0.113.77", via)

    _case("5. No ssh_host, no resolution -> 503")
    bh._invalidate_scaler_ops_cache()
    raised = False
    try:
        bh._resolve_mgmt_ip("unknown-device-xyz", "")
    except HTTPException as exc:
        raised = True
        _expect("status_code == 503", exc.status_code == 503, str(exc.status_code))
        _expect(
            "detail mentions the unknown device",
            "unknown-device-xyz" in (exc.detail or ""),
            exc.detail,
        )
    _expect("HTTPException raised", raised)

    _case("6. Happy path hostname lookup isn't broken by the fallback")
    bh._invalidate_scaler_ops_cache()
    ip, sid, via = bh._resolve_mgmt_ip("YOR_CL_PE-4", "")
    _expect("ip == 100.64.4.122", ip == "100.64.4.122", ip)
    _expect("scaler_id == YOR_CL_PE-4", sid == "YOR_CL_PE-4", sid)
    _expect(
        "via is a non-ghost-ip path",
        not via.startswith("sn_over_stale_ip:"),
        via,
    )

    _case("7. Stale placeholder dir inherits serial from console_mappings.json")
    # Mirrors the 2026-04-24 live state: PE-1/ is the serial-rich canonical
    # dir with ssh_host=100.64.2.33, and YOR_PE-1/ is a stale placeholder
    # with device_state=GI, no serial_number, and mgmt_ip=100.64.4.200
    # (which is actually PE-1's announced mgmt_ip from `show system stack`
    # -- the placeholder entry has it as its SSH target, which is wrong).
    # Without the inheritance fix, idx['100.64.4.200'] would point at the
    # stale YOR_PE-1 entry and SSH attempts would dial the wrong address.
    # With the fix, YOR_PE-1 inherits the chassis serial via console_mappings,
    # gets linked to PE-1 as the richer entry in Phase 2, and the stale IP
    # is removed from the index entirely.
    stale_dir = tmp / "db" / "configs" / "YOR_PE-1"
    (stale_dir / "operational.json").write_text(json.dumps({
        "hostname": "YOR_PE-1",
        "device_state": "GI",
        "mgmt_ip": "100.64.4.200",
        "ssh_host": "100.64.4.200",
        # NOTE: no serial_number -- that's the whole point
    }))
    # Write a minimal console_mappings.json with the alias / serial link
    # (mirrors the real DB: PE-1 with hostname_aliases=["YOR_PE-1"] and
    # serial_number=WK31D7VV00023).
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
            "PE-1":     {"console_server": "console-d16", "port": "1",
                          "serial_number": "WK31D7VV00023"},
            "YOR_PE-1": {"console_server": "console-d16", "port": "1",
                          "serial_number": "WK31D7VV00023"},
        },
    }))
    bh._invalidate_scaler_ops_cache()

    idx = bh._build_scaler_ops_index()
    _expect(
        "stale IP 100.64.4.200 no longer owns an index key",
        idx.get("100.64.4.200") is None,
        str(idx.get("100.64.4.200")),
    )
    yor_entry = idx.get("yor_pe-1")
    _expect("idx['yor_pe-1'] exists", yor_entry is not None)
    if yor_entry:
        _expect(
            "idx['yor_pe-1'].ip == 100.64.3.9 (PE-1's live ssh_host)",
            yor_entry.get("ip") == "100.64.3.9", str(yor_entry.get("ip")))
        _expect(
            "idx['yor_pe-1'].scaler_id == PE-1 (redirected to richer sibling)",
            yor_entry.get("scaler_id") == "PE-1", str(yor_entry.get("scaler_id")))

    ip, sid, via = bh._resolve_mgmt_ip("YOR-PE-1", "100.64.4.200")
    _expect("ip == 100.64.3.9 (redirected away from stale placeholder)",
            ip == "100.64.3.9", ip)
    _expect("scaler_id == PE-1", sid == "PE-1", sid)
    _expect(
        "via is sn_over_stale_ip (stale IP in canvas was rejected)",
        via.startswith("sn_over_stale_ip:100.64.4.200->100.64.3.9:"),
        via,
    )

    _case("8. Onboarding guard rejects same-IP cache from another owner")
    # Simulate active-NCC onboarding from a generated canvas label where the
    # typed transport IP is already indexed under an unrelated cached device.
    # The context builder may still use the IP for SSH, but it must not copy
    # the cached owner's stack_components into the new device.
    other_dir = tmp / "db" / "configs" / "OTHER-CLUSTER"
    other_dir.mkdir(parents=True, exist_ok=True)
    (other_dir / "operational.json").write_text(json.dumps({
        "hostname": "OTHER-CLUSTER",
        "serial_number": "SN-OTHER",
        "mgmt_ip": "100.64.4.151",
        "ssh_host": "100.64.4.151",
        "device_state": "DNOS",
        "stack_components": [{"name": "DNOS", "current": "stale-other"}],
        "stack_fetched_at": "2026-05-10T06:00:00Z",
    }))
    bh._invalidate_scaler_ops_cache()
    ctx = bh._get_device_context(
        "NCP-1",
        live=False,
        ssh_host="100.64.4.151",
        identity_guard={
            "requested_device_id": "NCP-1",
            "requested_host": "100.64.4.151",
            "verified_hostname": "NEW-CLUSTER",
            "registry_hostname": "NEW-CLUSTER",
            "registry_serial_number": "SN-NEW",
        },
    )
    _expect("onboarding ctx keeps typed IP as transport", ctx.get("resolved_ip") == "100.64.4.151", str(ctx.get("resolved_ip")))
    _expect("onboarding ctx reports cache owner conflict", bool(ctx.get("cache_owner_conflicts")), str(ctx.get("cache_owner_conflicts")))
    _expect("onboarding ctx does not borrow OTHER-CLUSTER stack", ctx.get("stack") == [], str(ctx.get("stack")))

    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
