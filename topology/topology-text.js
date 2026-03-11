// ============================================================================
// TOPOLOGY TEXT MANAGER MODULE
// ============================================================================
// Handles text object creation, editing, styling, and attachment.
// This is a wrapper module that delegates to editor methods.
//
// Usage:
//   const textMgr = new TextManager(editor);
//   textMgr.create(100, 200);
//   textMgr.updateSize('large');
// ============================================================================

class TextManager {
    constructor(editor) {
        this.editor = editor;
    }

    // ========== CREATION ==========
    
    /**
     * Create a new text object at position
     * @param {number} x - World X coordinate
     * @param {number} y - World Y coordinate
     * @param {string} content - Initial text content
     * @returns {object} Created text object
     */
    create(x, y, content = 'Text') {
        if (this.editor.createText) {
            return this.editor.createText(x, y, content);
        }
        console.warn('TextManager: createText not available on editor');
        return null;
    }

    /**
     * Add adjacent text to a link
     * @param {object} link - Link object to attach text to
     * @param {string} position - 'middle', 'start', 'end'
     * @param {string} content - Text content
     * @returns {object} Created text object
     */
    addAdjacentText(link, position = 'middle', content = 'Label') {
        if (this.editor.addAdjacentText) {
            return this.editor.addAdjacentText(link, position, content);
        }
        return null;
    }

    // ========== FINDING ==========
    
    /**
     * Find text object at world coordinates
     * @param {number} x - World X
     * @param {number} y - World Y
     * @returns {object|null} Text object or null
     */
    findAt(x, y) {
        if (this.editor.findTextAt) {
            return this.editor.findTextAt(x, y);
        }
        return null;
    }

    /**
     * Get all text objects
     * @returns {array} Array of text objects
     */
    getAll() {
        return this.editor.objects?.filter(obj => obj.type === 'text') || [];
    }

    /**
     * Get selected text objects
     * @returns {array} Array of selected text objects
     */
    getSelected() {
        return this.editor.selectedObjects?.filter(obj => obj.type === 'text') || [];
    }

    // ========== EDITING ==========
    
    /**
     * Show text editor for object
     * @param {object} textObj - Text object to edit
     */
    showEditor(textObj) {
        if (this.editor.showTextEditor) {
            this.editor.showTextEditor(textObj);
        }
    }

    /**
     * Hide text editor
     */
    hideEditor() {
        if (this.editor.hideTextEditor) {
            this.editor.hideTextEditor();
        }
    }

    /**
     * Show inline text editor
     * @param {object} textObj - Text object
     * @param {Event} event - Mouse event
     */
    showInlineEditor(textObj, event) {
        if (this.editor.showInlineTextEditor) {
            this.editor.showInlineTextEditor(textObj, event);
        }
    }

    /**
     * Hide inline text editor
     */
    hideInlineEditor() {
        if (this.editor.hideInlineTextEditor) {
            this.editor.hideInlineTextEditor();
        }
    }

    // ========== STYLING ==========
    
    /**
     * Update text size
     * @param {string} size - 'small', 'medium', 'large', 'xlarge'
     */
    updateSize(size) {
        if (this.editor.updateTextSize) {
            this.editor.updateTextSize(size);
        }
    }

    /**
     * Cycle text size through predefined values
     */
    cycleSize() {
        if (this.editor.cycleTextSize) {
            this.editor.cycleTextSize();
        }
    }

    /**
     * Update text properties (general)
     */
    updateProperties() {
        if (this.editor.updateTextProperties) {
            this.editor.updateTextProperties();
        }
    }

    /**
     * Apply font to selected text
     * @param {string} fontFamily - Font family name
     * @param {number} fontSize - Font size in pixels
     */
    applyFont(fontFamily, fontSize) {
        if (this.editor.applyFontToSelectedText) {
            this.editor.applyFontToSelectedText(fontFamily, fontSize);
        }
    }

    /**
     * Show color palette for text
     * @param {object} textObj - Text object
     */
    showColorPalette(textObj) {
        if (this.editor.showTextColorPalette) {
            this.editor.showTextColorPalette(textObj);
        }
    }

    /**
     * Show background color palette for text
     * @param {object} textObj - Text object
     */
    showBgColorPalette(textObj) {
        if (this.editor.showTextBgColorPalette) {
            this.editor.showTextBgColorPalette(textObj);
        }
    }

    /**
     * Show font selector for text
     * @param {object} textObj - Text object
     */
    showFontSelector(textObj) {
        if (this.editor.showTextFontSelector) {
            this.editor.showTextFontSelector(textObj);
        }
    }

    // ========== TOOLBAR ==========
    
    /**
     * Show text selection toolbar
     * @param {object} textObj - Selected text object
     */
    showToolbar(textObj) {
        if (this.editor.showTextSelectionToolbar) {
            this.editor.showTextSelectionToolbar(textObj);
        }
    }

    /**
     * Hide text selection toolbar
     */
    hideToolbar() {
        if (this.editor.hideTextSelectionToolbar) {
            this.editor.hideTextSelectionToolbar();
        }
    }

    /**
     * Update toolbar position
     */
    updateToolbarPosition() {
        if (this.editor.updateTextSelectionToolbarPosition) {
            this.editor.updateTextSelectionToolbarPosition();
        }
    }

    // ========== ATTACHMENT ==========
    
    /**
     * Attach text to a link
     * @param {object} textObj - Text object
     * @param {object} link - Link to attach to
     * @param {number} t - Position along link (0-1)
     */
    attachToLink(textObj, link, t) {
        if (this.editor.attachTextToLink) {
            this.editor.attachTextToLink(textObj, link, t);
        }
    }

    /**
     * Check if text overlaps with any link
     * @param {object} textObj - Text object
     * @returns {object|null} Overlapping link or null
     */
    checkLinkOverlap(textObj) {
        if (this.editor.checkTextLinkOverlap) {
            return this.editor.checkTextLinkOverlap(textObj);
        }
        return null;
    }

    /**
     * Detach text from link
     * @param {object} textObj - Text object to detach
     */
    detachFromLink(textObj) {
        if (this.editor.handleContextDetachFromLink && textObj) {
            // Temporarily select the text to use context menu handler
            const prevSelected = this.editor.selectedObjects;
            this.editor.selectedObjects = [textObj];
            this.editor.handleContextDetachFromLink();
            this.editor.selectedObjects = prevSelected;
        }
    }

    // ========== SETTINGS ==========
    
    /**
     * Save current text settings as default
     */
    saveDefaults() {
        if (this.editor.saveDefaultTextSettings) {
            this.editor.saveDefaultTextSettings();
        }
    }

    /**
     * Load default text settings
     * @returns {object} Default settings
     */
    loadDefaults() {
        if (this.editor.loadDefaultTextSettings) {
            return this.editor.loadDefaultTextSettings();
        }
        return {};
    }

    /**
     * Apply settings to selected text
     * @param {object} settings - Settings to apply
     * @param {string} changedProperty - Specific property that changed
     */
    applySettings(settings, changedProperty = null) {
        if (this.editor.applyTextSettingsToSelected) {
            this.editor.applyTextSettingsToSelected(settings, changedProperty);
        }
    }

    // ========== MODES ==========
    
    /**
     * Enter text placement mode
     */
    enterPlacementMode() {
        if (this.editor.enterTextPlacementMode) {
            this.editor.enterTextPlacementMode();
        }
    }

    /**
     * Toggle continuous text placement mode
     */
    toggleContinuousPlacement() {
        if (this.editor.toggleContinuousTextPlacement) {
            this.editor.toggleContinuousTextPlacement();
        }
    }

    /**
     * Exit continuous text placement mode
     */
    exitContinuousPlacement() {
        if (this.editor.exitContinuousTextPlacement) {
            this.editor.exitContinuousTextPlacement();
        }
    }

    // ========== UTILITY ==========
    
    /**
     * Get count of text objects
     * @returns {number} Count
     */
    getCount() {
        return this.getAll().length;
    }

    /**
     * Delete a text object
     * @param {object} textObj - Text object to delete
     */
    delete(textObj) {
        if (textObj && this.editor.objects) {
            const idx = this.editor.objects.indexOf(textObj);
            if (idx !== -1) {
                this.editor.objects.splice(idx, 1);
                this.editor.draw();
                this.editor.saveState();
            }
        }
    }
}

// Export for module loading
window.TextManager = TextManager;
window.createTextManager = function(editor) {
    return new TextManager(editor);
};

console.log('TextManager module loaded');
