/**
 * topology-context-menu-handlers.js - Context Menu Handlers Module
 * 
 * Extracted from topology.js for modular architecture.
 * All methods receive 'editor' as first parameter instead of using 'this'.
 */

'use strict';

window.ContextMenuHandlers = {
    handleContextMenu(editor, e) {
        e.preventDefault();
        
        // If in device placement mode, right-click exits to base mode
        if (editor.placingDevice) {
            editor.placingDevice = null;
            editor.placementPending = null;
            editor.setMode('base');
            return;
        }
        
        // If in text placement mode, right-click exits to base mode
        // Also exits continuous TB placement mode
        if (editor.currentTool === 'text') {
            editor.textPlacementPending = null;
            editor.exitContinuousTextPlacement(); // Exit continuous mode and update button
            editor.setMode('base');
            return;
        }
        
        // ✨ MULTI-SELECT: Check FIRST - Right-click with multiple objects selected → Show multi-select menu
        // This must come before link mode check to ensure MS menu works after marquee in link mode
        if (editor.selectedObjects && editor.selectedObjects.length > 1) {
            // Reset any active drag/rotation state
            editor.dragging = false;
            editor.dragStart = null;
            editor.rotatingDevice = null;
            editor.resizingDevice = null;
            
            // Show the special multi-select context menu (liquid glass design)
            editor.showMultiSelectContextMenu(e.clientX, e.clientY);
            
            if (editor.debugger) {
                const devices = editor.selectedObjects.filter(o => o.type === 'device').length;
                const links = editor.selectedObjects.filter(o => o.type === 'link' || o.type === 'unbound').length;
                const texts = editor.selectedObjects.filter(o => o.type === 'text').length;
                editor.debugger.logSuccess(`🖱️ Multi-select right-click: ${editor.selectedObjects.length} objects`);
                editor.debugger.logInfo(`   Devices: ${devices}, Links: ${links}, Text: ${texts}`);
            }
            return;
        }
        
        // If in link mode or TP chaining mode, right-click exits to base mode (no menu)
        if (editor.currentTool === 'link' || editor.currentMode === 'link' || editor._linkFromTP || editor.linking) {
            editor.linking = false;
            editor.linkStart = null;
            editor._linkFromTP = null; // Clear TP linking mode
            editor.setMode('base');
            editor.draw();
            
            if (editor.debugger) {
                editor.debugger.logInfo(`🔗 Right-click → Exited to BASE mode (no menu)`);
            }
            return; // CRITICAL: Return here to prevent any menu from opening
        }
        
        const pos = editor.getMousePos(e);
        const clickedObject = editor.findObjectAt(pos.x, pos.y);
        
        // CRITICAL: Stop any dragging when context menu opens
        editor.dragging = false;
        editor.dragStart = null;
        editor.stretchingLink = null;
        editor.stretchingEndpoint = null;
        editor.rotatingDevice = null;
        editor.resizingDevice = null;
        editor.resizeHandle = null;
        editor.resizeStartDist = 0; // Reset delta calculation value
        editor.rotatingText = false;
        editor.resizingText = false;
        
        
        // ✨ Right-click on device → Show device selection toolbar (liquid glass style)
        if (clickedObject && clickedObject.type === 'device') {
            // Cancel any device placement
            if (editor.placingDevice) {
                editor.placingDevice = null;
            }
            
            // Select the device if not already selected
            if (!editor.selectedObjects.includes(clickedObject)) {
                editor.selectedObject = clickedObject;
                editor.selectedObjects = [clickedObject];
                // GROUP EXPANSION: Include all group members
                if (editor.groups) editor.groups.expandSelection();
            }
            
            // Show the new device selection toolbar instead of context menu
            editor.showDeviceSelectionToolbar(clickedObject);
            
            if (editor.debugger) {
                const gridPos = editor.worldToGrid({ x: clickedObject.x, y: clickedObject.y });
                editor.debugger.logSuccess(`🖱️ Right-click on device: Toolbar for ${clickedObject.label || 'Device'}`);
                editor.debugger.logInfo(`Device: ${clickedObject.label} at Grid(${Math.round(gridPos.x)}, ${Math.round(gridPos.y)})`);
            }
            
            editor.draw();
            return;
        }
        
        // Right-click on TEXT object → Show text selection toolbar (NOT context menu)
        // All text features are now in the floating toolbar
        if (clickedObject && clickedObject.type === 'text') {
            // Select the text if not already selected
            if (!editor.selectedObjects.includes(clickedObject)) {
                editor.selectedObject = clickedObject;
                editor.selectedObjects = [clickedObject];
                // GROUP EXPANSION: Include all group members
                if (editor.groups) editor.groups.expandSelection();
            }
            
            // Show the text selection toolbar instead of context menu
            editor.showTextSelectionToolbar(clickedObject);
            
            if (editor.debugger) {
                editor.debugger.logSuccess(`🖱️ Right-click on text: Showing toolbar for "${clickedObject.text || 'Text'}"`);
            }
            
            editor.draw();
            return;
        }
        
        // For links (connected or unbound), show link selection toolbar (liquid glass style)
        if (clickedObject && (clickedObject.type === 'link' || clickedObject.type === 'unbound')) {
            // Check if clicked object is part of a BUL chain
            const isBulLink = clickedObject.type === 'unbound' && (clickedObject.mergedWith || clickedObject.mergedInto);
            
            // Check if current multi-selection is just a BUL chain (not manual multi-selection)
            let isOnlyBulChain = false;
            if (editor.selectedObjects.length > 1 && editor.selectedObjects.includes(clickedObject)) {
                // Check if all selected objects are part of the same BUL chain
                const allMergedLinks = editor.getAllMergedLinks(clickedObject);
                isOnlyBulChain = editor.selectedObjects.every(obj => allMergedLinks.includes(obj));
            }
            
            // If clicking on an already-selected object in TRUE multi-select (not just BUL chain), show bulk menu
            if (editor.selectedObjects.length > 1 && editor.selectedObjects.includes(clickedObject) && !isOnlyBulChain) {
                // Keep current multi-selection, show bulk operations menu
                editor.showBulkContextMenu(e.clientX, e.clientY);
            } else {
                // Single selection OR BUL chain - replace selection with clicked object and its chain
                editor.selectedObject = clickedObject;
                editor.selectedObjects = [clickedObject];
                
                // ENHANCED: If selecting a merged UL, also add ALL partners in the BUL chain to selection
                if (isBulLink) {
                    const allMergedLinks = editor.getAllMergedLinks(clickedObject);
                    allMergedLinks.forEach(link => {
                        if (!editor.selectedObjects.includes(link)) {
                            editor.selectedObjects.push(link);
                        }
                    });
                }
                
                // Show the new link selection toolbar instead of context menu
                editor.showLinkSelectionToolbar(clickedObject);
                
                if (editor.debugger) {
                    editor.debugger.logSuccess(`🖱️ Right-click on link: Toolbar for ${clickedObject.id}`);
                }
            }
            
            editor.draw();
            return;
        } else if (!clickedObject) {
            // Right-clicked on empty space (grid/background)
            // ALWAYS transition to base mode regardless of current mode
            // Clear any selection and hide toolbars
            if (editor.selectedObjects.length > 0 || editor.selectedObject) {
                editor.selectedObjects = [];
                editor.selectedObject = null;
            }
            editor.hideAllSelectionToolbars();
            editor.setMode('base');
            editor.draw();
        }
    },

    showContextMenu(editor, x, y, obj) {
        // BUGFIX: Hide text selection toolbar when showing context menu
        editor.hideTextSelectionToolbar();
        
        const menu = document.getElementById('context-menu');
        menu.style.display = 'block';
        
        // Get menu dimensions after making it visible
        const menuRect = menu.getBoundingClientRect();
        const menuWidth = menuRect.width || 200;  // Fallback width
        const menuHeight = menuRect.height || 300; // Fallback height
        
        // Get viewport dimensions
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // Adjust position to keep menu within viewport
        let adjustedX = x;
        let adjustedY = y;
        
        // Check right edge
        if (x + menuWidth > viewportWidth - 10) {
            adjustedX = viewportWidth - menuWidth - 10;
        }
        // Check left edge
        if (adjustedX < 10) {
            adjustedX = 10;
        }
        // Check bottom edge
        if (y + menuHeight > viewportHeight - 10) {
            adjustedY = viewportHeight - menuHeight - 10;
        }
        // Check top edge
        if (adjustedY < 10) {
            adjustedY = 10;
        }
        
        menu.style.left = adjustedX + 'px';
        menu.style.top = adjustedY + 'px';
        editor.contextMenuVisible = true;
        // Store position for submenus like adjacent text menu
        editor._contextMenuX = adjustedX;
        editor._contextMenuY = adjustedY;
        
        // Hide background-specific items
        const baseModeItem = document.getElementById('ctx-base-mode');
        if (baseModeItem) baseModeItem.style.display = 'none';
        
        // Get all menu items
        const copyStyleItem = document.getElementById('ctx-copy-style');
        const duplicateItem = document.getElementById('ctx-duplicate');
        const addTextItem = document.getElementById('ctx-add-text');
        const changeLabelItem = document.getElementById('ctx-change-label');
        const curveSubmenuTrigger = document.getElementById('ctx-curve');
        const changeColorItem = document.getElementById('ctx-change-color');
        const deleteItem = document.getElementById('ctx-delete');
        
        // Lock/Unlock options
        const lockItem = document.getElementById('ctx-lock');
        const unlockItem = document.getElementById('ctx-unlock');
        
        // Show common items for all object types
        if (copyStyleItem) copyStyleItem.style.display = 'block';
        if (duplicateItem) duplicateItem.style.display = 'block';
        if (changeColorItem) changeColorItem.style.display = 'block';
        if (deleteItem) deleteItem.style.display = 'block';
        
        // Link-specific items
        const changeWidthItem = document.getElementById('ctx-change-width');
        const changeStyleItem = document.getElementById('ctx-change-style');
        
        if (obj.type === 'link' || obj.type === 'unbound') {
            if (addTextItem) addTextItem.style.display = 'block';
            if (changeLabelItem) changeLabelItem.style.display = 'none';
            if (changeWidthItem) changeWidthItem.style.display = 'block';
            if (changeStyleItem) changeStyleItem.style.display = 'block';
            if (lockItem) lockItem.style.display = 'none';
            if (unlockItem) unlockItem.style.display = 'none';
            
            // Show curve submenu trigger for links
            if (curveSubmenuTrigger) {
                curveSubmenuTrigger.style.display = 'block';
                // Store link reference for submenu items
                editor._curveSubmenuLink = obj;
            }
            
            // Show detach option if link is attached to device(s)
            const detachDeviceItem = document.getElementById('ctx-detach-device');
            if (detachDeviceItem) {
                const device1 = obj.device1 ? editor.objects.find(d => d.id === obj.device1) : null;
                const device2 = obj.device2 ? editor.objects.find(d => d.id === obj.device2) : null;
                
                if (device1 || device2) {
                    detachDeviceItem.style.display = 'block';
                    let detachText = '';
                    if (device1 && device2) {
                        detachText = `Detach from ${device1.label || 'Device'} & ${device2.label || 'Device'}`;
                    } else if (device1) {
                        detachText = `Detach from ${device1.label || 'Device'}`;
                    } else if (device2) {
                        detachText = `Detach from ${device2.label || 'Device'}`;
                    }
                    detachDeviceItem.innerHTML = `${appIcon('unlink')} ${detachText}`;
                    // Store link reference for detach handler
                    editor._detachLink = obj;
                } else {
                    detachDeviceItem.style.display = 'none';
                }
            }
            
            // Hide device style submenu for links
            const deviceStyleTrigger = document.getElementById('ctx-device-style');
            if (deviceStyleTrigger) deviceStyleTrigger.style.display = 'none';
            
            // Hide SSH address and discovery options for links
            const sshAddressItem = document.getElementById('ctx-ssh-address');
            const sshSeparator = document.getElementById('ctx-ssh-separator');
            const startDiscoveryItem = document.getElementById('ctx-start-discovery');
            const enableLldpItem = document.getElementById('ctx-enable-lldp');
            if (sshAddressItem) sshAddressItem.style.display = 'none';
            if (sshSeparator) sshSeparator.style.display = 'none';
            if (startDiscoveryItem) startDiscoveryItem.style.display = 'none';
            if (enableLldpItem) enableLldpItem.style.display = 'none';
        } else if (obj.type === 'device') {
            if (addTextItem) addTextItem.style.display = 'block';
            if (changeLabelItem) changeLabelItem.style.display = 'block';
            if (curveSubmenuTrigger) curveSubmenuTrigger.style.display = 'none';
            if (changeWidthItem) changeWidthItem.style.display = 'none';
            if (changeStyleItem) changeStyleItem.style.display = 'none';
            
            // Show device style submenu trigger
            const deviceStyleTrigger = document.getElementById('ctx-device-style');
            if (deviceStyleTrigger) {
                deviceStyleTrigger.style.display = 'block';
                // Store device reference for submenu
                editor._deviceStyleDevice = obj;
            }
            
            // Show SSH Address option for devices (at top of menu)
            const sshAddressItem = document.getElementById('ctx-ssh-address');
            const sshSeparator = document.getElementById('ctx-ssh-separator');
            const startDiscoveryItem = document.getElementById('ctx-start-discovery');
            
            if (sshAddressItem) {
                sshAddressItem.style.display = 'block';
                // Update text to show current SSH config if set
                const sshConfig = obj.sshConfig || {};
                const sshHost = sshConfig.host || obj.deviceAddress;
                if (sshHost && sshHost.trim()) {
                    const sshUser = sshConfig.user || 'dnroot';
                    sshAddressItem.innerHTML = `<span class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/><polyline points="7,8 9,10 7,12"/><line x1="11" y1="12" x2="15" y2="12"/></svg></span> SSH: ${sshUser}@${sshHost}`;
                } else {
                    sshAddressItem.innerHTML = `<span class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/><polyline points="7,8 9,10 7,12"/><line x1="11" y1="12" x2="15" y2="12"/></svg></span> Set SSH Address`;
                }
            }
            if (sshSeparator) sshSeparator.style.display = 'block';
            
            // Show "Start Topology Discovery" option only for termination devices (not DNAAS routers)
            if (startDiscoveryItem) {
                if (editor.isTerminationDevice(obj)) {
                    startDiscoveryItem.style.display = 'block';
                } else {
                    startDiscoveryItem.style.display = 'none';
                }
            }
            
            // Show Enable LLDP option for devices (same as SSH - for discovery)
            const enableLldpItem = document.getElementById('ctx-enable-lldp');
            if (enableLldpItem) enableLldpItem.style.display = 'block';
            
            // Show lock or unlock based on current state
            if (obj.locked) {
                if (lockItem) lockItem.style.display = 'none';
                if (unlockItem) unlockItem.style.display = 'block';
            } else {
                if (lockItem) lockItem.style.display = 'block';
                if (unlockItem) unlockItem.style.display = 'none';
            }
        } else if (obj.type === 'text') {
            if (addTextItem) addTextItem.style.display = 'none';
            if (changeLabelItem) changeLabelItem.style.display = 'none';
            if (curveSubmenuTrigger) curveSubmenuTrigger.style.display = 'none';
            if (changeWidthItem) changeWidthItem.style.display = 'none';
            if (changeStyleItem) changeStyleItem.style.display = 'none';
            
            // Hide device style submenu for text
            const deviceStyleTrigger = document.getElementById('ctx-device-style');
            if (deviceStyleTrigger) deviceStyleTrigger.style.display = 'none';
            
            // Hide SSH address and discovery options for text
            const sshAddressItem = document.getElementById('ctx-ssh-address');
            const sshSeparator = document.getElementById('ctx-ssh-separator');
            const startDiscoveryItem = document.getElementById('ctx-start-discovery');
            const enableLldpItem = document.getElementById('ctx-enable-lldp');
            if (sshAddressItem) sshAddressItem.style.display = 'none';
            if (sshSeparator) sshSeparator.style.display = 'none';
            if (startDiscoveryItem) startDiscoveryItem.style.display = 'none';
            if (enableLldpItem) enableLldpItem.style.display = 'none';
            
            // Show lock or unlock based on current state
            if (obj.locked) {
                if (lockItem) lockItem.style.display = 'none';
                if (unlockItem) unlockItem.style.display = 'block';
            } else {
                if (lockItem) lockItem.style.display = 'block';
                if (unlockItem) unlockItem.style.display = 'none';
            }
            
            // Show "Detach from Link" option if text is attached to a link
            const detachLinkItem = document.getElementById('ctx-detach-link');
            if (detachLinkItem) {
                if (obj.linkId) {
                    detachLinkItem.style.display = 'block';
                    const link = editor.objects.find(l => l.id === obj.linkId);
                    const linkName = link ? (link.id || 'Link') : 'Link';
                    detachLinkItem.innerHTML = `${appIcon('link')} Detach from ${linkName}`;
                } else {
                    detachLinkItem.style.display = 'none';
                }
            }
        } else if (obj.type === 'shape') {
            if (addTextItem) addTextItem.style.display = 'none';
            if (changeLabelItem) changeLabelItem.style.display = 'none';
            if (curveSubmenuTrigger) curveSubmenuTrigger.style.display = 'none';
            if (changeWidthItem) changeWidthItem.style.display = 'none';
            if (changeStyleItem) changeStyleItem.style.display = 'none';
            
            const deviceStyleTrigger = document.getElementById('ctx-device-style');
            if (deviceStyleTrigger) deviceStyleTrigger.style.display = 'none';
            const sshAddressItem = document.getElementById('ctx-ssh-address');
            const sshSeparator = document.getElementById('ctx-ssh-separator');
            const startDiscoveryItem = document.getElementById('ctx-start-discovery');
            const enableLldpItem = document.getElementById('ctx-enable-lldp');
            if (sshAddressItem) sshAddressItem.style.display = 'none';
            if (sshSeparator) sshSeparator.style.display = 'none';
            if (startDiscoveryItem) startDiscoveryItem.style.display = 'none';
            if (enableLldpItem) enableLldpItem.style.display = 'none';
            
            if (obj.locked) {
                if (lockItem) lockItem.style.display = 'none';
                if (unlockItem) unlockItem.style.display = 'block';
            } else {
                if (lockItem) lockItem.style.display = 'block';
                if (unlockItem) unlockItem.style.display = 'none';
            }
            
            const detachLinkItem = document.getElementById('ctx-detach-link');
            if (detachLinkItem) detachLinkItem.style.display = 'none';
        } else {
            // Hide detach option for non-text objects
            const detachLinkItem = document.getElementById('ctx-detach-link');
            if (detachLinkItem) detachLinkItem.style.display = 'none';
        }
    },

    _adjustMenuPosition(editor, x, y, menu) {
        const menuRect = menu.getBoundingClientRect();
        const menuWidth = menuRect.width || 200;
        const menuHeight = menuRect.height || 300;
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        let adjustedX = x;
        let adjustedY = y;
        
        // Check right edge
        if (x + menuWidth > viewportWidth - 10) {
            adjustedX = viewportWidth - menuWidth - 10;
        }
        // Check left edge
        if (adjustedX < 10) {
            adjustedX = 10;
        }
        // Check bottom edge
        if (y + menuHeight > viewportHeight - 10) {
            adjustedY = viewportHeight - menuHeight - 10;
        }
        // Check top edge
        if (adjustedY < 10) {
            adjustedY = 10;
        }
        
        return { x: adjustedX, y: adjustedY };
    },

    hideContextMenu(editor) {
        const menu = document.getElementById('context-menu');
        menu.style.display = 'none';
        editor.contextMenuVisible = false;
        // Also hide any related popups and submenus if open
        editor.hideColorPalettePopup();
        editor.hideWidthSliderPopup();
        editor.hideStyleOptionsPopup();
        editor.hideCurveSubmenu();
        editor.hideCurveModeSubmenu();
        editor.hideCurveMagnitudePopup();
        editor.hideLayersSubmenu();
        editor.hideDeviceStyleSubmenu();
    },

    handleContextCopyStyle(editor) {
        if (editor.selectedObject) {
            // Save object info before copyObjectStyle clears selection
            const objType = editor.selectedObject.type;
            const objLabel = editor.selectedObject.label || editor.selectedObject.text || editor.selectedObject.id;
            editor.copyObjectStyle(editor.selectedObject);
            if (editor.debugger) {
                editor.debugger.logSuccess(`🖌️ Style copied from ${objType}: ${objLabel}`);
            }
        }
            editor.hideContextMenu();
    },

    copyObjectStyle(editor, obj) {
        if (!obj) return;
        
        // Store ALL style properties - we'll apply what's applicable at paste time
        editor.copiedStyle = {
            type: obj.type,
            color: obj.color,
            // Device properties
            radius: obj.radius,
            deviceType: obj.deviceType,
            visualStyle: obj.visualStyle,
            labelColor: obj.labelColor, // Device label text color
            labelSize: obj.labelSize, // Device label size
            // Link properties
            style: obj.style,
            width: obj.width,
            curveOverride: obj.curveOverride,
            curveMagnitude: obj.curveMagnitude,
            // Text properties
            fontSize: obj.fontSize,
            fontFamily: obj.fontFamily,
            fontWeight: obj.fontWeight,
            fontStyle: obj.fontStyle,
            textDecoration: obj.textDecoration,
            showBackground: obj.showBackground,
            backgroundColor: obj.backgroundColor,
            bgColor: obj.bgColor,
            backgroundPadding: obj.backgroundPadding,
            backgroundOpacity: obj.backgroundOpacity,
            // Border properties (for text)
            showBorder: obj.showBorder,
            borderColor: obj.borderColor,
            borderStyle: obj.borderStyle,
            borderWidth: obj.borderWidth,
            // Text attached-to-link properties
            alwaysFaceUser: obj.alwaysFaceUser,
            // Shape properties
            shapeType: obj.shapeType,
            shapeWidth: obj.width,
            shapeHeight: obj.height,
            fillColor: obj.fillColor,
            fillOpacity: obj.fillOpacity,
            fillEnabled: obj.fillEnabled,
            strokeColor: obj.strokeColor,
            strokeWidth: obj.strokeWidth,
            strokeEnabled: obj.strokeEnabled
        };
        
        // Enter paste style mode
        editor.pasteStyleMode = true;
        
        // BUGFIX: Clear selection to prevent accidental dragging in paste mode
        // The object style is already copied, we don't need it selected anymore
        editor.selectedObject = null;
        editor.selectedObjects = [];
        editor.multiSelectMode = false;
        
        // Also clear any pending drag state
        editor.dragging = false;
        editor._pendingDrag = null;
        
        // Use 'copy' cursor for paste style mode (professional look)
        editor.canvas.style.cursor = 'copy';
        
        if (editor.showToast) {
            editor.showToast('Click objects to paste. Press Escape to cancel.', 'info');
        }
        if (editor.debugger) {
            const holdShiftMsg = editor.shiftPressed ? ' (Hold Shift for continuous paste)' : ' (Click to paste, hold Shift for multiple)';
            editor.debugger.logInfo(`PASTE MODE: Click on objects to apply style${holdShiftMsg}`);
        }
        
        editor.draw();
    },

    _applyStyleToObject(editor, obj) {
        if (!editor.copiedStyle || !obj) return;
        
        const sourceType = editor.copiedStyle.type;
        const objType = obj.type;
        const isLinkType = (t) => t === 'link' || t === 'unbound';
        
        // Check if types are compatible for full style copy
        const sameCategory = (sourceType === objType) || 
                            (isLinkType(sourceType) && isLinkType(objType));
        
        // ENHANCED: Cross-type Device <-> Text Box copying with smart color mapping
        const isDeviceToText = sourceType === 'device' && objType === 'text';
        const isTextToDevice = sourceType === 'text' && objType === 'device';
        
        if (isDeviceToText) {
            // Device → TB: Smart color mapping based on whether TB has background
            const tbHasBackground = obj.showBackground || obj.bgColor || obj.backgroundColor;
            
            if (tbHasBackground) {
                // TB has background: device color → TB bg, device labelColor → TB text color
                if (editor.copiedStyle.color !== undefined) {
                    obj.backgroundColor = editor.copiedStyle.color;
                    obj.bgColor = editor.copiedStyle.color;
                }
                if (editor.copiedStyle.labelColor !== undefined) {
                    obj.color = editor.copiedStyle.labelColor;
                } else {
                    obj.color = '#ffffff'; // Default to white text
                }
            } else {
                // TB has NO background: device color → TB text color
                if (editor.copiedStyle.color !== undefined) {
                    obj.color = editor.copiedStyle.color;
                }
            }
            // Copy font properties from device
            if (editor.copiedStyle.fontFamily !== undefined) obj.fontFamily = editor.copiedStyle.fontFamily;
            if (editor.copiedStyle.labelSize !== undefined) obj.fontSize = editor.copiedStyle.labelSize;
            if (editor.copiedStyle.fontWeight !== undefined) obj.fontWeight = editor.copiedStyle.fontWeight;
            if (editor.copiedStyle.fontStyle !== undefined) obj.fontStyle = editor.copiedStyle.fontStyle;
            return; // Don't process further
        }
        
        if (isTextToDevice) {
            // TB → Device: Smart color mapping based on whether TB has background
            const tbHadBackground = editor.copiedStyle.showBackground || 
                                    editor.copiedStyle.bgColor || 
                                    editor.copiedStyle.backgroundColor;
            
            if (tbHadBackground) {
                // TB had background: TB bg → device color, TB text color → device labelColor
                if (editor.copiedStyle.backgroundColor !== undefined) {
                    obj.color = editor.copiedStyle.backgroundColor;
                } else if (editor.copiedStyle.bgColor !== undefined) {
                    obj.color = editor.copiedStyle.bgColor;
                }
                if (editor.copiedStyle.color !== undefined) {
                    obj.labelColor = editor.copiedStyle.color;
                }
            } else {
                // TB had NO background: TB text color → device labelColor
                if (editor.copiedStyle.color !== undefined) {
                    obj.labelColor = editor.copiedStyle.color;
                }
            }
            // Copy font properties from TB
            if (editor.copiedStyle.fontFamily !== undefined) obj.fontFamily = editor.copiedStyle.fontFamily;
            if (editor.copiedStyle.fontSize !== undefined) {
                obj.labelSize = editor.copiedStyle.fontSize;
                obj.fontSize = editor.copiedStyle.fontSize;
            }
            if (editor.copiedStyle.fontWeight !== undefined) obj.fontWeight = editor.copiedStyle.fontWeight;
            if (editor.copiedStyle.fontStyle !== undefined) obj.fontStyle = editor.copiedStyle.fontStyle;
            return; // Don't process further
        }
        
        // CROSS-TYPE: TB → Link
        const isTextToLink = sourceType === 'text' && isLinkType(objType);
        if (isTextToLink) {
            const tbHadBackground = editor.copiedStyle.showBackground || 
                                    editor.copiedStyle.bgColor || 
                                    editor.copiedStyle.backgroundColor;
            if (tbHadBackground) {
                // TB had background: TB bg color → link color
                if (editor.copiedStyle.backgroundColor !== undefined) {
                    obj.color = editor.copiedStyle.backgroundColor;
                } else if (editor.copiedStyle.bgColor !== undefined) {
                    obj.color = editor.copiedStyle.bgColor;
                }
            } else {
                // TB had NO background: TB text color → link color
                if (editor.copiedStyle.color !== undefined) {
                    obj.color = editor.copiedStyle.color;
                }
            }
            // TB border style → link style (solid/dashed)
            if (editor.copiedStyle.borderStyle !== undefined) {
                obj.style = editor.copiedStyle.borderStyle;
            }
            // TB border width → link width
            if (editor.copiedStyle.borderWidth !== undefined) {
                obj.width = editor.copiedStyle.borderWidth;
            }
            return;
        }
        
        // CROSS-TYPE: Link → TB
        const isLinkToText = isLinkType(sourceType) && objType === 'text';
        if (isLinkToText) {
            const tbHasBackground = obj.showBackground || obj.bgColor || obj.backgroundColor;
            if (tbHasBackground) {
                // TB has bg: link color → TB bg color
                if (editor.copiedStyle.color !== undefined) {
                    obj.backgroundColor = editor.copiedStyle.color;
                    obj.bgColor = editor.copiedStyle.color;
                }
            } else {
                // TB has no bg: link color → TB text color
                if (editor.copiedStyle.color !== undefined) {
                    obj.color = editor.copiedStyle.color;
                }
            }
            // Link style → TB border style
            if (editor.copiedStyle.style !== undefined) {
                obj.borderStyle = editor.copiedStyle.style;
            }
            return;
        }
        
        // CROSS-TYPE: TB → Shape
        const isTextToShape = sourceType === 'text' && objType === 'shape';
        if (isTextToShape) {
            const tbHadBackground = editor.copiedStyle.showBackground || 
                                    editor.copiedStyle.bgColor || 
                                    editor.copiedStyle.backgroundColor;
            if (tbHadBackground) {
                // TB had bg: TB bg color → shape fill, TB border/text color → shape stroke
                if (editor.copiedStyle.backgroundColor !== undefined) {
                    obj.fillColor = editor.copiedStyle.backgroundColor;
                } else if (editor.copiedStyle.bgColor !== undefined) {
                    obj.fillColor = editor.copiedStyle.bgColor;
                }
                if (editor.copiedStyle.borderColor !== undefined) {
                    obj.strokeColor = editor.copiedStyle.borderColor;
                } else if (editor.copiedStyle.color !== undefined) {
                    obj.strokeColor = editor.copiedStyle.color;
                }
            } else {
                // TB had no bg: TB text color → shape fill and stroke
                if (editor.copiedStyle.color !== undefined) {
                    obj.fillColor = editor.copiedStyle.color;
                    obj.strokeColor = editor.copiedStyle.color;
                }
            }
            // TB border width → shape stroke width
            if (editor.copiedStyle.borderWidth !== undefined) {
                obj.strokeWidth = editor.copiedStyle.borderWidth;
            }
            return;
        }
        
        // CROSS-TYPE: Shape → TB
        const isShapeToText = sourceType === 'shape' && objType === 'text';
        if (isShapeToText) {
            const tbHasBackground = obj.showBackground || obj.bgColor || obj.backgroundColor;
            if (tbHasBackground) {
                // TB has bg: shape fill → TB bg, shape stroke → TB border/text color
                if (editor.copiedStyle.fillColor !== undefined) {
                    obj.backgroundColor = editor.copiedStyle.fillColor;
                    obj.bgColor = editor.copiedStyle.fillColor;
                }
                if (editor.copiedStyle.strokeColor !== undefined) {
                    obj.borderColor = editor.copiedStyle.strokeColor;
                }
            } else {
                // TB no bg: shape fill → TB text color
                if (editor.copiedStyle.fillColor !== undefined) {
                    obj.color = editor.copiedStyle.fillColor;
                } else if (editor.copiedStyle.strokeColor !== undefined) {
                    obj.color = editor.copiedStyle.strokeColor;
                }
            }
            // Shape stroke width → TB border width
            if (editor.copiedStyle.strokeWidth !== undefined) {
                obj.borderWidth = editor.copiedStyle.strokeWidth;
            }
            return;
        }
        
        // CROSS-TYPE: Shape → Device (color only)
        const isShapeToDevice = sourceType === 'shape' && objType === 'device';
        if (isShapeToDevice) {
            if (editor.copiedStyle.fillColor !== undefined) {
                obj.color = editor.copiedStyle.fillColor;
            }
            if (editor.copiedStyle.strokeColor !== undefined) {
                obj.labelColor = editor.copiedStyle.strokeColor;
            }
            return;
        }
        
        // CROSS-TYPE: Shape → Link (color only)
        const isShapeToLink = sourceType === 'shape' && isLinkType(objType);
        if (isShapeToLink) {
            if (editor.copiedStyle.fillColor !== undefined) {
                obj.color = editor.copiedStyle.fillColor;
            } else if (editor.copiedStyle.strokeColor !== undefined) {
                obj.color = editor.copiedStyle.strokeColor;
            }
            return;
        }
        
        // Standard same-type or compatible type copying
        // ALWAYS copy color - works between any object types
        if (editor.copiedStyle.color !== undefined) {
            obj.color = editor.copiedStyle.color;
        }
            
        // Apply type-specific properties based on TARGET type
        if (objType === 'device') {
            // Copy labelColor for device-to-device
            if (editor.copiedStyle.labelColor !== undefined) {
                obj.labelColor = editor.copiedStyle.labelColor;
            }
            if (editor.copiedStyle.labelSize !== undefined) {
                obj.labelSize = editor.copiedStyle.labelSize;
            }
            if (editor.copiedStyle.radius !== undefined && sameCategory) {
                obj.radius = editor.copiedStyle.radius;
            }
            if (editor.copiedStyle.visualStyle !== undefined && sameCategory) {
                const oldStyle = obj.visualStyle;
                obj.visualStyle = editor.copiedStyle.visualStyle;
                if (oldStyle !== editor.copiedStyle.visualStyle) {
                    editor.reconnectLinksToDevice(obj);
                }
            }
            // Copy font properties for device
            if (editor.copiedStyle.fontFamily !== undefined) obj.fontFamily = editor.copiedStyle.fontFamily;
            if (editor.copiedStyle.fontWeight !== undefined) obj.fontWeight = editor.copiedStyle.fontWeight;
            if (editor.copiedStyle.fontStyle !== undefined) obj.fontStyle = editor.copiedStyle.fontStyle;
        } else if (isLinkType(objType)) {
                    if (editor.copiedStyle.style !== undefined) {
                        obj.style = editor.copiedStyle.style;
                    }
                    if (editor.copiedStyle.width !== undefined) {
                        obj.width = editor.copiedStyle.width;
                    }
            if (sameCategory) {
                    if (editor.copiedStyle.curveOverride !== undefined) {
                        obj.curveOverride = editor.copiedStyle.curveOverride;
                    }
                    if (editor.copiedStyle.curveMagnitude !== undefined) {
                        obj.curveMagnitude = editor.copiedStyle.curveMagnitude;
                }
                    }
                } else if (objType === 'text') {
                    if (editor.copiedStyle.fontSize !== undefined) {
                        obj.fontSize = editor.copiedStyle.fontSize;
                    }
                    if (editor.copiedStyle.fontFamily !== undefined) {
                        obj.fontFamily = editor.copiedStyle.fontFamily;
                    }
                    if (editor.copiedStyle.fontWeight !== undefined) {
                        obj.fontWeight = editor.copiedStyle.fontWeight;
                    }
                    if (editor.copiedStyle.fontStyle !== undefined) {
                        obj.fontStyle = editor.copiedStyle.fontStyle;
                    }
                    if (editor.copiedStyle.textDecoration !== undefined) {
                        obj.textDecoration = editor.copiedStyle.textDecoration;
                    }
                    if (editor.copiedStyle.showBackground !== undefined) {
                        obj.showBackground = editor.copiedStyle.showBackground;
                    }
                    if (editor.copiedStyle.backgroundColor !== undefined) {
                        obj.backgroundColor = editor.copiedStyle.backgroundColor;
                    }
            if (editor.copiedStyle.bgColor !== undefined) {
                obj.bgColor = editor.copiedStyle.bgColor;
            }
                    if (editor.copiedStyle.backgroundPadding !== undefined) {
                        obj.backgroundPadding = editor.copiedStyle.backgroundPadding;
                    }
            if (editor.copiedStyle.backgroundOpacity !== undefined) {
                obj.backgroundOpacity = editor.copiedStyle.backgroundOpacity;
            }
            // Border properties
            if (editor.copiedStyle.showBorder !== undefined) {
                obj.showBorder = editor.copiedStyle.showBorder;
            }
            if (editor.copiedStyle.borderColor !== undefined) {
                obj.borderColor = editor.copiedStyle.borderColor;
            }
            if (editor.copiedStyle.borderStyle !== undefined) {
                obj.borderStyle = editor.copiedStyle.borderStyle;
            }
            if (editor.copiedStyle.borderWidth !== undefined) {
                obj.borderWidth = editor.copiedStyle.borderWidth;
            }
            // Face User property (link-attached TB)
            if (editor.copiedStyle.alwaysFaceUser !== undefined) {
                obj.alwaysFaceUser = editor.copiedStyle.alwaysFaceUser;
            }
        } else if (objType === 'shape') {
            if (editor.copiedStyle.fillColor !== undefined) {
                obj.fillColor = editor.copiedStyle.fillColor;
            }
            if (editor.copiedStyle.strokeColor !== undefined) {
                obj.strokeColor = editor.copiedStyle.strokeColor;
            }
            // Also apply general color to shape fill/stroke if copying from non-shape
            if (editor.copiedStyle.color !== undefined && editor.copiedStyle.fillColor === undefined) {
                obj.fillColor = editor.copiedStyle.color;
                obj.strokeColor = editor.copiedStyle.color;
            }
            // Shape → Shape same shapeType: also copy size
            if (sourceType === 'shape' && editor.copiedStyle.shapeType === obj.shapeType) {
                if (editor.copiedStyle.shapeWidth !== undefined) {
                    obj.width = editor.copiedStyle.shapeWidth;
                }
                if (editor.copiedStyle.shapeHeight !== undefined) {
                    obj.height = editor.copiedStyle.shapeHeight;
                }
            }
        }
    },

    pasteStyleToObject(editor, targetObj) {
        if (!editor.copiedStyle || !targetObj) return false;
        
        const sourceType = editor.copiedStyle.type;
        const targetType = targetObj.type;
        const isLinkType = (t) => t === 'link' || t === 'unbound';
        
        // Check if types are compatible for full style copy
        const sameCategory = (sourceType === targetType) || 
                            (isLinkType(sourceType) && isLinkType(targetType));
        
        // Apply style
        editor.saveState();
        
        // ENHANCED: If target is a UL that's part of a BUL, apply style to ALL links in the chain
        let targetsToStyle = [targetObj];
        if (targetObj.type === 'unbound' && (targetObj.mergedWith || targetObj.mergedInto)) {
            targetsToStyle = editor.getAllMergedLinks(targetObj);
        }
        
        // Apply style to all targets using helper
        targetsToStyle.forEach(obj => {
            editor._applyStyleToObject(obj);
        });
        
        // Log appropriate message
        if (editor.debugger) {
            const isBul = targetsToStyle.length > 1;
            if (sameCategory) {
                if (isBul) {
                    editor.debugger.logSuccess(`🖌️ Full style pasted to BUL (${targetsToStyle.length} links)`);
                } else {
                    editor.debugger.logSuccess(`🖌️ Full style pasted to ${targetObj.label || targetObj.type}`);
                }
            } else {
                if (isBul) {
                    editor.debugger.logSuccess(`🎨 Color pasted to BUL (${targetsToStyle.length} links) (different type: ${sourceType} → ${targetType})`);
                } else {
                    editor.debugger.logSuccess(`🎨 Color pasted to ${targetObj.label || targetObj.type} (different type: ${sourceType} → ${targetType})`);
                }
            }
        }
        
        editor.draw();
        return true;
    },

    exitPasteStyleMode(editor) {
        editor.pasteStyleMode = false;
        editor.csmsMode = false; // Also clear CS-MS mode
        
        // Clear CS-MS animation frame if running
        if (editor._csmsAnimationFrame) {
            cancelAnimationFrame(editor._csmsAnimationFrame);
            editor._csmsAnimationFrame = null;
        }
        
        editor.canvas.style.cursor = 'default';
        editor.setMode('base');
        
        if (editor.showToast) {
            editor.showToast('Copy Style cancelled', 'info');
        }
        if (editor.debugger) {
            editor.debugger.logInfo(`🖌️ Exited paste style mode`);
        }
        
        editor.draw();
    },

    handleContextDuplicate(editor) {
        if (editor.selectedObject) {
            editor.duplicateObject(editor.selectedObject, false);
        }
        editor.hideContextMenu();
    },

    showAdjacentTextMenu(editor, link) {
        const device1 = link.device1 ? editor.objects.find(obj => obj.id === link.device1) : null;
        const device2 = link.device2 ? editor.objects.find(obj => obj.id === link.device2) : null;
        
        if (!device1 && !device2) {
            // Unbound link - just add text in middle
            const text = prompt('Enter text label:', 'Label');
            if (text !== null && text.trim() !== '') {
                editor.addAdjacentText(link, 'middle', text.trim());
            }
            return;
        }
        
        // Check existing texts for this link
        const existingTexts = editor.objects.filter(obj => 
            obj.type === 'text' && obj.linkId === link.id
        );
        const existingPositions = existingTexts.map(t => t.position);
        
        // Get position for menu placement (use stored context menu position or fallback)
        const mouseX = editor._contextMenuX || window.innerWidth / 2;
        const mouseY = editor._contextMenuY || window.innerHeight / 2;
        
        // Create styled menu dynamically
        const menu = document.createElement('div');
        menu.className = 'context-menu';
        menu.id = 'adjacent-text-menu';
        menu.style.display = 'block';
        menu.style.position = 'fixed';
        menu.style.left = mouseX + 'px';
        menu.style.top = mouseY + 'px';
        menu.style.zIndex = '10001';
        menu.style.minWidth = '200px';
        
        const device1Name = device1 ? (device1.label || 'Device 1') : 'Start';
        const device2Name = device2 ? (device2.label || 'Device 2') : 'End';
        
        // Check if positions already exist (simplified to 2 per link)
        const hasDevice1 = existingPositions.some(p => p && p.startsWith('device1'));
        const hasDevice2 = existingPositions.some(p => p && p.startsWith('device2'));
        
        menu.innerHTML = `
            <div style="padding: 10px 16px; font-weight: bold; border-bottom: 2px solid #3498db; color: #2c3e50; background: #ecf0f1;">
                📝 Add Interface Label
            </div>
            <div class="context-menu-item ${hasDevice1 ? 'disabled' : ''}" data-position="device1" style="${hasDevice1 ? 'opacity: 0.5; cursor: not-allowed;' : ''}">
                📍 Near ${device1Name} ${hasDevice1 ? '✓' : ''}
            </div>
            ${device2 ? `
            <div class="context-menu-item ${hasDevice2 ? 'disabled' : ''}" data-position="device2" style="${hasDevice2 ? 'opacity: 0.5; cursor: not-allowed;' : ''}">
                📍 Near ${device2Name} ${hasDevice2 ? '✓' : ''}
            </div>
            ` : ''}
        `;
        
        document.body.appendChild(menu);
        
        // Add click handlers
        menu.querySelectorAll('.context-menu-item').forEach(item => {
            item.addEventListener('click', (e) => {
                // Use closest() to handle clicks on child elements (emojis, text nodes)
                const menuItem = e.target.closest('.context-menu-item');
                if (!menuItem) return;
                
                const position = menuItem.getAttribute('data-position');
                const isDisabled = menuItem.classList.contains('disabled') || menuItem.innerHTML.includes('ico-check');
                
                if (position && !isDisabled) {
                    // Prompt for text input
                    const deviceName = position === 'device1' ? device1Name : device2Name;
                    const text = prompt(`Enter label near ${deviceName}:`, '');
                    
                    // Remove menu first (before checking text validity)
                        if (document.body.contains(menu)) {
                            document.body.removeChild(menu);
                        }
                    
                    if (text !== null && text.trim() !== '') {
                        editor.addAdjacentText(link, position, text.trim());
                        editor.draw();
                    }
                }
            });
        });
        
        // Close menu on outside click
        setTimeout(() => {
            document.addEventListener('click', function closeMenu(e) {
                if (!menu.contains(e.target)) {
                    if (document.body.contains(menu)) {
                        document.body.removeChild(menu);
                    }
                    document.removeEventListener('click', closeMenu);
                }
            });
        }, 100);
    },

    handleContextCurveMPs(editor) {
        // Toggle curve MPs for BUL chains from context menu
        editor.curveMPs = !editor.curveMPs;
        
        if (editor.debugger) {
            editor.debugger.logSuccess(`〰️ Curve MPs: ${editor.curveMPs ? 'ON' : 'OFF'}`);
        }
        
        editor.draw();
        editor.hideContextMenu();
    },

    showCurveSubmenu(editor) {
        const trigger = document.getElementById('ctx-curve');
        const submenu = document.getElementById('ctx-curve-submenu');
        
        if (!trigger || !submenu) return;
        
        const rect = trigger.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // Position submenu to the right of the trigger
        let left = rect.right - 4;
        let top = rect.top;
        
        // Get submenu dimensions (temporarily show to measure)
        submenu.style.display = 'block';
        const submenuRect = submenu.getBoundingClientRect();
        
        // Adjust if would overflow right edge
        if (left + submenuRect.width > viewportWidth - 10) {
            left = rect.left - submenuRect.width + 4;
        }
        
        // Adjust if would overflow bottom edge
        if (top + submenuRect.height > viewportHeight - 10) {
            top = viewportHeight - submenuRect.height - 10;
        }
        
        submenu.style.left = left + 'px';
        submenu.style.top = top + 'px';
        
        // Update submenu items based on link state
        editor.updateCurveSubmenuItems();
    },

    updateCurveSubmenuItems(editor) {
        const obj = editor._curveSubmenuLink || editor.selectedObject;
        if (!obj || (obj.type !== 'link' && obj.type !== 'unbound')) return;
        
        // Determine effective curve state
        const effectiveCurveMode = obj.curveMode || (editor.linkCurveMode ? editor.globalCurveMode : 'off');
        const curveEnabled = effectiveCurveMode !== 'off' && (obj.curveOverride !== false);
        
        // Curve Mode trigger - show current mode
        const modeTrigger = document.getElementById('ctx-curve-mode-trigger');
        if (modeTrigger) {
            let modeLabel = 'Global';
            if (obj.curveMode === 'auto') modeLabel = 'Auto';
            else if (obj.curveMode === 'manual') modeLabel = 'Manual';
            else if (obj.curveMode === 'off' || obj.curveOverride === false) modeLabel = 'Off';
            modeTrigger.innerHTML = `${appIcon('curve')} Curve Mode: ${modeLabel} ▶`;
        }
        
        // Keep curve item
        const keepItem = document.getElementById('ctx-keep-curve');
        if (keepItem) {
            if (obj.type === 'unbound' && curveEnabled) {
                keepItem.style.display = 'block';
                keepItem.innerHTML = obj.keepCurve ? `${appIcon('lock')} ${appIcon('check')} Keep Current Curve` : `${appIcon('unlock')} Keep Current Curve`;
            } else {
                keepItem.style.display = 'none';
            }
        }
        
        // Curve magnitude item
        const magnitudeItem = document.getElementById('ctx-curve-magnitude');
        if (magnitudeItem) {
            if (curveEnabled) {
                magnitudeItem.style.display = 'block';
                const magnitude = obj.curveMagnitude || 0;
                magnitudeItem.innerHTML = magnitude > 0 ? `${appIcon('curve')} Curve: ${magnitude}` : `${appIcon('curve')} Curve Magnitude`;
            } else {
                magnitudeItem.style.display = 'none';
            }
        }
        
        // Curve MPs item (BUL only)
        const mpsItem = document.getElementById('ctx-curve-mps');
        if (mpsItem) {
            const isBUL = obj.type === 'unbound' && (obj.mergedWith || obj.mergedInto);
            if (isBUL && curveEnabled) {
                mpsItem.style.display = 'block';
                mpsItem.innerHTML = editor.curveMPs ? `${appIcon('curve')} ${appIcon('check')} Curve MPs: ON` : `${appIcon('curve')} Curve MPs: OFF`;
            } else {
                mpsItem.style.display = 'none';
            }
        }
    },

    hideCurveSubmenu(editor) {
        const submenu = document.getElementById('ctx-curve-submenu');
        if (submenu) submenu.style.display = 'none';
    },

    hideCurveSubmenuIfNotHovered(editor) {
        const submenu = document.getElementById('ctx-curve-submenu');
        const trigger = document.getElementById('ctx-curve');
        // Only hide if neither the submenu nor its trigger are being hovered
        if (submenu && !submenu.matches(':hover') && (!trigger || !trigger.matches(':hover'))) {
            submenu.style.display = 'none';
        }
    },

    showCurveModeSubmenu(editor) {
        const trigger = document.getElementById('ctx-curve-mode-trigger');
        const submenu = document.getElementById('ctx-curve-mode-submenu');
        
        if (!trigger || !submenu) return;
        
        const rect = trigger.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // Position submenu to the right of the trigger
        let left = rect.right - 4;
        let top = rect.top;
        
        // Get submenu dimensions (temporarily show to measure)
        submenu.style.display = 'block';
        const submenuRect = submenu.getBoundingClientRect();
        
        // Adjust if would overflow right edge
        if (left + submenuRect.width > viewportWidth - 10) {
            left = rect.left - submenuRect.width + 4;
        }
        
        // Adjust if would overflow bottom edge
        if (top + submenuRect.height > viewportHeight - 10) {
            top = viewportHeight - submenuRect.height - 10;
        }
        
        submenu.style.left = left + 'px';
        submenu.style.top = top + 'px';
        
        // Update checkmarks based on current link's curve mode
        editor.updateCurveModeSubmenuItems();
    },

    hideCurveModeSubmenu(editor) {
        const submenu = document.getElementById('ctx-curve-mode-submenu');
        if (submenu) submenu.style.display = 'none';
    },

    hideCurveModeSubmenuIfNotHovered(editor) {
        const submenu = document.getElementById('ctx-curve-mode-submenu');
        const trigger = document.getElementById('ctx-curve-mode-trigger');
        // Only hide if neither the submenu nor its trigger are being hovered
        if (submenu && !submenu.matches(':hover') && (!trigger || !trigger.matches(':hover'))) {
            submenu.style.display = 'none';
        }
    },

    updateCurveModeSubmenuItems(editor) {
        const obj = editor._curveSubmenuLink || editor.selectedObject;
        if (!obj || (obj.type !== 'link' && obj.type !== 'unbound')) return;
        
        // Determine effective curve mode - curveOverride=false means 'off'
        let curveMode = obj.curveMode || null; // null = use global
        if (obj.curveOverride === false && !obj.curveMode) {
            curveMode = 'off';
        }
        
        // Update checkmarks
        const globalItem = document.getElementById('ctx-curve-mode-global');
        const autoItem = document.getElementById('ctx-curve-mode-auto');
        const manualItem = document.getElementById('ctx-curve-mode-manual');
        const offItem = document.getElementById('ctx-curve-mode-off');
        
        const check = '✓ ';
        
        // Global is selected only if no per-link override is set
        const isGlobal = obj.curveMode === undefined && obj.curveOverride === undefined;
        
        if (globalItem) {
            globalItem.innerHTML = `<span class="ico">🌐</span> ${isGlobal ? check : ''}Use Global Setting`;
        }
        if (autoItem) {
            autoItem.innerHTML = `<span class="ico">🧲</span> ${curveMode === 'auto' ? check : ''}Auto (Magnetic)`;
        }
        if (manualItem) {
            manualItem.innerHTML = `<span class="ico">✋</span> ${curveMode === 'manual' ? check : ''}Manual (Draggable)`;
        }
        if (offItem) {
            offItem.innerHTML = `<span class="ico">➖</span> ${curveMode === 'off' || obj.curveOverride === false ? check : ''}Off (Straight)`;
        }
    },

    handleContextCurveModeChange(editor, mode) {
        // Get the target link(s)
        const targetLink = editor._curveSubmenuLink || editor.selectedObject;
        const selectedLinks = editor.selectedObjects.filter(obj => obj.type === 'link' || obj.type === 'unbound');
        
        editor.saveState();
        
        // Helper function for SEAMLESS curve mode transitions
        // Strategy: Preserve curve data across modes, only capture when needed
        const captureCurrentCurveShape = (link) => {
            const currentMode = editor.getEffectiveCurveMode(link);
            
            // Switching TO MANUAL: Ensure we have a manualCurvePoint
            if (mode === 'manual') {
                // PRIORITY 1: Check for attached middle text box - use its position
                const attachedMiddleText = editor.objects.find(obj => 
                    obj.type === 'text' && obj.linkId === link.id && obj.position === 'middle'
                );
                if (attachedMiddleText) {
                    link.manualCurvePoint = { x: attachedMiddleText.x, y: attachedMiddleText.y };
                    link.manualControlPoint = { x: attachedMiddleText.x, y: attachedMiddleText.y };
                    if (editor.debugger) {
                        editor.debugger.logInfo(`   📌 →Manual: Using attached TB position at (${Math.round(attachedMiddleText.x)}, ${Math.round(attachedMiddleText.y)})`);
                    }
                    return;
                }
                
                // PRIORITY 2: If already has manualCurvePoint, keep it (seamless switch back)
                if (link.manualCurvePoint) {
                    if (editor.debugger) {
                        editor.debugger.logInfo(`   📌 →Manual: Kept existing curve at (${Math.round(link.manualCurvePoint.x)}, ${Math.round(link.manualCurvePoint.y)})`);
                    }
                    return;
                }
                
                // PRIORITY 3: Try to capture from keepCurve data (if switching back from Auto with keepCurve)
                if (link.keepCurve && link.savedCurveOffset && link._renderedEndpoints) {
                    const midX = (link._renderedEndpoints.startX + link._renderedEndpoints.endX) / 2;
                    const midY = (link._renderedEndpoints.startY + link._renderedEndpoints.endY) / 2;
                    const linkLength = Math.sqrt(
                        Math.pow(link._renderedEndpoints.endX - link._renderedEndpoints.startX, 2) + 
                        Math.pow(link._renderedEndpoints.endY - link._renderedEndpoints.startY, 2)
                    ) || 1;
                    
                    // Reconstruct control point from saved offset
                    const cpX = midX + link.savedCurveOffset.cp1OffsetX * linkLength;
                    const cpY = midY + link.savedCurveOffset.cp1OffsetY * linkLength;
                    
                    // Convert control point to visual midpoint (t=0.5)
                    // For bezier: M = 0.125*P0 + 0.75*cp + 0.125*P1
                    const visualMidX = 0.125 * link._renderedEndpoints.startX + 0.75 * cpX + 0.125 * link._renderedEndpoints.endX;
                    const visualMidY = 0.125 * link._renderedEndpoints.startY + 0.75 * cpY + 0.125 * link._renderedEndpoints.endY;
                    
                    link.manualCurvePoint = { x: visualMidX, y: visualMidY };
                    if (editor.debugger) {
                        editor.debugger.logInfo(`   📌 KeepCurve→Manual: Restored curve at (${Math.round(visualMidX)}, ${Math.round(visualMidY)})`);
                    }
                    return;
                }
                
                // PRIORITY 4: Capture from current auto curve
                if (currentMode === 'auto' || currentMode === 'off') {
                    const autoCurvePoint = editor.getAutoCurveMidpoint(link);
                    if (autoCurvePoint) {
                        link.manualCurvePoint = { x: autoCurvePoint.x, y: autoCurvePoint.y };
                        if (editor.debugger) {
                            editor.debugger.logInfo(`   📌 Auto→Manual: Captured curve at (${Math.round(autoCurvePoint.x)}, ${Math.round(autoCurvePoint.y)})`);
                        }
                    } else {
                        // FALLBACK: If no auto curve to capture, create a default curve position
                        // Use the link's midpoint with a slight offset to make it visible
                        const endpoints = editor.getLinkEndpoints(link);
                        if (endpoints) {
                            const midX = (endpoints.startX + endpoints.endX) / 2;
                            const midY = (endpoints.startY + endpoints.endY) / 2;
                            // Add a small perpendicular offset so the curve handle is visible
                            const dx = endpoints.endX - endpoints.startX;
                            const dy = endpoints.endY - endpoints.startY;
                            const len = Math.sqrt(dx * dx + dy * dy) || 1;
                            const perpX = -dy / len * 30; // 30px perpendicular offset
                            const perpY = dx / len * 30;
                            link.manualCurvePoint = { x: midX + perpX, y: midY + perpY };
                            if (editor.debugger) {
                                editor.debugger.logInfo(`   📌 →Manual: Created default curve at (${Math.round(midX + perpX)}, ${Math.round(midY + perpY)})`);
                            }
                        }
                    }
                }
            }
            // Switching TO AUTO: Clear keepCurve so auto mode calculates naturally
            // manualCurvePoint is preserved for switching back to Manual later
            else if (mode === 'auto') {
                // Clear keepCurve - let auto mode work naturally with magnetic repulsion
                delete link.keepCurve;
                delete link.savedCurveOffset;
                // DON'T delete manualCurvePoint - preserve it for switching back
                if (editor.debugger) {
                    editor.debugger.logInfo(`   📌 →Auto: Cleared keepCurve, auto mode active (manualCurvePoint preserved)`);
                }
            }
            // OFF → anything or anything → OFF: Nothing special to capture
        };
        
        if (selectedLinks.length > 0) {
            // Apply to all selected links
            selectedLinks.forEach(link => {
                // Capture current curve shape BEFORE changing mode (seamless transition)
                captureCurrentCurveShape(link);
                
                if (mode === null) {
                    delete link.curveMode;
                } else {
                    link.curveMode = mode;
                }
                
                // If switching to off, disable curve override too
                if (mode === 'off') {
                    link.curveOverride = false;
                } else if (mode === 'auto' || mode === 'manual') {
                    link.curveOverride = true;
                } else if (mode === null) {
                    delete link.curveOverride;
                }
                
                // Clear curve data when switching to OFF mode (complete reset)
                // Note: When switching to AUTO, captureCurrentCurveShape already handles converting to keepCurve
                if (mode === 'off') {
                    delete link.manualCurvePoint;
                    delete link.manualControlPoint;
                    delete link.keepCurve;
                    delete link.savedCurveOffset;
                }
            });
            
            if (editor.debugger) {
                const modeLabel = mode === null ? 'Global' : mode.charAt(0).toUpperCase() + mode.slice(1);
                editor.debugger.logSuccess(`🌊 Curve mode set to ${modeLabel} for ${selectedLinks.length} links`);
            }
        } else if (targetLink && (targetLink.type === 'link' || targetLink.type === 'unbound')) {
            // Capture current curve shape BEFORE changing mode (seamless transition)
            captureCurrentCurveShape(targetLink);
            
            // Single link
            if (mode === null) {
                delete targetLink.curveMode;
                delete targetLink.curveOverride;
            } else {
                targetLink.curveMode = mode;
                if (mode === 'off') {
                    targetLink.curveOverride = false;
                } else {
                    targetLink.curveOverride = true;
                }
            }
            
            // Clear curve data when switching to OFF mode (complete reset)
            // Note: When switching to AUTO, captureCurrentCurveShape already handles converting to keepCurve
            if (mode === 'off') {
                delete targetLink.manualCurvePoint;
                delete targetLink.manualControlPoint;
                delete targetLink.keepCurve;
                delete targetLink.savedCurveOffset;
            }
            
            if (editor.debugger) {
                const modeLabel = mode === null ? 'Global' : mode.charAt(0).toUpperCase() + mode.slice(1);
                editor.debugger.logSuccess(`🌊 Curve mode set to ${modeLabel} for link`);
            }
        }
        
        // CRITICAL: Clear any hover/drag state to prevent accidental drag after mode change
        editor.hoveredLinkMidpoint = null;
        editor.draggingCurveHandle = null;
        editor._potentialCPDrag = null;
        editor._curveSubmenuLink = null;
        editor.dragging = false;
        editor.stretchingLink = null;
        
        editor.hideContextMenu();
        
        // CRITICAL: Draw first to compute _cp1/_cp2 for the new curve mode
        editor.draw();
        
        // ENHANCED: Update all text boxes attached to affected links
        // This ensures TBs move to their correct positions after curve mode change
        const affectedLinks = selectedLinks.length > 0 ? selectedLinks : 
            (targetLink ? [targetLink] : []);
        
        for (const link of affectedLinks) {
            const attachedTexts = editor.objects.filter(obj => 
                obj.type === 'text' && obj.linkId === link.id
            );
            for (const textObj of attachedTexts) {
                editor.updateAdjacentTextPosition(textObj);
            }
        }
        
        // Redraw after TB position updates
        if (affectedLinks.length > 0) {
            editor.draw();
        }
        
        editor.scheduleAutoSave();
    },

    showLayersSubmenu(editor) {
        const trigger = document.getElementById('ctx-layers');
        const submenu = document.getElementById('ctx-layers-submenu');
        
        if (!trigger || !submenu) return;
        
        const rect = trigger.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // Position submenu to the right of the trigger
        let left = rect.right - 4;
        let top = rect.top;
        
        submenu.style.display = 'block';
        const submenuRect = submenu.getBoundingClientRect();
        
        // Adjust if would overflow right edge
        if (left + submenuRect.width > viewportWidth - 10) {
            left = rect.left - submenuRect.width + 4;
        }
        
        // Adjust if would overflow bottom edge
        if (top + submenuRect.height > viewportHeight - 10) {
            top = viewportHeight - submenuRect.height - 10;
        }
        
        submenu.style.left = left + 'px';
        submenu.style.top = top + 'px';
        
        // Update layer number display with more info
        const layerNumber = document.getElementById('ctx-layer-number');
        if (layerNumber && editor.selectedObject) {
            const currentLayer = editor.getObjectLayer(editor.selectedObject);
            const hasCustomLayer = editor.selectedObject.layer !== undefined;
            
            // Show layer with default indicator if using type default
            if (hasCustomLayer) {
                layerNumber.textContent = currentLayer;
            } else {
                // Show default layer for type (uses centralized function)
                const defaultLayer = editor.getDefaultLayerForType(editor.selectedObject.type);
                layerNumber.textContent = `${defaultLayer} (default)`;
            }
        }
        
        // Update reset button visibility
        const resetBtn = document.getElementById('ctx-layer-reset');
        if (resetBtn && editor.selectedObject) {
            const hasCustomLayer = editor.selectedObject.layer !== undefined;
            resetBtn.style.opacity = hasCustomLayer ? '1' : '0.5';
            resetBtn.style.pointerEvents = hasCustomLayer ? 'auto' : 'none';
        }
    },

    hideLayersSubmenu(editor) {
        const submenu = document.getElementById('ctx-layers-submenu');
        if (submenu) submenu.style.display = 'none';
    },

    hideLayersSubmenuIfNotHovered(editor) {
        const submenu = document.getElementById('ctx-layers-submenu');
        if (submenu && !submenu.matches(':hover')) {
            submenu.style.display = 'none';
        }
    },

    showDeviceStyleSubmenu(editor) {
        const trigger = document.getElementById('ctx-device-style');
        const submenu = document.getElementById('ctx-device-style-submenu');
        
        if (!trigger || !submenu) return;
        
        const rect = trigger.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // Position submenu to the right of the trigger
        let left = rect.right - 4;
        let top = rect.top;
        
        submenu.style.display = 'block';
        const submenuRect = submenu.getBoundingClientRect();
        
        // Adjust if would overflow right edge
        if (left + submenuRect.width > viewportWidth - 10) {
            left = rect.left - submenuRect.width + 4;
        }
        
        // Adjust if would overflow bottom edge
        if (top + submenuRect.height > viewportHeight - 10) {
            top = viewportHeight - submenuRect.height - 10;
        }
        
        submenu.style.left = left + 'px';
        submenu.style.top = top + 'px';
        
        // Update current style display
        const currentStyleSpan = document.getElementById('ctx-style-current');
        if (currentStyleSpan && editor._deviceStyleDevice) {
            const styleNames = {
                'circle': 'Circle',
                'classic': 'Classic Router',
                'simple': 'Simple Router',
                'server': 'Server Tower',
                'hex': 'Hex Router',
            };
            currentStyleSpan.textContent = styleNames[editor._deviceStyleDevice.visualStyle || 'circle'] || 'Circle';
        }
    },

    hideDeviceStyleSubmenu(editor) {
        const submenu = document.getElementById('ctx-device-style-submenu');
        if (submenu) submenu.style.display = 'none';
    },

    hideDeviceStyleSubmenuIfNotHovered(editor) {
        const submenu = document.getElementById('ctx-device-style-submenu');
        if (submenu && !submenu.matches(':hover')) {
            submenu.style.display = 'none';
        }
    },

    setDeviceVisualStyle(editor, style) {
        if (!editor._deviceStyleDevice) return;
        
        editor.saveState(); // Make style change undoable
        const device = editor._deviceStyleDevice;
        device.visualStyle = style;
        
        // Auto-reconnect: Update all links connected to this device
        editor.reconnectLinksToDevice(device);
        
        if (editor.debugger) {
            const styleNames = {
                'circle': 'Circle',
                'classic': 'Classic Router',
                'simple': 'Simple Router',
                'server': 'Server Tower',
                'hex': 'Hex Router',
            };
            editor.debugger.logSuccess(`📡 Device style changed to: ${styleNames[style] || style}`);
        }
        
        editor.hideContextMenu();
        editor.hideDeviceStyleSubmenu();
        editor.draw();
    },

    selectStyleAndEnterPlacementMode(editor, style) {
        // Set the default device style for new devices
        editor.defaultDeviceStyle = style;
        localStorage.setItem('defaultDeviceStyle', style);
        
        // Close context menu and submenu
        editor.hideContextMenu();
        editor.hideDeviceStyleSubmenu();
        
        // Enter router placement mode
        editor.setDevicePlacementMode('router');
        
        // Update HUD to show selected style
        const styleNames = {
            'circle': 'Circle',
            'classic': 'Cylinder',
            'simple': 'Schematic',
            'server': 'Tower',
            'hex': 'Hexagon',
        };
        
        // Update mode indicator with style info
        editor.updateModeIndicator();
        
        if (editor.debugger) {
            editor.debugger.logSuccess(`${appIcon('router')} Placing ${styleNames[style] || style} devices - click to place`);
        }
        
        editor.draw();
    }
};

console.log('[topology-context-menu-handlers.js] ContextMenuHandlers loaded');
