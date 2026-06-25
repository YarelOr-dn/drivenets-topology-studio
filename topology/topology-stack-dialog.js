/**
 * topology-stack-dialog.js - System Stack Table Dialog
 *
 * Shows show system stack output in a table. Live SSH fetch with fallbacks.
 * Modeled after topology-lldp-dialog.js.
 */

'use strict';

window.StackDialog = {
    _pickSshTarget(device, serial = '') {
        if (window.TopologyDeviceIdentity?.resolveIdentity) {
            const resolved = window.TopologyDeviceIdentity.resolveIdentity(device, { deviceId: serial });
            if (resolved.host) return resolved.host;
        }
        if (window.TopologySshTarget && window.TopologySshTarget.pick) {
            return window.TopologySshTarget.pick(device, { serial }).host;
        }
        return (device?.sshConfig?.hostBackup || device?.sshConfig?.host || serial || '').trim();
    },

    _isGeneratedCanvasLabel(value) {
        const clean = String(value || '').trim();
        return /^(NCP|NCP-\d+|S|S\d+)$/i.test(clean);
    },

    _escapeHtml(value) {
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    },

    _pickLookupId(device, serial = '', host = '') {
        if (window.TopologyDeviceIdentity?.resolveIdentity) {
            const resolved = window.TopologyDeviceIdentity.resolveIdentity(device, { deviceId: serial, host });
            if (resolved.deviceId) return resolved.deviceId;
        }
        const candidates = [
            device?._registeredDeviceId,
            device?._registeredHostname,
            device?._monitoredKey,
            device?.deviceSerial,
            device?.serial,
            device?.device_id,
            device?.hostname,
            host,
            serial,
            device?.label
        ].map(v => String(v || '').trim()).filter(Boolean);
        return candidates.find(v => !this._isGeneratedCanvasLabel(v)) || '';
    },

    showSystemStackDialog(editor, device, serial) {
        const self = this;
        const deviceLabel = device?.label || serial;
        const sshConfig = device?.sshConfig || {};
        const host = self._pickSshTarget(device, serial);
        const lookupId = self._pickLookupId(device, serial, host);
        const user = sshConfig.user || '';
        const password = sshConfig.password || '';
        const _stackMetadataState = (data = null) => {
            const guard = window.TopologyDeviceIdentity || null;
            if (!guard?.metadataState) return { ready: true, loading: false, status: 'ready' };
            return guard.metadataState(device, 'stack', { host, deviceId: lookupId || serial || '', data });
        };
        const _normIdentity = (value) => String(value || '').trim().toLowerCase().replace(/[_\-\s.]/g, '');
        const _stackIdentityGuard = () => {
            const cfg = device?.sshConfig || {};
            const label = String(device?.label || '').trim();
            const resolved = window.TopologyDeviceIdentity?.resolveIdentity
                ? window.TopologyDeviceIdentity.resolveIdentity(device, { deviceId: serial, host })
                : null;
            const firstRealName = [
                device?._registeredHostname,
                device?._registeredDeviceId,
                resolved?.deviceId,
                label && !self._isGeneratedCanvasLabel(label) ? label : ''
            ].map(v => String(v || '').trim()).find(v => v && !self._isGeneratedCanvasLabel(v)) || '';
            return {
                requested_device_id: serial || lookupId || label || '',
                requested_host: host || '',
                registered_device_id: device?._registeredDeviceId || '',
                registry_hostname: device?._registeredHostname || firstRealName || '',
                verified_hostname: firstRealName || '',
                hostname: firstRealName || '',
                registry_serial_number: device?._registeredSerialNumber || device?.deviceSerial || device?.serial || cfg._serial || '',
                verified_serial: device?._registeredSerialNumber || device?.deviceSerial || device?.serial || cfg._serial || '',
                serial_number: device?._registeredSerialNumber || device?.deviceSerial || device?.serial || cfg._serial || '',
            };
        };
        const _isTrustedStackData = (data, fromDiskCache = false, requireReadiness = true) => {
            if (!data || !(data.components?.length || data.raw_output)) return false;
            if (requireReadiness) {
                const state = _stackMetadataState(data);
                if (!state.ready) return false;
            }
            const source = String(data.source || '').toLowerCase();
            const isDiskCache = fromDiskCache || source === 'cached' || source.includes('disk');
            if (!isDiskCache) return true;
            if (Array.isArray(data.cache_owner_conflicts) && data.cache_owner_conflicts.length) return false;

            const guard = window.TopologyDeviceIdentity || null;
            const values = guard?.valuesFromResponse ? guard.valuesFromResponse(data) : { serials: [], hostnames: [], deviceIds: [] };
            const cfg = device?.sshConfig || {};
            const label = String(device?.label || serial || '').trim();
            const generatedLabel = self._isGeneratedCanvasLabel(label) || self._isGeneratedCanvasLabel(serial);
            const currentSerials = [
                device?._registeredSerialNumber,
                device?.deviceSerial,
                device?.serial,
                cfg._serial
            ].map(_normIdentity).filter(Boolean);
            const currentNames = [
                device?._registeredDeviceId,
                device?._registeredHostname,
                device?._monitoredKey,
                label && !self._isGeneratedCanvasLabel(label) ? label : ''
            ].map(_normIdentity).filter(Boolean);
            const responseSerials = (values.serials || []).map(_normIdentity).filter(Boolean);
            const responseNames = (values.hostnames || []).concat(values.deviceIds || []).map(_normIdentity).filter(Boolean);
            const intersects = (a, b) => a.some(v => b.includes(v));
            if (currentSerials.length && responseSerials.length && !intersects(currentSerials, responseSerials)) return false;
            if (currentNames.length && responseNames.length && !intersects(currentNames, responseNames)) return false;
            if (generatedLabel && !currentSerials.length && !currentNames.length) return false;
            if (generatedLabel && !responseSerials.length && !responseNames.length) return false;
            return true;
        };
        const _markStackReady = (data) => {
            const guard = window.TopologyDeviceIdentity || null;
            if (guard?.markMetadataReady && data && (data.components?.length || data.raw_output)) {
                guard.markMetadataReady(device, 'stack', {
                    host,
                    deviceId: lookupId || serial || '',
                    source: data.source || 'stack-dialog',
                    data,
                    updatedAt: _parseFetchedAt(data) || Date.now()
                });
            }
        };
        let devMode = (device?._deviceMode || '').toUpperCase() || '';
        const isCluster = sshConfig._isCluster || (device?.platform || '').toUpperCase().startsWith('CL-');
        const _getVirshInfo = () => device?.sshConfig?._virshInfo || {};
        const _normalizeNccLabel = (value) => {
            const raw = String(value || '').trim();
            if (!raw) return '';
            const short = raw.split('.').shift();
            const nccMatch = short.match(/(?:^|[-_])(ncc[-_]?\d+)$/i) || short.match(/^(ncc[-_]?\d+)$/i);
            return nccMatch ? nccMatch[1].replace(/_/g, '-').toUpperCase() : short;
        };
        const _readActiveNcc = () => (
            _getVirshInfo().activeNcc
            || sshConfig._activeNccVm
            || sshConfig._activeNccHost
            || sshConfig._activeNccNode
            || device?._activeNccHost
            || device?._activeNccVm
            || device?._activeNccNode
            || device?._stackData?.active_ncc_node
            || device?._stackData?.active_ncc_host
            || device?._stackData?.active_ncc_vm
            || device?._stackData?.active_ncc
            || ''
        );
        let activeNcc = _readActiveNcc();
        let nccVms = _getVirshInfo().nccVms || sshConfig._nccVms || [];
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
            ? `<span class="stack-ncc-badge" style="display:inline-block;padding:1px 7px;border-radius:4px;font-size:10px;font-weight:600;background:rgba(212,160,23,0.1);color:rgba(212,160,23,0.9);border:1px solid rgba(212,160,23,0.3);margin-left:4px;" title="Active NCC: ${activeNcc}${nccVms.length > 1 ? ' (' + nccVms.length + ' NCCs)' : ''}">ACTIVE: ${_normalizeNccLabel(activeNcc)}</span>`
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
                <button id="stack-table-refresh" title="Refresh stack only (fast: ~5s, runs show system stack + show system)" style="
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
                <button id="stack-table-deep-refresh" title="Deep refresh (slow: ~20s, also re-reads LLDP, git commit, system type, config)" style="
                    background: rgba(212, 160, 23, 0.12);
                    border: 1px solid rgba(212, 160, 23, 0.28);
                    border-radius: 6px;
                    width: 28px;
                    height: 28px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.15s;
                ">
                    <svg id="stack-deep-refresh-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#d4a017" stroke-width="2.5" style="transition: transform 0.3s;">
                        <path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/>
                        <circle cx="12" cy="12" r="2.5"/>
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
            const resolved = window.TopologyDeviceIdentity?.resolveIdentity
                ? window.TopologyDeviceIdentity.resolveIdentity(device, { deviceId: serial, host })
                : null;
            const candidates = [
                device.label,
                serial,
                device._registeredDeviceId,
                device._registeredHostname,
                device._monitoredKey,
                ...(resolved?.candidates || [])
            ].map(v => String(v || '').trim().toLowerCase()).filter(Boolean);
            const match = candidates.includes(String(deviceId).trim().toLowerCase());
            if (match && device._stackData && document.body.contains(dialog) && _stackMetadataState(device._stackData).ready) {
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
                const name = c.name || c.component || '-';
                const hwModel = c.hw_model || '-';
                const revert = c.revert || '-';
                const curr = c.current || '-';
                const tgt = c.target || '-';
                const diff = curr !== tgt && tgt !== '-';
                const copyVersion = curr && curr !== '-' ? String(curr) : '';
                const copyLabel = name && name !== '-' ? String(name) : 'version';
                const rowBg = i % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'transparent';
                const diffBadge = diff ? `<span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#d4a017;margin-left:6px;" title="Current != Target"></span>` : '';
                const copyBtn = copyVersion ? `<button type="button" class="stack-copy-version" data-version="${self._escapeHtml(copyVersion)}" data-label="${self._escapeHtml(copyLabel)}" title="Copy ${self._escapeHtml(copyLabel)} version" style="margin-left:8px;width:22px;height:22px;padding:0;border:none;border-radius:5px;background:rgba(255,255,255,0.06);color:rgba(255,255,255,0.55);cursor:pointer;display:inline-flex;align-items:center;justify-content:center;vertical-align:middle;"><svg width="12" height="12" viewBox="0 0 24 24"><use href="#ico-copy"/></svg></button>` : '';
                return `<tr style="background:${rowBg}; transition: background 0.12s;">
                    <td style="${tdStyle} font-weight: 500;">${self._escapeHtml(name)}</td>
                    <td style="${tdStyle}">${self._escapeHtml(hwModel)}</td>
                    <td style="${tdStyle}">${self._escapeHtml(revert)}</td>
                    <td style="${tdStyle}${diff ? ' color: #d4a017;' : ''}">${self._escapeHtml(curr)}${diffBadge}${copyBtn}</td>
                    <td style="${tdStyle}${diff ? ' color: #27ae60;' : ''}">${self._escapeHtml(tgt)}</td>
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
        const wireVersionCopy = () => {
            content.querySelectorAll('.stack-copy-version').forEach((btn) => {
                btn.onclick = (e) => {
                    e.stopPropagation();
                    const version = btn.getAttribute('data-version') || '';
                    const label = btn.getAttribute('data-label') || 'version';
                    const writer = (typeof window.safeClipboardWrite === 'function')
                        ? window.safeClipboardWrite
                        : (navigator.clipboard?.writeText?.bind(navigator.clipboard) || null);
                    if (!writer || !version) {
                        if (editor.showToast) editor.showToast(`Unable to copy ${label} version`, 'error');
                        return;
                    }
                    const icon = btn.querySelector('svg use');
                    writer(version).then(() => {
                        if (editor.showToast) editor.showToast(`${label} version copied`, 'success');
                        if (icon) icon.setAttribute('href', '#ico-check');
                        btn.style.color = 'rgba(39,174,96,0.9)';
                        setTimeout(() => {
                            if (icon) icon.setAttribute('href', '#ico-copy');
                            btn.style.color = 'rgba(255,255,255,0.55)';
                        }, 1500);
                    }).catch(() => {
                        if (editor.showToast) editor.showToast(`Failed to copy ${label} version`, 'error');
                    });
                };
            });
        };

        const STACK_CACHE_TTL = 300000;
        const STACK_CACHE_LOUD_THRESHOLD = 600000;
        const formatTimestamp = (ts) => {
            if (!ts) return '';
            const d = new Date(ts);
            const timeStr = d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
            const dateStr = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            return `${dateStr} ${timeStr}`;
        };
        const formatAge = (ms) => {
            if (ms == null || !isFinite(ms) || ms < 0) return '';
            const sec = Math.floor(ms / 1000);
            if (sec < 60) return `${sec}s ago`;
            const min = Math.floor(sec / 60);
            if (min < 60) return `${min}m ago`;
            const hr = Math.floor(min / 60);
            if (hr < 48) return `${hr}h ago`;
            const days = Math.floor(hr / 24);
            return `${days}d ago`;
        };
        const buildTimestampRow = (cachedAt, source) => {
            const ageMs = cachedAt ? (Date.now() - cachedAt) : null;
            const stale = ageMs != null && ageMs > STACK_CACHE_TTL;
            const loudStale = ageMs != null && ageMs > STACK_CACHE_LOUD_THRESHOLD;
            const isCached = (source || '').toLowerCase() === 'cached';
            const ageStr = ageMs != null ? ` (${formatAge(ageMs)})` : '';
            let badge = '';
            if (isCached && loudStale) {
                badge = ` <span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;letter-spacing:0.4px;background:rgba(231,76,60,0.15);color:#e74c3c;border:1px solid rgba(231,76,60,0.5);margin-left:8px;">CACHED${ageStr}</span>`;
            } else if (isCached) {
                badge = ` <span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;background:rgba(243,156,18,0.12);color:#f39c12;border:1px solid rgba(243,156,18,0.4);margin-left:8px;">CACHED${ageStr}</span>`;
            } else if (stale) {
                badge = ' <span style="color:#f39c12;font-size:10px;">[STALE]</span>';
            }
            const sourceLabel = isCached ? 'cached (disk)'
                : (source === 'context' ? 'live SSH' : (source || 'live'));
            const sourceColor = isCached ? 'rgba(243,156,18,0.8)' : 'rgba(39,174,96,0.8)';
            return `<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;padding:6px 0;font-size:11px;color:rgba(255,255,255,0.5);">
                <span>Queried: ${formatTimestamp(cachedAt) || '--'}${badge}</span>
                <span style="color:${sourceColor};">${sourceLabel}</span>
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
                const nccLabel = _normalizeNccLabel(activeNcc);
                parts.push(`<span>Active NCC: <strong>${nccLabel}</strong></span>`);
                if (nccVms.length > 1) {
                    const vmLabels = nccVms.map(v => _normalizeNccLabel(v)).join(', ');
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
        const _updateNccBadge = () => {
            const curNcc = _readActiveNcc();
            if (!curNcc || curNcc === activeNcc) return;
            activeNcc = curNcc;
            nccVms = _getVirshInfo().nccVms || sshConfig._nccVms || [];
            const nccLabel = _normalizeNccLabel(curNcc);
            const existing = header.querySelector('.stack-ncc-badge');
            if (existing) {
                existing.textContent = `ACTIVE: ${nccLabel}`;
                existing.title = `Active NCC: ${curNcc}`;
            } else if (isCluster) {
                const badge = document.createElement('span');
                badge.className = 'stack-ncc-badge';
                badge.style.cssText = 'display:inline-block;padding:1px 7px;border-radius:4px;font-size:10px;font-weight:600;background:rgba(212,160,23,0.1);color:rgba(212,160,23,0.9);border:1px solid rgba(212,160,23,0.3);margin-left:4px;';
                badge.textContent = `ACTIVE: ${nccLabel}`;
                badge.title = `Active NCC: ${curNcc}`;
                const titleRow = header.querySelector('div');
                if (titleRow) titleRow.appendChild(badge);
            }
        };
        const _parseFetchedAt = (data) => {
            const raw = data && data.stack_fetched_at;
            if (!raw) return null;
            const ms = Date.parse(raw);
            return isFinite(ms) ? ms : null;
        };
        const updateContent = (data, fromCache = false) => {
            const diskCacheView = fromCache || String(data?.source || '').toLowerCase() === 'cached';
            if (diskCacheView && !_isTrustedStackData(data, true, fromCache)) {
                content.innerHTML = `
                    <div style="text-align:center; padding:40px; color:rgba(255,255,255,0.55);">
                        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom:12px; opacity:0.5;">
                            <rect x="4" y="4" width="16" height="4" rx="1"/><rect x="4" y="10" width="16" height="4" rx="1"/><rect x="4" y="16" width="16" height="4" rx="1"/>
                        </svg>
                        <div style="font-weight:600;color:rgba(255,255,255,0.76);">System stack is loading</div>
                        <div style="font-size:11px;margin-top:8px;color:rgba(255,255,255,0.42);">Waiting for stack data validated against the current device identity.</div>
                    </div>
                `;
                return;
            }
            if (data.device_state) {
                const ds = data.device_state.toUpperCase();
                if (ds && ['DNOS', 'GI', 'RECOVERY'].includes(ds)) {
                    devMode = ds;
                    if (device) device._deviceMode = ds;
                    _updateModeBadge(ds);
                }
            }
            const returnedActiveNcc = data.active_ncc_node || data.active_ncc_host || data.active_ncc_vm || data.active_ncc || '';
            if (isCluster && returnedActiveNcc && device?.sshConfig) {
                const node = returnedActiveNcc;
                const vi = _getVirshInfo();
                const vms = vi.nccVms || [];
                const shortKey = node.replace(/-/g, '').toLowerCase();
                const matchVm = vms.find(v => v.toLowerCase() === node.toLowerCase())
                              || vms.find(v => v.toLowerCase().includes(shortKey));
                if (matchVm || node) {
                    device.sshConfig._virshInfo = device.sshConfig._virshInfo || {};
                    device.sshConfig._virshInfo.activeNcc = matchVm || node;
                }
            }
            if (isCluster && returnedActiveNcc) {
                if (device) device._activeNccHost = returnedActiveNcc;
            }
            _updateNccBadge();
            if (device && !fromCache && (data.components?.length || data.raw_output)) {
                _markStackReady(data);
                device._stackData = data;
                // Prefer the backend-provided device-query timestamp (when the data
                // was actually pulled from the device). Fall back to "now" for the
                // direct-SSH path (source='live') where the live fetch is happening
                // in real time.
                const backendTs = _parseFetchedAt(data);
                device._stackCachedAt = backendTs || Date.now();
                if (editor.requestDraw) editor.requestDraw();
            }
            const cachedAt = device?._stackCachedAt;
            const source = data.source || 'live';
            const infoBanner = buildInfoBanner();
            if (data.components && data.components.length > 0) {
                content.innerHTML = infoBanner + buildTimestampRow(cachedAt, source) + buildTableHtml(data.components);
                wireVersionCopy();
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
        const deepRefreshBtn = document.getElementById('stack-table-deep-refresh');
        const deepRefreshIcon = document.getElementById('stack-deep-refresh-icon');
        refreshBtn.addEventListener('mouseenter', () => {
            refreshBtn.style.background = 'rgba(0, 180, 216, 0.3)';
            refreshBtn.style.borderColor = 'rgba(0, 180, 216, 0.5)';
        });
        refreshBtn.addEventListener('mouseleave', () => {
            refreshBtn.style.background = 'rgba(0, 180, 216, 0.15)';
            refreshBtn.style.borderColor = 'rgba(0, 180, 216, 0.3)';
        });
        if (deepRefreshBtn) {
            deepRefreshBtn.addEventListener('mouseenter', () => {
                deepRefreshBtn.style.background = 'rgba(212, 160, 23, 0.25)';
                deepRefreshBtn.style.borderColor = 'rgba(212, 160, 23, 0.5)';
            });
            deepRefreshBtn.addEventListener('mouseleave', () => {
                deepRefreshBtn.style.background = 'rgba(212, 160, 23, 0.12)';
                deepRefreshBtn.style.borderColor = 'rgba(212, 160, 23, 0.28)';
            });
        }
        const stackAbort = new AbortController();
        if (StackDialog._lastStackAbort) StackDialog._lastStackAbort.abort();
        StackDialog._lastStackAbort = stackAbort;

        // Shared refresh handler. ``deep=false`` -> stack-fast first
        // (default Refresh button). ``deep=true`` -> full live context
        // re-read of LLDP, git commit, system_type, config, etc.
        const _doRefresh = async (deep) => {
            const btn = deep ? deepRefreshBtn : refreshBtn;
            const icon = deep ? deepRefreshIcon : refreshIcon;
            if (!btn) return;
            icon.style.animation = 'stackSpin 1s linear infinite';
            btn.disabled = true;
            const identityGuard = window.TopologyDeviceIdentity || null;
            const identityToken = identityGuard?.makeRequestToken
                ? identityGuard.makeRequestToken(device, { host, deviceId: lookupId || serial || '' })
                : null;
            // Cluster + non-DNOS devices route through the slower
            // virsh-console fallback (10-20s) because the cluster VIP
            // is unclaimed and direct SSH would just hang on the
            // paramiko banner. Tell the operator what's happening AND
            // keep the cached table visible underneath so they can
            // still read the stack while the refresh runs.
            const _devModeUpper = String(devMode || device?._deviceMode || '').toUpperCase();
            const _isClusterNonDnos = isCluster && _devModeUpper && _devModeUpper !== 'DNOS';
            const _spinnerMsg = _isClusterNonDnos
                ? 'Refreshing via virsh console (cluster in ' + _devModeUpper + ', VIP is dead)...'
                : (deep
                    ? 'Deep refresh: re-reading stack + LLDP + git commit + system type...'
                    : 'Fetching live stack via SSH (fast path)...');
            const _spinnerHtml = `
                <div data-role="stack-refresh-spinner" style="display: flex; align-items: center; justify-content: center; padding: 14px; color: rgba(255,255,255,0.6); border-bottom: 1px solid rgba(255,255,255,0.06); margin-bottom: 12px;">
                    <div style="width: 16px; height: 16px; border: 2px solid ${deep ? 'rgba(212,160,23,0.5)' : 'rgba(0, 180, 216, 0.5)'}; border-top-color: ${deep ? '#d4a017' : '#00B4D8'}; border-radius: 50%; animation: stackSpin 1s linear infinite; margin-right: 10px;"></div>
                    <span style="font-size: 12px;">${_spinnerMsg}</span>
                </div>
            `;
            const _existingTable = content.querySelector('table, pre');
            if (_existingTable) {
                const _holder = document.createElement('div');
                _holder.innerHTML = _spinnerHtml;
                content.insertBefore(_holder.firstElementChild, content.firstChild);
            } else {
                content.innerHTML = `
                    <div style="display: flex; align-items: center; justify-content: center; padding: 40px; color: rgba(255,255,255,0.6);">
                        <div style="width: 20px; height: 20px; border: 2px solid ${deep ? 'rgba(212,160,23,0.5)' : 'rgba(0, 180, 216, 0.5)'}; border-top-color: ${deep ? '#d4a017' : '#00B4D8'}; border-radius: 50%; animation: stackSpin 1s linear infinite; margin-right: 12px;"></div>
                        ${_spinnerMsg}
                    </div>
                `;
            }
            try {
                const data = await self._fetchStack(host, user, password, serial, lookupId, null, true, deep, _stackIdentityGuard());
                const identityCheck = identityGuard?.validateResponseForDevice && identityToken
                    ? identityGuard.validateResponseForDevice(device, data, identityToken, { host, deviceId: lookupId || serial || '' })
                    : { ok: true };
                if ((identityGuard?.signature && identityToken
                    && identityGuard.signature(device, host) !== identityToken.signature) || !identityCheck.ok) {
                    content.innerHTML = `
                    <div style="padding: 40px; text-align: center; color: #e67e22;">
                        <div>Stack response ignored</div>
                        <div style="margin-top: 8px; font-size: 11px;">${self._escapeHtml(identityCheck.reason || 'Device SN/host changed while the request was running. Refresh again for the current identity.')}</div>
                    </div>
                `;
                    return;
                }
                updateContent(data);
                if (editor.showToast) {
                    const label = deep ? 'Stack deep-refreshed' : 'Stack refreshed (fast)';
                    editor.showToast(label, 'success');
                }
            } catch (err) {
                content.innerHTML = `
                    <div style="padding: 40px; text-align: center; color: #e74c3c;">
                        <div>Failed to fetch stack</div>
                        <div style="margin-top: 8px; font-size: 11px;">${(err.message || 'SSH connection failed').replace(/</g, '&lt;')}</div>
                    </div>
                `;
                if (editor.showToast) editor.showToast('Stack refresh failed', 'error');
            } finally {
                icon.style.animation = 'none';
                btn.disabled = false;
            }
        };

        refreshBtn.addEventListener('click', () => _doRefresh(false));
        if (deepRefreshBtn) {
            deepRefreshBtn.addEventListener('click', () => _doRefresh(true));
        }

        const hasCache = device?._stackData && _isTrustedStackData(device._stackData, true);
        const cached = hasCache;
        const BACKGROUND_REFRESH_THRESHOLD = 300000;
        const _maybeBackgroundRefresh = () => {
            const ts = device?._stackCachedAt;
            const age = ts ? (Date.now() - ts) : Infinity;
            const isStale = !ts || age > BACKGROUND_REFRESH_THRESHOLD;
            const looksCached = (device?._stackData?.source || '') === 'cached';
            if (!isStale && !looksCached) return;
            const identityGuard = window.TopologyDeviceIdentity || null;
            const identityToken = identityGuard?.makeRequestToken
                ? identityGuard.makeRequestToken(device, { host, deviceId: lookupId || serial || '' })
                : null;
            self._fetchStack(host, user, password, serial, lookupId, stackAbort.signal, true, false, _stackIdentityGuard()).then((fresh) => {
                if (stackAbort.signal.aborted) return;
                if (!document.body.contains(dialog)) return;
                const identityCheck = identityGuard?.validateResponseForDevice && identityToken
                    ? identityGuard.validateResponseForDevice(device, fresh, identityToken, { host, deviceId: lookupId || serial || '' })
                    : { ok: true };
                if ((identityGuard?.signature && identityToken
                    && identityGuard.signature(device, host) !== identityToken.signature) || !identityCheck.ok) return;
                if (fresh && (fresh.components?.length || fresh.raw_output)) {
                    updateContent(fresh);
                    if (editor.showToast) editor.showToast('Stack refreshed (live)', 'success');
                }
            }).catch(() => {
                // Silent failure; user still has cached view. Annotate footer.
                if (!document.body.contains(dialog)) return;
                const footerNote = document.createElement('div');
                footerNote.style.cssText = 'margin-top:8px;padding:6px 10px;font-size:10px;color:#e67e22;background:rgba(230,126,34,0.08);border:1px solid rgba(230,126,34,0.25);border-radius:6px;';
                footerNote.textContent = 'Live refresh failed -- device may be unreachable right now. Showing last cached snapshot.';
                if (!content.querySelector('[data-role="live-refresh-note"]')) {
                    footerNote.setAttribute('data-role', 'live-refresh-note');
                    content.appendChild(footerNote);
                }
            });
        };
        if (cached) {
            updateContent(device._stackData, true);
            _maybeBackgroundRefresh();
        } else {
            const identityGuard = window.TopologyDeviceIdentity || null;
            const identityToken = identityGuard?.makeRequestToken
                ? identityGuard.makeRequestToken(device, { host, deviceId: lookupId || serial || '' })
                : null;
            self._fetchStack(host, user, password, serial, lookupId, stackAbort.signal, false, false, _stackIdentityGuard()).then(data => {
                if (stackAbort.signal.aborted) return;
                const identityCheck = identityGuard?.validateResponseForDevice && identityToken
                    ? identityGuard.validateResponseForDevice(device, data, identityToken, { host, deviceId: lookupId || serial || '' })
                    : { ok: true };
                if ((identityGuard?.signature && identityToken
                    && identityGuard.signature(device, host) !== identityToken.signature) || !identityCheck.ok) {
                    content.innerHTML = `
                    <div style="padding: 40px; text-align: center; color: #e67e22;">
                        <div>Stack response ignored</div>
                        <div style="margin-top: 8px; font-size: 11px;">${self._escapeHtml(identityCheck.reason || 'Device SN/host changed while the request was running. Refresh again for the current identity.')}</div>
                    </div>
                `;
                    return;
                }
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

    /**
     * Strategy ladder for the Stack dialog. Order changes when the user
     * explicitly clicks Refresh:
     *
     *   Initial open  (forceRefresh=false):
     *     1. Cached operational.json (instant)
     *     2. Full live context  (15-25s, populates everything)
     *     3. Direct stack-live  (last resort)
     *
     *   Manual Refresh (forceRefresh=true, deep=false):
     *     1. Fast stack-only via /api/devices/{id}/stack-fast (4-8s)
     *     2. Full live context with bypass_cache (fallback if stack-fast fails)
     *     3. Direct stack-live  (last resort)
     *
     *   Manual Deep Refresh (forceRefresh=true, deep=true):
     *     1. Full live context with bypass_cache (re-reads LLDP, git_commit,
     *        system_type, config too)
     *     2. Direct stack-live  (last resort)
     *
     * The fast path is the default for Refresh because the dialog ONLY
     * renders stack components + device_state + active_ncc -- and that's
     * exactly what stack-fast returns. Skipping the LLDP/shell/config
     * round-trips on every click cuts a busy active NCC from ~25s to
     * ~6s without any user-visible regression: LLDP/git_commit are still
     * refreshed by the background poller every 5 minutes (or on demand
     * via Deep Refresh).
     */
    async _fetchStack(host, user, password, serial, deviceLabel, signal,
                      forceRefresh = false, deep = false, identityGuard = null) {
        const deviceId = deviceLabel || serial || host;
        if (!deviceId || this._isGeneratedCanvasLabel(deviceId)) {
            throw new Error('Not discovered yet. Run probe/discover or add a verified device identity.');
        }

        // Strategy 1 (initial open only): fast cached context.
        if (!forceRefresh && typeof ScalerAPI !== 'undefined' && ScalerAPI.getDeviceContext) {
            try {
                const ctx = await ScalerAPI.getDeviceContext(deviceId, false, host, { identityGuard });
                if (!ctx?.cache_owner_conflicts?.length && ctx?.stack && (Array.isArray(ctx.stack) ? ctx.stack : ctx.stack.components || []).length) {
                    const components = Array.isArray(ctx.stack) ? ctx.stack : (ctx.stack.components || []);
                    const r = {
                        components,
                        source: 'cached',
                        device_state: ctx.device_state || '',
                        system_type: ctx.system_type || '',
                        stack_fetched_at: ctx.stack_fetched_at || '',
                        cache_owner_conflicts: ctx.cache_owner_conflicts || [],
                    };
                    r.hostname = ctx.hostname || ctx.identity?.hostname || '';
                    r.device_id = ctx.device_id || ctx.identity?.device_id || '';
                    r.identity = ctx.identity || null;
                    r.resolved_ip = ctx.resolved_ip || ctx.mgmt_ip || '';
                    if (ctx.active_ncc_node || ctx.active_ncc_host || ctx.active_ncc_vm || ctx.active_ncc_ip) {
                        r.active_ncc_node = ctx.active_ncc_node || ctx.active_ncc_host || ctx.active_ncc_vm || '';
                        r.active_ncc_host = ctx.active_ncc_host || '';
                        r.active_ncc_vm = ctx.active_ncc_vm || '';
                        r.active_ncc_ip = ctx.active_ncc_ip || '';
                    }
                    return r;
                }
            } catch (_) {}
        }

        // Strategy 2a (Refresh, NOT Deep): stack-fast first. Only runs the
        // two commands the dialog renders -- ~4-8s on a healthy active NCC.
        if (forceRefresh && !deep && typeof ScalerAPI !== 'undefined' && ScalerAPI.getDeviceStackFast) {
            try {
                const fast = await ScalerAPI.getDeviceStackFast(deviceId, host, {
                    bypassCache: true,
                    signal,
                    identityGuard,
                });
                if (fast && (fast.components?.length || fast.raw_output)) {
                    return {
                        components: fast.components || [],
                        raw_output: fast.raw_output || '',
                        source: fast.source || 'stack_fast',
                        device_state: fast.device_state || '',
                        active_ncc_node: fast.active_ncc_node || fast.active_ncc_host || fast.active_ncc_vm || '',
                        active_ncc_host: fast.active_ncc_host || '',
                        active_ncc_vm: fast.active_ncc_vm || '',
                        active_ncc_ip: fast.active_ncc_ip || '',
                        hostname: fast.hostname || fast.identity?.hostname || '',
                        device_id: fast.device_id || fast.identity?.device_id || '',
                        identity: fast.identity || null,
                        resolved_ip: fast.resolved_ip || fast.mgmt_ip || '',
                        cache_owner_conflicts: fast.cache_owner_conflicts || [],
                        stack_fetched_at: fast.stack_fetched_at || new Date().toISOString(),
                    };
                }
            } catch (_) {
                // Fall through to the heavier full-context path.
            }
        }

        // Strategy 2b: full live context. Used for the initial open's live
        // tier, for Deep Refresh, AND as a fallback when stack-fast fails.
        // bypass_cache is set whenever the user explicitly clicked Refresh.
        if (typeof ScalerAPI !== 'undefined' && ScalerAPI.getDeviceContext) {
            try {
                const ctxOpts = forceRefresh ? { bypassCache: true, identityGuard } : { identityGuard };
                const ctx = await ScalerAPI.getDeviceContext(deviceId, true, host, ctxOpts);
                if (ctx?.stack) {
                    const components = Array.isArray(ctx.stack) ? ctx.stack : (ctx.stack.components || []);
                    const r = {
                        components,
                        source: deep ? 'context_deep' : 'context',
                        device_state: ctx.device_state || '',
                        system_type: ctx.system_type || '',
                        stack_fetched_at: ctx.stack_fetched_at || '',
                        cache_owner_conflicts: ctx.cache_owner_conflicts || [],
                    };
                    r.hostname = ctx.hostname || ctx.identity?.hostname || '';
                    r.device_id = ctx.device_id || ctx.identity?.device_id || '';
                    r.identity = ctx.identity || null;
                    r.resolved_ip = ctx.resolved_ip || ctx.mgmt_ip || '';
                    if (ctx.active_ncc_node || ctx.active_ncc_host || ctx.active_ncc_vm || ctx.active_ncc_ip) {
                        r.active_ncc_node = ctx.active_ncc_node || ctx.active_ncc_host || ctx.active_ncc_vm || '';
                        r.active_ncc_host = ctx.active_ncc_host || '';
                        r.active_ncc_vm = ctx.active_ncc_vm || '';
                        r.active_ncc_ip = ctx.active_ncc_ip || '';
                    }
                    return r;
                }
            } catch (_) {}
        }

        // Strategy 3: direct stack-live (last resort).
        try {
            const data = await this._fetchStackLive(host, user, password, deviceId, signal);
            if (data && (data.components?.length || data.raw_output)) {
                data.source = 'live';
                if (!data.stack_fetched_at) {
                    data.stack_fetched_at = new Date().toISOString();
                }
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
