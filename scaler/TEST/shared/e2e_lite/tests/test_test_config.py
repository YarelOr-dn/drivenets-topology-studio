#!/usr/bin/env python3
"""Synthetic tests for test_config.py (TestConfiguration dataclass).

Run with:
    cd scaler/TEST/shared
    python3 -m e2e_lite.tests.test_test_config
"""
from __future__ import annotations

import json
import sys
import tempfile
import traceback
from pathlib import Path

_PARENT = Path(__file__).resolve().parent.parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from e2e_lite.base_validation import (  # noqa: E402
    BaseValidation,
    ShowCommandContains,
)
from e2e_lite.recovery_fsm_lite import RecoveryGuards, RecoveryFsmLite  # noqa: E402
from e2e_lite.test_config import (  # noqa: E402
    CLUSTER_REQUIREMENT_VALUES,
    TEST_MODE_VALUES,
    TestConfiguration,
    TestConfigurationError,
    cluster_requirement_matches,
    load_test_configuration,
    load_validation_spec,
    register_validation_type,
)


# ---------------------------------------------------------------------------
# Defaults & basic construction
# ---------------------------------------------------------------------------

def test_defaults_are_safe() -> None:
    cfg = TestConfiguration()
    assert cfg.test_mode == "dnos_mode"
    assert cfg.cluster_requirement == "any"
    assert cfg.test_id == ""
    assert cfg.additional_pre_validations == []
    assert cfg.snapshot_expected_changes == {}
    assert isinstance(cfg.fsm_guards, RecoveryGuards)


def test_invalid_test_mode_raises() -> None:
    try:
        TestConfiguration(test_mode="bogus")
    except TestConfigurationError as exc:
        assert "test_mode" in str(exc)
        return
    raise AssertionError("expected TestConfigurationError")


def test_invalid_cluster_requirement_raises() -> None:
    try:
        TestConfiguration(cluster_requirement="sa_maybe")
    except TestConfigurationError as exc:
        assert "cluster_requirement" in str(exc)
        return
    raise AssertionError("expected TestConfigurationError")


def test_literal_value_sets_are_exposed() -> None:
    assert "dnos_mode" in TEST_MODE_VALUES
    assert "baseos_mode" in TEST_MODE_VALUES
    assert set(CLUSTER_REQUIREMENT_VALUES) == {"sa_only", "cl_only", "any"}


# ---------------------------------------------------------------------------
# from_dict / from_recipe
# ---------------------------------------------------------------------------

def test_from_dict_none_returns_defaults() -> None:
    cfg = TestConfiguration.from_dict(None)
    assert cfg.test_mode == "dnos_mode"
    assert cfg.fsm_guards == RecoveryGuards()


def test_from_dict_empty_returns_defaults() -> None:
    cfg = TestConfiguration.from_dict({})
    assert cfg.test_id == ""


def test_from_dict_all_fields_populated() -> None:
    cfg = TestConfiguration.from_dict({
        "test_id": "TEST_ha_001",
        "test_mode": "dnos_mode",
        "cluster_requirement": "cl_only",
        "jira_component": "flowspec-vpn",
        "owner": "yarel.or",
        "additional_pre_validations": [
            {"type": "ShowCommandContains",
             "command": "show bgp summary",
             "substring": "Established",
             "device": "PE-4"},
        ],
        "snapshot_expected_changes": {
            "process_restart:routing:bgpd": "INCREASE_BY(1)",
            "new_core_dumps": "FORBIDDEN",
        },
        "fsm_guards": {
            "max_ssh_retries": 7,
            "max_scenario_retries": 3,
        },
    })
    assert cfg.test_id == "TEST_ha_001"
    assert cfg.owner == "yarel.or"
    assert cfg.cluster_requirement == "cl_only"
    assert len(cfg.additional_pre_validations) == 1
    assert isinstance(cfg.additional_pre_validations[0], ShowCommandContains)
    assert cfg.snapshot_expected_changes["new_core_dumps"] == "FORBIDDEN"
    assert cfg.fsm_guards.max_ssh_retries == 7
    assert cfg.fsm_guards.max_scenario_retries == 3
    # Untouched guard fields keep defaults
    assert cfg.fsm_guards.hard_timeout_sec == RecoveryGuards().hard_timeout_sec


def test_from_dict_unknown_field_raises() -> None:
    try:
        TestConfiguration.from_dict({"bogus_field": 42})
    except TestConfigurationError as exc:
        assert "bogus_field" in str(exc)
        return
    raise AssertionError("expected TestConfigurationError")


def test_from_dict_unknown_guard_raises() -> None:
    try:
        TestConfiguration.from_dict({"fsm_guards": {"unknown_guard": 5}})
    except TestConfigurationError as exc:
        assert "unknown_guard" in str(exc)
        return
    raise AssertionError("expected TestConfigurationError")


def test_from_dict_guards_can_be_recoveryguards_instance() -> None:
    g = RecoveryGuards(max_ssh_retries=9)
    cfg = TestConfiguration.from_dict({"fsm_guards": g})
    assert cfg.fsm_guards.max_ssh_retries == 9


def test_from_dict_invalid_validation_type_raises() -> None:
    try:
        TestConfiguration.from_dict({
            "additional_pre_validations": [{"type": "DoesNotExist"}],
        })
    except TestConfigurationError as exc:
        assert "DoesNotExist" in str(exc)
        return
    raise AssertionError("expected TestConfigurationError")


def test_from_dict_bad_validation_kwargs_raises() -> None:
    try:
        TestConfiguration.from_dict({
            "additional_pre_validations": [
                {"type": "ShowCommandContains", "not_a_real_arg": 1},
            ],
        })
    except TestConfigurationError as exc:
        assert "ShowCommandContains" in str(exc) or "not_a_real_arg" in str(exc)
        return
    raise AssertionError("expected TestConfigurationError")


def test_from_recipe_pulls_test_config_subkey() -> None:
    recipe = {
        "id": "TEST_foo",
        "test_config": {"test_id": "TEST_foo", "cluster_requirement": "sa_only"},
    }
    cfg = TestConfiguration.from_recipe(recipe)
    assert cfg.test_id == "TEST_foo"
    assert cfg.cluster_requirement == "sa_only"


def test_from_recipe_missing_block_returns_defaults() -> None:
    cfg = TestConfiguration.from_recipe({"id": "T"})
    assert cfg.test_id == ""
    assert cfg.test_mode == "dnos_mode"


def test_from_recipe_file_round_trip() -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump({
            "id": "TEST_smoke",
            "test_config": {
                "test_id": "TEST_smoke",
                "test_mode": "baseos_mode",
                "cluster_requirement": "any",
                "owner": "sut",
                "snapshot_expected_changes": {"alarm:any": "FORBIDDEN"},
            },
        }, tmp)
        path = tmp.name
    try:
        cfg = TestConfiguration.from_recipe_file(path)
        assert cfg.test_mode == "baseos_mode"
        assert cfg.snapshot_expected_changes == {"alarm:any": "FORBIDDEN"}
    finally:
        Path(path).unlink(missing_ok=True)


def test_from_recipe_file_missing_raises() -> None:
    try:
        TestConfiguration.from_recipe_file("/tmp/definitely-not-here.json")
    except TestConfigurationError:
        return
    raise AssertionError("expected TestConfigurationError")


# ---------------------------------------------------------------------------
# to_dict / to_json (round-trip)
# ---------------------------------------------------------------------------

def test_to_dict_round_trip_preserves_recipe_specs() -> None:
    raw = {
        "test_id": "T1",
        "cluster_requirement": "cl_only",
        "additional_pre_validations": [
            {"type": "ShowCommandContains",
             "command": "show version",
             "substring": "DNOS",
             "device": "PE-4",
             "name": "dnos_present"},
        ],
        "snapshot_expected_changes": {"new_core_dumps": "FORBIDDEN"},
        "fsm_guards": {"max_ssh_retries": 8},
    }
    cfg = TestConfiguration.from_dict(raw)
    out = cfg.to_dict()
    assert out["test_id"] == "T1"
    assert out["cluster_requirement"] == "cl_only"
    assert out["additional_pre_validations"] == raw["additional_pre_validations"]
    assert out["fsm_guards"]["max_ssh_retries"] == 8
    # Defaults for untouched guards must appear
    assert "hard_timeout_sec" in out["fsm_guards"]


def test_to_json_is_valid_and_parsable() -> None:
    cfg = TestConfiguration(test_id="T", owner="o")
    blob = cfg.to_json()
    parsed = json.loads(blob)
    assert parsed["test_id"] == "T"
    assert parsed["owner"] == "o"


def test_to_dict_programmatic_validations_fallback_serialises_best_effort() -> None:
    cfg = TestConfiguration(
        test_id="T",
        additional_pre_validations=[
            ShowCommandContains(
                command="show bgp summary",
                substring="Established",
                device="PE-4",
                name="bgp_up",
            ),
        ],
    )
    # No raw spec preserved (instance was built programmatically)
    out = cfg.to_dict()
    spec = out["additional_pre_validations"][0]
    assert spec["type"] == "ShowCommandContains"
    assert spec["command"] == "show bgp summary"
    assert spec["substring"] == "Established"
    assert spec["device"] == "PE-4"


# ---------------------------------------------------------------------------
# cluster_requirement_matches / matches_device
# ---------------------------------------------------------------------------

def test_cluster_requirement_any_accepts_everything() -> None:
    assert cluster_requirement_matches("any", "SA-36CD-S")
    assert cluster_requirement_matches("any", "CL-86")
    assert cluster_requirement_matches("any", "")


def test_cluster_requirement_sa_only_matches_sa() -> None:
    assert cluster_requirement_matches("sa_only", "SA-36CD-S")
    assert not cluster_requirement_matches("sa_only", "CL-86")


def test_cluster_requirement_cl_only_matches_cl() -> None:
    assert cluster_requirement_matches("cl_only", "CL-86")
    assert not cluster_requirement_matches("cl_only", "SA-36CD-S")


def test_cluster_requirement_unknown_raises() -> None:
    try:
        cluster_requirement_matches("bogus", "SA-36CD-S")
    except TestConfigurationError:
        return
    raise AssertionError("expected TestConfigurationError")


def test_matches_device_via_instance() -> None:
    sa_cfg = TestConfiguration(cluster_requirement="sa_only")
    cl_cfg = TestConfiguration(cluster_requirement="cl_only")
    any_cfg = TestConfiguration(cluster_requirement="any")
    assert sa_cfg.matches_device("SA-36CD-S")
    assert not sa_cfg.matches_device("CL-86")
    assert cl_cfg.matches_device("CL-86")
    assert any_cfg.matches_device("NCP-12")


# ---------------------------------------------------------------------------
# apply_guards_to
# ---------------------------------------------------------------------------

def test_apply_guards_to_real_fsm() -> None:
    fsm = RecoveryFsmLite()
    cfg = TestConfiguration(fsm_guards=RecoveryGuards(max_ssh_retries=42))
    cfg.apply_guards_to(fsm)
    assert fsm.guards.max_ssh_retries == 42


def test_apply_guards_to_none_is_noop() -> None:
    cfg = TestConfiguration()
    cfg.apply_guards_to(None)  # should not raise


def test_apply_guards_to_object_without_guards_is_noop() -> None:
    class Stub:
        pass
    cfg = TestConfiguration()
    cfg.apply_guards_to(Stub())  # must not raise


# ---------------------------------------------------------------------------
# load_validation_spec + register_validation_type
# ---------------------------------------------------------------------------

def test_load_validation_spec_builds_known_type() -> None:
    v = load_validation_spec({
        "type": "ShowCommandContains",
        "command": "show bgp",
        "substring": "Established",
        "device": "PE-4",
    })
    assert isinstance(v, ShowCommandContains)


def test_load_validation_spec_missing_type_raises() -> None:
    try:
        load_validation_spec({"command": "foo"})
    except TestConfigurationError:
        return
    raise AssertionError("expected TestConfigurationError")


def test_load_validation_spec_not_a_dict_raises() -> None:
    try:
        load_validation_spec(["ShowCommandContains", "foo"])  # type: ignore[arg-type]
    except TestConfigurationError:
        return
    raise AssertionError("expected TestConfigurationError")


def test_register_validation_type_enables_custom_spec() -> None:
    class MyCustomValidation(BaseValidation):
        should_connect_cli = False

        def __init__(self, *, tag: str = "x", **kwargs) -> None:
            super().__init__(**kwargs)
            self.tag = tag

        def _validate(self) -> bool:
            return True

    register_validation_type("MyCustomValidation", MyCustomValidation, overwrite=True)
    v = load_validation_spec({"type": "MyCustomValidation", "tag": "hello"})
    assert isinstance(v, MyCustomValidation)
    assert v.tag == "hello"


def test_register_validation_type_duplicate_without_overwrite_raises() -> None:
    try:
        register_validation_type("ShowCommandContains", ShowCommandContains)
    except TestConfigurationError:
        return
    raise AssertionError("expected TestConfigurationError (duplicate without overwrite)")


# ---------------------------------------------------------------------------
# load_test_configuration dispatcher
# ---------------------------------------------------------------------------

def test_load_from_none_defaults() -> None:
    cfg = load_test_configuration(None)
    assert cfg.test_mode == "dnos_mode"


def test_load_from_dict_with_test_config_subkey() -> None:
    cfg = load_test_configuration({
        "id": "T", "test_config": {"test_id": "abc"},
    })
    assert cfg.test_id == "abc"


def test_load_from_bare_dict() -> None:
    cfg = load_test_configuration({"test_id": "bare"})
    assert cfg.test_id == "bare"


def test_load_from_path() -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump({"test_config": {"test_id": "from_path"}}, tmp)
        path = tmp.name
    try:
        cfg = load_test_configuration(path)
        assert cfg.test_id == "from_path"
    finally:
        Path(path).unlink(missing_ok=True)


def test_load_from_unsupported_type_raises() -> None:
    try:
        load_test_configuration(42)  # type: ignore[arg-type]
    except TestConfigurationError:
        return
    raise AssertionError("expected TestConfigurationError")


# ---------------------------------------------------------------------------
# Summary line (smoke test)
# ---------------------------------------------------------------------------

def test_summary_contains_key_fields() -> None:
    cfg = TestConfiguration.from_dict({
        "test_id": "T1", "owner": "me", "cluster_requirement": "sa_only",
    })
    s = cfg.summary()
    assert "T1" in s
    assert "me" in s
    assert "sa_only" in s


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
