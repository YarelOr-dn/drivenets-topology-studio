"""Manual group management MCP tools."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from mcp.access import load_topology_for, save_topology_for


GROUP_FIELDS = {"groupId", "groupLeaderId", "groupOffsetX", "groupOffsetY", "groupName", "groupColor"}
GROUP_PALETTE = [
    "#00B4D8", "#FF5E1F", "#2ecc71", "#9b59b6", "#f39c12",
    "#1abc9c", "#e67e22", "#3b82f6", "#d35400", "#16a085",
    "#27ae60", "#8e44ad", "#f1c40f", "#c0392b", "#64748b",
]


def _objects(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    objects = data.setdefault("objects", [])
    if not isinstance(objects, list):
        data["objects"] = []
        return data["objects"]
    return objects


def _object_map(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(obj.get("id")): obj for obj in _objects(data) if isinstance(obj, dict) and obj.get("id") is not None}


def _stable_group_id(name: str, members: List[str]) -> str:
    seed = "|".join([name or "group"] + sorted(str(m) for m in members))
    return "group_" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]


def _color_for(group_id: str) -> str:
    digest = hashlib.sha1(str(group_id).encode("utf-8")).hexdigest()
    return GROUP_PALETTE[int(digest[:4], 16) % len(GROUP_PALETTE)]


def _position(obj: Dict[str, Any]) -> tuple[float, float]:
    if obj.get("type") == "unbound" and isinstance(obj.get("start"), dict) and isinstance(obj.get("end"), dict):
        return (
            (float(obj["start"].get("x") or 0) + float(obj["end"].get("x") or 0)) / 2,
            (float(obj["start"].get("y") or 0) + float(obj["end"].get("y") or 0)) / 2,
        )
    return float(obj.get("x") or 0), float(obj.get("y") or 0)


def _leader(members: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not members:
        return None
    return sorted(members, key=lambda obj: (-_position(obj)[0], _position(obj)[1], str(obj.get("id"))))[0]


def _clear_group(obj: Dict[str, Any]) -> None:
    for key in GROUP_FIELDS:
        obj.pop(key, None)


def _summarize_groups(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    for obj in _objects(data):
        if not isinstance(obj, dict) or not obj.get("groupId"):
            continue
        group_id = str(obj["groupId"])
        item = grouped.setdefault(
            group_id,
            {
                "id": group_id,
                "name": obj.get("groupName") or "",
                "color": obj.get("groupColor") or _color_for(group_id),
                "leader_id": obj.get("groupLeaderId") or "",
                "members": [],
            },
        )
        item["members"].append(str(obj.get("id")))
        if not item["name"] and obj.get("groupName"):
            item["name"] = obj.get("groupName")
        if not item["leader_id"] and obj.get("groupLeaderId"):
            item["leader_id"] = obj.get("groupLeaderId")
    return sorted(grouped.values(), key=lambda g: (str(g.get("name") or "").lower(), str(g["id"])))


def _save(username: str, topology: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    result = save_topology_for(
        username,
        topology.get("domain_id") or "",
        topology.get("id") or "",
        topology.get("name") or (data.get("metadata") or {}).get("name") or "Topology",
        data,
    )
    return {k: v for k, v in result.items() if not k.startswith("__")}


def _apply_group(data: Dict[str, Any], group_id: str, member_ids: List[str], name: str = "", color: str = "") -> Dict[str, Any]:
    by_id = _object_map(data)
    missing = [member_id for member_id in member_ids if str(member_id) not in by_id]
    if missing:
        raise ValueError("one or more group members do not exist")
    members = [by_id[str(member_id)] for member_id in member_ids]
    leader = _leader(members)
    leader_id = str(leader.get("id")) if leader else ""
    leader_x, leader_y = _position(leader or {})
    group_color = color or _color_for(group_id)
    for obj in members:
        x, y = _position(obj)
        obj["groupId"] = group_id
        obj["groupLeaderId"] = leader_id
        obj["groupOffsetX"] = x - leader_x
        obj["groupOffsetY"] = y - leader_y
        obj["groupName"] = name or obj.get("groupName") or group_id
        obj["groupColor"] = group_color
    return {
        "id": group_id,
        "name": name or group_id,
        "color": group_color,
        "leader_id": leader_id,
        "members": [str(obj.get("id")) for obj in members],
    }


def topology_list_groups(username: str, domain_id: str, topology_id: str) -> Dict[str, Any]:
    """List manual groups derived from object group fields."""
    topology = load_topology_for(username, domain_id, topology_id)
    groups = _summarize_groups(topology.get("data") or {})
    return {"ok": True, "groups": groups, "count": len(groups)}


def topology_create_group(
    username: str,
    domain_id: str,
    topology_id: str,
    member_ids: List[str],
    name: str = "",
    color: str = "",
    group_id: str = "",
) -> Dict[str, Any]:
    """Create a manual group by assigning group metadata to existing objects."""
    topology = load_topology_for(username, domain_id, topology_id, require_write=True)
    data = topology.get("data") or {}
    members = [str(member_id) for member_id in (member_ids or [])]
    if len(members) < 2:
        raise ValueError("group requires at least two members")
    effective_id = group_id or _stable_group_id(name, members)
    group = _apply_group(data, effective_id, members, name=name, color=color)
    saved = _save(username, topology, data)
    return {"ok": True, "group": group, "groups": _summarize_groups(data), "topology": saved}


def topology_update_group(
    username: str,
    domain_id: str,
    topology_id: str,
    group_id: str,
    name: str = "",
    color: str = "",
) -> Dict[str, Any]:
    """Rename or recolor an existing manual group."""
    topology = load_topology_for(username, domain_id, topology_id, require_write=True)
    data = topology.get("data") or {}
    members = [obj for obj in _objects(data) if isinstance(obj, dict) and str(obj.get("groupId")) == str(group_id)]
    if not members:
        raise ValueError("group not found")
    for obj in members:
        if name:
            obj["groupName"] = name
        if color:
            obj["groupColor"] = color
    saved = _save(username, topology, data)
    return {"ok": True, "group": next(g for g in _summarize_groups(data) if g["id"] == group_id), "topology": saved}


def topology_set_group_members(
    username: str,
    domain_id: str,
    topology_id: str,
    group_id: str,
    member_ids: List[str],
) -> Dict[str, Any]:
    """Replace the membership for a manual group."""
    topology = load_topology_for(username, domain_id, topology_id, require_write=True)
    data = topology.get("data") or {}
    prior = [obj for obj in _objects(data) if isinstance(obj, dict) and str(obj.get("groupId")) == str(group_id)]
    if not prior:
        raise ValueError("group not found")
    name = next((obj.get("groupName") for obj in prior if obj.get("groupName")), group_id)
    color = next((obj.get("groupColor") for obj in prior if obj.get("groupColor")), _color_for(group_id))
    for obj in prior:
        _clear_group(obj)
    members = [str(member_id) for member_id in (member_ids or [])]
    if len(members) < 2:
        saved = _save(username, topology, data)
        return {"ok": True, "group": None, "groups": _summarize_groups(data), "topology": saved}
    group = _apply_group(data, group_id, members, name=name, color=color)
    saved = _save(username, topology, data)
    return {"ok": True, "group": group, "groups": _summarize_groups(data), "topology": saved}


def topology_disband_group(username: str, domain_id: str, topology_id: str, group_id: str) -> Dict[str, Any]:
    """Remove group metadata from all members of a manual group."""
    topology = load_topology_for(username, domain_id, topology_id, require_write=True)
    data = topology.get("data") or {}
    removed = []
    for obj in _objects(data):
        if isinstance(obj, dict) and str(obj.get("groupId")) == str(group_id):
            removed.append(str(obj.get("id")))
            _clear_group(obj)
    if not removed:
        raise ValueError("group not found")
    saved = _save(username, topology, data)
    return {"ok": True, "disbanded": group_id, "removed_members": removed, "groups": _summarize_groups(data), "topology": saved}


def topology_delete_group(username: str, domain_id: str, topology_id: str, group_id: str) -> Dict[str, Any]:
    """Alias for topology_disband_group; topology groups are stored on members."""
    return topology_disband_group(username, domain_id, topology_id, group_id)


def topology_auto_group(
    username: str,
    domain_id: str,
    topology_id: str,
    field: str = "role",
    min_members: int = 2,
) -> Dict[str, Any]:
    """Create groups from a common object field such as role, site, type or deviceType."""
    allowed = {"field", "role", "site", "type", "deviceType", "device_type", "kind"}
    group_field = "deviceType" if field == "device_type" else field
    if group_field not in allowed:
        raise ValueError("unsupported auto-group field")
    topology = load_topology_for(username, domain_id, topology_id, require_write=True)
    data = topology.get("data") or {}
    buckets: Dict[str, List[str]] = {}
    for obj in _objects(data):
        if not isinstance(obj, dict):
            continue
        value = obj.get(group_field)
        if group_field == "role" and not value:
            value = obj.get("deviceRole") or obj.get("deviceType")
        if not value:
            continue
        buckets.setdefault(str(value), []).append(str(obj.get("id")))
    created = []
    for value, members in sorted(buckets.items()):
        if len(members) < max(2, int(min_members or 2)):
            continue
        group_name = f"{group_field}:{value}"
        group_id = _stable_group_id(group_name, members)
        created.append(_apply_group(data, group_id, members, name=group_name))
    saved = _save(username, topology, data)
    return {"ok": True, "created": created, "groups": _summarize_groups(data), "topology": saved}
