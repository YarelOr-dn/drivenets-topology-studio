// ============================================================================
// TOPOLOGY SHAPE MANAGER MODULE
// ============================================================================
// Handles shape creation, drawing, selection, and styling.
// This is a wrapper module that delegates to editor methods.
//
// Supported shapes: rectangle, ellipse, line, arrow, diamond
//
// Usage:
//   const shapeMgr = new ShapeManager(editor);
//   shapeMgr.create(100, 200, 'rectangle');
//   shapeMgr.selectType('ellipse');
// ============================================================================

class ShapeManager {
    constructor(editor) {
        this.editor = editor;
        
        // Shape types supported
        this.shapeTypes = ['rectangle', 'ellipse', 'line', 'arrow', 'diamond'];
    }

    // ========== CREATION ==========
    
    /**
     * Create a new shape at position
     * @param {number} x - World X coordinate
     * @param {number} y - World Y coordinate
     * @param {string} shapeType - Type of shape
     * @returns {object} Created shape object
     */
    create(x, y, shapeType) {
        if (this.editor.createShape) {
            return this.editor.createShape(x, y, shapeType);
        }
        console.warn('ShapeManager: createShape not available');
        return null;
    }

    // ========== SELECTION ==========
    
    /**
     * Select a shape type for placement
     * @param {string} shapeType - Shape type to select
     */
    selectType(shapeType) {
        if (this.editor.selectShapeType) {
            this.editor.selectShapeType(shapeType);
        }
    }

    /**
     * Get current selected shape type
     * @returns {string|null} Current shape type
     */
    getCurrentType() {
        return this.editor.selectedShapeType || null;
    }

    // ========== FINDING ==========
    
    /**
     * Find shape at world coordinates
     * @param {number} x - World X
     * @param {number} y - World Y
     * @returns {object|null} Shape object or null
     */
    findAt(x, y) {
        if (this.editor.findShapeAt) {
            return this.editor.findShapeAt(x, y);
        }
        return null;
    }

    /**
     * Find resize handle at position
     * @param {object} shape - Shape object
     * @param {number} x - World X
     * @param {number} y - World Y
     * @returns {string|null} Handle name or null
     */
    findResizeHandle(shape, x, y) {
        if (this.editor.findShapeResizeHandle) {
            return this.editor.findShapeResizeHandle(shape, x, y);
        }
        return null;
    }

    /**
     * Get all shapes
     * @returns {array} Array of shape objects
     */
    getAll() {
        return this.editor.objects?.filter(obj => obj.type === 'shape') || [];
    }

    /**
     * Get selected shapes
     * @returns {array} Array of selected shapes
     */
    getSelected() {
        return this.editor.selectedObjects?.filter(obj => obj.type === 'shape') || [];
    }

    // ========== MODES ==========
    
    /**
     * Enter shape placement mode
     * @param {string} shapeType - Type of shape to place
     */
    enterPlacementMode(shapeType) {
        if (this.editor.enterShapePlacementMode) {
            this.editor.enterShapePlacementMode(shapeType);
        }
    }

    /**
     * Exit shape placement mode
     */
    exitPlacementMode() {
        if (this.editor.exitShapePlacementMode) {
            this.editor.exitShapePlacementMode();
        }
    }

    // ========== DRAWING ==========
    
    /**
     * Draw a shape (called during render)
     * @param {object} shape - Shape to draw
     */
    draw(shape) {
        if (this.editor.drawShape) {
            this.editor.drawShape(shape);
        }
    }

    /**
     * Draw selection handles for a shape
     * @param {object} shape - Shape object
     */
    drawSelectionHandles(shape) {
        if (this.editor.drawShapeSelectionHandles) {
            this.editor.drawShapeSelectionHandles(shape);
        }
    }

    // ========== HANDLES ==========
    
    /**
     * Get handle positions for a shape
     * @param {object} shape - Shape object
     * @returns {object} Handle positions
     */
    getHandlePositions(shape) {
        if (this.editor.getShapeHandlePositions) {
            return this.editor.getShapeHandlePositions(shape);
        }
        return {};
    }

    // ========== STYLING ==========
    
    /**
     * Update style of selected shapes
     */
    updateSelectedStyle() {
        if (this.editor.updateSelectedShapeStyle) {
            this.editor.updateSelectedShapeStyle();
        }
    }

    // ========== TOOLBAR ==========
    
    /**
     * Setup shape toolbar (called during init)
     */
    setupToolbar() {
        if (this.editor.setupShapeToolbar) {
            this.editor.setupShapeToolbar();
        }
    }

    /**
     * Show shape selection toolbar
     * @param {object} shape - Selected shape
     */
    showToolbar(shape) {
        if (this.editor.showShapeSelectionToolbar) {
            this.editor.showShapeSelectionToolbar(shape);
        }
    }

    /**
     * Hide shape selection toolbar
     */
    hideToolbar() {
        if (this.editor.hideShapeSelectionToolbar) {
            this.editor.hideShapeSelectionToolbar();
        }
    }

    // ========== COLLISION ==========
    
    /**
     * Check if two shapes/devices would collide
     * @param {object} device1 - First device
     * @param {number} x1 - First X position
     * @param {number} y1 - First Y position
     * @param {object} device2 - Second device
     * @param {number} x2 - Second X position
     * @param {number} y2 - Second Y position
     * @returns {boolean} True if collision
     */
    checkCollision(device1, x1, y1, device2, x2, y2) {
        if (this.editor.checkShapeCollision) {
            return this.editor.checkShapeCollision(device1, x1, y1, device2, x2, y2);
        }
        return false;
    }

    // ========== UTILITY ==========
    
    /**
     * Get count of shapes
     * @returns {number} Count
     */
    getCount() {
        return this.getAll().length;
    }

    /**
     * Delete a shape
     * @param {object} shape - Shape to delete
     */
    delete(shape) {
        if (shape && this.editor.objects) {
            const idx = this.editor.objects.indexOf(shape);
            if (idx !== -1) {
                this.editor.objects.splice(idx, 1);
                this.editor.draw();
                this.editor.saveState();
            }
        }
    }

    /**
     * Get supported shape types
     * @returns {array} Array of shape type names
     */
    getShapeTypes() {
        return [...this.shapeTypes];
    }
}

// Export for module loading
window.ShapeManager = ShapeManager;
window.createShapeManager = function(editor) {
    return new ShapeManager(editor);
};

console.log('ShapeManager module loaded');
