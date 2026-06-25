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

    // 2026-05-12 [split-color refine]: trace the visible-shape path of a
    // device into the current canvas path (assumes the caller has
    // already translated + rotated into the device-local frame). Used
    // to clip the seam-bevel pass so the highlight/shadow never leaks
    // outside the device outline. Uses the same shape-type discrimination
    // as the selection-ring code (circle | rectangle | hexagon | classic).
    _traceDeviceShapePath(editor, device, bounds) {
        const r = device.radius || 30;
        editor.ctx.beginPath();
        switch (bounds && bounds.type) {
            case 'classic': {
                const hw = bounds.width / 2;
                const top = bounds.top;
                const bottom = bounds.bottom;
                editor.ctx.rect(-hw, top, hw * 2, bottom - top);
                break;
            }
            case 'rectangle': {
                const hw = bounds.width / 2;
                const hh = bounds.height / 2;
                editor.ctx.rect(-hw, -hh, hw * 2, hh * 2);
                break;
            }
            case 'hexagon': {
                const hexR = r * 0.65;
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
                editor.ctx.arc(0, 0, r, 0, Math.PI * 2);
                break;
        }
    },

    // 2026-05-12 [split-color refine]: paint the paper-fold seam bevel
    // along the split midline. The bevel is two thin rects clipped to
    // the device shape: one slightly LIGHTER on the left side of the
    // seam (a soft highlight) and one slightly DARKER on the right.
    // The total bevel width is ~2 screen pixels regardless of zoom.
    //
    // Why this treatment (vs. a single divider line or a gradient
    // smear)? A single hairline can look graphic-design-flat over
    // similar colors and disappears entirely over high-contrast joins.
    // A gradient blend muddles the colors. A 1px-light + 1px-dark
    // paper-fold suggests a physical fold so the eye reads the seam
    // as intentional even when both halves are visually similar, and
    // it scales down to invisible at extreme zoom-out without
    // breaking the silhouette.
    _paintSplitSeamBevel(editor, device, bounds) {
        if (!device || !editor || !editor.ctx) return;
        const rotation = (device.rotation || 0) * Math.PI / 180;
        const halfH = Math.max((bounds && bounds.height) ? bounds.height / 2 : device.radius,
                               device.radius || 30) + (device.radius || 30);
        const zoom = (editor.zoom && editor.zoom > 0) ? editor.zoom : 1;
        // Width of each side of the bevel. Slightly fattened in screen
        // space to survive subpixel rounding on HiDPI displays.
        const bevelW = 1 / zoom;

        // Color stack: in dark mode use a brighter highlight + softer
        // shadow; in light mode invert the alpha balance.
        const highlightAlpha = editor.darkMode ? 0.45 : 0.4;
        const shadowAlpha = editor.darkMode ? 0.35 : 0.28;

        editor.ctx.save();
        editor.ctx.translate(device.x, device.y);
        editor.ctx.rotate(rotation);
        // Clip to the device shape so the seam never paints over
        // background / links / neighbouring devices.
        this._traceDeviceShapePath(editor, device, bounds);
        editor.ctx.clip();

        // LEFT side of seam: 1px wide highlight, just inside the left
        // half. Pre-multiplied by globalAlpha so we still get crisp
        // anti-aliased edges from canvas rasteriser.
        editor.ctx.fillStyle = `rgba(255, 255, 255, ${highlightAlpha})`;
        editor.ctx.fillRect(-bevelW, -halfH, bevelW, halfH * 2);

        // RIGHT side of seam: 1px wide shadow, just inside the right
        // half. The two together form the paper-fold suggestion.
        editor.ctx.fillStyle = `rgba(0, 0, 0, ${shadowAlpha})`;
        editor.ctx.fillRect(0, -halfH, bevelW, halfH * 2);

        editor.ctx.restore();
    },

    drawDevice(editor, device, unused = false, skipLabelArg = false) {
        this._initBadgeClickHandlers(editor);
        const isSelected = editor.selectedObject === device || editor.selectedObjects.includes(device);
        const style = device.visualStyle || 'circle';

        // Check if multiple objects are selected - skip individual handles in multi-select
        const isMultiSelect = editor.selectedObjects.length > 1;

        // 2026-05-12 [split-color]: when a device has BOTH colorLeft and
        // colorRight set, render the body as two halves split along the
        // device's local vertical midline. Implementation strategy:
        //
        //   1. Pass 1: clip to the LEFT half of the device's local
        //      bounding box (in the device's rotated frame), set
        //      `device._renderColorOverride = device.colorLeft`, and
        //      dispatch the normal per-shape draw function. All fills,
        //      gradients, borders, and labels stroke onto the clipped
        //      canvas and only the LEFT half is painted.
        //
        //   2. Pass 2: same procedure with the RIGHT half clip and
        //      `colorRight`. Borders and labels at the seam x=device.x
        //      get drawn twice with identical pixel positions; both
        //      passes write the same border colour, so this is visually
        //      idempotent (no double-strokes, no anti-aliasing seam).
        //
        //   3. The override is cleared at the end so any later code
        //      that reads `_safeDeviceColor(device)` (selection ring,
        //      label, copy-style helpers) sees the legacy
        //      `device.color` again.
        //
        // For solid (non-split) mode the path is unchanged -- we just
        // call the per-shape draw function directly.
        const _splitMode = (typeof device.colorLeft === 'string' && device.colorLeft.trim().length > 0) &&
                           (typeof device.colorRight === 'string' && device.colorRight.trim().length > 0);

        const _drawShape = () => {
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
        };

        if (_splitMode) {
            // Compute a clip rectangle in the device's local (rotated)
            // frame that comfortably contains the entire shape. We use
            // getDeviceBounds() to get accurate shape-aware width/height
            // and pad generously so 3D depth, shadow offsets, and the
            // selection ring still fall inside the clip when they should.
            const bounds = (typeof editor.getDeviceBounds === 'function')
                ? editor.getDeviceBounds(device)
                : { width: device.radius * 2, height: device.radius * 2 };
            const r = device.radius || 30;
            const halfW = Math.max(bounds.width / 2, r) + r;
            const halfH = Math.max(bounds.height / 2, r) + r;
            const rotation = (device.rotation || 0) * Math.PI / 180;

            // Pass 1: LEFT half
            editor.ctx.save();
            editor.ctx.translate(device.x, device.y);
            editor.ctx.rotate(rotation);
            editor.ctx.beginPath();
            editor.ctx.rect(-halfW, -halfH, halfW, halfH * 2);
            editor.ctx.clip();
            editor.ctx.rotate(-rotation);
            editor.ctx.translate(-device.x, -device.y);
            device._renderColorOverride = device.colorLeft;
            _drawShape();
            editor.ctx.restore();

            // Pass 2: RIGHT half
            editor.ctx.save();
            editor.ctx.translate(device.x, device.y);
            editor.ctx.rotate(rotation);
            editor.ctx.beginPath();
            editor.ctx.rect(0, -halfH, halfW, halfH * 2);
            editor.ctx.clip();
            editor.ctx.rotate(-rotation);
            editor.ctx.translate(-device.x, -device.y);
            device._renderColorOverride = device.colorRight;
            _drawShape();
            editor.ctx.restore();

            device._renderColorOverride = null;

            // 2026-05-12 [split-color refine]: paint a subtle "paper-fold"
            // bevel along the seam so the join reads cleanly even when
            // both halves are close in luminance. A 1px-ish lighter line
            // on the LEFT side of the seam plus a 1px-ish darker line on
            // the RIGHT side suggests a fold without a hard divider.
            // Bevel width scales with zoom so it stays visually consistent
            // (~1 screen px per side). The bevel is clipped to the
            // device's shape (using `getDeviceBounds` type) so it never
            // leaks into the link/canvas area beneath the device.
            this._paintSplitSeamBevel(editor, device, bounds);
        } else {
            _drawShape();
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
                const rotTextSize = editor.getScreenStableFontSize ? editor.getScreenStableFontSize(10, 11) : (10 / editor.zoom);
                const rotTextGap = editor.getScreenStableStrokeWidth ? editor.getScreenStableStrokeWidth(8, 8) : (8 / editor.zoom);
                editor.ctx.font = `${rotTextSize}px Arial`;
                editor.ctx.fillStyle = '#27ae60';
                editor.ctx.textAlign = 'center';
                editor.ctx.textBaseline = 'middle';
                editor.ctx.fillText(`${rotationDegrees}°`, handleX, handleY - arcRadius - rotTextGap);
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
                const angleMeterSize = editor.getScreenStableFontSize
                    ? editor.getScreenStableFontSize(11, 11)
                    : (11 / editor.zoom);
                editor.ctx.font = `bold ${angleMeterSize}px Arial`;
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
        
        // Terminal button position calculation (actual drawing is in separate pass for top layer)
        // Always show on selected devices so user can click to connect or configure SSH
        // MULTI-SELECT: Skip terminal button when multiple objects selected
        if (isSelected && !isMultiSelect) {
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

    _paintDeviceLabelScreenContent(editor, device, label, labelY, fontSize, fontFamily, fontWeight, strokeColor, strokeWidth, textColor) {
        const zoom = Math.max(0.05, Number(editor.zoom) || 1);
        if (zoom >= 1.05) return false;
        const dpr = Math.max(1, Number(editor.dpr) || window.devicePixelRatio || 1);
        const sharpPan = typeof editor.getSharpPanOffset === 'function'
            ? editor.getSharpPanOffset()
            : { x: Math.round(editor.panOffset?.x || 0), y: Math.round(editor.panOffset?.y || 0) };
        const snapCss = (value) => Math.round((Number(value) || 0) * dpr) / dpr;
        const screenX = snapCss(sharpPan.x + (device.x || 0) * zoom);
        const screenY = snapCss(sharpPan.y + (device.y || 0) * zoom);
        const screenFontSize = Math.max(1, fontSize * zoom);
        const screenLabelY = snapCss(labelY * zoom);

        editor.ctx.save();
        editor.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        if (typeof editor.configureCanvasQuality === 'function') {
            editor.configureCanvasQuality(editor.ctx, { smoothing: false, textRendering: 'geometricPrecision' });
        } else {
            editor.ctx.imageSmoothingEnabled = false;
            editor.ctx.lineJoin = 'round';
            editor.ctx.lineCap = 'round';
        }
        editor.ctx.translate(screenX, screenY);
        editor.ctx.rotate((device.rotation || 0) * Math.PI / 180);
        editor.ctx.font = `${fontWeight} ${screenFontSize}px ${fontFamily}`;
        editor.ctx.textAlign = 'center';
        editor.ctx.textBaseline = 'middle';
        if (strokeColor) {
            editor.ctx.lineWidth = Math.max(strokeWidth * zoom, 1 / dpr);
            editor.ctx.strokeStyle = strokeColor;
            editor.ctx.lineJoin = 'round';
            editor.ctx.lineCap = 'round';
            editor.ctx.miterLimit = 2;
            editor.ctx.strokeText(label, 0, screenLabelY);
        }
        editor.ctx.fillStyle = textColor;
        editor.ctx.fillText(label, 0, screenLabelY);
        editor.ctx.restore();
        return true;
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
        
        // Use custom labelSize if set, otherwise calculate based on radius
        // ENHANCED: Scale label size more with device size (0.5 factor, max 36px)
        const baseFontSize = device.labelSize || Math.max(12, Math.min(device.radius * 0.5, 36));
        const fontSize = editor.getScreenStableFontSize
            ? editor.getScreenStableFontSize(baseFontSize, 11)
            : baseFontSize;

        // LOD cull: at extreme zoom-out a 3px-tall stroke-and-fill label is
        // illegible and just adds visual noise + draw cost during pan. Skip
        // it entirely once the rendered glyph would be smaller than the
        // outline stroke width (~3 screen px). This stays under the soft
        // floor so labels still appear at moderately low zoom (~0.18+ for
        // typical labelSize=16) -- only the truly-too-tiny cases are culled.
        const renderedScreenPx = fontSize * (editor.zoom || 1);
        if (renderedScreenPx < 3) {
            return;
        }

        // Draw device label - rotated and scaled with device
        editor.ctx.save();
        editor.ctx.translate(device.x, device.y);
        editor.ctx.rotate((device.rotation || 0) * Math.PI / 180);
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
            
            const baseStrokeWidth = editor.darkMode
                ? Math.max(2.4, fontSize * 0.16)
                : Math.max(2.8, fontSize * 0.18);
            const strokeWidth = editor.getScreenStableStrokeWidth
                ? editor.getScreenStableStrokeWidth(baseStrokeWidth, 1.4)
                : baseStrokeWidth;
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

            // 2026-05-12 [split-color refine]: in split mode the seam
            // introduces a high-contrast transition directly under
            // labels that sit ON the device body (circle / default
            // styles). The per-letter outline alone can read as
            // "half-haloed" when one side of the device is light and
            // the other is dark. Paint a faint rounded-rect backdrop
            // under the label in split mode so the text reads as a
            // single coherent label across the join. We only do this
            // when the label is over the body (NOT labelBelow) -- below-
            // body labels sit on the canvas background and already
            // benefit from the existing outline.
            const _splitModeLabel = (typeof device.colorLeft === 'string' && device.colorLeft.trim().length > 0) &&
                                    (typeof device.colorRight === 'string' && device.colorRight.trim().length > 0);
            if (_splitModeLabel && !labelBelow) {
                const prevFont = editor.ctx.font;
                editor.ctx.font = `${fontWeight} ${fontSize}px ${fontFamily}`;
                const tw = editor.ctx.measureText(label).width;
                editor.ctx.font = prevFont;
                const padX = Math.max(3, fontSize * 0.22);
                const padY = Math.max(2, fontSize * 0.14);
                const bgW = tw + padX * 2;
                const bgH = fontSize + padY * 2;
                const bgR = Math.max(2, fontSize * 0.20);
                // Pick the backdrop tone that contrasts with the text:
                // light text -> navy-deep backdrop, dark text -> cloud.
                const textLum = this._luminance(textColor);
                const bgFill = textLum > 0.5
                    ? 'rgba(13, 27, 42, 0.55)'   // --dn-navy-deep @ 55%
                    : 'rgba(240, 244, 248, 0.62)'; // --dn-cloud @ 62%
                editor.ctx.save();
                editor.ctx.fillStyle = bgFill;
                if (editor.ctx.roundRect) {
                    editor.ctx.beginPath();
                    editor.ctx.roundRect(-bgW / 2, labelY - bgH / 2, bgW, bgH, bgR);
                    editor.ctx.fill();
                } else {
                    editor.ctx.fillRect(-bgW / 2, labelY - bgH / 2, bgW, bgH);
                }
                editor.ctx.restore();
            }

            const paintedLabelInScreenSpace = this._paintDeviceLabelScreenContent(
                editor, device, label, labelY, fontSize, fontFamily, fontWeight, strokeColor, strokeWidth, textColor
            );
            if (!paintedLabelInScreenSpace) {
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

            // Mode badge: only alert when the device is in a non-DNOS mode.
            // DNOS is the normal operating state and should not appear as an
            // extra canvas label on newly onboarded devices.
            if (renderedScreenPx >= 8) {
                const _devMode = (device._deviceMode || '').toUpperCase();
                if (_devMode === 'GI' || _devMode === 'RECOVERY') {
                    const badgeFont = Math.max(7, Math.min(fontSize * 0.55, 12));
                    const badgeY = labelBelow
                        ? labelY + fontSize * 0.85
                        : -fontSize * 0.85;
                    const padX = badgeFont * 0.55;
                    const padY = badgeFont * 0.30;
                    editor.ctx.font = `700 ${badgeFont}px ${fontFamily}`;
                    const tw = editor.ctx.measureText(_devMode).width;
                    const bgColor = _devMode === 'GI' ? '#f39c12' : '#e74c3c';
                    const rx = Math.max(2, badgeFont * 0.35);
                    const w = tw + padX * 2;
                    const h = badgeFont + padY * 2;
                    editor.ctx.beginPath();
                    if (editor.ctx.roundRect) {
                        editor.ctx.roundRect(-w / 2, badgeY - h / 2, w, h, rx);
                    } else {
                        editor.ctx.rect(-w / 2, badgeY - h / 2, w, h);
                    }
                    editor.ctx.fillStyle = bgColor;
                    editor.ctx.fill();
                    editor.ctx.fillStyle = '#ffffff';
                    editor.ctx.textAlign = 'center';
                    editor.ctx.textBaseline = 'middle';
                    editor.ctx.fillText(_devMode, 0, badgeY);
                }
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

        // Eraser geometry must mirror the rendered TB exactly so the link
        // line is hidden in lockstep with the text background. Resolve via
        // getTextEffectiveBounds: that single source of truth honours
        // edge-stretched manual width/height + word-wrap, while still
        // returning auto-measured glyph bounds for legacy auto-size labels.
        // Polish + QA pass 2026-05-12 -- previously used raw measureText
        // which produced a too-narrow eraser if the operator had stretched
        // an attached label.
        let w;
        let h;
        if (window.ObjectDetection && window.ObjectDetection.getTextEffectiveBounds) {
            const bounds = window.ObjectDetection.getTextEffectiveBounds(editor, textObj);
            w = bounds.w;
            h = bounds.h;
        } else {
            const fontStyle = textObj.fontStyle || 'normal';
            const fontWeight = textObj.fontWeight || 'normal';
            const fontFamily = textObj.fontFamily || 'Arial, sans-serif';
            const requestedFontSize = Number(textObj.fontSize) || 14;
            const displayFontSize = editor.getDprSnappedFontSize
                ? editor.getDprSnappedFontSize(requestedFontSize)
                : requestedFontSize;
            editor.ctx.font = `${fontStyle} ${fontWeight} ${displayFontSize}px ${fontFamily}`;
            const metrics = editor.ctx.measureText(textObj.text || 'Text');
            w = metrics.width;
            h = parseInt(displayFontSize) || 14;
        }
        
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

    _normalizeTextBackgroundOpacity(value) {
        let opacity = value;
        if (opacity === undefined) {
            opacity = 0.95;
        } else if (opacity > 1) {
            opacity = opacity / 100;
        }
        opacity = Number(opacity);
        return Number.isFinite(opacity) ? Math.max(0, Math.min(1, opacity)) : 0.95;
    },

    _createTextRasterCanvas(width, height) {
        if (typeof OffscreenCanvas !== 'undefined') {
            return new OffscreenCanvas(width, height);
        }
        if (typeof document === 'undefined') return null;
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        return canvas;
    },

    _getTextRasterScale(editor) {
        const zoom = Math.max(0.05, Number(editor.zoom) || 1);
        const dpr = Math.max(1, Number(editor.dpr) || 1);
        const destinationScale = zoom * dpr;
        const supersample = destinationScale < 3 ? 2 : 1.25;
        const scale = Math.max(destinationScale, destinationScale * supersample);
        // Keep the offscreen cache high-DPI without letting one giant TB allocate
        // a huge bitmap. Geometry still comes from the measured world box.
        return Math.max(1, Math.min(8, Math.ceil(scale * 64) / 64));
    },

    _getTextRasterCache(editor) {
        if (!editor._textRasterCache) {
            editor._textRasterCache = new Map();
        }
        return editor._textRasterCache;
    },

    _pruneTextRasterCache(cache) {
        const MAX_ENTRIES = 220;
        const MAX_PIXELS = 24_000_000;
        let pixels = 0;
        for (const entry of cache.values()) {
            pixels += entry.pixels || 0;
        }
        while (cache.size > MAX_ENTRIES || pixels > MAX_PIXELS) {
            const firstKey = cache.keys().next().value;
            if (firstKey === undefined) break;
            const entry = cache.get(firstKey);
            pixels -= entry?.pixels || 0;
            cache.delete(firstKey);
        }
    },

    _paintTextVectorContent(editor, ctx, text, paint) {
        if (paint.shouldDrawBackground) {
            ctx.save();
            ctx.globalAlpha = paint.backgroundOpacity;
            ctx.fillStyle = paint.bgColor;
            ctx.fillRect(
                -paint.w / 2 - paint.padding,
                -paint.h / 2 - paint.padding,
                paint.w + paint.padding * 2,
                paint.h + paint.padding * 2
            );
            ctx.restore();
        }

        ctx.font = paint.font;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        paint.lines.forEach((line, index) => {
            const y = paint.startY + index * paint.lineHeight;

            if (text.showBorder && text.borderWidth > 0) {
                ctx.strokeStyle = text.borderColor || '#0066FA';
                ctx.lineWidth = editor.getScreenStableStrokeWidth
                    ? editor.getScreenStableStrokeWidth(text.borderWidth || 2, 1.2)
                    : (text.borderWidth || 2);
                ctx.lineJoin = 'round';
                ctx.miterLimit = 2;
                ctx.strokeText(line || ' ', 0, y);
            } else if (text.strokeWidth && text.strokeWidth > 0) {
                ctx.strokeStyle = text.strokeColor || '#000000';
                ctx.lineWidth = editor.getScreenStableStrokeWidth
                    ? editor.getScreenStableStrokeWidth(text.strokeWidth || 2, 1.2)
                    : (text.strokeWidth || 2);
                ctx.lineJoin = 'round';
                ctx.miterLimit = 2;
                ctx.strokeText(line || ' ', 0, y);
            }

            if (paint.textColorOverride) {
                ctx.fillStyle = paint.textColorOverride;
            } else if (paint.shouldDrawBackground && paint.bgColor && paint.bgColor !== 'transparent') {
                ctx.fillStyle = this._contrastColorForBg(editor, text.color, paint.bgColor);
            } else {
                ctx.fillStyle = editor.adjustColorForMode(text.color);
            }
            ctx.fillText(line || ' ', 0, y);
        });
    },

    _getGeneratedLabelFontSize(editor, worldSize, minScreenPx = 11) {
        const size = Number(worldSize) || minScreenPx;
        const zoom = Math.max(0.05, Number(editor.zoom) || 1);
        const naturalScreen = size * zoom;
        if (naturalScreen >= minScreenPx) return size;
        const targetWorld = minScreenPx / zoom;
        // Generated labels are system annotations, not user-placed geometry:
        // allow more inflation than regular TBs so the architecture is readable
        // from the default generated-topology view.
        return Math.min(targetWorld, size * 3.0);
    },

    /**
     * Word-wrap text content into lines that each fit inside `maxWidth`
     * (in world pixels) given the font currently set on `ctx`. Mirrors the
     * inline text-editor's `white-space: pre-wrap; word-wrap: break-word`
     * behaviour: explicit \n always breaks, words wrap on whitespace, and
     * a single word that is wider than maxWidth is broken character-by-
     * character (otherwise a long URL would overflow the bbox forever).
     *
     * Used by drawText when the text box has been resized from its edges
     * (manual-size mode). Auto-size text boxes do not wrap -- they
     * preserve the legacy "split on \n only" rendering.
     */
    _wrapTextLinesToWidth(ctx, content, maxWidth) {
        const out = [];
        if (!Number.isFinite(maxWidth) || maxWidth <= 0) {
            return content.split('\n');
        }
        const sourceLines = String(content).split('\n');
        for (const source of sourceLines) {
            if (source.length === 0) {
                out.push('');
                continue;
            }
            // Whitespace-preserving word split: every run of non-whitespace
            // becomes a "word", every run of whitespace is appended onto the
            // current line. This stops "Hello world" from collapsing its
            // space when re-emitted.
            const tokens = source.match(/\S+|\s+/g) || [source];
            let current = '';
            for (const token of tokens) {
                const candidate = current + token;
                if (ctx.measureText(candidate).width <= maxWidth) {
                    current = candidate;
                    continue;
                }
                // candidate overflows. If the failing token is whitespace
                // we drop it (line-end space) and start fresh.
                if (/^\s+$/.test(token)) {
                    if (current.length > 0) {
                        out.push(current);
                        current = '';
                    }
                    continue;
                }
                // The token is a word that pushes us past maxWidth.
                if (current.length > 0) {
                    out.push(current);
                    current = '';
                }
                // If the lone word still does not fit, character-break it.
                if (ctx.measureText(token).width > maxWidth) {
                    let chunk = '';
                    for (const ch of token) {
                        if (ctx.measureText(chunk + ch).width <= maxWidth || chunk.length === 0) {
                            chunk += ch;
                        } else {
                            out.push(chunk);
                            chunk = ch;
                        }
                    }
                    current = chunk;
                } else {
                    current = token;
                }
            }
            out.push(current);
        }
        // Always return at least one (possibly empty) line so callers that
        // do `lines.length * lineHeight` never get zero height.
        return out.length === 0 ? [''] : out;
    },

    /**
     * Truncate `line` so it fits inside `maxWidth` (in world pixels) given
     * the font currently set on `ctx`, and append a single-character
     * ellipsis. Used by drawText when the user has height-locked a text
     * box and the wrapped content has more lines than fit -- the last
     * visible line is replaced by the truncated form so the operator
     * sees that content was elided rather than silently lost.
     *
     * Character-break (greedy backward shrink) handles long URLs and
     * any token that the wrap step itself broke mid-word.
     */
    _truncateToWidthWithEllipsis(ctx, line, maxWidth) {
        const ELLIPSIS = '\u2026';
        if (!Number.isFinite(maxWidth) || maxWidth <= 0) return line;
        if (ctx.measureText(line + ELLIPSIS).width <= maxWidth) return line + ELLIPSIS;
        let cut = line;
        while (cut.length > 0 && ctx.measureText(cut + ELLIPSIS).width > maxWidth) {
            cut = cut.slice(0, -1);
        }
        return cut + ELLIPSIS;
    },

    _paintTextScreenContent(editor, text, paint, effectiveRotation, snappedTx, snappedTy) {
        const zoom = Math.max(0.05, Number(editor.zoom) || 1);
        const dpr = Math.max(1, Number(editor.dpr) || window.devicePixelRatio || 1);
        const sharpPan = typeof editor.getSharpPanOffset === 'function'
            ? editor.getSharpPanOffset()
            : { x: Math.round(editor.panOffset?.x || 0), y: Math.round(editor.panOffset?.y || 0) };
        const snapCss = (value) => Math.round((Number(value) || 0) * dpr) / dpr;
        const screenX = snapCss(sharpPan.x + (snappedTx || 0) * zoom);
        const screenY = snapCss(sharpPan.y + (snappedTy || 0) * zoom);
        const fontSize = Math.max(1, (Number(paint.fontSize) || 14) * zoom);
        const lineHeight = Math.max(1, paint.lineHeight * zoom);
        const textW = Math.max(1, paint.w * zoom);
        const textH = Math.max(1, paint.h * zoom);
        const padding = Math.max(0, paint.padding * zoom);
        const startY = -textH / 2 + lineHeight / 2;
        const fontStyle = text.fontStyle || 'normal';
        const fontWeight = text.fontWeight || 'normal';
        const fontFamily = text.fontFamily || 'Arial, sans-serif';

        editor.ctx.save();
        editor.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        if (typeof editor.configureCanvasQuality === 'function') {
            editor.configureCanvasQuality(editor.ctx, { smoothing: false, textRendering: 'geometricPrecision' });
        } else {
            editor.ctx.imageSmoothingEnabled = false;
            editor.ctx.lineJoin = 'round';
            editor.ctx.lineCap = 'round';
        }
        editor.ctx.translate(screenX, screenY);
        editor.ctx.rotate((effectiveRotation || 0) * Math.PI / 180);

        if (paint.shouldDrawBackground) {
            editor.ctx.save();
            editor.ctx.globalAlpha = paint.backgroundOpacity;
            editor.ctx.fillStyle = paint.bgColor;
            const x = snapCss(-textW / 2 - padding);
            const y = snapCss(-textH / 2 - padding);
            const w = snapCss(textW + padding * 2);
            const h = snapCss(textH + padding * 2);
            editor.ctx.fillRect(x, y, w, h);
            editor.ctx.restore();
        }

        editor.ctx.font = `${fontStyle} ${fontWeight} ${fontSize}px ${fontFamily}`;
        editor.ctx.textAlign = 'center';
        editor.ctx.textBaseline = 'middle';

        paint.lines.forEach((line, index) => {
            const y = snapCss(startY + index * lineHeight);
            if (text.showBorder && text.borderWidth > 0) {
                editor.ctx.strokeStyle = text.borderColor || '#0066FA';
                editor.ctx.lineWidth = Math.max((text.borderWidth || 2) * zoom, 1 / dpr);
                editor.ctx.lineJoin = 'round';
                editor.ctx.miterLimit = 2;
                editor.ctx.strokeText(line || ' ', 0, y);
            } else if (text.strokeWidth && text.strokeWidth > 0) {
                editor.ctx.strokeStyle = text.strokeColor || '#000000';
                editor.ctx.lineWidth = Math.max((text.strokeWidth || 2) * zoom, 1 / dpr);
                editor.ctx.lineJoin = 'round';
                editor.ctx.miterLimit = 2;
                editor.ctx.strokeText(line || ' ', 0, y);
            }

            if (paint.textColorOverride) {
                editor.ctx.fillStyle = paint.textColorOverride;
            } else if (paint.shouldDrawBackground && paint.bgColor && paint.bgColor !== 'transparent') {
                editor.ctx.fillStyle = this._contrastColorForBg(editor, text.color, paint.bgColor);
            } else {
                editor.ctx.fillStyle = editor.adjustColorForMode(text.color);
            }
            editor.ctx.fillText(line || ' ', 0, y);
        });

        editor.ctx.restore();
        return true;
    },

    _drawTextRasterContent(editor, text, paint) {
        const strokeWidth = text.showBorder && text.borderWidth > 0
            ? (text.borderWidth || 2)
            : (text.strokeWidth && text.strokeWidth > 0 ? (text.strokeWidth || 2) : 0);
        const visiblePad = paint.shouldDrawBackground ? paint.padding : 0;
        const rasterPad = Math.max(3, visiblePad, strokeWidth + 3);
        const box = {
            x: -paint.w / 2 - rasterPad,
            y: -paint.h / 2 - rasterPad,
            w: paint.w + rasterPad * 2,
            h: paint.h + rasterPad * 2
        };

        if (!Number.isFinite(box.w) || !Number.isFinite(box.h) || box.w <= 0 || box.h <= 0) {
            return false;
        }

        const renderScale = this._getTextRasterScale(editor);
        const pixelW = Math.max(1, Math.ceil(box.w * renderScale));
        const pixelH = Math.max(1, Math.ceil(box.h * renderScale));
        const pixels = pixelW * pixelH;
        if (pixels > 4_000_000) {
            return false;
        }

        const key = [
            paint.textContent,
            paint.font,
            paint.w.toFixed(3),
            paint.h.toFixed(3),
            paint.lineHeight.toFixed(3),
            paint.padding,
            paint.bgColor,
            paint.backgroundOpacity,
            paint.shouldDrawBackground ? 1 : 0,
            text.color || '',
            text.showBorder ? 1 : 0,
            text.borderWidth || 0,
            text.borderColor || '',
            text.strokeWidth || 0,
            text.strokeColor || '',
            editor.darkMode ? 1 : 0,
            renderScale.toFixed(3),
            pixelW,
            pixelH
        ].join('\u001f');

        const cache = this._getTextRasterCache(editor);
        let entry = cache.get(key);
        if (entry) {
            cache.delete(key);
            cache.set(key, entry);
        } else {
            const canvas = this._createTextRasterCanvas(pixelW, pixelH);
            const rctx = canvas?.getContext?.('2d', { alpha: true });
            if (!canvas || !rctx) {
                return false;
            }
            if (typeof editor.configureCanvasQuality === 'function') {
                editor.configureCanvasQuality(rctx, { smoothing: true });
            } else {
                rctx.imageSmoothingEnabled = true;
                if ('imageSmoothingQuality' in rctx) rctx.imageSmoothingQuality = 'high';
                rctx.lineJoin = 'round';
                rctx.lineCap = 'round';
            }
            rctx.clearRect(0, 0, pixelW, pixelH);
            rctx.setTransform(renderScale, 0, 0, renderScale, -box.x * renderScale, -box.y * renderScale);
            this._paintTextVectorContent(editor, rctx, text, paint);
            entry = { canvas, box, pixels };
            cache.set(key, entry);
            this._pruneTextRasterCache(cache);
        }

        editor.ctx.save();
        if (typeof editor.configureCanvasQuality === 'function') {
            editor.configureCanvasQuality(editor.ctx, { smoothing: true });
        } else {
            editor.ctx.imageSmoothingEnabled = true;
            if ('imageSmoothingQuality' in editor.ctx) editor.ctx.imageSmoothingQuality = 'high';
        }
        editor.ctx.drawImage(entry.canvas, entry.box.x, entry.box.y, entry.box.w, entry.box.h);
        editor.ctx.restore();
        return true;
    },

    /**
     * Draw the 8 visible resize dot-handles for a text box (corners as
     * squares, edge-midpoints as circles). Mirrors the shape resize handle
     * style in topology-shape-drawing.js so multi-select with mixed shapes
     * and text boxes reads consistently.
     *
     *   - Caller is in the rotated, centred local frame of the text box
     *     (0,0 == centre of bbox, +x right, +y down, axis-aligned).
     *   - `halfW`/`halfH` are HALF the bbox width/height in world units.
     *   - `zoomScale` = 1 / editor.zoom -- used to keep dot dimensions
     *     constant in CSS pixels regardless of canvas zoom (devices and
     *     shapes use the same trick so handles never become microscopic
     *     at zoom-out or absurdly huge at zoom-in).
     *
     * Hit-test: see findTextHandle (topology-object-detection.js); the dot
     * test runs FIRST and the 5-px edge-zone band is the fallback for
     * forgiving "drag anywhere on the border" gestures.
     */
    _drawTextResizeDots(ctx, halfW, halfH, zoomScale) {
        const cornerSize = 12 * zoomScale;
        const edgeSize   = 12 * zoomScale;
        const dots = [
            { x: -halfW, y: -halfH, isCorner: true  }, // nw
            { x:  halfW, y: -halfH, isCorner: true  }, // ne
            { x: -halfW, y:  halfH, isCorner: true  }, // sw
            { x:  halfW, y:  halfH, isCorner: true  }, // se
            { x:  0,     y: -halfH, isCorner: false }, // n
            { x:  0,     y:  halfH, isCorner: false }, // s
            { x: -halfW, y:  0,     isCorner: false }, // w
            { x:  halfW, y:  0,     isCorner: false }  // e
        ];
        ctx.save();
        for (const d of dots) {
            ctx.shadowColor = 'rgba(52, 152, 219, 0.6)';
            ctx.shadowBlur = 8 * zoomScale;
            if (d.isCorner) {
                const hs = cornerSize / 2;
                ctx.fillStyle = '#3498db';
                ctx.fillRect(d.x - hs, d.y - hs, cornerSize, cornerSize);
                ctx.shadowBlur = 0;
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 2 * zoomScale;
                ctx.strokeRect(d.x - hs, d.y - hs, cornerSize, cornerSize);
            } else {
                ctx.fillStyle = '#3498db';
                ctx.beginPath();
                ctx.arc(d.x, d.y, edgeSize / 2, 0, Math.PI * 2);
                ctx.fill();
                ctx.shadowBlur = 0;
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 2 * zoomScale;
                ctx.stroke();
            }
        }
        ctx.restore();
    },

    drawText(editor, text) {
        // Skip drawing if text is being edited inline (input shows it instead)
        if (text._editing) {
            return;
        }

        // Generated diagrams can contain many evidence/detail labels. At low
        // zoom those labels collapse into sub-pixel noise and make the whole
        // topology look blurry. Keep the architecture readable by culling
        // generated micro-detail first; users can zoom in for link evidence.
        if (text._generatedTopologyLabel) {
            const z = Number(editor.zoom) || 1;
            const isGeneratedDetail = text._afChip
                || text.position === 'device1'
                || text.position === 'device2'
                || text._generatedLayer === 'identity'
                || text._labelLayer === 'identity';
            if (z < 0.95 && isGeneratedDetail) return;
            if (z < 0.72 && text._linkDataLabel && !text._generatedServiceLabel) return;
        }
        
        const isSelected = editor.selectedObject === text || editor.selectedObjects.includes(text);
        
        editor.ctx.save();
        // Sub-pixel position snap: world (text.x, text.y) is multiplied by
        // (zoom * dpr) when it lands on the backing store. If text.x is e.g.
        // 100.7 the glyph centre lands at .7 of a physical pixel which makes
        // the rasterizer blur the stroke horizontally. We snap the world
        // translate so (text.x * zoom * dpr) is a whole physical pixel.
        // The shift is at most 0.5 physical pixels (< 0.25 CSS pixels even
        // on DPR=2) -- visually invisible but the glyph contour stops
        // straddling pixel boundaries. Hit detection still uses raw
        // text.x/y; the sub-pixel offset is well below pointer accuracy.
        const tZoom = editor.zoom || 1;
        const tDpr = editor.dpr || 1;
        const tSnap = Math.max(tZoom * tDpr, 0.05);
        const snappedTx = Math.round((text.x || 0) * tSnap) / tSnap;
        const snappedTy = Math.round((text.y || 0) * tSnap) / tSnap;
        editor.ctx.translate(snappedTx, snappedTy);
        
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
        const fontWeight = text.fontWeight || (text._generatedTopologyLabel ? '700' : 'normal');
        const fontFamily = text.fontFamily || 'Arial, sans-serif';
        // TB text-boxes are USER-PLACED world content -- they MUST scale
        // proportionally with zoom (just like devices, links, shapes). Do
        // NOT inflate the world size with a screen-pixel floor; that breaks
        // proportions at extreme zoom-out (a previous attempt to floor at
        // 10 screen px made TBs look 10x larger than the rest of the canvas
        // at zoom <= 0.1). getDprSnappedFontSize is historical naming: it now
        // applies the smooth soft-floor only, with no physical-pixel font-size
        // rounding. Phase 2 sharpness comes from high-DPI prerasterizing the
        // TB paint pass while leaving geometry and handles in world units.
        const requestedFontSize = Number(text.fontSize) || 14;
        const generatedMinScreenPx = text._generatedServiceLabel ? 13
            : text._linkDataLabel ? 12
                : text._afChip ? 10
                    : 11;
        const displayFontSize = text._generatedTopologyLabel
            ? this._getGeneratedLabelFontSize(editor, requestedFontSize, generatedMinScreenPx)
            : (editor.getDprSnappedFontSize
                ? editor.getDprSnappedFontSize(requestedFontSize)
                : requestedFontSize);
        editor.ctx.font = `${fontStyle} ${fontWeight} ${displayFontSize}px ${fontFamily}`;
        editor.ctx.textAlign = 'center';
        editor.ctx.textBaseline = 'middle';
        
        // ENHANCED: Attached text boxes (on link lines) get grid-matching backgrounds
        // This hides the link body through the text while grid shows through char gaps
        const isAttachedToLink = text.linkId && text._onLinkLine === true;
        const isInterfaceLabel = text._interfaceLabel === true;
        const isGeneratedLinkLabel = isAttachedToLink && (
            text._generatedTopologyLabel === true
            || text._linkDataLabel === true
            || !!text._generatedProtocol
        );
        
        // For interface labels on links: use grid-matching background color
        // This creates the "transparent" illusion where link is hidden but grid shows through
        const gridBgColor = editor.darkMode ? '#1a1a1a' : '#ffffff';
        const defaultBgColor = editor.darkMode ? '#1a1a1a' : '#f5f5f5';
        
        // Determine background color
        // FIXED: Attached text boxes can use their custom bgColor if set
        let bgColor;
        if (isInterfaceLabel || isGeneratedLinkLabel) {
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
        
        // MULTILINE SUPPORT: Split text into lines and measure all.
        // Use the SAME displayFontSize set above on ctx.font so the
        // measured width and line-height match what's painted. Hit
        // detection mirrors this exact computation.
        //
        // EDGE-STRETCH + REFLOW MODE (text-box edges, 2026-05-12):
        //
        //   * If the user dragged a side or corner, `text.width` is
        //     persisted and we treat it as the WIDTH constraint; lines
        //     are word-wrapped to fit.
        //
        //   * Height behaviour:
        //
        //       - Default (auto-grow):   the painted bbox always contains
        //         every wrapped line. `text.height` may or may not be set,
        //         but unless `text._heightLocked` is true we recompute h
        //         from the wrapped lines on every paint. This is the
        //         containment invariant -- text never bleeds past the
        //         visible rectangle, no matter what the user types.
        //
        //       - Locked  (`_heightLocked === true`): the user explicitly
        //         dragged a vertical edge or corner, so we honour
        //         `text.height` and clip overflow lines with an ellipsis
        //         on the last visible line. A small "..." chevron is
        //         painted at the bottom-right by the selection block to
        //         signal the clip.
        //
        // Auto-size mode (legacy text without width) keeps the prior
        // behaviour: split on \n only, no wrapping, w/h derive from content.
        // That mode is already containment-safe by construction.
        const textContent = text.text == null ? 'Text' : String(text.text);
        const fontSize = parseInt(displayFontSize) || 14;
        const lineHeight = fontSize * 1.3;
        const hasManualWidth = Number.isFinite(text.width) && text.width > 0;

        let lines;
        let w;
        let h;
        let isClippedByHeight = false;
        if (hasManualWidth) {
            const wrapped = this._wrapTextLinesToWidth(editor.ctx, textContent, text.width);
            w = text.width;

            const naturalH = Math.max(20, wrapped.length * lineHeight);
            const heightLocked = text._heightLocked === true && Number.isFinite(text.height);
            if (heightLocked) {
                h = Math.max(20, text.height);
                const maxLines = Math.max(1, Math.floor(h / lineHeight));
                if (wrapped.length > maxLines) {
                    const visible = wrapped.slice(0, maxLines);
                    const lastIdx = visible.length - 1;
                    visible[lastIdx] = this._truncateToWidthWithEllipsis(
                        editor.ctx, visible[lastIdx], text.width);
                    lines = visible;
                    isClippedByHeight = true;
                } else {
                    lines = wrapped;
                }
            } else {
                lines = wrapped;
                h = naturalH;
            }
        } else {
            lines = textContent.split('\n');
            let maxWidth = 0;
            for (const line of lines) {
                const metrics = editor.ctx.measureText(line || ' ');
                maxWidth = Math.max(maxWidth, metrics.width);
            }
            w = maxWidth;
            h = lines.length * lineHeight;
        }
        
        // Draw background for:
        // - Regular text with showBackground enabled
        // - Attached text with showBackground enabled (uses custom bgColor)
        // - Interface labels attached to links (always, to hide link body)
        const shouldDrawBackground = (text.showBackground !== false && bgColor !== 'transparent') ||
                                     isInterfaceLabel;
        const defaultPadding = isAttachedToLink ? 4 : 8;
        const padding = text.backgroundPadding !== undefined ? text.backgroundPadding : defaultPadding;
        const backgroundOpacity = this._normalizeTextBackgroundOpacity(text.backgroundOpacity);
        
        const startY = -h/2 + lineHeight/2; // Center the block vertically
        const paint = {
            textContent,
            lines,
            font: `${fontStyle} ${fontWeight} ${displayFontSize}px ${fontFamily}`,
            fontSize: displayFontSize,
            w,
            h,
            lineHeight,
            startY,
            padding,
            bgColor,
            backgroundOpacity,
            shouldDrawBackground,
            isClippedByHeight,
            textColorOverride: isGeneratedLinkLabel && !editor.darkMode && ['#ffffff', '#fff', '#e0e0e0', 'white'].includes(String(text.color || '').toLowerCase())
                ? '#111827'
                : null
        };
        const paintedInScreenSpace = (Number(editor.zoom) || 1) < 1.05
            && this._paintTextScreenContent(editor, text, paint, effectiveRotation, snappedTx, snappedTy);
        if (!paintedInScreenSpace && !this._drawTextRasterContent(editor, text, paint)) {
            this._paintTextVectorContent(editor, editor.ctx, text, paint);
        }
        
        // Draw selection highlight when text is selected (regardless of mode).
        // Halo style matches the shape selection halo (canonical app style):
        // semi-transparent blue stroke, 6/4 dash pattern, 4-px outline offset.
        // Polish + QA pass 2026-05-12 -- aligns text-box halo with shape halo
        // so multi-select containing both element types renders consistently.
        if (isSelected) {
            const haloOffset = 4;
            editor.ctx.strokeStyle = 'rgba(52, 152, 219, 0.8)';
            editor.ctx.lineWidth = 2;
            editor.ctx.setLineDash([6, 4]);
            // Smoothness pass 2026-05-12: square line-cap on the dashed
            // halo prevents sub-pixel feathering at non-integer zoom
            // levels (e.g. 0.83x) where the default round caps render
            // each dash with a half-pixel anti-aliased rim that bleeds
            // into the next dash. Square caps keep dashes crisp at any
            // zoom. Restored to 'butt' (canvas default) after stroke so
            // we don't leak state into other halo / link strokes painted
            // later in the frame.
            const _prevCap = editor.ctx.lineCap;
            editor.ctx.lineCap = 'square';
            editor.ctx.strokeRect(
                -w / 2 - haloOffset,
                -h / 2 - haloOffset,
                w + haloOffset * 2,
                h + haloOffset * 2
            );
            editor.ctx.lineCap = _prevCap;
            editor.ctx.setLineDash([]);

            // Clip indicator (containment invariant, 2026-05-12). When the
            // user has height-locked the box and the wrapped content does
            // not fit, drawText already truncated the last visible line
            // with an ellipsis. Paint a small down-chevron at the inside
            // bottom-right corner so the operator knows there is more
            // content below the visible area.
            if (isClippedByHeight) {
                const zoomScaleClip = 1 / (editor.zoom || 1);
                const chevSize = 6 * zoomScaleClip;
                const chevPad = 4 * zoomScaleClip;
                const cx = w / 2 - chevPad - chevSize;
                const cy = h / 2 - chevPad - chevSize;
                editor.ctx.save();
                editor.ctx.fillStyle = 'rgba(52, 152, 219, 0.85)';
                editor.ctx.beginPath();
                editor.ctx.moveTo(cx,                cy);
                editor.ctx.lineTo(cx + chevSize * 2, cy);
                editor.ctx.lineTo(cx + chevSize,     cy + chevSize);
                editor.ctx.closePath();
                editor.ctx.fill();
                editor.ctx.restore();
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

            // RESIZE HANDLES (text-box, 2026-05-12 dots+edge-zone coexist)
            // -----------------------------------------------------------------
            // Text boxes draw BOTH visible 8 dot-handles AND retain the
            // edge-zone stretch band. Two-track design:
            //
            //   * Visible dots (4 corners + 4 edge-midpoints) at the SAME
            //     style/colour/size as shape dot-handles -- pure visual
            //     affordance and discoverability. Clicking a dot is hit-tested
            //     FIRST in findTextHandle (object-detection) and routes to
            //     the matching `nw`/`ne`/`sw`/`se`/`n`/`s`/`e`/`w` handler.
            //   * Edge-zone band (existing 5-px world-space band hugging
            //     each side, in findTextHandle as the fallback). Lets the
            //     user start a resize anywhere along the edge -- they do
            //     not need pixel-perfect aim on a tiny dot.
            //
            // The dashed selection halo is still drawn (above) for parity
            // with shapes; the dots sit on its corners/midpoints. The
            // separate green rotation handle stays at the top-right
            // outside the bbox -- it pre-dates resize handles entirely.
            //
            // While a drag is in flight, a thin --dn-cyan highlight is
            // painted on the active edge so the operator sees exactly
            // which side is moving.
            const halfW = w / 2;
            const halfH = h / 2;
            const zoomScale = 1 / editor.zoom;

            // (1) ROTATION HANDLE -- separate, outside the top-right corner.
            // Same offset shapes use, drawn in the rotated context. The
            // green colour + arc + curved-arrow icon match the legacy text
            // rotation handle so users see no regression.
            {
                const rotHandleOffset = 15 * zoomScale;
                const rotX = halfW + rotHandleOffset;
                const rotY = -(halfH + rotHandleOffset);
                const rotHandleSize = Math.max(6, Math.min(10, 8 / editor.zoom));
                const rotationRadians = effectiveRotation * Math.PI / 180;
                const arcRadius = rotHandleSize + 4;

                if (Math.abs(rotationRadians) > 0.05) {
                    editor.ctx.beginPath();
                    editor.ctx.arc(rotX, rotY, arcRadius, -Math.PI / 2, -Math.PI / 2 + rotationRadians);
                    editor.ctx.strokeStyle = '#2ecc71';
                    editor.ctx.lineWidth = 2.5 * zoomScale;
                    editor.ctx.lineCap = 'round';
                    editor.ctx.stroke();
                }

                editor.ctx.beginPath();
                editor.ctx.arc(rotX, rotY, rotHandleSize, 0, Math.PI * 2);
                const rotGrad = editor.ctx.createRadialGradient(
                    rotX - rotHandleSize / 3, rotY - rotHandleSize / 3, 0,
                    rotX, rotY, rotHandleSize
                );
                rotGrad.addColorStop(0, '#58d68d');
                rotGrad.addColorStop(1, '#27ae60');
                editor.ctx.fillStyle = rotGrad;
                editor.ctx.fill();
                editor.ctx.strokeStyle = 'white';
                editor.ctx.lineWidth = 2 * zoomScale;
                editor.ctx.stroke();

                editor.ctx.save();
                editor.ctx.translate(rotX, rotY);
                editor.ctx.beginPath();
                editor.ctx.arc(0, 0, rotHandleSize * 0.5, -Math.PI * 0.8, Math.PI * 0.3);
                editor.ctx.strokeStyle = 'white';
                editor.ctx.lineWidth = 1.5 * zoomScale;
                editor.ctx.lineCap = 'round';
                editor.ctx.stroke();
                const arrowAngle = Math.PI * 0.3;
                const arrowX = Math.cos(arrowAngle) * rotHandleSize * 0.5;
                const arrowY = Math.sin(arrowAngle) * rotHandleSize * 0.5;
                editor.ctx.beginPath();
                editor.ctx.moveTo(arrowX, arrowY);
                editor.ctx.lineTo(arrowX + 3 * zoomScale, arrowY - 1 * zoomScale);
                editor.ctx.lineTo(arrowX + 1 * zoomScale, arrowY + 3 * zoomScale);
                editor.ctx.fillStyle = 'white';
                editor.ctx.fill();
                editor.ctx.restore();
            }

            // (2) DOT-HANDLES (8 positions, shape-style, 2026-05-12).
            // Re-introduced alongside the edge-zone band so users SEE the
            // resize affordance. Visual style mirrors shape resize handles
            // (topology-shape-drawing.js): square dots at the 4 corners,
            // circle dots at the 4 edge midpoints, --dn brand blue
            // (#3498db) fill with a white stroke and a soft blue glow.
            // Sizes are zoom-corrected so the dots stay 12 CSS-px regardless
            // of canvas zoom. Hit-tested in findTextHandle FIRST (before
            // edge-zone fallback) so a click on a dot routes deterministically
            // to the matching handle id.
            this._drawTextResizeDots(editor.ctx, halfW, halfH, zoomScale);

            // (3) ACTIVE-EDGE HIGHLIGHT during a drag. Cyan stroke, 1 CSS
            // px wide (zoom-corrected), drawn over the dashed halo AND on
            // top of the dots so the operator sees exactly which side is
            // moving. Only painted while THIS text is being resized;
            // never on hover.
            const activeHandle = (editor.resizingText && editor.selectedObject === text)
                ? editor.textResizeHandle
                : null;
            if (activeHandle) {
                const cyan = (typeof getComputedStyle === 'function' && document.documentElement)
                    ? (getComputedStyle(document.documentElement).getPropertyValue('--dn-cyan').trim() || '#22d3ee')
                    : '#22d3ee';
                editor.ctx.save();
                editor.ctx.strokeStyle = cyan;
                editor.ctx.lineWidth = Math.max(1 * zoomScale, 1 / (editor.zoom * (editor.dpr || 1)));
                editor.ctx.lineCap = 'round';
                editor.ctx.beginPath();
                if (activeHandle.includes('w') || activeHandle === 'nw' || activeHandle === 'sw') {
                    editor.ctx.moveTo(-halfW, -halfH);
                    editor.ctx.lineTo(-halfW,  halfH);
                }
                if (activeHandle.includes('e') || activeHandle === 'ne' || activeHandle === 'se') {
                    editor.ctx.moveTo( halfW, -halfH);
                    editor.ctx.lineTo( halfW,  halfH);
                }
                if (activeHandle === 'n' || activeHandle === 'nw' || activeHandle === 'ne') {
                    editor.ctx.moveTo(-halfW, -halfH);
                    editor.ctx.lineTo( halfW, -halfH);
                }
                if (activeHandle === 's' || activeHandle === 'sw' || activeHandle === 'se') {
                    editor.ctx.moveTo(-halfW,  halfH);
                    editor.ctx.lineTo( halfW,  halfH);
                }
                editor.ctx.stroke();
                editor.ctx.restore();
            }

        }
        
        editor.ctx.restore();
        
        // Draw Angle Meter if enabled (use effective rotation for display)
        if (isSelected && editor.showAngleMeter) {
            const meterRotation = editor.getEffectiveTextRotation ? editor.getEffectiveTextRotation(text) : (text.rotation || 0);
            let degrees = Math.round(meterRotation) % 360;
            if (degrees > 180) degrees -= 360;
            if (degrees < -180) degrees += 360;
            const normalizedDegrees = degrees;

            // Anchor the meter label off the same effective bounding box that
            // drawText painted: width/height honour the manual edge-stretch
            // values + word-wrap when the user has resized the box. Without
            // this fallback the meter floats over the un-stretched glyph
            // width and visibly drifts after a horizontal stretch.
            // Polish + QA pass 2026-05-12.
            const metricBounds = (window.ObjectDetection && window.ObjectDetection.getTextEffectiveBounds)
                ? window.ObjectDetection.getTextEffectiveBounds(editor, text)
                : null;
            const w = metricBounds ? metricBounds.w : 0;
            const h = metricBounds ? metricBounds.h : (parseInt(text.fontSize) || 14);
            
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
        const hasSSH = sshCfg.host || sshCfg.hostBackup || device.deviceSerial
            || (device.deviceAddress && device.deviceAddress.trim() !== '');

        const fillNormal = !hasSSH ? '#7f8c8d' : (isConsole ? '#e67e22' : '#27ae60');
        const fillHover  = !hasSSH ? '#95a5a6' : (isConsole ? '#f39c12' : '#2ecc71');

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
        mismatch:     { fill: '#8e44ad', glow: '142,68,173'  },
        // Amber "credentials saved without verification" badge -- painted
        // when the operator clicked "Save anyway" in the SSH dialog
        // because verify-credentials returned a non-OK reason. Cleared
        // automatically on the next successful verify (handled by the
        // SSH dialog: it strips _unverifiedSave from sshConfig on ok).
        unverified:   { fill: '#f39c12', glow: '243,156,18'  }
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
        if (device.sshConfig && device.sshConfig._unverifiedSave) {
            badges.push({ type: 'unverified' });
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
            const unverified = !!(o.sshConfig && o.sshConfig._unverifiedSave);
            return o._activeConfigJob || o._activeUpgradeJob || o._upgradeInProgress || o._upgradeFailedJob || o._hostnameMismatch || unverified;
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
                // Looping "rising arrow" animation: 3 arrows of different
                // ages travel upward inside the badge in a continuous loop,
                // reading unmistakably as "uploading / installing in
                // progress" -- much clearer than the previous bounce that
                // could be mistaken for an idle decoration.
                //
                // Each arrow has a phase offset (0, 1/3, 2/3 of the cycle).
                // For each phase ``t in [0,1)``:
                //   - y position: travels from +travel (below center) to
                //     -travel (above center), so it sweeps UPWARD.
                //   - alpha: fades in during the first 25%, holds full
                //     opacity in the middle 50%, fades out in the last 25%.
                //     This produces the "stream of arrows rising" effect
                //     without hard pop-in/pop-out at the edges.
                editor.ctx.lineCap = 'round';
                editor.ctx.lineJoin = 'round';
                const aH = r * 0.34;          // arrow half-height
                const aW = r * 0.32;          // arrow chevron half-width
                const travel = r * 0.65;      // vertical sweep range
                const cycleMs = 1400;         // one full rise = 1.4s
                const tNow = (Date.now() % cycleMs) / cycleMs;
                const arrowCount = 3;
                const baseAlpha = editor.ctx.globalAlpha;
                for (let i = 0; i < arrowCount; i++) {
                    let t = (tNow + i / arrowCount) % 1;
                    // Fade envelope: 0..0.25 fade-in, 0.25..0.75 hold,
                    // 0.75..1 fade-out.
                    let alpha;
                    if (t < 0.25) alpha = t / 0.25;
                    else if (t > 0.75) alpha = (1 - t) / 0.25;
                    else alpha = 1;
                    const cy = by + travel - t * (travel * 2);
                    editor.ctx.globalAlpha = baseAlpha * alpha;
                    editor.ctx.strokeStyle = color;
                    editor.ctx.lineWidth = 1.3 / z;
                    editor.ctx.beginPath();
                    editor.ctx.moveTo(bx - aW, cy + aH * 0.4);
                    editor.ctx.lineTo(bx, cy - aH * 0.6);
                    editor.ctx.lineTo(bx + aW, cy + aH * 0.4);
                    editor.ctx.stroke();
                }
                editor.ctx.globalAlpha = baseAlpha;
                // Continuous redraw is already driven by
                // `editor._badgePulseTimer` (~60 fps via rAF) at the top
                // of `_drawBadges`, started whenever any device has an
                // active upgrade/config/mismatch badge -- no extra rAF
                // needed here.
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
            case 'unverified': {
                // Draw a small "?" -- credentials saved without a
                // verification handshake. Stays until the next
                // successful verifyCredentials call wipes the flag.
                const fs = Math.round(11 / z);
                editor.ctx.font = `800 ${fs}px -apple-system, BlinkMacSystemFont, sans-serif`;
                editor.ctx.textAlign = 'center';
                editor.ctx.textBaseline = 'middle';
                if (!dismissed) {
                    editor.ctx.shadowColor = 'rgba(0,0,0,0.35)';
                    editor.ctx.shadowBlur = 2 / z;
                    editor.ctx.shadowOffsetY = 0.6 / z;
                }
                editor.ctx.fillStyle = color;
                editor.ctx.fillText('?', bx, by + 0.5 / z);
                editor.ctx.shadowColor = 'transparent';
                editor.ctx.shadowBlur = 0;
                editor.ctx.shadowOffsetY = 0;
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
            case 'unverified':
                // Re-open the SSH dialog so the operator can re-run the
                // credential verification handshake. Uses the canonical
                // entry point exposed by `topology-ssh-dialog.js`.
                if (typeof window.showSSHAddressDialog === 'function') {
                    try { window.showSSHAddressDialog(editor, device); } catch (_) {}
                }
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
        // Dismiss EVERY currently-known failed upgrade job for this device, not only the
        // one being displayed. Devices like PE4 accumulate several historical failed jobs;
        // dismissing only the visible one would let the watcher's next poll surface another
        // failed jobId for the same device, leaving the red badge "stuck" forever.
        const label = device.label || '';
        const knownForDevice = (editor && editor._failedUpgradeJobsByDevice && editor._failedUpgradeJobsByDevice[label]) || [];
        const jobIdsToDismiss = new Set();
        if (job.jobId) jobIdsToDismiss.add(job.jobId);
        for (const k of knownForDevice) {
            if (k && k.jobId) jobIdsToDismiss.add(k.jobId);
        }
        try {
            const raw = localStorage.getItem('scaler_dismissed_upgrade_failures');
            const arr = JSON.parse(raw || '[]');
            const set = new Set(Array.isArray(arr) ? arr : []);
            for (const jid of jobIdsToDismiss) {
                if (label) set.add(`${jid}:${label}`);
            }
            localStorage.setItem('scaler_dismissed_upgrade_failures', JSON.stringify([...set]));
        } catch (_) {}
        device._upgradeFailedJob = null;
        if (editor.requestDraw) editor.requestDraw();
    },

    _startJobWatcher(editor) {
        if (editor._jobWatcherStarted) return;
        editor._jobWatcherStarted = true;
        if (typeof ScalerAPI === 'undefined' || !ScalerAPI.getJobs) return;

        let failCount = 0;
        const BASE_INTERVAL = 3000;
        const MAX_INTERVAL = 30000;

        // Listen for login so the watcher resumes promptly after user switch.
        // (When logged out we skip fetches entirely; on login we wake the loop.)
        if (!editor._jobWatcherAuthBound) {
            editor._jobWatcherAuthBound = true;
            const self = this;
            window.addEventListener('topology:auth-login', function () {
                if (ScalerAPI) {
                    ScalerAPI._bridgeUp = true;
                    ScalerAPI._bridgeRetryAfter = 0;
                }
                if (self._jobWatcherTimeout) {
                    clearTimeout(self._jobWatcherTimeout);
                    self._jobWatcherTimeout = setTimeout(function () { poll(); }, 50);
                }
            });
            window.addEventListener('topology:auth-logout', function () {
                for (const obj of (editor.objects || [])) {
                    if (obj.type !== 'device') continue;
                    obj._activeConfigJob = null;
                    obj._activeUpgradeJob = null;
                    obj._upgradeFailedJob = null;
                }
                if (editor.requestDraw) editor.requestDraw();
            });
        }

        const poll = async () => {
            if (window.TopologyAuth && !window.TopologyAuth.isAuthenticated()) {
                this._jobWatcherTimeout = setTimeout(poll, BASE_INTERVAL * 2);
                return;
            }
            // During an announced backend restart, skip the fetch entirely
            // so DevTools doesn't fill with ERR_CONNECTION_REFUSED. The
            // GracefulRestart coordinator polls /api/health and clears the
            // window once the backend is back, at which point we resume
            // immediately at BASE_INTERVAL.
            if (window.GracefulRestart && window.GracefulRestart.isInWindow()) {
                const wait = Math.min(MAX_INTERVAL, Math.max(BASE_INTERVAL,
                    (window.GracefulRestart.secondsRemaining() + 1) * 1000));
                this._jobWatcherTimeout = setTimeout(poll, wait);
                return;
            }
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
                // Build per-device list of ALL currently failed jobs (not just the last one
                // written into failedDevMap). The dismiss handler uses this to suppress every
                // outstanding failed job for a device, not only the one displayed -- previously
                // dismissing left the badge "stuck" on devices like PE4 that had multiple
                // historical failed upgrade attempts: dismissing one simply exposed the next.
                const allFailedByDevice = {};
                for (const job of failed) {
                    const jid = job.job_id || '';
                    if (!jid) continue;
                    const dids = [];
                    if (job.device_id) dids.push(job.device_id);
                    if (Array.isArray(job.devices)) {
                        for (const d of job.devices) { if (d && !dids.includes(d)) dids.push(d); }
                    }
                    for (const did of dids) {
                        if (!did) continue;
                        if (!allFailedByDevice[did]) allFailedByDevice[did] = [];
                        if (!allFailedByDevice[did].some(j => j.jobId === jid)) {
                            allFailedByDevice[did].push({
                                jobId: jid,
                                name: job.job_name || 'Upgrade',
                                devices: job.devices || [],
                                sshHosts: job.ssh_hosts || {},
                            });
                        }
                    }
                }
                editor._failedUpgradeJobsByDevice = allFailedByDevice;
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
        if (typeof ScalerGUI === 'undefined') return;

        // When the user closes the upgrade progress popup and re-opens it
        // from the device's Upgrade badge, we previously passed a synthetic
        // `{job_id, job_name, devices, ssh_hosts}` dict that lacked the
        // accumulated `terminal_lines`. The reopened panel therefore came
        // back empty until the next SSE frame (and even then, only
        // showed lines produced AFTER the reopen).
        //
        // Fix: fetch the full job from the bridge -- `_sanitize_job` keeps
        // `terminal_lines`, `percent`, `phase`, `device_state`, so the panel
        // can pre-populate its terminal cards, progress bar, and per-device
        // rows. The SSE reconnect uses `terminalOffset` to skip the lines
        // we already rendered, preventing duplicates.
        const buildSeed = (fullJob) => {
            const base = {
                job_id: job.jobId,
                job_name: job.name,
                devices: job.devices || [],
                ssh_hosts: job.sshHosts || {},
            };
            if (!fullJob) return base;
            // Prefer backend-authoritative fields but fall back to the
            // synthetic seed we already have.
            return {
                ...fullJob,
                job_id: fullJob.job_id || base.job_id,
                job_name: fullJob.job_name || base.job_name,
                devices: fullJob.devices || base.devices,
                ssh_hosts: fullJob.ssh_hosts || base.ssh_hosts,
            };
        };

        const show = (seed) => {
            if (ScalerGUI._showRunningUpgradeProgress) {
                ScalerGUI._showRunningUpgradeProgress(seed);
            } else if (ScalerGUI.showProgress) {
                ScalerGUI.showProgress(seed.job_id, seed.job_name, {
                    upgradeDevices: seed.devices || [],
                    upgradeSshHosts: seed.ssh_hosts || {},
                    _initialJobData: seed,
                });
            }
        };

        if (typeof ScalerAPI !== 'undefined' && typeof ScalerAPI.getJob === 'function') {
            ScalerAPI.getJob(job.jobId)
                .then((fullJob) => show(buildSeed(fullJob)))
                .catch(() => show(buildSeed(null)));
        } else {
            show(buildSeed(null));
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
