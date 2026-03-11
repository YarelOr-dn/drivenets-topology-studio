// ============================================================================
// TOPOLOGY DEVICE RENAME POPUP MODULE
// ============================================================================
// Handles the device rename popup with font settings.
// Extracted from topology.js to reduce main file size (~350 lines).
//
// Usage:
//   showRenamePopup(editor, device);
//   hideRenamePopup();
//   applyRename(editor, device, newLabel, fontSettings);
// ============================================================================

/**
 * Show device rename popup with font controls
 * @param {TopologyEditor} editor - The editor instance
 * @param {object} device - The device object
 */
function showRenamePopup(editor, device) {
    // Remove any existing rename popup
    const existingPopup = document.getElementById('rename-popup');
    if (existingPopup) existingPopup.remove();
    
    // Get device screen position
    const screenPos = editor.worldToScreen({ x: device.x, y: device.y });
    
    // Create rename popup
    const popup = document.createElement('div');
    popup.id = 'rename-popup';
    popup.style.cssText = `
        position: fixed;
        left: ${screenPos.x + 50}px;
        top: ${screenPos.y - 20}px;
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 2px solid #3498db;
        border-radius: 8px;
        padding: 12px;
        z-index: 10001;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        min-width: 200px;
    `;
    
    // Title
    const title = document.createElement('div');
    const editIcon = typeof appIcon === 'function' ? appIcon('edit') : '✏️';
    title.innerHTML = `${editIcon} Rename Device`;
    title.style.cssText = 'color: #3498db; font-size: 12px; font-weight: bold; margin-bottom: 10px;';
    popup.appendChild(title);
    
    // Input field
    const input = document.createElement('input');
    input.type = 'text';
    input.value = device.label || '';
    input.placeholder = 'Enter device name';
    input.maxLength = 20;
    input.style.cssText = `
        width: 100%;
        padding: 8px 12px;
        background: #2d3748;
        border: 1px solid #4a5568;
        border-radius: 4px;
        color: #ecf0f1;
        font-size: 14px;
        outline: none;
        box-sizing: border-box;
    `;
    input.onfocus = () => input.style.borderColor = '#3498db';
    input.onblur = () => input.style.borderColor = '#4a5568';
    popup.appendChild(input);
    
    // Font controls section
    const fontSection = document.createElement('div');
    fontSection.style.cssText = 'margin-top: 12px; padding-top: 12px; border-top: 1px solid #4a5568;';
    
    const fontLabel = document.createElement('div');
    fontLabel.textContent = 'Font Settings';
    fontLabel.style.cssText = 'color: #3498db; font-size: 11px; font-weight: bold; margin-bottom: 8px;';
    fontSection.appendChild(fontLabel);
    
    // Font Family
    const fontFamilyContainer = document.createElement('div');
    fontFamilyContainer.style.cssText = 'margin-bottom: 8px;';
    const fontFamilyLabel = document.createElement('label');
    fontFamilyLabel.textContent = 'Family:';
    fontFamilyLabel.style.cssText = 'color: #ecf0f1; font-size: 11px; display: block; margin-bottom: 4px;';
    fontFamilyContainer.appendChild(fontFamilyLabel);
    const fontFamilySelect = document.createElement('select');
    fontFamilySelect.style.cssText = `
        width: 100%;
        padding: 6px 8px;
        background: #2d3748;
        border: 1px solid #4a5568;
        border-radius: 4px;
        color: #ecf0f1;
        font-size: 12px;
        outline: none;
        box-sizing: border-box;
    `;
    // Font families - MATCHING TB options for consistency
    const fontFamilies = [
        { value: 'Inter, sans-serif', label: 'Sans' },
        { value: "'IBM Plex Sans', sans-serif", label: 'Brand' },
        { value: "'Caveat', cursive", label: 'Hand' },
        { value: "'IBM Plex Mono', monospace", label: 'Mono' },
        { value: 'Georgia, serif', label: 'Serif' },
        { value: "'Comic Neue', cursive", label: 'Sketch' },
        { value: '-apple-system, BlinkMacSystemFont, sans-serif', label: 'System' },
        { value: 'Arial, sans-serif', label: 'Classic' }
    ];
    fontFamilies.forEach(font => {
        const option = document.createElement('option');
        option.value = font.value;
        option.textContent = font.label;
        if ((device.fontFamily || editor.defaultDeviceFontFamily || 'Inter, sans-serif') === font.value) {
            option.selected = true;
        }
        fontFamilySelect.appendChild(option);
    });
    fontFamilyContainer.appendChild(fontFamilySelect);
    fontSection.appendChild(fontFamilyContainer);
    
    // Font Size
    const fontSizeContainer = document.createElement('div');
    fontSizeContainer.style.cssText = 'margin-bottom: 8px;';
    const fontSizeLabel = document.createElement('label');
    fontSizeLabel.textContent = 'Size:';
    fontSizeLabel.style.cssText = 'color: #ecf0f1; font-size: 11px; display: block; margin-bottom: 4px;';
    fontSizeContainer.appendChild(fontSizeLabel);
    const fontSizeInput = document.createElement('input');
    fontSizeInput.type = 'number';
    fontSizeInput.min = '6';
    fontSizeInput.max = '30';
    fontSizeInput.value = device.labelSize || device.fontSize || Math.max(6, Math.min(device.radius * 0.35, 30));
    fontSizeInput.style.cssText = `
        width: 100%;
        padding: 6px 8px;
        background: #2d3748;
        border: 1px solid #4a5568;
        border-radius: 4px;
        color: #ecf0f1;
        font-size: 12px;
        outline: none;
        box-sizing: border-box;
    `;
    fontSizeContainer.appendChild(fontSizeInput);
    fontSection.appendChild(fontSizeContainer);
    
    // Font Weight and Style row
    const fontStyleRow = document.createElement('div');
    fontStyleRow.style.cssText = 'display: flex; gap: 8px;';
    
    // Font Weight
    const fontWeightContainer = document.createElement('div');
    fontWeightContainer.style.cssText = 'flex: 1;';
    const fontWeightLabel = document.createElement('label');
    fontWeightLabel.textContent = 'Weight:';
    fontWeightLabel.style.cssText = 'color: #ecf0f1; font-size: 11px; display: block; margin-bottom: 4px;';
    fontWeightContainer.appendChild(fontWeightLabel);
    const fontWeightSelect = document.createElement('select');
    fontWeightSelect.style.cssText = `
        width: 100%;
        padding: 6px 8px;
        background: #2d3748;
        border: 1px solid #4a5568;
        border-radius: 4px;
        color: #ecf0f1;
        font-size: 12px;
        outline: none;
        box-sizing: border-box;
    `;
    const fontWeights = ['normal', 'bold', '100', '200', '300', '400', '500', '600', '700', '800', '900'];
    fontWeights.forEach(weight => {
        const option = document.createElement('option');
        option.value = weight;
        option.textContent = weight === 'normal' ? 'Normal' : weight === 'bold' ? 'Bold' : weight;
        if ((device.fontWeight || 'normal') === weight) {
            option.selected = true;
        }
        fontWeightSelect.appendChild(option);
    });
    fontWeightContainer.appendChild(fontWeightSelect);
    fontStyleRow.appendChild(fontWeightContainer);
    
    // Font Style
    const fontStyleContainer = document.createElement('div');
    fontStyleContainer.style.cssText = 'flex: 1;';
    const fontStyleLabel = document.createElement('label');
    fontStyleLabel.textContent = 'Style:';
    fontStyleLabel.style.cssText = 'color: #ecf0f1; font-size: 11px; display: block; margin-bottom: 4px;';
    fontStyleContainer.appendChild(fontStyleLabel);
    const fontStyleSelect = document.createElement('select');
    fontStyleSelect.style.cssText = `
        width: 100%;
        padding: 6px 8px;
        background: #2d3748;
        border: 1px solid #4a5568;
        border-radius: 4px;
        color: #ecf0f1;
        font-size: 12px;
        outline: none;
        box-sizing: border-box;
    `;
    const fontStyles = ['normal', 'italic', 'oblique'];
    fontStyles.forEach(style => {
        const option = document.createElement('option');
        option.value = style;
        option.textContent = style.charAt(0).toUpperCase() + style.slice(1);
        if ((device.fontStyle || 'normal') === style) {
            option.selected = true;
        }
        fontStyleSelect.appendChild(option);
    });
    fontStyleContainer.appendChild(fontStyleSelect);
    fontStyleRow.appendChild(fontStyleContainer);
    
    fontSection.appendChild(fontStyleRow);
    
    // Label Color row
    const labelColorRow = document.createElement('div');
    labelColorRow.style.cssText = 'margin-top: 10px;';
    const labelColorLabel = document.createElement('label');
    labelColorLabel.textContent = 'Label Color:';
    labelColorLabel.style.cssText = 'color: #ecf0f1; font-size: 11px; display: block; margin-bottom: 6px;';
    labelColorRow.appendChild(labelColorLabel);
    
    const colorPalette = document.createElement('div');
    colorPalette.style.cssText = 'display: flex; gap: 4px; flex-wrap: wrap;';
    
    const labelColors = [
        { color: null, label: 'Auto' },
        { color: '#ffffff', label: 'White' },
        { color: '#1a1a2e', label: 'Black' },
        { color: '#e74c3c', label: 'Red' },
        { color: '#3498db', label: 'Blue' },
        { color: '#27ae60', label: 'Green' },
        { color: '#FF5E1F', label: 'Orange' },
        { color: '#9b59b6', label: 'Purple' }
    ];
    
    labelColors.forEach(({ color: c, label: l }) => {
        const swatch = document.createElement('button');
        const isAuto = c === null;
        const currentLabelColor = device.labelColor || null;
        const isSelected = currentLabelColor === c;
        
        swatch.title = l;
        swatch.style.cssText = `
            width: 24px; height: 24px; border-radius: 4px; cursor: pointer;
            border: 2px solid ${isSelected ? '#3498db' : 'rgba(255,255,255,0.2)'};
            background: ${isAuto ? 'linear-gradient(135deg, #fff 50%, #1a1a2e 50%)' : c};
            transition: all 0.15s;
            ${isSelected ? 'transform: scale(1.1); box-shadow: 0 2px 8px rgba(52, 152, 219, 0.4);' : ''}
        `;
        swatch.onclick = () => {
            device.labelColor = c;
            // Update all swatches
            colorPalette.querySelectorAll('button').forEach((sw, idx) => {
                const swColor = labelColors[idx].color;
                const nowSelected = device.labelColor === swColor;
                sw.style.border = `2px solid ${nowSelected ? '#3498db' : 'rgba(255,255,255,0.2)'}`;
                sw.style.transform = nowSelected ? 'scale(1.1)' : 'scale(1)';
                sw.style.boxShadow = nowSelected ? '0 2px 8px rgba(52, 152, 219, 0.4)' : 'none';
            });
            editor.draw();
        };
        colorPalette.appendChild(swatch);
    });
    
    labelColorRow.appendChild(colorPalette);
    fontSection.appendChild(labelColorRow);
    
    popup.appendChild(fontSection);
    
    // Apply on Enter
    input.onkeydown = (e) => {
        if (e.key === 'Enter') {
            applyRename(editor, device, input.value, {
                fontFamily: fontFamilySelect.value,
                fontSize: parseInt(fontSizeInput.value),
                fontWeight: fontWeightSelect.value,
                fontStyle: fontStyleSelect.value
            });
            hideRenamePopup();
        } else if (e.key === 'Escape') {
            hideRenamePopup();
        }
    };
    
    // Buttons container
    const btnContainer = document.createElement('div');
    btnContainer.style.cssText = 'display: flex; gap: 8px; margin-top: 10px; justify-content: flex-end;';
    
    // Cancel button
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancel';
    cancelBtn.style.cssText = `
        padding: 6px 12px; background: #4a5568; border: none;
        border-radius: 4px; color: #ecf0f1; cursor: pointer; font-size: 12px;
    `;
    cancelBtn.onclick = () => hideRenamePopup();
    btnContainer.appendChild(cancelBtn);
    
    // Apply button
    const applyBtn = document.createElement('button');
    applyBtn.textContent = 'Apply';
    applyBtn.style.cssText = `
        padding: 6px 12px; background: #3498db; border: none;
        border-radius: 4px; color: white; cursor: pointer; font-size: 12px;
    `;
    applyBtn.onclick = () => {
        applyRename(editor, device, input.value, {
            fontFamily: fontFamilySelect.value,
            fontSize: parseInt(fontSizeInput.value),
            fontWeight: fontWeightSelect.value,
            fontStyle: fontStyleSelect.value
        });
        hideRenamePopup();
    };
    btnContainer.appendChild(applyBtn);
    popup.appendChild(btnContainer);
    
    document.body.appendChild(popup);
    
    // Adjust position if popup goes off screen
    const popupRect = popup.getBoundingClientRect();
    if (popupRect.right > window.innerWidth) {
        popup.style.left = (window.innerWidth - popupRect.width - 20) + 'px';
    }
    if (popupRect.bottom > window.innerHeight) {
        popup.style.top = (window.innerHeight - popupRect.height - 20) + 'px';
    }
    
    // Focus input and select text
    setTimeout(() => {
        input.focus();
        input.select();
    }, 50);
}

/**
 * Apply rename and font settings to device
 * @param {TopologyEditor} editor - The editor instance
 * @param {object} device - The device object
 * @param {string} newLabel - New label text
 * @param {object} fontSettings - Font settings object
 */
function applyRename(editor, device, newLabel, fontSettings = null) {
    if (device && device.type === 'device') {
        if (editor.saveState) editor.saveState();
        device.label = newLabel.trim() || device.label;
        
        // Apply font settings if provided
        if (fontSettings) {
            device.fontFamily = fontSettings.fontFamily;
            device.labelSize = fontSettings.fontSize;
            device.fontSize = fontSettings.fontSize;
            device.fontWeight = fontSettings.fontWeight;
            device.fontStyle = fontSettings.fontStyle;
        }
        
        editor.draw();
    }
}

/**
 * Hide the rename popup
 */
function hideRenamePopup() {
    const popup = document.getElementById('rename-popup');
    if (popup) popup.remove();
}

// Export functions
window.showRenamePopup = showRenamePopup;
window.applyRename = applyRename;
window.hideRenamePopup = hideRenamePopup;

console.log('[topology-rename-popup.js] Device Rename Popup module loaded');
