"""Recipe runtime helpers: parameter substitution, phase execution, validation.

Extracted from ``mac_mobility_orchestrator.py``. This module handles the
recipe-side mechanics that the scenario/test runners invoke:

* ``substitute(cmd, params)`` -- simple ``{key}`` token replacement.
* ``_apply_recipe_runtime_parameters`` -- honor each recipe's
  ``runtime_parameters`` block by resolving placeholders from static values,
  live ``show`` output, or declared fallbacks.
* ``_resolve_named_config`` -- look up a named config-template key and return
  its fully-substituted command list.
* ``_run_spirent_phase_actions`` -- dispatch the Spirent action verbs the
  sticky-modes and multihoming recipes declare inside setup/cleanup phases.
* ``_run_recipe_phase`` -- run a single setup/cleanup phase (commands +
  named config + Spirent actions) against the live DUT.
* ``validate_recipe_commands`` / ``live_validate_prerequisites`` /
  ``run_recipe_dry`` -- static + live pre-execution validators.

All public helpers are re-exported from ``mac_mobility_orchestrator`` so
existing call sites keep working unchanged.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from shared.command_guard import known_invalid_reasons, unresolved_tokens
from shared.mac_parsers import strip_ansi
from shared.mac_trigger import (
    plan_mac_move,
    poll_until_mac_present,
    spirent_create_mac_block,
    spirent_inject_evpn_mac_route,
    spirent_inject_evpn_rt1_route,
    spirent_inject_evpn_rt4_route,
    spirent_protocol_start,
    spirent_protocol_stop,
    spirent_remove_device,
)

from .constants import (
    ACTION_TRIGGER_MAP,
    _PW_TRIGGERS,
    _SETUP_SPIRENT_DEFAULT_WAIT_SEC,
    _SETUP_SPIRENT_MAX_WAIT_SEC,
)
from .runtime_context import _discover_spirent_ldp_loopback
from .session_io import (
    _apply_corrections,
    _load_corrections,
    _record_runtime_failure,
    _record_runtime_success,
)


# ---------------------------------------------------------------------------
# Token substitution
# ---------------------------------------------------------------------------

def substitute(cmd: str, params: Dict[str, str]) -> str:
    out = cmd
    for k, v in params.items():
        out = out.replace("{" + k + "}", str(v))
    return out


# ---------------------------------------------------------------------------
# Runtime parameter resolution from recipe.runtime_parameters
# ---------------------------------------------------------------------------

def _apply_recipe_runtime_parameters(
    recipe: Optional[Dict[str, Any]],
    sub_params: Dict[str, str],
    run_show: Callable[[str, str], str],
    device: str,
) -> None:
    """Merge ``recipe['runtime_parameters']`` into ``sub_params``.

    Each entry supports the (live-validated) schema::

        "key": {
            "resolve": "static" | "runtime",
            "value":   "<static value>",
            "from":    "<show command>",      # for resolve=runtime
            "fallback_resolve": "runtime",
            "fallback_from":    "<show command>",
            "notes":   "..."
        }

    Resolution order per key:
      1. If the key already lives in ``sub_params`` (dynamic discovery wins),
         leave it untouched.
      2. If ``resolve == "static"`` and ``value`` is set, use ``value``.
      3. If ``resolve == "runtime"`` and ``from`` is set, run the command and
         capture the first non-empty stripped output line.
      4. If a fallback resolve+from is set, try that.
      5. Else fall back to ``value`` if present.

    This unblocks recipes like ``irb_si_rejection`` (G2) whose snapshot, trigger,
    and verify phases depend on placeholders such as ``{si_instance_name}``.
    """
    if not isinstance(recipe, dict):
        return
    rp = recipe.get("runtime_parameters")
    if not isinstance(rp, dict):
        return

    for key, spec in rp.items():
        if key in sub_params:
            continue
        if not isinstance(spec, dict):
            sub_params[key] = str(spec)
            continue

        resolve = (spec.get("resolve") or "").lower()
        value = spec.get("value")

        if resolve == "static" and value not in (None, ""):
            sub_params[key] = str(value)
            continue
        if resolve == "runtime":
            cmd = spec.get("from") or spec.get("source") or ""
            if cmd:
                try:
                    raw = run_show(device, cmd) or ""
                    text = strip_ansi(raw).strip()
                    first = next(
                        (ln.strip() for ln in text.splitlines() if ln.strip()),
                        "",
                    )
                    if first and "ERROR" not in first.upper():
                        sub_params[key] = first
                        continue
                except Exception:
                    pass

        fb_resolve = (spec.get("fallback_resolve") or "").lower()
        fb_from = spec.get("fallback_from") or ""
        if fb_resolve == "runtime" and fb_from:
            try:
                raw = run_show(device, fb_from) or ""
                text = strip_ansi(raw).strip()
                first = next(
                    (ln.strip() for ln in text.splitlines() if ln.strip()),
                    "",
                )
                if first and "ERROR" not in first.upper():
                    sub_params[key] = first
                    continue
            except Exception:
                pass

        if value not in (None, ""):
            sub_params[key] = str(value)


# ---------------------------------------------------------------------------
# Phase helpers (PR3): support legacy `commands` and the new phases.setup /
# phases.cleanup shapes used by sticky_modes and multihoming recipes.
# ---------------------------------------------------------------------------

def _resolve_named_config(
    recipe: Optional[Dict[str, Any]],
    sub_params: Dict[str, str],
    config_ref: Any,
) -> List[str]:
    """Resolve a named config_commands key into a list of CLI lines.

    Recipes use one of:
      "config": "enable_sticky_interface"
      "config": "enable_sticky_interface on {pw_test_evpn_name}"

    The 'on <evpn>' clause is informational only -- the actual EVPN name is
    already substituted into the named template via the {evpn_name} token in
    the recipe's config_commands map. We strip that suffix so the lookup hits.
    """
    if not isinstance(config_ref, str) or not config_ref.strip():
        return []
    config_map = (recipe or {}).get("config_commands", {}) or {}
    key = config_ref.split(" on ", 1)[0].strip()
    cmds = config_map.get(key)
    if not cmds:
        return []
    return [substitute(c, sub_params) for c in cmds]


def _run_spirent_phase_actions(
    actions: List[Dict[str, Any]],
    params: Dict[str, str],
    sub_params: Dict[str, str],
    obs: Any,
    evpn_name: str,
    phase_label: str,
) -> None:
    """Dispatch a list of recipe spirent action dicts (setup/cleanup phases).

    Supported action keys (from sticky_modes and multihoming recipes):
      create_l2_device, protocol_start, protocol_stop, remove_device, wait,
      inject_rt2, inject_rt4, inject_rt1_per_es, inject_rt1_per_evi,
      withdraw_rt4
    """
    if not actions:
        return
    test_mac = params.get("test_mac", "00:DE:AD:00:01:01")
    last_device_name: Optional[str] = None

    for act in actions:
        if not isinstance(act, dict):
            continue
        action_name = act.get("action", "")
        try:
            if action_name == "create_l2_device":
                vlan_str = substitute(str(act.get("vlan", "0")), sub_params)
                try:
                    vlan = int(vlan_str)
                except ValueError:
                    vlan = 0
                mac = substitute(act.get("mac", test_mac), sub_params)
                dev_name = act.get("device_name") or f"{phase_label}_v{vlan}"
                spirent_create_mac_block(dev_name, vlan, 1, mac)
                last_device_name = dev_name
                obs.record_event(
                    f"{phase_label}_create_l2_device",
                    f"{dev_name} vlan={vlan} mac={mac}",
                )

            elif action_name == "protocol_start":
                target = act.get("device_name") or last_device_name
                spirent_protocol_start(device_name=target)
                obs.record_event(f"{phase_label}_protocol_start", target or "all")

            elif action_name == "protocol_stop":
                target = act.get("device_name") or last_device_name
                spirent_protocol_stop(device_name=target)
                obs.record_event(f"{phase_label}_protocol_stop", target or "all")

            elif action_name == "remove_device":
                target = act.get("device_name") or last_device_name
                if target:
                    spirent_remove_device(target)
                    obs.record_event(f"{phase_label}_remove_device", target)

            elif action_name == "wait":
                seconds = int(act.get("seconds", _SETUP_SPIRENT_DEFAULT_WAIT_SEC))
                seconds = max(0, min(seconds, _SETUP_SPIRENT_MAX_WAIT_SEC))
                if seconds > 0:
                    poll_until_mac_present(
                        test_mac, timeout=float(seconds),
                        fallback_sleep=1.0, evpn_name=evpn_name,
                    )
                obs.record_event(
                    f"{phase_label}_wait",
                    f"{seconds}s mac-poll bounded (target={test_mac})",
                )

            elif action_name == "inject_rt2":
                bgp_dev = (
                    params.get("spirent_evpn_device", "")
                    or params.get("spirent_bgp_device", "")
                )
                if bgp_dev:
                    mac = substitute(act.get("mac", test_mac), sub_params)
                    rt = params.get("rt", "")
                    rd = params.get("rd", "")
                    evi_val = int(params.get("evi", "0") or 0)
                    seq = int(act.get("seq", 0) or 0)
                    sticky = bool(act.get("sticky", False))
                    nh_val = (
                        params.get("spirent_evpn_next_hop", "")
                        or _discover_spirent_ldp_loopback()
                    )
                    spirent_inject_evpn_mac_route(
                        bgp_dev, mac, evi=evi_val, rd=rd, rt=rt,
                        sticky=sticky, seq=seq, next_hop=nh_val,
                    )
                    obs.record_event(
                        f"{phase_label}_inject_rt2",
                        f"{bgp_dev} mac={mac} seq={seq} sticky={sticky}",
                    )

            elif action_name == "inject_rt4":
                bgp_dev = (
                    params.get("spirent_evpn_device", "")
                    or params.get("spirent_bgp_device", "")
                )
                esi = substitute(act.get("esi", ""), sub_params)
                if bgp_dev and esi:
                    spirent_inject_evpn_rt4_route(
                        bgp_dev, esi=esi,
                        originator_ip=act.get("originator_ip", "10.99.99.1"),
                    )
                    obs.record_event(
                        f"{phase_label}_inject_rt4",
                        f"{bgp_dev} esi={esi}",
                    )

            elif action_name in ("inject_rt1_per_es", "inject_rt1_per_evi"):
                bgp_dev = (
                    params.get("spirent_evpn_device", "")
                    or params.get("spirent_bgp_device", "")
                )
                esi = substitute(act.get("esi", ""), sub_params)
                if bgp_dev and esi:
                    evi_str = substitute(str(act.get("evi", "0")), sub_params)
                    try:
                        evi_val = int(evi_str or 0)
                    except ValueError:
                        evi_val = 0
                    sub_type = (
                        "per_es" if action_name == "inject_rt1_per_es" else "per_evi"
                    )
                    spirent_inject_evpn_rt1_route(
                        bgp_dev, esi=esi, evi=evi_val, sub_type=sub_type,
                    )
                    obs.record_event(
                        f"{phase_label}_{action_name}",
                        f"{bgp_dev} esi={esi} evi={evi_val}",
                    )

            elif action_name == "withdraw_rt4":
                bgp_dev = (
                    params.get("spirent_evpn_device", "")
                    or params.get("spirent_bgp_device", "")
                )
                if bgp_dev:
                    spirent_protocol_stop(device_name=bgp_dev)
                    obs.record_event(
                        f"{phase_label}_withdraw_rt4",
                        f"{bgp_dev} (via protocol-stop coarse withdraw)",
                    )

            else:
                obs.record_event(
                    f"{phase_label}_action_skipped",
                    f"Unknown action: {action_name}",
                )
        except Exception as exc:  # noqa: BLE001 -- per-action isolation
            obs.record_event(
                f"{phase_label}_action_error",
                f"{action_name}: {exc}",
            )


def _run_recipe_phase(
    phase_dict: Optional[Dict[str, Any]],
    recipe: Optional[Dict[str, Any]],
    params: Dict[str, str],
    sub_params: Dict[str, str],
    device: str,
    recorded_run_show: Callable[[str, str], str],
    obs: Any,
    evpn_name: str,
    phase_label: str,
) -> None:
    """Run a recipe setup or cleanup phase.

    Supports three coexisting shapes (executed in order):
      1. Legacy: {"commands": [<CLI strings>]}
      2. Named:  {"config": "<named_key_in_recipe.config_commands>"}
      3. Spirent: {"spirent": [<action dict>, ...]}
    """
    if not phase_dict or not isinstance(phase_dict, dict):
        return

    cmds = phase_dict.get("commands", []) or []
    config_ref = phase_dict.get("config")
    spirent_actions = phase_dict.get("spirent", []) or []

    if not (cmds or config_ref or spirent_actions):
        return

    obs.begin_phase(phase_label)
    try:
        for cmd in cmds:
            expanded = substitute(cmd, sub_params)
            corrected = _apply_corrections(expanded)
            try:
                out = recorded_run_show(device, corrected)
                obs.record_event(
                    f"{phase_label}_cmd", corrected,
                    {"output_len": len(out)},
                )
            except Exception as exc:  # noqa: BLE001
                obs.record_event(
                    f"{phase_label}_cmd_error",
                    f"{corrected}: {exc}",
                )

        if config_ref:
            named_cmds = _resolve_named_config(recipe, sub_params, config_ref)
            if not named_cmds:
                obs.record_event(
                    f"{phase_label}_named_config_unresolved",
                    f"No template for: {config_ref}",
                )
            for cmd in named_cmds:
                corrected = _apply_corrections(cmd)
                try:
                    out = recorded_run_show(device, corrected)
                    obs.record_event(
                        f"{phase_label}_named_config", corrected,
                        {"output_len": len(out)},
                    )
                except Exception as exc:  # noqa: BLE001
                    obs.record_event(
                        f"{phase_label}_named_config_error",
                        f"{corrected}: {exc}",
                    )

        if spirent_actions:
            _run_spirent_phase_actions(
                spirent_actions, params, sub_params, obs,
                evpn_name, phase_label,
            )
    finally:
        obs.end_phase()


# ---------------------------------------------------------------------------
# Validation (static + live prerequisite checks, plus dry-run planner)
# ---------------------------------------------------------------------------

def validate_recipe_commands(recipe: Dict[str, Any], params: Dict[str, str]) -> List[Dict[str, str]]:
    """Pre-scan all show/config commands in a recipe against the corrections DB.

    Returns a list of corrections that WILL be applied at runtime, so the user
    can review before executing.  Also flags UNVERIFIED commands.
    """
    corrections_applied: List[Dict[str, str]] = []
    seen: set = set()
    all_cmds: List[str] = []
    validation_params = dict(params)
    for key, spec in (recipe.get("runtime_parameters") or {}).items():
        if key in validation_params:
            continue
        if isinstance(spec, dict) and spec.get("value") not in (None, ""):
            validation_params[key] = str(spec["value"])
        elif not isinstance(spec, dict):
            validation_params[key] = str(spec)
    for cmd_key in recipe.get("show_commands_validated", {}):
        all_cmds.append(substitute(cmd_key, validation_params))
    for sc in recipe.get("scenarios", []):
        sc_params = _scenario_params(sc, validation_params)
        for phase in (sc.get("phases") or {}).values():
            if isinstance(phase, dict):
                for cmd in phase.get("show_commands") or []:
                    all_cmds.append(substitute(cmd, sc_params))
    for prereq in recipe.get("prerequisites", []):
        cc = prereq.get("check_command")
        if cc:
            all_cmds.append(substitute(cc, validation_params))
    for cmd in recipe.get("counter_commands", []):
        cc_str = cmd.get("command", cmd) if isinstance(cmd, dict) else cmd
        all_cmds.append(substitute(cc_str, validation_params))
    for cmd in recipe.get("cleanup_commands", []):
        all_cmds.append(substitute(str(cmd), validation_params))
    for section in (recipe.get("config_baseline") or {}).get("sections", []):
        all_cmds.append(f"show config {substitute(str(section), validation_params)} | no-more")

    for cmd in all_cmds:
        if cmd in seen:
            continue
        seen.add(cmd)
        tokens = unresolved_tokens(cmd)
        invalid = known_invalid_reasons(cmd)
        if tokens or invalid:
            corrections_applied.append({
                "original": cmd,
                "corrected": "[COMMAND-GUARD] blocked before DUT",
                "validation_method": "static_command_guard",
                "concern": "; ".join(
                    ([f"unresolved placeholders: {', '.join(tokens)}"] if tokens else [])
                    + invalid
                ),
            })
            continue
        corrected = _apply_corrections(cmd)
        if corrected != cmd:
            corrections_applied.append({"original": cmd, "corrected": corrected})

    corrections = _load_corrections()
    unverified = corrections.get("unverified_syntax", [])
    for u in unverified:
        corrections_applied.append({
            "original": u.get("command", ""),
            "corrected": f"[UNVERIFIED] {u.get('concern', '')}",
            "validation_method": u.get("validation_method", ""),
        })
    return corrections_applied


def live_validate_prerequisites(
    device: str,
    recipe: Dict[str, Any],
    params: Dict[str, str],
    run_show: Callable[[str, str], str],
) -> List[Dict[str, str]]:
    """Run every prerequisite check_command on the live device BEFORE execution.

    For each prerequisite:
      - If marked "validated": false, the command has NEVER been verified on a device.
      - Run it; if DNOS rejects it (ERROR/Unknown word), record the failure and
        try alt_check if available.
      - Return a list of validation results the user can review.

    This prevents the orchestrator from treating unvalidated output as truth.
    """
    results: List[Dict[str, str]] = []
    for prereq in recipe.get("prerequisites", []):
        check_cmd = prereq.get("check_command")
        if not check_cmd:
            continue
        check_cmd = substitute(check_cmd, params)
        if "{" in check_cmd:
            results.append({
                "prereq_id": prereq.get("id", "?"),
                "command": check_cmd,
                "status": "FAILED",
                "error": "unresolved recipe placeholder before live validation",
            })
            continue
        if not check_cmd.startswith("show"):
            results.append({
                "prereq_id": prereq.get("id", "?"),
                "command": check_cmd,
                "status": "SKIPPED",
                "note": "Not a device show command",
            })
            continue
        is_unvalidated = prereq.get("validated") is False
        entry: Dict[str, str] = {
            "prereq_id": prereq.get("id", "?"),
            "command": check_cmd,
            "was_unvalidated": str(is_unvalidated),
        }

        output = run_show(device, check_cmd)
        if "ERROR: Unknown word" in output or "Incomplete command" in output:
            entry["status"] = "FAILED"
            entry["error"] = output.strip()[:200]
            _record_runtime_failure(check_cmd, output)

            alt_cmd = prereq.get("alt_check")
            if alt_cmd:
                alt_cmd = substitute(alt_cmd, params)
                alt_output = run_show(device, alt_cmd)
                if "ERROR" not in alt_output and "Unknown word" not in alt_output:
                    entry["status"] = "FAILED_PRIMARY_ALT_OK"
                    entry["alt_command"] = alt_cmd
                    entry["alt_output_preview"] = alt_output.strip()[:200]
                    _record_runtime_success(alt_cmd)
                else:
                    entry["alt_status"] = "ALSO_FAILED"
                    entry["alt_error"] = alt_output.strip()[:200]
        else:
            entry["status"] = "VALID"
            entry["output_preview"] = output.strip()[:200]
            _record_runtime_success(check_cmd)

        results.append(entry)
    return results


def run_recipe_dry(
    device: str,
    recipe: Dict[str, Any],
    params: Dict[str, str],
) -> Dict[str, Any]:
    out: Dict[str, Any] = {"id": recipe.get("id"), "scenarios": []}
    for sc in recipe.get("scenarios", []):
        entry: Dict[str, Any] = {"id": sc.get("id"), "expanded_commands": [], "trigger_plan": None}
        sc_params = _scenario_params(sc, params)
        phases = sc.get("phases") or {}
        for phase_name, phase in phases.items():
            if not isinstance(phase, dict):
                continue
            for cmd in phase.get("show_commands") or []:
                entry["expanded_commands"].append(
                    {"phase": phase_name, "cmd": substitute(cmd, sc_params)}
                )
            ha_cmd = phase.get("ha_command")
            if ha_cmd:
                entry["expanded_commands"].append(
                    {"phase": phase_name, "cmd": substitute(ha_cmd, params), "type": "ha_trigger"}
                )
            action = phase.get("action")
            if action:
                mapped = ACTION_TRIGGER_MAP.get(action, "unknown")
                entry["trigger_plan"] = plan_mac_move(sc.get("id", ""), action, mapped)
        out["scenarios"].append(entry)
    return out


def _scenario_params(sc: Dict[str, Any], params: Dict[str, str]) -> Dict[str, str]:
    """Return token params adjusted for the scenario's active EVPN instance."""
    sc_params = dict(params)
    trigger = (sc.get("phases") or {}).get("trigger") or {}
    action = trigger.get("action", "") if isinstance(trigger, dict) else ""
    mapped = ACTION_TRIGGER_MAP.get(action, "unknown")
    if mapped in _PW_TRIGGERS and params.get("pw_evpn_name"):
        sc_params["evpn_name"] = params["pw_evpn_name"]
    sc_params["scenario_evpn_name"] = sc_params.get("evpn_name", params.get("evpn_name", ""))
    if sc.get("test_mac_override"):
        sc_params["test_mac"] = str(sc["test_mac_override"])
    return sc_params


__all__ = [
    "substitute",
    "_apply_recipe_runtime_parameters",
    "_resolve_named_config",
    "_run_spirent_phase_actions",
    "_run_recipe_phase",
    "validate_recipe_commands",
    "live_validate_prerequisites",
    "run_recipe_dry",
]
