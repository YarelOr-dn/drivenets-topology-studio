#!/usr/bin/env python3
"""
scenario_runner -- stop-fail-retry scenario gate for /TEST.

Fixes the "skip scenario" bug: when scenario N fails, we do NOT silently
proceed to scenario N+1. Instead we classify the failure:

    AUTOMATION (SSH drop, Spirent crash, CLI hang)
        -> FSM heals -> retry up to max_scenario_retries
        -> if exhausted: UnrecoverableSuiteFailure (HARD STOP)

    PRODUCT_BUG (DNOS actual bug found by test)
        -> pause -> AskQuestion: continue / abort / mark xfail

The runner is recipe-agnostic. A recipe provides:
    scenarios: List[Scenario]    -- id, name, callable, on_failure policy
    fsm: RecoveryFsmLite         -- healers registered
    classifier: callable(exc)    -> FailureClass

Usage:
    from e2e_lite import scenario_runner
    result = scenario_runner.run(
        suite_id="TEST_evpn_elan_ha_SW248907",
        scenarios=[...],
        fsm=fsm,
        on_product_bug="ask",      # "ask" | "abort" | "continue"
        active_session_path=Path.home() / "SCALER" / "TEST" / "active_test_session.json",
    )

A scenario is described by a `ScenarioSpec` dataclass. The run_fn receives
a RunContext that carries the FSM, the recipe-level payload, and a handle
to emit RecoveryEvents so the FSM state tracks reality.
"""

from __future__ import annotations

import json
import logging
import os
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .recovery_fsm_lite import (
    FailureClass,
    RecoveryEvent,
    RecoveryFsmLite,
    RecoveryState,
    UnrecoverableError,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

class ScenarioVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    XFAIL = "XFAIL"          # known bug, expected failure
    SKIPPED = "SKIPPED"      # deliberately skipped (not silent)
    ABORTED = "ABORTED"


@dataclass
class RunContext:
    """Per-run handle passed to each scenario run_fn."""

    suite_id: str
    fsm: RecoveryFsmLite
    payload: Dict[str, Any] = field(default_factory=dict)
    run_id: str = ""
    log_lines: List[str] = field(default_factory=list)

    def emit(self, event: RecoveryEvent, note: str = "", extra_payload: Optional[Dict[str, Any]] = None) -> None:
        """Forward an event into the FSM with merged payload."""
        merged = dict(self.payload)
        if extra_payload:
            merged.update(extra_payload)
        self.fsm.on_event(event, payload=merged, note=note)

    def log(self, msg: str) -> None:
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        line = f"{ts}  {msg}"
        self.log_lines.append(line)
        logger.info(msg)


ScenarioFn = Callable[["ScenarioSpec", RunContext], "ScenarioResult"]


@dataclass
class ScenarioSpec:
    """Describe one scenario the runner should execute."""

    id: str
    name: str
    run_fn: ScenarioFn
    on_failure: str = "fix_and_rerun"   # "fix_and_rerun" | "ask_user" | "abort" | "continue"
    known_bug: Optional[str] = None     # Jira key; failure is xfail when set + matched
    # Used by scenario_runner for the AskQuestion prompt text.
    description: str = ""
    # Optional per-scenario retry override (falls back to fsm.guards.max_scenario_retries)
    max_retries: Optional[int] = None

    def retries_budget(self, fsm: RecoveryFsmLite) -> int:
        if self.max_retries is not None:
            return self.max_retries
        return fsm.guards.max_scenario_retries


@dataclass
class ScenarioResult:
    """Outcome of one scenario invocation (before retry classification)."""

    id: str
    verdict: ScenarioVerdict
    failure_class: FailureClass = FailureClass.UNKNOWN
    error_message: str = ""
    duration_sec: float = 0.0
    attempt: int = 1
    details: Dict[str, Any] = field(default_factory=dict)
    exception: Optional[BaseException] = None

    @property
    def passed(self) -> bool:
        return self.verdict in (ScenarioVerdict.PASS, ScenarioVerdict.XFAIL)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["exception"] = str(self.exception) if self.exception else None
        d["verdict"] = self.verdict.value
        d["failure_class"] = self.failure_class.value
        return d


@dataclass
class SuiteResult:
    """Aggregate of a full suite run."""

    suite_id: str
    run_id: str
    started_at: str
    ended_at: str
    passed: int = 0
    failed: int = 0
    errored: int = 0
    skipped: int = 0
    xfailed: int = 0
    aborted: int = 0
    scenarios: List[Dict[str, Any]] = field(default_factory=list)
    final_fsm_state: str = ""
    unrecoverable: bool = False

    @property
    def total(self) -> int:
        return len(self.scenarios)

    @property
    def all_passed(self) -> bool:
        return self.failed == 0 and self.errored == 0 and self.aborted == 0 and not self.unrecoverable

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


# ---------------------------------------------------------------------------
# Classifiers
# ---------------------------------------------------------------------------

Classifier = Callable[[BaseException], FailureClass]


# Exception / message fragments that should be treated as AUTOMATION failures.
_AUTOMATION_SIGNATURES = (
    "paramiko",
    "ssh banner",
    "timed out",
    "timeout",
    "connection reset",
    "connection refused",
    "connection closed",
    "broken pipe",
    "eoferror",
    "no route to host",
    "spirent",
    "lab server",
    "stcweb",
    "bll",
    "label 'default' does not exist",
    "session dead",
    "watchdog",
    "recoverable",
)


def default_classifier(exc: BaseException) -> FailureClass:
    """Map an exception/message to AUTOMATION vs PRODUCT_BUG.

    The default is conservative: only well-known infra errors (SSH drop,
    Spirent crash, Lab Server 404, timeout) are AUTOMATION. Anything else --
    including assertion failures from verdict layers -- is PRODUCT_BUG so
    the user sees it and decides.
    """
    if isinstance(exc, AssertionError):
        return FailureClass.PRODUCT_BUG

    msg = str(exc).lower()
    for sig in _AUTOMATION_SIGNATURES:
        if sig in msg:
            return FailureClass.AUTOMATION

    # Specific exception types from our code base that we always treat as AUTOMATION.
    exc_type = type(exc).__name__.lower()
    if any(t in exc_type for t in ("sshexception", "timeouterror", "brokenpipe", "connection")):
        return FailureClass.AUTOMATION

    return FailureClass.UNKNOWN


# ---------------------------------------------------------------------------
# Ask-user interface (replaced at test time if needed)
# ---------------------------------------------------------------------------

def default_ask_product_bug(scenario: ScenarioSpec, result: ScenarioResult) -> str:
    """Terminal fallback when no GUI AskQuestion is wired.

    Returns one of: "continue", "abort", "xfail", "retry".
    """
    prompt = f"""
================================================================
PRODUCT BUG DETECTED in scenario {scenario.id} ({scenario.name})
  Error: {result.error_message[:300]}
  Attempt: {result.attempt}

Options:
  c -- continue to next scenario (mark this one FAIL, do not retry)
  r -- retry this scenario (may re-trigger the bug)
  x -- mark as XFAIL (known bug), continue
  a -- abort the suite
================================================================
Choice [c/r/x/a]: """.rstrip()
    # Best-effort CLI prompt; tests can monkey-patch this function.
    try:
        answer = input(prompt + " ").strip().lower()
    except EOFError:
        return "abort"
    mapping = {"c": "continue", "r": "retry", "x": "xfail", "a": "abort"}
    return mapping.get(answer, "abort")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

class UnrecoverableSuiteFailure(RuntimeError):
    """Raised when FSM reaches UNRECOVERABLE or the user aborts the suite."""


def run(
    suite_id: str,
    scenarios: List[ScenarioSpec],
    fsm: RecoveryFsmLite,
    payload: Optional[Dict[str, Any]] = None,
    classifier: Classifier = default_classifier,
    ask_product_bug: Callable[[ScenarioSpec, ScenarioResult], str] = default_ask_product_bug,
    on_product_bug: str = "ask",       # "ask" | "abort" | "continue"
    active_session_path: Optional[Path] = None,
    run_id: Optional[str] = None,
    results_path: Optional[Path] = None,
) -> SuiteResult:
    """Execute scenarios with the stop-fail-retry gate.

    Returns a SuiteResult. Raises UnrecoverableSuiteFailure if a scenario
    cannot be healed within its retry budget or the user aborts.

    `active_session_path` is updated after every scenario with FSM state,
    retry counters, and watchdog info so /SPIRENT status can read them.
    """
    run_id = run_id or datetime.now(timezone.utc).strftime("RUN_%Y%m%d_%H%M%S")
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    result = SuiteResult(
        suite_id=suite_id,
        run_id=run_id,
        started_at=started_at,
        ended_at="",
    )

    ctx = RunContext(
        suite_id=suite_id,
        fsm=fsm,
        payload=payload or {},
        run_id=run_id,
    )

    logger.info(
        "scenario_runner.run: suite=%s run_id=%s scenarios=%d",
        suite_id, run_id, len(scenarios),
    )
    ctx.log(f"Suite {suite_id} starting with {len(scenarios)} scenarios (FSM={fsm.state.value})")

    # Make sure FSM is primed to STABLE before any scenario.
    if fsm.state == RecoveryState.INIT:
        try:
            fsm.on_event(RecoveryEvent.HEALTH_OK, note="scenario_runner_boot")
        except UnrecoverableError as e:
            result.final_fsm_state = fsm.state.value
            result.unrecoverable = True
            result.ended_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            _persist_session(active_session_path, suite_id, fsm, result, run_id)
            raise UnrecoverableSuiteFailure("FSM could not reach STABLE before suite start") from e

    _persist_session(active_session_path, suite_id, fsm, result, run_id)

    try:
        for scenario in scenarios:
            attempt = 0
            scenario_done = False
            while not scenario_done:
                attempt += 1
                attempt_result = _run_one_attempt(scenario, ctx, classifier, attempt)

                if attempt_result.passed:
                    ctx.log(
                        f"Scenario {scenario.id} attempt {attempt}: "
                        f"{attempt_result.verdict.value} ({attempt_result.duration_sec:.1f}s)"
                    )
                    _record_scenario_attempt(result, scenario, attempt_result)
                    scenario_done = True
                    continue

                # -- Classification --------------------------------------------------
                cls = attempt_result.failure_class
                ctx.log(
                    f"Scenario {scenario.id} attempt {attempt}: FAIL classified={cls.value} "
                    f"msg={attempt_result.error_message[:200]}"
                )

                if cls == FailureClass.AUTOMATION:
                    scenario_done = _handle_automation_failure(
                        scenario, attempt_result, attempt, ctx,
                    )
                elif cls == FailureClass.PRODUCT_BUG:
                    scenario_done = _handle_product_bug(
                        scenario, attempt_result, ctx, on_product_bug, ask_product_bug,
                    )
                else:  # UNKNOWN -- treat as AUTOMATION with a log warning
                    ctx.log(
                        f"Scenario {scenario.id}: UNKNOWN failure class, "
                        f"treating as AUTOMATION"
                    )
                    scenario_done = _handle_automation_failure(
                        scenario, attempt_result, attempt, ctx,
                    )

                # Record AFTER handler so any verdict mutation (XFAIL, FAIL) is captured.
                _record_scenario_attempt(result, scenario, attempt_result)
                _persist_session(active_session_path, suite_id, fsm, result, run_id)
    except UnrecoverableSuiteFailure:
        result.unrecoverable = True
        raise
    except UnrecoverableError as e:
        ctx.log(f"Suite aborting: FSM reached {e.state.value}")
        result.unrecoverable = True
        raise UnrecoverableSuiteFailure(str(e)) from e
    finally:
        result.ended_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        result.final_fsm_state = fsm.state.value
        _persist_session(active_session_path, suite_id, fsm, result, run_id, final=True)
        if results_path:
            _write_results_file(results_path, result)

    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _run_one_attempt(
    scenario: ScenarioSpec,
    ctx: RunContext,
    classifier: Classifier,
    attempt: int,
) -> ScenarioResult:
    """Run one attempt, catching exceptions and classifying them."""
    start = time.time()
    try:
        result = scenario.run_fn(scenario, ctx)
        if not isinstance(result, ScenarioResult):
            # Allow run_fn to return ScenarioVerdict directly
            if isinstance(result, ScenarioVerdict):
                result = ScenarioResult(id=scenario.id, verdict=result)
            elif isinstance(result, bool):
                result = ScenarioResult(
                    id=scenario.id,
                    verdict=ScenarioVerdict.PASS if result else ScenarioVerdict.FAIL,
                )
            else:
                result = ScenarioResult(id=scenario.id, verdict=ScenarioVerdict.PASS)
        result.attempt = attempt
        result.duration_sec = time.time() - start
        # If the run_fn says FAIL without classifying, assume PRODUCT_BUG.
        if result.verdict == ScenarioVerdict.FAIL and result.failure_class == FailureClass.UNKNOWN:
            result.failure_class = FailureClass.PRODUCT_BUG
        return result
    except UnrecoverableError:
        raise
    except BaseException as exc:  # noqa: BLE001 -- we classify and re-throw as needed
        duration = time.time() - start
        cls = classifier(exc)
        tb = traceback.format_exc(limit=4)
        logger.warning(
            "Scenario %s attempt %d raised %s (class=%s): %s",
            scenario.id, attempt, type(exc).__name__, cls.value, exc,
        )
        return ScenarioResult(
            id=scenario.id,
            verdict=ScenarioVerdict.ERROR,
            failure_class=cls,
            error_message=f"{type(exc).__name__}: {exc}",
            duration_sec=duration,
            attempt=attempt,
            details={"traceback": tb},
            exception=exc,
        )


def _handle_automation_failure(
    scenario: ScenarioSpec,
    res: ScenarioResult,
    attempt: int,
    ctx: RunContext,
) -> bool:
    """Try to heal and retry. Return True when we've exhausted options."""
    budget = scenario.retries_budget(ctx.fsm)
    if attempt > budget:
        ctx.log(
            f"Scenario {scenario.id}: AUTOMATION failure exhausted "
            f"retry budget ({budget}); aborting suite"
        )
        raise UnrecoverableSuiteFailure(
            f"Scenario {scenario.id}: AUTOMATION failure beyond retry budget "
            f"({attempt}/{budget}): {res.error_message[:200]}"
        )

    ctx.fsm.record_scenario_retry(scenario.id)
    # Tell the FSM there was an automation-class failure; it will drive heal.
    try:
        ctx.fsm.on_event(RecoveryEvent.SCENARIO_FAIL_AUTOMATION, note=f"attempt_{attempt}")
        # After failure, explicitly ask FSM to walk back to STABLE (heal PrereqFailed).
        if ctx.fsm.state != RecoveryState.STABLE:
            ctx.fsm.on_event(RecoveryEvent.PREREQ_FIXED, note="post_automation_heal")
    except UnrecoverableError as e:
        ctx.log(f"FSM refused to heal: {e}")
        raise UnrecoverableSuiteFailure(str(e)) from e
    ctx.log(
        f"Scenario {scenario.id}: healed after AUTOMATION fail; retrying "
        f"(attempt {attempt+1}/{budget+1}); FSM={ctx.fsm.state.value}"
    )
    time.sleep(1.0)
    return False  # keep looping


def _handle_product_bug(
    scenario: ScenarioSpec,
    res: ScenarioResult,
    ctx: RunContext,
    policy: str,
    ask: Callable[[ScenarioSpec, ScenarioResult], str],
) -> bool:
    """Decide what to do with a PRODUCT_BUG based on recipe policy."""
    policy = (scenario.on_failure or policy or "ask").lower()

    if scenario.known_bug:
        res.verdict = ScenarioVerdict.XFAIL
        res.details["known_bug"] = scenario.known_bug
        ctx.fsm.on_event(
            RecoveryEvent.PRODUCT_BUG_ACCEPTED,
            note=f"known_bug={scenario.known_bug}",
        )
        ctx.log(
            f"Scenario {scenario.id}: XFAIL mapped to known_bug={scenario.known_bug}"
        )
        return True

    if policy in ("abort",):
        ctx.log(f"Scenario {scenario.id}: PRODUCT_BUG policy=abort; stopping suite")
        raise UnrecoverableSuiteFailure(
            f"Scenario {scenario.id}: PRODUCT_BUG per policy=abort: {res.error_message[:200]}"
        )
    if policy in ("continue", "fix_and_rerun"):
        # fix_and_rerun on PRODUCT_BUG means: heal infra, retry once; but we're
        # already past the infra layer. Mark FAIL and move on.
        ctx.fsm.on_event(RecoveryEvent.PRODUCT_BUG_ACCEPTED, note="policy_continue")
        res.verdict = ScenarioVerdict.FAIL
        return True

    # policy == "ask" (default)
    answer = ask(scenario, res)
    if answer == "abort":
        ctx.log(f"Scenario {scenario.id}: user chose ABORT")
        raise UnrecoverableSuiteFailure(
            f"Scenario {scenario.id}: user aborted after PRODUCT_BUG"
        )
    if answer == "retry":
        ctx.fsm.record_scenario_retry(scenario.id)
        return False  # retry loop
    if answer == "xfail":
        res.verdict = ScenarioVerdict.XFAIL
        ctx.fsm.on_event(RecoveryEvent.PRODUCT_BUG_ACCEPTED, note="user_xfail")
        return True
    # default: continue (mark FAIL, move on)
    ctx.fsm.on_event(RecoveryEvent.PRODUCT_BUG_ACCEPTED, note="user_continue")
    res.verdict = ScenarioVerdict.FAIL
    return True


def _record_scenario_attempt(
    suite_result: SuiteResult,
    scenario: ScenarioSpec,
    res: ScenarioResult,
) -> None:
    """Append or update the attempt record for this scenario in the suite result."""
    existing = next(
        (s for s in suite_result.scenarios if s["id"] == scenario.id),
        None,
    )
    payload = res.to_dict()
    payload["name"] = scenario.name
    payload["on_failure"] = scenario.on_failure

    if existing is None:
        existing = {"id": scenario.id, "attempts": []}
        suite_result.scenarios.append(existing)

    existing["attempts"].append(payload)
    existing["last_verdict"] = res.verdict.value
    existing["last_failure_class"] = res.failure_class.value

    # Only bump final-count buckets for the final attempt (when scenario is done).
    # _handle_product_bug + _handle_automation_failure decide that.
    # We update the summary when the attempt is "final" -- i.e., the scenario
    # won't be retried. We detect that by checking verdict vs policy.
    # Simpler approach: recompute at the end of the outer scenario loop.

    # For on-line visibility during the run, keep a rolling count.
    v = res.verdict
    counters = {
        ScenarioVerdict.PASS: "passed",
        ScenarioVerdict.FAIL: "failed",
        ScenarioVerdict.ERROR: "errored",
        ScenarioVerdict.XFAIL: "xfailed",
        ScenarioVerdict.SKIPPED: "skipped",
        ScenarioVerdict.ABORTED: "aborted",
    }
    # Recompute from the attempts list: final verdict per scenario.
    _recompute_summary(suite_result)


def _recompute_summary(suite_result: SuiteResult) -> None:
    passed = failed = errored = skipped = xfailed = aborted = 0
    for s in suite_result.scenarios:
        # Final verdict for a scenario = the last attempt's verdict.
        if not s.get("attempts"):
            continue
        last = s["attempts"][-1]["verdict"]
        if last == ScenarioVerdict.PASS.value:
            passed += 1
        elif last == ScenarioVerdict.FAIL.value:
            failed += 1
        elif last == ScenarioVerdict.ERROR.value:
            errored += 1
        elif last == ScenarioVerdict.XFAIL.value:
            xfailed += 1
        elif last == ScenarioVerdict.SKIPPED.value:
            skipped += 1
        elif last == ScenarioVerdict.ABORTED.value:
            aborted += 1
    suite_result.passed = passed
    suite_result.failed = failed
    suite_result.errored = errored
    suite_result.xfailed = xfailed
    suite_result.skipped = skipped
    suite_result.aborted = aborted


def _persist_session(
    path: Optional[Path],
    suite_id: str,
    fsm: RecoveryFsmLite,
    result: SuiteResult,
    run_id: str,
    final: bool = False,
) -> None:
    """Update ~/SCALER/TEST/active_test_session.json with FSM state for /SPIRENT."""
    if path is None:
        return
    try:
        existing: Dict[str, Any] = {}
        if path.exists():
            try:
                existing = json.loads(path.read_text())
            except Exception:
                existing = {}

        # Preserve non-runner fields if present.
        existing.setdefault("suite", suite_id)
        existing["run_id"] = run_id
        existing["active"] = not final
        existing["fsm_state"] = fsm.state.value
        existing["fsm_snapshot"] = fsm.snapshot()
        existing["scenario_retries_this_run"] = dict(fsm.context.scenario_retries)
        existing["passed"] = result.passed
        existing["failed"] = result.failed
        existing["errored"] = result.errored
        existing["xfailed"] = result.xfailed
        existing["updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(existing, indent=2, default=str))
    except Exception as exc:
        logger.warning("Failed to persist active_test_session.json: %s", exc)


def _write_results_file(path: Path, result: SuiteResult) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result.to_dict(), indent=2, default=str))
    except Exception:
        logger.exception("Failed to write suite results to %s", path)


__all__ = [
    "ScenarioFn",
    "ScenarioSpec",
    "ScenarioResult",
    "ScenarioVerdict",
    "SuiteResult",
    "RunContext",
    "UnrecoverableSuiteFailure",
    "default_classifier",
    "default_ask_product_bug",
    "run",
]
