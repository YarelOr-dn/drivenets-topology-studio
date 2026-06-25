"""Parse DNOS ``show config | flatten`` output for live link telemetry.

The telemetry UI needs service attachment facts from configuration, not from
interface descriptions. This parser stays intentionally permissive: each line
is treated independently so one unfamiliar hierarchy does not break the whole
refresh.
"""
from __future__ import annotations

import ipaddress
import re
import shlex
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class ConfigMember(BaseModel):
    interface: str
    role: str = "configured"
    port_state: str = ""
    protocol_state: str = ""
    flags: str = "configured"


class ConfigAttachment(BaseModel):
    kind: str = "none"
    service_name: str = ""
    vrf: str = ""
    rd: str = ""
    rt: str = ""
    evi: str = ""
    bridge_domain: str = ""


class ConfigProtocolNeighbor(BaseModel):
    protocol: str = ""
    peer: str = ""
    state: str = ""
    afi: str = ""
    local_as: str = ""
    remote_as: str = ""


class ConfigProtocol(BaseModel):
    bgp_neighbors: List[ConfigProtocolNeighbor] = Field(default_factory=list)
    isis: str = ""
    ldp: str = ""
    ospf: str = ""


class ConfigBundle(BaseModel):
    name: str
    members: List[ConfigMember] = Field(default_factory=list)
    lacp_mode: str = ""
    lacp_period: str = ""
    lacp_system_id: str = ""
    min_links: str = ""
    admin_state: str = ""
    mtu: str = ""


class ConfigSubInterface(BaseModel):
    name: str
    parent: str = ""
    outer_vlan: str = ""
    inner_vlan: str = ""
    tpid: str = ""
    vlan_manipulation_egress: str = ""
    ip: str = ""
    mtu: str = ""
    vrf: str = ""
    bridge_domain: str = ""
    l2_service: str = ""


class ParsedConfig(BaseModel):
    bundles: Dict[str, ConfigBundle] = Field(default_factory=dict)
    subifs: Dict[str, ConfigSubInterface] = Field(default_factory=dict)
    attachments: Dict[str, ConfigAttachment] = Field(default_factory=dict)
    protocols: Dict[str, ConfigProtocol] = Field(default_factory=dict)
    mtu_by_interface: Dict[str, str] = Field(default_factory=dict)


def _clean(value: Any) -> str:
    return str(value or "").strip().strip('"')


def _tokens(line: str) -> List[str]:
    text = _clean(line)
    if not text or text.startswith(("!", "#")):
        return []
    try:
        return shlex.split(text, posix=True)
    except ValueError:
        return text.split()


def flatten_hierarchical_config(output: str) -> str:
    """Convert cached indented DNOS config into ``show config | flatten``-like lines."""
    stack: List[Tuple[int, str]] = []
    out: List[str] = []
    for raw in (output or "").splitlines():
        if not raw.strip() or raw.lstrip().startswith(("#", "!")):
            if raw.strip() == "!" and stack:
                stack.pop()
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        text = raw.strip()
        if text.startswith(("dnRouter#", "Added:", "Deleted:", "Changed:")):
            continue
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parts = [item for _, item in stack] + [text]
        out.append(" ".join(parts))
        if not text.startswith(("admin-state ", "description ", "ipv4-address ", "ipv6-address ", "member ", "vlan-id ", "inner-vlan ", "second-dot1q ", "mtu ", "encapsulation ")):
            stack.append((indent, text))
    return "\n".join(out)


def _is_interface_name(value: str) -> bool:
    low = value.lower()
    return bool(
        low.startswith(("ge", "xe", "et", "fab", "mgmt", "bundle-", "lo", "irb", "pwhe"))
        or "." in low
    )


def _parent_if(name: str) -> str:
    return name.split(".", 1)[0] if "." in name else name


def _ensure_protocol(parsed: ParsedConfig, ifname: str) -> ConfigProtocol:
    return parsed.protocols.setdefault(ifname, ConfigProtocol())


def _ensure_attachment(parsed: ParsedConfig, ifname: str) -> ConfigAttachment:
    return parsed.attachments.setdefault(ifname, ConfigAttachment())


def _attachment(
    parsed: ParsedConfig,
    ifname: str,
    *,
    kind: str,
    service_name: str = "",
    vrf: str = "",
    bridge_domain: str = "",
    evi: str = "",
    rd: str = "",
    rt: str = "",
) -> None:
    if not ifname:
        return
    att = _ensure_attachment(parsed, ifname)
    att.kind = kind or att.kind
    att.service_name = service_name or att.service_name
    att.vrf = vrf or att.vrf
    att.bridge_domain = bridge_domain or att.bridge_domain
    att.evi = evi or att.evi
    att.rd = rd or att.rd
    att.rt = rt or att.rt


def _ensure_subif(parsed: ParsedConfig, ifname: str) -> ConfigSubInterface:
    sub = parsed.subifs.setdefault(ifname, ConfigSubInterface(name=ifname, parent=_parent_if(ifname)))
    if not sub.parent:
        sub.parent = _parent_if(ifname)
    return sub


def _ensure_bundle(parsed: ParsedConfig, name: str) -> ConfigBundle:
    return parsed.bundles.setdefault(name, ConfigBundle(name=name))


def _bundle_name(bundle_id: str) -> str:
    clean = _clean(bundle_id)
    if not clean:
        return ""
    return clean if clean.startswith("bundle-") else f"bundle-{clean}"


def _add_bundle_member(parsed: ParsedConfig, bundle_name: str, ifname: str) -> None:
    bundle_name = _bundle_name(bundle_name)
    member_if = _clean(ifname)
    if not bundle_name or not member_if:
        return
    bundle = _ensure_bundle(parsed, bundle_name)
    if member_if not in [m.interface for m in bundle.members]:
        bundle.members.append(ConfigMember(interface=member_if))


def _set_vlan_from_name(sub: ConfigSubInterface) -> None:
    if "." not in sub.name:
        return
    suffix = sub.name.split(".", 1)[1]
    parts = [p for p in suffix.split(".") if p.isdigit()]
    if len(parts) >= 2:
        if not sub.outer_vlan:
            sub.outer_vlan = parts[0]
        if not sub.inner_vlan:
            sub.inner_vlan = parts[1]
    elif parts and not sub.outer_vlan:
        sub.outer_vlan = parts[0]


def _parse_interface_line(parsed: ParsedConfig, parts: List[str]) -> None:
    if len(parts) < 3 or parts[0] != "interfaces":
        return
    ifname = parts[1]
    key = parts[2]
    value = parts[3] if len(parts) > 3 else ""

    if ifname.startswith("bundle-") and "." not in ifname:
        bundle = _ensure_bundle(parsed, ifname)
        if key == "member" and len(parts) > 3:
            _add_bundle_member(parsed, ifname, parts[3])
        elif key in ("admin-state", "admin") and value:
            bundle.admin_state = value
        elif key in ("min-links", "minimum-links") and value:
            bundle.min_links = value
        elif key == "mtu" and value:
            bundle.mtu = value
            parsed.mtu_by_interface[ifname] = value
        elif key == "lacp" and len(parts) > 4:
            if parts[3] in ("mode", "activity"):
                bundle.lacp_mode = parts[4]
            elif parts[3] in ("period", "timeout"):
                bundle.lacp_period = parts[4]
            elif parts[3] in ("system-id", "system-mac"):
                bundle.lacp_system_id = parts[4]

    if key == "bundle-id" and value:
        _add_bundle_member(parsed, value, ifname)

    if "." in ifname:
        sub = _ensure_subif(parsed, ifname)
        _set_vlan_from_name(sub)
        if key in ("vlan-id", "outer-vlan", "dot1q", "outer", "outer-tag") and value:
            sub.outer_vlan = value
        elif key in ("inner-vlan", "second-dot1q", "inner", "inner-tag") and value:
            sub.inner_vlan = value
        elif key in ("tpid", "vlan-tpid") and value:
            sub.tpid = value
        elif key in ("vlan-tags", "vlan-tagging"):
            _parse_vlan_tagging(sub, parts[3:])
        elif key in ("ipv4-address", "ipv6-address", "ip-address") and value:
            sub.ip = value
            _attachment(parsed, ifname, kind="plain-l3", service_name=ifname)
        elif key == "encapsulation":
            _parse_encapsulation(sub, parts[3:])
        elif key == "vlan-manipulation":
            _parse_vlan_manipulation(sub, parts[3:])
        elif key == "mtu" and value:
            sub.mtu = value
            parsed.mtu_by_interface[ifname] = value
    elif key == "mtu" and value:
        parsed.mtu_by_interface[ifname] = value


def _parse_encapsulation(sub: ConfigSubInterface, encap_parts: List[str]) -> None:
    for idx, token in enumerate(encap_parts):
        low = token.lower()
        nxt = encap_parts[idx + 1] if idx + 1 < len(encap_parts) else ""
        if low in ("dot1q", "vlan-id", "outer") and nxt:
            sub.outer_vlan = nxt
        elif low in ("second-dot1q", "inner") and nxt:
            sub.inner_vlan = nxt
        elif low in ("tpid", "ethertype") and nxt:
            sub.tpid = nxt


def _parse_vlan_tagging(sub: ConfigSubInterface, tag_parts: List[str]) -> None:
    for idx, token in enumerate(tag_parts):
        low = token.lower()
        nxt = tag_parts[idx + 1] if idx + 1 < len(tag_parts) else ""
        if low in ("outer", "outer-vlan", "outer-tag", "dot1q", "vlan-id") and nxt:
            sub.outer_vlan = nxt
        elif low in ("inner", "inner-vlan", "inner-tag", "second-dot1q") and nxt:
            sub.inner_vlan = nxt
        elif low in ("tpid", "outer-tpid", "ethertype") and nxt:
            sub.tpid = nxt


def _parse_vlan_manipulation(sub: ConfigSubInterface, manip_parts: List[str]) -> None:
    """Parse documented DNOS ``vlan-manipulation egress-mapping action`` syntax."""
    if len(manip_parts) < 3:
        return
    if manip_parts[0] != "egress-mapping" or manip_parts[1] != "action":
        return
    action = manip_parts[2]
    details = [action]
    for idx, token in enumerate(manip_parts[3:]):
        src_idx = idx + 3
        if token in ("outer-tag", "outer-tpid", "inner-tag", "inner-tpid") and src_idx + 1 < len(manip_parts):
            details.append(f"{token} {manip_parts[src_idx + 1]}")
    sub.vlan_manipulation_egress = " ".join(details)


def _parse_network_services(parsed: ParsedConfig, parts: List[str]) -> None:
    if not parts or parts[0] != "network-services":
        return
    if len(parts) >= 5 and parts[1] in ("vrf", "vpn") and parts[3] == "interface":
        vrf, ifname = parts[2], parts[4]
        sub = _ensure_subif(parsed, ifname) if "." in ifname else None
        if sub:
            sub.vrf = vrf
        _attachment(parsed, ifname, kind="l3vpn", service_name=vrf, vrf=vrf)
    if len(parts) >= 5 and parts[1] in ("bridge-domain", "bridge-domains") and parts[3] == "interface":
        bd, ifname = parts[2], parts[4]
        sub = _ensure_subif(parsed, ifname) if "." in ifname else None
        if sub:
            sub.bridge_domain = bd
            sub.l2_service = bd
        _attachment(parsed, ifname, kind="bridge-domain", service_name=bd, bridge_domain=bd)
    if len(parts) >= 5 and parts[1] in ("evpn-vpws", "vpws") and parts[3] == "interface":
        service, ifname = parts[2], parts[4]
        _attachment(parsed, ifname, kind="evpn-vpws", service_name=service)
    if len(parts) >= 6 and parts[1] == "evpn" and parts[2] in ("instance", "vpls"):
        service = parts[3]
        if "interface" in parts:
            idx = parts.index("interface")
            if idx + 1 < len(parts):
                _attachment(parsed, parts[idx + 1], kind="evpn-vpls", service_name=service)
        if "evi" in parts:
            idx = parts.index("evi")
            if idx + 1 < len(parts):
                for att in parsed.attachments.values():
                    if att.service_name == service:
                        att.evi = parts[idx + 1]


def _parse_protocols(parsed: ParsedConfig, parts: List[str]) -> None:
    if not parts or parts[0] != "protocols":
        return
    if len(parts) >= 5 and parts[1] == "isis" and "interface" in parts:
        idx = parts.index("interface")
        if idx + 1 < len(parts):
            _ensure_protocol(parsed, parts[idx + 1]).isis = "configured"
    if len(parts) >= 5 and parts[1] == "ldp" and "interface" in parts:
        idx = parts.index("interface")
        if idx + 1 < len(parts):
            _ensure_protocol(parsed, parts[idx + 1]).ldp = "configured"
    if len(parts) >= 5 and parts[1] == "ospf" and "interface" in parts:
        idx = parts.index("interface")
        if idx + 1 < len(parts):
            _ensure_protocol(parsed, parts[idx + 1]).ospf = "configured"
    if len(parts) >= 5 and parts[1] == "bgp" and "neighbor" in parts:
        nbr_idx = parts.index("neighbor")
        peer = parts[nbr_idx + 1] if nbr_idx + 1 < len(parts) else ""
        remote_as = ""
        if "remote-as" in parts:
            idx = parts.index("remote-as")
            remote_as = parts[idx + 1] if idx + 1 < len(parts) else ""
        if "interface" in parts:
            idx = parts.index("interface")
            if idx + 1 < len(parts):
                proto = _ensure_protocol(parsed, parts[idx + 1])
                if peer and peer not in [n.peer for n in proto.bgp_neighbors]:
                    proto.bgp_neighbors.append(ConfigProtocolNeighbor(
                        protocol="bgp",
                        peer=peer,
                        remote_as=remote_as,
                        state="configured",
                    ))


def parse_show_config_flatten(output: str) -> ParsedConfig:
    """Return structured link facts from ``show config | flatten`` output."""
    parsed = ParsedConfig()
    text = output or ""
    if any(line.startswith("  ") for line in text.splitlines()):
        text = text + "\n" + flatten_hierarchical_config(text)
    for line in text.splitlines():
        text = _clean(line)
        if not text or text.startswith(("dnRouter#", "Added:", "Deleted:", "Changed:")):
            continue
        parts = _tokens(text)
        if not parts:
            continue
        _parse_interface_line(parsed, parts)
        _parse_network_services(parsed, parts)
        _parse_protocols(parsed, parts)
    for sub in parsed.subifs.values():
        _set_vlan_from_name(sub)
    return parsed


def _ip_network(value: str) -> Optional[ipaddress._BaseNetwork]:
    try:
        return ipaddress.ip_interface(value).network
    except ValueError:
        return None


def same_link_subnet(ip_a: str, ip_b: str) -> bool:
    """Return true when two interface addresses are in the same configured subnet."""
    net_a = _ip_network(ip_a)
    net_b = _ip_network(ip_b)
    return bool(net_a and net_b and net_a.version == net_b.version and net_a == net_b)


def parse_bgp_summary(output: str) -> Dict[str, ConfigProtocolNeighbor]:
    """Best-effort parser for ``show bgp summary`` peer state rows."""
    peers: Dict[str, ConfigProtocolNeighbor] = {}
    afi = ""
    for line in (output or "").splitlines():
        text = line.strip()
        if not text:
            continue
        if re.search(r"\b(IPv4|IPv6|L2VPN|VPN)\b", text) and "Unicast" in text or "EVPN" in text:
            afi = text.strip("- ")
            continue
        m = re.match(r"(?P<peer>\d{1,3}(?:\.\d{1,3}){3}|[0-9a-fA-F:]{3,})\s+\d+\s+(?P<as>\d+)\s+.*?\s(?P<state>Established|Active|Idle|Connect|\d+)$", text)
        if not m:
            continue
        peer = m.group("peer")
        peers[peer] = ConfigProtocolNeighbor(
            protocol="bgp",
            peer=peer,
            remote_as=m.group("as"),
            state=m.group("state"),
            afi=afi,
        )
    return peers


def parse_isis_neighbors(output: str) -> Dict[str, str]:
    """Best-effort parser for documented ``show isis neighbors`` output."""
    states: Dict[str, str] = {}
    for line in (output or "").splitlines():
        text = line.strip()
        m = re.match(r"\S+\s+(?P<ifname>\S+)\s+\d+\s+(?P<state>Up|Down|Init)\b", text)
        if m and _is_interface_name(m.group("ifname")):
            states[m.group("ifname")] = m.group("state")
            continue
        m = re.search(r"Interface:\s*(?P<ifname>[^,\s]+),.*State:\s*(?P<state>\S+)", text)
        if m:
            states[m.group("ifname")] = m.group("state")
    return states


def parse_ospf_neighbors(output: str) -> Dict[str, str]:
    """Best-effort parser for documented ``show ospf neighbors`` output."""
    states: Dict[str, str] = {}
    for line in (output or "").splitlines():
        text = line.strip()
        if not text or text.startswith(("Neighbor ID", "Ospf Instance")):
            continue
        m = re.search(r"\s(?P<state>Full|2-Way|Init|Down|Exchange|Loading|ExStart)\s+\S+\s+\S+\s+(?P<ifname>[^:\s]+):", text)
        if m:
            states[m.group("ifname")] = m.group("state")
            continue
        m = re.search(r"via interface\s+(?P<ifname>\S+).*State is\s+(?P<state>\S+)", text)
        if m:
            states[m.group("ifname")] = m.group("state")
    return states


def parse_ldp_neighbors(output: str) -> Dict[str, str]:
    """Best-effort parser for documented ``show ldp neighbors detail`` output."""
    states: Dict[str, str] = {}
    current_peer = ""
    for line in (output or "").splitlines():
        text = line.strip()
        m = re.match(r"Peer LDP Identifier:\s*(?P<peer>\S+)", text)
        if m:
            current_peer = m.group("peer")
            continue
        m = re.match(r"State:\s*(?P<state>\S+)", text)
        if m and current_peer:
            states[current_peer] = m.group("state")
    return states
