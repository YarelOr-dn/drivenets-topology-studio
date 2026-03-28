// ============================================================================
// TOPOLOGY SSH ADDRESS DIALOG MODULE
// ============================================================================
// Handles the SSH configuration dialog for devices.
// Redesigned: connection-focused, methods always visible, per-method Connect.
//
// Usage:
//   showSSHAddressDialog(editor, device);
// ============================================================================

function _showMacIpPrompt(panel, editor, targetHost, currentMacIp, errorMsg, sshUser, sshPass) {
    const isDark = document.body.classList.contains('dark-mode');
    const bg = isDark ? '#1a1a2e' : '#fff';
    const border = isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)';
    const text = isDark ? '#c8d0da' : '#333';
    const overlay = document.createElement('div');
    overlay.style.cssText = `position:absolute;left:0;right:0;bottom:0;z-index:10;border-radius:0 0 12px 12px;padding:10px 14px;background:${isDark ? 'rgba(15,18,28,0.97)' : 'rgba(255,255,255,0.97)'};border-top:1px solid ${isDark ? 'rgba(230,126,34,0.3)' : 'rgba(230,126,34,0.2)'};`;
    overlay.innerHTML = `
        <div>
            <div style="color:#e67e22;font-weight:600;font-size:12px;margin-bottom:6px;">Mac Unreachable</div>
            <div style="color:${text};font-size:11px;margin-bottom:8px;">${errorMsg}. Update Mac VPN IP to clear host keys remotely.</div>
            <div style="display:flex;gap:6px;align-items:center;margin-bottom:10px;">
                <input type="text" id="_mac-ip-input" value="${currentMacIp}" placeholder="Mac VPN IP (e.g. 10.x.x.x)"
                    style="flex:1;padding:6px 8px;border-radius:4px;border:1px solid ${border};background:${isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.03)'};color:${text};font-size:11px;outline:none;font-family:'Space Grotesk',monospace;"/>
            </div>
            <div style="display:flex;gap:6px;justify-content:flex-end;">
                <button id="_mac-skip-btn" style="padding:5px 12px;border-radius:4px;border:1px solid ${border};background:transparent;color:${text};cursor:pointer;font-size:11px;">Skip</button>
                <button id="_mac-retry-btn" style="padding:5px 12px;border-radius:4px;border:none;background:#e67e22;color:#fff;cursor:pointer;font-size:11px;font-weight:600;">Update & Clear</button>
            </div>
            <div id="_mac-status" style="margin-top:8px;font-size:10px;color:${text};"></div>
        </div>`;
    panel.style.position = 'relative';
    panel.appendChild(overlay);
    const input = overlay.querySelector('#_mac-ip-input');
    const retryBtn = overlay.querySelector('#_mac-retry-btn');
    const skipBtn = overlay.querySelector('#_mac-skip-btn');
    const status = overlay.querySelector('#_mac-status');
    input.addEventListener('keydown', e => e.stopPropagation());
    skipBtn.addEventListener('click', () => overlay.remove());
    retryBtn.addEventListener('click', async () => {
        const newIp = input.value.trim();
        if (!newIp) { status.textContent = 'Enter an IP address'; return; }
        retryBtn.disabled = true;
        retryBtn.textContent = 'Clearing...';
        status.textContent = '';
        try {
            await fetch('/api/xray/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mac: { ip_vpn: newIp } })
            });
            const resp = await fetch('/api/ssh/clear-hostkey', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ host: targetHost })
            });
            const result = await resp.json();
            if (result.mac_cleared) {
                status.style.color = '#27ae60';
                status.textContent = `[OK] Cleared on Mac (${newIp}) -- connecting...`;
                setTimeout(() => {
                    overlay.remove();
                    if (editor._openSshUrl) {
                        if (window.ObjectDetection) window.ObjectDetection._pendingPassword = sshPass;
                        editor._openSshUrl(`ssh://${sshUser}@${targetHost}`);
                    }
                }, 1000);
            } else {
                retryBtn.disabled = false;
                retryBtn.textContent = 'Update & Clear';
                status.style.color = '#e74c3c';
                status.textContent = `Failed: ${result.message || 'SSH to Mac failed'} -- check IP/VPN`;
            }
        } catch (e) {
            retryBtn.disabled = false;
            retryBtn.textContent = 'Update & Clear';
            status.style.color = '#e74c3c';
            status.textContent = `Error: ${e.message}`;
        }
    });
    input.focus();
}

/**
 * Show SSH address configuration dialog
 * @param {TopologyEditor} editor - The editor instance
 * @param {object} device - The device object
 */
function showSSHAddressDialog(editor, device) {
    const existing = document.getElementById('ssh-address-dialog');
    if (existing) {
        if (existing._cleanup) existing._cleanup();
        existing.remove();
    }

    const sshConfig = device.sshConfig || {};
    let _addrHost = device.deviceAddress || '';
    if (_addrHost.includes('@')) _addrHost = _addrHost.split('@').pop();
    const currentHost = sshConfig._userSavedHost || sshConfig.host || _addrHost;
    const currentUser = sshConfig._userSavedUser || sshConfig.user || 'dnroot';
    const currentPass = sshConfig._userSavedPass || sshConfig.password || '';

    const rect = editor.canvas.getBoundingClientRect();
    const deviceScreenX = device.x * editor.zoom + editor.panOffset.x + rect.left;
    const deviceScreenY = device.y * editor.zoom + editor.panOffset.y + rect.top;
    const deviceRadius = (device.radius || 30) * editor.zoom;

    const isDarkMode = editor.darkMode;
    const glassBg = isDarkMode
        ? 'linear-gradient(135deg, rgba(20, 25, 40, 0.85) 0%, rgba(15, 20, 35, 0.9) 100%)'
        : 'linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(240, 245, 255, 0.85) 100%)';
    const glassBorder = isDarkMode ? 'rgba(100, 150, 255, 0.25)' : 'rgba(100, 150, 200, 0.2)';
    const glassShadow = isDarkMode
        ? '0 12px 48px rgba(0, 0, 0, 0.5), 0 4px 16px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
        : '0 12px 48px rgba(0, 0, 0, 0.15), 0 4px 16px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.8)';
    const textColor = isDarkMode ? '#ecf0f1' : '#1a1a2e';
    const labelColor = isDarkMode ? 'rgba(255, 255, 255, 0.7)' : 'rgba(30, 30, 50, 0.7)';
    const inputBg = isDarkMode ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.05)';
    const inputBorder = isDarkMode ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.1)';

    const _lastMethod = sshConfig._lastWorkingMethod || '';
    const _isConsole = _lastMethod === 'console' || _lastMethod === 'virsh_console';
    const _headerGrad = _isConsole ? 'linear-gradient(135deg, #e67e22, #f39c12)' : 'linear-gradient(135deg, #27ae60, #2ecc71)';
    const _headerLabel = _isConsole ? 'Console Connection' : 'SSH Connection';
    const _headerIcon = _isConsole
        ? `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.8" width="18" height="18">
            <rect x="3" y="4" width="18" height="16" rx="2" stroke-width="2"/>
            <rect x="9" y="7" width="6" height="3.5" rx="0.8" stroke-width="1.4"/>
            <line x1="10.5" y1="8" x2="10.5" y2="9.5" stroke-width="1"/><line x1="12" y1="8" x2="12" y2="9.5" stroke-width="1"/><line x1="13.5" y1="8" x2="13.5" y2="9.5" stroke-width="1"/>
            <path d="M12 10.5v2.5" stroke-width="1.8" stroke-linecap="round"/>
            <path d="M12 13c0 1.2-1.5 1.5-1.5 2.5s1.5 1.3 1.5 1.3s1.5-.3 1.5-1.3-1.5-1.3-1.5-2.5" stroke-width="1.4" stroke-linecap="round"/>
            <path d="M9.5 17h5" stroke-width="1.6" stroke-linecap="round"/></svg>`
        : `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" width="18" height="18">
            <rect x="2" y="3" width="20" height="14" rx="2"/><polyline points="7,8 9,10 7,12"/><line x1="11" y1="12" x2="15" y2="12"/></svg>`;

    const inputStyle = `
        width: 100%;
        padding: 6px 8px;
        border-radius: 6px;
        border: 1px solid ${inputBorder};
        background: ${inputBg};
        color: ${textColor};
        font-size: 11px;
        outline: none;
        box-sizing: border-box;
        transition: border-color 0.2s;
    `;

    const panel = document.createElement('div');
    panel.id = 'ssh-address-dialog';
    panel.style.cssText = `
        position: fixed;
        left: ${deviceScreenX}px;
        top: ${deviceScreenY + deviceRadius + 20}px;
        transform: translateX(-50%);
        z-index: 100000;
        background: ${glassBg};
        border: 1px solid ${glassBorder};
        border-radius: 14px;
        padding: 14px 18px;
        min-width: 360px;
        max-width: 420px;
        box-shadow: ${glassShadow};
        backdrop-filter: blur(32px) saturate(180%);
        -webkit-backdrop-filter: blur(32px) saturate(180%);
        opacity: 0;
        animation: sshDialogFadeIn 0.2s ease forwards;
    `;

    if (!document.getElementById('ssh-dialog-styles')) {
        const style = document.createElement('style');
        style.id = 'ssh-dialog-styles';
        style.textContent = `
            @keyframes sshDialogFadeIn {
                from { opacity: 0; transform: translateX(-50%) translateY(8px); }
                to { opacity: 1; transform: translateX(-50%) translateY(0); }
            }
            @keyframes sshProbeSpin {
                to { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }

    panel.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
            <div id="ssh-dialog-icon" style="width: 32px; height: 32px; background: ${_headerGrad}; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                ${_headerIcon}
            </div>
            <div style="flex: 1;">
                <div id="ssh-dialog-title" style="font-size: 13px; font-weight: 600; color: ${textColor};">${_headerLabel}</div>
                <div style="font-size: 11px; color: ${labelColor};">${device.label || 'Device'}<span id="ssh-active-ncc-badge" style="display:none;margin-left:6px;font-size:9px;font-weight:600;color:#27ae60;background:rgba(39,174,96,0.12);padding:1px 6px;border-radius:3px;"></span></div>
            </div>
            <button id="ssh-help-btn" title="Copy SSH command (no password)" style="
                width: 24px; height: 24px; border-radius: 50%;
                border: 1px solid ${inputBorder}; background: ${inputBg};
                color: ${labelColor}; font-size: 12px; font-weight: 600;
                cursor: pointer; display: flex; align-items: center; justify-content: center;
            ">?</button>
        </div>

        <div style="display: flex; gap: 8px; margin-bottom: 10px; align-items: flex-end;">
            <div style="flex: 2; min-width: 0;">
                <label style="display: block; margin-bottom: 2px; color: ${labelColor}; font-size: 10px;">Host / Serial</label>
                <input type="text" id="ssh-host-input" value="${currentHost}"
                    placeholder="IP, hostname, or serial"
                    style="${inputStyle}"
                />
            </div>
            <div style="flex: 1; min-width: 0;">
                <label style="display: block; margin-bottom: 2px; color: ${labelColor}; font-size: 10px;">User</label>
                <input type="text" id="ssh-user-input" value="${currentUser}"
                    placeholder="dnroot"
                    style="${inputStyle}"
                />
            </div>
            <div style="flex: 1; min-width: 0;">
                <label style="display: block; margin-bottom: 2px; color: ${labelColor}; font-size: 10px;">Pass</label>
                <div style="position: relative;">
                    <input type="password" id="ssh-pass-input" value="${currentPass}"
                        placeholder="••••"
                        style="${inputStyle} padding-right: 28px;"
                    />
                    <button id="ssh-toggle-pass" type="button" style="
                        position: absolute; right: 4px; top: 50%; transform: translateY(-50%);
                        background: none; border: none; color: ${labelColor};
                        cursor: pointer; padding: 2px; display: flex;
                    ">
                        <svg id="ssh-eye-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                            <circle cx="12" cy="12" r="3"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>

        <div id="ssh-connection-methods" style="margin: 8px 0; padding: 8px; background: ${inputBg}; border-radius: 6px; font-size: 11px; border: 1px solid ${inputBorder}; min-height: 48px;">
            <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px; color: ${labelColor};">
                <span>Connection Methods</span>
                <span id="ssh-probe-status" style="font-size: 10px; margin-left: auto;"></span>
            </div>
            <div id="ssh-methods-list"></div>
        </div>

        <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap; margin-bottom: 8px;">
            <button id="ssh-discover-console" style="
                padding: 5px 10px; font-size: 11px; border-radius: 6px;
                border: 1px solid ${inputBorder}; background: ${inputBg};
                color: ${textColor}; cursor: pointer;
            ">Discover Console</button>
            <button id="ssh-pdu-power-cycle" style="
                padding: 5px 10px; font-size: 11px; border-radius: 6px;
                border: 1px solid ${isDarkMode ? '#c0392b' : '#e74c3c'}; background: ${inputBg};
                color: ${isDarkMode ? '#e74c3c' : '#c0392b'}; cursor: pointer; display: none;
            ">Power Cycle (PDU)</button>
            <div style="display: flex; align-items: center; gap: 6px; margin-left: auto;">
                <input type="checkbox" id="ssh-clear-hostkey" style="width: 12px; height: 12px; accent-color: #e67e22; cursor: pointer;"/>
                <label for="ssh-clear-hostkey" style="color: ${labelColor}; font-size: 10px; cursor: pointer;">Clear host key</label>
            </div>
        </div>

        <div id="ssh-console-info" style="display: none; margin: 6px 0; padding: 6px 8px; background: ${inputBg}; border-radius: 6px; font-size: 10px; border: 1px solid ${inputBorder};">
            <div id="ssh-console-details" style="color: ${textColor};"></div>
        </div>

        <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top: 10px;">
            <button id="ssh-dialog-cancel" style="
                padding: 6px 14px; border-radius: 6px;
                border: 1px solid ${inputBorder}; background: ${inputBg};
                color: ${textColor}; font-size: 11px; cursor: pointer;
            ">Cancel</button>
            <button id="ssh-dialog-save" style="
                padding: 6px 16px; border-radius: 6px; border: none;
                background: linear-gradient(135deg, #27ae60, #2ecc71);
                color: white; font-size: 11px; font-weight: 600; cursor: pointer;
                box-shadow: 0 2px 8px rgba(39, 174, 96, 0.3);
            ">Save</button>
        </div>
    `;

    document.body.appendChild(panel);

    requestAnimationFrame(() => {
        const panelRect = panel.getBoundingClientRect();
        const padding = 15;
        if (panelRect.right > window.innerWidth - padding) panel.style.left = (window.innerWidth - panelRect.width / 2 - padding) + 'px';
        if (panelRect.left < padding) panel.style.left = (panelRect.width / 2 + padding) + 'px';
        if (panelRect.bottom > window.innerHeight - padding) panel.style.top = (deviceScreenY - deviceRadius - panelRect.height - 10) + 'px';
        if (panelRect.top < padding) panel.style.top = padding + 'px';
    });

    const hostInput = panel.querySelector('#ssh-host-input');
    const userInput = panel.querySelector('#ssh-user-input');
    const passInput = panel.querySelector('#ssh-pass-input');
    const togglePassBtn = panel.querySelector('#ssh-toggle-pass');
    const eyeIcon = panel.querySelector('#ssh-eye-icon');
    const methodsSection = panel.querySelector('#ssh-connection-methods');
    const methodsList = panel.querySelector('#ssh-methods-list');
    const probeStatus = panel.querySelector('#ssh-probe-status');
    const deviceId = device.label || device.deviceSerial || device.serial || '';

    let handleClickOutside, handleEscape;
    const _cleanupListeners = () => {
        if (handleEscape) { document.removeEventListener('keydown', handleEscape); handleEscape = null; }
        if (handleClickOutside) { document.removeEventListener('click', handleClickOutside); handleClickOutside = null; }
    };
    panel._cleanup = _cleanupListeners;
    const closeDialog = () => {
        _cleanupListeners();
        panel.remove();
        setTimeout(() => {
            if (editor.showDeviceSelectionToolbar) editor.showDeviceSelectionToolbar(device);
        }, 50);
    };

    setTimeout(() => hostInput && hostInput.focus(), 50);

    const _isConsoleMethod = (m) => m === 'console' || m === 'virsh_console';
    const _methodLabel = (m) => ({
        ssh_sn: 'SSH (Serial)', ssh_mgmt: 'SSH (Mgmt IP)', ssh_ncc: 'SSH (KVM NCC)',
        virsh_console: 'Virsh Console', console: 'Console (Serial)', ssh_loopback: 'SSH (Loopback)',
    }[m] || m);
    const _methodIcon = (m) => _isConsoleMethod(m)
        ? '<svg width="12" height="12" style="pointer-events:none;"><use href="#ico-console"/></svg>'
        : '<svg width="12" height="12" style="pointer-events:none;"><use href="#ico-terminal"/></svg>';

    let _lastProbeResult = null;
    let _lastDiscovery = null;
    let _probeDebounce = null;

    function connectBtnHtml(method) {
        const isConsole = method === 'console' || method === 'virsh_console';
        const tip = isConsole ? 'Open web terminal (in-browser)' : 'Connect to device';
        return `<button class="ssh-connect-btn" style="
            padding: 2px 6px; font-size: 10px; border-radius: 4px;
            border: 1px solid #27ae60; background: rgba(39,174,96,0.2);
            color: #27ae60; cursor: pointer; flex-shrink: 0;
            display: flex; align-items: center; gap: 2px;
        " title="${tip}">Connect</button>`;
    }

    function doConnect(method, host, port, kvmUser, kvmPass, kvmName, nccVms, consoleServer, consolePort) {
        const user = userInput?.value?.trim() || 'dnroot';
        const password = passInput?.value || '';
        const primaryHost = hostInput?.value?.trim() || '';

        device.sshConfig = device.sshConfig || {};
        device.sshConfig._lastWorkingMethod = method;
        device.sshConfig._virshInfo = null;

        let connectHost = host || primaryHost;
        let connectUser = user;
        let connectPass = password;

        // Set method-appropriate credentials for THIS connection only
        // (do NOT persist to device.sshConfig -- only Save button does that)
        const _isSSHMethod = method && method.startsWith('ssh_');
        if (_isSSHMethod) {
            connectUser = (user === 'dn') ? 'dnroot' : user;
            connectPass = (user === 'dn' && !password) ? 'dnroot' : (password || 'dnroot');
        }

        if (method === 'virsh_console' && host && (kvmUser || user)) {
            const activeNcc = (nccVms && nccVms[0]) || '';
            connectUser = kvmUser || user;
            connectPass = kvmPass || password;
            device.sshConfig._virshInfo = {
                kvmHost: host,
                kvmUser: connectUser,
                kvmPass: connectPass,
                kvmName: kvmName || host,
                nccVms: nccVms || [],
                activeNcc: activeNcc
            };
        }

        if (method === 'console' && consoleServer) {
            connectHost = consoleServer;
            connectUser = user || 'dn';
            connectPass = password || 'drive1234';
            device.sshConfig._consolePort = consolePort || '';
            device.sshConfig._consoleServer = consoleServer;
        }

        closeDialog();

        const _isConsoleMethod = method === 'console' || method === 'virsh_console';

        if (_isConsoleMethod) {
            // Console/Virsh -> in-browser web terminal (handles multi-hop auth)
            if (method === 'virsh_console' && device.sshConfig._virshInfo && window.TerminalPanel?.open) {
                const vi = device.sshConfig._virshInfo;
                window.TerminalPanel.open({
                    deviceId: device.label || device.id || '',
                    host: vi.kvmHost,
                    user: vi.kvmUser || connectUser,
                    method: 'virsh_console',
                    deviceLabel: `${device.label || 'Cluster'} (virsh -> ${vi.activeNcc || 'NCC'})`,
                    password: vi.kvmPass || connectPass,
                    virshInfo: vi,
                });
                editor.showNotification(`[OK] Web terminal opened to ${device.label || connectHost} via virsh console`, 'success', 4000);
            } else if (window.TerminalPanel?.open) {
                window.TerminalPanel.open({
                    deviceId: device.label || device.id || '',
                    host: connectHost,
                    user: connectUser,
                    password: connectPass,
                    method: 'console',
                    deviceLabel: `${device.label || 'Device'} (console ${consolePort || ''})`,
                });
                editor.showNotification(`[OK] Web terminal opened to ${device.label || connectHost} via console`, 'success', 4000);
            } else {
                editor.openTerminalToDevice(device);
            }
        } else {
            let _isIP = /^\d+\.\d+\.\d+\.\d+$/.test(connectHost);
            const _canSSH = _isIP || (_isSSHMethod && connectHost);
            if (_canSSH && editor._openSshUrl) {
                editor._openSshUrl(`ssh://${connectUser}@${connectHost}`);
                if (connectPass) {
                    const cpFn = (typeof window.safeClipboardWrite === 'function')
                        ? window.safeClipboardWrite
                        : (navigator.clipboard?.writeText?.bind(navigator.clipboard) || null);
                    if (cpFn) {
                        cpFn(connectPass).then(() => {
                            editor.showNotification(`[OK] iTerm opened to ${device.label || connectHost}. Password copied.`, 'success', 4000);
                        }).catch(() => {
                            editor.showNotification(`[OK] iTerm opened to ${device.label || connectHost}. Paste password manually.`, 'info', 4000);
                        });
                    } else {
                        editor.showNotification(`[OK] iTerm opened to ${device.label || connectHost}.`, 'success', 4000);
                    }
                } else {
                    editor.showNotification(`[OK] iTerm opened: ssh ${connectUser}@${connectHost}`, 'success', 4000);
                }
            } else if (window.TerminalPanel?.open) {
                window.TerminalPanel.open({
                    deviceId: device.label || device.id || '',
                    host: connectHost,
                    user: connectUser,
                    password: connectPass,
                    method: method || 'ssh_mgmt',
                    deviceLabel: device.label || connectHost || 'Device',
                });
                editor.showNotification(`[OK] Web terminal opened to ${device.label || connectHost}`, 'success', 4000);
            } else if (editor._openSshUrl) {
                editor._openSshUrl(`ssh://${connectUser}@${connectHost}`);
                editor.showNotification(`[OK] Terminal opened to ${device.label || connectHost}`, 'success', 4000);
            }
        }
    }

    const probeAndShowMethods = async () => {
        if (!deviceId || !hostInput?.value?.trim() || !methodsList) return;
        if (probeStatus) {
            probeStatus.innerHTML = '<span style="display:inline-flex;align-items:center;gap:4px;"><span style="display:inline-block;width:8px;height:8px;border:2px solid #27ae60;border-top-color:transparent;border-radius:50%;animation:sshProbeSpin 0.6s linear infinite;"></span> Probing...</span>';
        }
        try {
            const result = await (typeof ScalerAPI !== 'undefined' && ScalerAPI.probeConnection
                ? ScalerAPI.probeConnection(deviceId, hostInput.value.trim())
                : Promise.reject(new Error('ScalerAPI.probeConnection not available')));
            _lastProbeResult = result;
            const hasReachable = (result.methods || []).some(m => m.reachable);
            device._sshReachable = hasReachable;
            if (hasReachable) {
                device._sshReachableAt = Date.now();
            }
            if (editor?.requestDraw) editor.requestDraw();
            if (probeStatus) probeStatus.textContent = '';

            let html = '';
            (result.methods || []).forEach(m => {
                const dot = m.reachable ? '#27ae60' : '#95a5a6';
                const isRec = result.recommended === m.method;
                const recBg = isRec ? (isDarkMode ? 'rgba(39,174,96,0.12)' : 'rgba(39,174,96,0.08)') : 'transparent';
                const border = isRec ? 'border:1px solid #27ae60;' : 'border:1px solid transparent;';
                let hostDisplay = m.port != null ? `${m.host}:${m.port}` : m.host;
                if (m.method === 'virsh_console' && m.kvm_host_name) hostDisplay = `${m.kvm_host_name} (${m.host})`;
                const kvmUser = m.kvm_credentials?.username || '';
                const kvmPass = m.kvm_credentials?.password || '';
                const nccVms = (m.ncc_vms || []).filter(Boolean);
                const activeNcc = (m.vms_running && m.vms_running[0]) || nccVms[0] || '';

                html += `<div class="ssh-probe-method" data-method="${m.method}" data-host="${m.host}" data-port="${m.port}" data-reachable="${m.reachable}"
                    ${kvmUser ? `data-kvm-user="${kvmUser}" data-kvm-pass="${kvmPass}"` : ''}
                    ${m.kvm_host_name ? `data-kvm-name="${m.kvm_host_name}"` : ''}
                    data-ncc-vms="${(nccVms || []).join(',')}"
                    data-active-ncc="${activeNcc}"
                    style="display:flex;align-items:center;gap:6px;padding:4px 6px;margin:2px 0;border-radius:5px;${border}background:${recBg};${m.reachable ? 'opacity:1;' : 'opacity:0.45;'}"
                    title="${m.reachable ? 'Click row to select, Connect to open terminal' : 'Unreachable'}">
                    <span style="width:6px;height:6px;border-radius:50%;background:${dot};flex-shrink:0;${isRec ? 'box-shadow:0 0 4px ' + dot + ';' : ''}"></span>
                    <span style="display:flex;align-items:center;color:${textColor};">${_methodIcon(m.method)}</span>
                    <span style="color:${textColor};font-weight:${isRec ? '600' : '400'};">${_methodLabel(m.method)}</span>
                    <span style="color:${labelColor};margin-left:auto;font-size:10px;">${hostDisplay}</span>
                    ${m.reachable && m.latency_ms != null ? `<span style="color:#27ae60;font-weight:600;">${m.latency_ms}ms</span>` : ''}
                    ${m.reachable ? connectBtnHtml(m.method) : ''}
                </div>${m.vm_warning ? `<div style="padding:2px 6px 4px 24px;font-size:10px;color:#e67e22;">[WARN] ${m.vm_warning}</div>` : ''}`;
            });

            if (result.cluster) {
                html += _renderClusterInfo(result.cluster, textColor, labelColor, inputBg, inputBorder, connectBtnHtml, methodsList);
            }
            methodsList.innerHTML = html;

            // For cluster devices: show active NCC badge and auto-default host
            if (result.cluster?.active_ncc_vm) {
                const nccBadge = panel.querySelector('#ssh-active-ncc-badge');
                if (nccBadge) {
                    nccBadge.textContent = `Active: ${result.cluster.active_ncc_vm}`;
                    nccBadge.style.display = 'inline';
                }
                if (!sshConfig._userSavedHost) {
                    const activeRow = Array.from(methodsList.querySelectorAll('.ssh-probe-method[data-is-active-ncc="true"]')).find(r => r.dataset.reachable === 'true');
                    if (activeRow) {
                        const activeHost = activeRow.dataset.host;
                        if (activeHost && hostInput) {
                            hostInput.value = activeHost;
                            userInput.value = 'dnroot';
                            passInput.value = 'dnroot';
                        }
                        panel._selectedMethod = 'ssh_ncc';
                    }
                }
            }

            // If user has a saved host, re-highlight the method matching it
            const _savedH = sshConfig._userSavedHost || '';
            if (_savedH) {
                let matched = null;
                methodsList.querySelectorAll('.ssh-probe-method[data-reachable="true"]').forEach(row => {
                    row.style.background = 'transparent';
                    row.style.borderColor = 'transparent';
                    const dot = row.querySelector('span:first-child');
                    if (dot) dot.style.boxShadow = '';
                    const rHost = (row.dataset.host || '').toLowerCase();
                    if (rHost === _savedH.toLowerCase() && !matched) {
                        matched = row;
                    }
                });
                if (matched) {
                    matched.style.background = isDarkMode ? 'rgba(39,174,96,0.12)' : 'rgba(39,174,96,0.08)';
                    matched.style.borderColor = '#27ae60';
                    const dot = matched.querySelector('span:first-child');
                    if (dot) dot.style.boxShadow = '0 0 4px #27ae60';
                    panel._selectedMethod = matched.dataset.method;
                }
            }

            methodsList.querySelectorAll('.ssh-connect-btn').forEach(btn => {
                let _connecting = false;
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    if (_connecting) return;
                    const row = btn.closest('.ssh-probe-method');
                    if (!row || row.dataset.reachable !== 'true') return;
                    const h = row.dataset.host;
                    const meth = row.dataset.method;
                    if (!h || !meth) return;
                    _connecting = true;
                    btn.style.opacity = '0.5';
                    btn.style.pointerEvents = 'none';
                    const kvmUser = row.dataset.kvmUser || '';
                    const kvmPass = row.dataset.kvmPass || '';
                    const kvmName = row.dataset.kvmName || h;
                    const nccVms = row.dataset.nccVms ? row.dataset.nccVms.split(',').filter(Boolean) : [];
                    const activeNcc = row.dataset.activeNcc || nccVms[0] || '';
                    if (meth === 'virsh_console') {
                        panel._virshInfo = { kvmHost: h, kvmUser: kvmUser || 'dn', kvmPass: kvmPass || 'drive1234!', kvmName, nccVms, activeNcc };
                    } else if (meth === 'console') {
                        panel._virshInfo = null;
                    } else {
                        if (hostInput) hostInput.value = h;
                        if (userInput) userInput.value = 'dnroot';
                        if (passInput) passInput.value = 'dnroot';
                        panel._virshInfo = null;
                    }
                    panel._selectedMethod = meth;
                    doConnect(meth, h, row.dataset.port, kvmUser || 'dn', kvmPass || 'drive1234!', kvmName, nccVms, null, null);
                });
            });

            methodsList.querySelectorAll('.ssh-probe-method[data-reachable="true"]').forEach(el => {
                el.addEventListener('click', (e) => {
                    if (e.target.closest('.ssh-connect-btn')) return;
                    const h = el.dataset.host;
                    const meth = el.dataset.method;
                    if (h) {
                        panel._selectedMethod = meth;
                        // Only update host/credentials for SSH methods (not virsh/console -- those use KVM creds internally)
                        if (meth === 'virsh_console') {
                            panel._virshInfo = {
                                kvmHost: h,
                                kvmUser: el.dataset.kvmUser || 'dn',
                                kvmPass: el.dataset.kvmPass || 'drive1234!',
                                kvmName: el.dataset.kvmName || h,
                                nccVms: el.dataset.nccVms ? el.dataset.nccVms.split(',').filter(Boolean) : []
                            };
                        } else if (meth === 'console') {
                            panel._virshInfo = null;
                        } else {
                            if (hostInput) hostInput.value = h;
                            if (userInput) userInput.value = 'dnroot';
                            if (passInput) passInput.value = 'dnroot';
                            panel._virshInfo = null;
                        }
                        methodsList.querySelectorAll('.ssh-probe-method').forEach(row => {
                            row.style.background = 'transparent';
                            row.style.borderColor = 'transparent';
                            const dot = row.querySelector('span:first-child');
                            if (dot) dot.style.boxShadow = '';
                        });
                        el.style.background = isDarkMode ? 'rgba(39,174,96,0.12)' : 'rgba(39,174,96,0.08)';
                        el.style.borderColor = '#27ae60';
                        const dot = el.querySelector('span:first-child');
                        if (dot) dot.style.boxShadow = '0 0 4px #27ae60';
                    }
                });
            });
        } catch (e) {
            if (probeStatus) probeStatus.textContent = '';
            if (methodsList) methodsList.innerHTML = `<span style="color:#e74c3c;">[ERROR] Probe failed: ${e.message}</span>`;
        }
    }

    function _renderClusterInfo(cluster, textColor, labelColor, inputBg, inputBorder, connectBtnHtmlFn, methodsListEl) {
        if (!cluster || !cluster.is_cluster) return '';
        const activeVm = (cluster.active_ncc_vm || '').toLowerCase();
        let html = `<div style="margin-top:8px;padding:6px;background:${inputBg};border:1px solid ${inputBorder};border-radius:6px;">`;
        html += `<div style="font-weight:600;color:${textColor};margin-bottom:4px;font-size:10px;">Cluster Components</div>`;
        html += `<div style="font-size:9px;color:${labelColor};margin-bottom:4px;">Legacy clusters: NCM port 49 = NCC-0, port 50 = NCC-1. GI autodetects ncc-id via NCM LLDP.</div>`;
        if (cluster.ncc_vms && cluster.ncc_vms.length > 0) {
            cluster.ncc_vms.forEach((vm, i) => {
                const nccHost = (cluster.ncc_hosts && cluster.ncc_hosts[i]) || '';
                const nccLabel = `NCC-${i}`;
                const isActive = activeVm && vm.toLowerCase() === activeVm;
                const isStandby = activeVm && !isActive;
                const dotColor = isActive ? '#27ae60' : (isStandby ? '#95a5a6' : '#3498db');
                const roleTag = isActive
                    ? '<span style="font-size:9px;font-weight:600;color:#27ae60;margin-left:4px;">ACTIVE</span>'
                    : (isStandby ? '<span style="font-size:9px;color:#95a5a6;margin-left:4px;">standby</span>' : '');
                const nccTag = (i === 0) ? ' (NCM port 49)' : ' (NCM port 50)';
                const activeBorder = isActive ? 'border:1px solid rgba(39,174,96,0.4);background:rgba(39,174,96,0.08);' : 'border:1px solid transparent;';
                html += `<div class="ssh-probe-method" data-method="ssh_ncc" data-host="${nccHost}" data-reachable="${nccHost ? 'true' : 'false'}" data-is-active-ncc="${isActive}"
                    style="display:flex;align-items:center;gap:6px;padding:3px 6px;margin:2px 0;border-radius:4px;cursor:${nccHost ? 'pointer' : 'default'};${activeBorder}"
                    title="${isActive ? 'Active NCC - click to connect' : (isStandby ? 'Standby NCC' : 'Click to SSH to this NCC')}">
                    <span style="width:6px;height:6px;border-radius:50%;background:${dotColor};flex-shrink:0;${isActive ? 'box-shadow:0 0 4px #27ae60;' : ''}"></span>
                    <svg width="12" height="12" style="pointer-events:none;"><use href="#ico-terminal"/></svg>
                    <span style="color:${textColor};">${nccLabel}: ${vm}<span style="font-size:9px;color:${labelColor};">${nccTag}</span>${roleTag}</span>
                    ${nccHost ? `<span style="color:${labelColor};margin-left:auto;">${nccHost}</span>${connectBtnHtmlFn ? connectBtnHtmlFn('ssh_ncc') : ''}` : ''}
                </div>`;
            });
        }
        if (cluster.ncp_console) {
            const ncp = cluster.ncp_console;
            html += `<div style="color:${labelColor};font-size:10px;margin-top:6px;margin-bottom:2px;">NCP Console (Serial)</div>`;
            html += `<div style="display:flex;align-items:center;gap:6px;padding:3px 6px;">
                <span style="width:6px;height:6px;border-radius:50%;background:#e67e22;flex-shrink:0;"></span>
                <svg width="12" height="12" style="pointer-events:none;"><use href="#ico-console"/></svg>
                <span style="color:${textColor};">${ncp.console_server || '?'} port ${ncp.port || '?'}</span>
                <span style="color:${labelColor};margin-left:auto;">${ncp.source || ''}</span>
            </div>`;
        }
        html += '</div>';
        return html;
    }

    if (hostInput) {
        hostInput.addEventListener('input', () => {
            if (_probeDebounce) clearTimeout(_probeDebounce);
            _probeDebounce = setTimeout(() => {
                if (hostInput.value.trim()) probeAndShowMethods();
                else {
                    _lastProbeResult = null;
                    methodsList.innerHTML = '';
                    if (probeStatus) probeStatus.textContent = 'Enter host to probe';
                }
            }, 500);
        });
    }

    if (currentHost) {
        probeAndShowMethods();
    } else {
        if (probeStatus) probeStatus.textContent = 'Enter host to probe';
    }

    const discoverConsoleBtn = panel.querySelector('#ssh-discover-console');
    const consoleInfoSection = panel.querySelector('#ssh-console-info');
    const consoleDetails = panel.querySelector('#ssh-console-details');
    const pduPowerBtn = panel.querySelector('#ssh-pdu-power-cycle');

    if (discoverConsoleBtn) {
        discoverConsoleBtn.addEventListener('click', async () => {
            const serial = device.deviceSerial || device.serial || '';
            discoverConsoleBtn.textContent = 'Discovering...';
            discoverConsoleBtn.disabled = true;
            try {
                const r = await (typeof ScalerAPI !== 'undefined' && ScalerAPI.discoverConsole
                    ? ScalerAPI.discoverConsole(deviceId, serial, hostInput?.value?.trim())
                    : Promise.reject(new Error('ScalerAPI.discoverConsole not available')));
                _lastDiscovery = r;
                if (editor.showToast) editor.showToast(`[OK] Console: ${r.console_server || 'N/A'} port ${r.port || '?'} (${r.source || 'unknown'})`, 'success');

                let html = '';
                if (r.console_server) {
                    const targetLabel = r.is_cluster ? ' (NCP -- data plane)' : '';
                    html += `<div style="margin-bottom:4px;"><strong style="color:${isDarkMode ? '#2ecc71' : '#27ae60'}">Console${targetLabel}:</strong> ${r.console_server} port ${r.port || '?'}</div>`;
                    html += `<div style="color:${isDarkMode ? '#888' : '#999'};">Source: ${r.source || 'unknown'}${r.serial_no ? ' | SN: ' + r.serial_no : ''}</div>`;
                }
                if (r.cluster_note) {
                    html += `<div style="margin-top:6px;padding:4px 6px;background:${isDarkMode ? 'rgba(230,126,34,0.15)' : 'rgba(230,126,34,0.1)'};border-left:3px solid #e67e22;border-radius:3px;color:${isDarkMode ? '#f0c674' : '#d35400'};font-size:10px;">${r.cluster_note}</div>`;
                }
                if (r.pdu_entries && r.pdu_entries.length > 0) {
                    html += '<div style="margin-top:4px;"><strong>PDU:</strong>';
                    r.pdu_entries.forEach((e, i) => {
                        html += ` ${e.pdu} outlet ${e.outlet}${i < r.pdu_entries.length - 1 ? ',' : ''}`;
                    });
                    html += '</div>';
                    if (pduPowerBtn) pduPowerBtn.style.display = '';
                }
                if (!r.console_server && (!r.pdu_entries || r.pdu_entries.length === 0)) {
                    html = `<div style="color:${isDarkMode ? '#e67e22' : '#d35400'}">No console mapping found. Serial: ${serial || 'unknown'}</div>`;
                }
                if (consoleDetails) consoleDetails.innerHTML = html;
                if (consoleInfoSection) consoleInfoSection.style.display = '';

                if (r.console_server && methodsList) {
                    const badge = r.source === 'zohar_db' ? 'Lab DB' : (r.source === 'device42' ? 'Device42' : 'Discovered');
                    const consoleLabel = r.is_cluster ? `Console -> NCP [${badge}]` : `Console (Serial) [${badge}]`;
                    const consoleTitle = r.is_cluster
                        ? 'This console reaches the NCP (data plane), not the NCC. Use Virsh Console for NCC access.'
                        : 'Click Connect to open terminal to console server';
                    const consoleBorder = r.is_cluster ? 'border:1px solid #e67e22;background:rgba(230,126,34,0.12);' : 'border:1px solid #27ae60;background:rgba(39,174,96,0.12);';
                    const consoleDot = r.is_cluster ? '#e67e22' : '#27ae60';
                    const consoleRow = `<div class="ssh-probe-method ssh-console-discovered" data-method="console" data-host="${r.console_server}" data-reachable="true" data-console-port="${r.port || ''}"
                        style="display:flex;align-items:center;gap:6px;padding:4px 6px;margin:2px 0;border-radius:5px;${consoleBorder}"
                        title="${consoleTitle}">
                        <span style="width:6px;height:6px;border-radius:50%;background:${consoleDot};flex-shrink:0;"></span>
                        <span style="display:flex;align-items:center;color:${textColor};">${_methodIcon('console')}</span>
                        <span style="color:${textColor};font-weight:600;">${consoleLabel}</span>
                        <span style="color:${labelColor};margin-left:auto;">${r.console_server} port ${r.port || '?'}</span>
                        ${connectBtnHtml('console')}
                    </div>`;
                    const existing = methodsList.querySelector('.ssh-console-discovered');
                    if (existing) existing.remove();
                    methodsList.insertAdjacentHTML('beforeend', consoleRow);

                    methodsList.querySelector('.ssh-console-discovered .ssh-connect-btn')?.addEventListener('click', (e) => {
                        e.stopPropagation();
                        doConnect('console', r.console_server, r.port, userInput?.value?.trim() || 'dn', passInput?.value || '', null, null, r.console_server, r.port);
                    });
                }
            } catch (e) {
                if (consoleInfoSection) consoleInfoSection.style.display = '';
                if (typeof ScalerAPI !== 'undefined' && ScalerAPI.consoleScan) {
                    if (consoleDetails) consoleDetails.innerHTML = `<div style="color:${isDarkMode ? '#e67e22' : '#d35400'}">DB lookup failed. Scanning ports...</div>`;
                    discoverConsoleBtn.textContent = 'Scanning...';
                    try {
                        const scan = await ScalerAPI.consoleScan(deviceId, serial);
                        if (scan.found) {
                            const scanHost = scan.console_host || scan.console_server || '';
                            _lastDiscovery = { console_server: scanHost, port: scan.port, source: 'port_scan' };
                            if (editor.showToast) editor.showToast(`[OK] Found ${deviceId} on ${scanHost} port ${scan.port}`, 'success');
                            let html = `<div style="margin-bottom:4px;"><strong style="color:${isDarkMode ? '#2ecc71' : '#27ae60'}">Console:</strong> ${scanHost} port ${scan.port}</div>`;
                            html += `<div style="color:${isDarkMode ? '#888' : '#999'};">Source: port scan (${scan.scanned} ports)</div>`;
                            if (consoleDetails) consoleDetails.innerHTML = html;
                            if (methodsList) {
                                const consoleRow = `<div class="ssh-probe-method ssh-console-discovered" data-method="console" data-host="${scan.console_host}" data-reachable="true" data-console-port="${scan.port}"
                                    style="display:flex;align-items:center;gap:6px;padding:4px 6px;margin:2px 0;border-radius:5px;background:rgba(39,174,96,0.12);border:1px solid #27ae60;"
                                    title="Click Connect to open terminal">
                                    <span style="width:6px;height:6px;border-radius:50%;background:#27ae60;"></span>
                                    <span>${_methodIcon('console')}</span>
                                    <span style="color:${textColor};font-weight:600;">Console (Serial) [Port Scan]</span>
                                    <span style="color:${labelColor};margin-left:auto;">${scan.console_host} port ${scan.port}</span>
                                    ${connectBtnHtml('console')}
                                </div>`;
                                const existing = methodsList.querySelector('.ssh-console-discovered');
                                if (existing) existing.remove();
                                methodsList.insertAdjacentHTML('beforeend', consoleRow);
                                methodsList.querySelector('.ssh-console-discovered .ssh-connect-btn')?.addEventListener('click', (e) => {
                                    e.stopPropagation();
                                    doConnect('console', scan.console_host, scan.port, userInput?.value?.trim() || 'dn', passInput?.value || '', null, null, scan.console_host, scan.port);
                                });
                            }
                        } else {
                            const portSummary = (scan.all_results || [])
                                .filter(rr => rr.hostname_guess && rr.hostname_guess !== '_login_prompt_')
                                .map(rr => `port ${rr.port}: ${rr.hostname_guess}`)
                                .join(', ');
                            let html = `<div style="color:${isDarkMode ? '#e67e22' : '#d35400'}">Port scan: ${deviceId} not found (${scan.scanned} ports)</div>`;
                            if (portSummary) html += `<div style="color:${isDarkMode ? '#888' : '#999'};font-size:10px;">Devices: ${portSummary}</div>`;
                            if (scan.error) html += `<div style="color:#e74c3c;">${scan.error}</div>`;
                            if (consoleDetails) consoleDetails.innerHTML = html;
                            if (editor.showToast) editor.showToast(`[WARN] Port scan: ${deviceId} not found`, 'warning');
                        }
                    } catch (scanErr) {
                        if (consoleDetails) consoleDetails.innerHTML = `<span style="color:#e74c3c;">Discovery + scan failed: ${scanErr.message}</span>`;
                        if (editor.showToast) editor.showToast(`[ERROR] Console scan failed: ${scanErr.message}`, 'error');
                    }
                } else {
                    if (editor.showToast) editor.showToast(`[ERROR] Console discovery failed: ${e.message}`, 'error');
                    if (consoleDetails) consoleDetails.innerHTML = `<span style="color:#e74c3c;">${e.message}</span>`;
                }
            } finally {
                discoverConsoleBtn.textContent = 'Discover Console';
                discoverConsoleBtn.disabled = false;
            }
        });
    }

    if (pduPowerBtn) {
        pduPowerBtn.addEventListener('click', async () => {
            if (!_lastDiscovery?.pdu_entries?.length) {
                if (editor.showToast) editor.showToast('[WARN] No PDU mapping. Run Discover Console first.', 'warning');
                return;
            }
            const entry = _lastDiscovery.pdu_entries[0];
            const confirmed = confirm(
                `Power cycle ${entry.pdu} outlet ${entry.outlet}?\n\nOFF 5s then ON.\nDevice: ${device.label || deviceId}`
            );
            if (!confirmed) return;
            pduPowerBtn.textContent = 'Cycling...';
            pduPowerBtn.disabled = true;
            try {
                if (typeof ScalerAPI === 'undefined' || !ScalerAPI.pduPower) {
                    throw new Error('ScalerAPI.pduPower not available');
                }
                const r = await ScalerAPI.pduPower({
                    serial_number: _lastDiscovery.serial_no || device.deviceSerial || '',
                    device_id: deviceId,
                    action: 'reboot',
                    pdu_host: entry.pdu,
                    outlet: entry.outlet
                });
                if (editor.showToast) editor.showToast(`[OK] Power cycle: ${r.status_output || 'OK'}`, 'success');
                if (consoleDetails) consoleDetails.innerHTML += `<div style="margin-top:6px;color:#27ae60;">Power cycle done</div>`;
            } catch (e) {
                if (editor.showToast) editor.showToast(`[ERROR] PDU failed: ${e.message}`, 'error');
            } finally {
                pduPowerBtn.textContent = 'Power Cycle (PDU)';
                pduPowerBtn.disabled = false;
            }
        });
    }

    if (togglePassBtn && passInput && eyeIcon) {
        togglePassBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (passInput.type === 'password') {
                passInput.type = 'text';
                eyeIcon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>';
            } else {
                passInput.type = 'password';
                eyeIcon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>';
            }
        });
    }

    const saveAddress = async () => {
        const host = hostInput.value.trim();
        const user = userInput.value.trim() || 'dnroot';
        const password = passInput.value;
        const oldHost = device.sshConfig?.host;
        const clearHostKeyCheckbox = panel.querySelector('#ssh-clear-hostkey');
        const clearHostKey = clearHostKeyCheckbox ? clearHostKeyCheckbox.checked : false;

        if (clearHostKey && host) {
            let _clearOk = false;
            try {
                if (editor.showToast) editor.showToast(`Clearing host key for ${host} on Mac...`, 'info', 3000);
                const resp = await fetch('/api/ssh/clear-hostkey', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ host })
                });
                const result = await resp.json();
                if (result.mac_cleared) {
                    _clearOk = true;
                    if (editor.showToast) editor.showToast(`[OK] Host key cleared on Mac (${result.mac_ip}) -- connecting...`, 'success', 3000);
                } else if (result.mac_ip && !result.mac_cleared) {
                    _showMacIpPrompt(panel, editor, host, result.mac_ip, result.message, user, password);
                    return;
                } else if (!result.mac_ip) {
                    _showMacIpPrompt(panel, editor, host, '', 'Mac IP not configured', user, password);
                    return;
                } else {
                    if (editor.showToast) editor.showToast(`[WARN] ${result.error || result.message || 'Failed to clear host key'}`, 'warning');
                }
            } catch (err) {
                if (editor.showToast) editor.showToast(`[ERROR] Failed to clear host key: ${err.message}`, 'error');
            }
            if (_clearOk && host) {
                // Auto-connect after successful clear
                setTimeout(() => {
                    if (editor._openSshUrl) {
                        if (window.ObjectDetection) window.ObjectDetection._pendingPassword = password;
                        editor._openSshUrl(`ssh://${user}@${host}`);
                    }
                }, 500);
            }
        }

        device.sshConfig = {
            ...(device.sshConfig || {}),
            host: host,
            user: user,
            password: password,
            _userSavedHost: host || null,
            _userSavedUser: user || null,
            _userSavedPass: password || null,
            _lastWorkingMethod: panel._selectedMethod || device.sshConfig?._lastWorkingMethod || '',
            _virshInfo: panel._virshInfo || device.sshConfig?._virshInfo || null
        };
        device.deviceAddress = host ? `${user}@${host}` : '';

        if (typeof ScalerAPI !== 'undefined' && ScalerAPI.evictSSHPoolConnection) {
            if (oldHost) ScalerAPI.evictSSHPoolConnection(oldHost, deviceId).catch(() => {});
            if (host) ScalerAPI.evictSSHPoolConnection(host, deviceId).catch(() => {});
        }

        if (editor.saveState) editor.saveState();
        if (editor.scheduleAutoSave) editor.scheduleAutoSave();

        if (editor.debugger) {
            if (host) editor.debugger.logSuccess(`[OK] SSH configured for ${device.label}: ${user}@${host}`);
            else editor.debugger.logInfo(`[INFO] SSH config cleared for ${device.label}`);
        }

        if (editor.showToast) editor.showToast(host ? `[OK] SSH set: ${user}@${host}` : '[OK] SSH config cleared', 'success');
        closeDialog();
        editor.draw();
    };

    const saveBtn = panel.querySelector('#ssh-dialog-save');
    const cancelBtn = panel.querySelector('#ssh-dialog-cancel');
    const helpBtn = panel.querySelector('#ssh-help-btn');

    if (saveBtn) saveBtn.addEventListener('click', saveAddress);
    if (cancelBtn) cancelBtn.addEventListener('click', closeDialog);

    if (helpBtn) {
        helpBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const host = hostInput.value.trim();
            const user = userInput.value.trim() || 'dnroot';
            if (!host) {
                if (editor.showToast) editor.showToast('[WARN] Enter host/serial first', 'error');
                return;
            }
            const sshCommand = `ssh ${user}@${host}`;
            (typeof window.safeClipboardWrite === 'function' ? window.safeClipboardWrite(sshCommand) : Promise.reject(new Error('Clipboard unavailable')))
                .then(() => {
                    helpBtn.textContent = '[OK]';
                    helpBtn.style.background = 'rgba(39, 174, 96, 0.2)';
                    helpBtn.style.color = '#27ae60';
                    helpBtn.style.borderColor = 'rgba(39, 174, 96, 0.5)';
                    setTimeout(() => {
                        helpBtn.textContent = '?';
                        helpBtn.style.background = inputBg;
                        helpBtn.style.color = labelColor;
                        helpBtn.style.borderColor = inputBorder;
                    }, 2000);
                    if (editor.showToast) editor.showToast(`[OK] Copied: ${sshCommand}`, 'success');
                })
                .catch(() => {
                    if (editor.showToast) editor.showToast('[ERROR] Failed to copy to clipboard', 'error');
                });
        });
    }

    handleEscape = (e) => {
        if (e.key === 'Enter' && (document.activeElement === hostInput || document.activeElement === userInput || document.activeElement === passInput)) {
            e.preventDefault();
            saveAddress();
        } else if (e.key === 'Escape') {
            closeDialog();
        }
    };
    document.addEventListener('keydown', handleEscape);

    handleClickOutside = (e) => {
        if (!panel.contains(e.target)) {
            const newHost = hostInput.value.trim();
            const newUser = userInput.value.trim() || 'dnroot';
            const newPass = passInput.value;
            const changed = newHost !== currentHost || newUser !== currentUser || newPass !== currentPass;
            if (changed) saveAddress();
            else closeDialog();
        }
    };
    setTimeout(() => document.addEventListener('click', handleClickOutside), 100);
}

window.showSSHAddressDialog = showSSHAddressDialog;
console.log('[topology-ssh-dialog.js] SSH Address Dialog module loaded');
