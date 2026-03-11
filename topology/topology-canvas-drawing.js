/**
 * topology-canvas-drawing.js - Canvas Drawing Functions
 * 
 * Contains: drawDevice, drawDeviceLabel, drawText
 */

'use strict';

window.CanvasDrawing = {
    _contrastColorForBg(editor, textColor, bgColor) {
        const n = editor._normalizeHex(textColor);
        if (!n) return textColor;
        const isBlackOrWhite = (n === '#000000' || n === '#ffffff');
        if (!isBlackOrWhite) return textColor;
        const lum = this._luminance(bgColor);
        return lum > 0.45 ? '#000000' : '#ffffff';
    },

    _luminance(color) {
        if (!color || typeof color !== 'string') return 0.5;
        let r, g, b;
        if (color.startsWith('#')) {
            let hex = color.replace('#', '');
            if (hex.length === 3) hex = hex[0]+hex[0]+hex[1]+hex[1]+hex[2]+hex[2];
            r = parseInt(hex.substring(0,2), 16) / 255;
            g = parseInt(hex.substring(2,4), 16) / 255;
            b = parseInt(hex.substring(4,6), 16) / 255;
        } else if (color.startsWith('rgb')) {
            const m = color.match(/[\d.]+/g);
            if (!m || m.length < 3) return 0.5;
            r = parseFloat(m[0]) / 255;
            g = parseFloat(m[1]) / 255;
            b = parseFloat(m[2]) / 255;
        } else {
            return 0.5;
        }
        return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    },

    drawDevice(editor, device, unused = false, skipLabelArg = false) {
        const isSelected = editor.selectedObject === device || editor.selectedObjects.includes(device);
        const style = device.visualStyle || 'circle';
        
        // Check if multiple objects are selected - skip individual handles in multi-select
        const isMultiSelect = editor.selectedObjects.length > 1;
        
        // Dispatch to appropriate drawing method based on visualStyle
        switch (style) {
            case 'classic':
                editor.drawDeviceClassicRouter(device, isSelected);
                break;
            case 'simple':
                editor.drawDeviceSimpleRouter(device, isSelected);
                break;
            case 'server':
                editor.drawDeviceServerTower(device, isSelected);
                break;
            case 'hex':
                editor.drawDeviceHexRouter(device, isSelected);
                break;
            case 'circle':
            default:
                editor.drawDeviceCircle(device, isSelected);
                break;
        }
        
        // Skip label drawing if requested (labels drawn in separate pass for layering on top of links)
        // But still draw selection highlight and handles
        
        // Draw selection highlight when device is selected (regardless of mode)
        if (isSelected) {
            // Selection highlight ring - scales with zoom for consistent appearance
            const selectionOffset = 5 / editor.zoom; // 5px in screen space
            const dashLength = 5 / editor.zoom; // Dash pattern scales with zoom
            const deviceRotation = (device.rotation || 0) * Math.PI / 180;
            
            // Get shape-aware bounds for selection ring
            const bounds = editor.getDeviceBounds(device);
            const r = device.radius;
            
            editor.ctx.save();
            editor.ctx.translate(device.x, device.y);
            editor.ctx.rotate(deviceRotation);
            
            editor.ctx.strokeStyle = '#3498db';
            editor.ctx.lineWidth = 2 / editor.zoom;
            editor.ctx.setLineDash([dashLength, dashLength]);
            
            editor.ctx.beginPath();
            switch (bounds.type) {
                case 'classic': {
                    // Classic router - rectangular selection
                    const hw = bounds.width / 2 + selectionOffset;
                    const top = bounds.top - selectionOffset;
                    const bottom = bounds.bottom + selectionOffset;
                    editor.ctx.rect(-hw, top, hw * 2, bottom - top);
                    break;
                }
                case 'rectangle': {
                    // Server tower - rectangular selection
                    const hw = bounds.width / 2 + selectionOffset;
                    const hh = bounds.height / 2 + selectionOffset;
                    editor.ctx.rect(-hw, -hh, hw * 2, hh * 2);
                    break;
                }
                case 'hexagon': {
                    // Hex router - draw actual hexagon selection outline
                    const hexR = r * 0.65 + selectionOffset;
                    for (let i = 0; i < 6; i++) {
                        const angle = (Math.PI / 6) + (i * Math.PI / 3);
                        const px = Math.cos(angle) * hexR;
                        const py = Math.sin(angle) * hexR;
                        if (i === 0) editor.ctx.moveTo(px, py);
                        else editor.ctx.lineTo(px, py);
                    }
                    editor.ctx.closePath();
                    break;
                }
                case 'circle':
                default:
                    // Circle - standard circular selection
                    editor.ctx.arc(0, 0, r + selectionOffset, 0, Math.PI * 2);
                    break;
            }
            editor.ctx.stroke();
            editor.ctx.setLineDash([]);
            editor.ctx.restore();
            
            // MULTI-SELECT: Skip individual handles (rotation, resize, terminal) when multiple objects selected
            // This keeps the view clean - only show selection outline for each object
            if (!isMultiSelect) {
            // Draw rotation handle at TOP-RIGHT of device
            // UPDATED: Handles now scale with device size (no cap)
            const rotHandleOffset = 15 / editor.zoom; // Offset beyond edge
            // Use actual device bounds - handles follow the edge at any size
            const halfW = bounds.width / 2;
            const halfH = bounds.height / 2;
            // Local coords: top-right corner with offset
            const localRotX = halfW + rotHandleOffset;
            const localRotY = -(halfH + rotHandleOffset); // Negative because top is above center
            // Rotate to world coords
            const handleX = device.x + localRotX * Math.cos(deviceRotation) - localRotY * Math.sin(deviceRotation);
            const handleY = device.y + localRotX * Math.sin(deviceRotation) + localRotY * Math.cos(deviceRotation);
            
            // Draw angle meter arc around rotation handle
            const arcRadius = 16 / editor.zoom;
            const rotationRadians = (device.rotation || 0) * Math.PI / 180;
            
            // Draw background circle (light gray track)
            editor.ctx.beginPath();
            editor.ctx.arc(handleX, handleY, arcRadius, 0, Math.PI * 2);
            editor.ctx.strokeStyle = 'rgba(200, 200, 200, 0.4)';
            editor.ctx.lineWidth = 3 / editor.zoom;
            editor.ctx.stroke();
            
            // Draw arc from 0° to current rotation (green progress arc)
            if (Math.abs(rotationRadians) > 0.01) {
                editor.ctx.beginPath();
                editor.ctx.arc(handleX, handleY, arcRadius, 0, rotationRadians);
                editor.ctx.strokeStyle = '#27ae60';
                editor.ctx.lineWidth = 3 / editor.zoom;
                editor.ctx.stroke();
            }
            
            // Draw rotation handle dot
            const handleRadius = 10 / editor.zoom;
            editor.ctx.beginPath();
            editor.ctx.arc(handleX, handleY, handleRadius, 0, Math.PI * 2);
            editor.ctx.fillStyle = '#27ae60'; // Green color for rotation handle
            editor.ctx.fill();
            editor.ctx.strokeStyle = '#ffffff';
            editor.ctx.lineWidth = 2 / editor.zoom;
            editor.ctx.stroke();
            
            // Draw current rotation angle text
            const rotationDegrees = Math.round(device.rotation || 0);
            if (rotationDegrees !== 0) {
                editor.ctx.save();
                editor.ctx.font = `${10 / editor.zoom}px Arial`;
                editor.ctx.fillStyle = '#27ae60';
                editor.ctx.textAlign = 'center';
                editor.ctx.textBaseline = 'middle';
                editor.ctx.fillText(`${rotationDegrees}°`, handleX, handleY - arcRadius - 8 / editor.zoom);
                editor.ctx.restore();
            }
            
            // Draw resize handles - shape-aware positions
            const resizeOffset = 10 / editor.zoom;
            const resizeHandleRadius = 5 / editor.zoom;
            const cornerHandleSize = 6 / editor.zoom;
            const resizeHandleColor = '#3498db';

            // 4 cardinal resize handles only (N, E, S, W)
            const resizePositions = [];
            switch (bounds.type) {
                case 'classic': {
                    const top = bounds.top - resizeOffset;
                    const bottom = bounds.bottom + resizeOffset;
                    const cy = bounds.centerY;
                    const hw = bounds.width / 2 + resizeOffset;
                    resizePositions.push({ x: 0, y: top, id: 'n' });
                    resizePositions.push({ x: hw, y: cy, id: 'e' });
                    resizePositions.push({ x: 0, y: bottom, id: 's' });
                    resizePositions.push({ x: -hw, y: cy, id: 'w' });
                    break;
                }
                case 'rectangle': {
                    const hh = bounds.height / 2 + resizeOffset;
                    const hw = bounds.width / 2 + resizeOffset;
                    resizePositions.push({ x: 0, y: -hh, id: 'n' });
                    resizePositions.push({ x: hw, y: 0, id: 'e' });
                    resizePositions.push({ x: 0, y: hh, id: 's' });
                    resizePositions.push({ x: -hw, y: 0, id: 'w' });
                    break;
                }
                case 'hexagon': {
                    const hexR = r * 0.65 + resizeOffset;
                    resizePositions.push({ x: 0, y: -hexR, id: 'n' });
                    resizePositions.push({ x: hexR, y: 0, id: 'e' });
                    resizePositions.push({ x: 0, y: hexR, id: 's' });
                    resizePositions.push({ x: -hexR, y: 0, id: 'w' });
                    break;
                }
                case 'circle':
                default: {
                    const dist = r + resizeOffset;
                    resizePositions.push({ x: 0, y: -dist, id: 'n' });
                    resizePositions.push({ x: dist, y: 0, id: 'e' });
                    resizePositions.push({ x: 0, y: dist, id: 's' });
                    resizePositions.push({ x: -dist, y: 0, id: 'w' });
                    break;
                }
            }

            resizePositions.forEach(pos => {
                const rotatedX = pos.x * Math.cos(deviceRotation) - pos.y * Math.sin(deviceRotation);
                const rotatedY = pos.x * Math.sin(deviceRotation) + pos.y * Math.cos(deviceRotation);
                const resizeX = device.x + rotatedX;
                const resizeY = device.y + rotatedY;

                editor.ctx.beginPath();
                editor.ctx.arc(resizeX, resizeY, resizeHandleRadius, 0, Math.PI * 2);
                editor.ctx.fillStyle = resizeHandleColor;
                editor.ctx.fill();
                editor.ctx.strokeStyle = '#ffffff';
                editor.ctx.lineWidth = 1.5 / editor.zoom;
                editor.ctx.stroke();
            });
            
            // Calculate rotatedAngle for angle meter positioning
            const baseAngle = -Math.PI / 4;
            const rotatedAngle = baseAngle + deviceRotation;
            
            // NEW: Draw Angle Meter if enabled - rotates with device for cleaner UI
            if (editor.showAngleMeter) {
                const degrees = Math.round((device.rotation || 0) % 360);
                const normalizedDegrees = degrees < 0 ? degrees + 360 : degrees;
                
                editor.ctx.save();
                
                // Position relative to handle with rotation
                const labelOffsetDist = 25 / editor.zoom;
                const labelX = handleX + Math.cos(rotatedAngle) * labelOffsetDist;
                const labelY = handleY + Math.sin(rotatedAngle) * labelOffsetDist;
                
                // Translate to label position
                editor.ctx.translate(labelX, labelY);
                
                // ENHANCED: Rotate label to align with device rotation for cleaner look
                // Keep text horizontal when rotation is near 0/180, otherwise align with device
                const shouldAlignWithDevice = Math.abs(degrees % 180) > 15 && Math.abs(degrees % 180) < 165;
                if (shouldAlignWithDevice) {
                    editor.ctx.rotate(deviceRotation);
                }
                
                const text = `${normalizedDegrees}°`;
                editor.ctx.font = `bold ${11 / editor.zoom}px Arial`;
                const metrics = editor.ctx.measureText(text);
                
                const bgPad = 5 / editor.zoom;
                const bgW = metrics.width + bgPad * 2;
                const bgH = 16 / editor.zoom;
                const radius = 4 / editor.zoom;
                
                // Shadow for depth
                editor.ctx.shadowColor = 'rgba(0, 0, 0, 0.4)';
                editor.ctx.shadowBlur = 6 / editor.zoom;
                editor.ctx.shadowOffsetX = 1 / editor.zoom;
                editor.ctx.shadowOffsetY = 2 / editor.zoom;
                
                // Gradient background for modern look
                const gradient = editor.ctx.createLinearGradient(-bgW/2, -bgH/2, -bgW/2, bgH/2);
                gradient.addColorStop(0, 'rgba(46, 204, 113, 1)');
                gradient.addColorStop(1, 'rgba(39, 174, 96, 1)');
                
                // Rounded rectangle
                editor.ctx.beginPath();
                editor.ctx.moveTo(-bgW/2 + radius, -bgH/2);
                editor.ctx.lineTo(bgW/2 - radius, -bgH/2);
                editor.ctx.arcTo(bgW/2, -bgH/2, bgW/2, -bgH/2 + radius, radius);
                editor.ctx.lineTo(bgW/2, bgH/2 - radius);
                editor.ctx.arcTo(bgW/2, bgH/2, bgW/2 - radius, bgH/2, radius);
                editor.ctx.lineTo(-bgW/2 + radius, bgH/2);
                editor.ctx.arcTo(-bgW/2, bgH/2, -bgW/2, bgH/2 - radius, radius);
                editor.ctx.lineTo(-bgW/2, -bgH/2 + radius);
                editor.ctx.arcTo(-bgW/2, -bgH/2, -bgW/2 + radius, -bgH/2, radius);
                editor.ctx.closePath();
                editor.ctx.fillStyle = gradient;
                editor.ctx.fill();
                
                // Subtle border
                editor.ctx.shadowColor = 'transparent';
                editor.ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
                editor.ctx.lineWidth = 1.5 / editor.zoom;
                editor.ctx.stroke();
                
                // Text with shadow
                editor.ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
                editor.ctx.shadowBlur = 1 / editor.zoom;
                editor.ctx.shadowOffsetY = 1 / editor.zoom;
                editor.ctx.fillStyle = '#ffffff';
                editor.ctx.textAlign = 'center';
                editor.ctx.textBaseline = 'middle';
                editor.ctx.fillText(text, 0, 0);
                
                editor.ctx.restore();
            }
            } // End if (!isMultiSelect) - skip handles in multi-select
        }
        
        // Draw lock icon if device is locked AND (Labels toggle is ON OR device is selected)
        // This ensures locked devices are visually identifiable when selected
        const isDeviceSelected = editor.selectedObject === device || editor.selectedObjects.includes(device);
        if (device.locked && (editor.showLinkTypeLabels || isDeviceSelected)) {
            editor.ctx.save();
            
            // Position lock icon above the device
            const iconScale = 1 / editor.zoom;
            const iconSize = 14 * iconScale;
            editor.ctx.translate(device.x, device.y - device.radius - 12 * iconScale);
            
            // Draw a modern padlock icon with gradient
            // Background circle
            editor.ctx.beginPath();
            editor.ctx.arc(0, 0, iconSize * 0.7, 0, Math.PI * 2);
            const lockGradient = editor.ctx.createRadialGradient(0, 0, 0, 0, 0, iconSize * 0.7);
            lockGradient.addColorStop(0, 'rgba(231, 76, 60, 0.95)');
            lockGradient.addColorStop(1, 'rgba(192, 57, 43, 0.95)');
            editor.ctx.fillStyle = lockGradient;
            editor.ctx.fill();
            
            // White border
            editor.ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
            editor.ctx.lineWidth = 1.5 * iconScale;
            editor.ctx.stroke();
            
            // Draw padlock shape in white
            editor.ctx.strokeStyle = '#ffffff';
            editor.ctx.fillStyle = '#ffffff';
            editor.ctx.lineWidth = 1.2 * iconScale;
            
            // Lock body (rounded rectangle)
            const bodyW = iconSize * 0.5;
            const bodyH = iconSize * 0.4;
            const bodyX = -bodyW / 2;
            const bodyY = -bodyH / 2 + iconSize * 0.08;
            const bodyR = iconSize * 0.06;
            
            editor.ctx.beginPath();
            editor.ctx.roundRect(bodyX, bodyY, bodyW, bodyH, bodyR);
            editor.ctx.fill();
            
            // Lock shackle (U-shape on top)
            const shackleW = iconSize * 0.28;
            const shackleH = iconSize * 0.25;
            editor.ctx.beginPath();
            editor.ctx.arc(0, bodyY, shackleW / 2, Math.PI, 0, false);
            editor.ctx.lineWidth = iconSize * 0.1;
            editor.ctx.lineCap = 'round';
            editor.ctx.stroke();
            
            // Keyhole (small dark circle)
            editor.ctx.beginPath();
            editor.ctx.arc(0, bodyY + bodyH * 0.35, iconSize * 0.06, 0, Math.PI * 2);
            editor.ctx.fillStyle = 'rgba(192, 57, 43, 0.9)';
            editor.ctx.fill();
            
            editor.ctx.restore();
        }
        
        // Draw GROUP indicator icon if device belongs to a group
        // Shows a small chain link icon at the bottom-left corner
        if (device.groupId) {
            editor.ctx.save();
            
            const iconScale = 1 / editor.zoom;
            const iconSize = 12 * iconScale;
            
            // Position at bottom-left of device
            const iconX = device.x - device.radius * 0.7;
            const iconY = device.y + device.radius + 8 * iconScale;
            
            editor.ctx.translate(iconX, iconY);
            
            // Background circle with purple/magenta color (distinct from lock/terminal)
            editor.ctx.beginPath();
            editor.ctx.arc(0, 0, iconSize * 0.7, 0, Math.PI * 2);
            const groupGradient = editor.ctx.createRadialGradient(0, 0, 0, 0, 0, iconSize * 0.7);
            groupGradient.addColorStop(0, 'rgba(155, 89, 182, 0.95)');
            groupGradient.addColorStop(1, 'rgba(142, 68, 173, 0.95)');
            editor.ctx.fillStyle = groupGradient;
            editor.ctx.fill();
            
            // White border
            editor.ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
            editor.ctx.lineWidth = 1.5 * iconScale;
            editor.ctx.stroke();
            
            // Draw chain link icon in white
            editor.ctx.strokeStyle = '#ffffff';
            editor.ctx.lineWidth = 1.5 * iconScale;
            editor.ctx.lineCap = 'round';
            
            // Two interlocking ovals for chain link
            const ovalW = iconSize * 0.3;
            const ovalH = iconSize * 0.2;
            
            // Left oval
            editor.ctx.beginPath();
            editor.ctx.ellipse(-ovalW * 0.4, 0, ovalW, ovalH, 0, 0, Math.PI * 2);
            editor.ctx.stroke();
            
            // Right oval (overlapping)
            editor.ctx.beginPath();
            editor.ctx.ellipse(ovalW * 0.4, 0, ovalW, ovalH, 0, 0, Math.PI * 2);
            editor.ctx.stroke();
            
            editor.ctx.restore();
        }
        
        // Terminal button position calculation (actual drawing is in separate pass for top layer)
        // Only show when device is selected and has an address (either sshConfig.host or legacy deviceAddress)
        // MULTI-SELECT: Skip terminal button when multiple objects selected
        const hasSSHConfig = device.sshConfig?.host || (device.deviceAddress && device.deviceAddress.trim() !== '');
        if (isSelected && hasSSHConfig && !isMultiSelect) {
            // Calculate and store button position for hit detection and later drawing
            const btnRadius = 10 / editor.zoom;
            const deviceRotation = (device.rotation || 0) * Math.PI / 180;
            const bounds = editor.getDeviceBounds(device);
            const handleOffset = 15 / editor.zoom;
            const halfW = bounds.width / 2;
            const halfH = bounds.height / 2;
            const localX = -(halfW + handleOffset);
            const localY = -(halfH + handleOffset);
            const btnX = device.x + localX * Math.cos(deviceRotation) - localY * Math.sin(deviceRotation);
            const btnY = device.y + localX * Math.sin(deviceRotation) + localY * Math.cos(deviceRotation);
            
            // Store button position for hit detection (drawing happens in separate pass)
            device._terminalBtnPos = { x: btnX, y: btnY, radius: btnRadius };
        } else {
            // Clear button position when not visible
            delete device._terminalBtnPos;
        }
        
        // Draw LLDP animation effects (active animation, success glow, failure glow)
        if (device._lldpAnimating || device._lldpSuccessGlow || device._lldpFailureGlow) {
            try {
                editor._drawLldpEffects(device);
            } catch (e) {
                console.warn('[LLDP] Animation draw error:', e.message);
            }
        }
    },
    
    /**
     * Draw device label separately - called in a second pass to ensure labels
     * appear ON TOP of all links for better visibility
     * ENHANCED: Per-letter stroke/border for maximum visibility over links
     * Each letter has its own stroke outline, ensuring label is always readable
     */
    drawDeviceLabel(editor, device) {
        // Skip drawing label if device is being renamed inline
        if (device._renaming) return;
        
        const style = device.visualStyle || 'circle';
        
        // Draw device label - rotated and scaled with device
        editor.ctx.save();
        editor.ctx.translate(device.x, device.y);
        editor.ctx.rotate((device.rotation || 0) * Math.PI / 180);
        
        // Use custom labelSize if set, otherwise calculate based on radius
        // ENHANCED: Scale label size more with device size (0.5 factor, max 36px)
        const fontSize = device.labelSize || Math.max(12, Math.min(device.radius * 0.5, 36));
        // Use device's font family, or default DEVICE font family, or fallback to Inter
        const fontFamily = device.fontFamily || editor.defaultDeviceFontFamily || 'Inter, sans-serif';
        const fontWeight = device.fontWeight || '600';
        editor.ctx.font = `${fontWeight} ${fontSize}px ${fontFamily}`;
        editor.ctx.textAlign = 'center';
        editor.ctx.textBaseline = 'middle';
        
        const label = device.label || (device.deviceType === 'router' ? 'NCP' : 'S');
        
        // Adjust label position and style for different visual styles
        let labelY = 0;
        let labelBelow = false;
        let skipLabel = false;
        
        if (style === 'classic') {
            skipLabel = true; // Label is drawn on cylinder body
        } else if (style === 'hex') {
            labelY = device.radius * 0.85;
            labelBelow = true;
        } else if (style === 'simple') {
            labelY = device.radius * 1.15;
            labelBelow = true;
        } else if (style === 'server') {
            labelY = device.radius * 1.05;
            labelBelow = true;
        }
        
        if (!skipLabel) {
            // PER-LETTER STROKE APPROACH: Each letter gets its own border/outline
            // This creates visual separation from links without a background block
            
            const strokeWidth = editor.darkMode 
                ? Math.max(3.5, fontSize * 0.22) 
                : Math.max(4.5, fontSize * 0.28);
            let strokeColor;
            if (device.labelOutlineColor === 'none') {
                strokeColor = null;
            } else if (device.labelOutlineColor) {
                strokeColor = device.labelOutlineColor;
            } else {
                strokeColor = editor.darkMode 
                    ? 'rgba(13, 27, 42, 0.98)'
                    : 'rgba(255, 255, 255, 1)';
            }
            
            // Text fill color - use device.labelColor if set, else auto based on mode
            const textColor = device.labelColor || (editor.darkMode ? '#ECF0F1' : '#0d1b2a');
            
            if (strokeColor) {
                editor.ctx.lineWidth = strokeWidth;
                editor.ctx.strokeStyle = strokeColor;
                editor.ctx.lineJoin = 'round';
                editor.ctx.lineCap = 'round';
                editor.ctx.miterLimit = 2;
                editor.ctx.strokeText(label, 0, labelY);
            }
            
            editor.ctx.fillStyle = textColor;
            editor.ctx.fillText(label, 0, labelY);
            
            // Optional: Add subtle drop shadow for depth (labels below device get extra emphasis)
            if (labelBelow) {
                // Re-draw with slight shadow for depth
                editor.ctx.save();
                editor.ctx.shadowColor = editor.darkMode ? 'rgba(0,0,0,0.5)' : 'rgba(0,0,0,0.2)';
            editor.ctx.shadowBlur = 2;
            editor.ctx.shadowOffsetX = 0;
            editor.ctx.shadowOffsetY = 1;
                editor.ctx.fillStyle = textColor;
            editor.ctx.fillText(label, 0, labelY);
                editor.ctx.restore();
            }
        }
        
        editor.ctx.restore();
    },
    
    /**
     * Check if a device label overlaps with any entities (links, other devices, text boxes)
     * Returns true if there's significant overlap requiring a background
     */
    _checkLabelLinkOverlap(device, labelBounds) {
        // Check links
        const links = editor.objects.filter(obj => obj.type === 'link' || obj.type === 'unbound');
        
        for (const link of links) {
            // Skip links connected to this device (they naturally pass nearby)
            if (link.device1 === device.id || link.device2 === device.id) continue;
            
            // Get link endpoints
            let startX, startY, endX, endY;
            
            if (link.type === 'link') {
                const dev1 = editor.objects.find(o => o.id === link.device1);
                const dev2 = editor.objects.find(o => o.id === link.device2);
                if (!dev1 || !dev2) continue;
                startX = dev1.x;
                startY = dev1.y;
                endX = dev2.x;
                endY = dev2.y;
            } else if (link.type === 'unbound') {
                startX = link.start?.x ?? 0;
                startY = link.start?.y ?? 0;
                endX = link.end?.x ?? 0;
                endY = link.end?.y ?? 0;
            } else {
                continue;
            }
            
            // Simple line-rectangle intersection check
            if (editor._lineIntersectsRect(startX, startY, endX, endY, labelBounds)) {
                return true;
            }
        }
        
        // Check other devices (not self)
        const devices = editor.objects.filter(obj => 
            (obj.type === 'device' || obj.type === 'router' || obj.type === 'switch') && 
            obj.id !== device.id
        );
        
        for (const otherDev of devices) {
            // Calculate other device's bounding box
            const otherRadius = otherDev.radius || 30;
            const otherBounds = {
                left: otherDev.x - otherRadius,
                right: otherDev.x + otherRadius,
                top: otherDev.y - otherRadius,
                bottom: otherDev.y + otherRadius
            };
            
            // Check if label bounds overlap with device bounds
            if (editor._rectsOverlap(labelBounds, otherBounds)) {
                return true;
            }
        }
        
        // Check text boxes
        const textBoxes = editor.objects.filter(obj => obj.type === 'text');
        
        for (const textBox of textBoxes) {
            const tbBounds = {
                left: textBox.x,
                right: textBox.x + (textBox.width || 100),
                top: textBox.y,
                bottom: textBox.y + (textBox.height || 30)
            };
            
            if (editor._rectsOverlap(labelBounds, tbBounds)) {
                return true;
            }
        }
        
        return false;
    },
    
    /**
     * Check if two rectangles overlap
     */
    _rectsOverlap(rect1, rect2) {
        return !(rect1.right < rect2.left || 
                 rect1.left > rect2.right || 
                 rect1.bottom < rect2.top || 
                 rect1.top > rect2.bottom);
    },
    
    /**
     * Check if a line segment intersects with a rectangle
     */
    _lineIntersectsRect(x1, y1, x2, y2, rect) {
        // Check if line is completely outside the rect
        if ((x1 < rect.left && x2 < rect.left) || (x1 > rect.right && x2 > rect.right)) return false;
        if ((y1 < rect.top && y2 < rect.top) || (y1 > rect.bottom && y2 > rect.bottom)) return false;
        
        // Check if either endpoint is inside the rect
        if (x1 >= rect.left && x1 <= rect.right && y1 >= rect.top && y1 <= rect.bottom) return true;
        if (x2 >= rect.left && x2 <= rect.right && y2 >= rect.top && y2 <= rect.bottom) return true;
        
        // Check intersection with each edge of the rect
        const edges = [
            [rect.left, rect.top, rect.right, rect.top],     // top
            [rect.right, rect.top, rect.right, rect.bottom], // right
            [rect.left, rect.bottom, rect.right, rect.bottom], // bottom
            [rect.left, rect.top, rect.left, rect.bottom]    // left
        ];
        
        for (const [ex1, ey1, ex2, ey2] of edges) {
            if (editor._lineSegmentsIntersect(x1, y1, x2, y2, ex1, ey1, ex2, ey2)) {
                return true;
            }
        }
        
        return false;
    },
    
    /**
     * Check if two line segments intersect
     */
    _lineSegmentsIntersect(x1, y1, x2, y2, x3, y3, x4, y4) {
        const denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1);
        if (Math.abs(denom) < 0.0001) return false; // Parallel
        
        const ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom;
        const ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom;
        
        return ua >= 0 && ua <= 1 && ub >= 0 && ub <= 1;
    },
    
    drawLink(link) {
        if (window.LinkDrawing) {
            return window.LinkDrawing.drawLink(this, link);
        }
    },
    
    drawUnboundLink(link) {
        if (window.LinkDrawing) {
            return window.LinkDrawing.drawUnboundLink(this, link);
        }
    },
    
    
    // Draw a gap (eraser) in the link where on-line text is positioned
    drawLinkGapForText(textObj) {
        const link = editor.objects.find(obj => obj.id === textObj.linkId);
        if (!link) return;
        
        const effGapR = editor.getEffectiveTextRotation ? editor.getEffectiveTextRotation(textObj) : (textObj.rotation || 0);
        editor.ctx.save();
        editor.ctx.translate(textObj.x, textObj.y);
        editor.ctx.rotate(effGapR * Math.PI / 180);
        
        // Measure text using proper font (include fontStyle for italic)
        const fontStyle = textObj.fontStyle || 'normal';
        const fontWeight = textObj.fontWeight || 'normal';
        const fontFamily = textObj.fontFamily || 'Arial, sans-serif';
        editor.ctx.font = `${fontStyle} ${fontWeight} ${textObj.fontSize}px ${fontFamily}`;
        const metrics = editor.ctx.measureText(textObj.text || 'Text');
        const w = metrics.width;
        const h = parseInt(textObj.fontSize);
        
        // Padding around text for the gap
        const padding = 6;
        const gapWidth = w + padding * 2;
        const gapHeight = h + padding * 2;
        
        // Get link width to make sure the eraser covers the full link thickness
        const linkWidth = link.width !== undefined ? link.width : editor.currentLinkWidth;
        const eraserHeight = Math.max(gapHeight, linkWidth + 4);
        
        // Draw eraser rectangle (same color as background)
        editor.ctx.fillStyle = editor.darkMode ? '#1a1a1a' : '#f5f5f5';
        editor.ctx.fillRect(-gapWidth/2, -eraserHeight/2, gapWidth, eraserHeight);
        
        editor.ctx.restore();
    },
    
    drawText(editor, text) {
        // Skip drawing if text is being edited inline (input shows it instead)
        if (text._editing) {
            return;
        }
        
        const isSelected = editor.selectedObject === text || editor.selectedObjects.includes(text);
        
        editor.ctx.save();
        editor.ctx.translate(text.x, text.y);
        
        // Determine rotation: per-TB override > global setting > stored rotation
        // - If text.alwaysFaceUser is explicitly true → force 0°
        // - If text.alwaysFaceUser is explicitly false → use stored rotation
        // - If text.alwaysFaceUser is undefined → use global setting
        let effectiveRotation = text.rotation || 0;
        if (text.alwaysFaceUser === true) {
            effectiveRotation = 0; // Per-TB override
        } else if (text.alwaysFaceUser === false) {
            effectiveRotation = text.rotation || 0; // Per-TB explicit rotation
        } else if (editor.textAlwaysFaceUser) {
            effectiveRotation = 0; // Global setting
        }
        editor.ctx.rotate(effectiveRotation * Math.PI / 180);
        
        // Build font string with style, weight and family
        // Canvas font format: [font-style] [font-weight] font-size font-family
        const fontStyle = text.fontStyle || 'normal'; // italic, oblique, or normal
        const fontWeight = text.fontWeight || 'normal';
        const fontFamily = text.fontFamily || 'Arial, sans-serif';
        editor.ctx.font = `${fontStyle} ${fontWeight} ${text.fontSize}px ${fontFamily}`;
        editor.ctx.textAlign = 'center';
        editor.ctx.textBaseline = 'middle';
        
        // ENHANCED: Attached text boxes (on link lines) get grid-matching backgrounds
        // This hides the link body through the text while grid shows through char gaps
        const isAttachedToLink = text.linkId && text._onLinkLine === true;
        const isInterfaceLabel = text._interfaceLabel === true;
        
        // For interface labels on links: use grid-matching background color
        // This creates the "transparent" illusion where link is hidden but grid shows through
        const gridBgColor = editor.darkMode ? '#1a1a1a' : '#ffffff';
        const defaultBgColor = editor.darkMode ? '#1a1a1a' : '#f5f5f5';
        
        // Determine background color
        // FIXED: Attached text boxes can use their custom bgColor if set
        let bgColor;
        if (isInterfaceLabel) {
            // Interface labels always use grid color for seamless appearance
            bgColor = gridBgColor;
        } else if (isAttachedToLink && text.showBackground !== false) {
            // Attached text with background enabled: use custom bgColor if set, else grid color
            bgColor = text.bgColor || gridBgColor;
        } else if (isAttachedToLink) {
            // Attached text without explicit background: use grid color
            bgColor = gridBgColor;
        } else {
            // Regular text: use custom bgColor or default
            bgColor = text.bgColor || text.backgroundColor || defaultBgColor;
        }
        
        // MULTILINE SUPPORT: Split text into lines and measure all
        const textContent = text.text || 'Text';
        const lines = textContent.split('\n');
        const fontSize = parseInt(text.fontSize) || 14;
        const lineHeight = fontSize * 1.3; // Match hitbox calculation
        
        // Measure maximum width across all lines
        let maxWidth = 0;
        for (const line of lines) {
            const metrics = editor.ctx.measureText(line || ' ');
            maxWidth = Math.max(maxWidth, metrics.width);
        }
        const w = maxWidth;
        const h = lines.length * lineHeight;
        
        // Draw background for:
        // - Regular text with showBackground enabled
        // - Attached text with showBackground enabled (uses custom bgColor)
        // - Interface labels attached to links (always, to hide link body)
        const shouldDrawBackground = (text.showBackground !== false && bgColor !== 'transparent') ||
                                     isInterfaceLabel;
        
        if (shouldDrawBackground) {
            // TIGHTER padding for link-attached text to reduce visual gap
            const defaultPadding = isAttachedToLink ? 4 : 8;
            const padding = text.backgroundPadding !== undefined ? text.backgroundPadding : defaultPadding;
        
            // Apply opacity if set
            editor.ctx.save();
            // backgroundOpacity can be 0-1 or 0-100, normalize to 0-1
            let opacity = text.backgroundOpacity;
            if (opacity === undefined) {
                opacity = 0.95;
            } else if (opacity > 1) {
                opacity = opacity / 100; // Convert from 0-100 to 0-1
            }
            editor.ctx.globalAlpha = opacity;
            
            // Draw background rectangle (now correctly sized for multiline)
            editor.ctx.fillStyle = bgColor;
            editor.ctx.fillRect(-w/2 - padding, -h/2 - padding, w + padding * 2, h + padding * 2);
            
            editor.ctx.restore();
        }
        
        // Draw each line of text with stroke outline
        const startY = -h/2 + lineHeight/2; // Center the block vertically
        lines.forEach((line, index) => {
            const y = startY + index * lineHeight;
            
            // Draw text border/stroke outline first (if enabled)
            // Border = per-character stroke outline (not background box border)
            if (text.showBorder && text.borderWidth > 0) {
                editor.ctx.strokeStyle = text.borderColor || '#0066FA';
                editor.ctx.lineWidth = text.borderWidth || 2;
                editor.ctx.lineJoin = 'round'; // Smooth corners on stroke
                editor.ctx.miterLimit = 2;
                editor.ctx.strokeText(line || ' ', 0, y);
            } else if (text.strokeWidth && text.strokeWidth > 0) {
                // Legacy stroke support (for old text objects)
                editor.ctx.strokeStyle = text.strokeColor || '#000000';
                editor.ctx.lineWidth = text.strokeWidth || 2;
                editor.ctx.lineJoin = 'round';
                editor.ctx.miterLimit = 2;
                editor.ctx.strokeText(line || ' ', 0, y);
            }
            
            // Auto-adjust text color for visibility:
            // If TB has a visible background, contrast against that instead of the canvas mode
            if (shouldDrawBackground && bgColor && bgColor !== 'transparent') {
                editor.ctx.fillStyle = this._contrastColorForBg(editor, text.color, bgColor);
            } else {
                editor.ctx.fillStyle = editor.adjustColorForMode(text.color);
            }
            editor.ctx.fillText(line || ' ', 0, y);
        });
        
        // Draw selection highlight when text is selected (regardless of mode)
        // Use the calculated multiline w and h from above
        if (isSelected) {
            editor.ctx.strokeStyle = '#3498db';
            editor.ctx.lineWidth = 2;
            editor.ctx.setLineDash([5, 5]);
            editor.ctx.strokeRect(-w/2 - 5, -h/2 - 5, w + 10, h + 10);
            editor.ctx.setLineDash([]);
            
            // Draw GROUP indicator if text belongs to a group
            if (text.groupId) {
                const groupDotSize = 6;
                const groupDotX = w/2 + 10;
                const groupDotY = -h/2 - 10;
                
                // Purple dot indicator for grouped objects
                editor.ctx.beginPath();
                editor.ctx.arc(groupDotX, groupDotY, groupDotSize, 0, Math.PI * 2);
                const groupGradient = editor.ctx.createRadialGradient(groupDotX, groupDotY, 0, groupDotX, groupDotY, groupDotSize);
                groupGradient.addColorStop(0, 'rgba(155, 89, 182, 1)');
                groupGradient.addColorStop(1, 'rgba(142, 68, 173, 1)');
                editor.ctx.fillStyle = groupGradient;
                editor.ctx.fill();
                editor.ctx.strokeStyle = '#ffffff';
                editor.ctx.lineWidth = 1.5;
                editor.ctx.stroke();
            }
            
            // Draw LOCK indicator if text is locked
            if (text.locked) {
                const lockIconSize = 8;
                const lockIconX = -w/2 - 12;
                const lockIconY = -h/2 - 10;
                
                // Red background circle
                editor.ctx.beginPath();
                editor.ctx.arc(lockIconX, lockIconY, lockIconSize, 0, Math.PI * 2);
                const lockGradient = editor.ctx.createRadialGradient(lockIconX, lockIconY, 0, lockIconX, lockIconY, lockIconSize);
                lockGradient.addColorStop(0, 'rgba(231, 76, 60, 0.95)');
                lockGradient.addColorStop(1, 'rgba(192, 57, 43, 0.95)');
                editor.ctx.fillStyle = lockGradient;
                editor.ctx.fill();
                editor.ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
                editor.ctx.lineWidth = 1.5;
                editor.ctx.stroke();
                
                // Draw padlock in white
                editor.ctx.fillStyle = '#ffffff';
                editor.ctx.strokeStyle = '#ffffff';
                
                // Lock body
                const bodyW = lockIconSize * 0.6;
                const bodyH = lockIconSize * 0.5;
                const bodyX = lockIconX - bodyW / 2;
                const bodyY = lockIconY - bodyH / 2 + lockIconSize * 0.1;
                editor.ctx.beginPath();
                editor.ctx.roundRect(bodyX, bodyY, bodyW, bodyH, lockIconSize * 0.08);
                editor.ctx.fill();
                
                // Lock shackle
                editor.ctx.beginPath();
                editor.ctx.arc(lockIconX, bodyY, lockIconSize * 0.18, Math.PI, 0, false);
                editor.ctx.lineWidth = lockIconSize * 0.12;
                editor.ctx.lineCap = 'round';
                editor.ctx.stroke();
            }
            
            // MULTI-SELECT: Skip resize/rotate handles when multiple objects selected
            const isMultiSelect = editor.selectedObjects.length > 1;
            if (isMultiSelect) {
                editor.ctx.restore();
                return; // Skip handles in multi-select mode
            }
            
            // ENHANCED: Better sized handles that scale with zoom
            const handleSize = Math.max(6, Math.min(10, 8 / editor.zoom)); // Consistent size regardless of zoom
            const handleOffset = 8; // Distance from text edge
            
            // Draw corner handles for size control and rotation
            const corners = [
                { x: -w/2 - handleOffset, y: -h/2 - handleOffset, type: 'resize', cursor: 'nwse-resize' },  // Top-left
                { x: w/2 + handleOffset, y: -h/2 - handleOffset, type: 'rotation', cursor: 'grab' },  // Top-right (rotation)
                { x: w/2 + handleOffset, y: h/2 + handleOffset, type: 'resize', cursor: 'nwse-resize' },     // Bottom-right
                { x: -w/2 - handleOffset, y: h/2 + handleOffset, type: 'resize', cursor: 'nesw-resize' }     // Bottom-left
            ];
            
            corners.forEach(corner => {
                if (corner.type === 'rotation') {
                    // ROTATION HANDLE - Green with rotation icon (use effective rotation)
                    const rotationRadians = effectiveRotation * Math.PI / 180;
                    const arcRadius = handleSize + 4;
                    
                    // Draw progress arc showing current rotation
                    if (Math.abs(rotationRadians) > 0.05) {
                        editor.ctx.beginPath();
                        editor.ctx.arc(corner.x, corner.y, arcRadius, -Math.PI/2, -Math.PI/2 + rotationRadians);
                        editor.ctx.strokeStyle = '#2ecc71';
                        editor.ctx.lineWidth = 2.5;
                        editor.ctx.lineCap = 'round';
                        editor.ctx.stroke();
                    }
                    
                    // Main rotation handle - filled circle
                    editor.ctx.beginPath();
                    editor.ctx.arc(corner.x, corner.y, handleSize, 0, Math.PI * 2);
                    
                    // Gradient fill for 3D effect
                    const gradient = editor.ctx.createRadialGradient(
                        corner.x - handleSize/3, corner.y - handleSize/3, 0,
                        corner.x, corner.y, handleSize
                    );
                    gradient.addColorStop(0, '#58d68d');
                    gradient.addColorStop(1, '#27ae60');
                    editor.ctx.fillStyle = gradient;
                    editor.ctx.fill();
                    
                    // White border
                    editor.ctx.strokeStyle = 'white';
                    editor.ctx.lineWidth = 2;
                    editor.ctx.stroke();
                    
                    // Rotation icon (curved arrow)
                    editor.ctx.save();
                    editor.ctx.translate(corner.x, corner.y);
                    editor.ctx.beginPath();
                    editor.ctx.arc(0, 0, handleSize * 0.5, -Math.PI * 0.8, Math.PI * 0.3);
                    editor.ctx.strokeStyle = 'white';
                    editor.ctx.lineWidth = 1.5;
                    editor.ctx.lineCap = 'round';
                    editor.ctx.stroke();
                    // Arrow head
                    const arrowAngle = Math.PI * 0.3;
                    const arrowX = Math.cos(arrowAngle) * handleSize * 0.5;
                    const arrowY = Math.sin(arrowAngle) * handleSize * 0.5;
                    editor.ctx.beginPath();
                    editor.ctx.moveTo(arrowX, arrowY);
                    editor.ctx.lineTo(arrowX + 3, arrowY - 1);
                    editor.ctx.lineTo(arrowX + 1, arrowY + 3);
                    editor.ctx.fillStyle = 'white';
                    editor.ctx.fill();
                    editor.ctx.restore();
                } else {
                    // RESIZE HANDLES - Cyan/blue squares for better distinction
                    const squareSize = handleSize * 1.6;
                    
                    // Rounded square
                    const radius = 2;
                    editor.ctx.beginPath();
                    editor.ctx.moveTo(corner.x - squareSize/2 + radius, corner.y - squareSize/2);
                    editor.ctx.lineTo(corner.x + squareSize/2 - radius, corner.y - squareSize/2);
                    editor.ctx.arcTo(corner.x + squareSize/2, corner.y - squareSize/2, corner.x + squareSize/2, corner.y - squareSize/2 + radius, radius);
                    editor.ctx.lineTo(corner.x + squareSize/2, corner.y + squareSize/2 - radius);
                    editor.ctx.arcTo(corner.x + squareSize/2, corner.y + squareSize/2, corner.x + squareSize/2 - radius, corner.y + squareSize/2, radius);
                    editor.ctx.lineTo(corner.x - squareSize/2 + radius, corner.y + squareSize/2);
                    editor.ctx.arcTo(corner.x - squareSize/2, corner.y + squareSize/2, corner.x - squareSize/2, corner.y + squareSize/2 - radius, radius);
                    editor.ctx.lineTo(corner.x - squareSize/2, corner.y - squareSize/2 + radius);
                    editor.ctx.arcTo(corner.x - squareSize/2, corner.y - squareSize/2, corner.x - squareSize/2 + radius, corner.y - squareSize/2, radius);
                    editor.ctx.closePath();
                    
                    // Gradient fill
                    const gradient = editor.ctx.createRadialGradient(
                        corner.x - squareSize/4, corner.y - squareSize/4, 0,
                        corner.x, corner.y, squareSize
                    );
                    gradient.addColorStop(0, '#5dade2');
                    gradient.addColorStop(1, '#3498db');
                    editor.ctx.fillStyle = gradient;
                    editor.ctx.fill();
                    
                    // White border
                    editor.ctx.strokeStyle = 'white';
                    editor.ctx.lineWidth = 1.5;
                    editor.ctx.stroke();
                }
            });
        }
        
        // Draw GROUP indicator if text belongs to a group
        if (text.groupId) {
            const groupDotSize = 6;
            // Position at bottom-left of text box
            const dotX = -w/2 - 10;
            const dotY = h/2 + 10;
            
            // Purple dot indicator
            editor.ctx.beginPath();
            editor.ctx.arc(dotX, dotY, groupDotSize, 0, Math.PI * 2);
            const groupGradient = editor.ctx.createRadialGradient(dotX, dotY, 0, dotX, dotY, groupDotSize);
            groupGradient.addColorStop(0, 'rgba(155, 89, 182, 0.95)');
            groupGradient.addColorStop(1, 'rgba(142, 68, 173, 0.95)');
            editor.ctx.fillStyle = groupGradient;
            editor.ctx.fill();
            
            // White border
            editor.ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
            editor.ctx.lineWidth = 1.5;
            editor.ctx.stroke();
        }
        
        editor.ctx.restore();
        
        // Draw Angle Meter if enabled (use effective rotation for display)
        if (isSelected && editor.showAngleMeter) {
            const meterRotation = editor.getEffectiveTextRotation ? editor.getEffectiveTextRotation(text) : (text.rotation || 0);
            let degrees = Math.round(meterRotation) % 360;
            if (degrees > 180) degrees -= 360;
            if (degrees < -180) degrees += 360;
            const normalizedDegrees = degrees;
            
            editor.ctx.save();
            const fontFamily = text.fontFamily || 'Arial';
            const fontWeight = text.fontWeight || 'normal';
            const fontStyle = text.fontStyle || 'normal';
            const fontSize = parseInt(text.fontSize) || 14;
            editor.ctx.font = `${fontStyle} ${fontWeight} ${fontSize}px ${fontFamily}`;
            const metrics = editor.ctx.measureText(text.text || 'Text');
            const w = metrics.width;
            const h = fontSize;
            editor.ctx.restore();
            
            const angle = meterRotation * Math.PI / 180;
            
            // Top-right corner in local space (rotation handle position)
            const localX = w/2 + 5;
            const localY = -h/2 - 5;
            
            // Rotate to world space to get handle position
            const handleX = text.x + (localX * Math.cos(angle) - localY * Math.sin(angle));
            const handleY = text.y + (localX * Math.sin(angle) + localY * Math.cos(angle));
            
            // Calculate angle from text center to handle
            const handleAngle = Math.atan2(handleY - text.y, handleX - text.x);
            const labelOffsetDist = 25 / editor.zoom;
            const labelX = handleX + Math.cos(handleAngle) * labelOffsetDist;
            const labelY = handleY + Math.sin(handleAngle) * labelOffsetDist;
            
            editor.ctx.save();
            editor.ctx.translate(labelX, labelY);
            
            // ENHANCED: Align label with text rotation for cleaner look
            const shouldAlignWithText = Math.abs(degrees % 180) > 15 && Math.abs(degrees % 180) < 165;
            if (shouldAlignWithText) {
                editor.ctx.rotate(angle);
            }
            
            const labelText = normalizedDegrees >= 0 ? `+${normalizedDegrees}°` : `${normalizedDegrees}°`;
            editor.ctx.font = `bold ${11 / editor.zoom}px Arial`;
            const textMetrics = editor.ctx.measureText(labelText);
            
            const bgPad = 5 / editor.zoom;
            const bgW = textMetrics.width + bgPad * 2;
            const bgH = 16 / editor.zoom;
            const radius = 4 / editor.zoom;
            
            // Shadow for depth
            editor.ctx.shadowColor = 'rgba(0, 0, 0, 0.4)';
            editor.ctx.shadowBlur = 6 / editor.zoom;
            editor.ctx.shadowOffsetX = 1 / editor.zoom;
            editor.ctx.shadowOffsetY = 2 / editor.zoom;
            
            // Gradient background
            const gradient = editor.ctx.createLinearGradient(-bgW/2, -bgH/2, -bgW/2, bgH/2);
            gradient.addColorStop(0, 'rgba(46, 204, 113, 1)');
            gradient.addColorStop(1, 'rgba(39, 174, 96, 1)');
            
            // Rounded rectangle
            editor.ctx.beginPath();
            editor.ctx.moveTo(-bgW/2 + radius, -bgH/2);
            editor.ctx.lineTo(bgW/2 - radius, -bgH/2);
            editor.ctx.arcTo(bgW/2, -bgH/2, bgW/2, -bgH/2 + radius, radius);
            editor.ctx.lineTo(bgW/2, bgH/2 - radius);
            editor.ctx.arcTo(bgW/2, bgH/2, bgW/2 - radius, bgH/2, radius);
            editor.ctx.lineTo(-bgW/2 + radius, bgH/2);
            editor.ctx.arcTo(-bgW/2, bgH/2, -bgW/2, bgH/2 - radius, radius);
            editor.ctx.lineTo(-bgW/2, -bgH/2 + radius);
            editor.ctx.arcTo(-bgW/2, -bgH/2, -bgW/2 + radius, -bgH/2, radius);
            editor.ctx.closePath();
            editor.ctx.fillStyle = gradient;
            editor.ctx.fill();
            
            // Subtle border
            editor.ctx.shadowColor = 'transparent';
            editor.ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
            editor.ctx.lineWidth = 1.5 / editor.zoom;
            editor.ctx.stroke();
            
            // Text with shadow
            editor.ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
            editor.ctx.shadowBlur = 1 / editor.zoom;
            editor.ctx.shadowOffsetY = 1 / editor.zoom;
            editor.ctx.fillStyle = '#ffffff';
            editor.ctx.textAlign = 'center';
            editor.ctx.textBaseline = 'middle';
            editor.ctx.fillText(labelText, 0, 0);
        
        editor.ctx.restore();
        }
    },
    
    /**
     * Draw SSH Terminal button for a device (drawn in separate pass for top layer)
     * This ensures the button is ALWAYS on top of all other objects (text, links, etc.)
     * @param {Object} editor - TopologyEditor instance
     * @param {Object} device - Device object
     */
    drawTerminalButton(editor, device) {
        // Only draw if button position was calculated (device selected with SSH config)
        if (!device._terminalBtnPos) return;
        
        const btn = device._terminalBtnPos;
        const btnX = btn.x;
        const btnY = btn.y;
        const btnRadius = btn.radius;
        
        editor.ctx.save();
        
        // Check if mouse is hovering over button
        const isHovered = editor._hoveredTerminalBtn === device.id;
        
        // Draw button shadow
        editor.ctx.shadowColor = 'rgba(0, 0, 0, 0.4)';
        editor.ctx.shadowBlur = 6 / editor.zoom;
        editor.ctx.shadowOffsetX = 2 / editor.zoom;
        editor.ctx.shadowOffsetY = 2 / editor.zoom;
        
        // Draw button background
        editor.ctx.beginPath();
        editor.ctx.arc(btnX, btnY, btnRadius, 0, Math.PI * 2);
        editor.ctx.fillStyle = isHovered ? '#2ecc71' : '#27ae60';
        editor.ctx.fill();
        
        // Draw border
        editor.ctx.shadowColor = 'transparent';
        editor.ctx.strokeStyle = '#ffffff';
        editor.ctx.lineWidth = 2 / editor.zoom;
        editor.ctx.stroke();
        
        // Draw terminal icon (simple console/terminal shape)
        const iconSize = 8 / editor.zoom;
        editor.ctx.strokeStyle = '#ffffff';
        editor.ctx.lineWidth = 1.5 / editor.zoom;
        editor.ctx.lineCap = 'round';
        editor.ctx.lineJoin = 'round';
        
        // Terminal prompt: >_
        editor.ctx.beginPath();
        // Arrow/chevron
        editor.ctx.moveTo(btnX - iconSize * 0.6, btnY - iconSize * 0.3);
        editor.ctx.lineTo(btnX - iconSize * 0.1, btnY);
        editor.ctx.lineTo(btnX - iconSize * 0.6, btnY + iconSize * 0.3);
        editor.ctx.stroke();
        
        // Cursor underscore
        editor.ctx.beginPath();
        editor.ctx.moveTo(btnX + iconSize * 0.1, btnY + iconSize * 0.3);
        editor.ctx.lineTo(btnX + iconSize * 0.6, btnY + iconSize * 0.3);
        editor.ctx.stroke();
        
        editor.ctx.restore();
    },

};

console.log('[topology-canvas-drawing.js] CanvasDrawing loaded');
