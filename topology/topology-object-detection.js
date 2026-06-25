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
            // Draw order: shape(-1) < link(0) < device(1) < text(2) < packet(3) → lower drawn first (behind)
            // Hit order: packet(5) > text(4) > device(3) > link(2) > shape(1) → higher checked first (on top)
            // Packets are scenario callouts that sit ABOVE the link in z-order
            // and must be selected first so users can drag/edit them even when
            // they overlap the cable they describe.
            const typeOrder = { 'packet': 5, 'text': 4, 'device': 3, 'link': 2, 'unbound': 2, 'shape': 1 };
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

            // Hidden-object isolation: an object hidden via the BD legend,
            // generator visibility panel, or user group toggle must NOT
            // receive clicks, hover, or any pointer interaction. Without
            // this skip, hidden links remain "ghost-clickable" at their
            // original screen location and steal hover focus from the
            // visible objects underneath, breaking selection UX.
            if (obj && obj._hidden) continue;

            if (obj.type === 'text') {
                // Hitbox parity with stretch (2026-05-12): RESOLVE every
                // text-box hitbox through `getTextEffectiveBounds` so that
                // edge-stretched boxes (manual width with auto-grown or
                // locked height) get a hitbox that matches their VISIBLE
                // rectangle. Without this, `findObjectAt` would re-measure
                // the raw `obj.text` glyphs and miss clicks that landed
                // inside the new rectangle but outside the original glyph
                // box -- which then fell through to the background
                // double-click handler and spawned phantom unbound links
                // over the stretched text box.
                const bounds = this.getTextEffectiveBounds(editor, obj);
                const w = bounds.w;
                const h = bounds.h;

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
                // Shape hit detection must follow the rendered geometry. Avoid
                // rectangular false positives for circles, diamonds, triangles,
                // and line-like shapes.
                if (window.ShapeMethods?.hitTestShape) {
                    const hit = window.ShapeMethods.hitTestShape(editor, obj, x, y, {
                        borderOnly: !!obj.mergedToBackground
                    });
                    if (hit) return obj;
                }
            } else if (obj.type === 'packet') {
                // Packet card: rectangular hit test (the card has a fixed
                // bounding box that already accounts for visible-layer count
                // and longest-line width) plus a smaller summary/action pill
                // rendered below the card for direction control.
                if (window.PacketMethods && window.PacketMethods.hitTestPacket) {
                    if (window.PacketMethods.findPacketSummaryHit &&
                        window.PacketMethods.findPacketSummaryHit(editor, obj, x, y)) {
                        return obj;
                    }
                    if (window.PacketMethods.hitTestPacket(editor, obj, x, y)) return obj;
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
        // Check all text objects (highest layer first for proper detection).
        // Hidden-object isolation: text objects whose parent link is
        // hidden, or which are themselves hidden, MUST NOT be hit-tested.
        const textObjects = editor.objects
            .filter(obj => obj.type === 'text' && !obj._hidden)
            .sort((a, b) => editor.getObjectLayer(b) - editor.getObjectLayer(a));
        
        for (const obj of textObjects) {
            // Use the same effective bounds the renderer + handles use. When
            // text has been resized (manual mode) the persisted width/height
            // win; otherwise fall back to font + measureText auto-sizing.
            // This keeps the click target identical to the visible bbox at
            // any zoom and after resize.
            const bounds = this.getTextEffectiveBounds(editor, obj);
            const w = bounds.w;
            const h = bounds.h;

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
            // Text objects: rotation handle is at the top-right corner of
            // the *effective* bounding box. Resolve via getTextEffectiveBounds
            // so the handle stays glued to the rendered rectangle even when
            // the user has edge-stretched the box (manual width + word-wrap)
            // or height-locked it. The legacy raw-measureText path drifted
            // off the visible top-right after any stretch -- defensive
            // upgrade in the polish + QA pass 2026-05-12.
            //
            // Note: in current code paths text rotation hits go through
            // findTextHandle (which handles the same geometry inline). This
            // branch is kept for any future caller that walks the unified
            // findRotationHandle API for both devices and text.
            const bounds = (typeof this.getTextEffectiveBounds === 'function')
                ? this.getTextEffectiveBounds(editor, device)
                : null;
            let w, h;
            if (bounds) {
                w = bounds.w;
                h = bounds.h;
            } else {
                const fontFamily = device.fontFamily || editor.defaultFontFamily || 'Inter, sans-serif';
                const requestedFontSize = Number(device.fontSize) || 14;
                const renderedFontSize = editor.getDprSnappedFontSize
                    ? editor.getDprSnappedFontSize(requestedFontSize)
                    : requestedFontSize;
                editor.ctx.font = `${renderedFontSize}px ${fontFamily}`;
                const metrics = editor.ctx.measureText(device.text || 'Text');
                w = metrics.width;
                h = parseInt(renderedFontSize);
            }

            // Unrotated top-right corner relative to centre, with the same
            // 15-px (in CSS-px) outset that drawText uses for the rotation
            // handle so geometry round-trips to within sub-pixel.
            const zoomScale = Math.max(1, 1 / editor.zoom);
            const handleOffset = 15 * zoomScale;
            const localX = w / 2 + handleOffset;
            const localY = -(h / 2 + handleOffset);

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
     * Get the effective bounding box for a text object. MUST mirror the
     * same containment + reflow logic that drawText paints, otherwise the
     * edge-zone hit-test, dashed selection halo, and rotation handle drift
     * out of sync with the rectangle the user actually sees.
     *
     *   * If `text.width` is persisted: word-wrap to that width. Height
     *     auto-grows from wrapped lines unless `text._heightLocked` is true,
     *     in which case `text.height` is honoured (matching drawText's
     *     clip-with-ellipsis path).
     *   * Otherwise auto-measure from font + content (legacy behaviour --
     *     untouched for any text box that has never been edge-stretched).
     *
     * Returns: { w, h, fontSize, lineHeight }
     */
    getTextEffectiveBounds(editor, textObj) {
        const fontFamily = textObj.fontFamily || 'Arial';
        const fontWeight = textObj.fontWeight || 'normal';
        const fontStyle = textObj.fontStyle || 'normal';
        const requestedFontSize = Number(textObj.fontSize) || 14;
        const displayFontSize = editor.getDprSnappedFontSize
            ? editor.getDprSnappedFontSize(requestedFontSize)
            : requestedFontSize;
        const fontSize = parseInt(displayFontSize) || 14;
        const lineHeight = fontSize * 1.3;

        editor.ctx.save();
        editor.ctx.font = `${fontStyle} ${fontWeight} ${fontSize}px ${fontFamily}`;
        const textContent = textObj.text == null ? 'Text' : String(textObj.text);

        // Manual-WIDTH mode (edge-stretch + reflow, 2026-05-12).
        const hasManualWidth = Number.isFinite(textObj.width) && textObj.width > 0;
        if (hasManualWidth) {
            const Drawer = window.CanvasDrawing;
            let wrapped;
            if (Drawer && typeof Drawer._wrapTextLinesToWidth === 'function') {
                wrapped = Drawer._wrapTextLinesToWidth(editor.ctx, textContent, textObj.width);
            } else {
                wrapped = textContent.split('\n');
            }
            const naturalH = Math.max(20, wrapped.length * lineHeight);
            const heightLocked = textObj._heightLocked === true && Number.isFinite(textObj.height);
            const h = heightLocked ? Math.max(20, textObj.height) : naturalH;
            editor.ctx.restore();
            return { w: textObj.width, h, fontSize, lineHeight };
        }

        // Auto-size mode: measure font + content, mirror drawText exactly.
        const lines = textContent.split('\n');
        let maxWidth = 0;
        for (const line of lines) {
            const metrics = editor.ctx.measureText(line || ' ');
            if (metrics.width > maxWidth) maxWidth = metrics.width;
        }
        editor.ctx.restore();
        return {
            w: maxWidth,
            h: lines.length * lineHeight,
            fontSize,
            lineHeight
        };
    },

    /**
     * Edge-zone width in SCREEN pixels for text-box stretch. Two values
     * intentionally separated (smoothness pass 2026-05-12):
     *
     *   * TEXT_EDGE_ZONE_PX (5) -- the VISUAL semantic. Documented in
     *     drawing comments and matches typical OS window-resize edge
     *     zones. Reserved for any future "show edge zone on hover" UI
     *     so users perceive a 5-px band, not an 8-px one.
     *
     *   * TEXT_EDGE_ZONE_HIT_PX (8) -- the actual HIT target. Wider
     *     than the visual band so trackpad / coarse mouse users land
     *     on the edge reliably. The body of the text box (drag-to-move)
     *     keeps almost all of its area thanks to the
     *     `Math.min(halfW, halfH) * 0.45` clamp on tiny boxes.
     *
     * The actual world-space zone in findTextHandle is
     * `TEXT_EDGE_ZONE_HIT_PX / editor.zoom` so the hit target stays the
     * same physical thickness at any zoom level.
     */
    TEXT_EDGE_ZONE_PX: 5,
    TEXT_EDGE_ZONE_HIT_PX: 8,

    /**
     * Visible dot-handle hit-box in SCREEN pixels (matches shape resize
     * handle hit-boxes in topology-shape-methods.js -- corners 20, edges
     * 18 -- so the user gets identical click feel on shapes and text).
     */
    TEXT_DOT_CORNER_HIT_PX: 20,
    TEXT_DOT_EDGE_HIT_PX: 18,

    /**
     * Find which text-box stretch zone the mouse is over.
     *
     * 2026-05-12 dots+edge-zone coexist:
     *
     *   1. ROTATION handle (top-right outside, green) -- highest priority.
     *   2. DOT-HANDLES (8 visible dots painted by drawText) -- corners
     *      first then edge-midpoints, with shape-style hit-boxes (20/18
     *      CSS px). Discoverable: the user SEES the dot.
     *   3. EDGE-ZONE band (5-px world-space band hugging each side /
     *      corner) -- forgiving fallback so the user can grab the border
     *      anywhere along its length without pixel-perfect aim.
     *
     * Returns:
     *   - { type: 'rotation', cursor: 'grab' }
     *   - { type: 'resize',  cursor: 'ew-resize'|..., handle: 'e'|... }
     *   - null  (inside the body or outside the bbox+zone band)
     */
    findTextHandle(editor, textObj, x, y) {
        if (!textObj || textObj.type !== 'text') return null;

        const bounds = this.getTextEffectiveBounds(editor, textObj);
        const w = bounds.w;
        const h = bounds.h;
        const halfW = w / 2;
        const halfH = h / 2;
        const effRot = editor.getEffectiveTextRotation
            ? editor.getEffectiveTextRotation(textObj)
            : (textObj.rotation || 0);
        // Inverse rotation -- transform the click into the text's local frame
        // (centred at textObj.x, textObj.y, axis-aligned).
        const radians = -effRot * Math.PI / 180;
        const cos = Math.cos(radians);
        const sin = Math.sin(radians);
        const dx = x - textObj.x;
        const dy = y - textObj.y;
        const localX = dx * cos - dy * sin;
        const localY = dx * sin + dy * cos;

        // Edge-stretch HIT zone in WORLD pixels (clamped so it cannot
        // exceed half of the smaller dimension -- otherwise tiny text
        // boxes would be entirely "edge zone" with no body left for
        // drag-to-move). The HIT zone is intentionally wider than the
        // VISUAL semantic (TEXT_EDGE_ZONE_PX=5 vs HIT=8) so trackpad /
        // coarse mouse users land on the edge reliably without seeing
        // an inflated visual band. Smoothness pass 2026-05-12.
        const zoom = editor.zoom > 0 ? editor.zoom : 1;
        const desired = (this.TEXT_EDGE_ZONE_HIT_PX || 8) / zoom;
        const zone = Math.max(1, Math.min(desired, Math.min(halfW, halfH) * 0.45));

        // Rotation handle: outside the top-right corner, OUTSIDE the
        // edge-zone area so it remains independently grabbable. Hit-tested
        // FIRST so it always wins over a near-corner edge zone.
        const zoomScaleClamp = Math.max(1, 1 / editor.zoom);
        const rotHandleOffset = 15 * zoomScaleClamp;
        const rotationHitSize = 12 * zoomScaleClamp;
        const rotLocalX = halfW + rotHandleOffset;
        const rotLocalY = -(halfH + rotHandleOffset);
        const rdx = localX - rotLocalX;
        const rdy = localY - rotLocalY;
        if (Math.sqrt(rdx * rdx + rdy * rdy) <= rotationHitSize) {
            return { type: 'rotation', cursor: 'grab' };
        }

        // VISIBLE DOT-HANDLES (2026-05-12 dots+edge-zone coexist).
        // Hit-test the 8 painted dots BEFORE the edge-zone band so a
        // click landing on a visible dot routes deterministically to its
        // matching handle id. Corners use a 20-px square hit-box, edges
        // an 18-px circle hit-box -- mirrors shape resize handles.
        // Cursor field is a passive default; mouse-move overrides it via
        // _rotatedCursor(handle, effRot) when `handle` is present, so
        // rotated text boxes still get rotation-corrected cursors.
        const cornerHitWorld = (this.TEXT_DOT_CORNER_HIT_PX || 20) / zoom;
        const edgeHitWorld   = (this.TEXT_DOT_EDGE_HIT_PX   || 18) / zoom;
        const dotCorners = [
            { id: 'nw', x: -halfW, y: -halfH, cur: 'nwse-resize' },
            { id: 'ne', x:  halfW, y: -halfH, cur: 'nesw-resize' },
            { id: 'sw', x: -halfW, y:  halfH, cur: 'nesw-resize' },
            { id: 'se', x:  halfW, y:  halfH, cur: 'nwse-resize' }
        ];
        for (const d of dotCorners) {
            if (Math.abs(localX - d.x) <= cornerHitWorld &&
                Math.abs(localY - d.y) <= cornerHitWorld) {
                return { type: 'resize', cursor: d.cur, handle: d.id };
            }
        }
        const dotEdges = [
            { id: 'n', x:  0,     y: -halfH, cur: 'ns-resize' },
            { id: 's', x:  0,     y:  halfH, cur: 'ns-resize' },
            { id: 'w', x: -halfW, y:  0,     cur: 'ew-resize' },
            { id: 'e', x:  halfW, y:  0,     cur: 'ew-resize' }
        ];
        for (const d of dotEdges) {
            const ddx = localX - d.x;
            const ddy = localY - d.y;
            if (Math.sqrt(ddx * ddx + ddy * ddy) <= edgeHitWorld) {
                return { type: 'resize', cursor: d.cur, handle: d.id };
            }
        }

        // The hit area for the entire stretch surface is the bbox EXPANDED
        // outward by `zone`. If the click is outside that expanded box,
        // we are nowhere near the edge and bail out -- callers will then
        // route to body hit-test or whatever is below.
        if (Math.abs(localX) > halfW + zone) return null;
        if (Math.abs(localY) > halfH + zone) return null;

        // Compute "is this inside one of the four edge bands?" Each band
        // is a strip of width `zone` straddling the bbox edge (half outside,
        // half inside, conceptually -- but practically we treat anywhere
        // within `zone` of the edge as on the edge).
        const onLeft   = localX <= -halfW + zone;
        const onRight  = localX >=  halfW - zone;
        const onTop    = localY <= -halfH + zone;
        const onBottom = localY >=  halfH - zone;

        // Corner takes precedence over edge -- even a 1-pixel overlap of two
        // bands yields a diagonal cursor so the user knows they will get
        // both axes.
        if (onTop && onLeft)     return { type: 'resize', cursor: 'nwse-resize', handle: 'nw' };
        if (onTop && onRight)    return { type: 'resize', cursor: 'nesw-resize', handle: 'ne' };
        if (onBottom && onLeft)  return { type: 'resize', cursor: 'nesw-resize', handle: 'sw' };
        if (onBottom && onRight) return { type: 'resize', cursor: 'nwse-resize', handle: 'se' };
        if (onLeft)              return { type: 'resize', cursor: 'ew-resize',   handle: 'w' };
        if (onRight)             return { type: 'resize', cursor: 'ew-resize',   handle: 'e' };
        if (onTop)               return { type: 'resize', cursor: 'ns-resize',   handle: 'n' };
        if (onBottom)            return { type: 'resize', cursor: 'ns-resize',   handle: 's' };

        // Inside the body of the bbox but not in the edge zone -- the
        // caller (mouse-down for selected text, hover cursor logic) will
        // treat this as "no handle" and let body drag-to-move take over.
        return null;
    },
    
    // Check if click is on a device's terminal button
    findTerminalButton(editor, device, x, y) {
        if (!device || device.type !== 'device') return false;
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

    _pickSshTarget(device) {
        if (window.TopologySshTarget && window.TopologySshTarget.pick) {
            return window.TopologySshTarget.pick(device);
        }
        const cfg = device?.sshConfig || {};
        const addr = String(device?.deviceAddress || '').trim();
        const addrHost = addr.includes('@') ? addr.split('@').pop().trim() : addr;
        const snLockedHost = cfg._snVerified && cfg._snVerifiedHost ? String(cfg._snVerifiedHost).trim() : '';
        const savedHost = String(cfg._userSavedHost || '').trim();
        const preferredSavedHost = savedHost && !(snLockedHost && this._isSshTargetIp(savedHost) && !this._isSshTargetIp(snLockedHost))
            ? savedHost
            : '';
        const isCluster = !!(cfg._isCluster || cfg._virshInfo || device?._isCluster);
        const activeNccHost = [
            cfg._activeNccHost,
            cfg._virshInfo?.activeNcc,
            device?._monitorContext?.active_ncc_host,
            device?._monitorContext?.active_ncc_vm,
            device?._identity?.active_ncc_host,
            device?._identity?.active_ncc_vm,
        ].map(v => String(v || '').trim())
         .find(v => v && !this._isSshTargetIp(v) && /(^|[-_.])ncc\d+(\.|$)/i.test(v));
        const clusterSerialHost = (cfg._isCluster || cfg._virshInfo || device?._isCluster)
            && this._isSshTargetIp(cfg.host)
            ? (activeNccHost || snLockedHost || device?.deviceSerial || device?.serial || '')
            : '';
        return {
            host: (isCluster && activeNccHost ? activeNccHost : '')
                || preferredSavedHost
                || clusterSerialHost
                || snLockedHost
                || cfg.host
                || addrHost
                || device?.deviceSerial
                || device?.serial
                || cfg.hostBackup
                || '',
            addrUser: addr.includes('@') ? addr.split('@')[0] : '',
        };
    },

    _isSshTargetIp(value) {
        return /^\d+\.\d+\.\d+\.\d+$/.test(String(value || '').trim());
    },

    // Open terminal (SSH) to device -- iTerm preferred, web terminal as fallback
    async openTerminalToDevice(editor, device) {
        try {
            if (editor.hideDeviceSelectionToolbar) editor.hideDeviceSelectionToolbar();

            const sshConfig = device.sshConfig || {};
            const pickedTarget = this._pickSshTarget(device);
            let host = pickedTarget.host || '';
            let user = sshConfig._userSavedUser || sshConfig.user || 'dnroot';
            let password = sshConfig._userSavedPass || sshConfig.password || 'dnroot';
            let isCluster = sshConfig._isCluster || false;
            let virshCmd = sshConfig._virshCmd || '';

            if (pickedTarget.addrUser && !sshConfig._userSavedUser && !sshConfig.user) {
                user = pickedTarget.addrUser;
            }
            if (!host) {
                // No SSH config at all -- open SSH dialog so user can configure
                if (editor.showSSHAddressDialog) {
                    editor.showSSHAddressDialog(device);
                    return;
                }
                const recovered = await this._showTerminalRecoveryModal(editor, device, device.label || 'unknown');
                if (!recovered) return;
                host = recovered;
                device.sshConfig = device.sshConfig || {};
                device.sshConfig.host = host;
            }

            let _devMode = (device._deviceMode || '').toUpperCase();
            console.log(`[SSH] Start: label=${device.label}, host=${host}, cluster=${isCluster}, mode=${_devMode}`);

            // ===== FAST PATH: if host is set, pre-flight check then open iTerm =====
            // `_isClusterDev` starts from canvas state (which may be empty on
            // fresh loads). The backend context fetch below can promote it
            // to true once we see `is_cluster`/`ncc_type==='kvm'`/KVM hints.
            // Using `let` (not `const`) so the promotion actually takes
            // effect -- previously this stayed `false` after fresh page
            // loads and skipped the GI/active-NCC iTerm path entirely.
            let _isClusterDev = isCluster || !!(sshConfig._virshInfo?.kvmHost);
            const _hostIsKvm = sshConfig._virshInfo?.kvmHost && (
                host === sshConfig._virshInfo.kvmHost ||
                host === String(sshConfig._virshInfo.kvmHost || '')
            );
            if (host && !_hostIsKvm) {
                const isIP = /^\d+\.\d+\.\d+\.\d+$/.test(host);

                let _mgmtIpReaped = false;
                // ALWAYS fetch the backend context on click: even if the
                // canvas cached a `_deviceMode`, we still need `is_cluster`,
                // `active_ncc_host`, and `active_ncc_ip` to route iTerm to
                // the active NCC rather than stale NCC mgmt IP. The backend
                // /api/devices/:id/context read is served from on-disk
                // operational.json (no SSH) so this costs ~50ms.
                if (typeof ScalerAPI !== 'undefined' && ScalerAPI.getDeviceContext) {
                    try {
                        const ctx = await ScalerAPI.getDeviceContext(device.label || device.id || '');
                        const ctxState = (ctx?.device_state || '').toUpperCase();
                        if (ctxState) {
                            _devMode = ctxState;
                            device._deviceMode = ctxState;
                            console.log(`[SSH] Device state from backend: ${ctxState}`);
                        }
                        // Backend now exposes cluster identity directly --
                        // promote `_isClusterDev` so GI-mode / active-NCC
                        // iTerm works even when `sshConfig._isCluster` was
                        // never populated (fresh canvas load, incognito,
                        // different browser, etc.).
                        const ctxIsCluster = ctx?.is_cluster === true
                            || ctx?.ncc_type === 'kvm'
                            || !!(ctx?.kvm_host_ip || ctx?.kvm_host)
                            || !!(ctx?.active_ncc_host)
                            || (Array.isArray(ctx?.ncc_vms) && ctx.ncc_vms.length > 0)
                            || (Array.isArray(ctx?.ncc_hosts) && ctx.ncc_hosts.length > 0);
                        if (ctxIsCluster && !_isClusterDev) {
                            _isClusterDev = true;
                            device.sshConfig = device.sshConfig || {};
                            device.sshConfig._isCluster = true;
                            console.log(`[SSH] Cluster detected from backend context: ncc_type=${ctx?.ncc_type || '?'}, kvm_host=${ctx?.kvm_host_ip || ctx?.kvm_host || '?'}, active_ncc=${ctx?.active_ncc_host || '?'}`);
                        }
                        // Cache active-NCC hints so _getActiveNccTarget
                        // hits the fast 'cache' path (no second probe).
                        if (ctx?.active_ncc_host && typeof ctx.active_ncc_host === 'string') {
                            device.sshConfig = device.sshConfig || {};
                            device.sshConfig._activeNccHost = ctx.active_ncc_host.trim();
                        }
                        if (ctx?.active_ncc_ip && /^\d+\.\d+\.\d+\.\d+$/.test(ctx.active_ncc_ip)) {
                            // Reject the per-node-IP cache write when the
                            // backend claims ``active_ncc_ip`` equals the
                            // cluster VIP -- that's the resolver bug we
                            // patched on 27Apr2026 and a stale-cached value
                            // could still arrive from a not-yet-restarted
                            // bridge or a different worker. The frontend
                            // treats the per-node IP as the safe iTerm
                            // target, so accepting the VIP here would
                            // resurrect the flip-flop loop.
                            const _ctxVip = (ctx?.ncc_mgmt_ip || '').trim().split('/')[0];
                            const _claimed = ctx.active_ncc_ip.trim();
                            device.sshConfig = device.sshConfig || {};
                            if (_ctxVip && _claimed === _ctxVip) {
                                console.warn(
                                    `[SSH] Backend returned active_ncc_ip=${_claimed} which `
                                    + `equals ncc_mgmt_ip (cluster VIP). Ignoring -- the `
                                    + `frontend will fall back to the cached/probed per-node IP.`
                                );
                            } else {
                                device.sshConfig._activeNccIp = _claimed;
                            }
                        }
                        if (ctx?.active_ncc_source) {
                            device.sshConfig = device.sshConfig || {};
                            device.sshConfig._activeNccSource = ctx.active_ncc_source;
                        }
                        if (ctx?.ncc_dns_map && typeof ctx.ncc_dns_map === 'object') {
                            device.sshConfig = device.sshConfig || {};
                            device.sshConfig._activeNccDnsMap = ctx.ncc_dns_map;
                        }
                        // Cache virsh hints so the GI-mode fallback web
                        // terminal path doesn't have to re-probe when
                        // iTerm is declined.
                        if (_isClusterDev && (ctx?.kvm_host_ip || ctx?.kvm_host)) {
                            device.sshConfig = device.sshConfig || {};
                            const vi = device.sshConfig._virshInfo || {};
                            if (!vi.kvmHost) vi.kvmHost = ctx.kvm_host_ip || ctx.kvm_host;
                            if (!vi.activeNcc && ctx?.active_ncc_vm) vi.activeNcc = ctx.active_ncc_vm;
                            if (!vi.nccVms && Array.isArray(ctx?.ncc_vms)) vi.nccVms = ctx.ncc_vms.slice();
                            device.sshConfig._virshInfo = vi;
                        }
                        if (_isClusterDev) {
                            const ctxNccIp = (ctx?.ncc_mgmt_ip || '').trim();
                            if (ctxNccIp && /^\d+\.\d+\.\d+\.\d+$/.test(ctxNccIp)) {
                                device.sshConfig = device.sshConfig || {};
                                device.sshConfig._nccMgmtIp = ctxNccIp;
                            }
                        }
                        // `identity.mgmt_ip` is cleared by the backend reap
                        // when a ghost-IP is detected. If we still have a host
                        // from a client-side cache but the backend says the
                        // mgmt IP was reaped, treat the device as recovery.
                        const identityMgmt = (ctx?.identity?.mgmt_ip || '').trim();
                        if (_isClusterDev && identityMgmt === '') {
                            _mgmtIpReaped = true;
                            console.warn(`[SSH] Backend mgmt_ip is empty for cluster ${device.label} -- treating as recovery (local cache ${host} is likely ghost).`);
                        }
                    } catch (e) {
                        console.warn('[SSH] Could not fetch device state:', e?.message);
                    }
                }

                if (_isClusterDev) {
                    const activeHost = (device.sshConfig?._activeNccHost
                        || device.sshConfig?._virshInfo?.activeNcc
                        || '').trim();
                    const hostIsNcc = /(^|[-_.])ncc\d+(\.|$)/i.test(host);
                    if (activeHost && !this._isSshTargetIp(activeHost) && !hostIsNcc) {
                        console.log(
                            `[SSH] Cluster target corrected from '${host}' to active NCC '${activeHost}' `
                            + `(do not use chassis/NCP serial for CL-86 SSH).`
                        );
                        host = activeHost;
                    }
                }

                const _isGiOrShell = _isClusterDev && (
                    ['GI', 'BASEOS_SHELL', 'RECOVERY'].includes(_devMode) || _mgmtIpReaped
                );

                if (_isGiOrShell) {
                    // Canonical path for cluster in GI / BASEOS_SHELL /
                    // RECOVERY: iTerm to the ACTIVE NCC's own
                    // per-node hostname (``kvm108-cl408d-ncc0``), NOT
                    // the cluster VIP (``100.64.4.98``).
                    //
                    // The VIP is dead in GI -- a baseos sshd answers
                    // :22 but rejects dnroot. The per-node NCC, on
                    // the other hand, exposes an sshd that the
                    // operator's Mac can reach through lab DNS +
                    // VPN, and that sshd does accept dnroot when
                    // the NCC's baseos layer has been seeded with
                    // the standard lab key (which is the case for
                    // all staged CL-86 NCCs).
                    //
                    // Order (iTerm-first, virsh as fallback only):
                    //   1. iTerm -> ssh://dnroot@<active NCC hostname>
                    //      (hostname-first; Mac lab DNS resolves it).
                    //   2. iTerm -> ssh://dnroot@<active NCC per-node IP>
                    //      (hostname didn't resolve -- fall back to
                    //      the DNS-resolved per-node IP that the
                    //      backend probe wrote).
                    //   3. iTerm -> ssh://dnroot@<cached NCC mgmt IP>
                    //      (last SSH-based attempt; user override
                    //      ``preferredMethod='iterm'`` path).
                    //   4. Virsh console via web terminal (kvm host)
                    //      -- ONLY when every ssh-based attempt
                    //      above genuinely failed to dispatch.
                    //
                    // Default ``preferIp: true`` -- the backend has
                    // already resolved ``active_ncc_ip`` to the active
                    // NCC's per-node IPv4 (e.g. ``100.64.11.96`` for
                    // ``kvm108-cl408d-ncc0``) and that IP is routable
                    // from the operator's Mac via VPN regardless of
                    // whether the Mac has lab DNS loaded.
                    console.log(`[SSH] Cluster in ${_devMode} mode -- trying active-NCC iTerm first (per-node IP, mgmtIpReaped=${_mgmtIpReaped})`);

                    const snOpened = await this._tryOpenActiveNccIterm(editor, device, {
                        user, password, modeLabel: _devMode || (_mgmtIpReaped ? 'RECOVERY' : ''),
                    });
                    if (snOpened) return;
                    console.warn(`[SSH] active-NCC iTerm couldn't dispatch for ${device.label} -- trying NCC mgmt IP next`);

                    // Try explicit NCC mgmt IP fallback (still
                    // iTerm-based). Only if this ALSO fails do we
                    // fall through to the virsh web terminal.
                    const nccOpened = await this._tryOpenClusterNccMgmtIterm(editor, device, sshConfig);
                    if (nccOpened) return;
                    console.warn(`[SSH] NCC mgmt iTerm failed -- falling back to virsh console web terminal`);

                    let vi = sshConfig._virshInfo || {};

                    // Discover virsh info if missing (first visit to this
                    // cluster in GI mode, or sshConfig was wiped).
                    if (!vi.kvmHost && typeof ScalerAPI !== 'undefined' && ScalerAPI.probeConnection) {
                        try {
                            console.log(`[SSH] GI mode: probing to discover virsh info for ${device.label}`);
                            const result = await ScalerAPI.probeConnection(device.label || host, host);
                            const virshEntry = (result.methods || []).find(m => m.method === 'virsh_console' && m.reachable);
                            if (virshEntry) {
                                const kvmCreds = virshEntry.kvm_credentials || {};
                                const activeNcc = result.cluster?.active_ncc_vm
                                    || (virshEntry.vms_running?.[0])
                                    || (virshEntry.ncc_vms || [])[0]
                                    || '';
                                device.sshConfig = device.sshConfig || {};
                                device.sshConfig._isCluster = true;
                                device.sshConfig._virshInfo = {
                                    kvmHost: virshEntry.host,
                                    kvmUser: kvmCreds.username || 'dn',
                                    kvmPass: kvmCreds.password || '',
                                    activeNcc,
                                    nccVms: virshEntry.ncc_vms || [],
                                };
                                device.sshConfig._virshCmd = activeNcc ? `sudo virsh console --force ${activeNcc}` : '';
                                vi = device.sshConfig._virshInfo;
                                if (result.device_state) device._deviceMode = result.device_state;
                                console.log(`[SSH] GI probe discovered virsh: kvm=${vi.kvmHost}, activeNcc=${vi.activeNcc}`);
                            } else {
                                console.warn(`[SSH] GI probe: no reachable virsh_console method returned`);
                            }
                        } catch (e) {
                            console.warn(`[SSH] GI probe failed: ${e.message}`);
                        }
                    }

                    const kvmHost = vi.kvmHost || '';
                    if (kvmHost && typeof window.TerminalPanel !== 'undefined' && window.TerminalPanel.open) {
                        const activeNcc = vi.activeNcc || '';
                        console.log(`[SSH] ${_devMode} mode -> virsh console via web terminal: kvm=${kvmHost}, ncc=${activeNcc}`);
                        window.TerminalPanel.open({
                            deviceId: device.label || device.id || '',
                            host: kvmHost, method: 'virsh_console',
                            deviceLabel: `${device.label || 'Cluster'} (NCC ${activeNcc || 'console'}) - ${_devMode}`,
                            password: vi.kvmPass || 'drive1234!', user: vi.kvmUser || 'dn',
                            virshInfo: { kvmHost, kvmUser: vi.kvmUser || 'dn', kvmPass: vi.kvmPass || 'drive1234!',
                                nccVms: vi.nccVms || [], activeNcc },
                        });
                        this._fireBackgroundNccDiscovery(editor, device, {
                            kvmHost, kvmUser: vi.kvmUser || 'dn', kvmPass: vi.kvmPass || 'drive1234!',
                            nccVms: vi.nccVms || [], activeNcc });
                        editor.showNotification(`[OK] ${_devMode} mode -- virsh console (reliable path)`, 'success', 5000);
                        return;
                    }

                    // No virshInfo available -- last resort: try NCC mgmt iTerm
                    // (in case the user's network actually can reach it). If
                    // that fails, the unreachable modal offers virsh + dialog.
                    //
                    // NOTE: variable name MUST differ from the earlier
                    // `nccOpened` (line ~990) -- both bindings live in the
                    // same `if (_isGiOrShell)` scope, so duplicate `const`
                    // throws a parse-time SyntaxError that kills the whole
                    // file (fixed 2026-04-24t after the nccOpened-redecl
                    // regression).
                    console.warn(`[SSH] GI mode: no virsh info available, trying iTerm-to-NCC as last resort`);
                    const nccOpenedLastResort = await this._tryOpenClusterNccMgmtIterm(editor, device, sshConfig);
                    if (nccOpenedLastResort) return;

                    this._showSshUnreachableNotification(editor, device, host, _devMode, false, 'auth_unreliable');
                    return;
                }

                // ===== STALE STICKY for DNOS cluster devices =====
                // Two failure modes share the same fix:
                //
                //  (1) Stale NCC HOSTNAME sticky (e.g. ``kvm108-cl408d-ncc1``)
                //      left over from a delete/deploy upgrade. The Mac
                //      usually has lab routing (VPN) but not lab DNS, so
                //      ``ssh dnroot@kvm108-cl408d-ncc1`` returns "Could
                //      not resolve hostname" even though the per-node IP
                //      is reachable.
                //
                //  (2) Stale CLUSTER MGMT VIP sticky (e.g. ``100.64.4.98``).
                //      Some cluster VIP listeners are configured with a
                //      cluster-VIP-specific password, so launching iTerm
                //      to the VIP loops the operator on a "Permission
                //      denied" prompt while the per-node sshd next door
                //      would have accepted the universal dnroot/dnroot
                //      pair (observed on YOR_CL_PE-4 27-Apr-2026).
                //
                // For both we re-route through ``_tryOpenActiveNccIterm``
                // (preferIp=true) so iTerm lands on the active NCC's
                // per-node IP, the only target that universally accepts
                // dnroot in DNOS clusters. The cluster VIP stays in
                // ``ncc_mgmt_ip``/``mgmt_ip`` for callers (cluster mgmt
                // UI, upgrade orchestration) that explicitly need it.
                const _looksLikeNccHostnameSticky = false;
                const _stickyIsClusterVip = (() => {
                    if (!_isClusterDev || !isIP) return false;
                    const cfg = device.sshConfig || {};
                    const _vipCands = [
                        cfg._nccMgmtIp,
                        cfg._mgmtIp,
                        cfg._enrichedMgmtIp,
                    ].map(v => (typeof v === 'string' ? v.trim() : ''))
                     .filter(v => /^\d+\.\d+\.\d+\.\d+$/.test(v));
                    if (_vipCands.includes(host)) return true;
                    // Cached active NCC IP from a previous probe. Two
                    // distinct cases:
                    //   (a) ``_activeNccIp`` differs from ``host`` -- the
                    //       saved host is the VIP and the resolver
                    //       knows the per-node IP. Definitely stale.
                    //   (b) ``_activeNccIp`` EQUALS ``host`` while ``host``
                    //       is also one of the VIP candidates listed
                    //       above. Older resolver versions (pre-27Apr)
                    //       wrote the VIP into ``active_ncc_ip`` when
                    //       lab DNS only had the VIP A-record, so an
                    //       equality match against the VIP set still
                    //       counts as stale.
                    const _activeIp = cfg._activeNccIp || '';
                    if (_activeIp && /^\d+\.\d+\.\d+\.\d+$/.test(_activeIp)) {
                        if (_activeIp !== host) return true;
                        if (_vipCands.includes(_activeIp)) return true;
                    }
                    return false;
                })();
                if (_looksLikeNccHostnameSticky || _stickyIsClusterVip) {
                    const _why = `cluster mgmt VIP (active NCC hostname is the canonical cluster target)`;
                    console.log(
                        `[SSH] DNOS cluster: saved host '${host}' is the ${_why} `
                        + `-- routing via active-NCC iTerm to land on the active NCC hostname.`
                    );
                    const snOpened = await this._tryOpenActiveNccIterm(editor, device, {
                        user, password, modeLabel: _devMode || 'DNOS', preferIp: false,
                    });
                    if (snOpened) {
                        // Refresh the sticky to the active NCC's PER-NODE IP
                        // so subsequent clicks dispatch straight there
                        // without re-running this re-routing dance.
                        //
                        // We deliberately do NOT fall back to the cluster
                        // mgmt VIP (_nccMgmtIp): if we just landed here
                        // because the VIP rejected dnroot, refreshing the
                        // sticky to the VIP would re-trap us on the next
                        // click. When the per-node IP is unknown we leave
                        // the sticky alone so the next dispatch re-runs
                        // the re-route logic (which re-probes the active
                        // NCC) instead of hard-coding a stale target.
                        //
                        // EXTRA GUARD: even if ``_activeNccIp`` is set,
                        // refuse to write it into the sticky when it
                        // happens to equal one of the known cluster VIP
                        // candidates. Older backend resolvers (pre-27Apr)
                        // copied the VIP into ``active_ncc_ip`` when lab
                        // DNS only had the VIP A-record, and a stale
                        // cached value can still arrive via the
                        // device-context fetch. Writing it would lock
                        // the user back onto the broken VIP target.
                        const _cfg = device.sshConfig || {};
                        const _newSticky = _cfg._activeNccHost || '';
                        const _vipCandsSet = [
                            _cfg._nccMgmtIp, _cfg._mgmtIp, _cfg._enrichedMgmtIp,
                        ].map(v => (typeof v === 'string' ? v.trim() : ''))
                         .filter(v => /^\d+\.\d+\.\d+\.\d+$/.test(v));
                        const _newStickyIsVip = _newSticky && _vipCandsSet.includes(_newSticky);
                        if (_newSticky
                                && !/^\d+\.\d+\.\d+\.\d+$/.test(_newSticky)
                                && !_newStickyIsVip) {
                            device.sshConfig._userSavedHost = _newSticky;
                            device.sshConfig.host = _newSticky;
                            console.log(`[SSH] Sticky host refreshed to active NCC hostname: ${_newSticky}`);
                            try {
                                if (typeof saveTopology === 'function') saveTopology();
                                else if (typeof autoSave === 'function') autoSave();
                                else if (window.editor && typeof window.editor.autoSave === 'function') {
                                    window.editor.autoSave();
                                }
                            } catch (_persistErr) { /* best effort */ }
                        } else if (_newStickyIsVip) {
                            console.log(
                                `[SSH] Refusing to refresh sticky to ${_newSticky} -- `
                                + `that is the cluster VIP. Leaving sticky as-is so `
                                + `the next click re-resolves the active NCC.`
                            );
                        }
                        return;
                    }
                    console.warn(
                        `[SSH] active-NCC iTerm couldn't dispatch for ${device.label} `
                        + `-- falling back to direct dispatch with saved hostname.`
                    );
                }

                if (isIP && typeof ScalerAPI !== 'undefined' && ScalerAPI.checkPort) {
                    try {
                        const chk = await ScalerAPI.checkPort(host, 22);
                        if (chk && !chk.reachable) {
                            console.warn(`[SSH] Pre-flight FAILED: ${host}:22 unreachable`);
                            const vi = sshConfig._virshInfo || {};
                            const hasVirsh = _isClusterDev && vi.kvmHost && (vi.activeNcc || (vi.nccVms && vi.nccVms.length));
                            this._showSshUnreachableNotification(editor, device, host, _devMode, hasVirsh, 'port_closed');
                            return;
                        }
                    } catch (e) {
                        console.warn(`[SSH] Pre-flight check error (proceeding): ${e.message}`);
                    }
                }

                // ===== GHOST-IP IDENTITY PRE-FLIGHT =====
                // TCP reachable is NOT proof the IP still belongs to this
                // device. After an upgrade the IP may have been reassigned
                // to a completely different DUT. Ask the backend to SSH
                // briefly, read the banner, and confirm the hostname. On
                // mismatch the bridge reaps the stale record and we redirect
                // the user to the SSH dialog with the new state.
                if (isIP && typeof ScalerAPI !== 'undefined' && ScalerAPI.verifyDeviceIdentity) {
                    try {
                        const verify = await ScalerAPI.verifyDeviceIdentity(
                            device.label || device.id || '', host,
                            { user, password, autoReap: true },
                        );
                        if (verify && verify.reason === 'ghost_ip' && verify.identity_verified === false) {
                            console.warn(`[SSH] GHOST IP caught: ${host} now answers as '${verify.actual_hostname}' (expected ${verify.expected_hostname || device.label})`);
                            try {
                                window.dispatchEvent(new CustomEvent('ssh:ghost-ip-detected', {
                                    detail: {
                                        deviceId: device.label || device.id || '',
                                        ip: host,
                                        expected: verify.expected_hostname || device.label || '',
                                        actual: verify.actual_hostname || '',
                                        reason: 'ghost_ip_preflight',
                                    },
                                }));
                            } catch (_) {}

                            // Cluster recovery: first try iTerm to the
                            // ACTIVE NCC's DNS hostname (the canonical
                            // pre-upgrade route). The operator's Mac
                            // resolves the NCC hostname via lab DNS to
                            // the cluster mgmt IP that the active NCC
                            // currently owns -- this survives ghost-IP
                            // reaping since we are NOT using the stored
                            // (stale) IP but the hostname.
                            if (_isClusterDev) {
                                const snOpened = await this._tryOpenActiveNccIterm(editor, device, {
                                    user, password, modeLabel: 'ghost-IP recovery',
                                });
                                if (snOpened) {
                                    const nccHost = device.sshConfig?._activeNccHost || '';
                                    const bannerSn = `[GHOST IP] ${device.label}: ${host} now belongs to "${verify.actual_hostname}". Launching iTerm to active NCC ${nccHost}.`;
                                    if (editor.showNotification) editor.showNotification(bannerSn, 'warning', 10000);
                                    return;
                                }
                                console.warn(`[SSH] GHOST-IP: active-NCC iTerm unavailable, falling back to virsh console`);
                            }

                            // Cluster recovery fallback: if we know (or can
                            // discover) the KVM host + active NCC, open the
                            // virsh console in the web terminal so the user
                            // can reach the device while it has no valid
                            // mgmt IP. Used when SN DNS is unavailable.
                            let vi = (device.sshConfig && device.sshConfig._virshInfo) || null;
                            if ((!vi || !vi.kvmHost) && typeof ScalerAPI !== 'undefined' && ScalerAPI.probeConnection) {
                                try {
                                    console.log(`[SSH] GHOST-IP cluster recovery: probing for virsh info`);
                                    const probe = await ScalerAPI.probeConnection(device.label || device.id || '', '');
                                    const virshEntry = (probe && (probe.methods || []).find(m => m.method === 'virsh_console' && m.reachable)) || null;
                                    if (virshEntry) {
                                        const kvmCreds = virshEntry.kvm_credentials || {};
                                        const activeNcc = (probe.cluster && probe.cluster.active_ncc_vm)
                                            || (virshEntry.vms_running && virshEntry.vms_running[0])
                                            || (virshEntry.ncc_vms || [])[0]
                                            || '';
                                        vi = {
                                            kvmHost: virshEntry.host,
                                            kvmUser: kvmCreds.username || 'dn',
                                            kvmPass: kvmCreds.password || '',
                                            activeNcc,
                                            nccVms: virshEntry.ncc_vms || [],
                                        };
                                        device.sshConfig = device.sshConfig || {};
                                        device.sshConfig._isCluster = true;
                                        device.sshConfig._virshInfo = vi;
                                        device.sshConfig._virshCmd = activeNcc ? `sudo virsh console --force ${activeNcc}` : '';
                                    }
                                } catch (probeErr) {
                                    console.warn(`[SSH] GHOST-IP probe for virsh failed: ${probeErr && probeErr.message}`);
                                }
                            }

                            if (vi && vi.kvmHost && typeof window.TerminalPanel !== 'undefined' && window.TerminalPanel.open) {
                                const activeNcc = vi.activeNcc || (vi.nccVms && vi.nccVms[0]) || '';
                                console.log(`[SSH] GHOST-IP -> virsh console via web terminal: kvm=${vi.kvmHost}, ncc=${activeNcc}`);
                                const recoveryLabel = `${device.label || 'Cluster'} (recovery via virsh, mgmt IP ghosted)`;
                                window.TerminalPanel.open({
                                    deviceId: device.label || device.id || '',
                                    host: vi.kvmHost,
                                    method: 'virsh_console',
                                    deviceLabel: recoveryLabel,
                                    user: vi.kvmUser || 'dn',
                                    password: vi.kvmPass || 'drive1234!',
                                    virshInfo: {
                                        kvmHost: vi.kvmHost,
                                        kvmUser: vi.kvmUser || 'dn',
                                        kvmPass: vi.kvmPass || 'drive1234!',
                                        nccVms: vi.nccVms || [],
                                        activeNcc,
                                    },
                                });
                                if (this._fireBackgroundNccDiscovery) {
                                    this._fireBackgroundNccDiscovery(editor, device, {
                                        kvmHost: vi.kvmHost,
                                        kvmUser: vi.kvmUser || 'dn',
                                        kvmPass: vi.kvmPass || 'drive1234!',
                                        nccVms: vi.nccVms || [],
                                        activeNcc,
                                    });
                                }
                                const banner = `[GHOST IP] ${device.label}: ${host} now belongs to "${verify.actual_hostname}". Opened virsh console on ${vi.kvmHost} (NCC ${activeNcc || 'console'}).`;
                                if (editor.showNotification) editor.showNotification(banner, 'warning', 10000);
                                return;
                            }

                            // Non-cluster or no virsh info -- keep legacy behavior
                            const banner = `[GHOST IP] ${device.label}: ${host} now belongs to "${verify.actual_hostname}". Stale record cleared -- open SSH to re-discover.`;
                            if (editor.showNotification) editor.showNotification(banner, 'warning', 10000);
                            if (editor.showSSHAddressDialog) editor.showSSHAddressDialog(device);
                            return;
                        }
                        if (verify && verify.reason === 'generic_prompt') {
                            console.log(`[SSH] Identity ambiguous ('${verify.actual_hostname}') -- proceeding with ${host} (likely GI/RECOVERY mode).`);
                        } else if (verify && verify.identity_verified) {
                            console.log(`[SSH] Identity verified: ${host} = ${verify.actual_hostname || '(no banner)'}`);
                        }
                    } catch (e) {
                        console.warn(`[SSH] verify-identity failed (proceeding): ${e.message}`);
                    }
                }

                console.log(`[SSH] iTerm direct: ssh://${user}@${host} (mode=${_devMode}, cluster=${_isClusterDev})`);
                this._pendingPassword = password;
                this._pendingDevice = device;
                editor._openSshUrl(`ssh://${user}@${host}`);
                return;
            }
            if (host && _hostIsKvm) {
                console.log(`[SSH] Host is KVM hypervisor (${host}) -- skipping iTerm, using virsh console`);
            }

            // ===== NO HOST: fallback paths =====

            // Try enriched/cached NCC management IPs before probing
            {
                let iTermHost = sshConfig._enrichedMgmtIp || sshConfig._nccMgmtIp || null;
                if (iTermHost && iTermHost !== (sshConfig._virshInfo?.kvmHost || '')) {
                    console.log(`[SSH] iTerm (cached NCC mgmt): ssh://${user}@${iTermHost} (mode=${_devMode})`);
                    this._pendingPassword = password;
                    this._pendingDevice = device;
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
                this._pendingDevice = device;
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
                            const activeNcc = result.cluster?.active_ncc_vm || (virshEntry.vms_running?.[0]) || (virshEntry.ncc_vms || [])[0] || '';
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

            // ===== Post-probe: direct SSH via iTerm to best IP (any mode) =====
            {
                const dnosIP = bestIP || nccHost || (/^\d+\.\d+\.\d+\.\d+$/.test(host) ? host : null);
                const kvmH = clusterInfo?.kvmHost || sshConfig._virshInfo?.kvmHost || '';
                if (dnosIP && dnosIP !== kvmH) {
                    console.log(`[SSH] PROBE -> iTerm (mode=${probeMode||'default'}): ssh://${user}@${dnosIP}`);
                    this._pendingPassword = password;
                    this._pendingDevice = device;
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
                    this._pendingDevice = device;
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
                this._pendingDevice = device;
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
            this._pendingDevice = device;
            editor._openSshUrl(`ssh://${user}@${host}`);
        } catch (error) {
            console.error('[SSH] Error:', error);
            editor.showNotification(`Terminal error: ${error.message}`, 'error');
        }
    },

    /**
     * Resolve the active NCC's target for SSH on a cluster device. Returns
     * an object with BOTH the DNS hostname (e.g. "kvm108-cl408d-ncc1") and
     * the backend-resolved IPv4 (e.g. "100.64.4.122") so callers can pick
     * whichever fits their medium:
     *
     *   - iTerm / operator's Mac  -> prefer IP (Mac typically has lab
     *     routing via VPN but NOT lab DNS, so a hostname iTerm URL fails
     *     silently with "Could not resolve hostname").
     *   - UI display / notifications -> prefer hostname (human readable).
     *
     * The cluster mgmt IP follows whichever NCC is currently active
     * (mastership). This path survives mgmt-IP reaping, works in GI /
     * BASEOS_SHELL / RECOVERY, and always points at the node actually
     * running DNOS.
     *
     * NOTE: the legacy flow used the chassis serial + position
     * (e.g. "WDY1A17E00011-P3"), which is an NCP hostname -- not an NCC.
     *
     * Resolution order (parallel for host and ip):
     *   1. Cached on sshConfig._activeNccHost / _activeNccIp
     *   2. ScalerAPI.probeConnection -> cluster.active_ncc_host / active_ncc_ip
     *   3. ScalerAPI.probeConnection -> methods[ssh_ncc].host (+ dns_map lookup)
     *   4. ScalerAPI.probeConnection -> cluster.ncc_hosts[0] (ordered active-first)
     *   5. ScalerAPI.getDeviceContext -> active_ncc_host / active_ncc_node
     */
    async _getActiveNccTarget(device) {
        const out = { host: '', ip: '', source: '' };
        try {
            const c = device?.sshConfig || {};
            if (c._activeNccHost && typeof c._activeNccHost === 'string') {
                out.host = c._activeNccHost.trim();
            }
            if (c._activeNccIp && /^\d+\.\d+\.\d+\.\d+$/.test(c._activeNccIp)) {
                out.ip = c._activeNccIp.trim();
            }
            const mappedIp = out.host && c._activeNccDnsMap && c._activeNccDnsMap[out.host]
                ? String(c._activeNccDnsMap[out.host]).trim()
                : '';
            if (mappedIp && /^\d+\.\d+\.\d+\.\d+$/.test(mappedIp) && out.ip && out.ip !== mappedIp) {
                console.warn(
                    `[SSH] Cached active-NCC IP ${out.ip} does not match ${out.host} -> ${mappedIp}; `
                    + `discarding stale IP before launch.`
                );
                out.ip = '';
            }
            if (mappedIp && /^\d+\.\d+\.\d+\.\d+$/.test(mappedIp) && !out.ip) {
                out.ip = mappedIp;
            }
            if (out.host && out.ip) { out.source = 'cache'; return out; }
        } catch (_) {}

        if (typeof ScalerAPI !== 'undefined' && ScalerAPI.probeConnection) {
            try {
                const probe = await ScalerAPI.probeConnection(device.label || device.id || '', '');
                const cluster = (probe && probe.cluster) || {};
                if (!out.host) out.host = (cluster.active_ncc_host || '').trim();
                if (!out.ip) {
                    const ip = (cluster.active_ncc_ip || '').trim();
                    if (/^\d+\.\d+\.\d+\.\d+$/.test(ip)) out.ip = ip;
                }
                if (!out.ip && out.host && cluster.ncc_dns_map) {
                    const mapped = cluster.ncc_dns_map[out.host];
                    if (mapped && /^\d+\.\d+\.\d+\.\d+$/.test(mapped)) out.ip = mapped;
                }
                if (!out.host) {
                    const nccEntry = (probe.methods || []).find(m => m.method === 'ssh_ncc');
                    if (nccEntry && nccEntry.host) out.host = String(nccEntry.host).trim();
                }
                if (!out.host) {
                    const list = Array.isArray(cluster.ncc_hosts) ? cluster.ncc_hosts : [];
                    if (list.length > 0 && typeof list[0] === 'string') out.host = list[0].trim();
                }
                if (out.host || out.ip) {
                    out.source = cluster.active_ncc_source || 'probe';
                    device.sshConfig = device.sshConfig || {};
                    if (out.host) device.sshConfig._activeNccHost = out.host;
                    if (out.ip) device.sshConfig._activeNccIp = out.ip;
                    device.sshConfig._activeNccSource = out.source;
                    if (cluster.ncc_dns_map) device.sshConfig._activeNccDnsMap = cluster.ncc_dns_map;
                    return out;
                }
            } catch (e) {
                console.warn(`[SSH] _getActiveNccTarget: probe failed: ${e && e.message}`);
            }
        }

        if (typeof ScalerAPI !== 'undefined' && ScalerAPI.getDeviceContext) {
            try {
                const ctx = await ScalerAPI.getDeviceContext(device.label || device.id || '');
                if (!out.host) out.host = (ctx?.active_ncc_host || ctx?.active_ncc_node || '').trim();
                if (!out.ip) {
                    const ip = (ctx?.active_ncc_ip || '').trim();
                    if (/^\d+\.\d+\.\d+\.\d+$/.test(ip)) out.ip = ip;
                }
                if (out.host || out.ip) {
                    out.source = 'context';
                    device.sshConfig = device.sshConfig || {};
                    if (out.host) device.sshConfig._activeNccHost = out.host;
                    if (out.ip) device.sshConfig._activeNccIp = out.ip;
                    device.sshConfig._activeNccSource = 'context';
                }
            } catch (e) {
                console.warn(`[SSH] _getActiveNccTarget: context fetch failed: ${e && e.message}`);
            }
        }
        return out;
    },

    async _getActiveNccHost(device) {
        const t = await this._getActiveNccTarget(device);
        return t.host || '';
    },

    /**
     * Collect every plausible alias a stale SSH host-key entry could be
     * stored under for this device's active NCC. After a GI / RECOVERY
     * re-deploy the NCC gets brand-new ED25519 host keys, so `ssh` from
     * the operator's Mac bails with "Host key verification failed" and
     * iTerm silently closes the tab. We strip all of these at once so
     * the user never sees it.
     *
     * Collected from (in order):
     *   - the resolved active-NCC target (host + ip)
     *   - the device's DNS-map (all NCC hostnames and their resolved IPs)
     *   - the cluster mgmt IP currently stored on the device (was the
     *     active NCC mgmt IP before re-deploy; often reassigned to the
     *     new active NCC afterward)
     *   - any cached virsh / NCC-mgmt IP fields (same reasoning)
     *
     * Also adds a short-form of each hostname (token before the first
     * '.') because some operator ~/.ssh/known_hosts entries are stored
     * that way.
     */
    _collectStaleHostKeyTargets(device, resolvedTarget) {
        const cfg = (device && device.sshConfig) || {};
        const t = resolvedTarget || {};
        const out = new Set();
        const addHost = (v) => {
            if (!v || typeof v !== 'string') return;
            const s = v.trim();
            if (!s) return;
            out.add(s);
            const short = s.split('.')[0];
            if (short && short !== s) out.add(short);
        };
        const addIp = (v) => {
            if (!v || typeof v !== 'string') return;
            const s = v.trim();
            if (/^\d+\.\d+\.\d+\.\d+$/.test(s)) out.add(s);
        };
        addHost(t.host);
        addIp(t.ip);
        addHost(cfg._activeNccHost);
        addIp(cfg._activeNccIp);
        const dnsMap = cfg._activeNccDnsMap || {};
        Object.keys(dnsMap || {}).forEach((k) => {
            addHost(k);
            addIp(dnsMap[k]);
        });
        // The cluster mgmt IP is the moving target that followed the
        // active NCC across the re-deploy -- clear it too.
        const cfgHost = cfg.host || '';
        if (/^\d+\.\d+\.\d+\.\d+$/.test(cfgHost)) addIp(cfgHost);
        else addHost(cfgHost);
        addIp(cfg._nccMgmtIp);
        const vi = cfg._virshInfo || {};
        addIp(vi.nccMgmtIp);
        (vi.nccVms || []).forEach((n) => addHost(n));
        addHost(vi.activeNcc);
        return Array.from(out).filter(Boolean);
    },

    /**
     * Clear stale SSH host-key entries on the operator's Mac for every
     * alias this device's active NCC might be cached under. Designed to
     * run BEFORE a recovery-mode iTerm launch. On Mac-unreachable we
     * copy a ready-to-paste `ssh-keygen -R ...` command to the
     * clipboard and surface a toast so the user can fix it in one paste.
     *
     * Silent by design when everything succeeds (a single info toast);
     * noisy only when the Mac-side clear failed (so the user knows
     * iTerm may still reject the connection and what to paste).
     *
     * @param {object} editor         -- topology editor (for toasts)
     * @param {object} device         -- device record
     * @param {Array<string>} targets -- list from _collectStaleHostKeyTargets
     * @returns {Promise<{ok:boolean, macOk:boolean, targets:Array<string>}>}
     */
    async _clearStaleHostKeysOnMac(editor, device, targets) {
        const result = { ok: false, macOk: false, targets: targets || [] };
        if (!targets || targets.length === 0) return result;
        try {
            const authFetch = window.TopologyAuth?.authFetch
                ? window.TopologyAuth.authFetch.bind(window.TopologyAuth)
                : fetch;
            const resp = await authFetch('/api/ssh/clear-hostkey', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ hosts: targets }),
            });
            const data = await resp.json().catch(() => ({}));
            result.ok = !!data.ok;
            result.macOk = !!data.mac_cleared;
            // Timestamp + target snapshot let downstream dispatchers
            // (notably `_openSshUrl` with per-device `_autoClearHostKeys`)
            // skip re-clearing when this path already did the work
            // microseconds earlier. Without this a GI recovery launch
            // would clear twice (once in `_tryOpenActiveNccIterm`, once
            // in `_openSshUrl`).
            this._lastHostKeyClearAt = Date.now();
            this._lastHostKeyClearTargets = targets.slice();
            console.log(
                `[SSH] clear-hostkey targets=${targets.length} mac_ok=${result.macOk} `
                + `server_ok=${!!data.server_cleared} msg="${data.message || ''}"`
            );
            if (result.macOk) {
                if (editor && editor.showNotification) {
                    editor.showNotification(
                        `[OK] Cleared stale host keys on Mac (${targets.length} alias${targets.length === 1 ? '' : 'es'})`,
                        'success', 3500,
                    );
                }
                return result;
            }

            // Mac clear failed -- auto-copy the ssh-keygen commands so
            // the user can paste into their Terminal in one shot. This
            // is the most common recovery path when the operator's Mac
            // VPN IP is stale / Remote Login is off.
            const cmd = data.copy_command
                || targets.map((h) => `ssh-keygen -R ${h}`).join(' && ');
            try {
                await this._safeClipboardWrite(cmd);
                if (editor && editor.showNotification) {
                    editor.showNotification(
                        `[WARN] Mac clear failed (${data.message || 'unknown'}). `
                        + `Command copied -- paste it in your Mac Terminal, then retry.`,
                        'warning', 10000,
                    );
                }
            } catch (_clipErr) {
                if (editor && editor.showNotification) {
                    editor.showNotification(
                        `[WARN] Run on Mac: ${cmd}`,
                        'warning', 15000,
                    );
                }
            }
        } catch (e) {
            console.warn(`[SSH] clear-hostkey call failed: ${e && e.message}`);
            if (editor && editor.showNotification) {
                editor.showNotification(
                    `[WARN] Could not reach clear-hostkey API: ${e && e.message}`,
                    'warning', 6000,
                );
            }
        }
        return result;
    },

    /**
     * Launch iTerm against the active NCC's DNS hostname. This is the
     * pre-upgrade / pre-ghost-IP canonical recovery path for cluster
     * devices in GI / BASEOS_SHELL / RECOVERY.
     *
     * Unlike the IP-based flow there is no TCP pre-flight: the topology
     * server may be unable to resolve the NCC host (different subnet /
     * no lab DNS), but the user's Mac resolves it via lab DNS / VPN.
     *
     * Returns true when the ssh:// URL was dispatched to the OS handler,
     * false when no active-NCC hostname could be resolved.
     */
    async _tryOpenActiveNccIterm(editor, device, opts) {
        opts = opts || {};
        const modeLabel = opts.modeLabel || '';
        const user = opts.user || 'dnroot';
        const password = opts.password || 'dnroot';
        // `forceIterm` (default true for recovery callers): the GI/BASEOS_SHELL/
        // RECOVERY and ghost-IP paths represent an *explicit* operator intent --
        // "get me onto the active NCC via iTerm right now, regardless of what I
        // picked in the SSH dialog weeks ago". It bypasses any sticky
        // `sshConfig.preferredMethod = 'webterm'` that would otherwise flip
        // `_openSshUrl` to the web terminal. The sticky stays persisted; only
        // this one launch ignores it.
        const forceIterm = opts.forceIterm !== false;
        // `preferIp` (default false): CL-86 cluster launches should show and
        // use the active NCC identity (for example kvm108-cl408d-ncc1), not a
        // cached chassis/NCP serial and not a per-node IP. Callers may opt into
        // IP only for explicit network-reachability fallback.
        const preferIp = opts.preferIp === true;
        // `clearStaleHostKeys` (default true for recovery callers): GI /
        // BASEOS_SHELL / RECOVERY / ghost-IP launches happen AFTER a
        // re-deploy, which always gives the NCC fresh ED25519 host keys.
        // The operator's `~/.ssh/known_hosts` still holds the old key,
        // so `ssh` bails with "Host key verification failed" and iTerm
        // closes the tab before the user sees the error. We pre-clear
        // every alias the key may be stored under (NCC hostnames, short
        // forms, cluster mgmt IP, NCC mgmt IPs) and only then launch.
        // Mac-unreachable is handled by auto-copying a ready-to-paste
        // `ssh-keygen -R ...` command to the clipboard.
        const clearStaleHostKeys = opts.clearStaleHostKeys !== false;

        const target = await this._getActiveNccTarget(device);
        const host = target.host || '';
        const ip = target.ip || '';
        if (!host && !ip) {
            console.warn(`[SSH] _tryOpenActiveNccIterm: no active NCC target resolved for ${device.label || device.id}`);
            return false;
        }
        // Pick the ssh:// target: prefer IP when we have it so Mac DNS is
        // taken out of the equation. Keep the hostname for the toast so
        // the operator sees which NCC they landed on.
        const sshTarget = (preferIp && ip) ? ip : (host || ip);
        const displayLabel = host || ip;

        device.sshConfig = device.sshConfig || {};
        if (host) device.sshConfig._activeNccHost = host;
        if (ip) device.sshConfig._activeNccIp = ip;
        device.sshConfig._lastLaunchVia = 'ssh_active_ncc';
        device.sshConfig._lastLaunchAt = Date.now();

        const src = device.sshConfig._activeNccSource || target.source || '';
        const usedIp = sshTarget === ip && ip;
        console.log(
            `[SSH] -> iTerm via active NCC: ssh://${user}@${sshTarget} `
            + `(host=${host || '-'} ip=${ip || '-'})`
            + `${modeLabel ? ' ['+modeLabel+']' : ''}`
            + `${src ? ' [src='+src+']' : ''}`
            + `${usedIp ? ' [using-ip]' : ' [using-hostname]'}`
            + `${forceIterm ? ' [force-iterm]' : ''}`
            + `${clearStaleHostKeys ? ' [clear-stale-keys]' : ''}`
        );

        // Strip stale known_hosts entries BEFORE handing the ssh:// URL
        // to the OS. We do this synchronously (await) because the whole
        // point is that iTerm will refuse to connect otherwise -- there
        // is no value in racing the ssh launch against the ssh-keygen
        // call.
        if (clearStaleHostKeys) {
            const stale = this._collectStaleHostKeyTargets(device, target);
            if (stale.length > 0) {
                console.log(`[SSH] pre-launch: clearing ${stale.length} stale host-key alias(es): ${stale.join(', ')}`);
                await this._clearStaleHostKeysOnMac(editor, device, stale);
            }
        }

        this._pendingPassword = password;
        this._pendingDevice = device;
        if (forceIterm) this._forceItermOnce = true;
        if (editor._openSshUrl) editor._openSshUrl(`ssh://${user}@${sshTarget}`);

        const suffix = modeLabel ? ` (${modeLabel})` : '';
        if (editor.showNotification) {
            const niceTarget = (host && ip) ? `${host} (${ip})` : (host || ip);
            editor.showNotification(
                `[OK] iTerm -> ${niceTarget}${suffix}`,
                'success',
                5000,
            );
        }
        return true;
    },

    /**
     * If NCC mgmt IP answers on port 22, open iTerm (dnroot). Checks _nccMgmtIp first,
     * then falls back to sshConfig.host if it differs from the KVM host.
     */
    async _tryOpenClusterNccMgmtIterm(editor, device, sshConfig) {
        const cfg = sshConfig || device.sshConfig || {};
        const vi = cfg._virshInfo || {};
        const kvmHost = vi.kvmHost || '';
        const candidates = new Set();
        const nccIp = (cfg._nccMgmtIp || '').trim();
        if (nccIp && /^\d+\.\d+\.\d+\.\d+$/.test(nccIp)) candidates.add(nccIp);
        const enriched = (cfg._enrichedMgmtIp || '').trim();
        if (enriched && /^\d+\.\d+\.\d+\.\d+$/.test(enriched)) candidates.add(enriched);

        if (candidates.size === 0 && typeof ScalerAPI !== 'undefined' && ScalerAPI.getDeviceContext) {
            try {
                const ctx = await ScalerAPI.getDeviceContext(device.label || device.id || '');
                const ctxIp = (ctx?.ncc_mgmt_ip || ctx?.ssh_host || '').trim();
                if (ctxIp && /^\d+\.\d+\.\d+\.\d+$/.test(ctxIp) && ctxIp !== kvmHost) {
                    candidates.add(ctxIp);
                    console.log(`[SSH] NCC IP from device context: ${ctxIp}`);
                }
            } catch (e) {
                console.warn('[SSH] device context fetch for NCC IP:', e?.message);
            }
        }

        const hostIp = (cfg.host || '').trim();
        if (hostIp && /^\d+\.\d+\.\d+\.\d+$/.test(hostIp) && hostIp !== kvmHost) {
            candidates.add(hostIp);
        }
        if (candidates.size === 0) return false;
        if (typeof ScalerAPI === 'undefined' || !ScalerAPI.checkPort) return false;

        const ports = [22, 2222];
        for (const ip of candidates) {
            for (const port of ports) {
                try {
                    const chk = await ScalerAPI.checkPort(ip, port);
                    if (chk && chk.reachable) {
                        const sshUrl = port === 22
                            ? `ssh://dnroot@${ip}`
                            : `ssh://dnroot@${ip}:${port}`;
                        this._pendingPassword = 'dnroot';
                        this._pendingDevice = device;
                        if (editor._openSshUrl) editor._openSshUrl(sshUrl);
                        device.sshConfig = device.sshConfig || {};
                        device.sshConfig._nccMgmtIp = ip;
                        if (editor.showNotification) {
                            editor.showNotification(
                                `[OK] iTerm to NCC management ${ip}${port !== 22 ? ':' + port : ''}`,
                                'success', 4000);
                        }
                        return true;
                    }
                } catch (e) {
                    console.warn(`[SSH] checkPort NCC mgmt ${ip}:${port}:`, e?.message);
                }
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
    
    /**
     * Remote-access detection: the app is being served from a topology server
     * on a remote host (ie. the user's browser is NOT on the same network as
     * the lab). In this case the OS ssh:// handler runs on the user's machine
     * and cannot route to lab-internal IPs (100.64.x.x etc.). We detect remote
     * access by comparing window.location.hostname against a known local list,
     * and we detect "lab IPs" by matching RFC1918/CGNAT ranges.
     */
    _isRemoteBrowser() {
        try {
            const h = (window.location && window.location.hostname || '').toLowerCase();
            if (!h) return false;
            if (h === 'localhost' || h === '127.0.0.1' || h === '::1' || h === '0.0.0.0') return false;
            // Loopback + unspecified: treat as local.
            return true;
        } catch (_) {
            return false;
        }
    },

    _isLabIP(host) {
        if (!host) return false;
        const m = String(host).match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
        if (!m) return false;
        const a = +m[1], b = +m[2];
        if (a === 10) return true;
        if (a === 172 && b >= 16 && b <= 31) return true;
        if (a === 192 && b === 168) return true;
        if (a === 100 && b >= 64 && b <= 127) return true;
        return false;
    },

    /**
     * Global SSH launch preference, persisted in localStorage under
     * `xdn_ssh_launch_pref`. Three values:
     *   auto    -- platform-aware default (macOS/iOS -> iTerm, others -> web)
     *   iterm   -- always iTerm via the `ssh://` URL handler
     *   webterm -- always the in-browser web terminal via the bridge proxy
     *
     * Callers should prefer the per-device sticky key on `sshConfig.preferredMethod`
     * when present (set from the "Connect via" picker in the SSH dialog and
     * honoured below) -- the global pref is the fallback.
     */
    _getSshLaunchPref() {
        try {
            const v = localStorage.getItem('xdn_ssh_launch_pref');
            if (v === 'iterm' || v === 'webterm' || v === 'auto') return v;
        } catch (_) {}
        return 'auto';
    },

    /**
     * Detect Mac/iOS user agents. macOS (and iPadOS posing as Mac) is where
     * the `ssh://` URL handler reliably launches iTerm/Terminal and where
     * the user explicitly asked for the iTerm experience. On Linux/Windows
     * the same click usually 404s, so auto-mode routes to the web terminal.
     */
    _isMacUA() {
        const ua = (navigator && (navigator.userAgent || '')) || '';
        if (/iPhone|iPad|iPod/.test(ua)) return true;
        // Modern iPadOS reports "Macintosh" plus `ontouchend`.
        if (/Macintosh|Mac OS X/i.test(ua)) return true;
        // Safari on macOS exposes `platform` reliably.
        try {
            const plat = (navigator && (navigator.platform || '')) || '';
            if (/Mac|iPhone|iPad/i.test(plat)) return true;
        } catch (_) {}
        return false;
    },

    /**
     * Decide iTerm vs web-terminal for a resolved (user, host, device) triplet.
     *
     * Priority (first rule wins):
     *   1. Per-device `sshConfig.preferredMethod` sticky pref.
     *   2. Global localStorage `xdn_ssh_launch_pref` explicit override.
     *   3. Platform default: macOS/iOS -> iTerm; everything else -> web.
     *
     * The legacy "remote browser + lab IP -> web" heuristic was wrong: Mac
     * users connected via VPN *do* reach lab IPs, and the ssh:// handler is
     * exactly what they installed iTerm for. If auto-mode is wrong for a
     * specific device the user can pin it via the dialog picker in one click.
     *
     * The `why` return field is surfaced in console logs so future
     * debugging of "it picked the wrong method" is a grep away.
     */
    _pickLaunchMethod(host, device) {
        // Per-device sticky FIRST (matches JSDoc above + SSH-dialog segmented
        // control contract: "Connect via" explicitly pins a device). Before
        // 2026-04-24 this order was inverted -- global localStorage pref
        // short-circuited per-device sticky, so toggling Auto/iTerm/Web in
        // the SSH dialog appeared to do nothing whenever a global pref was
        // set (tests / docs / a stale key in the operator's browser).
        const sticky = device && device.sshConfig && device.sshConfig.preferredMethod;
        if (sticky === 'iterm') return { web: false, why: 'device-sticky=iterm' };
        if (sticky === 'webterm') {
            return { web: !!(window.TerminalPanel && window.TerminalPanel.open),
                     why: 'device-sticky=webterm' };
        }
        const pref = this._getSshLaunchPref();
        if (pref === 'iterm') return { web: false, why: 'global-pref=iterm' };
        if (pref === 'webterm') {
            return { web: !!(window.TerminalPanel && window.TerminalPanel.open),
                     why: 'global-pref=webterm' };
        }
        if (this._isMacUA()) return { web: false, why: 'auto mac-ua -> iterm' };
        return {
            web: !!(window.TerminalPanel && window.TerminalPanel.open),
            why: 'auto non-mac -> webterm',
        };
    },

    _shouldUseWebTerminal(host, device) {
        // One-shot override: callers (e.g. GI/RECOVERY active-NCC iTerm path)
        // set `_forceItermOnce` when they want to bypass the sticky
        // `sshConfig.preferredMethod = 'webterm'` for this single launch.
        // The flag is consumed here so the next unrelated click restores the
        // sticky preference automatically -- no need to clear anything.
        if (this._forceItermOnce) {
            try { console.log(`[SSH] method decision: host=${host} web=false reason=force-iterm-once (recovery-intent bypass)`); } catch (_) {}
            this._forceItermOnce = false;
            return false;
        }
        const decision = this._pickLaunchMethod(host, device);
        try { console.log(`[SSH] method decision: host=${host} web=${decision.web} reason=${decision.why}`); } catch (_) {}
        return decision.web;
    },

    _openSshUrl(editor, url) {
        console.log(`[SSH] _openSshUrl: ${url}`);
        try {
            const sshMatch = url.match(/ssh:\/\/([^@]+)@(.+)/);
            const user = sshMatch ? sshMatch[1] : '';
            const host = sshMatch ? sshMatch[2] : '';
            const cmd = sshMatch ? `ssh ${user}@${host}` : url;

            // `_pendingDevice` is set by `openTerminalToDevice` right before
            // calling `_openSshUrl` so the launch decision can consider the
            // per-device sticky preference (sshConfig.preferredMethod). Falls
            // back to lookup by host/label if the caller forgot to set it.
            const device = this._pendingDevice
                || this._findDeviceForSsh(editor, host, user)
                || null;

            // Auto-switch to web terminal when the decision tree picks it:
            // global pref = webterm, per-device sticky = webterm, or auto mode
            // on a non-Mac user agent. Mac users always get iTerm in auto mode.
            if (this._shouldUseWebTerminal(host, device) && window.TerminalPanel?.open) {
                const password = this._pendingPassword || '';
                console.log(`[SSH] -> web terminal: ${user}@${host}`);
                window.TerminalPanel.open({
                    deviceId: (device && (device.label || device.id)) || host,
                    host,
                    user: user || 'dnroot',
                    password,
                    method: 'ssh_mgmt',
                    deviceLabel: `${(device && device.label) || host} (web terminal)`,
                });
                editor.showNotification(`[OK] Web terminal: ${cmd}`, 'success', 5000);
                this._pendingPassword = null;
                this._pendingDevice = null;
                return;
            }

            // Per-device persistent intent: if the operator checked
            // "Auto-clear host key on connect" in the SSH dialog, clear
            // stale `known_hosts` entries on the Mac before dispatching
            // the ssh:// URL. The recovery-mode callers (GI/BASEOS/
            // RECOVERY/ghost-IP) already pre-clear inside
            // `_tryOpenActiveNccIterm`, but a healthy DNOS device whose
            // NCC was re-deployed at some point will also accumulate
            // stale keys -- and those launches come through here, NOT
            // through the recovery path. This hook bridges that gap.
            //
            // We wrap the dispatch in an async IIFE so the ssh:// URL
            // only fires AFTER the clear resolves. Without the await
            // iTerm would race the ssh-keygen and hit the stale entry.
            const shouldAutoClear = !!(device
                && device.sshConfig
                && device.sshConfig._autoClearHostKeys);

            const dispatchIterm = () => {
                // iTerm path: dispatch ssh:// via anchor click so the page doesn't unload.
                const link = document.createElement('a');
                link.href = url;
                link.style.display = 'none';
                document.body.appendChild(link);
                link.click();
                setTimeout(() => { try { link.remove(); } catch(_){} }, 500);
                console.log(`[SSH] -> iTerm ssh:// dispatched for: ${url}`);

                const password = this._pendingPassword || '';
                const devForFallback = device;
                if (password) {
                    this._safeClipboardWrite(password).then(() => {
                        this._showItermOpenedToast(editor, devForFallback, user, host, password, `${cmd}. Password copied -- paste with Cmd+V.`);
                    }).catch(() => {
                        this._showItermOpenedToast(editor, devForFallback, user, host, password, `${cmd}. Password: ${password}`);
                    });
                } else {
                    this._showItermOpenedToast(editor, devForFallback, user, host, password, cmd);
                }
                this._pendingPassword = null;
                this._pendingDevice = null;
            };

            if (shouldAutoClear && typeof this._clearStaleHostKeysOnMac === 'function') {
                // Collect every alias the stale key could be stored under.
                // Always include the actual ssh-target host so we clear the
                // exact entry the user's `ssh` command will look up.
                const resolved = { host: device.sshConfig._activeNccHost || '', ip: device.sshConfig._activeNccIp || '' };
                const aliases = (typeof this._collectStaleHostKeyTargets === 'function')
                    ? this._collectStaleHostKeyTargets(device, resolved)
                    : [];
                const merged = new Set(aliases);
                if (host) merged.add(host);
                const targets = Array.from(merged).filter(Boolean);

                // Skip if another code path (typically the GI/RECOVERY
                // `_tryOpenActiveNccIterm`) already fired the same
                // clear a few hundred ms ago. Saves a round-trip and
                // avoids a redundant toast.
                const freshWindowMs = 4000;
                const recentlyCleared = this._lastHostKeyClearAt
                    && (Date.now() - this._lastHostKeyClearAt) < freshWindowMs;
                const recentTargets = this._lastHostKeyClearTargets || [];
                const coveredByRecent = recentlyCleared
                    && targets.every((t) => recentTargets.indexOf(t) !== -1);

                if (coveredByRecent) {
                    console.log(`[SSH] _openSshUrl: auto-clear skipped (covered by recent clear ${Date.now() - this._lastHostKeyClearAt}ms ago)`);
                    dispatchIterm();
                    return;
                }

                console.log(`[SSH] _openSshUrl: auto-clear enabled for ${device.label || device.id} -- ${targets.length} alias(es)`);
                (async () => {
                    try {
                        await this._clearStaleHostKeysOnMac(editor, device, targets);
                    } catch (_) { /* user already saw the warning toast */ }
                    dispatchIterm();
                })();
                return;
            }

            dispatchIterm();
        } catch (error) {
            console.error('[SSH] _openSshUrl error:', error);
            editor.showNotification(`SSH error: ${error.message}`, 'error');
            this._pendingDevice = null;
            this._forceItermOnce = false;
        }
    },

    /**
     * Fallback lookup when `_openSshUrl` is called without a pre-set
     * `_pendingDevice`. Scans the editor's device list for a matching
     * sshConfig host/user; used so callers (e.g. SSH dialog Connect button)
     * that build the ssh:// URL directly still benefit from per-device
     * preferredMethod.
     */
    _findDeviceForSsh(editor, host, user) {
        try {
            const devices = (editor && editor.devices) || [];
            for (const d of devices) {
                const c = d && d.sshConfig;
                if (!c) continue;
                const h = c._userSavedHost || c.host;
                if (h && host && h === host) return d;
            }
        } catch (_) {}
        return null;
    },

    /**
     * Glass toast notification shown after an ssh:// URL is dispatched to
     * iTerm. Includes a "Web Terminal" action button that opens the
     * bridge-proxied web terminal to the same host -- the reliable fallback
     * when the user's Mac cannot route to lab CGNAT IPs (iTerm opens but
     * never connects) or when iTerm's ssh:// handler is misconfigured.
     *
     * Backward-compatible: callers that previously used editor.showNotification
     * for the iTerm message now get the same text plus an actionable fallback
     * in the same toast slot (replaces the prior notification).
     */
    _showItermOpenedToast(editor, device, user, host, password, messageBody) {
        try {
            const baseMsg = `[OK] iTerm: ${messageBody || `ssh ${user || 'dnroot'}@${host}`}`;
            // Web terminal must be available to show the fallback button.
            // If not, just use the plain notification (graceful degrade).
            if (!window.TerminalPanel || !window.TerminalPanel.open) {
                if (editor?.showNotification) editor.showNotification(baseMsg, 'success', 5000);
                return;
            }

            // Remove any existing notification so the fallback toast owns the slot
            const existing = document.getElementById('topology-notification');
            if (existing) existing.remove();
            const existingFallback = document.getElementById('topology-iterm-fallback-toast');
            if (existingFallback) existingFallback.remove();

            if (!document.getElementById('iterm-fallback-toast-styles')) {
                const s = document.createElement('style');
                s.id = 'iterm-fallback-toast-styles';
                s.textContent = `
                    @keyframes itermFallbackIn {
                        0%   { opacity:0; transform:translateX(-50%) translateY(16px) scale(0.92); }
                        60%  { opacity:1; transform:translateX(-50%) translateY(-3px) scale(1.01); }
                        100% { opacity:1; transform:translateX(-50%) translateY(0) scale(1); }
                    }
                    @keyframes itermFallbackOut {
                        0%   { opacity:1; transform:translateX(-50%) translateY(0) scale(1); }
                        100% { opacity:0; transform:translateX(-50%) translateY(10px) scale(0.95); }
                    }
                    @keyframes itermFallbackProgress {
                        from { transform: scaleX(1); }
                        to   { transform: scaleX(0); }
                    }
                `;
                document.head.appendChild(s);
            }

            const dk = document.body.classList.contains('dark-mode');
            const accent = '#4ade80';
            const glow = 'rgba(74,222,128,0.25)';
            const fallbackAccent = '#60a5fa';
            const duration = 9000;

            const toast = document.createElement('div');
            toast.id = 'topology-iterm-fallback-toast';
            toast.style.cssText = `
                position: fixed;
                bottom: 24px;
                left: 50%;
                transform: translateX(-50%);
                padding: 12px 16px 12px 16px;
                border-radius: 14px;
                font-size: 14px;
                color: ${dk ? 'rgba(255,255,255,0.92)' : 'rgba(15,15,30,0.88)'};
                z-index: 10000;
                animation: itermFallbackIn 0.35s cubic-bezier(0.22,1,0.36,1) forwards;
                background: ${dk
                    ? 'linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.03) 100%)'
                    : 'linear-gradient(135deg, rgba(255,255,255,0.75) 0%, rgba(255,255,255,0.55) 100%)'};
                backdrop-filter: blur(24px) saturate(1.6);
                -webkit-backdrop-filter: blur(24px) saturate(1.6);
                border: 1px solid ${dk ? 'rgba(74,222,128,0.3)' : 'rgba(255,255,255,0.6)'};
                box-shadow:
                    0 8px 32px rgba(0,0,0,${dk ? '0.45' : '0.1'}),
                    0 2px 8px ${glow},
                    inset 0 1px 0 ${dk ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.7)'};
                max-width: min(640px, 90vw);
                font-family: 'Poppins', -apple-system, sans-serif;
                display: flex;
                align-items: center;
                gap: 12px;
                overflow: hidden;
            `;

            const iconWrap = document.createElement('span');
            iconWrap.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>';
            iconWrap.style.cssText = `color: ${accent}; flex-shrink: 0; display: flex; align-items: center; filter: drop-shadow(0 0 4px ${glow});`;

            const textWrap = document.createElement('div');
            textWrap.style.cssText = 'display:flex; flex-direction:column; gap:2px; min-width:0; flex:1;';
            const mainText = document.createElement('span');
            mainText.textContent = baseMsg;
            mainText.style.cssText = 'line-height:1.4; font-weight:500; letter-spacing:0.1px; word-break:break-word;';
            const hintText = document.createElement('span');
            hintText.textContent = 'Not connecting? Use the Web Terminal fallback (bridge-proxied).';
            hintText.style.cssText = `font-size: 11px; opacity: 0.7; line-height: 1.3; color: ${dk ? 'rgba(255,255,255,0.75)' : 'rgba(15,15,30,0.7)'};`;
            textWrap.appendChild(mainText);
            textWrap.appendChild(hintText);

            const actions = document.createElement('div');
            actions.style.cssText = 'display:flex; align-items:center; gap:6px; flex-shrink:0;';

            const webBtn = document.createElement('button');
            webBtn.type = 'button';
            webBtn.textContent = 'Web Terminal';
            webBtn.title = 'Open the bridge-proxied web terminal to the same host (reliable when iTerm cannot reach lab IPs)';
            webBtn.style.cssText = `
                padding: 6px 12px;
                border-radius: 8px;
                border: 1px solid ${fallbackAccent};
                background: ${dk ? 'rgba(96,165,250,0.18)' : 'rgba(96,165,250,0.12)'};
                color: ${fallbackAccent};
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                font-family: inherit;
                white-space: nowrap;
            `;
            webBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                try {
                    const dLabel = (device && (device.label || device.id)) || host;
                    console.log(`[SSH] iTerm fallback -> web terminal for ${dLabel}`);
                    window.TerminalPanel.open({
                        deviceId: dLabel,
                        host,
                        user: user || 'dnroot',
                        password: password || 'dnroot',
                        method: 'ssh_mgmt',
                        deviceLabel: `${(device && device.label) || host} (web terminal)`,
                    });
                    if (editor?.showNotification) {
                        editor.showNotification(`[OK] Web terminal: ssh ${user || 'dnroot'}@${host}`, 'success', 4000);
                    }
                } catch (err) {
                    console.error('[SSH] Web terminal fallback failed:', err);
                    if (editor?.showNotification) {
                        editor.showNotification(`Web terminal error: ${err.message}`, 'error');
                    }
                }
                toast.style.animation = 'itermFallbackOut 0.25s cubic-bezier(0.22,1,0.36,1) forwards';
                setTimeout(() => toast.remove(), 250);
            });

            const closeBtn = document.createElement('button');
            closeBtn.type = 'button';
            closeBtn.setAttribute('aria-label', 'Dismiss');
            closeBtn.innerHTML = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
            closeBtn.style.cssText = `
                padding: 4px;
                border-radius: 6px;
                border: none;
                background: transparent;
                color: ${dk ? 'rgba(255,255,255,0.6)' : 'rgba(15,15,30,0.5)'};
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
            `;
            closeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                toast.style.animation = 'itermFallbackOut 0.25s cubic-bezier(0.22,1,0.36,1) forwards';
                setTimeout(() => toast.remove(), 250);
            });

            actions.appendChild(webBtn);
            actions.appendChild(closeBtn);

            const progress = document.createElement('div');
            progress.style.cssText = `
                position: absolute;
                bottom: 0; left: 0; right: 0;
                height: 2px;
                background: linear-gradient(90deg, transparent, ${accent}80, ${accent}, ${accent}80, transparent);
                transform-origin: left;
                animation: itermFallbackProgress ${duration}ms linear forwards;
                border-radius: 0 0 14px 14px;
            `;

            toast.appendChild(iconWrap);
            toast.appendChild(textWrap);
            toast.appendChild(actions);
            toast.appendChild(progress);
            document.body.appendChild(toast);

            setTimeout(() => {
                if (toast.parentNode) {
                    toast.style.animation = 'itermFallbackOut 0.3s cubic-bezier(0.22,1,0.36,1) forwards';
                    setTimeout(() => toast.remove(), 300);
                }
            }, duration);
        } catch (err) {
            console.warn('[SSH] _showItermOpenedToast failed, falling back to plain notification:', err);
            if (editor?.showNotification) editor.showNotification(messageBody ? `[OK] iTerm: ${messageBody}` : `[OK] iTerm opened`, 'success', 5000);
        }
    },

    _showSshUnreachableNotification(editor, device, host, devMode, hasVirsh, failKind) {
        const label = device.label || host;
        const modeHint = devMode ? ` (device in ${devMode} mode)` : '';
        let reason;
        if (failKind === 'auth_unreliable') {
            reason = `SSH port 22 is open on ${host} but the device is in ${devMode || 'recovery'} mode. ` +
                'Standard credentials may not work and sessions may hang. ' +
                'Use Web Terminal (virsh console) for reliable access.';
        } else {
            reason = `SSH port 22 is not reachable on ${host}${modeHint}. ` +
                (devMode === 'GI' || devMode === 'BASEOS_SHELL'
                    ? 'The device may be in base OS shell without SSH running.'
                    : 'Check network connectivity or device state.');
        }

        const overlay = document.createElement('div');
        overlay.style.cssText = 'position:fixed;inset:0;z-index:100000;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.45);';
        overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });

        const isDark = document.body.classList.contains('dark-mode') ||
            window.matchMedia?.('(prefers-color-scheme: dark)').matches;
        const bg = isDark ? '#1e2333' : '#ffffff';
        const txt = isDark ? '#e0e0e0' : '#1a1a2e';
        const muted = isDark ? '#8899aa' : '#666';
        const border = isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
        const isAuthWarn = failKind === 'auth_unreliable';
        const badgeBg = isAuthWarn ? '#e67e22' : '#e74c3c';
        const titleText = isAuthWarn ? `SSH Unstable: ${label}` : `SSH Unreachable: ${label}`;
        const badgeIcon = isAuthWarn
            ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`
            : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`;

        const card = document.createElement('div');
        card.style.cssText = `background:${bg};color:${txt};border-radius:12px;padding:24px 28px;` +
            `max-width:440px;width:90%;box-shadow:0 8px 32px rgba(0,0,0,0.3);border:1px solid ${border};`;

        let html = `<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">` +
            `<div style="width:36px;height:36px;border-radius:50%;background:${badgeBg};display:flex;align-items:center;justify-content:center;">` +
            `${badgeIcon}</div>` +
            `<div style="font-weight:600;font-size:15px;">${titleText}</div></div>` +
            `<div style="font-size:13px;color:${muted};margin-bottom:18px;line-height:1.5;">${reason}</div>` +
            `<div style="display:flex;gap:8px;flex-wrap:wrap;">`;

        if (hasVirsh) {
            html += `<button id="_ssh_virsh_btn" style="padding:8px 16px;border-radius:6px;border:none;` +
                `background:#e67e22;color:#fff;font-size:13px;font-weight:600;cursor:pointer;">` +
                `Web Terminal (virsh console)</button>`;
        }
        html += `<button id="_ssh_dialog_btn" style="padding:8px 16px;border-radius:6px;border:1px solid ${border};` +
            `background:transparent;color:${txt};font-size:13px;cursor:pointer;">` +
            `SSH Settings</button>`;
        html += `<button id="_ssh_force_btn" style="padding:8px 16px;border-radius:6px;border:1px solid ${border};` +
            `background:transparent;color:${muted};font-size:12px;cursor:pointer;">` +
            `Try iTerm anyway</button>`;
        html += `<button id="_ssh_close_btn" style="padding:8px 16px;border-radius:6px;border:1px solid ${border};` +
            `background:transparent;color:${muted};font-size:13px;cursor:pointer;">Close</button>`;
        html += '</div>';
        card.innerHTML = html;
        overlay.appendChild(card);
        document.body.appendChild(overlay);

        card.querySelector('#_ssh_close_btn').addEventListener('click', () => overlay.remove());
        card.querySelector('#_ssh_dialog_btn').addEventListener('click', () => {
            overlay.remove();
            if (editor.showSSHAddressDialog) editor.showSSHAddressDialog(device);
        });
        card.querySelector('#_ssh_force_btn').addEventListener('click', () => {
            overlay.remove();
            const sshCfg = device.sshConfig || {};
            this._pendingPassword = sshCfg._userSavedPass || sshCfg.password || 'dnroot';
            this._pendingDevice = device;
            editor._openSshUrl(`ssh://${sshCfg._userSavedUser || sshCfg.user || 'dnroot'}@${host}`);
        });
        if (hasVirsh) {
            card.querySelector('#_ssh_virsh_btn').addEventListener('click', () => {
                overlay.remove();
                const vi = device.sshConfig?._virshInfo || {};
                if (vi.kvmHost && window.TerminalPanel?.open) {
                    window.TerminalPanel.open({
                        deviceId: device.label || device.id || '',
                        host: vi.kvmHost,
                        user: vi.kvmUser || 'dn',
                        method: 'virsh_console',
                        deviceLabel: `${device.label || 'Cluster'} (virsh -> ${vi.activeNcc || 'NCC'})`,
                        password: vi.kvmPass || 'drive1234!',
                        virshInfo: vi,
                    });
                    editor.showNotification(`[OK] Web terminal opened via virsh console`, 'success', 4000);
                } else {
                    editor.showNotification('[WARN] Virsh info not available. Open SSH Settings to probe.', 'warning', 5000);
                }
            });
        }
    },

    /**
     * Force a single, immediate cluster-identity refresh for a device --
     * used right after a successful credential verification so the canvas
     * tooltip / sticky host / active-NCC details refresh within ~1s,
     * without waiting for the 5-min DeviceMonitor cycle.
     *
     * Wraps `ScalerAPI.probeConnection` and folds the result into
     * `device.sshConfig._activeNccHost / _activeNccIp / _kvmHost / _nccVms`
     * the same way the existing probe paths in this file do.
     *
     * Returns a Promise that resolves with the probe result, or null if
     * the probe could not run.
     */
    async refreshDeviceContext(device, opts = {}) {
        if (!device || typeof ScalerAPI === 'undefined' || !ScalerAPI.probeConnection) {
            return null;
        }
        const deviceId = device.label || device.id || '';
        if (!deviceId) return null;
        const probeHost = (device.sshConfig && (device.sshConfig._userSavedHost || device.sshConfig.host)) || '';
        const identityGuard = window.TopologyDeviceIdentity || null;
        const identityToken = identityGuard?.makeRequestToken
            ? identityGuard.makeRequestToken(device, { host: probeHost, deviceId })
            : null;
        let result = null;
        try {
            result = await ScalerAPI.probeConnection(deviceId, probeHost);
        } catch (err) {
            console.warn('[ObjectDetection.refreshDeviceContext] probe failed:', err && err.message);
            return null;
        }
        if (identityGuard?.signature && identityToken && identityGuard.signature(device, probeHost) !== identityToken.signature) {
            console.warn('[ObjectDetection.refreshDeviceContext] stale probe ignored: device identity changed during refresh');
            return null;
        }
        if (identityGuard?.validateResponseForDevice && identityToken) {
            const identityCheck = identityGuard.validateResponseForDevice(device, result || {}, identityToken, {
                host: probeHost,
                deviceId
            });
            if (!identityCheck.ok) {
                console.warn('[ObjectDetection.refreshDeviceContext] probe identity mismatch ignored:', identityCheck.reason);
                return null;
            }
        }
        if (!result || !result.cluster) return result;
        const cluster = result.cluster || {};
        device.sshConfig = device.sshConfig || {};
        // Only stamp non-VIP, non-empty values -- mirrors the
        // sticky-host guard already in `_resolveActiveNccHost`. Never
        // poison the per-node fields with a cluster VIP.
        const knownVip = (device.sshConfig.host || '').trim();
        if (cluster.active_ncc_host && cluster.active_ncc_host !== knownVip) {
            device.sshConfig._activeNccHost = cluster.active_ncc_host;
        }
        if (cluster.active_ncc_ip && cluster.active_ncc_ip !== knownVip) {
            device.sshConfig._activeNccIp = cluster.active_ncc_ip;
        }
        if (cluster.active_ncc_vm) device.sshConfig._activeNccVm = cluster.active_ncc_vm;
        if (cluster.kvm_host) device.sshConfig._kvmHost = cluster.kvm_host;
        if (Array.isArray(cluster.ncc_vms) && cluster.ncc_vms.length) {
            device.sshConfig._nccVms = cluster.ncc_vms;
        }
        try {
            const editor = (window.editor || (window.app && window.app.editor) || null);
            if (editor && typeof editor.draw === 'function') editor.draw();
        } catch (_) { /* non-fatal */ }
        return result;
    },

    // Per-device fast-initial timer registry. Keyed by deviceId so
    // re-arming on a second Save replaces the in-flight schedule
    // rather than stacking probes.
    _fastInitialTimers: Object.create(null),

    /**
     * Schedule a "fast-initial then slow" monitor sweep for a device:
     *
     *     +30s   -> probe + draw
     *     +60s   -> probe + draw
     *     +90s   -> probe + draw
     *     <after> the standard 5-min DeviceMonitor takes over.
     *
     * This is fired from the SSH dialog right after a successful credential
     * verification, so cluster details (active NCC, KVM host, image
     * versions) repopulate quickly during the post-verify window when
     * an NCC fail-over or upgrade-driven address shuffle is most likely.
     *
     * Idempotent: calling again for the same deviceId cancels the
     * previous schedule. Auto-clears after the last probe runs so we
     * don't leak timers.
     */
    startFastInitialMonitor(device, opts = {}) {
        if (!device) return;
        const deviceId = device.label || device.id || '';
        if (!deviceId) return;
        const probesAt = Array.isArray(opts.probesAt) && opts.probesAt.length
            ? opts.probesAt : [30000, 60000, 90000];
        // Cancel any prior schedule.
        const prior = this._fastInitialTimers[deviceId];
        if (prior && Array.isArray(prior)) {
            prior.forEach((t) => { try { clearTimeout(t); } catch (_) {} });
        }
        const handles = probesAt.map((delay) => setTimeout(() => {
            try { this.refreshDeviceContext(device, { force: true }); } catch (_) {}
        }, delay));
        this._fastInitialTimers[deviceId] = handles;
        // Auto-clear after the longest delay finishes (+ small buffer).
        const maxDelay = Math.max.apply(null, probesAt);
        setTimeout(() => {
            if (this._fastInitialTimers[deviceId] === handles) {
                delete this._fastInitialTimers[deviceId];
            }
        }, maxDelay + 5000);
    },

};

console.log('[topology-object-detection.js] ObjectDetection loaded');
