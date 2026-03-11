// ============================================================================
// TOPOLOGY SHAPE SELECTION TOOLBAR MODULE
// ============================================================================
// Handles the floating shape selection toolbar with liquid glass styling.
// Extracted from topology.js to reduce main file size (~700 lines).
//
// Usage:
//   showShapeSelectionToolbar(editor, shape);
//   hideShapeSelectionToolbar(editor);
// ============================================================================

/**
 * Show color palette popup for shape fill/stroke
 * @param {TopologyEditor} editor - The editor instance
 * @param {string} type - 'fill' or 'stroke'
 * @param {object} shape - The shape object
 * @param {HTMLElement} toolbar - The toolbar element
 * @param {Array} colorPalette - Array of palette colors
 * @param {Array} recentColors - Array of recent colors
 * @param {Function} saveRecentColor - Function to save a recent color
 */
function _showShapeColorPalette(editor, type, shape, toolbar, colorPalette, recentColors, saveRecentColor) {
    // Close existing palette
    const existingPalette = document.getElementById('shape-color-palette-popup');
    if (existingPalette) { existingPalette.remove(); return; }
    
    const colorBtn = toolbar.querySelector(type === 'fill' ? '#shape-fill-color-btn' : '#shape-stroke-color-btn');
    if (!colorBtn) return;
    
    const btnRect = colorBtn.getBoundingClientRect();
    const currentColor = type === 'fill' ? (shape.fillColor || '#3498db') : (shape.strokeColor || '#2c3e50');
    
    const popup = document.createElement('div');
    popup.id = 'shape-color-palette-popup';
    popup.style.cssText = `
        position: fixed;
        left: ${btnRect.left}px;
        top: ${btnRect.bottom + 8}px;
        background: linear-gradient(145deg, rgba(30, 30, 40, 0.95), rgba(20, 20, 30, 0.98));
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        padding: 12px;
        min-width: 200px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(8px);
        z-index: 100010;
    `;
    
    // Title
    const title = document.createElement('div');
    title.style.cssText = 'color: rgba(255,255,255,0.9); font-size: 12px; font-weight: 600; margin-bottom: 10px; text-transform: capitalize;';
    title.textContent = `${type} Color`;
    popup.appendChild(title);
    
    // Recent colors section
    if (recentColors && recentColors.length > 0) {
        const recentLabel = document.createElement('div');
        recentLabel.textContent = 'Recent';
        recentLabel.style.cssText = 'color: #FF7A33; font-size: 10px; margin-bottom: 6px; font-weight: 600;';
        popup.appendChild(recentLabel);
        
        const recentContainer = document.createElement('div');
        recentContainer.style.cssText = 'display: flex; gap: 5px; margin-bottom: 10px; flex-wrap: wrap;';
        recentColors.slice(0, 8).forEach(color => {
            const swatch = document.createElement('div');
            const isActive = color.toLowerCase() === currentColor.toLowerCase();
            swatch.style.cssText = `
                width: 22px; height: 22px; border-radius: 4px;
                background: ${color}; cursor: pointer;
                border: 2px solid ${isActive ? '#fff' : 'rgba(255,255,255,0.2)'};
                transition: all 0.15s ease;
            `;
            swatch.onmouseenter = () => { swatch.style.transform = 'scale(1.15)'; };
            swatch.onmouseleave = () => { swatch.style.transform = 'scale(1)'; };
            swatch.onclick = (e) => {
                e.stopPropagation();
                _applyShapeColor(editor, type, shape, color, colorBtn, toolbar);
                saveRecentColor(color);
                popup.remove();
            };
            recentContainer.appendChild(swatch);
        });
        popup.appendChild(recentContainer);
    }
    
    // Main palette label
    const paletteLabel = document.createElement('div');
    paletteLabel.textContent = 'Palette';
    paletteLabel.style.cssText = 'color: rgba(255,255,255,0.6); font-size: 10px; margin-bottom: 6px;';
    popup.appendChild(paletteLabel);
    
    // Main palette grid
    const grid = document.createElement('div');
    grid.style.cssText = 'display: grid; grid-template-columns: repeat(6, 1fr); gap: 5px; margin-bottom: 10px;';
    colorPalette.forEach(color => {
        const swatch = document.createElement('div');
        const isActive = color.toLowerCase() === currentColor.toLowerCase();
        swatch.style.cssText = `
            width: 26px; height: 26px; border-radius: 5px;
            background: ${color}; cursor: pointer;
            border: 2px solid ${isActive ? '#fff' : 'rgba(255,255,255,0.15)'};
            box-shadow: ${isActive ? '0 0 8px rgba(255,255,255,0.4)' : 'inset 0 1px 2px rgba(0,0,0,0.3)'};
            transition: all 0.15s ease;
        `;
        swatch.onmouseenter = () => { swatch.style.transform = 'scale(1.12)'; swatch.style.borderColor = 'rgba(255,255,255,0.5)'; };
        swatch.onmouseleave = () => { swatch.style.transform = 'scale(1)'; swatch.style.borderColor = isActive ? '#fff' : 'rgba(255,255,255,0.15)'; };
        swatch.onclick = (e) => {
            e.stopPropagation();
            _applyShapeColor(editor, type, shape, color, colorBtn, toolbar);
            saveRecentColor(color);
            popup.remove();
        };
        grid.appendChild(swatch);
    });
    popup.appendChild(grid);
    
    // Custom color picker
    const customRow = document.createElement('div');
    customRow.style.cssText = 'display: flex; align-items: center; gap: 8px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;';
    customRow.innerHTML = `<span style="color: rgba(255,255,255,0.6); font-size: 10px;">Custom:</span>`;
    
    const customPicker = document.createElement('input');
    customPicker.type = 'color';
    customPicker.value = currentColor;
    customPicker.style.cssText = 'width: 32px; height: 24px; border: none; border-radius: 4px; cursor: pointer; background: transparent;';
    customPicker.oninput = () => {
        _applyShapeColor(editor, type, shape, customPicker.value, colorBtn, toolbar);
    };
    customPicker.onchange = () => {
        saveRecentColor(customPicker.value);
        popup.remove();
    };
    customRow.appendChild(customPicker);
    popup.appendChild(customRow);
    
    document.body.appendChild(popup);
    
    // Close on click outside
    const closeHandler = (e) => {
        if (!popup.contains(e.target) && e.target !== colorBtn) {
            popup.remove();
            document.removeEventListener('click', closeHandler);
        }
    };
    setTimeout(() => document.addEventListener('click', closeHandler), 100);
    
    // Keep on screen
    requestAnimationFrame(() => {
        const popupRect = popup.getBoundingClientRect();
        if (popupRect.right > window.innerWidth) popup.style.left = `${window.innerWidth - popupRect.width - 10}px`;
        if (popupRect.bottom > window.innerHeight) popup.style.top = `${btnRect.top - popupRect.height - 8}px`;
    });
}

/**
 * Apply color to shape and update UI
 * @param {TopologyEditor} editor - The editor instance
 * @param {string} type - 'fill' or 'stroke'
 * @param {object} shape - The shape object
 * @param {string} color - The color to apply
 * @param {HTMLElement} colorBtn - The color button element
 * @param {HTMLElement} toolbar - The toolbar element
 */
function _applyShapeColor(editor, type, shape, color, colorBtn, toolbar) {
    if (type === 'fill') {
        shape.fillColor = color;
        if (colorBtn) colorBtn.style.background = color;
        // Update slider fill color
        const fillBar = toolbar.querySelector('#shape-fill-opacity-fill');
        if (fillBar) fillBar.style.background = color;
    } else {
        shape.strokeColor = color;
        if (colorBtn) colorBtn.style.background = color;
        // Update slider fill color
        const strokeBar = toolbar.querySelector('#shape-stroke-width-fill');
        if (strokeBar) strokeBar.style.background = color;
    }
    editor.draw();
    if (editor.scheduleAutoSave) editor.scheduleAutoSave();
}

/**
 * Show the shape selection toolbar
 * @param {TopologyEditor} editor - The editor instance
 * @param {object} shape - The selected shape object
 */
function showShapeSelectionToolbar(editor, shape) {
    if (!shape || shape.type !== 'shape') return;
    
    // Hide other toolbars
    hideShapeSelectionToolbar(editor);
    if (editor.hideDeviceSelectionToolbar) editor.hideDeviceSelectionToolbar();
    if (editor.hideLinkSelectionToolbar) editor.hideLinkSelectionToolbar();
    if (editor.hideTextSelectionToolbar) editor.hideTextSelectionToolbar();
    
    // Calculate screen position of the shape
    const rect = editor.canvas.getBoundingClientRect();
    
    const centerScreenX = shape.x * editor.zoom + editor.panOffset.x + rect.left;
    const centerScreenY = shape.y * editor.zoom + editor.panOffset.y + rect.top;
    
    const bottomY = centerScreenY + ((shape.height / 2) * editor.zoom);
    
    // Always position toolbar below the shape
    const toolbarGap = 25;
    const toolbarX = centerScreenX;
    let toolbarY = bottomY + toolbarGap;
    
    // Create the toolbar container - Liquid Glass Style
    const toolbar = document.createElement('div');
    toolbar.id = 'shape-selection-toolbar';
    const isDarkMode = editor.darkMode;
    const glassBg = isDarkMode ? 'rgba(15, 15, 25, 0.25)' : 'rgba(255, 255, 255, 0.25)';
    const glassBorder = isDarkMode ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.08)';
    const glassShadow = isDarkMode 
        ? '0 4px 30px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.08)'
        : '0 4px 30px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.5)';
    toolbar.style.cssText = `
        position: fixed;
        left: ${toolbarX}px;
        top: ${toolbarY}px;
        transform: translateX(-50%);
        z-index: 99999;
        background: ${glassBg};
        border: 1px solid ${glassBorder};
        border-radius: 14px;
        padding: 8px 12px;
        box-shadow: ${glassShadow};
        backdrop-filter: blur(28px) saturate(200%) brightness(1.02);
        -webkit-backdrop-filter: blur(28px) saturate(200%) brightness(1.02);
        display: flex;
        flex-direction: column;
        gap: 8px;
        align-items: stretch;
        user-select: none;
        -webkit-user-select: none;
        opacity: 0;
        animation: shapeTbFadeIn 0.2s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        min-width: 180px;
        overflow: visible;
    `;
    
    // Add CSS animation
    const oldStyle = document.getElementById('shape-toolbar-styles');
    if (oldStyle) oldStyle.remove();
    
    const style = document.createElement('style');
    style.id = 'shape-toolbar-styles';
    const labelColor = isDarkMode ? 'rgba(255, 255, 255, 0.7)' : 'rgba(30, 30, 50, 0.75)';
    const inputBg = isDarkMode ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.05)';
    const inputBorder = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    const inputColor = isDarkMode ? '#fff' : '#1a1a2e';
    const inputFocusBg = isDarkMode ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.08)';
    const colorBorder = isDarkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.15)';
    const colorHoverBorder = isDarkMode ? 'rgba(255, 255, 255, 0.4)' : 'rgba(0, 0, 0, 0.3)';
    const btnBg = isDarkMode ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.05)';
    const btnBorder = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    const btnColor = isDarkMode ? 'rgba(255, 255, 255, 0.85)' : 'rgba(30, 30, 50, 0.9)';
    const btnHoverBg = isDarkMode ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.08)';
    const btnHoverBorder = isDarkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.15)';
    style.textContent = `
        @keyframes shapeTbFadeIn {
            from { opacity: 0; transform: translateX(-50%) translateY(8px); }
            to { opacity: 1; transform: translateX(-50%) translateY(0); }
        }
        .shape-toolbar-row {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 4px 0;
        }
        .shape-toolbar-label {
            font-size: 11px;
            color: ${labelColor};
            min-width: 50px;
            font-weight: 500;
        }
        .shape-toolbar-input {
            flex: 1;
            background: ${inputBg};
            border: 1px solid ${inputBorder};
            border-radius: 6px;
            padding: 4px 8px;
            color: ${inputColor};
            font-size: 11px;
            outline: none;
            transition: all 0.2s;
        }
        .shape-toolbar-input:focus {
            border-color: rgba(52, 152, 219, 0.6);
            background: ${inputFocusBg};
        }
        .shape-toolbar-color {
            width: 28px;
            height: 28px;
            border: 2px solid ${colorBorder};
            border-radius: 6px;
            cursor: pointer;
            padding: 0;
            transition: all 0.2s;
        }
        .shape-toolbar-color:hover {
            border-color: ${colorHoverBorder};
            transform: scale(1.1);
        }
        .shape-toolbar-checkbox {
            width: 16px;
            height: 16px;
            accent-color: #3498db;
            cursor: pointer;
        }
        .shape-toolbar-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 6px 12px;
            background: ${btnBg};
            border: 1px solid ${btnBorder};
            border-radius: 6px;
            color: ${btnColor};
            font-size: 11px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        .shape-toolbar-btn:hover {
            background: ${btnHoverBg};
            border-color: ${btnHoverBorder};
        }
        .shape-toolbar-btn.active {
            background: rgba(52, 152, 219, 0.3);
            border-color: rgba(52, 152, 219, 0.5);
        }
        .shape-toolbar-btn.destructive:hover {
            background: rgba(231, 76, 60, 0.3);
            border-color: rgba(231, 76, 60, 0.5);
        }
        .shape-toolbar-divider {
            height: 1px;
            background: ${isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)'};
            margin: 4px 0;
        }
    `;
    document.head.appendChild(style);
    
    // Build toolbar content
    const content = document.createElement('div');
    content.style.cssText = 'position: relative; z-index: 1;';
    
    // Title row
    const titleColor = isDarkMode ? 'rgba(255,255,255,0.9)' : 'rgba(30,30,50,0.95)';
    const titleBorderColor = isDarkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)';
    const titleRow = document.createElement('div');
    titleRow.className = 'shape-toolbar-row';
    titleRow.style.borderBottom = `1px solid ${titleBorderColor}`;
    titleRow.style.paddingBottom = '8px';
    titleRow.style.marginBottom = '4px';
    const shapeIcon = editor._createIconSvg ? editor._createIconSvg('shape', 14, 'rgba(52, 152, 219, 0.9)') : '■';
    const shapeLabel = shape.label || shape.shapeType.charAt(0).toUpperCase() + shape.shapeType.slice(1);
    titleRow.innerHTML = `
        <span style="font-size: 12px; font-weight: 600; color: ${titleColor};">
            ${shapeIcon} 
            ${shapeLabel}
        </span>
    `;
    content.appendChild(titleRow);
    
    // Load recent colors from app-wide storage
    const recentColorsKey = 'topology_recent_colors';
    let recentColors = [];
    try {
        const saved = localStorage.getItem(recentColorsKey);
        if (saved) recentColors = JSON.parse(saved);
    } catch (e) { /* ignore */ }
    
    const saveRecentColor = (color) => {
        recentColors = recentColors.filter(c => c.toLowerCase() !== color.toLowerCase());
        recentColors.unshift(color);
        recentColors = recentColors.slice(0, 12);
        try { localStorage.setItem(recentColorsKey, JSON.stringify(recentColors)); } catch(e) {}
    };
    
    // Color palette
    const colorPalette = [
        '#e74c3c', '#FF5E1F', '#f1c40f', '#2ecc71', '#1abc9c', '#3498db',
        '#9b59b6', '#34495e', '#95a5a6', '#ecf0f1', '#1e272e', '#ff6b81',
        '#c44569', '#574b90', '#303952', '#786fa6', '#f8a5c2', '#63cdda'
    ];
    
    // Helper to create styled slider with color fill
    const createStyledSlider = (id, min, max, value, color, label, suffix, onChange) => {
        const container = document.createElement('div');
        container.style.cssText = 'display: flex; align-items: center; gap: 8px; flex: 1;';
        
        const slider = document.createElement('input');
        slider.type = 'range';
        slider.id = id;
        slider.min = min;
        slider.max = max;
        slider.value = value;
        slider.style.cssText = `
            flex: 1; min-width: 80px; height: 6px;
            -webkit-appearance: none; appearance: none;
            background: linear-gradient(to right, ${color} 0%, ${color} ${((value - min) / (max - min)) * 100}%, rgba(0,0,0,0.3) ${((value - min) / (max - min)) * 100}%, rgba(0,0,0,0.3) 100%);
            border-radius: 3px; cursor: pointer; outline: none;
        `;
        
        // Add dynamic styling
        const styleId = `slider-style-${id}`;
        let styleEl = document.getElementById(styleId);
        if (!styleEl) {
            styleEl = document.createElement('style');
            styleEl.id = styleId;
            document.head.appendChild(styleEl);
        }
        styleEl.textContent = `
            #${id}::-webkit-slider-thumb {
                -webkit-appearance: none; width: 18px; height: 18px; border-radius: 50%;
                background: #fff; border: 3px solid ${color}; cursor: pointer;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            }
            #${id}::-moz-range-thumb {
                width: 18px; height: 18px; border-radius: 50%;
                background: #fff; border: 3px solid ${color}; cursor: pointer;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3); border: none;
            }
        `;
        
        const valLabel = document.createElement('span');
        valLabel.id = `${id}-val`;
        valLabel.style.cssText = 'font-size: 12px; color: rgba(255,255,255,0.9); min-width: 36px; text-align: right; font-weight: 600;';
        valLabel.textContent = `${value}${suffix}`;
        
        slider.oninput = () => {
            const pct = ((slider.value - min) / (max - min)) * 100;
            slider.style.background = `linear-gradient(to right, ${color} 0%, ${color} ${pct}%, rgba(0,0,0,0.3) ${pct}%, rgba(0,0,0,0.3) 100%)`;
            valLabel.textContent = `${slider.value}${suffix}`;
            onChange(parseInt(slider.value));
        };
        
        container.appendChild(slider);
        container.appendChild(valLabel);
        return container;
    };
    
    // Helper to create icon button with tooltip
    const createIconBtn = (iconId, tooltip, onClick, options = {}) => {
        const { isDestructive = false, isActive = false, color = null, autoClose = true } = options;
        const btn = document.createElement('button');
        btn.style.cssText = `
            width: 32px; height: 32px; border: none; border-radius: 6px;
            background: ${isActive ? 'rgba(52, 152, 219, 0.3)' : 'rgba(255,255,255,0.08)'};
            border: 1px solid ${isActive ? 'rgba(52, 152, 219, 0.5)' : 'rgba(255,255,255,0.1)'};
            cursor: pointer; display: flex; align-items: center; justify-content: center;
            transition: all 0.15s ease;
        `;
        const iconColor = isDestructive ? 'rgba(231, 76, 60, 0.9)' : (color || 'rgba(255,255,255,0.8)');
        btn.innerHTML = editor._createIconSvg ? editor._createIconSvg(iconId, 15, iconColor) : '●';
        btn.onmouseenter = () => {
            btn.style.background = isDestructive ? 'rgba(231, 76, 60, 0.25)' : 'rgba(255,255,255,0.15)';
            btn.style.transform = 'scale(1.1)';
            if (editor._showToolbarTooltip) editor._showToolbarTooltip(btn, tooltip);
        };
        btn.onmouseleave = () => {
            btn.style.background = isActive ? 'rgba(52, 152, 219, 0.3)' : 'rgba(255,255,255,0.08)';
            btn.style.transform = 'scale(1)';
            if (editor._hideToolbarTooltip) editor._hideToolbarTooltip();
        };
        btn.onmousedown = (e) => { e.stopPropagation(); e.preventDefault(); };
        btn.onclick = (e) => { 
            e.stopPropagation(); 
            if (autoClose) {
                hideShapeSelectionToolbar(editor);
            }
            onClick(); 
        };
        return btn;
    };
    
    // Fill section
    const fillSection = document.createElement('div');
    fillSection.className = 'shape-toolbar-row';
    fillSection.style.flexDirection = 'column';
    fillSection.style.alignItems = 'stretch';
    fillSection.style.gap = '6px';
    
    // Fill header with checkbox and current color
    const fillHeader = document.createElement('div');
    fillHeader.style.cssText = 'display: flex; align-items: center; gap: 8px;';
    fillHeader.innerHTML = `
        <input type="checkbox" id="shape-fill-enabled" class="shape-toolbar-checkbox" ${shape.fillEnabled !== false ? 'checked' : ''}>
        <label class="shape-toolbar-label" style="flex: 0;">Fill</label>
    `;
    
    // Current fill color swatch (clickable to open picker)
    const fillColorBtn = document.createElement('div');
    fillColorBtn.id = 'shape-fill-color-btn';
    fillColorBtn.style.cssText = `
        width: 24px; height: 24px; border-radius: 4px; cursor: pointer;
        background: ${shape.fillColor || '#3498db'};
        border: 2px solid rgba(255,255,255,0.3);
        transition: all 0.15s;
    `;
    fillColorBtn.onclick = (e) => { e.stopPropagation(); _showShapeColorPalette(editor, 'fill', shape, toolbar, colorPalette, recentColors, saveRecentColor); };
    fillHeader.appendChild(fillColorBtn);
    
    const fillOpacityVal = Math.round((shape.fillOpacity !== undefined ? shape.fillOpacity : 0.5) * 100);
    const fillSlider = createStyledSlider('shape-fill-opacity', 0, 100, fillOpacityVal, shape.fillColor || '#3498db', 'Opacity', '%', (val) => {
        shape.fillOpacity = val / 100;
        editor.draw();
        if (editor.scheduleAutoSave) editor.scheduleAutoSave();
    });
    fillHeader.appendChild(fillSlider);
    fillSection.appendChild(fillHeader);
    content.appendChild(fillSection);
    
    // Stroke section
    const strokeSection = document.createElement('div');
    strokeSection.className = 'shape-toolbar-row';
    strokeSection.style.flexDirection = 'column';
    strokeSection.style.alignItems = 'stretch';
    strokeSection.style.gap = '6px';
    
    const strokeHeader = document.createElement('div');
    strokeHeader.style.cssText = 'display: flex; align-items: center; gap: 8px;';
    strokeHeader.innerHTML = `
        <input type="checkbox" id="shape-stroke-enabled" class="shape-toolbar-checkbox" ${shape.strokeEnabled !== false ? 'checked' : ''}>
        <label class="shape-toolbar-label" style="flex: 0;">Border</label>
    `;
    
    const strokeColorBtn = document.createElement('div');
    strokeColorBtn.id = 'shape-stroke-color-btn';
    strokeColorBtn.style.cssText = `
        width: 24px; height: 24px; border-radius: 4px; cursor: pointer;
        background: ${shape.strokeColor || '#2c3e50'};
        border: 2px solid rgba(255,255,255,0.3);
        transition: all 0.15s;
    `;
    strokeColorBtn.onclick = (e) => { e.stopPropagation(); _showShapeColorPalette(editor, 'stroke', shape, toolbar, colorPalette, recentColors, saveRecentColor); };
    strokeHeader.appendChild(strokeColorBtn);
    
    const strokeWidthVal = shape.strokeWidth !== undefined ? shape.strokeWidth : 2;
    const strokeSlider = createStyledSlider('shape-stroke-width', 1, 12, strokeWidthVal, shape.strokeColor || '#FF5E1F', 'Width', 'px', (val) => {
        shape.strokeWidth = val;
        editor.draw();
        if (editor.scheduleAutoSave) editor.scheduleAutoSave();
    });
    strokeHeader.appendChild(strokeSlider);
    strokeSection.appendChild(strokeHeader);
    content.appendChild(strokeSection);
    
    // Divider
    const divider = document.createElement('div');
    divider.className = 'shape-toolbar-divider';
    content.appendChild(divider);
    
    // Action buttons row - icon only with tooltips
    const actionsRow = document.createElement('div');
    actionsRow.style.cssText = 'display: flex; justify-content: center; gap: 6px; padding-top: 4px;';
    
    // Lock button - toggle, keeps toolbar open
    actionsRow.appendChild(createIconBtn(
        shape.locked ? 'lock' : 'unlock',
        shape.locked ? 'Unlock Shape' : 'Lock Shape',
        () => {
            shape.locked = !shape.locked;
            editor.draw();
            if (editor.scheduleAutoSave) editor.scheduleAutoSave();
            // Refresh toolbar to show updated state
            setTimeout(() => showShapeSelectionToolbar(editor, shape), 50);
        },
        { isActive: shape.locked, autoClose: false }
    ));
    
    // Merge to Background button - toggle, keeps toolbar open
    actionsRow.appendChild(createIconBtn(
        'layers',
        shape.mergedToBackground ? 'Unmerge from Background' : 'Merge to Background (Grid Overlay)',
        () => {
            if (editor.saveState) editor.saveState();
            if (shape.mergedToBackground) {
                // Unmerge - restore to normal shape
                shape.mergedToBackground = false;
                shape.locked = false;
                shape.layer = editor.getDefaultLayerForType ? editor.getDefaultLayerForType('shape') : 0;
                if (editor.showToast) editor.showToast('Shape unmerged from background', 'info');
            } else {
                // Merge to background
                shape.mergedToBackground = true;
                shape.locked = true;  // Lock it automatically
                shape.layer = -1;  // Lowest possible layer
                if (editor.showToast) editor.showToast('Shape merged to background. Only borders are clickable.', 'success');
            }
            editor.draw();
            if (editor.scheduleAutoSave) editor.scheduleAutoSave();
            // Refresh toolbar to show updated state
            setTimeout(() => showShapeSelectionToolbar(editor, shape), 50);
        },
        { isActive: shape.mergedToBackground, color: shape.mergedToBackground ? 'rgba(46, 204, 113, 0.9)' : null, autoClose: false }
    ));
    
    // Copy Style button
    actionsRow.appendChild(createIconBtn('brush', 'Copy Style', () => {
        hideShapeSelectionToolbar(editor);
        if (editor.copyObjectStyle) editor.copyObjectStyle(shape);
        if (editor.showToast) editor.showToast('Style copied! Click another object to paste.', 'success');
    }));
    
    // Duplicate button
    actionsRow.appendChild(createIconBtn('copy', 'Duplicate Shape', () => {
        // Use proper duplication with offset and deep copy of all properties
        if (editor.duplicateObject) editor.duplicateObject(shape, false);
        // Show toolbar on the new shape after duplication
        if (editor.selectedObject && editor.selectedObject.type === 'shape') {
            setTimeout(() => showShapeSelectionToolbar(editor, editor.selectedObject), 100);
        }
    }));
    
    // Delete button
    actionsRow.appendChild(createIconBtn('trash', 'Delete Shape', () => {
        const idx = editor.objects.indexOf(shape);
        if (idx > -1) {
            if (editor.saveState) editor.saveState();
            editor.objects.splice(idx, 1);
            editor.selectedObject = null;
            hideShapeSelectionToolbar(editor);
            editor.draw();
            if (editor.scheduleAutoSave) editor.scheduleAutoSave();
        }
    }, { isDestructive: true }));
    
    content.appendChild(actionsRow);
    toolbar.appendChild(content);
    
    // Add event listeners
    document.body.appendChild(toolbar);
    
    // Fill/Stroke enable checkboxes
    const fillEnabled = toolbar.querySelector('#shape-fill-enabled');
    const strokeEnabled = toolbar.querySelector('#shape-stroke-enabled');
    
    fillEnabled.onchange = () => {
        shape.fillEnabled = fillEnabled.checked;
        editor.draw();
        if (editor.scheduleAutoSave) editor.scheduleAutoSave();
    };
    strokeEnabled.onchange = () => {
        shape.strokeEnabled = strokeEnabled.checked;
        editor.draw();
        if (editor.scheduleAutoSave) editor.scheduleAutoSave();
    };
    
    // Store reference
    editor._shapeSelectionToolbar = toolbar;
    editor._shapeSelectionToolbarTarget = shape;
    
    // Keep toolbar on screen — always below the shape
    requestAnimationFrame(() => {
        const toolbarRect = toolbar.getBoundingClientRect();
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        
        // Account for left toolbar width
        const leftToolbar = document.getElementById('left-toolbar');
        const leftOffset = leftToolbar && !leftToolbar.classList.contains('collapsed') ? 230 : 10;
        
        // Horizontal: keep on screen
        if (toolbarRect.right > vw - 10) {
            toolbar.style.left = `${vw - toolbarRect.width - 15}px`;
            toolbar.style.transform = 'translateX(0)';
        }
        if (toolbarRect.left < leftOffset) {
            toolbar.style.left = `${leftOffset}px`;
            toolbar.style.transform = 'translateX(0)';
        }
        
        // Vertical: clamp to viewport bottom, but stay below shape
        if (toolbarRect.bottom > vh - 10) {
            toolbar.style.top = `${Math.max(50, vh - toolbarRect.height - 10)}px`;
        }
    });
}

/**
 * Hide the shape selection toolbar
 * @param {TopologyEditor} editor - The editor instance
 */
function hideShapeSelectionToolbar(editor) {
    if (editor._shapeSelectionToolbar) {
        editor._shapeSelectionToolbar.remove();
        editor._shapeSelectionToolbar = null;
        editor._shapeSelectionToolbarTarget = null;
    }
    // Also close any open color palette
    const existingPalette = document.getElementById('shape-color-palette-popup');
    if (existingPalette) existingPalette.remove();
    // Hide tooltip if present
    if (editor._hideToolbarTooltip) editor._hideToolbarTooltip();
}

// Export functions
window.showShapeSelectionToolbar = showShapeSelectionToolbar;
window.hideShapeSelectionToolbar = hideShapeSelectionToolbar;

console.log('[topology-shape-toolbar.js] Shape selection toolbar module loaded');
