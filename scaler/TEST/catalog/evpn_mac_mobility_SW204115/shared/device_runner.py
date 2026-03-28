#!/usr/bin/env python3
"""
Resilient device command runner for EVPN test suites.

Strategy chain (first success wins):
  1. Agent callback (MCP Network Mapper run_show_command) -- preferred, fastest
  2. DNOS_SHOW_HELPER environment variable script
  3. Persistent SSH session via InteractiveSSHSession (prompt-based, no sleeps)
  4. Explicit error (never silent placeholder)

The SSH strategy uses InteractiveSSHSession which:
  - Keeps a single SSH connection open across all commands (no reconnect overhead)
  - Detects the DNOS prompt with 50ms polling (returns immediately, no fixed sleeps)
  - Auto-reconnects after HA triggers that kill the management plane
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("device_runner")

SCALER_DB = Path.home() / "SCALER" / "db" / "devices.json"
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

_runner_cache: Dict[str, Callable] = {}
_session_cache: Dict[str, Any] = {}


def _load_device_db() -> List[Dict[str, Any]]:
    if not SCALER_DB.exists():
        return []
    try:
        data = json.loads(SCALER_DB.read_text())
        return data.get("devices", [])
    except Exception:
        return []


def _normalize_name(name: str) -> str:
    return name.lower().replace("-", "_").replace(" ", "_")


def _resolve_credentials(device: str) -> Optional[Dict[str, str]]:
    """Resolve device name to IP/credentials from SCALER DB or env vars.

    Matching is flexible: tries exact hostname, id, and substring matches
    after normalizing hyphens/spaces to underscores.
    """
    devices = _load_device_db()
    dev_norm = _normalize_name(device)

    for d in devices:
        candidates = [
            _normalize_name(d.get("hostname", "")),
            _normalize_name(d.get("id", "")),
            _normalize_name(d.get("description", "")),
        ]
        if dev_norm in candidates or any(dev_norm in c for c in candidates if c):
            password = d.get("password", "")
            try:
                decoded = base64.b64decode(password).decode("utf-8")
            except Exception:
                decoded = password
            return {
                "ip": d["ip"],
                "username": d.get("username", "dnroot"),
                "password": decoded,
                "hostname": d.get("hostname", device),
            }

    ip = os.environ.get("DNOS_SSH_IP")
    user = os.environ.get("DNOS_SSH_USER", "dnroot")
    pw = os.environ.get("DNOS_SSH_PASS", "dnroot")
    if ip:
        return {"ip": ip, "username": user, "password": pw, "hostname": device}

    return None


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _get_session(creds: Dict[str, str]) -> Any:
    """Get or create a persistent SSH session for this device."""
    from .ssh_session import InteractiveSSHSession

    key = creds["ip"]
    session = _session_cache.get(key)
    if session and session.is_alive():
        return session

    session = InteractiveSSHSession(
        creds["ip"], creds["username"], creds["password"],
    )
    _session_cache[key] = session
    return session


def _helper_execute(device: str, command: str) -> Optional[str]:
    """Execute via DNOS_SHOW_HELPER external script."""
    helper = os.environ.get("DNOS_SHOW_HELPER")
    if not helper or not Path(helper).is_file():
        return None
    try:
        proc = subprocess.run(
            [helper, device, command],
            capture_output=True, text=True, timeout=120,
        )
        return _strip_ansi(proc.stdout or proc.stderr or "")
    except Exception as exc:
        logger.warning("DNOS_SHOW_HELPER failed: %s", exc)
        return None


def create_device_runner(
    device: str,
    agent_callback: Optional[Callable[[str, str], str]] = None,
) -> Callable[[str, str], str]:
    """Create a resilient run_show function with automatic fallback.

    Strategy chain:
      1. agent_callback (MCP Network Mapper) if provided and working
      2. DNOS_SHOW_HELPER environment variable
      3. Persistent SSH session (prompt-based, 50ms polling, auto-reconnect)
      4. Explicit error (never a silent placeholder)

    The returned callable has:
      .method_used  -- dict tracking last strategy used
      .credentials  -- resolved device credentials
      .cleanup()    -- close persistent SSH session when done
    """
    credentials = _resolve_credentials(device)
    method_log: Dict[str, Any] = {"last": "none", "attempts": []}

    def run_show(dev: str, command: str) -> str:
        # Strategy 1: Agent callback (MCP)
        if agent_callback:
            try:
                result = agent_callback(dev, command)
                if result and not result.startswith("[ERROR]"):
                    placeholder_markers = ('"status": "placeholder"', "MCP Jira search placeholder")
                    if not any(m in result for m in placeholder_markers):
                        method_log["last"] = "mcp"
                        return result
            except Exception as exc:
                method_log["attempts"].append(("mcp", str(exc)))
                logger.info("MCP callback failed (%s), falling back to helper/SSH", exc)

        # Strategy 2: DNOS_SHOW_HELPER
        result = _helper_execute(dev, command)
        if result is not None:
            method_log["last"] = "helper"
            return result

        # Strategy 3: Persistent SSH session with prompt detection
        creds = credentials or _resolve_credentials(dev)
        if creds:
            try:
                session = _get_session(creds)
                result = session.send_command(command)
                if not result.startswith("[SSH ERROR]"):
                    method_log["last"] = "ssh_session"
                    return result
                method_log["attempts"].append(("ssh_session", result[:200]))
            except Exception as exc:
                method_log["attempts"].append(("ssh_session", str(exc)))
                logger.warning("SSH session failed for %s: %s", dev, exc)
                return f"[SSH ERROR] {type(exc).__name__}: {exc}"

        return (
            f"[ERROR] No method available to reach device '{dev}'. "
            f"Ensure MCP Network Mapper is running, or set DNOS_SHOW_HELPER, "
            f"or add device to ~/SCALER/db/devices.json for SSH fallback."
        )

    def cleanup() -> None:
        """Close any persistent SSH sessions held by this runner."""
        if credentials:
            key = credentials["ip"]
            session = _session_cache.pop(key, None)
            if session:
                try:
                    session.close()
                except Exception:
                    pass

    run_show.method_used = method_log  # type: ignore[attr-defined]
    run_show.credentials = credentials  # type: ignore[attr-defined]
    run_show.cleanup = cleanup  # type: ignore[attr-defined]
    return run_show


def get_cached_runner(
    device: str,
    agent_callback: Optional[Callable[[str, str], str]] = None,
) -> Callable[[str, str], str]:
    """Return a cached device runner (avoids re-resolving credentials per call)."""
    key = f"{device}:{id(agent_callback)}"
    if key not in _runner_cache:
        _runner_cache[key] = create_device_runner(device, agent_callback)
    return _runner_cache[key]


def cleanup_all_sessions() -> None:
    """Close all cached SSH sessions and runners. Call at test suite end."""
    for key, session in list(_session_cache.items()):
        try:
            session.close()
        except Exception:
            pass
    _session_cache.clear()
    _runner_cache.clear()
