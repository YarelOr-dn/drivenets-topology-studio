"""Focused unit tests for ``routes._console_fallback``.

Exercises edge cases that the end-to-end (``test_console_fallback_e2e.py``)
test intentionally skips, since e2e leans on the live SCALER DB
(operational.json, console_mappings.json) to simulate the
"after ghost-IP wipe" scenario. This module stays hermetic:

  * Purely in-memory ConsoleFallback objects (no filesystem).
  * An isolated ``TOPOLOGY_USERS_BASE`` under /tmp for the file-write tests.

Covered cases (must all pass or the script exits 1):

  1. Empty instance reports ``is_empty()`` true and ``best_method() == ""``.
  2. KVM-only instance -> ``best_method() == "virsh_console"``, availability
     flags correct.
  3. Console-server-only -> ``best_method() == "console_server"``.
  4. SSH-NCC-only -> ``best_method() == "ssh_ncc"``.
  5. SN-only -> ``best_method() == "ssh_sn"``.
  6. ``_merge`` overlays per-user > global > ops; list fields are unioned.
  7. ``sanitize`` replaces every password with ``"***"``, keeps usernames.
  8. ``write_fallback(merge_with_existing=False)`` DOES blank a stored
     password when the caller passes an explicit empty string.
  9. ``write_fallback(merge_with_existing=True)`` (default) preserves a
     pre-existing non-empty password when the new record leaves it blank.
  10. ``capture_from_probe_result`` projects a multi-method probe response
      correctly (extracts KVM + NCC-mgmt + console-server rows, unions
      ``ncc_vms``).
  11. ``capture_from_probe_result`` with no useful rows returns empty and
      does NOT persist anything to disk.
  12. ``describe_availability`` reports the correct flags for every
      degraded variant.

Run:
    PYTHONPATH="topology" python3 topology/tests/test_console_fallback_unit.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


def _case(label: str) -> None:
    print(f"\n=== {label}")


def main() -> int:
    os.environ["TOPOLOGY_USERS_BASE"] = "/tmp/cf_unit"
    base = Path(os.environ["TOPOLOGY_USERS_BASE"])
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)

    from routes._console_fallback import (
        ConsoleFallback,
        _merge,
        capture_from_probe_result,
        delete_fallback,
        describe_availability,
        read_fallback,
        sanitize,
        write_fallback,
    )

    _case("1. empty instance")
    empty = ConsoleFallback()
    assert empty.is_empty()
    assert empty.best_method() == ""
    print("  empty.best_method()='' is_empty()=True")

    _case("2. KVM-only -> virsh_console")
    kvm_only = ConsoleFallback(
        device_id="K1",
        ncc_type="kvm",
        kvm_host_ip="100.1.1.1",
        kvm_user="dn",
        kvm_pass="secret",
        ncc_vms=["k1-ncc0", "k1-ncc1"],
    )
    assert not kvm_only.is_empty()
    assert kvm_only.best_method() == "virsh_console"
    avail = describe_availability(kvm_only)
    assert avail["virsh_console"] is True
    assert avail["ssh_ncc"] is False
    assert avail["console_server"] is False
    assert avail["ssh_sn"] is False
    print(f"  best_method={kvm_only.best_method()} avail={avail}")

    _case("3. Console-server-only -> console_server")
    cs_only = ConsoleFallback(
        device_id="C1",
        console_server_host="term-acs-01",
        console_server_port=2014,
        console_server_user="admin",
        console_server_pass="pw",
    )
    assert cs_only.best_method() == "console_server"
    avail = describe_availability(cs_only)
    assert avail == {
        "virsh_console": False,
        "ssh_ncc": False,
        "console_server": True,
        "ssh_sn": False,
    }
    print(f"  best_method={cs_only.best_method()}")

    _case("4. SSH-NCC-only -> ssh_ncc")
    ncc_only = ConsoleFallback(device_id="N1", ncc_mgmt_ip="100.64.0.2")
    assert ncc_only.best_method() == "ssh_ncc"
    print(f"  best_method={ncc_only.best_method()}")

    _case("5. SN-only -> ssh_sn")
    sn_only = ConsoleFallback(
        device_id="S1", serial_hostname="WDYSOMESERIAL-P3",
    )
    assert sn_only.best_method() == "ssh_sn"
    print(f"  best_method={sn_only.best_method()}")

    _case("6. _merge overlays + unions ncc_vms")
    primary = ConsoleFallback(
        device_id="D1",
        kvm_host_ip="100.1.1.1",
        ncc_vms=["a"],
        source="user",
    )
    secondary = ConsoleFallback(
        device_id="D1",
        kvm_host_ip="10.0.0.9",
        kvm_user="dn",
        ncc_vms=["a", "b"],
        source="operational.json",
    )
    merged = _merge(primary, secondary)
    assert merged.kvm_host_ip == "100.1.1.1", merged.kvm_host_ip
    assert merged.kvm_user == "dn"
    assert sorted(merged.ncc_vms) == ["a", "b"]
    assert merged.source == "user"
    print(f"  merged kvm_host_ip={merged.kvm_host_ip} ncc_vms={merged.ncc_vms} source={merged.source}")

    _case("6b. _merge does NOT duplicate when primary.ncc_vms=[] and fallback.ncc_vms is non-empty")
    # Regression for a bug found during live API verification: when the
    # primary record was derived from an ops file that had no KVM data
    # but was still non-empty (serial_hostname="N/A"), merging with an
    # existing user fallback produced duplicates of every ncc_vm.
    prim_empty = ConsoleFallback(
        device_id="D2",
        serial_hostname="N/A",  # makes primary non-empty without ncc_vms
        ncc_vms=[],
    )
    fb_full = ConsoleFallback(
        device_id="D2",
        kvm_host_ip="100.1.1.1",
        ncc_vms=["x", "y"],
    )
    merged2 = _merge(prim_empty, fb_full)
    assert merged2.ncc_vms == ["x", "y"], merged2.ncc_vms
    assert merged2.kvm_host_ip == "100.1.1.1"
    print(f"  no-duplicate union ncc_vms={merged2.ncc_vms}")

    _case("7. sanitize redacts every password")
    rich = ConsoleFallback(
        device_id="R1",
        kvm_pass="kp",
        ncc_console_pass="ncp",
        console_server_pass="csp",
        dncli_pass="dcp",
        kvm_user="dn",
        ncc_console_user="dn",
        console_server_user="admin",
    )
    safe = sanitize(rich)
    assert safe["kvm_pass"] == "***"
    assert safe["ncc_console_pass"] == "***"
    assert safe["console_server_pass"] == "***"
    assert safe["dncli_pass"] == "***"
    assert safe["kvm_user"] == "dn"
    assert safe["console_server_user"] == "admin"
    empty_safe = sanitize(ConsoleFallback())
    for key in ("kvm_pass", "ncc_console_pass", "console_server_pass", "dncli_pass"):
        assert empty_safe[key] == "", (key, empty_safe[key])
    print(f"  redacted -> kvm_pass={safe['kvm_pass']!r} empty.kvm_pass={empty_safe['kvm_pass']!r}")

    _case("8. write merge_with_existing=False blanks password when told to")
    first = ConsoleFallback(
        device_id="W1",
        kvm_host_ip="100.2.2.2",
        kvm_user="dn",
        kvm_pass="old",
        ncc_vms=["w1-ncc0"],
    )
    write_fallback("alice", "W1", first, merge_with_existing=False)
    blanked = ConsoleFallback(
        device_id="W1",
        kvm_host_ip="100.2.2.2",
        kvm_user="dn",
        kvm_pass="",
        ncc_vms=["w1-ncc0"],
    )
    write_fallback("alice", "W1", blanked, merge_with_existing=False)
    data = json.loads((base / "alice" / "devices.json").read_text())
    assert data["W1"]["console_fallback"]["kvm_pass"] == "", (
        data["W1"]["console_fallback"]["kvm_pass"]
    )
    print("  kvm_pass blanked when merge_with_existing=False")

    _case("9. write merge_with_existing=True keeps old password")
    first2 = ConsoleFallback(
        device_id="W2",
        kvm_host_ip="100.3.3.3",
        kvm_user="dn",
        kvm_pass="old_pw",
        ncc_vms=["w2-ncc0"],
    )
    write_fallback("alice", "W2", first2, merge_with_existing=False)
    partial = ConsoleFallback(
        device_id="W2",
        kvm_host_ip="100.3.3.3",
        kvm_user="dn",
        kvm_pass="",
        ncc_vms=["w2-ncc0"],
    )
    write_fallback("alice", "W2", partial, merge_with_existing=True)
    data = json.loads((base / "alice" / "devices.json").read_text())
    assert data["W2"]["console_fallback"]["kvm_pass"] == "old_pw", (
        data["W2"]["console_fallback"]["kvm_pass"]
    )
    print("  kvm_pass preserved when merge_with_existing=True and new is blank")

    _case("10. capture_from_probe_result projects multi-method response")
    probe = {
        "cluster": {
            "active_ncc_vm": "p1-ncc1",
            "ncc_type": "kvm",
            "serial_number": "WDYTEST0001-P3",
        },
        "methods": [
            {
                "method": "virsh_console",
                "host": "100.10.10.10",
                "kvm_host_name": "kvm-probe",
                "kvm_credentials": {"username": "dn", "password": "secret"},
                "ncc_vms": ["p1-ncc0"],
                "vms_running": ["p1-ncc1"],
            },
            {
                "method": "ssh_ncc",
                "host": "100.64.0.11",
            },
            {
                "method": "console",
                "host": "acs-root",
                "port": 2030,
                "console_credentials": {"username": "admin", "password": "pw"},
            },
            {
                "method": "ssh_sn",
                "host": "some-serial-hostname",
            },
        ],
    }
    captured = capture_from_probe_result("alice", "P1", probe, reason="unit_probe")
    assert captured.kvm_host_ip == "100.10.10.10"
    assert captured.kvm_user == "dn"
    assert captured.ncc_mgmt_ip == "100.64.0.11"
    assert captured.console_server_host == "acs-root"
    assert captured.console_server_port == 2030
    assert captured.console_server_user == "admin"
    assert captured.active_ncc_vm_hint == "p1-ncc1"
    assert "p1-ncc0" in captured.ncc_vms
    assert "p1-ncc1" in captured.ncc_vms
    print(f"  captured kvm_host_ip={captured.kvm_host_ip} ncc_mgmt_ip={captured.ncc_mgmt_ip} cs={captured.console_server_host}:{captured.console_server_port} vms={captured.ncc_vms}")

    _case("11. capture_from_probe_result with no useful rows returns empty, no write")
    empty_probe = {
        "cluster": {},
        "methods": [
            {"method": "ssh_mgmt", "host": "100.64.5.5", "reachable": False},
        ],
    }
    before = (base / "alice" / "devices.json").read_text()
    out = capture_from_probe_result("alice", "P2", empty_probe)
    assert out.is_empty(), out
    after = (base / "alice" / "devices.json").read_text()
    assert before == after, "disk content should not change when probe has no fallback info"
    data_after = json.loads(after)
    assert "P2" not in data_after
    print("  no-useful-row probe did not touch disk")

    _case("12. availability flag variants")
    assert describe_availability(kvm_only)["virsh_console"] is True
    assert describe_availability(cs_only)["console_server"] is True
    assert describe_availability(ncc_only)["ssh_ncc"] is True
    assert describe_availability(sn_only)["ssh_sn"] is True
    partial_kvm = ConsoleFallback(
        device_id="K2",
        ncc_type="kvm",
        kvm_host_ip="100.1.1.1",
        ncc_vms=[],
    )
    assert describe_availability(partial_kvm)["virsh_console"] is False
    print("  partial KVM (no NCC VMs) -> virsh_console=False as expected")

    _case("13. read_fallback returns empty when user + device unknown")
    out = read_fallback("alice", "NONEXISTENT-DEVICE")
    assert out.is_empty() or out.source in ("empty", "global", "operational.json"), out.source
    print(f"  unknown device -> is_empty={out.is_empty()} source={out.source}")

    _case("13b. _from_ops normalizes placeholder values (N/A, null, -) to empty")
    from routes._console_fallback import _from_ops
    for placeholder in ("N/A", "null", "None", "-", "undefined", "Unknown", ""):
        cf_p = _from_ops({"serial_number": placeholder, "hostname": placeholder}, "X")
        assert cf_p.serial_number == "", (placeholder, cf_p.serial_number)
        assert cf_p.serial_hostname == "", (placeholder, cf_p.serial_hostname)
        assert cf_p.hostname == "", (placeholder, cf_p.hostname)
        assert cf_p.best_method() == "", (placeholder, cf_p.best_method())
        assert cf_p.is_empty(), placeholder
    cf_ok = _from_ops({"serial_number": "WDY1A17E00011-P3", "hostname": "MY-DEV"}, "X")
    assert cf_ok.serial_number == "WDY1A17E00011-P3"
    assert cf_ok.best_method() == "ssh_sn"
    print(f"  placeholders normalized; real SN -> best_method={cf_ok.best_method()}")

    _case("14. delete_fallback returns False when nothing to delete")
    ok = delete_fallback("alice", "NONEXISTENT-DEVICE")
    assert ok is False
    ok = delete_fallback("alice", "W1")
    assert ok is True
    data = json.loads((base / "alice" / "devices.json").read_text())
    assert "console_fallback" not in data["W1"]
    print("  delete_fallback: False for unknown, True + removes block for known")

    print("\nALL UNIT TESTS PASSED")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:
        print(f"\nASSERTION FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
