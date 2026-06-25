#!/usr/bin/env python3
"""Static guards for Topologies dropdown domain expansion.

Pins the 2026-05-05 regression where switching topologies could leave an
expanded domain body blank because the row depended on a previous async preload.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)
    print(f"ok: {msg}")


def test_domain_expand_paths_ensure_topology_children_render() -> None:
    src = _read("topology-file-ops.js")
    _assert(
        "_ensureDomainTopologiesRendered(editor, section, container)" in src,
        "central helper exists for expand-time child rendering",
    )
    _assert(
        src.count("FileOps._ensureDomainTopologiesRendered(editor, sec, toposListEl);") >= 3,
        "mouse, built-in, and keyboard expand paths all ensure child rendering",
    )
    _assert(
        "domainToposLoadingFor" in src and "domainToposLoadedFor" in src,
        "inline topology loader tracks loading and loaded state per domain",
    )
    _assert(
        "Loading topologies..." in src
        and "No topologies yet" in src
        and "Failed to load" in src,
        "own-domain child list has loading, empty, and error states",
    )


def test_topology_offset_navigation_handles_cached_entry_objects() -> None:
    src = _read("topology-file-ops.js")
    start = src.find("navigateTopoByOffset(offset)")
    assert start != -1, "navigateTopoByOffset exists"
    end = src.find("// ========================================================================", start)
    block = src[start:end]
    _assert(
        "entry.name || entry.filename" in block,
        "Alt+Left/Right derives names from cached topology entry objects",
    )
    _assert(
        "f.replace(/\\.json$/i, '')" not in block,
        "Alt+Left/Right no longer treats cached entries as bare strings",
    )


def test_domain_dropdown_cache_buster_bumped() -> None:
    """The topology-file-ops.js cache-buster MUST be newer than the original
    domain-expansion-fix value (?v=20260506a-state-isolation). It floats
    forward as later workers ship bug fixes / wizards on the same file --
    today (2026-05-12) the new-topology wizard moves it to
    20260512e-new-topo-flow. We accept any post-2026-05-06 string of the
    form YYYYMMDD<letter>-<slug> so the test does not flap every time a
    future worker bumps it again."""
    import re
    html = _read("index.html")
    match = re.search(
        r'topology-file-ops\.js\?v=(\d{8})([a-z])-([a-z0-9-]+)',
        html,
    )
    _assert(match is not None, "index.html exposes a versioned topology-file-ops.js script tag")
    if not match:
        return
    date_str = match.group(1)
    _assert(
        date_str >= "20260506",
        "index.html cache-buster is not older than the domain-expansion-fix baseline",
    )


if __name__ == "__main__":
    test_domain_expand_paths_ensure_topology_children_render()
    test_topology_offset_navigation_handles_cached_entry_objects()
    test_domain_dropdown_cache_buster_bumped()
    print("All domain dropdown render checks passed.")
