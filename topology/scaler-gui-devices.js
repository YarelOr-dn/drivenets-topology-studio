/**
 * ScalerGUI: canvas device list helpers, device manager, sync, quick-load, compare/ops
 * Source: split from scaler-gui.js.bak
 * @requires scaler-api.js
 * @requires scaler-gui.js (core)
 */
(function (G) {
    'use strict';
    if (!G) {
        console.error('[scaler-gui-devices.js] ScalerGUI core not loaded');
        return;
    }
    Object.assign(G, {
        _isDnaasDevice(name) {
            if (!name) return false;
            const u = name.toUpperCase();
            const patterns = ['DNAAS', 'LEAF', 'SPINE', 'FABRIC', 'TOR', 'AGGREGATION', 'AGG-', 'CORE-', '-LEAF', '-SPINE', 'NCM', 'NCF', 'NCC', 'SUPERSPINE'];
            return patterns.some(p => u.includes(p));
        },
        _getCanvasDeviceObjects(includeDnaas = false) {
            const editor = window.topologyEditor;
            if (!editor?.objects) return [];
            return editor.objects
                .filter(o => o.type === 'device' && o.label?.trim())
                .filter(o => includeDnaas || !this._isDnaasDevice(o.label))
                .map(o => ({
                    label: o.label.trim(),
                    sshHost: o.sshConfig?.host || '',
                    sshUser: o.sshConfig?.user || '',
                    sshPassword: o.sshConfig?.password || '',
                    serial: o.deviceSerial || '',
                    isDnaas: this._isDnaasDevice(o.label),
                    _stackData: o._stackData || null,
                    _stackCachedAt: o._stackCachedAt || null,
                    _deviceMode: o._deviceMode || '',
                    _hasCanvasSshConfig: !!(o.sshConfig?.host),
                    _nccMgmtIp: (o.sshConfig?._nccMgmtIp || '').trim(),
                    _isCluster: !!o.sshConfig?._isCluster,
                    _platform: (o.platform || '').trim(),
                }));
        },
        _getCanvasDevices(includeDnaas = false) {
            return this._getCanvasDeviceObjects(includeDnaas).map(d => d.label);
        },
        _resolveDeviceId(label) {
            const devs = this._getCanvasDeviceObjects(true);
            const dev = devs.find(d => d.label === label);
            return {
                label,
                sshHost: dev?.sshHost || '',
                sshUser: dev?.sshUser || '',
                sshPassword: dev?.sshPassword || '',
                serial: dev?.serial || '',
                isDnaas: dev?.isDnaas || false,
            };
        },
        _getWizardDeviceListSync() {
            const canvasDevObjs = this._getCanvasDeviceObjects();
            if (canvasDevObjs.length === 0) return [];
            return canvasDevObjs.map(cd => {
                const sshHost = (cd._isCluster && cd._nccMgmtIp)
                    ? cd._nccMgmtIp
                    : (cd.sshHost || '');
                const cached = this._deviceContexts?.[cd.label];
                const cachedSysType = cached?.system_type || '';
                const plat = this._sanitizeWizardSystemType(cachedSysType)
                    || this._sanitizeWizardSystemType(cd._platform)
                    || '';
                return {
                    id: cd.label,
                    hostname: cd.label,
                    ip: sshHost,
                    ssh_host: sshHost,
                    hasSSH: !!cd._hasCanvasSshConfig,
                    _stackData: cd._stackData || null,
                    _stackCachedAt: cd._stackCachedAt || null,
                    _deviceMode: cd._deviceMode || '',
                    _scalerId: '',
                    platform: plat,
                };
            });
        },
        
        _mergeWizardDeviceListFromApi(devices, apiDevices) {
            if (!devices || !apiDevices || !apiDevices.length) return;
            const apiByName = {};
            const apiByIp = {};
            for (const d of apiDevices) {
                const key = (d.hostname || d.id || '').toLowerCase().trim();
                if (key && !this._isDnaasDevice(d.hostname || d.id || '')) apiByName[key] = d;
                if (d.ip || d.mgmt_ip) apiByIp[(d.ip || d.mgmt_ip).trim()] = d;
            }
            for (const dev of devices) {
                const nameMatch = apiByName[dev.id.toLowerCase()];
                const ipMatch = dev.ssh_host ? apiByIp[dev.ssh_host] : null;
                const api = nameMatch || ipMatch;
                if (!api) continue;
                dev._scalerId = api.hostname || api.id || dev._scalerId;
                const aip = (api.ip || api.mgmt_ip || '').trim();
                if (aip && !dev.ssh_host) {
                    dev.ssh_host = aip;
                    dev.ip = aip;
                }
                const rawPlat = api.system_type || api.platform || '';
                const clean = this._sanitizeWizardSystemType(rawPlat);
                if (clean) dev.platform = clean;
            }
        },
        
        async _getWizardDeviceList() {
            const devices = this._getWizardDeviceListSync();
            if (devices.length === 0) return [];
            let apiDevices = [];
            try {
                apiDevices = (await ScalerAPI.getDevices()).devices || [];
            } catch (e) {
                console.warn('[ScalerGUI] Device list fetch failed:', e);
            }
            this._mergeWizardDeviceListFromApi(devices, apiDevices);
            return devices;
        },
        async openDeviceManager() {
            const content = document.createElement('div');
            content.className = 'scaler-device-manager';
            content.innerHTML = `
                <div class="scaler-toolbar">
                    <button class="scaler-btn scaler-btn-primary" id="dm-add-device">+ Add Device</button>
                    <button class="scaler-btn" id="dm-refresh">Refresh</button>
                </div>
                <div class="scaler-device-list" id="dm-device-list">
                    <div class="scaler-loading">Loading devices...</div>
                </div>
            `;
        
            this.openPanel('device-manager', 'Device Manager', content, {width: '500px', parentPanel: 'scaler-menu'});
        
            await this.refreshDeviceList();
        
            document.getElementById('dm-add-device').onclick = () => this.openAddDeviceDialog();
            document.getElementById('dm-refresh').onclick = () => this.refreshDeviceList();
        },
        
        async refreshDeviceList() {
            const listEl = document.getElementById('dm-device-list');
            if (!listEl) return;
        
            this.state.deviceCache = {};
            const canvasDevObjs = this._getCanvasDeviceObjects(false);
        
            if (canvasDevObjs.length === 0) {
                listEl.innerHTML = '<div class="scaler-empty">No devices on canvas.<br>Add devices to the topology first.</div>';
                return;
            }
        
            const devices = canvasDevObjs.map(co => ({
                id: co.label,
                hostname: co.label,
                ip: co.sshHost || '',
                serial: co.serial || '',
                platform: 'NCP',
                _hasSSH: !!co.sshHost,
            }));
        
            const canvasDevs = canvasDevObjs.reduce((m, co) => { m[co.label] = co; return m; }, {});
            listEl.innerHTML = devices.map(device => {
                this.state.deviceCache[device.id] = device;
                const canvasDev = canvasDevs[device.id];
                const lldpCount = canvasDev?._lldpData?.neighbors?.length ?? '—';
                const lldpNeighbors = canvasDev?._lldpData?.neighbors || [];
                const lldpList = lldpNeighbors.slice(0, 8).map(n => `${n.interface || n.local} -> ${n.neighbor || n.remote}`).join(', ');
                return `
                    <div class="scaler-device-card${device._hasSSH ? '' : ' scaler-device-no-ssh'}" data-device-id="${device.id}">
                        <div class="scaler-device-status" data-status="${device._hasSSH ? 'unknown' : 'no-ssh'}"></div>
                        <div class="scaler-device-info">
                            <div class="scaler-device-name">${device.hostname}</div>
                            <div class="scaler-device-ip">${device.ip || '<span style="font-size:10px;opacity:0.4">No SSH -- right-click device</span>'}</div>
                            <div class="scaler-device-meta">
                                <span class="scaler-dm-mode" title="Mode">—</span>
                                <span class="scaler-dm-lldp scaler-dm-lldp-click" title="LLDP neighbors (click to expand)" data-device-id="${device.id}">LLDP: ${lldpCount}</span>
                                <span class="scaler-dm-svc" title="Services">Svc: —</span>
                            </div>
                            <div class="scaler-device-platform">${device.platform}</div>
                        </div>
                        <div class="scaler-device-actions">
                            <button class="scaler-btn-icon" data-action="test" title="Test Connection"${device._hasSSH ? '' : ' disabled'}>
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                                    <path d="M22 4L12 14.01l-3-3"/>
                                </svg>
                            </button>
                            <button class="scaler-btn-icon" data-action="sync" title="Sync Config"${device._hasSSH ? '' : ' disabled'}>
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 2v6h-6"/>
                                    <path d="M3 12a9 9 0 0 1 15-6.7L21 8"/>
                                </svg>
                            </button>
                            <button class="scaler-btn-icon scaler-btn-danger" data-action="delete" title="Remove from list">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M3 6h18"/>
                                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
                                </svg>
                            </button>
                        </div>
                        <div class="scaler-dm-lldp-expand" data-device-id="${device.id}" style="display:none">
                            <div class="scaler-dm-lldp-list">${lldpList || '—'}</div>
                        </div>
                    </div>
                `;
            }).join('');
        
            ScalerAPI.getDevices().then(data => {
                const apiDevs = data.devices || [];
                const apiMap = {};
                apiDevs.forEach(d => { apiMap[(d.hostname || d.id || '').toLowerCase()] = d; });
                devices.forEach(device => {
                    const apiDev = apiMap[device.hostname.toLowerCase()];
                    if (apiDev) {
                        if (!device.ip && apiDev.ip) device.ip = apiDev.ip;
                        if (apiDev.platform) device.platform = apiDev.platform;
                        if (apiDev.system_type) device.platform = apiDev.system_type;
                    }
                    this.state.deviceCache[device.id] = device;
                    const card = listEl.querySelector(`[data-device-id="${device.id}"]`);
                    if (card) {
                        const ipEl = card.querySelector('.scaler-device-ip');
                        if (ipEl && device.ip) ipEl.textContent = device.ip;
                        const platEl = card.querySelector('.scaler-device-platform');
                        if (platEl && device.platform) platEl.textContent = device.platform;
                    }
                });
            }).catch(e => console.warn('[ScalerGUI] wizard operation failed:', e.message));
        
            devices.slice(0, 10).forEach(device => {
                const sshHost = canvasDevObjs.find(c => c.label === device.id)?.sshHost || device.ip || '';
                ScalerAPI.getDeviceContext(device.id, false, sshHost).then(ctx => {
                    const card = listEl.querySelector(`[data-device-id="${device.id}"]`);
                    if (!card) return;
                    const svc = ctx?.services || {};
                    const cfg = ctx?.config_summary || {};
                    const evpn = cfg?.evpn_services || {};
                    const svcCount = (svc.fxc_count || 0) + (svc.vrf_count || 0) + (Object.values(evpn).filter(Number.isFinite).reduce((a, b) => a + b, 0) || 0);
                    const lldpList = ctx?.lldp || [];
                    const lldpCount = lldpList.length;
                    const lldpStr = lldpList.map(n => `${n.local || n.interface || ''} -> ${n.neighbor || n.remote || ''}`).join(', ') || '—';
                    const modeEl = card.querySelector('.scaler-dm-mode');
                    const lldpEl = card.querySelector('.scaler-dm-lldp-click');
                    const svcEl = card.querySelector('.scaler-dm-svc');
                    const expandList = card.querySelector('.scaler-dm-lldp-list');
                    if (modeEl) modeEl.textContent = 'DNOS';
                    if (lldpEl) lldpEl.textContent = `LLDP: ${lldpCount}`;
                    if (svcEl) svcEl.textContent = `Svc: ${svcCount}`;
                    if (expandList) expandList.textContent = lldpStr;
                }).catch(e => console.warn('[ScalerGUI] wizard operation failed:', e.message));
            });
        
            listEl.querySelectorAll('[data-action]').forEach(btn => {
                btn.onclick = (e) => {
                    e.stopPropagation();
                    const card = btn.closest('.scaler-device-card');
                    const deviceId = card.dataset.deviceId;
                    this.handleDeviceAction(btn.dataset.action, deviceId);
                };
            });
        
            listEl.querySelectorAll('.scaler-device-card').forEach(card => {
                card.onclick = (e) => {
                    if (e.target.closest('.scaler-dm-lldp-click')) return;
                    this.showConfigSummary(card.dataset.deviceId);
                };
            });
            listEl.querySelectorAll('.scaler-dm-lldp-click').forEach(btn => {
                btn.onclick = (e) => {
                    e.stopPropagation();
                    const did = btn.dataset.deviceId;
                    const expand = listEl.querySelector(`.scaler-dm-lldp-expand[data-device-id="${did}"]`);
                    if (expand) {
                        expand.style.display = expand.style.display === 'none' ? 'block' : 'none';
                    }
                };
            });
        },
        
        async handleDeviceAction(action, deviceId) {
            const card = document.querySelector(`[data-device-id="${deviceId}"]`);
            const statusEl = card?.querySelector('.scaler-device-status');
        
            switch(action) {
                case 'test':
                    if (statusEl) statusEl.dataset.status = 'testing';
                    try {
                        const resolved = this._resolveDeviceId(deviceId);
                        await ScalerAPI.testConnection(deviceId, resolved.sshHost);
                        if (statusEl) statusEl.dataset.status = 'ok';
                        this.showNotification(`${deviceId}: Connection OK`, 'success');
                    } catch (error) {
                        if (statusEl) statusEl.dataset.status = 'error';
                        this.showNotification(`${deviceId}: ${error.message}`, 'error');
                    }
                    break;
        
                case 'sync':
                    if (statusEl) statusEl.dataset.status = 'syncing';
                    try {
                        await ScalerAPI.syncDevice(deviceId);
                        if (statusEl) statusEl.dataset.status = 'ok';
                        this.showNotification(`${deviceId}: Config synced`, 'success');
                    } catch (error) {
                        if (statusEl) statusEl.dataset.status = 'error';
                        this.showNotification(`${deviceId}: ${error.message}`, 'error');
                    }
                    break;
        
                case 'delete':
                    if (confirm(`Delete device ${deviceId}?`)) {
                        try {
                            await ScalerAPI.deleteDevice(deviceId);
                            this.showNotification(`${deviceId}: Deleted`, 'success');
                            await this.refreshDeviceList();
                        } catch (error) {
                            this.showNotification(`${deviceId}: ${error.message}`, 'error');
                        }
                    }
                    break;
            }
        },
        
        async openDeviceSelector(title, onSelect, options = {}) {
            const content = document.createElement('div');
            content.innerHTML = '<div class="scaler-loading">Loading devices...</div>';
        
            this.openPanel('device-selector', `Select Device - ${title}`, content, {width: '400px'});
        
            try {
                const canvasDevObjs = this._getCanvasDeviceObjects();
        
                let apiDevices = [];
                try {
                    apiDevices = (options.devices || (await ScalerAPI.getDevices()).devices || []);
                } catch (e) {
                    console.warn('[ScalerGUI] Device list fetch failed:', e);
                }
        
                const apiByName = {};
                const apiByIp = {};
                for (const d of apiDevices) {
                    const key = (d.hostname || d.id || '').toLowerCase().trim();
                    if (key && !this._isDnaasDevice(d.hostname || d.id || '')) apiByName[key] = d;
                    if (d.ip || d.mgmt_ip) apiByIp[(d.ip || d.mgmt_ip).trim()] = d;
                }
        
                let devices = [];
                if (canvasDevObjs.length > 0) {
                    for (const cd of canvasDevObjs) {
                        const nameMatch = apiByName[cd.label.toLowerCase()];
                        const ipMatch = cd.sshHost ? apiByIp[cd.sshHost] : null;
                        const api = nameMatch || ipMatch;
                        devices.push({
                            id: api?.id || api?.hostname || cd.label,
                            hostname: api?.hostname || cd.label,
                            ip: cd.sshHost || api?.ip || api?.mgmt_ip || '',
                            canvasLabel: cd.label,
                            sshHost: cd.sshHost,
                            sshUser: cd.sshUser,
                            sshPassword: cd.sshPassword,
                            serial: cd.serial || api?.serial || '',
                            isDnaas: cd.isDnaas,
                        });
                    }
                }
        
                const changes = this._wizardChangeLog.filter(c => Date.now() - c.timestamp < 300000);
                const changedLabels = new Set(changes.map(c => c.deviceId.toLowerCase()));
        
                const noSshDevices = devices.filter(d => !d.sshHost);
                const hasSshDevices = devices.filter(d => d.sshHost);
        
                content.innerHTML = `
                    <div class="scaler-device-list scaler-device-select-list">
                        ${devices.length === 0 ? '<div class="scaler-empty">No devices found. Add devices to your topology canvas.</div>' : ''}
                        ${hasSshDevices.map(device => {
                            const hasChanges = changedLabels.has(device.canvasLabel.toLowerCase());
                            return `
                            <div class="scaler-device-select-item${hasChanges ? ' scaler-device-changed' : ''}" data-canvas-label="${device.canvasLabel}">
                                <div style="display:flex;flex-direction:column;gap:2px;flex:1">
                                    <span class="scaler-device-name">${device.canvasLabel}</span>
                                    <span class="scaler-device-ip">${device.sshHost}${device.hostname !== device.canvasLabel ? ' (' + device.hostname + ')' : ''}</span>
                                </div>
                                ${hasChanges ? '<span class="scaler-device-change-badge">changed</span>' : ''}
                            </div>
                        `;}).join('')}
                        ${noSshDevices.length ? `
                            <div class="scaler-device-select-separator">No SSH configured</div>
                            ${noSshDevices.map(device => `
                                <div class="scaler-device-select-item scaler-device-no-ssh" data-canvas-label="${device.canvasLabel}">
                                    <span class="scaler-device-name" style="opacity:0.5">${device.canvasLabel}</span>
                                    <span class="scaler-device-ip" style="color:var(--dn-orange,#e67e22);font-size:11px">Set SSH first</span>
                                </div>
                            `).join('')}
                        ` : ''}
                    </div>
                `;
        
                content.querySelectorAll('.scaler-device-select-item').forEach(item => {
                    item.onclick = () => {
                        const label = item.dataset.canvasLabel;
                        const dev = devices.find(d => d.canvasLabel === label);
                        if (!dev?.sshHost) {
                            this.showNotification(`Set SSH address for ${label} first (right-click device > Set SSH)`, 'warning');
                            return;
                        }
                        this.closePanel('device-selector');
                        onSelect(label);
                    };
                });
            } catch (error) {
                content.innerHTML = `<div class="scaler-error">Failed to load devices: ${error.message}</div>`;
            }
        },
        // Placeholder methods for additional features
        async syncAllDevices() {
            // Create modal overlay
            const overlay = document.createElement('div');
            overlay.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.6); z-index: 9999; display: flex; align-items: center; justify-content: center;';
        
            // Create the sync panel
            const panel = document.createElement('div');
            panel.style.cssText = 'background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%); border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.5); width: 500px; max-width: 90vw; max-height: 80vh; display: flex; flex-direction: column; overflow: hidden;';
            panel.innerHTML = `
                <div style="padding: 15px 20px; border-bottom: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.02);">
                    <h3 style="margin: 0; color: #fff; font-size: 16px;">[SYNC] Syncing All Devices</h3>
                    <button id="sync-close-btn" style="background: none; border: none; color: #888; font-size: 24px; cursor: pointer; padding: 0 5px; display: none;">&times;</button>
                </div>
                <div style="padding: 20px; overflow-y: auto; flex: 1;">
                    <div id="sync-status-msg" style="font-size: 14px; margin-bottom: 15px; color: #aaa;">
                        Fetching device list...
                    </div>
                    <div id="sync-device-list" style="max-height: 300px; overflow-y: auto;"></div>
                    <div id="sync-summary" style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); display: none;">
                        <strong style="color: #fff;">Summary:</strong> <span id="sync-summary-text"></span>
                    </div>
                </div>
            `;
            overlay.appendChild(panel);
            document.body.appendChild(overlay);
        
            const statusMsg = panel.querySelector('#sync-status-msg');
            const deviceList = panel.querySelector('#sync-device-list');
            const summary = panel.querySelector('#sync-summary');
            const summaryText = panel.querySelector('#sync-summary-text');
            const closeBtn = panel.querySelector('#sync-close-btn');
        
            closeBtn.onclick = () => overlay.remove();
        
            let successCount = 0;
            let failCount = 0;
        
            try {
                const data = await ScalerAPI.getDevices();
        
                if (data.devices.length === 0) {
                    statusMsg.innerHTML = '[WARN] No devices registered. Add devices first.';
                    statusMsg.style.color = 'var(--warning-color, orange)';
                    closeBtn.style.display = 'block';
                    return;
                }
        
                statusMsg.innerHTML = `Syncing ${data.devices.length} device(s)... Extracting running configs via SSH.`;
        
                // Create device status rows
                for (const device of data.devices) {
                    const row = document.createElement('div');
                    row.id = `sync-row-${device.id}`;
                    row.style.cssText = 'display: flex; justify-content: space-between; padding: 8px 12px; margin-bottom: 4px; background: var(--bg-secondary); border-radius: 4px; align-items: center;';
                    row.innerHTML = `
                        <span style="font-weight: 500;">${device.hostname || device.id}</span>
                        <span class="sync-status" style="color: var(--text-secondary);">
                            <span class="sync-spinner" style="display: inline-block; animation: spin 1s linear infinite;">...</span> Connecting...
                        </span>
                    `;
                    deviceList.appendChild(row);
                }
        
                // Sync each device and update status
                for (const device of data.devices) {
                    const row = panel.querySelector(`#sync-row-${device.id}`);
                    const statusSpan = row.querySelector('.sync-status');
        
                    try {
                        statusSpan.innerHTML = '<span style="display: inline-block; animation: spin 1s linear infinite;">...</span> Extracting config...';
        
                        const result = await ScalerAPI.syncDevice(device.id);
        
                        successCount++;
                        statusSpan.innerHTML = `[OK] Synced (${result.lines || '?'} lines)`;
                        statusSpan.style.color = 'var(--success-color, #4caf50)';
                        row.style.background = 'rgba(76, 175, 80, 0.1)';
                    } catch (e) {
                        failCount++;
                        statusSpan.innerHTML = `[ERROR] ${e.message}`;
                        statusSpan.style.color = 'var(--error-color, #f44336)';
                        row.style.background = 'rgba(244, 67, 54, 0.1)';
                    }
                }
        
                // Show summary
                summary.style.display = 'block';
                if (failCount === 0) {
                    summaryText.innerHTML = `<span style="color: var(--success-color, #4caf50);">[OK] All ${successCount} device(s) synced successfully!</span>`;
                    statusMsg.innerHTML = '[OK] Sync complete! Config cache updated.';
                    statusMsg.style.color = 'var(--success-color, #4caf50)';
                        } else {
                    summaryText.innerHTML = `<span style="color: var(--success-color, #4caf50);">${successCount} succeeded</span>, <span style="color: var(--error-color, #f44336);">${failCount} failed</span>`;
                    statusMsg.innerHTML = '[WARN] Sync completed with errors.';
                    statusMsg.style.color = 'var(--warning-color, orange)';
                }
        
                closeBtn.style.display = 'block';
        
            } catch (error) {
                statusMsg.innerHTML = `[ERROR] Failed to fetch devices: ${error.message}`;
                statusMsg.style.color = 'var(--error-color, #f44336)';
                closeBtn.style.display = 'block';
            }
        },
        
        async openQuickLoad() {
            // Get devices first
            let devices;
            try {
                const data = await ScalerAPI.getDevices();
                devices = data.devices || [];
            } catch (e) {
                this.showNotification('Failed to get devices: ' + e.message, 'error');
                return;
            }
        
            if (devices.length === 0) {
                this.showNotification('No devices registered. Add devices first.', 'warning');
                return;
            }
        
            // Build the panel content HTML
            const content = document.createElement('div');
            content.innerHTML = `
                <div class="scaler-form-group" style="margin-bottom: 15px;">
                    <label>Select Device</label>
                    <select id="quickload-device" class="scaler-select">
                        ${devices.map(d => `<option value="${d.id}">${d.hostname || d.id}</option>`).join('')}
                    </select>
                </div>
                <div id="quickload-files" style="min-height: 200px; max-height: 400px; overflow-y: auto; border: 1px solid var(--border-color); border-radius: 6px; padding: 10px;">
                    <div style="color: var(--text-secondary); text-align: center; padding: 40px;">
                        Loading saved configs...
                    </div>
                </div>
                <div id="quickload-preview" style="display: none; margin-top: 15px; border-top: 1px solid var(--border-color); padding-top: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <strong id="quickload-preview-title" style="color: var(--text-primary);">Preview</strong>
                        <div>
                            <button id="quickload-push-btn" class="scaler-btn scaler-btn-primary" style="margin-right: 8px;">[PUSH] Push to Device</button>
                            <button id="quickload-compare-btn" class="scaler-btn">[COMPARE] Compare</button>
                        </div>
                    </div>
                    <pre id="quickload-preview-content" class="scaler-syntax-preview" style="max-height: 200px; overflow: auto; font-size: 12px; background: var(--bg-tertiary); padding: 10px; border-radius: 4px;"></pre>
                </div>
            `;
        
            // Use the existing openPanel system which works correctly
            this.openPanel('quick-load', '[LOAD] Quick Load Saved Configs', content, { width: '600px' });
        
            // Setup after panel is rendered
            setTimeout(() => {
                const deviceSelect = document.getElementById('quickload-device');
                const filesContainer = document.getElementById('quickload-files');
                const previewSection = document.getElementById('quickload-preview');
                const previewTitle = document.getElementById('quickload-preview-title');
                const previewContent = document.getElementById('quickload-preview-content');
                const pushBtn = document.getElementById('quickload-push-btn');
                const compareBtn = document.getElementById('quickload-compare-btn');
        
                if (!deviceSelect || !filesContainer) {
                    return;
                }
        
                let selectedFile = null;
        
                const loadFiles = async (deviceId) => {
                    filesContainer.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-secondary);">... Loading saved configs...</div>';
                    if (previewSection) previewSection.style.display = 'none';
        
                    try {
                        const response = await fetch((typeof ScalerAPI !== 'undefined' && ScalerAPI._api ? ScalerAPI._api(`/api/config/${encodeURIComponent(deviceId)}/saved-files`) : `/api/config/${encodeURIComponent(deviceId)}/saved-files`));
                        if (!response.ok) throw new Error('Failed to load files');
                        const data = await response.json();
        
                        if (!data.files || data.files.length === 0) {
                            filesContainer.innerHTML = `
                                <div style="text-align: center; padding: 40px; color: var(--text-secondary);">
                                    <div style="font-size: 14px; margin-bottom: 15px;">[NONE]</div>
                                    <div style="font-size: 14px;">No saved configs found for this device.</div>
                                    <div style="font-size: 12px; margin-top: 8px; opacity: 0.7;">Use the wizards to generate and save configs.</div>
                                </div>
                            `;
                            return;
                        }
        
                        filesContainer.innerHTML = data.files.map(f => `
                            <div class="quickload-file-item" data-path="${f.path}" data-filename="${f.filename}" 
                                 style="display: flex; justify-content: space-between; align-items: center; padding: 12px; 
                                        margin-bottom: 6px; background: var(--bg-secondary); border-radius: 6px; cursor: pointer;
                                        border: 2px solid transparent; transition: all 0.15s ease;">
                                <div style="flex: 1;">
                                    <div style="font-weight: 500; color: var(--text-primary); margin-bottom: 4px;">${f.filename}</div>
                                    <div style="font-size: 11px; color: var(--text-secondary);">
                                        Date: ${f.timestamp} • Lines: ${f.lines}
                                        ${f.pushed ? ' • <span style="color: #4caf50;">✓ Pushed</span>' : ''}
                                    </div>
                                </div>
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <button class="quickload-delete-btn" data-path="${f.path}" data-filename="${f.filename}"
                                            style="background: transparent; border: 1px solid #dc3545; color: #dc3545; 
                                                   padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 11px;
                                                   transition: all 0.15s ease;"
                                            onmouseover="this.style.background='#dc3545';this.style.color='#fff';"
                                            onmouseout="this.style.background='transparent';this.style.color='#dc3545';">
                                        [DELETE] Delete
                                    </button>
                                    <span style="color: var(--text-secondary); font-size: 18px;">›</span>
                                </div>
                            </div>
                        `).join('');
        
                        // Add click handlers for file selection
                        filesContainer.querySelectorAll('.quickload-file-item').forEach(item => {
                            item.onclick = async (e) => {
                                // Don't trigger if clicking the delete button
                                if (e.target.closest('.quickload-delete-btn')) return;
        
                                // Highlight selected
                                filesContainer.querySelectorAll('.quickload-file-item').forEach(i => {
                                    i.style.borderColor = 'transparent';
                                    i.style.background = 'var(--bg-secondary)';
                                });
                                item.style.borderColor = 'var(--primary-color, #7c3aed)';
                                item.style.background = 'rgba(124, 58, 237, 0.15)';
        
                                selectedFile = {
                                    path: item.dataset.path,
                                    filename: item.dataset.filename,
                                    deviceId: deviceId
                                };
        
                                // Load preview
                                if (previewTitle) previewTitle.textContent = `Preview: ${item.dataset.filename}`;
                                if (previewContent) previewContent.textContent = 'Loading...';
                                if (previewSection) previewSection.style.display = 'block';
        
                                try {
                                    const resp = await fetch((typeof ScalerAPI !== 'undefined' && ScalerAPI._api ? ScalerAPI._api(`/api/config/file?path=${encodeURIComponent(item.dataset.path)}`) : `/api/config/file?path=${encodeURIComponent(item.dataset.path)}`));
                                    if (resp.ok) {
                                        const text = await resp.text();
                                        if (previewContent) {
                                            previewContent.textContent = text.substring(0, 5000) + (text.length > 5000 ? '\n\n... (truncated)' : '');
                                        }
                                    } else {
                                        if (previewContent) previewContent.textContent = '(Could not load preview)';
                                    }
                                } catch (e) {
                                    if (previewContent) previewContent.textContent = '(Error loading preview)';
                                }
                            };
                        });
        
                        // Add click handlers for delete buttons
                        filesContainer.querySelectorAll('.quickload-delete-btn').forEach(btn => {
                            btn.onclick = async (e) => {
                                e.stopPropagation(); // Prevent file selection
                                const filePath = btn.dataset.path;
                                const fileName = btn.dataset.filename;
        
                                if (!confirm(`Are you sure you want to delete "${fileName}"?\n\nThis action cannot be undone.`)) {
                                    return;
                                }
        
                                try {
                                    const resp = await fetch((typeof ScalerAPI !== 'undefined' && ScalerAPI._api ? ScalerAPI._api(`/api/config/file?path=${encodeURIComponent(filePath)}`) : `/api/config/file?path=${encodeURIComponent(filePath)}`), {
                                        method: 'DELETE'
                                    });
                                    if (resp.ok) {
                                        this.showNotification(`Deleted ${fileName}`, 'success');
                                        // Refresh the file list
                                        loadFiles(deviceId);
                                        // Clear preview if this was the selected file
                                        if (selectedFile && selectedFile.path === filePath) {
                                            selectedFile = null;
                                            if (previewSection) previewSection.style.display = 'none';
                                        }
                                    } else {
                                        const error = await resp.json();
                                        throw new Error(ScalerAPI._formatError(error.detail, 'Delete failed'));
                                    }
                                } catch (e) {
                                    this.showNotification(`Delete failed: ${e.message}`, 'error');
                                }
                            };
                        });
        
                    } catch (e) {
                        filesContainer.innerHTML = `<div style="color: var(--error-color); padding: 40px; text-align: center;">[ERROR] ${e.message}</div>`;
                    }
                };
        
                deviceSelect.onchange = () => loadFiles(deviceSelect.value);
        
                if (pushBtn) {
                    pushBtn.onclick = async () => {
                        if (!selectedFile) {
                            this.showNotification('Select a file first', 'warning');
                            return;
                        }
                        // Push the config to device
                        try {
                            const configContent = await fetch((typeof ScalerAPI !== 'undefined' && ScalerAPI._api ? ScalerAPI._api(`/api/config/file?path=${encodeURIComponent(selectedFile.path)}`) : `/api/config/file?path=${encodeURIComponent(selectedFile.path)}`)).then(r => r.text());
                            const resp = await fetch((typeof ScalerAPI !== 'undefined' && ScalerAPI._api ? ScalerAPI._api(`/api/config/${encodeURIComponent(selectedFile.deviceId)}/push`) : `/api/config/${encodeURIComponent(selectedFile.deviceId)}/push`), {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ config: configContent, filename: selectedFile.filename })
                            });
                            if (resp.ok) {
                                this.showNotification(`Pushed ${selectedFile.filename} to device`, 'success');
                            } else {
                                throw new Error('Push failed');
                            }
                        } catch (e) {
                            this.showNotification(`Push failed: ${e.message}`, 'error');
                        }
                    };
                }
        
                if (compareBtn) {
                    compareBtn.onclick = async () => {
                        if (!selectedFile) {
                            this.showNotification('Select a file first', 'warning');
                            return;
                        }
                        this.openDeviceCompare();
                    };
                }
        
                // Load first device's files automatically
                loadFiles(devices[0].id);
            }, 100);
        },
        openDeviceCompare() {
            const devices = this._getCanvasDevices();
            if (devices.length < 2) { this.showNotification('Add at least 2 devices to the canvas to compare', 'warning'); return; }
            const deviceItems = devices.map(id => ({ id, hostname: id, ip: '' }));
            this.openDeviceSelector('Compare Configs (select first)', (id1) => {
                this.state._compareFirst = id1;
                this.openDeviceSelector('Compare Configs (select second)', async (id2) => {
                    if (id1 === id2) { this.showNotification('Select two different devices', 'warning'); return; }
                    const content = document.createElement('div');
                    content.innerHTML = '<div class="scaler-loading">Comparing configs...</div>';
                    this.openPanel('config-compare', `Compare: ${id1} vs ${id2}`, content, { width: '600px' });
                    try {
                        const r = await ScalerAPI.compareConfigs([id1, id2]);
                        content.innerHTML = `<div class="scaler-diff-view"><pre>${this.escapeHtml(r.diff_text || '(no diff)')}</pre></div>`;
                    } catch (e) { content.innerHTML = `<div class="scaler-error">${e.message}</div>`; }
                }, { devices: deviceItems });
            }, { devices: deviceItems });
        },
        openSyncStatus() {
            const devices = this._getCanvasDevices();
            if (!devices.length) { this.showNotification('Add devices to the canvas first', 'warning'); return; }
            const content = document.createElement('div');
            content.className = 'scaler-sync-status';
            content.innerHTML = '<div class="scaler-loading">Checking sync status...</div>';
            this.openPanel('sync-status', 'Sync Status', content, { width: '500px' });
            (async () => {
                const html = [];
                for (const d of devices) {
                    try {
                        const r = await ScalerAPI.getConfigDiff(d);
                        html.push(`<div class="scaler-sync-row"><span>${d}</span><span class="${r.in_sync ? 'scaler-sync-ok' : 'scaler-sync-out'}">${r.in_sync ? 'In sync' : 'Out of sync'}</span><button class="scaler-btn" data-dev="${d}">View diff</button></div>`);
                    } catch (e) { html.push(`<div class="scaler-sync-row"><span>${d}</span><span class="scaler-sync-err">${e.message}</span></div>`); }
                }
                content.innerHTML = html.join('') || '<div class="scaler-empty">No devices</div>';
                content.querySelectorAll('[data-dev]').forEach(btn => {
                    btn.onclick = () => {
                        const dev = btn.dataset.dev;
                        ScalerAPI.getConfigDiff(dev).then(r => {
                            const pop = document.createElement('div');
                            pop.className = 'scaler-diff-popup';
                            pop.innerHTML = `<pre>${this.escapeHtml(r.diff_text || '')}</pre>`;
                            pop.onclick = () => pop.remove();
                            document.body.appendChild(pop);
                        });
                    };
                });
            })();
        },
        openDeleteHierarchy(deviceId) {
            if (!deviceId) { this.openDeviceSelector('Delete Hierarchy', (id) => this.openDeleteHierarchy(id)); return; }
            const content = document.createElement('div');
            content.innerHTML = '<div class="scaler-form"><div class="scaler-loading">Loading hierarchy options...</div></div>';
            this.openPanel('delete-hierarchy', `Delete Hierarchy - ${deviceId}`, content, { width: '640px' });
            ScalerAPI.getDeleteHierarchyOptions().then(r => {
                const rows = (r.hierarchies || []).map((h, i) => `<tr class="scaler-dh-row" data-hierarchy="${h.hierarchy}" title="Click to select"><td>${i + 1}</td><td>${h.display}</td><td><code style="font-size:0.85em">${this.escapeHtml(h.command)}</code></td><td><span class="scaler-dh-warn">${this.escapeHtml(h.warning || '')}</span></td></tr>`).join('');
                content.innerHTML = `
                    <div class="scaler-form">
                        <div class="scaler-info-box">Select a hierarchy to delete. Each row shows the DNOS command and impact.</div>
                        <table class="scaler-table scaler-dh-table" style="font-size:0.9em"><thead><tr><th>#</th><th>Hierarchy</th><th>DNOS Command</th><th>Warning/Impact</th></tr></thead><tbody>${rows}</tbody></table>
                        <div class="scaler-form-group" style="margin-top:10px">
                            <label>Sub-path (optional)</label>
                            <input type="text" id="dh-subpath" class="scaler-input" placeholder="e.g. evpn-vpws-fxc instance SVC1">
                        </div>
                        <div class="scaler-form-group"><label><input type="checkbox" id="dh-dry" checked> Dry run (preview only)</label></div>
                        <button id="dh-run" class="scaler-btn scaler-btn-primary">Execute</button>
                        <pre id="dh-result" class="scaler-syntax-preview" style="margin-top:10px;min-height:60px;"></pre>
                    </div>`;
                let selected = (r.hierarchies || [])[0]?.hierarchy || '';
                content.querySelectorAll('.scaler-dh-row').forEach(row => {
                    row.addEventListener('click', () => {
                        content.querySelectorAll('.scaler-dh-row').forEach(rr => rr.classList.remove('selected'));
                        row.classList.add('selected');
                        selected = row.dataset.hierarchy;
                    });
                });
                if (content.querySelector('.scaler-dh-row')) content.querySelector('.scaler-dh-row').classList.add('selected');
                document.getElementById('dh-run').onclick = async () => {
                    const hier = content.querySelector('.scaler-dh-row.selected')?.dataset?.hierarchy || selected;
                    const subPath = document.getElementById('dh-subpath')?.value || '';
                    const dry = document.getElementById('dh-dry').checked;
                    const res = document.getElementById('dh-result');
                    res.textContent = 'Running...';
                    try {
                        const result = await ScalerAPI.deleteHierarchyOp(deviceId, hier, dry, subPath);
                        res.textContent = JSON.stringify(result, null, 2);
                        this.showNotification(dry ? 'Dry run complete' : 'Delete complete', 'success');
                    } catch (e) { res.textContent = e.message; this.showNotification(e.message, 'error'); }
                };
            }).catch(e => {
                content.innerHTML = `<div class="scaler-error">${this.escapeHtml(e.message)}</div>`;
            });
        },
        openModifyInterfaces() {
            this.openDeviceSelector('Modify Interfaces', async (deviceId) => {
                const content = document.createElement('div');
                content.innerHTML = '<div class="scaler-loading">Loading interfaces...</div>';
                this.openPanel('modify-interfaces', `Modify Interfaces - ${deviceId}`, content, { width: '500px' });
                try {
                    const r = await ScalerAPI.getInterfaces(deviceId);
                    content.innerHTML = `<div class="scaler-form"><h4>Interfaces (${r.count})</h4><pre class="scaler-syntax-preview">${(r.interfaces || []).map(i => `${i.name} ${i.vlan || ''}`).join('\n') || 'None'}</pre><p class="scaler-summary-hint">Use scaler-wizard for add/remove. This panel shows current state.</p></div>`;
                } catch (e) { content.innerHTML = `<div class="scaler-error">${e.message}</div>`; }
            });
        },
        openBatchOperations() {
            const devices = this._getCanvasDevices();
            if (!devices.length) { this.showNotification('Add devices to the canvas first', 'warning'); return; }
            this.showNotification(`Batch ops: ${devices.length} devices. Use scaler-wizard for push/scale.`, 'info');
        },
        openTemplateManager() {
            const content = document.createElement('div');
            content.innerHTML = '<div class="scaler-loading">Loading templates...</div>';
            this.openPanel('template-manager', 'Policy Templates', content, { width: '500px' });
            ScalerAPI.getTemplates().then(r => {
                const tpl = (r.templates || []).map(t => `<div class="scaler-template-item"><strong>${t.name}</strong><br><span class="scaler-dim">${t.description || ''}</span></div>`).join('');
                content.innerHTML = tpl ? `<div class="scaler-form">${tpl}</div><p class="scaler-summary-hint">Use scaler-wizard to generate from templates.</p>` : '<div class="scaler-empty">No templates</div>';
            }).catch(e => { content.innerHTML = `<div class="scaler-error">${e.message}</div>`; });
        },
        async showConfigSummary(deviceId) {
            const content = document.createElement('div');
            content.className = 'scaler-config-summary';
            content.innerHTML = '<div class="scaler-loading">Loading config summary...</div>';
            this.openPanel('config-summary', `Config Summary - ${deviceId}`, content, {width: '420px', parentPanel: 'device-manager'});
            try {
                const summary = await ScalerAPI.getConfigSummary(deviceId);
                content.innerHTML = '';
                const lines = summary.lines;
                const lo0 = summary.loopback0_ip || '-';
                const asNum = summary.as_number || '-';
                const rid = summary.router_id || '-';
                const rts = (summary.route_targets || []).length;
                const mh = summary.multihoming_interfaces || 0;
                const evpn = summary.evpn_services || {};
                let evpnHtml = '';
                for (const [k, v] of Object.entries(evpn)) {
                    evpnHtml += `<div class="scaler-summary-row"><span>${k}</span><span>${v}</span></div>`;
                }
                content.innerHTML = `
                    <div class="scaler-summary-section">
                        <div class="scaler-summary-row"><span>Lines</span><span>${lines}</span></div>
                        <div class="scaler-summary-row"><span>Loopback0</span><span>${lo0}</span></div>
                        <div class="scaler-summary-row"><span>AS Number</span><span>${asNum}</span></div>
                        <div class="scaler-summary-row"><span>Router ID</span><span>${rid}</span></div>
                        <div class="scaler-summary-row"><span>Route Targets</span><span>${rts}</span></div>
                        <div class="scaler-summary-row"><span>MH Interfaces</span><span>${mh}</span></div>
                    </div>
                    ${evpnHtml ? `<div class="scaler-summary-section"><h5>EVPN Services</h5>${evpnHtml}</div>` : ''}
                    <div class="scaler-summary-hint">Click Sync on the device card to refresh config.</div>
                `;
            } catch (e) {
                content.innerHTML = `<div class="scaler-error">${e.message}<br><br>Ensure scaler_bridge.py is running and device config is synced.</div>`;
            }
        },
        openAddDeviceDialog() {
            const content = document.createElement('div');
            content.innerHTML = `
                <div class="scaler-form">
                    <div class="scaler-form-group"><label>Device IP</label><input type="text" id="add-device-ip" class="scaler-input" placeholder="192.168.1.1"></div>
                    <button id="add-device-btn" class="scaler-btn scaler-btn-primary">Discover and Add</button>
                    <div id="add-device-result" style="margin-top:10px;min-height:24px;"></div>
                </div>`;
            this.openPanel('add-device', 'Add Device', content, { width: '400px', parentPanel: 'device-manager' });
            document.getElementById('add-device-btn').onclick = async () => {
                const ip = (document.getElementById('add-device-ip').value || '').trim();
                const res = document.getElementById('add-device-result');
                if (!ip) { this.showNotification('Enter device IP', 'warning'); return; }
                res.textContent = 'Discovering...';
                try {
                    const r = await ScalerAPI.discoverDevice(ip);
                    res.textContent = `Added: ${r.hostname || r.key} (${r.ip})`;
                    this.showNotification(`Device ${r.hostname || r.key} added`, 'success');
                    if (this.state.activePanels['device-manager']) this.refreshDeviceList();
                } catch (e) { res.textContent = e.message; this.showNotification(e.message, 'error'); }
            };
        }

    });
})(window.ScalerGUI);
