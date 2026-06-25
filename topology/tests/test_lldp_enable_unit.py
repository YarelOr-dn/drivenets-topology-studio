"""Static regression checks for the device LLDP enable flow.

Run:
    PYTHONPATH="topology" python3 topology/tests/test_lldp_enable_unit.py
"""
from __future__ import annotations

import os
import re


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOPO = os.path.join(REPO_ROOT, "topology")


def _read(rel: str) -> str:
    with open(os.path.join(TOPO, rel), "r", encoding="utf-8") as f:
        return f.read()


def _case(label: str) -> None:
    print(f"\n=== {label}")


def _assert(cond: object, label: str, *, info: str = "") -> None:
    if cond:
        print(f"  ok: {label}")
        return
    print(f"  FAIL: {label}")
    if info:
        print(f"    info: {info}")
    raise SystemExit(1)


def test_lldp_enable_does_not_force_serial_as_ssh_host() -> None:
    _case("LLDP enable lets backend resolve serial when no SSH host exists")
    src = _read("topology-dnaas-helpers.js")
    _assert(
        "backendResolvedHost" in src and "ScalerAPI.getDeviceContext" in src,
        "LLDP enable asks scaler bridge for the registered backend identity first",
    )
    _assert(
        "ssh_host: backendResolvedHost" in src,
        "request body sends only an explicit backend-resolved SSH host",
    )
    _assert(
        "sshConfig.hostBackup" in src and "value !== serial" in src,
        "explicit SSH fallback fields are allowed but canvas label/serial is skipped",
    )
    _assert(
        "ssh_host: sshConfig.host || serial" not in src,
        "canvas label/serial is not forced into ssh_host",
    )


def test_lldp_backend_uses_documented_show_command_only() -> None:
    _case("LLDP backend uses documented plural show command")
    src = _read("discovery_api.py")
    _assert(
        "show lldp neighbors" in src,
        "documented show lldp neighbors command remains in use",
    )
    _assert(
        "show lldp neighbor | no-more" not in src,
        "undocumented singular show lldp neighbor fallback is gone",
    )


def test_lldp_backend_covers_physical_interface_prefixes() -> None:
    _case("LLDP backend includes xe/et physical prefixes")
    src = _read("discovery_api.py")
    _assert(
        "(?:ge|xe|et|hu|ce|qsfp)" in src,
        "physical LLDP regex includes ge/xe/et/hu/ce/qsfp prefixes",
    )


def test_lldp_commit_errors_are_failures() -> None:
    _case("LLDP backend does not report success after commit errors")
    src = _read("discovery_api.py")
    m = re.search(
        r"if 'error' in commit_output\.lower\(\).*?LLDP commit failed.*?success': False",
        src,
        re.S,
    )
    _assert(
        m is not None,
        "commit error/failed/invalid output returns success False",
    )


def test_lldp_post_handler_has_no_local_re_import() -> None:
    _case("LLDP POST handler cannot shadow module-level re")
    src = _read("discovery_api.py")
    m = re.search(r"def _do_POST_inner\(self\):(?P<body>[\s\S]*?)\n    def log_message", src)
    _assert(m is not None, "located _do_POST_inner body")
    body = m.group("body")
    _assert(
        "import re\n" not in body and "import re\r\n" not in body,
        "_do_POST_inner does not import re locally after using re.sub",
    )


def test_lldp_backend_uses_shared_resolver_for_enable() -> None:
    _case("LLDP backend resolves labels before SSH")
    src = _read("discovery_api.py")
    m = re.search(
        r"def _enable_lldp_on_device[\s\S]*?:(?P<body>[\s\S]*?)\n    def _resolve_serial_to_host",
        src,
    )
    _assert(m is not None, "located _enable_lldp_on_device body")
    body = m.group("body")
    _assert(
        "self._resolve_serial_to_host(serial)" in body,
        "LLDP enabler uses shared resolver when ssh_host is absent",
    )
    _assert(
        "candidate in (dev_mgmt, dev_serial, key_value)" in src,
        "inventory resolver can use IP-valued inventory keys/serials",
    )


def test_lldp_jobs_are_durable_and_conflict_checked() -> None:
    _case("LLDP backend persists jobs and blocks concurrent mutations")
    src = _read("discovery_api.py")
    _assert("_job_store_path" in src and "discovery_jobs.db" in src, "per-user durable job store exists")
    _assert("_load_recent_jobs()" in src, "server startup rehydrates durable jobs")
    _assert("_tcp_preflight(resolved_target" in src, "LLDP POST preflights resolved SSH target")
    _assert("_find_active_lldp_for_device(device_key)" in src, "LLDP POST checks per-device active job")
    _assert("'options': ['watch', 'queue']" in src, "conflict response exposes watch/queue choices")


def test_dnaas_resume_find_endpoints_exist() -> None:
    _case("DNAAS and Multi-BD expose find/resume endpoints")
    src = _read("discovery_api.py")
    js = _read("topology-dnaas-helpers.js")
    api = _read("scaler-api.js")
    _assert("'/api/discovery/find'" in src and "'/api/multi-bd/find'" in src, "backend find endpoints are present")
    _assert("findDnaasDiscovery" in api and "findMultiBDDiscovery" in api, "ScalerAPI exposes find helpers")
    _assert("Reattached to discovery job" in js and "Reattached to Multi-BD job" in js, "frontend polling can reattach")


def test_dnaas_fallback_api_calls_keep_auth() -> None:
    _case("DNAAS helper fallbacks keep JWT auth")
    js = _read("topology-dnaas-helpers.js")
    protected_paths = [
        "/api/sections/${sectionId}/save",
        "/api/dnaas/discovery/start",
        "/api/dnaas/discovery/status",
        "/api/dnaas/discovery/file",
        "/api/dnaas/discovery/cancel",
        "/api/dnaas/multi-bd/start",
        "/api/dnaas/multi-bd/file",
        "/api/dnaas/devices/resolve-batch",
        "/api/xray/config",
    ]
    for path in protected_paths:
        _assert(path in js, f"{path} remains present")
    _assert("this._authFetch('/api/dnaas/discovery/start'" in js, "discovery start fallback uses authFetch")
    _assert("this._authFetch(`/api/dnaas/discovery/status" in js, "discovery status fallback uses authFetch")
    _assert("this._authFetch('/api/dnaas/multi-bd/start'" in js, "multi-BD start fallback uses authFetch")
    _assert("this._authFetch('/api/dnaas/devices/resolve-batch'" in js, "resolve-batch fallback uses authFetch")
    _assert("fetch('/api/dnaas/" not in js and "fetch(`/api/dnaas/" not in js, "no raw DNAAS API fetch fallback remains")


def test_lldp_existing_db_device_uses_scaler_context_first() -> None:
    _case("LLDP reads existing registered DB device before discovery fallback")
    src = _read("topology-lldp-dialog.js")
    _assert("_registeredDeviceId" in src and "_registeredMgmtIp" in src, "LLDP dialog includes backend registered identity candidates")
    _assert("ScalerAPI.getDeviceContext(deviceId, live, sshHost" in src, "cached LLDP uses scaler bridge context first")
    _assert("ScalerAPI.getDeviceContext(deviceId, true, sshHost" in src, "refresh LLDP uses live scaler bridge context before discovery_api fallback")
    _assert("this._authFetch(url.toString()" in src and "this._authFetch('/api/dnaas/lldp-neighbors-live'" in src, "discovery fallback still uses authFetch")


def test_link_details_lldp_autofill_uses_backend_identity() -> None:
    _case("Link Details LLDP autofill uses backend identity")
    src = _read("topology-link-details.js")
    _assert("_registeredDeviceId" in src and "_registeredMgmtIp" in src, "link details considers registered backend fields")
    _assert("ScalerAPI.getDeviceContext(deviceId, false, sshHost1)" in src, "link details tries scaler context before discovery fallback")
    _assert("this._authFetch(url.toString()" in src, "link details discovery fallback uses authFetch")


if __name__ == "__main__":
    test_lldp_enable_does_not_force_serial_as_ssh_host()
    test_lldp_backend_uses_documented_show_command_only()
    test_lldp_backend_covers_physical_interface_prefixes()
    test_lldp_commit_errors_are_failures()
    test_lldp_post_handler_has_no_local_re_import()
    test_lldp_backend_uses_shared_resolver_for_enable()
    test_lldp_jobs_are_durable_and_conflict_checked()
    test_dnaas_resume_find_endpoints_exist()
    test_dnaas_fallback_api_calls_keep_auth()
    test_lldp_existing_db_device_uses_scaler_context_first()
    test_link_details_lldp_autofill_uses_backend_identity()
    print("\nAll LLDP enable regression checks passed")
