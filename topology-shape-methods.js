/**
 * topology-shape-methods.js - Shape Creation and Interaction Methods
 * 
 * Extracted from topology.js for modular architecture.
 * All methods receive 'editor' as first parameter instead of using 'this'.
 */

'use strict';

window.ShapeMethods = {
    setupShapeToolbar(editor) {
        // Shape type buttons
        const shapeButtons = document.querySelectorAll('.shape-type-btn');
        shapeButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const shapeType = btn.dataset.shape;
                editor.selectShapeType(shapeType);
                editor.enterShapePlacementMode(shapeType);
                
                // Update button states
                shapeButtons.forEach(b => {
                    b.style.boxShadow = 'none';
                    b.style.transform = 'scale(1)';
                });
                btn.style.boxShadow = '0 0 0 2px rgba(52, 152, 219, 0.8)';
                btn.style.transform = 'scale(1.05)';
            });
            
            btn.addEventListener('mouseenter', () => {
                if (editor.currentShapeType !== btn.dataset.shape) {
                    btn.style.transform = 'scale(1.05)';
                    btn.style.filter = 'brightness(1.2)';
                }
            });
            btn.addEventListener('mouseleave', () => {
                if (editor.currentShapeType !== btn.dataset.shape) {
                    btn.style.transform = 'scale(1)';
                    btn.style.filter = 'none';
                }
            });
        });
        
        // Fill color controls
        const fillColorInput = document.getElementById('shape-fill-color');
        if (fillColorInput) {
            fillColorInput.addEventListener('input', (e) => {
                editor.shapeFillColor = e.target.value;
                editor.updateSelectedShapeStyle();
            });
        }
        
        const fillOpacityInput = document.getElementById('shape-fill-opacity');
        const fillOpacityValue = document.getElementById('shape-fill-opacity-value');
        if (fillOpacityInput) {
            fillOpacityInput.addEventListener('input', (e) => {
                // Store as 0-1 ratio (slider is 0-100)
                editor.shapeFillOpacity = parseInt(e.target.value) / 100;
                if (fillOpacityValue) fillOpacityValue.textContent = `${e.target.value}%`;
                editor.updateSelectedShapeStyle();
            });
        }
        
        const fillEnabledInput = document.getElementById('shape-fill-enabled');
        if (fillEnabledInput) {
            fillEnabledInput.addEventListener('change', (e) => {
                editor.shapeFillEnabled = e.target.checked;
                editor.updateSelectedShapeStyle();
            });
        }
        
        // Stroke color controls
        const strokeColorInput = document.getElementById('shape-stroke-color');
        if (strokeColorInput) {
            strokeColorInput.addEventListener('input', (e) => {
                editor.shapeStrokeColor = e.target.value;
                editor.updateSelectedShapeStyle();
            });
        }
        
        const strokeWidthInput = document.getElementById('shape-stroke-width');
        const strokeWidthValue = document.getElementById('shape-stroke-width-value');
        if (strokeWidthInput) {
            strokeWidthInput.addEventListener('input', (e) => {
                editor.shapeStrokeWidth = parseInt(e.target.value);
                if (strokeWidthValue) strokeWidthValue.textContent = `${editor.shapeStrokeWidth}px`;
                editor.updateSelectedShapeStyle();
            });
        }
        
        const strokeEnabledInput = document.getElementById('shape-stroke-enabled');
        if (strokeEnabledInput) {
            strokeEnabledInput.addEventListener('change', (e) => {
                editor.shapeStrokeEnabled = e.target.checked;
                editor.updateSelectedShapeStyle();
            });
        }
        
        // Grid snap
        const snapGridInput = document.getElementById('shape-snap-grid');
        if (snapGridInput) {
            snapGridInput.addEventListener('change', (e) => {
                editor.shapeSnapToGrid = e.target.checked;
            });
        }
    },

    selectShapeType(editor, shapeType) {
        editor.currentShapeType = shapeType;
        
        // Set default colors based on shape type - professional, vibrant palette
        const shapeColors = {
            rectangle: { fill: '#3498db', stroke: '#2980b9' },  // Blue
            circle: { fill: '#2ecc71', stroke: '#27ae60' },     // Green
            triangle: { fill: '#FF7A33', stroke: '#FF5E1F' },   // Orange
            diamond: { fill: '#9b59b6', stroke: '#8e44ad' },    // Purple
            checkmark: { fill: '#27ae60', stroke: '#1e8449' },  // Success green
            cross: { fill: '#e74c3c', stroke: '#c0392b' },      // Danger red
            arrow: { fill: '#34495e', stroke: '#2c3e50' },      // Dark slate
            star: { fill: '#f1c40f', stroke: '#d4ac0d' },       // Gold
            hexagon: { fill: '#FF5E1F', stroke: '#CC4A16' },    // Carrot orange
            ellipse: { fill: '#1abc9c', stroke: '#16a085' },    // Turquoise
            line: { fill: '#7f8c8d', stroke: '#6c7a7a' },       // Grey
            cloud: { fill: '#3498db', stroke: '#2980b9' }       // Sky blue
        };
        
        if (shapeColors[shapeType]) {
            editor.shapeFillColor = shapeColors[shapeType].fill;
            editor.shapeStrokeColor = shapeColors[shapeType].stroke;
            
            const fillColorInput = document.getElementById('shape-fill-color');
            const strokeColorInput = document.getElementById('shape-stroke-color');
            if (fillColorInput) fillColorInput.value = editor.shapeFillColor;
            if (strokeColorInput) strokeColorInput.value = editor.shapeStrokeColor;
        }
    },

    enterShapePlacementMode(editor, shapeType) {
        editor.placingShape = shapeType;
        editor.placingDevice = null;
        editor.setMode('shape');
        editor.canvas.style.cursor = 'crosshair';
        
        // Show mode indicator
        const indicator = document.getElementById('shape-mode-indicator');
        if (indicator) {
            indicator.style.display = 'inline-block';
            indicator.textContent = 'PLACING';
        }
        
        if (editor.debugger) {
            editor.debugger.logSuccess(`🔷 Shape placement mode: ${shapeType}`);
        }
    },

    exitShapePlacementMode(editor) {
        editor.placingShape = null;
        editor.setMode('base');
        editor.canvas.style.cursor = 'default';
        
        // Hide mode indicator
        const indicator = document.getElementById('shape-mode-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
        
        // Clear button selections
        const shapeButtons = document.querySelectorAll('.shape-type-btn');
        shapeButtons.forEach(btn => {
            btn.style.boxShadow = 'none';
            btn.style.transform = 'scale(1)';
        });
    },

    createShape(editor, x, y, shapeType) {
        // Snap to grid if enabled
        if (editor.shapeSnapToGrid) {
            const gridSize = 20;
            x = Math.round(x / gridSize) * gridSize;
            y = Math.round(y / gridSize) * gridSize;
        }
        
        const shapeNames = {
            rectangle: 'Rectangle',
            circle: 'Circle',
            triangle: 'Triangle',
            diamond: 'Diamond',
            checkmark: 'Checkmark',
            cross: 'Cross',
            arrow: 'Arrow',
            star: 'Star',
            hexagon: 'Hexagon',
            ellipse: 'Ellipse',
            line: 'Line',
            cloud: 'Cloud'
        };
        
        const shape = {
            type: 'shape',
            shapeType: shapeType || editor.currentShapeType,
            id: `shape_${editor.shapeIdCounter++}`,
            label: shapeNames[shapeType] || 'Shape', // Add label for debugging/display
            x: x,
            y: y,
            width: 80,
            height: shapeType === 'line' ? 2 : (shapeType === 'circle' ? 80 : 60),
            rotation: 0,
            fillColor: editor.shapeFillColor,
            fillOpacity: editor.shapeFillOpacity,
            fillEnabled: editor.shapeFillEnabled,
            strokeColor: editor.shapeStrokeColor,
            strokeWidth: editor.shapeStrokeWidth,
            strokeEnabled: editor.shapeStrokeEnabled,
            locked: false
        };
        
        // Adjust size based on shape type
        if (shapeType === 'checkmark' || shapeType === 'cross') {
            shape.width = 50;
            shape.height = 50;
        } else if (shapeType === 'arrow') {
            shape.width = 100;
            shape.height = 30;
        } else if (shapeType === 'star') {
            shape.width = 60;
            shape.height = 60;
        }
        
        editor.objects.push(shape);
        editor.saveState();
        editor.draw();
        
        if (editor.debugger) {
            editor.debugger.logSuccess(`🔷 Created ${shapeType} shape at (${Math.round(x)}, ${Math.round(y)})`);
        }
        
        return shape;
    },

    getShapeHandlePositions(editor, shape) {
        const x = shape.x;
        const y = shape.y;
        const w = shape.width;
        const h = shape.height;
        const handleSize = 12;
        const cornerHandleSize = 12;

        // Circle: 4 cardinal handles only (uniform radius)
        if (shape.shapeType === 'circle') {
            const r = w / 2;
            return [
                { x: x, y: y - r, id: 'n', size: handleSize, isCorner: false },
                { x: x, y: y + r, id: 's', size: handleSize, isCorner: false },
                { x: x - r, y: y, id: 'w', size: handleSize, isCorner: false },
                { x: x + r, y: y, id: 'e', size: handleSize, isCorner: false }
            ];
        }

        // Ellipse: 4 cardinal handles (stretch rx/ry independently)
        if (shape.shapeType === 'ellipse') {
            const rx = w / 2;
            const ry = h / 2;
            return [
                { x: x, y: y - ry, id: 'n', size: handleSize, isCorner: false },
                { x: x, y: y + ry, id: 's', size: handleSize, isCorner: false },
                { x: x - rx, y: y, id: 'w', size: handleSize, isCorner: false },
                { x: x + rx, y: y, id: 'e', size: handleSize, isCorner: false }
            ];
        }

        // Diamond: 4 vertex handles at cardinal points (uniform scale)
        if (shape.shapeType === 'diamond') {
            return [
                { x: x, y: y - h/2, id: 'n', size: handleSize, isCorner: false },
                { x: x, y: y + h/2, id: 's', size: handleSize, isCorner: false },
                { x: x - w/2, y: y, id: 'w', size: handleSize, isCorner: false },
                { x: x + w/2, y: y, id: 'e', size: handleSize, isCorner: false }
            ];
        }

        // Triangle/Star/Hexagon/Checkmark/Cross: 4 bounding-box edge handles (uniform scale)
        if (['triangle', 'star', 'hexagon', 'checkmark', 'cross'].includes(shape.shapeType)) {
            return [
                { x: x, y: y - h/2, id: 'n', size: handleSize, isCorner: false },
                { x: x, y: y + h/2, id: 's', size: handleSize, isCorner: false },
                { x: x - w/2, y: y, id: 'w', size: handleSize, isCorner: false },
                { x: x + w/2, y: y, id: 'e', size: handleSize, isCorner: false }
            ];
        }

        // Rectangle/Cloud: 8 handles (4 corners + 4 edges) for free stretching
        return [
            { x: x - w/2, y: y - h/2, id: 'nw', size: cornerHandleSize, isCorner: true },
            { x: x + w/2, y: y - h/2, id: 'ne', size: cornerHandleSize, isCorner: true },
            { x: x - w/2, y: y + h/2, id: 'sw', size: cornerHandleSize, isCorner: true },
            { x: x + w/2, y: y + h/2, id: 'se', size: cornerHandleSize, isCorner: true },
            { x: x, y: y - h/2, id: 'n', size: handleSize, isCorner: false },
            { x: x, y: y + h/2, id: 's', size: handleSize, isCorner: false },
            { x: x - w/2, y: y, id: 'w', size: handleSize, isCorner: false },
            { x: x + w/2, y: y, id: 'e', size: handleSize, isCorner: false }
        ];
    },

    findShapeAt(editor, x, y) {
        // Search in reverse order (top-most first)
        for (let i = editor.objects.length - 1; i >= 0; i--) {
            const obj = editor.objects[i];
            if (obj.type !== 'shape') continue;
            
            const dx = x - obj.x;
            const dy = y - obj.y;
            
            // Handle rotation - transform click point to shape's local coordinate system
            let localX = dx;
            let localY = dy;
            if (obj.rotation) {
                const angle = -(obj.rotation || 0) * Math.PI / 180;
                localX = dx * Math.cos(angle) - dy * Math.sin(angle);
                localY = dx * Math.sin(angle) + dy * Math.cos(angle);
            }
            
            // Use shape's actual dimensions with tolerance
            const zoomTolerance = Math.max(5, 10 / editor.zoom);
            const hw = (obj.width || 100) / 2;
            const hh = (obj.height || 100) / 2;
            
            // Shape-specific hit detection
            let isHit = false;
            switch (obj.shapeType) {
                case 'circle': {
                    // Circle: check distance from center
                    const radius = hw + zoomTolerance;
                    const dist = Math.sqrt(localX * localX + localY * localY);
                    isHit = dist <= radius;
                    break;
                }
                case 'ellipse': {
                    // Ellipse: normalized equation (x/a)² + (y/b)² <= 1
                    const a = hw + zoomTolerance;
                    const b = hh + zoomTolerance;
                    const normalizedDist = (localX * localX) / (a * a) + (localY * localY) / (b * b);
                    isHit = normalizedDist <= 1;
                    break;
                }
                case 'diamond': {
                    // Diamond: |x|/hw + |y|/hh <= 1
                    const normalizedDist = Math.abs(localX) / (hw + zoomTolerance) + Math.abs(localY) / (hh + zoomTolerance);
                    isHit = normalizedDist <= 1;
                    break;
                }
                case 'cloud': {
                    // Cloud: use ellipse approximation
                    const a = hw + zoomTolerance;
                    const b = hh + zoomTolerance;
                    const normalizedDist = (localX * localX) / (a * a) + (localY * localY) / (b * b);
                    isHit = normalizedDist <= 1;
                    break;
                }
                default:
                    // Rectangle: bounding box
                    isHit = Math.abs(localX) <= hw + zoomTolerance && Math.abs(localY) <= hh + zoomTolerance;
            }
            
            if (isHit) {
                return obj;
            }
        }
        return null;
    },

    findShapeResizeHandle(editor, shape, x, y) {
        if (!shape || shape.type !== 'shape') return null;
        
        // Scale by zoom - when zoomed out, handles need larger world-coord hit area
        // Larger hit areas to match the larger visual handles
        const zoomScale = Math.max(1, 1 / editor.zoom);
        const cornerHitSize = 20 * zoomScale;
        const edgeHitSize = 18 * zoomScale;
        const rotationHitSize = 18 * zoomScale;
        
        // Transform click position to shape's local coordinate system (undo rotation)
        const rotation = shape.rotation || 0;
        const radians = -rotation * Math.PI / 180;
        const cos = Math.cos(radians);
        const sin = Math.sin(radians);
        
        // Translate to shape center, rotate, translate back
        const dx = x - shape.x;
        const dy = y - shape.y;
        const localX = shape.x + dx * cos - dy * sin;
        const localY = shape.y + dx * sin + dy * cos;
        
        // Check rotation handle first (highest priority) - in local coords
        // Rotation handle is at top-right corner (matching device style)
        const rotHandleOffset = 15 * zoomScale;
        const halfW = shape.width / 2;
        const halfH = shape.height / 2;
        const rotHandleX = shape.x + halfW + rotHandleOffset;
        const rotHandleY = shape.y - halfH - rotHandleOffset;
        const rotationDx = localX - rotHandleX;
        const rotationDy = localY - rotHandleY;
        if (Math.sqrt(rotationDx * rotationDx + rotationDy * rotationDy) <= rotationHitSize) {
            return 'rotation';
        }
        
        // Use the same handle positions as drawing (in local coords)
        const handlePositions = editor.getShapeHandlePositions(shape);
        
        // Check corners first (higher priority, larger targets)
        const corners = handlePositions.filter(h => h.isCorner);
        for (const handle of corners) {
            const hdx = localX - handle.x;
            const hdy = localY - handle.y;
            // For square handles, use box collision
            if (Math.abs(hdx) <= cornerHitSize && Math.abs(hdy) <= cornerHitSize) {
                return handle.id;
            }
        }
        
        // Then check edges
        const edges = handlePositions.filter(h => !h.isCorner);
        for (const handle of edges) {
            const hdx = localX - handle.x;
            const hdy = localY - handle.y;
            // For circle handles, use distance
            if (Math.sqrt(hdx * hdx + hdy * hdy) <= edgeHitSize) {
                return handle.id;
            }
        }
        
        return null;
    }
};

console.log('[topology-shape-methods.js] ShapeMethods loaded');
