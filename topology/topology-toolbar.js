// ============================================================================
// TOPOLOGY TOOLBAR MODULE
// ============================================================================
// Handles toolbar setup, button event listeners, and tool mode management.
//
// Features:
//   - Tool mode buttons (select, link, text, shape)
//   - Device style buttons
//   - Link style buttons  
//   - Font selection
//   - Option toggles (numbering, collision, momentum)
//
// Usage:
//   const toolbar = new ToolbarManager(editor);
//   toolbar.setup();
// ============================================================================

class ToolbarManager {
    constructor(editor) {
        this.editor = editor;
    }

    // ========== SETUP ==========

    /**
     * Set up all toolbar event listeners
     * Called once during initialization
     */
    setup() {
        this.setupToolButtons();
        this.setupDeviceStyleButtons();
        this.setupLinkStyleButtons();
        this.setupFontButtons();
        this.setupOptionButtons();
        this.setupDnaasPanel();
        this.setupNetworkMapperPanel();
        console.log('[OK] ToolbarManager setup complete');
    }

    /**
     * Helper to safely add event listener
     * @param {string} id - Element ID
     * @param {string} event - Event type
     * @param {Function} handler - Event handler
     */
    safeAddListener(id, event, handler) {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener(event, handler);
        } else {
            console.warn(`Element ${id} not found, skipping event listener`);
        }
    }

    // ========== TOOL BUTTONS ==========

    setupToolButtons() {
        this.safeAddListener('btn-base', 'click', () => this.editor.setMode('base'));
        this.safeAddListener('btn-select', 'click', () => this.editor.toggleTool('select'));
        this.safeAddListener('btn-link', 'click', () => this.editor.toggleTool('link'));
        this.safeAddListener('btn-link-curve', 'click', () => this.editor.toggleLinkCurveMode());
        this.safeAddListener('btn-curve-auto', 'click', () => this.editor.setGlobalCurveMode('auto'));
        this.safeAddListener('btn-curve-manual', 'click', () => this.editor.setGlobalCurveMode('manual'));
        this.safeAddListener('btn-link-continuous', 'click', () => this.editor.toggleLinkContinuousMode());
        this.safeAddListener('btn-link-sticky', 'click', () => this.editor.toggleLinkStickyMode());
        this.safeAddListener('btn-link-ul', 'click', () => this.editor.toggleLinkULMode());
        this.safeAddListener('btn-device-numbering', 'click', () => this.editor.toggleDeviceNumbering());
        this.safeAddListener('btn-device-collision', 'click', () => this.editor.toggleDeviceCollision());
    }

    // ========== DEVICE STYLE BUTTONS ==========

    setupDeviceStyleButtons() {
        const deviceStylesBox = document.getElementById('device-styles-box');
        if (deviceStylesBox) {
            deviceStylesBox.addEventListener('click', (e) => {
                let target = e.target;
                while (target && target !== deviceStylesBox) {
                    if (target.classList && target.classList.contains('style-btn')) {
                        const btnId = target.id;
                        const styleMatch = btnId.match(/btn-style-(\w+)/);
                        if (styleMatch) {
                            e.stopPropagation();
                            e.preventDefault();
                            const style = styleMatch[1];
                            this.editor.setDeviceStyle(style);
                            return;
                        }
                    }
                    target = target.parentElement;
                }
            });
            console.log('[OK] Device style buttons event delegation set up');
        }
    }

    // ========== LINK STYLE BUTTONS ==========

    setupLinkStyleButtons() {
        ['solid', 'dashed', 'arrow'].forEach(baseStyle => {
            const btn = document.getElementById(`btn-link-style-${baseStyle}`);
            if (btn) {
                btn.addEventListener('click', (e) => {
                    const dot = e.target.closest('.style-dot');
                    if (dot) {
                        const dotIndex = parseInt(dot.dataset.index);
                        this.editor.setLinkStyleByIndex(baseStyle, dotIndex);
                    } else {
                        this.editor.cycleLinkStyle(baseStyle);
                    }
                });
            }
        });
    }

    // ========== FONT BUTTONS ==========

    setupFontButtons() {
        const deviceFontGrid = document.getElementById('device-font-grid');
        if (deviceFontGrid) {
            deviceFontGrid.querySelectorAll('.font-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const fontFamily = btn.dataset.deviceFont;
                    if (!fontFamily) return;
                    
                    // Update active state
                    this.updateFontButtonStates(deviceFontGrid, fontFamily);
                    
                    // Set default and apply
                    this.editor.defaultDeviceFontFamily = fontFamily;
                    localStorage.setItem('defaultDeviceFontFamily', fontFamily);
                    this.applyFontToSelectedDevices(fontFamily);
                });
            });
            
            // Restore saved preference
            this.restoreFontButtonState(deviceFontGrid);
            console.log('[OK] Device font buttons set up');
        }
    }

    updateFontButtonStates(grid, activeFont) {
        grid.querySelectorAll('.font-btn').forEach(btn => {
            const isActive = btn.dataset.deviceFont === activeFont;
            btn.classList.toggle('active', isActive);
            btn.style.background = isActive ? 'rgba(52, 152, 219, 0.3)' : 'rgba(255,255,255,0.05)';
            btn.style.borderColor = isActive ? '#3498db' : 'transparent';
            btn.style.color = isActive ? '#fff' : '#aaa';
        });
    }

    restoreFontButtonState(grid) {
        const savedFont = this.editor.defaultDeviceFontFamily;
        this.updateFontButtonStates(grid, savedFont);
    }

    applyFontToSelectedDevices(fontFamily) {
        let appliedCount = 0;
        
        if (this.editor.selectedObjects.length > 0) {
            this.editor.selectedObjects.forEach(obj => {
                if (obj.type === 'device') {
                    obj.fontFamily = fontFamily;
                    appliedCount++;
                }
            });
        }
        
        if (this.editor.selectedObject && this.editor.selectedObject.type === 'device') {
            this.editor.selectedObject.fontFamily = fontFamily;
            if (appliedCount === 0) appliedCount = 1;
        }
        
        this.editor.draw();
        this.editor.scheduleAutoSave();
    }

    // ========== OPTION BUTTONS ==========

    setupOptionButtons() {
        const momentumBtn = document.getElementById('btn-momentum');
        if (momentumBtn) {
            momentumBtn.addEventListener('click', () => this.editor.toggleMomentum());
        }
    }

    // ========== DNAAS PANEL ==========

    setupDnaasPanel() {
        // Delegate to DnaasManager if available
        if (this.editor.dnaas && this.editor.dnaas.setupPanel) {
            this.editor.dnaas.setupPanel();
        }
    }

    // ========== NETWORK MAPPER PANEL ==========

    setupNetworkMapperPanel() {
        if (this.editor.networkMapper && this.editor.networkMapper.setupPanel) {
            this.editor.networkMapper.setupPanel();
        }
    }

    // ========== TOOL STATE ==========

    /**
     * Update toolbar button states to reflect current mode
     */
    updateButtonStates() {
        const currentTool = this.editor.currentTool;
        
        // Update tool button active states
        ['select', 'link', 'text', 'shape'].forEach(tool => {
            const btn = document.getElementById(`btn-${tool}`);
            if (btn) {
                btn.classList.toggle('active', currentTool === tool);
            }
        });
    }
}

// Factory function
window.createToolbarManager = function(editor) {
    return new ToolbarManager(editor);
};

// Export for module use
window.ToolbarManager = ToolbarManager;
