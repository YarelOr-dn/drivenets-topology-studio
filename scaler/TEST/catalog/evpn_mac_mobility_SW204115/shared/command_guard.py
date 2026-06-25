#!/usr/bin/env python3
"""Pre-DUT command safety checks for /TEST runners.

This guard sits in front of every device-facing command so recipe rendering
bugs are caught locally. A command with unresolved tokens or a known-invalid
DNOS shape must never be sent to the DUT and then interpreted as a product
failure.
"""

from __future__ import annotations

import re
from typing import Iterable, List


class CommandGuardError(RuntimeError):
    """Raised when an automation command must not be sent to DNOS."""


_UNRESOLVED_TOKEN_RE = re.compile(r"\{[A-Za-z_][A-Za-z0-9_]*\}")
_BGP_BARE_RE = re.compile(r"^show\s+config\s+protocols\s+bgp(?:\s*\||\s*$)", re.I)
_TRACE_LAST_RE = re.compile(
    r"^show\s+file\s+traces\s+\S+\s+last\s+\d+(?:\s*\||\s*$)",
    re.I,
)
_PIPE_HEAD_TAIL_RE = re.compile(r"\|\s*(head|tail)\s+(\d+)\b", re.I)


def unresolved_tokens(command: str) -> List[str]:
    """Return unresolved ``{token}`` placeholders still present in a command."""

    if not isinstance(command, str):
        return []
    return sorted(set(_UNRESOLVED_TOKEN_RE.findall(command)))


def known_invalid_reasons(command: str) -> List[str]:
    """Return durable known-invalid DNOS command-shape reasons."""

    cmd = " ".join(str(command or "").strip().split())
    reasons: List[str] = []
    if _BGP_BARE_RE.search(cmd):
        reasons.append(
            "`show config protocols bgp` is incomplete on DNOS; use "
            "`show config protocols bgp <asn>` or parse `show config | flatten`."
        )
    if _TRACE_LAST_RE.search(cmd):
        reasons.append(
            "DNOS trace files do not support `last <N>` after the file path; "
            "use `| trailing <N>`."
        )
    pipe_head_tail = _PIPE_HEAD_TAIL_RE.search(cmd)
    if pipe_head_tail:
        replacement = "leading" if pipe_head_tail.group(1).lower() == "head" else "trailing"
        reasons.append(
            f"DNOS pipe syntax is `| {replacement} <N>`, not "
            f"`| {pipe_head_tail.group(1).lower()} <N>`."
        )
    if cmd.lower() == "no set logging terminal":
        reasons.append(
            "`no set logging terminal` is invalid operational syntax; use "
            "`unset logging terminal`."
        )
    return reasons


def guard_command(command: str, *, context: str = "") -> None:
    """Raise if ``command`` must not be sent to a live DUT."""

    problems: List[str] = []
    tokens = unresolved_tokens(command)
    if tokens:
        problems.append(f"unresolved placeholder(s): {', '.join(tokens)}")
    problems.extend(known_invalid_reasons(command))
    if not problems:
        return
    where = f" ({context})" if context else ""
    raise CommandGuardError(
        f"[COMMAND-GUARD]{where} blocked before DUT: {command!r}; "
        + "; ".join(problems)
    )


def guard_commands(commands: Iterable[str], *, context: str = "") -> None:
    """Validate a batch of commands before any of them is sent."""

    for command in commands:
        guard_command(command, context=context)
