#!/usr/bin/env python3
"""
Idempotent TEST: description tagger for DUT objects.

User mandate (2026-04-21): add descriptions for /TEST and /SPIRENT-owned
interfaces and instances so automation can detect ownership quickly.

Description tagging is static DUT config. Per the /TEST device interaction
tree, it must use dnos_atomic_commit rather than run_show/config-mode line
pushes. This keeps the operation transactional and prevents MCP-backed
run_show calls from treating config commands as operational show commands.
"""

from __future__ import annotations

import os
import re
import sys
import urllib.request
from typing import Callable, Dict, List, Optional, Sequence, Tuple

TagSpec = Tuple[str, str]  # (config_path, role[/extra])

_DNOS_CONFIG_MCP_HEALTH = os.environ.get(
    "DNOS_CONFIG_MCP_HEALTH",
    "http://localhost:9300/health",
)


def _parse_current_description(config_text: str) -> Optional[str]:
    """Return the current description (without quotes) or None."""
    for line in config_text.splitlines():
        m = re.search(r'^\s*description\s+(.*?)\s*$', line)
        if m:
            return m.group(1).strip().strip('"')
    return None


def _merge_test_tag(existing: Optional[str], new_tag: str) -> str:
    """Return merged description preserving any non-TEST:<same-id> content."""
    if not existing:
        return new_tag
    if new_tag in existing:
        return existing
    prefix = new_tag.split("/", 1)[0] if "/" in new_tag else new_tag
    cleaned = re.sub(
        r"\s*\|\s*" + re.escape(prefix) + r"/?\S*",
        "",
        existing,
    ).strip(" |")
    cleaned = re.sub(
        r"^" + re.escape(prefix) + r"/?\S*(\s*\|\s*)?",
        "",
        cleaned,
    ).strip(" |")
    return f"{cleaned} | {new_tag}" if cleaned else new_tag


class _StdoutResult:
    """Minimal stand-in for ProvisionResult when the caller doesn't use one."""

    def add(self, step: str, status: str, detail: str) -> None:
        print(f"  [{step}] {status} -- {detail}", flush=True)


def _probe_dnos_atomic_commit():
    """Return dnos-config MCP handle_tool_call when the local service is healthy."""
    try:
        with urllib.request.urlopen(_DNOS_CONFIG_MCP_HEALTH, timeout=2) as resp:
            if resp.status != 200:
                return None
    except Exception:
        return None

    if "/home/dn/dnos_config_mcp" not in sys.path:
        sys.path.insert(0, "/home/dn/dnos_config_mcp")
    try:
        from dnos_config_mcp.tools import handle_tool_call
    except Exception:
        return None
    return handle_tool_call


def _format_atomic_result(res: Dict) -> str:
    parts = [
        f"phase={res.get('phase', '?')}",
        f"rolled_back={res.get('rolled_back', False)}",
    ]
    commit_check = res.get("commit_check") or {}
    if commit_check:
        parts.append(
            "commit_check.ok="
            f"{commit_check.get('ok')} "
            f"out={(commit_check.get('output') or '')[:120]!r}"
        )
    commit = res.get("commit") or {}
    if commit:
        parts.append(
            "commit.ok="
            f"{commit.get('ok')} out={(commit.get('output') or '')[:120]!r}"
        )
    bad = [line for line in (res.get("lines") or []) if not line.get("ok")]
    if bad:
        parts.append(
            "bad_lines="
            + ", ".join(
                f"{b.get('line')!r}->{(b.get('output') or '')[:80]!r}"
                for b in bad[:3]
            )
        )
    errors = res.get("errors") or []
    if errors:
        parts.append("errors=" + " | ".join(errors[:3]))
    return " ; ".join(parts)


def _atomic_commit_descriptions(
    *,
    device: str,
    commands: Sequence[str],
    verify_commands: Sequence[str],
) -> Tuple[bool, str]:
    handle = _probe_dnos_atomic_commit()
    if handle is None:
        return False, (
            "[orchestrator-bug] dnos-config MCP unavailable; description "
            "tagging requires dnos_atomic_commit"
        )

    # Prefix every absolute config command with top so auto-descended DNOS
    # config prompts cannot shift the parse root between sibling commands.
    lines: List[str] = []
    for cmd in commands:
        lines.extend(("top", cmd))
    config_text = "\n".join(lines) + "\n"

    try:
        res = handle(
            "dnos_atomic_commit",
            {
                "device_name": device,
                "config_text": config_text,
                "verify_commands": list(verify_commands),
            },
        )
    except Exception as exc:
        return False, (
            "[orchestrator-bug] dnos_atomic_commit raised "
            f"{type(exc).__name__}: {exc}"
        )

    if not isinstance(res, dict):
        return False, (
            "[orchestrator-bug] dnos_atomic_commit returned "
            f"{type(res).__name__}"
        )
    return bool(res.get("ok")), _format_atomic_result(res)


def apply_test_descriptions(
    *,
    device: str,
    run_show: Callable[[str, str], str],
    result=None,
    test_id: str,
    objects: Sequence[TagSpec],
    step_name: str = "test_desc_tags",
    commit_fn: Optional[Callable] = None,
    cfg_block_fn: Optional[Callable] = None,
) -> bool:
    """Idempotently tag each object with a TEST:<test_id>/<role> description.

    ``commit_fn`` and ``cfg_block_fn`` remain accepted for API compatibility,
    but are intentionally ignored. Those legacy helpers route config lines via
    run_show in MCP-backed runs, which is exactly the bug this module prevents.
    """
    del commit_fn, cfg_block_fn

    if not objects:
        return True
    if result is None:
        result = _StdoutResult()

    patches: List[Tuple[str, str, str, str]] = []  # (path, cur, new, cmd)
    for path, role in objects:
        tag_prefix = f"TEST:{test_id}"
        new_tag = f"{tag_prefix}/{role}"
        cur_cfg = run_show(device, f"show config {path} | no-more") or ""
        cur = _parse_current_description(cur_cfg)
        merged = _merge_test_tag(cur, new_tag)
        if merged == cur:
            continue
        cmd = f'{path} description "{merged}"'
        patches.append((path, cur or "<none>", merged, cmd))

    if not patches:
        result.add(step_name, "PASS", f"{len(objects)} objects already tagged")
        return True

    ok, out = _atomic_commit_descriptions(
        device=device,
        commands=[p[3] for p in patches],
        verify_commands=[f"show config {p[0]} | no-more" for p in patches],
    )
    if not ok:
        result.add(
            step_name,
            "FAIL",
            f"atomic description commit failed: {out[:240] if out else 'unknown'}",
        )
        return False

    result.add(
        step_name,
        "PASS",
        f"{len(patches)} TEST:{test_id}/* descriptions applied "
        f"({len(objects) - len(patches)} already in sync); {out[:180]}",
    )
    return True


__all__ = ["apply_test_descriptions", "TagSpec"]
