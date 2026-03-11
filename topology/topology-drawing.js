// ============================================================================
// TOPOLOGY DRAWING MANAGER
// ============================================================================
// Handles canvas rendering and drawing operations.
// Migrating drawing code from topology.js incrementally.
//
// Usage:
//   editor.drawing.draw();
//   editor.drawing.drawObject(obj);
//   editor.drawing.drawGrid();
// ============================================================================

class DrawingManager {
    constructor(editor) {
        this.editor = editor;
        
        // Grid settings
        this.gridSize = 50; // Base grid size in world coordinates
        this.gridMargin = 500; // Extra margin for smooth panning
        
        // Rendering settings
        this.highQuality = true;
    }

    // ========================================================================
    // ACCESSORS (shortcuts to editor properties)
    // ========================================================================
    
    get ctx() { return this.editor.ctx; }
    get canvas() { return this.editor.canvas; }
    get zoom() { return this.editor.zoom; }
    get panOffset() { return this.editor.panOffset; }
    get darkMode() { return this.editor.darkMode; }
    get objects() { return this.editor.objects; }

    // ========================================================================
    // MAIN DRAW FUNCTIONS
    // ========================================================================

    /**
     * Main draw function - renders entire canvas
     * Delegates to editor.draw() for now (will migrate incrementally)
     */
    draw() {
        if (typeof this.editor.draw === 'function') {
            this.editor.draw();
        }
    }

    /**
     * Draw a specific object
     * @param {object} obj - Object to draw
     */
    drawObject(obj) {
        if (!obj || !this.ctx) return;
        
        switch (obj.type) {
            case 'device':
                this.drawDevice(obj);
                break;
            case 'link':
            case 'unbound':
                this.drawLink(obj);
                break;
            case 'text':
                this.drawText(obj);
                break;
            case 'shape':
                this.drawShape(obj);
                break;
        }
    }

    /**
     * Draw a device - delegates to editor
     * @param {object} device - Device object
     */
    drawDevice(device) {
        if (typeof this.editor.drawDevice === 'function') {
            this.editor.drawDevice(device);
        }
    }

    /**
     * Draw a link - delegates to editor
     * @param {object} link - Link object
     */
    drawLink(link) {
        if (typeof this.editor.drawLink === 'function') {
            this.editor.drawLink(link);
        }
    }

    /**
     * Draw a text box - delegates to editor
     * @param {object} text - Text object
     */
    drawText(text) {
        if (typeof this.editor.drawText === 'function') {
            this.editor.drawText(text);
        }
    }

    /**
     * Draw a shape - delegates to editor
     * @param {object} shape - Shape object
     */
    drawShape(shape) {
        if (typeof this.editor.drawShape === 'function') {
            this.editor.drawShape(shape);
        }
    }

    // ========================================================================
    // GRID DRAWING (MIGRATED FROM topology.js)
    // ========================================================================

    /**
     * Draw infinite grid that zooms with canvas - Notebook style
     * MIGRATED from topology.js drawGrid()
     */
    drawGrid() {
        if (!this.ctx || !this.canvas) return;
        
        const gridSize = this.gridSize;
        const margin = this.gridMargin;
        
        // Calculate extended visible area (draw beyond viewport for smooth panning)
        const startX = (-this.panOffset.x / this.zoom) - margin;
        const startY = (-this.panOffset.y / this.zoom) - margin;
        const cw = this.editor ? this.editor.canvasW : this.canvas.width;
        const ch = this.editor ? this.editor.canvasH : this.canvas.height;
        const endX = startX + (cw / this.zoom) + margin * 2;
        const endY = startY + (ch / this.zoom) + margin * 2;
        
        this.ctx.save();
        this.ctx.translate(this.panOffset.x, this.panOffset.y);
        this.ctx.scale(this.zoom, this.zoom);
        
        // Adjust grid color for dark mode
        this.ctx.strokeStyle = this.darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)';
        this.ctx.lineWidth = 1 / this.zoom;
        
        // Draw vertical lines
        const gridStartX = Math.floor(startX / gridSize) * gridSize;
        for (let x = gridStartX; x <= endX; x += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, startY);
            this.ctx.lineTo(x, endY);
            this.ctx.stroke();
        }
        
        // Draw horizontal lines
        const gridStartY = Math.floor(startY / gridSize) * gridSize;
        for (let y = gridStartY; y <= endY; y += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(startX, y);
            this.ctx.lineTo(endX, y);
            this.ctx.stroke();
        }
        
        this.ctx.restore();
    }

    // ========================================================================
    // CANVAS UTILITIES
    // ========================================================================

    /**
     * Clear the canvas with appropriate background
     */
    clearCanvas() {
        if (!this.ctx || !this.canvas) return;
        const cw = this.editor ? this.editor.canvasW : this.canvas.width;
        const ch = this.editor ? this.editor.canvasH : this.canvas.height;
        
        if (this.darkMode) {
            this.ctx.fillStyle = '#1a1a1a';
            this.ctx.fillRect(0, 0, cw, ch);
        } else {
            this.ctx.clearRect(0, 0, cw, ch);
        }
    }

    /**
     * Set up high-quality rendering
     */
    setupHighQualityRendering() {
        if (!this.ctx) return;
        
        this.ctx.imageSmoothingEnabled = true;
        this.ctx.imageSmoothingQuality = 'high';
        this.ctx.lineJoin = 'round';
        this.ctx.lineCap = 'round';
    }

    /**
     * Begin a transformed drawing context (with pan and zoom)
     */
    beginTransformed() {
        if (!this.ctx) return;
        
        this.ctx.save();
        // Translate to half-pixel boundaries for sharper rendering
        this.ctx.translate(Math.round(this.panOffset.x) + 0.5, Math.round(this.panOffset.y) + 0.5);
        this.ctx.scale(this.zoom, this.zoom);
    }

    /**
     * End transformed drawing context
     */
    endTransformed() {
        if (!this.ctx) return;
        this.ctx.restore();
    }

    /**
     * Convert screen coordinates to world coordinates
     * @param {number} screenX 
     * @param {number} screenY 
     * @returns {{x: number, y: number}}
     */
    screenToWorld(screenX, screenY) {
        return {
            x: (screenX - this.panOffset.x) / this.zoom,
            y: (screenY - this.panOffset.y) / this.zoom
        };
    }

    /**
     * Convert world coordinates to screen coordinates
     * @param {number} worldX 
     * @param {number} worldY 
     * @returns {{x: number, y: number}}
     */
    worldToScreen(worldX, worldY) {
        return {
            x: worldX * this.zoom + this.panOffset.x,
            y: worldY * this.zoom + this.panOffset.y
        };
    }

    /**
     * Get visible bounds in world coordinates
     * @returns {{minX: number, minY: number, maxX: number, maxY: number, width: number, height: number}}
     */
    getVisibleBounds() {
        const cw = this.editor ? this.editor.canvasW : this.canvas.width;
        const ch = this.editor ? this.editor.canvasH : this.canvas.height;
        const minX = -this.panOffset.x / this.zoom;
        const minY = -this.panOffset.y / this.zoom;
        const width = cw / this.zoom;
        const height = ch / this.zoom;
        
        return {
            minX,
            minY,
            maxX: minX + width,
            maxY: minY + height,
            width,
            height
        };
    }

    /**
     * Check if a point is visible on screen
     * @param {number} x - World X
     * @param {number} y - World Y
     * @param {number} margin - Extra margin
     * @returns {boolean}
     */
    isPointVisible(x, y, margin = 0) {
        const bounds = this.getVisibleBounds();
        return x >= bounds.minX - margin && x <= bounds.maxX + margin &&
               y >= bounds.minY - margin && y <= bounds.maxY + margin;
    }

    /**
     * Check if a rectangle is visible on screen
     * @param {number} x - World X
     * @param {number} y - World Y
     * @param {number} width 
     * @param {number} height 
     * @returns {boolean}
     */
    isRectVisible(x, y, width, height) {
        const bounds = this.getVisibleBounds();
        return x + width >= bounds.minX && x <= bounds.maxX &&
               y + height >= bounds.minY && y <= bounds.maxY;
    }

    // ========================================================================
    // PERFORMANCE OPTIMIZATIONS
    // ========================================================================

    /**
     * Request a redraw (use for external triggers)
     * Uses requestAnimationFrame for smooth, throttled updates
     */
    requestRedraw() {
        if (this._pendingRedraw) return; // Already scheduled
        
        this._pendingRedraw = true;
        requestAnimationFrame(() => {
            this._pendingRedraw = false;
            this.draw();
        });
    }
    
    /**
     * Mark canvas as dirty (needs redraw)
     * Use this for deferred/batched redraws
     */
    markDirty() {
        this._isDirty = true;
        this.requestRedraw();
    }
    
    /**
     * Check if an object is visible in the current viewport
     * Used for viewport culling to skip drawing off-screen objects
     * @param {object} obj - Object to check
     * @param {number} margin - Extra margin around viewport
     * @returns {boolean}
     */
    isObjectVisible(obj, margin = 100) {
        if (!obj) return false;
        
        const bounds = this.getVisibleBounds();
        
        // Handle different object types
        if (obj.type === 'device') {
            const radius = obj.radius || 30;
            return obj.x + radius >= bounds.minX - margin &&
                   obj.x - radius <= bounds.maxX + margin &&
                   obj.y + radius >= bounds.minY - margin &&
                   obj.y - radius <= bounds.maxY + margin;
        }
        
        if (obj.type === 'link' || obj.type === 'unbound') {
            const startX = obj.start?.x ?? obj.startPoint?.x ?? 0;
            const startY = obj.start?.y ?? obj.startPoint?.y ?? 0;
            const endX = obj.end?.x ?? obj.endPoint?.x ?? 0;
            const endY = obj.end?.y ?? obj.endPoint?.y ?? 0;
            
            const minX = Math.min(startX, endX);
            const maxX = Math.max(startX, endX);
            const minY = Math.min(startY, endY);
            const maxY = Math.max(startY, endY);
            
            return maxX >= bounds.minX - margin &&
                   minX <= bounds.maxX + margin &&
                   maxY >= bounds.minY - margin &&
                   minY <= bounds.maxY + margin;
        }
        
        if (obj.type === 'text' || obj.type === 'shape') {
            const x = obj.x || 0;
            const y = obj.y || 0;
            const width = obj.width || 100;
            const height = obj.height || 50;
            
            return x + width >= bounds.minX - margin &&
                   x <= bounds.maxX + margin &&
                   y + height >= bounds.minY - margin &&
                   y <= bounds.maxY + margin;
        }
        
        // Default: assume visible
        return true;
    }
    
    /**
     * Get visible objects (viewport culling)
     * @param {array} objects - All objects
     * @param {number} margin - Extra margin
     * @returns {array} Visible objects only
     */
    getVisibleObjects(objects, margin = 100) {
        if (!objects || !Array.isArray(objects)) return [];
        return objects.filter(obj => this.isObjectVisible(obj, margin));
    }
    
    /**
     * Batch draw operations with a single requestAnimationFrame
     * @param {function[]} operations - Array of draw operations
     */
    batchDraw(operations) {
        if (!operations || operations.length === 0) return;
        
        requestAnimationFrame(() => {
            operations.forEach(op => {
                if (typeof op === 'function') {
                    op();
                }
            });
        });
    }
    
    /**
     * Get rendering statistics
     * @returns {object} Stats
     */
    getStats() {
        const objects = this.objects || [];
        const visible = this.getVisibleObjects(objects);
        
        return {
            totalObjects: objects.length,
            visibleObjects: visible.length,
            culledObjects: objects.length - visible.length,
            zoom: this.zoom,
            isDirty: this._isDirty || false,
            pendingRedraw: this._pendingRedraw || false
        };
    }

    /**
     * Get canvas context
     * @returns {CanvasRenderingContext2D}
     */
    getContext() {
        return this.ctx;
    }

    /**
     * Get canvas element
     * @returns {HTMLCanvasElement}
     */
    getCanvas() {
        return this.canvas;
    }
    
    /**
     * Get current zoom level
     * @returns {number}
     */
    getZoom() {
        return this.zoom;
    }
    
    /**
     * Get pan offset
     * @returns {{x: number, y: number}}
     */
    getPanOffset() {
        return this.panOffset;
    }
}

// Export for use
window.DrawingManager = DrawingManager;

window.createDrawingManager = function(editor) {
    return new DrawingManager(editor);
};

console.log('[topology-drawing.js] DrawingManager with grid, utilities loaded');
