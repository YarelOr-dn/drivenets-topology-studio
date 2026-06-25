"""SSH/CLI implementation of live link telemetry."""
from __future__ import annotations

import json
import time
from typing import List, Optional

from routes._device_comm import DeviceCommHelper
try:
    from routes.bridge_helpers import _get_cached_config
except Exception:  # pragma: no cover - bridge helpers are optional in tests
    _get_cached_config = None

from . import cache
from .config_parser import (
    parse_bgp_summary,
    parse_isis_neighbors,
    parse_ldp_neighbors,
    parse_ospf_neighbors,
    parse_show_config_flatten,
)
from .parsers import (
    attach_lldp_to_interfaces,
    merge_interface_facts,
    merge_counters,
    parse_interfaces,
    parse_interfaces_counters,
    parse_interfaces_description,
    parse_lacp_interfaces,
    parse_lldp_neighbors,
)
from .provider_base import (
    AttachmentInfo,
    BundleRow,
    BundleMemberRow,
    CanvasDevice,
    CounterRow,
    DeviceTelemetry,
    InterfaceRow,
    LldpEdge,
    ProtocolInfo,
    ProtocolNeighbor,
    SubInterfaceRow,
    TelemetryProvider,
)


SHOW_COMMANDS = [
    "show interfaces",
    "show interfaces description",
    "show interfaces counters",
    "show lldp neighbors",
    "show lacp interfaces",
    "show config | flatten",
    "show config defaults interfaces",
    "show bgp summary",
    "show isis neighbors",
    "show ospf neighbors",
    "show ldp neighbors detail",
]


def _scalar_vlan(value: str) -> str:
    clean = str(value or "").strip()
    if clean.isdigit():
        return clean
    return ""


# region agent log
def _agent_debug_log(hypothesis_id: str, message: str, data: dict) -> None:
    try:
        payload = {
            "sessionId": "92c7a8",
            "runId": "linktable-inner-vlan-pre",
            "hypothesisId": hypothesis_id,
            "location": "telemetry/ssh_provider.py",
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with open("/home/dn/drivenets-topology-studio/.cursor/debug-92c7a8.log", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, separators=(",", ":")) + "\n")
    except Exception:
        pass
# endregion


class SshTelemetryProvider(TelemetryProvider):
    name = "ssh-cli"

    def __init__(self, app_user: str = "default", comm: DeviceCommHelper | None = None):
        self.app_user = app_user or "default"
        self.comm = comm or DeviceCommHelper()

    def available(self, device: CanvasDevice) -> bool:
        return bool(device.device_id or device.label or device.ssh_host)

    def _run_batch(self, device: CanvasDevice, *, force: bool = False) -> dict[str, str]:
        device_id = device.device_id or device.label
        cache_key = "batch:" + "|".join(SHOW_COMMANDS)
        if not force:
            cached = cache.get_cached(self.app_user, device_id, cache_key, ttl=15)
            if isinstance(cached, dict):
                return {str(k): str(v) for k, v in cached.items()}
        out = self.comm.run_show_batch(
            device_id,
            SHOW_COMMANDS,
            ssh_host=device.ssh_host or "",
            timeout=70,
            app_user=self.app_user,
        )
        cache.set_cached(self.app_user, device_id, cache_key, out)
        return out

    def fetch_device(self, device: CanvasDevice, *, force: bool = False) -> DeviceTelemetry:
        warnings: List[str] = []
        outputs = self._run_batch(device, force=force)
        for cmd, text in outputs.items():
            if "ERROR:" in text or "Unknown word" in text or "Incomplete command" in text:
                warnings.append(f"{cmd}: {text.splitlines()[0] if text else 'command failed'}")

        physical, subifs, bundles_from_desc = parse_interfaces_description(
            outputs.get("show interfaces description", "")
        )
        oper_physical, oper_subifs, oper_bundles = parse_interfaces(
            outputs.get("show interfaces", "")
        )
        physical, subifs, bundles_from_desc = merge_interface_facts(
            physical,
            subifs,
            bundles_from_desc,
            oper_physical,
            oper_subifs,
            oper_bundles,
        )
        lldp = parse_lldp_neighbors(outputs.get("show lldp neighbors", ""), device=device.device_id or device.label)
        counters = parse_interfaces_counters(outputs.get("show interfaces counters", ""))
        physical = attach_lldp_to_interfaces(physical, lldp)
        physical = merge_counters(physical, counters)
        bundles = parse_lacp_interfaces(outputs.get("show lacp interfaces", ""), bundles_from_desc)
        primary_config = outputs.get("show config | flatten", "")
        defaults_config = outputs.get("show config defaults interfaces", "")
        if "ERROR:" in defaults_config or "Unknown word" in defaults_config or "Incomplete command" in defaults_config:
            defaults_config = ""
        config_source = "live" if primary_config.strip() and "ERROR:" not in primary_config and "Unknown word" not in primary_config else "none"
        config_text = "\n".join(text for text in (primary_config, defaults_config) if text)
        if _get_cached_config and (not primary_config.strip() or "ERROR:" in primary_config or "Unknown word" in primary_config):
            for key in (device.device_id, device.label, device.ssh_host):
                if not key:
                    continue
                cached_config = _get_cached_config(str(key))
                if cached_config:
                    config_text = cached_config
                    config_source = f"cached:{key}"
                    warnings.append(f"{device.device_id or device.label}: using scaler DB cached running config")
                    break
        cfg = parse_show_config_flatten(config_text)
        bgp_states = parse_bgp_summary(outputs.get("show bgp summary", ""))
        isis_states = parse_isis_neighbors(outputs.get("show isis neighbors", ""))
        ospf_states = parse_ospf_neighbors(outputs.get("show ospf neighbors", ""))
        ldp_states = parse_ldp_neighbors(outputs.get("show ldp neighbors detail", ""))
        self._merge_config_facts(physical, bundles, subifs, cfg, bgp_states, isis_states, ospf_states, ldp_states)
        # region agent log
        _agent_debug_log("H1,H5", "link telemetry provider VLAN rows after config merge", {
            "device": device.device_id or device.label,
            "label": device.label,
            "configSource": config_source,
            "showInterfacesBytes": len(outputs.get("show interfaces", "") or ""),
            "primaryConfigBytes": len(primary_config or ""),
            "defaultsConfigBytes": len(defaults_config or ""),
            "subifs": [
                {
                    "name": row.name,
                    "parent": row.parent,
                    "outer": row.outer_vlan,
                    "inner": row.inner_vlan,
                    "tpid": row.tpid,
                    "ip": row.ip,
                    "mtu": row.mtu,
                    "attachment": getattr(row.attachment, "kind", ""),
                    "service": getattr(row.attachment, "service_name", ""),
                    "egress": row.vlan_manipulation_egress,
                }
                for row in subifs[:80]
            ],
            "bundles": [
                {
                    "name": row.name,
                    "admin": row.admin_state,
                    "oper": row.oper_state,
                    "members": [member.interface for member in (row.members or [])[:12]],
                    "membersConfig": [member.interface for member in (row.members_config or [])[:12]],
                }
                for row in bundles[:40]
            ],
        })
        # endregion
        return DeviceTelemetry(
            physical=physical,
            bundles=bundles,
            subifs=subifs,
            lldp=lldp,
            warnings=warnings,
            provider=self.name,
        )

    def fetch_interfaces(self, device: CanvasDevice, *, ifname: Optional[str] = None) -> List[InterfaceRow]:
        rows = self.fetch_device(device).physical
        if ifname:
            return [r for r in rows if r.name == ifname]
        return rows

    def fetch_bundles(self, device: CanvasDevice) -> List[BundleRow]:
        return self.fetch_device(device).bundles

    def fetch_subinterfaces(self, device: CanvasDevice, *, parent: Optional[str] = None) -> List[SubInterfaceRow]:
        rows = self.fetch_device(device).subifs
        if parent:
            return [r for r in rows if r.parent == parent]
        return rows

    def fetch_lldp(self, device: CanvasDevice) -> List[LldpEdge]:
        return self.fetch_device(device).lldp

    def fetch_counters(self, device: CanvasDevice, ifname: str) -> CounterRow:
        outputs = self._run_batch(device)
        counters = parse_interfaces_counters(outputs.get("show interfaces counters", ""))
        return counters.get(ifname, CounterRow(interface=ifname))

    def _merge_config_facts(
        self,
        physical: List[InterfaceRow],
        bundles: List[BundleRow],
        subifs: List[SubInterfaceRow],
        cfg,
        bgp_states,
        isis_states,
        ospf_states,
        ldp_states,
    ) -> None:
        bundles_by_name = {row.name: row for row in bundles}
        for name, facts in cfg.bundles.items():
            row = bundles_by_name.setdefault(name, BundleRow(name=name))
            if row not in bundles:
                bundles.append(row)
            row.members_config = [
                BundleMemberRow(
                    interface=member.interface,
                    role=member.role,
                    port_state=member.port_state,
                    protocol_state=member.protocol_state,
                    flags=member.flags,
                )
                for member in facts.members
            ]
            row.lacp_mode = facts.lacp_mode or row.lacp_mode or row.mode
            row.lacp_period = facts.lacp_period or row.lacp_period
            row.lacp_system_id = facts.lacp_system_id or row.lacp_system_id
            row.min_links = facts.min_links or row.min_links
            row.admin_state = facts.admin_state or row.admin_state
            row.mtu = facts.mtu or row.mtu

        subifs_by_name = {row.name: row for row in subifs}
        for name, facts in cfg.subifs.items():
            row = subifs_by_name.setdefault(name, SubInterfaceRow(name=name, parent=facts.parent))
            if row not in subifs:
                subifs.append(row)
            has_oper_row = bool(row.raw.get("show_interfaces"))
            row.parent = facts.parent or row.parent
            if not has_oper_row:
                row.outer_vlan = _scalar_vlan(facts.outer_vlan) or row.outer_vlan
                row.inner_vlan = _scalar_vlan(facts.inner_vlan) or row.inner_vlan
                row.tpid = facts.tpid or row.tpid
            else:
                row.outer_vlan = row.outer_vlan or _scalar_vlan(facts.outer_vlan)
                row.inner_vlan = row.inner_vlan or _scalar_vlan(facts.inner_vlan)
                row.tpid = row.tpid or facts.tpid
            row.vlan_manipulation_egress = facts.vlan_manipulation_egress or row.vlan_manipulation_egress
            row.ip = facts.ip or row.ip
            row.mtu = facts.mtu or row.mtu
            row.bridge_domain = facts.bridge_domain or row.bridge_domain
            row.raw["config"] = facts.dict()

        physical_by_name = {row.name: row for row in physical}
        for rows in (physical, bundles, subifs):
            for row in rows:
                name = row.name
                if not getattr(row, "mtu", "") and name in cfg.mtu_by_interface:
                    row.mtu = cfg.mtu_by_interface[name]
                att = cfg.attachments.get(name)
                if att:
                    row.attachment = AttachmentInfo(**att.dict())
                proto = cfg.protocols.get(name)
                if proto:
                    row.protocols = ProtocolInfo(
                        bgp_neighbors=[ProtocolNeighbor(**nbr.dict()) for nbr in proto.bgp_neighbors],
                        isis=proto.isis,
                        ldp=proto.ldp,
                        ospf=proto.ospf,
                    )
                if name in isis_states:
                    row.protocols.isis = isis_states[name]
                if name in ospf_states:
                    row.protocols.ospf = ospf_states[name]
                if row.protocols.ldp and ldp_states:
                    peers = ", ".join(f"{peer} {state}" for peer, state in ldp_states.items())
                    row.protocols.ldp = peers or row.protocols.ldp
                for nbr in row.protocols.bgp_neighbors:
                    live = bgp_states.get(nbr.peer)
                    if live:
                        nbr.state = live.state or nbr.state
                        nbr.afi = live.afi or nbr.afi
                        nbr.remote_as = live.remote_as or nbr.remote_as

        for row in subifs:
            if row.mtu:
                continue
            parent = row.parent or row.name.split(".", 1)[0]
            parent_row = bundles_by_name.get(parent) or physical_by_name.get(parent)
            if parent_row and getattr(parent_row, "mtu", ""):
                row.mtu = parent_row.mtu
