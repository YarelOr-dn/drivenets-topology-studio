#!/usr/bin/env python3
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lease
import onboard


def test_classify():
    assert onboard.classify_bd_type("g_mgmt_v999") == ("global", 999)
    assert onboard.classify_bd_type("g_foo_v2100") == ("global", 2100)
    assert onboard.classify_bd_type("l_bar_v10")[0] == "local"


def test_range():
    assert onboard.vlan_in_range(2100, "2100-2199")
    assert not onboard.vlan_in_range(999, "2100-2199")
    plan = onboard.onboard_plan({"vlan": 999, "vlan_range": "2100-2199"})
    assert plan["verdict"] == "VLAN_OUT_OF_RANGE"


def test_no_silent_999():
    plan = onboard.onboard_plan({
        "vlan": 2100,
        "bd_name": "g_mgmt_v999",
        "bd_show_text": "instance g_foo_v2100\n",
    })
    assert plan["verdict"] == "FORBIDDEN_FALLBACK"


def test_match_and_plan():
    show = "instance g_user_v2100\n"
    plan = onboard.onboard_plan({
        "vlan": 2100,
        "vlan_range": "2100-2199",
        "bd_show_text": show,
        "dnaas_leaf": "DNAAS-LEAF-X",
        "bundle": "bundle-100",
        "device": "PE-X",
        "dut_ip": "10.1.1.10",
        "gateway": "10.1.1.1",
        "subnet": "24",
    })
    assert plan["ok"] and plan["bd_name"] == "g_user_v2100"
    assert plan["subif"] == "bundle-100.2100"
    assert "g_mgmt_v999" not in json.dumps(plan)
    assert plan.get("execute") is False


def test_lease(tmp_path=None):
    orig = lease.LEASE_FILE
    d = Path(tempfile.mkdtemp())
    lease.LEASE_FILE = d / "active.json"
    lease.LEASES_DIR = d
    try:
        a = lease.acquire("alice", dut="PE-1")
        assert a["ok"]
        b = lease.acquire("bob", dut="PE-2")
        assert not b["ok"] and b["verdict"] == "DEVICE_BUSY"
        g = lease.require_owner("bob")
        assert g and g["verdict"] == "DEVICE_BUSY"
        assert lease.require_owner("alice") is None
        r = lease.release("alice")
        assert r["ok"]
        c = lease.acquire("bob")
        assert c["ok"]
    finally:
        lease.LEASE_FILE = orig


if __name__ == "__main__":
    test_classify()
    test_range()
    test_no_silent_999()
    test_match_and_plan()
    test_lease()
    print("[OK] onboard+lease unit tests")
