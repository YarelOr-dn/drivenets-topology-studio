"""DNOS Version Compatibility Module.

Reads the version knowledge base (db/dnos_version_compat.json) and provides:
  - Pre-upgrade compatibility reports (what config will be affected)
  - Data-driven config sanitization (replaces hardcoded patterns)
  - Version comparison utilities (is feature X available in version Y?)

The knowledge base is the single source of truth for all version-specific
behavior. When new incompatibilities are discovered, add them to the JSON
file -- the sanitizer and reports pick them up automatically.
"""

import json
import re
from pathlib import Path
from typing import Optional


_DB_PATH = Path(__file__).parent.parent / "db" / "dnos_version_compat.json"
_cached_db = None


def _load_db() -> dict:
    global _cached_db
    if _cached_db is not None:
        return _cached_db
    if not _DB_PATH.exists():
        return {"features": {}, "upgrade_warnings": {}, "collapsible_parents": {"keywords": []}}
    with open(_DB_PATH, "r") as f:
        _cached_db = json.load(f)
    return _cached_db


def reload_db():
    """Force-reload the knowledge base (useful after edits)."""
    global _cached_db
    _cached_db = None
    return _load_db()


def parse_version(version_str: str) -> tuple:
    """Parse '25.4.13.146' or '19.2.13.1' into (major, minor, patch) tuple."""
    if not version_str:
        return (0, 0, 0)
    parts = re.findall(r'\d+', version_str)
    if len(parts) >= 3:
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    elif len(parts) == 2:
        return (int(parts[0]), int(parts[1]), 0)
    elif len(parts) == 1:
        return (int(parts[0]), 0, 0)
    return (0, 0, 0)


def version_key(version_str: str) -> str:
    """Return 'major.minor' key for upgrade_warnings lookup."""
    v = parse_version(version_str)
    return f"{v[0]}.{v[1]}"


def is_feature_available(feature_id: str, target_version: str) -> bool:
    """Check if a feature (by knowledge base ID) is available in target_version."""
    db = _load_db()
    feat = db.get("features", {}).get(feature_id)
    if not feat:
        return True  # unknown feature = assume available
    added = parse_version(feat.get("added_in", "0.0"))
    target = parse_version(target_version)
    if target[0] == 0:
        return True  # unknown target = assume available
    return (target[0], target[1]) >= (added[0], added[1])


def get_incompatible_features(source_version: str, target_version: str) -> list:
    """Return list of features present in source but NOT in target.

    Each entry is a dict with: id, config_path, added_in, description, match_type.
    """
    db = _load_db()
    source = parse_version(source_version)
    target = parse_version(target_version)

    if source[0] == 0 or target[0] == 0:
        return []

    incompatible = []
    for feat_id, feat in db.get("features", {}).items():
        if feat.get("match_type") == "operational_only":
            continue
        added = parse_version(feat.get("added_in", "0.0"))
        # Feature is incompatible if: source has it (source >= added) but target doesn't (target < added)
        source_has = (source[0], source[1]) >= (added[0], added[1])
        target_has = (target[0], target[1]) >= (added[0], added[1])
        if source_has and not target_has:
            incompatible.append({
                "id": feat_id,
                "config_path": feat.get("config_path", ""),
                "added_in": feat.get("added_in", ""),
                "description": feat.get("description", ""),
                "match_type": feat.get("match_type", ""),
                "match_pattern": feat.get("match_pattern", ""),
                "portability_note": feat.get("portability_note", ""),
            })

    # Also check portability-flagged features on DOWNGRADES only.
    # Newer versions typically accept older config, but downgrading may hit
    # format changes even when both versions have the command.
    is_downgrade = (source[0], source[1]) > (target[0], target[1])
    if is_downgrade:
        for feat_id, feat in db.get("features", {}).items():
            if feat.get("match_type") == "operational_only":
                continue
            if feat.get("portability_note") and feat_id not in [f["id"] for f in incompatible]:
                added = parse_version(feat.get("added_in", "0.0"))
                source_has = (source[0], source[1]) >= (added[0], added[1])
                target_has = (target[0], target[1]) >= (added[0], added[1])
                if source_has and target_has and source[0] != target[0]:
                    incompatible.append({
                        "id": feat_id,
                        "config_path": feat.get("config_path", ""),
                        "added_in": feat.get("added_in", ""),
                        "description": feat.get("description", ""),
                        "match_type": feat.get("match_type", ""),
                        "match_pattern": feat.get("match_pattern", ""),
                        "portability_note": feat.get("portability_note", ""),
                    })

    return incompatible


def get_upgrade_warning(source_version: str, target_version: str) -> Optional[dict]:
    """Look up a pre-written upgrade warning for this version pair.

    Tries exact match first (e.g. '25.4 -> 19.2'), then wildcard (e.g. '26.x -> 25.x').
    """
    db = _load_db()
    warnings = db.get("upgrade_warnings", {})
    src_key = version_key(source_version)
    tgt_key = version_key(target_version)

    exact_key = f"{src_key} -> {tgt_key}"
    if exact_key in warnings:
        return warnings[exact_key]

    src_v = parse_version(source_version)
    tgt_v = parse_version(target_version)
    wildcard_key = f"{src_v[0]}.x -> {tgt_v[0]}.x"
    if wildcard_key in warnings:
        return warnings[wildcard_key]

    return None


def build_compatibility_report(source_version: str, target_version: str,
                               config_text: str = "") -> dict:
    """Build a full pre-upgrade compatibility report.

    Returns:
        {
            "source": "25.4.13.146",
            "target": "19.2.13.1",
            "is_downgrade": True,
            "severity": "high",
            "warning": "...",
            "incompatible_count": 15,
            "incompatible_features": [...],
            "config_lines_affected": 42,  # only if config_text provided
            "auto_sanitize": True,
            "recommendation": "..."
        }
    """
    src_v = parse_version(source_version)
    tgt_v = parse_version(target_version)
    is_downgrade = (src_v[0], src_v[1]) > (tgt_v[0], tgt_v[1])

    incompat = get_incompatible_features(source_version, target_version)
    warning_entry = get_upgrade_warning(source_version, target_version)

    severity = "low"
    if warning_entry:
        severity = warning_entry.get("severity", "medium")
    elif is_downgrade and len(incompat) > 5:
        severity = "high"
    elif is_downgrade:
        severity = "medium"

    warning_msg = ""
    auto_sanitize = False
    if warning_entry:
        warning_msg = warning_entry.get("warning_message", "")
        auto_sanitize = warning_entry.get("auto_sanitize", False)
    elif is_downgrade and incompat:
        warning_msg = (f"Downgrade from {source_version} to {target_version}: "
                       f"{len(incompat)} config features may be incompatible.")
        auto_sanitize = True

    lines_affected = 0
    if config_text and incompat:
        for line in config_text.split('\n'):
            for feat in incompat:
                pat = feat.get("match_pattern", "")
                if pat and re.match(pat, line):
                    lines_affected += 1
                    break

    recommendation = ""
    if not is_downgrade:
        recommendation = "Upgrade path: old config is accepted by new version. No sanitization needed."
    elif auto_sanitize:
        recommendation = ("Downgrade path: config will be automatically sanitized before restore. "
                          f"{len(incompat)} feature(s) will be stripped.")
    elif incompat:
        recommendation = ("Downgrade path: manual review recommended. Some config lines may fail on target version.")

    return {
        "source": source_version,
        "target": target_version,
        "is_downgrade": is_downgrade,
        "severity": severity,
        "warning": warning_msg,
        "incompatible_count": len(incompat),
        "incompatible_features": incompat,
        "config_lines_affected": lines_affected,
        "auto_sanitize": auto_sanitize,
        "recommendation": recommendation,
    }


def sanitize_config(config_text: str, source_version: str = "",
                    target_version: str = "") -> tuple:
    """Data-driven config sanitizer. Replaces the hardcoded sanitize_config_for_version().

    Reads incompatible features from the knowledge base and strips matching
    config lines/blocks. Falls back to the full feature list if versions
    are not provided (strips everything known to be version-specific).

    Returns: (cleaned_config: str, stripped_items: list[str])
    """
    db = _load_db()

    if source_version and target_version:
        incompat = get_incompatible_features(source_version, target_version)
    else:
        incompat = [
            {**feat, "id": fid}
            for fid, feat in db.get("features", {}).items()
            if feat.get("match_type") != "operational_only"
        ]

    single_line_removals = []
    block_removals = []
    for feat in incompat:
        pat = feat.get("match_pattern", "")
        if not pat:
            continue
        desc = feat.get("config_path", feat.get("id", "unknown"))
        if feat.get("match_type") == "block":
            block_removals.append((pat, desc))
        elif feat.get("match_type") == "single_line":
            single_line_removals.append((pat, desc))

    collapsible = set(db.get("collapsible_parents", {}).get("keywords", []))

    lines = config_text.split('\n')
    cleaned = []
    stripped = []
    skip_until_depth = -1

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped_line = line.rstrip()
        indent = len(line) - len(line.lstrip())

        if skip_until_depth >= 0:
            if stripped_line.strip() == '!' and indent <= skip_until_depth:
                skip_until_depth = -1
            i += 1
            continue

        single_matched = False
        for pattern, desc in single_line_removals:
            if re.match(pattern, line):
                stripped.append(desc)
                single_matched = True
                break
        if single_matched:
            i += 1
            continue

        block_matched = False
        for pattern, desc in block_removals:
            if re.match(pattern, line):
                stripped.append(f"[block] {desc}")
                skip_until_depth = indent
                block_matched = True
                break
        if block_matched:
            i += 1
            continue

        cleaned.append(stripped_line)
        i += 1

    changed = True
    while changed:
        changed = False
        result = []
        j = 0
        while j < len(cleaned):
            line = cleaned[j]
            keyword = line.strip()
            if (j + 1 < len(cleaned) and
                keyword in collapsible and
                cleaned[j + 1].strip() == '!'):
                indent_cur = len(line) - len(line.lstrip())
                indent_next = len(cleaned[j + 1]) - len(cleaned[j + 1].lstrip())
                if indent_next == indent_cur:
                    stripped.append(f"[empty] {keyword}")
                    j += 2
                    changed = True
                    continue
            result.append(line)
            j += 1
        cleaned = result

    return '\n'.join(cleaned), stripped


def format_report_for_terminal(report: dict) -> str:
    """Format a compatibility report as rich-compatible terminal text."""
    lines = []
    sev_color = {"high": "red", "medium": "yellow", "low": "green"}.get(report["severity"], "white")

    lines.append(f"[bold {sev_color}]Version Compatibility Report[/bold {sev_color}]")
    lines.append(f"  Source: [cyan]{report['source']}[/cyan]  →  Target: [cyan]{report['target']}[/cyan]")

    direction = "[red]DOWNGRADE[/red]" if report["is_downgrade"] else "[green]UPGRADE[/green]"
    lines.append(f"  Direction: {direction}  |  Severity: [{sev_color}]{report['severity'].upper()}[/{sev_color}]")

    if report.get("warning"):
        lines.append(f"\n  [dim]{report['warning']}[/dim]")

    if report["incompatible_count"] > 0:
        lines.append(f"\n  [bold]Incompatible features ({report['incompatible_count']}):[/bold]")
        for feat in report["incompatible_features"][:10]:
            added = feat.get("added_in", "?")
            path = feat.get("config_path", feat.get("id", ""))
            note = f" [dim]({feat['portability_note']})[/dim]" if feat.get("portability_note") else ""
            lines.append(f"    [{sev_color}]-[/{sev_color}] {path} [dim](added in {added})[/dim]{note}")
        if report["incompatible_count"] > 10:
            lines.append(f"    [dim]... and {report['incompatible_count'] - 10} more[/dim]")

    if report.get("config_lines_affected"):
        lines.append(f"\n  Config lines affected: ~{report['config_lines_affected']}")

    if report.get("auto_sanitize"):
        lines.append(f"\n  [green]Auto-sanitize: ENABLED[/green] -- incompatible lines will be stripped before config restore.")
    else:
        lines.append(f"\n  [dim]Auto-sanitize: not needed for this direction.[/dim]")

    if report.get("recommendation"):
        lines.append(f"\n  [bold]Recommendation:[/bold] {report['recommendation']}")

    return '\n'.join(lines)


def add_discovered_incompatibility(feature_id: str, config_path: str, added_in: str,
                                   description: str, match_type: str, match_pattern: str,
                                   discovered_via: str = "", portability_note: str = ""):
    """Add a newly discovered incompatibility to the knowledge base.

    Call this when a load override fails with an 'Unknown word' error for a command
    not yet in the DB. The knowledge base grows over time as more upgrades are performed.
    """
    db = _load_db()
    db["features"][feature_id] = {
        "added_in": added_in,
        "removed_in": None,
        "config_path": config_path,
        "config_hierarchy": config_path.split(" ")[:-1] if " " in config_path else [],
        "match_type": match_type,
        "match_pattern": match_pattern,
        "description": description,
        "discovered_via": discovered_via or f"Auto-discovered during upgrade on {__import__('time').strftime('%Y-%m-%d')}",
    }
    if portability_note:
        db["features"][feature_id]["portability_note"] = portability_note

    import time
    db["_updated"] = time.strftime("%Y-%m-%d")

    with open(_DB_PATH, "w") as f:
        json.dump(db, f, indent=2)

    global _cached_db
    _cached_db = db
