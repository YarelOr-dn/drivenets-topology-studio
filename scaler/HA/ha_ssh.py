#!/usr/bin/env python3
"""
ha_ssh.py -- Shared SSH shell utilities for DNOS HA tools.

Single source of truth for interactive SSH to DNOS devices. Uses select()-based
zero-CPU polling instead of fixed sleeps. Exits as soon as CLI prompt returns
or HA anomaly is detected.

Used by: ha_executor.py, ha_flowspec_test.py, ensure_dnaas_path.py
"""

import re
import select
import time
from typing import Pattern

import paramiko

# DNOS CLI prompt: hostname# or hostname(config-xxx)# with optional trailing space
PROMPT_RE = re.compile(r'[\w\-_.]+(?:\([^)]*\))?[#>]\s*$')

# HA system events that indicate an anomaly during command execution.
# These appear in SSH output when `set logging terminal` is active.
HA_EVENT_PATTERNS = [
    ("NCC_SWITCHOVER", "ncc_switchover"),
    ("SYSTEM_PROCESS_NOT_AVAILABLE", "process_down"),
    ("SYSTEM_CONTAINER_RESTART", "container_restart"),
    ("Connection closed", "connection_lost"),
    ("Connection reset", "connection_lost"),
]

# Per-command expect patterns. Avoids 1.5s idle-timeout fallback for known transitions.
EXPECT_MAP: dict[str, Pattern] = {
    "configure": re.compile(r'\(config\)[#>]\s*$'),
    "commit check": re.compile(r'\(config\)[#>]\s*$'),  # stays in config mode
    "commit": re.compile(r'[\w\-_.]+(?:\([^)]*\))?[#>]\s*$'),
    "exit": re.compile(r'[\w\-_.]+(?:\([^)]*\))?[#>]\s*$'),
}


def _expect_for_cmd(cmd: str) -> Pattern | None:
    """Return expect pattern for command, or None to use default PROMPT_RE."""
    cmd_stripped = cmd.strip()
    for key, pattern in EXPECT_MAP.items():
        if cmd_stripped.startswith(key):
            return pattern
    return None


def recv_until_ready(
    chan,
    timeout: float = 30.0,
    expect: Pattern | None = None,
    detect_anomalies: bool = True,
) -> tuple[str, str | None]:
    """
    Poll channel until the DNOS CLI prompt returns or an anomaly is detected.
    Returns (output_text, event_label_or_none).

    Uses select.select() for OS-level blocking -- zero CPU while waiting.
    Exits immediately when:
      - CLI prompt detected (command finished)
      - HA anomaly event found in output (e.g. NCC_SWITCHOVER)
      - No new data for 1.5s after receiving partial output (non-standard prompt fallback)
      - Hard timeout reached
    """
    buf = b""
    deadline = time.monotonic() + timeout
    last_recv_at = time.monotonic()
    prompt_re = expect or PROMPT_RE

    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        # OS-level block until data arrives -- zero CPU
        try:
            readable, _, _ = select.select([chan], [], [], min(remaining, 0.5))
        except (ValueError, OSError):
            # Channel closed or invalid fd
            break
        if readable:
            try:
                chunk = chan.recv(4096)
            except Exception:
                break
            if not chunk:
                break
            buf += chunk
            last_recv_at = time.monotonic()
            text = buf.decode("utf-8", errors="replace")
            last_line = text.rstrip().split("\n")[-1] if text.strip() else ""
            if prompt_re.search(last_line):
                return text, None
            if detect_anomalies:
                for pattern, label in HA_EVENT_PATTERNS:
                    if pattern in text:
                        return text, label
        else:
            # select timed out (0.5s window) -- check idle fallback
            if buf and (time.monotonic() - last_recv_at) > 1.5:
                return buf.decode("utf-8", errors="replace"), None

    return buf.decode("utf-8", errors="replace"), ("timeout" if not buf else None)


def run_ssh_shell(
    ip: str,
    user: str,
    password: str,
    commands: list[str],
    timeout: int = 60,
) -> str:
    """
    Run commands in interactive DNOS CLI shell.

    Uses select()-based recv_until_ready. Each command returns as soon as the
    CLI prompt reappears, an anomaly is detected, or the per-command timeout
    expires -- whichever comes first.
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    for attempt in range(3):
        try:
            ssh.connect(ip, username=user, password=password, timeout=8, allow_agent=False, look_for_keys=False)
            break
        except (TimeoutError, OSError):
            if attempt < 2:
                time.sleep(5)
                continue
            raise

    chan = ssh.invoke_shell(width=200, height=50)
    recv_until_ready(chan, timeout=10, detect_anomalies=False)

    output = []
    events = []
    for cmd in commands:
        chan.send(cmd + "\n")
        expect = _expect_for_cmd(cmd)
        text, event = recv_until_ready(chan, timeout=timeout, expect=expect)
        if text:
            output.append(text)
        if event:
            events.append((cmd, event))

    ssh.close()
    result = "".join(output)
    if events:
        result += f"\n[ha_ssh_events: {events}]"
    return result


def ssh_quick_check(
    ip: str,
    username: str,
    password: str,
    command: str,
    timeout: int = 10,
) -> tuple[bool, str]:
    """
    Single-shot SSH: try once, no retries. Returns (success, output).

    Fast variant for poll_recovery and dut_run_any_ip. Uses same select()-based
    recv_until_ready for accurate convergence time measurement.
    """
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password, timeout=timeout, allow_agent=False, look_for_keys=False)
        chan = ssh.invoke_shell(width=200, height=50)
        recv_until_ready(chan, timeout=10, detect_anomalies=False)
        chan.send(command + "\n")
        text, _ = recv_until_ready(chan, timeout=timeout)
        ssh.close()
        return True, text
    except Exception:
        return False, ""
