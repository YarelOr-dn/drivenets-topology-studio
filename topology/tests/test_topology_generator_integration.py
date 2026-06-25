"""Integration tests for the AI Topology Generator backend route.

These tests exercise the FULL request path of the core endpoints the
Generate Topology panel relies on, with the underlying helpers
(``_resolve_mgmt_ip``, ``_resolve_device``, ``_get_device_context``,
``_build_scaler_ops_index``, ``DeviceCommHelper.fetch_running_config``)
monkey-patched so we never touch the network. The purpose is to close
the "I never ran the real flow end-to-end" gap from the unit tests:

    1. POST /api/topology-generator/resolve-targets
       - Manual hostnames + raw IPs are parsed.
       - Inventory hostnames + serials come back from the resolver.
       - watch_ids dedupe across uppercase / lowercase aliases so the
         frontend's TopologyDeviceEvents.setWatchedDevices(...) call
         registers ONE watcher per DUT.
       - Per-user `domain_id` / `topology_id` are echoed back so the
         caller can confirm the multi-user scope was honored.

    2. GET /api/topology-generator/device-facts?fetch_config=1
       - Returns layered context (hostname/system_type/role/AS/router-id).
       - Returns a normalized LLDP neighbor list (the physical-source
         the frontend's adapterLive() consumes for the DUT-LLDP layer).
       - Returns rich logical config facts merged from
         ``_config_facts_from_summary`` + ``_config_facts_from_running``
         (vrfs, bridge_domains, bgp_peers, mpls flags, route
         distinguishers) -- exactly what the Live Devices tab promises.

    3. POST /api/topology-generator/collect-batch
       - Threads ``domain_id`` / ``topology_id`` to each per-device call.
       - One bad device does NOT poison the batch.
       - Each entry surfaces the same layered context + LLDP + config
         facts shape as the single-device endpoint.

    4. POST /api/topology-generator/correlate
       - Per-user temp SQLite correlates BGP peer IPs to indexed addresses,
         shared VRF/BD/RT memberships, and deletes the DB file afterward.

Run:

    PYTHONPATH="topology" python3 topology/tests/test_topology_generator_integration.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List


REPO = Path("/home/dn/drivenets-topology-studio")
sys.path.insert(0, str(REPO / "topology"))

os.environ.setdefault("TP_AUTH_ENFORCE", "never")


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


def _assert_true(cond: bool, label: str) -> None:
    if cond:
        print(f"  ok: {label}")
        return
    print(f"  FAIL: {label}")
    raise SystemExit(1)


# ---------------------------------------------------------------------------
# Fixture: a tiny 3-device topology shaped like a real Live Devices flow.
#
#   PE-1 (10.0.0.1) <--ge100-0/0/1 -- ge100-0/0/2--> PE-2 (10.0.0.2)
#   PE-1 (10.0.0.1) <--ge100-0/0/3 -- ge100-0/0/3--> CE-A (10.0.0.9, external)
#
#   PE-1 carries VRF RED + bridge-domain BD-100 + iBGP to PE-2 + eBGP to CE-A.
# ---------------------------------------------------------------------------
_FIXTURE_DEVICES: Dict[str, Dict[str, Any]] = {
    "PE-1": {
        "mgmt_ip": "10.0.0.1",
        "serial": "SN-PE1",
        "system_type": "sa-router",
        "dnos_version": "19.2.1",
        "as_number": "65000",
        "router_id": "10.255.0.1",
        "loopback0_ip": "10.255.0.1",
        "lldp": [
            {
                "local_interface": "ge100-0/0/1",
                "peer_hostname": "PE-2",
                "peer_interface": "ge100-0/0/2",
                "peer_chassis_id": "AA:BB:CC:00:00:02",
            },
            {
                "local_port": "ge100-0/0/3",
                "neighbor": "CE-A",
                "peer_port": "ge100-0/0/3",
            },
        ],
        "running_config": "\n".join([
            "system name PE-1",
            "vrf RED",
            "vrf BLUE",
            "interfaces ge100-0/0/1",
            "  ipv4 address 10.0.0.1/30",
            "interfaces ge100-0/0/3",
            "  ipv4 address 10.0.9.1/30",
            "interfaces bundle-1",
            "  ipv4 address 10.0.2.1/30",
            "bridge-domain BD-100",
            "neighbors 10.0.0.2",
            "  remote-as 65000",
            "neighbors 10.0.9.2",
            "  remote-as 65100",
            "route-distinguisher 65000:100",
            "router ospf 1",
            "  area 0",
            "mpls",
            "ldp",
            "segment-routing",
        ]),
    },
    "PE-2": {
        "mgmt_ip": "10.0.0.2",
        "serial": "SN-PE2",
        "system_type": "sa-router",
        "dnos_version": "19.2.1",
        "as_number": "65000",
        "router_id": "10.255.0.2",
        "loopback0_ip": "10.255.0.2",
        "lldp": [
            {
                "local_interface": "ge100-0/0/2",
                "peer_hostname": "PE-1",
                "peer_interface": "ge100-0/0/1",
                "peer_chassis_id": "AA:BB:CC:00:00:01",
            },
        ],
        "running_config": "\n".join([
            "system name PE-2",
            "vrf RED",
            "interfaces ge100-0/0/2",
            "  ipv4 address 10.0.0.2/30",
            "neighbors 10.0.0.1",
            "  remote-as 65000",
            "route-distinguisher 65000:200",
            "mpls",
        ]),
    },
}


# ---------------------------------------------------------------------------
# Monkey-patch the helpers BEFORE we import the router. The module imports
# them by name in `from routes.bridge_helpers import ...`, so we have to
# patch the names rebound on the route module after import. We do that
# below in `_install_patches`.
# ---------------------------------------------------------------------------
def _install_patches(generator_module) -> None:
    """Replace network-touching helpers on the route module."""

    def _fake_resolve_mgmt_ip(device_id: str, ssh_host: str = ""):
        device_id = (device_id or "").strip()
        ssh_host = (ssh_host or "").strip()
        # exact hostname match first
        if device_id in _FIXTURE_DEVICES:
            return _FIXTURE_DEVICES[device_id]["mgmt_ip"], device_id, "inventory"
        # raw IP match
        for name, dev in _FIXTURE_DEVICES.items():
            if dev["mgmt_ip"] in (device_id, ssh_host):
                return dev["mgmt_ip"], name, "inventory_by_ip"
        # unknown -> echo back what we got
        return ssh_host or device_id or "", "", "unresolved"

    def _fake_resolve_device(device_id: str):
        device_id = (device_id or "").strip()
        if device_id in _FIXTURE_DEVICES:
            return {
                "hostname": device_id,
                "name": device_id,
                "serial": _FIXTURE_DEVICES[device_id]["serial"],
            }
        for name, dev in _FIXTURE_DEVICES.items():
            if dev["mgmt_ip"] == device_id:
                return {"hostname": name, "name": name, "serial": dev["serial"]}
        return None

    def _fake_build_scaler_ops_index():
        idx: Dict[str, Dict[str, Any]] = {}
        for name, dev in _FIXTURE_DEVICES.items():
            entry = {"hostname": name, "scaler_id": dev["serial"]}
            idx[name.lower()] = entry
            idx[dev["mgmt_ip"]] = entry
            idx[dev["serial"].lower()] = entry
        return idx

    def _fake_get_device_context(device_id, live=False, ssh_host="", app_user="",
                                  domain_id="", topology_id=""):
        device_id = (device_id or "").strip()
        host = (ssh_host or "").strip()
        # capture for later assertions
        _fake_get_device_context.last_call = {
            "device_id": device_id,
            "live": bool(live),
            "ssh_host": host,
            "app_user": app_user,
            "domain_id": domain_id,
            "topology_id": topology_id,
        }
        dev = None
        if device_id in _FIXTURE_DEVICES:
            dev = _FIXTURE_DEVICES[device_id]
            hostname = device_id
        else:
            for name, candidate in _FIXTURE_DEVICES.items():
                if candidate["mgmt_ip"] in (device_id, host):
                    dev = candidate
                    hostname = name
                    break
        if dev is None:
            return {
                "identity": {"hostname": device_id or host},
                "hostname": device_id or host,
                "system_type": "",
                "dnos_version": "",
                "mgmt_ip": host,
                "lldp": [],
            }
        return {
            "identity": {
                "hostname": hostname,
                "system_type": dev["system_type"],
                "dnos_version": dev["dnos_version"],
                "mgmt_ip": dev["mgmt_ip"],
            },
            "hostname": hostname,
            "system_type": dev["system_type"],
            "dnos_version": dev["dnos_version"],
            "mgmt_ip": dev["mgmt_ip"],
            "as_number": dev["as_number"],
            "router_id": dev["router_id"],
            "loopback0_ip": dev["loopback0_ip"],
            "lldp": list(dev["lldp"]),
        }
    _fake_get_device_context.last_call = None

    class _FakeDeviceCommHelper:
        def fetch_running_config(self, device_id, ssh_host="", app_user=""):
            device_id = (device_id or "").strip()
            host = (ssh_host or "").strip()
            if device_id in _FIXTURE_DEVICES:
                return _FIXTURE_DEVICES[device_id]["running_config"]
            for name, dev in _FIXTURE_DEVICES.items():
                if dev["mgmt_ip"] in (device_id, host):
                    return dev["running_config"]
            return ""

    generator_module._resolve_mgmt_ip = _fake_resolve_mgmt_ip
    generator_module._resolve_device = _fake_resolve_device
    generator_module._build_scaler_ops_index = _fake_build_scaler_ops_index
    generator_module._get_device_context = _fake_get_device_context
    generator_module.DeviceCommHelper = _FakeDeviceCommHelper

    # Expose hooks for assertions.
    generator_module._test_get_device_context_call = (
        lambda: _fake_get_device_context.last_call
    )


def main() -> None:
    import fastapi
    from fastapi.testclient import TestClient

    from routes import topology_generator as gen

    _install_patches(gen)

    app = fastapi.FastAPI()
    app.include_router(gen.router)
    client = TestClient(app)

    # ---------------------------------------------------------------
    _case("POST /resolve-targets normalizes manual + IP entries")
    body = {
        "targets": [
            {"deviceId": "PE-1", "label": "PE-1"},
            {"deviceId": "10.0.0.2", "label": "PE-2 (by IP)"},
            # duplicate of the same DUT under a different alias --
            # watch_ids should dedupe so the frontend doesn't double-watch.
            {"deviceId": "pe-1"},
            # unknown raw IP -> still returned but flagged as unresolved.
            {"deviceId": "10.255.255.99"},
        ],
        "credentials": {"user": "dnroot", "password": "dnroot"},
        "domain_id": "dom-A",
        "topology_id": "topo-99",
    }
    r = client.post("/api/topology-generator/resolve-targets", json=body)
    _assert_eq(r.status_code, 200, "resolve-targets http status")
    data = r.json()
    resolved = data.get("resolved") or []
    _assert_eq(len(resolved), 4, "all four targets are returned")
    by_label = {row["deviceId"]: row for row in resolved}

    _assert_eq(by_label["PE-1"]["hostname"], "PE-1", "PE-1 hostname")
    _assert_eq(by_label["PE-1"]["mgmt_ip"], "10.0.0.1", "PE-1 mgmt_ip")
    _assert_eq(by_label["PE-1"]["serial"], "SN-PE1", "PE-1 serial from inventory")
    _assert_eq(by_label["PE-1"]["role"], "pe", "PE-1 role classified")
    _assert_eq(by_label["PE-1"]["dnos_version"], "19.2.1", "PE-1 dnos_version")
    _assert_eq(by_label["PE-1"]["ssh_user"], "dnroot", "PE-1 ssh user defaulted")

    _assert_eq(by_label["10.0.0.2"]["hostname"], "PE-2",
               "raw IP -> hostname rewritten via inventory")
    _assert_eq(by_label["10.0.0.2"]["mgmt_ip"], "10.0.0.2", "PE-2 mgmt_ip echoed")

    _assert_true(by_label["pe-1"].get("duplicate") is True,
                 "lowercase alias of PE-1 flagged duplicate")

    unknown = by_label["10.255.255.99"]
    _assert_eq(unknown["mgmt_ip"], "10.255.255.99",
               "unknown IP echoed (no synchronous discover)")
    _assert_eq(unknown["serial"], "", "unknown IP -> empty serial")

    watch_ids = data.get("watch_ids") or []
    _assert_true("PE-1" in watch_ids, "watch_ids contains PE-1")
    _assert_true("PE-2" in watch_ids, "watch_ids contains PE-2")
    _assert_true(
        sum(1 for w in watch_ids if w.lower() == "pe-1") == 1,
        "PE-1 deduplicated in watch_ids",
    )

    _assert_eq(data.get("domain_id"), "dom-A", "domain_id echoed back")
    _assert_eq(data.get("topology_id"), "topo-99", "topology_id echoed back")

    last_ctx_call = gen._test_get_device_context_call()
    _assert_eq(last_ctx_call["domain_id"], "dom-A",
               "_get_device_context received domain_id scope")
    _assert_eq(last_ctx_call["topology_id"], "topo-99",
               "_get_device_context received topology_id scope")

    # ---------------------------------------------------------------
    _case("GET /device-facts returns layered LLDP + logical config facts")
    r = client.get("/api/topology-generator/device-facts", params={
        "device_id": "PE-1",
        "fetch_config": 1,
        "live": 0,
        "domain_id": "dom-A",
        "topology_id": "topo-99",
    })
    _assert_eq(r.status_code, 200, "device-facts http status")
    facts = r.json()
    ctx = facts.get("context") or {}
    _assert_eq(ctx["hostname"], "PE-1", "context hostname")
    _assert_eq(ctx["role"], "pe", "context role")
    _assert_eq(ctx["as_number"], "65000", "context AS number")
    _assert_eq(ctx["router_id"], "10.255.0.1", "context router_id")

    lldp = facts.get("lldp_neighbors") or []
    _assert_eq(len(lldp), 2, "two LLDP rows returned")
    peer_pairs = sorted(
        [(row.get("local_interface"), row.get("peer_hostname"),
          row.get("peer_interface")) for row in lldp]
    )
    _assert_eq(
        peer_pairs,
        [
            ("ge100-0/0/1", "PE-2", "ge100-0/0/2"),
            ("ge100-0/0/3", "CE-A", "ge100-0/0/3"),
        ],
        "LLDP rows normalized across local_interface / local_port aliases",
    )

    cfg = facts.get("config_facts") or {}
    _assert_true(cfg is not None and isinstance(cfg, dict),
                 "config_facts present when fetch_config=1")
    _assert_eq(sorted(cfg.get("vrfs") or []), ["BLUE", "RED"],
               "config_facts vrfs (mgmt/default filtered)")
    _assert_eq(sorted(cfg.get("bridge_domains") or []), ["BD-100"],
               "config_facts bridge domains")
    _assert_eq(cfg.get("bundles") or [], ["bundle-1"],
               "config_facts bundle interfaces")
    _assert_eq(cfg.get("mpls"), {"enabled": True, "ldp": True, "sr": True},
               "config_facts mpls layered flags")
    _assert_eq(sorted(cfg.get("route_distinguishers") or []), ["65000:100"],
               "config_facts RDs")
    peer_summary = sorted([
        (p["peer"], p["remote_as"]) for p in cfg.get("bgp_peers") or []
    ])
    _assert_eq(
        peer_summary,
        [("10.0.0.2", 65000), ("10.0.9.2", 65100)],
        "config_facts bgp peers (iBGP + eBGP)",
    )

    # ---------------------------------------------------------------
    _case("GET /device-facts on unknown device degrades gracefully")
    r = client.get("/api/topology-generator/device-facts", params={
        "device_id": "MISSING-DUT",
        "fetch_config": 0,
    })
    _assert_eq(r.status_code, 200, "unknown device returns 200 (degraded)")
    bad = r.json()
    _assert_eq(bad["device_id"], "MISSING-DUT", "device_id echoed")
    _assert_true(isinstance(bad.get("lldp_neighbors"), list),
                 "lldp_neighbors is a list even for unknown")
    _assert_eq(bad.get("config_facts"), None,
               "config_facts is None when fetch_config=0")

    # ---------------------------------------------------------------
    _case("POST /collect-batch threads scope and survives one bad entry")
    body = {
        "devices": [
            {"device_id": "PE-1"},
            {"device_id": "PE-2"},
            "not-a-dict",  # ignored silently with a warning
            {"device_id": ""},  # warning, no result row
        ],
        "fetch_config": True,
        "live": False,
        "domain_id": "dom-B",
        "topology_id": "topo-42",
    }
    r = client.post("/api/topology-generator/collect-batch", json=body)
    _assert_eq(r.status_code, 200, "collect-batch http status")
    payload = r.json()
    results = payload.get("results") or []
    _assert_eq(len(results), 2, "two valid devices produced result rows")

    by_id = {row["device_id"]: row for row in results}
    _assert_true("PE-1" in by_id and "PE-2" in by_id,
                 "both PE-1 and PE-2 present in batch results")

    pe2_cfg = by_id["PE-2"].get("config_facts") or {}
    _assert_true(isinstance(pe2_cfg, dict) and pe2_cfg,
                 "PE-2 config_facts present in batch")
    _assert_eq(sorted(pe2_cfg.get("vrfs") or []), ["RED"],
               "PE-2 vrfs parsed in batch")
    _assert_eq(pe2_cfg.get("mpls"), {"enabled": True, "ldp": False, "sr": False},
               "PE-2 mpls flags partial (ldp/sr off)")

    pe2_peer_pairs = sorted(
        [(p["peer"], p["remote_as"]) for p in pe2_cfg.get("bgp_peers") or []]
    )
    _assert_eq(pe2_peer_pairs, [("10.0.0.1", 65000)],
               "PE-2 bgp peers parsed (iBGP back to PE-1)")

    last_ctx_call = gen._test_get_device_context_call()
    _assert_eq(last_ctx_call["domain_id"], "dom-B",
               "batch threaded domain_id to per-device context")
    _assert_eq(last_ctx_call["topology_id"], "topo-42",
               "batch threaded topology_id to per-device context")

    warns = payload.get("warnings") or []
    _assert_true(any("missing device_id" in w for w in warns),
                 "empty device_id surfaces a batch warning")

    # ---------------------------------------------------------------
    _case("POST /resolve-targets rejects empty payload with 400")
    r = client.post("/api/topology-generator/resolve-targets", json={"targets": []})
    _assert_eq(r.status_code, 400, "empty targets list -> HTTP 400")

    # ---------------------------------------------------------------
    _case("POST /correlate: temp SQLite, BGP IP match, VRF service, cleanup")
    from pathlib import Path as _Path

    scratch = _Path.home() / ".topology_users" / "default" / "tmp" / "topology_generator"
    before = set(scratch.glob("correlate_*.db")) if scratch.exists() else set()
    facts_body = {
        "domain_id": "dom-C",
        "topology_id": "topo-cor",
        "facts": {
            "devices": [
                {
                    "id": "pe1",
                    "hostname": "PE-1",
                    "role": "pe",
                    "tier": 1,
                    "ssh": {"host": "10.0.0.1"},
                    "config": {
                        "asn": "65000",
                        "router_id": "10.255.0.1",
                        "interfaces": [{"name": "ge100-0/0/1", "ip": "192.0.2.0/31"}],
                        "subinterfaces": [{"name": "ge100-0/0/1.100", "ip": "198.51.100.1/31", "vrf": "RED"}],
                        "bgp_peers": [
                            {"peer": "10.255.0.2", "remote_as": "65000", "local_as": "65000"},
                            {"peer": "4.4.4.4", "remote_as": "65000", "local_as": "65000"},
                        ],
                        "vrfs": ["RED"],
                        "route_targets": ["65000:100"],
                        "isis": {"area": "49.0001", "interfaces": []},
                        "mpls": {"enabled": True, "ldp": True, "sr": False},
                    },
                },
                {
                    "id": "pe2",
                    "hostname": "PE-2",
                    "role": "pe",
                    "tier": 1,
                    "ssh": {"host": "10.0.0.2"},
                    "config": {
                        "asn": "65000",
                        "router_id": "10.255.0.2",
                        "interfaces": [{"name": "ge100-0/0/2", "ip": "192.0.2.1/31"}],
                        "loopback0_ip": "10.255.0.2/32",
                        "vrfs": ["RED"],
                        "route_targets": ["65000:100"],
                        "isis": {"area": "49.0001", "interfaces": []},
                        "mpls": {"enabled": True, "ldp": True, "sr": False},
                    },
                },
                {
                    "id": "pe4",
                    "hostname": "YOR_CL_PE-4",
                    "role": "pe",
                    "tier": 1,
                    "ssh": {"host": "NCC-ACTIVE-1"},
                    "config": {
                        # Simulates preserved PE-4 canvas SSH evidence with
                        # failed auth/config collection. Correlation should
                        # still match PE-1's peer 4.4.4.4 by PE-4 label.
                    },
                },
                {
                    "id": "dna",
                    "hostname": "DNAAS-leaf-9",
                    "role": "leaf",
                    "tier": 1,
                    "ssh": {"host": "9.9.9.9"},
                    "config": {},
                },
            ],
            "links": [
                {
                    "fromDevice": "pe1",
                    "toDevice": "pe2",
                    "protocol": "LLDP",
                    "linkType": "physical-lldp",
                    "layer": "physical",
                    "fromInterface": "ge100-0/0/1",
                    "toInterface": "ge100-0/0/2",
                }
            ],
            "logicalLinks": [],
            "physicalLinks": [],
            "services": [],
            "groups": [],
            "warnings": [],
            "compositionReport": {"skippedDevices": [{"hostname": "x", "reason": "prior"}]},
            "provenance": {"source": "integration-test"},
        },
    }
    r = client.post("/api/topology-generator/correlate", json=facts_body)
    _assert_eq(r.status_code, 200, "correlate http status")
    out = r.json()
    _assert_true(out.get("ok") is True, "correlate ok")
    f = out.get("facts") or {}
    _assert_eq(len(f.get("devices") or []), 3, "DNAAS hostname device excluded while PE-4 is preserved")
    ev = out.get("correlationEvidence") or {}
    _assert_true(len(ev.get("bgp_edges") or []) >= 1, "at least one BGP edge from peer IP match")
    _assert_true(any(e.get("to") == "pe4" for e in ev.get("bgp_edges") or []),
                 "PE-4 correlated from inferred router-id alias when config auth fails")
    svc = f.get("services") or []
    _assert_true(
        any((s.get("kind") == "vrf" and s.get("name") == "RED") for s in svc),
        "shared VRF emitted as service",
    )
    red = next((s for s in svc if s.get("kind") == "vrf" and s.get("name") == "RED"), {})
    _assert_true("65000:100" in (red.get("routeTargets") or []),
                 "RT evidence is attached under VRF service")
    _assert_eq(red.get("_confidenceClass"), "correlated",
               "VRF service carries correlated confidence metadata")
    _assert_true(bool(red.get("_source")),
                 "VRF service carries source metadata")
    _assert_true("65000:100" in (red.get("_evidence") or []),
                 "VRF service carries route-target evidence metadata")
    _assert_true(not any(s.get("kind") == "rt" for s in svc),
                 "RT is not rendered as standalone service kind")
    lay = ev.get("layout") or {}
    _assert_true(isinstance(lay.get("positions"), dict), "symmetric layout positions")
    phys = (f.get("links") or [])[0]
    _assert_eq((phys.get("linkDetails") or {}).get("ipAddressA"), "192.0.2.0/31",
               "physical link enriched with side A IP")
    _assert_eq(phys.get("_confidenceClass"), "verified",
               "physical link confidence marked verified")
    _assert_true(not (phys.get("linkDetails") or {}).get("vlanIdA"),
                 "physical parent link does not invent subinterface VLAN")
    logical = f.get("logicalLinks") or []
    _assert_true(any((L.get("linkDetails") or {}).get("routerIdB") == "10.255.0.2" for L in logical),
                 "BGP logical links include remote router-id metadata")
    _assert_true(any((L.get("linkType") == "ISIS+LDP") for L in logical),
                 "IGP/LDP stack emitted as ISIS+LDP overlay")
    role_hints = ev.get("roleHints") or {}
    _assert_true(isinstance(role_hints, dict) and role_hints,
                 "correlate emits roleHints map for canvas placement")
    _assert_eq(role_hints.get("pe1"), "pe", "PE-1 classified as pe in roleHints")
    _assert_true(role_hints.get("pe4") in {"pe", "router"},
                 "PE-4 classified as a spoke role in roleHints")
    r = client.post("/api/topology-generator/enrich-link-tables", json={
        "domain_id": "dom-C",
        "topology_id": "topo-cor",
        "devices": [
            {"id": "pe1", "label": "PE-1", "config": facts_body["facts"]["devices"][0]["config"]},
            {"id": "pe2", "label": "PE-2", "config": facts_body["facts"]["devices"][1]["config"]},
        ],
        "links": [
            {"id": "l1", "device1": "pe1", "device2": "pe2",
             "device1Interface": "ge100-0/0/1.100", "device2Interface": "ge100-0/0/2"}
        ],
    })
    _assert_eq(r.status_code, 200, "enrich-link-tables http status")
    patch = (r.json().get("patches") or [])[0]
    _assert_eq(patch["fields"].get("device1VlanId"), "100",
               "enrich-link-tables returns subinterface VLAN patch")
    after = set(scratch.glob("correlate_*.db")) if scratch.exists() else set()
    _assert_eq(len(after - before), 0, "no new correlate_*.db left behind after request")

    # ---------------------------------------------------------------
    _case("POST /correlate hub-spoke triangle for PE-1 / RR-SA-2 / PE-4 trio")
    trio_body = {
        "domain_id": "dom-C",
        "topology_id": "topo-trio",
        "facts": {
            "devices": [
                {
                    "id": "pe1", "hostname": "PE-1", "tier": 1,
                    "ssh": {"host": "100.64.2.33"},
                    "config": {
                        "asn": "1234567", "router_id": "1.1.1.1",
                        "loopback0_ip": "1.1.1.1/32",
                        "isis": {"area": "49.0001", "system_id": "0001.0001.0001"},
                        "mpls": {"enabled": True, "ldp": True, "sr": False},
                        "bgp_peers": [{
                            "peer": "2.2.2.2", "remote_as": "123", "local_as": "1234567",
                            "address_families": ["ipv4-unicast", "ipv4-vpn", "l2vpn-evpn"],
                        }],
                    },
                    "_lldp": [{"peer_hostname": "DNAAS-LEAF-D16", "local_interface": "ge400-0/0/4"}],
                },
                {
                    "id": "rr_sa_2", "hostname": "RR-SA-2", "tier": 0,
                    "ssh": {"host": "100.64.4.205"},
                    "config": {
                        "asn": "123", "router_id": "2.2.2.2",
                        "loopback0_ip": "2.2.2.2/32",
                        "isis": {"area": "49.0001", "system_id": "0002.0002.0002"},
                        "mpls": {"enabled": True, "ldp": True, "sr": False},
                        "bgp_peers": [
                            {
                                "peer": "1.1.1.1", "remote_as": "1234567", "local_as": "123",
                                "address_families": ["ipv4-unicast", "ipv4-vpn", "l2vpn-evpn"],
                            },
                            {
                                "peer": "4.4.4.4", "remote_as": "1234567", "local_as": "123",
                                "address_families": ["ipv4-unicast", "ipv4-vpn", "ipv4-rt-constrain", "l2vpn-evpn"],
                            },
                            {"peer": "25.25.25.1", "remote_as": "65000", "local_as": "123", "source": "spirent"},
                        ],
                    },
                    "_lldp": [{"peer_hostname": "DNAAS-LEAF-B15", "local_interface": "ge400-0/0/0"}],
                },
                {
                    "id": "pe4", "hostname": "YOR_CL_PE-4", "tier": 1,
                    "ssh": {"host": "100.64.10.22"},
                    "config": {
                        "asn": "1234567", "router_id": "4.4.4.4",
                        "loopback0_ip": "4.4.4.4/32",
                        "isis": {
                            "area": "49.0001",
                            "system_id": "0010.0000.0001",
                            "neighbors": [
                                {
                                    "hostname": "jun204-rt02",
                                    "interface": "ge100-18/0/0.45",
                                    "areas": ["49.0002", "49.0003"],
                                }
                            ],
                        },
                        "mpls": {"enabled": True, "ldp": True, "sr": False},
                        "bgp_peers": [
                            {
                                "peer": "2.2.2.2", "remote_as": "123", "local_as": "1234567",
                                "address_families": ["ipv4-unicast", "ipv4-vpn", "ipv4-rt-constrain", "l2vpn-evpn"],
                            },
                            {
                                "peer": "100.64.6.134", "remote_as": "65200", "local_as": "1234567",
                                "source": "exabgp",
                                "address_families": ["ipv4-unicast", "ipv4-vpn", "ipv4-flowspec"],
                            },
                            *[
                                {"peer": f"10.99.101.{i}", "remote_as": "65200", "local_as": "1234567"}
                                for i in range(1, 13)
                            ],
                        ],
                    },
                    "_lldp": [{"peer_hostname": "DNAAS-LEAF-B10", "local_interface": "ge100-18/0/0"}],
                },
            ],
            "links": [],
            "logicalLinks": [],
            "physicalLinks": [],
            "services": [],
            "groups": [],
            "warnings": [],
            "compositionReport": {},
            "provenance": {"source": "trio-fixture"},
        },
    }
    r = client.post("/api/topology-generator/correlate", json=trio_body)
    _assert_eq(r.status_code, 200, "trio correlate http status")
    out = r.json()
    _assert_true(out.get("ok") is True, "trio correlate ok")
    ev = out.get("correlationEvidence") or {}
    layout = ev.get("layout") or {}
    _assert_eq(layout.get("mode"), "hub-spoke-triangle",
               "trio uses hub-spoke-triangle layout")
    role_hints = ev.get("roleHints") or {}
    _assert_eq(role_hints.get("rr_sa_2"), "rr",
               "RR-SA-2 classified as rr from name pattern")
    _assert_eq(role_hints.get("pe1"), "pe", "PE-1 classified as pe")
    _assert_eq(role_hints.get("pe4"), "pe", "PE-4 classified as pe")
    positions = layout.get("positions") or {}
    rr_pos = positions.get("rr_sa_2") or {}
    pe1_pos = positions.get("pe1") or {}
    pe4_pos = positions.get("pe4") or {}
    _assert_true(rr_pos.get("y", 9999) < pe1_pos.get("y", 0),
                 "RR sits above PE-1 in canvas")
    _assert_true(rr_pos.get("y", 9999) < pe4_pos.get("y", 0),
                 "RR sits above PE-4 in canvas")
    _assert_true(pe1_pos.get("x", 0) < pe4_pos.get("x", 0),
                 "PEs flank the RR (PE-1 left, PE-4 right) for triangle smoothness")
    _assert_eq(pe1_pos.get("y"), pe4_pos.get("y"),
               "Both PEs share the same spoke baseline")
    perimeter = ev.get("perimeter") or []
    _assert_true(any(p.get("_perimeterKind") == "scale-fan" and p.get("_perimeterCount") == 1
                     and "10.99.101.0/24 x12" in (p.get("hostname") or "") for p in perimeter),
                 "scale-fan perimeter node compacts 12 peers in 10.99.101.0/24")
    _assert_true(any(p.get("_perimeterKind") == "fabric" for p in perimeter),
                 "fabric LLDP peers are grouped as perimeter nodes")
    _assert_true(any(p.get("_perimeterKind") == "foreign-igp" and p.get("hostname") == "jun204-rt02"
                     for p in perimeter),
                 "foreign ISIS area neighbor is kept as perimeter evidence")
    _assert_eq(ev.get("overlayModesAvailable"), ["real-legs", "via-rr", "both"],
               "overlay modes surfaced for protocol panel")
    logical = (out.get("facts") or {}).get("logicalLinks") or []
    _assert_true(all(L.get("_confidenceClass") in {"verified", "correlated", "inferred", "missing"} for L in logical),
                 "logical links carry scene confidence class")
    _assert_true(any("ipv4-rt-constrain" in ((L.get("linkDetails") or {}).get("addressFamilies") or [])
                     for L in logical if L.get("linkType") in {"eBGP", "iBGP"}),
                 "BGP AF passthrough preserves ipv4-rt-constrain")

    print("\nALL TOPOLOGY-GENERATOR INTEGRATION TESTS PASSED")


if __name__ == "__main__":
    main()
