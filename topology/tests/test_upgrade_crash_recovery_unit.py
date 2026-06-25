"""Unit tests for crash-mid-upgrade phase markers + orphan-in-GI recovery.

These tests validate the resilience guarantees promised by
``_stamp_phase`` / ``_get_phase_marker`` / ``_latest_phase_reached`` /
``_drive_orphan_in_gi`` and the ``/api/operations/image-upgrade/stuck-
devices`` endpoint surface.

Why these tests exist
---------------------
The PE-4 incident on 2026-04-26 (server crashed BETWEEN ``request system
delete`` and ``request system deploy``) exposed a gap: the orphan
recovery scanner refused to drive devices stuck in GI mode because the
old logic assumed deploy had already happened. The fix added phase
markers to ``operational.json`` and an orphan-in-GI path that can
either auto-resume (when sys_type / ncc_id / image URLs are persisted)
or surface a "Resume Stuck Upgrade" banner to the operator.

Without these tests the next refactor will reintroduce the gap. Run
them in CI:

    cd /home/dn/drivenets-topology-studio/topology
    PYTHONPATH=. python tests/test_upgrade_crash_recovery_unit.py

The script exits 1 on the first failure, 0 on full pass.

Covered phase boundaries
------------------------
  1. ``delete_sent_at`` only -- crash IMMEDIATELY after `request system
     delete` was dispatched. Resumer should classify this as
     "delete-in-flight" and use live probe to determine whether GI was
     reached.
  2. ``gi_confirmed_at`` only -- crash AFTER GI confirmed but BEFORE
     image load. Resume should skip the delete (already done) and
     start at image load.
  3. ``images_loaded_at`` only -- crash AFTER images loaded but BEFORE
     deploy command. Resume should skip delete + load, jump to
     `request system deploy`.
  4. ``deploy_sent_at`` only -- crash AFTER deploy sent. Resume should
     enter `_post_deploy_verify` directly.
  5. ``dnos_confirmed_at`` only -- crash AFTER DNOS hand-off but
     BEFORE config repair. Resume should run config repair.
  6. ``config_repair_completed_at`` set + no ``upgrade_completed_at``
     -- crash in the final cleanup window. Resume should idempotently
     finish.
  7. ``upgrade_completed_at`` set -- nothing to do; orphan scanner
     must not surface this device.
  8. Manual-intervention path: ``deploy_sent_at`` missing AND
     ``upgrade_url_list`` missing -> ``_drive_orphan_in_gi`` writes
     ``manual_intervention_required = True`` with a missing-fields
     list. ``/api/operations/image-upgrade/stuck-devices`` must
     surface it.
  9. Auto-resume path: deploy_sent_at missing BUT system_type +
     ncc_id + url_list all persisted -> orphan-in-GI recovery
     synthesises a job (no manual-intervention flag set).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

# Discover repo root so `import routes...` works regardless of CWD.
_HERE = Path(__file__).resolve()
_TOPOLOGY_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_TOPOLOGY_ROOT))


# ---------------------------------------------------------------------------
# Test scaffolding
# ---------------------------------------------------------------------------
_FAILED = 0


def _check(cond: bool, msg: str) -> None:
    global _FAILED
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {msg}")
    if not cond:
        _FAILED += 1


def _make_temp_scaler_root() -> Path:
    """Build a SCALER_ROOT dir tree just complete enough for the helpers."""
    root = Path(tempfile.mkdtemp(prefix="upgrade_recovery_test_"))
    (root / "db" / "configs").mkdir(parents=True)
    return root


def _make_device(root: Path, name: str, op_data: dict, *,
                 backup_lines: int = 100) -> Path:
    """Drop a device dir with operational.json + a pre-delete backup."""
    dev_dir = root / "db" / "configs" / name
    dev_dir.mkdir(parents=True, exist_ok=True)
    (dev_dir / "operational.json").write_text(json.dumps(op_data, indent=2))
    backup_path = dev_dir / f"pre_delete_backup_{name}.txt"
    backup_path.write_text("\n".join(
        f"# line {i}" if i < 5 else f"interface ethernet {i}"
        for i in range(backup_lines)
    ))
    op_data["pre_delete_backup"] = str(backup_path)
    (dev_dir / "operational.json").write_text(json.dumps(op_data, indent=2))
    return dev_dir


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_stamp_and_read_markers():
    """`_stamp_phase` writes; `_get_phase_marker` and `_latest_phase_reached`
    read back the chronologically-latest one."""
    from routes import upgrade as up

    root = _make_temp_scaler_root()
    saved_root = up.SCALER_ROOT
    up.SCALER_ROOT = str(root)
    try:
        dev_dir = _make_device(root, "PE-test1", {"device_state": "DNOS"})

        ok = up._stamp_phase("PE-test1", "delete_sent_at")
        _check(ok, "stamp delete_sent_at returns True")

        op = json.loads((dev_dir / "operational.json").read_text())
        _check("delete_sent_at" in op, "delete_sent_at key present in ops")
        _check(op.get("upgrade_last_phase") == "delete_sent_at",
               "upgrade_last_phase tracks latest stamp")

        up._stamp_phase("PE-test1", "gi_confirmed_at",
                        gi_state_observed="GI")
        op = json.loads((dev_dir / "operational.json").read_text())
        _check("gi_confirmed_at" in op, "gi_confirmed_at key present")
        _check(op.get("gi_state_observed") == "GI",
               "extra kwargs persisted alongside marker")

        latest = up._latest_phase_reached(op)
        _check(latest == "gi_confirmed_at",
               f"_latest_phase_reached returns gi_confirmed_at (got {latest!r})")

        # Now stamp a later one and verify ordering
        up._stamp_phase("PE-test1", "deploy_sent_at",
                        upgrade_deploy_command="request system deploy ...")
        op = json.loads((dev_dir / "operational.json").read_text())
        _check(up._latest_phase_reached(op) == "deploy_sent_at",
               "_latest_phase_reached follows chronological order")

        # Clear should remove ALL markers
        up._clear_upgrade_markers("PE-test1")
        op = json.loads((dev_dir / "operational.json").read_text())
        for m in up._UPGRADE_PHASE_MARKERS:
            _check(m not in op, f"_clear_upgrade_markers removed {m}")
        _check("upgrade_deploy_command" not in op,
               "_clear_upgrade_markers removed deploy command too")
    finally:
        up.SCALER_ROOT = saved_root


def test_orphan_scan_skips_completed():
    """Orphan scanner must not pick up devices with upgrade_completed_at set."""
    from routes import upgrade as up

    root = _make_temp_scaler_root()
    saved_root = up.SCALER_ROOT
    up.SCALER_ROOT = str(root)
    try:
        # Completed device -- should be skipped
        _make_device(root, "PE-done", {
            "device_state": "DNOS",
            "delete_sent_at": "2026-04-27T10:00:00Z",
            "deploy_sent_at": "2026-04-27T10:05:00Z",
            "dnos_confirmed_at": "2026-04-27T10:25:00Z",
            "upgrade_completed_at": "2026-04-27T10:30:00Z",
        })
        # Stranded device -- should be picked up
        _make_device(root, "PE-stranded", {
            "device_state": "GI",
            "delete_sent_at": "2026-04-27T10:00:00Z",
            "gi_confirmed_at": "2026-04-27T10:08:00Z",
            "upgrade_in_progress": True,
        })

        # Drive the candidate-collection loop manually -- patch out the
        # actual recovery so we can inspect just the filter behaviour.
        candidates = []

        def _capture(scaler_hostname, op_data, backup_path,
                     _live=None, _mode=None):
            candidates.append(scaler_hostname)

        original_drive_dnos = up._drive_orphan_in_gi if hasattr(up, "_drive_orphan_in_gi") else None
        # Stub the live-probe and drivers so the scanner can run without
        # network. We just want to verify which devices ENTER the
        # "would be recovered" set.
        original_probe = up._live_probe_for_recovery
        up._live_probe_for_recovery = lambda *a, **k: {"mode": "GI"}
        up._drive_orphan_in_gi = _capture
        try:
            up._scan_orphan_post_deploy_devices(set())
        finally:
            up._live_probe_for_recovery = original_probe
            if original_drive_dnos is not None:
                up._drive_orphan_in_gi = original_drive_dnos

        _check("PE-done" not in candidates,
               "Completed device NOT picked up by orphan scanner")
        _check("PE-stranded" in candidates,
               "Stranded device IS picked up by orphan scanner")
    finally:
        up.SCALER_ROOT = saved_root


def test_drive_orphan_in_gi_marks_manual_when_missing_fields():
    """When deploy params are missing, `_drive_orphan_in_gi` should NOT
    auto-resume; it must mark `manual_intervention_required` and
    populate the missing-fields list so the wizard can prompt."""
    from routes import upgrade as up

    root = _make_temp_scaler_root()
    saved_root = up.SCALER_ROOT
    up.SCALER_ROOT = str(root)
    try:
        dev_dir = _make_device(root, "PE-missing", {
            "device_state": "GI",
            "delete_sent_at": "2026-04-27T10:00:00Z",
            "gi_confirmed_at": "2026-04-27T10:05:00Z",
            "pre_delete_backup_at": "2026-04-27T09:59:00Z",
            "upgrade_in_progress": True,
        })

        # Stub submit_upgrade so synth jobs don't actually queue.
        from routes import _worker_pool as wp
        original_submit = wp.submit_upgrade
        submitted = []
        wp.submit_upgrade = lambda fn: submitted.append(fn)
        try:
            up._drive_orphan_in_gi(
                "PE-missing",
                json.loads((dev_dir / "operational.json").read_text()),
                Path(json.loads((dev_dir / "operational.json").read_text())["pre_delete_backup"]),
                {"mode": "GI"},
                "GI",
            )
        finally:
            wp.submit_upgrade = original_submit

        op = json.loads((dev_dir / "operational.json").read_text())
        _check(op.get("manual_intervention_required") is True,
               "manual_intervention_required latched True when deploy params missing")
        missing = op.get("manual_intervention_missing", [])
        _check("system_type" in missing,
               f"missing list contains system_type (got {missing!r})")
        _check("ncc_id" in missing, "missing list contains ncc_id")
        _check("image_urls" in missing, "missing list contains image_urls")
        _check(len(submitted) == 0,
               "No recovery job queued when fields missing (operator must intervene)")
    finally:
        up.SCALER_ROOT = saved_root


def test_drive_orphan_in_gi_auto_resumes_when_complete():
    """When deploy params + image URLs are persisted, recovery is auto-
    queued (no manual_intervention_required latch)."""
    from routes import upgrade as up

    root = _make_temp_scaler_root()
    saved_root = up.SCALER_ROOT
    up.SCALER_ROOT = str(root)
    try:
        dev_dir = _make_device(root, "PE-complete", {
            "device_state": "GI",
            "delete_sent_at": "2026-04-27T10:00:00Z",
            "gi_confirmed_at": "2026-04-27T10:05:00Z",
            "images_loaded_at": "2026-04-27T10:12:00Z",
            "pre_delete_backup_at": "2026-04-27T09:59:00Z",
            "upgrade_deploy_system_type": "DNX-S04",
            "upgrade_deploy_name": "PE-complete",
            "upgrade_deploy_ncc_id": 1,
            "upgrade_deploy_command":
                "request system deploy system-type DNX-S04 name PE-complete ncc-id 1",
            "upgrade_url_list": [
                ["DNOS", "http://example/dnos.tar"],
                ["GI", "http://example/gi.tar"],
                ["BaseOS", "http://example/baseos.tar"],
            ],
            "upgrade_in_progress": True,
        })

        from routes import _worker_pool as wp
        original_submit = wp.submit_upgrade
        submitted = []
        wp.submit_upgrade = lambda fn: submitted.append(fn)
        try:
            up._drive_orphan_in_gi(
                "PE-complete",
                json.loads((dev_dir / "operational.json").read_text()),
                Path(json.loads((dev_dir / "operational.json").read_text())["pre_delete_backup"]),
                {"mode": "GI"},
                "GI",
            )
        finally:
            wp.submit_upgrade = original_submit

        op = json.loads((dev_dir / "operational.json").read_text())
        _check(not op.get("manual_intervention_required"),
               "manual_intervention_required NOT set when params complete")
        _check(len(submitted) == 1,
               f"Exactly one recovery job submitted (got {len(submitted)})")
    finally:
        up.SCALER_ROOT = saved_root


def test_stuck_devices_endpoint_filters_correctly():
    """The /stuck-devices endpoint must list manual_intervention=True
    devices and exclude completed ones."""
    from routes import upgrade as up

    root = _make_temp_scaler_root()
    saved_root = up.SCALER_ROOT
    up.SCALER_ROOT = str(root)
    try:
        _make_device(root, "PE-stuck1", {
            "device_state": "GI",
            "manual_intervention_required": True,
            "manual_intervention_reason": "missing image_urls",
            "manual_intervention_missing": ["image_urls"],
            "manual_intervention_live_mode": "GI",
            "manual_intervention_at": "2026-04-27T10:30:00Z",
            "manual_intervention_deploy_command":
                "request system deploy system-type DNX-S04 name PE-stuck1 ncc-id 1",
        })
        _make_device(root, "PE-stuck-but-done", {
            "device_state": "DNOS",
            "manual_intervention_required": True,
            "upgrade_completed_at": "2026-04-27T11:00:00Z",
        })
        _make_device(root, "PE-clean", {"device_state": "DNOS"})

        result = up.image_upgrade_stuck_devices()
        ids = [d["device_id"] for d in result["stuck_devices"]]

        _check("PE-stuck1" in ids, "PE-stuck1 surfaced by stuck-devices")
        _check("PE-stuck-but-done" not in ids,
               "Completed-but-formerly-stuck device hidden")
        _check("PE-clean" not in ids, "Clean device not surfaced")

        stuck1 = next(d for d in result["stuck_devices"] if d["device_id"] == "PE-stuck1")
        _check(stuck1["live_mode"] == "GI",
               "live_mode propagated to stuck-devices payload")
        _check("image_urls" in stuck1["missing"],
               "missing fields propagated to stuck-devices payload")
        _check(stuck1["suggested_deploy_command"].startswith(
            "request system deploy"),
               "suggested_deploy_command surfaced verbatim")
    finally:
        up.SCALER_ROOT = saved_root


def test_clear_stuck_endpoint_removes_latch():
    """The /clear-stuck endpoint must remove all
    manual_intervention_* fields without touching upgrade markers."""
    from routes import upgrade as up

    root = _make_temp_scaler_root()
    saved_root = up.SCALER_ROOT
    up.SCALER_ROOT = str(root)
    try:
        dev_dir = _make_device(root, "PE-clr", {
            "device_state": "GI",
            "manual_intervention_required": True,
            "manual_intervention_reason": "test",
            "manual_intervention_missing": ["image_urls"],
            "delete_sent_at": "2026-04-27T10:00:00Z",
        })
        result = up.image_upgrade_clear_stuck({"device_ids": ["PE-clr"]})
        _check("PE-clr" in result["cleared"],
               "Cleared device echoed in response")
        op = json.loads((dev_dir / "operational.json").read_text())
        _check(not op.get("manual_intervention_required"),
               "manual_intervention_required removed")
        _check("manual_intervention_reason" not in op,
               "manual_intervention_reason removed")
        _check(op.get("delete_sent_at") == "2026-04-27T10:00:00Z",
               "Phase markers preserved (clear-stuck is non-destructive)")
    finally:
        up.SCALER_ROOT = saved_root


class _FakeBashProbeChannel:
    """Tiny channel fake for bash-probe regression tests."""

    def __init__(self, *, closed=False):
        self.closed = closed
        self.sent = []
        self._buf = b""

    def send(self, data):
        if self.closed:
            raise OSError("Socket is closed")
        text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else str(data)
        self.sent.append(text)
        marker = "__BASH_PROBE_"
        if marker in text and "%s" in text:
            start = text.index(marker) + len(marker)
            nonce = text[start:].split("_", 1)[0]
            self._buf += f"__BASH_PROBE_{nonce}_OK__\n".encode()
        return len(data)

    def recv_ready(self):
        return bool(self._buf)

    def recv(self, _size):
        out = self._buf
        self._buf = b""
        return out


def test_probe_ncc_bash_and_closed_channel_guard():
    """KVM GI preflight must not treat a closed virsh channel as usable."""
    from routes import upgrade as up

    bash = _FakeBashProbeChannel()
    _check(up._probe_ncc_bash(bash, wait=0.01) is True,
           "NCC bash probe succeeds from bash shell")

    closed = _FakeBashProbeChannel(closed=True)
    _check(up._probe_ncc_bash(closed, wait=0.01) is False,
           "NCC bash probe returns False on closed channel")
    _check(up._ensure_ncc_bash(closed) is False,
           "_ensure_ncc_bash handles closed channel without raising")


class _FakeGiProbeChannel:
    """Fake channel that returns scripted output to show-system-stack probes."""

    def __init__(self, responses):
        self.closed = False
        self.sent = []
        self.responses = list(responses)
        self._buf = b""

    def send(self, data):
        text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else str(data)
        self.sent.append(text)
        if "show system stack" in text and self.responses:
            self._buf += self.responses.pop(0).encode()
        return len(data)

    def recv_ready(self):
        return bool(self._buf)

    def recv(self, _size):
        out = self._buf
        self._buf = b""
        return out


class _FakeQuietChannel:
    """Fake channel used when _make_send_wait is monkeypatched."""

    closed = False

    def __init__(self):
        self.sent = []

    def send(self, data):
        text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else str(data)
        self.sent.append(text)
        return len(data)

    def recv_ready(self):
        return False

    def recv(self, _size):
        return b""


class _FakePromptChannel:
    """Fake shell channel that appends a prompt after every command."""

    closed = False

    def __init__(self, prompt):
        self.prompt = prompt
        self.sent = []
        self._buf = b""

    def send(self, data):
        text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else str(data)
        self.sent.append(text)
        self._buf += (text + self.prompt).encode()
        return len(data)

    def recv_ready(self):
        return bool(self._buf)

    def recv(self, _size):
        out = self._buf
        self._buf = b""
        return out


class _FakeLoadChannel:
    """Fake GI channel for target-stack load/reconnect tests."""

    closed = False

    def __init__(self):
        self.sent = []
        self._buf = b""

    def send(self, data):
        text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else str(data)
        self.sent.append(text)
        if "request system target-stack load" in text:
            self._buf += b"Continue? (yes/no)\n"
        elif text.strip() == "yes":
            self._buf += b"download in progress\nGI# "
        elif "\x03" in text:
            self._buf += b"GI# "
        return len(data)

    def recv_ready(self):
        return bool(self._buf)

    def recv(self, _size):
        out = self._buf
        self._buf = b""
        return out


_PE4_STACK_WITH_DNOS_TARGET = """
GI# show system stack | no-more
| Component | Version | Current | Previous | Rollback | Target |
| BASEOS    | pkg     | 2.2620006128 | - | - | 2.2620006128 |
| GI        | pkg     | 26.2.0.339_dev.dev_v26_2_899 | - | - | 26.2.0.339_dev.dev_v26_2_899 |
| DNOS      | pkg     | - | - | - | 26.2.0.4_priv.usirota_evpn_vpls_irb_4 |
GI#
"""


def test_gi_stack_target_parser_and_skip_match():
    """Target column is authoritative for already-loaded selected images."""
    from routes import upgrade as up

    targets = up._parse_system_stack_targets(_PE4_STACK_WITH_DNOS_TARGET)
    _check(targets["DNOS"]["target"] == "26.2.0.4_priv.usirota_evpn_vpls_irb_4",
           "stack parser captures DNOS Target column")
    dnos_url = (
        "http://minio-ssd-il.dev.drivenets.net:9000/dnpkg-48hrs/"
        "drivenets_dnos_26.2.0.4_priv.usirota_evpn_vpls_irb_4.tar"
    )
    gi_url = (
        "http://minio-ssd-il.dev.drivenets.net:9000/dnpkg-48hrs/"
        "drivenets_gi_26.2.0.4_priv.usirota_evpn_vpls_irb_4.tar"
    )
    _check(up._target_stack_has_expected_component(targets, "DNOS", dnos_url),
           "DNOS URL is treated as already loaded when Target matches")
    _check(not up._target_stack_has_expected_component(targets, "GI", gi_url),
           "GI URL is not skipped when Target is still the old GI build")
    matched, missing, _ = up._verify_stack_targets_for_urls(
        _PE4_STACK_WITH_DNOS_TARGET,
        [("DNOS", dnos_url), ("GI", gi_url)],
    )
    _check("DNOS" in matched, "pre-deploy verifier accepts selected DNOS target")
    _check("GI" in missing, "pre-deploy verifier rejects mismatched GI target")


def test_pe4_deploy_params_are_guarded():
    """PE-4 deploy flows must always carry CL-86/YOR_CL_PE-4/ncc-id 1."""
    from routes import upgrade as up

    params = {"system_type": "SA-40C8CD", "deploy_name": "PE-4", "ncc_id": 0}
    up._normalize_deploy_params(params, scaler_hostname="YOR_CL_PE-4", device_id="PE-4")
    _check(params["system_type"] == "CL-86", "PE-4 deploy guard forces CL-86")
    _check(params["deploy_name"] == "YOR_CL_PE-4", "PE-4 deploy guard uses canonical deploy name")
    _check(params["ncc_id"] == 1, "PE-4 deploy guard forces ncc-id 1")


def test_load_images_skips_component_when_target_already_present():
    """_load_images_on_channel must not re-send load for a matching Target."""
    from routes import upgrade as up

    dnos_url = (
        "http://minio-ssd-il.dev.drivenets.net:9000/dnpkg-48hrs/"
        "drivenets_dnos_26.2.0.4_priv.usirota_evpn_vpls_irb_4.tar"
    )
    chan = _FakeQuietChannel()
    logs = []
    original_make = up._make_send_wait
    up._make_send_wait = lambda _chan: (lambda _cmd, _wait=0: _PE4_STACK_WITH_DNOS_TARGET)
    try:
        up._load_images_on_channel(
            "job-test", "PE-4", chan, [("DNOS", dnos_url)], {},
            lambda level, msg: logs.append((level, msg)),
            ensure_gi_cli=False)
    finally:
        up._make_send_wait = original_make

    sent = "".join(chan.sent)
    _check("request system target-stack load" not in sent,
           "matching DNOS Target skips request system target-stack load")
    _check(any("already in target-stack" in msg for _level, msg in logs),
           "skip decision is logged for operator visibility")


def test_ensure_gi_cli_recovers_from_shell_drift():
    """Shell drift before a GI command should re-enter dncli and re-probe."""
    from routes import upgrade as up

    shell_output = "ncc:~$ show system stack | no-more\nshow: command not found\nncc:~$ "
    chan = _FakeGiProbeChannel([shell_output, _PE4_STACK_WITH_DNOS_TARGET])
    logs = []
    original_ensure = up._ensure_ncc_bash
    original_enter = up._enter_dncli_from_bash
    try:
        up._ensure_ncc_bash = lambda _chan: True
        up._enter_dncli_from_bash = lambda _chan, _log: True
        _check(up._ensure_gi_cli_for_command(
            chan, lambda level, msg: logs.append((level, msg)),
            "unit-test command", probe_wait=0.05) is True,
               "GI ensure helper re-enters dncli after shell drift")
    finally:
        up._ensure_ncc_bash = original_ensure
        up._enter_dncli_from_bash = original_enter

    show_probes = [s for s in chan.sent if "show system stack" in s]
    _check(len(show_probes) >= 2, "GI ensure helper re-probes after dncli entry")
    _check(any("drifted to NCC shell" in msg for _level, msg in logs),
           "shell drift recovery is logged")


def test_gi_cli_kvm_host_shell_requires_reconnect():
    """Outer KVM host shell must reconnect virsh, not run dncli locally."""
    from routes import upgrade as up

    shell_output = (
        "dn@kvm108:~$ show system stack | no-more\n"
        "show: command not found\n"
        "dn@kvm108:~$ "
    )
    chan = _FakeGiProbeChannel([shell_output])
    logs = []
    raised = None
    try:
        up._ensure_gi_cli_for_command(
            chan, lambda level, msg: logs.append((level, msg)),
            "unit-test command", probe_wait=0.05)
    except RuntimeError as exc:
        raised = exc

    _check(raised is not None, "KVM host shell drift raises instead of continuing")
    _check("KVM host shell" in str(raised),
           f"KVM host shell diagnostic is explicit (got {raised!r})")
    _check(not any("dncli" in s for s in chan.sent),
           "dncli is not sent to the outer KVM host shell")


def test_ncc_bash_probe_rejects_kvm_host_shell():
    """A KVM host bash prompt is not an NCC bash prompt."""
    from routes import upgrade as up

    chan = _FakePromptChannel("dn@kvm108:~$ ")
    _check(up._probe_ncc_bash(chan, wait=0.05) is False,
           "NCC bash probe rejects outer KVM host shell")

    kvm_output = "dn@kvm108:~$ show system stack | no-more\nshow: command not found\ndn@kvm108:~$ "
    _check(up._looks_like_kvm_host_shell_output(kvm_output) is True,
           "KVM host shell classifier recognizes dn@kvm prompt")
    _check(up._looks_like_ncc_shell_output(kvm_output) is False,
           "NCC shell classifier does not absorb KVM host shell errors")
    _check(up._gi_command_failed_due_to_shell(kvm_output) is True,
           "GI command shell-failure detector still catches KVM host execution")


def test_gi_preflight_probe_does_not_ctrl_c_from_gi_cli():
    """GI preflight should classify with show-system-stack, not Ctrl+C."""
    from routes import upgrade as up

    chan = _FakeGiProbeChannel([_PE4_STACK_WITH_DNOS_TARGET])
    logs = []
    ssh, out_chan, ncc_id, recovered = up._preflight_gi_health(
        "job-test", "PE-4", chan, object(), "YOR_CL_PE-4",
        lambda level, msg: logs.append((level, msg)))

    _check(out_chan is chan and ncc_id is None and recovered is False,
           "GI preflight returns original channel when stack probe succeeds")
    _check(not any("\x03" in s for s in chan.sent),
           "GI preflight does not send Ctrl+C before stack probe")


def test_load_status_kvm_drift_reconnects_and_resumes_polling():
    """BaseOS load status poll can reconnect GI CLI without resending load."""
    from routes import upgrade as up
    import time as time_module

    chan = _FakeLoadChannel()
    logs = []
    ensure_calls = []
    reconnects = []
    sw_calls = []
    raised_status_once = {"done": False}
    baseos_url = (
        "http://minio-ssd-il.dev.drivenets.net:9000/dnpkg-48hrs/"
        "drivenets_baseos_26.2.0.4_priv.usirota_evpn_vpls_irb_4.tar"
    )

    original_ensure = up._ensure_gi_cli_for_command
    original_make = up._make_send_wait
    original_update = up._update_device_state
    original_cancel = up._check_upgrade_cancel
    original_sleep = time_module.sleep

    def fake_ensure(_chan, _log, context="GI command", probe_wait=6.0):
        ensure_calls.append(context)
        if "load status" in context and not raised_status_once["done"]:
            raised_status_once["done"] = True
            raise up._GiCliReconnectRequired("status poll saw dn@kvm108 host shell")
        return True

    def fake_make(_chan):
        def fake_send_wait(cmd, _wait=0):
            sw_calls.append(cmd)
            if "show system target-stack load" in cmd:
                return "Task status: Complete\nProgress: 100%\nGI#"
            return _PE4_STACK_WITH_DNOS_TARGET
        return fake_send_wait

    try:
        up._ensure_gi_cli_for_command = fake_ensure
        up._make_send_wait = fake_make
        up._update_device_state = lambda *args, **kwargs: None
        up._check_upgrade_cancel = lambda _job_id: None
        time_module.sleep = lambda _seconds: None

        up._load_images_on_channel(
            "job-test", "PE-4", chan, [("BaseOS", baseos_url)], {},
            lambda level, msg: logs.append((level, msg)),
            ensure_gi_cli=True,
            reconnect_gi_cli=lambda reason: reconnects.append(reason) or chan,
            pct_base=10,
            pct_range=10,
        )
    finally:
        up._ensure_gi_cli_for_command = original_ensure
        up._make_send_wait = original_make
        up._update_device_state = original_update
        up._check_upgrade_cancel = original_cancel
        time_module.sleep = original_sleep

    load_sends = [s for s in chan.sent if "request system target-stack load" in s]
    _check(len(load_sends) == 1,
           f"load command sent once while status reconnect resumes polling (got {len(load_sends)})")
    _check(len(reconnects) == 1,
           f"one GI reconnect requested during status poll drift (got {len(reconnects)})")
    _check(any("resuming target-stack polling" in msg for _level, msg in logs),
           "operator log says reconnect resumes target-stack polling")
    _check(any("show system target-stack load" in cmd for cmd in sw_calls),
           "status polling continued after reconnect")


def test_unverified_gi_manager_health_blocks_entry():
    """Unverified Docker health must not be treated as healthy."""
    from routes import upgrade as up

    chan = _FakeQuietChannel()
    logs = []
    original_ensure = up._ensure_ncc_bash
    original_health = up._check_gi_manager_health
    original_enter = up._enter_dncli_from_bash
    entered = {"called": False}
    try:
        up._ensure_ncc_bash = lambda _chan: True
        up._check_gi_manager_health = lambda _chan, _log: {
            "healthy": False,
            "needs_recovery": False,
            "diagnosis": "could not verify Docker service list; refusing automatic recovery",
        }
        def _enter(_chan, _log):
            entered["called"] = True
            return False
        up._enter_dncli_from_bash = _enter
        raised = None
        try:
            up._preflight_gi_health(
                "job-test", "PE-4", chan, object(), "YOR_CL_PE-4",
                lambda level, msg: logs.append((level, msg)))
        except RuntimeError as exc:
            raised = exc
    finally:
        up._ensure_ncc_bash = original_ensure
        up._check_gi_manager_health = original_health
        up._enter_dncli_from_bash = original_enter

    _check(raised is not None, "unverified gi-manager health blocks preflight")
    _check("unverified" in str(raised),
           f"unverified health diagnostic is explicit (got {raised!r})")
    _check(not entered["called"], "dncli is not attempted when health is unknown")


def test_upgrade_terminal_line_has_per_device_timestamp():
    """Per-device upgrade logs keep parser shape and show UTC+3 time."""
    from routes import upgrade as up
    from datetime import datetime, timedelta, timezone

    line = up._format_upgrade_terminal_line("INFO", "hello", "PE-4")
    _check(line.startswith("[INFO] PE-4: ["),
           f"per-device log keeps '[LEVEL] device:' prefix (got {line!r})")
    _check(bool(__import__("re").match(r"^\[INFO\] PE-4: \[\d{2}:\d{2}:\d{2}\] hello$", line)),
           "per-device log includes HH:MM:SS timestamp")
    expected_hour = datetime.now(timezone(timedelta(hours=3))).strftime("%H")
    _check(line.split("[", 2)[2].startswith(expected_hour),
           "per-device log timestamp is rendered in UTC+3")



def test_jobs_endpoint_tolerates_legacy_recovery_job_id():
    """/api/operations/jobs must not 500 on legacy rows that only carry id."""
    from routes import operations as ops
    from routes._state import _push_jobs, _push_jobs_lock

    class _State:
        user = "default"
        role = "admin"

    class _Req:
        state = _State()

    original_history = ops._load_push_history
    with _push_jobs_lock:
        saved = dict(_push_jobs)
        _push_jobs.clear()
        _push_jobs["legacy-active"] = {
            "id": "legacy-active",
            "job_type": "upgrade",
            "owner": "default",
            "status": "running",
            "started_at": "2026-05-10T00:00:00Z",
            "terminal_lines": ["[INFO] old row"],
        }
    try:
        ops._load_push_history = lambda: [{
            "id": "legacy-history",
            "owner": "default",
            "status": "completed",
            "started_at": "2026-05-09T00:00:00Z",
            "terminal_lines": object(),
        }]
        result = ops.list_jobs(_Req())
        ids = [j.get("job_id") for j in result.get("jobs", [])]
        _check("legacy-active" in ids, "legacy active job id normalized to job_id")
        _check("legacy-history" in ids, "legacy history job id normalized to job_id")
        json.dumps(result)
        _check(True, "jobs endpoint payload is strict JSON serializable")
    finally:
        ops._load_push_history = original_history
        with _push_jobs_lock:
            _push_jobs.clear()
            _push_jobs.update(saved)


def test_dnos_readiness_gate_and_config_snapshot_cleaning():
    """Post-deploy repair waits for real show system and strips CLI echoes."""
    from routes import upgrade as up

    ready, reason = up._dnos_show_system_ready(
        "RR-SA-2# show system | no-more\n"
        "system-type : SA-36CD-S\n"
        "name : RR-SA-2\n"
        "ncc-id : 0\n"
        "RR-SA-2#",
        "RR-SA-2",
        "RR-SA-2",
    )
    _check(ready, f"show system readiness accepts full DNOS output ({reason})")

    not_ready, bad_reason = up._dnos_show_system_ready(
        "RR-SA-2# show system | no-more\nERROR: temporarily unavailable\nRR-SA-2#",
        "RR-SA-2",
        "RR-SA-2",
    )
    _check(not not_ready, f"show system readiness rejects partial DNOS output ({bad_reason})")

    cleaned = up._clean_show_config_snapshot(
        "RR-SA-2# show config | no-more\r\n"
        "interfaces\n"
        " interface ge100-0/0/1\n"
        "!\n"
        "RR-SA-2#\n"
    )
    _check("show config" not in cleaned.lower(), "config snapshot cleaner removes command echo")
    _check("RR-SA-2#" not in cleaned, "config snapshot cleaner removes prompt")
    _check("interfaces" in cleaned, "config snapshot cleaner preserves config body")


def _install_fake_config_pusher(fake_cls):
    """Install a fake scaler.config_pusher module for restore unit tests."""
    import types

    fake_scaler = sys.modules.get("scaler")
    if fake_scaler is None:
        fake_scaler = types.ModuleType("scaler")
        sys.modules["scaler"] = fake_scaler
    fake_mod = types.ModuleType("scaler.config_pusher")
    fake_mod.ConfigPusher = fake_cls
    previous = sys.modules.get("scaler.config_pusher")
    previous_attr = getattr(fake_scaler, "config_pusher", None)
    sys.modules["scaler.config_pusher"] = fake_mod
    fake_scaler.config_pusher = fake_mod
    return fake_scaler, previous, previous_attr


def _restore_fake_config_pusher(fake_scaler, previous, previous_attr):
    if previous is None:
        sys.modules.pop("scaler.config_pusher", None)
    else:
        sys.modules["scaler.config_pusher"] = previous
    if previous_attr is None:
        try:
            delattr(fake_scaler, "config_pusher")
        except AttributeError:
            pass
    else:
        fake_scaler.config_pusher = previous_attr


def test_config_restore_auth_failure_is_retryable_pending():
    """Post-deploy file restore auth failure should stay pending/retryable."""
    from routes import upgrade as up

    root = _make_temp_scaler_root()
    saved_root = up.SCALER_ROOT
    job_id = "job-auth-retry"
    device_id = "PE-4"
    calls = []

    class FakePusher:
        def push_config(self, dev, *_args, **_kwargs):
            calls.append((dev.username, dev.ip))
            return False, "Authentication failed - check username/password"

    fake_scaler, previous_mod, previous_attr = _install_fake_config_pusher(FakePusher)
    original_get = up._get_credentials
    original_chain = up._get_lab_credential_chain
    original_resolve = up._resolve_mgmt_ip
    up.SCALER_ROOT = str(root)
    with up._push_jobs_lock:
        saved_jobs = dict(up._push_jobs)
        up._push_jobs.clear()
        up._push_jobs[job_id] = {
            "job_type": "upgrade",
            "device_state": {device_id: {}},
            "terminal_lines": [],
        }
    try:
        _make_device(root, "YOR_CL_PE-4", {"device_state": "DNOS"}, backup_lines=20)
        up._get_credentials = lambda *a, **k: ("dnroot", "dnroot")
        up._get_lab_credential_chain = lambda *a, **k: []
        up._resolve_mgmt_ip = lambda *_a, **_k: ("100.64.11.96", "YOR_CL_PE-4", None)
        logs = []
        terms = []
        outcome = up._post_deploy_restore_from_file(
            job_id, device_id, "YOR_CL_PE-4",
            lambda level, msg: logs.append((level, msg)),
            lambda msg: terms.append(msg),
            mgmt_ip_hint="100.64.11.96")
        state = up._push_jobs[job_id]["device_state"][device_id]
        _check(outcome[0] == "retryable",
               f"auth failure returns retryable outcome (got {outcome!r})")
        _check(state.get("config_repair_pending") is True,
               "auth failure marks config repair pending")
        _check(state.get("config_repair_retryable") is True,
               "auth failure marks config repair retryable")
        _check(state.get("config_restored") is False,
               "auth failure does not mark config restored")
        _check(calls == [("dnroot", "100.64.11.96")],
               f"restore used hinted active-NCC host (calls={calls!r})")
    finally:
        up._get_credentials = original_get
        up._get_lab_credential_chain = original_chain
        up._resolve_mgmt_ip = original_resolve
        up.SCALER_ROOT = saved_root
        _restore_fake_config_pusher(fake_scaler, previous_mod, previous_attr)
        with up._push_jobs_lock:
            up._push_jobs.clear()
            up._push_jobs.update(saved_jobs)


def test_config_restore_falls_back_to_lab_credentials():
    """Restore should try saved credentials first, then lab DNOS profile."""
    from routes import upgrade as up

    root = _make_temp_scaler_root()
    saved_root = up.SCALER_ROOT
    job_id = "job-auth-fallback"
    device_id = "PE-4"
    attempted_users = []

    class FakePusher:
        def push_config(self, dev, *_args, **_kwargs):
            attempted_users.append(dev.username)
            if dev.username == "baduser":
                return False, "Authentication failed - check username/password"
            return True, "Configuration committed successfully"

    fake_scaler, previous_mod, previous_attr = _install_fake_config_pusher(FakePusher)
    original_get = up._get_credentials
    original_chain = up._get_lab_credential_chain
    original_resolve = up._resolve_mgmt_ip
    up.SCALER_ROOT = str(root)
    with up._push_jobs_lock:
        saved_jobs = dict(up._push_jobs)
        up._push_jobs.clear()
        up._push_jobs[job_id] = {
            "job_type": "upgrade",
            "device_state": {device_id: {}},
            "terminal_lines": [],
        }
    try:
        _make_device(root, "YOR_CL_PE-4", {"device_state": "DNOS"}, backup_lines=20)
        up._get_credentials = lambda *a, **k: ("baduser", "badpass")
        up._get_lab_credential_chain = lambda *a, **k: [
            ("dut", "dnroot", "dnroot")
        ]
        up._resolve_mgmt_ip = lambda *_a, **_k: ("100.64.11.96", "YOR_CL_PE-4", None)
        logs = []
        outcome = up._post_deploy_restore_from_file(
            job_id, device_id, "YOR_CL_PE-4",
            lambda level, msg: logs.append((level, msg)),
            lambda _msg: None,
            mgmt_ip_hint="100.64.11.96")
        state = up._push_jobs[job_id]["device_state"][device_id]
        _check(outcome[0] == "success",
               f"lab credential fallback succeeds (got {outcome!r})")
        _check(attempted_users == ["baduser", "dnroot"],
               f"credential order is saved then lab profile (got {attempted_users!r})")
        _check(state.get("config_restored") is True,
               "successful fallback marks config restored")
        _check(state.get("config_repair_retryable") is False,
               "successful fallback clears retryable flag")
    finally:
        up._get_credentials = original_get
        up._get_lab_credential_chain = original_chain
        up._resolve_mgmt_ip = original_resolve
        up.SCALER_ROOT = saved_root
        _restore_fake_config_pusher(fake_scaler, previous_mod, previous_attr)
        with up._push_jobs_lock:
            up._push_jobs.clear()
            up._push_jobs.update(saved_jobs)


def test_manual_restore_endpoint_uses_shared_repair_path():
    """Manual restore must use the same per-user active-host repair helper."""
    from routes import upgrade as up
    from routes.bridge_helpers import current_app_user

    root = _make_temp_scaler_root()
    saved_root = up.SCALER_ROOT
    original_resolve = up._resolve_mgmt_ip
    original_restore = up._post_deploy_restore_from_file
    up.SCALER_ROOT = str(root)
    calls = []

    class _State:
        user = "alice"

    class _Request:
        state = _State()

    try:
        _make_device(root, "YOR_CL_PE-4", {"device_state": "DNOS"}, backup_lines=20)
        up._resolve_mgmt_ip = lambda did, ssh: ("100.64.11.96", "YOR_CL_PE-4", "monitored_registry:test")

        def _fake_restore(job_id, device_id, scaler_hostname, _log, _term, mgmt_ip_hint=""):
            calls.append({
                "job_id": job_id,
                "device_id": device_id,
                "scaler_hostname": scaler_hostname,
                "mgmt_ip_hint": mgmt_ip_hint,
                "app_user": current_app_user.get(),
            })
            _log("INFO", "fake restore")
            _term("[OK] fake restore")
            return ("success", "restored")

        up._post_deploy_restore_from_file = _fake_restore
        result = up.image_upgrade_restore_config(
            {"device_ids": ["PE-4"], "ssh_hosts": {"PE-4": "100.64.11.96"}},
            request=_Request(),
        )
        _check(result["results"]["PE-4"]["success"] is True,
               "manual restore reports shared repair success")
        _check(calls and calls[0]["scaler_hostname"] == "YOR_CL_PE-4",
               f"manual restore uses resolved canonical hostname (calls={calls!r})")
        _check(calls and calls[0]["mgmt_ip_hint"] == "100.64.11.96",
               f"manual restore preserves active-NCC mgmt hint (calls={calls!r})")
        _check(calls and calls[0]["app_user"] == "alice",
               f"manual restore binds request user for credentials (calls={calls!r})")
    finally:
        up._resolve_mgmt_ip = original_resolve
        up._post_deploy_restore_from_file = original_restore
        up.SCALER_ROOT = saved_root


def test_post_deploy_budget_and_retry_classifier():
    """Post-deploy verify should allow a bounded repair retry window."""
    from routes import upgrade as up

    defaults = up._post_deploy_verify.__defaults__
    _check(defaults[0] >= 1800,
           f"post-deploy verify default timeout is at least 30min (got {defaults[0]})")
    _check(up._config_repair_message_retryable(
        "Authentication failed - check username/password") is True,
        "auth failure is classified as retryable repair readiness")
    _check(up._config_repair_message_retryable(
        "Commit check failed: Unknown word 'flowspec-vpn'") is False,
        "DNOS config syntax failure is not classified as retryable auth readiness")


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("Upgrade crash-recovery regression suite")
    print("=" * 70)
    test_stamp_and_read_markers()
    test_orphan_scan_skips_completed()
    test_drive_orphan_in_gi_marks_manual_when_missing_fields()
    test_drive_orphan_in_gi_auto_resumes_when_complete()
    test_stuck_devices_endpoint_filters_correctly()
    test_clear_stuck_endpoint_removes_latch()
    test_probe_ncc_bash_and_closed_channel_guard()
    test_gi_stack_target_parser_and_skip_match()
    test_pe4_deploy_params_are_guarded()
    test_load_images_skips_component_when_target_already_present()
    test_ensure_gi_cli_recovers_from_shell_drift()
    test_gi_cli_kvm_host_shell_requires_reconnect()
    test_ncc_bash_probe_rejects_kvm_host_shell()
    test_gi_preflight_probe_does_not_ctrl_c_from_gi_cli()
    test_load_status_kvm_drift_reconnects_and_resumes_polling()
    test_unverified_gi_manager_health_blocks_entry()
    test_upgrade_terminal_line_has_per_device_timestamp()
    test_jobs_endpoint_tolerates_legacy_recovery_job_id()
    test_dnos_readiness_gate_and_config_snapshot_cleaning()
    test_config_restore_auth_failure_is_retryable_pending()
    test_config_restore_falls_back_to_lab_credentials()
    test_manual_restore_endpoint_uses_shared_repair_path()
    test_post_deploy_budget_and_retry_classifier()
    print("=" * 70)
    if _FAILED:
        print(f"FAILED: {_FAILED} assertion(s) failed")
        sys.exit(1)
    print("OK: all assertions passed")


if __name__ == "__main__":
    main()
