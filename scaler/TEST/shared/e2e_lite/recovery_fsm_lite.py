#!/usr/bin/env python3
"""
RecoveryFSM-lite -- event-driven recovery FSM for /TEST + /SPIRENT.

A trimmed version of cheetah's E2E RecoveryFSM (2,696 LOC, ~30 states) that
covers the failures we actually hit in the lab:

  * DUT SSH drop / CLI hang (e.g. after bgpd restart or NCC switchover)
  * Spirent Lab Server hiccup / session 404 / port lost
  * Prerequisite failure mid-scenario
  * Scenario failure (AUTOMATION class vs PRODUCT_BUG class)

11 states, 2 healing ladders, hard guards (max retries, max heavy ops, budget).

Integration:
    fsm = RecoveryFsmLite(guards=RecoveryGuards(max_scenario_retries=2))
    fsm.register_healer(RecoveryState.DUT_SSH_HEALING, _heal_dut_ssh)
    fsm.register_healer(RecoveryState.SPIRENT_HEAL_RECONNECT, _heal_spirent)
    ...
    try:
        fsm.on_event(RecoveryEvent.SPIRENT_SESSION_DEAD, context={"device": "PE-4"})
        # FSM drives itself to Stable or raises UnrecoverableError
    except UnrecoverableError as e:
        # scenario_runner deals with abort
        ...

States persist to /tmp/e2e_lite_fsm.json so /SPIRENT and /TEST can read
the current state without coupling.
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
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

FSM_STATE_PATH = Path(tempfile.gettempdir()) / "e2e_lite_fsm.json"


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class RecoveryState(str, Enum):
    """All 11 states of the lite FSM."""

    INIT = "Init"
    STABLE = "Stable"
    UNRECOVERABLE = "Unrecoverable"

    DUT_SSH_DOWN = "DutSshDown"
    DUT_SSH_HEALING = "DutSshHealing"
    DUT_CLI_UNRESPONSIVE = "DutCliUnresponsive"

    SPIRENT_DOWN = "SpirentDown"
    SPIRENT_HEAL_RECONNECT = "SpirentHealReconnect"
    SPIRENT_HEAL_LAB_SERVER = "SpirentHealLabServer"

    PREREQ_FAILED = "PrereqFailed"
    SCENARIO_FAILED = "ScenarioFailed"


class RecoveryEvent(str, Enum):
    """Events that drive transitions."""

    HEALTH_OK = "health_ok"

    SSH_FAIL = "ssh_fail"
    SSH_UP_CLI_HANG = "ssh_up_cli_hang"
    SSH_HEAL_OK = "ssh_heal_ok"

    SPIRENT_SESSION_DEAD = "spirent_session_dead"
    SPIRENT_CONNECT_OK = "spirent_connect_ok"
    SPIRENT_RECONNECT_FAIL = "spirent_reconnect_fail"
    SPIRENT_LAB_SERVER_OK = "spirent_lab_server_ok"
    SPIRENT_ESCALATE = "spirent_escalate"   # emitted by guard when max reconnects hit

    PREREQ_FAIL = "prereq_fail"
    PREREQ_FIXED = "prereq_fixed"
    PREREQ_UNFIXABLE = "prereq_unfixable"

    SCENARIO_FAIL_AUTOMATION = "scenario_fail_automation"
    SCENARIO_FAIL_PRODUCT_BUG = "scenario_fail_product_bug"
    PRODUCT_BUG_ACCEPTED = "product_bug_accepted"

    MAX_RETRIES = "max_retries"
    MAX_HEAVY_OPS = "max_heavy_ops"
    BUDGET_EXHAUSTED = "budget_exhausted"

    RESET_TO_INIT = "reset_to_init"


class FailureClass(str, Enum):
    """Used by scenario_runner to classify test failures."""

    AUTOMATION = "AUTOMATION"          # infra (SSH, Spirent, timeout) -> heal+retry
    PRODUCT_BUG = "PRODUCT_BUG"        # DNOS bug -> pause, ask user
    UNKNOWN = "UNKNOWN"                # treat as AUTOMATION by default


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class RecoveryGuards:
    """Bound what the FSM is allowed to do. Prevents livelock."""

    max_ssh_retries: int = 5
    max_spirent_reconnects: int = 3
    max_scenario_retries: int = 2            # per scenario, not per suite
    max_heavy_ops_per_session: int = 1       # reboots / Lab Server docker restarts
    hard_timeout_sec: int = 900              # 15 min total recovery budget
    ssh_backoff_sec: int = 5                 # starting backoff for SSH retries
    spirent_backoff_sec: int = 5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RecoveryTransition:
    """One transition record for audit and debugging."""

    timestamp: str
    from_state: str
    to_state: str
    event: str
    note: str = ""
    correlation_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RecoveryContext:
    """Runtime counters and metadata, separate from state."""

    started_at: float = field(default_factory=time.time)
    ssh_retry_count: int = 0
    spirent_reconnect_count: int = 0
    heavy_ops_used: int = 0
    scenario_retries: Dict[str, int] = field(default_factory=dict)
    last_transition: Optional[RecoveryTransition] = None
    transitions: List[RecoveryTransition] = field(default_factory=list)
    correlation_id: str = ""

    @property
    def elapsed_sec(self) -> float:
        return time.time() - self.started_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "started_at": self.started_at,
            "elapsed_sec": round(self.elapsed_sec, 2),
            "ssh_retry_count": self.ssh_retry_count,
            "spirent_reconnect_count": self.spirent_reconnect_count,
            "heavy_ops_used": self.heavy_ops_used,
            "scenario_retries": dict(self.scenario_retries),
            "correlation_id": self.correlation_id,
            "last_transition": (
                self.last_transition.to_dict() if self.last_transition else None
            ),
            "transitions_count": len(self.transitions),
        }


class UnrecoverableError(Exception):
    """Raised when FSM reaches UNRECOVERABLE. Suite should abort."""

    def __init__(self, message: str, state: RecoveryState, context: RecoveryContext) -> None:
        super().__init__(message)
        self.state = state
        self.context = context


# ---------------------------------------------------------------------------
# Transition table
# ---------------------------------------------------------------------------

# (from_state, event) -> to_state
# Guards are checked separately in on_event(). This table is declarative.
_TRANSITIONS: Dict[Tuple[RecoveryState, RecoveryEvent], RecoveryState] = {
    # From INIT
    (RecoveryState.INIT, RecoveryEvent.HEALTH_OK): RecoveryState.STABLE,
    (RecoveryState.INIT, RecoveryEvent.SSH_FAIL): RecoveryState.DUT_SSH_DOWN,
    (RecoveryState.INIT, RecoveryEvent.SPIRENT_SESSION_DEAD): RecoveryState.SPIRENT_DOWN,
    (RecoveryState.INIT, RecoveryEvent.PREREQ_FAIL): RecoveryState.PREREQ_FAILED,

    # From STABLE
    (RecoveryState.STABLE, RecoveryEvent.SSH_FAIL): RecoveryState.DUT_SSH_DOWN,
    (RecoveryState.STABLE, RecoveryEvent.SPIRENT_SESSION_DEAD): RecoveryState.SPIRENT_DOWN,
    (RecoveryState.STABLE, RecoveryEvent.PREREQ_FAIL): RecoveryState.PREREQ_FAILED,
    (RecoveryState.STABLE, RecoveryEvent.SCENARIO_FAIL_AUTOMATION): RecoveryState.SCENARIO_FAILED,
    (RecoveryState.STABLE, RecoveryEvent.SCENARIO_FAIL_PRODUCT_BUG): RecoveryState.SCENARIO_FAILED,
    (RecoveryState.STABLE, RecoveryEvent.RESET_TO_INIT): RecoveryState.INIT,

    # DUT ladder
    (RecoveryState.DUT_SSH_DOWN, RecoveryEvent.HEALTH_OK): RecoveryState.DUT_SSH_HEALING,
    (RecoveryState.DUT_SSH_DOWN, RecoveryEvent.MAX_RETRIES): RecoveryState.UNRECOVERABLE,

    (RecoveryState.DUT_SSH_HEALING, RecoveryEvent.SSH_HEAL_OK): RecoveryState.STABLE,
    (RecoveryState.DUT_SSH_HEALING, RecoveryEvent.SSH_UP_CLI_HANG): RecoveryState.DUT_CLI_UNRESPONSIVE,
    # Self-loop: on SSH_FAIL, re-fire healer until retries exhausted (then MAX_RETRIES).
    (RecoveryState.DUT_SSH_HEALING, RecoveryEvent.SSH_FAIL): RecoveryState.DUT_SSH_HEALING,
    (RecoveryState.DUT_SSH_HEALING, RecoveryEvent.MAX_RETRIES): RecoveryState.UNRECOVERABLE,

    (RecoveryState.DUT_CLI_UNRESPONSIVE, RecoveryEvent.SSH_FAIL): RecoveryState.DUT_SSH_DOWN,
    (RecoveryState.DUT_CLI_UNRESPONSIVE, RecoveryEvent.SSH_HEAL_OK): RecoveryState.STABLE,
    (RecoveryState.DUT_CLI_UNRESPONSIVE, RecoveryEvent.MAX_RETRIES): RecoveryState.UNRECOVERABLE,

    # Spirent ladder
    (RecoveryState.SPIRENT_DOWN, RecoveryEvent.HEALTH_OK): RecoveryState.SPIRENT_HEAL_RECONNECT,
    (RecoveryState.SPIRENT_DOWN, RecoveryEvent.MAX_RETRIES): RecoveryState.UNRECOVERABLE,

    (RecoveryState.SPIRENT_HEAL_RECONNECT, RecoveryEvent.SPIRENT_CONNECT_OK): RecoveryState.STABLE,
    # Self-loop: retry reconnects until max hit; then guard upgrades to SPIRENT_ESCALATE.
    (RecoveryState.SPIRENT_HEAL_RECONNECT, RecoveryEvent.SPIRENT_RECONNECT_FAIL): RecoveryState.SPIRENT_HEAL_RECONNECT,
    (RecoveryState.SPIRENT_HEAL_RECONNECT, RecoveryEvent.SPIRENT_ESCALATE): RecoveryState.SPIRENT_HEAL_LAB_SERVER,
    (RecoveryState.SPIRENT_HEAL_RECONNECT, RecoveryEvent.MAX_RETRIES): RecoveryState.UNRECOVERABLE,

    (RecoveryState.SPIRENT_HEAL_LAB_SERVER, RecoveryEvent.SPIRENT_LAB_SERVER_OK): RecoveryState.STABLE,
    (RecoveryState.SPIRENT_HEAL_LAB_SERVER, RecoveryEvent.MAX_HEAVY_OPS): RecoveryState.UNRECOVERABLE,
    (RecoveryState.SPIRENT_HEAL_LAB_SERVER, RecoveryEvent.SPIRENT_RECONNECT_FAIL): RecoveryState.UNRECOVERABLE,

    # Prerequisite ladder
    (RecoveryState.PREREQ_FAILED, RecoveryEvent.PREREQ_FIXED): RecoveryState.STABLE,
    (RecoveryState.PREREQ_FAILED, RecoveryEvent.PREREQ_UNFIXABLE): RecoveryState.UNRECOVERABLE,
    (RecoveryState.PREREQ_FAILED, RecoveryEvent.SSH_FAIL): RecoveryState.DUT_SSH_DOWN,
    (RecoveryState.PREREQ_FAILED, RecoveryEvent.SPIRENT_SESSION_DEAD): RecoveryState.SPIRENT_DOWN,

    # Scenario ladder
    (RecoveryState.SCENARIO_FAILED, RecoveryEvent.SCENARIO_FAIL_AUTOMATION): RecoveryState.PREREQ_FAILED,
    (RecoveryState.SCENARIO_FAILED, RecoveryEvent.PRODUCT_BUG_ACCEPTED): RecoveryState.STABLE,
    (RecoveryState.SCENARIO_FAILED, RecoveryEvent.MAX_RETRIES): RecoveryState.UNRECOVERABLE,

    # Budget exhaustion from anywhere
    (RecoveryState.DUT_SSH_DOWN, RecoveryEvent.BUDGET_EXHAUSTED): RecoveryState.UNRECOVERABLE,
    (RecoveryState.DUT_SSH_HEALING, RecoveryEvent.BUDGET_EXHAUSTED): RecoveryState.UNRECOVERABLE,
    (RecoveryState.SPIRENT_DOWN, RecoveryEvent.BUDGET_EXHAUSTED): RecoveryState.UNRECOVERABLE,
    (RecoveryState.SPIRENT_HEAL_RECONNECT, RecoveryEvent.BUDGET_EXHAUSTED): RecoveryState.UNRECOVERABLE,
    (RecoveryState.SPIRENT_HEAL_LAB_SERVER, RecoveryEvent.BUDGET_EXHAUSTED): RecoveryState.UNRECOVERABLE,
    (RecoveryState.PREREQ_FAILED, RecoveryEvent.BUDGET_EXHAUSTED): RecoveryState.UNRECOVERABLE,
    (RecoveryState.SCENARIO_FAILED, RecoveryEvent.BUDGET_EXHAUSTED): RecoveryState.UNRECOVERABLE,
}


HEALING_STATES = {
    RecoveryState.DUT_SSH_HEALING,
    RecoveryState.SPIRENT_HEAL_RECONNECT,
    RecoveryState.SPIRENT_HEAL_LAB_SERVER,
    RecoveryState.PREREQ_FAILED,
}

# These states spend one of the limited heavy ops when entered.
HEAVY_OP_STATES = {
    RecoveryState.SPIRENT_HEAL_LAB_SERVER,
}


# ---------------------------------------------------------------------------
# FSM
# ---------------------------------------------------------------------------

HealerFn = Callable[["RecoveryFsmLite", Dict[str, Any]], RecoveryEvent]


class RecoveryFsmLite:
    """Event-driven FSM with registered healers per healing state.

    Usage pattern:
        fsm = RecoveryFsmLite(guards=RecoveryGuards())
        fsm.register_healer(RecoveryState.DUT_SSH_HEALING, heal_dut_ssh_fn)
        fsm.register_healer(RecoveryState.SPIRENT_HEAL_RECONNECT, heal_spirent_fn)
        fsm.register_healer(RecoveryState.SPIRENT_HEAL_LAB_SERVER, recover_lab_server_fn)
        fsm.register_healer(RecoveryState.PREREQ_FAILED, fix_prereq_fn)

        # Drive with events
        fsm.on_event(RecoveryEvent.SPIRENT_SESSION_DEAD, {"device": "PE-4"})
        # FSM transitions through healing states, invoking healers, until it
        # lands on STABLE (success) or raises UnrecoverableError.
    """

    def __init__(
        self,
        guards: Optional[RecoveryGuards] = None,
        correlation_id: str = "",
        persist: bool = True,
        initial_state: RecoveryState = RecoveryState.INIT,
    ) -> None:
        self.guards = guards or RecoveryGuards()
        self.state: RecoveryState = initial_state
        self.context = RecoveryContext(correlation_id=correlation_id or _gen_correlation_id())
        self._healers: Dict[RecoveryState, HealerFn] = {}
        self._listeners: List[Callable[[RecoveryTransition], None]] = []
        self._persist = persist
        self._write_state()

    # -- registration --------------------------------------------------------

    def register_healer(self, state: RecoveryState, fn: HealerFn) -> None:
        """Register a healer callback for a HEALING state.

        The callback receives (fsm, payload) and must return a RecoveryEvent
        that drives the next transition. It should NOT call on_event itself.
        """
        if state not in HEALING_STATES:
            raise ValueError(f"{state} is not a healing state; cannot register healer")
        self._healers[state] = fn

    def on_transition(self, listener: Callable[[RecoveryTransition], None]) -> None:
        """Register a listener that fires after every transition."""
        self._listeners.append(listener)

    # -- driving -------------------------------------------------------------

    def on_event(
        self,
        event: RecoveryEvent,
        payload: Optional[Dict[str, Any]] = None,
        note: str = "",
    ) -> RecoveryState:
        """Apply an event. If transition enters a healing state, the healer is
        invoked automatically and its returned event is chained recursively.

        Returns the final state reached (STABLE, or raises UnrecoverableError).
        """
        payload = payload or {}

        if self.context.elapsed_sec > self.guards.hard_timeout_sec:
            logger.warning(
                "RecoveryFSM-lite budget exhausted after %.1fs (guard=%ds)",
                self.context.elapsed_sec, self.guards.hard_timeout_sec,
            )
            self._transition(RecoveryEvent.BUDGET_EXHAUSTED, note="hard_timeout_reached")

        # Guard checks first -- may upgrade the event to MAX_RETRIES / MAX_HEAVY_OPS.
        event = self._apply_guards(event)

        next_state = _TRANSITIONS.get((self.state, event))
        if next_state is None:
            logger.debug(
                "RecoveryFSM-lite: no transition for (%s, %s); staying",
                self.state.value, event.value,
            )
            return self.state

        # Heavy-op gate: if the transition would enter a HEAVY_OP_STATE and the
        # budget is already spent, redirect to UNRECOVERABLE instead of entering
        # and spending another heavy op we don't have.
        if (
            next_state in HEAVY_OP_STATES
            and next_state != self.state
            and self.context.heavy_ops_used >= self.guards.max_heavy_ops_per_session
        ):
            logger.warning(
                "RecoveryFSM-lite: heavy-op budget already spent (%d/%d); "
                "refusing to enter %s -> Unrecoverable",
                self.context.heavy_ops_used,
                self.guards.max_heavy_ops_per_session,
                next_state.value,
            )
            event = RecoveryEvent.MAX_HEAVY_OPS
            next_state = RecoveryState.UNRECOVERABLE

        self._transition(event, note=note, next_state=next_state)

        if self.state == RecoveryState.UNRECOVERABLE:
            raise UnrecoverableError(
                f"FSM reached UNRECOVERABLE via {event.value}",
                state=self.state,
                context=self.context,
            )

        # If we entered a healing state, fire the healer.
        if self.state in HEALING_STATES and self.state in self._healers:
            healer = self._healers[self.state]
            logger.info(
                "RecoveryFSM-lite: invoking healer for %s", self.state.value,
            )
            try:
                next_event = healer(self, payload)
            except Exception as exc:  # healer crashed
                logger.exception("Healer for %s crashed: %s", self.state.value, exc)
                next_event = _failure_event_for(self.state)

            # Chain the healer's outcome event.
            return self.on_event(next_event, payload=payload, note=f"from_{self.state.value}_healer")

        return self.state

    # -- helpers for healers -------------------------------------------------

    def record_ssh_retry(self) -> None:
        self.context.ssh_retry_count += 1

    def record_spirent_reconnect(self) -> None:
        self.context.spirent_reconnect_count += 1

    def record_heavy_op(self) -> None:
        self.context.heavy_ops_used += 1

    def record_scenario_retry(self, scenario_id: str) -> None:
        self.context.scenario_retries[scenario_id] = (
            self.context.scenario_retries.get(scenario_id, 0) + 1
        )

    def scenario_retry_count(self, scenario_id: str) -> int:
        return self.context.scenario_retries.get(scenario_id, 0)

    def reset_transient(self) -> None:
        """Called when a suite retry fully succeeds; reset transient counters."""
        self.context.ssh_retry_count = 0
        self.context.spirent_reconnect_count = 0

    # -- status / snapshot ---------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        """Full state snapshot for persistence and /SPIRENT status."""
        return {
            "state": self.state.value,
            "guards": self.guards.to_dict(),
            "context": self.context.to_dict(),
            "updated_at": _iso_now(),
            "healers_registered": sorted(s.value for s in self._healers.keys()),
        }

    def read_persisted(self) -> Optional[Dict[str, Any]]:
        """Read the last persisted state (for external tools)."""
        try:
            return json.loads(FSM_STATE_PATH.read_text())
        except Exception:
            return None

    # -- internal ------------------------------------------------------------

    def _apply_guards(self, event: RecoveryEvent) -> RecoveryEvent:
        """Translate bare events to guard-triggered escalations when needed."""
        # SSH retry ladder: escalate to MAX_RETRIES once budget is exhausted.
        if event == RecoveryEvent.SSH_FAIL:
            if self.context.ssh_retry_count >= self.guards.max_ssh_retries:
                logger.warning(
                    "RecoveryFSM-lite: max SSH retries (%d) hit; escalating to MAX_RETRIES",
                    self.guards.max_ssh_retries,
                )
                return RecoveryEvent.MAX_RETRIES

        # Spirent reconnect ladder: when in SPIRENT_HEAL_RECONNECT and the reconnect
        # budget is spent, escalate to SPIRENT_ESCALATE -> SPIRENT_HEAL_LAB_SERVER.
        # The heavy-op gate (in on_event) blocks that transition if heavy-op budget
        # is also spent.
        if (
            event == RecoveryEvent.SPIRENT_RECONNECT_FAIL
            and self.state == RecoveryState.SPIRENT_HEAL_RECONNECT
            and self.context.spirent_reconnect_count >= self.guards.max_spirent_reconnects
        ):
            logger.warning(
                "RecoveryFSM-lite: max Spirent reconnects (%d) hit; escalating",
                self.guards.max_spirent_reconnects,
            )
            return RecoveryEvent.SPIRENT_ESCALATE

        return event

    def _transition(
        self,
        event: RecoveryEvent,
        note: str = "",
        next_state: Optional[RecoveryState] = None,
    ) -> None:
        if next_state is None:
            next_state = _TRANSITIONS.get((self.state, event), self.state)
        prev = self.state
        self.state = next_state

        # Spend a heavy op on entering a heavy state.
        if next_state in HEAVY_OP_STATES and prev != next_state:
            self.record_heavy_op()

        transition = RecoveryTransition(
            timestamp=_iso_now(),
            from_state=prev.value,
            to_state=next_state.value,
            event=event.value,
            note=note,
            correlation_id=self.context.correlation_id,
        )
        self.context.last_transition = transition
        self.context.transitions.append(transition)
        logger.info(
            "RecoveryFSM-lite transition: %s --%s--> %s (%s)",
            prev.value, event.value, next_state.value, note or "",
        )
        for listener in self._listeners:
            try:
                listener(transition)
            except Exception:
                logger.exception("FSM listener crashed")

        self._write_state()

    def _write_state(self) -> None:
        if not self._persist:
            return
        try:
            FSM_STATE_PATH.write_text(json.dumps(self.snapshot(), indent=2))
            os.chmod(FSM_STATE_PATH, 0o644)
        except Exception:
            logger.exception("Failed to persist FSM state to %s", FSM_STATE_PATH)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _gen_correlation_id() -> str:
    """Short correlation id = date + epoch seconds (no hex randomness)."""
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _failure_event_for(state: RecoveryState) -> RecoveryEvent:
    """If a healer crashed in a given state, what event should we emit?"""
    mapping = {
        RecoveryState.DUT_SSH_HEALING: RecoveryEvent.SSH_FAIL,
        RecoveryState.SPIRENT_HEAL_RECONNECT: RecoveryEvent.SPIRENT_RECONNECT_FAIL,
        RecoveryState.SPIRENT_HEAL_LAB_SERVER: RecoveryEvent.SPIRENT_RECONNECT_FAIL,
        RecoveryState.PREREQ_FAILED: RecoveryEvent.PREREQ_UNFIXABLE,
    }
    return mapping.get(state, RecoveryEvent.MAX_RETRIES)


# ---------------------------------------------------------------------------
# Default healer stubs (used by scenario_runner if callers don't override)
# ---------------------------------------------------------------------------

def default_dut_ssh_healer(fsm: RecoveryFsmLite, payload: Dict[str, Any]) -> RecoveryEvent:
    """Best-effort DUT SSH heal via DNOSSession.

    payload: {"device_ip", "user", "password", "probe_cmd"}
    Returns SSH_HEAL_OK on success, SSH_UP_CLI_HANG if SSH layer is up but
    the CLI hangs, SSH_FAIL otherwise.
    """
    fsm.record_ssh_retry()
    time.sleep(fsm.guards.ssh_backoff_sec * (1 + fsm.context.ssh_retry_count))

    device_ip = payload.get("device_ip")
    if not device_ip:
        return RecoveryEvent.SSH_FAIL

    try:
        # Lazy import so this module stays free of scaler deps for unit testing.
        from scaler.dnos_session import DNOSSession  # type: ignore

        probe = payload.get("probe_cmd", "show system | no-more")
        with DNOSSession(
            device_ip,
            payload.get("user", "dnroot"),
            payload.get("password", "dnroot"),
            login_timeout=20,
        ) as ssh:
            out = ssh.send_command(probe, timeout=20)
            if out and "error" not in out.lower():
                return RecoveryEvent.SSH_HEAL_OK
            return RecoveryEvent.SSH_UP_CLI_HANG
    except Exception as exc:
        logger.warning("default_dut_ssh_healer: %s", exc)
        return RecoveryEvent.SSH_FAIL


def default_spirent_reconnect_healer(
    fsm: RecoveryFsmLite,
    payload: Dict[str, Any],
) -> RecoveryEvent:
    """Best-effort Spirent reconnect via spirent_tool.py connect + reserve.

    payload: {"spirent_tool_path": "/path/to/spirent_tool.py"}
    Returns SPIRENT_CONNECT_OK or SPIRENT_RECONNECT_FAIL.
    """
    fsm.record_spirent_reconnect()
    time.sleep(fsm.guards.spirent_backoff_sec * (1 + fsm.context.spirent_reconnect_count))

    tool = payload.get("spirent_tool_path") or os.environ.get("SPIRENT_TOOL_PATH")
    if not tool:
        # Best-effort guess.
        home = Path.home()
        candidates = [
            home / "SCALER" / "SPIRENT" / "spirent_tool.py",
            Path("/home/dn/SCALER/SPIRENT/spirent_tool.py"),
        ]
        for c in candidates:
            if c.exists():
                tool = str(c)
                break
    if not tool:
        return RecoveryEvent.SPIRENT_RECONNECT_FAIL

    try:
        p1 = subprocess.run(
            ["python3", tool, "connect"],
            capture_output=True, text=True, timeout=45,
        )
        if p1.returncode != 0:
            return RecoveryEvent.SPIRENT_RECONNECT_FAIL
        p2 = subprocess.run(
            ["python3", tool, "reserve"],
            capture_output=True, text=True, timeout=30,
        )
        if p2.returncode == 0:
            return RecoveryEvent.SPIRENT_CONNECT_OK
        return RecoveryEvent.SPIRENT_RECONNECT_FAIL
    except Exception as exc:
        logger.warning("default_spirent_reconnect_healer: %s", exc)
        return RecoveryEvent.SPIRENT_RECONNECT_FAIL


def default_spirent_lab_server_healer(
    fsm: RecoveryFsmLite,
    payload: Dict[str, Any],
) -> RecoveryEvent:
    """Escalate to Lab Server recovery via `spirent_tool.py recover --level stcweb`.

    This counts as a heavy op.
    """
    tool = payload.get("spirent_tool_path") or os.environ.get("SPIRENT_TOOL_PATH")
    if not tool:
        home = Path.home()
        candidate = home / "SCALER" / "SPIRENT" / "spirent_tool.py"
        if candidate.exists():
            tool = str(candidate)
    if not tool:
        return RecoveryEvent.SPIRENT_RECONNECT_FAIL

    try:
        p = subprocess.run(
            ["python3", tool, "recover", "--level", "stcweb"],
            capture_output=True, text=True, timeout=120,
        )
        if p.returncode == 0:
            return RecoveryEvent.SPIRENT_LAB_SERVER_OK
        return RecoveryEvent.SPIRENT_RECONNECT_FAIL
    except Exception as exc:
        logger.warning("default_spirent_lab_server_healer: %s", exc)
        return RecoveryEvent.SPIRENT_RECONNECT_FAIL


__all__ = [
    "FSM_STATE_PATH",
    "FailureClass",
    "RecoveryContext",
    "RecoveryEvent",
    "RecoveryFsmLite",
    "RecoveryGuards",
    "RecoveryState",
    "RecoveryTransition",
    "UnrecoverableError",
    "default_dut_ssh_healer",
    "default_spirent_lab_server_healer",
    "default_spirent_reconnect_healer",
]
