// ============================================================================
// TOPOLOGY DEVICE MANAGER MODULE
// ============================================================================
// Handles device creation, selection, styling, collision detection, and properties.
// This is a wrapper module that delegates to editor methods.
//
// Usage:
//   const deviceMgr = new DeviceManager(editor);
//   deviceMgr.add('SA-40C');
//   deviceMgr.addAtPosition('SA-40C', 100, 200);
// ============================================================================

class DeviceManager {
    constructor(editor) {
        this.editor = editor;
    }

    // ========================================================================
    // ACCESSORS
    // ========================================================================
    
    get objects() { return this.editor.objects || []; }
    get deviceCounters() { return this.editor.deviceCounters || { router: 0, switch: 0 }; }
    get deviceNumbering() { return this.editor.deviceNumbering !== false; } // Default true

    // ========== CREATION ==========
    
    /**
     * Add a device (prompts for placement)
     * @param {string} type - Device type (e.g., 'SA-40C')
     * @returns {object|null} Created device or null
     */
    add(type) {
        if (this.editor.addDevice) {
            return this.editor.addDevice(type);
        }
        return null;
    }

    /**
     * Add a device at specific position
     * Contains the actual implementation for device creation
     * @param {string} type - Device type
     * @param {number} x - World X coordinate
     * @param {number} y - World Y coordinate
     * @returns {object|null} Created device or null
     */
    addAtPosition(type, x, y) {
        const editor = this.editor;
        
        // Snap position to grid
        const clickedWorld = { x, y };
        const clickedGrid = editor.worldToGrid(clickedWorld);
        const snappedGrid = {
            x: Math.round(clickedGrid.x),
            y: Math.round(clickedGrid.y)
        };
        const snappedWorld = editor.gridToWorld(snappedGrid);
        
        // Validate
        if (!isFinite(snappedWorld.x) || !isFinite(snappedWorld.y)) {
            snappedWorld.x = x;
            snappedWorld.y = y;
        }
        
        const label = this.getNextLabel(type);
        
        // Validate uniqueness
        if (editor.deviceNumbering && !this.isNameUnique(label)) {
            alert(`Device name "${label}" already exists.`);
            return null;
        }

        // Default colors
        const colorPickerEl = document.getElementById('color-picker');
        const defaultColor = type === 'router' ? '#5B9BD5' : (colorPickerEl ? colorPickerEl.value : '#4CAF50');
        
        const device = {
            id: `device_${editor.deviceIdCounter++}`,
            type: 'device',
            deviceType: type,
            x: snappedWorld.x,
            y: snappedWorld.y,
            radius: 50,
            rotation: 0,
            color: defaultColor,
            label: label,
            locked: false,
            visualStyle: editor.defaultDeviceStyle || 'circle'
        };
        
        editor.saveState();
        editor.objects.push(device);
        editor.selectedObject = device;
        editor.selectedObjects = [device];
        editor.updateDeviceProperties();
        editor.draw();
        editor.lastClickPos = null;
        
        return device;
    }

    // ========== FINDING ==========
    
    /**
     * Find device at world coordinates
     * @param {number} x - World X
     * @param {number} y - World Y
     * @returns {object|null} Device object or null
     */
    findAt(x, y) {
        if (this.editor.findDeviceAt) {
            return this.editor.findDeviceAt(x, y);
        }
        return null;
    }

    /**
     * Get all devices
     * @returns {array} Array of device objects
     */
    getAll() {
        return this.editor.objects?.filter(obj => obj.type === 'device') || [];
    }

    /**
     * Get selected devices
     * @returns {array} Array of selected devices
     */
    getSelected() {
        return this.editor.selectedObjects?.filter(obj => obj.type === 'device') || [];
    }

    /**
     * Get device by ID
     * @param {string} id - Device ID
     * @returns {object|null} Device or null
     */
    getById(id) {
        return this.getAll().find(d => d.id === id) || null;
    }

    /**
     * Get device by label/name
     * @param {string} label - Device label
     * @returns {object|null} Device or null
     */
    getByLabel(label) {
        return this.getAll().find(d => d.label === label || d.name === label) || null;
    }

    // ========== NAMING (MIGRATED) ==========
    
    /**
     * Get next available device label
     * MIGRATED from topology.js getNextDeviceLabel()
     * @param {string} deviceType - 'router' or 'switch'
     * @returns {string} Next label
     */
    getNextLabel(deviceType) {
        // If numbering is disabled, always return base name
        if (!this.deviceNumbering) {
            return deviceType === 'router' ? 'NCP' : 'S';
        }
        
        // Numbering enabled - increment counter
        const counters = this.editor.deviceCounters || { router: 0, switch: 0 };
        counters[deviceType] = (counters[deviceType] || 0) + 1;
        this.editor.deviceCounters = counters;
        
        const count = counters[deviceType];
        
        if (count === 1) {
            return deviceType === 'router' ? 'NCP' : 'S';
        } else {
            return deviceType === 'router' ? `NCP-${count}` : `S${count}`;
        }
    }

    /**
     * Check if device name is unique
     * MIGRATED from topology.js isDeviceNameUnique()
     * @param {string} name - Name to check
     * @returns {boolean} True if unique
     */
    isNameUnique(name) {
        const existing = this.objects.find(obj => 
            obj.type === 'device' && obj.label === name
        );
        return !existing;
    }
    
    /**
     * Update device counters based on existing devices
     * MIGRATED from topology.js updateDeviceCounters()
     */
    updateCounters() {
        const counters = { router: 0, switch: 0 };
        
        this.objects.forEach(obj => {
            if (obj.type === 'device') {
                const label = obj.label || '';
                
                if (obj.deviceType === 'router') {
                    if (label === 'NCP' || label === 'R') {
                        counters.router = Math.max(counters.router, 1);
                    } else {
                        const matchNCP = label.match(/^NCP-(\d+)$/);
                        const matchR = label.match(/^R(\d+)$/);
                        if (matchNCP) {
                            counters.router = Math.max(counters.router, parseInt(matchNCP[1]));
                        } else if (matchR) {
                            counters.router = Math.max(counters.router, parseInt(matchR[1]));
                        }
                    }
                } else if (obj.deviceType === 'switch') {
                    if (label === 'S') {
                        counters.switch = Math.max(counters.switch, 1);
                    } else {
                        const match = label.match(/^S(\d+)$/);
                        if (match) {
                            counters.switch = Math.max(counters.switch, parseInt(match[1]));
                        }
                    }
                }
            }
        });
        
        this.editor.deviceCounters = counters;
        return counters;
    }

    /**
     * Update device label
     * @param {string} label - New label
     */
    updateLabel(label) {
        if (this.editor.updateDeviceLabel) {
            this.editor.updateDeviceLabel(label);
        }
    }

    /**
     * Apply device label to selection
     */
    applyLabel() {
        if (this.editor.applyDeviceLabel) {
            this.editor.applyDeviceLabel();
        }
    }

    // ========== MODES ==========
    
    /**
     * Set device placement mode
     * @param {string} deviceType - Type of device to place
     */
    setPlacementMode(deviceType) {
        if (this.editor.setDevicePlacementMode) {
            this.editor.setDevicePlacementMode(deviceType);
        }
    }

    /**
     * Toggle device placement mode
     * @param {string} deviceType - Device type
     */
    togglePlacementMode(deviceType) {
        if (this.editor.toggleDevicePlacementMode) {
            this.editor.toggleDevicePlacementMode(deviceType);
        }
    }

    // ========== STYLING ==========
    
    /**
     * Set device visual style
     * @param {string} style - Style name
     */
    setStyle(style) {
        if (this.editor.setDeviceStyle) {
            this.editor.setDeviceStyle(style);
        }
    }

    /**
     * Set device visual style (alternative)
     * @param {string} style - Style name
     */
    setVisualStyle(style) {
        if (this.editor.setDeviceVisualStyle) {
            this.editor.setDeviceVisualStyle(style);
        }
    }

    /**
     * Update device properties
     */
    updateProperties() {
        if (this.editor.updateDeviceProperties) {
            this.editor.updateDeviceProperties();
        }
    }

    /**
     * Update device radius
     * @param {number} radius - New radius
     */
    updateRadius(radius) {
        if (this.editor.updateDeviceRadius) {
            this.editor.updateDeviceRadius(radius);
        }
    }

    /**
     * Apply radius to selection
     */
    applyRadius() {
        if (this.editor.applyDeviceRadius) {
            this.editor.applyDeviceRadius();
        }
    }

    // ========== COLLISION ==========
    
    /**
     * Check device collision
     * @param {object} movingDevice - Device being moved
     * @param {number} proposedX - Proposed X position
     * @param {number} proposedY - Proposed Y position
     * @returns {object|null} Collision result
     */
    checkCollision(movingDevice, proposedX, proposedY) {
        if (this.editor.checkDeviceCollision) {
            return this.editor.checkDeviceCollision(movingDevice, proposedX, proposedY);
        }
        return null;
    }

    /**
     * Get device collision radius
     * @param {object} device - Device object
     * @returns {number} Collision radius
     */
    getCollisionRadius(device) {
        if (this.editor.getDeviceCollisionRadius) {
            return this.editor.getDeviceCollisionRadius(device);
        }
        return device.radius || 30;
    }

    /**
     * Get device visual bounds
     * @param {object} device - Device object
     * @returns {object} Bounds {x, y, width, height}
     */
    getVisualBounds(device) {
        if (this.editor.getDeviceVisualBounds) {
            return this.editor.getDeviceVisualBounds(device);
        }
        return { x: device.x, y: device.y, width: 60, height: 60 };
    }

    /**
     * Toggle collision detection
     */
    toggleCollision() {
        if (this.editor.toggleDeviceCollision) {
            this.editor.toggleDeviceCollision();
        }
    }

    // ========== TOOLBAR ==========
    
    /**
     * Show device selection toolbar
     * @param {object} device - Selected device
     */
    showToolbar(device) {
        if (this.editor.showDeviceSelectionToolbar) {
            this.editor.showDeviceSelectionToolbar(device);
        }
    }

    /**
     * Hide device selection toolbar
     */
    hideToolbar() {
        if (this.editor.hideDeviceSelectionToolbar) {
            this.editor.hideDeviceSelectionToolbar();
        }
    }

    /**
     * Show device style palette
     * @param {object} device - Device object
     */
    showStylePalette(device) {
        if (this.editor.showDeviceStylePalette) {
            this.editor.showDeviceStylePalette(device);
        }
    }

    // ========== EDITOR ==========
    
    /**
     * Show device editor panel
     * @param {object} device - Device to edit
     */
    showEditor(device) {
        if (this.editor.showDeviceEditor) {
            this.editor.showDeviceEditor(device);
        }
    }

    /**
     * Hide device editor panel
     */
    hideEditor() {
        if (this.editor.hideDeviceEditor) {
            this.editor.hideDeviceEditor();
        }
    }

    /**
     * Update device editor property
     * @param {string} property - Property name
     * @param {*} value - Property value
     */
    updateEditorProperty(property, value) {
        if (this.editor.updateDeviceEditorProperty) {
            this.editor.updateDeviceEditorProperty(property, value);
        }
    }

    // ========== INLINE RENAME ==========
    
    /**
     * Show inline device rename
     * @param {object} device - Device to rename
     */
    showInlineRename(device) {
        if (this.editor.showInlineDeviceRename) {
            this.editor.showInlineDeviceRename(device);
        }
    }

    /**
     * Hide inline device rename
     */
    hideInlineRename() {
        if (this.editor.hideInlineDeviceRename) {
            this.editor.hideInlineDeviceRename();
        }
    }

    // ========== DISPLAY OPTIONS ==========
    
    /**
     * Toggle device numbering display
     */
    toggleNumbering() {
        if (this.editor.toggleDeviceNumbering) {
            this.editor.toggleDeviceNumbering();
        }
    }

    /**
     * Toggle movable devices mode
     */
    toggleMovable() {
        if (this.editor.toggleMovableDevices) {
            this.editor.toggleMovableDevices();
        }
    }

    // ========== NAVIGATION ==========
    
    /**
     * Center view on all devices
     */
    centerOnAll() {
        if (this.editor.centerOnDevices) {
            this.editor.centerOnDevices();
        }
    }

    // ========== CONNECTIONS ==========
    
    /**
     * Get all devices connected to a link
     * @param {object} link - Link object
     * @returns {array} Connected devices
     */
    getConnectedToLink(link) {
        if (this.editor.getAllConnectedDevices) {
            return this.editor.getAllConnectedDevices(link);
        }
        return [];
    }

    /**
     * Get BUL endpoint devices
     * @param {object} link - Link object
     * @returns {array} Endpoint devices
     */
    getBULEndpoints(link) {
        if (this.editor.getBULEndpointDevices) {
            return this.editor.getBULEndpointDevices(link);
        }
        return [];
    }

    // ========== MODEL DETECTION ==========
    
    /**
     * Detect model from device name
     * @param {string} deviceName - Device name
     * @returns {string|null} Detected model
     */
    detectModel(deviceName) {
        if (this.editor.detectModelFromDeviceName) {
            return this.editor.detectModelFromDeviceName(deviceName);
        }
        return null;
    }

    // ========== COUNTERS ==========
    
    /**
     * Update device counters
     */
    updateCounters() {
        if (this.editor.updateDeviceCounters) {
            this.editor.updateDeviceCounters();
        }
    }

    // ========== UTILITY ==========
    
    /**
     * Get count of devices
     * @returns {number} Count
     */
    getCount() {
        return this.getAll().length;
    }

    /**
     * Delete a device
     * @param {object} device - Device to delete
     */
    delete(device) {
        if (device && this.editor.objects) {
            const idx = this.editor.objects.indexOf(device);
            if (idx !== -1) {
                this.editor.objects.splice(idx, 1);
                this.editor.draw();
                this.editor.saveState();
            }
        }
    }

    /**
     * Get device categories from platform data
     * @returns {array} Category names
     */
    getCategories() {
        if (this.editor.platformData) {
            return this.editor.platformData.getCategories();
        }
        return ['SA', 'CL', 'NC-AI', 'DNAAS'];
    }

    /**
     * Get platforms for a category
     * @param {string} category - Category name
     * @returns {array} Platform objects
     */
    getPlatforms(category) {
        if (this.editor.platformData) {
            return this.editor.platformData.getPlatformsByCategory(category);
        }
        return [];
    }
}

// Export for module loading
window.DeviceManager = DeviceManager;
window.createDeviceManager = function(editor) {
    return new DeviceManager(editor);
};

console.log('[topology-devices.js] DeviceManager with naming functions loaded');
