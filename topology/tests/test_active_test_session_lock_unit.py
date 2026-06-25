#!/usr/bin/env python3
"""Unit guards for the per-device /TEST active-session lock helper.

The helper itself lives at
``~/SCALER/TEST/_shared/lib/active_test_session_lock.py`` (outside this
repo); this test imports it by absolute path so it stays runnable as
``python3 <this-file>``.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

HELPER_PATH = Path(
    os.path.expanduser("~/SCALER/TEST/_shared/lib/active_test_session_lock.py")
)


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)
    print(f"ok: {msg}")


def _load_helper():
    spec = importlib.util.spec_from_file_location(
        "active_test_session_lock", HELPER_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load helper from {HELPER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh)


def test_lock_helper() -> None:
    _assert(HELPER_PATH.exists(), f"helper present at {HELPER_PATH}")
    lock = _load_helper()

    with tempfile.TemporaryDirectory() as tmp:
        scaler_test = Path(tmp)

        busy_pe4_payload = {
            "active": True,
            "test_id": "TEST_existing_pe4_run",
            "device": "PE-4",
            "phase": "setup",
            "started_at": "2026-05-05T09:14:22Z",
        }
        _write(scaler_test / "active_test_session_PE-4.json", busy_pe4_payload)

        busy, conflict = lock.is_device_busy(scaler_test, "PE-4")
        _assert(busy is True, "per-device file marks PE-4 busy")
        _assert(conflict is not None and conflict["test_id"] == "TEST_existing_pe4_run",
                "conflict payload exposes test_id of the running test")
        _assert(conflict["started_at"] == "2026-05-05T09:14:22Z",
                "conflict payload exposes started_at for caller's error message")

        busy_other, _ = lock.is_device_busy(scaler_test, "RR-SA-2")
        _assert(busy_other is False,
                "per-device file for PE-4 does NOT mark RR-SA-2 busy")

        rr_payload = {
            "active": True,
            "test_id": "TEST_rr_run",
            "device": "RR-SA-2",
            "phase": "execute",
        }
        target_path = lock.write_active_session(scaler_test, "RR-SA-2", rr_payload)
        _assert(target_path == scaler_test / "active_test_session_RR-SA-2.json",
                "write_active_session writes per-device file")
        _assert(target_path.exists(), "per-device file exists after write")

        for dev in ("PE-4", "RR-SA-2"):
            busy_n, conf_n = lock.is_device_busy(scaler_test, dev)
            _assert(busy_n is True, f"{dev} reports busy after both writes")
            _assert(conf_n is not None and conf_n["device"] == dev,
                    f"{dev} sees its own conflict payload, not the sibling's")

        finished = dict(rr_payload, active=False)
        lock.write_active_session(scaler_test, "RR-SA-2", finished)
        busy_after, _ = lock.is_device_busy(scaler_test, "RR-SA-2")
        _assert(busy_after is False,
                "RR-SA-2 no longer busy once active flips to false")
        busy_pe4_after, _ = lock.is_device_busy(scaler_test, "PE-4")
        _assert(busy_pe4_after is True,
                "PE-4 still busy after RR-SA-2 completes (independent locks)")

    with tempfile.TemporaryDirectory() as tmp:
        scaler_test = Path(tmp)
        legacy = {
            "active": True,
            "test_id": "TEST_legacy_pe4_run",
            "device": "PE-4",
            "phase": "execute",
        }
        _write(scaler_test / "active_test_session.json", legacy)

        busy_pe4, conflict = lock.is_device_busy(scaler_test, "PE-4")
        _assert(busy_pe4 is True,
                "legacy file with device=PE-4 still detects PE-4 conflict")
        _assert(conflict is not None and conflict["test_id"] == "TEST_legacy_pe4_run",
                "legacy fallback exposes the conflicting test_id")

        busy_rr, _ = lock.is_device_busy(scaler_test, "RR-SA-2")
        _assert(busy_rr is False,
                "legacy file for PE-4 does NOT spuriously mark RR-SA-2 busy")

        new_pe4 = {
            "active": True,
            "test_id": "TEST_new_pe4_run",
            "device": "PE-4",
            "phase": "setup",
        }
        lock.write_active_session(scaler_test, "PE-4", new_pe4)
        busy_pd, conf_pd = lock.is_device_busy(scaler_test, "PE-4")
        _assert(busy_pd is True, "per-device file present after write")
        _assert(conf_pd is not None and conf_pd["test_id"] == "TEST_new_pe4_run",
                "per-device file wins over legacy file when both exist")


if __name__ == "__main__":
    try:
        test_lock_helper()
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
    print("All active_test_session lock checks passed.")
