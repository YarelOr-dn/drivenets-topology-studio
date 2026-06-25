"""Topology summary and validation MCP tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from mcp.access import load_topology_for


def _objects(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    objects = data.get("objects") or []
    return [obj for obj in objects if isinstance(obj, dict)]


def _label(obj: Dict[str, Any]) -> str:
    return str(obj.get("label") or obj.get("name") or obj.get("hostname") or obj.get("id") or "")


def _link_endpoints(obj: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    source = obj.get("source") or obj.get("device1") or obj.get("from") or obj.get("fromDevice")
    target = obj.get("target") or obj.get("device2") or obj.get("to") or obj.get("toDevice")
    return (str(source) if source is not None else None, str(target) if target is not None else None)


def _validate_state(data: Dict[str, Any]) -> Dict[str, Any]:
    objects = _objects(data)
    issues: List[Dict[str, Any]] = []
    seen_ids: Dict[str, int] = {}
    seen_names: Dict[str, List[str]] = {}
    for obj in objects:
        object_id = obj.get("id")
        if object_id is None or str(object_id).strip() == "":
            issues.append({"severity": "error", "kind": "missing_id", "object": obj})
            continue
        object_id = str(object_id)
        seen_ids[object_id] = seen_ids.get(object_id, 0) + 1
        name = _label(obj).strip().lower()
        if name:
            seen_names.setdefault(name, []).append(object_id)
    duplicate_ids = sorted(object_id for object_id, count in seen_ids.items() if count > 1)
    for object_id in duplicate_ids:
        issues.append({"severity": "error", "kind": "duplicate_id", "object_id": object_id})
    duplicate_names = {name: ids for name, ids in seen_names.items() if len(ids) > 1}
    for name, ids in sorted(duplicate_names.items()):
        issues.append({"severity": "warning", "kind": "duplicate_name", "name": name, "object_ids": ids})

    valid_ids = set(seen_ids)
    for obj in objects:
        if obj.get("type") != "link":
            continue
        source, target = _link_endpoints(obj)
        missing = [endpoint for endpoint in (source, target) if endpoint and endpoint not in valid_ids]
        if missing:
            issues.append({
                "severity": "error",
                "kind": "missing_link_endpoint",
                "object_id": obj.get("id"),
                "missing": missing,
            })
        if not source or not target:
            issues.append({
                "severity": "error",
                "kind": "orphan_link",
                "object_id": obj.get("id"),
                "source": source or "",
                "target": target or "",
            })

    groups: Dict[str, List[str]] = {}
    leader_by_group: Dict[str, str] = {}
    for obj in objects:
        group_id = obj.get("groupId")
        if not group_id:
            continue
        group_key = str(group_id)
        groups.setdefault(group_key, []).append(str(obj.get("id")))
        if obj.get("groupLeaderId"):
            leader_by_group.setdefault(group_key, str(obj.get("groupLeaderId")))
    for group_id, members in sorted(groups.items()):
        if len(members) < 2:
            issues.append({"severity": "warning", "kind": "single_member_group", "group_id": group_id, "members": members})
        leader = leader_by_group.get(group_id)
        if leader and leader not in members:
            issues.append({
                "severity": "error",
                "kind": "broken_group_leader",
                "group_id": group_id,
                "leader_id": leader,
                "members": members,
            })

    by_type: Dict[str, int] = {}
    for obj in objects:
        kind = str(obj.get("type") or "unknown")
        by_type[kind] = by_type.get(kind, 0) + 1
    errors = [issue for issue in issues if issue.get("severity") == "error"]
    warnings = [issue for issue in issues if issue.get("severity") != "error"]
    return {
        "ok": len(errors) == 0,
        "summary": {
            "object_count": len(objects),
            "by_type": by_type,
            "group_count": len(groups),
            "link_count": by_type.get("link", 0),
            "device_count": by_type.get("device", 0),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "issues": issues,
    }


def topology_validate_topology(
    username: str,
    domain_id: str = "",
    topology_id: str = "",
    state_json: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Validate a saved topology or an unsaved topology JSON payload."""
    if state_json is not None:
        data = dict(state_json or {})
    else:
        topology = load_topology_for(username, domain_id, topology_id)
        data = topology.get("data") or {}
    result = _validate_state(data)
    return {
        "ok": True,
        "valid": result["ok"],
        "summary": result["summary"],
        "issues": result["issues"],
    }


def topology_summarize_topology(
    username: str,
    domain_id: str = "",
    topology_id: str = "",
    state_json: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Return object, link, group and issue counts for a topology."""
    result = topology_validate_topology(username, domain_id, topology_id, state_json)
    return {
        "ok": True,
        "valid": result["valid"],
        "summary": result["summary"],
        "issues": result["issues"][:20],
    }
