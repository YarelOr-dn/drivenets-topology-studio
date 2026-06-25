"""Shared Topology MCP server mounted by scaler_bridge at /mcp."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import sys

# This module intentionally lives at ``mcp.server`` for the local topology
# package, which would normally shadow the upstream ``mcp.server`` package.
# Mark it as package-like and point submodule resolution at the upstream server
# directory so ``mcp.server.fastmcp`` remains importable.
__path__ = []  # type: ignore[var-annotated]
_here = Path(__file__).resolve()
for _entry in list(sys.path):
    try:
        _candidate = Path(_entry).resolve() / "mcp" / "server"
    except Exception:
        continue
    if _candidate == _here.parent:
        continue
    if (_candidate / "fastmcp").is_dir():
        __path__.append(str(_candidate))  # type: ignore[name-defined]
        break

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette

from mcp import VERSION
from mcp.auth import TopologyMcpAuthMiddleware
from mcp.dispatcher import dispatch, list_tool_names, tool_schemas


def build_mcp() -> FastMCP:
    server = FastMCP(
        "drivenets-topology",
        instructions=(
            "Operate only the authenticated user's DriveNets Topology Studio "
            "domains, topologies and canvas objects."
        ),
        sse_path="/sse",
        message_path="/messages/",
    )

    @server.tool()
    def topology_health() -> Dict[str, Any]:
        return dispatch("topology_health", {})

    @server.tool()
    def topology_list_tools() -> Dict[str, Any]:
        return {"ok": True, "tools": list_tool_names(), "schemas": tool_schemas()}

    @server.tool()
    def topology_call_tool(tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call any topology_* tool by name with a JSON argument object."""
        return dispatch(tool_name, arguments or {})

    @server.tool()
    def topology_list_domains(include_shared: bool = True) -> Dict[str, Any]:
        return dispatch("topology_list_domains", {"include_shared": include_shared})

    @server.tool()
    def topology_list_topologies(domain_id: str = "", include_shared: bool = True) -> Dict[str, Any]:
        return dispatch(
            "topology_list_topologies",
            {"domain_id": domain_id, "include_shared": include_shared},
        )

    @server.tool()
    def topology_get_topology(domain_id: str, topology_id: str) -> Dict[str, Any]:
        return dispatch("topology_get_topology", {"domain_id": domain_id, "topology_id": topology_id})

    @server.tool()
    def topology_summarize_topology(
        domain_id: str = "",
        topology_id: str = "",
        state_json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return dispatch(
            "topology_summarize_topology",
            {"domain_id": domain_id, "topology_id": topology_id, "state_json": state_json},
        )

    @server.tool()
    def topology_validate_topology(
        domain_id: str = "",
        topology_id: str = "",
        state_json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return dispatch(
            "topology_validate_topology",
            {"domain_id": domain_id, "topology_id": topology_id, "state_json": state_json},
        )

    @server.tool()
    def topology_create_domain(name: str, description: str = "") -> Dict[str, Any]:
        return dispatch("topology_create_domain", {"name": name, "description": description})

    @server.tool()
    def topology_create_topology(
        domain_id: str,
        name: str,
        state_json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return dispatch(
            "topology_create_topology",
            {"domain_id": domain_id, "name": name, "state_json": state_json or {}},
        )

    @server.tool()
    def topology_create_bug_topology(
        sw_id: str,
        title: str = "",
        summary: str = "",
        devices: Optional[List[Dict[str, Any]]] = None,
        vrfs: Optional[List[Dict[str, Any]]] = None,
        route: Optional[Dict[str, Any]] = None,
        failure_device: str = "",
        force_placeholder: bool = False,
        force_non_bug: bool = False,
    ) -> Dict[str, Any]:
        return dispatch(
            "topology_create_bug_topology",
            {
                "sw_id": sw_id,
                "title": title,
                "summary": summary,
                "devices": devices or [],
                "vrfs": vrfs or [],
                "route": route or {},
                "failure_device": failure_device,
                "force_placeholder": force_placeholder,
                "force_non_bug": force_non_bug,
            },
        )

    @server.tool()
    def topology_save_topology(
        domain_id: str,
        topology_id: str,
        name: str,
        state_json: Dict[str, Any],
    ) -> Dict[str, Any]:
        return dispatch(
            "topology_save_topology",
            {
                "domain_id": domain_id,
                "topology_id": topology_id,
                "name": name,
                "state_json": state_json,
            },
        )

    @server.tool()
    def topology_add_device(domain_id: str, topology_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        return dispatch(
            "topology_add_device",
            {"domain_id": domain_id, "topology_id": topology_id, "properties": properties},
        )

    @server.tool()
    def topology_batch_update_objects(
        domain_id: str,
        topology_id: str,
        patches: list[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return dispatch(
            "topology_batch_update_objects",
            {"domain_id": domain_id, "topology_id": topology_id, "patches": patches},
        )

    @server.tool()
    def topology_list_groups(domain_id: str, topology_id: str) -> Dict[str, Any]:
        return dispatch("topology_list_groups", {"domain_id": domain_id, "topology_id": topology_id})

    @server.tool()
    def topology_create_group(
        domain_id: str,
        topology_id: str,
        member_ids: list[str],
        name: str = "",
        color: str = "",
        group_id: str = "",
    ) -> Dict[str, Any]:
        return dispatch(
            "topology_create_group",
            {
                "domain_id": domain_id,
                "topology_id": topology_id,
                "member_ids": member_ids,
                "name": name,
                "color": color,
                "group_id": group_id,
            },
        )

    @server.tool()
    def topology_set_group_members(domain_id: str, topology_id: str, group_id: str, member_ids: list[str]) -> Dict[str, Any]:
        return dispatch(
            "topology_set_group_members",
            {"domain_id": domain_id, "topology_id": topology_id, "group_id": group_id, "member_ids": member_ids},
        )

    @server.tool()
    def topology_disband_group(domain_id: str, topology_id: str, group_id: str) -> Dict[str, Any]:
        return dispatch("topology_disband_group", {"domain_id": domain_id, "topology_id": topology_id, "group_id": group_id})

    @server.tool()
    def topology_auto_group(domain_id: str, topology_id: str, field: str = "role", min_members: int = 2) -> Dict[str, Any]:
        return dispatch(
            "topology_auto_group",
            {"domain_id": domain_id, "topology_id": topology_id, "field": field, "min_members": min_members},
        )

    @server.tool()
    def topology_create_mesh(
        domain_id: str,
        name: str,
        device_count: int,
        device_type: str = "PE",
        mesh_type: str = "full",
    ) -> Dict[str, Any]:
        return dispatch(
            "topology_create_mesh",
            {
                "domain_id": domain_id,
                "name": name,
                "device_count": device_count,
                "device_type": device_type,
                "mesh_type": mesh_type,
            },
        )

    @server.tool()
    def topology_clean_layout(
        domain_id: str,
        topology_id: str,
        group_by: str = "role",
        columns: int = 8,
    ) -> Dict[str, Any]:
        return dispatch(
            "topology_clean_layout",
            {"domain_id": domain_id, "topology_id": topology_id, "group_by": group_by, "columns": columns},
        )

    @server.tool()
    def topology_plan_from_network_mapper(
        network_mapper_json: Dict[str, Any],
        name: str = "Network Mapper Import",
        auto_group_by: str = "role",
        attach_packets: bool = False,
    ) -> Dict[str, Any]:
        """Preview an import from already-fetched Network Mapper JSON.

        ``attach_packets=True`` adds one compact layered packet/frame chip per
        link that carries protocol/vrf/bd metadata. Empty rows stay collapsed.
        """
        return dispatch(
            "topology_plan_from_network_mapper",
            {
                "network_mapper_json": network_mapper_json,
                "name": name,
                "auto_group_by": auto_group_by,
                "attach_packets": attach_packets,
            },
        )

    @server.tool()
    def topology_plan_from_dnos_json(
        dnos_json: Dict[str, Any],
        name: str = "DNOS Import",
        auto_group_by: str = "role",
        attach_packets: bool = False,
    ) -> Dict[str, Any]:
        """Preview an import from already-fetched dnos-config JSON.

        ``attach_packets=True`` adds a layered packet chip per DNAAS hop link
        so the encap stack (BD/VRF/protocol) is visualized inline.
        """
        return dispatch(
            "topology_plan_from_dnos_json",
            {
                "dnos_json": dnos_json,
                "name": name,
                "auto_group_by": auto_group_by,
                "attach_packets": attach_packets,
            },
        )

    @server.tool()
    def topology_plan_from_image(
        image_extraction_json: Dict[str, Any],
        name: str = "Image Import",
        auto_group_by: str = "",
        auto_layout: bool = False,
        attach_packets: bool = False,
    ) -> Dict[str, Any]:
        """Preview a topology that the agent extracted from an image attached in chat.

        The MCP itself does not see the image. The agent reads the diagram with
        its own vision capability, then passes a payload of devices/links/groups
        (with image-derived X/Y coordinates) to this tool. By default the
        original positions are preserved (auto_layout=False). Save with
        topology_create_from_plan after the user confirms the destination domain.

        ``attach_packets=True`` adds one compact layered packet/frame chip per
        link with protocol/vrf/bd metadata so the agent can teach scenarios
        layer-by-layer above each connection.
        """
        return dispatch(
            "topology_plan_from_image",
            {
                "image_extraction_json": image_extraction_json,
                "name": name,
                "auto_group_by": auto_group_by,
                "auto_layout": auto_layout,
                "attach_packets": attach_packets,
            },
        )

    @server.tool()
    def topology_create_from_plan(domain_id: str, plan_json: Dict[str, Any], name: str = "") -> Dict[str, Any]:
        return dispatch("topology_create_from_plan", {"domain_id": domain_id, "plan_json": plan_json, "name": name})

    @server.tool()
    def topology_run_image_upgrade(
        domain_id: str,
        topology_id: str,
        device_id: str,
        image: str,
        dry_run: bool = True,
        execute: bool = False,
        confirm_phrase: str = "",
    ) -> Dict[str, Any]:
        return dispatch(
            "topology_run_image_upgrade",
            {
                "domain_id": domain_id,
                "topology_id": topology_id,
                "device_id": device_id,
                "image": image,
                "dry_run": dry_run,
                "execute": execute,
                "confirm_phrase": confirm_phrase,
            },
        )

    return server


def create_mcp_app() -> Starlette:
    app = build_mcp().sse_app()
    app.add_middleware(TopologyMcpAuthMiddleware)
    return app

