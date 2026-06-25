#!/usr/bin/env python3
"""
spirent_actions -- typed Spirent Actions built on BaseAction + SpirentWatchdog.

Replaces the scattered embedded ``spirent_*`` helpers in individual recipes
(see ``evpn_mac_mobility_SW204115/shared/mac_trigger.py``) with composable,
self-validating Actions. Each Action:

* Calls ``spirent_tool.py <subcommand>`` via ``SpirentWatchdog.guarded_run()``
  when a watchdog is injected, or directly via ``subprocess`` otherwise.
* Runs **typed pre-validations** (is the port reserved? is the BD READY?)
  before attempting the Spirent CLI call -- catching orchestrator bugs
  before they hit the Lab Server.
* Runs **typed post-validations** (does the stream exist? is TX > 0?
  is BGP ESTABLISHED?) after the CLI call -- so every action is self-proving.

When a recoverable failure is detected (Spirent session dead, port lost,
Lab Server hiccup) the command surface emits a ``RecoverableError`` so the
enclosing :mod:`scenario_runner` can apply stop-fail-retry and the FSM can
heal. A watchdog, when installed, additionally heals at the call site.

Actions implemented in this module
----------------------------------

``CreateStreamAction``
    Wraps ``spirent_tool.py create-stream``. Pre: port reserved. Post:
    stream name appears in ``status --json``.

``StartTrafficAction``
    Wraps ``spirent_tool.py start``. Pre: at least one stream configured.
    Post: ``stats --json`` shows non-zero TX rate within N seconds.

``StopTrafficAction``
    Wraps ``spirent_tool.py stop``. Pre: traffic running.

``BgpPeerAction``
    Wraps ``spirent_tool.py bgp-peer``. Pre: emulated device exists. Post:
    ``bgp-status --json`` shows ESTABLISHED within ``wait_established_sec``.

``EcmpBlockAction``
    Wraps ``spirent_tool.py ecmp``. Pre: port reserved. Post: ``N`` peers
    visible in ``bgp-status --json``; optional ``wait_established``.

``CreateMacBlockAction``
    Wraps ``spirent_tool.py create-device`` with ``--device-count`` and
    ``--mac-step`` to emulate N L2 devices behind one AC. Pre: port reserved.
    Post: device name appears in ``status --json``.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .base_action import BaseAction, RecoverableError
from .base_validation import BaseValidation
from .spirent_watchdog import SpirentCmdResult, SpirentWatchdog

logger = logging.getLogger(__name__)

__all__ = [
    "BgpPeerAction",
    "CreateMacBlockAction",
    "CreateStreamAction",
    "EcmpBlockAction",
    "SpirentCommandAction",
    "StartTrafficAction",
    "StopTrafficAction",
    "ValidateBgpEstablished",
    "ValidateDeviceExists",
    "ValidatePortReserved",
    "ValidateStreamExists",
    "ValidateTrafficRunning",
    "ValidateTxRateAbove",
    "default_spirent_tool_path",
    "spirent_status_json",
]


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def default_spirent_tool_path() -> str:
    """Return the absolute path to ``spirent_tool.py``.

    Looks first at ``SPIRENT_TOOL`` env var, then walks common checkout
    locations. If no candidate exists, falls back to the logical
    ``~/SCALER/SPIRENT/spirent_tool.py`` so misconfiguration shows up as a
    clean ``FileNotFoundError`` instead of a cryptic ``spirent_tool: command
    not found``.
    """
    env = os.environ.get("SPIRENT_TOOL")
    if env and Path(env).exists():
        return env
    candidates = [
        Path.home() / "SCALER" / "SPIRENT" / "spirent_tool.py",
        Path("/home/dn/drivenets-topology-studio/scaler/SPIRENT/spirent_tool.py"),
        Path(__file__).resolve().parents[3] / "SPIRENT" / "spirent_tool.py",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return str(Path.home() / "SCALER" / "SPIRENT" / "spirent_tool.py")


def _run_direct(
    argv: Sequence[str],
    tool: str,
    timeout: int = 120,
) -> SpirentCmdResult:
    """Run ``spirent_tool.py <argv>`` directly (no watchdog).

    Returned ``SpirentCmdResult`` mirrors the shape produced by the watchdog
    so downstream validations don't care which path was taken.
    """
    cmd = [sys.executable, tool, *list(argv)]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
        )
        return SpirentCmdResult(
            rc=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            attempts=1,
            healed=False,
            command=list(cmd),
        )
    except subprocess.TimeoutExpired as exc:
        return SpirentCmdResult(
            rc=124,
            stdout=exc.stdout or "",
            stderr=(exc.stderr or "") + f"\n[timeout after {timeout}s]",
            attempts=1,
            healed=False,
            command=list(cmd),
        )


def spirent_status_json(
    tool: Optional[str] = None,
    *,
    watchdog: Optional[SpirentWatchdog] = None,
    live: bool = False,
) -> Dict[str, Any]:
    """Read current Spirent session status as a dict (best-effort).

    Used by several validations; centralised here so every caller parses the
    exact same shape.
    """
    argv: List[str] = ["status", "--json"]
    if live:
        argv.insert(1, "--live")
    if watchdog is not None:
        res = watchdog.guarded_run(argv)
    else:
        res = _run_direct(argv, tool or default_spirent_tool_path())
    if res.rc != 0:
        return {"_error": (res.stderr or "").strip() or f"rc={res.rc}"}
    try:
        return json.loads(res.stdout) if res.stdout.strip() else {}
    except json.JSONDecodeError as exc:
        return {"_error": f"unparseable status JSON: {exc}"}


def _looks_recoverable(result: SpirentCmdResult) -> bool:
    """Classify Spirent CLI failures as recoverable or fatal.

    Recoverable = session died, port lost, Lab Server 404, stcweb crash.
    Fatal = user-error (bad args), orchestrator bug (bad YAML), missing file.
    """
    blob = ((result.stdout or "") + "\n" + (result.stderr or "")).lower()
    recoverable_markers = (
        "session_not_found",
        "port not reserved",
        "connection refused",
        "lab server",
        "stcweb",
        "broken pipe",
        "timed out",
        "404 not found",
        "the remote end closed",
        "could not connect",
        "session dead",
    )
    return any(m in blob for m in recoverable_markers)


# ---------------------------------------------------------------------------
# Typed Spirent validations (plug into BaseAction default_pre/post lists)
# ---------------------------------------------------------------------------

class _SpirentStatusMixin(BaseValidation):
    """Base for validations that read ``spirent_tool.py status --json``.

    Subclasses call :meth:`_get_status` to receive a parsed dict. When the
    status call itself fails, validation short-circuits as FAILED with a
    descriptive message (no need to raise).
    """
    should_connect_cli = False

    def __init__(
        self,
        *,
        watchdog: Optional[SpirentWatchdog] = None,
        spirent_tool: Optional[str] = None,
        status_ttl_sec: float = 1.5,
        use_live: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.watchdog = watchdog
        self.spirent_tool = spirent_tool
        self.status_ttl_sec = status_ttl_sec
        self.use_live = use_live
        self._status_cache: Dict[str, Any] = {}
        self._status_cache_at: float = 0.0

    def _get_status(self) -> Dict[str, Any]:
        now = time.time()
        if self._status_cache and (now - self._status_cache_at) < self.status_ttl_sec:
            return self._status_cache
        self._status_cache = spirent_status_json(
            self.spirent_tool, watchdog=self.watchdog, live=self.use_live,
        )
        self._status_cache_at = now
        return self._status_cache


class ValidatePortReserved(_SpirentStatusMixin):
    """PASS when the configured port is reserved on the Lab Server."""

    def _validate(self) -> bool:
        status = self._get_status()
        if "_error" in status:
            self._collected["status_error"] = status["_error"]
            return False
        port = status.get("port") or {}
        reserved = bool(port.get("reserved"))
        self._collected["port"] = port
        return reserved


class ValidateStreamExists(_SpirentStatusMixin):
    """PASS when a stream with the given ``stream_name`` appears in status."""

    def __init__(self, *, stream_name: str = "", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.stream_name = stream_name

    def _validate(self) -> bool:
        target = self.stream_name or self.params.get("stream_name", "")
        if not target:
            self._collected["error"] = "no stream_name provided"
            return False
        status = self._get_status()
        if "_error" in status:
            self._collected["status_error"] = status["_error"]
            return False
        streams = status.get("streams") or []
        names = sorted({s.get("name", "") for s in streams if isinstance(s, dict) and s.get("name")})
        self._collected["stream_names"] = names
        self._collected["looking_for"] = target
        return target in names


class ValidateDeviceExists(_SpirentStatusMixin):
    """PASS when an emulated device with the given ``device_name`` exists."""

    def __init__(self, *, device_name: str = "", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.device_name = device_name

    def _validate(self) -> bool:
        target = self.device_name or self.params.get("device_name", "")
        if not target:
            self._collected["error"] = "no device_name provided"
            return False
        status = self._get_status()
        if "_error" in status:
            self._collected["status_error"] = status["_error"]
            return False
        devices = status.get("devices") or []
        names = sorted({d.get("name", "") for d in devices if isinstance(d, dict) and d.get("name")})
        self._collected["device_names"] = names
        self._collected["looking_for"] = target
        return target in names


class ValidateTrafficRunning(_SpirentStatusMixin):
    """PASS when the session shows traffic in RUNNING/STARTED state."""

    def _validate(self) -> bool:
        status = self._get_status()
        if "_error" in status:
            self._collected["status_error"] = status["_error"]
            return False
        traffic = status.get("traffic") or {}
        state = str(traffic.get("state", "")).upper()
        self._collected["traffic_state"] = state
        return state in {"RUNNING", "STARTED"}


class ValidateTxRateAbove(BaseValidation):
    """PASS when TX rate (pps or bps) exceeds a threshold, polled until timeout.

    Runs ``spirent_tool.py stats --json`` in a poll loop. The ``timeout``
    kwarg (inherited from BaseValidation) is the total wait budget; the poll
    interval is configurable via ``poll_interval_sec``.
    """
    should_connect_cli = False

    def __init__(
        self,
        *,
        min_pps: int = 0,
        min_bps: int = 0,
        poll_interval_sec: float = 0.5,
        watchdog: Optional[SpirentWatchdog] = None,
        spirent_tool: Optional[str] = None,
        stats_timeout_sec: int = 30,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.min_pps = max(0, int(min_pps))
        self.min_bps = max(0, int(min_bps))
        self.poll_interval_sec = max(0.1, float(poll_interval_sec))
        self.watchdog = watchdog
        self.spirent_tool = spirent_tool
        self.stats_timeout_sec = stats_timeout_sec

    def _validate(self) -> bool:
        end_at = time.time() + max(1.0, float(self.timeout))
        last_tx_pps = 0
        last_tx_bps = 0
        while True:
            tx_pps, tx_bps = self._read_tx()
            last_tx_pps = max(last_tx_pps, tx_pps)
            last_tx_bps = max(last_tx_bps, tx_bps)
            pps_ok = tx_pps >= self.min_pps if self.min_pps > 0 else True
            bps_ok = tx_bps >= self.min_bps if self.min_bps > 0 else True
            if pps_ok and bps_ok:
                self._collected.update({
                    "tx_pps": tx_pps,
                    "tx_bps": tx_bps,
                    "passed_threshold": True,
                })
                return True
            if time.time() >= end_at:
                self._collected.update({
                    "tx_pps": last_tx_pps,
                    "tx_bps": last_tx_bps,
                    "passed_threshold": False,
                    "min_pps": self.min_pps,
                    "min_bps": self.min_bps,
                })
                return False
            time.sleep(self.poll_interval_sec)

    def _read_tx(self) -> Tuple[int, int]:
        argv: List[str] = ["stats", "--json"]
        if self.watchdog is not None:
            res = self.watchdog.guarded_run(argv)
        else:
            res = _run_direct(
                argv, self.spirent_tool or default_spirent_tool_path(),
                timeout=self.stats_timeout_sec,
            )
        if res.rc != 0 or not (res.stdout or "").strip():
            return 0, 0
        try:
            stats = json.loads(res.stdout)
        except json.JSONDecodeError:
            return 0, 0
        port = stats.get("port") or stats.get("tx") or {}
        tx_pps = int(port.get("tx_fps", port.get("tx_pps", 0)) or 0)
        tx_bps = int(port.get("tx_bps", port.get("tx_l1_bps", 0)) or 0)
        return tx_pps, tx_bps


class ValidateBgpEstablished(BaseValidation):
    """PASS when enough BGP peers reach ESTABLISHED within the timeout.

    Uses ``spirent_tool.py bgp-status --json``. If ``verify_dut=True`` the
    validation additionally passes ``--verify-dut`` for ground truth (STC
    state is sometimes stale after a port flap).
    """
    should_connect_cli = False

    def __init__(
        self,
        *,
        device_name: Optional[str] = None,
        min_established: int = 1,
        verify_dut: bool = False,
        poll_interval_sec: float = 2.0,
        watchdog: Optional[SpirentWatchdog] = None,
        spirent_tool: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.device_name = device_name
        self.min_established = max(1, int(min_established))
        self.verify_dut = bool(verify_dut)
        self.poll_interval_sec = max(0.5, float(poll_interval_sec))
        self.watchdog = watchdog
        self.spirent_tool = spirent_tool

    def _validate(self) -> bool:
        end_at = time.time() + max(1.0, float(self.timeout))
        last_count = 0
        last_states: List[str] = []
        while True:
            count, states = self._count_established()
            last_count = max(last_count, count)
            last_states = states or last_states
            if count >= self.min_established:
                self._collected.update({
                    "established": count,
                    "states": states,
                })
                return True
            if time.time() >= end_at:
                self._collected.update({
                    "established": last_count,
                    "states": last_states,
                    "needed": self.min_established,
                })
                return False
            time.sleep(self.poll_interval_sec)

    def _count_established(self) -> Tuple[int, List[str]]:
        argv: List[str] = ["bgp-status", "--json"]
        if self.device_name:
            argv += ["--device-name", self.device_name]
        if self.verify_dut:
            argv += ["--verify-dut"]
        if self.watchdog is not None:
            res = self.watchdog.guarded_run(argv)
        else:
            res = _run_direct(argv, self.spirent_tool or default_spirent_tool_path())
        if res.rc != 0 or not (res.stdout or "").strip():
            return 0, []
        try:
            data = json.loads(res.stdout)
        except json.JSONDecodeError:
            return 0, []
        peers = data.get("peers") or data.get("sessions") or []
        if not isinstance(peers, list):
            return 0, []
        states: List[str] = [str(p.get("state", "")).upper() for p in peers]
        established = sum(1 for s in states if s == "ESTABLISHED")
        return established, states


# ---------------------------------------------------------------------------
# Base Spirent action
# ---------------------------------------------------------------------------

class SpirentCommandAction(BaseAction):
    """Run a generic ``spirent_tool.py <subcommand>`` through the FSM stack.

    Subclasses override :meth:`_build_argv` to set the subcommand and flags.
    The action runs the command via the shared watchdog when injected, so
    a Lab Server hiccup is automatically classified by the FSM and the
    scenario runner can apply stop-fail-retry.
    """
    should_connect_cli = False

    def __init__(
        self,
        *,
        watchdog: Optional[SpirentWatchdog] = None,
        spirent_tool: Optional[str] = None,
        command_timeout_sec: int = 300,
        dry_run: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.watchdog = watchdog
        self.spirent_tool = spirent_tool
        self.command_timeout_sec = command_timeout_sec
        self.dry_run = dry_run

    def _resolved_tool(self) -> str:
        return self.spirent_tool or default_spirent_tool_path()

    def _build_argv(self) -> List[str]:
        raise NotImplementedError

    def describe_command(self) -> str:
        """Return a human-friendly representation of the CLI call."""
        try:
            return "spirent_tool.py " + " ".join(self._build_argv())
        except NotImplementedError:
            return type(self).__name__

    def get_action_outputs(self) -> Dict[str, Any]:
        """Expose common fields so post-validations can read them via set_params."""
        return {"action_name": self.name}

    def _execute_action(self) -> Dict[str, Any]:
        argv = list(self._build_argv())
        if self.dry_run:
            return {
                "dry_run": True,
                "argv": argv,
                "repr": f"spirent_tool.py {' '.join(argv)}",
            }

        if self.watchdog is not None:
            result = self.watchdog.guarded_run(argv)
        else:
            result = _run_direct(
                argv, self._resolved_tool(), timeout=self.command_timeout_sec,
            )

        payload: Dict[str, Any] = {
            "argv": argv,
            "rc": result.rc,
            "returncode": result.rc,
            "stdout": (result.stdout or "")[:8000],
            "stderr": (result.stderr or "")[:8000],
            "attempts": result.attempts,
            "healed": result.healed,
        }

        if result.rc != 0:
            if _looks_recoverable(result):
                raise RecoverableError(
                    "spirent_tool.py %s failed (rc=%d); treating as recoverable"
                    % (" ".join(argv), result.rc)
                )
            raise RuntimeError(
                "spirent_tool.py %s failed (rc=%d): %s"
                % (
                    " ".join(argv),
                    result.rc,
                    ((result.stderr or result.stdout) or "").strip()[:500],
                )
            )
        return payload


# ---------------------------------------------------------------------------
# Concrete actions
# ---------------------------------------------------------------------------

class CreateStreamAction(SpirentCommandAction):
    """Create a traffic stream.

    Wraps ``spirent_tool.py create-stream`` with the most common flags used
    by recipes. Unused fields are simply omitted from the argv so the
    spirent_tool CLI defaults apply.
    """

    def __init__(
        self,
        *,
        stream_name: str,
        vlan: Optional[int] = None,
        src_mac: Optional[str] = None,
        dst_mac: Optional[str] = None,
        src_ip: Optional[str] = None,
        dst_ip: Optional[str] = None,
        rate_mbps: Optional[float] = None,
        rate_pps: Optional[int] = None,
        frame_size: Optional[int] = None,
        inner_vlan: Optional[int] = None,
        no_qinq: bool = False,
        protocol: Optional[str] = None,
        exclude_inner_vlans: Optional[str] = None,
        watchdog: Optional[SpirentWatchdog] = None,
        spirent_tool: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        if not stream_name:
            raise ValueError("CreateStreamAction.stream_name is required")
        super().__init__(watchdog=watchdog, spirent_tool=spirent_tool, **kwargs)
        self.stream_name = stream_name
        self.vlan = vlan
        self.src_mac = src_mac
        self.dst_mac = dst_mac
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.rate_mbps = rate_mbps
        self.rate_pps = rate_pps
        self.frame_size = frame_size
        self.inner_vlan = inner_vlan
        self.no_qinq = no_qinq
        self.protocol = protocol
        self.exclude_inner_vlans = exclude_inner_vlans

        if not self._pre_validations:
            self.add_pre_validation(
                ValidatePortReserved(
                    watchdog=self.watchdog, spirent_tool=self.spirent_tool,
                    name="port_reserved",
                )
            )
        if not self._post_validations:
            self.add_post_validation(
                ValidateStreamExists(
                    stream_name=self.stream_name,
                    watchdog=self.watchdog, spirent_tool=self.spirent_tool,
                    name=f"stream_exists[{self.stream_name}]",
                )
            )

    def get_action_outputs(self) -> Dict[str, Any]:
        return {"stream_name": self.stream_name, "action_name": self.name}

    def _build_argv(self) -> List[str]:
        argv: List[str] = ["create-stream", "--name", self.stream_name]
        if self.vlan is not None:
            argv += ["--vlan", str(self.vlan)]
        if self.inner_vlan is not None:
            argv += ["--inner-vlan", str(self.inner_vlan)]
        if self.no_qinq:
            argv += ["--no-qinq"]
        if self.exclude_inner_vlans:
            argv += ["--exclude-inner-vlans", str(self.exclude_inner_vlans)]
        if self.src_mac:
            argv += ["--src-mac", self.src_mac]
        if self.dst_mac:
            argv += ["--dst-mac", self.dst_mac]
        if self.src_ip:
            argv += ["--src-ip", self.src_ip]
        if self.dst_ip:
            argv += ["--dst-ip", self.dst_ip]
        if self.rate_mbps is not None:
            argv += ["--rate-mbps", str(self.rate_mbps)]
        if self.rate_pps is not None:
            argv += ["--rate-pps", str(self.rate_pps)]
        if self.frame_size is not None:
            argv += ["--frame-size", str(self.frame_size)]
        if self.protocol:
            argv += ["--protocol", self.protocol]
        return argv


class StartTrafficAction(SpirentCommandAction):
    """Start traffic generation (optionally on a single stream).

    Pre: at least one stream exists. Post: TX rate is above the threshold
    within ``wait_tx_sec`` seconds.
    """

    def __init__(
        self,
        *,
        stream_name: Optional[str] = None,
        min_tx_pps: int = 1,
        wait_tx_sec: int = 5,
        post_poll_interval_sec: float = 0.5,
        watchdog: Optional[SpirentWatchdog] = None,
        spirent_tool: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(watchdog=watchdog, spirent_tool=spirent_tool, **kwargs)
        self.stream_name = stream_name
        self.min_tx_pps = max(0, int(min_tx_pps))
        self.wait_tx_sec = max(1, int(wait_tx_sec))
        self.post_poll_interval_sec = max(0.1, float(post_poll_interval_sec))

        if not self._pre_validations:
            self.add_pre_validation(
                ValidatePortReserved(
                    watchdog=self.watchdog, spirent_tool=self.spirent_tool,
                    name="port_reserved",
                )
            )
            if self.stream_name:
                self.add_pre_validation(
                    ValidateStreamExists(
                        stream_name=self.stream_name,
                        watchdog=self.watchdog, spirent_tool=self.spirent_tool,
                        name=f"stream_exists[{self.stream_name}]",
                    )
                )
        if not self._post_validations:
            self.add_post_validation(
                ValidateTxRateAbove(
                    min_pps=self.min_tx_pps,
                    timeout=self.wait_tx_sec,
                    poll_interval_sec=self.post_poll_interval_sec,
                    watchdog=self.watchdog, spirent_tool=self.spirent_tool,
                    name="tx_rate_above_zero",
                )
            )

    def _build_argv(self) -> List[str]:
        argv = ["start"]
        if self.stream_name:
            argv += ["--stream-name", self.stream_name]
        return argv


class StopTrafficAction(SpirentCommandAction):
    """Stop traffic generation.

    Pre: traffic reported RUNNING. (No post-validation by default; use
    ValidateTxRateAbove with min_pps=0 if you want to assert decay.)
    """

    def __init__(
        self,
        *,
        watchdog: Optional[SpirentWatchdog] = None,
        spirent_tool: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(watchdog=watchdog, spirent_tool=spirent_tool, **kwargs)
        if not self._pre_validations:
            self.add_pre_validation(
                ValidateTrafficRunning(
                    watchdog=self.watchdog, spirent_tool=self.spirent_tool,
                    name="traffic_running",
                )
            )

    def _build_argv(self) -> List[str]:
        return ["stop"]


class BgpPeerAction(SpirentCommandAction):
    """Configure and start a BGP session on one emulated device.

    Post-validation waits ``wait_established_sec`` for the session to reach
    ESTABLISHED via ``spirent_tool.py bgp-status``.
    """

    def __init__(
        self,
        *,
        device_name: str,
        as_num: int,
        dut_as: int,
        neighbor: Optional[str] = None,
        hold_timer: Optional[int] = None,
        keepalive: Optional[int] = None,
        afi: Optional[str] = None,
        negotiate_afi: Optional[str] = None,
        no_start: bool = False,
        evpn_rd: Optional[str] = None,
        evpn_rt: Optional[str] = None,
        wait_established_sec: int = 60,
        verify_dut: bool = False,
        watchdog: Optional[SpirentWatchdog] = None,
        spirent_tool: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        if not device_name:
            raise ValueError("BgpPeerAction.device_name is required")
        super().__init__(watchdog=watchdog, spirent_tool=spirent_tool, **kwargs)
        self.device_name = device_name
        self.as_num = int(as_num)
        self.dut_as = int(dut_as)
        self.neighbor = neighbor
        self.hold_timer = hold_timer
        self.keepalive = keepalive
        self.afi = afi
        self.negotiate_afi = negotiate_afi
        self.no_start = bool(no_start)
        self.evpn_rd = evpn_rd
        self.evpn_rt = evpn_rt
        self.wait_established_sec = max(1, int(wait_established_sec))
        self.verify_dut = bool(verify_dut)

        if not self._pre_validations:
            self.add_pre_validation(
                ValidatePortReserved(
                    watchdog=self.watchdog, spirent_tool=self.spirent_tool,
                    name="port_reserved",
                )
            )
            self.add_pre_validation(
                ValidateDeviceExists(
                    device_name=self.device_name,
                    watchdog=self.watchdog, spirent_tool=self.spirent_tool,
                    name=f"device_exists[{self.device_name}]",
                )
            )
        if not self._post_validations and not self.no_start:
            self.add_post_validation(
                ValidateBgpEstablished(
                    device_name=self.device_name,
                    min_established=1,
                    timeout=self.wait_established_sec,
                    verify_dut=self.verify_dut,
                    watchdog=self.watchdog, spirent_tool=self.spirent_tool,
                    name=f"bgp_established[{self.device_name}]",
                )
            )

    def get_action_outputs(self) -> Dict[str, Any]:
        return {
            "device_name": self.device_name,
            "as_num": self.as_num,
            "dut_as": self.dut_as,
            "action_name": self.name,
        }

    def _build_argv(self) -> List[str]:
        argv: List[str] = [
            "bgp-peer",
            "--device-name", self.device_name,
            "--as", str(self.as_num),
            "--dut-as", str(self.dut_as),
        ]
        if self.neighbor:
            argv += ["--neighbor", self.neighbor]
        if self.hold_timer is not None:
            argv += ["--hold-timer", str(self.hold_timer)]
        if self.keepalive is not None:
            argv += ["--keepalive", str(self.keepalive)]
        if self.afi:
            argv += ["--afi", self.afi]
        if self.negotiate_afi:
            argv += ["--negotiate-afi", self.negotiate_afi]
        if self.evpn_rd:
            argv += ["--evpn-rd", self.evpn_rd]
        if self.evpn_rt:
            argv += ["--evpn-rt", self.evpn_rt]
        if self.no_start:
            argv += ["--no-start"]
        return argv


class EcmpBlockAction(SpirentCommandAction):
    """Create a block of N ECMP BGP peers via STC Device Block multiplier.

    Pre: port reserved. Post: at least ``min_established`` of the ``count``
    peers reach ESTABLISHED within ``wait_established_sec`` seconds.
    """

    def __init__(
        self,
        *,
        count: int,
        vlan: Optional[int] = None,
        inner_vlan: Optional[int] = None,
        base_ip: Optional[str] = None,
        ip_step: Optional[str] = None,
        mac: Optional[str] = None,
        mac_step: Optional[str] = None,
        gateway: Optional[str] = None,
        prefix: Optional[str] = None,
        route_count: Optional[int] = None,
        as_num: Optional[int] = None,
        dut_as: Optional[int] = None,
        negotiate_afi: Optional[str] = None,
        wait_established_sec: int = 120,
        min_established: Optional[int] = None,
        gen_dut_config: bool = False,
        clean_stale: bool = True,
        watchdog: Optional[SpirentWatchdog] = None,
        spirent_tool: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        if int(count) <= 0:
            raise ValueError("EcmpBlockAction.count must be positive")
        super().__init__(watchdog=watchdog, spirent_tool=spirent_tool, **kwargs)
        self.count = int(count)
        self.vlan = vlan
        self.inner_vlan = inner_vlan
        self.base_ip = base_ip
        self.ip_step = ip_step
        self.mac = mac
        self.mac_step = mac_step
        self.gateway = gateway
        self.prefix = prefix
        self.route_count = route_count
        self.as_num = as_num
        self.dut_as = dut_as
        self.negotiate_afi = negotiate_afi
        self.wait_established_sec = max(0, int(wait_established_sec))
        self.min_established = self.count if min_established is None else int(min_established)
        self.gen_dut_config = bool(gen_dut_config)
        self.clean_stale = bool(clean_stale)

        if not self._pre_validations:
            self.add_pre_validation(
                ValidatePortReserved(
                    watchdog=self.watchdog, spirent_tool=self.spirent_tool,
                    name="port_reserved",
                )
            )
        if not self._post_validations and self.wait_established_sec > 0:
            self.add_post_validation(
                ValidateBgpEstablished(
                    min_established=self.min_established,
                    timeout=self.wait_established_sec,
                    watchdog=self.watchdog, spirent_tool=self.spirent_tool,
                    name="ecmp_block_established",
                )
            )

    def _build_argv(self) -> List[str]:
        argv: List[str] = ["ecmp", "--count", str(self.count)]
        if self.vlan is not None:
            argv += ["--vlan", str(self.vlan)]
        if self.inner_vlan is not None:
            argv += ["--inner-vlan", str(self.inner_vlan)]
        if self.base_ip:
            argv += ["--base-ip", self.base_ip]
        if self.ip_step:
            argv += ["--ip-step", str(self.ip_step)]
        if self.mac:
            argv += ["--mac", self.mac]
        if self.mac_step:
            argv += ["--mac-step", str(self.mac_step)]
        if self.gateway:
            argv += ["--gateway", self.gateway]
        if self.prefix:
            argv += ["--prefix", self.prefix]
        if self.route_count is not None:
            argv += ["--route-count", str(self.route_count)]
        if self.as_num is not None:
            argv += ["--as", str(self.as_num)]
        if self.dut_as is not None:
            argv += ["--dut-as", str(self.dut_as)]
        if self.negotiate_afi:
            argv += ["--negotiate-afi", self.negotiate_afi]
        if self.wait_established_sec:
            argv += ["--wait-established", str(self.wait_established_sec)]
        if self.gen_dut_config:
            argv += ["--gen-dut-config"]
        if self.clean_stale:
            argv += ["--clean-stale"]
        return argv


class CreateMacBlockAction(SpirentCommandAction):
    """Create an L2 device block on a VLAN (= one DUT AC).

    Wraps ``spirent_tool.py create-device`` with ``--device-count`` and
    ``--mac-step`` to emulate N L2 devices behind one AC. Supports Q-in-Q
    (pass ``outer_vlan`` to make ``vlan`` the inner VLAN).

    Post-validation: the device name is present in ``status --json``.
    """

    def __init__(
        self,
        *,
        device_name: str,
        vlan: int,
        count: int = 1,
        base_mac: str = "00:DE:AD:00:01:01",
        base_ip: str = "10.99.0.10",
        gateway: str = "10.99.0.1",
        prefix_len: int = 24,
        outer_vlan: Optional[int] = None,
        mac_step: str = "00:00:00:00:00:01",
        ip_step: str = "1",
        no_qinq: bool = True,
        exclude_inner_vlans: Optional[str] = None,
        watchdog: Optional[SpirentWatchdog] = None,
        spirent_tool: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        if not device_name:
            raise ValueError("CreateMacBlockAction.device_name is required")
        if int(count) <= 0:
            raise ValueError("CreateMacBlockAction.count must be positive")
        super().__init__(watchdog=watchdog, spirent_tool=spirent_tool, **kwargs)
        self.device_name = device_name
        self.vlan = int(vlan)
        self.count = int(count)
        self.base_mac = base_mac
        self.base_ip = base_ip
        self.gateway = gateway
        self.prefix_len = int(prefix_len)
        self.outer_vlan = outer_vlan
        self.mac_step = mac_step
        self.ip_step = ip_step
        self.no_qinq = bool(no_qinq)
        self.exclude_inner_vlans = exclude_inner_vlans

        if not self._pre_validations:
            self.add_pre_validation(
                ValidatePortReserved(
                    watchdog=self.watchdog, spirent_tool=self.spirent_tool,
                    name="port_reserved",
                )
            )
        if not self._post_validations:
            self.add_post_validation(
                ValidateDeviceExists(
                    device_name=self.device_name,
                    watchdog=self.watchdog, spirent_tool=self.spirent_tool,
                    name=f"device_exists[{self.device_name}]",
                )
            )

    def get_action_outputs(self) -> Dict[str, Any]:
        return {
            "device_name": self.device_name,
            "vlan": self.vlan,
            "count": self.count,
            "action_name": self.name,
        }

    def _build_argv(self) -> List[str]:
        argv: List[str] = [
            "create-device",
            "--name", self.device_name,
            "--ip", self.base_ip,
            "--gateway", self.gateway,
            "--prefix-len", str(self.prefix_len),
            "--mac", self.base_mac,
            "--mac-step", self.mac_step,
            "--ip-step", str(self.ip_step),
            "--device-count", str(self.count),
        ]
        if self.outer_vlan is not None:
            argv += ["--vlan", str(self.outer_vlan), "--inner-vlan", str(self.vlan)]
        else:
            argv += ["--vlan", str(self.vlan)]
            if self.no_qinq:
                argv += ["--no-qinq"]
        if self.exclude_inner_vlans:
            argv += ["--exclude-inner-vlans", self.exclude_inner_vlans]
        return argv
