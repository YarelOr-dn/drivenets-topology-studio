"""Shared per-user access helpers for Topology MCP tools."""

from __future__ import annotations

import json
import math
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from api.auth.user_store import SHARED_WITH_ME_DOMAIN_ID, user_store


READ_PERMISSIONS = {"read", "write"}
WRITE_PERMISSIONS = {"write"}


class McpAccessError(PermissionError):
    """Permission or visibility failure that must not leak cross-user data."""


def permission_to_role(permission: str) -> str:
    return "edit" if permission == "write" else "view"


def normalize_permission(permission: str) -> str:
    raw = (permission or "read").strip().lower()
    if raw in ("view", "read"):
        return "read"
    if raw in ("edit", "write"):
        return "write"
    raise ValueError("permission must be view/read or edit/write")


def list_domains_for(username: str, include_shared: bool = True) -> List[Dict[str, Any]]:
    domains = []
    for domain in user_store.list_domains(username):
        if not include_shared and (domain.get("is_shared") or domain.get("is_shared_with_me_domain")):
            continue
        item = dict(domain)
        if item.get("permission"):
            item["permission_label"] = permission_to_role(item["permission"])
        elif item.get("owner") == username or not item.get("is_shared"):
            item["permission"] = "write"
            item["permission_label"] = "owner"
        domains.append(item)
    return domains


def resolve_domain_access(
    username: str,
    domain_id: str,
    *,
    require_write: bool = False,
) -> Tuple[str, str, str]:
    """Return (owner, real_domain_id, permission) or raise a scrubbed error."""
    for domain in user_store.list_domains(username):
        if domain.get("id") != domain_id:
            continue
        if domain.get("is_shared_with_me_domain"):
            if require_write:
                return username, domain_id, "write"
            return username, domain_id, "read"
        if domain.get("is_shared"):
            permission = domain.get("permission") or "read"
            if require_write and permission not in WRITE_PERMISSIONS:
                raise McpAccessError("permission denied")
            return domain.get("owner") or username, domain_id, permission
        return username, domain_id, "write"
    raise McpAccessError("permission denied")


def load_topology_for(
    username: str,
    domain_id: str,
    topology_id: str,
    *,
    require_write: bool = False,
) -> Dict[str, Any]:
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        topology = user_store.load_topology(username, domain_id, topology_id)
        if not topology:
            raise McpAccessError("permission denied")
        permission = topology.get("__permission") or "read"
        if require_write and permission not in WRITE_PERMISSIONS:
            raise McpAccessError("permission denied")
        return topology
    owner, real_domain_id, permission = resolve_domain_access(
        username, domain_id, require_write=require_write,
    )
    topology = user_store.load_topology(owner, real_domain_id, topology_id)
    if not topology:
        raise McpAccessError("permission denied")
    if owner != username:
        topology["__permission"] = permission
        topology["__owner"] = owner
    return topology


def save_topology_for(
    username: str,
    domain_id: str,
    topology_id: Optional[str],
    name: str,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        if not topology_id:
            raise McpAccessError("permission denied")
        return user_store.save_topology(
            username, domain_id, name, data, topology_id=topology_id,
            actor=username, actor_display_name=username,
        )
    owner, real_domain_id, _permission = resolve_domain_access(
        username, domain_id, require_write=True,
    )
    result = user_store.save_topology(
        owner, real_domain_id, name, data, topology_id=topology_id,
        actor=username, actor_display_name=username,
    )
    _mirror_owned_topology_to_sections(owner, real_domain_id, result, data)
    return result


def list_topologies_for(username: str, domain_id: str) -> List[Dict[str, Any]]:
    if domain_id == SHARED_WITH_ME_DOMAIN_ID:
        return [dict(t) for t in user_store.list_topologies(username, domain_id)]
    owner, real_domain_id, permission = resolve_domain_access(username, domain_id)
    rows = [dict(t) for t in user_store.list_topologies(owner, real_domain_id)]
    for row in rows:
        row.setdefault("owner", owner)
        row.setdefault("permission", permission if owner != username else "write")
        row.setdefault("permission_label", "owner" if owner == username else permission_to_role(permission))
    return rows


def find_object(data: Dict[str, Any], object_id: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    objects = data.setdefault("objects", [])
    for obj in objects:
        if str(obj.get("id")) == str(object_id):
            return objects, obj
    raise ValueError("object not found")


def ensure_object_id(properties: Dict[str, Any]) -> Dict[str, Any]:
    obj = dict(properties or {})
    obj.setdefault("id", str(uuid.uuid4())[:12])
    return obj


def normalize_kind(kind: str) -> str:
    raw = (kind or "").strip().lower().replace("-", "_")
    if raw == "text_box":
        return "text"
    if raw in {"device", "link", "shape", "text", "unbound"}:
        return raw
    raise ValueError("unsupported object kind")


def apply_grid_layout(objects: Iterable[Dict[str, Any]], *, columns: int = 4, spacing: int = 180) -> None:
    placed = [o for o in objects if o.get("type") == "device"]
    columns = max(1, int(columns or 4))
    for index, obj in enumerate(placed):
        obj["x"] = 160 + (index % columns) * spacing
        obj["y"] = 140 + math.floor(index / columns) * spacing


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        prior_mode = path.stat().st_mode & 0o777
    except FileNotFoundError:
        prior_mode = 0o644
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, prior_mode)
        os.replace(tmp, path)
    except BaseException:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        raise


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data
    except Exception:
        return fallback


def _safe_name(value: str, fallback: str = "topology") -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(value or "").strip())
    return safe or fallback


def _domain_name_for(owner: str, domain_id: str) -> str:
    try:
        for domain in user_store.list_domains(owner):
            if str(domain.get("id") or "") == str(domain_id):
                return str(domain.get("name") or domain_id)
    except Exception:
        pass
    return domain_id


def _sections_root(owner: str) -> Path:
    return user_store.user_data_path(owner, "sections")


def _section_dir(owner: str, section_id: str) -> Path:
    return _sections_root(owner) / _safe_name(section_id, "default")


def _mirror_map_path(owner: str, section_id: str) -> Path:
    return _sections_root(owner) / f"_multiuser_mirror__{_safe_name(section_id, 'default')}.json"


def _ensure_legacy_section(owner: str, domain_id: str, domain_name: str) -> str:
    """Return the legacy section id that makes a DB domain visible in the current UI."""
    sections_path = _sections_root(owner) / "_sections.json"
    sections = _read_json(sections_path, [])
    if not isinstance(sections, list):
        sections = []

    for section in sections:
        if isinstance(section, dict) and str(section.get("id") or "") == str(domain_id):
            return str(section["id"])

    domain_lc = str(domain_name or "").strip().lower()
    if domain_lc:
        for section in sections:
            if isinstance(section, dict) and str(section.get("name") or "").strip().lower() == domain_lc:
                return str(section.get("id") or domain_id)

    section = {
        "id": _safe_name(domain_id, str(uuid.uuid4())[:8]),
        "name": domain_name or domain_id or "Topology",
        "icon": "folder",
        "color": "#3b82f6",
        "description": "Mirrored from Topology MCP so generated topologies are visible in the app.",
    }
    sections.append(section)
    _atomic_write_json(sections_path, sections)
    return str(section["id"])


def _mirror_owned_topology_to_sections(
    owner: str,
    domain_id: str,
    saved: Dict[str, Any],
    data: Dict[str, Any],
) -> None:
    """Mirror MCP DB writes into the legacy section files still used by the top-bar dropdown."""
    if not owner or domain_id == SHARED_WITH_ME_DOMAIN_ID:
        return
    topology_id = str(saved.get("__real_topology_id") or saved.get("id") or "")
    if not topology_id:
        return
    topology_name = str(saved.get("name") or (data.get("metadata") or {}).get("name") or "Topology")
    domain_name = _domain_name_for(owner, domain_id)
    try:
        section_id = _ensure_legacy_section(owner, domain_id, domain_name)
        filename = f"{_safe_name(topology_name)}.json"
        _atomic_write_json(_section_dir(owner, section_id) / filename, data or {})
        mirror_path = _mirror_map_path(owner, section_id)
        mirror = _read_json(mirror_path, {})
        if not isinstance(mirror, dict):
            mirror = {}
        mirror[filename] = {"domain_id": domain_id, "topology_id": topology_id}
        _atomic_write_json(mirror_path, mirror)
        saved["legacy_section_id"] = section_id
        saved["legacy_filename"] = filename
    except Exception as exc:
        saved["legacy_mirror_warning"] = str(exc)

