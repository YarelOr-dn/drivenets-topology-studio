#!/usr/bin/env python3
"""
ha_executor.py -- Lightweight SSH executor for /HA device configuration and operational commands.

Used by /HA when Network Mapper MCP only supports show commands. Handles:
- Operational commands: request system restart, clear bgp, set logging terminal, etc.
- Config changes: configure -> lines -> commit check -> commit -> exit
- Device verification: SSH + System Name + Serial Number check
- Debug flag tracking and auto-cleanup

Credentials from ~/SCALER/db/devices.json (base64 password decode).
Falls back to ConfigPusher for complex multi-block configs.

Usage (programmatic):
    from ha_executor import HAExecutor
    ex = HAExecutor()
    ex.connect("PE-4")
    ex.verify_device("YOR_CL_PE-4")
    ex.run_operational("set logging terminal")
    ex.run_config(["interfaces ge400-0/0/1 admin-state enabled"])
    ex.cleanup()
    ex.disconnect()
"""

import base64
import json
import re
import sys
import time
from pathlib import Path

HA_DIR = Path(__file__).parent
SCALER_DB = Path.home() / "SCALER" / "db" / "devices.json"

# Device alias: user says "PE-4" but DB has "YOR_CL_PE-4"
DEVICE_ALIASES = {"PE-4": "YOR_CL_PE-4", "PE4": "YOR_CL_PE-4"}

try:
    from .ha_ssh import run_ssh_shell
except ImportError:
    from ha_ssh import run_ssh_shell


def load_device(hostname: str) -> dict:
    """Load device from SCALER db (devices.json). Supports partial hostname match."""
    if not SCALER_DB.exists():
        raise FileNotFoundError(f"SCALER db not found: {SCALER_DB}")
    hostname = DEVICE_ALIASES.get(hostname.upper().replace(" ", ""), hostname)
    with open(SCALER_DB) as f:
        data = json.load(f)
    # Exact match first
    for d in data.get("devices", []):
        if d.get("hostname", "").upper() == hostname.upper():
            return _device_from_db(d)
    # Partial match (hostname ends with or contains)
    for d in data.get("devices", []):
        h = d.get("hostname", "")
        if hostname.upper() in h.upper() or h.upper().endswith(hostname.upper()):
            return _device_from_db(d)
    raise ValueError(f"Device {hostname} not found in {SCALER_DB}")


def _device_from_db(d: dict) -> dict:
    pw = d.get("password", "dnroot")
    if pw:
        try:
            pw = base64.b64decode(pw).decode("utf-8")
        except Exception:
            pass
    return {
        "hostname": d["hostname"],
        "ip": d["ip"],
        "username": d.get("username", "dnroot"),
        "password": pw,
    }


class HAExecutor:
    """Lightweight SSH executor for HA testing. Tracks debug flags for cleanup."""

    def __init__(self, session_log_path: str | Path | None = None, dry_run: bool = False):
        self.device: dict | None = None
        self._ssh = None
        self._chan = None
        self._session_log_path = Path(session_log_path) if session_log_path else None
        self._dry_run = dry_run
        self._debug_flags_enabled: list[str] = []
        self._logging_terminal_enabled = False

    def _log(self, msg: str) -> None:
        """Append to session log if configured."""
        if self._session_log_path:
            self._session_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._session_log_path, "a") as f:
                f.write(msg + "\n")

    def connect(self, device_name: str) -> dict:
        """Resolve device from SCALER DB, establish SSH. Returns device dict."""
        self.device = load_device(device_name)
        # For persistent connection we use one-shot shell; connect() just validates
        out = run_ssh_shell(
            self.device["ip"],
            self.device["username"],
            self.device["password"],
            ["show system version"],
            timeout=15,
        )
        self._log(f"[ha_executor] Connected to {self.device['hostname']} ({self.device['ip']})")
        return self.device

    def run_show(self, cmd: str, timeout: int = 30) -> str:
        """Run show command via SSH. Fallback when Network Mapper unavailable."""
        if not self.device:
            raise RuntimeError("Not connected. Call connect() first.")
        if self._dry_run:
            return f"DRY-RUN: {cmd}"
        out = run_ssh_shell(
            self.device["ip"],
            self.device["username"],
            self.device["password"],
            [cmd],
            timeout=timeout,
        )
        self._log(f"[ha_executor] run_show: {cmd[:60]}...")
        return out

    def run_operational(self, cmd: str, timeout: int = 60) -> str:
        """Run operational command (request system restart, clear bgp, set logging terminal, etc.)."""
        if not self.device:
            raise RuntimeError("Not connected. Call connect() first.")
        if self._dry_run:
            return f"DRY-RUN: {cmd}"
        # Track set logging terminal for cleanup
        if "set logging terminal" in cmd and "unset" not in cmd:
            self._logging_terminal_enabled = True
        if "unset logging terminal" in cmd:
            self._logging_terminal_enabled = False
        out = run_ssh_shell(
            self.device["ip"],
            self.device["username"],
            self.device["password"],
            [cmd],
            timeout=timeout,
        )
        self._log(f"[ha_executor] run_operational: {cmd[:60]}...")
        return out

    def run_config(self, config_lines: list[str] | str, timeout: int = 90) -> str:
        """Enter config mode, apply lines, commit check, commit, exit. Aborts on validation failure."""
        if not self.device:
            raise RuntimeError("Not connected. Call connect() first.")
        if isinstance(config_lines, str):
            config_lines = [line.strip() for line in config_lines.strip().split("\n") if line.strip()]
        if self._dry_run:
            return f"DRY-RUN: config {len(config_lines)} lines"
        commands = ["configure"]
        for line in config_lines:
            if line and not line.startswith("#"):
                commands.append(line)
        commands.extend(["commit check", "commit", "exit"])
        out = run_ssh_shell(
            self.device["ip"],
            self.device["username"],
            self.device["password"],
            commands,
            timeout=timeout,
        )
        self._log(f"[ha_executor] run_config: {len(config_lines)} lines")
        if "Error" in out or "error" in out.lower():
            # commit check may have failed
            if "commit check" in "".join(commands) and "Error" in out:
                raise RuntimeError(f"Config validation failed: {out[:500]}")
        return out

    def track_debug_flag(self, flag: str) -> None:
        """Track a debug flag for later cleanup (e.g. 'bgp updates-in')."""
        self._debug_flags_enabled.append(flag)

    def verify_device(self, expected_name: str | None = None) -> dict:
        """
        Run show system version + show system, extract identity. Optionally verify against expected_name.
        Returns dict with system_name, serial_number, software_version, system_type, active_ncc, standby_ncc, etc.
        """
        if not self.device:
            raise RuntimeError("Not connected. Call connect() first.")
        out_ver = self.run_show("show system version", timeout=15)
        out_sys = self.run_show("show system", timeout=15)
        info: dict = {}
        m = re.search(r"System Name\s*:\s*(\S+)", out_ver)
        if m:
            info["system_name"] = m.group(1)
        else:
            m = re.search(r"System Serial Number\s*:\s*(\S+)", out_ver)
            info["system_name"] = m.group(1) if m else "unknown"
        m = re.search(r"System Serial Number\s*:\s*(\S+)", out_ver)
        info["serial_number"] = m.group(1) if m else ""
        m = re.search(r"Version:\s*DNOS\s*\[([^\]]+)\]", out_ver)
        info["software_version"] = m.group(1) if m else ""
        m = re.search(r"System Type\s*:\s*(\S+)", out_sys)
        info["system_type"] = m.group(1) if m else ""
        m = re.search(r"BGP NSR\s*:\s*(\S+)", out_sys)
        info["bgp_nsr"] = m.group(1) if m else ""
        # Active/standby NCC
        for line in out_sys.split("\n"):
            if "active-up" in line and "NCC" in line:
                n = re.search(r"NCC\s*\|?\s*(\d+)", line)
                if n:
                    info["active_ncc_id"] = int(n.group(1))
            if "standby-up" in line and "NCC" in line:
                n = re.search(r"NCC\s*\|?\s*(\d+)", line)
                if n:
                    info["standby_ncc_id"] = int(n.group(1))
        if expected_name and info.get("system_name") != expected_name:
            raise ValueError(
                f"Device identity mismatch! Expected '{expected_name}' but got '{info.get('system_name')}'. "
                "Management IP may point to a different device."
            )
        return info

    def cleanup(self) -> None:
        """Undo debug flags and unset logging terminal."""
        if not self.device:
            return
        if self._dry_run:
            return
        cmds = []
        for flag in self._debug_flags_enabled:
            # DNOS debug: no debug bgp updates-in
            cmds.append(f"no debug {flag}")
        if self._logging_terminal_enabled:
            cmds.append("unset logging terminal")
        if cmds:
            run_ssh_shell(
                self.device["ip"],
                self.device["username"],
                self.device["password"],
                cmds,
                timeout=30,
            )
            self._log(f"[ha_executor] cleanup: {len(cmds)} commands")
        self._debug_flags_enabled.clear()
        self._logging_terminal_enabled = False

    def disconnect(self) -> None:
        """Close connection. Call cleanup() first if needed."""
        self.device = None
        self._ssh = None
        self._chan = None

    def push_config_blocks(self, config_blocks: list[str], description: str = "") -> str:
        """
        Apply multiple config blocks (e.g. DNAAS path, full VRF). Uses run_config internally.
        For very large configs (file upload, load merge), invoke ensure_dnaas_path.py or
        scaler/config_pusher.py as subprocess instead.
        """
        if not self.device:
            raise RuntimeError("Not connected. Call connect() first.")
        lines = []
        for block in config_blocks:
            for line in block.strip().split("\n"):
                l = line.strip()
                if l and not l.startswith("#"):
                    lines.append(l)
        out = self.run_config(lines, timeout=120)
        self._log(f"[ha_executor] push_config_blocks: {description or 'config'} ({len(lines)} lines)")
        return out


def main():
    """CLI for quick device verification."""
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--device", default="PE-4")
    p.add_argument("--show", action="store_true", help="Run show system version")
    p.add_argument("--verify", action="store_true", help="Verify device identity")
    args = p.parse_args()
    ex = HAExecutor()
    ex.connect(args.device)
    if args.show:
        print(ex.run_show("show system version"))
    if args.verify:
        info = ex.verify_device()
        print(json.dumps(info, indent=2))
    ex.disconnect()


if __name__ == "__main__":
    main()
