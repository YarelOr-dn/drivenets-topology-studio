/**
 * topology-device-styles.js
 * Device Visual Styles - Drawing and geometry functions for different device shapes
 * Extracted from topology.js to reduce file size
 * 
 * This module provides:
 * - Drawing functions for different device visual styles (circle, classic, simple, server, hex)
 * - Helper functions for arrows and color manipulation
 * - Geometry functions for device bounds, hit detection, and link connection points
 * 
 * Each device has a `visualStyle` property: 'circle', 'classic', 'simple', 'server', 'hex'
 * 
 * CRITICAL INTEGRATIONS:
 * 1. drawDevice() - dispatches to the correct drawing function
 * 2. getDeviceBounds() - returns shape-specific hitbox dimensions
 * 3. isPointInDeviceBounds() - shape-aware click detection
 * 4. getLinkConnectionPoint() - calculates edge intersection for links
 * 5. findResizeHandle() - positions resize handles based on shape
 * 6. findRotationHandle() - positions rotation handle based on shape
 * 7. Selection ring drawing in drawDevice() - draws shape-aware outline
 * 
 * WHEN ADDING A NEW STYLE:
 * - Add drawing function (drawDeviceXXX)
 * - Add case to getDeviceBounds() with accurate dimensions
 * - Add case to isPointInDeviceBounds() for hit detection
 * - Add case to getLinkConnectionPoint() for edge calculations
 * - Add case to findResizeHandle() for handle positions
 * - Update selection ring drawing in drawDevice()
 * - Add button and handler in setupToolbar() and setDeviceStyle()
 */

// ==================== DEVICE DRAWING FUNCTIONS ====================

/**
 * Draw device as a circle (default style)
 */
function drawDeviceCircle(editor, device, isSelected) {
    editor.ctx.beginPath();
    editor.ctx.arc(device.x, device.y, device.radius, 0, Math.PI * 2);
    editor.ctx.fillStyle = device.color;
    editor.ctx.fill();
    
    // Draw border (white in dark mode, dark gray in light mode)
    editor.ctx.strokeStyle = isSelected ? '#3498db' : (editor.darkMode ? '#ffffff' : '#333');
    editor.ctx.lineWidth = isSelected ? 3 : 2;
    editor.ctx.stroke();
}

/**
 * Draw device as Cylinder - 3D cylinder with gradient and arrows on top
 * Professional network device style
 */
function drawDeviceClassicRouter(editor, device, isSelected) {
    const r = device.radius;
    const x = device.x;
    const y = device.y;
    
    // Cylinder dimensions
    const width = r * 1.6;
    const topHeight = r * 0.4; // Ellipse height for top face
    const bodyHeight = r * 0.6; // Cylinder body height
    
    editor.ctx.save();
    editor.ctx.translate(x, y);
    editor.ctx.rotate((device.rotation || 0) * Math.PI / 180);
    
    const borderColor = isSelected ? '#3498db' : (editor.darkMode ? '#ffffff' : '#333');
    const darkerColor = darkenColor(device.color, 0.35);
    const highlightColor = lightenColor(device.color, 0.1);
    
    // Draw cylinder body (side) with horizontal gradient for 3D effect
    editor.ctx.beginPath();
    editor.ctx.moveTo(-width/2, -topHeight/2);
    editor.ctx.lineTo(-width/2, -topHeight/2 + bodyHeight);
    editor.ctx.ellipse(0, -topHeight/2 + bodyHeight, width/2, topHeight/2, 0, Math.PI, 0, true);
    editor.ctx.lineTo(width/2, -topHeight/2);
    editor.ctx.closePath();
    
    // Create horizontal gradient for cylinder body (light in center, dark at edges)
    const bodyGradient = editor.ctx.createLinearGradient(-width/2, 0, width/2, 0);
    bodyGradient.addColorStop(0, darkerColor);
    bodyGradient.addColorStop(0.3, darkenColor(device.color, 0.15));
    bodyGradient.addColorStop(0.5, darkenColor(device.color, 0.1));
    bodyGradient.addColorStop(0.7, darkenColor(device.color, 0.15));
    bodyGradient.addColorStop(1, darkerColor);
    editor.ctx.fillStyle = bodyGradient;
    editor.ctx.fill();
    editor.ctx.strokeStyle = borderColor;
    editor.ctx.lineWidth = isSelected ? 3 : 2;
    editor.ctx.stroke();
    
    // Draw label on the cylinder body (side surface) — skip when inline rename is active
    if (!device._renaming) {
        const label = device.label || (device.deviceType === 'router' ? 'NCP' : 'S');
        const labelY = bodyHeight * 0.4;
        const fontSize = device.labelSize || Math.max(10, Math.min(r * 0.35, 22));
        const fontFamily = device.fontFamily || editor.defaultDeviceFontFamily || 'Inter, sans-serif';
        editor.ctx.font = `bold ${fontSize}px ${fontFamily}`;
        editor.ctx.textAlign = 'center';
        editor.ctx.textBaseline = 'middle';
        
        const labelTextColor = device.labelColor || '#ffffff';
        editor.ctx.strokeStyle = 'rgba(0,0,0,0.6)';
        editor.ctx.lineWidth = 2.5;
        editor.ctx.strokeText(label, 0, labelY);
        editor.ctx.fillStyle = labelTextColor;
        editor.ctx.fillText(label, 0, labelY);
    }
    
    // Draw top ellipse face with subtle gradient
    editor.ctx.beginPath();
    editor.ctx.ellipse(0, -topHeight/2, width/2, topHeight/2, 0, 0, Math.PI * 2);
    
    // Radial gradient for top face (subtle lighting)
    const topGradient = editor.ctx.createRadialGradient(-width*0.15, -topHeight*0.6, 0, 0, -topHeight/2, width/2);
    topGradient.addColorStop(0, highlightColor);
    topGradient.addColorStop(0.7, device.color);
    topGradient.addColorStop(1, darkenColor(device.color, 0.1));
    editor.ctx.fillStyle = topGradient;
    editor.ctx.fill();
    editor.ctx.strokeStyle = borderColor;
    editor.ctx.stroke();
    
    // Draw 4-way arrows on top face (scaled to fit ellipse)
    // Always white arrows for visibility on colored device
    drawFourWayArrowsEllipse(editor, 0, -topHeight/2, width/2 * 0.7, topHeight/2 * 0.7, '#ffffff');
    
    editor.ctx.restore();
}

/**
 * Draw device as Simple Router - 2D minimal circle with crossed arrows
 * Clean, schematic style
 */
function drawDeviceSimpleRouter(editor, device, isSelected) {
    const r = device.radius;
    const x = device.x;
    const y = device.y;
    
    editor.ctx.save();
    editor.ctx.translate(x, y);
    editor.ctx.rotate((device.rotation || 0) * Math.PI / 180);
    
    const borderColor = isSelected ? '#3498db' : (editor.darkMode ? '#ffffff' : '#333');
    
    // Draw outer circle (outline only or very light fill)
    editor.ctx.beginPath();
    editor.ctx.arc(0, 0, r, 0, Math.PI * 2);
    editor.ctx.fillStyle = editor.darkMode ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.9)';
    editor.ctx.fill();
    editor.ctx.strokeStyle = borderColor;
    editor.ctx.lineWidth = isSelected ? 3 : 2.5;
    editor.ctx.stroke();
    
    // Draw inner circle
    editor.ctx.beginPath();
    editor.ctx.arc(0, 0, r * 0.15, 0, Math.PI * 2);
    editor.ctx.fillStyle = borderColor;
    editor.ctx.fill();
    
    // Draw 4 cardinal arrows pointing outward
    const arrowColor = borderColor;
    const arrowLen = r * 0.65;
    const arrowStart = r * 0.25;
    
    editor.ctx.strokeStyle = arrowColor;
    editor.ctx.fillStyle = arrowColor;
    editor.ctx.lineWidth = 2.5;
    
    // Cardinal directions: up, right, down, left
    const directions = [
        { dx: 0, dy: -1 },  // Up
        { dx: 1, dy: 0 },   // Right
        { dx: 0, dy: 1 },   // Down
        { dx: -1, dy: 0 }   // Left
    ];
    
    directions.forEach(dir => {
        const startX = dir.dx * arrowStart;
        const startY = dir.dy * arrowStart;
        const endX = dir.dx * arrowLen;
        const endY = dir.dy * arrowLen;
        
        // Draw arrow line
        editor.ctx.beginPath();
        editor.ctx.moveTo(startX, startY);
        editor.ctx.lineTo(endX, endY);
        editor.ctx.stroke();
        
        // Draw arrowhead
        const headLen = r * 0.18;
        const angle = Math.atan2(dir.dy, dir.dx);
        
        editor.ctx.beginPath();
        editor.ctx.moveTo(endX, endY);
        editor.ctx.lineTo(
            endX - headLen * Math.cos(angle - Math.PI/6),
            endY - headLen * Math.sin(angle - Math.PI/6)
        );
        editor.ctx.lineTo(
            endX - headLen * Math.cos(angle + Math.PI/6),
            endY - headLen * Math.sin(angle + Math.PI/6)
        );
        editor.ctx.closePath();
        editor.ctx.fill();
    });
    
    editor.ctx.restore();
}

/**
 * Draw device as Server Tower - 3D isometric vertical rectangle
 * Inspired by server/switch icons
 */
function drawDeviceServerTower(editor, device, isSelected) {
    const r = device.radius;
    const x = device.x;
    const y = device.y;
    
    // Tower dimensions (taller than wide)
    const width = r * 0.9;
    const height = r * 1.6;
    const depth = r * 0.4; // 3D depth
    
    editor.ctx.save();
    editor.ctx.translate(x, y);
    editor.ctx.rotate((device.rotation || 0) * Math.PI / 180);
    
    const borderColor = isSelected ? '#3498db' : (editor.darkMode ? '#ffffff' : '#333');
    const darkerColor = darkenColor(device.color, 0.25);
    const darkestColor = darkenColor(device.color, 0.45);
    
    // Draw right side (darkest)
    editor.ctx.beginPath();
    editor.ctx.moveTo(width/2, -height/2 + depth);
    editor.ctx.lineTo(width/2 + depth * 0.7, -height/2);
    editor.ctx.lineTo(width/2 + depth * 0.7, height/2 - depth);
    editor.ctx.lineTo(width/2, height/2);
    editor.ctx.closePath();
    editor.ctx.fillStyle = darkestColor;
    editor.ctx.fill();
    editor.ctx.strokeStyle = borderColor;
    editor.ctx.lineWidth = isSelected ? 2 : 1.5;
    editor.ctx.stroke();
    
    // Draw top face
    editor.ctx.beginPath();
    editor.ctx.moveTo(-width/2, -height/2 + depth);
    editor.ctx.lineTo(-width/2 + depth * 0.7, -height/2);
    editor.ctx.lineTo(width/2 + depth * 0.7, -height/2);
    editor.ctx.lineTo(width/2, -height/2 + depth);
    editor.ctx.closePath();
    editor.ctx.fillStyle = darkerColor;
    editor.ctx.fill();
    editor.ctx.strokeStyle = borderColor;
    editor.ctx.stroke();
    
    // Draw front face (main) with subtle gradient
    editor.ctx.beginPath();
    editor.ctx.rect(-width/2, -height/2 + depth, width, height - depth);
    
    // Vertical gradient for front face
    const frontGradient = editor.ctx.createLinearGradient(0, -height/2 + depth, 0, height/2);
    const highlightColor = lightenColor(device.color, 0.1);
    frontGradient.addColorStop(0, highlightColor);
    frontGradient.addColorStop(0.3, device.color);
    frontGradient.addColorStop(1, darkenColor(device.color, 0.1));
    editor.ctx.fillStyle = frontGradient;
    editor.ctx.fill();
    editor.ctx.strokeStyle = borderColor;
    editor.ctx.lineWidth = isSelected ? 3 : 2;
    editor.ctx.stroke();
    
    // Draw panel/screen area at top (always dark for consistent look)
    const panelY = -height/2 + depth + height * 0.08;
    const panelHeight = height * 0.18;
    editor.ctx.beginPath();
    editor.ctx.rect(-width/2 + width * 0.15, panelY, width * 0.7, panelHeight);
    editor.ctx.fillStyle = '#3a3a3a';  // Always dark panel
    editor.ctx.fill();
    editor.ctx.strokeStyle = '#555';
    editor.ctx.lineWidth = 1;
    editor.ctx.stroke();
    
    // Draw LED indicators on panel
    const ledRadius = height * 0.02;
    const ledY = panelY + panelHeight / 2;
    editor.ctx.beginPath();
    editor.ctx.arc(-width/2 + width * 0.25, ledY, ledRadius, 0, Math.PI * 2);
    editor.ctx.fillStyle = '#2ecc71'; // Green LED
    editor.ctx.fill();
    editor.ctx.beginPath();
    editor.ctx.arc(-width/2 + width * 0.35, ledY, ledRadius, 0, Math.PI * 2);
    editor.ctx.fillStyle = '#FF7A33'; // Orange LED
    editor.ctx.fill();
    
    // Draw 4-way arrows on front (always white for visibility on colored device)
    drawFourWayArrows(editor, 0, height * 0.2, r * 0.35, '#ffffff');
    
    editor.ctx.restore();
}

/**
 * Draw device as Hex Router - Hexagonal network device with subtle 3D effect
 * Professional look with shadow/highlight for depth
 */
function drawDeviceHexRouter(editor, device, isSelected) {
    const r = device.radius;
    const x = device.x;
    const y = device.y;
    
    const hexRadius = r * 0.65;
    const shadowOffset = r * 0.08; // Subtle shadow offset for 3D effect
    
    editor.ctx.save();
    editor.ctx.translate(x, y);
    editor.ctx.rotate((device.rotation || 0) * Math.PI / 180);
    
    const borderColor = isSelected ? '#3498db' : (editor.darkMode ? '#ffffff' : '#2c3e50');
    const shadowColor = darkenColor(device.color, 0.4);
    const highlightColor = lightenColor(device.color, 0.15);
    
    // Calculate hexagon points (flat-topped)
    const points = [];
    for (let i = 0; i < 6; i++) {
        const angle = (Math.PI / 6) + (i * Math.PI / 3);
        points.push({
            x: Math.cos(angle) * hexRadius,
            y: Math.sin(angle) * hexRadius
        });
    }
    
    // Draw shadow hexagon (offset down-right for 3D depth)
    editor.ctx.beginPath();
    editor.ctx.moveTo(points[0].x + shadowOffset, points[0].y + shadowOffset);
    for (let i = 1; i < 6; i++) {
        editor.ctx.lineTo(points[i].x + shadowOffset, points[i].y + shadowOffset);
    }
    editor.ctx.closePath();
    editor.ctx.fillStyle = shadowColor;
    editor.ctx.fill();
    
    // Draw main hexagon
    editor.ctx.beginPath();
    editor.ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < 6; i++) {
        editor.ctx.lineTo(points[i].x, points[i].y);
    }
    editor.ctx.closePath();
    
    // Gradient fill for subtle 3D lighting
    const gradient = editor.ctx.createLinearGradient(-hexRadius, -hexRadius, hexRadius, hexRadius);
    gradient.addColorStop(0, highlightColor);
    gradient.addColorStop(0.5, device.color);
    gradient.addColorStop(1, darkenColor(device.color, 0.15));
    editor.ctx.fillStyle = gradient;
    editor.ctx.fill();
    
    editor.ctx.strokeStyle = borderColor;
    editor.ctx.lineWidth = isSelected ? 3 : 2;
    editor.ctx.stroke();
    
    // Draw 4-way arrows centered on hexagon
    // Always white arrows for visibility on colored device
    drawFourWayArrows(editor, 0, 0, r * 0.35, '#ffffff');
    
    editor.ctx.restore();
}

// ==================== HELPER FUNCTIONS ====================

/**
 * Helper: Draw 4-way crossed arrows at specified position
 */
function drawFourWayArrows(editor, cx, cy, size, color) {
    editor.ctx.save();
    editor.ctx.translate(cx, cy);
    
    editor.ctx.strokeStyle = color;
    editor.ctx.fillStyle = color;
    editor.ctx.lineWidth = 2;
    
    // Diagonal arrows: ↗ ↘ ↙ ↖
    const directions = [
        { angle: -Math.PI / 4 },     // Top-right
        { angle: Math.PI / 4 },      // Bottom-right
        { angle: 3 * Math.PI / 4 },  // Bottom-left
        { angle: -3 * Math.PI / 4 }  // Top-left
    ];
    
    directions.forEach(dir => {
        const tipX = Math.cos(dir.angle) * size;
        const tipY = Math.sin(dir.angle) * size;
        
        // Draw arrow line from center
        editor.ctx.beginPath();
        editor.ctx.moveTo(0, 0);
        editor.ctx.lineTo(tipX, tipY);
        editor.ctx.stroke();
        
        // Draw arrowhead
        const headLen = size * 0.35;
        
        editor.ctx.beginPath();
        editor.ctx.moveTo(tipX, tipY);
        editor.ctx.lineTo(
            tipX - headLen * Math.cos(dir.angle - Math.PI/6),
            tipY - headLen * Math.sin(dir.angle - Math.PI/6)
        );
        editor.ctx.lineTo(
            tipX - headLen * Math.cos(dir.angle + Math.PI/6),
            tipY - headLen * Math.sin(dir.angle + Math.PI/6)
        );
        editor.ctx.closePath();
        editor.ctx.fill();
    });
    
    editor.ctx.restore();
}

/**
 * Helper: Draw 4-way crossed arrows scaled to fit an ellipse
 * Used for cylinder tops where the surface is elliptical
 */
function drawFourWayArrowsEllipse(editor, cx, cy, radiusX, radiusY, color) {
    editor.ctx.save();
    editor.ctx.translate(cx, cy);
    
    editor.ctx.strokeStyle = color;
    editor.ctx.fillStyle = color;
    editor.ctx.lineWidth = 2;
    
    // Diagonal arrows: ↗ ↘ ↙ ↖ (scaled to ellipse)
    const directions = [
        { angle: -Math.PI / 4 },     // Top-right
        { angle: Math.PI / 4 },      // Bottom-right
        { angle: 3 * Math.PI / 4 },  // Bottom-left
        { angle: -3 * Math.PI / 4 }  // Top-left
    ];
    
    directions.forEach(dir => {
        // Scale tips to fit within ellipse
        const tipX = Math.cos(dir.angle) * radiusX;
        const tipY = Math.sin(dir.angle) * radiusY;
        
        // Draw arrow line from center
        editor.ctx.beginPath();
        editor.ctx.moveTo(0, 0);
        editor.ctx.lineTo(tipX, tipY);
        editor.ctx.stroke();
        
        // Draw arrowhead (smaller for ellipse)
        const headLen = Math.min(radiusX, radiusY) * 0.35;
        
        editor.ctx.beginPath();
        editor.ctx.moveTo(tipX, tipY);
        editor.ctx.lineTo(
            tipX - headLen * Math.cos(dir.angle - Math.PI/6),
            tipY - headLen * Math.sin(dir.angle - Math.PI/6)
        );
        editor.ctx.lineTo(
            tipX - headLen * Math.cos(dir.angle + Math.PI/6),
            tipY - headLen * Math.sin(dir.angle + Math.PI/6)
        );
        editor.ctx.closePath();
        editor.ctx.fill();
    });
    
    editor.ctx.restore();
}

/**
 * Helper: Darken a color by a factor (0-1)
 */
function darkenColor(color, factor) {
    // Convert hex to RGB
    let hex = color.replace('#', '');
    if (hex.length === 3) {
        hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
    }
    const r = parseInt(hex.substr(0, 2), 16);
    const g = parseInt(hex.substr(2, 2), 16);
    const b = parseInt(hex.substr(4, 2), 16);
    
    // Darken
    const newR = Math.round(r * (1 - factor));
    const newG = Math.round(g * (1 - factor));
    const newB = Math.round(b * (1 - factor));
    
    return `rgb(${newR}, ${newG}, ${newB})`;
}

/**
 * Helper: Lighten a color by a factor (0-1)
 */
function lightenColor(color, factor) {
    // Convert hex to RGB
    let hex = color.replace('#', '');
    if (hex.length === 3) {
        hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
    }
    const r = parseInt(hex.substr(0, 2), 16);
    const g = parseInt(hex.substr(2, 2), 16);
    const b = parseInt(hex.substr(4, 2), 16);
    
    // Lighten (move toward 255)
    const newR = Math.round(r + (255 - r) * factor);
    const newG = Math.round(g + (255 - g) * factor);
    const newB = Math.round(b + (255 - b) * factor);
    
    return `rgb(${newR}, ${newG}, ${newB})`;
}

/**
 * Get theme-aware selection colors for a link
 * In dark mode with light links: use lightened colors (standard)
 * In light mode with light links: use contrasting blue selection
 * This ensures link selection is always visible regardless of theme
 */
function getLinkSelectionColors(editor, linkColor) {
    // Parse the link color to check its brightness
    let hex = linkColor.replace('#', '');
    if (hex.length === 3) {
        hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
    }
    
    // Handle rgb/rgba format
    let r, g, b;
    if (linkColor.startsWith('rgb')) {
        const match = linkColor.match(/(\d+),\s*(\d+),\s*(\d+)/);
        if (match) {
            r = parseInt(match[1]);
            g = parseInt(match[2]);
            b = parseInt(match[3]);
        } else {
            r = g = b = 128; // Fallback
        }
    } else {
        r = parseInt(hex.substr(0, 2), 16) || 0;
        g = parseInt(hex.substr(2, 2), 16) || 0;
        b = parseInt(hex.substr(4, 2), 16) || 0;
    }
    
    // Calculate brightness (0-255)
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    
    // Determine if link is "light" colored (brightness > 180)
    const isLightLink = brightness > 180;
    
    // In LIGHT MODE with a LIGHT LINK: use contrasting blue selection
    // Otherwise: use the standard lightened link color
    if (!editor.darkMode && isLightLink) {
        // Light mode + light link = use blue selection for visibility
        return {
            stroke: '#0066FA',      // DriveNets blue
            glow: 'rgba(0, 102, 250, 0.6)'
        };
    } else if (!editor.darkMode) {
        // Light mode + dark link = lighten the link color
        return {
            stroke: lightenColor(linkColor, 0.3) || linkColor,
            glow: lightenColor(linkColor, 0.5) || linkColor
        };
    } else if (editor.darkMode && !isLightLink) {
        // Dark mode + dark link = use blue selection for visibility
        return {
            stroke: '#64B5F6',      // Lighter blue for dark mode
            glow: 'rgba(100, 181, 246, 0.6)'
        };
    } else {
        // Dark mode + light link = standard lightening (as before)
        return {
            stroke: lightenColor(linkColor, 0.4) || linkColor,
            glow: lightenColor(linkColor, 0.6) || linkColor
        };
    }
}

// ==================== GEOMETRY FUNCTIONS ====================

/**
 * Get device bounds for a specific style (used for link connection calculations)
 * Returns {width, height, type} for the device shape
 */
function getDeviceBounds(device) {
    const style = device.visualStyle || 'circle';
    const r = device.radius;
    
    // Return EXACT bounds matching drawing code - using simple multipliers
    switch (style) {
        case 'classic':
            // Cylinder: width=1.6r, visual extends from -0.4r to 0.6r
            return { 
                type: 'classic', 
                width: r * 1.6, 
                height: r * 1.0,
                top: r * -0.4, 
                bottom: r * 0.6, 
                centerY: r * 0.1, 
                radius: r 
            };
        case 'simple':
            return { type: 'circle', width: r * 2, height: r * 2, radius: r };
        case 'server': {
            // 3D tower: front width=0.9r, 3D depth extends right by 0.28r
            const sW = r * 0.9;
            const sDepthX = r * 0.4 * 0.7;
            return { 
                type: 'rectangle', 
                width: sW + sDepthX,
                height: r * 1.6, 
                radius: r 
            };
        }
        case 'hex':
            // Flat hexagon: hexRadius * 2 for width, hexRadius * 2 for height
            // hexRadius = 0.65r, so width ≈ 1.13r (cos30° * 2), height = 1.3r
            return { 
                type: 'hexagon', 
                width: r * 1.13, 
                height: r * 1.3,
                top: r * -0.65, 
                bottom: r * 0.65, 
                centerY: 0, 
                radius: r 
            };
        case 'circle':
        default:
            return { type: 'circle', width: r * 2, height: r * 2, radius: r };
    }
}

/**
 * Check if a point is within a device's bounds (accounting for visual style and rotation)
 * @param {object} editor - Editor instance
 * @param {number} x - Point X coordinate
 * @param {number} y - Point Y coordinate
 * @param {object} device - Device object
 * @param {number} tolerance - Hit tolerance in world coordinates
 * @returns {boolean} True if point is within device bounds
 */
function isPointInDeviceBounds(editor, x, y, device, tolerance = 0) {
    const style = device.visualStyle || 'circle';
    const r = device.radius;
    
    // Transform point to device-local coordinates (accounting for rotation)
    const dx = x - device.x;
    const dy = y - device.y;
    const angle = -(device.rotation || 0) * Math.PI / 180;
    const localX = dx * Math.cos(angle) - dy * Math.sin(angle);
    const localY = dx * Math.sin(angle) + dy * Math.cos(angle);
    
    switch (style) {
        case 'classic': {
            // Rectangular hitbox for cylinder - exact bounds from drawing
            const bounds = getDeviceBounds(device);
            const halfW = bounds.width / 2 + tolerance;
            const top = bounds.top - tolerance;
            const bottom = bounds.bottom + tolerance;
            return Math.abs(localX) <= halfW && localY >= top && localY <= bottom;
        }
        case 'simple': {
            // Circular hitbox (same as circle - simple uses full radius)
            const distance = Math.sqrt(dx * dx + dy * dy);
            return distance <= r + tolerance;
        }
        case 'server': {
            // Asymmetric hitbox matching actual 3D tower shape
            // Front: -0.45r to +0.45r, 3D depth extends right to +0.73r
            const width = r * 0.9;
            const height = r * 1.6;
            const depthX = r * 0.4 * 0.7;
            const leftBound = -(width / 2) - tolerance;
            const rightBound = (width / 2) + depthX + tolerance;
            const topBound = -(height / 2) - tolerance;
            const bottomBound = (height / 2) + tolerance;
            return localX >= leftBound && localX <= rightBound &&
                   localY >= topBound && localY <= bottomBound;
        }
        case 'hex': {
            // Circular hitbox for simple flat hexagon
            const hexR = r * 0.65 + tolerance;
            const distance = Math.sqrt(localX * localX + localY * localY);
            return distance <= hexR;
        }
        case 'circle':
        default: {
            // Circular hitbox (original behavior)
            const distance = Math.sqrt(dx * dx + dy * dy);
            return distance <= r + tolerance;
        }
    }
}

/**
 * Get the connection point on a device's edge at a given angle
 * This properly calculates edge intersection based on device visual style
 * @param {object} device - The device object
 * @param {number} angle - Angle in radians from device center
 * @returns {{x: number, y: number}} Connection point coordinates
 */
function getLinkConnectionPoint(device, angle) {
    const style = device.visualStyle || 'circle';
    const r = device.radius;
    const rotation = (device.rotation || 0) * Math.PI / 180;
    
    // Adjust angle for device rotation
    const localAngle = angle - rotation;
    
    let localX, localY;
    
    switch (style) {
        case 'classic': {
            // Rectangle edge intersection - exact bounds from drawing
            const halfW = r * 0.8;  // Half width (1.6r / 2)
            const top = -r * 0.4;   // Top of cylinder
            const bottom = r * 0.6; // Bottom of cylinder
            const cos = Math.cos(localAngle);
            const sin = Math.sin(localAngle);
            
            // Find intersection with rectangle edges
            // Ray from (0,0) in direction (cos, sin)
            let t = Infinity;
            
            // Left/Right edges
            if (Math.abs(cos) > 0.001) {
                const tEdge = (cos > 0 ? halfW : -halfW) / cos;
                const yAtEdge = sin * tEdge;
                if (tEdge > 0 && yAtEdge >= top && yAtEdge <= bottom) {
                    t = Math.min(t, tEdge);
                }
            }
            // Top/Bottom edges
            if (Math.abs(sin) > 0.001) {
                const tEdge = (sin > 0 ? bottom : top) / sin;
                const xAtEdge = cos * tEdge;
                if (tEdge > 0 && Math.abs(xAtEdge) <= halfW) {
                    t = Math.min(t, tEdge);
                }
            }
            
            if (t === Infinity) t = r; // Fallback
            localX = cos * t;
            localY = sin * t;
            break;
        }
        case 'simple': {
            // Circle edge (same as default)
            localX = r * Math.cos(localAngle);
            localY = r * Math.sin(localAngle);
            break;
        }
        case 'server': {
            // Rectangle edge - matches draw: width≈1.18r, height=1.8r
            const halfW = r * 0.59;  // Half of 1.18r
            const halfH = r * 0.9;   // Half of 1.8r
            const cos = Math.cos(localAngle);
            const sin = Math.sin(localAngle);
            
            // Simple rectangle intersection centered at origin
            let scale = Infinity;
            if (Math.abs(cos) > 0.001) scale = Math.min(scale, halfW / Math.abs(cos));
            if (Math.abs(sin) > 0.001) scale = Math.min(scale, halfH / Math.abs(sin));
            
            localX = cos * scale;
            localY = sin * scale;
            break;
        }
        case 'hex': {
            // Calculate actual hexagon edge intersection
            const hexR = r * 0.65;
            const cos = Math.cos(localAngle);
            const sin = Math.sin(localAngle);
            
            // Hexagon has 6 edges - find intersection with ray from center
            let minT = Infinity;
            for (let i = 0; i < 6; i++) {
                const a1 = (Math.PI / 6) + (i * Math.PI / 3);
                const a2 = (Math.PI / 6) + ((i + 1) * Math.PI / 3);
                
                // Edge vertices
                const x1 = Math.cos(a1) * hexR;
                const y1 = Math.sin(a1) * hexR;
                const x2 = Math.cos(a2) * hexR;
                const y2 = Math.sin(a2) * hexR;
                
                // Ray-segment intersection
                // Ray: P = t * (cos, sin), t > 0
                // Segment: Q = (x1, y1) + s * (x2-x1, y2-y1), 0 <= s <= 1
                const dx = x2 - x1;
                const dy = y2 - y1;
                const denom = cos * dy - sin * dx;
                
                if (Math.abs(denom) > 0.0001) {
                    const t = (x1 * dy - y1 * dx) / denom;
                    const s = (x1 * sin - y1 * cos) / denom;
                    
                    if (t > 0 && s >= 0 && s <= 1) {
                        minT = Math.min(minT, t);
                    }
                }
            }
            
            if (minT === Infinity) minT = hexR; // Fallback
            localX = cos * minT;
            localY = sin * minT;
            break;
        }
        case 'circle':
        default: {
            // Circle edge
            localX = r * Math.cos(localAngle);
            localY = r * Math.sin(localAngle);
            break;
        }
    }
    
    // Rotate back to world coordinates
    const worldX = localX * Math.cos(rotation) - localY * Math.sin(rotation);
    const worldY = localX * Math.sin(rotation) + localY * Math.cos(rotation);
    
    return {
        x: device.x + worldX,
        y: device.y + worldY
    };
}

/**
 * Reconnect all links attached to a device after its style changes
 * Recalculates connection points based on the new shape
 */
function reconnectLinksToDevice(editor, device) {
    const deviceId = device.id;
    let linksFound = 0;
    
    // Find all links connected to this device
    editor.objects.forEach(obj => {
        if (obj.type === 'link') {
            // Quick links - recalculate on draw (handled by drawLink)
            // Nothing needed here as drawLink calculates positions dynamically
        } else if (obj.type === 'unbound') {
            // Unbound links - update stored positions
            if (obj.device1 === deviceId && obj.start) {
                linksFound++;
                const angle = Math.atan2(obj.end.y - device.y, obj.end.x - device.x);
                const newPoint = getLinkConnectionPoint(device, angle);
                obj.start.x = newPoint.x;
                obj.start.y = newPoint.y;
            }
            if (obj.device2 === deviceId && obj.end) {
                linksFound++;
                const angle = Math.atan2(obj.start.y - device.y, obj.start.x - device.x);
                const newPoint = getLinkConnectionPoint(device, angle);
                obj.end.x = newPoint.x;
                obj.end.y = newPoint.y;
            }
        }
    });
}

// ==================== EXPORTS ====================

// Export all functions to window for use by topology.js
window.DeviceStyles = {
    // Drawing functions
    drawDeviceCircle,
    drawDeviceClassicRouter,
    drawDeviceSimpleRouter,
    drawDeviceServerTower,
    drawDeviceHexRouter,
    
    // Helper functions
    drawFourWayArrows,
    drawFourWayArrowsEllipse,
    darkenColor,
    lightenColor,
    getLinkSelectionColors,
    
    // Geometry functions
    getDeviceBounds,
    isPointInDeviceBounds,
    getLinkConnectionPoint,
    reconnectLinksToDevice
};

console.log('[topology-device-styles.js] Device visual styles module loaded');
