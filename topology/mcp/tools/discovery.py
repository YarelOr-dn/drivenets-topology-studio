"""Discovery integration MCP tools.

These tools intentionally return lightweight job handles and instructions. The
existing discovery services remain the authority for live device probing; MCP
callers can use these helpers to create per-user workflow markers and then use
the normal web app for interactive review.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional

from api.auth.user_store import user_store
from mcp.access import load_topology_for, save_topology_for


def _job_path(username: str, job_id: str):
    return user_store.user_data_path(username, f"cursor_mcp/discovery/{job_id}.json")


def topology_discovery_trigger(
    username: str,
    domain_id: str,
    seed_devices: Optional[List[str]] = None,
    subnet: Optional[str] = None,
) -> Dict[str, Any]:
    job_id = str(uuid.uuid4())[:12]
    payload = {
        "job_id": job_id,
        "domain_id": domain_id,
        "seed_devices": seed_devices or [],
        "subnet": subnet or "",
        "status": "planned",
        "message": "Open the Topology Studio discovery panel to run the live sweep.",
        "results": [],
    }
    path = _job_path(username, job_id)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    tmp.replace(path)
    return {"ok": True, "job_id": job_id, "status": payload["status"], "message": payload["message"]}


def topology_discovery_status(username: str, job_id: str) -> Dict[str, Any]:
    path = _job_path(username, job_id)
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError):
        raise ValueError("discovery job not found")
    return {"ok": True, "job": payload}


def topology_discovery_results(username: str, job_id: str) -> Dict[str, Any]:
    job = topology_discovery_status(username, job_id)["job"]
    return {"ok": True, "job_id": job_id, "results": job.get("results") or []}


def topology_discovery_accept(
    username: str,
    job_id: str,
    device_ids: List[str],
    target_domain_id: str,
    target_topology_id: str,
) -> Dict[str, Any]:
    job = topology_discovery_status(username, job_id)["job"]
    topology = load_topology_for(username, target_domain_id, target_topology_id, require_write=True)
    data = topology.get("data") or {}
    objects = data.setdefault("objects", [])
    accepted = []
    for index, dev in enumerate(job.get("results") or []):
        if dev.get("id") not in set(device_ids or []):
            continue
        obj = {
            "id": dev.get("id"),
            "type": "device",
            "label": dev.get("name") or dev.get("hostname") or dev.get("id"),
            "hostname": dev.get("hostname") or dev.get("name") or "",
            "x": 160 + index * 160,
            "y": 180,
        }
        objects.append(obj)
        accepted.append(obj)
    saved = save_topology_for(username, target_domain_id, target_topology_id, topology.get("name") or "Topology", data)
    return {"ok": True, "accepted": accepted, "topology": {k: v for k, v in saved.items() if not k.startswith("__")}}

