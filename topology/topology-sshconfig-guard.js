// ============================================================================
// topology-sshconfig-guard.js
// ----------------------------------------------------------------------------
// SN-as-source-of-truth watchdog for `device.sshConfig`.
//
// Problem we're solving
// ---------------------
// The SSH credentials dialog writes the operator's explicit choice into two
// fields when they hit Save:
//
//   device.sshConfig.host           -- fast path used by openTerminalToDevice
//   device.sshConfig._userSavedHost -- "sticky" slot, survives reshapes
//
// Every other code path (DNAAS enrichment, network-mapper regeneration, probe
// row auto-highlight, scaler-bridge recovery, ...) is supposed to prefer
// `_userSavedHost` when it exists, or at minimum leave `host` alone if it is
// already populated. A single forgetful write like
//
//     device.sshConfig = { host: someDiscoveredIp, user: 'dnroot', ... };
//
// silently reverts the canvas back to the pre-upgrade mgmt IP for a device
// the operator just saved by serial number. The operator then opens the
// terminal and paramiko rejects the creds because it's attacking the wrong
// box -- this is the exact "Authentication failed" that shows up in the
// debugger log.
//
// What this guard does
// --------------------
// 1. Periodically scans every canvas device whose host expectation is
//    known. There are two sources of expectation, in priority order:
//      (a) `sshConfig._userSavedHost` -- the explicit operator choice
//          made via the SSH dialog Save button.
//      (b) `sshConfig._snVerified` + `sshConfig._snVerifiedHost` -- the
//          "SN host-lock" stamped by the SSH dialog when a probe / Discover
//          Console reported any of {ssh_sn, console, virsh_console} as
//          reachable. That is canonical SN -> host evidence and is the
//          source of truth for ghost-IP labs whose mgmt IP is wrong.
// 2. If `sshConfig.host` drifts away from the expectation, log a LOUD
//    warning including:
//      - device id/label/serial
//      - expected host + which source claimed it (userSaved | snVerified)
//      - unexpected host currently on sshConfig
//      - the last N call-sites that touched sshConfig (set-trap)
//      - a wall-clock timestamp so it lines up with the SSH dialog's own
//        "[OK] SSH set: ..." toast
// 3. If auto-heal is enabled (default ON), restore
//      sshConfig.host     = expected
//      sshConfig.user     = _userSavedUser || sshConfig.user
//      sshConfig.password = _userSavedPass || sshConfig.password
//    so the operator's next terminal click uses the correct host.
// 4. SN-verified branch is conservative: it only heals when the live host
//    looks like a mgmt IPv4 dotted quad AND the expected host does NOT.
//    That keeps benign user edits (typing a hostname while SN-locked) from
//    triggering a fight with the guard.
//
// Disabling / tuning
// ------------------
//   window.__SSH_CONFIG_GUARD_AUTOHEAL  = false  // report-only mode
//   window.__SSH_CONFIG_GUARD_DISABLED  = true   // turn watchdog off entirely
//   window.__SSH_CONFIG_GUARD_VERBOSE   = true   // log every scan, not just drifts
//   window.__SSH_CONFIG_GUARD_INTERVAL  = 2500   // scan period in ms (default 2500)
//
// Public API (attached to window.SSHConfigGuard)
// ----------------------------------------------
//   .audit()         -> returns [{ deviceId, label, savedHost, liveHost }]
//                       for every device currently in drift.
//   .history(limit)  -> returns the last `limit` drift events captured.
//   .resetHistory()  -> clears the drift history buffer.
//   .install()       -> start the interval (called automatically on
//                       DOMContentLoaded + when window.topologyEditor exists).
//   .uninstall()     -> stop the interval.
//   .snapshot()      -> compact summary useful for paste-into-chat diagnostics.
//
// This file is intentionally standalone -- no dependencies on topology.js
// internals beyond `window.topologyEditor.objects`. Safe to load anywhere in
// the <script defer> chain.
// ============================================================================
(function () {
    'use strict';

    if (window.SSHConfigGuard && window.SSHConfigGuard.__installed) {
        return;
    }

    const MAX_HISTORY = 50;
    const DEFAULT_INTERVAL_MS = 2500;
    const driftHistory = [];
    let intervalHandle = null;
    let _tick = 0;

    function _now() {
        const d = new Date();
        return d.toISOString().slice(11, 23); // HH:MM:SS.mmm, matches console timestamps
    }

    function _editor() {
        return window.topologyEditor || window.editor || null;
    }

    function _devices() {
        const ed = _editor();
        if (!ed || !Array.isArray(ed.objects)) return [];
        return ed.objects.filter(o => o && o.type === 'device');
    }

    function _trace() {
        try {
            // Capture a shallow stack so the operator can see which module
            // most recently touched sshConfig. New Error().stack on Chrome /
            // Firefox gives the full V8/Gecko trace without throwing.
            const e = new Error('SSH_CONFIG_GUARD_TRACE');
            return String(e.stack || '').split('\n').slice(2, 8).join('\n');
        } catch (_) {
            return '';
        }
    }

    function _recordDrift(entry) {
        driftHistory.push(entry);
        if (driftHistory.length > MAX_HISTORY) {
            driftHistory.splice(0, driftHistory.length - MAX_HISTORY);
        }
    }

    function _describe(device) {
        return {
            id: device.id || '',
            label: device.label || '',
            serial: device.deviceSerial || device.serial || '',
        };
    }

    function _isMgmtIpLike(h) {
        return typeof h === 'string' && /^\d+\.\d+\.\d+\.\d+$/.test(h.trim());
    }

    // Pick the host the guard wants to enforce for `dev`. Priority:
    //   1. `_userSavedHost`   -- explicit operator choice (existing
    //                            behaviour, survives reboots).
    //   2. `_snVerifiedHost`  -- SN-locked path. The SSH dialog stamps
    //                            this when a probe / Discover Console
    //                            returns reachable for ssh_sn / console
    //                            / virsh_console -- canonical SN -> host
    //                            evidence. Critical for ghost-IP labs
    //                            where the mgmt IP in inventory is
    //                            stale and should NEVER be re-stamped on
    //                            top of the working SN-based identifier.
    function _expectedHost(cfg) {
        const saved = (cfg._userSavedHost || '').toString().trim();
        if (saved) return { host: saved, source: 'userSaved' };
        if (cfg._snVerified) {
            const lock = (cfg._snVerifiedHost || '').toString().trim();
            if (lock) return { host: lock, source: 'snVerified' };
        }
        return { host: '', source: '' };
    }

    function _healDevice(device, cfg, expectedHost) {
        const savedHost = expectedHost || cfg._userSavedHost || cfg._snVerifiedHost || '';
        const savedUser = cfg._userSavedUser || '';
        const savedPass = cfg._userSavedPass || '';
        if (!savedHost) return false;
        cfg.host = savedHost;
        if (savedUser) cfg.user = savedUser;
        if (savedPass) cfg.password = savedPass;
        // Keep deviceAddress visual in sync for any UI reading it directly.
        try {
            const uName = cfg.user || 'dnroot';
            device.deviceAddress = `${uName}@${savedHost}`;
        } catch (_) {}
        return true;
    }

    function _scan() {
        if (window.__SSH_CONFIG_GUARD_DISABLED) return;
        _tick += 1;
        const autoHeal = window.__SSH_CONFIG_GUARD_AUTOHEAL !== false; // default ON
        const verbose = !!window.__SSH_CONFIG_GUARD_VERBOSE;
        const devices = _devices();
        if (!devices.length) return;

        const drifts = [];
        for (const dev of devices) {
            const cfg = dev.sshConfig;
            if (!cfg) continue;
            const expected = _expectedHost(cfg);
            if (!expected.host) continue;
            const live = (cfg.host || '').toString().trim();
            if (!live || live === expected.host) continue;

            // For the SN-verified branch we additionally require that
            // the live host is a mgmt-IP-like string while the expected
            // host is NOT. That keeps the guard from "fighting" benign
            // edits like the operator typing a non-IP hostname into
            // the dialog while a SN lock is still set -- only true
            // ghost-IP regressions trigger heal.
            if (expected.source === 'snVerified') {
                if (!_isMgmtIpLike(live) || _isMgmtIpLike(expected.host)) continue;
            }

            const entry = {
                at: _now(),
                device: _describe(dev),
                expected: expected.host,
                expectedSource: expected.source,
                got: live,
                user: cfg.user || '',
                userSavedUser: cfg._userSavedUser || '',
                trace: _trace(),
                tick: _tick,
            };
            drifts.push(entry);
            _recordDrift(entry);

            console.warn(
                `[SSHConfigGuard] drift detected @ ${entry.at} -- ` +
                `device=${entry.device.label} (id=${entry.device.id}, sn=${entry.device.serial}) ` +
                `expected host="${entry.expected}" (source=${entry.expectedSource}) ` +
                `but sshConfig.host="${entry.got}". ` +
                (autoHeal ? 'Auto-healing now.' : 'Auto-heal disabled.')
            );
            if (entry.trace) console.warn(`[SSHConfigGuard] recent call frames:\n${entry.trace}`);

            if (autoHeal) {
                const healed = _healDevice(dev, cfg, expected.host);
                if (healed) {
                    console.warn(
                        `[SSHConfigGuard] restored ${entry.device.label}: ` +
                        `sshConfig.host := "${entry.expected}" (source=${entry.expectedSource})`
                    );
                }
            }
        }

        if (verbose) {
            console.log(
                `[SSHConfigGuard] tick=${_tick} devices=${devices.length} ` +
                `with_saved=${devices.filter(d => d.sshConfig?._userSavedHost).length} ` +
                `drifts=${drifts.length}`
            );
        }
    }

    const SSHConfigGuard = {
        __installed: false,

        install() {
            if (this.__installed) return;
            const interval = Math.max(
                500,
                Number(window.__SSH_CONFIG_GUARD_INTERVAL) || DEFAULT_INTERVAL_MS
            );
            intervalHandle = setInterval(_scan, interval);
            this.__installed = true;
            console.log(
                `[SSHConfigGuard] watchdog installed (period=${interval}ms, ` +
                `auto-heal=${window.__SSH_CONFIG_GUARD_AUTOHEAL !== false}).`
            );
        },

        uninstall() {
            if (!this.__installed) return;
            if (intervalHandle) clearInterval(intervalHandle);
            intervalHandle = null;
            this.__installed = false;
            console.log('[SSHConfigGuard] watchdog uninstalled.');
        },

        audit() {
            const out = [];
            for (const dev of _devices()) {
                const cfg = dev.sshConfig;
                if (!cfg) continue;
                const expected = _expectedHost(cfg);
                if (!expected.host) continue;
                const live = (cfg.host || '');
                if (live === expected.host) continue;
                if (expected.source === 'snVerified') {
                    if (!_isMgmtIpLike(live) || _isMgmtIpLike(expected.host)) continue;
                }
                out.push({
                    deviceId: dev.id,
                    label: dev.label,
                    serial: dev.deviceSerial || dev.serial || '',
                    savedHost: expected.host,
                    expectedSource: expected.source,
                    liveHost: live,
                });
            }
            return out;
        },

        history(limit) {
            const n = Math.max(0, Number(limit) || MAX_HISTORY);
            return driftHistory.slice(-n);
        },

        resetHistory() {
            driftHistory.length = 0;
            console.log('[SSHConfigGuard] drift history cleared.');
        },

        snapshot() {
            const devs = _devices();
            const saved = devs.filter(d => d.sshConfig?._userSavedHost);
            const snLocked = devs.filter(d => d.sshConfig?._snVerified && d.sshConfig?._snVerifiedHost);
            const drifted = this.audit();
            return {
                at: _now(),
                totalDevices: devs.length,
                withUserSavedHost: saved.length,
                snLocked: snLocked.length,
                currentlyDrifted: drifted.length,
                drifted,
                recentDriftEvents: driftHistory.slice(-10),
            };
        },
    };

    window.SSHConfigGuard = SSHConfigGuard;

    // Auto-install once the editor exists. We don't want the scan firing
    // before the canvas has loaded objects, otherwise the first few ticks
    // are pure noise.
    function _autoInstall() {
        const ed = _editor();
        if (!ed) {
            setTimeout(_autoInstall, 500);
            return;
        }
        SSHConfigGuard.install();
    }

    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(_autoInstall, 0);
    } else {
        document.addEventListener('DOMContentLoaded', () => setTimeout(_autoInstall, 0));
    }
})();
