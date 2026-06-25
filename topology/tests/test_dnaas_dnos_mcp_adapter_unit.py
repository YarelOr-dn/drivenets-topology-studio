"""Regression checks for the dnos-config MCP DNAAS discovery adapter.

Run:
    PYTHONPATH="topology" python3 topology/tests/test_dnaas_dnos_mcp_adapter_unit.py
"""
from __future__ import annotations

import os
import re
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOPO = os.path.join(REPO_ROOT, "topology")
sys.path.insert(0, TOPO)


def _read(rel: str) -> str:
    with open(os.path.join(TOPO, rel), "r", encoding="utf-8") as f:
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


def _sample_walk_payload() -> dict:
    return {
        "ok": True,
        "dut": "YOR_CL_PE-4",
        "spirent_ingress_leaf": "DNAAS-LEAF-B14",
        "device_index_meta": {
            "DNAAS-LEAF-B10": {"device_ip": "100.64.101.3"},
            "DNAAS-SPINE-B09": {"device_ip": "100.64.100.12"},
            "DNAAS-LEAF-B14": {"device_ip": "100.64.101.5"},
        },
        "dut_acs": [
            {
                "dut_interface": "ge100-18/0/1",
                "lldp_to_dnaas": {
                    "neighbor_device": "DNAAS-LEAF-B10",
                    "neighbor_port": "ge100-0/0/4",
                },
                "dnaas_ac": {
                    "device": "DNAAS-LEAF-B10",
                    "interface": "ge100-0/0/4",
                    "bd_name": "g_yor_v211_STC-TO-CL_port-mode",
                },
                "bd_chain_id": "DNAAS-LEAF-B10::g_yor_v211_STC-TO-CL_port-mode",
                "verdict": "REACHABLE_TO_SPIRENT",
            }
        ],
        "bd_chains": {
            "DNAAS-LEAF-B10::g_yor_v211_STC-TO-CL_port-mode": {
                "starting_leaf": "DNAAS-LEAF-B10",
                "bd_name": "g_yor_v211_STC-TO-CL_port-mode",
                "reaches_spirent_ingress": True,
                "terminus": "DNAAS-LEAF-B14",
                "hops": [
                    {
                        "device": "DNAAS-LEAF-B10",
                        "bd_name": "g_yor_v211_STC-TO-CL_port-mode",
                        "uplink_ac": "bundle-60000.211",
                        "wire_encap_out": {"outer": 211, "inner": None},
                        "lldp_to_next": {
                            "neighbor_device": "DNAAS-SPINE-B09",
                            "neighbor_port": "ge100-0/0/0",
                        },
                    },
                    {
                        "device": "DNAAS-SPINE-B09",
                        "bd_name": "g_yor_v211_STC-TO-CL",
                        "uplink_ac": "bundle-60003.211",
                        "wire_encap_out": {"outer": 211, "inner": None},
                        "lldp_to_next": {
                            "neighbor_device": "DNAAS-LEAF-B14",
                            "neighbor_port": "ge100-0/0/36",
                        },
                    },
                ],
            }
        },
        "summary": {"total_dut_acs": 1, "reachable": 1},
        "cache": {"source": "cold"},
    }


def test_adapter_preserves_topology_contract() -> None:
    _case("dnos-config walk converts to DNAAS canvas topology")
    import discovery_api

    topology = discovery_api._dnos_mcp_walk_to_topology(_sample_walk_payload(), "PE-4")
    _assert(topology["version"] == "1.0", "topology version is present")
    _assert(topology["objects"], "topology contains canvas objects")
    _assert(topology["metadata"]["source_backend"] == "dnos-config-mcp", "backend source is tagged")
    _assert(
        topology["metadata"]["bridge_domains"],
        "bridge-domain metadata is populated for the BD legend",
    )
    _assert(
        "YOR_CL_PE-4" in topology["metadata"]["device_bd_mapping"],
        "DUT appears in device-to-BD mapping",
    )
    links = [o for o in topology["objects"] if o.get("type") == "link"]
    _assert(any(l["linkDetails"].get("source") == "dnos-config-mcp" for l in links), "links are source-tagged")
    _assert(any(l["linkDetails"].get("vlan_id") == 211 for l in links), "forwarding VLAN is preserved")
    _assert(any(o.get("label") == "Spirent 6/13" for o in topology["objects"]), "Spirent endpoint is rendered")


def test_backend_uses_mcp_cli_boundary() -> None:
    _case("backend does not bypass dnos-config MCP")
    src = _read("discovery_api.py")
    _assert("~/.cursor/tools/dnos_mcp.py" in src, "documented MCP CLI fallback is used")
    _assert("dnos_dnaas_walk_from_dut" in src, "dnos DNAAS walker is the adapter input")
    _assert("from dnos_config_mcp" not in src, "no direct dnos_config_mcp import")
    _assert("handle_tool_call" not in src, "no in-process dnos-config tool bypass")
    _assert(
        re.search(r"requested_backend\s*=.*legacy", src, re.S) is not None,
        "legacy backend remains available as an explicit fallback",
    )


if __name__ == "__main__":
    test_adapter_preserves_topology_contract()
    test_backend_uses_mcp_cli_boundary()
    print("\nAll dnos-config MCP adapter checks passed")
