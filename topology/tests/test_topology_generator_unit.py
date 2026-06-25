"""Unit tests for the AI Topology Generator backend route helpers.

Pin-points covered:

  1. _safe_role_hint maps DNOS naming conventions onto the same tier
     buckets the frontend NetworkMapperManager._classifyDevice uses.
     This guarantees the deterministic generator and the live-device
     adapter agree on roles even when LLDP is silent.

  2. _normalize_lldp tolerates the 3-4 historical neighbor field
     spellings (`local_interface` / `local_port` / `local_intf`,
     `peer_hostname` / `neighbor` / `system_name`, ...) and trims
     unknown rows. Regression target: the LLDP merge in
     adapterLive() depends on stable keys.

  3. _config_facts_from_summary keeps the small subset of fields the
     generator actually uses (asn parsed to int, route_targets capped,
     evpn_services dict-only) and never blows up on partial inputs.

Run:
    PYTHONPATH="topology" python3 topology/tests/test_topology_generator_unit.py
"""
from __future__ import annotations

import os
import sys


def _case(label: str) -> None:
    print(f"\n=== {label}")


def _assert_eq(actual, expected, label: str) -> None:
    if actual == expected:
        print(f"  ok: {label}")
        return
    print(f"  FAIL: {label}")
    print(f"    expected: {expected!r}")
    print(f"    actual:   {actual!r}")
    raise SystemExit(1)


def main() -> None:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
    from routes.topology_generator import (
        _config_facts_from_summary,
        _normalize_lldp,
        _safe_role_hint,
    )

    _case("_safe_role_hint maps host/system-type onto tier buckets")
    _assert_eq(_safe_role_hint("YOR-NCM-SPINE-1", "ncm-1"),    "super-spine", "NCM goes super-spine")
    _assert_eq(_safe_role_hint("spine-1",       ""),           "spine",       "spine name -> spine")
    _assert_eq(_safe_role_hint("YOR-NCF-LEAF",  "ncf-1"),      "leaf",        "NCF -> leaf")
    _assert_eq(_safe_role_hint("rr-1",          "ncc-1"),      "rr",          "NCC -> rr")
    _assert_eq(_safe_role_hint("YOR-PE-1",      ""),           "pe",          "pe in name -> pe")
    _assert_eq(_safe_role_hint("ce-site-a",     ""),           "ce",          "ce in name -> ce")
    _assert_eq(_safe_role_hint("exabgp-tester", ""),           "external",    "exabgp -> external")
    _assert_eq(_safe_role_hint("dut-1",         "cl-1"),       "pe",          "dut hits pe before cluster")
    _assert_eq(_safe_role_hint("clusterhead",   "cl-1"),       "ncr",         "cl- system_type -> ncr")
    _assert_eq(_safe_role_hint("",              ""),           "router",      "fallback router")

    _case("_normalize_lldp tolerates field-name aliases")
    rows_in = [
        {"local_interface": "ge100-0/0/1", "peer_hostname": "spine1", "peer_interface": "ge100-0/0/2"},
        {"local_port":      "ge100-0/0/3", "neighbor":       "spine2", "peer_port":      "ge100-0/0/4"},
        {"local_intf":      "ge100-0/0/5", "system_name":    "spine3", "port_id":        "ge100-0/0/6", "chassis_id": "AA:BB"},
        "not-a-dict",
        None,
    ]
    rows_out = _normalize_lldp(rows_in)
    _assert_eq(len(rows_out), 3, "non-dict rows dropped")
    _assert_eq(rows_out[0]["local_interface"], "ge100-0/0/1", "row0 local_interface")
    _assert_eq(rows_out[1]["local_interface"], "ge100-0/0/3", "row1 local_port -> local_interface")
    _assert_eq(rows_out[1]["peer_hostname"],    "spine2",     "row1 neighbor -> peer_hostname")
    _assert_eq(rows_out[2]["peer_interface"],   "ge100-0/0/6", "row2 port_id -> peer_interface")
    _assert_eq(rows_out[2]["peer_chassis_id"],  "AA:BB",      "row2 chassis_id passes through")

    _case("_config_facts_from_summary picks the small subset and parses asn")
    summary = {
        "as_number": "65000",
        "route_targets": [str(i) for i in range(80)],
        "evpn_services": {"l2": 3, "l3": 1},
        "lines": "412",
        "loopback0_ip": "10.0.0.1",
        "router_id": "10.0.0.1",
    }
    facts = _config_facts_from_summary(summary)
    _assert_eq(facts["asn"], 65000, "asn parsed to int")
    _assert_eq(len(facts["route_targets"]), 64, "route_targets capped at 64")
    _assert_eq(facts["evpn_services"], {"l2": 3, "l3": 1}, "evpn_services preserved as-is")
    _assert_eq(facts["summary_lines"], 412, "summary_lines parsed to int")
    _assert_eq(facts["loopback0_ip"], "10.0.0.1", "loopback0_ip preserved")
    _assert_eq(facts["router_id"], "10.0.0.1", "router_id preserved")

    bad_summary = {"as_number": "abc", "route_targets": "not-a-list", "evpn_services": "not-a-dict"}
    facts_bad = _config_facts_from_summary(bad_summary)
    _assert_eq(facts_bad["asn"], None, "non-numeric asn -> None (no crash)")
    _assert_eq(facts_bad["route_targets"], [], "non-list rts -> []")
    _assert_eq(facts_bad["evpn_services"], {}, "non-dict evpn_services -> {}")

    _case("_config_facts_from_running extracts richer logical facts")
    from routes.topology_generator import _config_facts_from_running
    sample = "\n".join([
        "vrf RED",
        "vrf BLUE",
        "interfaces ge100-0/0/1",
        "  ipv4 address 10.0.0.1/30",
        "interfaces ge100-0/0/1.100",
        "  ipv4 address 10.0.1.1/30",
        "interfaces bundle-1",
        "  ipv4 address 10.0.2.1/30",
        "bridge-domain BD-100",
        "bridge-domain BD-200",
        "neighbors 10.0.0.2",
        "  remote-as 65001",
        "neighbors 10.0.0.3",
        "  remote-as 65000",
        "route-distinguisher 65000:100",
        "router ospf 1",
        "  area 0",
        "mpls",
        "ldp",
        "segment-routing",
    ])
    rich = _config_facts_from_running(sample)
    _assert_eq(sorted(rich["vrfs"]), ["BLUE", "RED"], "vrfs parsed (mgmt/default filtered)")
    _assert_eq(sorted(rich["bridge_domains"]), ["BD-100", "BD-200"], "bridge domains parsed")
    _assert_eq(rich["bundles"], ["bundle-1"], "bundle interface listed")
    _assert_eq(rich["mpls"]["enabled"], True, "mpls detected")
    _assert_eq(rich["mpls"]["ldp"], True, "ldp detected")
    _assert_eq(rich["mpls"]["sr"], True, "segment-routing detected")
    _assert_eq(rich["ospf"]["area"], "0", "ospf area parsed")
    _assert_eq(rich["route_distinguishers"], ["65000:100"], "RD parsed")
    peer_pairs = sorted([(p["peer"], p["remote_as"]) for p in rich["bgp_peers"]])
    _assert_eq(peer_pairs, [("10.0.0.2", 65001), ("10.0.0.3", 65000)], "bgp peers parsed")

    rich_empty = _config_facts_from_running("")
    _assert_eq(rich_empty["vrfs"], [], "empty config -> empty vrfs")
    _assert_eq(rich_empty["mpls"], {"enabled": False, "ldp": False, "sr": False},
               "empty config -> all mpls flags false")

    print("\nALL TOPOLOGY-GENERATOR UNIT TESTS PASSED")


if __name__ == "__main__":
    main()
