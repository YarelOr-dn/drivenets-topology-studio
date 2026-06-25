"""High-power wizard MCP tools with dry-run-first safety gates."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from mcp.access import McpAccessError, load_topology_for


def _require_live_confirmation(device_name: str, dry_run: bool, execute: bool, confirm_phrase: str) -> None:
    if dry_run or not execute:
        return
    expected = f"I understand this is destructive on {device_name}"
    if confirm_phrase != expected:
        raise McpAccessError(
            "live wizard execution requires dry_run=false, execute=true, and the exact confirm_phrase"
        )


def _device_from_topology(topology: Dict[str, Any], device_id: str) -> Dict[str, Any]:
    data = topology.get("data") or {}
    for obj in data.get("objects") or []:
        if str(obj.get("id")) == str(device_id) or str(obj.get("label")) == str(device_id):
            if obj.get("type") == "device":
                return obj
    raise ValueError("device not found in topology")


def topology_run_image_upgrade(
    username: str,
    domain_id: str,
    topology_id: str,
    device_id: str,
    image: str,
    dry_run: bool = True,
    execute: bool = False,
    confirm_phrase: str = "",
) -> Dict[str, Any]:
    topology = load_topology_for(username, domain_id, topology_id, require_write=True)
    device = _device_from_topology(topology, device_id)
    device_name = device.get("label") or device.get("hostname") or device_id
    _require_live_confirmation(device_name, dry_run, execute, confirm_phrase)
    return {
        "ok": True,
        "dry_run": bool(dry_run or not execute),
        "wizard": "image_upgrade",
        "device": device,
        "image": image,
        "message": "Dry-run accepted. Use the web Image Upgrade Wizard for live execution until MCP device mutation is enabled.",
    }


def topology_run_config_push(
    username: str,
    domain_id: str,
    topology_id: str,
    device_id: str,
    config_blocks: List[str],
    dry_run: bool = True,
    execute: bool = False,
    confirm_phrase: str = "",
) -> Dict[str, Any]:
    topology = load_topology_for(username, domain_id, topology_id, require_write=True)
    device = _device_from_topology(topology, device_id)
    device_name = device.get("label") or device.get("hostname") or device_id
    _require_live_confirmation(device_name, dry_run, execute, confirm_phrase)
    return {
        "ok": True,
        "dry_run": bool(dry_run or not execute),
        "wizard": "config_push",
        "device": device,
        "config_blocks": config_blocks or [],
        "message": "Dry-run accepted. Use the web Config Push Wizard for live execution until MCP device mutation is enabled.",
    }


def topology_run_bul_links(
    username: str,
    domain_id: str,
    topology_id: str,
    plan_json: Dict[str, Any],
    dry_run: bool = True,
    execute: bool = False,
    confirm_phrase: str = "",
) -> Dict[str, Any]:
    topology = load_topology_for(username, domain_id, topology_id, require_write=True)
    _require_live_confirmation(topology.get("name") or topology_id, dry_run, execute, confirm_phrase)
    return {
        "ok": True,
        "dry_run": bool(dry_run or not execute),
        "wizard": "bul_links",
        "topology_id": topology_id,
        "plan": plan_json or {},
        "message": "Dry-run accepted. Use the web BUL wizard for live execution until MCP device mutation is enabled.",
    }

