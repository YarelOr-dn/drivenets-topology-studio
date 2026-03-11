// ============================================================================
// TOPOLOGY MULTI-SELECT CONTEXT MENU MODULE
// ============================================================================
// Handles the liquid glass multi-select context menu for controlling
// multiple selected objects by category.
//
// This module contains the full implementation - not just a wrapper.
// Reduces topology.js by ~875 lines.
//
// Usage:
//   showMultiSelectContextMenu(editor, screenX, screenY);
//   hideMultiSelectContextMenu(editor);
// ============================================================================

/**
 * Show the multi-select context menu
 * @param {TopologyEditor} editor - The editor instance
 * @param {number} screenX - Screen X position
 * @param {number} screenY - Screen Y position
 */
function showMultiSelectContextMenu(editor, screenX, screenY) {
    // Hide any existing menus first
    hideMultiSelectContextMenu(editor);
    editor.hideAllSelectionToolbars();
    
    // Categorize selected objects
    const devices = editor.selectedObjects.filter(o => o.type === 'device');
    const links = editor.selectedObjects.filter(o => o.type === 'link' || o.type === 'unbound');
    const texts = editor.selectedObjects.filter(o => o.type === 'text');
    const shapes = editor.selectedObjects.filter(o => o.type === 'shape');
    
    // FIXED: Position at top-right of canvas, not at click position
    const canvasRect = editor.canvas.getBoundingClientRect();
    const menuRight = canvasRect.right - 20;
    const menuTop = canvasRect.top + 60;
    
    // Create the menu container - Liquid Glass Design
    const menu = document.createElement('div');
    menu.id = 'multi-select-context-menu';
    menu.style.cssText = `
        position: fixed;
        right: ${window.innerWidth - menuRight}px;
        top: ${menuTop}px;
        z-index: 100001;
        min-width: 280px;
        max-width: 340px;
        background: linear-gradient(135deg, 
            rgba(30, 30, 40, 0.65) 0%, 
            rgba(20, 20, 30, 0.55) 50%,
            rgba(15, 15, 25, 0.45) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 12px;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.4),
            0 0 0 1px rgba(255, 255, 255, 0.05) inset;
        backdrop-filter: blur(20px) saturate(150%);
        -webkit-backdrop-filter: blur(20px) saturate(150%);
        opacity: 0;
        transform: scale(0.95) translateY(-5px);
        animation: msMenuFadeIn 0.2s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
        user-select: none;
        -webkit-user-select: none;
    `;
    
    // Add CSS animation
    const oldStyle = document.getElementById('ms-menu-styles');
    if (oldStyle) oldStyle.remove();
    
    const style = document.createElement('style');
    style.id = 'ms-menu-styles';
    style.textContent = `
        @keyframes msMenuFadeIn {
            from { opacity: 0; transform: scale(0.95) translateY(-5px); }
            to { opacity: 1; transform: scale(1) translateY(0); }
        }
        .ms-category-header {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 10px;
            margin-bottom: 6px;
            background: linear-gradient(90deg, rgba(255, 255, 255, 0.08) 0%, transparent 100%);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.15s ease;
        }
        .ms-category-header:hover {
            background: linear-gradient(90deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.05) 100%);
        }
        .ms-category-icon {
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 6px;
        }
        .ms-category-title {
            flex: 1;
            font-size: 13px;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.95);
            letter-spacing: 0.3px;
        }
        .ms-category-count {
            font-size: 11px;
            font-weight: 600;
            color: #FF7A33;
            background: rgba(255, 94, 31, 0.15);
            padding: 2px 8px;
            border-radius: 10px;
        }
        .ms-category-chevron {
            color: rgba(255, 255, 255, 0.5);
            transition: transform 0.2s ease;
        }
        .ms-category-header.expanded .ms-category-chevron {
            transform: rotate(90deg);
        }
        .ms-btn {
            display: flex;
            align-items: center;
            gap: 10px;
            width: 100%;
            padding: 8px 12px;
            margin: 2px 0;
            background: transparent;
            border: none;
            border-radius: 8px;
            color: rgba(255, 255, 255, 0.85);
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.12s ease;
            text-align: left;
        }
        .ms-btn:hover {
            background: rgba(255, 255, 255, 0.12);
            color: #fff;
            transform: translateX(3px);
        }
        .ms-btn.destructive:hover {
            background: rgba(255, 100, 100, 0.2);
            color: #ff6b6b;
        }
        .ms-btn-icon {
            width: 18px;
            height: 18px;
            opacity: 0.8;
        }
        .ms-divider {
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.15) 50%, transparent 100%);
            margin: 8px 0;
        }
        .ms-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 10px;
            margin-bottom: 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .ms-header-title {
            font-size: 14px;
            font-weight: 700;
            color: #fff;
            letter-spacing: 0.5px;
        }
        .ms-header-count {
            font-size: 11px;
            color: rgba(255, 255, 255, 0.6);
        }
        .ms-category-content {
            padding-left: 8px;
            margin-bottom: 8px;
            border-left: 2px solid rgba(255, 94, 31, 0.3);
        }
        .ms-color-row {
            display: flex;
            gap: 4px;
            padding: 6px 12px;
            flex-wrap: wrap;
        }
        .ms-color-swatch {
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 2px solid rgba(255, 255, 255, 0.2);
            cursor: pointer;
            transition: all 0.12s ease;
        }
        .ms-color-swatch:hover {
            transform: scale(1.2);
            border-color: rgba(255, 255, 255, 0.6);
        }
    `;
    document.head.appendChild(style);
    
    // Header
    const header = document.createElement('div');
    header.className = 'ms-header';
    header.innerHTML = `
        <span class="ms-header-title">✨ Multi-Select</span>
        <span class="ms-header-count">${editor.selectedObjects.length} objects</span>
    `;
    menu.appendChild(header);
    
    // Helper to create action button
    const createActionBtn = (iconId, label, onClick, isDestructive = false) => {
        const btn = document.createElement('button');
        btn.className = `ms-btn${isDestructive ? ' destructive' : ''}`;
        btn.innerHTML = `
            <span class="ms-btn-icon">${editor._createIconSvg ? editor._createIconSvg(iconId, 16) : '●'}</span>
            <span>${label}</span>
        `;
        btn.onclick = (e) => {
            e.stopPropagation();
            onClick();
        };
        return btn;
    };
    
    // Helper to create color row
    const createColorRow = (onColorSelect) => {
        const row = document.createElement('div');
        row.className = 'ms-color-row';
        const colors = ['#e74c3c', '#FF5E1F', '#f1c40f', '#2ecc71', '#1abc9c', '#3498db', '#9b59b6', '#34495e', '#ffffff', '#000000'];
        colors.forEach(color => {
            const swatch = document.createElement('div');
            swatch.className = 'ms-color-swatch';
            swatch.style.background = color;
            swatch.onclick = (e) => {
                e.stopPropagation();
                onColorSelect(color);
            };
            row.appendChild(swatch);
        });
        return row;
    };
    
    // Helper to create category section
    const createCategory = (iconId, title, count, iconColor, contentBuilder) => {
        if (count === 0) return null;
        
        const section = document.createElement('div');
        section.className = 'ms-category';
        
        const headerEl = document.createElement('div');
        headerEl.className = 'ms-category-header';
        headerEl.innerHTML = `
            <div class="ms-category-icon" style="color: ${iconColor}">${editor._createIconSvg ? editor._createIconSvg(iconId, 16) : '●'}</div>
            <span class="ms-category-title">${title}</span>
            <span class="ms-category-count">${count}</span>
            <span class="ms-category-chevron">▶</span>
        `;
        
        const content = document.createElement('div');
        content.className = 'ms-category-content';
        content.style.display = 'none';
        contentBuilder(content);
        
        headerEl.onclick = (e) => {
            e.stopPropagation();
            headerEl.classList.toggle('expanded');
            content.style.display = headerEl.classList.contains('expanded') ? 'block' : 'none';
        };
        
        section.appendChild(headerEl);
        section.appendChild(content);
        return section;
    };
    
    // === DEVICES CATEGORY ===
    const deviceSection = createCategory('router', 'Devices', devices.length, '#3498db', (content) => {
        content.appendChild(createActionBtn('palette', 'Set Color', () => {}));
        content.appendChild(createColorRow((color) => {
            devices.forEach(d => d.color = color);
            editor.saveState();
            editor.draw();
            editor.showToast(`Color applied to ${devices.length} devices`, 'success');
        }));
        
        content.appendChild(createActionBtn('lock', 'Lock All', () => {
            devices.forEach(d => d.locked = true);
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Locked ${devices.length} devices`, 'info');
        }));
        content.appendChild(createActionBtn('unlock', 'Unlock All', () => {
            devices.forEach(d => d.locked = false);
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Unlocked ${devices.length} devices`, 'info');
        }));
        
        content.appendChild(createActionBtn('resize', 'Set Size', () => {
            const size = prompt('Enter radius for all devices (20-100):', '35');
            if (size && !isNaN(size)) {
                const radius = Math.max(20, Math.min(100, parseInt(size)));
                devices.forEach(d => d.radius = radius);
                editor.saveState();
                editor.draw();
                hideMultiSelectContextMenu(editor);
                editor.showToast(`Resized ${devices.length} devices to radius ${radius}`, 'success');
            }
        }));
        
        content.appendChild(createActionBtn('align-h', 'Align Horizontally', () => {
            if (devices.length < 2) return;
            const avgY = devices.reduce((sum, d) => sum + d.y, 0) / devices.length;
            devices.forEach(d => d.y = avgY);
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Aligned ${devices.length} devices horizontally`, 'success');
        }));
        content.appendChild(createActionBtn('align-v', 'Align Vertically', () => {
            if (devices.length < 2) return;
            const avgX = devices.reduce((sum, d) => sum + d.x, 0) / devices.length;
            devices.forEach(d => d.x = avgX);
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Aligned ${devices.length} devices vertically`, 'success');
        }));
        
        content.appendChild(createActionBtn('distribute', 'Distribute Evenly', () => {
            if (devices.length < 3) return;
            const sorted = [...devices].sort((a, b) => a.x - b.x);
            const startX = sorted[0].x;
            const endX = sorted[sorted.length - 1].x;
            const gap = (endX - startX) / (devices.length - 1);
            sorted.forEach((d, i) => d.x = startX + i * gap);
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Distributed ${devices.length} devices evenly`, 'success');
        }));
        
        content.appendChild(createActionBtn('link', `Group These ${devices.length} Devices`, () => {
            if (devices.length < 2) {
                editor.showToast('Need 2+ devices to group', 'warning');
                return;
            }
            const groupId = editor.generateGroupId();
            const leader = editor.findGroupLeader(devices);
            const leaderPos = { x: leader.x, y: leader.y };
            
            devices.forEach(d => {
                d.groupId = groupId;
                d.groupLeaderId = leader.id;
                d.groupOffsetX = d.x - leaderPos.x;
                d.groupOffsetY = d.y - leaderPos.y;
            });
            
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Grouped ${devices.length} devices (leader: ${leader.label})`, 'success');
        }));
    });
    if (deviceSection) menu.appendChild(deviceSection);
    
    // === LINKS CATEGORY ===
    const linkSection = createCategory('link', 'Links', links.length, '#2ecc71', (content) => {
        content.appendChild(createActionBtn('palette', 'Set Color', () => {}));
        content.appendChild(createColorRow((color) => {
            links.forEach(l => l.color = color);
            editor.saveState();
            editor.draw();
            editor.showToast(`Color applied to ${links.length} links`, 'success');
        }));
        
        const widthRow = document.createElement('div');
        widthRow.style.cssText = 'display: flex; gap: 4px; padding: 6px 12px; align-items: center;';
        widthRow.innerHTML = '<span style="font-size: 11px; color: rgba(255,255,255,0.6); margin-right: 8px;">Width:</span>';
        [1, 2, 3, 4, 6, 8].forEach(w => {
            const btn = document.createElement('button');
            btn.style.cssText = `width: 24px; height: 24px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.2);
                background: rgba(255,255,255,0.1); color: #fff; font-size: 10px; cursor: pointer; transition: all 0.12s;`;
            btn.textContent = w;
            btn.onmouseenter = () => btn.style.background = 'rgba(255,255,255,0.25)';
            btn.onmouseleave = () => btn.style.background = 'rgba(255,255,255,0.1)';
            btn.onclick = (e) => {
                e.stopPropagation();
                links.forEach(l => l.width = w);
                editor.saveState();
                editor.draw();
                editor.showToast(`Width set to ${w}px for ${links.length} links`, 'success');
            };
            widthRow.appendChild(btn);
        });
        content.appendChild(widthRow);
        
        content.appendChild(createActionBtn('minus', 'Style: Solid', () => {
            links.forEach(l => l.style = 'solid');
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Style set to solid for ${links.length} links`, 'success');
        }));
        content.appendChild(createActionBtn('dotted', 'Style: Dashed', () => {
            links.forEach(l => l.style = 'dashed');
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Style set to dashed for ${links.length} links`, 'success');
        }));
        content.appendChild(createActionBtn('arrow-right', 'Style: Arrow', () => {
            links.forEach(l => l.style = 'arrow');
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Style set to arrow for ${links.length} links`, 'success');
        }));
        
        content.appendChild(createActionBtn('curve', 'Curve: Auto', () => {
            links.forEach(l => {
                l.curveMode = 'auto';
                l.curveOverride = true;
                delete l.manualCurvePoint;
                delete l.keepCurve;
            });
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Curve mode set to Auto for ${links.length} links`, 'success');
        }));
        content.appendChild(createActionBtn('edit', 'Curve: Manual', () => {
            links.forEach(l => {
                l.curveMode = 'manual';
                l.curveOverride = true;
            });
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Curve mode set to Manual for ${links.length} links`, 'success');
        }));
        content.appendChild(createActionBtn('minus', 'Curve: Off', () => {
            links.forEach(l => {
                l.curveMode = 'off';
                l.curveOverride = true;
                delete l.manualCurvePoint;
                delete l.keepCurve;
            });
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Curve mode set to Off for ${links.length} links`, 'success');
        }));
        
        content.appendChild(createActionBtn('lock', 'Lock All', () => {
            links.forEach(l => l.locked = true);
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Locked ${links.length} links`, 'info');
        }));
        content.appendChild(createActionBtn('unlock', 'Unlock All', () => {
            links.forEach(l => l.locked = false);
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Unlocked ${links.length} links`, 'info');
        }));
        
        content.appendChild(createActionBtn('link', `Group These ${links.length} Links`, () => {
            if (links.length < 2) {
                editor.showToast('Need 2+ links to group', 'warning');
                return;
            }
            const groupId = editor.generateGroupId();
            const leader = editor.findGroupLeader(links);
            const leaderPos = leader.type === 'unbound'
                ? { x: (leader.start.x + leader.end.x) / 2, y: (leader.start.y + leader.end.y) / 2 }
                : { x: leader.x, y: leader.y };
            
            links.forEach(l => {
                l.groupId = groupId;
                l.groupLeaderId = leader.id;
                const lPos = l.type === 'unbound'
                    ? { x: (l.start.x + l.end.x) / 2, y: (l.start.y + l.end.y) / 2 }
                    : { x: l.x, y: l.y };
                l.groupOffsetX = lPos.x - leaderPos.x;
                l.groupOffsetY = lPos.y - leaderPos.y;
            });
            
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Grouped ${links.length} links`, 'success');
        }));
    });
    if (linkSection) menu.appendChild(linkSection);
    
    // === TEXT CATEGORY ===
    const textSection = createCategory('text', 'Text Boxes', texts.length, '#9b59b6', (content) => {
        content.appendChild(createActionBtn('palette', 'Set Text Color', () => {}));
        content.appendChild(createColorRow((color) => {
            texts.forEach(t => t.color = color);
            editor.saveState();
            editor.draw();
            editor.showToast(`Color applied to ${texts.length} text boxes`, 'success');
        }));
        
        const sizeRow = document.createElement('div');
        sizeRow.style.cssText = 'display: flex; gap: 4px; padding: 6px 12px; align-items: center;';
        sizeRow.innerHTML = '<span style="font-size: 11px; color: rgba(255,255,255,0.6); margin-right: 8px;">Size:</span>';
        [12, 14, 16, 20, 24, 32].forEach(s => {
            const btn = document.createElement('button');
            btn.style.cssText = `padding: 4px 8px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.2);
                background: rgba(255,255,255,0.1); color: #fff; font-size: 10px; cursor: pointer; transition: all 0.12s;`;
            btn.textContent = s;
            btn.onmouseenter = () => btn.style.background = 'rgba(255,255,255,0.25)';
            btn.onmouseleave = () => btn.style.background = 'rgba(255,255,255,0.1)';
            btn.onclick = (e) => {
                e.stopPropagation();
                texts.forEach(t => t.fontSize = s);
                editor.saveState();
                editor.draw();
                editor.showToast(`Font size set to ${s}px for ${texts.length} text boxes`, 'success');
            };
            sizeRow.appendChild(btn);
        });
        content.appendChild(sizeRow);
        
        content.appendChild(createActionBtn('bold', 'Make Bold', () => {
            texts.forEach(t => t.fontWeight = t.fontWeight === 'bold' ? 'normal' : 'bold');
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Toggled bold for ${texts.length} text boxes`, 'success');
        }));
        
        content.appendChild(createActionBtn('square', 'Toggle Background', () => {
            texts.forEach(t => t.showBackground = !t.showBackground);
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Toggled background for ${texts.length} text boxes`, 'success');
        }));
        
        content.appendChild(createActionBtn('lock', 'Lock All', () => {
            texts.forEach(t => t.locked = true);
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Locked ${texts.length} text boxes`, 'info');
        }));
        content.appendChild(createActionBtn('unlock', 'Unlock All', () => {
            texts.forEach(t => t.locked = false);
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Unlocked ${texts.length} text boxes`, 'info');
        }));
        
        content.appendChild(createActionBtn('link', `Group These ${texts.length} Text Boxes`, () => {
            if (texts.length < 2) {
                editor.showToast('Need 2+ text boxes to group', 'warning');
                return;
            }
            const groupId = editor.generateGroupId();
            const leader = editor.findGroupLeader(texts);
            const leaderPos = { x: leader.x, y: leader.y };
            
            texts.forEach(t => {
                t.groupId = groupId;
                t.groupLeaderId = leader.id;
                t.groupOffsetX = t.x - leaderPos.x;
                t.groupOffsetY = t.y - leaderPos.y;
            });
            
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Grouped ${texts.length} text boxes`, 'success');
        }));
        
        const attachedTexts = texts.filter(t => t.linkId);
        if (attachedTexts.length > 0) {
            content.appendChild(createActionBtn('unlink', `Detach from Links (${attachedTexts.length})`, () => {
                attachedTexts.forEach(t => {
                    delete t.linkId;
                    delete t.position;
                    delete t.linkAttachT;
                    delete t._onLinkLine;
                });
                editor.saveState();
                editor.draw();
                hideMultiSelectContextMenu(editor);
                editor.showToast(`Detached ${attachedTexts.length} text boxes from links`, 'success');
            }));
        }
    });
    if (textSection) menu.appendChild(textSection);
    
    // === SHAPES CATEGORY ===
    const shapeSection = createCategory('shapes', 'Shapes', shapes.length, '#FF5E1F', (content) => {
        content.appendChild(createActionBtn('palette', 'Set Fill Color', () => {}));
        content.appendChild(createColorRow((color) => {
            shapes.forEach(s => s.fillColor = color);
            editor.saveState();
            editor.draw();
            editor.showToast(`Fill color applied to ${shapes.length} shapes`, 'success');
        }));
        
        content.appendChild(createActionBtn('brush', 'Set Stroke Color', () => {}));
        content.appendChild(createColorRow((color) => {
            shapes.forEach(s => s.strokeColor = color);
            editor.saveState();
            editor.draw();
            editor.showToast(`Stroke color applied to ${shapes.length} shapes`, 'success');
        }));
        
        const strokeRow = document.createElement('div');
        strokeRow.style.cssText = 'display: flex; gap: 4px; padding: 6px 12px; align-items: center;';
        strokeRow.innerHTML = '<span style="font-size: 11px; color: rgba(255,255,255,0.6); margin-right: 8px;">Stroke:</span>';
        [0, 1, 2, 3, 4, 6].forEach(w => {
            const btn = document.createElement('button');
            btn.style.cssText = `width: 24px; height: 24px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.2);
                background: rgba(255,255,255,0.1); color: #fff; font-size: 10px; cursor: pointer; transition: all 0.12s;`;
            btn.textContent = w;
            btn.onmouseenter = () => btn.style.background = 'rgba(255,255,255,0.25)';
            btn.onmouseleave = () => btn.style.background = 'rgba(255,255,255,0.1)';
            btn.onclick = (e) => {
                e.stopPropagation();
                shapes.forEach(s => s.strokeWidth = w);
                editor.saveState();
                editor.draw();
                editor.showToast(`Stroke width set to ${w}px for ${shapes.length} shapes`, 'success');
            };
            strokeRow.appendChild(btn);
        });
        content.appendChild(strokeRow);
        
        content.appendChild(createActionBtn('eye', 'Set Opacity', () => {
            const opacity = prompt('Enter opacity (0-100):', '100');
            if (opacity && !isNaN(opacity)) {
                const value = Math.max(0, Math.min(100, parseInt(opacity))) / 100;
                shapes.forEach(s => s.opacity = value);
                editor.saveState();
                editor.draw();
                hideMultiSelectContextMenu(editor);
                editor.showToast(`Opacity set to ${Math.round(value * 100)}% for ${shapes.length} shapes`, 'success');
            }
        }));
        
        content.appendChild(createActionBtn('lock', 'Lock All', () => {
            shapes.forEach(s => s.locked = true);
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Locked ${shapes.length} shapes`, 'info');
        }));
        content.appendChild(createActionBtn('unlock', 'Unlock All', () => {
            shapes.forEach(s => s.locked = false);
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Unlocked ${shapes.length} shapes`, 'info');
        }));
        
        content.appendChild(createActionBtn('link', `Group These ${shapes.length} Shapes`, () => {
            if (shapes.length < 2) {
                editor.showToast('Need 2+ shapes to group', 'warning');
                return;
            }
            const groupId = editor.generateGroupId();
            const leader = editor.findGroupLeader(shapes);
            const leaderPos = { x: leader.x, y: leader.y };
            
            shapes.forEach(s => {
                s.groupId = groupId;
                s.groupLeaderId = leader.id;
                s.groupOffsetX = s.x - leaderPos.x;
                s.groupOffsetY = s.y - leaderPos.y;
            });
            
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Grouped ${shapes.length} shapes`, 'success');
        }));
        
        content.appendChild(createActionBtn('layers', 'Merge to Background', () => {
            shapes.forEach(s => {
                s.mergedToBackground = true;
                s.locked = true;
                s.layer = -1;
            });
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Merged ${shapes.length} shapes to background`, 'success');
        }));
        content.appendChild(createActionBtn('layers', 'Unmerge from Background', () => {
            shapes.forEach(s => {
                s.mergedToBackground = false;
                s.locked = false;
                s.layer = editor.getDefaultLayerForType ? editor.getDefaultLayerForType('shape') : 0;
            });
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Unmerged ${shapes.length} shapes from background`, 'info');
        }));
        
        content.appendChild(createActionBtn('align-h', 'Align Horizontally', () => {
            if (shapes.length < 2) return;
            const avgY = shapes.reduce((sum, s) => sum + s.y, 0) / shapes.length;
            shapes.forEach(s => s.y = avgY);
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Aligned ${shapes.length} shapes horizontally`, 'success');
        }));
        content.appendChild(createActionBtn('align-v', 'Align Vertically', () => {
            if (shapes.length < 2) return;
            const avgX = shapes.reduce((sum, s) => sum + s.x, 0) / shapes.length;
            shapes.forEach(s => s.x = avgX);
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Aligned ${shapes.length} shapes vertically`, 'success');
        }));
        
        content.appendChild(createActionBtn('distribute', 'Distribute Evenly', () => {
            if (shapes.length < 3) return;
            const sorted = [...shapes].sort((a, b) => a.x - b.x);
            const startX = sorted[0].x;
            const endX = sorted[sorted.length - 1].x;
            const gap = (endX - startX) / (shapes.length - 1);
            sorted.forEach((s, i) => s.x = startX + i * gap);
            editor.saveState();
            editor.draw();
            hideMultiSelectContextMenu(editor);
            editor.showToast(`Distributed ${shapes.length} shapes evenly`, 'success');
        }));
    });
    if (shapeSection) menu.appendChild(shapeSection);
    
    // === GLOBAL ACTIONS ===
    const divider = document.createElement('div');
    divider.className = 'ms-divider';
    menu.appendChild(divider);
    
    // Check if any selected objects are already grouped
    const hasGrouped = editor.selectedObjects.some(o => o.groupId);
    
    // Group button
    menu.appendChild(createActionBtn('link', `Group (${editor.selectedObjects.length})`, () => {
        if (editor.groups) editor.groups.groupSelected();
        hideMultiSelectContextMenu(editor);
    }));
    
    // Ungroup button
    if (hasGrouped) {
        const groupedCount = editor.selectedObjects.filter(o => o.groupId).length;
        menu.appendChild(createActionBtn('unlink', `Ungroup (${groupedCount})`, () => {
            if (editor.groups) editor.groups.ungroupSelected();
            hideMultiSelectContextMenu(editor);
        }));
    }
    
    // Lock All
    menu.appendChild(createActionBtn('lock', `Lock All (${editor.selectedObjects.length})`, () => {
        editor.selectedObjects.forEach(obj => obj.locked = true);
        editor.saveState();
        editor.draw();
        hideMultiSelectContextMenu(editor);
        editor.showToast(`Locked ${editor.selectedObjects.length} objects`, 'info');
    }));
    
    // Unlock All
    menu.appendChild(createActionBtn('unlock', `Unlock All (${editor.selectedObjects.length})`, () => {
        editor.selectedObjects.forEach(obj => obj.locked = false);
        editor.saveState();
        editor.draw();
        hideMultiSelectContextMenu(editor);
        editor.showToast(`Unlocked ${editor.selectedObjects.length} objects`, 'info');
    }));
    
    // Duplicate all
    menu.appendChild(createActionBtn('copy', `Duplicate All (${editor.selectedObjects.length})`, () => {
        hideMultiSelectContextMenu(editor);
        editor.copiedObjects = JSON.parse(JSON.stringify(editor.selectedObjects));
        editor.pasteObjects();
        editor.showToast(`Duplicated ${editor.copiedObjects.length} objects`, 'success');
    }));
    
    // Delete all
    menu.appendChild(createActionBtn('trash', `Delete All (${editor.selectedObjects.length})`, () => {
        hideMultiSelectContextMenu(editor);
        editor.deleteSelected();
    }, true));
    
    document.body.appendChild(menu);
    editor._multiSelectMenu = menu;
    
    // Adjust position to stay on screen
    requestAnimationFrame(() => {
        const rect = menu.getBoundingClientRect();
        if (rect.right > window.innerWidth) {
            menu.style.left = `${window.innerWidth - rect.width - 10}px`;
        }
        if (rect.bottom > window.innerHeight) {
            menu.style.top = `${window.innerHeight - rect.height - 10}px`;
        }
    });
    
    // Close menu when clicking outside
    const closeHandler = (e) => {
        if (!menu.contains(e.target)) {
            hideMultiSelectContextMenu(editor);
            document.removeEventListener('mousedown', closeHandler);
        }
    };
    setTimeout(() => document.addEventListener('mousedown', closeHandler), 100);
}

/**
 * Hide the multi-select context menu
 * @param {TopologyEditor} editor - The editor instance
 */
function hideMultiSelectContextMenu(editor) {
    if (editor._multiSelectMenu) {
        editor._multiSelectMenu.remove();
        editor._multiSelectMenu = null;
    }
}

// Export functions
window.showMultiSelectContextMenu = showMultiSelectContextMenu;
window.hideMultiSelectContextMenu = hideMultiSelectContextMenu;

console.log('[topology-multiselect-menu.js] Multi-select menu module loaded');
