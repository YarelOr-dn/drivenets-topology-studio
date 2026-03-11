/**
 * topology-mouse-move.js - handleMouseMove handler
 * 
 * Extracted from topology-mouse.js for modular architecture.
 */

'use strict';

window.MouseMoveHandler = {
    _rotatedCursor(handleId, rotationDeg) {
        const cursors = ['ns-resize', 'nesw-resize', 'ew-resize', 'nwse-resize'];
        const handleAngles = { n: 0, ne: 45, e: 90, se: 135, s: 180, sw: 225, w: 270, nw: 315 };
        const baseAngle = handleAngles[handleId];
        if (baseAngle === undefined) return 'nwse-resize';
        const total = ((baseAngle + (rotationDeg || 0)) % 360 + 360) % 360;
        const idx = Math.round(total / 45) % 4;
        return cursors[idx];
    },

    handleMouseMove(editor, e) {
        // Store screen coordinates (logical/CSS pixels) for zoom operations
        const rect = editor.canvas.getBoundingClientRect();
        editor.lastMouseScreen = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };

        // If pointer is off-canvas and no active interaction, skip processing
        const offCanvas = e.clientX < rect.left || e.clientX > rect.right ||
                          e.clientY < rect.top  || e.clientY > rect.bottom;
        const hasActiveInteraction = editor.panning || editor.dragging || editor.isDragging ||
            editor._pendingDrag || editor.resizingDevice || editor.rotatingDevice ||
            editor.isDrawingLink || editor.draggingCurveHandle || editor.draggingAttachedText ||
            editor.draggingBULChain || editor.selectionBox || editor.isDrawingRuler;
        if (offCanvas && !hasActiveInteraction) return;
        
        // CRITICAL: Don't process mouse movements when context menu is visible
        // This prevents accidental dragging of objects while menu is open
        if (editor.contextMenuVisible) {
            return;
        }
        
        // Cancel long press if mouse moves
        if (editor.longPressTimer) {
            clearTimeout(editor.longPressTimer);
            editor.longPressTimer = null;
        }
        
        // Cancel move long-press if mouse moves before timer completes
        if (editor.moveLongPressTimer && !editor.dragging) {
            const pos = editor.getMousePos(e);
            const dx = pos.x - editor.lastMousePos?.x || 0;
            const dy = pos.y - editor.lastMousePos?.y || 0;
            const moveDist = Math.sqrt(dx * dx + dy * dy);
            
            // If moved more than 5 pixels, cancel long-press timer
            if (moveDist > 5) {
                clearTimeout(editor.moveLongPressTimer);
                editor.moveLongPressTimer = null;
            }
        }
        
        // Cancel resize long-press if mouse moves away from handle
        if (editor.resizeLongPressTimer && !editor.resizingDevice) {
            const pos = editor.getMousePos(e);
            const clickedObject = editor.findObjectAt(pos.x, pos.y);
            if (!clickedObject || clickedObject.type !== 'device') {
                clearTimeout(editor.resizeLongPressTimer);
                editor.resizeLongPressTimer = null;
                editor.resizeHandle = null;
            }
        }
        
        if (editor.panning) {
            // Hide LLDP submenu when panning (table dialog persists as a window)
            const lldpSubmenu = document.getElementById('lldp-inline-submenu');
            if (lldpSubmenu) lldpSubmenu.remove();
            
            editor.panOffset.x = e.clientX - editor.panStart.x;
            editor.panOffset.y = e.clientY - editor.panStart.y;
            if (!editor._panSaveThrottle) {
                editor._panSaveThrottle = setTimeout(() => { editor._panSaveThrottle = null; editor.savePanOffset(); }, 200);
            }
            editor.updateScrollbars();
            editor.scheduleDraw();
            editor.updateHud();
            return;
        }
        
        const pos = editor.getMousePos(e);
        
        // Store world position for debugger and HUD
        editor.lastMousePos = pos;
        
        // Skip all cursor hover detection during any active interaction
        const _anyActive = editor.dragging || editor.isDragging || editor.resizingDevice ||
            editor.rotatingDevice || editor.isDrawingLink || editor.draggingCurveHandle ||
            editor.draggingAttachedText || editor.draggingBULChain || editor.selectionBox ||
            editor.stretchingLink || editor.rotatingShape || editor.resizingShape ||
            editor.rotatingText || editor.resizingText || editor._pendingDrag;
        
        // Update cursor if hovering over rotation, resize, or terminal button handles
        if (!_anyActive && editor.selectedObject && editor.selectedObject.type === 'device' && 
            !editor.rotatingDevice && !editor.resizingDevice &&
            editor.selectedObject._mouseReleasedAfterSelection === true) {
            // Check terminal button hover first
            if (editor.findTerminalButton(editor.selectedObject, pos.x, pos.y)) {
                editor.canvas.style.cursor = 'pointer';
                // Track hover state for visual feedback
                if (editor._hoveredTerminalBtn !== editor.selectedObject.id) {
                    editor._hoveredTerminalBtn = editor.selectedObject.id;
                    editor.draw(); // Redraw to show hover effect
                }
            } else if (editor.findRotationHandle(editor.selectedObject, pos.x, pos.y)) {
                editor.canvas.style.cursor = 'grab';
                if (editor._hoveredTerminalBtn) {
                    editor._hoveredTerminalBtn = null;
                    editor.draw();
                }
            } else {
                const rHandle = editor.findResizeHandle(editor.selectedObject, pos.x, pos.y);
                if (rHandle) {
                    editor.canvas.style.cursor = MouseMoveHandler._rotatedCursor(rHandle, editor.selectedObject.rotation || 0);
                    if (editor._hoveredTerminalBtn) {
                        editor._hoveredTerminalBtn = null;
                        editor.draw();
                    }
                } else if (!editor.dragging && !editor.panning) {
                    if (editor._hoveredTerminalBtn) {
                        editor._hoveredTerminalBtn = null;
                        editor.draw();
                    }
                    editor.updateCursor();
                }
            }
        }
        
        // TEXT handle cursor feedback
        if (!_anyActive && editor.selectedObject && editor.selectedObject.type === 'text' && 
            !editor.rotatingText && !editor.resizingText &&
            editor.selectedObject._mouseReleasedAfterSelection === true) {
            const textHandle = editor.findTextHandle(editor.selectedObject, pos.x, pos.y);
            if (textHandle) {
                if (textHandle.type === 'rotation') {
                    editor.canvas.style.cursor = 'grab';
                } else {
                    editor.canvas.style.cursor = textHandle.cursor || 'nwse-resize';
                }
            } else if (!editor.dragging && !editor.panning) {
                editor.updateCursor();
            }
        }
        
        // SHAPE handle cursor feedback
        if (!_anyActive && editor.selectedObject && editor.selectedObject.type === 'shape' && 
            !editor.resizingShape && !editor.rotatingShape &&
            editor.selectedObject._mouseReleasedAfterSelection === true) {
            const shapeHandle = editor.findShapeResizeHandle(editor.selectedObject, pos.x, pos.y);
            if (shapeHandle) {
                if (shapeHandle === 'rotation') {
                    editor.canvas.style.cursor = 'grab';
                } else {
                    editor.canvas.style.cursor = MouseMoveHandler._rotatedCursor(shapeHandle, editor.selectedObject.rotation || 0);
                }
            } else if (!editor.dragging && !editor.panning) {
                editor.updateCursor();
            }
        }
        
        // Handle potential CP drag → start actual drag if moved enough while mouse is down
        if (editor._potentialCPDrag && e.buttons === 1) { // Left mouse button held
            const dx = pos.x - editor._potentialCPDrag.startX;
            const dy = pos.y - editor._potentialCPDrag.startY;
            const dist = Math.sqrt(dx * dx + dy * dy);
            const dragThreshold = 8; // pixels to start dragging
            
            if (dist >= dragThreshold) {
                // Convert to actual curve drag
                editor.draggingCurveHandle = {
                    link: editor._potentialCPDrag.link,
                    startX: editor._potentialCPDrag.startX,
                    startY: editor._potentialCPDrag.startY,
                    initialPoint: editor._potentialCPDrag.initialPoint
                };
                editor._potentialCPDrag = null;
                editor.canvas.style.cursor = 'grabbing';
                editor.saveState(); // Make curve edit undoable
                
                // Deselect link and hide toolbar since we're now dragging CP
                if (editor.selectedObject === editor.draggingCurveHandle.link) {
                    editor.selectedObject = null;
                    editor.selectedObjects = [];
                }
                if (editor.hideLinkSelectionToolbar) {
                    editor.hideLinkSelectionToolbar();
                }
                
                if (editor.debugger) {
                    editor.debugger.logInfo(`CP Drag Started: ${editor.draggingCurveHandle.link.id}`);
                }
            }
        } else if (editor._potentialCPDrag && e.buttons !== 1) {
            // Mouse button released - clear potential drag
            editor._potentialCPDrag = null;
        }
        
        // Handle curve handle dragging (manual curve mode)
        if (editor.draggingCurveHandle) {
            const link = editor.draggingCurveHandle.link;
            
            // Update the manual control point to current mouse position
            link.manualControlPoint = { x: pos.x, y: pos.y };
            link.manualCurvePoint = { x: pos.x, y: pos.y };  // Keep both in sync
            
            // Set curve mode to manual for this link if not already
            if (link.curveMode !== 'manual') {
                link.curveMode = 'manual';
            }
            
            // CRITICAL: Update any middle-position TB attached to this link
            // The TB should follow the CP when CP is being dragged directly
            const attachedMiddleTexts = editor.objects.filter(obj => 
                obj.type === 'text' && obj.linkId === link.id && obj.position === 'middle'
            );
            for (const textObj of attachedMiddleTexts) {
                textObj.x = pos.x;
                textObj.y = pos.y;
            }
            
            // Update the hovered midpoint position for visual feedback
            editor.hoveredLinkMidpoint = { link, midpoint: { x: pos.x, y: pos.y } };
            
            editor.scheduleDraw();
            return; // Don't process other movements while dragging curve handle
        }
        
        // Check for curve handle hover (manual curve mode)
        if (!_anyActive) {
            const curveHandle = editor.findCurveHandleAt(pos.x, pos.y);
            const prevHovered = editor.hoveredLinkMidpoint;
            
            if (curveHandle) {
                editor.hoveredLinkMidpoint = curveHandle;
                // Smart cursor: TB (text box) area → move cursor, CP area → grab cursor
                const textAtPos = editor.findTextAt(pos.x, pos.y);
                
                if (textAtPos && curveHandle.isOnCP) {
                    // Both TB and CP at this position - determine which has priority
                    editor.ctx.save();
                    const fontFamily = textAtPos.fontFamily || 'Arial';
                    const fontWeight = textAtPos.fontWeight || 'normal';
                    editor.ctx.font = `${fontWeight} ${textAtPos.fontSize}px ${fontFamily}`;
                    const metrics = editor.ctx.measureText(textAtPos.text || 'Text');
                    const textW = metrics.width;
                    const textH = parseInt(textAtPos.fontSize) || 14;
                    editor.ctx.restore();
                    
                    // Check if mouse is on TB visible area (text + background)
                    const dx = pos.x - textAtPos.x;
                    const dy = pos.y - textAtPos.y;
                    const angle = -(textAtPos.rotation || 0) * Math.PI / 180;
                    const localX = dx * Math.cos(angle) - dy * Math.sin(angle);
                    const localY = dx * Math.sin(angle) + dy * Math.cos(angle);
                    
                    // FIX: Use same hitbox as click handler (full visible area)
                    const hasBackground = textAtPos.showBackground !== false;
                    const bgPadding = hasBackground ? (textAtPos.backgroundPadding || 8) : 6;
                    const clickPadding = bgPadding + 6;
                    
                    const isOnTextArea = Math.abs(localX) <= (textW/2 + clickPadding) && 
                                         Math.abs(localY) <= (textH/2 + clickPadding);
                    
                    if (isOnTextArea) {
                        // ENHANCED: Check if TB is attached to a link at MIDDLE position
                        // Middle-position TBs act as curve control points - show grab cursor
                        // (Dragging will automatically set link to manual mode)
                        const attachedLink = textAtPos.linkId ? 
                            editor.objects.find(o => o.id === textAtPos.linkId) : null;
                        const isMiddlePosition = textAtPos.position === 'middle';
                        
                        if (attachedLink && isMiddlePosition) {
                            // Middle TB IS the curve control point - show grab cursor
                            // (Works for any curve mode - dragging sets it to manual)
                            editor.canvas.style.cursor = 'grab';
                        } else {
                            // Regular TB - show move cursor
                            editor.canvas.style.cursor = 'move';
                        }
                    } else {
                        // Outside TB, on CP handle - show grab cursor
                        editor.canvas.style.cursor = 'grab';
                    }
                } else if (textAtPos && textAtPos.linkId) {
                    // ENHANCED: Check if TB is attached to a link at MIDDLE position
                    // Middle-position TBs act as curve control points
                    const attachedLink = editor.objects.find(o => o.id === textAtPos.linkId);
                    const isMiddlePosition = textAtPos.position === 'middle';
                    
                    if (attachedLink && isMiddlePosition) {
                        // Middle TB IS the curve control - show grab cursor
                        editor.canvas.style.cursor = 'grab';
                    } else {
                        // Regular TB - show move cursor
                        editor.canvas.style.cursor = 'move';
                    }
                } else if (curveHandle.isOnCP) {
                    // Only CP here - show grab cursor
                    editor.canvas.style.cursor = 'grab';
                }
                // Don't change cursor if just hovering over link body (CP will still be visible)
                
                // Request redraw if hover state changed
                if (!prevHovered || prevHovered.link !== curveHandle.link) {
                    editor.draw();
                }
            } else if (prevHovered) {
                editor.hoveredLinkMidpoint = null;
                editor.updateCursor();
                editor.draw();
            }
        }

        // XRAY icon hover detection
        if (window.ObjectDetection && window.ObjectDetection.checkXrayIconHover) {
            const wasHovered = editor._hoveredXrayIcon;
            window.ObjectDetection.checkXrayIconHover(editor, pos.x, pos.y);
            if (editor._hoveredXrayIcon !== wasHovered) {
                editor.canvas.style.cursor = editor._hoveredXrayIcon ? 'pointer' : '';
                editor.draw();
            }
        }

        // If in device placement with a pending click and the user drags, start marquee selection instead of placing
        if (editor.placingDevice && editor.placementPending && editor.selectionRectStart) {
            const dx = Math.abs(pos.x - editor.placementPending.startPos.x);
            const dy = Math.abs(pos.y - editor.placementPending.startPos.y);
            if (dx > 3 || dy > 3) {
                // Cancel pending placement and start marquee selection - SEAMLESS TRANSITION
                const deviceType = editor.placingDevice;
                editor.placementPending = null;
                editor.placingDevice = null; // Temporarily exit placement mode
                editor.startMarqueeSelection(editor.selectionRectStart);
                
                // Store device type to resume after marquee
                editor.resumePlacementAfterMarquee = deviceType;
                
                if (editor.debugger) {
                    editor.debugger.logInfo(`Seamless transition: Device placement -> MS mode (drag detected)`);
                }
            }
        }
        
        // Handle pending link stretch - check if drag threshold exceeded
        if (editor._pendingStretch && !editor.stretchingLink) {
            const dx = pos.x - editor._pendingStretch.startX;
            const dy = pos.y - editor._pendingStretch.startY;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance >= editor._pendingStretch.threshold) {
                // Threshold exceeded - start actual stretching
                editor.stretchingLink = editor._pendingStretch.link;
                editor.stretchingEndpoint = editor._pendingStretch.endpoint;
                editor.stretchingConnectionPoint = editor._pendingStretch.isConnectionPoint;
                
                // Setup tracking data
                const allMergedLinks = editor.getAllMergedLinks(editor.stretchingLink);
                editor._bulTrackingData = {
                    startTime: Date.now(),
                    links: allMergedLinks.map(link => ({
                        id: link.id,
                        type: link.type,
                        startPos: { x: link.start.x, y: link.start.y },
                        endPos: { x: link.end.x, y: link.end.y },
                        device1: link.device1,
                        device2: link.device2,
                        lastPos: { 
                            start: { x: link.start.x, y: link.start.y },
                            end: { x: link.end.x, y: link.end.y }
                        }
                    })),
                    grabPoint: editor.stretchingEndpoint,
                    isConnectionPoint: editor.stretchingConnectionPoint,
                    totalJumps: 0
                };
                
                // CRITICAL: Store old midpoints for CP shifting (to preserve curve shape)
                // FIXED: Always use link.start/end for consistency with _updateCurvePointsDuringStretch
                // Using _renderedEndpoints was causing jumps because it includes device edge offsets
                editor._stretchOldMidpoints = {};
                for (const link of allMergedLinks) {
                    editor._stretchOldMidpoints[link.id] = {
                        startX: link.start.x,
                        startY: link.start.y,
                        endX: link.end.x,
                        endY: link.end.y
                    };
                }
                
                if (editor.debugger) {
                    const ulNumber = allMergedLinks.findIndex(l => l.id === editor.stretchingLink.id) + 1;
                    editor.debugger.logInfo(`UL Stretch Started (threshold ${editor._pendingStretch.threshold}px exceeded)`);
                    editor.debugger.logInfo(`   Link: ${editor.stretchingLink.id} (U${ulNumber}) at ${editor.stretchingEndpoint}`);
                }
                
                // Clear pending
                editor._pendingStretch = null;
            }
        }
        
        // Handle pending object drag - check if drag threshold exceeded
        if (editor._pendingDrag && !editor.dragging) {
            const dx = pos.x - editor._pendingDrag.startX;
            const dy = pos.y - editor._pendingDrag.startY;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance >= editor._pendingDrag.threshold) {
                // Threshold exceeded - start actual dragging
                
                // Handle different drag types
                if (editor._pendingDrag.isMultiSelect) {
                    // CRITICAL FIX: Re-capture FRESH positions at drag start moment
                    // Objects may have shifted between mousedown and threshold exceeded
                    // (momentum decay, draw-cycle updates, etc.)
                    // Setting dragStart to CURRENT mouse pos ensures dx/dy starts at 0
                    editor.dragStart = { x: pos.x, y: pos.y };
                    editor.multiSelectInitialPositions = editor.selectedObjects.map(obj => {
                        const initPos = { id: obj.id, x: obj.x, y: obj.y };
                        if (obj.type === 'unbound') {
                            initPos.startX = obj.start.x;
                            initPos.startY = obj.start.y;
                            initPos.endX = obj.end.x;
                            initPos.endY = obj.end.y;
                            initPos.curvePointX = obj.manualCurvePoint?.x;
                            initPos.curvePointY = obj.manualCurvePoint?.y;
                            initPos.controlPointX = obj.manualControlPoint?.x;
                            initPos.controlPointY = obj.manualControlPoint?.y;
                        }
                        return initPos;
                    });
                    // Fresh QL and UL CP capture at drag start
                    const deviceIds = editor.selectedObjects.filter(o => o.type === 'device').map(o => o.id);
                    editor._initialQuickLinkCPs = editor.objects
                        .filter(obj => obj.type === 'link' && 
                            (deviceIds.includes(obj.device1) || deviceIds.includes(obj.device2)) &&
                            (obj.manualCurvePoint || obj.manualControlPoint))
                        .map(ql => ({
                            id: ql.id,
                            curvePointX: ql.manualCurvePoint?.x,
                            curvePointY: ql.manualCurvePoint?.y,
                            controlPointX: ql.manualControlPoint?.x,
                            controlPointY: ql.manualControlPoint?.y,
                            bothEndpointsMoved: deviceIds.includes(ql.device1) && deviceIds.includes(ql.device2)
                        }));
                    const selectedLinkIds = editor.selectedObjects.filter(o => o.type === 'unbound').map(o => o.id);
                    editor._initialAttachedULCPs = editor.objects
                        .filter(obj => obj.type === 'unbound' && 
                            obj.manualCurvePoint &&
                            !selectedLinkIds.includes(obj.id) &&
                            (deviceIds.includes(obj.device1) || deviceIds.includes(obj.device2)))
                        .map(ul => ({
                            id: ul.id,
                            curvePointX: ul.manualCurvePoint?.x,
                            curvePointY: ul.manualCurvePoint?.y,
                            bothEndpointsMoved: deviceIds.includes(ul.device1) && deviceIds.includes(ul.device2)
                        }));
                    editor.dragStartPos = null; // Multi-select uses different tracking
                    editor._lastMultiDragTime = 0; // Reset dedup timer
                } else if (editor._pendingDrag.isUnboundLinkBody) {
                    // Restore drag state from mousedown for single-object paths
                    editor.dragStart = editor._pendingDrag.dragStart;
                    editor.unboundLinkInitialPos = editor._pendingDrag.unboundLinkInitialPos;
                    editor.dragStartPos = editor._pendingDrag.dragStartPos;
                } else {
                    // Restore drag state from mousedown for single-object paths
                    editor.dragStart = editor._pendingDrag.dragStart;
                    editor.unboundLinkInitialPos = editor._pendingDrag.unboundLinkInitialPos;
                    editor.textDragInitialPos = editor._pendingDrag.textDragInitialPos;
                    editor.deviceDragInitialPos = editor._pendingDrag.deviceDragInitialPos;
                    editor.shapeDragInitialPos = editor._pendingDrag.shapeDragInitialPos;
                    editor.dragStartPos = editor._pendingDrag.dragStartPos;
                }
                
                // Clear tap tracking when dragging starts
                editor.lastTapTime = 0;
                editor._lastTapDevice = null;
                editor._lastTapPos = null;
                editor._lastTapStartTime = 0;
                
                // NOW set dragging=true
                editor.dragging = true;
                
                // Hide ALL selection toolbars when dragging starts
                editor.hideAllSelectionToolbars();
                
                if (editor.debugger) {
                    if (editor._pendingDrag.isMultiSelect) {
                        editor.debugger.logInfo(`Multi-select Drag Started (threshold ${editor._pendingDrag.threshold}px exceeded)`);
                        editor.debugger.logInfo(`   Objects: ${editor.selectedObjects.length} items`);
                    } else if (editor._pendingDrag.isUnboundLinkBody) {
                        const obj = editor._pendingDrag.object;
                        editor.debugger.logInfo(`UL Body Drag Started (threshold ${editor._pendingDrag.threshold}px exceeded)`);
                        editor.debugger.logInfo(`   Link: ${obj.id}`);
                    } else {
                        const obj = editor._pendingDrag.object;
                        editor.debugger.logInfo(`Drag Started (threshold ${editor._pendingDrag.threshold}px exceeded)`);
                        editor.debugger.logInfo(`   Object: ${obj.label || obj.id || obj.type}`);
                    }
                }
                
                // Clear pending
                editor._pendingDrag = null;
            }
        }
        
        // Handle link stretching (unbound links)
        // CRITICAL: Only process if stretching flags are set (safety check)
        if (editor.stretchingLink && editor.stretchingEndpoint) {
            // ENHANCED: Special handling for connection point dragging (MPs)
            if (editor.stretchingConnectionPoint) {
                // Dragging an MP - ONLY move the MP endpoint itself!
                // CRITICAL FIX: Don't translate the whole link, just move the grabbed endpoint
                const newX = pos.x;
                const newY = pos.y;
                
                // Move ONLY the endpoint we're dragging (the MP), NOT the entire link
                if (editor.stretchingEndpoint === 'start') {
                    // Only move start if it's NOT a TP (not attached to device)
                    if (!editor.stretchingLink.device1) {
                        editor.stretchingLink.start.x = newX;
                        editor.stretchingLink.start.y = newY;
                    }
                } else {
                    // Only move end if it's NOT a TP (not attached to device)
                    if (!editor.stretchingLink.device2) {
                        editor.stretchingLink.end.x = newX;
                        editor.stretchingLink.end.y = newY;
                    }
                }
                
                // Find the partner link and update its connected endpoint
                // CRITICAL FIX: For MIDDLE links, determine which MP based on which endpoint is being dragged!
                let partnerLink = null;
                let partnerEndpoint = null;
                let isConnectingToParent = false;
                let isConnectingToChild = false;
                
                const isMiddleLink = editor.stretchingLink.mergedInto && editor.stretchingLink.mergedWith;
                
                if (isMiddleLink) {
                    // MIDDLE LINK: Determine which connection based on grabbed endpoint
                    const parentLink = editor.objects.find(o => o.id === editor.stretchingLink.mergedInto.parentId);
                    
                    // Find which endpoint connects to parent
                    const parentConnectsToEndpoint = parentLink?.mergedWith?.childConnectionEndpoint ||
                        (parentLink?.mergedWith?.childFreeEnd === 'start' ? 'end' : 'start');
                    
                    // Find which endpoint connects to child
                    const childConnectsToEndpoint = editor.stretchingLink.mergedWith.connectionEndpoint ||
                        (editor.stretchingLink.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start');
                    
                    if (editor.stretchingEndpoint === parentConnectsToEndpoint) {
                        // Dragging endpoint that connects to PARENT
                        isConnectingToParent = true;
                        partnerLink = parentLink;
                        if (partnerLink?.mergedWith) {
                            partnerEndpoint = partnerLink.mergedWith.connectionEndpoint ||
                                (partnerLink.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start');
                        }
                        
                        // Update this link's mergedInto AND parent's mergedWith
                        if (editor.stretchingLink.mergedInto.connectionPoint) {
                            editor.stretchingLink.mergedInto.connectionPoint.x = newX;
                            editor.stretchingLink.mergedInto.connectionPoint.y = newY;
                        }
                        if (partnerLink?.mergedWith?.connectionPoint) {
                            partnerLink.mergedWith.connectionPoint.x = newX;
                            partnerLink.mergedWith.connectionPoint.y = newY;
                        }
                    } else if (editor.stretchingEndpoint === childConnectsToEndpoint) {
                        // Dragging endpoint that connects to CHILD
                        isConnectingToChild = true;
                        partnerLink = editor.objects.find(o => o.id === editor.stretchingLink.mergedWith.linkId);
                        partnerEndpoint = editor.stretchingLink.mergedWith.childConnectionEndpoint ||
                            (editor.stretchingLink.mergedWith.childFreeEnd === 'start' ? 'end' : 'start');
                        
                        // Update this link's mergedWith AND child's mergedInto
                        if (editor.stretchingLink.mergedWith.connectionPoint) {
                            editor.stretchingLink.mergedWith.connectionPoint.x = newX;
                            editor.stretchingLink.mergedWith.connectionPoint.y = newY;
                        }
                        if (partnerLink?.mergedInto?.connectionPoint) {
                            partnerLink.mergedInto.connectionPoint.x = newX;
                            partnerLink.mergedInto.connectionPoint.y = newY;
                        }
                    }
                } else if (editor.stretchingLink.mergedWith) {
                    // HEAD or STANDALONE with child
                    isConnectingToChild = true;
                    partnerLink = editor.objects.find(o => o.id === editor.stretchingLink.mergedWith.linkId);
                    partnerEndpoint = editor.stretchingLink.mergedWith.childConnectionEndpoint ||
                        (editor.stretchingLink.mergedWith.childFreeEnd === 'start' ? 'end' : 'start');
                    
                    // Update connection point in metadata
                    if (editor.stretchingLink.mergedWith.connectionPoint) {
                        editor.stretchingLink.mergedWith.connectionPoint.x = newX;
                        editor.stretchingLink.mergedWith.connectionPoint.y = newY;
                    }
                    if (partnerLink?.mergedInto?.connectionPoint) {
                        partnerLink.mergedInto.connectionPoint.x = newX;
                        partnerLink.mergedInto.connectionPoint.y = newY;
                    }
                } else if (editor.stretchingLink.mergedInto) {
                    // TAIL with parent
                    isConnectingToParent = true;
                    partnerLink = editor.objects.find(o => o.id === editor.stretchingLink.mergedInto.parentId);
                    if (partnerLink && partnerLink.mergedWith) {
                        partnerEndpoint = partnerLink.mergedWith.connectionEndpoint || 
                                        partnerLink.mergedWith.parentEndpoint ||
                                        (partnerLink.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start');
                    }
                    
                    // Update connection point in metadata
                    if (editor.stretchingLink.mergedInto.connectionPoint) {
                        editor.stretchingLink.mergedInto.connectionPoint.x = newX;
                        editor.stretchingLink.mergedInto.connectionPoint.y = newY;
                    }
                    if (partnerLink?.mergedWith?.connectionPoint) {
                        partnerLink.mergedWith.connectionPoint.x = newX;
                        partnerLink.mergedWith.connectionPoint.y = newY;
                    }
                }
                
                // Update partner link's endpoint position
                // FIXED: Only update if NOT attached to a device (i.e., NOT a TP)
                if (partnerLink && partnerEndpoint) {
                    if (partnerEndpoint === 'start' && !partnerLink.device1) {
                        partnerLink.start.x = newX;
                        partnerLink.start.y = newY;
                    } else if (partnerEndpoint === 'end' && !partnerLink.device2) {
                        partnerLink.end.x = newX;
                        partnerLink.end.y = newY;
                    }
                }
                
                // CRITICAL FIX: DO NOT call updateAllConnectionPoints() here!
                // That function updates ALL connection points in ALL links, causing other MPs to jump
                // We already manually updated the relevant connection points above (lines 2779-2827)
                // Only those two connection points (on the stretching link and its partner) should move
                // Other MPs in the chain should stay in place!
                // editor.updateAllConnectionPoints(); // REMOVED - causes MP-2 to jump when dragging MP-1
                
                // REAL-TIME CP UPDATE: Keep curve points synchronized during MP drag
                editor._updateCurvePointsDuringStretch();
                
                // REAL-TIME FEEDBACK: Draw immediately to show link movement during drag
                editor.scheduleDraw();
                return;
            }
            
            // ENHANCED: TP stretching with BUL chain support and real-time tracking
            // Find nearby device for visual feedback and magnetic snap
            const endpointPos = editor.stretchingEndpoint === 'start' 
                ? editor.stretchingLink.start 
                : editor.stretchingLink.end;
            
            // AI DEBUGGER: Real-time TP/MP tracking during stretch
            if (editor.debugger && editor._bulTrackingData) {
                const allLinks = editor.getAllMergedLinks(editor.stretchingLink);
                const currentPos = { x: pos.x, y: pos.y };
                const startPos = editor._bulTrackingData.links.find(l => l.id === editor.stretchingLink.id);
                
                if (startPos) {
                    const startEndpointPos = editor.stretchingEndpoint === 'start' ? startPos.startPos : startPos.endPos;
                    const distance = Math.hypot(currentPos.x - startEndpointPos.x, currentPos.y - startEndpointPos.y);
                    
                    // Update tracking data
                    const trackData = editor._bulTrackingData.links.find(l => l.id === editor.stretchingLink.id);
                    if (trackData) {
                        trackData.currentPos = currentPos;
                        trackData.distance = distance;
                    }
                    
                    // Log movement every 50px or on significant changes
                    if (!editor._lastTrackingLog || (Date.now() - editor._lastTrackingLog) > 200) {
                        const ulNum = allLinks.findIndex(l => l.id === editor.stretchingLink.id) + 1;
                        
                        // Determine if it's a TP or MP
                        if (!editor.stretchingConnectionPoint) {
                            // It's a TP - find TP number
                            const tpsInBUL = [];
                            allLinks.forEach(chainLink => {
                                if (!editor.isEndpointConnected(chainLink, 'start')) {
                                    tpsInBUL.push({ linkId: chainLink.id, endpoint: 'start' });
                                }
                                if (!editor.isEndpointConnected(chainLink, 'end')) {
                                    tpsInBUL.push({ linkId: chainLink.id, endpoint: 'end' });
                                }
                            });
                            tpsInBUL.sort((a, b) => {
                                const ulNumA = parseInt(a.linkId.split('_')[1]) || 0;
                                const ulNumB = parseInt(b.linkId.split('_')[1]) || 0;
                                return ulNumA - ulNumB;
                            });
                            const tpIdx = tpsInBUL.findIndex(tp => tp.linkId === editor.stretchingLink.id && tp.endpoint === editor.stretchingEndpoint);
                            const tpNum = (tpIdx >= 0) ? tpIdx + 1 : '?';
                            
                            editor.debugger.logInfo(`⚪ TP-${tpNum}(U${ulNum}) moving: ${Math.round(distance)}px from start`);
                        } else {
                            // It's an MP - find MP number
                            let mpNumber = 0;
                            if (editor.stretchingLink.mergedWith) {
                                mpNumber = editor.stretchingLink.mergedWith.mpNumber || 0;
                            } else if (editor.stretchingLink.mergedInto) {
                                const parent = editor.objects.find(o => o.id === editor.stretchingLink.mergedInto.parentId);
                                if (parent?.mergedWith) {
                                    mpNumber = parent.mergedWith.mpNumber || 0;
                                }
                            }
                            editor.debugger.logInfo(`MP-${mpNumber}(U${ulNum}) moving: ${Math.round(distance)}px from start`);
                        }
                        editor._lastTrackingLog = Date.now();
                    }
                }
            }
            
            let nearbyDevice = null;
            let snapDistance = Infinity;
            let snapAngle = 0;
            
            // ENHANCED: Check all devices for the closest one within attachment range
            editor.objects.forEach(obj => {
                if (obj.type === 'device') {
                    const dx = pos.x - obj.x;
                    const dy = pos.y - obj.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    
                    // ENHANCED: Use device bounds to calculate proper attachment range based on device style
                    const bounds = editor.getDeviceBounds(obj);
                    let attachmentRange;
                    
                    // Calculate attachment range based on device style
                    if (bounds.type === 'circle' || bounds.type === 'hexagon') {
                        // Circular devices: use radius + tolerance
                        attachmentRange = bounds.radius + 25;
                    } else if (bounds.type === 'rectangle' || bounds.type === 'classic') {
                        // Rectangular devices: use diagonal half + tolerance
                        const halfDiagonal = Math.sqrt(bounds.width * bounds.width + bounds.height * bounds.height) / 2;
                        attachmentRange = halfDiagonal + 25;
                    } else {
                        // Fallback: use radius + tolerance
                        attachmentRange = obj.radius + 25;
                    }
                    
                    if (distance <= attachmentRange && distance < snapDistance) {
                        nearbyDevice = obj;
                        snapDistance = distance;
                        snapAngle = Math.atan2(dy, dx);
                    }
                }
            });

            // ENHANCED: Check for nearby UL endpoints (TPs) for link-to-link snapping
            let nearbyULEndpoint = null;
            let ulSnapDistance = Infinity;
            
            // Only search for merge targets if the stretching endpoint is a FREE TP
            // Check if stretchingEndpointIsFree logic (replicated from onMouseUp logic)
            let stretchingEndpointIsFree = true;
            if (editor.stretchingConnectionPoint) stretchingEndpointIsFree = false;
            if (editor.stretchingLink.mergedWith && editor.stretchingEndpoint !== editor.stretchingLink.mergedWith.parentFreeEnd) stretchingEndpointIsFree = false;
            if (editor.stretchingLink.mergedInto) {
                const parent = editor.objects.find(o => o.id === editor.stretchingLink.mergedInto.parentId);
                if (parent && parent.mergedWith && editor.stretchingEndpoint !== parent.mergedWith.childFreeEnd) stretchingEndpointIsFree = false;
            }

            if (stretchingEndpointIsFree) {
                editor.objects.forEach(obj => {
                    if (obj.type === 'unbound' && obj.id !== editor.stretchingLink.id) {
                         // Skip middle links
                         if (obj.mergedInto && obj.mergedWith) return;

                         // Check start
                         let startIsConnectionPoint = false;
                         if (obj.connectedTo && obj.connectedTo.thisEndpoint === 'start') startIsConnectionPoint = true;
                         else if (obj.mergedWith && obj.mergedWith.parentFreeEnd !== 'start') startIsConnectionPoint = true;
                         else if (obj.mergedInto) {
                             const p = editor.objects.find(o => o.id === obj.mergedInto.parentId);
                             if (p && p.mergedWith && p.mergedWith.childFreeEnd !== 'start') startIsConnectionPoint = true;
                         }

                         if (!obj.device1 && !startIsConnectionPoint) {
                             const dist = Math.sqrt(Math.pow(pos.x - obj.start.x, 2) + Math.pow(pos.y - obj.start.y, 2));
                             if (dist < editor.ulSnapDistance && dist < ulSnapDistance) {
                                 nearbyULEndpoint = obj.start;
                                 ulSnapDistance = dist;
                             }
                         }

                         // Check end
                         let endIsConnectionPoint = false;
                         if (obj.connectedTo && obj.connectedTo.thisEndpoint === 'end') endIsConnectionPoint = true;
                         else if (obj.mergedWith && obj.mergedWith.parentFreeEnd !== 'end') endIsConnectionPoint = true;
                         else if (obj.mergedInto) {
                             const p = editor.objects.find(o => o.id === obj.mergedInto.parentId);
                             if (p && p.mergedWith && p.mergedWith.childFreeEnd !== 'end') endIsConnectionPoint = true;
                         }

                         if (!obj.device2 && !endIsConnectionPoint) {
                             const dist = Math.sqrt(Math.pow(pos.x - obj.end.x, 2) + Math.pow(pos.y - obj.end.y, 2));
                             if (dist < editor.ulSnapDistance && dist < ulSnapDistance) {
                                 nearbyULEndpoint = obj.end;
                                 ulSnapDistance = dist;
                             }
                         }
                    }
                });
            }
            
            // Store nearby device for visual feedback during draw (only if sticky links enabled)
            // ENHANCED: Check per-link stickyDisabled property (set when user detaches link)
            const linkStickyEnabled = editor.linkStickyMode && !editor.stretchingLink.stickyDisabled;
            editor._stretchingNearDevice = linkStickyEnabled ? nearbyDevice : null;
            editor._stretchingSnapAngle = (linkStickyEnabled && nearbyDevice) ? snapAngle : null;
            editor._stretchingNearUL = (linkStickyEnabled && nearbyULEndpoint) ? nearbyULEndpoint : null;
            
            // ENHANCED: Multi-stage magnetic snap for smoother attachment
            let finalX = pos.x;
            let finalY = pos.y;
            
            if (linkStickyEnabled) {
                if (nearbyDevice) {
                const targetPoint = editor.getLinkConnectionPoint(nearbyDevice, snapAngle);
                const targetX = targetPoint.x;
                const targetY = targetPoint.y;
                
                if (snapDistance < (nearbyDevice.radius + 8)) {
                    // Very close - strong snap (90%)
                    const pullStrength = 0.9;
                finalX = pos.x + (targetX - pos.x) * pullStrength;
                finalY = pos.y + (targetY - pos.y) * pullStrength;
                    editor.canvas.style.cursor = 'crosshair'; // Ready to attach
                } else if (snapDistance < (nearbyDevice.radius + 15)) {
                    // Close - medium snap (50%)
                    const pullStrength = 0.5;
                    finalX = pos.x + (targetX - pos.x) * pullStrength;
                    finalY = pos.y + (targetY - pos.y) * pullStrength;
                    editor.canvas.style.cursor = 'crosshair'; // Approaching
                } else {
                    // In range - gentle pull (20%)
                    const pullStrength = 0.2;
                    finalX = pos.x + (targetX - pos.x) * pullStrength;
                    finalY = pos.y + (targetY - pos.y) * pullStrength;
                    editor.canvas.style.cursor = 'move'; // Getting closer
                    }
                } else if (nearbyULEndpoint) {
                    // UL Snap Logic - IMMEDIATE STICKY SNAP
                     const targetX = nearbyULEndpoint.x;
                    const targetY = nearbyULEndpoint.y;
                    
                    if (ulSnapDistance < 5) {
                        // INSTANT snap when very close
                        finalX = targetX;
                        finalY = targetY;
                        editor.canvas.style.cursor = 'copy'; 
                    } else if (ulSnapDistance < 15) {
                        // Very strong pull
                        const pullStrength = 0.95;
                        finalX = pos.x + (targetX - pos.x) * pullStrength;
                        finalY = pos.y + (targetY - pos.y) * pullStrength;
                        editor.canvas.style.cursor = 'copy';
                    } else if (ulSnapDistance < 25) {
                        // Medium pull
                        const pullStrength = 0.6;
                        finalX = pos.x + (targetX - pos.x) * pullStrength;
                        finalY = pos.y + (targetY - pos.y) * pullStrength;
                        editor.canvas.style.cursor = 'copy';
                    } else {
                        // Gentle attraction
                        const pullStrength = 0.25;
                        finalX = pos.x + (targetX - pos.x) * pullStrength;
                        finalY = pos.y + (targetY - pos.y) * pullStrength;
                        editor.canvas.style.cursor = 'move';
                    }
                } else {
                    editor.canvas.style.cursor = 'grab';
                }
            } else {
                editor.canvas.style.cursor = 'grab'; // Normal cursor
            }
            
            // If endpoint is attached to a device and user moves it away, detach it
            if (editor.stretchingEndpoint === 'start') {
                if (editor.stretchingLink.device1) {
                    const device1 = editor.objects.find(obj => obj.id === editor.stretchingLink.device1);
                    if (device1) {
                        const dx = finalX - device1.x;
                        const dy = finalY - device1.y;
                        const distance = Math.sqrt(dx * dx + dy * dy);
                        // Detach if moved more than device radius + 30px away (more forgiving)
                        if (distance > (device1.radius + 30)) {
                            const detachedFrom = device1.label || device1.id;
                            editor.stretchingLink.device1 = null;
                            delete editor.stretchingLink.device1Angle; // Clear stored angle on detach
                            
                            // CRITICAL: Change originType from QL to UL when link is detached
                            if (editor.stretchingLink.originType === 'QL') {
                                editor.stretchingLink.originType = 'UL';
                            }
                            
                            // TRACKING: Log detachment
                            if (editor._bulTrackingData) {
                                const trackData = editor._bulTrackingData.links.find(l => l.id === editor.stretchingLink.id);
                                if (trackData) {
                                    trackData.detachments = (trackData.detachments || 0) + 1;
                                }
                            }
                            
                            if (editor.debugger) {
                                // Calculate UL and TP numbers
                                const allLinks = editor.getAllMergedLinks(editor.stretchingLink);
                                const ulNum = allLinks.findIndex(l => l.id === editor.stretchingLink.id) + 1;
                                
                                // Find TP number for start endpoint
                                // FIXED: Use clearer logic - endpoint is TP if NOT connected
                                const tpsInBUL = [];
                                allLinks.forEach(chainLink => {
                                    let sIsConnected = false;
                                    if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'end') sIsConnected = true;
                                    if (chainLink.mergedInto) {
                                        const prnt = editor.objects.find(o => o.id === chainLink.mergedInto.parentId);
                                        if (prnt?.mergedWith && prnt.mergedWith.childFreeEnd === 'end') sIsConnected = true;
                                    }
                                    if (!sIsConnected) tpsInBUL.push({ linkId: chainLink.id, endpoint: 'start' });
                                    
                                    let eIsConnected = false;
                                    if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'start') eIsConnected = true;
                                    if (chainLink.mergedInto) {
                                        const prnt = editor.objects.find(o => o.id === chainLink.mergedInto.parentId);
                                        if (prnt?.mergedWith && prnt.mergedWith.childFreeEnd === 'start') eIsConnected = true;
                                    }
                                    if (!eIsConnected) tpsInBUL.push({ linkId: chainLink.id, endpoint: 'end' });
                                });
                                
                                // FIXED: Sort TPs by UL number so TP-1 is always on lowest UL, TP-2 on highest
                                tpsInBUL.sort((a, b) => {
                                    const ulNumA = parseInt(a.linkId.split('_')[1]) || 0;
                                    const ulNumB = parseInt(b.linkId.split('_')[1]) || 0;
                                    return ulNumA - ulNumB;
                                });
                                
                                const tpIdx = tpsInBUL.findIndex(tp => tp.linkId === editor.stretchingLink.id && tp.endpoint === 'start');
                                const tpNum = (tpIdx >= 0) ? tpIdx + 1 : '?';
                                
                                editor.debugger.logInfo(`[DETACH] U${ulNum}-TP-${tpNum}(start) from ${detachedFrom}`);
                            }
                        } else {
                            // Keep attached - snap to device edge (shape-aware)
                            const angle = Math.atan2(finalY - device1.y, finalX - device1.x);
                            const edgePt = editor.getLinkConnectionPoint(device1, angle);
                            finalX = edgePt.x;
                            finalY = edgePt.y;
                        }
                    }
                }
                
                editor.stretchingLink.start = { x: finalX, y: finalY };
                
                // TRACKING: Detect position jumps for this endpoint
                if (editor._bulTrackingData) {
                    const trackData = editor._bulTrackingData.links.find(l => l.id === editor.stretchingLink.id);
                    if (trackData) {
                        const lastStart = trackData.lastPos.start;
                        const jump = Math.sqrt(
                            Math.pow(finalX - lastStart.x, 2) + 
                            Math.pow(finalY - lastStart.y, 2)
                        );
                        
                        // Detect jumps - threshold scales with zoom to avoid false positives
                        // At 25% zoom, a 100px mouse move = 400px world coords, so base threshold is 500px * (1/zoom)
                        const zoomAdjustedThreshold = 500 / Math.min(editor.zoom, 1);
                        if (jump > zoomAdjustedThreshold) {
                            editor._bulTrackingData.totalJumps++;
                            if (editor.debugger) {
                                editor.debugger.logWarning(`Large move: ${editor.stretchingLink.id} START moved ${jump.toFixed(1)}px (threshold: ${zoomAdjustedThreshold.toFixed(0)}px at ${(editor.zoom*100).toFixed(0)}% zoom)`);
                            }
                        }
                        
                        // Update tracking
                        trackData.lastPos.start = { x: finalX, y: finalY };
                    }
                }
                
                // ENHANCED: TP stretching in BUL chains - only update THIS link's endpoint
                // TPs are free endpoints and don't affect other links in the chain
                // Only MPs (connection points) move multiple links together
                
                // CRITICAL: When stretching a TP (not MP), we only move this link's endpoint
                // The connection points (MPs) stay fixed - they only move when explicitly dragged
                // This ensures fluid, independent TP movement in BUL chains
                
                // Update connection point metadata if this endpoint is part of a merge
                // But only update metadata, don't move other links (they stay fixed)
                if (editor.stretchingLink.mergedWith) {
                    const parentFreeEnd = editor.stretchingLink.mergedWith.parentFreeEnd;
                    const parentConnectedEnd = parentFreeEnd === 'start' ? 'end' : 'start';
                    
                    // If we're stretching the connected end (MP), update connection point
                    if (editor.stretchingEndpoint === parentConnectedEnd && editor.stretchingConnectionPoint) {
                        const newConnectionX = finalX;
                        const newConnectionY = finalY;
                        
                        // Update connection point in metadata
                        if (editor.stretchingLink.mergedWith.connectionPoint) {
                            editor.stretchingLink.mergedWith.connectionPoint.x = newConnectionX;
                            editor.stretchingLink.mergedWith.connectionPoint.y = newConnectionY;
                        }
                        
                        // Also update child link's endpoint if it's connected here
                        const childLink = editor.objects.find(o => o.id === editor.stretchingLink.mergedWith.linkId);
                        if (childLink && childLink.mergedInto) {
                        const childConnectedEnd = editor.stretchingLink.mergedWith.childConnectionEndpoint ||
                            (editor.stretchingLink.mergedWith.childFreeEnd === 'start' ? 'end' : 'start');
                            
                        if (childConnectedEnd === 'start') {
                            childLink.start.x = newConnectionX;
                            childLink.start.y = newConnectionY;
                        } else {
                            childLink.end.x = newConnectionX;
                            childLink.end.y = newConnectionY;
                        }
                        
                            if (childLink.mergedInto.connectionPoint) {
                            childLink.mergedInto.connectionPoint.x = newConnectionX;
                            childLink.mergedInto.connectionPoint.y = newConnectionY;
                        }
                    }
                    }
                } else if (editor.stretchingLink.mergedInto) {
                    // This is a child link - update parent's connection point if we're dragging the connected end
                    const parentLink = editor.objects.find(o => o.id === editor.stretchingLink.mergedInto.parentId);
                    if (parentLink && parentLink.mergedWith) {
                        const childFreeEnd = parentLink.mergedWith.childFreeEnd;
                        const childConnectedEnd = childFreeEnd === 'start' ? 'end' : 'start';
                        
                        // If stretching the connected end (MP), update connection point
                        if (editor.stretchingEndpoint === childConnectedEnd && editor.stretchingConnectionPoint) {
                            const newConnectionX = finalX;
                            const newConnectionY = finalY;
                            
                            // Update parent's endpoint
                            const parentConnectedEnd = parentLink.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start';
                        if (parentConnectedEnd === 'start') {
                            parentLink.start.x = newConnectionX;
                            parentLink.start.y = newConnectionY;
                        } else {
                            parentLink.end.x = newConnectionX;
                            parentLink.end.y = newConnectionY;
                        }
                        
                            // Update connection point metadata
                            if (parentLink.mergedWith.connectionPoint) {
                            parentLink.mergedWith.connectionPoint.x = newConnectionX;
                            parentLink.mergedWith.connectionPoint.y = newConnectionY;
                        }
                            if (editor.stretchingLink.mergedInto.connectionPoint) {
                        editor.stretchingLink.mergedInto.connectionPoint.x = newConnectionX;
                        editor.stretchingLink.mergedInto.connectionPoint.y = newConnectionY;
                    }
                }
                    }
                }
                
                // CRITICAL: Update all connection points after any movement to keep chain synced
                editor.updateAllConnectionPoints();
            } else {
                if (editor.stretchingLink.device2) {
                    const device2 = editor.objects.find(obj => obj.id === editor.stretchingLink.device2);
                    if (device2) {
                        const dx = finalX - device2.x;
                        const dy = finalY - device2.y;
                        const distance = Math.sqrt(dx * dx + dy * dy);
                        // Detach if moved more than device radius + 30px away (more forgiving)
                        if (distance > (device2.radius + 30)) {
                            const detachedFrom = device2.label || device2.id;
                            editor.stretchingLink.device2 = null;
                            delete editor.stretchingLink.device2Angle; // Clear stored angle on detach
                            
                            // CRITICAL: Change originType from QL to UL when link is detached
                            if (editor.stretchingLink.originType === 'QL') {
                                editor.stretchingLink.originType = 'UL';
                            }
                            
                            // TRACKING: Log detachment
                            if (editor._bulTrackingData) {
                                const trackData = editor._bulTrackingData.links.find(l => l.id === editor.stretchingLink.id);
                                if (trackData) {
                                    trackData.detachments = (trackData.detachments || 0) + 1;
                                }
                            }
                            
                            if (editor.debugger) {
                                // Calculate UL and TP numbers
                                const allLinks = editor.getAllMergedLinks(editor.stretchingLink);
                                const ulNum = allLinks.findIndex(l => l.id === editor.stretchingLink.id) + 1;
                                
                                // Find TP number for end endpoint
                                // FIXED: Use clearer logic - endpoint is TP if NOT connected
                                const tpsInBUL = [];
                                allLinks.forEach(chainLink => {
                                    let sIsConnected = false;
                                    if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'end') sIsConnected = true;
                                    if (chainLink.mergedInto) {
                                        const prnt = editor.objects.find(o => o.id === chainLink.mergedInto.parentId);
                                        if (prnt?.mergedWith && prnt.mergedWith.childFreeEnd === 'end') sIsConnected = true;
                                    }
                                    if (!sIsConnected) tpsInBUL.push({ linkId: chainLink.id, endpoint: 'start' });
                                    
                                    let eIsConnected = false;
                                    if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'start') eIsConnected = true;
                                    if (chainLink.mergedInto) {
                                        const prnt = editor.objects.find(o => o.id === chainLink.mergedInto.parentId);
                                        if (prnt?.mergedWith && prnt.mergedWith.childFreeEnd === 'start') eIsConnected = true;
                                    }
                                    if (!eIsConnected) tpsInBUL.push({ linkId: chainLink.id, endpoint: 'end' });
                                });
                                
                                // FIXED: Sort TPs by UL number so TP-1 is always on lowest UL, TP-2 on highest
                                tpsInBUL.sort((a, b) => {
                                    const ulNumA = parseInt(a.linkId.split('_')[1]) || 0;
                                    const ulNumB = parseInt(b.linkId.split('_')[1]) || 0;
                                    return ulNumA - ulNumB;
                                });
                                
                                const tpIdx = tpsInBUL.findIndex(tp => tp.linkId === editor.stretchingLink.id && tp.endpoint === 'end');
                                const tpNum = (tpIdx >= 0) ? tpIdx + 1 : '?';
                                
                                editor.debugger.logInfo(`[DETACH] U${ulNum}-TP-${tpNum}(end) from ${detachedFrom}`);
                            }
                        } else {
                            // Keep attached - snap to device edge (shape-aware)
                            const angle = Math.atan2(finalY - device2.y, finalX - device2.x);
                            const edgePoint = editor.getLinkConnectionPoint(device2, angle);
                            finalX = edgePoint.x;
                            finalY = edgePoint.y;
                        }
                    }
                }
                editor.stretchingLink.end = { x: finalX, y: finalY };
                
                // TRACKING: Detect position jumps for this endpoint
                if (editor._bulTrackingData) {
                    const trackData = editor._bulTrackingData.links.find(l => l.id === editor.stretchingLink.id);
                    if (trackData) {
                        const lastEnd = trackData.lastPos.end;
                        const jump = Math.sqrt(
                            Math.pow(finalX - lastEnd.x, 2) + 
                            Math.pow(finalY - lastEnd.y, 2)
                        );
                        
                        // Detect jumps - threshold scales with zoom to avoid false positives
                        const zoomAdjustedThreshold = 500 / Math.min(editor.zoom, 1);
                        if (jump > zoomAdjustedThreshold) {
                            editor._bulTrackingData.totalJumps++;
                            if (editor.debugger) {
                                editor.debugger.logWarning(`Large move: ${editor.stretchingLink.id} END moved ${jump.toFixed(1)}px (threshold: ${zoomAdjustedThreshold.toFixed(0)}px)`);
                            }
                        }
                        
                        // Update tracking
                        trackData.lastPos.end = { x: finalX, y: finalY };
                    }
                }
                
                // ENHANCED: TP stretching in BUL chains - only update THIS link's endpoint
                // TPs are free endpoints and don't affect other links in the chain
                // Only MPs (connection points) move multiple links together
                
                // CRITICAL: When stretching a TP (not MP), we only move this link's endpoint
                // The connection points (MPs) stay fixed - they only move when explicitly dragged
                // This ensures fluid, independent TP movement in BUL chains
                
                // Update connection point metadata if this endpoint is part of a merge
                // But only update metadata, don't move other links (they stay fixed)
                if (editor.stretchingLink.mergedWith) {
                    const parentFreeEnd = editor.stretchingLink.mergedWith.parentFreeEnd;
                    const parentConnectedEnd = parentFreeEnd === 'start' ? 'end' : 'start';
                    
                    // If we're stretching the connected end (MP), update connection point
                    if (editor.stretchingEndpoint === parentConnectedEnd && editor.stretchingConnectionPoint) {
                        const newConnectionX = finalX;
                        const newConnectionY = finalY;
                        
                        // Update connection point in metadata
                        if (editor.stretchingLink.mergedWith.connectionPoint) {
                            editor.stretchingLink.mergedWith.connectionPoint.x = newConnectionX;
                            editor.stretchingLink.mergedWith.connectionPoint.y = newConnectionY;
                        }
                        
                        // Also update child link's endpoint if it's connected here
                        const childLink = editor.objects.find(o => o.id === editor.stretchingLink.mergedWith.linkId);
                        if (childLink && childLink.mergedInto) {
                        const childConnectedEnd = editor.stretchingLink.mergedWith.childConnectionEndpoint ||
                            (editor.stretchingLink.mergedWith.childFreeEnd === 'start' ? 'end' : 'start');
                            
                        if (childConnectedEnd === 'start') {
                            childLink.start.x = newConnectionX;
                            childLink.start.y = newConnectionY;
                        } else {
                            childLink.end.x = newConnectionX;
                            childLink.end.y = newConnectionY;
                        }
                        
                            if (childLink.mergedInto.connectionPoint) {
                            childLink.mergedInto.connectionPoint.x = newConnectionX;
                            childLink.mergedInto.connectionPoint.y = newConnectionY;
                            }
                        }
                    }
                } else if (editor.stretchingLink.mergedInto) {
                    // This is a child link - update parent's connection point if we're dragging the connected end
                    const parentLink = editor.objects.find(o => o.id === editor.stretchingLink.mergedInto.parentId);
                    if (parentLink && parentLink.mergedWith) {
                        const childFreeEnd = parentLink.mergedWith.childFreeEnd;
                        const childConnectedEnd = childFreeEnd === 'start' ? 'end' : 'start';
                        
                        // If stretching the connected end (MP), update connection point
                        if (editor.stretchingEndpoint === childConnectedEnd && editor.stretchingConnectionPoint) {
                            const newConnectionX = finalX;
                            const newConnectionY = finalY;
                            
                            // Update parent's endpoint
                            const parentConnectedEnd = parentLink.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start';
                        if (parentConnectedEnd === 'start') {
                            parentLink.start.x = newConnectionX;
                            parentLink.start.y = newConnectionY;
                        } else {
                            parentLink.end.x = newConnectionX;
                            parentLink.end.y = newConnectionY;
                        }
                        
                            // Update connection point metadata
                            if (parentLink.mergedWith.connectionPoint) {
                            parentLink.mergedWith.connectionPoint.x = newConnectionX;
                            parentLink.mergedWith.connectionPoint.y = newConnectionY;
                        }
                            if (editor.stretchingLink.mergedInto.connectionPoint) {
                        editor.stretchingLink.mergedInto.connectionPoint.x = newConnectionX;
                        editor.stretchingLink.mergedInto.connectionPoint.y = newConnectionY;
                            }
                    }
                }
                }
                
                // CRITICAL: Update all connection points after any movement to keep chain synced
                editor.updateAllConnectionPoints();
            }
            
            // TRACKING: Check ALL links in BUL chain for unexpected jumps
            if (editor._bulTrackingData) {
                const allMergedLinks = editor.getAllMergedLinks(editor.stretchingLink);
                // Zoom-adjusted threshold for chain jump detection
                const chainJumpThreshold = 50 / Math.min(editor.zoom, 1);
                
                allMergedLinks.forEach(link => {
                    const trackData = editor._bulTrackingData.links.find(l => l.id === link.id);
                    if (trackData) {
                        // Check start position
                        const startJump = Math.sqrt(
                            Math.pow(link.start.x - trackData.lastPos.start.x, 2) + 
                            Math.pow(link.start.y - trackData.lastPos.start.y, 2)
                        );
                        
                        if (startJump > chainJumpThreshold && link.id !== editor.stretchingLink.id) {
                            editor._bulTrackingData.totalJumps++;
                            if (editor.debugger) {
                                editor.debugger.logError(`[CHAIN JUMP] ${link.id} START moved ${startJump.toFixed(1)}px unexpectedly!`);
                                editor.debugger.logInfo(`   This link was NOT being dragged - BUG DETECTED!`);
                            }
                        }
                        
                        // Check end position
                        const endJump = Math.sqrt(
                            Math.pow(link.end.x - trackData.lastPos.end.x, 2) + 
                            Math.pow(link.end.y - trackData.lastPos.end.y, 2)
                        );
                        
                        if (endJump > chainJumpThreshold && link.id !== editor.stretchingLink.id) {
                            editor._bulTrackingData.totalJumps++;
                            if (editor.debugger) {
                                editor.debugger.logError(`[CHAIN JUMP] ${link.id} END moved ${endJump.toFixed(1)}px unexpectedly!`);
                                editor.debugger.logInfo(`   This link was NOT being dragged - BUG DETECTED!`);
                            }
                        }
                        
                        // Update positions for next frame
                        trackData.lastPos.start = { x: link.start.x, y: link.start.y };
                        trackData.lastPos.end = { x: link.end.x, y: link.end.y };
                    }
                });
            }
            
            // REAL-TIME CP UPDATE: Keep curve points synchronized during TP stretch
            editor._updateCurvePointsDuringStretch();
            
            editor.scheduleDraw();
            editor.updateHud(pos);
            return;
        }
        
        // Handle device rotation
        if (editor.rotatingDevice) {
            editor.canvas.style.cursor = 'grabbing'; // Show grabbing cursor during rotation
            const currentAngle = Math.atan2(pos.y - editor.rotatingDevice.y, pos.x - editor.rotatingDevice.x);
            const angleDiff = (currentAngle - editor.rotationStartAngle) * 180 / Math.PI;
            let newRotation = (editor.rotationStartValue + angleDiff + 360) % 360;
            if (newRotation < 0) newRotation += 360;
            
            editor.rotatingDevice.rotation = newRotation;
            
            // GROUP ROTATION: If this device belongs to a group, rotate all members around it
            const device = editor.rotatingDevice;
            if (device.groupId) {
                const rotationCenter = { x: device.x, y: device.y };
                const rotationDelta = angleDiff * Math.PI / 180; // Convert to radians
                
                const groupMembers = editor.getGroupMembers(device);
                groupMembers.forEach(member => {
                    if (member.id === device.id || member.locked) return;
                    
                    // Get member center
                    const memberCenter = member.type === 'unbound'
                        ? { x: (member.start.x + member.end.x) / 2, y: (member.start.y + member.end.y) / 2 }
                        : { x: member.x, y: member.y };
                    
                    // Calculate offset from rotation center
                    const dx = memberCenter.x - rotationCenter.x;
                    const dy = memberCenter.y - rotationCenter.y;
                    
                    // Rotate the offset around rotation center
                    const cos = Math.cos(rotationDelta);
                    const sin = Math.sin(rotationDelta);
                    const newDx = dx * cos - dy * sin;
                    const newDy = dx * sin + dy * cos;
                    
                    // Apply new position
                    if (member.type === 'unbound') {
                        const moveDx = newDx - dx;
                        const moveDy = newDy - dy;
                        member.start.x += moveDx;
                        member.start.y += moveDy;
                        member.end.x += moveDx;
                        member.end.y += moveDy;
                        if (member.manualCurvePoint) {
                            member.manualCurvePoint.x += moveDx;
                            member.manualCurvePoint.y += moveDy;
                        }
                        if (member.manualControlPoint) {
                            member.manualControlPoint.x += moveDx;
                            member.manualControlPoint.y += moveDy;
                        }
                    } else {
                        member.x = rotationCenter.x + newDx;
                        member.y = rotationCenter.y + newDy;
                        // Also rotate the member's own rotation
                        if (member.rotation !== undefined) {
                            member.rotation = ((member.rotation || 0) + angleDiff) % 360;
                            if (member.rotation < 0) member.rotation += 360;
                        }
                    }
                });
            }
            
            editor.scheduleDraw();
            editor.updateHud(pos);
            return;
        }
        
        // Handle device resizing
        if (editor.resizingDevice) {
            editor.canvas.style.cursor = editor.resizeHandle
                ? MouseMoveHandler._rotatedCursor(editor.resizeHandle, editor.resizingDevice.rotation || 0)
                : 'nwse-resize';
            
            // FIX: Use delta-based resizing to prevent size jumps when grabbing the handle
            // Calculate initial distance from center to start position (on first move)
            if (!editor.resizeStartDist) {
                editor.resizeStartDist = Math.sqrt(
                    Math.pow(editor.resizeStartPos.x - editor.resizingDevice.x, 2) + 
                    Math.pow(editor.resizeStartPos.y - editor.resizingDevice.y, 2)
                );
            }
            
            // Calculate current distance from device center to mouse
            const currentDist = Math.sqrt(
                Math.pow(pos.x - editor.resizingDevice.x, 2) + 
                Math.pow(pos.y - editor.resizingDevice.y, 2)
            );
            
            // Calculate the delta (change in distance from start)
            const distDelta = currentDist - editor.resizeStartDist;
            
            // Apply delta to the original starting radius for smooth, jump-free resizing
            let newRadius = editor.resizeStartRadius + distDelta;
            
            // Clamp radius to reasonable bounds (increased max from 200 to 500 for larger devices)
            newRadius = Math.max(15, Math.min(500, newRadius));
            
            editor.resizingDevice.radius = newRadius;
            
            // Update device editor if it's open
            const sizeSlider = document.getElementById('editor-device-size');
            const sizeValue = document.getElementById('editor-device-size-value');
            if (sizeSlider) sizeSlider.value = Math.round(newRadius);
            if (sizeValue) sizeValue.textContent = Math.round(newRadius);
            
            editor.scheduleDraw();
            editor.updateHud(pos);
            return;
        }
        
        // Handle shape rotation
        if (editor.rotatingShape && editor._shapeRotationStart) {
            editor.canvas.style.cursor = 'grabbing';
            const shape = editor.rotatingShape;
            const centerX = shape.x;
            const centerY = shape.y;
            
            // Calculate current angle from center to mouse
            const currentAngle = Math.atan2(pos.y - centerY, pos.x - centerX);
            const startAngle = editor._shapeRotationStart.startAngle;
            const originalRotation = editor._shapeRotationStart.originalRotation;
            
            // Calculate delta angle and convert to degrees
            let deltaAngle = (currentAngle - startAngle) * (180 / Math.PI);
            let newRotation = originalRotation + deltaAngle;
            
            // Normalize to 0-360
            while (newRotation < 0) newRotation += 360;
            while (newRotation >= 360) newRotation -= 360;
            
            // Snap to 15° increments if shift is held
            if (editor._shiftHeld) {
                newRotation = Math.round(newRotation / 15) * 15;
            }
            
            shape.rotation = newRotation;
            
            editor.scheduleDraw();
            editor.updateHud(pos);
            return;
        }
        
        // Handle shape resizing
        if (editor.resizingShape && editor.shapeResizeHandle) {
            const shape = editor.resizingShape;
            const handle = editor.shapeResizeHandle;

            // Transform mouse delta into shape-local coordinates (accounting for rotation)
            const rot = (shape.rotation || 0) * Math.PI / 180;
            const rawDx = pos.x - editor._shapeResizeStart.x;
            const rawDy = pos.y - editor._shapeResizeStart.y;
            const dx = rawDx * Math.cos(-rot) - rawDy * Math.sin(-rot);
            const dy = rawDx * Math.sin(-rot) + rawDy * Math.cos(-rot);

            const origCenterX = editor._shapeResizeStart.centerX || shape.x;
            const origCenterY = editor._shapeResizeStart.centerY || shape.y;
            const startWidth = editor._shapeResizeStart.width;
            const startHeight = editor._shapeResizeStart.height;

            let newWidth = startWidth;
            let newHeight = startHeight;
            let newCx = origCenterX;
            let newCy = origCenterY;

            const isCircle = shape.shapeType === 'circle';
            const uniformTypes = ['diamond', 'triangle', 'star', 'hexagon', 'checkmark', 'cross'];
            const isUniform = uniformTypes.includes(shape.shapeType);

            const isCorner = ['nw', 'ne', 'sw', 'se'].includes(handle);
            const isEdge = ['n', 's', 'e', 'w'].includes(handle);

            if (isCorner) {
                // Corner handles: free resize anchored at opposite corner
                const signX = handle.includes('e') ? 1 : -1;
                const signY = handle.includes('s') ? 1 : -1;
                newWidth = Math.max(20, startWidth + signX * dx);
                newHeight = Math.max(20, startHeight + signY * dy);
                // Shift center so opposite corner stays fixed
                const localShiftX = (newWidth - startWidth) * signX / 2;
                const localShiftY = (newHeight - startHeight) * signY / 2;
                newCx = origCenterX + localShiftX * Math.cos(rot) - localShiftY * Math.sin(rot);
                newCy = origCenterY + localShiftX * Math.sin(rot) + localShiftY * Math.cos(rot);
            } else if (isEdge) {
                if (isCircle) {
                    // Circle: any edge handle changes radius uniformly
                    let delta = 0;
                    if (handle === 'e') delta = dx;
                    else if (handle === 'w') delta = -dx;
                    else if (handle === 's') delta = dy;
                    else if (handle === 'n') delta = -dy;
                    newWidth = Math.max(20, startWidth + delta * 2);
                    newHeight = newWidth;
                } else if (isUniform) {
                    // Uniform shapes: edge handles scale proportionally
                    let delta = 0;
                    if (handle === 'e') delta = dx;
                    else if (handle === 'w') delta = -dx;
                    else if (handle === 's') delta = dy;
                    else if (handle === 'n') delta = -dy;
                    const scale = Math.max(0.1, (startWidth + delta * 2) / startWidth);
                    newWidth = Math.max(20, startWidth * scale);
                    newHeight = Math.max(20, startHeight * scale);
                } else {
                    // Rect/ellipse/cloud: axis-constrained, anchor opposite edge
                    if (handle === 'e') {
                        newWidth = Math.max(20, startWidth + dx);
                        const localShift = (newWidth - startWidth) / 2;
                        newCx = origCenterX + localShift * Math.cos(rot);
                        newCy = origCenterY + localShift * Math.sin(rot);
                    } else if (handle === 'w') {
                        newWidth = Math.max(20, startWidth - dx);
                        const localShift = -(newWidth - startWidth) / 2;
                        newCx = origCenterX + localShift * Math.cos(rot);
                        newCy = origCenterY + localShift * Math.sin(rot);
                    } else if (handle === 's') {
                        newHeight = Math.max(20, startHeight + dy);
                        const localShift = (newHeight - startHeight) / 2;
                        newCx = origCenterX - localShift * Math.sin(rot);
                        newCy = origCenterY + localShift * Math.cos(rot);
                    } else if (handle === 'n') {
                        newHeight = Math.max(20, startHeight - dy);
                        const localShift = -(newHeight - startHeight) / 2;
                        newCx = origCenterX - localShift * Math.sin(rot);
                        newCy = origCenterY + localShift * Math.cos(rot);
                    }
                }
            }

            shape.width = Math.max(20, newWidth);
            shape.height = Math.max(20, newHeight);
            shape.x = newCx;
            shape.y = newCy;

            if (editor.shapeSnapToGrid) {
                const gridSize = 20;
                shape.width = Math.round(shape.width / gridSize) * gridSize;
                shape.height = Math.round(shape.height / gridSize) * gridSize;
                if (isCircle) shape.height = shape.width;
                shape.x = Math.round(shape.x / gridSize) * gridSize;
                shape.y = Math.round(shape.y / gridSize) * gridSize;
            }

            editor.canvas.style.cursor = MouseMoveHandler._rotatedCursor(handle, shape.rotation || 0);
            editor.scheduleDraw();
            return;
        }
        
        // Handle text rotation
        if (editor.rotatingText && editor.selectedObject && editor.selectedObject.type === 'text') {
            const mouseAngle = Math.atan2(pos.y - editor.selectedObject.y, pos.x - editor.selectedObject.x);
            const angleDiff = (mouseAngle - editor.textRotationStartAngle) * 180 / Math.PI;
            let newRotation = (editor.textRotationStartRot + angleDiff) % 360;
            if (newRotation < 0) newRotation += 360;
            
            editor.selectedObject.rotation = newRotation;
            
            // GROUP ROTATION: If this object belongs to a group, rotate all members around the rotated object
            if (editor.selectedObject.groupId) {
                const rotatedObj = editor.selectedObject;
                const rotationCenter = { x: rotatedObj.x, y: rotatedObj.y };
                const rotationDelta = (angleDiff) * Math.PI / 180; // Convert to radians
                
                const groupMembers = editor.getGroupMembers(rotatedObj);
                groupMembers.forEach(member => {
                    if (member.id === rotatedObj.id || member.locked) return;
                    
                    // Get member center
                    const memberCenter = member.type === 'unbound'
                        ? { x: (member.start.x + member.end.x) / 2, y: (member.start.y + member.end.y) / 2 }
                        : { x: member.x, y: member.y };
                    
                    // Calculate offset from rotation center
                    const dx = memberCenter.x - rotationCenter.x;
                    const dy = memberCenter.y - rotationCenter.y;
                    
                    // Rotate the offset around rotation center
                    const cos = Math.cos(rotationDelta);
                    const sin = Math.sin(rotationDelta);
                    const newDx = dx * cos - dy * sin;
                    const newDy = dx * sin + dy * cos;
                    
                    // Apply new position
                    if (member.type === 'unbound') {
                        const moveDx = newDx - dx;
                        const moveDy = newDy - dy;
                        member.start.x += moveDx;
                        member.start.y += moveDy;
                        member.end.x += moveDx;
                        member.end.y += moveDy;
                        if (member.manualCurvePoint) {
                            member.manualCurvePoint.x += moveDx;
                            member.manualCurvePoint.y += moveDy;
                        }
                        if (member.manualControlPoint) {
                            member.manualControlPoint.x += moveDx;
                            member.manualControlPoint.y += moveDy;
                        }
                    } else {
                        member.x = rotationCenter.x + newDx;
                        member.y = rotationCenter.y + newDy;
                        // Also rotate the member's own rotation
                        if (member.rotation !== undefined) {
                            member.rotation = ((member.rotation || 0) + angleDiff) % 360;
                            if (member.rotation < 0) member.rotation += 360;
                        }
                    }
                });
            }
            
            // Update UI elements if they exist
            const slider = document.getElementById('rotation-slider');
            const value = document.getElementById('rotation-value');
            if (slider) slider.value = Math.round(newRotation);
            if (value) value.textContent = Math.round(newRotation) + '°';
            
            editor.scheduleDraw();
            editor.updateHud(pos);
            return;
        }
        
        // Handle text resizing
        if (editor.resizingText && editor.selectedObject) {
            const currentDist = Math.sqrt(
                Math.pow(pos.x - editor.selectedObject.x, 2) + 
                Math.pow(pos.y - editor.selectedObject.y, 2)
            );
            const distRatio = currentDist / editor.textResizeStartDist;
            // Increased max font size from 72 to 200 for larger text
            const newSize = Math.max(8, Math.min(200, editor.textResizeStartSize * distRatio));
            editor.selectedObject.fontSize = Math.round(newSize);
            const fontSizeEl = document.getElementById('font-size');
            if (fontSizeEl) fontSizeEl.value = Math.round(newSize);
            editor.scheduleDraw();
            editor.updateHud(pos);
            return;
        }
        
        // Handle multi-select drag (from marquee selection or group)
        if (editor.dragging && editor.selectedObjects.length > 1 && editor.multiSelectInitialPositions) {
            // DEDUP: Prevent double-processing from pointer+mouse events firing for same movement
            const now = Date.now();
            if (editor._lastMultiDragTime && (now - editor._lastMultiDragTime) < 8) {
                return; // Skip duplicate event within 8ms
            }
            editor._lastMultiDragTime = now;
            
            // Calculate simple mouse movement delta (works even after MS exits to base mode)
            const dx = pos.x - editor.dragStart.x;
            const dy = pos.y - editor.dragStart.y;
            
            // COLLISION FIX: For multi-device drag, we need to resolve collisions iteratively
            // First pass: calculate proposed positions for all devices
            const proposedPositions = new Map();
            
            // Get all unlocked device objects (check collision only if deviceCollision is ON)
            const deviceObjects = editor.selectedObjects.filter(obj => 
                obj.type === 'device' && !obj.locked
            );
            
            // Only calculate collision if deviceCollision is enabled
            if (editor.deviceCollision) {
                deviceObjects.forEach(obj => {
                    const initialPos = editor.multiSelectInitialPositions.find(p => p.id === obj.id);
                    if (initialPos) {
                        let newX = initialPos.x + dx;
                        let newY = initialPos.y + dy;
                        
                        // First collision check against non-moving devices
                        const proposedPos = editor.checkDeviceCollision(obj, newX, newY);
                        proposedPositions.set(obj.id, { x: proposedPos.x, y: proposedPos.y });
                    }
                });
            }
            
            // Second pass: resolve collisions between moving devices themselves
            if (deviceObjects.length > 1 && editor.deviceCollision) {
                const maxIterations = 5;
                for (let iter = 0; iter < maxIterations; iter++) {
                    let adjusted = false;
                    for (let i = 0; i < deviceObjects.length; i++) {
                        const obj1 = deviceObjects[i];
                        const pos1 = proposedPositions.get(obj1.id);
                        if (!pos1) continue;
                        
                        for (let j = i + 1; j < deviceObjects.length; j++) {
                            const obj2 = deviceObjects[j];
                            const pos2 = proposedPositions.get(obj2.id);
                            if (!pos2) continue;
                            
                            const dx_coll = pos1.x - pos2.x;
                            const dy_coll = pos1.y - pos2.y;
                            let dist = Math.sqrt(dx_coll * dx_coll + dy_coll * dy_coll);
                            
                            // SHAPE-ACCURATE COLLISION: Calculate angle and get direction-aware radii
                            const angle = Math.atan2(dy_coll, dx_coll);
                            const radius1 = editor.getDeviceCollisionRadiusInDirection(obj1, angle);
                            const radius2 = editor.getDeviceCollisionRadiusInDirection(obj2, angle + Math.PI);
                            const minDist = radius1 + radius2 + 1;  // Minimal gap
                            
                            if (dist < minDist && dist > 0.01) {
                                const push = (minDist - dist) / 2; // Split push between both devices
                                const nx = dx_coll / dist;
                                const ny = dy_coll / dist;
                                
                                pos1.x += nx * push;
                                pos1.y += ny * push;
                                pos2.x -= nx * push;
                                pos2.y -= ny * push;
                                adjusted = true;
                            }
                        }
                    }
                    if (!adjusted) break;
                }
            }
            
            // Collect device IDs that are being moved (for QL CP update)
            const movedDeviceIds = editor.selectedObjects
                .filter(obj => obj.type === 'device' && !obj.locked)
                .map(obj => obj.id);
            
            // Move ALL selected objects by the same offset from their initial positions
            editor.selectedObjects.forEach(obj => {
                    // Skip locked objects
                    if (obj.locked) return;
                    
                    // Skip adjacent text (glued to links)
                    if (obj.type === 'text' && obj.linkId && obj.position) return;
                    
                    // Skip Quick Links (type 'link') - they follow their connected devices automatically
                    // Moving them here would corrupt their x/y properties (which they don't have)
                    if (obj.type === 'link') return;
                    
                    // Handle unbound links - they CAN be moved!
                    if (obj.type === 'unbound') {
                        const initialPos = editor.multiSelectInitialPositions.find(p => p.id === obj.id);
                        if (initialPos && initialPos.startX !== undefined) {
                            // Determine which endpoint devices are in the selection
                            const d1InSelection = obj.device1 && movedDeviceIds.includes(obj.device1);
                            const d2InSelection = obj.device2 && movedDeviceIds.includes(obj.device2);
                            const bothDevicesMoved = (!obj.device1 || d1InSelection) && (!obj.device2 || d2InSelection);
                            
                            // Move free endpoints by full offset; device-attached endpoints
                            // will be overwritten by drawUnboundLink to match device edge
                            obj.start.x = initialPos.startX + dx;
                            obj.start.y = initialPos.startY + dy;
                            obj.end.x = initialPos.endX + dx;
                            obj.end.y = initialPos.endY + dy;
                            
                            // CP shift: full delta when both endpoints move, half when only one does
                            const cpShiftX = bothDevicesMoved ? dx : dx / 2;
                            const cpShiftY = bothDevicesMoved ? dy : dy / 2;
                            
                            if (obj.manualCurvePoint && initialPos.curvePointX !== undefined) {
                                obj.manualCurvePoint.x = initialPos.curvePointX + cpShiftX;
                                obj.manualCurvePoint.y = initialPos.curvePointY + cpShiftY;
                            }
                            if (obj.manualControlPoint && initialPos.controlPointX !== undefined) {
                                obj.manualControlPoint.x = initialPos.controlPointX + cpShiftX;
                                obj.manualControlPoint.y = initialPos.controlPointY + cpShiftY;
                            }
                            
                            // CRITICAL FIX: Only move partner links if they're NOT already in selection
                            // If all links in BUL are selected, they move together naturally
                            // Connection points will be updated by updateAllConnectionPoints() after drag ends
                            // This prevents conflicting updates and jumps in 3+ link BULs
                            
                            // Check if partner is in selection first
                            let partnerInSelection = false;
                            if (obj.mergedWith) {
                                const childLink = editor.objects.find(o => o.id === obj.mergedWith.linkId);
                                partnerInSelection = childLink && editor.selectedObjects.includes(childLink);
                            } else if (obj.mergedInto) {
                                const parentLink = editor.objects.find(o => o.id === obj.mergedInto.parentId);
                                partnerInSelection = parentLink && editor.selectedObjects.includes(parentLink);
                            }
                            
                            // Only do partner dragging if partner is NOT selected
                            if (!partnerInSelection) {
                            // ENHANCED: If this UL is merged, move the connected UL as one unit
                            if (obj.mergedWith) {
                                const childLink = editor.objects.find(o => o.id === obj.mergedWith.linkId);
                                    if (childLink) {
                                    // Move child link's free endpoint (keep connection point synced)
                                    const childFreeEnd = obj.mergedWith.childFreeEnd;
                                    const connectionPoint = obj.mergedWith.connectionPoint;
                                    
                                    // Calculate new connection point position after parent move
                                    const parentConnectedEnd = obj.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start';
                                    const newConnectionX = parentConnectedEnd === 'start' ? obj.start.x : obj.end.x;
                                    const newConnectionY = parentConnectedEnd === 'start' ? obj.start.y : obj.end.y;
                                    
                                    // Calculate offset from old connection point to new
                                    const connDx = newConnectionX - connectionPoint.x;
                                    const connDy = newConnectionY - connectionPoint.y;
                                    
                                    // Move child link maintaining its shape relative to connection
                                    childLink.start.x += connDx;
                                    childLink.start.y += connDy;
                                    childLink.end.x += connDx;
                                    childLink.end.y += connDy;
                                    
                                    // Move curve control points to preserve curve shape
                                    if (childLink.manualCurvePoint) {
                                        childLink.manualCurvePoint.x += connDx;
                                        childLink.manualCurvePoint.y += connDy;
                                    }
                                    if (childLink.manualControlPoint) {
                                        childLink.manualControlPoint.x += connDx;
                                        childLink.manualControlPoint.y += connDy;
                                    }
                                    
                                    // Update connection point
                                    obj.mergedWith.connectionPoint.x = newConnectionX;
                                    obj.mergedWith.connectionPoint.y = newConnectionY;
                                    childLink.mergedInto.connectionPoint.x = newConnectionX;
                                    childLink.mergedInto.connectionPoint.y = newConnectionY;
                                }
                            } else if (obj.mergedInto) {
                                // This is a child link - also move parent
                                const parentLink = editor.objects.find(o => o.id === obj.mergedInto.parentId);
                                    if (parentLink) {
                                    const connectionPoint = obj.mergedInto.connectionPoint;
                                    
                                    // Find which endpoint of child is connected
                                        const parentFreeEnd = parentLink.mergedWith ? parentLink.mergedWith.parentFreeEnd : 'end';
                                        const childConnectedEnd = parentFreeEnd === 'start' ? 'end' : 'start';
                                    const newConnectionX = childConnectedEnd === 'start' ? obj.start.x : obj.end.x;
                                    const newConnectionY = childConnectedEnd === 'start' ? obj.start.y : obj.end.y;
                                    
                                    // Calculate offset
                                    const connDx = newConnectionX - connectionPoint.x;
                                    const connDy = newConnectionY - connectionPoint.y;
                                    
                                    // Move parent link
                                    parentLink.start.x += connDx;
                                    parentLink.start.y += connDy;
                                    parentLink.end.x += connDx;
                                    parentLink.end.y += connDy;
                                    
                                    // Move curve control points to preserve curve shape
                                    if (parentLink.manualCurvePoint) {
                                        parentLink.manualCurvePoint.x += connDx;
                                        parentLink.manualCurvePoint.y += connDy;
                                    }
                                    if (parentLink.manualControlPoint) {
                                        parentLink.manualControlPoint.x += connDx;
                                        parentLink.manualControlPoint.y += connDy;
                                    }
                                    
                                    // Update connection points
                                    if (parentLink.mergedWith) {
                                        parentLink.mergedWith.connectionPoint.x = newConnectionX;
                                        parentLink.mergedWith.connectionPoint.y = newConnectionY;
                                    }
                                    obj.mergedInto.connectionPoint.x = newConnectionX;
                                    obj.mergedInto.connectionPoint.y = newConnectionY;
                                }
                            }
                            }
                            // If partner IS in selection, connection points will be updated by updateAllConnectionPoints() at the end
                            
                            // Log to debugger (only once per drag, not every frame)
                            if (editor.debugger && !editor._unboundLinkMoveLogged) {
                                editor._unboundLinkMoveLogged = true;
                                const mergedInfo = obj.mergedWith ? ' (merged unit)' : obj.mergedInto ? ' (merged unit)' : '';
                                editor.debugger.logSuccess(`↔️ Unbound link moved in MS mode${mergedInfo}`);
                            }
                        }
                        return;
                    }
                    
                    // Use proposed position if collision was calculated, otherwise use simple offset
                    if (editor.deviceCollision && obj.type === 'device') {
                        const proposedPos = proposedPositions.get(obj.id);
                        if (proposedPos) {
                            const oldX = obj.x;
                            const oldY = obj.y;
                            obj.x = proposedPos.x;
                            obj.y = proposedPos.y;
                            
                            // Apply movable device chain reaction (push nearby devices)
                            if (editor.movableDevices) {
                                // Amplify velocity during multi-select drag for better chain reactions
                                const dragAmplification = 2.0;
                                const velocityX = (proposedPos.x - oldX) * dragAmplification;
                                const velocityY = (proposedPos.y - oldY) * dragAmplification;
                                editor.applyDeviceChainReaction(obj, velocityX, velocityY);
                            }
                            return;
                        }
                    }
                    
                    const initialPos = editor.multiSelectInitialPositions.find(p => p.id === obj.id);
                    // Only update x/y for objects that have valid initial positions
                    // This prevents corrupting links or other objects without x/y properties
                    if (initialPos && typeof initialPos.x === 'number' && typeof initialPos.y === 'number') {
                        const oldX = obj.x;
                        const oldY = obj.y;
                        const newX = initialPos.x + dx;
                        const newY = initialPos.y + dy;
                        
                        obj.x = newX;
                        obj.y = newY;
                    }
                }
            );
            
            // ENHANCED: Update Quick Link CPs using INITIAL positions (not cumulative)
            // This prevents CP drift when moving devices with curved QLs
            if (editor._initialQuickLinkCPs && editor._initialQuickLinkCPs.length > 0) {
                for (const init of editor._initialQuickLinkCPs) {
                    const ql = editor.objects.find(o => o.id === init.id);
                    if (!ql) continue;
                    
                    // Calculate shift: full delta if both endpoints moved, half if only one
                    const shiftX = init.bothEndpointsMoved ? dx : dx / 2;
                    const shiftY = init.bothEndpointsMoved ? dy : dy / 2;
                    
                    // Set CP to initial position + shift (ABSOLUTE, not cumulative)
                    if (ql.manualCurvePoint && init.curvePointX !== undefined) {
                        ql.manualCurvePoint.x = init.curvePointX + shiftX;
                        ql.manualCurvePoint.y = init.curvePointY + shiftY;
                    }
                    if (ql.manualControlPoint && init.controlPointX !== undefined) {
                        ql.manualControlPoint.x = init.controlPointX + shiftX;
                        ql.manualControlPoint.y = init.controlPointY + shiftY;
                    }
                }
            }
            
            // CRITICAL FIX: Update attached Unbound Link CPs using INITIAL positions
            if (editor._initialAttachedULCPs && editor._initialAttachedULCPs.length > 0) {
                for (const init of editor._initialAttachedULCPs) {
                    const ul = editor.objects.find(o => o.id === init.id);
                    if (!ul || !ul.manualCurvePoint) continue;
                    
                    // Calculate shift: full delta if both endpoints moved, half if only one
                    const shiftX = init.bothEndpointsMoved ? dx : dx / 2;
                    const shiftY = init.bothEndpointsMoved ? dy : dy / 2;
                    
                    // Set CP to initial position + shift (ABSOLUTE, not cumulative)
                    ul.manualCurvePoint.x = init.curvePointX + shiftX;
                    ul.manualCurvePoint.y = init.curvePointY + shiftY;
                }
            }
            
            // CRITICAL: Update all connection points after multi-select dragging
            // This ensures MPs stay synchronized when dragging 3+ link BULs
            editor.updateAllConnectionPoints();
            
            editor.scheduleDraw();
            return;
        }

        // Instant marquee activation on drag - smooth and fast like Ctrl+drag
        if (!editor.marqueeActive && editor.selectionRectStart && editor.marqueeTimer) {
            const dx = Math.abs(pos.x - editor.selectionRectStart.x);
            const dy = Math.abs(pos.y - editor.selectionRectStart.y);

            // If mouse moves more than 3 pixels, immediately start marquee (very fast response)
            if (dx > 3 || dy > 3) {
                clearTimeout(editor.marqueeTimer);
                editor.marqueeTimer = null;
                editor.startMarqueeSelection(editor.selectionRectStart);
            }
        }
        
        // Handle marquee selection rectangle drawing
        if (editor.marqueeActive && editor.selectionRectStart) {
            const start = editor.selectionRectStart;
            editor.selectionRectangle = {
                x: Math.min(start.x, pos.x),
                y: Math.min(start.y, pos.y),
                width: Math.abs(pos.x - start.x),
                height: Math.abs(pos.y - start.y)
            };
            
            // Find all objects that intersect with rectangle
            editor.selectedObjects = editor.findObjectsInRectangle(editor.selectionRectangle);
            
            // Expand BUL chains: if any UL of a BUL is selected, include the whole chain
            const bulExpanded = [];
            editor.selectedObjects.forEach(obj => {
                if (obj.type === 'unbound' && (obj.mergedWith || obj.mergedInto)) {
                    const chain = editor.getAllMergedLinks(obj);
                    chain.forEach(link => {
                        if (!editor.selectedObjects.includes(link) && !bulExpanded.includes(link)) {
                            bulExpanded.push(link);
                        }
                    });
                }
            });
            if (bulExpanded.length > 0) {
                editor.selectedObjects.push(...bulExpanded);
            }
            
            if (editor.selectedObjects.length > 0) {
                editor.selectedObject = editor.selectedObjects[0];
            }
            
            editor.scheduleDraw();
            return;
        }
        
        if (editor.dragging && editor.selectedObject) {
            // Don't allow dragging locked objects
            if (editor.selectedObject.locked) {
                return;
            }
            
            // GROUP DRAG SAFETY NET: If dragging a grouped object but not all members selected,
            // expand selection and convert to multi-select drag with CORRECT dragStart
            if (editor.selectedObject.groupId && editor.selectedObjects.length === 1) {
                const groupMembers = editor.getGroupMembers(editor.selectedObject);
                if (groupMembers.length > 1) {
                    // Add all group members to selection
                    groupMembers.forEach(member => {
                        if (!editor.selectedObjects.includes(member)) {
                            editor.selectedObjects.push(member);
                        }
                    });
                    
                    // CRITICAL FIX: Reset dragStart to ABSOLUTE mouse position
                    // Single-object drag stores OFFSET in dragStart, but multi-select needs ABSOLUTE
                    editor.dragStart = { x: pos.x, y: pos.y };
                    
                    // Always capture FRESH positions at this moment
                    editor.multiSelectInitialPositions = editor.selectedObjects.map(obj => {
                        const initPos = { id: obj.id, x: obj.x, y: obj.y };
                        if (obj.type === 'unbound') {
                            initPos.startX = obj.start.x;
                            initPos.startY = obj.start.y;
                            initPos.endX = obj.end.x;
                            initPos.endY = obj.end.y;
                            initPos.curvePointX = obj.manualCurvePoint?.x;
                            initPos.curvePointY = obj.manualCurvePoint?.y;
                            initPos.controlPointX = obj.manualControlPoint?.x;
                            initPos.controlPointY = obj.manualControlPoint?.y;
                        }
                        return initPos;
                    });
                    // Return immediately - multi-select handler above will pick up next frame
                    return;
                }
            }
            
            // CRITICAL FIX: Regular links (bound to devices) are NOT draggable!
            if (editor.selectedObject.type === 'link') {
                // Regular links can't be moved - they follow their connected devices
                return;
            }
            
            // Handle dragging adjacent text (text attached to links)
            // ENHANCED: Dragging attached text moves the ENTIRE BUL chain (all merged links)
            if (editor.selectedObject.type === 'text' && editor.selectedObject.linkId) {
                const textObj = editor.selectedObject;
                const link = editor.objects.find(obj => obj.id === textObj.linkId);
                
                // CRITICAL FIX (Dec 2025): Deduplicate pointer/mouse events that fire for same physical movement
                // Skip events within 8ms of the last processed event
                // This prevents oscillation from pointer+mouse events having slightly different positions
                // while still allowing ~120 events per second for smooth dragging
                const now = Date.now();
                if (editor._lastAttachedTextMoveTime && (now - editor._lastAttachedTextMoveTime) < 8) {
                    // Skip duplicate event
                    return;
                }
                editor._lastAttachedTextMoveTime = now;
                
                // CRITICAL: Middle-position TBs ALWAYS control the curve (skip link body movement)
                // This makes the TB act as the curve control point for ANY link type
                const isMiddlePositionTB = textObj.position === 'middle';
                
                // Check if link exists and has valid start/end positions
                // BUT: Skip link body movement for middle-position TBs - they control the curve instead
                if (link && link.start && link.end && !isMiddlePositionTB &&
                    (link.type === 'unbound' || !link.device1 || !link.device2)) {
                    
                    // Validate that start/end have valid coordinates
                    if (link.start.x === undefined || link.start.y === undefined ||
                        link.end.x === undefined || link.end.y === undefined) {
                        console.warn('Attached text drag: Link has invalid start/end positions');
                        return;
                    }
                    
                    // ENHANCED: Get ALL links in the BUL chain (if this is part of a BUL)
                    const allLinksInChain = editor.getAllMergedLinks(link);
                    
                    // Initialize dragging state if needed - MUST be done BEFORE calculating delta
                    // CRITICAL FIX (Dec 2025): Store the MOUSE position at drag start, not use offset-based dragStart
                    // ENHANCED: Store initial positions for ALL links in the BUL chain
                    if (!editor._attachedTextDragStart) {
                        const chainPositions = [];
                        for (const chainLink of allLinksInChain) {
                            chainPositions.push({
                                linkId: chainLink.id,
                                startX: chainLink.start.x,
                                startY: chainLink.start.y,
                                endX: chainLink.end.x,
                                endY: chainLink.end.y,
                                device1: chainLink.device1,
                                device2: chainLink.device2
                            });
                        }
                        
                        editor._attachedTextDragStart = {
                            mouseStartX: pos.x,  // Store actual mouse position at drag start
                            mouseStartY: pos.y,
                            textX: textObj.x,
                            textY: textObj.y,
                            chainPositions: chainPositions  // Store all chain link positions
                        };
                    }
                    
                    // CRITICAL FIX (Dec 2025): Calculate delta from stored mouse start position, not offset-based dragStart
                    const dx = pos.x - editor._attachedTextDragStart.mouseStartX;
                    const dy = pos.y - editor._attachedTextDragStart.mouseStartY;
                    
                    // Validate stored positions
                    if (!editor._attachedTextDragStart.chainPositions || 
                        editor._attachedTextDragStart.chainPositions.length === 0) {
                        console.warn('Attached text drag: Invalid stored chain positions');
                        editor._attachedTextDragStart = null;
                        return;
                    }
                    
                    // ENHANCED: Move ALL links in the BUL chain (only free endpoints - not attached to devices)
                    for (const chainPos of editor._attachedTextDragStart.chainPositions) {
                        const chainLink = editor.objects.find(o => o.id === chainPos.linkId);
                        if (!chainLink) continue;
                        
                        const startDevice = chainPos.device1 ? editor.objects.find(o => o.id === chainPos.device1) : null;
                        const endDevice = chainPos.device2 ? editor.objects.find(o => o.id === chainPos.device2) : null;
                        
                        if (!startDevice && !isNaN(dx) && !isNaN(dy)) {
                            chainLink.start.x = chainPos.startX + dx;
                            chainLink.start.y = chainPos.startY + dy;
                        }
                        if (!endDevice && !isNaN(dx) && !isNaN(dy)) {
                            chainLink.end.x = chainPos.endX + dx;
                            chainLink.end.y = chainPos.endY + dy;
                        }
                    }
                    
                    // Update text positions for ALL attached texts in the chain
                    const allLinkIds = allLinksInChain.map(l => l.id);
                    const allAttachedTexts = editor.objects.filter(obj => 
                        obj.type === 'text' && obj.linkId && allLinkIds.includes(obj.linkId)
                    );
                    for (const attachedText of allAttachedTexts) {
                        editor.updateAdjacentTextPosition(attachedText);
                    }
                    
                    // TB moves the link body - CP is separate and only controls curve shape
                    // (CP is shown/dragged via hoveredLinkMidpoint, not via TB)
                    
                    editor.scheduleDraw();
                    return;
                }
                
                // For bound links (both endpoints attached to devices), text stays attached to link
                // ENHANCED: If TB is at MIDDLE position, dragging it should control the curve
                // This makes the TB act as the curve control point (sets link to manual mode automatically)
                // FIX: Allow curve control for MIDDLE TBs regardless of current curve mode
                const isMiddlePosition = textObj.position === 'middle';
                const effectiveCurveMode = link ? editor.getEffectiveCurveMode(link) : null;
                
                // FIXED: Middle-position TBs can ALWAYS control the curve (will set to manual mode)
                // Other positions only work if already in manual mode
                if (link && (isMiddlePosition || effectiveCurveMode === 'manual')) {
                    
                    // Initialize curve drag state if needed
                    if (!editor._tbCurveDragStart) {
                        // IMMEDIATELY set link to manual curve mode when starting drag
                        // This ensures the curve will follow the TB from the first frame
                        if (link.curveMode !== 'manual') {
                            link.curveMode = 'manual';
                            link.curveOverride = true;
                            if (editor.debugger) {
                                editor.debugger.logInfo(`📐 TB drag: Set link ${link.id} to manual curve mode`);
                            }
                        }
                        
                        // Get initial curve point
                        // CRITICAL: For middle-position TBs, ALWAYS use TB's position as initial point
                        // The TB IS the curve control - curve follows TB, not the other way around
                        let initialCurvePoint;
                        if (isMiddlePosition) {
                            // Middle TB: use TB's current position (TB drives the curve)
                            initialCurvePoint = { x: textObj.x, y: textObj.y };
                            // Also sync the link's curve point to TB position immediately
                            link.manualCurvePoint = { x: textObj.x, y: textObj.y };
                            link.manualControlPoint = { x: textObj.x, y: textObj.y };
                        } else if (link.manualControlPoint) {
                            initialCurvePoint = { ...link.manualControlPoint };
                        } else if (link.manualCurvePoint) {
                            initialCurvePoint = { ...link.manualCurvePoint };
                        } else {
                            // Calculate from midpoint for non-middle TBs
                            const endpoints = editor.getLinkEndpoints(link);
                            if (endpoints) {
                                const midX = (endpoints.startX + endpoints.endX) / 2;
                                const midY = (endpoints.startY + endpoints.endY) / 2;
                                initialCurvePoint = { x: midX, y: midY };
                            } else {
                                initialCurvePoint = { x: textObj.x, y: textObj.y };
                            }
                        }
                        
                        editor._tbCurveDragStart = {
                            mouseStartX: pos.x,
                            mouseStartY: pos.y,
                            textStartX: textObj.x,
                            textStartY: textObj.y,
                            initialCurvePoint: initialCurvePoint,
                            isMiddlePosition: isMiddlePosition
                        };
                        editor.saveState(); // Make curve edit undoable
                        
                        // Show grabbing cursor for middle-position TB (it's the curve control)
                        if (isMiddlePosition) {
                            editor.canvas.style.cursor = 'grabbing';
                            editor._tbActedAsCP = true;
                            editor.hideTextSelectionToolbar();
                        }
                    }
                    
                    // Calculate delta from drag start
                    const dx = pos.x - editor._tbCurveDragStart.mouseStartX;
                    const dy = pos.y - editor._tbCurveDragStart.mouseStartY;
                    
                    // Update the curve point based on mouse movement
                    const newCurveX = editor._tbCurveDragStart.initialCurvePoint.x + dx;
                    const newCurveY = editor._tbCurveDragStart.initialCurvePoint.y + dy;
                    
                    // Set manual curve point - this curves the link
                    link.manualCurvePoint = { x: newCurveX, y: newCurveY };
                    link.manualControlPoint = { x: newCurveX, y: newCurveY }; // For live preview
                    // Note: Link is already set to manual mode at drag initialization
                    
                    // For middle-position text, TB follows curve point exactly (seamless)
                    // For other positions, text stays at its attachment point on the newly curved link
                    if (editor._tbCurveDragStart.isMiddlePosition) {
                        // Middle text: directly set position to curve point
                        textObj.x = newCurveX;
                        textObj.y = newCurveY;
                    }
                    
                    // Update ALL attached texts on this link (positions follow the curve)
                    const attachedTexts = editor.objects.filter(obj => 
                        obj.type === 'text' && obj.linkId === link.id
                    );
                    for (const attachedText of attachedTexts) {
                        if (attachedText.id !== textObj.id || !editor._tbCurveDragStart.isMiddlePosition) {
                            editor.updateAdjacentTextPosition(attachedText);
                        }
                    }
                    
                    // Update hover state for visual feedback (shows CP handle at new position)
                    editor.hoveredLinkMidpoint = { link, midpoint: { x: newCurveX, y: newCurveY }, isOnCP: true };
                    
                    editor.scheduleDraw();
                    return;
                }
                
                // Non-middle text on bound links: just return without moving
                // Text position updates automatically via updateAdjacentTextPosition
                return;
            }
            
            // ENHANCED: Special handling for unbound links - move entire link body
            if (editor.selectedObject.type === 'unbound' && !editor.stretchingLink) {
                // User is dragging the link body (not stretching an endpoint)
                const dx = pos.x - editor.dragStart.x;
                const dy = pos.y - editor.dragStart.y;
                const link = editor.selectedObject;
                
                // Move both endpoints by the same offset (translate the entire link)
                // BUT: If an endpoint is attached to a device, keep it at the device edge
                if (editor.unboundLinkInitialPos) {
                    // Calculate total drag delta from start
                    const dx = pos.x - editor.dragStart.x;
                    const dy = pos.y - editor.dragStart.y;
                    
                    // ENHANCED: Move ENTIRE BUL chain as one unit with preserved structure
                    // Use absolute positioning (initial + delta) instead of incremental movement
                    if (editor._bulChainInitialPositions && editor._bulChainInitialPositions.size > 0) {
                        const allChainLinks = editor.getAllMergedLinks(editor.selectedObject);
                        
                        // CRITICAL: Capture initial TB positions on first move
                        if (!editor._attachedTBInitialPositions) {
                            editor._attachedTBInitialPositions = new Map();
                            // Find all TBs attached to any link in the chain
                            for (const chainLink of allChainLinks) {
                                const attachedTBs = editor.objects.filter(obj => 
                                    obj.type === 'text' && obj.linkId === chainLink.id
                                );
                                for (const tb of attachedTBs) {
                                    editor._attachedTBInitialPositions.set(tb.id, {
                                        x: tb.x,
                                        y: tb.y
                                    });
                                }
                            }
                        }
                        
                        for (const chainLink of allChainLinks) {
                            const initialPos = editor._bulChainInitialPositions.get(chainLink.id);
                            if (!initialPos) continue; // Safety check
                            
                            // Check if endpoints are attached to devices
                            const startDevice = chainLink.device1 ? editor.objects.find(o => o.id === chainLink.device1) : null;
                            const endDevice = chainLink.device2 ? editor.objects.find(o => o.id === chainLink.device2) : null;
                            
                            // Move free endpoints using absolute positioning
                            if (!startDevice) {
                                chainLink.start.x = initialPos.startX + dx;
                                chainLink.start.y = initialPos.startY + dy;
                            }
                            if (!endDevice) {
                                chainLink.end.x = initialPos.endX + dx;
                                chainLink.end.y = initialPos.endY + dy;
                            }
                            
                            // Move curve points — proportional to how much the midpoint actually moved
                            const bothEndsFree = !startDevice && !endDevice;
                            const cpDx = bothEndsFree ? dx : dx / 2;
                            const cpDy = bothEndsFree ? dy : dy / 2;
                            
                            if (chainLink.manualCurvePoint && initialPos.curvePointX !== undefined) {
                                chainLink.manualCurvePoint.x = initialPos.curvePointX + cpDx;
                                chainLink.manualCurvePoint.y = initialPos.curvePointY + cpDy;
                            }
                            if (chainLink.manualControlPoint && initialPos.controlPointX !== undefined) {
                                chainLink.manualControlPoint.x = initialPos.controlPointX + cpDx;
                                chainLink.manualControlPoint.y = initialPos.controlPointY + cpDy;
                            }
                            
                            // Move MP connection points to preserve chain structure
                            if (chainLink.mergedWith?.connectionPoint && initialPos.mpConnectionX !== undefined) {
                                chainLink.mergedWith.connectionPoint.x = initialPos.mpConnectionX + dx;
                                chainLink.mergedWith.connectionPoint.y = initialPos.mpConnectionY + dy;
                            }
                            if (chainLink.mergedInto?.connectionPoint && initialPos.parentMpConnectionX !== undefined) {
                                chainLink.mergedInto.connectionPoint.x = initialPos.parentMpConnectionX + dx;
                                chainLink.mergedInto.connectionPoint.y = initialPos.parentMpConnectionY + dy;
                            }
                            
                            // Recalculate device-attached endpoints to stay at device edge (shape-aware)
                            if (startDevice) {
                                const targetX = endDevice ? endDevice.x : chainLink.end.x;
                                const targetY = endDevice ? endDevice.y : chainLink.end.y;
                                const angle = Math.atan2(targetY - startDevice.y, targetX - startDevice.x);
                                const startPt = editor.getLinkConnectionPoint(startDevice, angle);
                                chainLink.start.x = startPt.x;
                                chainLink.start.y = startPt.y;
                            }
                            if (endDevice) {
                                const targetX = startDevice ? startDevice.x : chainLink.start.x;
                                const targetY = startDevice ? startDevice.y : chainLink.start.y;
                                const angle = Math.atan2(targetY - endDevice.y, targetX - endDevice.x);
                                const endPt = editor.getLinkConnectionPoint(endDevice, angle);
                                chainLink.end.x = endPt.x;
                                chainLink.end.y = endPt.y;
                            }
                        }
                        
                        // Move attached TBs by the same delta to preserve exact positions
                        if (editor._attachedTBInitialPositions) {
                            for (const [tbId, initialTBPos] of editor._attachedTBInitialPositions.entries()) {
                                const tb = editor.objects.find(o => o.id === tbId);
                                if (tb) {
                                    tb.x = initialTBPos.x + dx;
                                    tb.y = initialTBPos.y + dy;
                                }
                            }
                        }
                        
                        // Draw and return - no need for old propagation logic
                        editor.scheduleDraw();
                        return;
                    }
                    
                    // ENHANCED: Move all TBs attached to links in the chain
                    // TBs should move with the link as a rigid unit
                    const allChainLinks = editor.getAllMergedLinks(editor.selectedObject);
                    const chainLinkIds = new Set(allChainLinks.map(l => l.id));
                    const attachedTBs = editor.objects.filter(obj => 
                        obj.type === 'text' && obj.linkId && chainLinkIds.has(obj.linkId)
                    );
                    
                    for (const tb of attachedTBs) {
                        // Store initial TB position if not already stored
                        if (!editor._tbInitialPositions) {
                            editor._tbInitialPositions = new Map();
                        }
                        if (!editor._tbInitialPositions.has(tb.id)) {
                            editor._tbInitialPositions.set(tb.id, { x: tb.x, y: tb.y });
                        }
                        
                        // Move TB by the same delta
                        const initialTBPos = editor._tbInitialPositions.get(tb.id);
                        tb.x = initialTBPos.x + dx;
                        tb.y = initialTBPos.y + dy;
                    }
                    
                    // FALLBACK: Old single-link logic (if chain positions weren't captured)
                    const link = editor.selectedObject;
                    // Check if start is attached to a device
                    const startDevice = link.device1 ? editor.objects.find(o => o.id === link.device1) : null;
                    // Check if end is attached to a device
                    const endDevice = link.device2 ? editor.objects.find(o => o.id === link.device2) : null;
                    
                    // If both endpoints are attached to devices, nothing to move
                    if (startDevice && endDevice) {
                        // Both ends anchored - just update draw (edge positions handled by drawUnboundLink)
                        editor.scheduleDraw();
                        return;
                    }
                    
                    // Move free endpoints
                    if (!startDevice) {
                        link.start.x = editor.unboundLinkInitialPos.startX + dx;
                        link.start.y = editor.unboundLinkInitialPos.startY + dy;
                    }
                    if (!endDevice) {
                        link.end.x = editor.unboundLinkInitialPos.endX + dx;
                        link.end.y = editor.unboundLinkInitialPos.endY + dy;
                    }
                    
                    // CRITICAL: Move CP to preserve its relative position to TPs
                    // If both endpoints move: CP moves by full dx, dy (preserves shape perfectly)
                    // If only one endpoint moves: CP moves proportionally to maintain relative position
                    const bothEndpointsFree = !startDevice && !endDevice;
                    
                    if (bothEndpointsFree) {
                        // Both endpoints free - move CP by full amount to preserve exact shape
                    if (link.manualCurvePoint && editor.unboundLinkInitialPos.curvePointX !== undefined) {
                        link.manualCurvePoint.x = editor.unboundLinkInitialPos.curvePointX + dx;
                        link.manualCurvePoint.y = editor.unboundLinkInitialPos.curvePointY + dy;
                    }
                    if (link.manualControlPoint && editor.unboundLinkInitialPos.controlPointX !== undefined) {
                        link.manualControlPoint.x = editor.unboundLinkInitialPos.controlPointX + dx;
                        link.manualControlPoint.y = editor.unboundLinkInitialPos.controlPointY + dy;
                        }
                    } else {
                        // One endpoint attached - CP should stay at same relative position along the curve
                        // Calculate the original relative position of CP between original TPs
                        if (link.manualCurvePoint && editor.unboundLinkInitialPos.curvePointX !== undefined) {
                            const origStartX = editor.unboundLinkInitialPos.startX;
                            const origStartY = editor.unboundLinkInitialPos.startY;
                            const origEndX = editor.unboundLinkInitialPos.endX;
                            const origEndY = editor.unboundLinkInitialPos.endY;
                            const origCpX = editor.unboundLinkInitialPos.curvePointX;
                            const origCpY = editor.unboundLinkInitialPos.curvePointY;
                            
                            // Calculate relative position (0-1) of CP along original link
                            const origMidX = (origStartX + origEndX) / 2;
                            const origMidY = (origStartY + origEndY) / 2;
                            const origOffsetX = origCpX - origMidX;
                            const origOffsetY = origCpY - origMidY;
                            
                            // Apply same offset from new midpoint
                            const newMidX = (link.start.x + link.end.x) / 2;
                            const newMidY = (link.start.y + link.end.y) / 2;
                            link.manualCurvePoint.x = newMidX + origOffsetX;
                            link.manualCurvePoint.y = newMidY + origOffsetY;
                        }
                        if (link.manualControlPoint && editor.unboundLinkInitialPos.controlPointX !== undefined) {
                            const origStartX = editor.unboundLinkInitialPos.startX;
                            const origStartY = editor.unboundLinkInitialPos.startY;
                            const origEndX = editor.unboundLinkInitialPos.endX;
                            const origEndY = editor.unboundLinkInitialPos.endY;
                            const origCpX = editor.unboundLinkInitialPos.controlPointX;
                            const origCpY = editor.unboundLinkInitialPos.controlPointY;
                            
                            const origMidX = (origStartX + origEndX) / 2;
                            const origMidY = (origStartY + origEndY) / 2;
                            const origOffsetX = origCpX - origMidX;
                            const origOffsetY = origCpY - origMidY;
                            
                            const newMidX = (link.start.x + link.end.x) / 2;
                            const newMidY = (link.start.y + link.end.y) / 2;
                            link.manualControlPoint.x = newMidX + origOffsetX;
                            link.manualControlPoint.y = newMidY + origOffsetY;
                        }
                    }
                    
                    // Recalculate device-attached endpoints to stay at device edge (shape-aware)
                    if (startDevice) {
                        // Calculate angle from device to the other endpoint
                        const targetX = endDevice ? endDevice.x : link.end.x;
                        const targetY = endDevice ? endDevice.y : link.end.y;
                        const angle = Math.atan2(targetY - startDevice.y, targetX - startDevice.x);
                        const startPt = editor.getLinkConnectionPoint(startDevice, angle);
                        link.start.x = startPt.x;
                        link.start.y = startPt.y;
                    }
                    if (endDevice) {
                        // Calculate angle from device to the other endpoint
                        const targetX = startDevice ? startDevice.x : link.start.x;
                        const targetY = startDevice ? startDevice.y : link.start.y;
                        const angle = Math.atan2(targetY - endDevice.y, targetX - endDevice.x);
                        const endPt = editor.getLinkConnectionPoint(endDevice, angle);
                        link.end.x = endPt.x;
                        link.end.y = endPt.y;
                    }
                    
                    // DON'T update attached text positions - they're already moved by TB initial positions
                    // This preserves the exact angle/structure of the link+TB unit
                    
                    editor.scheduleDraw();
                    editor.updateHud(pos);
                    return;
                } else {
                    // CRITICAL FIX: If unboundLinkInitialPos is missing, initialize it now!
                    if (editor.debugger) {
                        editor.debugger.logWarning(`Unbound link missing initial position - reinitializing`);
                    }
                    editor.unboundLinkInitialPos = {
                        startX: editor.selectedObject.start.x - dx,
                        startY: editor.selectedObject.start.y - dy,
                        endX: editor.selectedObject.end.x - dx,
                        endY: editor.selectedObject.end.x - dy,
                        // Store manual curve point for body drag preservation
                        curvePointX: editor.selectedObject.manualCurvePoint ? editor.selectedObject.manualCurvePoint.x - dx : undefined,
                        curvePointY: editor.selectedObject.manualCurvePoint ? editor.selectedObject.manualCurvePoint.y - dy : undefined,
                        // Store manual control point (active curve handle) for body drag preservation
                        controlPointX: editor.selectedObject.manualControlPoint ? editor.selectedObject.manualControlPoint.x - dx : undefined,
                        controlPointY: editor.selectedObject.manualControlPoint ? editor.selectedObject.manualControlPoint.y - dy : undefined
                    };
                    
                    // DON'T update attached text positions - they're already moved by TB initial positions
                    // in the fallback code above (lines 8796-8817)
                    
                    editor.scheduleDraw();
                    editor.updateHud(pos);
                    return;
                }
            }
            
            // ULTRA-FIXED: Calculate new position maintaining grab offset
            // CRITICAL: Validate dragStart is an offset, not mouse position
            // If dragStart looks like a mouse position (large values), recalculate offset
            
            const dragStartMag = Math.sqrt(editor.dragStart.x * editor.dragStart.x + editor.dragStart.y * editor.dragStart.y);
            
            // =========================================================================
            // LARGE DEVICE FIX (Dec 2025): Scale max valid offset with device radius
            // =========================================================================
            // For devices, the valid offset can be up to device radius + buffer (edge click)
            // For large devices (radius 150+), clicking near edge gives offset > 100px legitimately
            // =========================================================================
            let maxValidOffset = 100; // default for non-device objects
            if (editor.selectedObject.type === 'device' && editor.selectedObject.radius) {
                // Allow offset up to device radius + small buffer for edge clicks
                maxValidOffset = editor.selectedObject.radius + 50;
            }
            const isDragStartMousePos = editor.selectedObject.type !== 'text' && dragStartMag > maxValidOffset;
            
            let actualOffsetX = editor.dragStart.x;
            let actualOffsetY = editor.dragStart.y;
            
            // CRITICAL FIX: If dragStart looks like mouse position, recalculate offset
            if (isDragStartMousePos && editor.selectedObject.x !== undefined && editor.selectedObject.y !== undefined) {
                // dragStart is incorrectly set to mouse position - recalculate offset
                actualOffsetX = pos.x - editor.selectedObject.x;
                actualOffsetY = pos.y - editor.selectedObject.y;
                
                // Update dragStart with correct offset
                editor.dragStart = { x: actualOffsetX, y: actualOffsetY };
            }
            
            // Calculate new position
            let newX, newY;
            
            // For text objects, use stored initial positions for extra stability
            if (editor.selectedObject.type === 'text' && editor.textDragInitialPos) {
                // Calculate based on stored initial offset
                const mouseDx = pos.x - editor.textDragInitialPos.mouseX;
                const mouseDy = pos.y - editor.textDragInitialPos.mouseY;
                
                newX = editor.textDragInitialPos.textX + mouseDx;
                newY = editor.textDragInitialPos.textY + mouseDy;
            } else if (editor.selectedObject.type === 'device' && editor.deviceDragInitialPos) {
                // CRITICAL FIX: Use stored initial position for devices too
                // This prevents collision-modified positions from causing drift/jumping
                const mouseDx = pos.x - editor.deviceDragInitialPos.mouseX;
                const mouseDy = pos.y - editor.deviceDragInitialPos.mouseY;
                
                newX = editor.deviceDragInitialPos.deviceX + mouseDx;
                newY = editor.deviceDragInitialPos.deviceY + mouseDy;
            } else if (editor.selectedObject.type === 'device' && !editor.deviceDragInitialPos) {
                newX = pos.x - actualOffsetX;
                newY = pos.y - actualOffsetY;
            } else if (editor.selectedObject.type === 'shape' && editor.shapeDragInitialPos) {
                // SHAPES: Use stored initial position for smooth dragging from any click point
                const mouseDx = pos.x - editor.shapeDragInitialPos.mouseX;
                const mouseDy = pos.y - editor.shapeDragInitialPos.mouseY;
                
                newX = editor.shapeDragInitialPos.shapeX + mouseDx;
                newY = editor.shapeDragInitialPos.shapeY + mouseDy;
            } else {
                // Fallback: Standard position calculation
                newX = pos.x - actualOffsetX;
                newY = pos.y - actualOffsetY;
            }
            
            // ENHANCED: Detailed jump detection and diagnostics
            // Only flag truly anomalous jumps (>500px) - fast mouse movement can easily do 100-300px
            // CRITICAL FIX: Only check for jumps on objects with x/y properties (devices, text)
            if (editor.debugger && editor.selectedObject.x !== undefined && editor.selectedObject.y !== undefined) {
                const jumpX = Math.abs(newX - editor.selectedObject.x);
                const jumpY = Math.abs(newY - editor.selectedObject.y);
                // High threshold - only actual bugs cause 500px+ jumps, not fast dragging
                if (jumpX > 500 || jumpY > 500) {
                    // CRITICAL FIX: Only log jump ONCE per drag session, not every frame!
                    if (!editor._jumpDetectedThisDrag) {
                        editor._jumpDetectedThisDrag = true; // Set flag to prevent spam
                        
                        // Log comprehensive jump diagnostic (single logWarning call with all info)
                        const jumpDiagnostics = `[WARN] Large move detected: Delta (${Math.round(jumpX)}, ${Math.round(jumpY)})
Obj: (${editor.selectedObject.x.toFixed(0)}, ${editor.selectedObject.y.toFixed(0)}) → (${newX.toFixed(0)}, ${newY.toFixed(0)})`;
                        
                        editor.debugger.logWarning(jumpDiagnostics);
                        editor.latestJumpDetails = jumpDiagnostics;
                    }
                }
            }
            
            // Track velocity for momentum (only for objects with x/y properties)
            if (editor.momentum && editor.lastDragPos && editor.lastDragTime && 
                editor.selectedObject.x !== undefined && editor.selectedObject.y !== undefined) {
                const now = Date.now();
                const dt = now - editor.lastDragTime;
                if (dt > 0) {
                    const dx = newX - editor.selectedObject.x;
                    const dy = newY - editor.selectedObject.y;
                    editor.momentum.trackVelocity(dx, dy, dt);
                }
                editor.lastDragPos = { x: editor.selectedObject.x, y: editor.selectedObject.y };
                editor.lastDragTime = now;
            }
            
            // Apply collision detection if enabled (devices only)
            let finalX = newX;
            let finalY = newY;
            if (editor.deviceCollision && editor.selectedObject.type === 'device') {
                const proposedPos = editor.checkDeviceCollision(editor.selectedObject, newX, newY);
                finalX = proposedPos.x;
                finalY = proposedPos.y;
                
                const collisionDx = finalX - newX;
                const collisionDy = finalY - newY;
                if ((Math.abs(collisionDx) > 0.5 || Math.abs(collisionDy) > 0.5) && editor.deviceDragInitialPos) {
                    editor.deviceDragInitialPos.deviceX += collisionDx;
                    editor.deviceDragInitialPos.deviceY += collisionDy;
                }
            }
            
            // Alignment guides: show lines when device aligns with others
            if (editor.selectedObject.type === 'device') {
                const alignThreshold = 5;
                let alignX = null, alignY = null;
                for (const obj of editor.objects) {
                    if (obj.type !== 'device' || obj === editor.selectedObject) continue;
                    if (Math.abs(finalX - obj.x) < alignThreshold) { alignX = obj.x; finalX = obj.x; }
                    if (Math.abs(finalY - obj.y) < alignThreshold) { alignY = obj.y; finalY = obj.y; }
                    if (alignX !== null && alignY !== null) break;
                }
                editor._alignGuides = (alignX !== null || alignY !== null) ? { x: alignX, y: alignY } : null;
            }
            
            // CRITICAL FIX: Only set x/y if object has those properties
            if (editor.selectedObject.x !== undefined && editor.selectedObject.y !== undefined) {
                // Store old position for momentum transfer
                const oldX = editor.selectedObject.x;
                const oldY = editor.selectedObject.y;
                
                editor.selectedObject.x = finalX;
                editor.selectedObject.y = finalY;
                
                // TEXT-TO-LINK SNAP DETECTION during drag
                if (editor.selectedObject.type === 'text') {
                    // MANUAL CURVE: If text is attached to a link, set link to manual curve mode
                    // The text position becomes the curve control point
                    if (editor.selectedObject.linkId) {
                        const attachedLink = editor.objects.find(o => o.id === editor.selectedObject.linkId);
                        if (attachedLink && editor.linkCurveMode && editor.globalCurveMode === 'manual') {
                            // Set link to manual curve mode - text position controls the curve
                            if (attachedLink.curveMode !== 'manual') {
                                attachedLink.curveMode = 'manual';
                            }
                        }
                    }
                    
                    // Check if text is near a link for potential snap
                    // BUT only if the text is NOT already attached to a link
                    if (!editor.selectedObject.linkId) {
                        const snapTarget = editor.findNearestLinkToPoint(finalX, finalY, 50);
                        if (snapTarget && snapTarget.distance < 40) {
                            // Store snap preview info for drawing
                            editor._textSnapPreview = {
                                link: snapTarget.link,
                                point: snapTarget.point,
                                position: snapTarget.position,
                                t: snapTarget.t
                            };
                        } else {
                            editor._textSnapPreview = null;
                        }
                    } else {
                        // Text is already attached - no snap preview
                        editor._textSnapPreview = null;
                    }
                }
                
                // Apply movable device chain reaction (push nearby devices)
                if (editor.movableDevices && editor.selectedObject.type === 'device') {
                    // Calculate velocity from last drag position for more accurate momentum transfer
                    let velocityX = finalX - oldX;
                    let velocityY = finalY - oldY;
                    
                    // Amplify velocity during drag to make chain reactions more noticeable
                    const dragAmplification = 2.0; // Make dragging push stronger
                    velocityX *= dragAmplification;
                    velocityY *= dragAmplification;
                    
                    editor.applyDeviceChainReaction(editor.selectedObject, velocityX, velocityY);
                }
                
                // ENHANCED: Update Quick Link CPs when single device is dragged
                // This keeps the manual curve shape synchronized with device movement
                if (editor.selectedObject.type === 'device') {
                    const dx = finalX - oldX;
                    const dy = finalY - oldY;
                    editor.updateQuickLinkControlPointsAfterDeviceMove(dx, dy, [editor.selectedObject.id]);
                    
                    // CRITICAL FIX: Also shift attached Unbound Link CPs to preserve curve shape
                    // The CP maintains its relative offset from the link's midpoint
                    const attachedULs = editor.objects.filter(obj => 
                        obj.type === 'unbound' && 
                        (obj.device1 === editor.selectedObject.id || obj.device2 === editor.selectedObject.id) &&
                        obj.manualCurvePoint
                    );
                    for (const ul of attachedULs) {
                        // Check if BOTH endpoints are attached to this device
                        const bothEnds = ul.device1 === editor.selectedObject.id && ul.device2 === editor.selectedObject.id;
                        // Shift amount: full delta if both ends, half if only one end moves
                        const shiftX = bothEnds ? dx : dx / 2;
                        const shiftY = bothEnds ? dy : dy / 2;
                        
                        // Shift curve point by same amount as midpoint moves
                        ul.manualCurvePoint.x += shiftX;
                        ul.manualCurvePoint.y += shiftY;
                    }
                }
            }
            editor.scheduleDraw();
            editor.updateHud(pos);
            
            // CRITICAL: Update PLACEMENT TRACKING in real-time during drag!
            if (editor.debugger && editor.selectedObject.x !== undefined && editor.selectedObject.y !== undefined) {
                const clickTrackDiv = document.getElementById('debug-click-track');
                if (clickTrackDiv) {
                    const devicePos = { x: editor.selectedObject.x, y: editor.selectedObject.y };
                    const deviceGrid = editor.worldToGrid(devicePos);
                    const mouseGrid = editor.worldToGrid(pos);
                    
                    // Calculate relative position (mouse - device)
                    const relativePos = { x: pos.x - devicePos.x, y: pos.y - devicePos.y };
                    const relativeMag = Math.sqrt(relativePos.x * relativePos.x + relativePos.y * relativePos.y);
                    
                    // Calculate offset mismatch
                    const offsetDiffX = relativePos.x - editor.dragStart.x;
                    const offsetDiffY = relativePos.y - editor.dragStart.y;
                    const offsetMismatch = Math.sqrt(offsetDiffX * offsetDiffX + offsetDiffY * offsetDiffY);
                    
                    const inputSource = editor._lastInputType || 'mouse';
                    const icon = inputSource === 'trackpad' ? '🖐️' : inputSource === 'mouse' ? '🖱️' : '👆';
                    
                    clickTrackDiv.innerHTML = `
                        <span style="color: #FF7A33; font-weight: bold; font-size: 11px;">${icon} DRAGGING: ${editor.selectedObject.label || 'Device'}</span><br>
                        <br>
                        <span style="color: #0ff; font-weight: bold;">📍 DEVICE POSITION:</span><br>
                        World: <span style="color: #0ff;">(${devicePos.x.toFixed(1)}, ${devicePos.y.toFixed(1)})</span><br>
                        Grid: <span style="color: #0ff;">(${Math.round(deviceGrid.x)}, ${Math.round(deviceGrid.y)})</span><br>
                        <br>
                        <span style="color: #fa0; font-weight: bold;">🖱️ MOUSE POSITION:</span><br>
                        World: <span style="color: #fa0;">(${pos.x.toFixed(1)}, ${pos.y.toFixed(1)})</span><br>
                        Grid: <span style="color: #fa0;">(${Math.round(mouseGrid.x)}, ${Math.round(mouseGrid.y)})</span><br>
                        <br>
                        <span style="color: #667eea; font-weight: bold;">📏 RELATIVE (Mouse - Device):</span><br>
                        Delta: <span style="color: #667eea; font-weight: bold;">(${relativePos.x.toFixed(1)}, ${relativePos.y.toFixed(1)})</span><br>
                        Distance: <span style="color: #667eea;">${relativeMag.toFixed(1)}px</span><br>
                        <br>
                        <span style="color: #0f0; font-weight: bold;">EXPECTED OFFSET:</span><br>
                        Stored: <span style="color: #0f0;">(${editor.dragStart.x.toFixed(1)}, ${editor.dragStart.y.toFixed(1)})</span><br>
                        <br>
                        <div style="padding: 4px; background: ${offsetMismatch > 1 ? 'rgba(231, 76, 60, 0.2)' : 'rgba(39, 174, 96, 0.2)'}; border-radius: 3px; border-left: 3px solid ${offsetMismatch > 1 ? '#e74c3c' : '#27ae60'}; margin-bottom: 6px;">
                            <span style="color: ${offsetMismatch > 1 ? '#f00' : '#0f0'}; font-weight: bold;">
                                ${offsetMismatch > 1 ? '[!] OFFSET DRIFT DETECTED!' : '[OK] Offset Stable'}
                            </span><br>
                            ${offsetMismatch > 1 ? `
                            <span style="color: #fff; font-size: 9px;">Expected relative: (${editor.dragStart.x.toFixed(1)}, ${editor.dragStart.y.toFixed(1)})</span><br>
                            <span style="color: #fff; font-size: 9px;">Actual relative: (${relativePos.x.toFixed(1)}, ${relativePos.y.toFixed(1)})</span><br>
                            <span style="color: #f00; font-size: 9px;">Drift: (${offsetDiffX.toFixed(1)}, ${offsetDiffY.toFixed(1)}) = ${offsetMismatch.toFixed(1)}px</span><br>
                            ` : `<span style="color: #0f0; font-size: 9px;">Offset maintaining correctly</span><br>`}
                        </div>
                        <span style="color: #888; font-size: 9px;">
                            State: ACTIVE DRAG<br>
                            Updates: Real-time (every frame)
                        </span>
                    `;
                }
            }
        } else if (editor.currentTool === 'link' && editor.linking && editor.linkStart) {
            // LINK PREVIEW MODE: Just call draw() - the preview is now drawn inside draw()
            editor.lastMousePos = pos; // Store position for draw() to use
            editor.draw();
        } else if (editor.currentTool === 'link' && editor.linking && editor._linkFromTP) {
            // Draw preview for link from TP mode
            // SAFETY CHECK: Verify source link still exists (might have been deleted)
            const sourceLinkExists = editor.objects.some(obj => obj.id === editor._linkFromTP.link.id);
            if (!sourceLinkExists) {
                // Source link was deleted - abort TP link mode
                editor._linkFromTP = null;
                editor.linking = false;
                editor.setMode('base');
                if (editor.debugger) {
                    editor.debugger.logInfo('🔗 Link from TP: Aborted - source UL no longer exists');
                }
                editor.draw();
                return;
            }
            // Store mouse position for draw() to use for TP preview
            editor.lastMousePos = pos;
            editor.draw();
        }
        
        // ENHANCED: Always update HUD with current position to show link attachment info
        editor.updateHud(pos);
    },
};

console.log('[topology-mouse-move.js] MouseMoveHandler loaded');
