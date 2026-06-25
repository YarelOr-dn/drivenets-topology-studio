/**
 * topology-color-popups.js - Color Palette Popup UI Components
 *
 * Extracted from topology.js for modular architecture. Renders the
 * "Quick Colors" popup that appears for devices, links, and text. The
 * popup is opened from object toolbars and from the right-click
 * context menu via `editor.showColorPalettePopupFromToolbar` and
 * `editor.showColorPalettePopup`.
 *
 * 2026-05-12 [recent-colors polish + split-color]:
 *   - Recent-color cap raised to 8 (was 4); user-editable in
 *     `editor.recentColorsCap`.
 *   - Pinned colors row floats above the MRU row; pinned colors
 *     persist in localStorage under the per-user prefix and are never
 *     evicted by the MRU rotation.
 *   - Right-click on any pinned / recent swatch opens a small context
 *     menu with Pin/Unpin and Remove (see `showSwatchContextMenu`).
 *   - Each swatch is keyboard accessible (tabindex=0, Enter/Space pick).
 *   - All emoji removed; section labels use SVG icons via `appIcon()`.
 *   - For devices: a Solid / Split toggle gates between the legacy
 *     full-grid view and a two-column Left | Right side picker; each
 *     side surfaces a "Suggested: <swatch>" chip when one of the
 *     device's neighbours on that side has a >=50% dominant color
 *     (see `editor.getNeighborColorSuggestion`). The Split column
 *     also offers a swap button and a "Make Solid" affordance per
 *     the user-facing spec.
 *   - Hover / active / focus states honour the DriveNets brand
 *     palette (--dn-orange / --dn-cyan / --dn-navy-deep) via classes
 *     defined in styles.css.
 *
 * The non-device flows (link, text) are unchanged: they continue to
 * render the legacy single-grid popup.
 *
 * @version 2.0.0
 * @date 2026-05-12
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

    // ------------------------------------------------------------------
    // Section helpers
    // ------------------------------------------------------------------
    _sectionLabel(iconKey, text) {
        const label = document.createElement('div');
        label.className = 'color-popup-section-label';
        const iconHtml = (typeof appIcon === 'function') ? appIcon(iconKey) : '';
        label.innerHTML = `${iconHtml}<span>${text}</span>`;
        return label;
    },

    _container(layoutHint) {
        const div = document.createElement('div');
        div.className = 'color-popup-row ' + (layoutHint || '');
        return div;
    },

    // ------------------------------------------------------------------
    // Recent + pinned swatch row builder
    // ------------------------------------------------------------------
    _appendRecentRow(popup, editor, applyFn, opts) {
        opts = opts || {};
        const pinned = Array.isArray(editor.pinnedColors) ? editor.pinnedColors : [];
        const recent = Array.isArray(editor.recentColors) ? editor.recentColors : [];

        const cap = Math.max(1, (editor.recentColorsCap || 8));
        const visibleRecent = recent.slice(0, cap);

        if (pinned.length === 0 && visibleRecent.length === 0) return;

        // Combine but tag each entry so the swatch builder can decorate.
        const entries = [];
        pinned.forEach(c => entries.push({ color: c, pinned: true }));
        visibleRecent.forEach(c => entries.push({ color: c, pinned: false }));

        const label = this._sectionLabel('palette',
            (pinned.length ? 'Pinned + Recent' : 'Recent'));
        popup.appendChild(label);

        const row = this._container('color-popup-row--flex');
        entries.forEach(({ color, pinned: isPinned }) => {
            const swatch = this._createSwatch(color, opts.size || 32, () => applyFn(color), {
                isActive: opts.activeColor && color.toLowerCase() === String(opts.activeColor).toLowerCase(),
                isPinned: isPinned,
                onContext: (clientX, clientY) =>
                    this.showSwatchContextMenu(editor, color, clientX, clientY),
            });
            row.appendChild(swatch);
        });
        popup.appendChild(row);
    },

    // ------------------------------------------------------------------
    // Right-click context menu for a swatch (Pin/Unpin/Remove)
    // ------------------------------------------------------------------
    showSwatchContextMenu(editor, color, clientX, clientY) {
        const existing = document.getElementById('color-swatch-context-menu');
        if (existing) existing.remove();

        if (!editor || !color) return;

        const menu = document.createElement('div');
        menu.id = 'color-swatch-context-menu';
        menu.className = 'color-swatch-context-menu';
        menu.style.left = clientX + 'px';
        menu.style.top = clientY + 'px';

        const isPinned = typeof editor.isColorPinned === 'function'
            ? editor.isColorPinned(color)
            : false;

        const makeItem = (label, iconKey, handler, disabled) => {
            const item = document.createElement('button');
            item.type = 'button';
            item.className = 'color-swatch-context-menu__item';
            if (disabled) item.setAttribute('disabled', 'disabled');
            const iconHtml = (typeof appIcon === 'function') ? appIcon(iconKey) : '';
            item.innerHTML = `${iconHtml}<span>${label}</span>`;
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                e.preventDefault();
                if (disabled) return;
                handler();
                menu.remove();
            });
            return item;
        };

        const swatchPreview = document.createElement('div');
        swatchPreview.className = 'color-swatch-context-menu__header';
        swatchPreview.innerHTML =
            `<span class="color-swatch-context-menu__chip" style="background:${color};"></span>` +
            `<code>${color}</code>`;
        menu.appendChild(swatchPreview);

        menu.appendChild(makeItem(
            isPinned ? 'Unpin' : 'Pin',
            'pin',
            () => {
                if (typeof editor.togglePinnedColor === 'function') {
                    editor.togglePinnedColor(color);
                }
                // Re-render the parent popup if it's still open.
                this._refreshOpenPopup(editor);
            },
            false
        ));

        menu.appendChild(makeItem(
            'Remove from recents',
            'trash',
            () => {
                if (typeof editor.removeRecentColor === 'function') {
                    editor.removeRecentColor(color);
                }
                this._refreshOpenPopup(editor);
            },
            isPinned // disabled when pinned -- user must unpin first
        ));

        document.body.appendChild(menu);

        const rect = menu.getBoundingClientRect();
        if (rect.right > window.innerWidth) {
            menu.style.left = (window.innerWidth - rect.width - 8) + 'px';
        }
        if (rect.bottom > window.innerHeight) {
            menu.style.top = (window.innerHeight - rect.height - 8) + 'px';
        }

        // Dismiss on outside click / escape.
        const dismiss = (e) => {
            if (e.type === 'keydown' && e.key !== 'Escape') return;
            if (e.type !== 'keydown' && menu.contains(e.target)) return;
            menu.remove();
            document.removeEventListener('mousedown', dismiss, true);
            document.removeEventListener('keydown', dismiss, true);
        };
        setTimeout(() => {
            document.addEventListener('mousedown', dismiss, true);
            document.addEventListener('keydown', dismiss, true);
        }, 0);
    },

    _refreshOpenPopup(editor) {
        const popup = document.getElementById('color-palette-popup');
        if (!popup) return;
        const obj = popup.__cpObj;
        const objType = popup.__cpObjType;
        const anchor = popup.__cpAnchor;
        const mode = popup.__cpMode;
        if (!obj || !objType) return;
        popup.remove();
        if (anchor === 'toolbar' && popup.__cpToolbar) {
            this.showColorPalettePopupFromToolbar(editor, obj, objType, popup.__cpToolbar, mode);
        } else {
            this.showColorPalettePopup(editor, obj, objType, mode);
        }
    },

    // ------------------------------------------------------------------
    // Show color palette popup from context menu
    // ------------------------------------------------------------------
    showColorPalettePopup(editor, obj, objType, mode) {
        const existingPopup = document.getElementById('color-palette-popup');
        if (existingPopup) existingPopup.remove();

        if (objType === 'link') {
            editor._colorEditingLink = obj;
            editor.draw();
        }

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

        const popup = this._buildPopup(editor, obj, objType, mode, 'context', null);
        popup.style.left = leftPos + 'px';
        popup.style.top = topPos + 'px';
        document.body.appendChild(popup);

        const popupRect = popup.getBoundingClientRect();
        if (menuRect && popupRect.right > window.innerWidth) {
            popup.style.left = (menuRect.left - popupRect.width - 5) + 'px';
        }
        if (popupRect.bottom > window.innerHeight) {
            popup.style.top = (window.innerHeight - popupRect.height - 10) + 'px';
        }
        this._attachKeyboardNav(popup);
    },

    // ------------------------------------------------------------------
    // Show color palette popup from a toolbar element
    // ------------------------------------------------------------------
    showColorPalettePopupFromToolbar(editor, obj, objType, toolbar, mode) {
        const existingPopup = document.getElementById('color-palette-popup');
        if (existingPopup) {
            existingPopup.remove();
            if (editor) {
                editor._colorEditingLink = null;
                if (typeof editor.draw === 'function') editor.draw();
            }
            return;
        }
        if (window.SelectionPopups && typeof window.SelectionPopups.closeObjectToolbarPopups === 'function') {
            window.SelectionPopups.closeObjectToolbarPopups(editor, 'color-palette-popup');
        }

        if (objType === 'link') {
            editor._colorEditingLink = obj;
            editor.draw();
        }

        const toolbarRect = toolbar.getBoundingClientRect();
        const leftPos = toolbarRect.left + toolbarRect.width / 2;
        const topPos = toolbarRect.bottom + 8;

        const popup = this._buildPopup(editor, obj, objType, mode, 'toolbar', toolbar);
        popup.style.left = leftPos + 'px';
        popup.style.top = topPos + 'px';
        popup.style.transform = 'translateX(-50%)';
        popup.addEventListener('mousedown', (e) => e.stopPropagation());
        popup.addEventListener('click', (e) => e.stopPropagation());

        document.body.appendChild(popup);

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
        this._attachKeyboardNav(popup);
    },

    // ------------------------------------------------------------------
    // Shared popup builder. Routes to solid or split layout based on
    // the object type and current device color mode.
    // ------------------------------------------------------------------
    _buildPopup(editor, obj, objType, mode, anchor, toolbar) {
        const popup = document.createElement('div');
        popup.id = 'color-palette-popup';
        popup.className = 'color-popup color-popup--liquid';
        popup.setAttribute('role', 'dialog');
        popup.setAttribute('aria-label', 'Color picker');
        popup.__cpObj = obj;
        popup.__cpObjType = objType;
        popup.__cpAnchor = anchor;
        popup.__cpToolbar = toolbar || null;

        // Title
        const title = document.createElement('div');
        title.className = 'color-popup-title';
        const titleIcon = (typeof appIcon === 'function') ? appIcon('palette') : '';
        title.innerHTML = `${titleIcon}<span>Quick Colors</span>`;
        popup.appendChild(title);

        // Solid / Split toggle, only for devices.
        const isDevice = (objType === 'device');
        const splitFlag = isDevice
            && typeof obj.colorLeft === 'string' && obj.colorLeft.trim().length > 0
            && typeof obj.colorRight === 'string' && obj.colorRight.trim().length > 0;
        const resolvedMode = (mode === 'split' || mode === 'solid')
            ? mode
            : (splitFlag ? 'split' : 'solid');
        popup.__cpMode = resolvedMode;

        if (isDevice) {
            popup.appendChild(this._buildModeToggle(editor, obj, objType, anchor, toolbar, resolvedMode));
        }

        if (isDevice && resolvedMode === 'split') {
            this._buildSplitBody(popup, editor, obj, anchor, toolbar);
        } else {
            this._buildSolidBody(popup, editor, obj, objType, anchor);
        }

        return popup;
    },

    _buildModeToggle(editor, obj, objType, anchor, toolbar, currentMode) {
        const wrap = document.createElement('div');
        wrap.className = 'color-popup-mode-toggle';

        const makeBtn = (label, modeValue) => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'color-popup-mode-toggle__btn' +
                (currentMode === modeValue ? ' is-active' : '');
            btn.textContent = label;
            btn.setAttribute('aria-pressed', currentMode === modeValue ? 'true' : 'false');
            btn.addEventListener('click', () => {
                if (currentMode === modeValue) return;
                if (typeof editor.setDeviceColorMode === 'function') {
                    editor.setDeviceColorMode(obj, modeValue);
                }
                // Re-open the popup in the new mode.
                const popup = document.getElementById('color-palette-popup');
                if (popup) popup.remove();
                if (anchor === 'toolbar' && toolbar) {
                    this.showColorPalettePopupFromToolbar(editor, obj, objType, toolbar, modeValue);
                } else {
                    this.showColorPalettePopup(editor, obj, objType, modeValue);
                }
            });
            return btn;
        };

        wrap.appendChild(makeBtn('Solid', 'solid'));
        wrap.appendChild(makeBtn('Split', 'split'));
        return wrap;
    },

    // ------------------------------------------------------------------
    // Solid layout (legacy behaviour + Part A polish)
    // ------------------------------------------------------------------
    _buildSolidBody(popup, editor, obj, objType, anchor) {
        const activeColor = (obj && typeof obj.color === 'string') ? obj.color : '';
        const apply = (color) => editor.applyColorToObject(obj, color);

        // Recent + pinned row.
        this._appendRecentRow(popup, editor, apply, {
            size: 32,
            activeColor: activeColor,
        });

        // Standard palette.
        popup.appendChild(this._sectionLabel('palette', 'Palette'));
        const palette = this._container('color-popup-row--grid-6');
        const colors = (anchor === 'toolbar') ? this.compactColors : this.standardColors;
        const cols = (anchor === 'toolbar') ? 5 : 6;
        palette.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
        colors.forEach(color => {
            const isActive = (activeColor || '').toLowerCase() === color.toLowerCase();
            const swatch = this._createSwatch(color, anchor === 'toolbar' ? 32 : 28, () => apply(color), {
                isActive: isActive,
            });
            palette.appendChild(swatch);
        });
        popup.appendChild(palette);

        // Custom color picker.
        popup.appendChild(this._buildCustomPicker(editor, obj, activeColor, (color) => apply(color)));
    },

    // ------------------------------------------------------------------
    // Split layout (Part B)
    // 2026-05-12 [split-color refine]:
    //   * The two columns are visually divided by a hairline rule inside
    //     the grid (handled via CSS background-image on the grid itself).
    //   * Each column header is rendered as a small-caps brand chip in
    //     `--dn-orange` instead of a plain label.
    //   * The Swap button uses the new `ico-swap-horizontal` icon
    //     (horizontal opposing arrows) rather than the circular refresh.
    //   * Just above the Make-Solid buttons we render an inline INFO
    //     note explaining which side will be kept on revert.
    // ------------------------------------------------------------------
    _buildSplitBody(popup, editor, obj, anchor, toolbar) {
        const leftCol = this._buildSplitColumn(editor, obj, 'left', anchor);
        const rightCol = this._buildSplitColumn(editor, obj, 'right', anchor);

        const grid = document.createElement('div');
        grid.className = 'color-popup-split-grid';
        grid.appendChild(leftCol);
        grid.appendChild(rightCol);
        popup.appendChild(grid);

        // INFO note: explain the revert-to-solid behaviour before showing
        // the two buttons. Uses the [INFO] tag prefix per workspace rule
        // -- NO EMOJIS anywhere in the codebase.
        const info = document.createElement('div');
        info.className = 'color-popup-split-info';
        info.innerHTML =
            `<span class="color-popup-split-info__tag">[INFO]</span>` +
            `<span class="color-popup-split-info__text">` +
            `Reverting to solid keeps one side's color and drops the other. ` +
            `Use Swap to flip first if you want the opposite side to win.` +
            `</span>`;
        popup.appendChild(info);

        // Footer: swap + make-solid actions.
        const footer = document.createElement('div');
        footer.className = 'color-popup-split-footer';

        const swap = document.createElement('button');
        swap.type = 'button';
        swap.className = 'color-popup-split-action color-popup-split-action--swap';
        const swapIcon = (typeof appIcon === 'function') ? appIcon('swap-horizontal') : '';
        swap.innerHTML = `${swapIcon}<span>Swap sides</span>`;
        swap.title = 'Swap the left and right colors';
        swap.addEventListener('click', () => {
            if (typeof editor.swapDeviceColorSides === 'function') {
                editor.swapDeviceColorSides(obj);
            }
            this._refreshOpenPopup(editor);
        });
        footer.appendChild(swap);

        const makeSolidBtn = (label, keepSide, swatchColor) => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'color-popup-split-action color-popup-split-action--quiet color-popup-split-action--solidify';
            btn.innerHTML =
                `<span class="color-popup-split-action__chip" style="background:${swatchColor};"></span>` +
                `<span>${label}</span>`;
            btn.title = `Revert to a single color, keeping the ${keepSide} side (${swatchColor})`;
            btn.addEventListener('click', () => {
                if (typeof editor.setDeviceColorMode === 'function') {
                    editor.setDeviceColorMode(obj, 'solid', { keepSide: keepSide });
                }
                // Inline pulse-confirm so the user sees feedback before
                // the popup re-renders into solid mode.
                btn.classList.add('is-confirming');
                setTimeout(() => {
                    const popupEl = document.getElementById('color-palette-popup');
                    if (popupEl) popupEl.remove();
                    if (anchor === 'toolbar' && toolbar) {
                        this.showColorPalettePopupFromToolbar(editor, obj, 'device', toolbar, 'solid');
                    } else {
                        this.showColorPalettePopup(editor, obj, 'device', 'solid');
                    }
                }, 180);
            });
            return btn;
        };

        const leftSwatch = obj.colorLeft || obj.color || '#3498db';
        const rightSwatch = obj.colorRight || obj.color || '#3498db';
        footer.appendChild(makeSolidBtn('Keep L as solid', 'left', leftSwatch));
        footer.appendChild(makeSolidBtn('Keep R as solid', 'right', rightSwatch));

        popup.appendChild(footer);
    },

    _buildSplitColumn(editor, obj, side, anchor) {
        const col = document.createElement('div');
        col.className = 'color-popup-split-col color-popup-split-col--' + side;

        // 2026-05-12 [split-color refine]: render the header as a small
        // brand-coloured "tag" rather than plain label text. The chip
        // (filled swatch) sits to the LEFT for the left column and to
        // the RIGHT for the right column, so the visual weight matches
        // the side it represents.
        const header = document.createElement('div');
        header.className = 'color-popup-split-col__header color-popup-split-col__header--' + side;
        const sideLabel = side === 'left' ? 'Left half' : 'Right half';
        const sideColor = (side === 'left' ? obj.colorLeft : obj.colorRight) || obj.color || '#3498db';
        const chipHtml = `<span class="color-popup-split-col__chip" style="background:${sideColor};"></span>`;
        const tagHtml = `<span class="color-popup-split-col__tag color-popup-split-col__tag--${side}">${sideLabel}</span>`;
        const hexHtml = `<code class="color-popup-split-col__hex">${sideColor}</code>`;
        // Header order: left col -> [chip][tag][hex]; right col -> [hex][tag][chip].
        if (side === 'left') {
            header.innerHTML = chipHtml + tagHtml + hexHtml;
        } else {
            header.innerHTML = hexHtml + tagHtml + chipHtml;
        }
        col.appendChild(header);

        // Suggested chip (only when >= 50% confidence).
        // 2026-05-12 [split-color refine]: chip now includes a
        // direction chevron pointing at the side it will apply to (a
        // right-chevron for the left column meaning "this becomes the
        // left side", and vice versa). The chevron is in `--dn-orange`
        // so it picks up the brand accent and visually ties the
        // suggestion to its destination column.
        if (typeof editor.getNeighborColorSuggestion === 'function') {
            const suggestion = editor.getNeighborColorSuggestion(obj, side);
            const chevronKey = (side === 'left') ? 'right' : 'left';
            const chevronHtml = (typeof appIcon === 'function')
                ? `<span class="color-popup-suggested__chevron color-popup-suggested__chevron--${side}">${appIcon(chevronKey)}</span>`
                : '';
            if (suggestion && suggestion.color && suggestion.confidence >= 0.5) {
                const chip = document.createElement('button');
                chip.type = 'button';
                chip.className = 'color-popup-suggested color-popup-suggested--' + side;
                const pct = Math.round(suggestion.confidence * 100);
                chip.innerHTML =
                    `<span class="color-popup-suggested__swatch" style="background:${suggestion.color};"></span>` +
                    `<span class="color-popup-suggested__label">Suggested <code>${suggestion.color}</code></span>` +
                    `<small>${pct}% of ${suggestion.total} neighbour${suggestion.total === 1 ? '' : 's'}</small>` +
                    chevronHtml;
                chip.title = `Apply ${suggestion.color} to the ${sideLabel.toLowerCase()} ` +
                    `(matches the facing color of the majority of neighbours on this side)`;
                chip.setAttribute('aria-label', chip.title);
                chip.addEventListener('click', () => {
                    if (typeof editor.applyColorToObjectSide === 'function') {
                        editor.applyColorToObjectSide(obj, side, suggestion.color);
                    }
                    this._refreshOpenPopup(editor);
                });
                col.appendChild(chip);
            } else if (suggestion && suggestion.alts && suggestion.alts.length > 0) {
                // Soft hint: show top 2 candidates as small chips.
                const hint = document.createElement('div');
                hint.className = 'color-popup-suggested-hints';
                const headerLine = document.createElement('span');
                headerLine.textContent = 'No clear winner -- hints:';
                hint.appendChild(headerLine);
                const candidates = [{ color: suggestion.color, count: suggestion.count, confidence: suggestion.confidence }]
                    .concat(suggestion.alts)
                    .slice(0, 2);
                candidates.forEach(c => {
                    const chip = document.createElement('button');
                    chip.type = 'button';
                    chip.className = 'color-popup-suggested-hint';
                    chip.innerHTML =
                        `<span class="color-popup-suggested__swatch" style="background:${c.color};"></span>` +
                        `<code>${c.color}</code>` +
                        chevronHtml;
                    chip.title = `${c.count} neighbour${c.count === 1 ? '' : 's'} on this side ` +
                        `(${Math.round((c.confidence || 0) * 100)}% share)`;
                    chip.addEventListener('click', () => {
                        if (typeof editor.applyColorToObjectSide === 'function') {
                            editor.applyColorToObjectSide(obj, side, c.color);
                        }
                        this._refreshOpenPopup(editor);
                    });
                    hint.appendChild(chip);
                });
                col.appendChild(hint);
            }
        }

        // Recent + pinned (compact, smaller swatches).
        const apply = (color) => {
            if (typeof editor.applyColorToObjectSide === 'function') {
                editor.applyColorToObjectSide(obj, side, color);
            }
            this._refreshOpenPopup(editor);
        };
        this._appendRecentRow(col, editor, apply, {
            size: 26,
            activeColor: sideColor,
        });

        // Compact palette.
        col.appendChild(this._sectionLabel('palette', 'Palette'));
        const palette = this._container('color-popup-row--grid-5');
        palette.style.gridTemplateColumns = 'repeat(5, 1fr)';
        this.compactColors.forEach(color => {
            const isActive = (sideColor || '').toLowerCase() === color.toLowerCase();
            const swatch = this._createSwatch(color, 26, () => apply(color), { isActive: isActive });
            palette.appendChild(swatch);
        });
        col.appendChild(palette);

        // Custom picker on this side.
        col.appendChild(this._buildCustomPicker(editor, obj, sideColor, (color) => apply(color)));

        return col;
    },

    _buildCustomPicker(editor, obj, activeColor, applyFn) {
        const wrap = document.createElement('div');
        wrap.className = 'color-popup-custom';
        const label = document.createElement('span');
        label.className = 'color-popup-custom__label';
        label.textContent = 'Custom:';
        wrap.appendChild(label);

        const input = document.createElement('input');
        input.type = 'color';
        input.value = activeColor || '#3498db';
        input.className = 'color-popup-custom__input';
        input.title = 'Pick a custom color';
        input.oninput = (e) => applyFn(e.target.value);
        wrap.appendChild(input);

        return wrap;
    },

    // ------------------------------------------------------------------
    // Keyboard navigation across all swatches in the popup
    // ------------------------------------------------------------------
    _attachKeyboardNav(popup) {
        if (!popup) return;
        const focusables = () => Array.from(popup.querySelectorAll(
            '[data-color-swatch], button.color-popup-suggested, button.color-popup-suggested-hint, button.color-popup-mode-toggle__btn, button.color-popup-split-action, input.color-popup-custom__input'
        )).filter(el => !el.disabled);

        popup.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                popup.remove();
                e.preventDefault();
                return;
            }
            const fs = focusables();
            if (fs.length === 0) return;
            const idx = fs.indexOf(document.activeElement);
            const grid = popup.querySelector('.color-popup-row--grid-6, .color-popup-row--grid-5');
            const stride = grid ? (parseInt(getComputedStyle(grid).gridTemplateColumns.split(' ').length, 10) || 6) : 1;

            if (e.key === 'ArrowRight') {
                e.preventDefault();
                const next = fs[Math.min(fs.length - 1, Math.max(0, idx) + 1)] || fs[0];
                next.focus();
            } else if (e.key === 'ArrowLeft') {
                e.preventDefault();
                const prev = fs[Math.max(0, (idx < 0 ? 0 : idx - 1))];
                if (prev) prev.focus();
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                const next = fs[Math.min(fs.length - 1, (idx < 0 ? 0 : idx + stride))];
                if (next) next.focus();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                const prev = fs[Math.max(0, (idx < 0 ? 0 : idx - stride))];
                if (prev) prev.focus();
            }
        });
        // Move focus to the first swatch for immediate keyboard control.
        setTimeout(() => {
            const fs = focusables();
            if (fs.length > 0) fs[0].focus();
        }, 0);
    },

    // ------------------------------------------------------------------
    // Hide color palette popup
    // ------------------------------------------------------------------
    hideColorPalettePopup(editor) {
        const popup = document.getElementById('color-palette-popup');
        if (popup) popup.remove();
        const ctxMenu = document.getElementById('color-swatch-context-menu');
        if (ctxMenu) ctxMenu.remove();
        if (editor) {
            editor._colorEditingLink = null;
            editor.draw();
        }
    },

    // ------------------------------------------------------------------
    // Create a single color swatch. opts: { isActive, isPinned, onContext }
    // ------------------------------------------------------------------
    _createSwatch(color, size, onClick, opts) {
        opts = opts || {};
        const isActive = !!opts.isActive;
        const isPinned = !!opts.isPinned;
        const onContext = (typeof opts.onContext === 'function') ? opts.onContext : null;

        const swatch = document.createElement('div');
        swatch.className = 'color-popup-swatch' +
            (isActive ? ' is-active' : '') +
            (isPinned ? ' is-pinned' : '');
        swatch.setAttribute('data-color-swatch', '');
        swatch.setAttribute('role', 'button');
        swatch.setAttribute('tabindex', '0');
        swatch.style.width = size + 'px';
        swatch.style.height = size + 'px';
        swatch.style.borderRadius = (size > 30 ? 8 : 6) + 'px';
        swatch.style.background = color;
        swatch.dataset.color = color;
        swatch.title = isPinned ? `Pinned ${color}` : color;

        if (isPinned) {
            const dot = document.createElement('span');
            dot.className = 'color-popup-swatch__pin-dot';
            swatch.appendChild(dot);
        }

        swatch.addEventListener('click', onClick);
        swatch.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onClick();
            }
        });
        if (onContext) {
            swatch.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                e.stopPropagation();
                onContext(e.clientX, e.clientY);
            });
        }
        return swatch;
    }
};

console.log('[topology-color-popups.js v2.0.0 2026-05-12] ColorPopups loaded (recent-colors polish + split-color)');
