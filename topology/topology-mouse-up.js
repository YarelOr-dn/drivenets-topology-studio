/**
 * topology-mouse-up.js - handleMouseUp handler
 * 
 * Extracted from topology-mouse.js for modular architecture.
 */

'use strict';

window.MouseUpHandler = {
    handleMouseUp(editor, e) {
        // Device placement is now handled immediately in handleMouseDown
        
        // Clear debug flag for next drag session
        editor._dragLoggedOnce = false;
        
        // Get mouse position first - needed by multiple code paths
        const pos = editor.getMousePos(e);
        
        // Clear potential CP drag on mouseup (if user didn't move enough to start drag)
        if (editor._potentialCPDrag) {
            editor._potentialCPDrag = null;
            // Link selection already happened in mousedown, nothing else to do
        }
        
        // MANUAL CURVE: Finalize curve handle drag
        if (editor.draggingCurveHandle) {
            const link = editor.draggingCurveHandle.link;
            
            // Store ABSOLUTE position (stays fixed when devices move)
            link.manualCurvePoint = { x: pos.x, y: pos.y };
            
            // Clear temporary drag position and legacy offset
            delete link.manualControlPoint;
            delete link.manualCurveOffset;
            
            // Set curve mode to manual for this link
            link.curveMode = 'manual';
            
            // CRITICAL: Update any middle-position TB attached to this link to final position
            const attachedMiddleTexts = editor.objects.filter(obj => 
                obj.type === 'text' && obj.linkId === link.id && obj.position === 'middle'
            );
            for (const textObj of attachedMiddleTexts) {
                textObj.x = pos.x;
                textObj.y = pos.y;
            }
            
            if (editor.debugger) {
                editor.debugger.logSuccess(`✅ Curve Handle Released: ${link.id} at fixed position (${Math.round(pos.x)}, ${Math.round(pos.y)})`);
            }
            
            editor.draggingCurveHandle = null;
            editor.hoveredLinkMidpoint = null;
            editor.updateCursor();
            editor.scheduleAutoSave();
            editor.draw();
            return;
        }
        
        // CRITICAL: Update tap duration when mouse is released
        // This allows us to detect if the first tap was a long press (which should not trigger double-tap)
        if (editor._lastTapStartTime > 0) {
            const tapDuration = Date.now() - editor._lastTapStartTime;
            // If tap was too long (long press), clear tap tracking to prevent double-tap
            if (tapDuration >= editor.maxTapDuration) {
                editor.lastTapTime = 0;
                editor._lastTapDevice = null;
                editor._lastTapPos = null;
                editor._lastTapStartTime = 0;
            }
        }
        
        // Clear all timers
        if (editor.longPressTimer) {
            clearTimeout(editor.longPressTimer);
            editor.longPressTimer = null;
        }
        if (editor.marqueeTimer) {
            clearTimeout(editor.marqueeTimer);
            editor.marqueeTimer = null;
        }
        
        if (editor.panning) {
            editor.panning = false;
            editor.updateCursor();
            if (window.XrayPopup && window.XrayPopup.temporaryShow) {
                window.XrayPopup.temporaryShow();
            }
            // Object stays selected but toolbar does NOT auto-restore after panning.
            // User must click the object again to bring toolbar back.
            return;
        }
        
        // TEXT PLACEMENT: Handle deferred text placement (like devices)
        if (editor.currentTool === 'text' && editor.textPlacementPending && !editor.marqueeActive) {
            const clickDuration = Date.now() - editor.textPlacementPending.clickTime;
            const clickedPos = editor.textPlacementPending.startPos;
            editor.textPlacementPending = null;
            
            // Check if clicking on existing object - EXIT text/continuous mode
            const clickedObject = editor.findObjectAt(clickedPos.x, clickedPos.y);
            if (clickedObject && (clickedObject.type === 'text' || clickedObject.type === 'device')) {
                // Clicked on existing TB or device - exit text placement mode
                editor.exitContinuousTextPlacement(); // Also handles button state
                editor.setMode('base');
                editor.selectedObject = clickedObject;
                editor.selectedObjects = [clickedObject];
                if (editor.debugger) {
                    editor.debugger.logInfo(`Text placement exited - clicked on ${clickedObject.type}: ${clickedObject.label || clickedObject.text || clickedObject.id}`);
                }
                editor.draw();
                return;
            }
            
            // Only place if it was a quick tap (< 200ms) - prevents accidental placement
            if (clickDuration < 200) {
                editor.saveState();
                const text = editor.createText(clickedPos.x, clickedPos.y);
                editor.objects.push(text);
                editor.updateTextProperties();
                
                // Check if text was placed near a link - auto-attach if so
                const nearLink = editor.findNearestLinkToPoint(clickedPos.x, clickedPos.y, 40);
                if (nearLink && nearLink.distance < 30) {
                    editor._attachingFromDrop = true;
                    editor.attachTextToLink(text, nearLink.link, nearLink.t);
                    editor._attachingFromDrop = false;
                    if (editor.debugger) {
                        editor.debugger.logSuccess(`Text placed and attached to ${nearLink.link.id} at ${nearLink.position}`);
                    }
                } else {
                    if (editor.debugger) {
                        editor.debugger.logSuccess(`Text placed at (${Math.round(clickedPos.x)}, ${Math.round(clickedPos.y)})`);
                    }
                }
                
                // CONTINUOUS PLACEMENT MODE: Stay in text mode only if Place TBs is active
                if (editor.continuousTextPlacement) {
                    // Keep placing TBs - deselect placed text and stay in text mode
                editor.selectedObject = null;
                editor.selectedObjects = [];
                if (editor.debugger) {
                        editor.debugger.logInfo(`   Continuous TB mode: ready for next placement`);
                    }
                } else {
                    // Normal single placement - exit to base mode and select the text
                    editor.selectedObject = text;
                    editor.selectedObjects = [text];
                    editor.setMode('base');
                }
                
                editor.draw();
            } else {
                if (editor.debugger) {
                    editor.debugger.logWarning(`Long press detected (${clickDuration}ms) - text placement cancelled`);
                }
            }
            return;
        }
        
        // If we deferred placement and did not start marquee selection, perform placement now
        if (editor.placingDevice && editor.placementPending && !editor.marqueeActive) {
            const typeToPlace = editor.placementPending.type;
            const clickDuration = Date.now() - editor.placementPending.clickTime;
            const clickedPos = editor.placementPending.startPos; // Where mouse actually clicked
            editor.placementPending = null;
            
            // CRITICAL: Check if clicking on an existing device - prevent placement on top of devices!
            // This check works regardless of collision detection setting
            const clickedOnDevice = editor.objects.find(obj => {
                if (obj.type === 'device') {
                    const dx = clickedPos.x - obj.x;
                    const dy = clickedPos.y - obj.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    // Use device radius + small tolerance for hitbox
                    return dist <= obj.radius + 5;
                }
                return false;
            });
            
            if (clickedOnDevice) {
                // Clicked on an existing device - cancel placement
                if (editor.debugger) {
                    editor.debugger.logWarning(`📍 Device placement cancelled - clicked on existing device: ${clickedOnDevice.label || clickedOnDevice.id}`);
                    editor.debugger.logInfo(`   Use empty space to place new devices`);
                }
                return;
            }
            
            // Only place if it was a quick tap (< 200ms) - prevents accidental placement
            if (clickDuration < 200) {
                // CRITICAL FIX: Always use the CLICKED position, not the mouseup position
                // This ensures devices are placed exactly where clicked, even during rapid placement
                editor.lastClickPos = clickedPos;
                // Pass clicked position directly to ensure accurate placement
                editor.addDeviceAtPosition(typeToPlace, clickedPos.x, clickedPos.y);
                // Deselect the newly placed device
                editor.selectedObject = null;
                editor.selectedObjects = [];
                // BUGFIX: Hide text selection toolbar when placing new device
                editor.hideTextSelectionToolbar();
                editor.updatePropertiesPanel();
                editor.draw();
                
                if (editor.debugger) {
                    editor.debugger.logInfo(`📍 Quick tap: Device placed (${clickDuration}ms) at clicked position`);
                }
            } else {
                if (editor.debugger) {
                    editor.debugger.logWarning(`📍 Long press detected (${clickDuration}ms) - placement cancelled`);
                }
            }
            
            return;
        }

        // Handle marquee selection release
        if (editor.marqueeActive) {
            // Save start position before clearing
            const startPos = editor.selectionRectStart;

            // Clear marquee visuals immediately
            editor.marqueeActive = false;
            editor.selectionRectangle = null; // Rectangle disappears immediately
            editor.selectionRectStart = null;
            
            // Check if this was a very small drag (essentially a click) - cancel selection
            if (startPos && pos) {
                const dx = Math.abs(pos.x - startPos.x);
                const dy = Math.abs(pos.y - startPos.y);
                if (dx < 5 && dy < 5) {
                    // Very small movement - treat as click, cancel marquee
                    editor.selectedObjects = [];
                    editor.selectedObject = null;
                    // BUGFIX: Hide text selection toolbar when canceling marquee
                    editor.hideTextSelectionToolbar();
                    
                    // CS-MS MODE: If cancelled, stay in paste mode but exit csmsMode
                    if (editor.csmsMode) {
                        editor.csmsMode = false;
                        // Restore paste style cursor
                        editor.canvas.style.cursor = 'copy';
                        if (editor.debugger) {
                            editor.debugger.logInfo(`CS-MS cancelled (small movement) - still in paste mode`);
                        }
                        editor.draw();
                        return;
                    }
                    
                    // SEAMLESS: Resume device placement if came from there
                    if (editor.resumePlacementAfterMarquee) {
                        editor.setDevicePlacementMode(editor.resumePlacementAfterMarquee);
                        editor.resumePlacementAfterMarquee = null;
                        
                        if (editor.debugger) {
                            editor.debugger.logInfo(`Seamless transition: MS cancelled -> Device placement resumed`);
                        }
                    } else {
                        editor.setMode('base');
                    }
                    
                    editor.draw();
                    return;
                }
            }

            // After MS release, keep items selected; enable multi-select drag semantics
            if (editor.selectedObjects.length > 0) {
                // CS-MS MODE: If in paste style mode (or csmsMode), paste style to ALL selected objects
                if ((editor.pasteStyleMode || editor.csmsMode) && editor.copiedStyle) {
                    // Save state once before batch operation
                    editor.saveState();
                    const pastedCount = editor.selectedObjects.length;
                    
                    // Apply style to all selected objects
                    editor.selectedObjects.forEach(obj => {
                        // Apply directly without triggering saveState each time
                        editor._applyStyleToObject(obj);
                    });
                    
                    if (editor.debugger) {
                        const modeLabel = editor.csmsMode ? '🎨 CS-MS (Long Press)' : '🖌️ CS-MS';
                        editor.debugger.logSuccess(`${modeLabel}: Style pasted to ${pastedCount} objects`);
                    }
                    
                    // Exit paste style mode and CS-MS mode after operation
                    editor.csmsMode = false;
                    editor.exitPasteStyleMode();
                    editor.draw();
                    return;
                }
                
                editor.multiSelectMode = true; // Allow group drag on next mousedown
                
                // SEAMLESS: Resume link mode if came from there, otherwise stay in select
                if (editor.resumeModeAfterMarquee === 'link') {
                    editor.currentMode = 'link';
                    editor.currentTool = 'link';
                    // Update UI to show link mode - with null checks
                    const btnBaseL = document.getElementById('btn-base');
                    const btnSelectL = document.getElementById('btn-select');
                    const btnLinkL = document.getElementById('btn-link');
                    if (btnBaseL) btnBaseL.classList.remove('active');
                    if (btnSelectL) btnSelectL.classList.remove('active');
                    if (btnLinkL) btnLinkL.classList.add('active');
                    editor.updateModeIndicator();
                    
                    if (editor.debugger) {
                        editor.debugger.logSuccess(`👆 MS → LINK mode: ${editor.selectedObjects.length} objects selected`);
                        editor.debugger.logInfo(`Seamless transition back to LINK mode`);
                    }
                } else {
                    editor.currentMode = 'select'; // Stay in select mode to handle multi-select
                    editor.currentTool = 'select';
                    // Update UI to show select mode - with null checks
                    const btnBaseS = document.getElementById('btn-base');
                    const btnSelectS = document.getElementById('btn-select');
                    if (btnBaseS) btnBaseS.classList.remove('active');
                    if (btnSelectS) btnSelectS.classList.add('active');
                    editor.updateModeIndicator();
                    
                    if (editor.debugger) {
                        editor.debugger.logSuccess(`👆 MS mode: ${editor.selectedObjects.length} objects selected`);
                    }
                }
                
                editor.backgroundClickCount = 0; // Reset counter for new selection
                editor.resumePlacementAfterMarquee = null;
                editor.resumeModeAfterMarquee = null;
            } else {
                // No objects selected
                // CS-MS MODE: If no objects selected, stay in paste mode
                if (editor.csmsMode) {
                    editor.csmsMode = false;
                    // Restore paste style cursor
                    editor.canvas.style.cursor = 'copy';
                    if (editor.debugger) {
                        editor.debugger.logInfo(`CS-MS: No objects selected - still in paste mode`);
                    }
                } else if (editor.resumePlacementAfterMarquee) {
                    // SEAMLESS: Resume device placement if came from there
                    editor.setDevicePlacementMode(editor.resumePlacementAfterMarquee);
                    editor.resumePlacementAfterMarquee = null;
                    
                    if (editor.debugger) {
                        editor.debugger.logInfo(`Seamless transition: MS empty -> Device placement resumed`);
                    }
                } else if (editor.resumeModeAfterMarquee) {
                    const modeToResume = editor.resumeModeAfterMarquee;
                    editor.setMode(modeToResume);
                    editor.resumeModeAfterMarquee = null;
                    
                    if (editor.debugger) {
                        editor.debugger.logInfo(`Seamless transition: MS empty -> ${modeToResume.toUpperCase()} resumed`);
                    }
                } else {
                    editor.setMode('base');
                }
            }
            
            editor.draw(); // Redraw without rectangle
            return;
        }
        
        // Apply momentum/sliding if dragging ended
        // CRITICAL: Don't apply momentum if we were resizing or rotating (interferes with handles)
        // CRITICAL FIX: Don't apply momentum if there was no significant movement (just a tap/click)
        if (editor.dragging && editor.momentum && editor.momentum.enabled && editor.selectedObject &&
            !editor.resizingDevice && !editor.rotatingDevice) {
            
            // Check if there was actual movement (not just a tap)
            let actuallyMoved = false;
            const minDragDistance = 3; // Minimum pixels of movement to be considered a drag
            
            if (editor.dragStartPos) {
                if (editor.selectedObject.type === 'unbound') {
                    // For unbound links, check center position movement
                    const currentCenterX = (editor.selectedObject.start.x + editor.selectedObject.end.x) / 2;
                    const currentCenterY = (editor.selectedObject.start.y + editor.selectedObject.end.y) / 2;
                    const dx = currentCenterX - editor.dragStartPos.x;
                    const dy = currentCenterY - editor.dragStartPos.y;
                    const dragDistance = Math.sqrt(dx * dx + dy * dy);
                    actuallyMoved = dragDistance > minDragDistance;
                } else if (editor.selectedObject.x !== undefined && editor.selectedObject.y !== undefined) {
                    // For devices and text objects
                    const dx = editor.selectedObject.x - editor.dragStartPos.x;
                    const dy = editor.selectedObject.y - editor.dragStartPos.y;
                    const dragDistance = Math.sqrt(dx * dx + dy * dy);
                    actuallyMoved = dragDistance > minDragDistance;
                } else {
                    // Fallback: check velocity history
                    actuallyMoved = editor.momentum.velocityHistory.length > 2;
                }
            } else {
                // For objects without stored start position, check velocity history
                actuallyMoved = editor.momentum.velocityHistory.length > 2;
            }
            
            // Only apply momentum if there was actual dragging movement
            if (actuallyMoved) {
            const velocity = editor.momentum.calculateReleaseVelocity();
            const speed = Math.sqrt(velocity.vx * velocity.vx + velocity.vy * velocity.vy);
            
            if (speed > editor.momentum.minVelocity) {
                // Start sliding for this object
                editor.momentum.startSlide(editor.selectedObject, velocity.vx, velocity.vy);
                }
            } else {
                // No movement detected - this was just a tap/click, not a drag
                // Reduced logging: Don't log every tap
                // if (editor.debugger) {
                //     editor.debugger.logInfo(`✓ Tap detected (no drag)`);
                // }
            }
        }
        
        // Save state after any operation completes (before clearing flags)
        // This captures the FINAL state after drag/resize/rotate/text operations
        if (editor.dragging || editor.resizingText || editor.rotatingText || editor.rotatingDevice || editor.resizingDevice || editor.stretchingLink) {
            console.log('Saving final state after operation');
            // Don't save immediately if momentum slide is starting (it will save when slide ends)
            if (!(editor.momentum && editor.momentum.activeSlides.size > 0)) {
                editor.saveState(); // Capture final state and trigger auto-save
            }
        }
        
        editor.rotatingText = false;
        editor.resizingText = false;
        if (editor.rotatingDevice) {
            const dev = editor.rotatingDevice;
            editor.rotatingDevice = null;
            editor.updateCursor();
            if (editor.selectedObject === dev) {
                setTimeout(() => {
                    if (editor.selectedObject === dev && !editor.dragging) {
                        editor.showDeviceSelectionToolbar(dev);
                    }
                }, 50);
            }
        }
        if (editor.resizingDevice) {
            const dev = editor.resizingDevice;
            editor.resizingDevice = null;
            editor.resizeHandle = null;
            editor.resizeStartDist = 0;
            editor.updateCursor();
            if (editor.selectedObject === dev) {
                setTimeout(() => {
                    if (editor.selectedObject === dev && !editor.dragging) {
                        editor.showDeviceSelectionToolbar(dev);
                    }
                }, 50);
            }
        }
        
        // Clear shape resize state and reshow toolbar
        if (editor.resizingShape) {
            const shape = editor.resizingShape;
            editor.resizingShape = null;
            editor.shapeResizeHandle = null;
            editor._shapeResizeStart = null;
            editor.scheduleAutoSave();
            editor.updateCursor();
            
            // Reshow shape toolbar after resize completes
            if (editor.selectedObject === shape) {
                setTimeout(() => {
                    if (editor.selectedObject === shape && !editor.dragging) {
                        editor.showShapeSelectionToolbar(shape);
                    }
                }, 50);
            }
        }
        
        // Clear shape rotation state and reshow toolbar
        if (editor.rotatingShape) {
            const shape = editor.rotatingShape;
            editor.rotatingShape = null;
            editor._shapeRotationStart = null;
            editor.scheduleAutoSave();
            editor.updateCursor();
            
            // Reshow shape toolbar after rotation completes
            if (editor.selectedObject === shape) {
                setTimeout(() => {
                    if (editor.selectedObject === shape && !editor.dragging) {
                        editor.showShapeSelectionToolbar(shape);
                    }
                }, 50);
            }
        }
        
        // CRITICAL: Check if stretching link endpoint should attach to a device OR another UL endpoint
        // Only attach if sticky links mode is enabled AND link doesn't have sticky disabled
        const linkStickyEnabled = editor.linkStickyMode && !editor.stretchingLink?.stickyDisabled;
        if (editor.stretchingLink && editor.stretchingEndpoint && linkStickyEnabled) {
            const endpointPos = editor.stretchingEndpoint === 'start' 
                ? editor.stretchingLink.start 
                : editor.stretchingLink.end;
            
            // CRITICAL FIX: Check if the stretching endpoint is a FREE TP (not an MP)
            // Only FREE TPs can merge with other FREE TPs to create new MPs
            let stretchingEndpointIsFree = true;
            
            // If we're dragging a connection point (MP), it's not free
            if (editor.stretchingConnectionPoint) {
                stretchingEndpointIsFree = false;
            }
            
            // Check if stretchingLink is part of a BUL and if the stretchingEndpoint is an MP
            if (editor.stretchingLink.mergedWith) {
                // This link is a parent in a BUL
                // parentFreeEnd tells us which end IS FREE, the opposite is an MP
                const parentFreeEnd = editor.stretchingLink.mergedWith.parentFreeEnd;
                if (editor.stretchingEndpoint !== parentFreeEnd) {
                    // We're dragging the connected end (MP), not the free end
                    stretchingEndpointIsFree = false;
                }
            }
            
            if (editor.stretchingLink.mergedInto) {
                // This link is a child in a BUL
                const parentLink = editor.objects.find(o => o.id === editor.stretchingLink.mergedInto.parentId);
                if (parentLink && parentLink.mergedWith) {
                    // childFreeEnd tells us which end of this child IS FREE
                    const childFreeEnd = parentLink.mergedWith.childFreeEnd;
                    if (editor.stretchingEndpoint !== childFreeEnd) {
                        // We're dragging the connected end (MP), not the free end
                        stretchingEndpointIsFree = false;
                    }
                }
            }
            
            // ENHANCED: First check for nearby UL endpoints to snap together
            // CRITICAL: Only look for merge candidates if the stretching endpoint is FREE
            let nearbyULEndpoint = null;
            let nearbyULLink = null;
            let nearbyULEndpointType = null;
            let ulSnapDistance = Infinity;
            
            // Only search for merge targets if the stretching endpoint is a FREE TP
            if (!stretchingEndpointIsFree) {
                if (editor.debugger) {
                    editor.debugger.logInfo(`🚫 Dragging MP, not TP - skipping merge search`);
                }
                // Skip to device attachment logic (MPs don't merge but TPs do)
            } else {
            editor.objects.forEach(obj => {
                if (obj.type === 'unbound' && obj.id !== editor.stretchingLink.id) {
                    // CRITICAL: Skip middle links entirely - they have NO free ends!
                    // If a link has BOTH mergedInto AND mergedWith, both ends are MPs
                    if (obj.mergedInto && obj.mergedWith) {
                        return; // Skip this link completely - it's in the middle of a chain
                    }
                    
                    // ENHANCED: Skip endpoints that are:
                    // 1. Attached to devices (they're not available for merging)
                    // 2. Connection points (endpoints that are already merged)
                    
                    // Check if start endpoint is a connection point (MP)
                    let startIsConnectionPoint = false;
                    if (obj.connectedTo && obj.connectedTo.thisEndpoint === 'start') {
                        startIsConnectionPoint = true;
                    } else if (obj.mergedWith && obj.mergedWith.parentFreeEnd !== 'start') {
                        // This is a parent link, and start is the connected end (not free)
                        startIsConnectionPoint = true;
                    } else if (obj.mergedInto) {
                        // This is a child link - check which end is connected
                        const parentLink = editor.objects.find(o => o.id === obj.mergedInto.parentId);
                        if (parentLink && parentLink.mergedWith) {
                            // Child's connected end is opposite of child's free end
                            const childFreeEnd = parentLink.mergedWith.childFreeEnd;
                            startIsConnectionPoint = (childFreeEnd !== 'start'); // Start is connected if it's NOT the free end
                        }
                    }
                    
                    // CRITICAL ADDITIONAL CHECK: If this link has BOTH parent and child,
                    // it's in the MIDDLE of a chain and BOTH ends are MPs!
                    if (!startIsConnectionPoint && obj.mergedInto && obj.mergedWith) {
                        // Link in middle - both ends are connection points (MPs)
                        // Neither end is available for merging
                        startIsConnectionPoint = true;
                    }
                    
                    // Check start endpoint (only if not attached to device AND not a connection point)
                    if (!obj.device1 && !startIsConnectionPoint) {
                    const distStart = Math.sqrt(
                        Math.pow(endpointPos.x - obj.start.x, 2) + 
                        Math.pow(endpointPos.y - obj.start.y, 2)
                    );
                    if (distStart < editor.ulSnapDistance && distStart < ulSnapDistance) {
                        nearbyULEndpoint = obj.start;
                        nearbyULLink = obj;
                        nearbyULEndpointType = 'start';
                        ulSnapDistance = distStart;
                        }
                    }
                    
                    // Check if end endpoint is a connection point (MP)
                    let endIsConnectionPoint = false;
                    if (obj.connectedTo && obj.connectedTo.thisEndpoint === 'end') {
                        endIsConnectionPoint = true;
                    } else if (obj.mergedWith && obj.mergedWith.parentFreeEnd !== 'end') {
                        // This is a parent link, and end is the connected end (not free)
                        endIsConnectionPoint = true;
                    } else if (obj.mergedInto) {
                        // This is a child link - check which end is connected
                        const parentLink = editor.objects.find(o => o.id === obj.mergedInto.parentId);
                        if (parentLink && parentLink.mergedWith) {
                            // Child's connected end is opposite of child's free end
                            const childFreeEnd = parentLink.mergedWith.childFreeEnd;
                            endIsConnectionPoint = (childFreeEnd !== 'end'); // End is connected if it's NOT the free end
                        }
                    }
                    
                    // CRITICAL ADDITIONAL CHECK: If this link has BOTH parent and child,
                    // it's in the MIDDLE of a chain and BOTH ends are MPs!
                    if (!endIsConnectionPoint && obj.mergedInto && obj.mergedWith) {
                        // Link in middle - both ends are connection points (MPs)
                        // Neither end is available for merging
                        endIsConnectionPoint = true;
                    }
                    
                    // Check end endpoint (only if not attached to device AND not a connection point)
                    if (!obj.device2 && !endIsConnectionPoint) {
                    const distEnd = Math.sqrt(
                        Math.pow(endpointPos.x - obj.end.x, 2) + 
                        Math.pow(endpointPos.y - obj.end.y, 2)
                    );
                    if (distEnd < editor.ulSnapDistance && distEnd < ulSnapDistance) {
                        nearbyULEndpoint = obj.end;
                        nearbyULLink = obj;
                        nearbyULEndpointType = 'end';
                        ulSnapDistance = distEnd;
                        }
                    }
                }
            });
            } // Close the else block for stretchingEndpointIsFree check
            
            // If found nearby UL endpoint, snap and merge the links into one logical link
            if (nearbyULLink && nearbyULEndpoint) {
                // CRITICAL: Check if these two links already share an MP (connection point)
                // If they do, prevent creating another connection between their free TPs
                const alreadyShareMP = editor.linksAlreadyShareMP(editor.stretchingLink, nearbyULLink);
                
                if (alreadyShareMP) {
                    // These links already have an MP together - don't allow another connection
                    if (editor.debugger) {
                        editor.debugger.logInfo(`🚫 Cannot merge: Links already share an MP`);
                    }
                    // Don't merge - just return without creating new connection
                    return;
                }
                
                // CRITICAL: Snap the NEW link's endpoint to the EXISTING link's endpoint
                // The existing link stays in place - only the new link moves to connect
                // This ensures links keep their position when merging
                if (editor.stretchingEndpoint === 'start') {
                    editor.stretchingLink.start.x = nearbyULEndpoint.x;
                    editor.stretchingLink.start.y = nearbyULEndpoint.y;
                } else {
                    editor.stretchingLink.end.x = nearbyULEndpoint.x;
                    editor.stretchingLink.end.y = nearbyULEndpoint.y;
                }
                
                // UNIFIED TP MERGE: Simplified, geometry-based merge logic
                const connectionPoint = { x: nearbyULEndpoint.x, y: nearbyULEndpoint.y };
                
                // Helper: Find the actual chain end (not middle links)
                const findChainEnd = (link, direction) => {
                    if (!link) return null;
                    let current = link;
                    if (direction === 'parent') {
                        while (current.mergedInto) {
                            const parent = editor.objects.find(o => o.id === current.mergedInto.parentId);
                            if (!parent) break;
                            current = parent;
                        }
                    } else {
                        while (current.mergedWith) {
                            const child = editor.objects.find(o => o.id === current.mergedWith.linkId);
                            if (!child) break;
                            current = child;
                        }
                    }
                    return current;
                };
                
                // Step 1: Find actual chain ends (never merge to middle links)
                let targetLink = nearbyULLink;
                let targetEndpoint = nearbyULEndpointType;
                
                // If target is a middle link (both mergedInto and mergedWith), find the chain end
                if (targetLink.mergedInto && targetLink.mergedWith) {
                    // Determine which side we're closer to
                    const parentEnd = findChainEnd(targetLink, 'parent');
                    const childEnd = findChainEnd(targetLink, 'child');
                    
                    const parentDist = parentEnd ? Math.hypot(
                        (parentEnd[parentEnd.mergedWith?.parentFreeEnd || 'start']?.x || 0) - connectionPoint.x,
                        (parentEnd[parentEnd.mergedWith?.parentFreeEnd || 'start']?.y || 0) - connectionPoint.y
                    ) : Infinity;
                    
                    const childDist = childEnd ? Math.hypot(
                        (childEnd[childEnd.mergedInto ? (editor.objects.find(o => o.id === childEnd.mergedInto.parentId)?.mergedWith?.childFreeEnd || 'start') : 'start']?.x || 0) - connectionPoint.x,
                        (childEnd[childEnd.mergedInto ? (editor.objects.find(o => o.id === childEnd.mergedInto.parentId)?.mergedWith?.childFreeEnd || 'start') : 'start']?.y || 0) - connectionPoint.y
                    ) : Infinity;
                    
                    if (parentDist < childDist && parentEnd) {
                        targetLink = parentEnd;
                        targetEndpoint = parentEnd.mergedWith?.parentFreeEnd || 'start';
                    } else if (childEnd) {
                        targetLink = childEnd;
                        const childParent = editor.objects.find(o => o.id === childEnd.mergedInto?.parentId);
                        targetEndpoint = childParent?.mergedWith?.childFreeEnd || 'end';
                    }
                } else if (targetLink.mergedWith && !targetLink.mergedInto) {
                    // Target is a parent - if connecting to occupied end, find chain end
                    const targetFreeEnd = targetLink.mergedWith.parentFreeEnd;
                    if (targetEndpoint !== targetFreeEnd) {
                        const chainEnd = findChainEnd(targetLink, 'child');
                        if (chainEnd) {
                            targetLink = chainEnd;
                            const chainParent = editor.objects.find(o => o.id === chainEnd.mergedInto?.parentId);
                            targetEndpoint = chainParent?.mergedWith?.childFreeEnd || 'end';
                        }
                    }
                } else if (targetLink.mergedInto && !targetLink.mergedWith) {
                    // Target is a TAIL (child with no children of its own)
                    // CRITICAL FIX: Don't redirect to head! Keep the tail and use its free end
                    // The tail's free end is stored in its parent's mergedWith metadata
                    const tailParent = editor.objects.find(o => o.id === targetLink.mergedInto.parentId);
                    if (tailParent?.mergedWith) {
                        targetEndpoint = tailParent.mergedWith.childFreeEnd;
                    }
                    // Keep targetLink as-is (the tail) - don't redirect to head!
                }
                
                // Step 2: Determine parent/child relationship
                // ENHANCED: Unified logic for all merge scenarios
                
                let parentLink = targetLink;
                let childLink = editor.stretchingLink;
                
                // Check if links are in BULs
                const stretchingIsInBUL = childLink.mergedWith || childLink.mergedInto;
                const targetIsInBUL = parentLink.mergedWith || parentLink.mergedInto;
                
                // Helper to renumber MPs in a chain
                const renumberChainMPs = (startLink) => {
                    let current = findChainEnd(startLink, 'parent') || startLink;
                    let count = 0;
                    const chainLinks = [];
                    
                    // First pass: collect all links
                    let temp = current;
                    while (temp) {
                        chainLinks.push(temp);
                        if (!temp.mergedWith) break;
                        const nextId = temp.mergedWith.linkId;
                        temp = editor.objects.find(o => o.id === nextId);
                    }
                    
                    // Second pass: assign MP numbers
                    // MP-1 is between Link 1 and Link 2
                    for (let i = 0; i < chainLinks.length - 1; i++) {
                        const link = chainLinks[i];
                        if (link.mergedWith) {
                            link.mergedWith.mpNumber = i + 1;
                        }
                    }
                };

                // CRITICAL CASE: Standalone UL joining BUL (or vice versa)
                if (!stretchingIsInBUL && targetIsInBUL) {
                    // Standalone UL (childLink) -> BUL (parentLink)
                    
                    const chainHead = findChainEnd(parentLink, 'parent') || parentLink;
                    const chainTail = findChainEnd(parentLink, 'child') || parentLink;
                    
                    // CRITICAL FIX: Use SYMMETRIC logic for both prepend and append
                    const detectIsHead = nearbyULLink.id === chainHead.id;
                    const detectIsTail = nearbyULLink.id === chainTail.id;
                    
                    if (detectIsHead) {
                        // PREPEND: Connecting to HEAD
                        // Set parentLink to head and get its free end
                        parentLink = chainHead;
                        if (chainHead.mergedWith) {
                            targetEndpoint = chainHead.mergedWith.parentFreeEnd;
                        }
                        
                        // SWAP: Standalone becomes parent
                        [parentLink, childLink] = [childLink, parentLink];
                        
                        if (editor.debugger) editor.debugger.logInfo('   PREPEND to HEAD: Standalone->Parent, Head->Child');
                        
                    } else if (detectIsTail) {
                        // APPEND: Connecting to TAIL  
                        // Set parentLink to tail and get its free end
                        parentLink = chainTail;
                        if (chainTail.mergedInto) {
                            const tailParent = editor.objects.find(o => o.id === chainTail.mergedInto.parentId);
                            if (tailParent?.mergedWith) {
                                targetEndpoint = tailParent.mergedWith.childFreeEnd;
                            }
                        }
                        
                        // NO SWAP: Tail stays as parent, Standalone is child
                        // parentLink = UL-2, childLink = UL-3
                        
                        if (editor.debugger) editor.debugger.logInfo('   APPEND to TAIL: Tail->Parent, Standalone->Child');
                    }

                } else if (stretchingIsInBUL && !targetIsInBUL) {
                    // BUL (childLink) -> Standalone (parentLink)
                    
                    const chainHead = findChainEnd(childLink, 'parent') || childLink;
                    const chainTail = findChainEnd(childLink, 'child') || childLink;
                    
                    const isHead = childLink.id === chainHead.id;
                    const isTail = childLink.id === chainTail.id;
                    
                    // Check if dragging Head's free end (Prepend)
                    let isPrepend = false;
                    if (isHead && childLink.mergedWith) {
                         const headFreeEnd = childLink.mergedWith.parentFreeEnd;
                         if (editor.stretchingEndpoint === headFreeEnd) {
                             isPrepend = true;
                         }
                    }

                    if (isPrepend) {
                        // Standalone -> Head. Standalone is Parent.
                        // No swap needed (parentLink is already Standalone)
                        if (editor.debugger) editor.debugger.logInfo('   Dragged HEAD to Standalone (Prepend)');
                    } else {
                        // Tail -> Standalone. Tail becomes Parent.
                        // If middle link dragged, treat as Tail
                        if (!isTail) {
                            childLink = chainTail;
                        }
                        [parentLink, childLink] = [childLink, parentLink];
                        if (editor.debugger) editor.debugger.logInfo('   Dragged TAIL to Standalone (Append)');
                    }
                } else if (stretchingIsInBUL && targetIsInBUL) {
                    // Both in BULs - join two chains
                    // Always append stretching chain to target chain (simplified)
                    
                    const targetChainTail = findChainEnd(parentLink, 'child') || parentLink;
                    const stretchingChainHead = findChainEnd(childLink, 'parent') || childLink;
                    
                    parentLink = targetChainTail;
                    childLink = stretchingChainHead;
                    
                    // FIXED: Get tail's free end directly from parent metadata (don't use getOppositeEndpoint)
                    if (targetChainTail.mergedInto) {
                        const tailParent = editor.objects.find(o => o.id === targetChainTail.mergedInto.parentId);
                        if (tailParent?.mergedWith) {
                            targetEndpoint = tailParent.mergedWith.childFreeEnd;
                        }
                    } else {
                         targetEndpoint = targetChainTail.mergedWith ? targetChainTail.mergedWith.childFreeEnd : 'end';
                    }
                }

                // Step 3: Use geometry to detect actual connecting endpoints
                let parentConnectingEnd, childConnectingEnd;
                
                // Determine endpoints based on CURRENT roles (swapped or not)
                // We use the original stretching/target identifiers to map back to endpoints
                
                const isParentStretching = (parentLink.id === editor.stretchingLink.id);
                const isChildStretching = (childLink.id === editor.stretchingLink.id);
                
                if (isParentStretching) {
                    parentConnectingEnd = editor.stretchingEndpoint; 
                } else {
                    // If parent was target, use targetEndpoint (already calculated above)
                    // FIXED: Don't recalculate with getOppositeEndpoint - use the targetEndpoint we already determined
                    parentConnectingEnd = targetEndpoint;
                }
                
                if (isChildStretching) {
                    childConnectingEnd = editor.stretchingEndpoint;
                        } else {
                    // If child was target (e.g. dragging Head to Standalone -> Prepend)
                     if (childLink.mergedWith) {
                        childConnectingEnd = childLink.mergedWith.parentFreeEnd;
                    } else {
                        childConnectingEnd = editor.getLinkEndpointNearPoint(childLink, connectionPoint) || (targetEndpoint === 'start' ? 'start' : 'end');
                    }
                }
                
                // Step 4: Calculate free ends
                // CRITICAL: For middle links (has both mergedInto and mergedWith), there is NO free end!
                // But we still need to store which end is "free" in the context of THIS merge
                let parentFreeEnd, childFreeEnd;
                
                // Check if parent will become middle link (already has mergedInto)
                if (parentLink.mergedInto) {
                    // Parent is/will be middle link - its "free" end is the one NOT connecting to child
                    parentFreeEnd = editor.getOppositeEndpoint(parentConnectingEnd);
                    // This end is NOT actually free (it's connected to another link), but we need to store it
                    if (editor.debugger) {
                        editor.debugger.logWarning(`⚠️ ${parentLink.id} will be MIDDLE LINK - no truly free ends`);
                    }
                } else {
                    // Parent is head or standalone - free end is opposite of connecting end
                    parentFreeEnd = editor.getOppositeEndpoint(parentConnectingEnd);
                }
                
                // Check if child will become middle link (already has mergedWith)  
                if (childLink.mergedWith) {
                    // Child is/will be middle link
                    childFreeEnd = editor.getOppositeEndpoint(childConnectingEnd);
                    if (editor.debugger) {
                        editor.debugger.logWarning(`⚠️ ${childLink.id} will be MIDDLE LINK - no truly free ends`);
                    }
                } else {
                    // Child is tail or standalone
                    childFreeEnd = editor.getOppositeEndpoint(childConnectingEnd);
                }
                
                if (editor.debugger) {
                    editor.debugger.logInfo(`   Calculated parentFreeEnd: ${parentFreeEnd} (opposite of ${parentConnectingEnd})`);
                    editor.debugger.logInfo(`   Calculated childFreeEnd: ${childFreeEnd} (opposite of ${childConnectingEnd})`);
                }
                
                // Step 5: Merge
                if (!parentLink.mergedWith || parentLink.mergedWith.linkId !== childLink.id) {
                    // DEBUG: Log COMPLETE chain state before merge
                    if (editor.debugger) {
                        editor.debugger.logInfo(`━━━━━━━━━ BEFORE MERGE ━━━━━━━━━`);
                        
                        // Show entire existing chain if any
                        if (parentLink.mergedInto || parentLink.mergedWith) {
                            const existingChain = editor.getAllMergedLinks(parentLink);
                            editor.debugger.logInfo(`   Existing chain: ${existingChain.length} links`);
                            existingChain.forEach((link, i) => {
                                editor.debugger.logInfo(`     U${i+1}: ${link.id} | ↑${link.mergedInto?.parentId || 'none'} | ↓${link.mergedWith?.linkId || 'none'}`);
                            });
                        }
                        
                        editor.debugger.logInfo(`📝 Creating Merge Metadata:`);
                        editor.debugger.logInfo(`   Parent: ${parentLink.id}`);
                        editor.debugger.logInfo(`   Child: ${childLink.id}`);
                        editor.debugger.logInfo(`   Parent state: mergedInto=${parentLink.mergedInto ? parentLink.mergedInto.parentId : 'none'}, mergedWith=${parentLink.mergedWith ? parentLink.mergedWith.linkId : 'none'}`);
                        editor.debugger.logInfo(`   Child state: mergedInto=${childLink.mergedInto ? childLink.mergedInto.parentId : 'none'}, mergedWith=${childLink.mergedWith ? childLink.mergedWith.linkId : 'none'}`);
                        editor.debugger.logInfo(`   Endpoints: parent-${parentConnectingEnd}, child-${childConnectingEnd}`);
                        editor.debugger.logInfo(`   Free ends: parent-${parentFreeEnd}, child-${childFreeEnd}`);
                    }
                    
                    // Create merge
                // CRITICAL: Check if we're OVERWRITING existing connections before creating new ones
                const parentHadMergedWith = !!parentLink.mergedWith;
                const childHadMergedInto = !!childLink.mergedInto;
                
                // CRITICAL FIX: CLONE connectionPoint for EACH metadata object!
                // They MUST be separate objects or updating one MP will affect all others!
                const parentConnectionPoint = { x: connectionPoint.x, y: connectionPoint.y };
                const childConnectionPoint = { x: connectionPoint.x, y: connectionPoint.y };
                
                parentLink.mergedWith = {
                    linkId: childLink.id,
                    connectionPoint: parentConnectionPoint, // CLONED - not shared!
                        parentFreeEnd: parentFreeEnd,
                        childFreeEnd: childFreeEnd,
                    childStart: { x: childLink.start.x, y: childLink.start.y },
                    childEnd: { x: childLink.end.x, y: childLink.end.y },
                        parentDevice: parentFreeEnd === 'start' ? parentLink.device1 : parentLink.device2,
                        childDevice: childFreeEnd === 'start' ? childLink.device1 : childLink.device2,
                    mpCreatedAt: Date.now(),
                        mpNumber: 0, // Will be updated by renumberChainMPs
                        connectionEndpoint: parentConnectingEnd,
                        childConnectionEndpoint: childConnectingEnd
                };
                
                // CRITICAL FIX: ALWAYS create/update childLink.mergedInto, even if it exists!
                // This is needed for prepend scenarios where childLink (after swap) already has mergedInto
                // But we need to ADD a new parent connection (the one we're creating now)
                // WAIT - a link can only have ONE parent! If childLink already has mergedInto, something is wrong!
                
                if (childHadMergedInto) {
                    if (editor.debugger) {
                        editor.debugger.logError(`🚨 CRITICAL: ${childLink.id} already has mergedInto! This means it's a middle/tail link being used as child.`);
                        editor.debugger.logError(`   This is WRONG - child should only have mergedWith (be a parent), not mergedInto!`);
                        editor.debugger.logError(`   Role swap may have failed!`);
                    }
                }
                
                childLink.mergedInto = {
                    parentId: parentLink.id,
                    connectionPoint: childConnectionPoint, // CLONED - not shared!
                            childEndpoint: childConnectingEnd,
                            parentEndpoint: parentConnectingEnd
                };
                
                // CRITICAL VALIDATION: Verify endpoints make sense
                if (editor.debugger) {
                    // Check if stored endpoints match actual connection geometry
                    const parentActualEnd = parentConnectingEnd === 'start' ? parentLink.start : parentLink.end;
                    const childActualEnd = childConnectingEnd === 'start' ? childLink.start : childLink.end;
                    const dist = Math.hypot(
                        parentActualEnd.x - childActualEnd.x,
                        parentActualEnd.y - childActualEnd.y
                    );
                    
                    if (dist > 5) {
                        editor.debugger.logError(`🚨 ENDPOINT MISMATCH: Stored endpoints don't connect!`);
                        editor.debugger.logError(`   ${parentLink.id}[${parentConnectingEnd}] at (${parentActualEnd.x.toFixed(1)}, ${parentActualEnd.y.toFixed(1)})`);
                        editor.debugger.logError(`   ${childLink.id}[${childConnectingEnd}] at (${childActualEnd.x.toFixed(1)}, ${childActualEnd.y.toFixed(1)})`);
                        editor.debugger.logError(`   Distance: ${dist.toFixed(1)}px (should be ~0)`);
                    } else {
                        editor.debugger.logSuccess(`✅ Endpoints validated: distance=${dist.toFixed(2)}px`);
                    }
                }
                
                    // DEBUG: Verify what was created
                    if (editor.debugger) {
                        editor.debugger.logSuccess(`✅ Merge Created Successfully`);
                        editor.debugger.logInfo(`   ${parentLink.id}.mergedWith → ${childLink.id}`);
                        editor.debugger.logInfo(`   ${childLink.id}.mergedInto → ${parentLink.id}`);
                        editor.debugger.logInfo(`   Parent AFTER: mergedInto=${parentLink.mergedInto ? parentLink.mergedInto.parentId : 'none'}, mergedWith=${parentLink.mergedWith.linkId}`);
                        editor.debugger.logInfo(`   Child AFTER: mergedInto=${childLink.mergedInto.parentId}, mergedWith=${childLink.mergedWith ? childLink.mergedWith.linkId : 'none'}`);
                        
                        // CRITICAL CHECK: If parent is UL-2 (middle link), verify both connections intact
                        if (parentLink.mergedInto && parentLink.mergedWith) {
                            editor.debugger.logWarning(`⚠️ MIDDLE LINK: ${parentLink.id} now has BOTH connections`);
                            editor.debugger.logInfo(`   UP to: ${parentLink.mergedInto.parentId} (should be UL-1)`);
                            editor.debugger.logInfo(`   DOWN to: ${parentLink.mergedWith.linkId} (should be UL-3)`);
                            editor.debugger.logInfo(`   Check MP-1 metadata in UL-1.mergedWith:`);
                            const ul1 = editor.objects.find(o => o.id === parentLink.mergedInto.parentId);
                            if (ul1?.mergedWith) {
                                editor.debugger.logInfo(`   UL-1.mergedWith.linkId: ${ul1.mergedWith.linkId}`);
                                editor.debugger.logInfo(`   UL-1.mergedWith.parentEndpoint: ${ul1.mergedWith.connectionEndpoint}`);
                                editor.debugger.logInfo(`   UL-1.mergedWith.childEndpoint: ${ul1.mergedWith.childConnectionEndpoint}`);
                            }
                        }
                    }

                    // CRITICAL FIX: When creating a middle link, DON'T update parent's metadata!
                    // The parent's childFreeEnd/childConnectionEndpoint should STAY THE SAME
                    // because they describe how the parent connects to THIS child, not what the child does elsewhere
                    //
                    // KEY INSIGHT: childFreeEnd means "child's end that is NOT connecting to parent"
                    // When child was tail: end was free (not connecting to parent = start connects)
                    // When child is middle: end connects to grandchild (still not connecting to parent!)
                    // So childFreeEnd should NOT change! It's still the "other" end.
                    //
                    // The metadata is RELATIVE to the parent-child relationship, not absolute!
                    
                    // DEBUG ONLY: Verify grandparent metadata is still correct
                    if (editor.debugger && parentLink.mergedInto) {
                        const grandparent = editor.objects.find(o => o.id === parentLink.mergedInto.parentId);
                        if (grandparent?.mergedWith && grandparent.mergedWith.linkId === parentLink.id) {
                            editor.debugger.logInfo(`🔍 ${grandparent.id}.mergedWith (MP-1) metadata unchanged:`);
                            editor.debugger.logInfo(`   childFreeEnd: ${grandparent.mergedWith.childFreeEnd} (other end from connection)`);
                            editor.debugger.logInfo(`   childConnectionEnd: ${grandparent.mergedWith.childConnectionEndpoint} (connects to ${grandparent.id})`);
                        }
                    }
                    
                    // Renumber MPs for the entire chain
                    renumberChainMPs(parentLink);
                    
                    // CRITICAL VERIFICATION: Check entire chain metadata integrity
                    if (editor.debugger) {
                        const allLinks = editor.getAllMergedLinks(parentLink);
                        editor.debugger.logInfo(`🔍 VERIFICATION: Checking all ${allLinks.length} links in chain...`);
                        
                        allLinks.forEach((link, idx) => {
                            const hasParent = link.mergedInto ? '✓' : '✗';
                            const hasChild = link.mergedWith ? '✓' : '✗';
                            const parentId = link.mergedInto?.parentId || 'none';
                            const childId = link.mergedWith?.linkId || 'none';
                            
                            editor.debugger.logInfo(`   U${idx+1} (${link.id}): ↑${hasParent} parent=${parentId}, ↓${hasChild} child=${childId}`);
                            
                            // Verify endpoints exist
                            if (link.mergedWith) {
                                const cep = link.mergedWith.connectionEndpoint;
                                const ccep = link.mergedWith.childConnectionEndpoint;
                                const pfe = link.mergedWith.parentFreeEnd;
                                const cfe = link.mergedWith.childFreeEnd;
                                if (!cep || !ccep || !pfe || !cfe) {
                                    editor.debugger.logError(`🚨 MISSING ENDPOINTS in ${link.id}.mergedWith: cep=${cep}, ccep=${ccep}, pfe=${pfe}, cfe=${cfe}`);
                                }
                            }
                            if (link.mergedInto) {
                                const pe = link.mergedInto.parentEndpoint;
                                const ce = link.mergedInto.childEndpoint;
                                if (!pe || !ce) {
                                    editor.debugger.logError(`🚨 MISSING ENDPOINTS in ${link.id}.mergedInto: pe=${pe}, ce=${ce}`);
                                }
                            }
                        });
                    }
                        
                        // CRITICAL: Change originType to UL when links are merged
                    if (parentLink.originType === 'QL') parentLink.originType = 'UL';
                    if (childLink.originType === 'QL') childLink.originType = 'UL';
                    
                    // DEBUG: Log merge creation
                        if (editor.debugger) {
                            const allLinks = editor.getAllMergedLinks(parentLink);
                        const isExtending = allLinks.length > 2;
                        if (isExtending) {
                            editor.debugger.logInfo(`🔗 Extending ${allLinks.length}-link BUL chain`);
                                } else {
                            editor.debugger.logInfo(`🔗 Creating new 2-link BUL`);
                        }
                        editor.debugger.logInfo(`   New link: ${editor.stretchingLink.id}, connecting via ${editor.stretchingEndpoint}`);
                        editor.debugger.logInfo(`   Target link: ${nearbyULLink.id}, connecting to ${nearbyULEndpointType}`);
                        editor.debugger.logSuccess(`✅ BUL ${isExtending ? 'extended' : 'created'}! Now ${allLinks.length} links in chain`);
                        
                        const parentUL = allLinks.findIndex(l => l.id === parentLink.id) + 1;
                        const childUL = allLinks.findIndex(l => l.id === childLink.id) + 1;
                        const parentTPUsed = parentFreeEnd === 'start' ? 'end' : 'start';
                        const childTPUsed = childFreeEnd === 'start' ? 'end' : 'start';
                        // Get MP number from the merge metadata (set by renumberChainMPs)
                        const mpNumber = parentLink.mergedWith?.mpNumber || 0;
                        editor.debugger.logInfo(`   🔗 Merge: U${parentUL}-TP(${parentTPUsed}) + U${childUL}-TP(${childTPUsed}) → MP-${mpNumber}`);
                }
                
                // Copy device attachments from child to parent if needed
                    const finalChildFreeEnd = childFreeEnd;
                    const finalParentFreeEnd = parentFreeEnd;
                
                let deviceToCopy = null;
                
                if (finalChildFreeEnd === 'start' && childLink.device1) {
                    deviceToCopy = childLink.device1;
                } else if (finalChildFreeEnd === 'end' && childLink.device2) {
                    deviceToCopy = childLink.device2;
                } else if (childLink.mergedWith) {
                    // Child is also a parent - check its child's device
                    const grandchildLink = editor.objects.find(o => o.id === childLink.mergedWith.linkId);
                    if (grandchildLink) {
                        const grandchildFreeEnd = childLink.mergedWith.childFreeEnd;
                        if (grandchildFreeEnd === 'start' && grandchildLink.device1) {
                            deviceToCopy = grandchildLink.device1;
                        } else if (grandchildFreeEnd === 'end' && grandchildLink.device2) {
                            deviceToCopy = grandchildLink.device2;
                        }
                    }
                    } else if (childLink.mergedInto) {
                        // Child is also a child (middle link) - we can't easily trace through parents
                        // But we can check its free end if it's directly attached
                        if (finalChildFreeEnd === 'start' && childLink.device1) deviceToCopy = childLink.device1;
                        if (finalChildFreeEnd === 'end' && childLink.device2) deviceToCopy = childLink.device2;
                }
                
                if (deviceToCopy) {
                    if (finalParentFreeEnd === 'start') {
                        parentLink.device1 = deviceToCopy;
                            // Clear from child to avoid duplication
                            if (finalChildFreeEnd === 'start') childLink.device1 = null;
                            else if (finalChildFreeEnd === 'end') childLink.device2 = null;
                    } else {
                        parentLink.device2 = deviceToCopy;
                            // Clear from child to avoid duplication
                            if (finalChildFreeEnd === 'start') childLink.device1 = null;
                            else if (finalChildFreeEnd === 'end') childLink.device2 = null;
                        }
                        if (editor.debugger) {
                            editor.debugger.logInfo(`   Moved device attachment: ${deviceToCopy} to parent free end`);
                    }
                }
                
                // Keep the connection tracking for rendering
                // CRITICAL: Use FINAL endpoints after role swapping, not original ones
                parentLink.connectedTo = {
                    linkId: childLink.id,
                    thisEndpoint: parentConnectingEnd,
                    otherEndpoint: childConnectingEnd
                };
                
                childLink.connectedTo = {
                    linkId: parentLink.id,
                    thisEndpoint: childConnectingEnd,
                    otherEndpoint: parentConnectingEnd
                };
                
                // CRITICAL: Update all connection points after merge to ensure chain is synced
                editor.updateAllConnectionPoints();
                
                if (editor.debugger) {
                    // Get all devices connected across the entire BUL chain
                    const connectedDevicesInfo = editor.getAllConnectedDevices(parentLink);
                    const allLinksInChain = connectedDevicesInfo.links;
                    const deviceLabels = connectedDevicesInfo.devices.map(d => d.label || d.id).join(' ↔ ');
                    
                    // ENHANCED: Analyze BUL chain structure
                    const chainAnalysis = editor.analyzeBULChain(parentLink);
                    
                    // Determine which link is new (the one being stretched)
                    const newLinkId = editor.stretchingLink.id;
                    const isExtendingChain = allLinksInChain.length > 2;
                    
                    if (isExtendingChain) {
                        // Find which TPs were merged
                        const stretchingUL = allLinksInChain.findIndex(l => l.id === editor.stretchingLink.id) + 1;
                        const targetUL = allLinksInChain.findIndex(l => l.id === nearbyULLink.id) + 1;
                        const stretchingTPUsed = editor.stretchingEndpoint;
                        const targetTPUsed = nearbyULEndpointType;
                        
                        editor.debugger.logSuccess(`🔗 BUL Extended: ${newLinkId} (U${stretchingUL}) added to chain`);
                        editor.debugger.logInfo(`   🔗 Merge: U${stretchingUL}-TP(${stretchingTPUsed}) + U${targetUL}-TP(${targetTPUsed}) → MP`);
                        
                        // Collect TPs for numbering
                        // FIXED: Use clearer logic - endpoint is TP if NOT connected
                        const tpsInChain = [];
                        allLinksInChain.forEach(chainLink => {
                            let startIsConnected = false;
                            if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'end') startIsConnected = true;
                            if (chainLink.mergedInto) {
                                const parent = editor.objects.find(o => o.id === chainLink.mergedInto.parentId);
                                if (parent?.mergedWith && parent.mergedWith.childFreeEnd === 'end') startIsConnected = true;
                            }
                            if (!startIsConnected) tpsInChain.push({ link: chainLink, endpoint: 'start' });
                            
                            let endIsConnected = false;
                            if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'start') endIsConnected = true;
                            if (chainLink.mergedInto) {
                                const parent = editor.objects.find(o => o.id === chainLink.mergedInto.parentId);
                                if (parent?.mergedWith && parent.mergedWith.childFreeEnd === 'start') endIsConnected = true;
                            }
                            if (!endIsConnected) tpsInChain.push({ link: chainLink, endpoint: 'end' });
                        });
                        
                        // FIXED: Sort TPs by UL number so TP-1 is always on lowest UL, TP-2 on highest
                        tpsInChain.sort((a, b) => {
                            const ulNumA = parseInt(a.link.id.split('_')[1]) || 0;
                            const ulNumB = parseInt(b.link.id.split('_')[1]) || 0;
                            return ulNumA - ulNumB;
                        });
                        
                        // Build TP labels with detailed info
                        const tpLabels = tpsInChain.map((tp, idx) => {
                            const ulNum = allLinksInChain.findIndex(l => l.id === tp.link.id) + 1;
                            const endpointLabel = tp.endpoint === 'start' ? 'start' : 'end';
                            return `TP-${idx + 1}(U${ulNum}-${endpointLabel})`;
                        }).join(', ');
                        
                        // Build MP labels (per-BUL numbering)
                        const mps = [];
                        allLinksInChain.forEach(link => {
                            if (link.mergedWith?.mpNumber) {
                                const ulNum = allLinksInChain.findIndex(l => l.id === link.id) + 1;
                                mps.push({ num: link.mergedWith.mpNumber, ul: ulNum });
                            }
                        });
                        mps.sort((a, b) => a.num - b.num);
                        const mpLabels = mps.map(mp => `MP-${mp.num}(U${mp.ul})`).join(', ');
                        
                        editor.debugger.logInfo(`   📊 Structure: ${chainAnalysis.linkCount} links | ${chainAnalysis.tpCount} TPs | ${chainAnalysis.mpCount} MPs`);
                        editor.debugger.logInfo(`   🔸 TPs: ${tpLabels}`);
                        editor.debugger.logInfo(`   🔸 MPs: ${mpLabels}`);
                        
                        // Show creation order for all links
                        const sortedLinks = allLinksInChain.sort((a, b) => (a.createdAt || 0) - (b.createdAt || 0));
                        const linkLabels = sortedLinks.map((l, i) => `${l.originType || 'UL'}${i + 1}`).join('--🟣--');
                        editor.debugger.logInfo(`   📝 Chain: TP--${linkLabels}--TP`);
                        
                        editor.debugger.logInfo(`   ${chainAnalysis.isValid ? '✅ Valid: 2 TPs at ends + ' + chainAnalysis.mpCount + ' MPs between' : '⚠️ Invalid structure detected!'}`);
                    } else {
                        // BUL Created (first merge of 2 ULs)
                        const parentUL = allLinksInChain.findIndex(l => l.id === parentLink.id) + 1;
                        const childUL = allLinksInChain.findIndex(l => l.id === childLink.id) + 1;
                        
                        // Calculate which TPs were used for merge
                        const parentTPUsed = parentFreeEnd === 'start' ? 'end' : 'start';
                        const childTPUsed = childFreeEnd === 'start' ? 'end' : 'start';
                        
                        editor.debugger.logSuccess(`🔗 BUL Created: ${parentLink.id} (U${parentUL}) + ${childLink.id} (U${childUL})`);
                        editor.debugger.logInfo(`   🔗 Merge: U${parentUL}-TP(${parentTPUsed}) + U${childUL}-TP(${childTPUsed}) → MP-1`);
                        
                        // Collect TPs for the new BUL
                        // FIXED: Use clearer logic - endpoint is TP if NOT connected
                        const tpsInChain = [];
                        allLinksInChain.forEach(chainLink => {
                            let startIsConnected = false;
                            if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'end') startIsConnected = true;
                            if (chainLink.mergedInto) {
                                const parent = editor.objects.find(o => o.id === chainLink.mergedInto.parentId);
                                if (parent?.mergedWith && parent.mergedWith.childFreeEnd === 'end') startIsConnected = true;
                            }
                            if (!startIsConnected) tpsInChain.push({ link: chainLink, endpoint: 'start' });
                            
                            let endIsConnected = false;
                            if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'start') endIsConnected = true;
                            if (chainLink.mergedInto) {
                                const parent = editor.objects.find(o => o.id === chainLink.mergedInto.parentId);
                                if (parent?.mergedWith && parent.mergedWith.childFreeEnd === 'start') endIsConnected = true;
                            }
                            if (!endIsConnected) tpsInChain.push({ link: chainLink, endpoint: 'end' });
                        });
                        
                        // FIXED: Sort TPs by UL number so TP-1 is always on lowest UL, TP-2 on highest
                        tpsInChain.sort((a, b) => {
                            const ulNumA = parseInt(a.link.id.split('_')[1]) || 0;
                            const ulNumB = parseInt(b.link.id.split('_')[1]) || 0;
                            return ulNumA - ulNumB;
                        });
                        
                        const tpLabels = tpsInChain.map((tp, idx) => {
                            const ulNum = allLinksInChain.findIndex(l => l.id === tp.link.id) + 1;
                            const endpointLabel = tp.endpoint === 'start' ? 'start' : 'end';
                            return `TP-${idx + 1}(U${ulNum}-${endpointLabel})`;
                        }).join(', ');
                        
                        const mpNum = parentLink.mergedWith?.mpNumber || 1;
                        const mpUL = allLinksInChain.findIndex(l => l.id === parentLink.id) + 1;
                        
                        editor.debugger.logInfo(`   📊 Structure: ${chainAnalysis.linkCount} links | ${chainAnalysis.tpCount} TPs | ${chainAnalysis.mpCount} MPs`);
                        editor.debugger.logInfo(`   🔸 TPs: ${tpLabels}`);
                        editor.debugger.logInfo(`   🔸 MPs: MP-${mpNum}(U${mpUL})`);
                        editor.debugger.logInfo(`   📝 Chain: TP--${parentLink.originType || 'UL'}1--🟣--${childLink.originType || 'UL'}2--TP`);
                    }
                    
                    if (connectedDevicesInfo.count > 0) {
                        editor.debugger.logInfo(`   Devices: ${deviceLabels}`);
                    }
                    }
                }
                
                // Force immediate draw to update labels
                editor.draw();
            } else {
                // No UL snap, check for device attachment
                // CRITICAL: MPs (connection points) should NOT stick to devices!
                // Only TPs (free endpoints) can attach to devices
                if (!editor.stretchingConnectionPoint) {
                    // This is a TP - allow device attachment
            let nearbyDevice = null;
            let snapDistance = Infinity;
            let snapAngle = 0;
            
            // ENHANCED: Larger attachment range for easier UL-to-device connection
            editor.objects.forEach(obj => {
                if (obj.type === 'device') {
                    const dx = endpointPos.x - obj.x;
                    const dy = endpointPos.y - obj.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    
                    // ENHANCED: Use device bounds to calculate proper attachment range based on device style
                    const bounds = editor.getDeviceBounds(obj);
                    let attachmentRange;
                    
                    // Calculate attachment range based on device style
                    if (bounds.type === 'circle' || bounds.type === 'hexagon') {
                        // Circular devices: use radius + tolerance
                        attachmentRange = bounds.radius + 20;
                    } else if (bounds.type === 'rectangle' || bounds.type === 'classic') {
                        // Rectangular devices: use diagonal half + tolerance
                        const halfDiagonal = Math.sqrt(bounds.width * bounds.width + bounds.height * bounds.height) / 2;
                        attachmentRange = halfDiagonal + 20;
                    } else {
                        // Fallback: use radius + tolerance
                        attachmentRange = obj.radius + 20;
                    }
                    
                    if (distance <= attachmentRange && distance < snapDistance) {
                        nearbyDevice = obj;
                        snapDistance = distance;
                        snapAngle = Math.atan2(dy, dx);
                    }
                }
            });
            
            if (nearbyDevice) {
                // Attach endpoint to device
                const wasAttached = (editor.stretchingEndpoint === 'start' && editor.stretchingLink.device1) ||
                                   (editor.stretchingEndpoint === 'end' && editor.stretchingLink.device2);
                
                if (editor.stretchingEndpoint === 'start') {
                    editor.stretchingLink.device1 = nearbyDevice.id;
                    // CRITICAL: Store the attachment angle to preserve connection location
                    editor.stretchingLink.device1Angle = snapAngle;
                    // ENHANCED: Smooth snap to device edge (shape-aware)
                    const startSnapPt = editor.getLinkConnectionPoint(nearbyDevice, snapAngle);
                    editor.stretchingLink.start.x = startSnapPt.x;
                    editor.stretchingLink.start.y = startSnapPt.y;
                    
                    // Reduced logging: Angle storage is automatic, don't log it
                    // if (editor.debugger && !wasAttached) {
                    //     const angleDegrees = (snapAngle * 180 / Math.PI).toFixed(1);
                    //     editor.debugger.logInfo(`Attachment angle: ${angleDegrees}deg`);
                    // }
                } else {
                    editor.stretchingLink.device2 = nearbyDevice.id;
                    // CRITICAL: Store the attachment angle to preserve connection location
                    editor.stretchingLink.device2Angle = snapAngle;
                    // ENHANCED: Smooth snap to device edge (shape-aware)
                    const endSnapPt = editor.getLinkConnectionPoint(nearbyDevice, snapAngle);
                    editor.stretchingLink.end.x = endSnapPt.x;
                    editor.stretchingLink.end.y = endSnapPt.y;
                    
                    // Reduced logging: Angle storage is automatic, don't log it
                    // if (editor.debugger && !wasAttached) {
                    //     const angleDegrees = (snapAngle * 180 / Math.PI).toFixed(1);
                    //     editor.debugger.logInfo(`Attachment angle: ${angleDegrees}deg`);
                    // }
                }
                
                // ENHANCED: Recalculate linkIndex after attaching to device
                // This ensures proper offset for multiple links between same devices (QL + UL combined)
                const endpoints = editor.getBULEndpointDevices(editor.stretchingLink);
                if (endpoints.hasEndpoints) {
                    const oldIndex = editor.stretchingLink.linkIndex || 0;
                    const newIndex = editor.calculateLinkIndex(editor.stretchingLink);
                    editor.stretchingLink.linkIndex = newIndex;
                    
                    // CRITICAL: When BOTH ends are attached, recalculate angles to use device-to-device direction
                    // This ensures ULs position correctly like QLs (left/right offset)
                    const dev1 = editor.objects.find(d => d.id === endpoints.device1);
                    const dev2 = editor.objects.find(d => d.id === endpoints.device2);
                    if (dev1 && dev2) {
                        // Calculate base angle from device1 to device2
                        const baseAngle = Math.atan2(dev2.y - dev1.y, dev2.x - dev1.x);
                        
                        // Update stored angles to use device-to-device direction
                        // This overrides the manual snap angle with the proper calculated angle
                        if (editor.stretchingLink.device1 === endpoints.device1) {
                            editor.stretchingLink.device1Angle = baseAngle;
                        } else {
                            editor.stretchingLink.device1Angle = baseAngle + Math.PI;
                        }
                        
                        if (editor.stretchingLink.device2 === endpoints.device2) {
                            editor.stretchingLink.device2Angle = baseAngle + Math.PI;
                        } else {
                            editor.stretchingLink.device2Angle = baseAngle;
                        }
                        
                        // ENHANCED: Immediately update endpoint positions with proper offset (like QL)
                        // Calculate perpendicular offset
                        const sortedIds = [endpoints.device1, endpoints.device2].sort();
                        const isNormalDirection = editor.stretchingLink.device1 === sortedIds[0];
                        let perpAngle = baseAngle + Math.PI / 2;
                        if (!isNormalDirection) {
                            perpAngle += Math.PI;
                        }
                        
                        // Calculate offset amount based on linkIndex
                        let offsetAmount = 0;
                        if (newIndex > 0) {
                            const magnitude = Math.ceil(newIndex / 2) * 20;
                            const direction = (newIndex % 2 === 1) ? 1 : -1;
                            offsetAmount = magnitude * direction;
                        }
                        
                        const offsetX = Math.cos(perpAngle) * offsetAmount;
                        const offsetY = Math.sin(perpAngle) * offsetAmount;
                        
                        // Update start endpoint position (shape-aware)
                        if (editor.stretchingLink.device1) {
                            const actualDev1 = editor.objects.find(d => d.id === editor.stretchingLink.device1);
                            if (actualDev1) {
                                const baseStartPoint = editor.getLinkConnectionPoint(actualDev1, editor.stretchingLink.device1Angle);
                                const targetStartX = baseStartPoint.x + offsetX;
                                const targetStartY = baseStartPoint.y + offsetY;
                                const startDirAngle = Math.atan2(targetStartY - actualDev1.y, targetStartX - actualDev1.x);
                                const startPoint = editor.getLinkConnectionPoint(actualDev1, startDirAngle);
                                editor.stretchingLink.start.x = startPoint.x;
                                editor.stretchingLink.start.y = startPoint.y;
                            }
                        }
                        
                        // Update end endpoint position (shape-aware)
                        if (editor.stretchingLink.device2) {
                            const actualDev2 = editor.objects.find(d => d.id === editor.stretchingLink.device2);
                            if (actualDev2) {
                                const baseEndPoint = editor.getLinkConnectionPoint(actualDev2, editor.stretchingLink.device2Angle);
                                const targetEndX = baseEndPoint.x + offsetX;
                                const targetEndY = baseEndPoint.y + offsetY;
                                const endDirAngle = Math.atan2(targetEndY - actualDev2.y, targetEndX - actualDev2.x);
                                const endPoint = editor.getLinkConnectionPoint(actualDev2, endDirAngle);
                                editor.stretchingLink.end.x = endPoint.x;
                                editor.stretchingLink.end.y = endPoint.y;
                            }
                        }
                    }
                    
                    // Count all links between these devices for context
                    const allLinksBetween = editor.objects.filter(obj => {
                        if (obj.type === 'link' && obj.device1 && obj.device2) {
                            return (obj.device1 === endpoints.device1 && obj.device2 === endpoints.device2) ||
                                   (obj.device1 === endpoints.device2 && obj.device2 === endpoints.device1);
                        }
                        if (obj.type === 'unbound') {
                            const objEnd = editor.getBULEndpointDevices(obj);
                            if (objEnd.hasEndpoints) {
                                return (objEnd.device1 === endpoints.device1 && objEnd.device2 === endpoints.device2) ||
                                       (objEnd.device1 === endpoints.device2 && objEnd.device2 === endpoints.device1);
                            }
                        }
                        return false;
                    });
                    
                    if (editor.debugger) {
                        const position = editor.stretchingLink.linkIndex === 0 ? 'Middle' :
                                       editor.stretchingLink.linkIndex % 2 === 1 ? 'Right' : 'Left';
                        const device1Name = editor.objects.find(d => d.id === endpoints.device1)?.label || endpoints.device1;
                        const device2Name = editor.objects.find(d => d.id === endpoints.device2)?.label || endpoints.device2;
                        
                        editor.debugger.logSuccess(`📊 UL positioned: #${editor.stretchingLink.linkIndex + 1} of ${allLinksBetween.length} (${position} side)`);
                        editor.debugger.logInfo(`   Between: ${device1Name} ↔ ${device2Name}`);
                        editor.debugger.logInfo(`   Link type: ${editor.stretchingLink.originType || 'UL'} | Index: ${editor.stretchingLink.linkIndex}`);
                        
                        // Show breakdown if multiple links
                        if (allLinksBetween.length > 1) {
                            const qlCount = allLinksBetween.filter(l => l.type === 'link').length;
                            const ulCount = allLinksBetween.filter(l => l.type === 'unbound').length;
                            editor.debugger.logInfo(`   Mix: ${qlCount} QL + ${ulCount} UL = ${allLinksBetween.length} total`);
                            
                            // Log all links with their positions for debugging
                            const linkDetails = allLinksBetween.map((l, idx) => {
                                const type = l.type === 'link' ? 'QL' : 'UL';
                                const side = idx === 0 ? 'M' : (idx % 2 === 1 ? 'R' : 'L');
                                return `${type}${idx}(${side})`;
                            }).join(', ');
                            editor.debugger.logInfo(`   Layout: ${linkDetails}`);
                        }
                    }
                }
                
                // DISABLED: No longer convert to regular link - keep as unbound link with TPs
                // This ensures all links always have 2 TPs at their ends
                // if (editor.stretchingLink.device1 && editor.stretchingLink.device2) {
                //     // Conversion logic disabled - links remain as 'unbound' type with start/end TPs
                // }
                
                if (!wasAttached) {
                    // Only log if this is a new attachment (not re-attaching)
                    if (editor.debugger) {
                        // Check if this link is part of a BUL chain and show all connected devices
                        const connectedDevicesInfo = editor.getAllConnectedDevices(editor.stretchingLink);
                        const deviceLabels = connectedDevicesInfo.devices.map(d => d.label || d.id).join(', ');
                        
                        if (connectedDevicesInfo.count > 1) {
                            editor.debugger.logSuccess(`🔗 Connected: ${deviceLabels}`);
                        } else {
                            editor.debugger.logSuccess(`🔗 Attached to ${nearbyDevice.label || nearbyDevice.id}`);
                        }
                        
                        // Show link index if multiple links between same devices
                        if (editor.stretchingLink.linkIndex > 0) {
                            const totalLinks = editor.stretchingLink.linkIndex + 1;
                            editor.debugger.logInfo(`   Position: ${totalLinks}${editor.getOrdinalSuffix(totalLinks)} link between these devices`);
                        }
                    }
                }
                
                // Update link details table if it's open for this link
                if (editor.editingLink && editor.editingLink.id === editor.stretchingLink.id) {
                    editor.showLinkDetails(editor.stretchingLink);
                }
                
                editor.draw();
                }
                } else {
                    // This is an MP (connection point) - don't attach to devices
                    if (editor.debugger) {
                        editor.debugger.logInfo(`🟣 MP is free-floating - does not attach to devices (routing only)`);
                    }
                }
            }
        }
        
        // Clear visual feedback state
        editor._stretchingNearDevice = null;
        editor._stretchingSnapAngle = null;
        
        // TRACKING: Generate final report for UL/BUL stretch operation
        if (editor._bulTrackingData && editor.debugger) {
            const duration = Date.now() - editor._bulTrackingData.startTime;
            const chainSize = editor._bulTrackingData.links.length;
            
            // Calculate total movement and detachments
            let totalMovement = 0;
            let maxJumpPerLink = 0;
            let linkWithMaxJump = null;
            let totalDetachments = 0;
            
            editor._bulTrackingData.links.forEach(trackData => {
                const link = editor.objects.find(l => l.id === trackData.id);
                if (link) {
                    const startMove = Math.sqrt(
                        Math.pow(link.start.x - trackData.startPos.x, 2) + 
                        Math.pow(link.start.y - trackData.startPos.y, 2)
                    );
                    const endMove = Math.sqrt(
                        Math.pow(link.end.x - trackData.endPos.x, 2) + 
                        Math.pow(link.end.y - trackData.endPos.y, 2)
                    );
                    
                    const maxMove = Math.max(startMove, endMove);
                    totalMovement += maxMove;
                    totalDetachments += (trackData.detachments || 0);
                    
                    if (maxMove > maxJumpPerLink) {
                        maxJumpPerLink = maxMove;
                        linkWithMaxJump = trackData.id;
                    }
                }
            });
            
            // Generate report ONLY if there were issues (jumps detected)
            if (editor._bulTrackingData.totalJumps > 0) {
                editor.debugger.logError(`⚠️ UL/BUL STRETCH - BUGS DETECTED`);
                editor.debugger.logError(`   🚨 Total Jumps: ${editor._bulTrackingData.totalJumps}`);
                
                editor.debugger.logInfo(`📊 Debug Info:`);
                editor.debugger.logInfo(`   Duration: ${duration}ms`);
                editor.debugger.logInfo(`   Chain size: ${chainSize} link(s)`);
                editor.debugger.logInfo(`   Max jump: ${maxJumpPerLink.toFixed(1)}px (${linkWithMaxJump})`);
                
                // Per-link breakdown
                editor.debugger.logInfo(`🔍 Per-Link Movement:`);
                editor._bulTrackingData.links.forEach(trackData => {
                    const link = editor.objects.find(l => l.id === trackData.id);
                    if (link) {
                        const startMove = Math.sqrt(
                            Math.pow(link.start.x - trackData.startPos.x, 2) + 
                            Math.pow(link.start.y - trackData.startPos.y, 2)
                        );
                        const endMove = Math.sqrt(
                            Math.pow(link.end.x - trackData.endPos.x, 2) + 
                            Math.pow(link.end.y - trackData.endPos.y, 2)
                        );
                        
                        editor.debugger.logInfo(`   ${trackData.id}: START ${startMove.toFixed(1)}px, END ${endMove.toFixed(1)}px`);
                    }
                });
            }
            // Reduced logging: Don't show success message every time (too verbose)
            
            // Clear tracking data
            editor._bulTrackingData = null;
        }
        
        // CRITICAL: Always clear stretching flags to prevent "sticking"
        // This fixes the issue where MP continues to follow mouse after release
        const wasStretching = editor.stretchingLink !== null;
        const stretchedLink = editor.stretchingLink; // Store reference before clearing for CP update
        const wasPendingStretch = editor._pendingStretch !== null;
        const hadPendingDrag = editor._pendingDrag !== null; // Track if we had pending drag
        // Store pending stretch info before clearing (for link from TP feature)
        const pendingStretchInfo = editor._pendingStretch ? { ...editor._pendingStretch } : null;
        editor._pendingStretchInfo = pendingStretchInfo; // Temporarily store for processing below
        editor.stretchingLink = null;
        editor.stretchingEndpoint = null;
        editor.stretchingConnectionPoint = false; // Clear connection point dragging flag
        editor._pendingStretch = null; // Clear pending stretch (light tap without drag)
        editor._pendingDrag = null; // Clear pending drag (light tap without drag)
        
        // CRITICAL FIX: If we had a pending drag (user clicked on object but released before threshold),
        // clear tap tracking to prevent false double-tap detection
        if (hadPendingDrag) {
            editor.lastTapTime = 0;
            editor._lastTapDevice = null;
            editor._lastTapPos = null;
            editor._lastTapStartTime = 0;
        }
        
        // CRITICAL FIX: Also clear pending stretch if we had one (prevents stuck selection)
        if (wasPendingStretch && !wasStretching) {
            editor.lastTapTime = 0;
            editor._lastTapDevice = null;
            editor._lastTapPos = null;
            editor._lastTapStartTime = 0;
        }
        
        // ENHANCED: If user clicked on a TP without dragging, enter "link from TP" mode
        // This allows creating a new UL from an existing UL's terminal point
        if (wasPendingStretch && !wasStretching) {
            const pendingInfo = editor._pendingStretchInfo;
            if (pendingInfo && !pendingInfo.isConnectionPoint) {
                // Check if this endpoint is really a free TP (not attached to a device AND not connected to another link)
                const link = pendingInfo.link;
                const endpoint = pendingInfo.endpoint;
                
                // CRITICAL FIX: Check BOTH device attachment AND merge connection
                // An endpoint is only a "free TP" if it has no device AND is not connected to another link
                const isStartFree = !link.device1 && !editor.isEndpointConnected(link, 'start');
                const isEndFree = !link.device2 && !editor.isEndpointConnected(link, 'end');
                
                const isFreeTP = (endpoint === 'start' && isStartFree) || (endpoint === 'end' && isEndFree);
                
                // CRITICAL: Only allow link from TP if chain mode is ON
                if (isFreeTP && editor.linkContinuousMode) {
                    // Enter "link from TP" mode
                    editor._linkFromTP = {
                        link: link,
                        endpoint: endpoint,
                        startPos: endpoint === 'start' ? { ...link.start } : { ...link.end }
                    };
                    editor.setMode('link');
                    editor.linking = true;
                    editor.linkStart = null; // Not starting from a device
                    
                    // Keep the BUL chain selected for visual feedback
                    const allMergedLinks = editor.getAllMergedLinks(link);
                    editor.selectedObjects = allMergedLinks;
                    editor.selectedObject = link;
                    
                    if (editor.debugger) {
                        editor.debugger.logSuccess(`🔗 Link from TP: Started from ${link.id} (${endpoint})`);
                        editor.debugger.logInfo(`   Click on a device, grid, or another TP to connect`);
                    }
                    
                    // Show notification to user
                    editor.showNotification('Click to extend chain from TP (ESC to cancel)', 'info');
                    
                    editor.draw();
                    return; // Don't process further
                } else if (isFreeTP && !editor.linkContinuousMode) {
                    // Chain mode OFF - don't enter link from TP mode, just keep selected
                    if (editor.debugger) {
                        editor.debugger.logInfo(`🔗 Chain mode OFF → TP click (enable chain mode to extend)`);
                    }
                    // Show hint to user
                    editor.showNotification('Enable "Chain" mode to extend from TP', 'warning');
                }
            }
        }
        
        // CRITICAL: Clear _pendingStretchInfo after processing
        editor._pendingStretchInfo = null;
        
        // If we were stretching, update all connection points in the chain
        if (wasStretching) {
            editor.updateAllConnectionPoints();
            
            // NOTE: CP shifting is now done REAL-TIME during the stretch via _updateCurvePointsDuringStretch()
            // This prevents visual jumps when releasing the mouse
            // Just do one final update to ensure everything is synced
            if (stretchedLink && editor._stretchOldMidpoints) {
                editor._updateCurvePointsDuringStretch(stretchedLink);
            }
            
            // Clear stored old midpoints
            editor._stretchOldMidpoints = null;
        }
        
        // Reset cursor
        editor.updateCursor();
        if (editor.moveLongPressTimer) {
            clearTimeout(editor.moveLongPressTimer);
            editor.moveLongPressTimer = null;
        }
        
        // CRITICAL: Update PLACEMENT TRACKING on drag release BEFORE clearing flags!
        if (editor.dragging && editor.selectedObject && editor.debugger) {
            // Handle devices/text (have x,y) and unbound links (have start/end) differently
            let objPos, objGrid;
            
            if (editor.selectedObject.x !== undefined && editor.selectedObject.y !== undefined) {
                // Device or text object
                objPos = { x: editor.selectedObject.x, y: editor.selectedObject.y };
                objGrid = editor.worldToGrid(objPos);
            } else if (editor.selectedObject.type === 'unbound') {
                // Unbound link - use center point
                const centerX = (editor.selectedObject.start.x + editor.selectedObject.end.x) / 2;
                const centerY = (editor.selectedObject.start.y + editor.selectedObject.end.y) / 2;
                objPos = { x: centerX, y: centerY };
                objGrid = editor.worldToGrid(objPos);
            }
            
            if (objPos) {
                const clickTrackDiv = document.getElementById('debug-click-track');
                if (clickTrackDiv) {
                    const mousePos = editor.lastMousePos || pos;
                    const mouseGrid = editor.worldToGrid(mousePos);
                    const relativePos = { x: mousePos.x - objPos.x, y: mousePos.y - objPos.y };
                    const relativeMag = Math.sqrt(relativePos.x * relativePos.x + relativePos.y * relativePos.y);
                    const inputSource = editor._lastInputType || 'mouse';
                    const icon = inputSource === 'trackpad' ? '🖐️' : inputSource === 'mouse' ? '🖱️' : '👆';
                    
                    // Update placement data with release information
                    if (editor.debugger.placementData && editor.debugger.placementData.grabPosition) {
                        editor.debugger.placementData.releasePosition = {
                            x: objPos.x,
                            y: objPos.y,
                            gridX: Math.round(objGrid.x),
                            gridY: Math.round(objGrid.y)
                        };
                        editor.debugger.placementData.mouseRelease = { x: mousePos.x, y: mousePos.y };
                        
                        // Calculate distance moved
                        const dx = objPos.x - editor.debugger.placementData.grabPosition.x;
                        const dy = objPos.y - editor.debugger.placementData.grabPosition.y;
                        editor.debugger.placementData.distance = Math.sqrt(dx * dx + dy * dy);
                    }
                
                    const objLabel = editor.selectedObject.label || 
                                     (editor.selectedObject.type === 'unbound' ? 'Unbound Link' : 'Device');
                    
                    clickTrackDiv.innerHTML = `
                        <span style="color: #27ae60; font-weight: bold; font-size: 11px;">${icon} DRAG RELEASED: ${objLabel}</span><br>
                        <span style="color: #0f0; font-size: 10px;">✓ Object still selected - ready for re-grab</span><br>
                        <br>
                        <span style="color: #0ff; font-weight: bold;">📍 FINAL POSITION:</span><br>
                        World: <span style="color: #0ff;">(${objPos.x.toFixed(1)}, ${objPos.y.toFixed(1)})</span><br>
                        Grid: <span style="color: #0ff;">(${Math.round(objGrid.x)}, ${Math.round(objGrid.y)})</span><br>
                        <br>
                        <span style="color: #fa0; font-weight: bold;">🖱️ RELEASE MOUSE POSITION:</span><br>
                        World: <span style="color: #fa0;">(${mousePos.x.toFixed(1)}, ${mousePos.y.toFixed(1)})</span><br>
                        Grid: <span style="color: #fa0;">(${Math.round(mouseGrid.x)}, ${Math.round(mouseGrid.y)})</span><br>
                        <br>
                        <span style="color: #667eea; font-weight: bold;">📏 RELATIVE AT RELEASE:</span><br>
                        Delta: <span style="color: #667eea;">(${relativePos.x.toFixed(1)}, ${relativePos.y.toFixed(1)})</span><br>
                        Distance: <span style="color: #667eea;">${relativeMag.toFixed(1)}px</span><br>
                        <br>
                        <div style="padding: 4px; background: rgba(155, 89, 182, 0.2); border-radius: 3px; border-left: 3px solid #9b59b6; margin-bottom: 6px;">
                            <span style="color: #9b59b6; font-weight: bold;">⏭️ NEXT: Re-Grab Test</span><br>
                            <span style="color: #fff; font-size: 9px;">
                                Click this object again to test re-grab!<br>
                                • Watch for offset changes<br>
                                • Monitor for position jumps<br>
                                • Compare relative position
                            </span>
                        </div>
                        <span style="color: #888; font-size: 9px;">
                            State: RELEASED - STILL SELECTED<br>
                            Type: ${editor.selectedObject.type.toUpperCase()}<br>
                            Input: ${inputSource.toUpperCase()}<br>
                            Code: handleMouseUp()
                        </span>
                    `;
                }
            }
        }
        
        // CRITICAL: Set flag that mouse was released after selection
        // This enables handle operations (resize/rotate) on next click
        if (editor.selectedObject && (editor.selectedObject.type === 'device' || editor.selectedObject.type === 'text' || editor.selectedObject.type === 'shape') && !editor.dragging) {
            // Mouse released without dragging - this completes the selection
            editor.selectedObject._mouseReleasedAfterSelection = true;
            
            if (editor.debugger) {
                const objName = editor.selectedObject.label || editor.selectedObject.text || 'Object';
                editor.debugger.logSuccess(`✓ Mouse released - handles now ENABLED for ${objName}`);
                editor.debugger.logInfo(`   Selection complete - resize/rotate available on next click`);
            }
        }
        
        // CRITICAL: Clear dragging flag and notify debugger
        const wasDragging = editor.dragging;
        editor.dragging = false;
        editor._groupDragDebugLogged = false; // Reset group drag debug flag
        editor._lastMultiDragTime = 0; // Reset multi-drag dedup timer
        
        // CRITICAL FIX: Track when drag ended to prevent accidental double-click LINK mode entry
        if (wasDragging) {
            editor._lastDragEndTime = Date.now();
        }
        
        // CRITICAL: Update all connection points after dragging/moving merged links
        if (wasDragging) {
            editor.updateAllConnectionPoints();
        }
        
        // Reshow selection toolbar after drag ends (for shapes and other objects)
        if (wasDragging && editor.selectedObject) {
            const obj = editor.selectedObject;
            setTimeout(() => {
                // Only show toolbar if still selected and not dragging again
                if (editor.selectedObject === obj && !editor.dragging) {
                    if (obj.type === 'shape') {
                        editor.showShapeSelectionToolbar(obj);
                    } else if (obj.type === 'device') {
                        editor.showDeviceSelectionToolbar(obj);
                    } else if (obj.type === 'text') {
                        // Skip toolbar when TB acts as a curve control point
                        if (!(obj.linkId && obj.position === 'middle' && editor._tbActedAsCP)) {
                            editor.showTextSelectionToolbar(obj);
                        }
                    } else if (obj.type === 'link' || obj.type === 'unbound') {
                        editor.showLinkSelectionToolbar(obj);
                    }
                }
                editor._tbActedAsCP = false;
            }, 50);
        }
        
        // CRITICAL: Clear tap tracking after drag ends to prevent drag-release from being mistaken for double-tap
        // This ensures that only intentional double-taps (not drag-release) can enter link mode
        if (wasDragging) {
            editor.lastTapTime = 0;
            editor._lastTapDevice = null;
            editor._lastTapPos = null;
            editor._lastTapStartTime = 0;
        }
        
        // Clear drag bug buffer on mouse up (prevents spam during drag)
        if (wasDragging && editor.debugger) {
            if (editor.debugger._dragBugBuffer && editor.debugger._dragBugBuffer.length > 1) {
                const bufferedBugs = editor.debugger._dragBugBuffer.length;
                console.log(`✓ Drag complete - suppressed ${bufferedBugs - 1} duplicate bugs during drag`);
                editor.debugger.log(`Drag ended - ${bufferedBugs - 1} duplicate bugs suppressed`, 'info');
            }
            // Clear buffer
            if (editor.debugger._dragBugBuffer) {
                editor.debugger._dragBugBuffer = [];
            }
        }
        
        editor.multiSelectInitialPositions = null;
        editor._initialQuickLinkCPs = null; // Clear QL CP positions
        editor._initialAttachedULCPs = null; // Clear attached UL CP positions
        editor.unboundLinkInitialPos = null; // Clear UL body drag position
        editor._bulChainInitialPositions = null; // Clear BUL chain initial positions
        editor._attachedTBInitialPositions = null; // Clear attached TB initial positions
        editor._tbInitialPositions = null; // Clear TB initial positions (fallback)
        editor._onLineTextDragStart = null; // Clear on-line text drag state
        editor._attachedTextDragStart = null; // Clear attached text drag state
        
        // FINALIZE TB CURVE DRAG: Clean up temporary control point
        if (editor._tbCurveDragStart && editor.selectedObject && editor.selectedObject.type === 'text') {
            const textObj = editor.selectedObject;
            const link = editor.objects.find(obj => obj.id === textObj.linkId);
            if (link && link.manualControlPoint) {
                // Clear temporary preview point (manualCurvePoint is the permanent one)
                delete link.manualControlPoint;
                editor.scheduleAutoSave();
            }
        }
        editor._tbCurveDragStart = null; // Clear TB curve drag state (middle-attached text curving)
        
        // TEXT-TO-LINK SNAP: If text was being dragged and has a snap preview, attach it
        if (wasDragging && editor.selectedObject && editor.selectedObject.type === 'text' && editor._textSnapPreview) {
            const snap = editor._textSnapPreview;
            editor.attachTextToLink(editor.selectedObject, snap.link, snap.t);
            
            // After attaching, transition to base mode for seamless experience
            if (editor.currentMode === 'text') {
                editor.setMode('base');
                editor.selectedObject = editor.selectedObject; // Keep text selected
                editor.selectedObjects = [editor.selectedObject];
            }
        }
        editor._textSnapPreview = null;
        editor._alignGuides = null;
        
        // ENHANCED: Keep text selection toolbar visible after dragging a text box
        // But skip when TB acts as a curve control point (CP behavior = no toolbar)
        if (wasDragging && editor.selectedObject && editor.selectedObject.type === 'text') {
            const tb = editor.selectedObject;
            const isActingAsCP = tb.linkId && tb.position === 'middle' && editor._tbActedAsCP;
            if (!isActingAsCP) {
                editor.updateTextSelectionToolbarPosition();
                if (!editor._textSelectionToolbar) {
                    editor.showTextSelectionToolbar(tb);
                }
            }
        }
        
        // ENHANCED: Re-show device toolbar after dragging a device
        if (wasDragging && editor.selectedObject && editor.selectedObject.type === 'device') {
            // Re-show toolbar at new position (below device)
            editor.showDeviceSelectionToolbar(editor.selectedObject);
        }
        
        // ENHANCED: Re-show link toolbar after dragging a link
        if (wasDragging && editor.selectedObject && (editor.selectedObject.type === 'link' || editor.selectedObject.type === 'unbound')) {
            // Re-show toolbar at link center (no click position available after drag)
            editor.showLinkSelectionToolbar(editor.selectedObject);
        }
        
        editor.textDragInitialPos = null; // Clear text drag position
        editor.deviceDragInitialPos = null; // Clear device drag position
        editor.shapeDragInitialPos = null; // Clear shape drag position
        editor.dragStartPos = null; // Clear starting position for tap vs drag detection
        editor.lastMousePos = null; // Clear last mouse position
        editor._unboundLinkMoveLogged = false; // Reset UL move log flag
        editor._unboundBodyDragLogged = false; // Reset UL body drag log flag
        editor.lastDragPos = null; // Clear drag position tracking
        editor._jumpDetectedThisDrag = false; // Reset jump detection flag for next drag
        editor.lastDragTime = null;
        if (editor.currentTool !== 'link') {
            editor.linking = false;
            editor.linkStart = null;
        }

        // If we temporarily exited placement to drag the newly placed device,
        // restore device placement mode after releasing the mouse
        if (editor.tempPlacementResumeType) {
            editor.setDevicePlacementMode(editor.tempPlacementResumeType);
            editor.tempPlacementResumeType = null;
        }
    },
};

console.log('[topology-mouse-up.js] MouseUpHandler loaded');
