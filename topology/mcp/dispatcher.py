"""Tool registry and dispatch layer for the Topology MCP server."""

from __future__ import annotations

import inspect
from typing import Any, Callable, Dict

from mcp.auth import current_username
from mcp.access import McpAccessError
from mcp.tools import (
    bug_topology,
    bulk,
    discovery,
    domains,
    groups,
    imports,
    inspect as inspect_tools,
    objects,
    topologies,
    validation,
    wizards,
)
from api.auth.user_store import user_store


ToolFn = Callable[..., Dict[str, Any]]


TOOLS: Dict[str, ToolFn] = {
    name: fn
    for module in (
        inspect_tools,
        bug_topology,
        domains,
        topologies,
        objects,
        groups,
        bulk,
        imports,
        validation,
        discovery,
        wizards,
    )
    for name, fn in vars(module).items()
    if name.startswith("topology_") and callable(fn)
}

READ_ONLY_TOOLS = {
    "topology_health",
    "topology_list_domains",
    "topology_list_topologies",
    "topology_get_topology",
    "topology_get_topology_metadata",
    "topology_search",
    "topology_list_groups",
    "topology_validate_topology",
    "topology_summarize_topology",
    "topology_plan_from_network_mapper",
    "topology_plan_from_dnos_json",
    "topology_plan_from_image",
    "topology_discovery_status",
    "topology_discovery_results",
}

TOOL_DESCRIPTIONS: Dict[str, str] = {
    "topology_health": "Check the authenticated user's Topology MCP health, version, role, and domain count. Use as a read-only bootstrap before topology automation.",
    "topology_list_tools": "List available user-topology MCP tools. Use for capability discovery only; route normal work to the specific topology_* tool.",
    "topology_call_tool": "Dispatch a topology MCP tool by name through the authenticated user's context. Use only as a compatibility bridge when a direct topology_* tool is unavailable.",
    "topology_list_domains": "List the authenticated user's own and shared Topology Studio domains. Use before creating or selecting a topology.",
    "topology_create_domain": "Create a per-user Topology Studio domain. Use only for canvas/domain state, not live DNOS inventory.",
    "topology_list_topologies": "List topologies in one domain or across accessible domains. Use before reading, updating, or creating duplicates.",
    "topology_get_topology": "Read one topology JSON from the authenticated user's accessible domain. Use before summarizing or updating canvas objects.",
    "topology_get_topology_metadata": "Read lightweight topology metadata and object count without returning the full canvas payload.",
    "topology_search": "Search accessible domains, topologies, and canvas objects by name/label/hostname. Use to locate an existing topology or object before creating a new one.",
    "topology_summarize_topology": "Summarize a topology's devices, links, groups, and object counts for human review or cross-MCP handoff.",
    "topology_create_topology": "Create a new per-user topology in a selected domain. Use after confirming no existing topology should be updated.",
    "topology_save_topology": "Save or replace topology canvas data in a selected domain. Use for finalizing planned canvas changes.",
    "topology_add_device": "Add one device object to an existing topology canvas. Device truth still comes from dnos-config or Network Mapper.",
    "topology_batch_update_objects": "Apply scoped bulk updates to existing canvas objects. Prefer this over repeated single-object edits.",
    "topology_create_group": "Create a visual group on the canvas. Use for presentation/grouping only, not live device membership.",
    "topology_auto_group": "Auto-create visual groups from topology object metadata such as site, role, or layer.",
    "topology_set_group_members": "Set membership for an existing visual group using canvas object ids.",
    "topology_disband_group": "Remove a visual group while preserving member objects.",
    "topology_list_groups": "List visual groups in a topology. Use before modifying group membership.",
    "topology_clean_layout": "Normalize canvas object placement/layout for readability without changing live network state.",
    "topology_plan_from_network_mapper": "Create a preview-only topology plan from Network Mapper discovery output. Plan first, then call topology_create_from_plan if the user wants canvas state created.",
    "topology_plan_from_dnos_json": "Create a preview-only topology plan from DNOS JSON or exported device data.",
    "topology_plan_from_image": "Create a preview-only topology plan from image-extracted nodes/links. Validate before saving.",
    "topology_create_from_plan": "Create a topology from a previously generated plan. Use after plan review/selection.",
    "topology_create_mesh": "Create a simple mesh topology for demos, validation, or repro scaffolding.",
    "topology_create_bug_topology": "Create a visual bug-repro topology with devices, roles, links, and annotations for Jira/debug handoff.",
    "topology_validate_topology": "Validate topology canvas data before handoff or save; catches missing endpoints and malformed objects.",
    "topology_run_image_upgrade": "Topology app bridge for image-upgrade planning. Actual DNOS upgrade execution belongs to the /UPGRADE skill and dnos-config tools.",
}


def list_tool_names() -> list[str]:
    return sorted(TOOLS)


def tool_schemas() -> Dict[str, Dict[str, Any]]:
    schemas: Dict[str, Dict[str, Any]] = {}
    for name, fn in TOOLS.items():
        sig = inspect.signature(fn)
        params = {}
        required = []
        for param_name, param in sig.parameters.items():
            if param_name == "username":
                continue
            params[param_name] = {"type": "string"}
            annotation = param.annotation
            annotation_text = str(annotation)
            if annotation in (int, float) or annotation_text in ("int", "float"):
                params[param_name]["type"] = "number"
            elif annotation is bool or annotation_text == "bool":
                params[param_name]["type"] = "boolean"
            elif "List" in annotation_text or "list" in annotation_text:
                params[param_name]["type"] = "array"
            elif "Dict" in annotation_text or "dict" in annotation_text:
                params[param_name]["type"] = "object"
            if param.default is inspect._empty:
                required.append(param_name)
        schemas[name] = {
            "name": name,
            "description": TOOL_DESCRIPTIONS.get(name) or inspect.getdoc(fn) or name.replace("_", " "),
            "input_schema": {
                "type": "object",
                "properties": params,
                "required": required,
            },
        }
    return schemas


def dispatch(tool_name: str, arguments: Dict[str, Any] | None = None) -> Dict[str, Any]:
    username = current_username()
    fn = TOOLS.get(tool_name)
    if not fn:
        raise ValueError(f"Unknown tool: {tool_name}")
    if tool_name not in READ_ONLY_TOOLS and not user_store.has_role_or_higher(username, "engineer"):
        return {"ok": False, "error": "permission denied", "code": "permission_denied"}
    try:
        return fn(username=username, **(arguments or {}))
    except McpAccessError as exc:
        return {"ok": False, "error": str(exc) or "permission denied", "code": "permission_denied"}
    except PermissionError as exc:
        return {"ok": False, "error": str(exc) or "permission denied", "code": "permission_denied"}

