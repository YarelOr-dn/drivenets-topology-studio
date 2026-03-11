/**
 * topology-link-drawing.js - Link Drawing Module
 * 
 * Extracted from topology.js for modular architecture
 * Contains: drawLink, drawUnboundLink
 * 
 * These functions handle rendering of links between devices.
 */

'use strict';

// Export LinkDrawing to global scope
window.LinkDrawing = {
    drawLink(editor, link) {
        // Skip hidden links (e.g., when BD visibility is toggled off)
        if (link._hidden || link.hidden) return;
        
        // Handle unbound links differently
        if (link.type === 'unbound') {
            editor.drawUnboundLink(link);
            return;
        }
        
        const device1 = editor.objects.find(obj => obj.id === link.device1);
        const device2 = editor.objects.find(obj => obj.id === link.device2);
        
        if (!device1 || !device2) return;
        
        const isSelected = editor.selectedObject === link || editor.selectedObjects.includes(link);
        
        // Calculate connection points using shape-aware edge calculation
        const angle = Math.atan2(device2.y - device1.y, device2.x - device1.x);
        const startPt = editor.getLinkConnectionPoint(device1, angle);
        const endPt = editor.getLinkConnectionPoint(device2, angle + Math.PI);
        const startX = startPt.x;
        const startY = startPt.y;
        const endX = endPt.x;
        const endY = endPt.y;
        
        // DYNAMIC link index calculation for tracking across all link types
        // This ensures that QL, SUL, and BUL links are all counted together
        // and positioned correctly relative to each other for seamless visual integration
        const connectedLinks = editor.objects.filter(obj => {
            // Quick Links (type: 'link')
            if (obj.type === 'link' && obj.device1 && obj.device2) {
                return (obj.device1 === device1.id && obj.device2 === device2.id) ||
                       (obj.device1 === device2.id && obj.device2 === device1.id);
            }
            
            // Standalone Unbound Links (SUL) - direct device attachment
            if (obj.type === 'unbound' && obj.device1 && obj.device2) {
                return (obj.device1 === device1.id && obj.device2 === device2.id) ||
                       (obj.device1 === device2.id && obj.device2 === device1.id);
            }
            
            // BUL chains with endpoints attached to devices
            if (obj.type === 'unbound' && (obj.mergedWith || obj.mergedInto)) {
                const objEndpoints = editor.getBULEndpointDevices(obj);
                if (!objEndpoints.hasEndpoints) return false;
                return (objEndpoints.device1 === device1.id && objEndpoints.device2 === device2.id) ||
                       (objEndpoints.device1 === device2.id && objEndpoints.device2 === device1.id);
            }
            
            return false;
        }).sort((a, b) => {
            // Sort by ID to ensure stable order
            // Extract number from ID (link_123 -> 123)
            const idA = parseInt(a.id.split('_')[1]) || 0;
            const idB = parseInt(b.id.split('_')[1]) || 0;
            return idA - idB;
        });
        
        const linkIndex = connectedLinks.findIndex(l => l.id === link.id);
        if (linkIndex === -1) return; // Should not happen
        
        // NORMALIZE perpendicular direction for true bidirectional behavior
        // Always use the same perpendicular direction regardless of link direction
        // Sort device IDs to get consistent orientation
        const sortedIds = [link.device1, link.device2].sort();
        const isNormalDirection = link.device1 === sortedIds[0];
        
        // First link (index 0) is dead center - no offset
        let offsetAmount = 0;
        let direction = 0;
        if (linkIndex > 0) {
            // User requested logic:
            // First (0): Middle
            // Second (1): Right (+)
            // Third (2): Left (-)
            // Fourth (3): Right (+)
            // Fifth (4): Left (-)
            
            // Logic:
            // ceil(index / 2) gives magnitude: ceil(1/2)=1, ceil(2/2)=1, ceil(3/2)=2...
            // direction: index odd -> 1 (Right), index even -> -1 (Left)
            
            const magnitude = Math.ceil(linkIndex / 2) * 20;
            direction = (linkIndex % 2 === 1) ? 1 : -1;
            offsetAmount = magnitude * direction;
        }
        
        // Calculate perpendicular offset with normalized direction
        let perpAngle = angle + Math.PI / 2;
        // Flip perpendicular if link is in reverse direction (ensures consistent sides)
        if (!isNormalDirection) {
            perpAngle += Math.PI; // Flip 180 degrees
        }
        
        const offsetX = Math.cos(perpAngle) * offsetAmount;
        const offsetY = Math.sin(perpAngle) * offsetAmount;
        
        // Calculate offset start/end points
        const offsetStartX = startX + offsetX;
        const offsetStartY = startY + offsetY;
        const offsetEndX = endX + offsetX;
        const offsetEndY = endY + offsetY;
        
        // Calculate touch points on device edges that account for offset
        // Use shape-aware edge intersection
        const actualStartAngle = Math.atan2(device2.y - device1.y, device2.x - device1.x);
        
        // Start with base touch points (centered line) - shape-aware
        const baseStartPt = editor.getLinkConnectionPoint(device1, actualStartAngle);
        const baseEndPt = editor.getLinkConnectionPoint(device2, actualStartAngle + Math.PI);
        
        // Apply offset to create target line
        const targetStartX = baseStartPt.x + offsetX;
        const targetStartY = baseStartPt.y + offsetY;
        const targetEndX = baseEndPt.x + offsetX;
        const targetEndY = baseEndPt.y + offsetY;
        
        // Calculate direction from device centers to offset target points
        const startDirAngle = Math.atan2(targetStartY - device1.y, targetStartX - device1.x);
        const endDirAngle = Math.atan2(targetEndY - device2.y, targetEndX - device2.x);
        
        // Final touch points on device edges along these directions (shape-aware)
        const finalStartPt = editor.getLinkConnectionPoint(device1, startDirAngle);
        const finalEndPt = editor.getLinkConnectionPoint(device2, endDirAngle);
        let finalStartX = finalStartPt.x;
        let finalStartY = finalStartPt.y;
        let finalEndX = finalEndPt.x;
        let finalEndY = finalEndPt.y;
        
        // Store original endpoints for arrow drawing (before shortening)
        const origEndX = finalEndX;
        const origEndY = finalEndY;
        const origStartX = finalStartX;
        const origStartY = finalStartY;
        
        // Get link width and style early for arrow shortening
        const linkWidthEarly = link.width !== undefined ? link.width : editor.currentLinkWidth;
        const linkStyleEarly = link.style !== undefined ? link.style : 'solid';
        const isArrowStyle = linkStyleEarly === 'arrow' || linkStyleEarly === 'double-arrow' || 
                            linkStyleEarly === 'dashed-arrow' || linkStyleEarly === 'dashed-double-arrow';
        
        // ENHANCED: Shorten line for arrow styles so line doesn't show through arrowhead
        // CRITICAL: Only shorten STRAIGHT lines - curved lines use the filled arrow to cover overlap
        const curveWillBeEnabled = (link.curveOverride !== undefined ? link.curveOverride : editor.linkCurveMode) && editor.magneticFieldStrength > 0;
        const arrowInset = isArrowStyle ? (10 + (linkWidthEarly * 3) + linkWidthEarly) : 0;
        
        // Only shorten for STRAIGHT lines (not curved) to maintain arrow alignment
        if (isArrowStyle && !curveWillBeEnabled) {
            const lineAngle = Math.atan2(finalEndY - finalStartY, finalEndX - finalStartX);
            
            // Shorten end for drawing
            finalEndX = origEndX - Math.cos(lineAngle) * arrowInset;
            finalEndY = origEndY - Math.sin(lineAngle) * arrowInset;
            
            // Shorten start for double-arrow
            if (linkStyleEarly === 'double-arrow' || linkStyleEarly === 'dashed-double-arrow') {
                finalStartX = origStartX + Math.cos(lineAngle) * arrowInset;
                finalStartY = origStartY + Math.sin(lineAngle) * arrowInset;
            }
        }
        
        // Update link positions (used by hitbox detection) - use ORIGINAL positions (arrow tips)
        // This ensures TP clickable area is at the arrow tip, not inside the arrow
        link.start = { x: origStartX, y: origStartY };
        link.end = { x: origEndX, y: origEndY };
        
        // Clear stored control points - will be set below if curve is enabled
        link._cp1 = null;
        link._cp2 = null;
        
        // Determine if curve mode is enabled for this link
        // Magnetic field must be > 0 for curves to work
        const curveEnabled = (link.curveOverride !== undefined ? link.curveOverride : editor.linkCurveMode) && editor.magneticFieldStrength > 0;
        
        // ENHANCED: Use clipping to create true transparent gaps for attached text
        const attachedTexts = editor.objects.filter(obj => 
            obj.type === 'text' && 
            obj.linkId === link.id && 
            obj._onLinkLine === true
        );
        
        if (attachedTexts.length > 0) {
            editor.ctx.save();
            // Create clipping region that excludes text box areas
            editor.ctx.beginPath();
            // Draw a large rectangle covering the whole canvas
            editor.ctx.rect(-100000, -100000, 200000, 200000);
            
            // For each attached text, cut out its area (counter-clockwise for hole)
            for (const textObj of attachedTexts) {
                // Calculate text box dimensions (multi-line aware)
                editor.ctx.save();
                const fontStyle = textObj.fontStyle || 'normal';
                const fontWeight = textObj.fontWeight || 'normal';
                const fontFamily = textObj.fontFamily || 'Arial, sans-serif';
                editor.ctx.font = `${fontStyle} ${fontWeight} ${textObj.fontSize}px ${fontFamily}`;
                
                const textContent = textObj.text || 'Text';
                const lines = textContent.split('\n');
                const fontSize = parseInt(textObj.fontSize) || 14;
                const lineHeight = fontSize * 1.3;
                let maxLineW = 0;
                for (const line of lines) {
                    const m = editor.ctx.measureText(line || ' ');
                    if (m.width > maxLineW) maxLineW = m.width;
                }
                editor.ctx.restore();
                
                const w = maxLineW;
                const h = lines.length * lineHeight;
                const isAttached = !!textObj.linkId && textObj._onLinkLine === true;
                const padding = isAttached ? (textObj.backgroundPadding !== undefined ? textObj.backgroundPadding : 4) : 4;
                const gapW = w + padding * 2;
                const gapH = h + padding * 2;
                
                // Use effective rotation so gap aligns with drawn text
                const effGapRot = editor.getEffectiveTextRotation ? editor.getEffectiveTextRotation(textObj) : (textObj.rotation || 0);
                const textAngle = effGapRot * Math.PI / 180;
                const cos = Math.cos(textAngle);
                const sin = Math.sin(textAngle);
                
                // Calculate corners of the text box in world space (counter-clockwise for clipping hole)
                const corners = [
                    { x: -gapW/2, y: -gapH/2 },
                    { x: -gapW/2, y: gapH/2 },
                    { x: gapW/2, y: gapH/2 },
                    { x: gapW/2, y: -gapH/2 }
                ];
                
                // Transform corners to world space
                const worldCorners = corners.map(c => ({
                    x: textObj.x + c.x * cos - c.y * sin,
                    y: textObj.y + c.x * sin + c.y * cos
                }));
                
                // Add hole (counter-clockwise)
                editor.ctx.moveTo(worldCorners[0].x, worldCorners[0].y);
                for (let i = 1; i < worldCorners.length; i++) {
                    editor.ctx.lineTo(worldCorners[i].x, worldCorners[i].y);
                }
                editor.ctx.closePath();
            }
            
            editor.ctx.clip('evenodd');
        }
        
        // Draw curved path for multiple links (more elegant)
        editor.ctx.beginPath();
        
        let cp1x, cp1y, cp2x, cp2y;
        
        // MANUAL CURVE MODE: Use user-defined control point (relative or absolute during drag)
        const effectiveCurveMode = editor.getEffectiveCurveMode(link);
        const hasManualCurve = link.manualCurvePoint || link.manualCurveOffset || link.manualControlPoint || editor.getAttachedTextAsCP(link);
        if (effectiveCurveMode === 'manual' && hasManualCurve) {
            // Calculate midpoint and link geometry
            const straightMidX = (finalStartX + finalEndX) / 2;
            const straightMidY = (finalStartY + finalEndY) / 2;
            const linkDx = finalEndX - finalStartX;
            const linkDy = finalEndY - finalStartY;
            const linkLength = Math.sqrt(linkDx * linkDx + linkDy * linkDy);
            
            // Get the target midpoint (where user wants curve to pass through)
            // CRITICAL: Use the EXACT position where user released the mouse
            let targetMidX, targetMidY;
            if (link.manualControlPoint) {
                // During active drag: use current mouse position
                targetMidX = link.manualControlPoint.x;
                targetMidY = link.manualControlPoint.y;
            } else if (link.manualCurvePoint) {
                // After release: use the EXACT saved position (no conversion!)
                targetMidX = link.manualCurvePoint.x;
                targetMidY = link.manualCurvePoint.y;
            } else if (link.manualCurveOffset) {
                // Legacy offset format - convert to absolute
                const midX = straightMidX;
                const midY = straightMidY;
                targetMidX = midX + link.manualCurveOffset.x;
                targetMidY = midY + link.manualCurveOffset.y;
            } else {
                // Check for attached text acting as CP
                const attachedText = editor.getAttachedTextAsCP(link);
                if (attachedText) {
                    targetMidX = attachedText.x;
                    targetMidY = attachedText.y;
                } else {
                    targetMidX = straightMidX;
                    targetMidY = straightMidY;
                }
            }
            
            // Calculate perpendicular offset (how far curve is pulled from straight line)
            const perpDx = targetMidX - straightMidX;
            const perpDy = targetMidY - straightMidY;
            const perpDistance = Math.sqrt(perpDx * perpDx + perpDy * perpDy);
            
            // EXACT CURVE: Curve passes EXACTLY through the CP location
            // For cubic bezier with cp1 = cp2 = cp, the midpoint at t=0.5 is:
            //   M = 0.125*P0 + 0.75*cp + 0.125*P1
            // Solving for cp to make curve pass through target point M:
            //   cp = (8*M - P0 - P1) / 6
            if (perpDistance > 0.5 && linkLength > 0) {
                // EXACT MATH: Calculate control point so curve passes through targetMid
                const cpX = (8 * targetMidX - finalStartX - finalEndX) / 6;
                const cpY = (8 * targetMidY - finalStartY - finalEndY) / 6;
                
                // Both control points at the same position for smooth symmetric curve
                cp1x = cpX;
                cp1y = cpY;
                cp2x = cpX;
                cp2y = cpY;
            } else {
                // Fallback to original parabolic curve for very small curves
                const bezierX = (4 * targetMidX - straightMidX) / 3;
                const bezierY = (4 * targetMidY - straightMidY) / 3;
                cp1x = bezierX;
                cp1y = bezierY;
                cp2x = bezierX;
                cp2y = bezierY;
            }
            
            // Store control points for hitbox detection
            link._cp1 = { x: cp1x, y: cp1y };
            link._cp2 = { x: cp2x, y: cp2y };
            
            // Also store rendered endpoints for handle calculation
            link._renderedEndpoints = { startX: finalStartX, startY: finalStartY, endX: finalEndX, endY: finalEndY };
            
            editor.ctx.moveTo(finalStartX, finalStartY);
            editor.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, finalEndX, finalEndY);
        }
        // ENHANCED: Check if "Keep Current Curve" is enabled - use saved curve shape
        else if (curveEnabled && link.keepCurve && link.savedCurveOffset) {
            // Calculate control points based on saved relative curve offset
            const midX = (finalStartX + finalEndX) / 2;
            const midY = (finalStartY + finalEndY) / 2;
            const linkLength = Math.sqrt(
                Math.pow(finalEndX - finalStartX, 2) + 
                Math.pow(finalEndY - finalStartY, 2)
            );
            
            // Apply saved curve offsets scaled to current link length
            cp1x = midX + link.savedCurveOffset.cp1OffsetX * linkLength;
            cp1y = midY + link.savedCurveOffset.cp1OffsetY * linkLength;
            cp2x = midX + link.savedCurveOffset.cp2OffsetX * linkLength;
            cp2y = midY + link.savedCurveOffset.cp2OffsetY * linkLength;
            
            // Store control points for hitbox detection
            link._cp1 = { x: cp1x, y: cp1y };
            link._cp2 = { x: cp2x, y: cp2y };
            
            // Store rendered endpoints for handle calculation
            link._renderedEndpoints = { startX: finalStartX, startY: finalStartY, endX: finalEndX, endY: finalEndY };
            
            // For curved lines - draw to full endpoints, filled arrow covers any overlap
            editor.ctx.moveTo(finalStartX, finalStartY);
            editor.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, finalEndX, finalEndY);
        } else if (curveEnabled) {
            // Curve mode enabled - check for obstacles and curve around them
            const obstacles = editor.findAllObstaclesOnPath(finalStartX, finalStartY, finalEndX, finalEndY, link);
            
            if (obstacles.length > 0) {
                // ENHANCED: Smart curve calculation that ensures clearance even when line passes directly over devices
                
                // Calculate path midpoint and link direction
                const straightMidX = (finalStartX + finalEndX) / 2;
                const straightMidY = (finalStartY + finalEndY) / 2;
                const linkLength = Math.sqrt(Math.pow(finalEndX - finalStartX, 2) + Math.pow(finalEndY - finalStartY, 2));
                
                // Link direction vector (normalized)
                const linkDirX = (finalEndX - finalStartX) / linkLength;
                const linkDirY = (finalEndY - finalStartY) / linkLength;
                
                // Perpendicular to link (for deflection direction)
                const perpX = -linkDirY;
                const perpY = linkDirX;
                
                // ENHANCED: Track pressure from each perpendicular side separately
                // This prevents opposite-side obstacles from canceling each other out
                let closestObstacleRadius = 0;
                let minDistanceToLine = Infinity;
                let positiveSidePressure = 0;  // Pressure from positive perpendicular direction
                let negativeSidePressure = 0;  // Pressure from negative perpendicular direction
                let maxDeflectionNeeded = 0;
                
                // ENHANCED: Use per-link curve magnitude if set, otherwise use global
                const effectiveMagnitude = link.curveMagnitude !== undefined ? link.curveMagnitude : editor.magneticFieldStrength;
                const magneticNormalized = effectiveMagnitude / 80;
                const magneticCurve = Math.pow(magneticNormalized, 0.7); // Slight curve for more responsive low-end
                
                obstacles.forEach((obstacleInfo) => {
                    const obstacle = obstacleInfo.device;
                    
                    // CRITICAL: Calculate PERPENDICULAR distance from obstacle center to the STRAIGHT LINE
                    const toObstacleX = obstacle.x - finalStartX;
                    const toObstacleY = obstacle.y - finalStartY;
                    
                    // Project onto link direction to find closest point on line
                    const projLength = toObstacleX * linkDirX + toObstacleY * linkDirY;
                    const closestOnLineX = finalStartX + linkDirX * projLength;
                    const closestOnLineY = finalStartY + linkDirY * projLength;
                    
                    // Vector from closest point on line TO obstacle (points toward obstacle)
                    const towardObstacleX = obstacle.x - closestOnLineX;
                    const towardObstacleY = obstacle.y - closestOnLineY;
                    const perpDist = Math.sqrt(towardObstacleX * towardObstacleX + towardObstacleY * towardObstacleY) || 0.1;
                    
                    minDistanceToLine = Math.min(minDistanceToLine, perpDist);
                    
                    // ENHANCED: Dynamic clearance based on magnetic field strength
                    const baseClearance = obstacle.radius + 15;
                    const extraClearance = 25 * magneticCurve; // More clearance at higher magnetic field
                    const requiredClearance = baseClearance + extraClearance;
                    
                    // Calculate deflection needed - scales smoothly with magnetic field
                    const baseDeflection = Math.max(0, requiredClearance - perpDist);
                    const neededDeflection = baseDeflection * (1 + magneticCurve); // Amplify with magnetic field
                    
                    // ENHANCED: Smoother repulsion formula with magnetic field control
                    const proximityFactor = Math.pow(requiredClearance / (perpDist + 1), 1 + magneticCurve * 0.5);
                    const repulsionStrength = neededDeflection * proximityFactor * (0.5 + magneticCurve * 1.5);
                    
                    // Determine which side of the link this obstacle is on
                    const sideSign = towardObstacleX * perpX + towardObstacleY * perpY;
                    
                    if (sideSign > 0) {
                        positiveSidePressure += repulsionStrength;
                    } else {
                        negativeSidePressure += repulsionStrength;
                    }
                    
                    maxDeflectionNeeded = Math.max(maxDeflectionNeeded, neededDeflection);
                    closestObstacleRadius = Math.max(closestObstacleRadius, obstacle.radius);
                });
                
                // ENHANCED: Choose curve direction based on which side has LESS pressure
                let curveDir = 1;
                if (positiveSidePressure > negativeSidePressure) {
                    curveDir = -1;  // More pressure from positive side - curve toward negative
                } else if (negativeSidePressure > positiveSidePressure) {
                    curveDir = 1;   // More pressure from negative side - curve toward positive
                }
                
                // Calculate deflection magnitude based on the higher pressure
                const deflectionMag = Math.max(positiveSidePressure, negativeSidePressure);
                
                // Use the perpendicular direction multiplied by curve direction
                const totalRepulsionX = perpX * curveDir * deflectionMag;
                const totalRepulsionY = perpY * curveDir * deflectionMag;
                
                // ENHANCED: Max deflection scales with magnetic field for dramatic effect
                const maxDeflectionBase = Math.max(linkLength * 0.4, closestObstacleRadius * 2);
                const maxDeflectionBonus = Math.max(linkLength * 0.3, closestObstacleRadius * 2) * magneticCurve;
                const maxDeflection = maxDeflectionBase + maxDeflectionBonus;
                const actualDeflection = Math.min(deflectionMag, maxDeflection);
                
                const normalizedRepulX = totalRepulsionX / (deflectionMag || 1);
                const normalizedRepulY = totalRepulsionY / (deflectionMag || 1);
                
                const deflectedMidX = straightMidX + normalizedRepulX * actualDeflection;
                const deflectedMidY = straightMidY + normalizedRepulY * actualDeflection;
                
                // ENHANCED: Control weight varies with magnetic field for smoother curves
                // Low magnetic = subtle curves (0.5), High magnetic = dramatic curves (0.8)
                const controlWeight = 0.5 + magneticCurve * 0.3;
                const midWeight = 1 - controlWeight;
                
                cp1x = finalStartX * midWeight + deflectedMidX * controlWeight;
                cp1y = finalStartY * midWeight + deflectedMidY * controlWeight;
                cp2x = finalEndX * midWeight + deflectedMidX * controlWeight;
                cp2y = finalEndY * midWeight + deflectedMidY * controlWeight;
                
                // Store control points for hitbox detection
                link._cp1 = { x: cp1x, y: cp1y };
                link._cp2 = { x: cp2x, y: cp2y };
                
                // Store rendered endpoints for handle calculation
                link._renderedEndpoints = { startX: finalStartX, startY: finalStartY, endX: finalEndX, endY: finalEndY };
                
                // For curved lines - draw to full endpoints, filled arrow covers any overlap
                editor.ctx.moveTo(finalStartX, finalStartY);
                editor.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, finalEndX, finalEndY);
        } else {
                // No obstacles - add slight curvature for visual separation
            const curveOffset = linkIndex > 0 ? Math.ceil(linkIndex / 2) * 10 * direction : 0;
            cp1x = finalStartX + Math.cos(perpAngle) * curveOffset;
            cp1y = finalStartY + Math.sin(perpAngle) * curveOffset;
            cp2x = finalEndX + Math.cos(perpAngle) * curveOffset;
            cp2y = finalEndY + Math.sin(perpAngle) * curveOffset;
        
            // Store control points for hitbox detection
            link._cp1 = { x: cp1x, y: cp1y };
            link._cp2 = { x: cp2x, y: cp2y };
            
            // Store rendered endpoints for handle calculation
            link._renderedEndpoints = { startX: finalStartX, startY: finalStartY, endX: finalEndX, endY: finalEndY };
        
                // For curved lines - draw to full endpoints, filled arrow covers any overlap
        editor.ctx.moveTo(finalStartX, finalStartY);
        editor.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, finalEndX, finalEndY);
            }
        } else {
            // Curve mode disabled - draw straight line (static, no gravity)
            editor.ctx.moveTo(finalStartX, finalStartY);
            editor.ctx.lineTo(finalEndX, finalEndY);
            
            // Store rendered endpoints for handle calculation (also for straight lines)
            link._renderedEndpoints = { startX: finalStartX, startY: finalStartY, endX: finalEndX, endY: finalEndY };
            // Clear curve control points since this is a straight line
            link._cp1 = null;
            link._cp2 = null;
        }
        
        // ENHANCED: Auto-adjust link color for visibility in current mode
        let linkColor = link.color;
        if (!isSelected) {
            // Adjust color based on mode (darken light colors in light mode, brighten dark colors in dark mode)
            linkColor = editor.adjustColorForMode(link.color);
        }
        
        // Get link width (use per-link width if set, otherwise use global currentLinkWidth)
        const linkWidth = link.width !== undefined ? link.width : editor.currentLinkWidth;
        
        // ENHANCED: Instant visual feedback with glow on selection
        // Skip highlight when editing color/width/style to see actual appearance
        const skipHighlight = editor._colorEditingLink === link;
        
        // THEME-AWARE SELECTION: Use contrasting colors based on current mode
        // In light mode with light links, we need darker selection colors
        // In dark mode with dark links, we need lighter selection colors
        const selectionColors = editor.getLinkSelectionColors(linkColor);
        const selectionColor = selectionColors.stroke;
        const selectionGlow = selectionColors.glow;
        
        if (link._xrayCaptureActive) {
            editor.ctx.save();
            editor.ctx.shadowColor = 'rgba(0, 200, 255, 0.6)';
            editor.ctx.shadowBlur = 14;
            editor.ctx.strokeStyle = 'rgba(0, 200, 255, 0.35)';
            editor.ctx.lineWidth = linkWidth + 8;
            editor.ctx.setLineDash([6, 4]);
            editor.ctx.beginPath();
            editor.ctx.moveTo(startX, startY);
            editor.ctx.lineTo(endX, endY);
            editor.ctx.stroke();
            editor.ctx.setLineDash([]);
            editor.ctx.restore();
        }
        if (isSelected && !skipHighlight) {
            editor.ctx.shadowColor = selectionGlow;
            editor.ctx.shadowBlur = 8;
            editor.ctx.strokeStyle = selectionColor;
            editor.ctx.lineWidth = linkWidth + 2;
        } else {
            editor.ctx.shadowBlur = 0;
            editor.ctx.strokeStyle = linkColor;
            editor.ctx.lineWidth = linkWidth;
        }
        
        // CRITICAL: Use link's own style if set
        // If link has no style property (old links), default to 'solid' (not global style)
        // This ensures existing links don't change when global style changes
        const linkStyle = link.style !== undefined ? link.style : 'solid';
        
        // ENHANCED: Apply link style (solid, dashed, dashed-wide, dotted, arrow variants)
        // Scale dash patterns with link width for consistent visual appearance
        // CRITICAL: Use butt lineCap for arrow styles to prevent bump at curve endpoints
        const isArrowStyleForCap = linkStyle === 'arrow' || linkStyle === 'double-arrow' || 
                                    linkStyle === 'dashed-arrow' || linkStyle === 'dashed-double-arrow';
        if (isArrowStyleForCap) {
            editor.ctx.lineCap = 'butt'; // Prevents line from extending past arrow
        } else {
            // Use round lineCap and lineJoin for smoother, more circular curves
            editor.ctx.lineCap = 'round';
            editor.ctx.lineJoin = 'round';
        }
        
        if (linkStyle === 'dashed' || linkStyle === 'dashed-arrow' || linkStyle === 'dashed-double-arrow') {
            // Scale dash pattern with width: base 8,4 at width 2, scale proportionally
            const dashScale = Math.max(1, linkWidth / 2);
            editor.ctx.setLineDash([8 * dashScale, 4 * dashScale]);
        } else if (linkStyle === 'dashed-wide') {
            // Scale wide dash pattern with width
            const dashScale = Math.max(1, linkWidth / 2);
            editor.ctx.setLineDash([18 * dashScale, 18 * dashScale]);
        } else if (linkStyle === 'dotted') {
            // For dotted, use round caps - the dot size IS the lineWidth
            // Scale gap based on line width so dots stay visible when thick
            editor.ctx.lineCap = 'round';
            const dotSize = Math.max(linkWidth * 2, 4); // Bigger dots (minimum 4px)
            const dotGap = Math.max(linkWidth * 4 + 12, 16); // Gap scales with width (minimum 16px)
            editor.ctx.setLineDash([0.1, dotGap]); // Tiny dash with scaled gap
            editor.ctx.lineWidth = dotSize; // Dot diameter = lineWidth
        } else {
            editor.ctx.setLineDash([]); // Solid line
        }
        
        editor.ctx.stroke();
        
        // ENHANCED: Restore clipping context if we applied it for text gaps
        if (attachedTexts.length > 0) {
            editor.ctx.restore();
        }
        
        // Reset lineCap, lineJoin and lineWidth after dotted or any link
            editor.ctx.lineCap = 'butt';
        editor.ctx.lineJoin = 'miter';
        if (linkStyle === 'dotted') {
            editor.ctx.lineWidth = linkWidth;
        }
        
        editor.ctx.shadowBlur = 0; // Reset shadow for other elements
        editor.ctx.setLineDash([]); // Reset dash
        
        // Draw arrowheads (single arrow or double-arrow, including dashed variants)
        // ENHANCED: Always show arrows regardless of width - scale arrow size with link width
        const isArrowStyleQL = linkStyle === 'arrow' || linkStyle === 'double-arrow' || 
                              linkStyle === 'dashed-arrow' || linkStyle === 'dashed-double-arrow';
        
        // Clear arrow tip positions for non-arrow links
        if (!isArrowStyleQL) {
            link._arrowTipStart = null;
            link._arrowTipEnd = null;
        }
        
        if (isArrowStyleQL) {
            // Scale arrow size with link width (base 16px for width 2, scales proportionally)
            const arrowLength = 10 + (linkWidth * 3);
            const arrowAngleSpread = Math.PI / 5; // 36° angle for nice arrowhead
            
            // =========================================================================
            // ARROW TIP ALIGNMENT - CRITICAL DOCUMENTATION (Dec 2025)
            // =========================================================================
            // For Bezier curves: tangent at t=1 is (P3-P2), tangent at t=0 is (P1-P0)
            //
            // ARROW DRAWING GEOMETRY:
            // - END arrow uses MINUS: `arrowEndX - arrowLength * cos(endAngle)`
            //   → Arrow body extends BACKWARD from tip, so arrow POINTS in endAngle direction
            // - START arrow uses PLUS: `arrowStartX + arrowLength * cos(startAngle)`
            //   → Arrow body extends FORWARD along startAngle, so arrow POINTS in (startAngle + π) direction
            //
            // THEREFORE:
            // - endAngle = direction of travel at end (tangent pointing outward) ✓
            // - startAngle = direction of travel at start (tangent), so startAngle + π = outward ✓
            //
            // DO NOT CHANGE startAngle to be "opposite of travel" - this breaks the geometry!
            // =========================================================================
            let endAngle, startAngle;
            
            // For CURVED links: arrow tips at curve endpoints (finalEndX/Y after curve drawing)
            // For STRAIGHT links: arrow tips at original positions (line is shortened, arrow covers end)
            const arrowEndX = curveEnabled ? finalEndX : origEndX;
            const arrowEndY = curveEnabled ? finalEndY : origEndY;
            const arrowStartX = curveEnabled ? finalStartX : origStartX;
            const arrowStartY = curveEnabled ? finalStartY : origStartY;
            
            // Store arrow tip positions for hitbox detection
            link._arrowTipEnd = { x: arrowEndX, y: arrowEndY };
            link._arrowTipStart = { x: arrowStartX, y: arrowStartY };
            // Angles and geometry stored after calculation below (see _arrowEndAngle etc.)
            link._arrowLength = arrowLength;
            link._arrowAngleSpread = arrowAngleSpread;
        
        if (curveEnabled && (cp1x !== undefined && cp2x !== undefined)) {
                // CRITICAL: If control points equal endpoints (no actual curve), use straight line calc
                const cp2AtEnd = Math.abs(finalEndX - cp2x) < 0.1 && Math.abs(finalEndY - cp2y) < 0.1;
                const cp1AtStart = Math.abs(finalStartX - cp1x) < 0.1 && Math.abs(finalStartY - cp1y) < 0.1;
                
                if (cp2AtEnd || cp1AtStart) {
                    // Control points at endpoints - effectively straight line
                    // Both angles = direction of travel (start→end)
                    endAngle = Math.atan2(finalEndY - finalStartY, finalEndX - finalStartX);
                    startAngle = Math.atan2(finalEndY - finalStartY, finalEndX - finalStartX);
                } else {
                    // True curve - use Bezier tangent derivatives
                    // endAngle: tangent at t=1 = direction from cp2 to curve endpoint
                    endAngle = Math.atan2(finalEndY - cp2y, finalEndX - cp2x);
                    // startAngle: tangent at t=0 = direction from curve start toward cp1
                    startAngle = Math.atan2(cp1y - finalStartY, cp1x - finalStartX);
                }
        } else {
                // Straight lines: both angles = direction of travel using ORIGINAL positions
                endAngle = Math.atan2(origEndY - origStartY, origEndX - origStartX);
                startAngle = Math.atan2(origEndY - origStartY, origEndX - origStartX);
        }
            // Store angles for hitbox detection
            link._arrowEndAngle = endAngle;
            link._arrowStartAngle = startAngle;
        
            // Store arrow colors for deferred drawing pass (arrows drawn AFTER devices)
            link._arrowFillColor = isSelected && !skipHighlight ? selectionColor : linkColor;
            link._arrowStrokeColor = linkColor;
            link._arrowStrokeWidth = 1;
            
            // Store which endpoints have arrows (for hitbox and deferred drawing)
            link._arrowAtEnd = true;
            link._arrowAtStart = (linkStyle === 'double-arrow' || linkStyle === 'dashed-double-arrow');
        } else {
            link._arrowAtEnd = false;
            link._arrowAtStart = false;
        }
        
        // Selection highlight with dashed outline
        if (isSelected) {
            editor.ctx.shadowBlur = 0; // No shadow for dashed outline
            editor.ctx.strokeStyle = '#3498db';
            editor.ctx.lineWidth = 1;
            editor.ctx.setLineDash([3, 3]);
            editor.ctx.beginPath();
            editor.ctx.moveTo(finalStartX, finalStartY);
            
            if (curveEnabled && (cp1x !== undefined && cp2x !== undefined)) {
                // Bezier curve
            editor.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, finalEndX, finalEndY);
            } else {
                // Straight line
                editor.ctx.lineTo(finalEndX, finalEndY);
            }
            editor.ctx.stroke();
            editor.ctx.setLineDash([]);
        }
        
        // DEBUG VIEW: Draw link type label above link
        if (editor.showLinkTypeLabels) {
            const midX = (finalStartX + finalEndX) / 2;
            const midY = (finalStartY + finalEndY) / 2;
            
            editor.ctx.save();
            editor.ctx.font = `bold ${11 / editor.zoom}px Arial`;
            editor.ctx.textAlign = 'center';
            editor.ctx.textBaseline = 'bottom';
            
            // Use originType to preserve link creation method
            const label = link.originType || 'QL';
            const padding = 3 / editor.zoom;
            const metrics = editor.ctx.measureText(label);
            const textWidth = metrics.width;
            const textHeight = 11 / editor.zoom;
            
            // Green background for QLs (they never merge with ULs)
            editor.ctx.fillStyle = 'rgba(46, 204, 113, 0.9)';
            editor.ctx.fillRect(
                midX - textWidth / 2 - padding,
                midY - 18 / editor.zoom - textHeight - padding,
                textWidth + padding * 2,
                textHeight + padding * 2
            );
            
            // Draw label text
            editor.ctx.fillStyle = 'white';
            editor.ctx.strokeStyle = '#27ae60';
            editor.ctx.lineWidth = 0.5 / editor.zoom;
            editor.ctx.strokeText(label, midX, midY - 18 / editor.zoom);
            editor.ctx.fillText(label, midX, midY - 18 / editor.zoom);
            
            editor.ctx.restore();
        }
    },
    
    drawUnboundLink(editor, link) {
        // ENHANCED: Check if this link is part of a merged chain - highlight ALL links in the chain
        let isSelected = editor.selectedObject === link || editor.selectedObjects.includes(link);
        
        // If not directly selected, check if ANY link in the merge chain is selected
        if (!isSelected) {
            const mergedLinks = editor.getAllMergedLinks(link);
            for (const mergedLink of mergedLinks) {
                if (mergedLink !== link && (editor.selectedObject === mergedLink || editor.selectedObjects.includes(mergedLink))) {
                    isSelected = true;
                    break;
                }
            }
        }
        
        // CRITICAL: If endpoint is attached to a device, calculate position from device edge
        // This ensures ULs visually connect properly to devices
        let startX, startY, endX, endY;
        
        // Get device references if attached
        const device1 = link.device1 ? editor.objects.find(o => o.id === link.device1) : null;
        const device2 = link.device2 ? editor.objects.find(o => o.id === link.device2) : null;
        
        // Calculate start position (shape-aware)
        if (device1) {
            // Start is attached to device1 - calculate edge position
            const targetX = device2 ? device2.x : link.end.x;
            const targetY = device2 ? device2.y : link.end.y;
            const angle = Math.atan2(targetY - device1.y, targetX - device1.x);
            const startPt = editor.getLinkConnectionPoint(device1, angle);
            startX = startPt.x;
            startY = startPt.y;
            // Also update stored position for consistency
            link.start.x = startX;
            link.start.y = startY;
        } else {
                startX = link.start.x;
                startY = link.start.y;
        }
        
        // Calculate end position (shape-aware)
        if (device2) {
            // End is attached to device2 - calculate edge position
            const targetX = device1 ? device1.x : link.start.x;
            const targetY = device1 ? device1.y : link.start.y;
            const angle = Math.atan2(targetY - device2.y, targetX - device2.x);
            const endPt = editor.getLinkConnectionPoint(device2, angle);
            endX = endPt.x;
            endY = endPt.y;
            // Also update stored position for consistency
            link.end.x = endX;
            link.end.y = endY;
        } else {
        endX = link.end.x;
        endY = link.end.y;
        }
        
        // Store original endpoints for arrow drawing (before shortening)
        const origStartX = startX;
        const origStartY = startY;
        const origEndX = endX;
        const origEndY = endY;
        
        // Get link width and style early for arrow shortening
        const linkWidthEarly = link.width !== undefined ? link.width : editor.currentLinkWidth;
        const linkStyleEarly = link.style !== undefined ? link.style : 'solid';
        const isArrowStyle = linkStyleEarly === 'arrow' || linkStyleEarly === 'double-arrow' || 
                            linkStyleEarly === 'dashed-arrow' || linkStyleEarly === 'dashed-double-arrow';
        
        // Check which endpoints are free TPs (for shortening only free TPs with arrows)
        // CRITICAL: An endpoint is a "free TP" only if it's NOT attached to a device AND NOT an MP (merge point)
        const isStartDeviceAttached = !!link.device1;
        const isEndDeviceAttached = !!link.device2;
        
        // Check if start is an MP (connected to another link via merge)
        let isStartMP = false;
        if (link.mergedWith && link.mergedWith.parentFreeEnd !== 'start') {
            isStartMP = true; // Start is connected to child link
        }
        if (link.mergedInto) {
            const parentLink = editor.objects.find(o => o.id === link.mergedInto.parentId);
            if (parentLink?.mergedWith?.childFreeEnd !== 'start') {
                isStartMP = true; // Start is connected to parent link
            }
        }
        
        // Check if end is an MP (connected to another link via merge)
        let isEndMP = false;
        if (link.mergedWith && link.mergedWith.parentFreeEnd !== 'end') {
            isEndMP = true; // End is connected to child link
        }
        if (link.mergedInto) {
            const parentLink = editor.objects.find(o => o.id === link.mergedInto.parentId);
            if (parentLink?.mergedWith?.childFreeEnd !== 'end') {
                isEndMP = true; // End is connected to parent link
            }
        }
        
        // A TP is "free" only if not attached to device AND not an MP
        const isStartFreeTP = !isStartDeviceAttached && !isStartMP;
        const isEndFreeTP = !isEndDeviceAttached && !isEndMP;
        
        // For arrow drawing/shortening: show arrows at device attachments too, only hide at MPs
        const showArrowAtStart = !isStartMP;
        const showArrowAtEnd = !isEndMP;
        
        // Determine if curve mode is enabled for this unbound link
        // Magnetic field must be > 0 for curves to work (same as QLs)
        // MOVED UP: Need to know this BEFORE shortening to match drawLink behavior
        const curveWillBeEnabled = (link.curveOverride !== undefined ? link.curveOverride : editor.linkCurveMode) && editor.magneticFieldStrength > 0;
        
        // ENHANCED: Shorten line for arrow styles so line doesn't show through arrowhead
        // CRITICAL: Only shorten STRAIGHT lines - curved lines use the filled arrow to cover overlap
        // Extra padding (linkWidth * 1) ensures thick lines are fully hidden behind arrow
        const arrowInset = isArrowStyle ? (10 + (linkWidthEarly * 3) + linkWidthEarly) : 0;
        
        // Only shorten for STRAIGHT lines (not curved) to maintain arrow alignment
        if (isArrowStyle && !curveWillBeEnabled) {
            const lineAngle = Math.atan2(endY - startY, endX - startX);
            
            // For single arrow: determine where the arrow actually goes
            // Arrow goes at the FREE endpoint (TP), not at MPs
            const isDoubleArrow = linkStyleEarly === 'double-arrow' || linkStyleEarly === 'dashed-double-arrow';
            
            // Shorten end if arrow will be shown there
            if (showArrowAtEnd && (isDoubleArrow || isEndFreeTP)) {
                endX = origEndX - Math.cos(lineAngle) * arrowInset;
                endY = origEndY - Math.sin(lineAngle) * arrowInset;
            }
            
            // Shorten start if arrow will be shown there
            // For double-arrow: always shorten both ends at TPs
            // For single-arrow: shorten start if start is the TP (arrow points outward from start)
            if (showArrowAtStart && (isDoubleArrow || (isStartFreeTP && !isEndFreeTP))) {
                startX = origStartX + Math.cos(lineAngle) * arrowInset;
                startY = origStartY + Math.sin(lineAngle) * arrowInset;
            }
        }
        
        // Use the already calculated curve mode value
        const curveEnabled = curveWillBeEnabled;
        
        // CRITICAL: For SULs with both devices attached, calculate curve parameters EXACTLY like QLs
        // This ensures seamless visual integration between QL and SUL
        const isSUL = !link.mergedWith && !link.mergedInto && link.device1 && link.device2;
        let perpAngle = 0;
        let curveDirection = 0;
        
        if (isSUL) {
            // Calculate perpendicular angle for curvature - EXACTLY like drawLink()
            const device1 = editor.objects.find(o => o.id === link.device1);
            const device2 = editor.objects.find(o => o.id === link.device2);
            
            if (device1 && device2) {
                const angle = Math.atan2(device2.y - device1.y, device2.x - device1.x);
                const sortedIds = [link.device1, link.device2].sort();
                const isNormalDirection = link.device1 === sortedIds[0];
                
                perpAngle = angle + Math.PI / 2;
                if (!isNormalDirection) {
                    perpAngle += Math.PI;
                }
                
                // Calculate curve direction based on linkIndex
                const linkIndex = link.linkIndex || 0;
                if (linkIndex > 0) {
                    curveDirection = (linkIndex % 2 === 1) ? 1 : -1; // Odd = Right, Even = Left
                }
            }
        }
        
        // Draw line (curved or straight)
        // ENHANCED: Use clipping to create true transparent gaps for attached text
        const attachedTexts = editor.objects.filter(obj => 
            obj.type === 'text' && 
            obj.linkId === link.id && 
            obj._onLinkLine === true
        );
        
        if (attachedTexts.length > 0) {
            editor.ctx.save();
            // Create clipping region that excludes text box areas
            editor.ctx.beginPath();
            // Draw a large rectangle covering the whole canvas
            editor.ctx.rect(-100000, -100000, 200000, 200000);
            
            // For each attached text, cut out its area (counter-clockwise for hole)
            for (const textObj of attachedTexts) {
                editor.ctx.save();
                const txtMetrics = editor.ctx.measureText(textObj.text || 'Text');
                editor.ctx.restore();
                
                // Calculate text box dimensions
                editor.ctx.save();
                editor.ctx.font = `${textObj.fontSize}px Arial`;
                const metrics = editor.ctx.measureText(textObj.text || 'Text');
                editor.ctx.restore();
                
                const w = metrics.width;
                const h = parseInt(textObj.fontSize);
                const padding = 4;
                const gapW = w + padding * 2;
                const gapH = h + padding * 2;
                
                const effGapRot2 = editor.getEffectiveTextRotation ? editor.getEffectiveTextRotation(textObj) : (textObj.rotation || 0);
                const textAngle = effGapRot2 * Math.PI / 180;
                const cos = Math.cos(textAngle);
                const sin = Math.sin(textAngle);
                
                const corners = [
                    { x: -gapW/2, y: -gapH/2 },
                    { x: -gapW/2, y: gapH/2 },
                    { x: gapW/2, y: gapH/2 },
                    { x: gapW/2, y: -gapH/2 }
                ];
                
                // Transform corners to world space
                const worldCorners = corners.map(c => ({
                    x: textObj.x + c.x * cos - c.y * sin,
                    y: textObj.y + c.x * sin + c.y * cos
                }));
                
                // Add hole (counter-clockwise)
                editor.ctx.moveTo(worldCorners[0].x, worldCorners[0].y);
                for (let i = 1; i < worldCorners.length; i++) {
                    editor.ctx.lineTo(worldCorners[i].x, worldCorners[i].y);
                }
                editor.ctx.closePath();
            }
            
            editor.ctx.clip('evenodd');
        }

        editor.ctx.beginPath();
        let cp1x, cp1y, cp2x, cp2y;
        
        // Clear stored control points - will be set below if curve is enabled
        link._cp1 = null;
        link._cp2 = null;
        
        // MANUAL CURVE MODE: Use user-defined control point (relative or absolute during drag)
        const effectiveCurveMode = editor.getEffectiveCurveMode(link);
        const hasManualCurve = link.manualCurvePoint || link.manualCurveOffset || link.manualControlPoint || editor.getAttachedTextAsCP(link);
        if (effectiveCurveMode === 'manual' && hasManualCurve) {
            let bezierCP;
            
            if (link.manualControlPoint) {
                // During drag: user is dragging the visual midpoint
                // For CUBIC Bezier with cp1=cp2=C, point at t=0.5 is: (P0 + 6*C + P3) / 8
                // To pass through M: C = (8*M - P0 - P3) / 6 = (4*M - midpoint) / 3
                const straightMidX = (startX + endX) / 2;
                const straightMidY = (startY + endY) / 2;
                bezierCP = {
                    x: (4 * link.manualControlPoint.x - straightMidX) / 3,
                    y: (4 * link.manualControlPoint.y - straightMidY) / 3
                };
            } else {
                // After release: calculate from rendered endpoints for consistency
                bezierCP = editor.getManualCurveBezierControlPoint(link, {
                    startX: startX, startY: startY,
                    endX: endX, endY: endY
                });
            }
            
            if (bezierCP) {
                // Use quadratic bezier with single control point
                cp1x = bezierCP.x;
                cp1y = bezierCP.y;
                cp2x = bezierCP.x;
                cp2y = bezierCP.y;
                
                // Store control points for hitbox detection
                link._cp1 = { x: cp1x, y: cp1y };
                link._cp2 = { x: cp2x, y: cp2y };
                
                // Also store rendered endpoints for handle calculation
                link._renderedEndpoints = { startX: startX, startY: startY, endX: endX, endY: endY };
                
                editor.ctx.moveTo(startX, startY);
                editor.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, endX, endY);
            }
        }
        // ENHANCED: Check if keepCurve is enabled and we have saved curve offsets
        // If so, apply the saved curve shape instead of recalculating
        else if (curveEnabled && link.keepCurve && link.savedCurveOffset) {
            const midX = (startX + endX) / 2;
            const midY = (startY + endY) / 2;
            const linkLength = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2));
            
            // Restore control points from saved offsets
            cp1x = midX + link.savedCurveOffset.cp1OffsetX * linkLength;
            cp1y = midY + link.savedCurveOffset.cp1OffsetY * linkLength;
            cp2x = midX + link.savedCurveOffset.cp2OffsetX * linkLength;
            cp2y = midY + link.savedCurveOffset.cp2OffsetY * linkLength;
            
            // Store control points for hitbox detection
            link._cp1 = { x: cp1x, y: cp1y };
            link._cp2 = { x: cp2x, y: cp2y };
            
            // Store rendered endpoints for handle calculation
            link._renderedEndpoints = { startX: startX, startY: startY, endX: endX, endY: endY };
            
            // For curved lines - draw to full endpoints, filled arrow covers any overlap
            editor.ctx.moveTo(startX, startY);
            editor.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, endX, endY);
        } else if (curveEnabled) {
            // Apply guitar string physics to unbound links too
            const obstacles = editor.findAllObstaclesOnPath(startX, startY, endX, endY, link);
            
            if (obstacles.length > 0) {
                // ENHANCED: Smart curve calculation - EXACTLY like drawLink()
                const straightMidX = (startX + endX) / 2;
                const straightMidY = (startY + endY) / 2;
                const linkLength = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2));
                
                // Link direction vector (normalized)
                const linkDirX = (endX - startX) / linkLength;
                const linkDirY = (endY - startY) / linkLength;
                
                // Perpendicular to link (for deflection direction)
                const perpX = -linkDirY;
                const perpY = linkDirX;
                
                // ENHANCED: Use per-link curve magnitude if set, otherwise use global
                const effectiveMagnitude = link.curveMagnitude !== undefined ? link.curveMagnitude : editor.magneticFieldStrength;
                const magneticNormalized = effectiveMagnitude / 80;
                const magneticCurve = Math.pow(magneticNormalized, 0.7);
                
                let closestObstacleRadius = 0;
                let minDistanceToLine = Infinity;
                
                // ENHANCED: Track pressure from each perpendicular side separately
                // This prevents opposite-side obstacles from canceling each other out
                let positiveSidePressure = 0;  // Pressure from positive perpendicular direction
                let negativeSidePressure = 0;  // Pressure from negative perpendicular direction
                let maxDeflectionNeeded = 0;
                
                obstacles.forEach((obstacleInfo) => {
                    const obstacle = obstacleInfo.device;
                    
                    // Calculate PERPENDICULAR distance from obstacle center to the STRAIGHT LINE
                    const toObstacleX = obstacle.x - startX;
                    const toObstacleY = obstacle.y - startY;
                    
                    // Project onto link direction to find closest point on line
                    const projLength = toObstacleX * linkDirX + toObstacleY * linkDirY;
                    const closestOnLineX = startX + linkDirX * projLength;
                    const closestOnLineY = startY + linkDirY * projLength;
                    
                    // Vector from closest point on line TO obstacle (points toward obstacle)
                    const towardObstacleX = obstacle.x - closestOnLineX;
                    const towardObstacleY = obstacle.y - closestOnLineY;
                    const perpDist = Math.sqrt(towardObstacleX * towardObstacleX + towardObstacleY * towardObstacleY) || 0.1;
                    
                    minDistanceToLine = Math.min(minDistanceToLine, perpDist);
                    
                    // ENHANCED: Dynamic clearance based on magnetic field strength
                    const baseClearance = obstacle.radius + 15;
                    const extraClearance = 25 * magneticCurve;
                    const requiredClearance = baseClearance + extraClearance;
                    
                    // Calculate deflection needed - scales smoothly with magnetic field
                    const baseDeflection = Math.max(0, requiredClearance - perpDist);
                    const neededDeflection = baseDeflection * (1 + magneticCurve);
                    
                    // ENHANCED: Smoother repulsion formula with magnetic field control
                    const proximityFactor = Math.pow(requiredClearance / (perpDist + 1), 1 + magneticCurve * 0.5);
                    const repulsionStrength = neededDeflection * proximityFactor * (0.5 + magneticCurve * 1.5);
                    
                    // Determine which side of the link this obstacle is on
                    // Using dot product with perpendicular vector
                    const sideSign = towardObstacleX * perpX + towardObstacleY * perpY;
                    
                    if (sideSign > 0) {
                        positiveSidePressure += repulsionStrength;
                    } else {
                        negativeSidePressure += repulsionStrength;
                    }
                    
                    maxDeflectionNeeded = Math.max(maxDeflectionNeeded, neededDeflection);
                    closestObstacleRadius = Math.max(closestObstacleRadius, obstacle.radius);
                });
                
                // ENHANCED: Choose curve direction based on which side has LESS pressure
                // This ensures the link curves toward the clearer side, avoiding overlap
                let curveDir = 1;
                let totalPressure = positiveSidePressure + negativeSidePressure;
                
                if (positiveSidePressure > negativeSidePressure) {
                    // More pressure from positive side - curve toward negative side
                    curveDir = -1;
                } else if (negativeSidePressure > positiveSidePressure) {
                    // More pressure from negative side - curve toward positive side
                    curveDir = 1;
                }
                // If equal pressure, use default direction (positive)
                
                // Calculate deflection magnitude based on total pressure but in chosen direction
                const deflectionMag = Math.max(positiveSidePressure, negativeSidePressure);
                
                // Use the perpendicular direction multiplied by curve direction
                const totalRepulsionX = perpX * curveDir * deflectionMag;
                const totalRepulsionY = perpY * curveDir * deflectionMag;
                
                // Note: magnitude of totalRepulsion vector equals deflectionMag (perp is unit vector)
                
                // ENHANCED: Max deflection scales with magnetic field
                const maxDeflectionBase = Math.max(linkLength * 0.4, closestObstacleRadius * 2);
                const maxDeflectionBonus = Math.max(linkLength * 0.3, closestObstacleRadius * 2) * magneticCurve;
                const maxDeflection = maxDeflectionBase + maxDeflectionBonus;
                const actualDeflection = Math.min(deflectionMag, maxDeflection);
                const normalizedRepulX = totalRepulsionX / (deflectionMag || 1);
                const normalizedRepulY = totalRepulsionY / (deflectionMag || 1);
                const deflectedMidX = straightMidX + normalizedRepulX * actualDeflection;
                const deflectedMidY = straightMidY + normalizedRepulY * actualDeflection;
                
                // ENHANCED: Control weight varies with magnetic field
                const controlWeight = 0.5 + magneticCurve * 0.3;
                const midWeight = 1 - controlWeight;
                cp1x = startX * midWeight + deflectedMidX * controlWeight;
                cp1y = startY * midWeight + deflectedMidY * controlWeight;
                cp2x = endX * midWeight + deflectedMidX * controlWeight;
                cp2y = endY * midWeight + deflectedMidY * controlWeight;
                
                // Store control points for hitbox detection
                link._cp1 = { x: cp1x, y: cp1y };
                link._cp2 = { x: cp2x, y: cp2y };
                
                // Store rendered endpoints for handle calculation
                link._renderedEndpoints = { startX: startX, startY: startY, endX: endX, endY: endY };
                
                // For curved lines - draw to full endpoints, filled arrow covers any overlap
                editor.ctx.moveTo(startX, startY);
                editor.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, endX, endY);
            } else {
                // No obstacles - add slight curvature for visual separation (EXACTLY like QLs)
                const linkIndex = link.linkIndex || 0;
                const curveOffset = linkIndex > 0 ? Math.ceil(linkIndex / 2) * 10 * curveDirection : 0;
                
                cp1x = startX + Math.cos(perpAngle) * curveOffset;
                cp1y = startY + Math.sin(perpAngle) * curveOffset;
                cp2x = endX + Math.cos(perpAngle) * curveOffset;
                cp2y = endY + Math.sin(perpAngle) * curveOffset;
                
                // Store control points for hitbox detection
                link._cp1 = { x: cp1x, y: cp1y };
                link._cp2 = { x: cp2x, y: cp2y };
                
                // Store rendered endpoints for handle calculation
                link._renderedEndpoints = { startX: startX, startY: startY, endX: endX, endY: endY };
                
                // For curved lines - draw to full endpoints, filled arrow covers any overlap
        editor.ctx.moveTo(startX, startY);
                editor.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, endX, endY);
            }
        } else {
            // Curve disabled - straight line
            editor.ctx.moveTo(startX, startY);
            editor.ctx.lineTo(endX, endY);
            
            // Store rendered endpoints for handle calculation (also for straight lines)
            link._renderedEndpoints = { startX: startX, startY: startY, endX: endX, endY: endY };
            // Clear curve control points since this is a straight line
            link._cp1 = null;
            link._cp2 = null;
        }
        
        // ENHANCED: Auto-adjust link color for visibility in current mode
        let linkColor = link.color;
        if (!isSelected) {
            // Adjust color based on mode (darken light colors in light mode, brighten dark colors in dark mode)
            linkColor = editor.adjustColorForMode(link.color);
        }
        
        // Get link width (use per-link width if set, otherwise use global currentLinkWidth)
        const linkWidth = link.width !== undefined ? link.width : editor.currentLinkWidth;
        
        // THEME-AWARE SELECTION: Use contrasting colors based on current mode
        const selectionColors = editor.getLinkSelectionColors(linkColor);
        const selectionColor = selectionColors.stroke;
        const selectionGlow = selectionColors.glow;
        
        // ENHANCED: Subtle glow effect on selection
        // Skip highlight when editing color/width/style to see actual appearance
        const skipHighlight = editor._colorEditingLink === link;
        if (isSelected && !skipHighlight) {
            editor.ctx.shadowColor = selectionGlow;
            editor.ctx.shadowBlur = 8;
            editor.ctx.strokeStyle = selectionColor;
            editor.ctx.lineWidth = linkWidth + 2;
        } else {
            editor.ctx.shadowBlur = 0;
            editor.ctx.strokeStyle = linkColor;
            editor.ctx.lineWidth = linkWidth;
        }
        
        // CRITICAL: Use link's own style if set
        // If link has no style property (old links), default to 'solid' (not global style)
        // This ensures existing links don't change when global style changes
        const linkStyle = link.style !== undefined ? link.style : 'solid';
        
        // ENHANCED: Apply link style (solid, dashed, dashed-wide, dotted, arrow variants)
        // Scale dash patterns with link width for consistent visual appearance
        // CRITICAL: Use butt lineCap for arrow styles to prevent bump at curve endpoints
        const isArrowStyleForCap = linkStyle === 'arrow' || linkStyle === 'double-arrow' || 
                                    linkStyle === 'dashed-arrow' || linkStyle === 'dashed-double-arrow';
        if (isArrowStyleForCap) {
            editor.ctx.lineCap = 'butt'; // Prevents line from extending past arrow
        } else {
            // Use round lineCap and lineJoin for smoother, more circular curves
            editor.ctx.lineCap = 'round';
            editor.ctx.lineJoin = 'round';
        }
        
        if (linkStyle === 'dashed' || linkStyle === 'dashed-arrow' || linkStyle === 'dashed-double-arrow') {
            // Scale dash pattern with width: base 8,4 at width 2, scale proportionally
            const dashScale = Math.max(1, linkWidth / 2);
            editor.ctx.setLineDash([8 * dashScale, 4 * dashScale]);
        } else if (linkStyle === 'dashed-wide') {
            // Scale wide dash pattern with width
            const dashScale = Math.max(1, linkWidth / 2);
            editor.ctx.setLineDash([18 * dashScale, 18 * dashScale]);
        } else if (linkStyle === 'dotted') {
            // For dotted, use round caps - the dot size IS the lineWidth
            // Scale gap based on line width so dots stay visible when thick
            editor.ctx.lineCap = 'round';
            const dotSize = Math.max(linkWidth * 2, 4); // Bigger dots (minimum 4px)
            const dotGap = Math.max(linkWidth * 4 + 12, 16); // Gap scales with width (minimum 16px)
            editor.ctx.setLineDash([0.1, dotGap]); // Tiny dash with scaled gap
            editor.ctx.lineWidth = dotSize; // Dot diameter = lineWidth
        } else {
            editor.ctx.setLineDash([]); // Solid line
        }
        
        editor.ctx.stroke();
        
        // ENHANCED: Restore clipping context if we applied it for text gaps
        if (attachedTexts.length > 0) {
            editor.ctx.restore();
        }
        
        // Reset lineCap, lineJoin and lineWidth after any link style
            editor.ctx.lineCap = 'butt';
        editor.ctx.lineJoin = 'miter';
        if (linkStyle === 'dotted') {
            editor.ctx.lineWidth = linkWidth;
        }
        
        editor.ctx.shadowBlur = 0; // Reset shadow after drawing link
        editor.ctx.setLineDash([]); // Reset dash
        
        // CRITICAL: Calculate arrow position once and use for both drawing and hiding TP
        // This ensures arrow tip IS the TP (no separate dot)
        let arrowAtStart = false;
        let arrowAtEnd = false;
        let arrowX, arrowY, arrowAngle;
        let startArrowAngle; // For double-arrow
        
        // Clear arrow tip positions for non-arrow links (isArrowStyle already defined earlier)
        if (!isArrowStyle) {
            link._arrowTipStart = null;
            link._arrowTipEnd = null;
        }
        
        // ENHANCED: Always show arrows regardless of width - scale arrow size with link width
        if (isArrowStyle) {
            // Determine which endpoint is the free TP (where arrow should be)
            let isStartFree = true;
            let isEndFree = true;
            
            // Check if start is attached to device
            const startAttached = link.device1 !== null && link.device1 !== undefined;
            // Check if end is attached to device
            const endAttached = link.device2 !== null && link.device2 !== undefined;
            
            // Device-attached endpoints are NOT free (arrow should not point toward device)
            if (startAttached) isStartFree = false;
            if (endAttached) isEndFree = false;
            
            // Check merge status to determine free endpoints
            if (link.mergedWith) {
                // This is a parent link - MP endpoints are not free
                const parentFreeEnd = link.mergedWith.parentFreeEnd;
                isStartFree = (parentFreeEnd === 'start') && !startAttached;
                isEndFree = (parentFreeEnd === 'end') && !endAttached;
            }
            
            // CRITICAL: If also a child (middle link), MUST check parent connection too
            if (link.mergedInto) {
                // This is a child link
                const parentLink = editor.objects.find(o => o.id === link.mergedInto.parentId);
                if (parentLink && parentLink.mergedWith) {
                    const childFreeEnd = parentLink.mergedWith.childFreeEnd;
                    if (childFreeEnd !== 'start') isStartFree = false;
                    if (childFreeEnd !== 'end') isEndFree = false;
                }
            }
            
            // =========================================================================
            // ARROW TIP ALIGNMENT FOR UNBOUND LINKS - CRITICAL DOCUMENTATION (Dec 2025)
            // =========================================================================
            // Same geometry rules as drawLink() apply here. See documentation there.
            // - END arrow uses MINUS → points in endTangentAngle direction
            // - START arrow uses PLUS → points in (startTangentAngle + π) direction
            // Therefore: startTangentAngle must be TANGENT (direction of travel), not opposite!
            // =========================================================================
            let endTangentAngle, startTangentAngle;
            
                if (curveEnabled && (cp1x !== undefined && cp2x !== undefined)) {
                // Check if control points are at curve endpoints (no actual curve)
                const cp2AtEnd = Math.abs(endX - cp2x) < 0.1 && Math.abs(endY - cp2y) < 0.1;
                const cp1AtStart = Math.abs(startX - cp1x) < 0.1 && Math.abs(startY - cp1y) < 0.1;
                
                if (cp2AtEnd || cp1AtStart) {
                    // Control points at endpoints - effectively straight line
                    // Both angles = direction of travel
                    endTangentAngle = Math.atan2(endY - startY, endX - startX);
                    startTangentAngle = Math.atan2(endY - startY, endX - startX);
                } else {
                    // True curve - use Bezier tangent derivatives
                    endTangentAngle = Math.atan2(endY - cp2y, endX - cp2x);
                    // startTangentAngle: from curve start toward cp1
                    startTangentAngle = Math.atan2(cp1y - startY, cp1x - startX);
                }
                } else {
                // Straight lines: both angles = direction of travel
                // Use link.start/end directly for accurate direction during stretching
                endTangentAngle = Math.atan2(link.end.y - link.start.y, link.end.x - link.start.x);
                startTangentAngle = Math.atan2(link.end.y - link.start.y, link.end.x - link.start.x);
            }
            
            // Scale arrow size with link width (base 16px for width 2, scales proportionally)
            const arrowLength = 10 + (linkWidth * 3);
            const arrowAngleSpread = Math.PI / 5; // 36°
            
            // For double-arrow and dashed-double-arrow, draw at FREE endpoints only (TPs)
            // This ensures merged BULs only show arrow tips at TPs, not at MPs
            // CRITICAL: Arrow tips must be EXACTLY at link.start/end for free TPs
            // For device-attached: use device edge position (origEndX/Y)
            // For free TPs: use link.end directly to ensure tip is at exact TP position
            const isEndDeviceAttached = !!link.device2;
            const isStartDeviceAttached = !!link.device1;
            
            // For free TPs, ensure arrow tip is exactly at link.end (not origEndX which might have device edge calc)
            const arrowEndX = isEndDeviceAttached ? origEndX : link.end.x;
            const arrowEndY = isEndDeviceAttached ? origEndY : link.end.y;
            const arrowStartX = isStartDeviceAttached ? origStartX : link.start.x;
            const arrowStartY = isStartDeviceAttached ? origStartY : link.start.y;
            
            // Store arrow tip positions and geometry for hitbox detection
            link._arrowTipEnd = { x: arrowEndX, y: arrowEndY };
            link._arrowTipStart = { x: arrowStartX, y: arrowStartY };
            link._arrowLength = arrowLength;
            link._arrowAngleSpread = arrowAngleSpread;
            link._arrowEndAngle = endTangentAngle;
            link._arrowStartAngle = startTangentAngle;
            
            // Store arrow colors for deferred drawing pass (arrows drawn AFTER devices)
            link._arrowFillColor = isSelected ? selectionColor : linkColor;
            link._arrowStrokeColor = isSelected ? linkColor : '#333';
            link._arrowStrokeWidth = 1.5;
            
            if (linkStyle === 'double-arrow' || linkStyle === 'dashed-double-arrow') {
                if (isEndFree) arrowAtEnd = true;
                if (isStartFree) arrowAtStart = true;
            } else {
                if (isEndFree && !isStartFree) {
                    arrowAtEnd = true;
                } else if (isStartFree && !isEndFree) {
                    arrowAtStart = true;
                } else if (isStartFree && isEndFree) {
                    arrowAtEnd = true;
                }
            }
        }
        
        // Store which endpoints have arrows drawn (for hitbox detection)
        link._arrowAtStart = arrowAtStart;
        link._arrowAtEnd = arrowAtEnd;
        
        // Draw endpoints (circles) with visual distinction for attached endpoints
        // ENHANCED: Draw connection points for merged ULs as movable points
        // CRITICAL: If arrow style is used, don't draw TP circle at the arrow tip (arrow tip IS the TP)
        // ENHANCED: For dotted links, match TP size to the dot size
        let endpointRadius = isSelected ? 6 : 4;
        if (linkStyle === 'dotted') {
            // Match the dot size from line drawing: Math.max(linkWidth * 2, 4)
            const dotSize = Math.max(linkWidth * 2, 4);
            endpointRadius = dotSize / 2; // Radius is half the dot diameter
        }
        const isStretching = editor.stretchingLink === link;
        
        // Check if start endpoint is an MP (actual connection point where 2 TPs merged)
        // CRITICAL: Only the ACTUAL merge points should be MPs, not free endpoints!
        let startIsMP = false;
        
        // CRITICAL FIX: Middle links (have BOTH mergedInto AND mergedWith) have BOTH ends as MPs!
        if (link.mergedInto && link.mergedWith) {
            // This is a middle link in a chain - BOTH ends are MPs (neither is a free TP)
            startIsMP = true;
        }
        // Check if this is a parent link and start is the CONNECTED end (not the free end)
        else if (link.mergedWith && link.mergedWith.parentFreeEnd !== 'start') {
            startIsMP = true; // Start is where this link connects to its child (MP)
        }
        // Check if this is a child link and start is the CONNECTED end (not the free end)
        else if (link.mergedInto) {
            const parentLink = editor.objects.find(o => o.id === link.mergedInto.parentId);
            if (parentLink && parentLink.mergedWith) {
                const childFreeEnd = parentLink.mergedWith.childFreeEnd;
                if (childFreeEnd !== 'start') {
                    startIsMP = true; // Start is where this link connects to its parent (MP)
                }
            }
        }
        
        const startConnectedToUL = startIsMP;
        
        // Start endpoint - draw normally if NOT connected to another UL and NOT attached to device
        // CRITICAL: Skip drawing TP circle if arrow is at this endpoint OR if attached to device
        const startAttached = link.device1 !== null && link.device1 !== undefined;
        
        if (!startConnectedToUL && !arrowAtStart && !startAttached) {
        // Only draw TP if it's FREE (not attached to device, not merged)
        const startIsStretching = isStretching && editor.stretchingEndpoint === 'start';
        const startNearDevice = startIsStretching && editor._stretchingNearDevice;
        
        editor.ctx.beginPath();
        editor.ctx.arc(startX, startY, endpointRadius, 0, Math.PI * 2);
        // Orange/yellow when near device, blue for selected, gray for normal
        if (startNearDevice) {
            editor.ctx.fillStyle = '#FF7A33'; // Orange - ready to attach
        } else if (isSelected) {
            editor.ctx.fillStyle = '#3498db'; // Blue - selected
        } else {
            editor.ctx.fillStyle = '#666'; // Gray - normal
        }
        editor.ctx.fill();
        editor.ctx.strokeStyle = 'white';
        editor.ctx.lineWidth = 1;
        editor.ctx.stroke();
        
        // ENHANCED: Add TP numbering - POSITIONAL (TP-1 and TP-2 are current free ends)
        // For individual UL: show which endpoint (TP1=start, TP2=end)
        // For BUL: TP-1 and TP-2 are the 2 current free endpoints
        const allLinks = editor.getAllMergedLinks(link);
        const isBUL = allLinks.length > 1;
        
        if (isBUL) {
            // Find the 2 TPs in the BUL and number them positionally
            // TP-1 and TP-2 are the current free endpoints (can change as BUL grows)
            let tpNumber = 0;
            
            // Collect all TPs in the BUL with their link IDs
            // FIXED: Use clearer logic - endpoint is TP if NOT connected via mergedWith or mergedInto
            const tpsInBUL = [];
            for (const chainLink of allLinks) {
                // Check start - is it connected?
                let startIsConnected = false;
                // Via mergedWith: parentFreeEnd='end' means end is free, so start is connected
                if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'end') {
                    startIsConnected = true;
                }
                // Via mergedInto: childFreeEnd='end' means end is free, so start is connected
                if (chainLink.mergedInto) {
                    const parent = editor.objects.find(o => o.id === chainLink.mergedInto.parentId);
                    if (parent?.mergedWith && parent.mergedWith.childFreeEnd === 'end') {
                        startIsConnected = true;
                    }
                }
                if (!startIsConnected) {
                    tpsInBUL.push({ linkId: chainLink.id, endpoint: 'start', link: chainLink });
                }
                
                // Check end - is it connected?
                let endIsConnected = false;
                // Via mergedWith: parentFreeEnd='start' means start is free, so end is connected
                if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'start') {
                    endIsConnected = true;
                }
                // Via mergedInto: childFreeEnd='start' means start is free, so end is connected
                if (chainLink.mergedInto) {
                    const parent = editor.objects.find(o => o.id === chainLink.mergedInto.parentId);
                    if (parent?.mergedWith && parent.mergedWith.childFreeEnd === 'start') {
                        endIsConnected = true;
                    }
                }
                if (!endIsConnected) {
                    tpsInBUL.push({ linkId: chainLink.id, endpoint: 'end', link: chainLink });
                }
            }
            
            // FIXED: Sort TPs by UL number so TP-1 is always on lowest UL, TP-2 on highest
            tpsInBUL.sort((a, b) => {
                const ulNumA = parseInt(a.linkId.split('_')[1]) || 0;
                const ulNumB = parseInt(b.linkId.split('_')[1]) || 0;
                return ulNumA - ulNumB;
            });
            
            // Number TPs: TP-1 on lowest UL number, TP-2 on highest UL number
            // CRITICAL: Find index based on BOTH linkId AND endpoint
            const tpIndex = tpsInBUL.findIndex(tp => tp.linkId === link.id && tp.endpoint === 'start');
            tpNumber = (tpIndex >= 0) ? tpIndex + 1 : 0;
            
            // VALIDATION: If tpNumber is 0, this TP wasn't found in the list (BUG!)
            if (tpNumber === 0 && editor.debugger) {
                editor.debugger.logError(`❌ TP not found in BUL list! Link: ${link.id}, endpoint: start`);
                editor.debugger.logInfo(`   TPs in BUL: ${JSON.stringify(tpsInBUL.map(tp => ({id: tp.linkId, ep: tp.endpoint})))}`);
            }
            
            // Draw TP number with UL identification
            const ulNumber = allLinks.findIndex(l => l.id === link.id) + 1;
            editor.ctx.save();
            editor.ctx.font = `bold ${8 / editor.zoom}px Arial`;
            editor.ctx.fillStyle = 'white';
            editor.ctx.textAlign = 'center';
            editor.ctx.textBaseline = 'middle';
            editor.ctx.fillText(`${tpNumber}`, startX, startY);
            // Show which UL this TP belongs to
            editor.ctx.font = `${6 / editor.zoom}px Arial`;
            editor.ctx.fillText(`U${ulNumber}`, startX, startY + 10 / editor.zoom);
            editor.ctx.restore();
        } else {
            // Individual UL - show which endpoint (1=start, 2=end)
            editor.ctx.save();
            editor.ctx.font = `bold ${7 / editor.zoom}px Arial`;
            editor.ctx.fillStyle = 'white';
            editor.ctx.textAlign = 'center';
            editor.ctx.textBaseline = 'middle';
            editor.ctx.fillText('1', startX, startY);
            editor.ctx.restore();
        }
        }
        
        // Check if end endpoint is an MP (actual connection point where 2 TPs merged)
        // CRITICAL: Only the ACTUAL merge points should be MPs, not free endpoints!
        let endIsMP = false;
        
        // CRITICAL FIX: Middle links (have BOTH mergedInto AND mergedWith) have BOTH ends as MPs!
        if (link.mergedInto && link.mergedWith) {
            // This is a middle link in a chain - BOTH ends are MPs (neither is a free TP)
            endIsMP = true;
        }
        // Check if this is a parent link and end is the CONNECTED end (not the free end)
        else if (link.mergedWith && link.mergedWith.parentFreeEnd !== 'end') {
            endIsMP = true; // End is where this link connects to its child (MP)
        }
        // Check if this is a child link and end is the CONNECTED end (not the free end)
        else if (link.mergedInto) {
            const parentLink = editor.objects.find(o => o.id === link.mergedInto.parentId);
            if (parentLink && parentLink.mergedWith) {
                const childFreeEnd = parentLink.mergedWith.childFreeEnd;
                if (childFreeEnd !== 'end') {
                    endIsMP = true; // End is where this link connects to its parent (MP)
                }
            }
        }
        
        const endConnectedToUL = endIsMP;
        
        // End endpoint - draw normally if NOT connected to another UL and NOT attached to device
        // CRITICAL: Skip drawing TP circle if arrow is at this endpoint OR if attached to device
        const endAttached = link.device2 !== null && link.device2 !== undefined;
        
        if (!endConnectedToUL && !arrowAtEnd && !endAttached) {
        // Only draw TP if it's FREE (not attached to device, not merged)
        const endIsStretching = isStretching && editor.stretchingEndpoint === 'end';
        const endNearDevice = endIsStretching && editor._stretchingNearDevice;
        
        editor.ctx.beginPath();
        editor.ctx.arc(endX, endY, endpointRadius, 0, Math.PI * 2);
        // Orange/yellow when near device, blue for selected, gray for normal
        if (endNearDevice) {
            editor.ctx.fillStyle = '#FF7A33'; // Orange - ready to attach
        } else if (isSelected) {
            editor.ctx.fillStyle = '#3498db'; // Blue - selected
        } else {
            editor.ctx.fillStyle = '#666'; // Gray - normal
        }
        editor.ctx.fill();
        editor.ctx.strokeStyle = 'white';
        editor.ctx.lineWidth = 1;
        editor.ctx.stroke();
        
        // ENHANCED: Add TP numbering - POSITIONAL (TP-1 and TP-2 are current free ends)
        const allLinks = editor.getAllMergedLinks(link);
        const isBUL = allLinks.length > 1;
        
        if (isBUL) {
            // Find the 2 TPs in the BUL and number them positionally
            let tpNumber = 0;
            
            // Collect all TPs in the BUL
            // FIXED: Use clearer logic - endpoint is TP if NOT connected via mergedWith or mergedInto
            const tpsInBUL = [];
            for (const chainLink of allLinks) {
                // Check start - is it connected?
                let startIsConnected = false;
                if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'end') {
                    startIsConnected = true;
                }
                if (chainLink.mergedInto) {
                    const parent = editor.objects.find(o => o.id === chainLink.mergedInto.parentId);
                    if (parent?.mergedWith && parent.mergedWith.childFreeEnd === 'end') {
                        startIsConnected = true;
                    }
                }
                if (!startIsConnected) {
                    tpsInBUL.push({ linkId: chainLink.id, endpoint: 'start', link: chainLink });
                }
                
                // Check end - is it connected?
                let endIsConnected = false;
                if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'start') {
                    endIsConnected = true;
                }
                if (chainLink.mergedInto) {
                    const parent = editor.objects.find(o => o.id === chainLink.mergedInto.parentId);
                    if (parent?.mergedWith && parent.mergedWith.childFreeEnd === 'start') {
                        endIsConnected = true;
                    }
                }
                if (!endIsConnected) {
                    tpsInBUL.push({ linkId: chainLink.id, endpoint: 'end', link: chainLink });
                }
            }
            
            // FIXED: Sort TPs by UL number so TP-1 is always on lowest UL, TP-2 on highest
            tpsInBUL.sort((a, b) => {
                const ulNumA = parseInt(a.linkId.split('_')[1]) || 0;
                const ulNumB = parseInt(b.linkId.split('_')[1]) || 0;
                return ulNumA - ulNumB;
            });
            
            // Number TPs: TP-1 on lowest UL number, TP-2 on highest UL number
            // CRITICAL: Find index based on BOTH linkId AND endpoint
            const tpIndex = tpsInBUL.findIndex(tp => tp.linkId === link.id && tp.endpoint === 'end');
            tpNumber = (tpIndex >= 0) ? tpIndex + 1 : 0;
            
            // VALIDATION: If tpNumber is 0, this TP wasn't found in the list (BUG!)
            if (tpNumber === 0 && editor.debugger) {
                editor.debugger.logError(`❌ TP not found in BUL list! Link: ${link.id}, endpoint: end`);
                editor.debugger.logInfo(`   TPs in BUL: ${JSON.stringify(tpsInBUL.map(tp => ({id: tp.linkId, ep: tp.endpoint})))}`);
            }
            
            // Draw TP number with UL identification
            const ulNumber = allLinks.findIndex(l => l.id === link.id) + 1;
            editor.ctx.save();
            editor.ctx.font = `bold ${8 / editor.zoom}px Arial`;
            editor.ctx.fillStyle = 'white';
            editor.ctx.textAlign = 'center';
            editor.ctx.textBaseline = 'middle';
            editor.ctx.fillText(`${tpNumber}`, endX, endY);
            // Show which UL this TP belongs to
            editor.ctx.font = `${6 / editor.zoom}px Arial`;
            editor.ctx.fillText(`U${ulNumber}`, endX, endY + 10 / editor.zoom);
            editor.ctx.restore();
        } else {
            // Individual UL - show which endpoint (1=start, 2=end)
            editor.ctx.save();
            editor.ctx.font = `bold ${7 / editor.zoom}px Arial`;
            editor.ctx.fillStyle = 'white';
            editor.ctx.textAlign = 'center';
            editor.ctx.textBaseline = 'middle';
            editor.ctx.fillText('2', endX, endY);
            editor.ctx.restore();
        }
        }
        
        // ENHANCED: Draw MPs (merge points) - small purple dots showing where ULs connect
        // BUL chain structure: TP--MP--MP--MP--TP (2 TPs at ends, N-1 MPs for N links)
        // Show MPs when link type labels are ON OR when curveMPs is enabled
        const showMPIndicators = editor.showLinkTypeLabels || editor.curveMPs;
        
        // Draw MP at start if it's a merge point (NOT attached to device, NOT arrow tip)
        if (startIsMP && !startAttached && !arrowAtStart && showMPIndicators) {
            // Calculate MP position - use curve if curveMPs is enabled
            let mpStartX = startX;
            let mpStartY = startY;
            
            if (editor.curveMPs && curveEnabled && link._cp1 && link._cp2) {
                // ENHANCED: Position MP along the actual bezier curve path
                // Sample a small distance along the curve from the start point
                // This makes the MP visually connect with the curve, not the straight line
                const t = 0.05; // Sample at 5% along the curve
                mpStartX = Math.pow(1-t, 3) * startX + 
                           3 * Math.pow(1-t, 2) * t * link._cp1.x + 
                           3 * (1-t) * Math.pow(t, 2) * link._cp2.x + 
                           Math.pow(t, 3) * endX;
                mpStartY = Math.pow(1-t, 3) * startY + 
                           3 * Math.pow(1-t, 2) * t * link._cp1.y + 
                           3 * (1-t) * Math.pow(t, 2) * link._cp2.y + 
                           Math.pow(t, 3) * endY;
            }
            
            const mpRadius = isSelected ? 5 / editor.zoom : 4 / editor.zoom; // Slightly bigger when selected
            editor.ctx.beginPath();
            editor.ctx.arc(mpStartX, mpStartY, mpRadius, 0, Math.PI * 2);
            editor.ctx.fillStyle = isSelected ? '#5599FF' : '#0066FA'; // DriveNets blue - brighter when selected
            editor.ctx.fill();
            editor.ctx.strokeStyle = isSelected ? '#0052CC' : '#003D99'; // Darker blue outline
            editor.ctx.lineWidth = 2 / editor.zoom;
            editor.ctx.stroke();
            
            // ENHANCED: Add MP numbering based on CREATION ORDER
            // MPs are numbered by when they were created (MP-1, MP-2, MP-3...)
            const allLinks = editor.getAllMergedLinks(link);
            if (allLinks.length > 1) {
                let mpNumber = 0;
                
                // Find which MP this is (at link's start)
                // Check if this link is the parent (mergedWith) and start is the connected end
                if (link.mergedWith) {
                    const parentConnectedEnd = link.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start';
                    if (parentConnectedEnd === 'start') {
                        // This MP is at this link's start
                        mpNumber = link.mergedWith.mpNumber || 0;
                    }
                }
                // Check if this link is a child (mergedInto) and start is where it connects
                if (link.mergedInto && mpNumber === 0) { // Only if not already found as parent
                    const parent = editor.objects.find(o => o.id === link.mergedInto.parentId);
                    if (parent?.mergedWith) {
                        const childConnectedEnd = parent.mergedWith.childConnectionEndpoint ||
                            (parent.mergedWith.childFreeEnd === 'start' ? 'end' : 'start');
                        if (childConnectedEnd === 'start') {
                            // This MP is at this link's start
                            mpNumber = parent.mergedWith.mpNumber || 0;
                        }
                    }
                }
                
                // Draw MP number with connected UL information
                const ulNumber = allLinks.findIndex(l => l.id === link.id) + 1;
                editor.ctx.save();
                editor.ctx.font = `bold ${7 / editor.zoom}px Arial`;
                editor.ctx.fillStyle = 'white';
                editor.ctx.textAlign = 'center';
                editor.ctx.textBaseline = 'middle';
                editor.ctx.fillText(`${mpNumber}`, mpStartX, mpStartY);
                // Show which UL this MP is on
                editor.ctx.font = `${6 / editor.zoom}px Arial`;
                editor.ctx.fillText(`U${ulNumber}`, mpStartX, mpStartY + 10 / editor.zoom);
                editor.ctx.restore();
            }
        }
        
        // Draw MP at end if it's a merge point (NOT attached to device, NOT arrow tip)
        // Show MPs when link type labels are ON OR when curveMPs is enabled
        if (endIsMP && !endAttached && !arrowAtEnd && showMPIndicators) {
            // Calculate MP position - use curve if curveMPs is enabled
            let mpEndX = endX;
            let mpEndY = endY;
            
            if (editor.curveMPs && curveEnabled && link._cp1 && link._cp2) {
                // ENHANCED: Position MP along the actual bezier curve path
                // Sample a small distance along the curve from the end point
                // This makes the MP visually connect with the curve, not the straight line
                const t = 0.95; // Sample at 95% along the curve (near the end)
                mpEndX = Math.pow(1-t, 3) * startX + 
                         3 * Math.pow(1-t, 2) * t * link._cp1.x + 
                         3 * (1-t) * Math.pow(t, 2) * link._cp2.x + 
                         Math.pow(t, 3) * endX;
                mpEndY = Math.pow(1-t, 3) * startY + 
                         3 * Math.pow(1-t, 2) * t * link._cp1.y + 
                         3 * (1-t) * Math.pow(t, 2) * link._cp2.y + 
                         Math.pow(t, 3) * endY;
            }
            
            const mpRadius = isSelected ? 5 / editor.zoom : 4 / editor.zoom; // Slightly bigger when selected
            editor.ctx.beginPath();
            editor.ctx.arc(mpEndX, mpEndY, mpRadius, 0, Math.PI * 2);
            editor.ctx.fillStyle = isSelected ? '#5599FF' : '#0066FA'; // DriveNets blue - brighter when selected
            editor.ctx.fill();
            editor.ctx.strokeStyle = isSelected ? '#0052CC' : '#003D99'; // Darker blue outline
            editor.ctx.lineWidth = 2 / editor.zoom;
            editor.ctx.stroke();
            
            // ENHANCED: Add MP numbering based on CREATION ORDER
            // MPs are numbered by when they were created (MP-1, MP-2, MP-3...)
            const allLinks = editor.getAllMergedLinks(link);
            if (allLinks.length > 1) {
                let mpNumber = 0;
                
                // Find which MP this is (at link's end)
                // Check if this link is the parent (mergedWith) and end is the connected end
                if (link.mergedWith) {
                    const parentConnectedEnd = link.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start';
                    if (parentConnectedEnd === 'end') {
                        // This MP is at this link's end
                        mpNumber = link.mergedWith.mpNumber || 0;
                    }
                }
                // Check if this link is a child (mergedInto) and end is where it connects
                if (link.mergedInto && mpNumber === 0) { // Only if not already found as parent
                    const parent = editor.objects.find(o => o.id === link.mergedInto.parentId);
                    if (parent?.mergedWith) {
                        const childConnectedEnd = parent.mergedWith.childConnectionEndpoint ||
                            (parent.mergedWith.childFreeEnd === 'start' ? 'end' : 'start');
                        if (childConnectedEnd === 'end') {
                            // This MP is at this link's end
                            mpNumber = parent.mergedWith.mpNumber || 0;
                        }
                    }
                }
                
                // Draw MP number with connected UL information
                const ulNumber = allLinks.findIndex(l => l.id === link.id) + 1;
                editor.ctx.save();
                editor.ctx.font = `bold ${7 / editor.zoom}px Arial`;
                editor.ctx.fillStyle = 'white';
                editor.ctx.textAlign = 'center';
                editor.ctx.textBaseline = 'middle';
                editor.ctx.fillText(`${mpNumber}`, mpEndX, mpEndY);
                // Show which UL this MP is on
                editor.ctx.font = `${6 / editor.zoom}px Arial`;
                editor.ctx.fillText(`U${ulNumber}`, mpEndX, mpEndY + 10 / editor.zoom);
                editor.ctx.restore();
            }
        }
        
        // Draw visual feedback: highlight nearby device when stretching
        // Shape matches the device's visual style
        if (isStretching && editor._stretchingNearDevice) {
            const device = editor._stretchingNearDevice;
            const style = device.visualStyle || 'circle';
            const r = device.radius;
            const pad = 8;
            const rotation = (device.rotation || 0) * Math.PI / 180;
            
            editor.ctx.strokeStyle = '#FF7A33';
            editor.ctx.lineWidth = 2;
            editor.ctx.setLineDash([4, 4]);
            
            editor.ctx.beginPath();
            switch (style) {
                case 'classic': {
                    const halfW = r * 0.8 + pad;
                    const top = r * -0.4 - pad;
                    const bottom = r * 0.6 + pad;
                    editor.ctx.save();
                    editor.ctx.translate(device.x, device.y);
                    editor.ctx.rotate(rotation);
                    editor.ctx.roundRect(-halfW, top, halfW * 2, bottom - top, 4);
                    editor.ctx.restore();
                    break;
                }
                case 'server': {
                    const halfW = r * 0.59 + pad;
                    const halfH = r * 0.9 + pad;
                    editor.ctx.save();
                    editor.ctx.translate(device.x, device.y);
                    editor.ctx.rotate(rotation);
                    editor.ctx.roundRect(-halfW, -halfH, halfW * 2, halfH * 2, 4);
                    editor.ctx.restore();
                    break;
                }
                case 'hex': {
                    const hexR = r * 0.65 + pad;
                    editor.ctx.save();
                    editor.ctx.translate(device.x, device.y);
                    editor.ctx.rotate(rotation);
                    const pts = [];
                    for (let i = 0; i < 6; i++) {
                        const a = (Math.PI / 6) + (i * Math.PI / 3);
                        pts.push({ x: Math.cos(a) * hexR, y: Math.sin(a) * hexR });
                    }
                    editor.ctx.moveTo(pts[0].x, pts[0].y);
                    for (let i = 1; i < 6; i++) editor.ctx.lineTo(pts[i].x, pts[i].y);
                    editor.ctx.closePath();
                    editor.ctx.restore();
                    break;
                }
                case 'circle':
                case 'simple':
                default:
                    editor.ctx.arc(device.x, device.y, r + pad, 0, Math.PI * 2);
                    break;
            }
            editor.ctx.stroke();
            editor.ctx.setLineDash([]);
            
            // Draw connection preview line
            const previewEndpoint = editor.stretchingEndpoint === 'start' 
                ? { x: startX, y: startY }
                : { x: endX, y: endY };
            editor.ctx.beginPath();
            editor.ctx.moveTo(device.x, device.y);
            editor.ctx.lineTo(previewEndpoint.x, previewEndpoint.y);
            editor.ctx.strokeStyle = 'rgba(255, 94, 31, 0.4)';
            editor.ctx.lineWidth = 2;
            editor.ctx.setLineDash([3, 3]);
            editor.ctx.stroke();
            editor.ctx.setLineDash([]);
        }
        
        // Selection highlight
        if (isSelected) {
            editor.ctx.strokeStyle = '#3498db';
            editor.ctx.lineWidth = 1;
            editor.ctx.setLineDash([3, 3]);
            editor.ctx.beginPath();
            editor.ctx.moveTo(startX, startY);
            if (curveEnabled && cp1x !== undefined) {
                editor.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, endX, endY);
            } else {
            editor.ctx.lineTo(endX, endY);
            }
            editor.ctx.stroke();
            editor.ctx.setLineDash([]);
        }
        
        // DEBUG VIEW: Draw link type label above UL/BUL
        if (editor.showLinkTypeLabels) {
            const midX = (startX + endX) / 2;
            const midY = (startY + endY) / 2;
            
            editor.ctx.save();
            editor.ctx.font = `bold ${11 / editor.zoom}px Arial`;
            editor.ctx.textAlign = 'center';
            editor.ctx.textBaseline = 'bottom';
            
            // ENHANCED: Show origin type + creation order in BUL
            const originType = link.originType || 'UL'; // Preserve original type
            let label = originType; // Base label
            let bgColor = 'rgba(52, 152, 219, 0.9)'; // Blue background (single UL)
            let strokeColor = '#2980b9';
            
            // Add merge status and creation order
            if (link.mergedWith || link.mergedInto) {
                // Get all links in the BUL chain
                const allMergedLinks = editor.getAllMergedLinks(link);
                
                // Sort by creation time to determine order
                const sortedByCreation = allMergedLinks.sort((a, b) => {
                    const aTime = a.createdAt || 0;
                    const bTime = b.createdAt || 0;
                    return aTime - bTime;
                });
                
                // Find this link's position in creation order
                const creationOrder = sortedByCreation.findIndex(l => l.id === link.id) + 1;
                
                // Show origin type + creation order number
                label = `${originType}${creationOrder}`;
                bgColor = 'rgba(0, 180, 216, 0.9)'; // Cyan background (indicates part of BUL)
                strokeColor = '#0891B2';
            }
            
            const padding = 3 / editor.zoom;
            const metrics = editor.ctx.measureText(label);
            const textWidth = metrics.width;
            const textHeight = 11 / editor.zoom;
            
            // Draw background
            editor.ctx.fillStyle = bgColor;
            editor.ctx.fillRect(
                midX - textWidth / 2 - padding,
                midY - 18 / editor.zoom - textHeight - padding,
                textWidth + padding * 2,
                textHeight + padding * 2
            );
            
            // Draw label text
            editor.ctx.fillStyle = 'white';
            editor.ctx.strokeStyle = strokeColor;
            editor.ctx.lineWidth = 0.5 / editor.zoom;
            editor.ctx.strokeText(label, midX, midY - 18 / editor.zoom);
            editor.ctx.fillText(label, midX, midY - 18 / editor.zoom);
            
            editor.ctx.restore();
        }
        
        // Draw GROUP indicator if link belongs to a group
        if (link.groupId) {
            const midX = (startX + endX) / 2;
            const midY = (startY + endY) / 2;
            const dotSize = 5 / editor.zoom;
            
            // Small purple dot at midpoint of link
            editor.ctx.beginPath();
            editor.ctx.arc(midX, midY + 12 / editor.zoom, dotSize, 0, Math.PI * 2);
            const groupGradient = editor.ctx.createRadialGradient(
                midX, midY + 12 / editor.zoom, 0, 
                midX, midY + 12 / editor.zoom, dotSize
            );
            groupGradient.addColorStop(0, 'rgba(155, 89, 182, 0.95)');
            groupGradient.addColorStop(1, 'rgba(142, 68, 173, 0.95)');
            editor.ctx.fillStyle = groupGradient;
            editor.ctx.fill();
            
            editor.ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
            editor.ctx.lineWidth = 1 / editor.zoom;
            editor.ctx.stroke();
        }

    },

    drawLinkArrows(editor, link) {
        if (!link._arrowAtEnd && !link._arrowAtStart) return;
        if (!link._arrowTipEnd && !link._arrowTipStart) return;
        
        const len = link._arrowLength;
        const spread = link._arrowAngleSpread;
        const fillColor = link._arrowFillColor;
        const strokeColor = link._arrowStrokeColor;
        const strokeWidth = link._arrowStrokeWidth || 1;
        if (!len || !spread) return;
        
        if (link._arrowAtEnd && link._arrowTipEnd) {
            const tip = link._arrowTipEnd;
            const angle = link._arrowEndAngle;
            editor.ctx.beginPath();
            editor.ctx.moveTo(tip.x, tip.y);
            editor.ctx.lineTo(tip.x - len * Math.cos(angle - spread), tip.y - len * Math.sin(angle - spread));
            editor.ctx.lineTo(tip.x - len * Math.cos(angle + spread), tip.y - len * Math.sin(angle + spread));
            editor.ctx.closePath();
            editor.ctx.fillStyle = fillColor;
            editor.ctx.fill();
            editor.ctx.strokeStyle = strokeColor;
            editor.ctx.lineWidth = strokeWidth;
            editor.ctx.stroke();
        }
        
        if (link._arrowAtStart && link._arrowTipStart) {
            const tip = link._arrowTipStart;
            const angle = link._arrowStartAngle;
            editor.ctx.beginPath();
            editor.ctx.moveTo(tip.x, tip.y);
            editor.ctx.lineTo(tip.x + len * Math.cos(angle - spread), tip.y + len * Math.sin(angle - spread));
            editor.ctx.lineTo(tip.x + len * Math.cos(angle + spread), tip.y + len * Math.sin(angle + spread));
            editor.ctx.closePath();
            editor.ctx.fillStyle = fillColor;
            editor.ctx.fill();
            editor.ctx.strokeStyle = strokeColor;
            editor.ctx.lineWidth = strokeWidth;
            editor.ctx.stroke();
        }
    },
};

console.log('[topology-link-drawing.js] LinkDrawing loaded');
