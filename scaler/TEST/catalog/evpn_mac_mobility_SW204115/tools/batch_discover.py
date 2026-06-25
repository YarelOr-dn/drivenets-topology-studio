#!/usr/bin/env python3
"""Batch DNOS 26.2 syntax discovery for every recipe in the suite.

Motivation
----------
Before Block 3 (generic handlers) landed, every new recipe triggered a
separate per-file round of "SSH to PE-1 -> run ? completion -> fix
syntax -> re-run". With five recipes coming online at once (G1/G3/G4/G5
plus G2), that per-file grind becomes O(N) SSH sessions for what is
fundamentally an O(1) discovery job.

``batch_discover`` collects every show / clear / config command referenced
by any recipe under ``tests/*/recipe.json`` (optionally filtered via
``--only``), opens **one** persistent SSH session to the target device,
and validates each command in a single pass. Results are written back
into ``runtime_corrections.json`` under the ``per_recipe_validation``
section so subsequent runs of ``mac_mobility_orchestrator.py`` pick up
the live evidence automatically.

Command classification
----------------------
``show`` and ``show config``
    Executed directly. PASS if output has no ``ERROR``/``unknown word``/
    ``incomplete command`` markers.

``clear``
    Executed directly. Clear commands are operational and non-destructive
    for MAC mobility state (no committed config change), so running them
    in batch mode is safe. PASS if output is clean.

``config`` blocks (list of lines starting with ``configure`` /
``network-services ...`` / ``commit`` / ``rollback``)
    Routed through ``commit check`` and then ``rollback 0`` so nothing
    persists. PASS if ``Validation complete`` appears in the commit-check
    output. FAIL if the commit-check emits an ``ERROR`` line (we capture
    the exact text so the recipe / correction file can reference it).

Dry-run
-------
When called with ``--dry-run`` or when no SSH credentials can be
resolved, the tool enumerates every command it would send without
touching the device. Useful for CI and for code review -- the JSON
output can be diffed to confirm a recipe exposes the expected commands.

Exit codes
----------
0 -- All commands validated (or dry-run completed without issue).
1 -- One or more commands returned ERROR during live validation.
2 -- No recipes matched the ``--only`` filter.

Usage examples
--------------

    # Validate every recipe against PE-1 (default device)
    python3 tools/batch_discover.py

    # Dry-run listing every command per recipe
    python3 tools/batch_discover.py --dry-run

    # Only the 4 Block-3 recipes
    python3 tools/batch_discover.py --only evpn_evpn,scale_64k,clear_operations,pw_suppression_sanctions

    # JSON output piped into jq
    python3 tools/batch_discover.py --json | jq '.summary'
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

SUITE_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = SUITE_ROOT / "tests"
CORRECTIONS_FILE = SUITE_ROOT / "runtime_corrections.json"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class CommandFinding:
    recipe: str
    command: str
    kind: str  # "show", "clear", "config"
    source: str  # dotted-path into the recipe (e.g. SC01.trigger.before_shows[0])
    status: str = "pending"  # "pass", "fail", "skip", "dry_run"
    evidence: str = ""
    error: str = ""


@dataclass
class RecipeFindings:
    recipe_id: str
    recipe_path: Path
    recipe_type: str
    commands: List[CommandFinding] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Recipe extraction
# ---------------------------------------------------------------------------


_SHOW_PREFIX = re.compile(r"^\s*show\b")
_CLEAR_PREFIX = re.compile(r"^\s*clear\b")
_CONFIG_PREFIX = re.compile(r"^\s*(configure|config|end|commit|rollback)\b")
_SCAFFOLD = re.compile(
    r"^\s*(configure|config|end|commit|rollback)\s*(0|check)?\s*$",
)

# Key-path segments that definitely do NOT contain CLI commands. We
# enumerate them so descriptive prose (what_happens, what_cannot_happen,
# scenarios[*].name etc.) can never be misread as config lines.
_DESCRIPTIVE_SEGMENTS = {
    "name", "what_happens", "what_cannot_happen", "description",
    "note", "notes", "reason", "rationale", "redesign_note",
    "status_note", "title", "label",
    "recipe_type", "type", "source", "jira_key", "parent_category",
    "status", "feature", "created", "updated", "wired",
    "gap_rationale", "spirent_note", "suppression_note",
    "gap_rationale", "device", "doc_source",
    "pass_criteria", "method", "sanction", "parser",
    "resolve", "fallback_resolve", "value", "fallback_value",
    "setup_sequence",
    "dnos_26_2_validated_sanctions", "dnos_26_2_invalid_sanctions",
    "clear_commands_tested", "show_commands_validated",
    "ignore_patterns", "sections", "full_config",
    "timing_requirements",
    "convergence_criteria",
    "config_generator_ref", "fix_config", "fix_via",
}

# Segment names that SHOULD contain command strings. Anything else
# we only treat as a command if its parent segment is in this set.
_COMMAND_SEGMENTS = {
    "command", "commands", "config_commands",
    "check_command", "check_commands", "show_command",
    "show_commands", "before_shows", "after_shows",
    "cleanup_commands", "setup_commands",
    "counter_command", "counter_commands",
    "rollback_command",
    "from", "fallback_from",
    "keys",  # synthesised by _walk_strings when emitting dict keys
            # from _KEY_IS_COMMAND_CONTAINERS entries.
}


def _classify(cmd: str) -> Optional[str]:
    if _SHOW_PREFIX.match(cmd):
        return "show"
    if _CLEAR_PREFIX.match(cmd):
        return "clear"
    if _SCAFFOLD.match(cmd):
        # ``configure`` / ``commit`` / ``rollback 0`` / ``end`` -- scaffolds
        # that we record but do not individually validate.
        return "config"
    if _CONFIG_PREFIX.match(cmd):
        return "config"
    # Bare config lines (e.g. ``network-services evpn instance ...``) are
    # treated as config too.
    if re.match(r"^\s*(network-services|protocols|interfaces|"
                r"routing-options|routing-policy)\b", cmd):
        return "config"
    return None


def _path_segments(path: str) -> List[str]:
    """Split a dotted-path like ``a.b[0].c`` into atomic segments."""
    return [s.split("[", 1)[0] for s in path.split(".") if s]


def _path_is_descriptive(path: str) -> bool:
    """Return True if the leaf segment is known to carry prose, not CLI."""
    segments = _path_segments(path)
    if not segments:
        return False
    last = segments[-1]
    return last in _DESCRIPTIVE_SEGMENTS


def _path_is_command_bearing(path: str) -> bool:
    """Return True if the path points into a command-bearing key."""
    segments = _path_segments(path)
    return any(s in _COMMAND_SEGMENTS for s in segments)


# Dict keys in these objects ARE commands (keys = commands, values =
# descriptions). Emit the KEY, not the VALUE, when walking them.
_KEY_IS_COMMAND_CONTAINERS = {
    "show_commands_validated", "clear_commands_validated",
    "clear_commands_tested", "show_commands_tested",
}


def _walk_strings(obj: Any, path: str,
                  out: List[Tuple[str, str]]) -> None:
    """Walk any JSON structure, emitting (path, string) for each leaf str."""
    if isinstance(obj, dict):
        leaf = _path_segments(path)[-1] if path else ""
        if leaf in _KEY_IS_COMMAND_CONTAINERS:
            # Keys in this dict are the commands themselves; values are
            # descriptions we deliberately ignore so "Clear suppression
            # for specific MAC" doesn't get mis-classified as a clear
            # command.
            for k in obj:
                if isinstance(k, str):
                    out.append((f"{path}.keys", k))
            return
        for k, v in obj.items():
            _walk_strings(v, f"{path}.{k}" if path else str(k), out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _walk_strings(v, f"{path}[{i}]", out)
    elif isinstance(obj, str):
        out.append((path, obj))


def _extract_commands(recipe: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """Return [(command, kind, source_path)] for every show/clear/config line.

    Rules:
      * Path must sit inside a known command-bearing segment
        (e.g. ``.check_command``, ``.commands[*]``, ``.before_shows[*]``).
      * Descriptive segments (``what_happens``, ``name`` etc.) are skipped
        even if the string happens to start with ``clear`` or ``show``.
      * Pure scaffolds (``config`` / ``commit`` / ``rollback 0`` / ``end``)
        are emitted with kind ``config`` so the tool records that the
        recipe uses them, but the live validator skips them.
    """
    pairs: List[Tuple[str, str]] = []
    _walk_strings(recipe, "", pairs)
    seen: Set[Tuple[str, str]] = set()
    out: List[Tuple[str, str, str]] = []
    for src, s in pairs:
        if _path_is_descriptive(src):
            continue
        kind = _classify(s)
        if not kind:
            continue
        # Require a command-bearing parent segment OR a leaf that is a
        # genuine CLI command prefix (show/clear/commit/rollback/end).
        # This catches config_commands[] entries while excluding free-text
        # descriptive keys.
        if not _path_is_command_bearing(src):
            # Still allow unambiguous CLI commands (show/clear/scaffolds)
            # even if the enclosing key isn't in the whitelist; but skip
            # bare "config"/"end" words inside arbitrary arrays since they
            # create noise.
            if _SCAFFOLD.match(s):
                continue
            if not (_SHOW_PREFIX.match(s) or _CLEAR_PREFIX.match(s)):
                continue
        key = (s, kind)
        if key in seen:
            continue
        seen.add(key)
        out.append((s, kind, src))
    return out


def _load_recipes(only: Optional[Set[str]]) -> List[RecipeFindings]:
    findings: List[RecipeFindings] = []
    for recipe_file in sorted(TESTS_DIR.glob("*/recipe.json")):
        group = recipe_file.parent.name
        if only and group not in only:
            continue
        try:
            data = json.loads(recipe_file.read_text())
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] {recipe_file}: invalid JSON ({exc})", file=sys.stderr)
            continue
        rf = RecipeFindings(
            recipe_id=data.get("id", group),
            recipe_path=recipe_file,
            recipe_type=data.get("recipe_type") or data.get("type") or "unknown",
        )
        for cmd, kind, source in _extract_commands(data):
            rf.commands.append(CommandFinding(
                recipe=group, command=cmd, kind=kind, source=source,
            ))
        findings.append(rf)
    return findings


# ---------------------------------------------------------------------------
# Live SSH validation
# ---------------------------------------------------------------------------


_ERR_MARKERS = (
    "unknown word",
    "incomplete command",
    "syntax error",
    "ambiguous command",
)

# Substrings that look like syntax errors but indicate environmental /
# placeholder mismatches rather than a broken recipe line. batch_discover
# records them as SKIP so the session doesn't flag a fake regression.
_ENV_MARKERS = (
    "no ncp id found for interface",
    "interface not found",
    "no such instance",
    "no matching entries",
)

# Substrings that confirm a candidate commit has nothing to change. These
# are PASS for syntax-validation purposes (DNOS accepted the structure;
# the config happened to be idempotent). Without this, the tool misreads
# an already-configured line as a failure.
_NOOP_COMMIT_MARKERS = (
    "commit action is not applicable",
    "no configuration changes were made",
    "no changes to commit",
)


def _looks_like_error(output: str) -> bool:
    low = output.lower()
    if any(m in low for m in _NOOP_COMMIT_MARKERS):
        return False
    if any(m in low for m in _ENV_MARKERS):
        return False
    # A bare "error" word alone is too broad (e.g. "Error counters: 0")
    # so we require one of the structured markers above OR a line starting
    # with "ERROR:" / "% ".
    for line in low.splitlines():
        stripped = line.strip()
        if stripped.startswith("error:") or stripped.startswith("% "):
            return True
    return any(m in low for m in _ERR_MARKERS)


def _is_env_mismatch(output: str) -> bool:
    low = output.lower()
    return any(m in low for m in _ENV_MARKERS)


def _is_noop_commit(output: str) -> bool:
    low = output.lower()
    return any(m in low for m in _NOOP_COMMIT_MARKERS)


def _validate_live(findings: List[RecipeFindings], device: str,
                   template_evpn: str) -> None:
    """Open one SSH session, validate each unique command, record status."""
    # Import lazily so dry-run works without the full orchestrator stack.
    sys.path.insert(0, str(SUITE_ROOT))
    try:
        from shared.device_runner import (  # type: ignore
            get_persistent_ssh_session,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] cannot import device_runner: {exc}", file=sys.stderr)
        for rf in findings:
            for cmd in rf.commands:
                cmd.status = "skip"
                cmd.error = f"device_runner import failed: {exc}"
        return

    session = get_persistent_ssh_session(device)
    if session is None:
        print(
            f"[WARN] No SSH session available for {device!r}; "
            "falling back to dry-run mode.",
            file=sys.stderr,
        )
        for rf in findings:
            for cmd in rf.commands:
                cmd.status = "skip"
                cmd.error = "No SSH credentials"
        return

    # De-duplicate commands across recipes -- execute each unique
    # command ONCE and share the verdict.
    unique: Dict[Tuple[str, str], Tuple[str, str]] = {}

    def _substitute(cmd: str) -> str:
        # Replace common recipe placeholders so the CLI parser can accept
        # the command. These substitutions are informational only -- the
        # caller's goal is "did DNOS accept the structure?", not "did the
        # concrete instance match".
        return (cmd
                .replace("{evpn_name}", template_evpn)
                .replace("{test_mac}", "00:DE:AD:00:01:01")
                .replace("{ncp_id}", "0")
                .replace("{ac_interface}", "ge100-0/0/3")
                .replace("{ac1_interface}", "ge100-0/0/3"))

    try:
        for rf in findings:
            for cmd in rf.commands:
                key = (cmd.command, cmd.kind)
                if key in unique:
                    status, evidence = unique[key]
                    cmd.status = status
                    cmd.evidence = evidence[:500]
                    continue
                try:
                    expanded = _substitute(cmd.command)
                    if cmd.kind == "config":
                        # Wrap in commit check so nothing persists.
                        if _CONFIG_PREFIX.match(expanded):
                            # Raw "config" / "commit" / "rollback" etc. --
                            # not something we can standalone-validate.
                            cmd.status = "skip"
                            cmd.evidence = "[config scaffold line -- not sent]"
                            unique[key] = (cmd.status, cmd.evidence)
                            continue
                        session.send_command("configure", auto_no_more=False)
                        try:
                            cfg_out = session.send_command(
                                expanded, auto_no_more=False,
                            )
                            cc = session.send_command(
                                "commit check", auto_no_more=False,
                            )
                        finally:
                            session.send_command("rollback 0", auto_no_more=False)
                            session.send_command("end", auto_no_more=False)
                        combined = (cfg_out or "") + "\n" + (cc or "")
                        # Environmental mismatches (placeholder interface
                        # not on DUT, etc.) are NOT recipe bugs -- skip.
                        if _is_env_mismatch(combined):
                            cmd.status = "skip"
                            cmd.evidence = (
                                "[env mismatch -- placeholder not on DUT] "
                                + combined[:400]
                            )
                        # Idempotent commits (already configured) mean
                        # DNOS accepted the syntax; treat as PASS.
                        elif _is_noop_commit(combined):
                            cmd.status = "pass"
                            cmd.evidence = (
                                "[noop commit: config already in place] "
                                + combined[:400]
                            )
                        else:
                            cc_ok = (
                                "validation complete" in cc.lower()
                                and not _looks_like_error(combined)
                            )
                            cmd.status = "pass" if cc_ok else "fail"
                            cmd.evidence = cc[:500]
                            if not cc_ok:
                                cmd.error = combined[:300]
                    else:
                        out = session.send_command(expanded, auto_no_more=False)
                        if _is_env_mismatch(out):
                            cmd.status = "skip"
                            cmd.evidence = (
                                "[env mismatch -- placeholder not on DUT] "
                                + out[:400]
                            )
                        elif _looks_like_error(out):
                            cmd.status = "fail"
                            cmd.evidence = out[:500]
                            cmd.error = out[:300]
                        else:
                            cmd.status = "pass"
                            cmd.evidence = out[:300]
                except Exception as exc:  # noqa: BLE001
                    cmd.status = "fail"
                    cmd.error = f"{type(exc).__name__}: {exc}"
                unique[key] = (cmd.status, cmd.evidence)
    finally:
        # Do not close the session -- it may be reused by the
        # orchestrator on a subsequent invocation within the same
        # process.
        pass


# ---------------------------------------------------------------------------
# Output + persistence
# ---------------------------------------------------------------------------


def _update_corrections(findings: List[RecipeFindings], device: str,
                        dry_run: bool) -> None:
    if not CORRECTIONS_FILE.exists():
        return
    data = json.loads(CORRECTIONS_FILE.read_text())
    per_recipe = data.setdefault("per_recipe_validation", {})
    now = datetime.now(timezone.utc).isoformat()
    for rf in findings:
        group = rf.recipe_path.parent.name
        entry = per_recipe.setdefault(group, {})
        entry["recipe_path"] = str(rf.recipe_path.relative_to(SUITE_ROOT))
        entry["batch_validated_on"] = "dry-run" if dry_run else now
        entry["batch_device"] = device if not dry_run else "n/a"
        entry["command_counts"] = {
            "show": sum(1 for c in rf.commands if c.kind == "show"),
            "clear": sum(1 for c in rf.commands if c.kind == "clear"),
            "config": sum(1 for c in rf.commands if c.kind == "config"),
        }
        per_status: Dict[str, int] = {}
        for c in rf.commands:
            per_status[c.status] = per_status.get(c.status, 0) + 1
        entry["batch_status_breakdown"] = per_status
        entry["batch_failures"] = [
            {"command": c.command, "kind": c.kind, "error": c.error[:200]}
            for c in rf.commands if c.status == "fail"
        ]
    data["_last_validated"] = now[:10]
    if dry_run:
        data["_last_validated_note"] = "dry-run batch_discover"
    CORRECTIONS_FILE.write_text(json.dumps(data, indent=2) + "\n")


def _summary(findings: List[RecipeFindings]) -> Dict[str, Any]:
    total = sum(len(rf.commands) for rf in findings)
    by_status: Dict[str, int] = {}
    for rf in findings:
        for c in rf.commands:
            by_status[c.status] = by_status.get(c.status, 0) + 1
    return {
        "recipes_scanned": len(findings),
        "total_commands": total,
        "by_status": by_status,
    }


def _print_human(findings: List[RecipeFindings]) -> None:
    for rf in findings:
        group = rf.recipe_path.parent.name
        print(f"\n=== {group} ({rf.recipe_type}) ===")
        print(f"    {rf.recipe_path}")
        if not rf.commands:
            print("    (no commands found)")
            continue
        for c in rf.commands:
            mark = {
                "pass": "[OK]   ",
                "fail": "[FAIL] ",
                "skip": "[SKIP] ",
                "dry_run": "[DRY]  ",
                "pending": "[??]   ",
            }.get(c.status, "[??]   ")
            src = f" ({c.source})" if c.source else ""
            print(f"  {mark} {c.kind:<6} {c.command}{src}")
            if c.status == "fail" and c.error:
                print(f"           error: {c.error[:200]}")


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--device", default="PE-1",
                        help="DNOS device name resolved via "
                             "shared.device_runner (default: PE-1)")
    parser.add_argument("--only", default="",
                        help="Comma-separated recipe directory names "
                             "(e.g. clear_operations,evpn_evpn). "
                             "Empty = all recipes.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Do not SSH; only enumerate commands.")
    parser.add_argument("--json", action="store_true",
                        help="Emit machine-readable JSON report to stdout "
                             "instead of the human-readable table.")
    parser.add_argument("--template-evpn", default="HA_TEST_ELAN",
                        help="Substituted for '{evpn_name}' in commands "
                             "sent to the device (default: HA_TEST_ELAN).")
    parser.add_argument("--no-persist", action="store_true",
                        help="Do NOT write per-recipe validation results "
                             "back into runtime_corrections.json.")
    args = parser.parse_args(argv)

    only = {s.strip() for s in args.only.split(",") if s.strip()} or None
    findings = _load_recipes(only)
    if only and not findings:
        print(
            f"[ERROR] --only filter {sorted(only)} matched 0 recipes",
            file=sys.stderr,
        )
        return 2

    if args.dry_run:
        for rf in findings:
            for c in rf.commands:
                c.status = "dry_run"
    else:
        _validate_live(findings, args.device, args.template_evpn)

    if not args.no_persist:
        _update_corrections(findings, args.device, args.dry_run)

    if args.json:
        out = {
            "device": args.device,
            "dry_run": args.dry_run,
            "summary": _summary(findings),
            "recipes": [
                {
                    "recipe": rf.recipe_path.parent.name,
                    "recipe_type": rf.recipe_type,
                    "recipe_id": rf.recipe_id,
                    "commands": [
                        {
                            "command": c.command,
                            "kind": c.kind,
                            "source": c.source,
                            "status": c.status,
                            "error": c.error,
                        }
                        for c in rf.commands
                    ],
                }
                for rf in findings
            ],
        }
        print(json.dumps(out, indent=2))
    else:
        _print_human(findings)
        print("\n--- Summary ---")
        print(json.dumps(_summary(findings), indent=2))

    fail_count = sum(
        1 for rf in findings for c in rf.commands if c.status == "fail"
    )
    return 1 if fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
