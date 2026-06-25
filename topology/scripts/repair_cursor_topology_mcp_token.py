#!/usr/bin/env python3
"""Rotate the per-user Topology MCP token and update Cursor's MCP config.

This helper intentionally does not print the raw token. It writes
``~/.cursor/mcp.json`` atomically because that file is shared Cursor state.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TOPOLOGY_ROOT = REPO_ROOT / "topology"
if str(TOPOLOGY_ROOT) not in sys.path:
    sys.path.insert(0, str(TOPOLOGY_ROOT))

from api.auth.user_store import user_store  # noqa: E402


def atomic_write_json(path: Path, payload: dict) -> None:
    body = json.dumps(payload, indent=2, sort_keys=False) + "\n"
    try:
        prior_mode = path.stat().st_mode & 0o777
    except FileNotFoundError:
        prior_mode = 0o600
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(body)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, prior_mode)
        os.replace(tmp, path)
    except BaseException:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    username = sys.argv[1] if len(sys.argv) > 1 else "yor"
    if not user_store.get_user(username):
        print(f"ERROR: user {username!r} does not exist", file=sys.stderr)
        return 2

    issued = user_store.issue_cursor_token(username)
    token = issued["token"]

    config_path = Path.home() / ".cursor" / "mcp.json"
    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)

    servers = config.setdefault("mcpServers", {})
    topology = servers.setdefault("topology", {})
    topology["url"] = "http://127.0.0.1:8080/mcp/sse"
    headers = topology.setdefault("headers", {})
    headers["Authorization"] = f"Bearer {token}"

    atomic_write_json(config_path, config)
    status = user_store.cursor_token_status(username)
    print(
        "updated topology MCP token:",
        f"user={username}",
        f"created_at={status.get('created_at', '')}",
        f"hint={status.get('token_hint', '')}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
