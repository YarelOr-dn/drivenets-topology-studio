/**
 * topology-packet-popup.js -- Packet selection popup with layer toggles.
 *
 * Floating panel that appears next to the selected packet object. It lists
 * every layer in the packet's stack, each with:
 *   - a checkbox-style visibility toggle (mirrors layer.visible)
 *   - the layer's accent color (square swatch)
 *   - editable layer name + one-line text
 *
 * The popup also offers presets (collapse all, show all, show common L2+L3),
 * a "rename packet title" line, and a "Detach from link" / "Re-attach" toggle
 * when the packet has a linkId. Closing the popup persists nothing extra --
 * mutations call `editor.saveState()` directly so undo/redo works.
 *
 * Mutual exclusion: registers under the same `closeObjectToolbarPopups`
 * keepId mechanism as the link/device toolbars; opening the packet popup
 * closes any other selection popup.
 *
 * Multi-user: pure DOM, lives only inside the editing user's browser. No
 * persistent state.
 */

'use strict';

(function () {
    const POPUP_ID = 'packet-popup';
    const SUMMARY_EDITOR_ID = 'packet-summary-editor';
    const MAX_LINE_LEN = 40;
    const MAX_LINES = 2;
    const LAYER_VALIDATORS = {
        l2: { allow: /[0-9a-fA-F:.\s\->,\nsrcdt*]/g, hint: 'src 00:..:01\ndst 00:..:02' },
        vlan: { allow: /[0-9=,\-\s\noutrieinvlapq]/gi, hint: 'outer=N\ninner=M' },
        mpls: { allow: /[0-9A-Za-z\s\-_,\n:]/g, hint: 'label=N stack=M' },
        l3: { allow: /[0-9a-fA-F.:\/\-\s>,\nsrcdt*]/g, hint: 'src 10.0.0.1\ndst 10.0.0.2' },
        l4: { allow: /[0-9A-Za-z\-=\s,\n:]/g, hint: 'tcp/179\nflags SYN' },
        payload: { allow: /[\x20-\x7E\n]/g, hint: 'free text (printable)' }
    };

    // Structured field editors per layer type. Each layer renders dedicated,
    // self-validating inputs (e.g. Src/Dst MAC for L2, Src/Dst IP for L3)
    // instead of one freeform textarea. The fields compose back into
    // `layer.text` (what the canvas chip renders) and the raw values are also
    // stored on `layer.fields` so reopening the popup restores them exactly.
    // The per-row "raw" toggle (layer.freeText) drops back to the textarea for
    // anything the structured editor can't express.
    const LAYER_FIELD_SCHEMAS = {
        l2: [
            { key: 'src', label: 'Src MAC', ph: '00:11:22:33:44:55', kind: 'mac', tpl: 'src {v}' },
            { key: 'dst', label: 'Dst MAC', ph: 'aa:bb:cc:dd:ee:ff', kind: 'mac', tpl: 'dst {v}' }
        ],
        vlan: [
            { key: 'outer', label: 'Outer', ph: '100', kind: 'vlan', tpl: 'outer={v}' },
            { key: 'inner', label: 'Inner', ph: '200', kind: 'vlan', tpl: 'inner={v}' }
        ],
        mpls: [
            { key: 'label', label: 'Label', ph: '24001', kind: 'num', tpl: 'label {v}' },
            { key: 'stack', label: 'Stack', ph: '2', kind: 'num', tpl: 'stack {v}' }
        ],
        l3: [
            { key: 'src', label: 'Src IP', ph: '10.0.0.1', kind: 'ip', tpl: 'src {v}' },
            { key: 'dst', label: 'Dst IP', ph: '10.0.0.2', kind: 'ip', tpl: 'dst {v}' }
        ],
        l4: [
            { key: 'proto', label: 'Proto', ph: 'tcp/179', kind: 'l4', tpl: '{v}' },
            { key: 'flags', label: 'Flags', ph: 'SYN', kind: 'l4', tpl: '{v}' }
        ]
    };

    const FIELD_KIND_FILTERS = {
        mac: { re: /[0-9a-fA-F:.\-]/g, max: 23 },
        ip: { re: /[0-9a-fA-F.:\/]/g, max: 43 },
        vlan: { re: /[0-9]/g, max: 4 },
        num: { re: /[0-9]/g, max: 7 },
        l4: { re: /[0-9A-Za-z\/\-_.: ]/g, max: 18 },
        text: { re: /[\x20-\x7E]/g, max: 24 }
    };

    function _schemaFor(layer) {
        const id = String((layer && layer.id) || '').toLowerCase();
        return LAYER_FIELD_SCHEMAS[id] || null;
    }

    function _fieldFilter(value, kind) {
        const spec = FIELD_KIND_FILTERS[kind] || FIELD_KIND_FILTERS.text;
        const matched = String(value || '').match(spec.re);
        let out = matched ? matched.join('') : '';
        if (out.length > spec.max) out = out.slice(0, spec.max);
        return out;
    }

    function _composeLayerText(layer) {
        const schema = _schemaFor(layer);
        if (!schema) return layer.text || '';
        const fields = layer.fields || {};
        const lines = [];
        for (const f of schema) {
            const v = String(fields[f.key] || '').trim();
            if (v) lines.push(f.tpl.replace('{v}', v));
        }
        return lines.join('\n');
    }

    function _deriveFields(layer) {
        const schema = _schemaFor(layer);
        if (!schema) return {};
        if (layer.fields && typeof layer.fields === 'object') return layer.fields;
        const lines = String(layer.text || '').split('\n').map(s => s.trim());
        const fields = {};
        schema.forEach((f, idx) => {
            let raw = '';
            const prefix = f.tpl.split('{v}')[0].trim().replace(/=$/, '');
            if (prefix) {
                const re = new RegExp('^' + prefix.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '[=\\s]+(.+)$', 'i');
                for (const ln of lines) {
                    const m = ln.match(re);
                    if (m) { raw = m[1]; break; }
                }
            } else {
                raw = lines[idx] || '';
            }
            fields[f.key] = _fieldFilter(raw, f.kind);
        });
        layer.fields = fields;
        return fields;
    }

    function _isDarkMode() {
        const skin = document.documentElement.getAttribute('data-skin');
        if (skin === 'v23-light') return false;
        if (skin === 'v23-dark') return true;
        const body = document.body;
        if (body && body.classList && body.classList.contains('light-mode')) return false;
        return true;
    }

    function _ensureMutualExclusion(editor) {
        if (window.SelectionPopups && typeof window.SelectionPopups.closeObjectToolbarPopups === 'function') {
            window.SelectionPopups.closeObjectToolbarPopups(editor, POPUP_ID);
        }
    }

    // One-time scoped stylesheet so every control in the packet popup gets
    // consistent tactile feedback (press/hover/focus) and smooth transitions
    // without each button hand-rolling its own handlers. Only adds transform +
    // outline so it never fights the per-button background colors set inline.
    function _ensureStyles() {
        if (document.getElementById('packet-popup-style')) return;
        const style = document.createElement('style');
        style.id = 'packet-popup-style';
        style.textContent = `
            #${POPUP_ID} { animation: packetPopupIn .12s ease-out; transform-origin: left center; }
            @keyframes packetPopupIn {
                from { opacity: 0; transform: translateY(4px) scale(0.98); }
                to   { opacity: 1; transform: translateY(0) scale(1); }
            }
            #${POPUP_ID} button {
                transition: transform .07s ease, background .12s ease,
                            box-shadow .12s ease, border-color .12s ease, opacity .12s ease;
                -webkit-tap-highlight-color: transparent;
                user-select: none;
            }
            #${POPUP_ID} button:not([disabled]):hover { filter: brightness(1.08); }
            #${POPUP_ID} button:not([disabled]):active { transform: translateY(1px) scale(0.95); }
            #${POPUP_ID} button:focus-visible {
                outline: 2px solid rgba(0, 220, 255, 0.65);
                outline-offset: 1px;
            }
            #${POPUP_ID} .packet-layer-row { transition: opacity .12s ease, background .12s ease, box-shadow .12s ease; }
            #${POPUP_ID} .packet-layer-row:hover { box-shadow: inset 0 0 0 1px rgba(0, 220, 255, 0.18); }
            #${POPUP_ID} .packet-checkbox { transition: background .12s ease, border-color .12s ease, transform .07s ease; }
            #${POPUP_ID} .packet-checkbox:active { transform: scale(0.88); }
            #${POPUP_ID} input, #${POPUP_ID} textarea { transition: border-color .12s ease, box-shadow .12s ease; }
            #${POPUP_ID} input:focus, #${POPUP_ID} textarea:focus {
                border-color: rgba(0, 220, 255, 0.6) !important;
                box-shadow: 0 0 0 2px rgba(0, 220, 255, 0.18);
            }
        `;
        document.head.appendChild(style);
    }

    function close(editor) {
        const el = document.getElementById(POPUP_ID);
        if (el) el.remove();
        document.removeEventListener('mousedown', _outsideHandler, true);
    }

    let _outsideTarget = null;
    function _outsideHandler(e) {
        const popup = document.getElementById(POPUP_ID);
        if (!popup) return;
        if (popup.contains(e.target)) return;
        if (_outsideTarget && typeof _outsideTarget.editor === 'object') {
            close(_outsideTarget.editor);
            _outsideTarget = null;
        }
    }

    function _createSwatch(color) {
        const sw = document.createElement('span');
        sw.style.cssText = `
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 3px;
            background: ${color || '#3498db'};
            border: 1px solid rgba(255, 255, 255, 0.25);
            flex: 0 0 auto;
        `;
        return sw;
    }

    function _createCheckbox(checked) {
        const wrap = document.createElement('span');
        wrap.className = 'packet-checkbox';
        _setCheckbox(wrap, checked);
        return wrap;
    }

    function _setCheckbox(wrap, checked) {
        wrap.style.cssText = `
            position: relative;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 16px;
            height: 16px;
            border-radius: 3px;
            border: 1px solid ${checked ? 'rgba(0, 220, 255, 0.85)' : 'rgba(255, 255, 255, 0.45)'};
            background: ${checked ? 'rgba(0, 220, 255, 0.85)' : 'transparent'};
            cursor: pointer;
            flex: 0 0 auto;
            transition: all 0.12s ease;
        `;
        wrap.innerHTML = '';
        if (checked) {
            wrap.innerHTML = `<svg width="10" height="10" viewBox="0 0 12 12" fill="none">
                <path d="M2 6.5l2.5 2.5L10 3" stroke="#0a1530" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>`;
        }
    }

    function _validatorFor(layer) {
        const id = String((layer && layer.id) || 'payload').toLowerCase();
        return LAYER_VALIDATORS[id] || LAYER_VALIDATORS.payload;
    }

    function _filterWithRegex(value, regex) {
        const text = String(value || '');
        if (!regex) return { value: text, changed: false };
        regex.lastIndex = 0;
        const matches = text.match(regex);
        const filtered = matches ? matches.join('') : '';
        return { value: filtered, changed: filtered !== text };
    }

    function _limitLines(value, maxLines, maxLen) {
        const lines = String(value || '').split(/\r?\n/).slice(0, maxLines);
        return lines.map(line => line.slice(0, maxLen)).join('\n');
    }

    function _filterValue(value, validator, opts) {
        opts = opts || {};
        let next = String(value || '').replace(/\r/g, '');
        let changed = false;
        if (!opts.freeText && validator && validator.allow) {
            const filtered = _filterWithRegex(next, validator.allow);
            next = filtered.value;
            changed = changed || filtered.changed;
        }
        if (opts.printableOnly) {
            const printable = next.replace(/[^\x20-\x7E]/g, '');
            changed = changed || printable !== next;
            next = printable;
        }
        const limited = opts.singleLine
            ? next.replace(/\n/g, '').slice(0, opts.maxLen || 24)
            : _limitLines(next, opts.maxLines || MAX_LINES, opts.maxLen || MAX_LINE_LEN);
        changed = changed || limited !== next;
        return { value: limited, changed };
    }

    function _flashInvalid(el, originalBorder) {
        if (!el) return;
        el.style.border = '1px dashed #e74c3c';
        window.clearTimeout(el._packetWarnTimer);
        el._packetWarnTimer = window.setTimeout(() => {
            el.style.border = originalBorder;
        }, 800);
    }

    function _debouncedSave(editor, holder, delay) {
        if (holder.timer) window.clearTimeout(holder.timer);
        holder.timer = window.setTimeout(() => {
            holder.timer = null;
            _safeSaveState(editor);
        }, delay || 700);
    }

    function _flushSave(editor, holder) {
        if (!holder || !holder.timer) return;
        window.clearTimeout(holder.timer);
        holder.timer = null;
        _safeSaveState(editor);
    }

    function _safeSaveState(editor) {
        if (typeof editor.saveState === 'function') editor.saveState();
    }

    function _safeDraw(editor) {
        if (typeof editor.draw === 'function') editor.draw();
    }

    function show(editor, packet) {
        if (!editor || !packet || packet.type !== 'packet') return;
        _ensureStyles();
        _ensureMutualExclusion(editor);
        close(editor);
        _outsideTarget = { editor };
        const summaryEditor = document.getElementById(SUMMARY_EDITOR_ID);
        if (summaryEditor) summaryEditor.remove();

        const dark = _isDarkMode();
        const popup = document.createElement('div');
        popup.id = POPUP_ID;
        popup.style.cssText = `
            position: fixed;
            z-index: 100002;
            min-width: 240px;
            max-width: 320px;
            background: ${dark ? 'rgba(15, 20, 30, 0.97)' : 'rgba(255, 255, 255, 0.98)'};
            color: ${dark ? '#e6edf3' : '#1a1a2e'};
            border: 1px solid ${dark ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.12)'};
            border-radius: 10px;
            padding: 8px 10px 10px;
            box-shadow: ${dark
                ? '0 8px 32px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.07)'
                : '0 8px 32px rgba(0, 0, 0, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.5)'};
            font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
            font-size: 12px;
            backdrop-filter: blur(12px) saturate(160%);
            -webkit-backdrop-filter: blur(12px) saturate(160%);
        `;

        // ---- Header: title input + close button -----------------------------
        const header = document.createElement('div');
        header.style.cssText = 'display:flex; align-items:center; gap:6px; margin-bottom:8px;';
        const titleInput = document.createElement('input');
        titleInput.type = 'text';
        titleInput.value = packet.title || 'Frame';
        titleInput.placeholder = 'Frame';
        titleInput.maxLength = 24;
        titleInput.style.cssText = `
            flex: 1 1 auto;
            background: ${dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)'};
            border: 1px solid ${dark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.1)'};
            border-radius: 6px;
            padding: 4px 8px;
            color: inherit;
            font-size: 12px;
            font-weight: 600;
        `;
        const titleSave = { timer: null };
        const titleBorder = `1px solid ${dark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.1)'}`;
        titleInput.oninput = () => {
            const filtered = _filterValue(titleInput.value, null, {
                printableOnly: true,
                singleLine: true,
                maxLen: 24
            });
            if (filtered.changed) {
                titleInput.value = filtered.value;
                _flashInvalid(titleInput, titleBorder);
            }
            packet.title = filtered.value.trim() || 'Frame';
            _safeDraw(editor);
            _debouncedSave(editor, titleSave);
        };
        titleInput.onblur = () => _flushSave(editor, titleSave);
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '&times;';
        closeBtn.title = 'Close';
        closeBtn.style.cssText = `
            background: transparent;
            border: none;
            color: ${dark ? 'rgba(255,255,255,0.55)' : 'rgba(0,0,0,0.55)'};
            cursor: pointer;
            font-size: 18px;
            line-height: 1;
            padding: 0 4px;
        `;
        closeBtn.onclick = (e) => { e.stopPropagation(); close(editor); };
        header.appendChild(titleInput);
        header.appendChild(closeBtn);
        popup.appendChild(header);

        // ---- Quick actions bar ---------------------------------------------
        const actions = document.createElement('div');
        actions.style.cssText = 'display:flex; gap:4px; margin-bottom:8px; flex-wrap:wrap;';
        const layerRows = [];
        const refreshLayerChrome = () => {
            layerRows.forEach(({ layer, row, checkbox, freeBtn, freeBadge, hasSchema }) => {
                _setCheckbox(checkbox, layer.visible !== false);
                checkbox.title = layer.visible === false ? 'Show this layer' : 'Hide this layer';
                row.style.opacity = layer.visible === false ? '0.62' : '1';
                const rawMode = layer.freeText === true;
                if (freeBtn) {
                    freeBtn.style.background = rawMode
                        ? (dark ? 'rgba(0,220,255,0.22)' : 'rgba(0,130,170,0.16)')
                        : 'transparent';
                    if (hasSchema) {
                        freeBtn.textContent = rawMode ? 'fields' : 'raw';
                        freeBtn.title = rawMode
                            ? 'Switch back to structured fields'
                            : 'Switch to raw free-text for this layer';
                    } else {
                        freeBtn.textContent = 'abc';
                        freeBtn.title = rawMode
                            ? 'Free-text mode enabled for this layer'
                            : 'Strict packet-field validation enabled';
                    }
                }
                if (freeBadge) {
                    freeBadge.textContent = hasSchema ? 'raw' : 'free';
                    freeBadge.style.display = rawMode ? 'inline' : 'none';
                }
            });
        };
        const _btn = (label, onclick, opts) => {
            opts = opts || {};
            const b = document.createElement('button');
            b.textContent = label;
            b.style.cssText = `
                padding: 3px 8px;
                font-size: 11px;
                background: ${dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)'};
                color: inherit;
                border: 1px solid ${dark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.1)'};
                border-radius: 5px;
                cursor: pointer;
                transition: all 0.12s ease;
            `;
            b.onmouseenter = () => {
                b.style.background = dark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)';
            };
            b.onmouseleave = () => {
                b.style.background = dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)';
            };
            b.onclick = (e) => { e.stopPropagation(); onclick(); };
            return b;
        };
        actions.appendChild(_btn('Show all', () => {
            (packet.layers || []).forEach(l => l.visible = true);
            _safeSaveState(editor);
            _safeDraw(editor);
            refreshLayerChrome();
        }));
        actions.appendChild(_btn('Hide all', () => {
            (packet.layers || []).forEach(l => l.visible = false);
            _safeSaveState(editor);
            _safeDraw(editor);
            refreshLayerChrome();
        }));
        actions.appendChild(_btn('L2+L3 only', () => {
            (packet.layers || []).forEach(l => {
                const id = String(l.id || '').toLowerCase();
                l.visible = (id === 'l2' || id === 'l3');
            });
            _safeSaveState(editor);
            _safeDraw(editor);
            refreshLayerChrome();
        }));
        // Toggle buttons update their own label in place instead of tearing
        // down and rebuilding the whole popup. The previous full re-show()
        // caused a visible flicker and lost input focus on every click.
        const collapseBtn = _btn(packet.collapsed ? 'Expand' : 'Collapse', () => {
            packet.collapsed = !packet.collapsed;
            collapseBtn.textContent = packet.collapsed ? 'Expand' : 'Collapse';
            _safeSaveState(editor);
            _safeDraw(editor);
        });
        actions.appendChild(collapseBtn);
        const reverseBtn = _btn(packet.direction === 'backward' ? 'Reverse \u2192' : 'Reverse \u2190', () => {
            packet.direction = packet.direction === 'backward' ? 'forward' : 'backward';
            reverseBtn.textContent = packet.direction === 'backward' ? 'Reverse \u2192' : 'Reverse \u2190';
            _safeSaveState(editor);
            _safeDraw(editor);
        });
        actions.appendChild(reverseBtn);
        const sideBtn = _btn(packet.side === 'below' ? 'Move above' : 'Move below', () => {
            packet.side = packet.side === 'below' ? 'above' : 'below';
            sideBtn.textContent = packet.side === 'below' ? 'Move above' : 'Move below';
            if (window.PacketMethods && typeof window.PacketMethods.updatePacketPosition === 'function') {
                window.PacketMethods.updatePacketPosition(editor, packet);
            }
            _safeSaveState(editor);
            _safeDraw(editor);
        });
        actions.appendChild(sideBtn);
        actions.appendChild(_btn('Reset width', () => {
            delete packet.userWidth;
            _safeSaveState(editor);
            _safeDraw(editor);
        }));
        popup.appendChild(actions);

        // ---- Per-layer rows -------------------------------------------------
        const layersContainer = document.createElement('div');
        layersContainer.style.cssText = 'display:flex; flex-direction:column; gap:4px;';

        (packet.layers || []).forEach((layer) => {
            const row = document.createElement('div');
            row.className = 'packet-layer-row';
            row.style.cssText = `
                display: flex;
                align-items: flex-start;
                gap: 6px;
                padding: 4px 6px;
                background: ${dark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)'};
                border-radius: 6px;
                border-left: 3px solid ${layer.color || '#3498db'};
            `;

            // Visibility toggle
            const checkbox = _createCheckbox(layer.visible !== false);
            checkbox.title = layer.visible === false ? 'Show this layer' : 'Hide this layer';
            checkbox.onclick = (e) => {
                e.stopPropagation();
                layer.visible = layer.visible === false ? true : false;
                _safeSaveState(editor);
                _safeDraw(editor);
                refreshLayerChrome();
            };

            // Layer body: name row + a detail area that swaps between the
            // structured field editor (default) and a raw textarea (freeText).
            const body = document.createElement('div');
            body.style.cssText = 'flex: 1 1 auto; display:flex; flex-direction:column; gap:3px; min-width:0;';
            const nameRow = document.createElement('div');
            nameRow.style.cssText = 'display:flex; align-items:center; gap:4px;';
            const swatch = _createSwatch(layer.color);
            const hasSchema = !!_schemaFor(layer);
            const freeBtn = document.createElement('button');
            freeBtn.type = 'button';
            freeBtn.style.cssText = `
                flex: 0 0 auto;
                border: 1px solid ${dark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.10)'};
                border-radius: 4px;
                background: transparent;
                color: inherit;
                cursor: pointer;
                font-size: 9px;
                padding: 1px 5px;
            `;
            const freeBadge = document.createElement('span');
            freeBadge.style.cssText = `
                font-style: italic;
                font-size: 9px;
                opacity: 0.7;
            `;
            const nameInput = document.createElement('input');
            nameInput.type = 'text';
            nameInput.value = layer.name || '';
            nameInput.maxLength = 12;
            nameInput.style.cssText = `
                flex: 1 1 auto;
                min-width: 0;
                background: transparent;
                border: none;
                border-bottom: 1px dashed ${dark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.15)'};
                color: inherit;
                font-size: 11px;
                font-weight: 600;
                padding: 1px 2px;
                outline: none;
            `;
            const nameSave = { timer: null };
            nameInput.oninput = () => {
                const filtered = _filterValue(nameInput.value, null, {
                    printableOnly: true,
                    singleLine: true,
                    maxLen: 12
                });
                if (filtered.changed) nameInput.value = filtered.value;
                layer.name = filtered.value;
                _safeDraw(editor);
                _debouncedSave(editor, nameSave);
            };
            nameInput.onblur = () => _flushSave(editor, nameSave);
            nameRow.appendChild(swatch);
            nameRow.appendChild(freeBtn);
            nameRow.appendChild(freeBadge);
            nameRow.appendChild(nameInput);

            // Detail area re-renders when the raw/fields mode flips.
            const detail = document.createElement('div');
            detail.style.cssText = 'display:flex; flex-direction:column; gap:3px; min-width:0;';

            const buildRawTextarea = () => {
                const textArea = document.createElement('textarea');
                const validator = _validatorFor(layer);
                textArea.value = layer.text || '';
                textArea.placeholder = validator.hint || 'one or two short lines';
                textArea.rows = Math.max(1, Math.min(3, String(layer.text || '').split('\n').length));
                textArea.style.cssText = `
                    width: 100%;
                    resize: vertical;
                    background: ${dark ? 'rgba(0,0,0,0.25)' : 'rgba(255,255,255,0.5)'};
                    border: 1px solid ${dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'};
                    border-radius: 4px;
                    color: inherit;
                    font-family: 'JetBrains Mono', 'Menlo', monospace;
                    font-size: 10.5px;
                    padding: 3px 5px;
                    line-height: 1.4;
                    outline: none;
                    box-sizing: border-box;
                `;
                const textBorder = `1px solid ${dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'}`;
                const textSave = { timer: null };
                textArea.oninput = () => {
                    const filtered = _filterValue(textArea.value, validator, {
                        freeText: layer.freeText === true,
                        maxLines: MAX_LINES,
                        maxLen: MAX_LINE_LEN
                    });
                    if (filtered.changed) {
                        textArea.value = filtered.value;
                        _flashInvalid(textArea, textBorder);
                    }
                    layer.text = filtered.value;
                    // Drop cached structured fields so a later flip back re-parses.
                    if (_schemaFor(layer)) delete layer.fields;
                    _safeDraw(editor);
                    _debouncedSave(editor, textSave);
                };
                textArea.onblur = () => _flushSave(editor, textSave);
                return textArea;
            };

            const buildFieldEditor = (schema) => {
                const grid = document.createElement('div');
                grid.style.cssText = 'display:flex; flex-direction:column; gap:3px; min-width:0;';
                const fields = _deriveFields(layer);
                layer.text = _composeLayerText(layer);
                schema.forEach((f) => {
                    const fr = document.createElement('div');
                    fr.style.cssText = 'display:flex; align-items:center; gap:6px; min-width:0;';
                    const lbl = document.createElement('span');
                    lbl.textContent = f.label;
                    lbl.style.cssText = 'flex:0 0 50px; font-size:9.5px; opacity:0.65; text-align:right; white-space:nowrap;';
                    const inp = document.createElement('input');
                    inp.type = 'text';
                    inp.value = fields[f.key] || '';
                    inp.placeholder = f.ph;
                    inp.spellcheck = false;
                    inp.style.cssText = `
                        flex: 1 1 auto;
                        min-width: 0;
                        background: ${dark ? 'rgba(0,0,0,0.25)' : 'rgba(255,255,255,0.6)'};
                        border: 1px solid ${dark ? 'rgba(255,255,255,0.10)' : 'rgba(0,0,0,0.10)'};
                        border-radius: 4px;
                        color: inherit;
                        font-family: 'JetBrains Mono', 'Menlo', monospace;
                        font-size: 10.5px;
                        padding: 2px 6px;
                        outline: none;
                        box-sizing: border-box;
                    `;
                    const fSave = { timer: null };
                    inp.oninput = () => {
                        const v = _fieldFilter(inp.value, f.kind);
                        if (v !== inp.value) inp.value = v;
                        if (!layer.fields) layer.fields = {};
                        layer.fields[f.key] = v;
                        layer.text = _composeLayerText(layer);
                        _safeDraw(editor);
                        _debouncedSave(editor, fSave);
                    };
                    inp.onblur = () => _flushSave(editor, fSave);
                    fr.appendChild(lbl);
                    fr.appendChild(inp);
                    grid.appendChild(fr);
                });
                return grid;
            };

            const renderDetail = () => {
                detail.innerHTML = '';
                const schema = _schemaFor(layer);
                if (schema && layer.freeText !== true) {
                    detail.appendChild(buildFieldEditor(schema));
                } else {
                    detail.appendChild(buildRawTextarea());
                }
            };
            renderDetail();

            freeBtn.onclick = (e) => {
                e.stopPropagation();
                layer.freeText = layer.freeText === true ? false : true;
                _safeSaveState(editor);
                renderDetail();
                _safeDraw(editor);
                refreshLayerChrome();
            };

            body.appendChild(nameRow);
            body.appendChild(detail);

            row.appendChild(checkbox);
            row.appendChild(body);
            layersContainer.appendChild(row);
            layerRows.push({ layer, row, checkbox, freeBtn, freeBadge, hasSchema });
        });
        refreshLayerChrome();

        popup.appendChild(layersContainer);

        // ---- Footer: link attach status + packet actions ---------------------
        const footer = document.createElement('div');
        footer.style.cssText = 'margin-top:8px; padding-top:6px; border-top:1px solid ' +
            (dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)') +
            '; display:flex; align-items:center; justify-content:space-between; gap:6px;';

        const linkInfo = document.createElement('div');
        linkInfo.style.cssText = `font-size:10.5px; color:${dark ? 'rgba(255,255,255,0.55)' : 'rgba(0,0,0,0.55)'};`;
        if (packet.linkId) {
            const link = editor.objects.find(o => o.id === packet.linkId);
            const t = (typeof packet.linkAttachT === 'number' ? packet.linkAttachT : 0.5).toFixed(2);
            linkInfo.textContent = link ? `Attached to ${packet.linkId} (t=${t})` : `Link not found`;
        } else {
            linkInfo.textContent = 'Freestanding - drag onto a link or use Re-attach';
        }
        footer.appendChild(linkInfo);

        const footerActions = document.createElement('div');
        footerActions.style.cssText = 'display:flex; align-items:center; gap:5px; flex:0 0 auto;';

        // Detach when attached; Re-attach (snap to nearest link) when freestanding.
        const detachBtn = document.createElement('button');
        detachBtn.textContent = packet.linkId ? 'Detach' : 'Re-attach';
        detachBtn.title = packet.linkId
            ? 'Detach this packet from its link and keep it at the current canvas position'
            : 'Attach this packet to the nearest link on the canvas';
        detachBtn.style.cssText = `
            padding: 3px 8px;
            font-size: 11px;
            background: ${dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)'};
            color: inherit;
            border: 1px solid ${dark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.1)'};
            border-radius: 5px;
            cursor: pointer;
            opacity: 1;
            transition: all 0.12s ease;
        `;
        detachBtn.onmouseenter = () => {
            detachBtn.style.background = dark ? 'rgba(255,255,255,0.16)' : 'rgba(0,0,0,0.1)';
        };
        detachBtn.onmouseleave = () => {
            detachBtn.style.background = dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)';
        };
        detachBtn.onclick = (e) => {
            e.stopPropagation();
            if (packet.linkId) {
                if (window.PacketMethods && typeof window.PacketMethods.detachPacket === 'function') {
                    window.PacketMethods.detachPacket(editor, packet);
                } else {
                    packet.linkId = null;
                    packet.linkAttachT = undefined;
                }
            } else {
                // Re-attach: snap to the nearest link anywhere on the canvas.
                const link = (window.PacketMethods && typeof window.PacketMethods.attachPacketToNearestLink === 'function')
                    ? window.PacketMethods.attachPacketToNearestLink(editor, packet, Infinity)
                    : null;
                if (!link) {
                    linkInfo.textContent = 'No link on canvas to attach to';
                    return;
                }
            }
            _safeSaveState(editor);
            _safeDraw(editor);
            show(editor, packet);
        };

        const delBtn = document.createElement('button');
        delBtn.textContent = 'Delete';
        delBtn.style.cssText = `
            padding: 3px 8px;
            font-size: 11px;
            background: rgba(231, 76, 60, 0.85);
            color: #fff;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.12s ease;
        `;
        delBtn.onmouseenter = () => { delBtn.style.background = '#c0392b'; };
        delBtn.onmouseleave = () => { delBtn.style.background = 'rgba(231, 76, 60, 0.85)'; };
        delBtn.onclick = (e) => {
            e.stopPropagation();
            const idx = editor.objects.indexOf(packet);
            if (idx >= 0) editor.objects.splice(idx, 1);
            _safeSaveState(editor);
            if (editor.selectedObject === packet) editor.selectedObject = null;
            _safeDraw(editor);
            close(editor);
        };
        footerActions.appendChild(detachBtn);
        footerActions.appendChild(delBtn);
        footer.appendChild(footerActions);
        popup.appendChild(footer);

        document.body.appendChild(popup);

        // Position the popup next to the packet on canvas.
        if (editor.canvas && typeof editor.zoom === 'number') {
            const rect = editor.canvas.getBoundingClientRect();
            const pan = editor.panOffset || { x: 0, y: 0 };
            const screenX = rect.left + packet.x * editor.zoom + pan.x;
            const screenY = rect.top + packet.y * editor.zoom + pan.y;
            const popupRect = popup.getBoundingClientRect();
            const packetWidth = (window.PacketMethods && window.PacketMethods.getPacketBounds)
                ? window.PacketMethods.getPacketBounds(editor, packet).w
                : (packet.width || 140);
            let left = screenX + packetWidth * editor.zoom / 2 + 12;
            let top = screenY - popupRect.height / 2;
            // Clamp inside viewport.
            const margin = 8;
            const vw = window.innerWidth;
            const vh = window.innerHeight;
            if (left + popupRect.width + margin > vw) {
                left = screenX - packetWidth * editor.zoom / 2 - popupRect.width - 12;
            }
            if (left < margin) left = margin;
            if (top < margin) top = margin;
            if (top + popupRect.height + margin > vh) top = vh - popupRect.height - margin;
            popup.style.left = `${left}px`;
            popup.style.top = `${top}px`;
        } else {
            popup.style.left = '50%';
            popup.style.top = '20%';
            popup.style.transform = 'translateX(-50%)';
        }

        // Outside-click close (deferred so the click that opened us doesn't
        // immediately close us).
        setTimeout(() => {
            document.addEventListener('mousedown', _outsideHandler, true);
        }, 30);
    }

    function showSummaryEditor(editor, packet) {
        if (!editor || !packet || packet.type !== 'packet' || !editor.canvas || !window.PacketMethods) return;
        const old = document.getElementById(SUMMARY_EDITOR_ID);
        if (old) old.remove();
        const bounds = window.PacketMethods.getPacketSummaryBounds(editor, packet);
        if (!bounds) return;
        const rect = editor.canvas.getBoundingClientRect();
        const zoom = editor.zoom || 1;
        const pan = editor.panOffset || { x: 0, y: 0 };
        const input = document.createElement('input');
        input.id = SUMMARY_EDITOR_ID;
        input.type = 'text';
        input.maxLength = 16;
        input.value = packet.summary || window.PacketMethods.getPacketSummary(packet);
        input.style.cssText = `
            position: fixed;
            z-index: 100003;
            left: ${rect.left + (bounds.x - bounds.w / 2) * zoom + pan.x}px;
            top: ${rect.top + (bounds.y - bounds.h / 2) * zoom + pan.y}px;
            width: ${Math.max(64, bounds.w * zoom)}px;
            height: ${Math.max(18, bounds.h * zoom)}px;
            border: 1px solid rgba(0, 220, 255, 0.85);
            border-radius: 5px;
            background: rgba(7, 15, 26, 0.96);
            color: #e6edf3;
            font: 600 11px Arial, sans-serif;
            padding: 1px 6px;
            box-sizing: border-box;
            outline: none;
        `;
        const commit = () => {
            const filtered = _filterValue(input.value, null, {
                printableOnly: true,
                singleLine: true,
                maxLen: 16
            }).value.replace(/[^A-Za-z0-9 ._\-+/]/g, '').replace(/\s+/g, ' ').trim();
            packet.summary = filtered || '';
            _safeSaveState(editor);
            _safeDraw(editor);
            input.remove();
        };
        input.oninput = () => {
            const next = input.value.replace(/[^A-Za-z0-9 ._\-+/]/g, '').slice(0, 16);
            if (next !== input.value) input.value = next;
            packet.summary = next.trim();
            _safeDraw(editor);
        };
        input.onkeydown = (e) => {
            if (e.key === 'Enter') commit();
            if (e.key === 'Escape') input.remove();
        };
        input.onblur = commit;
        input.addEventListener('mousedown', e => e.stopPropagation(), true);
        document.body.appendChild(input);
        input.focus();
        input.select();
    }

    window.PacketPopup = { show, close, showSummaryEditor, LAYER_VALIDATORS, _filterValue };
})();
