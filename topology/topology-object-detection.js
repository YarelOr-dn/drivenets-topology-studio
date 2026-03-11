/**
 * topology-object-detection.js - Object Detection Module
 * Contains: findObjectAt, findTextAt, findRotationHandle, findTextHandle, findTerminalButton
 */

'use strict';

window.ObjectDetection = {
    findObjectAt(editor, x, y) {
        // TRUE LAYER-AWARE: Sort objects by layer (highest first), then by type within same layer
        // Matches visual z-order exactly: higher layer = higher selection priority
        // MERGED SHAPES: Checked absolutely last - they are part of the grid background
        const sortedByLayerDesc = [...editor.objects].sort((a, b) => {
            // CRITICAL: Merged-to-background shapes go LAST (checked after everything)
            const aMerged = a.type === 'shape' && a.mergedToBackground;
            const bMerged = b.type === 'shape' && b.mergedToBackground;
            if (aMerged && !bMerged) return 1;  // a (merged) goes after b
            if (bMerged && !aMerged) return -1; // b (merged) goes after a
            
            // Layer-based ordering for ALL object types (including shapes)
            const layerA = editor.getObjectLayer(a);
            const layerB = editor.getObjectLayer(b);
            if (layerA !== layerB) {
                return layerB - layerA; // Higher layers first
            }
            // Within same layer, match visual draw order (reversed for hit detection):
            // Draw order: shape(-1) < link(0) < device(1) < text(2) → lower drawn first (behind)
            // Hit order: text(4) > device(3) > link(2) > shape(1) → higher checked first (on top)
            const typeOrder = { 'text': 4, 'device': 3, 'link': 2, 'unbound': 2, 'shape': 1 };
            return (typeOrder[b.type] || 0) - (typeOrder[a.type] || 0);
        });
        
        // ENHANCED: Track closest link for precise selection when multiple links overlap
        let closestLink = null;
        let closestLinkDistance = Infinity;
        
        // ENHANCED: Also track closest TP (termination point) across ALL links
        // When clicking near TPs, prioritize the closest TP regardless of which link body is closer
        let closestTPLink = null;
        let closestTPDistance = Infinity;
        
        // SINGLE PASS: Check ALL objects in TRUE layer order (highest layer first)
        // This respects the layering system - a link on layer 10 will be detected before a device on layer 5
        for (let i = 0; i < sortedByLayerDesc.length; i++) {
            const obj = sortedByLayerDesc[i];
            
            if (obj.type === 'text') {
                // CRITICAL: Set font BEFORE measuring text (include fontStyle for italic)
                editor.ctx.save();
                const fontFamily = obj.fontFamily || 'Arial';
                const fontWeight = obj.fontWeight || 'normal';
                const fontStyle = obj.fontStyle || 'normal';
                editor.ctx.font = `${fontStyle} ${fontWeight} ${obj.fontSize}px ${fontFamily}`;
                
                // MULTILINE SUPPORT: Measure each line separately for accurate hitbox
                const lines = (obj.text || 'Text').split('\n');
                let maxWidth = 0;
                for (const line of lines) {
                    const lineMetrics = editor.ctx.measureText(line || ' ');
                    maxWidth = Math.max(maxWidth, lineMetrics.width);
                }
                const w = maxWidth;
                const fontSize = parseInt(obj.fontSize) || 14;
                const lineHeight = fontSize * 1.3; // Match the 1.3 line-height from drawing
                const h = lines.length * lineHeight;
                editor.ctx.restore();
                
                // Rotate point to check if it's in bounding box (use effective rotation)
                const dx = x - obj.x;
                const dy = y - obj.y;
                const effRot = editor.getEffectiveTextRotation ? editor.getEffectiveTextRotation(obj) : (obj.rotation || 0);
                const angle = -effRot * Math.PI / 180;
                const rx = dx * Math.cos(angle) - dy * Math.sin(angle);
                const ry = dx * Math.sin(angle) + dy * Math.cos(angle);
                
                // ZOOM-AWARE HITBOX: Convert padding to world coords for pixel-accurate detection
                const hasBackground = obj.showBackground !== false;
                const bgPadding = hasBackground ? (obj.backgroundPadding || 8) : 4;
                const isSelected = editor.selectedObject === obj;
                
                // PIXEL-ACCURATE: Use screen-space padding converted to world coords
                // This ensures consistent click tolerance regardless of zoom level
                const screenPadding = isSelected ? 8 : 4; // Screen pixels
                const worldPadding = screenPadding / editor.zoom; // Convert to world coords
                const totalPadding = bgPadding + worldPadding;
                
                if (Math.abs(rx) <= (w/2 + totalPadding) && Math.abs(ry) <= (h/2 + totalPadding)) return obj;
            } else if (obj.type === 'device') {
                // PIXEL-ACCURATE DEVICE HITBOX: Convert tolerance to screen space
                // This ensures consistent clickability at all zoom levels
                const isSelected = editor.selectedObject === obj;
                const screenTolerance = isSelected ? 12 : 6; // Screen pixels
                const hitboxTolerance = screenTolerance / editor.zoom; // Convert to world coords
                
                if (editor.isPointInDeviceBounds(x, y, obj, hitboxTolerance)) return obj;
            } else if (obj.type === 'shape') {
                // Shape hit detection - handle rotation like text objects
                const dx = x - obj.x;
                const dy = y - obj.y;
                
                // If shape has rotation, transform the click point to shape's local coordinate system
                let localX = dx;
                let localY = dy;
                if (obj.rotation) {
                    const angle = -(obj.rotation || 0) * Math.PI / 180;
                    localX = dx * Math.cos(angle) - dy * Math.sin(angle);
                    localY = dx * Math.sin(angle) + dy * Math.cos(angle);
                }
                
                // Use shape's actual dimensions with tolerance that scales with zoom
                const zoomTolerance = Math.max(8, 15 / editor.zoom);
                const hw = (obj.width || 100) / 2 + zoomTolerance;
                const hh = (obj.height || 100) / 2 + zoomTolerance;
                
                // MERGED TO BACKGROUND: Only detect clicks on the BORDERS, not the interior
                // Interior acts like grid - transparent to clicks, devices can be placed on it
                if (obj.mergedToBackground) {
                    // Border detection: minimum 15px clickable zone regardless of stroke width
                    const strokeWidth = obj.strokeWidth || 2;
                    const minBorderHitbox = 15;  // Minimum clickable border width in screen pixels
                    const borderTolerance = Math.max(minBorderHitbox, strokeWidth + 8) / editor.zoom;
                    
                    // Shape-specific border hit detection
                    const shapeType = obj.shapeType || 'rectangle';
                    let onBorder = false;
                    
                    if (shapeType === 'circle') {
                        // Circle: check distance from center
                        const dist = Math.sqrt(localX * localX + localY * localY);
                        const outerRadius = (obj.width || 100) / 2 + zoomTolerance;
                        const innerRadius = Math.max(0, outerRadius - borderTolerance);
                        onBorder = dist <= outerRadius && dist >= innerRadius;
                    } else if (shapeType === 'ellipse') {
                        // Ellipse: use normalized ellipse equation
                        const outerA = hw;  // Already includes zoomTolerance
                        const outerB = hh;
                        const innerA = Math.max(1, outerA - borderTolerance);
                        const innerB = Math.max(1, outerB - borderTolerance);
                        const outerDist = (localX * localX) / (outerA * outerA) + (localY * localY) / (outerB * outerB);
                        const innerDist = (localX * localX) / (innerA * innerA) + (localY * localY) / (innerB * innerB);
                        onBorder = outerDist <= 1 && innerDist >= 1;
                    } else {
                        // Rectangle and other shapes: use rectangular bounds
                        const innerHw = Math.max(0, hw - borderTolerance);
                        const innerHh = Math.max(0, hh - borderTolerance);
                        const insideOuter = Math.abs(localX) <= hw && Math.abs(localY) <= hh;
                        const insideInner = innerHw > 0 && innerHh > 0 && 
                                            Math.abs(localX) <= innerHw && Math.abs(localY) <= innerHh;
                        onBorder = insideOuter && !insideInner;
                    }
                    
                    if (onBorder) return obj;  // Only border hit
                    // If inside inner area (the "grid zone"), don't return this shape - continue checking
                } else {
                    // Normal shape: entire area is clickable
                    if (Math.abs(localX) <= hw && Math.abs(localY) <= hh) return obj;
                }
            } else if (obj.type === 'link' || obj.type === 'unbound') {
                // For links, collect distance - we'll find the CLOSEST link later
                const hitDistance = editor._checkLinkHit(x, y, obj);
                if (hitDistance >= 0) {
                    // Store this link as a candidate with its distance
                    if (!closestLink || hitDistance < closestLinkDistance) {
                        closestLink = obj;
                        closestLinkDistance = hitDistance;
                    }
                }
                
                // ENHANCED: Also check distance to this link's TPs specifically
                // This helps prioritize TP clicks when multiple links have nearby endpoints
                const tpRadius = 5 / editor.zoom;
                let tpDist = Infinity;
                
                // Get link endpoints
                if (obj.type === 'unbound' && obj.start && obj.end) {
                    const distToStart = Math.sqrt(Math.pow(x - obj.start.x, 2) + Math.pow(y - obj.start.y, 2));
                    const distToEnd = Math.sqrt(Math.pow(x - obj.end.x, 2) + Math.pow(y - obj.end.y, 2));
                    tpDist = Math.min(distToStart, distToEnd);
                } else if (obj._renderedEndpoints) {
                    const distToStart = Math.sqrt(Math.pow(x - obj._renderedEndpoints.startX, 2) + Math.pow(y - obj._renderedEndpoints.startY, 2));
                    const distToEnd = Math.sqrt(Math.pow(x - obj._renderedEndpoints.endX, 2) + Math.pow(y - obj._renderedEndpoints.endY, 2));
                    tpDist = Math.min(distToStart, distToEnd);
                }
                
                // If this TP is closer than any previous, and within click radius, track it
                if (tpDist < tpRadius && tpDist < closestTPDistance) {
                    closestTPLink = obj;
                    closestTPDistance = tpDist;
                }
            }
        }
        
        // PRIORITY: If a TP was clicked directly, prioritize that link over general link body hits
        // This ensures clicking on a specific TP selects that link even if another link body is nearby
        if (closestTPLink && closestTPDistance < 8 / editor.zoom) {
            // Use the TP-clicked link, but still check device bounds
            closestLink = closestTPLink;
            closestLinkDistance = closestTPDistance;
        }
        
        // PRIORITY FIX: Before returning a link, check if click is INSIDE a device's visual bounds
        // Only give device priority when click is actually ON the device, not just near it
        // This prevents links from being un-selectable when they pass near devices
        if (closestLink) {
            // Only check devices that the link is connected to
            const connectedDeviceIds = new Set();
            if (closestLink.device1) connectedDeviceIds.add(closestLink.device1);
            if (closestLink.device2) connectedDeviceIds.add(closestLink.device2);
            if (closestLink.connectedTo) connectedDeviceIds.add(closestLink.connectedTo.deviceId);
            
            // Check ONLY connected devices with a SMALL tolerance (just the visual device bounds)
            for (const deviceId of connectedDeviceIds) {
                const device = editor.objects.find(o => o.id === deviceId);
                if (device) {
                    // Use minimal tolerance - only if click is truly ON the device visually
                    const visualTolerance = 5 / editor.zoom; // 5 screen pixels
                    if (editor.isPointInDeviceBounds(x, y, device, visualTolerance)) {
                        return device;
                    }
                }
            }
            
            return closestLink;
        }

        return null; // Nothing found
    },
    
    // Find specifically a TEXT object at the given position
    // Used to give TB priority over CP (curve control point) during click detection
    // FIX: Increased hitbox for TBs attached to links to match click handler logic
    findTextAt(editor, x, y) {
        // Check all text objects (highest layer first for proper detection)
        const textObjects = editor.objects
            .filter(obj => obj.type === 'text')
            .sort((a, b) => editor.getObjectLayer(b) - editor.getObjectLayer(a));
        
        for (const obj of textObjects) {
            // CRITICAL: Set font BEFORE measuring text (include fontStyle for italic)
            editor.ctx.save();
            const fontFamily = obj.fontFamily || 'Arial';
            const fontWeight = obj.fontWeight || 'normal';
            const fontStyle = obj.fontStyle || 'normal';
            editor.ctx.font = `${fontStyle} ${fontWeight} ${obj.fontSize}px ${fontFamily}`;
            const metrics = editor.ctx.measureText(obj.text || 'Text');
            const w = metrics.width;
            const h = parseInt(obj.fontSize) || 14;
            editor.ctx.restore();
            
            // Rotate point to check if it's in bounding box (use effective rotation)
            const dx = x - obj.x;
            const dy = y - obj.y;
            const effRot2 = editor.getEffectiveTextRotation ? editor.getEffectiveTextRotation(obj) : (obj.rotation || 0);
            const angle = -effRot2 * Math.PI / 180;
            const rx = dx * Math.cos(angle) - dy * Math.sin(angle);
            const ry = dx * Math.sin(angle) + dy * Math.cos(angle);
            
            // TB attached to link should have LARGER hitbox to win over CP
            const hasBackground = obj.showBackground !== false;
            const bgPadding = hasBackground ? (obj.backgroundPadding || 8) : 6;
            const isSelected = editor.selectedObject === obj;
            // Larger base for attached TBs to ensure they win over CP
            const extraPadding = isSelected ? 10 : 6;
            const totalPadding = bgPadding + extraPadding;
            
            if (Math.abs(rx) <= (w/2 + totalPadding) && Math.abs(ry) <= (h/2 + totalPadding)) {
                return obj;
            }
        }
        
        return null;
    },
    
    // Helper to check if a point hits a link
    _checkLinkHit(x, y, obj) {
        // CRITICAL FIX: For BUL chains, we need special handling
        // TAIL/MIDDLE links should NOT be skipped - instead, we redirect to the HEAD
        // so clicking ANY segment selects the whole chain
        if (obj.type === 'unbound' && obj.mergedInto) {
            // This is a TAIL or MIDDLE link - find the HEAD and delegate to it
            let headLink = obj;
            while (headLink.mergedInto) {
                const parentId = headLink.mergedInto.parentId;
                const parent = editor.objects.find(o => o.id === parentId);
                if (!parent) break;
                headLink = parent;
            }
            // If we found a different HEAD, delegate to it
            if (headLink.id !== obj.id) {
                return -1; // Skip this - HEAD will handle the whole chain
            }
        }
        
        // CRITICAL FIX: Exclude points that are INSIDE connected devices
        // This ensures clicking on a device doesn't accidentally select the connected link
        // Device has visual priority - if you click inside a device, you want the device, not the link
        if (obj.device1) {
            const device1 = editor.objects.find(o => o.id === obj.device1);
            if (device1 && editor.isPointInDeviceBounds(x, y, device1, 0)) {
                return -1; // Point is inside device1, don't count as link hit
            }
        }
        if (obj.device2) {
            const device2 = editor.objects.find(o => o.id === obj.device2);
            if (device2 && editor.isPointInDeviceBounds(x, y, device2, 0)) {
                return -1; // Point is inside device2, don't count as link hit
            }
        }
        // For unbound links attached to devices
        if (obj.type === 'unbound') {
            if (obj.device1) {
                const dev = editor.objects.find(o => o.id === obj.device1);
                if (dev && editor.isPointInDeviceBounds(x, y, dev, 0)) {
                    return -1;
                }
            }
            if (obj.device2) {
                const dev = editor.objects.find(o => o.id === obj.device2);
                if (dev && editor.isPointInDeviceBounds(x, y, dev, 0)) {
                    return -1;
                }
            }
        }
        
        let minDistToLink = Infinity;
        
        // FIXED: Calculate hitbox based on VISUAL appearance on screen
        // The hit area should match what the user sees, regardless of zoom level
        const linkWidth = obj.width !== undefined ? obj.width : editor.currentLinkWidth;
        
        // ENHANCED: Zoom-aware tolerance with better small object detection
        // Use smaller tolerance when zoomed in for precise clicking on elements
        // Use larger tolerance when zoomed out to maintain clickability
        const baseScreenTolerance = 8; // Base tolerance in screen pixels
        const zoomFactor = Math.max(0.5, Math.min(2.0, editor.zoom)); // Clamp zoom factor
        
        // Adaptive tolerance: smaller when zoomed in (precise), larger when zoomed out (forgiving)
        const adaptiveScreenTolerance = editor.zoom > 1.0 
            ? baseScreenTolerance / Math.sqrt(zoomFactor)  // Tighter when zoomed in
            : baseScreenTolerance * Math.sqrt(1 / zoomFactor); // More forgiving when zoomed out
        
        const worldTolerance = adaptiveScreenTolerance / editor.zoom;
        
        // Maximum distance = half the visual width + adaptive world tolerance
        // This ensures the hitbox adapts to zoom for accurate clicking
        const maxDistance = (linkWidth / 2) + worldTolerance;
        
        // ADDITIONAL: For curved links, we need a slightly larger detection area
        // because the curve sampling might miss some points
        const hasCurve = !!(obj._cp1 && obj._cp2) || !!obj.manualCurvePoint;
        const curveBonus = hasCurve ? (5 / editor.zoom) : 0;
                        
        // Get the actual rendered endpoints (prefer _renderedEndpoints if available)
        let startX, startY, endX, endY;
        if (obj._renderedEndpoints) {
            startX = obj._renderedEndpoints.startX;
            startY = obj._renderedEndpoints.startY;
            endX = obj._renderedEndpoints.endX;
            endY = obj._renderedEndpoints.endY;
        } else if (obj.start && obj.end) {
            // Unbound links with direct start/end coordinates
            startX = obj.start.x;
            startY = obj.start.y;
            endX = obj.end.x;
            endY = obj.end.y;
        } else {
            // FALLBACK: Calculate endpoints from devices for device-connected links
            // This handles the case when links haven't been drawn yet (e.g., after loading)
            const calculatedEndpoints = editor.getLinkRenderedEndpoints(obj);
            if (calculatedEndpoints) {
                startX = calculatedEndpoints.startX;
                startY = calculatedEndpoints.startY;
                endX = calculatedEndpoints.endX;
                endY = calculatedEndpoints.endY;
        } else {
            return -1; // No valid endpoints
            }
        }
        
        // Calculate distance to link using stored control points if available
        // PRIORITY: Always use stored _cp1/_cp2 first for exact hitbox match with rendered curve
                    if (obj._cp1 && obj._cp2) {
                        // Use stored control points for accurate curved hitbox
            minDistToLink = editor.distanceToCurvedLineWithControlPoints(
                x, y, 
                { x: startX, y: startY }, 
                { x: endX, y: endY }, 
                obj._cp1, obj._cp2
            );
        } else if (obj.manualCurvePoint) {
            // Manual curve mode but control points not stored yet - derive from manualCurvePoint
            // Use symmetric control points based on manual curve point position
            const midX = (startX + endX) / 2;
            const midY = (startY + endY) / 2;
            const offsetX = obj.manualCurvePoint.x - midX;
            const offsetY = obj.manualCurvePoint.y - midY;
            // For symmetric bezier, control points are offset from endpoints toward the curve apex
            const cp1 = { x: startX + offsetX * 1.33, y: startY + offsetY * 1.33 };
            const cp2 = { x: endX + offsetX * 1.33, y: endY + offsetY * 1.33 };
            minDistToLink = editor.distanceToCurvedLineWithControlPoints(
                x, y, 
                { x: startX, y: startY }, 
                { x: endX, y: endY }, 
                cp1, cp2
            );
        } else if (obj.device1 && obj.device2) {
            // Device-to-device link - use full curve calculation (will recalculate curves)
            const d1 = editor.objects.find(o => o.id === obj.device1);
            const d2 = editor.objects.find(o => o.id === obj.device2);
            if (d1 && d2) {
                minDistToLink = editor.distanceToCurvedLine(x, y, obj, d1, d2);
            }
                    } else {
            // Straight line fallback
            minDistToLink = editor.distanceToLine(x, y, { x: startX, y: startY }, { x: endX, y: endY });
        }
        
        // Check arrow tip hitbox for arrow-style links
        // CRITICAL: Hitbox must be zoom-aware for consistent screen-space size
                const linkStyle = obj.style || 'solid';
                const isArrowStyle = linkStyle.includes('arrow');
        if (isArrowStyle) {
                    const arrowLength = 10 + (linkWidth * 3);
            const arrowTipRadius = arrowLength / editor.zoom;
                    
            const arrowTipEndX = obj._arrowTipEnd ? obj._arrowTipEnd.x : endX;
            const arrowTipEndY = obj._arrowTipEnd ? obj._arrowTipEnd.y : endY;
            const arrowTipStartX = obj._arrowTipStart ? obj._arrowTipStart.x : startX;
            const arrowTipStartY = obj._arrowTipStart ? obj._arrowTipStart.y : startY;
            
            // Check end tip
            const distToEndTip = Math.sqrt(Math.pow(x - arrowTipEndX, 2) + Math.pow(y - arrowTipEndY, 2));
                    if (distToEndTip < arrowTipRadius) {
                minDistToLink = Math.min(minDistToLink, distToEndTip * 0.5); // Prioritize arrow tip
                    }
                    
            // Check start tip for double-arrow
                    if (linkStyle.includes('double')) {
                const distToStartTip = Math.sqrt(Math.pow(x - arrowTipStartX, 2) + Math.pow(y - arrowTipStartY, 2));
                        if (distToStartTip < arrowTipRadius) {
                    minDistToLink = Math.min(minDistToLink, distToStartTip * 0.5);
                        }
                    }
                }
                
        // Also check BUL chain links
                if (obj.type === 'unbound' && (obj.mergedWith || obj.mergedInto)) {
                    const allChainLinks = editor.getAllMergedLinks(obj);
                    for (const chainLink of allChainLinks) {
                        if (chainLink.id === obj.id) continue;
                        if (chainLink.start && chainLink.end) {
                            let distToChainLink = Infinity;
                            
                    // Get chain link's rendered endpoints
                    let cStartX, cStartY, cEndX, cEndY;
                    if (chainLink._renderedEndpoints) {
                        cStartX = chainLink._renderedEndpoints.startX;
                        cStartY = chainLink._renderedEndpoints.startY;
                        cEndX = chainLink._renderedEndpoints.endX;
                        cEndY = chainLink._renderedEndpoints.endY;
                                } else {
                        cStartX = chainLink.start.x;
                        cStartY = chainLink.start.y;
                        cEndX = chainLink.end.x;
                        cEndY = chainLink.end.y;
                                }
                    
                    if (chainLink._cp1 && chainLink._cp2) {
                        distToChainLink = editor.distanceToCurvedLineWithControlPoints(
                            x, y, 
                            { x: cStartX, y: cStartY }, 
                            { x: cEndX, y: cEndY }, 
                            chainLink._cp1, chainLink._cp2
                        );
                            } else {
                        distToChainLink = editor.distanceToLine(x, y, { x: cStartX, y: cStartY }, { x: cEndX, y: cEndY });
                            }
                            minDistToLink = Math.min(minDistToLink, distToChainLink);
                        }
                    }
                }
                
        // Check if within clickable distance (include curve bonus for curved links)
        const effectiveMaxDistance = maxDistance + curveBonus;
        
        // ENHANCED: Return the actual distance if within range, or -1 if not
        // This allows findObjectAt to find the CLOSEST link when multiple links overlap
        if (minDistToLink <= effectiveMaxDistance) {
            return minDistToLink; // Return actual distance for comparison
        }
        return -1; // Not within range
    },
    
    findRotationHandle(editor, device, x, y) {
        // Check if click is on the rotation handle at bottom-right corner
        // Bottom-right corner angle: -Math.PI/4 (or 315 degrees, -45 degrees)
        const deviceRotation = (device.rotation || 0) * Math.PI / 180;
        
        // Handle logic for Text objects vs Devices
        let handleX, handleY;
        
        if (device.type === 'text') {
            // Text objects: rotation handle is top-right corner of bounding box
            // We need to calculate the bounding box based on text content
            const fontFamily = device.fontFamily || editor.defaultFontFamily || 'Inter, sans-serif';
            editor.ctx.font = `${device.fontSize}px ${fontFamily}`;
            const metrics = editor.ctx.measureText(device.text || 'Text');
            const w = metrics.width;
            const h = parseInt(device.fontSize);
            
            // Unrotated top-right corner relative to center
            const localX = w/2 + 5;
            const localY = -h/2 - 5;
            
            // Rotate the point
            handleX = device.x + (localX * Math.cos(deviceRotation) - localY * Math.sin(deviceRotation));
            handleY = device.y + (localX * Math.sin(deviceRotation) + localY * Math.cos(deviceRotation));
        } else {
            // Devices: rotation handle at TOP-RIGHT of device
            // UPDATED: Handles now scale with device size (no cap)
            const handleOffset = 15 / editor.zoom; // Offset beyond edge
            const bounds = editor.getDeviceBounds(device);
            // Use actual device bounds - handles follow the edge at any size
            const halfW = bounds.width / 2;
            const halfH = bounds.height / 2;
            // Local coords: top-right corner with offset
            const localX = halfW + handleOffset;
            const localY = -(halfH + handleOffset); // Negative because top is above center
            // Rotate to world coords
            handleX = device.x + localX * Math.cos(deviceRotation) - localY * Math.sin(deviceRotation);
            handleY = device.y + localX * Math.sin(deviceRotation) + localY * Math.cos(deviceRotation);
        }
        
        // Check if click is within hitbox (scaled with zoom for consistent screen size)
        // ENHANCED: Larger hitbox (20px) for easier clicking
        const hitboxSize = 20 / editor.zoom; // 20px in screen space
        const dist = Math.sqrt(Math.pow(x - handleX, 2) + Math.pow(y - handleY, 2));
        
        if (dist < hitboxSize) {
            return true;
        }
        return false;
    },
    
    /**
     * Find which text handle the mouse is over (for cursor feedback)
     * Returns: { type: 'rotation'|'resize', cursor: 'grab'|'nwse-resize'|etc, corner: 0-3 } or null
     */
    findTextHandle(editor, textObj, x, y) {
        if (!textObj || textObj.type !== 'text') return null;
        
        // Calculate text dimensions - MUST match drawing font exactly (including multiline)
        editor.ctx.save();
        const fontFamily = textObj.fontFamily || 'Arial';
        const fontWeight = textObj.fontWeight || 'normal';
        const fontStyle = textObj.fontStyle || 'normal';
        const fontSize = parseInt(textObj.fontSize) || 14;
        editor.ctx.font = `${fontStyle} ${fontWeight} ${fontSize}px ${fontFamily}`;
        
        // Handle multiline text - same calculation as drawText
        const textContent = textObj.text || 'Text';
        const lines = textContent.split('\n');
        const lineHeight = fontSize * 1.3; // Match drawText line-height
        
        let maxWidth = 0;
        for (const line of lines) {
            const metrics = editor.ctx.measureText(line || ' ');
            maxWidth = Math.max(maxWidth, metrics.width);
        }
        const w = maxWidth;
        const h = lines.length * lineHeight;
        editor.ctx.restore();
        
        const effRotH = editor.getEffectiveTextRotation ? editor.getEffectiveTextRotation(textObj) : (textObj.rotation || 0);
        const angle = effRotH * Math.PI / 180;
        const handleOffset = 8;
        
        // Define all corner handles with their cursor types
        const corners = [
            { x: -w/2 - handleOffset, y: -h/2 - handleOffset, type: 'resize', cursor: 'nwse-resize' },  // Top-left
            { x: w/2 + handleOffset, y: -h/2 - handleOffset, type: 'rotation', cursor: 'grab' },       // Top-right (rotation)
            { x: w/2 + handleOffset, y: h/2 + handleOffset, type: 'resize', cursor: 'nwse-resize' },   // Bottom-right
            { x: -w/2 - handleOffset, y: h/2 + handleOffset, type: 'resize', cursor: 'nesw-resize' }   // Bottom-left
        ];
        
        // PIXEL-ACCURATE: Match hitbox to visual handle size (handleSize from drawText)
        const handleSize = Math.max(6, Math.min(10, 8 / editor.zoom));
        const hitboxSize = handleSize + 4; // Small tolerance for easier clicking
        
        for (let i = 0; i < corners.length; i++) {
            const corner = corners[i];
            // Transform corner to world coordinates (accounting for text rotation)
            const rotatedX = corner.x * Math.cos(angle) - corner.y * Math.sin(angle);
            const rotatedY = corner.x * Math.sin(angle) + corner.y * Math.cos(angle);
            const handleWorldX = textObj.x + rotatedX;
            const handleWorldY = textObj.y + rotatedY;
            
            const dx = x - handleWorldX;
            const dy = y - handleWorldY;
            const dist = Math.sqrt(dx * dx + dy * dy);
            
            if (dist < hitboxSize) {
                return { type: corner.type, cursor: corner.cursor, corner: i };
            }
        }
        
        return null;
    },
    
    // Check if click is on a device's terminal button
    findTerminalButton(editor, device, x, y) {
        if (!device || device.type !== 'device') return false;
        // Check for either sshConfig.host or legacy deviceAddress
        const hasSSHConfig = device.sshConfig?.host || (device.deviceAddress && device.deviceAddress.trim() !== '');
        if (!hasSSHConfig) return false;
        if (!device._terminalBtnPos) return false;
        
        const btn = device._terminalBtnPos;
        const dist = Math.sqrt(Math.pow(x - btn.x, 2) + Math.pow(y - btn.y, 2));
        
        // Use MUCH larger hitbox for guaranteed easy clicking (2x visual radius)
        // SSH button has ABSOLUTE click priority, so larger hitbox is safe
        const hitboxRadius = btn.radius * 2.0;
        return dist <= hitboxRadius;
    },
    
    // Open terminal (SSH) to device
    async openTerminalToDevice(editor, device) {
        try {
            // Get SSH config - support both new sshConfig and legacy deviceAddress
            const sshConfig = device.sshConfig || {};
            let host = sshConfig.host || '';
            let user = sshConfig.user || 'dnroot';
            let password = sshConfig.password || 'dnroot';
        
        // Fallback chain for host:
        // 1. sshConfig.host (primary - mgmt IP)
        // 2. sshConfig.hostBackup (backup - serial number)
        // 3. device.deviceSerial (from DNAAS discovery)
        // 4. device.deviceAddress (legacy format)
        if (!host && sshConfig.hostBackup) {
            host = sshConfig.hostBackup;
            if (editor.debugger) {
                editor.debugger.logInfo(`Using backup host (SN): ${host}`);
            }
        }
        
        if (!host && device.deviceSerial) {
            host = device.deviceSerial;
            if (editor.debugger) {
                editor.debugger.logInfo(`Using deviceSerial as host: ${host}`);
            }
        }
        
        // Fallback to legacy deviceAddress
        if (!host && device.deviceAddress) {
            const address = device.deviceAddress.trim();
            if (address.includes('@')) {
                const parts = address.split('@');
                user = parts[0];
                host = parts[1];
            } else {
                host = address;
            }
        }
        
        if (!host) {
            if (editor.debugger) {
                editor.debugger.logWarning('Cannot open terminal: No device address set');
            }
            editor.showNotification('No SSH address configured. Right-click device → Set SSH Address', 'warning');
            return;
        }
        
        // CRITICAL: Check if host is a valid SSH target (IP or simple hostname without special chars)
        const isIPAddress = /^\d+\.\d+\.\d+\.\d+$/.test(host);
        const isValidSshHost = /^[a-zA-Z0-9._-]+$/.test(host) || isIPAddress;
        
        if (!isIPAddress && isValidSshHost) {
            try {
                const lookupName = device.label || host;
                if (typeof ScalerAPI !== 'undefined' && ScalerAPI.getDevice) {
                    const resolved = await ScalerAPI.getDevice(lookupName);
                    if (resolved && resolved.ip) {
                        console.log(`[Terminal] Resolved "${host}" -> "${resolved.ip}" via Network Mapper`);
                        const oldHost = host;
                        host = resolved.ip;
                        device.sshConfig = device.sshConfig || {};
                        device.sshConfig.host = resolved.ip;
                        device.sshConfig.hostBackup = oldHost;
                        if (resolved.serial) device.deviceSerial = resolved.serial;
                    }
                }
            } catch (e) {
                console.warn('[Terminal] Could not resolve device IP:', e.message);
            }
        }
        
        if (!isValidSshHost) {
            console.warn(`[Terminal] Invalid SSH host: "${host}" - contains special characters`);
            
            // First, try to find an IP address in the sshConfig or device properties
            // These are more reliable than hostnames
            const altHosts = [
                sshConfig.hostBackup,
                device.deviceSerial,
                device.sshConfig?.managedDeviceIp,
            ].filter(h => h && /^\d+\.\d+\.\d+\.\d+$/.test(h) || /^[a-z0-9]+$/i.test(h));
            
            if (altHosts.length > 0) {
                host = altHosts[0];
                console.log(`[Terminal] Using alternative host: "${host}"`);
            } else {
                // Fallback: Try to extract just the hostname part before any parentheses/date suffix
                const cleanHost = host.split('(')[0].trim();
                if (cleanHost && cleanHost !== host && /^[a-zA-Z0-9._-]+$/.test(cleanHost)) {
                    console.log(`[Terminal] Cleaned host: "${cleanHost}"`);
                    host = cleanHost;
                } else {
                    editor.showNotification(`Invalid SSH host: "${host}". Right-click → Set SSH Address with a valid IP.`, 'error');
                    return;
                }
            }
        }
        
        // Build SSH command
        const sshCommand = `ssh ${user}@${host}`;
        
        if (editor.debugger) {
            editor.debugger.logInfo(`🖥️ Opening terminal to ${device.label || 'Device'}: ${sshCommand}`);
        }
        
        // Detect operating system
        const ua = navigator.userAgent;
        const isMac = /Mac|iPhone|iPod|iPad/.test(ua);
        const isLinux = /Linux/.test(ua) && !(/Android/.test(ua));
        
        // Linux: Just copy the SSH command - _openSshUrl handles the rest
        if (isLinux) {
            const sshUrl = `ssh://${user}@${host}`;
            editor._openSshUrl(sshUrl);
            
            // CRITICAL FIX (Jan 2026): Do NOT delay password copy - it interferes with
            // subsequent SSH operations. Instead, show password in notification immediately.
            if (password) {
                // Show password visibly in notification so user can see it
                // No clipboard copy - that would overwrite the SSH command we just copied!
                editor.showNotification(`🔑 Password: ${password}`, 'info', 10000); // Show for 10 seconds
            }
            return;
        }
        
        // macOS: Use iTerm integration with ssh:// URL scheme
        // SIMPLIFIED (Jan 2026): Always open new window - no complex session tracking
        const sshUrl = `ssh://${user}@${host}`;
        editor._openSshUrl(sshUrl);
        
        if (password) {
            editor._safeClipboardWrite(password).catch(() => {});
            editor.showNotification(`🖥️ Terminal opened to ${device.label || host}! Password copied (⌘V)`, 'success');
        } else {
            editor.showNotification(`🖥️ Terminal opened: ${sshCommand}`, 'success');
        }
        } catch (error) {
            console.error('[Terminal] Error opening terminal:', error);
            editor.showNotification(`Terminal error: ${error.message}`, 'error');
        }
    },
    
    // Safe clipboard write that works on HTTP (non-HTTPS) contexts
    _safeClipboardWrite(text) {
        // Try modern clipboard API first (requires HTTPS or localhost)
        if (navigator.clipboard && navigator.clipboard.writeText) {
            return navigator.clipboard.writeText(text).catch((err) => {
                console.warn('[Clipboard] Modern API failed:', err);
                return this._legacyClipboardWrite(text);
            });
        }
        // Fallback to legacy method
        return this._legacyClipboardWrite(text);
    },
    
    _legacyClipboardWrite(text) {
        return new Promise((resolve, reject) => {
            try {
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.style.cssText = 'position:fixed;left:-9999px;top:-9999px;opacity:0';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                const success = document.execCommand('copy');
                document.body.removeChild(textArea);
                if (success) {
                    resolve();
                } else {
                    reject(new Error('execCommand failed'));
                }
            } catch (e) {
                reject(e);
            }
        });
    },
    
    _openSshUrl(editor, url) {
        try {
            // Detect operating system
            const ua = navigator.userAgent;
            const isMac = /Mac|iPhone|iPod|iPad/.test(ua);
            const isLinux = /Linux/.test(ua) && !(/Android/.test(ua));
            
            console.log(`[Terminal] _openSshUrl called, isLinux: ${isLinux}, isMac: ${isMac}, url: ${url}`);
            
            if (isLinux) {
                // Linux: Try multiple approaches to open a new terminal window
                const sshMatch = url.match(/ssh:\/\/(.+)/) || url.match(/iterm-ssh:\/\/(.+)/);
                if (sshMatch) {
                    const sshCommand = `ssh ${sshMatch[1]}`;
                    console.log(`[Terminal] Linux detected, SSH command: ${sshCommand}`);
                    
                    // ENHANCED (Jan 2026): Try to actually open a terminal window
                    // Method 1: Try x-terminal-emulator (Debian/Ubuntu default)
                    // Method 2: Try gnome-terminal
                    // Method 3: Copy to clipboard as fallback
                    
                    // Try opening via custom URL scheme first (if xdg-open is configured)
                    // Some Linux distros support ssh:// URLs
                    const testLink = document.createElement('a');
                    testLink.href = url;
                    testLink.target = '_blank';
                    testLink.style.display = 'none';
                    document.body.appendChild(testLink);
                    
                    // Use window.open with a unique window name to force new window
                    const windowName = `ssh_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
                    const newWindow = window.open(url, windowName, 'noopener,noreferrer');
                    
                    document.body.removeChild(testLink);
                    
                    // Also copy command to clipboard as backup
                    editor._safeClipboardWrite(sshCommand).then(() => {
                        if (newWindow) {
                            editor.showNotification(`🖥️ Terminal opening... Command also copied to clipboard`, 'success');
                        } else {
                            editor.showNotification(`📋 SSH command copied! Paste in terminal: ${sshCommand}`, 'success');
                        }
                    }).catch((err) => {
                        console.warn('[Terminal] Clipboard write failed:', err);
                        editor.showNotification(`🖥️ Run in terminal: ${sshCommand}`, 'info');
                    });
                } else {
                    console.warn('[Terminal] Could not parse SSH URL:', url);
                    editor.showNotification(`Could not parse SSH URL`, 'error');
                }
                return;
            }
            
            // macOS: Trigger ssh:// URL scheme to open iTerm/Terminal
            console.log(`[Terminal] Opening SSH URL for macOS: ${url}`);
            
            const sshMatch = url.match(/ssh:\/\/([^@]+)@(.+)/);
            const sshCommand = sshMatch ? `ssh ${sshMatch[1]}@${sshMatch[2]}` : url;
            
            // Use an anchor element with click() -- avoids Chrome's iframe credential block
            // and reliably triggers the OS URL scheme handler (iTerm, Terminal.app)
            try {
                const link = document.createElement('a');
                link.href = url;
                link.style.display = 'none';
                document.body.appendChild(link);
                link.click();
                setTimeout(() => {
                    if (document.body.contains(link)) document.body.removeChild(link);
                }, 200);
                console.log(`[Terminal] Triggered URL scheme via anchor click: ${url}`);
            } catch (e) {
                console.warn('[Terminal] Anchor click failed, trying window.open:', e);
                window.open(url, '_blank', 'noopener,noreferrer');
            }
            
            // Copy SSH command to clipboard as reliable fallback
            editor._safeClipboardWrite(sshCommand).then(() => {
                editor.showNotification(`Terminal opening to ${sshMatch ? sshMatch[2] : url}. Command also copied.`, 'success', 5000);
            }).catch(() => {
                editor.showNotification(`Run: ${sshCommand}`, 'info', 8000);
            });
        } catch (error) {
            console.error('[Terminal] Error in _openSshUrl:', error);
            editor.showNotification(`SSH error: ${error.message}`, 'error');
        }
    },
    

};

console.log('[topology-object-detection.js] ObjectDetection loaded');
