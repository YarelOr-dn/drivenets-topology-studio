#!/usr/bin/env python3
"""Live DNOS syntax probes for /TP spec-binding (cmd-search + ?-completion cache).

No dedicated ?-completion MCP tool: completion results are cached by the agent
via record_question_mark_probe(). dnos_cmd_search may be invoked when MCP CLI is
available; otherwise reads ~/.cursor/tp_cache/live_probe_* (24h TTL).
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

from _tp_paths import resolve_mcp_cli
from typing import Any

from _tp_syntax_common import TP_CACHE_DIR, atomic_write_json, normalize_cmd

_CACHE_TTL_SEC = 24 * 3600
_MCP_CLI = resolve_mcp_cli()
_PYTHON = "/usr/bin/python3"


def _cache_path(device: str, cmd: str) -> Path:
    h = hashlib.sha256(normalize_cmd(cmd).encode()).hexdigest()[:16]
    safe_dev = re.sub(r"[^\w.-]", "_", device)
    return TP_CACHE_DIR / f"live_probe_{safe_dev}_{h}.json"


def _read_cache(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        ts = float(data.get("ts") or 0)
        if time.time() - ts > _CACHE_TTL_SEC:
            return None
        return data
    except (json.JSONDecodeError, OSError, ValueError):
        return None


def record_question_mark_probe(device: str, cmd: str, completion: str, *, source: str = "agent") -> None:
    """Agent/MCP path records ?-completion authority into the live probe cache."""
    path = _cache_path(device, cmd)
    atomic_write_json(
        path,
        {
            "device": device,
            "command": cmd,
            "cmd_search": None,
            "question_mark": completion,
            "ts": time.time(),
            "source": source,
        },
    )


def _mcp_cmd_search(device: str, keyword: str) -> dict | None:
    if not _MCP_CLI.is_file():
        return None
    payload = json.dumps({"device_name": device, "keyword": keyword, "format": "json"})
    try:
        p = subprocess.run(
            [_PYTHON, str(_MCP_CLI), "user-dnos-config-mcp", "dnos_cmd_search", payload],
            capture_output=True,
            text=True,
            timeout=45,
        )
        if p.returncode != 0:
            return None
        return json.loads(p.stdout or "{}")
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return None


def _syntax_keyword(cmd: str) -> str:
    parts = cmd.strip().split()
    return " ".join(parts[:4]) if len(parts) >= 4 else cmd.strip()


def probe_device_reachable(device: str) -> dict[str, Any]:
    """Best-effort reachability via cmd-search on a trivial keyword."""
    hit = _mcp_cmd_search(device, "show version")
    reachable = bool(hit and hit.get("ok"))
    build = None
    if isinstance(hit, dict):
        build = hit.get("device_version") or hit.get("version")
    return {"device": device, "reachable": reachable, "build": build}


def probe_live_syntax(device: str, cmd: str) -> dict[str, Any]:
    """Return {cmd_search, question_mark, state} for one command."""
    cached = _read_cache(_cache_path(device, cmd))
    if cached:
        cs = cached.get("cmd_search")
        qm = cached.get("question_mark")
        state = None
        if qm:
            state = "LIVE_QUESTION_MARK"
        elif cs:
            state = "LIVE_CMD_SEARCH"
        return {"cmd_search": cs, "question_mark": qm, "state": state, "cache": True}

    keyword = _syntax_keyword(cmd)
    cs = _mcp_cmd_search(device, keyword)
    cs_hit = bool(cs and cs.get("ok"))
    qm = None
    state = None
    if cs_hit:
        state = "LIVE_CMD_SEARCH"
    result = {
        "device": device,
        "command": cmd,
        "cmd_search": cs if cs_hit else None,
        "question_mark": qm,
        "ts": time.time(),
        "state": state,
    }
    if cs_hit or qm:
        atomic_write_json(_cache_path(device, cmd), result)
    return {"cmd_search": result["cmd_search"], "question_mark": qm, "state": state, "cache": False}
