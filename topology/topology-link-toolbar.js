// ============================================================================
// TOPOLOGY LINK SELECTION TOOLBAR MODULE
// ============================================================================
// Handles the floating link selection toolbar with liquid glass styling.
// Extracted from topology.js to reduce main file size (~430 lines).
//
// Usage:
//   showLinkSelectionToolbar(editor, link, clickPos);
//   hideLinkSelectionToolbar(editor);
// ============================================================================

/**
 * Show the link selection toolbar
 * @param {TopologyEditor} editor - The editor instance
 * @param {object} link - The selected link
 * @param {object} clickPos - Optional click position
 */
function showLinkSelectionToolbar(editor, link, clickPos = null) {
    if (!link || (link.type !== 'link' && link.type !== 'unbound')) return;
    
    // Hide other toolbars
    if (editor.hideDeviceSelectionToolbar) editor.hideDeviceSelectionToolbar();
    hideLinkSelectionToolbar(editor);
    if (editor.hideTextSelectionToolbar) editor.hideTextSelectionToolbar();
    
    // Calculate screen position
    const rect = editor.canvas.getBoundingClientRect();
    
    // Find the visual midpoint of the link (respects curve)
    let posX, posY;
    let curvePeakY = null;
    
    if (clickPos) {
        posX = clickPos.x;
        posY = clickPos.y;
    } else if (link.type === 'unbound') {
        posX = (link.start.x + link.end.x) / 2;
        posY = (link.start.y + link.end.y) / 2;
    } else {
        const d1 = editor.objects.find(o => o.id === link.device1);
        const d2 = editor.objects.find(o => o.id === link.device2);
        if (d1 && d2) {
            posX = (d1.x + d2.x) / 2;
            posY = (d1.y + d2.y) / 2;
            // Use actual curve midpoint if link is curved
            if (link._cp1 && link._cp2 && link._renderedEndpoints) {
                const ep = link._renderedEndpoints;
                const t = 0.5;
                const mt = 1 - t;
                posX = mt*mt*mt*ep.startX + 3*mt*mt*t*link._cp1.x + 3*mt*t*t*link._cp2.x + t*t*t*ep.endX;
                posY = mt*mt*mt*ep.startY + 3*mt*mt*t*link._cp1.y + 3*mt*t*t*link._cp2.y + t*t*t*ep.endY;
                // Sample curve to find the bottommost point
                curvePeakY = posY;
                for (let s = 0; s <= 1; s += 0.05) {
                    const ms = 1 - s;
                    const cy = ms*ms*ms*ep.startY + 3*ms*ms*s*link._cp1.y + 3*ms*s*s*link._cp2.y + s*s*s*ep.endY;
                    if (cy > curvePeakY) curvePeakY = cy;
                }
            }
        } else {
            return;
        }
    }
    
    // Place toolbar below the lowest point of the curve (or midpoint for straight links)
    const belowY = curvePeakY !== null ? Math.max(posY, curvePeakY) : posY;
    const toolbarX = posX * editor.zoom + editor.panOffset.x + rect.left;
    const toolbarY = belowY * editor.zoom + editor.panOffset.y + rect.top + 30;
    
    // Create the toolbar container - Liquid Glass Style
    const toolbar = document.createElement('div');
    toolbar.id = 'link-selection-toolbar';
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
        animation: linkTbFadeIn 0.2s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        overflow: visible;
    `;
    
    // Add CSS animation
    const oldStyle = document.getElementById('link-tb-styles');
    if (oldStyle) oldStyle.remove();
    
    const style = document.createElement('style');
    style.id = 'link-tb-styles';
    style.textContent = `
        @keyframes linkTbFadeIn {
            from { opacity: 0; transform: translateX(-50%) translateY(5px); }
            to { opacity: 1; transform: translateX(-50%) translateY(0); }
        }
    `;
    document.head.appendChild(style);
    
    // Helper to create toolbar buttons
    const createButton = (iconId, title, onClick, options = {}) => {
        const { isDestructive = false, color = null } = options;
        const btn = document.createElement('button');
        btn.className = 'link-tb-btn';
        btn.innerHTML = `${editor._createIconSvg ? editor._createIconSvg(iconId, 16, color) : '●'}`;
        const iconColor = isDestructive 
            ? 'rgba(255, 100, 100, 0.9)' 
            : (isDarkMode ? 'rgba(255, 255, 255, 0.85)' : 'rgba(30, 30, 50, 0.85)');
        const hoverBg = isDarkMode ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.08)';
        const hoverColor = isDestructive ? '#ff6b6b' : (isDarkMode ? '#fff' : '#1a1a2e');
        btn.style.cssText = `
            position: relative;
            width: 30px;
            height: 30px;
            border: none;
            background: transparent;
            color: ${iconColor};
            cursor: pointer;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.12s ease;
            overflow: visible;
            user-select: none;
            -webkit-user-select: none;
        `;
        
        btn.onmouseenter = () => {
            btn.style.background = hoverBg;
            btn.style.color = hoverColor;
            btn.style.transform = 'scale(1.12)';
            if (editor._showToolbarTooltip) editor._showToolbarTooltip(btn, title);
        };
        btn.onmouseleave = () => {
            btn.style.background = 'transparent';
            btn.style.color = iconColor;
            btn.style.transform = 'scale(1)';
            if (editor._hideToolbarTooltip) editor._hideToolbarTooltip();
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
    
    // === LINK TOOLBAR BUTTONS ===
    
    // Add Adjacent Text button
    toolbar.appendChild(createButton('text', 'Add Text', () => {
        hideLinkSelectionToolbar(editor);
        if (editor.showAdjacentTextMenu) editor.showAdjacentTextMenu(link);
    }));
    
    toolbar.appendChild(createSeparator());
    
    // Color button
    toolbar.appendChild(createButton('palette', 'Color', () => {
        if (editor.showColorPalettePopupFromToolbar) editor.showColorPalettePopupFromToolbar(link, 'link', toolbar);
    }));
    
    // Width button
    toolbar.appendChild(createButton('ruler', 'Width', () => {
        if (editor.showLinkWidthSlider) editor.showLinkWidthSlider(link);
    }));
    
    // Style button
    toolbar.appendChild(createButton('sparkle', 'Style', () => {
        if (editor.showLinkStyleOptions) editor.showLinkStyleOptions(link);
    }));
    
    // Curve button
    toolbar.appendChild(createButton('curve', 'Curve', () => {
        if (editor.showLinkCurveOptions) editor.showLinkCurveOptions(link);
    }));
    
    toolbar.appendChild(createSeparator());
    
    // Attach/Detach button
    const isConnectedLink = link.type === 'link';
    const hasStartAttachment = link.device1 || (link.connectedTo && link.connectedTo.thisEndpoint === 'start');
    const hasEndAttachment = link.device2 || (link.connectedTo && link.connectedTo.thisEndpoint === 'end');
    const hasAnyAttachment = isConnectedLink || hasStartAttachment || hasEndAttachment;
    const isStickyEnabled = !link.stickyDisabled;
    
    let btnTooltip, btnColor, btnHoverColor;
    if (hasAnyAttachment) {
        btnTooltip = 'Detach from devices';
        btnColor = 'rgba(231, 76, 60, 0.85)';
        btnHoverColor = 'rgba(192, 57, 43, 1)';
    } else if (isStickyEnabled) {
        btnTooltip = 'Sticky: ON (click to disable)';
        btnColor = 'rgba(52, 152, 219, 0.85)';
        btnHoverColor = 'rgba(41, 128, 185, 1)';
    } else {
        btnTooltip = 'Sticky: OFF (click to enable)';
        btnColor = 'rgba(127, 140, 141, 0.7)';
        btnHoverColor = 'rgba(95, 106, 106, 1)';
    }
    
    const attachDetachBtn = document.createElement('button');
    attachDetachBtn.className = 'link-tb-btn';
    let iconName;
    if (hasAnyAttachment) {
        iconName = 'unlink';
    } else if (isStickyEnabled) {
        iconName = 'magnet';
    } else {
        iconName = 'magnet-off';
    }
    attachDetachBtn.innerHTML = editor._createIconSvg ? editor._createIconSvg(iconName, 16, '#ffffff') : '●';
    attachDetachBtn.style.cssText = `
        width: 30px;
        height: 30px;
        border: none;
        background: ${btnColor};
        color: #ffffff;
        cursor: pointer;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.12s ease;
    `;
    attachDetachBtn.onmouseenter = () => {
        attachDetachBtn.style.background = btnHoverColor;
        attachDetachBtn.style.transform = 'scale(1.1)';
        if (editor._showToolbarTooltip) editor._showToolbarTooltip(attachDetachBtn, btnTooltip);
    };
    attachDetachBtn.onmouseleave = () => {
        attachDetachBtn.style.background = btnColor;
        attachDetachBtn.style.transform = 'scale(1)';
        if (editor._hideToolbarTooltip) editor._hideToolbarTooltip();
    };
    attachDetachBtn.onmousedown = (e) => { e.stopPropagation(); e.preventDefault(); };
    attachDetachBtn.onclick = (e) => {
        e.stopPropagation();
        e.preventDefault();
        
        if (hasAnyAttachment) {
            // DETACH action
            if (editor.saveState) editor.saveState();
            
            if (isConnectedLink) {
                const dev1 = editor.objects.find(o => o.id === link.device1);
                const dev2 = editor.objects.find(o => o.id === link.device2);
                
                let startX, startY, endX, endY;
                
                if (dev1 && dev2) {
                    const getEdgePoint = (fromDevice, toDevice) => {
                        const dx = toDevice.x - fromDevice.x;
                        const dy = toDevice.y - fromDevice.y;
                        const dist = Math.sqrt(dx * dx + dy * dy);
                        const radius = fromDevice.radius || 40;
                        if (dist === 0) return { x: fromDevice.x + radius, y: fromDevice.y };
                        const ratio = radius / dist;
                        return { x: fromDevice.x + dx * ratio, y: fromDevice.y + dy * ratio };
                    };
                    
                    const startPos = getEdgePoint(dev1, dev2);
                    const endPos = getEdgePoint(dev2, dev1);
                    startX = startPos.x;
                    startY = startPos.y;
                    endX = endPos.x;
                    endY = endPos.y;
                } else if (dev1) {
                    startX = dev1.x + (dev1.radius || 40);
                    startY = dev1.y;
                    endX = startX + 100;
                    endY = startY;
                } else if (dev2) {
                    endX = dev2.x + (dev2.radius || 40);
                    endY = dev2.y;
                    startX = endX - 100;
                    startY = endY;
                } else {
                    startX = (editor.canvasW || editor.canvas.width) / 2 - 50;
                    startY = (editor.canvasH || editor.canvas.height) / 2;
                    endX = startX + 100;
                    endY = startY;
                }
                
                link.type = 'unbound';
                link.originType = 'UL';
                link.start = { x: startX, y: startY };
                link.end = { x: endX, y: endY };
                delete link.device1;
                delete link.device2;
                delete link.connectedTo;
                delete link._renderedEndpoints;
                delete link.device1Angle;
                delete link.device2Angle;
                
                if (editor.showToast) editor.showToast('Link detached - now free', 'success');
            } else {
                delete link.device1;
                delete link.device2;
                delete link.connectedTo;
                delete link._renderedEndpoints;
                delete link.device1Angle;
                delete link.device2Angle;
                
                if (!link.start || !link.end) {
                    link.start = { x: (editor.canvasW || editor.canvas.width) / 2 - 50, y: (editor.canvasH || editor.canvas.height) / 2 };
                    link.end = { x: (editor.canvasW || editor.canvas.width) / 2 + 50, y: (editor.canvasH || editor.canvas.height) / 2 };
                }
                
                if (editor.showToast) editor.showToast('Detached from devices', 'info');
            }
            
            link.stickyDisabled = true;
            if (link.originType === 'QL') link.originType = 'UL';
        } else {
            // TOGGLE STICKY mode
            if (editor.saveState) editor.saveState();
            if (isStickyEnabled) {
                link.stickyDisabled = true;
                if (editor.showToast) editor.showToast('Sticky OFF - won\'t attach to devices', 'info');
            } else {
                delete link.stickyDisabled;
                if (editor.showToast) editor.showToast('Sticky ON - drag near devices to attach', 'success');
            }
        }
        
        hideLinkSelectionToolbar(editor);
        if (editor.draw) editor.draw();
        if (editor.scheduleAutoSave) editor.scheduleAutoSave();
        
        setTimeout(() => {
            if (editor.selectedObject === link) {
                showLinkSelectionToolbar(editor, link);
            }
        }, 100);
    };
    toolbar.appendChild(attachDetachBtn);
    
    toolbar.appendChild(createSeparator());
    
    // Duplicate button
    toolbar.appendChild(createButton('copy', 'Duplicate', () => {
        hideLinkSelectionToolbar(editor);
        if (editor.duplicateObject) editor.duplicateObject(link, false);
    }));
    
    // Copy Style button
    toolbar.appendChild(createButton('brush', 'Copy Style', () => {
        hideLinkSelectionToolbar(editor);
        if (editor.copyObjectStyle) editor.copyObjectStyle(link);
        if (editor.showToast) editor.showToast('Style copied! Click another link to paste.', 'success');
    }));
    
    toolbar.appendChild(createSeparator());
    
    // Delete button — if part of a BUL chain, offer single-UL deletion
    const isBULMember = link.type === 'unbound' && (link.mergedWith || link.mergedInto);
    if (isBULMember) {
        const chainLinks = editor.getAllMergedLinks ? editor.getAllMergedLinks(link) : [link];
        const chainLen = chainLinks.length;
        
        toolbar.appendChild(createButton('trash', `Delete this UL (${chainLen} in chain)`, () => {
            hideLinkSelectionToolbar(editor);
            if (editor.saveState) editor.saveState();
            if (editor.handleULDeletionInBUL) editor.handleULDeletionInBUL(link);
            editor.objects = editor.objects.filter(obj => obj.id !== link.id);
            // Clean up attached text
            editor.objects.forEach(obj => {
                if (obj.type === 'text' && obj.linkId === link.id) {
                    delete obj.linkId;
                    delete obj.position;
                    delete obj.linkAttachT;
                }
            });
            editor.selectedObject = null;
            editor.selectedObjects = [];
            if (editor.draw) editor.draw();
            if (editor.scheduleAutoSave) editor.scheduleAutoSave();
            if (editor.showToast) editor.showToast('UL removed from chain', 'success');
        }, { isDestructive: true }));
        
        toolbar.appendChild(createButton('trash', 'Delete entire chain', () => {
            hideLinkSelectionToolbar(editor);
            // Select all chain links then delete
            editor.selectedObjects = chainLinks;
            editor.selectedObject = chainLinks[0];
            if (editor.deleteSelected) editor.deleteSelected();
        }, { isDestructive: true }));
    } else {
        toolbar.appendChild(createButton('trash', 'Delete', () => {
            hideLinkSelectionToolbar(editor);
            if (editor.deleteSelected) editor.deleteSelected();
        }, { isDestructive: true }));
    }
    
    // Prevent clicks from propagating to canvas
    toolbar.addEventListener('mousedown', (e) => {
        e.stopPropagation();
        e.preventDefault();
    });
    toolbar.addEventListener('click', (e) => {
        e.stopPropagation();
        e.preventDefault();
    });
    
    document.body.appendChild(toolbar);
    editor._linkSelectionToolbar = toolbar;
    editor._linkSelectionToolbarTarget = link;
    
    // Keep toolbar within viewport
    requestAnimationFrame(() => {
        const toolbarRect = toolbar.getBoundingClientRect();
        if (toolbarRect.right > window.innerWidth - 10) {
            toolbar.style.left = `${window.innerWidth - toolbarRect.width / 2 - 10}px`;
        }
        if (toolbarRect.left < 10) {
            toolbar.style.left = `${toolbarRect.width / 2 + 10}px`;
        }
        if (toolbarRect.bottom > window.innerHeight - 10) {
            toolbar.style.top = `${window.innerHeight - toolbarRect.height - 10}px`;
        }
    });
}

/**
 * Hide the link selection toolbar
 * @param {TopologyEditor} editor - The editor instance
 */
function hideLinkSelectionToolbar(editor) {
    if (editor._linkSelectionToolbar) {
        editor._linkSelectionToolbar.remove();
        editor._linkSelectionToolbar = null;
        editor._linkSelectionToolbarTarget = null;
    }
    if (editor._hideToolbarTooltip) editor._hideToolbarTooltip();
    const widthSlider = document.getElementById('link-width-slider-popup');
    if (widthSlider) widthSlider.remove();
    const stylePopup = document.getElementById('link-style-options-popup');
    if (stylePopup) stylePopup.remove();
    const curvePopup = document.getElementById('link-curve-options-popup');
    if (curvePopup) curvePopup.remove();
}

// Export functions
window.showLinkSelectionToolbar = showLinkSelectionToolbar;
window.hideLinkSelectionToolbar = hideLinkSelectionToolbar;

console.log('[topology-link-toolbar.js] Link selection toolbar module loaded');
