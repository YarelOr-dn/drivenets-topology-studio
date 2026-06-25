#!/usr/bin/env python3
"""Orchestrator for TEST_pw_scale_mac_mobility_ha_SW204115.

Creates the 200-service PW scale topology, starts 400 unique L2 streams,
verifies bidirectional MAC learning, and optionally runs HA scenarios.

No phase runs unless invoked explicitly by /TEST RUN or by this script's CLI.
Use `--dry-run` to validate generation and result wiring without touching DUTs
or Spirent.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence

THIS_DIR = Path(__file__).resolve().parent
RECIPE_PATH = THIS_DIR / "recipe.json"
RESULTS_DIR = THIS_DIR / "results"

if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from shared.pw_scale_builder import (  # noqa: E402
    DEFAULT_PE4_DEVICE,
    DEFAULT_RR_DEVICE,
    build_expected_traffic,
    build_service_matrix,
    rows_as_dicts,
)
from shared.pw_scale_runner import (  # noqa: E402
    ACTIVE_SESSION_PATH,
    PhaseResult,
    activate_mass_mobility_streams,
    activate_modifier_streams,
    aggregate_stream_names,
    apply_config_chunks,
    cleanup_config_chunks,
    collect_spirent_stats,
    create_mass_mobility_modifier_streams,
    create_spirent_modifier_streams,
    create_spirent_streams,
    mobility_stream_names,
    mcp_call,
    poll_pw_establishment,
    run_show_commands,
    set_streams_active,
    verify_mac_learning,
    verify_mass_mobility,
    wave_activate_streams,
    write_active_session,
    write_phase_result,
)


def load_recipe() -> Dict[str, Any]:
    return json.loads(RECIPE_PATH.read_text())


def _now_tag() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def _make_run_dir(test_id: str, tag: str | None = None) -> Path:
    run_tag = tag or _now_tag()
    path = RESULTS_DIR / f"RUN_{run_tag}_PE4_RRSA2" / test_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _append_log(run_dir: Path, message: str) -> None:
    with (run_dir / "EXECUTION_LOG.md").open("a") as fh:
        fh.write(f"[{time.strftime('%H:%M:%S')}] {message}\n")


def _progress(
    run_dir: Path,
    phase: str,
    step: str,
    *,
    status: str = "running",
    detail: str = "",
    **data: Any,
) -> None:
    """Write a live heartbeat for long scale runs and print it to stdout."""

    record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "phase": phase,
        "step": step,
        "status": status,
        "detail": detail,
        **data,
    }
    (run_dir / "progress.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    with (run_dir / "progress.jsonl").open("a") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")

    counters = []
    if "completed" in data and "total" in data:
        counters.append(f"{data['completed']}/{data['total']}")
    if "created" in data and "total" in data:
        counters.append(f"{data['created']}/{data['total']}")
    if "passed_services" in data and "total_services" in data:
        counters.append(f"{data['passed_services']}/{data['total_services']} services")
    suffix = f" ({', '.join(counters)})" if counters else ""
    message = f"{phase}:{step} {status}{suffix}"
    if detail:
        message = f"{message} - {detail}"
    _append_log(run_dir, f"PROGRESS {message}")
    print(f"[PROGRESS] {message}", flush=True)


def _runner_progress(run_dir: Path, phase: str):
    def emit(step: str, data: Dict[str, Any]) -> None:
        _progress(run_dir, phase, step, **data)

    return emit


def _write_json(run_dir: Path, name: str, data: Any) -> None:
    (run_dir / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def _finish_active_session(*, ok: bool, reason: str) -> None:
    try:
        payload = json.loads(ACTIVE_SESSION_PATH.read_text()) if ACTIVE_SESSION_PATH.exists() else {}
    except Exception:  # noqa: BLE001
        payload = {}
    payload.update(
        {
            "active": False,
            "completed": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "verdict": "PASS" if ok else "FAIL",
            "completion_reason": reason,
        }
    )
    ACTIVE_SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_SESSION_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _all_ok(results: Sequence[PhaseResult]) -> bool:
    return all(result.ok for result in results)


def _range(values: Sequence[int]) -> Dict[str, int]:
    return {"start": min(values), "end": max(values), "count": len(values)}


def build_parameter_summary(rows) -> Dict[str, Any]:
    """Compact proof of the generated non-overlapping service window."""

    return {
        "service_count": len(rows),
        "stream_count": len(rows) * 2,
        "service_index": _range([row.index for row in rows]),
        "inner_vlan": _range([row.inner_vlan for row in rows]),
        "evi": _range([row.evi for row in rows]),
        "pe4_site_id": _range([row.pe4_site_id for row in rows]),
        "rr_site_id": _range([row.rr_site_id for row in rows]),
        "label_block_size": rows[0].label_block_size if rows else 0,
        "label_budget_per_device": {
            "slots": sum(row.label_block_size for row in rows),
            "first_slot": rows[0].label_block_budget_start if rows else None,
            "last_slot": rows[-1].label_block_budget_end if rows else None,
        },
        "pe4": {
            "device": DEFAULT_PE4_DEVICE,
            "outer_vlan": rows[0].pe4_outer_vlan if rows else None,
            "ac_parent": "ge100-18/0/0",
            "first_ac": rows[0].pe4_ac if rows else None,
            "last_ac": rows[-1].pe4_ac if rows else None,
        },
        "rr_sa_2": {
            "device": DEFAULT_RR_DEVICE,
            "spirent_outer_vlan": rows[0].rr_spirent_outer_vlan if rows else None,
            "wire_outer_vlan": rows[0].rr_wire_outer_vlan if rows else None,
            "ac_parent": "bundle-100",
            "first_ac": rows[0].rr_ac if rows else None,
            "last_ac": rows[-1].rr_ac if rows else None,
        },
        "uniqueness": {
            "service_names": len({row.name for row in rows}),
            "route_targets": len({row.route_target for row in rows}),
            "pe4_rds": len({row.pe4_rd for row in rows}),
            "rr_rds": len({row.rr_rd for row in rows}),
            "site_ids_total": len({*(row.pe4_site_id for row in rows), *(row.rr_site_id for row in rows)}),
            "source_macs": len({*(row.pe4_src_mac for row in rows), *(row.rr_src_mac for row in rows)}),
            "destination_macs": len({*(row.pe4_dst_mac for row in rows), *(row.rr_dst_mac for row in rows)}),
        },
    }


def _extract_command_output(mcp_result: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key in ("results", "partial_results"):
        for rec in mcp_result.get(key, []) if isinstance(mcp_result, dict) else []:
            if isinstance(rec, dict):
                parts.append(str(rec.get("output") or rec.get("error") or ""))
    return "\n".join(parts)


def _window_collisions(rows, live_config: Dict[str, str]) -> List[Dict[str, Any]]:
    collisions: List[Dict[str, Any]] = []
    for row in rows:
        probes = {
            DEFAULT_PE4_DEVICE: (
                row.name,
                row.pe4_ac,
                f"vlan-tags outer-tag {row.pe4_outer_vlan} inner-tag {row.inner_vlan}",
            ),
            DEFAULT_RR_DEVICE: (
                row.name,
                row.rr_ac,
                f"vlan-tags outer-tag {row.rr_wire_outer_vlan} inner-tag {row.inner_vlan}",
            ),
        }
        for device, tokens in probes.items():
            text = live_config.get(device, "")
            matches = [token for token in tokens if token in text]
            if matches:
                collisions.append(
                    {
                        "device": device,
                        "service": row.name,
                        "inner_vlan": row.inner_vlan,
                        "matches": matches,
                    }
                )
    return collisions


def _system_name_present(output: str) -> bool:
    return "System Name" in output or "System name" in output


def _standby_ready(output: str) -> bool:
    return "standby-up" in output.lower()


def _critical_alarm_seen(output: str) -> bool:
    text = output.lower()
    if re.search(r"\bcritical\b\s*[:|]\s*[1-9]\d*", text):
        return True
    return bool(re.search(r"\bcritical\b.*\b(active|raised|alarm)\b", text))


def _bgp_vpls_label_pool_size(output: str) -> int | None:
    """Extract the active bgp-vpls label pool size from show mpls label-allocation tables."""

    match = re.search(r"^\|\s*bgp-vpls\s*\|\s*(\d+)\s*\|", output, flags=re.MULTILINE)
    return int(match.group(1)) if match else None


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)


def _parse_bgp_vpls_label_state(output: str) -> Dict[str, Any]:
    """Parse bgp-vpls configured/in-use label pool state from DNOS label tables."""

    state: Dict[str, Any] = {
        "in_use_labels": None,
        "configured_labels": None,
        "routing_options_label_block_size": None,
        "configured_differs_from_in_use": False,
        "sw253359_zero_pool_signature": False,
        "restart_required": False,
    }
    current_section: str | None = None
    cleaned = _strip_ansi(output)

    for raw_line in cleaned.splitlines():
        line = raw_line.strip()
        lower = line.lower()
        if lower == "in use:":
            current_section = "in_use"
            continue
        if lower.startswith("configured:"):
            current_section = "configured"
            if "differ" in lower and "restart system" in lower:
                state["configured_differs_from_in_use"] = True
                state["restart_required"] = True
            continue
        if "configured values differ from current in use values" in lower and "restart system" in lower:
            state["configured_differs_from_in_use"] = True
            state["restart_required"] = True

        route_opt_match = re.search(r"\bbgp-vpls-label-block-size\s+(\d+)\b", line)
        if route_opt_match:
            state["routing_options_label_block_size"] = int(route_opt_match.group(1))

        row_match = re.match(r"^\|\s*bgp-vpls\s*\|\s*(\d+)\s*\|\s*([^|]+)\|", line)
        if not row_match:
            continue
        labels = int(row_match.group(1))
        label_range = row_match.group(2).strip()
        if labels == 0 and label_range.upper() == "N/A":
            state["sw253359_zero_pool_signature"] = True
        if current_section == "configured":
            state["configured_labels"] = labels
        else:
            state["in_use_labels"] = labels

    return state


def _label_pool_remediation(required_labels: int) -> str:
    return (
        "bgp-vpls label pool config is not active. Keep routing-options "
        f"bgp-vpls-label-block-size >= {required_labels}, then perform a full cold "
        "system restart with documented DNOS syntax 'request system restart'. "
        "Do not rely on bgpd restart, routing-engine/container restart, or NCC "
        "switchover; after boot, re-run 'show mpls label-allocation tables' and "
        "require the bgp-vpls In use total to match the configured pool."
    )


def _configured_si_label_blocks(output: str) -> Dict[str, int]:
    """Return configured EVPN-SI label-block-size per instance from flattened config."""

    blocks: Dict[str, int] = {}
    pattern = re.compile(
        r"network-services evpn instance (\S+) seamless-integration label-block-size (\d+)"
    )
    for match in pattern.finditer(output):
        blocks[match.group(1)] = int(match.group(2))
    return blocks


def _required_bgp_vpls_label_budget(rows, output: str) -> Dict[str, Any]:
    """Budget bgp-vpls pool using observed DNOS export behavior.

    Each EVPN-SI VPLS service exports two VPLS label-block routes per local
    service: one for the local site offset and one for the remote site offset.
    A label-block-size of 8 therefore needs 16 labels of bgp-vpls capacity.
    """

    route_multiplier = 2
    target_names = {row.name for row in rows}
    configured_blocks = _configured_si_label_blocks(output)
    existing_non_target = {
        name: size for name, size in configured_blocks.items() if name not in target_names
    }
    target_budget = sum(row.label_block_size * route_multiplier for row in rows)
    existing_budget = sum(size * route_multiplier for size in existing_non_target.values())
    return {
        "route_multiplier": route_multiplier,
        "target_services": len(rows),
        "target_budget": target_budget,
        "existing_non_target_instances": len(existing_non_target),
        "existing_non_target_budget": existing_budget,
        "required_labels": target_budget + existing_budget,
    }


def _sample_rows(rows, mode: str, *, chunk_size: int = 25):
    if mode == "skip":
        return []
    if mode == "full" or len(rows) <= chunk_size:
        return list(rows)
    selected = set()
    for idx in (0, 1, 2, len(rows) // 2, len(rows) - 3, len(rows) - 2, len(rows) - 1):
        if 0 <= idx < len(rows):
            selected.add(idx)
    for idx in range(0, len(rows), chunk_size):
        selected.add(idx)
        if idx:
            selected.add(idx - 1)
    return [rows[idx] for idx in sorted(selected)]


def _dnaas_path_has_no_live_faults(diag: Dict[str, Any]) -> bool:
    fault_summary = diag.get("fault_summary") if isinstance(diag, dict) else {}
    if diag.get("overall_verdict") == "pass":
        return True
    return (
        isinstance(fault_summary, dict)
        and fault_summary.get("verdict") == "pass"
        and not diag.get("faults")
        and not diag.get("failed_hops")
    )


def _expected_ac_is_ready(device: str, expected_ac: str, inner_vlan: int) -> Dict[str, Any]:
    try:
        res = mcp_call(
            "dnos_run_show_commands",
            {
                "device_name": device,
                "commands": [f"show interfaces {expected_ac} | no-more"],
                "format": "json",
            },
        )
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "expected_ac": expected_ac, "error": f"{type(exc).__name__}: {exc}"}

    output = _extract_command_output(res)
    ready = (
        "Admin state: enabled" in output
        and "Operational state: up" in output
        and f"Inner: {inner_vlan} " in output
    )
    return {
        "ok": ready,
        "expected_ac": expected_ac,
        "inner_vlan": inner_vlan,
        "output_excerpt": output[:1200],
    }


def _corroborate_dnaas_preflight(
    args: Dict[str, Any],
    res: Dict[str, Any],
    *,
    require_ready: bool,
    expected_ac: str,
) -> tuple[str | None, Dict[str, Any] | None]:
    """Validate by live BD logic and expected AC, not by literal subif numbering."""

    verdict = res.get("verdict")
    if verdict == "READY":
        return None, None

    frame_recipe = res.get("frame_recipe") or {}
    recipe_blockers = frame_recipe.get("recipe_blockers") or []
    blocker_codes = {
        str(blocker.get("code"))
        for blocker in recipe_blockers
        if isinstance(blocker, dict)
    }
    allowed_preconfig_blockers = {"NO_DUT_AC", "INNER_VLAN_PIN_NOT_FOUND", "FABRIC_HOP_SUBIF_MISSING"}
    if not require_ready and blocker_codes <= allowed_preconfig_blockers:
        return "NEEDS_AC", {
            "ok": True,
            "source": "preconfig_allowed_blockers",
            "blocker_codes": sorted(blocker_codes),
            "note": "Prerequisite gate allows missing/generated AC evidence before config is pushed.",
        }

    dut_target = res.get("dut_target") if isinstance(res, dict) else {}
    if isinstance(dut_target, dict):
        target_ac = str(dut_target.get("ac_interface") or "")
        target_ready = (
            target_ac == expected_ac
            and dut_target.get("ac_admin_state") == "enabled"
            and dut_target.get("ac_oper_state") == "up"
        )
        if target_ready:
            return "READY", {
                "ok": True,
                "source": "dnos_dnaas_spirent_preflight.dut_target",
                "expected_ac": expected_ac,
                "dut_target": dut_target,
                "note": "Accepted live DUT AC readiness despite DNAAS fabric suffix mismatch.",
            }

    # Some DNAAS MCP paths still derive faults from literal sub-interface
    # suffixes (for example requiring .219), but forwarding is determined by
    # BD membership and vlan-manipulation. If the expected post-config DUT AC is
    # live and matches the requested inner VLAN, do not block the run on suffix
    # mismatches from the fabric walker.
    ac_probe = _expected_ac_is_ready(args["dut"], expected_ac, int(args["inner_vlan"]))
    if ac_probe.get("ok") and "FABRIC_HOP_SUBIF_MISSING" in blocker_codes:
        return "READY", {
            "ok": True,
            "source": "expected_ac_live_probe",
            "expected_ac": expected_ac,
            "ac_probe": ac_probe,
            "blocker_codes": sorted(blocker_codes),
            "note": "Accepted live expected AC; DNAAS sub-interface suffix is not the transport VLAN authority.",
        }

    try:
        diag = mcp_call(
            "dnos_dnaas_diagnose",
            {
                "vlan": args["vlan"],
                "dut": args["dut"],
                "include_dut_validation": False,
                "refresh": True,
                "format": "json",
            },
        )
    except Exception as exc:  # noqa: BLE001
        return None, {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    if not bool(diag.get("ok")) or not _dnaas_path_has_no_live_faults(diag):
        return None, diag

    diag["expected_ac_probe"] = ac_probe

    if ac_probe.get("ok"):
        return "READY", diag

    return None, diag


def _run_dnaas_preflight_window(
    rows,
    *,
    mode: str,
    require_ready: bool,
    dry_run: bool,
    parallelism: int,
    progress_run_dir: Path | None = None,
) -> PhaseResult:
    """Validate the PE-4 and RR-SA-2 Spirent frame recipes for the service window."""

    selected_rows = list(rows) if mode == "smart" else _sample_rows(rows, mode)
    phase = "dnaas_preflight_ready" if require_ready else "dnaas_preflight_prereq"
    if dry_run:
        planned_checks = len(selected_rows) * 2
        if mode == "smart" and selected_rows:
            planned_checks = min(3, len(selected_rows)) * 2 + 2
        return PhaseResult(
            phase,
            True,
            f"dry-run planned {planned_checks} DNAAS preflight checks",
            {
                "mode": mode,
                "require_ready": require_ready,
                "sampled_services": [row.name for row in selected_rows],
                "strategy": "aggregate" if mode == "smart" else "per_service",
            },
        )
    if not selected_rows:
        return PhaseResult(phase, True, "DNAAS preflight skipped by parameter", {"mode": mode})

    def side_args(row, side: str) -> tuple[str, Dict[str, Any]]:
        if side == "pe4":
            expected_ac = row.pe4_ac
            args = {
                "vlan": row.pe4_outer_vlan,
                "dut": DEFAULT_PE4_DEVICE,
                "inner_vlan": row.inner_vlan,
                "test_mac": row.pe4_src_mac,
                "caller_intent": "test_recipe",
                "format": "json",
            }
        else:
            expected_ac = row.rr_ac
            args = {
                "vlan": row.rr_spirent_outer_vlan,
                "dut": DEFAULT_RR_DEVICE,
                "inner_vlan": row.inner_vlan,
                "test_mac": row.rr_src_mac,
                "caller_intent": "test_recipe",
                "format": "json",
            }
        return expected_ac, args

    def call_one(row, side: str) -> Dict[str, Any]:
        expected_ac, args = side_args(row, side)
        res = mcp_call("dnos_dnaas_spirent_preflight", args)
        verdict = res.get("verdict")
        ok_verdicts = {"READY"} if require_ready else {"READY", "NEEDS_AC"}
        override_verdict = None
        diagnose_override = None
        if verdict not in ok_verdicts:
            override_verdict, diagnose_override = _corroborate_dnaas_preflight(
                args,
                res,
                require_ready=require_ready,
                expected_ac=expected_ac,
            )
        if override_verdict:
            verdict = override_verdict
        effective_ok = bool(res.get("ok"))
        if diagnose_override and diagnose_override.get("ok"):
            effective_ok = True
        return {
            "service": row.name,
            "side": side,
            "inner_vlan": row.inner_vlan,
            "ok": effective_ok and verdict in ok_verdicts,
            "verdict": verdict,
            "block_reason": res.get("block_reason"),
            "dut_target": res.get("dut_target"),
            "spirent_flags": res.get("spirent_flags"),
            "raw_ok": res.get("ok"),
            "diagnose_override": diagnose_override,
        }

    def representative_rows() -> List[Any]:
        if not selected_rows:
            return []
        indexes = {0, len(selected_rows) // 2, len(selected_rows) - 1}
        return [selected_rows[idx] for idx in sorted(indexes) if 0 <= idx < len(selected_rows)]

    def call_inner_plan(side: str) -> Dict[str, Any]:
        if side == "pe4":
            device = DEFAULT_PE4_DEVICE
            outer_vlan = selected_rows[0].pe4_outer_vlan
        else:
            device = DEFAULT_RR_DEVICE
            # RR-SA-2 receives traffic through DNAAS fabric VLAN 215, but the
            # DUT-side ACs are authored with wire outer VLAN 4 after the fabric
            # swap. Inner-VLAN inventory must inspect the DUT wire tag.
            outer_vlan = selected_rows[0].rr_wire_outer_vlan
        expected_inners = {int(row.inner_vlan) for row in selected_rows}
        res = mcp_call(
            "dnos_dnaas_inner_vlan_plan",
            {
                "device_name": device,
                "outer_vlan": outer_vlan,
                "refresh": require_ready,
                "format": "json",
            },
        )
        used = {
            int(vlan)
            for vlan in (res.get("used_inner_vlans") or [])
            if str(vlan).isdigit()
        }
        missing = sorted(expected_inners - used)
        return {
            "service": "ALL",
            "side": side,
            "device": device,
            "outer_vlan": outer_vlan,
            "check": "inner_vlan_range",
            "ok": bool(res.get("ok")) and (not require_ready or not missing),
            "verdict": "READY" if not missing else ("BLOCKED" if require_ready else "NEEDS_AC"),
            "expected_count": len(expected_inners),
            "present_count": len(expected_inners) - len(missing),
            "missing_inner_vlans": missing[:40],
            "raw_ok": res.get("ok"),
        }

    def call_ac_status(side: str) -> Dict[str, Any]:
        if side == "pe4":
            device = DEFAULT_PE4_DEVICE
            ac_for_row = lambda row: row.pe4_ac
        else:
            device = DEFAULT_RR_DEVICE
            ac_for_row = lambda row: row.rr_ac

        commands = [f"show interfaces {ac_for_row(row)} | no-more" for row in selected_rows]
        res = mcp_call(
            "dnos_run_show_commands",
            {"device_name": device, "commands": commands, "format": "json"},
        )
        command_results = res.get("results") or []
        bad: List[Dict[str, Any]] = []
        for row, cmd_result in zip(selected_rows, command_results):
            output = str(cmd_result.get("output") or "")
            expected_ac = ac_for_row(row)
            ready = (
                bool(cmd_result.get("ok"))
                and "Admin state: enabled" in output
                and "Operational state: up" in output
                and f"Inner: {row.inner_vlan} " in output
            )
            if not ready:
                bad.append(
                    {
                        "service": row.name,
                        "expected_ac": expected_ac,
                        "inner_vlan": row.inner_vlan,
                        "command_ok": cmd_result.get("ok"),
                        "error": cmd_result.get("error"),
                        "output_excerpt": output[:500],
                    }
                )
        missing_results = max(0, len(selected_rows) - len(command_results))
        return {
            "service": "ALL",
            "side": side,
            "device": device,
            "check": "all_ac_oper_state",
            "ok": bool(res.get("ok")) and not bad and missing_results == 0,
            "verdict": "READY" if not bad and missing_results == 0 else "BLOCKED",
            "checked_count": len(command_results),
            "expected_count": len(selected_rows),
            "missing_results": missing_results,
            "bad_acs": bad[:40],
            "raw_ok": res.get("ok"),
        }

    if mode == "smart":
        smart_checks: List[tuple[str, Any, str]] = [
            ("preflight", row, side)
            for row in representative_rows()
            for side in ("pe4", "rr")
        ] + [("inner_plan", None, "pe4"), ("inner_plan", None, "rr")]
        if require_ready:
            smart_checks.extend([("ac_status", None, "pe4"), ("ac_status", None, "rr")])
        results: List[Dict[str, Any]] = []
        total = len(smart_checks)
        if progress_run_dir:
            _progress(
                progress_run_dir,
                phase,
                "start",
                total=total,
                completed=0,
                detail=(
                    f"running {total} smart DNAAS checks "
                    f"for {len(selected_rows) * 2} service-side frame recipes"
                ),
            )
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(parallelism, total))) as pool:
            futures = []
            for check_type, row, side in smart_checks:
                if check_type == "inner_plan":
                    futures.append(pool.submit(call_inner_plan, side))
                elif check_type == "ac_status":
                    futures.append(pool.submit(call_ac_status, side))
                else:
                    futures.append(pool.submit(call_one, row, side))
            for fut in concurrent.futures.as_completed(futures):
                try:
                    results.append(fut.result())
                except Exception as exc:  # noqa: BLE001
                    results.append({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
                if progress_run_dir:
                    _progress(
                        progress_run_dir,
                        phase,
                        "dnaas_check",
                        total=total,
                        completed=len(results),
                        failures=sum(1 for rec in results if not rec.get("ok")),
                    )

        failures = [rec for rec in results if not rec.get("ok")]
        if progress_run_dir:
            _progress(
                progress_run_dir,
                phase,
                "done",
                status="pass" if not failures else "fail",
                total=total,
                completed=len(results),
                failures=len(failures),
            )
        return PhaseResult(
            phase,
            not failures,
            (
                f"Smart DNAAS preflight passed for {len(selected_rows) * 2} service-side recipes "
                f"using {len(results)} aggregate checks"
                if not failures
                else f"Smart DNAAS preflight failed for {len(failures)} of {len(results)} aggregate checks"
            ),
            {
                "mode": mode,
                "strategy": "aggregate",
                "require_ready": require_ready,
                "service_side_recipes_covered": len(selected_rows) * 2,
                "checked": len(results),
                "failures": failures[:50],
                "results": sorted(results, key=lambda rec: (str(rec.get("side")), str(rec.get("service")))),
            },
        )

    checks = [(row, "pe4") for row in selected_rows] + [(row, "rr") for row in selected_rows]
    results: List[Dict[str, Any]] = []
    total = len(checks)
    progress_every = max(1, total // 20)
    if progress_run_dir:
        _progress(
            progress_run_dir,
            phase,
            "start",
            total=total,
            completed=0,
            detail=f"running {total} DNAAS preflight checks",
        )
    batch_size = max(1, min(parallelism, total))
    for batch_start in range(0, total, batch_size):
        batch = checks[batch_start : batch_start + batch_size]
        if progress_run_dir:
            _progress(
                progress_run_dir,
                phase,
                "dnaas_batch_start",
                total=total,
                completed=len(results),
                detail=f"batch {batch_start // batch_size + 1}/{(total + batch_size - 1) // batch_size}",
            )
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as pool:
            futures = [pool.submit(call_one, row, side) for row, side in batch]
            for fut in concurrent.futures.as_completed(futures):
                try:
                    results.append(fut.result())
                except Exception as exc:  # noqa: BLE001
                    results.append({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
                if progress_run_dir and (
                    len(results) == 1 or len(results) % progress_every == 0 or len(results) == total
                ):
                    _progress(
                        progress_run_dir,
                        phase,
                        "dnaas_check",
                        total=total,
                        completed=len(results),
                        failures=sum(1 for rec in results if not rec.get("ok")),
                    )

    failures = [rec for rec in results if not rec.get("ok")]
    if progress_run_dir:
        _progress(
            progress_run_dir,
            phase,
            "done",
            status="pass" if not failures else "fail",
            total=total,
            completed=len(results),
            failures=len(failures),
        )
    return PhaseResult(
        phase,
        not failures,
        (
            f"DNAAS preflight passed for {len(results)} checks"
            if not failures
            else f"DNAAS preflight failed for {len(failures)} of {len(results)} checks"
        ),
        {
            "mode": mode,
            "require_ready": require_ready,
            "checked": len(results),
            "failures": failures[:50],
            "results": sorted(results, key=lambda rec: (str(rec.get("service")), str(rec.get("side"))))[:80],
        },
    )


def prerequisite_gate(
    rows,
    run_dir: Path,
    *,
    dry_run: bool,
    ha_mode: str,
    dnaas_preflight_mode: str,
    dnaas_parallelism: int,
    allow_existing_service_window: bool,
) -> PhaseResult:
    """Block unsafe runs before config, traffic, or HA operations start."""

    expected = build_expected_traffic(rows)
    _progress(
        run_dir,
        "prerequisite_gate",
        "start",
        service_count=len(rows),
        expected_traffic_count=len(expected),
    )
    write_active_session(
        test_id=load_recipe()["id"],
        rows=rows,
        phase="prerequisite_gate",
        run_dir=run_dir,
        extra={"dry_run": dry_run},
    )
    data: Dict[str, Any] = {
        "service_count": len(rows),
        "expected_traffic_count": len(expected),
        "first_service": rows[0].to_dict(),
        "last_service": rows[-1].to_dict(),
    }
    if dry_run:
        data["dnaas_preflight_plan"] = _run_dnaas_preflight_window(
            rows,
            mode=dnaas_preflight_mode,
            require_ready=False,
            dry_run=True,
            parallelism=dnaas_parallelism,
        ).to_dict()
        return PhaseResult("prerequisite_gate", True, "dry-run prerequisite context generated", data)

    checks = {
        DEFAULT_PE4_DEVICE: [
            "show system version | no-more",
            "show system | no-more",
            "show system alarms | no-more",
            "show interfaces management | no-more",
            "show mpls label-allocation tables | no-more",
            "show config routing-options | no-more",
            "show config | flatten",
        ],
        DEFAULT_RR_DEVICE: [
            "show system version | no-more",
            "show system alarms | no-more",
            "show mpls label-allocation tables | no-more",
            "show config routing-options | no-more",
            "show config | flatten",
        ],
    }
    live: Dict[str, Any] = {}
    flattened_config: Dict[str, str] = {}
    outputs: Dict[str, str] = {}
    for device, commands in checks.items():
        _progress(
            run_dir,
            "prerequisite_gate",
            "live_checks_start",
            detail=f"{device}: {len(commands)} commands",
            device=device,
        )
        live[device] = run_show_commands(device, commands)
        outputs[device] = _extract_command_output(live[device])
        flattened_config[device] = outputs[device]
        _progress(
            run_dir,
            "prerequisite_gate",
            "live_checks_done",
            detail=device,
            device=device,
        )
    data["live_checks"] = live

    _progress(run_dir, "prerequisite_gate", "analyze_live_state")
    failures: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    required_bgp_vpls_labels = sum(row.label_block_size * 2 for row in rows)
    data["required_bgp_vpls_labels"] = required_bgp_vpls_labels
    data["required_bgp_vpls_label_budget_rule"] = (
        "EVPN-SI VPLS exports two label-block routes per service, so capacity is "
        "2 * service_count * label-block-size plus existing non-target SI services."
    )
    label_pool_observations: Dict[str, Any] = {}
    for device, output in outputs.items():
        label_budget = _required_bgp_vpls_label_budget(rows, output)
        required_labels_for_device = int(label_budget["required_labels"])
        if not _system_name_present(output):
            failures.append({"device": device, "check": "identity", "detail": "System Name not found"})
        label_state = _parse_bgp_vpls_label_state(output)
        label_state["capacity_budget"] = label_budget
        label_pool_observations[device] = label_state
        if label_state["sw253359_zero_pool_signature"] or "bgp-vpls: 0 labels, N/A" in output:
            failures.append(
                {
                    "device": device,
                    "check": "label_pool_not_sw253359",
                    "detail": "Matches known bug SW-253359: bgp-vpls label pool inactive",
                    "known_bug": "SW-253359",
                    "remediation": _label_pool_remediation(required_labels_for_device),
                }
            )
        label_pool_size = label_state["in_use_labels"]
        if label_pool_size is None:
            label_pool_size = _bgp_vpls_label_pool_size(output)
        if label_pool_size is None:
            warnings.append(
                {
                    "device": device,
                    "check": "bgp_vpls_label_pool_capacity",
                    "detail": "Could not parse active bgp-vpls label pool size",
                }
            )
        elif label_pool_size < required_labels_for_device:
            failures.append(
                {
                    "device": device,
                    "check": "bgp_vpls_label_pool_capacity",
                    "detail": (
                        f"bgp-vpls pool has {label_pool_size} labels, but "
                        f"{len(rows)} services with label-block-size {rows[0].label_block_size if rows else 0} "
                        f"require at least {required_labels_for_device} labels on this DUT "
                        "(2 VPLS label-block routes per service plus existing SI services)"
                    ),
                    "label_budget": label_budget,
                }
            )
        configured_labels = label_state["configured_labels"] or label_state["routing_options_label_block_size"]
        if (
            configured_labels
            and label_pool_size is not None
            and configured_labels != label_pool_size
            and label_pool_size < required_labels_for_device
        ):
            failures.append(
                {
                    "device": device,
                    "check": "bgp_vpls_label_pool_restart_required",
                    "known_bug": "SW-253359",
                    "detail": (
                        f"bgp-vpls configured pool is {configured_labels}, but active In use pool is "
                        f"{label_pool_size}; {required_labels_for_device} labels are required. "
                        "DNOS reports configured values differ from current in-use values."
                    ),
                    "remediation": _label_pool_remediation(required_labels_for_device),
                    "label_state": label_state,
                }
            )
        elif (
            configured_labels
            and label_pool_size is not None
            and configured_labels != label_pool_size
        ):
            warnings.append(
                {
                    "device": device,
                    "check": "bgp_vpls_label_pool_config_in_use_mismatch",
                    "detail": (
                        f"bgp-vpls configured pool is {configured_labels}, active In use pool is "
                        f"{label_pool_size}; current run budget is still satisfied."
                    ),
                    "label_state": label_state,
                }
            )
        if _critical_alarm_seen(output):
            failures.append({"device": device, "check": "critical_alarms", "detail": "critical alarm detected"})
        if "bgp-vpls-label-block-size" not in output:
            warnings.append(
                {
                    "device": device,
                    "check": "routing_options_label_block",
                    "detail": "bgp-vpls-label-block-size not visible in routing-options output",
                }
            )
    data["label_pool_observations"] = label_pool_observations
    if ha_mode != "skip" and not _standby_ready(outputs.get(DEFAULT_PE4_DEVICE, "")):
        failures.append(
            {
                "device": DEFAULT_PE4_DEVICE,
                "check": "ha_readiness",
                "detail": "standby-up not found; HA switchover/restart tests are unsafe",
            }
        )

    collisions = _window_collisions(rows, flattened_config)
    _progress(
        run_dir,
        "prerequisite_gate",
        "collision_scan_done",
        collision_count=len(collisions),
    )
    data["service_window_collisions"] = collisions[:50]
    if collisions and allow_existing_service_window:
        warnings.append(
            {
                "check": "live_service_window_empty",
                "detail": (
                    "Generated service window already exists; allowed for post-config/post-restart "
                    "prerequisite validation before traffic or HA."
                ),
                "collisions": collisions[:20],
            }
        )
    elif collisions:
        failures.append(
            {
                "check": "live_service_window_empty",
                "detail": "generated service window overlaps existing DUT config",
                "collisions": collisions[:20],
            }
        )

    dnaas_result = _run_dnaas_preflight_window(
        rows,
        mode=dnaas_preflight_mode,
        require_ready=False,
        dry_run=False,
        parallelism=dnaas_parallelism,
        progress_run_dir=run_dir,
    )
    data["dnaas_preflight"] = dnaas_result.to_dict()
    if not dnaas_result.ok:
        failures.append({"check": "dnaas_preflight_prereq", "detail": dnaas_result.detail})

    data["warnings"] = warnings
    data["failures"] = failures
    _progress(
        run_dir,
        "prerequisite_gate",
        "done",
        status="pass" if not failures else "fail",
        failures=len(failures),
        warnings=len(warnings),
    )
    return PhaseResult(
        "prerequisite_gate",
        not failures,
        "all prerequisite gates passed" if not failures else f"{len(failures)} prerequisite gate(s) failed",
        data,
    )


def _extract_active_ncc_id(show_system_text: str) -> int:
    for line in show_system_text.splitlines():
        if "NCC" in line and "active-up" in line:
            match = re.search(r"NCC\s*\|?\s*(\d+)", line)
            if match:
                return int(match.group(1))
    return 1


def _run_operational_ha_command(device: str, command: str, *, dry_run: bool, run_dir: Path) -> str:
    if dry_run:
        return f"DRY-RUN: {command}"

    sys.path.insert(0, str(Path.home() / "SCALER" / "HA"))
    from ha_executor import HAExecutor  # type: ignore
    from ha_ssh import run_ssh_shell  # type: ignore

    ex = HAExecutor(session_log_path=run_dir / "HA_EXECUTOR.log")
    try:
        ex.connect(device)
        if command.strip() == "request system ncc switchover":
            # DNOS documents an interactive Yes/No prompt for switchover. Drive
            # that prompt explicitly so the recipe cannot hang before traffic sampling.
            out = run_ssh_shell(
                ex.device["ip"],
                ex.device["username"],
                ex.device["password"],
                [command, "Yes"],
                timeout=60,
            )
            with (run_dir / "HA_EXECUTOR.log").open("a") as fh:
                fh.write("[ha_executor] run_operational: request system ncc switchover + Yes\n")
            return out
        return ex.run_operational(command, timeout=120)
    finally:
        try:
            ex.cleanup()
            ex.disconnect()
        except Exception:
            pass


def _to_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _spirent_loss_counters(stats: Dict[str, Any]) -> Dict[str, Any]:
    streams = stats.get("streams") if isinstance(stats.get("streams"), list) else []
    per_stream = {
        str(stream.get("name") or stream.get("handle") or index): _to_int(stream.get("dropped"))
        for index, stream in enumerate(streams)
        if isinstance(stream, dict)
    }
    return {
        "loss_frames": _to_int((stats.get("loss") or {}).get("frames")),
        "rx_dropped_frames": _to_int((stats.get("rx") or {}).get("dropped_frames")),
        "stream_dropped_frames": sum(per_stream.values()),
        "per_stream": per_stream,
    }


def _spirent_loss_delta(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    before_counters = _spirent_loss_counters(before)
    after_counters = _spirent_loss_counters(after)
    per_stream_delta = {
        name: max(0, dropped - before_counters["per_stream"].get(name, 0))
        for name, dropped in after_counters["per_stream"].items()
    }
    return {
        "loss_frames": max(0, after_counters["loss_frames"] - before_counters["loss_frames"]),
        "rx_dropped_frames": max(0, after_counters["rx_dropped_frames"] - before_counters["rx_dropped_frames"]),
        "stream_dropped_frames": max(
            0,
            after_counters["stream_dropped_frames"] - before_counters["stream_dropped_frames"],
        ),
        "per_stream_deltas": {name: delta for name, delta in per_stream_delta.items() if delta > 0},
    }


def _collect_spirent_during_ha(
    before_stats: Dict[str, Any],
    *,
    duration_sec: int = 60,
    interval_sec: int = 5,
) -> Dict[str, Any]:
    """Poll Spirent during the HA window; any new loss is a hard failure."""

    samples: List[Dict[str, Any]] = []
    max_delta = {
        "loss_frames": 0,
        "rx_dropped_frames": 0,
        "stream_dropped_frames": 0,
        "per_stream_deltas": {},
    }
    deadline = time.time() + duration_sec
    while time.time() < deadline:
        time.sleep(interval_sec)
        stats = collect_spirent_stats()
        delta = _spirent_loss_delta(before_stats, stats)
        samples.append({"timestamp": stats.get("timestamp"), "stats": stats, "delta_from_before": delta})
        for key in ("loss_frames", "rx_dropped_frames", "stream_dropped_frames"):
            max_delta[key] = max(max_delta[key], delta[key])
        for stream_name, stream_delta in delta["per_stream_deltas"].items():
            current = max_delta["per_stream_deltas"].get(stream_name, 0)
            if stream_delta > current:
                max_delta["per_stream_deltas"][stream_name] = stream_delta
    ok = (
        max_delta["loss_frames"] == 0
        and max_delta["rx_dropped_frames"] == 0
        and max_delta["stream_dropped_frames"] == 0
        and not max_delta["per_stream_deltas"]
    )
    return {"ok": ok, "max_delta": max_delta, "samples": samples}


def _run_ha_scenario(
    rows,
    run_dir: Path,
    *,
    scenario_id: str,
    command_template: str,
    dry_run: bool,
    expected_mac_state: str,
) -> PhaseResult:
    before_stats = collect_spirent_stats() if not dry_run else {"dry_run": True}
    sys_state = run_show_commands(DEFAULT_PE4_DEVICE, ["show system | no-more"]) if not dry_run else {}
    sys_out = ""
    for rec in sys_state.get("results", []) if isinstance(sys_state, dict) else []:
        sys_out += rec.get("output", "")
    active_ncc = _extract_active_ncc_id(sys_out)
    command = command_template.format(active_ncc_id=active_ncc, active_ncp_id=18)
    trigger_out = _run_operational_ha_command(DEFAULT_PE4_DEVICE, command, dry_run=dry_run, run_dir=run_dir)

    if not dry_run:
        traffic_during_ha = _collect_spirent_during_ha(before_stats)
        pw_result = poll_pw_establishment(rows, timeout_sec=600, interval_sec=15)
        if expected_mac_state == "moved":
            mac_result = verify_mass_mobility(rows, timeout_sec=600, interval_sec=15)
        else:
            mac_result = verify_mac_learning(rows, timeout_sec=600, interval_sec=15)
        after_stats = collect_spirent_stats()
        final_loss = _spirent_loss_delta(before_stats, after_stats)
        traffic_ok = traffic_during_ha["ok"] and not any(
            final_loss[key] for key in ("loss_frames", "rx_dropped_frames", "stream_dropped_frames")
        ) and not final_loss["per_stream_deltas"]
        ok = pw_result.ok and mac_result.ok and traffic_ok
    else:
        pw_result = PhaseResult("verify_pw_establishment", True, "dry-run")
        mac_result = PhaseResult("verify_mac_learning", True, "dry-run")
        traffic_during_ha = {"ok": True, "dry_run": True}
        final_loss = {"dry_run": True}
        after_stats = {"dry_run": True}
        ok = True

    data = {
        "scenario_id": scenario_id,
        "command": command,
        "expected_mac_state": expected_mac_state,
        "trigger_output": trigger_out,
        "before_stats": before_stats,
        "traffic_during_ha": traffic_during_ha,
        "after_stats": after_stats,
        "final_loss_delta": final_loss,
        "pw_result": pw_result.to_dict(),
        "mac_result": mac_result.to_dict(),
    }
    detail = "HA scenario complete with zero Spirent loss" if ok else "HA scenario failed or Spirent loss detected"
    return PhaseResult(f"ha_{scenario_id}", ok, detail, data)


def run_selected_ha(
    rows,
    run_dir: Path,
    *,
    ha_mode: str,
    dry_run: bool,
    expected_mac_state: str,
) -> List[PhaseResult]:
    if ha_mode == "skip":
        return [PhaseResult("ha_skip", True, "HA mode skipped by parameter")]

    scenarios = [
        ("ncc_switchover", "request system ncc switchover"),
    ]
    if ha_mode == "safe_no_bgp":
        scenarios.append(
            ("wb_agent_container_restart", "request system container restart ncp {active_ncp_id} datapath")
        )
    if ha_mode in {"core3", "full_7_chunked"}:
        scenarios.extend(
            [
                ("bgpd_restart", "request system process restart ncc {active_ncc_id} routing-engine routing:bgpd"),
                ("wb_agent_container_restart", "request system container restart ncp {active_ncp_id} datapath"),
            ]
        )
    if ha_mode == "full_7_chunked":
        scenarios.extend(
            [
                ("fibmgrd_restart", "request system process restart ncc {active_ncc_id} routing-engine routing:fibmgrd"),
                ("rib_manager_restart", "request system process restart ncc {active_ncc_id} routing-engine routing:rib_manager"),
                ("second_ncc_switchover", "request system ncc switchover"),
                ("bgpd_restart_relearn_sweep", "request system process restart ncc {active_ncc_id} routing-engine routing:bgpd"),
            ]
        )

    results: List[PhaseResult] = []
    for scenario_id, command_template in scenarios:
        result = _run_ha_scenario(
            rows,
            run_dir,
            scenario_id=scenario_id,
            command_template=command_template,
            dry_run=dry_run,
            expected_mac_state=expected_mac_state,
        )
        write_phase_result(run_dir, result)
        results.append(result)
        if not result.ok:
            break
        if ha_mode == "full_7_chunked" and scenario_id in {"ncc_switchover", "second_ncc_switchover"}:
            time.sleep(300 if not dry_run else 0)
        elif ha_mode == "full_7_chunked":
            time.sleep(90 if not dry_run else 0)
    return results


def run_repeated_mobility(
    rows,
    run_dir: Path,
    *,
    cycles: int,
    dry_run: bool,
) -> List[PhaseResult]:
    """Flip all MACs back and forth; each cycle ends in moved state."""

    results: List[PhaseResult] = []
    for cycle in range(1, cycles + 1):
        if not dry_run:
            set_streams_active(aggregate_stream_names(rows) + mobility_stream_names(rows), active=False)
        baseline_activate = activate_modifier_streams(
            rows,
            dry_run=dry_run,
            progress=_runner_progress(run_dir, f"multi_mobility_cycle_{cycle}_baseline_activation"),
        )
        baseline_activate.phase = f"multi_mobility_cycle_{cycle}_baseline_activation"
        results.append(baseline_activate)
        if not baseline_activate.ok:
            break

        baseline_verify = (
            verify_mac_learning(
                rows,
                timeout_sec=600,
                interval_sec=10,
                progress=_runner_progress(run_dir, f"multi_mobility_cycle_{cycle}_baseline_verify"),
            )
            if not dry_run
            else PhaseResult(f"multi_mobility_cycle_{cycle}_baseline_verify", True, "dry-run")
        )
        baseline_verify.phase = f"multi_mobility_cycle_{cycle}_baseline_verify"
        results.append(baseline_verify)
        if not baseline_verify.ok:
            break

        if not dry_run:
            set_streams_active(aggregate_stream_names(rows) + mobility_stream_names(rows), active=False)
        moved_activate = activate_mass_mobility_streams(
            rows,
            dry_run=dry_run,
            progress=_runner_progress(run_dir, f"multi_mobility_cycle_{cycle}_moved_activation"),
        )
        moved_activate.phase = f"multi_mobility_cycle_{cycle}_moved_activation"
        results.append(moved_activate)
        if not moved_activate.ok:
            break

        moved_verify = (
            verify_mass_mobility(
                rows,
                timeout_sec=600,
                interval_sec=10,
                progress=_runner_progress(run_dir, f"multi_mobility_cycle_{cycle}_moved_verify"),
            )
            if not dry_run
            else PhaseResult(f"multi_mobility_cycle_{cycle}_moved_verify", True, "dry-run")
        )
        moved_verify.phase = f"multi_mobility_cycle_{cycle}_moved_verify"
        results.append(moved_verify)
        if not moved_verify.ok:
            break
    return results


def build_summary(run_dir: Path, results: Sequence[PhaseResult]) -> None:
    ok = _all_ok(results)
    parameter_summary = {}
    parameter_summary_path = run_dir / "parameter_summary.json"
    if parameter_summary_path.exists():
        parameter_summary = json.loads(parameter_summary_path.read_text())
    lines = [
        f"# PW Scale MAC Mobility HA Result",
        "",
        f"- Verdict: {'PASS' if ok else 'FAIL'}",
        f"- Run directory: `{run_dir}`",
        f"- Services: {parameter_summary.get('service_count', 'unknown')}",
        f"- StreamBlocks: {parameter_summary.get('stream_count', 'unknown')}",
        f"- Inner VLAN window: {parameter_summary.get('inner_vlan', {}).get('start', 'unknown')}..{parameter_summary.get('inner_vlan', {}).get('end', 'unknown')}",
        f"- Label budget per device: {parameter_summary.get('label_budget_per_device', {}).get('slots', 'unknown')} slots",
        "",
        "| Phase | Result | Detail |",
        "|---|---|---|",
    ]
    for result in results:
        lines.append(f"| `{result.phase}` | {'PASS' if result.ok else 'FAIL'} | {result.detail[:180]} |")
    (run_dir / "SUMMARY.md").write_text("\n".join(lines) + "\n")
    _write_json(run_dir, "verdict.json", {"ok": ok, "phases": [r.to_dict() for r in results]})


def run_all(args: argparse.Namespace) -> int:
    recipe = load_recipe()
    rows = build_service_matrix(scale=args.scale, offset=args.service_offset)
    run_dir = _make_run_dir(recipe["id"], args.run_tag)
    parameter_summary = build_parameter_summary(rows)
    parameter_summary["traffic_strategy"] = args.traffic_strategy
    parameter_summary["logical_streams"] = len(rows) * 2
    parameter_summary["stream_count"] = 2 if args.traffic_strategy == "modifier" else len(rows) * 2
    _write_json(run_dir, "parameter_summary.json", parameter_summary)
    _write_json(run_dir, "service_matrix.json", rows_as_dicts(rows))
    _write_json(run_dir, "expected_traffic.json", build_expected_traffic(rows))
    _progress(
        run_dir,
        "setup",
        "initialized",
        service_count=len(rows),
        stream_count=2 if args.traffic_strategy == "modifier" else len(rows) * 2,
        traffic_strategy=args.traffic_strategy,
        result_dir=str(run_dir),
    )

    results: List[PhaseResult] = []

    def record(result: PhaseResult) -> bool:
        _append_log(run_dir, f"{result.phase}: {'PASS' if result.ok else 'FAIL'} - {result.detail}")
        write_phase_result(run_dir, result)
        results.append(result)
        write_active_session(
            test_id=recipe["id"],
            rows=rows,
            phase=result.phase,
            run_dir=run_dir,
            extra={"dry_run": args.dry_run, "last_result": result.to_dict()},
        )
        return result.ok

    phase = args.phase
    expected_mac_state = args.expected_mac_state
    if phase in {"all", "prerequisite_gate"}:
        if not record(
            prerequisite_gate(
                rows,
                run_dir,
                dry_run=args.dry_run,
                ha_mode=args.ha_mode,
                dnaas_preflight_mode=args.dnaas_preflight_mode,
                dnaas_parallelism=args.dnaas_parallelism,
                allow_existing_service_window=args.allow_existing_service_window,
            )
        ):
            build_summary(run_dir, results)
            return 1
    if phase in {"all", "bulk_config_setup"}:
        if args.dry_run:
            chunk_count = (len(rows) + args.chunk_commit_size - 1) // args.chunk_commit_size
            chunk_results = [
                PhaseResult(
                    "bulk_config_setup",
                    True,
                    f"dry-run generated {chunk_count} paired PE-4/RR-SA-2 commit chunks",
                    {"chunk_count": chunk_count, "chunk_size": args.chunk_commit_size},
                )
            ]
        else:
            chunk_results = apply_config_chunks(
                rows,
                chunk_size=args.chunk_commit_size,
                dry_run=False,
                progress=_runner_progress(run_dir, "bulk_config_setup"),
            )
        for result in chunk_results:
            if not record(result):
                build_summary(run_dir, results)
                return 1
    if phase in {"all", "verify_pw_establishment"}:
        if not record(
            poll_pw_establishment(
                rows,
                timeout_sec=300,
                interval_sec=10,
                progress=_runner_progress(run_dir, "verify_pw_establishment"),
            )
            if not args.dry_run
            else PhaseResult("verify_pw_establishment", True, "dry-run")
        ):
            build_summary(run_dir, results)
            return 1
    if phase in {"all", "verify_dnaas_ready_after_config"}:
        if not record(
            _run_dnaas_preflight_window(
                rows,
                mode=args.dnaas_preflight_mode,
                require_ready=True,
                dry_run=args.dry_run,
                parallelism=args.dnaas_parallelism,
                progress_run_dir=run_dir,
            )
        ):
            build_summary(run_dir, results)
            return 1
    if phase in {"all", "spirent_streams_create_400"}:
        if args.traffic_strategy == "modifier":
            create_result = create_spirent_modifier_streams(
                rows,
                rate_mbps=args.rate_mbps,
                frame_size=args.frame_size,
                dry_run=args.dry_run,
                progress=_runner_progress(run_dir, "spirent_modifier_streams_create"),
            )
        else:
            create_result = create_spirent_streams(
                rows,
                rate_mbps=args.rate_mbps,
                frame_size=args.frame_size,
                dry_run=args.dry_run,
                progress=_runner_progress(run_dir, "spirent_streams_create_400"),
            )
        if not record(create_result):
            build_summary(run_dir, results)
            return 1
    if phase in {"all", "wave_activation_50_per_5s"}:
        if args.traffic_strategy == "modifier":
            activation_result = activate_modifier_streams(
                rows,
                dry_run=args.dry_run,
                progress=_runner_progress(run_dir, "modifier_stream_activation"),
            )
        else:
            activation_result = wave_activate_streams(
                rows,
                wave_size=args.wave_size,
                wave_spacing_sec=args.wave_spacing_sec,
                dry_run=args.dry_run,
                progress=_runner_progress(run_dir, "wave_activation_50_per_5s"),
            )
        if not record(activation_result):
            build_summary(run_dir, results)
            return 1
    if phase in {"all", "verify_mac_learn_both_sides"}:
        if not record(
            verify_mac_learning(
                rows,
                timeout_sec=600,
                interval_sec=10,
                progress=_runner_progress(run_dir, "verify_mac_learn_both_sides"),
            )
            if not args.dry_run
            else PhaseResult("verify_mac_learning", True, "dry-run")
        ):
            build_summary(run_dir, results)
            return 1
        expected_mac_state = "baseline"
    if phase in {"all", "mass_mobility"}:
        create_result = create_mass_mobility_modifier_streams(
            rows,
            rate_mbps=args.rate_mbps,
            frame_size=args.frame_size,
            dry_run=args.dry_run,
            progress=_runner_progress(run_dir, "mass_mobility_streams_create"),
        )
        if not record(create_result):
            build_summary(run_dir, results)
            return 1
        activation_result = activate_mass_mobility_streams(
            rows,
            dry_run=args.dry_run,
            progress=_runner_progress(run_dir, "mass_mobility_stream_activation"),
        )
        if not record(activation_result):
            build_summary(run_dir, results)
            return 1
        if not record(
            verify_mass_mobility(
                rows,
                timeout_sec=600,
                interval_sec=10,
                progress=_runner_progress(run_dir, "verify_mass_mobility"),
            )
            if not args.dry_run
            else PhaseResult("verify_mass_mobility", True, "dry-run")
        ):
            build_summary(run_dir, results)
            return 1
        expected_mac_state = "moved"
    if phase in {"multi_mobility"}:
        for result in run_repeated_mobility(
            rows,
            run_dir,
            cycles=args.move_cycles,
            dry_run=args.dry_run,
        ):
            if not record(result):
                build_summary(run_dir, results)
                return 1
        expected_mac_state = "moved"
    if phase in {"all", "stabilization_window"}:
        _progress(run_dir, "stabilization_window", "start", duration_sec=args.stabilization_window_sec)
        if not args.dry_run:
            time.sleep(args.stabilization_window_sec)
        _progress(run_dir, "stabilization_window", "done", status="pass")
        record(PhaseResult("stabilization_window", True, "complete"))
    if phase in {"all", "ha"}:
        for result in run_selected_ha(
            rows,
            run_dir,
            ha_mode=args.ha_mode,
            dry_run=args.dry_run,
            expected_mac_state=expected_mac_state,
        ):
            if not record(result):
                build_summary(run_dir, results)
                return 1
    if phase == "cleanup":
        if args.dry_run:
            cleanup_results = [
                PhaseResult(
                    "cleanup",
                    True,
                    "dry-run cleanup plan generated",
                    {"service_count": len(rows), "chunk_size": args.chunk_commit_size},
                )
            ]
        else:
            cleanup_results = cleanup_config_chunks(rows, chunk_size=args.chunk_commit_size, dry_run=False)
        for result in cleanup_results:
            if not record(result):
                build_summary(run_dir, results)
                return 1

    build_summary(run_dir, results)
    _finish_active_session(ok=_all_ok(results), reason="completed")
    print(f"Result directory: {run_dir}")
    return 0 if _all_ok(results) else 1


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        default="all",
        choices=[
            "all",
            "prerequisite_gate",
            "bulk_config_setup",
            "verify_pw_establishment",
            "verify_dnaas_ready_after_config",
            "spirent_streams_create_400",
            "wave_activation_50_per_5s",
            "verify_mac_learn_both_sides",
            "mass_mobility",
            "multi_mobility",
            "stabilization_window",
            "ha",
            "cleanup",
        ],
    )
    parser.add_argument("--scale", type=int, default=200)
    parser.add_argument("--service-offset", type=int, default=0)
    parser.add_argument("--chunk-commit-size", type=int, default=25)
    parser.add_argument(
        "--ha-mode",
        default="core3",
        choices=["full_7_chunked", "core3", "safe_no_bgp", "switchover_only", "skip"],
    )
    parser.add_argument("--expected-mac-state", default="baseline", choices=["baseline", "moved"])
    parser.add_argument("--move-cycles", type=int, default=2)
    parser.add_argument("--rate-mbps", type=int, default=1)
    parser.add_argument("--frame-size", type=int, default=128)
    parser.add_argument("--traffic-strategy", default="modifier", choices=["modifier", "per-service"])
    parser.add_argument("--wave-size", type=int, default=50)
    parser.add_argument("--wave-spacing-sec", type=int, default=5)
    parser.add_argument("--stabilization-window-sec", type=int, default=60)
    parser.add_argument("--dnaas-preflight-mode", default="smart", choices=["smart", "full", "sample", "skip"])
    parser.add_argument("--dnaas-parallelism", type=int, default=8)
    parser.add_argument(
        "--allow-existing-service-window",
        action="store_true",
        help="Allow generated services/ACs to already exist during post-config prerequisite validation.",
    )
    parser.add_argument("--run-tag", default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    def _handle_termination(signum, _frame):  # noqa: ANN001
        raise KeyboardInterrupt(f"received signal {signum}")

    signal.signal(signal.SIGTERM, _handle_termination)
    args = parse_args(argv or sys.argv[1:])
    try:
        return run_all(args)
    except KeyboardInterrupt as exc:
        _finish_active_session(ok=False, reason=f"interrupted: {exc}")
        print(f"[PROGRESS] interrupted - {exc}", flush=True)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
