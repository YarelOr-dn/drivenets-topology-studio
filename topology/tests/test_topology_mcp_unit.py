#!/usr/bin/env python3
"""Unit smoke for the Topology MCP dispatcher and per-user isolation."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.auth.user_store import user_store  # noqa: E402
from mcp.auth import current_mcp_user  # noqa: E402
from mcp.dispatcher import dispatch, list_tool_names, tool_schemas  # noqa: E402


def _assert_mcp_streaming_middleware_contract() -> None:
    """Static guard for MCP SSE stability.

    The MCP ASGI app is mounted and streams SSE. Starlette BaseHTTPMiddleware can
    corrupt mounted streaming response sequencing and crash uvicorn with
    "Unexpected http.response.start", so both bridge and MCP auth middleware must
    stay plain ASGI.
    """
    scaler_bridge = (ROOT / "scaler_bridge.py").read_text(encoding="utf-8")
    mcp_auth = (ROOT / "mcp" / "auth.py").read_text(encoding="utf-8")
    serve = (ROOT / "serve.py").read_text(encoding="utf-8")
    assert '@app.middleware("http")' not in scaler_bridge
    assert "class JwtAuthMiddleware:" in scaler_bridge
    assert "class TopologyMcpAuthMiddleware:" in mcp_auth
    assert "from starlette.middleware.base import BaseHTTPMiddleware" not in mcp_auth
    assert 'Request(DISCOVERY_API + "/api/health", method="GET")' in serve
    assert 'Request(SCALER_BRIDGE_API + "/api/health", method="GET")' in serve
    bridge_start = serve[serve.index("def _start_scaler_bridge"):serve.index("def _health_ok")]
    discovery_start = serve[serve.index("def _start_discovery_api"):serve.index("def _start_scaler_bridge")]
    assert "stderr=subprocess.PIPE" not in bridge_start
    assert "stdout=log_file" in bridge_start and "stderr=subprocess.STDOUT" in bridge_start
    assert "bridge_cmd = [" in bridge_start
    bridge_cmd = bridge_start[bridge_start.index("bridge_cmd = ["):bridge_start.index("proc = subprocess.Popen", bridge_start.index("bridge_cmd = ["))]
    assert '"--reload"' not in bridge_cmd
    assert "stderr=subprocess.PIPE" not in discovery_start
    assert "stdout=log_file" in discovery_start and "stderr=subprocess.STDOUT" in discovery_start
    assert "def _try_topology_read_fallback(self, method):" in serve
    assert "store.list_domains(user)" in serve
    assert "store.list_topologies(user, parts[2])" in serve
    assert "store.load_topology(user, parts[2], parts[4])" in serve
    assert "topo_files" in serve and "Move or delete individual topologies before deleting the domain." in serve
    assert "oauth-protected-resource" in serve
    assert "oauth-protected-resource" in scaler_bridge


def _assert_destructive_domain_delete_contract() -> None:
    """Domain/section deletes must never cascade-delete topology files."""
    serve = (ROOT / "serve.py").read_text(encoding="utf-8")
    domains_router = (ROOT / "api" / "domains" / "router.py").read_text(encoding="utf-8")
    user_store_src = (ROOT / "api" / "auth" / "user_store.py").read_text(encoding="utf-8")
    assert "Domain contains {len(topologies)} topology file(s)." in domains_router
    assert "SELECT COUNT(*) FROM topologies WHERE domain_id = ?" in user_store_src
    assert "if int(topo_count or 0) > 0:" in user_store_src
    section_delete = serve[serve.index('if path.startswith("/api/sections/") and path.endswith("/delete"):'):serve.index('if path == "/api/sections/update":')]
    assert "topo_files" in section_delete
    assert "return True" in section_delete[section_delete.index("if topo_files:"):]


def _assert_domain_topology_quota_contract() -> None:
    """Every create path must enforce the 15-topology per-domain cap."""
    serve = (ROOT / "serve.py").read_text(encoding="utf-8")
    domains_router = (ROOT / "api" / "domains" / "router.py").read_text(encoding="utf-8")
    user_store_src = (ROOT / "api" / "auth" / "user_store.py").read_text(encoding="utf-8")
    file_ops = (ROOT / "topology-file-ops.js").read_text(encoding="utf-8")
    bugs_js = (ROOT / "topology-bugs.js").read_text(encoding="utf-8")
    assert "DOMAIN_TOPOLOGY_LIMIT = 15" in user_store_src
    assert "class DomainTopologyLimitError" in user_store_src
    assert "code\": \"domain-topology-limit\"" in user_store_src
    assert "if len(existing) >= DOMAIN_TOPOLOGY_LIMIT:" in user_store_src
    assert 'path.endswith("/topologies/cleanup")' in serve
    assert "DOMAIN_TOPOLOGY_LIMIT = 15" in serve
    assert "if len(existing_topologies) >= DOMAIN_TOPOLOGY_LIMIT:" in serve
    assert "len(self._section_topology_files(user, dest_sid)) >= DOMAIN_TOPOLOGY_LIMIT" in serve
    assert "@router.post(\"/{domain_id}/topologies/cleanup\")" in domains_router
    assert "except DomainTopologyLimitError as exc:" in domains_router
    assert "domain-topology-limit" in file_ops
    assert "_openDomainCleanupPrompt" in file_ops
    assert "clean-domain" in file_ops
    assert "window.FileOps._isDomainLimitResult(json)" in bugs_js


def _assert_bug_topology_mcp_contract() -> None:
    """Bug topology generation must be available as a first-class MCP tool."""
    server_src = (ROOT / "mcp" / "server.py").read_text(encoding="utf-8")
    tool_src = (ROOT / "mcp" / "tools" / "bug_topology.py").read_text(encoding="utf-8")
    assert "def topology_create_bug_topology(" in server_src
    assert 'dispatch(\n            "topology_create_bug_topology"' in server_src
    assert "POST /api/bugs/from-jira" in tool_src
    assert '"/api/bugs/from-jira"' in tool_src
    assert '"section_id": result.get("section_id") or "__bugs"' in tool_src
    assert "topology_create_bug_topology" in list_tool_names()
    schema = tool_schemas()["topology_create_bug_topology"]["input_schema"]
    assert "sw_id" in schema["required"]
    assert schema["properties"]["devices"]["type"] == "array"
    assert schema["properties"]["route"]["type"] == "object"


def _assert_packet_object_contract() -> None:
    """Layered packet/frame canvas object must be wired end-to-end."""
    # Frontend modules must exist and expose the required methods/popup.
    packets_js = (ROOT / "topology-packets.js").read_text(encoding="utf-8")
    popup_js = (ROOT / "topology-packet-popup.js").read_text(encoding="utf-8")
    assert "function createPacket(" in packets_js
    assert "function attachPacketToLink(" in packets_js
    assert "function updatePacketPosition(" in packets_js
    assert "function findPacketAt(" in packets_js
    assert "function drawPacket(" in packets_js
    assert "function projectCursorToLinkT(" in packets_js
    assert "function findPacketResizeHandle(" in packets_js
    assert "function findPacketSummaryHit(" in packets_js
    assert "function getPacketSummaryBounds(" in packets_js
    assert "packet.userWidth" in packets_js
    assert "packet.groupColor" in packets_js
    assert "packet.summary" in packets_js
    assert "window.PacketMethods" in packets_js
    assert "LAYER_VALIDATORS" in popup_js
    assert "_filterValue" in popup_js
    assert "layer.freeText" in popup_js
    assert "showSummaryEditor" in popup_js
    assert "window.PacketPopup" in popup_js
    # Renderer must update positions before sort/draw, hit-test must include packets.
    draw_js = (ROOT / "topology-draw.js").read_text(encoding="utf-8")
    assert "obj.type === 'packet'" in draw_js
    assert "PacketMethods.updatePacketPosition" in draw_js
    assert "PacketMethods.drawPacket" in draw_js
    detect_js = (ROOT / "topology-object-detection.js").read_text(encoding="utf-8")
    assert "'packet':" in detect_js
    assert "findPacketSummaryHit" in detect_js
    mouse_move_js = (ROOT / "topology-mouse-move.js").read_text(encoding="utf-8")
    assert "obj.type === 'packet' && obj.linkId" in mouse_move_js
    assert "editor.resizingPacket" in mouse_move_js
    mouse_down_js = (ROOT / "topology-mouse-down.js").read_text(encoding="utf-8")
    assert "findPacketResizeHandle" in mouse_down_js
    assert "showSummaryEditor" in mouse_down_js
    mouse_up_js = (ROOT / "topology-mouse-up.js").read_text(encoding="utf-8")
    assert "editor.resizingPacket" in mouse_up_js
    # Core orchestrator wrappers + counter persistence.
    core_js = (ROOT / "topology.js").read_text(encoding="utf-8")
    assert "this.packetIdCounter = 0" in core_js
    assert "createPacket(x, y, options)" in core_js
    assert "showPacketSelectionToolbar(packet)" in core_js
    assert "packetIdCounter: this.packetIdCounter" in core_js
    files_js = (ROOT / "topology-files.js").read_text(encoding="utf-8")
    assert "packet: this.editor.packetIdCounter" in files_js
    assert "this.editor.packetIdCounter = data.counters.packet" in files_js
    file_ops_js = (ROOT / "topology-file-ops.js").read_text(encoding="utf-8")
    assert "'packetIdCounter'" in file_ops_js
    # Link toolbar must expose Add Packet next to Add Text.
    link_tb_js = (ROOT / "topology-link-toolbar.js").read_text(encoding="utf-8")
    assert "'Add Packet'" in link_tb_js
    assert "'packet', 'Add Packet'" in link_tb_js
    # index.html must load both new modules and ship the packet icon symbol.
    index_html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "topology-packets.js?v=" in index_html
    assert "topology-packet-popup.js?v=" in index_html
    assert 'id="ico-packet"' in index_html
    # Backend bug-topology generator must emit packet objects when route info is present.
    serve_src = (ROOT / "serve.py").read_text(encoding="utf-8")
    assert '"type": "packet"' in serve_src
    assert "linkAttachT" in serve_src
    assert "_packet_direction_for_link" in serve_src
    assert "_packet_summary_from_route" in serve_src
    assert '"packetIdCounter": packet_id_counter' in serve_src
    # MCP imports planner must expose attach_packets across all 3 tools.
    imports_src = (ROOT / "mcp" / "tools" / "imports.py").read_text(encoding="utf-8")
    assert "def _attach_packets_to_links(" in imports_src
    assert "attach_packets: bool = False" in imports_src
    assert "def _packet_direction(" in imports_src
    assert "def _packet_summary(" in imports_src
    server_src = (ROOT / "mcp" / "server.py").read_text(encoding="utf-8")
    assert server_src.count("attach_packets: bool = False") >= 3
    # Tool schemas auto-derived from signatures must surface the new boolean.
    # NOTE: the dispatcher's schema generator currently treats annotations as
    # strings (`from __future__ import annotations` defers evaluation), so the
    # generated `type` is always `string` for bool params -- same as the existing
    # `auto_layout` boolean. We assert presence + parity with `auto_layout`
    # rather than the JSON Schema `boolean` type.
    schemas = tool_schemas()
    for tool in ("topology_plan_from_network_mapper",
                 "topology_plan_from_dnos_json",
                 "topology_plan_from_image"):
        props = schemas[tool]["input_schema"]["properties"]
        assert "attach_packets" in props, tool
        assert "attach_packets" not in (schemas[tool]["input_schema"].get("required") or []), tool
    image_props = schemas["topology_plan_from_image"]["input_schema"]["properties"]
    # parity check: same generated shape as the long-standing auto_layout bool
    assert image_props["attach_packets"] == image_props["auto_layout"], image_props


def _as_user(username: str, tool: str, args: dict):
    token = current_mcp_user.set(username)
    try:
        return dispatch(tool, args)
    finally:
        current_mcp_user.reset(token)


def _ensure_user(username: str) -> None:
    if not user_store.get_user(username):
        user_store.create_user(username, "test-password", username, role="engineer")


def main() -> None:
    _assert_mcp_streaming_middleware_contract()
    _assert_destructive_domain_delete_contract()
    _assert_domain_topology_quota_contract()
    _assert_bug_topology_mcp_contract()
    _assert_packet_object_contract()
    suffix = uuid.uuid4().hex[:8]
    user_a = f"mcp_a_{suffix}"
    user_b = f"mcp_b_{suffix}"
    _ensure_user(user_a)
    _ensure_user(user_b)
    try:
        domain = _as_user(user_a, "topology_create_domain", {"name": "MCP Smoke"})["domain"]
        topo = _as_user(
            user_a,
            "topology_create_topology",
            {
                "domain_id": domain["id"],
                "name": "Private",
                "state_json": {
                    "objects": [
                        {"id": "pe1", "type": "device", "label": "PE-1", "role": "pe", "x": 0, "y": 0},
                        {"id": "pe2", "type": "device", "label": "PE-2", "role": "pe", "x": 100, "y": 0},
                        {"id": "rr1", "type": "device", "label": "RR-1", "role": "rr", "x": 50, "y": 100},
                        {"id": "l1", "type": "link", "source": "pe1", "target": "pe2"},
                    ]
                },
            },
        )["topology"]

        group = _as_user(
            user_a,
            "topology_create_group",
            {
                "domain_id": domain["id"],
                "topology_id": topo["id"],
                "member_ids": ["pe1", "pe2"],
                "name": "PE Pair",
                "group_id": "group_pe_pair",
            },
        )
        assert group["ok"] is True, group
        assert group["group"]["leader_id"] in {"pe1", "pe2"}, group
        groups = _as_user(user_a, "topology_list_groups", {"domain_id": domain["id"], "topology_id": topo["id"]})
        assert groups["count"] == 1, groups

        batch = _as_user(
            user_a,
            "topology_batch_update_objects",
            {
                "domain_id": domain["id"],
                "topology_id": topo["id"],
                "patches": [{"id": "rr1", "fields": {"site": "lab-a"}}],
            },
        )
        assert batch["ok"] is True and batch["count"] == 1, batch

        validation = _as_user(
            user_a,
            "topology_validate_topology",
            {"domain_id": domain["id"], "topology_id": topo["id"]},
        )
        assert validation["ok"] is True and validation["valid"] is True, validation

        invalid = _as_user(
            user_a,
            "topology_validate_topology",
            {"state_json": {"objects": [{"id": "bad-link", "type": "link", "source": "missing", "target": "pe1"}]}},
        )
        assert invalid["ok"] is True and invalid["valid"] is False, invalid
        assert any(issue["kind"] == "missing_link_endpoint" for issue in invalid["issues"]), invalid

        b_list = _as_user(user_b, "topology_list_topologies", {"domain_id": domain["id"]})
        assert b_list.get("ok") is False, b_list

        b_get = _as_user(
            user_b,
            "topology_get_topology",
            {"domain_id": domain["id"], "topology_id": topo["id"]},
        )
        assert b_get.get("ok") is False, b_get

        _as_user(
            user_a,
            "topology_share_domain",
            {"domain_id": domain["id"], "target_users": [user_b], "permission": "view"},
        )
        shared = _as_user(user_b, "topology_list_domains", {})
        assert any(d.get("id") == domain["id"] for d in shared["domains"]), shared

        b_save = _as_user(
            user_b,
            "topology_save_topology",
            {
                "domain_id": domain["id"],
                "topology_id": topo["id"],
                "name": "Should Fail",
                "state_json": {"objects": []},
            },
        )
        assert b_save.get("ok") is False, b_save

        b_group = _as_user(
            user_b,
            "topology_create_group",
            {
                "domain_id": domain["id"],
                "topology_id": topo["id"],
                "member_ids": ["pe1", "pe2"],
                "name": "Should Fail",
            },
        )
        assert b_group.get("ok") is False, b_group

        preview = _as_user(
            user_a,
            "topology_plan_from_network_mapper",
            {
                "network_mapper_json": {
                    "devices": [
                        {"id": "a", "hostname": "A", "role": "leaf"},
                        {"id": "b", "hostname": "B", "role": "leaf"},
                    ],
                    "links": [{"fromDevice": "a", "toDevice": "b", "protocol": "LLDP"}],
                },
                "name": "Preview",
            },
        )
        assert preview["ok"] is True and preview["dry_run"] is True, preview
        assert preview["plan"]["summary"]["device_count"] == 2, preview
        assert _as_user(user_a, "topology_list_topologies", {"domain_id": domain["id"]})["count"] == 1

        created = _as_user(
            user_a,
            "topology_create_from_plan",
            {"domain_id": domain["id"], "plan_json": preview["plan"]},
        )
        assert created["ok"] is True, created
        assert _as_user(user_a, "topology_list_topologies", {"domain_id": domain["id"]})["count"] == 2

        # /TOPOLOGY image flow: agent extracts a payload from a chat image
        # (label, role, X/Y read from the diagram) and previews via
        # topology_plan_from_image. Default auto_layout=False MUST preserve the
        # agent-derived coordinates so the saved canvas matches what the user
        # drew.
        image_payload = {
            "devices": [
                {
                    "label": "PE-1",
                    "deviceType": "PE",
                    "role": "PE",
                    "x": 220,
                    "y": 220,
                    "style": {"visualStyle": "classic", "color": "#0ea5e9", "radius": 46},
                },
                {
                    "label": "PE-2",
                    "deviceType": "PE",
                    "role": "PE",
                    "x": 980,
                    "y": 220,
                    "deviceStyle": "classic",
                    "color": "#16a34a",
                    "labelColor": "#f8fafc",
                },
                {"label": "P-1", "deviceType": "P", "role": "P", "x": 600, "y": 80},
            ],
            "links": [
                {
                    "source": "PE-1",
                    "target": "P-1",
                    "label": "ge-0/0/0",
                    "style": {"lineStyle": "dashed-arrow", "strokeColor": "#ffffff", "strokeWidth": 3},
                },
                {"source": "PE-2", "target": "P-1", "label": "ge-0/0/1", "lineStyle": "dotted", "color": "#22c55e"},
            ],
            "groups": [
                {"name": "Provider Edge", "members": ["PE-1", "PE-2"], "color": "#0ea5e9"},
            ],
            "shapes": [
                {"label": "IRB", "x": 520, "y": 20, "width": 240, "height": 80, "fillColor": "#111827"},
            ],
            "texts": [
                {"text": "IRB\nIP = 100.100.100.1/24", "x": 640, "y": 60},
            ],
        }
        image_preview = _as_user(
            user_a,
            "topology_plan_from_image",
            {"image_extraction_json": image_payload, "name": "Image Preview"},
        )
        assert image_preview["ok"] is True and image_preview["dry_run"] is True, image_preview
        assert image_preview["plan"]["source"] == "chat-image", image_preview
        assert image_preview["plan"]["summary"]["device_count"] == 3, image_preview
        image_devices = {
            obj["label"]: obj
            for obj in image_preview["plan"]["state"]["objects"]
            if obj.get("type") == "device"
        }
        assert image_devices["PE-1"]["x"] == 220 and image_devices["PE-1"]["y"] == 220, image_devices
        assert image_devices["PE-2"]["x"] == 980 and image_devices["PE-2"]["y"] == 220, image_devices
        assert image_devices["P-1"]["x"] == 600 and image_devices["P-1"]["y"] == 80, image_devices
        assert image_devices["PE-1"]["visualStyle"] == "classic", image_devices
        assert image_devices["PE-1"]["color"] == "#0ea5e9" and image_devices["PE-1"]["radius"] == 46, image_devices
        assert image_devices["PE-2"]["visualStyle"] == "classic" and image_devices["PE-2"]["color"] == "#16a34a", image_devices
        assert image_devices["P-1"]["visualStyle"] == "classic", image_devices
        assert image_devices["PE-1"]["groupName"] == "Provider Edge", image_devices
        assert image_devices["PE-2"]["groupId"] == image_devices["PE-1"]["groupId"], image_devices
        image_objects = image_preview["plan"]["state"]["objects"]
        image_links = {obj["label"]: obj for obj in image_objects if obj.get("type") == "link"}
        assert image_links["ge-0/0/0"]["style"] == "dashed-arrow", image_links
        assert image_links["ge-0/0/0"]["color"] == "#ffffff" and image_links["ge-0/0/0"]["width"] == 3, image_links
        assert image_links["ge-0/0/1"]["style"] == "dotted" and image_links["ge-0/0/1"]["color"] == "#22c55e", image_links
        assert any(obj.get("type") == "shape" and obj.get("label") == "IRB" for obj in image_objects), image_objects
        assert any(obj.get("type") == "text" and "100.100.100.1/24" in obj.get("text", "") for obj in image_objects), image_objects

        # auto_layout=True MUST override agent positions with the deterministic
        # row layout (used when the image was too sparse for usable coordinates).
        image_preview_layout = _as_user(
            user_a,
            "topology_plan_from_image",
            {
                "image_extraction_json": image_payload,
                "name": "Image Preview Auto-Layout",
                "auto_layout": True,
            },
        )
        assert image_preview_layout["ok"] is True, image_preview_layout
        layout_devices = {
            obj["label"]: obj
            for obj in image_preview_layout["plan"]["state"]["objects"]
            if obj.get("type") == "device"
        }
        # auto_layout always overrides at least one extracted coordinate; the
        # original (220, 220) PE-1 won't survive the row layout.
        assert (
            layout_devices["PE-1"]["x"] != 220 or layout_devices["PE-1"]["y"] != 220
        ), layout_devices

        # Save the preserved-positions preview into the same domain to prove the
        # full image -> create_from_plan path works end-to-end.
        image_saved = _as_user(
            user_a,
            "topology_create_from_plan",
            {"domain_id": domain["id"], "plan_json": image_preview["plan"]},
        )
        assert image_saved["ok"] is True, image_saved
        assert _as_user(user_a, "topology_list_topologies", {"domain_id": domain["id"]})["count"] == 3

        # attach_packets=True must auto-emit one layered packet chip per link
        # that carries protocol/vrf/bd/interface metadata. Empty rows must be
        # pre-collapsed (visible=false) so the chip stays compact.
        packet_payload = {
            "devices": [
                {"label": "PE-1", "deviceType": "PE", "role": "PE", "x": 100, "y": 100},
                {"label": "PE-2", "deviceType": "PE", "role": "PE", "x": 600, "y": 100},
            ],
            "links": [
                {
                    "source": "PE-1",
                    "target": "PE-2",
                    "label": "iBGP",
                    "protocol": "BGP",
                    "vrf": "RED",
                    "bd": "g_yor_v211",
                    "fromInterface": "ge100-0/0/4",
                    "toInterface": "ge100-0/0/5",
                },
            ],
        }
        packet_preview = _as_user(
            user_a,
            "topology_plan_from_image",
            {
                "image_extraction_json": packet_payload,
                "name": "Packet Preview",
                "attach_packets": True,
            },
        )
        assert packet_preview["ok"] is True, packet_preview
        packet_objs = [
            obj
            for obj in packet_preview["plan"]["state"]["objects"]
            if obj.get("type") == "packet"
        ]
        assert len(packet_objs) == 1, packet_preview
        pkt = packet_objs[0]
        assert pkt.get("linkId"), pkt
        assert pkt.get("title") in ("iBGP", "Frame", "BGP"), pkt
        assert pkt.get("direction") == "forward", pkt
        assert pkt.get("summary") == "BGP UPD", pkt
        layer_index = {row["id"]: row for row in pkt.get("layers", [])}
        assert layer_index["L2"]["visible"] is True and "ge100-0/0/4" in layer_index["L2"]["text"], pkt
        assert layer_index["VLAN"]["visible"] is True and layer_index["VLAN"]["text"] == "g_yor_v211", pkt
        assert layer_index["MPLS"]["visible"] is True and "vrf RED" in layer_index["MPLS"]["text"], pkt
        # L3 has no source/dest IP in this payload so it must stay collapsed.
        assert layer_index["L3"]["visible"] is False, pkt
        assert layer_index["L4"]["visible"] is True and layer_index["L4"]["text"] == "BGP", pkt
        assert (
            packet_preview["plan"]["state"]["metadata"].get("packetIdCounter") == 1
        ), packet_preview
        # Default (attach_packets omitted) must NOT emit packets.
        no_packet_preview = _as_user(
            user_a,
            "topology_plan_from_image",
            {"image_extraction_json": packet_payload, "name": "No Packets"},
        )
        assert no_packet_preview["ok"] is True, no_packet_preview
        assert not any(
            obj.get("type") == "packet"
            for obj in no_packet_preview["plan"]["state"]["objects"]
        ), no_packet_preview

        # /TOPOLOGY bug SW-XXXXX with a route hint must auto-emit one packet
        # chip on the link entering the failure device. Use a non-strict bug
        # path here -- this is just smoke for the auto-emit branch in
        # serve.py:_build_bug_topology_json. The class is named `Handler`,
        # and the builder is a staticmethod so we can call it without an
        # http server instance.
        from serve import Handler as _BugBuilder  # noqa: E402
        bug_state = _BugBuilder._build_bug_topology_json(
            "SW-PACKETSMOKE",
            title="Packet auto-emit smoke",
            summary="symptom example",
            devices=[
                {"label": "CE-A"},
                {"label": "PE-1"},
                {"label": "PE-2"},
            ],
            route={"dst": "10.0.0.1", "src": "10.0.0.2", "action": "drop", "protocol": "BGP"},
            failure_device="CE-A",
            ticket_url="",
            source="placeholder",
            issue_type="Bug",
        )
        bug_packets = [obj for obj in bug_state["objects"] if obj.get("type") == "packet"]
        assert len(bug_packets) == 1, bug_state
        bug_pkt = bug_packets[0]
        assert bug_pkt.get("linkId") and bug_pkt["linkId"].startswith("link_"), bug_pkt
        assert bug_pkt.get("direction") == "backward", bug_pkt
        assert bug_pkt.get("summary") == "BGP UPD", bug_pkt
        bug_layer_index = {row["id"]: row for row in bug_pkt.get("layers", [])}
        assert bug_layer_index["L3"]["visible"] is True, bug_pkt
        assert "10.0.0.2" in bug_layer_index["L3"]["text"] and "10.0.0.1" in bug_layer_index["L3"]["text"], bug_pkt
        assert bug_layer_index["L4"]["visible"] is True, bug_pkt
        assert "drop" in bug_layer_index["L4"]["text"], bug_pkt
        assert bug_state["metadata"].get("packetIdCounter") == 1, bug_state

        _as_user(
            user_a,
            "topology_unshare_domain",
            {"domain_id": domain["id"], "target_user": user_b},
        )
        revoked = _as_user(user_b, "topology_list_domains", {})
        assert not any(d.get("id") == domain["id"] for d in revoked["domains"]), revoked
        print("topology MCP isolation smoke passed")
    finally:
        user_store.delete_user(user_a)
        user_store.delete_user(user_b)


if __name__ == "__main__":
    main()

