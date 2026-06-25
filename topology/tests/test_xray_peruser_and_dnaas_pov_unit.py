"""Static + functional checks for the 2026-04-26 XRAY per-user hardening
and DNAAS-POV refusal.

Three independent fixes, all guarded here:

1. **`/api/xray/run` rejects anonymous callers cleanly.** Previously
   `do_POST` only short-circuited when the caller sent a *malformed*
   Authorization header; an anonymous request (no header at all) fell
   through to `_xray_run` after `_require_xray_user` had already sent
   the 401, doing wasted server work the user could never see.

2. **`/api/xray/redeliver` requires auth.** Previously the redeliver
   endpoint had no `_require_xray_user` gate; the pcap-path realpath
   check inside the handler enforced ownership but anonymous callers
   could still trigger an SCP attempt against the legacy global config.

3. **DNAAS fabric devices cannot be a CP/DP capture POV.** A leaf/spine
   doesn't expose a DNOS shell that `live_capture.py` can SSH into, so
   the legacy `cp` / `dp` modes fail with a 600s SSH timeout. Only the
   dedicated `dnaas-dp` mode (uplink mirror via the shared sisaev
   account) is correct for those devices. The popup disables the POV
   button at render time; `_startCapture` re-checks at click time;
   `_xray_run` refuses on the backend regardless of caller. The
   keyword list MUST stay in sync between the JS popup
   (`_DNAAS_POV_KEYWORDS`) and `serve.py::_DNAAS_LABEL_KEYWORDS`.

Run with::

    PYTHONPATH="topology" python3 topology/tests/test_xray_peruser_and_dnaas_pov_unit.py
"""
from __future__ import annotations

import os
import re
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOPO = os.path.join(REPO_ROOT, "topology")
sys.path.insert(0, TOPO)


def _read(rel: str) -> str:
    p = os.path.join(TOPO, rel)
    with open(p, "r", encoding="utf-8") as f:
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


# ---------------------------------------------------------------------------
# 1. Backend: /api/xray/run + /api/xray/redeliver auth gates
# ---------------------------------------------------------------------------
def test_serve_xray_run_short_circuits_when_anonymous() -> None:
    _case("/api/xray/run returns immediately when the caller has no JWT")
    src = _read("serve.py")

    # Locate the `/api/xray/run` handler block.
    m = re.search(
        r'if path == "/api/xray/run":\s*\n'
        r'(?P<body>(?:.+\n){1,40}?)\s*if path == "/api/xray/redeliver":',
        src,
    )
    _assert(
        m is not None,
        "located the /api/xray/run handler block",
        info="anchor regex failed -- did the route move?",
    )
    body = m.group("body")
    _assert(
        "_require_xray_user()" in body,
        "handler still calls _require_xray_user() to send 401",
    )
    _assert(
        "if not username:" in body and "return" in body,
        "anonymous caller short-circuits regardless of Authorization header",
        info="previous code only returned when Authorization was present, "
             "so a no-header request leaked into _xray_run",
    )
    # Negative: ensure we no longer have the buggy combined predicate.
    _assert(
        "if not username and self.headers.get(\"Authorization\")" not in body,
        "buggy `not username and Authorization-present` predicate is gone",
    )


def test_serve_xray_redeliver_requires_auth() -> None:
    _case("/api/xray/redeliver requires an authenticated user")
    src = _read("serve.py")

    m = re.search(
        r'if path == "/api/xray/redeliver":\s*\n'
        r'(?P<body>(?:.+\n){1,80}?)\s*if path\.startswith\("/api/xray/stop/"\):',
        src,
    )
    _assert(
        m is not None,
        "located the /api/xray/redeliver handler block",
    )
    body = m.group("body")
    _assert(
        "_require_xray_user()" in body,
        "handler now calls _require_xray_user() before any work",
    )
    _assert(
        re.search(r"username,\s*_role\s*=\s*self\._require_xray_user\(\)", body) is not None,
        "username is captured so the realpath gate below can identify the caller",
    )
    _assert(
        re.search(r"if not username:\s*\n\s*return", body) is not None,
        "redeliver short-circuits on missing JWT",
    )


# ---------------------------------------------------------------------------
# 2. Backend: _xray_run refuses DNAAS-fabric devices in cp/dp modes
# ---------------------------------------------------------------------------
def test_xray_run_refuses_dnaas_label_in_cp_dp_modes() -> None:
    _case("_xray_run refuses cp/dp captures against DNAAS fabric devices")
    src = _read("serve.py")

    _assert(
        "_DNAAS_LABEL_KEYWORDS" in src,
        "DNAAS keyword list is declared on the handler class",
    )

    # Required keywords (must mirror topology-xray-popup.js _DNAAS_POV_KEYWORDS
    # AND topology-dnaas.js::isRouter). Drift between any two of them
    # silently re-opens the bug, so we hard-pin every keyword here.
    required = (
        "DNAAS", "LEAF", "SPINE", "FABRIC", "TOR",
        "AGGREGATION", "AGG-", "CORE-", "-LEAF", "-SPINE",
        "NCM", "NCF",
    )
    list_block = re.search(
        r"_DNAAS_LABEL_KEYWORDS\s*=\s*\(\s*([^)]+)\)",
        src,
        re.S,
    )
    _assert(
        list_block is not None,
        "found _DNAAS_LABEL_KEYWORDS tuple body",
    )
    list_text = list_block.group(1)
    for kw in required:
        _assert(
            f'"{kw}"' in list_text,
            f"DNAAS keyword present: {kw}",
        )

    _assert(
        "_is_dnaas_device_label" in src,
        "label classifier helper exists",
    )
    _assert(
        re.search(
            r"if self\._is_dnaas_device_label\(device_label\)\s+and\s+requested_mode\s*!=\s*['\"]dnaas-dp['\"]\s*:",
            src,
        ) is not None,
        "_xray_run refuses DNAAS-labelled devices unless mode == 'dnaas-dp'",
    )
    # Make sure the gate runs BEFORE the mac-verification gate so an
    # invalid POV is rejected with a useful message rather than a
    # generic "Mac workstation not verified" one.
    pos_dnaas = src.find("_is_dnaas_device_label(device_label)")
    pos_mac = src.find("Mac workstation not verified")
    _assert(
        0 < pos_dnaas < pos_mac,
        "DNAAS POV gate runs before the mac-verification gate",
    )


# ---------------------------------------------------------------------------
# 3. _xray_run live execution: positive + negative paths
# ---------------------------------------------------------------------------
class _StubHandler:
    """Just enough of the serve.py handler to call _xray_run() in-process.

    We don't want to spin a real HTTP server; instead we re-bind the
    methods we need from `Handler` onto a plain object, stub out the
    config readers + auth helpers, and assert on the return value.
    `_xray_run` is plain Python so this works.
    """

    headers: dict
    _last_cfg: dict

    def __init__(self, cfg=None, user="alice"):
        self.headers = {}
        self._last_cfg = cfg or {
            "script_path": "/tmp/live_capture.py",
            "credentials": {"device_user": "dnroot", "device_password": "dnroot"},
            "mac": {},
        }
        self._user = user

    def _xray_config_read(self):  # noqa: D401
        return self._last_cfg

    def _xray_user(self):
        return (self._user, "user")


def _bind_xray_run() -> tuple:
    """Lazy-import serve so its top-level monitor thread doesn't start
    just from `import serve` (the module spawns workers under
    `if __name__ == '__main__'` only, so this is safe). Returns a
    `_xray_run` callable bound to a fresh `_StubHandler`.

    `_xray_run` calls a few Handler helpers/constants. Bind them onto the
    stub class so the method works without a real HTTP request lifecycle."""
    import serve  # noqa: WPS433
    handler_cls = serve.Handler
    # Mirror the classmethod + the constants the live function reads.
    _StubHandler._is_dnaas_device_label = handler_cls._is_dnaas_device_label
    _StubHandler._xray_build_capture_filter = handler_cls._xray_build_capture_filter
    _StubHandler._xray_is_ipv4 = staticmethod(handler_cls._xray_is_ipv4)
    _StubHandler._xray_inventory_key = staticmethod(handler_cls._xray_inventory_key)
    _StubHandler._xray_load_device_inventory_index = lambda self: {}
    _StubHandler._xray_inventory_entry_host = handler_cls._xray_inventory_entry_host
    _StubHandler._xray_resolve_inventory_host = handler_cls._xray_resolve_inventory_host
    _StubHandler._xray_discover_mgmt_ip = lambda self, *names: ""
    _StubHandler._xray_resolve_device_host = handler_cls._xray_resolve_device_host
    _StubHandler._xray_resolve_dut_host = handler_cls._xray_resolve_dut_host
    _StubHandler._xray_dnaas_mirror_preflight = lambda self, _params: {
        "available": True,
        "chosen": "ge100-0/0/0",
        "leaf_host": "100.64.101.3",
        "spine_host": "100.64.100.12",
    }
    _StubHandler._DNAAS_LABEL_KEYWORDS = handler_cls._DNAAS_LABEL_KEYWORDS
    _StubHandler._XRAY_MAC_VERIFY_TTL_SECONDS = handler_cls._XRAY_MAC_VERIFY_TTL_SECONDS
    stub = _StubHandler()
    bound = handler_cls._xray_run.__get__(stub, handler_cls)
    return bound, stub, handler_cls, serve


def test_xray_run_returns_error_dict_for_dnaas_pov() -> None:
    _case("_xray_run live: cp mode against LEAF-XYZ returns an error dict")
    bound, _stub, handler_cls, serve_mod = _bind_xray_run()
    # Patch out subprocess.Popen so we never actually run live_capture.py
    # in case the gate accidentally lets the call through.
    import subprocess
    real_popen = subprocess.Popen
    subprocess.Popen = lambda *a, **kw: (_ for _ in ()).throw(
        AssertionError("Popen should not be reached for blocked DNAAS POV")
    )
    try:
        out = bound({"device": "LEAF-PE1-A", "mode": "cp", "interface": "any"})
    finally:
        subprocess.Popen = real_popen
    _assert(
        isinstance(out, dict) and "error" in out,
        "returns an error dict (not a capture_id string)",
        info=f"got: {out!r}",
    )
    _assert(
        "DNAAS" in out["error"] and "POV" in out["error"],
        "error message mentions DNAAS + POV so the user knows what to fix",
        info=f"got: {out['error']!r}",
    )


def test_xray_run_allows_dnaas_label_for_dnaas_dp_mode() -> None:
    _case("_xray_run live: dnaas-dp mode against LEAF-XYZ is NOT blocked by the label gate")
    bound, _stub, _hcls, _serve_mod = _bind_xray_run()
    # We don't actually want to run a real subprocess; intercept Popen
    # and force a fake "completed" result so we can confirm the gate
    # let us through. The test asserts on the *type* of return (string
    # capture_id), not on the subprocess behaviour itself.
    import subprocess
    real_popen = subprocess.Popen

    class _FakeProc:
        stdout = iter([])  # nothing to read
        returncode = 0

        def wait(self):
            return 0

    subprocess.Popen = lambda *a, **kw: _FakeProc()
    try:
        out = bound({
            "device": "LEAF-PE1-A",
            "mode": "dnaas-dp",
            "interface": "any",
            "output": "pcap",  # avoid mac-gate
        })
    finally:
        subprocess.Popen = real_popen
    _assert(
        isinstance(out, str),
        "dnaas-dp mode returns a capture_id string (label gate did not fire)",
        info=f"got: {out!r}",
    )


def test_xray_run_allows_non_dnaas_label() -> None:
    _case("_xray_run live: cp mode against PE-1 (non-DNAAS) is NOT blocked")
    bound, _stub, _hcls, _serve_mod = _bind_xray_run()
    import subprocess
    real_popen = subprocess.Popen

    class _FakeProc:
        stdout = iter([])
        returncode = 0

        def wait(self):
            return 0

    subprocess.Popen = lambda *a, **kw: _FakeProc()
    try:
        out = bound({
            "device": "PE-1",
            "mode": "cp",
            "interface": "any",
            "output": "pcap",
        })
    finally:
        subprocess.Popen = real_popen
    _assert(
        isinstance(out, str),
        "non-DNAAS device returns a capture_id string",
        info=f"got: {out!r}",
    )


def test_xray_backend_resolves_non_ip_dut_host_before_launch() -> None:
    _case("_xray_run resolves non-IP dut_host labels before passing them to live_capture")
    bound, stub, _hcls, _serve_mod = _bind_xray_run()
    stub._xray_discover_mgmt_ip = lambda *names: "100.64.4.205" if "RR-SA-2" in names else ""

    import subprocess
    real_popen = subprocess.Popen
    captured = {}

    class _FakeProc:
        stdout = iter([])
        returncode = 0

        def wait(self):
            return 0

    def _fake_popen(cmd, *args, **kwargs):
        captured["cmd"] = cmd
        return _FakeProc()

    subprocess.Popen = _fake_popen
    try:
        out = bound({
            "device": "RR-SA-2",
            "dut_host": "RR-SA-2",
            "mode": "cp",
            "interface": "bundle-100.215",
            "output": "pcap",
        })
    finally:
        subprocess.Popen = real_popen

    _assert(isinstance(out, str), "capture request reached helper launch")
    cmd = captured.get("cmd", [])
    _assert("--dut-host" in cmd, "helper command includes --dut-host")
    host = cmd[cmd.index("--dut-host") + 1] if "--dut-host" in cmd else ""
    _assert(
        host == "100.64.4.205",
        "non-IP DUT label is replaced with resolved management IP",
        info=f"cmd: {cmd}",
    )


# ---------------------------------------------------------------------------
# 4. Frontend: per-user authFetch + DNAAS POV gate
# ---------------------------------------------------------------------------
def test_xray_popup_uses_authfetch() -> None:
    _case("topology-xray-popup.js routes every /api/xray/* call through authFetch")
    src = _read("topology-xray-popup.js")
    # Helper exists.
    _assert(
        "function _xrayAuthFetch(" in src,
        "auth-aware fetch helper is defined at the top of the file",
    )
    _assert(
        "TopologyAuth.authFetch" in src,
        "helper delegates to window.TopologyAuth.authFetch when available",
    )
    # No raw fetch('/api/xray/...') calls remain. Bare fetch leaks the
    # JWT in multi-user mode and the backend then refuses with 401.
    bare_fetches = re.findall(r"fetch\(['`]/api/xray/", src)
    _assert(
        not bare_fetches,
        "no remaining bare fetch('/api/xray/...') calls",
        info=f"found: {bare_fetches}",
    )


def test_xray_popup_dnaas_pov_keywords_match_backend() -> None:
    _case("Frontend DNAAS POV keyword list matches the backend list")
    fe_src = _read("topology-xray-popup.js")
    be_src = _read("serve.py")

    fe_block = re.search(
        r"_DNAAS_POV_KEYWORDS\s*:\s*\[([^\]]+)\]",
        fe_src,
    )
    be_block = re.search(
        r"_DNAAS_LABEL_KEYWORDS\s*=\s*\(([^)]+)\)",
        be_src,
    )
    _assert(fe_block is not None, "frontend keyword array exists")
    _assert(be_block is not None, "backend keyword tuple exists")
    fe_kws = set(re.findall(r"'([^']+)'", fe_block.group(1)))
    be_kws = set(re.findall(r'"([^"]+)"', be_block.group(1)))
    _assert(
        fe_kws == be_kws,
        "frontend and backend keyword sets are identical",
        info=f"frontend-only: {fe_kws - be_kws}; backend-only: {be_kws - fe_kws}",
    )


def test_xray_popup_disables_dnaas_pov_button_at_render_time() -> None:
    _case("Popup show() disables a POV button when its endpoint is a DNAAS device")
    src = _read("topology-xray-popup.js")
    _assert(
        "dev1IsDnaas" in src and "dev2IsDnaas" in src,
        "DNAAS-ness of both endpoints is computed in show()",
    )
    _assert(
        re.search(r"this\._isDnaasPov\(device1\)", src) is not None
        and re.search(r"this\._isDnaasPov\(device2\)", src) is not None,
        "show() runs _isDnaasPov() on both endpoints",
    )
    _assert(
        "btn.dataset.dnaasBlocked" in src,
        "blocked POV buttons are tagged with dataset.dnaasBlocked so click handlers can refuse",
    )
    _assert(
        re.search(
            r"if\s*\(\s*dev1IsDnaas\s*&&\s*dev2IsDnaas\s*\)",
            src,
        ) is not None,
        "both-DNAAS endpoint case disables Start with a clear status",
    )
    _assert(
        "DP (DNAAS) mode" in src,
        "block message points the user at the right alternative mode",
    )


def test_xray_popup_savedpov_flips_away_from_dnaas() -> None:
    _case("show() flips a saved POV away from a DNAAS endpoint when the other side is regular")
    src = _read("topology-xray-popup.js")
    _assert(
        re.search(
            r"savedPov\s*=\s*'device2'.*dev1IsDnaas\s*&&\s*!dev2IsDnaas",
            src,
            re.S,
        ) is not None
        or re.search(
            r"savedPov\s*===\s*'device1'\s*&&\s*dev1IsDnaas\s*&&\s*!dev2IsDnaas",
            src,
        ) is not None,
        "device1 saved POV flips to device2 when device1 is DNAAS and device2 isn't",
    )
    _assert(
        re.search(
            r"savedPov\s*===\s*'device2'\s*&&\s*dev2IsDnaas\s*&&\s*!dev1IsDnaas",
            src,
        ) is not None,
        "device2 saved POV flips to device1 when device2 is DNAAS and device1 isn't",
    )


def test_xray_popup_startcapture_re_checks_dnaas_pov() -> None:
    _case("_startCapture re-checks DNAAS POV at click time (defense-in-depth)")
    src = _read("topology-xray-popup.js")
    # Find the _startCapture body and assert the gate is in there.
    m = re.search(
        r"async _startCapture\(\)\s*\{(?P<body>[\s\S]*?)\n\s+\},",
        src,
    )
    _assert(m is not None, "located _startCapture body")
    body = m.group("body")
    _assert(
        "this._isDnaasPov(device)" in body,
        "_startCapture calls _isDnaasPov(device) on the active POV",
    )
    _assert(
        "this._state.mode !== 'dnaas-dp'" in body,
        "the DNAAS gate explicitly allows dnaas-dp mode through",
    )
    # Make sure the DNAAS gate fires BEFORE the mode/health gate so the
    # user gets a precise message instead of "device not in DNOS mode".
    pos_dnaas = body.find("this._isDnaasPov(device)")
    pos_mode = body.find("DeviceModeGate.require")
    _assert(
        0 < pos_dnaas < pos_mode,
        "DNAAS POV gate fires before the device-mode gate",
    )


def test_xray_popup_row_filters_follow_active_pov() -> None:
    _case("XRAY selected-row VLAN/IP filters are only sent for the active capture POV")
    src = _read("topology-xray-popup.js")
    m = re.search(
        r"async _startCapture\(\)\s*\{(?P<body>[\s\S]*?)\n\s+\},",
        src,
    )
    _assert(m is not None, "located _startCapture body")
    body = m.group("body")
    _assert(
        "const rowMatchesPov = !!(useLinkContext && rowSide === this._state.pov);" in body,
        "_startCapture computes whether the clicked telemetry row is the active POV",
    )
    _assert(
        "link_context_filter_enabled: rowMatchesPov" in body,
        "request body records whether row-derived filters are active",
    )
    _assert(
        "auto_vlan_filter: !!(rowMatchesPov && this._state.autoVlanFilter" in body,
        "auto VLAN filtering is suppressed when the clicked row is not the active POV",
    )
    _assert(
        "ip: rowMatchesPov ? (activeSrcRow.ip || undefined) : undefined" in body,
        "row IP is not sent as a BPF host filter for the opposite POV",
    )


def test_xray_popup_uses_shared_ssh_target_picker_for_dut_host() -> None:
    _case("XRAY popup does not pass canvas labels as explicit dut_host values")
    src = _read("topology-xray-popup.js")
    m = re.search(
        r"async _startCapture\(\)\s*\{(?P<body>[\s\S]*?)\n\s+\},",
        src,
    )
    _assert(m is not None, "located _startCapture body")
    body = m.group("body")
    _assert(
        "window.TopologySshTarget.pick(device)" in body,
        "_startCapture delegates DUT target choice to the shared SSH target picker",
    )
    _assert(
        "targetPick?.source === 'serial'" in body
        and "omit dut_host and let the" in body
        and "backend resolve the device label through inventory" in body,
        "serial/label-only targets are not sent as dut_host",
    )
    _assert(
        "dutHost = (device.sshConfig && device.sshConfig.host)" not in body,
        "old direct sshConfig.host-to-dut_host assignment is gone",
    )


def test_xray_popup_dp_detection_classifies_lldp_neighbors() -> None:
    _case("XRAY DP detection separates Arista neighbors from DNAAS fabric neighbors")
    src = _read("topology-xray-popup.js")
    _assert(
        "if (this._isDnaas(neighbor)) return false;" in src,
        "Live Capture does not misclassify DN-LEAF/DNAAS neighbors as Arista",
    )
    _assert(
        "DN[-_]?LEAF" in src and "DN[-_]?SPINE" in src,
        "DNAAS-DP detection recognizes DN-LEAF / DN-SPINE LLDP names",
    )
    _assert(
        "n.neighbor_port" in src and "n.remote_port_id" in src,
        "LLDP normalization accepts cached and live remote-port key variants",
    )
    _assert(
        "fetchSide(device1, neighbors1, 'device1')" in src
        and "fetchSide(device2, neighbors2, 'device2')" in src,
        "live LLDP refresh is per-side tolerant instead of failing both buttons on one bad request",
    )
    _assert(
        "/api/xray/dnaas-mirror-preflight" in src,
        "DNAAS-DP button requires a mirror-port preflight before it is enabled",
    )
    _assert(
        "dnaasBtn.disabled = true" in src and "mirrorPreflight?.available" in src,
        "DNAAS-DP stays blocked until the leaf reports a free mirror destination",
    )
    _assert(
        "_linkDnaasEndpoint" in src
        and "source: 'canvas-link'" in src
        and "leafLabel" in src,
        "DNAAS-DP can derive leaf/source-port from the canvas link when LLDP is incomplete",
    )
    _assert(
        "dnaas_spine_host = this._dnaasInfo.mirrorPreflight.spine_host" in src
        and "dnaas_leaf_label" in src,
        "popup passes backend-resolved DNAAS spine and leaf label into /api/xray/run",
    )


def test_xray_backend_rechecks_dnaas_mirror_preflight() -> None:
    _case("XRAY backend refuses DNAAS-DP when no free mirror destination exists")
    src = _read("serve.py")
    _assert(
        'path == "/api/xray/dnaas-mirror-preflight"' in src,
        "serve.py exposes an authenticated read-only DNAAS mirror preflight endpoint",
    )
    _assert(
        'if requested_mode == "dnaas-dp":' in src
        and "_xray_dnaas_mirror_preflight" in src
        and 'params["dnaas_mirror_uplink"] = preflight["chosen"]' in src,
        "_xray_run rechecks mirror availability and pins the chosen uplink before launch",
    )
    _assert(
        "show services port-mirroring sessions | no-more" in src
        and "show config interfaces | flatten" in src,
        "mirror preflight reads live port-mirroring sessions and interface config",
    )
    _assert(
        "XRAY_SCALER_DEVICES_FILE" in src
        and "_xray_resolve_device_host" in src
        and "Could not resolve DNAAS leaf host" in src,
        "backend resolves DNAAS leaf labels/IPs through SCALER inventory before SSH",
    )
    _assert(
        "show lldp neighbors {result['chosen']} | no-more" in src
        and "show lldp neighbors interface" not in src,
        "backend uses documented DNOS LLDP detail syntax to discover the DNAAS spine",
    )
    _assert(
        'params["dnaas_leaf_host"] = preflight["leaf_host"]' in src
        and 'params["dnaas_spine_host"] = preflight["spine_host"]' in src,
        "_xray_run passes resolved leaf/spine hosts to live_capture",
    )


def test_xray_run_passes_resolved_dnaas_hosts_to_helper() -> None:
    _case("_xray_run passes preflight-resolved DNAAS leaf and spine IPs to live_capture")
    bound, _stub, _hcls, _serve_mod = _bind_xray_run()

    import subprocess
    real_popen = subprocess.Popen
    captured = {}

    class _FakeProc:
        stdout = iter([])
        returncode = 0

        def wait(self):
            return 0

    def _fake_popen(cmd, *args, **kwargs):
        captured["cmd"] = cmd
        return _FakeProc()

    subprocess.Popen = _fake_popen
    try:
        out = bound({
            "device": "PE-4",
            "mode": "dnaas-dp",
            "interface": "ge100-18/0/1",
            "output": "pcap",
            "dnaas_leaf_host": "DNAAS-LEAF-B10",
            "dnaas_leaf_label": "DNAAS-LEAF-B10",
            "dnaas_leaf_source_port": "ge100-0/0/4",
        })
    finally:
        subprocess.Popen = real_popen

    _assert(isinstance(out, str), "capture request reached helper launch")
    cmd = captured.get("cmd", [])
    for flag, expected in (
        ("--dnaas-leaf-host", "100.64.101.3"),
        ("--dnaas-spine-host", "100.64.100.12"),
        ("--dnaas-mirror-uplink", "ge100-0/0/0"),
    ):
        _assert(flag in cmd, f"helper command includes {flag}")
        value = cmd[cmd.index(flag) + 1]
        _assert(value == expected, f"{flag} value comes from backend preflight", info=f"cmd: {cmd}")


def test_xray_popup_does_not_client_timeout_mac_delivery() -> None:
    _case("XRAY Mac delivery waits for backend status instead of a fixed browser timeout")
    src = _read("topology-xray-popup.js")
    m = re.search(
        r"_updateCountdown\(btn,\s*statusEl\)\s*\{(?P<body>[\s\S]*?)\n\s+\},\n\s+_stopCapture",
        src,
    )
    _assert(m is not None, "located _updateCountdown body")
    body = m.group("body")
    _assert(
        "DELIVERY_TIMEOUT_MS" not in body,
        "browser no longer has a fixed Mac delivery timeout",
    )
    _assert(
        "Mac delivery timed out" not in body,
        "browser does not invent a Mac-unreachable error while backend is still running",
    )
    _assert(
        "_stopCapture();" not in body,
        "_updateCountdown does not stop polling during delivery phase",
    )


def test_xray_popup_surfaces_status_poll_failures() -> None:
    _case("XRAY status polling failures are surfaced instead of ignored forever")
    src = _read("topology-xray-popup.js")
    m = re.search(
        r"async _pollStatus\(\)\s*\{(?P<body>[\s\S]*?)\n\s+\},\n\s+_showMacRetryPrompt",
        src,
    )
    _assert(m is not None, "located _pollStatus body")
    body = m.group("body")
    _assert("if (!resp.ok)" in body, "non-OK status responses are treated as poll failures")
    _assert("_pollFailures" in body, "poll failures are counted")
    _assert("Lost XRAY status" in body, "user gets a visible status-lost error")


def test_xray_mac_delivery_has_explicit_final_state() -> None:
    _case("XRAY Mac output is not green-complete without delivery confirmation")
    popup = _read("topology-xray-popup.js")
    serve = _read("serve.py")
    _assert(
        "mac_delivery_status" in serve
        and "mac_delivery_unconfirmed" in serve
        and "\"unconfirmed\"" in serve,
        "backend records explicit unconfirmed Mac delivery without marking saved pcaps as failed",
    )
    _assert(
        "deliveryStatus = data.mac_delivery_status" in popup,
        "popup reads explicit backend Mac delivery state",
    )
    _assert(
        "deliveryStatus === 'failed'" in popup
        and "deliveryStatus !== 'delivered'" in popup,
        "popup blocks green completion unless Mac delivery is delivered",
    )
    _assert(
        "_showMacRetryPrompt(status, data.local_pcap_path || data.pcap_path, { failed: false })" in popup
        and "retry delivery or download" in popup,
        "popup shows retry/download prompt for unconfirmed saved pcaps",
    )
    _assert(
        "Capture is temporarily available" in popup
        and "Temporary server file:" in popup
        and "server-side capture was cleaned up" in popup,
        "popup reflects ephemeral non-Yarel pcap retention",
    )
    _assert(
        "Capture finished, but Mac delivery is still not confirmed" not in popup,
        "popup no longer leaves a stale waiting message after backend completion",
    )
    _assert(
        "data.error && !data.status" in popup,
        "poller does not turn legitimate backend error status into status-lost noise",
    )
    _assert(
        "_requested_duration" in serve
        and "early_exit" in serve
        and "before requested" in serve,
        "backend rejects captures that exit before requested duration",
    )
    _assert(
        "_last_meaningful_output" in serve
        and "f\": {detail}\" if detail else \"\"" in serve,
        "backend includes the meaningful helper output with exit-code errors",
    )
    _assert(
        "_showCaptureError(status, data)" in popup
        and "output_lines" in popup
        and "Fatal" not in popup,
        "popup renders backend output lines for failed captures",
    )


def test_xray_non_yarel_pcaps_are_ephemeral() -> None:
    _case("XRAY backend keeps server-side pcaps only for Yarel")
    src = _read("serve.py")
    _assert("def should_retain_pcap(username):" in src, "retention helper is explicit")
    _assert("_YAREL_PCAP_RETAIN_USERS" in src and '"yarel"' in src and '"yor"' in src, "Yarel/yor aliases are the only retain allowlist")
    _assert("return normalized in _YAREL_PCAP_RETAIN_USERS" in src, "anonymous/default users do not retain pcaps")
    _assert('"_pcap_ephemeral": not retain_pcap' in src, "capture entries mark non-Yarel pcaps ephemeral")
    _assert("_xray_cleanup_capture_pcaps(entry, \"ephemeral_capture_finished\")" in src, "non-Yarel completed/failed captures clean server pcaps")
    _assert("_xray_schedule_ephemeral_cleanup(entry, \"ephemeral_awaiting_download\")" in src, "non-Yarel browser downloads get bounded temporary retention")
    _assert("_xray_cleanup_capture_pcaps(entry, \"ephemeral_download_served\")" in src, "download endpoint deletes non-Yarel pcaps after sending")
    _assert("\"ephemeral_redeliver_attempt\"" in src, "redelivery attempts delete non-Yarel pcaps after Mac copy attempt")


def test_xray_mac_delivery_uses_fast_poll_and_step_progress() -> None:
    _case("XRAY Mac delivery polls fast and surfaces granular sub-steps")
    popup = _read("topology-xray-popup.js")
    serve = _read("serve.py")
    # Backend: granular sub-step field is plumbed end-to-end.
    _assert(
        "mac_delivery_step" in serve
        and "_xray_promote_step" in serve
        and "opening_wireshark" in serve
        and "sftp_done" in serve,
        "backend tracks granular Mac delivery sub-steps",
    )
    _assert(
        "\"mac_delivery_step\": entry.get(\"mac_delivery_step\", \"queued\")" in serve,
        "/api/xray/status surfaces the current sub-step",
    )
    # Frontend: poll cadence tightens once delivery is in progress, and the
    # countdown-zero handler immediately polls and tightens cadence so the
    # UI flips to "Wireshark opened" within ~500ms instead of 2000ms.
    _assert(
        "_setPollCadence" in popup
        and "this._setPollCadence(500)" in popup,
        "popup defines a fast-poll cadence helper for the Mac-delivery phase",
    )
    _assert(
        popup.count("this._setPollCadence(500)") >= 2,
        "popup tightens cadence both on backend in_progress AND when local countdown hits 0",
    )
    _assert(
        "this._pollStatus();" in popup
        and "_deliveryStartedAt = Date.now();" in popup,
        "popup forces an immediate poll the instant the local countdown hits 0",
    )
    _assert(
        "_renderDeliveryProgress" in popup
        and "Open Wireshark" in popup
        and "Pcap copied" in popup,
        "popup renders a granular delivery step strip with chips",
    )


def test_xray_disabled_dp_modes_explain_themselves() -> None:
    _case("Disabled DP / DP (DNAAS) mode buttons explain why on click")
    popup = _read("topology-xray-popup.js")
    _assert(
        "_explainDisabledMode" in popup,
        "popup defines a per-button explanation helper for disabled DP modes",
    )
    _assert(
        "Live Capture (DP) unavailable" in popup
        and "DP (DNAAS) unavailable" in popup,
        "explanation distinguishes DP vs DP (DNAAS)",
    )
    _assert(
        "this._dnaasInfo" in popup
        and "preflight" in popup
        and "DNAAS mirror preflight" in popup,
        "DNAAS-DP explanation cites the mirror preflight reason",
    )
    _assert(
        "click that POV header to switch sides" in popup,
        "DP explanation suggests switching POV when the other side has Arista",
    )
    _assert(
        "modeRow.addEventListener" in popup,
        "popup catches clicks on disabled mode buttons via the parent row delegate",
    )


def test_xray_canvas_halo_is_runtime_bound_and_not_persisted() -> None:
    _case("XRAY canvas halo is runtime-bound and stripped from persisted topology state")
    popup = _read("topology-xray-popup.js")
    drawing = _read("topology-link-drawing.js")
    file_ops = _read("topology-file-ops.js")
    files = _read("topology-files.js")
    topo = _read("topology.js")

    _assert(
        "_isXrayCaptureRenderActive" in drawing,
        "link renderer has an explicit XRAY runtime gate",
    )
    _assert(
        "editor._xrayCapturing === link.id" in drawing
        and "window.XrayPopup.isOpenForLink" in drawing,
        "renderer only shows the halo for the live capture or live popup link",
    )
    _assert(
        "link._xrayCaptureActive)" not in drawing
        and "!link._xrayCaptureActive" not in drawing,
        "renderer no longer trusts the persisted _xrayCaptureActive flag",
    )
    _assert(
        "editor.getObjectById?.(link.device1)" in drawing
        and "editor.getObjectById?.(link.device2)" in drawing,
        "halo rendering is bound to valid live endpoint devices",
    )
    _assert(
        "finalStartX, finalStartY" in drawing
        and "bezierCurveTo(cp1x, cp1y, cp2x, cp2y, finalEndX, finalEndY)" in drawing
        and "getScreenStableStrokeWidth(8, 6)" in drawing,
        "halo follows rendered link geometry with zoom-stable stroke/dash widths",
    )
    _assert(
        "isOpenForLink(editor, link)" in popup,
        "XRAY popup exposes a live link ownership check for drawing",
    )
    for src_name, src in (
        ("topology-file-ops.js", file_ops),
        ("topology-files.js", files),
        ("topology.js", topo),
    ):
        _assert(
            "delete copy._xrayCaptureActive" in src or "delete obj._xrayCaptureActive" in src,
            f"{src_name} strips stale XRAY capture flags from saved/loaded state",
        )


# ---------------------------------------------------------------------------
# 5. Cache-buster bump so users actually fetch the new XRAY popup
# ---------------------------------------------------------------------------
def test_index_html_xray_popup_cache_buster_is_fresh() -> None:
    _case("index.html bumps the topology-xray-popup.js cache-buster")
    src = _read("index.html")
    m = re.search(
        r'topology-xray-popup\.js\?v=([^"]+)',
        src,
    )
    _assert(m is not None, "found topology-xray-popup.js cache-buster query")
    tag = m.group(1)
    # Either a 202604xx/2026-04 dated tag with a per-fix suffix, or a
    # future 202605+/2026-05+ tag. We only refuse strictly-stale tags.
    _assert(
        re.match(r"^2026(04|05|06)|^202604|^202605|^202606", tag) is not None,
        "cache-buster tag is on or after 2026-04",
        info=f"tag: {tag}",
    )
    _assert(
        "peruser" in tag or "dnaas-pov" in tag or "xray" in tag or "r" in tag,
        "cache-buster carries a per-fix suffix so reviewers see the bump",
        info=f"tag: {tag}",
    )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def main() -> int:
    test_xray_mac_delivery_uses_fast_poll_and_step_progress()
    test_xray_disabled_dp_modes_explain_themselves()
    test_xray_canvas_halo_is_runtime_bound_and_not_persisted()
    test_serve_xray_run_short_circuits_when_anonymous()
    test_serve_xray_redeliver_requires_auth()
    test_xray_run_refuses_dnaas_label_in_cp_dp_modes()
    test_xray_run_returns_error_dict_for_dnaas_pov()
    test_xray_run_allows_dnaas_label_for_dnaas_dp_mode()
    test_xray_run_allows_non_dnaas_label()
    test_xray_backend_resolves_non_ip_dut_host_before_launch()
    test_xray_popup_uses_authfetch()
    test_xray_popup_dnaas_pov_keywords_match_backend()
    test_xray_popup_disables_dnaas_pov_button_at_render_time()
    test_xray_popup_savedpov_flips_away_from_dnaas()
    test_xray_popup_startcapture_re_checks_dnaas_pov()
    test_xray_popup_row_filters_follow_active_pov()
    test_xray_popup_uses_shared_ssh_target_picker_for_dut_host()
    test_xray_popup_dp_detection_classifies_lldp_neighbors()
    test_xray_backend_rechecks_dnaas_mirror_preflight()
    test_xray_run_passes_resolved_dnaas_hosts_to_helper()
    test_xray_popup_does_not_client_timeout_mac_delivery()
    test_xray_popup_surfaces_status_poll_failures()
    test_xray_mac_delivery_has_explicit_final_state()
    test_xray_non_yarel_pcaps_are_ephemeral()
    test_index_html_xray_popup_cache_buster_is_fresh()
    print("\nAll XRAY per-user + DNAAS-POV checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
