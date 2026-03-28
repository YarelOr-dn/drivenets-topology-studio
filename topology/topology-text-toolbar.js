// ============================================================================
// TOPOLOGY TEXT SELECTION TOOLBAR MODULE
// ============================================================================
// Handles the floating text selection toolbar with liquid glass styling.
// Extracted from topology.js to reduce main file size (~360 lines).
//
// Usage:
//   showTextSelectionToolbar(editor, textObj);
//   hideTextSelectionToolbar(editor);
// ============================================================================

/**
 * Show the text selection toolbar
 * @param {TopologyEditor} editor - The editor instance
 * @param {object} textObj - The selected text object
 */
function showTextSelectionToolbar(editor, textObj) {
    if (!textObj || textObj.type !== 'text') return;
    
    // Don't show if inline editor is active
    if (editor._inlineTextEditor) return;
    
    // Don't show if text is currently being dragged
    if (editor.dragging) return;
    
    // Remove existing toolbar if any
    hideTextSelectionToolbar(editor);
    
    // Hide other toolbars
    if (editor.hideDeviceSelectionToolbar) editor.hideDeviceSelectionToolbar();
    if (editor.hideLinkSelectionToolbar) editor.hideLinkSelectionToolbar();
    if (editor.hideShapeSelectionToolbar) editor.hideShapeSelectionToolbar();
    
    // Calculate screen position of the text
    const rect = editor.canvas.getBoundingClientRect();
    
    // Get text dimensions
    const fontSize = parseInt(textObj.fontSize) || 14;
    const lines = (textObj.text || '').split('\n');
    const lineCount = Math.max(1, lines.length);
    const lineHeight = fontSize * 1.3;
    const textContentHeight = lineCount * lineHeight;
    const bgPadding = textObj.showBackground !== false ? (textObj.bgPadding || 8) : 0;
    const boxHeight = textContentHeight + bgPadding * 2;
    const boxWidth = (textObj.width || 100) + bgPadding * 2;
    
    // Use effective rotation (respects alwaysFaceUser) for toolbar placement
    const effRotShow = editor.getEffectiveTextRotation ? editor.getEffectiveTextRotation(textObj) : (textObj.rotation || 0);
    const rotation = effRotShow * Math.PI / 180;
    
    // Calculate the 4 corners of the text box (relative to center)
    const halfW = boxWidth / 2;
    const halfH = boxHeight / 2;
    const corners = [
        { x: -halfW, y: -halfH },
        { x: halfW, y: -halfH },
        { x: halfW, y: halfH },
        { x: -halfW, y: halfH }
    ];
    
    // Rotate corners and find the bounding box
    const cos = Math.cos(rotation);
    const sin = Math.sin(rotation);
    let minY = Infinity, maxY = -Infinity;
    
    corners.forEach(corner => {
        const rotY = corner.x * sin + corner.y * cos;
        minY = Math.min(minY, rotY);
        maxY = Math.max(maxY, rotY);
    });
    
    const centerScreenX = textObj.x * editor.zoom + editor.panOffset.x + rect.left;
    const centerScreenY = textObj.y * editor.zoom + editor.panOffset.y + rect.top;
    
    // Calculate bottom of the rotated bounding box in screen coordinates
    const bottomY = centerScreenY + (maxY * editor.zoom);
    
    // Position toolbar BELOW the rotated bounding box
    const toolbarX = centerScreenX;
    const toolbarY = bottomY + 15;
    
    // Create the toolbar container - Liquid Glass Style
    const toolbar = document.createElement('div');
    toolbar.id = 'text-selection-toolbar';
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
        animation: textTbFadeIn 0.15s ease-out forwards;
        overflow: visible;
    `;
    
    // Add CSS animation
    const oldStyle = document.getElementById('text-tb-styles');
    if (oldStyle) oldStyle.remove();
    
    const style = document.createElement('style');
    style.id = 'text-tb-styles';
    style.textContent = `
        @keyframes textTbFadeIn {
            from { opacity: 0; transform: translateX(-50%) translateY(5px); }
            to { opacity: 1; transform: translateX(-50%) translateY(0); }
        }
        #text-selection-toolbar { overflow: visible !important; }
        .text-tb-btn { overflow: visible !important; position: relative; }
    `;
    document.head.appendChild(style);
    
    // Helper to create toolbar buttons
    const iconColor = isDarkMode ? 'rgba(255, 255, 255, 0.85)' : 'rgba(30, 30, 50, 0.85)';
    const hoverBg = isDarkMode ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.08)';
    
    const createButton = (iconId, title, onClick, options = {}) => {
        const { isDestructive = false, color = null } = options;
        const btn = document.createElement('button');
        btn.className = 'text-tb-btn';
        btn.innerHTML = editor._createIconSvg ? editor._createIconSvg(iconId, 16, color) : '●';
        
        const btnColor = isDestructive ? 'rgba(255, 100, 100, 0.9)' : iconColor;
        const btnBg = isDestructive ? (isDarkMode ? 'rgba(192, 57, 43, 0.15)' : 'rgba(231, 76, 60, 0.1)') : 'transparent';
        
        btn.style.cssText = `
            position: relative;
            width: 30px;
            height: 30px;
            border: none;
            background: ${btnBg};
            color: ${btnColor};
            cursor: pointer;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.12s ease;
            overflow: visible;
        `;
        
        btn.onmouseenter = () => {
            btn.style.background = isDestructive 
                ? (isDarkMode ? 'rgba(192, 57, 43, 0.35)' : 'rgba(231, 76, 60, 0.2)')
                : hoverBg;
            btn.style.transform = 'scale(1.08)';
            if (editor._showToolbarTooltip) editor._showToolbarTooltip(btn, title);
        };
        btn.onmouseleave = () => {
            btn.style.background = btnBg;
            btn.style.transform = 'scale(1)';
            if (editor._hideToolbarTooltip) editor._hideToolbarTooltip();
        };
        btn.onmousedown = (e) => { e.stopPropagation(); e.preventDefault(); };
        btn.onclick = (e) => {
            e.stopPropagation();
            onClick();
        };
        return btn;
    };
    
    // Separator helper
    const createSeparator = () => {
        const sep = document.createElement('div');
        sep.style.cssText = `width: 1px; height: 20px; background: ${isDarkMode ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)'}; margin: 0 2px;`;
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
            badge.textContent = editor.getObjectLayer ? editor.getObjectLayer(obj) : 30;
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
            e.stopPropagation(); e.preventDefault();
            if (dropdown) { closeDropdown(); return; }
            dropdown = document.createElement('div');
            dropdown.style.cssText = `position: fixed; z-index: 100002; min-width: 160px; background: ${glassBgDrop}; border: 1px solid ${glassBorderDrop}; border-radius: 10px; padding: 4px 0; box-shadow: ${glassShadowDrop}; backdrop-filter: blur(24px) saturate(200%); -webkit-backdrop-filter: blur(24px) saturate(200%);`;
            items.forEach((item) => {
                if (!item) { const sep = document.createElement('div'); sep.style.cssText = `height: 1px; background: ${isDarkMode ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)'}; margin: 4px 6px;`; dropdown.appendChild(sep); return; }
                const div = document.createElement('div');
                div.style.cssText = `padding: 6px 12px; cursor: pointer; font-size: 12px; border-radius: 6px; margin: 0 4px; color: ${badgeColor};`;
                div.textContent = item.label;
                div.onmouseenter = () => { div.style.background = isDarkMode ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.06)'; };
                div.onmouseleave = () => { div.style.background = 'transparent'; };
                div.onmousedown = (ev) => { ev.stopPropagation(); ev.preventDefault(); };
                div.onclick = (ev) => { ev.stopPropagation(); ev.preventDefault(); applyLayerAction(item.fn); closeDropdown(); };
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
    
    // === TOOLBAR BUTTONS ===
    const isLinked = !!textObj.linkId;
    
    // Group 1: Content — Edit, Font, Color
    
    toolbar.appendChild(createButton('edit', 'Edit', () => {
        hideTextSelectionToolbar(editor);
        editor.showInlineTextEditor(textObj, null);
    }));
    
    toolbar.appendChild(createButton('text', 'Font', () => {
        editor.showTextFontSelector(textObj);
    }));
    
    toolbar.appendChild(createButton('palette', 'Color', () => {
        editor.showTextColorPalette(textObj);
    }));
    
    toolbar.appendChild(createSeparator());
    
    // Group 2: Appearance — Background, BG Color, Orientation
    
    toolbar.appendChild(createButton(textObj.showBackground !== false ? 'bg-on' : 'bg-off', 'Background', () => {
        textObj.showBackground = textObj.showBackground === false;
        if (isLinked && editor.updateAdjacentTextPosition) {
            editor.updateAdjacentTextPosition(textObj);
        }
        editor.saveState();
        editor.draw();
        setTimeout(() => showTextSelectionToolbar(editor, textObj), 50);
    }));
    
    if (textObj.showBackground !== false) {
        toolbar.appendChild(createButton('fill', 'BG Color', () => {
            editor.showTextBgColorPalette(textObj);
        }));
    }
    
    // Orientation: Link-attached → Face User / Follow Link toggle; Free → Rotate +45°
    if (isLinked) {
        const isFacingUser = textObj.alwaysFaceUser === true;
        toolbar.appendChild(createButton(isFacingUser ? 'link-dir' : 'eye',
            isFacingUser ? 'Follow Link Direction' : 'Face User (horizontal)',
            () => {
                textObj.alwaysFaceUser = !textObj.alwaysFaceUser;
                if (textObj.alwaysFaceUser) {
                    textObj.rotation = 0;
                } else {
                    delete textObj.alwaysFaceUser;
                    if (editor.updateAdjacentTextPosition) editor.updateAdjacentTextPosition(textObj);
                }
                editor.saveState();
                editor.draw();
                setTimeout(() => showTextSelectionToolbar(editor, textObj), 50);
            },
            { color: isFacingUser ? 'rgba(46, 204, 113, 0.9)' : 'rgba(160, 140, 255, 0.9)' }
        ));
    } else {
        toolbar.appendChild(createButton('rotate', 'Rotate 45°', () => {
            textObj.rotation = Math.round(((textObj.rotation || 0) + 45) % 360);
            editor.saveState();
            editor.draw();
            setTimeout(() => showTextSelectionToolbar(editor, textObj), 50);
        }));
    }
    
    toolbar.appendChild(createSeparator());
    
    // Group 3: Actions — Duplicate, Copy Style, Lock
    
    toolbar.appendChild(createButton('copy', 'Duplicate', () => {
        hideTextSelectionToolbar(editor);
        const newText = JSON.parse(JSON.stringify(textObj));
        newText.id = editor._generateId ? editor._generateId() : `text_${Date.now()}`;
        newText.x += 30;
        newText.y += 30;
        delete newText.linkId;
        delete newText.position;
        editor.objects.push(newText);
        editor.selectedObject = newText;
        editor.selectedObjects = [newText];
        editor.saveState();
        editor.draw();
        setTimeout(() => showTextSelectionToolbar(editor, newText), 100);
    }));
    
    toolbar.appendChild(createButton('brush', 'Copy Style', () => {
        hideTextSelectionToolbar(editor);
        editor.copyObjectStyle(textObj);
    }));
    
    const isLocked = textObj.locked || false;
    toolbar.appendChild(createButton(isLocked ? 'lock' : 'unlock', isLocked ? 'Unlock' : 'Lock', () => {
        textObj.locked = !textObj.locked;
        editor.saveState();
        editor.draw();
        setTimeout(() => showTextSelectionToolbar(editor, textObj), 50);
    }));
    
    toolbar.appendChild(createLayerWidget(textObj));
    
    // Detach from link (only if attached)
    if (isLinked) {
        toolbar.appendChild(createButton('unlink', 'Detach from Link', () => {
            delete textObj.linkId;
            delete textObj.position;
            delete textObj.linkAttachT;
            delete textObj._onLinkLine;
            delete textObj._interfaceLabel;
            delete textObj.alwaysFaceUser;
            hideTextSelectionToolbar(editor);
            editor.saveState();
            editor.draw();
        }));
    }
    
    toolbar.appendChild(createSeparator());
    
    // Group 4: Delete
    
    toolbar.appendChild(createButton('trash', 'Delete', () => {
        hideTextSelectionToolbar(editor);
        const index = editor.objects.indexOf(textObj);
        if (index > -1) {
            editor.saveState();
            editor.objects.splice(index, 1);
            editor.selectedObject = null;
            editor.selectedObjects = [];
            editor.draw();
        }
    }, { isDestructive: true }));
    
    toolbar.addEventListener('mousedown', (e) => e.stopPropagation());
    toolbar.addEventListener('click', (e) => e.stopPropagation());
    toolbar.addEventListener('keydown', (e) => { e.stopPropagation(); });
    toolbar.addEventListener('keyup', (e) => { e.stopPropagation(); });
    
    document.body.appendChild(toolbar);
    
    // Store references
    editor._textSelectionToolbar = toolbar;
    editor._textSelectionToolbarTarget = textObj;
    
    // Adjust position if off-screen
    setTimeout(() => {
        const toolbarRect = toolbar.getBoundingClientRect();
        if (toolbarRect.right > window.innerWidth - 10) {
            toolbar.style.left = `${window.innerWidth - toolbarRect.width / 2 - 10}px`;
        }
        if (toolbarRect.left < 10) {
            toolbar.style.left = `${toolbarRect.width / 2 + 10}px`;
        }
        if (toolbarRect.bottom > window.innerHeight - 10) {
            // Position ABOVE the text box instead
            const topY = centerScreenY + (minY * editor.zoom) - 15;
            toolbar.style.top = `${topY - toolbarRect.height}px`;
        }
    }, 0);
}

/**
 * Hide the text selection toolbar
 * @param {TopologyEditor} editor - The editor instance
 */
function hideTextSelectionToolbar(editor) {
    if (editor._textSelectionToolbar) {
        editor._textSelectionToolbar.remove();
        editor._textSelectionToolbar = null;
        editor._textSelectionToolbarTarget = null;
    }
    // Remove the active tooltip if present
    const tooltip = document.getElementById('tb-active-tooltip');
    if (tooltip) tooltip.remove();
    // Remove text color palette if present
    const colorPalette = document.getElementById('text-color-palette-popup');
    if (colorPalette) colorPalette.remove();
    const bgColorPalette = document.getElementById('text-bg-color-palette-popup');
    if (bgColorPalette) bgColorPalette.remove();
}

/**
 * Update toolbar position when canvas pans/zooms (horizontal toolbar)
 * @param {TopologyEditor} editor - The editor instance
 */
function updateTextSelectionToolbarPosition(editor) {
    if (!editor._textSelectionToolbar || !editor._textSelectionToolbarTarget) return;
    
    const textObj = editor._textSelectionToolbarTarget;
    const rect = editor.canvas.getBoundingClientRect();
    
    // Measure actual text width using canvas context
    editor.ctx.save();
    const fontFamily = textObj.fontFamily || 'Arial';
    const fontWeight = textObj.fontWeight || 'normal';
    const fontSize = parseInt(textObj.fontSize) || 14;
    editor.ctx.font = `${fontWeight} ${fontSize}px ${fontFamily}`;
    const textContent = textObj.text || 'Text';
    const lines = textContent.split('\n');
    const lineCount = Math.max(1, lines.length);
    
    // Measure the widest line
    let maxLineWidth = 0;
    lines.forEach(line => {
        const metrics = editor.ctx.measureText(line || ' ');
        maxLineWidth = Math.max(maxLineWidth, metrics.width);
    });
    editor.ctx.restore();
    
    const lineHeight = fontSize * 1.3;
    const textContentHeight = lineCount * lineHeight;
    const bgPadding = textObj.showBackground !== false ? (textObj.bgPadding || 8) : 4;
    const boxHeight = textContentHeight + bgPadding * 2;
    const boxWidth = maxLineWidth + bgPadding * 2;
    
    // Use effective rotation (respects alwaysFaceUser) for toolbar position
    const effRotUpd = editor.getEffectiveTextRotation ? editor.getEffectiveTextRotation(textObj) : (textObj.rotation || 0);
    const rotation = effRotUpd * Math.PI / 180;
    
    // Calculate the 4 corners of the text box (relative to center)
    const halfW = boxWidth / 2;
    const halfH = boxHeight / 2;
    const corners = [
        { x: -halfW, y: -halfH },
        { x: halfW, y: -halfH },
        { x: halfW, y: halfH },
        { x: -halfW, y: halfH }
    ];
    
    // Rotate corners and find bounding box
    const cos = Math.cos(rotation);
    const sin = Math.sin(rotation);
    let maxY = -Infinity;
    
    corners.forEach(corner => {
        const rotY = corner.x * sin + corner.y * cos;
        maxY = Math.max(maxY, rotY);
    });
    
    const centerScreenX = textObj.x * editor.zoom + editor.panOffset.x + rect.left;
    const centerScreenY = textObj.y * editor.zoom + editor.panOffset.y + rect.top;
    
    // Position below rotated bounding box with consistent gap
    const bottomY = centerScreenY + (maxY * editor.zoom);
    const toolbarGap = 20; // Fixed pixel gap below text
    
    editor._textSelectionToolbar.style.left = `${centerScreenX}px`;
    editor._textSelectionToolbar.style.top = `${bottomY + toolbarGap}px`;
    editor._textSelectionToolbar.style.transform = `translateX(-50%)`;
}

// Export functions
window.showTextSelectionToolbar = showTextSelectionToolbar;
window.hideTextSelectionToolbar = hideTextSelectionToolbar;
window.updateTextSelectionToolbarPosition = updateTextSelectionToolbarPosition;

console.log('[topology-text-toolbar.js] Text selection toolbar module loaded');
