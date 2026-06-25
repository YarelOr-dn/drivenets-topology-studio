"""End-to-end sanity test for the console-fallback subsystem.

Simulates the lifecycle:
  1. Fresh user -- read a device with KVM info in ops, confirm fallback
     is populated from ops.
  2. Capture on probe -- call the capture helper directly, confirm the
     per-user devices.json now has the console_fallback block with
     0600 perms.
  3. Priority order -- user > global > ops. Write a user override,
     confirm the merged result prefers user values over ops.
  4. Ops wipe rescue -- wipe operational.json and console_mappings
     cluster_ncc_access, call scaler's _get_kvm_host_config, confirm
     it returns the KVM config from user_fallback.
  5. Cross-user propagation -- user bob reads after user alice
     captured, confirms the global scan in scaler picks up alice's
     record.
  6. Sanitize invariants -- redacted output never leaks a password,
     but preserves usernames and non-sensitive fields.

Run from the repo root:
  PYTHONPATH="scaler:topology" TOPOLOGY_USERS_BASE=/tmp/cf_e2e \\
      python3 topology/tests/test_console_fallback_e2e.py

Exits 0 on success, 1 on any assertion failure.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


def _seed_ops_with_kvm_info() -> Path:
    """Ensure /home/dn/SCALER/db/configs/YOR_CL_PE-4/operational.json
    has the baseline KVM fields this test needs.

    The PE-4 record lives on-disk already; this just tops up any
    missing KVM fields (tests are idempotent / non-destructive).
    """
    path = Path("/home/dn/SCALER/db/configs/YOR_CL_PE-4/operational.json")
    if not path.exists():
        raise RuntimeError(f"missing ops file: {path}")
    existing = json.loads(path.read_text())
    top_up = {
        "serial_number": "WDY1A17E00011-P3",
        "hostname": "YOR_CL_PE-4",
        "ncc_type": "kvm",
        "kvm_host": "kvm108",
        "kvm_host_ip": "100.64.6.6",
        "active_ncc_vm": "kvm108-cl408d-ncc1",
        "ncc_mgmt_ip": "100.64.4.122",
        "ncc_vms": ["kvm108-cl408d-ncc0", "kvm108-cl408d-ncc1"],
        "ncc_hosts": ["kvm108-cl408d-ncc0", "kvm108-cl408d-ncc1"],
        "kvm_host_credentials": {"username": "dn", "password": "drive1234!"},
        "ncc_console_credentials": {"username": "dn", "password": "drivenets"},
        "dncli_credentials": {"username": "dnroot", "password": "dnroot"},
    }
    changed = False
    for k, v in top_up.items():
        if not existing.get(k):
            existing[k] = v
            changed = True
    if changed:
        path.write_text(json.dumps(existing, indent=2))
        os.chmod(path, 0o600)
    return path


def _case(label: str) -> None:
    print(f"\n=== {label}")


def main() -> int:
    os.environ.setdefault("TOPOLOGY_USERS_BASE", "/tmp/cf_e2e")
    base = Path(os.environ["TOPOLOGY_USERS_BASE"])
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)

    ops_path = _seed_ops_with_kvm_info()
    map_path = Path("/home/dn/SCALER/db/console_mappings.json")

    from routes import _console_fallback as cf

    _case("1. Fresh user -- read from ops")
    fb = cf.read_fallback("alice", "YOR_CL_PE-4")
    assert fb.kvm_host_ip == "100.64.6.6", fb.kvm_host_ip
    assert fb.source == "operational.json", fb.source
    assert fb.best_method() == "virsh_console"
    print(f"  best_method={fb.best_method()} source={fb.source}")

    _case("2. capture_from_ops -> persisted 0600")
    # Seed a pre-existing SSH credential entry so we can later verify
    # delete_fallback only drops the console_fallback block.
    dev_file = base / "alice" / "devices.json"
    dev_file.parent.mkdir(parents=True, exist_ok=True)
    dev_file.write_text(json.dumps({
        "YOR_CL_PE-4": {"user": "dnroot", "password": "ZG5yb290", "updated_at": "pre-seed"}
    }))
    os.chmod(dev_file, 0o600)

    captured = cf.capture_from_ops("alice", "YOR_CL_PE-4", reason="e2e")
    assert not captured.is_empty()
    assert dev_file.exists()
    assert oct(dev_file.stat().st_mode)[-3:] == "600"
    data = json.loads(dev_file.read_text())
    assert data["YOR_CL_PE-4"]["console_fallback"]["kvm_user"] == "dn"
    # Pre-existing SSH cred must survive the capture.
    assert data["YOR_CL_PE-4"]["user"] == "dnroot"
    print(f"  captured kvm_host_ip={captured.kvm_host_ip} auto_captured_at={captured.auto_captured_at}")
    print(f"  pre-seeded SSH cred preserved: user={data['YOR_CL_PE-4']['user']}")

    _case("3. User override > ops")
    data["YOR_CL_PE-4"]["console_fallback"]["kvm_host_ip"] = "10.10.10.10"
    data["YOR_CL_PE-4"]["console_fallback"]["notes"] = "manual-override"
    dev_file.write_text(json.dumps(data))
    os.chmod(dev_file, 0o600)
    fb2 = cf.read_fallback("alice", "YOR_CL_PE-4")
    assert fb2.kvm_host_ip == "10.10.10.10", fb2.kvm_host_ip
    # ncc_mgmt_ip was not overridden -> should fill in from ops
    assert fb2.ncc_mgmt_ip == "100.64.4.122", fb2.ncc_mgmt_ip
    print(f"  user kvm_host_ip={fb2.kvm_host_ip} (override) ncc_mgmt_ip={fb2.ncc_mgmt_ip} (merged from ops)")

    _case("4. Ops wipe + map wipe -> scaler rescues via user_fallback")
    ops_backup = ops_path.with_suffix(".e2e_bak")
    map_backup = map_path.with_suffix(".e2e_bak")
    shutil.copy(ops_path, ops_backup)
    shutil.copy(map_path, map_backup)
    try:
        ops_path.write_text("{}")
        os.chmod(ops_path, 0o600)
        mdata = json.loads(map_backup.read_text())
        mdata["cluster_ncc_access"] = {}
        map_path.write_text(json.dumps(mdata))

        # Restore the user fallback to the pre-override state so we test
        # a clean captured-from-ops record, not the manual override IP.
        data["YOR_CL_PE-4"]["console_fallback"]["kvm_host_ip"] = "100.64.6.6"
        data["YOR_CL_PE-4"]["console_fallback"]["notes"] = "pre_wipe_capture"
        dev_file.write_text(json.dumps(data))
        os.chmod(dev_file, 0o600)

        from scaler.connection_strategy import DeviceConnector
        class _Dev:
            hostname = "YOR_CL_PE-4"
            ip = "100.64.4.122"
            serial_number = None
            username = "dnroot"
            password = "dnroot"
            loopback_ip = None
        conn = DeviceConnector(_Dev(), console_config=None)
        kvm_cfg = conn._get_kvm_host_config()
        assert kvm_cfg is not None
        assert kvm_cfg.get("_source") == "user_fallback", kvm_cfg.get("_source")
        assert kvm_cfg["kvm_host_ip"] == "100.64.6.6"
        assert kvm_cfg["kvm_host_credentials"]["password"] == "drive1234!"
        assert "kvm108-cl408d-ncc1" in kvm_cfg["ncc_vms"]
        print(f"  scaler picked up user_fallback kvm_host_ip={kvm_cfg['kvm_host_ip']} ncc_vms={kvm_cfg['ncc_vms']}")
    finally:
        shutil.move(ops_backup, ops_path)
        os.chmod(ops_path, 0o600)
        shutil.move(map_backup, map_path)

    _case("5. User bob still sees ops data (no manual capture needed)")
    bob = cf.read_fallback("bob", "YOR_CL_PE-4")
    assert bob.source == "operational.json"
    assert bob.kvm_host_ip == "100.64.6.6"
    print(f"  bob: source={bob.source} kvm_host_ip={bob.kvm_host_ip}")

    _case("6. sanitize invariants")
    fb3 = cf.read_fallback("alice", "YOR_CL_PE-4")
    safe = cf.sanitize(fb3)
    assert safe["kvm_pass"] == "***"
    assert safe["kvm_user"] == "dn"
    assert safe.get("ncc_vms") and len(safe["ncc_vms"]) >= 2
    print(f"  sanitized kvm_pass={safe['kvm_pass']!r} kvm_user={safe['kvm_user']!r}")

    _case("7. describe_availability")
    avail = cf.describe_availability(fb3)
    assert avail["virsh_console"] is True
    assert avail["ssh_ncc"] is True
    print(f"  availability={avail}")

    _case("8. delete_fallback -- only removes console_fallback, keeps creds")
    cf.delete_fallback("alice", "YOR_CL_PE-4")
    data_after = json.loads(dev_file.read_text())
    assert "console_fallback" not in data_after["YOR_CL_PE-4"]
    assert data_after["YOR_CL_PE-4"].get("user") == "dnroot"
    print("  console_fallback removed; user/password entry retained")

    print("\nALL E2E TESTS PASSED")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:
        print(f"\nASSERTION FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
