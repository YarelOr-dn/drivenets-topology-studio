/**
 * topology-draw.js - Main Draw Function Module
 * 
 * Contains the main draw() function that renders the entire canvas
 */

'use strict';

window.DrawModule = {
    scheduleDraw(editor) {
        if (editor._drawRafId) return;
        editor._drawRafId = requestAnimationFrame(() => {
            editor._drawRafId = null;
            this.draw(editor);
        });
    },

    draw(editor) {
        // ENHANCED: Hide text toolbar while object is sliding (momentum active)
        // Show again when slide ends
        if (editor._textSelectionToolbar && editor._textSelectionToolbarTarget) {
            const textObj = editor._textSelectionToolbarTarget;
            const isSliding = editor.momentum && editor.momentum.activeSlides && editor.momentum.activeSlides.has(textObj.id);
            
            if (isSliding || editor.dragging) {
                // Hide toolbar during slide/drag - smooth fade out
                editor._textSelectionToolbar.style.opacity = '0';
                editor._textSelectionToolbar.style.pointerEvents = 'none';
            } else {
                // Show toolbar when not sliding - smooth fade in
                editor._textSelectionToolbar.style.opacity = '1';
                editor._textSelectionToolbar.style.pointerEvents = 'auto';
            }
        }
        
        // Update text selection toolbar position if visible (follows pan/zoom)
        editor.updateTextSelectionToolbarPosition();
        // Update inline text editor position if active (follows pan/zoom)
        editor.updateInlineTextEditorPosition();
        // Update inline device rename position if active (follows pan/zoom)
        editor.updateInlineDeviceRenamePosition();
        
        // HiDPI: Apply device pixel ratio for crisp rendering
        const dpr = editor.dpr || 1;
        editor.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        
        editor.ctx.imageSmoothingEnabled = true;
        editor.ctx.imageSmoothingQuality = 'high';
        
        // Clear with appropriate background color (logical dimensions)
        const cw = editor.canvasW || editor.canvas.width;
        const ch = editor.canvasH || editor.canvas.height;
        if (editor.darkMode) {
            editor.ctx.fillStyle = '#1a1a1a';
            editor.ctx.fillRect(0, 0, cw, ch);
        } else {
            editor.ctx.clearRect(0, 0, cw, ch);
        }
        
        // Draw grid before transformations (if enabled)
        // MIGRATED: Use DrawingManager.drawGrid() if available
        if (editor.gridZoomEnabled) {
            if (editor.drawing && typeof editor.drawing.drawGrid === 'function') {
                editor.drawing.drawGrid();
            } else {
                editor.drawGrid(); // Fallback to local method
            }
        }
        
        editor.ctx.save();
        // ULTRA: Translate to half-pixel boundaries for sharper rendering
        editor.ctx.translate(Math.round(editor.panOffset.x) + 0.5, Math.round(editor.panOffset.y) + 0.5);
        editor.ctx.scale(editor.zoom, editor.zoom);
        
        // Enable anti-aliasing for smooth circles and lines
        editor.ctx.lineJoin = 'round';
        editor.ctx.lineCap = 'round';
        
        // Skip expensive O(n^2) position recalc during pure viewport changes (zoom/pan).
        // World positions don't move -- only the view transform changes.
        const skipPositionUpdate = !!editor._viewportOnly;
        editor._viewportOnly = false;

        if (!skipPositionUpdate)
        editor.objects.forEach(obj => {
            // Skip if this is the link currently being stretched (let handleMouseMove control it)
            if (editor.stretchingLink && obj.id === editor.stretchingLink.id) {
                return; // Don't recalculate position while user is dragging
            }
            
            if (obj.type === 'unbound' && (obj.device1 || obj.device2)) {
                // CRITICAL: Check if this is a STANDALONE UL (SUL) with BOTH endpoints attached to devices
                // SULs should behave EXACTLY like Quick Links (QLs) - dynamic positioning every frame
                const isSUL = !obj.mergedWith && !obj.mergedInto; // Not part of BUL chain
                const hasBothDevices = obj.device1 && obj.device2;
                
                if (isSUL && hasBothDevices) {
                    // ===== SUL WITH BOTH DEVICES: USE EXACT QL LOGIC =====
                    const device1 = editor.objects.find(o => o.id === obj.device1);
                    const device2 = editor.objects.find(o => o.id === obj.device2);
                    
                    if (device1 && device2) {
                        // Calculate connection points - EXACTLY like drawLink()
                        const angle = Math.atan2(device2.y - device1.y, device2.x - device1.x);
                        
                        // DYNAMIC link index calculation - count ALL links between these devices
                        // CRITICAL: Must include QL, SUL, AND BUL chains for seamless integration
                        const connectedLinks = editor.objects.filter(o => {
                            // Quick Links (type: 'link')
                            if (o.type === 'link' && o.device1 && o.device2) {
                                return (o.device1 === device1.id && o.device2 === device2.id) ||
                                       (o.device1 === device2.id && o.device2 === device1.id);
                            }
                            
                            // Standalone Unbound Links (SUL) - direct device attachment
                            if (o.type === 'unbound' && o.device1 && o.device2) {
                                return (o.device1 === device1.id && o.device2 === device2.id) ||
                                       (o.device1 === device2.id && o.device2 === device1.id);
                            }
                            
                            // BUL chains with endpoints attached to devices
                            if (o.type === 'unbound' && (o.mergedWith || o.mergedInto)) {
                                const oEndpoints = editor.getBULEndpointDevices(o);
                                if (!oEndpoints.hasEndpoints) return false;
                                return (oEndpoints.device1 === device1.id && oEndpoints.device2 === device2.id) ||
                                       (oEndpoints.device1 === device2.id && oEndpoints.device2 === device1.id);
                            }
                            
                            return false;
                        }).sort((a, b) => {
                            const idA = parseInt(a.id.split('_')[1]) || 0;
                            const idB = parseInt(b.id.split('_')[1]) || 0;
                            return idA - idB;
                        });
                        
                        const linkIndex = connectedLinks.findIndex(l => l.id === obj.id);
                        obj.linkIndex = linkIndex >= 0 ? linkIndex : 0;
                        
                        // NORMALIZE perpendicular direction - EXACTLY like drawLink()
                        const sortedIds = [obj.device1, obj.device2].sort();
                        const isNormalDirection = obj.device1 === sortedIds[0];
                        
                        // Calculate offset - First (0) = Middle, Second (1) = Right, Third (2) = Left
                        let offsetAmount = 0;
                        if (linkIndex > 0) {
                            const magnitude = Math.ceil(linkIndex / 2) * 20;
                            const direction = (linkIndex % 2 === 1) ? 1 : -1;
                            offsetAmount = magnitude * direction;
                        }
                        
                        // Calculate perpendicular offset - EXACTLY like drawLink()
                        let perpAngle = angle + Math.PI / 2;
                        if (!isNormalDirection) {
                            perpAngle += Math.PI;
                        }
                        
                        const offsetX = Math.cos(perpAngle) * offsetAmount;
                        const offsetY = Math.sin(perpAngle) * offsetAmount;
                        
                        // Calculate base touch points (centered line) - shape-aware
                        const baseStartPt = editor.getLinkConnectionPoint(device1, angle);
                        const baseEndPt = editor.getLinkConnectionPoint(device2, angle + Math.PI);
                        
                        // Apply offset to create target line
                        const targetStartX = baseStartPt.x + offsetX;
                        const targetStartY = baseStartPt.y + offsetY;
                        const targetEndX = baseEndPt.x + offsetX;
                        const targetEndY = baseEndPt.y + offsetY;
                        
                        // Calculate direction from device centers to offset target points
                        const startDirAngle = Math.atan2(targetStartY - device1.y, targetStartX - device1.x);
                        const endDirAngle = Math.atan2(targetEndY - device2.y, targetEndX - device2.x);
                        
                        // Final touch points on device edges - shape-aware
                        const finalStartPt = editor.getLinkConnectionPoint(device1, startDirAngle);
                        const finalEndPt = editor.getLinkConnectionPoint(device2, endDirAngle);
                        obj.start = { 
                            x: finalStartPt.x, 
                            y: finalStartPt.y 
                        };
                        obj.end = { 
                            x: finalEndPt.x, 
                            y: finalEndPt.y 
                        };
                    }
                    
                    // Skip the rest of the loop for this SUL - we've handled it completely
                    return;
                }
                
                // ===== BUL or PARTIALLY ATTACHED UL: Use existing logic =====
                // Get endpoint devices for offset calculation
                const endpoints = editor.getBULEndpointDevices(obj);
                let baseAngle = null;
                let offsetAmount = 0;
                
                // Calculate offset if both endpoints are attached to devices
                if (endpoints.hasEndpoints && endpoints.device1 && endpoints.device2) {
                    const device1 = editor.objects.find(o => o.id === endpoints.device1);
                    const device2 = editor.objects.find(o => o.id === endpoints.device2);
                    
                    if (device1 && device2) {
                        // Base angle between the two endpoint devices
                        baseAngle = Math.atan2(device2.y - device1.y, device2.x - device1.x);
                        
                        // Calculate offset based on linkIndex
                        // User requested logic: First (0) = Middle, Second (1) = Right (+), Third (2) = Left (-)
                        const linkIndex = editor.calculateLinkIndex(obj);
                        if (linkIndex > 0) {
                            const magnitude = Math.ceil(linkIndex / 2) * 20;
                            const direction = (linkIndex % 2 === 1) ? 1 : -1; // Odd = Right (+), Even = Left (-)
                            offsetAmount = magnitude * direction;
                        }
                        
                        // Store linkIndex on the object for reference (don't log every frame)
                        if (obj.linkIndex !== linkIndex) {
                            obj.linkIndex = linkIndex;
                        }
                    }
                }
                
                // Update start TP if attached to device1
                if (obj.device1) {
                const device1 = editor.objects.find(o => o.id === obj.device1);
                    if (device1) {
                        let angle = baseAngle;
                        
                        // If no baseAngle (not both ends attached), calculate dynamically
                        if (angle === null) {
                            // Check if this is a SUL (standalone) with only one end attached
                            const isSULSingleEnd = !obj.mergedWith && !obj.mergedInto && !obj.device2;
                            
                            if (isSULSingleEnd) {
                                // SUL with single end: Always point toward the FREE endpoint (like QL behavior)
                                // This makes the attached end dynamically rotate around the device edge
                                angle = Math.atan2(obj.end.y - device1.y, obj.end.x - device1.x);
                            } else if (obj.device1Angle !== undefined) {
                                // BUL: Use stored attachment angle if available
                                    angle = obj.device1Angle;
                                } else {
                                    // Fallback: calculate to other end or connected device
                            let targetPoint = obj.end;
                            if (obj.mergedWith || obj.mergedInto) {
                                const connectedDevices = editor.getAllConnectedDevices(obj);
                                const otherDeviceId = connectedDevices.deviceIds.find(id => id !== obj.device1);
                                if (otherDeviceId) {
                                    const otherDevice = editor.objects.find(o => o.id === otherDeviceId);
                                    if (otherDevice) {
                                        targetPoint = { x: otherDevice.x, y: otherDevice.y };
                                    }
                                }
                            }
                            angle = Math.atan2(targetPoint.y - device1.y, targetPoint.x - device1.x);
                            }
                        }
                        
                        // Calculate base position on device edge (shape-aware)
                        const baseStartPt = editor.getLinkConnectionPoint(device1, angle);
                        
                        // ENHANCED: Apply perpendicular offset SAME AS QUICK LINKS
                        let targetX = baseStartPt.x;
                        let targetY = baseStartPt.y;
                        
                        if (baseAngle !== null) {
                            // Both ends attached - use EXACT same offset logic as QLs in drawLink()
                            const sortedIds = [endpoints.device1, endpoints.device2].sort();
                            // CRITICAL: Use the LINK's actual device1, not the sorted endpoint
                            const isNormalDirection = obj.device1 === sortedIds[0];
                            // CRITICAL: Use baseAngle for perpendicular, NOT the current angle
                            let perpAngle = baseAngle + Math.PI / 2;
                            if (!isNormalDirection) {
                                perpAngle += Math.PI;
                            }
                            
                            const offsetX = Math.cos(perpAngle) * offsetAmount;
                            const offsetY = Math.sin(perpAngle) * offsetAmount;
                            
                            // Create offset target point
                            const targetStartX = baseStartPt.x + offsetX;
                            const targetStartY = baseStartPt.y + offsetY;
                            
                            // Calculate direction from device center to offset target point
                            const startDirAngle = Math.atan2(targetStartY - device1.y, targetStartX - device1.x);
                            
                            // Final touch point on device edge along this direction (shape-aware)
                            const finalStartPt = editor.getLinkConnectionPoint(device1, startDirAngle);
                            targetX = finalStartPt.x;
                            targetY = finalStartPt.y;
                        }
                        
                        // SMOOTH MOVEMENT: Use lerp for Arrow-style ULs for smoother animation
                        const linkStyle = obj.style !== undefined ? obj.style : 'solid';
                        if ((linkStyle === 'arrow' || linkStyle === 'double-arrow' || linkStyle === 'dashed-arrow' || linkStyle === 'dashed-double-arrow') && obj.start) {
                            obj._targetStart = { x: targetX, y: targetY }; // Store target for animation loop
                            obj.start = editor.lerpPoint(obj.start, { x: targetX, y: targetY }, 0.2);
                        } else {
                            obj.start = { x: targetX, y: targetY };
                        }
                        
                        // If this is the connected end in a merge, update the MP position
                        if (obj.mergedWith && obj.mergedWith.parentFreeEnd !== 'start') {
                            obj.mergedWith.connectionPoint.x = obj.start.x;
                            obj.mergedWith.connectionPoint.y = obj.start.y;
                            
                            // Also update child's connection point
                            const childLink = editor.objects.find(o => o.id === obj.mergedWith.linkId);
                            if (childLink && childLink.mergedInto) {
                                childLink.mergedInto.connectionPoint.x = obj.start.x;
                                childLink.mergedInto.connectionPoint.y = obj.start.y;
                            }
                        }
                        if (obj.mergedInto) {
                            const parentLink = editor.objects.find(o => o.id === obj.mergedInto.parentId);
                            if (parentLink && parentLink.mergedWith && parentLink.mergedWith.childFreeEnd !== 'start') {
                                obj.mergedInto.connectionPoint.x = obj.start.x;
                                obj.mergedInto.connectionPoint.y = obj.start.y;
                                parentLink.mergedWith.connectionPoint.x = obj.start.x;
                                parentLink.mergedWith.connectionPoint.y = obj.start.y;
                            }
                        }
                    }
                }
                
                // Update end TP if attached to device2
                if (obj.device2) {
                const device2 = editor.objects.find(o => o.id === obj.device2);
                    if (device2) {
                        let angle = baseAngle !== null ? baseAngle + Math.PI : null; // Opposite direction
                        
                        // If no baseAngle (not both ends attached), calculate dynamically
                        if (angle === null) {
                            // Check if this is a SUL (standalone) with only one end attached
                            const isSULSingleEnd = !obj.mergedWith && !obj.mergedInto && !obj.device1;
                            
                            if (isSULSingleEnd) {
                                // SUL with single end: Always point toward the FREE endpoint (like QL behavior)
                                // This makes the attached end dynamically rotate around the device edge
                                angle = Math.atan2(obj.start.y - device2.y, obj.start.x - device2.x);
                            } else if (obj.device2Angle !== undefined) {
                                // BUL: Use stored attachment angle if available
                                    angle = obj.device2Angle;
                                } else {
                                    // Fallback: calculate to other end or connected device
                            let targetPoint = obj.start;
                            if (obj.mergedWith || obj.mergedInto) {
                                const connectedDevices = editor.getAllConnectedDevices(obj);
                                const otherDeviceId = connectedDevices.deviceIds.find(id => id !== obj.device2);
                                if (otherDeviceId) {
                                    const otherDevice = editor.objects.find(o => o.id === otherDeviceId);
                                    if (otherDevice) {
                                        targetPoint = { x: otherDevice.x, y: otherDevice.y };
                                    }
                                }
                            }
                                angle = Math.atan2(targetPoint.y - device2.y, targetPoint.x - device2.x);
                            }
                        }
                        
                        // Calculate base position on device edge (shape-aware)
                        const baseEndPt = editor.getLinkConnectionPoint(device2, angle);
                        
                        // ENHANCED: Apply perpendicular offset SAME AS QUICK LINKS
                        let targetX = baseEndPt.x;
                        let targetY = baseEndPt.y;
                        
                        if (baseAngle !== null) {
                            // Both ends attached - use EXACT same offset logic as QLs in drawLink()
                            const sortedIds = [endpoints.device1, endpoints.device2].sort();
                            // CRITICAL: Use the LINK's actual device1 for consistent direction check
                            const isNormalDirection = obj.device1 === sortedIds[0];
                            // CRITICAL: Use baseAngle for perpendicular, NOT the current angle
                            let perpAngle = baseAngle + Math.PI / 2;
                            if (!isNormalDirection) {
                                perpAngle += Math.PI;
                            }
                            
                            const offsetX = Math.cos(perpAngle) * offsetAmount;
                            const offsetY = Math.sin(perpAngle) * offsetAmount;
                            
                            // Create offset target point
                            const targetEndX = baseEndPt.x + offsetX;
                            const targetEndY = baseEndPt.y + offsetY;
                            
                            // Calculate direction from device center to offset target point
                            const endDirAngle = Math.atan2(targetEndY - device2.y, targetEndX - device2.x);
                            
                            // Final touch point on device edge along this direction (shape-aware)
                            const finalEndPt = editor.getLinkConnectionPoint(device2, endDirAngle);
                            targetX = finalEndPt.x;
                            targetY = finalEndPt.y;
                        }
                        
                        // SMOOTH MOVEMENT: Use lerp for Arrow-style ULs for smoother animation
                        const linkStyleEnd = obj.style !== undefined ? obj.style : 'solid';
                        if ((linkStyleEnd === 'arrow' || linkStyleEnd === 'double-arrow') && obj.end) {
                            obj._targetEnd = { x: targetX, y: targetY }; // Store target for animation loop
                            obj.end = editor.lerpPoint(obj.end, { x: targetX, y: targetY }, 0.2);
                        } else {
                            obj.end = { x: targetX, y: targetY };
                        }
                        
                        // If this is the connected end in a merge, update the MP position
                        if (obj.mergedWith && obj.mergedWith.parentFreeEnd !== 'end') {
                            obj.mergedWith.connectionPoint.x = obj.end.x;
                            obj.mergedWith.connectionPoint.y = obj.end.y;
                            
                            // Also update child's connection point
                            const childLink = editor.objects.find(o => o.id === obj.mergedWith.linkId);
                            if (childLink && childLink.mergedInto) {
                                childLink.mergedInto.connectionPoint.x = obj.end.x;
                                childLink.mergedInto.connectionPoint.y = obj.end.y;
                            }
                        }
                        if (obj.mergedInto) {
                            const parentLink = editor.objects.find(o => o.id === obj.mergedInto.parentId);
                            if (parentLink && parentLink.mergedWith && parentLink.mergedWith.childFreeEnd !== 'end') {
                                obj.mergedInto.connectionPoint.x = obj.end.x;
                                obj.mergedInto.connectionPoint.y = obj.end.y;
                                parentLink.mergedWith.connectionPoint.x = obj.end.x;
                                parentLink.mergedWith.connectionPoint.y = obj.end.y;
                            }
                        }
                    }
                }
            }
        });
        
        if (!skipPositionUpdate)
        editor.objects.forEach(obj => {
            if (obj.type === 'text' && obj.linkId && obj.position) {
                editor.updateAdjacentTextPosition(obj);
            }
        });
        
        // LAYER-AWARE DRAWING: Sort objects by layer for proper visual ordering
        // Objects with higher layer values are drawn LAST (appear on top)
        // MERGED SHAPES: Always drawn FIRST (lowest layer) - they are grid overlays
        const sortedObjects = [...editor.objects].sort((a, b) => {
            // Merged-to-background shapes are ALWAYS drawn first (act as grid design)
            const aMerged = a.type === 'shape' && a.mergedToBackground;
            const bMerged = b.type === 'shape' && b.mergedToBackground;
            if (aMerged && !bMerged) return -1;  // a (merged) goes first
            if (bMerged && !aMerged) return 1;   // b (merged) goes first
            
            const layerA = editor.getObjectLayer(a);
            const layerB = editor.getObjectLayer(b);
            if (layerA !== layerB) {
                return layerA - layerB; // Lower layers first
            }
            // Within same layer, maintain type order: shapes < links < devices < text
            const typeOrder = { 'shape': -1, 'link': 0, 'unbound': 0, 'device': 1, 'text': 2 };
            return (typeOrder[a.type] || 0) - (typeOrder[b.type] || 0);
        });
        
        // LAYER-AWARE DRAWING: Draw all objects in TRUE layer order
        // Objects are sorted by layer, then by type within same layer
        // This ensures a device on layer 5 appears ABOVE a link on layer 3
        // NOTE: Text gaps in links are created using canvas clipping in drawLink/drawUnboundLink
        sortedObjects.forEach(obj => {
            // Skip hidden objects (hidden by BD visibility toggle)
            if (obj._hidden) return;
            
            if (obj.type === 'link' || obj.type === 'unbound') {
                editor.drawLink(obj);
            } else if (obj.type === 'device') {
                editor.drawDevice(obj, false, true); // skipLabel=true - draw shape only
            } else if (obj.type === 'text') {
                // Skip link-attached text if global toggle is OFF
                if (obj.linkId && !editor.showLinkAttachments) {
                    return; // Skip drawing this attached text
                }
                editor.drawText(obj);
            } else if (obj.type === 'shape') {
                editor.drawShape(obj);
            }
        });
        
        // DEVICE LABELS PASS: Draw device labels so they appear ON TOP of links
        // This ensures device names are never obscured by links passing over them
        sortedObjects.forEach(obj => {
            if (obj._hidden) return;
            if (obj.type === 'device') {
                editor.drawDeviceLabel(obj);
            }
        });
        
        // ARROW TIPS PASS: Draw link arrowheads AFTER devices so they appear ON TOP
        // Arrowheads at device edges must be visible, not hidden behind the device fill
        sortedObjects.forEach(obj => {
            if (obj._hidden) return;
            if ((obj.type === 'link' || obj.type === 'unbound') && (obj._arrowAtEnd || obj._arrowAtStart)) {
                editor.drawLinkArrows(obj);
            }
        });
        
        // ═══════════════════════════════════════════════════════════════════════════
        // SSH TERMINAL BUTTONS PASS: Draw LAST so they appear ON TOP of EVERYTHING
        // ═══════════════════════════════════════════════════════════════════════════
        // This includes text blocks, labels, and any other objects
        // SSH buttons must be visually on top AND have highest click priority
        sortedObjects.forEach(obj => {
            if (obj._hidden) return;
            if (obj.type === 'device') {
                // Draw terminal button if device is selected and has SSH config
                if (window.CanvasDrawing && window.CanvasDrawing.drawTerminalButton) {
                    window.CanvasDrawing.drawTerminalButton(editor, obj);
                }
            }
        });
        
        // MISMATCH BADGES PASS: Draw ABOVE everything else so alerts stand out
        if (window.CanvasDrawing && window.CanvasDrawing.drawDeviceBadges) {
            window.CanvasDrawing.drawDeviceBadges(editor);
        }
        
        // ALIGNMENT GUIDES: thin lines when a device aligns with others
        if (editor._alignGuides && editor.dragging && editor.selectedObject) {
            const ag = editor._alignGuides;
            editor.ctx.save();
            editor.ctx.strokeStyle = 'rgba(52, 152, 219, 0.55)';
            editor.ctx.lineWidth = 1 / editor.zoom;
            editor.ctx.setLineDash([6 / editor.zoom, 4 / editor.zoom]);
            
            // Determine visible canvas bounds in world coords
            const vl = -editor.panOffset.x / editor.zoom;
            const vr = vl + editor.canvasW / editor.zoom;
            const vt = -editor.panOffset.y / editor.zoom;
            const vb = vt + editor.canvasH / editor.zoom;
            
            if (ag.x !== null) {
                editor.ctx.beginPath();
                editor.ctx.moveTo(ag.x, vt);
                editor.ctx.lineTo(ag.x, vb);
                editor.ctx.stroke();
            }
            if (ag.y !== null) {
                editor.ctx.beginPath();
                editor.ctx.moveTo(vl, ag.y);
                editor.ctx.lineTo(vr, ag.y);
                editor.ctx.stroke();
            }
            editor.ctx.setLineDash([]);
            editor.ctx.restore();
        }
        
        // TEXT-TO-LINK SNAP PREVIEW: Professional orange indicator when dragging text near a link
        if (editor._textSnapPreview && editor.dragging && editor.selectedObject && editor.selectedObject.type === 'text') {
            const snap = editor._textSnapPreview;
            const point = snap.point;
            const orangeColor = '#FF7A33';
            const orangeGlow = 'rgba(255, 94, 31, 0.4)';
            const orangeLight = 'rgba(255, 94, 31, 0.15)';
            
            editor.ctx.save();
            
            // Draw elegant connection line from text to snap point
            // Gradient line effect
            const gradient = editor.ctx.createLinearGradient(
                editor.selectedObject.x, editor.selectedObject.y, 
                point.x, point.y
            );
            gradient.addColorStop(0, 'rgba(255, 94, 31, 0.3)');
            gradient.addColorStop(0.5, orangeColor);
            gradient.addColorStop(1, orangeColor);
            
            editor.ctx.strokeStyle = gradient;
            editor.ctx.lineWidth = 2.5 / editor.zoom;
            editor.ctx.setLineDash([6 / editor.zoom, 4 / editor.zoom]);
            editor.ctx.lineCap = 'round';
            editor.ctx.beginPath();
            editor.ctx.moveTo(editor.selectedObject.x, editor.selectedObject.y);
            editor.ctx.lineTo(point.x, point.y);
            editor.ctx.stroke();
            editor.ctx.setLineDash([]);
            
            // Draw snap point indicator with professional pulsing effect
            const time = Date.now() / 200;
            const pulseScale = 1 + Math.sin(time) * 0.15;
            const baseSize = 10 / editor.zoom;
            const pulseSize = baseSize * pulseScale;
            
            // Outer soft glow (largest)
            editor.ctx.beginPath();
            editor.ctx.arc(point.x, point.y, pulseSize + 8 / editor.zoom, 0, Math.PI * 2);
            editor.ctx.fillStyle = orangeLight;
            editor.ctx.fill();
            
            // Middle glow ring
            editor.ctx.beginPath();
            editor.ctx.arc(point.x, point.y, pulseSize + 4 / editor.zoom, 0, Math.PI * 2);
            editor.ctx.fillStyle = orangeGlow;
            editor.ctx.fill();
            
            // Inner solid circle with white border
            editor.ctx.beginPath();
            editor.ctx.arc(point.x, point.y, pulseSize, 0, Math.PI * 2);
            editor.ctx.fillStyle = orangeColor;
            editor.ctx.fill();
            editor.ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
            editor.ctx.lineWidth = 2.5 / editor.zoom;
            editor.ctx.stroke();
            
            // Center dot (white)
            editor.ctx.beginPath();
            editor.ctx.arc(point.x, point.y, 3 / editor.zoom, 0, Math.PI * 2);
            editor.ctx.fillStyle = 'white';
            editor.ctx.fill();
            
            // Professional position label with background
            // Only show CENTER label for middle zone, otherwise just "ATTACH"
            let labelText;
            if (snap.position === 'middle') {
                labelText = '⚡ ATTACH: CENTER';
            } else if (snap.position === 'device1') {
                labelText = '⚡ ATTACH: LEFT';
            } else if (snap.position === 'device2') {
                labelText = '⚡ ATTACH: RIGHT';
            } else {
                // 'custom' position - just say attach
                labelText = '⚡ ATTACH TO LINK';
            }
            const fontSize = 11 / editor.zoom;
            editor.ctx.font = `600 ${fontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Arial`;
            
            const textMetrics = editor.ctx.measureText(labelText);
            const labelPadX = 8 / editor.zoom;
            const labelPadY = 4 / editor.zoom;
            const labelWidth = textMetrics.width + labelPadX * 2;
            const labelHeight = fontSize + labelPadY * 2;
            const labelX = point.x - labelWidth / 2;
            const labelY = point.y - pulseSize - 16 / editor.zoom - labelHeight;
            
            // Label background with rounded corners
            editor.ctx.beginPath();
            const cornerRadius = 4 / editor.zoom;
            editor.ctx.roundRect(labelX, labelY, labelWidth, labelHeight, cornerRadius);
            editor.ctx.fillStyle = orangeColor;
            editor.ctx.fill();
            editor.ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
            editor.ctx.lineWidth = 1 / editor.zoom;
            editor.ctx.stroke();
            
            // Label text
            editor.ctx.fillStyle = 'white';
            editor.ctx.textAlign = 'center';
            editor.ctx.textBaseline = 'middle';
            editor.ctx.fillText(labelText, point.x, labelY + labelHeight / 2);
            
            editor.ctx.restore();
            
            // Request redraw for smooth animation
            if (!editor._snapAnimationFrame) {
                editor._snapAnimationFrame = requestAnimationFrame(() => {
                    editor._snapAnimationFrame = null;
                    if (editor._textSnapPreview) editor.draw();
                });
            }
        }
        
        // Draw marquee selection rectangle with visual feedback
        if (editor.marqueeActive && editor.selectionRectangle) {
            // CS-MS MODE: Professional style paste selection using copied style color
            if (editor.csmsMode) {
                const rect = editor.selectionRectangle;
                const radius = 6 / editor.zoom; // Rounded corners
                
                editor.ctx.save();
                
                // Get the copied style color - use it for the selection UI
                const styleColor = editor.copiedStyle?.color || '#3b82f6';
                
                // Parse color to RGB for transparency variations
                const parseColor = (color) => {
                    if (color.startsWith('#')) {
                        const hex = color.slice(1);
                        const r = parseInt(hex.slice(0, 2), 16);
                        const g = parseInt(hex.slice(2, 4), 16);
                        const b = parseInt(hex.slice(4, 6), 16);
                        return { r, g, b };
                    }
                    // Default to blue if parsing fails
                    return { r: 59, g: 130, b: 246 };
                };
                
                const rgb = parseColor(styleColor);
                
                // Helper function for rounded rectangle path
                const roundedRectPath = (x, y, w, h, r) => {
                    r = Math.min(r, w / 2, h / 2);
                    editor.ctx.beginPath();
                    editor.ctx.moveTo(x + r, y);
                    editor.ctx.lineTo(x + w - r, y);
                    editor.ctx.quadraticCurveTo(x + w, y, x + w, y + r);
                    editor.ctx.lineTo(x + w, y + h - r);
                    editor.ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
                    editor.ctx.lineTo(x + r, y + h);
                    editor.ctx.quadraticCurveTo(x, y + h, x, y + h - r);
                    editor.ctx.lineTo(x, y + r);
                    editor.ctx.quadraticCurveTo(x, y, x + r, y);
                    editor.ctx.closePath();
                };
                
                // Subtle animated pulse effect
                const pulse = 0.7 + 0.3 * Math.sin(Date.now() / 400);
                
                // Fill with copied style color (transparent)
                roundedRectPath(rect.x, rect.y, rect.width, rect.height, radius);
                editor.ctx.fillStyle = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${0.12 * pulse})`;
                editor.ctx.fill();
                
                // Outer border using copied style color
                roundedRectPath(rect.x, rect.y, rect.width, rect.height, radius);
                editor.ctx.strokeStyle = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${0.8 * pulse})`;
                editor.ctx.lineWidth = 2.5 / editor.zoom;
                editor.ctx.setLineDash([]);
                editor.ctx.stroke();
                
                // Corner accents using copied style color
                const accentSize = 8 / editor.zoom;
                editor.ctx.fillStyle = styleColor;
                
                // Draw corner L-shapes for modern look
                const cornerLen = 12 / editor.zoom;
                const cornerWidth = 2.5 / editor.zoom;
                editor.ctx.fillStyle = styleColor;
                
                // Top-left corner
                editor.ctx.fillRect(rect.x - cornerWidth/2, rect.y - cornerWidth/2, cornerLen, cornerWidth);
                editor.ctx.fillRect(rect.x - cornerWidth/2, rect.y - cornerWidth/2, cornerWidth, cornerLen);
                
                // Top-right corner
                editor.ctx.fillRect(rect.x + rect.width - cornerLen + cornerWidth/2, rect.y - cornerWidth/2, cornerLen, cornerWidth);
                editor.ctx.fillRect(rect.x + rect.width - cornerWidth/2, rect.y - cornerWidth/2, cornerWidth, cornerLen);
                
                // Bottom-left corner
                editor.ctx.fillRect(rect.x - cornerWidth/2, rect.y + rect.height - cornerWidth/2, cornerLen, cornerWidth);
                editor.ctx.fillRect(rect.x - cornerWidth/2, rect.y + rect.height - cornerLen + cornerWidth/2, cornerWidth, cornerLen);
                
                // Bottom-right corner
                editor.ctx.fillRect(rect.x + rect.width - cornerLen + cornerWidth/2, rect.y + rect.height - cornerWidth/2, cornerLen, cornerWidth);
                editor.ctx.fillRect(rect.x + rect.width - cornerWidth/2, rect.y + rect.height - cornerLen + cornerWidth/2, cornerWidth, cornerLen);
                
                // Modern floating label pill at top - using copied style color
                const labelText = 'Apply Style';
                const fontSize = 11 / editor.zoom;
                editor.ctx.font = `600 ${fontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
                const labelMetrics = editor.ctx.measureText(labelText);
                const pillWidth = labelMetrics.width + 20 / editor.zoom;
                const pillHeight = 20 / editor.zoom;
                const pillX = rect.x + rect.width / 2 - pillWidth / 2;
                const pillY = rect.y - pillHeight - 6 / editor.zoom;
                const pillRadius = 4 / editor.zoom;
                
                // Pill background with subtle shadow
                editor.ctx.shadowColor = 'rgba(0, 0, 0, 0.2)';
                editor.ctx.shadowBlur = 6 / editor.zoom;
                editor.ctx.shadowOffsetY = 2 / editor.zoom;
                
                // Draw pill shape with rounded corners
                roundedRectPath(pillX, pillY, pillWidth, pillHeight, pillRadius);
                editor.ctx.fillStyle = styleColor;
                editor.ctx.fill();
                
                // Reset shadow
                editor.ctx.shadowColor = 'transparent';
                editor.ctx.shadowBlur = 0;
                editor.ctx.shadowOffsetY = 0;
                
                // Pill text - white or dark based on color brightness
                const brightness = (rgb.r * 299 + rgb.g * 587 + rgb.b * 114) / 1000;
                editor.ctx.fillStyle = brightness > 128 ? '#1f2937' : '#ffffff';
                editor.ctx.textAlign = 'center';
                editor.ctx.textBaseline = 'middle';
                editor.ctx.fillText(labelText, pillX + pillWidth / 2, pillY + pillHeight / 2);
                
                // Object count indicator (bottom right) - using copied style color
                if (editor.selectedObjects && editor.selectedObjects.length > 0) {
                    const countText = `${editor.selectedObjects.length}`;
                    editor.ctx.font = `600 ${10 / editor.zoom}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
                    const countSize = 20 / editor.zoom;
                    const countX = rect.x + rect.width + 4 / editor.zoom;
                    const countY = rect.y + rect.height - countSize;
                    
                    // Count circle background
                    editor.ctx.beginPath();
                    editor.ctx.arc(countX + countSize/2, countY + countSize/2, countSize/2, 0, Math.PI * 2);
                    editor.ctx.fillStyle = styleColor;
                    editor.ctx.fill();
                    
                    // Count text
                    editor.ctx.fillStyle = brightness > 128 ? '#1f2937' : '#ffffff';
                    editor.ctx.textAlign = 'center';
                    editor.ctx.textBaseline = 'middle';
                    editor.ctx.fillText(countText, countX + countSize/2, countY + countSize/2);
                }
                
                editor.ctx.restore();
                
                // Request animation frame for pulse effect
                if (!editor._csmsAnimationFrame) {
                    editor._csmsAnimationFrame = requestAnimationFrame(() => {
                        editor._csmsAnimationFrame = null;
                        if (editor.csmsMode && editor.marqueeActive) editor.draw();
                    });
                }
            } else {
                // CLEAN MS BOX - Professional, simple selection rectangle (no animations)
                const rect = editor.selectionRectangle;
                const radius = 6 / editor.zoom; // Subtle rounded corners
                
                editor.ctx.save();
                
                // Helper function for rounded rectangle path
                const roundedRectPath = (x, y, w, h, r) => {
                    r = Math.min(r, w / 2, h / 2);
                    editor.ctx.beginPath();
                    editor.ctx.moveTo(x + r, y);
                    editor.ctx.lineTo(x + w - r, y);
                    editor.ctx.quadraticCurveTo(x + w, y, x + w, y + r);
                    editor.ctx.lineTo(x + w, y + h - r);
                    editor.ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
                    editor.ctx.lineTo(x + r, y + h);
                    editor.ctx.quadraticCurveTo(x, y + h, x, y + h - r);
                    editor.ctx.lineTo(x, y + r);
                    editor.ctx.quadraticCurveTo(x, y, x + r, y);
                    editor.ctx.closePath();
                };
                
                // Simple semi-transparent fill (mode-aware)
                roundedRectPath(rect.x, rect.y, rect.width, rect.height, radius);
                editor.ctx.fillStyle = editor.darkMode ? 'rgba(52, 152, 219, 0.12)' : 'rgba(52, 152, 219, 0.08)';
                editor.ctx.fill();
                
                // Clean solid border
                editor.ctx.strokeStyle = 'rgba(52, 152, 219, 0.6)';
                editor.ctx.lineWidth = 1.5 / editor.zoom;
                editor.ctx.setLineDash([]);
                editor.ctx.stroke();
                
                // Selection count badge (simple pill)
                if (editor.selectedObjects && editor.selectedObjects.length > 0) {
                    const countText = `${editor.selectedObjects.length}`;
                    editor.ctx.font = `600 ${10 / editor.zoom}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
                    const countSize = 18 / editor.zoom;
                    const countX = rect.x + rect.width + 4 / editor.zoom;
                    const countY = rect.y + 4 / editor.zoom;
                    
                    // Simple pill background
                    roundedRectPath(countX, countY, countSize, countSize, countSize / 2);
                    editor.ctx.fillStyle = 'rgba(52, 152, 219, 0.9)';
                    editor.ctx.fill();
                    
                    // Count text
                    editor.ctx.fillStyle = '#ffffff';
                    editor.ctx.textAlign = 'center';
                    editor.ctx.textBaseline = 'middle';
                    editor.ctx.fillText(countText, countX + countSize / 2, countY + countSize / 2);
                }
                
                editor.ctx.restore();
                // No animation frame needed - static display
            }
            editor.ctx.setLineDash([]);
        }
        
        // MANUAL CURVE: Draw control handles
        // Handle is shown ONLY when hovering over a manual curve link or actively dragging
        // TB (text box) and CP (control point) are SEPARATE - TB moves link, CP controls curve
        const linksToDrawHandles = [];
        
        // During active drag: show handle at the curve pass-through point
        if (editor.draggingCurveHandle) {
            const link = editor.draggingCurveHandle.link;
            // The manualControlPoint IS the pass-through point - curve goes exactly through this point
            if (link.manualControlPoint) {
                linksToDrawHandles.push({
                    link: link,
                    midpoint: link.manualControlPoint,
                    isActive: true
                });
            }
        }
        // When hovering over a link with manual curve mode: show handle at the curve midpoint
        // FIXED: Check effective curve mode (global or per-link), not just per-link property
        // ENHANCED: Pass isOnCP state for differentiated rendering (subtle when nearby, bold when on handle)
        // CRITICAL FIX: Don't show CP when there's a middle-attached TB (TB acts as CP in that case)
        else if (editor.hoveredLinkMidpoint) {
            const link = editor.hoveredLinkMidpoint.link;
            const effectiveMode = editor.getEffectiveCurveMode(link);
            if (effectiveMode === 'manual') {
                // Check if there's a middle-attached TB on this link
                // If so, the TB IS the curve control - don't show separate CP handle
                const hasMiddleAttachedTB = editor.objects.some(obj => 
                    obj.type === 'text' && obj.linkId === link.id && obj.position === 'middle'
                );
                
                if (!hasMiddleAttachedTB) {
                    // FIXED: Recalculate midpoint fresh instead of using cached value
                    // This ensures the CP moves with the link when the link body is being dragged
                    const freshMidpoint = editor.getLinkMidpoint(link);
                    
                    if (freshMidpoint) {
                        linksToDrawHandles.push({
                            link: link,
                            midpoint: freshMidpoint,
                            isActive: true,
                            isOnCP: editor.hoveredLinkMidpoint.isOnCP === true // Pass through direct hover state
                        });
                    }
                }
            }
        }
        
        // Draw all curve handles (only when hovering over link)
        // PERFECTED: Premium liquid glass CP with polished gem-like appearance
        // THREE VISUAL STATES: Nearby (subtle hint), OnCP (full), Dragging (brilliant + pulse)
        for (const handleInfo of linksToDrawHandles) {
            const isDragging = editor.draggingCurveHandle?.link === handleInfo.link;
            const isOnCP = handleInfo.isOnCP === true || isDragging; // Directly over the handle
            const isNearby = handleInfo.isActive && !isOnCP; // Near but not directly on CP
            
            // Size based on state: dragging > onCP > nearby
            const baseRadius = isDragging ? 11 : (isOnCP ? 9 : 7);
            const handleRadius = baseRadius / editor.zoom;
            const x = handleInfo.midpoint.x;
            const y = handleInfo.midpoint.y;
            
            // Opacity multiplier for nearby (subtle) vs direct (full)
            const opacity = isNearby ? 0.65 : 1.0;
            
            // ===== LAYER 1: Outer ambient glow (soft halo) =====
            if (isOnCP || isDragging) {
                // Full glow when directly over or dragging
                const glowGradient = editor.ctx.createRadialGradient(x, y, 0, x, y, handleRadius * 2.8);
                glowGradient.addColorStop(0, isDragging ? 'rgba(255, 167, 38, 0.5)' : 'rgba(255, 167, 38, 0.35)');
                glowGradient.addColorStop(0.4, isDragging ? 'rgba(245, 130, 32, 0.25)' : 'rgba(245, 130, 32, 0.15)');
                glowGradient.addColorStop(1, 'rgba(255, 94, 31, 0)');
                
                editor.ctx.beginPath();
                editor.ctx.arc(x, y, handleRadius * 2.8, 0, Math.PI * 2);
                editor.ctx.fillStyle = glowGradient;
                editor.ctx.fill();
            } else if (isNearby) {
                // Subtle hint glow when nearby
                const hintGlow = editor.ctx.createRadialGradient(x, y, 0, x, y, handleRadius * 2);
                hintGlow.addColorStop(0, 'rgba(255, 167, 38, 0.15)');
                hintGlow.addColorStop(1, 'rgba(255, 94, 31, 0)');
                
                editor.ctx.beginPath();
                editor.ctx.arc(x, y, handleRadius * 2, 0, Math.PI * 2);
                editor.ctx.fillStyle = hintGlow;
                editor.ctx.fill();
            }
            
            // ===== LAYER 2: Drop shadow for depth =====
            editor.ctx.beginPath();
            editor.ctx.arc(x + 1/editor.zoom, y + 2/editor.zoom, handleRadius * 1.05, 0, Math.PI * 2);
            editor.ctx.fillStyle = `rgba(0, 0, 0, ${0.3 * opacity})`;
            editor.ctx.fill();
            
            // ===== LAYER 3: Outer ring (dark accent) - only when on CP or dragging =====
            if (isOnCP || isDragging) {
                editor.ctx.beginPath();
                editor.ctx.arc(x, y, handleRadius + 2.5/editor.zoom, 0, Math.PI * 2);
                const ringGradient = editor.ctx.createRadialGradient(x, y, handleRadius * 0.8, x, y, handleRadius + 2.5/editor.zoom);
                ringGradient.addColorStop(0, isDragging ? '#CC4A16' : '#B3400F');
                ringGradient.addColorStop(1, isDragging ? '#A04000' : '#8D2B0B');
                editor.ctx.fillStyle = ringGradient;
                editor.ctx.fill();
            }
            
            // ===== LAYER 4: Main body with liquid glass gradient =====
            editor.ctx.beginPath();
            editor.ctx.arc(x, y, handleRadius, 0, Math.PI * 2);
            
            // Premium multi-stop gradient for gem-like appearance
            const bodyGradient = editor.ctx.createRadialGradient(
                x - handleRadius * 0.35, y - handleRadius * 0.35, 0,
                x, y, handleRadius * 1.2
            );
            
            if (isDragging) {
                // Actively dragging - brilliant warm glow
                bodyGradient.addColorStop(0, '#FFECB3');    // Bright highlight
                bodyGradient.addColorStop(0.15, '#FFD54F'); // Golden
                bodyGradient.addColorStop(0.4, '#FFA726');  // Orange
                bodyGradient.addColorStop(0.7, '#F57C00');  // Deep orange
                bodyGradient.addColorStop(1, '#E65100');    // Rich orange
            } else if (isOnCP) {
                // Directly on handle - vibrant and inviting
                bodyGradient.addColorStop(0, '#FFF8E1');    // Soft cream highlight
                bodyGradient.addColorStop(0.2, '#FFCC80');  // Light orange
                bodyGradient.addColorStop(0.5, '#FFA726');  // Orange
                bodyGradient.addColorStop(0.8, '#FB8C00');  // Deep orange
                bodyGradient.addColorStop(1, '#EF6C00');    // Rich orange
            } else {
                // Nearby - subtle polished orange with reduced saturation
                bodyGradient.addColorStop(0, `rgba(255, 236, 179, ${opacity})`);
                bodyGradient.addColorStop(0.3, `rgba(255, 183, 77, ${opacity})`);
                bodyGradient.addColorStop(0.6, `rgba(255, 152, 0, ${opacity})`);
                bodyGradient.addColorStop(1, `rgba(245, 124, 0, ${opacity})`);
            }
            
            editor.ctx.fillStyle = bodyGradient;
            editor.ctx.fill();
            
            // ===== LAYER 5: Glass highlight (top-left shine) =====
            editor.ctx.beginPath();
            editor.ctx.ellipse(
                x - handleRadius * 0.25, 
                y - handleRadius * 0.3, 
                handleRadius * 0.45, 
                handleRadius * 0.3, 
                -Math.PI / 6, 0, Math.PI * 2
            );
            const highlightGradient = editor.ctx.createRadialGradient(
                x - handleRadius * 0.3, y - handleRadius * 0.35, 0,
                x - handleRadius * 0.2, y - handleRadius * 0.25, handleRadius * 0.5
            );
            highlightGradient.addColorStop(0, `rgba(255, 255, 255, ${0.95 * opacity})`);
            highlightGradient.addColorStop(0.5, `rgba(255, 255, 255, ${0.45 * opacity})`);
            highlightGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
            editor.ctx.fillStyle = highlightGradient;
            editor.ctx.fill();
            
            // ===== LAYER 6: Secondary highlight (bottom-right reflection) =====
            if (isOnCP || isDragging) {
                editor.ctx.beginPath();
                editor.ctx.arc(x + handleRadius * 0.25, y + handleRadius * 0.25, handleRadius * 0.2, 0, Math.PI * 2);
                editor.ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
                editor.ctx.fill();
            }
            
            // ===== LAYER 7: Crisp white border =====
            editor.ctx.beginPath();
            editor.ctx.arc(x, y, handleRadius, 0, Math.PI * 2);
            editor.ctx.strokeStyle = `rgba(255, 255, 255, ${0.95 * opacity})`;
            editor.ctx.lineWidth = (isOnCP || isDragging ? 2.5 : 1.5) / editor.zoom;
            editor.ctx.stroke();
            
            // ===== LAYER 8: Inner icon (curve symbol) - only on direct hover or drag =====
            if (isOnCP || isDragging) {
                const iconScale = handleRadius * 0.4;
                editor.ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
                editor.ctx.lineWidth = 1.5 / editor.zoom;
                editor.ctx.lineCap = 'round';
                
                // Draw a small bezier curve icon inside
            editor.ctx.beginPath();
                editor.ctx.moveTo(x - iconScale, y);
                editor.ctx.quadraticCurveTo(x, y - iconScale * 1.2, x + iconScale, y);
                editor.ctx.stroke();
                
                // Small dots at the ends
                editor.ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
                editor.ctx.beginPath();
                editor.ctx.arc(x - iconScale, y, 1.8/editor.zoom, 0, Math.PI * 2);
            editor.ctx.fill();
                editor.ctx.beginPath();
                editor.ctx.arc(x + iconScale, y, 1.8/editor.zoom, 0, Math.PI * 2);
                editor.ctx.fill();
            }
            
            // ===== LAYER 9: Pulse animation ring when dragging =====
            if (isDragging) {
                const pulsePhase = (Date.now() % 1000) / 1000;
                const pulseRadius = handleRadius * (1.4 + pulsePhase * 0.9);
                const pulseAlpha = 0.5 * (1 - pulsePhase);
                
                editor.ctx.beginPath();
                editor.ctx.arc(x, y, pulseRadius, 0, Math.PI * 2);
                editor.ctx.strokeStyle = `rgba(255, 167, 38, ${pulseAlpha})`;
                editor.ctx.lineWidth = 2.5 / editor.zoom;
                editor.ctx.stroke();
                
                // Second pulse ring (offset timing)
                const pulsePhase2 = ((Date.now() + 500) % 1000) / 1000;
                const pulseRadius2 = handleRadius * (1.4 + pulsePhase2 * 0.9);
                const pulseAlpha2 = 0.3 * (1 - pulsePhase2);
                
                editor.ctx.beginPath();
                editor.ctx.arc(x, y, pulseRadius2, 0, Math.PI * 2);
                editor.ctx.strokeStyle = `rgba(255, 193, 7, ${pulseAlpha2})`;
                editor.ctx.lineWidth = 1.5 / editor.zoom;
            editor.ctx.stroke();
                
                // Request redraw for animation
                if (!editor._cpPulseAnimationFrame) {
                    editor._cpPulseAnimationFrame = requestAnimationFrame(() => {
                        editor._cpPulseAnimationFrame = null;
                        if (editor.draggingCurveHandle) editor.draw();
                    });
                }
            }
        }
        
        // LINK PREVIEW: Draw link preview line when in link mode (BEFORE restore, so it uses the transform)
        if (editor.currentTool === 'link' && editor.linking && editor.lastMousePos) {
            const endPos = editor.lastMousePos;
            let startPt = null;
            let previewColor = '#3498db'; // Default blue
            
            // Check if preview is from device or from TP
            if (editor.linkStart) {
                // Preview from device double-click - use device color
                const startDevice = editor.linkStart;
                previewColor = startDevice.color || '#3498db';
                const angle1 = Math.atan2(endPos.y - startDevice.y, endPos.x - startDevice.x);
                startPt = editor.getLinkConnectionPoint(startDevice, angle1);
            } else if (editor._linkFromTP) {
                // Preview from TP click — use the source link's color
                const srcLink = editor._linkFromTP.link;
                previewColor = (srcLink && srcLink.color) || editor.currentLinkColor || '#3498db';
                startPt = editor._linkFromTP.startPos;
            }
            
            if (startPt) {
                // Use device color for preview line
                editor.ctx.strokeStyle = previewColor;
                editor.ctx.lineWidth = 3 / editor.zoom;
                editor.ctx.setLineDash([8 / editor.zoom, 4 / editor.zoom]);
                
                editor.ctx.beginPath();
                editor.ctx.moveTo(startPt.x, startPt.y);
                editor.ctx.lineTo(endPos.x, endPos.y);
                editor.ctx.stroke();
                
                // Draw a small circle at the cursor position
                editor.ctx.fillStyle = previewColor;
                editor.ctx.beginPath();
                editor.ctx.arc(endPos.x, endPos.y, 5 / editor.zoom, 0, Math.PI * 2);
                editor.ctx.fill();
                
                // Reset line dash
                editor.ctx.setLineDash([]);
            }
        }
        
        editor.ctx.restore();
        
        // Active topology label removed — shown only in the indicator bar next to minimap
        
        // SMOOTH MOVEMENT: Continue animation loop for Arrow-style ULs still interpolating
        // Check if any arrow-style ULs need more interpolation
        let needsMoreAnimation = false;
        editor.objects.forEach(obj => {
            if (obj.type === 'unbound' && (obj.style === 'arrow' || obj.style === 'double-arrow')) {
                // Check if positions are still interpolating (not settled yet)
                if (obj._targetStart && obj.start) {
                    const startDist = Math.sqrt(
                        Math.pow(obj.start.x - obj._targetStart.x, 2) + 
                        Math.pow(obj.start.y - obj._targetStart.y, 2)
                    );
                    if (startDist > 1) needsMoreAnimation = true;
                }
                if (obj._targetEnd && obj.end) {
                    const endDist = Math.sqrt(
                        Math.pow(obj.end.x - obj._targetEnd.x, 2) + 
                        Math.pow(obj.end.y - obj._targetEnd.y, 2)
                    );
                    if (endDist > 1) needsMoreAnimation = true;
                }
            }
        });
        
        if (needsMoreAnimation && !editor._smoothAnimationPending) {
            editor._smoothAnimationPending = true;
            requestAnimationFrame(() => {
                editor._smoothAnimationPending = false;
                editor.draw();
            });
        }

        if (editor.minimap && editor.minimap.visible !== false && window.MinimapRender) {
            window.MinimapRender.scheduleRender(editor);
        }
    }
    
    // ==================== DEVICE VISUAL STYLES ====================
    // Implementation moved to topology-device-styles.js (~840 lines extracted)
    // See DeviceStyles module for drawing functions and geometry calculations
    

};

console.log('[topology-draw.js] DrawModule loaded');
