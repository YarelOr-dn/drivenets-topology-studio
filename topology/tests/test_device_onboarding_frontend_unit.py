"""Static regression checks for premium device onboarding UX/API contract.

Run:
    python3 topology/tests/test_device_onboarding_frontend_unit.py
"""
from __future__ import annotations

from pathlib import Path


TOPO = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (TOPO / rel).read_text(encoding="utf-8")


def _assert(cond: object, label: str) -> None:
    if not cond:
        raise AssertionError(label)
    print(f"ok: {label}")


def test_scaler_api_uses_auth_fetch_for_protected_calls() -> None:
    src = _read("scaler-api.js")
    _assert("TopologyAuth.authFetch" in src, "ScalerAPI delegates to TopologyAuth.authFetch")
    _assert("verifyAndRegister(deviceId, host, user, password" in src, "verifyAndRegister helper exists")
    _assert("await fetch(this._api" not in src, "ScalerAPI has no raw fetch(this._api...) calls")
    _assert("await fetch(url" not in src, "ScalerAPI has no raw fetch(url...) calls")


def test_ssh_dialog_has_premium_onboarding_state_machine() -> None:
    src = _read("topology-ssh-dialog.js")
    _assert("Step 1/4: verifying SSH" in src, "onboarding shows verify/register/DB/API progress")
    _assert("SSH verified, but backend DB registration did not complete" in src, "no green success when DB registration fails")
    _assert("const hasBackendRegistration = !!(" in src and "result.device_context?.canonical?.key" in src,
            "existing backend DB identity is accepted as onboarding success")
    _assert("Existing DB device reused for this user" in src, "existing DB device reuse is a success")
    _assert("friendlyBridgeError" in src, "bridge/auth/role failures are mapped to user-friendly messages")
    _assert("applyCanonicalOnboardingContext" in src, "onboarding applies backend canonical context before toolbar refresh")
    _assert("result.onboarding_metadata || result.device_context?.validated_metadata" in src, "onboarding consumes backend-validated metadata envelope")
    _assert("metadataReliable" in src, "frontend gates metadata mirroring on reliable backend validation")
    _assert("_clearUnreliableOnboardingMetadata" in src, "unreliable onboarding metadata clears stale identity-bound cache")
    _assert("stale LLDP, stack, and git cache were cleared" in src, "onboarding warns when stale metadata is quarantined")
    _assert("Retry onboarding" in src and "Refresh device context" in src, "onboarding provides specific retry actions for metadata conflicts")
    _assert("Do not start a separate" in src and "frontend context hydrate" in src, "onboarding avoids stale frontend context hydrate")
    _assert("_registeredDeviceId" in src and "_registeredMgmtIp" in src, "frontend stores canonical backend identity after onboarding")
    _assert("device:context-updated" in src, "frontend refreshes device state from backend truth after onboarding")
    _assert("applyHostnameCanvasMismatch(device, actualConfigHostname" in src, "backend onboarding immediately checks device hostname against canvas label")
    _assert("source: 'backend-validated-onboarding'" in src, "onboarding mismatch check is sourced to backend validation")
    _assert("_newIdentityToken(host, 'save')" in src, "save verification uses a scoped identity token")
    _assert("showCanvasHostnameMismatchPrompt" in src, "onboarding shows the hostname mismatch prompt after a verified save")


def test_ssh_dialog_prefers_registered_identity_for_console_and_probe() -> None:
    src = _read("topology-ssh-dialog.js")
    _assert("const deviceId = device._registeredDeviceId" in src, "SSH dialog API identity starts with registered device id")
    _assert("|| device._registeredHostname" in src, "SSH dialog falls back to registered hostname before canvas label")
    _assert("const _currentApiDeviceId = () =>" in src, "SSH dialog re-resolves API identity after onboarding stamps backend fields")
    _assert("_isUnsafeGeneratedProbe(apiDeviceId)" in src, "SSH dialog skips auto-probe with generated labels before backend identity is ready")
    _assert("const probeHostHint = _sshDialogIsIp(typedHost) ? typedHost : ''" in src, "probe clears serial/hostname ssh_host hints")
    _assert("ScalerAPI.probeConnection(apiDeviceId, probeHostHint)" in src, "probe sends sanitized host hint with current backend identity")
    _assert("const verifyHost = pickDirectVerifyHost()" in src, "save verification reuses reachable direct SSH host when available")
    _assert("GI mode uses serial/KVM console paths" in src, "GI serial/KVM save returns early instead of waiting on wrong host")
    _assert("&& !_wantsWeb" in src, "GI auto connect prefers web/virsh path instead of iTerm direct SSH")
    _assert("probe_service_unavailable" in src, "probe 503 marks metadata unknown instead of attaching stale data")
    _assert("credentialDeviceId = _currentApiDeviceId()" in src, "credential persistence uses current backend identity after onboarding")
    _assert("deviceId,\n                    host: connectHost" in src, "web terminal launches use canonical device id")


def test_hostname_mismatch_helper_is_per_device_and_reuses_existing_semantics() -> None:
    src = _read("topology-devices.js")
    _assert("applyHostnameCanvasMismatch(device, configHostname" in src, "shared hostname mismatch helper exists")
    _assert("device._hostnameMismatch = mismatch" in src, "mismatch state is stored on the canvas device")
    _assert("giSerialIdentity" in src, "GI serial/NCP identities suppress hostname mismatch state")
    _assert("isGiMode" in src and "isSerialLike" in src, "identity helper exposes GI/serial predicates")
    _assert("global._deviceInventory || global.deviceInventory" in src, "inventory-label precedence is preserved")
    _assert("device:identity-mismatch" in src, "existing mismatch warning event is emitted")
    _assert("device._mismatchDismissed = false" in src, "new mismatch clears stale dismissals")
    rename = _read("topology-device-rename.js")
    _assert("suppressGiSerialMismatch" in rename, "rename-time mismatch refresh also suppresses GI serial identities")


def test_auto_repair_label_only_replaces_generated_canvas_labels() -> None:
    # Regression for the "name mismatch prompt does not fire" bug (2026-05-12):
    # auto-repair must NOT silently overwrite user-defined canvas labels even
    # when the live config hostname looks like a real DNOS hostname. Only
    # generated placeholders (NCP / NCP-N / S / SN) may be silently aligned.
    src = _read("topology-device-monitor.js")
    _assert("_shouldAutoRepairLabel" in src, "device monitor exposes the auto-repair helper")
    _assert("isGeneratedCanvasLabel" in src,
            "auto-repair consults the shared generated-label predicate before silently aligning")
    _assert("if (!isGeneratedLabel) return false" in src,
            "auto-repair short-circuits for any non-generated canvas label so the mismatch popup can fire")


def test_scaler_api_probe_tracks_bridge_503_cooldown() -> None:
    src = _read("scaler-api.js")
    _assert("async probeConnection(deviceId, sshHost = '')" in src, "probeConnection helper exists")
    _assert("e.status = response.status" in src, "probeConnection exposes HTTP status to callers")
    _assert("e.bridgeUnavailable = true" in src, "probeConnection tags bridge-unavailable failures")
    _assert("this._bridgeRetryAfter = Date.now() + 15000" in src, "probeConnection applies bounded bridge retry cooldown")


def test_toolbar_survives_partial_and_final_context() -> None:
    toolbar = _read("topology-device-toolbar.js")
    target = _read("topology-ssh-target.js")
    _assert("hasBackendIdentity" in toolbar and "isOnboarding" in toolbar, "toolbar renders monitored/loading state before full context")
    _assert("context refresh failed" in toolbar, "toolbar context refresh cannot crash selection UI")
    _assert("button action failed" in toolbar, "toolbar action handlers are guarded")
    _assert("device?._registeredMgmtIp" in target, "SSH target selection prefers registered management IP")
    _assert("device?._registeredDeviceId" in target, "SSH target selection can use registered backend hostname")


def test_stack_dialog_does_not_trust_same_ip_disk_cache_without_identity() -> None:
    stack = _read("topology-stack-dialog.js")
    api = _read("scaler-api.js")
    routes = _read("routes/devices.py")
    _assert("_stackIdentityGuard" in stack, "stack dialog builds an identity guard for cache reads")
    _assert("_isTrustedStackData" in stack, "stack dialog has a disk-cache trust gate")
    _assert("cache_owner_conflicts" in stack, "stack dialog rejects backend-reported cache owner conflicts")
    _assert("generatedLabel && !currentSerials.length && !currentNames.length" in stack,
            "generated labels cannot validate disk cache with only an IP")
    _assert("opts.identityGuard" in api and "identity_guard" in api,
            "ScalerAPI forwards the stack identity guard to backend routes")
    _assert("_identity_guard_matches_entry" in routes and "stack_fast_same_ip_owner_did_not_match_current_identity" in routes,
            "stack-fast avoids writing/reading through mismatched same-IP cache owners")


def test_git_commit_fetch_uses_fast_alias_cache() -> None:
    api = _read("scaler-api.js")
    popup = _read("topology-selection-popups.js")
    routes = _read("routes/devices.py")
    _assert("_fetchWithTimeout(url, {}, 10000)" in api, "git commit fetch has a bounded fast timeout")
    _assert("responsePayload.git_commit_fetched_at" in popup, "git commit popup preserves backend cache timestamp")
    _assert("cache_device_id" in routes and "_candidate_config_ids" in routes,
            "git commit endpoint checks canonical/alias operational caches before live SSH")


def test_lldp_neighbor_connect_uses_native_iterm_flow() -> None:
    lldp = _read("topology-lldp-dialog.js")
    _assert("class=\"lldp-neighbor-connect\"" in lldp, "LLDP rows render a compact per-neighbor Connect action")
    _assert("_resolveLldpNeighborTarget" in lldp and "ScalerAPI.getDeviceContext(candidate, false, '')" in lldp,
            "LLDP neighbor buttons resolve through backend device context")
    _assert("_openNeighborNativeSsh" in lldp and "editor._openSshUrl(`ssh://${user}@${host}`)" in lldp,
            "LLDP neighbor Connect launches through the native SSH/iTerm helper")
    _assert("window.ObjectDetection._pendingDevice = device" in lldp and "window.ObjectDetection._forceItermOnce = true" in lldp,
            "LLDP native SSH reuses the canonical pending-device launch context")
    _assert("TerminalPanel.open" not in lldp and "serverCredentials" not in lldp,
            "LLDP neighbor Connect does not launch the web terminal path")


def test_web_terminal_panel_is_responsive_and_fit_aware() -> None:
    terminal = _read("topology-terminal.js")
    styles = _read("styles.css")
    _assert("panel.className = 'terminal-panel'" in terminal, "web terminal applies the CSS panel hook")
    _assert("_clampPanelHeight(height)" in terminal and "calc(100vh - 28px)" in terminal,
            "web terminal height is clamped to the viewport")
    _assert("new ResizeObserver" in terminal and "_scheduleFit(this._getActiveSession()" in terminal,
            "web terminal refits xterm when the panel body or viewport changes")
    _assert("_fitSession(session, false)" in terminal and "this._sendResize(session)" in terminal,
            "web terminal fits before sending connected resize dimensions")
    _assert("@media (max-width: 900px)" in styles and "@media (max-height: 560px)" in styles,
            "web terminal CSS includes width and height responsive polish")


def test_serve_exposes_onboarding_route_on_active_path() -> None:
    src = _read("serve.py")
    _assert('path == "/api/devices/verify-and-register"' in src, "serve.py proxies verify-and-register")
    _assert('path == "/api/devices/monitored" or path.startswith("/api/devices/monitored/")' in src, "serve.py proxies monitored reads")
    _assert('path.startswith("/api/devices/monitored/") and path.endswith("/attach")' in src, "serve.py proxies monitored attach/detach")


def test_canvas_autosave_persists_active_topology_to_backend() -> None:
    editor = _read("topology.js")
    ops = _read("topology-file-ops.js")
    _assert("window.FileOps._schedulePersistentAutoSave(this" in editor,
            "editor autosave schedules a persistent backend save")
    _assert("_schedulePersistentAutoSave(editor" in ops,
            "FileOps exposes debounced persistent autosave")
    _assert("window.TopologySync.saveActive(safeName, data)" in ops,
            "persistent autosave writes active TopologySync records")
    _assert("FileOps._sectionSaveWithConflict(" in ops,
            "persistent autosave falls back to legacy section save with conflict guard")
    _assert("_persistentAutoSaveConflict" in ops and "_showStaleSaveBanner" in ops,
            "persistent autosave stops and surfaces conflicts instead of overwriting")
    _assert("const delay = Number.isFinite(opts.delayMs) ? Math.max(0, opts.delayMs) : 350;" in ops,
            "persistent autosave debounces each topology step change with a short delay")
    _assert("allowEmpty: !!opts.allowEmpty" in editor and "force: !!opts.force" in editor,
            "editor autosave can intentionally persist empty current-topology clears")


def test_topology_switch_auto_saves_current_before_loading_next() -> None:
    ops = _read("topology-file-ops.js")
    _assert("_saveCurrentTopologyBeforeSwitch(editor, opts = {})" in ops,
            "topology transition save helper accepts explicit options")
    _assert("FileOps._saveCurrentTopologyBeforeSwitch(editor, { allowEmpty: true, silent: true })" in ops,
            "dirty topology switches auto-save the current active topology before loading the next")
    _assert("FileOps._showUnsavedSwitchPrompt(editor, targetBase" in ops,
            "untargeted/new canvases still prompt instead of silently discarding")
    _assert("syncActive.permission && syncActive.permission !== 'write'" in ops,
            "view-only shared topologies are not silently saved during switching")
    _assert("info.shared && (info.shared.isSharedIn || info.shared.isInbox)" in ops,
            "shared-in topologies never fall back to legacy section saves")


def test_clear_canvas_is_current_topology_only() -> None:
    editor = _read("topology.js")
    ops = _read("topology-file-ops.js")
    _assert("editor.clearCanvas();" in editor,
            "toolbar Clear button routes to current-topology clear behavior")
    _assert("_clearCurrentTopologyOnly(editor)" in ops,
            "FileOps exposes a current-topology-only clear helper")
    _assert("FileOps.performClearCanvas(editor, { preserveActive: true, markClean: false });" in ops,
            "current-topology clear keeps the active topology identity until its empty snapshot saves")
    _assert("Other topologies and domains are untouched" in ops,
            "clear confirmation tells users scope is current topology only")
    _assert("editor.autoSave({ force: true, allowEmpty: true });" in ops,
            "current-topology clear writes the empty canvas to local autosave immediately")


def test_cmd_x_clears_current_topology_with_confirmation() -> None:
    keyboard = _read("topology-keyboard.js")
    ops = _read("topology-file-ops.js")
    _assert("Cmd/Ctrl + X clears the currently opened topology" in keyboard,
            "Cmd/Ctrl+X documents clear-current-topology behavior")
    _assert("editor.clearCanvas();" in keyboard,
            "Cmd/Ctrl+X routes to editor.clearCanvas (which prompts before wiping)")
    _assert("Select objects before cutting" not in keyboard,
            "Cmd/Ctrl+X must not require a selection -- it clears the topology, not a cut")
    _assert("editor.performClearCanvas();" not in keyboard,
            "Cmd/Ctrl+X must not bypass the prompt by calling performClearCanvas directly")
    # The prompt + scope-to-current-topology path lives in FileOps -- the
    # shortcut handler does not duplicate that logic, it just dispatches to
    # editor.clearCanvas which routes through _clearCurrentTopologyOnly.
    _assert("_clearCurrentTopologyOnly(editor)" in ops,
            "FileOps still exposes the current-topology-only clear helper that Cmd/Ctrl+X relies on")
    _assert("Other topologies and domains are untouched" in ops,
            "Cmd/Ctrl+X confirmation explicitly tells users the scope is the current topology only")


def test_topology_row_loader_scopes_load_token_for_error_path() -> None:
    ops = _read("topology-file-ops.js")
    _assert("let loadToken = null;" in ops,
            "own-domain topology row loader declares loadToken outside try/catch")
    _assert("if (loadToken && !FileOps._isTopologyLoadCurrent(editor, loadToken)) return;" in ops,
            "own-domain topology row loader catch path guards stale loadToken checks")
    _assert("if (loadToken) FileOps._cancelTopologyLoad(editor, loadToken);" in ops,
            "own-domain topology row loader catch path only cancels initialized load tokens")


def test_topology_indicator_share_segments_helper_exists() -> None:
    ops = _read("topology-file-ops.js")
    html = _read("index.html")
    _assert("_updateIndicatorShareSegments(name, sectionId, sharedInfo, isGeneral) {" in ops,
            "topology indicator share segment helper exists")
    _assert("FileOps._updateIndicatorShareSegments(name, sectionId, sharedInfo, isGeneral);" in ops,
            "topology indicator calls the share segment helper")
    _assert("target.closest('#topo-active-shared-by')" in ops,
            "shared-by chip clicks do not reopen the topology dropdown")
    _assert("topology-file-ops.js?v=20260513e-topology-safety" in html,
            "topology-file-ops cache buster was bumped for topology safety")
    _assert("topology-domains.js?v=20260513a-topology-safety" in html,
            "topology-domains cache buster was bumped for stale-list safety")


def test_topology_visibility_failures_preserve_cached_lists() -> None:
    ops = _read("topology-file-ops.js")
    domains = _read("topology-domains.js")
    _assert("editor._customSections = editor._customSections || [];" in ops,
            "section refresh failure keeps the last known domain list")
    _assert("Topology domains temporarily unavailable; keeping the last known list." in ops,
            "section refresh failure is presented as temporary, not deleted")
    _assert("Existing topologies were not deleted." in ops,
            "topology row failure does not render a destructive empty state")
    _assert("if (!resp.ok) return _domains;" in domains and "return _domains;" in domains,
            "multi-user domain refresh failure preserves cached domains")
    _assert("Delete empty domain" in ops and "Move or delete individual topologies first." in ops,
            "domain delete UI explains non-empty domains are protected")


if __name__ == "__main__":
    test_scaler_api_uses_auth_fetch_for_protected_calls()
    test_ssh_dialog_has_premium_onboarding_state_machine()
    test_ssh_dialog_prefers_registered_identity_for_console_and_probe()
    test_hostname_mismatch_helper_is_per_device_and_reuses_existing_semantics()
    test_auto_repair_label_only_replaces_generated_canvas_labels()
    test_scaler_api_probe_tracks_bridge_503_cooldown()
    test_toolbar_survives_partial_and_final_context()
    test_stack_dialog_does_not_trust_same_ip_disk_cache_without_identity()
    test_git_commit_fetch_uses_fast_alias_cache()
    test_lldp_neighbor_connect_uses_native_iterm_flow()
    test_web_terminal_panel_is_responsive_and_fit_aware()
    test_serve_exposes_onboarding_route_on_active_path()
    test_canvas_autosave_persists_active_topology_to_backend()
    test_topology_switch_auto_saves_current_before_loading_next()
    test_clear_canvas_is_current_topology_only()
    test_cmd_x_is_cut_only_not_clear_canvas()
    test_topology_row_loader_scopes_load_token_for_error_path()
    test_topology_indicator_share_segments_helper_exists()
    test_topology_visibility_failures_preserve_cached_lists()
    print("All device onboarding frontend checks passed.")
