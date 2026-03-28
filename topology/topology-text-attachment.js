/**
 * topology-text-attachment.js - Text-to-Link Attachment and Positioning
 * 
 * Extracted from topology.js for modular architecture.
 * All methods receive 'editor' as first parameter instead of using 'this'.
 */

'use strict';

window.TextAttachment = {
    findNearestLinkToPoint(editor, x, y, maxDistance = 50) {
        let nearestLink = null;
        let nearestDistance = maxDistance;
        let nearestT = 0.5; // Parametric position on link (0=start, 0.5=middle, 1=end)
        let nearestPoint = null;
        
        const links = editor.objects.filter(obj => obj.type === 'link' || obj.type === 'unbound');
        
        for (const link of links) {
            // Get link start and end positions
            let linkStart = link.start ? { ...link.start } : null;
            let linkEnd = link.end ? { ...link.end } : null;
            
            // For device-connected links, calculate actual positions
            if (link.device1) {
                const device1 = editor.objects.find(o => o.id === link.device1);
                if (device1) {
                    // Calculate angle to other endpoint
                    const targetX = link.device2 ? 
                        (editor.objects.find(o => o.id === link.device2)?.x || (linkEnd ? linkEnd.x : device1.x)) :
                        (linkEnd ? linkEnd.x : device1.x);
                    const targetY = link.device2 ? 
                        (editor.objects.find(o => o.id === link.device2)?.y || (linkEnd ? linkEnd.y : device1.y)) :
                        (linkEnd ? linkEnd.y : device1.y);
                    const angle = Math.atan2(targetY - device1.y, targetX - device1.x);
                    linkStart = {
                        x: device1.x + Math.cos(angle) * device1.radius,
                        y: device1.y + Math.sin(angle) * device1.radius
                    };
                }
            }
            
            if (link.device2) {
                const device2 = editor.objects.find(o => o.id === link.device2);
                if (device2) {
                    // Calculate angle to other endpoint
                    const targetX = link.device1 ? 
                        (editor.objects.find(o => o.id === link.device1)?.x || (linkStart ? linkStart.x : device2.x)) :
                        (linkStart ? linkStart.x : device2.x);
                    const targetY = link.device1 ? 
                        (editor.objects.find(o => o.id === link.device1)?.y || (linkStart ? linkStart.y : device2.y)) :
                        (linkStart ? linkStart.y : device2.y);
                    const angle = Math.atan2(targetY - device2.y, targetX - device2.x);
                    linkEnd = {
                        x: device2.x + Math.cos(angle) * device2.radius,
                        y: device2.y + Math.sin(angle) * device2.radius
                    };
                }
            }
            
            if (!linkStart || !linkEnd) continue;
            
            // Check if this link is curved
            const isCurved = (link.curveOverride !== undefined ? link.curveOverride : editor.linkCurveMode) && 
                             editor.magneticFieldStrength > 0;
            
            let result;
            
            if (isCurved) {
                // For curved links, sample points along the bezier curve
                result = editor.getClosestPointOnCurvedLink(x, y, link, linkStart, linkEnd);
            } else {
                // For straight links, use line segment calculation
                result = editor.getClosestPointOnLineSegment(x, y, linkStart.x, linkStart.y, linkEnd.x, linkEnd.y);
            }
            
            // Use actual visual path distance - no bias, just pick the closest visual path
            if (result.distance < nearestDistance) {
                nearestDistance = result.distance;
                nearestLink = link;
                nearestT = result.t;
                nearestPoint = result.point;
            }
        }
        
        if (!nearestLink) return null;

        // Check if another text box is already attached at this location
        const tSnap = nearestT;
        const occupied = editor.objects.some(obj => {
            if (obj.type !== 'text' || obj.linkId !== nearestLink.id) return false;
            const existingT = obj.linkAttachT !== undefined ? obj.linkAttachT : 0.5;
            return Math.abs(existingT - tSnap) < 0.08;
        });
        if (occupied) return null;

        return {
            link: nearestLink,
            distance: nearestDistance,
            t: nearestT,
            point: nearestPoint,
            position: editor.getAttachmentPositionFromT(nearestT)
        };
    },

    getClosestPointOnCurvedLink(editor, px, py, link, linkStart, linkEnd) {
        const midX = (linkStart.x + linkEnd.x) / 2;
        const midY = (linkStart.y + linkEnd.y) / 2;
        
        const dx = linkEnd.x - linkStart.x;
        const dy = linkEnd.y - linkStart.y;
        const linkLength = Math.sqrt(dx * dx + dy * dy);
        
        // CRITICAL FIX: Use stored control points if available (set during draw), 
        // otherwise calculate using the SAME magnetic deflection algorithm as drawLink/drawUnboundLink
        let cp1x, cp1y, cp2x, cp2y;
        let useCubicBezier = false;
        
        if (link._cp1 && link._cp2 && link._cp1.x !== undefined && link._cp2.x !== undefined) {
            // Use stored control points from last draw (most accurate)
            cp1x = link._cp1.x;
            cp1y = link._cp1.y;
            cp2x = link._cp2.x;
            cp2y = link._cp2.y;
            useCubicBezier = true;
        } else {
            // Calculate control points using magnetic field deflection (same as drawing code)
            const obstacles = editor.findAllObstaclesOnPath(linkStart.x, linkStart.y, linkEnd.x, linkEnd.y, link);
            
            if (obstacles.length > 0) {
                // Magnetic deflection calculation (matches drawLink/drawUnboundLink)
                let totalRepulsionX = 0;
                let totalRepulsionY = 0;
                let closestObstacleRadius = 0;
                
                const effectiveMagnitude = link.curveMagnitude !== undefined ? link.curveMagnitude : editor.magneticFieldStrength;
                
                obstacles.forEach((obstacleInfo) => {
                    const obstacle = obstacleInfo.device;
                    const odx = midX - obstacle.x;
                    const ody = midY - obstacle.y;
                    const distToMid = Math.sqrt(odx * odx + ody * ody) || 1;
                    const minClearance = obstacle.radius + 18;
                    const repelDirX = odx / distToMid;
                    const repelDirY = ody / distToMid;
                    const k = minClearance * minClearance * effectiveMagnitude * 2;
                    const repulsionStrength = k / Math.pow(distToMid, 0.8);
                    totalRepulsionX += repelDirX * repulsionStrength;
                    totalRepulsionY += repelDirY * repulsionStrength;
                    closestObstacleRadius = Math.max(closestObstacleRadius, obstacle.radius);
                });
                
                const deflectionMag = Math.sqrt(totalRepulsionX * totalRepulsionX + totalRepulsionY * totalRepulsionY);
                const maxDeflection = Math.min(linkLength * 0.45, closestObstacleRadius * 2.5);
                const actualDeflection = Math.min(deflectionMag, maxDeflection);
                const normalizedRepulX = totalRepulsionX / (deflectionMag || 1);
                const normalizedRepulY = totalRepulsionY / (deflectionMag || 1);
                const deflectedMidX = midX + normalizedRepulX * actualDeflection;
                const deflectedMidY = midY + normalizedRepulY * actualDeflection;
                
                // Calculate control points (same as drawing code)
                const controlWeight = 0.7;
                const midWeight = 1 - controlWeight;
                cp1x = linkStart.x * midWeight + deflectedMidX * controlWeight;
                cp1y = linkStart.y * midWeight + deflectedMidY * controlWeight;
                cp2x = linkEnd.x * midWeight + deflectedMidX * controlWeight;
                cp2y = linkEnd.y * midWeight + deflectedMidY * controlWeight;
                useCubicBezier = true;
            } else {
                // No obstacles - fall back to simple perpendicular offset
                const curveMagnitude = link.curveMagnitude !== undefined ? link.curveMagnitude : editor.magneticFieldStrength;
                const curveOffset = curveMagnitude * 0.5;
                const perpX = -dy / (linkLength || 1);
                const perpY = dx / (linkLength || 1);
                cp1x = midX + perpX * curveOffset;
                cp1y = midY + perpY * curveOffset;
                // For quadratic bezier, cp2 is same as cp1
                cp2x = cp1x;
                cp2y = cp1y;
                useCubicBezier = false;
            }
        }
        
        // Sample points along the bezier curve
        let closestDistance = Infinity;
        let closestT = 0.5;
        let closestPoint = { x: midX, y: midY };
        
        const samples = 30; // Increased for better accuracy
        for (let i = 0; i <= samples; i++) {
            const t = i / samples;
            let bx, by;
            
            if (useCubicBezier) {
                // Cubic bezier: B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3
                const t2 = t * t;
                const t3 = t2 * t;
                const mt = 1 - t;
                const mt2 = mt * mt;
                const mt3 = mt2 * mt;
                bx = mt3 * linkStart.x + 3 * mt2 * t * cp1x + 3 * mt * t2 * cp2x + t3 * linkEnd.x;
                by = mt3 * linkStart.y + 3 * mt2 * t * cp1y + 3 * mt * t2 * cp2y + t3 * linkEnd.y;
            } else {
                // Quadratic bezier: B(t) = (1-t)²P0 + 2(1-t)tP1 + t²P2
                const oneMinusT = 1 - t;
                bx = oneMinusT * oneMinusT * linkStart.x + 
                     2 * oneMinusT * t * cp1x + 
                     t * t * linkEnd.x;
                by = oneMinusT * oneMinusT * linkStart.y + 
                     2 * oneMinusT * t * cp1y + 
                     t * t * linkEnd.y;
            }
            
            const dist = Math.sqrt((px - bx) * (px - bx) + (py - by) * (py - by));
            
            if (dist < closestDistance) {
                closestDistance = dist;
                closestT = t;
                closestPoint = { x: bx, y: by };
            }
        }
        
        return {
            point: closestPoint,
            t: closestT,
            distance: closestDistance
        };
    },

    addAdjacentText(editor, link, position = 'middle', textContent = 'Label') {
        editor.saveState(); // Save before adding text
        const device1 = link.device1 ? editor.objects.find(obj => obj.id === link.device1) : null;
        const device2 = link.device2 ? editor.objects.find(obj => obj.id === link.device2) : null;
        
        // Calculate link angle
        const angle = Math.atan2(link.end.y - link.start.y, link.end.x - link.start.x);
        
        // NORMALIZE perpendicular direction (match drawLink and updateAdjacentTextPosition)
        const sortedIds = [link.device1, link.device2].sort();
        const isNormalDirection = link.device1 === sortedIds[0];
        
        // Calculate link offset based on linkIndex (to match the actual link position)
        // User requested logic: First (0) = Middle, Second (1) = Right (+), Third (2) = Left (-)
        const linkIndex = link.linkIndex || 0;
        let linkOffsetAmount = 0;
        let linkDirection = 0;
        if (linkIndex > 0) {
            const magnitude = Math.ceil(linkIndex / 2) * 20;
            linkDirection = (linkIndex % 2 === 1) ? 1 : -1; // Odd = Right (+), Even = Left (-)
            linkOffsetAmount = magnitude * linkDirection;
        }
        
        // Calculate perpendicular with normalized direction
        let perpAngle = angle + Math.PI / 2;
        if (!isNormalDirection) {
            perpAngle += Math.PI; // Flip to match drawLink
        }
        
        // Base offset for text from link (perpendicular distance)
        const baseTextOffset = 12;
        
        // Auto-determine side based on link offset direction
        // If link is offset upward (direction = 1), place text above
        // If link is offset downward (direction = -1), place text below
        // If link is centered (direction = 0), place text above by default
        const autoSide = linkDirection >= 0 ? -1 : 1;
        
        // Determine position based on selection
        let textX, textY;
        
        // Handle legacy positions with explicit top/bottom
        if (position === 'device1-top' || position === 'device1-bottom') {
            const side = position.includes('top') ? -1 : 1;
            const posAlongLink = 0.15;
            const alongX = link.start.x + (link.end.x - link.start.x) * posAlongLink;
            const alongY = link.start.y + (link.end.y - link.start.y) * posAlongLink;
            const totalOffset = linkOffsetAmount + (baseTextOffset * side);
            textX = alongX + Math.cos(perpAngle) * totalOffset;
            textY = alongY + Math.sin(perpAngle) * totalOffset;
        } else if (position === 'device2-top' || position === 'device2-bottom') {
            const side = position.includes('top') ? -1 : 1;
            const posAlongLink = 0.85;
            const alongX = link.start.x + (link.end.x - link.start.x) * posAlongLink;
            const alongY = link.start.y + (link.end.y - link.start.y) * posAlongLink;
            const totalOffset = linkOffsetAmount + (baseTextOffset * side);
            textX = alongX + Math.cos(perpAngle) * totalOffset;
            textY = alongY + Math.sin(perpAngle) * totalOffset;
        } else if (position === 'device1') {
            // Simplified position - auto-determine side
            const posAlongLink = 0.15;
            const alongX = link.start.x + (link.end.x - link.start.x) * posAlongLink;
            const alongY = link.start.y + (link.end.y - link.start.y) * posAlongLink;
            const totalOffset = linkOffsetAmount + (baseTextOffset * autoSide);
            textX = alongX + Math.cos(perpAngle) * totalOffset;
            textY = alongY + Math.sin(perpAngle) * totalOffset;
        } else if (position === 'device2') {
            // Simplified position - auto-determine side
            const posAlongLink = 0.85;
            const alongX = link.start.x + (link.end.x - link.start.x) * posAlongLink;
            const alongY = link.start.y + (link.end.y - link.start.y) * posAlongLink;
            const totalOffset = linkOffsetAmount + (baseTextOffset * autoSide);
            textX = alongX + Math.cos(perpAngle) * totalOffset;
            textY = alongY + Math.sin(perpAngle) * totalOffset;
        } else {
            // Middle (default for unbound links)
            const midX = (link.start.x + link.end.x) / 2;
            const midY = (link.start.y + link.end.y) / 2;
            const totalOffset = linkOffsetAmount + (baseTextOffset * autoSide);
            textX = midX + Math.cos(perpAngle) * totalOffset;
            textY = midY + Math.sin(perpAngle) * totalOffset;
        }
        
        // Calculate link length for text size
        const linkLength = Math.sqrt(Math.pow(link.end.x - link.start.x, 2) + Math.pow(link.end.y - link.start.y, 2));
        // Smaller text size - about 1/5 of link length or smaller
        const textSize = Math.max(8, Math.min(16, linkLength / 5));
        
        // Calculate rotation with flip for upside-down text
        let rotationDegrees = angle * 180 / Math.PI;
        while (rotationDegrees > 180) rotationDegrees -= 360;
        while (rotationDegrees < -180) rotationDegrees += 360;
        if (rotationDegrees > 90 || rotationDegrees < -90) {
            rotationDegrees += 180;
            while (rotationDegrees > 180) rotationDegrees -= 360;
            while (rotationDegrees < -180) rotationDegrees += 360;
        }
        
        const text = {
            id: `text_${editor.textIdCounter++}`,
            type: 'text',
            x: textX,
            y: textY,
            text: textContent,
            fontSize: Math.round(textSize),
            color: '#333',
            rotation: rotationDegrees,
            linkId: link.id, // Track which link this text belongs to
            position: position // Track position for this link
        };
        
        editor.objects.push(text);
        editor.selectedObject = text;
        editor.selectedObjects = [text];
        editor.updateTextProperties();
    }
};

console.log('[topology-text-attachment.js] TextAttachment loaded');
