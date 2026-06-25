// ============================================================================
// TOPOLOGY DEVICE SELECTION TOOLBAR MODULE
// ============================================================================
// Handles the floating device selection toolbar with liquid glass styling.
// Extracted from topology.js to reduce main file size (~340 lines).
//
// Usage:
//   showDeviceSelectionToolbar(editor, device);
//   hideDeviceSelectionToolbar(editor);
// ============================================================================

/**
 * Show the device selection toolbar
 * @param {TopologyEditor} editor - The editor instance
 * @param {object} device - The selected device
 */
function showDeviceSelectionToolbar(editor, device) {
    if (!device || device.type !== 'device') return;
    const safeString = (value) => String(value || '').trim();
    
    // Hide other toolbars
    hideDeviceSelectionToolbar(editor);
    if (editor.hideLinkSelectionToolbar) editor.hideLinkSelectionToolbar();
    if (editor.hideTextSelectionToolbar) editor.hideTextSelectionToolbar();
    if (editor.hideShapeSelectionToolbar) editor.hideShapeSelectionToolbar();
    
    // Calculate screen position of the device
    const rect = editor.canvas.getBoundingClientRect();
    
    const centerScreenX = device.x * editor.zoom + editor.panOffset.x + rect.left;
    const centerScreenY = device.y * editor.zoom + editor.panOffset.y + rect.top;
    
    const deviceRadius = (device.radius || 30) * editor.zoom;
    const toolbarGap = 25;
    const toolbarX = centerScreenX;
    const toolbarY = centerScreenY + deviceRadius + toolbarGap;
    
    // Create the toolbar container - Liquid Glass Style
    const toolbar = document.createElement('div');
    toolbar.id = 'device-selection-toolbar';
    const isDarkMode = editor.darkMode;
    const glassBg = isDarkMode ? 'rgba(15, 15, 25, 0.25)' : 'rgba(255, 255, 255, 0.25)';
    const glassBorder = isDarkMode ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.08)';
    const glassShadow = isDarkMode 
        ? '0 4px 30px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.08)'
        : '0 4px 30px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.5)';
    toolbar.style.cssText = `
        position: fixed;
        left: ${toolbarX}px;
        top: ${toolbarY}px;
        transform: translateX(-50%);
        z-index: 99999;
        background: ${glassBg};
        border: 1px solid ${glassBorder};
        border-radius: 12px;
        padding: 5px 8px;
        box-shadow: ${glassShadow};
        backdrop-filter: blur(24px) saturate(200%);
        -webkit-backdrop-filter: blur(24px) saturate(200%);
        display: flex;
        gap: 2px;
        align-items: center;
        user-select: none;
        -webkit-user-select: none;
        opacity: 0;
        animation: deviceTbFadeIn 0.2s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        overflow: visible;
    `;
    
    // Add CSS animation
    const oldStyle = document.getElementById('device-tb-styles');
    if (oldStyle) oldStyle.remove();
    
    const style = document.createElement('style');
    style.id = 'device-tb-styles';
    style.textContent = `
        @keyframes deviceTbFadeIn {
            from { opacity: 0; transform: translateX(-50%) translateY(5px); }
            to { opacity: 1; transform: translateX(-50%) translateY(0); }
        }
    `;
    document.head.appendChild(style);

    // Connection mode badge row (when GI or RECOVERY)
    const devMode = device._deviceMode || 'unknown';
    // Device mode (GI/RECOVERY) is shown via the SSH button tooltip
    
    if (device._hostnameMismatch && !device._mismatchDismissed) {
        const cfgHost = device._identity?.config_hostname || device._configHostname || '';
        if (cfgHost) {
            const mismatchBar = document.createElement('div');
            mismatchBar.className = 'device-tb-mismatch-bar';
            mismatchBar.style.cssText = `
                display: flex; align-items: center; gap: 6px;
                padding: 5px 10px; margin: -5px -8px 5px -8px;
                border-radius: 8px 8px 0 0;
                background: rgba(142, 68, 173, 0.12);
                border-bottom: 1px solid rgba(142, 68, 173, 0.25);
                font-size: 11px; cursor: pointer;
                color: ${isDarkMode ? 'rgba(255,255,255,0.75)' : 'rgba(30,30,50,0.75)'};
            `;
            mismatchBar.innerHTML = `
                <span style="color:#8e44ad;font-weight:700;font-size:13px;">!</span>
                <span>Name mismatch: <strong style="color:#8e44ad;">${cfgHost}</strong> on device</span>
            `;
            mismatchBar.onclick = (e) => {
                e.stopPropagation();
                e.stopImmediatePropagation();
                hideDeviceSelectionToolbar(editor);
                editor.selectedObject = null;
                editor.selectedObjects = [];
                if (window.CanvasDrawing?._showMismatchPopup) {
                    const pos = editor.worldToScreen({ x: device.x, y: device.y });
                    window.CanvasDrawing._showMismatchPopup(editor, device, pos.x + 30, pos.y - 20);
                }
            };
            toolbar.appendChild(mismatchBar);
        }
    }
    
    // Helper to create toolbar buttons
    const createButton = (iconId, title, onClick, options = {}) => {
        const { isDestructive = false, color = null, strongAction = false, actionLabel = '' } = options;
        const btn = document.createElement('button');
        btn.className = strongAction ? 'device-tb-btn device-tb-btn-strong' : 'device-tb-btn';
        
        const isPillButton = color && (color === '#27ae60' || color === '#e74c3c');
        const iconColor = isPillButton 
            ? '#ffffff'
            : (strongAction
                ? '#ffffff'
                : (isDestructive
                    ? 'rgba(255, 100, 100, 0.9)'
                    : (isDarkMode ? 'rgba(255, 255, 255, 0.85)' : 'rgba(30, 30, 50, 0.85)')));
        
        let iconMarkup = '';
        try {
            iconMarkup = editor._createIconSvg
                ? editor._createIconSvg(iconId, 16, isPillButton ? '#ffffff' : color)
                : '●';
        } catch (err) {
            console.warn('[device-toolbar] icon render failed:', iconId, err?.message || err);
            iconMarkup = '<span style="font-size:14px;line-height:1;">?</span>';
        }
        btn.innerHTML = `${iconMarkup}`;
        
        const hoverBg = strongAction
            ? 'linear-gradient(135deg, #0891b2, #0066FA)'
            : isPillButton
            ? (color === '#27ae60' ? '#229954' : '#c0392b')
            : (isDarkMode ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.08)');
        const hoverColor = isPillButton 
            ? '#ffffff'
            : (isDestructive ? '#ff6b6b' : (isDarkMode ? '#fff' : '#1a1a2e'));
        
        const baseBg = strongAction
            ? 'linear-gradient(135deg, #00B4D8, #0066FA)'
            : (isPillButton ? color : 'transparent');
        
        btn.style.cssText = `
            position: relative;
            ${isPillButton || strongAction ? 'width: auto; padding: 0 10px;' : 'width: 30px;'}
            height: 30px;
            border: ${strongAction ? '1px solid rgba(255,255,255,0.34)' : 'none'};
            background: ${baseBg};
            color: ${iconColor};
            cursor: pointer;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
            transition: all 0.12s ease;
            overflow: visible;
            user-select: none;
            -webkit-user-select: none;
            ${isPillButton || strongAction ? 'font-size: 11px; font-weight: 800; letter-spacing: .2px;' : ''}
            ${strongAction ? 'box-shadow: 0 5px 14px rgba(0, 102, 250, 0.28), inset 0 1px 0 rgba(255,255,255,0.35);' : ''}
        `;
        
        if ((isPillButton || strongAction) && title) {
            let pillIcon = '';
            try {
                pillIcon = editor._createIconSvg ? editor._createIconSvg(iconId, 14, '#ffffff') : '●';
            } catch (_) {
                pillIcon = '<span style="font-size:12px;line-height:1;">?</span>';
            }
            const label = actionLabel || title.replace('Enable ', '').replace(' Retry', '');
            btn.innerHTML = `${pillIcon}<span style="color: white;">${label}</span>`;
        }
        
        btn.onmouseenter = () => {
            btn.style.background = hoverBg;
            if (!isPillButton) btn.style.color = hoverColor;
            btn.style.transform = 'scale(1.08)';
            if (!isPillButton && editor._showToolbarTooltip) editor._showToolbarTooltip(btn, title);
        };
        btn.onmouseleave = () => {
            btn.style.background = baseBg;
            if (!isPillButton) btn.style.color = iconColor;
            btn.style.transform = 'scale(1)';
            if (!isPillButton && editor._hideToolbarTooltip) editor._hideToolbarTooltip();
        };
        btn.onmousedown = (e) => {
            e.stopPropagation();
            e.preventDefault();
        };
        btn.onclick = (e) => {
            e.stopPropagation();
            e.preventDefault();
            try {
                onClick(e);
            } catch (err) {
                console.error('[device-toolbar] button action failed:', title, err);
                if (editor.showToast) editor.showToast(`${title || 'Toolbar action'} unavailable: ${err.message || err}`, 'error');
            }
        };
        return btn;
    };
    
    const createSeparator = () => {
        const sep = document.createElement('div');
        const sepColor = isDarkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.12)';
        sep.style.cssText = `width: 1px; height: 18px; background: ${sepColor}; margin: 0 4px;`;
        return sep;
    };

    // Layer widget: badge + dropdown (submenu style, like LLDP/System Stack)
    const createLayerWidget = (obj, refreshToolbar) => {
        const widget = document.createElement('div');
        widget.className = 'layer-widget';
        widget.style.cssText = 'display: inline-flex; align-items: center; gap: 1px;';
        const badgeColor = isDarkMode ? 'rgba(255,255,255,0.85)' : 'rgba(30,30,50,0.85)';
        const badgeBg = isDarkMode ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.08)';
        const badgeBorder = isDarkMode ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.12)';
        const updateBadge = () => {
            badge.textContent = editor.getObjectLayer ? editor.getObjectLayer(obj) : 20;
        };
        const applyLayerAction = (fn) => {
            if (!editor[fn] || !obj) return;
            editor.saveState && editor.saveState();
            editor[fn](obj);
            editor.draw && editor.draw();
            updateBadge();
            if (refreshToolbar) setTimeout(refreshToolbar, 50);
        };
        const badge = document.createElement('button');
        badge.className = 'layer-badge';
        badge.style.cssText = `min-width: 28px; height: 24px; padding: 0 6px; border: 1px solid ${badgeBorder}; background: ${badgeBg}; color: ${badgeColor}; font-size: 11px; font-family: monospace; font-weight: 600; cursor: pointer; border-radius: 6px; display: flex; align-items: center; justify-content: center;`;
        updateBadge();
        badge.onmousedown = (e) => { e.stopPropagation(); e.preventDefault(); };
        let dropdown = null;
        const glassBgDrop = isDarkMode ? 'rgba(15, 15, 25, 0.85)' : 'rgba(255, 255, 255, 0.92)';
        const glassBorderDrop = isDarkMode ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.08)';
        const glassShadowDrop = isDarkMode
            ? '0 4px 30px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.08)'
            : '0 4px 30px rgba(0, 0, 0, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.5)';
        const items = [
            { label: 'Bring to Front', fn: 'moveObjectToFront' },
            { label: 'Move Forward', fn: 'moveObjectForward' },
            { label: 'Move Backward', fn: 'moveObjectBackward' },
            { label: 'Send to Back', fn: 'moveObjectToBack' },
            null,
            { label: 'Reset to Default', fn: 'resetObjectLayer' }
        ];
        const closeDropdown = () => {
            if (dropdown) { dropdown.remove(); dropdown = null; }
            document.removeEventListener('mousedown', outsideClick);
        };
        const outsideClick = (e) => {
            if (dropdown && !dropdown.contains(e.target) && e.target !== badge) closeDropdown();
        };
        badge.onclick = (e) => {
            e.stopPropagation();
            e.preventDefault();
            if (dropdown) { closeDropdown(); return; }
            if (window.SelectionPopups?.closeObjectToolbarPopups) {
                window.SelectionPopups.closeObjectToolbarPopups(editor, 'device-layer-dropdown');
            }
            dropdown = document.createElement('div');
            dropdown.id = 'device-layer-dropdown';
            dropdown.style.cssText = `
                position: fixed; z-index: 100002; min-width: 160px;
                background: ${glassBgDrop}; border: 1px solid ${glassBorderDrop};
                border-radius: 10px; padding: 4px 0;
                box-shadow: ${glassShadowDrop};
                backdrop-filter: blur(24px) saturate(200%);
                -webkit-backdrop-filter: blur(24px) saturate(200%);
            `;
            items.forEach((item) => {
                if (!item) {
                    const sep = document.createElement('div');
                    sep.style.cssText = `height: 1px; background: ${isDarkMode ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)'}; margin: 4px 6px;`;
                    dropdown.appendChild(sep);
                    return;
                }
                const div = document.createElement('div');
                div.style.cssText = `padding: 6px 12px; cursor: pointer; font-size: 12px; border-radius: 6px; margin: 0 4px; color: ${badgeColor};`;
                div.textContent = item.label;
                div.onmouseenter = () => { div.style.background = isDarkMode ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.06)'; };
                div.onmouseleave = () => { div.style.background = 'transparent'; };
                div.onmousedown = (e) => { e.stopPropagation(); e.preventDefault(); };
                div.onclick = (ev) => {
                    ev.stopPropagation(); ev.preventDefault();
                    applyLayerAction(item.fn);
                    closeDropdown();
                };
                dropdown.appendChild(div);
            });
            document.body.appendChild(dropdown);
            const r = badge.getBoundingClientRect();
            dropdown.style.left = `${r.left + r.width / 2 - 80}px`;
            dropdown.style.top = `${r.bottom + 6}px`;
            setTimeout(() => document.addEventListener('mousedown', outsideClick), 10);
        };
        const wrap = document.createElement('div');
        wrap.style.cssText = 'position: relative; display: inline-flex; align-items: center;';
        wrap.appendChild(badge);
        widget.appendChild(wrap);
        badge.onmouseenter = () => { badge.style.background = isDarkMode ? 'rgba(255,255,255,0.18)' : 'rgba(0,0,0,0.1)'; if (editor._showToolbarTooltip) editor._showToolbarTooltip(badge, 'Layer (click for menu)'); };
        badge.onmouseleave = () => { badge.style.background = badgeBg; if (editor._hideToolbarTooltip) editor._hideToolbarTooltip(); };
        return widget;
    };
    
    // === DEVICE TOOLBAR BUTTONS ===
    // Group 1: Identity — Rename, SSH, LLDP
    
    // Rename button
    toolbar.appendChild(createButton('edit', 'Rename', () => {
        if (editor.showInlineDeviceRename) editor.showInlineDeviceRename(device);
    }));
    
    // SSH/Console button: click=open SSH dialog with connection methods and Connect buttons
    const sshConfig = device.sshConfig || {};
    const pickedTarget = (window.TopologySshTarget && window.TopologySshTarget.pick)
        ? window.TopologySshTarget.pick(device, { sshConfig })
        : { host: sshConfig.host || device.deviceAddress || '', source: '' };
    const sshHost = pickedTarget.host || sshConfig.host || device.deviceAddress;
    const deviceMode = device._deviceMode || 'unknown';
    const isModeAlert = deviceMode === 'GI' || deviceMode === 'RECOVERY';
    const lastMethod = sshConfig._lastWorkingMethod || '';
    const isConsoleMode = lastMethod === 'console' || lastMethod === 'virsh_console' || isModeAlert;
    const connIcon = isConsoleMode ? 'console' : 'terminal';
    const connLabel = isConsoleMode ? 'Console' : 'SSH';
    const hasSshConfigured = !!sshHost;
    const SSH_FRESH_MS = 10 * 60 * 1000;
    const SSH_STALE_MS = 2 * 60 * 60 * 1000;
    const _sshReachAt = device._sshReachableAt || 0;
    const _ageMs = _sshReachAt ? (Date.now() - _sshReachAt) : Infinity;
    const sshReachable = !!device._sshReachable && _ageMs <= SSH_FRESH_MS;
    const sshReachableStale = !!device._sshReachable && _ageMs > SSH_FRESH_MS && _ageMs <= SSH_STALE_MS;
    const sshReachableExpired = !!device._sshReachable && _ageMs > SSH_STALE_MS;
    const _reachStr = sshReachable ? ' [OK]'
        : sshReachableStale ? ' [stale]'
        : sshReachableExpired ? ' [unknown]'
        : '';
    const sshTitle = isModeAlert
        ? `${device.label || 'Device'} in ${deviceMode} mode. Click for connection settings.`
        : (hasSshConfigured
            ? `${connLabel}: ${sshConfig.user || 'dnroot'}@${sshHost}${_reachStr} -- Click for connection settings.`
            : 'No SSH configured. Click to set credentials.');
    const sshBtn = createButton(connIcon, sshTitle, (e) => {
        if (device._upgradeInProgress) return;
        hideDeviceSelectionToolbar(editor);
        if (editor.showSSHAddressDialog) editor.showSSHAddressDialog(device);
    });
    if (device._upgradeInProgress) {
        sshBtn.style.opacity = '0.35';
        sshBtn.style.pointerEvents = 'none';
        sshBtn.title = 'Unavailable during upgrade';
    }
    if (sshReachable) {
        sshBtn.style.boxShadow = 'inset 0 0 0 2px #27ae60';
    } else if (sshReachableStale) {
        sshBtn.style.boxShadow = 'inset 0 0 0 2px #f39c12';
    }
    if (isModeAlert) {
        const sshWrap = document.createElement('div');
        sshWrap.style.cssText = 'position: relative; display: inline-flex;';
        sshWrap.appendChild(sshBtn);
        const badge = document.createElement('span');
        badge.style.cssText = `position: absolute; top: -2px; right: -2px; width: 8px; height: 8px;
            background: ${deviceMode === 'RECOVERY' ? '#e74c3c' : '#f39c12'}; border-radius: 50%;
            border: 2px solid ${isDarkMode ? '#1a202c' : '#ffffff'};`;
        badge.title = sshTitle;
        sshWrap.appendChild(badge);
        toolbar.appendChild(sshWrap);
    } else {
        toolbar.appendChild(sshBtn);
    }
    
    // LLDP button + System Stack button gate.
    //
    // Auto-monitor (Phase 2 MVP, OQ-7 = SHIP): tighten the gate from
    // "credentials present" to "credentials present AND verified
    // reachable". A typed-but-unverified credential set should NOT
    // surface buttons that need a live SSH session -- otherwise the
    // user clicks LLDP / Stack on an unreachable device, the
    // background fetch fails 30s later, and the UI feels broken.
    //
    // ``_legacyAlwaysOn`` returns true for devices loaded from a
    // section JSON that lacks the new ``_sshReachable`` flag (PE-1 /
    // PE-4 / RR-SA-2 / DNAAS-* baselines). The smooth-ZTP hydrate in
    // ``topology-devices.js`` populates ``_sshReachable=true`` for
    // these from the registry's ``last_seen_ok`` BEFORE the first
    // toolbar paint, so this fallback is only a defense-in-depth.
    const _legacyAlwaysOn = (d) => {
        // Devices that pre-date the new flag have NEITHER _sshReachable
        // NOR _monitorRegistered set. Anything that came through the
        // new verify-and-register path will have _monitorRegistered and
        // we should defer to _sshReachable. Otherwise (no registry
        // mention at all) treat as a legacy load and keep the old
        // permissive behaviour so PE-1's toolbar doesn't regress.
        return !d._monitorRegistered && (d._sshReachable === undefined);
    };
    const hasSshCredentials = !!(sshConfig && (sshConfig.host || device._registeredMgmtIp || device._registeredDeviceId) && sshConfig.user && sshConfig.password);
    const isReachable = !!device._sshReachable || _legacyAlwaysOn(device);
    const hasBackendIdentity = !!(device._monitorRegistered && (device._registeredMgmtIp || device._registeredDeviceId || device._monitoredKey));
    const onboardingPhase = safeString(device._onboardingPhase || device._onboarding?.phase);
    const isOnboarding = !!onboardingPhase && onboardingPhase !== 'api_ready' && onboardingPhase !== 'failed';
    const metadataGuard = window.TopologyDeviceIdentity || null;
    const resolvedIdentity = metadataGuard?.resolveIdentity
        ? metadataGuard.resolveIdentity(device, { host: pickedTarget.host })
        : null;
    const metadataHostHint = resolvedIdentity?.host || pickedTarget.host || device._registeredMgmtIp || device._registeredDeviceId || device.deviceSerial || device.serial || device.label || '';
    const hasKnownMetadataIdentity = metadataGuard?.hasKnownMetadataIdentity
        ? metadataGuard.hasKnownMetadataIdentity(device, { host: metadataHostHint })
        : !!(
            hasBackendIdentity
            || device._monitorContext
            || device._monitorCapabilities
            || device._metadataDiscovered
        );
    const canShowMetadataActions = hasKnownMetadataIdentity || (hasSshCredentials && (isReachable || hasBackendIdentity || isOnboarding));
    if (canShowMetadataActions) {
        const serial = resolvedIdentity?.deviceId || pickedTarget.host || device._registeredMgmtIp || device._registeredDeviceId || device._monitoredKey || device.deviceSerial || device.label || '';
        const metadataHost = resolvedIdentity?.host || pickedTarget.host || device._registeredMgmtIp || serial;
        const metadataDeviceId = resolvedIdentity?.deviceId || device._registeredDeviceId || device._registeredHostname || device._monitoredKey || device.deviceSerial || device.serial || serial;
        const metadataState = (kind, data = null) => metadataGuard?.metadataState
            ? metadataGuard.metadataState(device, kind, { host: metadataHost, deviceId: metadataDeviceId, data })
            : { ready: true, loading: false, status: 'ready' };
        const lldpRows = (window.LldpDialog?._sanitizeLldpNeighbors)
            ? window.LldpDialog._sanitizeLldpNeighbors(device._lldpData?.neighbors || device._lldpData?.lldp_neighbors || [])
            : (device._lldpData?.neighbors || []);
        const lldpReadyState = metadataState('lldp', device._lldpData);
        const stackReadyState = metadataState('stack', device._stackData);
        const gitReadyState = metadataState('git');
        const lldpReady = lldpReadyState.ready && (lldpRows.length || device._lldpData?.raw_output);
        const stackReady = stackReadyState.ready && !!(device._stackData?.components?.length || device._stackData?.raw_output);
        const gitReady = gitReadyState.ready && device._gitCommit !== undefined && device._gitCommit !== null && device._gitCommit !== '';
        const metadataLoading = lldpReadyState.loading || stackReadyState.loading || gitReadyState.loading || isOnboarding;
        const disabledMetaTitle = metadataLoading
            ? 'Device metadata is loading. Try again after discovery finishes.'
            : (hasKnownMetadataIdentity
                ? 'Device metadata is not available yet. Waiting for backend context or cached monitor data.'
                : 'Not discovered yet. Run probe/discover before opening device metadata.');
        const applyMetadataDisabled = (btn, title = disabledMetaTitle) => {
            btn.style.opacity = '0.42';
            btn.style.cursor = 'not-allowed';
            btn.style.color = isDarkMode ? 'rgba(190, 195, 205, 0.55)' : 'rgba(90, 95, 105, 0.55)';
            btn.style.background = isDarkMode ? 'rgba(120, 130, 145, 0.08)' : 'rgba(0, 0, 0, 0.05)';
            btn.title = title;
        };
        const showMetadataPending = () => {
            if (editor.showToast) editor.showToast(disabledMetaTitle, 'info');
        };
        const isLldpRunning = device._lldpRunning || device._lldpAnimating;
        const hasLldpData = device.lldpEnabled || device.lldpDiscoveryComplete;
        const hasNewResults = device._lldpNewResults;
        const lldpCompletedAt = device._lldpCompletedAt;
        
        const defaultIconColor = isDarkMode ? 'rgba(255, 255, 255, 0.85)' : 'rgba(30, 30, 50, 0.85)';
        const defaultHoverBg = isDarkMode ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.08)';
        
        if (!document.getElementById('lldp-spin-style')) {
            const lldpStyle = document.createElement('style');
            lldpStyle.id = 'lldp-spin-style';
            lldpStyle.textContent = `@keyframes lldpSpin { to { transform: rotate(360deg); } }`;
            document.head.appendChild(lldpStyle);
        }
        
        let lldpColor = defaultIconColor;
        let lldpBg = 'transparent';
        let indicatorHtml = '';
        let tooltipText = 'LLDP';
        
        if (isLldpRunning) {
            lldpColor = '#00B4D8';
            lldpBg = 'rgba(0, 180, 216, 0.15)';
            tooltipText = 'LLDP scanning...';
            indicatorHtml = `<span style="position:absolute;top:-2px;right:-2px;width:10px;height:10px;border:2px solid rgba(0, 180, 216, 0.3);border-top-color:#00B4D8;border-radius:50%;animation:lldpSpin 0.8s linear infinite;"></span>`;
        } else if (!lldpReady && !hasKnownMetadataIdentity) {
            lldpColor = isDarkMode ? 'rgba(190, 195, 205, 0.55)' : 'rgba(90, 95, 105, 0.55)';
            lldpBg = isDarkMode ? 'rgba(120, 130, 145, 0.08)' : 'rgba(0, 0, 0, 0.05)';
            tooltipText = disabledMetaTitle;
        } else if (!lldpReady) {
            tooltipText = 'LLDP Table (loads current device data)';
        } else if (hasNewResults) {
            lldpColor = '#27ae60';
            lldpBg = 'rgba(39, 174, 96, 0.15)';
            tooltipText = lldpCompletedAt
                ? `LLDP scan done (${new Date(lldpCompletedAt).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })})`
                : 'LLDP scan done';
            indicatorHtml = `<span style="position:absolute;top:-2px;right:-2px;width:8px;height:8px;background:#27ae60;border-radius:50%;border:2px solid ${isDarkMode ? '#1a202c' : '#ffffff'};"></span>`;
        }
        
        const lldpBtn = document.createElement('button');
        lldpBtn.style.cssText = `
            width: 28px; height: 28px; padding: 0; border: none;
            background: ${lldpBg}; border-radius: 6px; cursor: pointer;
            color: ${lldpColor}; display: flex; align-items: center;
            justify-content: center; transition: all 0.12s ease; position: relative;
        `;
        lldpBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"/>
                <path d="M7.76 7.76a6 6 0 0 1 8.48 0"/>
                <path d="M7.76 16.24a6 6 0 0 0 8.48 0"/>
            </svg>
            ${indicatorHtml}
        `;
        lldpBtn.onmouseenter = () => {
            lldpBtn.style.background = !lldpReady && !isLldpRunning && !hasKnownMetadataIdentity ? lldpBg : (hasNewResults ? 'rgba(39, 174, 96, 0.25)' : (isLldpRunning ? 'rgba(0, 180, 216, 0.25)' : defaultHoverBg));
            lldpBtn.style.transform = !lldpReady && !isLldpRunning && !hasKnownMetadataIdentity ? 'none' : 'scale(1.08)';
            if (editor._showToolbarTooltip) editor._showToolbarTooltip(lldpBtn, tooltipText);
        };
        lldpBtn.onmouseleave = () => {
            lldpBtn.style.background = lldpBg;
            lldpBtn.style.transform = 'scale(1)';
            if (editor._hideToolbarTooltip) editor._hideToolbarTooltip();
        };
        lldpBtn.onmousedown = (e) => { e.stopPropagation(); e.preventDefault(); };
        lldpBtn.onclick = (e) => {
            e.stopPropagation();
            e.preventDefault();
            if (device._upgradeInProgress) return;
            if (!lldpReady && !isLldpRunning && !hasKnownMetadataIdentity) {
                showMetadataPending();
                return;
            }
            if (editor._showLldpInlineSubmenu) {
                editor._showLldpInlineSubmenu(lldpBtn, device, serial, sshConfig, toolbar, isDarkMode, defaultIconColor, defaultHoverBg);
            }
        };
        if (device._upgradeInProgress) {
            lldpBtn.style.opacity = '0.35';
            lldpBtn.style.pointerEvents = 'none';
            lldpBtn.title = 'Unavailable during upgrade';
        } else if (!lldpReady && !isLldpRunning && !hasKnownMetadataIdentity) {
            applyMetadataDisabled(lldpBtn);
        }
        toolbar.appendChild(lldpBtn);
        
        // System Stack button (opens submenu with Stack Table + Git Commit)
        const stackBtn = createButton('layers', 'System Stack', () => {
            if (device._upgradeInProgress) return;
            if (!stackReady && !gitReady && !hasKnownMetadataIdentity) {
                showMetadataPending();
                return;
            }
            if (editor._showSystemStackInlineSubmenu) {
                editor._showSystemStackInlineSubmenu(stackBtn, device, serial, sshConfig, toolbar, isDarkMode, defaultIconColor, defaultHoverBg);
            }
        });
        if (device._upgradeInProgress) {
            stackBtn.style.opacity = '0.35';
            stackBtn.style.pointerEvents = 'none';
            stackBtn.title = 'Unavailable during upgrade';
        } else if (!stackReady && !gitReady && !hasKnownMetadataIdentity) {
            applyMetadataDisabled(stackBtn);
        }
        toolbar.appendChild(stackBtn);
    } else if (device._monitorRegistered || isOnboarding) {
        const pendingBtn = createButton('layers', 'Monitoring options are preparing from backend identity', () => {
            if (editor.showToast) editor.showToast('Device monitoring is still preparing. Try again in a few seconds.', 'info');
        });
        pendingBtn.style.opacity = '0.55';
        pendingBtn.title = 'Monitoring options are preparing';
        toolbar.appendChild(pendingBtn);
    }
    
    toolbar.appendChild(createSeparator());
    
    // Group 2: Appearance — Style, Color, Label Style
    
    toolbar.appendChild(createButton('router', 'Style', () => {
        if (editor.showDeviceStylePalette) editor.showDeviceStylePalette(device);
    }));
    
    toolbar.appendChild(createButton('palette', 'Color', () => {
        if (editor.showColorPalettePopupFromToolbar) editor.showColorPalettePopupFromToolbar(device, 'device', toolbar);
    }));
    
    toolbar.appendChild(createButton('text', 'Label Style', () => {
        if (editor.showDeviceLabelStyleMenu) editor.showDeviceLabelStyleMenu(device, toolbar);
    }));
    
    toolbar.appendChild(createSeparator());
    
    // Group 3: Actions — Duplicate, Copy Style, Lock
    
    toolbar.appendChild(createButton('copy', 'Duplicate', () => {
        hideDeviceSelectionToolbar(editor);
        if (editor.duplicateObject) editor.duplicateObject(device, false);
    }));
    
    toolbar.appendChild(createButton('brush', 'Copy Style', () => {
        hideDeviceSelectionToolbar(editor);
        if (editor.copyObjectStyle) editor.copyObjectStyle(device);
        if (editor.showToast) editor.showToast('Style copied — click another device to paste', 'success');
    }));
    
    const isLocked = device.locked || false;
    toolbar.appendChild(createButton(isLocked ? 'lock' : 'unlock', isLocked ? 'Unlock' : 'Lock', () => {
        device.locked = !device.locked;
        if (editor.saveState) editor.saveState();
        if (editor.draw) editor.draw();
        if (editor.showToast) editor.showToast(device.locked ? 'Device locked' : 'Device unlocked', 'info');
        setTimeout(() => showDeviceSelectionToolbar(editor, device), 50);
    }));
    
    toolbar.appendChild(createLayerWidget(device, () => showDeviceSelectionToolbar(editor, device)));

    // Groups button: opens the canonical Groups panel from
    // ``topology-groups-panel.js`` (the floating panel anchored to the
    // top-bar `#btn-groups-panel` id and the keyboard shortcut `g`).
    //
    // History (2026-05-12 fix): this button used to open the per-object
    // ``ObjectGroupPopover.toggleFor(editor, anchorEl)`` micro-popover --
    // a quick add/remove menu attached to the toolbar. The user reported
    // the device-toolbar Groups button "does NOT open the regular Groups
    // panel" and asked for it to route to the canonical panel that the
    // rest of the app uses (top-bar shortcut + sidebar entry). We
    // delegate straight to ``GroupsPanel.toggle`` so a single click
    // opens the same draggable, resizable floating panel that the
    // top-bar button opens. The ObjectGroupPopover surface is preserved
    // for shape/link/text toolbars (out of scope for this fix), and is
    // also still reachable from keyboard shortcut workflows.
    if (window.GroupsPanel) {
        const groupBtn = createButton('group', 'Groups', () => {
            try {
                window.GroupsPanel.toggle(editor);
            } catch (err) {
                console.error('[device-toolbar] Failed to toggle Groups panel:', err);
                if (editor.showToast) {
                    editor.showToast('Groups panel failed to open. Check console.', 'error');
                }
            }
        }, { strongAction: true, actionLabel: 'Groups' });
        groupBtn.setAttribute('aria-label', 'Open Groups panel');
        groupBtn.setAttribute('title', 'Groups panel');
        toolbar.appendChild(groupBtn);
    }
    
    toolbar.appendChild(createSeparator());
    
    // Group 4: Destructive — Delete
    
    toolbar.appendChild(createButton('trash', 'Delete', () => {
        hideDeviceSelectionToolbar(editor);
        if (editor.deleteSelected) editor.deleteSelected();
    }, { isDestructive: true }));
    
    // Prevent ALL events from propagating to canvas/keyboard handler
    toolbar.addEventListener('mousedown', (e) => {
        e.stopPropagation();
        e.preventDefault();
    });
    toolbar.addEventListener('click', (e) => {
        e.stopPropagation();
        e.preventDefault();
    });
    toolbar.addEventListener('keydown', (e) => { e.stopPropagation(); });
    toolbar.addEventListener('keyup', (e) => { e.stopPropagation(); });
    
    document.body.appendChild(toolbar);
    editor._deviceSelectionToolbar = toolbar;
    editor._deviceSelectionToolbarTarget = device;
    const deviceId = device.label || device.deviceSerial || device.serial || '';
    const refreshOnContext = (e) => {
        const d = e.detail?.device;
        if (!d || (d.label !== deviceId && d.deviceSerial !== deviceId && d.serial !== deviceId)) return;
        if (editor._deviceContextRefreshHandler) {
            window.removeEventListener('device:context-updated', editor._deviceContextRefreshHandler);
            editor._deviceContextRefreshHandler = null;
        }
        try {
            hideDeviceSelectionToolbar(editor);
            showDeviceSelectionToolbar(editor, d);
        } catch (err) {
            console.error('[device-toolbar] context refresh failed:', err);
            if (editor.showToast) editor.showToast(`Device toolbar is waiting for backend context: ${err.message || err}`, 'warning');
        }
    };
    editor._deviceContextRefreshHandler = refreshOnContext;
    window.addEventListener('device:context-updated', refreshOnContext);
    
    // Keep toolbar within viewport
    requestAnimationFrame(() => {
        const toolbarRect = toolbar.getBoundingClientRect();
        if (toolbarRect.right > window.innerWidth - 10) {
            toolbar.style.left = `${window.innerWidth - toolbarRect.width / 2 - 10}px`;
        }
        if (toolbarRect.bottom > window.innerHeight - 10) {
            toolbar.style.top = `${toolbarY - deviceRadius - toolbarGap - toolbarRect.height - 10}px`;
        }
    });
}

/**
 * Hide the device selection toolbar
 * @param {TopologyEditor} editor - The editor instance
 */
function hideDeviceSelectionToolbar(editor) {
    if (editor._deviceContextRefreshHandler) {
        window.removeEventListener('device:context-updated', editor._deviceContextRefreshHandler);
        editor._deviceContextRefreshHandler = null;
    }
    if (editor._deviceSelectionToolbar) {
        editor._deviceSelectionToolbar.remove();
        editor._deviceSelectionToolbar = null;
        editor._deviceSelectionToolbarTarget = null;
    }
    const orphaned = document.getElementById('device-selection-toolbar');
    if (orphaned) orphaned.remove();
    if (editor._hideToolbarTooltip) editor._hideToolbarTooltip();
    const stylePalette = document.getElementById('device-style-palette-popup');
    if (stylePalette) stylePalette.remove();
    const labelStyleMenu = document.getElementById('device-label-style-menu');
    if (labelStyleMenu) labelStyleMenu.remove();
    if (window.SelectionPopups?.closeObjectToolbarPopups) {
        window.SelectionPopups.closeObjectToolbarPopups(editor);
    }
}

// Export functions
window.showDeviceSelectionToolbar = showDeviceSelectionToolbar;
window.hideDeviceSelectionToolbar = hideDeviceSelectionToolbar;

console.log('[topology-device-toolbar.js] Device selection toolbar module loaded');
