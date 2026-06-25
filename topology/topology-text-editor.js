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

    /**
     * Commit user-entered text without treating an empty string as deletion.
     * Deleting a TB is handled only by explicit canvas delete actions.
     */
    _setTextValue: function(textObj, value) {
        if (!textObj || textObj.type !== 'text') return;
        const nextValue = value == null ? '' : String(value);
        textObj.text = nextValue;
        if (nextValue === '') {
            textObj._textCleared = true;
        } else if (textObj._textCleared) {
            delete textObj._textCleared;
        }
    },

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
                this._setTextValue(editor.editingText, e.target.value);
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
     * Show inline text editor overlay.
     *
     * Visual continuity contract -- the overlay's text glyphs must land on
     * the SAME screen pixels the canvas painted them on, with the same
     * font, weight, style, line-height, padding and content-area width.
     * Any mismatch causes a "jump" when entering/exiting edit mode.
     *
     * Canvas paint reference (topology-canvas-drawing.js drawText):
     *   ctx.font          = "<style> <weight> <size>px <family>"
     *   ctx.textAlign     = 'center'
     *   ctx.textBaseline  = 'middle'
     *   lineHeight        = fontSize * 1.3
     *   glyph block       = (w x h) centered on (text.x, text.y)
     *   background block  = (w + 2*P) x (h + 2*P) centered on (text.x, text.y)
     *                       where P = text.backgroundPadding ?? 8
     *
     * Overlay model (matches canvas exactly):
     *   - position centered on (text.x, text.y) screen coords (translate -50%)
     *   - padding = P * editor.zoom  (mirrors background block margin)
     *   - inner content area = (w * editor.zoom) -- wraps at same column
     *   - line-height = 1.3 (matches canvas)
     *   - border = 0; visible blue ring is a box-shadow OUTSIDE the content
     *     so it never consumes layout space (no wrap shift)
     *   - letter-spacing = 0 explicit (browser default; canvas implicit)
     *   - box-sizing: border-box so width/height include padding
     *
     * Polish + QA pass 2026-05-12.
     *
     * @param {Object} editor   - TopologyEditor instance
     * @param {Object} textObj  - Text object to edit
     * @param {Event}  event    - Triggering event (currently unused)
     * @param {Object} [options]
     * @param {boolean} [options.selectAll] - true: select all text on focus
     *        (typing replaces). false: caret at end (typing appends). When
     *        omitted, defaults to true for empty / placeholder "Text" boxes
     *        and false for boxes with real user content.
     */
    showInline: function(editor, textObj, event, options) {
        if (!textObj || textObj.type !== 'text') return;
        const opts = options || {};

        textObj._editing = true;
        this.hideInline(editor);
        editor.editingText = textObj;

        // Snapshot original text so hideInline only saves a state when
        // the user actually changed something. Avoids spurious undo
        // entries when the user just opens-and-closes the editor.
        editor._inlineEditorOriginalText = textObj.text == null ? '' : String(textObj.text);

        const rect = editor.canvas.getBoundingClientRect();
        const screenX = rect.left + textObj.x * editor.zoom + editor.panOffset.x;
        const screenY = rect.top + textObj.y * editor.zoom + editor.panOffset.y;

        const requestedFontSize = Number(textObj.fontSize) || 14;
        const scaledFontSize = requestedFontSize * editor.zoom;
        const fontFamily = textObj.fontFamily || 'Arial, sans-serif';
        // Canonical fontWeight/fontStyle fields win over the legacy
        // textObj.bold / textObj.italic booleans (kept as a fallback so
        // older saved sections still edit correctly).
        const fontWeight = textObj.fontWeight
            || (textObj.bold ? 'bold' : 'normal');
        const fontStyle = textObj.fontStyle
            || (textObj.italic ? 'italic' : 'normal');

        // Mirror the canvas's background padding exactly. Default is 8 world
        // units (4 for link-attached labels). Persist as paddingPx in screen
        // space for the textarea CSS.
        const paddingWorld = Number.isFinite(textObj.backgroundPadding)
            ? textObj.backgroundPadding
            : (textObj.linkId && textObj._onLinkLine === true ? 4 : 8);
        const paddingPx = Math.max(0, paddingWorld * editor.zoom);

        // Width model: when the user has edge-stretched the box, lock the
        // outer width so wrapping mirrors what drawText will paint after
        // commit. Inner content area = text.width * zoom; outer = inner +
        // 2*paddingPx. With box-sizing: border-box the textarea's `width`
        // CSS prop is the OUTER value.
        const hasManualWidth = Number.isFinite(textObj.width) && textObj.width > 0;
        const innerWidthPx = hasManualWidth ? Math.max(40, textObj.width * editor.zoom) : null;
        const lockedOuterWidth = innerWidthPx != null ? (innerWidthPx + 2 * paddingPx) : null;

        // Height model: when `_heightLocked === true` the user explicitly
        // dragged a vertical edge or corner -- honour `text.height` and let
        // the textarea scroll past it (the renderer clips with ellipsis on
        // the next paint). For auto-grow boxes we let the height grow
        // naturally via autoResize().
        const hasLockedHeight = textObj._heightLocked === true && Number.isFinite(textObj.height);
        const innerHeightPx = hasLockedHeight ? Math.max(24, textObj.height * editor.zoom) : null;
        const lockedOuterHeight = innerHeightPx != null ? (innerHeightPx + 2 * paddingPx) : null;

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
        textInput.dataset.inlineTextEditor = '1';
        textInput.style.cssText = `
            position: fixed;
            left: ${screenX}px;
            top: ${screenY}px;
            font-size: ${scaledFontSize}px;
            font-family: ${fontFamily};
            font-weight: ${fontWeight};
            font-style: ${fontStyle};
            line-height: 1.3;
            letter-spacing: 0;
            color: ${textObj.color || '#333333'};
            background: ${bgColor};
            border: 0;
            border-radius: 4px;
            padding: ${paddingPx}px;
            margin: 0;
            outline: none;
            box-shadow: 0 0 0 2px #3498db, 0 4px 16px rgba(52, 152, 219, 0.25);
            transform: translate(-50%, -50%) rotate(${textObj.rotation || 0}deg);
            transform-origin: center center;
            min-width: ${Math.max(40, scaledFontSize * 2)}px;
            min-height: ${Math.max(scaledFontSize * 1.3 + 2 * paddingPx, scaledFontSize + 12)}px;
            resize: none;
            overflow: ${hasLockedHeight ? 'auto' : 'hidden'};
            z-index: 10000;
            text-align: ${textObj.textAlign || 'center'};
            box-sizing: border-box;
            white-space: pre-wrap;
            word-wrap: break-word;
            overflow-wrap: break-word;
            word-break: normal;
            caret-color: #3498db;
        `;

        document.body.appendChild(textInput);
        editor._inlineTextEditor = textInput;

        // Auto-resize textarea outer dimensions so the inner content area
        // stays equal to the canvas glyph block. Two regimes:
        //
        //  - Manual width AND locked height: clamp BOTH dimensions; the
        //    textarea scrolls internally if content overflows (matches
        //    the renderer's clip-with-ellipsis behaviour, just live).
        //
        //  - Manual width only: lock outer width, grow outer height to fit
        //    wrapped lines.
        //
        //  - Auto-grow (no width set): outer width grows to longest line,
        //    outer height grows to N lines. Mirrors the legacy un-stretched
        //    text-box behaviour.
        const autoResize = () => {
            textInput.style.height = 'auto';
            const measureMaxWidth = innerWidthPx || 500;
            const measure = document.createElement('div');
            measure.style.cssText = `
                position: absolute; visibility: hidden;
                top: -10000px; left: -10000px;
                white-space: pre-wrap;
                word-wrap: break-word;
                overflow-wrap: break-word;
                word-break: normal;
                font-size: ${scaledFontSize}px;
                font-family: ${fontFamily};
                font-weight: ${fontWeight};
                font-style: ${fontStyle};
                line-height: 1.3;
                letter-spacing: 0;
                padding: 0;
                box-sizing: border-box;
                max-width: ${measureMaxWidth}px;
                ${innerWidthPx ? `width: ${innerWidthPx}px;` : ''}
            `;
            // Trailing zero-width space ensures empty lines / trailing
            // newline are measured (the textarea's own caret needs the row).
            measure.textContent = (textInput.value || ' ') + '\u200b';
            document.body.appendChild(measure);
            const measuredInnerW = innerWidthPx || Math.max(40, measure.offsetWidth);
            const measuredInnerH = Math.max(
                Math.ceil(scaledFontSize * 1.3),
                measure.offsetHeight
            );
            document.body.removeChild(measure);

            const outerW = measuredInnerW + 2 * paddingPx;
            const outerH = hasLockedHeight
                ? lockedOuterHeight
                : (measuredInnerH + 2 * paddingPx);

            textInput.style.width = `${outerW}px`;
            textInput.style.height = `${outerH}px`;
        };

        autoResize();

        // Decide select-all vs caret-at-end. Empty boxes and placeholder
        // "Text" boxes auto-select-all so the first keystroke replaces the
        // dummy content. Existing user content keeps the caret at the end
        // (less surprising than full select on every double-click).
        const initialValue = textObj.text == null ? '' : String(textObj.text);
        const isPlaceholder = initialValue === '' || initialValue === 'Text';
        const shouldSelectAll = (opts.selectAll === true)
            || (opts.selectAll !== false && isPlaceholder);

        // Focus + caret placement: setTimeout(0) instead of (10) -- the
        // browser still completes layout before the focus runs, but the
        // visible "no caret yet" gap shrinks. The 10ms delay used to be a
        // workaround for a race that's no longer relevant after the
        // mousedown click-outside arming was moved behind a 100ms guard.
        setTimeout(() => {
            textInput.focus();
            if (shouldSelectAll) {
                textInput.select();
            } else {
                const len = textInput.value.length;
                try { textInput.setSelectionRange(len, len); } catch (_) { /* noop */ }
            }
        }, 0);

        textInput.addEventListener('input', () => {
            if (editor.editingText) {
                this._setTextValue(editor.editingText, textInput.value);
                autoResize();
                // RAF-coalesce paints during typing. Burst keystrokes used
                // to fire one synchronous editor.draw() per char, which
                // monopolised the main thread on long passages and made
                // the auto-grow re-flow look "chunky". scheduleDraw() folds
                // every pending paint into one per RAF; the textarea
                // itself updates instantly via the browser's native input
                // handling, so users still see their characters with
                // zero perceptible latency. Smoothness pass 2026-05-12.
                if (editor.scheduleDraw) editor.scheduleDraw();
                else editor.draw();
            }
        });

        // Handle keyboard
        textInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                e.preventDefault();
                this.hideInline(editor);
            } else if (e.key === 'Enter' && e.shiftKey) {
                // Allow shift+enter for newlines (default textarea behaviour).
            } else if (e.key === 'Enter') {
                e.preventDefault();
                this.hideInline(editor);
            }
            // All other keys (arrows, Backspace, Delete, Cmd-A, Cmd-Z, etc.)
            // are handled natively by the textarea. The global keyboard
            // shortcut handler in topology-keyboard.js already gates on
            // _isEditableShortcutTarget, so canvas-level shortcuts (Delete
            // selected element, Cmd-Z canvas undo, arrow-pan, etc.) cannot
            // fire while the textarea has focus.
        });

        // Click outside handler -- commit on any document mousedown whose
        // target is not the textarea itself (canvas background, another
        // canvas object, sidebar, etc.). Armed after a 100ms guard so the
        // mousedown that opened the editor doesn't immediately close it.
        editor._inlineEditorClickOutside = (e) => {
            if (editor._inlineTextEditor && e.target !== editor._inlineTextEditor) {
                this.hideInline(editor);
            }
        };

        setTimeout(() => {
            document.addEventListener('mousedown', editor._inlineEditorClickOutside);
        }, 100);

        // Safety fallback -- if the textarea got removed externally without
        // hideInline being called (ought never happen, but guard anyway),
        // restore the text visibility on the next tick.
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
     * Update inline editor position when canvas pans/zooms.
     *
     * Refreshes ALL canonical paint props (font, color, background,
     * padding, line-height) so the overlay continues to match the canvas
     * exactly even if the user changed style via toolbar mid-edit. Polish
     * + QA pass 2026-05-12 -- previously only left/top/font-size/rotation
     * were refreshed, which caused style drift on color/background changes
     * during edit.
     *
     * @param {Object} editor - TopologyEditor instance
     */
    updateInlinePosition: function(editor) {
        if (!editor._inlineTextEditor || !editor.editingText) return;

        const textObj = editor.editingText;
        const el = editor._inlineTextEditor;
        const rect = editor.canvas.getBoundingClientRect();
        const screenX = rect.left + textObj.x * editor.zoom + editor.panOffset.x;
        const screenY = rect.top + textObj.y * editor.zoom + editor.panOffset.y;
        const requestedFontSize = Number(textObj.fontSize) || 14;
        const scaledFontSize = requestedFontSize * editor.zoom;
        const fontFamily = textObj.fontFamily || 'Arial, sans-serif';
        const fontWeight = textObj.fontWeight || (textObj.bold ? 'bold' : 'normal');
        const fontStyle = textObj.fontStyle || (textObj.italic ? 'italic' : 'normal');
        const paddingWorld = Number.isFinite(textObj.backgroundPadding)
            ? textObj.backgroundPadding
            : (textObj.linkId && textObj._onLinkLine === true ? 4 : 8);
        const paddingPx = Math.max(0, paddingWorld * editor.zoom);

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

        el.style.left = `${screenX}px`;
        el.style.top = `${screenY}px`;
        el.style.fontSize = `${scaledFontSize}px`;
        el.style.fontFamily = fontFamily;
        el.style.fontWeight = fontWeight;
        el.style.fontStyle = fontStyle;
        el.style.color = textObj.color || '#333333';
        el.style.background = bgColor;
        el.style.padding = `${paddingPx}px`;
        el.style.lineHeight = '1.3';
        el.style.transform = `translate(-50%, -50%) rotate(${textObj.rotation || 0}deg)`;
    },

    /**
     * Hide inline text editor.
     *
     * Polish + QA pass 2026-05-12: only saves a state when the text
     * actually changed (snapshot taken in showInline). Marks the textObj
     * `_mouseReleasedAfterSelection = true` so the very next mouse-down on
     * a resize handle starts the resize directly instead of needing a
     * second click cycle to "arm" the handle hit-test.
     *
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

        const textObj = editor.editingText;
        if (textObj) {
            textObj._editing = false;
            // Arm the resize-handle hit-test so the next mouse-down on a
            // dot or edge-zone band starts the resize without needing a
            // second click. The flag is consumed by topology-mouse-down.js
            // resize gate.
            textObj._mouseReleasedAfterSelection = true;

            const originalText = editor._inlineEditorOriginalText;
            const currentText = textObj.text == null ? '' : String(textObj.text);
            if (typeof originalText === 'string' && originalText !== currentText) {
                editor.saveState();
                if (editor.scheduleAutoSave) editor.scheduleAutoSave();
            }
        }
        editor._inlineEditorOriginalText = null;

        editor.editingText = null;
        // RAF-coalesce the commit paint so the textarea-removal frame
        // and the canvas re-render happen in the SAME RAF tick. With a
        // synchronous editor.draw() the browser sometimes painted the
        // canvas (without the text overlay) on one frame and removed
        // the textarea on the next, causing a 16 ms visual gap. Using
        // requestDraw avoids that two-frame split. Smoothness pass
        // 2026-05-12.
        if (editor.requestDraw) editor.requestDraw();
        else editor.draw();
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
