#!/usr/bin/env python3
"""
core_dump_registry -- session-scoped background monitor for DNOS core dumps.

Why a registry (not a per-scenario check)
-----------------------------------------

Core dumps are the loudest possible failure signal but they often appear
*during* a scenario rather than before/after. A snapshot-only approach
(as in ``system_snapshot.py``) misses dumps that arrive between snapshots
or during a long wait. This module adds a lightweight background poller
that samples ``show system core-dumps`` every N seconds per device,
compares against a baseline captured at session start, and raises events
for every new dump it observes.

Design
------

* Strict session scope. The "baseline" is captured once at session start.
  Anything added after that is considered a new, session-scoped dump --
  even if it happens to be an old dump file that the OS rolled into the
  listing afterwards.
* Per-device run_show callable. The registry never owns SSH or FSM state.
  Each device is given a ``run_show(device, cmd) -> str`` just like
  ``SystemSnapshotter``, so unit tests can feed deterministic outputs.
* Non-blocking. A daemon thread drives the polling loop. The FSM is never
  called directly -- the registry only reports via callbacks, state file,
  and the summary API. Orchestrators decide how to act.
* Lock-protected state. Every mutation (baseline, observed, subscribers)
  goes through the internal mutex so subscribers can read consistent
  snapshots at any time.
* Idempotent and re-startable. Call ``start()`` / ``stop()`` as many times
  as needed; the final state is always recoverable from the JSON file.

Usage
-----

Context-manager form (preferred)::

    with CoreDumpSessionRegistry(
        devices=[("PE-4", run_show_pe4), ("PE-1", run_show_pe1)],
        poll_interval_sec=30,
    ) as registry:
        registry.subscribe(lambda evt: print("CORE!", evt))
        run_scenarios()
    # at block exit the registry is stopped, state is flushed to disk
    assert registry.new_cores_total() == 0

Manual form::

    registry = CoreDumpSessionRegistry(devices=[...])
    registry.capture_baseline()
    registry.start()
    try:
        run_scenarios()
    finally:
        registry.stop()

Events are dicts with: ``device``, ``dump_line``, ``observed_at`` (ISO),
and ``poll_index`` (0 = baseline, 1.. = periodic polls).
"""
from __future__ import annotations

import json
import logging
import tempfile
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

__all__ = [
    "CORE_DUMP_REGISTRY_STATE_PATH",
    "CoreDumpEvent",
    "CoreDumpRegistryError",
    "CoreDumpRegistrySummary",
    "CoreDumpSessionRegistry",
    "DeviceCoreState",
    "RunShowFn",
    "default_core_dump_commands",
]

CORE_DUMP_REGISTRY_STATE_PATH: Path = (
    Path(tempfile.gettempdir()) / "core_dump_registry.json"
)

RunShowFn = Callable[[str, str], str]


# ---------------------------------------------------------------------------
# DNOS commands that surface core dumps
# ---------------------------------------------------------------------------

def default_core_dump_commands() -> Tuple[str, ...]:
    """Return the list of show commands used to surface core dumps.

    The registry treats any line containing ``.core`` (e.g. ``bgpd.core.1234``)
    or ``core_dump`` as a dump. Callers can override this via the
    ``core_dump_commands`` constructor argument if their platform needs
    something different (e.g. ``show system file-system | include core``).
    """
    return (
        "show system core-dumps | no-more",
        "show system | include core",
    )


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CoreDumpEvent:
    """Single observed core-dump event."""

    device: str
    dump_line: str
    observed_at: str
    poll_index: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DeviceCoreState:
    """Per-device tracking state."""

    device: str
    baseline: List[str] = field(default_factory=list)
    observed: List[str] = field(default_factory=list)
    new_events: List[CoreDumpEvent] = field(default_factory=list)
    last_poll_ts: float = 0.0
    last_poll_error: str = ""
    poll_count: int = 0

    @property
    def new_count(self) -> int:
        return len(self.new_events)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device": self.device,
            "baseline": list(self.baseline),
            "observed": list(self.observed),
            "new_events": [e.to_dict() for e in self.new_events],
            "last_poll_ts": self.last_poll_ts,
            "last_poll_error": self.last_poll_error,
            "poll_count": self.poll_count,
            "new_count": self.new_count,
        }


@dataclass
class CoreDumpRegistrySummary:
    """Structured summary suitable for verdict consumers."""

    started_at: str
    stopped_at: str
    poll_interval_sec: float
    poll_count: int
    devices: List[DeviceCoreState] = field(default_factory=list)

    @property
    def new_cores_total(self) -> int:
        return sum(d.new_count for d in self.devices)

    @property
    def ok(self) -> bool:
        return self.new_cores_total == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "poll_interval_sec": self.poll_interval_sec,
            "poll_count": self.poll_count,
            "new_cores_total": self.new_cores_total,
            "ok": self.ok,
            "devices": [d.to_dict() for d in self.devices],
        }


class CoreDumpRegistryError(RuntimeError):
    """Raised for fatal registry lifecycle issues."""


# ---------------------------------------------------------------------------
# The registry
# ---------------------------------------------------------------------------

SubscriberFn = Callable[[CoreDumpEvent], None]


class CoreDumpSessionRegistry:
    """Session-scoped core-dump monitor with 30s-default polling.

    Arguments:
        devices             -- sequence of (device, run_show) pairs; each
                               device is polled independently.
        poll_interval_sec   -- how often to poll. 30s matches the Cheetah
                               E2E convention and is a good default for
                               DNOS filesystem scans.
        state_path          -- JSON file for persisted summary. Set to
                               ``None`` to disable disk writes (useful
                               in tests).
        core_dump_commands  -- override list of show commands.
        markers             -- case-insensitive substrings that identify a
                               core-dump line. Defaults to ``(".core",
                               "core_dump")``.
        thread_name         -- override the poller thread name.
        clock               -- ``time.time``-compatible callable (injected
                               for deterministic tests).
        sleep               -- ``time.sleep``-compatible callable.
        raise_if_started_twice -- when True, ``start()`` raises on a second
                               invocation; False = no-op.
    """

    _DEFAULT_MARKERS = (".core", "core_dump")

    def __init__(
        self,
        devices: Sequence[Tuple[str, RunShowFn]],
        *,
        poll_interval_sec: float = 30.0,
        state_path: Optional[Path] = CORE_DUMP_REGISTRY_STATE_PATH,
        core_dump_commands: Optional[Sequence[str]] = None,
        markers: Optional[Sequence[str]] = None,
        thread_name: str = "CoreDumpSessionRegistry",
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
        raise_if_started_twice: bool = False,
    ) -> None:
        if not devices:
            raise CoreDumpRegistryError(
                "CoreDumpSessionRegistry requires at least one device"
            )
        self._devices: Dict[str, RunShowFn] = {}
        for name, fn in devices:
            if not callable(fn):
                raise CoreDumpRegistryError(
                    f"run_show for {name} is not callable"
                )
            self._devices[name] = fn

        self.poll_interval_sec = max(1.0, float(poll_interval_sec))
        self.state_path = Path(state_path) if state_path else None
        self.core_dump_commands = tuple(
            core_dump_commands or default_core_dump_commands()
        )
        self.markers = tuple(
            m.lower() for m in (markers or self._DEFAULT_MARKERS)
        )
        self._thread_name = thread_name
        self._clock = clock
        self._sleep = sleep
        self._raise_if_started_twice = raise_if_started_twice

        self._states: Dict[str, DeviceCoreState] = {
            name: DeviceCoreState(device=name) for name in self._devices
        }
        self._subscribers: List[SubscriberFn] = []
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._baseline_captured = False
        self._started_at: Optional[str] = None
        self._stopped_at: Optional[str] = None
        self._poll_count_global: int = 0

    # -- lifecycle -----------------------------------------------------------

    def capture_baseline(self) -> Dict[str, List[str]]:
        """Snapshot each device's current dumps as the baseline.

        Everything *returned from a later poll that is not in this baseline*
        counts as a new, session-scoped dump. Called implicitly by
        ``start()`` unless the caller already invoked it.
        """
        snap: Dict[str, List[str]] = {}
        with self._lock:
            for name, run_show in self._devices.items():
                dumps = self._sample_one(name, run_show)
                self._states[name].baseline = list(dumps)
                self._states[name].observed = list(dumps)
                snap[name] = list(dumps)
            self._baseline_captured = True
            self._started_at = self._now_iso()
        logger.info(
            "CoreDumpSessionRegistry: baseline captured for %d devices, "
            "dumps per device: %s",
            len(snap), {k: len(v) for k, v in snap.items()},
        )
        self._persist()
        return snap

    def start(self) -> None:
        """Kick off the background polling thread (daemon)."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                if self._raise_if_started_twice:
                    raise CoreDumpRegistryError("registry already started")
                logger.debug("registry already running -- ignoring start()")
                return
            if not self._baseline_captured:
                self.capture_baseline()
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run, name=self._thread_name, daemon=True,
            )
            self._thread.start()
        logger.info(
            "CoreDumpSessionRegistry: poller started (interval=%.1fs)",
            self.poll_interval_sec,
        )

    def stop(self, timeout_sec: float = 10.0) -> None:
        """Signal the poller to stop and block until it exits."""
        self._stop_event.set()
        t = self._thread
        if t is not None and t.is_alive():
            t.join(timeout=max(0.1, float(timeout_sec)))
            if t.is_alive():
                logger.warning(
                    "CoreDumpSessionRegistry: poller did not stop within %ss",
                    timeout_sec,
                )
        with self._lock:
            self._thread = None
            if self._stopped_at is None:
                self._stopped_at = self._now_iso()
        self._persist()
        logger.info("CoreDumpSessionRegistry: stopped (poll_count=%d)",
                    self._poll_count_global)

    # -- context manager protocol -------------------------------------------

    def __enter__(self) -> "CoreDumpSessionRegistry":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    # -- subscribers ---------------------------------------------------------

    def subscribe(self, fn: SubscriberFn) -> None:
        """Register a callback invoked on every new core dump.

        Callbacks run on the poller thread. Keep them fast; defer expensive
        work via a queue if needed.
        """
        if not callable(fn):
            raise CoreDumpRegistryError("subscriber is not callable")
        with self._lock:
            if fn not in self._subscribers:
                self._subscribers.append(fn)

    def unsubscribe(self, fn: SubscriberFn) -> None:
        with self._lock:
            if fn in self._subscribers:
                self._subscribers.remove(fn)

    # -- queries -------------------------------------------------------------

    def snapshot(self, device: Optional[str] = None) -> Dict[str, Any]:
        """Read-only view of current state (one device or all)."""
        with self._lock:
            if device is not None:
                if device not in self._states:
                    raise CoreDumpRegistryError(
                        f"unknown device {device!r}"
                    )
                return self._states[device].to_dict()
            return {name: st.to_dict() for name, st in self._states.items()}

    def new_cores_total(self) -> int:
        with self._lock:
            return sum(st.new_count for st in self._states.values())

    def new_events(
        self, device: Optional[str] = None,
    ) -> List[CoreDumpEvent]:
        with self._lock:
            if device is not None:
                if device not in self._states:
                    return []
                return list(self._states[device].new_events)
            all_events: List[CoreDumpEvent] = []
            for st in self._states.values():
                all_events.extend(st.new_events)
            return all_events

    def summary(self) -> CoreDumpRegistrySummary:
        with self._lock:
            return CoreDumpRegistrySummary(
                started_at=self._started_at or "",
                stopped_at=self._stopped_at or "",
                poll_interval_sec=self.poll_interval_sec,
                poll_count=self._poll_count_global,
                devices=[
                    DeviceCoreState(
                        device=st.device,
                        baseline=list(st.baseline),
                        observed=list(st.observed),
                        new_events=list(st.new_events),
                        last_poll_ts=st.last_poll_ts,
                        last_poll_error=st.last_poll_error,
                        poll_count=st.poll_count,
                    )
                    for st in self._states.values()
                ],
            )

    # -- test helpers --------------------------------------------------------

    def poll_once(self) -> int:
        """Run a single poll iteration synchronously (for tests)."""
        with self._lock:
            if not self._baseline_captured:
                self.capture_baseline()
        return self._poll_cycle()

    # -- internals -----------------------------------------------------------

    def _run(self) -> None:
        logger.debug("CoreDumpSessionRegistry: poller thread started")
        try:
            while not self._stop_event.is_set():
                try:
                    self._poll_cycle()
                except Exception as exc:  # noqa: BLE001 -- daemon must not die
                    logger.exception(
                        "CoreDumpSessionRegistry poll cycle failed: %s", exc,
                    )
                # interruptible sleep
                self._stop_event.wait(self.poll_interval_sec)
        finally:
            logger.debug("CoreDumpSessionRegistry: poller thread exiting")

    def _poll_cycle(self) -> int:
        """Return the number of new events discovered this cycle."""
        new_total = 0
        with self._lock:
            self._poll_count_global += 1
            cycle_idx = self._poll_count_global
            devices = list(self._devices.items())

        for name, run_show in devices:
            try:
                dumps = self._sample_one(name, run_show)
            except Exception as exc:  # noqa: BLE001 -- isolate per device
                with self._lock:
                    self._states[name].last_poll_error = str(exc)[:200]
                    self._states[name].poll_count += 1
                logger.warning(
                    "CoreDumpSessionRegistry: sampling %s failed: %s",
                    name, exc,
                )
                continue

            new_lines: List[str] = []
            with self._lock:
                st = self._states[name]
                existing = set(st.observed)
                for line in dumps:
                    if line not in existing:
                        new_lines.append(line)
                        st.observed.append(line)
                for line in new_lines:
                    if line in st.baseline:
                        continue
                    evt = CoreDumpEvent(
                        device=name,
                        dump_line=line,
                        observed_at=self._now_iso(),
                        poll_index=cycle_idx,
                    )
                    st.new_events.append(evt)
                    new_total += 1
                    self._notify(evt)
                st.last_poll_ts = self._clock()
                st.last_poll_error = ""
                st.poll_count += 1

        if new_total > 0:
            logger.warning(
                "CoreDumpSessionRegistry: %d new core dump(s) observed "
                "this cycle (total new = %d)",
                new_total, self.new_cores_total(),
            )
        self._persist()
        return new_total

    def _sample_one(self, device: str, run_show: RunShowFn) -> List[str]:
        """Return the list of dump lines currently visible on ``device``."""
        collected: List[str] = []
        for cmd in self.core_dump_commands:
            try:
                out = run_show(device, cmd) or ""
            except Exception as exc:
                logger.debug("core-dump probe %r on %s raised: %s",
                             cmd, device, exc)
                continue
            for raw in out.splitlines():
                line = raw.strip()
                if not line:
                    continue
                low = line.lower()
                if any(m in low for m in self.markers):
                    collected.append(line)
        seen: Dict[str, None] = {}
        for l in collected:
            seen.setdefault(l, None)
        return list(seen.keys())

    def _notify(self, event: CoreDumpEvent) -> None:
        for sub in list(self._subscribers):
            try:
                sub(event)
            except Exception as exc:  # noqa: BLE001 -- subscriber isolation
                logger.warning(
                    "CoreDumpSessionRegistry subscriber failed: %s", exc,
                )

    def _persist(self) -> None:
        if self.state_path is None:
            return
        try:
            summary = self.summary().to_dict()
            summary["updated_at"] = self._now_iso()
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.state_path.with_suffix(
                self.state_path.suffix + ".tmp"
            )
            tmp.write_text(json.dumps(summary, indent=2))
            tmp.replace(self.state_path)
        except Exception as exc:  # noqa: BLE001 -- never break polling
            logger.warning(
                "CoreDumpSessionRegistry: state persistence failed: %s", exc,
            )

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds")
