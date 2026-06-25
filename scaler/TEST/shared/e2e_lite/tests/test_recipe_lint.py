#!/usr/bin/env python3
"""Synthetic tests for recipe_lint.py -- schema v2 backward-compat gate."""
from __future__ import annotations

import json
import sys
import tempfile
import traceback
from pathlib import Path

_PARENT = Path(__file__).resolve().parent.parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from e2e_lite.recipe_lint import (  # noqa: E402
    CURRENT_SCHEMA_VERSION,
    LintReport,
    lint_catalog,
    lint_manifest,
    lint_recipe,
    main,
)


# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------

def _write(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _tmpdir() -> Path:
    d = Path(tempfile.mkdtemp(prefix="recipe_lint_test_"))
    return d


# ---------------------------------------------------------------------------
# Single-recipe linter
# ---------------------------------------------------------------------------

def test_v1_recipe_without_test_config_passes() -> None:
    d = _tmpdir()
    p = _write(d / "r.json", {
        "id": "TEST_a",
        "name": "...",
        "phases": [],
    })
    report = lint_recipe(p)
    assert report.ok(), [i.formatted() for i in report.issues]
    assert not report.warnings


def test_missing_file_reports_error() -> None:
    report = lint_recipe("/tmp/does-not-exist.json")
    assert not report.ok()
    assert any("not found" in i.message for i in report.errors)


def test_invalid_json_reports_error() -> None:
    d = _tmpdir()
    p = d / "r.json"
    p.write_text("not json at all {{{", encoding="utf-8")
    report = lint_recipe(p)
    assert not report.ok()
    assert any("invalid JSON" in i.message for i in report.errors)


def test_non_object_top_level_reports_error() -> None:
    d = _tmpdir()
    p = d / "r.json"
    p.write_text("[1, 2, 3]", encoding="utf-8")
    report = lint_recipe(p)
    assert not report.ok()
    assert any("object" in i.message for i in report.errors)


def test_missing_id_reports_error() -> None:
    d = _tmpdir()
    p = _write(d / "r.json", {"name": "no id here"})
    report = lint_recipe(p)
    assert not report.ok()
    assert any("'id'" in i.message for i in report.errors)


def test_v2_recipe_with_valid_test_config_passes() -> None:
    d = _tmpdir()
    p = _write(d / "r.json", {
        "id": "TEST_v2",
        "recipe_schema_version": 2,
        "test_config": {
            "test_id": "TEST_v2",
            "test_mode": "dnos_mode",
            "cluster_requirement": "any",
            "owner": "me",
            "fsm_guards": {"max_ssh_retries": 7},
        },
    })
    report = lint_recipe(p)
    assert report.ok(), [i.formatted() for i in report.issues]


def test_v2_recipe_with_bad_test_config_reports_error() -> None:
    d = _tmpdir()
    p = _write(d / "r.json", {
        "id": "TEST_v2",
        "recipe_schema_version": 2,
        "test_config": {"test_mode": "bogus_mode"},
    })
    report = lint_recipe(p)
    assert not report.ok()
    assert any("test_mode" in i.message for i in report.errors)


def test_v2_recipe_with_unknown_guard_reports_error() -> None:
    d = _tmpdir()
    p = _write(d / "r.json", {
        "id": "TEST_v2",
        "recipe_schema_version": 2,
        "test_config": {"fsm_guards": {"max_ssh_retries_xx": 5}},
    })
    report = lint_recipe(p)
    assert not report.ok()
    assert any("fsm_guards" in i.message for i in report.errors)


def test_recipe_with_test_config_but_no_version_warns() -> None:
    d = _tmpdir()
    p = _write(d / "r.json", {
        "id": "TEST_v2_no_version",
        "test_config": {"test_id": "TEST_v2_no_version"},
    })
    report = lint_recipe(p)
    assert report.ok()
    assert any("recipe_schema_version is not set" in i.message
               for i in report.warnings)


def test_version_newer_than_understood_reports_error() -> None:
    d = _tmpdir()
    p = _write(d / "r.json", {
        "id": "TEST_future",
        "recipe_schema_version": CURRENT_SCHEMA_VERSION + 5,
    })
    report = lint_recipe(p)
    assert not report.ok()
    assert any("newer than" in i.message for i in report.errors)


def test_version_zero_reports_error() -> None:
    d = _tmpdir()
    p = _write(d / "r.json", {"id": "x", "recipe_schema_version": 0})
    report = lint_recipe(p)
    assert not report.ok()


def test_version_wrong_type_reports_error() -> None:
    d = _tmpdir()
    p = _write(d / "r.json", {"id": "x", "recipe_schema_version": "two"})
    report = lint_recipe(p)
    assert not report.ok()
    assert any("integer" in i.message for i in report.errors)


def test_id_mismatch_between_top_and_test_config_warns() -> None:
    d = _tmpdir()
    p = _write(d / "r.json", {
        "id": "TEST_a",
        "recipe_schema_version": 2,
        "test_config": {"test_id": "TEST_b"},
    })
    report = lint_recipe(p)
    assert report.ok()
    assert any("does not match top-level" in i.message
               for i in report.warnings)


def test_test_config_required_via_flag_reports_error_when_missing() -> None:
    d = _tmpdir()
    p = _write(d / "r.json", {"id": "TEST_a", "recipe_schema_version": 2})
    report = lint_recipe(p, test_config_required=True)
    assert not report.ok()
    assert any("test_config_required" in i.message for i in report.errors)


# ---------------------------------------------------------------------------
# Manifest linter
# ---------------------------------------------------------------------------

def test_manifest_lints_referenced_recipes() -> None:
    d = _tmpdir()
    _write(d / "tests" / "a" / "recipe.json", {
        "id": "TEST_a", "recipe_schema_version": 2,
    })
    _write(d / "tests" / "b" / "recipe.json", {
        "id": "TEST_b", "recipe_schema_version": 2,
    })
    mp = _write(d / "suite_manifest.json", {
        "suite_id": "s",
        "recipe_schema_version": 2,
        "tests": [
            {"id": "TEST_a", "path": "tests/a/recipe.json"},
            {"id": "TEST_b", "path": "tests/b/recipe.json"},
        ],
    })
    report = lint_manifest(mp)
    assert report.ok(), [i.formatted() for i in report.issues]
    assert report.files_checked == 2


def test_manifest_missing_file_reports_error() -> None:
    report = lint_manifest("/tmp/definitely-not-here.json")
    assert not report.ok()


def test_manifest_invalid_json_reports_error() -> None:
    d = _tmpdir()
    mp = d / "suite_manifest.json"
    mp.write_text("{{{bad", encoding="utf-8")
    report = lint_manifest(mp)
    assert not report.ok()
    assert any("invalid JSON" in i.message for i in report.errors)


def test_manifest_enforces_test_config_required() -> None:
    d = _tmpdir()
    _write(d / "tests" / "a" / "recipe.json", {
        "id": "TEST_a", "recipe_schema_version": 2,
    })  # no test_config
    mp = _write(d / "suite_manifest.json", {
        "suite_id": "s",
        "recipe_schema_version": 2,
        "test_config_required": True,
        "tests": [{"id": "TEST_a", "path": "tests/a/recipe.json"}],
    })
    report = lint_manifest(mp)
    assert not report.ok()
    assert any("test_config_required" in i.message for i in report.errors)


def test_manifest_version_future_reports_error() -> None:
    d = _tmpdir()
    mp = _write(d / "suite_manifest.json", {
        "suite_id": "s",
        "recipe_schema_version": CURRENT_SCHEMA_VERSION + 10,
        "tests": [],
    })
    report = lint_manifest(mp)
    assert not report.ok()
    assert any("newer than" in i.message for i in report.errors)


def test_manifest_missing_tests_path_reports_error() -> None:
    d = _tmpdir()
    mp = _write(d / "suite_manifest.json", {
        "suite_id": "s",
        "tests": [{"id": "TEST_a"}],  # missing 'path'
    })
    report = lint_manifest(mp)
    assert not report.ok()
    assert any("missing 'path'" in i.message for i in report.errors)


# ---------------------------------------------------------------------------
# Catalog linter
# ---------------------------------------------------------------------------

def test_catalog_walks_all_manifests() -> None:
    d = _tmpdir()
    # Two suites, each with one recipe
    _write(d / "suite_a" / "tests" / "t1" / "recipe.json", {"id": "T1"})
    _write(d / "suite_a" / "suite_manifest.json", {
        "suite_id": "suite_a",
        "tests": [{"id": "T1", "path": "tests/t1/recipe.json"}],
    })
    _write(d / "suite_b" / "tests" / "t2" / "recipe.json", {"id": "T2"})
    _write(d / "suite_b" / "suite_manifest.json", {
        "suite_id": "suite_b",
        "tests": [{"id": "T2", "path": "tests/t2/recipe.json"}],
    })
    report = lint_catalog(d)
    assert report.ok(), [i.formatted() for i in report.issues]
    assert report.files_checked == 2


def test_catalog_empty_directory_warns() -> None:
    d = _tmpdir()
    report = lint_catalog(d)
    assert report.ok()
    assert any("no suite_manifest" in i.message.lower() for i in report.warnings)


def test_catalog_nonexistent_path_errors() -> None:
    report = lint_catalog("/tmp/no-such-catalog-xyz")
    assert not report.ok()


# ---------------------------------------------------------------------------
# Real repo catalog smoke test
# ---------------------------------------------------------------------------

def test_real_mac_mobility_suite_lints_clean() -> None:
    """Regression: the real mac-mobility suite must stay clean under v2."""
    repo_root = Path(__file__).resolve().parents[5]
    manifest = (
        repo_root / "scaler" / "TEST" / "catalog"
        / "evpn_mac_mobility_SW204115" / "suite_manifest.json"
    )
    if not manifest.exists():  # skip gracefully when run in a trimmed checkout
        return
    report = lint_manifest(manifest)
    assert report.ok(), [i.formatted() for i in report.issues]


# ---------------------------------------------------------------------------
# CLI dispatch
# ---------------------------------------------------------------------------

def test_cli_lints_single_recipe_via_argv() -> None:
    d = _tmpdir()
    p = _write(d / "r.json", {"id": "T", "recipe_schema_version": 2})
    rc = main([str(p)])
    assert rc == 0


def test_cli_nonzero_when_errors() -> None:
    d = _tmpdir()
    p = _write(d / "r.json", {"id": "T", "recipe_schema_version": "bad"})
    rc = main([str(p)])
    assert rc == 1


def test_cli_json_emit_valid_structure(capsys=None) -> None:
    d = _tmpdir()
    p = _write(d / "r.json", {"id": "T", "recipe_schema_version": 2})
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = main([str(p), "--json"])
    assert rc == 0
    parsed = json.loads(buf.getvalue())
    assert "files_checked" in parsed
    assert "errors" in parsed
    assert "warnings" in parsed


# ---------------------------------------------------------------------------
# LintReport ergonomics
# ---------------------------------------------------------------------------

def test_lint_report_aggregates() -> None:
    a = LintReport()
    a.add(Path("a"), "error", "boom")
    b = LintReport()
    b.add(Path("b"), "warning", "meh")
    b.files_checked = 3
    a.extend(b)
    assert len(a.errors) == 1
    assert len(a.warnings) == 1
    assert a.files_checked == 3
    assert not a.ok()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _discover() -> list:
    g = globals()
    return sorted(
        (name, fn) for name, fn in g.items()
        if name.startswith("test_") and callable(fn)
    )


def run_all() -> int:
    tests = _discover()
    passed = failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"[PASS] {name}")
            passed += 1
        except Exception:
            print(f"[FAIL] {name}")
            traceback.print_exc()
            failed += 1
    print(f"\nTotal: {len(tests)}  Passed: {passed}  Failed: {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all())
