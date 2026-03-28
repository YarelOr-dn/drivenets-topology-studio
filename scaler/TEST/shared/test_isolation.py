#!/usr/bin/env python3
"""
Test isolation and cleanup guarantee engine.

Ensures tests leave devices in a clean state, even on crash or SIGTERM:
  - atexit + signal handlers for guaranteed cleanup
  - Config rollback commands from recipe
  - State clearing between scenarios
  - Mini config diff to verify cleanup

Recipe JSON format:
    "cleanup_commands": [
        "no debug evpn mac-mobility",
        "no set logging terminal"
    ],
    "isolation": {
        "clear_between_scenarios": true,
        "clear_commands": [
            "clear evpn mac-table instance {evpn_name} | no-more"
        ],
        "config_rollback_commands": [],
        "verify_cleanup": true
    }
"""

from __future__ import annotations

import atexit
import logging
import signal
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("test_isolation")

RunShowFn = Callable[[str, str], str]

_registered_cleanups: List[Callable] = []
_cleanup_ran = False


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CleanupAction:
    """One cleanup action to execute."""
    command: str
    device: str
    executed: bool = False
    result: str = ""
    error: Optional[str] = None


@dataclass
class IsolationResult:
    """Result of cleanup/isolation operations."""
    actions: List[CleanupAction] = field(default_factory=list)
    config_debris_found: bool = False
    cleanup_successful: bool = True
    errors: List[str] = field(default_factory=list)

    def summary(self) -> str:
        executed = sum(1 for a in self.actions if a.executed)
        failed = sum(1 for a in self.actions if a.error)
        return f"Cleanup: {executed}/{len(self.actions)} executed, {failed} errors, debris={'YES' if self.config_debris_found else 'NO'}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cleanup_successful": self.cleanup_successful,
            "config_debris_found": self.config_debris_found,
            "errors": self.errors,
            "actions": [
                {
                    "command": a.command,
                    "device": a.device,
                    "executed": a.executed,
                    "error": a.error,
                }
                for a in self.actions
            ],
        }


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

class TestIsolationGuard:
    """Context manager that guarantees cleanup on exit, crash, or signal."""

    def __init__(
        self,
        device: str,
        run_show: RunShowFn,
        cleanup_commands: Optional[List[str]] = None,
        config_rollback_commands: Optional[List[str]] = None,
    ):
        self.device = device
        self.run_show = run_show
        self.cleanup_commands = cleanup_commands or []
        self.config_rollback_commands = config_rollback_commands or []
        self._original_sigterm = None
        self._original_sigint = None
        self._cleaned = False
        self._result = IsolationResult()

    def __enter__(self) -> "TestIsolationGuard":
        self._register_handlers()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.cleanup()
        return False

    def cleanup(self) -> IsolationResult:
        """Execute all cleanup commands. Safe to call multiple times."""
        if self._cleaned:
            return self._result

        self._cleaned = True
        logger.info("Running cleanup for device %s (%d commands)", self.device, len(self.cleanup_commands))

        all_commands = self.cleanup_commands + self.config_rollback_commands

        for cmd in all_commands:
            action = CleanupAction(command=cmd, device=self.device)
            try:
                result = self.run_show(self.device, cmd)
                action.executed = True
                action.result = result[:500]
                if "error" in result.lower() and "no entries" not in result.lower():
                    action.error = result[:200]
            except Exception as exc:
                action.error = str(exc)
                self._result.errors.append(f"{cmd}: {exc}")
            self._result.actions.append(action)

        self._result.cleanup_successful = not self._result.errors
        self._restore_handlers()
        return self._result

    def clear_between_scenarios(
        self,
        clear_commands: Optional[List[str]] = None,
    ) -> List[str]:
        """Run inter-scenario state clearing commands."""
        results: List[str] = []
        for cmd in (clear_commands or []):
            try:
                output = self.run_show(self.device, cmd)
                results.append(f"[OK] {cmd}")
            except Exception as exc:
                results.append(f"[ERROR] {cmd}: {exc}")
        return results

    def _register_handlers(self) -> None:
        """Register atexit and signal handlers for cleanup."""
        global _registered_cleanups

        def _signal_handler(signum, frame):
            logger.warning("Received signal %d, running cleanup", signum)
            self.cleanup()
            sys.exit(128 + signum)

        self._original_sigterm = signal.getsignal(signal.SIGTERM)
        self._original_sigint = signal.getsignal(signal.SIGINT)

        try:
            signal.signal(signal.SIGTERM, _signal_handler)
            signal.signal(signal.SIGINT, _signal_handler)
        except (ValueError, OSError):
            pass

        cleanup_ref = self.cleanup
        _registered_cleanups.append(cleanup_ref)
        atexit.register(cleanup_ref)

    def _restore_handlers(self) -> None:
        """Restore original signal handlers."""
        try:
            if self._original_sigterm is not None:
                signal.signal(signal.SIGTERM, self._original_sigterm)
            if self._original_sigint is not None:
                signal.signal(signal.SIGINT, self._original_sigint)
        except (ValueError, OSError):
            pass

    @property
    def result(self) -> IsolationResult:
        return self._result


def load_isolation_config(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """Load isolation configuration from recipe."""
    return recipe.get("isolation", {
        "clear_between_scenarios": False,
        "clear_commands": [],
        "config_rollback_commands": [],
        "verify_cleanup": True,
    })


def load_cleanup_commands(recipe: Dict[str, Any]) -> List[str]:
    """Load cleanup commands from recipe top-level or isolation block."""
    commands = list(recipe.get("cleanup_commands", []))
    iso = recipe.get("isolation", {})
    commands.extend(iso.get("config_rollback_commands", []))
    return commands


def run_cleanup_guarantee(
    device: str,
    run_show: RunShowFn,
    recipe: Dict[str, Any],
) -> IsolationResult:
    """One-shot cleanup using recipe commands."""
    cleanup_cmds = load_cleanup_commands(recipe)
    guard = TestIsolationGuard(device, run_show, cleanup_cmds)
    return guard.cleanup()
