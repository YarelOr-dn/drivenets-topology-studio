/**
 * topology-color-popups.js - Color Palette Popup UI Components
 * 
 * Extracted from topology.js for modular architecture.
 * Contains color selection popup dialogs.
 * 
 * @version 1.0.0
 * @date 2026-02-04
 */

'use strict';

window.ColorPopups = {

    // Standard color palette
    standardColors: [
        '#e74c3c', '#FF5E1F', '#f1c40f', '#2ecc71', '#1abc9c', '#3498db',
        '#9b59b6', '#e91e63', '#00bcd4', '#ff5722', '#795548', '#607d8b',
        '#3498db', '#2980b9', '#8e44ad', '#16a085', '#27ae60', '#34495e',
        '#ffffff', '#ecf0f1', '#bdc3c7', '#95a5a6', '#7f8c8d', '#000000'
    ],

    // Compact color palette (for toolbar popups)
    compactColors: [
        '#e74c3c', '#FF5E1F', '#f1c40f', '#2ecc71', '#1abc9c',
        '#3498db', '#9b59b6', '#34495e', '#ffffff', '#000000'
    ],

    /**
     * Show color palette popup from context menu
     * @param {Object} editor - TopologyEditor instance
     * @param {Object} obj - The object to color
     * @param {string} objType - Object type ('link', 'device', 'text')
     */
    showColorPalettePopup(editor, obj, objType) {
        // Remove any existing color palette popup
        const existingPopup = document.getElementById('color-palette-popup');
        if (existingPopup) existingPopup.remove();
        
        // Temporarily disable link highlight to see actual color
        if (objType === 'link') {
            editor._colorEditingLink = obj;
            editor.draw();
        }
        
        // Calculate position - try context menu first, then text toolbar, then center screen
        let leftPos, topPos;
        const contextMenu = document.getElementById('context-menu');
        const textToolbar = document.getElementById('text-selection-toolbar');
        let menuRect = null;
        
        if (contextMenu && contextMenu.style.display !== 'none') {
            menuRect = contextMenu.getBoundingClientRect();
            leftPos = menuRect.right + 5;
            topPos = menuRect.top;
        } else if (textToolbar) {
            const toolbarRect = textToolbar.getBoundingClientRect();
            leftPos = toolbarRect.left;
            topPos = toolbarRect.bottom + 10;
        } else {
            const rect = editor.canvas.getBoundingClientRect();
            const screenX = obj.x * editor.zoom + editor.panOffset.x + rect.left;
            const screenY = obj.y * editor.zoom + editor.panOffset.y + rect.top;
            leftPos = screenX;
            topPos = screenY + 50;
        }
        
        // Create color palette popup with liquid glass aesthetic
        const popup = document.createElement('div');
        popup.id = 'color-palette-popup';
        popup.style.cssText = `
            position: fixed;
            left: ${leftPos}px;
            top: ${topPos}px;
            background: linear-gradient(135deg, 
                rgba(255, 255, 255, 0.15) 0%, 
                rgba(255, 255, 255, 0.08) 50%, 
                rgba(255, 255, 255, 0.05) 100%);
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 16px;
            padding: 14px;
            z-index: 10002;
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.3),
                0 0 0 1px rgba(255, 255, 255, 0.1) inset,
                0 2px 4px rgba(255, 255, 255, 0.1) inset;
            backdrop-filter: blur(24px) saturate(180%);
            -webkit-backdrop-filter: blur(24px) saturate(180%);
            min-width: 190px;
        `;
        
        // Title with liquid glass style
        const title = document.createElement('div');
        title.innerHTML = `${appIcon('palette')} Quick Colors`;
        title.style.cssText = 'color: rgba(255, 255, 255, 0.9); font-size: 13px; font-weight: 600; margin-bottom: 12px; text-align: center; text-shadow: 0 1px 2px rgba(0,0,0,0.3);';
        popup.appendChild(title);
        
        // Recent colors section
        if (editor.recentColors && editor.recentColors.length > 0) {
            const recentLabel = document.createElement('div');
            recentLabel.textContent = '🕐 Recent';
            recentLabel.style.cssText = 'color: #FF7A33; font-size: 11px; margin-bottom: 6px; font-weight: 600; text-shadow: 0 1px 2px rgba(0,0,0,0.3);';
            popup.appendChild(recentLabel);
            
            const recentContainer = document.createElement('div');
            recentContainer.style.cssText = 'display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap;';
            
            editor.recentColors.forEach(color => {
                const swatch = this._createSwatch(color, 32, () => {
                    editor.applyColorToObject(obj, color);
                });
                recentContainer.appendChild(swatch);
            });
            popup.appendChild(recentContainer);
        }
        
        // Color palette
        const paletteLabel = document.createElement('div');
        paletteLabel.innerHTML = `${appIcon('palette')} Palette`;
        paletteLabel.style.cssText = 'color: #FF7A33; font-size: 11px; margin-bottom: 6px; font-weight: 600; text-shadow: 0 1px 2px rgba(0,0,0,0.3);';
        popup.appendChild(paletteLabel);
        
        const paletteContainer = document.createElement('div');
        paletteContainer.style.cssText = 'display: grid; grid-template-columns: repeat(6, 1fr); gap: 6px; margin-bottom: 12px;';
        
        this.standardColors.forEach(color => {
            const swatch = this._createSwatch(color, 28, () => {
                editor.applyColorToObject(obj, color);
            });
            paletteContainer.appendChild(swatch);
        });
        popup.appendChild(paletteContainer);
        
        // Custom color picker with liquid glass style
        const customContainer = document.createElement('div');
        customContainer.style.cssText = 'display: flex; align-items: center; gap: 10px; padding-top: 4px; border-top: 1px solid rgba(255,255,255,0.1);';
        
        const customLabel = document.createElement('span');
        customLabel.textContent = 'Custom:';
        customLabel.style.cssText = 'color: #FF7A33; font-size: 11px; font-weight: 600; text-shadow: 0 1px 2px rgba(0,0,0,0.3);';
        customContainer.appendChild(customLabel);
        
        const customPicker = document.createElement('input');
        customPicker.type = 'color';
        customPicker.value = obj.color || '#3498db';
        customPicker.style.cssText = `
            width: 44px; height: 32px; 
            border: 2px solid rgba(255,255,255,0.25); 
            border-radius: 8px; 
            cursor: pointer;
            background: transparent;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        `;
        customPicker.oninput = (e) => {
            editor.applyColorToObject(obj, e.target.value);
        };
        customContainer.appendChild(customPicker);
        popup.appendChild(customContainer);
        
        document.body.appendChild(popup);
        
        // Adjust position if popup goes off screen
        const popupRect = popup.getBoundingClientRect();
        if (menuRect && popupRect.right > window.innerWidth) {
            popup.style.left = (menuRect.left - popupRect.width - 5) + 'px';
        }
        if (popupRect.bottom > window.innerHeight) {
            popup.style.top = (window.innerHeight - popupRect.height - 10) + 'px';
        }
    },

    /**
     * Show color palette popup from toolbar
     * @param {Object} editor - TopologyEditor instance
     * @param {Object} obj - The object to color
     * @param {string} objType - Object type ('link', 'device', 'text')
     * @param {HTMLElement} toolbar - The toolbar element to position relative to
     */
    showColorPalettePopupFromToolbar(editor, obj, objType, toolbar) {
        // Remove any existing color palette popup
        const existingPopup = document.getElementById('color-palette-popup');
        if (existingPopup) existingPopup.remove();
        
        // Temporarily disable link highlight to see actual color
        if (objType === 'link') {
            editor._colorEditingLink = obj;
            editor.draw();
        }
        
        // Get toolbar position for popup placement
        const toolbarRect = toolbar.getBoundingClientRect();
        const leftPos = toolbarRect.left + toolbarRect.width / 2;
        const topPos = toolbarRect.bottom + 8;
        
        // Create color palette popup with liquid glass aesthetic
        const popup = document.createElement('div');
        popup.id = 'color-palette-popup';
        popup.style.cssText = `
            position: fixed;
            left: ${leftPos}px;
            top: ${topPos}px;
            transform: translateX(-50%);
            background: linear-gradient(135deg, 
                rgba(255, 255, 255, 0.15) 0%, 
                rgba(255, 255, 255, 0.08) 50%, 
                rgba(255, 255, 255, 0.05) 100%);
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 16px;
            padding: 14px;
            z-index: 10002;
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.3),
                0 0 0 1px rgba(255, 255, 255, 0.1) inset,
                0 2px 4px rgba(255, 255, 255, 0.1) inset;
            backdrop-filter: blur(24px) saturate(180%);
            -webkit-backdrop-filter: blur(24px) saturate(180%);
            min-width: 190px;
        `;
        
        // Title with liquid glass style
        const title = document.createElement('div');
        title.innerHTML = `${appIcon('palette')} Quick Colors`;
        title.style.cssText = 'color: rgba(255, 255, 255, 0.9); font-size: 13px; font-weight: 600; margin-bottom: 12px; text-align: center; text-shadow: 0 1px 2px rgba(0,0,0,0.3);';
        popup.appendChild(title);
        
        // Recent colors section
        if (editor.recentColors && editor.recentColors.length > 0) {
            const recentLabel = document.createElement('div');
            recentLabel.textContent = '🕐 Recent';
            recentLabel.style.cssText = 'color: #FF7A33; font-size: 11px; margin-bottom: 6px; font-weight: 600; text-shadow: 0 1px 2px rgba(0,0,0,0.3);';
            popup.appendChild(recentLabel);
            
            const recentContainer = document.createElement('div');
            recentContainer.style.cssText = 'display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap;';
            
            editor.recentColors.forEach(color => {
                const swatch = this._createSwatch(color, 32, () => {
                    editor.applyColorToObject(obj, color);
                });
                recentContainer.appendChild(swatch);
            });
            popup.appendChild(recentContainer);
        }
        
        // Color palette
        const paletteLabel = document.createElement('div');
        paletteLabel.innerHTML = `${appIcon('palette')} Palette`;
        paletteLabel.style.cssText = 'color: #FF7A33; font-size: 11px; margin-bottom: 6px; font-weight: 600; text-shadow: 0 1px 2px rgba(0,0,0,0.3);';
        popup.appendChild(paletteLabel);
        
        const paletteContainer = document.createElement('div');
        paletteContainer.style.cssText = 'display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-bottom: 14px;';
        
        this.compactColors.forEach(color => {
            const isActive = (obj.color || '').toLowerCase() === color.toLowerCase();
            const swatch = this._createSwatch(color, 32, () => {
                editor.applyColorToObject(obj, color);
            }, isActive);
            paletteContainer.appendChild(swatch);
        });
        popup.appendChild(paletteContainer);
        
        // Custom color picker with liquid glass style
        const customContainer = document.createElement('div');
        customContainer.style.cssText = 'display: flex; align-items: center; gap: 10px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.1);';
        
        const customLabel = document.createElement('span');
        customLabel.textContent = 'Custom:';
        customLabel.style.cssText = 'color: #FF7A33; font-size: 11px; font-weight: 600; text-shadow: 0 1px 2px rgba(0,0,0,0.3);';
        customContainer.appendChild(customLabel);
        
        const customPicker = document.createElement('input');
        customPicker.type = 'color';
        customPicker.value = obj.color || '#3498db';
        customPicker.style.cssText = `
            width: 44px; height: 32px; 
            border: 2px solid rgba(255,255,255,0.25); 
            border-radius: 8px; 
            cursor: pointer;
            background: transparent;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        `;
        customPicker.oninput = (e) => {
            editor.applyColorToObject(obj, e.target.value);
        };
        customContainer.appendChild(customPicker);
        popup.appendChild(customContainer);
        
        // Prevent clicks from closing toolbar
        popup.addEventListener('mousedown', (e) => e.stopPropagation());
        popup.addEventListener('click', (e) => e.stopPropagation());
        
        document.body.appendChild(popup);
        
        // Adjust position if popup goes off screen
        const popupRect = popup.getBoundingClientRect();
        if (popupRect.right > window.innerWidth) {
            popup.style.left = (window.innerWidth - popupRect.width - 10) + 'px';
            popup.style.transform = 'none';
        }
        if (popupRect.left < 0) {
            popup.style.left = '10px';
            popup.style.transform = 'none';
        }
        if (popupRect.bottom > window.innerHeight) {
            popup.style.top = (toolbarRect.top - popupRect.height - 8) + 'px';
        }
    },

    /**
     * Hide color palette popup
     * @param {Object} editor - TopologyEditor instance
     */
    hideColorPalettePopup(editor) {
        const popup = document.getElementById('color-palette-popup');
        if (popup) popup.remove();
        // Clear color editing flag to restore highlight
        if (editor) {
            editor._colorEditingLink = null;
            editor.draw();
        }
    },

    /**
     * Create a color swatch element
     * @param {string} color - Hex color
     * @param {number} size - Size in pixels
     * @param {Function} onClick - Click handler
     * @param {boolean} isActive - Whether this color is currently active
     * @returns {HTMLElement} Swatch element
     * @private
     */
    _createSwatch(color, size, onClick, isActive = false) {
        const swatch = document.createElement('div');
        swatch.style.cssText = `
            width: ${size}px; height: ${size}px; border-radius: ${size > 30 ? 8 : 6}px;
            background: ${color}; cursor: pointer;
            border: ${isActive ? '2px solid rgba(255,255,255,0.9)' : '2px solid rgba(255,255,255,0.3)'};
            transition: all 0.15s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        `;
        swatch.title = color;
        swatch.onmouseenter = () => { 
            swatch.style.transform = 'scale(1.1)'; 
            swatch.style.borderColor = 'rgba(255,255,255,0.8)'; 
            swatch.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)'; 
        };
        swatch.onmouseleave = () => { 
            swatch.style.transform = 'scale(1)'; 
            swatch.style.borderColor = isActive ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.3)'; 
            swatch.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)'; 
        };
        swatch.onclick = onClick;
        return swatch;
    }
};

console.log('[topology-color-popups.js] ColorPopups loaded');
