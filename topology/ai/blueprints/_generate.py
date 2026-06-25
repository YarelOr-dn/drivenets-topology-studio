"""Blueprint generator (one-shot).

Run from this directory: ``python3 _generate.py``. Writes all canonical
blueprint JSON files under this tree. Overwrites on every run -- treat
the .json output as authoritative (edit those directly, not this
script) for any post-generation tweaks. The script is kept in-tree so
the initial corpus is reproducible and future bulk additions stay
consistent.

Every blueprint produced here follows the per-protocol visual
conventions documented in knowledge.md and topology-link-styles.js.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


HERE = Path(__file__).parent

# ---------------------------------------------------------------------------
# Shared palette (mirrors topology-link-styles.js).
# ---------------------------------------------------------------------------
COL_IBGP = "#3498db"
COL_EBGP = "#e67e22"
COL_BGP = "#e67e22"
COL_OSPF = "#27ae60"
COL_ISIS = "#9b59b6"
COL_MPLS = "#e74c3c"
COL_SR = "#c0392b"
COL_EVPN = "#1abc9c"
COL_VXLAN = "#8e44ad"
COL_PW = "#16a085"
COL_DNAAS = "#00b4d8"

# Device colors
COL_DEV_SPINE = "#2980b9"
COL_DEV_LEAF = "#27ae60"
COL_DEV_RR = "#f39c12"
COL_DEV_PE = "#9b59b6"
COL_DEV_P = "#34495e"
COL_DEV_CE = "#16a085"
COL_DEV_ABR = "#e67e22"
COL_DEV_CORE = "#34495e"
COL_DEV_DIST = "#7f8c8d"
COL_DEV_ACCESS = "#95a5a6"
COL_DEV_CLOUD = "#bdc3c7"
COL_DEV_NCP = "#2c3e50"
COL_DEV_NCF = "#2980b9"

# AS / area translucent fills
COL_AS_BLUE = "#3498db"
COL_AS_ORANGE = "#e67e22"
COL_AS_PURPLE = "#9b59b6"
COL_AREA_0 = "#95a5a6"
COL_AREA_1 = "#27ae60"
COL_AREA_2 = "#e67e22"
COL_AREA_3 = "#9b59b6"

TEXT_BG_DARK = "#0f172a"
TEXT_BG_LIGHT = "#f1f5f9"


def device(id_, label, x, y, role, visual_style="classic", color=None, ip=None, radius=None):
    d: Dict[str, Any] = {
        "id": id_,
        "type": "device",
        "label": label,
        "x": x,
        "y": y,
        "role": role,
        "visualStyle": visual_style,
    }
    if color:
        d["color"] = color
    if ip:
        d["ip"] = ip
    if radius is not None:
        d["radius"] = radius
    return d


def link(id_, a, b, link_type="default", color=None, style=None, width=None, label=None):
    l: Dict[str, Any] = {
        "id": id_,
        "type": "link",
        "device1": a,
        "device2": b,
    }
    if link_type and link_type != "default":
        l["linkType"] = link_type
    if color:
        l["color"] = color
    if style:
        l["style"] = style
    if width:
        l["width"] = width
    if label:
        l["label"] = label
    return l


def shape(id_, shape_type, x, y, width, height, fill_color=None, fill_opacity=None,
          stroke_color=None, stroke_width=None, corner_radius=None, rotation=None,
          label=None):
    s: Dict[str, Any] = {
        "id": id_,
        "type": "shape",
        "shapeType": shape_type,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
    }
    if fill_color:
        s["fillColor"] = fill_color
        s["fillEnabled"] = True
    if fill_opacity is not None:
        s["fillOpacity"] = fill_opacity
    if stroke_color:
        s["strokeColor"] = stroke_color
        s["strokeEnabled"] = True
    if stroke_width is not None:
        s["strokeWidth"] = stroke_width
    if corner_radius is not None:
        s["cornerRadius"] = corner_radius
    if rotation is not None:
        s["rotation"] = rotation
    if label:
        s["label"] = label
    return s


def text(id_, content, x, y, *, font_size=14, color="#e2e8f0",
         show_background=True, background_color=TEXT_BG_DARK,
         background_opacity=0.85, background_padding=8,
         show_border=False, border_color="#334155", border_width=1):
    t: Dict[str, Any] = {
        "id": id_,
        "type": "text",
        "text": content,
        "x": x,
        "y": y,
        "fontSize": font_size,
        "color": color,
        "showBackground": show_background,
        "backgroundColor": background_color,
        "backgroundOpacity": background_opacity,
        "backgroundPadding": background_padding,
    }
    if show_border:
        t["showBorder"] = True
        t["borderColor"] = border_color
        t["borderWidth"] = border_width
    return t


def write_blueprint(path: Path, meta: Dict[str, Any], objects: List[Dict[str, Any]]) -> None:
    payload = {
        "name": path.stem,
        "protocol": meta["protocol"],
        "scale": meta["scale"],
        "summary": meta["summary"],
        "tags": meta.get("tags", []),
        "layout_hint": meta.get("layout_hint"),
        "objects": objects,
    }
    # Remove None-valued optional keys to keep JSON tidy.
    payload = {k: v for k, v in payload.items() if v is not None}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


# ===========================================================================
# BGP
# ===========================================================================
def bgp_ibgp_full_mesh_4():
    objs: List[Dict[str, Any]] = []
    # 4 routers in a square, full-mesh iBGP
    coords = [("R1", 400, 280), ("R2", 1000, 280), ("R3", 1000, 720), ("R4", 400, 720)]
    ips = {"R1": "10.0.0.1", "R2": "10.0.0.2", "R3": "10.0.0.3", "R4": "10.0.0.4"}
    objs.append(shape("as1", "rectangle", 700, 500, 900, 640,
                      fill_color=COL_AS_BLUE, fill_opacity=0.08,
                      stroke_color=COL_AS_BLUE, stroke_width=2,
                      corner_radius=14, label="AS 65001"))
    for name, x, y in coords:
        objs.append(device(name.lower(), name, x, y, "pe", "classic",
                           color=COL_DEV_PE, ip=ips[name]))
    # Full-mesh iBGP (6 links in a 4-node mesh)
    pairs = [("r1","r2"), ("r1","r3"), ("r1","r4"), ("r2","r3"), ("r2","r4"), ("r3","r4")]
    for i, (a, b) in enumerate(pairs):
        objs.append(link(f"l_{a}_{b}", a, b, "ibgp", color=COL_IBGP, style="dashed",
                         label="iBGP"))
    objs.append(text("t_title", "iBGP Full Mesh (4 nodes)", 700, 160, font_size=20))
    objs.append(text("t_note", "AS 65001 -- every speaker peers with every other\n"
                              "BGP session count = n(n-1)/2 = 6",
                     700, 840, font_size=13, show_border=True))
    return objs, {
        "protocol": "ibgp",
        "scale": "small",
        "summary": "Classic 4-node iBGP full mesh. Every router peers with every other; "
                   "session count scales as n(n-1)/2 -- the reason Route Reflectors exist.",
        "tags": ["ibgp", "full-mesh", "4-node"],
        "layout_hint": "mesh",
    }


def bgp_ibgp_rr_hub_spoke_6():
    objs: List[Dict[str, Any]] = []
    # Two RRs (redundant) hub, 4 clients
    objs.append(shape("as1", "rectangle", 800, 540, 1100, 700,
                      fill_color=COL_AS_BLUE, fill_opacity=0.08,
                      stroke_color=COL_AS_BLUE, stroke_width=2,
                      corner_radius=14, label="AS 65001"))
    objs.append(device("rr1", "RR-1", 600, 340, "rr", "hex", color=COL_DEV_RR, ip="10.0.0.101", radius=45))
    objs.append(device("rr2", "RR-2", 1000, 340, "rr", "hex", color=COL_DEV_RR, ip="10.0.0.102", radius=45))
    clients = [("PE-1", 360, 700), ("PE-2", 660, 820), ("PE-3", 960, 820), ("PE-4", 1260, 700)]
    for name, x, y in clients:
        cid = name.lower().replace("-", "")
        ip = f"10.0.0.{int(name.split('-')[1]) + 10}"
        objs.append(device(cid, name, x, y, "pe", "classic", color=COL_DEV_PE, ip=ip))
    # RR-RR peer (iBGP between RRs)
    objs.append(link("l_rr1_rr2", "rr1", "rr2", "ibgp", color=COL_IBGP, style="dashed",
                     width=3, label="iBGP RR-RR"))
    # Each client peers with both RRs
    client_ids = ["pe1", "pe2", "pe3", "pe4"]
    for cid in client_ids:
        objs.append(link(f"l_{cid}_rr1", cid, "rr1", "ibgp", color=COL_IBGP, style="dashed"))
        objs.append(link(f"l_{cid}_rr2", cid, "rr2", "ibgp", color=COL_IBGP, style="dashed"))
    objs.append(text("t_title", "iBGP with Redundant Route Reflectors", 800, 180, font_size=20))
    objs.append(text("t_rr", "RR-1 + RR-2 (cluster-id shared)\nN RR-clients = N iBGP sessions\n(not N(N-1)/2)",
                     280, 280, font_size=12, show_border=True))
    objs.append(text("t_legend", "Clients: PE-1 .. PE-4\nEach peers with BOTH RRs\nfor redundancy",
                     1340, 280, font_size=12, show_border=True))
    return objs, {
        "protocol": "ibgp",
        "scale": "medium",
        "summary": "iBGP with a redundant Route-Reflector pair. Each PE peers with both RRs "
                   "(N sessions per client) and the RRs peer with each other; the classic "
                   "scaling fix to the N^2 iBGP full-mesh problem.",
        "tags": ["ibgp", "route-reflector", "rr", "hub-spoke", "6-node"],
        "layout_hint": "hub-spoke",
    }


def bgp_ebgp_2as_transit():
    objs: List[Dict[str, Any]] = []
    # AS65001 (left) -- AS65002 transit (middle) -- AS65003 (right)
    # ASBR-1 -- P(transit) -- ASBR-2, with local PE in each AS
    objs.append(shape("as1", "rectangle", 300, 500, 380, 560,
                      fill_color=COL_AS_BLUE, fill_opacity=0.08,
                      stroke_color=COL_AS_BLUE, stroke_width=2,
                      corner_radius=14, label="AS 65001"))
    objs.append(shape("as2", "rectangle", 920, 500, 440, 560,
                      fill_color=COL_AS_ORANGE, fill_opacity=0.08,
                      stroke_color=COL_AS_ORANGE, stroke_width=2,
                      corner_radius=14, label="AS 65002 (Transit)"))
    objs.append(shape("as3", "rectangle", 1540, 500, 380, 560,
                      fill_color=COL_AS_PURPLE, fill_opacity=0.08,
                      stroke_color=COL_AS_PURPLE, stroke_width=2,
                      corner_radius=14, label="AS 65003"))

    objs.append(device("pe_a", "PE-A", 220, 400, "pe", "classic", color=COL_DEV_PE, ip="10.1.0.1"))
    objs.append(device("asbr_a", "ASBR-A", 460, 620, "pe", "classic", color=COL_DEV_PE, ip="10.1.0.2"))
    objs.append(device("p1", "P1-Transit", 780, 400, "p", "classic", color=COL_DEV_P, ip="10.2.0.1"))
    objs.append(device("p2", "P2-Transit", 1080, 620, "p", "classic", color=COL_DEV_P, ip="10.2.0.2"))
    objs.append(device("asbr_b", "ASBR-B", 1380, 400, "pe", "classic", color=COL_DEV_PE, ip="10.3.0.1"))
    objs.append(device("pe_b", "PE-B", 1640, 620, "pe", "classic", color=COL_DEV_PE, ip="10.3.0.2"))

    # Intra-AS iBGP + IGP
    objs.append(link("l1", "pe_a", "asbr_a", "ibgp", color=COL_IBGP, style="dashed", label="iBGP"))
    objs.append(link("l2", "p1", "p2", "ibgp", color=COL_IBGP, style="dashed", label="iBGP"))
    objs.append(link("l3", "asbr_b", "pe_b", "ibgp", color=COL_IBGP, style="dashed", label="iBGP"))
    # eBGP transit
    objs.append(link("l4", "asbr_a", "p1", "ebgp", color=COL_EBGP, style="arrow", width=3, label="eBGP"))
    objs.append(link("l5", "p2", "asbr_b", "ebgp", color=COL_EBGP, style="arrow", width=3, label="eBGP"))

    objs.append(text("t_title", "eBGP Transit between 3 ASes", 1100, 160, font_size=20))
    objs.append(text("t_note",
                     "eBGP (orange/arrow) crosses AS boundaries\niBGP (blue/dashed) stays inside an AS",
                     1100, 940, font_size=12, show_border=True))
    return objs, {
        "protocol": "ebgp",
        "scale": "medium",
        "summary": "eBGP transit between three ASes. AS 65002 transits routes between "
                   "AS 65001 and AS 65003; iBGP inside each AS, eBGP at the boundaries.",
        "tags": ["ebgp", "transit", "3-as", "asbr"],
    }


def bgp_ixp_route_server():
    objs: List[Dict[str, Any]] = []
    # Central IXP route-server with N member ASes around it
    objs.append(shape("ixp", "ellipse", 960, 540, 520, 520,
                      fill_color="#1abc9c", fill_opacity=0.1,
                      stroke_color="#1abc9c", stroke_width=2, label="IXP Fabric"))
    objs.append(device("rs", "Route-Server", 960, 540, "rr", "hex", color=COL_DEV_RR,
                       ip="198.51.100.1", radius=55))
    members = [("AS65010", 0), ("AS65020", 60), ("AS65030", 120), ("AS65040", 180),
               ("AS65050", 240), ("AS65060", 300)]
    for i, (as_name, angle) in enumerate(members):
        rad = math.radians(angle)
        mx = 960 + 360 * math.cos(rad)
        my = 540 + 360 * math.sin(rad)
        mid = f"m{i+1}"
        objs.append(device(mid, as_name, mx, my, "pe", "classic", color=COL_DEV_PE,
                           ip=f"198.51.100.{10 + i}"))
        objs.append(link(f"l_rs_{mid}", "rs", mid, "ebgp", color=COL_EBGP, style="arrow",
                         label="multi-hop eBGP"))
    objs.append(text("t_title", "Internet Exchange Point (Route-Server Model)", 960, 120, font_size=20))
    objs.append(text("t_note",
                     "Each member establishes a single eBGP session\nwith the Route-Server instead of a full mesh\nof N(N-1)/2 pairwise peerings",
                     960, 960, font_size=12, show_border=True))
    return objs, {
        "protocol": "ebgp",
        "scale": "medium",
        "summary": "IXP route-server topology. Each member AS peers with a single "
                   "central route-server instead of building a full mesh, scaling peering "
                   "from N^2 to N sessions.",
        "tags": ["ebgp", "ixp", "route-server", "peering"],
    }


def bgp_confederation():
    objs: List[Dict[str, Any]] = []
    # AS 65000 broken into two sub-ASes: 65001 and 65002. Full mesh iBGP
    # inside each sub-AS, eBGP (inter-confederation) between sub-ASes.
    objs.append(shape("conf", "rectangle", 1020, 540, 1680, 760,
                      fill_color="#bdc3c7", fill_opacity=0.06,
                      stroke_color="#7f8c8d", stroke_width=3,
                      corner_radius=18, label="AS 65000 (Confederation)"))
    objs.append(shape("sub1", "rectangle", 500, 540, 660, 560,
                      fill_color=COL_AS_BLUE, fill_opacity=0.1,
                      stroke_color=COL_AS_BLUE, stroke_width=2,
                      corner_radius=14, label="Sub-AS 65501"))
    objs.append(shape("sub2", "rectangle", 1540, 540, 660, 560,
                      fill_color=COL_AS_ORANGE, fill_opacity=0.1,
                      stroke_color=COL_AS_ORANGE, stroke_width=2,
                      corner_radius=14, label="Sub-AS 65502"))

    subs = [
        ("r1", "R1", 320, 380, "sub1"), ("r2", "R2", 680, 380, "sub1"),
        ("r3", "R3", 500, 700, "sub1"),
        ("r4", "R4", 1360, 380, "sub2"), ("r5", "R5", 1720, 380, "sub2"),
        ("r6", "R6", 1540, 700, "sub2"),
    ]
    for rid, label, x, y, _ in subs:
        objs.append(device(rid, label, x, y, "pe", "classic", color=COL_DEV_PE))
    # iBGP full mesh within each sub-AS
    for a, b in [("r1","r2"), ("r1","r3"), ("r2","r3")]:
        objs.append(link(f"l_{a}_{b}", a, b, "ibgp", color=COL_IBGP, style="dashed", label="iBGP"))
    for a, b in [("r4","r5"), ("r4","r6"), ("r5","r6")]:
        objs.append(link(f"l_{a}_{b}", a, b, "ibgp", color=COL_IBGP, style="dashed", label="iBGP"))
    # Inter-confederation eBGP border
    objs.append(link("l_r2_r4", "r2", "r4", "ebgp", color=COL_EBGP, style="arrow",
                     width=3, label="confed-eBGP"))
    objs.append(link("l_r3_r6", "r3", "r6", "ebgp", color=COL_EBGP, style="arrow",
                     width=3, label="confed-eBGP"))

    objs.append(text("t_title", "BGP Confederation (AS 65000 split into two sub-ASes)", 1020, 120, font_size=20))
    objs.append(text("t_note",
                     "Outside the confederation: AS 65000\nInside: sub-ASes 65501 and 65502\nFull mesh iBGP inside each sub-AS,\neBGP between sub-ASes.",
                     1020, 960, font_size=12, show_border=True))
    return objs, {
        "protocol": "bgp",
        "scale": "medium",
        "summary": "BGP confederation: AS 65000 split into two private sub-ASes (65501 / "
                   "65502) to scale iBGP. Full-mesh iBGP inside each sub-AS, confederation "
                   "eBGP between them.",
        "tags": ["ibgp", "ebgp", "confederation", "scaling"],
    }


# ===========================================================================
# OSPF
# ===========================================================================
def ospf_single_area_5():
    objs: List[Dict[str, Any]] = []
    objs.append(shape("area0", "ellipse", 960, 540, 1280, 620,
                      fill_color=COL_AREA_0, fill_opacity=0.10,
                      stroke_color=COL_AREA_0, stroke_width=2,
                      label="OSPF Area 0 (backbone)"))
    coords = [("R1", 420, 400), ("R2", 740, 320), ("R3", 1180, 320),
              ("R4", 1500, 400), ("R5", 960, 740)]
    for name, x, y in coords:
        objs.append(device(name.lower(), name, x, y, "p", "classic",
                           color=COL_DEV_P, ip=f"10.0.0.{name[-1]}"))
    pairs = [("r1","r2"), ("r2","r3"), ("r3","r4"),
             ("r1","r5"), ("r2","r5"), ("r3","r5"), ("r4","r5")]
    for a, b in pairs:
        objs.append(link(f"l_{a}_{b}", a, b, "ospf", color=COL_OSPF, style="solid",
                         label="OSPF a0"))
    objs.append(text("t_title", "OSPF Single Area (backbone)", 960, 160, font_size=20))
    objs.append(text("t_note", "All routers in Area 0\nDR/BDR elected per broadcast link",
                     960, 900, font_size=12, show_border=True))
    return objs, {
        "protocol": "ospf",
        "scale": "small",
        "summary": "OSPF single-area (Area 0) baseline. Five routers all speaking OSPF in the "
                   "backbone area -- the starting point before partitioning into multi-area.",
        "tags": ["ospf", "single-area", "area-0", "5-node"],
    }


def ospf_multi_area_0_1_2():
    objs: List[Dict[str, Any]] = []
    # Area 1 (left) -- Area 0 backbone (middle) -- Area 2 (right)
    objs.append(shape("a1", "ellipse", 420, 540, 520, 600,
                      fill_color=COL_AREA_1, fill_opacity=0.10,
                      stroke_color=COL_AREA_1, stroke_width=2, label="Area 1"))
    objs.append(shape("a0", "ellipse", 1000, 540, 580, 600,
                      fill_color=COL_AREA_0, fill_opacity=0.10,
                      stroke_color=COL_AREA_0, stroke_width=2, label="Area 0 (backbone)"))
    objs.append(shape("a2", "ellipse", 1580, 540, 520, 600,
                      fill_color=COL_AREA_2, fill_opacity=0.10,
                      stroke_color=COL_AREA_2, stroke_width=2, label="Area 2"))

    # Area 1 internal
    objs.append(device("r1", "R1", 260, 420, "p", "classic", color=COL_DEV_P))
    objs.append(device("r2", "R2", 260, 660, "p", "classic", color=COL_DEV_P))
    objs.append(device("abr1", "ABR-1", 580, 540, "p", "classic", color=COL_DEV_ABR, radius=45))
    # Area 0 backbone
    objs.append(device("bb1", "BB-1", 880, 400, "p", "classic", color=COL_DEV_CORE))
    objs.append(device("bb2", "BB-2", 1120, 400, "p", "classic", color=COL_DEV_CORE))
    objs.append(device("bb3", "BB-3", 1000, 680, "p", "classic", color=COL_DEV_CORE))
    # Area 2 internal
    objs.append(device("abr2", "ABR-2", 1420, 540, "p", "classic", color=COL_DEV_ABR, radius=45))
    objs.append(device("r3", "R3", 1740, 420, "p", "classic", color=COL_DEV_P))
    objs.append(device("r4", "R4", 1740, 660, "p", "classic", color=COL_DEV_P))

    # OSPF links
    def add(a, b, lbl):
        objs.append(link(f"l_{a}_{b}", a, b, "ospf", color=COL_OSPF, style="solid", label=lbl))
    add("r1", "abr1", "OSPF a1")
    add("r2", "abr1", "OSPF a1")
    add("abr1", "bb1", "OSPF a0")
    add("abr1", "bb3", "OSPF a0")
    add("bb1", "bb2", "OSPF a0")
    add("bb2", "bb3", "OSPF a0")
    add("bb2", "abr2", "OSPF a0")
    add("bb3", "abr2", "OSPF a0")
    add("abr2", "r3", "OSPF a2")
    add("abr2", "r4", "OSPF a2")

    objs.append(text("t_title", "OSPF Multi-Area (Area 0 / 1 / 2)", 1000, 140, font_size=20))
    objs.append(text("t_abr", "ABR = Area Border Router\nMaintains a separate LSDB per area",
                     580, 260, font_size=12, show_border=True))
    objs.append(text("t_rules",
                     "All non-backbone areas attach to Area 0\nvia an ABR (or a virtual link).",
                     1000, 940, font_size=12, show_border=True))
    return objs, {
        "protocol": "ospf",
        "scale": "medium",
        "summary": "OSPF multi-area: Area 0 backbone with two ABRs fan-out to Area 1 and "
                   "Area 2. Canonical LSDB-scaling design.",
        "tags": ["ospf", "multi-area", "abr", "area-0", "area-1", "area-2"],
    }


def ospf_totally_stubby():
    objs: List[Dict[str, Any]] = []
    objs.append(shape("a0", "ellipse", 600, 540, 520, 620,
                      fill_color=COL_AREA_0, fill_opacity=0.10,
                      stroke_color=COL_AREA_0, stroke_width=2, label="Area 0"))
    objs.append(shape("a10", "ellipse", 1400, 540, 520, 620,
                      fill_color=COL_AREA_2, fill_opacity=0.10,
                      stroke_color=COL_AREA_2, stroke_width=2,
                      label="Area 10 (Totally Stubby)"))
    objs.append(device("bb1", "BB-1", 420, 400, "p", "classic", color=COL_DEV_CORE))
    objs.append(device("bb2", "BB-2", 420, 680, "p", "classic", color=COL_DEV_CORE))
    objs.append(device("abr", "ABR", 900, 540, "p", "classic", color=COL_DEV_ABR, radius=50))
    objs.append(device("r1", "R1-stub", 1240, 400, "p", "classic", color=COL_DEV_P))
    objs.append(device("r2", "R2-stub", 1240, 680, "p", "classic", color=COL_DEV_P))
    objs.append(device("r3", "R3-stub", 1580, 540, "p", "classic", color=COL_DEV_P))

    for a, b in [("bb1","bb2"), ("bb1","abr"), ("bb2","abr")]:
        objs.append(link(f"l_{a}_{b}", a, b, "ospf", color=COL_OSPF, style="solid", label="a0"))
    for a, b in [("abr","r1"), ("abr","r2"), ("r1","r3"), ("r2","r3")]:
        objs.append(link(f"l_{a}_{b}", a, b, "ospf", color=COL_OSPF, style="solid", label="a10"))

    objs.append(text("t_title", "OSPF Totally Stubby Area", 1000, 140, font_size=20))
    objs.append(text("t_stubby",
                     "Totally Stubby: inter-area LSAs and\nexternal LSAs (Type-5) blocked.\nDefault route (0.0.0.0/0) injected\nby the ABR.",
                     1400, 920, font_size=12, show_border=True))
    return objs, {
        "protocol": "ospf",
        "scale": "small",
        "summary": "OSPF totally stubby area. The ABR blocks both Type-3 and Type-5 LSAs "
                   "into the stub; internal routers rely on a single 0.0.0.0/0 default.",
        "tags": ["ospf", "totally-stubby", "area-10", "abr", "default-route"],
    }


def ospf_abr_dr_hierarchy():
    objs: List[Dict[str, Any]] = []
    objs.append(shape("a0", "ellipse", 960, 380, 1280, 400,
                      fill_color=COL_AREA_0, fill_opacity=0.10,
                      stroke_color=COL_AREA_0, stroke_width=2, label="Area 0"))
    objs.append(shape("a1", "ellipse", 520, 780, 640, 400,
                      fill_color=COL_AREA_1, fill_opacity=0.10,
                      stroke_color=COL_AREA_1, stroke_width=2, label="Area 1"))
    objs.append(shape("a2", "ellipse", 1400, 780, 640, 400,
                      fill_color=COL_AREA_2, fill_opacity=0.10,
                      stroke_color=COL_AREA_2, stroke_width=2, label="Area 2"))

    objs.append(device("dr", "DR", 960, 380, "p", "classic", color=COL_DEV_CORE, radius=55))
    objs.append(device("bdr", "BDR", 640, 380, "p", "classic", color=COL_DEV_CORE, radius=48))
    objs.append(device("dr_other", "DR-Other", 1280, 380, "p", "classic", color=COL_DEV_P))
    objs.append(device("abr1", "ABR-1", 520, 620, "p", "classic", color=COL_DEV_ABR, radius=48))
    objs.append(device("abr2", "ABR-2", 1400, 620, "p", "classic", color=COL_DEV_ABR, radius=48))
    objs.append(device("a1_r1", "A1-R1", 320, 900, "p", "classic", color=COL_DEV_P))
    objs.append(device("a1_r2", "A1-R2", 720, 900, "p", "classic", color=COL_DEV_P))
    objs.append(device("a2_r1", "A2-R1", 1200, 900, "p", "classic", color=COL_DEV_P))
    objs.append(device("a2_r2", "A2-R2", 1600, 900, "p", "classic", color=COL_DEV_P))

    for a, b in [("dr","bdr"), ("dr","dr_other"), ("bdr","dr_other")]:
        objs.append(link(f"l_{a}_{b}", a, b, "ospf", color=COL_OSPF, style="solid", label="a0"))
    for a, b in [("bdr","abr1"), ("dr_other","abr2")]:
        objs.append(link(f"l_{a}_{b}", a, b, "ospf", color=COL_OSPF, style="solid", label="a0"))
    for a, b in [("abr1","a1_r1"), ("abr1","a1_r2"), ("a1_r1","a1_r2")]:
        objs.append(link(f"l_{a}_{b}", a, b, "ospf", color=COL_OSPF, style="solid", label="a1"))
    for a, b in [("abr2","a2_r1"), ("abr2","a2_r2"), ("a2_r1","a2_r2")]:
        objs.append(link(f"l_{a}_{b}", a, b, "ospf", color=COL_OSPF, style="solid", label="a2"))

    objs.append(text("t_title", "OSPF DR/BDR + ABR Hierarchy", 960, 140, font_size=20))
    objs.append(text("t_dr",
                     "DR / BDR elected per broadcast segment\nDR-Other talks only to DR/BDR (224.0.0.6)\nABRs translate between Area 0 and non-zero areas",
                     960, 1060, font_size=12, show_border=True))
    return objs, {
        "protocol": "ospf",
        "scale": "medium",
        "summary": "Full OSPF hierarchy: DR / BDR / DR-Other on a broadcast backbone plus "
                   "two ABRs fan-out into Area 1 and Area 2.",
        "tags": ["ospf", "dr", "bdr", "abr", "multi-area"],
    }


# ===========================================================================
# IS-IS
# ===========================================================================
def isis_l1_l2_hierarchy():
    objs: List[Dict[str, Any]] = []
    objs.append(shape("l1", "rectangle", 500, 700, 660, 460,
                      fill_color=COL_AREA_1, fill_opacity=0.10,
                      stroke_color=COL_AREA_1, stroke_width=2, corner_radius=16,
                      label="Area 49.0001 (L1)"))
    objs.append(shape("l2", "rectangle", 1380, 380, 900, 460,
                      fill_color=COL_AREA_0, fill_opacity=0.10,
                      stroke_color=COL_AREA_0, stroke_width=2, corner_radius=16,
                      label="L2 Backbone"))

    objs.append(device("l1r1", "L1-R1", 280, 600, "p", "classic", color=COL_DEV_P))
    objs.append(device("l1r2", "L1-R2", 280, 820, "p", "classic", color=COL_DEV_P))
    objs.append(device("l1l2a", "L1L2-A", 700, 700, "p", "classic", color=COL_DEV_ABR, radius=48))
    objs.append(device("l2r1", "L2-R1", 1100, 380, "p", "classic", color=COL_DEV_CORE))
    objs.append(device("l2r2", "L2-R2", 1420, 380, "p", "classic", color=COL_DEV_CORE))
    objs.append(device("l2r3", "L2-R3", 1740, 380, "p", "classic", color=COL_DEV_CORE))
    objs.append(device("l1l2b", "L1L2-B", 1420, 620, "p", "classic", color=COL_DEV_ABR, radius=48))

    for a, b in [("l1r1","l1r2"), ("l1r1","l1l2a"), ("l1r2","l1l2a")]:
        objs.append(link(f"l_{a}_{b}", a, b, "isis", color=COL_ISIS, style="solid", label="IS-IS L1"))
    objs.append(link("l_l1l2a_l2r1", "l1l2a", "l2r1", "isis", color=COL_ISIS, style="solid", label="IS-IS L1/L2"))
    for a, b in [("l2r1","l2r2"), ("l2r2","l2r3")]:
        objs.append(link(f"l_{a}_{b}", a, b, "isis", color=COL_ISIS, style="solid", label="IS-IS L2"))
    objs.append(link("l_l2r2_l1l2b", "l2r2", "l1l2b", "isis", color=COL_ISIS, style="solid", label="IS-IS L1/L2"))

    objs.append(text("t_title", "IS-IS L1 + L2 Hierarchy", 1100, 140, font_size=20))
    objs.append(text("t_note",
                     "L1 routers know only Area 49.0001\nL2 routers exchange inter-area reachability\nL1L2 routers sit on the boundary (NET = 49.0001.xxxx.xxxx.xxxx.00)",
                     1100, 1060, font_size=12, show_border=True))
    return objs, {
        "protocol": "isis",
        "scale": "medium",
        "summary": "IS-IS hierarchical design. Area 49.0001 (L1) attaches to the L2 backbone "
                   "via two L1L2 routers. Classic SP backbone topology.",
        "tags": ["isis", "l1", "l2", "hierarchical", "sp-backbone"],
    }


def isis_pure_l2_backbone():
    objs: List[Dict[str, Any]] = []
    objs.append(shape("l2", "rectangle", 960, 540, 1300, 520,
                      fill_color=COL_AREA_0, fill_opacity=0.10,
                      stroke_color=COL_AREA_0, stroke_width=2, corner_radius=16,
                      label="Pure L2 Backbone (Area 49.0000)"))
    coords = [("R1", 420, 420), ("R2", 720, 380), ("R3", 1020, 420),
              ("R4", 1320, 380), ("R5", 1620, 420),
              ("R6", 620, 720), ("R7", 1120, 720), ("R8", 1520, 720)]
    for name, x, y in coords:
        rid = name.lower()
        objs.append(device(rid, name, x, y, "p", "classic", color=COL_DEV_CORE,
                           ip=f"10.0.0.{name[1]}"))
    pairs = [("r1","r2"), ("r2","r3"), ("r3","r4"), ("r4","r5"),
             ("r1","r6"), ("r3","r7"), ("r5","r8"),
             ("r6","r7"), ("r7","r8"), ("r2","r6"), ("r4","r8")]
    for a, b in pairs:
        objs.append(link(f"l_{a}_{b}", a, b, "isis", color=COL_ISIS, style="solid", label="IS-IS L2"))

    objs.append(text("t_title", "IS-IS Pure L2 Backbone (all L2)", 960, 140, font_size=20))
    objs.append(text("t_note",
                     "All 8 routers configured level-2-only.\nSingle Area 49.0000 -- no L1 adjacency.\nPreferred in SP cores where IS-IS is the IGP.",
                     960, 920, font_size=12, show_border=True))
    return objs, {
        "protocol": "isis",
        "scale": "medium",
        "summary": "IS-IS pure-L2 backbone. All routers run level-2-only in a single area -- the "
                   "scale-out IGP choice most SP core networks pick.",
        "tags": ["isis", "l2", "pure-l2", "sp-core", "8-node"],
    }


# ===========================================================================
# MPLS L3VPN
# ===========================================================================
def mpls_l3vpn_2pe_1ce_basic():
    objs: List[Dict[str, Any]] = []
    objs.append(shape("core", "rectangle", 960, 540, 1100, 460,
                      fill_color="#e74c3c", fill_opacity=0.06,
                      stroke_color=COL_MPLS, stroke_width=2, corner_radius=16,
                      label="MPLS Core (AS 65000)"))

    objs.append(device("ce_a", "CE-A", 360, 540, "ce", "simple", color=COL_DEV_CE, ip="192.168.10.1"))
    objs.append(device("pe_a", "PE-A", 660, 540, "pe", "classic", color=COL_DEV_PE, ip="10.0.0.1"))
    objs.append(device("p1", "P1", 960, 420, "p", "classic", color=COL_DEV_P, ip="10.0.0.100"))
    objs.append(device("p2", "P2", 960, 660, "p", "classic", color=COL_DEV_P, ip="10.0.0.101"))
    objs.append(device("pe_b", "PE-B", 1260, 540, "pe", "classic", color=COL_DEV_PE, ip="10.0.0.2"))
    objs.append(device("ce_b", "CE-B", 1560, 540, "ce", "simple", color=COL_DEV_CE, ip="192.168.20.1"))

    # CE-PE eBGP (VRF)
    objs.append(link("l_cea_pea", "ce_a", "pe_a", "ebgp", color=COL_EBGP, style="arrow", label="eBGP VPN-Customer"))
    objs.append(link("l_ceb_peb", "ce_b", "pe_b", "ebgp", color=COL_EBGP, style="arrow", label="eBGP VPN-Customer"))
    # PE-P MPLS
    objs.append(link("l_pea_p1", "pe_a", "p1", "mpls", color=COL_MPLS, style="solid", label="MPLS/LDP"))
    objs.append(link("l_pea_p2", "pe_a", "p2", "mpls", color=COL_MPLS, style="solid", label="MPLS/LDP"))
    objs.append(link("l_p1_peb", "p1", "pe_b", "mpls", color=COL_MPLS, style="solid", label="MPLS/LDP"))
    objs.append(link("l_p2_peb", "p2", "pe_b", "mpls", color=COL_MPLS, style="solid", label="MPLS/LDP"))
    # PE-PE iBGP VPNv4
    objs.append(link("l_pea_peb", "pe_a", "pe_b", "ibgp", color=COL_IBGP, style="dashed",
                     width=3, label="iBGP VPNv4"))

    objs.append(text("t_title", "MPLS L3VPN - 2 PEs + 1 CE per site", 960, 140, font_size=20))
    objs.append(text("t_vrf_a", "VRF CUSTOMER-A\nRD: 65000:100\nRT: 65000:100",
                     360, 400, font_size=12, show_border=True, border_color=COL_EBGP))
    objs.append(text("t_vrf_b", "VRF CUSTOMER-A\nRD: 65000:100\nRT: 65000:100",
                     1560, 400, font_size=12, show_border=True, border_color=COL_EBGP))
    objs.append(text("t_labels", "Two-label forwarding:\n  Outer = LDP transport\n  Inner = VPN label (from MP-BGP)",
                     960, 880, font_size=12, show_border=True, border_color=COL_MPLS))
    return objs, {
        "protocol": "mpls-l3vpn",
        "scale": "small",
        "summary": "Basic MPLS L3VPN: 2 PEs, 2 P routers in the core, 1 CE per site. "
                   "LDP transport label + MP-BGP VPN label two-label forwarding.",
        "tags": ["mpls", "l3vpn", "vrf", "rd-rt", "ibgp", "2pe"],
        "layout_hint": "sp-backbone",
    }


def mpls_l3vpn_4pe_rr_hub():
    objs: List[Dict[str, Any]] = []
    objs.append(shape("core", "rectangle", 960, 560, 1420, 580,
                      fill_color="#e74c3c", fill_opacity=0.06,
                      stroke_color=COL_MPLS, stroke_width=2, corner_radius=16,
                      label="MPLS Core (AS 65000)"))
    # PEs around a central RR
    pe_coords = [("PE-1", 360, 440), ("PE-2", 1560, 440),
                 ("PE-3", 360, 720), ("PE-4", 1560, 720)]
    for name, x, y in pe_coords:
        pid = name.lower().replace("-", "")
        objs.append(device(pid, name, x, y, "pe", "classic", color=COL_DEV_PE,
                           ip=f"10.0.0.{name[-1]}"))
    objs.append(device("rr", "RR-VPNv4", 960, 440, "rr", "hex", color=COL_DEV_RR,
                       ip="10.0.0.50", radius=50))
    objs.append(device("p1", "P1", 720, 560, "p", "classic", color=COL_DEV_P))
    objs.append(device("p2", "P2", 1200, 560, "p", "classic", color=COL_DEV_P))

    # MPLS core
    for a, b in [("pe1","p1"), ("pe3","p1"), ("p1","rr"), ("p1","p2"),
                 ("pe2","p2"), ("pe4","p2"), ("p2","rr")]:
        objs.append(link(f"l_{a}_{b}", a, b, "mpls", color=COL_MPLS, style="solid", label="LDP"))
    # iBGP VPNv4 from each PE to RR
    for pid in ["pe1", "pe2", "pe3", "pe4"]:
        objs.append(link(f"lv_{pid}_rr", pid, "rr", "ibgp", color=COL_IBGP, style="dashed",
                         label="iBGP VPNv4"))

    objs.append(text("t_title", "MPLS L3VPN with VPNv4 Route-Reflector", 960, 140, font_size=20))
    objs.append(text("t_rr",
                     "RR-VPNv4 reflects VPNv4 / VPNv6\n(address-family mp-ibgp) prefixes\ninstead of a full PE mesh.",
                     960, 900, font_size=12, show_border=True, border_color=COL_IBGP))
    return objs, {
        "protocol": "mpls-l3vpn",
        "scale": "medium",
        "summary": "4-PE MPLS L3VPN with a VPNv4 Route-Reflector. Each PE peers only with the RR "
                   "(not a full mesh) for MP-BGP VPN distribution.",
        "tags": ["mpls", "l3vpn", "route-reflector", "vpnv4", "4pe"],
    }


def mpls_l3vpn_multi_site():
    objs: List[Dict[str, Any]] = []
    # Hub PE + 3 spoke PEs, each with a CE (customer site)
    objs.append(shape("core", "rectangle", 960, 540, 1500, 440,
                      fill_color="#e74c3c", fill_opacity=0.06,
                      stroke_color=COL_MPLS, stroke_width=2, corner_radius=16,
                      label="MPLS Core"))
    objs.append(device("hub_pe", "HUB-PE", 960, 540, "pe", "hex", color=COL_DEV_RR, radius=50))
    sites = [("SPK-PE-1", 340, 400, "CE-Site1", 160, 200),
             ("SPK-PE-2", 1580, 400, "CE-Site2", 1760, 200),
             ("SPK-PE-3", 960, 800, "CE-Site3", 960, 1020)]
    p_coords = [("P-N", 640, 440), ("P-S", 1280, 640)]
    for name, x, y in p_coords:
        objs.append(device(name.lower().replace("-", ""), name, x, y, "p", "classic", color=COL_DEV_P))
    for pe, px, py, ce, cx, cy in sites:
        pid = pe.lower().replace("-", "")
        cid = ce.lower().replace("-", "")
        objs.append(device(pid, pe, px, py, "pe", "classic", color=COL_DEV_PE))
        objs.append(device(cid, ce, cx, cy, "ce", "simple", color=COL_DEV_CE))
        objs.append(link(f"l_{cid}_{pid}", cid, pid, "ebgp", color=COL_EBGP, style="arrow", label="CE-PE"))

    # MPLS core fabric
    for a, b in [("spkpe1","pn"), ("spkpe2","ps"), ("spkpe3","ps"),
                 ("pn","hub_pe"), ("ps","hub_pe"), ("pn","ps")]:
        objs.append(link(f"l_{a}_{b}", a, b, "mpls", color=COL_MPLS, style="solid", label="LDP"))
    # iBGP VPNv4 hub-and-spoke
    for pid in ["spkpe1", "spkpe2", "spkpe3"]:
        objs.append(link(f"lv_{pid}_hub", pid, "hub_pe", "ibgp", color=COL_IBGP, style="dashed",
                         label="VPNv4 hub-spoke"))

    objs.append(text("t_title", "Multi-Site MPLS L3VPN (Hub-Spoke)", 960, 120, font_size=20))
    objs.append(text("t_vrfhub", "VRF HUB\nRD 65000:1\nRT export 1:1\nRT import 1:100",
                     960, 700, font_size=11, show_border=True, border_color=COL_IBGP))
    objs.append(text("t_vrfspoke", "VRF SPOKE\nRD 65000:100\nRT export 1:100\nRT import 1:1",
                     1760, 340, font_size=11, show_border=True, border_color=COL_EBGP))
    return objs, {
        "protocol": "mpls-l3vpn",
        "scale": "medium",
        "summary": "Multi-site MPLS L3VPN hub-and-spoke. Three spoke sites share routes via a "
                   "central hub PE using asymmetric RT import/export (classic enterprise "
                   "managed-services VPN design).",
        "tags": ["mpls", "l3vpn", "hub-spoke", "multi-site", "rt-asymmetric"],
    }


# ===========================================================================
# EVPN-VXLAN
# ===========================================================================
def evpn_vxlan_2spine_4leaf_anycast_gw():
    objs: List[Dict[str, Any]] = []
    objs.append(shape("fabric", "rectangle", 960, 520, 1600, 560,
                      fill_color=COL_EVPN, fill_opacity=0.06,
                      stroke_color=COL_EVPN, stroke_width=2, corner_radius=16,
                      label="EVPN-VXLAN Fabric (AS 65100)"))
    objs.append(device("s1", "Spine-1", 660, 320, "spine", "classic", color=COL_DEV_SPINE))
    objs.append(device("s2", "Spine-2", 1260, 320, "spine", "classic", color=COL_DEV_SPINE))
    leaves = [("Leaf-1", 360, 720), ("Leaf-2", 760, 720),
              ("Leaf-3", 1160, 720), ("Leaf-4", 1560, 720)]
    for name, x, y in leaves:
        lid = name.lower().replace("-", "")
        objs.append(device(lid, name, x, y, "leaf", "classic", color=COL_DEV_LEAF))
    # Underlay eBGP + overlay EVPN
    for lid in ["leaf1", "leaf2", "leaf3", "leaf4"]:
        for sid in ["s1", "s2"]:
            objs.append(link(f"lu_{lid}_{sid}", lid, sid, "ebgp", color=COL_EBGP, style="arrow",
                             label="eBGP underlay"))
    for lid in ["leaf1", "leaf2", "leaf3", "leaf4"]:
        for sid in ["s1", "s2"]:
            objs.append(link(f"lo_{lid}_{sid}", lid, sid, "evpn", color=COL_EVPN, style="dashed-wide",
                             label="EVPN overlay"))

    objs.append(text("t_title", "EVPN-VXLAN DC Fabric (2 spine / 4 leaf) - Anycast Gateway", 960, 140, font_size=20))
    objs.append(text("t_vni", "Anycast Gateway IRB\nVNI 10010 (Tenant A)\nVNI 10020 (Tenant B)",
                     260, 400, font_size=11, show_border=True, border_color=COL_EVPN))
    objs.append(text("t_encap",
                     "VXLAN UDP/4789 encapsulation\nBGP-EVPN AF (Type-2/3/5) control plane",
                     1660, 400, font_size=11, show_border=True, border_color=COL_EVPN))
    return objs, {
        "protocol": "evpn-vxlan",
        "scale": "medium",
        "summary": "EVPN-VXLAN DC fabric: 2 spines + 4 leaves with anycast-gateway IRB. "
                   "eBGP underlay (Juniper / Arista / Cisco style), BGP-EVPN overlay.",
        "tags": ["evpn", "vxlan", "spine-leaf", "anycast-gw", "clos-3-stage"],
        "layout_hint": "clos-3-stage",
    }


def evpn_vxlan_edge_routed_bridging():
    objs: List[Dict[str, Any]] = []
    objs.append(shape("fabric", "rectangle", 960, 520, 1520, 540,
                      fill_color=COL_EVPN, fill_opacity=0.06,
                      stroke_color=COL_EVPN, stroke_width=2, corner_radius=16,
                      label="EVPN-VXLAN ERB Fabric"))
    objs.append(device("s1", "Spine-1", 720, 300, "spine", "classic", color=COL_DEV_SPINE))
    objs.append(device("s2", "Spine-2", 1200, 300, "spine", "classic", color=COL_DEV_SPINE))
    leaves_erb = [("L1-Border", 380, 680, "border-leaf"), ("L2-Server", 760, 680, "server-leaf"),
                  ("L3-Server", 1160, 680, "server-leaf"), ("L4-Border", 1540, 680, "border-leaf")]
    for name, x, y, role in leaves_erb:
        lid = name.lower().replace("-", "").replace(" ", "")
        color = "#e67e22" if role.startswith("border") else COL_DEV_LEAF
        objs.append(device(lid, name, x, y, role, "classic", color=color))
    for lid in ["l1border", "l2server", "l3server", "l4border"]:
        for sid in ["s1", "s2"]:
            objs.append(link(f"l_{lid}_{sid}", lid, sid, "evpn", color=COL_EVPN,
                             style="dashed-wide", label="EVPN"))
    # External DC edge
    objs.append(device("wan", "WAN Edge", 960, 960, "pe", "classic", color=COL_DEV_PE))
    objs.append(link("l_l1_wan", "l1border", "wan", "ebgp", color=COL_EBGP, style="arrow", label="eBGP"))
    objs.append(link("l_l4_wan", "l4border", "wan", "ebgp", color=COL_EBGP, style="arrow", label="eBGP"))

    objs.append(text("t_title", "EVPN-VXLAN Edge-Routed Bridging (ERB)", 960, 140, font_size=20))
    objs.append(text("t_erb",
                     "Gateway IRB on the LEAF (border role)\nL2 + L3 VNIs terminate at the edge\nSpine stays pure IP-underlay",
                     280, 400, font_size=11, show_border=True, border_color=COL_EVPN))
    return objs, {
        "protocol": "evpn-vxlan",
        "scale": "medium",
        "summary": "EVPN-VXLAN Edge-Routed Bridging. Border leaves terminate L3 VNIs and peer to "
                   "the WAN edge; server leaves stay pure L2. Modern DC alternative to centralised IRB.",
        "tags": ["evpn", "vxlan", "erb", "border-leaf", "irb"],
        "layout_hint": "clos-3-stage",
    }


def evpn_vxlan_multi_tenant():
    objs: List[Dict[str, Any]] = []
    objs.append(shape("fabric", "rectangle", 960, 540, 1520, 540,
                      fill_color=COL_EVPN, fill_opacity=0.06,
                      stroke_color=COL_EVPN, stroke_width=2, corner_radius=16,
                      label="EVPN-VXLAN Fabric"))
    objs.append(shape("t1", "rectangle", 440, 860, 460, 280,
                      fill_color=COL_AS_BLUE, fill_opacity=0.08, corner_radius=14,
                      stroke_color=COL_AS_BLUE, stroke_width=2, label="Tenant A (VRF-A)"))
    objs.append(shape("t2", "rectangle", 1480, 860, 460, 280,
                      fill_color=COL_AS_ORANGE, fill_opacity=0.08, corner_radius=14,
                      stroke_color=COL_AS_ORANGE, stroke_width=2, label="Tenant B (VRF-B)"))

    objs.append(device("s1", "Spine-1", 720, 340, "spine", "classic", color=COL_DEV_SPINE))
    objs.append(device("s2", "Spine-2", 1200, 340, "spine", "classic", color=COL_DEV_SPINE))
    objs.append(device("l1", "Leaf-1", 440, 640, "leaf", "classic", color=COL_DEV_LEAF))
    objs.append(device("l2", "Leaf-2", 960, 640, "leaf", "classic", color=COL_DEV_LEAF))
    objs.append(device("l3", "Leaf-3", 1480, 640, "leaf", "classic", color=COL_DEV_LEAF))
    # Tenant A hosts
    objs.append(device("host_a1", "Host-A1", 300, 900, "host", "server", color=COL_DEV_CE))
    objs.append(device("host_a2", "Host-A2", 580, 900, "host", "server", color=COL_DEV_CE))
    # Tenant B hosts
    objs.append(device("host_b1", "Host-B1", 1340, 900, "host", "server", color=COL_DEV_CE))
    objs.append(device("host_b2", "Host-B2", 1620, 900, "host", "server", color=COL_DEV_CE))

    for lid in ["l1", "l2", "l3"]:
        for sid in ["s1", "s2"]:
            objs.append(link(f"l_{lid}_{sid}", lid, sid, "evpn", color=COL_EVPN,
                             style="dashed-wide", label="EVPN"))
    objs.append(link("l_ha1_l1", "host_a1", "l1", "default", color="#95a5a6", label="VLAN 10"))
    objs.append(link("l_ha2_l1", "host_a2", "l1", "default", color="#95a5a6", label="VLAN 10"))
    objs.append(link("l_hb1_l3", "host_b1", "l3", "default", color="#95a5a6", label="VLAN 20"))
    objs.append(link("l_hb2_l3", "host_b2", "l3", "default", color="#95a5a6", label="VLAN 20"))

    objs.append(text("t_title", "Multi-Tenant EVPN-VXLAN", 960, 140, font_size=20))
    objs.append(text("t_tenantA",
                     "Tenant A\nVNI 10010\nVRF-A (RD 65100:10, RT 65100:10)",
                     440, 1060, font_size=11, show_border=True, border_color=COL_AS_BLUE)) 
    objs.append(text("t_tenantB",
                     "Tenant B\nVNI 10020\nVRF-B (RD 65100:20, RT 65100:20)",
                     1480, 1060, font_size=11, show_border=True, border_color=COL_AS_ORANGE))
    return objs, {
        "protocol": "evpn-vxlan",
        "scale": "medium",
        "summary": "Multi-tenant EVPN-VXLAN. Two tenants isolated by VNI / VRF, sharing the same "
                   "leaf-spine fabric. Demonstrates RT-import/export per tenant.",
        "tags": ["evpn", "vxlan", "multi-tenant", "vrf", "vni"],
        "layout_hint": "clos-3-stage",
    }


# ===========================================================================
# Segment Routing
# ===========================================================================
def sr_mpls_ti_lfa():
    objs: List[Dict[str, Any]] = []
    objs.append(shape("sr", "rectangle", 960, 540, 1400, 520,
                      fill_color=COL_SR, fill_opacity=0.06,
                      stroke_color=COL_SR, stroke_width=2, corner_radius=16,
                      label="SR-MPLS Core"))
    coords = [("PE1", 360, 540), ("P1", 680, 340), ("P2", 960, 340),
              ("P3", 1240, 340), ("PE2", 1560, 540),
              ("P4", 680, 740), ("P5", 960, 740), ("P6", 1240, 740)]
    for name, x, y in coords:
        nid = name.lower()
        role = "pe" if name.startswith("PE") else "p"
        color = COL_DEV_PE if role == "pe" else COL_DEV_P
        sid = {"pe1":"16001","p1":"16002","p2":"16003","p3":"16004","pe2":"16005",
               "p4":"16006","p5":"16007","p6":"16008"}[nid]
        objs.append(device(nid, f"{name}\nSID {sid}", x, y, role, "classic", color=color))
    pairs = [("pe1","p1"), ("pe1","p4"), ("p1","p2"), ("p2","p3"),
             ("p3","pe2"), ("p4","p5"), ("p5","p6"), ("p6","pe2"),
             ("p1","p4"), ("p3","p6")]
    for a, b in pairs:
        objs.append(link(f"l_{a}_{b}", a, b, "sr-mpls", color=COL_SR, style="solid", label="SR"))
    # Protected path (primary) and TI-LFA backup highlighted
    objs.append(link("l_primary", "pe1", "p2", "sr-mpls", color=COL_SR, style="arrow",
                     width=4, label="Primary SR path"))
    objs.append(shape("fail", "cross", 820, 340, 60, 60, stroke_color="#e74c3c",
                      fill_color="#e74c3c", stroke_width=4, label="link failure"))
    objs.append(text("t_title", "SR-MPLS with TI-LFA Fast-Reroute", 960, 140, font_size=20))
    objs.append(text("t_ti",
                     "TI-LFA: Topology-Independent LFA\nPre-computes a post-convergence backup path\nusing node + adjacency SIDs\nSub-50 ms protection",
                     960, 940, font_size=11, show_border=True, border_color=COL_SR))
    return objs, {
        "protocol": "sr",
        "scale": "medium",
        "summary": "SR-MPLS core with TI-LFA fast-reroute. Node-SIDs advertised via IS-IS SR; "
                   "every router pre-computes a backup path for sub-50 ms convergence on link "
                   "failure.",
        "tags": ["sr", "sr-mpls", "ti-lfa", "fast-reroute", "node-sid"],
    }


def sr_te_policy():
    objs: List[Dict[str, Any]] = []
    objs.append(shape("sr", "rectangle", 960, 540, 1400, 520,
                      fill_color=COL_SR, fill_opacity=0.06,
                      stroke_color=COL_SR, stroke_width=2, corner_radius=16,
                      label="SR-TE (Traffic Engineering)"))
    coords = [("Ingress", 340, 540), ("P1", 680, 340), ("P2", 960, 340),
              ("P3", 1240, 340), ("Egress", 1580, 540),
              ("P4", 680, 740), ("P5", 960, 740), ("P6", 1240, 740)]
    for name, x, y in coords:
        nid = name.lower()
        role = "pe" if name.startswith(("Ingress","Egress")) else "p"
        color = COL_DEV_PE if role == "pe" else COL_DEV_P
        objs.append(device(nid, name, x, y, role, "classic", color=color))
    # IGP links
    for a, b in [("ingress","p1"), ("ingress","p4"), ("p1","p2"), ("p2","p3"),
                 ("p3","egress"), ("p4","p5"), ("p5","p6"), ("p6","egress"),
                 ("p1","p4"), ("p3","p6")]:
        objs.append(link(f"l_{a}_{b}", a, b, "isis", color=COL_ISIS, style="solid", label="IS-IS SR"))
    # SR-TE policy (red arrow) takes the "southern" (P4-P5-P6) path
    te_pairs = [("ingress","p4"), ("p4","p5"), ("p5","p6"), ("p6","egress")]
    for i, (a, b) in enumerate(te_pairs):
        objs.append(link(f"te_{i}", a, b, "sr-mpls", color=COL_SR, style="arrow",
                         width=5, label="SR-TE policy"))

    objs.append(text("t_title", "SR-TE Policy (steering via color/binding-SID)", 960, 140, font_size=20))
    objs.append(text("t_policy",
                     "Policy: LOW-LATENCY\nColor 200, Endpoint Egress\nSID-list: < 16006, 16007, 16008 >",
                     960, 920, font_size=11, show_border=True, border_color=COL_SR))
    return objs, {
        "protocol": "sr",
        "scale": "medium",
        "summary": "SR-TE policy-based traffic steering. A low-latency policy pushes an explicit "
                   "SID-list that routes traffic along the southern path, overriding the IGP "
                   "best-metric decision.",
        "tags": ["sr", "sr-te", "traffic-engineering", "binding-sid", "policy"],
    }


# ===========================================================================
# Clos + Campus + Ring + DCI + DriveNets
# ===========================================================================
def clos_3stage_2x4():
    objs: List[Dict[str, Any]] = []
    objs.append(shape("fab", "rectangle", 960, 540, 1500, 540,
                      fill_color="#3498db", fill_opacity=0.06,
                      stroke_color="#3498db", stroke_width=2, corner_radius=16,
                      label="Clos 3-stage (2 spines / 4 leaves)"))
    objs.append(device("s1", "Spine-1", 700, 320, "spine", "classic", color=COL_DEV_SPINE))
    objs.append(device("s2", "Spine-2", 1220, 320, "spine", "classic", color=COL_DEV_SPINE))
    for i, x in enumerate([460, 800, 1140, 1480], start=1):
        lid = f"l{i}"
        objs.append(device(lid, f"Leaf-{i}", x, 720, "leaf", "classic", color=COL_DEV_LEAF))
    for lid in ["l1", "l2", "l3", "l4"]:
        for sid in ["s1", "s2"]:
            objs.append(link(f"u_{lid}_{sid}", lid, sid, "ebgp", color=COL_EBGP, style="arrow",
                             label="eBGP"))
    objs.append(text("t_title", "Clos 3-stage Fabric (2 spine / 4 leaf)", 960, 140, font_size=20))
    objs.append(text("t_fabric",
                     "Non-blocking 2:1 oversubscription\nEvery leaf has 2 uplinks (one per spine)\nFull-bandwidth server-to-server",
                     960, 900, font_size=12, show_border=True))
    return objs, {
        "protocol": "clos",
        "scale": "medium",
        "summary": "Clos 3-stage DC fabric with 2 spines and 4 leaves. Canonical non-blocking "
                   "spine-leaf design used by every modern hyperscale DC.",
        "tags": ["clos", "3-stage", "spine-leaf", "dc-fabric"],
        "layout_hint": "clos-3-stage",
    }


def clos_5stage_super_spine():
    objs: List[Dict[str, Any]] = []
    objs.append(shape("fab", "rectangle", 960, 600, 1680, 820,
                      fill_color="#3498db", fill_opacity=0.05,
                      stroke_color="#3498db", stroke_width=2, corner_radius=16,
                      label="Clos 5-stage (Super-Spine / Spine / Leaf)"))
    # Super-spines row (y=260)
    for i, x in enumerate([680, 1000, 1320], start=1):
        objs.append(device(f"ss{i}", f"SS-{i}", x, 260, "super-spine", "classic", color="#2c3e50"))
    # Spines row (y=540)
    for i, x in enumerate([480, 780, 1080, 1380, 1680], start=1):
        objs.append(device(f"sp{i}", f"Spine-{i}", x, 540, "spine", "classic", color=COL_DEV_SPINE))
    # Leaves row (y=860)
    leaf_xs = [340, 540, 740, 940, 1140, 1340, 1540, 1740]
    for i, x in enumerate(leaf_xs, start=1):
        objs.append(device(f"lf{i}", f"Leaf-{i}", x, 860, "leaf", "classic", color=COL_DEV_LEAF))
    # SS-Spine links
    for ss in ["ss1", "ss2", "ss3"]:
        for sp in ["sp1", "sp2", "sp3", "sp4", "sp5"]:
            objs.append(link(f"l_{ss}_{sp}", ss, sp, "ebgp", color=COL_EBGP, style="arrow"))
    # Spine-Leaf links (every leaf -> 2 spines, simplified)
    for i, lid in enumerate([f"lf{j}" for j in range(1, 9)]):
        sp_a = f"sp{(i % 5) + 1}"
        sp_b = f"sp{((i + 2) % 5) + 1}"
        objs.append(link(f"u_{lid}_{sp_a}", lid, sp_a, "ebgp", color=COL_EBGP, style="arrow"))
        objs.append(link(f"u_{lid}_{sp_b}", lid, sp_b, "ebgp", color=COL_EBGP, style="arrow"))

    objs.append(text("t_title", "Clos 5-stage (Super-Spine / Spine / Leaf)", 960, 120, font_size=20))
    objs.append(text("t_scale",
                     "Super-spines aggregate PODs for east-west traffic\n5-stage = 3 super-spine layers of folded Clos",
                     960, 1020, font_size=12, show_border=True))
    return objs, {
        "protocol": "clos",
        "scale": "large",
        "summary": "Clos 5-stage hyperscale DC fabric. Three super-spines aggregate five spines "
                   "over eight leaves -- the scaling step beyond the 3-stage baseline.",
        "tags": ["clos", "5-stage", "super-spine", "hyperscale"],
        "layout_hint": "clos-5-stage",
    }


def campus_3tier_mlag():
    objs: List[Dict[str, Any]] = []
    objs.append(shape("fab", "rectangle", 960, 600, 1500, 820,
                      fill_color="#2ecc71", fill_opacity=0.05,
                      stroke_color="#2ecc71", stroke_width=2, corner_radius=16,
                      label="Enterprise Campus (Core / Dist / Access)"))
    # Core
    objs.append(device("core1", "Core-1", 780, 260, "core", "classic", color=COL_DEV_CORE))
    objs.append(device("core2", "Core-2", 1140, 260, "core", "classic", color=COL_DEV_CORE))
    # Dist (MLAG pair)
    objs.append(device("dist1", "Dist-1", 780, 540, "dist", "classic", color=COL_DEV_DIST))
    objs.append(device("dist2", "Dist-2", 1140, 540, "dist", "classic", color=COL_DEV_DIST))
    # Access
    for i, x in enumerate([480, 780, 1140, 1440], start=1):
        aid = f"acc{i}"
        objs.append(device(aid, f"Access-{i}", x, 820, "access", "classic", color=COL_DEV_ACCESS))

    # Core mesh
    objs.append(link("l_c1_c2", "core1", "core2", "ospf", color=COL_OSPF, style="solid", label="OSPF a0"))
    # Core-Dist
    for c in ["core1", "core2"]:
        for d in ["dist1", "dist2"]:
            objs.append(link(f"l_{c}_{d}", c, d, "ospf", color=COL_OSPF, style="solid", label="OSPF"))
    # Dist MLAG peer-link
    objs.append(link("l_mlag", "dist1", "dist2", "default", color="#f39c12", style="solid",
                     width=3, label="MLAG peer"))
    # Access-Dist MLAG uplinks
    for a in ["acc1", "acc2", "acc3", "acc4"]:
        objs.append(link(f"l_{a}_d1", a, "dist1", "default", color="#95a5a6", style="solid",
                         label="LAG"))
        objs.append(link(f"l_{a}_d2", a, "dist2", "default", color="#95a5a6", style="solid",
                         label="LAG"))

    objs.append(text("t_title", "Campus 3-Tier with MLAG", 960, 120, font_size=20))
    objs.append(text("t_mlag",
                     "MLAG peer-link (orange, thick)\nAccess switches run a LAG toward\nboth distribution switches simultaneously",
                     960, 980, font_size=12, show_border=True))
    return objs, {
        "protocol": "campus",
        "scale": "medium",
        "summary": "Enterprise 3-tier campus (Core / Distribution / Access) with MLAG. "
                   "OSPF between core and distribution; access uplinks as LAGs terminating on "
                   "the MLAG peer-group.",
        "tags": ["campus", "3-tier", "mlag", "ospf", "access"],
        "layout_hint": "campus",
    }


def ring_metro_g8032_6node():
    objs: List[Dict[str, Any]] = []
    objs.append(shape("ring", "ellipse", 960, 540, 700, 700,
                      fill_color="#f39c12", fill_opacity=0.06,
                      stroke_color="#f39c12", stroke_width=2,
                      label="G.8032 Metro Ring"))
    nodes = []
    for i in range(6):
        angle = math.radians(-90 + i * 60)
        x = 960 + 320 * math.cos(angle)
        y = 540 + 320 * math.sin(angle)
        nid = f"rn{i+1}"
        objs.append(device(nid, f"RN-{i+1}", x, y, "access", "classic", color=COL_DEV_ACCESS))
        nodes.append(nid)
    for i in range(6):
        a = nodes[i]
        b = nodes[(i + 1) % 6]
        style = "dashed" if (i == 0) else "solid"
        label = "RPL (blocked)" if i == 0 else "Ring"
        color = "#e74c3c" if i == 0 else "#f39c12"
        objs.append(link(f"l_{a}_{b}", a, b, "default", color=color, style=style, width=3, label=label))

    objs.append(text("t_title", "Metro Ethernet Ring (G.8032 / ERPS)", 960, 120, font_size=20))
    objs.append(text("t_rpl",
                     "RPL = Ring Protection Link (blocked during\nnormal operation). On failure the RPL is\nunblocked and traffic re-routes; < 50 ms.",
                     960, 980, font_size=12, show_border=True, border_color="#e74c3c"))
    return objs, {
        "protocol": "ring",
        "scale": "small",
        "summary": "G.8032 metro Ethernet ring with 6 access nodes. One link is the Ring "
                   "Protection Link (normally blocked). Sub-50 ms protection on failure.",
        "tags": ["ring", "g8032", "erps", "rpl", "metro"],
        "layout_hint": "ring",
    }


def ring_erps_ring():
    objs: List[Dict[str, Any]] = []
    objs.append(shape("ring", "ellipse", 960, 540, 900, 640,
                      fill_color="#1abc9c", fill_opacity=0.06,
                      stroke_color="#1abc9c", stroke_width=2, label="ERPS Ring (open)"))
    for i in range(8):
        angle = math.radians(-90 + i * 45)
        x = 960 + 380 * math.cos(angle)
        y = 540 + 280 * math.sin(angle)
        nid = f"en{i+1}"
        role = "pe" if i in (0, 4) else "access"
        color = COL_DEV_PE if role == "pe" else COL_DEV_ACCESS
        objs.append(device(nid, f"EN-{i+1}", x, y, role, "classic", color=color))
    for i in range(8):
        a = f"en{i+1}"
        b = f"en{((i + 1) % 8) + 1}"
        if i == 3:
            objs.append(link(f"l_rpl", a, b, "default", color="#e74c3c", style="dashed",
                             width=3, label="RPL (blocked)"))
        else:
            objs.append(link(f"l_{a}_{b}", a, b, "default", color="#16a085", style="solid",
                             width=3, label="Ring"))

    objs.append(text("t_title", "ERPS Ring (8 nodes, 2 gateways)", 960, 120, font_size=20))
    objs.append(text("t_erps",
                     "ITU-T G.8032v2 / MEF-specified\nEN-1 and EN-5 are edge gateways to the core\nRPL blocks normal traffic; R-APS messages\nprotect on failure.",
                     960, 1020, font_size=12, show_border=True, border_color="#16a085"))
    return objs, {
        "protocol": "ring",
        "scale": "medium",
        "summary": "8-node ERPS (Ethernet Ring Protection Switching) ring with two core-facing "
                   "gateways. Single RPL blocked during normal operation per G.8032v2.",
        "tags": ["ring", "erps", "g8032", "metro", "8-node"],
        "layout_hint": "ring",
    }


def dci_l2_extension_evpn_wan():
    objs: List[Dict[str, Any]] = []
    objs.append(shape("dc1", "rectangle", 440, 540, 640, 560,
                      fill_color=COL_AS_BLUE, fill_opacity=0.08,
                      stroke_color=COL_AS_BLUE, stroke_width=2, corner_radius=16,
                      label="Data Center 1"))
    objs.append(shape("dc2", "rectangle", 1480, 540, 640, 560,
                      fill_color=COL_AS_ORANGE, fill_opacity=0.08,
                      stroke_color=COL_AS_ORANGE, stroke_width=2, corner_radius=16,
                      label="Data Center 2"))
    objs.append(shape("wan", "cloud", 960, 540, 340, 240,
                      fill_color="#bdc3c7", fill_opacity=0.25,
                      stroke_color="#7f8c8d", stroke_width=2, label="WAN"))

    objs.append(device("dc1_spine", "DC1-Spine", 440, 360, "spine", "classic", color=COL_DEV_SPINE))
    objs.append(device("dc1_leaf", "DC1-Leaf", 280, 720, "leaf", "classic", color=COL_DEV_LEAF))
    objs.append(device("dc1_dci", "DC1-DCI-GW", 600, 720, "pe", "hex", color=COL_DEV_PE))
    objs.append(device("dc2_spine", "DC2-Spine", 1480, 360, "spine", "classic", color=COL_DEV_SPINE))
    objs.append(device("dc2_leaf", "DC2-Leaf", 1640, 720, "leaf", "classic", color=COL_DEV_LEAF))
    objs.append(device("dc2_dci", "DC2-DCI-GW", 1320, 720, "pe", "hex", color=COL_DEV_PE))

    # Intra-DC
    objs.append(link("l_dc1", "dc1_leaf", "dc1_spine", "evpn", color=COL_EVPN, style="dashed-wide", label="EVPN"))
    objs.append(link("l_dc1d", "dc1_dci", "dc1_spine", "evpn", color=COL_EVPN, style="dashed-wide", label="EVPN"))
    objs.append(link("l_dc2", "dc2_leaf", "dc2_spine", "evpn", color=COL_EVPN, style="dashed-wide", label="EVPN"))
    objs.append(link("l_dc2d", "dc2_dci", "dc2_spine", "evpn", color=COL_EVPN, style="dashed-wide", label="EVPN"))
    # DCI across WAN
    objs.append(link("l_dci", "dc1_dci", "dc2_dci", "evpn", color=COL_EVPN, style="dashed-wide",
                     width=4, label="DCI EVPN-VXLAN-over-WAN"))

    objs.append(text("t_title", "DCI: L2-extension with EVPN-VXLAN over WAN", 960, 140, font_size=20))
    objs.append(text("t_note",
                     "DCI gateways stitch EVPN instances across sites\nTenant VNIs preserved end-to-end\nTypically rides MPLS or SRv6 WAN transport",
                     960, 920, font_size=12, show_border=True, border_color=COL_EVPN))
    return objs, {
        "protocol": "dci",
        "scale": "medium",
        "summary": "Data-Center Interconnect with L2 extension via EVPN-VXLAN over a shared WAN. "
                   "Each DC runs its own fabric and stitches tenant VNIs end-to-end at the DCI "
                   "gateways.",
        "tags": ["dci", "evpn", "vxlan", "wan", "l2-extension"],
    }


def drivenets_ncp_ncf_cluster():
    objs: List[Dict[str, Any]] = []
    objs.append(shape("cluster", "rectangle", 960, 540, 1500, 640,
                      fill_color="#00b4d8", fill_opacity=0.06,
                      stroke_color=COL_DNAAS, stroke_width=2, corner_radius=18,
                      label="DriveNets Network Cloud Cluster"))
    # 2x NCF (fabric) spine
    objs.append(device("ncf1", "NCF-1", 720, 320, "spine", "classic", color=COL_DEV_NCF))
    objs.append(device("ncf2", "NCF-2", 1200, 320, "spine", "classic", color=COL_DEV_NCF))
    # 4x NCP (packet) leaf
    for i, x in enumerate([460, 760, 1160, 1460], start=1):
        nid = f"ncp{i}"
        objs.append(device(nid, f"NCP-{i}", x, 720, "leaf", "classic", color=COL_DEV_NCP))
    # NCM
    objs.append(device("ncm", "NCM", 960, 960, "core", "hex", color="#00b4d8", radius=48))

    for nid in ["ncp1", "ncp2", "ncp3", "ncp4"]:
        for f in ["ncf1", "ncf2"]:
            objs.append(link(f"l_{nid}_{f}", nid, f, "dnaas", color=COL_DNAAS, style="solid",
                             label="Cluster fabric"))
    for nid in ["ncp1", "ncp2", "ncp3", "ncp4", "ncf1", "ncf2"]:
        objs.append(link(f"mgmt_{nid}", "ncm", nid, "default", color="#95a5a6",
                         style="dashed", label="mgmt"))

    objs.append(text("t_title", "DriveNets Network Cloud (NCP/NCF) Cluster", 960, 140, font_size=20))
    objs.append(text("t_roles",
                     "NCP = Network Cloud Packet (forwarding)\nNCF = Network Cloud Fabric (Clos spine)\nNCM = Network Cloud Manager (control)",
                     960, 1100, font_size=12, show_border=True, border_color=COL_DNAAS))
    return objs, {
        "protocol": "drivenets",
        "scale": "medium",
        "summary": "DriveNets Network Cloud disaggregated cluster: 4 NCP packet boxes, 2 NCF "
                   "fabric chassis, and NCM control plane. Canonical scale-out DNOS chassis "
                   "replacement.",
        "tags": ["drivenets", "ncp", "ncf", "ncm", "cluster", "dnos"],
        "layout_hint": "clos-3-stage",
    }


def drivenets_dnaas_fabric():
    objs: List[Dict[str, Any]] = []
    objs.append(shape("dnaas", "rectangle", 960, 600, 1700, 720,
                      fill_color="#00b4d8", fill_opacity=0.06,
                      stroke_color=COL_DNAAS, stroke_width=2, corner_radius=18,
                      label="DNAAS Service Fabric"))
    # 2 PE (customer facing) + 2 Spine + 2 Leaf + 2 CE (customer sites)
    objs.append(device("ce1", "Customer-A", 220, 400, "ce", "simple", color=COL_DEV_CE))
    objs.append(device("ce2", "Customer-B", 220, 880, "ce", "simple", color=COL_DEV_CE))
    objs.append(device("pe1", "PE-1", 480, 400, "pe", "classic", color=COL_DEV_PE))
    objs.append(device("pe2", "PE-2", 480, 880, "pe", "classic", color=COL_DEV_PE))
    objs.append(device("leaf1", "LEAF-1", 820, 400, "leaf", "classic", color=COL_DEV_LEAF))
    objs.append(device("leaf2", "LEAF-2", 820, 880, "leaf", "classic", color=COL_DEV_LEAF))
    objs.append(device("spine1", "SPINE-1", 1200, 400, "spine", "classic", color=COL_DEV_SPINE))
    objs.append(device("spine2", "SPINE-2", 1200, 880, "spine", "classic", color=COL_DEV_SPINE))
    objs.append(device("fabric1", "FABRIC-1", 1560, 400, "spine", "classic", color=COL_DEV_NCF))
    objs.append(device("fabric2", "FABRIC-2", 1560, 880, "spine", "classic", color=COL_DEV_NCF))

    # CE-PE
    objs.append(link("l_ce1_pe1", "ce1", "pe1", "ebgp", color=COL_EBGP, style="arrow", label="CE-PE"))
    objs.append(link("l_ce2_pe2", "ce2", "pe2", "ebgp", color=COL_EBGP, style="arrow", label="CE-PE"))
    # PE-Leaf
    objs.append(link("l_pe1_l1", "pe1", "leaf1", "dnaas", color=COL_DNAAS, style="solid", label="DNAAS"))
    objs.append(link("l_pe2_l2", "pe2", "leaf2", "dnaas", color=COL_DNAAS, style="solid", label="DNAAS"))
    # Leaf-Spine
    for a in ["leaf1", "leaf2"]:
        for b in ["spine1", "spine2"]:
            objs.append(link(f"l_{a}_{b}", a, b, "dnaas", color=COL_DNAAS, style="solid", label="fabric"))
    # Spine-Fabric
    for a in ["spine1", "spine2"]:
        for b in ["fabric1", "fabric2"]:
            objs.append(link(f"l_{a}_{b}", a, b, "dnaas", color=COL_DNAAS, style="solid", label="fabric"))

    objs.append(text("t_title", "DNAAS Service Fabric (DriveNets)", 960, 140, font_size=20))
    objs.append(text("t_roles",
                     "PE = customer-facing (VPN termination)\nLEAF / SPINE / FABRIC = cluster fabric\nDNAAS = Disaggregated Network-as-a-Service",
                     960, 1060, font_size=12, show_border=True, border_color=COL_DNAAS))
    return objs, {
        "protocol": "drivenets",
        "scale": "large",
        "summary": "DriveNets DNAAS service fabric. Customer PEs front-end a leaf/spine/fabric "
                   "disaggregated cluster for VPN + VPWS service delivery at scale.",
        "tags": ["drivenets", "dnaas", "service-fabric", "pe-ce", "leaf-spine"],
    }


# ===========================================================================
# Dispatch table.
# ===========================================================================
GENERATORS = {
    # BGP
    "bgp/ibgp-full-mesh-4.json":          bgp_ibgp_full_mesh_4,
    "bgp/ibgp-rr-hub-spoke-6.json":       bgp_ibgp_rr_hub_spoke_6,
    "bgp/ebgp-2as-transit.json":          bgp_ebgp_2as_transit,
    "bgp/ixp-route-server.json":          bgp_ixp_route_server,
    "bgp/bgp-confederation.json":         bgp_confederation,
    # OSPF
    "ospf/single-area-5.json":            ospf_single_area_5,
    "ospf/multi-area-0-1-2.json":         ospf_multi_area_0_1_2,
    "ospf/totally-stubby.json":           ospf_totally_stubby,
    "ospf/abr-dr-hierarchy.json":         ospf_abr_dr_hierarchy,
    # IS-IS
    "isis/l1-l2-hierarchy.json":          isis_l1_l2_hierarchy,
    "isis/pure-l2-backbone.json":         isis_pure_l2_backbone,
    # MPLS L3VPN
    "mpls-l3vpn/2pe-1ce-basic.json":      mpls_l3vpn_2pe_1ce_basic,
    "mpls-l3vpn/4pe-rr-hub.json":         mpls_l3vpn_4pe_rr_hub,
    "mpls-l3vpn/multi-site-vpn.json":     mpls_l3vpn_multi_site,
    # EVPN-VXLAN
    "evpn-vxlan/2spine-4leaf-anycast-gw.json": evpn_vxlan_2spine_4leaf_anycast_gw,
    "evpn-vxlan/edge-routed-bridging.json":    evpn_vxlan_edge_routed_bridging,
    "evpn-vxlan/multi-tenant.json":            evpn_vxlan_multi_tenant,
    # Segment Routing
    "sr/sr-mpls-ti-lfa.json":             sr_mpls_ti_lfa,
    "sr/sr-te-policy.json":               sr_te_policy,
    # Clos
    "clos/3stage-2x4.json":               clos_3stage_2x4,
    "clos/5stage-super-spine.json":       clos_5stage_super_spine,
    # Campus
    "campus/3tier-mlag.json":             campus_3tier_mlag,
    # Ring
    "ring/metro-g8032-6node.json":        ring_metro_g8032_6node,
    "ring/erps-ring.json":                ring_erps_ring,
    # DCI
    "dci/l2-extension-evpn-wan.json":     dci_l2_extension_evpn_wan,
    # DriveNets
    "drivenets/ncp-ncf-cluster.json":     drivenets_ncp_ncf_cluster,
    "drivenets/dnaas-fabric.json":        drivenets_dnaas_fabric,
}


def main():
    count = 0
    for rel, fn in GENERATORS.items():
        out_path = HERE / rel
        objs, meta = fn()
        write_blueprint(out_path, meta, objs)
        print(f"  wrote {rel}  ({len(objs)} objects)")
        count += 1
    print(f"Generated {count} blueprints under {HERE}")


if __name__ == "__main__":
    main()
