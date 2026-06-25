"""Best-effort parsers for DNOS live link telemetry show commands."""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Tuple

from .provider_base import AttachmentInfo, BundleMemberRow, BundleRow, CounterRow, InterfaceRow, LldpEdge, SubInterfaceRow


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _split_table_row(line: str) -> List[str]:
    raw = line.strip()
    if not raw.startswith("|") or not raw.endswith("|"):
        return []
    if set(raw.replace("|", "").replace("+", "").replace("-", "").strip()) == set():
        return []
    cells = [c.strip() for c in raw.strip("|").split("|")]
    if not cells or all(not c for c in cells):
        return []
    if any(set(c.replace("-", "").replace("+", "").strip()) == set() and c for c in cells):
        return []
    return cells


def parse_table(output: str) -> Tuple[List[str], List[Dict[str, str]]]:
    """Parse DNOS pipe tables into dictionaries.

    The DNOS docs use aligned ``| col |`` tables. This parser intentionally
    stays permissive so future versions still produce rows instead of failing
    the entire live-table refresh.
    """
    headers: List[str] = []
    rows: List[Dict[str, str]] = []
    for line in (output or "").splitlines():
        cells = _split_table_row(line)
        if not cells:
            continue
        lowered = [c.lower() for c in cells]
        if not headers and any("interface" in c for c in lowered):
            headers = lowered
            continue
        if headers and len(cells) >= 1:
            row: Dict[str, str] = {}
            for idx, header in enumerate(headers):
                row[header] = cells[idx] if idx < len(cells) else ""
            rows.append(row)
    return headers, rows


def classify_interface(name: str) -> str:
    low = _clean(name).lower()
    if not low:
        return "unknown"
    if low.startswith("bundle-") and "." in low:
        return "bundle-subinterface"
    if low.startswith("bundle-"):
        return "bundle"
    if "." in low:
        return "subinterface"
    if low.startswith(("ge", "xe", "et", "mgmt", "mgmt-", "fab")):
        return "physical"
    return "logical"


def split_subinterface(name: str) -> Tuple[str, str, str]:
    raw = _clean(name)
    if "." not in raw:
        return raw, "", ""
    parent, suffix = raw.split(".", 1)
    parts = [part for part in suffix.split(".") if part]
    outer = parts[0] if parts else ""
    inner = parts[1] if len(parts) > 1 else ""
    return parent, outer, inner


def clean_interface_name(name: str) -> str:
    """Remove DNOS display-only suffixes such as ``(L2)`` from interface names."""
    return re.sub(r"\s+\([^)]*\)\s*$", "", _clean(name))


def parse_vlan_cell(value: str) -> Tuple[str, str]:
    """Parse ``show interfaces`` VLAN cells.

    Examples:
    - ``219`` -> outer 219
    - ``219, 3101(i)`` -> outer 219, inner 3101
    - ``vlan-list`` / empty -> no scalar VLAN stack for Link Table matching
    """
    text = _clean(value)
    if not text or text.lower() in {"list", "range", "vlan-list", "vlan-range"}:
        return "", ""
    parts = [part.strip() for part in text.split(",") if part.strip()]
    if not parts:
        return "", ""
    outer = re.sub(r"\D.*$", "", parts[0]).strip()
    inner = ""
    for part in parts[1:]:
        if "(i)" in part.lower() or re.search(r"\bi\b", part.lower()):
            inner = re.sub(r"\D.*$", "", part).strip()
            break
    return outer, inner


def attachment_from_network_service(value: str) -> AttachmentInfo:
    service = _clean(value)
    match = re.match(r"([A-Za-z0-9_-]+)\s*\(([^)]*)\)", service)
    if not match:
        return AttachmentInfo(kind="none")
    kind = match.group(1).lower()
    name = match.group(2).strip()
    if kind == "vrf":
        if not name or name == "default":
            return AttachmentInfo(kind="plain-l3", service_name=name)
        return AttachmentInfo(kind="l3vpn", service_name=name, vrf=name)
    if kind == "evpn":
        return AttachmentInfo(kind="evpn-vpls", service_name=name)
    if kind in {"bridge-domain", "bd"}:
        return AttachmentInfo(kind="bridge-domain", service_name=name, bridge_domain=name)
    return AttachmentInfo(kind=kind, service_name=name)


def parse_interfaces(output: str) -> Tuple[List[InterfaceRow], List[SubInterfaceRow], List[BundleRow]]:
    """Parse ``show interfaces`` operational rows.

    This table is the source of truth for displayed VLAN stack and operational
    state because DNOS includes translated outer/inner VLANs in the ``VLAN``
    column, while sub-interface names and flattened config can be service labels.
    """
    _, rows = parse_table(output)
    physical: List[InterfaceRow] = []
    subifs: List[SubInterfaceRow] = []
    bundles: Dict[str, BundleRow] = {}
    for row in rows:
        display_name = _clean(row.get("interface") or row.get("interface name"))
        name = clean_interface_name(display_name)
        if not name:
            continue
        admin = _clean(row.get("admin") or row.get("admin-state") or row.get("admin state"))
        oper = _clean(row.get("operational") or row.get("oper") or row.get("oper-state") or row.get("oper state"))
        mtu = _clean(row.get("mtu") or row.get("l2 mtu") or row.get("l3 mtu") or row.get("max frame size"))
        ipv4 = _clean(row.get("ipv4 address") or row.get("ipv4-address"))
        ipv6 = _clean(row.get("ipv6 address") or row.get("ipv6-address"))
        vlan_cell = _clean(row.get("vlan"))
        network_service = _clean(row.get("network-service") or row.get("network service"))
        outer_vlan, inner_vlan = parse_vlan_cell(vlan_cell)
        kind = classify_interface(name)
        raw = {"show_interfaces": dict(row), "display_name": display_name}
        if kind == "bundle":
            bundles[name] = BundleRow(name=name, admin_state=admin, oper_state=oper, mtu=mtu, raw=raw)
        elif kind in ("subinterface", "bundle-subinterface"):
            parent, name_outer, name_inner = split_subinterface(name)
            subifs.append(SubInterfaceRow(
                name=name,
                parent=parent,
                outer_vlan=outer_vlan or name_outer,
                inner_vlan=inner_vlan or name_inner,
                ip=ipv4 or ipv6,
                mtu=mtu,
                admin_state=admin,
                oper_state=oper,
                attachment=attachment_from_network_service(network_service),
                raw=raw,
            ))
        else:
            physical.append(InterfaceRow(
                name=name,
                kind=kind,
                admin_state=admin,
                oper_state=oper,
                mtu=mtu,
                attachment=attachment_from_network_service(network_service),
                raw={**raw, "bundle_id": _clean(row.get("bundle-id") or row.get("bundle id"))},
            ))
    return physical, subifs, list(bundles.values())


def merge_interface_facts(
    base_physical: List[InterfaceRow],
    base_subifs: List[SubInterfaceRow],
    base_bundles: List[BundleRow],
    oper_physical: List[InterfaceRow],
    oper_subifs: List[SubInterfaceRow],
    oper_bundles: List[BundleRow],
) -> Tuple[List[InterfaceRow], List[SubInterfaceRow], List[BundleRow]]:
    physical = {row.name: row for row in base_physical}
    for row in oper_physical:
        current = physical.get(row.name)
        if not current:
            physical[row.name] = row
            continue
        current.admin_state = row.admin_state or current.admin_state
        current.oper_state = row.oper_state or current.oper_state
        current.mtu = row.mtu or current.mtu
        if row.attachment.kind != "none":
            current.attachment = row.attachment
        current.raw.update(row.raw)

    subifs = {row.name: row for row in base_subifs}
    for row in oper_subifs:
        current = subifs.get(row.name)
        if not current:
            subifs[row.name] = row
            continue
        current.parent = row.parent or current.parent
        current.outer_vlan = row.outer_vlan or current.outer_vlan
        current.inner_vlan = row.inner_vlan or current.inner_vlan
        current.ip = row.ip or current.ip
        current.mtu = row.mtu or current.mtu
        current.admin_state = row.admin_state or current.admin_state
        current.oper_state = row.oper_state or current.oper_state
        if row.attachment.kind != "none":
            current.attachment = row.attachment
        current.raw.update(row.raw)

    bundles = {row.name: row for row in base_bundles}
    for row in oper_bundles:
        current = bundles.get(row.name)
        if not current:
            bundles[row.name] = row
            continue
        current.admin_state = row.admin_state or current.admin_state
        current.oper_state = row.oper_state or current.oper_state
        current.mtu = row.mtu or current.mtu
        current.raw.update(row.raw)

    return list(physical.values()), list(subifs.values()), list(bundles.values())


def parse_interfaces_description(output: str) -> Tuple[List[InterfaceRow], List[SubInterfaceRow], List[BundleRow]]:
    _, rows = parse_table(output)
    physical: List[InterfaceRow] = []
    subifs: List[SubInterfaceRow] = []
    bundles: Dict[str, BundleRow] = {}
    for row in rows:
        name = clean_interface_name(row.get("interface") or row.get("interface name"))
        if not name:
            continue
        admin = _clean(row.get("admin") or row.get("admin-state") or row.get("admin state"))
        oper = _clean(row.get("operational") or row.get("oper") or row.get("oper-state") or row.get("oper state"))
        desc = _clean(row.get("description"))
        mtu = _clean(row.get("mtu") or row.get("l2 mtu") or row.get("l3 mtu") or row.get("max frame size"))
        speed = _clean(row.get("speed") or row.get("bandwidth"))
        kind = classify_interface(name)
        if kind == "bundle":
            bundles[name] = BundleRow(name=name, admin_state=admin, oper_state=oper, speed_sum=speed, mtu=mtu, raw={"description": desc, **dict(row)})
        elif kind in ("subinterface", "bundle-subinterface"):
            parent, outer_vlan, inner_vlan = split_subinterface(name)
            subifs.append(SubInterfaceRow(
                name=name,
                parent=parent,
                outer_vlan=outer_vlan,
                inner_vlan=inner_vlan,
                mtu=mtu,
                admin_state=admin,
                oper_state=oper,
                description=desc,
                raw=dict(row),
            ))
        else:
            physical.append(InterfaceRow(
                name=name,
                kind=kind,
                admin_state=admin,
                oper_state=oper,
                description=desc,
                speed=speed,
                mtu=mtu,
                raw=dict(row),
            ))
    return physical, subifs, list(bundles.values())


def parse_lldp_neighbors(output: str, device: str = "") -> List[LldpEdge]:
    _, rows = parse_table(output)
    edges: List[LldpEdge] = []
    for row in rows:
        local = _clean(row.get("interface") or row.get("local interface"))
        peer = _clean(row.get("neighbor system name") or row.get("system name") or row.get("peer"))
        peer_if = _clean(row.get("neighbor interface") or row.get("neighbor port") or row.get("port id"))
        if not local or not peer:
            continue
        edges.append(LldpEdge(
            device=device,
            local_interface=local,
            peer_hostname=peer,
            peer_interface=peer_if,
            evidence=f"show lldp neighbors {local}".strip(),
        ))
    return edges


def attach_lldp_to_interfaces(physical: Iterable[InterfaceRow], edges: Iterable[LldpEdge]) -> List[InterfaceRow]:
    by_if = {edge.local_interface: edge for edge in edges}
    out: List[InterfaceRow] = []
    for row in physical:
        edge = by_if.get(row.name)
        if edge:
            row.lldp_neighbor = edge.peer_hostname
            row.lldp_neighbor_interface = edge.peer_interface
        out.append(row)
    return out


def parse_lacp_interfaces(output: str, existing_bundles: Iterable[BundleRow] = ()) -> List[BundleRow]:
    bundles: Dict[str, BundleRow] = {b.name: b for b in existing_bundles if b.name}
    current = ""
    for line in (output or "").splitlines():
        text = line.strip()
        if not text:
            continue
        m = re.search(r"Aggregate Interface:\s*(\S+)", text, re.I)
        if m:
            current = m.group(1)
            bundles.setdefault(current, BundleRow(name=current))
            continue
        if current:
            mode = re.search(r"\bMode:\s*([^,]+)", text, re.I)
            sysid = re.search(r"System-id:\s*([0-9a-f:.-]+)", text, re.I)
            force = re.search(r"Force-up:\s*(\S+)", text, re.I)
            if mode:
                bundles[current].mode = mode.group(1).strip()
            if sysid:
                bundles[current].lacp_system_id = sysid.group(1).strip()
            if force:
                bundles[current].force_up = force.group(1).strip()
        cells = _split_table_row(line)
        if cells and cells[0].lower() not in ("interface", "--------------") and current and len(cells) >= 3:
            if re.match(r"^(ge|xe|et|fab|mgmt)", cells[0], re.I):
                bundles[current].members.append(BundleMemberRow(
                    interface=cells[0],
                    role=cells[1] if len(cells) > 1 else "",
                    port_state=cells[2] if len(cells) > 2 else "",
                    protocol_state=cells[3] if len(cells) > 3 else "",
                    flags=" ".join(cells[1:4]),
                ))
    return list(bundles.values())


def parse_interfaces_counters(output: str) -> Dict[str, CounterRow]:
    _, rows = parse_table(output)
    counters: Dict[str, CounterRow] = {}
    for row in rows:
        name = _clean(row.get("interface") or row.get("interface name"))
        if not name:
            continue
        counters[name] = CounterRow(
            interface=name,
            rx_packets=_clean(row.get("rx packets") or row.get("in packets") or row.get("rx")),
            tx_packets=_clean(row.get("tx packets") or row.get("out packets") or row.get("tx")),
            rx_errors=_clean(row.get("rx errors") or row.get("input errors")),
            tx_errors=_clean(row.get("tx errors") or row.get("output errors")),
            raw=dict(row),
        )
    return counters


def merge_counters(physical: List[InterfaceRow], counters: Dict[str, CounterRow]) -> List[InterfaceRow]:
    for row in physical:
        ctr = counters.get(row.name)
        if ctr:
            err = []
            if ctr.rx_errors:
                err.append(f"rx {ctr.rx_errors}")
            if ctr.tx_errors:
                err.append(f"tx {ctr.tx_errors}")
            row.errors = ", ".join(err)
            row.raw["counters"] = ctr.dict()
    return physical
