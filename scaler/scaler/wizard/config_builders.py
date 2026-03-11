"""
Pure DNOS config generators. No Rich, no Prompt.ask, no console.print.
Used by both the terminal wizard (interactive_scale) and the GUI API (scaler_bridge).
"""

import re
from typing import Any, Dict, List, Optional


def _is_unusable_ip(ip_int: int, prefix_len: int, is_v6: bool) -> bool:
    """Return True if ip_int is the network or broadcast address for its subnet.
    /31 and /32 (point-to-point, loopback) are exempt per RFC 3021."""
    import ipaddress

    if is_v6 or prefix_len >= 31:
        return False
    try:
        addr = ipaddress.IPv4Address(ip_int)
        net = ipaddress.IPv4Network(f"{addr}/{prefix_len}", strict=False)
        return addr == net.network_address or addr == net.broadcast_address
    except Exception:
        return False


def _calculate_next_ip(
    base_ip: str,
    index: int,
    mode: str,
    prefix_len: int,
    parent_idx: int = 0,
    subif_within_parent: int = 0,
    custom_step: Optional[int] = None,
) -> str:
    """Calculate the next IP address based on stepping mode. Pure function.
    Automatically skips network and broadcast addresses for the given prefix."""
    import ipaddress

    try:
        if "/" in base_ip:
            base_ip = base_ip.split("/")[0]
        if ":" in base_ip:
            ip_int = int(ipaddress.IPv6Address(base_ip))
            is_v6 = True
        else:
            ip_int = int(ipaddress.IPv4Address(base_ip))
            is_v6 = False

        if mode == "per_subif":
            step = custom_step if custom_step is not None else 1
            new_ip_int = ip_int + (index * step)
        elif mode == "per_parent":
            if is_v6:
                new_ip_int = ip_int + (parent_idx * 256) + subif_within_parent
            else:
                base_octets = [
                    (ip_int >> 24) & 0xFF,
                    (ip_int >> 16) & 0xFF,
                    (ip_int >> 8) & 0xFF,
                    ip_int & 0xFF,
                ]
                base_octets[2] = (base_octets[2] + parent_idx) % 256
                base_octets[3] = (base_octets[3] + subif_within_parent) % 256
                new_ip_int = (
                    (base_octets[0] << 24)
                    + (base_octets[1] << 16)
                    + (base_octets[2] << 8)
                    + base_octets[3]
                )
        elif mode == "unique_subnet":
            step = (
                custom_step
                if custom_step is not None
                else (2 ** (128 - prefix_len) if is_v6 else 2 ** (32 - prefix_len))
            )
            new_ip_int = ip_int + (index * step)
        else:
            step = custom_step if custom_step is not None else 1
            new_ip_int = ip_int + (index * step)

        if _is_unusable_ip(new_ip_int, prefix_len, is_v6):
            new_ip_int += 1
            if _is_unusable_ip(new_ip_int, prefix_len, is_v6):
                new_ip_int += 1

        if is_v6:
            return str(ipaddress.IPv6Address(new_ip_int))
        return str(ipaddress.IPv4Address(new_ip_int))
    except Exception:
        return base_ip.split("/")[0] if "/" in base_ip else base_ip


BASIC_TYPES = {"bundle", "ph", "irb"}
PHYSICAL_TYPES = {"ge100", "ge400", "ge10"}


def build_from_expansion(
    parents: List[str],
    subifs_by_parent: Dict[str, List[str]],
    vlan_type: str = "single",
    outer_vlan_start: int = 1,
    outer_vlan_step: int = 1,
    inner_vlan_start: int = 1,
    inner_vlan_step: int = 1,
    configure_ip: bool = False,
    ip_version: Optional[str] = None,
    ip_mode: Optional[str] = None,
    ipv4_start: Optional[str] = None,
    ipv4_prefix: int = 30,
    ipv4_step: int = 1,
    ipv6_start: Optional[str] = None,
    ipv6_prefix: int = 128,
    ipv6_step: int = 1,
) -> tuple:
    """Generate DNOS interface config from pre-expanded parent/sub-if names.

    Called by the terminal wizard's _configure_single_interface_type after
    all prompts are done.  Returns (config_text, created_interfaces_list).
    """
    config_lines: List[str] = ["interfaces"]
    created: List[str] = []

    global_subif_idx = 0
    for parent_idx, parent in enumerate(parents):
        config_lines.append(f"  {parent}")
        config_lines.append("    admin-state enabled")
        config_lines.append("  !")

        parent_subifs = subifs_by_parent.get(parent, [])
        for subif_within_parent, subif in enumerate(parent_subifs):
            config_lines.append(f"  {subif}")
            config_lines.append("    admin-state enabled")

            if vlan_type == "qinq":
                if outer_vlan_step == -1:
                    outer = outer_vlan_start + parent_idx
                elif outer_vlan_step == 0:
                    outer = outer_vlan_start
                else:
                    outer = outer_vlan_start + (global_subif_idx * outer_vlan_step)
                if inner_vlan_step == -2:
                    inner = inner_vlan_start + parent_idx
                else:
                    inner = inner_vlan_start + (subif_within_parent * inner_vlan_step)
                outer = min(max(outer, 1), 4094)
                inner = min(max(inner, 1), 4094)
                config_lines.append(
                    f"    vlan-tags outer-tag {outer} inner-tag {inner} outer-tpid 0x8100"
                )
            else:
                vlan = outer_vlan_start + (global_subif_idx * outer_vlan_step)
                vlan = min(max(vlan, 1), 4094)
                config_lines.append(f"    vlan-id {vlan}")

            if configure_ip:
                if ip_version in ("ipv4", "dual") and ipv4_start:
                    addr = _calculate_next_ip(
                        ipv4_start,
                        global_subif_idx,
                        ip_mode or "per_subif",
                        ipv4_prefix,
                        parent_idx,
                        subif_within_parent,
                        ipv4_step,
                    )
                    config_lines.append(f"    ipv4-address {addr}/{ipv4_prefix}")

                if ip_version in ("ipv6", "dual") and ipv6_start:
                    addr = _calculate_next_ip(
                        ipv6_start,
                        global_subif_idx,
                        ip_mode or "per_subif",
                        ipv6_prefix,
                        parent_idx,
                        subif_within_parent,
                        ipv6_step,
                    )
                    config_lines.append(f"    ipv6-address {addr}/{ipv6_prefix}")

            config_lines.append("  !")
            created.append(subif)
            global_subif_idx += 1

    config_lines.append("!")
    return "\n".join(config_lines), created


def build_interface_config(params: Dict[str, Any]) -> str:
    """Build DNOS interface config from params. Pure function.

    Two modes matching the terminal wizard:
      - Basic (bundle/ph/irb/loopback): parent=admin-state only,
        sub-if=admin-state+vlan+IP.  No l2-service/mpls/flowspec/bfd/mtu.
      - Physical (ge100/ge400/ge10): full E/7 flow with L2 or L3 mode,
        MPLS, flowspec, BFD, MTU on sub-ifs.
    """
    itype = (params.get("interface_type") or "bundle").lower()
    parent_interfaces = params.get("parent_interfaces") or []
    start = int(params.get("start_number", 1))
    count = int(params.get("count", 1))
    if itype == "subif" and parent_interfaces:
        count = len(parent_interfaces)
    slot = int(params.get("slot", 1))
    bay = int(params.get("bay", 0))
    port_start = int(params.get("port_start", 0))
    create_sub = bool(params.get("create_subinterfaces", False))
    if itype == "subif":
        create_sub = True
    vlan_mode = (params.get("vlan_mode") or "single").lower()
    vlan_start = int(params.get("subif_vlan_start", params.get("vlan_start", 100)))
    vlan_step = int(params.get("subif_vlan_step", params.get("vlan_step", 1)))
    outer_vlan_start = int(params.get("outer_vlan_start", vlan_start))
    inner_vlan_start = int(params.get("inner_vlan_start", vlan_start))
    outer_vlan_step = int(params.get("outer_vlan_step", vlan_step))
    inner_vlan_step = int(params.get("inner_vlan_step", vlan_step))
    subif_count = int(params.get("subif_count_per_interface", 1))

    is_basic = itype in BASIC_TYPES
    is_physical = itype in PHYSICAL_TYPES or itype == "subif"

    l2_service = bool(params.get("l2_service", False))
    ip_enabled = bool(params.get("ip_enabled", False))
    ip_version = (params.get("ip_version") or "ipv4").lower()
    ip_start = params.get("ip_start", "10.0.0.1")
    ip_prefix = int(params.get("ip_prefix", 24))
    ip_step = int(params.get("ip_step", 1))
    ip_mode = (params.get("ip_mode") or "per_subif").lower()
    ipv6_start = params.get("ipv6_start", "2001:db8::1")
    ipv6_prefix = int(params.get("ipv6_prefix", 128))
    mpls_enabled = bool(params.get("mpls_enabled", False)) and is_physical
    flowspec_enabled = bool(params.get("flowspec_enabled", False)) and is_physical
    mtu = params.get("mtu") if is_physical else None
    bfd = bool(params.get("bfd", False)) and is_physical
    desc_tpl = params.get("description", "")
    bundle_members = params.get("bundle_members") or []
    lacp_mode = (params.get("lacp_mode") or "active").lower()

    if is_basic:
        l2_service = False

    def _iface_name(i: int) -> str:
        if itype == "subif" and i < len(parent_interfaces):
            return parent_interfaces[i]
        num = start + i
        if itype == "bundle":
            return f"bundle-{num}"
        if itype == "ph":
            return f"ph{num}"
        if itype == "ge400":
            return f"ge400-{slot}/{bay}/{port_start + i}"
        if itype == "ge100":
            return f"ge100-{slot}/{bay}/{port_start + i}"
        if itype == "ge10":
            return f"ge10-{slot}/{bay}/{port_start + i}"
        if itype == "irb":
            return f"irb{num}"
        if itype == "loopback":
            return f"lo{num}" if num > 0 else "lo0"
        return f"bundle-{num}"

    lines: List[str] = ["interfaces"]

    # === LOOPBACK: admin-state + description(optional) + ipv4(optional) ===
    if itype == "loopback":
        for i in range(count):
            name = _iface_name(i)
            lines.append(f"  {name}")
            lines.append("    admin-state enabled")
            if desc_tpl:
                desc = desc_tpl.replace("{i}", str(i + 1))
                lines.append(f'    description "{desc}"')
            if ip_enabled and ip_start:
                base = ip_start.split("/")[0]
                prefix = "/32" if "/" not in ip_start else "/" + ip_start.split("/")[1]
                if "." in base and count > 1 and i > 0:
                    parts = base.split(".")
                    if len(parts) == 4:
                        try:
                            last = int(parts[3]) + i
                            parts[3] = str(last % 256)
                            if last >= 256:
                                parts[2] = str(int(parts[2]) + last // 256)
                            base = ".".join(parts)
                        except ValueError:
                            pass
                addr = f"{base}{prefix}"
                lines.append(f"    ipv4-address {addr}")
            lines.append("  !")
        lines.append("!")
        return "\n".join(lines)

    # === NON-LOOPBACK: parent + optional sub-interfaces ===
    for i in range(count):
        name = _iface_name(i)

        # Parent interface: admin-state only for basic types,
        # full features for physical types
        lines.append(f"  {name}")
        lines.append("    admin-state enabled")
        if is_physical:
            if desc_tpl:
                desc = desc_tpl.replace("{i}", str(i + 1))
                lines.append(f'    description "{desc}"')
            if mtu:
                lines.append(f"    mtu {int(mtu)}")
            if flowspec_enabled:
                lines.append("    flowspec enabled")
            if bfd:
                lines.append("    bfd")
                lines.append("      admin-state enabled")
                bfd_interval = params.get("bfd_interval")
                bfd_multiplier = params.get("bfd_multiplier")
                if bfd_interval is not None and bfd_interval != "":
                    lines.append(f"      interval {int(bfd_interval)}")
                if bfd_multiplier is not None and bfd_multiplier != "":
                    lines.append(f"      multiplier {int(bfd_multiplier)}")
                lines.append("    !")
        lines.append("  !")

        # Sub-interfaces
        if create_sub:
            for j in range(subif_count):
                sub_idx = i * subif_count + j
                vlan = min(max(vlan_start + sub_idx * vlan_step, 1), 4094)

                if outer_vlan_step == -1:
                    outer = outer_vlan_start + i
                elif outer_vlan_step == 0:
                    outer = outer_vlan_start
                else:
                    outer = outer_vlan_start + sub_idx * outer_vlan_step
                outer = min(max(outer, 1), 4094)

                if inner_vlan_step == -2:
                    inner = inner_vlan_start + i
                elif inner_vlan_step == 0:
                    inner = inner_vlan_start
                else:
                    inner = inner_vlan_start + j * inner_vlan_step
                inner = min(max(inner, 1), 4094)
                lines.append(f"  {name}.{vlan}")
                lines.append("    admin-state enabled")
                if vlan_mode == "qinq":
                    lines.append(
                        f"    vlan-tags outer-tag {outer} inner-tag {inner} outer-tpid 0x8100"
                    )
                else:
                    lines.append(f"    vlan-id {vlan}")

                # L2 service: only for physical types in L2 mode
                if l2_service and is_physical:
                    lines.append("    l2-service enabled")

                # IP addressing
                if ip_enabled and not l2_service:
                    ip_idx = sub_idx if ip_mode == "per_subif" else i
                    if ip_version in ("v4", "ipv4", "dual"):
                        v4addr = _calculate_next_ip(
                            ip_start, ip_idx, ip_mode, ip_prefix, i, j, ip_step
                        )
                        lines.append(f"    ipv4-address {v4addr}/{ip_prefix}")
                    if ip_version in ("v6", "ipv6", "dual"):
                        v6addr = _calculate_next_ip(
                            ipv6_start, ip_idx, ip_mode, ipv6_prefix, i, j, ip_step
                        )
                        lines.append(f"    ipv6-address {v6addr}/{ipv6_prefix}")

                # L3 features: only for physical types in L3 mode
                if is_physical and not l2_service:
                    if mpls_enabled:
                        lines.append("    mpls enabled")
                    if flowspec_enabled:
                        lines.append("    flowspec enabled")
                    if mtu:
                        lines.append(f"    mtu {int(mtu)}")
                    if bfd:
                        lines.append("    bfd")
                        lines.append("      admin-state enabled")
                        bfd_interval = params.get("bfd_interval")
                        bfd_multiplier = params.get("bfd_multiplier")
                        if bfd_interval is not None and bfd_interval != "":
                            lines.append(f"      interval {int(bfd_interval)}")
                        if bfd_multiplier is not None and bfd_multiplier != "":
                            lines.append(f"      multiplier {int(bfd_multiplier)}")
                        lines.append("    !")

                lines.append("  !")

    # Bundle member assignment
    if bundle_members and itype == "bundle":
        bundle_num = str(start)
        for m in bundle_members:
            m = str(m).strip()
            if m:
                lines.append(f"  {m}")
                lines.append(f"    bundle-id {bundle_num}")
                lines.append("  !")
    lines.append("!")

    # LACP for bundles
    if bundle_members and itype == "bundle" and lacp_mode in ("active", "passive"):
        lines.append("")
        lines.append("protocols")
        lines.append("  lacp")
        for m in bundle_members:
            m = str(m).strip()
            if m:
                lines.append(f"    interface {m}")
                lines.append(f"      mode {lacp_mode}")
                lines.append("    !")
        lines.append("  !")
        lines.append("!")

    return "\n".join(lines)


def build_service_config(params: Dict[str, Any]) -> str:
    """Build DNOS network-services config. Pure function."""
    svc_type = (params.get("service_type") or "evpn-vpws-fxc").lower()
    prefix = params.get("name_prefix", "FXC_")
    start = int(params.get("start_number", 1))
    count = int(params.get("count", 1))
    evi_start = int(params.get("evi_start", params.get("service_id_start", 1000)))
    rd_base = str(params.get("rd_base", "65000"))
    lines: List[str] = []

    if "vrf" in svc_type:
        try:
            from ..interactive_scale import _generate_vrf_config

            vrf_prefix = prefix.rstrip("_") if prefix.endswith("_") else prefix
            vrf_description = params.get("description", "VRF {n}") or "VRF {n}"
            attach_interfaces = bool(params.get("attach_interfaces", False))
            interface_list = params.get("interface_list", [])
            interfaces_per_vrf = int(params.get("interfaces_per_vrf", 1))
            enable_bgp = bool(params.get("enable_bgp", False))
            bgp_config = params.get("bgp_config", {"as": 65000, "router_id": "10.0.0.1"})
            rt_config = params.get("rt_config", {"mode": "same_as_rd"})
            redistribute_config = params.get("redistribute_config", {})
            vrf_interface_mapping = params.get("vrf_interface_mapping")

            return _generate_vrf_config(
                vrf_count=count,
                vrf_prefix=vrf_prefix,
                vrf_start=start,
                vrf_description=vrf_description,
                attach_interfaces=attach_interfaces,
                interface_list=interface_list,
                interfaces_per_vrf=interfaces_per_vrf,
                enable_bgp=enable_bgp,
                bgp_config=bgp_config,
                rt_config=rt_config,
                redistribute_config=redistribute_config,
                enable_flowspec_on_vrf=bool(params.get("enable_flowspec_on_vrf", False)),
                vrf_neighbors=params.get("vrf_neighbors", []),
                static_routes=params.get("static_routes", []),
                vrf_interface_mapping=vrf_interface_mapping,
            )
        except ImportError:
            pass

    interface_list = params.get("interface_list") or []
    interfaces_per_service = int(params.get("interfaces_per_service", params.get("interfaces_per_vrf", 1)))
    description_tpl = params.get("description", "")
    route_policy_import = params.get("route_policy_import")
    route_policy_export = params.get("route_policy_export")

    subifs = [i for i in interface_list if "." in i] if interface_list else []
    for i in range(count):
        num = start + i
        name = f"{prefix}{num}"
        evi = evi_start + i
        if "evpn-vpws-fxc" in svc_type or "fxc" in svc_type:
            lines.append(f"network-services evpn-vpws-fxc instance {name}")
            lines.append(f"  service-id {evi}")
            lines.append(f"  evi {evi}")
        elif "evpn" in svc_type and "vpls" not in svc_type:
            lines.append(f"network-services evpn instance {name}")
            lines.append(f"  evi {evi}")
        elif "bridge-domain" in svc_type:
            lines.append(f"network-services bridge-domain instance {name}")
            if description_tpl:
                desc = description_tpl.replace("{n}", str(num)).replace("{i}", str(i))
                lines.append(f'  description "{desc}"')
            if subifs and interfaces_per_service > 0:
                idx = i * interfaces_per_service
                for j in range(interfaces_per_service):
                    if idx + j < len(subifs):
                        lines.append(f"  interface {subifs[idx + j]}")
                        lines.append("  !")
            storm_rate = params.get("storm_control_broadcast_rate")
            if storm_rate is not None and int(storm_rate) > 0:
                lines.append("  storm-control")
                lines.append(f"    broadcast-packet-rate {int(storm_rate)}")
                lines.append("  !")
            lines.append("  admin-state enabled")
            lines.append("!")
            continue
        else:
            lines.append(f"network-services evpn-vpws-fxc instance {name}")
            lines.append(f"  service-id {evi}")
            lines.append(f"  evi {evi}")
        if description_tpl:
            desc = description_tpl.replace("{n}", str(num)).replace("{i}", str(i)).replace("{evi}", str(evi))
            lines.append(f'  description "{desc}"')
        if route_policy_import:
            lines.append(f"  route-policy import {route_policy_import}")
        if route_policy_export:
            lines.append(f"  route-policy export {route_policy_export}")
        if subifs and interfaces_per_service > 0:
            idx = i * interfaces_per_service
            for j in range(interfaces_per_service):
                if idx + j < len(subifs):
                    lines.append(f"  interface {subifs[idx + j]}")
                    lines.append("  !")
        lines.append("  admin-state enabled")
        lines.append("!")

    return "\n".join(lines)


def build_bgp_config(params: Dict[str, Any]) -> str:
    """Build DNOS BGP peer config. Pure function."""
    local_as = int(params.get("local_as", 65000))
    peer_ip_start = params.get("peer_ip_start", "10.0.0.1")
    count = int(params.get("count", 1))
    peer_as = int(params.get("peer_as", 65001))
    peer_as_step = int(params.get("peer_as_step", 0))
    peer_ip_step = int(params.get("peer_ip_step", 1))
    peer_group = params.get("peer_group")
    address_families = params.get("address_families", params.get("address_family", ["ipv4-unicast"]))
    if isinstance(address_families, str):
        address_families = [address_families]
    update_source = params.get("update_source")
    route_reflector_client = bool(params.get("route_reflector_client", False))
    hold_time = params.get("hold_time")
    keepalive = params.get("keepalive")
    ebgp_multihop = params.get("ebgp_multihop")
    bfd = bool(params.get("bfd", False))
    description = params.get("description")
    password = params.get("password")

    parts = peer_ip_start.split("/")[0].split(".")
    if len(parts) != 4:
        base_ip = [10, 0, 0, 1]
    else:
        base_ip = [int(p) for p in parts]

    lines = [f"protocols bgp {local_as}"]
    for i in range(count):
        ip = base_ip.copy()
        ip[3] += i * peer_ip_step
        for k in range(3, 0, -1):
            while ip[k] > 255:
                ip[k] -= 256
                ip[k - 1] += 1
        peer_ip_str = ".".join(str(p) for p in ip)
        peer_as_val = peer_as + (i * peer_as_step)
        lines.append(f"  neighbor {peer_ip_str}")
        lines.append(f"    remote-as {peer_as_val}")
        if peer_group:
            lines.append(f"    peer-group {peer_group}")
        lines.append("    admin-state enabled")
        if update_source:
            lines.append(f"    update-source {update_source}")
        if hold_time is not None and hold_time != "":
            lines.append(f"    hold-time {int(hold_time)}")
        if keepalive is not None and keepalive != "":
            lines.append(f"    keepalive {int(keepalive)}")
        if ebgp_multihop is not None and ebgp_multihop != "":
            ttl = int(ebgp_multihop) if ebgp_multihop else 255
            lines.append(f"    ebgp-multihop {ttl}")
        if bfd:
            lines.append("    bfd")
        if description:
            lines.append(f'    description "{description}"')
        if password:
            lines.append(f'    password "{password}"')
        for af in address_families:
            lines.append(f"    address-family {af}")
            if route_reflector_client:
                lines.append("      route-reflector-client")
            lines.append("    !")
        lines.append("  !")
    lines.append("!")
    return "\n".join(lines)


def build_igp_config(params: Dict[str, Any]) -> str:
    """Build DNOS IGP (ISIS/OSPF) config. Pure function."""
    from .igp import ip_to_isis_net

    protocol = (params.get("protocol") or "isis").lower()
    area_id = params.get("area_id", "49.0001")
    router_id = params.get("router_id", params.get("router_ip", "10.0.0.1"))
    interfaces = params.get("interfaces", [])
    level = params.get("level", "level-1-2")
    interface_options = params.get("interface_options") or {}
    passive_for_all = bool(params.get("passive_for_all", False))
    default_metric = params.get("default_metric")

    if protocol == "isis":
        net = ip_to_isis_net(router_id, area_id)
        lines = ["protocols", "  isis", f"    net {net}", "    admin-state enabled"]
        if level and level != "level-1-2":
            lines.append(f"    level {level}")
        for iface in interfaces:
            opts = interface_options.get(iface, {}) if isinstance(interface_options, dict) else {}
            lines.append(f"    interface {iface}")
            lines.append("      admin-state enabled")
            if opts.get("passive") or passive_for_all:
                lines.append("      passive")
            if opts.get("metric") is not None:
                lines.append(f"      metric {int(opts['metric'])}")
            elif default_metric is not None and default_metric != "":
                lines.append(f"      metric {int(default_metric)}")
            if opts.get("circuit_type"):
                lines.append(f"      circuit-type {opts['circuit_type']}")
            lines.append("    !")
        lines.append("  !")
        lines.append("!")
        return "\n".join(lines)

    if protocol == "ospf":
        lines = ["protocols", "  ospf", "    admin-state enabled"]
        if router_id:
            lines.insert(3, f"    router-id {router_id}")
        for iface in interfaces:
            opts = interface_options.get(iface, {}) if isinstance(interface_options, dict) else {}
            lines.append(f"    interface {iface}")
            lines.append(f"      area {area_id}")
            lines.append("      admin-state enabled")
            if opts.get("passive") or passive_for_all:
                lines.append("      passive")
            if opts.get("metric") is not None:
                lines.append(f"      metric {int(opts['metric'])}")
            elif default_metric is not None and default_metric != "":
                lines.append(f"      metric {int(default_metric)}")
            lines.append("    !")
        lines.append("  !")
        lines.append("!")
        return "\n".join(lines)

    return ""


def build_flowspec_config(params: Dict[str, Any]) -> str:
    """Build DNOS FlowSpec local policies config. Pure function.

    Params:
        policy_name: Policy name
        match_classes: List of {name, dest_ip, source_ip?, dest_port?, protocol?, action, rate_bps?}
        include_ipv4: Include IPv4 (default True)
        include_ipv6: Include IPv6 (default False)
        vrf: Optional VRF name to restrict match
    """
    policy_name = params.get("policy_name", "FLOWSPEC-POL")
    match_classes = params.get("match_classes", [])
    include_ipv4 = params.get("include_ipv4", True)
    include_ipv6 = params.get("include_ipv6", False)
    vrf_name = params.get("vrf")

    if not match_classes:
        return ""

    def gen_mc(ip_version: str, indent: str = "    ") -> List[str]:
        lines = [f"{indent}{ip_version}"]
        for mc in match_classes:
            lines.append(f"{indent}  match-class {mc.get('name', 'MC-1')}")
            if vrf_name:
                lines.append(f"{indent}    vrf {vrf_name}")
            if mc.get("dest_ip"):
                lines.append(f"{indent}    dest-ip {mc['dest_ip']}")
            if mc.get("source_ip"):
                lines.append(f"{indent}    source-ip {mc['source_ip']}")
            if not mc.get("dest_ip") and not mc.get("source_ip"):
                lines.append(f"{indent}    dest-ip 0.0.0.0/32")
            if mc.get("dest_port"):
                p = mc["dest_port"]
                lines.append(f"{indent}    dest-port eq {p}" if "-" not in str(p) else f"{indent}    dest-port {p}")
            if mc.get("protocol"):
                lines.append(f"{indent}    protocol eq {mc['protocol']}")
            lines.append(f"{indent}  !")
        lines.append(f"{indent}  policy {policy_name}")
        for mc in match_classes:
            lines.append(f"{indent}    match-class {mc.get('name', 'MC-1')}")
            action = mc.get("action", "drop")
            if action == "drop":
                lines.append(f"{indent}      action-type rate-limit max-rate 0")
            elif action == "rate-limit":
                rate = int(mc.get("rate_bps", 1000000))
                lines.append(f"{indent}      action-type rate-limit max-rate {rate}")
            elif action == "redirect":
                nh = mc.get("redirect_ip", "10.0.0.1")
                lines.append(f"{indent}      action-type redirect-to-ip next-hop {nh}")
            else:
                lines.append(f"{indent}      action-type rate-limit max-rate 0")
            lines.append(f"{indent}    !")
        lines.append(f"{indent}  !")
        lines.append(f"{indent}!")
        return lines

    out = ["routing-policy", "  flowspec-local-policies"]
    if include_ipv4:
        out.extend(gen_mc("ipv4"))
    if include_ipv6:
        out.extend(gen_mc("ipv6"))
    out.append("  !")
    out.append("!")
    out.append("!")
    out.append("forwarding-options")
    out.append("  flowspec-local")
    if include_ipv4:
        out.extend(["    ipv4", f"      apply-policy-to-flowspec {policy_name}", "    !"])
    if include_ipv6:
        out.extend(["    ipv6", f"      apply-policy-to-flowspec {policy_name}", "    !"])
    out.append("  !")
    out.append("!")
    return "\n".join(out)


def build_routing_policy_config(params: Dict[str, Any]) -> str:
    """Build DNOS routing-policy config. Pure function.

    Params:
        type: 'prefix-list' | 'route-policy'
        For prefix-list: name, ip_version (ipv4|ipv6), entries: [{prefix, action: permit|deny, ge?, le?}]
        For route-policy (new syntax SW-181332): name, body (one-liner quoted string)
    """
    ptype = (params.get("type") or "prefix-list").lower()
    if ptype == "prefix-list":
        name = params.get("name", "PL-1")
        ip_version = params.get("ip_version", "ipv4")
        entries = params.get("entries", [])
        if not entries:
            entries = [{"prefix": "0.0.0.0/0", "action": "deny"}]
        lines = ["routing-policy", f"  prefix-list {ip_version} {name}"]
        for i, e in enumerate(entries, start=10):
            prefix = e.get("prefix", "0.0.0.0/0")
            action = e.get("action", "deny")
            ge = e.get("ge")
            le = e.get("le")
            rule = f"    rule {i} {action} {prefix}"
            if ge is not None:
                rule += f" ge {int(ge)}"
            if le is not None:
                rule += f" le {int(le)}"
            lines.append(rule)
        lines.append("  !")
        lines.append("!")
        return "\n".join(lines)
    if ptype == "route-policy":
        name = params.get("name", "POL-1")
        body = params.get("body", f'route-policy {name}() {{ return deny }}')
        if "route-policy " not in body and "()" not in body:
            body = f"route-policy {name}() {{ {body} }}"
        lines = ["routing-policy", f'  route-policy {name} "{body}"', "!", "!"]
        return "\n".join(lines)
    return ""
