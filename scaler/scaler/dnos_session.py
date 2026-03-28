#!/usr/bin/env python3
"""
Persistent interactive SSH session for DNOS devices (shared library).

Promoted from TEST catalog InteractiveSSHSession with optional SSHConnectionPool
integration (reuse an existing paramiko.SSHClient), config helpers, and interactive
send/recv for flows like ``run start shell`` + password prompts.

Usage::

    with DNOSSession("100.64.4.200", "dnroot", "dnroot") as ssh:
        output = ssh.send_command("show evpn mac-table instance EVPN1")

    # Pool: pass client from SSHConnectionPool; close() only closes the shell.
    with DNOSSession(ip, user, pw, client=pooled_client, owns_client=False) as ssh:
        ...
"""

from __future__ import annotations

import logging
import re
import socket
import time
from contextlib import contextmanager
from typing import Iterator, Optional

logger = logging.getLogger("dnos_session")

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
_POLL_INTERVAL = 0.05
_PROMPT_DETECT_TIMEOUT = 15
_DEFAULT_CMD_TIMEOUT = 120
_STABLE_SILENCE_MS = 500


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


class DNOSSession:
    """Persistent SSH session with prompt-based command completion detection."""

    def __init__(
        self,
        ip: str,
        username: str,
        password: str,
        *,
        client=None,
        owns_client: Optional[bool] = None,
        connect_timeout: int = 15,
        shell_width: int = 250,
        shell_height: int = 50,
    ):
        """
        Args:
            ip: Device management IP.
            username: SSH username.
            password: SSH password.
            client: Optional existing ``paramiko.SSHClient`` (e.g. from a pool).
            owns_client: If False, ``close()`` does not close ``client`` (only the shell).
            connect_timeout: TCP connect timeout when creating a new client.
            shell_width / shell_height: PTY dimensions for ``invoke_shell``.
        """
        self.ip = ip
        self.username = username
        self.password = password
        self._external_client = client
        if owns_client is None:
            self._owns_client = client is None
        else:
            self._owns_client = owns_client
        self.connect_timeout = connect_timeout
        self.shell_width = shell_width
        self.shell_height = shell_height

        self._client = None
        self._shell = None
        self._prompt_re: Optional[re.Pattern] = None
        self._hostname: str = ""
        self._connected = False

        self._connect()

    def _connect(self) -> None:
        """Establish SSH connection and auto-detect the DNOS prompt."""
        import paramiko

        if self._external_client is not None:
            self._client = self._external_client
        else:
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self._client.connect(
                self.ip,
                port=22,
                username=self.username,
                password=self.password,
                timeout=self.connect_timeout,
                look_for_keys=False,
                allow_agent=False,
                banner_timeout=20,
            )

        self._shell = self._client.invoke_shell(
            width=self.shell_width, height=self.shell_height,
        )
        self._shell.settimeout(_DEFAULT_CMD_TIMEOUT)
        self._connected = True

        self._detect_prompt()

    def _detect_prompt(self) -> None:
        """Read login banner and build a regex matching the DNOS prompt."""
        buf = b""
        deadline = time.time() + _PROMPT_DETECT_TIMEOUT

        while time.time() < deadline:
            if self._shell.recv_ready():
                buf += self._shell.recv(65536)
                decoded = _strip_ansi(buf.decode("utf-8", errors="replace"))
                for line in reversed(decoded.strip().splitlines()):
                    stripped = line.strip()
                    if not stripped:
                        continue
                    if stripped.endswith("#") or stripped.endswith(">"):
                        hostname = re.sub(r"[\(#>].*$", "", stripped).strip()
                        if hostname and "loading" not in hostname.lower():
                            self._hostname = hostname
                            escaped = re.escape(hostname)
                            self._prompt_re = re.compile(
                                r"[\r\n]" + escaped + r"(\([^\)]*\))?[#>]\s*$"
                            )
                            logger.debug(
                                "Detected prompt hostname=%s regex=%s",
                                hostname, self._prompt_re.pattern,
                            )
                            return
            else:
                time.sleep(_POLL_INTERVAL)

        decoded = _strip_ansi(buf.decode("utf-8", errors="replace"))
        lines = decoded.strip().splitlines()
        fallback = lines[-1].strip() if lines else "UNKNOWN"
        hostname = re.sub(r"[\(#>].*$", "", fallback).strip() or "UNKNOWN"
        self._hostname = hostname
        escaped = re.escape(hostname)
        self._prompt_re = re.compile(
            r"[\r\n]" + escaped + r"(\([^\)]*\))?[#>]\s*$"
        )
        logger.warning(
            "Prompt detection timed out, using fallback hostname=%s", hostname,
        )

    def _read_until_prompt(self, timeout: int) -> str:
        """Read output until the DNOS prompt reappears."""
        buf = b""
        deadline = time.time() + timeout

        while time.time() < deadline:
            if self._shell.recv_ready():
                buf += self._shell.recv(65536)

                decoded = buf.decode("utf-8", errors="replace")
                clean = _strip_ansi(decoded)
                if self._prompt_re and self._prompt_re.search(clean):
                    return decoded
            else:
                time.sleep(_POLL_INTERVAL)

        return buf.decode("utf-8", errors="replace")

    def recv_until_markers(
        self,
        markers: list[str],
        timeout_s: float = 15.0,
        initial_drain: bool = False,
    ) -> str:
        """Read from the shell until any marker string appears (substring match).

        Used for interactive flows (e.g. password prompts, ``run start shell``).
        """
        if initial_drain and self._shell.recv_ready():
            self._shell.recv(65536)

        buf = ""
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self._shell.recv_ready():
                buf += self._shell.recv(65535).decode("utf-8", errors="replace")
                for m in markers:
                    if m in buf:
                        return buf
            else:
                time.sleep(_POLL_INTERVAL)
        return buf

    def send_raw(self, data: str) -> None:
        """Send bytes to the shell without ``| no-more`` or prompt handling."""
        self._shell.send(data)

    def find_prompt(self, timeout: float = 5.0) -> str:
        """Return the last line that looks like a DNOS prompt after brief idle read."""
        buf = self.recv_until_markers(["#", ">"], timeout_s=timeout)
        clean = _strip_ansi(buf)
        lines = [ln.strip() for ln in clean.splitlines() if ln.strip()]
        for line in reversed(lines):
            if line.endswith("#") or line.endswith(">"):
                return line
        return lines[-1] if lines else ""

    def disable_paging(self, timeout: int = 30) -> str:
        """Try ``set terminal length 0`` (best-effort; DNOS also supports ``| no-more``)."""
        return self.send_command(
            "set terminal length 0",
            timeout=timeout,
            auto_no_more=False,
        )

    def _clean_output(self, raw: str, command: str) -> str:
        """Strip command echo, trailing prompt, and ANSI codes."""
        cleaned = _strip_ansi(raw)
        lines = cleaned.splitlines()

        cmd_base = command.replace("| no-more", "").strip()
        start_idx = 0
        for i, line in enumerate(lines):
            s = line.strip()
            if not s:
                start_idx = i + 1
                continue
            if cmd_base and cmd_base in s:
                start_idx = i + 1
                continue
            break

        end_idx = len(lines)
        for i in range(len(lines) - 1, max(start_idx - 1, -1), -1):
            s = lines[i].strip()
            if not s:
                end_idx = i
                continue
            is_prompt = (
                (self._hostname and s.startswith(self._hostname) and "#" in s)
                or (self._prompt_re and self._prompt_re.search("\n" + s))
            )
            if is_prompt:
                end_idx = i
            else:
                break

        return "\n".join(lines[start_idx:end_idx])

    def is_alive(self) -> bool:
        """Check if the SSH connection is still active."""
        if not self._connected or not self._client or not self._shell:
            return False
        transport = self._client.get_transport()
        if not transport or not transport.is_active():
            return False
        try:
            transport.send_ignore()
            return True
        except Exception:
            return False

    def _reconnect(self) -> None:
        """Close stale shell and re-establish (only when we own the client)."""
        try:
            if self._shell:
                self._shell.close()
        except Exception:
            pass
        self._shell = None
        self._connected = False

        if self._external_client is not None:
            # Pooled client: open a new shell on same client
            import paramiko
            self._shell = self._external_client.invoke_shell(
                width=self.shell_width, height=self.shell_height,
            )
            self._shell.settimeout(_DEFAULT_CMD_TIMEOUT)
            self._connected = True
            self._detect_prompt()
            return

        if self._owns_client and self._client:
            try:
                self._client.close()
            except Exception:
                pass
        self._client = None
        self._connect()

    def send_command(
        self,
        command: str,
        timeout: int = _DEFAULT_CMD_TIMEOUT,
        auto_no_more: bool = True,
        reconnect_attempts: int = 3,
        reconnect_interval: float = 5.0,
    ) -> str:
        """Send a command and return output when the prompt reappears."""
        if auto_no_more and "| no-more" not in command:
            command = f"{command} | no-more"

        for attempt in range(reconnect_attempts + 1):
            try:
                if not self.is_alive():
                    self._reconnect()

                if self._shell.recv_ready():
                    self._shell.recv(65536)

                self._shell.send(command + "\n")

                raw = self._read_until_prompt(timeout)
                return self._clean_output(raw, command)

            except (socket.error, OSError, EOFError) as exc:
                logger.info(
                    "SSH connection lost (attempt %d/%d): %s",
                    attempt + 1, reconnect_attempts + 1, exc,
                )
                if attempt < reconnect_attempts:
                    time.sleep(reconnect_interval)
                    try:
                        self._reconnect()
                    except Exception as re_exc:
                        logger.debug("Reconnect failed: %s", re_exc)
                        continue
                else:
                    return f"[SSH ERROR] Connection lost after {reconnect_attempts + 1} attempts: {exc}"

            except Exception as exc:
                import paramiko as _pm
                if isinstance(exc, _pm.SSHException):
                    logger.info("SSHException (attempt %d): %s", attempt + 1, exc)
                    if attempt < reconnect_attempts:
                        time.sleep(reconnect_interval)
                        try:
                            self._reconnect()
                        except Exception:
                            continue
                    else:
                        return f"[SSH ERROR] {exc}"
                else:
                    return f"[SSH ERROR] Unexpected: {type(exc).__name__}: {exc}"

        return f"[SSH ERROR] Failed after {reconnect_attempts + 1} attempts"

    def send_command_ha_resilient(
        self,
        command: str,
        timeout: int = _DEFAULT_CMD_TIMEOUT,
        max_wait_sec: int = 180,
        retry_interval: float = 10.0,
    ) -> str:
        """Send a command with extended retry for post-HA recovery."""
        max_attempts = max(1, int(max_wait_sec / retry_interval))
        return self.send_command(
            command,
            timeout=timeout,
            reconnect_attempts=max_attempts,
            reconnect_interval=retry_interval,
        )

    @contextmanager
    def config_mode(self) -> Iterator[None]:
        """Enter ``configure``, yield, then ``end``."""
        out = self.send_command("configure", auto_no_more=False)
        if "[SSH ERROR]" in out or "ERROR" in out:
            logger.warning("config_mode: configure may have failed: %s", out[:200])
        try:
            yield
        finally:
            self.send_command("end", auto_no_more=False)

    def commit(self, check_only: bool = False) -> tuple[bool, str]:
        """Run ``commit`` or ``commit check`` from configuration mode."""
        cmd = "commit check" if check_only else "commit"
        out = self.send_command(cmd, auto_no_more=False)
        ok = "[SSH ERROR]" not in out and "error" not in out.lower()
        return ok, out

    def rollback(self, n: int = 0) -> str:
        """Run ``rollback`` or ``rollback N``."""
        cmd = f"rollback {n}" if n else "rollback"
        return self.send_command(cmd, auto_no_more=False)

    def send_config_set(
        self,
        commands: list[str],
        *,
        commit: bool = True,
        check_only: bool = False,
    ) -> str:
        """Enter config mode, send lines, optionally commit, then exit config mode."""
        acc: list[str] = []
        with self.config_mode():
            for line in commands:
                line = line.strip()
                if not line or line.startswith("!"):
                    continue
                acc.append(self.send_command(line, auto_no_more=False))
            if commit:
                ok, cout = self.commit(check_only=check_only)
                acc.append(cout)
                if not ok:
                    return "\n".join(acc)
        return "\n".join(acc)

    @property
    def hostname(self) -> str:
        return self._hostname

    @property
    def prompt_pattern(self) -> Optional[str]:
        return self._prompt_re.pattern if self._prompt_re else None

    def close(self) -> None:
        """Close the shell; optionally close the SSH client if we own it."""
        self._connected = False
        try:
            if self._shell:
                self._shell.close()
        except Exception:
            pass
        self._shell = None
        if self._owns_client and self._client and self._external_client is None:
            try:
                self._client.close()
            except Exception:
                pass
        self._client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __repr__(self):
        state = "connected" if self.is_alive() else "disconnected"
        return f"<DNOSSession {self._hostname}@{self.ip} [{state}]>"


class InteractiveSSHSession(DNOSSession):
    """Backward-compatible alias for promoted TEST code."""

    def __init__(
        self,
        ip: str,
        username: str,
        password: str,
        connect_timeout: int = 15,
        shell_width: int = 250,
        shell_height: int = 50,
    ):
        super().__init__(
            ip,
            username,
            password,
            connect_timeout=connect_timeout,
            shell_width=shell_width,
            shell_height=shell_height,
        )

    def __repr__(self):
        state = "connected" if self.is_alive() else "disconnected"
        return f"<InteractiveSSHSession {self._hostname}@{self.ip} [{state}]>"
