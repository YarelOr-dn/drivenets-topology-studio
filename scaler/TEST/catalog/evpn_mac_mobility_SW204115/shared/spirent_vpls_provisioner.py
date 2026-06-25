#!/usr/bin/env python3
"""
Auto-provisioner for spirent_vpls_cp infrastructure.

Creates and validates the full MPLS tunnel + VPLS PW chain required for
PW data-plane MAC mobility tests (ac_pw, evpn_pw, pw_pw, sticky SC03-SC06).

The chain:
  1. PE-1 label pool (bgp-vpls-label-block-size)
  2. PE-1 BGP l2vpn-vpls AF
  3. PE-1 EVPN instance PW_TEST_ELAN (SI enabled, VPLS-only RT)
  4. PE-1 AC interface on DNAAS path (ge400-0/0/5.1010)
  5. PE-1 BGP neighbors for Spirent (17.17.17.2, 18.18.18.2)
  6. Spirent devices on ge400-0/0/5.3 and .4 subnets
  7. Spirent ISIS + LDP + BGP l2vpn-vpls
  8. PW(s) active (ingress labels in MPLS FIB)

STC ISIS sharing constraint (discovered 2026-04-02):
  Multiple STC emulated devices on the SAME physical port share a single
  ISIS instance. Only ONE loopback prefix survives in the ISIS LSDB.
  Both peers therefore use the SAME loopback (VPLS_SHARED_LOOPBACK) as
  their VPLS nexthop. Different VE-IDs + RDs give each PW its own unique
  ingress label. DNOS LDP only labels IGP routes (not static), so ISIS
  is mandatory for MPLS tunnel establishment.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Action+validate primitives -- replace fixed sleep loops with event-driven polls.
from .validators import poll_until
from .spirent_paths import spirent_tool_command, spirent_tool_path

logger = logging.getLogger("spirent_vpls_provisioner")

# Backwards-compat alias for legacy callers; resolved via shared.spirent_paths.
SPIRENT_TOOL = spirent_tool_path()

VPLS_SHARED_LOOPBACK = "6.6.6.6"  # Both STC devices share this ISIS loopback + VPLS nexthop
VPLS_LABEL_BLOCK_SIZE = 8
VPLS_ISIS_AREA = "49.0001"
VPLS_PEER_OUTER_VLAN = 214

VPLS_PEER_SYSTEM_ID = "0000.0000.0003"
VPLS_PEER_IP = "17.17.17.2"
VPLS_PEER_GW = "17.17.17.1"
VPLS_PEER_INNER_VLAN = 3
VPLS_DEVICE_NAME = "VPLS_PW_Peer"

VPLS_PEER2_SYSTEM_ID = "0000.0000.0006"
VPLS_PEER2_IP = "18.18.18.2"
VPLS_PEER2_GW = "18.18.18.1"
VPLS_PEER2_INNER_VLAN = 4
VPLS_DEVICE2_NAME = "VPLS_PW_Peer_2"
VPLS_PEER2_VE_ID = 3

VPLS_BGP_NEIGHBOR_IP = VPLS_PEER_IP  # 17.17.17.2 -- connected IP for BGP TCP

# Interface hints below are PE-1-specific defaults. Deployments with different
# DUTs (e.g. PE-4 with ge100-18/0/X) MUST either rely on runtime DUTProfile
# discovery (preferred) or override via env vars EVPN_MM_PW_TEST_AC_SUBIF /
# EVPN_MM_VPLS_BGP_UPDATE_SOURCE so no code edit is required.
VPLS_BGP_UPDATE_SOURCE = os.environ.get("EVPN_MM_VPLS_BGP_UPDATE_SOURCE", "ge400-0/0/5.3")

PW_TEST_EVPN_NAME = os.environ.get("EVPN_MM_PW_TEST_EVPN_NAME", "PW_TEST_ELAN")
PW_TEST_EVI = int(os.environ.get("EVPN_MM_PW_TEST_EVI", "9990"))
PW_TEST_VPLS_RT = os.environ.get("EVPN_MM_PW_TEST_VPLS_RT", "9990:9990")
PW_TEST_EVPN_RT = os.environ.get("EVPN_MM_PW_TEST_EVPN_RT", "9990:9990")
PW_TEST_SITE_ID = int(os.environ.get("EVPN_MM_PW_TEST_SITE_ID", "2"))  # within Spirent label block range (offset 1, block 8 -> VE-IDs 1-8)
PW_TEST_AC_SUBIF = os.environ.get("EVPN_MM_PW_TEST_AC_SUBIF", "ge400-0/0/5.1010")
PW_TEST_AC_OUTER = int(os.environ.get("EVPN_MM_PW_TEST_AC_OUTER", "214"))
PW_TEST_AC_INNER = int(os.environ.get("EVPN_MM_PW_TEST_AC_INNER", "1010"))
# STC adds BlkOffset(1) to VeId when encoding the wire VE-ID in the BGP VPLS NLRI.
# VeId=1 -> wire VE-ID 2, which collides with DUT site-id=2. Use VeId=3 -> wire VE-ID 3 or 4.
PW_TEST_VE_ID = 3

EVPN_PEER_SYSTEM_ID = "0000.0000.0005"
EVPN_PEER_IP = "19.19.19.2"
EVPN_PEER_GW = "19.19.19.1"
EVPN_PEER_INNER_VLAN = 5
EVPN_DEVICE_NAME = "EVPN_RT2_Peer"
EVPN_BGP_NEIGHBOR = "19.19.19.1"  # PE-1 directly connected (bypasses RR-SA-2 reflection issues)
PE1_ASN = 1234567
PE1_MGMT_IP = "100.64.4.200"

DUT_BGP_ASN = 1234567
DUT_ROUTER_ID = "1.1.1.1"


@dataclass
class DUTProfile:
    """All DUT-derived parameters needed to create perfectly-matched Spirent peers.

    Built once from resolve_runtime_params output + a few targeted show commands.
    When passed to provisioners, replaces the module-level hardcoded constants.
    When None / not passed, provisioners fall back to the constants above.
    """
    device: str = ""
    mgmt_ip: str = ""
    bgp_asn: int = DUT_BGP_ASN
    router_id: str = DUT_ROUTER_ID
    # EVPN RT-2 peer (SC02 remote MAC injection)
    evpn_neighbor_ip: str = EVPN_PEER_IP
    evpn_neighbor_gw: str = EVPN_PEER_GW
    evpn_neighbor_outer_vlan: int = VPLS_PEER_OUTER_VLAN
    evpn_neighbor_inner_vlan: int = EVPN_PEER_INNER_VLAN
    evpn_import_rt: str = ""
    evpn_export_rt: str = ""
    evpn_rd: str = ""
    evpn_evi: int = 0
    evpn_sub_if_mac: str = ""
    # VPLS PW peer (SC03 PW MAC learning)
    vpls_neighbor_ip: str = VPLS_PEER_IP
    vpls_neighbor_gw: str = VPLS_PEER_GW
    vpls_neighbor_outer_vlan: int = VPLS_PEER_OUTER_VLAN
    vpls_neighbor_inner_vlan: int = VPLS_PEER_INNER_VLAN
    vpls_import_rt: str = ""
    vpls_rd: str = ""
    vpls_site_id: int = PW_TEST_SITE_ID
    vpls_label_block_size: int = VPLS_LABEL_BLOCK_SIZE
    vpls_source_loopback: str = ""
    vpls_isis_area: str = VPLS_ISIS_AREA
    vpls_isis_interface: str = VPLS_BGP_UPDATE_SOURCE
    vpls_mpls_enabled: bool = True
    pw_test_evpn_name: str = PW_TEST_EVPN_NAME
    pw_test_evi: int = PW_TEST_EVI
    pw_test_vpls_rt: str = PW_TEST_VPLS_RT
    pw_test_evpn_rt: str = PW_TEST_EVPN_RT
    pw_test_ac_subif: str = PW_TEST_AC_SUBIF
    pw_test_ac_outer: int = PW_TEST_AC_OUTER
    pw_test_ac_inner: int = PW_TEST_AC_INNER
    pw_test_ve_id: int = PW_TEST_VE_ID
    # L2 ACs
    ac_interfaces: List[Dict[str, Any]] = field(default_factory=list)
    dut_interface_mac: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for JSON caching."""
        import dataclasses
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DUTProfile":
        """Deserialize from JSON cache."""
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in known})


@dataclass
class ProvisionResult:
    """Aggregated result of a provisioning run."""
    steps: List[Dict[str, Any]] = field(default_factory=list)
    params: Dict[str, str] = field(default_factory=dict)
    pw_active: bool = False
    ingress_label: int = 0
    protocols_deferred: bool = False
    blocker: str = ""

    @property
    def ready(self) -> bool:
        if self.protocols_deferred:
            return True
        return self.pw_active and self.ingress_label > 0

    def add(self, step_id: str, status: str, detail: str = "", **extra):
        entry = {"step": step_id, "status": status, "detail": detail}
        entry.update(extra)
        self.steps.append(entry)

    def summary_lines(self) -> List[str]:
        lines = []
        for s in self.steps:
            icon = "[OK]" if s["status"] == "PASS" else "[!!]" if s["status"] == "FAIL" else "[--]"
            lines.append(f"  {icon} {s['step']}: {s.get('detail', '')}")
        if self.ready:
            lines.append(f"  [OK] PW ACTIVE -- ingress label {self.ingress_label}")
        elif self.blocker:
            lines.append(f"  [!!] BLOCKER: {self.blocker}")
        return lines


_PROVISIONER_MUTATING = {
    "create-device", "create-stream", "vpls-stream", "remove-device",
    "remove-stream", "protocol-start", "protocol-stop",
    "bgp-peer", "ecmp", "evpn-routes", "add-routes",
    "withdraw-routes", "reserve", "connect",
    "ldp-peer", "isis-peer", "evpn-peer", "add-afi", "mac-block",
}

_SESSION_DEAD_MARKERS = (
    "No active session", "Port not reserved", "Stale handles",
    "Session not found", "Session marked inactive", "Connection refused",
    "timed out", "HTTPError", "ConnectionError",
    "404 Not Found", "session not found", "No Remote Test Session",
    "JOIN-only mode", "SpirentSessionError",
)


_DAEMON_CLIENT = None
_DAEMON_LAST_PROBE = 0.0
_DAEMON_PROBE_INTERVAL = 5.0
_DAEMON_DISABLED = os.environ.get("SPIRENT_NO_DAEMON", "").lower() in {"1", "true", "yes"}


def _daemon_alive_cached() -> bool:
    """Cheap, cached daemon-alive probe.

    The daemon client import is lazy so modules that run without the SPIRENT
    tree installed don't pay a cost.  We cache the answer for a few seconds
    so each ``_run_spirent`` call doesn't spam a ping over the socket.
    """
    global _DAEMON_CLIENT, _DAEMON_LAST_PROBE
    if _DAEMON_DISABLED:
        return False
    now = time.monotonic()
    if _DAEMON_CLIENT is None and (now - _DAEMON_LAST_PROBE) < _DAEMON_PROBE_INTERVAL:
        return False
    _DAEMON_LAST_PROBE = now
    try:
        if _DAEMON_CLIENT is None:
            tool_dir = spirent_tool_path().parent
            import importlib
            import sys as _sys
            if str(tool_dir) not in _sys.path:
                _sys.path.insert(0, str(tool_dir))
            _DAEMON_CLIENT = importlib.import_module("spirent_daemon")
        return _DAEMON_CLIENT.daemon_is_alive(timeout=1.0)
    except Exception:
        _DAEMON_CLIENT = None
        return False


def _run_spirent(
    args: List[str],
    timeout: int = 60,
    retries: int = 1,
    return_streams: bool = False,
) -> Any:
    """Run spirent_tool.py with bounded retries and stream-aware return.

    Mutating verbs auto-bump retries to 2 when the caller did not specify a
    higher value -- one transient TCL/STC stutter should not abort an entire
    provisioning run.  By default we still return the legacy combined string
    (stdout + stderr) so existing parsers keep working.  Pass
    ``return_streams=True`` to receive ``{"stdout","stderr","rc"}`` -- safer
    when the caller will ``json.loads`` the output (a stderr ``Warning:``
    line otherwise corrupts the JSON).

    F5 integration: when ``spirent_daemon.py`` is running we route the call
    through its unix socket, skipping the per-invocation Python cold start
    and the StcHttp re-authentication.  This cuts a typical
    ``bgp-peer`` + ``isis-peer`` + ``ldp-peer`` burst from ~5s to ~1s and
    drastically reduces REST load on the Lab Server.  Set
    ``SPIRENT_NO_DAEMON=1`` to force the legacy subprocess path.
    """
    if retries <= 1 and args and args[0] in _PROVISIONER_MUTATING:
        retries = 2

    last_stdout = ""
    last_stderr = ""
    last_rc = -1

    use_daemon = _daemon_alive_cached()

    for attempt in range(max(1, retries)):
        try:
            if use_daemon:
                try:
                    rc, out, err, _elapsed = _DAEMON_CLIENT.run_via_daemon(
                        list(args), timeout=max(timeout, 30)
                    )
                    last_stdout = out or ""
                    last_stderr = err or ""
                    last_rc = int(rc)
                except Exception as de:
                    # Daemon fell over -- drop it for the rest of this call
                    # and fall back to subprocess.
                    use_daemon = False
                    last_stderr = f"[DAEMON-FALLBACK] {de}"
                    proc = subprocess.run(
                        spirent_tool_command(*args),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        text=True, timeout=timeout,
                    )
                    last_stdout = proc.stdout or ""
                    last_stderr = (proc.stderr or "") + "\n" + last_stderr
                    last_rc = proc.returncode
            else:
                proc = subprocess.run(
                    spirent_tool_command(*args),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, timeout=timeout,
                )
                last_stdout = proc.stdout or ""
                last_stderr = proc.stderr or ""
                last_rc = proc.returncode

            combined = last_stdout + last_stderr

            if last_rc != 0 and attempt < retries - 1:
                if any(s in combined for s in _SESSION_DEAD_MARKERS):
                    time.sleep(min(2.0 * (attempt + 1), 5.0))
                    continue

            if return_streams:
                return {"stdout": last_stdout, "stderr": last_stderr,
                        "rc": last_rc, "combined": combined}
            return combined

        except subprocess.TimeoutExpired:
            last_stderr = f"[TIMEOUT] after {timeout}s"
            last_rc = -1
            if attempt < retries - 1:
                time.sleep(1.0)
                continue
        except Exception as e:
            last_stderr = f"[ERROR] {e.__class__.__name__}: {e}"
            last_rc = -1
            if attempt < retries - 1:
                time.sleep(1.0)
                continue

    if return_streams:
        return {"stdout": last_stdout, "stderr": last_stderr,
                "rc": last_rc, "combined": last_stdout + last_stderr}
    return last_stdout + last_stderr if last_stdout or last_stderr else "[ERROR] all retries exhausted"


def _cfg_block(run_show, device: str, commands: List[str]) -> str:
    """Send a block of config commands using 'top' navigation.

    DNOS CLI navigation rules (from Confluence CLI docs):
      - 'top'  = return to config root (stays in config mode)
      - 'end'  = exit config mode entirely
      - 'exit' = go up ONE level in the hierarchy

    Each block starts with 'config', sends commands, then 'top' to reset.
    Returns the output of the last command (for error checking).
    """
    run_show(device, "config")
    last = ""
    for c in commands:
        last = run_show(device, c)
    run_show(device, "top")
    return last


def _force_session_to_operational(run_show, device: str) -> None:
    """Forcibly drag the SSH session back to operational mode.

    Critical safety net: if a previous `_cfg_commit` failed, the session may
    be stuck inside `config` mode with uncommitted candidate changes. ANY
    later show command on that session will hit DNOS's
        "Configuration includes uncommitted changes, would you like to
         commit them before exiting (yes/no/cancel)?"
    prompt and time out (we observed 150-second hangs per command -- this is
    the entire source of the perceived '10-minute idle' on long runs).

    Sequence: rollback any candidate -> answer the warn prompt with
    'no' if asked -> exit config mode. Each call is bounded; we ignore
    any "Unknown word" replies because they just mean we were already
    in operational mode.
    """
    try:
        run_show(device, "rollback 0")
    except Exception:
        pass
    try:
        # If a previous `end` was already issued and DNOS is showing the
        # "uncommitted changes" prompt, answering 'no' clears it without
        # committing.
        run_show(device, "no")
    except Exception:
        pass
    try:
        run_show(device, "end")
    except Exception:
        pass


def _cfg_commit(run_show, device: str) -> tuple:
    """Commit check then commit. Returns (ok, output).

    Caller MUST already be in config mode. We try `commit check` first; if
    DNOS replies `Unknown word: 'commit'`, that means the session fell back
    to operational mode (e.g. the previous block's `top` or a stray `end`),
    so we re-enter config and retry once. Without this guard, sequential
    provisioning blocks intermittently fail with a confusing
    `pe1_commit: Unknown word: 'commit'` even though the underlying config
    was valid.

    On successful commit, invalidates the DUTProfile cache for this device
    because the live config has changed and the cached profile is now stale.
    """
    check = run_show(device, "commit check")
    if "Unknown word" in check and "commit" in check:
        run_show(device, "config")
        check = run_show(device, "commit check")
    if "ERROR" in check and "passed" not in check.lower():
        run_show(device, "rollback 0")
        run_show(device, "end")
        return False, check
    commit_out = run_show(device, "commit")
    if "Unknown word" in commit_out and "commit" in commit_out:
        run_show(device, "config")
        commit_out = run_show(device, "commit")
    ok = "ERROR" not in commit_out or "succeeded" in commit_out.lower()
    if ok:
        run_show(device, "end")
        invalidate_dut_profile_cache(device)
    else:
        # Commit failed -- session may still be in config mode with dirty
        # candidate. Force-clean before returning so the next show command
        # on this session doesn't hit the uncommitted-changes prompt.
        _force_session_to_operational(run_show, device)
    return ok, commit_out


def _check_and_fix_label_pool(
    device: str,
    run_show: Callable[[str, str], str],
    result: ProvisionResult,
) -> bool:
    """Step 1: Ensure VPLS label block is allocated."""
    output = run_show(device, "show mpls label-allocation tables | no-more")
    if "bgp-vpls" in output:
        m = re.search(r"bgp-vpls\s+\|\s+(\d+)", output)
        if m and int(m.group(1)) > 0:
            result.add("label_pool", "PASS",
                        f"bgp-vpls: {m.group(1)} labels allocated")
            return True

    alt = run_show(device, "show config routing-options | flatten | include bgp-vpls-label-block-size | no-more")
    if "bgp-vpls-label-block-size" in alt:
        result.add("label_pool", "PASS",
                    "Label block configured (may need restart to activate -- SW-253359)")
        return True

    result.add("label_pool", "FIX",
               "Applying: routing-options bgp-vpls-label-block-size 130")
    _cfg_block(run_show, device, [
        "routing-options bgp-vpls-label-block-size 130",
    ])
    ok, out = _cfg_commit(run_show, device)
    if not ok:
        result.add("label_pool_commit", "FAIL", out[:200])
        return False
    result.add("label_pool", "PASS", "Label block configured (130)")
    return True


def _check_and_fix_bgp_vpls_af(
    device: str,
    run_show: Callable[[str, str], str],
    result: ProvisionResult,
    asn: int = DUT_BGP_ASN,
) -> bool:
    """Step 2: Ensure BGP l2vpn-vpls AF is enabled."""
    output = run_show(device, f"show config protocols bgp {asn} | flatten | include l2vpn-vpls | no-more")
    if "l2vpn-vpls" in output:
        result.add("bgp_vpls_af", "PASS", "l2vpn-vpls AF already configured")
        return True

    result.add("bgp_vpls_af", "FIX", "Enabling l2vpn-vpls AF")
    _cfg_block(run_show, device, [
        f"protocols bgp {asn}",
        "address-family l2vpn-vpls",
    ])
    ok, out = _cfg_commit(run_show, device)
    if not ok:
        result.add("bgp_vpls_af_commit", "FAIL", out[:200])
        return False
    result.add("bgp_vpls_af", "PASS", "l2vpn-vpls AF enabled")
    return True


def _check_and_create_evpn_instance(
    device: str,
    run_show: Callable[[str, str], str],
    result: ProvisionResult,
    asn: int = DUT_BGP_ASN,
    router_id: str = DUT_ROUTER_ID,
    evpn_name: str = PW_TEST_EVPN_NAME,
    evpn_rt: str = PW_TEST_EVPN_RT,
    vpls_rt: str = PW_TEST_VPLS_RT,
    evi: int = PW_TEST_EVI,
    site_id: int = PW_TEST_SITE_ID,
    ac_subif: str = PW_TEST_AC_SUBIF,
) -> bool:
    """Step 3: Create EVPN instance with SI + VPLS RT.

    Uses 'top' navigation between config blocks (validated on PE-1 2026-04-02).
    DNOS config hierarchy for EVPN SI (from Confluence + live validation):
      network-services > evpn > instance X > protocols > bgp ASN > export-l2vpn-evpn
      network-services > evpn > instance X > seamless-integration > protocols > bgp > export-l2vpn-vpls
      network-services > evpn > instance X > seamless-integration > site-id N > site-interface IF
      network-services > evpn > instance X > interface IF
    """
    output = run_show(device, f"show config network-services evpn instance {evpn_name} | no-more")
    if f"instance {evpn_name}" in output:
        if "seamless-integration" in output:
            result.add("evpn_instance", "PASS",
                       f"{evpn_name} exists with SI (required for VPLS PW)")
        else:
            result.add("evpn_instance", "PASS", f"{evpn_name} exists (SI will be added for VPLS PW)")

        si_output = run_show(device, f"show config network-services evpn instance {evpn_name} seamless-integration | flatten | no-more")

        wrong_site = re.search(r"site-id\s+(\d+)", si_output)
        if wrong_site and int(wrong_site.group(1)) != site_id:
            old_id = wrong_site.group(1)
            result.add("site_id_fix", "FIX",
                       f"site-id {old_id} != expected {site_id} "
                       f"(same as Spirent VE-ID blocks PW creation)")
            _cfg_block(run_show, device, [
                f"no network-services evpn instance {evpn_name} "
                f"seamless-integration site-id {old_id}",
            ])
            _cfg_block(run_show, device, [
                f"network-services evpn instance {evpn_name}",
                "seamless-integration",
                f"site-id {site_id} site-interface {ac_subif}",
            ])
            ok, commit_out = _cfg_commit(run_show, device)
            if ok:
                result.add("site_id_fix", "PASS",
                           f"site-id corrected: {old_id} -> {site_id}")
            else:
                result.add("site_id_fix", "FAIL", commit_out[:200])

        if "export-l2vpn-vpls" not in si_output:
            result.add("vpls_rt", "FIX",
                       f"Adding SI with l2vpn-vpls RT {vpls_rt} (VPLS RT must be under seamless-integration)")
            _cfg_block(run_show, device, [
                f"network-services evpn instance {evpn_name}",
                "seamless-integration",
                "protocols",
                "bgp",
                f"export-l2vpn-vpls route-target {vpls_rt}",
                f"import-l2vpn-vpls route-target {vpls_rt}",
            ])
            _cfg_block(run_show, device, [
                f"network-services evpn instance {evpn_name}",
                "seamless-integration",
                "label-block-size 8",
                "source-if lo0",
                f"site-id {site_id} site-interface {ac_subif}",
            ])
            ok, commit_out = _cfg_commit(run_show, device)
            if ok:
                result.add("vpls_rt", "PASS", f"SI + l2vpn-vpls RT {vpls_rt} configured")
            else:
                result.add("vpls_rt", "WARN", f"Commit failed: {commit_out[:200]}")
        return True

    result.add("evpn_instance", "FIX", f"Creating {evpn_name} with SI + VPLS RT")
    rd = f"{router_id}:{evi}"

    _cfg_block(run_show, device, [
        f"network-services evpn instance {evpn_name}",
        "protocols",
        f"bgp {asn}",
        f"export-l2vpn-evpn route-target {evpn_rt}",
        f"import-l2vpn-evpn route-target {evpn_rt}",
        f"route-distinguisher {rd}",
    ])

    _cfg_block(run_show, device, [
        f"network-services evpn instance {evpn_name}",
        "seamless-integration",
        "protocols",
        "bgp",
        f"export-l2vpn-vpls route-target {vpls_rt}",
        f"import-l2vpn-vpls route-target {vpls_rt}",
    ])

    _cfg_block(run_show, device, [
        f"network-services evpn instance {evpn_name}",
        "seamless-integration",
        "label-block-size 8",
        "source-if lo0",
        f"site-id {site_id} site-interface {ac_subif}",
    ])

    _cfg_block(run_show, device, [
        f"network-services evpn instance {evpn_name}",
        f"interface {ac_subif}",
    ])

    ok, commit_out = _cfg_commit(run_show, device)
    if not ok:
        result.add("evpn_instance_commit", "FAIL", commit_out[:300])
        return False
    result.add("evpn_instance", "PASS",
               f"{evpn_name} created with SI + RT {vpls_rt}")
    return True


def _check_and_create_ac_interface(
    device: str,
    run_show: Callable[[str, str], str],
    result: ProvisionResult,
    ac_subif: str = PW_TEST_AC_SUBIF,
    ac_outer: int = PW_TEST_AC_OUTER,
    ac_inner: int = PW_TEST_AC_INNER,
) -> bool:
    """Step 4: Create AC sub-interface on DNAAS path for local MAC learning."""
    output = run_show(device, f"show config interfaces {ac_subif} | no-more")
    if "l2-service" in output and f"inner-tag {ac_inner}" in output:
        result.add("ac_interface", "PASS", f"{ac_subif} already configured")
        return True

    result.add("ac_interface", "FIX", f"Creating {ac_subif}")
    _cfg_block(run_show, device, [
        f"interfaces {ac_subif}",
        "admin-state enabled",
        "l2-service enabled",
        f"vlan-tags outer-tag {ac_outer} inner-tag {ac_inner}",
    ])
    ok, commit_out = _cfg_commit(run_show, device)
    if not ok:
        result.add("ac_interface_commit", "FAIL", commit_out[:200])
        return False
    result.add("ac_interface", "PASS",
               f"{ac_subif} created (outer {ac_outer}, inner {ac_inner})")
    return True


def _check_and_create_bgp_neighbor(
    device: str,
    run_show: Callable[[str, str], str],
    result: ProvisionResult,
    asn: int = DUT_BGP_ASN,
    neighbor_ip: str = VPLS_BGP_NEIGHBOR_IP,
    update_source: str = VPLS_BGP_UPDATE_SOURCE,
) -> bool:
    """Step 5: Configure BGP neighbor for Spirent's connected IP.

    STC BGP sources TCP from the device's connected interface (17.17.17.2),
    NOT from the ISIS-advertised loopback (3.3.3.3). PE-1's BGP neighbor
    must therefore use the connected IP without update-source lo0.
    """
    output = run_show(
        device,
        f"show config protocols bgp {asn} | flatten | include {neighbor_ip} | no-more",
    )
    if neighbor_ip in output and "l2vpn-vpls" in output:
        result.add("bgp_neighbor", "PASS",
                    f"BGP neighbor {neighbor_ip} already configured with l2vpn-vpls")
        return True

    old_nbr = run_show(
        device,
        f"show config protocols bgp {asn} | flatten | include {VPLS_SHARED_LOOPBACK} | no-more",
    )
    if VPLS_SHARED_LOOPBACK in old_nbr:
        result.add("bgp_neighbor", "FIX",
                    f"Removing old loopback neighbor {VPLS_SHARED_LOOPBACK} (STC needs connected IP)")
        _cfg_block(run_show, device, [
            f"no protocols bgp {asn} neighbor {VPLS_SHARED_LOOPBACK}",
        ])

    result.add("bgp_neighbor", "FIX",
               f"Adding BGP neighbor {neighbor_ip} with l2vpn-vpls (connected IP)")

    _cfg_block(run_show, device, [
        f"protocols bgp {asn} neighbor {neighbor_ip}",
        "admin-state enabled",
        f"remote-as {asn}",
        f"update-source {update_source}",
    ])

    _cfg_block(run_show, device, [
        f"protocols bgp {asn} neighbor {neighbor_ip}",
        "address-family l2vpn-vpls",
        "send-community community-type both",
        "soft-reconfiguration inbound",
    ])

    ok, commit_out = _cfg_commit(run_show, device)
    if not ok:
        result.add("bgp_neighbor_commit", "FAIL", commit_out[:200])
        return False
    result.add("bgp_neighbor", "PASS",
               f"BGP neighbor {neighbor_ip} configured (iBGP, l2vpn-vpls)")
    return True


def _create_spirent_vpls_device(
    result: ProvisionResult,
    ip: str = VPLS_PEER_IP,
    gw: str = VPLS_PEER_GW,
    outer_vlan: int = VPLS_PEER_OUTER_VLAN,
    inner_vlan: int = VPLS_PEER_INNER_VLAN,
) -> bool:
    """Step 6: Create Spirent emulated device on DUT's MPLS-enabled interface subnet."""
    status_out = _run_spirent(["status", "--json"])
    try:
        status = json.loads(status_out)
        for d in status.get("devices", []):
            if d.get("name") == VPLS_DEVICE_NAME:
                result.add("spirent_device", "PASS",
                           f"{VPLS_DEVICE_NAME} already exists")
                return True
    except json.JSONDecodeError:
        pass

    result.add("spirent_device", "FIX", f"Creating {VPLS_DEVICE_NAME}")
    out = _run_spirent([
        "create-device",
        "--name", VPLS_DEVICE_NAME,
        "--ip", ip,
        "--gateway", gw,
        "--vlan", str(outer_vlan),
        "--inner-vlan", str(inner_vlan),
        "--mac", "00:10:94:00:03:03",
        "--device-count", "1",
    ])
    if "ERROR" in out and "already exists" not in out:
        result.add("spirent_device_create", "FAIL", out[:200])
        return False
    result.add("spirent_device", "PASS",
               f"{VPLS_DEVICE_NAME} at {ip} (vlan {outer_vlan}/{inner_vlan})")
    return True


def _configure_spirent_isis(result: ProvisionResult, area_id: str = VPLS_ISIS_AREA) -> bool:
    """Step 7a: Configure ISIS on the Spirent device.

    Uses VPLS_SHARED_LOOPBACK because STC devices on the same physical
    port share a single ISIS instance -- only one loopback survives.
    """
    out = _run_spirent([
        "isis-peer",
        "--device-name", VPLS_DEVICE_NAME,
        "--system-id", VPLS_PEER_SYSTEM_ID,
        "--area-id", area_id,
        "--level", "LEVEL2",
        "--loopback", VPLS_SHARED_LOOPBACK,
        "--loopback-metric", "10",
    ], timeout=120)
    if "[OK]" in out:
        result.add("spirent_isis", "PASS",
                    f"ISIS configured: sys-id={VPLS_PEER_SYSTEM_ID}, area={area_id}, lo={VPLS_SHARED_LOOPBACK}/32")
        return True
    result.add("spirent_isis", "FAIL", out[:200])
    return False


def _configure_spirent_ldp(result: ProvisionResult) -> bool:
    """Step 7b: Configure LDP on the Spirent device."""
    out = _run_spirent([
        "ldp-peer",
        "--device-name", VPLS_DEVICE_NAME,
        "--router-id", VPLS_SHARED_LOOPBACK,
        "--transport-address", VPLS_SHARED_LOOPBACK,
        "--fec-prefix", VPLS_SHARED_LOOPBACK,
    ], timeout=120)
    if "[OK]" in out:
        result.add("spirent_ldp", "PASS",
                    f"LDP configured: router-id={VPLS_SHARED_LOOPBACK}")
        return True
    result.add("spirent_ldp", "FAIL", out[:200])
    return False


def _configure_spirent_bgp_vpls(
    result: ProvisionResult,
    asn: int = DUT_BGP_ASN,
    neighbor_gw: str = VPLS_PEER_GW,
    vpls_rt: str = PW_TEST_VPLS_RT,
    evi: int = PW_TEST_EVI,
    ve_id: int = PW_TEST_VE_ID,
    block_size: int = VPLS_LABEL_BLOCK_SIZE,
) -> bool:
    """Step 7c: Configure BGP with l2vpn-vpls on the Spirent device.

    Uses the shared ISIS loopback as VPLS nexthop (STC constraint).
    RD uses VPLS_PEER_IP to keep it unique per peer.
    """
    out = _run_spirent([
        "bgp-peer",
        "--device-name", VPLS_DEVICE_NAME,
        "--as", str(asn),
        "--dut-as", str(asn),
        "--neighbor", neighbor_gw,
        "--negotiate-afi", "l2vpn-vpls",
        "--vpls-nexthop", VPLS_SHARED_LOOPBACK,
        "--vpls-rd", f"{VPLS_PEER_IP}:{evi}",
        "--vpls-rt", vpls_rt,
        "--vpls-ve-id", str(ve_id),
        "--vpls-block-size", str(block_size),
        "--no-start",
    ], timeout=120)
    if "ESTABLISHED" in out or "[OK]" in out:
        result.add("spirent_bgp_vpls", "PASS",
                    f"BGP l2vpn-vpls configured (ASN={asn}, RT={vpls_rt})")
        return True
    if "not ESTABLISHED" in out.lower() or "WARNING" in out or "[TIMEOUT]" in out:
        result.add("spirent_bgp_vpls", "PASS",
                    "BGP l2vpn-vpls configured (deferred start, DUT-side check will follow)")
        return True
    result.add("spirent_bgp_vpls", "FAIL", out[:300])
    return False


def _start_spirent_protocols(result: ProvisionResult) -> bool:
    """Step 8: Start all protocols (ISIS + LDP + BGP) on the Spirent device."""
    out = _run_spirent(["protocol-start", "--device-name", VPLS_DEVICE_NAME])
    if "ERROR" not in out:
        result.add("spirent_proto_start", "PASS", "Protocols started")
        return True
    result.add("spirent_proto_start", "FAIL", out[:200])
    return False


def _validate_pw_state(
    device: str,
    run_show: Callable[[str, str], str],
    result: ProvisionResult,
    wait_sec: int = 60,
) -> bool:
    """Step 9: Wait for PW to appear and check if ingress label is in MPLS FIB.

    Uses `poll_until` for event-driven waiting -- exits the moment the PW row
    appears, instead of fixed 5s sleeps. On timeout, the last observed VPLS
    table snippet is captured for diagnostics.
    """
    result.add("pw_validation", "INFO", f"Waiting up to {wait_sec}s for PW to come up...")

    def _check() -> Tuple[bool, Any]:
        """One poll attempt: returns (pw_row_found, last_observation)."""
        vpls_out = run_show(device, "show evpn vpls-pw | no-more")
        lines = vpls_out.split(PW_TEST_EVPN_NAME)
        if len(lines) <= 1:
            return False, "PW row not yet in 'show evpn vpls-pw'"
        table_section = lines[1]
        row_m = re.search(
            r"\|\s*([\d.]+)\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+(\S+)",
            table_section,
        )
        if not row_m:
            return False, f"PW row malformed: {table_section[:160]!r}"
        return True, {
            "peer_ip": row_m.group(1),
            "ingress_label": int(row_m.group(3)),
            "status": row_m.group(6),
        }

    poll = poll_until(_check, timeout_sec=float(wait_sec), interval_sec=5.0,
                      progress_label="vpls_pw_row_appears")
    if not poll.passed:
        result.add("pw_validation", "FAIL",
                   f"No PW found for {PW_TEST_EVPN_NAME} after {wait_sec}s "
                   f"(last_observed={poll.last_value!r})")
        result.blocker = "VPLS PW did not appear. Check ISIS/LDP/BGP adjacency."
        return False

    obs = poll.last_value or {}
    peer_ip = obs.get("peer_ip", "?")
    ingress_label = int(obs.get("ingress_label", 0))
    status = str(obs.get("status", "?"))
    result.add("pw_found", "PASS",
               f"PW to {peer_ip}: ingress={ingress_label}, status={status} "
               f"(found after {poll.elapsed_sec:.1f}s, {poll.attempts} poll(s))")
    result.ingress_label = ingress_label

    fib_out = run_show(device, f"show mpls forwarding-table label {ingress_label} | no-more")
    if status.lower() in ("uninstalled", "bni"):
        if "No information found" in fib_out:
            result.pw_active = False
            result.blocker = (
                f"PW label {ingress_label} is {status} (NOT in MPLS FIB). "
                f"SI mode makes PW BNI. vpls-stream requires label in FIB."
            )
            result.add("pw_fib", "FAIL", result.blocker)
        else:
            result.pw_active = True
            result.add("pw_fib", "PASS",
                       f"Label {ingress_label} found in MPLS FIB")
    else:
        result.pw_active = "No information found" not in fib_out
        status_str = "in FIB" if result.pw_active else "NOT in FIB"
        result.add("pw_fib",
                   "PASS" if result.pw_active else "FAIL",
                   f"Label {ingress_label} {status_str}")

    result.params["pw_ingress_label"] = str(ingress_label)
    result.params["pw_test_evpn_name"] = PW_TEST_EVPN_NAME
    result.params["pw_test_evi"] = str(PW_TEST_EVI)
    result.params["vpls_rd"] = f"{DUT_ROUTER_ID}:{PW_TEST_EVI}"
    result.params["vpls_rt"] = PW_TEST_VPLS_RT
    result.params["vpls_ve_id"] = str(PW_TEST_VE_ID)
    return result.pw_active


# ---------------------------------------------------------------------------
# DUTProfile builder -- reads params dict + targeted show commands
# ---------------------------------------------------------------------------

def _strip(text: str) -> str:
    """Inline ANSI strip for DUTProfile builder (avoid circular import)."""
    return re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)


def build_dut_profile(
    params: Dict[str, str],
    run_show: Callable[[str, str], str],
    device: str,
) -> DUTProfile:
    """Build a DUTProfile from already-resolved runtime params + a few extra show commands.

    Most fields come directly from the params dict that resolve_runtime_params()
    already populates. The remaining gaps (ISIS area, lo0 IP, VPLS sub-interface
    VLANs) are filled with 3-4 targeted show commands.
    """
    p = DUTProfile(device=device)

    # -- Fields directly from params dict --
    p.bgp_asn = int(params.get("asn") or DUT_BGP_ASN)
    p.evpn_import_rt = params.get("rt_import", "") or params.get("rt", "")
    p.evpn_export_rt = params.get("rt_export", "") or params.get("rt", "")
    p.evpn_rd = params.get("rd", "")
    p.evpn_evi = int(params.get("evi") or 0)
    p.dut_interface_mac = params.get("pw_dut_mac", "")
    p.pw_test_evpn_name = params.get("pw_test_evpn_name", PW_TEST_EVPN_NAME)
    p.pw_test_evi = int(params.get("pw_evi") or PW_TEST_EVI)
    p.pw_test_vpls_rt = params.get("pw_rt") or PW_TEST_VPLS_RT
    p.pw_test_evpn_rt = params.get("rt") or PW_TEST_EVPN_RT

    if params.get("pw_outer_vlan"):
        p.vpls_neighbor_outer_vlan = int(params["pw_outer_vlan"])
        p.evpn_neighbor_outer_vlan = int(params["pw_outer_vlan"])
    if params.get("pw_inner_vlan"):
        p.pw_test_ac_inner = int(params["pw_inner_vlan"])

    pw_ac_if = params.get("_pw_ac1_interface") or params.get("_pw_ac_interface", "")
    if pw_ac_if:
        p.pw_test_ac_subif = pw_ac_if
        outer = params.get("pw_outer_vlan", "")
        inner = params.get("pw_inner_vlan", "")
        if outer:
            p.pw_test_ac_outer = int(outer)
        if inner:
            p.pw_test_ac_inner = int(inner)

    # AC interfaces from params
    ac_str = params.get("_evpn_ac_interfaces", "")
    if ac_str:
        for name in ac_str.split(","):
            name = name.strip()
            if name:
                p.ac_interfaces.append({"interface": name})

    # PW RD
    pw_rd = params.get("pw_rd", "")
    if pw_rd:
        p.vpls_rd = pw_rd

    # PW site-id from DUT
    pw_local_site = params.get("pw_local_site_id", "")
    if pw_local_site:
        p.vpls_site_id = int(pw_local_site)

    # -- Additional targeted show commands for remaining gaps --

    # 1. Router-ID from BGP summary
    try:
        bgp_sum = run_show(device, "show bgp summary | no-more")
        rid_m = re.search(r"BGP\s+router\s+identifier\s+([\d.]+)", _strip(bgp_sum))
        if rid_m:
            p.router_id = rid_m.group(1)
    except Exception:
        pass

    # 2. ISIS area (for Spirent ISIS peering)
    try:
        isis_cfg = run_show(device, "show config protocols isis | flatten | include area-id | no-more")
        area_m = re.search(r"area-id\s+(\S+)", _strip(isis_cfg))
        if area_m:
            p.vpls_isis_area = area_m.group(1)
    except Exception:
        pass

    # 3. lo0 IP (for ISIS route target / VPLS source-if)
    try:
        lo0_out = run_show(device, "show interfaces lo0 | no-more")
        lo0_m = re.search(r"inet\s+([\d.]+)/|IPv4\s+Address:\s+([\d.]+)", _strip(lo0_out))
        if lo0_m:
            p.vpls_source_loopback = lo0_m.group(1) or lo0_m.group(2)
    except Exception:
        pass

    # 4. VPLS neighbor sub-interface VLANs (the .3 sub-if used for BGP peering)
    vpls_if = params.get("_pw_ac_interface", "")
    if vpls_if:
        base_if = vpls_if.rsplit(".", 1)[0]
        # Discover which sub-ifs have MPLS enabled on the same base interface
        try:
            if_cfg = run_show(device, f"show config interfaces {base_if} | flatten | no-more")
            if_clean = _strip(if_cfg)
            # Find MPLS-enabled sub-ifs for VPLS peering
            for m in re.finditer(r"interfaces\s+([\w/.-]+\.(\d+)).*?mpls", if_clean):
                sub_name = m.group(1)
                if sub_name != vpls_if:
                    p.vpls_isis_interface = sub_name
                    inner_m = re.search(
                        rf"interfaces\s+{re.escape(sub_name)}.*?inner-tag\s+(\d+)", if_clean
                    )
                    if inner_m:
                        p.vpls_neighbor_inner_vlan = int(inner_m.group(1))
                    break
        except Exception:
            pass

    # 5. Management IP from device context (with scaler DB fallback)
    try:
        mgmt_out = run_show(device, "show interfaces management | no-more")
        mgmt_m = re.search(r"inet\s+([\d.]+)/|IPv4\s+Address:\s+([\d.]+)", _strip(mgmt_out))
        if mgmt_m:
            p.mgmt_ip = mgmt_m.group(1) or mgmt_m.group(2)
    except Exception:
        pass
    if not p.mgmt_ip:
        try:
            _db_path = Path(__file__).resolve().parents[3] / "scaler" / "db" / "devices.json"
            if _db_path.exists():
                import json as _json_mgmt
                _db = _json_mgmt.loads(_db_path.read_text())
                _norm = device.lower().replace("-", "_").replace(" ", "_")
                for _d in _db.get("devices", []):
                    _cands = [_d.get("hostname", ""), _d.get("id", "")]
                    if any(_norm in c.lower().replace("-", "_") for c in _cands if c):
                        p.mgmt_ip = _d.get("ip", "")
                        break
        except Exception:
            pass
    if not p.mgmt_ip:
        p.mgmt_ip = PE1_MGMT_IP

    # Fill derived fields
    if not p.evpn_rd and p.router_id and p.evpn_evi:
        p.evpn_rd = f"{p.router_id}:{p.evpn_evi}"
    if not p.vpls_rd and p.router_id and p.pw_test_evi:
        p.vpls_rd = f"{p.router_id}:{p.pw_test_evi}"

    logger.info(
        "[DUTProfile] Built for %s: ASN=%s, RID=%s, ISIS=%s, lo0=%s, EVPN_RT=%s, VPLS_RT=%s",
        device, p.bgp_asn, p.router_id, p.vpls_isis_area, p.vpls_source_loopback,
        p.evpn_import_rt, p.pw_test_vpls_rt,
    )

    return p


# ---------------------------------------------------------------------------
# DUTProfile cache -- dynamic invalidation via config fingerprint
# ---------------------------------------------------------------------------

_DUT_PROFILE_CACHE_DIR = Path.home() / ".cursor" / "spirent_cache"
_DUT_PROFILE_CACHE_HARD_MAX_SEC = 900  # 15 min absolute max even if fingerprint matches
_SCALER_DB_PATH = Path(__file__).resolve().parents[4] / "db" / "devices.json"


def _compute_config_fingerprint(
    run_show: Optional[Callable] = None,
    device: str = "",
) -> str:
    """Compute a lightweight fingerprint from DUT config that changes when
    EVPN/BGP/interface topology changes.

    Uses 3 fast show commands (~1s total) whose output changes when any
    provisioning-relevant config is modified:
      - EVPN instance count + names
      - BGP neighbor count
      - Sub-interface count on the DNAAS-facing port
    """
    import hashlib
    parts = []
    if run_show and device:
        try:
            evpn_sum = run_show(device, "show evpn summary | no-more")
            parts.append(evpn_sum.strip()[:2000])
        except Exception:
            pass
        try:
            bgp_sum = run_show(device, "show bgp summary | no-more")
            parts.append(bgp_sum.strip()[:2000])
        except Exception:
            pass
        try:
            mpls_lbl = run_show(device, "show mpls label-allocation tables | no-more")
            parts.append(mpls_lbl.strip()[:500])
        except Exception:
            pass
    # Include scaler DB last_sync as a secondary signal
    try:
        if _SCALER_DB_PATH.exists():
            db = json.loads(_SCALER_DB_PATH.read_text())
            for d in db.get("devices", []):
                aliases = [d.get("hostname", "").lower(), d.get("id", "").lower()]
                aliases += [a.lower() for a in d.get("aliases", [])]
                if device.lower() in aliases or device == d.get("ip", ""):
                    parts.append(d.get("last_sync", ""))
                    break
    except Exception:
        pass
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16] if raw else ""


def save_dut_profile_cache(
    profile: DUTProfile,
    fingerprint: str = "",
) -> Path:
    """Persist DUTProfile to JSON with a config fingerprint for smart invalidation."""
    _DUT_PROFILE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = _DUT_PROFILE_CACHE_DIR / f"dut_profile_{profile.device}.json"
    payload = profile.to_dict()
    payload["_cached_at"] = time.time()
    payload["_fingerprint"] = fingerprint
    cache_file.write_text(json.dumps(payload, indent=2))
    return cache_file


def load_dut_profile_cache(
    device: str,
    run_show: Optional[Callable] = None,
    max_age_sec: int = _DUT_PROFILE_CACHE_HARD_MAX_SEC,
    _precomputed_fp: str = "",
) -> Optional[DUTProfile]:
    """Load cached DUTProfile if it exists and config hasn't drifted.

    Invalidation logic (in priority order):
      1. Hard age > 15 min -> always rebuild (config may have changed silently)
      2. If run_show is available (or _precomputed_fp provided), compare live
         fingerprint against stored. Mismatch -> rebuild.
      3. If fingerprints match -> reuse regardless of age (config hasn't changed)
      4. If no live fingerprint available -> fall back to 5-min TTL
      5. If stored cache has no fingerprint (legacy file) -> fall back to 5-min TTL

    Args:
        _precomputed_fp: If a caller already computed the live fingerprint, pass it
            here to avoid redundant SSH calls.
    """
    cache_file = _DUT_PROFILE_CACHE_DIR / f"dut_profile_{device}.json"
    if not cache_file.exists():
        return None
    try:
        payload = json.loads(cache_file.read_text())
        cached_at = payload.get("_cached_at", 0)
        stored_fp = payload.get("_fingerprint", "")
        age = time.time() - cached_at

        if age > max_age_sec:
            logger.info(
                "[DUTProfile] Cache expired (age=%.0fs > hard max %ds)", age, max_age_sec,
            )
            return None

        live_fp = _precomputed_fp
        if not live_fp and run_show and device:
            live_fp = _compute_config_fingerprint(run_show, device)

        if live_fp and stored_fp:
            if live_fp != stored_fp:
                logger.info("[DUTProfile] Config drift detected (fingerprint mismatch) -- rebuilding")
                return None
            payload.pop("_cached_at", None)
            payload.pop("_fingerprint", None)
            profile = DUTProfile.from_dict(payload)
            logger.info("[DUTProfile] Loaded from cache (%.0fs old, fingerprint OK)", age)
            return profile

        # No live fingerprint (SSH failed) or no stored fingerprint (legacy cache) --
        # fall back to short TTL so we don't serve very stale data.
        if age > 300:
            logger.info("[DUTProfile] Cache too old for TTL fallback (%.0fs > 300s)", age)
            return None
        payload.pop("_cached_at", None)
        payload.pop("_fingerprint", None)
        profile = DUTProfile.from_dict(payload)
        logger.info("[DUTProfile] Loaded from cache (%.0fs old, no fingerprint available)", age)
        return profile
    except Exception as exc:
        logger.warning("[DUTProfile] Cache load error: %s", exc)
        return None


def invalidate_dut_profile_cache(device: str) -> bool:
    """Explicitly invalidate cache for a device (e.g. after config commit)."""
    cache_file = _DUT_PROFILE_CACHE_DIR / f"dut_profile_{device}.json"
    if cache_file.exists():
        cache_file.unlink()
        return True
    return False


def require_dut_profile(
    device: str,
    params: Dict[str, str],
    run_show: Callable[[str, str], str],
    existing_profile: Optional[DUTProfile] = None,
) -> DUTProfile:
    """Ensure a fresh DUTProfile exists -- mandatory gateway for all Spirent operations.

    Call this before any provisioning or Spirent traffic operation. It:
      1. Computes a live config fingerprint ONCE (3 fast show commands, ~1s)
      2. Returns the existing profile if fingerprint hasn't changed
      3. Loads from disk cache if fingerprint matches
      4. Builds a new profile and caches it with the fingerprint

    The fingerprint is computed exactly once and threaded to all sub-calls,
    avoiding redundant SSH round-trips.

    Raises RuntimeError if the profile cannot be built (no SSH, parse failure).
    """
    live_fp = _compute_config_fingerprint(run_show, device)

    if existing_profile is not None and live_fp:
        cache_file = _DUT_PROFILE_CACHE_DIR / f"dut_profile_{device}.json"
        stored_fp = ""
        if cache_file.exists():
            try:
                stored_fp = json.loads(cache_file.read_text()).get("_fingerprint", "")
            except Exception:
                pass
        if stored_fp and live_fp == stored_fp:
            return existing_profile

    cached = load_dut_profile_cache(device, _precomputed_fp=live_fp)
    if cached is not None:
        return cached

    profile = build_dut_profile(params, run_show, device)
    save_dut_profile_cache(profile, fingerprint=live_fp)
    return profile


def provision_spirent_vpls_cp(
    device: str,
    run_show: Callable[[str, str], str],
    skip_spirent: bool = False,
    defer_protocol_start: bool = True,
    profile: Optional[DUTProfile] = None,
) -> ProvisionResult:
    """Run the full spirent_vpls_cp provisioning chain.

    Args:
        device: DUT hostname (for run_show calls).
        run_show: Callable(device, command) -> output.
        skip_spirent: If True, only provision PE-1 config (skip Spirent steps).
        defer_protocol_start: If True (default), configure VPLS device + protocols
            but do NOT start them. This prevents stc.apply() hangs when later
            creating MAC learning devices. Call spirent_tool.py protocol-start
            explicitly when a PW scenario trigger needs protocols running.
            STC HANG WARNING: starting ISIS+LDP+BGP protocols causes every
            subsequent stc.apply() to take 60-180s (full re-convergence).
        profile: Optional DUTProfile with live device params. When provided,
            all provisioning uses DUT-derived values instead of hardcoded constants.

    Returns:
        ProvisionResult with all step outcomes and extracted parameters.
    """
    if profile is None:
        logger.warning(
            "[WARN] provision_spirent_vpls_cp called WITHOUT DUTProfile -- "
            "using hardcoded constants. Build a profile first for accurate provisioning."
        )
    result = ProvisionResult()

    _asn = profile.bgp_asn if profile else DUT_BGP_ASN
    _rid = profile.router_id if profile else DUT_ROUTER_ID
    _evpn_name = profile.pw_test_evpn_name if profile else PW_TEST_EVPN_NAME
    _evpn_rt = profile.pw_test_evpn_rt if profile else PW_TEST_EVPN_RT
    _vpls_rt = profile.pw_test_vpls_rt if profile else PW_TEST_VPLS_RT
    _evi = profile.pw_test_evi if profile else PW_TEST_EVI
    _site_id = profile.vpls_site_id if profile else PW_TEST_SITE_ID
    _ac_subif = profile.pw_test_ac_subif if profile else PW_TEST_AC_SUBIF
    _ac_outer = profile.pw_test_ac_outer if profile else PW_TEST_AC_OUTER
    _ac_inner = profile.pw_test_ac_inner if profile else PW_TEST_AC_INNER
    _vpls_peer_ip = profile.vpls_neighbor_ip if profile else VPLS_PEER_IP
    _vpls_peer_gw = profile.vpls_neighbor_gw if profile else VPLS_PEER_GW
    _vpls_outer = profile.vpls_neighbor_outer_vlan if profile else VPLS_PEER_OUTER_VLAN
    _vpls_inner = profile.vpls_neighbor_inner_vlan if profile else VPLS_PEER_INNER_VLAN
    _isis_area = profile.vpls_isis_area if profile else VPLS_ISIS_AREA
    _update_src = profile.vpls_isis_interface if profile else VPLS_BGP_UPDATE_SOURCE
    _lbl_block = profile.vpls_label_block_size if profile else VPLS_LABEL_BLOCK_SIZE
    _ve_id = profile.pw_test_ve_id if profile else PW_TEST_VE_ID

    if not _check_and_fix_label_pool(device, run_show, result):
        return result

    if not _check_and_fix_bgp_vpls_af(device, run_show, result, asn=_asn):
        return result

    if not _check_and_create_ac_interface(device, run_show, result,
                                          ac_subif=_ac_subif, ac_outer=_ac_outer, ac_inner=_ac_inner):
        return result

    if not _check_and_create_evpn_instance(device, run_show, result,
                                           asn=_asn, router_id=_rid,
                                           evpn_name=_evpn_name, evpn_rt=_evpn_rt,
                                           vpls_rt=_vpls_rt, evi=_evi,
                                           site_id=_site_id, ac_subif=_ac_subif):
        return result

    if not _check_and_create_bgp_neighbor(device, run_show, result,
                                          asn=_asn, neighbor_ip=_vpls_peer_ip,
                                          update_source=_update_src):
        return result

    if skip_spirent:
        result.add("spirent_skipped", "SKIP", "Spirent steps skipped (skip_spirent=True)")
        return result

    if not _create_spirent_vpls_device(result,
                                       ip=_vpls_peer_ip, gw=_vpls_peer_gw,
                                       outer_vlan=_vpls_outer, inner_vlan=_vpls_inner):
        return result

    if not _configure_spirent_isis(result, area_id=_isis_area):
        return result

    if not _configure_spirent_ldp(result):
        return result

    if not _configure_spirent_bgp_vpls(result,
                                       asn=_asn, neighbor_gw=_vpls_peer_gw,
                                       vpls_rt=_vpls_rt, evi=_evi,
                                       ve_id=_ve_id, block_size=_lbl_block):
        return result

    if defer_protocol_start:
        result.add("spirent_proto_start", "DEFERRED",
                    "Protocols configured but NOT started. "
                    "Call protocol-start when PW scenario trigger needs them. "
                    "This prevents 60-180s stc.apply() hangs from ISIS+LDP+BGP re-convergence.")
        result.protocols_deferred = True
    else:
        _start_spirent_protocols(result)
        _validate_pw_state(device, run_show, result, wait_sec=60)

    # TEST: description tags -- idempotent, safe to call on every run.
    # Enables `show config | flatten | include TEST:mac_mobility` for instant
    # ownership snapshot and `spirent_tool.py footprint --dut <ip>` to
    # cross-check state (interface admin/oper + BGP peer state) in one shot.
    try:
        from .test_description_tagger import apply_test_descriptions
        apply_test_descriptions(
            device=device,
            run_show=run_show,
            result=result,
            test_id="mac_mobility",
            commit_fn=_cfg_commit,
            cfg_block_fn=_cfg_block,
            step_name="test_desc_tags_vpls",
            objects=[
                (f"network-services evpn instance {_evpn_name}",
                 f"evpn-instance/vpls-pw/evi{_evi}"),
                (f"interfaces {_ac_subif}",
                 f"evpn-ac/pw/outer{_ac_outer}+inner{_ac_inner}"),
                (f"protocols bgp {_asn} neighbor {_vpls_peer_ip}",
                 f"vpls-peer/v{_vpls_outer}+{_vpls_inner}/as{_asn}"),
            ],
        )
    except Exception as _tag_exc:  # noqa: BLE001 -- tagging is best-effort
        result.add("test_desc_tags_vpls", "WARN",
                   f"description tagging failed (non-fatal): {_tag_exc}")

    return result


def _create_spirent_vpls_device_2(result: ProvisionResult) -> bool:
    """Create second Spirent emulated device for pw_pw testing."""
    status_out = _run_spirent(["status", "--json"])
    try:
        status = json.loads(status_out)
        for d in status.get("devices", []):
            if d.get("name") == VPLS_DEVICE2_NAME:
                result.add("spirent_device_2", "PASS",
                           f"{VPLS_DEVICE2_NAME} already exists")
                return True
    except json.JSONDecodeError:
        pass

    result.add("spirent_device_2", "FIX", f"Creating {VPLS_DEVICE2_NAME}")
    out = _run_spirent([
        "create-device",
        "--name", VPLS_DEVICE2_NAME,
        "--ip", VPLS_PEER2_IP,
        "--gateway", VPLS_PEER2_GW,
        "--vlan", str(VPLS_PEER_OUTER_VLAN),
        "--inner-vlan", str(VPLS_PEER2_INNER_VLAN),
        "--mac", "00:10:94:00:04:04",
        "--device-count", "1",
    ])
    if "ERROR" in out and "already exists" not in out:
        result.add("spirent_device_2_create", "FAIL", out[:200])
        return False
    result.add("spirent_device_2", "PASS",
               f"{VPLS_DEVICE2_NAME} at {VPLS_PEER2_IP}")
    return True


def _configure_spirent_isis_2(result: ProvisionResult) -> bool:
    """Configure ISIS on the second Spirent device (shared loopback)."""
    out = _run_spirent([
        "isis-peer",
        "--device-name", VPLS_DEVICE2_NAME,
        "--system-id", VPLS_PEER2_SYSTEM_ID,
        "--area-id", VPLS_ISIS_AREA,
        "--level", "LEVEL2",
        "--loopback", VPLS_SHARED_LOOPBACK,
        "--loopback-metric", "10",
    ])
    if "[OK]" in out:
        result.add("spirent_isis_2", "PASS",
                    f"ISIS configured: lo={VPLS_SHARED_LOOPBACK}/32")
        return True
    result.add("spirent_isis_2", "FAIL", out[:200])
    return False


def _configure_spirent_ldp_2(result: ProvisionResult) -> bool:
    """Configure LDP on the second Spirent device (shared loopback)."""
    out = _run_spirent([
        "ldp-peer",
        "--device-name", VPLS_DEVICE2_NAME,
        "--router-id", VPLS_SHARED_LOOPBACK,
        "--transport-address", VPLS_SHARED_LOOPBACK,
        "--fec-prefix", VPLS_SHARED_LOOPBACK,
    ])
    if "[OK]" in out:
        result.add("spirent_ldp_2", "PASS",
                    f"LDP configured: router-id={VPLS_SHARED_LOOPBACK}")
        return True
    result.add("spirent_ldp_2", "FAIL", out[:200])
    return False


def _configure_spirent_bgp_vpls_2(result: ProvisionResult) -> bool:
    """Configure BGP l2vpn-vpls on the second Spirent device."""
    out = _run_spirent([
        "bgp-peer",
        "--device-name", VPLS_DEVICE2_NAME,
        "--as", str(DUT_BGP_ASN),
        "--dut-as", str(DUT_BGP_ASN),
        "--neighbor", VPLS_PEER2_GW,
        "--negotiate-afi", "l2vpn-vpls",
        "--vpls-nexthop", VPLS_SHARED_LOOPBACK,
        "--vpls-rd", f"{VPLS_PEER2_IP}:{PW_TEST_EVI}",
        "--vpls-rt", PW_TEST_VPLS_RT,
        "--vpls-ve-id", str(VPLS_PEER2_VE_ID),
        "--vpls-block-size", str(VPLS_LABEL_BLOCK_SIZE),
    ])
    if "ESTABLISHED" in out or "[OK]" in out:
        result.add("spirent_bgp_vpls_2", "PASS",
                    f"BGP l2vpn-vpls configured toward {DUT_ROUTER_ID}")
        return True
    if "not ESTABLISHED" in out.lower() or "WARNING" in out:
        result.add("spirent_bgp_vpls_2", "WARN",
                    "BGP configured but session not yet ESTABLISHED")
        return True
    result.add("spirent_bgp_vpls_2", "FAIL", out[:300])
    return False


def _check_and_create_bgp_neighbor_2(
    device: str,
    run_show: Callable[[str, str], str],
    result: ProvisionResult,
    asn: int = DUT_BGP_ASN,
) -> bool:
    """Configure second BGP neighbor on DUT for Spirent peer 2."""
    neighbor_ip = VPLS_PEER2_IP

    output = run_show(
        device,
        f"show config protocols bgp {asn} | flatten | include {neighbor_ip} | no-more",
    )
    if neighbor_ip in output and "l2vpn-vpls" in output:
        result.add("bgp_neighbor_2", "PASS",
                    f"BGP neighbor {neighbor_ip} already configured")
        return True

    result.add("bgp_neighbor_2", "FIX",
               f"Adding BGP neighbor {neighbor_ip} with l2vpn-vpls")

    _cfg_block(run_show, device, [
        f"protocols bgp {asn} neighbor {neighbor_ip}",
        "admin-state enabled",
        f"remote-as {asn}",
        "update-source ge400-0/0/5.4",
    ])

    _cfg_block(run_show, device, [
        f"protocols bgp {asn} neighbor {neighbor_ip}",
        "address-family l2vpn-vpls",
        "send-community community-type both",
        "soft-reconfiguration inbound",
    ])

    ok, commit_out = _cfg_commit(run_show, device)
    if not ok:
        result.add("bgp_neighbor_2_commit", "FAIL", commit_out[:200])
        return False
    result.add("bgp_neighbor_2", "PASS",
               f"BGP neighbor {neighbor_ip} configured")
    return True


def provision_spirent_vpls_cp_dual(
    device: str,
    run_show: Callable[[str, str], str],
    skip_spirent: bool = False,
    profile: Optional[DUTProfile] = None,
) -> ProvisionResult:
    """Provision two VPLS peers for pw_pw (PW-to-PW move) testing.

    Both STC devices share the same ISIS loopback (VPLS_SHARED_LOOPBACK)
    because STC devices on the same port share a single ISIS instance.
    Each peer uses a different VE-ID so the DUT creates two distinct PWs
    with separate ingress labels.  ISIS provides the IGP route that LDP
    needs to install MPLS labels (DNOS LDP ignores static routes).
    """
    result = provision_spirent_vpls_cp(device, run_show, skip_spirent, profile=profile)

    if not result.ready and not skip_spirent:
        return result

    if not _check_and_create_bgp_neighbor_2(device, run_show, result):
        return result

    if skip_spirent:
        return result

    if not _create_spirent_vpls_device_2(result):
        return result

    if not _configure_spirent_isis_2(result):
        return result

    if not _configure_spirent_ldp_2(result):
        return result

    if not _configure_spirent_bgp_vpls_2(result):
        return result

    _start_spirent_protocols(result)

    # No pre-sleep -- _validate_pw_state polls (5s interval) up to wait_sec for
    # the PW row to appear, so it tolerates startup latency event-driven.
    _validate_pw_state(device, run_show, result, wait_sec=70)

    # TEST: description tag on the second VPLS BGP neighbor (first is already
    # tagged by provision_spirent_vpls_cp). Makes pw_pw scenario peers instantly
    # visible to the prereq gate's tag-based classifier.
    _asn_dual = profile.bgp_asn if profile else DUT_BGP_ASN
    _outer_dual = VPLS_PEER_OUTER_VLAN  # both peers share the same outer VLAN
    try:
        from .test_description_tagger import apply_test_descriptions
        apply_test_descriptions(
            device=device,
            run_show=run_show,
            result=result,
            test_id="mac_mobility",
            commit_fn=_cfg_commit,
            cfg_block_fn=_cfg_block,
            step_name="test_desc_tags_vpls_peer2",
            objects=[
                (f"protocols bgp {_asn_dual} neighbor {VPLS_PEER2_IP}",
                 f"vpls-peer2/v{_outer_dual}+{VPLS_PEER2_INNER_VLAN}/as{_asn_dual}"),
            ],
        )
    except Exception as _tag_exc:  # noqa: BLE001 -- tagging is best-effort
        result.add("test_desc_tags_vpls_peer2", "WARN",
                   f"description tagging failed (non-fatal): {_tag_exc}")

    return result


def rebuild_spirent_session(timeout: int = 45) -> bool:
    """Reconnect + reserve port after a Lab Server session drop.

    This is the fast-path for recovery when the STC session dies
    mid-test (404 errors). Avoids recreating devices if possible
    by first trying to rejoin the existing dn_spirent_main session.

    Returns True on success.
    """
    out = _run_spirent(["connect"], timeout=timeout)
    if "[ERROR]" in out or "[TIMEOUT]" in out:
        out = _run_spirent(["connect", "--force-new"], timeout=timeout)
        if "[ERROR]" in out or "[TIMEOUT]" in out:
            return False
    reserve_out = _run_spirent(["reserve"], timeout=30)
    return "[ERROR]" not in reserve_out and "[TIMEOUT]" not in reserve_out


# NOTE: previous helper `rebuild_full_vpls_evpn_infra` was removed in PR7d
# (2026-04-14). No code path called it; recovery flows go through
# `rebuild_spirent_session` + `provision_spirent_vpls_cp(_dual)` directly,
# which keeps the recovery footprint smaller and avoids the unused
# `need_evpn_peer` branch.


def check_spirent_vpls_cp_ready(
    device: str,
    run_show: Callable[[str, str], str],
    profile: Optional[DUTProfile] = None,
) -> Dict[str, Any]:
    """Quick check if spirent_vpls_cp infrastructure is already provisioned.

    Returns dict with 'ready' bool and details of what's missing.
    """
    _asn = profile.bgp_asn if profile else DUT_BGP_ASN
    _evpn_name = profile.pw_test_evpn_name if profile else PW_TEST_EVPN_NAME
    _ac_subif = profile.pw_test_ac_subif if profile else PW_TEST_AC_SUBIF
    _nbr_ip = profile.vpls_neighbor_ip if profile else VPLS_BGP_NEIGHBOR_IP

    checks = {}

    label_out = run_show(device, "show mpls label-allocation tables | no-more")
    checks["label_pool"] = "bgp-vpls" in label_out

    af_out = run_show(device, f"show config protocols bgp {_asn} | flatten | include l2vpn-vpls | no-more")
    checks["bgp_vpls_af"] = "l2vpn-vpls" in af_out

    evpn_out = run_show(device, f"show config network-services evpn instance {_evpn_name} | no-more")
    checks["evpn_instance"] = _evpn_name in evpn_out

    ac_out = run_show(device, f"show config interfaces {_ac_subif} | no-more")
    checks["ac_interface"] = "l2-service" in ac_out

    nbr_out = run_show(
        device,
        f"show config protocols bgp {_asn} | flatten | include {_nbr_ip} | no-more",
    )
    checks["bgp_neighbor"] = _nbr_ip in nbr_out

    vpls_pw_out = run_show(device, "show evpn vpls-pw | no-more")
    checks["pw_exists"] = _evpn_name in vpls_pw_out

    nbr2_out = run_show(
        device,
        f"show config protocols bgp {_asn} | flatten | include {VPLS_PEER2_IP} | no-more",
    )
    checks["bgp_neighbor_2"] = VPLS_PEER2_IP in nbr2_out

    all_ready = all(checks.values())
    missing = [k for k, v in checks.items() if not v]

    return {
        "ready": all_ready,
        "checks": checks,
        "missing": missing,
    }


# ---------------------------------------------------------------------------
# EVPN BGP Peer provisioning (for SC02: remote EVPN RT-2 via RR-SA-2)
# ---------------------------------------------------------------------------

def _create_spirent_evpn_device(
    result: ProvisionResult,
    ip: str = EVPN_PEER_IP,
    gw: str = EVPN_PEER_GW,
    outer_vlan: int = VPLS_PEER_OUTER_VLAN,
    inner_vlan: int = EVPN_PEER_INNER_VLAN,
) -> bool:
    """Create Spirent emulated device for EVPN BGP peering."""
    status_out = _run_spirent(["status", "--json"])
    try:
        status = json.loads(status_out)
        for d in status.get("devices", []):
            if d.get("name") == EVPN_DEVICE_NAME:
                result.add("spirent_evpn_device", "PASS",
                           f"{EVPN_DEVICE_NAME} already exists")
                return True
    except json.JSONDecodeError:
        pass

    result.add("spirent_evpn_device", "FIX", f"Creating {EVPN_DEVICE_NAME}")
    out = _run_spirent([
        "create-device",
        "--name", EVPN_DEVICE_NAME,
        "--ip", ip,
        "--gateway", gw,
        "--vlan", str(outer_vlan),
        "--inner-vlan", str(inner_vlan),
        "--mac", "00:10:94:00:05:05",
        "--device-count", "1",
    ])
    if "ERROR" in out and "already exists" not in out:
        result.add("spirent_evpn_device_create", "FAIL", out[:200])
        return False
    result.add("spirent_evpn_device", "PASS",
               f"{EVPN_DEVICE_NAME} at {ip} (vlan {outer_vlan}/{inner_vlan})")
    return True


def _configure_spirent_evpn_isis(result: ProvisionResult) -> bool:
    """Configure ISIS on the EVPN Spirent device (shared loopback)."""
    out = _run_spirent([
        "isis-peer",
        "--device-name", EVPN_DEVICE_NAME,
        "--system-id", EVPN_PEER_SYSTEM_ID,
        "--area-id", VPLS_ISIS_AREA,
        "--level", "LEVEL2",
        "--loopback", VPLS_SHARED_LOOPBACK,
        "--loopback-metric", "10",
    ])
    if "[OK]" in out:
        result.add("spirent_evpn_isis", "PASS",
                    f"ISIS configured: sys-id={EVPN_PEER_SYSTEM_ID}, lo={VPLS_SHARED_LOOPBACK}/32")
        return True
    result.add("spirent_evpn_isis", "FAIL", out[:200])
    return False


def _configure_spirent_evpn_ldp(result: ProvisionResult) -> bool:
    """Configure LDP on the EVPN Spirent device (shared loopback)."""
    out = _run_spirent([
        "ldp-peer",
        "--device-name", EVPN_DEVICE_NAME,
        "--router-id", VPLS_SHARED_LOOPBACK,
        "--transport-address", VPLS_SHARED_LOOPBACK,
        "--fec-prefix", VPLS_SHARED_LOOPBACK,
    ])
    if "[OK]" in out:
        result.add("spirent_evpn_ldp", "PASS",
                    f"LDP configured: router-id={VPLS_SHARED_LOOPBACK}")
        return True
    result.add("spirent_evpn_ldp", "FAIL", out[:200])
    return False


def _configure_spirent_evpn_bgp(
    result: ProvisionResult,
    evpn_rt: str = "100:100",
    evpn_mac: str = "00:DE:AD:00:02:02",
    nexthop_override: str = "",
    asn: int = PE1_ASN,
    neighbor: str = EVPN_BGP_NEIGHBOR,
) -> bool:
    """Configure BGP L2VPN EVPN on the Spirent device toward DUT directly.

    nexthop_override: when bgp_only=True, use the directly connected IP
    so the DUT can resolve the NextHop without MPLS tunnel.
    When using ISIS/LDP, use VPLS_SHARED_LOOPBACK.
    """
    nh = nexthop_override or VPLS_SHARED_LOOPBACK
    rd_prefix = nexthop_override or VPLS_SHARED_LOOPBACK
    _bgp_args = [
        "bgp-peer",
        "--device-name", EVPN_DEVICE_NAME,
        "--as", str(asn),
        "--dut-as", str(asn),
        "--neighbor", neighbor,
        "--negotiate-afi", "l2vpn-evpn",
        "--evpn-rd", f"{rd_prefix}:500",
        "--evpn-rt", evpn_rt,
        "--evpn-mac", evpn_mac,
        "--evpn-nexthop", nh,
        "--no-start",
    ]
    out = _run_spirent(_bgp_args, timeout=120)
    if "ESTABLISHED" in out or "[OK]" in out:
        result.add("spirent_evpn_bgp", "PASS",
                    f"BGP l2vpn-evpn configured (ASN={asn}, neighbor={neighbor})")
        return True
    if "not ESTABLISHED" in out.lower() or "WARNING" in out or "[TIMEOUT]" in out:
        result.add("spirent_evpn_bgp", "PASS",
                    "BGP l2vpn-evpn configured (deferred start, DUT-side check will follow)")
        return True
    result.add("spirent_evpn_bgp", "FAIL", out[:300])
    return False


def _configure_pe1_evpn_neighbor(
    run_show: Callable[[str, str], str],
    result: ProvisionResult,
    asn: int = PE1_ASN,
    peer_ip: str = EVPN_PEER_IP,
    mgmt_ip: str = PE1_MGMT_IP,
    device: str = "PE-1",
) -> bool:
    """Configure DUT to accept BGP L2VPN EVPN from the Spirent peer.

    Uses run_show (MCP or device_runner) for all DUT commands -- same
    pattern as the VPLS neighbor provisioner. No separate SSH session.
    """
    try:
        existing = run_show(device,
            f"show config protocols bgp {asn} "
            f"neighbor {peer_ip} | flatten | no-more"
        )
        if peer_ip in existing and "admin-state enabled" in existing:
            result.add("pe1_evpn_neighbor", "PASS",
                       f"DUT neighbor {peer_ip} already configured")
            return True

        result.add("pe1_evpn_neighbor", "FIX",
                   f"Adding neighbor {peer_ip} to DUT BGP {asn}")

        _cfg_block(run_show, device, [
            f"protocols bgp {asn} neighbor {peer_ip} remote-as {asn}",
            f"protocols bgp {asn} neighbor {peer_ip} admin-state enabled",
            f"protocols bgp {asn} neighbor {peer_ip} address-family l2vpn-evpn",
            f"protocols bgp {asn} neighbor {peer_ip} address-family l2vpn-evpn as-loop-check disabled",
            f"protocols bgp {asn} neighbor {peer_ip} address-family l2vpn-evpn send-community community-type both",
            f"protocols bgp {asn} neighbor {peer_ip} address-family l2vpn-evpn soft-reconfiguration inbound",
        ])
        ok, commit_out = _cfg_commit(run_show, device)
        if not ok:
            result.add("pe1_commit", "FAIL", commit_out[:200])
            _force_session_to_operational(run_show, device)
            return False

        result.add("pe1_evpn_neighbor", "PASS",
                   f"DUT neighbor {peer_ip} configured "
                   f"(l2vpn-evpn, as-loop-check disabled)")
        return True

    except Exception as e:
        result.add("pe1_evpn_neighbor", "FAIL", f"DUT config failed: {e}")
        _force_session_to_operational(run_show, device)
        return False


def _verify_evpn_bgp_established(
    run_show: Callable[[str, str], str],
    result: ProvisionResult,
    wait_sec: int = 60,
    device: str = "PE-1",
    peer_ip: str = EVPN_PEER_IP,
) -> bool:
    """Wait for EVPN BGP session to establish on the DUT.

    Uses `poll_until` (event-driven) instead of fixed 5s sleeps -- exits the
    moment `state` becomes numeric (PFXrcd) which is DNOS's ESTABLISHED marker.
    """
    result.add("evpn_bgp_verify", "INFO",
               f"Polling up to {wait_sec}s for EVPN BGP session to {peer_ip}...")

    def _check() -> Tuple[bool, Any]:
        try:
            summary = run_show(device, "show bgp l2vpn evpn summary | no-more")
        except Exception as e:
            return False, f"run_show error: {e}"
        for line in summary.splitlines():
            if peer_ip not in line:
                continue
            parts = line.split()
            if len(parts) < 9:
                return False, f"line malformed: {line!r}"
            state = parts[-1]
            if state.isdigit() or state == "0":
                return True, {"peer": peer_ip, "state": state, "line": line.strip()}
            return False, f"state={state} (waiting for numeric/0 = PFXrcd)"
        return False, f"peer {peer_ip} not yet in 'show bgp l2vpn evpn summary'"

    poll = poll_until(_check, timeout_sec=float(wait_sec), interval_sec=5.0,
                      progress_label="evpn_bgp_established")
    if poll.passed:
        obs = poll.last_value or {}
        result.add("evpn_bgp_verify", "PASS",
                   f"EVPN BGP ESTABLISHED with {peer_ip} (state={obs.get('state','?')}, "
                   f"after {poll.elapsed_sec:.1f}s, {poll.attempts} poll(s))")
        return True

    result.add("evpn_bgp_verify", "FAIL",
               f"EVPN BGP with {peer_ip} not ESTABLISHED after {wait_sec}s "
               f"(last_observed={poll.last_value!r})")
    return False


def provision_spirent_evpn_peer(
    device: str,
    run_show: Callable[[str, str], str],
    evpn_rt: str = "100:100",
    evpn_mac: str = "00:DE:AD:00:02:02",
    bgp_only: bool = False,
    defer_protocol_start: bool = False,
    profile: Optional[DUTProfile] = None,
) -> ProvisionResult:
    """Provision Spirent EVPN BGP peer for remote RT-2 injection via direct DUT peering.

    bgp_only=True (RECOMMENDED): Skip ISIS/LDP, use direct BGP TCP peering only.
    defer_protocol_start=True: Configure device+BGP but do NOT start protocols.
    Caller is responsible for calling protocol-start after all devices are set up.
    This prevents STC crashes from interleaved protocol starts.
    profile: Optional DUTProfile for DUT-derived parameters.
    """
    if profile is None:
        logger.warning(
            "[WARN] provision_spirent_evpn_peer called WITHOUT DUTProfile -- "
            "using hardcoded constants. Build a profile first for accurate provisioning."
        )
    result = ProvisionResult()

    _asn = profile.bgp_asn if profile else PE1_ASN
    _evpn_ip = profile.evpn_neighbor_ip if profile else EVPN_PEER_IP
    _evpn_gw = profile.evpn_neighbor_gw if profile else EVPN_PEER_GW
    _evpn_outer = profile.evpn_neighbor_outer_vlan if profile else VPLS_PEER_OUTER_VLAN
    _evpn_inner = profile.evpn_neighbor_inner_vlan if profile else EVPN_PEER_INNER_VLAN
    _bgp_neighbor = _evpn_gw

    if not _create_spirent_evpn_device(result, ip=_evpn_ip, gw=_evpn_gw,
                                       outer_vlan=_evpn_outer, inner_vlan=_evpn_inner):
        return result

    if not bgp_only:
        if not _configure_spirent_evpn_isis(result):
            return result
        if not _configure_spirent_evpn_ldp(result):
            return result
    else:
        result.add("spirent_evpn_isis", "SKIP",
                    "ISIS skipped (bgp_only=True, direct connected peering)")
        result.add("spirent_evpn_ldp", "SKIP",
                    "LDP skipped (bgp_only=True, no MPLS tunnel needed for control plane)")

    if not _configure_pe1_evpn_neighbor(run_show, result, asn=_asn,
                                        peer_ip=_evpn_ip, device=device):
        return result

    evpn_nh = _evpn_ip if bgp_only else VPLS_SHARED_LOOPBACK
    if not _configure_spirent_evpn_bgp(result, evpn_rt=evpn_rt, evpn_mac=evpn_mac,
                                       nexthop_override=evpn_nh, asn=_asn,
                                       neighbor=_bgp_neighbor):
        return result

    if defer_protocol_start:
        result.add("spirent_evpn_proto_start", "DEFERRED",
                    "Protocols configured but NOT started. Caller will start all devices together.")
        result.protocols_deferred = True
    else:
        _run_spirent(["protocol-start", "--device-name", EVPN_DEVICE_NAME])
        result.add("spirent_evpn_proto_start", "PASS", "Protocols started on EVPN peer")
        # No fixed pre-sleep -- _verify_evpn_bgp_established polls 60s, returns
        # the moment the peer reaches PFXrcd state (event-driven).
        _verify_evpn_bgp_established(run_show, result, wait_sec=60,
                                     device=device, peer_ip=_evpn_ip)

    result.pw_active = True
    result.params["spirent_evpn_device"] = EVPN_DEVICE_NAME
    result.params["evpn_bgp_neighbor"] = _bgp_neighbor
    result.params["bgp_only_mode"] = str(bgp_only)

    # TEST: description tag on the DUT BGP neighbor we just provisioned.
    # The prereq gate's description-owner classifier uses this to count only
    # test-relevant peers (vs legacy stubs like 2.2.2.2 that never converge).
    # Idempotent: on re-runs the tagger sees the tag is already in place and
    # skips the commit entirely.
    #
    # CRITICAL: the DUT's BGP neighbor IP is the SPIRENT peer IP (_evpn_ip,
    # e.g. 19.19.19.2) -- not the gateway (_evpn_gw, DUT's own interface IP
    # 19.19.19.1). Using _bgp_neighbor (= _evpn_gw) here would try to tag a
    # non-existent `neighbor 19.19.19.1` on the DUT, implicitly create it,
    # and blow up the commit-check with "Missing remote-as". Always tag
    # _evpn_ip (the remote peer address the DUT peers with).
    try:
        from .test_description_tagger import apply_test_descriptions
        _evpn_role = (
            f"evpn-peer/v{_evpn_outer}+{_evpn_inner}/as{_asn}"
            if _evpn_inner is not None else
            f"evpn-peer/v{_evpn_outer}/as{_asn}"
        )
        apply_test_descriptions(
            device=device,
            run_show=run_show,
            result=result,
            test_id="mac_mobility",
            commit_fn=_cfg_commit,
            cfg_block_fn=_cfg_block,
            step_name="test_desc_tags_evpn_peer",
            objects=[
                (f"protocols bgp {_asn} neighbor {_evpn_ip}", _evpn_role),
            ],
        )
    except Exception as _tag_exc:  # noqa: BLE001 -- tagging is best-effort
        result.add("test_desc_tags_evpn_peer", "WARN",
                   f"description tagging failed (non-fatal): {_tag_exc}")

    return result
