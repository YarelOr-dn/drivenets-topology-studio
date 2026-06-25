"""Canvas object mutation MCP tools."""

from __future__ import annotations

from typing import Any, Dict, List

from mcp.access import ensure_object_id, find_object, load_topology_for, normalize_kind, save_topology_for


def _save_loaded(username: str, topology: Dict[str, Any]) -> Dict[str, Any]:
    data = topology.get("data") or {}
    name = topology.get("name") or (data.get("metadata") or {}).get("name") or "Untitled"
    domain_id = topology.get("domain_id") or ""
    topology_id = topology.get("id") or ""
    result = save_topology_for(username, domain_id, topology_id, name, data)
    return {k: v for k, v in result.items() if not k.startswith("__")}


def topology_add_object(
    username: str,
    domain_id: str,
    topology_id: str,
    kind: str,
    properties: Dict[str, Any],
) -> Dict[str, Any]:
    topology = load_topology_for(username, domain_id, topology_id, require_write=True)
    data = topology.setdefault("data", {})
    objects = data.setdefault("objects", [])
    obj = ensure_object_id(properties or {})
    obj["type"] = normalize_kind(kind)
    objects.append(obj)
    saved = _save_loaded(username, topology)
    return {"ok": True, "object": obj, "topology": saved}


def topology_update_object(
    username: str,
    domain_id: str,
    topology_id: str,
    object_id: str,
    fields: Dict[str, Any],
) -> Dict[str, Any]:
    topology = load_topology_for(username, domain_id, topology_id, require_write=True)
    _objects, obj = find_object(topology.setdefault("data", {}), object_id)
    for key, value in (fields or {}).items():
        if key in {"id"}:
            continue
        obj[key] = value
    saved = _save_loaded(username, topology)
    return {"ok": True, "object": obj, "topology": saved}


def topology_batch_update_objects(
    username: str,
    domain_id: str,
    topology_id: str,
    patches: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Apply multiple object field updates in one topology save."""
    topology = load_topology_for(username, domain_id, topology_id, require_write=True)
    data = topology.setdefault("data", {})
    updated = []
    for patch in patches or []:
        object_id = patch.get("id") or patch.get("object_id")
        if not object_id:
            raise ValueError("each patch requires id or object_id")
        _objects, obj = find_object(data, str(object_id))
        fields = dict(patch.get("fields") or {})
        for key, value in patch.items():
            if key not in {"id", "object_id", "fields"}:
                fields.setdefault(key, value)
        for key, value in fields.items():
            if key == "id":
                continue
            obj[key] = value
        updated.append(obj)
    saved = _save_loaded(username, topology)
    return {"ok": True, "updated": updated, "count": len(updated), "topology": saved}


def topology_patch_objects(
    username: str,
    domain_id: str,
    topology_id: str,
    patches: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Alias for topology_batch_update_objects."""
    return topology_batch_update_objects(username, domain_id, topology_id, patches)


def topology_move_object(
    username: str,
    domain_id: str,
    topology_id: str,
    object_id: str,
    x: float,
    y: float,
) -> Dict[str, Any]:
    return topology_update_object(
        username, domain_id, topology_id, object_id, {"x": x, "y": y},
    )


def topology_delete_object(
    username: str,
    domain_id: str,
    topology_id: str,
    object_id: str,
) -> Dict[str, Any]:
    topology = load_topology_for(username, domain_id, topology_id, require_write=True)
    data = topology.setdefault("data", {})
    objects, obj = find_object(data, object_id)
    data["objects"] = [o for o in objects if str(o.get("id")) != str(object_id)]
    saved = _save_loaded(username, topology)
    return {"ok": True, "deleted": obj, "topology": saved}


def topology_add_device(username: str, domain_id: str, topology_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
    return topology_add_object(username, domain_id, topology_id, "device", properties)


def topology_update_device(username: str, domain_id: str, topology_id: str, object_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    return topology_update_object(username, domain_id, topology_id, object_id, fields)


def topology_delete_device(username: str, domain_id: str, topology_id: str, object_id: str) -> Dict[str, Any]:
    return topology_delete_object(username, domain_id, topology_id, object_id)


def topology_move_device(username: str, domain_id: str, topology_id: str, object_id: str, x: float, y: float) -> Dict[str, Any]:
    return topology_move_object(username, domain_id, topology_id, object_id, x, y)


def topology_add_link(username: str, domain_id: str, topology_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
    return topology_add_object(username, domain_id, topology_id, "link", properties)


def topology_update_link(username: str, domain_id: str, topology_id: str, object_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    return topology_update_object(username, domain_id, topology_id, object_id, fields)


def topology_delete_link(username: str, domain_id: str, topology_id: str, object_id: str) -> Dict[str, Any]:
    return topology_delete_object(username, domain_id, topology_id, object_id)


def topology_move_link(username: str, domain_id: str, topology_id: str, object_id: str, x: float, y: float) -> Dict[str, Any]:
    return topology_move_object(username, domain_id, topology_id, object_id, x, y)


def topology_add_shape(username: str, domain_id: str, topology_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
    return topology_add_object(username, domain_id, topology_id, "shape", properties)


def topology_update_shape(username: str, domain_id: str, topology_id: str, object_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    return topology_update_object(username, domain_id, topology_id, object_id, fields)


def topology_delete_shape(username: str, domain_id: str, topology_id: str, object_id: str) -> Dict[str, Any]:
    return topology_delete_object(username, domain_id, topology_id, object_id)


def topology_move_shape(username: str, domain_id: str, topology_id: str, object_id: str, x: float, y: float) -> Dict[str, Any]:
    return topology_move_object(username, domain_id, topology_id, object_id, x, y)


def topology_add_text_box(username: str, domain_id: str, topology_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
    return topology_add_object(username, domain_id, topology_id, "text_box", properties)


def topology_update_text_box(username: str, domain_id: str, topology_id: str, object_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    return topology_update_object(username, domain_id, topology_id, object_id, fields)


def topology_delete_text_box(username: str, domain_id: str, topology_id: str, object_id: str) -> Dict[str, Any]:
    return topology_delete_object(username, domain_id, topology_id, object_id)


def topology_move_text_box(username: str, domain_id: str, topology_id: str, object_id: str, x: float, y: float) -> Dict[str, Any]:
    return topology_move_object(username, domain_id, topology_id, object_id, x, y)

