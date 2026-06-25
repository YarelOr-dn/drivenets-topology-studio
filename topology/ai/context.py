"""Live per-user context + tool schema for the AI assistant.

build_live_context(username, canvas_snapshot) is called on every chat
turn. It returns a small (<6 KB) JSON blob that the router serializes
into a system message. Keep the budget tight -- we want the model to
think about the user's question, not re-read their whole workspace.

All reads are per-user via user_store. Anything we cannot read (a
store that does not yet exist for this user) is quietly omitted so a
single missing file never breaks chat.
"""

from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from api.auth.user_store import user_store
except Exception:  # pragma: no cover
    user_store = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Tool schema for create_topology.
# ---------------------------------------------------------------------------
# Kept deliberately permissive: the backend validator
# (normalize_topology_payload) enforces the hard invariants before the
# payload touches disk. The LLM sees this schema every turn.
TOPOLOGY_TOOL_SCHEMA: Dict[str, Any] = {
    "name": "create_topology",
    "description": (
        "Generate a new topology for the user. The topology is returned to "
        "the UI as a pending placement card: the user then chooses an "
        "existing domain or creates a new named one -- we no longer auto-"
        "save to a hidden 'AI' domain. ONLY call this when the user asks "
        "to create / build / make a topology -- do NOT call it to answer a "
        "'how does X work?' question.\n\n"
        "LAYOUT: Either provide `x`/`y` coordinates for every device (canvas "
        "space, devices readable between 100..2400 on X and 100..1400 on Y, "
        "spacing >= 180px) OR provide `layout_hint` and let the server "
        "auto-place devices on a canonical grid. Do NOT stack devices at "
        "(0,0) -- the canvas treats that as unpositioned.\n\n"
        "SCALE: `realism_scale` (small/medium/large/enterprise) hints at "
        "device count. Prefer PROFESSIONAL scenarios drawn from the Blueprint "
        "Library section of the knowledge digest.\n\n"
        "QUALITY: Generate a topology that is detailed but not noisy. Default "
        "to 5-10 devices unless the user asks for more, include only the "
        "devices needed to explain the requested protocol or service, and add "
        "2-5 short annotations (text boxes) that explain the control-plane "
        "flow, AS/area/VRF/RD/RT/VNI details, source/receiver roles, or failure "
        "domain. Use grouping shapes for AS, site, OSPF area, tenant, or "
        "multicast domain boundaries. Use semantic `linkType`, link color/style, "
        "and short labels so the canvas itself teaches the scenario without "
        "becoming a wall of text. Text annotations must be short chips placed "
        "outside device icons and away from other text; never stack multiple "
        "text objects at one coordinate. Adapt names, counts, IPs, and labels "
        "to the user's exact ask; do not return a generic blueprint unchanged.\n\n"
        "DETAIL CONTRACT (mandatory for conceptual topologies -- the canvas "
        "must look like a real lab even when the user did not provide IPs):\n"
        "  * EVERY device MUST carry an `ip` (loopback /32 like `10.0.0.1`, "
        "`10.0.0.2`, ...). Use the same /16 across the topology so the IPs "
        "look related. Devices in different ASes may use different /16s.\n"
        "  * Devices that play a routing role MUST carry a `role` AND a "
        "matching `visualStyle` (see knowledge digest).\n"
        "  * EVERY link SHOULD carry `interface1` and `interface2` (e.g. "
        "`ge100-0/0/1`, `Eth0/1`) and a `linkDetails` blob with the "
        "per-link IPs (e.g. {`ip1`: `10.10.0.1/31`, `ip2`: `10.10.0.0/31`}). "
        "For protocol links, also stamp the protocol-specific facts in "
        "`linkDetails` (e.g. `as1`/`as2` for eBGP, `area` for OSPF, `level` "
        "for IS-IS, `rd`/`rt` for L3VPN, `vni`/`bd` for EVPN-VXLAN, `vlan` "
        "for L2 trunks). Pick non-overlapping /31 (P2P) or /30 (legacy) "
        "subnets so two adjacent links never reuse the same IPs.\n"
        "  * Annotation text boxes for AS / area / VRF / VNI MUST include "
        "the dummy numeric value (e.g. `AS 65001\\n10.0.0.0/24`, "
        "`Area 0`, `VRF cust-A\\nRD 65000:100\\nRT 65000:100`).\n"
        "  * NEVER emit blank IPs / empty interfaces / zero AS numbers. Pick "
        "plausible RFC1918 / 100.64.0.0/10 (carrier) ranges.\n\n"
        "GROUPING CONTRACT: When you emit a `shape` that wraps devices "
        "(AS box, OSPF area, tenant frame, site rectangle), set "
        "`containerMode: true` on that shape AND size it so every wrapped "
        "device's centre falls inside the shape. The canvas then treats "
        "the shape as a CONTAINER -- dragging the shape moves every "
        "object whose centre is inside it as a single unit, while the "
        "user can still click the inner devices independently to edit "
        "them. This lets the user reorganise the diagram by AS/area "
        "without losing the per-object handles. Do NOT set "
        "`containerMode: true` on cross / checkmark / arrow / line / "
        "diamond callouts -- only on rectangle / ellipse / cloud "
        "boundaries that wrap multiple devices."
    ),
    "parameters": {
        "type": "object",
        "required": ["name", "objects"],
        "properties": {
            "name": {
                "type": "string",
                "description": (
                    "Short, file-safe name for the topology (1-60 chars). "
                    "Letters, digits, dashes, underscores, and spaces only."
                ),
            },
            "summary": {
                "type": "string",
                "description": "One-sentence description of what this topology represents.",
            },
            # Server-side layout hint. The backend uses this PLUS the graph
            # to auto-place any device that is missing x/y. Pass whichever
            # one best matches the scenario; the backend falls back to
            # "auto" (graph-based detection) if omitted.
            "layout_hint": {
                "type": "string",
                "description": (
                    "Optional structural hint for auto-layout when devices "
                    "omit x/y. `clos-3-stage` = spines on top row, leaves "
                    "below. `clos-5-stage` = super-spines / spines / leaves "
                    "on three rows. `hub-spoke` = 1 central + N around. "
                    "`ring` = single cycle. `path` = horizontal chain. "
                    "`mesh` = grid of near-full-mesh peers. `tree` = "
                    "hierarchical root-down. `campus` = core/dist/access "
                    "3-tier. `sp-backbone` = PE/P/RR dumbbell. "
                    "`dual-homed` = 2 PEs + 1 CE dual-attached. "
                    "`metro-ring` = Ethernet access ring. `auto` = let "
                    "the server detect from the graph."
                ),
                "enum": [
                    "auto", "clos-3-stage", "clos-5-stage", "hub-spoke",
                    "ring", "path", "mesh", "tree", "campus",
                    "sp-backbone", "dual-homed", "metro-ring",
                ],
            },
            "realism_scale": {
                "type": "string",
                "description": (
                    "Size preset: `small` (2-6 devices, single-site demo); "
                    "`medium` (6-14 devices, site-level scenario); "
                    "`large` (14-30 devices, multi-site SP/DC); "
                    "`enterprise` (30-60 devices, full-fabric reference). "
                    "Use this to pick a realistic device count if the user "
                    "did not specify one."
                ),
                "enum": ["small", "medium", "large", "enterprise"],
            },
            "objects": {
                "type": "array",
                "description": (
                    "All canvas objects. Order: devices first, then links, then "
                    "shapes (optional), then text (optional). IDs must be unique. "
                    "Devices SHOULD include `x` and `y` in canvas space (spacing "
                    ">= 180 px between neighbours) unless `layout_hint` is set -- "
                    "if omitted, the server auto-places using the hint or graph "
                    "detection."
                ),
                "items": {
                    "type": "object",
                    "required": ["id", "type"],
                    "properties": {
                        "id": {"type": "string"},
                        "type": {
                            "type": "string",
                            "enum": ["device", "link", "text", "shape"],
                        },
                        # Device-specific.
                        # x/y are strongly recommended but not required at
                        # the schema level so the server can apply smart
                        # auto-layout when the model forgets. The backend
                        # always delivers a canvas-ready payload.
                        "x": {
                            "type": "number",
                            "description": (
                                "Canvas X (world coords). Prefer 100..2400. "
                                "Neighbouring devices should be >= 180 px "
                                "apart. Omit ONLY if `layout_hint` is set."
                            ),
                        },
                        "y": {
                            "type": "number",
                            "description": (
                                "Canvas Y (world coords). Prefer 100..1400. "
                                "Tiers stack on separate Y bands (300 px "
                                "apart). Omit ONLY if `layout_hint` is set."
                            ),
                        },
                        "label": {"type": "string"},
                        "ip": {"type": "string"},
                        "deviceType": {"type": "string"},
                        "visualStyle": {
                            "type": "string",
                            "description": (
                                "Device visual rendering style. classic = "
                                "DriveNets classic router icon (best for "
                                "PE/P/RR). server = server chassis icon "
                                "(ExaBGP/test hosts). simple = simple box "
                                "(CE/leaf minimal). circle = plain circle "
                                "(default/generic). hex = hexagon (special "
                                "role like RR / anycast VTEP)."
                            ),
                            "enum": [
                                "classic", "server", "simple", "circle", "hex",
                            ],
                        },
                        "color": {"type": "string", "description": "Hex color like '#3498db'."},
                        # `role` is a tier hint used by the server layout
                        # engine. Accepted values include: super-spine,
                        # spine, leaf, pe, p, rr, ce, cpe, core, dist,
                        # access, border. Free-form strings still render.
                        "role": {
                            "type": "string",
                            "description": (
                                "Tier hint used by auto-layout: "
                                "super-spine, spine, leaf, pe, p, rr, ce, "
                                "core, dist, access, border."
                            ),
                        },
                        "radius": {
                            "type": "number",
                            "description": "Device icon radius in world px (default ~40). Bumps for important nodes like RR/ABR.",
                        },
                        # Link-specific
                        "device1": {"type": "string"},
                        "device2": {"type": "string"},
                        "connectionPoint": {
                            "type": "object",
                            "properties": {
                                "x": {"type": "number"},
                                "y": {"type": "number"},
                            },
                        },
                        "linkType": {
                            "type": "string",
                            "description": (
                                "Semantic link category. Drives default "
                                "color/style when `color`/`style` are not "
                                "set. Recognised: default, bgp, ebgp, "
                                "ibgp, ospf, isis, mpls, ldp, rsvp, "
                                "sr-mpls, srv6, evpn, vxlan, pw, vpws, "
                                "l2vpn, l3vpn, dnaas, bul, lag."
                            ),
                        },
                        "interface1": {
                            "type": "string",
                            "description": (
                                "Interface name on `device1` end of the "
                                "link (e.g. `ge100-0/0/1`, `Eth0/1`). "
                                "Surfaced in the link-table popup. "
                                "REQUIRED for conceptual topologies."
                            ),
                        },
                        "interface2": {
                            "type": "string",
                            "description": (
                                "Interface name on `device2` end of the "
                                "link. REQUIRED for conceptual topologies."
                            ),
                        },
                        "vlan": {
                            "type": "string",
                            "description": "VLAN id for L2 trunks (string).",
                        },
                        "bd": {
                            "type": "string",
                            "description": "Bridge-domain name for EVPN/L2.",
                        },
                        "linkDetails": {
                            "type": "object",
                            "description": (
                                "Free-form per-link facts surfaced in the "
                                "link-table popup. Conceptual topologies "
                                "MUST stamp at least `ip1`/`ip2` (e.g. "
                                "`10.10.0.0/31` and `10.10.0.1/31`), and "
                                "should add protocol-specific facts: "
                                "`as1`/`as2` for eBGP, `area` for OSPF, "
                                "`level` for IS-IS, `rd`/`rt`/`vrf` for "
                                "L3VPN, `vni`/`bd`/`vlan` for EVPN/VXLAN, "
                                "`label` for MPLS, `metric` for IGP."
                            ),
                            "additionalProperties": True,
                        },
                        "style": {
                            "type": "string",
                            "enum": [
                                "solid", "dashed", "dashed-wide", "dotted",
                                "arrow", "double-arrow",
                                "dashed-arrow", "dashed-double-arrow",
                            ],
                            "description": (
                                "Link line style. Overrides the protocol "
                                "default from `linkType`."
                            ),
                        },
                        "width": {
                            "type": "number",
                            "description": (
                                "Width in px. Devices/shapes also use "
                                "this for size; links use it for line "
                                "thickness. Bump to 3-4 for BUL/LAG."
                            ),
                        },
                        # Text-specific
                        "text": {"type": "string"},
                        "fontSize": {"type": "number"},
                        "showBackground": {"type": "boolean"},
                        "backgroundColor": {"type": "string"},
                        "backgroundOpacity": {"type": "number"},
                        "backgroundPadding": {"type": "number"},
                        "showBorder": {"type": "boolean"},
                        "borderColor": {"type": "string"},
                        "borderWidth": {"type": "number"},
                        # Shape-specific
                        "height": {"type": "number"},
                        "shapeType": {
                            "type": "string",
                            "enum": [
                                "rectangle", "ellipse", "oval",
                                "line", "arrow",
                                "diamond", "cloud",
                                "cross", "checkmark",
                            ],
                            "description": (
                                "Shape kind. rectangle/ellipse for AS or "
                                "area groupings, cloud for Internet/WAN, "
                                "diamond for decision points, arrow for "
                                "direction indicators, cross for failure "
                                "markers, checkmark for healthy/validated."
                            ),
                        },
                        "fillColor": {"type": "string", "description": "Shape fill color (hex)."},
                        "fillOpacity": {
                            "type": "number",
                            "description": "Shape fill alpha 0..1 (use 0.06-0.12 for AS/area grouping boxes).",
                        },
                        "fillEnabled": {"type": "boolean"},
                        "strokeColor": {"type": "string"},
                        "strokeWidth": {"type": "number"},
                        "strokeEnabled": {"type": "boolean"},
                        "cornerRadius": {
                            "type": "number",
                            "description": "Rectangle corner radius in px. Use 10-16 for rounded AS grouping boxes.",
                        },
                        "rotation": {
                            "type": "number",
                            "description": "Rotation in degrees (shapes only).",
                        },
                        "containerMode": {
                            "type": "boolean",
                            "description": (
                                "Shape-only. When true, the shape acts "
                                "as a CONTAINER: dragging it on the "
                                "canvas moves every object whose centre "
                                "falls inside the shape's bounding box "
                                "as a single unit (devices, text, "
                                "nested shapes, link endpoints). The "
                                "user can still click the inner objects "
                                "to edit them. Set this on every "
                                "rectangle / ellipse / cloud that wraps "
                                "an AS, OSPF / IS-IS area, VRF, tenant, "
                                "or physical site so the diagram stays "
                                "tidy when reorganised. Do NOT set on "
                                "callout markers (cross / checkmark / "
                                "arrow / line / diamond)."
                            ),
                        },
                        "opacity": {"type": "number"},
                    },
                },
            },
            "metadata": {
                "type": "object",
                "description": "Optional free-form metadata (version, notes, ...).",
                "additionalProperties": True,
            },
        },
    },
}


# ---------------------------------------------------------------------------
# apply_canvas_edits tool schema (2026-04-22).
#
# `create_topology` is the right tool when the user wants a WHOLE
# topology generated from scratch -- the output is saved to a domain
# and the user clicks "Load" to bring it onto the canvas.
#
# For "add a spine to my existing canvas", "connect those two routers",
# "rename leaf3 to spine2", etc., we need a SMALLER tool that returns a
# list of granular edits which the frontend applies IN-PLACE without
# replacing the whole canvas. That's this schema. The frontend
# (_applyCanvasEdits in topology-ai.js) consumes the emitted edits and
# calls editor.addDeviceAtPosition / editor.createLink / etc. on each
# one, with smart auto-placement for missing x/y.
#
# Why a separate tool (not a flag on create_topology):
#   * Different failure modes. create_topology needs a VALID topology
#     payload (connected graph, coordinate spread); apply_canvas_edits
#     can legitimately be "just add one link" -- we don't validate
#     whole-topology invariants.
#   * Different provenance. create_topology output is returned to the
#     UI as a pending placement and the user picks the destination
#     domain; apply_canvas_edits is a live patch that mutates the
#     in-memory canvas and the next auto-save captures the result.
#   * Different LLM prompt. create_topology says "build from scratch";
#     apply_canvas_edits says "here's the current canvas, modify it".
CANVAS_EDITS_TOOL_SCHEMA: Dict[str, Any] = {
    "name": "apply_canvas_edits",
    "description": (
        "Mutate the LIVE canvas in-place with a list of granular edits. "
        "Use this when the user asks to ADD / REMOVE / CONNECT / MOVE / "
        "RENAME one-or-more objects ON THE EXISTING CANVAS -- not when "
        "they ask for a whole new topology from scratch (use "
        "`create_topology` for that instead).\n\n"
        "APP TERMINOLOGY (critical -- users use these shorthands):\n"
        "  - 'UL' or 'unbound link' or 'unbounded link' or 'free link' "
        "-> use op=`add_unbound_link`. This is a link with BOTH "
        "endpoints floating -- it does NOT connect two devices. The "
        "user can drag the endpoints onto devices later.\n"
        "  - 'QL' or 'quick link' -> use op=`add_link` (regular "
        "device-to-device connection).\n"
        "  - 'BUL' or 'bundled link' or 'LAG' -> a chain of unbound "
        "links merged together. For creation, emit `add_unbound_link` "
        "entries and set `linkType='bul'`; the user merges them from "
        "the UI. DO NOT try to set `mergedWith`/`mergedInto` yourself.\n"
        "  - 'rename X to Y' -> use op=`relabel`.\n\n"
        "PLACEMENT RULES (decision order -- pick the FIRST that matches):\n"
        "  1. User gave EXPLICIT coordinates (\"at x=500, y=300\", "
        "\"at 100,200\") -> emit `x` + `y` exactly as asked.\n"
        "  2. User said 'between X and Y' -> read X.x, X.y, Y.x, Y.y "
        "from `current.devices[]` in the live context, emit "
        "`x: (X.x + Y.x) / 2, y: (X.y + Y.y) / 2`.\n"
        "  3. User said 'N pixels above/below/left/right of X' with "
        "an explicit distance -> read X.x, X.y, emit the shifted "
        "coords directly.\n"
        "  4. User said 'above/below/left/right of X' without a "
        "distance -> use the ANCHOR shortcut: set `anchor` to X's "
        "id-or-label and `anchor_position` to above/below/left/right. "
        "The executor picks sensible spacing.\n"
        "  5. User said 'top-left / centre / bottom-right / in the "
        "visible area' -> read `current.viewport.visible_world` "
        "({x, y, w, h, cx, cy}) and emit coords inside that rect. "
        "For 'top-left' use `x: visible_world.x + 80, y: "
        "visible_world.y + 80`. For 'centre' use `x: "
        "visible_world.cx, y: visible_world.cy`. ALWAYS clamp to "
        "within `visible_world` or the user can't see the result.\n"
        "  6. User just said 'add a spine' with NO placement hint -> "
        "omit `x`/`y`, set `role` (spine/leaf/pe/p/rr/ce/core/dist/"
        "access/border) so smart auto-layout picks a tier row.\n\n"
        "IMPORTANT: `current.devices[]` now includes `x` and `y` for "
        "every existing object (world coords, integer pixels). You "
        "MUST use these numbers when the user asks for relative or "
        "spatial placement -- don't guess. The viewport block tells "
        "you what the user is actually looking at right now, so "
        "emitted coords fall inside the visible rect unless the "
        "user asked otherwise.\n\n"
        "ID RESOLUTION: `from` / `to` / `id` / `anchor` can be either "
        "the numeric canvas id (e.g. `3`) OR the human label "
        "(e.g. `spine1`). If ambiguous (two devices share a label), "
        "the first match wins -- the frontend surfaces a warning in "
        "that case."
    ),
    "parameters": {
        "type": "object",
        "required": ["edits"],
        "properties": {
            "summary": {
                "type": "string",
                "description": "One-sentence natural-language summary of what this batch does (shown as a toast).",
            },
            "edits": {
                "type": "array",
                "description": "Ordered list of edits. Applied top-to-bottom so later edits can reference objects created by earlier ones.",
                "items": {
                    "type": "object",
                    "required": ["op"],
                    "properties": {
                        "op": {
                            "type": "string",
                            "enum": [
                                "add_device",
                                "add_link",
                                "add_unbound_link",
                                "add_text",
                                "add_shape",
                                "remove",
                                "move",
                                "relabel",
                                "style",
                                "select",
                                "zoom_to",
                                "create_domain",
                            ],
                            "description": (
                                "add_device: create a new device (label "
                                "required). add_link: connect two "
                                "existing devices by id-or-label "
                                "(from+to required) -- a.k.a. 'QL' / "
                                "'quick link'. Optional `color`, "
                                "`style`, `width`, `label`, `linkType` "
                                "drive the rendering (protocol colors "
                                "auto-apply from linkType). Optional "
                                "link-table fields `interface1`, "
                                "`interface2`, `vlan`, `bd`, "
                                "`linkDetails` populate the link-table "
                                "popup (set them when you have real "
                                "interface / VLAN / BD data from the "
                                "topology-generator preview or the "
                                "user). "
                                "add_unbound_link: drop a "
                                "free-ended link (both endpoints float, "
                                "no device connection required) -- "
                                "a.k.a. 'UL' / 'unbounded link'. Pair "
                                "with `anchor`+`anchor_position` to "
                                "place it near an existing device. Same "
                                "styling fields as add_link apply. "
                                "add_text: drop a text annotation (text "
                                "required). Optional `color`, "
                                "`fontSize`, `showBackground`, "
                                "`backgroundColor`, `backgroundOpacity`, "
                                "`backgroundPadding`, `showBorder`, "
                                "`borderColor`, `borderWidth` for the "
                                "bordered-panel pattern used to "
                                "annotate AS numbers, RD/RT, VLAN IDs. "
                                "add_shape: drop a geometric shape "
                                "(AS boundary rectangle, OSPF area "
                                "ellipse, Internet cloud, failure "
                                "cross, checkmark, arrow direction "
                                "indicator, decision diamond). "
                                "`shapeType` required: rectangle, "
                                "ellipse, line, arrow, diamond, cloud, "
                                "cross, checkmark. Optional x/y, "
                                "width/height, fillColor, fillOpacity "
                                "(use 0.06-0.12 for grouping boxes), "
                                "fillEnabled, strokeColor, strokeWidth, "
                                "strokeEnabled, cornerRadius (10-16 "
                                "for rounded AS boxes), rotation. "
                                "remove: delete an object by "
                                "id-or-label. move: change x/y of an "
                                "existing object (id+x+y required). "
                                "relabel: change an object's label "
                                "(id+label required). "
                                "style: change an EXISTING object's "
                                "visual attributes without moving / "
                                "renaming it. id required; any of "
                                "`color`, `visualStyle`, `fontSize`, "
                                "`style` (link style), `width` (link "
                                "width), `linkType`, `fillColor`, "
                                "`strokeColor` may be set. For LINKS, "
                                "you may ALSO stamp link-table fields "
                                "`interface1`, `interface2`, `vlan`, "
                                "`bd`, `linkDetails` to ENRICH a "
                                "generated topology with real "
                                "operational data (protocol, AS, "
                                "MPLS label, IPs). Use 'color all "
                                "spines red' -> one `style` per "
                                "matching device. "
                                "select: select one or more existing "
                                "objects. Either pass `id` (single) "
                                "or `ids` (array of id-or-label). "
                                "The frontend highlights them and "
                                "future turns see them in "
                                "`current.selection`. "
                                "zoom_to: pan + zoom the canvas to "
                                "focus on an object or a world rect. "
                                "Pass EITHER `id` (focus that object) "
                                "OR `x`+`y`+`w`+`h` (focus that rect). "
                                "Omit all four -> fit-to-screen. "
                                "create_domain: add a brand-new topology "
                                "domain to the user's workspace (appears "
                                "in the Topologies dropdown). `label` "
                                "required -- the domain name, must be "
                                "unique and NOT collide with built-ins "
                                "(Bugs/DNAAS). Optional: `color` (hex), "
                                "`icon` (layers, wifi, share, lightning, "
                                "sparkles, ...). Use this when the user "
                                "says 'create a domain called X' BEFORE "
                                "calling create_topology, or standalone "
                                "to prepare a container for future "
                                "topologies."
                            ),
                        },
                        # add_device / add_text / add_unbound_link common fields
                        "label": {
                            "type": "string",
                            "description": "For add_device: the device name (e.g. 'spine1'). For add_unbound_link: optional text label printed on the link. For relabel: the new label.",
                        },
                        "x": {
                            "type": "number",
                            "description": "Canvas X (world coords). Omit on add_device/add_text to let smart auto-layout pick.",
                        },
                        "y": {
                            "type": "number",
                            "description": "Canvas Y (world coords). Omit on add_device/add_text to let smart auto-layout pick.",
                        },
                        # Anchor-relative placement (add_unbound_link, add_device, add_text).
                        "anchor": {
                            "type": "string",
                            "description": "For anchor-relative placement: id-or-label of the existing device to place near.",
                        },
                        "anchor_position": {
                            "type": "string",
                            "enum": ["above", "below", "left", "right"],
                            "description": "For anchor-relative placement: which side of the anchor to place on. Ignored if `anchor` is missing.",
                        },
                        # add_device-specific
                        "deviceType": {
                            "type": "string",
                            "description": "Device kind hint -- router, switch, server, ... Free-form.",
                        },
                        "role": {
                            "type": "string",
                            "description": (
                                "Tier hint used by auto-placement: "
                                "super-spine, spine, leaf, pe, p, rr, ce, "
                                "core, dist, access, border. Strongly "
                                "preferred over x/y."
                            ),
                        },
                        "ip": {"type": "string"},
                        "color": {"type": "string"},
                        "visualStyle": {"type": "string"},
                        # add_link / add_unbound_link-specific
                        "from": {
                            "type": "string",
                            "description": "For add_link: source device id-or-label. Ignored for add_unbound_link (endpoints are free).",
                        },
                        "to": {
                            "type": "string",
                            "description": "For add_link: target device id-or-label. Ignored for add_unbound_link (endpoints are free).",
                        },
                        "linkType": {
                            "type": "string",
                            "description": (
                                "Semantic link category. Drives default "
                                "color + style when `color`/`style` are "
                                "not explicitly set. Recognised: "
                                "default, bgp, ebgp, ibgp, ospf, isis, "
                                "mpls, ldp, rsvp, sr-mpls, srv6, evpn, "
                                "vxlan, pw, vpws, l2vpn, l3vpn, dnaas, "
                                "bul, lag."
                            ),
                        },
                        "style": {
                            "type": "string",
                            "enum": [
                                "solid", "dashed", "dashed-wide", "dotted",
                                "arrow", "double-arrow",
                                "dashed-arrow", "dashed-double-arrow",
                            ],
                            "description": (
                                "Link line style (applies to add_link / "
                                "add_unbound_link / style op). Overrides "
                                "the protocol default from linkType."
                            ),
                        },
                        "width": {
                            "type": "number",
                            "description": (
                                "Link line thickness (px) or shape/text "
                                "width (px). For BUL/LAG bump to 3-4."
                            ),
                        },
                        # add_unbound_link-specific (explicit endpoints)
                        "x1": {
                            "type": "number",
                            "description": "For add_unbound_link: start endpoint X (world coords). Optional; defaults to anchor-relative or canvas centre.",
                        },
                        "y1": {
                            "type": "number",
                            "description": "For add_unbound_link: start endpoint Y (world coords). Optional.",
                        },
                        "x2": {
                            "type": "number",
                            "description": "For add_unbound_link: end endpoint X (world coords). Optional.",
                        },
                        "y2": {
                            "type": "number",
                            "description": "For add_unbound_link: end endpoint Y (world coords). Optional.",
                        },
                        "length": {
                            "type": "number",
                            "description": "For add_unbound_link: link length in world px when we're auto-placing (default 120). Ignored when x1/y1/x2/y2 are given.",
                        },
                        "orientation": {
                            "type": "string",
                            "enum": ["horizontal", "vertical"],
                            "description": "For add_unbound_link: orientation when auto-placing. Default horizontal.",
                        },
                        # add_text-specific
                        "text": {
                            "type": "string",
                            "description": "The text content for add_text.",
                        },
                        "fontSize": {"type": "number"},
                        "showBackground": {
                            "type": "boolean",
                            "description": "add_text: render a filled background rectangle behind the text.",
                        },
                        "backgroundColor": {"type": "string", "description": "add_text: background hex color."},
                        "backgroundOpacity": {"type": "number", "description": "add_text: background alpha 0..1."},
                        "backgroundPadding": {"type": "number", "description": "add_text: padding around text in px (default 6)."},
                        "showBorder": {
                            "type": "boolean",
                            "description": "add_text: render a border around the text (use with showBackground for the bordered-panel annotation pattern).",
                        },
                        "borderColor": {"type": "string"},
                        "borderWidth": {"type": "number"},
                        # add_shape-specific
                        "shapeType": {
                            "type": "string",
                            "enum": [
                                "rectangle", "ellipse", "oval",
                                "line", "arrow",
                                "diamond", "cloud",
                                "cross", "checkmark",
                            ],
                            "description": (
                                "add_shape: shape kind. rectangle / "
                                "ellipse for AS or area grouping "
                                "(with fillOpacity 0.06-0.12). cloud "
                                "for Internet / WAN. diamond for "
                                "decision points or IXP fabric. "
                                "arrow for traffic-direction "
                                "indicators. cross for failure "
                                "markers. checkmark for healthy / "
                                "validated states. line for a plain "
                                "separator."
                            ),
                        },
                        "height": {"type": "number"},
                        "fillColor": {"type": "string"},
                        "fillOpacity": {
                            "type": "number",
                            "description": "Fill alpha 0..1. Use 0.06-0.12 for AS/area grouping boxes so they sit behind devices without hiding them.",
                        },
                        "fillEnabled": {"type": "boolean"},
                        "strokeColor": {"type": "string"},
                        "strokeWidth": {"type": "number"},
                        "strokeEnabled": {"type": "boolean"},
                        "cornerRadius": {
                            "type": "number",
                            "description": "Rectangle corner radius in px. Use 10-16 for rounded AS grouping boxes.",
                        },
                        "rotation": {
                            "type": "number",
                            "description": "Rotation in degrees (shapes only).",
                        },
                        "containerMode": {
                            "type": "boolean",
                            "description": (
                                "add_shape / style on a shape: when "
                                "true, the shape becomes a CONTAINER so "
                                "dragging it carries every object whose "
                                "centre is inside it (devices, text, "
                                "nested shapes, link endpoints). Use on "
                                "AS / area / VRF / tenant grouping "
                                "frames so the user can reorganise the "
                                "diagram per-AS without ungrouping. Do "
                                "NOT set on callout shapes (cross, "
                                "checkmark, arrow, line, diamond)."
                            ),
                        },
                        # Link-table metadata (add_link / style ops on
                        # links and unbound links). The topology
                        # generator stamps these from real-device facts;
                        # the AI enrichment path can also use them to
                        # populate per-link interface labels, VLAN ids,
                        # and bridge-domain hints so the canvas
                        # link-table popup shows real data.
                        "interface1": {
                            "type": "string",
                            "description": (
                                "For add_link / style on a link: short "
                                "interface name on the FROM device "
                                "(e.g. `Eth0/1`, `ge100-0/0/1`). Drives "
                                "the link-table popup."
                            ),
                        },
                        "interface2": {
                            "type": "string",
                            "description": (
                                "For add_link / style on a link: short "
                                "interface name on the TO device. Drives "
                                "the link-table popup."
                            ),
                        },
                        "vlan": {
                            "type": "string",
                            "description": (
                                "For add_link / style on a link: VLAN "
                                "id (string). Stamped onto the link's "
                                "linkDetails for the link-table popup."
                            ),
                        },
                        "bd": {
                            "type": "string",
                            "description": (
                                "For add_link / style on a link: "
                                "bridge-domain name. Stamped onto the "
                                "link's linkDetails for the link-table "
                                "popup."
                            ),
                        },
                        "linkDetails": {
                            "type": "object",
                            "description": (
                                "For add_link / style on a link: a "
                                "free-form metadata blob merged into "
                                "the link's linkDetails (protocol, AS, "
                                "MPLS label, IPs, ...). Surfaced by the "
                                "link-table popup verbatim. Use sparingly "
                                "-- only fields you actually have."
                            ),
                            "additionalProperties": True,
                        },
                        # remove / move / relabel / style / select / zoom_to-specific
                        "id": {
                            "type": "string",
                            "description": "Object id or label for remove/move/relabel/style/select/zoom_to.",
                        },
                        # select-specific (multi-select form)
                        "ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "For `select`: array of ids or labels to select together. Use instead of `id` when you mean multiple objects.",
                        },
                        # zoom_to-specific (rect form)
                        "w": {
                            "type": "number",
                            "description": "For `zoom_to` rect form: width of the world rect to fit on screen.",
                        },
                        "h": {
                            "type": "number",
                            "description": "For `zoom_to` rect form: height of the world rect to fit on screen.",
                        },
                        # create_domain-specific
                        "icon": {
                            "type": "string",
                            "description": "For `create_domain`: icon name. Common choices: layers, wifi, share, lightning, sparkles, globe, lock. Default: sparkles.",
                        },
                    },
                },
            },
        },
    },
}


# ---------------------------------------------------------------------------
# Blueprint library tools (2026-04-24).
#
# The blueprint library (topology/ai/blueprints/) is a canonical set of
# protocol-topology examples (iBGP full-mesh, OSPF multi-area, MPLS L3VPN,
# EVPN-VXLAN fabric, Clos 3-stage, campus 3-tier, metro ring, DCI, ...)
# that the model should consult BEFORE emitting a topology from scratch.
# Each blueprint uses the industry-standard colors, shapes, arrows, and
# text-box annotations the canvas supports today.
#
# Workflow the model is expected to follow:
#
#   user: "make me a small MPLS L3VPN with 2 PEs and an RR"
#     1) list_blueprints({protocol: "mpls-l3vpn"})
#        -> [{name: "2pe-1ce-basic", ...}, {name: "4pe-rr-hub", ...}, ...]
#     2) load_blueprint({name: "2pe-1ce-basic"})
#        -> full JSON including coloured links, VRF/RD text boxes,
#           AS rectangle
#     3) Adapt device counts / names to the user's ask.
#     4) create_topology with the adapted objects.
#
# See knowledge.md -> "Blueprint Library" for the full catalog.
# ---------------------------------------------------------------------------
LIST_BLUEPRINTS_TOOL_SCHEMA: Dict[str, Any] = {
    "name": "list_blueprints",
    "description": (
        "List canonical protocol-topology blueprints available to the "
        "assistant. Each entry is a compact metadata record (name, "
        "protocol, scale, summary, device/link counts, tags). Use this "
        "to discover which blueprint best matches the user's ask; then "
        "call `load_blueprint` to fetch the full JSON so you can adapt "
        "and feed it into `create_topology`. Filters are AND-combined "
        "and all optional -- call with {} to get the whole catalog.\n\n"
        "Prefer this over building a protocol topology from memory: the "
        "blueprints already use the correct color coding (iBGP blue "
        "dashed, eBGP orange arrow, OSPF green, ISIS purple, MPLS red, "
        "EVPN teal dashed-wide, ...), AS-grouping rectangles, "
        "area-grouping ellipses, and RD/RT/VRF text-box annotations."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "protocol": {
                "type": "string",
                "description": (
                    "Filter by protocol: bgp, ibgp, ebgp, ospf, isis, "
                    "mpls-l3vpn, evpn-vxlan, sr, clos, campus, ring, "
                    "dci, drivenets. `bgp` matches ibgp/ebgp too."
                ),
            },
            "scale": {
                "type": "string",
                "enum": ["small", "medium", "large", "enterprise"],
                "description": "Filter by size preset.",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Filter by arbitrary tags (e.g. `hub-spoke`, "
                    "`full-mesh`, `multi-area`, `anycast-gw`)."
                ),
            },
            "query": {
                "type": "string",
                "description": (
                    "Free-form substring search across name, summary, "
                    "protocol, and tags."
                ),
            },
        },
    },
}


LOAD_BLUEPRINT_TOOL_SCHEMA: Dict[str, Any] = {
    "name": "load_blueprint",
    "description": (
        "Fetch the full JSON for one blueprint by its `name` (filename "
        "stem, e.g. `ibgp-full-mesh-4`, `ospf-multi-area-0-1-2`, "
        "`mpls-l3vpn-2pe-1ce-basic`). Returns the complete object list "
        "the blueprint ships with -- devices with explicit x/y and "
        "role/color/visualStyle, links with linkType/color/style/label, "
        "shapes for AS/area grouping, and text boxes for AS numbers, "
        "areas, RD/RT, VRF.\n\n"
        "You SHOULD adapt device counts, names, IP addresses, and "
        "labels to the user's specific ask, then emit the adapted "
        "objects via `create_topology`. Do NOT emit a blueprint "
        "unchanged unless the user asked for the exact scenario."
    ),
    "parameters": {
        "type": "object",
        "required": ["name"],
        "properties": {
            "name": {
                "type": "string",
                "description": (
                    "Blueprint name (filename stem). Discoverable via "
                    "`list_blueprints`."
                ),
            },
        },
    },
}


# 2026-04-24r -- interactive follow-up helpers.
#
# ASK_USER_QUESTION_TOOL_SCHEMA:
#   When the user's ask is genuinely ambiguous (destructive, multi-path,
#   or the canvas has several plausible targets), emit this tool instead
#   of guessing. The frontend renders the question + options as clickable
#   chips; picking one becomes the next user turn. Keep questions SHORT:
#   one sentence + 2-5 options. NEVER use this for Q&A or when the user
#   clearly stated what they want -- it's strictly a disambiguation
#   escape hatch, not a conversation filler.
ASK_USER_QUESTION_TOOL_SCHEMA: Dict[str, Any] = {
    "name": "ask_user_question",
    "description": (
        "Pose ONE short clarifying question with 2-5 quick-pick options "
        "before committing to a destructive or multi-path action. The "
        "frontend renders the options as clickable chips. Only use when "
        "the ask is genuinely ambiguous (e.g. multiple matching devices, "
        "reversible vs destructive paths, IPv4 vs dual-stack). Also use "
        "when the user wants a NEW topology but the prompt is still vague "
        "(e.g. protocol only, no scale, no topology style) -- offer chips "
        "for common variants instead of guessing a huge diagram. Never use "
        "this for pure explanation requests ('how does X work?') or when "
        "the user's intent is already specific (counts, ASNs, RR vs mesh, "
        "named sites). Never use for DNOS config syntax questions."
    ),
    "parameters": {
        "type": "object",
        "required": ["question", "options"],
        "properties": {
            "question": {
                "type": "string",
                "description": (
                    "The question to show the user. One short sentence. "
                    "Include the *ambiguity* so the user doesn't have "
                    "to scroll back ('You have 3 PEs -- dual-home just "
                    "PE1, or all of them?')."
                ),
            },
            "options": {
                "type": "array",
                "minItems": 2,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "required": ["label", "value"],
                    "properties": {
                        "label": {
                            "type": "string",
                            "description": (
                                "Chip text. Keep to 1-4 words. e.g. "
                                "'Dual-stack', 'IPv4 only', 'All PEs', "
                                "'Just PE1'."
                            ),
                        },
                        "value": {
                            "type": "string",
                            "description": (
                                "Full user-turn content sent back when "
                                "this option is picked. Should be a "
                                "self-contained instruction so the "
                                "follow-up turn has enough context: "
                                "'Apply VRRP to all 3 PEs (PE1/PE2/PE3) "
                                "with v4+v6'."
                            ),
                        },
                    },
                },
            },
            "allow_free_text": {
                "type": "boolean",
                "description": (
                    "True if the user should ALSO be allowed to type a "
                    "free-text reply in addition to the chips."
                ),
            },
        },
    },
}


# PROPOSE_CANVAS_EDITS_TOOL_SCHEMA:
#   Same semantics as apply_canvas_edits, but NON-APPLYING: the frontend
#   renders a diff preview (adds / removes / renames / styles) with
#   Apply / Tweak / Cancel controls. If the user clicks Apply, the
#   frontend locally runs the exact same edits through its normal
#   _applyCanvasEdits path -- no second LLM round-trip. Use this for
#   anything irreversible (remove, bulk relabel, domain moves, > 10
#   devices) or when the user asked "what would you do?" rather than
#   "do it".
import copy as _copy
PROPOSE_CANVAS_EDITS_TOOL_SCHEMA: Dict[str, Any] = _copy.deepcopy(CANVAS_EDITS_TOOL_SCHEMA)
PROPOSE_CANVAS_EDITS_TOOL_SCHEMA["name"] = "propose_canvas_edits"
PROPOSE_CANVAS_EDITS_TOOL_SCHEMA["description"] = (
    "Propose (but do NOT apply) an edit list for the user's review. "
    "Frontend shows a diff preview with Apply / Tweak / Cancel. Use "
    "this for anything destructive (remove ops), bulk changes "
    "(> 10 edits), or when the user says 'what would you do?' / "
    "'show me the changes first'. The edit schema is identical to "
    "apply_canvas_edits -- same op names, same properties. Prefer "
    "this over apply_canvas_edits for irreversible ops."
)


# ---------------------------------------------------------------------------
# Smart auto-layout engine.
#
# LLMs are unreliable about emitting canvas coordinates: they often skip
# `x`/`y` entirely (see the 2026-04-21 "clos-4x2" regression, every
# device had only id+label+type). Without coordinates the canvas loader
# falls back to a dumb 5-wide linear grid, which produces inconsistent,
# unreadable layouts for every topology shape.
#
# This engine fills in coordinates when the LLM forgets, using:
#   1. An explicit `layout_hint` from the tool call (most reliable).
#   2. Label-based role detection ("spine", "leaf", "pe", "core", ...).
#   3. Graph shape detection (bipartite tiers, cycles, hub degree).
#   4. A clean generic fallback (hierarchical by degree).
#
# Coordinate space mirrors the canvas world coords (loadTopologyFromData
# consumes whatever x/y we emit, unmodified). Spacing is tuned so the
# resulting topology looks good on a 1920x1080 canvas at 100% zoom.
# ---------------------------------------------------------------------------
# Canvas coord tuning. These are world coords that render nicely on a
# 1600-2400 px wide viewport at zoom=1. The canvas' centerOnDevices()
# will re-centre and zoom-to-fit after load, so they don't have to be
# pixel-perfect -- they just have to be SPREAD.
_LAYOUT_PAD = 180          # minimum gap between siblings in the same tier
_LAYOUT_TIER_GAP = 320     # vertical gap between tiers
_LAYOUT_ORIGIN_X = 260     # where the left-most column lives
_LAYOUT_ORIGIN_Y = 200     # top tier

# Role keyword -> canonical tier. Matched case-insensitively against
# `role` / `deviceType` / `visualStyle` / `label`. Longer prefixes win
# (so "super-spine" > "spine"). Each tier maps to a Y-band in the
# layered rendering: lower tier value = higher on canvas (closer to y=0).
_ROLE_TIERS: List[Tuple[str, int]] = [
    # super-spine / spine / leaf (DC fabric)
    ("super-spine", 0), ("superspine", 0), ("ssp", 0),
    ("spine", 1), ("sp-", 1),
    ("leaf",  2), ("lf-", 2), ("tor", 2),
    # SP backbone
    ("rr",    0), ("route-reflector", 0),
    ("core",  1), ("p-", 1),   # "P" routers
    ("pe",    2), ("edge", 2), ("border", 2),
    ("ce",    3), ("cpe",  3), ("host", 3),
    # Campus / enterprise
    ("dist",  1), ("distribution", 1), ("agg", 1),
    ("access", 2), ("sw-", 2),
]


def _detect_role_tier(dev: Dict[str, Any]) -> Optional[int]:
    """Return the canonical tier (0=top) derived from a device's hints.

    Checks `role` first (strongest signal), then `deviceType`,
    `visualStyle`, then the `label`. The longest matching keyword wins
    so "super-spine" beats "spine".
    """
    hay_parts: List[str] = []
    for key in ("role", "deviceType", "visualStyle", "label", "id"):
        val = dev.get(key)
        if isinstance(val, str) and val.strip():
            hay_parts.append(val.strip().lower())
    if not hay_parts:
        return None
    hay = " ".join(hay_parts)
    # Sort by keyword length descending so "super-spine" beats "spine".
    best: Optional[int] = None
    best_len = -1
    for kw, tier in sorted(_ROLE_TIERS, key=lambda p: -len(p[0])):
        if kw in hay and len(kw) > best_len:
            best = tier
            best_len = len(kw)
    return best


def _build_graph(devices: List[Dict[str, Any]],
                 links: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Build an undirected adjacency map keyed by device id."""
    dev_ids = {str(d.get("id") or "") for d in devices if d.get("id")}
    adj: Dict[str, List[str]] = {did: [] for did in dev_ids}
    for ln in links:
        a = str(ln.get("device1") or "")
        b = str(ln.get("device2") or "")
        if a and b and a in dev_ids and b in dev_ids and a != b:
            # Dedup parallel links so degree counts by unique neighbour.
            if b not in adj[a]:
                adj[a].append(b)
            if a not in adj[b]:
                adj[b].append(a)
    return adj


def _is_bipartite(adj: Dict[str, List[str]]) -> Optional[Tuple[List[str], List[str]]]:
    """Return (tier_A, tier_B) if the graph is connected + bipartite.

    Used as the primary signal for CLOS 3-stage detection: every leaf
    touches every spine but no leaf-leaf or spine-spine link.
    """
    if not adj:
        return None
    colour: Dict[str, int] = {}
    start = next(iter(adj))
    colour[start] = 0
    queue = [start]
    while queue:
        node = queue.pop()
        for nb in adj[node]:
            if nb not in colour:
                colour[nb] = 1 - colour[node]
                queue.append(nb)
            elif colour[nb] == colour[node]:
                return None  # not bipartite
    if len(colour) != len(adj):
        return None  # not connected -- ignore
    tier_a = [n for n, c in colour.items() if c == 0]
    tier_b = [n for n, c in colour.items() if c == 1]
    return tier_a, tier_b


def _is_ring(adj: Dict[str, List[str]]) -> bool:
    """True when every node has exactly 2 neighbours and the graph is
    a single connected cycle."""
    if not adj:
        return False
    if any(len(nbs) != 2 for nbs in adj.values()):
        return False
    # Walk the cycle and ensure we touch every node exactly once.
    start = next(iter(adj))
    visited = {start}
    prev = None
    curr = start
    for _ in range(len(adj)):
        nxt = None
        for nb in adj[curr]:
            if nb != prev:
                nxt = nb
                break
        if nxt is None:
            return False
        if nxt == start:
            break
        if nxt in visited:
            return False
        visited.add(nxt)
        prev, curr = curr, nxt
    return len(visited) == len(adj)


def _is_path(adj: Dict[str, List[str]]) -> bool:
    """True when the graph is a simple path (exactly 2 endpoints of
    degree 1, every other node degree 2)."""
    if not adj:
        return False
    deg1 = sum(1 for nbs in adj.values() if len(nbs) == 1)
    deg2 = sum(1 for nbs in adj.values() if len(nbs) == 2)
    return deg1 == 2 and deg1 + deg2 == len(adj)


def _is_hub_spoke(adj: Dict[str, List[str]]) -> Optional[str]:
    """Return the hub id if the graph is a star: one node of degree N-1
    and every other node has degree 1 (single connection to the hub)."""
    if len(adj) < 3:
        return None
    hub_candidates = [n for n, nbs in adj.items() if len(nbs) == len(adj) - 1]
    if len(hub_candidates) != 1:
        return None
    hub = hub_candidates[0]
    for n, nbs in adj.items():
        if n == hub:
            continue
        if nbs != [hub]:
            return None
    return hub


def _place_ring(devices: List[Dict[str, Any]]) -> None:
    """Place devices on a circle so the cycle renders cleanly."""
    n = len(devices)
    if n == 0:
        return
    # Radius scales with N so a 4-node ring is compact and a 12-node
    # ring is readable. Minimum 260 (looks like a square for n=4), max
    # 600 to keep even very large rings inside the default viewport.
    radius = max(260, min(600, int(_LAYOUT_PAD * n / (2 * math.pi))))
    cx = _LAYOUT_ORIGIN_X + 600
    cy = _LAYOUT_ORIGIN_Y + 400
    for idx, dev in enumerate(devices):
        angle = 2 * math.pi * idx / n - math.pi / 2  # start at top
        dev["x"] = round(cx + radius * math.cos(angle), 1)
        dev["y"] = round(cy + radius * math.sin(angle), 1)


def _place_hub_spoke(devices: List[Dict[str, Any]], hub_id: Optional[str]) -> None:
    """Put the hub in the centre and arrange spokes on a circle."""
    if not devices:
        return
    hub = next((d for d in devices if str(d.get("id")) == hub_id), None)
    spokes = [d for d in devices if d is not hub]
    cx = _LAYOUT_ORIGIN_X + 600
    cy = _LAYOUT_ORIGIN_Y + 400
    if hub is not None:
        hub["x"] = cx
        hub["y"] = cy
    if not spokes:
        return
    radius = max(260, min(520, int(_LAYOUT_PAD * len(spokes) / (2 * math.pi)) + 200))
    for idx, dev in enumerate(spokes):
        angle = 2 * math.pi * idx / len(spokes) - math.pi / 2
        dev["x"] = round(cx + radius * math.cos(angle), 1)
        dev["y"] = round(cy + radius * math.sin(angle), 1)


def _place_path(devices: List[Dict[str, Any]],
                adj: Dict[str, List[str]]) -> None:
    """Lay devices out left-to-right along the path order."""
    # Walk from an endpoint.
    endpoints = [n for n, nbs in adj.items() if len(nbs) == 1]
    if not endpoints:
        # Fallback: arbitrary order.
        order = [str(d.get("id")) for d in devices]
    else:
        order: List[str] = []
        prev: Optional[str] = None
        curr: Optional[str] = endpoints[0]
        while curr and curr not in order:
            order.append(curr)
            nxt = None
            for nb in adj.get(curr, []):
                if nb != prev:
                    nxt = nb
                    break
            prev, curr = curr, nxt
    id_to_dev = {str(d.get("id")): d for d in devices}
    y = _LAYOUT_ORIGIN_Y + 400
    for idx, did in enumerate(order):
        dev = id_to_dev.get(did)
        if dev is None:
            continue
        dev["x"] = _LAYOUT_ORIGIN_X + idx * _LAYOUT_PAD * 1.4
        dev["y"] = y


def _place_layered(tiers: List[List[Dict[str, Any]]]) -> None:
    """Render a list of tiers top-to-bottom, each tier evenly spread on
    the X axis. Used for CLOS 3/5-stage, campus, SP backbone."""
    non_empty = [t for t in tiers if t]
    if not non_empty:
        return
    widest = max(len(t) for t in non_empty)
    total_width = max(1, (widest - 1)) * _LAYOUT_PAD * 1.6
    origin_x = _LAYOUT_ORIGIN_X + 120
    for tier_idx, tier in enumerate(tiers):
        if not tier:
            continue
        y = _LAYOUT_ORIGIN_Y + tier_idx * _LAYOUT_TIER_GAP
        count = len(tier)
        # Centre each tier on the widest one.
        tier_width = max(1, (count - 1)) * _LAYOUT_PAD * 1.6
        x_start = origin_x + (total_width - tier_width) / 2
        for col, dev in enumerate(tier):
            dev["x"] = round(x_start + col * _LAYOUT_PAD * 1.6, 1)
            dev["y"] = y


def _place_clos_3stage(devices: List[Dict[str, Any]],
                       bipartition: Optional[Tuple[List[str], List[str]]]) -> None:
    """Place a CLOS 3-stage (spine-leaf) fabric in two horizontal rows.

    Tier identification priority: explicit `role`/label hint > side of
    the bipartition with fewer nodes (=spines). Leaves go below spines.
    """
    spines: List[Dict[str, Any]] = []
    leaves: List[Dict[str, Any]] = []
    other: List[Dict[str, Any]] = []
    id_to_dev = {str(d.get("id")): d for d in devices}

    if bipartition is not None:
        tier_a, tier_b = bipartition
        # Use role hints if available; otherwise the smaller tier is
        # spines (fewer spines than leaves is the normal 2:N ratio).
        a_role = [_detect_role_tier(id_to_dev[i]) for i in tier_a if i in id_to_dev]
        b_role = [_detect_role_tier(id_to_dev[i]) for i in tier_b if i in id_to_dev]
        a_is_spine = any(r == 1 for r in a_role) and not any(r == 2 for r in a_role)
        b_is_spine = any(r == 1 for r in b_role) and not any(r == 2 for r in b_role)
        if a_is_spine and not b_is_spine:
            spine_ids, leaf_ids = tier_a, tier_b
        elif b_is_spine and not a_is_spine:
            spine_ids, leaf_ids = tier_b, tier_a
        else:
            spine_ids, leaf_ids = (tier_a, tier_b) if len(tier_a) <= len(tier_b) else (tier_b, tier_a)
        for did in spine_ids:
            d = id_to_dev.get(did)
            if d is not None:
                spines.append(d)
        for did in leaf_ids:
            d = id_to_dev.get(did)
            if d is not None:
                leaves.append(d)
    else:
        for dev in devices:
            tier = _detect_role_tier(dev)
            if tier == 1:
                spines.append(dev)
            elif tier == 2 or tier == 3:
                leaves.append(dev)
            else:
                other.append(dev)
        if not spines and leaves:
            # Everyone detected as leaves -- fall back to label heuristics.
            leaves, other = other + leaves, []
    # Sort each tier by label for predictable left-to-right ordering.
    spines.sort(key=lambda d: str(d.get("label") or d.get("id") or ""))
    leaves.sort(key=lambda d: str(d.get("label") or d.get("id") or ""))
    other.sort(key=lambda d: str(d.get("label") or d.get("id") or ""))
    # "other" devices (non-classified) get their own row beneath leaves.
    _place_layered([spines, leaves, other])


def _place_clos_5stage(devices: List[Dict[str, Any]]) -> None:
    """Place super-spines / spines / leaves on three rows."""
    ss, sp, lf, other = [], [], [], []
    for dev in devices:
        tier = _detect_role_tier(dev)
        if tier == 0:
            ss.append(dev)
        elif tier == 1:
            sp.append(dev)
        elif tier in (2, 3):
            lf.append(dev)
        else:
            other.append(dev)
    for tier in (ss, sp, lf, other):
        tier.sort(key=lambda d: str(d.get("label") or d.get("id") or ""))
    _place_layered([ss, sp, lf, other])


def _place_sp_backbone(devices: List[Dict[str, Any]]) -> None:
    """RR / Core-P / PE / CE layered (SP backbone with route reflectors)."""
    rr, core, pe, ce, other = [], [], [], [], []
    for dev in devices:
        tier = _detect_role_tier(dev)
        if tier == 0:
            rr.append(dev)
        elif tier == 1:
            core.append(dev)
        elif tier == 2:
            pe.append(dev)
        elif tier == 3:
            ce.append(dev)
        else:
            other.append(dev)
    for tier in (rr, core, pe, ce, other):
        tier.sort(key=lambda d: str(d.get("label") or d.get("id") or ""))
    _place_layered([rr, core, pe, ce, other])


def _place_campus(devices: List[Dict[str, Any]]) -> None:
    """Core / Distribution / Access layered (enterprise campus)."""
    core, dist, access, other = [], [], [], []
    for dev in devices:
        tier = _detect_role_tier(dev)
        if tier == 1:
            # Both core and dist keyword map to tier 1 -- discriminate by
            # the raw label.
            hay = " ".join([str(dev.get(k, "")) for k in ("role", "label", "id")]).lower()
            if "core" in hay:
                core.append(dev)
            else:
                dist.append(dev)
        elif tier == 2:
            access.append(dev)
        else:
            other.append(dev)
    for tier in (core, dist, access, other):
        tier.sort(key=lambda d: str(d.get("label") or d.get("id") or ""))
    _place_layered([core, dist, access, other])


def _place_tree(devices: List[Dict[str, Any]],
                adj: Dict[str, List[str]]) -> None:
    """BFS-based tree layout from the highest-degree node."""
    if not devices:
        return
    id_to_dev = {str(d.get("id")): d for d in devices}
    # Root = highest degree node (ties broken by label alphabetically).
    root = max(adj.keys(), key=lambda n: (len(adj[n]), n)) if adj else None
    if root is None:
        _place_generic(devices)
        return
    visited: Dict[str, int] = {root: 0}
    tiers: List[List[str]] = [[root]]
    frontier = [root]
    while frontier:
        next_frontier: List[str] = []
        for node in frontier:
            for nb in sorted(adj.get(node, [])):
                if nb not in visited:
                    visited[nb] = visited[node] + 1
                    next_frontier.append(nb)
        if next_frontier:
            tiers.append(next_frontier)
        frontier = next_frontier
    # Any disconnected stragglers get appended to the last tier.
    stragglers = [str(d.get("id")) for d in devices if str(d.get("id")) not in visited]
    if stragglers:
        tiers.append(stragglers)
    tier_devs: List[List[Dict[str, Any]]] = []
    for tier in tiers:
        tier_devs.append([id_to_dev[i] for i in tier if i in id_to_dev])
    _place_layered(tier_devs)


def _place_generic(devices: List[Dict[str, Any]]) -> None:
    """Last-resort layered grid: group by degree bucket, then spread."""
    if not devices:
        return
    # Stable grid: ceil(sqrt(N)) wide, rows spaced.
    n = len(devices)
    cols = max(1, int(math.ceil(math.sqrt(n))))
    for idx, dev in enumerate(devices):
        row = idx // cols
        col = idx % cols
        dev["x"] = _LAYOUT_ORIGIN_X + col * _LAYOUT_PAD * 1.6
        dev["y"] = _LAYOUT_ORIGIN_Y + row * _LAYOUT_TIER_GAP


def _apply_layout(objects: List[Dict[str, Any]],
                  layout_hint: Optional[str]) -> None:
    """Fill in x/y for every device that lacks one.

    This mutates the list in place. Devices that already have numeric
    x/y are left untouched so a carefully-placed-by-the-LLM topology
    survives. Only the UNPLACED devices get auto-positioned. If the
    whole set is unplaced, we run the full detected-shape layout.
    """
    devices = [o for o in objects if o.get("type") == "device"]
    links = [o for o in objects if o.get("type") == "link"]
    if not devices:
        return

    def _has_coords(d: Dict[str, Any]) -> bool:
        try:
            x = float(d.get("x")) if d.get("x") is not None else None
            y = float(d.get("y")) if d.get("y") is not None else None
        except (TypeError, ValueError):
            return False
        # (0, 0) is treated as unplaced -- many LLMs emit it as a
        # "I don't know where to put this" marker.
        if x is None or y is None:
            return False
        if math.isnan(x) or math.isnan(y):
            return False
        if abs(x) < 1 and abs(y) < 1:
            return False
        return True

    placed = [d for d in devices if _has_coords(d)]
    unplaced = [d for d in devices if not _has_coords(d)]
    if not unplaced:
        return  # The LLM did it right this time, leave it alone.

    # If SOME devices have coordinates but not all, use a generic grid
    # below the existing cluster so we don't overlap.
    if placed and unplaced:
        max_y = max((float(d.get("y") or 0) for d in placed), default=_LAYOUT_ORIGIN_Y)
        origin_y = max_y + _LAYOUT_TIER_GAP
        cols = max(1, int(math.ceil(math.sqrt(len(unplaced)))))
        for idx, dev in enumerate(unplaced):
            row = idx // cols
            col = idx % cols
            dev["x"] = _LAYOUT_ORIGIN_X + col * _LAYOUT_PAD * 1.6
            dev["y"] = origin_y + row * _LAYOUT_TIER_GAP
        return

    # All devices are unplaced -- run the full shape-aware layout.
    adj = _build_graph(devices, links)
    hint = (layout_hint or "auto").strip().lower()

    # Explicit hint short-circuits graph detection.
    if hint == "clos-3-stage":
        _place_clos_3stage(devices, _is_bipartite(adj))
        return
    if hint == "clos-5-stage":
        _place_clos_5stage(devices)
        return
    if hint == "hub-spoke":
        _place_hub_spoke(devices, _is_hub_spoke(adj))
        return
    if hint == "ring":
        _place_ring(devices)
        return
    if hint == "path":
        _place_path(devices, adj)
        return
    if hint == "sp-backbone":
        _place_sp_backbone(devices)
        return
    if hint == "campus":
        _place_campus(devices)
        return
    if hint == "tree":
        _place_tree(devices, adj)
        return
    if hint in ("metro-ring", "ring-access"):
        _place_ring(devices)
        return
    if hint == "dual-homed":
        # Two PEs on top, CE(s) on bottom. Detect by role.
        pes = [d for d in devices if _detect_role_tier(d) == 2]
        ces = [d for d in devices if _detect_role_tier(d) == 3]
        other = [d for d in devices if d not in pes and d not in ces]
        _place_layered([other, pes, ces])
        return
    if hint == "mesh":
        # Circular layout so every mutual link is equally long.
        _place_ring(devices)
        return

    # hint == "auto" -- detect from graph / labels.
    #
    # Order matters: a specific graph SHAPE (ring, simple path,
    # hub-and-spoke) unambiguously defines the layout and wins over
    # role-based labelling. A PE-P-P-PE chain is a path even though
    # its role labels say "CLOS-3". A 6-node metro ring is a ring even
    # though every even cycle is bipartite. Only when the graph has no
    # distinctive shape do we fall back to role-based tiering.
    #
    # 1) Specific graph shapes first (ring / path / star).
    if _is_ring(adj):
        _place_ring(devices)
        return
    if _is_path(adj):
        _place_path(devices, adj)
        return
    hub = _is_hub_spoke(adj)
    if hub is not None:
        _place_hub_spoke(devices, hub)
        return
    # 2) Role labelling (SP backbone, campus, CLOS-5-stage, CLOS-3-stage).
    role_tiers = [_detect_role_tier(d) for d in devices]
    role_set = {t for t in role_tiers if t is not None}
    if role_set:
        if 0 in role_set and 1 in role_set and 2 in role_set:
            # super-spine + spine + leaf => CLOS-5 OR RR + core + PE => SP
            # discriminate by labels
            hay = " ".join(str(d.get("label") or d.get("id") or "") for d in devices).lower()
            if "rr" in hay or "route-reflector" in hay or "pe" in hay or re.search(r"\bp\b|\bp-", hay):
                _place_sp_backbone(devices)
            else:
                _place_clos_5stage(devices)
            return
        if 1 in role_set and 2 in role_set:
            hay = " ".join(str(d.get("label") or d.get("id") or "") for d in devices).lower()
            if "core" in hay and "access" in hay:
                _place_campus(devices)
                return
            _place_clos_3stage(devices, _is_bipartite(adj))
            return
        if 2 in role_set and 3 in role_set:
            # PE + CE => dual-homed or SP
            pes = [d for d, t in zip(devices, role_tiers) if t == 2]
            ces = [d for d, t in zip(devices, role_tiers) if t == 3]
            other = [d for d, t in zip(devices, role_tiers) if t not in (2, 3)]
            _place_layered([other, pes, ces])
            return
    # 3) Generic bipartite => CLOS-3 fabric.
    bip = _is_bipartite(adj)
    if bip is not None:
        _place_clos_3stage(devices, bip)
        return
    # 4) Fall back to BFS tree from the highest-degree node.
    if any(adj.values()):
        _place_tree(devices, adj)
    else:
        _place_generic(devices)


def _text_box(obj: Dict[str, Any]) -> Tuple[float, float, float, float]:
    """Approximate a text object's rendered bounds for collision checks."""
    try:
        x = float(obj.get("x") or 0)
        y = float(obj.get("y") or 0)
    except (TypeError, ValueError):
        x, y = 0.0, 0.0
    text = str(obj.get("text") or obj.get("label") or "")
    try:
        font = float(obj.get("fontSize") or 12)
    except (TypeError, ValueError):
        font = 12.0
    lines = text.splitlines() or [text]
    longest = max((len(line) for line in lines), default=1)
    pad = float(obj.get("backgroundPadding") or 5)
    width = max(42.0, min(360.0, longest * font * 0.58 + pad * 2))
    height = max(font + pad * 2, len(lines) * font * 1.25 + pad * 2)
    return (x - width / 2, y - height / 2, x + width / 2, y + height / 2)


def _device_box(obj: Dict[str, Any]) -> Tuple[float, float, float, float]:
    """Approximate a device's occupied label/icon area."""
    try:
        x = float(obj.get("x") or 0)
        y = float(obj.get("y") or 0)
    except (TypeError, ValueError):
        x, y = 0.0, 0.0
    try:
        radius = float(obj.get("radius") or 42)
    except (TypeError, ValueError):
        radius = 42.0
    # Include the visible label under/inside the icon.
    return (x - radius - 48, y - radius - 34, x + radius + 48, y + radius + 42)


def _boxes_intersect(a: Tuple[float, float, float, float],
                     b: Tuple[float, float, float, float],
                     gap: float = 10.0) -> bool:
    return not (
        a[2] + gap < b[0]
        or a[0] - gap > b[2]
        or a[3] + gap < b[1]
        or a[1] - gap > b[3]
    )


def _apply_annotation_layout(objects: List[Dict[str, Any]]) -> None:
    """Move AI-generated text annotations so they do not overlap.

    LLMs frequently stack several callouts directly over a device or over
    each other. This deterministic pass keeps explicit positions when they
    are readable, otherwise searches nearby slots in a stable spiral.
    """
    devices = [o for o in objects if o.get("type") == "device"]
    texts = [o for o in objects if o.get("type") == "text"]
    if not texts:
        return
    blockers: List[Tuple[float, float, float, float]] = [_device_box(d) for d in devices]
    if devices:
        xs = [float(d.get("x") or 0) for d in devices]
        ys = [float(d.get("y") or 0) for d in devices]
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        min_x = min(xs) - 260
        max_x = max(xs) + 260
        min_y = min(ys) - 180
        max_y = max(ys) + 220
    else:
        cx, cy = 600.0, 420.0
        min_x, max_x, min_y, max_y = 120.0, 1400.0, 80.0, 1000.0

    # Bigger/title callouts first so smaller notes flow around them.
    def _text_priority(obj: Dict[str, Any]) -> Tuple[float, str]:
        try:
            font = float(obj.get("fontSize") or 12)
        except (TypeError, ValueError):
            font = 12.0
        return (-font, str(obj.get("id") or ""))

    ring_offsets: List[Tuple[float, float]] = [(0, 0)]
    for r in (95, 150, 220, 300, 390, 500):
        ring_offsets.extend([
            (0, -r), (r, -r * 0.65), (r, 0), (r, r * 0.65),
            (0, r), (-r, r * 0.65), (-r, 0), (-r, -r * 0.65),
        ])

    for idx, txt in enumerate(sorted(texts, key=_text_priority)):
        if "text" not in txt and "label" in txt:
            txt["text"] = txt.get("label")
        txt.setdefault("showBackground", True)
        txt.setdefault("backgroundColor", "rgba(11, 22, 36, 0.88)")
        txt.setdefault("backgroundOpacity", 0.88)
        txt.setdefault("backgroundPadding", 5)
        txt.setdefault("showBorder", True)
        txt.setdefault("borderColor", "rgba(255, 255, 255, 0.25)")
        txt.setdefault("borderWidth", 1)

        has_coords = isinstance(txt.get("x"), (int, float)) and isinstance(txt.get("y"), (int, float))
        base_x = float(txt.get("x")) if has_coords else cx
        base_y = float(txt.get("y")) if has_coords else cy
        # If a note starts inside the device cluster, bias it outward so
        # labels stay readable instead of sitting on icons.
        if devices and abs(base_x - cx) < 140 and abs(base_y - cy) < 140:
            base_y = min_y - 40 + idx * 28

        chosen = None
        for ox, oy in ring_offsets:
            candidate_x = max(min_x, min(max_x, base_x + ox))
            candidate_y = max(min_y, min(max_y, base_y + oy))
            txt["x"], txt["y"] = round(candidate_x, 1), round(candidate_y, 1)
            box = _text_box(txt)
            if not any(_boxes_intersect(box, b) for b in blockers):
                chosen = box
                break
        if chosen is None:
            # Last resort: deterministic right-side stack outside the graph.
            txt["x"] = round(max_x + 130, 1)
            txt["y"] = round(min_y + idx * 54, 1)
            chosen = _text_box(txt)
        blockers.append(chosen)


# ---------------------------------------------------------------------------
# Sanity-check + normalize a topology payload coming from an LLM tool call.
# Raises ValueError on unrecoverable issues; fills in safe defaults for minor
# omissions (e.g. missing metadata.version).
# ---------------------------------------------------------------------------
def normalize_topology_payload(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Turn an LLM tool_use result into a valid topology JSON.

    Contract:
      - Returns a dict with `version`, `objects`, `metadata`.
      - `name` is lifted into metadata.name (and echoed by the caller
        as the section filename).
      - Object-level invariants: unique ids, valid type, at least one
        endpoint reference on links.
      - Unknown fields pass through (the canvas loader ignores
        fields it doesn't recognize).
    """
    if not isinstance(raw, dict):
        raise ValueError("create_topology expected a JSON object")
    name = (raw.get("name") or "").strip()
    if not name:
        raise ValueError("create_topology.name is required")
    objects = raw.get("objects") or []
    if not isinstance(objects, list) or not objects:
        raise ValueError("create_topology.objects must be a non-empty list")

    seen_ids: Dict[str, bool] = {}
    normalized: List[Dict[str, Any]] = []
    device_ids: Dict[str, bool] = {}
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        oid = str(obj.get("id") or "").strip()
        otype = str(obj.get("type") or "").strip()
        if not oid or not otype:
            continue
        if oid in seen_ids:
            # De-dup silently -- cheaper than asking the model to retry.
            continue
        seen_ids[oid] = True
        if otype not in {"device", "link", "text", "shape"}:
            continue
        if otype == "device":
            device_ids[oid] = True
        normalized.append(obj)

    # Drop links that reference nothing.
    cleaned: List[Dict[str, Any]] = []
    for obj in normalized:
        if obj.get("type") == "link":
            has_dev = obj.get("device1") in device_ids or obj.get("device2") in device_ids
            has_cp = isinstance(obj.get("connectionPoint"), dict)
            if not has_dev and not has_cp:
                continue
        cleaned.append(obj)

    if not cleaned:
        raise ValueError("create_topology.objects contained no valid entries")
    device_count = sum(1 for obj in cleaned if obj.get("type") == "device")
    link_count = sum(1 for obj in cleaned if obj.get("type") == "link")
    if device_count < 2 or link_count < 1:
        raise ValueError(
            "create_topology produced a weak topology: at least 2 devices "
            "and 1 link are required. Use apply_canvas_edits for single-object "
            "changes, or regenerate a complete topology with real endpoints."
        )

    # ---- Smart auto-layout ------------------------------------------------
    # Fill in x/y for devices the LLM forgot to place. Without this, the
    # canvas falls back to a 5-wide linear grid that produces unreadable
    # layouts for every topology shape. See _apply_layout() above for the
    # detection heuristics (explicit hint > label roles > graph shape).
    layout_hint = (raw.get("layout_hint") or "").strip().lower() or None
    try:
        _apply_layout(cleaned, layout_hint)
    except Exception as exc:  # pragma: no cover -- never crash the save path
        # A broken auto-layout must NOT block the save -- fall back to
        # whatever coordinates the LLM did provide (or none, in which
        # case the canvas' legacy grid kicks in). We just log via the
        # metadata so dev tooling can catch it.
        if isinstance(metadata := raw.get("metadata"), dict):
            metadata.setdefault("layout_error", str(exc))
    try:
        _apply_annotation_layout(cleaned)
    except Exception as exc:  # pragma: no cover -- annotation layout is best-effort
        if isinstance(metadata := raw.get("metadata"), dict):
            metadata.setdefault("annotation_layout_error", str(exc))

    metadata = raw.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}
    metadata.setdefault("name", name)
    metadata.setdefault("generated_by", "ai-assistant")
    summary = (raw.get("summary") or "").strip()
    if summary:
        metadata.setdefault("summary", summary)
    if layout_hint:
        metadata.setdefault("layout_hint", layout_hint)
    realism_scale = (raw.get("realism_scale") or "").strip().lower()
    if realism_scale in {"small", "medium", "large", "enterprise"}:
        metadata.setdefault("realism_scale", realism_scale)

    return {
        "version": "1.0",
        "objects": cleaned,
        "metadata": metadata,
    }


# ---------------------------------------------------------------------------
# Live context builder.
# ---------------------------------------------------------------------------
_MAX_DEVICES = 40
_MAX_LINKS = 80
_MAX_TEXTS = 20
_MAX_SHAPES = 20
_MAX_DOMAINS = 25
_MAX_RECENT_TOPOS = 15
_MAX_RECENT_EVENTS = 20
_TEXT_SNIPPET_LEN = 60


def build_live_context(
    username: str,
    canvas_snapshot: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Return a compact per-user / per-canvas context blob."""
    ctx: Dict[str, Any] = {
        "user": _user_block(username),
        "current": _canvas_block(canvas_snapshot),
        "workspace": _workspace_block(username),
    }
    events = _events_block(username)
    if events:
        ctx["recent_events"] = events
    devices = _devices_block(username)
    if devices:
        ctx["devices"] = devices
    return ctx


def _user_block(username: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {"username": username or "unknown"}
    if user_store is None or not username:
        return out
    try:
        record = user_store.get_user(username)
    except Exception:
        record = None
    if record:
        out["role"] = record.get("role") or ""
        out["display_name"] = record.get("display_name") or ""
    return out


def _canvas_block(snapshot: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Normalise a canvas snapshot into a compact per-turn context block.

    Accepts TWO shapes so the backend stays robust to frontend refactors:

    1. *Flat-typed* (what ``topology.js`` exports for save/load):
       ``{"objects": [{"type":"device",...}, {"type":"link",...}, ...]}``

    2. *Pre-bucketed* (what ``topology-ai.js::_collectCanvasSnapshot``
       actually sends over ``/api/ai/chat`` today):
       ``{"topology": {...}, "counts": {...}, "devices": [...], "links": [...]}``

    Before 2026-04-21k the code only understood shape #1, so every AI
    turn saw ``device_count: 0`` regardless of what was on the canvas,
    and the model correctly but embarrassingly answered "no devices,
    no links" when asked to explain the canvas. Handling both shapes
    here is a thin normalisation layer; no frontend change needed.
    """
    if not isinstance(snapshot, dict):
        return {"topology_name": "", "device_count": 0, "link_count": 0}

    devices: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []
    texts: List[str] = []
    shape_count = 0
    truncated_devices = 0
    truncated_links = 0
    truncated_texts = 0

    objects = snapshot.get("objects")
    if isinstance(objects, list) and objects:
        # --- shape #1: flat typed list --------------------------------
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            t = obj.get("type")
            if t == "device":
                if len(devices) < _MAX_DEVICES:
                    # 2026-04-24q -- preserve spatial info so the LLM
                    # can honour precise-placement prompts. `x`/`y` are
                    # world-coord integers (frontend already rounds).
                    dx = obj.get("x")
                    dy = obj.get("y")
                    devices.append({
                        "id": str(obj.get("id") or "")[:40],
                        "label": str(obj.get("label") or "")[:40],
                        "role": str(obj.get("deviceType") or obj.get("visualStyle") or "")[:24],
                        "color": str(obj.get("color") or "")[:16],
                        "x": int(dx) if isinstance(dx, (int, float)) else None,
                        "y": int(dy) if isinstance(dy, (int, float)) else None,
                    })
                else:
                    truncated_devices += 1
            elif t in {"link", "unbound"}:
                if len(links) < _MAX_LINKS:
                    links.append({
                        "id": str(obj.get("id") or "")[:40],
                        "a": str(obj.get("device1") or "")[:40],
                        "b": str(obj.get("device2") or "")[:40],
                        "linkType": str(obj.get("linkType") or "")[:16],
                    })
                else:
                    truncated_links += 1
            elif t == "text":
                if len(texts) < _MAX_TEXTS:
                    snippet = str(obj.get("text") or "")[:_TEXT_SNIPPET_LEN]
                    if snippet.strip():
                        texts.append(snippet)
                else:
                    truncated_texts += 1
            elif t == "shape":
                shape_count += 1
    else:
        # --- shape #2: pre-bucketed (topology-ai.js) ------------------
        raw_devices = snapshot.get("devices") or []
        raw_links   = snapshot.get("links") or []
        for d in raw_devices:
            if not isinstance(d, dict):
                continue
            if len(devices) < _MAX_DEVICES:
                dx = d.get("x")
                dy = d.get("y")
                devices.append({
                    "id":    str(d.get("id")    or "")[:40],
                    "label": str(d.get("name") or d.get("label") or "")[:40],
                    "role":  str(d.get("role") or d.get("dnos")  or "")[:24],
                    "vrfs":  int(d.get("vrfs") or 0),
                    "x":     int(dx) if isinstance(dx, (int, float)) else None,
                    "y":     int(dy) if isinstance(dy, (int, float)) else None,
                })
            else:
                truncated_devices += 1
        for l in raw_links:
            if not isinstance(l, dict):
                continue
            if len(links) < _MAX_LINKS:
                # Pull both the numeric ids and the human labels so the
                # LLM can cross-reference links against the devices[]
                # block without a separate id lookup. Frontend
                # `_collectCanvasSnapshot` writes these as `from`/`to`
                # (ids) + `from_label`/`to_label`.
                links.append({
                    "a":        str(l.get("from") or "")[:40],
                    "b":        str(l.get("to")   or "")[:40],
                    "a_label":  str(l.get("from_label") or "")[:40],
                    "b_label":  str(l.get("to_label")   or "")[:40],
                    "linkType": str(l.get("linkType") or "")[:16],
                    "speed":    str(l.get("speed") or l.get("capacity") or "")[:16],
                })
            else:
                truncated_links += 1
        # Counts for shapes/texts come straight from the frontend's
        # `counts` block since topology-ai.js doesn't forward the raw
        # text/shape objects (intentional -- saves bytes on the wire).
        counts = snapshot.get("counts") or {}
        if isinstance(counts, dict):
            try:
                shape_count = int(counts.get("shapes") or 0)
            except (TypeError, ValueError):
                shape_count = 0
            # `text_count` below uses this:
            try:
                truncated_texts = max(0, int(counts.get("texts") or 0))
            except (TypeError, ValueError):
                truncated_texts = 0

    selection: List[str] = []
    for sel in snapshot.get("selection") or []:
        if isinstance(sel, str):
            selection.append(sel[:40])
        elif isinstance(sel, dict) and sel.get("id"):
            selection.append(str(sel["id"])[:40])

    # Topology / domain metadata lives at different keys depending on
    # the snapshot shape. Accept both.
    topo = snapshot.get("topology") if isinstance(snapshot.get("topology"), dict) else {}
    topology_name = (
        (topo.get("name") if topo else None)
        or snapshot.get("topology_name")
        or snapshot.get("name")
        or ""
    )
    domain_name = (
        (topo.get("domain") if topo else None)
        or snapshot.get("domain")
        or ""
    )
    section_id = (
        (topo.get("section_id") if topo else None)
        or snapshot.get("section_id")
        or ""
    )

    out: Dict[str, Any] = {
        "topology_name": str(topology_name)[:80],
        "domain":        str(domain_name)[:40],
        "section_id":    str(section_id)[:40],
        "device_count":  len(devices) + truncated_devices,
        "link_count":    len(links) + truncated_links,
        "text_count":    len(texts) + truncated_texts,
        "shape_count":   shape_count,
        "devices":       devices,
        "links":         links,
        "texts":         texts,
        "selection":     selection,
    }
    # 2026-04-24q -- viewport info (zoom, pan, visible world rect).
    # Passing this through lets the LLM map natural-language regions
    # like "top-left", "near the selection", "next to spine-1 but
    # off-screen to the right" to real world coordinates. We accept
    # either a dict shape (normal case) or silently drop on anything
    # unexpected so a future frontend refactor can't crash the chat.
    vp = snapshot.get("viewport")
    if isinstance(vp, dict):
        # Keep only well-typed primitives so the JSON we splice into
        # the system prompt is small and deterministic.
        safe_vp: Dict[str, Any] = {}
        try:
            if isinstance(vp.get("zoom"), (int, float)):
                safe_vp["zoom"] = float(vp["zoom"])
            for k in ("pan", "canvas_px", "visible_world"):
                sub = vp.get(k)
                if isinstance(sub, dict):
                    safe_vp[k] = {
                        kk: int(vv) for kk, vv in sub.items()
                        if isinstance(vv, (int, float))
                    }
            if safe_vp:
                out["viewport"] = safe_vp
        except Exception:
            pass
    if truncated_devices:
        out["devices_truncated"] = truncated_devices
    if truncated_links:
        out["links_truncated"] = truncated_links
    if truncated_texts and texts:
        out["texts_truncated"] = truncated_texts

    # 2026-04-24r -- add a short prose `summary` line alongside the
    # structured JSON. LLMs reliably scan "Canvas has 3 PEs, 2 Ps, 8
    # links" faster than they count fields inside the JSON block, and
    # the serve-side system prompt surfaces this line above the block
    # so even a small/cheap model can tell empty from 50-device canvas
    # at a glance.
    out["summary"] = _narrative_canvas_summary(out)
    return out


def _narrative_canvas_summary(canvas: Dict[str, Any]) -> str:
    """One-line human-readable summary of the canvas block.

    Examples:
      - "Canvas is empty (no devices yet)."
      - "Canvas has 3 devices (3 router), 2 links (2 ibgp) on 'dc1'."
      - "Canvas has 4 devices (2 pe, 2 p), 6 links (4 isis, 2 custom),
         1 selected on 'fabric' in 'dc-west'."
    """
    devs  = canvas.get("devices")  or []
    links = canvas.get("links")    or []
    sel   = canvas.get("selection") or []

    role_counts: Dict[str, int] = {}
    for d in devs:
        r = (d.get("role") or "").strip().lower() or "device"
        role_counts[r] = role_counts.get(r, 0) + 1
    link_counts: Dict[str, int] = {}
    for l in links:
        lt = (l.get("linkType") or "").strip().lower() or "default"
        link_counts[lt] = link_counts.get(lt, 0) + 1

    dcount = int(canvas.get("device_count") or len(devs))
    lcount = int(canvas.get("link_count")   or len(links))
    scount = len(sel)

    if dcount == 0 and lcount == 0 and scount == 0:
        return "Canvas is empty (no devices yet)."

    def _fmt_counts(counts: Dict[str, int]) -> str:
        ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        return ", ".join(f"{n} {k}" for k, n in ordered if k)

    role_str = _fmt_counts(role_counts)
    link_str = _fmt_counts(link_counts)

    parts: List[str] = []
    parts.append(f"{dcount} device{'s' if dcount != 1 else ''}"
                 + (f" ({role_str})" if role_str else ""))
    if lcount:
        parts.append(f"{lcount} link{'s' if lcount != 1 else ''}"
                     + (f" ({link_str})" if link_str else ""))
    if scount:
        parts.append(f"{scount} selected")

    name   = (canvas.get("topology_name") or "").strip()
    domain = (canvas.get("domain")        or "").strip()
    loc = ""
    if name and domain:
        loc = f" on '{name}' in '{domain}'"
    elif name:
        loc = f" on '{name}'"
    elif domain:
        loc = f" in '{domain}'"

    return "Canvas has " + ", ".join(parts) + loc + "."


def _workspace_block(username: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {"domains": [], "recent_topologies": []}
    if user_store is None or not username:
        return out
    try:
        domains = user_store.list_domains(username) or []
    except Exception:
        domains = []
    compact_domains: List[Dict[str, Any]] = []
    for d in domains[:_MAX_DOMAINS]:
        compact_domains.append({
            "id": str(d.get("id") or "")[:40],
            "name": str(d.get("name") or "")[:40],
            "topology_count": int(d.get("topology_count") or 0),
            "is_built_in": bool(d.get("is_built_in")),
            "is_shared": bool(d.get("is_shared")),
        })
    out["domains"] = compact_domains

    recent: List[Dict[str, Any]] = []
    for d in domains[:_MAX_DOMAINS]:
        did = d.get("id")
        if not did or d.get("is_shared_with_me_domain"):
            continue
        try:
            topos = user_store.list_topologies(username, did) or []
        except Exception:
            topos = []
        for t in topos:
            recent.append({
                "name": str(t.get("name") or "")[:60],
                "domain": str(d.get("name") or "")[:40],
                "domain_id": did,
                "updated_at": t.get("updated_at") or "",
                "device_count": int(t.get("device_count") or 0),
                "link_count": int(t.get("link_count") or 0),
            })
    recent.sort(key=lambda r: r.get("updated_at") or "", reverse=True)
    out["recent_topologies"] = recent[:_MAX_RECENT_TOPOS]
    return out


def _events_block(username: str) -> List[Dict[str, Any]]:
    """Best-effort: peek at the per-user topology event bus if available.

    The in-tree event bus is TopologyEvents on the frontend side; the
    backend equivalent (api/event_bus.py) is per-device, not per-user.
    We treat this block as optional. A future phase can add a proper
    per-user bus -- until then the frontend injects recent events into
    the canvas snapshot directly, and we surface those.
    """
    return []


def _devices_block(username: str) -> List[Dict[str, Any]]:
    """Best-effort device inventory hints (labels + roles, never creds)."""
    if user_store is None or not username:
        return []
    try:
        path = user_store.user_devices_db_path(username)
    except Exception:
        return []
    if not path or not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, dict):
        return []
    devices = data.get("devices") or []
    out: List[Dict[str, Any]] = []
    for d in devices[:50]:
        if not isinstance(d, dict):
            continue
        out.append({
            "label": str(d.get("label") or d.get("name") or "")[:40],
            "role": str(d.get("role") or d.get("deviceType") or "")[:24],
        })
    return out


def context_size_bytes(ctx: Dict[str, Any]) -> int:
    """Quick diagnostic: how big is the serialized context?"""
    try:
        return len(json.dumps(ctx, separators=(",", ":")).encode("utf-8"))
    except Exception:
        return -1
