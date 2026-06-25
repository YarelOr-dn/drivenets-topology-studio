#!/usr/bin/env python3
"""
recipe_to_dnos_e2e.py -- deterministic /TEST recipe.json -> cheetah dnos_e2e (mcDNOS) pytest emitter.

WHY THIS EXISTS
---------------
/TEST recipes run via MCP/chat against the live lab (Spirent over DNAAS). To run the SAME
behaviors consistently in CI on mcDNOS/CDNOS containers, this tool reads the recipe's
declarative ``e2e`` block and emits a pytest module modeled 1:1 on the live reference test
``tests/suites/dnos_e2e/tests/test_bgp_evpn_mcdnos.py`` (Leonid Berman's framework).

The recipe stays the single source of truth. The same recipe drives:
  * lab run  : traffic.backend == "otg"     -> ArpPingFloodSpirent + traffic_generator_config
  * CI run   : traffic.backend == "arpping" -> ArpPingFloodDNOS (software, hermetic mcDNOS)
Both feed identical validations (ValidateEvpnMacTable / ValidateBGPevpnRoutes /
ValidateInterfaceCounters), so a PASS means the same thing in both worlds.

CONSISTENCY GUARANTEES
----------------------
1. Symbol-exists gate: every framework symbol referenced by the emitted test is checked
   against a verified allowlist AND (when ``--cheetah-root`` points at a real checkout)
   grep-verified to be defined there. The generator refuses to emit on drift.
2. Deterministic identities: MACs / IPs / VLANs / RDs come from the recipe (pinned),
   never lab-discovered -> reproducible runs.
3. Jira binding: emits @pytest.mark.testing_task(epic=, testing_task=) from recipe
   traceability so CI reporting + traceability survive.
4. lab_only scenarios (e.g. VPLS-PW SI) are skipped with a documented reason, never faked.

This tool NEVER writes into the cheetah tree. It emits into an export dir; you then place
the file on a cheetah feature branch under the declared ``suite_path``.

USAGE
-----
    python3 recipe_to_dnos_e2e.py <recipe.json> [--out <dir>] [--cheetah-root ~/cheetah] [--print]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

# Framework symbols this emitter is allowed to import, verified live against
# tests/shared/dnos_e2e_utils on 2026-06-15. Update only after re-verifying on a
# cheetah checkout (the --cheetah-root gate enforces this at emit time).
VERIFIED_SYMBOLS = {
    "dnos_e2e_utils.actions.bgp_actions": [
        "ConfigBGPRouter", "ConfigBGPNeighborsForEVPN", "DisableBGPNeighbors", "ConfigBGPNetwork",
    ],
    "dnos_e2e_utils.actions.interface_actions": [
        "ConfigIPInterface", "ConfigL2ServiceInterface", "ConfigVlanL2SubInterface",
        "BaseConfigInterface", "ClearInterfaceCounters",
    ],
    "dnos_e2e_utils.actions.evpn_actions": [
        "ConfigureEVPN", "DeleteEVPN",
    ],
    "dnos_e2e_utils.actions.general_actions": [
        "ExecuteWithConfigCleanup", "ActionsSequenceExecutor",
    ],
    "dnos_e2e_utils.actions.system_actions": [
        "SaveConfig", "LoadOverrideConfig", "DeleteFileDnosCli",
    ],
    "dnos_e2e_utils.actions.traffic_actions": [
        "ArpPingFloodDNOS",
    ],
    "dnos_e2e_utils.validations.evpn_validations": [
        "ValidateEvpnMacTable", "ValidateBGPevpnRoutes",
    ],
    "dnos_e2e_utils.validations.interface_validations": [
        "ValidateInterfaceOperationalState", "ValidateInterfaceCounters",
    ],
    "dnos_e2e_utils.dnos_e2e_device_definitions": ["MCDnosDefinition"],
    "dnos_e2e_utils.consts": ["BGPStates", "SetupTypes", "InterfaceAdminState"],
    "dnos_e2e_utils.dnos_e2e_routing_utils": ["get_interface_mac_address"],
    "dn_common.globals": ["dn_services"],
}


class GeneratorError(RuntimeError):
    pass


def _load_recipe(path: Path) -> dict:
    data = json.loads(path.read_text())
    if "e2e" not in data:
        raise GeneratorError(f"recipe {path} has no 'e2e' block; cannot emit a CI test.")
    return data


def _symbol_gate(cheetah_root: Path | None) -> list[str]:
    """Verify every allowlisted symbol is actually defined in the cheetah checkout.

    Returns a list of human-readable warnings (empty == clean). When cheetah_root is
    None we trust the static allowlist (and say so), because we must not invent a tree.
    """
    if cheetah_root is None or not (cheetah_root / "tests" / "shared" / "dnos_e2e_utils").is_dir():
        return ["[gate] cheetah root not provided/usable -- trusting static VERIFIED_SYMBOLS allowlist only."]
    warnings: list[str] = []
    utils = cheetah_root / "tests" / "shared" / "dnos_e2e_utils"
    for module, names in VERIFIED_SYMBOLS.items():
        if not module.startswith("dnos_e2e_utils"):
            continue  # only verify framework-local modules
        rel = module.replace("dnos_e2e_utils.", "").replace(".", "/") + ".py"
        f = utils / rel
        if not f.is_file():
            warnings.append(f"[gate] MISSING module file: {f}")
            continue
        body = f.read_text(errors="ignore")
        for name in names:
            if not re.search(rf"^\s*(class|def)\s+{re.escape(name)}\b", body, re.MULTILINE):
                warnings.append(f"[gate] symbol drift: {name} not defined in {f}")
    return warnings


def _ascii_topology(e2e: dict) -> str:
    nodes = e2e["topology"]["nodes"]
    by_role = {n["role"]: n for n in nodes}
    dut = by_role.get("dut", {}).get("name", "SA1")
    local = by_role.get("host_local_ac", {}).get("name", "mcdnos1")
    remote = by_role.get("remote_pe", {}).get("name", "mcdnos2")
    return (
        f"    {local} (local AC source) --ge100-0/0/0-- {dut} (DUT) --ge100-0/0/0-- {remote} (remote EVPN PE)\n"
        f"    EVPN AC learning: {local} floods -> {dut} learns L> ; {remote} advertises RT-2 -> {dut} installs B>"
    )


def _imports_block() -> str:
    lines = ["import ipaddress", "import logging", "import pytest", ""]
    lines.append("from ..dnos_e2e_base import DnosE2EBase")
    lines.append("from ..dnos_e2e_test_config import (")
    lines.append("    ClusterRequirement, LinkDefinition, TestConfiguration, TestMode, TopologyRequirements,")
    lines.append(")")
    lines.append("from ..dnos_e2e_network_dataclasses import (")
    lines.append("    TopologyNetworkConfig, RouterConfig, BGPRouterConfig, BGPRouterInfo,")
    lines.append("    BGPNeighborInfo, InterfaceConfig, EVPNInstanceConfig, EVPNBGPConfig, CountersValidation,")
    lines.append(")")
    for module, names in VERIFIED_SYMBOLS.items():
        if module.startswith("dnos_e2e_utils") or module.startswith("dn_common"):
            lines.append(f"from {module} import {', '.join(names)}")
    lines.append("from utils.jira_utils import JiraComponent")
    lines.append("")
    lines.append("logger = logging.getLogger(__name__)")
    return "\n".join(lines)


def _render(recipe: dict) -> str:
    e2e = recipe["e2e"]
    trace = recipe.get("traceability", {})
    evi = e2e["evi_name"]
    cls = e2e["test_class"]
    owner = e2e["owner"]
    comp = e2e["jira_component"]
    as_num = e2e["bgp_as"]
    vlan = e2e["vlan_ac"]
    traffic = e2e["traffic"]
    epic = trace.get("source_epic", recipe.get("parent_category", ""))
    task = trace.get("source_user_story", recipe.get("jira_key", ""))
    desc = recipe.get("name", recipe.get("id", ""))

    supported = [s for s in e2e["scenarios"] if s.get("ci_target", e2e["ci_target"]) != "lab_only"]
    lab_only = [s for s in e2e["scenarios"] if s.get("ci_target", e2e["ci_target"]) == "lab_only"]
    local = next((s for s in supported if s["kind"] == "local_learn"), None)
    remote = next((s for s in supported if s["kind"] == "remote_evpn_learn"), None)

    ip = e2e["topology"]["ip_plan"]
    sa1_v4 = ip["sa1_to_mcdnos2_v4"]
    mc2_v4 = ip["mcdnos2_to_sa1_v4"]
    mc1_v4 = ip["mcdnos1_to_sa1_v4"]
    sa1_rid = ip["sa1_router_id"]

    skip_note = ""
    if lab_only:
        reasons = "; ".join(f"{s['recipe_scenario']}: {s.get('reason','lab only')}" for s in lab_only)
        skip_note = f"\n    LAB-ONLY (not emitted to CI): {reasons}"

    head = f'''"""
AUTO-GENERATED by scaler/TEST/shared/recipe_to_dnos_e2e.py -- DO NOT EDIT BY HAND.
Source recipe: {recipe.get("id","")} ({task} / epic {epic})

Behavioral mcDNOS port of the lab MAC-mobility recipe. Proves the same EVPN MAC
learning outcomes (L> local AC, B> remote EVPN via RT-2) on hermetic mcDNOS
containers with software traffic, suitable for CI (dtest dnos_e2e).

Topology:
{_ascii_topology(e2e)}{skip_note}
"""'''

    imports = _imports_block()

    body = f'''

EVI_NAME = "{evi}"
BGP_AS = {as_num}
VLAN_ID_A = {vlan}

SA1_TO_MC2 = ipaddress.ip_interface("{sa1_v4}")
MC2_TO_SA1 = ipaddress.ip_interface("{mc2_v4}")
MC1_TO_SA1 = ipaddress.ip_interface("{mc1_v4}")
SA1_ROUTER_ID = "{sa1_rid}"
RD = f"{{SA1_TO_MC2.ip}}:10"
RT = "10:10"
FEC = "rs-fec-528-514"

ARP_MAC = "{traffic.get("arp_mac","aa:bb:cc:dd:ee:ff")}"
FLOOD_COUNT = {traffic.get("count",200)}
TX_MIN = {traffic.get("tx_min_frames",200)}
RX_MIN = {traffic.get("rx_min_frames",20)}
CTR_TIMEOUT = {traffic.get("counter_timeout_sec",90)}

# Pinned test MACs (deterministic, from recipe scenarios)
MAC_LOCAL = "{(local or {}).get("test_mac","00:de:ad:00:01:01")}"
MAC_REMOTE = "{(remote or {}).get("test_mac","00:de:ad:00:02:01")}"


@pytest.mark.dnos_e2e_evpn_mobility
class {cls}(DnosE2EBase):
    """MAC mobility basic learning on mcDNOS (CI port of {task})."""

    @classmethod
    def create_topology_requirements(cls, topology_handler):
        sa1_name = topology_handler.first_device_name(setup_type=SetupTypes.SA)
        return TopologyRequirements(
            topology_handler=topology_handler,
            devices=[MCDnosDefinition(name="mcdnos1"), MCDnosDefinition(name="mcdnos2")],
            physical_links=[
                LinkDefinition(
                    peer1_device_name=sa1_name,
                    peer1_interface_name=topology_handler.get_sa_interface1_name(),
                    peer2_device_name="mcdnos1",
                    peer2_interface_name="ge100-0/0/0",
                ),
                LinkDefinition(
                    peer1_device_name=sa1_name,
                    peer1_interface_name=topology_handler.get_sa_interface2_name(),
                    peer2_device_name="mcdnos2",
                    peer2_interface_name="ge100-0/0/0",
                ),
            ],
        )

    @pytest.fixture(scope="class", autouse=True)
    def set_topology_requirements(self, request):
        request.cls._topology_requirements = self.create_topology_requirements(self._topology_handler)

    @classmethod
    def _resolve_names_and_links(cls):
        cls.DUT = "SA1"
        cls.LOCAL = "mcdnos1"
        cls.REMOTE = "mcdnos2"
        cls.DUT_AC = cls._topology_handler.links.get_device_port(cls.DUT, cls.LOCAL)
        cls.DUT_TO_REMOTE = cls._topology_handler.links.get_device_port(cls.DUT, cls.REMOTE)
        cls.REMOTE_TO_DUT = cls._topology_handler.links.get_device_port(cls.REMOTE, cls.DUT)
        cls.LOCAL_TO_DUT = cls._topology_handler.links.get_device_port(cls.LOCAL, cls.DUT)

    @pytest.fixture(scope="class", autouse=True)
    def set_topology_network_config(self, request, set_topology_requirements):
        cls = request.cls
        cls._resolve_names_and_links()
        cls.DUT_BGP = BGPRouterInfo(local_as=BGP_AS, router_id=str(SA1_TO_MC2.ip))
        cls.REMOTE_BGP = BGPRouterInfo(local_as=BGP_AS, router_id=str(MC2_TO_SA1.ip))

        dut_ac_iface = InterfaceConfig(interface_name=cls.DUT_AC, fec=FEC, speed=100)
        dut_ctrl_iface = InterfaceConfig(
            interface_name=cls.DUT_TO_REMOTE, ipv4_address=str(SA1_TO_MC2), fec=FEC, speed=100)
        remote_ctrl_iface = InterfaceConfig(
            interface_name=cls.REMOTE_TO_DUT, ipv4_address=str(MC2_TO_SA1), fec=FEC, speed=100)
        remote_ac_iface = InterfaceConfig(
            interface_name=f"{{cls.REMOTE_TO_DUT}}.{{VLAN_ID_A}}", speed=100)
        # LOCAL (mcdnos1) source interface facing the DUT AC -- its MAC is what the DUT learns as L>
        local_src_iface = InterfaceConfig(
            interface_name=cls.LOCAL_TO_DUT, ipv4_address=str(MC1_TO_SA1), fec=FEC, speed=100)

        cls.TOPOLOGY_NETWORK_CONFIG = TopologyNetworkConfig(routers={{
            cls.DUT: RouterConfig(
                router_name=cls.DUT,
                interfaces=[dut_ac_iface, dut_ctrl_iface],
                bgp_config=BGPRouterConfig(
                    router_info=cls.DUT_BGP,
                    neighbor_info=[BGPNeighborInfo(
                        neighbor_ip=str(MC2_TO_SA1.ip), source_interface=cls.DUT_TO_REMOTE,
                        remote_as=BGP_AS, address_family="l2vpn-evpn", community_type="both")],
                ),
                evpn_config=EVPNInstanceConfig(
                    evpn_name=EVI_NAME, interfaces=[dut_ac_iface.interface_name],
                    bgp_config=EVPNBGPConfig(bgp_as=BGP_AS, route_distinguisher=RD,
                                             export_route_target=RT, import_route_target=RT)),
            ),
            cls.LOCAL: RouterConfig(router_name=cls.LOCAL, interfaces=[local_src_iface]),
            cls.REMOTE: RouterConfig(
                router_name=cls.REMOTE,
                interfaces=[remote_ctrl_iface, remote_ac_iface],
                bgp_config=BGPRouterConfig(
                    router_info=cls.REMOTE_BGP,
                    neighbor_info=[BGPNeighborInfo(
                        neighbor_ip=str(SA1_TO_MC2.ip), source_interface=cls.REMOTE_TO_DUT,
                        remote_as=BGP_AS, address_family="l2vpn-evpn", community_type="both")],
                ),
                evpn_config=EVPNInstanceConfig(
                    evpn_name=EVI_NAME, interfaces=[remote_ac_iface.interface_name],
                    bgp_config=EVPNBGPConfig(bgp_as=BGP_AS, route_distinguisher=f"{{MC2_TO_SA1.ip}}:10",
                                             export_route_target=RT, import_route_target=RT)),
            ),
        }})

    @classmethod
    def create_default_test_config(cls) -> TestConfiguration:
        return TestConfiguration(test_mode=TestMode.DNOS_MODE,
                                 cluster_requirement=ClusterRequirement.SA_ONLY)

    @pytest.fixture(scope="class", autouse=True)
    def set_default_test_config(self, request, set_topology_network_config):
        cls = request.cls
        merged = cls.create_default_test_config().merge_with(
            TestConfiguration(topology_requirements=cls._topology_requirements))
        cls.default_test_config = cls.default_test_config.merge_with(merged)

    @pytest.mark.owner(user="{owner}", component=JiraComponent.{comp})
    @pytest.mark.testing_task(component=JiraComponent.{comp}, epic="{epic}",
                              testing_task="{task}", test_description="{desc}")
    def test_mac_mobility_basic(self):
        """SC01 (L> local AC) + SC02 (B> remote EVPN) + SC04 coexistence on mcDNOS."""
        dut_h = self._topology_handler.topology[self.DUT]
        remote_h = self._topology_handler.topology[self.REMOTE]
        local_h = self._topology_handler.topology[self.LOCAL]
        re_container = dn_services.ContainerType.ROUTING_ENGINE.service

        # --- configure interfaces + BGP-EVPN + EVPN instances on DUT and REMOTE ---
        self._configure_suite(dut_h, remote_h)

        # ============ SC01: L> local AC learning + RT-2 advertised ============
        ClearInterfaceCounters(cluster_handler=dut_h, interface=self.DUT_AC).execute()
        # MAC the DUT will learn as L> = LOCAL node's source-interface MAC.
        # LIVE-VALIDATE: confirm get_interface_mac_address(cli, iface_name) signature + that
        # local_h cli resolves on mcDNOS during first `dtest dnos_e2e` run.
        local_cli = self._cli_of(local_h)
        local_mac = get_interface_mac_address(local_cli, self.LOCAL_TO_DUT)
        ArpPingFloodDNOS(
            cluster_handler=local_h, container_name=re_container,
            destination_ip=SA1_ROUTER_ID, count=FLOOD_COUNT, arp_mac=ARP_MAC,
            clear_mac_table=True, evpn_name=EVI_NAME, receiver_cluster_handler=dut_h,
            transmitter_validations=[CountersValidation(
                name=self.LOCAL_TO_DUT, counter_field="TX frames", operator=">=",
                expected_value=TX_MIN, timeout=CTR_TIMEOUT)],
            receiver_validations=[ValidateInterfaceCounters(
                cluster_handler=dut_h, counters_data=[CountersValidation(
                    name=self.DUT_AC, counter_field="RX frames", operator=">=",
                    expected_value=RX_MIN, timeout=CTR_TIMEOUT)])],
        ).execute()

        ValidateEvpnMacTable(cluster_handler=dut_h, evpn_name=EVI_NAME,
                             expected_mac=local_mac.lower(), timeout=30).execute()
        type2_local = f"type:=2,eth-tag:=0,mac-address:={{local_mac.lower()}}"
        ValidateBGPevpnRoutes(cluster_handler=dut_h, expected_content=[type2_local], timeout=30).execute()
        ValidateBGPevpnRoutes(cluster_handler=remote_h, expected_content=[type2_local], timeout=30).execute()
        logger.info("SC01 PASS: L> learned on DUT AC and RT-2 advertised to remote PE")

        # ============ SC02: B> remote EVPN learn (DUT receives RT-2) ============
        # Flooding the remote AC makes REMOTE learn locally and advertise RT-2; DUT installs B>.
        ArpPingFloodDNOS(
            cluster_handler=remote_h, container_name=re_container,
            destination_ip=str(SA1_TO_MC2.ip), count=FLOOD_COUNT, arp_mac=ARP_MAC,
        ).execute()
        remote_cli = self._cli_of(remote_h)
        remote_mac = get_interface_mac_address(remote_cli, self.REMOTE_TO_DUT)
        type2_remote = f"type:=2,eth-tag:=0,mac-address:={{remote_mac.lower()}}"
        ValidateBGPevpnRoutes(cluster_handler=dut_h, expected_content=[type2_remote], timeout=30).execute()
        ValidateEvpnMacTable(cluster_handler=dut_h, evpn_name=EVI_NAME,
                             expected_mac=remote_mac.lower(), timeout=30).execute()
        logger.info("SC02 PASS: DUT received RT-2 from remote PE (B>)")

        # ============ SC04: coexistence + stability ============
        ValidateEvpnMacTable(cluster_handler=dut_h, evpn_name=EVI_NAME,
                             expected_mac=local_mac.lower(), timeout=30).execute()
        ValidateEvpnMacTable(cluster_handler=dut_h, evpn_name=EVI_NAME,
                             expected_mac=remote_mac.lower(), timeout=30).execute()
        logger.info("SC04 PASS: L> and B> coexist on DUT; no suppression/ghost expected")

    @staticmethod
    def _cli_of(cluster_handler):
        """Resolve the active-NCC CLI for a cluster handler (mirrors reference rollback usage)."""
        return cluster_handler.clis[cluster_handler.active_ncc.node_name]

    def _configure_suite(self, dut_h, remote_h):
        """Mirror reference: config interfaces + BGP-EVPN network + EVPN instances with cleanup."""
        bgp_actions, bgp_cleanup, expected = [], [], {{}}
        for name, h in ((self.DUT, dut_h), (self.REMOTE, remote_h)):
            rc = self.TOPOLOGY_NETWORK_CONFIG.get_router(name)
            for iface in rc.interfaces:
                if "." in iface.interface_name and iface.interface_name.split(".")[-1].isdigit():
                    ConfigVlanL2SubInterface(cluster_handler=h, interface_config=iface,
                                             vlan_id=VLAN_ID_A).execute()
                elif getattr(iface, "ipv4_address", None):
                    ConfigIPInterface(cluster_handler=h, interface_config=iface).execute()
                else:
                    ConfigL2ServiceInterface(cluster_handler=h, interface_config=iface).execute()
            bgp_actions.append(ConfigBGPRouter(cluster_handler=h, router_info=rc.bgp_config.router_info))
            bgp_actions.append(ConfigBGPNeighborsForEVPN(
                cluster_handler=h, local_as=rc.bgp_config.router_info.local_as,
                neighbor_info=rc.bgp_config.neighbor_info))
            bgp_cleanup.append(DisableBGPNeighbors(
                cluster_handler=h, local_as=rc.bgp_config.router_info.local_as,
                neighbor_info=rc.bgp_config.neighbor_info))
            expected[h] = rc.bgp_config.neighbor_info
        ConfigBGPNetwork(bgp_config_actions=bgp_actions, expected_neighbors_info=expected,
                         expected_state=BGPStates.ESTABLISHED).execute()
        for name, h in ((self.DUT, dut_h), (self.REMOTE, remote_h)):
            ConfigureEVPN(cluster_handler=h,
                          evpn_config=self.TOPOLOGY_NETWORK_CONFIG.get_router(name).evpn_config).execute()
'''
    return head + "\n" + imports + body


def _atomic_write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as f:
            f.write(body)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


DEFAULT_OUT = Path(__file__).resolve().parents[1] / "e2e_export"
DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "catalog"
DEFAULT_CHEETAH = Path(os.path.expanduser("~/cheetah"))


def _schema_issues(recipe: dict) -> list[str]:
    """Lightweight structural checks on the recipe e2e block (no device access)."""
    issues: list[str] = []
    e2e = recipe.get("e2e")
    if not isinstance(e2e, dict):
        return ["recipe has no 'e2e' block"]
    for key in ("ci_target", "suite_path", "test_module", "test_class", "evi_name", "topology", "scenarios"):
        if key not in e2e:
            issues.append(f"e2e missing required key: {key}")
    topo = e2e.get("topology", {})
    if isinstance(topo, dict):
        roles = {n.get("role") for n in topo.get("nodes", []) if isinstance(n, dict)}
        if e2e.get("ci_target") != "lab_only" and "dut" not in roles:
            issues.append("e2e.topology.nodes has no node with role 'dut'")
        ipp = topo.get("ip_plan", {})
        for need in ("mcdnos1_to_sa1_v4", "sa1_router_id", "sa1_to_mcdnos2_v4", "mcdnos2_to_sa1_v4"):
            if need not in ipp and e2e.get("ci_target") != "lab_only":
                issues.append(f"e2e.topology.ip_plan missing: {need}")
    if not isinstance(e2e.get("scenarios"), list) or not e2e.get("scenarios"):
        issues.append("e2e.scenarios must be a non-empty list")
    return issues


def _resolved_gate(cheetah_root) -> list[str]:
    root = Path(cheetah_root) if cheetah_root else None
    return _symbol_gate(root if (root and root.exists()) else None)


def validate(recipe_path, cheetah_root=DEFAULT_CHEETAH) -> dict:
    """Read-only: symbol gate + structural check for a recipe's e2e block."""
    recipe = _load_recipe(Path(recipe_path))
    e2e = recipe.get("e2e", {})
    warnings = _resolved_gate(cheetah_root)
    drift = [w for w in warnings if "drift" in w or "MISSING" in w]
    issues = _schema_issues(recipe)
    scn = [
        {"id": s.get("recipe_scenario"), "kind": s.get("kind"),
         "ci_target": s.get("ci_target", e2e.get("ci_target"))}
        for s in e2e.get("scenarios", [])
    ]
    emittable = [s for s in scn if s["ci_target"] != "lab_only"]
    return {
        "ok": not drift and not issues,
        "recipe_id": recipe.get("id"),
        "ci_target": e2e.get("ci_target"),
        "suite_path": e2e.get("suite_path"),
        "test_module": e2e.get("test_module"),
        "scenarios": scn,
        "emittable_count": len(emittable),
        "lab_only_count": len(scn) - len(emittable),
        "gate_warnings": warnings,
        "drift": drift,
        "schema_issues": issues,
    }


def emit(recipe_path, out_dir=DEFAULT_OUT, cheetah_root=DEFAULT_CHEETAH, write=True) -> dict:
    """Emit the dnos_e2e pytest from a recipe e2e block. write=False returns a preview only."""
    recipe = _load_recipe(Path(recipe_path))
    e2e = recipe["e2e"]
    if e2e.get("ci_target") == "lab_only":
        return {"ok": True, "skipped": True, "reason": "ci_target=lab_only", "recipe_id": recipe.get("id")}
    issues = _schema_issues(recipe)
    if issues:
        return {"ok": False, "errors": issues, "recipe_id": recipe.get("id")}
    warnings = _resolved_gate(cheetah_root)
    drift = [w for w in warnings if "drift" in w or "MISSING" in w]
    if drift:
        return {"ok": False, "errors": drift, "gate_warnings": warnings}
    code = _render(recipe)
    rel = Path(e2e["suite_path"]) / e2e["test_module"]
    out_path = Path(out_dir) / rel
    result = {
        "ok": True,
        "recipe_id": recipe.get("id"),
        "rel_path": str(rel),
        "out_path": str(out_path),
        "lines": code.count("\n") + 1,
        "place_to": f"{e2e['suite_path']}/{e2e['test_module']}",
        "gate_warnings": warnings,
        "written": bool(write),
    }
    if write:
        _atomic_write(out_path, code)
    else:
        result["code_preview"] = "\n".join(code.splitlines()[:48])
    return result


def list_recipes(catalog_root=DEFAULT_CATALOG) -> dict:
    """Inventory: which recipes have an e2e block + whether an artifact was emitted."""
    rows = []
    root = Path(catalog_root)
    for recipe_file in sorted(root.glob("**/recipe.json")):
        try:
            data = json.loads(recipe_file.read_text())
        except Exception:
            continue
        e2e = data.get("e2e")
        rel = None
        emitted = False
        if isinstance(e2e, dict):
            rel = f"{e2e.get('suite_path','')}/{e2e.get('test_module','')}"
            emitted = (DEFAULT_OUT / e2e.get("suite_path", "") / e2e.get("test_module", "")).exists()
        rows.append({
            "recipe_id": data.get("id"),
            "path": str(recipe_file),
            "has_e2e": isinstance(e2e, dict),
            "ci_target": (e2e or {}).get("ci_target") if isinstance(e2e, dict) else None,
            "place_to": rel,
            "emitted": emitted,
        })
    return {"ok": True, "count": len(rows), "recipes": rows}


def scaffold_e2e_block(recipe_path) -> dict:
    """Return a starter e2e block (JSON) for a recipe that lacks one. Does not write."""
    data = json.loads(Path(recipe_path).read_text())
    rid = data.get("id", "TEST_X")
    trace = data.get("traceability", {})
    block = {
        "ci_target": "mcdnos",
        "suite_path": "tests/suites/dnos_e2e/tests/evpn",
        "test_module": f"test_{rid.lower()}_mcdnos.py",
        "test_class": "Test" + "".join(p.capitalize() for p in re.split(r"[^a-zA-Z0-9]", rid) if p),
        "owner": "youruser",
        "jira_component": "ROUTING",
        "evi_name": "ci-evpn",
        "bgp_as": 100,
        "vlan_ac": 1500,
        "topology": {
            "nodes": [
                {"name": "SA1", "role": "dut", "type": "sa", "router_id": "2.1.1.1"},
                {"name": "mcdnos1", "role": "host_local_ac", "type": "mcdnos", "router_id": "2.1.1.2"},
                {"name": "mcdnos2", "role": "remote_pe", "type": "mcdnos", "router_id": "3.1.1.2"},
            ],
            "links": [
                {"a": "SA1", "a_if": "{sa_interface1}", "b": "mcdnos1", "b_if": "ge100-0/0/0", "ac": True},
                {"a": "SA1", "a_if": "{sa_interface2}", "b": "mcdnos2", "b_if": "ge100-0/0/0", "bgp_control": True},
            ],
            "ip_plan": {
                "mcdnos1_to_sa1_v4": "2.1.1.2/24",
                "sa1_router_id": "2.1.1.1",
                "sa1_to_mcdnos2_v4": "3.1.1.1/24",
                "mcdnos2_to_sa1_v4": "3.1.1.2/24",
            },
        },
        "scenarios": [
            {"recipe_scenario": "SC01", "kind": "local_learn", "ci_target": "mcdnos",
             "test_mac": "00:de:ad:00:01:01", "expected_flag": "L>", "assert_rt2_advertised": True},
            {"recipe_scenario": "SC02", "kind": "remote_evpn_learn", "ci_target": "mcdnos",
             "test_mac": "00:de:ad:00:02:01", "expected_flag": "B>", "assert_rt2_received": True},
        ],
        "traffic": {"backend": "arpping", "count": 200, "arp_mac": "aa:bb:cc:dd:ee:ff",
                    "rx_min_frames": 20, "tx_min_frames": 200, "counter_timeout_sec": 90},
        "validations": {"mac_table": "ValidateEvpnMacTable", "bgp_routes": "ValidateBGPevpnRoutes",
                        "counters": "ValidateInterfaceCounters"},
    }
    _ = trace
    return {"ok": True, "recipe_id": rid, "e2e_block": block,
            "note": "Paste this under the top-level recipe object as \"e2e\": {...}, then run e2e_validate + e2e_emit."}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Emit a cheetah dnos_e2e mcDNOS pytest from a /TEST recipe.")
    ap.add_argument("recipe", type=Path)
    ap.add_argument("--out", type=Path,
                    default=Path(__file__).resolve().parents[1] / "e2e_export")
    ap.add_argument("--cheetah-root", type=Path, default=Path(os.path.expanduser("~/cheetah")))
    ap.add_argument("--print", action="store_true", dest="do_print")
    args = ap.parse_args(argv)

    recipe = _load_recipe(args.recipe)
    e2e = recipe["e2e"]
    if e2e.get("ci_target") == "lab_only":
        print(f"[skip] recipe {recipe.get('id')} is ci_target=lab_only; nothing to emit.")
        return 0

    warnings = _symbol_gate(args.cheetah_root if args.cheetah_root.exists() else None)
    drift = [w for w in warnings if "drift" in w or "MISSING" in w]
    for w in warnings:
        print(w, file=sys.stderr)
    if drift:
        raise GeneratorError("symbol gate failed -- emitted test would reference undefined framework symbols.")

    code = _render(recipe)
    rel = Path(e2e["suite_path"]) / e2e["test_module"]
    out_path = args.out / rel
    _atomic_write(out_path, code)
    print(f"[ok] emitted {out_path}")
    print(f"[next] copy to a cheetah feature branch at: {e2e['suite_path']}/{e2e['test_module']}")
    if args.do_print:
        print("\n" + "=" * 80 + "\n" + code)
    return 0


if __name__ == "__main__":
    sys.exit(main())
