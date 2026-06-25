"""Topology file management MCP tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from api.auth.user_store import SHARED_WITH_ME_DOMAIN_ID, user_store
from mcp.access import (
    McpAccessError,
    _mirror_owned_topology_to_sections,
    load_topology_for,
    normalize_permission,
    resolve_domain_access,
    save_topology_for,
)


def topology_create_topology(
    username: str,
    domain_id: str,
    name: str,
    state_json: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        raise McpAccessError("permission denied")
    data = dict(state_json or {})
    data.setdefault("objects", [])
    topo = save_topology_for(username, domain_id, None, (name or "Untitled").strip(), data)
    return {"ok": True, "topology": {k: v for k, v in topo.items() if not k.startswith("__")}}


def topology_save_topology(
    username: str,
    domain_id: str,
    topology_id: str,
    name: str,
    state_json: Dict[str, Any],
) -> Dict[str, Any]:
    topo = save_topology_for(username, domain_id, topology_id, name, dict(state_json or {}))
    return {"ok": True, "topology": {k: v for k, v in topo.items() if not k.startswith("__")}}


def topology_repair_legacy_visibility(
    username: str,
    domain_id: str,
    topology_id: str,
) -> Dict[str, Any]:
    """Mirror an existing DB topology into the legacy section files used by the current dropdown."""
    owner, real_domain_id, _permission = resolve_domain_access(username, domain_id, require_write=True)
    if owner != username:
        raise McpAccessError("permission denied")
    topology = load_topology_for(username, real_domain_id, topology_id, require_write=True)
    data = dict(topology.get("data") or {})
    result = {
        "id": topology.get("id") or topology_id,
        "__real_topology_id": topology.get("id") or topology_id,
        "name": topology.get("name") or (data.get("metadata") or {}).get("name") or "Topology",
    }
    _mirror_owned_topology_to_sections(owner, real_domain_id, result, data)
    return {"ok": True, "topology": {k: v for k, v in result.items() if not k.startswith("__")}}


def topology_delete_topology(username: str, domain_id: str, topology_id: str) -> Dict[str, Any]:
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        raise McpAccessError("permission denied")
    owner, real_domain_id, _permission = resolve_domain_access(username, domain_id, require_write=True)
    if owner != username:
        raise McpAccessError("permission denied")
    result = user_store.delete_topology(username, real_domain_id, topology_id, actor=username)
    return {"ok": bool(result.get("deleted")), "result": result}


def topology_share_topology(
    username: str,
    domain_id: str,
    topology_id: str,
    target_users: List[str],
    permission: str = "view",
) -> Dict[str, Any]:
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        raise McpAccessError("permission denied")
    owner, real_domain_id, _permission = resolve_domain_access(username, domain_id, require_write=True)
    if owner != username:
        raise McpAccessError("permission denied")
    perm = normalize_permission(permission)
    missing = [u for u in (target_users or []) if not user_store.get_user(u)]
    if missing:
        raise ValueError("one or more target users do not exist")
    result = user_store.share_topology(
        username, real_domain_id, topology_id, target_users or [], perm,
        actor=username, actor_display_name=username,
    )
    if not result.get("ok"):
        raise ValueError("topology not found")
    return {"ok": True, "result": result}


def topology_unshare_topology(
    username: str,
    domain_id: str,
    topology_id: str,
    target_user: str,
) -> Dict[str, Any]:
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        raise McpAccessError("permission denied")
    owner, real_domain_id, _permission = resolve_domain_access(username, domain_id, require_write=True)
    if owner != username:
        raise McpAccessError("permission denied")
    result = user_store.unshare_topology(
        username, real_domain_id, topology_id, target_user,
        actor=username, actor_display_name=username,
    )
    return {"ok": True, "result": result}

