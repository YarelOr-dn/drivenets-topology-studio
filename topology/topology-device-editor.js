// ============================================================================
// TOPOLOGY DEVICE EDITOR MODULE
// ============================================================================
// Handles the device editor modal functionality.
// Extracted from topology.js to reduce main file size (~60 lines).
//
// Usage:
//   showDeviceEditor(editor, device);
//   hideDeviceEditor(editor);
//   updateDeviceEditorProperty(editor, property, value);
//
// 2026-05-12 [split-color]: the modal stays a "simple" entry point that
// edits `device.color` as a SOLID color. When the user opens the modal
// on a split-coloured device, we surface a small inline hint with a
// shortcut button that opens the full Split popup; we do NOT swallow
// the user's color edit silently. If they DO use the color input, the
// device is reverted to solid (this is the documented contract in
// `topology/DEVELOPMENT_GUIDELINES.md` -> "Split-color editing").
// ============================================================================

function _renderSplitColorHint(editor, device) {
    const hintId = 'editor-device-split-hint';
    let hint = document.getElementById(hintId);
    const isSplit = (typeof device.colorLeft === 'string' && device.colorLeft.trim().length > 0) &&
                    (typeof device.colorRight === 'string' && device.colorRight.trim().length > 0);
    if (!isSplit) {
        if (hint) hint.remove();
        return;
    }
    if (!hint) {
        const colorInput = document.getElementById('editor-device-color');
        if (!colorInput || !colorInput.parentElement) return;
        hint = document.createElement('div');
        hint.id = hintId;
        hint.style.cssText = 'margin-top:8px;padding:8px 10px;background:rgba(255,94,31,0.12);' +
            'border:1px solid rgba(255,94,31,0.35);border-radius:8px;font-size:11px;' +
            'color:#FFD6BD;display:flex;align-items:center;gap:8px;';
        colorInput.parentElement.appendChild(hint);
    }
    hint.innerHTML =
        `<span style="display:inline-flex;align-items:center;gap:4px;">` +
        `<span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:${device.colorLeft};border:1px solid rgba(255,255,255,0.4);"></span>` +
        `<span style="opacity:0.7;font-weight:600;">|</span>` +
        `<span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:${device.colorRight};border:1px solid rgba(255,255,255,0.4);"></span>` +
        `</span>` +
        `<span>[INFO] This device uses split colours. The colour input below will revert it to solid.</span>` +
        `<button type="button" id="editor-device-open-split" style="margin-left:auto;background:rgba(255,94,31,0.2);border:1px solid rgba(255,94,31,0.45);color:#fff;border-radius:6px;padding:4px 8px;cursor:pointer;font-size:11px;font-weight:600;">Edit halves</button>`;
    const openBtn = hint.querySelector('#editor-device-open-split');
    if (openBtn) {
        openBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            // Close the modal so the canvas popup is unobstructed.
            hideDeviceEditor(editor);
            if (editor.showColorPalettePopup) {
                editor.showColorPalettePopup(device, 'device');
            }
        };
    }
}

/**
 * Show the device editor modal
 * @param {TopologyEditor} editor - The editor instance
 * @param {object} device - The device to edit
 */
function showDeviceEditor(editor, device) {
    if (!device || device.type !== 'device') return;
    
    editor.editingDevice = device;
    
    // Set current values - with null checks
    const editorDeviceColor = document.getElementById('editor-device-color');
    const editorDeviceSize = document.getElementById('editor-device-size');
    const editorDeviceSizeValue = document.getElementById('editor-device-size-value');
    const editorDeviceLabel = document.getElementById('editor-device-label');
    const editorDeviceAddress = document.getElementById('editor-device-address');
    
    if (editorDeviceColor) editorDeviceColor.value = device.color || '#3498db';
    if (editorDeviceSize) editorDeviceSize.value = device.radius || 30;
    if (editorDeviceSizeValue) editorDeviceSizeValue.textContent = device.radius || 30;
    if (editorDeviceLabel) editorDeviceLabel.value = device.label || '';
    if (editorDeviceAddress) editorDeviceAddress.value = device.deviceAddress || '';
    
    // Update recent colors display
    if (editor.updateRecentColorsUI) editor.updateRecentColorsUI();

    // Show a split-mode hint if the device has colorLeft/colorRight.
    _renderSplitColorHint(editor, device);

    const modal = document.getElementById('device-editor-modal');
    if (modal) {
        // Reset modal position to centered before showing
        const modalContent = modal.querySelector('.modal-content');
        if (modalContent) {
            modalContent.style.position = 'relative';
            modalContent.style.left = '';
            modalContent.style.top = '';
            modalContent.style.transform = '';
            modalContent.style.margin = '';
        }
        modal.classList.add('show');
    }
}

/**
 * Hide the device editor modal
 * @param {TopologyEditor} editor - The editor instance
 */
function hideDeviceEditor(editor) {
    const modal = document.getElementById('device-editor-modal');
    if (modal) modal.classList.remove('show');
    editor.editingDevice = null;
    editor.draw();
}

/**
 * Update a device property from the editor modal.
 * 2026-05-12 [split-color]: editing `color` from this modal is treated
 * as a "go back to solid" action; we drop `colorLeft`/`colorRight` so
 * the device renders solid with the new color. The Split popup remains
 * the only way to enter / edit split mode (per the user-facing contract).
 *
 * @param {TopologyEditor} editor - The editor instance
 * @param {string} property - The property name to update
 * @param {*} value - The new value
 */
function updateDeviceEditorProperty(editor, property, value) {
    if (!editor.editingDevice) return;
    if (editor.saveState) editor.saveState();
    const dev = editor.editingDevice;
    dev[property] = value;

    if (property === 'color') {
        // Revert split mode back to solid on modal-driven colour edits.
        if (typeof dev.colorLeft === 'string' || typeof dev.colorRight === 'string') {
            delete dev.colorLeft;
            delete dev.colorRight;
        }
        if (editor.addRecentColor) editor.addRecentColor(value);
        // Re-render the split hint (will tear itself down now that the
        // device is solid again).
        _renderSplitColorHint(editor, dev);
    }

    editor.draw();
}

// Export functions
window.showDeviceEditorModal = showDeviceEditor;
window.hideDeviceEditorModal = hideDeviceEditor;
window.updateDeviceEditorPropertyExt = updateDeviceEditorProperty;

console.log('[topology-device-editor.js] Device editor module loaded');
