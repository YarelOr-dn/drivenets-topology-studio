#!/usr/bin/env python3
"""HTTP-level unit tests for the auto-monitor endpoints.

Brings up a minimal FastAPI app with ONLY ``routes.monitored_devices.router``
mounted plus a tiny test middleware that stamps ``request.state.user``
from an ``X-Test-User`` header. The real JWT middleware lives in
``scaler_bridge.py`` and pulls the same ``request.state.user`` slot, so
this test exercises the route handlers' multi-user contract (per-user
isolation, refcount math, last-referencer detection, leakage redaction)
without dragging in the SSH stack, Network Mapper MCP, or the live
SCALER ``devices.json``.

The two heavy collaborators (``verify_credentials_inline`` and
``monitored_dispatch``) are monkey-patched at module level BEFORE the
router is imported so the routes pick up the stubs. The verify stub
returns a deterministic OK payload; the dispatch stub no-ops.

Runnable as ``python3 topology/tests/test_monitored_endpoints_unit.py``;
exits 0 on success, 1 on the first failed assertion.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOPOLOGY_ROOT = HERE.parent
if str(TOPOLOGY_ROOT) not in sys.path:
    sys.path.insert(0, str(TOPOLOGY_ROOT))


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)
    print(f"ok: {msg}")


def _build_app(tmp_db: Path):
    """Construct a fresh FastAPI app with a clean registry DB.

    All collaborators are stubbed:
      * ``api.monitored_registry.REGISTRY_DB_PATH`` -> tmp file
      * ``routes.devices.verify_credentials_inline`` -> always-OK stub
      * ``routes.monitored_dispatch.bring_up`` / ``tear_down`` -> no-op
    """
    from api import monitored_registry as reg
    reg.REGISTRY_DB_PATH = tmp_db  # type: ignore[attr-defined]
    reg._ensure_schema()

    from routes import devices as devices_module
    from routes import monitored_dispatch as dispatch_module

    def _fake_verify_credentials_inline(device_id, body, app_user):
        host = (body or {}).get("host", "")
        # Optional per-test override -- the test sets this attribute to
        # control the stub's response from outside.
        override = getattr(_fake_verify_credentials_inline, "next_response", None)
        if override is not None:
            _fake_verify_credentials_inline.next_response = None
            return override
        return {
            "ok": True,
            "actual_hostname": device_id,
            "platform": "NCP",
            "is_cluster": False,
            "raw_verify": {
                "actual_hostname": device_id,
                "platform": "NCP",
                "serial": f"SN-{device_id}",
            },
            "raw_probe": {
                "platform": "NCP",
                "serial": f"SN-{device_id}",
                "cluster": {"is_cluster": False},
            },
        }

    devices_module.verify_credentials_inline = _fake_verify_credentials_inline

    def _no_op_dispatch(record, *_args, **_kwargs):
        return [
            {"subsystem": "scaler_devices_mirror", "ok": True, "skipped": True},
            {"subsystem": "network_mapper", "ok": True, "skipped": True},
        ]
    dispatch_module.bring_up = _no_op_dispatch
    dispatch_module.tear_down = _no_op_dispatch

    # Import the router AFTER stubs are in place; the module captures
    # the verify_credentials_inline reference at import time.
    if "routes.monitored_devices" in sys.modules:
        del sys.modules["routes.monitored_devices"]
    from routes import monitored_devices as routes_module
    routes_module.verify_credentials_inline = _fake_verify_credentials_inline
    routes_module.monitored_dispatch = dispatch_module

    def _fake_live_context(device_id, host, app_user, identity_guard=None):
        override = getattr(_fake_live_context, "next_response", None)
        if override is not None:
            _fake_live_context.next_response = None
            return override
        return {
            "device_id": device_id,
            "hostname": device_id,
            "resolved_ip": host,
            "mgmt_ip": host,
            "timestamp": "2026-05-07T09:00:00",
            "identity": {
                "canvas_label": device_id,
                "config_hostname": device_id,
                "serial": f"SN-{device_id}",
                "mgmt_ip": host,
                "ssh_host": host,
                "scaler_ids": [device_id],
                "inventory_keys": [],
                "hostname_mismatch": False,
            },
            "lldp": [{"local": "ge0", "neighbor": "PEER-1", "remote": "ge1"}],
            "stack": [{"name": "DNOS", "current": "19.2.13.1"}],
            "git_commit": "abcdef1",
            "device_state": "DNOS",
            "stack_fetched_at": "2026-05-07T09:00:00Z",
            "git_commit_fetched_at": "2026-05-07T09:00:00Z",
        }
    routes_module._fetch_live_onboarding_context = _fake_live_context

    class _FakeUserStore:
        def has_role_or_higher(self, username, min_role):
            return username != "viewer_only"

    routes_module.user_store = _FakeUserStore()

    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    app = FastAPI()

    @app.middleware("http")
    async def _test_user_middleware(request: Request, call_next):
        # Mirror the production bridge JWT middleware: reject every
        # request that does NOT carry an authenticated principal. The
        # real bridge does this with a JWT signature check; the test
        # stand-in does it with an explicit X-Test-User header.
        user = request.headers.get("X-Test-User", "").strip()
        if not user:
            return JSONResponse(status_code=401,
                                content={"detail": "Authentication required"})
        request.state.user = user
        request.state.role = "engineer"
        return await call_next(request)

    app.include_router(routes_module.router)
    return app, _fake_verify_credentials_inline, _fake_live_context, reg


def _user_headers(name: str) -> dict:
    return {"X-Test-User": name}


def main() -> int:
    from fastapi.testclient import TestClient

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "registry.db"
        app, fake_verify, fake_live_context, reg = _build_app(db_path)
        client = TestClient(app)

        # ----- 401 when no user header is set -----------------------
        resp = client.get("/api/devices/monitored")
        _assert(resp.status_code == 401,
                f"unauthenticated GET monitored returns 401 (got {resp.status_code})")

        resp = client.post("/api/devices/verify-and-register",
                           json={"device_id": "PE-9", "host": "100.64.4.99"})
        _assert(resp.status_code == 401,
                f"unauthenticated verify-and-register returns 401 (got {resp.status_code})")

        resp = client.post(
            "/api/devices/verify-and-register",
            json={"device_id": "PE-9", "host": "100.64.4.99"},
            headers=_user_headers("viewer_only"),
        )
        _assert(resp.status_code == 403,
                f"viewer verify-and-register returns 403 (got {resp.status_code})")

        # ----- alice: verify-and-register a device ------------------
        resp = client.post(
            "/api/devices/verify-and-register",
            json={
                "device_id": "PE-9",
                "host": "100.64.4.99",
                "user": "dnroot",
                "password": "dnroot",
            },
            headers=_user_headers("alice"),
        )
        _assert(resp.status_code == 200,
                f"alice verify-and-register 200 (got {resp.status_code} {resp.text})")
        body = resp.json()
        _assert(body.get("ok") is True, "verify-and-register ok=True")
        _assert(body.get("registered") is True, "verify-and-register registered=True")
        _assert(body.get("management_ip") == "100.64.4.99",
                "verify-and-register returns registered management_ip")
        _assert(body.get("registered_device_id") == "PE-9",
                "verify-and-register returns registered backend identity")
        _assert(body.get("newly_registered") is True,
                "first verify-and-register reports newly_registered")
        _assert(body.get("onboarding_phase") == "api_ready",
                "verify-and-register reports API-ready onboarding phase")
        _assert(body.get("capabilities", {}).get("lldp") is True,
                "verify-and-register returns LLDP capability")
        _assert(body.get("capabilities", {}).get("health") is True,
                "verify-and-register returns health monitoring capability")
        _assert(body.get("device_context", {}).get("canonical", {}).get("management_ip") == "100.64.4.99",
                "verify-and-register returns canonical device context")
        _assert(body.get("onboarding_metadata", {}).get("status") == "reliable",
                "verify-and-register returns reliable backend-validated metadata")
        _assert(body.get("onboarding_metadata", {}).get("source") == "backend-onboarding",
                "metadata source is backend onboarding")
        _assert(body.get("onboarding_metadata", {}).get("stack", [{}])[0].get("name") == "DNOS",
                "validated stack metadata is attached to onboarding response")
        _assert(body.get("onboarding_metadata", {}).get("git_commit") == "abcdef1",
                "validated git metadata is attached to onboarding response")
        _assert(body.get("metadata_validation", {}).get("reliable") is True,
                "metadata validation summary is reliable")
        _assert(isinstance(body.get("monitoring_options", {}).get("subsystems"), list),
                "verify-and-register returns monitoring subsystem options")
        _assert(body.get("references_count_total") == 1,
                "after alice attaches, total ref count = 1")
        _assert(body.get("references_user_count") == 1,
                "after alice attaches, alice's ref count = 1")
        alice_key = body.get("key")
        _assert("100.64.4.99|" in alice_key, "key uses <ip>|<sn> form")

        # ----- bob: same device, different user -> ref+1 -----------
        resp = client.post(
            "/api/devices/verify-and-register",
            json={
                "device_id": "PE-9",
                "host": "100.64.4.99",
            },
            headers=_user_headers("bob"),
        )
        _assert(resp.status_code == 200, "bob verify-and-register 200")
        bob_body = resp.json()
        _assert(bob_body.get("newly_registered") is False,
                "second verify-and-register on same device is NOT newly_registered")
        _assert(bob_body.get("device_context", {}).get("monitoring_options", {}).get("state") == "ready",
                "existing DB device reuse still returns ready monitoring context")
        _assert(bob_body.get("references_count_total") == 2,
                "total ref count is 2 after bob attaches")
        _assert(bob_body.get("references_user_count") == 1,
                "bob's per-user ref count is 1, not 2 (no leakage)")

        # ----- GET /api/devices/monitored -- per-user isolation ----
        resp = client.get("/api/devices/monitored", headers=_user_headers("alice"))
        _assert(resp.status_code == 200, "alice GET monitored 200")
        alice_list = resp.json()
        _assert(alice_list.get("count") == 1, "alice sees 1 device")

        resp = client.get("/api/devices/monitored", headers=_user_headers("carol"))
        _assert(resp.status_code == 200, "carol GET monitored 200")
        carol_list = resp.json()
        _assert(carol_list.get("count") == 0,
                "carol (no references) sees ZERO devices -- no leakage")

        # ----- GET /api/devices/monitored/{ip} 404 for non-attached --
        resp = client.get("/api/devices/monitored/100.64.4.99",
                          headers=_user_headers("carol"))
        _assert(resp.status_code == 404,
                "non-attached carol gets 404 -- existence redacted")

        resp = client.get("/api/devices/monitored/100.64.4.99",
                          headers=_user_headers("bob"))
        _assert(resp.status_code == 200, "bob gets the device he attached")
        detail = resp.json()
        _assert(detail.get("references_user_count") == 1,
                "single-device GET reports bob's own user_count=1")
        _assert(detail.get("references_count_total") == 2,
                "single-device GET reports total=2")
        _assert("scopes_for_caller" in detail,
                "single-device GET exposes scopes_for_caller (no other users' scopes)")

        # ----- detach: alice's detach must NOT affect bob ------------
        resp = client.delete("/api/devices/monitored/100.64.4.99/attach",
                             headers=_user_headers("alice"))
        _assert(resp.status_code == 200, "alice DELETE attach 200")
        d_alice = resp.json()
        _assert(d_alice.get("removed") is True, "alice's row was removed")
        _assert(d_alice.get("references_count_total") == 1,
                "after alice detach, total drops to 1 (bob still attached)")
        _assert(d_alice.get("would_stop_monitoring") is False,
                "would_stop_monitoring False while bob still attached")

        # bob still sees the device
        resp = client.get("/api/devices/monitored/100.64.4.99",
                          headers=_user_headers("bob"))
        _assert(resp.status_code == 200,
                "bob still sees the device after alice's detach")

        # alice no longer sees it
        resp = client.get("/api/devices/monitored/100.64.4.99",
                          headers=_user_headers("alice"))
        _assert(resp.status_code == 404,
                "alice's detach removes the device from her view")

        # ----- attach idempotency on a fresh re-attach --------------
        resp = client.post("/api/devices/monitored/100.64.4.99/attach",
                           json={"scope_type": "topology", "scope_id": "topo_a1"},
                           headers=_user_headers("alice"))
        _assert(resp.status_code == 200, "alice POST attach 200")
        a_attach = resp.json()
        _assert(a_attach.get("newly_attached") is True,
                "alice's re-attach reports newly_attached")
        _assert(a_attach.get("references_user_count") == 1,
                "alice re-attach -> 1 user-ref again")

        # Idempotent re-attach with SAME scope -> not newly_attached
        resp = client.post("/api/devices/monitored/100.64.4.99/attach",
                           json={"scope_type": "topology", "scope_id": "topo_a1"},
                           headers=_user_headers("alice"))
        _assert(resp.status_code == 200, "alice idempotent POST attach 200")
        a_attach2 = resp.json()
        _assert(a_attach2.get("newly_attached") is False,
                "second identical attach is idempotent (newly_attached=False)")

        # ----- detach BOTH -> would_stop_monitoring trips true ------
        # bob first
        resp = client.delete("/api/devices/monitored/100.64.4.99/attach",
                             headers=_user_headers("bob"))
        d_bob = resp.json()
        _assert(d_bob.get("references_count_total") == 1,
                "after bob detach, only alice's reattach remains")
        _assert(d_bob.get("would_stop_monitoring") is False,
                "still false because alice is attached")
        # alice second
        resp = client.delete("/api/devices/monitored/100.64.4.99/attach",
                             params={"scope_type": "topology", "scope_id": "topo_a1"},
                             headers=_user_headers("alice"))
        d_alice2 = resp.json()
        _assert(d_alice2.get("references_count_total") == 0,
                "after alice second detach, total = 0")
        _assert(d_alice2.get("is_last_reference") is True,
                "is_last_reference flips true at refcount 0")
        _assert(d_alice2.get("would_stop_monitoring") is True,
                "would_stop_monitoring trips true on the last detach (non-legacy)")

        # ----- failed verify must NOT register the device ----------
        fake_verify.next_response = {
            "ok": False,
            "reason": "auth_failed",
            "message": "permission denied",
        }
        resp = client.post(
            "/api/devices/verify-and-register",
            json={"device_id": "PE-99", "host": "100.64.4.199"},
            headers=_user_headers("alice"),
        )
        _assert(resp.status_code == 200,
                "verify-and-register returns 200 even when verify fails (carries reason)")
        fail_body = resp.json()
        _assert(fail_body.get("ok") is False,
                "failed verify response carries ok=False")
        _assert(fail_body.get("registered") is False,
                "failed verify does NOT register the device (multi-user safety)")
        # Confirm DAL has no row for the failed IP
        from api import monitored_registry as reg2
        rec = reg2.find_by_ip("100.64.4.199")
        _assert(rec is None,
                "DAL has zero rows for the failed-verify IP")

        # ----- live metadata identity conflict must not be trusted ---
        fake_live_context.next_response = {
            "device_id": "PE-9",
            "hostname": "PE-9",
            "resolved_ip": "100.64.4.250",
            "mgmt_ip": "100.64.4.250",
            "identity": {
                "canvas_label": "PE-9",
                "config_hostname": "PE-9",
                "serial": "SN-PE-9",
                "mgmt_ip": "100.64.4.250",
                "ssh_host": "100.64.4.250",
                "scaler_ids": ["PE-9"],
                "inventory_keys": [],
            },
            "lldp": [{"local": "bad", "neighbor": "STALE", "remote": "bad"}],
            "stack": [{"name": "DNOS", "current": "stale"}],
            "git_commit": "badcafe",
            "device_state": "DNOS",
        }
        resp = client.post(
            "/api/devices/verify-and-register",
            json={"device_id": "PE-9", "host": "100.64.4.99"},
            headers=_user_headers("alice"),
        )
        _assert(resp.status_code == 200, "metadata-conflict verify-and-register returns 200")
        conflict_body = resp.json()
        _assert(conflict_body.get("registered") is True,
                "metadata conflict does not undo verified registry attach")
        _assert(conflict_body.get("onboarding_metadata", {}).get("status") == "conflict",
                "metadata conflict is explicit")
        _assert(conflict_body.get("onboarding_metadata", {}).get("reliable") is False,
                "conflicting metadata is not reliable")
        _assert(conflict_body.get("onboarding_metadata", {}).get("lldp") == [],
                "conflicting LLDP is not returned for frontend mirroring")

        # ----- cluster active-NCC IP should reuse existing cluster row ---
        fake_verify.next_response = {
            "ok": True,
            "actual_hostname": "CL-9",
            "platform": "CL-86",
            "is_cluster": True,
            "active_ncc_ip": "100.64.4.151",
            "active_ncc_vm": "kvm999-cl9-ncc1",
            "raw_verify": {
                "actual_hostname": "CL-9",
                "platform": "CL-86",
                "serial": "SN-CL9",
            },
            "raw_probe": {
                "platform": "CL-86",
                "serial": "SN-CL9",
                "cluster": {
                    "is_cluster": True,
                    "active_ncc_ip": "100.64.4.151",
                    "active_ncc_vm": "kvm999-cl9-ncc1",
                    "ncc_vms": [{"name": "kvm999-cl9-ncc1", "ip": "100.64.4.151"}],
                },
            },
        }
        resp = client.post(
            "/api/devices/verify-and-register",
            json={"device_id": "CL-9", "host": "100.64.4.150"},
            headers=_user_headers("alice"),
        )
        _assert(resp.status_code == 200, "cluster chassis verify-and-register 200")
        chassis_body = resp.json()
        cluster_key = chassis_body.get("key")
        _assert(chassis_body.get("management_ip") == "100.64.4.150",
                "cluster row uses chassis management IP")
        _assert("100.64.4.151" in (chassis_body.get("cluster_ncc_ips") or []),
                "cluster row records active NCC member IP")

        fake_verify.next_response = {
            "ok": True,
            "actual_hostname": "CL-9",
            "platform": "CL-86",
            "is_cluster": True,
            "active_ncc_ip": "100.64.4.151",
            "active_ncc_vm": "kvm999-cl9-ncc1",
            "raw_verify": {
                "actual_hostname": "CL-9",
                "platform": "CL-86",
                "serial": "SN-CL9",
            },
            "raw_probe": {
                "platform": "CL-86",
                "serial": "SN-CL9",
                "cluster": {
                    "is_cluster": True,
                    "active_ncc_ip": "100.64.4.151",
                    "active_ncc_vm": "kvm999-cl9-ncc1",
                    "ncc_vms": [{"name": "kvm999-cl9-ncc1", "ip": "100.64.4.151"}],
                },
            },
        }
        resp = client.post(
            "/api/devices/verify-and-register",
            json={"device_id": "NCP-1", "host": "100.64.4.151"},
            headers=_user_headers("bob"),
        )
        _assert(resp.status_code == 200, "active-NCC member onboarding 200")
        member_body = resp.json()
        _assert(member_body.get("key") == cluster_key,
                "active-NCC member IP reuses existing cluster registry row")
        _assert(member_body.get("management_ip") == "100.64.4.150",
                "member IP onboarding preserves chassis management IP")
        rows = reg.list_devices()
        cluster_rows = [r for r in rows if r.get("hostname") == "CL-9"]
        _assert(len(cluster_rows) == 1,
                "active-NCC onboarding does not create a duplicate cluster row")

    print("\nALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # pragma: no cover
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
