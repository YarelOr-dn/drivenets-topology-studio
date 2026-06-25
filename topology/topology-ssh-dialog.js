// ============================================================================
// TOPOLOGY SSH ADDRESS DIALOG MODULE
// ============================================================================
// Handles the SSH configuration dialog for devices.
// Redesigned: connection-focused, methods always visible, per-method Connect.
//
// Usage:
//   showSSHAddressDialog(editor, device);
// ============================================================================

function _sshDialogAuthFetch(url, options) {
    if (window.TopologyAuth && typeof window.TopologyAuth.authFetch === 'function') {
        return window.TopologyAuth.authFetch(url, options);
    }
    return fetch(url, options);
}

function _sshDialogIsIp(value) {
    const v = (value || '').toString().trim();
    return /^(?:\d{1,3}\.){3}\d{1,3}$/.test(v);
}

function _sshDialogIsGiMode(device) {
    const values = [
        device?._deviceMode,
        device?._modeRawState,
        device?._monitorContext?.device_state,
        device?._identity?.device_state,
        device?.sshConfig?._deviceState,
    ].map(v => String(v || '').trim().toUpperCase()).filter(Boolean);
    return values.some(v => v === 'GI' || v === 'BASEOS_SHELL' || v.includes('GI_MODE'));
}

function _sshDialogLooksLikeSerial(value) {
    const v = String(value || '').trim();
    return !!v && !_sshDialogIsIp(v) && /^[A-Z0-9]{8,}$/i.test(v);
}

function _showMacIpPrompt(panel, editor, targetHost, currentMacIp, errorMsg, sshUser, sshPass, hostsForCopy, targetDevice) {
    // Drop any existing Mac-IP overlay first. If the user saves twice (or
    // the dialog re-opens without a cleanup), a second overlay would stack
    // on top of the first and the panel would grow into what looks like
    // a grey modal. This guarantees only ONE prompt at a time.
    const _existing = panel.querySelectorAll('._mac-ip-overlay');
    _existing.forEach((n) => n.remove());

    const isDark = document.body.classList.contains('dark-mode');
    const bg = isDark ? '#1a1a2e' : '#fff';
    const border = isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)';
    const text = isDark ? '#c8d0da' : '#333';
    const overlay = document.createElement('div');
    overlay.className = '_mac-ip-overlay';
    // IMPORTANT: the overlay uses `position: absolute` and anchors to the
    // parent panel. The panel is already `position: fixed`, which IS a
    // positioning context -- so we do NOT rewrite `panel.style.position`.
    // An earlier version did `panel.style.position = 'relative'`, which
    // overrode `position: fixed` while keeping the inline `left`/`top`/
    // `transform: translateX(-50%)`. Those declarations are meaningful
    // only for `fixed`/`absolute`; under `relative` they turn into flow
    // offsets and the dialog jumped to a random spot on screen (often
    // off-canvas) -- what the operator saw as a "grey screen".
    // Using max-height + overflow so the dialog never grows past the
    // panel (it's an inline overlay, not a fullscreen modal).
    overlay.style.cssText = `position:absolute;left:0;right:0;bottom:0;z-index:10;border-radius:0 0 12px 12px;padding:10px 14px;background:${isDark ? 'rgba(15,18,28,0.97)' : 'rgba(255,255,255,0.97)'};border-top:1px solid ${isDark ? 'rgba(230,126,34,0.3)' : 'rgba(230,126,34,0.2)'};max-height:260px;overflow:auto;`;
    overlay.innerHTML = `
        <div>
            <div style="color:#e67e22;font-weight:600;font-size:12px;margin-bottom:6px;display:flex;align-items:center;justify-content:space-between;">
                <span>Mac Unreachable -- stale host key not cleared</span>
                <button id="_mac-close-btn" title="Dismiss" style="background:transparent;border:none;color:${text};cursor:pointer;font-size:14px;line-height:1;padding:0 4px;">&times;</button>
            </div>
            <div style="color:${text};font-size:11px;margin-bottom:8px;">${errorMsg}. Either update the Mac VPN IP below, or paste the copy-command in your Mac Terminal.</div>
            <div style="display:flex;gap:6px;align-items:center;margin-bottom:10px;">
                <input type="text" id="_mac-ip-input" value="${currentMacIp}" placeholder="Mac VPN IP (e.g. 10.x.x.x)"
                    style="flex:1;padding:6px 8px;border-radius:4px;border:1px solid ${border};background:${isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.03)'};color:${text};font-size:11px;outline:none;font-family:'Space Grotesk',monospace;"/>
            </div>
            <div style="display:flex;gap:6px;justify-content:flex-end;flex-wrap:wrap;">
                <button id="_mac-copy-btn" title="Copy ssh-keygen -R command for pasting in Mac Terminal"
                    style="padding:5px 12px;border-radius:4px;border:1px solid ${border};background:transparent;color:${text};cursor:pointer;font-size:11px;">Copy command</button>
                <button id="_mac-skip-btn" style="padding:5px 12px;border-radius:4px;border:1px solid ${border};background:transparent;color:${text};cursor:pointer;font-size:11px;">Skip &amp; connect</button>
                <button id="_mac-retry-btn" style="padding:5px 12px;border-radius:4px;border:none;background:#e67e22;color:#fff;cursor:pointer;font-size:11px;font-weight:600;">Update &amp; Clear</button>
            </div>
            <div id="_mac-status" style="margin-top:8px;font-size:10px;color:${text};"></div>
        </div>`;
    panel.appendChild(overlay);

    const input = overlay.querySelector('#_mac-ip-input');
    const retryBtn = overlay.querySelector('#_mac-retry-btn');
    const skipBtn = overlay.querySelector('#_mac-skip-btn');
    const copyBtn = overlay.querySelector('#_mac-copy-btn');
    const closeBtn = overlay.querySelector('#_mac-close-btn');
    const status = overlay.querySelector('#_mac-status');

    // Every alias we should clear. Passed from saveAddress when available;
    // fall back to the user's current host so we never reach zero.
    const _hosts = (Array.isArray(hostsForCopy) && hostsForCopy.length) ? hostsForCopy : [targetHost];
    const _copyCmd = _hosts.map((h) => `ssh-keygen -R ${h}`).join(' && ');

    input.addEventListener('keydown', e => e.stopPropagation());
    if (closeBtn) closeBtn.addEventListener('click', () => overlay.remove());

    // "Skip & connect": user accepts the risk / is going to clear
    // manually. Dispatch the ssh:// now so they are not left clicking
    // Save twice.
    skipBtn.addEventListener('click', () => {
        overlay.remove();
        if (editor._openSshUrl) {
            if (window.ObjectDetection) {
                window.ObjectDetection._pendingPassword = sshPass;
                if (targetDevice) window.ObjectDetection._pendingDevice = targetDevice;
            }
            editor._openSshUrl(`ssh://${sshUser}@${targetHost}`);
        }
    });

    // "Copy command": writes `ssh-keygen -R a && ssh-keygen -R b && ...`
    // to the OS clipboard and surfaces a toast, so the operator can paste
    // in Mac Terminal in a single step.
    copyBtn.addEventListener('click', async () => {
        try {
            const writer = (editor && editor._safeClipboardWrite)
                ? editor._safeClipboardWrite.bind(editor)
                : (window.safeClipboardWrite || (async (t) => { throw new Error('no clipboard'); }));
            await writer(_copyCmd);
            status.style.color = '#27ae60';
            status.textContent = `[OK] Copied: ${_copyCmd.length > 60 ? _copyCmd.slice(0, 57) + '...' : _copyCmd}`;
            if (editor.showNotification) {
                editor.showNotification('[OK] ssh-keygen -R command copied -- paste in your Mac Terminal', 'success');
            }
        } catch (e) {
            status.style.color = '#e74c3c';
            status.textContent = `Clipboard failed: run manually: ${_copyCmd}`;
        }
    });

    retryBtn.addEventListener('click', async () => {
        const newIp = input.value.trim();
        if (!newIp) { status.textContent = 'Enter an IP address'; return; }
        retryBtn.disabled = true;
        retryBtn.textContent = 'Clearing...';
        status.textContent = '';
        try {
            await _sshDialogAuthFetch('/api/xray/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mac: { ip_vpn: newIp } })
            });
            const resp = await _sshDialogAuthFetch('/api/ssh/clear-hostkey', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                // batch form -- clears every alias the key may be stored
                // under. Older backends that only honour `host` still get
                // the first entry, which matches legacy behaviour.
                body: JSON.stringify({ hosts: _hosts, host: _hosts[0] })
            });
            const result = await resp.json();
            if (result.mac_cleared) {
                status.style.color = '#27ae60';
                status.textContent = `[OK] Cleared on Mac (${newIp}) -- connecting...`;
                setTimeout(() => {
                    overlay.remove();
                    if (editor._openSshUrl) {
                        if (window.ObjectDetection) {
                            window.ObjectDetection._pendingPassword = sshPass;
                            if (targetDevice) window.ObjectDetection._pendingDevice = targetDevice;
                        }
                        editor._openSshUrl(`ssh://${sshUser}@${targetHost}`);
                    }
                }, 800);
            } else {
                retryBtn.disabled = false;
                retryBtn.textContent = 'Update & Clear';
                status.style.color = '#e74c3c';
                status.textContent = `Failed: ${result.message || 'SSH to Mac failed'} -- use Copy command instead`;
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
    // SN host-lock: once a probe has confirmed an SN-based connection
    // path (ssh_sn / console / virsh_console with console_mappings
    // source) for this device, treat the saved SN/console identifier
    // as the source of truth. The mgmt IP cached in `sshConfig.host`
    // is allowed to be stale (ghost-IP class) -- if it ever drifts,
    // we don't want it to leak into the dialog where the operator
    // might inadvertently Save it back over the working SN. The user
    // can still type any value into the field and Save to override
    // the lock explicitly.
    const _isMgmtIpLike = (h) => typeof h === 'string' && /^\d+\.\d+\.\d+\.\d+$/.test(h.trim());
    const _snLockedHost = (sshConfig._snVerified && sshConfig._snVerifiedHost) || '';
    const _isCluster = !!(sshConfig._isCluster || sshConfig._virshInfo || device?._isCluster);
    const _activeNccHost = [
        sshConfig._activeNccHost,
        sshConfig._virshInfo?.activeNcc,
        device?._monitorContext?.active_ncc_host,
        device?._monitorContext?.active_ncc_vm,
        device?._identity?.active_ncc_host,
        device?._identity?.active_ncc_vm,
    ].map(v => String(v || '').trim())
     .find(v => v && !_isMgmtIpLike(v) && /(^|[-_.])ncc\d+(\.|$)/i.test(v));
    const _hostFromConfig = _snLockedHost && _isMgmtIpLike(sshConfig.host || '') && !_isMgmtIpLike(_snLockedHost)
        ? _snLockedHost
        : (sshConfig.host || '');
    const currentHost = (_isCluster && _activeNccHost ? _activeNccHost : '')
        || sshConfig._userSavedHost
        || _hostFromConfig
        || _snLockedHost
        || _addrHost;
    const currentUser = sshConfig._userSavedUser || sshConfig.user || 'dnroot';
    const currentPass = sshConfig._userSavedPass || sshConfig.password || '';
    const _identityGuard = () => window.TopologyDeviceIdentity || null;
    const _newIdentityToken = (host, scope = 'default') => {
        const guard = _identityGuard();
        const apiDeviceId = (typeof _currentApiDeviceId === 'function')
            ? _currentApiDeviceId()
            : (deviceId || device.label || '');
        const token = guard?.makeRequestToken
            ? guard.makeRequestToken(device, { host, deviceId: apiDeviceId })
            : { id: `${Date.now()}:${Math.random()}`, host, signature: `${host}|${apiDeviceId}` };
        token.scope = scope || 'default';
        device._identityRequestTokens = device._identityRequestTokens || {};
        device._identityRequestTokens[token.scope] = token.id;
        if (token.scope === 'default') {
            device._identityRequestToken = token.id;
        }
        return token;
    };
    const _isIdentityRequestCurrent = (token, host) => {
        const guard = _identityGuard();
        const scope = token?.scope || 'default';
        if (scope !== 'default') {
            const currentInputHost = (host || '').trim();
            const requestedHost = (token?.host || '').trim();
            if (!token || !device || !device._identityRequestTokens || device._identityRequestTokens[scope] !== token.id) {
                return false;
            }
            if (currentInputHost && requestedHost && currentInputHost.toLowerCase() !== requestedHost.toLowerCase()) {
                return false;
            }
            // Save is guarded by the typed SN/host plus the scoped token id.
            // Do not compare the full device metadata signature here: a
            // background probe may legitimately stamp registered identity
            // while Save is in flight, and the response payload is validated
            // separately before any onboarding data is applied.
            return true;
        }
        if (guard?.isRequestCurrent) {
            return guard.isRequestCurrent(device, token, { currentHost: host });
        }
        return !!token && device._identityRequestToken === token.id && (token.host || '') === (host || '');
    };
    const _validateIdentityResult = (result, token, ctx = null, host = '') => {
        const guard = _identityGuard();
        if (!guard?.validateResponseForDevice) return { ok: true };
        return guard.validateResponseForDevice(device, result || {}, token, {
            host: host || token?.host || '',
            ctx,
            deviceId: (typeof _currentApiDeviceId === 'function') ? _currentApiDeviceId() : (deviceId || device.label || '')
        });
    };
    const _invalidateForHostChange = (host, previousHost, reason) => {
        const guard = _identityGuard();
        if (!guard?.invalidateIdentityBoundMetadata) return false;
        const changed = guard.invalidateIdentityBoundMetadata(device, host, {
            previousHost,
            reason
        });
        if (changed) {
            try {
                window.dispatchEvent(new CustomEvent('device:context-updated', {
                    detail: { deviceId: deviceId || device.label || '', device, source: 'ssh-dialog-identity-invalidated' },
                }));
            } catch (_) {}
        }
        return changed;
    };
    const _clearUnreliableOnboardingMetadata = (backendMetadata, host, registeredId) => {
        const reason = backendMetadata?.reason || 'Backend did not return identity-verified metadata.';
        let changed = _invalidateForHostChange(host || '', device.sshConfig?.host || '', 'onboarding_metadata_unreliable');
        if (device._stackData || device._lldpData || device._gitCommit || device._monitorContext || device._monitorConfigFacts) {
            changed = true;
        }
        delete device._stackData;
        delete device._lldpData;
        delete device._gitCommit;
        delete device._gitCommitFetchedAt;
        delete device._monitorContext;
        delete device._monitorConfigFacts;
        device._metadataReadiness = device._metadataReadiness || {};
        ['lldp', 'stack', 'git'].forEach((kind) => {
            device._metadataReadiness[kind] = {
                status: backendMetadata?.status || 'unknown',
                source: backendMetadata?.source || 'backend-onboarding',
                reason,
                host: host || '',
                deviceId: registeredId || deviceId || '',
                updatedAt: Date.now(),
            };
        });
        device._staleIdentityMetadataCleared = {
            at: Date.now(),
            reason,
            status: backendMetadata?.status || 'unknown',
            source: 'onboarding_metadata_unreliable',
        };
        return changed;
    };

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

    // Initial best-guess position. We use conservative estimates for width
    // (420 == max-width) and height (clamped to viewport minus 24px margin)
    // so the dialog never spawns outside the viewport even before the
    // post-render correction below has a chance to run. The real width
    // /height are measured after insertion and clamped properly; this
    // pre-clamp just keeps the initial fade-in from flashing off-screen.
    const _viewportPad = 12;
    const _estWidth = 420;
    const _estHalfW = _estWidth / 2;
    const _estHeight = Math.min(640, window.innerHeight - _viewportPad * 2);

    let _initialLeft = deviceScreenX;
    _initialLeft = Math.max(_estHalfW + _viewportPad,
        Math.min(_initialLeft, window.innerWidth - _estHalfW - _viewportPad));

    let _initialTop = deviceScreenY + deviceRadius + 20;
    // Prefer below the device; if it would clip the bottom edge, try
    // above; if even that clips the top, stick to the top margin and
    // let internal overflow handle the rest.
    if (_initialTop + _estHeight > window.innerHeight - _viewportPad) {
        const _aboveTop = deviceScreenY - deviceRadius - 20 - _estHeight;
        _initialTop = _aboveTop >= _viewportPad
            ? _aboveTop
            : _viewportPad;
    }
    // Final hard clamp so a device panned above/below the viewport can
    // never push the dialog off-screen during the initial paint.
    _initialTop = Math.max(_viewportPad,
        Math.min(_initialTop, window.innerHeight - _estHeight - _viewportPad));

    panel.style.cssText = `
        position: fixed;
        left: ${_initialLeft}px;
        top: ${_initialTop}px;
        transform: translateX(-50%);
        z-index: 100000;
        background: ${glassBg};
        border: 1px solid ${glassBorder};
        border-radius: 14px;
        padding: 14px 18px;
        min-width: 360px;
        max-width: 420px;
        max-height: calc(100vh - 24px);
        overflow-y: auto;
        overscroll-behavior: contain;
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
            #ssh-address-dialog::-webkit-scrollbar {
                width: 6px;
            }
            #ssh-address-dialog::-webkit-scrollbar-track {
                background: transparent;
            }
            #ssh-address-dialog::-webkit-scrollbar-thumb {
                background: rgba(255,255,255,0.15);
                border-radius: 3px;
            }
            #ssh-address-dialog::-webkit-scrollbar-thumb:hover {
                background: rgba(255,255,255,0.25);
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
                <div style="font-size: 11px; color: ${labelColor};">${device.label || 'Device'}<span id="ssh-active-ncc-badge" style="display:none;margin-left:6px;font-size:9px;font-weight:600;color:#27ae60;background:rgba(39,174,96,0.12);padding:1px 6px;border-radius:3px;vertical-align:middle;"></span><button id="ssh-active-ncc-verify" type="button" title="Re-probe: ask the KVM host which NCC is actually active" style="display:none;margin-left:4px;padding:0 6px;height:16px;font-size:9px;font-weight:600;color:#3498db;background:transparent;border:1px solid rgba(52,152,219,0.5);border-radius:3px;cursor:pointer;vertical-align:middle;">Verify</button></div>
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
                    autocomplete="off"
                    data-lpignore="true" data-1p-ignore="true" data-form-type="other"
                    style="${inputStyle}"
                />
            </div>
            <div style="flex: 1; min-width: 0;">
                <label style="display: block; margin-bottom: 2px; color: ${labelColor}; font-size: 10px;">User</label>
                <input type="text" id="ssh-user-input" value="${currentUser}"
                    placeholder="dnroot"
                    autocomplete="off"
                    data-lpignore="true" data-1p-ignore="true" data-form-type="other"
                    style="${inputStyle}"
                />
            </div>
            <div style="flex: 1; min-width: 0;">
                <label style="display: block; margin-bottom: 2px; color: ${labelColor}; font-size: 10px;">Pass</label>
                <div style="position: relative;">
                    <input type="password" id="ssh-pass-input" value="${currentPass}"
                        placeholder="••••"
                        autocomplete="one-time-code"
                        data-lpignore="true" data-1p-ignore="true" data-form-type="other"
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

        <div style="display: flex; gap: 6px; margin: 6px 0 8px; align-items: center;">
            <label style="color: ${labelColor}; font-size: 10px; font-weight: 500; flex-shrink: 0;">Connect via</label>
            <div id="ssh-connect-via" role="tablist" style="display: inline-flex; flex: 1; border-radius: 6px; background: ${inputBg}; border: 1px solid ${inputBorder}; overflow: hidden;">
                <button type="button" data-method="auto" role="tab"
                    title="Platform default (Mac -> iTerm, others -> Web Terminal)"
                    style="flex: 1; padding: 5px 8px; font-size: 11px; border: none; background: transparent; color: ${textColor}; cursor: pointer; border-right: 1px solid ${inputBorder};">Auto</button>
                <button type="button" data-method="iterm" role="tab"
                    title="Open native terminal via ssh:// URL (iTerm / Terminal on macOS)"
                    style="flex: 1; padding: 5px 8px; font-size: 11px; border: none; background: transparent; color: ${textColor}; cursor: pointer; border-right: 1px solid ${inputBorder};">iTerm</button>
                <button type="button" data-method="webterm" role="tab"
                    title="In-browser terminal via server proxy (works anywhere)"
                    style="flex: 1; padding: 5px 8px; font-size: 11px; border: none; background: transparent; color: ${textColor}; cursor: pointer;">Web</button>
            </div>
            <span id="ssh-save-creds-hint" style="color: ${labelColor}; font-size: 10px; margin-left: auto; display: none;">[OK] saved</span>
        </div>

        <div id="ssh-connection-methods" style="margin: 8px 0; padding: 8px; background: ${inputBg}; border-radius: 6px; font-size: 11px; border: 1px solid ${inputBorder}; min-height: 48px;">
            <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px; color: ${labelColor};">
                <span>Connection Methods</span>
                <span id="ssh-probe-status" style="font-size: 10px; margin-left: auto;"></span>
            </div>
            <div id="ssh-methods-list"></div>
        </div>

        <div id="ssh-post-delete-banner" style="
            display: none;
            margin: 0 0 8px;
            padding: 8px 10px;
            border-radius: 8px;
            background: ${isDarkMode
                ? 'linear-gradient(135deg, rgba(230,126,34,0.14), rgba(192,57,43,0.12))'
                : 'linear-gradient(135deg, rgba(230,126,34,0.10), rgba(192,57,43,0.08))'};
            border: 1px solid ${isDarkMode ? 'rgba(230,126,34,0.45)' : 'rgba(230,126,34,0.35)'};
            font-size: 10px;
            color: ${textColor};
        ">
            <div style="display: flex; align-items: flex-start; gap: 8px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#e67e22" stroke-width="2"
                    style="flex-shrink: 0; margin-top: 1px;">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                    <path d="M10 11v6"/><path d="M14 11v6"/>
                </svg>
                <div style="flex: 1; min-width: 0; line-height: 1.35;">
                    <div style="font-weight: 600; color: #e67e22; margin-bottom: 2px;">
                        System was deleted on this device
                    </div>
                    <div id="ssh-post-delete-detail" style="color: ${labelColor}; font-size: 10px;">
                        The active NCC host key will have rotated. Clearing it
                        before reconnecting avoids the stale known_hosts warning.
                    </div>
                </div>
                <button id="ssh-post-delete-dismiss" type="button" title="Dismiss this hint"
                    style="background: transparent; border: none; color: ${labelColor};
                           cursor: pointer; font-size: 14px; line-height: 1; padding: 0 2px;
                           flex-shrink: 0;">&times;</button>
            </div>
        </div>

        <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap; margin-bottom: 8px; padding: 6px; border: 1px solid ${inputBorder}; border-radius: 8px; background: ${isDarkMode ? 'rgba(255,255,255,0.025)' : 'rgba(0,0,0,0.025)'};">
            <button id="ssh-discover-console" style="
                padding: 5px 10px; font-size: 11px; border-radius: 6px;
                border: 1px solid ${inputBorder}; background: ${inputBg};
                color: ${textColor}; cursor: pointer;
            ">Discover Console</button>
            <button id="ssh-pdu-power-cycle" title="Hard power reboot through the mapped lab PDU outlet. Use only for recovery." style="
                padding: 5px 10px; font-size: 11px; border-radius: 6px;
                border: 1px solid ${isDarkMode ? '#c0392b' : '#e74c3c'}; background: ${isDarkMode ? 'rgba(192,57,43,0.12)' : 'rgba(231,76,60,0.08)'};
                color: ${isDarkMode ? '#e74c3c' : '#c0392b'}; cursor: pointer; display: none;
            ">PDU Reboot</button>
            <div id="ssh-clear-hostkey-wrap" style="display: flex; align-items: center; gap: 6px; margin-left: auto;" title="When checked, runs ssh-keygen -R on every alias (hostname, IP, short form) on your Mac before each connect. Persists per device.">
                <input type="checkbox" id="ssh-clear-hostkey" ${sshConfig._autoClearHostKeys ? 'checked' : ''} style="width: 12px; height: 12px; accent-color: #e67e22; cursor: pointer;"/>
                <label for="ssh-clear-hostkey" style="color: ${labelColor}; font-size: 10px; cursor: pointer;">Auto-clear host key on connect</label>
            </div>
        </div>

        <div id="ssh-console-info" style="display: none; margin: 6px 0; padding: 8px 10px; background: ${inputBg}; border-radius: 8px; font-size: 10px; border: 1px solid ${inputBorder};">
            <div id="ssh-console-details" style="color: ${textColor};"></div>
        </div>

        <!-- Verification status row: shown only while a verify is in
             flight or after a verify completes. Stays hidden by default
             so the dialog visually identical to before for users who
             don't trigger any verify. -->
        <div id="ssh-verify-status" style="
            display: none; margin: 8px 0 4px 0; padding: 8px 10px;
            border-radius: 6px; font-size: 11px; line-height: 1.45;
            border: 1px solid ${inputBorder}; background: ${inputBg};
            color: ${textColor};
        "></div>

        <!-- Advanced disclosure: per-device monitor cadence + discovery
             depth. Closed by default so the dialog stays a one-click
             flow for the 95% case. -->
        <details id="ssh-advanced-section" style="
            margin: 8px 0 0 0; font-size: 10px; color: ${labelColor};
        ">
            <summary style="cursor: pointer; user-select: none; padding: 2px 0;">Advanced &#9662;</summary>
            <div style="
                display: grid; grid-template-columns: 1fr 1fr; gap: 8px;
                margin-top: 6px; padding: 8px; background: ${inputBg};
                border: 1px solid ${inputBorder}; border-radius: 6px;
            ">
                <div>
                    <label for="ssh-monitor-cadence" style="
                        display: block; color: ${labelColor};
                        font-size: 10px; margin-bottom: 3px;
                    ">Monitor cadence</label>
                    <select id="ssh-monitor-cadence" style="
                        width: 100%; padding: 4px 6px; border-radius: 4px;
                        border: 1px solid ${inputBorder};
                        background: ${inputBg}; color: ${textColor};
                        font-size: 10px;
                    ">
                        <option value="fast_initial">Fast initial then slow (default)</option>
                        <option value="default">Standard 5 min</option>
                        <option value="aggressive">Aggressive 60 s</option>
                    </select>
                </div>
                <div>
                    <label for="ssh-discovery-depth" style="
                        display: block; color: ${labelColor};
                        font-size: 10px; margin-bottom: 3px;
                    ">Discovery depth</label>
                    <select id="ssh-discovery-depth" style="
                        width: 100%; padding: 4px 6px; border-radius: 4px;
                        border: 1px solid ${inputBorder};
                        background: ${inputBg}; color: ${textColor};
                        font-size: 10px;
                    ">
                        <option value="minimal">Minimal (banner only)</option>
                        <option value="standard" selected>Standard (cluster identity)</option>
                        <option value="full">Full (LLDP + interfaces)</option>
                    </select>
                </div>
            </div>
        </details>

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

    panel.addEventListener('wheel', (e) => { e.stopPropagation(); }, { passive: true });
    panel.addEventListener('mousedown', (e) => { e.stopPropagation(); });
    panel.addEventListener('touchstart', (e) => { e.stopPropagation(); }, { passive: true });

    // Post-render clamp: measure the real panel and make sure it fits
    // entirely inside the viewport on both axes. Horizontal clamp
    // respects the `translateX(-50%)` anchor (so `left` is the panel's
    // visual centre). Vertical clamp prefers below the device, falls
    // back to above, then falls back to a fixed top margin; every
    // branch ends with a hard viewport clamp so a panned-off-screen
    // device can never spawn the dialog outside the viewport.
    const clampPanelToViewport = () => {
        const panelRect = panel.getBoundingClientRect();
        const padding = 15;
        const halfW = panelRect.width / 2;

        let currentLeft = parseFloat(panel.style.left) || deviceScreenX;
        currentLeft = Math.max(halfW + padding,
            Math.min(currentLeft, window.innerWidth - halfW - padding));
        panel.style.left = currentLeft + 'px';

        const maxPanelH = window.innerHeight - padding * 2;
        if (panelRect.height > maxPanelH) {
            panel.style.maxHeight = maxPanelH + 'px';
        }
        const effectiveH = Math.min(panelRect.height, maxPanelH);

        let currentTop = parseFloat(panel.style.top) || (deviceScreenY + deviceRadius + 20);
        if (currentTop + effectiveH > window.innerHeight - padding) {
            const aboveTop = deviceScreenY - deviceRadius - 20 - effectiveH;
            currentTop = aboveTop >= padding ? aboveTop : padding;
        }
        currentTop = Math.max(padding,
            Math.min(currentTop, window.innerHeight - effectiveH - padding));
        panel.style.top = currentTop + 'px';
    };

    requestAnimationFrame(clampPanelToViewport);
    // Re-clamp on window resize so the dialog never slips off-screen
    // when the user resizes the browser while the panel is open. The
    // listener is removed by `_cleanupListeners` below (which is the
    // single source of truth for panel teardown).
    const _onResize = () => clampPanelToViewport();
    window.addEventListener('resize', _onResize);

    const hostInput = panel.querySelector('#ssh-host-input');
    const userInput = panel.querySelector('#ssh-user-input');
    const passInput = panel.querySelector('#ssh-pass-input');
    const togglePassBtn = panel.querySelector('#ssh-toggle-pass');
    const eyeIcon = panel.querySelector('#ssh-eye-icon');
    const methodsSection = panel.querySelector('#ssh-connection-methods');
    const methodsList = panel.querySelector('#ssh-methods-list');
    const probeStatus = panel.querySelector('#ssh-probe-status');
    const deviceId = device._registeredDeviceId
        || device._registeredHostname
        || device.registeredDeviceId
        || device.hostname
        || device.label
        || device.deviceSerial
        || device.serial
        || '';
    const _generatedCanvasLabel = (value) => {
        const guard = window.TopologyDeviceIdentity || null;
        if (guard?.isGeneratedCanvasLabel) return guard.isGeneratedCanvasLabel(value);
        return /^(NCP|NCP-\d+|S|S\d+)$/i.test(String(value || '').trim());
    };
    const _currentApiDeviceId = () => {
        const registered = device._registeredDeviceId
            || device._registeredHostname
            || device.registeredDeviceId
            || device.registeredHostname
            || device.hostname
            || '';
        if (registered && !_generatedCanvasLabel(registered)) return registered;
        const serial = device._registeredSerialNumber
            || device.registeredSerialNumber
            || device.deviceSerial
            || device.serial
            || '';
        if (serial && !_generatedCanvasLabel(serial)) return serial;
        return registered || device.label || deviceId || '';
    };
    const _hasRegisteredProbeIdentity = () => !!(
        device._monitorRegistered
        && (device._registeredDeviceId || device._registeredHostname || device._registeredMgmtIp || device._monitoredKey)
    );
    const _isUnsafeGeneratedProbe = (apiId) => (
        _generatedCanvasLabel(apiId)
        && !_hasRegisteredProbeIdentity()
        && !(device._registeredSerialNumber || device.deviceSerial || device.serial)
    );
    const _markProbeUnknown = (reason, opts = {}) => {
        device._sshReachable = false;
        device._probeUnavailableAt = Date.now();
        device._probeUnavailableReason = reason;
        if (opts.retryMs) {
            device._probeRetryAfter = Date.now() + opts.retryMs;
        }
        device._metadataReadiness = device._metadataReadiness || {};
        ['lldp', 'stack', 'git'].forEach((kind) => {
            device._metadataReadiness[kind] = {
                status: 'unknown',
                source: 'ssh-probe',
                reason,
                host: (hostInput?.value || '').trim(),
                deviceId: _currentApiDeviceId(),
                updatedAt: Date.now(),
            };
        });
        try {
            window.dispatchEvent(new CustomEvent('device:context-updated', {
                detail: { deviceId: _currentApiDeviceId(), device, source: 'ssh-dialog-probe-unavailable' },
            }));
        } catch (_) {}
    };

    // "Connect via" picker (auto / iterm / webterm). The chosen value is
    // persisted as a sticky per-device preference on `device.sshConfig.preferredMethod`
    // so `_shouldUseWebTerminal` can honour it on every launch -- both from
    // the dialog Connect button and the canvas SSH icon. Choosing "auto"
    // clears the sticky pref and falls back to the platform default.
    const connectVia = panel.querySelector('#ssh-connect-via');
    if (connectVia) {
        const activeMethod = (sshConfig.preferredMethod === 'iterm' || sshConfig.preferredMethod === 'webterm')
            ? sshConfig.preferredMethod : 'auto';
        const highlightMethod = (m) => {
            connectVia.querySelectorAll('button[data-method]').forEach(btn => {
                const isActive = btn.dataset.method === m;
                btn.style.background = isActive
                    ? (isDarkMode ? 'rgba(100, 150, 255, 0.25)' : 'rgba(100, 150, 255, 0.22)')
                    : 'transparent';
                btn.style.fontWeight = isActive ? '600' : '400';
            });
        };
        highlightMethod(activeMethod);
        connectVia.addEventListener('click', (e) => {
            const btn = e.target.closest('button[data-method]');
            if (!btn) return;
            const m = btn.dataset.method;
            device.sshConfig = device.sshConfig || {};
            if (m === 'auto') {
                delete device.sshConfig.preferredMethod;
            } else {
                device.sshConfig.preferredMethod = m;
            }
            highlightMethod(m);
            if (editor.saveState) editor.saveState();
            if (editor.scheduleAutoSave) editor.scheduleAutoSave();
            console.log(`[SSH] preferredMethod for ${device.label || device.id || '?'} set to ${m}`);
            if (editor.showToast) editor.showToast(`[OK] Connect via: ${m === 'auto' ? 'platform default' : (m === 'iterm' ? 'iTerm' : 'Web Terminal')}`, 'success', 2500);
        });
    }

    let handleClickOutside, handleEscape;
    const _cleanupListeners = () => {
        if (handleEscape) { document.removeEventListener('keydown', handleEscape); handleEscape = null; }
        if (handleClickOutside) { document.removeEventListener('click', handleClickOutside); handleClickOutside = null; }
        window.removeEventListener('resize', _onResize);
    };
    panel._cleanup = _cleanupListeners;
    const closeDialog = () => {
        _cleanupListeners();
        panel.remove();
        setTimeout(() => {
            if (editor.showDeviceSelectionToolbar) editor.showDeviceSelectionToolbar(device);
        }, 50);
    };

    // ---------------- Post-delete host-key hint ----------------
    // When the upgrade flow runs `request system delete` it stamps
    // `sshConfig._postDeleteClearHostKey = true` on this device (see
    // `scaler-gui-progress.js::_stampPostDeleteSuggestion`). Render an
    // amber banner, auto-check "Auto-clear host key on connect", and
    // after the cluster probe completes pre-select the NCC row that
    // was active right before the delete -- that's the NCC whose host
    // key will have rotated on reboot.
    const _POST_DELETE_TTL_MS = 4 * 60 * 60 * 1000;
    panel._postDeleteDevice = device;
    const _postDeleteBanner = panel.querySelector('#ssh-post-delete-banner');
    const _postDeleteDetail = panel.querySelector('#ssh-post-delete-detail');
    const _postDeleteDismiss = panel.querySelector('#ssh-post-delete-dismiss');
    const _clearHostKeyInput = panel.querySelector('#ssh-clear-hostkey');
    const _clearHostKeyWrap = panel.querySelector('#ssh-clear-hostkey-wrap');

    const _fmtPostDeleteTime = (iso) => {
        if (!iso) return '';
        try {
            const d = new Date(iso);
            if (Number.isNaN(d.getTime())) return '';
            const mm = String(d.getMonth() + 1).padStart(2, '0');
            const dd = String(d.getDate()).padStart(2, '0');
            const hh = String(d.getHours()).padStart(2, '0');
            const mi = String(d.getMinutes()).padStart(2, '0');
            return `${mm}-${dd} ${hh}:${mi}`;
        } catch (_) { return ''; }
    };

    function _renderPostDeleteHint() {
        const cfg = device.sshConfig || {};
        const active = !!cfg._postDeleteClearHostKey;
        let stillFresh = active;
        if (active && cfg._postDeleteAtIso) {
            const ts = Date.parse(cfg._postDeleteAtIso);
            if (!Number.isNaN(ts) && (Date.now() - ts) > _POST_DELETE_TTL_MS) {
                stillFresh = false;
            }
        }
        if (!_postDeleteBanner) return;
        if (!stillFresh) {
            _postDeleteBanner.style.display = 'none';
            return;
        }
        const nccId = (cfg._postDeleteActiveNccId !== null && cfg._postDeleteActiveNccId !== undefined)
            ? Number(cfg._postDeleteActiveNccId) : null;
        const nccVm = cfg._postDeleteActiveNccVm || '';
        const whenTxt = _fmtPostDeleteTime(cfg._postDeleteAtIso) || 'recently';
        const nccLabel = (nccId !== null) ? `NCC-${nccId}` : 'the active NCC';
        const vmTag = nccVm ? ` (${nccVm})` : '';
        const ipTag = cfg._postDeleteMgmtIp ? ` on ${cfg._postDeleteMgmtIp}` : '';
        if (_postDeleteDetail) {
            _postDeleteDetail.innerHTML =
                `System delete ran at <b>${whenTxt}</b>${ipTag}. ` +
                `The active NCC was <b>${nccLabel}</b>${vmTag} -- its host key ` +
                `will have rotated. ` +
                `<b>Auto-clear host key on connect</b> has been enabled so the ` +
                `next connect runs <code>ssh-keygen -R</code> for every alias.`;
        }
        _postDeleteBanner.style.display = '';
        if (_clearHostKeyInput && !_clearHostKeyInput.checked) {
            _clearHostKeyInput.checked = true;
            panel._postDelHintAppliedAutoCheck = true;
        }
        if (_clearHostKeyWrap) {
            _clearHostKeyWrap.style.boxShadow = `0 0 0 1px ${isDarkMode ? 'rgba(230,126,34,0.45)' : 'rgba(230,126,34,0.55)'}`;
            _clearHostKeyWrap.style.borderRadius = '6px';
            _clearHostKeyWrap.style.padding = '2px 6px';
        }
        panel._postDelHintVisible = true;
    }

    function _dismissPostDeleteHint({ persistAutoCheck = false } = {}) {
        if (_postDeleteBanner) _postDeleteBanner.style.display = 'none';
        if (_clearHostKeyWrap) {
            _clearHostKeyWrap.style.boxShadow = '';
            _clearHostKeyWrap.style.padding = '';
        }
        panel._postDelHintVisible = false;
        if (!panel._postDelHintAppliedAutoCheck || persistAutoCheck) {
            // Operator explicitly opted into the auto-clear (or we're
            // persisting after a successful save). Leave the checkbox
            // alone; the save flow will handle `_autoClearHostKeys`.
        } else if (_clearHostKeyInput) {
            _clearHostKeyInput.checked = !!(device.sshConfig && device.sshConfig._autoClearHostKeys);
        }
        panel._postDelHintAppliedAutoCheck = false;
        if (device.sshConfig) {
            delete device.sshConfig._postDeleteClearHostKey;
            delete device.sshConfig._postDeleteActiveNccVm;
            delete device.sshConfig._postDeleteActiveNccId;
            delete device.sshConfig._postDeleteMgmtIp;
            delete device.sshConfig._postDeleteAtIso;
            delete device.sshConfig._postDeleteJobId;
        }
        try { editor.saveState?.(); } catch (_) {}
        try { editor.scheduleAutoSave?.(); } catch (_) {}
    }
    panel._dismissPostDeleteHint = _dismissPostDeleteHint;

    if (_postDeleteDismiss) {
        _postDeleteDismiss.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            _dismissPostDeleteHint();
        });
    }

    _renderPostDeleteHint();

    // Expose a re-render hook so the progress panel can refresh an
    // already-open SSH dialog the moment the backend signals the
    // post-delete state (see scaler-gui-progress.js).
    window.refreshSSHDialogPostDeleteHint = function (targetDevice) {
        const open = document.getElementById('ssh-address-dialog');
        if (!open || !open._postDeleteDevice) return;
        if (targetDevice && targetDevice !== open._postDeleteDevice) return;
        const fn = open.querySelector('#ssh-post-delete-banner');
        if (!fn) return;
        // Re-run the private renderer by simulating the in-scope call.
        try {
            if (typeof open._postDelReRender === 'function') {
                open._postDelReRender();
            }
        } catch (_) { /* swallow */ }
    };
    panel._postDelReRender = _renderPostDeleteHint;

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

        // Silent auto-persist: if the user typed a real credential and this is
        // an SSH method, push it to the per-user backend store BEFORE launching
        // so future discovery / config-push / LLDP calls see it. Without this,
        // clicking "Connect" on a discovered method would skip persistence
        // (which only happened via the "Save" button) and the backend would
        // fall back to dnroot/dnroot on the next operation -- the exact bug
        // the user reported.
        const credsDirty = user && password && (
            user !== (device.sshConfig?._userSavedUser || '') ||
            password !== (device.sshConfig?._userSavedPass || '')
        );
        const connectCredentialDeviceId = _currentApiDeviceId();
        if (_isSSHMethod && credsDirty && connectCredentialDeviceId && typeof ScalerAPI !== 'undefined' && ScalerAPI.saveDeviceCredentials) {
            ScalerAPI.saveDeviceCredentials(connectCredentialDeviceId, connectUser, connectPass).then(() => {
                device.sshConfig = device.sshConfig || {};
                device.sshConfig._userSavedUser = connectUser;
                device.sshConfig._userSavedPass = connectPass;
                console.log(`[SSH] creds auto-persisted on connect for ${connectCredentialDeviceId}`);
            }).catch((err) => {
                console.warn(`[SSH] creds auto-persist failed for ${connectCredentialDeviceId}:`, err?.message || err);
            });
        }

        if (method === 'virsh_console' && host && (kvmUser || user)) {
            const existingActiveNcc = device.sshConfig?._virshInfo?.activeNcc || '';
            const activeNcc = existingActiveNcc || (nccVms && nccVms[0]) || '';
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

        // Respect the "Connect via" segmented control for console/virsh rows.
        // Before 2026-04-24 `doConnect` always sent virsh_console + console
        // straight to `TerminalPanel.open` (in-browser). That meant the
        // operator could pick "iTerm" in the dialog, click Connect on Virsh
        // Console, and still end up in the web terminal -- user-reported
        // bug: "does not work when jumping between auto and iterm preferability".
        // Now: iTerm-pref opens an `ssh://` to the jump host (KVM for virsh,
        // console-server for serial) with the follow-up command staged for
        // clipboard so the operator can paste it once iTerm lands. Auto/
        // webterm preserve the original in-browser flow.
        const _preferredMethod = (device.sshConfig && device.sshConfig.preferredMethod) || 'auto';
        const _isGiMode = _sshDialogIsGiMode(device);
        const _wantsIterm = _preferredMethod === 'iterm'
            || (_preferredMethod === 'auto' && !_isGiMode);
        const _wantsWeb = _preferredMethod === 'web'
            || (_preferredMethod === 'auto' && _isGiMode);

        if (_isConsoleMethod) {
            if (method === 'virsh_console' && _wantsIterm && device.sshConfig._virshInfo && editor._openSshUrl) {
                // iTerm path for virsh: ssh to the KVM host, then the
                // operator pastes `sudo virsh console --force <active-ncc>`
                // (copied to clipboard below). The KVM password is staged
                // on ObjectDetection so the existing iTerm toast can show
                // it / copy it like a regular SSH launch.
                const vi = device.sshConfig._virshInfo;
                const _virshNcc = vi.activeNcc || (vi.nccVms && vi.nccVms[0]) || '';
                const _virshCmd = _virshNcc ? `sudo virsh console --force ${_virshNcc}` : 'sudo virsh list --all';
                if (window.ObjectDetection) {
                    window.ObjectDetection._pendingDevice = device;
                    window.ObjectDetection._pendingPassword = vi.kvmPass || connectPass;
                }
                try {
                    if (navigator?.clipboard?.writeText) {
                        navigator.clipboard.writeText(_virshCmd).catch(() => {});
                    }
                } catch (_) {}
                editor._openSshUrl(`ssh://${vi.kvmUser || connectUser}@${vi.kvmHost}`);
                if (editor.showNotification) {
                    editor.showNotification(
                        `[iTerm] SSH to ${vi.kvmHost}. Virsh command copied -- paste:\n  ${_virshCmd}`,
                        'info', 7000
                    );
                }
                return;
            }
            if (method === 'console' && _wantsIterm && consoleServer && editor._openSshUrl) {
                // iTerm path for serial console: ssh to console-server on
                // the discovered port. Port goes in the URL authority so
                // the Mac `ssh://` handler passes it through to `ssh -p`.
                const _consoleUser = connectUser || 'dn';
                const _consoleHost = consolePort ? `${consoleServer}:${consolePort}` : consoleServer;
                if (window.ObjectDetection) {
                    window.ObjectDetection._pendingDevice = device;
                    window.ObjectDetection._pendingPassword = connectPass;
                }
                editor._openSshUrl(`ssh://${_consoleUser}@${_consoleHost}`);
                if (editor.showNotification) {
                    editor.showNotification(
                        `[iTerm] SSH to ${consoleServer}${consolePort ? ' port ' + consolePort : ''} (serial console)`,
                        'info', 5000
                    );
                }
                return;
            }

            if (method === 'virsh_console' && device.sshConfig._virshInfo && window.TerminalPanel?.open) {
                const vi = device.sshConfig._virshInfo;
                window.TerminalPanel.open({
                    deviceId,
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
                    deviceId,
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
            if (_canSSH && editor._openSshUrl && !_wantsWeb) {
                // ObjectDetection._openSshUrl owns the notification (including
                // the Web Terminal fallback button for remote-Mac users whose
                // iTerm can't reach lab CGNAT IPs). We only need to seed the
                // pending device + password so the clipboard copy and toast
                // have context. Avoid calling editor.showNotification here --
                // it would overlap with the iTerm fallback toast.
                if (window.ObjectDetection) {
                    window.ObjectDetection._pendingDevice = device;
                    if (connectPass) window.ObjectDetection._pendingPassword = connectPass;
                }
                editor._openSshUrl(`ssh://${connectUser}@${connectHost}`);
            } else if (window.TerminalPanel?.open) {
                window.TerminalPanel.open({
                    deviceId,
                    host: connectHost,
                    user: connectUser,
                    password: connectPass,
                    method: method || 'ssh_mgmt',
                    deviceLabel: device.label || connectHost || 'Device',
                });
                editor.showNotification(`[OK] Web terminal opened to ${device.label || connectHost}`, 'success', 4000);
            } else if (editor._openSshUrl) {
                if (window.ObjectDetection) {
                    window.ObjectDetection._pendingDevice = device;
                    if (connectPass) window.ObjectDetection._pendingPassword = connectPass;
                }
                editor._openSshUrl(`ssh://${connectUser}@${connectHost}`);
            }
        }
    }

    const probeAndShowMethods = async () => {
        const apiDeviceId = _currentApiDeviceId();
        const typedHost = (hostInput?.value || '').trim();
        if (!apiDeviceId || !typedHost || !methodsList) return;
        if (_isUnsafeGeneratedProbe(apiDeviceId)) {
            const msg = 'Probe paused until backend registration returns a real device identity. Save/verify this device first.';
            _lastProbeResult = null;
            _markProbeUnknown('backend_identity_pending');
            if (probeStatus) probeStatus.textContent = msg;
            methodsList.innerHTML = `<span style="color:#e67e22;">${msg}</span>`;
            return;
        }
        if (device._probeRetryAfter && Date.now() < device._probeRetryAfter) {
            const waitSec = Math.ceil((device._probeRetryAfter - Date.now()) / 1000);
            if (probeStatus) probeStatus.textContent = `Probe temporarily unavailable. Retrying is allowed in ${waitSec}s.`;
            return;
        }
        if (probeStatus) {
            probeStatus.innerHTML = '<span style="display:inline-flex;align-items:center;gap:4px;"><span style="display:inline-block;width:8px;height:8px;border:2px solid #27ae60;border-top-color:transparent;border-radius:50%;animation:sshProbeSpin 0.6s linear infinite;"></span> Probing...</span>';
        }
        try {
            const requestToken = _newIdentityToken(typedHost);
            const probeHostHint = _sshDialogIsIp(typedHost) ? typedHost : '';
            const result = await (typeof ScalerAPI !== 'undefined' && ScalerAPI.probeConnection
                ? ScalerAPI.probeConnection(apiDeviceId, probeHostHint)
                : Promise.reject(new Error('ScalerAPI.probeConnection not available')));
            if (!_isIdentityRequestCurrent(requestToken, (hostInput.value || '').trim())) {
                if (probeStatus) probeStatus.textContent = 'Probe result ignored because the device SN/host changed.';
                return;
            }
            const identityCheck = _validateIdentityResult(result, requestToken, null, typedHost);
            if (!identityCheck.ok) {
                if (probeStatus) probeStatus.textContent = `[WARN] ${identityCheck.reason} Result ignored.`;
                if (editor.showToast) editor.showToast(`[WARN] ${identityCheck.reason}`, 'warning', 6000);
                return;
            }
            _lastProbeResult = result;
            const hasReachable = (result.methods || []).some(m => m.reachable);
            device._sshReachable = hasReachable;
            if (hasReachable) {
                device._sshReachableAt = Date.now();
            } else {
                _markProbeUnknown('no_reachable_methods');
            }

            // SN host-lock: any reachable SN-based method (ssh_sn / console /
            // virsh_console) is hard evidence that we know how to talk to
            // THIS device by serial -- which makes the device's serial /
            // KVM hostname the source of truth, not whatever stale mgmt IP
            // the inventory currently advertises. Stamp the lock so:
            //   - DNAAS / NM / generator writers refuse to overwrite
            //     `sshConfig.host` with a mgmt IP for this device,
            //   - SSHConfigGuard restores the SN host if a writer slips
            //     past the gate,
            //   - reopening this dialog displays the SN, not the IP.
            // Only sets the lock; never clears it on a probe that fails.
            // Failure = "we couldn't reach right now", not "the SN is
            // wrong". The user can override explicitly via Save.
            try {
                const _snMethods = (result.methods || [])
                    .filter(m => m.reachable && (m.method === 'ssh_sn' || m.method === 'console' || m.method === 'virsh_console'));
                if (_snMethods.length > 0) {
                    device.sshConfig = device.sshConfig || {};
                    // Choose the locked identifier in priority order:
                    // 1. existing _userSavedHost if it is non-IP (the user
                    //    explicitly chose a serial/hostname)
                    // 2. the device serial number
                    // 3. the m.host of the first SN-based reachable row
                    //    that is non-IP (e.g. console server hostname)
                    const _existingSaved = (device.sshConfig._userSavedHost || '').trim();
                    let _lockHost = '';
                    if (_existingSaved && !_isMgmtIpLike(_existingSaved)) _lockHost = _existingSaved;
                    if (!_lockHost && device.deviceSerial) _lockHost = String(device.deviceSerial);
                    if (!_lockHost) {
                        const _nonIpRow = _snMethods.find(m => m.host && !_isMgmtIpLike(m.host));
                        if (_nonIpRow) _lockHost = String(_nonIpRow.host);
                    }
                    if (_lockHost) {
                        device.sshConfig._snVerified = true;
                        device.sshConfig._snVerifiedHost = _lockHost;
                        device.sshConfig._snVerifiedAt = Date.now();
                        device.sshConfig._snVerifiedMethods = _snMethods.map(m => m.method);
                        // If the dialog was opened on a stale mgmt IP and
                        // the operator hasn't started typing yet, swap the
                        // field to the SN-locked host so the next Save
                        // can't accidentally persist the wrong IP. We
                        // suppress the input event so this doesn't kick
                        // off another probe round-trip.
                        try {
                            if (hostInput && !panel._hostUserEdited) {
                                const _liveVal = (hostInput.value || '').trim();
                                if (_liveVal && _isMgmtIpLike(_liveVal) && !_isMgmtIpLike(_lockHost) && _liveVal !== _lockHost) {
                                    hostInput.value = _lockHost;
                                }
                            }
                        } catch (_) { /* UI-only nicety */ }
                    }
                }
            } catch (_) { /* lock is best-effort, never break the probe UX */ }

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
                const activeNcc = result.cluster?.active_ncc_vm || (m.vms_running && m.vms_running[0]) || nccVms[0] || '';

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
                // Honor the operator's manual pin: if they previously
                // clicked "Connect" on a specific NCC row in this dialog,
                // we sticky that VM in `device.sshConfig._userPinnedActiveNccVm`
                // and the row stays painted ACTIVE even after the next
                // backend re-probe lands on a different guess. The "Verify"
                // button (header) clears this pin so an explicit re-probe
                // re-establishes ground truth.
                const _pinnedVm = device.sshConfig?._userPinnedActiveNccVm || '';
                const _clusterForRender = _pinnedVm
                    ? { ...result.cluster, active_ncc_vm: _pinnedVm,
                        active_ncc_host: _pinnedVm,
                        active_ncc_source: 'user_pinned' }
                    : result.cluster;
                html += _renderClusterInfo(_clusterForRender, textColor, labelColor, inputBg, inputBorder, connectBtnHtml, methodsList);
            }
            methodsList.innerHTML = html;

            // For cluster devices: show active NCC badge, persist to virshInfo, and auto-default host
            if (result.cluster?.active_ncc_vm) {
                device.sshConfig = device.sshConfig || {};
                if (device.sshConfig._virshInfo) {
                    device.sshConfig._virshInfo.activeNcc = result.cluster.active_ncc_vm;
                } else {
                    const virshMethod = (result.methods || []).find(m => m.method === 'virsh_console');
                    if (virshMethod) {
                        device.sshConfig._virshInfo = {
                            kvmHost: virshMethod.host,
                            kvmUser: virshMethod.kvm_credentials?.username || 'dn',
                            kvmPass: virshMethod.kvm_credentials?.password || 'drive1234!',
                            kvmName: virshMethod.kvm_host_name || virshMethod.host,
                            nccVms: (virshMethod.ncc_vms || []).filter(Boolean),
                            activeNcc: result.cluster.active_ncc_vm,
                        };
                    }
                }
                const nccBadge = panel.querySelector('#ssh-active-ncc-badge');
                const verifyBtn = panel.querySelector('#ssh-active-ncc-verify');
                if (nccBadge) {
                    // Confidence bucket derived from the backend `active_ncc_source`.
                    // User reported: "Is PE-4 TRULY NCC-0 active?" -- the badge used
                    // to paint solid green regardless of how the backend resolved
                    // the claim. `fallback` = we picked hosts[0]. `kvm_first_running`
                    // = both NCCs were running, we picked the first one virsh
                    // listed. Those are guesses, not facts. Paint them amber +
                    // append "(guess)" / "(cached)" / etc. so the operator knows.
                    const _src = (result.cluster.active_ncc_source || '').toLowerCase();
                    let _conf, _srcLabel, _color, _bg, _border;
                    if (_src === 'port22_alive' || _src === 'dns_match' || _src === 'virsh_console_verified' ||
                        _src === 'kvm_domifaddr_match' || _src === 'kvm_arp_mac_match') {
                        _conf = 'verified'; _srcLabel = _src.replace(/_/g, ' ');
                        _color = '#27ae60'; _bg = 'rgba(39,174,96,0.12)'; _border = 'rgba(39,174,96,0.35)';
                    } else if (_src === 'cached' || _src === 'kvm_only_running') {
                        _conf = 'cached'; _srcLabel = _src.replace(/_/g, ' ');
                        _color = '#d4a017'; _bg = 'rgba(230,193,23,0.12)'; _border = 'rgba(230,193,23,0.40)';
                    } else {
                        _conf = 'guess'; _srcLabel = _src || 'unknown';
                        _color = '#e67e22'; _bg = 'rgba(230,126,34,0.12)'; _border = 'rgba(230,126,34,0.45)';
                    }
                    nccBadge.textContent = `Active: ${result.cluster.active_ncc_vm} (${_conf})`;
                    nccBadge.title = `Backend source: ${_srcLabel}`;
                    nccBadge.style.color = _color;
                    nccBadge.style.background = _bg;
                    nccBadge.style.border = `1px solid ${_border}`;
                    nccBadge.style.display = 'inline-block';
                }
                if (verifyBtn && !verifyBtn._wired) {
                    verifyBtn._wired = true;
                    verifyBtn.style.display = 'inline-block';
                    verifyBtn.addEventListener('click', async () => {
                        const prevLabel = verifyBtn.textContent;
                        verifyBtn.disabled = true;
                        verifyBtn.textContent = 'Verifying...';
                        try {
                            // Verify = "throw away the pin, get me ground
                            // truth". The pin exists so backend re-probes
                            // don't visually flip the operator's choice
                            // mid-decision; pressing Verify is the explicit
                            // request to re-establish source-of-truth.
                            if (device.sshConfig && device.sshConfig._userPinnedActiveNccVm) {
                                console.log(
                                    `[SSH] Verify pressed -- clearing active-NCC pin `
                                    + `(was '${device.sshConfig._userPinnedActiveNccVm}')`
                                );
                                delete device.sshConfig._userPinnedActiveNccVm;
                                delete device.sshConfig._userPinnedAt;
                            }
                            // Re-probe via the same ScalerAPI path the dialog
                            // already uses. The backend prefers
                            // `virsh_console_verified` / `port22_alive` over
                            // cached data when it has a fresh signal, so a
                            // re-probe IS the source of truth.
                            await probeAndShowMethods();
                            if (editor.showToast) editor.showToast('[OK] Active-NCC re-probed', 'success', 2500);
                        } catch (e) {
                            if (editor.showToast) editor.showToast(`[ERR] Verify failed: ${e?.message || e}`, 'error', 3500);
                        } finally {
                            verifyBtn.disabled = false;
                            verifyBtn.textContent = prevLabel;
                        }
                    });
                } else if (verifyBtn) {
                    verifyBtn.style.display = 'inline-block';
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

            // If the upgrade flow stamped a post-delete hint, highlight the
            // NCC row that was active right before `system delete` ran. That
            // NCC's host key will have rotated on reboot; selecting it here
            // lines the host field up with the NCC the operator needs to
            // clear. Matches by ncc_id first, falling back to vm name.
            const _postDelCfg = device.sshConfig || {};
            if (_postDelCfg._postDeleteClearHostKey) {
                const wantId = (_postDelCfg._postDeleteActiveNccId !== null
                    && _postDelCfg._postDeleteActiveNccId !== undefined)
                    ? String(_postDelCfg._postDeleteActiveNccId) : '';
                const wantVm = (_postDelCfg._postDeleteActiveNccVm || '').toLowerCase();
                let nccRow = null;
                if (wantId) {
                    nccRow = methodsList.querySelector(
                        `.ssh-probe-method[data-method="ssh_ncc"][data-ncc-index="${wantId}"]`);
                }
                if (!nccRow && wantVm) {
                    nccRow = Array.from(
                        methodsList.querySelectorAll('.ssh-probe-method[data-method="ssh_ncc"]'))
                        .find(r => (r.dataset.nccVm || '').toLowerCase() === wantVm) || null;
                }
                if (nccRow && nccRow.dataset.reachable === 'true') {
                    methodsList.querySelectorAll('.ssh-probe-method').forEach(row => {
                        row.style.background = 'transparent';
                        row.style.borderColor = 'transparent';
                        const dot = row.querySelector('span:first-child');
                        if (dot) dot.style.boxShadow = '';
                    });
                    nccRow.style.background = isDarkMode
                        ? 'rgba(230,126,34,0.16)' : 'rgba(230,126,34,0.10)';
                    nccRow.style.borderColor = '#e67e22';
                    const dot = nccRow.querySelector('span:first-child');
                    if (dot) dot.style.boxShadow = '0 0 4px #e67e22';
                    panel._selectedMethod = 'ssh_ncc';
                    const rHost = nccRow.dataset.host || '';
                    if (rHost && hostInput && !sshConfig._userSavedHost) {
                        hostInput.value = rHost;
                    }
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
                    // Operator hit Connect on a specific NCC row -- pin
                    // that NCC as the active one so future re-renders
                    // (auto-probe, reopened dialog) don't visually flip
                    // the ACTIVE indicator back to a backend guess. The
                    // pin is per-device on sshConfig and is cleared by
                    // the "Verify" button in the header.
                    if (meth === 'ssh_ncc') {
                        const _pinVm = row.dataset.nccVm || h || '';
                        if (_pinVm) {
                            device.sshConfig = device.sshConfig || {};
                            device.sshConfig._userPinnedActiveNccVm = _pinVm;
                            device.sshConfig._userPinnedAt = Date.now();
                            console.log(`[SSH] User pinned active NCC: ${_pinVm}`);
                        }
                    }
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
                        // Same pin-on-select behaviour as the Connect btn
                        // (see comment there). Selecting a different NCC
                        // counts as the operator's choice -- pin it so
                        // the next probe doesn't visually flip the ACTIVE
                        // tag back to a backend guess while they're still
                        // mid-decision. Cleared by the "Verify" button.
                        if (meth === 'ssh_ncc') {
                            const _pinVm = el.dataset.nccVm || h || '';
                            if (_pinVm) {
                                device.sshConfig = device.sshConfig || {};
                                device.sshConfig._userPinnedActiveNccVm = _pinVm;
                                device.sshConfig._userPinnedAt = Date.now();
                                console.log(`[SSH] User pinned active NCC (row-select): ${_pinVm}`);
                            }
                        }
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
            _lastProbeResult = null;
            const status = Number(e?.status || 0);
            const isBridgeUnavailable = !!e?.bridgeUnavailable || status === 503 || status === 502 || status === 501;
            const cleanMessage = isBridgeUnavailable
                ? 'Connection probe service is unavailable. Metadata remains unknown until the bridge is healthy and a fresh probe succeeds.'
                : `Probe failed: ${e?.message || e}`;
            _markProbeUnknown(isBridgeUnavailable ? 'probe_service_unavailable' : 'probe_failed', {
                retryMs: isBridgeUnavailable ? 15000 : 0,
            });
            if (probeStatus) probeStatus.textContent = isBridgeUnavailable ? 'Probe service unavailable' : 'Probe failed';
            if (methodsList) methodsList.innerHTML = `<span style="color:${isBridgeUnavailable ? '#e67e22' : '#e74c3c'};">[WARN] ${cleanMessage}</span>`;
        }
    }

    function _renderClusterInfo(cluster, textColor, labelColor, inputBg, inputBorder, connectBtnHtmlFn, methodsListEl) {
        if (!cluster || !cluster.is_cluster) return '';
        const activeVm = (cluster.active_ncc_vm || '').toLowerCase();
        // Confidence bucket for the "ACTIVE" tag -- matches the header badge.
        // Weak sources (fallback / kvm_first_running / empty) paint the tag
        // amber and append "(guess)" so the operator knows the ACTIVE
        // designation is a heuristic, not a verified fact.
        const _activeSrc = (cluster.active_ncc_source || '').toLowerCase();
        // ``user_pinned`` = the operator clicked Connect on a specific NCC
        // row in this dialog. We treat that as a hard fact (strongest
        // confidence) and paint solid green with a "(pinned)" tail so
        // the operator can see they're driving the choice, not the
        // backend guess. Cleared by the "Verify" button.
        const _activePinned = _activeSrc === 'user_pinned';
        const _activeStrong = _activePinned
            || _activeSrc === 'port22_alive' || _activeSrc === 'dns_match' || _activeSrc === 'virsh_console_verified' ||
            _activeSrc === 'kvm_domifaddr_match' || _activeSrc === 'kvm_arp_mac_match';
        const _activeMedium = _activeSrc === 'cached' || _activeSrc === 'kvm_only_running';
        const _activeColor = _activeStrong ? '#27ae60' : (_activeMedium ? '#d4a017' : '#e67e22');
        const _activeTail = _activePinned ? ' (pinned)' : (_activeStrong ? '' : (_activeMedium ? ' (cached)' : ' (guess)'));
        let html = `<div style="margin-top:8px;padding:6px;background:${inputBg};border:1px solid ${inputBorder};border-radius:6px;">`;
        html += `<div style="font-weight:600;color:${textColor};margin-bottom:4px;font-size:10px;">Cluster Components</div>`;
        html += `<div style="font-size:9px;color:${labelColor};margin-bottom:4px;">Legacy clusters: NCM port 49 = NCC-0, port 50 = NCC-1. GI autodetects ncc-id via NCM LLDP.</div>`;
        if (cluster.ncc_vms && cluster.ncc_vms.length > 0) {
            cluster.ncc_vms.forEach((vm, i) => {
                // ncc_hosts may be reordered active-first by the backend so
                // index-aligning it with the original ncc_vms list can attach
                // the active tag to the wrong host. The VM name itself is the
                // stable SSH/virsh target; use it first.
                const nccHost = vm || (cluster.ncc_hosts && cluster.ncc_hosts[i]) || '';
                const nccLabel = `NCC-${i}`;
                const isActive = activeVm && vm.toLowerCase() === activeVm;
                const isStandby = activeVm && !isActive;
                const dotColor = isActive ? _activeColor : (isStandby ? '#95a5a6' : '#3498db');
                const roleTag = isActive
                    ? `<span title="Backend source: ${_activeSrc || 'unknown'}" style="font-size:9px;font-weight:600;color:${_activeColor};margin-left:4px;">ACTIVE${_activeTail}</span>`
                    : (isStandby ? '<span style="font-size:9px;color:#95a5a6;margin-left:4px;">standby</span>' : '');
                const nccTag = (i === 0) ? ' (NCM port 49)' : ' (NCM port 50)';
                const _activeBgRgba = _activeStrong
                    ? 'rgba(39,174,96,0.08)'
                    : (_activeMedium ? 'rgba(230,193,23,0.10)' : 'rgba(230,126,34,0.10)');
                const _activeBorderRgba = _activeStrong
                    ? 'rgba(39,174,96,0.4)'
                    : (_activeMedium ? 'rgba(230,193,23,0.45)' : 'rgba(230,126,34,0.55)');
                const activeBorder = isActive
                    ? `border:1px solid ${_activeBorderRgba};background:${_activeBgRgba};`
                    : 'border:1px solid transparent;';
                const _activeTitle = isActive
                    ? (_activeStrong ? 'Active NCC (verified) - click to connect'
                        : (_activeMedium ? `Active NCC (cached from ${_activeSrc || 'ops'}) - click to connect`
                            : 'Active NCC is a HEURISTIC GUESS - click Verify in the header to re-probe'))
                    : (isStandby ? 'Standby NCC' : 'Click to SSH to this NCC');
                html += `<div class="ssh-probe-method" data-method="ssh_ncc" data-host="${nccHost}" data-reachable="${nccHost ? 'true' : 'false'}" data-is-active-ncc="${isActive}"
                    data-ncc-index="${i}" data-ncc-vm="${vm || ''}"
                    style="display:flex;align-items:center;gap:6px;padding:3px 6px;margin:2px 0;border-radius:4px;cursor:${nccHost ? 'pointer' : 'default'};${activeBorder}"
                    title="${_activeTitle}">
                    <span style="width:6px;height:6px;border-radius:50%;background:${dotColor};flex-shrink:0;${isActive ? 'box-shadow:0 0 4px ' + _activeColor + ';' : ''}"></span>
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
        // Track whether the operator has typed in the field. Lets
        // probeAndShowMethods auto-replace a stale mgmt IP with the
        // SN-locked host on first probe success WITHOUT clobbering an
        // edit-in-progress.
        panel._hostUserEdited = false;
        hostInput.addEventListener('input', () => {
            panel._hostUserEdited = true;
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
            const serial = device._registeredSerialNumber
                || device.registeredSerialNumber
                || device.deviceSerial
                || device.serial
                || '';
            discoverConsoleBtn.textContent = 'Discovering...';
            discoverConsoleBtn.disabled = true;
            try {
                const discoveryHost = hostInput?.value?.trim() || serial || '';
                const requestToken = _newIdentityToken(discoveryHost);
                const r = await (typeof ScalerAPI !== 'undefined' && ScalerAPI.discoverConsole
                    ? ScalerAPI.discoverConsole(deviceId, serial, discoveryHost)
                    : Promise.reject(new Error('ScalerAPI.discoverConsole not available')));
                if (!_isIdentityRequestCurrent(requestToken, hostInput?.value?.trim() || discoveryHost)) {
                    if (consoleInfoSection) consoleInfoSection.style.display = '';
                    if (consoleDetails) consoleDetails.innerHTML = '<span style="color:#e67e22;">Console discovery ignored because the device SN/host changed.</span>';
                    return;
                }
                const identityCheck = _validateIdentityResult({
                    ...r,
                    serial_number: r.serial_no || r.serial_number || serial || ''
                }, requestToken, null, discoveryHost);
                if (!identityCheck.ok) {
                    if (consoleInfoSection) consoleInfoSection.style.display = '';
                    if (consoleDetails) consoleDetails.innerHTML = `<span style="color:#e67e22;">${identityCheck.reason} Console mapping ignored.</span>`;
                    if (editor.showToast) editor.showToast(`[WARN] ${identityCheck.reason}`, 'warning', 6000);
                    return;
                }
                _lastDiscovery = r;
                if (editor.showToast) editor.showToast(`[OK] Console: ${r.console_server || 'N/A'} port ${r.port || '?'} (${r.source || 'unknown'})`, 'success');

                let html = '';
                if (r.console_server) {
                    const targetLabel = r.is_cluster ? ` -> ${r.console_target_label || 'NCP data-plane'}` : '';
                    html += `<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                        <strong style="color:${isDarkMode ? '#2ecc71' : '#27ae60'}">Console${targetLabel}</strong>
                        <span style="color:${labelColor};margin-left:auto;">${r.console_server} port ${r.port || '?'}</span>
                    </div>`;
                    html += `<div style="color:${isDarkMode ? '#888' : '#999'};">Source: ${r.source || 'unknown'}${r.serial_no ? ' | SN: ' + r.serial_no : ''}</div>`;
                }
                if (r.cluster_note) {
                    html += `<div style="margin-top:6px;padding:6px 8px;background:${isDarkMode ? 'rgba(230,126,34,0.15)' : 'rgba(230,126,34,0.1)'};border-left:3px solid #e67e22;border-radius:6px;color:${isDarkMode ? '#f0c674' : '#d35400'};font-size:10px;line-height:1.35;">${r.cluster_note}</div>`;
                }
                if (r.pdu_entries && r.pdu_entries.length > 0) {
                    html += '<div style="margin-top:6px;color:' + labelColor + ';"><strong>PDU:</strong>';
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
                    // SN host-lock: when discovery returns a console mapping
                    // sourced from `console_mappings` / `zohar_db`, that's
                    // canonical SN -> console-server data. Stamp the lock
                    // so future writers can't push a stale mgmt IP into
                    // `sshConfig.host` for this device. See SSHConfigGuard.
                    try {
                        device.sshConfig = device.sshConfig || {};
                        const _existingSaved = (device.sshConfig._userSavedHost || '').trim();
                        let _lockHost = '';
                        if (_existingSaved && !_isMgmtIpLike(_existingSaved)) _lockHost = _existingSaved;
                        if (!_lockHost && (r.serial_no || device.deviceSerial)) _lockHost = String(r.serial_no || device.deviceSerial);
                        if (!_lockHost && r.console_server) _lockHost = String(r.console_server);
                        if (_lockHost) {
                            device.sshConfig._snVerified = true;
                            device.sshConfig._snVerifiedHost = _lockHost;
                            device.sshConfig._snVerifiedAt = Date.now();
                            device.sshConfig._snVerifiedSource = r.source || 'discover_console';
                        }
                    } catch (_) { /* lock is best-effort */ }
                    const badge = r.source === 'zohar_db' ? 'Lab DB' : (r.source === 'device42' ? 'Device42' : 'Discovered');
                    const consoleTarget = r.is_cluster ? (r.console_target_label || 'NCP data-plane') : 'Serial';
                    const consoleLabel = r.is_cluster ? `Console -> ${consoleTarget} [${badge}]` : `Console (Serial) [${badge}]`;
                    const consoleTitle = r.is_cluster
                        ? `This console reaches ${consoleTarget}, not the NCC. Use Virsh Console for NCC access.`
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
                        const scanToken = _newIdentityToken(hostInput?.value?.trim() || serial || '');
                        const scan = await ScalerAPI.consoleScan(deviceId, serial);
                        if (!_isIdentityRequestCurrent(scanToken, hostInput?.value?.trim() || serial || '')) {
                            if (consoleDetails) consoleDetails.innerHTML = '<span style="color:#e67e22;">Console scan ignored because the device SN/host changed.</span>';
                            return;
                        }
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
                `Hard PDU reboot ${entry.pdu} outlet ${entry.outlet}?\n\nThis cuts physical power OFF and then ON. DNOS will go down immediately.\nDevice: ${device.label || deviceId}`
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
                pduPowerBtn.textContent = 'PDU Reboot';
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

    const saveAddress = async (opts = {}) => {
        const host = hostInput.value.trim();
        const user = userInput.value.trim() || 'dnroot';
        const password = passInput.value;
        const oldHost = device.sshConfig?.host;
        const oldSavedHost = device.sshConfig?._userSavedHost || oldHost || '';
        const clearHostKeyCheckbox = panel.querySelector('#ssh-clear-hostkey');
        const clearHostKey = clearHostKeyCheckbox ? clearHostKeyCheckbox.checked : false;

        // Collect every alias a stale key could live under. Keeps the
        // SSH dialog in sync with the recovery flow in ObjectDetection
        // (hostname, IP, short-name, all known NCC aliases, cluster
        // mgmt IP). When ObjectDetection exposes the helper we use it;
        // otherwise we fall back to just `host`.
        let aliases = [host].filter(Boolean);
        try {
            if (window.ObjectDetection && typeof window.ObjectDetection._collectStaleHostKeyTargets === 'function') {
                const collected = window.ObjectDetection._collectStaleHostKeyTargets(device, {
                    host: device.sshConfig?._activeNccHost || '',
                    ip: device.sshConfig?._activeNccIp || '',
                });
                // Make sure the user-entered host is always included.
                const merged = new Set(collected);
                if (host) merged.add(host);
                aliases = Array.from(merged).filter(Boolean);
            }
        } catch (_) { /* fall back to [host] */ }

        // Fold in any post-delete identifiers the upgrade flow stamped
        // (the pre-delete mgmt IP + active NCC VM name). Those are the
        // aliases whose host keys JUST rotated and that
        // `_collectStaleHostKeyTargets` does not know about yet.
        try {
            const _pd = device.sshConfig || {};
            if (_pd._postDeleteClearHostKey) {
                const mergedPd = new Set(aliases);
                const maybeAdd = (v) => {
                    if (!v || typeof v !== 'string') return;
                    const s = v.trim();
                    if (!s) return;
                    mergedPd.add(s);
                    const short = s.split('.')[0];
                    if (short && short !== s) mergedPd.add(short);
                };
                maybeAdd(_pd._postDeleteMgmtIp);
                maybeAdd(_pd._postDeleteActiveNccVm);
                aliases = Array.from(mergedPd).filter(Boolean);
            }
        } catch (_) { /* fall back to current aliases */ }

        if (clearHostKey && host) {
            let _clearOk = false;
            try {
                if (editor.showNotification) editor.showNotification(`Clearing host key for ${host} on Mac...`, 'info');
                const resp = await _sshDialogAuthFetch('/api/ssh/clear-hostkey', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ hosts: aliases, host: aliases[0] })
                });
                const result = await resp.json();
                if (result.mac_cleared) {
                    _clearOk = true;
                    // Post-delete hint served its purpose -- drop it so the
                    // banner + auto-check don't persist across unrelated
                    // future SSH dialog opens.
                    if (typeof panel._dismissPostDeleteHint === 'function') {
                        try { panel._dismissPostDeleteHint({ persistAutoCheck: true }); } catch (_) {}
                    }
                    if (editor.showNotification) editor.showNotification(`[OK] Host key cleared on Mac (${result.mac_ip}) for ${aliases.length} alias(es) -- connecting...`, 'success');
                } else if (result.mac_ip && !result.mac_cleared) {
                    _showMacIpPrompt(panel, editor, host, result.mac_ip, result.message, user, password, aliases, device);
                    // Still persist the sshConfig below so the "auto-clear
                    // on connect" intent is not lost while the user
                    // decides to retry, copy, or skip.
                } else if (!result.mac_ip) {
                    _showMacIpPrompt(panel, editor, host, '', 'Mac IP not configured', user, password, aliases, device);
                } else {
                    if (editor.showNotification) editor.showNotification(`[WARN] ${result.error || result.message || 'Failed to clear host key'}`, 'warning');
                }
            } catch (err) {
                if (editor.showNotification) editor.showNotification(`[ERROR] Failed to clear host key: ${err.message}`, 'error');
            }
            if (_clearOk && host) {
                // Auto-connect after successful clear
                setTimeout(() => {
                    if (editor._openSshUrl) {
                        if (window.ObjectDetection) {
                            window.ObjectDetection._pendingPassword = password;
                            window.ObjectDetection._pendingDevice = device;
                        }
                        editor._openSshUrl(`ssh://${user}@${host}`);
                    }
                }, 500);
            }
        }

        // SN host-lock interaction with explicit Save:
        //  - If the user typed a non-IP value (serial, hostname, console
        //    server name) -> they want SN-style routing; refresh the lock
        //    so future writers can't push a mgmt IP into this slot.
        //  - If the user typed an IP -> explicit override. Clear the
        //    lock so the operator can use the mgmt IP path again
        //    without the guard auto-healing it back to the SN.
        //  - Empty host -> leave any existing lock alone (user just
        //    cleared the field; they may re-enter shortly).
        const _saveHostIsIp = !!host && /^\d+\.\d+\.\d+\.\d+$/.test(host);
        const _saveSnPatch = (() => {
            if (!host) return {};
            if (_saveHostIsIp) {
                return {
                    _snVerified: false,
                    _snVerifiedHost: '',
                    _snVerifiedAt: device.sshConfig?._snVerifiedAt || 0,
                    _snClearedByUserAt: Date.now(),
                };
            }
            return {
                _snVerified: true,
                _snVerifiedHost: host,
                _snVerifiedAt: Date.now(),
                _snVerifiedSource: device.sshConfig?._snVerifiedSource || 'user_save',
            };
        })();

        device.sshConfig = {
            ...(device.sshConfig || {}),
            host: host,
            user: user,
            password: password,
            _userSavedHost: host || null,
            _userSavedUser: user || null,
            _userSavedPass: password || null,
            _lastWorkingMethod: panel._selectedMethod || device.sshConfig?._lastWorkingMethod || '',
            _virshInfo: panel._virshInfo || device.sshConfig?._virshInfo || null,
            ..._saveSnPatch,
            // Persist the operator's "Always clear host key on connect"
            // intent. ObjectDetection._openSshUrl reads this flag on
            // every future iTerm launch for this device and pre-calls
            // `_clearStaleHostKeysOnMac` before dispatching the ssh://
            // URL. Set to `false` when the checkbox is unchecked so the
            // operator can opt back out at any time.
            _autoClearHostKeys: !!clearHostKey,
            _autoClearHostKeysUpdatedAt: Date.now(),
        };
        device.deviceAddress = host ? `${user}@${host}` : '';
        if (!opts.skipIdentityInvalidation && host !== oldSavedHost) {
            const invalidated = _invalidateForHostChange(host, oldSavedHost, 'ssh_host_saved');
            if (invalidated && editor.showToast) {
                editor.showToast('[INFO] Device identity changed. Cached LLDP, stack, git, and onboarding metadata were cleared until refresh.', 'info', 6000);
            }
        }

        if (typeof ScalerAPI !== 'undefined' && ScalerAPI.evictSSHPoolConnection) {
            if (oldHost) ScalerAPI.evictSSHPoolConnection(oldHost, deviceId).catch(() => {});
            if (host) ScalerAPI.evictSSHPoolConnection(host, deviceId).catch(() => {});
        }

        // Persist credentials server-side so `_get_credentials` picks them up on
        // every future SSH operation (discovery, config push, LLDP probe).
        // Without this the backend keeps falling back to `dnroot/dnroot` and
        // any device using a non-default password silently fails.
        const credentialDeviceId = _currentApiDeviceId();
        if (credentialDeviceId && user && password && typeof ScalerAPI !== 'undefined' && ScalerAPI.saveDeviceCredentials) {
            ScalerAPI.saveDeviceCredentials(credentialDeviceId, user, password).then((r) => {
                console.log(`[SSH] creds persisted for ${credentialDeviceId}`, r);
                const hint = panel.querySelector('#ssh-save-creds-hint');
                if (hint) {
                    hint.textContent = '[OK] creds saved';
                    hint.style.display = '';
                    setTimeout(() => { if (hint) hint.style.display = 'none'; }, 2500);
                }
            }).catch((err) => {
                console.warn(`[SSH] creds persist failed for ${credentialDeviceId}:`, err?.message || err);
                if (editor.showToast) editor.showToast(`[WARN] Save cred to server failed: ${err?.message || 'unknown'}`, 'warning', 4000);
            });
        } else if (credentialDeviceId && !password && typeof ScalerAPI !== 'undefined' && ScalerAPI.deleteDeviceCredential) {
            ScalerAPI.deleteDeviceCredential(credentialDeviceId).catch(() => {});
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
    const verifyStatus = panel.querySelector('#ssh-verify-status');
    const cadenceSel = panel.querySelector('#ssh-monitor-cadence');
    const depthSel = panel.querySelector('#ssh-discovery-depth');

    // Re-hydrate the Advanced selectors from any previously saved
    // per-device policy so the operator's last choice "sticks" across
    // dialog opens. New devices fall back to the defaults baked into
    // the <option selected> markup above.
    try {
        const pol = (device.sshConfig && device.sshConfig._monitorPolicy) || {};
        if (cadenceSel && pol.cadence) cadenceSel.value = pol.cadence;
        if (depthSel && pol.discovery_depth) depthSel.value = pol.discovery_depth;
    } catch (_) { /* defaults already applied */ }

    /**
     * Render a single inline status block in the dialog. `kind` controls
     * the colour (info/success/warn/error). When `actions` is provided,
     * each entry is rendered as a button; clicking calls `onClick`.
     * Pass `kind: 'spinner'` to show the animated "verifying..." state.
     */
    const renderVerifyStatus = (kind, message, actions = []) => {
        if (!verifyStatus) return;
        const palette = {
            info:    { bg: 'rgba(52, 152, 219, 0.10)', bd: 'rgba(52, 152, 219, 0.45)', fg: '#3498db', icon: 'i' },
            spinner: { bg: 'rgba(52, 152, 219, 0.10)', bd: 'rgba(52, 152, 219, 0.45)', fg: '#3498db', icon: '~' },
            success: { bg: 'rgba(39, 174, 96, 0.12)',  bd: 'rgba(39, 174, 96, 0.45)',  fg: '#27ae60', icon: '[OK]' },
            warn:    { bg: 'rgba(241, 196, 15, 0.14)', bd: 'rgba(241, 196, 15, 0.5)',  fg: '#f39c12', icon: '!' },
            error:   { bg: 'rgba(231, 76, 60, 0.14)',  bd: 'rgba(231, 76, 60, 0.5)',   fg: '#e74c3c', icon: 'x' },
        }[kind] || { bg: inputBg, bd: inputBorder, fg: textColor, icon: '*' };
        verifyStatus.style.background = palette.bg;
        verifyStatus.style.borderColor = palette.bd;
        verifyStatus.style.color = textColor;
        verifyStatus.style.display = '';
        const spinnerSpan = (kind === 'spinner')
            ? `<span style="
                display: inline-block; width: 10px; height: 10px;
                border: 2px solid ${palette.fg};
                border-top-color: transparent; border-radius: 50%;
                animation: ssh-verify-spin 0.8s linear infinite;
                margin-right: 6px; vertical-align: middle;
            "></span>` : `<span style="color: ${palette.fg}; font-weight: 700; margin-right: 6px;">${palette.icon}</span>`;
        const actionHtml = (actions || []).map((a, i) => `
            <button data-verify-action="${i}" style="
                margin-right: 6px; margin-top: 6px;
                padding: 4px 10px; border-radius: 4px;
                border: 1px solid ${palette.bd};
                background: ${a.primary ? palette.fg : 'transparent'};
                color: ${a.primary ? '#fff' : palette.fg};
                font-size: 10px; font-weight: 600; cursor: pointer;
            ">${a.label}</button>
        `).join('');
        verifyStatus.innerHTML = `
            <div>${spinnerSpan}<span style="vertical-align: middle;">${message}</span></div>
            ${actionHtml ? `<div style="margin-top: 2px;">${actionHtml}</div>` : ''}
        `;
        (actions || []).forEach((a, i) => {
            const btn = verifyStatus.querySelector(`[data-verify-action="${i}"]`);
            if (btn && typeof a.onClick === 'function') {
                btn.addEventListener('click', a.onClick);
            }
        });
    };

    const friendlyBridgeError = (err) => {
        const status = err?.httpStatus || err?.status || 0;
        const raw = (err?.message || String(err || '') || '').trim();
        if (status === 401) return 'Your session is not authenticated. Log in again, then retry onboarding.';
        if (status === 403) return 'Your user does not have permission to register devices. Ask an admin for engineer access.';
        if (status === 404) return 'The onboarding endpoint is not available through the active web server. Reload the app services and retry.';
        if (status >= 500) return `Backend service is unavailable (${status}). The device was not registered; retry after the bridge is healthy.`;
        if (/failed to fetch|networkerror|aborterror/i.test(raw)) {
            return 'The backend is unreachable from the browser. Check the app service and network, then retry.';
        }
        return raw || 'Backend could not complete onboarding. Retry or ask an admin to check the bridge logs.';
    };

    const applyCanonicalOnboardingContext = (result = {}, ctx = null) => {
        const canonical = result.device_context?.canonical || result.device_context?.identity || {};
        const backendMetadata = result.onboarding_metadata || result.device_context?.validated_metadata || null;
        const metadataReliable = !!(backendMetadata && backendMetadata.reliable === true && backendMetadata.status === 'reliable');
        const metadataCtx = metadataReliable ? (backendMetadata.context || ctx || {}) : null;
        const mgmtIp = (
            result.management_ip || canonical.management_ip || metadataCtx?.resolved_ip || metadataCtx?.mgmt_ip || metadataCtx?.ip || ''
        ).toString().trim();
        const registeredId = (
            result.registered_device_id || canonical.device_id || result.hostname || canonical.hostname || deviceId || ''
        ).toString().trim();
        const hostname = (result.hostname || canonical.hostname || registeredId || '').toString().trim();
        const serialNumber = (result.serial_number || canonical.serial_number || metadataCtx?.serial_number || metadataCtx?.serial || '').toString().trim();
        const actualConfigHostname = (
            metadataCtx?.identity?.config_hostname
            || result.identity?.config_hostname
            || result.actual_hostname
            || result.raw_verify?.actual_hostname
            || canonical.hostname
            || result.hostname
            || hostname
            || ''
        ).toString().trim();
        const onboardingDeviceState = (
            result.device_state
            || result.raw_verify?.device_state
            || backendMetadata?.device_state
            || metadataCtx?.device_state
            || ''
        ).toString().trim().toUpperCase();

        device._monitorRegistered = !!(result.registered || device._monitorRegistered);
        device._onboardingPhase = ctx ? 'api_ready' : (result.onboarding_phase || 'context_hydrating');
        device._onboarding = {
            phase: device._onboardingPhase,
            source: metadataReliable ? 'backend-validated-onboarding' : 'verify-and-register',
            metadataStatus: backendMetadata?.status || 'unknown',
            metadataReliable,
            metadataReason: backendMetadata?.reason || '',
            sourceIdentity: backendMetadata?.source_identity || null,
            updatedAt: Date.now(),
        };
        if (result.key || canonical.key) device._monitoredKey = result.key || canonical.key;
        if (registeredId) device._registeredDeviceId = registeredId;
        if (hostname) device._registeredHostname = hostname;
        if (mgmtIp) device._registeredMgmtIp = mgmtIp;
        if (serialNumber) {
            device.deviceSerial = serialNumber;
            device.serial = serialNumber;
            device._registeredSerialNumber = serialNumber;
        }
        if (onboardingDeviceState) {
            device._modeRawState = onboardingDeviceState;
        }
        if (result.platform || canonical.platform || metadataCtx?.platform) {
            device._platform = result.platform || canonical.platform || metadataCtx.platform;
        }
        device._monitorCapabilities = result.capabilities || result.device_context?.capabilities || device._monitorCapabilities || {
            ssh: true,
            device_context: true,
            monitoring: true,
            lldp: true,
            link_details: true,
            xray: true,
            health: true,
            system_stack: true,
        };
        device._monitoringOptions = result.monitoring_options || result.device_context?.monitoring_options || device._monitoringOptions || {
            state: 'preparing',
            phase: device._onboardingPhase,
            subsystems: Array.isArray(result.monitor_started_subsystems) ? result.monitor_started_subsystems : [],
        };
        if (!metadataReliable) {
            _clearUnreliableOnboardingMetadata(backendMetadata, mgmtIp || currentHost || '', registeredId || hostname || deviceId || '');
        }

        device.sshConfig = device.sshConfig || {};
        if (mgmtIp) {
            device.sshConfig._registeredMgmtIp = mgmtIp;
            device.sshConfig._enrichedMgmtIp = mgmtIp;
            device.sshConfig._mgmtIp = mgmtIp;
            device.sshConfig.hostBackup = device.sshConfig.hostBackup || mgmtIp;
        }
        if (hostname) device.sshConfig._registeredHostname = hostname;
        if (serialNumber) device.sshConfig._registeredSerialNumber = serialNumber;
        if (actualConfigHostname && window.TopologyDeviceIdentity?.applyHostnameCanvasMismatch) {
            window.TopologyDeviceIdentity.applyHostnameCanvasMismatch(device, actualConfigHostname, {
                editor,
                deviceId: registeredId || hostname || deviceId,
                source: 'backend-validated-onboarding',
                deviceState: onboardingDeviceState,
                shouldAutoRepairLabel: (currentLabel, cfgHost) => {
                    try {
                        return !!(window.DeviceMonitor
                            && typeof window.DeviceMonitor._shouldAutoRepairLabel === 'function'
                            && window.DeviceMonitor._shouldAutoRepairLabel(currentLabel, cfgHost));
                    } catch (_) {
                        return false;
                    }
                },
            });
        }

        if (metadataReliable && metadataCtx && typeof metadataCtx === 'object') {
            device._monitorContext = {
                ...(device._monitorContext || {}),
                interfaces: metadataCtx.interfaces || {},
                wan_interfaces: metadataCtx.wan_interfaces || [],
                bgp_peers: metadataCtx.bgp_peers || [],
                bridge_domains: metadataCtx.bridge_domains || [],
                vrfs: metadataCtx.vrfs || [],
                loopbacks: metadataCtx.loopbacks || [],
                config_summary: metadataCtx.config_summary || {},
                existing_route_targets: metadataCtx.existing_route_targets || [],
                management_ip: mgmtIp || metadataCtx.resolved_ip || metadataCtx.mgmt_ip || '',
                timestamp: metadataCtx.timestamp || backendMetadata.fetched_at || new Date().toISOString(),
                source: 'backend-validated-onboarding',
                metadata_validation: result.metadata_validation || null,
            };
            device._monitorConfigFacts = device._monitorContext;
            if (Array.isArray(backendMetadata.lldp) || Array.isArray(metadataCtx.lldp) || Array.isArray(metadataCtx.lldp_neighbors)) {
                const neighbors = Array.isArray(backendMetadata.lldp)
                    ? backendMetadata.lldp
                    : (Array.isArray(metadataCtx.lldp) ? metadataCtx.lldp : metadataCtx.lldp_neighbors);
                const cleanNeighbors = (window.LldpDialog && typeof window.LldpDialog._sanitizeLldpNeighbors === 'function')
                    ? window.LldpDialog._sanitizeLldpNeighbors(neighbors)
                    : neighbors;
                device._lldpData = {
                    neighbors: cleanNeighbors,
                    lldp_neighbors: neighbors,
                    source: 'backend-validated-onboarding',
                    last_updated: backendMetadata.fetched_at || new Date().toISOString(),
                };
                device.lldpDiscoveryComplete = true;
                if (window.TopologyDeviceIdentity?.markMetadataReady) {
                    window.TopologyDeviceIdentity.markMetadataReady(device, 'lldp', {
                        host: mgmtIp || metadataCtx.resolved_ip || metadataCtx.mgmt_ip || '',
                        deviceId: device._registeredDeviceId || device._registeredHostname || deviceId,
                        source: 'backend-validated-onboarding',
                        data: device._lldpData
                    });
                }
            }
            if (backendMetadata.stack || metadataCtx.stack) {
                const rawStack = backendMetadata.stack || metadataCtx.stack;
                const components = Array.isArray(rawStack) ? rawStack : (rawStack.components || []);
                device._stackData = {
                    components,
                    source: 'backend-validated-onboarding',
                    stack_fetched_at: backendMetadata.stack_fetched_at || metadataCtx.stack_fetched_at || backendMetadata.fetched_at || '',
                    active_ncc_node: metadataCtx.active_ncc_node || metadataCtx.active_ncc_vm || metadataCtx.active_ncc_host || '',
                };
                if ((components.length || device._stackData.stack_fetched_at) && window.TopologyDeviceIdentity?.markMetadataReady) {
                    window.TopologyDeviceIdentity.markMetadataReady(device, 'stack', {
                        host: mgmtIp || metadataCtx.resolved_ip || metadataCtx.mgmt_ip || '',
                        deviceId: device._registeredDeviceId || device._registeredHostname || deviceId,
                        source: 'backend-validated-onboarding',
                        data: device._stackData
                    });
                }
            }
            if (backendMetadata.device_state != null || metadataCtx.device_state != null) {
                device._modeRawState = String(backendMetadata.device_state || metadataCtx.device_state || '').toUpperCase();
            }
            if (metadataCtx.system_type) device._systemType = metadataCtx.system_type;
            if (metadataCtx.deploy_system_type) device._deploySystemType = metadataCtx.deploy_system_type;
            if (backendMetadata.git_commit != null || metadataCtx.git_commit != null) {
                device._gitCommit = backendMetadata.git_commit != null ? backendMetadata.git_commit : metadataCtx.git_commit;
                device._gitCommitFetchedAt = backendMetadata.git_commit_fetched_at
                    ? Date.parse(backendMetadata.git_commit_fetched_at) || Date.now()
                    : Date.now();
                if (window.TopologyDeviceIdentity?.markMetadataReady) {
                    window.TopologyDeviceIdentity.markMetadataReady(device, 'git', {
                        host: mgmtIp || metadataCtx.resolved_ip || metadataCtx.mgmt_ip || '',
                        deviceId: device._registeredDeviceId || device._registeredHostname || deviceId,
                        source: 'backend-validated-onboarding'
                    });
                }
            }
            if (metadataCtx.active_ncc_host) device.sshConfig._activeNccHost = metadataCtx.active_ncc_host;
            if (metadataCtx.active_ncc_ip) device.sshConfig._activeNccIp = metadataCtx.active_ncc_ip;
            if (metadataCtx.active_ncc_vm) device.sshConfig._activeNccVm = metadataCtx.active_ncc_vm;
            if (Array.isArray(metadataCtx.ncc_vms) && metadataCtx.ncc_vms.length) device.sshConfig._nccVms = metadataCtx.ncc_vms;
        }
    };

    const dispatchContextUpdated = (source) => {
        try {
            window.dispatchEvent(new CustomEvent('device:context-updated', {
                detail: { deviceId, device, source },
            }));
        } catch (_) {
            // dispatchEvent is best-effort; the next selection toggle
            // will still re-render the toolbar.
        }
    };

    const showCanvasHostnameMismatchPrompt = () => {
        if (!device?._hostnameMismatch || device._mismatchDismissed) return;
        const drawer = window.CanvasDrawing || null;
        if (!drawer || typeof drawer._showMismatchPopup !== 'function') return;
        try {
            const pos = editor.worldToScreen
                ? editor.worldToScreen({ x: device.x || 0, y: device.y || 0 })
                : { x: window.innerWidth / 2, y: window.innerHeight / 2 };
            drawer._showMismatchPopup(editor, device, pos.x + 34, pos.y - 18);
        } catch (err) {
            console.warn('[SSH dialog] hostname mismatch prompt failed:', err);
        }
    };

    // Inject the keyframe for the spinner once. Idempotent: a second
    // dialog instance reuses the existing rule.
    if (!document.getElementById('ssh-verify-spin-style')) {
        const style = document.createElement('style');
        style.id = 'ssh-verify-spin-style';
        style.textContent = '@keyframes ssh-verify-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }';
        document.head.appendChild(style);
    }

    /**
     * Verify-then-save wrapper. Runs a backend credential verification
     * BEFORE persisting `device.sshConfig`. Skips verification entirely
     * for the "clear credentials" path (empty host) so the legacy
     * clear-out flow is untouched.
     *
     *   Success         -> saveAddress() (existing persist + close path)
     *   Failure         -> inline smart-by-reason error block, dialog stays open
     *   Save anyway     -> set _unverifiedSave flag + saveAddress()
     *   Discard / Edit  -> just leave the dialog open
     */
    const verifyThenSave = async () => {
        const host = hostInput.value.trim();
        const user = userInput.value.trim() || 'dnroot';
        const password = passInput.value;
        const previousIdentityHost = device.sshConfig?._userSavedHost || device.sshConfig?.host || currentHost || '';

        // Empty host = "clear credentials" -- nothing to verify; fall
        // straight through to the legacy persist path so the operator
        // can still wipe an SSH config out of a topology JSON.
        if (!host) {
            try { await saveAddress(); } catch (e) { console.warn('[SSH dialog] saveAddress threw on clear-creds path:', e); }
            return;
        }

        // No password yet (e.g. user is editing host but hasn't typed a
        // password) -- skip the verification gate (verifying with no
        // password just produces an auth_failed false negative). The
        // legacy save path will still call saveDeviceCredentials only
        // when both user + password are present.
        if (!password) {
            try { await saveAddress(); } catch (e) { console.warn('[SSH dialog] saveAddress threw on no-password path:', e); }
            return;
        }

        if (typeof ScalerAPI === 'undefined' || typeof ScalerAPI.verifyCredentials !== 'function') {
            // Backend missing the new endpoint -- fail open, preserve
            // legacy behaviour. Better than blocking Save when an
            // older bridge is paired with a newer frontend.
            console.warn('[SSH dialog] ScalerAPI.verifyCredentials unavailable -- falling back to legacy save');
            try { await saveAddress(); } catch (e) { console.warn('[SSH dialog] saveAddress threw:', e); }
            return;
        }

        const cadence = (cadenceSel && cadenceSel.value) || 'fast_initial';
        const depth = (depthSel && depthSel.value) || 'standard';
        const pickDirectVerifyHost = () => {
            if (_sshDialogIsIp(host)) return host;
            const methods = Array.isArray(_lastProbeResult?.methods) ? _lastProbeResult.methods : [];
            const reachableSsh = methods.filter(m => (
                m && m.reachable && String(m.method || '').startsWith('ssh_') && m.host
            ));
            const ipRow = reachableSsh.find(m => _sshDialogIsIp(m.host));
            if (ipRow) return String(ipRow.host).trim();
            const hostnameRow = reachableSsh.find(m => {
                const h = String(m.host || '').trim();
                return h && !_sshDialogLooksLikeSerial(h) && !/^kvm/i.test(h);
            });
            return hostnameRow ? String(hostnameRow.host).trim() : host;
        };
        const verifyHost = pickDirectVerifyHost();
        const serialOrKvmHost = _sshDialogLooksLikeSerial(host) || /^kvm/i.test(host);
        if (!_sshDialogIsIp(verifyHost) && serialOrKvmHost && _sshDialogIsGiMode(device)) {
            renderVerifyStatus('warn',
                'GI mode uses serial/KVM console paths; direct SSH verification would wait on the wrong host. Select a reachable method above, or save this console path as offline.',
                [
                    { label: 'Probe again', primary: true, onClick: () => probeAndShowMethods() },
                    { label: 'Save offline', onClick: () => {
                        device.sshConfig = device.sshConfig || {};
                        device.sshConfig._unverifiedSave = true;
                        device.sshConfig._unverifiedReason = 'gi_console_path';
                        device.sshConfig._unverifiedAt = Date.now();
                        device.sshConfig._monitorPolicy = { cadence, discovery_depth: depth };
                        saveAddress();
                    }},
                    { label: 'Edit host', onClick: () => {
                        verifyStatus.style.display = 'none';
                        try { hostInput.focus(); hostInput.select(); } catch (_) {}
                    }},
                ]);
            return;
        }

        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.style.opacity = '0.6';
            saveBtn.style.cursor = 'wait';
        }
        renderVerifyStatus(
            'spinner',
            `Step 1/4: verifying SSH for ${user}@${verifyHost}. Next: register device, persist DB reference, refresh API identity.`
        );

        // Auto-monitor (Phase 2 MVP): prefer the new verify-and-register
        // endpoint that BOTH verifies SSH AND atomically registers the
        // device into the shared monitoring registry. Fallback to legacy
        // verifyCredentials when paired with an older bridge that hasn't
        // shipped /api/devices/verify-and-register yet, so a frontend
        // ahead of backend doesn't break Save. The new response is a
        // SUPERSET of the legacy one, so all the existing branches below
        // (auth_failed / port_closed / ghost_ip / ...) keep working.
        let result = null;
        let bridgeError = null;
        const useAutoMonitor = (typeof ScalerAPI.verifyAndRegister === 'function');
        const verifyToken = _newIdentityToken(host, 'save');
        const verifyDeviceId = _currentApiDeviceId();
        try {
            if (useAutoMonitor) {
                result = await ScalerAPI.verifyAndRegister(verifyDeviceId, verifyHost, user, password, {
                    discoveryDepth: depth,
                    monitorCadence: cadence,
                });
            } else {
                result = await ScalerAPI.verifyCredentials(verifyDeviceId, verifyHost, user, password, {
                    discoveryDepth: depth,
                    monitorCadence: cadence,
                });
            }
        } catch (err) {
            bridgeError = err;
        }

        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.style.opacity = '';
            saveBtn.style.cursor = 'pointer';
        }

        if (!_isIdentityRequestCurrent(verifyToken, hostInput.value.trim())) {
            renderVerifyStatus('warn',
                'Onboarding response ignored because the device SN/host changed while verification was running. Save again to verify the current identity.',
                [
                    { label: 'Verify current SN', primary: true, onClick: () => verifyThenSave() },
                    { label: 'Cancel', onClick: () => { verifyStatus.style.display = 'none'; } },
                ]);
            return;
        }

        if (bridgeError && !result) {
            // Bridge itself failed (5xx, network drop, CORS, ...) -- this
            // is NOT a credential failure. Do not show a green success:
            // backend registration did not happen. The operator can still
            // save an offline hint, but it is explicitly marked unverified.
            renderVerifyStatus('warn',
                `${friendlyBridgeError(bridgeError)} Save as offline/unverified?`,
                [
                    { label: 'Try again', primary: true, onClick: () => verifyThenSave() },
                    { label: 'Save anyway', onClick: () => {
                        device.sshConfig = device.sshConfig || {};
                        device.sshConfig._unverifiedSave = true;
                        device.sshConfig._unverifiedReason = 'bridge_error';
                        device.sshConfig._unverifiedAt = Date.now();
                        saveAddress();
                    }},
                    { label: 'Cancel', onClick: () => { verifyStatus.style.display = 'none'; } },
                ]);
            return;
        }

        const hasBackendRegistration = !!(
            result && (
                result.registered
                || result.newly_registered === false
                || result.key
                || result.registered_device_id
                || result.device_context?.canonical?.key
            )
        );
        if (result && result.ok && useAutoMonitor && !hasBackendRegistration) {
            renderVerifyStatus('error',
                'SSH verified, but backend DB registration did not complete. Nothing was saved as ready-for-APIs.',
                [
                    { label: 'Try again', primary: true, onClick: () => verifyThenSave() },
                    { label: 'Cancel', onClick: () => { verifyStatus.style.display = 'none'; } },
                ]);
            return;
        }

        // Successful verification -- stamp the verified metadata onto
        // sshConfig (cluster identity, monitor policy) and run the
        // legacy persist path. The backend already wrote operational.json,
        // so the in-memory copy stays in sync without an extra fetch.
        if (result && result.ok) {
            const identityCheck = _validateIdentityResult(result, verifyToken, null, host);
            if (!identityCheck.ok) {
                renderVerifyStatus('warn',
                    `${identityCheck.reason} Onboarding data was not applied to this canvas device.`,
                    [
                        { label: 'Edit SN/host', primary: true, onClick: () => {
                            verifyStatus.style.display = 'none';
                            try { hostInput.focus(); hostInput.select(); } catch (_) {}
                        }},
                        { label: 'Try again', onClick: () => verifyThenSave() },
                    ]);
                return;
            }
            device.sshConfig = device.sshConfig || {};
            device.sshConfig._verifiedAt = Date.now();
            device.sshConfig._verifiedReason = 'ok';
            device.sshConfig._monitorPolicy = result.monitor_policy || { cadence, discovery_depth: depth };
            // Drop any prior "unverified" flag -- a successful verify
            // clears the amber badge.
            delete device.sshConfig._unverifiedSave;
            delete device.sshConfig._unverifiedReason;
            delete device.sshConfig._unverifiedAt;

            // Auto-monitor (Phase 2 MVP) -- stamp the device-level flags
            // the toolbar gate now requires (`_sshReachable`) and the
            // shared registry bookkeeping (`_monitorRegistered`,
            // `_monitoredKey`, `_monitoredSubsystems`). Then dispatch
            // `device:context-updated` so the floating canvas toolbar
            // re-renders with the full button set + green-ring SSH icon
            // immediately. Without this dispatch, the toolbar only
            // updates on the next selection toggle. See Section 7 of
            // topology/docs/AUTO_MONITOR_ON_ATTACH.md.
            if (host !== previousIdentityHost) {
                _invalidateForHostChange(host, previousIdentityHost, 'ssh_host_verified');
            }
            device._sshReachable = true;
            device._sshReachableAt = Date.now();
            applyCanonicalOnboardingContext(result);
            if (Array.isArray(result.monitor_started_subsystems)) {
                device._monitoredSubsystems = result.monitor_started_subsystems;
            }
            if (typeof result.references_count_total === 'number') {
                device._monitoredReferenceTotal = result.references_count_total;
            }
            if (typeof result.references_user_count === 'number') {
                device._monitoredReferenceUserCount = result.references_user_count;
            }
            // Stamp cluster identity if the probe filled it in. The
            // existing object-detection sticky-host logic already
            // consumes _activeNccHost / _activeNccIp / _kvmHost.
            if (result.is_cluster) {
                if (result.active_ncc_host) device.sshConfig._activeNccHost = result.active_ncc_host;
                if (result.active_ncc_ip)   device.sshConfig._activeNccIp = result.active_ncc_ip;
                if (result.active_ncc_vm)   device.sshConfig._activeNccVm = result.active_ncc_vm;
                if (result.kvm_host)        device.sshConfig._kvmHost = result.kvm_host;
                if (result.kvm_host_ip)     device.sshConfig._kvmHostIp = result.kvm_host_ip;
                if (Array.isArray(result.ncc_vms) && result.ncc_vms.length) {
                    device.sshConfig._nccVms = result.ncc_vms;
                }
            }
            dispatchContextUpdated('ssh-dialog-verify-and-register');
            const reuseText = result.newly_registered === false
                ? 'Existing DB device reused for this user.'
                : 'Device registered in backend DB.';
            const refText = typeof result.references_user_count === 'number'
                ? ` User references: ${result.references_user_count}.`
                : '';
            const metadataStatus = result.metadata_validation || {};
            const metadataReady = metadataStatus.reliable === true;
            const metadataText = metadataReady
                ? ' Metadata is identity-checked and ready.'
                : ` Metadata is ${metadataStatus.status || 'unknown'}; stale LLDP, stack, and git cache were cleared until a verified refresh succeeds.`;
            const metadataActions = metadataReady ? [] : [
                { label: 'Retry onboarding', primary: true, onClick: () => verifyThenSave() },
                { label: 'Refresh device context', onClick: () => {
                    try {
                        if (window.ObjectDetection && typeof window.ObjectDetection.refreshDeviceContext === 'function') {
                            window.ObjectDetection.refreshDeviceContext(device, { force: true });
                        } else if (editor.objectDetection && typeof editor.objectDetection.refreshDeviceContext === 'function') {
                            editor.objectDetection.refreshDeviceContext(device, { force: true });
                        }
                    } catch (e) {
                        console.warn('[SSH dialog] refresh device context failed:', e);
                    }
                }},
            ];
            renderVerifyStatus(
                metadataReady ? 'success' : 'warn',
                `Step 4/4: API identity ready. ${reuseText}${refText} SSH, config, and discovery will use backend identity ${result.registered_device_id || result.hostname || deviceId}.${metadataText}`,
                metadataActions
            );
            // Tiny delay so the operator actually sees the success
            // banner before the dialog closes.
            setTimeout(() => {
                try { saveAddress({ skipIdentityInvalidation: true }); } catch (e) { console.warn('[SSH dialog] saveAddress threw:', e); }
                setTimeout(showCanvasHostnameMismatchPrompt, 120);
                // Identity-bound metadata is now part of the backend
                // verify-and-register payload. Do not start a separate
                // frontend context hydrate here; that path can resolve by
                // stale canvas/cache labels after the user changes SN/host.
                // Schedule the fast-initial follow-up sweep (only when
                // the operator picked that cadence). The standalone
                // helper handles its own teardown after 3 probes.
                try {
                    if ((cadence === 'fast_initial') &&
                        window.ObjectDetection &&
                        typeof window.ObjectDetection.startFastInitialMonitor === 'function') {
                        window.ObjectDetection.startFastInitialMonitor(device);
                    }
                } catch (_) { /* non-fatal */ }
            }, 350);
            return;
        }

        // Verification failed -- render smart-by-reason actions.
        const reason = (result && result.reason) || 'error';
        const message = (result && result.message) || 'Verification failed.';

        const saveAnyway = (reasonTag) => {
            device.sshConfig = device.sshConfig || {};
            device.sshConfig._unverifiedSave = true;
            device.sshConfig._unverifiedReason = reasonTag;
            device.sshConfig._unverifiedAt = Date.now();
            device.sshConfig._monitorPolicy = { cadence, discovery_depth: depth };
            saveAddress();
        };
        const focusPassword = () => {
            verifyStatus.style.display = 'none';
            try { passInput.focus(); passInput.select(); } catch (_) {}
        };
        const focusHost = () => {
            verifyStatus.style.display = 'none';
            try { hostInput.focus(); hostInput.select(); } catch (_) {}
        };

        if (reason === 'auth_failed') {
            renderVerifyStatus('error', message, [
                { label: 'Edit credentials', primary: true, onClick: focusPassword },
                { label: 'Try again', onClick: () => verifyThenSave() },
            ]);
        } else if (reason === 'port_closed' || reason === 'timeout') {
            renderVerifyStatus('warn', message, [
                { label: 'Try again', primary: true, onClick: () => verifyThenSave() },
                { label: 'Save anyway -- offline', onClick: () => saveAnyway(reason) },
                { label: 'Edit host', onClick: focusHost },
            ]);
        } else if (reason === 'ghost_ip') {
            // The backend already reaped the stale record. Save here
            // means "yes, I know the device moved -- write the new IP
            // into the topology JSON" (with an unverified flag so
            // operator sees the amber badge until next probe confirms).
            renderVerifyStatus('warn', message, [
                { label: 'Save with new identity', primary: true, onClick: () => saveAnyway('ghost_ip_override') },
                { label: 'Edit host', onClick: focusHost },
                { label: 'Cancel', onClick: () => { verifyStatus.style.display = 'none'; } },
            ]);
        } else if (reason === 'identity_mismatch') {
            renderVerifyStatus('warn', message, [
                { label: 'Override', primary: true, onClick: () => saveAnyway('identity_override') },
                { label: 'Cancel', onClick: () => { verifyStatus.style.display = 'none'; } },
            ]);
        } else if (reason === 'generic_prompt') {
            // GI / BASEOS / RECOVERY mode -- the device IS reachable,
            // the operator just needs to acknowledge that the banner
            // wasn't a confirmable hostname. Save anyway is the
            // expected primary action here.
            renderVerifyStatus('warn', message, [
                { label: 'Save anyway -- mode unknown', primary: true, onClick: () => saveAnyway('generic_prompt') },
                { label: 'Try again', onClick: () => verifyThenSave() },
                { label: 'Cancel', onClick: () => { verifyStatus.style.display = 'none'; } },
            ]);
        } else {
            // 'error' or unknown reason
            renderVerifyStatus('error', message, [
                { label: 'Try again', primary: true, onClick: () => verifyThenSave() },
                { label: 'Save anyway', onClick: () => saveAnyway('unknown_error') },
                { label: 'Cancel', onClick: () => { verifyStatus.style.display = 'none'; } },
            ]);
        }
    };

    if (saveBtn) saveBtn.addEventListener('click', verifyThenSave);
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
            verifyThenSave();
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
            if (changed) verifyThenSave();
            else closeDialog();
        }
    };
    setTimeout(() => document.addEventListener('click', handleClickOutside), 100);
}

window.showSSHAddressDialog = showSSHAddressDialog;

// ----------------------------------------------------------------------------
// Ghost-IP handling: when the terminal WS detects the DUT at a given IP
// answers with the wrong hostname it dispatches `ssh:ghost-ip-detected`. We
// drop the cached host on the canvas device so the next SSH click starts
// fresh and the user cannot accidentally dial the ghost IP again.
// ----------------------------------------------------------------------------
(function installGhostIpHandler() {
    if (window._topologyGhostIpHandlerInstalled) return;
    window._topologyGhostIpHandlerInstalled = true;

    window.addEventListener('ssh:ghost-ip-detected', (ev) => {
        try {
            const detail = ev.detail || {};
            const {
                deviceId, ip, expected, actual,
                actorUser, source,
            } = detail;
            const editor = window.topologyEditor || window.editor;
            if (!editor || !editor.objects) return;

            // Remote/broadcast provenance = another user triggered this reap
            // (or we did, on a different tab). Surface it with a toast so the
            // user notices why their cached IP just disappeared.
            const isBroadcast = source === 'broadcast';
            let selfUser = '';
            try {
                const cu = (window.TopologyAuth && window.TopologyAuth.getCurrentUser && window.TopologyAuth.getCurrentUser()) || null;
                selfUser = (cu && cu.username) || '';
            } catch (_) { /* swallow */ }

            const matches = editor.objects.filter(o => {
                if (!o || o.type !== 'device') return false;
                const ids = [o.label, o.deviceSerial, o.serial, o.deviceId, o.id]
                    .map(v => (v || '').toString().trim().toLowerCase())
                    .filter(Boolean);
                if (deviceId && ids.includes(String(deviceId).toLowerCase())) return true;
                if (ip && o.sshConfig && (o.sshConfig.host || '').trim() === ip) return true;
                return false;
            });

            let cleared = 0;
            // The fast path in openTerminalToDevice reads host from many
            // fallback slots: sshConfig.host, _userSavedHost, hostBackup,
            // _enrichedMgmtIp, _nccMgmtIp, deviceAddress, deviceSerial. If
            // the ghost IP is cached in ANY of them, the next SSH click can
            // silently reintroduce it. We nuke every IP-bearing slot that
            // equals the ghost IP, preserving identity fields (serial,
            // label, virshInfo) so cluster recovery still works.
            const ghostIp = (ip || '').trim();
            const ipSlots = [
                'host', '_userSavedHost', 'hostBackup',
                '_enrichedMgmtIp', '_nccMgmtIp',
                '_candidateMgmtIp',
            ];
            matches.forEach(device => {
                if (!device.sshConfig) device.sshConfig = {};
                const before = {};
                let dirty = false;
                ipSlots.forEach(slot => {
                    const v = (device.sshConfig[slot] || '').toString().trim();
                    if (v && (!ghostIp || v === ghostIp)) {
                        before[slot] = v;
                        device.sshConfig[slot] = '';
                        dirty = true;
                    }
                });
                if ((device.deviceAddress || '').toString().trim() &&
                    (!ghostIp || device.deviceAddress === ghostIp)) {
                    before.deviceAddress = device.deviceAddress;
                    device.deviceAddress = '';
                    dirty = true;
                }
                if (dirty) {
                    device.sshConfig._ghostHost = before.host || before._userSavedHost || before.hostBackup || ghostIp || '';
                    device.sshConfig._ghostCleared = before;
                    device.sshConfig._ghostClearedAt = new Date().toISOString();
                    device.sshConfig._ghostActualHostname = actual || '';
                    delete device.sshConfig._lastWorkingMethod;
                    cleared++;
                }
            });

            if (cleared > 0) {
                try { editor.history?.saveState?.(); } catch (_) {}
                try { editor.drawing?.draw?.(); } catch (_) {}
                try { editor.files?.saveToLocalStorage?.(); } catch (_) {}
                console.log(`[SSH] Ghost IP cleared on ${cleared} device(s): ${expected} used to be ${ip}, now ${actual}${actorUser ? ' (by ' + actorUser + ')' : ''}`);

                // Broadcast-origin reap = surface a toast so the user sees
                // "someone else cleaned this up" without needing the console.
                if (isBroadcast && typeof window.showToast === 'function') {
                    const otherUser = actorUser && actorUser !== selfUser && actorUser !== 'system'
                        ? actorUser : '';
                    const target = deviceId || expected || 'device';
                    const msg = otherUser
                        ? `[SHARED] ${otherUser} reaped a ghost IP on ${target}${actual ? ' (was answering as ' + actual + ')' : ''}`
                        : `[INFO] Stale IP cleared on ${target}`;
                    try { window.showToast(msg, 'warning', 6000); } catch (_) { /* swallow */ }
                }
            }
        } catch (err) {
            console.error('[SSH] Failed to process ghost-ip event:', err);
        }
    });
})();

console.log('[topology-ssh-dialog.js] SSH Address Dialog module loaded');
