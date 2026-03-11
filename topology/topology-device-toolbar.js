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
    
    // Helper to create toolbar buttons
    const createButton = (iconId, title, onClick, options = {}) => {
        const { isDestructive = false, color = null } = options;
        const btn = document.createElement('button');
        btn.className = 'device-tb-btn';
        
        const isPillButton = color && (color === '#27ae60' || color === '#e74c3c');
        const iconColor = isPillButton 
            ? '#ffffff'
            : (isDestructive 
                ? 'rgba(255, 100, 100, 0.9)' 
                : (isDarkMode ? 'rgba(255, 255, 255, 0.85)' : 'rgba(30, 30, 50, 0.85)'));
        
        btn.innerHTML = `${editor._createIconSvg ? editor._createIconSvg(iconId, 16, isPillButton ? '#ffffff' : color) : '●'}`;
        
        const hoverBg = isPillButton 
            ? (color === '#27ae60' ? '#229954' : '#c0392b')
            : (isDarkMode ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.08)');
        const hoverColor = isPillButton 
            ? '#ffffff'
            : (isDestructive ? '#ff6b6b' : (isDarkMode ? '#fff' : '#1a1a2e'));
        
        const baseBg = isPillButton ? color : 'transparent';
        
        btn.style.cssText = `
            position: relative;
            ${isPillButton ? 'width: auto; padding: 0 10px;' : 'width: 30px;'}
            height: 30px;
            border: none;
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
            ${isPillButton ? 'font-size: 11px; font-weight: 600;' : ''}
        `;
        
        if (isPillButton && title) {
            btn.innerHTML = `${editor._createIconSvg ? editor._createIconSvg(iconId, 14, '#ffffff') : '●'}<span style="color: white;">${title.replace('Enable ', '').replace(' Retry', '')}</span>`;
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
            onClick();
        };
        return btn;
    };
    
    const createSeparator = () => {
        const sep = document.createElement('div');
        const sepColor = isDarkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.12)';
        sep.style.cssText = `width: 1px; height: 18px; background: ${sepColor}; margin: 0 4px;`;
        return sep;
    };
    
    // === DEVICE TOOLBAR BUTTONS ===
    // Group 1: Identity — Rename, SSH, LLDP
    
    // Rename button
    toolbar.appendChild(createButton('edit', 'Rename', () => {
        if (editor.showInlineDeviceRename) editor.showInlineDeviceRename(device);
    }));
    
    // SSH button
    const sshConfig = device.sshConfig || {};
    const sshHost = sshConfig.host || device.deviceAddress;
    const sshTitle = sshHost ? `SSH: ${sshConfig.user || 'dnroot'}@${sshHost}` : 'Set SSH';
    toolbar.appendChild(createButton('terminal', sshTitle, () => {
        hideDeviceSelectionToolbar(editor);
        if (editor.handleContextSSHAddress) editor.handleContextSSHAddress();
    }));
    
    // LLDP button - only show if SSH credentials configured
    const hasSshCredentials = sshConfig && sshConfig.host && sshConfig.user && sshConfig.password;
    if (hasSshCredentials) {
        const serial = sshConfig.host || device.deviceSerial || device.label || '';
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
            lldpBtn.style.background = hasNewResults ? 'rgba(39, 174, 96, 0.25)' : (isLldpRunning ? 'rgba(0, 180, 216, 0.25)' : defaultHoverBg);
            lldpBtn.style.transform = 'scale(1.08)';
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
            if (editor._showLldpInlineSubmenu) {
                editor._showLldpInlineSubmenu(lldpBtn, device, serial, sshConfig, toolbar, isDarkMode, defaultIconColor, defaultHoverBg);
            }
        };
        toolbar.appendChild(lldpBtn);
        
        // System Stack button (opens submenu with Stack Table + Git Commit)
        const stackBtn = createButton('layers', 'System Stack', () => {
            if (editor._showSystemStackInlineSubmenu) {
                editor._showSystemStackInlineSubmenu(stackBtn, device, serial, sshConfig, toolbar, isDarkMode, defaultIconColor, defaultHoverBg);
            }
        });
        toolbar.appendChild(stackBtn);
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
    if (editor._deviceSelectionToolbar) {
        editor._deviceSelectionToolbar.remove();
        editor._deviceSelectionToolbar = null;
        editor._deviceSelectionToolbarTarget = null;
    }
    if (editor._hideToolbarTooltip) editor._hideToolbarTooltip();
    const stylePalette = document.getElementById('device-style-palette-popup');
    if (stylePalette) stylePalette.remove();
    const labelStyleMenu = document.getElementById('device-label-style-menu');
    if (labelStyleMenu) labelStyleMenu.remove();
}

// Export functions
window.showDeviceSelectionToolbar = showDeviceSelectionToolbar;
window.hideDeviceSelectionToolbar = hideDeviceSelectionToolbar;

console.log('[topology-device-toolbar.js] Device selection toolbar module loaded');
