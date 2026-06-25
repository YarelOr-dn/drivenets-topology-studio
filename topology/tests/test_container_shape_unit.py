"""Unit tests for the container-shape contract (2026-04-26).

Coverage:

  1. ``TOPOLOGY_TOOL_SCHEMA`` exposes ``containerMode`` (boolean) on the
     per-object property bag, so the LLM tool-use protocol can emit
     it without a schema-validation rejection.
  2. ``CANVAS_EDITS_TOOL_SCHEMA`` exposes ``containerMode`` as well,
     so existing-canvas edits (``add_shape`` / ``style``) can promote
     a shape into a container without tool-call rejections.
  3. Description text on the ``create_topology`` tool mentions the
     container contract (``containerMode``) and the dummy-IP /
     interface / link-detail contract. These are the hooks the LLM
     reads on every turn -- if they vanish, generated topologies go
     back to grey-link / no-IP output.
  4. ``normalize_topology_payload`` preserves the ``containerMode``
     flag and the link ``linkDetails`` dummy-data blob on objects
     without dropping them as "unknown" fields.
  5. The Detail Contract block from ``knowledge.md`` is present in the
     bundled digest so the system prompt actually carries it.

Run:
    PYTHONPATH="topology" python3 topology/tests/test_container_shape_unit.py
"""

from __future__ import annotations

import os
import sys


def _case(label: str) -> None:
    print(f"\n=== {label}")


def _assert(cond: object, label: str, *, info: str = "") -> None:
    if cond:
        print(f"  ok: {label}")
        return
    print(f"  FAIL: {label}")
    if info:
        print(f"    info: {info}")
    raise SystemExit(1)


def _topology_props():
    from ai.context import TOPOLOGY_TOOL_SCHEMA
    return TOPOLOGY_TOOL_SCHEMA["parameters"]["properties"]["objects"]["items"]["properties"]


def _canvas_edit_props():
    from ai.context import CANVAS_EDITS_TOOL_SCHEMA
    edits = CANVAS_EDITS_TOOL_SCHEMA["parameters"]["properties"]["edits"]
    return edits["items"]["properties"]


def main() -> None:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
    from ai.context import (
        TOPOLOGY_TOOL_SCHEMA,
        CANVAS_EDITS_TOOL_SCHEMA,
        normalize_topology_payload,
    )

    # --------------------------------------------------------------
    # 1. create_topology schema exposes containerMode.
    # --------------------------------------------------------------
    _case("create_topology schema exposes containerMode")
    props = _topology_props()
    _assert("containerMode" in props,
            "create_topology object props include containerMode")
    _assert(props["containerMode"].get("type") == "boolean",
            "containerMode is a boolean")
    desc = (props["containerMode"].get("description") or "").lower()
    _assert("container" in desc and "drag" in desc,
            "containerMode description mentions container + drag",
            info=desc[:120])
    _assert("interface1" in props and "linkDetails" in props,
            "create_topology link props include interface1 + linkDetails")

    # --------------------------------------------------------------
    # 2. apply_canvas_edits schema exposes containerMode.
    # --------------------------------------------------------------
    _case("apply_canvas_edits schema exposes containerMode")
    eprops = _canvas_edit_props()
    _assert("containerMode" in eprops,
            "edit props include containerMode")
    _assert(eprops["containerMode"].get("type") == "boolean",
            "edit containerMode is a boolean")

    # --------------------------------------------------------------
    # 3. Tool description carries the detail + container contract.
    # --------------------------------------------------------------
    _case("create_topology description carries detail + container contract")
    tdesc = TOPOLOGY_TOOL_SCHEMA.get("description") or ""
    must_have = [
        "DETAIL CONTRACT",
        "loopback",
        "linkDetails",
        "GROUPING CONTRACT",
        "containerMode",
        "centre falls inside",
    ]
    for tok in must_have:
        _assert(tok in tdesc,
                f"description mentions {tok!r}",
                info=f"first 240 chars: {tdesc[:240]}")

    # --------------------------------------------------------------
    # 4. normalize_topology_payload preserves containerMode + linkDetails.
    # --------------------------------------------------------------
    _case("normalize_topology_payload preserves dummy-data + containerMode")
    raw = {
        "name": "ai-detail-test",
        "objects": [
            {
                "id": "pe1", "type": "device", "x": 200, "y": 200,
                "label": "PE1", "ip": "10.0.0.1", "role": "pe",
                "visualStyle": "classic",
            },
            {
                "id": "pe2", "type": "device", "x": 800, "y": 200,
                "label": "PE2", "ip": "10.0.0.2", "role": "pe",
                "visualStyle": "classic",
            },
            {
                "id": "ln1", "type": "link",
                "device1": "pe1", "device2": "pe2",
                "linkType": "ibgp",
                "interface1": "ge100-0/0/1",
                "interface2": "ge100-0/0/1",
                "linkDetails": {
                    "ip1": "10.10.0.0/31",
                    "ip2": "10.10.0.1/31",
                    "as1": 65000,
                    "as2": 65000,
                },
            },
            {
                "id": "as-box", "type": "shape", "x": 500, "y": 200,
                "width": 800, "height": 300, "shapeType": "rectangle",
                "fillOpacity": 0.08, "cornerRadius": 14,
                "label": "AS 65000",
                "containerMode": True,
            },
        ],
    }
    out = normalize_topology_payload(raw)
    objs = out["objects"]
    shape = next(o for o in objs if o.get("type") == "shape")
    link = next(o for o in objs if o.get("type") == "link")
    pe1 = next(o for o in objs if o.get("id") == "pe1")
    _assert(shape.get("containerMode") is True,
            "shape.containerMode preserved through normalize")
    _assert(link.get("interface1") == "ge100-0/0/1",
            "link.interface1 preserved")
    _assert(isinstance(link.get("linkDetails"), dict),
            "link.linkDetails preserved as dict")
    _assert(link["linkDetails"].get("ip1") == "10.10.0.0/31",
            "linkDetails.ip1 preserved")
    _assert(pe1.get("ip") == "10.0.0.1",
            "device.ip dummy loopback preserved")

    # --------------------------------------------------------------
    # 5. knowledge digest carries the Detail Contract block.
    # --------------------------------------------------------------
    _case("knowledge.md carries the Detail Contract + container block")
    from ai.service import load_knowledge_digest
    text = load_knowledge_digest()
    for tok in [
        "Detail contract for AI-generated topologies",
        "loopback",
        "containerMode: true",
        "Container shapes",
    ]:
        _assert(tok in text,
                f"knowledge digest mentions {tok!r}",
                info="first 240 chars: " + text[:240])

    print("\nAll container-shape unit tests passed.")


if __name__ == "__main__":
    main()
