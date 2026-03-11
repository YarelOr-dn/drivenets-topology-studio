// ============================================================================
// TOPOLOGY UI MANAGER MODULE
// ============================================================================
// Handles selection toolbars, panels, and UI state management.
// This is a wrapper module that delegates to editor methods.
//
// UI Components:
//   - Selection toolbars (device, link, text, shape)
//   - Properties panel
//   - Color palettes
//   - Style options
//
// Usage:
//   const uiMgr = new UIManager(editor);
//   uiMgr.showToolbar('device', deviceObj);
//   uiMgr.hideAllToolbars();
// ============================================================================

class UIManager {
    constructor(editor) {
        this.editor = editor;
    }

    // ========== DEVICE TOOLBAR ==========
    
    /**
     * Show device selection toolbar
     * @param {object} device - Selected device
     */
    showDeviceToolbar(device) {
        if (this.editor.showDeviceSelectionToolbar) {
            this.editor.showDeviceSelectionToolbar(device);
        }
    }

    /**
     * Hide device selection toolbar
     */
    hideDeviceToolbar() {
        if (this.editor.hideDeviceSelectionToolbar) {
            this.editor.hideDeviceSelectionToolbar();
        }
    }

    /**
     * Show device style palette
     * @param {object} device - Device object
     */
    showDeviceStylePalette(device) {
        if (this.editor.showDeviceStylePalette) {
            this.editor.showDeviceStylePalette(device);
        }
    }

    /**
     * Show device label style menu
     * @param {object} device - Device object
     * @param {HTMLElement} toolbar - Toolbar element
     */
    showDeviceLabelStyleMenu(device, toolbar) {
        if (this.editor.showDeviceLabelStyleMenu) {
            this.editor.showDeviceLabelStyleMenu(device, toolbar);
        }
    }

    // ========== LINK TOOLBAR ==========
    
    /**
     * Show link selection toolbar
     * @param {object} link - Selected link
     * @param {object} clickPos - Click position
     */
    showLinkToolbar(link, clickPos = null) {
        if (this.editor.showLinkSelectionToolbar) {
            this.editor.showLinkSelectionToolbar(link, clickPos);
        }
    }

    /**
     * Hide link selection toolbar
     */
    hideLinkToolbar() {
        if (this.editor.hideLinkSelectionToolbar) {
            this.editor.hideLinkSelectionToolbar();
        }
    }

    /**
     * Show link width slider
     * @param {object} link - Link object
     */
    showLinkWidthSlider(link) {
        if (this.editor.showLinkWidthSlider) {
            this.editor.showLinkWidthSlider(link);
        }
    }

    /**
     * Show link style options
     * @param {object} link - Link object
     */
    showLinkStyleOptions(link) {
        if (this.editor.showLinkStyleOptions) {
            this.editor.showLinkStyleOptions(link);
        }
    }

    /**
     * Show link curve options
     * @param {object} link - Link object
     */
    showLinkCurveOptions(link) {
        if (this.editor.showLinkCurveOptions) {
            this.editor.showLinkCurveOptions(link);
        }
    }

    // ========== TEXT TOOLBAR ==========
    
    /**
     * Show text selection toolbar
     * @param {object} textObj - Selected text object
     */
    showTextToolbar(textObj) {
        if (this.editor.showTextSelectionToolbar) {
            this.editor.showTextSelectionToolbar(textObj);
        }
    }

    /**
     * Hide text selection toolbar
     */
    hideTextToolbar() {
        if (this.editor.hideTextSelectionToolbar) {
            this.editor.hideTextSelectionToolbar();
        }
    }

    /**
     * Update text toolbar position
     */
    updateTextToolbarPosition() {
        if (this.editor.updateTextSelectionToolbarPosition) {
            this.editor.updateTextSelectionToolbarPosition();
        }
    }

    /**
     * Show text color palette
     * @param {object} textObj - Text object
     */
    showTextColorPalette(textObj) {
        if (this.editor.showTextColorPalette) {
            this.editor.showTextColorPalette(textObj);
        }
    }

    /**
     * Show text font selector
     * @param {object} textObj - Text object
     */
    showTextFontSelector(textObj) {
        if (this.editor.showTextFontSelector) {
            this.editor.showTextFontSelector(textObj);
        }
    }

    /**
     * Show text background color palette
     * @param {object} textObj - Text object
     */
    showTextBgColorPalette(textObj) {
        if (this.editor.showTextBgColorPalette) {
            this.editor.showTextBgColorPalette(textObj);
        }
    }

    // ========== SHAPE TOOLBAR ==========
    
    /**
     * Show shape selection toolbar
     * @param {object} shape - Selected shape
     */
    showShapeToolbar(shape) {
        if (this.editor.showShapeSelectionToolbar) {
            this.editor.showShapeSelectionToolbar(shape);
        }
    }

    /**
     * Hide shape selection toolbar
     */
    hideShapeToolbar() {
        if (this.editor.hideShapeSelectionToolbar) {
            this.editor.hideShapeSelectionToolbar();
        }
    }

    // ========== GENERIC TOOLBAR ==========
    
    /**
     * Show toolbar for any object type
     * @param {string} type - Object type ('device', 'link', 'text', 'shape')
     * @param {object} obj - The object
     * @param {object} options - Additional options
     */
    showToolbar(type, obj, options = {}) {
        switch (type) {
            case 'device':
                this.showDeviceToolbar(obj);
                break;
            case 'link':
                this.showLinkToolbar(obj, options.clickPos);
                break;
            case 'text':
                this.showTextToolbar(obj);
                break;
            case 'shape':
                this.showShapeToolbar(obj);
                break;
            default:
                console.warn(`UIManager: Unknown toolbar type: ${type}`);
        }
    }

    /**
     * Hide toolbar for any object type
     * @param {string} type - Object type
     */
    hideToolbar(type) {
        switch (type) {
            case 'device':
                this.hideDeviceToolbar();
                break;
            case 'link':
                this.hideLinkToolbar();
                break;
            case 'text':
                this.hideTextToolbar();
                break;
            case 'shape':
                this.hideShapeToolbar();
                break;
            default:
                console.warn(`UIManager: Unknown toolbar type: ${type}`);
        }
    }

    /**
     * Hide all selection toolbars
     */
    hideAllToolbars() {
        if (this.editor.hideAllSelectionToolbars) {
            this.editor.hideAllSelectionToolbars();
        } else {
            // Fallback: hide each individually
            this.hideDeviceToolbar();
            this.hideLinkToolbar();
            this.hideTextToolbar();
            this.hideShapeToolbar();
        }
    }

    // ========== PROPERTIES PANEL ==========
    
    /**
     * Update properties panel
     */
    updatePropertiesPanel() {
        if (this.editor.updatePropertiesPanel) {
            this.editor.updatePropertiesPanel();
        }
    }

    // ========== EDITORS ==========
    
    /**
     * Show device editor
     * @param {object} device - Device to edit
     */
    showDeviceEditor(device) {
        if (this.editor.showDeviceEditor) {
            this.editor.showDeviceEditor(device);
        }
    }

    /**
     * Hide device editor
     */
    hideDeviceEditor() {
        if (this.editor.hideDeviceEditor) {
            this.editor.hideDeviceEditor();
        }
    }

    /**
     * Show link editor
     * @param {object} link - Link to edit
     */
    showLinkEditor(link) {
        if (this.editor.showLinkEditor) {
            this.editor.showLinkEditor(link);
        }
    }

    /**
     * Hide link editor
     */
    hideLinkEditor() {
        if (this.editor.hideLinkEditor) {
            this.editor.hideLinkEditor();
        }
    }

    /**
     * Show text editor
     * @param {object} textObj - Text to edit
     */
    showTextEditor(textObj) {
        if (this.editor.showTextEditor) {
            this.editor.showTextEditor(textObj);
        }
    }

    /**
     * Hide text editor
     */
    hideTextEditor() {
        if (this.editor.hideTextEditor) {
            this.editor.hideTextEditor();
        }
    }

    // ========== INLINE EDITORS ==========
    
    /**
     * Show inline text editor
     * @param {object} textObj - Text object
     * @param {Event} event - Mouse event
     */
    showInlineTextEditor(textObj, event) {
        if (this.editor.showInlineTextEditor) {
            this.editor.showInlineTextEditor(textObj, event);
        }
    }

    /**
     * Hide inline text editor
     */
    hideInlineTextEditor() {
        if (this.editor.hideInlineTextEditor) {
            this.editor.hideInlineTextEditor();
        }
    }

    /**
     * Show inline device rename
     * @param {object} device - Device to rename
     */
    showInlineDeviceRename(device) {
        if (this.editor.showInlineDeviceRename) {
            this.editor.showInlineDeviceRename(device);
        }
    }

    /**
     * Hide inline device rename
     */
    hideInlineDeviceRename() {
        if (this.editor.hideInlineDeviceRename) {
            this.editor.hideInlineDeviceRename();
        }
    }

    // ========== LINK DETAILS ==========
    
    /**
     * Show link details panel
     * @param {object} link - Link object
     */
    showLinkDetails(link) {
        if (this.editor.showLinkDetails) {
            this.editor.showLinkDetails(link);
        }
    }

    /**
     * Hide link details panel
     */
    hideLinkDetails() {
        if (this.editor.hideLinkDetails) {
            this.editor.hideLinkDetails();
        }
    }

    // ========== COLOR PALETTE ==========
    
    /**
     * Show color palette popup from toolbar
     * @param {object} obj - Target object
     * @param {string} objType - Object type
     * @param {HTMLElement} toolbar - Toolbar element
     */
    showColorPaletteFromToolbar(obj, objType, toolbar) {
        if (this.editor.showColorPalettePopupFromToolbar) {
            this.editor.showColorPalettePopupFromToolbar(obj, objType, toolbar);
        }
    }

    // ========== INTERFACE MENU ==========
    
    /**
     * Show link interface menu
     * @param {object} link - Link object
     */
    showLinkInterfaceMenu(link) {
        if (this.editor.showLinkInterfaceMenu) {
            this.editor.showLinkInterfaceMenu(link);
        }
    }

    /**
     * Show adjacent text menu for link
     * @param {object} link - Link object
     */
    showAdjacentTextMenu(link) {
        if (this.editor.showAdjacentTextMenu) {
            this.editor.showAdjacentTextMenu(link);
        }
    }

    // ========== LLDP MENU ==========
    
    /**
     * Show LLDP button menu
     * @param {object} device - Device object
     * @param {number} x - Screen X
     * @param {number} y - Screen Y
     */
    showLldpButtonMenu(device, x, y) {
        if (this.editor.showLldpButtonMenu) {
            this.editor.showLldpButtonMenu(device, x, y);
        }
    }

    // ========== MULTI-SELECT ==========
    
    /**
     * Show multi-select context menu
     * @param {number} screenX - Screen X
     * @param {number} screenY - Screen Y
     */
    showMultiSelectMenu(screenX, screenY) {
        if (this.editor.showMultiSelectContextMenu) {
            this.editor.showMultiSelectContextMenu(screenX, screenY);
        }
    }

    /**
     * Hide multi-select context menu
     */
    hideMultiSelectMenu() {
        if (this.editor.hideMultiSelectContextMenu) {
            this.editor.hideMultiSelectContextMenu();
        }
    }

    // ========== UTILITY ==========
    
    /**
     * Get currently visible toolbar type
     * @returns {string|null} Toolbar type or null
     */
    getActiveToolbarType() {
        // Check each toolbar's visibility
        const toolbars = [
            { type: 'device', el: document.getElementById('device-selection-toolbar') },
            { type: 'link', el: document.getElementById('link-selection-toolbar') },
            { type: 'text', el: document.getElementById('text-selection-toolbar') },
            { type: 'shape', el: document.getElementById('shape-selection-toolbar') },
        ];
        
        for (const tb of toolbars) {
            if (tb.el && tb.el.style.display !== 'none') {
                return tb.type;
            }
        }
        return null;
    }

    /**
     * Check if any toolbar is visible
     * @returns {boolean} True if any toolbar visible
     */
    hasActiveToolbar() {
        return this.getActiveToolbarType() !== null;
    }
}

// Export for module loading
window.UIManager = UIManager;
window.createUIManager = function(editor) {
    return new UIManager(editor);
};

console.log('UIManager module loaded');
