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
        this._initBadgeClickHandlers(editor);
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

        if (!device._hostnameMismatch) {
            device._badgeWorlds = null;
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
        if (!device._terminalBtnPos) return;

        const btn = device._terminalBtnPos;
        const btnX = btn.x;
        const btnY = btn.y;
        const btnRadius = btn.radius;
        const isHovered = editor._hoveredTerminalBtn === device.id;

        const sshCfg = device.sshConfig || {};
        const lastMethod = sshCfg._lastWorkingMethod || '';
        const devMode = device._deviceMode || '';
        const isConsole = lastMethod === 'console' || lastMethod === 'virsh_console'
            || devMode === 'GI' || devMode === 'RECOVERY';

        const fillNormal = isConsole ? '#e67e22' : '#27ae60';
        const fillHover  = isConsole ? '#f39c12' : '#2ecc71';

        editor.ctx.save();

        editor.ctx.shadowColor = 'rgba(0, 0, 0, 0.4)';
        editor.ctx.shadowBlur = 6 / editor.zoom;
        editor.ctx.shadowOffsetX = 2 / editor.zoom;
        editor.ctx.shadowOffsetY = 2 / editor.zoom;

        editor.ctx.beginPath();
        editor.ctx.arc(btnX, btnY, btnRadius, 0, Math.PI * 2);
        editor.ctx.fillStyle = isHovered ? fillHover : fillNormal;
        editor.ctx.fill();

        editor.ctx.shadowColor = 'transparent';
        editor.ctx.strokeStyle = '#ffffff';
        editor.ctx.lineWidth = 2 / editor.zoom;
        editor.ctx.stroke();

        const s = 8 / editor.zoom;
        editor.ctx.strokeStyle = '#ffffff';
        editor.ctx.lineWidth = 1.5 / editor.zoom;
        editor.ctx.lineCap = 'round';
        editor.ctx.lineJoin = 'round';

        if (isConsole) {
            // Console cable icon: RJ45 connector + cable
            const top = btnY - s * 0.55;
            editor.ctx.strokeRect(btnX - s * 0.35, top, s * 0.7, s * 0.4);
            // Pins
            editor.ctx.lineWidth = 1 / editor.zoom;
            for (const dx of [-0.15, 0, 0.15]) {
                editor.ctx.beginPath();
                editor.ctx.moveTo(btnX + s * dx, top + s * 0.08);
                editor.ctx.lineTo(btnX + s * dx, top + s * 0.28);
                editor.ctx.stroke();
            }
            // Cable
            editor.ctx.lineWidth = 1.8 / editor.zoom;
            editor.ctx.beginPath();
            editor.ctx.moveTo(btnX, top + s * 0.4);
            editor.ctx.lineTo(btnX, btnY + s * 0.1);
            editor.ctx.stroke();
            // Wavy section
            editor.ctx.lineWidth = 1.2 / editor.zoom;
            editor.ctx.beginPath();
            editor.ctx.moveTo(btnX, btnY + s * 0.1);
            editor.ctx.quadraticCurveTo(btnX - s * 0.3, btnY + s * 0.3, btnX, btnY + s * 0.5);
            editor.ctx.stroke();
        } else {
            // Terminal prompt: >_
            editor.ctx.beginPath();
            editor.ctx.moveTo(btnX - s * 0.6, btnY - s * 0.3);
            editor.ctx.lineTo(btnX - s * 0.1, btnY);
            editor.ctx.lineTo(btnX - s * 0.6, btnY + s * 0.3);
            editor.ctx.stroke();
            editor.ctx.beginPath();
            editor.ctx.moveTo(btnX + s * 0.1, btnY + s * 0.3);
            editor.ctx.lineTo(btnX + s * 0.6, btnY + s * 0.3);
            editor.ctx.stroke();
        }

        editor.ctx.restore();
    },

    // =========================================================================
    // DEVICE BADGE SYSTEM
    // Three badge types: config (green), upgrade (orange), mismatch (crimson)
    // Positioned as detached perfect circles above the device
    // =========================================================================

    _BADGE_DEFS: {
        config:       { fill: '#27ae60', glow: '39,174,96'   },
        upgrade:      { fill: '#e67e22', glow: '230,126,34'  },
        upgradeFail:  { fill: '#e74c3c', glow: '231,76,60'   },
        mismatch:     { fill: '#8e44ad', glow: '142,68,173'  }
    },

    _getDeviceBadges(device) {
        const badges = [];
        if (device._activeConfigJob) {
            badges.push({ type: 'config' });
        }
        if (device._upgradeFailedJob) {
            badges.push({ type: 'upgradeFail' });
        } else if (device._activeUpgradeJob || device._upgradeInProgress) {
            badges.push({ type: 'upgrade' });
        }
        if (device._hostnameMismatch) {
            badges.push({ type: 'mismatch', dismissed: !!device._mismatchDismissed });
        }
        return badges;
    },

    _getBadgeAnchor(device) {
        const r = device.radius || 30;
        const style = device.visualStyle || 'circle';
        const gap = 10;
        switch (style) {
            case 'classic': return { x: 0, y: -(r * 0.4 + gap) };
            case 'hex':     return { x: 0, y: -(r + gap) };
            case 'server':  return { x: 0, y: -(r * 0.85 + gap) };
            case 'simple':
            case 'circle':
            default:        return { x: 0, y: -(r + gap) };
        }
    },

    drawDeviceBadges(editor) {
        this._startJobWatcher(editor);
        const devices = (editor.objects || []).filter(o => {
            if (o.type !== 'device' || o._hidden) return false;
            return o._activeConfigJob || o._activeUpgradeJob || o._upgradeInProgress || o._upgradeFailedJob || o._hostnameMismatch;
        });
        if (devices.length === 0) {
            if (editor._badgePulseTimer) {
                clearInterval(editor._badgePulseTimer);
                editor._badgePulseTimer = null;
            }
            return;
        }
        for (const device of devices) {
            const badges = this._getDeviceBadges(device);
            if (badges.length > 0) {
                this._drawBadgeRow(editor, device, badges);
            } else {
                device._badgeWorlds = null;
            }
        }
        const hasPulse = devices.some(d =>
            (d._hostnameMismatch && !d._mismatchDismissed) || d._activeConfigJob || d._activeUpgradeJob || d._upgradeInProgress || d._upgradeFailedJob
        );
        if (hasPulse && !editor._badgePulseTimer) {
            const tick = () => {
                const still = (editor.objects || []).some(o =>
                    o.type === 'device' && !o._hidden && (
                        (o._hostnameMismatch && !o._mismatchDismissed) || o._activeConfigJob || o._activeUpgradeJob || o._upgradeInProgress || o._upgradeFailedJob
                    )
                );
                if (still) {
                    editor.requestDraw?.();
                    editor._badgePulseTimer = requestAnimationFrame(tick);
                } else {
                    editor._badgePulseTimer = null;
                }
            };
            editor._badgePulseTimer = requestAnimationFrame(tick);
        }
    },

    _drawBadgeRow(editor, device, badges) {
        const z = editor.zoom;
        const badgeR = 7 / z;
        const badgeGap = 5 / z;
        const anchor = this._getBadgeAnchor(device);
        const totalWidth = badges.length * (badgeR * 2) + (badges.length - 1) * badgeGap;
        const startX = anchor.x - totalWidth / 2 + badgeR;

        editor.ctx.save();
        editor.ctx.translate(device.x, device.y);
        editor.ctx.rotate((device.rotation || 0) * Math.PI / 180);

        const rot = (device.rotation || 0) * Math.PI / 180;
        const cos = Math.cos(rot), sin = Math.sin(rot);
        device._badgeWorlds = [];

        badges.forEach((badge, i) => {
            const bx = startX + i * (badgeR * 2 + badgeGap);
            const by = anchor.y;
            const def = this._BADGE_DEFS[badge.type];
            this._drawSingleBadge(editor, bx, by, badgeR, badge, def, z);
            device._badgeWorlds.push({
                type: badge.type,
                x: device.x + cos * bx - sin * by,
                y: device.y + sin * bx + cos * by,
                r: badgeR
            });
        });

        editor.ctx.restore();
    },

    _drawSingleBadge(editor, bx, by, r, badge, def, z) {
        const isMismatch = badge.type === 'mismatch';
        const isFailed = badge.type === 'upgradeFail';
        const isActive = badge.type === 'config' || badge.type === 'upgrade';
        const dismissed = isMismatch && badge.dismissed;
        const pulse = (isMismatch && !dismissed)
            ? (0.5 + 0.5 * Math.sin(Date.now() * 0.004))
            : isFailed ? (0.5 + 0.5 * Math.sin(Date.now() * 0.005))
            : isActive ? (0.5 + 0.5 * Math.sin(Date.now() * 0.003)) : 0;

        if ((isMismatch && !dismissed) || isActive || isFailed) {
            const glowR = r * (2.2 + pulse * 0.5);
            const glow = editor.ctx.createRadialGradient(bx, by, r * 0.3, bx, by, glowR);
            glow.addColorStop(0, `rgba(${def.glow}, ${0.35 + pulse * 0.15})`);
            glow.addColorStop(1, `rgba(${def.glow}, 0)`);
            editor.ctx.beginPath();
            editor.ctx.arc(bx, by, glowR, 0, Math.PI * 2);
            editor.ctx.fillStyle = glow;
            editor.ctx.fill();
        }

        editor.ctx.save();
        editor.ctx.shadowColor = 'rgba(0, 0, 0, 0.4)';
        editor.ctx.shadowBlur = 4 / z;
        editor.ctx.shadowOffsetY = 1.5 / z;
        editor.ctx.beginPath();
        editor.ctx.arc(bx, by, r, 0, Math.PI * 2);
        editor.ctx.fillStyle = dismissed ? 'rgba(70, 70, 80, 0.4)' : def.fill;
        editor.ctx.fill();
        editor.ctx.restore();

        editor.ctx.beginPath();
        editor.ctx.arc(bx, by, r, 0, Math.PI * 2);
        editor.ctx.strokeStyle = dismissed
            ? 'rgba(255,255,255,0.1)'
            : `rgba(255,255,255,${0.5 + pulse * 0.15})`;
        editor.ctx.lineWidth = 1.6 / z;
        editor.ctx.stroke();

        const hlGrad = editor.ctx.createLinearGradient(bx, by - r, bx, by);
        hlGrad.addColorStop(0, `rgba(255,255,255,${dismissed ? 0.05 : 0.22})`);
        hlGrad.addColorStop(1, 'rgba(255,255,255,0)');
        editor.ctx.beginPath();
        editor.ctx.arc(bx, by - r * 0.12, r * 0.82, Math.PI, 0);
        editor.ctx.closePath();
        editor.ctx.fillStyle = hlGrad;
        editor.ctx.fill();

        this._drawBadgeIcon(editor, bx, by, r, badge.type, dismissed, z);
    },

    _drawBadgeIcon(editor, bx, by, r, type, dismissed, z) {
        const color = dismissed ? 'rgba(255,255,255,0.3)' : '#ffffff';
        switch (type) {
            case 'mismatch': {
                const fs = Math.round(10 / z);
                editor.ctx.font = `800 ${fs}px -apple-system, BlinkMacSystemFont, sans-serif`;
                editor.ctx.textAlign = 'center';
                editor.ctx.textBaseline = 'middle';
                if (!dismissed) {
                    editor.ctx.shadowColor = 'rgba(0,0,0,0.35)';
                    editor.ctx.shadowBlur = 2 / z;
                }
                editor.ctx.fillStyle = color;
                editor.ctx.fillText('!', bx, by + 0.3 / z);
                editor.ctx.shadowColor = 'transparent';
                editor.ctx.shadowBlur = 0;
                break;
            }
            case 'config': {
                editor.ctx.strokeStyle = color;
                editor.ctx.lineWidth = 1.2 / z;
                editor.ctx.lineCap = 'round';
                const lineLen = r * 0.5;
                const lineGap = r * 0.3;
                for (let i = -1; i <= 1; i++) {
                    editor.ctx.beginPath();
                    editor.ctx.moveTo(bx - lineLen, by + i * lineGap);
                    editor.ctx.lineTo(bx + lineLen, by + i * lineGap);
                    editor.ctx.stroke();
                }
                break;
            }
            case 'upgrade': {
                editor.ctx.strokeStyle = color;
                editor.ctx.lineWidth = 1.3 / z;
                editor.ctx.lineCap = 'round';
                editor.ctx.lineJoin = 'round';
                const aH = r * 0.42;
                const aW = r * 0.38;
                editor.ctx.beginPath();
                editor.ctx.moveTo(bx - aW, by + aH * 0.15);
                editor.ctx.lineTo(bx, by - aH);
                editor.ctx.lineTo(bx + aW, by + aH * 0.15);
                editor.ctx.stroke();
                editor.ctx.beginPath();
                editor.ctx.moveTo(bx, by - aH);
                editor.ctx.lineTo(bx, by + aH);
                editor.ctx.stroke();
                break;
            }
            case 'upgradeFail': {
                editor.ctx.strokeStyle = color;
                editor.ctx.lineWidth = 1.3 / z;
                editor.ctx.lineCap = 'round';
                editor.ctx.lineJoin = 'round';
                const ufH = r * 0.42;
                const ufW = r * 0.38;
                editor.ctx.beginPath();
                editor.ctx.moveTo(bx - ufW, by + ufH * 0.15);
                editor.ctx.lineTo(bx, by - ufH);
                editor.ctx.lineTo(bx + ufW, by + ufH * 0.15);
                editor.ctx.stroke();
                editor.ctx.beginPath();
                editor.ctx.moveTo(bx, by - ufH);
                editor.ctx.lineTo(bx, by + ufH);
                editor.ctx.stroke();
                break;
            }
        }
    },

    _hitTestAnyBadge(editor, clientX, clientY) {
        const rect = editor.canvas.getBoundingClientRect();
        const screenX = clientX - rect.left;
        const screenY = clientY - rect.top;
        const adjustedPanX = Math.round(editor.panOffset.x) + 0.5;
        const adjustedPanY = Math.round(editor.panOffset.y) + 0.5;
        const worldX = (screenX - adjustedPanX) / editor.zoom;
        const worldY = (screenY - adjustedPanY) / editor.zoom;
        const devices = (editor.objects || []).filter(
            o => o.type === 'device' && o._badgeWorlds && o._badgeWorlds.length > 0
        );
        for (const dev of devices) {
            for (const b of dev._badgeWorlds) {
                const dx = worldX - b.x, dy = worldY - b.y;
                const hitR = b.r + 4 / editor.zoom;
                if (dx * dx + dy * dy <= hitR * hitR) {
                    return { device: dev, type: b.type };
                }
            }
        }
        return null;
    },

    _initBadgeClickHandlers(editor) {
        if (editor._badgeClickBound) return;
        editor._badgeClickBound = true;
        const self = this;

        // Shared handler for both pointerdown and mousedown.
        // pointerdown fires FIRST and calls handleMouseDown internally,
        // so we must intercept it in capture phase to prevent device selection.
        const onDown = (e) => {
            const hit = self._hitTestAnyBadge(editor, e.clientX, e.clientY);
            if (hit) {
                e.stopPropagation();
                e.stopImmediatePropagation();
                e.preventDefault();
                if (window.hideDeviceSelectionToolbar) window.hideDeviceSelectionToolbar(editor);
                editor.selectedObject = null;
                editor.selectedObjects = [];
                editor._badgeClickPending = { ...hit, x: e.clientX, y: e.clientY };
            }
        };

        editor.canvas.addEventListener('pointerdown', onDown, true);
        editor.canvas.addEventListener('mousedown', onDown, true);

        const onUp = (e) => {
            const pending = editor._badgeClickPending;
            if (!pending) return;
            editor._badgeClickPending = null;
            e.stopPropagation();
            e.stopImmediatePropagation();
            e.preventDefault();
            self._handleBadgeClick(editor, pending);
        };

        editor.canvas.addEventListener('pointerup', onUp, true);
        editor.canvas.addEventListener('mouseup', onUp, true);

        const onClick = (e) => {
            if (self._hitTestAnyBadge(editor, e.clientX, e.clientY)) {
                e.stopPropagation();
                e.stopImmediatePropagation();
                e.preventDefault();
            }
        };

        editor.canvas.addEventListener('click', onClick, true);

        editor.canvas.addEventListener('mousemove', (e) => {
            const hit = self._hitTestAnyBadge(editor, e.clientX, e.clientY);
            if (hit) {
                if (!editor._badgeCursorActive) {
                    editor._badgeCursorActive = true;
                    editor._badgeCursorPrev = editor.canvas.style.cursor;
                    editor.canvas.style.cursor = 'pointer';
                }
            } else if (editor._badgeCursorActive) {
                editor._badgeCursorActive = false;
                editor.canvas.style.cursor = editor._badgeCursorPrev || '';
            }
        });
    },

    _handleBadgeClick(editor, pending) {
        const { device, type, x, y } = pending;
        switch (type) {
            case 'mismatch':
                this._showMismatchPopup(editor, device, x, y);
                break;
            case 'config':
                this._openConfigPanel(editor, device);
                break;
            case 'upgrade':
                this._openUpgradeWizard(editor, device);
                break;
            case 'upgradeFail':
                this._openFailedUpgradeDetails(editor, device);
                break;
        }
    },

    _openFailedUpgradeDetails(editor, device) {
        if (!device._upgradeFailedJob) return;
        const job = device._upgradeFailedJob;
        if (typeof ScalerGUI !== 'undefined' && ScalerGUI.showProgress) {
            ScalerGUI.showProgress(job.jobId, job.name || 'Failed upgrade', {
                upgradeDevices: job.devices || [],
                upgradeSshHosts: job.sshHosts || {},
            });
        }
    },

    _startJobWatcher(editor) {
        if (editor._jobWatcherStarted) return;
        editor._jobWatcherStarted = true;
        if (typeof ScalerAPI === 'undefined' || !ScalerAPI.getJobs) return;

        let failCount = 0;
        const BASE_INTERVAL = 3000;
        const MAX_INTERVAL = 30000;

        const poll = async () => {
            try {
                const data = await ScalerAPI.getJobs();
                failCount = 0;
                const jobs = data?.jobs || [];
                const active = jobs.filter(j =>
                    j.status !== 'completed' && j.status !== 'failed' && j.status !== 'cancelled'
                );
                const failed = jobs.filter(j =>
                    j.status === 'failed' && (j.job_type === 'upgrade' || j.job_type === 'wait_and_upgrade'
                        || /upgrade|image/i.test(j.job_name || ''))
                );
                const deviceMap = {};
                for (const job of active) {
                    const isUpgrade = /upgrade|image|build/i.test(job.job_name || '')
                        || job.job_type === 'build_monitor';
                    const dids = [];
                    if (job.device_id) dids.push(job.device_id);
                    if (Array.isArray(job.devices)) {
                        for (const d of job.devices) { if (d && !dids.includes(d)) dids.push(d); }
                    }
                    for (const did of dids) {
                        if (!deviceMap[did]) deviceMap[did] = {};
                        if (isUpgrade) {
                            deviceMap[did].upgrade = { jobId: job.job_id, name: job.job_name || 'Upgrade', phase: job.phase || job.status || '', percent: job.percent || 0 };
                        } else {
                            deviceMap[did].config = { jobId: job.job_id, name: job.job_name || 'Config push', phase: job.phase || job.status || '', percent: job.percent || 0 };
                        }
                    }
                }
                const failedDevMap = {};
                let dismissedKeys = [];
                try {
                    const raw = localStorage.getItem('scaler_dismissed_upgrade_failures');
                    const parsed = JSON.parse(raw || '[]');
                    dismissedKeys = Array.isArray(parsed) ? parsed : [];
                } catch (_) { dismissedKeys = []; }
                const isDismissed = (jid, did) => dismissedKeys.includes(`${jid}:${did}`);
                for (const job of failed) {
                    const jid = job.job_id || '';
                    const dids = [];
                    if (job.device_id) dids.push(job.device_id);
                    if (Array.isArray(job.devices)) {
                        for (const d of job.devices) { if (d && !dids.includes(d)) dids.push(d); }
                    }
                    const ds = job.device_state || {};
                    for (const did of dids) {
                        const devState = ds[did] || {};
                        if (devState.status === 'failed' || devState.phase === 'interrupted' || job.status === 'failed') {
                            if (jid && isDismissed(jid, did)) continue;
                            failedDevMap[did] = {
                                jobId: jid,
                                name: job.job_name || 'Upgrade',
                                phase: devState.phase || job.phase || 'failed',
                                devices: job.devices || [],
                                sshHosts: job.ssh_hosts || {},
                            };
                        }
                    }
                }
                let changed = false;
                for (const obj of (editor.objects || [])) {
                    if (obj.type !== 'device') continue;
                    const entry = deviceMap[obj.label] || null;
                    const newCfg = entry?.config || null;
                    const newUpg = entry?.upgrade || null;
                    const newFail = failedDevMap[obj.label] || null;
                    if (!!obj._activeConfigJob !== !!newCfg || !!obj._activeUpgradeJob !== !!newUpg || !!obj._upgradeFailedJob !== !!newFail) changed = true;
                    obj._activeConfigJob = newCfg;
                    obj._activeUpgradeJob = newUpg;
                    obj._upgradeFailedJob = newFail;
                }
                if (Object.keys(failedDevMap).length === 0) {
                    const fBanner = document.getElementById('upgrade-failed-banner');
                    if (fBanner) fBanner.remove();
                }
                if (changed && editor.requestDraw) editor.requestDraw();
            } catch (_) {
                failCount++;
            }
            const delay = Math.min(BASE_INTERVAL * Math.pow(2, failCount), MAX_INTERVAL);
            this._jobWatcherTimeout = setTimeout(poll, delay);
        };
        poll();
    },

    _stopJobWatcher() {
        if (this._jobWatcherInterval) {
            clearInterval(this._jobWatcherInterval);
            this._jobWatcherInterval = null;
        }
        if (this._jobWatcherTimeout) {
            clearTimeout(this._jobWatcherTimeout);
            this._jobWatcherTimeout = null;
        }
    },

    _openConfigPanel(editor, device) {
        if (!device._activeConfigJob) return;
        const job = device._activeConfigJob;
        if (typeof ScalerGUI !== 'undefined' && ScalerGUI.showProgress) {
            ScalerGUI.showProgress(job.jobId, job.name);
        }
    },

    _openUpgradeWizard(editor, device) {
        if (!device._activeUpgradeJob) return;
        const job = device._activeUpgradeJob;
        if (typeof ScalerGUI !== 'undefined' && ScalerGUI._showRunningUpgradeProgress) {
            ScalerGUI._showRunningUpgradeProgress({
                job_id: job.jobId,
                job_name: job.name,
                devices: job.devices || [],
                ssh_hosts: job.sshHosts || {},
            });
        } else if (typeof ScalerGUI !== 'undefined' && ScalerGUI.showProgress) {
            ScalerGUI.showProgress(job.jobId, job.name);
        }
    },

    _showMismatchPopup(editor, device, screenX, screenY) {
        this._hideMismatchPopup();
        if (window.hideDeviceSelectionToolbar) window.hideDeviceSelectionToolbar(editor);
        const identity = device._identity;
        const cfgHost = identity?.config_hostname || device._configHostname || 'unknown';
        const canvasLabel = (device.label || '').trim() || 'unknown';
        const sshHost = device.sshConfig?.host || device.sshConfig?.hostBackup || '';
        const hasSsh = !!sshHost;
        const isDark = editor.darkMode;

        const accentColor = '#8e44ad';
        const accentLight = isDark ? '#c39bd3' : '#6c3483';

        const popup = document.createElement('div');
        popup.id = 'mismatch-badge-popup';
        popup.style.cssText = `
            position: fixed; left: ${screenX + 12}px; top: ${screenY - 12}px;
            z-index: 20000; min-width: 300px; max-width: 360px;
            background: ${isDark ? '#1e1e30' : '#ffffff'};
            color: ${isDark ? '#d8d8e8' : '#1a1a2e'};
            border: 1px solid ${isDark ? 'rgba(142,68,173,0.4)' : 'rgba(142,68,173,0.5)'};
            border-radius: 10px; overflow: hidden;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            box-shadow: 0 8px 28px rgba(0,0,0,0.35);
            pointer-events: auto;
        `;

        const hdrBg = isDark ? 'rgba(142,68,173,0.12)' : 'rgba(142,68,173,0.06)';
        const mutedColor = isDark ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.45)';
        const btnBase = `padding:7px 0;font-size:12px;border-radius:6px;cursor:pointer;font-weight:500;
            border:none;width:100%;text-align:left;padding-left:12px;padding-right:12px;`;

        popup.innerHTML = `
            <div style="padding:10px 14px 8px;background:${hdrBg};border-bottom:1px solid ${isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'};">
                <div style="font-weight:700;font-size:13px;color:${accentColor};margin-bottom:6px;">Name Mismatch</div>
                <div style="font-size:11px;color:${mutedColor};line-height:1.5;">
                    The canvas label does not match the hostname<br>configured on the device's running config.
                </div>
            </div>
            <div style="padding:10px 14px 6px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                    <div style="font-size:11px;">
                        <span style="color:${mutedColor};">Canvas:</span>
                        <strong style="color:${accentLight};margin-left:4px;">${canvasLabel}</strong>
                    </div>
                    <div style="font-size:16px;color:${mutedColor};padding:0 8px;">!=</div>
                    <div style="font-size:11px;">
                        <span style="color:${mutedColor};">Device:</span>
                        <strong style="color:${accentLight};margin-left:4px;">${cfgHost}</strong>
                    </div>
                </div>
                <div style="display:flex;flex-direction:column;gap:4px;">
                    <button type="button" data-act="rename-canvas" style="${btnBase}
                        background:${isDark ? 'rgba(142,68,173,0.15)' : 'rgba(142,68,173,0.08)'};
                        color:${accentLight};
                    ">Rename canvas label to <strong>${cfgHost}</strong></button>
                    <button type="button" data-act="rename-device" ${!hasSsh ? 'disabled' : ''} style="${btnBase}
                        background:${isDark ? 'rgba(52,152,219,0.12)' : 'rgba(52,152,219,0.08)'};
                        color:${hasSsh ? (isDark ? '#7ec8e3' : '#1a6fa0') : mutedColor};
                        ${!hasSsh ? 'opacity:0.5;cursor:not-allowed;' : ''}
                    ">Change device hostname to <strong>${canvasLabel}</strong>${!hasSsh ? ' <span style="font-size:10px;">(no SSH)</span>' : ''}</button>
                    <button type="button" data-act="dismiss" style="${btnBase}
                        background:transparent;color:${mutedColor};
                    ">Dismiss</button>
                </div>
            </div>
        `;

        const self = this;

        popup.querySelector('[data-act="rename-canvas"]').onclick = (ev) => {
            ev.stopPropagation();
            if (cfgHost && cfgHost !== 'unknown') {
                if (editor.applyRename) {
                    editor.applyRename(device, cfgHost);
                } else {
                    if (editor.saveState) editor.saveState();
                    device.label = cfgHost;
                    if (window.checkDeviceMismatchLive) window.checkDeviceMismatchLive(device);
                    editor.draw();
                }
            }
            self._hideMismatchPopup();
        };

        const renameDeviceBtn = popup.querySelector('[data-act="rename-device"]');
        if (hasSsh) {
            renameDeviceBtn.onclick = (ev) => {
                ev.stopPropagation();
                self._pushHostnameChange(editor, device, canvasLabel, sshHost, popup);
            };
        }

        popup.querySelector('[data-act="dismiss"]').onclick = (ev) => {
            ev.stopPropagation();
            device._mismatchDismissed = true;
            editor.draw();
            self._hideMismatchPopup();
        };

        popup.querySelectorAll('button:not(:disabled)').forEach(btn => {
            btn.onmouseenter = () => { btn.style.filter = 'brightness(1.15)'; };
            btn.onmouseleave = () => { btn.style.filter = ''; };
        });

        document.body.appendChild(popup);
        const br = popup.getBoundingClientRect();
        if (br.right > window.innerWidth) popup.style.left = `${screenX - br.width - 12}px`;
        if (br.bottom > window.innerHeight) popup.style.top = `${screenY - br.height - 12}px`;
        setTimeout(() => {
            const outsideClick = (ev) => {
                if (!popup.contains(ev.target)) {
                    self._hideMismatchPopup();
                    document.removeEventListener('mousedown', outsideClick, true);
                }
            };
            document.addEventListener('mousedown', outsideClick, true);
        }, 80);
    },

    async _pushHostnameChange(editor, device, newHostname, sshHost, popup) {
        const btn = popup.querySelector('[data-act="rename-device"]');
        btn.disabled = true;
        btn.style.opacity = '0.6';
        btn.style.cursor = 'wait';
        const self = this;
        const deviceId = device.label || device.deviceSerial || device.serial || '';

        btn.innerHTML = '<span style="opacity:0.7;">Changing hostname...</span>';
        try {
            const result = await ScalerAPI.setHostname(deviceId, newHostname, sshHost);
            if (result?.status === 'error') {
                btn.innerHTML = `<span style="color:#e74c3c;">Failed: ${result.commit_output || 'Push error'}</span>`;
                btn.disabled = false;
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
                return;
            }
            device._configHostname = newHostname;
            if (device._identity) device._identity.config_hostname = newHostname;
            if (window.checkDeviceMismatchLive) window.checkDeviceMismatchLive(device);
            editor.draw();
            if (device._hostnameMismatch) {
                btn.innerHTML = '<span style="color:#8e44ad;">Device renamed, but canvas label still differs</span>';
            } else {
                btn.innerHTML = '<span style="color:#27ae60;">Hostname changed -- names match</span>';
            }
            btn.style.opacity = '1';
            setTimeout(() => self._hideMismatchPopup(), 1500);
            if (deviceId && window.DeviceMonitor?.refreshDevice) {
                setTimeout(() => window.DeviceMonitor.refreshDevice(deviceId, true), 1500);
            }
        } catch (err) {
            btn.innerHTML = `<span style="color:#e74c3c;">Error: ${err.message || 'Connection failed'}</span>`;
            btn.disabled = false;
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
        }
    },

    _hideMismatchPopup() {
        const existing = document.getElementById('mismatch-badge-popup');
        if (existing) existing.remove();
    },
};

console.log('[topology-canvas-drawing.js] CanvasDrawing loaded');
