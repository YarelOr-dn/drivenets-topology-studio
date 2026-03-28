#!/usr/bin/env python3
"""
Golden config baseline engine for DNOS test automation.

Snapshots the running config before a test, then diffs after to detect
config debris (leftover config from failed cleanup, unintended changes).

Works with any DNOS feature -- no hardcoded config paths.

Recipe JSON format:
    "config_baseline": {
        "sections": ["network-services evpn", "protocols bgp"],
        "full_config": true,
        "ignore_patterns": ["last-modified", "commit-id"]
    }
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

RunShowFn = Callable[[str, str], str]

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text) if isinstance(text, str) else str(text)


@dataclass
class ConfigSnapshot:
    """Config snapshot at a point in time."""
    label: str
    timestamp: str = ""
    sections: Dict[str, str] = field(default_factory=dict)
    full_config: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "timestamp": self.timestamp,
            "sections": {k: v[:500] + "..." if len(v) > 500 else v for k, v in self.sections.items()},
            "full_config_lines": len(self.full_config.splitlines()),
        }


@dataclass
class ConfigDiffItem:
    """One section's diff result."""
    section: str
    has_changes: bool
    added_lines: List[str] = field(default_factory=list)
    removed_lines: List[str] = field(default_factory=list)
    unified_diff: str = ""


@dataclass
class ConfigBaselineResult:
    """Full baseline comparison result."""
    before_label: str
    after_label: str
    diffs: List[ConfigDiffItem] = field(default_factory=list)
    debris_detected: bool = False
    debris_summary: str = ""

    @property
    def clean(self) -> bool:
        return not self.debris_detected

    def summary(self) -> str:
        if self.clean:
            return f"Config baseline CLEAN: no debris between {self.before_label} and {self.after_label}"
        parts = [f"Config baseline DEBRIS DETECTED ({self.before_label} -> {self.after_label}):"]
        for d in self.diffs:
            if d.has_changes:
                parts.append(f"  [{d.section}] +{len(d.added_lines)} -{len(d.removed_lines)} lines")
        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "before_label": self.before_label,
            "after_label": self.after_label,
            "clean": self.clean,
            "debris_detected": self.debris_detected,
            "debris_summary": self.debris_summary,
            "diffs": [
                {
                    "section": d.section,
                    "has_changes": d.has_changes,
                    "added_count": len(d.added_lines),
                    "removed_count": len(d.removed_lines),
                    "added_lines": d.added_lines[:20],
                    "removed_lines": d.removed_lines[:20],
                    "unified_diff": d.unified_diff[:2000],
                }
                for d in self.diffs
            ],
        }


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def snapshot_config(
    device: str,
    label: str,
    run_show: RunShowFn,
    sections: Optional[List[str]] = None,
    full_config: bool = True,
) -> ConfigSnapshot:
    """Take a config snapshot of specified sections and/or full running config."""
    snap = ConfigSnapshot(label=label, timestamp=_iso_now())

    if full_config:
        try:
            output = run_show(device, "show running-config | no-more")
            snap.full_config = _strip_ansi(output)
        except Exception:
            try:
                output = run_show(device, "show config | display flat | no-more")
                snap.full_config = _strip_ansi(output)
            except Exception:
                snap.full_config = ""

    if sections:
        for section in sections:
            cmd = f"show config {section} | no-more"
            try:
                output = run_show(device, cmd)
                snap.sections[section] = _strip_ansi(output)
            except Exception:
                snap.sections[section] = ""

    return snap


def diff_config(
    before: ConfigSnapshot,
    after: ConfigSnapshot,
    ignore_patterns: Optional[List[str]] = None,
) -> ConfigBaselineResult:
    """Compare two config snapshots and detect debris."""
    result = ConfigBaselineResult(
        before_label=before.label,
        after_label=after.label,
    )

    ignore_re = [re.compile(p, re.IGNORECASE) for p in (ignore_patterns or [])]

    # Compare each section
    all_sections = set(list(before.sections.keys()) + list(after.sections.keys()))
    for section in sorted(all_sections):
        before_text = before.sections.get(section, "")
        after_text = after.sections.get(section, "")
        diff_item = _diff_text(section, before_text, after_text, ignore_re)
        result.diffs.append(diff_item)

    # Compare full config if both have it
    if before.full_config and after.full_config:
        diff_item = _diff_text("full_config", before.full_config, after.full_config, ignore_re)
        result.diffs.append(diff_item)

    changed = [d for d in result.diffs if d.has_changes]
    if changed:
        result.debris_detected = True
        parts = []
        for d in changed:
            parts.append(f"{d.section}: +{len(d.added_lines)} -{len(d.removed_lines)}")
        result.debris_summary = "Changes in: " + ", ".join(parts)

    return result


def load_baseline_config(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """Load baseline configuration from recipe."""
    return recipe.get("config_baseline", {
        "sections": [],
        "full_config": True,
        "ignore_patterns": ["last-modified", "commit-id", "Commit performed"],
    })


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _diff_text(
    label: str,
    before: str,
    after: str,
    ignore_re: List[re.Pattern],
) -> ConfigDiffItem:
    """Diff two text blocks, ignoring lines matching ignore patterns."""
    before_lines = _filter_lines(before, ignore_re)
    after_lines = _filter_lines(after, ignore_re)

    diff = list(difflib.unified_diff(before_lines, after_lines, lineterm="",
                                     fromfile=f"{label} (before)", tofile=f"{label} (after)"))

    added = [l[1:] for l in diff if l.startswith("+") and not l.startswith("+++")]
    removed = [l[1:] for l in diff if l.startswith("-") and not l.startswith("---")]

    return ConfigDiffItem(
        section=label,
        has_changes=bool(added or removed),
        added_lines=added,
        removed_lines=removed,
        unified_diff="\n".join(diff),
    )


def _filter_lines(text: str, ignore_re: List[re.Pattern]) -> List[str]:
    """Split text into lines, filtering out ignored patterns and empty lines."""
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if any(p.search(stripped) for p in ignore_re):
            continue
        lines.append(line)
    return lines
