#!/usr/bin/env python3
"""
recipe_lint -- schema-level linter for /TEST recipe.json files.

Enforces the backward-compatible v1 <-> v2 contract documented in
``RECIPE_SCHEMA.md``:

* v1 recipes MUST still load (no ``test_config`` block required).
* v2 recipes declare ``recipe_schema_version: 2`` at the top level.
* When ``test_config`` is present, it MUST deserialise cleanly through
  ``TestConfiguration.from_recipe()``; any error surfaces with the file
  path prefixed so CI can pinpoint the broken recipe.
* Suite manifests MAY declare ``test_config_required: true`` -- in that
  case every recipe listed under ``tests[*].path`` MUST carry the block.
* Forward-incompat gate: a recipe whose ``recipe_schema_version`` exceeds
  the version understood by this module is rejected with a clear message.

Usage:

    # Lint a single recipe file
    python3 -m e2e_lite.recipe_lint path/to/recipe.json

    # Lint a whole suite by manifest path
    python3 -m e2e_lite.recipe_lint --manifest path/to/suite_manifest.json

    # Scan the whole TEST catalog
    python3 -m e2e_lite.recipe_lint --catalog scaler/TEST/catalog

Exit codes: 0 = clean, 1 = at least one error, 2 = bad CLI usage.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence

from .test_config import TestConfiguration, TestConfigurationError

CURRENT_SCHEMA_VERSION = 2
"""The highest recipe_schema_version this build understands."""

__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "LintIssue",
    "LintReport",
    "lint_manifest",
    "lint_recipe",
    "lint_catalog",
    "main",
]


# ---------------------------------------------------------------------------
# Report dataclasses
# ---------------------------------------------------------------------------

@dataclass
class LintIssue:
    """One lint finding."""
    path: Path
    severity: str  # "error" | "warning"
    message: str

    def formatted(self) -> str:
        tag = self.severity.upper()
        return f"[{tag}] {self.path}: {self.message}"


@dataclass
class LintReport:
    issues: List[LintIssue] = field(default_factory=list)
    files_checked: int = 0

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def add(self, path: Path, severity: str, message: str) -> None:
        self.issues.append(LintIssue(path=path, severity=severity, message=message))

    def ok(self) -> bool:
        return not self.errors

    def extend(self, other: "LintReport") -> None:
        self.issues.extend(other.issues)
        self.files_checked += other.files_checked


# ---------------------------------------------------------------------------
# Single-recipe linter
# ---------------------------------------------------------------------------

def lint_recipe(
    path: Path | str,
    *,
    test_config_required: bool = False,
    report: Optional[LintReport] = None,
) -> LintReport:
    """Lint a single recipe file. Returns a :class:`LintReport`."""
    report = report or LintReport()
    p = Path(path)
    report.files_checked += 1

    if not p.exists():
        report.add(p, "error", "recipe file not found")
        return report

    try:
        raw = p.read_text(encoding="utf-8")
    except OSError as exc:
        report.add(p, "error", f"could not read file: {exc}")
        return report

    try:
        recipe = json.loads(raw)
    except json.JSONDecodeError as exc:
        report.add(p, "error", f"invalid JSON: {exc}")
        return report

    if not isinstance(recipe, dict):
        report.add(p, "error", "top-level JSON value must be an object")
        return report

    # Version gate (forward-incompat)
    version = recipe.get("recipe_schema_version")
    if version is None:
        # v1: nothing to enforce on the schema side. If v2 fields slipped in
        # without a version bump, warn so owners explicit-bump.
        if "test_config" in recipe:
            report.add(
                p, "warning",
                "recipe uses v2 field 'test_config' but recipe_schema_version "
                "is not set (recommended: bump to 2)",
            )
    elif not isinstance(version, int):
        report.add(
            p, "error",
            f"recipe_schema_version must be an integer, got {type(version).__name__}",
        )
    elif version < 1:
        report.add(
            p, "error", f"recipe_schema_version must be >= 1, got {version}",
        )
    elif version > CURRENT_SCHEMA_VERSION:
        report.add(
            p, "error",
            f"recipe_schema_version={version} is newer than this linter "
            f"understands ({CURRENT_SCHEMA_VERSION}); upgrade e2e_lite",
        )

    # Required identity fields (common to v1 + v2)
    for required in ("id",):
        if required not in recipe or not recipe[required]:
            report.add(p, "error", f"missing required top-level field '{required}'")

    # test_config gating
    has_block = "test_config" in recipe
    if test_config_required and not has_block:
        report.add(
            p, "error",
            "suite manifest sets test_config_required=true but recipe has no "
            "'test_config' block",
        )

    if has_block:
        try:
            cfg = TestConfiguration.from_recipe(recipe)
        except TestConfigurationError as exc:
            report.add(p, "error", f"test_config: {exc}")
            return report

        # ID consistency warning -- easy to miss, never a hard error.
        if cfg.test_id and recipe.get("id") and cfg.test_id != recipe["id"]:
            report.add(
                p, "warning",
                f"test_config.test_id ({cfg.test_id!r}) does not match top-level "
                f"id ({recipe['id']!r})",
            )

    return report


# ---------------------------------------------------------------------------
# Manifest linter (recipe_schema_version + test_config_required enforcement)
# ---------------------------------------------------------------------------

def lint_manifest(
    manifest_path: Path | str,
    *,
    report: Optional[LintReport] = None,
) -> LintReport:
    """Lint a suite_manifest.json and every recipe it references."""
    report = report or LintReport()
    mp = Path(manifest_path)

    if not mp.exists():
        report.add(mp, "error", "manifest file not found")
        return report
    try:
        manifest = json.loads(mp.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.add(mp, "error", f"invalid JSON: {exc}")
        return report

    if not isinstance(manifest, dict):
        report.add(mp, "error", "top-level JSON value must be an object")
        return report

    suite_version = manifest.get("recipe_schema_version")
    if suite_version is not None:
        if not isinstance(suite_version, int) or suite_version < 1:
            report.add(
                mp, "error",
                f"recipe_schema_version must be a positive integer, "
                f"got {suite_version!r}",
            )
        elif suite_version > CURRENT_SCHEMA_VERSION:
            report.add(
                mp, "error",
                f"manifest recipe_schema_version={suite_version} is newer than "
                f"this linter understands ({CURRENT_SCHEMA_VERSION})",
            )

    test_config_required = bool(manifest.get("test_config_required", False))

    tests = manifest.get("tests", [])
    if not isinstance(tests, list):
        report.add(mp, "error", "'tests' field must be a list")
        return report

    suite_dir = mp.parent
    for i, entry in enumerate(tests):
        if not isinstance(entry, dict):
            report.add(mp, "error", f"tests[{i}] must be an object")
            continue
        rel = entry.get("path")
        if not rel:
            report.add(mp, "error", f"tests[{i}] missing 'path' field")
            continue
        recipe_path = (suite_dir / rel).resolve()
        lint_recipe(
            recipe_path,
            test_config_required=test_config_required,
            report=report,
        )

    return report


# ---------------------------------------------------------------------------
# Catalog linter (walks a directory for suite_manifest.json files)
# ---------------------------------------------------------------------------

def lint_catalog(
    catalog_path: Path | str,
    *,
    report: Optional[LintReport] = None,
) -> LintReport:
    """Walk ``catalog_path`` and lint every suite it contains."""
    report = report or LintReport()
    cp = Path(catalog_path)

    if not cp.exists() or not cp.is_dir():
        report.add(cp, "error", "catalog path does not exist or is not a directory")
        return report

    manifests = sorted(cp.glob("*/suite_manifest.json"))
    if not manifests:
        report.add(cp, "warning", "no suite_manifest.json files found under catalog")
        return report

    for manifest in manifests:
        lint_manifest(manifest, report=report)

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="recipe_lint",
        description=(
            "Lint /TEST recipes against schema v2 "
            "(backward-compatible with v1)."
        ),
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "recipes", nargs="*", default=[], help="recipe.json files to lint"
    )
    group.add_argument(
        "--manifest", type=str,
        help="lint a suite_manifest.json and all recipes it references",
    )
    group.add_argument(
        "--catalog", type=str,
        help="walk a catalog directory and lint every suite",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="emit machine-readable JSON report instead of text",
    )
    return parser


def _emit_text(report: LintReport) -> None:
    for issue in report.issues:
        print(issue.formatted())
    summary = (
        f"Checked {report.files_checked} file(s): "
        f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)."
    )
    print(summary)


def _emit_json(report: LintReport) -> None:
    payload = {
        "files_checked": report.files_checked,
        "errors": [
            {"path": str(i.path), "message": i.message}
            for i in report.errors
        ],
        "warnings": [
            {"path": str(i.path), "message": i.message}
            for i in report.warnings
        ],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    report = LintReport()
    if args.manifest:
        lint_manifest(args.manifest, report=report)
    elif args.catalog:
        lint_catalog(args.catalog, report=report)
    else:
        recipes = args.recipes or []
        if not recipes:
            parser.error("no recipe files provided")
        for r in recipes:
            lint_recipe(r, report=report)

    if args.json:
        _emit_json(report)
    else:
        _emit_text(report)

    return 0 if report.ok() else 1


if __name__ == "__main__":
    sys.exit(main())
