"""Preview-only topology import planning MCP tools."""

from __future__ import annotations

import hashlib
import math
from typing import Any, Dict, Iterable, List, Optional

from mcp.access import save_topology_for
from mcp.tools.validation import topology_validate_topology


def _slug(value: Any, prefix: str) -> str:
    text = str(value or "").strip()
    if not text:
        text = prefix
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in text).strip("-")
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    if not cleaned:
        cleaned = prefix
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:6]
    return f"{cleaned[:42]}-{digest}"


def _first(row: Dict[str, Any], keys: Iterable[str], default: Any = "") -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return default


def _style_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Merge a nested style block with top-level fields.

    Image extraction payloads often carry visual details either as flat keys
    (`color`, `visualStyle`) or under a nested `style` / `styles` dictionary.
    Top-level fields win so callers can override one style attribute without
    rebuilding the whole nested block.
    """
    merged: Dict[str, Any] = {}
    for key in ("style", "styles", "visual"):
        value = row.get(key)
        if isinstance(value, dict):
            merged.update(value)
    for key, value in row.items():
        if key in ("style", "styles", "visual") and isinstance(value, dict):
            continue
        merged[key] = value
    return merged


def _as_float(value: Any, default: float) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _image_device_style(row: Dict[str, Any]) -> str:
    explicit = str(_first(row, ("visualStyle", "visual_style", "deviceStyle", "device_style", "canvasStyle"), "")).strip()
    if explicit:
        alias = explicit.lower().replace("_", "-")
        aliases = {
            "router": "classic",
            "cylinder": "classic",
            "classic-router": "classic",
            "tower": "server",
            "server-tower": "server",
            "hexagon": "hex",
        }
        return aliases.get(alias, alias)
    role = str(_first(row, ("role", "deviceType", "device_type", "type", "platform", "kind"), "")).lower()
    if any(token in role for token in ("ce", "host", "server", "client", "endpoint", "spirent")):
        return "server"
    if any(token in role for token in ("switch", "leaf", "spine", "fabric")):
        return "hex"
    if role in ("p", "p-router") or any(token in role for token in ("router", "pe", "rr", "ncp")):
        return "classic"
    return "circle"


def _extract_devices(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = payload.get("devices") or payload.get("nodes") or payload.get("hosts") or []
    if isinstance(raw, dict):
        raw = [{"id": key, **(value if isinstance(value, dict) else {"label": value})} for key, value in raw.items()]
    devices = []
    for index, row in enumerate(raw if isinstance(raw, list) else []):
        if not isinstance(row, dict):
            continue
        styled = _style_row(row)
        label = str(_first(row, ("label", "name", "hostname", "device_name", "deviceName", "id"), f"Device-{index + 1}"))
        object_id = str(_first(row, ("id", "device_id", "deviceId", "hostname", "name"), label))
        device = {
            "id": _slug(object_id, f"dev-{index + 1}"),
            "_source_id": object_id,
            "type": "device",
            "label": label,
            "hostname": str(_first(row, ("hostname", "name", "label"), label)),
            "deviceType": str(_first(row, ("deviceType", "device_type", "role", "type", "platform"), "router")),
            "role": str(_first(row, ("role", "tier", "kind"), "")),
            "site": str(_first(row, ("site", "location", "domain"), "")),
            "x": float((row.get("position") or {}).get("x") or row.get("x") or 0),
            "y": float((row.get("position") or {}).get("y") or row.get("y") or 0),
            "visualStyle": _image_device_style(styled),
            "color": str(_first(styled, ("color", "fillColor", "fill", "accentColor"), "#3498db")),
            "radius": _as_float(_first(styled, ("radius", "size"), 40), 40),
            "rotation": _as_float(_first(styled, ("rotation", "angle"), 0), 0),
            "labelColor": str(_first(styled, ("labelColor", "textColor", "fontColor"), "#ffffff")),
        }
        optional_device_fields = {
            "labelSize": ("labelSize", "fontSize", "font_size"),
            "fontFamily": ("fontFamily", "font_family"),
            "fontWeight": ("fontWeight", "font_weight"),
            "labelOutlineColor": ("labelOutlineColor", "outlineColor"),
            "layer": ("layer", "canvasLayer"),
        }
        for field, keys in optional_device_fields.items():
            value = _first(styled, keys, "")
            if value not in (None, ""):
                device[field] = _as_float(value, 0) if field == "labelSize" else value
        devices.append(device)
    return devices


def _extract_links(payload: Dict[str, Any], id_map: Dict[str, str]) -> tuple[List[Dict[str, Any]], List[str]]:
    raw = payload.get("links") or payload.get("edges") or payload.get("physicalLinks") or []
    raw = list(raw if isinstance(raw, list) else [])
    raw.extend(payload.get("logicalLinks") or [])
    links = []
    warnings = []
    for index, row in enumerate(raw):
        if not isinstance(row, dict):
            continue
        styled = _style_row(row)
        source_raw = _first(row, ("source", "device1", "from", "fromDevice", "src", "local_device", "localDevice"), "")
        target_raw = _first(row, ("target", "device2", "to", "toDevice", "dst", "remote_device", "remoteDevice"), "")
        source = id_map.get(str(source_raw)) or id_map.get(_slug(source_raw, "dev"))
        target = id_map.get(str(target_raw)) or id_map.get(_slug(target_raw, "dev"))
        if not source or not target:
            warnings.append(f"Skipped link {index + 1}: missing endpoint {source_raw!r}->{target_raw!r}")
            continue
        link_id = _slug(_first(row, ("id", "link_id", "name"), f"{source}-{target}-{index}"), f"link-{index + 1}")
        link = {
            "id": link_id,
            "type": "link",
            "source": source,
            "target": target,
            "device1": source,
            "device2": target,
            "label": str(_first(row, ("label", "name", "protocol", "linkType", "layer"), "")),
            "layer": str(_first(row, ("layer", "linkLayer"), "physical")),
            "protocol": str(_first(row, ("protocol", "linkType", "type"), "")),
            "bd": str(_first(row, ("bd", "bridgeDomain", "bridge_domain"), "")),
            "vrf": str(_first(row, ("vrf", "networkService", "service"), "")),
            "fromInterface": str(_first(row, ("fromInterface", "local_interface", "localInterface", "srcInterface"), "")),
            "toInterface": str(_first(row, ("toInterface", "remote_interface", "remoteInterface", "dstInterface"), "")),
            "color": str(_first(styled, ("color", "strokeColor", "lineColor"), "#666666")),
            "width": _as_float(_first(styled, ("width", "strokeWidth", "lineWidth"), 2), 2),
            "style": str(_first(styled, ("style", "lineStyle", "linkStyle"), "solid")),
        }
        for field, keys in {
            "curveOverride": ("curveOverride", "curved"),
            "description": ("description", "note"),
        }.items():
            value = _first(styled, keys, "")
            if value not in (None, ""):
                link[field] = value
        links.append(link)
    return links, warnings


def _color_for_id(value: str, default: str = "#00B4D8") -> str:
    text = str(value or "").strip()
    if not text:
        return default
    return "#" + hashlib.sha1(text.encode("utf-8")).hexdigest()[:6]


def _extract_shapes(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = payload.get("shapes") or payload.get("panels") or []
    shapes: List[Dict[str, Any]] = []
    for index, row in enumerate(raw if isinstance(raw, list) else []):
        if not isinstance(row, dict):
            continue
        bounds = row.get("bounds") if isinstance(row.get("bounds"), dict) else {}
        label = str(_first(row, ("label", "name", "title"), ""))
        shape_id = _slug(_first(row, ("id", "shape_id", "name", "label"), f"shape-{index + 1}"), f"shape-{index + 1}")
        fill = str(_first(row, ("fillColor", "fill", "color"), "#1f77b4"))
        shapes.append({
            "id": shape_id,
            "type": "shape",
            "shapeType": str(_first(row, ("shapeType", "shape_type", "kind"), "rectangle")),
            "x": float(bounds.get("x") or row.get("x") or 0),
            "y": float(bounds.get("y") or row.get("y") or 0),
            "width": float(bounds.get("width") or row.get("width") or 220),
            "height": float(bounds.get("height") or row.get("height") or 120),
            "fillColor": fill,
            "fillOpacity": float(_first(row, ("fillOpacity", "opacity"), 0.12)),
            "fillEnabled": bool(_first(row, ("fillEnabled",), True)),
            "strokeColor": str(_first(row, ("strokeColor", "borderColor", "color"), fill)),
            "strokeWidth": float(_first(row, ("strokeWidth",), 1.4)),
            "strokeEnabled": bool(_first(row, ("strokeEnabled",), True)),
            "cornerRadius": float(_first(row, ("cornerRadius",), 24)),
            "rotation": float(_first(row, ("rotation",), 0)),
            "label": label,
            "locked": bool(_first(row, ("locked",), False)),
        })
    return shapes


def _extract_texts(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = payload.get("texts") or payload.get("annotations") or payload.get("labels") or []
    texts: List[Dict[str, Any]] = []
    for index, row in enumerate(raw if isinstance(raw, list) else []):
        if not isinstance(row, dict):
            continue
        body = str(_first(row, ("text", "label", "content", "title"), "")).strip()
        if not body:
            continue
        text_id = _slug(_first(row, ("id", "text_id", "name", "label"), f"text-{index + 1}"), f"text-{index + 1}")
        texts.append({
            "id": text_id,
            "type": "text",
            "x": float(row.get("x") or 0),
            "y": float(row.get("y") or 0),
            "text": body,
            "fontSize": float(_first(row, ("fontSize", "font_size"), 13)),
            "fontWeight": str(_first(row, ("fontWeight", "font_weight"), "700")),
            "color": str(_first(row, ("color",), "#e2e8f0")),
            "showBackground": bool(_first(row, ("showBackground", "show_background"), True)),
            "backgroundColor": str(_first(row, ("backgroundColor", "background_color"), "rgba(17, 25, 40, 0.86)")),
            "backgroundOpacity": float(_first(row, ("backgroundOpacity", "background_opacity"), 0.9)),
            "backgroundPadding": float(_first(row, ("backgroundPadding", "background_padding"), 6)),
            "borderRadius": float(_first(row, ("borderRadius", "border_radius"), 6)),
            "locked": bool(_first(row, ("locked",), False)),
        })
    return texts


def _resolve_member_id(member: Any, id_map: Dict[str, str]) -> str:
    if isinstance(member, dict):
        raw = _first(member, ("id", "label", "name", "hostname", "device", "object"), "")
    else:
        raw = member
    raw_text = str(raw or "")
    return id_map.get(raw_text) or id_map.get(_slug(raw_text, "obj")) or ""


def _extract_explicit_groups(
    payload: Dict[str, Any],
    objects: List[Dict[str, Any]],
    id_map: Dict[str, str],
) -> List[Dict[str, Any]]:
    raw = payload.get("groups") or payload.get("clusters") or []
    by_id = {str(obj.get("id")): obj for obj in objects if isinstance(obj, dict) and obj.get("id")}
    groups: List[Dict[str, Any]] = []
    for index, row in enumerate(raw if isinstance(raw, list) else []):
        if not isinstance(row, dict):
            continue
        name = str(_first(row, ("name", "label", "title"), f"Group {index + 1}"))
        group_id = _slug(_first(row, ("id", "group_id", "name", "label"), name), f"group-{index + 1}")
        members = []
        for member in row.get("members") or row.get("objects") or row.get("devices") or []:
            resolved = _resolve_member_id(member, id_map)
            if resolved and resolved in by_id and resolved not in members:
                members.append(resolved)
        if not members:
            continue
        color = str(_first(row, ("color", "fillColor", "strokeColor"), _color_for_id(group_id)))
        leader_id = _resolve_member_id(_first(row, ("leader_id", "leader", "leaderId"), ""), id_map) or members[0]
        if leader_id not in members:
            leader_id = members[0]
        for member_id in members:
            obj = by_id.get(member_id)
            if not obj:
                continue
            obj["groupId"] = group_id
            obj["groupLeaderId"] = leader_id
            obj["groupName"] = name
            obj["groupColor"] = color
        groups.append({"id": group_id, "name": name, "members": members, "color": color, "leader_id": leader_id})
    return groups


def _apply_clean_layout(objects: List[Dict[str, Any]], group_by: str = "role") -> None:
    devices = [obj for obj in objects if obj.get("type") == "device"]
    if not devices:
        return
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for obj in sorted(devices, key=lambda item: str(item.get("label") or item.get("id"))):
        key = str(obj.get(group_by) or obj.get("role") or obj.get("deviceType") or "devices")
        buckets.setdefault(key, []).append(obj)
    role_order = {
        "spine": 0,
        "superspine": 0,
        "super-spine": 0,
        "leaf": 1,
        "border": 1,
        "pe": 2,
        "rr": 2,
        "ce": 3,
        "router": 4,
        "devices": 5,
    }
    row_y = 140
    for bucket_name, bucket in sorted(buckets.items(), key=lambda item: (role_order.get(item[0].lower(), 9), item[0].lower())):
        count = len(bucket)
        spacing = 220 if count < 6 else 170
        per_row = 6 if count < 13 else 8
        row_width = (min(count, per_row) - 1) * spacing
        start_x = 620 - row_width / 2
        for index, obj in enumerate(bucket):
            obj["x"] = start_x + (index % per_row) * spacing
            obj["y"] = row_y + math.floor(index / per_row) * 150
            obj["_layoutBucket"] = bucket_name
        row_y += 210 + math.floor((count - 1) / per_row) * 150


def _auto_groups(objects: List[Dict[str, Any]], field: str) -> List[Dict[str, Any]]:
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for obj in objects:
        if obj.get("type") != "device":
            continue
        value = obj.get(field) or obj.get("role") or obj.get("site") or obj.get("deviceType")
        if value:
            buckets.setdefault(str(value), []).append(obj)
    groups = []
    for value, members in sorted(buckets.items()):
        if len(members) < 2:
            continue
        group_id = _slug(f"{field}-{value}", "group")
        color = "#" + hashlib.sha1(group_id.encode("utf-8")).hexdigest()[:6]
        leader = sorted(members, key=lambda obj: (-float(obj.get("x") or 0), float(obj.get("y") or 0)))[0]
        for obj in members:
            obj["groupId"] = group_id
            obj["groupLeaderId"] = leader["id"]
            obj["groupOffsetX"] = float(obj.get("x") or 0) - float(leader.get("x") or 0)
            obj["groupOffsetY"] = float(obj.get("y") or 0) - float(leader.get("y") or 0)
            obj["groupName"] = f"{field}:{value}"
            obj["groupColor"] = color
        groups.append({"id": group_id, "name": f"{field}:{value}", "members": [obj["id"] for obj in members], "color": color})
    return groups


def _link_endpoints(link: Dict[str, Any]) -> tuple[str, str]:
    return str(link.get("device1") or link.get("source") or ""), str(link.get("device2") or link.get("target") or "")


def _attach_links_to_endpoint_groups(objects: List[Dict[str, Any]], groups: List[Dict[str, Any]]) -> None:
    by_id = {str(obj.get("id")): obj for obj in objects if isinstance(obj, dict) and obj.get("id")}
    group_by_id = {str(group.get("id")): group for group in groups if isinstance(group, dict) and group.get("id")}
    for link in objects:
        if not isinstance(link, dict) or link.get("type") != "link":
            continue
        source_id, target_id = _link_endpoints(link)
        source = by_id.get(source_id)
        target = by_id.get(target_id)
        source_group = source.get("groupId") if source else None
        target_group = target.get("groupId") if target else None
        if source_group and source_group == target_group:
            group_id = str(source_group)
            group = group_by_id.get(group_id)
            if not group:
                continue
            leader_id = str(group.get("leader_id") or (group.get("members") or [source_id])[0])
            leader = by_id.get(leader_id) or source
            link["groupId"] = group_id
            link["groupLeaderId"] = leader_id
            link["groupName"] = group.get("name") or group_id
            link["groupColor"] = group.get("color") or "#00B4D8"
            link["groupOffsetX"] = float(link.get("x") or 0) - float((leader or {}).get("x") or 0)
            link["groupOffsetY"] = float(link.get("y") or 0) - float((leader or {}).get("y") or 0)
            members = group.setdefault("members", [])
            if str(link.get("id")) not in members:
                members.append(str(link.get("id")))


def _generated_protocol_groups(objects: List[Dict[str, Any]], base_groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    generated = list(base_groups)
    buckets: Dict[str, Dict[str, Any]] = {}
    for link in objects:
        if not isinstance(link, dict) or link.get("type") != "link":
            continue
        for kind, prefix, value in (
            ("protocol", "protocol", link.get("protocol") or link.get("label")),
            ("service", "bd", link.get("bd")),
            ("service", "vrf", link.get("vrf")),
        ):
            if not value:
                continue
            group_id = _slug(f"{prefix}-{value}", prefix)
            item = buckets.setdefault(
                group_id,
                {
                    "id": group_id,
                    "label": f"{prefix.upper()} {value}" if prefix in {"bd", "vrf"} else str(value),
                    "kind": kind,
                    "layer": "service" if kind == "service" else str(link.get("layer") or "physical"),
                    "members": [],
                    "color": "#" + hashlib.sha1(group_id.encode("utf-8")).hexdigest()[:6],
                },
            )
            item["members"].append(str(link.get("id")))
            link_groups = link.setdefault("_generatedGroupIds", [])
            if group_id not in link_groups:
                link_groups.append(group_id)
    generated.extend(buckets.values())
    return generated


def _attach_packets_to_links(objects: List[Dict[str, Any]]) -> int:
    """Auto-emit one layered packet chip per link that carries protocol metadata.

    A link is considered "interesting enough to deserve a packet" when it has
    any of: protocol, vrf, bd, fromInterface/toInterface, or a non-empty label
    that looks like a service name. The packet rows are filled from those
    fields and rows with no data are pre-collapsed (visible=false) so the
    chip stays compact. Operators can toggle layers back on via the popup.

    Returns the count of packets that were appended to ``objects``.
    """

    def _layer(layer_id: str, label: str, text: str, color: str) -> Dict[str, Any]:
        body = (text or "").strip()
        return {
            "id": layer_id,
            "label": label,
            "text": body,
            "color": color,
            "visible": bool(body),
        }

    def _norm_name(value: Any) -> str:
        return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())

    def _packet_summary(protocol: str, label: str, vrf: str, bd: str) -> str:
        text = f"{protocol} {label} {vrf} {bd}".lower()
        if "flowspec" in text or "flow spec" in text:
            return "FLOWSPEC"
        if "evpn" in text and ("rt-2" in text or "rt2" in text or "mac" in text):
            return "EVPN RT-2"
        if "vpls-pw" in text or "vpls pw" in text or "vpws" in text:
            return "VPLS PW"
        if "bgp" in text or "ibgp" in text or "ebgp" in text:
            return "BGP UPD"
        if vrf:
            return "VRF FLOW"
        return "FRAME"

    def _packet_direction(link: Dict[str, Any]) -> str:
        src_hint = _norm_name(
            link.get("src_device") or link.get("source_device") or
            link.get("from_device") or link.get("fromDevice")
        )
        dst_hint = _norm_name(
            link.get("dst_device") or link.get("target_device") or
            link.get("to_device") or link.get("toDevice")
        )
        d1_names = {_norm_name(link.get(k)) for k in ("device1", "source", "from")}
        d2_names = {_norm_name(link.get(k)) for k in ("device2", "target", "to")}
        if src_hint or dst_hint:
            if (src_hint and src_hint in d1_names) or (dst_hint and dst_hint in d2_names):
                return "forward"
            if (src_hint and src_hint in d2_names) or (dst_hint and dst_hint in d1_names):
                return "backward"
        return "forward"

    packet_idx = 0
    for obj in list(objects):
        if not isinstance(obj, dict):
            continue
        if obj.get("type") not in ("link", "unbound"):
            continue
        protocol = (obj.get("protocol") or "").strip()
        bd = (obj.get("bd") or "").strip()
        vrf = (obj.get("vrf") or "").strip()
        from_if = (obj.get("fromInterface") or "").strip()
        to_if = (obj.get("toInterface") or "").strip()
        label = (obj.get("label") or "").strip()
        if not (protocol or bd or vrf or from_if or to_if or label):
            continue
        # Compose layer rows.
        l2_text = ""
        if from_if or to_if:
            l2_text = f"{from_if or '?'} -> {to_if or '?'}"
        vlan_text = bd if bd else ""
        mpls_text = ""
        if vrf:
            mpls_text = f"vrf {vrf}"
        l3_text = ""
        l4_text = protocol if protocol else ""
        payload_text = label if (label and label != protocol) else ""
        packet = {
            "id": f"packet_{packet_idx}",
            "type": "packet",
            "linkId": obj.get("id"),
            "linkAttachT": 0.5,
            "x": 0,
            "y": 0,
            "title": (label or protocol or "Frame")[:40] or "Frame",
            "summary": _packet_summary(protocol, label, vrf, bd),
            "direction": _packet_direction(obj),
            "collapsed": False,
            "layers": [
                _layer("L2", "L2", l2_text, "#5dade2"),
                _layer("VLAN", "VLAN", vlan_text, "#48c9b0"),
                _layer("MPLS", "MPLS", mpls_text, "#bb8fce"),
                _layer("L3", "L3", l3_text, "#f5b041"),
                _layer("L4", "L4", l4_text, "#e59866"),
                _layer("PAYLOAD", "Payload", payload_text, "#85c1e9"),
            ],
            "locked": False,
        }
        objects.append(packet)
        packet_idx += 1
    return packet_idx


def _build_plan(
    payload: Dict[str, Any],
    *,
    source: str,
    name: str,
    auto_group_by: str = "",
    auto_layout: bool = True,
    attach_packets: bool = False,
) -> Dict[str, Any]:
    devices = _extract_devices(payload)
    id_map = {str(device.get("_source_id")): device["id"] for device in devices}
    for device in devices:
        for key in ("id", "label", "hostname"):
            value = device.get(key)
            if value not in (None, ""):
                id_map[str(value)] = device["id"]
    links, warnings = _extract_links(payload, id_map)
    extra_objects = _extract_shapes(payload) + _extract_texts(payload)
    for obj in extra_objects:
        if obj.get("id"):
            id_map[str(obj["id"])] = str(obj["id"])
        if obj.get("label"):
            id_map[str(obj["label"])] = str(obj["id"])
        if obj.get("text"):
            id_map[str(obj["text"])] = str(obj["id"])
    objects = [{k: v for k, v in device.items() if not k.startswith("_")} for device in devices] + links + extra_objects
    # Network Mapper / DNOS imports always run the deterministic grouped row
    # layout because their JSON rarely carries usable canvas coordinates.
    # Image extractions read positions straight from the diagram, so the
    # caller can pass auto_layout=False to keep what the agent saw.
    if auto_layout:
        _apply_clean_layout(objects, group_by=auto_group_by or "role")
    groups = _extract_explicit_groups(payload, objects, id_map)
    if auto_group_by:
        groups.extend(_auto_groups(objects, auto_group_by))
    _attach_links_to_endpoint_groups(objects, groups)
    generated_groups = _generated_protocol_groups(objects, groups)
    packet_count = 0
    if attach_packets:
        packet_count = _attach_packets_to_links(objects)
    state: Dict[str, Any] = {
        "version": "1.0",
        "objects": objects,
        "metadata": {
            "name": name or "Imported Topology",
            "generatedBy": "topology-mcp",
            "importSource": source,
            "generatedProtocolGroups": generated_groups,
        },
    }
    if packet_count:
        state["metadata"]["packetIdCounter"] = packet_count
        state["metadata"]["autoPackets"] = True
    validation = topology_validate_topology("", state_json=state)
    return {
        "ok": True,
        "dry_run": True,
        "plan": {
            "version": 1,
            "name": name or "Imported Topology",
            "source": source,
            "state": state,
            "summary": validation.get("summary") or {},
            "warnings": warnings,
            "validation": {"valid": validation.get("valid"), "issues": validation.get("issues") or []},
        },
    }


def topology_plan_from_network_mapper(
    username: str,
    network_mapper_json: Dict[str, Any],
    name: str = "Network Mapper Import",
    auto_group_by: str = "role",
    attach_packets: bool = False,
) -> Dict[str, Any]:
    """Build a preview plan from already-fetched Network Mapper JSON without saving it.

    Pass ``attach_packets=True`` to auto-emit one layered packet/frame chip per
    link that carries protocol/vrf/bd metadata. The chip starts compact (rows
    with no data are pre-collapsed); operators can toggle layers via the
    in-canvas packet popup.
    """
    return _build_plan(
        network_mapper_json or {},
        source="network-mapper-json",
        name=name,
        auto_group_by=auto_group_by,
        attach_packets=attach_packets,
    )


def topology_plan_from_dnos_json(
    username: str,
    dnos_json: Dict[str, Any],
    name: str = "DNOS Import",
    auto_group_by: str = "role",
    attach_packets: bool = False,
) -> Dict[str, Any]:
    """Build a preview plan from already-fetched DNOS/dnos-config JSON without saving it.

    Pass ``attach_packets=True`` to auto-emit one layered packet chip per hop
    link, surfacing the DNAAS protocol/VRF/BD context above each hop. Useful
    when the import shows a path discovered by ``dnos_dnaas_path`` /
    ``dnos_dnaas_inverse_path`` and the operator wants the encap stack
    visualized inline.
    """
    payload = dict(dnos_json or {})
    if "hops" in payload and "devices" not in payload:
        devices = []
        links = []
        prior = None
        for index, hop in enumerate(payload.get("hops") or []):
            if not isinstance(hop, dict):
                continue
            host = _first(hop, ("device", "hostname", "node", "leaf", "name"), f"hop-{index + 1}")
            devices.append({"id": host, "hostname": host, "role": _first(hop, ("role", "type"), "dnaas-hop")})
            if prior:
                links.append({"fromDevice": prior, "toDevice": host, "protocol": "DNAAS"})
            prior = host
        payload = {"devices": devices, "links": links}
    return _build_plan(
        payload,
        source="dnos-json",
        name=name,
        auto_group_by=auto_group_by,
        attach_packets=attach_packets,
    )


def topology_plan_from_image(
    username: str,
    image_extraction_json: Dict[str, Any],
    name: str = "Image Import",
    auto_group_by: str = "",
    auto_layout: bool = False,
    attach_packets: bool = False,
) -> Dict[str, Any]:
    """Preview a topology that the agent extracted from an image attached in chat.

    The MCP server itself does NOT see the image. Image parsing is the agent's
    responsibility: read the diagram with vision, then emit a payload in the
    standard import shape:

        {
          "devices": [
            {"label": "PE-1",  "deviceType": "PE",  "role": "PE",  "x": 120, "y": 200},
            {"label": "PE-2",  "deviceType": "PE",  "role": "PE",  "x": 400, "y": 200},
            {"label": "P-1",   "deviceType": "P",   "role": "P",   "x": 260, "y":  90},
            {"label": "CE-A",  "deviceType": "CE",  "role": "CE",  "x": 120, "y": 360}
          ],
          "links": [
            {"source": "PE-1", "target": "P-1",   "label": "ge-0/0/0"},
            {"source": "PE-2", "target": "P-1",   "label": "ge-0/0/1"},
            {"source": "PE-1", "target": "CE-A",  "protocol": "BGP"}
          ],
          "groups": [  // optional, only when the diagram visually clusters devices
            {"name": "Provider Edge", "members": ["PE-1", "PE-2"]}
          ]
        }

    Defaults differ from the Network Mapper / DNOS importers:

    - `auto_layout=False` -- keep the X/Y the agent read from the image so the
      saved canvas matches what the user drew. Pass `auto_layout=True` only
      when the agent could not extract usable positions and wants the
      deterministic grouped row layout instead.
    - `auto_group_by=""` -- do not synthesize role/site groups from metadata.
      The agent should pass explicit `groups: [...]` in the payload when the
      image shows visual clusters; the importer wires them up via
      `_auto_groups` only when the caller opts in.

    The result is a preview only. The caller must show the plan to the user
    (validation issues, summary, warnings), ask which domain to save into via
    AskQuestion, and then call `topology_create_from_plan(domain_id=..., plan_json=plan, name=...)`.
    """
    return _build_plan(
        image_extraction_json or {},
        source="chat-image",
        name=name,
        auto_group_by=auto_group_by,
        auto_layout=auto_layout,
        attach_packets=attach_packets,
    )


def topology_create_from_plan(username: str, domain_id: str, plan_json: Dict[str, Any], name: str = "") -> Dict[str, Any]:
    """Persist a previously previewed topology import plan into a user's domain."""
    plan = dict(plan_json or {})
    state = plan.get("state") or plan.get("state_json") or plan.get("topology") or {}
    if not isinstance(state, dict):
        raise ValueError("plan_json must include a state object")
    validation = topology_validate_topology(username, state_json=state)
    if not validation.get("valid"):
        return {"ok": False, "error": "plan validation failed", "validation": validation}
    topo_name = name or plan.get("name") or (state.get("metadata") or {}).get("name") or "Imported Topology"
    saved = save_topology_for(username, domain_id, None, topo_name, state)
    return {"ok": True, "topology": {k: v for k, v in saved.items() if not k.startswith("__")}, "validation": validation}
