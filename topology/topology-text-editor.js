/**
 * topology-text-editor.js - Text Editor Module
 *
 * Extracted from topology.js for modular architecture.
 * Contains text editing modal and inline editor functions.
 *
 * @version 1.0.0
 * @date 2026-02-04
 */

'use strict';

window.TextEditorModule = {

    // Store live preview handlers
    _livePreviewHandlers: {},

    // =========================================================================
    // MODAL TEXT EDITOR
    // =========================================================================

    /**
     * Show the text editor modal for a text object
     * @param {Object} editor - TopologyEditor instance
     * @param {Object} textObj - Text object to edit
     */
    show: function(editor, textObj) {
        if (!textObj) textObj = editor.selectedObject;
        if (!textObj || textObj.type !== 'text') return;
        
        // Hide other editors first
        editor.hideTextSelectionToolbar();
        this.hideInline(editor);
        
        editor.editingText = textObj;
        
        // Set editor values with null checks
        const editorTextContent = document.getElementById('editor-text-content');
        const editorFontSize = document.getElementById('editor-font-size');
        const editorTextColor = document.getElementById('editor-text-color');
        const editorRotation = document.getElementById('editor-rotation');
        const editorRotationValue = document.getElementById('editor-rotation-value');
        const editorTextAlign = document.getElementById('editor-text-align');
        
        if (editorTextContent) editorTextContent.value = textObj.text || '';
        if (editorFontSize) editorFontSize.value = textObj.fontSize || 14;
        if (editorTextColor) editorTextColor.value = textObj.color || '#333333';
        if (editorRotation) editorRotation.value = textObj.rotation || 0;
        if (editorRotationValue) editorRotationValue.textContent = (textObj.rotation || 0) + '°';
        if (editorTextAlign) editorTextAlign.value = textObj.textAlign || 'center';
        
        // Initialize background color controls
        const showBgCheckbox = document.getElementById('editor-show-background');
        const bgColorInput = document.getElementById('editor-bg-color');
        if (showBgCheckbox) {
            showBgCheckbox.checked = textObj.showBackground !== false;
        }
        if (bgColorInput) {
            bgColorInput.value = textObj.backgroundColor || (editor.darkMode ? '#1a1a1a' : '#f5f5f5');
        }
        
        // Setup live preview listeners
        this._setupLivePreview(editor, textObj);
        
        // Setup palette color clicks for text color
        document.querySelectorAll('.text-palette-color').forEach(swatch => {
            swatch.onclick = () => {
                if (editor.editingText) {
                    const color = swatch.dataset.color;
                    editor.editingText.color = color;
                    document.getElementById('editor-text-color').value = color;
                    editor.addRecentColor(color);
                    editor.draw();
                }
            };
        });
        
        // Setup palette color clicks for background color
        document.querySelectorAll('#bg-color-palette .palette-color').forEach(swatch => {
            swatch.onclick = () => {
                if (editor.editingText) {
                    const color = swatch.dataset.color;
                    editor.editingText.backgroundColor = color;
                    if (color !== 'transparent') {
                        document.getElementById('editor-bg-color').value = color;
                        editor.addRecentColor(color);
                    }
                    editor.draw();
                }
            };
        });
        
        // Setup custom color picker buttons
        const textColorPickerBtn = document.getElementById('text-color-picker-btn');
        const bgColorPickerBtn = document.getElementById('bg-color-picker-btn');
        
        if (textColorPickerBtn) {
            textColorPickerBtn.onclick = () => {
                document.getElementById('editor-text-color').click();
            };
        }
        if (bgColorPickerBtn) {
            bgColorPickerBtn.onclick = () => {
                document.getElementById('editor-bg-color').click();
            };
        }
        
        // Setup opacity slider
        const bgOpacity = document.getElementById('editor-bg-opacity');
        const bgOpacityValue = document.getElementById('editor-bg-opacity-value');
        if (bgOpacity) {
            bgOpacity.value = textObj.backgroundOpacity !== undefined ? textObj.backgroundOpacity : 95;
            if (bgOpacityValue) bgOpacityValue.textContent = bgOpacity.value + '%';
            bgOpacity.oninput = () => {
                if (editor.editingText) {
                    editor.editingText.backgroundOpacity = parseInt(bgOpacity.value);
                    if (bgOpacityValue) bgOpacityValue.textContent = bgOpacity.value + '%';
                    editor.draw();
                }
            };
        }
        
        // Update recent colors display
        editor.updateRecentColorsUI();
        
        const modal = document.getElementById('text-editor-modal');
        
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
    },

    /**
     * Setup live preview event listeners
     * @param {Object} editor - TopologyEditor instance
     * @param {Object} textObj - Text object being edited
     */
    _setupLivePreview: function(editor, textObj) {
        const textContent = document.getElementById('editor-text-content');
        const fontSize = document.getElementById('editor-font-size');
        const textColor = document.getElementById('editor-text-color');
        const rotation = document.getElementById('editor-rotation');
        const showBgCheckbox = document.getElementById('editor-show-background');
        const bgColorInput = document.getElementById('editor-bg-color');
        
        // Remove old listeners
        this._removeLivePreviewListeners();
        
        // Create new handlers
        this._livePreviewHandlers.text = (e) => {
            if (editor.editingText) {
                editor.editingText.text = e.target.value;
                editor.draw();
            }
        };
        this._livePreviewHandlers.fontSize = (e) => {
            if (editor.editingText) {
                editor.editingText.fontSize = parseInt(e.target.value) || 14;
                editor.draw();
            }
        };
        this._livePreviewHandlers.color = (e) => {
            if (editor.editingText) {
                editor.editingText.color = e.target.value;
                editor.addRecentColor(e.target.value);
                editor.draw();
            }
        };
        this._livePreviewHandlers.rotation = (e) => {
            if (editor.editingText) {
                editor.editingText.rotation = parseInt(e.target.value) || 0;
                editor.draw();
            }
        };
        this._livePreviewHandlers.showBg = (e) => {
            if (editor.editingText) {
                editor.editingText.showBackground = e.target.checked;
                if (editor.editingText.linkId) {
                    editor.updateAdjacentTextPosition(editor.editingText);
                }
                editor.draw();
            }
        };
        this._livePreviewHandlers.bgColor = (e) => {
            if (editor.editingText) {
                editor.editingText.backgroundColor = e.target.value;
                editor.addRecentColor(e.target.value);
                editor.draw();
            }
        };
        
        // Add listeners
        if (textContent) textContent.addEventListener('input', this._livePreviewHandlers.text);
        if (fontSize) fontSize.addEventListener('input', this._livePreviewHandlers.fontSize);
        if (textColor) textColor.addEventListener('input', this._livePreviewHandlers.color);
        if (rotation) rotation.addEventListener('input', this._livePreviewHandlers.rotation);
        if (showBgCheckbox) showBgCheckbox.addEventListener('change', this._livePreviewHandlers.showBg);
        if (bgColorInput) bgColorInput.addEventListener('input', this._livePreviewHandlers.bgColor);
    },

    /**
     * Remove live preview event listeners
     */
    _removeLivePreviewListeners: function() {
        const textContent = document.getElementById('editor-text-content');
        const fontSize = document.getElementById('editor-font-size');
        const textColor = document.getElementById('editor-text-color');
        const rotation = document.getElementById('editor-rotation');
        const showBgCheckbox = document.getElementById('editor-show-background');
        const bgColorInput = document.getElementById('editor-bg-color');
        
        if (textContent && this._livePreviewHandlers.text) {
            textContent.removeEventListener('input', this._livePreviewHandlers.text);
        }
        if (fontSize && this._livePreviewHandlers.fontSize) {
            fontSize.removeEventListener('input', this._livePreviewHandlers.fontSize);
        }
        if (textColor && this._livePreviewHandlers.color) {
            textColor.removeEventListener('input', this._livePreviewHandlers.color);
        }
        if (rotation && this._livePreviewHandlers.rotation) {
            rotation.removeEventListener('input', this._livePreviewHandlers.rotation);
        }
        if (showBgCheckbox && this._livePreviewHandlers.showBg) {
            showBgCheckbox.removeEventListener('change', this._livePreviewHandlers.showBg);
        }
        if (bgColorInput && this._livePreviewHandlers.bgColor) {
            bgColorInput.removeEventListener('input', this._livePreviewHandlers.bgColor);
        }
    },

    /**
     * Hide the text editor modal
     * @param {Object} editor - TopologyEditor instance
     */
    hide: function(editor) {
        console.log('TextEditorModule.hide() called');
        
        // Remove live preview listeners
        this._removeLivePreviewListeners();
        
        const modal = document.getElementById('text-editor-modal');
        if (!modal) {
            console.error('Text editor modal element not found!');
            return;
        }
        
        modal.classList.remove('show');
        
        // Clear editing reference
        editor.editingText = null;
        editor.draw();
    },

    /**
     * Apply text editor changes
     * @param {Object} editor - TopologyEditor instance
     */
    apply: function(editor) {
        if (!editor.editingText) return;
        
        // Values are already applied via live preview
        // Just save state and hide modal
        editor.saveState();
        editor.updatePropertiesPanel();
        this.hide(editor);
    },

    // =========================================================================
    // INLINE TEXT EDITOR
    // =========================================================================

    /**
     * Show inline text editor overlay
     * @param {Object} editor - TopologyEditor instance
     * @param {Object} textObj - Text object to edit
     * @param {Event} event - Triggering event
     */
    showInline: function(editor, textObj, event) {
        if (!textObj || textObj.type !== 'text') return;
        
        textObj._editing = true;
        this.hideInline(editor);
        editor.editingText = textObj;
        
        const rect = editor.canvas.getBoundingClientRect();
        const screenX = rect.left + textObj.x * editor.zoom + editor.panOffset.x;
        const screenY = rect.top + textObj.y * editor.zoom + editor.panOffset.y;
        
        const scaledFontSize = (textObj.fontSize || 14) * editor.zoom;
        const fontFamily = textObj.fontFamily || 'Arial, sans-serif';
        const fontWeight = textObj.bold ? 'bold' : 'normal';
        const fontStyle = textObj.italic ? 'italic' : 'normal';

        let bgColor = 'transparent';
        if (textObj.showBackground !== false) {
            const raw = textObj.backgroundColor || (editor.darkMode ? '#1a1a1a' : '#f5f5f5');
            const opacity = textObj.backgroundOpacity != null ? textObj.backgroundOpacity : 1;
            if (opacity < 1 && raw.startsWith('#') && raw.length >= 7) {
                const r = parseInt(raw.slice(1, 3), 16);
                const g = parseInt(raw.slice(3, 5), 16);
                const b = parseInt(raw.slice(5, 7), 16);
                bgColor = `rgba(${r},${g},${b},${opacity})`;
            } else {
                bgColor = raw;
            }
        }

        const textInput = document.createElement('textarea');
        textInput.value = textObj.text || '';
        textInput.style.cssText = `
            position: fixed;
            left: ${screenX}px;
            top: ${screenY}px;
            font-size: ${scaledFontSize}px;
            font-family: ${fontFamily};
            font-weight: ${fontWeight};
            font-style: ${fontStyle};
            line-height: 1.35;
            color: ${textObj.color || '#333333'};
            background: ${bgColor};
            border: 2px solid #3498db;
            border-radius: 4px;
            padding: 4px 8px;
            outline: none;
            transform: translate(-50%, -50%) rotate(${textObj.rotation || 0}deg);
            transform-origin: center center;
            min-width: 60px;
            min-height: ${Math.round(scaledFontSize * 1.6)}px;
            resize: none;
            overflow: hidden;
            z-index: 10000;
            text-align: ${textObj.textAlign || 'center'};
            box-sizing: border-box;
            white-space: pre-wrap;
            word-wrap: break-word;
            caret-color: #3498db;
        `;

        document.body.appendChild(textInput);
        editor._inlineTextEditor = textInput;

        // Auto-resize textarea to fit content
        const autoResize = () => {
            textInput.style.height = 'auto';
            textInput.style.width = 'auto';
            const measure = document.createElement('div');
            measure.style.cssText = `
                position: absolute; visibility: hidden; white-space: pre-wrap;
                word-wrap: break-word; font-size: ${scaledFontSize}px;
                font-family: ${fontFamily}; font-weight: ${fontWeight};
                font-style: ${fontStyle}; line-height: 1.35;
                padding: 4px 8px; box-sizing: border-box; max-width: 500px;
            `;
            measure.textContent = (textInput.value || ' ') + '\u200b';
            document.body.appendChild(measure);
            const w = Math.max(60, measure.offsetWidth + 4);
            const h = Math.max(Math.round(scaledFontSize * 1.6), measure.offsetHeight + 4);
            document.body.removeChild(measure);
            textInput.style.width = `${w}px`;
            textInput.style.height = `${h}px`;
        };

        autoResize();

        setTimeout(() => {
            textInput.focus();
            textInput.select();
        }, 10);
        
        textInput.addEventListener('input', () => {
            if (editor.editingText) {
                editor.editingText.text = textInput.value;
                autoResize();
                editor.draw();
            }
        });
        
        // Handle keyboard
        textInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                e.preventDefault();
                this.hideInline(editor);
            } else if (e.key === 'Enter' && e.shiftKey) {
                // Allow shift+enter for newlines
            } else if (e.key === 'Enter') {
                e.preventDefault();
                this.hideInline(editor);
            }
        });
        
        // Click outside handler
        editor._inlineEditorClickOutside = (e) => {
            if (editor._inlineTextEditor && e.target !== editor._inlineTextEditor) {
                this.hideInline(editor);
            }
        };
        
        setTimeout(() => {
            document.addEventListener('mousedown', editor._inlineEditorClickOutside);
        }, 100);
        
        // Safety fallback
        editor._inlineEditorFallback = setTimeout(() => {
            if (textObj._editing && !document.body.contains(editor._inlineTextEditor)) {
                console.warn('Inline editor disappeared unexpectedly, restoring text visibility');
                textObj._editing = false;
                editor.editingText = null;
                editor._inlineTextEditor = null;
                editor.draw();
            }
        }, 500);
    },

    /**
     * Update inline editor position when canvas pans/zooms
     * @param {Object} editor - TopologyEditor instance
     */
    updateInlinePosition: function(editor) {
        if (!editor._inlineTextEditor || !editor.editingText) return;
        
        const textObj = editor.editingText;
        const rect = editor.canvas.getBoundingClientRect();
        const screenX = rect.left + textObj.x * editor.zoom + editor.panOffset.x;
        const screenY = rect.top + textObj.y * editor.zoom + editor.panOffset.y;
        const scaledFontSize = (textObj.fontSize || 14) * editor.zoom;
        
        editor._inlineTextEditor.style.left = `${screenX}px`;
        editor._inlineTextEditor.style.top = `${screenY}px`;
        editor._inlineTextEditor.style.fontSize = `${scaledFontSize}px`;
        editor._inlineTextEditor.style.transform = `translate(-50%, -50%) rotate(${textObj.rotation || 0}deg)`;
    },

    /**
     * Hide inline text editor
     * @param {Object} editor - TopologyEditor instance
     */
    hideInline: function(editor) {
        // Clear fallback safety timer
        if (editor._inlineEditorFallback) {
            clearTimeout(editor._inlineEditorFallback);
            editor._inlineEditorFallback = null;
        }
        
        if (editor._inlineTextEditor) {
            editor._inlineTextEditor.remove();
            editor._inlineTextEditor = null;
        }
        
        if (editor._inlineEditorClickOutside) {
            document.removeEventListener('mousedown', editor._inlineEditorClickOutside);
            editor._inlineEditorClickOutside = null;
        }
        
        if (editor.editingText) {
            editor.editingText._editing = false;
            editor.saveState();
        }
        
        editor.editingText = null;
        editor.draw();
    },

    // =========================================================================
    // INLINE DEVICE RENAME EDITOR
    // =========================================================================

    /**
     * Update inline device rename position when canvas pans/zooms
     */
    _getLabelParams: function(editor, device) {
        const rect = editor.canvas.getBoundingClientRect();
        const style = device.visualStyle || 'circle';
        const isClassic = style === 'classic';

        let labelOffsetY = 0;
        if (isClassic)       labelOffsetY = device.radius * 0.6 * 0.4;
        else if (style === 'hex')    labelOffsetY = device.radius * 0.85;
        else if (style === 'simple') labelOffsetY = device.radius * 1.15;
        else if (style === 'server') labelOffsetY = device.radius * 1.05;

        const rotRad = (device.rotation || 0) * Math.PI / 180;
        const labelWorldX = device.x + (-labelOffsetY * Math.sin(rotRad));
        const labelWorldY = device.y + (labelOffsetY * Math.cos(rotRad));
        const screenX = labelWorldX * editor.zoom + editor.panOffset.x + rect.left;
        const screenY = labelWorldY * editor.zoom + editor.panOffset.y + rect.top;

        const fontSize = isClassic
            ? (device.labelSize || Math.max(10, Math.min(device.radius * 0.35, 22)))
            : (device.labelSize || Math.max(12, Math.min(device.radius * 0.5, 36)));
        const scaledFontSize = fontSize * editor.zoom;
        const fontFamily = device.fontFamily || editor.defaultDeviceFontFamily || 'Inter, sans-serif';
        const fontWeight = isClassic ? 'bold' : (device.fontWeight || '600');

        let textColor, strokeColor;
        if (isClassic) {
            textColor = device.labelColor || '#ffffff';
            strokeColor = 'rgba(0,0,0,0.6)';
        } else {
            textColor = device.labelColor || (editor.darkMode ? '#ECF0F1' : '#0d1b2a');
            if (device.labelOutlineColor === 'none') {
                strokeColor = null;
            } else if (device.labelOutlineColor) {
                strokeColor = device.labelOutlineColor;
            } else {
                strokeColor = editor.darkMode ? 'rgba(13,27,42,0.98)' : 'rgba(255,255,255,1)';
            }
        }

        const strokePx = strokeColor ? Math.max(1, scaledFontSize * 0.14) : 0;

        return { screenX, screenY, scaledFontSize, fontFamily, fontWeight, textColor, strokeColor, strokePx, isClassic, style };
    },

    updateDeviceRenamePosition: function(editor) {
        if (!editor._inlineDeviceRename || !editor._renamingDevice) return;
        const p = this._getLabelParams(editor, editor._renamingDevice);
        const el = editor._inlineDeviceRename;
        el.style.left = `${p.screenX}px`;
        el.style.top = `${p.screenY}px`;
        el.style.fontSize = `${p.scaledFontSize}px`;
        el.style.transform = `translate(-50%, -50%) rotate(${editor._renamingDevice.rotation || 0}deg)`;
        if (p.strokeColor && p.strokePx > 0) {
            el.style.webkitTextStroke = `${p.strokePx}px ${p.strokeColor}`;
        }
    },

    /**
     * Show inline device rename input
     * @param {Object} editor - TopologyEditor instance
     * @param {Object} device - Device object to rename
     */
    showDeviceRename: function(editor, device) {
        if (!device || device.type !== 'device') return;

        editor.hideDeviceSelectionToolbar();
        this.hideDeviceRename(editor);
        editor._renamingDevice = device;

        try {
            const p = this._getLabelParams(editor, device);

            const input = document.createElement('input');
            input.type = 'text';
            input.id = 'inline-device-rename';
            input.value = device.label || '';
            input.placeholder = device.deviceType === 'router' ? 'NCP' : 'S';
            input.maxLength = 30;

            const strokeCSS = (p.strokeColor && p.strokePx > 0)
                ? `-webkit-text-stroke: ${p.strokePx}px ${p.strokeColor}; paint-order: stroke fill;`
                : '';

            input.style.cssText = `
                position: fixed;
                left: ${p.screenX}px;
                top: ${p.screenY}px;
                transform: translate(-50%, -50%) rotate(${device.rotation || 0}deg);
                transform-origin: center center;
                z-index: 10000;
                background: transparent;
                border: none;
                padding: 0;
                margin: 0;
                color: ${p.textColor};
                font-size: ${p.scaledFontSize}px;
                font-family: ${p.fontFamily};
                font-weight: ${p.fontWeight};
                text-align: center;
                outline: none;
                min-width: 20px;
                box-sizing: content-box;
                caret-color: #3498db;
                letter-spacing: 0.3px;
                ${strokeCSS}
            `;

            document.body.appendChild(input);
            editor._inlineDeviceRename = input;
            device._renaming = true;

            input.focus();
            input.select();

            const autoResize = () => {
                const span = document.createElement('span');
                span.style.cssText = `
                    position: absolute; visibility: hidden; white-space: pre;
                    font-size: ${p.scaledFontSize}px; font-family: ${p.fontFamily};
                    font-weight: ${p.fontWeight}; letter-spacing: 0.3px;
                `;
                span.textContent = input.value || input.placeholder;
                document.body.appendChild(span);
                input.style.width = `${Math.max(20, span.offsetWidth + 4)}px`;
                document.body.removeChild(span);
            };
            autoResize();

            input.addEventListener('input', () => {
                if (editor._renamingDevice) {
                    editor._renamingDevice.label = input.value;
                    if (window.checkDeviceMismatchLive) {
                        window.checkDeviceMismatchLive(editor._renamingDevice);
                    }
                    autoResize();
                    editor.draw();
                }
            });

            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === 'Escape') {
                    e.preventDefault();
                    this.hideDeviceRename(editor);
                }
            });

            const self = this;
            editor._deviceRenameClickOutside = (e) => {
                if (editor._inlineDeviceRename && e.target !== editor._inlineDeviceRename) {
                    self.hideDeviceRename(editor);
                }
            };
            setTimeout(() => document.addEventListener('mousedown', editor._deviceRenameClickOutside), 100);

            editor.draw();

            if (editor.debugger) {
                editor.debugger.logInfo(`Inline device rename opened for "${device.label}"`);
            }
        } catch (e) {
            console.error('Failed to show inline device rename:', e);
            delete device._renaming;
            editor._renamingDevice = null;
            editor._inlineDeviceRename = null;
            editor.draw();
        }
    },

    /**
     * Hide inline device rename input
     * @param {Object} editor - TopologyEditor instance
     */
    hideDeviceRename: function(editor) {
        if (editor._inlineDeviceRename) {
            editor._inlineDeviceRename.remove();
            editor._inlineDeviceRename = null;
        }
        
        if (editor._deviceRenameClickOutside) {
            document.removeEventListener('mousedown', editor._deviceRenameClickOutside);
            editor._deviceRenameClickOutside = null;
        }
        
        const device = editor._renamingDevice;
        editor._renamingDevice = null;
        
        if (device) {
            delete device._renaming;
            if (window.checkDeviceMismatchLive) {
                window.checkDeviceMismatchLive(device);
            }
            editor.selectedObject = device;
            editor.selectedObjects = [device];
            editor.saveState();
            const mismatchPopup = document.getElementById('mismatch-badge-popup');
            if (!mismatchPopup) {
                editor.showDeviceSelectionToolbar(device);
            }
        }
        
        editor.draw();
    }
};

console.log('[topology-text-editor.js] TextEditorModule loaded');
