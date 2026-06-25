/**
 * topology-keyboard.js
 * Keyboard event handling for the Topology Editor
 * Extracted from topology.js to reduce file size
 * 
 * This module handles:
 * - Key down events (shortcuts, tool toggles, etc.)
 * - Key up events (modifier key tracking)
 * - Input focus detection to avoid conflicts
 */

const _arrowKeys = new Set(['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight']);
const _arrowKeysDown = new Set();
let _arrowPanRaf = null;
let _arrowPanEditor = null;
const _ARROW_PAN_SPEED = 6;
const _nonTextInputTypes = new Set(['color', 'checkbox', 'radio', 'range', 'button', 'submit', 'reset']);
let _appRefreshInProgress = false;

function _arrowPanTick() {
    const editor = _arrowPanEditor;
    if (!editor || _arrowKeysDown.size === 0) {
        _arrowPanRaf = null;
        return;
    }
    let dx = 0, dy = 0;
    if (_arrowKeysDown.has('ArrowLeft'))  dx += 1;
    if (_arrowKeysDown.has('ArrowRight')) dx -= 1;
    if (_arrowKeysDown.has('ArrowUp'))    dy += 1;
    if (_arrowKeysDown.has('ArrowDown'))  dy -= 1;

    if (dx !== 0 || dy !== 0) {
        const mag = Math.sqrt(dx * dx + dy * dy);
        const zoom = editor.zoom || 1;
        const speed = _ARROW_PAN_SPEED / zoom;
        editor.panOffset.x += (dx / mag) * speed;
        editor.panOffset.y += (dy / mag) * speed;
        editor.savePanOffset();
        editor.updateScrollbars();
        editor.draw();
    }
    _arrowPanRaf = requestAnimationFrame(_arrowPanTick);
}

function _elementFromEventTarget(target) {
    if (!target) return null;
    if (target.nodeType === 1) return target;
    if (target.parentElement) return target.parentElement;
    return null;
}

function _isEditableShortcutTarget(target) {
    const el = _elementFromEventTarget(target);
    if (!el) return false;

    const editable = el.closest?.('input, textarea, select, [contenteditable]');
    if (!editable) return false;

    const tagName = editable.tagName;
    if (tagName === 'INPUT') {
        return !_nonTextInputTypes.has((editable.type || 'text').toLowerCase());
    }
    if (tagName === 'TEXTAREA' || tagName === 'SELECT') {
        return true;
    }
    return editable.getAttribute('contenteditable') !== 'false';
}

function _isRKey(e) {
    const key = typeof e.key === 'string' ? e.key.toLowerCase() : '';
    return key === 'r' || e.code === 'KeyR';
}

function _isBrowserRefreshShortcut(e) {
    if (e.key === 'F5') return true;
    return _isRKey(e) && (e.ctrlKey || e.metaKey) && !e.altKey;
}

function _shouldHandleAppRefreshShortcut(e, isInputFocused) {
    return !_appRefreshInProgress
        && !e.repeat
        && _isRKey(e)
        && !isInputFocused
        && !e.metaKey
        && !e.ctrlKey
        && !e.altKey
        && !e.shiftKey;
}

function _triggerAppRefresh(e) {
    _appRefreshInProgress = true;
    console.log('R key pressed - refreshing...');
    e.preventDefault();
    e.stopPropagation();
    if (typeof e.stopImmediatePropagation === 'function') {
        e.stopImmediatePropagation();
    }
    const topoMenu = document.getElementById('topologies-dropdown-menu');
    if (topoMenu) topoMenu.style.display = 'none';
    window.location.reload();
}

/**
 * Handle keyboard down events
 * @param {TopologyEditor} editor - The editor instance
 * @param {KeyboardEvent} e - The keyboard event
 */
function handleKeyDown(editor, e) {
    // Track modifier keys regardless of dialogs (needed for multi-select etc.)
    if (e.key === 'Control' || e.key === 'Meta') { editor.ctrlPressed = true; }
    if (e.key === 'Alt') { editor.altPressed = true; }
    if (e.key === 'Shift') { editor.shiftPressed = true; }
    
    if (!e.key) return;

    // Browser-native refresh shortcuts must remain untouched. The app owns
    // only plain unmodified R/physical KeyR, handled below after focus checks.
    if (_isBrowserRefreshShortcut(e)) {
        return;
    }
    
    // DIALOG GUARD: Block all editor shortcuts (except Escape) when an
    // interactive dialog/modal/popup/overlay is open. Dynamic popups are
    // created and removed on close. Permanent modals use .show qualifier.
    // Read-only panels (stack, LLDP, git-commit, xray) are excluded so
    // canvas shortcuts keep working while viewing reference data.
    const _dialogSelectors = [
        '#enable-lldp-dialog-overlay',
        '#dnaas-topology-dialog',
        '#dnaas-save-dialog',
        '#recovery-modal',
        '#new-topo-domain-picker',
        '#quick-save-domain-picker',
        '#png-export-dialog',
        '#device-style-palette-popup',
        '#device-label-style-menu',
        '#link-style-options-popup',
        '#link-curve-options-popup',
        '#link-width-slider-popup',
        '#width-slider-popup',
        '#color-palette-popup',
        '#text-editor-modal.show',
        '#link-editor-modal.show',
        '#link-details-modal.show',
        '#device-editor-modal.show',
        '#shortcuts-modal.show',
    ];
    let openDialog = null;
    try {
        const candidates = document.querySelectorAll(_dialogSelectors.join(', '));
        for (const el of candidates) {
            if (el.offsetParent !== null || el.style.display === 'flex' || el.style.display === 'block'
                || el.classList.contains('show') || (el.style.opacity && el.style.opacity !== '0')) {
                openDialog = el;
                break;
            }
        }
    } catch (err) {
        console.warn('[KB] dialog guard selector error:', err);
    }
    if (openDialog) {
        if (e.key === 'Escape') {
            if (openDialog.classList?.contains('show')) {
                openDialog.classList.remove('show');
            } else {
                openDialog.remove();
            }
            e.preventDefault();
            e.stopPropagation();
        }
        return;
    }
    
    // Check if focus is on editable text/select controls to avoid conflicts.
    const isInputFocused = _isEditableShortcutTarget(e.target);
    
    // Plain R refreshes the app canvas page. Physical KeyR is accepted so the
    // shortcut remains reliable across keyboard layouts and CapsLock state.
    if (_shouldHandleAppRefreshShortcut(e, isInputFocused)) {
        _triggerAppRefresh(e);
        return false;
    }
    
    // Guard: some key events (dead keys, IME) have undefined e.key
    if (!e.key) return;

    // Toggle DNAAS panel with 'D' key (when no input is focused)
    if (e.key.toLowerCase() === 'd' && !isInputFocused && !e.metaKey && !e.ctrlKey) {
        const dnaasBtn = document.getElementById('btn-dnaas');
        if (dnaasBtn) {
            dnaasBtn.click();
            console.log('DNAAS panel toggled');
        }
        return;
        // NOTE: Old debugger toggle - use editor.debugger.toggle() in console if needed
    }
    
    // 'B' key for BD Legend panel toggle
    if (e.key.toLowerCase() === 'b' && !isInputFocused && !e.metaKey && !e.ctrlKey) {
        editor.toggleBDLegendPanel();
        return;
    }

    // 'T' key for Topologies dropdown toggle
    if (e.key.toLowerCase() === 't' && !isInputFocused && !e.metaKey && !e.ctrlKey) {
        const btnTopo = document.getElementById('btn-topologies');
        if (btnTopo) btnTopo.click();
        return;
    }

    // 'M' key for Minimap toggle (when no input is focused)
    if (e.key.toLowerCase() === 'm' && !isInputFocused && !e.metaKey && !e.ctrlKey) {
        editor.toggleMinimap();
        return;
    }
    
    // 'G' key handling (when no input is focused):
    //   - plain "G"           -> Groups panel toggle (new unified panel)
    //   - Cmd/Ctrl+Shift+G    -> Grid lines toggle (was plain "G" pre 2026-04-30)
    // The grid toggle was relocated when the Groups panel was promoted
    // to a first-class top-toolbar feature; the Cmd/Ctrl+Shift+G combo
    // matches the convention used by other rare-use canvas toggles.
    if (e.key.toLowerCase() === 'g' && !isInputFocused) {
        if ((e.metaKey || e.ctrlKey) && e.shiftKey) {
            e.preventDefault();
            editor.toggleGridLines();
            return;
        }
        if (!e.metaKey && !e.ctrlKey && !e.altKey && !e.shiftKey) {
            if (window.GroupsPanel) {
                window.GroupsPanel.toggle(editor);
            }
            return;
        }
    }
    
    // Bare number keys activate tools. Cmd/Ctrl+1..9 keeps topology quick-jump.
    if (e.key >= '1' && e.key <= '9' && !isInputFocused && !e.altKey) {
        if (e.metaKey || e.ctrlKey) {
            if (window.FileOps && window.FileOps._domainTopoCache && window.FileOps._domainTopoCache.length > 1) {
                const idx = parseInt(e.key) - 1;
                if (idx < window.FileOps._domainTopoCache.length) {
                    e.preventDefault();
                    window.FileOps._navigateToTopology(idx);
                    return;
                }
            }
            return;
        }

        const slot = {
            '1': 'select',
            '2': 'link',
            '3': 'device',
            '4': 'shape',
            '5': 'text',
            '6': 'laser',
        }[e.key];
        if (slot && window.toolbarManager) {
            e.preventDefault();
            window.toolbarManager.activateTool(slot, { quickAccess: true, source: 'shortcut' });
            return;
        }
    }

    if (e.key === '0' && !isInputFocused && !e.metaKey && !e.ctrlKey && !e.altKey) {
        e.preventDefault();
        window.toolbarManager?.activateTool('settings', { quickAccess: true, source: 'shortcut' });
        return;
    }

    // Alt + Left/Right arrow to navigate prev/next topology in domain
    if (e.altKey && !e.metaKey && !e.ctrlKey && !isInputFocused) {
        if (e.key === 'ArrowLeft') {
            if (window.FileOps && window.FileOps._domainTopoCache && window.FileOps._domainTopoCache.length > 1) {
                e.preventDefault();
                window.FileOps.navigateTopoByOffset(-1);
                return;
            }
        }
        if (e.key === 'ArrowRight') {
            if (window.FileOps && window.FileOps._domainTopoCache && window.FileOps._domainTopoCache.length > 1) {
                e.preventDefault();
                window.FileOps.navigateTopoByOffset(1);
                return;
            }
        }
    }

    // Arrow keys (no modifiers) - smooth canvas pan with multi-key diagonal
    if (_arrowKeys.has(e.key) && !isInputFocused && !e.altKey && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        if (_arrowKeysDown.size === 0 && editor.beginCanvasPanInteraction) {
            editor.beginCanvasPanInteraction();
        }
        _arrowKeysDown.add(e.key);
        _arrowPanEditor = editor;
        if (!_arrowPanRaf) {
            _arrowPanRaf = requestAnimationFrame(_arrowPanTick);
        }
        return;
    }

    // 'L' key for Light/Dark mode toggle (when no input is focused)
    if (e.key.toLowerCase() === 'l' && !isInputFocused && !e.metaKey && !e.ctrlKey) {
        editor.toggleTheme();
        return;
    }
    
    // 'F' key for Fit/Center all objects in view
    if (e.key.toLowerCase() === 'f' && !isInputFocused && !e.metaKey && !e.ctrlKey) {
        editor.centerOnDevices();
        return;
    }
    
    // '+' / '=' key for zoom in, '-' key for zoom out
    if ((e.key === '+' || e.key === '=') && !isInputFocused && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        editor.zoomIn();
        return;
    }
    if (e.key === '-' && !isInputFocused && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        editor.zoomOut();
        return;
    }
    
    // 'C' key: Copy Style (object selected) or toggle Config panel (nothing selected)
    if (e.key.toLowerCase() === 'c' && !isInputFocused && !e.metaKey && !e.ctrlKey) {
        if (editor.selectedObject) {
            const objType = editor.selectedObject.type;
            const objLabel = editor.selectedObject.label || editor.selectedObject.text || editor.selectedObject.id;
            editor.copyObjectStyle(editor.selectedObject);
            if (editor.debugger) {
                editor.debugger.logSuccess(`CS: Style copied from ${objType}: ${objLabel}`);
            }
        } else if (typeof ScalerGUI !== 'undefined') {
            const now = Date.now();
            if (now - (editor._lastScalerToggle || 0) < 300) return;
            editor._lastScalerToggle = now;
            const hasOpenPanels = ScalerGUI.state?.activePanel
                || Object.keys(ScalerGUI.state?.activePanels || {}).length > 0;
            if (hasOpenPanels) {
                ScalerGUI.closeAllPanels();
            } else {
                ScalerGUI.openScalerMenu();
            }
        }
        return;
    }
    
    // LAYER SHORTCUTS (like Photoshop/Figma)
    // Cmd/Ctrl + ] = Move Forward, Cmd/Ctrl + [ = Move Backward
    // Cmd/Ctrl + Shift + ] = To Front, Cmd/Ctrl + Shift + [ = To Back
    if ((e.metaKey || e.ctrlKey) && e.key === ']' && !isInputFocused) {
        e.preventDefault();
        if (editor.selectedObject || editor.selectedObjects.length > 0) {
            if (e.shiftKey) {
                // Reuse context menu handler (has proper multi-select logic)
                editor.handleContextLayerToFront();
            } else {
                // Move Forward - simple for multi-select (all move +1)
                editor.handleContextLayerForward();
            }
        }
        return;
    }
    
    if ((e.metaKey || e.ctrlKey) && e.key === '[' && !isInputFocused) {
        e.preventDefault();
        if (editor.selectedObject || editor.selectedObjects.length > 0) {
            if (e.shiftKey) {
                // Reuse context menu handler (has proper multi-select logic)
                editor.handleContextLayerToBack();
            } else {
                // Move Backward - simple for multi-select (all move -1)
                editor.handleContextLayerBackward();
            }
        }
        return;
    }
    
    // Toggle left toolbar with '[' key (when no modifier and no input focused)
    if (e.key === '[' && !isInputFocused && !e.metaKey && !e.ctrlKey) {
        const toolbar = document.getElementById('left-toolbar');
        if (toolbar) {
            toolbar.classList.toggle('collapsed');
            editor.syncBarCollapseState?.();
            if (editor.smoothResizeDuring) editor.smoothResizeDuring();
            else { setTimeout(() => { editor.resizeCanvas(); editor.draw(); }, 300); }
            if (editor.debugger) {
                editor.debugger.logInfo(`Left toolbar ${toolbar.classList.contains('collapsed') ? 'hidden' : 'shown'}`);
            }
        }
        return;
    }

    // Toggle top bar with ']' key (when no modifier and no input focused)
    if (e.key === ']' && !isInputFocused && !e.metaKey && !e.ctrlKey) {
        const topBar = document.querySelector('.top-bar');
        if (topBar) {
            topBar.classList.toggle('collapsed');
            editor.syncBarCollapseState?.();
            if (editor.smoothResizeDuring) editor.smoothResizeDuring();
            else { setTimeout(() => { editor.resizeCanvas(); editor.draw(); }, 300); }
            if (editor.debugger) {
                editor.debugger.logInfo(`Top bar ${topBar.classList.contains('collapsed') ? 'hidden' : 'shown'}`);
            }
        }
        return;
    }
    
    // Cmd/Ctrl + S — save to current domain file, or quick save dialog
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's') {
        if (!isInputFocused) {
            e.preventDefault();
            if (window.FileOps) window.FileOps._cmdSave(editor);
        }
        return;
    }
    
    // Cmd/Ctrl + T for text size (only when text is selected)
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 't') {
        if (!isInputFocused) {
            e.preventDefault();
            if (editor.selectedObject && editor.selectedObject.type === 'text') {
                editor.cycleTextSize();
            }
        }
        return;
    }
    
    // ⌘ + L (Mac) or Ctrl + L (Windows/Linux) for unbound link
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'l') {
        if (!isInputFocused) {
            e.preventDefault();
            editor.createUnboundLink();
        }
        return;
    }
    
    // Cmd/Ctrl + Shift + D to set current view as default
    if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key.toLowerCase() === 'd') {
        if (!isInputFocused) {
            e.preventDefault();
            editor.setDefaultView();
            // Show brief confirmation
            const indicator = document.getElementById('mode-indicator');
            if (indicator) {
                const modeText = indicator.querySelector('#mode-text');
                const originalText = modeText.textContent;
                modeText.textContent = 'DEFAULT VIEW SET';
                setTimeout(() => {
                    modeText.textContent = originalText;
                }, 1000);
            }
        }
        return;
    }
    
    // Cmd/Ctrl + X clears the currently opened topology (with confirmation).
    // The shortcut is intentionally selection-agnostic: it always asks the
    // user before wiping the canvas, then routes through editor.clearCanvas
    // -> FileOps._clearCurrentTopologyOnly so the empty snapshot is written
    // ONLY to the active topology row. Other topologies, other domains, and
    // shared-with-me views are not touched.
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'x') {
        if (!isInputFocused) {
            e.preventDefault();
            if (typeof editor.clearCanvas === 'function') {
                editor.clearCanvas();
            }
        }
        return;
    }
    
    // Cmd/Ctrl + Z for undo
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'z' && !e.shiftKey) {
        console.log('⏪ Cmd+Z detected, isInputFocused:', isInputFocused);
        if (!isInputFocused) {
            e.preventDefault();
            editor.undo();
        } else {
            console.log('⚠️ Undo blocked - input is focused');
        }
        return;
    }
    
    // Cmd/Ctrl + C for copy
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'c') {
        if (!isInputFocused) {
            e.preventDefault();
            editor.copySelected();
        }
        return;
    }
    
    // Cmd/Ctrl + V for paste
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'v') {
        if (!isInputFocused) {
            e.preventDefault();
            editor.pasteObjects();
        }
        return;
    }
    
    // Cmd/Ctrl + Y or Cmd/Ctrl + Shift + Z for redo
    if (((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'y') ||
        ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'z' && e.shiftKey)) {
        if (!isInputFocused) {
            e.preventDefault();
            editor.redo();
        }
        return;
    }
    
    if (e.key === 'Delete' || e.key === 'Backspace') {
        if (!isInputFocused) {
            e.preventDefault();
            editor.deleteSelected();
            return; // Only return if we handled the delete
        }
        // If input is focused, let browser handle it naturally (don't return, don't prevent)
    }
    
    if (e.key === 'Escape') {
        // Exit various modes - check for text selection toolbar first
        if (editor._textSelectionToolbar) {
            editor.hideTextSelectionToolbar();
        } else if (editor.contextMenuVisible) {
            editor.hideContextMenu();
        } else if (editor._linkFromTP) {
            // Exit "link from TP" mode
            editor._linkFromTP = null;
            editor.linking = false;
            editor.linkStart = null;
            editor.setMode('select');
            if (editor.debugger) {
                editor.debugger.logInfo('🔗 Link from TP: Cancelled');
            }
            editor.draw();
        } else if (editor.csmsMode) {
            // Exit CS-MS marquee mode but stay in paste style mode
            editor.csmsMode = false;
            editor.marqueeActive = false;
            editor.selectionRectangle = null;
            editor.selectionRectStart = null;
            editor.canvas.style.cursor = 'copy';
            if (editor.debugger) {
                editor.debugger.logInfo(`CS-MS cancelled - still in paste mode`);
            }
            editor.draw();
        } else if (editor.pasteStyleMode) {
            // Exit paste style mode
            editor.exitPasteStyleMode();
        } else if (editor.placingDevice) {
            // Exit device placement mode
            editor.placingDevice = null;
            editor.placementPending = null;
            editor.setMode('base');
        } else if (editor.currentTool === 'laser') {
            if (window.toolbarManager && window.toolbarManager.closeToolPanel) {
                window.toolbarManager.closeToolPanel();
            }
            editor.setMode('base');
        } else if (editor.currentTool === 'text') {
            // Exit text placement mode
            editor.textPlacementPending = null;
            editor.setMode('base');
        } else if (editor.multiSelectMode) {
            editor.multiSelectMode = false;
            editor.selectedObjects = [];
            if (editor.selectedObject) {
                editor.selectedObjects = [editor.selectedObject];
            }
            editor.draw();
        } else {
            const toolPanel = document.querySelector('#left-toolbar .tool-side-panel');
            if (toolPanel && toolPanel.dataset.tool) {
                if (window.toolbarManager && window.toolbarManager.closeToolPanel) {
                    window.toolbarManager.closeToolPanel();
                } else {
                    toolPanel.dataset.tool = '';
                }
            }
        }
    } else if (e.key === ' ') {
        // Polish + QA pass 2026-05-12: only flip spacePressed (which arms
        // canvas pan-on-drag) when the user is NOT typing into an editable
        // input. Otherwise typing a space inside an inline text editor or
        // sidebar input would silently arm pan mode for the next click.
        if (!_isEditableShortcutTarget(e.target)) {
            editor.spacePressed = true;
            editor.updateCursor();
            e.preventDefault();
        }
    }
}

/**
 * Handle keyboard up events
 * @param {TopologyEditor} editor - The editor instance
 * @param {KeyboardEvent} e - The keyboard event
 */
function handleKeyUp(editor, e) {
    if (e.key === ' ') {
        // Mirror the keydown gate (only release when not in an editable
        // input). Avoids leaking spacePressed=false when the user releases
        // space inside a textarea after typing.
        if (!_isEditableShortcutTarget(e.target)) {
            editor.spacePressed = false;
            editor.updateCursor();
        }
    }

    // Arrow key release - stop pan when all released
    if (_arrowKeys.has(e.key)) {
        _arrowKeysDown.delete(e.key);
        if (_arrowKeysDown.size === 0) {
            if (_arrowPanRaf) {
                cancelAnimationFrame(_arrowPanRaf);
                _arrowPanRaf = null;
            }
            if (editor.restoreToolbarAfterCanvasPan) {
                editor.restoreToolbarAfterCanvasPan();
            }
        }
    }
    
    // Track Ctrl/Cmd release
    if (e.key === 'Control' || e.key === 'Meta') {
        editor.ctrlPressed = false;
    }
    
    // Track Alt/Option release
    if (e.key === 'Alt') {
        editor.altPressed = false;
    }
    
    // Track Shift release - exit paste style mode if in continuous paste
    if (e.key === 'Shift') {
        editor.shiftPressed = false;
        // If we were in continuous paste mode, exit to base mode
        if (editor.pasteStyleMode) {
            editor.exitPasteStyleMode();
        }
    }
}

// Clear arrow pan on window blur to prevent stuck keys
window.addEventListener('blur', () => {
    const editor = _arrowPanEditor;
    _arrowKeysDown.clear();
    if (_arrowPanRaf) {
        cancelAnimationFrame(_arrowPanRaf);
        _arrowPanRaf = null;
    }
    if (editor && editor.restoreToolbarAfterCanvasPan) {
        editor.restoreToolbarAfterCanvasPan();
    }
});

// Export functions to window
window.KeyboardHandler = {
    handleKeyDown,
    handleKeyUp,
    _isEditableShortcutTarget,
    _isBrowserRefreshShortcut,
    _shouldHandleAppRefreshShortcut
};

console.log('[topology-keyboard.js] Keyboard handler module loaded');
