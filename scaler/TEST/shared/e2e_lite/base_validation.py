#!/usr/bin/env python3
"""
base_validation -- lightweight Validation contract for /TEST actions.

Inspired by cheetah's `dnos_e2e_utils.validations.base_validation.BaseValidation`,
but simplified for our shell-backed world:

    * No pytest coupling (no `request` fixture, no cluster_handler property).
    * Works with DNOSSession (paramiko) or a callable run_show function.
    * `collect_data()` is called BEFORE the owning action; `execute()` AFTER.
    * Supports `negative_validation` (pass when _validate raises or returns False).

Typical usage:

    class ValidateBdReady(BaseValidation):
        def __init__(self, vlan: int, session: DNOSSession):
            super().__init__(session=session, name=f"BD_{vlan}_ready")
            self.vlan = vlan
        def _validate(self) -> bool:
            out = self.run_show(f"show network-services bridge-domain bd_{self.vlan}")
            return "READY" in out

    val = ValidateBdReady(vlan=219, session=dut_ssh)
    action.add_pre_validation(val)

The base class handles timeouts, collect_data, negative-flag flipping, and
pretty logging. Subclasses only need `_validate()` and optionally `collect_data()`
+ `on_failure()`.
"""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class ValidationStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    ERRORED = "errored"
    SKIPPED = "skipped"


@dataclass
class ValidationResult:
    """Outcome of a single validation run."""
    name: str
    status: ValidationStatus = ValidationStatus.PENDING
    message: str = ""
    duration_sec: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    collected: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "duration_sec": round(self.duration_sec, 3),
            "details": self.details,
            "collected": self.collected,
        }


class BaseValidation(ABC):
    """Base class for all /TEST validations.

    Subclass and override `_validate` (mandatory) and `collect_data` (optional)
    and `on_failure` (optional).

    Constructor kwargs (all optional):
        name                -- override the class-derived name
        timeout             -- soft budget for `_validate` (seconds)
        negative_validation -- pass when _validate returns False / raises
        session             -- DNOSSession for run-show helper
        run_show            -- callable(device, cmd) -> str alternative
        fail_on_error       -- if False, _validate exception -> FAILED (not re-raised)
    """
    should_connect_cli: bool = True

    def __init__(
        self,
        *,
        name: Optional[str] = None,
        timeout: int = 30,
        negative_validation: bool = False,
        session: Any = None,
        run_show: Optional[Callable[[str, str], str]] = None,
        fail_on_error: bool = True,
    ) -> None:
        self._name = name or self.__class__.__name__
        self.timeout = timeout
        self.negative_validation = negative_validation
        self.session = session
        self._run_show = run_show
        self.fail_on_error = fail_on_error

        self.action_result: Any = None
        self.params: Dict[str, Any] = {}
        self._collected: Dict[str, Any] = {}
        self.last_result: Optional[ValidationResult] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def name(self) -> str:
        return self._name

    def set_params(self, **kwargs) -> "BaseValidation":
        """Receive outputs from the owning action (e.g. stream_name, vlan)."""
        self.params.update(kwargs)
        return self

    def collect_data(self) -> None:
        """Optional pre-action data grab. Runs once before the action."""
        pass

    def on_failure(self) -> None:
        """Optional hook for side effects when validation fails."""
        pass

    def execute(self) -> ValidationResult:
        """Run validation end-to-end and return a ValidationResult.

        - Respects `timeout` (soft; we don't forcibly interrupt).
        - Honours `negative_validation` inversion.
        - Stores last_result for post-mortem inspection.
        """
        start = time.time()
        res = ValidationResult(name=self.name, collected=dict(self._collected))
        try:
            passed = bool(self._validate())
            if self.negative_validation:
                passed = not passed
            res.status = ValidationStatus.PASSED if passed else ValidationStatus.FAILED
            res.message = "OK" if passed else "validation returned False"
        except Exception as exc:
            if self.negative_validation:
                res.status = ValidationStatus.PASSED
                res.message = f"negative: raised as expected ({type(exc).__name__}: {exc})"
            else:
                res.status = ValidationStatus.ERRORED
                res.message = f"{type(exc).__name__}: {exc}"
                try:
                    self.on_failure()
                except Exception:
                    logger.exception("on_failure raised for %s", self.name)
                if self.fail_on_error:
                    res.duration_sec = time.time() - start
                    self.last_result = res
                    raise
        finally:
            res.duration_sec = time.time() - start
            self.last_result = res

        if res.status == ValidationStatus.FAILED and not self.negative_validation:
            try:
                self.on_failure()
            except Exception:
                logger.exception("on_failure raised for %s", self.name)
        return res

    # ------------------------------------------------------------------
    # Helpers subclasses can use
    # ------------------------------------------------------------------
    def run_show(self, command: str, device: str = "") -> str:
        """Run a show command via session or custom run_show callable."""
        if self.session is not None and hasattr(self.session, "send_command"):
            return self.session.send_command(command, timeout=self.timeout)
        if self._run_show is not None:
            return self._run_show(device, command)
        raise RuntimeError(
            f"{self.name}: no session or run_show provided; cannot run '{command}'"
        )

    @abstractmethod
    def _validate(self) -> bool:
        """Do the work. Return True on success. Raise for errors."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Ready-made validations for common use cases
# ---------------------------------------------------------------------------

class CallableValidation(BaseValidation):
    """Wrap an arbitrary callable -> bool as a BaseValidation.

    Useful in tests and quick one-offs where writing a subclass is overkill::

        val = CallableValidation(
            name="ping_pe4",
            fn=lambda: subprocess.call(["ping", "-c1", "100.64.4.98"]) == 0,
        )
    """

    def __init__(self, fn: Callable[[], bool], **kwargs) -> None:
        super().__init__(**kwargs)
        self._fn = fn

    def _validate(self) -> bool:
        return bool(self._fn())


class ShowCommandContains(BaseValidation):
    """Pass when a DNOS show command output contains the given substring."""

    def __init__(self, command: str, substring: str, device: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self.command = command
        self.substring = substring
        self.device = device

    def _validate(self) -> bool:
        out = self.run_show(self.command, device=self.device)
        self._collected["output_head"] = out[:500]
        return self.substring in out


class WaitForCondition(BaseValidation):
    """Poll a callable until it returns True, within `timeout` seconds."""

    def __init__(
        self,
        predicate: Callable[[], bool],
        *,
        poll_interval: float = 2.0,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.predicate = predicate
        self.poll_interval = max(0.1, poll_interval)

    def _validate(self) -> bool:
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            try:
                if self.predicate():
                    return True
            except Exception:
                logger.debug("WaitForCondition predicate raised; retrying")
            time.sleep(self.poll_interval)
        return False


__all__ = [
    "BaseValidation",
    "CallableValidation",
    "ShowCommandContains",
    "ValidationResult",
    "ValidationStatus",
    "WaitForCondition",
]
