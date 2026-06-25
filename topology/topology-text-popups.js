// ============================================================================
// TOPOLOGY TEXT POPUPS MODULE
// ============================================================================
// Handles text color palette, font selector, and background color popups.
// Extracted from topology.js to reduce main file size (~620 lines).
//
// Usage:
//   showTextColorPalette(editor, textObj);
//   showTextFontSelector(editor, textObj);
//   showTextBgColorPalette(editor, textObj);
// ============================================================================

/**
 * Show a color palette popup for text objects
 * @param {TopologyEditor} editor - The editor instance
 * @param {object} textObj - The text object
 */
function showTextColorPalette(editor, textObj) {
    // Remove existing palette if any
    const existingPalette = document.getElementById('text-color-palette-popup');
    if (existingPalette) {
        existingPalette.remove();
        return; // Toggle off if clicking again
    }
    
    // Get toolbar position for placement
    const toolbar = document.getElementById('text-selection-toolbar');
    if (!toolbar) return;
    
    const toolbarRect = toolbar.getBoundingClientRect();
    
    // Load recent colors from localStorage
    const recentColorsKey = 'topology_recent_text_colors';
    let recentColors = [];
    try {
        const saved = localStorage.getItem(recentColorsKey);
        if (saved) recentColors = JSON.parse(saved);
    } catch (e) { /* ignore */ }
    
    // Helper to save recent color
    const saveRecentColor = (color) => {
        recentColors = recentColors.filter(c => c.toLowerCase() !== color.toLowerCase());
        recentColors.unshift(color);
        recentColors = recentColors.slice(0, 12);
        try {
            localStorage.setItem(recentColorsKey, JSON.stringify(recentColors));
        } catch (e) { /* ignore */ }
    };
    
    // Create the color palette popup
    const popup = document.createElement('div');
    popup.id = 'text-color-palette-popup';
    popup.style.cssText = `
        position: fixed;
        left: ${toolbarRect.left + toolbarRect.width / 2}px;
        top: ${toolbarRect.bottom + 8}px;
        transform: translateX(-50%);
        background: ${editor.darkMode ? 'rgba(30, 30, 35, 0.98)' : 'rgba(255, 255, 255, 0.98)'};
        border: 1px solid ${editor.darkMode ? '#555' : '#ccc'};
        border-radius: 10px;
        padding: 12px;
        z-index: 10001;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        backdrop-filter: blur(10px);
        min-width: 200px;
    `;
    
    // Title
    const title = document.createElement('div');
    title.textContent = 'Text Color';
    title.style.cssText = `
        color: ${editor.darkMode ? '#fff' : '#333'};
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 10px;
        text-align: center;
    `;
    popup.appendChild(title);
    
    // Recent colors section
    if (recentColors.length > 0) {
        const recentLabel = document.createElement('div');
        recentLabel.textContent = 'Recent';
        recentLabel.style.cssText = 'color: #FF7A33; font-size: 11px; margin-bottom: 5px; font-weight: 600;';
        popup.appendChild(recentLabel);
        
        const recentContainer = document.createElement('div');
        recentContainer.style.cssText = 'display: flex; gap: 4px; margin-bottom: 8px; flex-wrap: wrap;';
        
        recentColors.forEach(color => {
            const swatch = document.createElement('div');
            const isCurrentColor = textObj.color && textObj.color.toLowerCase() === color.toLowerCase();
            swatch.style.cssText = `
                width: 24px;
                height: 24px;
                border-radius: 4px;
                background: ${color};
                cursor: pointer;
                border: 2px solid ${isCurrentColor ? '#3498db' : (color.toLowerCase() === '#ffffff' ? '#ccc' : 'transparent')};
                transition: transform 0.1s;
            `;
            swatch.title = color;
            swatch.onmouseenter = () => swatch.style.transform = 'scale(1.15)';
            swatch.onmouseleave = () => swatch.style.transform = 'scale(1)';
            swatch.onclick = (e) => {
                e.stopPropagation();
                textObj.color = color;
                saveRecentColor(color);
                if (editor.saveState) editor.saveState();
                editor.draw();
            };
            recentContainer.appendChild(swatch);
        });
        popup.appendChild(recentContainer);
    }
    
    // Color palette grid
    const colors = [
        '#ffffff', '#000000', '#e74c3c', '#e91e63', '#9b59b6', '#673ab7',
        '#3498db', '#2196f3', '#00bcd4', '#009688', '#2ecc71', '#4caf50',
        '#8bc34a', '#cddc39', '#f39c12', '#ff9800', '#ff5722', '#795548',
        '#607d8b', '#9e9e9e', '#bdc3c7', '#ecf0f1', '#1abc9c', '#16a085'
    ];
    
    const paletteContainer = document.createElement('div');
    paletteContainer.style.cssText = 'display: grid; grid-template-columns: repeat(6, 1fr); gap: 4px; margin-bottom: 10px;';
    
    colors.forEach(color => {
        const swatch = document.createElement('div');
        const isCurrentColor = textObj.color && textObj.color.toLowerCase() === color.toLowerCase();
        swatch.style.cssText = `
            width: 28px;
            height: 28px;
            border-radius: 4px;
            background: ${color};
            cursor: pointer;
            border: 2px solid ${isCurrentColor ? '#3498db' : (color === '#ffffff' ? '#ccc' : 'transparent')};
            transition: transform 0.1s, border-color 0.15s;
        `;
        swatch.title = color;
        swatch.onmouseenter = () => {
            swatch.style.transform = 'scale(1.15)';
            swatch.style.borderColor = '#3498db';
        };
        swatch.onmouseleave = () => {
            swatch.style.transform = 'scale(1)';
            swatch.style.borderColor = isCurrentColor ? '#3498db' : (color === '#ffffff' ? '#ccc' : 'transparent');
        };
        swatch.onclick = (e) => {
            e.stopPropagation();
            textObj.color = color;
            saveRecentColor(color);
            if (editor.saveState) editor.saveState();
            editor.draw();
            paletteContainer.querySelectorAll('div').forEach(s => {
                const c = s.title;
                const isCurrent = c.toLowerCase() === color.toLowerCase();
                s.style.borderColor = isCurrent ? '#3498db' : (c === '#ffffff' ? '#ccc' : 'transparent');
            });
        };
        paletteContainer.appendChild(swatch);
    });
    popup.appendChild(paletteContainer);
    
    // Custom color picker
    const customRow = document.createElement('div');
    customRow.style.cssText = 'display: flex; align-items: center; gap: 8px; padding-top: 8px; border-top: 1px solid ' + (editor.darkMode ? '#444' : '#ddd') + ';';
    
    const customLabel = document.createElement('span');
    customLabel.textContent = 'Custom:';
    customLabel.style.cssText = 'color: #FF7A33; font-size: 11px; font-weight: 600;';
    customRow.appendChild(customLabel);
    
    const customInput = document.createElement('input');
    customInput.type = 'color';
    customInput.value = textObj.color || '#ffffff';
    customInput.style.cssText = 'width: 32px; height: 28px; border: none; border-radius: 4px; cursor: pointer; background: none;';
    customInput.oninput = (e) => {
        textObj.color = e.target.value;
        if (editor.saveState) editor.saveState();
        editor.draw();
    };
    customInput.onchange = (e) => {
        saveRecentColor(e.target.value);
    };
    customRow.appendChild(customInput);
    
    // Done button
    const doneBtn = document.createElement('button');
    doneBtn.textContent = 'Done';
    doneBtn.style.cssText = `
        margin-left: auto;
        padding: 5px 12px;
        background: #3498db;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 11px;
        font-weight: 500;
    `;
    doneBtn.onmouseenter = () => doneBtn.style.background = '#2980b9';
    doneBtn.onmouseleave = () => doneBtn.style.background = '#3498db';
    doneBtn.onclick = () => {
        popup.remove();
    };
    customRow.appendChild(doneBtn);
    
    popup.appendChild(customRow);
    
    popup.addEventListener('mousedown', (e) => e.stopPropagation());
    popup.addEventListener('click', (e) => e.stopPropagation());
    
    document.body.appendChild(popup);
    
    // Adjust if off-screen
    setTimeout(() => {
        const rect = popup.getBoundingClientRect();
        if (rect.right > window.innerWidth - 10) {
            popup.style.left = `${window.innerWidth - rect.width / 2 - 10}px`;
        }
        if (rect.bottom > window.innerHeight - 10) {
            popup.style.top = `${toolbarRect.top - rect.height - 8}px`;
        }
    }, 0);
}

/**
 * Show a font selector popup for text objects
 * @param {TopologyEditor} editor - The editor instance
 * @param {object} textObj - The text object
 */
function showTextFontSelector(editor, textObj) {
    // Remove existing popup if any
    const existingPopup = document.getElementById('text-font-selector-popup');
    if (existingPopup) {
        existingPopup.remove();
        return;
    }
    
    // Also remove other popups if open
    const colorPalette = document.getElementById('text-color-palette-popup');
    if (colorPalette) colorPalette.remove();
    const bgColorPalette = document.getElementById('text-bg-color-palette-popup');
    if (bgColorPalette) bgColorPalette.remove();
    
    // Get toolbar position for placement
    const toolbar = document.getElementById('text-selection-toolbar');
    if (!toolbar) return;
    
    const toolbarRect = toolbar.getBoundingClientRect();
    
    // Font options
    const fonts = [
        { name: 'Sans', family: 'Inter, sans-serif', preview: 'Aa' },
        { name: 'Brand', family: "'IBM Plex Sans', sans-serif", preview: 'Aa' },
        { name: 'Hand', family: "'Caveat', cursive", preview: 'Aa' },
        { name: 'Mono', family: "'IBM Plex Mono', monospace", preview: 'Aa' },
        { name: 'Serif', family: 'Georgia, serif', preview: 'Aa' },
        { name: 'Sketch', family: "'Comic Neue', cursive", preview: 'Aa' },
        { name: 'System', family: '-apple-system, BlinkMacSystemFont, sans-serif', preview: 'Aa' },
        { name: 'Classic', family: 'Arial, sans-serif', preview: 'Aa' }
    ];
    
    // Create the font selector popup
    const popup = document.createElement('div');
    popup.id = 'text-font-selector-popup';
    popup.style.cssText = `
        position: fixed;
        left: ${toolbarRect.left + toolbarRect.width / 2}px;
        top: ${toolbarRect.bottom + 8}px;
        transform: translateX(-50%);
        background: ${editor.darkMode ? 'rgba(30, 30, 35, 0.98)' : 'rgba(255, 255, 255, 0.98)'};
        border: 1px solid ${editor.darkMode ? '#555' : '#ccc'};
        border-radius: 10px;
        padding: 12px;
        z-index: 10001;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        backdrop-filter: blur(10px);
        min-width: 180px;
    `;
    
    // Title
    const title = document.createElement('div');
    title.textContent = 'Font Family';
    title.style.cssText = `
        color: ${editor.darkMode ? '#fff' : '#333'};
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 10px;
        text-align: center;
    `;
    popup.appendChild(title);
    
    // Font grid
    const fontGrid = document.createElement('div');
    fontGrid.style.cssText = 'display: grid; grid-template-columns: 1fr 1fr; gap: 6px;';
    
    const currentFont = textObj.fontFamily || editor.defaultFontFamily || 'Inter, sans-serif';
    
    fonts.forEach(font => {
        const isActive = currentFont.includes(font.family.split(',')[0].replace(/'/g, ''));
        
        const btn = document.createElement('button');
        btn.style.cssText = `
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 2px;
            padding: 8px 4px;
            background: ${isActive 
                ? 'linear-gradient(135deg, #FF5E1F, #CC4A16)' 
                : (editor.darkMode ? '#2a2a30' : '#f5f5f5')};
            border: 1px solid ${isActive ? '#FF5E1F' : (editor.darkMode ? '#444' : '#ddd')};
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.15s ease;
            min-height: 48px;
        `;
        
        // Font preview
        const preview = document.createElement('span');
        preview.textContent = font.preview;
        preview.style.cssText = `
            font-family: ${font.family};
            font-size: 16px;
            color: ${isActive ? '#fff' : (editor.darkMode ? '#fff' : '#333')};
        `;
        btn.appendChild(preview);
        
        // Font label
        const label = document.createElement('span');
        label.textContent = font.name;
        label.style.cssText = `
            font-size: 9px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: ${isActive ? 'rgba(255,255,255,0.9)' : (editor.darkMode ? '#888' : '#666')};
            font-family: Inter, sans-serif;
        `;
        btn.appendChild(label);
        
        btn.onmouseenter = () => {
            if (!isActive) {
                btn.style.background = editor.darkMode ? '#3a3a40' : '#e8e8e8';
                btn.style.borderColor = '#0066FA';
                btn.style.transform = 'translateY(-1px)';
            }
        };
        btn.onmouseleave = () => {
            if (!isActive) {
                btn.style.background = editor.darkMode ? '#2a2a30' : '#f5f5f5';
                btn.style.borderColor = editor.darkMode ? '#444' : '#ddd';
                btn.style.transform = 'none';
            }
        };
        btn.onclick = (e) => {
            e.stopPropagation();
            textObj.fontFamily = font.family;
            if (editor.saveState) editor.saveState();
            editor.draw();
            popup.remove();
            // Refresh toolbar to show updated state
            setTimeout(() => {
                if (editor.showTextSelectionToolbar) editor.showTextSelectionToolbar(textObj);
            }, 50);
        };
        
        fontGrid.appendChild(btn);
    });
    
    popup.appendChild(fontGrid);
    
    // Close when clicking outside
    const closeHandler = (e) => {
        if (!popup.contains(e.target)) {
            popup.remove();
            document.removeEventListener('mousedown', closeHandler);
        }
    };
    setTimeout(() => document.addEventListener('mousedown', closeHandler), 0);
    
    document.body.appendChild(popup);
    
    // Adjust position if offscreen
    setTimeout(() => {
        const rect = popup.getBoundingClientRect();
        if (rect.right > window.innerWidth - 10) {
            popup.style.left = `${window.innerWidth - rect.width / 2 - 10}px`;
        }
        if (rect.bottom > window.innerHeight - 10) {
            popup.style.top = `${toolbarRect.top - rect.height - 8}px`;
        }
    }, 0);
}

/**
 * Show background color palette for text objects
 * @param {TopologyEditor} editor - The editor instance
 * @param {object} textObj - The text object
 */
function showTextBgColorPalette(editor, textObj) {
    // Remove existing palette if any
    const existingPalette = document.getElementById('text-bg-color-palette-popup');
    if (existingPalette) {
        existingPalette.remove();
        return;
    }
    
    // Also remove text color palette if open
    const textColorPalette = document.getElementById('text-color-palette-popup');
    if (textColorPalette) textColorPalette.remove();
    
    const toolbar = editor._textSelectionToolbar;
    if (!toolbar) return;
    
    const toolbarRect = toolbar.getBoundingClientRect();
    
    // Load recent BG colors from localStorage
    const recentColorsKey = 'topology_recent_bg_colors';
    let recentColors = [];
    try {
        const saved = localStorage.getItem(recentColorsKey);
        if (saved) recentColors = JSON.parse(saved);
    } catch (e) { /* ignore */ }
    
    // Helper to save recent color
    const saveRecentColor = (color) => {
        recentColors = recentColors.filter(c => c.toLowerCase() !== color.toLowerCase());
        recentColors.unshift(color);
        recentColors = recentColors.slice(0, 12);
        try {
            localStorage.setItem(recentColorsKey, JSON.stringify(recentColors));
        } catch (e) { /* ignore */ }
    };
    
    // Create palette popup
    const popup = document.createElement('div');
    popup.id = 'text-bg-color-palette-popup';
    popup.style.cssText = `
        position: fixed;
        top: ${toolbarRect.bottom + 8}px;
        left: ${toolbarRect.left + toolbarRect.width / 2}px;
        transform: translateX(-50%);
        z-index: 100000;
        background: ${editor.darkMode ? 'rgba(35, 35, 40, 0.98)' : 'rgba(250, 250, 250, 0.98)'};
        border: 1px solid ${editor.darkMode ? '#555' : '#ccc'};
        border-radius: 8px;
        padding: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        min-width: 220px;
    `;
    
    // Title
    const title = document.createElement('div');
    title.textContent = 'Background Color';
    title.style.cssText = `
        color: ${editor.darkMode ? '#fff' : '#333'};
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 10px;
        text-align: center;
    `;
    popup.appendChild(title);
    
    // Recent colors section
    if (recentColors.length > 0) {
        const recentLabel = document.createElement('div');
        recentLabel.textContent = 'Recent';
        recentLabel.style.cssText = 'color: #FF7A33; font-size: 11px; margin-bottom: 5px; font-weight: 600;';
        popup.appendChild(recentLabel);
        
        const recentContainer = document.createElement('div');
        recentContainer.style.cssText = 'display: flex; gap: 4px; margin-bottom: 8px; flex-wrap: wrap;';
        
        recentColors.forEach(color => {
            const swatch = document.createElement('div');
            const isTransparent = color === 'rgba(0,0,0,0)';
            const currentBgColor = textObj.bgColor || 'rgba(30, 30, 30, 0.9)';
            const isSelected = color === currentBgColor;
            swatch.style.cssText = `
                width: 24px;
                height: 24px;
                border-radius: 4px;
                background: ${isTransparent ? 'repeating-conic-gradient(#ccc 0% 25%, #fff 0% 50%) 50% / 8px 8px' : color};
                cursor: pointer;
                border: 2px solid ${isSelected ? '#3498db' : 'transparent'};
                transition: transform 0.1s;
            `;
            swatch.title = isTransparent ? 'Transparent' : color;
            swatch.onmouseenter = () => swatch.style.transform = 'scale(1.15)';
            swatch.onmouseleave = () => swatch.style.transform = 'scale(1)';
            swatch.onclick = (e) => {
                e.stopPropagation();
                textObj.bgColor = color;
                saveRecentColor(color);
                if (editor.saveState) editor.saveState();
                editor.draw();
            };
            recentContainer.appendChild(swatch);
        });
        popup.appendChild(recentContainer);
    }
    
    // Color palette
    const bgColors = [
        '#1a1a2e', '#16213e', '#0f3460', '#533483', '#4a0072', '#3d0066',
        '#2c3e50', '#34495e', '#7f8c8d', '#95a5a6', '#bdc3c7', '#ecf0f1',
        '#27ae60', '#2ecc71', '#1abc9c', '#16a085', '#3498db', '#2980b9',
        '#e74c3c', '#c0392b', '#CC4A16', '#FF5E1F', '#f39c12', '#f1c40f',
        '#9b59b6', '#8e44ad', '#e91e63', '#ad1457', '#880e4f', '#4a148c',
        'rgba(0,0,0,0)', '#ffffff', '#000000', '#333333', '#666666', '#999999'
    ];
    
    const paletteContainer = document.createElement('div');
    paletteContainer.style.cssText = 'display: grid; grid-template-columns: repeat(6, 1fr); gap: 4px; margin-bottom: 10px;';
    
    const currentBgColor = textObj.bgColor || 'rgba(30, 30, 30, 0.9)';
    
    bgColors.forEach(color => {
        const swatch = document.createElement('div');
        const isTransparent = color === 'rgba(0,0,0,0)';
        const isSelected = color === currentBgColor;
        swatch.style.cssText = `
            width: 28px;
            height: 28px;
            border-radius: 4px;
            cursor: pointer;
            border: ${isSelected ? '2px solid #3498db' : '1px solid ' + (editor.darkMode ? '#555' : '#ccc')};
            background: ${isTransparent ? 'repeating-conic-gradient(#ccc 0% 25%, #fff 0% 50%) 50% / 8px 8px' : color};
            transition: transform 0.1s, border-color 0.1s;
            position: relative;
        `;
        if (isTransparent) {
            swatch.title = 'Transparent';
        }
        swatch.onmouseenter = () => {
            swatch.style.transform = 'scale(1.1)';
            swatch.style.borderColor = '#3498db';
        };
        swatch.onmouseleave = () => {
            swatch.style.transform = 'scale(1)';
            swatch.style.borderColor = isSelected ? '#3498db' : (editor.darkMode ? '#555' : '#ccc');
        };
        swatch.onclick = () => {
            textObj.bgColor = color;
            saveRecentColor(color);
            if (editor.saveState) editor.saveState();
            editor.draw();
            paletteContainer.querySelectorAll('div').forEach(s => {
                s.style.borderColor = editor.darkMode ? '#555' : '#ccc';
                s.style.borderWidth = '1px';
            });
            swatch.style.borderColor = '#3498db';
            swatch.style.borderWidth = '2px';
        };
        paletteContainer.appendChild(swatch);
    });
    popup.appendChild(paletteContainer);
    
    // Custom color picker
    const customRow = document.createElement('div');
    customRow.style.cssText = 'display: flex; align-items: center; gap: 8px; padding-top: 8px; border-top: 1px solid ' + (editor.darkMode ? '#444' : '#ddd') + ';';
    
    const customLabel = document.createElement('span');
    customLabel.textContent = 'Custom:';
    customLabel.style.cssText = 'color: #FF7A33; font-size: 11px; font-weight: 600;';
    customRow.appendChild(customLabel);
    
    const customInput = document.createElement('input');
    customInput.type = 'color';
    let hexValue = currentBgColor;
    if (currentBgColor.startsWith('rgba') || currentBgColor.startsWith('rgb')) {
        hexValue = '#1e1e1e';
    }
    customInput.value = hexValue;
    customInput.style.cssText = 'width: 32px; height: 28px; border: none; border-radius: 4px; cursor: pointer; background: none;';
    customInput.oninput = (e) => {
        textObj.bgColor = e.target.value;
        if (editor.saveState) editor.saveState();
        editor.draw();
    };
    customInput.onchange = (e) => {
        saveRecentColor(e.target.value);
    };
    customRow.appendChild(customInput);
    
    // Done button
    const doneBtn = document.createElement('button');
    doneBtn.textContent = 'Done';
    doneBtn.style.cssText = `
        margin-left: auto;
        padding: 5px 12px;
        background: #3498db;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 11px;
        font-weight: 500;
    `;
    doneBtn.onmouseenter = () => doneBtn.style.background = '#2980b9';
    doneBtn.onmouseleave = () => doneBtn.style.background = '#3498db';
    doneBtn.onclick = () => {
        popup.remove();
    };
    customRow.appendChild(doneBtn);
    
    popup.appendChild(customRow);
    
    popup.addEventListener('mousedown', (e) => e.stopPropagation());
    popup.addEventListener('click', (e) => e.stopPropagation());
    
    document.body.appendChild(popup);
    
    // Adjust if off-screen
    setTimeout(() => {
        const rect = popup.getBoundingClientRect();
        if (rect.right > window.innerWidth - 10) {
            popup.style.left = `${window.innerWidth - rect.width / 2 - 10}px`;
        }
        if (rect.bottom > window.innerHeight - 10) {
            popup.style.top = `${toolbarRect.top - rect.height - 8}px`;
        }
    }, 0);
}

/**
 * Show a font-size selector popup for text objects (2026-05-12).
 *
 * Closes a long-standing usability gap: the floating text-selection
 * toolbar previously only exposed font FAMILY, leaving font SIZE
 * reachable only via the left-sidebar "Default Text" panel or the
 * legacy Edit Text Properties modal. With this popover, changing size
 * is one click from a selected text box.
 *
 * Behaviour:
 *   * Preset buttons S / M / L / XL / XXL (10 / 14 / 18 / 24 / 32 px)
 *     plus a custom range slider 8-72 px.
 *   * Writes through `applyFontToSelectedText(null, size)` so the
 *     change is undoable, autosaved, and applied to every selected
 *     text object (single + multi-select).
 *   * Containment guard: when `text._heightLocked` is true and the
 *     new font size would clip ALL wrapped lines, expand text.height
 *     just enough to fit the wrapped content. The user keeps their
 *     manual height where possible, but never ends up with a frame
 *     that hides the typed content.
 *
 * @param {TopologyEditor} editor - The editor instance
 * @param {object} textObj - The text object
 */
function showTextSizeSelector(editor, textObj) {
    const existing = document.getElementById('text-size-selector-popup');
    if (existing) {
        existing.remove();
        return;
    }

    // Mutually-exclusive with sibling text popups.
    const colorPalette = document.getElementById('text-color-palette-popup');
    if (colorPalette) colorPalette.remove();
    const bgColorPalette = document.getElementById('text-bg-color-palette-popup');
    if (bgColorPalette) bgColorPalette.remove();
    const fontSelector = document.getElementById('text-font-selector-popup');
    if (fontSelector) fontSelector.remove();

    const toolbar = document.getElementById('text-selection-toolbar');
    if (!toolbar) return;
    const toolbarRect = toolbar.getBoundingClientRect();

    const presets = [
        { label: 'S',   size: 10 },
        { label: 'M',   size: 14 },
        { label: 'L',   size: 18 },
        { label: 'XL',  size: 24 },
        { label: 'XXL', size: 32 }
    ];

    const isDark = editor.darkMode;
    const popup = document.createElement('div');
    popup.id = 'text-size-selector-popup';
    popup.style.cssText = `
        position: fixed;
        left: ${toolbarRect.left + toolbarRect.width / 2}px;
        top: ${toolbarRect.bottom + 8}px;
        transform: translateX(-50%);
        background: ${isDark ? 'rgba(30, 30, 35, 0.98)' : 'rgba(255, 255, 255, 0.98)'};
        border: 1px solid ${isDark ? '#555' : '#ccc'};
        border-radius: 10px;
        padding: 12px;
        z-index: 10001;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        backdrop-filter: blur(10px);
        min-width: 220px;
    `;

    const title = document.createElement('div');
    title.textContent = 'Text Size';
    title.style.cssText = `
        color: ${isDark ? '#fff' : '#333'};
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 10px;
        text-align: center;
    `;
    popup.appendChild(title);

    const currentSize = parseInt(textObj.fontSize) || 14;

    /**
     * Containment helper: drawText computes per-line height from fontSize,
     * so a bigger font in a height-locked manual-width box can clip ALL
     * lines if the user previously dragged the bottom edge tight. This
     * mirrors the wrapping math in topology-canvas-drawing.js drawText
     * to expand the locked height JUST ENOUGH to keep the wrapped
     * content visible. Auto-grow boxes (no _heightLocked) need no help
     * -- their height re-derives from wrapped lines on the next paint.
     */
    const ensureHeightFitsAfterFontChange = (newSize) => {
        if (!textObj || textObj._heightLocked !== true) return;
        if (!Number.isFinite(textObj.height) || !Number.isFinite(textObj.width)) return;
        if (!editor.ctx) return;
        const fontFamily = textObj.fontFamily || editor.defaultFontFamily || 'Inter, sans-serif';
        const fontWeight = textObj.fontWeight || 'normal';
        const fontStyle  = textObj.fontStyle  || 'normal';
        const lineHeight = newSize * 1.3;
        editor.ctx.save();
        editor.ctx.font = `${fontStyle} ${fontWeight} ${newSize}px ${fontFamily}`;
        const Drawer = window.CanvasDrawing;
        const textContent = textObj.text == null ? 'Text' : String(textObj.text);
        let wrapped;
        if (Drawer && typeof Drawer._wrapTextLinesToWidth === 'function') {
            wrapped = Drawer._wrapTextLinesToWidth(editor.ctx, textContent, textObj.width);
        } else {
            wrapped = textContent.split('\n');
        }
        editor.ctx.restore();
        const requiredH = Math.max(20, wrapped.length * lineHeight);
        if (requiredH > textObj.height) {
            textObj.height = requiredH;
        }
    };

    const applySize = (size) => {
        const numeric = parseInt(size);
        if (!numeric || numeric < 4 || numeric > 200) return;
        ensureHeightFitsAfterFontChange(numeric);
        if (typeof editor.applyFontToSelectedText === 'function') {
            editor.applyFontToSelectedText(null, numeric);
        } else {
            // Defensive: write directly + redraw if the helper is absent.
            if (editor.saveState) editor.saveState();
            textObj.fontSize = numeric;
            if (editor.requestDraw) editor.requestDraw();
            else if (editor.draw) editor.draw();
        }
        if (editor._textSelectionToolbar && editor.updateTextSelectionToolbarPosition) {
            editor.updateTextSelectionToolbarPosition();
        }
    };

    // Preset row
    const presetGrid = document.createElement('div');
    presetGrid.style.cssText = 'display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; margin-bottom: 12px;';
    presets.forEach(p => {
        const isActive = currentSize === p.size;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = p.label;
        btn.title = `${p.size}px`;
        btn.style.cssText = `
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 8px 4px;
            min-height: 36px;
            background: ${isActive
                ? 'linear-gradient(135deg, #FF5E1F, #CC4A16)'
                : (isDark ? '#2a2a30' : '#f5f5f5')};
            border: 1px solid ${isActive ? '#FF5E1F' : (isDark ? '#444' : '#ddd')};
            border-radius: 6px;
            color: ${isActive ? '#fff' : (isDark ? '#fff' : '#333')};
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s ease;
        `;
        btn.onmouseenter = () => {
            if (!isActive) {
                btn.style.background = isDark ? '#3a3a40' : '#e8e8e8';
                btn.style.borderColor = '#0066FA';
                btn.style.transform = 'translateY(-1px)';
            }
        };
        btn.onmouseleave = () => {
            if (!isActive) {
                btn.style.background = isDark ? '#2a2a30' : '#f5f5f5';
                btn.style.borderColor = isDark ? '#444' : '#ddd';
                btn.style.transform = 'none';
            }
        };
        btn.onmousedown = (ev) => { ev.stopPropagation(); ev.preventDefault(); };
        btn.onclick = (ev) => {
            ev.stopPropagation();
            applySize(p.size);
            popup.remove();
            document.removeEventListener('mousedown', closeHandler);
        };
        presetGrid.appendChild(btn);
    });
    popup.appendChild(presetGrid);

    // Custom slider row
    const sliderRow = document.createElement('div');
    sliderRow.style.cssText = 'display: flex; flex-direction: column; gap: 6px;';

    const sliderLabel = document.createElement('div');
    sliderLabel.style.cssText = `display: flex; justify-content: space-between; align-items: center; color: ${isDark ? '#bbb' : '#555'}; font-size: 11px; font-weight: 500;`;
    const sliderTitle = document.createElement('span');
    sliderTitle.textContent = 'Custom';
    const sliderValue = document.createElement('span');
    sliderValue.textContent = currentSize + 'px';
    sliderValue.style.cssText = `font-family: monospace; color: ${isDark ? '#fff' : '#222'}; padding: 1px 6px; border: 1px solid ${isDark ? '#444' : '#ccc'}; border-radius: 4px; background: ${isDark ? '#2a2a30' : '#fafafa'};`;
    sliderLabel.appendChild(sliderTitle);
    sliderLabel.appendChild(sliderValue);
    sliderRow.appendChild(sliderLabel);

    const slider = document.createElement('input');
    slider.type = 'range';
    slider.min = '8';
    slider.max = '72';
    slider.step = '1';
    slider.value = currentSize;
    slider.style.cssText = 'width: 100%; cursor: pointer;';
    slider.oninput = (ev) => {
        const val = parseInt(ev.target.value) || currentSize;
        sliderValue.textContent = val + 'px';
        applySize(val);
    };
    slider.onmousedown = (ev) => { ev.stopPropagation(); };
    sliderRow.appendChild(slider);
    popup.appendChild(sliderRow);

    const closeHandler = (ev) => {
        if (!popup.contains(ev.target)) {
            popup.remove();
            document.removeEventListener('mousedown', closeHandler);
        }
    };
    setTimeout(() => document.addEventListener('mousedown', closeHandler), 0);

    document.body.appendChild(popup);

    setTimeout(() => {
        const rect = popup.getBoundingClientRect();
        if (rect.right > window.innerWidth - 10) {
            popup.style.left = `${window.innerWidth - rect.width / 2 - 10}px`;
        }
        if (rect.bottom > window.innerHeight - 10) {
            popup.style.top = `${toolbarRect.top - rect.height - 8}px`;
        }
    }, 0);
}

// Export functions
window.showTextColorPalette = showTextColorPalette;
window.showTextFontSelector = showTextFontSelector;
window.showTextSizeSelector = showTextSizeSelector;
window.showTextBgColorPalette = showTextBgColorPalette;

console.log('[topology-text-popups.js] Text popups module loaded');
