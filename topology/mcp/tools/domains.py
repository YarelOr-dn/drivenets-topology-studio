"""Domain management Topology MCP tools."""

from __future__ import annotations

from typing import Any, Dict, List

from api.auth.user_store import SHARED_WITH_ME_DOMAIN_ID, user_store
from mcp.access import McpAccessError, normalize_permission, resolve_domain_access


def topology_create_domain(username: str, name: str, description: str = "") -> Dict[str, Any]:
    domain = user_store.create_domain(username, (name or "").strip(), description or "")
    return {"ok": True, "domain": domain}


def topology_rename_domain(username: str, domain_id: str, new_name: str) -> Dict[str, Any]:
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        raise McpAccessError("permission denied")
    owner, _real_domain_id, _permission = resolve_domain_access(username, domain_id, require_write=True)
    if owner != username:
        raise McpAccessError("permission denied")
    domains = user_store.list_domains(username)
    target = None
    for domain in domains:
        if domain.get("id") == domain_id and not domain.get("is_shared"):
            target = dict(domain)
            break
    if not target:
        raise McpAccessError("permission denied")
    target["name"] = (new_name or "").strip()
    user_store.update_domain(username, domain_id, target["name"], target.get("description", ""))
    return {"ok": True, "domain": target}


def topology_delete_domain(username: str, domain_id: str) -> Dict[str, Any]:
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        raise McpAccessError("permission denied")
    owner, _real_domain_id, _permission = resolve_domain_access(username, domain_id, require_write=True)
    if owner != username:
        raise McpAccessError("permission denied")
    return {"ok": user_store.delete_domain(username, domain_id), "domain_id": domain_id}


def topology_share_domain(
    username: str,
    domain_id: str,
    target_users: List[str],
    permission: str = "view",
) -> Dict[str, Any]:
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        raise McpAccessError("permission denied")
    owner, _real_domain_id, _permission = resolve_domain_access(username, domain_id, require_write=True)
    if owner != username:
        raise McpAccessError("permission denied")
    perm = normalize_permission(permission)
    missing = [u for u in (target_users or []) if not user_store.get_user(u)]
    if missing:
        raise ValueError("one or more target users do not exist")
    ok = user_store.share_domain(username, domain_id, target_users or [], perm, actor=username)
    return {"ok": ok, "domain_id": domain_id, "shared_with": target_users or [], "permission": perm}


def topology_unshare_domain(username: str, domain_id: str, target_user: str) -> Dict[str, Any]:
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        raise McpAccessError("permission denied")
    owner, _real_domain_id, _permission = resolve_domain_access(username, domain_id, require_write=True)
    if owner != username:
        raise McpAccessError("permission denied")
    ok = user_store.unshare_domain(username, domain_id, target_user, actor=username)
    return {"ok": ok, "domain_id": domain_id, "target_user": target_user}

