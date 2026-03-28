#!/usr/bin/env python3
"""
vtysh deep access runner for DNOS test automation.

Provides access to FRR/Quagga vtysh shell on DNOS devices for deep
inspection of internal routing tables, zebra DB, flowspec DB, and RIB.

Enters vtysh via the standard InteractiveSSHSession by sending the
'vtysh' command in the routing container, then executes show commands
within the vtysh context.

Usage:
    runner = VtyshRunner(device, run_show, credentials)
    result = runner.run_vtysh_command("show bgp l2vpn evpn")
    runner.close()
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("vtysh_runner")

RunShowFn = Callable[[str, str], str]

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

VTYSH_ENTRY_CMD = "run container-shell ncc {ncc_id} routing vtysh"

VTYSH_PROMPT_RE = re.compile(r"[\w\-]+[#>]\s*$", re.MULTILINE)


@dataclass
class VtyshResult:
    """Result of one vtysh command execution."""
    command: str
    output: str
    success: bool = True
    error: Optional[str] = None
    duration_ms: int = 0


class VtyshRunner:
    """Execute vtysh commands on a DNOS device via SSH.

    Uses InteractiveSSHSession for prompt-based completion.
    Falls back to wrapping vtysh commands via the DNOS CLI pipe syntax.
    """

    def __init__(
        self,
        device: str,
        run_show: RunShowFn,
        ncc_id: str = "0",
    ):
        self.device = device
        self.run_show = run_show
        self.ncc_id = ncc_id
        self._direct_session = None

    def run_vtysh_command(self, command: str) -> VtyshResult:
        """Execute a vtysh command and return the result.

        Strategy:
          1. Try wrapping via DNOS CLI: run container-shell command
          2. Fall back to pipe-based execution
        """
        t0 = time.monotonic()

        # Strategy 1: Execute via container-shell
        result = self._run_via_container_shell(command)
        if result.success:
            result.duration_ms = int((time.monotonic() - t0) * 1000)
            return result

        # Strategy 2: Try direct vtysh command with ncp prefix
        result = self._run_via_ncp_vtysh(command)
        result.duration_ms = int((time.monotonic() - t0) * 1000)
        return result

    def run_vtysh_batch(self, commands: List[str]) -> List[VtyshResult]:
        """Execute multiple vtysh commands in sequence."""
        return [self.run_vtysh_command(cmd) for cmd in commands]

    def close(self) -> None:
        """Clean up any direct SSH sessions."""
        if self._direct_session:
            try:
                self._direct_session.close()
            except Exception:
                pass
            self._direct_session = None

    def _run_via_container_shell(self, command: str) -> VtyshResult:
        """Execute vtysh command via container-shell."""
        full_cmd = (
            f"run container-shell ncc {self.ncc_id} routing "
            f"vtysh -c \"{command}\" | no-more"
        )
        try:
            output = self.run_show(self.device, full_cmd)
            clean = _ANSI_RE.sub("", output).strip()
            if "error" in clean.lower()[:50] or "command not found" in clean.lower():
                return VtyshResult(command=command, output=clean, success=False,
                                   error="container-shell vtysh failed")
            return VtyshResult(command=command, output=clean, success=True)
        except Exception as exc:
            return VtyshResult(command=command, output="", success=False, error=str(exc))

    def _run_via_ncp_vtysh(self, command: str) -> VtyshResult:
        """Fallback: try running vtysh command via NCP."""
        full_cmd = (
            f"run container-shell ncp {self.ncc_id} routing "
            f"vtysh -c \"{command}\" | no-more"
        )
        try:
            output = self.run_show(self.device, full_cmd)
            clean = _ANSI_RE.sub("", output).strip()
            return VtyshResult(command=command, output=clean, success=True)
        except Exception as exc:
            return VtyshResult(command=command, output="", success=False, error=str(exc))


# ---------------------------------------------------------------------------
# Convenience functions (feature-agnostic)
# ---------------------------------------------------------------------------

def get_zebra_rib(
    device: str,
    run_show: RunShowFn,
    vrf: str = "default",
    ncc_id: str = "0",
) -> VtyshResult:
    """Get zebra RIB (routing information base)."""
    runner = VtyshRunner(device, run_show, ncc_id)
    cmd = f"show ip route vrf {vrf}" if vrf != "default" else "show ip route"
    result = runner.run_vtysh_command(cmd)
    runner.close()
    return result


def get_bgp_evpn_vtysh(
    device: str,
    run_show: RunShowFn,
    ncc_id: str = "0",
) -> VtyshResult:
    """Get BGP L2VPN EVPN table via vtysh."""
    runner = VtyshRunner(device, run_show, ncc_id)
    result = runner.run_vtysh_command("show bgp l2vpn evpn")
    runner.close()
    return result


def get_evpn_vni(
    device: str,
    run_show: RunShowFn,
    ncc_id: str = "0",
) -> VtyshResult:
    """Get EVPN VNI information via vtysh."""
    runner = VtyshRunner(device, run_show, ncc_id)
    result = runner.run_vtysh_command("show evpn vni")
    runner.close()
    return result
