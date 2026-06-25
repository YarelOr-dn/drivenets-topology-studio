#!/usr/bin/env python3
"""Recipe linter for the EVPN MAC Mobility test suite (SW-204115).

Validates every ``tests/<group>/recipe.json`` file against:

  * Required top-level keys (id, name, jira_key, scenarios, runtime_parameters).
  * Each scenario has ``id`` + ``phases`` and at least one of:
    snapshot / before_snapshot / setup / trigger / verify / cleanup.
  * Every ``phases.trigger.action`` (when present) is recognised by the
    orchestrator's ``ACTION_TRIGGER_MAP`` (or the explicit ``noop`` fallback).
  * Every ``infra_required`` value (recipe-level + scenario-level) exists in
    ``suite_manifest.json -> infrastructure_modes`` AND is not deprecated.
  * No reference to the dropped ``non_si_mode`` mode.
  * Each test in ``suite_manifest.json -> tests`` resolves to an existing
    recipe file; orphan recipes (recipes not listed in either ``tests`` or
    ``experimental_tests``) are reported as warnings.

Recipes flagged as ``"status": "experimental"`` are linted with relaxed
``trigger.action`` validation: unknown actions become warnings instead of
errors, since by definition their orchestrator handlers are not yet wired.
All other rules (JSON validity, jira_key presence, infra mode validity)
still apply -- experimental recipes must stay schema-clean so they can be
promoted to the main ``tests`` array as soon as their blockers clear.

Exit code: 0 if clean, 1 if any errors. Warnings do NOT fail the run by
default (use ``--strict`` to promote warnings to errors).

Usage:

  python3 tools/lint_recipes.py
  python3 tools/lint_recipes.py --strict
  python3 tools/lint_recipes.py --json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

SUITE_ROOT = Path(__file__).resolve().parent.parent
SUITE_MANIFEST = SUITE_ROOT / "suite_manifest.json"
INFRA_MODES_FILE = SUITE_ROOT / "shared" / "infrastructure_modes.json"
ORCHESTRATOR = SUITE_ROOT / "mac_mobility_orchestrator.py"
ORCHESTRATION_CONSTANTS = SUITE_ROOT / "orchestration" / "constants.py"
TESTS_DIR = SUITE_ROOT / "tests"

# Modes deprecated and removed in PR5 (2026-04-14). Any recipe still
# referencing them is a hard error.
DEPRECATED_MODES = {"non_si_mode"}

# Triggers that ACTION_TRIGGER_MAP doesn't contain but the trigger executor
# still handles via the SPIRENT-runner fallback branch (`_SPIRENT_PHASE_TRIGGER_VERBS`).
# Keep this set in sync with that orchestrator constant. Anything not in
# ACTION_TRIGGER_MAP and not in this set is a lint error.
ALLOWED_NOOP_ACTIONS = {
    "noop",                # explicit observation-only marker
    "withdraw_rt4",        # multihoming SC02 -- routed via _run_spirent_phase_actions
    "inject_rt4",          # multihoming setup / trigger
    "inject_rt2",          # multihoming/spirent setup / trigger
    "inject_rt1_per_es",   # multihoming setup
    "inject_rt1_per_evi",  # multihoming setup
    "create_l2_device",    # sticky_modes setup
    "protocol_start",      # sticky_modes setup
    "protocol_stop",       # sticky_modes cleanup
    "remove_device",       # sticky_modes cleanup
    "wait",                # generic step delay
}


def _extract_action_trigger_keys(source: str) -> Set[str]:
    """Pull keys from a literal ACTION_TRIGGER_MAP dict in the given source."""
    m = re.search(r"ACTION_TRIGGER_MAP\s*:\s*Dict\[[^\]]+\]\s*=\s*\{(.*?)\n\}", source, flags=re.S)
    if not m:
        m = re.search(r"ACTION_TRIGGER_MAP\s*=\s*\{(.*?)\n\}", source, flags=re.S)
    if not m:
        return set()
    body = m.group(1)
    return set(re.findall(r'"([A-Za-z0-9_]+)"\s*:', body))


def _load_action_trigger_map() -> Set[str]:
    """Load ACTION_TRIGGER_MAP keys without importing the whole orchestrator.

    Looks first at orchestration/constants.py (the canonical home after the
    2026-04 split), then falls back to the legacy mac_mobility_orchestrator.py
    location. Both code paths source-parse the dict literal so we never
    execute heavy imports.
    """
    keys: Set[str] = set()
    if ORCHESTRATION_CONSTANTS.exists():
        keys |= _extract_action_trigger_keys(
            ORCHESTRATION_CONSTANTS.read_text(encoding="utf-8")
        )
    if ORCHESTRATOR.exists():
        keys |= _extract_action_trigger_keys(
            ORCHESTRATOR.read_text(encoding="utf-8")
        )
    return keys


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        print(f"[FATAL] {path}: invalid JSON -- {exc}", file=sys.stderr)
        sys.exit(2)


class LintReport:
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def err(self, where: str, msg: str) -> None:
        self.errors.append(f"[ERROR] {where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"[WARN]  {where}: {msg}")

    def note(self, where: str, msg: str) -> None:
        self.info.append(f"[INFO]  {where}: {msg}")

    def render(self, json_mode: bool = False) -> str:
        if json_mode:
            return json.dumps({
                "errors": self.errors,
                "warnings": self.warnings,
                "info": self.info,
            }, indent=2)
        out = []
        out.extend(self.info)
        out.extend(self.warnings)
        out.extend(self.errors)
        out.append(
            f"Summary: {len(self.errors)} error(s), "
            f"{len(self.warnings)} warning(s), {len(self.info)} info."
        )
        return "\n".join(out)


# Inner-command surface keys recognised by shared.inner_command_runner_glue.
# When present in a phase, the scenario runner attempts to drive the matching
# nested DNOS shell. Currently only the verify phase consumes them, but the
# linter accepts them in any phase to make future migrations cheap.
_INNER_LIST_KEYS = {"vtysh_commands", "ncc_shell_commands"}
_INNER_NCP_BLOCK_KEYS = {"ncp_shell_commands", "xraycli"}
_INNER_TRACE_KEY = "trace_views"
_TRACE_VIEW_REQUIRED = ("file", "match")
_TRACE_VIEW_OPTIONAL = {"context_before", "context_after",
                        "max_lines", "ncp_id"}


def _validate_inner_blocks(
    phase: Dict[str, Any],
    sc_ph: str,
    report: LintReport,
    *,
    is_verify: bool,
) -> None:
    """Validate the optional inner-command keys on a single phase dict."""
    # Plain string-list keys ----------------------------------------------
    for key in _INNER_LIST_KEYS:
        val = phase.get(key)
        if val is None:
            continue
        if not is_verify:
            report.warn(sc_ph, f"'{key}' in non-verify phase -- orchestrator "
                               f"only executes inner commands during verify")
        if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
            report.err(sc_ph, f"'{key}' must be a list of strings")
            continue
        if not val:
            report.warn(sc_ph, f"'{key}' is an empty list -- remove it or fill")

    # NCP-keyed list blocks ('ncp_shell_commands' / 'xraycli') ------------
    for key in _INNER_NCP_BLOCK_KEYS:
        val = phase.get(key)
        if val is None:
            continue
        if not is_verify:
            report.warn(sc_ph, f"'{key}' in non-verify phase -- orchestrator "
                               f"only executes inner commands during verify")
        if not isinstance(val, list) or not val:
            report.err(sc_ph, f"'{key}' must be a non-empty list")
            continue
        # Two accepted shapes: flat list of strings, or list of dicts with
        # ncp_id + (commands|topics).
        first = val[0]
        if isinstance(first, str):
            if not all(isinstance(x, str) for x in val):
                report.err(sc_ph, f"'{key}' flat list must contain only strings")
            continue
        list_inner = "topics" if key == "xraycli" else "commands"
        for idx, entry in enumerate(val):
            if not isinstance(entry, dict):
                report.err(sc_ph, f"'{key}'[{idx}] must be an object or string")
                continue
            cmds = entry.get(list_inner) or entry.get("commands")
            if not isinstance(cmds, list) or not cmds \
                    or not all(isinstance(x, str) for x in cmds):
                report.err(sc_ph,
                           f"'{key}'[{idx}] must declare '{list_inner}' as a "
                           f"non-empty list of strings")
            ncp = entry.get("ncp_id", 0)
            try:
                int(ncp)
            except (TypeError, ValueError):
                report.err(sc_ph,
                           f"'{key}'[{idx}].ncp_id must be an integer (got {ncp!r})")

    # trace_views ---------------------------------------------------------
    views = phase.get(_INNER_TRACE_KEY)
    if views is None:
        return
    if not is_verify:
        report.warn(sc_ph, f"'{_INNER_TRACE_KEY}' in non-verify phase -- "
                           f"orchestrator only executes inner commands during verify")
    if not isinstance(views, list) or not views:
        report.err(sc_ph, f"'{_INNER_TRACE_KEY}' must be a non-empty list")
        return
    for idx, view in enumerate(views):
        if not isinstance(view, dict):
            report.err(sc_ph, f"'{_INNER_TRACE_KEY}'[{idx}] must be an object")
            continue
        for req in _TRACE_VIEW_REQUIRED:
            if not isinstance(view.get(req), str) or not view[req]:
                report.err(sc_ph,
                           f"'{_INNER_TRACE_KEY}'[{idx}] missing required "
                           f"string field '{req}'")
        for opt_int in ("context_before", "context_after", "max_lines"):
            v = view.get(opt_int)
            if v is None:
                continue
            try:
                if int(v) < 0:
                    raise ValueError
            except (TypeError, ValueError):
                report.err(sc_ph,
                           f"'{_INNER_TRACE_KEY}'[{idx}].{opt_int} must be a "
                           f"non-negative integer (got {v!r})")
        ncp = view.get("ncp_id")
        if ncp not in (None, ""):
            try:
                int(ncp)
            except (TypeError, ValueError):
                report.err(sc_ph,
                           f"'{_INNER_TRACE_KEY}'[{idx}].ncp_id must be an "
                           f"integer or null (got {ncp!r})")
        unknown = set(view.keys()) - set(_TRACE_VIEW_REQUIRED) - _TRACE_VIEW_OPTIONAL
        if unknown:
            report.warn(sc_ph,
                        f"'{_INNER_TRACE_KEY}'[{idx}] has unknown key(s): "
                        f"{sorted(unknown)} -- runner will ignore")


def _validate_recipe(
    path: Path,
    recipe: Dict[str, Any],
    action_map_keys: Set[str],
    valid_modes: Set[str],
    report: LintReport,
) -> None:
    rel = path.relative_to(SUITE_ROOT)
    where = str(rel)

    is_experimental = (recipe.get("status") == "experimental")
    if is_experimental:
        report.note(where, "recipe is marked status=experimental -- trigger.action validation relaxed")

    required_top = ("id", "name", "jira_key", "scenarios", "runtime_parameters")
    for key in required_top:
        if key not in recipe:
            report.err(where, f"missing required top-level key '{key}'")

    infra_recipe = recipe.get("infra_required")
    if infra_recipe and infra_recipe not in {"mixed", *valid_modes}:
        if infra_recipe in DEPRECATED_MODES:
            report.err(where, f"recipe-level infra_required='{infra_recipe}' is DEPRECATED -- update to a current mode")
        else:
            report.err(where, f"recipe-level infra_required='{infra_recipe}' is not in suite_manifest.infrastructure_modes ({sorted(valid_modes)})")

    scenarios = recipe.get("scenarios", [])
    if not isinstance(scenarios, list) or not scenarios:
        report.err(where, "scenarios[] must be a non-empty list")
        return

    sc_ids: Set[str] = set()
    for idx, sc in enumerate(scenarios):
        if not isinstance(sc, dict):
            report.err(where, f"scenarios[{idx}] is not an object")
            continue
        sc_id = sc.get("id") or f"<idx={idx}>"
        sc_where = f"{where}::{sc_id}"
        if not sc.get("id"):
            report.err(sc_where, "scenario missing 'id'")
        elif sc_id in sc_ids:
            report.err(sc_where, "duplicate scenario id")
        else:
            sc_ids.add(sc_id)

        if not sc.get("name"):
            report.warn(sc_where, "scenario missing 'name'")

        infra_sc = sc.get("infra_required")
        if infra_sc and infra_sc not in valid_modes:
            if infra_sc in DEPRECATED_MODES:
                report.err(sc_where, f"scenario infra_required='{infra_sc}' is DEPRECATED")
            else:
                report.err(sc_where, f"scenario infra_required='{infra_sc}' not in {sorted(valid_modes)}")

        phases = sc.get("phases")
        if not isinstance(phases, dict):
            report.err(sc_where, "phases must be an object")
            continue

        recognised_phases = {
            "setup", "setup_trigger", "snapshot", "before_snapshot",
            "trigger", "poll_convergence", "verify", "after_snapshot",
            "cleanup", "poll_recovery", "event_expectations",
        }
        unknown_phases = set(phases.keys()) - recognised_phases
        if unknown_phases:
            report.warn(sc_where, f"unknown phase keys (orchestrator will ignore): {sorted(unknown_phases)}")

        if not (phases.get("trigger") or phases.get("verify") or phases.get("setup")):
            report.warn(sc_where, "scenario has no setup/trigger/verify -- the orchestrator will SKIP it")

        trigger = phases.get("trigger")
        if isinstance(trigger, dict):
            action = trigger.get("action")
            ha_command = trigger.get("ha_command")
            cli_cmd = trigger.get("command")
            has_steps = any(k.startswith("step") for k in trigger.keys())

            if not (action or ha_command or cli_cmd or has_steps):
                report.err(sc_where, "trigger has no 'action', 'ha_command', 'command', or 'stepN' field")

            # The orchestrator dispatches on 'action' only. A trigger with only
            # stepN keys but no top-level action will be classified as Unknown
            # and SKIP'd. Recipes must promote the multi-step intent to an
            # explicit action so the orchestrator can pick the right handler.
            if has_steps and not action and not ha_command:
                if is_experimental:
                    report.warn(
                        sc_where,
                        "trigger has stepN keys but no top-level 'action' "
                        "(experimental recipe -- promote to 'action' before moving to tests[]).",
                    )
                else:
                    report.err(
                        sc_where,
                        "trigger has stepN keys but no top-level 'action' -- orchestrator only "
                        "dispatches on 'action'. Add an explicit action that maps to a multi-step "
                        "handler (e.g. 'learn_on_pw_then_configure_sticky' -> spirent_pw_then_ac).",
                    )

            if action and action not in action_map_keys and action not in ALLOWED_NOOP_ACTIONS:
                msg = (
                    f"trigger.action='{action}' is not in ACTION_TRIGGER_MAP and not in ALLOWED_NOOP_ACTIONS -- "
                    f"orchestrator will mark trigger as UNKNOWN (SKIP)"
                )
                if is_experimental:
                    report.warn(sc_where, msg + " [experimental: tracked in suite_manifest.experimental_tests blockers]")
                else:
                    report.err(sc_where, msg)

    # Check show commands referenced for known invalid forms.
    invalid_cmds = recipe.get("invalid_commands", {}) or {}
    for sc in scenarios:
        if not isinstance(sc, dict):
            continue
        phases = sc.get("phases", {}) or {}
        for ph_name in ("snapshot", "before_snapshot", "verify", "after_snapshot"):
            ph = phases.get(ph_name)
            if not isinstance(ph, dict):
                continue
            for cmd in ph.get("show_commands", []) or []:
                bare = cmd.strip()
                for bad_prefix in invalid_cmds.keys():
                    if bare.startswith(bad_prefix):
                        report.err(
                            f"{where}::{sc.get('id', '?')}::{ph_name}",
                            f"uses INVALID command '{bad_prefix}' -- {invalid_cmds[bad_prefix]}",
                        )

        # ----------------------------------------------------------------
        # Inner-command surfaces (shared.inner_command_runner_glue). All
        # are optional and only meaningful inside a verify-phase block,
        # but we tolerate them in any phase the orchestrator inspects so
        # future migrations of trace_views into snapshot/before_snapshot
        # remain valid.
        # ----------------------------------------------------------------
        for ph_name in ("setup", "before_snapshot", "snapshot",
                        "trigger", "verify", "after_snapshot", "cleanup"):
            ph = phases.get(ph_name)
            if not isinstance(ph, dict):
                continue
            sc_ph = f"{where}::{sc.get('id', '?')}::{ph_name}"
            _validate_inner_blocks(ph, sc_ph, report,
                                   is_verify=(ph_name == "verify"))

    # ----------------------------------------------------------------------
    # Frame-recipe consistency lint
    # ----------------------------------------------------------------------
    # Recipes that declare a `mcp_dnaas_teach_plan` prerequisite MUST consume
    # the resulting frame_recipe via active_test_session.expected_traffic.
    # Any phase that hard-codes spirent_args.outer_vlan / spirent_args.vlan
    # to a literal integer bypasses the override mechanism in
    # spirent_create_l2_stream and risks injecting wrong-encapsulation frames.
    # See shared/frame_recipe_consumer.py and the 2026-05-01 SC02 incident.
    try:
        # frame_recipe_consumer is in shared/, which is on sys.path when the
        # linter is invoked from the suite root. Tolerate the import failing
        # (e.g. running from a different worktree); skip the lint silently
        # rather than blocking unrelated lint runs.
        if str(SUITE_ROOT) not in sys.path:
            sys.path.insert(0, str(SUITE_ROOT))
        from shared.frame_recipe_consumer import iter_frame_recipe_violations
        for msg in iter_frame_recipe_violations(recipe):
            report.err(where, f"frame_recipe lint: {msg}")
    except Exception as exc:
        report.note(where, f"frame_recipe lint skipped ({type(exc).__name__}: {exc})")


def _validate_manifest(
    manifest: Dict[str, Any],
    valid_modes: Set[str],
    report: LintReport,
) -> Tuple[Dict[str, Path], Dict[str, Path]]:
    """Returns (production_recipes, experimental_recipes) mapping test_id -> Path."""
    where = "suite_manifest.json"
    production: Dict[str, Path] = {}
    experimental: Dict[str, Path] = {}

    if not isinstance(manifest.get("tests"), list):
        report.err(where, "'tests' must be a list")
        return production, experimental

    def _walk(entries: List[Any], bucket: Dict[str, Path], section_label: str) -> None:
        for entry in entries:
            if not isinstance(entry, dict):
                report.err(where, f"{section_label} entry is not an object: {entry!r}")
                continue
            test_id = entry.get("id") or "<no id>"
            rel_path = entry.get("path")
            if not rel_path:
                report.err(where, f"{section_label} {test_id}: missing 'path'")
                continue
            recipe_path = SUITE_ROOT / rel_path
            if not recipe_path.exists():
                report.err(where, f"{section_label} {test_id}: recipe path '{rel_path}' does not exist")
                continue
            bucket[test_id] = recipe_path

            infra = entry.get("infra_required")
            if infra and infra not in {"mixed", *valid_modes}:
                if infra in DEPRECATED_MODES:
                    report.err(where, f"{section_label} {test_id}: infra_required='{infra}' is DEPRECATED")
                else:
                    report.err(where, f"{section_label} {test_id}: infra_required='{infra}' not in {sorted(valid_modes)}")

    _walk(manifest["tests"], production, "tests")

    exp = manifest.get("experimental_tests")
    if isinstance(exp, list):
        _walk(exp, experimental, "experimental_tests")

    # Detect deprecated mode references anywhere in the manifest body.
    raw = json.dumps(manifest)
    for dep in DEPRECATED_MODES:
        if f'"{dep}"' in raw:
            report.warn(where, f"manifest still references deprecated mode '{dep}' -- remove it")

    return production, experimental


def _validate_orphans(
    manifest_recipes: Dict[str, Path],
    experimental_recipes: Dict[str, Path],
    all_recipes: Iterable[Path],
    report: LintReport,
) -> None:
    known = {p.resolve() for p in manifest_recipes.values()}
    known |= {p.resolve() for p in experimental_recipes.values()}
    for p in all_recipes:
        if p.resolve() not in known:
            rel = p.relative_to(SUITE_ROOT)
            report.warn("orphan", f"recipe '{rel}' is not listed in suite_manifest.tests[] or experimental_tests[]")


def _harvest_show_commands(recipe: Dict[str, Any]) -> List[str]:
    """Walk a recipe and pull every CLI command we will run on the device.

    Looks at the same buckets the runner consumes:

    * ``scenarios[].phases.*.show_commands``
    * ``scenarios[].phases.*.cli_commands``
    * ``scenarios[].phases.verify.cross_layer_checks[].show_commands``

    Inner-shell commands (vtysh / ncc_shell / xraycli / trace_views) live
    in their own scope; this validator only proves the **outer DNOS CLI**
    show-command surface, which is the one ``run_show_command`` /
    ``DNOSSession.send_command`` use. Inner shells are validated by their
    own runner during execution.
    """
    found: List[str] = []
    seen: set = set()

    def _add(cmd: Any) -> None:
        if isinstance(cmd, str) and cmd.strip() and cmd.strip() not in seen:
            seen.add(cmd.strip())
            found.append(cmd.strip())

    for scenario in recipe.get("scenarios", []) or []:
        if not isinstance(scenario, dict):
            continue
        phases = scenario.get("phases") or {}
        if not isinstance(phases, dict):
            continue
        for phase_block in phases.values():
            if isinstance(phase_block, dict):
                for cmd in phase_block.get("show_commands", []) or []:
                    _add(cmd)
                for cmd in phase_block.get("cli_commands", []) or []:
                    _add(cmd)
                for clc in phase_block.get("cross_layer_checks", []) or []:
                    if isinstance(clc, dict):
                        for cmd in clc.get("show_commands", []) or []:
                            _add(cmd)
    return found


def _run_live_command_validation(
    device_ip: str,
    user: str,
    password: str,
    device_label: str,
    recipes: List[Tuple[Path, Dict[str, Any]]],
    report: "LintReport",
    persist: bool,
) -> int:
    """Open SSH to *device_ip* and validate every show command we found.

    Returns 0 on full pass, 1 on at least one rejection. Failures are
    appended to *report* as warnings so existing schema-clean recipes don't
    suddenly become errors when a device is offline; promote with
    ``--strict``.
    """
    try:
        from scaler.dnos_session import DNOSSession  # type: ignore
    except Exception as exc:  # noqa: BLE001
        report.warn("live-validate", f"cannot import scaler.dnos_session ({exc}); skipping live syntax validation")
        return 0

    try:
        from shared.cli_syntax_validator import CliSyntaxValidator  # type: ignore
    except Exception:
        # Re-try via package-relative path (when invoked from the suite root).
        sys.path.insert(0, str(SUITE_ROOT))
        from shared.cli_syntax_validator import CliSyntaxValidator  # type: ignore

    # Wire to the cross-suite knowledge tier so every passing command lands
    # in ~/SCALER/TEST/_shared/knowledge/ (visible to every future /TEST suite).
    try:
        from lib.cache_store import CacheStore  # type: ignore
    except Exception:
        # _shared/lib was added to sys.path by the shim above; if not, try harder.
        for cand in (
            Path.home() / "SCALER" / "TEST" / "_shared",
            Path.home() / "drivenets-topology-studio" / "scaler" / "TEST" / "_shared",
            SUITE_ROOT.parent.parent / "_shared",
        ):
            if (cand / "lib" / "cache_store.py").exists():
                sys.path.insert(0, str(cand))
                break
        from lib.cache_store import CacheStore  # type: ignore

    suite_id = SUITE_ROOT.name
    suite_local_cache = SUITE_ROOT / "tools" / "cli_validation_cache.json"
    cache_store = CacheStore(
        suite_cache=suite_local_cache,
        suite_id=suite_id,
    )

    all_failures = 0
    print(f"\n[live-validate] Connecting to {device_label} ({device_ip}) ...")
    print(f"[live-validate] using shared knowledge: {cache_store.shared_root}")
    try:
        with DNOSSession(device_ip, user, password) as ssh:
            validator = CliSyntaxValidator(
                ssh, device_label=device_label, cache_store=cache_store,
            )
            for recipe_path, recipe in recipes:
                cmds = _harvest_show_commands(recipe)
                if not cmds:
                    continue
                rel = recipe_path.relative_to(SUITE_ROOT)
                print(f"[live-validate] {rel}: validating {len(cmds)} commands ...")
                reports = validator.validate_batch(cmds)
                for r in reports:
                    if r.ok:
                        continue
                    all_failures += 1
                    msg = f"command rejected by device: {r.command!r}"
                    if r.suggestion:
                        msg += f"  ({r.suggestion})"
                    report.warn(str(rel), msg)
            if persist:
                cache_path = validator.persist()
                print(f"[live-validate] Cache persisted: {cache_path}")
    except Exception as exc:  # noqa: BLE001
        report.warn("live-validate", f"SSH validation aborted ({type(exc).__name__}: {exc})")
        return 0

    return 1 if all_failures else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Lint EVPN MAC Mobility recipes.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument(
        "--device",
        metavar="IP",
        help=(
            "Optional: open SSH to this device IP and live-validate every "
            "show command found in every recipe via the ?-completion walker. "
            "Validated commands are cached forever in tools/cli_validation_cache.json."
        ),
    )
    parser.add_argument("--user", default="dnroot", help="SSH user for --device (default: dnroot)")
    parser.add_argument("--password", default="dnroot", help="SSH password for --device (default: dnroot)")
    parser.add_argument(
        "--device-label",
        default="device",
        help="Human-readable label for the device (used in cache provenance, e.g. 'PE-1')",
    )
    parser.add_argument(
        "--no-persist-cache",
        action="store_true",
        help="Do not write the validated commands back to the cache file (dry-run)",
    )
    args = parser.parse_args(argv)

    report = LintReport()

    manifest = _load_json(SUITE_MANIFEST)
    if manifest is None:
        report.err("suite_manifest.json", "file missing")
        print(report.render(args.json), file=sys.stderr)
        return 1
    infra_modes_doc = _load_json(INFRA_MODES_FILE) or {}

    valid_modes: Set[str] = set()
    manifest_modes = manifest.get("infrastructure_modes")
    if isinstance(manifest_modes, dict):
        valid_modes.update(manifest_modes.keys())
    file_modes = (infra_modes_doc.get("modes") or {})
    if isinstance(file_modes, dict):
        valid_modes.update(file_modes.keys())
    valid_modes -= DEPRECATED_MODES

    # Manifest-level deprecation check on infrastructure_modes too.
    if isinstance(manifest_modes, dict):
        for dep in DEPRECATED_MODES:
            if dep in manifest_modes:
                report.err("suite_manifest.json::infrastructure_modes", f"deprecated mode '{dep}' must be removed")
    if isinstance(file_modes, dict):
        for dep in DEPRECATED_MODES:
            if dep in file_modes:
                report.err("infrastructure_modes.json::modes", f"deprecated mode '{dep}' must be removed")

    action_map_keys = _load_action_trigger_map()
    if not action_map_keys:
        report.warn(
            "orchestrator",
            "could not extract ACTION_TRIGGER_MAP keys -- trigger.action validation skipped",
        )

    manifest_recipes, experimental_recipes = _validate_manifest(manifest, valid_modes, report)

    all_recipes = sorted(TESTS_DIR.glob("*/recipe.json"))
    if not all_recipes:
        report.err("tests/", "no recipe.json files found under tests/")
        print(report.render(args.json), file=sys.stderr)
        return 1

    parsed_recipes: List[Tuple[Path, Dict[str, Any]]] = []
    for recipe_path in all_recipes:
        recipe = _load_json(recipe_path)
        if recipe is None:
            report.err(str(recipe_path.relative_to(SUITE_ROOT)), "could not parse JSON")
            continue
        _validate_recipe(recipe_path, recipe, action_map_keys, valid_modes, report)
        parsed_recipes.append((recipe_path, recipe))

    _validate_orphans(manifest_recipes, experimental_recipes, all_recipes, report)

    if args.device and not report.errors:
        # Live-validate only when schema lint is clean. We never run device
        # commands against a recipe that doesn't even parse correctly.
        _run_live_command_validation(
            device_ip=args.device,
            user=args.user,
            password=args.password,
            device_label=args.device_label,
            recipes=parsed_recipes,
            report=report,
            persist=not args.no_persist_cache,
        )

    print(report.render(args.json))

    if report.errors:
        return 1
    if args.strict and report.warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
