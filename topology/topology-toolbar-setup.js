/**
 * topology-toolbar-setup.js - Toolbar Setup Module
 * 
 * Extracted from topology.js for modular architecture
 * Contains: setupToolbar function with all toolbar event handlers
 */

'use strict';

window.ToolbarSetup = {
    setupToolbar(editor) {
        // Helper function to safely add event listener
        const safeAddListener = (id, event, handler) => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener(event, handler);
            }
            // Silently skip missing elements (toolbar may be in different layout/panel)
        };
        
        safeAddListener('btn-base', 'click', () => editor.setMode('base'));
        safeAddListener('btn-select', 'click', () => editor.toggleTool('select'));
        safeAddListener('btn-link', 'click', () => editor.toggleTool('link'));
        safeAddListener('btn-link-curve', 'click', () => editor.toggleLinkCurveMode());
        safeAddListener('btn-curve-auto', 'click', () => editor.setGlobalCurveMode('auto'));
        safeAddListener('btn-curve-manual', 'click', () => editor.setGlobalCurveMode('manual'));
        safeAddListener('btn-link-continuous', 'click', () => editor.toggleLinkContinuousMode());
        safeAddListener('btn-link-sticky', 'click', () => editor.toggleLinkStickyMode());
        safeAddListener('btn-link-ul', 'click', () => editor.toggleLinkULMode());
        // Link style buttons - click cycles through variants
        ['solid', 'dashed', 'arrow'].forEach(baseStyle => {
            const btn = document.getElementById(`btn-link-style-${baseStyle}`);
            if (btn) {
                btn.addEventListener('click', (e) => {
                    // Check if a dot was clicked
                    const dot = e.target.closest('.style-dot');
                    if (dot) {
                        const dotIndex = parseInt(dot.dataset.index);
                        editor.setLinkStyleByIndex(baseStyle, dotIndex);
                    } else {
                        // Cycle to next variant
                        editor.cycleLinkStyle(baseStyle);
                    }
                });
            }
        });
        safeAddListener('btn-device-numbering', 'click', () => editor.toggleDeviceNumbering());
        safeAddListener('btn-device-collision', 'click', () => editor.toggleDeviceCollision());
        
        // Device style buttons - use event delegation on container for robust handling
        const deviceStylesBox = document.getElementById('device-styles-box');
        if (deviceStylesBox) {
            deviceStylesBox.addEventListener('click', (e) => {
                // Find the button that was clicked (or parent button if child was clicked)
                let target = e.target;
                let traversalPath = [];
                while (target && target !== deviceStylesBox) {
                    traversalPath.push({tag: target.tagName, id: target.id, hasStyleBtn: target.classList?.contains('style-btn')});
                    if (target.classList && target.classList.contains('style-btn')) {
                        const btnId = target.id;
                        const styleMatch = btnId.match(/btn-style-(\w+)/);
                        if (styleMatch) {
                            e.stopPropagation();
                            e.preventDefault();
                            const style = styleMatch[1];
                            editor.setDeviceStyle(style);
                            editor.setDevicePlacementMode('router');
                            return;
                        }
                    }
                    target = target.parentElement;
                }
            });
            console.log('[OK] Device style buttons event delegation set up');
        } else {
            console.warn('[WARN] device-styles-box not found');
        }

        setTimeout(() => ToolbarSetup._renderDeviceStylePreviews(editor), 200);
        
        // Device Label Font buttons
        const deviceFontGrid = document.getElementById('device-font-grid');
        if (deviceFontGrid) {
            deviceFontGrid.querySelectorAll('.font-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const fontFamily = btn.dataset.deviceFont;
                    if (!fontFamily) return;
                    
                    // Update active state
                    deviceFontGrid.querySelectorAll('.font-btn').forEach(b => {
                        b.classList.remove('active');
                        b.style.background = 'rgba(255,255,255,0.05)';
                        b.style.borderColor = 'transparent';
                        b.style.color = '#aaa';
                    });
                    btn.classList.add('active');
                    btn.style.background = 'rgba(52, 152, 219, 0.3)';
                    btn.style.borderColor = '#3498db';
                    btn.style.color = '#fff';
                    
                    // Set default device font and save to localStorage
                    editor.defaultDeviceFontFamily = fontFamily;
                    localStorage.setItem('defaultDeviceFontFamily', fontFamily);
                    
                    // Apply to selected device(s)
                    let appliedCount = 0;
                    
                    // Check multi-selection first
                    if (editor.selectedObjects.length > 0) {
                        editor.selectedObjects.forEach(obj => {
                            if (obj.type === 'device') {
                                obj.fontFamily = fontFamily;
                                appliedCount++;
                            }
                        });
                    }
                    
                    // Also check single selected object
                    if (editor.selectedObject && editor.selectedObject.type === 'device') {
                        editor.selectedObject.fontFamily = fontFamily;
                        if (appliedCount === 0) appliedCount = 1;
                    }
                    
                    editor.draw();
                    editor.scheduleAutoSave();
                    
                    if (editor.debugger) {
                        const fontName = fontFamily.split(',')[0].replace(/['"]/g, '');
                        if (appliedCount > 0) {
                            editor.debugger.logSuccess(`Device font "${fontName}" applied to ${appliedCount} device(s)`);
                        } else {
                            editor.debugger.logInfo(`Default device font set to: ${fontName}`);
                        }
                    }
                });
            });
            
            // RESTORE: Set the correct button as active based on saved preference
            const savedDeviceFont = editor.defaultDeviceFontFamily;
            deviceFontGrid.querySelectorAll('.font-btn').forEach(btn => {
                const btnFont = btn.dataset.deviceFont;
                if (btnFont === savedDeviceFont) {
                    btn.classList.add('active');
                    btn.style.background = 'rgba(52, 152, 219, 0.3)';
                    btn.style.borderColor = '#3498db';
                    btn.style.color = '#fff';
                } else {
                    btn.classList.remove('active');
                    btn.style.background = 'rgba(255,255,255,0.05)';
                    btn.style.borderColor = 'transparent';
                    btn.style.color = '#aaa';
                }
            });
            
            console.log('[OK] Device font buttons set up');
        }
        
        // Momentum button (optional)
        const momentumBtn = document.getElementById('btn-momentum');
        if (momentumBtn) {
            momentumBtn.addEventListener('click', () => editor.toggleMomentum());
        }
        
        // Movable devices button
        const movableBtn = document.getElementById('btn-movable');
        if (movableBtn) {
            movableBtn.addEventListener('click', () => editor.toggleMovableDevices());
        }
        
        // Jump to Devices button (center view on all devices)
        const jumpToDevicesBtn = document.getElementById('jump-to-devices-btn');
        if (jumpToDevicesBtn) {
            jumpToDevicesBtn.addEventListener('click', () => editor.centerOnDevices());
            // Hover effects
            jumpToDevicesBtn.addEventListener('mouseenter', () => {
                jumpToDevicesBtn.style.background = 'rgba(52, 152, 219, 1)';
                jumpToDevicesBtn.style.transform = 'scale(1.05)';
            });
            jumpToDevicesBtn.addEventListener('mouseleave', () => {
                jumpToDevicesBtn.style.background = 'rgba(52, 152, 219, 0.85)';
                jumpToDevicesBtn.style.transform = 'scale(1)';
            });
        }
        
        safeAddListener('curve-magnitude-slider', 'input', (e) => editor.updateCurveMagnitude(e.target.value));
        safeAddListener('friction-slider', 'input', (e) => editor.updateFriction(e.target.value));
        
        // Link width slider
        const linkWidthSlider = document.getElementById('link-width-slider');
        const linkWidthValue = document.getElementById('link-width-value');
        if (linkWidthSlider) {
            // Initialize slider with saved value
            linkWidthSlider.value = editor.currentLinkWidth;
            if (linkWidthValue) linkWidthValue.textContent = editor.currentLinkWidth;
            
            linkWidthSlider.addEventListener('input', (e) => {
                let width = parseInt(e.target.value);
                editor.currentLinkWidth = width;
                // Save to localStorage for persistence
                localStorage.setItem('currentLinkWidth', width.toString());
                if (linkWidthValue) linkWidthValue.textContent = width;
                
                // Update ALL selected links (multi-select support)
                let updated = false;
                if (editor.selectedObjects && editor.selectedObjects.length > 0) {
                    editor.selectedObjects.forEach(obj => {
                        if (obj.type === 'link' || obj.type === 'unbound') {
                            // Cap width to prevent overlap with neighbor links
                            const maxWidth = editor.getMaxLinkWidth(obj);
                            const cappedWidth = Math.min(width, maxWidth);
                            obj.width = cappedWidth;
                            updated = true;
                        }
                    });
                }
                // Also update single selected link if not in multi-select
                if (!updated && editor.selectedObject && (editor.selectedObject.type === 'link' || editor.selectedObject.type === 'unbound')) {
                    editor.selectedObject.width = width;
                    updated = true;
                }
                
                // Always redraw to update any link previews
                editor.draw();
                
                if (updated && editor.debugger) {
                    editor.debugger.logInfo(`Link width: ${width}px`);
                }
            });
            
            // Also save on change (when user releases slider)
            linkWidthSlider.addEventListener('change', () => {
                editor.scheduleAutoSave();
            });
        }
        
        // Default Link Color picker and palette
        const defaultLinkColor = document.getElementById('default-link-color');
        const defaultLinkColorHex = document.getElementById('default-link-color-hex');
        const linkColorPalette = document.querySelectorAll('.default-link-palette-color');
        const applyLinkColorAllBtn = document.getElementById('btn-apply-link-color-all');
        
        // Initialize default link color from localStorage or based on dark mode
        editor.defaultLinkColor = localStorage.getItem('defaultLinkColor') || (editor.darkMode ? '#ffffff' : '#000000');
        if (defaultLinkColor) {
            defaultLinkColor.value = editor.defaultLinkColor;
            if (defaultLinkColorHex) defaultLinkColorHex.textContent = editor.defaultLinkColor.toUpperCase();
        }
        
        // Update palette to show active color
        const updateLinkColorPalette = (color) => {
            linkColorPalette.forEach(swatch => {
                if (swatch.dataset.color.toLowerCase() === color.toLowerCase()) {
                    swatch.style.border = '2px solid rgba(255,255,255,0.8)';
                    swatch.style.boxShadow = '0 0 8px rgba(255,255,255,0.4)';
                } else {
                    swatch.style.border = '2px solid transparent';
                    swatch.style.boxShadow = 'none';
                }
            });
        };
        updateLinkColorPalette(editor.defaultLinkColor);
        
        if (defaultLinkColor) {
            defaultLinkColor.addEventListener('input', (e) => {
                editor.defaultLinkColor = e.target.value;
                localStorage.setItem('defaultLinkColor', editor.defaultLinkColor);
                if (defaultLinkColorHex) defaultLinkColorHex.textContent = editor.defaultLinkColor.toUpperCase();
                updateLinkColorPalette(editor.defaultLinkColor);
            });
        }
        
        // Link color palette clicks
        linkColorPalette.forEach(swatch => {
            swatch.addEventListener('click', () => {
                const color = swatch.dataset.color;
                editor.defaultLinkColor = color;
                localStorage.setItem('defaultLinkColor', color);
                if (defaultLinkColor) defaultLinkColor.value = color;
                if (defaultLinkColorHex) defaultLinkColorHex.textContent = color.toUpperCase();
                updateLinkColorPalette(color);
                editor.addToLastUsedColors(color);
            });
        });
        
        // Apply color to all links button
        if (applyLinkColorAllBtn) {
            applyLinkColorAllBtn.addEventListener('click', () => {
                editor.saveState();
                let count = 0;
                editor.objects.forEach(obj => {
                    if (obj.type === 'link' || obj.type === 'unbound') {
                        obj.color = editor.defaultLinkColor;
                        count++;
                    }
                });
                editor.draw();
                if (editor.debugger) {
                    editor.debugger.logSuccess(`Applied color ${editor.defaultLinkColor} to ${count} links`);
                }
                editor.showNotification(`Applied color to ${count} links`, 'success');
            });
        }
        
        // btn-router removed; device style buttons now enter placement mode
        // Text tool button (existing)
        safeAddListener('btn-text', 'click', () => editor.toggleTool('text'));
        
        // ========== SHAPE TOOLBAR SETUP ==========
        editor.setupShapeToolbar();
        
        // Place TBs button - continuous text box placement mode
        const placeTbsBtn = document.getElementById('btn-place-tbs');
        if (placeTbsBtn) {
            placeTbsBtn.addEventListener('click', () => editor.toggleContinuousTextPlacement());
        }
        
        // SCALER/CONFIG cloud button - handled by scaler-gui.js (opens SCALER menu)
        // The click handler is set by ScalerGUI.addScalerButton() in scaler-gui.js
        
        // NEW: Angle meter toggle button
        const angleMeterBtn = document.getElementById('btn-angle-meter');
        if (angleMeterBtn) {
            angleMeterBtn.addEventListener('click', () => editor.toggleAngleMeter());
        }
        
        // TB Attach toggle button - auto-create interface text boxes
        const tbAttachBtn = document.getElementById('btn-tb-attach');
        if (tbAttachBtn) {
            tbAttachBtn.addEventListener('click', () => editor.toggleTBAttach());
        }
        
        // ========== UNIFIED COLOR CONTROLS ==========
        const defaultTextColor = document.getElementById('default-text-color');
        const defaultBgColor = document.getElementById('default-text-bg-color');
        const defaultBorderColor = document.getElementById('default-text-border-color');
        const defaultTextColorPreview = document.getElementById('default-text-color-preview');
        const unifiedColorInput = document.getElementById('unified-color-input');
        const unifiedColorHex = document.getElementById('unified-color-hex');
        const activeColorTarget = document.getElementById('active-color-target');
        const bgOpacityContainer = document.getElementById('bg-opacity-container');
        
        // Current active color target: 'text', 'background', or 'border'
        editor.activeColorTarget = 'text';
        
        // Initialize color preview dots
        const updateColorPreviewDots = () => {
            const textDot = document.getElementById('text-color-preview-dot');
            const bgDot = document.getElementById('bg-color-preview-dot');
            const borderDot = document.getElementById('border-color-preview-dot');
            
            if (textDot && defaultTextColor) textDot.style.background = defaultTextColor.value;
            if (bgDot && defaultBgColor) {
                bgDot.style.background = defaultBgColor.value === 'transparent' 
                    ? 'linear-gradient(45deg, #666 25%, transparent 25%), linear-gradient(-45deg, #666 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #666 75%), linear-gradient(-45deg, transparent 75%, #666 75%)'
                    : defaultBgColor.value;
                bgDot.style.backgroundSize = '4px 4px';
            }
            if (borderDot && defaultBorderColor) borderDot.style.background = defaultBorderColor.value;
        };
        
        // Update unified color input based on active target
        const updateUnifiedColorInput = () => {
            let color, label;
            switch (editor.activeColorTarget) {
                case 'text':
                    color = defaultTextColor?.value || '#ffffff';
                    label = 'Text Color';
                    if (bgOpacityContainer) bgOpacityContainer.style.display = 'none';
                    break;
                case 'background':
                    color = defaultBgColor?.value || '#1a1a2e';
                    label = 'Background';
                    if (bgOpacityContainer) bgOpacityContainer.style.display = 'block';
                    break;
                case 'border':
                    color = defaultBorderColor?.value || '#0066FA';
                    label = 'Text Border';
                    if (bgOpacityContainer) bgOpacityContainer.style.display = 'none';
                    break;
            }
            if (unifiedColorInput) unifiedColorInput.value = color === 'transparent' ? '#1a1a2e' : color;
            if (unifiedColorHex) unifiedColorHex.textContent = color.toUpperCase();
            if (activeColorTarget) activeColorTarget.textContent = label;
            
            // Update preview text
            if (defaultTextColorPreview) {
                defaultTextColorPreview.style.color = defaultTextColor?.value || '#ffffff';
                const bgEnabled = document.getElementById('default-text-bg-enabled')?.checked;
                const bgOpacity = (document.getElementById('default-bg-opacity')?.value || 100) / 100;
                if (bgEnabled && defaultBgColor) {
                    const bg = defaultBgColor.value;
                    if (bg === 'transparent') {
                        defaultTextColorPreview.style.background = 'transparent';
                    } else {
                        // Convert hex to rgba with opacity
                        const r = parseInt(bg.slice(1,3), 16);
                        const g = parseInt(bg.slice(3,5), 16);
                        const b = parseInt(bg.slice(5,7), 16);
                        defaultTextColorPreview.style.background = `rgba(${r},${g},${b},${bgOpacity})`;
                    }
                } else {
                    defaultTextColorPreview.style.background = 'transparent';
                }
            }
            
            // Update palette active state
            document.querySelectorAll('.palette-swatch').forEach(swatch => {
                swatch.classList.toggle('active', swatch.dataset.color.toLowerCase() === color.toLowerCase());
            });
            
            updateColorPreviewDots();
        };
        
        // Color target button clicks
        document.querySelectorAll('.color-target-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Don't switch if clicking on toggle
                if (e.target.closest('.mini-toggle')) return;
                
                document.querySelectorAll('.color-target-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                editor.activeColorTarget = btn.dataset.target;
                updateUnifiedColorInput();
            });
        });
        
        // Unified color input changes
        if (unifiedColorInput) {
            unifiedColorInput.addEventListener('input', (e) => {
                const color = e.target.value;
                switch (editor.activeColorTarget) {
                    case 'text':
                if (defaultTextColor) defaultTextColor.value = color;
                        break;
                    case 'background':
                        if (defaultBgColor) defaultBgColor.value = color;
                        break;
                    case 'border':
                        if (defaultBorderColor) defaultBorderColor.value = color;
                        break;
                }
                if (unifiedColorHex) unifiedColorHex.textContent = color.toUpperCase();
                updateUnifiedColorInput();
                editor.saveDefaultTextSettings();
            });
            
            unifiedColorInput.addEventListener('change', (e) => {
                editor.addToLastUsedColors(e.target.value);
            });
        }
        
        // Unified palette swatch clicks
        document.querySelectorAll('.palette-swatch').forEach(swatch => {
            swatch.addEventListener('click', () => {
                const color = swatch.dataset.color;
                switch (editor.activeColorTarget) {
                    case 'text':
                        if (defaultTextColor) defaultTextColor.value = color === 'transparent' ? '#ffffff' : color;
                        break;
                    case 'background':
                if (defaultBgColor) defaultBgColor.value = color;
                        break;
                    case 'border':
                        if (defaultBorderColor) defaultBorderColor.value = color === 'transparent' ? '#0066FA' : color;
                        break;
                }
                if (color !== 'transparent') editor.addToLastUsedColors(color);
                updateUnifiedColorInput();
                editor.saveDefaultTextSettings();
            });
        });
        
        // Background enabled toggle
        const bgEnabledToggle = document.getElementById('default-text-bg-enabled');
        if (bgEnabledToggle) {
            bgEnabledToggle.addEventListener('change', () => {
                updateUnifiedColorInput();
                editor.saveDefaultTextSettings();
            });
        }
        
        // Background opacity
        const bgOpacitySlider = document.getElementById('default-bg-opacity');
        const bgOpacityValue = document.getElementById('bg-opacity-value');
        if (bgOpacitySlider) {
            bgOpacitySlider.addEventListener('input', (e) => {
                if (bgOpacityValue) bgOpacityValue.textContent = e.target.value + '%';
                updateUnifiedColorInput();
            });
            bgOpacitySlider.addEventListener('change', () => editor.saveDefaultTextSettings());
        }
        
        // Border enabled toggle
        const borderEnabledToggle = document.getElementById('default-text-border-enabled');
        if (borderEnabledToggle) {
            borderEnabledToggle.addEventListener('change', () => {
                editor.saveDefaultTextSettings();
            });
        }
        
        // Initialize unified color display
        setTimeout(() => updateUnifiedColorInput(), 100);
        
        // ========== SYNCHRONIZED LAST USED COLORS ==========
        // Load and initialize last used colors from localStorage
        editor.lastUsedColors = JSON.parse(localStorage.getItem('syncedLastUsedColors')) || [];
        editor.updateAllLastUsedColorDisplays();
        
        // Setup click handlers for unified last used color swatches
        document.querySelectorAll('#unified-last-used-colors > div, #link-last-used-colors > div').forEach(swatch => {
            swatch.addEventListener('click', (e) => {
                const color = e.target.dataset.color;
                if (!color) return;
                
                const parent = e.target.closest('.synced-last-used');
                if (parent && parent.id === 'link-last-used-colors') {
                    // Link color palette
                    const linkColorInput = document.getElementById('default-link-color');
                    const linkColorHex = document.getElementById('default-link-color-hex');
                    if (linkColorInput) linkColorInput.value = color;
                    if (linkColorHex) linkColorHex.textContent = color.toUpperCase();
                    editor.defaultLinkColor = color;
                    localStorage.setItem('defaultLinkColor', color);
                } else {
                    // Unified text color palette - apply to active target
                    switch (editor.activeColorTarget) {
                        case 'text':
                            if (defaultTextColor) defaultTextColor.value = color;
                            break;
                        case 'background':
                            if (defaultBgColor) defaultBgColor.value = color;
                            break;
                        case 'border':
                            if (defaultBorderColor) defaultBorderColor.value = color;
                            break;
                    }
                    // Trigger update
                    const updateEvent = new Event('input', { bubbles: true });
                    if (unifiedColorInput) {
                        unifiedColorInput.value = color;
                        unifiedColorInput.dispatchEvent(updateEvent);
                    }
                }
            });
        });
        
        // Toggle palette visibility when clicking on headers
        const textColorHeader = document.getElementById('default-text-color-header');
        const textColorPalette = document.getElementById('default-text-color-palette');
        const textColorToggle = document.getElementById('default-text-color-toggle');
        if (textColorHeader && textColorPalette) {
            textColorHeader.addEventListener('click', (e) => {
                // Don't toggle if clicking on the color input itself
                if (e.target.type === 'color') return;
                const isHidden = textColorPalette.style.display === 'none';
                textColorPalette.style.display = isHidden ? 'grid' : 'none';
                if (textColorToggle) textColorToggle.textContent = isHidden ? '▲' : '▼';
            });
        }
        
        const bgColorHeader = document.getElementById('default-bg-color-header');
        const bgColorPalette = document.getElementById('default-bg-color-palette');
        const bgColorToggle = document.getElementById('default-bg-color-toggle');
        if (bgColorHeader && bgColorPalette) {
            bgColorHeader.addEventListener('click', (e) => {
                // Don't toggle if clicking on the color input or checkbox
                if (e.target.type === 'color' || e.target.type === 'checkbox') return;
                const isHidden = bgColorPalette.style.display === 'none';
                bgColorPalette.style.display = isHidden ? 'grid' : 'none';
                if (bgColorToggle) bgColorToggle.textContent = isHidden ? '▲' : '▼';
            });
        }
        
        // Save default text settings when changed
        if (defaultTextColor) {
            defaultTextColor.addEventListener('change', () => editor.saveDefaultTextSettings());
        }
        if (defaultBgColor) {
            defaultBgColor.addEventListener('change', () => editor.saveDefaultTextSettings());
        }
        const defaultBgEnabled = document.getElementById('default-text-bg-enabled');
        if (defaultBgEnabled) {
            defaultBgEnabled.addEventListener('change', () => editor.saveDefaultTextSettings());
        }
        
        // Load saved default text settings
        editor.loadDefaultTextSettings();
        
        // ====== NEW TEXT TOOL CONTROLS ======
        
        // Font Selection Buttons - selecting a font enters text placement mode OR applies to selected text
        document.querySelectorAll('.font-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const fontFamily = btn.dataset.font;
                if (!fontFamily) return;
                
                // Update active state
                document.querySelectorAll('.font-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Save font selection
                editor.defaultFontFamily = fontFamily;
                editor.saveDefaultTextSettings();
                
                // Update preview if exists
                const preview = document.getElementById('default-text-color-preview');
                if (preview) preview.style.fontFamily = fontFamily;
                
                // Check if there are selected text objects - if so, apply font directly
                const hasSelectedText = (editor.selectedObject && editor.selectedObject.type === 'text') ||
                    (editor.selectedObjects && editor.selectedObjects.some(obj => obj.type === 'text'));
                
                if (hasSelectedText) {
                    // Apply font to selected text objects
                    editor.applyFontToSelectedText(fontFamily, null);
                } else {
                    // ENTER TEXT PLACEMENT MODE (like device placement) - only if no text selected
                editor.enterTextPlacementMode();
                }
            });
        });
        
        // Text Size Preset Buttons
        document.querySelectorAll('.size-preset-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const size = parseInt(btn.dataset.size);
                if (!size) return;
                
                // Update active state
                document.querySelectorAll('.size-preset-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Update slider and value display
                const sizeSlider = document.getElementById('default-text-size');
                const sizeValue = document.getElementById('default-text-size-value');
                if (sizeSlider) sizeSlider.value = size;
                if (sizeValue) sizeValue.textContent = size + 'px';
                
                // Save size selection
                editor.defaultFontSize = size;
                editor.saveDefaultTextSettings();
                
                // Apply to selected text objects
                editor.applyFontToSelectedText(null, size);
                
                if (editor.debugger) {
                    editor.debugger.logInfo(`Default text size set to: ${size}px`);
                }
            });
        });
        
        // Text Size Slider
        const textSizeSlider = document.getElementById('default-text-size');
        const textSizeValue = document.getElementById('default-text-size-value');
        if (textSizeSlider) {
            textSizeSlider.addEventListener('input', (e) => {
                const size = parseInt(e.target.value);
                if (textSizeValue) textSizeValue.textContent = size + 'px';
                
                // Update preset button active state
                document.querySelectorAll('.size-preset-btn').forEach(btn => {
                    const presetSize = parseInt(btn.dataset.size);
                    if (presetSize === size) {
                        btn.classList.add('active');
                    } else {
                        btn.classList.remove('active');
                    }
                });
                
                // Save size selection
                editor.defaultFontSize = size;
                editor.saveDefaultTextSettings();
                
                // Apply to selected text objects
                editor.applyFontToSelectedText(null, size);
            });
        }
        
        // NOTE: Background Opacity, Border Toggle, and Border Color handlers are in unified color section above
        
        // Border Style Buttons
        document.querySelectorAll('.border-style-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const style = btn.dataset.style;
                if (!style) return;
                
                // Update active state
                document.querySelectorAll('.border-style-btn').forEach(b => {
                    b.classList.remove('active');
                    b.style.background = 'rgba(0,0,0,0.2)';
                    b.style.borderColor = 'rgba(255,255,255,0.1)';
                });
                btn.classList.add('active');
                btn.style.background = 'rgba(0,102,250,0.25)';
                btn.style.borderColor = '#0066FA';
                
                editor.defaultBorderStyle = style;
                editor.saveDefaultTextSettings();
            });
        });
        
        safeAddListener('btn-undo', 'click', () => editor.undo());
        safeAddListener('btn-redo', 'click', () => editor.redo());
        // Top bar buttons
        safeAddListener('btn-delete-top', 'click', () => editor.deleteSelected());
        safeAddListener('btn-clear-top', 'click', () => editor.clearCanvas());
        safeAddListener('btn-save-top', 'click', () => editor.saveTopology());
        safeAddListener('btn-load-top', 'click', () => {
            const fileInput = document.getElementById('file-input');
            if (fileInput) fileInput.click();
        });
        safeAddListener('btn-shortcuts-top', 'click', () => editor.showShortcuts());

        // Click flash for all top-bar buttons: brief orange highlight border on click
        document.querySelectorAll('.top-bar-btn, .cloud-glass-btn, .cloud-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                if (btn.classList.contains('active') || btn.classList.contains('dnaas-panel-open') || btn.classList.contains('topologies-open')) return;
                const target = btn.querySelector('.glass-layer') || btn;
                target.classList.remove('click-flash');
                void target.offsetWidth;
                target.classList.add('click-flash');
                target.addEventListener('animationend', () => target.classList.remove('click-flash'), { once: true });
            });
        });

        // File menu removed — consolidated into Topologies dropdown
        
        // Debugger toggle button
        const debuggerBtn = document.getElementById('btn-debugger-top');
        if (debuggerBtn) {
            debuggerBtn.addEventListener('click', () => {
                if (editor.debugger) {
                    editor.debugger.toggle();
                }
            });
        }
        
        // Link type labels toggle button (debug view)
        const linkTypeLabelsBtn = document.getElementById('btn-link-type-labels');
        if (linkTypeLabelsBtn) {
            linkTypeLabelsBtn.addEventListener('click', () => {
                editor.showLinkTypeLabels = !editor.showLinkTypeLabels;
                const statusText = linkTypeLabelsBtn.querySelector('.status-text');
                
                if (editor.showLinkTypeLabels) {
                    linkTypeLabelsBtn.classList.add('active');
                    if (statusText) statusText.textContent = 'Labels: ON';
                    if (editor.debugger) {
                        editor.debugger.logSuccess('Link type labels enabled');
                    }
                } else {
                    linkTypeLabelsBtn.classList.remove('active');
                    if (statusText) statusText.textContent = 'Labels: OFF';
                    if (editor.debugger) {
                        editor.debugger.logInfo('Link type labels disabled');
                    }
                }
                
                editor.draw();
            });
        }
        
        // Link attachments toggle button (show/hide text attached to links)
        const linkAttachBtn = document.getElementById('btn-link-attachments');
        if (linkAttachBtn) {
            // Load saved state from localStorage
            const savedLinkAttachments = localStorage.getItem('topology_showLinkAttachments');
            if (savedLinkAttachments !== null) {
                editor.showLinkAttachments = savedLinkAttachments === 'true';
                const statusText = linkAttachBtn.querySelector('.status-text');
                if (editor.showLinkAttachments) {
                    linkAttachBtn.classList.add('active');
                    if (statusText) statusText.textContent = 'Link Text: ON';
                } else {
                    linkAttachBtn.classList.remove('active');
                    if (statusText) statusText.textContent = 'Link Text: OFF';
                }
            }
            
            linkAttachBtn.addEventListener('click', () => {
                editor.showLinkAttachments = !editor.showLinkAttachments;
                const statusText = linkAttachBtn.querySelector('.status-text');
                
                // Save to localStorage
                localStorage.setItem('topology_showLinkAttachments', editor.showLinkAttachments.toString());
                
                if (editor.showLinkAttachments) {
                    linkAttachBtn.classList.add('active');
                    if (statusText) statusText.textContent = 'Link Text: ON';
                    if (editor.debugger) {
                        editor.debugger.logSuccess('Link attachments shown');
                    }
                } else {
                    linkAttachBtn.classList.remove('active');
                    if (statusText) statusText.textContent = 'Link Text: OFF';
                    if (editor.debugger) {
                        editor.debugger.logInfo('Link attachments hidden');
                    }
                }
                editor.draw();
            });
        }
        
        // Text Always Face User toggle button
        const textFaceUserBtn = document.getElementById('btn-text-face-user');
        if (textFaceUserBtn) {
            // Load saved state from localStorage
            const savedTextFaceUser = localStorage.getItem('topology_textAlwaysFaceUser');
            if (savedTextFaceUser !== null) {
                editor.textAlwaysFaceUser = savedTextFaceUser === 'true';
                const statusText = textFaceUserBtn.querySelector('.status-text');
                if (editor.textAlwaysFaceUser) {
                    textFaceUserBtn.classList.add('active');
                    if (statusText) statusText.textContent = 'Face User: ON';
                } else {
                    textFaceUserBtn.classList.remove('active');
                    if (statusText) statusText.textContent = 'Face User: OFF';
                }
            }
            
            textFaceUserBtn.addEventListener('click', () => {
                editor.textAlwaysFaceUser = !editor.textAlwaysFaceUser;
                const statusText = textFaceUserBtn.querySelector('.status-text');
                
                // Save to localStorage
                localStorage.setItem('topology_textAlwaysFaceUser', editor.textAlwaysFaceUser.toString());
                
                if (editor.textAlwaysFaceUser) {
                    textFaceUserBtn.classList.add('active');
                    if (statusText) statusText.textContent = 'Face User: ON';
                    if (editor.debugger) {
                        editor.debugger.logSuccess('Text will always face user (0° rotation)');
                    }
                    editor.showToast('All text now horizontal', 'success');
                } else {
                    textFaceUserBtn.classList.remove('active');
                    if (statusText) statusText.textContent = 'Face User: OFF';
                    if (editor.debugger) {
                        editor.debugger.logInfo('Text rotation enabled');
                    }
                    editor.showToast('Text follows link rotation', 'info')
                }
                
                editor.draw();
            });
        }
        
        // DNAAS panel button (opens discovery panel)
        const dnaasBtn = document.getElementById('btn-dnaas');
        const dnaasPanel = document.getElementById('dnaas-panel');
        if (dnaasBtn && dnaasPanel) {
            // Move panel to body so it escapes .top-bar's transform containing block
            // (transform: translateZ(0) on .top-bar makes position:fixed relative to it)
            document.body.appendChild(dnaasPanel);
            
            const updatePanelOpenClass = () => {
                const isOpen = dnaasPanel.style.display === 'block';
                if (isOpen) {
                    dnaasBtn.classList.add('dnaas-panel-open');
                } else {
                    dnaasBtn.classList.remove('dnaas-panel-open');
                }
            };
            
            dnaasBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const isVisible = dnaasPanel.style.display === 'block';
                
                if (!isVisible) {
                    // Close Topologies dropdown if open
                    const topoDD = document.getElementById('topologies-dropdown-menu');
                    const topoBtn = document.getElementById('btn-topologies');
                    if (topoDD && topoDD.style.display === 'block') {
                        topoDD.style.display = 'none';
                        if (topoBtn) topoBtn.classList.remove('topologies-open');
                    }
                    // Close Network Mapper panel if open
                    const nmPanel = document.getElementById('network-mapper-panel');
                    const nmBtn = document.getElementById('btn-network-mapper');
                    if (nmPanel && nmPanel.style.display === 'block') {
                        nmPanel.style.display = 'none';
                        if (nmBtn) nmBtn.classList.remove('nm-panel-open');
                    }
                    
                    const btnRect = dnaasBtn.getBoundingClientRect();
                    const panelWidth = 400;
                    const padding = 10;
                    
                    let left = btnRect.right - panelWidth;
                    let top = btnRect.bottom + 5;
                    
                    if (left < padding) left = padding;
                    if (left + panelWidth > window.innerWidth - padding) {
                        left = window.innerWidth - panelWidth - padding;
                    }
                    if (top + 500 > window.innerHeight) {
                        top = Math.max(padding, btnRect.top - 500 - 5);
                    }
                    
                    dnaasPanel.style.left = left + 'px';
                    dnaasPanel.style.top = top + 'px';
                    dnaasPanel.style.display = 'block';
                    
                    editor.populateDnaasSuggestions();
                } else {
                    dnaasPanel.style.display = 'none';
                }
                
                updatePanelOpenClass();
            });
            
            document.addEventListener('click', (e) => {
                if (!dnaasBtn.contains(e.target) && !dnaasPanel.contains(e.target)) {
                    dnaasPanel.style.display = 'none';
                    updatePanelOpenClass();
                }
            });
            
            // Panel item hover effects (if any dropdown items exist)
            const dropdownItems = dnaasPanel.querySelectorAll('.dropdown-item');
            dropdownItems.forEach(item => {
                item.addEventListener('mouseenter', () => {
                    item.style.background = 'rgba(52, 152, 219, 0.3)';
                });
                item.addEventListener('mouseleave', () => {
                    item.style.background = 'none';
                });
            });
            
            // BD Hierarchy badge - toggles BD Legend panel (small badge on DNAAS button)
            const bdHierarchyBtn = document.getElementById('btn-bd-hierarchy');
            if (bdHierarchyBtn) {
                bdHierarchyBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    editor.toggleBDLegendPanel();
                });
                // Hover effects for the badge
                bdHierarchyBtn.addEventListener('mouseenter', () => {
                    bdHierarchyBtn.style.transform = 'scale(1.1)';
                });
                bdHierarchyBtn.addEventListener('mouseleave', () => {
                    bdHierarchyBtn.style.transform = 'scale(1)';
                });
            }
            
            // Load Latest discovery file
            const bd210Btn = document.getElementById('dnaas-bd210');
            if (bd210Btn) {
                bd210Btn.addEventListener('click', async () => {
                    try {
                        editor.showToast('Loading latest discovery...', 'info');
                                
                        // Always use direct fetch for reliability
                            const resp = await fetch('/api/dnaas/discovery/list');
                        if (!resp.ok) {
                            throw new Error(`API error: ${resp.status}`);
                        }
                            const files = await resp.json();
                        console.log('[Load Latest] Files from API:', files);
                        
                            if (files.files && files.files.length > 0) {
                            // Sort by modified date (newest first) - already sorted by API but ensure
                            const sortedFiles = [...files.files].sort((a, b) => b.modified - a.modified);
                            // Prefer multi_bd files
                                const latestFile = sortedFiles.find(f => f.name.includes('multi_bd')) || sortedFiles[0];
                            
                            console.log('[Load Latest] Loading file:', latestFile.name);
                            
                            // Fetch the file
                            const dataResp = await fetch(`/api/dnaas/discovery/file/${encodeURIComponent(latestFile.name)}`);
                            if (!dataResp.ok) {
                                throw new Error(`Failed to load file: ${dataResp.status}`);
                            }
                            let data = await dataResp.json();
                            
                            console.log('[Load Latest] File loaded, objects:', data.objects?.length || 0);
                            
                            // Try to enrich, but don't fail if enrichment fails
                            try {
                                data = await editor.enrichTerminationDevicesWithManagedConfig(data);
                            } catch (enrichErr) {
                                console.warn('[Load Latest] Enrichment failed, using raw data:', enrichErr);
                            }
                            
                            // Load into canvas
                                editor.loadDnaasData(data);
                                editor.showToast(`Loaded: ${latestFile.name}`, 'success');
                            } else {
                            editor.showToast('No discovery files found. Run a discovery first.', 'warning');
                        }
                    } catch (err) {
                        console.error('[Load Latest] Failed:', err);
                        editor.showToast(`Failed to load: ${err.message}`, 'error');
                    }
                    dnaasPanel.style.display = 'none';
                });
            }
            
            // Discover live network
            const discoverBtn = document.getElementById('dnaas-discover');
            if (discoverBtn) {
                discoverBtn.addEventListener('click', () => {
                    editor.loadDnaasTopology('discover');
                    dnaasPanel.style.display = 'none';
                });
            }
            
            // Trace Path by Serial Number
            const traceSerialBtn = document.getElementById('dnaas-trace-serial');
            if (traceSerialBtn) {
                traceSerialBtn.addEventListener('click', () => {
                    editor.showDnaasTraceDialog();
                    dnaasPanel.style.display = 'none';
                });
            }
            
            // Find DNAAS Bridge Domains
            const findBdsBtn = document.getElementById('dnaas-find-bds');
            if (findBdsBtn) {
                findBdsBtn.addEventListener('click', () => {
                    editor.showDnaasFindBDsDialog();
                    dnaasPanel.style.display = 'none';
                });
            }
            
            // Load from Discovery Output
            const loadJsonBtn = document.getElementById('dnaas-load-json');
            if (loadJsonBtn) {
                loadJsonBtn.addEventListener('click', () => {
                    editor.loadDnaasFromFile();
                    dnaasPanel.style.display = 'none';
                });
            }
            
            // Save Topology quick action in Quick Actions section
            const saveDnaasTopoBtn = document.getElementById('dnaas-save-dnaas-topo');
            if (saveDnaasTopoBtn) {
                saveDnaasTopoBtn.addEventListener('click', () => {
                    if (editor.objects.length === 0) {
                        editor.showToast('Canvas is empty -- run a discovery first', 'warning');
                        return;
                    }
                    const deviceName = window._dnaasDiscoveryData?.metadata?.source
                        || '';
                    editor.saveAsDnaasTopology(deviceName);
                    dnaasPanel.style.display = 'none';
                });
            }
            
            // Enable LLDP button - shows menu with Enable LLDP and LLDP Table options
            const enableLldpBtn = document.getElementById('dnaas-enable-lldp');
            if (enableLldpBtn) {
                enableLldpBtn.addEventListener('click', (e) => {
                    const serialInput = document.getElementById('dnaas-serial-input');
                    const serial = serialInput?.value.trim();
                    if (!serial) {
                        editor.showToast('Please enter a device serial or hostname first', 'warning');
                        serialInput?.focus();
                        return;
                    }
                    
                    // Find device object by serial/hostname
                    const device = editor.objects.find(obj => 
                        obj.type === 'device' && (
                            obj.sshConfig?.host === serial ||
                            obj.deviceSerial === serial ||
                            obj.label === serial
                        )
                    ) || { label: serial, sshConfig: { host: serial } };
                    
                    // Show LLDP menu at button position
                    const rect = enableLldpBtn.getBoundingClientRect();
                    editor.showLldpButtonMenu(device, rect.left, rect.bottom + 5);
                });
            }
            
            // MAIN Start Discovery button - ALWAYS does Multi-BD discovery
            const startDiscoveryBtn = document.getElementById('dnaas-start-discovery');
            const serialInput = document.getElementById('dnaas-serial-input');
            if (startDiscoveryBtn && serialInput) {
                startDiscoveryBtn.addEventListener('click', () => {
                    const serial = serialInput.value.trim();
                    if (!serial) {
                        editor.showToast('Please enter a device serial or hostname', 'error');
                        return;
                    }
                    
                    // Check if the device is a DNAAS router (not allowed to start discovery from)
                    if (editor.isDnaasRouter(serial)) {
                        editor.showToast('Discovery must start from a Termination device (PE/CE), not from DNAAS routers', 'error');
                        return;
                    }
                    
                    // Start Multi-BD discovery (full topology with all Bridge Domains)
                    editor.startMultiBDDiscovery(serial);
                });
            }
            
            // Cancel Discovery button
            const cancelDiscoveryBtn = document.getElementById('dnaas-cancel-discovery');
            if (cancelDiscoveryBtn) {
                cancelDiscoveryBtn.addEventListener('click', () => {
                    editor.cancelDnaasDiscovery();
                });
            }
            
            // dnaas-save-as-dnaas handler is set by startMultiBDDiscovery
            // (topology-dnaas-helpers.js) — no duplicate listener here
            
            // Dismiss Result button - closes panel without loading, resets button state
            const dismissResultBtn = document.getElementById('dnaas-dismiss-result');
            if (dismissResultBtn) {
                dismissResultBtn.addEventListener('click', () => {
                    editor.dismissDnaasResult();
                });
            }
            
            // Multi-BD Discovery button
            const multiBdBtn = document.getElementById('dnaas-multi-bd-discovery');
            if (multiBdBtn) {
                multiBdBtn.addEventListener('click', () => {
                    const serialInput = document.getElementById('dnaas-serial-input');
                    const serial = serialInput ? serialInput.value.trim() : '';
                    
                    if (!serial) {
                        editor.showToast('Please enter a device serial or hostname', 'warning');
                        if (serialInput) serialInput.focus();
                        return;
                    }
                    
                    // Check if the device is a DNAAS router (not allowed to start discovery from)
                    if (editor.isDnaasRouter(serial)) {
                        editor.showToast('Discovery must start from a Termination device (PE/CE), not from DNAAS routers', 'error');
                        return;
                    }
                    
                    // Start Multi-BD discovery
                    editor.startMultiBDDiscovery(serial);
                });
            }
        }
        
        // Theme toggle button
        const themeBtn = document.getElementById('btn-theme-toggle');
        if (themeBtn) {
            themeBtn.addEventListener('click', () => editor.toggleTheme());
        }
        
        // Grid Lines toggle button
        const gridLinesBtn = document.getElementById('btn-grid-lines');
        if (gridLinesBtn) {
            gridLinesBtn.addEventListener('click', () => editor.toggleGridLines());
            // Set initial state (grid is ON by default)
            if (editor.gridZoomEnabled) {
                gridLinesBtn.classList.add('active', 'grid-on');
            }
        }
        
        // Sync body classes for fixed-position toggle visibility
        const syncBarCollapseState = () => {
            const topBar = document.querySelector('.top-bar');
            const toolbar = document.getElementById('left-toolbar');
            if (topBar?.classList.contains('collapsed')) document.body.classList.add('top-bar-collapsed');
            else document.body.classList.remove('top-bar-collapsed');
            if (toolbar?.classList.contains('collapsed')) document.body.classList.add('toolbar-collapsed');
            else document.body.classList.remove('toolbar-collapsed');
        };

        const smoothResizeDuring = (durationMs = 320) => {
            const start = performance.now();
            const tick = () => {
                editor.resizeCanvas();
                if (performance.now() - start < durationMs) requestAnimationFrame(tick);
            };
            requestAnimationFrame(tick);
        };

        // Left Toolbar toggle
        const toolbarToggle = document.getElementById('toolbar-toggle');
        if (toolbarToggle) {
            toolbarToggle.addEventListener('click', () => {
                const toolbar = document.getElementById('left-toolbar');
                if (toolbar) {
                    toolbar.classList.toggle('collapsed');
                    syncBarCollapseState();
                    smoothResizeDuring();
                }
            });
        }

        // Top Bar toggle
        const topBarToggle = document.getElementById('top-bar-toggle');
        if (topBarToggle) {
            topBarToggle.addEventListener('click', () => {
                const topBar = document.querySelector('.top-bar');
                if (topBar) {
                    topBar.classList.toggle('collapsed');
                    syncBarCollapseState();
                    smoothResizeDuring();
                }
            });
        }

        syncBarCollapseState(); // Initial sync
        editor.syncBarCollapseState = syncBarCollapseState;
        editor.smoothResizeDuring = smoothResizeDuring;
        
        const colorPicker = document.getElementById('color-picker');
        if (colorPicker) {
            colorPicker.addEventListener('change', (e) => editor.updateSelectedColor(e.target.value));
            colorPicker.addEventListener('focus', () => {
            if (editor.selectedObject && editor.selectedObject.type === 'device') {
                editor.canvas.style.cursor = 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'24\' height=\'24\' viewBox=\'0 0 24 24\'%3E%3Cpath d=\'M20.71 5.63l-1.34-1.34c-.39-.39-1.02-.39-1.41 0L9 12.25 11.75 15l8.96-8.96c.39-.39.39-1.02 0-1.41zM7 14a3 3 0 0 0-3 3c0 1.31-1.16 2-2 2 .92 1.22 2.49 2 4 2a4 4 0 0 0 4-4c0-1.66-1.34-3-3-3z\' fill=\'%23000\'/%3E%3C/svg%3E") 12 12, auto';
            }
        });
            colorPicker.addEventListener('blur', () => {
            editor.updateCursor();
        });
        }
        const fontSizeInput = document.getElementById('font-size');
        if (fontSizeInput) {
            fontSizeInput.addEventListener('input', (e) => editor.updateTextSize(e.target.value));
            fontSizeInput.addEventListener('change', (e) => editor.saveState()); // Save when slider released
        }
        
        // Device label now controlled via device editor modal (double-click device)
        // Left toolbar device-label input removed
        
        // Shortcuts button is in top bar, not toolbar
        const shortcutsBtn = document.getElementById('btn-shortcuts');
        if (shortcutsBtn) {
            shortcutsBtn.addEventListener('click', () => editor.showShortcuts());
        }
        const closeShortcutsBtn = document.getElementById('close-shortcuts');
        if (closeShortcutsBtn) {
            closeShortcutsBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                editor.hideShortcuts();
            });
        }
        
        // Zoom buttons with hold-to-repeat functionality
        const zoomInBtn = document.getElementById('btn-zoom-in');
        if (zoomInBtn) {
            let zoomInInterval = null;
            zoomInBtn.addEventListener('mousedown', () => {
                editor.zoomIn(); // Immediate first zoom
                zoomInInterval = setInterval(() => editor.zoomIn(), 150); // Repeat every 150ms
            });
            zoomInBtn.addEventListener('mouseup', () => {
                if (zoomInInterval) clearInterval(zoomInInterval);
            });
            zoomInBtn.addEventListener('mouseleave', () => {
                if (zoomInInterval) clearInterval(zoomInInterval);
            });
        }
        
        const zoomOutBtn = document.getElementById('btn-zoom-out');
        if (zoomOutBtn) {
            let zoomOutInterval = null;
            zoomOutBtn.addEventListener('mousedown', () => {
                editor.zoomOut(); // Immediate first zoom
                zoomOutInterval = setInterval(() => editor.zoomOut(), 150); // Repeat every 150ms
            });
            zoomOutBtn.addEventListener('mouseup', () => {
                if (zoomOutInterval) clearInterval(zoomOutInterval);
            });
            zoomOutBtn.addEventListener('mouseleave', () => {
                if (zoomOutInterval) clearInterval(zoomOutInterval);
            });
        }
        
        const zoomResetBtn = document.getElementById('btn-zoom-reset');
        if (zoomResetBtn) {
            zoomResetBtn.addEventListener('click', () => editor.resetZoom());
        }
        
        // HUD Zoom Controls (bottom-right corner)
        const zoomInHudBtn = document.getElementById('btn-zoom-in-hud');
        if (zoomInHudBtn) {
            let zoomInInterval = null;
            zoomInHudBtn.addEventListener('mousedown', () => {
                editor.zoomIn();
                zoomInInterval = setInterval(() => editor.zoomIn(), 150);
            });
            zoomInHudBtn.addEventListener('mouseup', () => {
                if (zoomInInterval) clearInterval(zoomInInterval);
            });
            zoomInHudBtn.addEventListener('mouseleave', () => {
                if (zoomInInterval) clearInterval(zoomInInterval);
            });
        }
        
        const zoomOutHudBtn = document.getElementById('btn-zoom-out-hud');
        if (zoomOutHudBtn) {
            let zoomOutInterval = null;
            zoomOutHudBtn.addEventListener('mousedown', () => {
                editor.zoomOut();
                zoomOutInterval = setInterval(() => editor.zoomOut(), 150);
            });
            zoomOutHudBtn.addEventListener('mouseup', () => {
                if (zoomOutInterval) clearInterval(zoomOutInterval);
            });
            zoomOutHudBtn.addEventListener('mouseleave', () => {
                if (zoomOutInterval) clearInterval(zoomOutInterval);
            });
        }
        
        const zoomResetHudBtn = document.getElementById('btn-zoom-reset-hud');
        if (zoomResetHudBtn) {
            zoomResetHudBtn.addEventListener('click', () => editor.resetZoom());
        }
        
        // Context menu handlers - safe with null checks
        const safeCtxListener = (id, handler) => {
            const el = document.getElementById(id);
            if (el) el.addEventListener('click', handler);
        };
        
        // CRITICAL: Prevent context menu mousedown from triggering canvas drag
        // This fixes the bug where clicking a menu option causes the selected device to move
        const contextMenu = document.getElementById('context-menu');
        if (contextMenu) {
            contextMenu.addEventListener('mousedown', (e) => {
                e.stopPropagation(); // Don't let canvas receive this event
            });
        }
        
        // Also prevent mousedown on all submenus from triggering canvas drag
        [
            'ctx-curve-submenu', 'ctx-layers-submenu', 'ctx-device-style-submenu', 
            'ctx-curve-mode-submenu', 'ctx-scaler-submenu', 'ctx-bulk-links-submenu',
            'ctx-bulk-devices-submenu', 'ctx-bulk-textboxes-submenu'
        ].forEach(id => {
            const submenu = document.getElementById(id);
            if (submenu) {
                submenu.addEventListener('mousedown', (e) => {
                    e.stopPropagation(); // Don't let canvas receive this event
                });
            }
        });
        safeCtxListener('ctx-copy-style', () => editor.handleContextCopyStyle());
        safeCtxListener('ctx-duplicate', () => editor.handleContextDuplicate());
        safeCtxListener('ctx-add-text', () => editor.handleContextAddText());
        safeCtxListener('ctx-change-color', () => editor.handleContextColor());
        
        // Curve submenu hover (for links)
        const curveSubmenuTrigger = document.getElementById('ctx-curve');
        if (curveSubmenuTrigger) {
            // Click to toggle submenu (more reliable than hover-only)
            curveSubmenuTrigger.addEventListener('click', (e) => {
                e.stopPropagation();
                const submenu = document.getElementById('ctx-curve-submenu');
                if (submenu && submenu.style.display === 'block') {
                    editor.hideCurveSubmenu();
                } else {
                    // Close other submenus before opening this one
                    editor.hideDeviceStyleSubmenu();
                    editor.hideLayersSubmenu();
                    editor.showCurveSubmenu();
                }
            });
            // REMOVED: mouseenter auto-open - submenus should only open on click
            // curveSubmenuTrigger.addEventListener('mouseenter', () => { ... });
            // Hide submenu when mouse leaves the trigger (with delay to allow moving to submenu)
            curveSubmenuTrigger.addEventListener('mouseleave', () => {
                setTimeout(() => editor.hideCurveSubmenuIfNotHovered(), 150);
            });
        }
        
        // Curve submenu mouseleave - hide when mouse leaves the submenu itself
        const curveSubmenu = document.getElementById('ctx-curve-submenu');
        if (curveSubmenu) {
            curveSubmenu.addEventListener('mouseleave', () => {
                setTimeout(() => editor.hideCurveSubmenuIfNotHovered(), 150);
            });
        }
        
        // Curve submenu item handlers
        safeCtxListener('ctx-keep-curve', () => editor.handleContextKeepCurve());
        safeCtxListener('ctx-curve-magnitude', () => editor.handleContextCurveMagnitude());
        safeCtxListener('ctx-curve-mps', () => editor.handleContextCurveMPs());
        
        // Curve Mode submenu trigger - CLICK ONLY (no hover auto-open)
        const curveModeSubmenuTrigger = document.getElementById('ctx-curve-mode-trigger');
        if (curveModeSubmenuTrigger) {
            // REMOVED: mouseenter auto-open - submenus should only open on click
            curveModeSubmenuTrigger.addEventListener('click', (e) => {
                e.stopPropagation();
                e.preventDefault();
                editor.showCurveModeSubmenu();
            });
            // Keep mouseleave for closing when moving away
            curveModeSubmenuTrigger.addEventListener('mouseleave', () => {
                setTimeout(() => editor.hideCurveModeSubmenuIfNotHovered(), 150);
            });
        }
        
        // Curve Mode submenu mouseleave - hide when mouse leaves the submenu itself
        const curveModeSubmenu = document.getElementById('ctx-curve-mode-submenu');
        if (curveModeSubmenu) {
            curveModeSubmenu.addEventListener('mouseleave', () => {
                setTimeout(() => editor.hideCurveModeSubmenuIfNotHovered(), 150);
            });
        }
        
        // Curve Mode submenu options - use event delegation on the submenu container
        const curveModeSubmenuContainer = document.getElementById('ctx-curve-mode-submenu');
        if (curveModeSubmenuContainer) {
            curveModeSubmenuContainer.addEventListener('mousedown', (e) => {
                e.stopPropagation();
            }, true);
            
            curveModeSubmenuContainer.addEventListener('click', (e) => {
                const target = e.target.closest('.context-menu-item');
                if (!target) return;
                
                e.stopPropagation();
                e.preventDefault();
                
                const id = target.id;
                if (id === 'ctx-curve-mode-global') {
                    editor.handleContextCurveModeChange(null);
                } else if (id === 'ctx-curve-mode-auto') {
                    editor.handleContextCurveModeChange('auto');
                } else if (id === 'ctx-curve-mode-manual') {
                    editor.handleContextCurveModeChange('manual');
                } else if (id === 'ctx-curve-mode-off') {
                    editor.handleContextCurveModeChange('off');
                }
            });
        }
        // ctx-change-size removed - device sizing handled via double-click editor
        safeCtxListener('ctx-change-width', () => editor.handleContextWidth());
        safeCtxListener('ctx-change-style', () => editor.handleContextStyle());
        safeCtxListener('ctx-change-label', () => editor.handleContextLabel());
        safeCtxListener('ctx-lock', () => editor.handleContextLock());
        safeCtxListener('ctx-unlock', () => editor.handleContextUnlock());
        safeCtxListener('ctx-ssh-address', () => editor.handleContextSSHAddress());
        safeCtxListener('ctx-enable-lldp', () => editor.handleContextEnableLldp());
        safeCtxListener('ctx-start-discovery', () => editor.handleContextStartDiscovery());
        safeCtxListener('ctx-detach-link', () => editor.handleContextDetachFromLink());
        safeCtxListener('ctx-detach-device', () => editor.handleContextDetachFromDevice());
        safeCtxListener('ctx-delete', () => editor.handleContextDelete());
        
        // Layer context menu items
        safeCtxListener('ctx-layer-to-front', () => editor.handleContextLayerToFront());
        safeCtxListener('ctx-layer-forward', () => editor.handleContextLayerForward());
        safeCtxListener('ctx-layer-backward', () => editor.handleContextLayerBackward());
        safeCtxListener('ctx-layer-to-back', () => editor.handleContextLayerToBack());
        safeCtxListener('ctx-layer-reset', () => editor.handleContextLayerReset());
        
        // Layers submenu hover
        const layersSubmenuTrigger = document.getElementById('ctx-layers');
        if (layersSubmenuTrigger) {
            // Click to toggle submenu (more reliable than hover-only)
            layersSubmenuTrigger.addEventListener('click', (e) => {
                e.stopPropagation();
                e.preventDefault();
                const submenu = document.getElementById('ctx-layers-submenu');
                if (submenu && submenu.style.display === 'block') {
                    editor.hideLayersSubmenu();
                } else {
                    // Close other submenus before opening this one
                    editor.hideDeviceStyleSubmenu();
                    editor.hideCurveSubmenu();
                    editor.showLayersSubmenu();
                }
            });
            // REMOVED: mouseenter auto-open - submenus should only open on click
            // layersSubmenuTrigger.addEventListener('mouseenter', () => { ... });
        }
        // Don't auto-hide layers submenu on mouseleave - let it stay open until context menu closes
        
        // Device Style submenu events - CLICK ONLY to toggle (no hover auto-open)
        const deviceStyleSubmenuTrigger = document.getElementById('ctx-device-style');
        if (deviceStyleSubmenuTrigger) {
            // Click to toggle submenu (REMOVED hover - user complained about auto-open)
            deviceStyleSubmenuTrigger.addEventListener('click', (e) => {
                e.stopPropagation();
                e.preventDefault();
                const submenu = document.getElementById('ctx-device-style-submenu');
                if (submenu && submenu.style.display === 'block') {
                    editor.hideDeviceStyleSubmenu();
                } else {
                    // Close other submenus before opening this one
                    editor.hideLayersSubmenu();
                    editor.hideCurveSubmenu();
                    editor.showDeviceStyleSubmenu();
                }
            });
            // REMOVED: mouseenter auto-open - submenus should only open on click
            // deviceStyleSubmenuTrigger.addEventListener('mouseenter', () => { ... });
        }
        // Don't auto-hide submenu on mouseleave - let it stay open until context menu closes or user clicks elsewhere
        
        // Device style option click handlers - select style and enter placement mode
        const styleCircle = document.getElementById('ctx-style-circle');
        if (styleCircle) styleCircle.addEventListener('click', () => editor.selectStyleAndEnterPlacementMode('circle'));
        const styleClassic = document.getElementById('ctx-style-classic');
        if (styleClassic) styleClassic.addEventListener('click', () => editor.selectStyleAndEnterPlacementMode('classic'));
        const styleSimple = document.getElementById('ctx-style-simple');
        if (styleSimple) styleSimple.addEventListener('click', () => editor.selectStyleAndEnterPlacementMode('simple'));
        const styleServer = document.getElementById('ctx-style-server');
        if (styleServer) styleServer.addEventListener('click', () => editor.selectStyleAndEnterPlacementMode('server'));
        const styleHex = document.getElementById('ctx-style-hex');
        if (styleHex) styleHex.addEventListener('click', () => editor.selectStyleAndEnterPlacementMode('hex'));
        
        // Link editor modal events - with null checks
        const closeLinkEditor = document.getElementById('close-link-editor');
        if (closeLinkEditor) closeLinkEditor.addEventListener('click', () => editor.hideLinkEditor());
        
        const linkEditorModal = document.getElementById('link-editor-modal');
        if (linkEditorModal) linkEditorModal.addEventListener('click', (e) => {
            if (e.target.id === 'link-editor-modal') editor.hideLinkEditor();
        });
        
        const editorLinkColor = document.getElementById('editor-link-color');
        if (editorLinkColor) editorLinkColor.addEventListener('input', (e) => editor.updateLinkEditorProperty('color', e.target.value));
        
        const editorLinkWidth = document.getElementById('editor-link-width');
        if (editorLinkWidth) editorLinkWidth.addEventListener('input', (e) => {
            const widthValue = document.getElementById('editor-link-width-value');
            if (widthValue) widthValue.textContent = e.target.value;
            editor.updateLinkEditorProperty('width', parseInt(e.target.value));
        });
        
        const editorLinkStyle = document.getElementById('editor-link-style');
        if (editorLinkStyle) editorLinkStyle.addEventListener('change', (e) => editor.updateLinkEditorProperty('style', e.target.value));
        
        const editorLinkCurve = document.getElementById('editor-link-curve');
        if (editorLinkCurve) editorLinkCurve.addEventListener('change', (e) => {
            editor.updateLinkEditorProperty('curveOverride', e.target.checked);
            // Show/hide curve magnitude section based on curve enabled
            const magnitudeSection = document.getElementById('editor-curve-magnitude-section');
            if (magnitudeSection) {
                magnitudeSection.style.display = e.target.checked ? 'block' : 'none';
            }
            // Show/hide keep curve section (UL/BUL only)
            const keepCurveSection = document.getElementById('editor-keep-curve-section');
            if (keepCurveSection && editor.editingLink && editor.editingLink.type === 'unbound') {
                keepCurveSection.style.display = e.target.checked ? 'block' : 'none';
            }
        });
        
        const editorLinkCurveMagnitude = document.getElementById('editor-link-curve-magnitude');
        if (editorLinkCurveMagnitude) editorLinkCurveMagnitude.addEventListener('input', (e) => {
            const magnitudeValue = document.getElementById('editor-link-curve-magnitude-value');
            if (magnitudeValue) magnitudeValue.textContent = e.target.value;
            editor.updateLinkEditorProperty('curveMagnitude', parseInt(e.target.value));
        });
        
        // Per-link curve mode dropdown (auto/manual/off override)
        const editorLinkCurveMode = document.getElementById('editor-link-curve-mode');
        if (editorLinkCurveMode) editorLinkCurveMode.addEventListener('change', (e) => {
            const value = e.target.value || null; // Empty string = use global
            
            // Use the same curve mode change handler as context menu for consistency
            // This ensures seamless transitions between modes (capturing curve shapes, etc.)
            if (editor.editingLink) {
                // Set the target link for the handler
                editor._curveSubmenuLink = editor.editingLink;
                editor.handleContextCurveModeChange(value);
                editor._curveSubmenuLink = null;
            }
            
            editor.draw();
        });
        
        // Keep Current Curve checkbox (UL/BUL only)
        const editorLinkKeepCurve = document.getElementById('editor-link-keep-curve');
        if (editorLinkKeepCurve) editorLinkKeepCurve.addEventListener('change', (e) => {
            editor.handleKeepCurveChange(e.target.checked);
        });
        
        // Device editor modal events - with null checks
        const closeDeviceEditor = document.getElementById('close-device-editor');
        if (closeDeviceEditor) closeDeviceEditor.addEventListener('click', () => editor.hideDeviceEditor());
        
        const deviceEditorModal = document.getElementById('device-editor-modal');
        if (deviceEditorModal) deviceEditorModal.addEventListener('click', (e) => {
            if (e.target.id === 'device-editor-modal') editor.hideDeviceEditor();
        });
        
        const editorDeviceColor = document.getElementById('editor-device-color');
        if (editorDeviceColor) editorDeviceColor.addEventListener('input', (e) => editor.updateDeviceEditorProperty('color', e.target.value));
        
        const editorDeviceSize = document.getElementById('editor-device-size');
        if (editorDeviceSize) editorDeviceSize.addEventListener('input', (e) => {
            const sizeValue = document.getElementById('editor-device-size-value');
            if (sizeValue) sizeValue.textContent = e.target.value;
            editor.updateDeviceEditorProperty('radius', parseInt(e.target.value));
        });
        
        const editorDeviceLabel = document.getElementById('editor-device-label');
        if (editorDeviceLabel) editorDeviceLabel.addEventListener('input', (e) => editor.updateDeviceEditorProperty('label', e.target.value));
        
        // Device address input (for SSH terminal button)
        const editorDeviceAddress = document.getElementById('editor-device-address');
        if (editorDeviceAddress) editorDeviceAddress.addEventListener('input', (e) => editor.updateDeviceEditorProperty('deviceAddress', e.target.value));
        
        // Close context menu on outside click
        // But NOT when clicking on related popups (color palette, width slider, style options)
        document.addEventListener('click', (e) => {
            const isOnContextMenu = e.target.closest('#context-menu');
            const isOnColorPalette = e.target.closest('#color-palette-popup');
            const isOnWidthSlider = e.target.closest('#width-slider-popup');
            const isOnStyleOptions = e.target.closest('#style-options-popup');
            const isOnAdjacentTextMenu = e.target.closest('#adjacent-text-menu');
            const isOnCurveMagnitude = e.target.closest('#curve-magnitude-popup');
            const isOnCurveSubmenu = e.target.closest('#ctx-curve-submenu');
            const isOnCurveModeSubmenu = e.target.closest('#ctx-curve-mode-submenu');
            const isOnLayersSubmenu = e.target.closest('#ctx-layers-submenu');
            const isOnDeviceStyleSubmenu = e.target.closest('#ctx-device-style-submenu');
            
            if (!isOnContextMenu && !isOnColorPalette && !isOnWidthSlider && !isOnStyleOptions && 
                !isOnAdjacentTextMenu && !isOnCurveMagnitude && !isOnCurveSubmenu && !isOnCurveModeSubmenu &&
                !isOnLayersSubmenu && !isOnDeviceStyleSubmenu) {
                editor.hideContextMenu();
            }
        });
        
        // Close shortcuts modal on backdrop click
        const shortcutsModal = document.getElementById('shortcuts-modal');
        if (shortcutsModal) shortcutsModal.addEventListener('click', (e) => {
            if (e.target.id === 'shortcuts-modal') {
                editor.hideShortcuts();
            }
        });

        // Close shortcuts modal on Escape key
        document.addEventListener('keydown', (e) => {
            const shortcutsModal = document.getElementById('shortcuts-modal');
            const textEditorModal = document.getElementById('text-editor-modal');
            const linkDetailsModal = document.getElementById('link-details-modal');
            
            if (e.key === 'Escape') {
                if (shortcutsModal && shortcutsModal.classList.contains('show')) {
                    e.preventDefault();
                    e.stopPropagation();
                    editor.hideShortcuts();
                } else if (textEditorModal && textEditorModal.classList.contains('show')) {
                    e.preventDefault();
                    e.stopPropagation();
                    editor.hideTextEditor();
                } else if (linkDetailsModal && linkDetailsModal.classList.contains('show')) {
                    e.preventDefault();
                    e.stopPropagation();
                    editor.forceHideLinkDetails(); // Force close on Escape
                }
            }
        });
        
        // Close text editor modal on backdrop click
        const textEditorModal = document.getElementById('text-editor-modal');
        if (textEditorModal) {
            textEditorModal.addEventListener('click', (e) => {
                if (e.target.id === 'text-editor-modal') {
                    // CRITICAL FIX: Don't close if we just finished dragging
                    const modalContent = textEditorModal.querySelector('.draggable-modal');
                    if (modalContent && modalContent.dataset.justDragged === 'true') {
                        return; // Ignore backdrop click after drag
                    }
                    editor.hideTextEditor();
                }
            });
        }
        
        // Close link details modal on backdrop click ONLY
        // ENHANCED: Prevent closing during drag/resize operations
        const linkDetailsModal = document.getElementById('link-details-modal');
        if (linkDetailsModal) {
            // Make these accessible from makeDraggableModal/makeResizableModal
            window._linkModalDragging = false;
            window._linkModalResizing = false;
            let lastInteractionTime = 0;
            
            // Track interaction state
            const modalContent = linkDetailsModal.querySelector('.modal-content');
            if (modalContent) {
                // Track all mousedown events on modal
                modalContent.addEventListener('mousedown', (e) => {
                    lastInteractionTime = Date.now();
                    console.log('📌 Modal content mousedown');
                });
                
                // Only stop click propagation on modal body/content (not handles/header)
                const modalBody = modalContent.querySelector('.modal-body');
                if (modalBody) {
                    modalBody.addEventListener('click', (e) => {
                        e.stopPropagation();
                    });
                }
            }
            
            // Only close on backdrop click (with multiple safety checks)
            linkDetailsModal.addEventListener('click', (e) => {
                const timeSinceInteraction = Date.now() - lastInteractionTime;
                
                console.log('Modal backdrop clicked:', {
                    target: e.target.id,
                    dragging: window._linkModalDragging,
                    resizing: window._linkModalResizing,
                    timeSince: timeSinceInteraction
                });
                
                // Only close if:
                // 1. Clicking directly on backdrop
                // 2. Not currently dragging or resizing
                // 3. At least 500ms since last interaction (prevents close after drag/resize)
                if (e.target.id === 'link-details-modal' && 
                    !window._linkModalDragging && 
                    !window._linkModalResizing &&
                    timeSinceInteraction > 500) {
                    console.log('[OK] Closing modal (intentional backdrop click)');
                    editor.hideLinkDetails();
                } else {
                    console.log('[BLOCKED] Modal close blocked (safety check)');
                }
            });
        }
        
        // Text editor modal handlers
        const closeTextEditorBtn = document.getElementById('close-text-editor');
        if (closeTextEditorBtn) {
            closeTextEditorBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Close text editor button clicked');
                editor.hideTextEditor();
            });
        } else {
            console.warn('Close text editor button not found during setup');
        }
        const applyTextEditorBtn = document.getElementById('btn-text-editor-apply');
        if (applyTextEditorBtn) {
            applyTextEditorBtn.addEventListener('click', () => editor.applyTextEditor());
        }
        const cancelTextEditorBtn = document.getElementById('btn-text-editor-cancel');
        if (cancelTextEditorBtn) {
            cancelTextEditorBtn.addEventListener('click', () => editor.hideTextEditor());
        }

        // Link details modal handlers
        const closeLinkDetailsBtn = document.getElementById('close-link-details');
        if (closeLinkDetailsBtn) {
            closeLinkDetailsBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Close link details button clicked');
                editor.forceHideLinkDetails(); // Force close even with invalid fields
            });
        } else {
            console.warn('Close link details button not found during setup');
        }
        const closeLinkDetailsBtn2 = document.getElementById('btn-close-link-details');
        if (closeLinkDetailsBtn2) {
            closeLinkDetailsBtn2.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Close link details button 2 clicked');
                editor.forceHideLinkDetails(); // Force close even with invalid fields
            });
        }
        // Link Table Action Buttons
        const resetLinkTableBtn = document.getElementById('btn-reset-link-table');
        if (resetLinkTableBtn) {
            resetLinkTableBtn.addEventListener('click', () => editor.resetLinkTableFields());
        }
        
        const copyMarkdownBtn = document.getElementById('btn-copy-link-markdown');
        if (copyMarkdownBtn) {
            copyMarkdownBtn.addEventListener('click', () => editor.copyLinkTableAsMarkdown());
        }
        
        const saveLinkTableBtn = document.getElementById('btn-save-link-table');
        if (saveLinkTableBtn) {
            saveLinkTableBtn.addEventListener('click', () => editor.saveLinkDetails());
        }
        
        // Fetch Details button for DNAAS interface details
        const fetchDetailsBtn = document.getElementById('lt-fetch-details-btn');
        if (fetchDetailsBtn) {
            fetchDetailsBtn.addEventListener('click', () => editor.fetchDnaasInterfaceDetails());
        }
        
        const createLinkTextBtn = document.getElementById('btn-create-link-text');
        if (createLinkTextBtn) {
            createLinkTextBtn.addEventListener('click', () => editor.createLinkTextBoxes());
        }
        
        const editorRotation = document.getElementById('editor-rotation');
        if (editorRotation) editorRotation.addEventListener('input', (e) => {
            const rotationValue = document.getElementById('editor-rotation-value');
            if (rotationValue) rotationValue.textContent = e.target.value + '°';
        });

        // XRAY Settings - Mac / Wireshark config
        const xraySection = document.getElementById('xray-settings-section');
        if (xraySection) {
            const loadXrayConfig = async () => {
                try {
                    const resp = await fetch('/api/xray/config');
                    if (resp.ok) {
                        const cfg = await resp.json();
                        const mac = cfg.mac || {};
                        const ipInput = document.getElementById('xray-mac-ip');
                        const userInput = document.getElementById('xray-mac-user');
                        const passInput = document.getElementById('xray-mac-password');
                        const wsInput = document.getElementById('xray-wireshark-path');
                        const dirInput = document.getElementById('xray-pcap-dir');
                        if (ipInput) ipInput.value = mac.ip_vpn || '';
                        if (userInput) userInput.value = mac.user || '';
                        if (passInput) passInput.value = mac.password || '';
                        if (wsInput) wsInput.value = mac.wireshark_path || '/Applications/Wireshark.app/Contents/MacOS/Wireshark';
                        if (dirInput) dirInput.value = mac.pcap_directory || '~/Desktop/Packet-captures';
                    }
                } catch (e) {
                    console.warn('[XRAY] Failed to load config:', e);
                }
            };
            loadXrayConfig();

            const saveBtn = document.getElementById('xray-save-config');
            if (saveBtn) {
                saveBtn.addEventListener('click', async () => {
                    const mac = {
                        ip_vpn: document.getElementById('xray-mac-ip')?.value?.trim() || null,
                        user: document.getElementById('xray-mac-user')?.value?.trim() || null,
                        password: document.getElementById('xray-mac-password')?.value || null,
                        wireshark_path: document.getElementById('xray-wireshark-path')?.value?.trim() || null,
                        pcap_directory: document.getElementById('xray-pcap-dir')?.value?.trim() || null
                    };
                    try {
                        const resp = await fetch('/api/xray/config', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ mac })
                        });
                        const result = await resp.json();
                        if (result.error) {
                            editor.showToast('XRAY config save failed: ' + result.error, 'error');
                            return;
                        }
                        editor.showToast('XRAY config saved', 'success');
                    } catch (e) {
                        editor.showToast('Failed to save XRAY config: ' + e.message, 'error');
                    }
                });
            }

            const verifyBtn = document.getElementById('xray-verify-mac');
            const verifyStatus = document.getElementById('xray-verify-status');
            if (verifyBtn && verifyStatus) {
                verifyBtn.addEventListener('click', async () => {
                    const ip = document.getElementById('xray-mac-ip')?.value?.trim();
                    const user = document.getElementById('xray-mac-user')?.value?.trim();
                    const pass = document.getElementById('xray-mac-password')?.value;
                    if (!ip) {
                        editor.showToast('Enter Mac IP first', 'warning');
                        return;
                    }
                    verifyStatus.style.display = 'block';
                    verifyStatus.textContent = 'Verifying...';
                    verifyStatus.className = 'xray-verify-status';
                    try {
                        const resp = await fetch('/api/xray/verify-mac', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ ip, user: user || undefined, password: pass || undefined })
                        });
                        const data = await resp.json();
                        if (data.reachable) {
                            verifyStatus.textContent = 'Mac reachable (SSH OK)';
                            verifyStatus.className = 'xray-verify-status ok';
                        } else if (data.ping && !data.ssh) {
                            verifyStatus.innerHTML = '';
                            const line1 = document.createElement('div');
                            line1.textContent = 'Ping OK but SSH failed';
                            line1.style.fontWeight = '600';
                            const line2 = document.createElement('div');
                            line2.textContent = data.error || 'Enable Remote Login on Mac';
                            line2.style.cssText = 'font-size:10px;opacity:0.85;margin-top:2px;';
                            verifyStatus.appendChild(line1);
                            verifyStatus.appendChild(line2);
                            verifyStatus.className = 'xray-verify-status fail';
                        } else {
                            verifyStatus.textContent = data.error || 'Mac not reachable';
                            verifyStatus.className = 'xray-verify-status fail';
                        }
                    } catch (e) {
                        verifyStatus.textContent = 'Verify failed: ' + e.message;
                        verifyStatus.className = 'xray-verify-status fail';
                    }
                });
            }

            const passToggle = document.getElementById('xray-password-toggle');
            if (passToggle) {
                passToggle.addEventListener('click', () => {
                    const input = document.getElementById('xray-mac-password');
                    if (!input) return;
                    if (input.type === 'password') {
                        input.type = 'text';
                        passToggle.textContent = 'Hide';
                    } else {
                        input.type = 'password';
                        passToggle.textContent = 'Show';
                    }
                });
            }
        }
    },

    // LAYER SYSTEM COMPLETELY REMOVED

    _renderDeviceStylePreviews(editor) {
        const DS = window.DeviceStyles;
        if (!DS) {
            console.warn('[DeviceStylePreview] DeviceStyles not loaded, retrying in 500ms');
            setTimeout(() => ToolbarSetup._renderDeviceStylePreviews(editor), 500);
            return;
        }

        const styles = [
            { btnId: 'btn-style-circle', id: 'circle', name: 'Circle' },
            { btnId: 'btn-style-classic', id: 'classic', name: 'Cylinder' },
            { btnId: 'btn-style-simple', id: 'simple', name: 'Simple' },
            { btnId: 'btn-style-hex', id: 'hex', name: 'Hexagon' },
            { btnId: 'btn-style-server', id: 'server', name: 'Tower' }
        ];
        const isDark = editor.darkMode;
        const color = '#3498db';
        const dpr = window.devicePixelRatio || 1;
        const w = 40, h = 28;
        const r = 11;

        styles.forEach(style => {
            const btn = document.getElementById(style.btnId);
            if (!btn) return;
            btn.innerHTML = '';

            const canvas = document.createElement('canvas');
            canvas.width = w * dpr;
            canvas.height = h * dpr;
            canvas.style.width = w + 'px';
            canvas.style.height = h + 'px';
            canvas.style.display = 'block';
            canvas.style.pointerEvents = 'none';

            const ctx = canvas.getContext('2d');
            ctx.scale(dpr, dpr);
            ctx.clearRect(0, 0, w, h);

            const fakeDevice = { x: w / 2, y: h / 2, radius: r, color, rotation: 0, visualStyle: style.id, deviceType: 'router' };
            const fakeEditor = { ctx, darkMode: isDark, defaultDeviceFontFamily: 'Inter, sans-serif' };
            try {
                switch (style.id) {
                    case 'circle': DS.drawDeviceCircle(fakeEditor, fakeDevice, false); break;
                    case 'classic': DS.drawDeviceClassicRouter(fakeEditor, fakeDevice, false); break;
                    case 'simple': DS.drawDeviceSimpleRouter(fakeEditor, fakeDevice, false); break;
                    case 'server': DS.drawDeviceServerTower(fakeEditor, fakeDevice, false); break;
                    case 'hex': DS.drawDeviceHexRouter(fakeEditor, fakeDevice, false); break;
                }
            } catch (err) {
                console.warn('[DeviceStylePreview] Failed to render', style.id, err);
            }

            const label = document.createElement('span');
            label.className = 'style-label';
            label.textContent = style.name;

            btn.appendChild(canvas);
            btn.appendChild(label);
        });
    },

    buildHelpersSection(editor) {
        const dk = document.body.classList.contains('dark-mode');
        const scriptsContainer = document.getElementById('helpers-setup-scripts');
        const tipsContainer = document.getElementById('helpers-usage-tips');
        if (!scriptsContainer || !tipsContainer) return;

        const SETUP_SCRIPTS = [
            {
                id: 'server',
                icon: 'ico-rocket',
                title: 'Start App Server',
                env: 'H263 (Linux)',
                tooltip: 'Starts both the frontend server (port 8080) and the discovery API (port 8765). Run this on the H263 Linux server where the app is deployed. The frontend serves index.html + JS, and the discovery API handles DNAAS, Network Mapper, and device inventory.',
                script: 'cd ~/CURSOR && python3 serve.py &\ncd ~/CURSOR && python3 discovery_api.py &',
                check: '/api/xray/config'
            },
            {
                id: 'scaler-bridge',
                icon: 'ico-layers',
                title: 'Start Scaler Bridge',
                env: 'H263 (Linux)',
                tooltip: 'The Scaler Bridge exposes scaler-wizard config fetch, sync, and summary via REST. Enables Device Manager Sync, config viewing, and config comparison in the CONFIG panel. Requires serve.py and discovery_api.py running.',
                script: 'cd ~/CURSOR && python3 scaler_bridge.py &',
                noCheck: true
            },
            {
                id: 'mac-remote-login',
                icon: 'ico-target',
                title: 'Enable Remote Login (Mac)',
                env: 'MacBook',
                tooltip: 'Packet Capture needs SSH access to your Mac to deliver .pcap files and open them in Wireshark. This enables the built-in SSH server on macOS. After enabling, configure your Mac IP in the Packet-Capture section above.',
                script: 'sudo systemsetup -setremotelogin on\nsudo launchctl load -w /System/Library/LaunchDaemons/ssh.plist',
                noCheck: true
            },
            {
                id: 'mac-wireshark',
                icon: 'ico-search',
                title: 'Install Wireshark (Mac)',
                env: 'MacBook',
                tooltip: 'Wireshark is required on the Mac to auto-open captured packets. Install via Homebrew or download from wireshark.org. The app auto-detects Wireshark at /Applications/Wireshark.app.',
                script: 'brew install --cask wireshark',
                noCheck: true
            },
            {
                id: 'xray-deps',
                icon: 'ico-bug',
                title: 'Install Capture Dependencies',
                env: 'H263 (Linux)',
                tooltip: 'Installs Python packages needed for all packet capture modes (CP, DP, DNAAS-DP). paramiko for SSH sessions, scp for file transfer, scapy for packet analysis, sshpass for non-interactive SSH auth to Mac and Arista, tshark for protocol decoding.',
                script: 'pip3 install paramiko scp scapy\nsudo apt install -y sshpass tshark',
                check: '/api/xray/config'
            },
            {
                id: 'network-mapper',
                icon: 'ico-network',
                title: 'Start Network Mapper MCP',
                env: 'H263 (Linux)',
                tooltip: 'The Network Mapper MCP server enables recursive LLDP-based network discovery. It walks device neighbors to build a full topology map automatically. The MCP server must be running for the Network Mapper panel to work.',
                script: 'cd ~/network-mapper && npm start &',
                noCheck: true
            },
            {
                id: 'scaler-db',
                icon: 'ico-layers',
                title: 'Sync Scaler Device DB',
                env: 'H263 (Linux)',
                tooltip: 'The Scaler DB (operational.json) caches device serials, hostnames, management IPs, and last-seen timestamps. DNAAS discovery and NCC resolution rely on it. This pulls the latest device inventory from the Scaler system.',
                script: 'cd ~/SCALER && python3 -m scaler.wizard inventory --refresh',
                noCheck: true
            }
        ];

        const USAGE_TIPS = [
            { icon: 'ico-hand', title: 'Keyboard Shortcuts', desc: '<span class="helper-key">R</span> Refresh <span class="helper-key">D</span> DNAAS <span class="helper-key">B</span> BD Panel <span class="helper-key">T</span> Topologies <span class="helper-key">M</span> Minimap <span class="helper-key">G</span> Grid <span class="helper-key">L</span> Light/Dark <span class="helper-key">F</span> Fit View <span class="helper-key">C</span> Copy Style <span class="helper-key">Del</span> Delete' },
            { icon: 'ico-router', title: 'Place Devices', desc: 'Select a device type from the toolbar, then click on the canvas to place it. Hold Shift and click multiple times for continuous placement.' },
            { icon: 'ico-link', title: 'Create Links', desc: 'Click "Link" mode, then click the first device and then the second. Use the Link Table to fill in interface details. Hold Alt + click a device to quick-start link mode.' },
            { icon: 'ico-search', title: 'Packet Capture', desc: 'Click the magnifying glass icon on any link to open capture popup. Set your Mac IP, user, and password in the Packet-Capture section above. Enable "Remote Login" on Mac.' },
            { icon: 'ico-discover', title: 'DNAAS Discovery', desc: 'Press D or click DNAAS to open the discovery panel. Enter device name and run discovery to auto-populate the topology with real device data.' },
            { icon: 'ico-save', title: 'Save / Load', desc: 'Ctrl+S to quick-save. Use the Topologies dropdown (T key) to manage saved topologies across domains. Export as JSON or PNG.' },
            { icon: 'ico-palette', title: 'Style & Customize', desc: 'Click a device to open its per-device toolbar. Change colors, styles, labels, and fonts. Copy a style with C and paste it onto other devices with Shift+Click.' }
        ];

        scriptsContainer.innerHTML = '';
        const header = document.createElement('div');
        header.style.cssText = 'font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.6px;opacity:0.5;margin-bottom:6px;padding-left:4px;';
        header.textContent = 'Setup Scripts';
        scriptsContainer.appendChild(header);

        for (const s of SETUP_SCRIPTS) {
            const item = document.createElement('div');
            item.className = 'helper-item helper-script-item';

            const titleRow = document.createElement('div');
            titleRow.className = 'helper-title';
            titleRow.style.cssText = 'justify-content:space-between;';

            const left = document.createElement('span');
            left.style.cssText = 'display:flex;align-items:center;gap:5px;';
            left.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24"><use href="#${s.icon}"/></svg> ${s.title}`;

            const right = document.createElement('span');
            right.style.cssText = 'display:flex;align-items:center;gap:4px;';

            const envBadge = document.createElement('span');
            envBadge.className = 'helper-env-badge';
            envBadge.textContent = s.env;
            right.appendChild(envBadge);

            const helpBtn = document.createElement('span');
            helpBtn.className = 'helper-tooltip-trigger';
            helpBtn.textContent = '?';
            helpBtn.setAttribute('tabindex', '0');
            const tip = document.createElement('span');
            tip.className = 'helper-tooltip-text';
            tip.textContent = s.tooltip;
            helpBtn.appendChild(tip);
            right.appendChild(helpBtn);

            titleRow.appendChild(left);
            titleRow.appendChild(right);
            item.appendChild(titleRow);

            const codeRow = document.createElement('div');
            codeRow.className = 'helper-code-row';

            const code = document.createElement('code');
            code.className = 'helper-code';
            code.textContent = s.script;

            const copyBtn = document.createElement('button');
            copyBtn.className = 'helper-copy-btn';
            copyBtn.innerHTML = '<svg width="11" height="11" viewBox="0 0 24 24"><use href="#ico-copy"/></svg>';
            copyBtn.title = 'Copy to clipboard';
            copyBtn.addEventListener('click', () => {
                window.safeClipboardWrite(s.script).then(() => {
                    copyBtn.innerHTML = '<svg width="11" height="11" viewBox="0 0 24 24"><use href="#ico-check"/></svg>';
                    copyBtn.style.color = '#27ae60';
                    if (editor?.showToast) editor.showToast(`Copied "${s.title}" script`, 'success');
                    setTimeout(() => {
                        copyBtn.innerHTML = '<svg width="11" height="11" viewBox="0 0 24 24"><use href="#ico-copy"/></svg>';
                        copyBtn.style.color = '';
                    }, 2000);
                });
            });

            codeRow.appendChild(code);
            codeRow.appendChild(copyBtn);
            item.appendChild(codeRow);
            scriptsContainer.appendChild(item);
        }

        tipsContainer.innerHTML = '';
        const tipsHeader = document.createElement('div');
        tipsHeader.style.cssText = 'font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.6px;opacity:0.5;margin-bottom:6px;padding-left:4px;';
        tipsHeader.textContent = 'Usage Tips';
        tipsContainer.appendChild(tipsHeader);

        for (const t of USAGE_TIPS) {
            const item = document.createElement('div');
            item.className = 'helper-item';
            item.innerHTML = `<div class="helper-title"><svg width="12" height="12" viewBox="0 0 24 24"><use href="#${t.icon}"/></svg> ${t.title}</div><div class="helper-desc">${t.desc}</div>`;
            tipsContainer.appendChild(item);
        }
    }

};

console.log('[topology-toolbar-setup.js] ToolbarSetup loaded');
