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

    _resizeHandleDirections() {
        return [
            { id: 'nw', dx: -1, dy: -1, isCorner: true },
            { id: 'ne', dx: 1, dy: -1, isCorner: true },
            { id: 'sw', dx: -1, dy: 1, isCorner: true },
            { id: 'se', dx: 1, dy: 1, isCorner: true },
            { id: 'n', dx: 0, dy: -1, isCorner: false },
            { id: 's', dx: 0, dy: 1, isCorner: false },
            { id: 'w', dx: -1, dy: 0, isCorner: false },
            { id: 'e', dx: 1, dy: 0, isCorner: false }
        ];
    },

    _shapePolygonPoints(shape) {
        const w = shape.width || 80;
        const h = shape.height || 60;
        const hw = w / 2;
        const hh = h / 2;
        switch (shape.shapeType) {
            case 'triangle':
                return [{ x: 0, y: -hh }, { x: hw, y: hh }, { x: -hw, y: hh }];
            case 'diamond':
                return [{ x: 0, y: -hh }, { x: hw, y: 0 }, { x: 0, y: hh }, { x: -hw, y: 0 }];
            case 'hexagon': {
                const points = [];
                for (let i = 0; i < 6; i++) {
                    const angle = (i * 60 - 90) * Math.PI / 180;
                    points.push({ x: hw * Math.cos(angle), y: hh * Math.sin(angle) });
                }
                return points;
            }
            case 'star': {
                const points = [];
                for (let i = 0; i < 10; i++) {
                    const radiusX = i % 2 === 0 ? hw : hw / 2;
                    const radiusY = i % 2 === 0 ? hh : hh / 2;
                    const angle = (i * 36 - 90) * Math.PI / 180;
                    points.push({ x: radiusX * Math.cos(angle), y: radiusY * Math.sin(angle) });
                }
                return points;
            }
            case 'cloud':
                return [
                    { x: -w * 0.425, y: h * 0.135 },
                    { x: -w * 0.525, y: -h * 0.1575 },
                    { x: -w * 0.125, y: -h * 0.3825 },
                    { x: w * 0.15, y: -h * 0.4275 },
                    { x: w * 0.4, y: -h * 0.3375 },
                    { x: w * 0.5, y: h * 0.135 }
                ];
            default:
                return null;
        }
    },

    _rayPolygonIntersection(points, dx, dy) {
        if (!Array.isArray(points) || points.length < 2) return null;
        let best = null;
        for (let i = 0; i < points.length; i++) {
            const a = points[i];
            const b = points[(i + 1) % points.length];
            const sx = b.x - a.x;
            const sy = b.y - a.y;
            const denom = dx * sy - dy * sx;
            if (Math.abs(denom) < 1e-9) continue;
            const t = (a.x * sy - a.y * sx) / denom;
            const u = (a.x * dy - a.y * dx) / denom;
            if (t >= -1e-9 && u >= -1e-9 && u <= 1 + 1e-9) {
                if (!best || t > best.t) best = { t, x: dx * t, y: dy * t };
            }
        }
        return best ? { x: best.x, y: best.y } : null;
    },

    _ellipseBoundaryPoint(rx, ry, dx, dy) {
        const denom = Math.sqrt((dx * dx) / (rx * rx) + (dy * dy) / (ry * ry));
        if (!denom) return { x: 0, y: 0 };
        return { x: dx / denom, y: dy / denom };
    },

    _distanceToSegment(px, py, ax, ay, bx, by) {
        const dx = bx - ax;
        const dy = by - ay;
        const lenSq = dx * dx + dy * dy;
        if (lenSq <= 1e-9) return Math.hypot(px - ax, py - ay);
        const t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / lenSq));
        return Math.hypot(px - (ax + dx * t), py - (ay + dy * t));
    },

    _pointInPolygon(points, px, py) {
        if (!Array.isArray(points) || points.length < 3) return false;
        let inside = false;
        for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
            const xi = points[i].x;
            const yi = points[i].y;
            const xj = points[j].x;
            const yj = points[j].y;
            const intersects = ((yi > py) !== (yj > py)) &&
                (px < (xj - xi) * (py - yi) / ((yj - yi) || 1e-9) + xi);
            if (intersects) inside = !inside;
        }
        return inside;
    },

    _distanceToPolyline(points, px, py, closed = false) {
        if (!Array.isArray(points) || points.length < 2) return Infinity;
        let minDist = Infinity;
        const end = closed ? points.length : points.length - 1;
        for (let i = 0; i < end; i++) {
            const a = points[i];
            const b = points[(i + 1) % points.length];
            minDist = Math.min(minDist, this._distanceToSegment(px, py, a.x, a.y, b.x, b.y));
        }
        return minDist;
    },

    _shapeLocalPath(shape) {
        const w = shape.width || 80;
        const h = shape.height || 60;
        const hw = w / 2;
        const hh = h / 2;
        switch (shape.shapeType) {
            case 'line':
                return { points: [{ x: -hw, y: 0 }, { x: hw, y: 0 }], closed: false };
            case 'checkmark':
                return {
                    points: [
                        { x: -w / 3, y: 0 },
                        { x: -w / 10, y: h / 3 },
                        { x: w / 3, y: -h / 3 }
                    ],
                    closed: false
                };
            case 'cross':
                return {
                    segments: [
                        [{ x: -w / 3, y: -h / 3 }, { x: w / 3, y: h / 3 }],
                        [{ x: w / 3, y: -h / 3 }, { x: -w / 3, y: h / 3 }]
                    ],
                    closed: false
                };
            case 'arrow':
                return {
                    segments: [
                        [{ x: -hw, y: 0 }, { x: w / 4, y: 0 }],
                        [{ x: w / 4 - h / 2, y: -hh }, { x: hw, y: 0 }],
                        [{ x: hw, y: 0 }, { x: w / 4 - h / 2, y: hh }]
                    ],
                    closed: false
                };
            default: {
                const points = this._shapePolygonPoints(shape);
                return points ? { points, closed: true } : null;
            }
        }
    },

    _shapeGeometryHitLocal(shape, localX, localY, tolerance = 0, options = {}) {
        const w = shape.width || 80;
        const h = shape.height || 60;
        const hw = w / 2;
        const hh = h / 2;
        const strokeWidth = Math.max(1, Number(shape.strokeWidth) || 2);
        const strokeTolerance = Math.max(tolerance, strokeWidth / 2 + tolerance);
        const fillEnabled = shape.fillEnabled !== false && !options.borderOnly;
        const shapeType = shape.shapeType || 'rectangle';

        if (shapeType === 'circle') {
            const r = Math.max(1, w / 2);
            const dist = Math.hypot(localX, localY);
            return fillEnabled
                ? dist <= r + tolerance
                : Math.abs(dist - r) <= strokeTolerance;
        }

        if (shapeType === 'ellipse' || shapeType === 'cloud') {
            const rx = Math.max(1, hw);
            const ry = Math.max(1, hh);
            const normalized = (localX * localX) / (rx * rx) + (localY * localY) / (ry * ry);
            if (fillEnabled && normalized <= 1) return true;
            const boundary = this._ellipseBoundaryPoint(rx, ry, localX || 1e-9, localY || 0);
            return Math.hypot(localX - boundary.x, localY - boundary.y) <= strokeTolerance;
        }

        if (shapeType === 'rectangle') {
            const inside = Math.abs(localX) <= hw + tolerance && Math.abs(localY) <= hh + tolerance;
            if (!inside) return false;
            if (fillEnabled) return true;
            const edgeDist = Math.min(Math.abs(hw - Math.abs(localX)), Math.abs(hh - Math.abs(localY)));
            return edgeDist <= strokeTolerance;
        }

        const path = this._shapeLocalPath(shape);
        if (path?.segments) {
            return path.segments.some(segment => (
                this._distanceToSegment(localX, localY, segment[0].x, segment[0].y, segment[1].x, segment[1].y) <= strokeTolerance
            ));
        }

        if (path?.points) {
            const inside = path.closed && this._pointInPolygon(path.points, localX, localY);
            if (fillEnabled && inside) return true;
            return this._distanceToPolyline(path.points, localX, localY, path.closed) <= strokeTolerance;
        }

        const insideFallback = Math.abs(localX) <= hw + tolerance && Math.abs(localY) <= hh + tolerance;
        return fillEnabled ? insideFallback : false;
    },

    hitTestShape(editor, shape, x, y, options = {}) {
        if (!shape || shape.type !== 'shape') return false;
        const dx = x - shape.x;
        const dy = y - shape.y;
        let localX = dx;
        let localY = dy;
        if (shape.rotation) {
            const angle = -(shape.rotation || 0) * Math.PI / 180;
            localX = dx * Math.cos(angle) - dy * Math.sin(angle);
            localY = dx * Math.sin(angle) + dy * Math.cos(angle);
        }

        const zoom = editor && Number.isFinite(editor.zoom) && editor.zoom > 0 ? editor.zoom : 1;
        const screenTolerance = Number.isFinite(options.screenTolerance)
            ? options.screenTolerance
            : (shape.mergedToBackground || shape.fillEnabled === false ? 7 : 4);
        const tolerance = Math.max(0, screenTolerance / zoom);
        return this._shapeGeometryHitLocal(shape, localX, localY, tolerance, {
            borderOnly: !!options.borderOnly
        });
    },

    _shapeLocalHandlePoint(shape, handle) {
        const w = shape.width || 80;
        const h = shape.height || 60;
        const hw = w / 2;
        const hh = h / 2;
        const dx = handle.dx;
        const dy = handle.dy;

        switch (shape.shapeType) {
            case 'rectangle':
                return { x: dx * hw, y: dy * hh };
            case 'circle': {
                const r = w / 2;
                const len = Math.hypot(dx, dy) || 1;
                return { x: r * dx / len, y: r * dy / len };
            }
            case 'ellipse':
                return this._ellipseBoundaryPoint(hw, hh, dx, dy);
            case 'line':
                if (handle.id === 'w') return { x: -hw, y: 0 };
                if (handle.id === 'e') return { x: hw, y: 0 };
                return null;
            case 'checkmark': {
                const points = [
                    { x: -w / 3, y: 0 },
                    { x: -w / 10, y: h / 3 },
                    { x: w / 3, y: -h / 3 }
                ];
                const byId = {
                    w: points[0],
                    s: points[1],
                    e: points[2],
                    n: points[2],
                    sw: points[0],
                    se: points[1],
                    ne: points[2]
                };
                return byId[handle.id] || null;
            }
            case 'cross': {
                const byId = {
                    nw: { x: -w / 3, y: -h / 3 },
                    ne: { x: w / 3, y: -h / 3 },
                    sw: { x: -w / 3, y: h / 3 },
                    se: { x: w / 3, y: h / 3 },
                    n: { x: 0, y: -h / 3 },
                    s: { x: 0, y: h / 3 },
                    w: { x: -w / 3, y: 0 },
                    e: { x: w / 3, y: 0 }
                };
                return byId[handle.id] || null;
            }
            case 'arrow': {
                const byId = {
                    w: { x: -hw, y: 0 },
                    e: { x: hw, y: 0 },
                    n: { x: w / 4 - h / 2, y: -hh },
                    s: { x: w / 4 - h / 2, y: hh },
                    nw: { x: -hw, y: 0 },
                    ne: { x: w / 4 - h / 2, y: -hh },
                    sw: { x: -hw, y: 0 },
                    se: { x: w / 4 - h / 2, y: hh }
                };
                return byId[handle.id] || null;
            }
            default: {
                const points = this._shapePolygonPoints(shape);
                const point = this._rayPolygonIntersection(points, dx, dy);
                return point || { x: dx * hw, y: dy * hh };
            }
        }
    },

    getShapeHandlePositions(editor, shape) {
        const x = shape.x;
        const y = shape.y;
        const handleSize = 12;
        const cornerHandleSize = 12;
        return this._resizeHandleDirections()
            .map(handle => {
                const local = this._shapeLocalHandlePoint(shape, handle);
                if (!local) return null;
                return {
                    x: x + local.x,
                    y: y + local.y,
                    id: handle.id,
                    size: handle.isCorner ? cornerHandleSize : handleSize,
                    isCorner: handle.isCorner
                };
            })
            .filter(Boolean);
    },

    findShapeAt(editor, x, y) {
        // Search in reverse order (top-most first)
        for (let i = editor.objects.length - 1; i >= 0; i--) {
            const obj = editor.objects[i];
            if (obj.type !== 'shape') continue;

            if (this.hitTestShape(editor, obj, x, y, { borderOnly: obj.mergedToBackground })) {
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
    },

    // ========================================================================
    // CONTAINER SHAPE HELPERS (2026-04-26)
    // ------------------------------------------------------------------------
    // A "container" is a shape with `containerMode: true`. When such a shape
    // is dragged, every object whose centre falls inside the shape's
    // bounding region moves with it as a single unit. This is how the AI
    // generator emits AS / OSPF area / VRF / tenant boundaries that stay
    // tidy when the user reorganises the diagram.
    //
    // Implementation notes:
    //   * Containment is computed at drag-START (a snapshot), not on every
    //     mouse move. This avoids "swallowing" objects the user happens to
    //     drag through and keeps drag latency tiny.
    //   * Hit-testing uses the same per-shape geometry as findShapeAt so the
    //     visible boundary matches the container boundary.
    //   * A container never contains itself, and it does not contain other
    //     container shapes that are LARGER than it (prevents swapping
    //     parent/child during nested drag).
    //   * Links are NOT captured -- they re-render automatically when their
    //     endpoint devices move. Unbound links ARE captured (they own
    //     `start`/`end` coords).
    // ========================================================================

    isPointInsideShape(shape, px, py) {
        if (!shape || shape.type !== 'shape') return false;
        const dx = px - shape.x;
        const dy = py - shape.y;
        let lx = dx;
        let ly = dy;
        if (shape.rotation) {
            const a = -shape.rotation * Math.PI / 180;
            lx = dx * Math.cos(a) - dy * Math.sin(a);
            ly = dx * Math.sin(a) + dy * Math.cos(a);
        }
        return this._shapeGeometryHitLocal(shape, lx, ly, 0, { borderOnly: false });
    },

    objectCenter(obj) {
        if (!obj) return null;
        if (obj.type === 'unbound') {
            const sx = obj.start ? obj.start.x : null;
            const sy = obj.start ? obj.start.y : null;
            const ex = obj.end ? obj.end.x : null;
            const ey = obj.end ? obj.end.y : null;
            if (sx == null || ex == null) return null;
            return { x: (sx + ex) / 2, y: (sy + ey) / 2 };
        }
        if (typeof obj.x === 'number' && typeof obj.y === 'number') {
            return { x: obj.x, y: obj.y };
        }
        return null;
    },

    /**
     * Return the snapshot of objects to drag together with a container shape.
     * Each entry has the captured initial position so the move handler can
     * apply a clean delta without drift.
     *
     * @param {object} editor - the canvas editor
     * @param {object} shape - the container shape being dragged
     * @returns {Array<{obj:object, type:string, startX:number, startY:number, startEnd?:{x:number,y:number}}>}
     */
    getContainerChildren(editor, shape) {
        if (!shape || shape.type !== 'shape' || !shape.containerMode) return [];
        const out = [];
        const objs = editor.objects || [];
        const shapeArea = (shape.width || 100) * (shape.height || 100);
        for (let i = 0; i < objs.length; i++) {
            const obj = objs[i];
            if (!obj || obj === shape) continue;
            // Skip pure links (they follow their endpoints automatically).
            if (obj.type === 'link') continue;
            // Skip larger container shapes so we never swallow our parent.
            if (obj.type === 'shape' && obj.containerMode) {
                const otherArea = (obj.width || 100) * (obj.height || 100);
                if (otherArea >= shapeArea) continue;
            }
            // Hidden / collapsed objects should not be dragged.
            if (obj.hidden === true) continue;
            const c = window.ShapeMethods.objectCenter(obj);
            if (!c) continue;
            if (!window.ShapeMethods.isPointInsideShape(shape, c.x, c.y)) continue;
            const entry = {
                obj: obj,
                type: obj.type,
                startX: typeof obj.x === 'number' ? obj.x : null,
                startY: typeof obj.y === 'number' ? obj.y : null,
            };
            if (obj.type === 'unbound' && obj.start && obj.end) {
                entry.startStart = { x: obj.start.x, y: obj.start.y };
                entry.startEnd = { x: obj.end.x, y: obj.end.y };
            }
            out.push(entry);
        }
        return out;
    },

    /**
     * Apply a delta (dx, dy) to every captured container child. Used by
     * topology-mouse-move.js while a container shape is being dragged.
     */
    applyContainerDelta(children, dx, dy) {
        if (!Array.isArray(children) || children.length === 0) return;
        for (let i = 0; i < children.length; i++) {
            const c = children[i];
            if (!c || !c.obj) continue;
            if (c.type === 'unbound' && c.startStart && c.startEnd) {
                if (c.obj.start) {
                    c.obj.start.x = c.startStart.x + dx;
                    c.obj.start.y = c.startStart.y + dy;
                }
                if (c.obj.end) {
                    c.obj.end.x = c.startEnd.x + dx;
                    c.obj.end.y = c.startEnd.y + dy;
                }
                continue;
            }
            if (c.startX !== null && typeof c.obj.x === 'number') {
                c.obj.x = c.startX + dx;
            }
            if (c.startY !== null && typeof c.obj.y === 'number') {
                c.obj.y = c.startY + dy;
            }
        }
    },
};

console.log('[topology-shape-methods.js] ShapeMethods loaded');
