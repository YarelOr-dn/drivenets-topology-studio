/**
 * topology-link-geometry.js - Link Geometry, Hit Detection and BUL Chain Analysis
 * 
 * Extracted from topology.js for modular architecture.
 * All methods receive 'editor' as first parameter instead of using 'this'.
 */

'use strict';

window.LinkGeometry = {
    _checkLinkHit(editor, x, y, obj) {
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
        
        const baseScreenTolerance = 5; // Base tolerance in screen pixels
        const zoomFactor = Math.max(0.5, Math.min(2.0, editor.zoom)); // Clamp zoom factor
        
        // Adaptive tolerance: smaller when zoomed in (precise), larger when zoomed out (forgiving)
        const adaptiveScreenTolerance = editor.zoom > 1.0 
            ? baseScreenTolerance / Math.sqrt(zoomFactor)  // Tighter when zoomed in
            : baseScreenTolerance * Math.sqrt(1 / zoomFactor); // More forgiving when zoomed out
        
        const worldTolerance = adaptiveScreenTolerance / editor.zoom;
        
        // Maximum distance = half the visual width + adaptive world tolerance
        const maxDistance = (linkWidth / 2) + worldTolerance;
        
        // ADDITIONAL: For curved links, we need a slightly larger detection area
        const hasCurve = !!(obj._cp1 && obj._cp2) || !!obj.manualCurvePoint;
        const curveBonus = hasCurve ? (3 / editor.zoom) : 0;
                        
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
        if (obj._cp1 && obj._cp2) {
            // Use stored control points for accurate curved hitbox
            minDistToLink = editor.distanceToCurvedLineWithControlPoints(
                x, y, 
                { x: startX, y: startY }, 
                { x: endX, y: endY }, 
                obj._cp1, obj._cp2
            );
        } else if (obj.manualCurvePoint) {
            // Manual curve mode but control points not stored yet
            const midX = (startX + endX) / 2;
            const midY = (startY + endY) / 2;
            const offsetX = obj.manualCurvePoint.x - midX;
            const offsetY = obj.manualCurvePoint.y - midY;
            const cp1 = { x: startX + offsetX * 1.33, y: startY + offsetY * 1.33 };
            const cp2 = { x: endX + offsetX * 1.33, y: endY + offsetY * 1.33 };
            minDistToLink = editor.distanceToCurvedLineWithControlPoints(
                x, y, 
                { x: startX, y: startY }, 
                { x: endX, y: endY }, 
                cp1, cp2
            );
        } else if (obj.device1 && obj.device2) {
            // Device-to-device link - use full curve calculation
            const d1 = editor.objects.find(o => o.id === obj.device1);
            const d2 = editor.objects.find(o => o.id === obj.device2);
            if (d1 && d2) {
                minDistToLink = editor.distanceToCurvedLine(x, y, obj, d1, d2);
            }
        } else {
            // Straight line fallback
            minDistToLink = editor.distanceToLine(x, y, { x: startX, y: startY }, { x: endX, y: endY });
        }
        
        // Check arrow tip hitbox for arrow-style links using pixel-accurate triangle collision
        const linkStyle = obj.style || 'solid';
        const isArrowStyle = linkStyle.includes('arrow');
        if (isArrowStyle) {
            const arrowLength = obj._arrowLength || (10 + (linkWidth * 3));
            const arrowAngleSpread = obj._arrowAngleSpread || (Math.PI / 5);
            
            const arrowTipEndX = obj._arrowTipEnd ? obj._arrowTipEnd.x : endX;
            const arrowTipEndY = obj._arrowTipEnd ? obj._arrowTipEnd.y : endY;
            const arrowTipStartX = obj._arrowTipStart ? obj._arrowTipStart.x : startX;
            const arrowTipStartY = obj._arrowTipStart ? obj._arrowTipStart.y : startY;
            
            const hasTriangleData = window.MathUtils && window.MathUtils.isPointInTriangle;
            
            // Check END arrow tip with triangle collision
            if (obj._arrowEndAngle !== undefined && hasTriangleData) {
                const angle = obj._arrowEndAngle;
                // END arrow uses MINUS (triangle extends backward from tip)
                const leftX = arrowTipEndX - arrowLength * Math.cos(angle - arrowAngleSpread);
                const leftY = arrowTipEndY - arrowLength * Math.sin(angle - arrowAngleSpread);
                const rightX = arrowTipEndX - arrowLength * Math.cos(angle + arrowAngleSpread);
                const rightY = arrowTipEndY - arrowLength * Math.sin(angle + arrowAngleSpread);
                
                if (window.MathUtils.isPointInTriangle(x, y, arrowTipEndX, arrowTipEndY, leftX, leftY, rightX, rightY)) {
                    minDistToLink = 0; // Direct hit on arrow triangle
                }
            } else {
                const distToEndTip = Math.hypot(x - arrowTipEndX, y - arrowTipEndY);
                if (distToEndTip < (arrowLength * 0.6) / editor.zoom) {
                    minDistToLink = Math.min(minDistToLink, distToEndTip * 0.5);
                }
            }
            
            // Check START arrow tip for double-arrow
            if (linkStyle.includes('double')) {
                if (obj._arrowStartAngle !== undefined && hasTriangleData) {
                    const angle = obj._arrowStartAngle;
                    const leftX = arrowTipStartX + arrowLength * Math.cos(angle - arrowAngleSpread);
                    const leftY = arrowTipStartY + arrowLength * Math.sin(angle - arrowAngleSpread);
                    const rightX = arrowTipStartX + arrowLength * Math.cos(angle + arrowAngleSpread);
                    const rightY = arrowTipStartY + arrowLength * Math.sin(angle + arrowAngleSpread);
                    
                    if (window.MathUtils.isPointInTriangle(x, y, arrowTipStartX, arrowTipStartY, leftX, leftY, rightX, rightY)) {
                        minDistToLink = 0;
                    }
                } else {
                    const distToStartTip = Math.hypot(x - arrowTipStartX, y - arrowTipStartY);
                    if (distToStartTip < (arrowLength * 0.6) / editor.zoom) {
                        minDistToLink = Math.min(minDistToLink, distToStartTip * 0.5);
                    }
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
        
        // CRITICAL FIX: Tighten hitbox near endpoints so it doesn't extend beyond the visual TP circle.
        // distanceToLine clamps to the segment, so clicking PAST an endpoint returns the distance TO
        // that endpoint. This makes the link body hitbox act as a large circle around each TP.
        // We reduce the effective tolerance when the closest point is actually an endpoint
        // (i.e., the click is in the "endcap" zone beyond the line body).
        if (minDistToLink <= effectiveMaxDistance && obj.start && obj.end) {
            // Check if click projects outside the segment (endcap zone)
            const sx = obj.start.x, sy = obj.start.y;
            const ex = obj.end.x, ey = obj.end.y;
            const dx = ex - sx, dy = ey - sy;
            const lenSq = dx * dx + dy * dy;
            if (lenSq > 0) {
                const t = ((x - sx) * dx + (y - sy) * dy) / lenSq;
                if (t < 0 || t > 1) {
                    // Click projects beyond the segment ends - use tight TP-sized tolerance
                    const endcapTolerance = 5 / editor.zoom;
                    if (minDistToLink > endcapTolerance) {
                        return -1; // Beyond visual TP, don't count as link hit
                    }
                }
            }
        }
        
        // Return the actual distance if within range, or -1 if not
        if (minDistToLink <= effectiveMaxDistance) {
            return minDistToLink;
        }
        return -1;
    },

    distanceToLine(editor, px, py, lineStart, lineEnd) {
        if (window.MathUtils) {
            return window.MathUtils.distanceToLine(px, py, lineStart, lineEnd);
        }
        // Fallback implementation
        const A = px - lineStart.x;
        const B = py - lineStart.y;
        const C = lineEnd.x - lineStart.x;
        const D = lineEnd.y - lineStart.y;
        const dot = A * C + B * D;
        const lenSq = C * C + D * D;
        let param = lenSq !== 0 ? dot / lenSq : -1;
        let xx = param < 0 ? lineStart.x : (param > 1 ? lineEnd.x : lineStart.x + param * C);
        let yy = param < 0 ? lineStart.y : (param > 1 ? lineEnd.y : lineStart.y + param * D);
        return Math.hypot(px - xx, py - yy);
    },

    linksAlreadyShareMP(editor, link1, link2) {
        if (window.BulUtils) {
            return window.BulUtils.linksAlreadyShareMP(editor, link1, link2);
        }
        // Fallback - check direct relationships
        if (link1.mergedWith?.linkId === link2.id || link2.mergedWith?.linkId === link1.id) return true;
        if (link1.mergedInto?.parentId === link2.id || link2.mergedInto?.parentId === link1.id) return true;
        return false;
    },

    analyzeBULChain(editor, link) {
        const allLinks = editor.getAllMergedLinks(link);
        let tpCount = 0;
        let mpCount = 0;
        
        // Count MPs (merge points) - each mergedWith relationship creates one MP
        allLinks.forEach(chainLink => {
            if (chainLink.mergedWith) {
                mpCount++;
            }
        });
        
        // FIXED: Count actual free TPs by checking BOTH mergedWith AND mergedInto
        // An endpoint is a TP if it's NOT connected to another link
        allLinks.forEach(chainLink => {
            // Check start endpoint
            let startIsConnected = false;
            
            // Check if THIS link's start is the connection point (via mergedWith)
            if (chainLink.mergedWith) {
                // parentFreeEnd tells us which end is FREE, so the OTHER end is connected
                if (chainLink.mergedWith.parentFreeEnd === 'end') {
                    startIsConnected = true; // Start is the MP (connected to child)
                }
            }
            // Check if THIS link's start is connected via mergedInto (this link is a child)
            if (chainLink.mergedInto) {
                const parentLink = editor.objects.find(o => o.id === chainLink.mergedInto.parentId);
                if (parentLink && parentLink.mergedWith) {
                    // childFreeEnd tells us which end of the CHILD is free
                    if (parentLink.mergedWith.childFreeEnd === 'end') {
                        startIsConnected = true; // Start is connected to parent
                    }
                }
            }
            if (!startIsConnected) tpCount++;
            
            // Check end endpoint
            let endIsConnected = false;
            
            // Check if THIS link's end is the connection point (via mergedWith)
            if (chainLink.mergedWith) {
                // parentFreeEnd tells us which end is FREE, so the OTHER end is connected
                if (chainLink.mergedWith.parentFreeEnd === 'start') {
                    endIsConnected = true; // End is the MP (connected to child)
                }
            }
            // Check if THIS link's end is connected via mergedInto (this link is a child)
            if (chainLink.mergedInto) {
                const parentLink = editor.objects.find(o => o.id === chainLink.mergedInto.parentId);
                if (parentLink && parentLink.mergedWith) {
                    // childFreeEnd tells us which end of the CHILD is free
                    if (parentLink.mergedWith.childFreeEnd === 'start') {
                        endIsConnected = true; // End is connected to parent
                    }
                }
            }
            if (!endIsConnected) tpCount++;
        });
        
        return {
            linkCount: allLinks.length,
            tpCount,
            mpCount,
            links: allLinks,
            isValid: (tpCount === 2 && mpCount === allLinks.length - 1) // Valid: 2 TPs, N-1 MPs for N links
        };
    },

    handleULDeletionInBUL(editor, deletedLink) {
        // When a UL in a BUL chain is deleted, we need to:
        // 1. Disconnect it from parent and child
        // 2. Optionally reconnect parent and child directly (if both exist)
        // 3. Clean up merge metadata
        
        const parentLink = deletedLink.mergedInto ? editor.objects.find(o => o.id === deletedLink.mergedInto.parentId) : null;
        const childLink = deletedLink.mergedWith ? editor.objects.find(o => o.id === deletedLink.mergedWith.linkId) : null;
        
        if (editor.debugger) {
            editor.debugger.logInfo(`🔗 Removing UL from BUL chain: ${deletedLink.id}`);
            if (parentLink) editor.debugger.logInfo(`   Parent: ${parentLink.id}`);
            if (childLink) editor.debugger.logInfo(`   Child: ${childLink.id}`);
        }
        
        // Case 1: Link has both parent and child (middle of chain)
        if (parentLink && childLink) {
            // Remove child's connection to deleted link
            if (childLink.mergedInto && childLink.mergedInto.parentId === deletedLink.id) {
                delete childLink.mergedInto;
            }
            
            // Remove parent's connection to deleted link
            if (parentLink.mergedWith && parentLink.mergedWith.linkId === deletedLink.id) {
                delete parentLink.mergedWith;
            }
            
            // Note: We don't auto-reconnect parent to child because they may be too far apart
            // The user can manually reconnect if desired
            if (editor.debugger) {
                editor.debugger.logInfo(`   ✂️ Chain split: ${parentLink.id} and ${childLink.id} are now separate`);
            }
        }
        // Case 2: Link has only parent (end of chain)
        else if (parentLink && !childLink) {
            // Remove parent's connection to deleted link
            if (parentLink.mergedWith && parentLink.mergedWith.linkId === deletedLink.id) {
                delete parentLink.mergedWith;
                if (editor.debugger) {
                    editor.debugger.logInfo(`   ✂️ ${parentLink.id} is now free at its former connection point`);
                }
            }
        }
        // Case 3: Link has only child (start of chain)
        else if (childLink && !parentLink) {
            // Remove child's connection to deleted link
            if (childLink.mergedInto && childLink.mergedInto.parentId === deletedLink.id) {
                delete childLink.mergedInto;
                if (editor.debugger) {
                    editor.debugger.logInfo(`   ✂️ ${childLink.id} is now free at its former connection point`);
                }
            }
        }
    },

    distanceToCurvedLine(editor, px, py, link, device1, device2) {
        // Check distance to line (curved or straight based on curve mode)
        if (!device1 || !device2) return Infinity;
        
        // CRITICAL: For manual curve mode, use stored control points for accurate hitbox
        // This ensures the hitbox matches the visual curve exactly
        if (link._cp1 && link._cp2 && link.start && link.end) {
            return editor.distanceToCurvedLineWithControlPoints(px, py, link.start, link.end, link._cp1, link._cp2);
        }
        
        // Determine if curve mode is enabled for this link
        // Magnetic field must be > 0 for curves to work
        const curveEnabled = (link.curveOverride !== undefined ? link.curveOverride : editor.linkCurveMode) && editor.magneticFieldStrength > 0;
        
        const linkIndex = link.linkIndex || 0;
        const angle = Math.atan2(device2.y - device1.y, device2.x - device1.x);
        
        // NORMALIZE perpendicular direction for true bidirectional behavior (same as drawLink)
        const sortedIds = [link.device1, link.device2].sort();
        const isNormalDirection = link.device1 === sortedIds[0];
        
        // Calculate offset (same as in drawLink)
        // User requested logic: First (0) = Middle, Second (1) = Right (+), Third (2) = Left (-)
        let offsetAmount = 0;
        let direction = 0;
        if (linkIndex > 0) {
            const magnitude = Math.ceil(linkIndex / 2) * 20;
            direction = (linkIndex % 2 === 1) ? 1 : -1; // Odd = Right (+), Even = Left (-)
            offsetAmount = magnitude * direction;
        }
        
        // Calculate perpendicular offset with normalized direction
        let perpAngle = angle + Math.PI / 2;
        if (!isNormalDirection) {
            perpAngle += Math.PI; // Flip 180 degrees for consistent sides
        }
        
        // CRITICAL: Use link's ACTUAL drawn positions for exact hitbox match
        // These positions are already calculated correctly by the draw loop
        let offsetStartX, offsetStartY, offsetEndX, offsetEndY;
        
        if (link.start && link.end) {
            // Use the link's actual rendered positions
            offsetStartX = link.start.x;
            offsetStartY = link.start.y;
            offsetEndX = link.end.x;
            offsetEndY = link.end.y;
        } else {
            // Fallback: calculate from device positions (shape-aware)
        const offsetX = Math.cos(perpAngle) * offsetAmount;
        const offsetY = Math.sin(perpAngle) * offsetAmount;
        
        const startPt = editor.getLinkConnectionPoint(device1, angle);
        const endPt = editor.getLinkConnectionPoint(device2, angle + Math.PI);
        
            offsetStartX = startPt.x + offsetX;
            offsetStartY = startPt.y + offsetY;
            offsetEndX = endPt.x + offsetX;
            offsetEndY = endPt.y + offsetY;
        }
        
        if (!curveEnabled) {
            // Curve mode disabled - calculate distance to straight line
            return editor.distanceToLine(px, py, 
                { x: offsetStartX, y: offsetStartY }, 
                { x: offsetEndX, y: offsetEndY }
            );
        }
        
        // Curve mode enabled - check for obstacles and calculate distance to curved line
        const obstacles = editor.findAllObstaclesOnPath(offsetStartX, offsetStartY, offsetEndX, offsetEndY, link);
        
        let minDist = Infinity;
        // ULTIMATE PRECISION: Maximum samples for pixel-perfect hitbox accuracy
        const samples = 100; // High precision for exact curve matching
        let cp1x, cp1y, cp2x, cp2y;
        
        if (obstacles.length > 0) {
            // Gentle magnetic repulsion (same algorithm as drawLink for consistency)
            const straightMidX = (offsetStartX + offsetEndX) / 2;
            const straightMidY = (offsetStartY + offsetEndY) / 2;
            const linkLength = Math.sqrt(Math.pow(offsetEndX - offsetStartX, 2) + Math.pow(offsetEndY - offsetStartY, 2));
            
            let totalRepulsionX = 0;
            let totalRepulsionY = 0;
            let closestObstacleRadius = 0;
            
            // Use per-link curve magnitude if set, otherwise use global
            const effectiveMagnitude = link.curveMagnitude !== undefined ? link.curveMagnitude : editor.magneticFieldStrength;
            
            obstacles.forEach((obstacleInfo) => {
                const obstacle = obstacleInfo.device;
                const dx = straightMidX - obstacle.x;
                const dy = straightMidY - obstacle.y;
                const distToMid = Math.sqrt(dx * dx + dy * dy) || 1;
                const minClearance = obstacle.radius + 18;
                const repelDirX = dx / distToMid;
                const repelDirY = dy / distToMid;
                const k = minClearance * minClearance * effectiveMagnitude * 2; // Increased strength
                const repulsionStrength = k / Math.pow(distToMid, 0.8); // Stronger magnetic repulsion falloff
                totalRepulsionX += repelDirX * repulsionStrength;
                totalRepulsionY += repelDirY * repulsionStrength;
                closestObstacleRadius = Math.max(closestObstacleRadius, obstacle.radius);
            });
            
            const deflectionMag = Math.sqrt(totalRepulsionX * totalRepulsionX + totalRepulsionY * totalRepulsionY);
            const maxDeflection = Math.min(linkLength * 0.45, closestObstacleRadius * 2.5); // Match drawing
            const actualDeflection = Math.min(deflectionMag, maxDeflection);
            const normalizedRepulX = totalRepulsionX / (deflectionMag || 1);
            const normalizedRepulY = totalRepulsionY / (deflectionMag || 1);
            const deflectedMidX = straightMidX + normalizedRepulX * actualDeflection;
            const deflectedMidY = straightMidY + normalizedRepulY * actualDeflection;
            
            // Curvier control points (same as drawing)
            const controlWeight = 0.7; // Match drawing for consistency
            const midWeight = 1 - controlWeight;
            cp1x = offsetStartX * midWeight + deflectedMidX * controlWeight;
            cp1y = offsetStartY * midWeight + deflectedMidY * controlWeight;
            cp2x = offsetEndX * midWeight + deflectedMidX * controlWeight;
            cp2y = offsetEndY * midWeight + deflectedMidY * controlWeight;
        } else {
            // No obstacles - simple curve for multi-link separation
            const curveOffset = linkIndex > 0 ? Math.ceil(linkIndex / 2) * 10 * direction : 0;
            cp1x = offsetStartX + Math.cos(perpAngle) * curveOffset;
            cp1y = offsetStartY + Math.sin(perpAngle) * curveOffset;
            cp2x = offsetEndX + Math.cos(perpAngle) * curveOffset;
            cp2y = offsetEndY + Math.sin(perpAngle) * curveOffset;
        }
        
        // CRITICAL: Use stored control points from drawing if available for exact hitbox match
        // This ensures the hitbox matches the ACTUAL drawn curve, not a recalculated approximation
        if (link._cp1 && link._cp2) {
            cp1x = link._cp1.x;
            cp1y = link._cp1.y;
            cp2x = link._cp2.x;
            cp2y = link._cp2.y;
        }
        
        // Sample points along Bezier curve
        for (let i = 0; i <= samples; i++) {
            const t = i / samples;
            const curveX = Math.pow(1-t, 3) * offsetStartX + 3 * Math.pow(1-t, 2) * t * cp1x + 3 * (1-t) * Math.pow(t, 2) * cp2x + Math.pow(t, 3) * offsetEndX;
            const curveY = Math.pow(1-t, 3) * offsetStartY + 3 * Math.pow(1-t, 2) * t * cp1y + 3 * (1-t) * Math.pow(t, 2) * cp2y + Math.pow(t, 3) * offsetEndY;
            
            const dist = Math.sqrt(Math.pow(px - curveX, 2) + Math.pow(py - curveY, 2));
            if (dist < minDist) minDist = dist;
        }
        
        return minDist;
    }
};

console.log('[topology-link-geometry.js] LinkGeometry loaded');
