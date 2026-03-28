/**
 * topology-stack-dialog.js - System Stack Table Dialog
 *
 * Shows show system stack output in a table. Live SSH fetch with fallbacks.
 * Modeled after topology-lldp-dialog.js.
 */

'use strict';

window.StackDialog = {
    showSystemStackDialog(editor, device, serial) {
        const self = this;
        const deviceLabel = device?.label || serial;
        const sshConfig = device?.sshConfig || {};
        const host = sshConfig.host || serial;
        const user = sshConfig.user || '';
        const password = sshConfig.password || '';
        let devMode = (device?._deviceMode || '').toUpperCase() || '';
        const isCluster = sshConfig._isCluster || (device?.platform || '').toUpperCase().startsWith('CL-');
        const virshInfo = sshConfig._virshInfo || {};
        const activeNcc = virshInfo.activeNcc || '';
        const nccVms = virshInfo.nccVms || [];
        const sysType = (device?.platform || '').toUpperCase();

        const existingDialog = document.getElementById('stack-table-dialog');
        if (existingDialog && existingDialog.dataset.serial === String(serial)) {
            existingDialog.remove();
            return;
        }
        if (existingDialog) existingDialog.remove();

        const dialog = document.createElement('div');
        dialog.id = 'stack-table-dialog';
        dialog.dataset.serial = String(serial);
        dialog.style.cssText = `
            position: fixed;
            z-index: 10002;
            min-width: 480px;
            max-width: 700px;
            max-height: 70vh;
            background: rgba(20, 25, 35, 0.75);
            backdrop-filter: blur(40px) saturate(180%);
            -webkit-backdrop-filter: blur(40px) saturate(180%);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 2px 8px rgba(0, 0, 0, 0.2);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        `;

        const header = document.createElement('div');
        header.style.cssText = `
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 14px 18px;
            background: rgba(212, 160, 23, 0.1);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            cursor: move;
            user-select: none;
        `;
        const _modeColors = { DNOS: '#27ae60', GI: '#d4a017', RECOVERY: '#e74c3c' };
        const _modeColor = _modeColors[devMode] || 'rgba(255,255,255,0.4)';
        const _modeBadge = devMode
            ? `<span class="stack-mode-badge" style="display:inline-block;padding:1px 7px;border-radius:4px;font-size:10px;font-weight:700;letter-spacing:0.5px;background:${_modeColor}22;color:${_modeColor};border:1px solid ${_modeColor}55;margin-left:8px;">${devMode}</span>`
            : '';
        const _clusterBadge = isCluster
            ? `<span style="display:inline-block;padding:1px 7px;border-radius:4px;font-size:10px;font-weight:600;background:rgba(0,180,216,0.1);color:rgba(0,180,216,0.9);border:1px solid rgba(0,180,216,0.3);margin-left:4px;">${sysType || 'CL'}</span>`
            : '';
        const _nccBadge = isCluster && activeNcc
            ? `<span style="display:inline-block;padding:1px 7px;border-radius:4px;font-size:10px;font-weight:600;background:rgba(212,160,23,0.1);color:rgba(212,160,23,0.9);border:1px solid rgba(212,160,23,0.3);margin-left:4px;" title="Active NCC: ${activeNcc}${nccVms.length > 1 ? ' (' + nccVms.length + ' NCCs)' : ''}">NCC: ${activeNcc.replace(/^.*-ncc/, 'NCC-')}</span>`
            : '';
        header.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#d4a017" stroke-width="2">
                    <rect x="4" y="4" width="16" height="4" rx="1"/>
                    <rect x="4" y="10" width="16" height="4" rx="1"/>
                    <rect x="4" y="16" width="16" height="4" rx="1"/>
                </svg>
                <span style="color: rgba(255, 255, 255, 0.95); font-weight: 600; font-size: 14px;">
                    System Stack - ${deviceLabel}
                </span>
                ${_modeBadge}${_clusterBadge}${_nccBadge}
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <button id="stack-table-refresh" title="Refresh via live SSH" style="
                    background: rgba(0, 180, 216, 0.15);
                    border: 1px solid rgba(0, 180, 216, 0.3);
                    border-radius: 6px;
                    width: 28px;
                    height: 28px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.15s;
                ">
                    <svg id="stack-refresh-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#00B4D8" stroke-width="2.5" style="transition: transform 0.3s;">
                        <path d="M23 4v6h-6"/><path d="M1 20v-6h6"/>
                        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                    </svg>
                </button>
                <button id="stack-table-close" style="
                    background: rgba(255, 255, 255, 0.1);
                    border: none;
                    border-radius: 6px;
                    width: 28px; height: 28px;
                    cursor: pointer;
                    display: flex; align-items: center; justify-content: center;
                ">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            </div>
        `;

        const content = document.createElement('div');
        content.style.cssText = `padding: 16px; overflow-y: auto; flex: 1;`;
        content.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; padding: 40px; color: rgba(255,255,255,0.6);">
                <div style="width: 20px; height: 20px; border: 2px solid rgba(212, 160, 23, 0.5); border-top-color: #d4a017; border-radius: 50%; animation: stackSpin 1s linear infinite; margin-right: 12px;"></div>
                Loading system stack...
            </div>
        `;

        // Keyframes MUST live on the dialog (not inside replaceable content),
        // otherwise updateContent() destroys them and refresh animation breaks.
        if (!document.getElementById('stack-spin-style')) {
            const spinStyle = document.createElement('style');
            spinStyle.id = 'stack-spin-style';
            spinStyle.textContent = '@keyframes stackSpin { to { transform: rotate(360deg); } }';
            document.head.appendChild(spinStyle);
        }

        dialog.appendChild(header);
        dialog.appendChild(content);
        
        // Keyboard isolation: prevent ALL key events from reaching the global
        // editor keyboard handler while this dialog is open. Without this,
        // Delete/Backspace deletes selected canvas objects, Ctrl+X clears canvas,
        // and 'R' triggers a full page reload.
        dialog.addEventListener('keydown', (e) => { e.stopPropagation(); });
        dialog.addEventListener('keyup', (e) => { e.stopPropagation(); });
        dialog.tabIndex = -1;
        
        document.body.appendChild(dialog);
        dialog.focus();
        dialog.style.left = '50%';
        dialog.style.top = '50%';
        dialog.style.transform = 'translate(-50%, -50%)';

        let isDragging = false, startX, startY, startLeft, startTop;
        header.addEventListener('mousedown', (e) => {
            if (e.target.closest('button')) return;
            isDragging = true;
            const rect = dialog.getBoundingClientRect();
            startX = e.clientX;
            startY = e.clientY;
            startLeft = rect.left;
            startTop = rect.top;
            dialog.style.transform = 'none';
            dialog.style.left = startLeft + 'px';
            dialog.style.top = startTop + 'px';
        });
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            dialog.style.left = (startLeft + e.clientX - startX) + 'px';
            dialog.style.top = (startTop + e.clientY - startY) + 'px';
        });
        document.addEventListener('mouseup', () => { isDragging = false; });

        const onContextUpdated = (e) => {
            const { deviceId } = e.detail || {};
            if (!deviceId || !device) return;
            const match = (device.label && device.label === deviceId) || (String(serial) === String(deviceId));
            if (match && device._stackData && document.body.contains(dialog)) {
                updateContent(device._stackData, true);
            }
        };
        window.addEventListener('device:context-updated', onContextUpdated);
        document.getElementById('stack-table-close').onclick = () => {
            window.removeEventListener('device:context-updated', onContextUpdated);
            dialog.remove();
        };

            const thStyle = 'padding: 10px 12px; text-align: left; color: rgba(255,255,255,0.6); font-size: 11px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid rgba(255,255,255,0.12); white-space: nowrap;';
        const tdStyle = 'padding: 9px 12px; color: rgba(255,255,255,0.85); font-size: 12px; border-bottom: 1px solid rgba(255,255,255,0.06); font-family: "Monaco", "Menlo", "Consolas", monospace;';
        const buildTableHtml = (components) => {
            if (!components || components.length === 0) return '';
            const rows = components.map((c, i) => {
                const curr = c.current || '-';
                const tgt = c.target || '-';
                const diff = curr !== tgt && tgt !== '-';
                const rowBg = i % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'transparent';
                const diffBadge = diff ? `<span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#d4a017;margin-left:6px;" title="Current != Target"></span>` : '';
                return `<tr style="background:${rowBg}; transition: background 0.12s;">
                    <td style="${tdStyle} font-weight: 500;">${(c.name || c.component || '-')}</td>
                    <td style="${tdStyle}">${(c.hw_model || '-')}</td>
                    <td style="${tdStyle}">${(c.revert || '-')}</td>
                    <td style="${tdStyle}${diff ? ' color: #d4a017;' : ''}">${curr}${diffBadge}</td>
                    <td style="${tdStyle}${diff ? ' color: #27ae60;' : ''}">${tgt}</td>
                </tr>`;
            }).join('');
            return `
                <table style="width:100%; border-collapse: collapse; border-spacing: 0;">
                    <thead><tr style="background: rgba(255,255,255,0.04);">
                        <th style="${thStyle}">Component</th>
                        <th style="${thStyle}">HW Model</th>
                        <th style="${thStyle}">Revert</th>
                        <th style="${thStyle}">Current</th>
                        <th style="${thStyle}">Target</th>
                    </tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            `;
        };

        const STACK_CACHE_TTL = 300000;
        const formatTimestamp = (ts) => {
            if (!ts) return '';
            const d = new Date(ts);
            const timeStr = d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
            const dateStr = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            return `${dateStr} ${timeStr}`;
        };
        const buildTimestampRow = (cachedAt, source) => {
            const stale = cachedAt && (Date.now() - cachedAt) > STACK_CACHE_TTL;
            const staleBadge = stale ? ' <span style="color:#f39c12;font-size:10px;">[STALE]</span>' : '';
            return `<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;padding:6px 0;font-size:11px;color:rgba(255,255,255,0.5);">
                <span>Last fetched: ${formatTimestamp(cachedAt) || '--'}${staleBadge}</span>
                <span style="color:rgba(212,160,23,0.8);">${source || 'cached'}</span>
            </div>`;
        };
        const cleanAnsi = (s) => String(s || '').replace(/\x1b\[[0-9;]*[A-Za-z]/g, '').replace(/\x1b\].*?\x07/g, '');
        const buildInfoBanner = () => {
            const _curMode = devMode || (device?._deviceMode || '').toUpperCase();
            const parts = [];
            if (_curMode) {
                const c = _modeColors[_curMode] || 'rgba(255,255,255,0.5)';
                parts.push(`<span style="color:${c};font-weight:600">Mode: ${_curMode}</span>`);
            }
            if (sysType) parts.push(`<span>Type: <strong>${sysType}</strong></span>`);
            if (isCluster && activeNcc) {
                const nccLabel = activeNcc.replace(/^.*-ncc/, 'NCC-');
                parts.push(`<span>Active NCC: <strong>${nccLabel}</strong></span>`);
                if (nccVms.length > 1) {
                    const vmLabels = nccVms.map(v => v.replace(/^.*-ncc/, 'NCC-')).join(', ');
                    parts.push(`<span style="opacity:0.7">All NCCs: ${vmLabels}</span>`);
                }
            }
            if (parts.length === 0) return '';
            return `<div style="display:flex;flex-wrap:wrap;gap:12px;padding:8px 12px;margin-bottom:10px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:8px;font-size:11px;color:rgba(255,255,255,0.7);">${parts.join('<span style="opacity:0.3">|</span>')}</div>`;
        };
        const _updateModeBadge = (mode) => {
            if (!mode) return;
            const c = _modeColors[mode] || 'rgba(255,255,255,0.4)';
            const existing = header.querySelector('.stack-mode-badge');
            if (existing) {
                existing.textContent = mode;
                existing.style.background = c + '22';
                existing.style.color = c;
                existing.style.borderColor = c + '55';
            } else {
                const badge = document.createElement('span');
                badge.className = 'stack-mode-badge';
                badge.style.cssText = `display:inline-block;padding:1px 7px;border-radius:4px;font-size:10px;font-weight:700;letter-spacing:0.5px;background:${c}22;color:${c};border:1px solid ${c}55;margin-left:8px;`;
                badge.textContent = mode;
                const titleRow = header.querySelector('div');
                if (titleRow) titleRow.appendChild(badge);
            }
        };
        const updateContent = (data, fromCache = false) => {
            if (data.device_state) {
                const ds = data.device_state.toUpperCase();
                if (ds && ['DNOS', 'GI', 'RECOVERY'].includes(ds)) {
                    devMode = ds;
                    if (device) device._deviceMode = ds;
                    _updateModeBadge(ds);
                }
            }
            if (device && !fromCache && (data.components?.length || data.raw_output)) {
                device._stackData = data;
                device._stackCachedAt = Date.now();
                if (editor.requestDraw) editor.requestDraw();
            }
            const cachedAt = device?._stackCachedAt;
            const source = data.source || 'live';
            const infoBanner = buildInfoBanner();
            if (data.components && data.components.length > 0) {
                content.innerHTML = infoBanner + buildTimestampRow(cachedAt, source) + buildTableHtml(data.components);
            } else if (data.raw_output) {
                const raw = cleanAnsi(data.raw_output).replace(/</g, '&lt;');
                content.innerHTML = infoBanner + buildTimestampRow(cachedAt, source) + `
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px; padding:8px 12px; background:rgba(212,160,23,0.1); border:1px solid rgba(212,160,23,0.2); border-radius:8px;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#d4a017" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                        <span style="color:rgba(212,160,23,0.9); font-size:11px;">Could not parse table columns. Showing raw CLI output:</span>
                    </div>
                    <pre style="background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:14px; color:rgba(255,255,255,0.8); font-size:11px; font-family:'Monaco','Menlo','Consolas',monospace; white-space:pre-wrap; word-break:break-all; max-height:400px; overflow-y:auto; line-height:1.5;">${raw}</pre>
                `;
            } else {
                content.innerHTML = `
                    <div style="text-align:center; padding:40px; color:rgba(255,255,255,0.5);">
                        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom:12px; opacity:0.5;">
                            <rect x="4" y="4" width="16" height="4" rx="1"/><rect x="4" y="10" width="16" height="4" rx="1"/><rect x="4" y="16" width="16" height="4" rx="1"/>
                        </svg>
                        <div>No stack data available</div>
                        ${data.error ? `<div style="color:#e74c3c; margin-top:8px; font-size:11px;">${String(data.error).replace(/</g, '&lt;')}</div>` : ''}
                        <div style="font-size:11px; margin-top:8px; color:rgba(255,255,255,0.35);">Ensure device has SSH credentials and is reachable</div>
                    </div>
                `;
            }
        };

        const refreshBtn = document.getElementById('stack-table-refresh');
        const refreshIcon = document.getElementById('stack-refresh-icon');
        refreshBtn.addEventListener('mouseenter', () => {
            refreshBtn.style.background = 'rgba(0, 180, 216, 0.3)';
            refreshBtn.style.borderColor = 'rgba(0, 180, 216, 0.5)';
        });
        refreshBtn.addEventListener('mouseleave', () => {
            refreshBtn.style.background = 'rgba(0, 180, 216, 0.15)';
            refreshBtn.style.borderColor = 'rgba(0, 180, 216, 0.3)';
        });
        const stackAbort = new AbortController();
        if (StackDialog._lastStackAbort) StackDialog._lastStackAbort.abort();
        StackDialog._lastStackAbort = stackAbort;

        refreshBtn.addEventListener('click', async () => {
            refreshIcon.style.animation = 'stackSpin 1s linear infinite';
            refreshBtn.disabled = true;
            content.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; padding: 40px; color: rgba(255,255,255,0.6);">
                    <div style="width: 20px; height: 20px; border: 2px solid rgba(0, 180, 216, 0.5); border-top-color: #00B4D8; border-radius: 50%; animation: stackSpin 1s linear infinite; margin-right: 12px;"></div>
                    Fetching live stack via SSH...
                </div>
            `;
            try {
                const data = await self._fetchStack(host, user, password, serial, deviceLabel, null, true);
                updateContent(data);
                if (editor.showToast) editor.showToast('Stack refreshed (live)', 'success');
            } catch (err) {
                content.innerHTML = `
                    <div style="padding: 40px; text-align: center; color: #e74c3c;">
                        <div>Failed to fetch stack</div>
                        <div style="margin-top: 8px; font-size: 11px;">${(err.message || 'SSH connection failed').replace(/</g, '&lt;')}</div>
                    </div>
                `;
                if (editor.showToast) editor.showToast('Stack refresh failed', 'error');
            } finally {
                refreshIcon.style.animation = 'none';
                refreshBtn.disabled = false;
            }
        });

        const hasCache = device?._stackData && (device._stackData.components?.length || device._stackData.raw_output);
        const cached = hasCache;
        if (cached) {
            updateContent(device._stackData, true);
        } else {
            self._fetchStack(host, user, password, serial, deviceLabel, stackAbort.signal).then(data => {
                if (stackAbort.signal.aborted) return;
                updateContent(data);
            }).catch(err => {
                if (stackAbort.signal.aborted) return;
                content.innerHTML = `
                    <div style="text-align:center; padding:40px; color:rgba(255,255,255,0.5);">
                        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#e74c3c" stroke-width="1.5" style="margin-bottom:12px;">
                            <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
                        </svg>
                        <div style="color:#e74c3c; font-weight:500;">Failed to load stack</div>
                        <div style="font-size:11px; margin-top:8px; color:rgba(255,255,255,0.4);">${(err.message || 'Unknown error').replace(/</g, '&lt;')}</div>
                        <div style="font-size:11px; margin-top:12px; color:rgba(255,255,255,0.3);">Click the refresh button to retry</div>
                    </div>
                `;
                if (editor.showToast) editor.showToast('Stack load failed', 'error');
            });
        }
    },

    async _fetchStack(host, user, password, serial, deviceLabel, signal, forceRefresh = false) {
        const deviceId = deviceLabel || serial || host;
        // Strategy 1: Fast cached context from operational.json (skip on manual refresh)
        if (!forceRefresh && typeof ScalerAPI !== 'undefined' && ScalerAPI.getDeviceContext) {
            try {
                const ctx = await ScalerAPI.getDeviceContext(deviceId, false, host);
                if (ctx?.stack && (Array.isArray(ctx.stack) ? ctx.stack : ctx.stack.components || []).length) {
                    const components = Array.isArray(ctx.stack) ? ctx.stack : (ctx.stack.components || []);
                    return { components, source: 'cached', device_state: ctx.device_state || '', system_type: ctx.system_type || '' };
                }
            } catch (_) {}
        }
        // Strategy 2: Live context via scaler_bridge SSH (better resolution, caches result)
        if (typeof ScalerAPI !== 'undefined' && ScalerAPI.getDeviceContext) {
            try {
                const ctx = await ScalerAPI.getDeviceContext(deviceId, true, host);
                if (ctx?.stack) {
                    const components = Array.isArray(ctx.stack) ? ctx.stack : (ctx.stack.components || []);
                    return { components, source: 'context', device_state: ctx.device_state || '', system_type: ctx.system_type || '' };
                }
            } catch (_) {}
        }
        // Strategy 3: Direct SSH via discovery_api (last resort)
        try {
            const data = await this._fetchStackLive(host, user, password, serial, signal);
            if (data && (data.components?.length || data.raw_output)) {
                data.source = 'live';
                return data;
            }
        } catch (_) {}
        throw new Error('No stack data available. Configure SSH and try Refresh.');
    },

    async _fetchStackLive(host, user, password, serial, signal) {
        const deviceId = serial || host;
        const controller = new AbortController();
        if (signal) signal.addEventListener('abort', () => controller.abort(), { once: true });
        const timer = setTimeout(() => controller.abort(), 50000);
        const headers = { 'Content-Type': 'application/json' };
        const body = JSON.stringify({ ssh_host: host, ssh_user: user, ssh_password: password });
        const resp = await fetch(`/api/devices/${encodeURIComponent(deviceId)}/stack-live`, {
            method: 'POST', headers, body, signal: controller.signal
        }).finally(() => clearTimeout(timer));
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || err.error || `HTTP ${resp.status}`);
        }
        return resp.json();
    }
};
