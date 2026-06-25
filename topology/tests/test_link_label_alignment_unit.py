#!/usr/bin/env python3
"""Static guards for attached link interface-label alignment."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)
    print(f"ok: {msg}")


def test_interface_labels_follow_rendered_link_path() -> None:
    src = _read("topology.js")
    drawing_src = _read("topology-link-drawing.js")
    _assert("visualPathAlreadyOffset" in src, "attached label positioning tracks whether path already includes visual offset")
    _assert("link._renderedEndpoints" in src, "attached labels prefer drawLink rendered endpoints")
    _assert("anchorsMatchCurrentDevices" in src, "rendered endpoint reuse is gated by fresh device anchors")
    _assert("_renderedEndpointAnchors" in drawing_src, "drawLink records anchor positions for rendered endpoint freshness")
    _assert("this.getLinkConnectionPoint(device1, startDirAngle)" in src, "first-frame fallback uses shape-aware start point")
    _assert("this.getLinkConnectionPoint(device2, endDirAngle)" in src, "first-frame fallback uses shape-aware end point")
    _assert("if (!visualPathAlreadyOffset && linkIndex > 0)" in src, "parallel offset is not applied twice")


if __name__ == "__main__":
    test_interface_labels_follow_rendered_link_path()
    print("All link label alignment checks passed.")
