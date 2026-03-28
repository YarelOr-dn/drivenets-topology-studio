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

    init(editor) {
        if (this._editor) return;
        this._editor = editor;
        setTimeout(() => this._tick(true), 2000);
        this._start();
        this._listenForUpgradeEvents();
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
        return true;
    },

    _shouldAutoRepairLabel(currentLabel, cfgHostname) {
        if (!currentLabel || !cfgHostname) return false;

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
        const device = editor.objects.find(o => o.type === 'device' && (o.label === deviceId || o.serial === deviceId));
        if (!device) return Promise.resolve();
        return this._refreshOne(device, live);
    },

    async _resolveActiveNcc(device) {
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
        try {
            for (let i = 0; i < devices.length; i += this._BATCH_SIZE) {
                const batch = devices.slice(i, i + this._BATCH_SIZE);
                await Promise.all(batch.map(d => this._refreshOne(d, live)));
                if (i + this._BATCH_SIZE < devices.length) {
                    await new Promise(r => setTimeout(r, this._BATCH_DELAY_MS));
                }
            }
        } finally {
            this._running = false;
        }
    },

    async _refreshOne(device, live = true) {
        if (typeof ScalerAPI === 'undefined' || !ScalerAPI.getDeviceContext) return;
        const deviceId = device.label || device.deviceSerial || device.serial || '';
        if (!deviceId) return;
        const sshHost = device.sshConfig?.host || device.sshConfig?.hostBackup || '';
        if (!sshHost) return;
        const safetyTimeout = new Promise((_, rej) => setTimeout(() => rej(new Error('monitor timeout')), live ? 35000 : 10000));
        let contextOk = false;
        try {
            await Promise.race([this._refreshOneInner(device, deviceId, live), safetyTimeout]);
            contextOk = true;
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
                    const res = await ScalerAPI.getDeviceGitCommit(deviceId, host, sshUser, sshPass);
                    if (res?.git_commit != null) {
                        device._gitCommit = res.git_commit;
                        device._gitCommitFetchedAt = Date.now();
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
            }
        }
    },

    async _refreshOneInner(device, deviceId, live) {
        let sshHost = device.sshConfig?.host || device.sshConfig?.hostBackup || '';
        const isCluster = device.subType?.toLowerCase().includes('cluster') ||
            /ncc\d+/i.test(deviceId) || /\bcl\b/i.test(deviceId);
        if (isCluster) {
            const activeHost = await this._resolveActiveNcc(device);
            if (activeHost) sshHost = activeHost;
        }
        const ctx = await ScalerAPI.getDeviceContext(deviceId, live, sshHost);
        const now = Date.now();
        if (ctx?.stack) {
            const components = Array.isArray(ctx.stack) ? ctx.stack : (ctx.stack?.components || []);
            device._stackData = { components, source: 'monitor' };
            device._stackCachedAt = now;
        }
        if (ctx?.lldp && Array.isArray(ctx.lldp)) {
            device._lldpData = {
                neighbors: ctx.lldp.map(n => ({
                    interface: n.local || n.interface || '',
                    neighbor: n.neighbor || n.neighbor_device || '',
                    remote_port: n.remote || n.remote_port || ''
                })),
                source: 'monitor',
                last_updated: new Date(now).toISOString()
            };
            device._lldpCompletedAt = now;
        }
        if (ctx?.git_commit != null) {
            device._gitCommit = ctx.git_commit;
            device._gitCommitFetchedAt = now;
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
        device._sshReachable = true;
        device._sshReachableAt = now;
        if (ctx?.identity) {
            const prevCfgHost = device._identity?.config_hostname;
            device._identity = ctx.identity;
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
    }
};
