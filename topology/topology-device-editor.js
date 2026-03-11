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
// ============================================================================

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
 * Update a device property from the editor modal
 * @param {TopologyEditor} editor - The editor instance
 * @param {string} property - The property name to update
 * @param {*} value - The new value
 */
function updateDeviceEditorProperty(editor, property, value) {
    if (!editor.editingDevice) return;
    if (editor.saveState) editor.saveState();
    editor.editingDevice[property] = value;
    
    // Track color changes for recent colors
    if (property === 'color' && editor.addRecentColor) {
        editor.addRecentColor(value);
    }
    
    editor.draw();
}

// Export functions
window.showDeviceEditorModal = showDeviceEditor;
window.hideDeviceEditorModal = hideDeviceEditor;
window.updateDeviceEditorPropertyExt = updateDeviceEditorProperty;

console.log('[topology-device-editor.js] Device editor module loaded');
