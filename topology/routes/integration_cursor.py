"""Cursor integration endpoints for the Topology MCP + skill install flow."""

from __future__ import annotations

import io
import tarfile
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from api.auth.user_store import user_store
from mcp import VERSION
from mcp.auth import bearer_from_headers, resolve_bearer_token
from mcp.dispatcher import list_tool_names, tool_schemas


router = APIRouter(prefix="/api/integration/cursor", tags=["Cursor Integration"])


def _current_user(request: Request) -> Dict[str, Any]:
    username = resolve_bearer_token(bearer_from_headers(request.headers))
    if not username:
        raise HTTPException(status_code=401, detail="Authentication required")
    user = user_store.get_user(username)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return dict(user)


def _base_url(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-proto")
    scheme = forwarded or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"{scheme}://{host}".rstrip("/")


def _install_prompt(base_url: str, token: str, username: str) -> str:
    return f"""Install the DriveNets Topology MCP and skill for me.

Canonical instructions: {base_url}/api/integration/cursor/install

Steps:
1. Add MCP server "topology" to ~/.cursor/mcp.json:
   url: {base_url}/mcp/sse
   headers.Authorization: Bearer {token}
2. Download skill bundle to ~/.cursor/skills/topology/:
   mkdir -p ~/.cursor/skills/topology
   curl -sSL -H "Authorization: Bearer {token}" {base_url}/api/integration/cursor/skill.tar.gz | tar -xz -C ~/.cursor/skills/topology
3. Reload Cursor window so the MCP loader binds the new server.
4. Verify by calling topology_health. Expected: ok=true and username={username}.
"""


@router.get("/install")
async def install_instructions(request: Request, user=Depends(_current_user)) -> Dict[str, Any]:
    base = _base_url(request)
    return {
        "ok": True,
        "version": VERSION,
        "username": user["username"],
        "mcp": {
            "name": "topology",
            "transport": "sse",
            "url": f"{base}/mcp/sse",
            "headers": {"Authorization": "Bearer <USER_TOKEN>"},
        },
        "skill": {
            "url": f"{base}/api/integration/cursor/skill.tar.gz",
            "target_dir": "~/.cursor/skills/topology",
        },
        "verify_tool": "topology_health",
        "tools": list_tool_names(),
        "schemas": tool_schemas(),
    }


@router.get("/token")
async def token_status(user=Depends(_current_user)) -> Dict[str, Any]:
    return {"ok": True, **user_store.cursor_token_status(user["username"])}


@router.post("/token")
async def issue_token(request: Request, user=Depends(_current_user)) -> Dict[str, Any]:
    issued = user_store.issue_cursor_token(user["username"])
    base = _base_url(request)
    return {
        "ok": True,
        "token": issued["token"],
        "created_at": issued["created_at"],
        "prompt": _install_prompt(base, issued["token"], user["username"]),
    }


@router.delete("/token")
async def revoke_token(user=Depends(_current_user)) -> Dict[str, Any]:
    return {"ok": user_store.revoke_cursor_token(user["username"])}


@router.get("/prompt")
async def install_prompt(request: Request, user=Depends(_current_user)) -> Response:
    issued = user_store.issue_cursor_token(user["username"])
    prompt = _install_prompt(_base_url(request), issued["token"], user["username"])
    return Response(prompt, media_type="text/plain; charset=utf-8")


@router.get("/skill.tar.gz")
async def skill_bundle(user=Depends(_current_user)) -> Response:
    bundle_dir = Path(__file__).resolve().parents[1] / "mcp" / "skill_bundle"
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for path in sorted(bundle_dir.iterdir()):
            if path.is_file():
                tar.add(path, arcname=path.name)
    return Response(
        buf.getvalue(),
        media_type="application/gzip",
        headers={"Content-Disposition": 'attachment; filename="topology-skill.tar.gz"'},
    )

