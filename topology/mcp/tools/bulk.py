"""Bulk topology creation and layout MCP tools."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from mcp.access import apply_grid_layout, load_topology_for, save_topology_for


def topology_create_from_spec(
    username: str,
    domain_id: str,
    name: str,
    spec_json: Dict[str, Any],
) -> Dict[str, Any]:
    data = dict(spec_json or {})
    data.setdefault("objects", [])
    topo = save_topology_for(username, domain_id, None, name or "Generated Topology", data)
    return {"ok": True, "topology": {k: v for k, v in topo.items() if not k.startswith("__")}}


def _device(index: int, device_type: str, label: str, x: float, y: float) -> Dict[str, Any]:
    return {
        "id": f"dev-{index + 1}",
        "type": "device",
        "deviceType": device_type,
        "label": label,
        "x": x,
        "y": y,
    }


def _link(index: int, a: str, b: str) -> Dict[str, Any]:
    return {
        "id": f"link-{index + 1}",
        "type": "link",
        "source": a,
        "target": b,
        "device1": a,
        "device2": b,
    }


def topology_create_mesh(
    username: str,
    domain_id: str,
    name: str,
    device_count: int,
    device_type: str = "PE",
    mesh_type: str = "full",
) -> Dict[str, Any]:
    count = max(1, min(int(device_count or 1), 200))
    devices = [
        _device(i, device_type, f"{device_type}-{i + 1}", 160 + (i % 5) * 180, 140 + (i // 5) * 160)
        for i in range(count)
    ]
    links: List[Dict[str, Any]] = []
    if mesh_type == "hub_spoke":
        links = [_link(i, devices[0]["id"], devices[i]["id"]) for i in range(1, count)]
    elif mesh_type == "partial":
        links = [_link(i, devices[i]["id"], devices[i + 1]["id"]) for i in range(count - 1)]
    else:
        idx = 0
        for i in range(count):
            for j in range(i + 1, count):
                links.append(_link(idx, devices[i]["id"], devices[j]["id"]))
                idx += 1
    return topology_create_from_spec(username, domain_id, name, {"objects": devices + links})


def topology_create_chain(
    username: str,
    domain_id: str,
    name: str,
    device_count: int,
    device_type: str = "PE",
    link_template: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    count = max(1, min(int(device_count or 1), 200))
    devices = [_device(i, device_type, f"{device_type}-{i + 1}", 120 + i * 170, 220) for i in range(count)]
    links = []
    for i in range(count - 1):
        link = _link(i, devices[i]["id"], devices[i + 1]["id"])
        link.update(link_template or {})
        links.append(link)
    return topology_create_from_spec(username, domain_id, name, {"objects": devices + links})


def topology_create_star(
    username: str,
    domain_id: str,
    name: str,
    hub_device_type: str = "NCC",
    spoke_count: int = 4,
    spoke_device_type: str = "PE",
) -> Dict[str, Any]:
    count = max(1, min(int(spoke_count or 1), 200))
    objects = [_device(0, hub_device_type, f"{hub_device_type}-HUB", 420, 260)]
    for i in range(count):
        objects.append(_device(i + 1, spoke_device_type, f"{spoke_device_type}-{i + 1}", 120 + i * 150, 120 + (i % 2) * 280))
    links = [_link(i, objects[0]["id"], objects[i + 1]["id"]) for i in range(count)]
    return topology_create_from_spec(username, domain_id, name, {"objects": objects + links})


def topology_duplicate_topology(
    username: str,
    source_domain_id: str,
    source_topology_id: str,
    new_name: str,
    target_domain_id: Optional[str] = None,
) -> Dict[str, Any]:
    source = load_topology_for(username, source_domain_id, source_topology_id)
    target_domain = target_domain_id or source_domain_id
    data = dict(source.get("data") or {})
    return topology_create_from_spec(username, target_domain, new_name or f"{source.get('name', 'Topology')} Copy", data)


def topology_apply_layout(
    username: str,
    domain_id: str,
    topology_id: str,
    layout: str = "grid",
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    topology = load_topology_for(username, domain_id, topology_id, require_write=True)
    data = topology.get("data") or {}
    objects = data.get("objects") or []
    if layout not in ("grid", "force", "hierarchical", "circular"):
        raise ValueError("unsupported layout")
    apply_grid_layout(
        objects,
        columns=int((options or {}).get("columns") or 4),
        spacing=int((options or {}).get("spacing") or 180),
    )
    result = save_topology_for(username, domain_id, topology_id, topology.get("name") or "Topology", data)
    return {"ok": True, "topology": {k: v for k, v in result.items() if not k.startswith("__")}}


def topology_clean_layout(
    username: str,
    domain_id: str,
    topology_id: str,
    group_by: str = "role",
    columns: int = 8,
    x_spacing: int = 180,
    y_spacing: int = 160,
) -> Dict[str, Any]:
    """Apply a deterministic row layout, keeping grouped/imported topologies readable."""
    topology = load_topology_for(username, domain_id, topology_id, require_write=True)
    data = topology.get("data") or {}
    objects = data.get("objects") or []
    devices = [obj for obj in objects if isinstance(obj, dict) and obj.get("type") == "device"]
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for device in sorted(devices, key=lambda obj: str(obj.get("label") or obj.get("hostname") or obj.get("id"))):
        group_value = (
            device.get(group_by)
            or device.get("role")
            or device.get("site")
            or device.get("deviceType")
            or "devices"
        )
        buckets.setdefault(str(group_value), []).append(device)
    row_y = 120
    max_columns = max(1, min(int(columns or 8), 24))
    for _name, bucket in sorted(buckets.items()):
        for index, device in enumerate(bucket):
            device["x"] = 160 + (index % max_columns) * int(x_spacing or 180)
            device["y"] = row_y + math.floor(index / max_columns) * int(y_spacing or 160)
        row_y += int(y_spacing or 160) + math.floor(max(0, len(bucket) - 1) / max_columns) * int(y_spacing or 160)
    result = save_topology_for(username, domain_id, topology_id, topology.get("name") or "Topology", data)
    return {"ok": True, "layout": "clean", "group_by": group_by, "topology": {k: v for k, v in result.items() if not k.startswith("__")}}

