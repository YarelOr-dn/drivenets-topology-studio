#!/usr/bin/env python3
"""Runtime helpers for the PW scale MAC-mobility HA recipe.

The helpers are deliberately small and composable so the recipe can run a
scale=10 smoke, resume after a partial chunk, or execute the full 200-service
profile without changing the service-generation rules.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    from .pw_scale_builder import (
        DEFAULT_PE4_DEVICE,
        DEFAULT_RR_DEVICE,
        ServiceRow,
        build_expected_traffic,
        chunk_rows,
        render_delete_config,
        render_device_config,
    )
except ImportError:  # pragma: no cover - direct script execution fallback
    from pw_scale_builder import (  # type: ignore
        DEFAULT_PE4_DEVICE,
        DEFAULT_RR_DEVICE,
        ServiceRow,
        build_expected_traffic,
        chunk_rows,
        render_delete_config,
        render_device_config,
    )


MCP_HEALTH_URL = os.environ.get("DNOS_CONFIG_MCP_HEALTH", "http://localhost:9300/health")
DNOS_CONFIG_MCP_PATH = os.environ.get("DNOS_CONFIG_MCP_PATH", "/home/dn/dnos_config_mcp")
SPIRENT_TOOL = Path.home() / "SCALER" / "SPIRENT" / "spirent_tool.py"
SPIRENT_SESSION_PATH = Path.home() / "SCALER" / "SPIRENT" / "sessions" / "dn_spirent_main.json"
ACTIVE_SESSION_PATH = Path.home() / "SCALER" / "TEST" / "active_test_session.json"
ProgressCallback = Callable[[str, Dict[str, Any]], None]
MCP_HANDLE_LOCK = threading.Lock()
MCP_HANDLE = None


@dataclass
class PhaseResult:
    phase: str
    ok: bool
    detail: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _probe_mcp():
    """Return the in-process dnos-config MCP dispatcher or raise RuntimeError.

    Python orchestrators cannot invoke Cursor's native MCP tool surface directly.
    Keep this as the in-process fallback for long-running recipe code, but cache
    the dispatcher and do not serialize every call. DNAAS preflight phases rely
    on ThreadPoolExecutor to overlap independent read-only checks.
    """

    global MCP_HANDLE
    if MCP_HANDLE is not None:
        return MCP_HANDLE

    try:
        with urllib.request.urlopen(MCP_HEALTH_URL, timeout=5.0) as resp:
            data = json.loads(resp.read())
            if data.get("status") != "ok":
                raise RuntimeError(f"MCP health not ok: {data}")
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"dnos-config MCP unavailable at {MCP_HEALTH_URL}: {exc}") from exc

    with MCP_HANDLE_LOCK:
        if MCP_HANDLE is not None:
            return MCP_HANDLE
        if DNOS_CONFIG_MCP_PATH not in sys.path:
            sys.path.insert(0, DNOS_CONFIG_MCP_PATH)
        from dnos_config_mcp.tools import handle_tool_call  # type: ignore

        MCP_HANDLE = handle_tool_call
        return MCP_HANDLE


def mcp_call(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    handle = _probe_mcp()
    if os.environ.get("TEST_MCP_SERIALIZE_CALLS") == "1":
        with MCP_HANDLE_LOCK:
            res = handle(tool_name, args)
    else:
        res = handle(tool_name, args)
    if not isinstance(res, dict):
        raise RuntimeError(f"{tool_name} returned {type(res).__name__}, expected dict")
    return res


def run_show_commands(device_name: str, commands: Sequence[str]) -> Dict[str, Any]:
    return mcp_call(
        "dnos_run_show_commands",
        {"device_name": device_name, "commands": list(commands), "format": "json"},
    )


def apply_config_chunks(
    rows: Sequence[ServiceRow],
    *,
    chunk_size: int = 25,
    mode: str = "all_or_nothing",
    dry_run: bool = False,
    progress: Optional[ProgressCallback] = None,
) -> List[PhaseResult]:
    """Apply PE-4 and RR-SA-2 service config in paired transactional chunks."""

    results: List[PhaseResult] = []
    commit_mode = "dry_run" if dry_run else mode
    chunks = chunk_rows(rows, chunk_size)
    for chunk_index, chunk in enumerate(chunks, start=1):
        if progress:
            progress(
                "bulk_config_chunk_start",
                {
                    "chunk_index": chunk_index,
                    "chunk_total": len(chunks),
                    "first_service": chunk[0].name,
                    "last_service": chunk[-1].name,
                    "service_count": len(chunk),
                },
            )
        pe4_cfg = render_device_config(DEFAULT_PE4_DEVICE, chunk)
        rr_cfg = render_device_config(DEFAULT_RR_DEVICE, chunk)
        verify = [
            f"show evpn instance {row.name} detail | no-more"
            for row in (chunk[0], chunk[-1])
        ]
        args = {
            "mode": commit_mode,
            "format": "json",
            "parallelism": 2,
            "targets": [
                {
                    "device_name": DEFAULT_PE4_DEVICE,
                    "config_text": pe4_cfg,
                    "verify_commands": verify,
                },
                {
                    "device_name": DEFAULT_RR_DEVICE,
                    "config_text": rr_cfg,
                    "verify_commands": verify,
                },
            ],
            "line_timeout_sec": 5,
            "commit_timeout_sec": 180,
        }
        try:
            res = mcp_call("dnos_multi_device_commit", args)
            ok = bool(res.get("ok", False))
            detail = res.get("summary_markdown") or json.dumps(res)[:1000]
        except Exception as exc:  # noqa: BLE001
            ok = False
            detail = f"{type(exc).__name__}: {exc}"
            res = {"error": detail}

        results.append(
            PhaseResult(
                phase=f"bulk_config_chunk_{chunk_index:02d}",
                ok=ok,
                detail=detail,
                data={
                    "chunk_index": chunk_index,
                    "count": len(chunk),
                    "first_service": chunk[0].name,
                    "last_service": chunk[-1].name,
                    "mcp_result": res,
                },
            )
        )
        if progress:
            progress(
                "bulk_config_chunk_done",
                {
                    "chunk_index": chunk_index,
                    "chunk_total": len(chunks),
                    "ok": ok,
                    "first_service": chunk[0].name,
                    "last_service": chunk[-1].name,
                },
            )
        if not ok:
            break
    return results


def cleanup_config_chunks(
    rows: Sequence[ServiceRow],
    *,
    chunk_size: int = 25,
    dry_run: bool = False,
) -> List[PhaseResult]:
    """Remove services and AC subinterfaces in reverse chunk order."""

    results: List[PhaseResult] = []
    chunks = chunk_rows(rows, chunk_size)
    for chunk_index, chunk in reversed(list(enumerate(chunks, start=1))):
        args = {
            "mode": "dry_run" if dry_run else "all_or_nothing",
            "format": "json",
            "parallelism": 2,
            "targets": [
                {
                    "device_name": DEFAULT_PE4_DEVICE,
                    "config_text": render_delete_config(DEFAULT_PE4_DEVICE, chunk),
                },
                {
                    "device_name": DEFAULT_RR_DEVICE,
                    "config_text": render_delete_config(DEFAULT_RR_DEVICE, chunk),
                },
            ],
            "line_timeout_sec": 5,
            "commit_timeout_sec": 180,
        }
        try:
            res = mcp_call("dnos_multi_device_commit", args)
            ok = bool(res.get("ok", False))
            detail = res.get("summary_markdown") or json.dumps(res)[:1000]
        except Exception as exc:  # noqa: BLE001
            ok = False
            detail = f"{type(exc).__name__}: {exc}"
            res = {"error": detail}
        results.append(
            PhaseResult(
                phase=f"cleanup_config_chunk_{chunk_index:02d}",
                ok=ok,
                detail=detail,
                data={"chunk_index": chunk_index, "count": len(chunk), "mcp_result": res},
            )
        )
        if not ok:
            break
    return results


def _extract_command_output(mcp_result: Dict[str, Any]) -> str:
    outputs: List[str] = []
    for rec in mcp_result.get("results") or []:
        if isinstance(rec, dict):
            outputs.append(str(rec.get("output") or rec.get("error") or ""))
    for rec in mcp_result.get("partial_results") or []:
        if isinstance(rec, dict):
            outputs.append(str(rec.get("output") or rec.get("error") or ""))
    return "\n".join(outputs)


def poll_pw_establishment(
    rows: Sequence[ServiceRow],
    *,
    timeout_sec: int = 300,
    interval_sec: int = 10,
    progress: Optional[ProgressCallback] = None,
) -> PhaseResult:
    """Poll until every service has visible VPLS PW state on both DUTs."""

    wanted = {row.name for row in rows}
    deadline = time.time() + timeout_sec
    last_data: Dict[str, Any] = {}
    iteration = 0
    while time.time() < deadline:
        iteration += 1
        pe4 = run_show_commands(DEFAULT_PE4_DEVICE, ["show evpn vpls-pw | no-more"])
        rr = run_show_commands(DEFAULT_RR_DEVICE, ["show evpn vpls-pw | no-more"])
        pe4_out = _extract_command_output(pe4)
        rr_out = _extract_command_output(rr)
        pe4_seen = {name for name in wanted if name in pe4_out}
        rr_seen = {name for name in wanted if name in rr_out}
        pe4_installed = {name for name in pe4_seen if re.search(rf"{re.escape(name)}.*Installed", pe4_out, re.S)}
        rr_installed = {name for name in rr_seen if re.search(rf"{re.escape(name)}.*Installed", rr_out, re.S)}
        last_data = {
            "iteration": iteration,
            "pe4_seen": len(pe4_seen),
            "rr_seen": len(rr_seen),
            "pe4_installed": len(pe4_installed),
            "rr_installed": len(rr_installed),
            "missing_pe4": sorted(wanted - pe4_seen)[:20],
            "missing_rr": sorted(wanted - rr_seen)[:20],
            "missing_installed_pe4": sorted(wanted - pe4_installed)[:20],
            "missing_installed_rr": sorted(wanted - rr_installed)[:20],
        }
        if progress:
            progress("pw_poll", last_data)
        if len(pe4_installed) == len(wanted) and len(rr_installed) == len(wanted):
            return PhaseResult("verify_pw_establishment", True, "all PWs installed", last_data)
        time.sleep(interval_sec)
    return PhaseResult("verify_pw_establishment", False, "PW establishment timeout", last_data)


def _run_spirent(args: Sequence[str], *, timeout: int = 120) -> str:
    cmd = ["python3", str(SPIRENT_TOOL), *args]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"spirent_tool.py {' '.join(args)} failed rc={proc.returncode}: "
            f"{proc.stderr.strip() or proc.stdout.strip()}"
        )
    return proc.stdout.strip()


def create_spirent_streams(
    rows: Sequence[ServiceRow],
    *,
    rate_mbps: int = 1,
    frame_size: int = 128,
    dry_run: bool = False,
    progress: Optional[ProgressCallback] = None,
) -> PhaseResult:
    """Create one L2 StreamBlock per side per service."""

    commands: List[List[str]] = []
    for row in rows:
        commands.append(
            [
                "create-stream",
                "--protocol",
                "l2",
                "--vlan",
                str(row.pe4_outer_vlan),
                "--inner-vlan",
                str(row.inner_vlan),
                "--src-mac",
                row.pe4_src_mac,
                "--dst-mac",
                row.pe4_dst_mac,
                "--rate-mbps",
                str(rate_mbps),
                "--frame-size",
                str(frame_size),
                "--name",
                row.pe4_stream_name,
            ]
        )
        commands.append(
            [
                "create-stream",
                "--protocol",
                "l2",
                "--vlan",
                str(row.rr_spirent_outer_vlan),
                "--inner-vlan",
                str(row.inner_vlan),
                "--src-mac",
                row.rr_src_mac,
                "--dst-mac",
                row.rr_dst_mac,
                "--rate-mbps",
                str(rate_mbps),
                "--frame-size",
                str(frame_size),
                "--name",
                row.rr_stream_name,
            ]
        )

    if dry_run:
        return PhaseResult(
            "spirent_streams_create",
            True,
            f"dry-run generated {len(commands)} stream commands",
            {"commands": commands[:10], "total_commands": len(commands)},
        )

    created: List[str] = []
    total = len(commands)
    for command in commands:
        _run_spirent(command, timeout=60)
        created.append(command[-1])
        if progress and (len(created) == 1 or len(created) % 20 == 0 or len(created) == total):
            progress(
                "stream_create",
                {
                    "created": len(created),
                    "total": total,
                    "last_stream": command[-1],
                },
            )
    return PhaseResult(
        "spirent_streams_create",
        True,
        f"created {len(created)} StreamBlocks",
        {"stream_names": created},
    )


def aggregate_stream_names(rows: Sequence[ServiceRow]) -> List[str]:
    if not rows:
        return []
    first = rows[0].inner_vlan
    last = rows[-1].inner_vlan
    return [
        f"pw_scale_pe4_all_i{first}_{last}",
        f"pw_scale_rr_all_i{first}_{last}",
    ]


def mobility_stream_names(rows: Sequence[ServiceRow]) -> List[str]:
    if not rows:
        return []
    first = rows[0].inner_vlan
    last = rows[-1].inner_vlan
    return [
        f"pw_mob_rr_moves_pe4_i{first}_{last}",
        f"pw_mob_pe4_moves_rr_i{first}_{last}",
    ]


def _indexed_mac(prefix: str, index: int) -> str:
    if index < 1 or index > 4095:
        raise ValueError(f"index out of supported MAC range: {index}")
    return f"{prefix}:{(index >> 8) & 0x0f:02x}:{index & 0xff:02x}".lower()


def _session_stream_names() -> List[str]:
    try:
        data = json.loads(SPIRENT_SESSION_PATH.read_text())
    except Exception:  # noqa: BLE001
        return []
    names: List[str] = []
    for stream in data.get("streams") or []:
        if isinstance(stream, dict) and stream.get("name"):
            names.append(str(stream["name"]))
    return names


def create_spirent_modifier_streams(
    rows: Sequence[ServiceRow],
    *,
    rate_mbps: int = 1,
    frame_size: int = 128,
    dry_run: bool = False,
    progress: Optional[ProgressCallback] = None,
) -> PhaseResult:
    """Create two aggregate L2 StreamBlocks with VLAN/MAC RangeModifiers."""

    if not rows:
        return PhaseResult("spirent_modifier_streams_create", True, "no rows")
    pe4_name, rr_name = aggregate_stream_names(rows)
    count = len(rows)
    commands = [
        [
            "create-modifier-stream",
            "--name",
            pe4_name,
            "--outer-vlan",
            str(rows[0].pe4_outer_vlan),
            "--inner-vlan-start",
            str(rows[0].inner_vlan),
            "--count",
            str(count),
            "--src-mac",
            rows[0].pe4_src_mac,
            "--dst-mac",
            rows[0].pe4_dst_mac,
            "--rate-mbps",
            str(rate_mbps),
            "--frame-size",
            str(frame_size),
        ],
        [
            "create-modifier-stream",
            "--name",
            rr_name,
            "--outer-vlan",
            str(rows[0].rr_spirent_outer_vlan),
            "--inner-vlan-start",
            str(rows[0].inner_vlan),
            "--count",
            str(count),
            "--src-mac",
            rows[0].rr_src_mac,
            "--dst-mac",
            rows[0].rr_dst_mac,
            "--rate-mbps",
            str(rate_mbps),
            "--frame-size",
            str(frame_size),
        ],
    ]
    data = {
        "strategy": "modifier",
        "logical_flows_per_side": count,
        "stream_names": [pe4_name, rr_name],
        "inner_vlan": {"start": rows[0].inner_vlan, "end": rows[-1].inner_vlan, "count": count},
        "pe4": {
            "outer_vlan": rows[0].pe4_outer_vlan,
            "src_mac_start": rows[0].pe4_src_mac,
            "src_mac_end": rows[-1].pe4_src_mac,
            "dst_mac_start": rows[0].pe4_dst_mac,
            "dst_mac_end": rows[-1].pe4_dst_mac,
        },
        "rr_sa_2": {
            "outer_vlan": rows[0].rr_spirent_outer_vlan,
            "src_mac_start": rows[0].rr_src_mac,
            "src_mac_end": rows[-1].rr_src_mac,
            "dst_mac_start": rows[0].rr_dst_mac,
            "dst_mac_end": rows[-1].rr_dst_mac,
        },
    }
    if dry_run:
        data["commands"] = commands
        return PhaseResult(
            "spirent_modifier_streams_create",
            True,
            f"dry-run generated 2 modifier StreamBlocks for {count * 2} logical flows",
            data,
        )

    created: List[str] = []
    for command in commands:
        _run_spirent(command, timeout=60)
        created.append(command[command.index("--name") + 1])
        if progress:
            progress("modifier_stream_create", {"created": len(created), "total": len(commands), "last_stream": created[-1]})
    return PhaseResult(
        "spirent_modifier_streams_create",
        True,
        f"created 2 modifier StreamBlocks for {count * 2} logical flows",
        data,
    )


def create_mass_mobility_modifier_streams(
    rows: Sequence[ServiceRow],
    *,
    rate_mbps: int = 1,
    frame_size: int = 128,
    dry_run: bool = False,
    progress: Optional[ProgressCallback] = None,
) -> PhaseResult:
    """Create reverse-direction streams that move all learned MACs across the PW."""

    if not rows:
        return PhaseResult("mass_mobility_streams_create", True, "no rows")
    rr_moves_pe4, pe4_moves_rr = mobility_stream_names(rows)
    count = len(rows)
    commands = [
        [
            "create-modifier-stream",
            "--name",
            rr_moves_pe4,
            "--outer-vlan",
            str(rows[0].rr_spirent_outer_vlan),
            "--inner-vlan-start",
            str(rows[0].inner_vlan),
            "--count",
            str(count),
            "--src-mac",
            rows[0].pe4_src_mac,
            "--dst-mac",
            _indexed_mac("02:aa:fa:01", rows[0].index),
            "--rate-mbps",
            str(rate_mbps),
            "--frame-size",
            str(frame_size),
        ],
        [
            "create-modifier-stream",
            "--name",
            pe4_moves_rr,
            "--outer-vlan",
            str(rows[0].pe4_outer_vlan),
            "--inner-vlan-start",
            str(rows[0].inner_vlan),
            "--count",
            str(count),
            "--src-mac",
            rows[0].rr_src_mac,
            "--dst-mac",
            _indexed_mac("02:aa:fb:01", rows[0].index),
            "--rate-mbps",
            str(rate_mbps),
            "--frame-size",
            str(frame_size),
        ],
    ]
    data = {
        "strategy": "mass_mobility_modifier",
        "logical_flows_per_side": count,
        "stream_names": [rr_moves_pe4, pe4_moves_rr],
        "inner_vlan": {"start": rows[0].inner_vlan, "end": rows[-1].inner_vlan, "count": count},
        "rr_sa_2_moves_pe4_macs": {
            "outer_vlan": rows[0].rr_spirent_outer_vlan,
            "src_mac_start": rows[0].pe4_src_mac,
            "src_mac_end": rows[-1].pe4_src_mac,
            "dst_mac_start": _indexed_mac("02:aa:fa:01", rows[0].index),
            "dst_mac_end": _indexed_mac("02:aa:fa:01", rows[-1].index),
        },
        "pe4_moves_rr_macs": {
            "outer_vlan": rows[0].pe4_outer_vlan,
            "src_mac_start": rows[0].rr_src_mac,
            "src_mac_end": rows[-1].rr_src_mac,
            "dst_mac_start": _indexed_mac("02:aa:fb:01", rows[0].index),
            "dst_mac_end": _indexed_mac("02:aa:fb:01", rows[-1].index),
        },
    }
    if dry_run:
        data["commands"] = commands
        return PhaseResult(
            "mass_mobility_streams_create",
            True,
            f"dry-run generated 2 reverse modifier StreamBlocks for {count * 2} logical flows",
            data,
        )

    created: List[str] = []
    for command in commands:
        _run_spirent(command, timeout=60)
        created.append(command[command.index("--name") + 1])
        if progress:
            progress(
                "mass_mobility_stream_create",
                {"created": len(created), "total": len(commands), "last_stream": created[-1]},
            )
    return PhaseResult(
        "mass_mobility_streams_create",
        True,
        f"created 2 reverse modifier StreamBlocks for {count * 2} logical flows",
        data,
    )


def activate_modifier_streams(
    rows: Sequence[ServiceRow],
    *,
    dry_run: bool = False,
    progress: Optional[ProgressCallback] = None,
) -> PhaseResult:
    names = aggregate_stream_names(rows)
    if dry_run:
        return PhaseResult("modifier_stream_activation", True, "dry-run", {"stream_names": names})
    set_streams_active(names, active=True)
    _run_spirent(["start"], timeout=30)
    if progress:
        progress("modifier_streams_started", {"stream_count": len(names), "logical_flows_per_side": len(rows)})
    return PhaseResult(
        "modifier_stream_activation",
        True,
        f"started {len(names)} modifier StreamBlocks",
        {"stream_names": names, "logical_flows_per_side": len(rows)},
    )


def activate_mass_mobility_streams(
    rows: Sequence[ServiceRow],
    *,
    dry_run: bool = False,
    progress: Optional[ProgressCallback] = None,
) -> PhaseResult:
    names = mobility_stream_names(rows)
    if dry_run:
        return PhaseResult("mass_mobility_stream_activation", True, "dry-run", {"stream_names": names})
    all_names = sorted(set(_session_stream_names() + aggregate_stream_names(rows) + names))
    set_streams_active(all_names, active=False)
    set_streams_active(names, active=True)
    _run_spirent(["start"], timeout=30)
    if progress:
        progress("mass_mobility_streams_started", {"stream_count": len(names), "logical_flows_per_side": len(rows)})
    return PhaseResult(
        "mass_mobility_stream_activation",
        True,
        f"started {len(names)} reverse modifier StreamBlocks",
        {"stream_names": names, "logical_flows_per_side": len(rows), "deactivated_streams": len(all_names)},
    )


def set_streams_active(names: Sequence[str], *, active: bool) -> None:
    if not names:
        return
    _run_spirent(
        [
            "set-stream-active",
            "--names",
            ",".join(names),
            "--active",
            "true" if active else "false",
        ],
        timeout=60,
    )


def wave_activate_streams(
    rows: Sequence[ServiceRow],
    *,
    wave_size: int = 50,
    wave_spacing_sec: int = 5,
    dry_run: bool = False,
    progress: Optional[ProgressCallback] = None,
) -> PhaseResult:
    stream_names: List[str] = []
    for row in rows:
        stream_names.extend([row.pe4_stream_name, row.rr_stream_name])

    waves = [stream_names[i : i + wave_size] for i in range(0, len(stream_names), wave_size)]
    if dry_run:
        return PhaseResult(
            "wave_activation",
            True,
            f"dry-run generated {len(waves)} activation waves",
            {"waves": [len(w) for w in waves]},
        )

    set_streams_active(stream_names, active=False)
    for wave_index, names in enumerate(waves, start=1):
        if progress:
            progress("wave_start", {"wave_index": wave_index, "wave_total": len(waves), "stream_count": len(names)})
        set_streams_active(names, active=True)
        _run_spirent(["start"], timeout=30)
        if progress:
            progress("wave_done", {"wave_index": wave_index, "wave_total": len(waves), "stream_count": len(names)})
        if wave_index < len(waves):
            time.sleep(wave_spacing_sec)
    return PhaseResult("wave_activation", True, f"activated {len(stream_names)} streams", {"waves": len(waves)})


def _has_flag(output: str, mac: str, expected_flag: str, instance: str) -> bool:
    text = output.lower()
    mac_text = mac.lower()
    flag_text = expected_flag.lower()
    if mac_text not in text:
        return False

    # DNOS prints flags before the MAC in table view, and protocol after the MAC
    # in per-MAC detail view. Accept both forms for source-qualified proof.
    for line in text.splitlines():
        if mac_text in line and flag_text in line:
            return True

    pos = text.find(mac_text)
    window = text[pos : pos + 800]
    if flag_text == "l>":
        return "protocol: local" in window
    if flag_text == "b>":
        return "protocol: bgp" in window
    if flag_text == "v>":
        return "protocol: vpls" in window or "vpls pw" in window
    return instance.lower() in text and flag_text in window


def _has_remote_mac(output: str, mac: str, instance: str) -> bool:
    return _has_flag(output, mac, "v>", instance)


def _batched_mac_outputs(device_name: str, rows: Sequence[ServiceRow]) -> Dict[str, str]:
    """Fetch all per-MAC proofs for one DUT in one persistent MCP session."""

    commands: List[str] = []
    for row in rows:
        commands.extend(
            [
                f"show evpn mac-table instance {row.name} mac {row.pe4_src_mac} | no-more",
                f"show evpn mac-table instance {row.name} mac {row.rr_src_mac} | no-more",
            ]
        )
    result = run_show_commands(device_name, commands)
    outputs: Dict[str, str] = {}
    for rec in result.get("results", []) if isinstance(result, dict) else []:
        if isinstance(rec, dict):
            outputs[str(rec.get("command") or "")] = str(rec.get("output") or rec.get("error") or "")
    return outputs


def verify_mac_learning(
    rows: Sequence[ServiceRow],
    *,
    timeout_sec: int = 300,
    interval_sec: int = 10,
    progress: Optional[ProgressCallback] = None,
) -> PhaseResult:
    """Verify each service has local and remote PW-learned MACs on both DUTs."""

    deadline = time.time() + timeout_sec
    last: Dict[str, Any] = {}
    iteration = 0
    while time.time() < deadline:
        iteration += 1
        failures: List[Dict[str, Any]] = []
        pe4_outputs = _batched_mac_outputs(DEFAULT_PE4_DEVICE, rows)
        rr_outputs = _batched_mac_outputs(DEFAULT_RR_DEVICE, rows)
        for row in rows:
            pe4_local_cmd = f"show evpn mac-table instance {row.name} mac {row.pe4_src_mac} | no-more"
            pe4_remote_cmd = f"show evpn mac-table instance {row.name} mac {row.rr_src_mac} | no-more"
            rr_remote_cmd = f"show evpn mac-table instance {row.name} mac {row.pe4_src_mac} | no-more"
            rr_local_cmd = f"show evpn mac-table instance {row.name} mac {row.rr_src_mac} | no-more"
            checks = {
                "pe4_sees_pe4_local": _has_flag(pe4_outputs.get(pe4_local_cmd, ""), row.pe4_src_mac, "L>", row.name),
                "rr_sees_pe4_remote": _has_remote_mac(rr_outputs.get(rr_remote_cmd, ""), row.pe4_src_mac, row.name),
                "rr_sees_rr_local": _has_flag(rr_outputs.get(rr_local_cmd, ""), row.rr_src_mac, "L>", row.name),
                "pe4_sees_rr_remote": _has_remote_mac(pe4_outputs.get(pe4_remote_cmd, ""), row.rr_src_mac, row.name),
            }
            if not all(checks.values()):
                failures.append({"service": row.name, "inner_vlan": row.inner_vlan, "checks": checks})
        last = {
            "iteration": iteration,
            "total_services": len(rows),
            "passed_services": len(rows) - len(failures),
            "failed_services": len(failures),
            "sample_failures": failures[:20],
        }
        if progress:
            progress("mac_learning_poll", {k: v for k, v in last.items() if k != "sample_failures"})
        if not failures:
            return PhaseResult("verify_mac_learning", True, "all service MACs learned on both sides", last)
        time.sleep(interval_sec)
    return PhaseResult("verify_mac_learning", False, "MAC learning timeout", last)


def verify_mass_mobility(
    rows: Sequence[ServiceRow],
    *,
    timeout_sec: int = 300,
    interval_sec: int = 10,
    progress: Optional[ProgressCallback] = None,
) -> PhaseResult:
    """Verify all existing MACs moved to the opposite DUT through the VPLS PW."""

    deadline = time.time() + timeout_sec
    last: Dict[str, Any] = {}
    iteration = 0
    while time.time() < deadline:
        iteration += 1
        failures: List[Dict[str, Any]] = []
        pe4_outputs = _batched_mac_outputs(DEFAULT_PE4_DEVICE, rows)
        rr_outputs = _batched_mac_outputs(DEFAULT_RR_DEVICE, rows)
        for row in rows:
            pe4_for_pe4_mac = f"show evpn mac-table instance {row.name} mac {row.pe4_src_mac} | no-more"
            pe4_for_rr_mac = f"show evpn mac-table instance {row.name} mac {row.rr_src_mac} | no-more"
            rr_for_pe4_mac = f"show evpn mac-table instance {row.name} mac {row.pe4_src_mac} | no-more"
            rr_for_rr_mac = f"show evpn mac-table instance {row.name} mac {row.rr_src_mac} | no-more"
            checks = {
                "rr_now_owns_pe4_mac_local": _has_flag(rr_outputs.get(rr_for_pe4_mac, ""), row.pe4_src_mac, "L>", row.name),
                "pe4_sees_pe4_mac_remote": _has_remote_mac(pe4_outputs.get(pe4_for_pe4_mac, ""), row.pe4_src_mac, row.name),
                "pe4_now_owns_rr_mac_local": _has_flag(pe4_outputs.get(pe4_for_rr_mac, ""), row.rr_src_mac, "L>", row.name),
                "rr_sees_rr_mac_remote": _has_remote_mac(rr_outputs.get(rr_for_rr_mac, ""), row.rr_src_mac, row.name),
            }
            if not all(checks.values()):
                failures.append({"service": row.name, "inner_vlan": row.inner_vlan, "checks": checks})
        last = {
            "iteration": iteration,
            "total_services": len(rows),
            "moved_services": len(rows) - len(failures),
            "failed_services": len(failures),
            "sample_failures": failures[:20],
        }
        if progress:
            progress("mass_mobility_poll", {k: v for k, v in last.items() if k != "sample_failures"})
        if not failures:
            return PhaseResult("verify_mass_mobility", True, "all service MACs moved to opposite DUT", last)
        time.sleep(interval_sec)
    return PhaseResult("verify_mass_mobility", False, "mass MAC mobility timeout", last)


def collect_spirent_stats() -> Dict[str, Any]:
    raw = _run_spirent(["stats", "--json"], timeout=60)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def write_active_session(
    *,
    test_id: str,
    rows: Sequence[ServiceRow],
    phase: str,
    run_dir: Path,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    payload = {
        "active": True,
        "test_id": test_id,
        "phase": phase,
        "run_dir": str(run_dir),
        "devices": [DEFAULT_PE4_DEVICE, DEFAULT_RR_DEVICE],
        "service_count": len(rows),
        "expected_traffic": build_expected_traffic(rows),
        "service_matrix": [row.to_dict() for row in rows],
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    if extra:
        payload.update(extra)
    ACTIVE_SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_SESSION_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_phase_result(run_dir: Path, result: PhaseResult) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / f"{result.phase}.json"
    path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n")
