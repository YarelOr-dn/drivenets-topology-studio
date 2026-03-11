/**
 * topology-bd-legend.js - Bridge Domain Legend Module
 * 
 * Contains the BD legend UI component
 */

'use strict';

window.BDLegend = {
    showBDLegend(editor, bridgeDomains) {
        // Remove existing legend if present
        editor.hideBDLegend();
        
        // Load saved state from localStorage
        const savedState = editor._loadBDPanelState();
        
        // Initialize BD visibility state (use saved or defaults)
        if (!editor._bdVisibility) {
            editor._bdVisibility = savedState.bdVisibility || {};
        }
        bridgeDomains.forEach(bd => {
            const bdName = bd.name || bd.bd_name;
            if (bdName && editor._bdVisibility[bdName] === undefined) {
                editor._bdVisibility[bdName] = true;
            }
        });
        
        // Save metadata for restore after refresh (panel state saved after DOM append)
        editor._multiBDMetadata = editor._multiBDMetadata || { bridge_domains: bridgeDomains };
        
        // Get the canvas container to position panel ON the grid
        const canvasContainer = editor.canvas.parentElement;
        const containerRect = canvasContainer.getBoundingClientRect();
        
        // Use saved position or defaults, but validate it's within bounds
        let posTop = savedState.top || 80;
        let posLeft = savedState.left || 10;
        
        // Validate position is within visible area (reset if outside)
        const panelWidth = 200;  // Approximate panel width
        const panelHeight = 300; // Approximate panel height
        const minVisible = 50;
        
        // Reset if panel would be mostly off-screen
        if (posLeft < -panelWidth + minVisible || posLeft > containerRect.width - minVisible) {
            posLeft = 10; // Reset to default
        }
        if (posTop < 0 || posTop > containerRect.height - minVisible) {
            posTop = 80; // Reset to default
        }
        
        const legend = document.createElement('div');
        legend.id = 'bd-legend-panel';
        
        // Load saved size from state
        const savedWidth = savedState.width || 300;
        const savedHeight = savedState.height || 'auto';
        
        legend.style.cssText = `
            position: absolute;
            top: ${posTop}px;
            left: ${posLeft}px;
            background: ${editor.darkMode ? 'rgba(17, 25, 40, 0.75)' : 'rgba(255, 255, 255, 0.65)'};
            border: 1px solid ${editor.darkMode ? 'rgba(255, 255, 255, 0.125)' : 'rgba(0, 0, 0, 0.1)'};
            border-radius: 16px;
            padding: 15px 18px;
            min-width: 220px;
            width: ${savedWidth}px;
            min-height: 180px;
            ${savedHeight !== 'auto' ? `height: ${savedHeight}px;` : ''}
            max-height: 600px;
            overflow-y: auto;
            z-index: 1000;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            font-family: 'Poppins', -apple-system, sans-serif;
            backdrop-filter: blur(16px) saturate(180%);
            -webkit-backdrop-filter: blur(16px) saturate(180%);
        `;
        
        // Make panel draggable with boundary constraints
        legend.style.cursor = 'move';
        let isDragging = false;
        let hasMoved = false;
        let dragOffsetX = 0, dragOffsetY = 0;
        
        const constrainToViewport = (x, y) => {
            const container = canvasContainer;
            const containerRect = container.getBoundingClientRect();
            const panelWidth = legend.offsetWidth || 200;
            const panelHeight = legend.offsetHeight || 300;
            
            // Minimum visible portion (at least 50px must stay visible)
            const minVisible = 50;
            
            // Constrain X: keep at least minVisible pixels inside container
            let newX = x;
            if (newX < -panelWidth + minVisible) newX = -panelWidth + minVisible;
            if (newX > containerRect.width - minVisible) newX = containerRect.width - minVisible;
            
            // Constrain Y: keep at least minVisible pixels inside container
            let newY = y;
            if (newY < 0) newY = 0; // Don't go above top
            if (newY > containerRect.height - minVisible) newY = containerRect.height - minVisible;
            
            return { x: newX, y: newY };
        };
        
        legend.addEventListener('mousedown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'BUTTON' || e.target.tagName === 'LABEL') return;
            if (e.target.closest && e.target.closest('.bd-legend-item')) return;
            isDragging = true;
            hasMoved = false;
            dragOffsetX = e.clientX - legend.offsetLeft;
            dragOffsetY = e.clientY - legend.offsetTop;
            legend.style.cursor = 'grabbing';
            legend.style.zIndex = '1001';
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            hasMoved = true;
            
            let newX = e.clientX - dragOffsetX;
            let newY = e.clientY - dragOffsetY;
            
            const constrained = constrainToViewport(newX, newY);
            
            legend.style.left = constrained.x + 'px';
            legend.style.top = constrained.y + 'px';
        });
        
        document.addEventListener('mouseup', () => {
            if (isDragging) {
                editor._saveBDPanelState();
                legend.style.zIndex = '1000';
            }
            isDragging = false;
            hasMoved = false;
            if (legend) legend.style.cursor = 'move';
        });
        
        // Header
        const header = document.createElement('div');
        header.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 1px solid ${editor.darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'};
        `;
        
        const title = document.createElement('h4');
        title.textContent = 'Bridge Domains';
        title.style.cssText = `margin: 0; color: ${editor.darkMode ? 'rgba(255,255,255,0.9)' : '#333'}; font-size: 14px; font-weight: 600;`;
        header.appendChild(title);
        
        legend.appendChild(header);
        
        // Quick actions row
        const actionsRow = document.createElement('div');
        actionsRow.style.cssText = `
            display: flex;
            gap: 6px;
            margin-bottom: 10px;
        `;
        
        const showAllBtn = document.createElement('button');
        showAllBtn.textContent = 'All';
        showAllBtn.title = 'Show all bridge domains on canvas';
        showAllBtn.style.cssText = `
            flex: 1;
            background: rgba(39,174,96,0.2);
            color: ${editor.darkMode ? 'rgba(39,174,96,0.9)' : '#27ae60'};
            border: 1px solid rgba(39,174,96,0.25);
            border-radius: 8px;
            padding: 5px 8px;
            font-size: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s;
            backdrop-filter: blur(6px);
        `;
        showAllBtn.onmouseenter = () => { showAllBtn.style.background = 'rgba(39,174,96,0.35)'; };
        showAllBtn.onmouseleave = () => { showAllBtn.style.background = 'rgba(39,174,96,0.2)'; };
        showAllBtn.onclick = () => editor.setBDVisibilityAll(true);
        actionsRow.appendChild(showAllBtn);
        
        const hideAllBtn = document.createElement('button');
        hideAllBtn.textContent = 'None';
        hideAllBtn.title = 'Hide all bridge domains from canvas';
        hideAllBtn.style.cssText = `
            flex: 1;
            background: rgba(231,76,60,0.2);
            color: ${editor.darkMode ? 'rgba(231,76,60,0.9)' : '#e74c3c'};
            border: 1px solid rgba(231,76,60,0.25);
            border-radius: 8px;
            padding: 5px 8px;
            font-size: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s;
            backdrop-filter: blur(6px);
        `;
        hideAllBtn.onmouseenter = () => { hideAllBtn.style.background = 'rgba(231,76,60,0.35)'; };
        hideAllBtn.onmouseleave = () => { hideAllBtn.style.background = 'rgba(231,76,60,0.2)'; };
        hideAllBtn.onclick = () => editor.setBDVisibilityAll(false);
        actionsRow.appendChild(hideAllBtn);
        
        legend.appendChild(actionsRow);
        
        // BD list with checkboxes
        const bdList = document.createElement('div');
        bdList.id = 'bd-legend-list';
        
        bridgeDomains.forEach((bd, idx) => {
            const color = bd.color || BD_COLOR_PALETTE[idx % BD_COLOR_PALETTE.length];
            const bdNameValue = bd.name || bd.bd_name || 'Unknown BD';
            const isVisible = editor._bdVisibility[bdNameValue] !== false;
            
            const bdItem = document.createElement('div');
            bdItem.className = 'bd-legend-item';
            bdItem.dataset.bdName = bdNameValue;
            bdItem.style.cssText = `
                display: flex;
                align-items: center;
                padding: 6px 8px;
                margin-bottom: 4px;
                background: ${editor.darkMode ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)'};
                border-left: 4px solid ${color};
                border-radius: 8px;
                transition: background 0.15s, opacity 0.15s;
                opacity: ${isVisible ? 1 : 0.5};
                cursor: pointer;
            `;
            
            bdItem.onmouseenter = () => {
                bdItem.style.background = editor.darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)';
            };
            bdItem.onmouseleave = () => {
                bdItem.style.background = editor.darkMode ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)';
            };
            
            // Checkbox for visibility
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `bd-check-${idx}`;
            checkbox.checked = isVisible;
            checkbox.style.cssText = `
                width: 15px;
                height: 15px;
                margin-right: 8px;
                cursor: pointer;
                accent-color: ${color};
                pointer-events: none;
            `;
            bdItem.appendChild(checkbox);
            
            // Color indicator
            const colorDot = document.createElement('div');
            colorDot.style.cssText = `
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: ${color};
                margin-right: 8px;
                flex-shrink: 0;
                pointer-events: none;
            `;
            bdItem.appendChild(colorDot);
            
            // BD info
            const bdInfo = document.createElement('div');
            bdInfo.style.cssText = 'flex: 1; min-width: 0; pointer-events: none;';
            
            const bdName = document.createElement('div');
            bdName.textContent = bdNameValue;
            bdName.style.cssText = `
                font-weight: 600;
                font-size: 11px;
                color: ${editor.darkMode ? 'rgba(255,255,255,0.9)' : '#333'};
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            `;
            bdInfo.appendChild(bdName);
            
            const bdMeta = document.createElement('div');
            const vlanValue = bd.vlan || bd.vlan_id || bd.global_vlan || 'N/A';
            let typeValue = bd.type;
            if (!typeValue && bdNameValue) {
                const nameLower = bdNameValue.toLowerCase();
                if (nameLower.startsWith('g_')) typeValue = 'Global';
                else if (nameLower.startsWith('l_')) typeValue = 'Local';
            }
            typeValue = typeValue ? typeValue.charAt(0).toUpperCase() + typeValue.slice(1) : 'Unknown';
            bdMeta.textContent = `${typeValue} • VLAN ${vlanValue}`;
            bdMeta.style.cssText = `
                font-size: 9px;
                color: ${editor.darkMode ? 'rgba(255,255,255,0.5)' : '#666'};
                margin-top: 1px;
            `;
            bdInfo.appendChild(bdMeta);
            
            bdItem.appendChild(bdInfo);
            
            // Click anywhere on the row to toggle visibility
            bdItem.addEventListener('click', (e) => {
                e.stopPropagation();
                e.preventDefault();
                checkbox.checked = !checkbox.checked;
                editor.toggleBDVisibility(bdNameValue, checkbox.checked);
                bdItem.style.opacity = checkbox.checked ? 1 : 0.5;
            });
            
            bdList.appendChild(bdItem);
        });
        
        legend.appendChild(bdList);
        
        // Close button
        const closeBtn = document.createElement('button');
        closeBtn.textContent = '×';
        closeBtn.title = 'Close panel [B]';
        closeBtn.style.cssText = `
            position: absolute;
            top: 8px;
            right: 10px;
            background: ${editor.darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)'};
            border: 1px solid ${editor.darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)'};
            font-size: 14px;
            color: ${editor.darkMode ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.4)'};
            cursor: pointer;
            padding: 2px 6px;
            line-height: 1;
            border-radius: 6px;
            transition: all 0.15s;
        `;
        closeBtn.onmouseenter = () => { closeBtn.style.background = editor.darkMode ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.08)'; closeBtn.style.color = editor.darkMode ? 'rgba(255,255,255,0.8)' : 'rgba(0,0,0,0.7)'; };
        closeBtn.onmouseleave = () => { closeBtn.style.background = editor.darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)'; closeBtn.style.color = editor.darkMode ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.4)'; };
        closeBtn.onclick = () => {
            editor.hideBDLegend();
            editor.updateBDHierarchyButton();
        };
        legend.appendChild(closeBtn);
        
        // Reset Position button (small icon next to close)
        const resetBtn = document.createElement('button');
        resetBtn.innerHTML = '⌂';
        resetBtn.title = 'Reset panel position and size';
        resetBtn.style.cssText = `
            position: absolute;
            top: 8px;
            right: 36px;
            background: ${editor.darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)'};
            border: 1px solid ${editor.darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)'};
            font-size: 13px;
            color: ${editor.darkMode ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.4)'};
            cursor: pointer;
            padding: 2px 6px;
            line-height: 1;
            border-radius: 6px;
            transition: all 0.15s;
        `;
        resetBtn.onmouseenter = () => { resetBtn.style.background = editor.darkMode ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.08)'; resetBtn.style.color = editor.darkMode ? 'rgba(255,255,255,0.8)' : 'rgba(0,0,0,0.7)'; };
        resetBtn.onmouseleave = () => { resetBtn.style.background = editor.darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)'; resetBtn.style.color = editor.darkMode ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.4)'; };
        resetBtn.onclick = (e) => {
            e.stopPropagation();
            // Reset to default position and size
            legend.style.top = '80px';
            legend.style.left = '10px';
            legend.style.width = '300px';
            legend.style.height = 'auto';
            editor._saveBDPanelState();
            editor.showToast('Panel position reset', 'info');
        };
        legend.appendChild(resetBtn);
        
        // ========== Edge Resize Handles ==========
        const createResizeHandle = (position) => {
            const handle = document.createElement('div');
            handle.className = `bd-resize-handle bd-resize-${position}`;
            
            let cursor, top, bottom, left, right, width, height;
            
            switch (position) {
                case 'left':
                    cursor = 'ew-resize';
                    top = '0'; bottom = '0'; left = '0'; width = '6px'; height = '100%';
                    break;
                case 'right':
                    cursor = 'ew-resize';
                    top = '0'; bottom = '0'; right = '0'; width = '6px'; height = '100%';
                    break;
                case 'top':
                    cursor = 'ns-resize';
                    top = '0'; left = '0'; right = '0'; height = '6px'; width = '100%';
                    break;
                case 'bottom':
                    cursor = 'ns-resize';
                    bottom = '0'; left = '0'; right = '0'; height = '6px'; width = '100%';
                    break;
                case 'bottom-left':
                    cursor = 'nesw-resize';
                    bottom = '0'; left = '0'; width = '12px'; height = '12px';
                    break;
                case 'bottom-right':
                    cursor = 'nwse-resize';
                    bottom = '0'; right = '0'; width = '12px'; height = '12px';
                    break;
                case 'top-left':
                    cursor = 'nwse-resize';
                    top = '0'; left = '0'; width = '12px'; height = '12px';
                    break;
                case 'top-right':
                    cursor = 'nesw-resize';
                    top = '0'; right = '0'; width = '12px'; height = '12px';
                    break;
            }
            
            handle.style.cssText = `
                position: absolute;
                cursor: ${cursor};
                z-index: 10;
                ${top ? `top: ${top};` : ''}
                ${bottom ? `bottom: ${bottom};` : ''}
                ${left ? `left: ${left};` : ''}
                ${right ? `right: ${right};` : ''}
                width: ${width};
                height: ${height};
                background: transparent;
            `;
            
            // Visual indicator on hover for corner handles
            if (position.includes('-')) {
                handle.onmouseenter = () => { 
                    handle.style.background = 'rgba(155, 89, 182, 0.4)'; 
                    handle.style.borderRadius = position === 'bottom-right' || position === 'top-left' ? '0 8px 0 8px' : '8px 0 8px 0';
                };
                handle.onmouseleave = () => { handle.style.background = 'transparent'; };
            }
            
            return handle;
        };
        
        // Create all 8 resize handles
        const resizeHandles = ['left', 'right', 'top', 'bottom', 'bottom-left', 'bottom-right', 'top-left', 'top-right'];
        resizeHandles.forEach(pos => legend.appendChild(createResizeHandle(pos)));
        
        // Resize logic
        let isResizing = false;
        let resizeDirection = null;
        let resizeStartX, resizeStartY, startWidth, startHeight, startLeft, startTop;
        
        legend.addEventListener('mousedown', (e) => {
            const handle = e.target.closest('.bd-resize-handle');
            if (handle) {
                e.stopPropagation();
                isResizing = true;
                resizeDirection = handle.className.replace('bd-resize-handle bd-resize-', '');
                resizeStartX = e.clientX;
                resizeStartY = e.clientY;
                startWidth = legend.offsetWidth;
                startHeight = legend.offsetHeight;
                startLeft = legend.offsetLeft;
                startTop = legend.offsetTop;
                document.body.style.cursor = handle.style.cursor;
                document.body.style.userSelect = 'none';
            }
        });
        
        const resizeMouseMove = (e) => {
            if (!isResizing) return;
            
            const dx = e.clientX - resizeStartX;
            const dy = e.clientY - resizeStartY;
            const minW = 220;
            const minH = 180;
            
            let newWidth = startWidth;
            let newHeight = startHeight;
            let newLeft = startLeft;
            let newTop = startTop;
            
            // Handle horizontal resizing
            if (resizeDirection.includes('right')) {
                newWidth = Math.max(minW, startWidth + dx);
            }
            if (resizeDirection.includes('left')) {
                const proposedWidth = startWidth - dx;
                if (proposedWidth >= minW) {
                    newWidth = proposedWidth;
                    newLeft = startLeft + dx;
                }
            }
            
            // Handle vertical resizing
            if (resizeDirection.includes('bottom') && !resizeDirection.startsWith('bottom-')) {
                newHeight = Math.max(minH, startHeight + dy);
            } else if (resizeDirection.includes('bottom')) {
                newHeight = Math.max(minH, startHeight + dy);
            }
            if (resizeDirection.includes('top') && !resizeDirection.startsWith('top-')) {
                const proposedHeight = startHeight - dy;
                if (proposedHeight >= minH) {
                    newHeight = proposedHeight;
                    newTop = startTop + dy;
                }
            } else if (resizeDirection.startsWith('top-')) {
                const proposedHeight = startHeight - dy;
                if (proposedHeight >= minH) {
                    newHeight = proposedHeight;
                    newTop = startTop + dy;
                }
            }
            
            legend.style.width = newWidth + 'px';
            legend.style.height = newHeight + 'px';
            legend.style.left = newLeft + 'px';
            legend.style.top = newTop + 'px';
        };
        
        const resizeMouseUp = () => {
            if (isResizing) {
                isResizing = false;
                resizeDirection = null;
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
                editor._saveBDPanelState();
            }
        };
        
        document.addEventListener('mousemove', resizeMouseMove);
        document.addEventListener('mouseup', resizeMouseUp);
        
        // Store cleanup function for when panel is removed
        legend._cleanupResize = () => {
            document.removeEventListener('mousemove', resizeMouseMove);
            document.removeEventListener('mouseup', resizeMouseUp);
        };
        
        // Append to canvas container so it's on the grid
        canvasContainer.appendChild(legend);
        
        // NOW save state (after panel is in DOM)
        editor._saveBDPanelState();
        
        // Show the BD Hierarchy button in top bar
        editor.updateBDHierarchyButton();
        
        console.log('[BD Panel] Created and state saved');
    },
    
    /**
     * Toggle BD visibility - extracted from topology.js
     */
    toggleBDVisibility(editor, bdName, visible) {
        if (!editor._bdVisibility) editor._bdVisibility = {};
        editor._bdVisibility[bdName] = visible;
        
        editor.objects.forEach(obj => {
            if (obj.type === 'link') {
                const linkBdName = obj.linkDetails?.bd_name || obj._bdName;
                if (linkBdName === bdName) obj._hidden = !visible;
            }
        });
        
        this.updateDeviceVisibilityByBD(editor);
        editor._saveBDPanelState();
        editor.draw();
    },

    /**
     * Update device visibility based on BD states - extracted from topology.js
     */
    updateDeviceVisibilityByBD(editor) {
        if (!editor._bdVisibility) return;
        
        const deviceBDs = {};
        
        editor.objects.forEach(obj => {
            if (obj.type === 'link' || obj.type === 'unbound') {
                const bdName = obj.linkDetails?.bd_name || obj._bdName;
                if (!bdName) return;
                
                let device1, device2;
                if (obj.device1) device1 = editor.objects.find(d => d.id === obj.device1);
                if (obj.device2) device2 = editor.objects.find(d => d.id === obj.device2);
                
                if (device1 && device1.type === 'device') {
                    if (!deviceBDs[device1.id]) deviceBDs[device1.id] = new Set();
                    deviceBDs[device1.id].add(bdName);
                }
                if (device2 && device2.type === 'device') {
                    if (!deviceBDs[device2.id]) deviceBDs[device2.id] = new Set();
                    deviceBDs[device2.id].add(bdName);
                }
            }
        });
        
        editor.objects.forEach(obj => {
            if (obj.type === 'device' && obj._bridgeDomains) {
                if (!deviceBDs[obj.id]) deviceBDs[obj.id] = new Set();
                obj._bridgeDomains.forEach(bd => deviceBDs[obj.id].add(bd));
            }
        });
        
        editor.objects.forEach(obj => {
            if (obj.type === 'device') {
                const bds = deviceBDs[obj.id];
                if (bds && bds.size > 0) {
                    let hasVisibleBD = false;
                    for (const bd of bds) {
                        if (editor._bdVisibility[bd] !== false) { hasVisibleBD = true; break; }
                    }
                    obj._hidden = !hasVisibleBD;
                } else {
                    const connectedLinks = editor.objects.filter(l => 
                        (l.type === 'link' || l.type === 'unbound') && 
                        (l.device1 === obj.id || l.device2 === obj.id)
                    );
                    if (connectedLinks.length > 0) {
                        const hasVisibleLink = connectedLinks.some(l => !l._hidden);
                        obj._hidden = !hasVisibleLink;
                    }
                }
            }
        });
        
        editor.objects.forEach(obj => {
            if (obj.type === 'text' && obj.linkId) {
                const parentLink = editor.objects.find(l => l.id === obj.linkId);
                obj._hidden = parentLink && parentLink._hidden;
            }
        });
    },

    /**
     * Set visibility for all BDs - extracted from topology.js
     */
    setBDVisibilityAll(editor, visible) {
        if (!editor._bdVisibility) editor._bdVisibility = {};
        
        const checkboxes = document.querySelectorAll('#bd-legend-list input[type="checkbox"]');
        checkboxes.forEach(cb => {
            cb.checked = visible;
            const item = cb.closest('.bd-legend-item');
            if (item) item.style.opacity = visible ? 1 : 0.5;
        });
        
        Object.keys(editor._bdVisibility).forEach(bdName => {
            editor._bdVisibility[bdName] = visible;
        });
        
        editor.objects.forEach(obj => {
            if (obj.type === 'link' && obj.linkDetails?.bd_name) obj._hidden = !visible;
        });
        
        this.updateDeviceVisibilityByBD(editor);
        editor._saveBDPanelState();
        editor.draw();
    },

    // ========================================================================
    // BD PANEL STATE & LIFECYCLE (moved from topology.js)
    // ========================================================================

    hideBDLegend(editor) {
        const existing = document.getElementById('bd-legend-panel');
        if (existing) {
            if (existing._cleanupResize) existing._cleanupResize();
            existing.remove();
        }
    },

    toggleBDLegendPanel(editor) {
        const existing = document.getElementById('bd-legend-panel');

        if (existing) {
            this.hideBDLegend(editor);
            this._saveBDPanelState(editor);
            this.updateBDHierarchyButton(editor);
        } else {
            if (!editor._multiBDMetadata || !editor._multiBDMetadata.bridge_domains || editor._multiBDMetadata.bridge_domains.length === 0) {
                this._reconstructBDMetadataFromCanvas(editor);
            }
            if (editor._multiBDMetadata && editor._multiBDMetadata.bridge_domains && editor._multiBDMetadata.bridge_domains.length > 0) {
                this.showBDLegend(editor, editor._multiBDMetadata.bridge_domains);
                this.updateBDHierarchyButton(editor);
            } else {
                editor.showToast('No Bridge Domains on canvas. Run DNAAS discovery first.', 'warning');
            }
        }
    },

    _reconstructBDMetadataFromCanvas(editor) {
        const palette = [
            '#00bcd4', '#ff9800', '#4caf50', '#e91e63', '#9c27b0',
            '#03a9f4', '#ff5722', '#8bc34a', '#673ab7', '#ffc107',
            '#009688', '#f44336', '#2196f3', '#cddc39', '#ff6f00'
        ];
        const seen = new Map();
        editor.objects.forEach(obj => {
            if (obj.type !== 'link' && obj.type !== 'unbound') return;
            const bdName = obj.linkDetails?.bd_name || obj._bdName;
            if (!bdName || seen.has(bdName)) return;
            const vlan = obj.linkDetails?.vlan_id || obj.linkDetails?.vlan || obj.linkDetails?.global_vlan || null;
            seen.set(bdName, vlan);
        });
        if (seen.size === 0) return;
        const bds = [];
        let idx = 0;
        for (const [name, vlan] of seen) {
            bds.push({ name, bd_name: name, vlan, color: palette[idx % palette.length] });
            idx++;
        }
        editor._multiBDMetadata = { bridge_domains: bds, view_mode: 'separate' };
    },

    updateBDHierarchyButton(editor) {
        const bdBadge = document.getElementById('btn-bd-hierarchy');
        if (!bdBadge) return;

        const hasBDs = editor._multiBDMetadata &&
                       editor._multiBDMetadata.bridge_domains &&
                       editor._multiBDMetadata.bridge_domains.length > 0;

        bdBadge.style.display = hasBDs ? 'inline-block' : 'none';

        const panelExists = !!document.getElementById('bd-legend-panel');
        if (panelExists) {
            bdBadge.style.background = 'linear-gradient(135deg, #27ae60, #1e8449)';
            bdBadge.style.boxShadow = '0 0 6px rgba(39, 174, 96, 0.6)';
        } else {
            bdBadge.style.background = 'linear-gradient(135deg, #9b59b6, #8e44ad)';
            bdBadge.style.boxShadow = 'none';
        }
    },

    _saveBDPanelState(editor) {
        const legend = document.getElementById('bd-legend-panel');
        const state = {
            visible: !!legend,
            top: legend ? parseInt(legend.style.top) || 80 : 80,
            left: legend ? parseInt(legend.style.left) || 10 : 10,
            width: legend ? legend.offsetWidth || 300 : 300,
            height: legend ? legend.offsetHeight || 'auto' : 'auto',
            bdVisibility: editor._bdVisibility || {},
            viewMode: editor._multiBDMetadata?.view_mode || 'separate',
            bridgeDomains: editor._multiBDMetadata?.bridge_domains || []
        };
        localStorage.setItem('bd_panel_state', JSON.stringify(state));
    },

    _loadBDPanelState(editor) {
        try {
            const saved = localStorage.getItem('bd_panel_state');
            if (saved) return JSON.parse(saved);
        } catch (e) {
            console.warn('Failed to load BD panel state:', e);
        }
        return {};
    },

    restoreBDPanelIfNeeded(editor) {
        const state = this._loadBDPanelState(editor);

        if (state.visible && state.bridgeDomains && state.bridgeDomains.length > 0) {
            editor._bdVisibility = state.bdVisibility || {};
            editor._multiBDMetadata = {
                bridge_domains: state.bridgeDomains,
                view_mode: state.viewMode || 'separate'
            };

            this.showBDLegend(editor, state.bridgeDomains);

            if (editor._bdVisibility) {
                for (const [bdName, visible] of Object.entries(editor._bdVisibility)) {
                    if (!visible) this.toggleBDVisibility(editor, bdName, false);
                }
            }
        }
    },

    _updateBDPanelTheme(editor) {
        const panel = document.getElementById('bd-legend-panel');
        if (!panel) return;

        this._saveBDPanelState(editor);

        if (editor._multiBDMetadata && editor._multiBDMetadata.bridge_domains && editor._multiBDMetadata.bridge_domains.length > 0) {
            this.showBDLegend(editor, editor._multiBDMetadata.bridge_domains);
            this.updateBDHierarchyButton(editor);
        }
    },

    toggleBDLinkView(editor) {
        if (!editor._multiBDMetadata) return;

        const currentMode = editor._multiBDMetadata.view_mode || 'combined';
        const newMode = currentMode === 'combined' ? 'separate' : 'combined';
        editor._multiBDMetadata.view_mode = newMode;

        const toggleBtn = document.getElementById('bd-view-toggle');
        if (toggleBtn) toggleBtn.textContent = newMode === 'combined' ? 'Separate' : 'Combined';

        this.applyBDViewMode(editor, newMode);
        editor.draw();
        editor.showToast(`Link view: ${newMode}`, 'info');
    },

    applyBDViewMode(editor, mode) {
        if (!editor._multiBDMetadata || !editor._multiBDMetadata.bridge_domains) return;

        const links = editor.objects.filter(o => o.type === 'link');

        if (mode === 'combined') {
            const pairsSeen = new Set();
            links.forEach(link => {
                const pairKey = [link.device1, link.device2].sort().join('|');
                link.hidden = pairsSeen.has(pairKey);
                if (!link.hidden) pairsSeen.add(pairKey);
            });
        } else {
            links.forEach(link => { link.hidden = false; });
        }
    },

    highlightBDPath(editor, bdName) {
        if (!editor._multiBDMetadata) return;

        const bd = editor._multiBDMetadata.bridge_domains.find(b =>
            (b.name === bdName) || (b.bd_name === bdName)
        );
        if (!bd) return;

        editor.objects.forEach(obj => { if (obj._bdHighlight) delete obj._bdHighlight; });

        if (bd.path_devices) {
            bd.path_devices.forEach(deviceName => {
                const device = editor.objects.find(o => o.type === 'device' && o.label === deviceName);
                if (device) device._bdHighlight = bd.color;
            });
        }

        editor.objects.filter(o => o.type === 'link').forEach(link => {
            if (link.linkDetails && link.linkDetails.bridgeDomains) {
                if (link.linkDetails.bridgeDomains.some(b => b.bd_name === bdName)) {
                    link._bdHighlight = bd.color;
                }
            }
        });

        editor.draw();

        setTimeout(() => {
            editor.objects.forEach(obj => { if (obj._bdHighlight) delete obj._bdHighlight; });
            editor.draw();
        }, 2000);
    },

    createBDTextBox(editor, bd, colorIndex) {
        const color = bd.color || BD_COLOR_PALETTE[colorIndex % BD_COLOR_PALETTE.length];
        return {
            id: `bd_text_${colorIndex}`,
            type: 'text',
            x: 80,
            y: 100 + colorIndex * 70,
            text: `${bd.name}\nType: ${bd.type || 'Unknown'}\nVLAN: ${bd.vlan || bd.global_vlan || 'N/A'}`,
            fontSize: 12,
            color: color,
            rotation: 0,
            showBackground: true,
            backgroundColor: color + '20',
            backgroundOpacity: 90,
            strokeColor: color,
            strokeWidth: 1
        };
    },

    // ========================================================================
    // INJECT METHODS ONTO EDITOR
    // ========================================================================

    inject(editor) {
        const methods = [
            'showBDLegend', 'hideBDLegend', 'toggleBDVisibility', 'setBDVisibilityAll',
            'updateDeviceVisibilityByBD', 'toggleBDLegendPanel', 'updateBDHierarchyButton',
            '_saveBDPanelState', '_loadBDPanelState', 'restoreBDPanelIfNeeded',
            '_updateBDPanelTheme', '_reconstructBDMetadataFromCanvas',
            'toggleBDLinkView', 'applyBDViewMode', 'highlightBDPath', 'createBDTextBox'
        ];
        for (const name of methods) {
            if (this[name]) {
                editor[name] = (...args) => this[name](editor, ...args);
            }
        }
    }

};

console.log('[topology-bd-legend.js] BDLegend loaded');
