"""Unit tests for DNOS flattened-config telemetry parser.

Run:
    PYTHONPATH="topology" python3 topology/tests/test_telemetry_config_parser_unit.py
"""
from __future__ import annotations

import sys
from pathlib import Path


REPO = Path("/home/dn/drivenets-topology-studio")
sys.path.insert(0, str(REPO / "topology"))

from telemetry.config_parser import (  # noqa: E402
    flatten_hierarchical_config,
    parse_ldp_neighbors,
    parse_ospf_neighbors,
    parse_show_config_flatten,
    same_link_subnet,
)


def _assert_eq(actual, expected, label):
    if actual != expected:
        raise SystemExit(f"FAIL {label}: expected {expected!r}, got {actual!r}")
    print(f"ok: {label}")


def test_bundle_and_lacp_config():
    parsed = parse_show_config_flatten("""
interfaces bundle-21 admin-state enabled
interfaces bundle-21 member ge100-0/0/1
interfaces bundle-21 member ge100-0/0/2
interfaces ge100-0/0/3 bundle-id 21
interfaces bundle-21 lacp mode active
interfaces bundle-21 lacp period short
interfaces bundle-21 min-links 1
""")
    bundle = parsed.bundles["bundle-21"]
    _assert_eq(bundle.admin_state, "enabled", "bundle admin-state parsed")
    _assert_eq(bundle.lacp_mode, "active", "bundle lacp mode parsed")
    _assert_eq(bundle.lacp_period, "short", "bundle lacp period parsed")
    _assert_eq([m.interface for m in bundle.members], ["ge100-0/0/1", "ge100-0/0/2", "ge100-0/0/3"], "bundle members parsed")


def test_sub_bundle_l3vpn_attachment():
    parsed = parse_show_config_flatten("""
interfaces bundle-21.100 encapsulation dot1q 100 second-dot1q 200
interfaces bundle-21.100 mtu 9200
interfaces bundle-21.100 ipv4-address 10.0.0.1/31
network-services vrf CUST_A interface bundle-21.100
protocols isis CORE interface bundle-21.100
""")
    sub = parsed.subifs["bundle-21.100"]
    _assert_eq(sub.parent, "bundle-21", "sub-bundle parent parsed")
    _assert_eq(sub.outer_vlan, "100", "sub-bundle outer vlan parsed")
    _assert_eq(sub.inner_vlan, "200", "sub-bundle inner vlan parsed")
    _assert_eq(sub.mtu, "9200", "sub-bundle mtu parsed")
    _assert_eq(parsed.attachments["bundle-21.100"].kind, "l3vpn", "l3vpn attachment parsed")
    _assert_eq(parsed.protocols["bundle-21.100"].isis, "configured", "isis protocol parsed")


def test_bridge_domain_attachment():
    parsed = parse_show_config_flatten("""
interfaces ge100-0/0/1.300 vlan-id 300
network-services bridge-domain BD300 interface ge100-0/0/1.300
""")
    sub = parsed.subifs["ge100-0/0/1.300"]
    _assert_eq(sub.parent, "ge100-0/0/1", "physical subinterface parent parsed")
    _assert_eq(parsed.attachments["ge100-0/0/1.300"].kind, "bridge-domain", "bridge-domain attachment parsed")
    _assert_eq(parsed.attachments["ge100-0/0/1.300"].bridge_domain, "BD300", "bridge-domain name parsed")


def test_vlan_tagging_outer_inner_variants():
    parsed = parse_show_config_flatten("""
interfaces ge100-18/0/0.210 vlan-tagging outer-tag 210 inner-tag 310 tpid 0x8100
interfaces ge100-18/0/1.220 outer-vlan 220
interfaces ge100-18/0/1.220 inner-vlan 320
""")
    stacked = parsed.subifs["ge100-18/0/0.210"]
    _assert_eq(stacked.outer_vlan, "210", "vlan-tagging outer tag parsed")
    _assert_eq(stacked.inner_vlan, "310", "vlan-tagging inner tag parsed")
    _assert_eq(stacked.tpid, "0x8100", "vlan-tagging tpid parsed")
    split = parsed.subifs["ge100-18/0/1.220"]
    _assert_eq(split.outer_vlan, "220", "outer-vlan alias parsed")
    _assert_eq(split.inner_vlan, "320", "inner-vlan alias parsed")


def test_same_link_subnet():
    _assert_eq(same_link_subnet("10.0.0.0/31", "10.0.0.1/31"), True, "same /31 subnet matches")
    _assert_eq(same_link_subnet("10.0.0.0/31", "10.0.0.2/31"), False, "different /31 subnet rejected")


def test_hierarchical_scaler_config_flattening():
    config = """
interfaces
  bundle-9
    mtu 9100
    member ge100-0/0/9
    lacp
      mode active
    !
  !
  bundle-9.24
    encapsulation dot1q 24
    ipv4-address 20.0.0.1/31
  !
  bundle-9.24.300
    ipv4-address 20.0.1.1/31
  !
!
network-services
  vrf CUST24
    interface bundle-9.24
  !
!
"""
    flat = flatten_hierarchical_config(config)
    _assert_eq("interfaces bundle-9 member ge100-0/0/9" in flat, True, "hierarchical member flattened")
    parsed = parse_show_config_flatten(config)
    _assert_eq(parsed.bundles["bundle-9"].members[0].interface, "ge100-0/0/9", "cached scaler bundle parsed")
    _assert_eq(parsed.bundles["bundle-9"].mtu, "9100", "cached scaler bundle mtu parsed")
    _assert_eq(parsed.subifs["bundle-9.24"].outer_vlan, "24", "cached scaler vlan parsed")
    _assert_eq(parsed.subifs["bundle-9.24.300"].outer_vlan, "24", "cached scaler qinq outer vlan parsed")
    _assert_eq(parsed.subifs["bundle-9.24.300"].inner_vlan, "300", "cached scaler qinq inner vlan parsed")
    _assert_eq(parsed.attachments["bundle-9.24"].kind, "l3vpn", "cached scaler vrf attachment parsed")


def test_operational_protocol_parsers():
    ospf = parse_ospf_neighbors("""
Neighbor ID      Pri State           Dead Time Address         Interface                   Uptime        RXmtL RqstL DBsmL
2.2.2.2           1 Full              36.483s 12.12.4.2       ge100-0/0/4:12.12.4.1        2m47s         0     0     0
""")
    _assert_eq(ospf["ge100-0/0/4"], "Full", "ospf neighbor state parsed")
    ldp = parse_ldp_neighbors("""
Peer LDP Identifier: 2.2.2.2:0
  TCP connection: 1.1.1.1:646 - 2.2.2.2:34719
  State: OPERATIONAL
""")
    _assert_eq(ldp["2.2.2.2:0"], "OPERATIONAL", "ldp neighbor state parsed")


if __name__ == "__main__":
    test_bundle_and_lacp_config()
    test_sub_bundle_l3vpn_attachment()
    test_bridge_domain_attachment()
    test_vlan_tagging_outer_inner_variants()
    test_same_link_subnet()
    test_hierarchical_scaler_config_flattening()
    test_operational_protocol_parsers()
    print("All telemetry config parser tests passed")
