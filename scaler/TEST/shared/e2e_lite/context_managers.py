#!/usr/bin/env python3
"""
context_managers -- scope-bounded primitives for /TEST orchestrators.

A context manager pairs a reversible setup step with its cleanup so that
orchestrators get test isolation "for free" even when a scenario raises
halfway through. Each manager in this module is intentionally small: it
composes the Phase 1 + Phase 2 building blocks (``SpirentWatchdog``,
``RecoveryFsmLite``, ``SystemSnapshotter``, ``BaseAction``) instead of
duplicating their logic.

All managers are safe to enter inside an already-failing scenario: if the
setup call itself raises, __exit__ is never invoked and the exception
propagates cleanly; if the cleanup call raises while another exception is
already in flight, the original exception is preserved and the cleanup
error is logged at WARNING.

Context managers
----------------

``SpirentTrafficSection``
    Start Spirent traffic on entry, stop it on exit. Optionally captures
    pre/post stats into a supplied list for the verdict stage.

``SwitchoverSection``
    Record the active NCC on entry, run the switchover, wait for stability,
    and on exit assert that the active NCC has flipped. Captures a
    SystemSnapshot pair that the orchestrator can diff against
    ``test_config.snapshot_expected_changes``.

``ProcessRestartSection``
    Stop/restart a single DNOS process (e.g. ``routing:bgpd``) with automatic
    pre/post snapshots and a wait-for-healthy gate. Tracks retries through
    the shared FSM so the scenario_runner sees recoverable failures via the
    standard event stream.

``DutCliSection``
    Opens a persistent ``DNOSSession`` for the duration of the block. On
    exit, runs an optional list of cleanup commands AND always forces
    ``rollback 0`` + ``end`` as a safety net so test config never leaks.

Design notes
------------

* Setup is done in ``__enter__`` *after* entering the `with` block -- this
  means an exception raised in setup propagates to the caller (no cleanup
  runs, because the manager is not considered entered). This mirrors
  Python's documented context manager semantics.
* Every ``__exit__`` swallows cleanup exceptions only when another
  exception is already propagating (else they re-raise), logs them at
  WARNING, and records them on the manager's ``cleanup_errors`` list for
  the orchestrator to surface in the verdict.
* ``ProcessRestartSection`` and ``SwitchoverSection`` interact with the
  DUT through a caller-supplied ``run_show`` function (same contract as
  ``SystemSnapshotter``) so they stay testable without real SSH.
"""
from __future__ import annotations

import logging
import os
import time
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Type,
)

from .recovery_fsm_lite import RecoveryFsmLite
from .spirent_watchdog import (
    SpirentCmdResult,
    SpirentWatchdog,
)
from .system_snapshot import SnapshotDiff, SystemSnapshot, SystemSnapshotter

logger = logging.getLogger(__name__)

__all__ = [
    "ContextManagerError",
    "DutCliSection",
    "ProcessRestartSection",
    "SectionResult",
    "SpirentTrafficSection",
    "SwitchoverSection",
]


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

class ContextManagerError(RuntimeError):
    """Raised for fatal setup/cleanup failures inside a section."""


RunShowFn = Callable[[str, str], str]


@dataclass
class SectionResult:
    """Structured record a section produces for the verdict pipeline."""

    name: str
    entered: bool = False
    completed: bool = False
    duration_sec: float = 0.0
    errors: List[str] = field(default_factory=list)
    cleanup_errors: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)

    def add_cleanup_error(self, msg: str) -> None:
        self.cleanup_errors.append(msg)

    def summary(self) -> str:
        status = "OK" if self.completed and not self.errors else "FAIL"
        return (
            f"{self.name}[{status}] dur={self.duration_sec:.2f}s "
            f"errs={len(self.errors)} cleanup_errs={len(self.cleanup_errors)}"
        )


def _swallow_cleanup(
    result: SectionResult,
    label: str,
    fn: Callable[[], Any],
    *,
    exc_in_flight: bool,
) -> None:
    """Run ``fn`` as cleanup, recording errors on ``result``.

    * If no exception is in flight and cleanup raises, re-raise.
    * If an exception is in flight, swallow and log; the original will
      propagate out of __exit__.
    """
    try:
        fn()
    except Exception as exc:
        msg = f"{label}: {exc}"
        result.add_cleanup_error(msg)
        logger.warning("cleanup failed (%s)", msg)
        if not exc_in_flight:
            raise


class _SectionBase(AbstractContextManager):
    """Shared scaffolding for all sections -- timing, result capture, logging."""

    SECTION_NAME: str = "Section"

    def __init__(self) -> None:
        self.result = SectionResult(name=self.SECTION_NAME)
        self._t0: Optional[float] = None

    def _finalise_timing(self) -> None:
        if self._t0 is not None:
            self.result.duration_sec = time.time() - self._t0

    def __enter__(self) -> "_SectionBase":
        self._t0 = time.time()
        try:
            self._do_enter()
        except Exception as exc:
            self.result.add_error(str(exc))
            self._finalise_timing()
            raise
        self.result.entered = True
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[Any],
    ) -> Optional[bool]:
        try:
            self._do_exit(exc_type, exc, tb)
        finally:
            self._finalise_timing()
            self.result.completed = exc_type is None and not self.result.errors
        return False  # never swallow caller's exception

    def _do_enter(self) -> None:
        raise NotImplementedError

    def _do_exit(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[Any],
    ) -> None:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# SpirentTrafficSection
# ---------------------------------------------------------------------------

@dataclass
class SpirentTrafficStats:
    """Lightweight before/after wrapper for Spirent counters."""

    before: Dict[str, Any] = field(default_factory=dict)
    after: Dict[str, Any] = field(default_factory=dict)
    started_at: float = 0.0
    stopped_at: float = 0.0

    @property
    def duration_sec(self) -> float:
        if self.stopped_at and self.started_at:
            return max(0.0, self.stopped_at - self.started_at)
        return 0.0


class SpirentTrafficSection(_SectionBase):
    """Start Spirent traffic on entry, stop it on exit.

    Usage::

        with SpirentTrafficSection(watchdog, capture_stats=True) as sect:
            # run your scenario while traffic is running
            ...
        # traffic stopped here; sect.result.extra['stats'] has before/after

    Arguments:
        watchdog         -- SpirentWatchdog (drives all commands).
        extra_start_args -- additional argv for ``start`` (e.g. specific streams).
        capture_stats    -- Poll ``stats --json`` before start and after stop.
        stop_on_failure  -- When True (default), attempt ``stop`` even if
                            scenario raised; when False, skip stop on error
                            (useful for forensics).
        start_grace_sec  -- Sleep after start to let streams ramp (default 2s).
        probe_first      -- Call ``watchdog.ensure_healthy()`` before start.
    """

    SECTION_NAME = "SpirentTrafficSection"

    def __init__(
        self,
        watchdog: SpirentWatchdog,
        *,
        extra_start_args: Optional[Sequence[str]] = None,
        capture_stats: bool = True,
        stop_on_failure: bool = True,
        start_grace_sec: float = 2.0,
        probe_first: bool = True,
    ) -> None:
        super().__init__()
        self.watchdog = watchdog
        self.extra_start_args = list(extra_start_args or [])
        self.capture_stats = capture_stats
        self.stop_on_failure = stop_on_failure
        self.start_grace_sec = start_grace_sec
        self.probe_first = probe_first
        self.stats = SpirentTrafficStats()
        self.result.extra["stats"] = self.stats

    # -- public API ----------------------------------------------------------
    def poll_stats(self) -> Dict[str, Any]:
        """Ad-hoc stats snapshot while traffic is running."""
        return self._stats_snapshot()

    # -- protocol ------------------------------------------------------------
    def _do_enter(self) -> None:
        if self.probe_first:
            self.watchdog.ensure_healthy(raise_if_dead=True)
        if self.capture_stats:
            self.stats.before = self._stats_snapshot()
        self._run(["start", *self.extra_start_args])
        self.stats.started_at = time.time()
        if self.start_grace_sec > 0:
            time.sleep(self.start_grace_sec)

    def _do_exit(self, exc_type, exc, tb) -> None:
        exc_in_flight = exc is not None

        if exc_in_flight and not self.stop_on_failure:
            logger.info(
                "SpirentTrafficSection: scenario raised %s; skipping stop "
                "per stop_on_failure=False", exc_type.__name__ if exc_type else "?",
            )
            return

        def _stop() -> None:
            self._run(["stop"], raise_on_error=False)
            self.stats.stopped_at = time.time()
            if self.capture_stats:
                self.stats.after = self._stats_snapshot()

        _swallow_cleanup(
            self.result, "spirent stop", _stop, exc_in_flight=exc_in_flight,
        )

    # -- helpers -------------------------------------------------------------
    def _run(
        self,
        args: Sequence[str],
        *,
        raise_on_error: bool = True,
    ) -> SpirentCmdResult:
        res = self.watchdog.guarded_run(
            list(args),
            raise_on_error=raise_on_error,
        )
        return res

    def _stats_snapshot(self) -> Dict[str, Any]:
        res = self.watchdog.guarded_run(
            ["stats", "--json"], raise_on_error=False,
        )
        if not res.ok:
            return {"error": (res.stderr or "").strip()[:200] or "stats failed"}
        try:
            import json as _json
            return _json.loads(res.stdout) if res.stdout else {}
        except (ValueError, TypeError):
            return {"raw": (res.stdout or "")[:1000]}


# ---------------------------------------------------------------------------
# SwitchoverSection
# ---------------------------------------------------------------------------

SwitchoverFn = Callable[[], None]
"""Callable that executes the switchover. Kept abstract so the orchestrator
controls *how* the switchover happens (MCP `request system ncc switchover`,
SSH command, or DIY)."""


class SwitchoverSection(_SectionBase):
    """Surround an NCC switchover with pre/post snapshots and active-NCC assertion.

    Usage::

        with SwitchoverSection(
            device="PE-4", run_show=run_show,
            snapshotter=snapshotter, fsm=fsm,
            trigger=lambda: run_cli("request system ncc switchover"),
            wait_for_stable_sec=90,
        ) as sect:
            # caller can run extra probes here while waiting for recovery
            pass
        assert sect.result.completed
        diff = sect.diff  # available after exit if snapshotter given

    Arguments:
        device                 -- device identifier (for logging + snapshot label).
        run_show               -- run_show(device, cmd) -> str (same as SystemSnapshotter).
        trigger                -- zero-arg callable that actually issues the switchover.
        snapshotter            -- optional SystemSnapshotter for pre/post diffs.
        fsm                    -- optional RecoveryFsmLite to record events.
        active_ncc_cmd         -- show command that reveals the active NCC; default
                                  ``show system | include Active``.
        wait_for_stable_sec    -- how long to wait post-switchover for active NCC
                                  to re-appear (default 90s).
        poll_interval_sec      -- poll interval during the wait (default 5s).
        require_active_flip    -- when True (default), assert active NCC changed.
    """

    SECTION_NAME = "SwitchoverSection"

    def __init__(
        self,
        *,
        device: str,
        run_show: RunShowFn,
        trigger: SwitchoverFn,
        snapshotter: Optional[SystemSnapshotter] = None,
        fsm: Optional[RecoveryFsmLite] = None,
        active_ncc_cmd: str = "show system | include Active",
        wait_for_stable_sec: int = 90,
        poll_interval_sec: int = 5,
        require_active_flip: bool = True,
    ) -> None:
        super().__init__()
        self.device = device
        self.run_show = run_show
        self.trigger = trigger
        self.snapshotter = snapshotter
        self.fsm = fsm
        self.active_ncc_cmd = active_ncc_cmd
        self.wait_for_stable_sec = wait_for_stable_sec
        self.poll_interval_sec = max(1, int(poll_interval_sec))
        self.require_active_flip = require_active_flip

        self.snapshot_before: Optional[SystemSnapshot] = None
        self.snapshot_after: Optional[SystemSnapshot] = None
        self.diff: Optional[SnapshotDiff] = None
        self.active_ncc_before: Optional[str] = None
        self.active_ncc_after: Optional[str] = None

    # -- protocol ------------------------------------------------------------
    def _do_enter(self) -> None:
        self.active_ncc_before = self._probe_active_ncc()
        self.result.extra["active_ncc_before"] = self.active_ncc_before

        if self.snapshotter:
            self.snapshot_before = self.snapshotter.capture("pre_switchover")
            self.result.extra["snapshot_before"] = self.snapshot_before.label

        if self.fsm:
            self.fsm.record_heavy_op()
            logger.info("SwitchoverSection: triggering on %s", self.device)
        self.trigger()
        self._wait_for_stable()

    def _do_exit(self, exc_type, exc, tb) -> None:
        exc_in_flight = exc is not None

        def _finalise() -> None:
            self.active_ncc_after = self._probe_active_ncc()
            self.result.extra["active_ncc_after"] = self.active_ncc_after

            if self.snapshotter:
                self.snapshot_after = self.snapshotter.capture("post_switchover")
                self.result.extra["snapshot_after"] = self.snapshot_after.label
                # Diff with no expected rules; caller layers its own in the
                # verdict step. We expose the diff so the orchestrator can
                # re-run it against cfg.snapshot_expected_changes.
                self.diff = self.snapshotter.diff(
                    self.snapshot_before, self.snapshot_after,
                )

            if self.require_active_flip and not exc_in_flight:
                before = (self.active_ncc_before or "").strip()
                after = (self.active_ncc_after or "").strip()
                if before and after and before == after:
                    raise ContextManagerError(
                        f"{self.device}: NCC did not flip "
                        f"(before={before!r} after={after!r})"
                    )

        _swallow_cleanup(
            self.result, "switchover finalise", _finalise,
            exc_in_flight=exc_in_flight,
        )

    # -- helpers -------------------------------------------------------------
    def _probe_active_ncc(self) -> str:
        try:
            return (self.run_show(self.device, self.active_ncc_cmd) or "").strip()
        except Exception as exc:
            logger.warning("active-NCC probe failed: %s", exc)
            return ""

    def _wait_for_stable(self) -> None:
        deadline = time.time() + max(1, int(self.wait_for_stable_sec))
        while time.time() < deadline:
            time.sleep(self.poll_interval_sec)
            probe = self._probe_active_ncc()
            if probe:
                self.active_ncc_after = probe
                self.result.extra["active_ncc_probed_at"] = time.time()
                return
        logger.warning(
            "%s: switchover wait timed out after %ds",
            self.device, self.wait_for_stable_sec,
        )


# ---------------------------------------------------------------------------
# ProcessRestartSection
# ---------------------------------------------------------------------------

RestartFn = Callable[[str], None]
"""Callable that restarts a named process (e.g. 'routing:bgpd')."""


class ProcessRestartSection(_SectionBase):
    """Restart a DNOS process with pre/post snapshot + wait-for-healthy.

    Usage::

        with ProcessRestartSection(
            device="PE-4", run_show=run_show,
            snapshotter=snapshotter, process="routing:bgpd",
            restart_fn=lambda p: run_cli(f"request system process restart ncc 0 routing-engine {p}"),
            wait_for_healthy_sec=120,
        ) as sect:
            ...
    """

    SECTION_NAME = "ProcessRestartSection"

    def __init__(
        self,
        *,
        device: str,
        run_show: RunShowFn,
        snapshotter: Optional[SystemSnapshotter],
        process: str,
        restart_fn: RestartFn,
        fsm: Optional[RecoveryFsmLite] = None,
        wait_for_healthy_sec: int = 120,
        poll_interval_sec: int = 5,
        process_state_cmd: Optional[str] = None,
        healthy_substrings: Sequence[str] = ("running", "active", "up"),
    ) -> None:
        super().__init__()
        self.device = device
        self.run_show = run_show
        self.snapshotter = snapshotter
        self.process = process
        self.restart_fn = restart_fn
        self.fsm = fsm
        self.wait_for_healthy_sec = wait_for_healthy_sec
        self.poll_interval_sec = max(1, int(poll_interval_sec))
        self.process_state_cmd = (
            process_state_cmd or f"show system process {process}"
        )
        self.healthy_substrings = tuple(s.lower() for s in healthy_substrings)

        self.snapshot_before: Optional[SystemSnapshot] = None
        self.snapshot_after: Optional[SystemSnapshot] = None
        self.diff: Optional[SnapshotDiff] = None
        self.process_healthy: bool = False

    # -- protocol ------------------------------------------------------------
    def _do_enter(self) -> None:
        if self.snapshotter:
            self.snapshot_before = self.snapshotter.capture(
                f"pre_restart_{self.process}",
            )
        if self.fsm:
            self.fsm.record_heavy_op()
            logger.info(
                "ProcessRestartSection: restarting %s on %s",
                self.process,
                self.device,
            )
        self.restart_fn(self.process)

    def _do_exit(self, exc_type, exc, tb) -> None:
        exc_in_flight = exc is not None

        def _wait_and_snapshot() -> None:
            self.process_healthy = self._wait_for_process_healthy()
            self.result.extra["process_healthy"] = self.process_healthy

            if self.snapshotter:
                self.snapshot_after = self.snapshotter.capture(
                    f"post_restart_{self.process}",
                )
                self.diff = self.snapshotter.diff(
                    self.snapshot_before, self.snapshot_after,
                )

            if not exc_in_flight and not self.process_healthy:
                raise ContextManagerError(
                    f"{self.device}: process {self.process} did not return to "
                    f"healthy within {self.wait_for_healthy_sec}s"
                )

        _swallow_cleanup(
            self.result, "process wait/snapshot", _wait_and_snapshot,
            exc_in_flight=exc_in_flight,
        )

    # -- helpers -------------------------------------------------------------
    def _wait_for_process_healthy(self) -> bool:
        deadline = time.time() + max(1, int(self.wait_for_healthy_sec))
        while time.time() < deadline:
            try:
                output = (
                    self.run_show(self.device, self.process_state_cmd) or ""
                ).lower()
            except Exception as exc:
                logger.warning(
                    "process state probe failed: %s", exc,
                )
                output = ""
            if output and any(s in output for s in self.healthy_substrings):
                return True
            time.sleep(self.poll_interval_sec)
        return False


# ---------------------------------------------------------------------------
# DutCliSection
# ---------------------------------------------------------------------------

class DutCliSection(_SectionBase):
    """Persistent DUT CLI scope with guaranteed rollback.

    Opens a DNOSSession for the body of the ``with`` block and exposes it as
    ``section.session``. On exit, runs optional ``cleanup_commands`` (e.g.
    ``no network-services evpn instance TEST``), always followed by
    ``end`` -> ``config`` -> ``rollback 0`` -> ``end`` as a safety net so
    no test config ever leaks.

    Callers that don't have ``scaler.dnos_session`` available in their PYTHONPATH
    can pass ``session_factory`` to inject their own session builder -- useful
    for unit tests.
    """

    SECTION_NAME = "DutCliSection"

    def __init__(
        self,
        *,
        device: str,
        ip: str,
        username: str,
        password: str,
        cleanup_commands: Optional[Sequence[str]] = None,
        force_rollback: bool = True,
        session_factory: Optional[Callable[..., Any]] = None,
        session_kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__()
        self.device = device
        self.ip = ip
        self.username = username
        self.password = password
        self.cleanup_commands = list(cleanup_commands or [])
        self.force_rollback = force_rollback
        self.session_factory = session_factory
        self.session_kwargs = dict(session_kwargs or {})
        self.session: Any = None

    # -- protocol ------------------------------------------------------------
    def _do_enter(self) -> None:
        if self.session_factory is None:
            self.session_factory = self._default_session_factory
        self.session = self.session_factory(
            self.ip, self.username, self.password, **self.session_kwargs,
        )
        opener = getattr(self.session, "open", None) or getattr(
            self.session, "connect", None,
        )
        if opener is not None:
            opener()

    def _do_exit(self, exc_type, exc, tb) -> None:
        exc_in_flight = exc is not None

        def _cleanup() -> None:
            try:
                for cmd in self.cleanup_commands:
                    try:
                        self._send(cmd)
                    except Exception as inner:
                        logger.warning(
                            "cleanup command %r failed: %s", cmd, inner,
                        )
                        self.result.add_cleanup_error(
                            f"{cmd!r}: {inner}"
                        )

                if self.force_rollback:
                    try:
                        self._send("end")
                    except Exception:
                        pass
                    try:
                        self._send("config")
                        self._send("rollback 0")
                        self._send("end")
                    except Exception as rollback_exc:
                        logger.warning("rollback 0 best-effort: %s", rollback_exc)
                        self.result.add_cleanup_error(
                            f"rollback: {rollback_exc}"
                        )
            finally:
                closer = (
                    getattr(self.session, "close", None)
                    or getattr(self.session, "disconnect", None)
                )
                if closer is not None:
                    try:
                        closer()
                    except Exception as close_exc:
                        logger.warning("session close failed: %s", close_exc)
                        self.result.add_cleanup_error(f"close: {close_exc}")

        _swallow_cleanup(
            self.result, "dut cli cleanup", _cleanup, exc_in_flight=exc_in_flight,
        )

    # -- helpers -------------------------------------------------------------
    def _send(self, cmd: str) -> str:
        sender = (
            getattr(self.session, "send_command", None)
            or getattr(self.session, "run", None)
        )
        if sender is None:
            raise ContextManagerError(
                "DUT session object exposes neither send_command nor run"
            )
        return sender(cmd)

    @staticmethod
    def _default_session_factory(
        ip: str, username: str, password: str, **kwargs: Any,
    ) -> Any:
        try:
            from scaler.dnos_session import DNOSSession  # type: ignore
        except Exception as exc:  # pragma: no cover -- exercised in prod
            raise ContextManagerError(
                f"DNOSSession is not importable ({exc}); pass session_factory="
            )
        return DNOSSession(ip, username, password, **kwargs)


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _discover_spirent_tool_path() -> Path:
    """Return the default path to spirent_tool.py.

    Resolution order matches ``spirent_watchdog._find_default_tool`` on
    purpose: the canonical runtime copy at ``~/SCALER/SPIRENT/spirent_tool.py``
    must win over any checkout-relative path. Before this change we preferred
    ``here.parents[3] / "SPIRENT" / "spirent_tool.py"`` which, when the test
    harness ran from an in-tree worktree at
    ``/home/dn/drivenets-topology-studio/scaler/TEST/...``, resolved to the
    workspace copy of ``scaler/SPIRENT/spirent_tool.py``. That copy was
    frequently out of sync with ``~/SCALER/SPIRENT/`` (e.g. missed the
    ``cmd_start``/``cmd_stop --stream-name`` fix), so orchestrators running
    per-stream start/stop silently fell back to whole-port start/stop.

    ``SPIRENT_TOOL_PATH`` env override still wins unconditionally so CI and
    debug harnesses can pin an explicit copy.
    """
    env = os.environ.get("SPIRENT_TOOL_PATH")
    if env:
        p = Path(env).expanduser()
        if p.exists():
            return p
    here = Path(__file__).resolve()
    candidates = [
        Path.home() / "SCALER" / "SPIRENT" / "spirent_tool.py",
        Path("/home/dn/SCALER/SPIRENT/spirent_tool.py"),
        here.parents[3] / "SPIRENT" / "spirent_tool.py",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]
