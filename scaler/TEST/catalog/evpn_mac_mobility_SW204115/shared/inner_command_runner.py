"""Inner CLI surface runner for DNOS test recipes.

Wraps a persistent ``DNOSSession`` with prompt-aware nested-shell navigation
so /TEST recipes can declare typed phases that execute on:

* **vtysh** -- Quagga shell (``show flowspec db``, ``show evpn vni``, ...)
* **NCC routing-engine shell** -- Linux container hosting bgpd/zebra/...
* **NCP datapath shell** -- Linux container hosting wb_agent/xraycli
* **xraycli** -- ``/wb_agent/<topic>`` introspection on the datapath

Every entry/exit sequence here was live-validated on PE-1
(DNOS 26.2.0_339_dev, build commit 8fd38d35-dev_v26_2) on 2026-04-30.
See ``/tmp/probe_inner_surfaces_result.json`` for the ground-truth probe
output.

Why this exists vs. plain ``run_show_command`` / ``shell_run_commands``:

* ``run_show_command`` MCP rejects anything not starting with ``show`` --
  ``run start shell``, ``vtysh``, ``xraycli`` are blocked.
* ``shell_run_commands`` MCP is locked to ``/core/traces``, ``/core/logs``,
  ``/core/core_dumps/containers`` and uses one-shot exec -- it cannot do
  ``cat /.gitcommit`` (outside allowlist) or run ``vtysh`` / ``xraycli``.
* ``DNOSSession.send_command`` auto-appends ``| no-more`` and uses a
  DNOS-prompt regex; both break inside vtysh/Linux subshells.

This module uses ``send_raw`` + ``recv_until_markers`` (the documented
interactive primitives in :mod:`scaler.dnos_session`) to drive the nested
prompts deterministically, and **always** unwinds back to the DNOS prompt
even on exception so the persistent session stays usable for later phases.

Each surface returns a structured result:

.. code-block:: python

    {
        "surface":   "vtysh|ncc_shell|ncp_shell|xraycli",
        "command":   "show flowspec db",
        "ok":        True,
        "markers":   ["% Unknown"],   # rejection markers detected in output
        "elapsed_s": 0.42,
        "output":    "<cleaned stdout>",
    }

Recipes consume this via the new ``trace_views`` / ``vtysh_commands`` /
``ncc_shell_commands`` / ``xraycli`` keys in verify-phase blocks.
"""
from __future__ import annotations

import logging
import re
import time
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional

if TYPE_CHECKING:  # pragma: no cover - type-only import
    from scaler.dnos_session import DNOSSession

log = logging.getLogger(__name__)

_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
_BRACKETED_PASTE_RE = re.compile(r"\x1b\[\?2004[hl]")


def _strip_ansi(s: str) -> str:
    if not s:
        return ""
    return _ANSI_RE.sub("", _BRACKETED_PASTE_RE.sub("", s))


# ---------------------------------------------------------------------------
# Surface contract: prompt cues + rejection markers
# ---------------------------------------------------------------------------

# Prompt fragments we wait for after entering each surface. Order matters:
# the first marker that appears wins. We pick *substrings* (not regexes)
# because ``DNOSSession.recv_until_markers`` does substring matching.
_PROMPT_CUES: Dict[str, List[str]] = {
    # NCC routing-engine shell prompt looks like:
    #   (WK31D7VV00023)root@routing_engine:/[2026-04-30 16:15:45][inband_ns]#
    # Some builds prompt for password first.
    "ncc_shell": ["root@routing_engine", "$ ", "# "],
    # NCP datapath shell prompt:
    #   (WK31D7VV00023)root@datapath:/[ts][default]#
    "ncp_shell": ["root@datapath", "$ ", "# "],
    # vtysh prompt is hostname-flavored just like DNOS:
    #   YOR_PE-1#  (after entering vtysh)
    # We can't tell vtysh-# apart from DNOS-# textually, so callers track
    # which surface they are in via this module's state machine.
    "vtysh": ["# ", "> "],
    "password": ["assword:", "Password:"],
}

# Surface-specific rejection markers. Independent of DNOS CLI markers
# (which scenario_runner._show_command_error already covers for the outer
# CLI). Every entry is a substring; case-insensitive lookup.
_REJECT_MARKERS: Dict[str, List[str]] = {
    "vtysh": [
        "% Unknown command",
        "% Unknown",
        "% Command incomplete",
        "% Ambiguous command",
        "% Incomplete",
    ],
    "ncc_shell": [
        ": command not found",
        "No such file or directory",
        "Permission denied",
        "Operation not permitted",
    ],
    "ncp_shell": [
        ": command not found",
        "No such file or directory",
        "Permission denied",
        "Operation not permitted",
    ],
    "xraycli": [
        "xquery-invalid",
        "Error: Missing argument",
        "Usage: xraycli",
        "unknown topic",
        "Unknown topic",
    ],
}


def detect_markers(surface: str, output: str) -> List[str]:
    """Return the rejection markers seen in *output* for *surface*.

    Empty list = output looks healthy. Markers do *not* automatically
    fail the result; the caller decides how to score them (e.g. an
    ``xquery-invalid`` from ``xraycli`` may legitimately mean "topic
    not present" rather than a hard failure).
    """
    if not output:
        return []
    out_l = output.lower()
    return [m for m in _REJECT_MARKERS.get(surface, []) if m.lower() in out_l]


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------

@dataclass
class InnerResult:
    """One inner-command execution outcome.

    Attributes:
        surface: One of ``vtysh|ncc_shell|ncp_shell|xraycli``.
        command: The exact command string sent to the inner shell.
        ok: ``True`` if no rejection markers were seen *and* no transport
            error. Note: a passing command with empty output is still
            ``ok=True`` (e.g. ``grep`` with zero matches).
        markers: Rejection markers found in *output*.
        elapsed_s: Wall-clock seconds the command took (entry + execute,
            not including the surface entry/exit overhead).
        output: Cleaned stdout (ANSI stripped, prompt trimmed).
        error: Transport-level error string if the SSH call itself blew
            up. ``None`` when the surface returned any output at all.
    """

    surface: str
    command: str
    ok: bool
    markers: List[str] = field(default_factory=list)
    elapsed_s: float = 0.0
    output: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# The runner
# ---------------------------------------------------------------------------

class InnerCommandRunner:
    """Drive nested DNOS shells over a persistent ``DNOSSession``.

    Usage::

        from scaler.dnos_session import DNOSSession
        with DNOSSession(ip, user, password) as ssh:
            runner = InnerCommandRunner(ssh, password=password)
            results = runner.run_vtysh(["show flowspec db"])
            results += runner.run_ncc_shell(["cat /.gitcommit",
                                             "grep -B 5 -A 5 NOTIFICATION "
                                             "/core/traces/routing_engine/bgpd_traces"])
            results += runner.run_xraycli(["/wb_agent/flowspec/info"], ncp_id=0)

    Every public method is **safe to call in any order**: each one enters
    its surface, runs the commands, and exits cleanly. If any step
    raises, the runner unwinds the prompt stack via ``_drain_to_dnos()``
    so the session remains usable.
    """

    # Bounded waits per surface (seconds). Picked from live PE-1 latencies
    # plus 3x headroom. Override per-call via ``timeout_s``.
    _ENTRY_TIMEOUT = 15.0
    _EXIT_TIMEOUT = 8.0
    _CMD_TIMEOUT = 15.0

    def __init__(
        self,
        ssh: "DNOSSession",
        password: Optional[str] = None,
        *,
        device_label: Optional[str] = None,
    ) -> None:
        """Wrap a live ``DNOSSession``.

        Args:
            ssh: Connected ``DNOSSession`` (the same one
                ``scenario_runner.commit_check_assert`` already uses).
            password: Device login password. Some builds prompt for it
                again on ``run start shell``; some don't. The runner
                tries to pre-empt either way.
            device_label: Optional name for log lines (e.g. ``"PE-1"``).
        """
        self._ssh = ssh
        self._password = password or ""
        self._label = device_label or "device"

    # ------------------------------------------------------------------
    # Internal: nested-shell entry / exit primitives
    # ------------------------------------------------------------------

    def _send_raw(self, data: str) -> None:
        self._ssh.send_raw(data)

    def _recv(self, markers: Iterable[str], timeout_s: float) -> str:
        return self._ssh.recv_until_markers(list(markers), timeout_s=timeout_s)

    def _maybe_handle_password_prompt(
        self, buf: str, timeout_s: float = 8.0,
    ) -> str:
        """If *buf* contains a password prompt, send the password; return
        what we read after the answer."""
        for cue in _PROMPT_CUES["password"]:
            if cue in buf:
                if not self._password:
                    log.warning(
                        "%s: shell prompted for password but none was provided",
                        self._label,
                    )
                    return buf
                self._send_raw(self._password + "\n")
                return self._recv(_PROMPT_CUES["ncc_shell"], timeout_s=timeout_s)
        return ""

    def _drain_to_dnos(self, max_levels: int = 4) -> None:
        """Best-effort: send ``exit`` until we land back on the DNOS prompt.

        Used in ``finally`` blocks so an exception inside an inner shell
        never strands the persistent session in vtysh/bash. We only send
        ``exit`` -- never config-mode rollbacks -- because this runner
        does not enter config mode.
        """
        for _ in range(max_levels):
            try:
                self._send_raw("exit\n")
                self._recv(["# ", "> ", _PROMPT_CUES["ncc_shell"][0]],
                           timeout_s=self._EXIT_TIMEOUT)
            except Exception as exc:  # noqa: BLE001
                log.debug("%s: drain-exit raised %s; stopping", self._label, exc)
                break

    # ------------------------------------------------------------------
    # NCC routing-engine shell ('run start shell')
    # ------------------------------------------------------------------

    def _enter_ncc_shell(self) -> None:
        self._send_raw("run start shell\n")
        buf = self._recv(
            _PROMPT_CUES["ncc_shell"] + _PROMPT_CUES["password"],
            timeout_s=self._ENTRY_TIMEOUT,
        )
        self._maybe_handle_password_prompt(buf)

    def _exit_ncc_shell(self) -> None:
        self._send_raw("exit\n")
        self._recv(["# "], timeout_s=self._EXIT_TIMEOUT)

    @contextmanager
    def _ncc_shell_context(self):
        try:
            self._enter_ncc_shell()
            yield
        finally:
            try:
                self._exit_ncc_shell()
            except Exception:  # noqa: BLE001
                self._drain_to_dnos()

    # ------------------------------------------------------------------
    # NCP datapath shell ('run start shell ncp <id>')
    # ------------------------------------------------------------------

    def _enter_ncp_shell(self, ncp_id: int) -> None:
        self._send_raw(f"run start shell ncp {int(ncp_id)}\n")
        buf = self._recv(
            _PROMPT_CUES["ncp_shell"] + _PROMPT_CUES["password"],
            timeout_s=self._ENTRY_TIMEOUT,
        )
        self._maybe_handle_password_prompt(buf)

    def _exit_ncp_shell(self) -> None:
        self._send_raw("exit\n")
        self._recv(["# "], timeout_s=self._EXIT_TIMEOUT)

    @contextmanager
    def _ncp_shell_context(self, ncp_id: int):
        try:
            self._enter_ncp_shell(ncp_id)
            yield
        finally:
            try:
                self._exit_ncp_shell()
            except Exception:  # noqa: BLE001
                self._drain_to_dnos()

    # ------------------------------------------------------------------
    # vtysh: enter via 'run start shell' -> 'vtysh', exit via 'exit' x2
    # ------------------------------------------------------------------

    def _enter_vtysh(self) -> None:
        self._enter_ncc_shell()
        self._send_raw("vtysh\n")
        # vtysh emits a banner then a hostname# prompt. We accept '#' as
        # a sufficient cue here; the caller will validate output.
        self._recv(_PROMPT_CUES["vtysh"], timeout_s=self._ENTRY_TIMEOUT)

    def _exit_vtysh(self) -> None:
        self._send_raw("exit\n")
        self._recv(_PROMPT_CUES["ncc_shell"], timeout_s=self._EXIT_TIMEOUT)
        self._exit_ncc_shell()

    @contextmanager
    def _vtysh_context(self):
        try:
            self._enter_vtysh()
            yield
        finally:
            try:
                self._exit_vtysh()
            except Exception:  # noqa: BLE001
                self._drain_to_dnos()

    # ------------------------------------------------------------------
    # Generic single-command run inside an already-entered surface
    # ------------------------------------------------------------------

    def _run_in_current_surface(
        self,
        surface: str,
        command: str,
        *,
        timeout_s: float,
        wait_markers: Optional[List[str]] = None,
    ) -> InnerResult:
        # Pick prompt cues to terminate on. For Linux shells we expect
        # the prompt-cue list; for vtysh we accept '# ' / '> '.
        cues = wait_markers or _PROMPT_CUES.get(surface, ["# ", "> "])
        t0 = time.time()
        try:
            self._send_raw(command + "\n")
            raw = self._recv(cues, timeout_s=timeout_s)
        except Exception as exc:  # noqa: BLE001
            return InnerResult(
                surface=surface, command=command, ok=False,
                markers=[], elapsed_s=time.time() - t0,
                output="", error=f"{type(exc).__name__}: {exc}",
            )
        elapsed = time.time() - t0
        cleaned = _strip_ansi(raw)
        # Trim command echo line and trailing prompt line for readability.
        lines = cleaned.splitlines()
        if lines and command.split()[0] in lines[0]:
            lines = lines[1:]
        # Drop trailing prompt line if present
        if lines and (lines[-1].rstrip().endswith("#")
                      or lines[-1].rstrip().endswith("$")):
            lines = lines[:-1]
        clean_out = "\n".join(lines).rstrip()
        markers = detect_markers(surface, clean_out)
        return InnerResult(
            surface=surface, command=command,
            ok=not markers,
            markers=markers, elapsed_s=elapsed,
            output=clean_out, error=None,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_vtysh(
        self,
        commands: List[str],
        *,
        timeout_s: float = _CMD_TIMEOUT,
    ) -> List[InnerResult]:
        """Execute *commands* in the vtysh shell (one entry/exit)."""
        results: List[InnerResult] = []
        with self._vtysh_context():
            for cmd in commands:
                results.append(self._run_in_current_surface(
                    "vtysh", cmd, timeout_s=timeout_s,
                    wait_markers=_PROMPT_CUES["vtysh"],
                ))
        return results

    def run_ncc_shell(
        self,
        commands: List[str],
        *,
        timeout_s: float = _CMD_TIMEOUT,
    ) -> List[InnerResult]:
        """Execute *commands* in the NCC routing-engine Linux shell."""
        results: List[InnerResult] = []
        with self._ncc_shell_context():
            for cmd in commands:
                results.append(self._run_in_current_surface(
                    "ncc_shell", cmd, timeout_s=timeout_s,
                    wait_markers=_PROMPT_CUES["ncc_shell"],
                ))
        return results

    def run_ncp_shell(
        self,
        commands: List[str],
        *,
        ncp_id: int = 0,
        timeout_s: float = _CMD_TIMEOUT,
    ) -> List[InnerResult]:
        """Execute *commands* in the NCP datapath Linux shell."""
        results: List[InnerResult] = []
        with self._ncp_shell_context(ncp_id):
            for cmd in commands:
                results.append(self._run_in_current_surface(
                    "ncp_shell", cmd, timeout_s=timeout_s,
                    wait_markers=_PROMPT_CUES["ncp_shell"],
                ))
        return results

    def run_xraycli(
        self,
        topics: List[str],
        *,
        ncp_id: int = 0,
        timeout_s: float = _CMD_TIMEOUT,
    ) -> List[InnerResult]:
        """Execute ``xraycli /wb_agent/<topic>`` calls inside the NCP shell.

        Each entry in *topics* is the path argument (e.g.
        ``"/wb_agent/flowspec/info"``). The runner prefixes ``xraycli ``
        for you. To pass options use a full command string with leading
        ``xraycli`` -- the runner detects that and skips the prefix.
        """
        results: List[InnerResult] = []
        with self._ncp_shell_context(ncp_id):
            for topic in topics:
                cmd = topic if topic.lstrip().startswith("xraycli") \
                    else f"xraycli {topic}"
                results.append(self._run_in_current_surface(
                    "xraycli", cmd, timeout_s=timeout_s,
                    wait_markers=_PROMPT_CUES["ncp_shell"],
                ))
        return results

    # ------------------------------------------------------------------
    # Trace views: 'grep -B/-A' on /core/traces/<file> (NCC shell)
    # ------------------------------------------------------------------

    def run_trace_views(
        self,
        views: List[Dict[str, Any]],
        *,
        timeout_s: float = _CMD_TIMEOUT,
    ) -> List[InnerResult]:
        """Run a list of trace_view declarations.

        Each *view* is a dict::

            {
                "file":   "routing_engine/bgpd_traces",  # path under /core/traces/
                "match":  "MAC.*move",                   # regex (egrep -E)
                "context_before": 5,                     # optional, default 0
                "context_after":  5,                     # optional, default 0
                "max_lines":      200,                   # optional cap
                "ncp_id":         null                   # null = NCC shell
            }

        Uses ``grep -E -B<n> -A<n>`` on the NCC routing-engine shell. If
        ``ncp_id`` is set (int), runs on the NCP datapath shell instead
        (for ``datapath/wb_agent.*`` traces).
        """
        # Bucket views by surface (NCC vs NCP) so we minimize entry/exit cost.
        ncc_views = [v for v in views if v.get("ncp_id") in (None, "")]
        ncp_views_by_id: Dict[int, List[Dict[str, Any]]] = {}
        for v in views:
            nid = v.get("ncp_id")
            if nid in (None, ""):
                continue
            try:
                key = int(nid)
            except (TypeError, ValueError):
                continue
            ncp_views_by_id.setdefault(key, []).append(v)

        results: List[InnerResult] = []
        if ncc_views:
            with self._ncc_shell_context():
                for view in ncc_views:
                    results.append(self._exec_trace_view(
                        view, surface="ncc_shell", timeout_s=timeout_s,
                    ))
        for ncp_id, vs in ncp_views_by_id.items():
            with self._ncp_shell_context(ncp_id):
                for view in vs:
                    results.append(self._exec_trace_view(
                        view, surface="ncp_shell", timeout_s=timeout_s,
                    ))
        return results

    def _exec_trace_view(
        self,
        view: Dict[str, Any],
        *,
        surface: str,
        timeout_s: float,
    ) -> InnerResult:
        path_rel = (view.get("file") or "").lstrip("/")
        if not path_rel:
            return InnerResult(
                surface=surface, command="<no file>", ok=False,
                error="trace_view missing 'file'",
            )
        if surface == "ncp_shell":
            full = f"/core/traces/{path_rel}" if not path_rel.startswith(
                "/core/traces/") else path_rel
        else:
            full = f"/core/traces/{path_rel}" if not path_rel.startswith(
                "/core/traces/") else path_rel
        match = view.get("match") or ""
        before = int(view.get("context_before") or 0)
        after = int(view.get("context_after") or 0)
        max_lines = int(view.get("max_lines") or 0)
        # Build grep command. Quote pattern with single quotes; if pattern
        # itself contains single quotes, fall back to fgrep-style.
        use_fixed = view.get("fixed_string") is True
        pat = match.replace("'", "'\\''")  # bash-safe single-quote escape
        flag = "-F" if use_fixed else "-E"
        cmd = f"grep {flag} -B {before} -A {after} '{pat}' {full}"
        if max_lines > 0:
            cmd += f" | head -n {max_lines}"
        cues = _PROMPT_CUES["ncp_shell" if surface == "ncp_shell" else "ncc_shell"]
        return self._run_in_current_surface(
            surface, cmd, timeout_s=timeout_s, wait_markers=cues,
        )


__all__ = [
    "InnerCommandRunner",
    "InnerResult",
    "detect_markers",
]
