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
                    // When an unbound link and a Quick Link hit at similar distances,
                    // prefer the unbound link since QLs follow their devices automatically
                    // and the user likely wants to interact with the UL.
                    const ulBonus = obj.type === 'unbound' ? 2 / editor.zoom : 0;
                    const adjustedDist = hitDistance - ulBonus;
                    if (!closestLink || adjustedDist < closestLinkDistance) {
                        closestLink = obj;
                        closestLinkDistance = adjustedDist;
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
        
        // SELECTION STICKINESS: When the selected object is a link and the click is
        // in its general vicinity, prefer it over other overlapping links. This prevents
        // accidental selection changes when a newly created UL overlaps with an
        // existing link at the same position (e.g., both pass through viewport center).
        // Uses a 12px bounding-box margin for both link types (symmetric behavior).
        if (closestLink && editor.selectedObject &&
            (editor.selectedObject.type === 'link' || editor.selectedObject.type === 'unbound') &&
            editor.selectedObject !== closestLink) {
            const sel = editor.selectedObject;
            let nearSelected = false;
            // Newly created links (within 2s) get stronger stickiness to prevent accidental switch
            const createdTs = sel._createdAt ?? sel.createdAt;
            const isRecentlyCreated = createdTs && (Date.now() - createdTs) < 2000;
            const margin = (isRecentlyCreated ? 20 : 12) / editor.zoom;
            let sx, sy, ex, ey;
            if (sel.type === 'unbound' && sel.start && sel.end) {
                sx = sel.start.x; sy = sel.start.y; ex = sel.end.x; ey = sel.end.y;
                const minX = Math.min(sx, ex) - margin;
                const maxX = Math.max(sx, ex) + margin;
                const minY = Math.min(sy, ey) - margin;
                const maxY = Math.max(sy, ey) + margin;
                nearSelected = (x >= minX && x <= maxX && y >= minY && y <= maxY);
            } else if (sel._renderedEndpoints) {
                sx = sel._renderedEndpoints.startX; sy = sel._renderedEndpoints.startY;
                ex = sel._renderedEndpoints.endX; ey = sel._renderedEndpoints.endY;
                const minX = Math.min(sx, ex) - margin;
                const maxX = Math.max(sx, ex) + margin;
                const minY = Math.min(sy, ey) - margin;
                const maxY = Math.max(sy, ey) + margin;
                nearSelected = (x >= minX && x <= maxX && y >= minY && y <= maxY);
            } else if (editor.getLinkRenderedEndpoints && editor.getLinkRenderedEndpoints(sel)) {
                const ep = editor.getLinkRenderedEndpoints(sel);
                sx = ep.startX; sy = ep.startY; ex = ep.endX; ey = ep.endY;
                const minX = Math.min(sx, ex) - margin;
                const maxX = Math.max(sx, ex) + margin;
                const minY = Math.min(sy, ey) - margin;
                const maxY = Math.max(sy, ey) + margin;
                nearSelected = (x >= minX && x <= maxX && y >= minY && y <= maxY);
            } else {
                nearSelected = editor._checkLinkHit(x, y, sel) >= 0;
            }
            
            if (nearSelected) {
                closestLink = sel;
                closestLinkDistance = 0;
            }
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
        const hasSSHConfig = device.sshConfig?.host || device.sshConfig?.hostBackup || device.deviceSerial || (device.deviceAddress && device.deviceAddress.trim() !== '');
        if (!hasSSHConfig) return false;
        if (!device._terminalBtnPos) return false;
        
        const btn = device._terminalBtnPos;
        const dist = Math.sqrt(Math.pow(x - btn.x, 2) + Math.pow(y - btn.y, 2));
        
        // Use MUCH larger hitbox for guaranteed easy clicking (2x visual radius)
        // SSH button has ABSOLUTE click priority, so larger hitbox is safe
        const hitboxRadius = btn.radius * 2.0;
        return dist <= hitboxRadius;
    },
    
    /**
     * Show a recovery modal when device IP can't be resolved.
     * Offers: manual IP entry, console discovery, open SSH config dialog.
     * Returns resolved IP string, or null to abort.
     */
    async _showTerminalRecoveryModal(editor, device, failedHost) {
        return new Promise((resolve) => {
            const deviceId = device.label || device.id || failedHost;
            const serial = device.deviceSerial || device.serial || '';
            const mode = device._deviceMode || '';
            const cachedIp = device.sshConfig?.managedDeviceIp || device.sshConfig?.hostBackup || '';
            const cachedIsIP = cachedIp && /^\d+\.\d+\.\d+\.\d+$/.test(cachedIp);

            const isDark = document.body.classList.contains('dark-mode') ||
                window.matchMedia?.('(prefers-color-scheme: dark)').matches;
            const bg = isDark ? 'rgba(30,35,50,0.97)' : 'rgba(255,255,255,0.97)';
            const text = isDark ? '#e0e0e0' : '#1a1a2e';
            const border = isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.1)';
            const accent = '#e67e22';
            const inputBg = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)';

            const overlay = document.createElement('div');
            overlay.style.cssText = 'position:fixed;inset:0;z-index:100000;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.5);';

            const modeBadge = mode && mode !== 'unknown'
                ? `<span style="background:${mode === 'DNOS' ? '#27ae60' : mode === 'GI' ? '#f39c12' : '#e74c3c'};color:#fff;padding:2px 8px;border-radius:4px;font-size:10px;margin-left:6px;">${mode}</span>`
                : '';

            overlay.innerHTML = `
                <div style="background:${bg};border:1px solid ${border};border-radius:12px;padding:20px 24px;max-width:440px;width:90%;color:${text};font-family:system-ui;box-shadow:0 20px 60px rgba(0,0,0,0.3);">
                    <div style="font-size:14px;font-weight:600;margin-bottom:12px;display:flex;align-items:center;gap:6px;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="${accent}" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                        Cannot Resolve Device IP${modeBadge}
                    </div>
                    <div style="font-size:12px;margin-bottom:14px;color:${isDark ? '#aaa' : '#666'};">
                        <strong>${deviceId}</strong> could not be resolved to an IP address.
                        ${serial ? 'Serial: ' + serial : ''}
                        ${mode === 'GI' || mode === 'RECOVERY' ? '<br>Device may be in ' + mode + ' mode -- SSH may be unavailable.' : ''}
                    </div>
                    <div style="margin-bottom:10px;">
                        <label style="font-size:11px;color:${isDark ? '#999' : '#777'};display:block;margin-bottom:4px;">Management IP address:</label>
                        <input id="_trm_ip_input" type="text" placeholder="e.g. 100.64.4.98"
                            value="${cachedIsIP ? cachedIp : ''}"
                            style="width:100%;box-sizing:border-box;padding:8px 10px;border-radius:6px;border:1px solid ${border};background:${inputBg};color:${text};font-size:13px;outline:none;" />
                    </div>
                    <div id="_trm_status" style="font-size:11px;min-height:18px;margin-bottom:10px;color:${isDark ? '#888' : '#999'};"></div>
                    <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px;">
                        <button id="_trm_discover" style="padding:5px 10px;font-size:11px;border-radius:5px;border:1px solid ${border};background:${inputBg};color:${text};cursor:pointer;">Discover Console</button>
                        <button id="_trm_ssh_dialog" style="padding:5px 10px;font-size:11px;border-radius:5px;border:1px solid ${border};background:${inputBg};color:${text};cursor:pointer;">SSH Config</button>
                    </div>
                    <div style="display:flex;gap:8px;justify-content:flex-end;">
                        <button id="_trm_cancel" style="padding:6px 14px;border-radius:6px;border:1px solid ${border};background:${inputBg};color:${text};font-size:12px;cursor:pointer;">Cancel</button>
                        <button id="_trm_connect" style="padding:6px 16px;border-radius:6px;border:none;background:linear-gradient(135deg,${accent},#d35400);color:#fff;font-size:12px;cursor:pointer;font-weight:500;">Connect</button>
                    </div>
                </div>`;

            document.body.appendChild(overlay);

            const ipInput = overlay.querySelector('#_trm_ip_input');
            const statusEl = overlay.querySelector('#_trm_status');
            const connectBtn = overlay.querySelector('#_trm_connect');
            const cancelBtn = overlay.querySelector('#_trm_cancel');
            const discoverBtn = overlay.querySelector('#_trm_discover');
            const sshDialogBtn = overlay.querySelector('#_trm_ssh_dialog');

            const cleanup = () => { if (overlay.parentNode) overlay.remove(); };

            cancelBtn.addEventListener('click', () => { cleanup(); resolve(null); });
            overlay.addEventListener('click', (e) => { if (e.target === overlay) { cleanup(); resolve(null); } });

            connectBtn.addEventListener('click', () => {
                const ip = (ipInput.value || '').trim();
                if (!ip) {
                    statusEl.textContent = 'Enter a valid IP address or hostname.';
                    statusEl.style.color = '#e74c3c';
                    return;
                }
                cleanup();
                resolve(ip);
            });

            ipInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') connectBtn.click();
                if (e.key === 'Escape') { cleanup(); resolve(null); }
            });
            const _escHandler = (e) => { if (e.key === 'Escape') { cleanup(); resolve(null); } };
            document.addEventListener('keydown', _escHandler);
            const _origCleanup = cleanup;
            cleanup = () => { document.removeEventListener('keydown', _escHandler); _origCleanup(); };

            discoverBtn.addEventListener('click', async () => {
                if (typeof ScalerAPI === 'undefined' || !ScalerAPI.discoverConsole) {
                    statusEl.textContent = 'Console discovery not available.';
                    statusEl.style.color = '#e74c3c';
                    return;
                }
                discoverBtn.textContent = 'Discovering...';
                discoverBtn.disabled = true;
                try {
                    const r = await ScalerAPI.discoverConsole(deviceId, serial, ipInput.value?.trim());
                    let msg = '';
                    if (r.console_server) msg += `Console: ${r.console_server} port ${r.port || '?'} (${r.source || '?'})`;
                    if (r.pdu_entries?.length) msg += ` | PDU: ${r.pdu_entries[0].pdu} outlet ${r.pdu_entries[0].outlet}`;
                    if (!msg) msg = 'No console mapping found.';
                    statusEl.textContent = msg;
                    statusEl.style.color = r.console_server ? '#27ae60' : '#e67e22';
                } catch (e) {
                    statusEl.textContent = `Discovery failed: ${e.message}`;
                    statusEl.style.color = '#e74c3c';
                } finally {
                    discoverBtn.textContent = 'Discover Console';
                    discoverBtn.disabled = false;
                }
            });

            sshDialogBtn.addEventListener('click', () => {
                cleanup();
                resolve(null);
                if (typeof window.showSSHAddressDialog === 'function') {
                    window.showSSHAddressDialog(editor, device);
                } else if (editor.showSSHAddressDialog) {
                    editor.showSSHAddressDialog(device);
                } else {
                    editor.showNotification('[INFO] Right-click device > Set SSH Address', 'info');
                }
            });

            setTimeout(() => ipInput.focus(), 100);
        });
    },

    // Open terminal (SSH) to device -- iTerm preferred, web terminal as fallback
    async openTerminalToDevice(editor, device) {
        try {
            if (editor.hideDeviceSelectionToolbar) editor.hideDeviceSelectionToolbar();

            const sshConfig = device.sshConfig || {};
            let host = sshConfig._userSavedHost || sshConfig.host || '';
            let user = sshConfig._userSavedUser || sshConfig.user || 'dnroot';
            let password = sshConfig._userSavedPass || sshConfig.password || 'dnroot';
            let isCluster = sshConfig._isCluster || false;
            let virshCmd = sshConfig._virshCmd || '';

            if (!host) host = sshConfig.hostBackup || '';
            if (!host) host = device.deviceSerial || '';
            if (!host && device.deviceAddress) {
                const addr = device.deviceAddress.trim();
                if (addr.includes('@')) { user = addr.split('@')[0]; host = addr.split('@')[1]; }
                else host = addr;
            }
            if (!host) {
                const recovered = await this._showTerminalRecoveryModal(editor, device, device.label || 'unknown');
                if (!recovered) return;
                host = recovered;
                device.sshConfig = device.sshConfig || {};
                device.sshConfig.host = host;
            }

            const _devMode = (device._deviceMode || '').toUpperCase();
            console.log(`[SSH] Start: label=${device.label}, host=${host}, cluster=${isCluster}, mode=${_devMode}`);

            // ===== ALWAYS: if host is set, open iTerm directly (any mode) =====
            if (host) {
                console.log(`[SSH] iTerm direct: ssh://${user}@${host} (mode=${_devMode})`);
                this._pendingPassword = password;
                editor._openSshUrl(`ssh://${user}@${host}`);
                return;
            }

            // ===== NO HOST: fallback paths =====
            const _isRecoveryMode = _devMode === 'GI' || _devMode === 'RECOVERY';

            // Try enriched/cached IPs before probing
            if (!_isRecoveryMode) {
                let iTermHost = sshConfig._enrichedMgmtIp || sshConfig._nccMgmtIp || null;
                if (iTermHost) {
                    console.log(`[SSH] iTerm (cached): ssh://${user}@${iTermHost}`);
                    this._pendingPassword = password;
                    editor._openSshUrl(`ssh://${user}@${iTermHost}`);
                    return;
                }
            }

            // ===== CLUSTER INSTANT (GI/RECOVERY, no host): try NCC mgmt, then virsh console =====
            if (isCluster && virshCmd) {
                const vi = sshConfig._virshInfo || {};
                const kvmHost = vi.kvmHost || (/^\d+\.\d+\.\d+\.\d+$/.test(host) ? host : '');
                const hasNccInfo = (vi.nccVms && vi.nccVms.length > 0) || vi.activeNcc;
                const openedIterm = await this._tryOpenClusterNccMgmtIterm(editor, device, sshConfig);
                if (openedIterm) return;
                if (kvmHost && hasNccInfo && typeof window.TerminalPanel !== 'undefined' && window.TerminalPanel.open) {
                    console.log(`[SSH] CLUSTER INSTANT -> web terminal virsh: kvm=${kvmHost}, activeNcc=${vi.activeNcc}`);
                    window.TerminalPanel.open({
                        deviceId: device.label || device.id || '', host: kvmHost,
                        method: 'virsh_console',
                        deviceLabel: `${device.label || 'Cluster'} (NCC ${vi.activeNcc || 'console'})`,
                        password: vi.kvmPass || 'drive1234!', user: vi.kvmUser || 'dn',
                        virshInfo: {
                            kvmHost, kvmUser: vi.kvmUser || 'dn', kvmPass: vi.kvmPass || 'drive1234!',
                            nccVms: vi.nccVms || [], activeNcc: vi.activeNcc || '',
                        },
                    });
                    this._fireBackgroundNccDiscovery(editor, device, {
                        kvmHost,
                        kvmUser: vi.kvmUser || 'dn',
                        kvmPass: vi.kvmPass || 'drive1234!',
                        nccVms: vi.nccVms || [],
                        activeNcc: vi.activeNcc || '',
                    });
                    editor.showNotification(`[OK] Connecting to ${device.label} NCC via virsh console...`, 'success', 5000);
                    return;
                }
                console.log('[SSH] Cluster but missing KVM IP or NCC info, falling to probe');
            }

            // ===== STANDALONE INSTANT: host is an IP and NOT a cluster → iTerm =====
            if (/^\d+\.\d+\.\d+\.\d+$/.test(host) && !isCluster) {
                console.log(`[SSH] INSTANT iTerm: ssh://${user}@${host}`);
                this._pendingPassword = password;
                editor._openSshUrl(`ssh://${user}@${host}`);
                if (typeof ScalerAPI !== 'undefined' && ScalerAPI.probeConnection) {
                    ScalerAPI.probeConnection(device.label || host, host).then(r => {
                        if (r.device_state) device._deviceMode = r.device_state;
                        this._updateClusterInfo(device, r);
                    }).catch(() => {});
                }
                return;
            }

            // ===== PROBE PATH =====
            let bestIP = null;
            let nccHost = null;
            let clusterInfo = null;

            if (typeof ScalerAPI !== 'undefined' && ScalerAPI.probeConnection) {
                try {
                    const probeHost = /^\d+\.\d+\.\d+\.\d+$/.test(host) ? host : '';
                    const result = await ScalerAPI.probeConnection(device.label || host, probeHost);
                    const reachable = (result.methods || []).filter(m => m.reachable);
                    console.log(`[SSH] Probe: ${reachable.length} reachable, state=${result.device_state}`);

                    if (reachable.length === 0) {
                        editor.showNotification(`[WARN] ${device.label || host}: No method reachable.`, 'warning', 6000);
                        return;
                    }

                    if (result.device_state) device._deviceMode = result.device_state;
                    const probeMode = (result.device_state || _devMode || '').toUpperCase();

                    // For clusters: find the NCC SSH entry (ssh_ncc)
                    const nccEntry = reachable.find(m => m.method === 'ssh_ncc');
                    if (nccEntry) nccHost = nccEntry.host;

                    // Best reachable IP from non-virsh SSH methods
                    const ipEntry = reachable.find(m =>
                        m.method !== 'virsh_console' && m.method !== 'console' &&
                        /^\d+\.\d+\.\d+\.\d+$/.test(m.host)
                    );
                    if (ipEntry) bestIP = ipEntry.host;

                    // Detect cluster
                    const virshEntry = reachable.find(m => m.method === 'virsh_console');
                    if (result.cluster?.is_cluster || (virshEntry && (virshEntry.ncc_vms?.length > 0 || virshEntry.vms_running?.length > 0))) {
                        if (virshEntry) {
                            const kvmCreds = virshEntry.kvm_credentials || {};
                            const activeNcc = (virshEntry.vms_running?.[0]) || (virshEntry.ncc_vms || [])[0] || '';
                            clusterInfo = {
                                kvmHost: virshEntry.host,
                                kvmUser: kvmCreds.username || 'dn',
                                kvmPass: kvmCreds.password || '',
                                activeNcc,
                                nccVms: virshEntry.ncc_vms || [],
                                virshCmd: activeNcc ? `sudo virsh console --force ${activeNcc}` : '',
                            };
                        }
                    }

                    if (result.ncc_mgmt_ip && /^\d+\.\d+\.\d+\.\d+$/.test(String(result.ncc_mgmt_ip).trim())) {
                        device.sshConfig = device.sshConfig || {};
                        device.sshConfig._nccMgmtIp = String(result.ncc_mgmt_ip).trim();
                    }
                    this._updateClusterInfo(device, result);
                } catch (e) {
                    console.warn('[SSH] Probe failed:', e.message);
                }
            }

            const probeMode = (device._deviceMode || _devMode || '').toUpperCase();
            console.log(`[SSH] After probe: host=${host}, bestIP=${bestIP}, nccHost=${nccHost}, cluster=${!!clusterInfo}, mode=${probeMode}`);

            // ===== NON-GI/RECOVERY (from probe): direct SSH via iTerm =====
            const _probeRecovery = probeMode === 'GI' || probeMode === 'RECOVERY';
            if (!_probeRecovery) {
                const dnosIP = bestIP || (/^\d+\.\d+\.\d+\.\d+$/.test(host) ? host : null);
                if (dnosIP) {
                    console.log(`[SSH] PROBE -> iTerm (mode=${probeMode||'default'}): ssh://${user}@${dnosIP}`);
                    this._pendingPassword = password;
                    editor._openSshUrl(`ssh://${user}@${dnosIP}`);
                    device.sshConfig = device.sshConfig || {};
                    device.sshConfig._nccMgmtIp = dnosIP;
                    return;
                }
            }

            // ===== CLUSTER (from probe, non-DNOS): try iTerm to NCC mgmt first, then virsh =====
            if (clusterInfo && clusterInfo.kvmHost && typeof window.TerminalPanel !== 'undefined' && window.TerminalPanel.open) {
                const openedProbe = await this._tryOpenClusterNccMgmtIterm(editor, device, device.sshConfig || sshConfig);
                if (openedProbe) return;
                if (bestIP && bestIP !== clusterInfo.kvmHost) {
                    console.log(`[SSH] PROBE CLUSTER -> iTerm via NCC IP: ${bestIP}`);
                    this._pendingPassword = 'dnroot';
                    editor._openSshUrl(`ssh://dnroot@${bestIP}`);
                    device.sshConfig = device.sshConfig || {};
                    device.sshConfig._nccMgmtIp = bestIP;
                    editor.showNotification(`[OK] iTerm to NCC ${bestIP}`, 'success', 4000);
                    return;
                }
                console.log(`[SSH] PROBE CLUSTER -> web terminal virsh: kvm=${clusterInfo.kvmHost}, activeNcc=${clusterInfo.activeNcc}`);
                device.sshConfig = device.sshConfig || {};
                device.sshConfig._isCluster = true;
                device.sshConfig._virshCmd = clusterInfo.virshCmd;
                device.sshConfig._virshInfo = {
                    kvmHost: clusterInfo.kvmHost, kvmUser: clusterInfo.kvmUser, kvmPass: clusterInfo.kvmPass,
                    nccVms: clusterInfo.nccVms, activeNcc: clusterInfo.activeNcc,
                };
                window.TerminalPanel.open({
                    deviceId: device.label || device.id || '', host: clusterInfo.kvmHost,
                    method: 'virsh_console',
                    deviceLabel: `${device.label || 'Cluster'} (NCC ${clusterInfo.activeNcc || 'console'})`,
                    password: clusterInfo.kvmPass || 'drive1234!', user: clusterInfo.kvmUser || 'dn',
                    virshInfo: clusterInfo,
                });
                this._fireBackgroundNccDiscovery(editor, device, {
                    kvmHost: clusterInfo.kvmHost,
                    kvmUser: clusterInfo.kvmUser || 'dn',
                    kvmPass: clusterInfo.kvmPass || 'drive1234!',
                    nccVms: clusterInfo.nccVms || [],
                    activeNcc: clusterInfo.activeNcc || '',
                });
                editor.showNotification(`[OK] Connecting to ${device.label} NCC via virsh console...`, 'success', 5000);
                return;
            }

            // ===== STANDALONE: iTerm (got IP from probe) =====
            if (bestIP) {
                host = bestIP;
                device.sshConfig = device.sshConfig || {};
                device.sshConfig._nccMgmtIp = host;
            }
            if (/^\d+\.\d+\.\d+\.\d+$/.test(host)) {
                console.log(`[SSH] PROBE -> iTerm: ssh://${user}@${host}`);
                this._pendingPassword = password;
                editor._openSshUrl(`ssh://${user}@${host}`);
                return;
            }

            // ===== WEB TERMINAL (non-IP host, backend resolves) =====
            if (typeof window.TerminalPanel !== 'undefined' && window.TerminalPanel.open) {
                console.log(`[SSH] -> Web terminal: ${host}`);
                window.TerminalPanel.open({
                    deviceId: device.label || device.id || '', host,
                    user: user || 'dnroot', password: password || 'dnroot',
                    method: 'ssh_mgmt', deviceLabel: device.label || host || 'Device',
                });
                editor.showNotification(`[OK] Web terminal to ${device.label || host}`, 'success', 4000);
                return;
            }

            this._pendingPassword = password;
            editor._openSshUrl(`ssh://${user}@${host}`);
        } catch (error) {
            console.error('[SSH] Error:', error);
            editor.showNotification(`Terminal error: ${error.message}`, 'error');
        }
    },

    /**
     * If NCC mgmt IP answers on port 22, open iTerm (dnroot). Checks _nccMgmtIp first,
     * then falls back to sshConfig.host if it differs from the KVM host.
     */
    async _tryOpenClusterNccMgmtIterm(editor, device, sshConfig) {
        const cfg = sshConfig || device.sshConfig || {};
        const vi = cfg._virshInfo || {};
        const kvmHost = vi.kvmHost || '';
        const candidates = [];
        const nccIp = (cfg._nccMgmtIp || '').trim();
        if (nccIp && /^\d+\.\d+\.\d+\.\d+$/.test(nccIp)) candidates.push(nccIp);
        const hostIp = (cfg.host || '').trim();
        if (hostIp && /^\d+\.\d+\.\d+\.\d+$/.test(hostIp) && hostIp !== kvmHost && !candidates.includes(hostIp)) {
            candidates.push(hostIp);
        }
        if (candidates.length === 0) return false;
        if (typeof ScalerAPI === 'undefined' || !ScalerAPI.checkPort) return false;
        for (const ip of candidates) {
            try {
                const chk = await ScalerAPI.checkPort(ip, 22);
                if (chk && chk.reachable) {
                    this._pendingPassword = 'dnroot';
                    if (editor._openSshUrl) editor._openSshUrl(`ssh://dnroot@${ip}`);
                    device.sshConfig = device.sshConfig || {};
                    device.sshConfig._nccMgmtIp = ip;
                    if (editor.showNotification) {
                        editor.showNotification(`[OK] iTerm to NCC management ${ip}`, 'success', 4000);
                    }
                    return true;
                }
            } catch (e) {
                console.warn(`[SSH] checkPort NCC mgmt ${ip}:`, e && e.message);
            }
        }
        if (device.sshConfig) delete device.sshConfig._nccMgmtIp;
        return false;
    },

    /**
     * Fire-and-forget: discover NCC mgmt IP via virsh + show interfaces management (backend).
     */
    _fireBackgroundNccDiscovery(editor, device, virshInfo) {
        if (typeof ScalerAPI === 'undefined' || !ScalerAPI.discoverNccMgmtIp) return;
        const deviceId = device.label || device.id || '';
        const kvmHost = virshInfo.kvmHost || '';
        const kvmUser = virshInfo.kvmUser || 'dn';
        const kvmPass = virshInfo.kvmPass || '';
        const nccVms = virshInfo.nccVms || [];
        const activeNcc = virshInfo.activeNcc || '';
        if (!deviceId || !kvmHost || !kvmPass) return;
        ScalerAPI.discoverNccMgmtIp({
            deviceId, kvmHost, kvmUser, kvmPass, nccVms, activeNcc
        }).then((r) => {
            if (r.ssh_auth_ok && r.ncc_mgmt_ip) {
                device.sshConfig = device.sshConfig || {};
                device.sshConfig._nccMgmtIp = r.ncc_mgmt_ip;
                if (editor.showNotification) {
                    editor.showNotification(
                        `[OK] NCC management IP discovered: ${r.ncc_mgmt_ip} -- next SSH can use iTerm`,
                        'success',
                        7000
                    );
                }
            }
        }).catch((e) => console.warn('[SSH] background NCC mgmt discovery:', e && e.message));
    },

    _updateClusterInfo(device, probeResult) {
        if (!probeResult?.cluster?.is_cluster) return;
        const virshEntry = (probeResult.methods || []).find(m => m.method === 'virsh_console' && m.reachable);
        if (!virshEntry) return;
        const kvmCreds = virshEntry.kvm_credentials || {};
        const nccVms = virshEntry.ncc_vms || [];
        const activeNcc = (virshEntry.vms_running?.[0]) || nccVms[0] || '';
        const kvmHost = virshEntry.host || device.sshConfig?.host || '';
        device.sshConfig = device.sshConfig || {};
        device.sshConfig._isCluster = true;
        device.sshConfig._virshCmd = activeNcc ? `sudo virsh console --force ${activeNcc}` : '';
        const isDnos = (device._deviceMode || probeResult.device_state || '').toUpperCase() === 'DNOS';
        if (!isDnos && !device.sshConfig.user) {
            if (kvmCreds.username) device.sshConfig.user = kvmCreds.username;
            if (kvmCreds.password) device.sshConfig.password = kvmCreds.password;
        }
        device.sshConfig._virshInfo = {
            kvmHost,
            kvmUser: kvmCreds.username || 'dn',
            kvmPass: kvmCreds.password || '',
            nccVms,
            activeNcc,
        };
    },
    
    // Safe clipboard write that works on HTTP (non-HTTPS) contexts
    _safeClipboardWrite(text) {
        if (typeof window.safeClipboardWrite === 'function') {
            return window.safeClipboardWrite(text);
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
            return navigator.clipboard.writeText(text).catch((err) => {
                console.warn('[Clipboard] Modern API failed:', err);
                return this._legacyClipboardWrite(text);
            });
        }
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
        console.log(`[SSH] _openSshUrl: ${url}`);
        try {
            const sshMatch = url.match(/ssh:\/\/([^@]+)@(.+)/);
            const cmd = sshMatch ? `ssh ${sshMatch[1]}@${sshMatch[2]}` : url;

            // Anchor click is the correct way to trigger protocol handlers (ssh://)
            // window.open creates a blank tab instead of triggering the handler
            const link = document.createElement('a');
            link.href = url;
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            setTimeout(() => { try { link.remove(); } catch(_){} }, 300);
            console.log(`[SSH] Anchor click dispatched for: ${url}`);

            const password = this._pendingPassword || '';
            if (password) {
                this._safeClipboardWrite(password).then(() => {
                    editor.showNotification(`[OK] iTerm: ${cmd}. Password copied -- paste with Cmd+V.`, 'success', 5000);
                }).catch(() => {
                    editor.showNotification(`[OK] iTerm: ${cmd}. Password: ${password}`, 'info', 8000);
                });
            } else {
                editor.showNotification(`[OK] iTerm: ${cmd}`, 'success', 5000);
            }
            this._pendingPassword = null;
        } catch (error) {
            console.error('[SSH] _openSshUrl error:', error);
            editor.showNotification(`SSH error: ${error.message}`, 'error');
        }
    },
    

};

console.log('[topology-object-detection.js] ObjectDetection loaded');
