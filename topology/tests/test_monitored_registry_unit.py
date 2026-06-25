#!/usr/bin/env python3
"""DAL unit tests for the auto-monitor reference-counted registry.

Covers the multi-user safety contract that the Phase 2 MVP design
locked in (see ``topology/docs/AUTO_MONITOR_ON_ATTACH.md`` Section 5):

  * ``upsert_device`` is field-level merge -- a re-register that doesn't
    know the platform must NOT blank the previously-stored platform.
  * ``add_reference`` is idempotent. Re-attaching the same
    (key, username, scope_type, scope_id) is a no-op (no duplicate row,
    ``attached_at`` preserved on first attach).
  * ``remove_reference`` only removes the caller's row. Two users
    attached to the same device -> alice's detach must NOT delete bob's
    reference.
  * ``would_stop_monitoring`` is true ONLY when the global refcount
    drops to zero AND the device is not ``legacy_global``.
  * ``list_devices(only_user=...)`` filters per-user correctly so the
    GET ``/api/devices/monitored`` endpoint never leaks one user's
    devices to another.

Runnable as ``python3 topology/tests/test_monitored_registry_unit.py``;
exits 0 on success, 1 on the first failed assertion. No external
dependencies beyond the stdlib + the worktree's own
``api/monitored_registry.py``.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Make the worktree's ``topology/`` importable so ``from api.monitored_registry``
# resolves without requiring the package to be installed.
HERE = Path(__file__).resolve().parent
TOPOLOGY_ROOT = HERE.parent
if str(TOPOLOGY_ROOT) not in sys.path:
    sys.path.insert(0, str(TOPOLOGY_ROOT))


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)
    print(f"ok: {msg}")


def _run_with_temp_db():
    """Drive the DAL against a throw-away SQLite file in a temp dir.

    The registry module exposes ``REGISTRY_DB_PATH`` as a module-level
    constant. The test rebinds it BEFORE calling any DAL function so
    each run gets a clean DB without touching the user's real
    ``~/.topology_shared/monitored_registry.db``.
    """
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "registry_test.db"
        # IMPORTANT: import AFTER we have a tmp path so we can rebind
        # ``REGISTRY_DB_PATH`` before ``_ensure_schema`` runs.
        from api import monitored_registry as reg
        reg.REGISTRY_DB_PATH = db_path  # type: ignore[attr-defined]

        reg._ensure_schema()
        _assert(db_path.exists(), "schema bootstrap creates the DB file")

        # ----- upsert + idempotency -------------------------------------
        first = reg.upsert_device(
            management_ip="100.64.4.99",
            serial_number="ABC123",
            hostname="DEMO-PE-9",
            platform="NCP",
            actor="alice",
        )
        _assert(first["newly_inserted"] is True, "first upsert reports newly_inserted")
        _assert(first["key"] == "100.64.4.99|ABC123",
                "key composes from <ip>|<sn>")
        _assert(first["hostname"] == "DEMO-PE-9", "hostname round-trips")
        _assert(first["platform"] == "NCP", "platform round-trips")
        _assert(first["legacy_global"] is False, "legacy flag defaults to False")

        # Second upsert from a different actor with NO platform -- must
        # preserve the previously-stored "NCP" instead of blanking it.
        second = reg.upsert_device(
            management_ip="100.64.4.99",
            serial_number="ABC123",
            hostname="DEMO-PE-9",
            platform="",
            actor="bob",
        )
        _assert(second["newly_inserted"] is False,
                "second upsert reports newly_inserted=False")
        _assert(second["platform"] == "NCP",
                "field-level merge preserves prior platform when caller omits it")

        # Re-onboarding may arrive through an active-NCC hostname while the
        # existing registry row is keyed by a chassis IP. Stable serial identity
        # must reuse the existing row and must not downgrade the canonical IP.
        via_active_ncc = reg.upsert_device(
            management_ip="demo-pe9-ncc1",
            serial_number="ABC123",
            hostname="DEMO-PE-9",
            platform="",
            actor="carol",
        )
        _assert(via_active_ncc["newly_inserted"] is False,
                "same serial through active NCC host reuses existing DB device")
        _assert(via_active_ncc["key"] == first["key"],
                "same serial preserves the existing registry key")
        _assert(via_active_ncc["management_ip"] == "100.64.4.99",
                "active NCC hostname does not overwrite canonical management IP")

        # Legacy bad rows from older onboarding builds sometimes stored the
        # typed serial/SN in management_ip with an empty serial field. A later
        # correct onboarding with that serial must repair/reuse that row rather
        # than creating a duplicate or failing as "already in DB".
        malformed = reg.upsert_device(
            management_ip="SERIAL-ONLY-1",
            serial_number="",
            hostname="DEMO-PE-10",
            platform="NCP",
            actor="alice",
        )
        repaired = reg.upsert_device(
            management_ip="demo-pe10-ncc1",
            serial_number="SERIAL-ONLY-1",
            hostname="DEMO-PE-10",
            platform="",
            actor="bob",
        )
        _assert(repaired["newly_inserted"] is False,
                "serial matching a legacy management_ip row reuses the existing DB device")
        _assert(repaired["key"] == malformed["key"],
                "legacy serial-keyed row is reused instead of duplicated")
        _assert(repaired["serial_number"] == "SERIAL-ONLY-1",
                "legacy serial-keyed row is repaired with the real serial field")

        # ----- references: per-user isolation ---------------------------
        ref_alice = reg.add_reference(
            key=first["key"], username="alice",
            scope_type="topology", scope_id="topo_a",
        )
        _assert(ref_alice["newly_attached"] is True,
                "alice's first attach is newly_attached")

        ref_alice_again = reg.add_reference(
            key=first["key"], username="alice",
            scope_type="topology", scope_id="topo_a",
        )
        _assert(ref_alice_again["newly_attached"] is False,
                "re-attach with same scope is idempotent")

        ref_bob = reg.add_reference(
            key=first["key"], username="bob",
            scope_type="topology", scope_id="topo_b",
        )
        _assert(ref_bob["newly_attached"] is True, "bob's attach is independent")

        # Both users see the device when filtering by their own name;
        # neither sees a phantom row referencing the OTHER user.
        alice_view = reg.list_devices(only_user="alice")
        bob_view = reg.list_devices(only_user="bob")
        carol_view = reg.list_devices(only_user="carol")
        _assert(len(alice_view) == 1, "alice sees one device")
        _assert(len(bob_view) == 1, "bob sees one device")
        _assert(len(carol_view) == 0,
                "carol (no references) sees zero devices -- per-user isolation")

        # Reference summary is total + per-user breakdown (the route
        # decides whether to redact the user list before responding).
        summary = reg.reference_summary(first["key"])
        _assert(summary["total"] == 2,
                "reference_summary total counts both alice + bob")
        users = sorted(r["username"] for r in summary["users"])
        _assert(users == ["alice", "bob"],
                "reference_summary lists both attaching users")

        # ----- detach: alice's detach must not remove bob's row ---------
        det_alice = reg.remove_reference(
            key=first["key"], username="alice",
            scope_type="topology", scope_id="topo_a",
        )
        _assert(det_alice["removed"] is True, "alice's detach removes a row")
        _assert(det_alice["user_references_remaining"] == 0,
                "alice has zero references left for this device")
        _assert(det_alice["references_count_total"] == 1,
                "but bob's reference is still counted in the total")
        _assert(det_alice["is_last_reference"] is False,
                "is_last_reference is False because bob is still attached")
        _assert(det_alice["would_stop_monitoring"] is False,
                "would_stop_monitoring is False while another user is attached")

        # bob is still listed by the device-listing endpoint.
        post_alice_bob_view = reg.list_devices(only_user="bob")
        _assert(len(post_alice_bob_view) == 1,
                "bob still sees the device after alice detached")
        # alice no longer sees it.
        post_alice_alice_view = reg.list_devices(only_user="alice")
        _assert(len(post_alice_alice_view) == 0,
                "alice no longer sees the device after detaching")

        # ----- last-referencer detection --------------------------------
        det_bob = reg.remove_reference(
            key=first["key"], username="bob",
            scope_type="topology", scope_id="topo_b",
        )
        _assert(det_bob["removed"] is True, "bob's detach removes the last row")
        _assert(det_bob["references_count_total"] == 0,
                "total reference count drops to zero")
        _assert(det_bob["is_last_reference"] is True,
                "is_last_reference flips true when count == 0")
        _assert(det_bob["would_stop_monitoring"] is True,
                "would_stop_monitoring true for non-legacy device at refcount 0")

        # ----- legacy_global devices NEVER trigger would_stop_monitoring -
        legacy = reg.upsert_device(
            management_ip="100.64.4.200",
            serial_number="LEGACY-PE-1",
            hostname="PE-1",
            platform="NCP",
            actor="system",
            legacy_global=True,
        )
        _assert(legacy["legacy_global"] is True,
                "legacy_global flag is honoured on insert")
        reg.add_reference(
            key=legacy["key"], username="alice",
            scope_type="topology", scope_id="topo_a",
        )
        det_legacy = reg.remove_reference(
            key=legacy["key"], username="alice",
            scope_type="topology", scope_id="topo_a",
        )
        _assert(det_legacy["is_last_reference"] is True,
                "legacy device still reports is_last_reference at refcount 0")
        _assert(det_legacy["would_stop_monitoring"] is False,
                "would_stop_monitoring stays false for legacy_global devices")

        # ----- subsystem status round-trip ------------------------------
        reg.update_subsystem_status(
            key=first["key"],
            subsystem=reg.SUBSYSTEM_SCALER_MIRROR,
            status="ok",
        )
        statuses = reg.list_subsystem_status(first["key"])
        scaler_row = [s for s in statuses if s["subsystem"] == reg.SUBSYSTEM_SCALER_MIRROR]
        _assert(len(scaler_row) == 1,
                "subsystem status is recorded after dispatch update")
        _assert(scaler_row[0]["status"] == "ok",
                "subsystem status reflects the latest update")

        # ----- audit log captures the journey ---------------------------
        audit = reg.list_audit(key=first["key"])
        actions = sorted({entry["action"] for entry in audit})
        # We expect at minimum: registered, reference_added, reference_removed.
        for needed in ("registered", reg.ACTION_REFERENCE_ADDED,
                       reg.ACTION_REFERENCE_REMOVED):
            _assert(needed in actions,
                    f"audit log captured action={needed!r}")


def main() -> int:
    try:
        _run_with_temp_db()
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - test harness safety net
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("\nALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
