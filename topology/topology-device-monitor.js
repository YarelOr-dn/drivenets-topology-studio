/**
 * topology-device-monitor.js - Background Device Monitor
 *
 * Polls all topology devices with SSH credentials every 5 minutes.
 * Stores stack, LLDP, and git commit data on device objects for instant
 * cache-first dialog opens. Fires device:context-updated for open dialogs.
 */

'use strict';

window.DeviceMonitor = {
    _editor: null,
    _intervalId: null,
    _running: false,
    _INTERVAL_MS: 5 * 60 * 1000,
    _BATCH_SIZE: 5,
    _BATCH_DELAY_MS: 2000,
    _upgradingDevices: new Set(),
    _POST_UPGRADE_DELAY_MS: 30000,
    // Wave 2.3: visibilitychange pause + global cooldown.
    // When the tab is hidden, no tick runs. When the backend responds with
    // 429 or 503 + Retry-After, all polling pauses until the cooldown
    // expires. Per-device exponential backoff prevents one flaky device
    // from consuming the whole batch.
    _cooldownUntil: 0,
    _lastTickAt: 0,
    _visibilityHandlerBound: false,
    _MIN_DEVICE_BACKOFF_MS: 30 * 1000,
    _MAX_DEVICE_BACKOFF_MS: 30 * 60 * 1000,
    _IDENTITY_MISMATCH_DEBUG_MS: 60 * 1000,
    _identityMismatchLog: null,

    init(editor) {
        if (this._editor) return;
        this._editor = editor;
        this._bindVisibilityHandler();
        this._bindScopeHandlers();
        setTimeout(() => this._tick(true), 2000);
        this._start();
        this._listenForUpgradeEvents();
    },

    _bindScopeHandlers() {
        if (this._scopeHandlersBound) return;
        this._scopeHandlersBound = true;
        // Bug fix (2026-04-26): the previous behaviour was to set a 2s
        // cooldown on `topology:unloaded` and let the interval keep
        // running. In practice this produced a stream of
        //   `[DeviceMonitor] backing off ... due to topology:unloaded`
        // warnings every time the canvas was cleared (or rapidly when
        // the user switched between topologies), and could re-fire
        // SSH calls against an empty/stale canvas before
        // `topology:loaded` arrived. We now stop polling outright on
        // unload and re-arm the interval when the new topology is in.
        window.addEventListener('topology:unloaded', () => {
            this.stop();
            if (window.DeviceState && typeof window.DeviceState.abortScope === 'function') {
                try { window.DeviceState.abortScope(undefined, 'topology:unloaded'); } catch (_) {}
            }
        });
        window.addEventListener('topology:loaded', () => {
            // Fresh topology -- drop any per-device backoff that
            // referred to the OLD canvas objects and schedule an
            // immediate catch-up tick so the new canvas populates fast.
            if (!this._intervalId) this._start();
            setTimeout(() => this._tick(true), 800);
        });
        // `topology:active-changed` is fired by TopologySync AFTER
        // `topology:loaded` (because setActive runs post-load), and is
        // the moment DeviceState's scope key actually flips. We schedule
        // one more catch-up tick so the refresh runs under the NEW
        // scope key and populates NEW-scope caches, rather than
        // landing under OLD-scope keys that will get aborted 50ms
        // later when the orchestrator notices the transition.
        window.addEventListener('topology:active-changed', () => {
            if (!this._intervalId) this._start();
            setTimeout(() => this._tick(true), 400);
        });
        const onAuthLogout = () => {
            this.stop();
            if (window.DeviceState && typeof window.DeviceState.abortAll === 'function') {
                try { window.DeviceState.abortAll('topology:auth-logout'); } catch (_) {}
            }
        };
        const onAuthLogin = () => {
            if (!this._intervalId) this._start();
        };
        // TopologyAuth dispatches `topology:auth-*` (see topology-auth.js).
        // Legacy `auth:*` names were never emitted here, so logout left
        // polling alive and produced 401 spam on every device refresh.
        window.addEventListener('topology:auth-logout', onAuthLogout);
        window.addEventListener('topology:auth-login', onAuthLogin);
        window.addEventListener('auth:logout', onAuthLogout);
        window.addEventListener('auth:login', onAuthLogin);
    },

    _bindVisibilityHandler() {
        if (this._visibilityHandlerBound) return;
        this._visibilityHandlerBound = true;
        const onVisibility = () => {
            if (document.visibilityState === 'visible') {
                const sinceLast = Date.now() - (this._lastTickAt || 0);
                if (this._lastTickAt && sinceLast > this._INTERVAL_MS) {
                    console.debug('[DeviceMonitor] tab visible after', Math.round(sinceLast / 1000),
                        's idle -- catching up with an immediate tick');
                    setTimeout(() => this._tick(true), 500);
                }
            } else {
                console.debug('[DeviceMonitor] tab hidden -- pausing polling');
            }
        };
        document.addEventListener('visibilitychange', onVisibility);
    },

    _inCooldown() {
        return this._cooldownUntil > Date.now();
    },

    _setCooldown(seconds, reason) {
        const until = Date.now() + Math.max(0, seconds) * 1000;
        if (until > this._cooldownUntil) this._cooldownUntil = until;
        // Bug fix (2026-04-26): dedupe identical reasons within a 30s
        // window so the console doesn't get flooded with a backoff line
        // for every subsequent device hitting the same 429/503/network
        // failure.
        const now = Date.now();
        const lastFor = this._lastBackoffLog && this._lastBackoffLog[reason];
        if (!lastFor || now - lastFor > 30000) {
            console.warn('[DeviceMonitor] backing off', seconds, 's due to', reason);
            this._lastBackoffLog = this._lastBackoffLog || {};
            this._lastBackoffLog[reason] = now;
        }
    },

    _logIgnoredIdentityMismatch(device, deviceId, reason, details = {}) {
        const now = Date.now();
        const cleanReason = String(reason || 'identity mismatch');
        const key = `${deviceId || 'unknown'}|${cleanReason}`;
        this._identityMismatchLog = this._identityMismatchLog || {};
        const entry = this._identityMismatchLog[key] || {
            firstAt: now,
            lastDebugAt: 0,
            count: 0
        };
        entry.count += 1;
        if (device) {
            device._monitorLastIgnoredContext = {
                deviceId,
                reason: cleanReason,
                host: details.host || '',
                ignoredAt: now,
                source: 'device-monitor',
                repeatCount: entry.count
            };
        }
        if (entry.count === 1) {
            console.warn('[DeviceMonitor] ignoring context identity mismatch for',
                deviceId, cleanReason, '-- stale response ignored');
        } else if (now - entry.lastDebugAt > this._IDENTITY_MISMATCH_DEBUG_MS) {
            console.debug('[DeviceMonitor] repeated context identity mismatch for',
                deviceId, `(${entry.count}x)`, cleanReason);
            entry.lastDebugAt = now;
        }
        this._identityMismatchLog[key] = entry;
    },

    _listenForUpgradeEvents() {
        window.addEventListener('device:upgrade-started', (e) => {
            const devices = e.detail?.devices || [];
            devices.forEach(d => this._upgradingDevices.add(d));
            console.debug('[DeviceMonitor] Upgrade started, pausing polling for:', devices);
        });

        window.addEventListener('device:upgrade-complete', (e) => {
            const detail = e.detail || {};
            const allDevices = detail.allDevices || [];
            const completedDevices = detail.completedDevices || [];

            allDevices.forEach(d => this._upgradingDevices.delete(d));
            console.debug('[DeviceMonitor] Upgrade complete. Completed:', completedDevices,
                'Scheduling live refresh in', this._POST_UPGRADE_DELAY_MS / 1000, 's');

            if (completedDevices.length > 0) {
                setTimeout(() => {
                    this._postUpgradeRefresh(completedDevices);
                }, this._POST_UPGRADE_DELAY_MS);
            }
        });
    },

    async _postUpgradeRefresh(deviceIds) {
        const editor = this._editor;
        if (!editor?.objects) return;
        console.debug('[DeviceMonitor] Post-upgrade live refresh for:', deviceIds);

        for (const did of deviceIds) {
            const device = editor.objects.find(o =>
                o.type === 'device' && (o.label === did || o.serial === did));
            if (!device) continue;
            try {
                await this._refreshOne(device, true);
                console.debug('[DeviceMonitor] Post-upgrade context refreshed:', did);
            } catch (e) {
                console.warn('[DeviceMonitor] Post-upgrade refresh failed for', did, e?.message);
            }

            if (typeof ScalerAPI !== 'undefined' && ScalerAPI.syncDevice) {
                try {
                    await ScalerAPI.syncDevice(did);
                    console.debug('[DeviceMonitor] Post-upgrade config re-extracted:', did);
                } catch (e) {
                    console.warn('[DeviceMonitor] Post-upgrade config sync failed for', did, e?.message);
                }
            }
        }

        if (editor?.showNotification) {
            editor.showNotification(
                `[INFO] Post-upgrade refresh complete for ${deviceIds.length} device(s)`,
                'info', 6000
            );
        }
    },

    _start() {
        if (this._intervalId) return;
        this._intervalId = setInterval(() => this._tick(true), this._INTERVAL_MS);
    },

    stop() {
        if (this._intervalId) {
            clearInterval(this._intervalId);
            this._intervalId = null;
        }
        this._running = false;
    },

    _isMonitorable(device) {
        if (!(device.sshConfig?.host || device.sshConfig?.hostBackup || device.deviceSerial || device.serial)) {
            return false;
        }
        const did = device.label || device.deviceSerial || device.serial || '';
        if (this._upgradingDevices.has(did)) {
            return false;
        }
        // Wave 2.3: honor per-device backoff.
        if (device._monitorBackoffUntil && device._monitorBackoffUntil > Date.now()) {
            return false;
        }
        return true;
    },

    _shouldAutoRepairLabel(currentLabel, cfgHostname) {
        if (!currentLabel || !cfgHostname) return false;

        // Bug fix 2026-05-12 (Name Mismatch Prompt Suppression):
        // Only auto-align canvas labels that the system itself generated
        // (NCP / NCP-N / S / SN placeholders). Any user-defined label --
        // even one that looks like a DNOS hostname (e.g. "PE-7", "Router-A")
        // -- must defer to the explicit mismatch popup so the operator can
        // choose Rename-canvas / Change-device-hostname / Dismiss. Without
        // this gate, a save against a device whose live hostname matches
        // the DNOS regex silently overwrites the operator's intentional
        // canvas label and the mismatch prompt never fires.
        const guard = window.TopologyDeviceIdentity || null;
        const isGeneratedLabel = guard && typeof guard.isGeneratedCanvasLabel === 'function'
            ? guard.isGeneratedCanvasLabel(currentLabel)
            : /^(NCP|NCP-\d+|S|S\d+)$/i.test(String(currentLabel || '').trim());
        if (!isGeneratedLabel) return false;

        const inv = window._deviceInventory || window.deviceInventory;
        const inventoryHostnames = new Set();
        if (inv?.devices) {
            for (const info of Object.values(inv.devices)) {
                if (info.hostname) {
                    const hn = info.hostname.replace(/,$/, '').trim();
                    if (hn) inventoryHostnames.add(hn);
                }
            }
        }

        // If current label IS an inventory hostname, it was set by LabelRepair
        // or the user intentionally. Inventory (DNAAS discovery) takes precedence
        // over device running-config hostname (which may be a default like CDNOS-RR).
        if (inventoryHostnames.has(currentLabel)) return false;

        const _DEVICE_RE = /\b(PE|RR|SA|CL|NCC|NCP|NCM|NCF|LEAF|SPINE|DUT|CDNOS|YOR|BGW)\b/i;
        const cfgInInventory = inventoryHostnames.has(cfgHostname);
        const cfgLooksValid = _DEVICE_RE.test(cfgHostname);
        return cfgInInventory || cfgLooksValid;
    },

    refreshDevice(deviceId, live = true) {
        const editor = this._editor;
        if (!editor?.objects) return Promise.resolve();
        const needle = String(deviceId || '').trim().toLowerCase();
        const device = editor.objects.find(o => {
            if (!o || o.type !== 'device') return false;
            const resolved = window.TopologyDeviceIdentity?.resolveIdentity
                ? window.TopologyDeviceIdentity.resolveIdentity(o)
                : null;
            const candidates = [
                o.label,
                o.serial,
                o.deviceSerial,
                o._registeredDeviceId,
                o._registeredHostname,
                o._monitoredKey,
                ...(resolved?.candidates || [])
            ].map(v => String(v || '').trim().toLowerCase()).filter(Boolean);
            return candidates.includes(needle);
        });
        if (!device) return Promise.resolve();
        return this._refreshOne(device, live);
    },

    _pickGitCommit(payload = {}) {
        const candidates = [
            payload.git_commit,
            payload.gitCommit,
            payload.git_commit_hash,
            payload.git_hash,
            payload.commit,
            payload.commit_hash,
            payload.build_git_commit,
            payload.version_info?.git_commit,
            payload.context?.git_commit,
        ];
        const value = candidates.find(v => v !== undefined && v !== null && String(v).trim() !== '');
        return value === undefined ? null : String(value).trim();
    },

    async _resolveActiveNcc(device) {
        const cachedIp = device.sshConfig?._activeNccIp || device._activeNccIp || '';
        if (cachedIp) return cachedIp;
        const cachedHost = device.sshConfig?._activeNccHost || device._activeNccHost || '';
        if (cachedHost) return cachedHost;
        if (typeof DnaasHelpers === 'undefined' || !DnaasHelpers._findActiveNcc) return null;
        try {
            let invFile = window._deviceInventory || window.deviceInventory;
            if (!invFile?.devices && typeof ScalerAPI !== 'undefined' && ScalerAPI.getDeviceInventory) {
                invFile = await ScalerAPI.getDeviceInventory();
            }
            if (!invFile?.devices) return null;
            const serial = device.deviceSerial || device.serial || device.label || '';
            const activeKey = DnaasHelpers._findActiveNcc(invFile, serial);
            if (activeKey) {
                const activeInfo = invFile.devices[activeKey];
                return activeInfo?.mgmt_ip || activeInfo?.ip || null;
            }
        } catch (_) {}
        return null;
    },

    async _tick(live = true) {
        if (this._running) return;
        const editor = this._editor;
        if (!editor?.objects) return;

        if (typeof window.TopologyAuth === 'object' && window.TopologyAuth
            && typeof window.TopologyAuth.isAuthenticated === 'function'
            && !window.TopologyAuth.isAuthenticated()) {
            return;
        }

        // Wave 2.3: skip ticking when the tab is hidden -- users on an
        // idle background tab should not cause live SSH traffic to pile
        // up on the backend. A visibilitychange handler schedules a
        // catch-up tick when they come back.
        if (typeof document !== 'undefined' && document.visibilityState === 'hidden') {
            return;
        }

        // Wave 2.3: honor global cooldown from Retry-After.
        if (this._inCooldown()) {
            return;
        }

        if (this._consecutiveNetFails > 2) {
            try {
                const r = await fetch('/api/health', { signal: AbortSignal.timeout(3000) });
                if (!r.ok) { this._consecutiveNetFails++; return; }
                this._consecutiveNetFails = 0;
            } catch (_) { this._consecutiveNetFails++; return; }
        }

        const devices = editor.objects
            .filter(o => o.type === 'device' && this._isMonitorable(o));
        if (devices.length === 0) return;
        this._running = true;
        this._lastTickAt = Date.now();
        try {
            for (let i = 0; i < devices.length; i += this._BATCH_SIZE) {
                const batch = devices.slice(i, i + this._BATCH_SIZE);
                await Promise.all(batch.map(d => this._refreshOne(d, live)));
                if (i + this._BATCH_SIZE < devices.length) {
                    await new Promise(r => setTimeout(r, this._BATCH_DELAY_MS));
                    // If a 429/503 came in during the batch, abort the rest.
                    if (this._inCooldown()) break;
                }
            }
        } finally {
            this._running = false;
        }
    },

    async _refreshOne(device, live = true) {
        if (typeof ScalerAPI === 'undefined' || !ScalerAPI.getDeviceContext) return;
        const resolvedIdentity = window.TopologyDeviceIdentity?.resolveIdentity
            ? window.TopologyDeviceIdentity.resolveIdentity(device)
            : null;
        const deviceId = resolvedIdentity?.deviceId || (
            device._registeredDeviceId
            || device._registeredHostname
            || device.deviceSerial
            || device.serial
            || device.label
            || ''
        );
        if (!deviceId) return;
        const sshHost = resolvedIdentity?.host || device._registeredMgmtIp || device.sshConfig?._registeredMgmtIp || device.sshConfig?.host || device.sshConfig?.hostBackup || '';
        if (!sshHost) return;
        // Wave 2.3: honor the cooldown window a second time -- the
        // outer tick might have committed us to this device just
        // before the global cooldown was set.
        if (this._inCooldown()) return;
        const safetyTimeout = new Promise((_, rej) => setTimeout(() => rej(new Error('monitor timeout')), live ? 35000 : 10000));
        let contextOk = false;
        try {
            const applied = await Promise.race([this._refreshOneInner(device, deviceId, live), safetyTimeout]);
            if (applied === false) return;
            contextOk = true;
            // Success -- clear any per-device backoff.
            if (device._monitorBackoffMs || device._monitorBackoffUntil) {
                device._monitorBackoffMs = 0;
                device._monitorBackoffUntil = 0;
            }
            if (device._gitCommit == null && ScalerAPI.getDeviceGitCommit && !device._gitCommitFailed) {
                const isCluster = device.subType?.toLowerCase().includes('cluster') ||
                    /ncc\d+/i.test(deviceId) || /\bcl\b/i.test(deviceId);
                let host = sshHost;
                if (isCluster) {
                    const activeHost = await this._resolveActiveNcc(device);
                    if (activeHost) host = activeHost;
                }
                try {
                    const sshUser = device.sshConfig?.user || '';
                    const sshPass = device.sshConfig?.password || '';
                    const identityGuard = window.TopologyDeviceIdentity || null;
                    const identityToken = identityGuard?.makeRequestToken
                        ? identityGuard.makeRequestToken(device, { host, deviceId })
                        : null;
                    const res = await ScalerAPI.getDeviceGitCommit(deviceId, host, sshUser, sshPass);
                    if (identityGuard?.signature && identityToken
                        && identityGuard.signature(device, host) !== identityToken.signature) {
                        return;
                    }
                    const gitCommit = this._pickGitCommit(res || {});
                    if (gitCommit != null) {
                        device._gitCommit = gitCommit;
                        device._gitCommitFetchedAt = Date.now();
                        if (identityGuard?.markMetadataReady) {
                            identityGuard.markMetadataReady(device, 'git', {
                                host,
                                deviceId,
                                source: 'device-monitor',
                            });
                        }
                        if (this._editor?.requestDraw) this._editor.requestDraw();
                        window.dispatchEvent(new CustomEvent('device:context-updated', { detail: { deviceId, device } }));
                    }
                } catch (_) {
                    device._gitCommitFailed = true;
                    setTimeout(() => { device._gitCommitFailed = false; }, 10 * 60 * 1000);
                }
            }
        } catch (e) {
            device._sshReachable = false;

            // Wave 2.3: Retry-After from backend trumps local retry logic.
            if (e?.status === 429 || e?.status === 503) {
                const retry = Number.isFinite(e.retryAfter) ? e.retryAfter : 30;
                this._setCooldown(retry, `HTTP ${e.status} for ${deviceId}`);
                return;
            }

            const isNetwork = e?.message?.includes('Failed to fetch') || e?.message?.includes('ERR_CONNECTION');
            if (isNetwork) {
                this._consecutiveNetFails = (this._consecutiveNetFails || 0) + 1;
                if (this._consecutiveNetFails <= 1) {
                    console.debug('[DeviceMonitor] server unreachable, backing off');
                }
            } else {
                const isTimeout = e?.name === 'AbortError' || e?.message?.includes('timeout');
                if (isTimeout) {
                    console.debug('[DeviceMonitor] timeout for', deviceId);
                } else if (!contextOk) {
                    console.warn('[DeviceMonitor] refresh failed for', deviceId, e?.message);
                }
                // Wave 2.3: per-device exponential backoff on 5xx / unknown
                // errors. Doubles each consecutive failure, capped at 30 min.
                // Prevents one flaky device from burning the whole batch.
                if (!isNetwork && !isTimeout && e?.status !== undefined && e.status >= 500) {
                    const prev = device._monitorBackoffMs || 0;
                    const next = Math.min(
                        Math.max(prev * 2, this._MIN_DEVICE_BACKOFF_MS),
                        this._MAX_DEVICE_BACKOFF_MS
                    );
                    device._monitorBackoffMs = next;
                    device._monitorBackoffUntil = Date.now() + next;
                    console.debug('[DeviceMonitor] per-device backoff for', deviceId,
                        'until', new Date(device._monitorBackoffUntil).toISOString(),
                        `(${Math.round(next / 1000)}s)`);
                }
            }
        }
    },

    async _refreshOneInner(device, deviceId, live) {
        const resolvedIdentity = window.TopologyDeviceIdentity?.resolveIdentity
            ? window.TopologyDeviceIdentity.resolveIdentity(device, { deviceId })
            : null;
        let sshHost = resolvedIdentity?.host || device._registeredMgmtIp || device.sshConfig?._registeredMgmtIp || device.sshConfig?.host || device.sshConfig?.hostBackup || '';
        const isCluster = device.subType?.toLowerCase().includes('cluster') ||
            /ncc\d+/i.test(deviceId) || /\bcl\b/i.test(deviceId);
        if (isCluster) {
            const activeHost = await this._resolveActiveNcc(device);
            if (activeHost) sshHost = activeHost;
        }
        // Capture the topology scope BEFORE the fetch so we can drop a
        // response that arrives after the user navigated away. Without
        // this guard a slow SSH (30-45s on a flaky link) lands on the
        // canvas object that used to live at this label in the previous
        // topology, causing phantom mode flips and zombie stack data.
        const scopeBefore = (window.DeviceState && typeof window.DeviceState.getScope === 'function')
            ? window.DeviceState.getScope()
            : null;
        const identityGuard = window.TopologyDeviceIdentity || null;
        const identityToken = identityGuard?.makeRequestToken
            ? identityGuard.makeRequestToken(device, { host: sshHost, deviceId })
            : null;
        let ctx;
        if (window.DeviceState && typeof window.DeviceState.getContext === 'function') {
            // Orchestrator handles single-flight dedup + TTL cache +
            // per-user/topology namespacing. DeviceMonitor is one of
            // several producers for the same device; before this the
            // monitor + wizard + stack dialog could all SSH the same
            // box within the same second.
            ctx = await window.DeviceState.getContext(deviceId, {
                live,
                sshHost,
                bypassCache: !!live,
            });
        } else {
            ctx = await ScalerAPI.getDeviceContext(deviceId, live, sshHost);
        }
        if (scopeBefore && window.DeviceState && window.DeviceState.getScope() !== scopeBefore) {
            if (this._debug) {
                console.debug('[DeviceMonitor] dropping stale response for', deviceId,
                    '-- topology scope changed during fetch');
            }
            return false;
        }
        // Guard against the canvas object having been removed (user
        // deleted the device or loaded a new topology) while we were
        // waiting on the SSH response.
        if (!this._editor?.objects || !this._editor.objects.includes(device)) {
            return false;
        }
        if (identityGuard?.signature && identityToken && identityGuard.signature(device, sshHost) !== identityToken.signature) {
            if (this._debug) {
                console.debug('[DeviceMonitor] dropping stale response for', deviceId,
                    '-- device identity changed during fetch');
            }
            return false;
        }
        if (identityGuard?.validateResponseForDevice && identityToken) {
            const identityCheck = identityGuard.validateResponseForDevice(device, {}, identityToken, {
                host: sshHost,
                ctx,
                deviceId
            });
            if (!identityCheck.ok) {
                this._logIgnoredIdentityMismatch(device, deviceId, identityCheck.reason, { host: sshHost });
                return false;
            }
        }
        if (device._monitorLastIgnoredContext) {
            delete device._monitorLastIgnoredContext;
        }
        const now = Date.now();
        if (ctx?.stack) {
            const components = Array.isArray(ctx.stack) ? ctx.stack : (ctx.stack?.components || []);
            const fetchedAtMs = ctx.stack_fetched_at ? Date.parse(ctx.stack_fetched_at) : 0;
            const isActuallyLive = live && fetchedAtMs && (now - fetchedAtMs) < 120000;
            device._stackData = {
                components,
                source: isActuallyLive ? 'monitor' : 'cached',
                stack_fetched_at: ctx.stack_fetched_at || '',
                active_ncc_node: ctx.active_ncc_node || ctx.active_ncc_vm || ctx.active_ncc_host || '',
            };
            device._stackCachedAt = fetchedAtMs || now;
            if (identityGuard?.markMetadataReady && (components.length || ctx.stack?.raw_output)) {
                identityGuard.markMetadataReady(device, 'stack', {
                    host: sshHost,
                    deviceId,
                    source: device._stackData.source,
                    data: device._stackData,
                    updatedAt: device._stackCachedAt
                });
            }
        }
        if (ctx?.lldp && Array.isArray(ctx.lldp)) {
            const norm = typeof LldpDialog !== 'undefined' && LldpDialog._normNeighbor
                ? LldpDialog._normNeighbor
                : (n) => ({ interface: n.local || n.interface || '', neighbor: n.neighbor || n.neighbor_device || '', remote_port: n.remote || n.remote_port || '' });
            const normalized = ctx.lldp.map(n => norm(n));
            const neighbors = (typeof LldpDialog !== 'undefined' && LldpDialog._sanitizeLldpNeighbors)
                ? LldpDialog._sanitizeLldpNeighbors(normalized)
                : normalized;
            device._lldpData = {
                neighbors,
                source: 'monitor',
                last_updated: new Date(now).toISOString()
            };
            if (neighbors.length) {
                device._lldpCompletedAt = now;
                if (identityGuard?.markMetadataReady) {
                    identityGuard.markMetadataReady(device, 'lldp', {
                        host: sshHost,
                        deviceId,
                        source: 'monitor',
                        data: device._lldpData,
                        updatedAt: now
                    });
                }
            } else if (device._metadataReadiness?.lldp) {
                delete device._metadataReadiness.lldp;
            }
        }
        device._monitorContext = {
            device_id: ctx?.device_id || ctx?.identity?.device_id || deviceId,
            hostname: ctx?.hostname || ctx?.identity?.hostname || '',
            management_ip: ctx?.mgmt_ip || ctx?.resolved_ip || ctx?.identity?.mgmt_ip || '',
            resolved_ip: ctx?.resolved_ip || ctx?.mgmt_ip || '',
            interfaces: ctx?.interfaces || {},
            wan_interfaces: ctx?.wan_interfaces || [],
            bgp_peers: ctx?.bgp_peers || [],
            bridge_domains: ctx?.bridge_domains || [],
            vrfs: ctx?.vrfs || [],
            loopbacks: ctx?.loopbacks || [],
            config_summary: ctx?.config_summary || {},
            existing_route_targets: ctx?.existing_route_targets || [],
            router_id: (ctx?.config_summary && ctx.config_summary.router_id) || ctx?.router_id || '',
            loopback0_ip: (ctx?.config_summary && ctx.config_summary.loopback0_ip) || ctx?.loopback0_ip || '',
            asn: (ctx?.config_summary && (ctx.config_summary.as_number || ctx.config_summary.asn)) || ctx?.as_number || '',
            timestamp: ctx?.timestamp || new Date(now).toISOString(),
            source: live ? 'device-monitor-live' : 'device-monitor-cache'
        };
        device._monitorConfigFacts = device._monitorContext;
        if (window.TopologyLinkAutofill && typeof window.TopologyLinkAutofill.schedule === 'function') {
            window.TopologyLinkAutofill.schedule(this._editor, 'device-monitor');
        }
        const contextGitCommit = this._pickGitCommit(ctx || {});
        if (contextGitCommit != null) {
            device._gitCommit = contextGitCommit;
            device._gitCommitFetchedAt = now;
            if (identityGuard?.markMetadataReady) {
                identityGuard.markMetadataReady(device, 'git', {
                    host: sshHost,
                    deviceId,
                    source: live ? 'device-monitor-live' : 'device-monitor-cache',
                    updatedAt: now
                });
            }
        }
        if (ctx?.active_ncc_host || ctx?.active_ncc_vm || ctx?.active_ncc_node || ctx?.active_ncc_ip) {
            device.sshConfig = device.sshConfig || {};
            const activeNcc = ctx.active_ncc_host || ctx.active_ncc_vm || ctx.active_ncc_node || '';
            if (activeNcc) {
                device.sshConfig._activeNccHost = activeNcc;
                device.sshConfig._activeNccSource = ctx.active_ncc_source || 'monitor';
                device._activeNccHost = activeNcc;
                device._activeNccSource = ctx.active_ncc_source || 'monitor';
                device._activeNccMonitoredAt = now;
                device.sshConfig._virshInfo = device.sshConfig._virshInfo || {};
                device.sshConfig._virshInfo.activeNcc = activeNcc;
                if (Array.isArray(ctx.ncc_vms) && ctx.ncc_vms.length) {
                    device.sshConfig._virshInfo.nccVms = ctx.ncc_vms.slice();
                }
            }
            if (ctx.active_ncc_ip) {
                device.sshConfig._activeNccIp = ctx.active_ncc_ip;
                device._activeNccIp = ctx.active_ncc_ip;
            }
            if (ctx.ncc_mgmt_ip) {
                device.sshConfig._nccMgmtIp = ctx.ncc_mgmt_ip;
            }
        }
        if (ctx?.device_state != null) {
            const raw = (ctx.device_state || '').toUpperCase();
            // UPGRADING/DEPLOYING are transient ops flags, not GI CLI -- do not flip canvas to GI.
            const GI_STATES = ['GI', 'BASEOS_SHELL', 'ONIE'];
            const REC_STATES = ['RECOVERY', 'DN_RECOVERY'];
            let mode = device._deviceMode || 'unknown';
            if (raw === 'UPGRADING' || raw === 'DEPLOYING') {
                mode = device._deviceMode && device._deviceMode !== 'unknown' ? device._deviceMode : 'unknown';
            } else if (GI_STATES.includes(raw)) mode = 'GI';
            else if (REC_STATES.includes(raw)) mode = 'RECOVERY';
            else if (raw === 'DNOS' || raw === 'STANDALONE') mode = 'DNOS';
            const prevMode = device._deviceMode;
            device._deviceMode = mode;
            // Wave 2026-04-26: stamp the freshness so DeviceModeGate
            // can decide whether to trust the cached mode or force a
            // live probe before allowing DNAAS discovery / capture /
            // config apply.
            device._modeFetchedAt = now;
            device._modeRawState = raw;
            if (prevMode !== mode) {
                window.dispatchEvent(new CustomEvent('device:mode-changed', { detail: { deviceId, device, mode, prevMode } }));
            }
        } else {
            device._deviceMode = device._deviceMode || 'unknown';
        }
        if (ctx?.system_type) {
            device._systemType = ctx.system_type;
            device._systemTypeCachedAt = now;
        }
        if (ctx?.deploy_system_type) {
            device._deploySystemType = ctx.deploy_system_type;
        }
        // Only mark SSH reachable when the bridge actually completed a live SSH
        // round trip. When live=true but the bridge falls back to cached data
        // (upstream SSH failed), keep the previous reachable state intact so
        // the canvas/toolbar indicator can age into "stale" / "unknown".
        const _stackTs = ctx?.stack_fetched_at ? Date.parse(ctx.stack_fetched_at) : 0;
        const _liveOk = live && _stackTs && (now - _stackTs) < 120000;
        if (_liveOk || !live) {
            device._sshReachable = true;
            device._sshReachableAt = now;
        }
        if (ctx?.identity) {
            const prevCfgHost = device._identity?.config_hostname;
            device._identity = ctx.identity;
            const scalerIds = Array.isArray(ctx.identity.scaler_ids) ? ctx.identity.scaler_ids : [];
            const inventoryKeys = Array.isArray(ctx.identity.inventory_keys) ? ctx.identity.inventory_keys : [];
            const knownBackendIdentity = !!(
                ctx.resolved_ip
                || ctx.mgmt_ip
                || ctx.identity.mgmt_ip
                || scalerIds.length
                || inventoryKeys.length
            );
            if (knownBackendIdentity) {
                const guard = window.TopologyDeviceIdentity || null;
                const nonGenerated = (value) => {
                    const clean = String(value || '').trim();
                    if (!clean) return '';
                    return guard?.isGeneratedCanvasLabel?.(clean) ? '' : clean;
                };
                const canonicalId = nonGenerated(ctx.hostname)
                    || nonGenerated(scalerIds[0])
                    || nonGenerated(ctx.device_id)
                    || nonGenerated(deviceId);
                if (canonicalId) {
                    device._registeredDeviceId = device._registeredDeviceId || canonicalId;
                    device._registeredHostname = device._registeredHostname || canonicalId;
                }
                const registeredIp = ctx.identity.mgmt_ip || ctx.mgmt_ip || ctx.resolved_ip || '';
                if (registeredIp) {
                    device._registeredMgmtIp = device._registeredMgmtIp || registeredIp;
                    device.sshConfig = device.sshConfig || {};
                    device.sshConfig._registeredMgmtIp = device.sshConfig._registeredMgmtIp || registeredIp;
                    device.sshConfig._enrichedMgmtIp = device.sshConfig._enrichedMgmtIp || registeredIp;
                }
                if (ctx.identity.serial) {
                    device._registeredSerialNumber = device._registeredSerialNumber || ctx.identity.serial;
                }
                device._monitoredKey = device._monitoredKey || inventoryKeys[0] || scalerIds[0] || canonicalId || '';
                device._monitorRegistered = true;
            }
            const cfgHost = ctx.identity.config_hostname || '';
            if (cfgHost) {
                device._configHostname = cfgHost;
            }
            const currentLabel = (device.label || '').trim();
            let mismatch = cfgHost !== '' && currentLabel !== '' && cfgHost !== currentLabel;

            // Inventory-label precedence: if the canvas label matches an
            // inventory hostname, treat it as authoritative even when the
            // device's running-config hostname differs (e.g. default "CDNOS-RR").
            if (mismatch) {
                const inv = window._deviceInventory || window.deviceInventory;
                if (inv?.devices) {
                    for (const info of Object.values(inv.devices)) {
                        const hn = (info.hostname || '').replace(/,$/, '').trim();
                        if (hn && hn === currentLabel) { mismatch = false; break; }
                    }
                }
            }

            device._hostnameMismatch = mismatch;
            device._identity.hostname_mismatch = mismatch;
            device._identity.canvas_label = currentLabel;
            if (mismatch) {
                if (this._shouldAutoRepairLabel(currentLabel, cfgHost)) {
                    console.warn(`[DeviceMonitor] Auto-repairing label: "${currentLabel}" -> "${cfgHost}"`);
                    device.label = cfgHost;
                    device._hostnameMismatch = false;
                    device._identity.hostname_mismatch = false;
                    device._identity.canvas_label = cfgHost;
                    device._mismatchDismissed = false;
                    device._badgeWorlds = null;
                    const editor = this._editor;
                    if (editor?.autoSave) editor.autoSave();
                    if (editor?.showNotification) {
                        editor.showNotification(
                            `[INFO] Repaired device label: "${currentLabel}" -> "${cfgHost}"`,
                            'info', 6000
                        );
                    }
                } else {
                    if (prevCfgHost !== cfgHost) {
                        device._mismatchDismissed = false;
                    }
                    window.dispatchEvent(new CustomEvent('device:identity-mismatch', {
                        detail: { deviceId, device, configHostname: cfgHost, canvasLabel: currentLabel }
                    }));
                }
            } else {
                device._mismatchDismissed = false;
                device._badgeWorlds = null;
            }
        } else {
            device._identity = null;
            device._hostnameMismatch = false;
            device._mismatchDismissed = false;
            device._badgeWorlds = null;
        }
        const editor = this._editor;
        if (editor?.requestDraw) editor.requestDraw();
        window.dispatchEvent(new CustomEvent('device:context-updated', { detail: { deviceId, device } }));
        return true;
    }
};
