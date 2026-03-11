// ============================================================================
// TOPOLOGY MENU MANAGER MODULE
// ============================================================================
// Handles context menus for various interactions.
// This is a wrapper module that delegates to editor methods.
//
// Menu Types:
//   - Background context menu (right-click on empty space)
//   - Object context menu (right-click on device/link/text/shape)
//   - Bulk context menu (multiple selection)
//   - Marquee context menu (after marquee selection)
//
// Usage:
//   const menuMgr = new MenuManager(editor);
//   menuMgr.showContextMenu(x, y, obj);
//   menuMgr.hideContextMenu();
// ============================================================================

class MenuManager {
    constructor(editor) {
        this.editor = editor;
    }

    // ========== CONTEXT MENU ==========
    
    /**
     * Show context menu for an object
     * @param {number} x - Screen X
     * @param {number} y - Screen Y
     * @param {object} obj - Target object (or null for background)
     */
    showContextMenu(x, y, obj = null) {
        if (obj === null) {
            this.showBackgroundMenu(x, y);
        } else if (this.editor.showContextMenu) {
            this.editor.showContextMenu(x, y, obj);
        }
    }

    /**
     * Hide context menu
     */
    hideContextMenu() {
        if (this.editor.hideContextMenu) {
            this.editor.hideContextMenu();
        }
    }

    // ========== BACKGROUND MENU ==========
    
    /**
     * Show background context menu (empty space)
     * @param {number} x - Screen X
     * @param {number} y - Screen Y
     */
    showBackgroundMenu(x, y) {
        if (this.editor.showBackgroundContextMenu) {
            this.editor.showBackgroundContextMenu(x, y);
        }
    }

    // ========== BULK MENU ==========
    
    /**
     * Show bulk context menu (multiple selection)
     * @param {number} x - Screen X
     * @param {number} y - Screen Y
     */
    showBulkMenu(x, y) {
        if (this.editor.showBulkContextMenu) {
            this.editor.showBulkContextMenu(x, y);
        }
    }

    // ========== MARQUEE MENU ==========
    
    /**
     * Show marquee context menu (after marquee selection)
     * @param {number} x - Screen X
     * @param {number} y - Screen Y
     */
    showMarqueeMenu(x, y) {
        if (this.editor.showMarqueeContextMenu) {
            this.editor.showMarqueeContextMenu(x, y);
        }
    }

    // ========== MULTI-SELECT MENU ==========
    
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

    // ========== DEVICE STYLE SUBMENU ==========
    
    /**
     * Show device style submenu
     */
    showDeviceStyleSubmenu() {
        if (this.editor.showDeviceStyleSubmenu) {
            this.editor.showDeviceStyleSubmenu();
        }
    }

    /**
     * Hide device style submenu
     */
    hideDeviceStyleSubmenu() {
        if (this.editor.hideDeviceStyleSubmenu) {
            this.editor.hideDeviceStyleSubmenu();
        }
    }

    // ========== CONTEXT MENU ACTIONS ==========
    
    /**
     * Handle copy style action
     */
    handleCopyStyle() {
        if (this.editor.handleContextCopyStyle) {
            this.editor.handleContextCopyStyle();
        }
    }

    /**
     * Handle duplicate action
     */
    handleDuplicate() {
        if (this.editor.handleContextDuplicate) {
            this.editor.handleContextDuplicate();
        }
    }

    /**
     * Handle delete action
     */
    handleDelete() {
        if (this.editor.handleContextDelete) {
            this.editor.handleContextDelete();
        }
    }

    /**
     * Handle add text action
     */
    handleAddText() {
        if (this.editor.handleContextAddText) {
            this.editor.handleContextAddText();
        }
    }

    /**
     * Handle toggle curve action
     */
    handleToggleCurve() {
        if (this.editor.handleContextToggleCurve) {
            this.editor.handleContextToggleCurve();
        }
    }

    /**
     * Handle color action
     */
    handleColor() {
        if (this.editor.handleContextColor) {
            this.editor.handleContextColor();
        }
    }

    /**
     * Handle size action
     */
    handleSize() {
        if (this.editor.handleContextSize) {
            this.editor.handleContextSize();
        }
    }

    /**
     * Handle width action
     */
    handleWidth() {
        if (this.editor.handleContextWidth) {
            this.editor.handleContextWidth();
        }
    }

    /**
     * Handle style action
     */
    handleStyle() {
        if (this.editor.handleContextStyle) {
            this.editor.handleContextStyle();
        }
    }

    /**
     * Handle label action
     */
    handleLabel() {
        if (this.editor.handleContextLabel) {
            this.editor.handleContextLabel();
        }
    }

    /**
     * Handle lock action
     */
    handleLock() {
        if (this.editor.handleContextLock) {
            this.editor.handleContextLock();
        }
    }

    /**
     * Handle unlock action
     */
    handleUnlock() {
        if (this.editor.handleContextUnlock) {
            this.editor.handleContextUnlock();
        }
    }

    /**
     * Handle toggle lock action
     */
    handleToggleLock() {
        if (this.editor.handleContextToggleLock) {
            this.editor.handleContextToggleLock();
        }
    }

    // ========== LAYER ACTIONS ==========
    
    /**
     * Handle layer to front action
     */
    handleLayerToFront() {
        if (this.editor.handleContextLayerToFront) {
            this.editor.handleContextLayerToFront();
        }
    }

    /**
     * Handle layer forward action
     */
    handleLayerForward() {
        if (this.editor.handleContextLayerForward) {
            this.editor.handleContextLayerForward();
        }
    }

    /**
     * Handle layer backward action
     */
    handleLayerBackward() {
        if (this.editor.handleContextLayerBackward) {
            this.editor.handleContextLayerBackward();
        }
    }

    /**
     * Handle layer to back action
     */
    handleLayerToBack() {
        if (this.editor.handleContextLayerToBack) {
            this.editor.handleContextLayerToBack();
        }
    }

    /**
     * Handle layer reset action
     */
    handleLayerReset() {
        if (this.editor.handleContextLayerReset) {
            this.editor.handleContextLayerReset();
        }
    }

    // ========== LINK ACTIONS ==========
    
    /**
     * Handle detach from link action
     */
    handleDetachFromLink() {
        if (this.editor.handleContextDetachFromLink) {
            this.editor.handleContextDetachFromLink();
        }
    }

    /**
     * Handle detach from device action
     */
    handleDetachFromDevice() {
        if (this.editor.handleContextDetachFromDevice) {
            this.editor.handleContextDetachFromDevice();
        }
    }

    /**
     * Handle curve mode change
     * @param {string} mode - Curve mode
     */
    handleCurveModeChange(mode) {
        if (this.editor.handleContextCurveModeChange) {
            this.editor.handleContextCurveModeChange(mode);
        }
    }

    /**
     * Handle curve magnitude action
     */
    handleCurveMagnitude() {
        if (this.editor.handleContextCurveMagnitude) {
            this.editor.handleContextCurveMagnitude();
        }
    }

    // ========== DEVICE ACTIONS ==========
    
    /**
     * Handle SSH address action
     */
    handleSSHAddress() {
        if (this.editor.handleContextSSHAddress) {
            this.editor.handleContextSSHAddress();
        }
    }

    /**
     * Handle enable LLDP action
     */
    handleEnableLldp() {
        if (this.editor.handleContextEnableLldp) {
            this.editor.handleContextEnableLldp();
        }
    }

    /**
     * Handle start discovery action
     */
    handleStartDiscovery() {
        if (this.editor.handleContextStartDiscovery) {
            this.editor.handleContextStartDiscovery();
        }
    }

    // ========== UTILITY ==========
    
    /**
     * Check if context menu is visible
     * @returns {boolean} True if visible
     */
    isContextMenuVisible() {
        const menu = document.getElementById('context-menu');
        return menu && menu.style.display !== 'none';
    }

    /**
     * Hide all menus
     */
    hideAllMenus() {
        this.hideContextMenu();
        this.hideMultiSelectMenu();
        this.hideDeviceStyleSubmenu();
    }
}

// Export for module loading
window.MenuManager = MenuManager;
window.createMenuManager = function(editor) {
    return new MenuManager(editor);
};

console.log('MenuManager module loaded');
