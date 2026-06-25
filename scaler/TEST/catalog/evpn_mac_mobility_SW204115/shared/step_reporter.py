#!/usr/bin/env python3
"""
Step reporter -- structured visibility for action+validate flows.

Every long-running step in /TEST orchestration is wrapped by a `Step` context
manager so the user sees:

    [STEP 3/12] action=apply_subif validate=oper_up timeout=15s ...
    [STEP 3/12] PASS in 3.2s (1 poll, last=admin=enabled oper=up)

Instead of the legacy:

    [REPROV-DNOS-SUBIF] applying...
    (silence for 15s)
    [REPROV-DNOS-SUBIF] applied
    sleeping 5s for IP to settle...
    (silence for 5s)

Design:
  - Each StepReporter tracks (current_idx, total) for a phase.
  - Each Step is opened with `name`, optional `validate` label, optional
    `timeout_sec`, and emits start + end lines.
  - End line includes elapsed, validation outcome, and last observed value
    so a quick scan tells you exactly which step failed and why.
  - Records are kept in `reporter.history` for evidence dumps.

Usage:
    rep = StepReporter("REPROV", total=8)
    with rep.step("discover_topology", validate="dut_subif_present",
                  timeout_sec=10) as step:
        info = discover_dead_peer_topology(...)
        step.set_result(info)
        if not info["found"]:
            step.fail("no matching sub-if -- aborting")
    if step.failed:
        return {...}

    with rep.step("recover_in_place_spirent_peer", validate="bgp_established",
                  timeout_sec=60) as step:
        result = recover_in_place_spirent_peer(...)
        step.attach_validation(result.get("validation"))
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional


@dataclass
class StepRecord:
    idx: int
    total: int
    name: str
    validate: str = ""
    timeout_sec: Optional[float] = None
    started_at: float = field(default_factory=time.time)
    ended_at: Optional[float] = None
    passed: Optional[bool] = None
    detail: str = ""
    last_observed: Any = None
    result: Any = None

    @property
    def elapsed_sec(self) -> float:
        end = self.ended_at if self.ended_at is not None else time.time()
        return round(end - self.started_at, 2)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "idx": self.idx,
            "total": self.total,
            "name": self.name,
            "validate": self.validate,
            "timeout_sec": self.timeout_sec,
            "elapsed_sec": self.elapsed_sec,
            "passed": self.passed,
            "detail": self.detail[:240] if isinstance(self.detail, str) else self.detail,
            "last_observed": self.last_observed,
        }


class _StepContext:
    """Returned by StepReporter.step() -- callers use .set_result(),
    .attach_validation(), .fail(reason), .pass_(reason).
    """

    def __init__(self, record: StepRecord, reporter: "StepReporter") -> None:
        self._record = record
        self._reporter = reporter
        self._explicit = False

    @property
    def record(self) -> StepRecord:
        return self._record

    @property
    def failed(self) -> bool:
        return self._record.passed is False

    @property
    def passed(self) -> bool:
        return self._record.passed is True

    def set_result(self, value: Any) -> None:
        """Store the action's return value for the evidence dump."""
        self._record.result = value

    def set_observed(self, value: Any) -> None:
        """Store the last observed value (e.g. raw_state, MAC count)."""
        self._record.last_observed = value

    def attach_validation(self, val: Any) -> None:
        """Pull pass/fail + observed value out of a ValidationResult or dict.

        Accepts either a ValidationResult instance or its `.as_dict()` form
        (which is what flows back through JSON-serialized step results).
        """
        if val is None:
            return
        if hasattr(val, "passed"):
            passed = bool(val.passed)
            observed = getattr(val, "last_value", None)
            reason = getattr(val, "reason", "")
            attempts = getattr(val, "attempts", None)
        elif isinstance(val, dict):
            passed = bool(val.get("passed"))
            observed = val.get("last_value")
            reason = str(val.get("reason", ""))
            attempts = val.get("attempts")
        else:
            return
        if passed:
            extra = f" ({attempts} poll(s))" if attempts else ""
            self.pass_(reason + extra if reason else f"validation passed{extra}")
        else:
            self.fail(reason or "validation failed")
        self._record.last_observed = observed

    def pass_(self, detail: str = "") -> None:
        """Explicitly mark this step as passed with a one-line detail."""
        self._record.passed = True
        if detail:
            self._record.detail = detail
        self._explicit = True

    def fail(self, detail: str = "") -> None:
        """Explicitly mark this step as failed with a one-line reason."""
        self._record.passed = False
        if detail:
            self._record.detail = detail
        self._explicit = True

    def warn(self, detail: str = "") -> None:
        """Mark passed=True but flag with a [WARN] prefix in the report."""
        self._record.passed = True
        if detail:
            self._record.detail = f"[WARN] {detail}"
        self._explicit = True

    @property
    def is_explicit(self) -> bool:
        return self._explicit


class StepReporter:
    """Emits structured `[STEP N/M] action=X validate=Y ...` lines.

    Args:
        prefix: Tag printed at the start of each line (e.g. "REPROV", "PEER").
        total: Expected total steps for this phase (used in `N/M`). Set 0
            if unknown -- the reporter will print just `[STEP N]`.
        out: Optional callable for output (defaults to print). Tests can
            substitute a list-collector.
    """

    def __init__(self, prefix: str, total: int = 0,
                 out: Optional[Any] = None) -> None:
        self.prefix = prefix.strip("[] ")
        self.total = max(0, int(total))
        self._idx = 0
        self.history: List[StepRecord] = []
        self._out = out if out is not None else print

    def _emit(self, msg: str) -> None:
        try:
            self._out(msg, flush=True)
        except TypeError:
            # Custom out callables may not accept flush=
            try:
                self._out(msg)
            except Exception:
                pass

    def _label(self, idx: int) -> str:
        if self.total > 0:
            return f"[{self.prefix}][STEP {idx}/{self.total}]"
        return f"[{self.prefix}][STEP {idx}]"

    @contextmanager
    def step(
        self,
        name: str,
        validate: str = "",
        timeout_sec: Optional[float] = None,
    ) -> Iterator[_StepContext]:
        """Open a step. Use as a context manager.

        On normal completion: if the caller did not call `pass_()` or `fail()`,
        the step is marked PASS by default (action ran without exception).
        On exception: marked FAIL automatically with the exception message.
        """
        self._idx += 1
        record = StepRecord(
            idx=self._idx,
            total=self.total,
            name=name,
            validate=validate,
            timeout_sec=timeout_sec,
        )
        self.history.append(record)
        ctx = _StepContext(record, self)

        header = f"  {self._label(record.idx)} action={name}"
        if validate:
            header += f" validate={validate}"
        if timeout_sec is not None:
            header += f" timeout={timeout_sec}s"
        header += " ..."
        self._emit(header)

        try:
            yield ctx
            if record.passed is None:
                record.passed = True
                if not record.detail:
                    record.detail = "completed without explicit validation"
        except Exception as exc:
            record.passed = False
            record.detail = f"{exc.__class__.__name__}: {exc}"
            record.ended_at = time.time()
            self._emit_outcome(record)
            raise
        finally:
            if record.ended_at is None:
                record.ended_at = time.time()
                self._emit_outcome(record)

    def _emit_outcome(self, record: StepRecord) -> None:
        verdict = "PASS" if record.passed else "FAIL"
        bracket = "[OK]" if record.passed else "[!!]"
        line = (f"  {self._label(record.idx)} {bracket} {verdict} "
                f"in {record.elapsed_sec}s")
        if record.detail:
            line += f" -- {record.detail[:200]}"
        self._emit(line)

    def summary(self) -> Dict[str, Any]:
        """Return a JSON-friendly summary of all steps for evidence dumps."""
        passed = sum(1 for r in self.history if r.passed)
        failed = sum(1 for r in self.history if r.passed is False)
        return {
            "prefix": self.prefix,
            "total_planned": self.total,
            "total_run": len(self.history),
            "passed": passed,
            "failed": failed,
            "elapsed_sec": round(sum(r.elapsed_sec for r in self.history), 2),
            "steps": [r.as_dict() for r in self.history],
        }

    def all_passed(self) -> bool:
        return all(r.passed for r in self.history) and bool(self.history)


__all__ = ["StepReporter", "StepRecord"]
