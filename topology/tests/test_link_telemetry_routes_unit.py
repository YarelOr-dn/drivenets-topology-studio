"""Unit tests for live link telemetry routes.

Run:
    PYTHONPATH="topology" python3 topology/tests/test_link_telemetry_routes_unit.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace


REPO = Path("/home/dn/drivenets-topology-studio")
sys.path.insert(0, str(REPO / "topology"))

import routes.link_telemetry as routes_mod  # noqa: E402
from telemetry.provider_base import AttachmentInfo, BundleMemberRow, BundleRow, DeviceTelemetry, InterfaceRow, LldpEdge, ProtocolInfo, SubInterfaceRow  # noqa: E402


def _assert_eq(actual, expected, label):
    if actual != expected:
        raise SystemExit(f"FAIL {label}: expected {expected!r}, got {actual!r}")
    print(f"ok: {label}")


def test_refresh_correlates_lldp(monkeypatch=None):
    def fake_fetch(device, app_user, force=False):
        if device.device_id == "PE-1":
            return DeviceTelemetry(
                physical=[InterfaceRow(name="ge100-0/0/1", admin_state="enabled", oper_state="up")],
                lldp=[LldpEdge(device="PE-1", local_interface="ge100-0/0/1", peer_hostname="PE-2", peer_interface="ge100-0/0/2")],
                provider="test",
            )
        return DeviceTelemetry(
            physical=[InterfaceRow(name="ge100-0/0/2", admin_state="enabled", oper_state="up")],
            provider="test",
        )

    old_fetch = routes_mod._fetch_device
    routes_mod._fetch_device = fake_fetch
    try:
        request = SimpleNamespace(state=SimpleNamespace(user="dn", role="engineer"))
        body = {"links": [{"linkId": "l1", "deviceA": {"device_id": "PE-1"}, "deviceB": {"device_id": "PE-2"}}]}
        result = routes_mod.refresh_link_telemetry(body, request)
        row = result["results"][0]
        _assert_eq(row["lldp"]["ifA"], "ge100-0/0/1", "LLDP ifA correlated")
        _assert_eq(row["lldp"]["ifB"], "ge100-0/0/2", "LLDP ifB correlated")
        _assert_eq(row["correlation"]["kind"], "physical", "LLDP physical kind classified")
        _assert_eq(row["correlation"]["candidates"][0]["source"], "sideA", "LLDP ranked first")
        _assert_eq(row["side_a"]["physical"][0]["name"], "ge100-0/0/1", "side A physical returned")
    finally:
        routes_mod._fetch_device = old_fetch


def test_refresh_classifies_config_kinds():
    request = SimpleNamespace(state=SimpleNamespace(user="dn", role="engineer"))

    cases = [
        (
            "bundle",
            DeviceTelemetry(bundles=[BundleRow(name="bundle-10")], subifs=[]),
            DeviceTelemetry(bundles=[BundleRow(name="bundle-20")], subifs=[]),
            {"hintIfA": "bundle-10", "hintIfB": "bundle-20"},
        ),
        (
            "sub-bundle",
            DeviceTelemetry(subifs=[SubInterfaceRow(name="bundle-10.100", parent="bundle-10", outer_vlan="100", ip="10.0.0.0/31")]),
            DeviceTelemetry(subifs=[SubInterfaceRow(name="bundle-20.100", parent="bundle-20", outer_vlan="100", ip="10.0.0.1/31")]),
            {},
        ),
        (
            "sub-interface",
            DeviceTelemetry(subifs=[SubInterfaceRow(name="ge100-0/0/1.200", parent="ge100-0/0/1", outer_vlan="200", ip="10.0.1.0/31")]),
            DeviceTelemetry(subifs=[SubInterfaceRow(name="ge100-0/0/2.200", parent="ge100-0/0/2", outer_vlan="200", ip="10.0.1.1/31")]),
            {},
        ),
        (
            "none",
            DeviceTelemetry(physical=[InterfaceRow(name="ge100-0/0/1")]),
            DeviceTelemetry(physical=[InterfaceRow(name="ge100-0/0/2")]),
            {},
        ),
    ]

    for expected, side_a, side_b, hints in cases:
        def fake_fetch(device, app_user, force=False):
            return side_a if device.device_id == "PE-1" else side_b

        old_fetch = routes_mod._fetch_device
        routes_mod._fetch_device = fake_fetch
        try:
            body = {
                "links": [{
                    "linkId": f"l-{expected}",
                    "deviceA": {"device_id": "PE-1"},
                    "deviceB": {"device_id": "PE-2"},
                    **hints,
                }]
            }
            result = routes_mod.refresh_link_telemetry(body, request)
            _assert_eq(result["results"][0]["correlation"]["kind"], expected, f"{expected} kind classified")
        finally:
            routes_mod._fetch_device = old_fetch


def test_refresh_ranks_protocol_operational_match():
    request = SimpleNamespace(state=SimpleNamespace(user="dn", role="engineer"))
    side_a = DeviceTelemetry(subifs=[
        SubInterfaceRow(
            name="ge100-0/0/1.301",
            parent="ge100-0/0/1",
            protocols=ProtocolInfo(isis="Up", ospf="Full"),
        ),
        SubInterfaceRow(name="ge100-0/0/1.999", parent="ge100-0/0/1", outer_vlan="999"),
    ])
    side_b = DeviceTelemetry(subifs=[
        SubInterfaceRow(
            name="ge100-0/0/2.301",
            parent="ge100-0/0/2",
            protocols=ProtocolInfo(isis="Up", ospf="Full"),
        ),
        SubInterfaceRow(name="ge100-0/0/2.999", parent="ge100-0/0/2", outer_vlan="999"),
    ])

    def fake_fetch(device, app_user, force=False):
        return side_a if device.device_id == "PE-1" else side_b

    old_fetch = routes_mod._fetch_device
    routes_mod._fetch_device = fake_fetch
    try:
        body = {"links": [{"linkId": "l-proto", "deviceA": {"device_id": "PE-1"}, "deviceB": {"device_id": "PE-2"}}]}
        result = routes_mod.refresh_link_telemetry(body, request)
        corr = result["results"][0]["correlation"]
        _assert_eq(corr["subA"], "ge100-0/0/1.301", "protocol match selected side A")
        _assert_eq(corr["subB"], "ge100-0/0/2.301", "protocol match selected side B")
        _assert_eq("ISIS" in corr["evidence"], True, "protocol evidence included")
    finally:
        routes_mod._fetch_device = old_fetch


def test_lldp_lacp_member_promotes_to_bundle():
    request = SimpleNamespace(state=SimpleNamespace(user="dn", role="engineer"))
    side_a = DeviceTelemetry(
        physical=[InterfaceRow(name="ge100-0/0/1", admin_state="enabled", oper_state="up")],
        bundles=[BundleRow(
            name="bundle-100",
            admin_state="enabled",
            oper_state="up",
            members=[BundleMemberRow(interface="ge100-0/0/1", role="active", port_state="up", protocol_state="collecting")]
        )],
        lldp=[LldpEdge(device="PE-1", local_interface="ge100-0/0/1", peer_hostname="PE-2", peer_interface="ge100-0/0/2")],
    )
    side_b = DeviceTelemetry(
        physical=[InterfaceRow(name="ge100-0/0/2", admin_state="enabled", oper_state="up")],
        bundles=[BundleRow(
            name="bundle-200",
            admin_state="enabled",
            oper_state="up",
            members=[BundleMemberRow(interface="ge100-0/0/2", role="active", port_state="up", protocol_state="collecting")]
        )],
    )

    def fake_fetch(device, app_user, force=False):
        return side_a if device.device_id == "PE-1" else side_b

    old_fetch = routes_mod._fetch_device
    routes_mod._fetch_device = fake_fetch
    try:
        body = {"links": [{"linkId": "l-lag", "deviceA": {"device_id": "PE-1"}, "deviceB": {"device_id": "PE-2"}}]}
        corr = routes_mod.refresh_link_telemetry(body, request)["results"][0]["correlation"]
        _assert_eq(corr["kind"], "bundle", "LLDP LACP member promoted to bundle kind")
        _assert_eq(corr["ifA"], "bundle-100", "Side A promoted to bundle")
        _assert_eq(corr["ifB"], "bundle-200", "Side B promoted to bundle")
        _assert_eq(corr["memberA"], "ge100-0/0/1", "Side A member evidence preserved")
        _assert_eq(corr["memberB"], "ge100-0/0/2", "Side B member evidence preserved")
        _assert_eq(corr["correlationStatus"], "verified-up", "bundle state reported verified up")
    finally:
        routes_mod._fetch_device = old_fetch


def test_lldp_lacp_member_promotes_to_subbundle():
    request = SimpleNamespace(state=SimpleNamespace(user="dn", role="engineer"))
    side_a = DeviceTelemetry(
        physical=[InterfaceRow(name="ge100-0/0/1", admin_state="enabled", oper_state="up")],
        bundles=[BundleRow(name="bundle-100", members_config=[BundleMemberRow(interface="ge100-0/0/1")])],
        subifs=[SubInterfaceRow(name="bundle-100.2001", parent="bundle-100", outer_vlan="2001", ip="10.0.0.0/31", admin_state="enabled", oper_state="up")],
        lldp=[LldpEdge(device="PE-1", local_interface="ge100-0/0/1", peer_hostname="PE-2", peer_interface="ge100-0/0/2")],
    )
    side_b = DeviceTelemetry(
        physical=[InterfaceRow(name="ge100-0/0/2", admin_state="enabled", oper_state="up")],
        bundles=[BundleRow(name="bundle-200", members_config=[BundleMemberRow(interface="ge100-0/0/2")])],
        subifs=[SubInterfaceRow(name="bundle-200.2001", parent="bundle-200", outer_vlan="2001", ip="10.0.0.1/31", admin_state="enabled", oper_state="up")],
    )

    def fake_fetch(device, app_user, force=False):
        return side_a if device.device_id == "PE-1" else side_b

    old_fetch = routes_mod._fetch_device
    routes_mod._fetch_device = fake_fetch
    try:
        body = {"links": [{"linkId": "l-sub-lag", "deviceA": {"device_id": "PE-1"}, "deviceB": {"device_id": "PE-2"}}]}
        corr = routes_mod.refresh_link_telemetry(body, request)["results"][0]["correlation"]
        _assert_eq(corr["kind"], "sub-bundle", "service VLAN promotes bundle to sub-bundle")
        _assert_eq(corr["logicalIfA"], "bundle-100.2001", "Side A logical label is sub-bundle")
        _assert_eq(corr["logicalIfB"], "bundle-200.2001", "Side B logical label is sub-bundle")
    finally:
        routes_mod._fetch_device = old_fetch


def test_lldp_lacp_subbundle_prefers_matching_logical_unit_over_first_vlan_tie():
    request = SimpleNamespace(state=SimpleNamespace(user="dn", role="engineer"))
    side_a = DeviceTelemetry(
        physical=[InterfaceRow(name="ge100-0/0/6", admin_state="enabled", oper_state="up")],
        bundles=[BundleRow(name="bundle-100", members=[BundleMemberRow(interface="ge100-0/0/6")])],
        subifs=[
            SubInterfaceRow(name="bundle-100.210", parent="bundle-100", outer_vlan="12", admin_state="enabled", oper_state="up"),
            SubInterfaceRow(name="bundle-100.215", parent="bundle-100", outer_vlan="4", admin_state="enabled", oper_state="up"),
        ],
        lldp=[LldpEdge(device="DNAAS", local_interface="ge100-0/0/6", peer_hostname="RR-SA-2", peer_interface="ge400-0/0/0")],
    )
    side_b = DeviceTelemetry(
        physical=[InterfaceRow(name="ge400-0/0/0", admin_state="enabled", oper_state="up")],
        bundles=[BundleRow(name="bundle-100", members=[BundleMemberRow(interface="ge400-0/0/0")])],
        subifs=[
            SubInterfaceRow(name="bundle-100.12", parent="bundle-100", outer_vlan="12", admin_state="enabled", oper_state="up"),
            SubInterfaceRow(name="bundle-100.215", parent="bundle-100", outer_vlan="4", admin_state="enabled", oper_state="up"),
        ],
    )

    def fake_fetch(device, app_user, force=False):
        return side_a if device.device_id == "DNAAS" else side_b

    old_fetch = routes_mod._fetch_device
    routes_mod._fetch_device = fake_fetch
    try:
        body = {"links": [{"linkId": "l-sub-lag-tie", "deviceA": {"device_id": "DNAAS"}, "deviceB": {"device_id": "RR-SA-2"}}]}
        corr = routes_mod.refresh_link_telemetry(body, request)["results"][0]["correlation"]
        _assert_eq(corr["subA"], "bundle-100.215", "matching Side A logical unit wins VLAN tie")
        _assert_eq(corr["subB"], "bundle-100.215", "matching Side B logical unit wins VLAN tie")
    finally:
        routes_mod._fetch_device = old_fetch


def test_lldp_physical_pair_promotes_to_vlan_subinterfaces():
    request = SimpleNamespace(state=SimpleNamespace(user="dn", role="engineer"))
    side_a = DeviceTelemetry(
        physical=[InterfaceRow(name="ge100-0/0/3", admin_state="enabled", oper_state="up")],
        subifs=[SubInterfaceRow(name="ge100-0/0/3.210", parent="ge100-0/0/3", outer_vlan="210", admin_state="enabled", oper_state="up")],
        lldp=[LldpEdge(device="DNAAS", local_interface="ge100-0/0/3", peer_hostname="PE-4", peer_interface="ge100-18/0/0")],
    )
    side_b = DeviceTelemetry(
        physical=[InterfaceRow(name="ge100-18/0/0", admin_state="enabled", oper_state="up")],
        subifs=[SubInterfaceRow(name="ge100-18/0/0.210", parent="ge100-18/0/0", outer_vlan="210", admin_state="enabled", oper_state="up")],
    )

    def fake_fetch(device, app_user, force=False):
        return side_a if device.device_id == "DNAAS" else side_b

    old_fetch = routes_mod._fetch_device
    routes_mod._fetch_device = fake_fetch
    try:
        body = {"links": [{"linkId": "l-subif", "deviceA": {"device_id": "DNAAS"}, "deviceB": {"device_id": "PE-4"}}]}
        corr = routes_mod.refresh_link_telemetry(body, request)["results"][0]["correlation"]
        _assert_eq(corr["kind"], "sub-interface", "LLDP physical pair promoted to sub-interface")
        _assert_eq(corr["subA"], "ge100-0/0/3.210", "Side A VLAN sub-interface selected")
        _assert_eq(corr["subB"], "ge100-18/0/0.210", "Side B VLAN sub-interface selected")
        _assert_eq(corr["outerVlanA"], "210", "Side A outer VLAN preserved")
        _assert_eq(corr["outerVlanB"], "210", "Side B outer VLAN preserved")
    finally:
        routes_mod._fetch_device = old_fetch


def test_lldp_physical_pair_infers_missing_peer_vlan_subinterface():
    request = SimpleNamespace(state=SimpleNamespace(user="dn", role="engineer"))
    side_a = DeviceTelemetry(
        physical=[InterfaceRow(name="ge100-0/0/3", admin_state="enabled", oper_state="up")],
        subifs=[SubInterfaceRow(name="ge100-0/0/3.210.310", parent="ge100-0/0/3", outer_vlan="210", inner_vlan="310", admin_state="enabled", oper_state="up")],
        lldp=[LldpEdge(device="DNAAS", local_interface="ge100-0/0/3", peer_hostname="PE-4", peer_interface="ge100-18/0/0")],
    )
    side_b = DeviceTelemetry(
        physical=[InterfaceRow(name="ge100-18/0/0", admin_state="enabled", oper_state="up")],
    )

    def fake_fetch(device, app_user, force=False):
        return side_a if device.device_id == "DNAAS" else side_b

    old_fetch = routes_mod._fetch_device
    routes_mod._fetch_device = fake_fetch
    try:
        body = {"links": [{"linkId": "l-inferred-subif", "deviceA": {"device_id": "DNAAS"}, "deviceB": {"device_id": "PE-4"}}]}
        corr = routes_mod.refresh_link_telemetry(body, request)["results"][0]["correlation"]
        _assert_eq(corr["kind"], "sub-interface", "one-sided VLAN still promotes logical kind")
        _assert_eq(corr["subA"], "ge100-0/0/3.210.310", "existing side sub-interface selected")
        _assert_eq(corr["subB"], "ge100-18/0/0.210.310", "missing peer sub-interface inferred")
        _assert_eq(corr["outerVlanB"], "210", "inferred peer outer VLAN preserved")
        _assert_eq(corr["innerVlanB"], "310", "inferred peer inner VLAN preserved")
    finally:
        routes_mod._fetch_device = old_fetch


def test_service_attachment_alone_does_not_match_different_vlan_rows():
    request = SimpleNamespace(state=SimpleNamespace(user="dn", role="engineer"))
    side_a = DeviceTelemetry(subifs=[
        SubInterfaceRow(
            name="bundle-1.131",
            parent="bundle-1",
            outer_vlan="131",
            attachment=AttachmentInfo(kind="bridge-domain", service_name="g_site_a_v131"),
            admin_state="enabled",
            oper_state="down",
        )
    ])
    side_b = DeviceTelemetry(subifs=[
        SubInterfaceRow(
            name="bundle-100.23",
            parent="bundle-100",
            outer_vlan="23",
            attachment=AttachmentInfo(kind="plain-l3", service_name="bundle-100.23"),
            admin_state="enabled",
            oper_state="up",
        )
    ])

    def fake_fetch(device, app_user, force=False):
        return side_a if device.device_id == "DNAAS" else side_b

    old_fetch = routes_mod._fetch_device
    routes_mod._fetch_device = fake_fetch
    try:
        body = {"links": [{"linkId": "l-service-only", "deviceA": {"device_id": "DNAAS"}, "deviceB": {"device_id": "RR-SA-2"}}]}
        corr = routes_mod.refresh_link_telemetry(body, request)["results"][0]["correlation"]
        _assert_eq(corr["kind"], "none", "different VLAN service-only rows are not treated as a match")
    finally:
        routes_mod._fetch_device = old_fetch


def test_down_expected_link_still_correlates_from_cached_lldp_and_config():
    request = SimpleNamespace(state=SimpleNamespace(user="dn", role="engineer"))
    side_a = DeviceTelemetry(
        physical=[InterfaceRow(name="ge100-0/0/1", admin_state="enabled", oper_state="down")],
        bundles=[BundleRow(
            name="bundle-100",
            admin_state="enabled",
            oper_state="down",
            members_config=[BundleMemberRow(interface="ge100-0/0/1")]
        )],
    )
    side_b = DeviceTelemetry(
        physical=[InterfaceRow(name="ge100-0/0/2", admin_state="enabled", oper_state="down")],
        bundles=[BundleRow(
            name="bundle-200",
            admin_state="enabled",
            oper_state="down",
            members_config=[BundleMemberRow(interface="ge100-0/0/2")]
        )],
    )

    def fake_fetch(device, app_user, force=False):
        return side_a if device.device_id == "PE-1" else side_b

    old_fetch = routes_mod._fetch_device
    routes_mod._fetch_device = fake_fetch
    try:
        body = {"links": [{
            "linkId": "l-down-lag",
            "deviceA": {"device_id": "PE-1"},
            "deviceB": {"device_id": "PE-2"},
            "previousCorrelation": {"memberA": "ge100-0/0/1", "memberB": "ge100-0/0/2", "source": "sideA"}
        }]}
        corr = routes_mod.refresh_link_telemetry(body, request)["results"][0]["correlation"]
        _assert_eq(corr["kind"], "bundle", "down expected link still resolves to bundle")
        _assert_eq(corr["correlationStatus"], "expected-down", "down state is reported as expected-down")
        _assert_eq(corr["ifA"], "bundle-100", "down side A promoted to configured bundle")
        _assert_eq(corr["ifB"], "bundle-200", "down side B promoted to configured bundle")
    finally:
        routes_mod._fetch_device = old_fetch


if __name__ == "__main__":
    test_refresh_correlates_lldp()
    test_refresh_classifies_config_kinds()
    test_refresh_ranks_protocol_operational_match()
    test_lldp_lacp_member_promotes_to_bundle()
    test_lldp_lacp_member_promotes_to_subbundle()
    test_lldp_lacp_subbundle_prefers_matching_logical_unit_over_first_vlan_tie()
    test_lldp_physical_pair_promotes_to_vlan_subinterfaces()
    test_lldp_physical_pair_infers_missing_peer_vlan_subinterface()
    test_service_attachment_alone_does_not_match_different_vlan_rows()
    test_down_expected_link_still_correlates_from_cached_lldp_and_config()
    print("All link telemetry route tests passed")
