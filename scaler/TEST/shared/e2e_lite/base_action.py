#!/usr/bin/env python3
"""
base_action -- lightweight Action contract for /TEST.

Port of cheetah's `dnos_e2e_utils.actions.base_action.BaseAction`, simplified
for shell-backed tools (no pytest, no dn_cli_api).

The Action contract:

    action = MyAction(...)                             # configure
    action.add_pre_validation(ValidateFoo())           # optional extras
    action.add_post_validation(ValidateBar())
    out = action.execute()                             # runs pre -> exec -> post

Execute flow:

    1. `collect_data()` on every post-validation (pre-action snapshot).
    2. Run all pre-validations; fail fast on first FAIL unless
       `fail_on_first_validation=False`.
    3. Run `_execute_action()` (subclass implements).
    4. Run all post-validations.
    5. Return action output.

FSM integration: if an FSM is attached via `bind_fsm(fsm)`, recoverable
failures (SSH drop, Spirent crash) raise `RecoverableError`, which the Action
forwards to `fsm.on_event(classify(exc))` before re-raising. The scenario
runner then heals and retries.

This module does NOT depend on pytest. It depends only on `base_validation`
and optionally the recovery FSM.
"""
from __future__ import annotations

import logging
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type

from .base_validation import (
    BaseValidation,
    ValidationResult,
    ValidationStatus,
)

logger = logging.getLogger(__name__)

PRE_SUFFIX = "_Pre"
POST_SUFFIX = "_Post"


class ActionValidationStatus:
    """String enum for wire-compat with cheetah action results."""
    PASSED = "passed"
    FAILED = "failed"
    ERRORED = "errored"
    SKIPPED = "skipped"


class RecoverableError(RuntimeError):
    """Raise from `_execute_action` for failures the FSM should heal.

    Examples: SSH drop, Spirent session dead, Lab Server 404.

    The Action.execute() top-level will forward this to the FSM as a
    failure event, then re-raise so the scenario runner can decide whether
    to retry.
    """


@dataclass
class ActionRunRecord:
    """Per-call summary of an Action run."""
    name: str
    started_at: float = 0.0
    ended_at: float = 0.0
    duration_sec: float = 0.0
    output: Any = None
    pre_validations: List[Dict[str, Any]] = field(default_factory=list)
    post_validations: List[Dict[str, Any]] = field(default_factory=list)
    error: str = ""
    recoverable: bool = False
    fsm_state_after: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_sec": round(self.duration_sec, 3),
            "output": str(self.output) if self.output is not None else None,
            "pre_validations": self.pre_validations,
            "post_validations": self.post_validations,
            "error": self.error,
            "recoverable": self.recoverable,
            "fsm_state_after": self.fsm_state_after,
        }


# ---------------------------------------------------------------------------
# Classifier: map raised exceptions to "is this a RecoverableError?"
# ---------------------------------------------------------------------------

_RECOVERABLE_SIGNATURES = (
    "ssh",
    "paramiko",
    "connection refused",
    "connection reset",
    "connection closed",
    "broken pipe",
    "timed out",
    "timeout",
    "spirent",
    "lab server",
    "stcweb",
    "bll handle",
    "session dead",
    "no active session",
    "port not reserved",
)


def default_is_recoverable(exc: BaseException) -> bool:
    """Decide whether an exception is 'infra-level' and should trigger heal."""
    if isinstance(exc, RecoverableError):
        return True
    msg = str(exc).lower()
    if any(sig in msg for sig in _RECOVERABLE_SIGNATURES):
        return True
    type_name = type(exc).__name__.lower()
    return any(t in type_name for t in ("sshexception", "timeouterror", "brokenpipe"))


# ---------------------------------------------------------------------------
# BaseAction
# ---------------------------------------------------------------------------

class BaseAction(ABC):
    """Base class for all /TEST actions with pre/post validation.

    Subclass and override `_execute_action` (mandatory). Override
    `default_pre_validations` / `default_post_validations` if you want the
    subclass to always attach certain validations.

    Construction args (all optional):
        name                        -- action name (defaults to class name)
        timeout                     -- soft execution budget
        fail_on_first_validation    -- stop at first failed validation (default True)
        fsm                         -- RecoveryFsmLite to notify on recoverable errors
        is_recoverable              -- callable(exc) -> bool (override classifier)

    Instance extension points:
        add_pre_validation(v)  / remove_pre_validation(type)
        add_post_validation(v) / remove_post_validation(type)
        clear_default_validations()
        postpone_pre_validations(flag) / postpone_post_validations(flag)

    Call:
        out = action.execute()          # returns whatever _execute_action returned
    """
    should_connect_cli: bool = True
    default_pre_validations: List[BaseValidation] = []
    default_post_validations: List[BaseValidation] = []

    def __init__(
        self,
        *,
        name: Optional[str] = None,
        timeout: Optional[int] = None,
        fail_on_first_validation: bool = True,
        fsm: Any = None,
        is_recoverable: Optional[Callable[[BaseException], bool]] = None,
    ) -> None:
        self._name = name or self.__class__.__name__
        self.timeout = timeout
        self.fail_on_first_validation = fail_on_first_validation
        self.fsm = fsm
        self._is_recoverable = is_recoverable or default_is_recoverable

        self._pre_validations: List[BaseValidation] = []
        self._post_validations: List[BaseValidation] = []
        self._validation_results: Dict[str, ValidationResult] = {}
        self._postpone_pre = False
        self._postpone_post = False
        self.last_record: Optional[ActionRunRecord] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def name(self) -> str:
        return self._name

    def bind_fsm(self, fsm: Any) -> "BaseAction":
        """Attach a RecoveryFsmLite so recoverable errors drive FSM events."""
        self.fsm = fsm
        return self

    def add_pre_validation(self, v: BaseValidation) -> "BaseAction":
        self._pre_validations.append(v)
        return self

    def add_post_validation(self, v: BaseValidation) -> "BaseAction":
        self._post_validations.append(v)
        return self

    def add_pre_validations(self, vs: List[BaseValidation]) -> "BaseAction":
        self._pre_validations.extend(vs)
        return self

    def add_post_validations(self, vs: List[BaseValidation]) -> "BaseAction":
        self._post_validations.extend(vs)
        return self

    def remove_pre_validation(self, cls: Type[BaseValidation]) -> "BaseAction":
        self._pre_validations = [v for v in self._pre_validations if type(v) is not cls]
        self.default_pre_validations = [
            v for v in self.default_pre_validations if type(v) is not cls
        ]
        return self

    def remove_post_validation(self, cls: Type[BaseValidation]) -> "BaseAction":
        self._post_validations = [v for v in self._post_validations if type(v) is not cls]
        self.default_post_validations = [
            v for v in self.default_post_validations if type(v) is not cls
        ]
        return self

    def clear_default_validations(self) -> "BaseAction":
        self.default_pre_validations = []
        self.default_post_validations = []
        return self

    def postpone_pre_validations(self, flag: bool = True) -> "BaseAction":
        self._postpone_pre = flag
        return self

    def postpone_post_validations(self, flag: bool = True) -> "BaseAction":
        self._postpone_post = flag
        return self

    def get_action_outputs(self) -> Dict[str, Any]:
        """Override to inject action outputs into validations via set_params()."""
        return {}

    def execute(self) -> Any:
        """Main entry point. Returns the raw action output.

        On RecoverableError: emits SSH_FAIL or SPIRENT_SESSION_DEAD event
        to the FSM (if bound) and re-raises so the scenario runner can heal.
        """
        started = time.time()
        record = ActionRunRecord(name=self.name, started_at=started)
        self.last_record = record

        try:
            logger.debug("Action %s: collect_data on %d post-validations",
                         self.name, len(self._all_post()))
            self._run_collect_validations()

            if not self._postpone_pre:
                self._run_pre_validations(record)

            logger.debug("Action %s: _execute_action()", self.name)
            output = self._execute_action()
            record.output = output

            if not self._postpone_post:
                self._run_post_validations(record)

            return output
        except RecoverableError as exc:
            record.recoverable = True
            record.error = f"{type(exc).__name__}: {exc}"
            self._emit_recoverable_to_fsm(exc)
            raise
        except Exception as exc:
            record.error = f"{type(exc).__name__}: {exc}"
            if self._is_recoverable(exc):
                record.recoverable = True
                self._emit_recoverable_to_fsm(exc)
            raise
        finally:
            record.ended_at = time.time()
            record.duration_sec = record.ended_at - started
            if self.fsm is not None and hasattr(self.fsm, "state"):
                record.fsm_state_after = self.fsm.state.value

    def run_validations(
        self,
        pre_validations: bool = False,
        post_validations: bool = False,
    ) -> None:
        """Manually run validations (useful when postponed)."""
        if pre_validations:
            self._run_pre_validations(self.last_record or ActionRunRecord(name=self.name))
        if post_validations:
            self._run_post_validations(self.last_record or ActionRunRecord(name=self.name))

    # ------------------------------------------------------------------
    # Must implement
    # ------------------------------------------------------------------
    @abstractmethod
    def _execute_action(self) -> Any:
        """Do the work. Return any useful output."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _all_pre(self) -> List[BaseValidation]:
        seen_ids = set()
        out: List[BaseValidation] = []
        for v in list(self._pre_validations) + list(self.default_pre_validations):
            if id(v) in seen_ids:
                continue
            seen_ids.add(id(v))
            out.append(v)
        return out

    def _all_post(self) -> List[BaseValidation]:
        seen_ids = set()
        out: List[BaseValidation] = []
        for v in list(self._post_validations) + list(self.default_post_validations):
            if id(v) in seen_ids:
                continue
            seen_ids.add(id(v))
            out.append(v)
        return out

    def _run_collect_validations(self) -> None:
        for v in self._all_post():
            try:
                v.collect_data()
            except Exception:
                logger.debug("Post-validation collect_data raised for %s",
                             v.name, exc_info=True)

    def _run_pre_validations(self, record: ActionRunRecord) -> None:
        outputs = self.get_action_outputs()
        for v in self._all_pre():
            v.set_params(**outputs)
            result = self._run_one_validation(v, record, "pre")
            self._validation_results[v.name + PRE_SUFFIX] = result

    def _run_post_validations(self, record: ActionRunRecord) -> None:
        outputs = self.get_action_outputs()
        for v in self._all_post():
            v.set_params(**outputs)
            result = self._run_one_validation(v, record, "post")
            self._validation_results[v.name + POST_SUFFIX] = result

    def _run_one_validation(
        self,
        v: BaseValidation,
        record: ActionRunRecord,
        phase: str,
    ) -> ValidationResult:
        try:
            result = v.execute()
        except Exception as exc:
            result = ValidationResult(
                name=v.name,
                status=ValidationStatus.ERRORED,
                message=f"{type(exc).__name__}: {exc}",
                details={"traceback": traceback.format_exc(limit=4)},
            )
            if phase == "pre":
                record.pre_validations.append(result.to_dict())
            else:
                record.post_validations.append(result.to_dict())
            if self.fail_on_first_validation:
                raise
            return result

        if phase == "pre":
            record.pre_validations.append(result.to_dict())
        else:
            record.post_validations.append(result.to_dict())

        if result.status == ValidationStatus.FAILED and self.fail_on_first_validation:
            raise AssertionError(
                f"{self.name}: {phase}-validation {v.name} FAILED: {result.message}"
            )
        return result

    def _emit_recoverable_to_fsm(self, exc: BaseException) -> None:
        if self.fsm is None:
            return
        try:
            from .recovery_fsm_lite import RecoveryEvent  # local import to avoid cycle
        except Exception:
            return
        msg = str(exc).lower()
        if "spirent" in msg or "lab server" in msg or "bll" in msg or "stcweb" in msg:
            event = RecoveryEvent.SPIRENT_SESSION_DEAD
        elif "ssh" in msg or "paramiko" in msg or "connection" in msg or "broken pipe" in msg:
            event = RecoveryEvent.SSH_FAIL
        else:
            event = RecoveryEvent.SCENARIO_FAIL_AUTOMATION
        try:
            self.fsm.on_event(event, note=f"action={self.name}")
        except Exception:
            logger.exception("FSM rejected event %s from action %s",
                             event, self.name)


# ---------------------------------------------------------------------------
# Ready-made actions
# ---------------------------------------------------------------------------

class CallableAction(BaseAction):
    """Wrap a callable as a BaseAction -- handy for one-offs and tests.

    Usage:
        action = CallableAction(fn=lambda: run_ssh_cmd(...), name="check_link")
        action.add_post_validation(ShowCommandContains("show interfaces", "UP"))
        action.execute()
    """

    def __init__(
        self,
        fn: Callable[[], Any],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._fn = fn

    def _execute_action(self) -> Any:
        return self._fn()


class DnosShowAction(BaseAction):
    """Run a DNOS show command via a DNOSSession (or run_show callable)."""

    def __init__(
        self,
        command: str,
        *,
        session: Any = None,
        run_show: Optional[Callable[[str, str], str]] = None,
        device: str = "",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.command = command
        self.session = session
        self._run_show = run_show
        self.device = device

    def _execute_action(self) -> str:
        if self.session is not None and hasattr(self.session, "send_command"):
            try:
                return self.session.send_command(
                    self.command, timeout=self.timeout or 30,
                )
            except Exception as exc:
                raise RecoverableError(f"DnosShowAction SSH error: {exc}") from exc
        if self._run_show is not None:
            return self._run_show(self.device, self.command)
        raise RuntimeError(
            f"{self.name}: no session or run_show provided for '{self.command}'"
        )


__all__ = [
    "ActionRunRecord",
    "ActionValidationStatus",
    "BaseAction",
    "CallableAction",
    "DnosShowAction",
    "RecoverableError",
    "default_is_recoverable",
]
