#!/usr/bin/env python3
"""
DNOS CLI Discovery Tool -- automated `cmd search` + recipe validation.

Connects to a DNOS device via SSH (expect-based for TTY), runs `cmd search`
for specified keywords, parses show/clear/configure command trees, and
cross-validates recipe files.

Usage:
    # Discover all EVPN commands and validate recipes
    python3 dnos_cli_discovery.py --device RR-SA-2 --ip 100.64.4.205 \\
        --keywords evpn,mac-mobility,bridge-domain \\
        --catalog scaler/TEST/catalog/evpn_mac_mobility_SW204115

    # Just discover (no recipe validation)
    python3 dnos_cli_discovery.py --device PE-4 --ip 100.64.7.197 \\
        --keywords evpn --output-json /tmp/evpn_commands.json

    # Validate recipes against existing CLI completions DB (no device needed)
    python3 dnos_cli_discovery.py --offline \\
        --catalog scaler/TEST/catalog/evpn_mac_mobility_SW204115
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

_SCALER_DB = Path.home() / "SCALER" / "db" / "devices.json"
_CLI_COMPLETIONS = Path.home() / ".cursor" / "dnos-cli-completions.json"
_LEARNED_RULES = Path.home() / ".cursor" / "test-reference" / "learned_rules.md"

CREDENTIAL_SETS = [
    ("dnroot", "dnroot"),
    ("dn", "drivenets"),
    ("admin", "admin"),
]


@dataclass
class DiscoveryResult:
    device: str
    device_ip: str
    dnos_version: str = ""
    keywords: List[str] = field(default_factory=list)
    show_commands: List[str] = field(default_factory=list)
    clear_commands: List[str] = field(default_factory=list)
    configure_paths: List[str] = field(default_factory=list)
    internal_commands: List[str] = field(default_factory=list)
    raw_output: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device": self.device,
            "device_ip": self.device_ip,
            "dnos_version": self.dnos_version,
            "keywords": self.keywords,
            "show_commands": self.show_commands,
            "clear_commands": self.clear_commands,
            "configure_paths": self.configure_paths,
            "internal_commands": self.internal_commands,
            "errors": self.errors,
            "timestamp": self.timestamp,
            "stats": {
                "total_show": len(self.show_commands),
                "total_clear": len(self.clear_commands),
                "total_configure": len(self.configure_paths),
                "total_internal": len(self.internal_commands),
            },
        }

    def categorize(self) -> Dict[str, List[str]]:
        """Group show commands by feature subtree (e.g., mac-table, arp-table)."""
        cats: Dict[str, List[str]] = {}
        for cmd in self.show_commands:
            parts = cmd.replace("show ", "").split()
            if len(parts) >= 2:
                key = f"{parts[0]} {parts[1]}"
            elif parts:
                key = parts[0]
            else:
                key = "other"
            cats.setdefault(key, []).append(cmd)
        return cats


@dataclass
class ValidationReport:
    recipe_path: str
    recipe_id: str
    validated_ok: List[str] = field(default_factory=list)
    missing_from_recipe: List[str] = field(default_factory=list)
    invalid_in_recipe: List[str] = field(default_factory=list)
    wrongly_marked_invalid: List[str] = field(default_factory=list)
    tbd_items: List[str] = field(default_factory=list)
    suggested_additions: List[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not (
            self.invalid_in_recipe
            or self.wrongly_marked_invalid
            or self.tbd_items
        )

    def summary_line(self) -> str:
        status = "OK" if self.clean else "NEEDS FIX"
        parts = [f"validated={len(self.validated_ok)}"]
        if self.missing_from_recipe:
            parts.append(f"new={len(self.missing_from_recipe)}")
        if self.invalid_in_recipe:
            parts.append(f"INVALID={len(self.invalid_in_recipe)}")
        if self.wrongly_marked_invalid:
            parts.append(f"WRONG_INVALID={len(self.wrongly_marked_invalid)}")
        if self.tbd_items:
            parts.append(f"TBD={len(self.tbd_items)}")
        return f"  {self.recipe_id:40s} {' '.join(parts)}  {status}"


# ---------------------------------------------------------------------------
# SSH via expect
# ---------------------------------------------------------------------------

def _resolve_device(device_name: str) -> Optional[Tuple[str, str, str]]:
    """Look up device in SCALER DB -> (hostname, ip, password)."""
    if not _SCALER_DB.is_file():
        return None
    try:
        with open(_SCALER_DB) as f:
            db = json.load(f)
        for dev in db.get("devices", []):
            if device_name.lower() in (
                dev.get("hostname", "").lower(),
                dev.get("id", "").lower(),
            ):
                pw = dev.get("password", "")
                try:
                    pw = base64.b64decode(pw).decode()
                except Exception:
                    pass
                return dev["hostname"], dev["ip"], pw
    except Exception:
        pass
    return None


def ssh_cmd_search(
    ip: str,
    keyword: str,
    username: str = "dnroot",
    password: str = "dnroot",
    timeout: int = 25,
) -> str:
    """Run `cmd search <keyword> | no-more` on a DNOS device via expect."""
    expect_script = textwrap.dedent(f"""\
        set timeout {timeout}
        log_user 1
        spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no {username}@{ip}
        expect "assword:"
        send "{password}\\r"
        expect "#"
        send "cmd search {keyword} | no-more\\r"
        expect "#"
        send "exit\\r"
        expect eof
    """)
    try:
        result = subprocess.run(
            ["expect", "-c", expect_script],
            capture_output=True,
            text=True,
            timeout=timeout + 10,
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        return f"ERROR: SSH timeout after {timeout}s for keyword '{keyword}'"
    except FileNotFoundError:
        return "ERROR: 'expect' not installed"


def ssh_show_version(
    ip: str,
    username: str = "dnroot",
    password: str = "dnroot",
) -> str:
    """Get DNOS version from device."""
    expect_script = textwrap.dedent(f"""\
        set timeout 15
        log_user 1
        spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no {username}@{ip}
        expect "assword:"
        send "{password}\\r"
        expect "#"
        send "show system | no-more\\r"
        expect "#"
        send "exit\\r"
        expect eof
    """)
    try:
        result = subprocess.run(
            ["expect", "-c", expect_script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        m = re.search(r"DNOS \[[\d.]+\].*Copyright", result.stdout)
        if m:
            return m.group(0)
        m2 = re.search(r"Version:\s*(.+)", result.stdout)
        if m2:
            return m2.group(1).strip()
    except Exception:
        pass
    return ""


def ssh_multi_cmd_search(
    ip: str,
    keywords: List[str],
    username: str = "dnroot",
    password: str = "dnroot",
    timeout: int = 30,
) -> Dict[str, str]:
    """Run multiple cmd search commands in a single SSH session."""
    cmd_block = ""
    for kw in keywords:
        cmd_block += f'send "cmd search {kw} | no-more\\r"\nexpect "#"\n'

    expect_script = textwrap.dedent(f"""\
        set timeout {timeout}
        log_user 1
        spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no {username}@{ip}
        expect "assword:"
        send "{password}\\r"
        expect "#"
        {cmd_block}
        send "exit\\r"
        expect eof
    """)
    try:
        result = subprocess.run(
            ["expect", "-c", expect_script],
            capture_output=True,
            text=True,
            timeout=timeout + 15,
        )
        output = result.stdout
    except subprocess.TimeoutExpired:
        return {kw: f"ERROR: timeout" for kw in keywords}
    except FileNotFoundError:
        return {kw: "ERROR: expect not installed" for kw in keywords}

    results = {}
    for kw in keywords:
        marker = f"cmd search {kw} | no-more"
        start = output.find(marker)
        if start == -1:
            results[kw] = ""
            continue
        end = output.find("# cmd search", start + len(marker))
        if end == -1:
            end = output.find("# exit", start + len(marker))
        if end == -1:
            end = len(output)
        results[kw] = output[start + len(marker) : end]
    return results


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\[0m|\[7m")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def parse_cmd_search_output(raw: str) -> Tuple[List[str], List[str], List[str], List[str]]:
    """
    Parse `cmd search` output into (show_cmds, clear_cmds, configure_paths, internal_cmds).

    Each line of `cmd search` output is a full command path.
    """
    show: List[str] = []
    clear: List[str] = []
    configure: List[str] = []
    internal: List[str] = []

    for raw_line in _strip_ansi(raw).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "cmd search" in line:
            continue
        if line.startswith("-- More --") or line.startswith("ERROR:"):
            continue

        if line.startswith("show dnos-internal"):
            internal.append(line)
        elif line.startswith("show "):
            show.append(line)
        elif line.startswith("clear "):
            clear.append(line)
        elif line.startswith("configure "):
            configure.append(line)

    return show, clear, configure, internal


def discover_device_cli(
    device: str,
    ip: str,
    keywords: List[str],
    username: str = "dnroot",
    password: str = "dnroot",
) -> DiscoveryResult:
    """Full CLI discovery: connect, search, parse, return structured result."""
    result = DiscoveryResult(device=device, device_ip=ip, keywords=keywords)

    result.dnos_version = ssh_show_version(ip, username, password)

    if len(keywords) <= 5:
        raw_outputs = ssh_multi_cmd_search(ip, keywords, username, password)
    else:
        raw_outputs = {}
        for kw in keywords:
            raw_outputs[kw] = ssh_cmd_search(ip, kw, username, password)

    all_show: Set[str] = set()
    all_clear: Set[str] = set()
    all_configure: Set[str] = set()
    all_internal: Set[str] = set()

    for kw, raw in raw_outputs.items():
        if raw.startswith("ERROR:"):
            result.errors.append(f"{kw}: {raw}")
            continue
        result.raw_output[kw] = raw[:50000]
        show, clear, configure, internal = parse_cmd_search_output(raw)
        all_show.update(show)
        all_clear.update(clear)
        all_configure.update(configure)
        all_internal.update(internal)

    result.show_commands = sorted(all_show)
    result.clear_commands = sorted(all_clear)
    result.configure_paths = sorted(all_configure)
    result.internal_commands = sorted(all_internal)
    return result


# ---------------------------------------------------------------------------
# Recipe validation
# ---------------------------------------------------------------------------

_ALWAYS_VALID_PREFIXES = [
    "show system",
    "show config ",
    "show file ",
    "show interfaces ",
    "show bridge-domain ",
    "show network-services ",
    "show bgp ",
]


def validate_recipe(
    recipe_path: Path,
    discovery: DiscoveryResult,
) -> ValidationReport:
    """Cross-reference a recipe's commands against live discovery."""
    with open(recipe_path) as f:
        recipe = json.load(f)

    report = ValidationReport(
        recipe_path=str(recipe_path),
        recipe_id=recipe.get("id", recipe_path.stem),
    )

    all_valid = set(discovery.show_commands) | set(discovery.internal_commands)
    all_clear_valid = set(discovery.clear_commands)

    show_validated = recipe.get("show_commands_validated", {})
    for cmd_with_pipe in show_validated:
        base_cmd = cmd_with_pipe.split(" | ")[0].strip()

        if any(base_cmd.startswith(p) for p in _ALWAYS_VALID_PREFIXES):
            report.validated_ok.append(cmd_with_pipe)
            continue

        found = False
        for valid_cmd in all_valid:
            if _fuzzy_cmd_match(base_cmd, valid_cmd):
                found = True
                break
        if found:
            report.validated_ok.append(cmd_with_pipe)
        else:
            report.invalid_in_recipe.append(cmd_with_pipe)

    invalid_cmds = recipe.get("invalid_commands", {})
    for cmd in invalid_cmds:
        base = cmd.split(" | ")[0].strip()
        for valid_cmd in all_valid:
            if _fuzzy_cmd_match(base, valid_cmd):
                report.wrongly_marked_invalid.append(
                    f"{cmd} -> actually exists as: {valid_cmd}"
                )
                break

    content_str = json.dumps(recipe).lower()
    tbd_count = content_str.count("tbd")
    if tbd_count > 0:
        report.tbd_items.append(f"{tbd_count} TBD references found in recipe")

    _suggest_additions(recipe, discovery, report)
    return report


def _fuzzy_cmd_match(template: str, candidate: str) -> bool:
    """Check if a template command (with {params}) matches a candidate (with <params>).

    Handles optional parameters in brackets [...] and different param syntax.
    """
    t_parts = re.sub(r"\{[^}]+\}", "PARAM", template).split()
    c_raw = re.sub(r"\[([^\]]+)\]", r"\1", candidate)
    c_parts = re.sub(r"<[^>]+>", "PARAM", c_raw).split()
    c_parts = [re.sub(r"<<[^>]+>>", "PARAM", p) for p in c_parts]

    if len(t_parts) == len(c_parts):
        return all(
            tp == cp or tp == "PARAM" or cp == "PARAM"
            for tp, cp in zip(t_parts, c_parts)
        )

    if len(t_parts) < len(c_parts):
        i = 0
        for tp in t_parts:
            if i >= len(c_parts):
                return False
            if tp == c_parts[i] or tp == "PARAM" or c_parts[i] == "PARAM":
                i += 1
            else:
                return False
        return True

    return False


_FEATURE_SHOW_PATTERNS = {
    "evpn-mac-mobility": [
        "show evpn mac-table instance PARAM suppress",
        "show evpn mac-table instance PARAM detail",
        "show evpn mac-table instance PARAM local",
        "show evpn instance PARAM loop-prevention",
        "show evpn mac summary",
        "show evpn forwarding-table mac-address-table instance PARAM",
        "show dnos-internal routing evpn mac-mobility-redis-count",
    ],
    "evpn": [
        "show evpn summary",
        "show evpn mac-table instance PARAM",
        "show evpn mac-table instance PARAM mac PARAM",
        "show evpn arp-table instance PARAM",
        "show evpn instance PARAM detail",
        "show bgp l2vpn evpn summary",
    ],
}


def _suggest_additions(
    recipe: dict,
    discovery: DiscoveryResult,
    report: ValidationReport,
) -> None:
    """Suggest commands from discovery that the recipe might benefit from."""
    feature = recipe.get("feature", "")
    patterns = _FEATURE_SHOW_PATTERNS.get(feature, [])
    if not patterns:
        for key, pats in _FEATURE_SHOW_PATTERNS.items():
            if key in feature:
                patterns = pats
                break

    existing = set()
    for cmd in recipe.get("show_commands_validated", {}):
        existing.add(re.sub(r"\{[^}]+\}", "PARAM", cmd.split(" | ")[0].strip()))

    for pattern in patterns:
        if pattern not in existing:
            for valid_cmd in discovery.show_commands + discovery.internal_commands:
                norm = re.sub(r"<[^>]+>", "PARAM", valid_cmd)
                norm = re.sub(r"<<[^>]+>>", "PARAM", norm)
                if norm == pattern:
                    report.suggested_additions.append(valid_cmd)
                    break


def validate_catalog(
    catalog_path: Path,
    discovery: DiscoveryResult,
) -> List[ValidationReport]:
    """Validate all recipes in a test catalog against discovery."""
    reports = []
    tests_dir = catalog_path / "tests"
    if not tests_dir.is_dir():
        recipe = catalog_path / "recipe.json"
        if recipe.is_file():
            reports.append(validate_recipe(recipe, discovery))
        return reports

    for test_dir in sorted(tests_dir.iterdir()):
        recipe = test_dir / "recipe.json"
        if recipe.is_file():
            reports.append(validate_recipe(recipe, discovery))
    return reports


# ---------------------------------------------------------------------------
# CLI completions DB update
# ---------------------------------------------------------------------------

def update_cli_completions(
    discovery: DiscoveryResult,
    feature_key: str,
) -> Tuple[int, int]:
    """Update ~/.cursor/dnos-cli-completions.json with discovery results.

    Returns (new_entries, updated_entries).
    """
    db: Dict[str, Any] = {}
    if _CLI_COMPLETIONS.is_file():
        with open(_CLI_COMPLETIONS) as f:
            db = json.load(f)

    new_count = 0
    updated_count = 0

    section_key = f"show {feature_key} <hierarchy>"
    if section_key not in db:
        new_count += 1
    else:
        updated_count += 1

    show_cats: Dict[str, List[str]] = {}
    for cmd in discovery.show_commands:
        prefix = cmd.split()[1] if len(cmd.split()) > 1 else "other"
        sub = cmd.split()[2] if len(cmd.split()) > 2 else "top"
        cat_key = f"{prefix}_{sub}" if sub != "top" else prefix
        show_cats.setdefault(cat_key, []).append(cmd)

    db[section_key] = {
        "description": f"Show commands for {feature_key}. Auto-discovered via dnos_cli_discovery.py.",
        "discovered_on": f"{discovery.device} ({discovery.device_ip})",
        "discovered_at": datetime.now().strftime("%Y-%m-%d"),
        "dnos_version": discovery.dnos_version,
        **show_cats,
    }

    clear_key = f"clear {feature_key} <subcommands>"
    if discovery.clear_commands:
        if clear_key not in db:
            new_count += 1
        else:
            updated_count += 1
        clear_cats: Dict[str, List[str]] = {}
        for cmd in discovery.clear_commands:
            parts = cmd.replace("clear ", "").split()
            cat = parts[1] if len(parts) > 1 else "general"
            clear_cats.setdefault(cat, []).append(cmd)
        db[clear_key] = {
            "description": f"Clear commands for {feature_key}. Auto-discovered.",
            "discovered_at": datetime.now().strftime("%Y-%m-%d"),
            **clear_cats,
        }

    internal_key = f"show dnos-internal {feature_key}"
    if discovery.internal_commands:
        internals_for_feature = [
            c for c in discovery.internal_commands if feature_key in c
        ]
        if internals_for_feature:
            if internal_key not in db:
                new_count += 1
            else:
                updated_count += 1
            db[internal_key] = {
                "description": f"Internal debug commands for {feature_key}.",
                "discovered_at": datetime.now().strftime("%Y-%m-%d"),
                "commands": internals_for_feature,
            }

    db["_last_updated"] = datetime.now().strftime("%Y-%m-%d")
    db["_source_device"] = f"{discovery.device} ({discovery.device_ip})"

    with open(_CLI_COMPLETIONS, "w") as f:
        json.dump(db, f, indent=2)

    return new_count, updated_count


# ---------------------------------------------------------------------------
# Auto-fix recipes
# ---------------------------------------------------------------------------

def auto_fix_recipe(
    recipe_path: Path,
    discovery: DiscoveryResult,
    report: ValidationReport,
    dry_run: bool = True,
) -> List[str]:
    """Apply fixes to a recipe based on validation report.

    Returns list of changes made (or would-be-made if dry_run).
    """
    changes: List[str] = []

    with open(recipe_path) as f:
        recipe = json.load(f)

    if report.wrongly_marked_invalid:
        inv = recipe.get("invalid_commands", {})
        for entry in report.wrongly_marked_invalid:
            wrong_cmd = entry.split(" -> ")[0].strip()
            actual = entry.split("actually exists as: ")[-1].strip()
            if wrong_cmd in inv:
                del inv[wrong_cmd]
                changes.append(f"REMOVED from invalid_commands: {wrong_cmd} (is valid: {actual})")
        recipe["invalid_commands"] = inv

    if report.suggested_additions:
        validated = recipe.get("show_commands_validated", {})
        for cmd in report.suggested_additions:
            key = f"{cmd} | no-more"
            if key not in validated:
                validated[key] = f"Auto-discovered on {discovery.device} {discovery.timestamp[:10]}"
                changes.append(f"ADDED to show_commands_validated: {key}")
        recipe["show_commands_validated"] = validated

    content_str = json.dumps(recipe)
    if "tbd" in content_str.lower() or "TBD" in content_str:
        changes.append("WARNING: Recipe still contains TBD items (manual fix needed)")

    if changes and not dry_run:
        with open(recipe_path, "w") as f:
            json.dump(recipe, f, indent=2)
            f.write("\n")

    return changes


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def format_discovery_report(
    discovery: DiscoveryResult,
    reports: List[ValidationReport],
) -> str:
    """Format a human-readable report of discovery + validation."""
    lines = [
        "=" * 70,
        "DNOS CLI Discovery Report",
        "=" * 70,
        f"Device:   {discovery.device} ({discovery.device_ip})",
        f"Version:  {discovery.dnos_version}",
        f"Keywords: {', '.join(discovery.keywords)}",
        f"Time:     {discovery.timestamp}",
        "",
        f"Show commands discovered:      {len(discovery.show_commands)}",
        f"Clear commands discovered:     {len(discovery.clear_commands)}",
        f"Configure paths discovered:    {len(discovery.configure_paths)}",
        f"Internal commands discovered:  {len(discovery.internal_commands)}",
    ]

    if discovery.errors:
        lines.append(f"\nErrors: {len(discovery.errors)}")
        for e in discovery.errors:
            lines.append(f"  - {e}")

    if reports:
        lines.append("")
        lines.append("-" * 70)
        lines.append("Recipe Validation Results")
        lines.append("-" * 70)
        all_clean = True
        for r in reports:
            lines.append(r.summary_line())
            if not r.clean:
                all_clean = False
            if r.wrongly_marked_invalid:
                for w in r.wrongly_marked_invalid:
                    lines.append(f"    [WRONG INVALID] {w}")
            if r.invalid_in_recipe:
                for i in r.invalid_in_recipe:
                    lines.append(f"    [NOT FOUND ON DEVICE] {i}")
            if r.suggested_additions:
                for s in r.suggested_additions:
                    lines.append(f"    [SUGGEST ADD] {s}")
            if r.tbd_items:
                for t in r.tbd_items:
                    lines.append(f"    [TBD] {t}")

        lines.append("")
        lines.append(f"Overall: {'ALL CLEAN' if all_clean else 'FIXES NEEDED'}")

    lines.append("=" * 70)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="DNOS CLI Discovery & Recipe Validation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              # Full discovery + validation
              python3 dnos_cli_discovery.py --device RR-SA-2 --keywords evpn,bridge-domain \\
                  --catalog ~/SCALER/TEST/catalog/evpn_mac_mobility_SW204115

              # Discovery only, save JSON
              python3 dnos_cli_discovery.py --device PE-4 --keywords evpn --output-json /tmp/out.json

              # Offline validation (uses cached CLI completions)
              python3 dnos_cli_discovery.py --offline --catalog ~/SCALER/TEST/catalog/some_suite

              # Auto-fix recipes
              python3 dnos_cli_discovery.py --device RR-SA-2 --keywords evpn \\
                  --catalog ~/SCALER/TEST/catalog/evpn_mac_mobility_SW204115 --auto-fix
        """),
    )
    parser.add_argument("--device", help="Device hostname (resolved from SCALER DB)")
    parser.add_argument("--ip", help="Device management IP (overrides DB lookup)")
    parser.add_argument("--username", default="dnroot")
    parser.add_argument("--password", default="dnroot")
    parser.add_argument(
        "--keywords",
        help="Comma-separated search keywords (e.g., evpn,mac-mobility,bridge-domain)",
    )
    parser.add_argument("--catalog", help="Path to test catalog for recipe validation")
    parser.add_argument("--output-json", help="Save discovery results as JSON")
    parser.add_argument(
        "--update-completions",
        action="store_true",
        default=True,
        help="Update ~/.cursor/dnos-cli-completions.json (default: true)",
    )
    parser.add_argument("--no-update-completions", action="store_true")
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Auto-fix recipe issues (wrongly marked invalid, add suggested commands)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what auto-fix would do without writing",
    )
    parser.add_argument("--offline", action="store_true", help="Skip device connection")
    parser.add_argument("--quiet", action="store_true")

    args = parser.parse_args()

    if not args.offline and not args.device and not args.ip:
        parser.error("Need --device or --ip (or --offline for cached validation)")

    ip = args.ip
    device_name = args.device or "unknown"
    password = args.password

    if not args.offline:
        if not ip and args.device:
            resolved = _resolve_device(args.device)
            if resolved:
                device_name, ip, password = resolved
            else:
                parser.error(f"Device '{args.device}' not found in SCALER DB and no --ip given")

        if not ip:
            parser.error("No IP resolved for device")

        keywords = [k.strip() for k in (args.keywords or "").split(",") if k.strip()]
        if not keywords:
            parser.error("Need --keywords for device discovery")

        if not args.quiet:
            print(f"[*] Connecting to {device_name} ({ip})...")

        discovery = discover_device_cli(
            device_name, ip, keywords, args.username, password
        )

        if not args.quiet:
            print(f"[*] Discovered: {len(discovery.show_commands)} show, "
                  f"{len(discovery.clear_commands)} clear, "
                  f"{len(discovery.configure_paths)} config, "
                  f"{len(discovery.internal_commands)} internal")

        if args.output_json:
            with open(args.output_json, "w") as f:
                json.dump(discovery.to_dict(), f, indent=2)
            if not args.quiet:
                print(f"[*] Saved discovery JSON to {args.output_json}")

        if not args.no_update_completions and args.update_completions:
            feature_key = keywords[0] if keywords else "unknown"
            new, updated = update_cli_completions(discovery, feature_key)
            if not args.quiet:
                print(f"[*] CLI completions DB: {new} new sections, {updated} updated")
    else:
        discovery = DiscoveryResult(device=device_name, device_ip="offline")
        if _CLI_COMPLETIONS.is_file():
            with open(_CLI_COMPLETIONS) as f:
                db = json.load(f)
            for key, val in db.items():
                if isinstance(val, dict):
                    for sub_key, sub_val in val.items():
                        if isinstance(sub_val, list):
                            for cmd in sub_val:
                                if isinstance(cmd, str):
                                    if cmd.startswith("show dnos-internal"):
                                        discovery.internal_commands.append(cmd)
                                    elif cmd.startswith("show "):
                                        discovery.show_commands.append(cmd)
                                    elif cmd.startswith("clear "):
                                        discovery.clear_commands.append(cmd)

    reports: List[ValidationReport] = []
    if args.catalog:
        catalog_path = Path(args.catalog).expanduser()
        if not catalog_path.is_dir():
            print(f"[!] Catalog path not found: {catalog_path}", file=sys.stderr)
            return 1
        reports = validate_catalog(catalog_path, discovery)

        if args.auto_fix or args.dry_run:
            prefix = "[DRY RUN] " if args.dry_run else ""
            for r in reports:
                recipe_p = Path(r.recipe_path)
                changes = auto_fix_recipe(
                    recipe_p, discovery, r, dry_run=args.dry_run
                )
                if changes:
                    print(f"\n{prefix}Fixes for {r.recipe_id}:")
                    for c in changes:
                        print(f"  {c}")

    if not args.quiet:
        print()
        print(format_discovery_report(discovery, reports))

    return 0 if all(r.clean for r in reports) else 2


if __name__ == "__main__":
    sys.exit(main())
