"""Unit tests for live link telemetry parsers.

Run:
    PYTHONPATH="topology" python3 topology/tests/test_telemetry_parsers_unit.py
"""
from __future__ import annotations

import sys
from pathlib import Path


REPO = Path("/home/dn/drivenets-topology-studio")
sys.path.insert(0, str(REPO / "topology"))

from telemetry.parsers import (  # noqa: E402
    merge_interface_facts,
    parse_interfaces,
    parse_interfaces_description,
    parse_lacp_interfaces,
    parse_lldp_neighbors,
)
from telemetry.config_parser import parse_show_config_flatten  # noqa: E402
from telemetry.ssh_provider import SshTelemetryProvider  # noqa: E402


def _assert_eq(actual, expected, label):
    if actual != expected:
        raise SystemExit(f"FAIL {label}: expected {expected!r}, got {actual!r}")
    print(f"ok: {label}")


def test_interfaces_description():
    output = """
| Interface       | Admin    | Operational | Speed | MTU  | Description          |
+-----------------+----------+-------------+-------+------+----------------------+
| bundle-21       | enabled  | up          | 200G  | 9216 | LAG to PE-2          |
| ge100-0/0/1     | enabled  | up          | 100G  | 9216 | Physical to PE-2     |
| ge100-0/0/1.100 | enabled  | up          |       | 9100 | VLAN 100             |
| bundle-21.100.7 | enabled  | up          |       | 9100 | QinQ VLAN 100/7      |
"""
    physical, subifs, bundles = parse_interfaces_description(output)
    _assert_eq(physical[0].name, "ge100-0/0/1", "physical interface parsed")
    _assert_eq(physical[0].mtu, "9216", "physical MTU parsed")
    _assert_eq(physical[0].speed, "100G", "physical speed parsed")
    _assert_eq(subifs[0].parent, "ge100-0/0/1", "subinterface parent parsed")
    _assert_eq(subifs[0].outer_vlan, "100", "subinterface VLAN parsed")
    _assert_eq(subifs[0].mtu, "9100", "subinterface MTU parsed")
    _assert_eq(subifs[1].outer_vlan, "100", "qinq outer VLAN parsed")
    _assert_eq(subifs[1].inner_vlan, "7", "qinq inner VLAN parsed")
    _assert_eq(bundles[0].name, "bundle-21", "bundle parsed")
    _assert_eq(bundles[0].mtu, "9216", "bundle MTU parsed")


def test_show_interfaces_vlan_stack_overrides_display_suffix():
    output = """
Legend: i - inner vlan
| Interface                  |  Admin   | Operational     | IPv4 Address           | IPv6 Address        | VLAN          | MTU  | Network-Service        | Bundle-Id  |
+----------------------------+----------+-----------------+------------------------+---------------------+---------------+------+------------------------+------------+
| ge100-18/0/0               | enabled  | up              |                        |                     |               | 9216 | VRF (default)          |            |
| ge100-18/0/0.100           | enabled  | up              | 10.99.100.2/30         |                     | 219, 100(i)   | 9224 | VRF (ALPHA)            |            |
| ge100-18/0/0.3101 (L2)     | enabled  | up              |                        |                     | 219, 3101(i)  | 9224 | EVPN (EVPN_PW_S001)    |            |
"""
    physical, subifs, _ = parse_interfaces(output)
    _assert_eq(physical[0].name, "ge100-18/0/0", "show interfaces physical parsed")
    _assert_eq(subifs[0].name, "ge100-18/0/0.100", "show interfaces L3 subif name parsed")
    _assert_eq(subifs[0].outer_vlan, "219", "show interfaces outer VLAN parsed")
    _assert_eq(subifs[0].inner_vlan, "100", "show interfaces inner VLAN parsed")
    _assert_eq(subifs[0].attachment.kind, "l3vpn", "show interfaces VRF attachment parsed")
    _assert_eq(subifs[1].name, "ge100-18/0/0.3101", "show interfaces removes L2 display suffix")
    _assert_eq(subifs[1].outer_vlan, "219", "show interfaces L2 outer VLAN parsed")
    _assert_eq(subifs[1].inner_vlan, "3101", "show interfaces L2 inner VLAN parsed")
    _assert_eq(subifs[1].attachment.kind, "evpn-vpls", "show interfaces EVPN attachment parsed")


def test_show_interfaces_operational_facts_override_description_suffix_vlan():
    desc = """
| Interface              | Admin    | Operational | Speed | MTU  | Description |
+------------------------+----------+-------------+-------+------+-------------+
| bundle-100.215 (L2)    | enabled  | up          |       | 9216 | from desc   |
"""
    show = """
| Interface              | Admin    | Operational | IPv4 Address | IPv6 Address | VLAN       | MTU  | Network-Service      | Bundle-Id |
+------------------------+----------+-------------+--------------+--------------+------------+------+----------------------+-----------+
| bundle-100.215 (L2)    | enabled  | up          |              |              | 4, 215(i)  | 9224 | EVPN (plain-l3)      |           |
"""
    physical, subifs, bundles = parse_interfaces_description(desc)
    oper_physical, oper_subifs, oper_bundles = parse_interfaces(show)
    _, merged_subifs, _ = merge_interface_facts(physical, subifs, bundles, oper_physical, oper_subifs, oper_bundles)
    _assert_eq(merged_subifs[0].name, "bundle-100.215", "merged subif name is clean")
    _assert_eq(merged_subifs[0].outer_vlan, "4", "show interfaces overrides display suffix outer VLAN")
    _assert_eq(merged_subifs[0].inner_vlan, "215", "show interfaces fills inner VLAN")
    _assert_eq(merged_subifs[0].mtu, "9224", "show interfaces overrides MTU")


def test_config_merge_does_not_overwrite_operational_vlan_stack():
    row = parse_interfaces("""
| Interface              | Admin    | Operational | IPv4 Address | IPv6 Address | VLAN       | MTU  | Network-Service      | Bundle-Id |
+------------------------+----------+-------------+--------------+--------------+------------+------+----------------------+-----------+
| ge100-0/0/3.210        | enabled  | up          |              |              |            | 9224 | EVPN (PW)            |           |
""")[1][0]
    cfg = parse_show_config_flatten("""
interfaces ge100-0/0/3.210 vlan-id list
interfaces ge100-0/0/3.210 inner-vlan 215
""")
    subifs = [row]
    SshTelemetryProvider()._merge_config_facts([], [], subifs, cfg, {}, {}, {}, {})
    _assert_eq(subifs[0].outer_vlan, "210", "operational suffix VLAN survives non-scalar config")
    _assert_eq(subifs[0].inner_vlan, "215", "scalar config can fill missing inner VLAN")


def test_lldp_neighbors():
    output = """
| Interface    | Neighbor System Name | Neighbor interface | Neighbor TTL |
|--------------+----------------------+--------------------+--------------|
| ge100-0/0/1  | PE-2                 | ge100-0/0/2        | 120          |
"""
    rows = parse_lldp_neighbors(output, device="PE-1")
    _assert_eq(rows[0].local_interface, "ge100-0/0/1", "lldp local interface parsed")
    _assert_eq(rows[0].peer_hostname, "PE-2", "lldp peer hostname parsed")
    _assert_eq(rows[0].peer_interface, "ge100-0/0/2", "lldp peer interface parsed")


def test_lacp_interfaces():
    output = """
Local:
Aggregate Interface: bundle-21
Mode: active, Period: short, Key: 21
System-priority: 1, System-id: 11:22:33:44:55:66
Force-up: disabled

| Interface    | Role       | Port State | Protocol State |
|--------------+------------+------------+----------------|
| ge100-0/0/1  | actor      | a/s/c/d    | synchronized   |
"""
    rows = parse_lacp_interfaces(output)
    _assert_eq(rows[0].name, "bundle-21", "lacp bundle parsed")
    _assert_eq(rows[0].lacp_system_id, "11:22:33:44:55:66", "lacp system-id parsed")
    _assert_eq(rows[0].members[0].interface, "ge100-0/0/1", "lacp member parsed")


def test_config_vlan_manipulation():
    output = """
interfaces bundle-21.100 vlan-id 100 tpid 0x8100
interfaces bundle-21.100 vlan-manipulation egress-mapping action pop-swap outer-tag 200 outer-tpid 0x9100
"""
    parsed = parse_show_config_flatten(output)
    subif = parsed.subifs["bundle-21.100"]
    _assert_eq(subif.outer_vlan, "100", "config outer VLAN parsed")
    _assert_eq(subif.vlan_manipulation_egress, "pop-swap outer-tag 200 outer-tpid 0x9100", "config VLAN manipulation parsed")


if __name__ == "__main__":
    test_interfaces_description()
    test_show_interfaces_vlan_stack_overrides_display_suffix()
    test_show_interfaces_operational_facts_override_description_suffix_vlan()
    test_config_merge_does_not_overwrite_operational_vlan_stack()
    test_lldp_neighbors()
    test_lacp_interfaces()
    test_config_vlan_manipulation()
    print("All telemetry parser tests passed")
