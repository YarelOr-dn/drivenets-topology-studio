/**
 * topology-context-menus.js - Context Menu Module
 *
 * Extracted from topology.js for modular architecture.
 * Contains context menu display and positioning functions.
 *
 * @version 1.0.0
 * @date 2026-02-04
 */

'use strict';

window.ContextMenus = {

    // =========================================================================
    // MENU POSITIONING
    // =========================================================================

    /**
     * Adjust menu position to keep it within viewport bounds
     * @param {number} x - Requested X position
     * @param {number} y - Requested Y position
     * @param {HTMLElement} menu - Menu element
     * @returns {Object} Adjusted position {x, y}
     */
    adjustMenuPosition(x, y, menu) {
        const menuRect = menu.getBoundingClientRect();
        const menuWidth = menuRect.width || 200;
        const menuHeight = menuRect.height || 300;
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        let adjustedX = x;
        let adjustedY = y;
        
        // Check right edge
        if (x + menuWidth > viewportWidth - 10) {
            adjustedX = viewportWidth - menuWidth - 10;
        }
        // Check left edge
        if (adjustedX < 10) {
            adjustedX = 10;
        }
        // Check bottom edge
        if (y + menuHeight > viewportHeight - 10) {
            adjustedY = viewportHeight - menuHeight - 10;
        }
        // Check top edge
        if (adjustedY < 10) {
            adjustedY = 10;
        }
        
        return { x: adjustedX, y: adjustedY };
    },

    // =========================================================================
    // BACKGROUND CONTEXT MENU
    // =========================================================================

    /**
     * Show context menu for background (no object selected)
     * @param {Object} editor - TopologyEditor instance
     * @param {number} x - Screen X position
     * @param {number} y - Screen Y position
     */
    showBackgroundContextMenu(editor, x, y) {
        const menu = document.getElementById('context-menu');
        if (!menu) return;
        
        menu.style.display = 'block';
        
        // Adjust position to keep menu within viewport
        const adjusted = this.adjustMenuPosition(x, y, menu);
        menu.style.left = adjusted.x + 'px';
        menu.style.top = adjusted.y + 'px';
        editor.contextMenuVisible = true;
        
        // Hide all standard menu items
        this._safeSetDisplay('ctx-duplicate', 'none');
        this._safeSetDisplay('ctx-add-text', 'none');
        this._safeSetDisplay('ctx-curve', 'none');
        this._safeSetDisplay('ctx-change-color', 'none');
        this._safeSetDisplay('ctx-change-label', 'none');
        this._safeSetDisplay('ctx-lock', 'none');
        this._safeSetDisplay('ctx-unlock', 'none');
        this._safeSetDisplay('ctx-delete', 'none');
        
        // Create temporary menu item for base mode
        const existingBaseModeItem = document.getElementById('ctx-base-mode');
        if (existingBaseModeItem) {
            existingBaseModeItem.style.display = 'block';
        } else {
            const baseModeItem = document.createElement('div');
            baseModeItem.id = 'ctx-base-mode';
            baseModeItem.className = 'context-menu-item';
            baseModeItem.textContent = '← Return to Base Mode';
            baseModeItem.addEventListener('click', () => {
                editor.setMode('base');
                editor.hideContextMenu();
            });
            menu.insertBefore(baseModeItem, menu.firstChild);
        }
    },

    // =========================================================================
    // BULK CONTEXT MENU
    // =========================================================================

    /**
     * Show context menu for multiple selected objects
     * @param {Object} editor - TopologyEditor instance
     * @param {number} x - Screen X position
     * @param {number} y - Screen Y position
     */
    showBulkContextMenu(editor, x, y) {
        const menu = document.getElementById('context-menu');
        menu.style.display = 'block';
        
        // Adjust position to keep menu within viewport
        const adjusted = this.adjustMenuPosition(x, y, menu);
        menu.style.left = adjusted.x + 'px';
        menu.style.top = adjusted.y + 'px';
        editor.contextMenuVisible = true;
        
        // Hide background-specific items
        this._safeSetDisplay('ctx-base-mode', 'none');
        
        // Check what types of objects are selected
        const hasDevices = editor.selectedObjects.some(obj => obj.type === 'device');
        const hasLinks = editor.selectedObjects.some(obj => obj.type === 'link' || obj.type === 'unbound');
        const hasText = editor.selectedObjects.some(obj => obj.type === 'text');
        const hasLockable = editor.selectedObjects.some(obj => obj.type === 'device' || obj.type === 'text');
        
        // Show appropriate bulk operations
        this._safeSetDisplay('ctx-duplicate', 'none');
        this._safeSetDisplay('ctx-add-text', 'none');
        this._safeSetDisplay('ctx-change-color', (hasDevices || hasText) ? 'block' : 'none');
        this._safeSetDisplay('ctx-change-label', 'none');
        
        // Show curve submenu for bulk link operations
        const curveSubmenuTrigger = document.getElementById('ctx-curve');
        if (curveSubmenuTrigger) {
            if (hasLinks) {
                curveSubmenuTrigger.style.display = 'block';
                const firstLink = editor.selectedObjects.find(obj => obj.type === 'link' || obj.type === 'unbound');
                editor._curveSubmenuLink = firstLink;
            } else {
                curveSubmenuTrigger.style.display = 'none';
            }
        }
        
        // Show lock/unlock based on current state
        const lockItem = document.getElementById('ctx-lock');
        const unlockItem = document.getElementById('ctx-unlock');
        
        if (hasLockable) {
            const lockableObjects = editor.selectedObjects.filter(obj => obj.type === 'device' || obj.type === 'text');
            const anyLocked = lockableObjects.some(obj => obj.locked);
            const anyUnlocked = lockableObjects.some(obj => !obj.locked);
            const unlockedCount = lockableObjects.filter(obj => !obj.locked).length;
            const lockedCount = lockableObjects.filter(obj => obj.locked).length;
            
            if (anyUnlocked) {
                if (lockItem) {
                    lockItem.style.display = 'block';
                    lockItem.innerHTML = `🔒 Lock ${unlockedCount} objects`;
                }
            } else {
                if (lockItem) lockItem.style.display = 'none';
            }
            
            if (anyLocked) {
                if (unlockItem) {
                    unlockItem.style.display = 'block';
                    unlockItem.innerHTML = `🔓 Unlock ${lockedCount} objects`;
                }
            } else {
                if (unlockItem) unlockItem.style.display = 'none';
            }
        } else {
            if (lockItem) lockItem.style.display = 'none';
            if (unlockItem) unlockItem.style.display = 'none';
        }
        
        // Show delete
        this._safeSetDisplay('ctx-delete', 'block');
        
        // Update delete text to reflect count
        const deleteItem = document.getElementById('ctx-delete');
        if (deleteItem) {
            deleteItem.innerHTML = `🗑️ Delete ${editor.selectedObjects.length} objects`;
        }
        
        // Hide device-specific items
        this._safeSetDisplay('ctx-device-style', 'none');
        this._safeSetDisplay('ctx-ssh-address', 'none');
        this._safeSetDisplay('ctx-ssh-separator', 'none');
        this._safeSetDisplay('ctx-start-discovery', 'none');
        this._safeSetDisplay('ctx-enable-lldp', 'none');
        
        // Hide link-specific items that don't apply to bulk
        this._safeSetDisplay('ctx-change-width', hasLinks ? 'block' : 'none');
        this._safeSetDisplay('ctx-change-style', hasLinks ? 'block' : 'none');
        this._safeSetDisplay('ctx-detach-device', 'none');
        this._safeSetDisplay('ctx-detach-link', 'none');
    },

    // =========================================================================
    // MARQUEE CONTEXT MENU
    // =========================================================================

    /**
     * Show context menu for marquee-selected objects
     * @param {Object} editor - TopologyEditor instance
     * @param {number} x - Screen X position
     * @param {number} y - Screen Y position
     */
    showMarqueeContextMenu(editor, x, y) {
        const menu = document.getElementById('context-menu');
        if (!menu) return;
        
        menu.style.display = 'block';
        
        // Adjust position to keep menu within viewport
        const adjusted = this.adjustMenuPosition(x, y, menu);
        menu.style.left = adjusted.x + 'px';
        menu.style.top = adjusted.y + 'px';
        editor.contextMenuVisible = true;
        
        // Check what types of objects are selected
        const hasDevices = editor.selectedObjects.some(obj => obj.type === 'device');
        const hasLinks = editor.selectedObjects.some(obj => obj.type === 'link' || obj.type === 'unbound');
        const hasText = editor.selectedObjects.some(obj => obj.type === 'text');
        const hasLockable = editor.selectedObjects.some(obj => obj.type === 'device' || obj.type === 'text');
        
        // Show appropriate bulk operations
        this._safeSetDisplay('ctx-duplicate', 'none');
        this._safeSetDisplay('ctx-add-text', 'none');
        this._safeSetDisplay('ctx-change-color', (hasDevices || hasText) ? 'block' : 'none');
        this._safeSetDisplay('ctx-change-label', 'none');
        
        // Show curve submenu only if links are selected
        const curveSubmenu = document.getElementById('ctx-curve');
        if (curveSubmenu) {
            if (hasLinks) {
                curveSubmenu.style.display = 'block';
                const firstLink = editor.selectedObjects.find(obj => obj.type === 'link' || obj.type === 'unbound');
                editor._curveSubmenuLink = firstLink;
            } else {
                curveSubmenu.style.display = 'none';
            }
        }
        
        this._safeSetDisplay('ctx-toggle-lock', hasLockable ? 'block' : 'none');
        this._safeSetDisplay('ctx-delete', 'block');
        
        // Update lock text based on selection
        if (hasLockable) {
            const allLocked = editor.selectedObjects.filter(obj => obj.type === 'device' || obj.type === 'text').every(obj => obj.locked);
            const toggleLockItem = document.getElementById('ctx-toggle-lock');
            if (toggleLockItem) toggleLockItem.textContent = allLocked ? 'Unlock All' : 'Lock All';
        }
    },

    // =========================================================================
    // HELPERS
    // =========================================================================

    /**
     * Safely set display property on an element
     * @param {string} id - Element ID
     * @param {string} display - Display value
     */
    _safeSetDisplay(id, display) {
        const el = document.getElementById(id);
        if (el) el.style.display = display;
    }
};

console.log('[topology-context-menus.js] ContextMenus module loaded');
