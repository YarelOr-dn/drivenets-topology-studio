#!/usr/bin/env python3
"""
spirent_watchdog -- shared Spirent session watchdog with FSM integration.

Replaces the per-recipe retry logic scattered in `mac_trigger.py._run_spirent`
with a single, session-wide watchdog that:

    * Caches a 5s-window health probe (`spirent_tool.py status --json`)
    * Classifies failures -> emits RecoveryEvent to RecoveryFsmLite
    * Exposes state to /tmp/spirent_watchdog.json for /SPIRENT status
    * Provides `guarded_run()` which runs any spirent_tool.py command and
      asks the FSM to heal on failure

FSM coupling:
    watchdog = SpirentWatchdog(fsm=fsm, tool_path=spirent_tool_path())
    result = watchdog.guarded_run(["create-stream", ...])

If the command fails because the session is dead, the watchdog asks the FSM
to heal (reconnect, then Lab Server recovery). If healing succeeds, it
retries the same command. On FSM UNRECOVERABLE, it re-raises.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .recovery_fsm_lite import (
    RecoveryEvent,
    RecoveryFsmLite,
    RecoveryState,
    UnrecoverableError,
    default_spirent_lab_server_healer,
    default_spirent_reconnect_healer,
)

logger = logging.getLogger(__name__)

WATCHDOG_STATE_PATH = Path(tempfile.gettempdir()) / "spirent_watchdog.json"


# Signatures that indicate a dead/degraded Spirent session.
_DEAD_SESSION_SIGNATURES = (
    "No active session",
    "Port not reserved",
    "Stale handles",
    "Session not found",
    "Session marked inactive",
    "Connection refused",
    "timed out",
    "HTTPError",
    "ConnectionError",
    "404",
    "BLL Handle",
    "stcweb",
)

# Mutating commands that warrant an extra retry after heal.
_MUTATING = {
    "create-device", "create-stream", "vpls-stream", "remove-device",
    "remove-stream", "protocol-start", "protocol-stop",
    "bgp-peer", "ecmp", "evpn-routes", "add-routes",
}

_READONLY = {
    "status", "show", "devices", "streams", "port-status",
    "get-mac-table", "get-arp-table", "ports",
}


@dataclass
class SpirentHealth:
    """Cached health probe result."""

    ts: float = 0.0
    healthy: bool = False
    active: bool = False
    port_reserved: bool = False
    raw: Dict[str, Any] = field(default_factory=dict)

    def is_fresh(self, ttl_sec: float) -> bool:
        return (time.time() - self.ts) < ttl_sec and self.ts > 0


@dataclass
class WatchdogState:
    """Serialised to WATCHDOG_STATE_PATH."""

    state: str = "idle"                          # idle | healthy | reconnecting | lab_server | dead
    last_probe_ts: float = 0.0
    last_heal_ts: float = 0.0
    last_heal_event: str = ""
    fail_count: int = 0
    total_heals: int = 0
    total_lab_server_recovers: int = 0
    port_reserved: bool = False
    session_active: bool = False
    fsm_state: str = ""
    last_error: str = ""
    correlation_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        return d


@dataclass
class SpirentCmdResult:
    """Return value of guarded_run()."""

    rc: int
    stdout: str = ""
    stderr: str = ""
    combined: str = ""
    healed: bool = False
    attempts: int = 1
    command: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.rc == 0


class SpirentUnrecoverableError(RuntimeError):
    """Raised when the watchdog can't recover the Spirent session."""


class SpirentWatchdog:
    """Session-wide watchdog for spirent_tool.py invocations.

    One watchdog per test session (typically created by the orchestrator /
    scenario_runner). Commands issued through `guarded_run` get automatic
    pre-flight health check, automatic heal + retry on dead-session errors,
    and state telemetry.

    Arguments:
        fsm         -- RecoveryFsmLite (events + healers are registered here)
        tool_path   -- Path to spirent_tool.py (or str).
        probe_ttl_s -- Health-probe cache TTL (default 5s).
        max_retries -- Hard retry cap per guarded_run (default 3).
        autostart_healers -- If True and the FSM has no healer for
                       SPIRENT_HEAL_RECONNECT / SPIRENT_HEAL_LAB_SERVER,
                       register `default_spirent_*_healer` automatically.
    """

    def __init__(
        self,
        fsm: RecoveryFsmLite,
        tool_path: Optional[Path] = None,
        probe_ttl_s: float = 5.0,
        max_retries: int = 3,
        python: str = "python3",
        autostart_healers: bool = True,
    ) -> None:
        self.fsm = fsm
        self.tool_path = Path(tool_path) if tool_path else _discover_tool_path()
        self.probe_ttl_s = probe_ttl_s
        self.max_retries = max_retries
        self.python = python
        self.health = SpirentHealth()
        self.state = WatchdogState(correlation_id=self.fsm.context.correlation_id)
        self._write_state()

        if autostart_healers:
            self._register_default_healers()

    # -- public API ----------------------------------------------------------

    def probe(self, force: bool = False) -> SpirentHealth:
        """Return cached SpirentHealth or refresh if stale.

        Runs `spirent_tool.py status --json` under a 10s timeout.
        """
        if not force and self.health.is_fresh(self.probe_ttl_s):
            return self.health

        cmd = [self.python, str(self.tool_path), "status", "--json"]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
            data: Dict[str, Any] = {}
            if p.stdout:
                try:
                    data = json.loads(p.stdout)
                except (json.JSONDecodeError, ValueError):
                    data = {}
            sess = data.get("session", {}) or {}
            active = bool(sess.get("active"))
            port_reserved = bool(sess.get("port_reserved"))
            healthy = p.returncode == 0 and active and port_reserved
            self.health = SpirentHealth(
                ts=time.time(),
                healthy=healthy,
                active=active,
                port_reserved=port_reserved,
                raw=data,
            )
            self.state.last_probe_ts = self.health.ts
            self.state.port_reserved = port_reserved
            self.state.session_active = active
            self.state.state = "healthy" if healthy else "dead"
        except subprocess.TimeoutExpired:
            logger.warning("Spirent status probe timed out")
            self.health = SpirentHealth(ts=time.time(), healthy=False, raw={"error": "timeout"})
            self.state.state = "dead"
            self.state.last_error = "probe timeout"
        except FileNotFoundError as exc:
            logger.warning("Spirent tool not found: %s", exc)
            self.health = SpirentHealth(ts=time.time(), healthy=False, raw={"error": str(exc)})
            self.state.state = "dead"
            self.state.last_error = f"tool missing: {exc}"
        except Exception as exc:
            logger.warning("Spirent probe raised: %s", exc)
            self.health = SpirentHealth(ts=time.time(), healthy=False, raw={"error": str(exc)})
            self.state.state = "dead"
            self.state.last_error = str(exc)
        finally:
            self._write_state()
        return self.health

    def ensure_healthy(self, raise_if_dead: bool = True) -> bool:
        """Probe and, if dead, trigger FSM heal.

        Returns True when the session is healthy (or healed to healthy).
        Raises SpirentUnrecoverableError if raise_if_dead and healing fails.
        """
        health = self.probe()
        if health.healthy:
            return True
        return self._heal_with_fsm(raise_if_dead=raise_if_dead)

    def guarded_run(
        self,
        args: Sequence[str],
        timeout: int = 60,
        retries: Optional[int] = None,
        raise_on_error: bool = False,
        return_streams: bool = False,
        health_precheck: bool = True,
    ) -> SpirentCmdResult:
        """Invoke `spirent_tool.py *args` with automatic heal + retry.

        - If `health_precheck=True` (default), probe before the first call
          (cached, so repeated callers share the result).
        - On failure that matches dead-session signatures, ask the FSM to
          heal, then retry up to `max_retries` times.
        - If `raise_on_error`, raise SpirentUnrecoverableError when retries
          are exhausted.

        Returns SpirentCmdResult.
        """
        args = list(args)
        if not args:
            raise ValueError("guarded_run requires at least one arg")
        retries = retries if retries is not None else self.max_retries
        retries = max(1, retries)

        if health_precheck and args[0] not in _READONLY:
            try:
                self.ensure_healthy(raise_if_dead=False)
            except Exception:
                pass  # ensure_healthy already logs

        last: Optional[SpirentCmdResult] = None
        healed = False
        for attempt in range(1, retries + 1):
            res = self._invoke(args, timeout=timeout)
            last = res
            res.attempts = attempt
            res.healed = healed

            if res.ok:
                self.state.fail_count = 0
                self._write_state()
                return res

            if _is_dead_session_signature(res.combined):
                logger.warning(
                    "Spirent guarded_run[%d/%d]: dead-session signature detected (%s)",
                    attempt, retries, args[:2],
                )
                self.state.fail_count += 1
                self.state.last_error = res.combined[:400]
                self._write_state()
                try:
                    self._heal_with_fsm(raise_if_dead=(attempt == retries))
                    healed = True
                    continue
                except SpirentUnrecoverableError:
                    if raise_on_error:
                        raise
                    res.healed = False
                    return res

            # Not a dead-session error -- bubble up without healing.
            break

        if raise_on_error and last is not None and not last.ok:
            raise SpirentUnrecoverableError(
                f"spirent_tool.py {' '.join(args[:3])} failed after {last.attempts} attempts: "
                f"{last.combined[:400]}"
            )
        return last if last is not None else SpirentCmdResult(rc=-1, command=args)

    def snapshot(self) -> Dict[str, Any]:
        """Current watchdog status (for /SPIRENT status consumers)."""
        self.state.fsm_state = self.fsm.state.value
        d = self.state.to_dict()
        d["health"] = asdict(self.health)
        d["health"]["is_fresh"] = self.health.is_fresh(self.probe_ttl_s)
        return d

    # -- internal ------------------------------------------------------------

    def _invoke(self, args: List[str], timeout: int = 60) -> SpirentCmdResult:
        cmd = [self.python, str(self.tool_path)] + args
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return SpirentCmdResult(
                rc=p.returncode,
                stdout=p.stdout or "",
                stderr=p.stderr or "",
                combined=(p.stdout or "") + (p.stderr or ""),
                command=cmd,
            )
        except subprocess.TimeoutExpired:
            return SpirentCmdResult(
                rc=-1,
                stderr=f"TIMEOUT after {timeout}s: {' '.join(args[:3])}",
                combined=f"TIMEOUT after {timeout}s",
                command=cmd,
            )
        except FileNotFoundError as exc:
            return SpirentCmdResult(
                rc=-127,
                stderr=str(exc),
                combined=str(exc),
                command=cmd,
            )

    def _heal_with_fsm(self, raise_if_dead: bool = True) -> bool:
        """Drive the FSM through Spirent recovery. Returns True on STABLE."""
        self.state.state = "reconnecting"
        self._write_state()

        payload = {"spirent_tool_path": str(self.tool_path)}
        try:
            # Tell FSM the session is dead. Allow INIT too so the first ever
            # failure doesn't wedge the watchdog on a freshly-created FSM.
            if self.fsm.state in (RecoveryState.INIT, RecoveryState.STABLE):
                self.fsm.on_event(RecoveryEvent.SPIRENT_SESSION_DEAD, payload=payload)
            # If we're now DOWN, request heal.
            if self.fsm.state == RecoveryState.SPIRENT_DOWN:
                self.fsm.on_event(RecoveryEvent.HEALTH_OK, payload=payload)
        except UnrecoverableError as e:
            self.state.state = "dead"
            self.state.last_error = f"FSM unrecoverable: {e}"
            self._write_state()
            if raise_if_dead:
                raise SpirentUnrecoverableError(str(e)) from e
            return False

        healed = self.fsm.state == RecoveryState.STABLE
        if not healed:
            # FSM did not return to STABLE (e.g. stuck in DOWN because
            # caller disabled autostart_healers). Escalate.
            if raise_if_dead:
                raise SpirentUnrecoverableError(
                    f"FSM did not reach STABLE after heal; state={self.fsm.state.value}"
                )
        self.state.total_heals += 1
        self.state.last_heal_ts = time.time()
        self.state.last_heal_event = self.fsm.context.last_transition.event if self.fsm.context.last_transition else ""
        self.state.state = "healthy" if healed else "dead"
        self.state.fsm_state = self.fsm.state.value
        self._write_state()

        if healed:
            # Force a fresh probe so the new-session state is visible to callers.
            self.probe(force=True)
        return healed

    def _register_default_healers(self) -> None:
        """If FSM has no healer for Spirent states, register the defaults."""
        # We only register if not already set -- don't clobber recipe-specific healers.
        if RecoveryState.SPIRENT_HEAL_RECONNECT not in self.fsm._healers:  # noqa: SLF001
            self.fsm.register_healer(
                RecoveryState.SPIRENT_HEAL_RECONNECT,
                default_spirent_reconnect_healer,
            )
        if RecoveryState.SPIRENT_HEAL_LAB_SERVER not in self.fsm._healers:  # noqa: SLF001
            self.fsm.register_healer(
                RecoveryState.SPIRENT_HEAL_LAB_SERVER,
                default_spirent_lab_server_healer,
            )

    def _write_state(self) -> None:
        try:
            self.state.fsm_state = self.fsm.state.value
            WATCHDOG_STATE_PATH.write_text(json.dumps(self.snapshot(), indent=2, default=str))
            os.chmod(WATCHDOG_STATE_PATH, 0o644)
        except Exception:
            logger.exception("Failed to write watchdog state to %s", WATCHDOG_STATE_PATH)


# ---------------------------------------------------------------------------
# Module helpers
# ---------------------------------------------------------------------------

def _is_dead_session_signature(text: str) -> bool:
    if not text:
        return False
    return any(sig.lower() in text.lower() for sig in _DEAD_SESSION_SIGNATURES)


def _discover_tool_path() -> Path:
    """Find spirent_tool.py by convention."""
    env = os.environ.get("SPIRENT_TOOL_PATH")
    if env:
        p = Path(env)
        if p.exists():
            return p
    candidates = [
        Path.home() / "SCALER" / "SPIRENT" / "spirent_tool.py",
        Path("/home/dn/SCALER/SPIRENT/spirent_tool.py"),
        Path("/home/dn/drivenets-topology-studio/scaler/SPIRENT/spirent_tool.py"),
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        "Could not locate spirent_tool.py. Set $SPIRENT_TOOL_PATH or ensure it "
        "lives under ~/SCALER/SPIRENT/ or the drivenets-topology-studio/scaler/SPIRENT/."
    )


def read_watchdog_state() -> Optional[Dict[str, Any]]:
    """Public helper for /SPIRENT status consumers."""
    try:
        return json.loads(WATCHDOG_STATE_PATH.read_text())
    except Exception:
        return None


__all__ = [
    "SpirentCmdResult",
    "SpirentHealth",
    "SpirentUnrecoverableError",
    "SpirentWatchdog",
    "WATCHDOG_STATE_PATH",
    "WatchdogState",
    "read_watchdog_state",
]
