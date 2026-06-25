"""Read-only Topology MCP tools."""

from __future__ import annotations

from typing import Any, Dict, List

from api.auth.user_store import user_store
from mcp import VERSION
from mcp.access import list_domains_for, list_topologies_for, load_topology_for


def topology_health(username: str) -> Dict[str, Any]:
    user = user_store.get_user(username) or {}
    domains = list_domains_for(username, include_shared=True)
    return {
        "ok": True,
        "username": username,
        "display_name": user.get("display_name") or username,
        "role": user.get("role") or "",
        "version": VERSION,
        "domain_count": len(domains),
    }


def topology_list_domains(username: str, include_shared: bool = True) -> Dict[str, Any]:
    domains = list_domains_for(username, include_shared=include_shared)
    return {"ok": True, "domains": domains, "count": len(domains)}


def topology_list_topologies(
    username: str,
    domain_id: str = "",
    include_shared: bool = True,
) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    if domain_id:
        rows = list_topologies_for(username, domain_id)
    else:
        for domain in list_domains_for(username, include_shared=include_shared):
            rows.extend(list_topologies_for(username, domain["id"]))
    return {"ok": True, "topologies": rows, "count": len(rows)}


def topology_get_topology(username: str, domain_id: str, topology_id: str) -> Dict[str, Any]:
    topology = load_topology_for(username, domain_id, topology_id)
    return {"ok": True, "topology": topology}


def topology_get_topology_metadata(username: str, domain_id: str, topology_id: str) -> Dict[str, Any]:
    topology = load_topology_for(username, domain_id, topology_id)
    data = topology.get("data") or {}
    metadata = {k: v for k, v in topology.items() if k != "data"}
    metadata["object_count"] = len(data.get("objects") or [])
    return {"ok": True, "metadata": metadata}


def topology_search(username: str, query: str, scope: str = "all") -> Dict[str, Any]:
    needle = (query or "").strip().lower()
    if not needle:
        return {"ok": True, "results": [], "count": 0}
    include_shared = scope in ("all", "shared")
    include_own = scope in ("all", "own")
    results: List[Dict[str, Any]] = []
    for domain in list_domains_for(username, include_shared=True):
        is_shared = bool(domain.get("is_shared") or domain.get("is_shared_with_me_domain"))
        if is_shared and not include_shared:
            continue
        if not is_shared and not include_own:
            continue
        if needle in (domain.get("name") or "").lower():
            results.append({"type": "domain", "domain": domain})
        for topo in list_topologies_for(username, domain["id"]):
            if needle in (topo.get("name") or "").lower():
                results.append({"type": "topology", "domain": domain, "topology": topo})
                continue
            try:
                full = load_topology_for(username, domain["id"], topo["id"])
                for obj in (full.get("data") or {}).get("objects") or []:
                    haystack = " ".join(
                        str(obj.get(k) or "")
                        for k in ("id", "name", "label", "text", "hostname", "deviceType")
                    ).lower()
                    if needle in haystack:
                        results.append({
                            "type": "object",
                            "domain": domain,
                            "topology": topo,
                            "object": obj,
                        })
                        break
            except Exception:
                continue
    return {"ok": True, "results": results, "count": len(results)}

