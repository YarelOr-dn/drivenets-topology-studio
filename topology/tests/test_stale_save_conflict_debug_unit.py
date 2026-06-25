"""Regression checks for stale-save 409 diagnostics and owner-only skips.

Run with::

    PYTHONPATH="topology" python3 topology/tests/test_stale_save_conflict_debug_unit.py
"""
from __future__ import annotations

import os
import re
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOPO = os.path.join(REPO_ROOT, "topology")
sys.path.insert(0, TOPO)


def _read(rel: str) -> str:
    with open(os.path.join(TOPO, rel), "r", encoding="utf-8") as f:
        return f.read()


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


def test_user_store_meta_exposes_last_writer_and_share_counts() -> None:
    _case("user_store.get_topology_meta exposes last writer and share counts")
    src = _read("api/auth/user_store.py")

    _assert(
        "last_actor" in src and "last_actor_display_name" in src,
        "topology meta includes last-writer fields",
    )
    _assert(
        "FROM topology_events" in src
        and "event_type IN ('topology.saved', 'topology.created')" in src,
        "last-writer data comes from the topology event log",
    )
    for field in (
        "topology_share_count",
        "topology_write_share_count",
        "domain_share_count",
        "domain_write_share_count",
        "share_recipient_count",
        "write_share_recipient_count",
    ):
        _assert(field in src, f"meta includes {field}")
    _assert(
        "FROM topology_shares WHERE composite_id = ?" in src,
        "per-file share counts are queried from topology_shares",
    )
    _assert(
        "FROM domain_shares WHERE domain_id = ?" in src,
        "domain-share counts are queried too (domain shares can write topologies)",
    )


def test_serve_conflict_response_has_debug_and_last_writer() -> None:
    _case("serve.py 409 response includes conflict_debug + last_writer")
    src = _read("serve.py")

    _assert("_STALE_SAVE_SKEW_SECONDS = 5" in src, "skew threshold is named")
    _assert(
        "def _stale_save_conflict_payload(" in src,
        "central debug-payload helper exists",
    )
    for field in (
        "disk_mtime_epoch",
        "disk_mtime",
        "db_updated_at",
        "db_updated_at_epoch",
        "delta_seconds",
        "threshold_seconds",
        "shares",
        "last_writer",
    ):
        _assert(field in src, f"debug payload carries {field}")

    m = re.search(
        r'"conflict": True,\s*'
        r'"current_updated_at": meta\["updated_at"\],\s*'
        r'"filename": safe \+ "\.json",(?P<body>[\s\S]*?)\}, 409\)',
        src,
    )
    _assert(m is not None, "located 409 response body")
    body = m.group("body")
    _assert('"last_writer": last_writer' in body, "409 response includes last_writer")
    _assert('"conflict_reason": reason' in body, "409 response includes conflict_reason")
    _assert('"conflict_debug": debug' in body, "409 response includes conflict_debug")
    _assert('"last_actor_display_name"' in body, "legacy last_actor_display_name is preserved")


def test_owner_only_mirror_rows_skip_conflict() -> None:
    _case("owner-only mirror rows skip the stale-save conflict")
    src = _read("serve.py")

    _assert(
        "write_collabs = int(meta.get(\"write_share_recipient_count\") or 0)" in src,
        "guard reads write collaborator count",
    )
    _assert(
        "last_actor_is_other = bool(last_actor and last_actor != user)" in src,
        "guard checks if last writer is not the owner",
    )
    _assert(
        "if write_collabs <= 0 and not last_actor_is_other:" in src,
        "owner-only mirror rows skip 409",
    )
    _assert(
        "owner_only_mirror_row" in src,
        "debug reason names owner-only skip",
    )
    _assert(
        "skipped_conflict_debug" in src,
        "skipped owner-only conflicts remain observable in debug mode",
    )


def test_legacy_mirror_save_records_actor_display() -> None:
    _case("legacy mirror save records owner actor/display in event log")
    src = _read("serve.py")

    _assert(
        "user_meta = store.get_user(user)" in src,
        "legacy section save resolves the caller display name",
    )
    _assert(
        "actor=user" in src and "actor_display_name=actor_display" in src,
        "store.save_topology gets explicit actor metadata",
    )


def test_file_ops_surfaces_debug_context_and_uses_authfetch() -> None:
    _case("FileOps banner/log shows last-writer diagnostics and uses authFetch")
    src = _read("topology-file-ops.js")

    section = re.search(
        r"async _sectionSaveWithConflict\(editor, sectionId, body, onSuccess\) \{"
        r"(?P<body>[\s\S]*?)\n    \},\n\n    // Stale-save banner",
        src,
    )
    _assert(section is not None, "located _sectionSaveWithConflict")
    body = section.group("body")
    _assert("TopologyAuth.authFetch" in body, "section save uses authFetch")
    _assert("result.conflict_debug || {}" in body, "console.info logs conflict_debug")
    _assert("lastWriter:" in body, "banner receives lastWriter")
    _assert("conflictReason:" in body, "banner receives conflictReason")
    _assert("conflictDebug:" in body, "banner receives conflictDebug")

    _assert("FileOps._escapeHtml(" in src, "banner escapes backend-provided text")
    _assert("ssb-detail" in src, "banner renders last saved by detail")
    _assert("ssb-debug" in src, "banner renders compact debug detail")


def test_styles_and_cache_busters_are_updated() -> None:
    _case("CSS + cache-busters include stale-save diagnostics")
    css = _read("styles.css")
    index = _read("index.html")

    _assert(".topology-stale-save-banner .ssb-detail" in css, "ssb-detail CSS exists")
    _assert(".topology-stale-save-banner .ssb-debug" in css, "ssb-debug CSS exists")
    _assert(
        "topology-file-ops.js?v=20260426r-conflict-debug" in index,
        "topology-file-ops cache-buster was bumped",
    )
    _assert(
        "styles.css?v=20260426i-conflict-debug" in index,
        "styles.css cache-buster was bumped",
    )


def main() -> int:
    test_user_store_meta_exposes_last_writer_and_share_counts()
    test_serve_conflict_response_has_debug_and_last_writer()
    test_owner_only_mirror_rows_skip_conflict()
    test_legacy_mirror_save_records_actor_display()
    test_file_ops_surfaces_debug_context_and_uses_authfetch()
    test_styles_and_cache_busters_are_updated()
    print("\nAll stale-save conflict diagnostics checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
