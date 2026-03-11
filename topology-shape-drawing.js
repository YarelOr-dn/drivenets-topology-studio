/**
 * topology-shape-drawing.js - Shape Drawing Module
 * Contains: drawShape, drawShapeSelectionHandles
 */

'use strict';

window.ShapeDrawing = {
    drawShape(editor, shape) {
        if (!shape || shape.type !== 'shape') return;
        
        const ctx = editor.ctx;
        const x = shape.x;
        const y = shape.y;
        const w = shape.width;
        const h = shape.height;
        
        ctx.save();
        
        // Apply rotation
        if (shape.rotation) {
            ctx.translate(x, y);
            ctx.rotate(shape.rotation * Math.PI / 180);
            ctx.translate(-x, -y);
        }
        
        // Calculate fill color with opacity
        // fillOpacity is stored as 0-1 (e.g., 0.5 = 50%)
        let fillColor = 'transparent';
        if (shape.fillEnabled !== false) {
            const opacity = shape.fillOpacity !== undefined ? shape.fillOpacity : 0.5;
            fillColor = editor.hexToRgba(shape.fillColor || '#3498db', opacity);
        }
        
        // Stroke settings
        const strokeEnabled = shape.strokeEnabled !== false;
        const strokeColor = shape.strokeColor || '#3498db';
        const strokeWidth = shape.strokeWidth || 2;
        
        ctx.fillStyle = fillColor;
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = strokeWidth;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        
        // Draw based on shape type
        // Corner radius: use shape's cornerRadius if set, or calculate based on size
        const cornerRadius = shape.cornerRadius !== undefined 
            ? shape.cornerRadius 
            : Math.min(w, h) * 0.15; // Default: 15% of smaller dimension (nice rounded look)
        
        switch (shape.shapeType) {
            case 'rectangle':
                ctx.beginPath();
                ctx.roundRect(x - w/2, y - h/2, w, h, cornerRadius);
                if (shape.fillEnabled !== false) ctx.fill();
                if (strokeEnabled) ctx.stroke();
                break;
                
            case 'circle':
                ctx.beginPath();
                ctx.arc(x, y, w/2, 0, Math.PI * 2);
                if (shape.fillEnabled !== false) ctx.fill();
                if (strokeEnabled) ctx.stroke();
                break;
                
            case 'ellipse':
                ctx.beginPath();
                ctx.ellipse(x, y, w/2, h/2, 0, 0, Math.PI * 2);
                if (shape.fillEnabled !== false) ctx.fill();
                if (strokeEnabled) ctx.stroke();
                break;
                
            case 'triangle':
                ctx.beginPath();
                ctx.moveTo(x, y - h/2);
                ctx.lineTo(x + w/2, y + h/2);
                ctx.lineTo(x - w/2, y + h/2);
                ctx.closePath();
                if (shape.fillEnabled !== false) ctx.fill();
                if (strokeEnabled) ctx.stroke();
                break;
                
            case 'diamond':
                ctx.beginPath();
                ctx.moveTo(x, y - h/2);
                ctx.lineTo(x + w/2, y);
                ctx.lineTo(x, y + h/2);
                ctx.lineTo(x - w/2, y);
                ctx.closePath();
                if (shape.fillEnabled !== false) ctx.fill();
                if (strokeEnabled) ctx.stroke();
                break;
                
            case 'hexagon':
                ctx.beginPath();
                for (let i = 0; i < 6; i++) {
                    const angle = (i * 60 - 90) * Math.PI / 180;
                    const px = x + (w/2) * Math.cos(angle);
                    const py = y + (h/2) * Math.sin(angle);
                    if (i === 0) ctx.moveTo(px, py);
                    else ctx.lineTo(px, py);
                }
                ctx.closePath();
                if (shape.fillEnabled !== false) ctx.fill();
                if (strokeEnabled) ctx.stroke();
                break;
                
            case 'star':
                ctx.beginPath();
                for (let i = 0; i < 10; i++) {
                    const radius = i % 2 === 0 ? w/2 : w/4;
                    const angle = (i * 36 - 90) * Math.PI / 180;
                    const px = x + radius * Math.cos(angle);
                    const py = y + radius * Math.sin(angle);
                    if (i === 0) ctx.moveTo(px, py);
                    else ctx.lineTo(px, py);
                }
                ctx.closePath();
                if (shape.fillEnabled !== false) ctx.fill();
                if (strokeEnabled) ctx.stroke();
                break;
                
            case 'checkmark':
                ctx.beginPath();
                ctx.moveTo(x - w/3, y);
                ctx.lineTo(x - w/10, y + h/3);
                ctx.lineTo(x + w/3, y - h/3);
                ctx.lineWidth = strokeWidth + 1;
                if (strokeEnabled) ctx.stroke();
                break;
                
            case 'cross':
                ctx.beginPath();
                ctx.moveTo(x - w/3, y - h/3);
                ctx.lineTo(x + w/3, y + h/3);
                ctx.moveTo(x + w/3, y - h/3);
                ctx.lineTo(x - w/3, y + h/3);
                ctx.lineWidth = strokeWidth + 1;
                if (strokeEnabled) ctx.stroke();
                break;
                
            case 'arrow':
                ctx.beginPath();
                // Arrow body
                ctx.moveTo(x - w/2, y);
                ctx.lineTo(x + w/4, y);
                // Arrow head
                ctx.moveTo(x + w/4 - h/2, y - h/2);
                ctx.lineTo(x + w/2, y);
                ctx.lineTo(x + w/4 - h/2, y + h/2);
                ctx.lineWidth = strokeWidth + 1;
                if (strokeEnabled) ctx.stroke();
                break;
                
            case 'line':
                ctx.beginPath();
                ctx.moveTo(x - w/2, y);
                ctx.lineTo(x + w/2, y);
                if (strokeEnabled) ctx.stroke();
                break;
                
            case 'cloud':
                // Fluffy cloud with multiple rounded bumps - iconic cloud shape
                ctx.beginPath();
                
                // Cloud dimensions - wider and fluffier
                const cloudW = w * 0.5;
                const cloudH = h * 0.45;
                const baseY = y + cloudH * 0.3;  // Slightly lower base
                
                // Start from bottom left corner
                ctx.moveTo(x - cloudW * 0.85, baseY);
                
                // Left small bump
                ctx.bezierCurveTo(
                    x - cloudW * 1.0, baseY - cloudH * 0.1,
                    x - cloudW * 1.05, baseY - cloudH * 0.5,
                    x - cloudW * 0.8, baseY - cloudH * 0.65
                );
                
                // Left medium bump
                ctx.bezierCurveTo(
                    x - cloudW * 0.7, baseY - cloudH * 0.9,
                    x - cloudW * 0.45, baseY - cloudH * 1.0,
                    x - cloudW * 0.25, baseY - cloudH * 0.85
                );
                
                // Center-left tall bump
                ctx.bezierCurveTo(
                    x - cloudW * 0.1, baseY - cloudH * 1.15,
                    x + cloudW * 0.15, baseY - cloudH * 1.2,
                    x + cloudW * 0.3, baseY - cloudH * 0.95
                );
                
                // Center-right tallest bump (the main fluffy top)
                ctx.bezierCurveTo(
                    x + cloudW * 0.45, baseY - cloudH * 1.25,
                    x + cloudW * 0.7, baseY - cloudH * 1.15,
                    x + cloudW * 0.8, baseY - cloudH * 0.75
                );
                
                // Right small bump
                ctx.bezierCurveTo(
                    x + cloudW * 0.95, baseY - cloudH * 0.55,
                    x + cloudW * 1.0, baseY - cloudH * 0.2,
                    x + cloudW * 0.85, baseY
                );
                
                // Flat-ish bottom with slight curve
                ctx.bezierCurveTo(
                    x + cloudW * 0.5, baseY + cloudH * 0.1,
                    x - cloudW * 0.5, baseY + cloudH * 0.1,
                    x - cloudW * 0.85, baseY
                );
                
                ctx.closePath();
                
                if (shape.fillEnabled !== false) ctx.fill();
                if (strokeEnabled) ctx.stroke();
                break;
        }
        
        ctx.restore();
        
        // Draw selection visuals
        const isShapeSelected = editor.selectedObject === shape || editor.selectedObjects.includes(shape);
        const isSingleSelect = editor.selectedObject === shape && (!editor.selectedObjects || editor.selectedObjects.length <= 1);
        if (isSingleSelect) {
            editor.drawShapeSelectionHandles(shape);
        } else if (isShapeSelected && editor.selectedObjects && editor.selectedObjects.length > 1) {
            // Multi-select: dashed outline only, no handles
            const rotation = shape.rotation || 0;
            const outlineOffset = 4;
            ctx.save();
            ctx.translate(shape.x, shape.y);
            ctx.rotate(rotation * Math.PI / 180);
            ctx.translate(-shape.x, -shape.y);
            ctx.strokeStyle = 'rgba(52, 152, 219, 0.7)';
            ctx.lineWidth = 2;
            ctx.setLineDash([6, 4]);
            if (shape.shapeType === 'circle') {
                ctx.beginPath();
                ctx.arc(shape.x, shape.y, (shape.width || 50)/2 + outlineOffset, 0, Math.PI * 2);
                ctx.stroke();
            } else if (shape.shapeType === 'ellipse' || shape.shapeType === 'cloud') {
                ctx.beginPath();
                ctx.ellipse(shape.x, shape.y, (shape.width || 50)/2 + outlineOffset, (shape.height || 50)/2 + outlineOffset, 0, 0, Math.PI * 2);
                ctx.stroke();
            } else if (shape.shapeType === 'diamond') {
                ctx.beginPath();
                ctx.moveTo(shape.x, shape.y - (shape.height || 50)/2 - outlineOffset);
                ctx.lineTo(shape.x + (shape.width || 50)/2 + outlineOffset, shape.y);
                ctx.lineTo(shape.x, shape.y + (shape.height || 50)/2 + outlineOffset);
                ctx.lineTo(shape.x - (shape.width || 50)/2 - outlineOffset, shape.y);
                ctx.closePath();
                ctx.stroke();
            } else {
                const w = shape.width || 50, h = shape.height || 50;
                ctx.strokeRect(shape.x - w/2 - outlineOffset, shape.y - h/2 - outlineOffset, w + outlineOffset*2, h + outlineOffset*2);
            }
            ctx.setLineDash([]);
            ctx.restore();
        }
        if (editor.showLinkTypeLabels || (isShapeSelected && (shape.locked || shape.mergedToBackground))) {
            const iconScale = 1 / editor.zoom;
            const iconSize = 12 * iconScale;
            const shapeTop = shape.y - (shape.height || 50) / 2;
            
            // If merged to background, show grid overlay icon (green)
            if (shape.mergedToBackground) {
                ctx.save();
                ctx.translate(shape.x, shapeTop - 10 * iconScale);
                
                // Background circle - green for merged
                ctx.beginPath();
                ctx.arc(0, 0, iconSize * 0.65, 0, Math.PI * 2);
                const mergedGradient = ctx.createRadialGradient(0, 0, 0, 0, 0, iconSize * 0.65);
                mergedGradient.addColorStop(0, 'rgba(46, 204, 113, 0.95)');
                mergedGradient.addColorStop(1, 'rgba(39, 174, 96, 0.95)');
                ctx.fillStyle = mergedGradient;
                ctx.fill();
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.7)';
                ctx.lineWidth = 1 * iconScale;
                ctx.stroke();
                
                // Draw grid pattern in white
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = iconSize * 0.05;
                const gridSize = iconSize * 0.55;
                
                // Horizontal lines
                ctx.beginPath();
                ctx.moveTo(-gridSize/2, -gridSize/4);
                ctx.lineTo(gridSize/2, -gridSize/4);
                ctx.moveTo(-gridSize/2, gridSize/4);
                ctx.lineTo(gridSize/2, gridSize/4);
                
                // Vertical lines
                ctx.moveTo(-gridSize/4, -gridSize/2);
                ctx.lineTo(-gridSize/4, gridSize/2);
                ctx.moveTo(gridSize/4, -gridSize/2);
                ctx.lineTo(gridSize/4, gridSize/2);
                ctx.stroke();
                
                ctx.restore();
            } else if (shape.locked) {
                // Normal locked shape - show lock icon (red)
                ctx.save();
                ctx.translate(shape.x, shapeTop - 10 * iconScale);
                
                // Background circle
                ctx.beginPath();
                ctx.arc(0, 0, iconSize * 0.65, 0, Math.PI * 2);
                const lockGradient = ctx.createRadialGradient(0, 0, 0, 0, 0, iconSize * 0.65);
                lockGradient.addColorStop(0, 'rgba(231, 76, 60, 0.95)');
                lockGradient.addColorStop(1, 'rgba(192, 57, 43, 0.95)');
                ctx.fillStyle = lockGradient;
                ctx.fill();
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.7)';
                ctx.lineWidth = 1 * iconScale;
                ctx.stroke();
                
                // Draw padlock in white
                ctx.fillStyle = '#ffffff';
                ctx.strokeStyle = '#ffffff';
                
                // Lock body
                const bodyW = iconSize * 0.45;
                const bodyH = iconSize * 0.35;
                const bodyX = -bodyW / 2;
                const bodyY = -bodyH / 2 + iconSize * 0.07;
                ctx.beginPath();
                ctx.roundRect(bodyX, bodyY, bodyW, bodyH, iconSize * 0.05);
                ctx.fill();
                
                // Lock shackle
                ctx.beginPath();
                ctx.arc(0, bodyY, iconSize * 0.13, Math.PI, 0, false);
                ctx.lineWidth = iconSize * 0.08;
                ctx.lineCap = 'round';
                ctx.stroke();
                
                // Keyhole
                ctx.beginPath();
                ctx.arc(0, bodyY + bodyH * 0.35, iconSize * 0.05, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(192, 57, 43, 0.9)';
                ctx.fill();
                
                ctx.restore();
            }
        }
    },
    
    drawShapeSelectionHandles(editor, shape) {
        const ctx = editor.ctx;
        const x = shape.x;
        const y = shape.y;
        const w = shape.width;
        const h = shape.height;
        const rotation = shape.rotation || 0;
        
        // Get shape-specific handle positions (in local coordinates)
        const handlePositions = editor.getShapeHandlePositions(shape);
        
        // Selection outline with glow effect
        ctx.save();
        
        // Apply rotation around shape center
        ctx.translate(x, y);
        ctx.rotate(rotation * Math.PI / 180);
        ctx.translate(-x, -y);
        
        // Glow
        ctx.shadowColor = 'rgba(52, 152, 219, 0.5)';
        ctx.shadowBlur = 8;
        ctx.strokeStyle = 'rgba(52, 152, 219, 0.8)';
        ctx.lineWidth = 2;
        ctx.setLineDash([6, 4]);
        
        // Draw shape-specific selection outline (matches visual shape exactly)
        const outlineOffset = 4; // Pixels outside the shape
        if (shape.shapeType === 'circle') {
            ctx.beginPath();
            ctx.arc(x, y, w/2 + outlineOffset, 0, Math.PI * 2);
            ctx.stroke();
        } else if (shape.shapeType === 'ellipse') {
            ctx.beginPath();
            ctx.ellipse(x, y, w/2 + outlineOffset, h/2 + outlineOffset, 0, 0, Math.PI * 2);
            ctx.stroke();
        } else if (shape.shapeType === 'diamond') {
            // Diamond outline follows the diamond shape
            ctx.beginPath();
            ctx.moveTo(x, y - h/2 - outlineOffset); // Top
            ctx.lineTo(x + w/2 + outlineOffset, y); // Right
            ctx.lineTo(x, y + h/2 + outlineOffset); // Bottom
            ctx.lineTo(x - w/2 - outlineOffset, y); // Left
            ctx.closePath();
            ctx.stroke();
        } else if (shape.shapeType === 'cloud') {
            // Cloud outline follows ellipse approximation
            ctx.beginPath();
            ctx.ellipse(x, y, w/2 + outlineOffset, h/2 + outlineOffset, 0, 0, Math.PI * 2);
            ctx.stroke();
        } else {
            // Rectangle
            ctx.strokeRect(x - w/2 - outlineOffset, y - h/2 - outlineOffset, w + outlineOffset*2, h + outlineOffset*2);
        }
        ctx.setLineDash([]);
        ctx.shadowBlur = 0;
        
        // Draw handles at their positions - zoom-adjusted sizes like devices
        const zoomScale = 1 / editor.zoom;
        handlePositions.forEach(handle => {
            // Larger sizes, zoom-adjusted
            const displaySize = handle.size * zoomScale;
            
            // Draw glow behind handle
            ctx.shadowColor = 'rgba(52, 152, 219, 0.6)';
            ctx.shadowBlur = 8 * zoomScale;
            
            // Corner handles are squares, edge handles are circles (blue like devices)
            if (handle.isCorner) {
                // Square handle for corners
                const hs = displaySize / 2;
                ctx.fillStyle = '#3498db'; // Blue like device resize handles
                ctx.fillRect(handle.x - hs, handle.y - hs, displaySize, displaySize);
                ctx.shadowBlur = 0;
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 2 * zoomScale;
                ctx.strokeRect(handle.x - hs, handle.y - hs, displaySize, displaySize);
            } else {
                // Circle handle for edges (blue like devices)
                ctx.fillStyle = '#3498db'; // Blue like device resize handles
                ctx.beginPath();
                ctx.arc(handle.x, handle.y, displaySize/2, 0, Math.PI * 2);
                ctx.fill();
                ctx.shadowBlur = 0;
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 2 * zoomScale;
                ctx.stroke();
            }
        });
        
        // Draw rotation handle at TOP-RIGHT (matching device style) - zoom-adjusted
        const rotHandleOffset = 15 * zoomScale;
        const halfW = w / 2;
        const halfH = h / 2;
        // Local coords: top-right corner with offset
        const localRotX = halfW + rotHandleOffset;
        const localRotY = -(halfH + rotHandleOffset);
        // Position is already rotated since we're in rotated context
        const handleX = x + localRotX;
        const handleY = y + localRotY;
        
        // Draw angle meter arc around rotation handle (like device)
        const arcRadius = 16 * zoomScale;
        const rotationRadians = (rotation) * Math.PI / 180;
        
        // Draw background circle (light gray track)
        ctx.beginPath();
        ctx.arc(handleX, handleY, arcRadius, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(200, 200, 200, 0.4)';
        ctx.lineWidth = 3 * zoomScale;
        ctx.stroke();
        
        // Draw arc from 0° to current rotation (green progress arc)
        if (Math.abs(rotationRadians) > 0.01) {
            ctx.beginPath();
            ctx.arc(handleX, handleY, arcRadius, 0, rotationRadians);
            ctx.strokeStyle = '#27ae60';
            ctx.lineWidth = 3 * zoomScale;
            ctx.stroke();
        }
        
        // Draw rotation handle dot (green, like device)
        const handleRadius = 12 * zoomScale; // Larger like devices
        ctx.beginPath();
        ctx.arc(handleX, handleY, handleRadius, 0, Math.PI * 2);
        ctx.fillStyle = '#27ae60'; // Green color for rotation handle
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2 * zoomScale;
        ctx.stroke();
        
        // Draw current rotation angle text
        const rotationDegrees = Math.round(rotation);
        if (rotationDegrees !== 0) {
            ctx.save();
            ctx.font = `${11 * zoomScale}px Arial`;
            ctx.fillStyle = '#27ae60';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(`${rotationDegrees}°`, handleX, handleY - arcRadius - 8 * zoomScale);
            ctx.restore();
        }
        
        // Draw GROUP indicator if shape belongs to a group
        if (shape.groupId) {
            const dotSize = 6 * zoomScale;
            // Position at bottom-left of shape
            const dotX = x - w/2 - 10 * zoomScale;
            const dotY = y + h/2 + 10 * zoomScale;
            
            // Purple dot indicator
            ctx.beginPath();
            ctx.arc(dotX, dotY, dotSize, 0, Math.PI * 2);
            const groupGradient = ctx.createRadialGradient(dotX, dotY, 0, dotX, dotY, dotSize);
            groupGradient.addColorStop(0, 'rgba(155, 89, 182, 0.95)');
            groupGradient.addColorStop(1, 'rgba(142, 68, 173, 0.95)');
            ctx.fillStyle = groupGradient;
            ctx.fill();
            
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
            ctx.lineWidth = 1.5 * zoomScale;
            ctx.stroke();
        }
        
        ctx.restore();
    },
    
    // Get handle positions based on shape type - handles at actual visual boundaries

};

console.log('[topology-shape-drawing.js] ShapeDrawing loaded');
