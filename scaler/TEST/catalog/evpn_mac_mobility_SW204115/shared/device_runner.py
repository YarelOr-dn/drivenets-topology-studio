#!/usr/bin/env python3
"""
Resilient device command runner for EVPN test suites.

Strategy chain (first success wins):
  0. dnos-config MCP (dnos_run_show_commands) -- automatic when service is up
  1. Agent callback (MCP Network Mapper run_show_command) -- legacy, optional
  2. DNOS_SHOW_HELPER environment variable script
  3. Persistent SSH session via InteractiveSSHSession (prompt-based, no sleeps)
  4. Explicit error (never silent placeholder)

The SSH strategy uses InteractiveSSHSession which:
  - Keeps a single SSH connection open across all commands (no reconnect overhead)
  - Detects the DNOS prompt with 50ms polling (returns immediately, no fixed sleeps)
  - Auto-reconnects after HA triggers that kill the management plane

MCP-first routing (Strategy 0)
------------------------------
When the dnos-config MCP service is reachable on http://localhost:9300, every
show command is automatically routed through it -- no per-test wiring needed.
This delivers:
  - Persistent SSH session reuse on the MCP side (single connect per device)
  - Cross-test command corrections (the MCP self-heals known syntax errors)
  - Built-in rejection detection (Unknown word / Incomplete command)
  - Cross-chat handoff visibility (commands appear in MCP audit log)

The MCP probe runs ONCE per device per process (cached). If the service is
down we silently fall through to the existing strategies; users may set
TEST_DISABLE_MCP=1 to opt out entirely.
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

from .command_guard import CommandGuardError, guard_command

logger = logging.getLogger("device_runner")

SCALER_DB = Path.home() / "SCALER" / "db" / "devices.json"
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

_runner_cache: Dict[str, Callable] = {}
_session_cache: Dict[str, Any] = {}

# ---------------------------------------------------------------------------
# Config-mode deadlock guard
# ---------------------------------------------------------------------------
# DNOS prompts for `yes/no/cancel` when a session in `config` mode is asked
# to run a show/clear command while the candidate has uncommitted changes:
#
#     "Configuration includes uncommitted changes, would you like to commit
#      them before exiting (yes/no/cancel)?"
#
# Our SSH layer expects a `#` prompt and times out (~150s) instead of
# answering. One stuck session, even silently, can add 5+ minutes to a test.
# Worse, every subsequent command on that session ALSO hits the prompt.
#
# This guard:
#   * Detects the warning in any output the runner sees
#   * Auto-recovers by sending `no` (decline commit) -> `end` (leave config)
#     before returning -- so the next command doesn't deadlock
#   * Is fast (sub-second) and idempotent
#   * Applies to EVERY /TEST suite that uses create_device_runner()
#
# We track recovered-state per device so the user-visible warning is logged
# only once per session.

_CONFIG_PROMPT_MARKERS = (
    "Configuration includes uncommitted changes",
    "would you like to commit them before exiting",
    "(yes/no/cancel)",
)

_RECOVERY_FLAGS: Dict[str, int] = {}  # device -> recovery_count for this process


def _is_config_mode_deadlock(output: str) -> bool:
    """Return True if `output` contains the DNOS uncommitted-changes prompt."""
    if not output:
        return False
    return any(marker in output for marker in _CONFIG_PROMPT_MARKERS)


def _recover_config_mode_session(dev: str, send_fn: Callable[[str, str], str]) -> None:
    """Forcibly drag a stuck SSH session back to operational mode.

    Sends, in order:
      1. ``no``        -- answer the yes/no/cancel prompt; declines commit
      2. ``rollback 0`` -- discard any uncommitted candidate
      3. ``end``        -- leave config mode

    Each call is best-effort and bounded; we ignore "Unknown word" replies
    because they just mean we're already in operational mode. The guard's
    job is to ensure the NEXT command sees a clean `#` prompt.
    """
    _RECOVERY_FLAGS[dev] = _RECOVERY_FLAGS.get(dev, 0) + 1
    logger.warning(
        "[CONFIG-MODE-GUARD] Detected stuck config-mode session on %s "
        "(uncommitted-changes prompt); auto-recovering #%d",
        dev,
        _RECOVERY_FLAGS[dev],
    )
    print(
        f"    [CONFIG-MODE-GUARD] {dev}: auto-recovering from uncommitted-changes "
        f"prompt deadlock (recovery #{_RECOVERY_FLAGS[dev]})",
        flush=True,
    )
    for cmd in ("no", "rollback 0", "end"):
        try:
            send_fn(dev, cmd)
        except Exception:
            pass  # any error here means we just keep going

# ---------------------------------------------------------------------------
# Strategy 0: dnos-config MCP (auto-detected, cached per process)
# ---------------------------------------------------------------------------

_MCP_HEALTH_URL = os.environ.get("DNOS_CONFIG_MCP_HEALTH",
                                 "http://localhost:9300/health")
_mcp_handle_call: Optional[Callable[[str, dict], dict]] = None
_mcp_probed: bool = False


def _probe_mcp() -> Optional[Callable[[str, dict], dict]]:
    """Return the in-process handle_tool_call if the dnos-config MCP is healthy.

    Cached: probe runs at most once per process. Set TEST_DISABLE_MCP=1 to skip.

    The /health probe is retried once with a longer timeout (5s) before
    falling through to legacy Strategies 1-3. The previous 1.5s single-shot
    occasionally raced systemd-managed MCP startup (or a busy first call)
    and caused a spurious "SSH session failed for X: timed out" warning at
    the very first command of a run. The retry costs nothing in the steady
    state (the cached `True` short-circuits all subsequent calls).
    """
    global _mcp_handle_call, _mcp_probed
    if _mcp_probed:
        return _mcp_handle_call
    _mcp_probed = True

    if os.environ.get("TEST_DISABLE_MCP", "").lower() in ("1", "true", "yes"):
        logger.info("device_runner: TEST_DISABLE_MCP set, skipping MCP")
        return None

    import urllib.request
    import time as _time
    health_ok = False
    last_exc: Optional[Exception] = None
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(_MCP_HEALTH_URL, timeout=5.0) as resp:
                data = json.loads(resp.read())
                if data.get("status") == "ok":
                    health_ok = True
                    break
                logger.info("device_runner: MCP /health not ok (attempt %d): %s",
                            attempt, data)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            logger.info("device_runner: MCP /health attempt %d failed: %s",
                        attempt, exc)
            if attempt == 1:
                _time.sleep(0.5)  # brief pause; cheap insurance against startup race
    if not health_ok:
        logger.info("device_runner: MCP unreachable at %s (%s) -- falling back",
                    _MCP_HEALTH_URL, last_exc)
        return None

    try:
        import sys as _sys
        if "/home/dn/dnos_config_mcp" not in _sys.path:
            _sys.path.insert(0, "/home/dn/dnos_config_mcp")
        from dnos_config_mcp.tools import handle_tool_call as _h
        _mcp_handle_call = _h
        logger.info("device_runner: dnos-config MCP wired (Strategy 0 active)")
        return _h
    except Exception as exc:  # noqa: BLE001
        logger.info("device_runner: MCP module import failed: %s", exc)
        return None


def _mcp_run_show(device: str, command: str) -> Optional[str]:
    """Call dnos_run_show_commands via the in-process MCP entrypoint.

    Returns the raw command output on success, None if the MCP is unavailable
    or the call dispatcher itself failed. Returns the device's own error text
    when DNOS rejects the command -- callers should treat that as a real
    response (the existing error-marker scan in session_io picks it up and
    records the failure for self-healing).
    """
    handle = _probe_mcp()
    if handle is None:
        return None
    try:
        res = handle("dnos_run_show_commands", {
            "device_name": device,
            "commands": [command],
        })
    except Exception as exc:  # noqa: BLE001
        logger.warning("device_runner: MCP call raised %s for %s",
                       type(exc).__name__, device)
        return None
    if not isinstance(res, dict):
        return None
    results = res.get("results") or []
    if not results:
        partial = res.get("partial_results") or []
        if partial:
            rec = partial[0]
            return rec.get("output", "") or rec.get("error", "") or json.dumps(rec)[:2000]
        errors = res.get("errors") or []
        if errors:
            return "[ERROR] dnos-config MCP: " + "; ".join(str(e) for e in errors)
        if res.get("ok") is False:
            return "[ERROR] dnos-config MCP returned ok=false with no command output"
        return None
    rec = results[0]
    out = rec.get("output", "")
    err = rec.get("error", "")
    if rec.get("ok"):
        return out
    # ok=false: device rejected the command. Return the rejection text so the
    # session_io error scan can record the failure (same behaviour as SSH path).
    if err:
        return err
    return out or None


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
        for alias in d.get("aliases", []):
            candidates.append(_normalize_name(alias))
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
        # Wrap the strategy chain so we capture (cmd -> output -> method) for
        # the per-run transcript regardless of which strategy executed.
        import time as _t
        try:
            from . import run_transcript as _xcript  # type: ignore
        except Exception:  # pragma: no cover
            _xcript = None  # logging is best-effort
        _t0 = _t.monotonic()
        result = ""
        method = "error"

        def _maybe_recover(out: str) -> None:
            """If `out` is a config-mode deadlock prompt, kick the session
            back to operational mode so the NEXT command isn't also stuck.

            This is the systemic guard for ALL /TEST suites: one slip in a
            provisioner that returns False without cleaning up `config` mode
            used to cascade into 150s-per-command deadlocks. Now any single
            command that sees the prompt is the worst case -- the guard
            recovers before returning so subsequent commands run normally.
            """
            if not _is_config_mode_deadlock(out):
                return
            # Avoid infinite recursion: don't recover on commands we send
            # AS PART OF the recovery itself.
            if command.strip() in ("no", "rollback 0", "end"):
                return
            try:
                _recover_config_mode_session(dev, run_show)  # noqa: F821 (closure)
            except Exception as exc:
                logger.warning("[CONFIG-MODE-GUARD] recovery failed: %s", exc)

        try:
            try:
                guard_command(command, context=f"{dev}/run_show")
            except CommandGuardError as exc:
                method = "command_guard"
                result = str(exc)
                raise

            # Strategy 0: dnos-config MCP (auto-routed when service is up)
            mcp_result = _mcp_run_show(dev, command)
            if mcp_result is not None:
                method_log["last"] = "dnos_config_mcp"
                method = "dnos_config_mcp"
                result = mcp_result
                _maybe_recover(mcp_result)
                return mcp_result
            if _mcp_handle_call is not None:
                method_log["last"] = "dnos_config_mcp_no_output"
                method = "dnos_config_mcp_no_output"
                result = (
                    "[ERROR] dnos-config MCP is available but returned no output "
                    f"for command {command!r}; refusing raw SSH fallback. "
                    "Route non-show/config-mode work through the proper MCP "
                    "commit or scenario executor."
                )
                return result

            # Strategy 1: Agent callback (MCP Network Mapper, legacy)
            if agent_callback:
                try:
                    cb_result = agent_callback(dev, command)
                    if cb_result and not cb_result.startswith("[ERROR]"):
                        placeholder_markers = (
                            '"status": "placeholder"',
                            "MCP Jira search placeholder",
                        )
                        if not any(m in cb_result for m in placeholder_markers):
                            method_log["last"] = "mcp"
                            method = "mcp_network_mapper"
                            result = cb_result
                            _maybe_recover(cb_result)
                            return cb_result
                except Exception as exc:
                    method_log["attempts"].append(("mcp", str(exc)))
                    logger.info(
                        "MCP callback failed (%s), falling back to helper/SSH", exc,
                    )

            # Strategy 2: DNOS_SHOW_HELPER
            helper_result = _helper_execute(dev, command)
            if helper_result is not None:
                method_log["last"] = "helper"
                method = "helper"
                result = helper_result
                _maybe_recover(helper_result)
                return helper_result

            # Strategy 3: Persistent SSH session with prompt detection
            creds = credentials or _resolve_credentials(dev)
            if creds:
                try:
                    session = _get_session(creds)
                    ssh_result = session.send_command(command)
                    if not ssh_result.startswith("[SSH ERROR]"):
                        method_log["last"] = "ssh_session"
                        method = "ssh_session"
                        result = ssh_result
                        _maybe_recover(ssh_result)
                        return ssh_result
                    method_log["attempts"].append(("ssh_session", ssh_result[:200]))
                    method = "ssh_error"
                    result = ssh_result
                    return ssh_result
                except Exception as exc:
                    method_log["attempts"].append(("ssh_session", str(exc)))
                    logger.warning("SSH session failed for %s: %s", dev, exc)
                    method = "ssh_exception"
                    result = f"[SSH ERROR] {type(exc).__name__}: {exc}"
                    return result

            method = "no_method"
            result = (
                f"[ERROR] No method available to reach device '{dev}'. "
                f"Ensure MCP Network Mapper is running, or set DNOS_SHOW_HELPER, "
                f"or add device to ~/SCALER/db/devices.json for SSH fallback."
            )
            return result
        finally:
            if _xcript is not None:
                try:
                    _xcript.record_command(
                        device=dev,
                        command=command,
                        output=result,
                        method=method,
                        elapsed_ms=(_t.monotonic() - _t0) * 1000,
                    )
                except Exception:
                    pass  # never fail a test because logging failed

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


def get_persistent_ssh_session(device: str) -> Optional[Any]:
    """Return a cached, stateful SSH session for ``device`` (or ``None``).

    Use this when a handler needs to drive multi-step stateful flows
    (``configure`` ... ``commit check`` ... ``rollback 0`` ... ``end``) that
    the MCP ``run_show_command`` strategy cannot support -- MCP runs each
    command in a fresh shell, losing config-mode state.

    Returns ``None`` if no SSH credentials can be resolved (device missing
    from ``~/SCALER/db/devices.json`` and ``DNOS_SSH_IP`` env var unset).

    The session is the same one cached internally for SSH fallback in
    ``run_show``, so reusing it here avoids opening a second connection.
    Closing happens via :func:`cleanup_all_sessions` at suite end.
    """
    creds = _resolve_credentials(device)
    if not creds:
        return None
    try:
        return _get_session(creds)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to open SSH session for %s: %s", device, exc)
        return None


def get_session_credentials(device: str) -> Optional[Dict[str, str]]:
    """Return the resolved ``{ip, username, password, hostname}`` for *device*.

    Companion to :func:`get_persistent_ssh_session`. Some flows (notably the
    inner-shell runner -- ``run start shell``, ``vtysh``, ``xraycli``) need
    the device password to answer secondary prompts that some DNOS builds
    raise inside nested containers. The persistent ``DNOSSession`` does not
    re-expose the password, so callers go through this helper instead.

    Returns ``None`` when ``_resolve_credentials`` cannot find an entry --
    same semantics as ``get_persistent_ssh_session``.
    """
    return _resolve_credentials(device)


def cleanup_all_sessions() -> None:
    """Close all cached SSH sessions and runners. Call at test suite end."""
    for _key, session in list(_session_cache.items()):
        try:
            session.close()
        except Exception:
            pass
    _session_cache.clear()
    _runner_cache.clear()
