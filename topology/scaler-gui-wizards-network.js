/**
 * ScalerGUI: interface, service, VRF, bridge-domain, multihoming wizards
 * Source: split from scaler-gui.js.bak
 * @requires scaler-api.js
 * @requires scaler-gui.js (core)
 */
(function (G) {
    'use strict';
    if (!G) {
        console.error('[scaler-gui-wizards-network.js] ScalerGUI core not loaded');
        return;
    }
    Object.assign(G, {
        // =========================================================================
        // INTERFACE WIZARD (6 Steps)
        // =========================================================================
        
        async openInterfaceWizard(deviceId = null, prefillParams = null) {
            if (!deviceId) {
                this.openDeviceSelector('Interface Wizard', (id) => this.openInterfaceWizard(id, prefillParams));
                return;
            }
            if (!this._isDeviceConfigurable(deviceId)) return;
        
            const content = document.createElement('div');
            content.innerHTML = '<div class="scaler-loading">Loading...</div>';
        
            this.openPanel('interface-wizard', `Interface Wizard - ${deviceId}`, content, {
                width: '540px',
                parentPanel: 'scaler-menu'
            });
        
            const self = this;
            const cachedCtx = this._deviceContexts[deviceId];
            const hasFresh = cachedCtx && (Date.now() - (cachedCtx._fetchedAt || 0)) < this._contextCacheTTL;
            let ctx = hasFresh ? this._applyPendingChanges(deviceId, cachedCtx) : null;
        
            const _ifaceAllSteps = [
                    {
                        id: 'type',
                        title: 'Type',
                        render: (data) => {
                            const ctx = data.deviceContext || {};
                            const parentCount = (() => {
                                const ctx2 = data.deviceContext || {};
                                const phys = (ctx2.interfaces?.physical || []).filter(p => p.oper === 'up');
                                const bun = ctx2.interfaces?.bundle || [];
                                return phys.length + bun.length;
                            })();
                            return `
                            <div class="scaler-form">
                <div class="scaler-form-group">
                    <label>Interface Type</label>
                    <div class="scaler-type-options" id="iface-type-options">
                        <label class="scaler-type-option option-active" data-type="subif">
                            <input type="radio" name="iface-type" value="subif" checked>
                            <span class="option-title">Sub-interface</span>
                            <span class="option-desc">Create sub-interfaces on existing oper-up parents${parentCount ? ` (${parentCount} available)` : ''}</span>
                        </label>
                    </div>
                </div>
                            </div>
                        `;
                        },
                        collectData: () => {
                            return { interfaceType: 'subif', startNumber: 1, count: 1 };
                        }
                    },
                    {
                        id: 'members',
                        title: 'Bundle Members',
                        render: (data) => {
                            if (data.interfaceType !== 'bundle') return '<div class="scaler-info-box">Skip - not creating bundles.</div>';
                            const ctx = data.deviceContext || {};
                            const isDnaas = ctx._isDnaas || false;
                            const lldp = isDnaas ? [] : (ctx.lldp || []);
                            const free = ctx.interfaces?.free_physical || [];
                            const used = new Set();
                            (ctx.interfaces?.bundle || []).forEach(b => (b.members || []).forEach(m => used.add(m)));
                            const lldpItems = lldp.map(n => ({ value: n.local, label: `${n.local} -> ${n.neighbor}` }));
                            const freeItems = free.filter(f => !used.has(f));
                            const noSuggestions = !lldpItems.length && !freeItems.length;
                            return `
                            <div class="scaler-form">
                                <div class="scaler-info-box">Select interfaces to add as bundle members.${isDnaas ? '' : ' LLDP interfaces show neighbor.'}</div>
                                ${isDnaas ? '<div class="scaler-info-box" style="color:var(--dn-orange,#e67e22);font-size:12px">DNAAS fabric device -- LLDP suggestions disabled.</div>' : ''}
                                ${noSuggestions && !isDnaas ? '<div class="scaler-info-box" style="opacity:0.6">No suggestions available. Use "Refresh Live" in the context panel above, or type interface names manually.</div>' : ''}
                                ${lldpItems.length ? `
                                <div class="scaler-form-group">
                                    <label>LLDP interfaces (with neighbor)</label>
                                    <div id="bundle-members-lldp"></div>
                                </div>` : ''}
                                ${freeItems.length ? `
                                <div class="scaler-form-group">
                                    <label>Free physical interfaces (${freeItems.length})</label>
                                    <div id="bundle-members-free"></div>
                                </div>` : ''}
                                <div class="scaler-form-group">
                                    <label>Selected members (comma-separated)</label>
                                    <input type="text" id="bundle-members-input" class="scaler-input" value="${(data.bundleMembers || []).join(', ')}" placeholder="e.g. ge400-0/0/1, ge400-0/0/2">
                                </div>
                                <div class="scaler-form-group">
                                    <label>LACP Mode</label>
                                    <div class="scaler-radio-group">
                                        <label class="scaler-radio"><input type="radio" name="lacp-mode" value="active" ${(data.lacpMode || 'active') === 'active' ? 'checked' : ''}><span>Active</span></label>
                                        <label class="scaler-radio"><input type="radio" name="lacp-mode" value="passive" ${data.lacpMode === 'passive' ? 'checked' : ''}><span>Passive</span></label>
                                        <label class="scaler-radio"><input type="radio" name="lacp-mode" value="static" ${data.lacpMode === 'static' ? 'checked' : ''}><span>Static (no LACP)</span></label>
                                    </div>
                                </div>
                            </div>
                        `;
                        },
                        afterRender: (data) => {
                            if (data.interfaceType !== 'bundle') return;
                            const ctx = data.deviceContext || {};
                            const isDnaas = ctx._isDnaas || false;
                            const lldp = isDnaas ? [] : (ctx.lldp || []).map(n => ({ value: n.local, label: `${n.local} -> ${n.neighbor}` }));
                            const free = (ctx.interfaces?.free_physical || []).filter(f => {
                                const used = new Set();
                                (ctx.interfaces?.bundle || []).forEach(b => (b.members || []).forEach(m => used.add(m)));
                                return !used.has(f);
                            });
                            const input = document.getElementById('bundle-members-input');
                            const toggleMember = (v, _t, btn) => {
                                const cur = (input.value || '').split(',').map(s => s.trim()).filter(Boolean);
                                const idx = cur.indexOf(v);
                                if (idx >= 0) {
                                    cur.splice(idx, 1);
                                    if (btn) btn.classList.remove('chip-selected');
                                } else {
                                    cur.push(v);
                                    if (btn) btn.classList.add('chip-selected');
                                }
                                input.value = cur.join(', ');
                            };
                            const lldpDiv = document.getElementById('bundle-members-lldp');
                            const freeDiv = document.getElementById('bundle-members-free');
                            const curMembers = (data.bundleMembers || []).map(String);
                            const lldpChips = lldp.length ? ScalerGUI.renderSuggestionChips(lldp, { type: 'lldp', onSelect: toggleMember }) : null;
                            const freeChips = free.length ? ScalerGUI.renderSuggestionChips(free, { type: 'free', onSelect: toggleMember }) : null;
                            if (lldpDiv && lldpChips) {
                                lldpDiv.appendChild(lldpChips);
                                lldpDiv.querySelectorAll('.suggestion-chip').forEach(btn => {
                                    if (curMembers.includes(btn.dataset.value)) btn.classList.add('chip-selected');
                                });
                            }
                            if (freeDiv && freeChips) {
                                freeDiv.appendChild(freeChips);
                                freeDiv.querySelectorAll('.suggestion-chip').forEach(btn => {
                                    if (curMembers.includes(btn.dataset.value)) btn.classList.add('chip-selected');
                                });
                            }
                        },
                        collectData: () => ({
                            bundleMembers: (document.getElementById('bundle-members-input')?.value || '').split(',').map(s => s.trim()).filter(Boolean),
                            lacpMode: document.querySelector('input[name="lacp-mode"]:checked')?.value || 'active'
                        }),
                        skipable: true
                    },
                    {
                        id: 'parent',
                        title: 'Select Parent',
                        render: (data) => {
                            const ctx = data.deviceContext || {};
                            const bundles = ctx.interfaces?.bundle || [];
                            const physical = (ctx.interfaces?.physical || []).filter(p => p.oper === 'up');
                            const selected = data.subifParents || [];
        
                            const renderGroup = (label, items, nameKey) => {
                                if (!items.length) return `<div style="opacity:.5;margin:8px 0">${label}: none available</div>`;
                                return `<div style="margin:8px 0">
                                    <label style="font-size:12px;opacity:.7;margin-bottom:4px;display:block">${label}</label>
                                    <div style="display:flex;flex-wrap:wrap;gap:6px">
                                        ${items.map(it => {
                                            const name = typeof it === 'string' ? it : (it[nameKey] || it.name);
                                            const isSel = selected.includes(name);
                                            const memberInfo = it.members ? ` (${it.members.length} members)` : '';
                                            const speedInfo = it.speed ? ` ${it.speed}` : '';
                                            return `<button type="button" class="suggestion-chip chip-config ${isSel ? 'chip-selected' : ''}"
                                                data-value="${name}" style="cursor:pointer;padding:6px 12px;font-size:12px">
                                                ${name}${memberInfo}${speedInfo}
                                            </button>`;
                                        }).join('')}
                                    </div>
                                </div>`;
                            };
        
                            return `<div class="scaler-form">
                                <div class="scaler-info-box">
                                    Select parent interfaces to create sub-interfaces on.
                                    Only oper-up interfaces are shown.
                                </div>
                                <div id="parent-bundles">${renderGroup('Bundles', bundles, 'name')}</div>
                                <div id="parent-physical">${renderGroup('Physical (oper-up)', physical, 'name')}</div>
                                <div style="margin-top:12px">
                                    <label style="font-size:12px;opacity:.7">Selected parents:</label>
                                    <div id="parent-selected-display" style="margin-top:4px;font-family:monospace;font-size:12px;color:var(--dn-cyan,#3498db)">
                                        ${selected.length ? selected.join(', ') : 'None -- click interfaces above'}
                                    </div>
                                </div>
                                <input type="hidden" id="parent-selected-input" value="${selected.join(',')}">
                            </div>`;
                        },
                        afterRender: async (data) => {
                            const chips = document.querySelectorAll('#parent-bundles .suggestion-chip, #parent-physical .suggestion-chip');
                            const display = document.getElementById('parent-selected-display');
                            const input = document.getElementById('parent-selected-input');
                            const selected = new Set(data.subifParents || []);
        
                            const fetchDetectedPattern = async (firstParent) => {
                                if (!firstParent || !data.deviceId) return;
                                const ctx = data.deviceContext || {};
                                const sshHost = ctx.mgmt_ip || ctx.ip || '';
                                try {
                                    const pattern = await ScalerAPI.detectPattern({
                                        device_id: data.deviceId,
                                        ssh_host: sshHost,
                                        parent_interface: firstParent
                                    });
                                    if (ScalerGUI.WizardController?.data) {
                                        ScalerGUI.WizardController.data.detectedPattern = pattern;
                                    }
                                } catch (_) {
                                    if (ScalerGUI.WizardController?.data) {
                                        ScalerGUI.WizardController.data.detectedPattern = null;
                                    }
                                }
                            };
        
                            const updateDisplay = () => {
                                const arr = [...selected];
                                if (display) display.textContent = arr.length ? arr.join(', ') : 'None -- click interfaces above';
                                if (input) input.value = arr.join(',');
                                if (arr.length > 0) fetchDetectedPattern(arr[0]);
                                else if (ScalerGUI.WizardController?.data) ScalerGUI.WizardController.data.detectedPattern = null;
                            };
        
                            chips.forEach(chip => {
                                chip.addEventListener('click', () => {
                                    const val = chip.dataset.value;
                                    if (selected.has(val)) {
                                        selected.delete(val);
                                        chip.classList.remove('chip-selected');
                                    } else {
                                        selected.add(val);
                                        chip.classList.add('chip-selected');
                                    }
                                    updateDisplay();
                                });
                            });
                            if (selected.size > 0) fetchDetectedPattern([...selected][0]);
                        },
                        collectData: () => {
                            const val = document.getElementById('parent-selected-input')?.value || '';
                            const parents = val.split(',').filter(Boolean);
                            return {
                                subifParents: parents,
                                count: Math.max(parents.length, 1),
                                startNumber: 1
                            };
                        }
                    },
                    {
                        id: 'subifs',
                        get title() {
                            const t = (ScalerGUI.WizardController.data?.interfaceType || 'subif');
                            return 'Mode & Features';
                            return 'Sub-ifs & IP';
                        },
                        render: (data) => {
                            const t = data.interfaceType || 'subif';
                            const isLoopback = t === 'loopback';
                            const isBasic = ['bundle', 'ph', 'irb'].includes(t);
                            const isPhysical = t === 'subif';
        
                            if (isLoopback) return `<div class="scaler-form">
                                <div class="scaler-info-box">Loopback interfaces (lo) -- no sub-interfaces.
                                IPv4 with /32 prefix. Matches terminal wizard loopback flow.</div>
                                <div class="scaler-form-group">
                                    <label>Description (optional)</label>
                                    <input type="text" id="lo-desc" class="scaler-input" value="${data.description || ''}" placeholder="e.g. Management loopback">
                                </div>
                                <div class="scaler-form-group">
                                    <label>IPv4 Address (optional)</label>
                                    <input type="text" id="ip-start" class="scaler-input" value="${data.ipStart || ''}" placeholder="e.g. 1.1.1.1/32">
                                </div>
                                <div class="scaler-preview-box"><label>DNOS SYNTAX PREVIEW:</label>
                                    <pre id="subif-preview" class="scaler-syntax-preview">Loading...</pre>
                                </div></div>`;
        
                            const defaultPrefix = isPhysical ? 30 : 31;
                            const isSubifMode = t === 'subif';
                            const parentNames = isSubifMode ? (data.subifParents || []) : [];
                            const parentLabel = isSubifMode && parentNames.length
                                ? `<div class="scaler-info-box" style="margin-bottom:10px">Creating sub-interfaces on: <strong>${parentNames.join(', ')}</strong></div>`
                                : '';
                            return `
                            <div class="scaler-form">
                                ${parentLabel}
                                ${isSubifMode ? '<input type="checkbox" id="create-subif" checked style="display:none">' : `
                                <label class="scaler-switch" for="create-subif">
                                    <input type="checkbox" id="create-subif" ${data.createSubinterfaces !== false ? 'checked' : ''}>
                                    <span class="scaler-switch-track"></span>
                                    <span class="scaler-switch-label">Create Sub-interfaces</span>
                                </label>`}
                                <div id="subif-options" class="scaler-collapse-section ${data.createSubinterfaces === false && !isSubifMode ? 'collapsed' : ''}" style="margin-top:10px">
                                    <div class="scaler-form-group">
                                        <label>Sub-interfaces per Parent</label>
                                        <input type="number" id="subif-count" class="scaler-input" value="${data.subifCount || 1}" min="1" max="4094">
                                    </div>
                                </div>
                                ${isPhysical ? `
                                <div class="scaler-form-group" style="margin-top:12px">
                                    <label>Interface Mode</label>
                                    <div class="scaler-radio-group">
                                        <label class="scaler-radio"><input type="radio" name="iface-mode" value="l3" ${data.interfaceMode !== 'l2' ? 'checked' : ''}><span>L3 (Routing -- IP, MPLS)</span></label>
                                        <label class="scaler-radio"><input type="radio" name="iface-mode" value="l2" ${data.interfaceMode === 'l2' ? 'checked' : ''}><span>L2 (l2-service for xconnect/EVPN)</span></label>
                                    </div>
                                </div>
                                <div id="l2-info" style="display:${data.interfaceMode === 'l2' ? 'block' : 'none'}">
                                    <div class="scaler-info-box">L2 mode adds <code>l2-service enabled</code> to each sub-interface.
                                    Cannot combine with IP addressing (DNOS rule).</div>
                                </div>
                                <div id="l2l3-conflict-warning" class="scaler-l2l3-conflict" style="display:none"></div>` : ''}
                                    <div id="ip-section" style="display:${isPhysical && data.interfaceMode === 'l2' ? 'none' : 'block'}">
                                    <div class="scaler-form-group" style="margin-top:12px">
                                        <label>IP Addressing</label>
                                        <div class="scaler-form-row" style="align-items:center;gap:8px;margin-bottom:8px">
                                            <label style="font-size:11px;color:var(--scaler-text-dim,#999);white-space:nowrap" title="How IPs are distributed across sub-interfaces and parents">IP Mode</label>
                                            <select id="ip-mode" class="scaler-input" style="max-width:180px" title="per_subif: sequential per sub-if | per_parent: reset per parent | unique_subnet: one subnet per sub-if | octet_step: use dotted step value">
                                                <option value="per_subif" ${(data.ipMode || 'per_subif') === 'per_subif' ? 'selected' : ''}>Per sub-interface</option>
                                                <option value="per_parent" ${data.ipMode === 'per_parent' ? 'selected' : ''}>Per parent</option>
                                                <option value="unique_subnet" ${data.ipMode === 'unique_subnet' ? 'selected' : ''}>Unique subnet</option>
                                                <option value="octet_step" ${data.ipMode === 'octet_step' ? 'selected' : ''}>Octet step</option>
                                            </select>
                                        </div>
                                        <div class="scaler-radio-group">
                                            <label class="scaler-radio"><input type="radio" name="ip-version" value="none" ${!data.ipEnabled ? 'checked' : ''}><span>None</span></label>
                                            <label class="scaler-radio"><input type="radio" name="ip-version" value="ipv4" ${data.ipVersion === 'ipv4' ? 'checked' : ''}><span>IPv4</span></label>
                                            <label class="scaler-radio"><input type="radio" name="ip-version" value="ipv6" ${data.ipVersion === 'ipv6' ? 'checked' : ''}><span>IPv6</span></label>
                                            <label class="scaler-radio"><input type="radio" name="ip-version" value="dual" ${data.ipVersion === 'dual' ? 'checked' : ''}><span>Dual-stack</span></label>
                                        </div>
                                    </div>
                                    <div id="ip-options" style="display:${data.ipEnabled ? 'block' : 'none'}">
                                        <div class="scaler-form-row">
                                            <div class="scaler-form-group">
                                                <label>IPv4 Start</label>
                                                <input type="text" id="ip-start" class="scaler-input" value="${data.ipStart || '10.0.0.1'}" placeholder="10.0.0.1">
                                            </div>
                                            <div class="scaler-form-group">
                                                <label>Prefix Length</label>
                                                <input type="number" id="ip-prefix" class="scaler-input" value="${data.ipPrefix || defaultPrefix}" min="1" max="128">
                                            </div>
                                        </div>
                                        <div id="ipv6-row" class="scaler-form-row" style="display:${data.ipVersion === 'dual' ? 'flex' : 'none'}">
                                            <div class="scaler-form-group">
                                                <label>IPv6 Start</label>
                                                <input type="text" id="ipv6-start" class="scaler-input" value="${data.ipv6Start || '2001:db8::1'}" placeholder="2001:db8::1">
                                            </div>
                                            <div class="scaler-form-group">
                                                <label>IPv6 Prefix</label>
                                                <input type="number" id="ipv6-prefix" class="scaler-input" value="${data.ipv6Prefix || 128}" min="1" max="128">
                                            </div>
                                        </div>
                                        <div class="scaler-form-group">
                                            <label>IP Step (per sub-interface)</label>
                                            <div class="scaler-form-row" style="align-items:center;gap:8px;flex-wrap:wrap">
                                                <input type="text" id="ip-step-dotted" class="scaler-input" value="${data.ipStepDotted || data.ipStep || '0.0.0.1'}" placeholder="0.0.0.1" style="max-width:120px" pattern="[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+">
                                                <div class="scaler-step-presets" id="ip-step-presets">
                                                    <button type="button" class="scaler-step-chip" data-step="0.0.0.1" title="Increment by 1 in the last octet. Example: 10.0.0.1, 10.0.0.2, 10.0.0.3">+1</button>
                                                    <button type="button" class="scaler-step-chip" data-step="0.0.1.0" title="Increment by 1 in the third octet. Example: 10.0.0.1, 10.0.1.1, 10.0.2.1">+octet3</button>
                                                    <button type="button" class="scaler-step-chip" data-step="auto" title="Auto-calculate step from prefix length so each sub-interface gets its own subnet. Example: /31 = step 0.0.0.2, /30 = step 0.0.0.4">/prefix</button>
                                                </div>
                                            </div>
                                            <div id="ip-step-preview" class="scaler-info-box" style="font-size:10px;margin-top:4px">Preview: 10.0.0.1, 10.0.0.2, 10.0.0.3...</div>
                                        </div>
                                        <div id="ip-validation-warning" class="scaler-info-box" style="display:none;color:var(--dn-orange,#e67e22);border-color:var(--dn-orange,#e67e22);margin-top:8px"></div>
                                        <div id="ip-overlap-warning" class="scaler-collision-warning" style="display:none;margin-top:8px"></div>
                                        <div id="ip-used-summary" class="scaler-info-box" style="display:none;font-size:11px;margin-top:6px"></div>
                                    </div>
                                </div>
                                ${isPhysical ? `
                                <div id="iface-desc-row" class="scaler-form-group" style="margin-top:8px">
                                    <label>Description (optional, use {i} for index)</label>
                                    <input type="text" id="iface-desc" class="scaler-input" value="${data.description || ''}" placeholder="e.g. WAN link {i}">
                                </div>
                                <div id="l3-features" style="display:${data.interfaceMode === 'l2' ? 'none' : 'flex'};flex-wrap:wrap;gap:12px;margin-top:10px">
                                    <label><input type="checkbox" id="mpls-enabled" ${data.mplsEnabled ? 'checked' : ''}> MPLS</label>
                                    <label><input type="checkbox" id="flowspec-enabled" ${data.flowspecEnabled ? 'checked' : ''}> Flowspec</label>
                                    <label><input type="checkbox" id="bfd-enabled" ${data.bfdEnabled ? 'checked' : ''}> BFD</label>
                                </div>
                                <div id="bfd-options-row" class="scaler-form-row" style="display:${(data.bfdEnabled && isPhysical && data.interfaceMode !== 'l2') ? 'flex' : 'none'};margin-top:6px;gap:12px">
                                    <div class="scaler-form-group" style="max-width:100px"><label>BFD Interval (ms)</label><input type="number" id="bfd-interval" class="scaler-input" value="${data.bfdInterval || ''}" placeholder="100" min="50"></div>
                                    <div class="scaler-form-group" style="max-width:100px"><label>BFD Multiplier</label><input type="number" id="bfd-multiplier" class="scaler-input" value="${data.bfdMultiplier || ''}" placeholder="3" min="2"></div>
                                </div>
                                <div id="mtu-row" class="scaler-form-row" style="display:${data.interfaceMode === 'l2' ? 'none' : 'flex'};margin-top:8px">
                                    <div class="scaler-form-group">
                                        <label>MTU (optional)</label>
                                        <input type="number" id="iface-mtu" class="scaler-input" value="${data.mtu || ''}" placeholder="9000" min="64" max="9216">
                                    </div>
                                </div>` : ''}
                                <div id="subif-limits-warning" class="scaler-limits-warning" style="display:none"></div>
                                <div class="scaler-preview-box"><label>DNOS SYNTAX PREVIEW:</label>
                                    <pre id="subif-preview" class="scaler-syntax-preview">Loading...</pre>
                                </div>
                            </div>`;
                        },
                        afterRender: (data) => {
                            const t = data.interfaceType || 'subif';
                            const isLoopback = t === 'loopback';
                            const isPhysical = t === 'subif';
                            const parentCount = Math.min(data.count || 10, 2);
                            let debounceTimer;
        
                            const isSubif = t === 'subif';
                            const _buildPreviewParams = () => {
                                if (isLoopback) {
                                    return {
                                        interface_type: 'loopback',
                                        start_number: data.startNumber ?? 0,
                                        count: Math.min(data.count || 1, 3),
                                        ip_enabled: !!document.getElementById('ip-start')?.value,
                                        ip_start: document.getElementById('ip-start')?.value || '',
                                        ip_prefix: 32,
                                        description: document.getElementById('lo-desc')?.value || '',
                                    };
                                }
                                const ifaceMode = document.querySelector('input[name="iface-mode"]:checked')?.value || 'l3';
                                const isL2 = (isPhysical || isSubif) && ifaceMode === 'l2';
                                const ipVer = isL2 ? 'none' : (document.querySelector('input[name="ip-version"]:checked')?.value || 'none');
                                const ipEnabled = ipVer !== 'none';
                                const parents = data.subifParents || [];
                                const effectiveType = isSubif ? 'subif' : t;
                                return {
                                    interface_type: effectiveType,
                                    start_number: data.startNumber || 1,
                                    count: isSubif ? Math.min(parents.length || 1, 2) : parentCount,
                                    parent_interfaces: isSubif ? parents.slice(0, 2) : undefined,
                                    slot: data.slot || 0,
                                    bay: data.bay || 0,
                                    port_start: data.portStart || 0,
                                    create_subinterfaces: document.getElementById('create-subif')?.checked ?? true,
                                    subif_count_per_interface: Math.min(parseInt(document.getElementById('subif-count')?.value) || 1, 3),
                                    subif_vlan_start: data.vlanStart || 100,
                                    subif_vlan_step: data.vlanStep || 1,
                                    vlan_mode: data.encapsulation === 'qinq' ? 'qinq' : 'single',
                                    l2_service: isL2,
                                    ip_enabled: ipEnabled,
                                    ip_version: ipVer,
                                    ip_start: document.getElementById('ip-start')?.value || '10.0.0.1',
                                    ip_prefix: parseInt(document.getElementById('ip-prefix')?.value) || 30,
                                    ipv6_start: document.getElementById('ipv6-start')?.value || '2001:db8::1',
                                    ipv6_prefix: parseInt(document.getElementById('ipv6-prefix')?.value) || 128,
                                    ip_step: document.getElementById('ip-step-dotted')?.value || '0.0.0.1',
                                    mpls_enabled: isPhysical ? (document.getElementById('mpls-enabled')?.checked || false) : false,
                                    flowspec_enabled: isPhysical ? (document.getElementById('flowspec-enabled')?.checked || false) : false,
                                    bfd: isPhysical ? (document.getElementById('bfd-enabled')?.checked || false) : false,
                                    bfd_interval: isPhysical && document.getElementById('bfd-enabled')?.checked ? (document.getElementById('bfd-interval')?.value || undefined) : undefined,
                                    bfd_multiplier: isPhysical && document.getElementById('bfd-enabled')?.checked ? (document.getElementById('bfd-multiplier')?.value || undefined) : undefined,
                                    description: document.getElementById('iface-desc')?.value || '',
                                    mtu: isPhysical ? (parseInt(document.getElementById('iface-mtu')?.value) || null) : null,
                                };
                            };
        
                            const updatePreview = async () => {
                                clearTimeout(debounceTimer);
                                debounceTimer = setTimeout(async () => {
                                    const preview = document.getElementById('subif-preview');
                                    if (!preview) return;
                                    try {
                                        const params = _buildPreviewParams();
                                        const result = await ScalerAPI.generateInterfaces(params);
                                        const actualCount = data.count || 10;
                                        const subifCount = parseInt(document.getElementById('subif-count')?.value) || 1;
                                        const lines = result.config.split('\n').slice(0, 25);
                                        preview.textContent = lines.join('\n') +
                                            (actualCount > 2 || subifCount > 3 ? `\n... (${actualCount} parents x ${subifCount} sub-ifs)` : '');
                                    } catch (e) {
                                        preview.textContent = `Error: ${e.message}`;
                                    }
                                    updateLimitsWarning();
                                }, 300);
                            };
        
                            const _limitsCache = { key: null, val: null, ts: 0 };
                            const updateLimitsWarning = async () => {
                                const el = document.getElementById('subif-limits-warning');
                                const isLoopbackLocal = (data.interfaceType || 'subif') === 'loopback';
                                if (!el || isLoopbackLocal) return;
                                const createSub = document.getElementById('create-subif')?.checked ?? false;
                                if (!createSub) {
                                    el.style.display = 'none';
                                    return;
                                }
                                const count = data.count || 0;
                                const subifCount = parseInt(document.getElementById('subif-count')?.value) || 1;
                                const total = count * subifCount;
                                if (total <= 0) {
                                    el.style.display = 'none';
                                    return;
                                }
                                try {
                                    const devId = data.deviceId || '';
                                    const now = Date.now();
                                    if (_limitsCache.key !== devId || now - _limitsCache.ts > 60000) {
                                        _limitsCache.key = devId;
                                        _limitsCache.val = await ScalerAPI.getLimits(devId);
                                        _limitsCache.ts = now;
                                    }
                                    const maxSubifs = _limitsCache.val.max_subifs || 20480;
                                    if (total > maxSubifs) {
                                        el.textContent = `Total sub-interfaces (${total}) exceeds platform limit (${maxSubifs}). Push may fail.`;
                                        el.style.display = 'block';
                                        el.className = 'scaler-limits-warning scaler-limits-warning-exceeded';
                                    } else {
                                        el.style.display = 'none';
                                    }
                                } catch {
                                    el.style.display = 'none';
                                }
                            };
        
                            if (isLoopback) {
                                document.getElementById('ip-start')?.addEventListener('input', updatePreview);
                                document.getElementById('lo-desc')?.addEventListener('input', updatePreview);
                                updatePreview();
                                return;
                            }
        
                            const validateIpAddress = () => {
                                const warn = document.getElementById('ip-validation-warning');
                                if (!warn) return;
                                const ipVer = document.querySelector('input[name="ip-version"]:checked')?.value;
                                if (!ipVer || ipVer === 'none') { warn.style.display = 'none'; return; }
                                const ipStr = (document.getElementById('ip-start')?.value || '').trim();
                                const prefix = parseInt(document.getElementById('ip-prefix')?.value) || 30;
                                const msgs = [];
                                if (ipStr && ipStr.includes('.') && prefix < 31) {
                                    const parts = ipStr.split('/')[0].split('.');
                                    if (parts.length === 4) {
                                        const ipInt = parts.reduce((a, o) => (a << 8) + (parseInt(o) || 0), 0) >>> 0;
                                        const mask = (0xFFFFFFFF << (32 - prefix)) >>> 0;
                                        const netAddr = (ipInt & mask) >>> 0;
                                        const bcastAddr = (netAddr | (~mask >>> 0)) >>> 0;
                                        const _ipStr = (v) => [(v>>>24)&255,(v>>>16)&255,(v>>>8)&255,v&255].join('.');
                                        if (ipInt === netAddr)
                                            msgs.push(`${ipStr} is the network address for /${prefix}. Use ${_ipStr(netAddr + 1)} instead.`);
                                        else if (ipInt === bcastAddr)
                                            msgs.push(`${ipStr} is the broadcast address for /${prefix}. Use a host address.`);
                                        const dotted = document.getElementById('ip-step-dotted')?.value || '0.0.0.1';
                                        const step = dotted.includes('.') ? (() => { try { const p = dotted.trim().split('.'); if (p.length !== 4) return 1; return (parseInt(p[0]) << 24) + (parseInt(p[1]) << 16) + (parseInt(p[2]) << 8) + parseInt(p[3]); } catch { return 1; } })() : (parseInt(dotted) || 1);
                                        const count = parseInt(document.getElementById('subif-count')?.value) || 1;
                                        if (count > 1) {
                                            for (let idx = 1; idx < Math.min(count, 10); idx++) {
                                                const nextIp = ipInt + (idx * step);
                                                const nextMask = (0xFFFFFFFF << (32 - prefix)) >>> 0;
                                                const nextNet = (nextIp & nextMask) >>> 0;
                                                const nextBcast = (nextNet | (~nextMask >>> 0)) >>> 0;
                                                if (nextIp === nextNet || nextIp === nextBcast) {
                                                    const o = [(nextIp>>>24)&255,(nextIp>>>16)&255,(nextIp>>>8)&255,nextIp&255].join('.');
                                                    msgs.push(`Sub-if #${idx + 1} would get ${o}/${prefix} (${nextIp === nextNet ? 'network' : 'broadcast'} address). Backend will auto-skip to next valid host.`);
                                                    break;
                                                }
                                            }
                                        }
                                    }
                                }
                                if (msgs.length) { warn.innerHTML = msgs.join('<br>'); warn.style.display = 'block'; }
                                else { warn.style.display = 'none'; }
                            };
        
                            let _ipScanCache = { key: null, val: null, ts: 0 };
                            let _ipOverlapDebounce = null;
                            let _ipScanAbort = null;
                            const updateIPOverlapBanner = async () => {
                                clearTimeout(_ipOverlapDebounce);
                                if (_ipScanAbort) { _ipScanAbort.abort(); _ipScanAbort = null; }
                                _ipOverlapDebounce = setTimeout(async () => {
                                const ctrl = new AbortController();
                                _ipScanAbort = ctrl;
                                const warnEl = document.getElementById('ip-overlap-warning');
                                const summaryEl = document.getElementById('ip-used-summary');
                                if (!warnEl || !summaryEl) return;
                                const ipVer = document.querySelector('input[name="ip-version"]:checked')?.value;
                                if (!ipVer || ipVer === 'none') { warnEl.style.display = 'none'; summaryEl.style.display = 'none'; return; }
                                const devId = data.deviceId || '';
                                const ctx = data.deviceContext || {};
                                const sshHost = ctx.mgmt_ip || ctx.ip || '';
                                if (!devId) { warnEl.style.display = 'none'; summaryEl.style.display = 'none'; return; }
                                const ipv4Start = (document.getElementById('ip-start')?.value || '').trim().split('/')[0];
                                const ipv6Start = (document.getElementById('ipv6-start')?.value || '').trim().split('/')[0];
                                const ipv4Prefix = parseInt(document.getElementById('ip-prefix')?.value) || 31;
                                const ipv6Prefix = parseInt(document.getElementById('ipv6-prefix')?.value) || 127;
                                const ipStepDotted = (document.getElementById('ip-step-dotted')?.value || '0.0.0.1').trim();
                                const parentCount = (data.subifParents || []).length || 1;
                                const subifCount = parseInt(document.getElementById('subif-count')?.value, 10) || 1;
                                const ipv4Count = parentCount * subifCount;
                                const parent = (data.subifParents || [])[0];
                                try {
                                    const now = Date.now();
                                    const needOverlapCheck = (ipVer !== 'ipv6' && ipv4Start) || ((ipVer === 'dual' || ipVer === 'ipv6') && ipv6Start);
                                    const cacheKey = needOverlapCheck ? null : `${devId}:${parent || ''}`;
                                    if (!needOverlapCheck && _ipScanCache.key === `${devId}:${parent || ''}` && now - _ipScanCache.ts < 60000) {
                                        /* use cached */
                                    } else {
                                        _ipScanCache.key = cacheKey || `${devId}:${parent || ''}`;
                                        _ipScanCache.val = await ScalerAPI.scanIPs({
                                            device_id: devId,
                                            ssh_host: sshHost,
                                            parent_interface: parent || undefined,
                                            ipv4_prefix: ipv4Prefix,
                                            ipv6_prefix: ipv6Prefix,
                                            ipv4_count: ipv4Count,
                                            ipv6_count: ipv4Count,
                                            ipv4_step_dotted: ipStepDotted,
                                            preferred_ipv4_base: ipv4Start || undefined,
                                            preferred_ipv6_base: (ipVer === 'dual' || ipVer === 'ipv6') && ipv6Start ? ipv6Start : undefined,
                                            check_ipv4: ipv4Start || undefined,
                                            check_ipv6: (ipVer === 'dual' || ipVer === 'ipv6') && ipv6Start ? ipv6Start : undefined,
                                        });
                                        if (ctrl.signal.aborted) return;
                                        _ipScanCache.ts = now;
                                    }
                                    const scan = _ipScanCache.val;
                                    const used = scan.used_ips || {};
                                    const suggestion = scan.suggestion || {};
                                    const overlap = scan.overlap_check || {};
                                    const usedV4 = used.ipv4 || [];
                                    const usedV6 = used.ipv6 || [];
                                    const nV4 = usedV4.length, nV6 = usedV6.length;
                                    const overlaps = overlap.overlaps || [];
                                    const hasOverlap = overlaps.length > 0 && (ipv4Start || ipv6Start);
                                    const hasUsed = nV4 > 0 || nV6 > 0;
        
                                    const sugV4 = suggestion.ipv4_start || '';
                                    const sugV6 = suggestion.ipv6_start || '';
                                    const hasSuggestion = sugV4 || sugV6;
                                    const _applySuggestion = () => {
                                        const changes = [];
                                        if (sugV4) {
                                            const el = document.getElementById('ip-start');
                                            if (el) {
                                                const prev = el.value;
                                                el.value = sugV4;
                                                el.dispatchEvent(new Event('input', { bubbles: true }));
                                                if (prev !== sugV4) changes.push(`IPv4: ${prev || '(empty)'} -> ${sugV4}`);
                                            }
                                        }
                                        if (sugV6) {
                                            const el = document.getElementById('ipv6-start');
                                            if (el) {
                                                const prev = el.value;
                                                el.value = sugV6;
                                                el.dispatchEvent(new Event('input', { bubbles: true }));
                                                if (prev !== sugV6) changes.push(`IPv6: ${prev || '(empty)'} -> ${sugV6}`);
                                            }
                                        }
                                        const btn = document.getElementById('ip-apply-suggested');
                                        if (btn) {
                                            btn.classList.add('scaler-ip-scan-applied');
                                            btn.textContent = changes.length ? 'Applied' : 'Already set';
                                            btn.disabled = true;
                                            setTimeout(() => {
                                                btn.classList.remove('scaler-ip-scan-applied');
                                                btn.disabled = false;
                                                btn.textContent = hasOverlap ? 'Fix overlap' : 'Use next available';
                                            }, 2000);
                                        }
                                        if (changes.length) {
                                            self.showNotification(`IP updated: ${changes.join(', ')}`, 'info');
                                        }
                                        _ipScanCache.ts = 0;
                                        updatePreview();
                                        updateIPOverlapBanner();
                                    };
        
                                    warnEl.style.display = 'none';
                                    summaryEl.style.display = 'none';
        
                                    if (hasUsed || hasOverlap) {
                                        summaryEl.style.display = 'block';
                                        summaryEl.className = hasOverlap
                                            ? 'scaler-ip-scan-panel scaler-ip-scan-overlap'
                                            : 'scaler-ip-scan-panel scaler-ip-scan-ok';
        
                                        let html = '';
                                        if (hasOverlap) {
                                            const raw = overlaps[0] || '';
                                            const match = raw.match(/IPv[46]\s+(\S+)\s+overlaps with\s+(\S+)/);
                                            const yourRange = match ? match[1] : '';
                                            const existingRange = match ? match[2] : '';
                                            html += `<div class="scaler-ip-scan-status scaler-ip-scan-status-error">
                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                                                <span>Overlap: <code>${yourRange}</code> conflicts with <code>${existingRange}</code></span>
                                            </div>`;
                                        } else {
                                            html += `<div class="scaler-ip-scan-status scaler-ip-scan-status-ok">
                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                                                <span>No overlap detected</span>
                                            </div>`;
                                        }
        
                                        let ipRows = '';
                                        if (nV4) {
                                            const v4Items = usedV4.slice(0, 3).map(u => `<code>${u.address}/${u.prefix}</code>`).join(' ');
                                            ipRows += `<div class="scaler-ip-scan-row"><span class="scaler-ip-scan-label">IPv4 (${nV4})</span>${v4Items}${nV4 > 3 ? ` <span class="scaler-ip-scan-more">+${nV4 - 3} more</span>` : ''}</div>`;
                                        }
                                        if (nV6) {
                                            const v6Items = usedV6.slice(0, 3).map(u => `<code>${u.address}/${u.prefix}</code>`).join(' ');
                                            ipRows += `<div class="scaler-ip-scan-row"><span class="scaler-ip-scan-label">IPv6 (${nV6})</span>${v6Items}${nV6 > 3 ? ` <span class="scaler-ip-scan-more">+${nV6 - 3} more</span>` : ''}</div>`;
                                        }
                                        if (ipRows) {
                                            html += `<div class="scaler-ip-scan-ips">${ipRows}</div>`;
                                        }
        
                                        if (hasSuggestion) {
                                            const sugLabel = [sugV4, sugV6].filter(Boolean).join(' / ');
                                            const btnLabel = hasOverlap ? 'Fix overlap -- apply suggested IPs' : 'Apply suggested IPs';
                                            const btnTitle = `Sets start IPs to: ${sugLabel}. This skips past all existing addresses on the device.`;
                                            html += `<div class="scaler-ip-scan-footer">
                                                <span class="scaler-ip-scan-suggestion">Suggested start: <code>${sugLabel}</code></span>
                                                <button type="button" class="scaler-ip-scan-apply" id="ip-apply-suggested" title="${btnTitle}">${btnLabel}</button>
                                            </div>`;
                                        }
        
                                        summaryEl.innerHTML = html;
                                        document.getElementById('ip-apply-suggested')?.addEventListener('click', _applySuggestion);
                                    }
                                } catch (_) {
                                    warnEl.style.display = 'none';
                                    summaryEl.style.display = 'none';
                                }
                                }, 400);
                            };
        
                            document.getElementById('create-subif')?.addEventListener('change', (e) => {
                                const opts = document.getElementById('subif-options');
                                if (opts) {
                                    if (e.target.checked) opts.classList.remove('collapsed');
                                    else opts.classList.add('collapsed');
                                }
                                updatePreview();
                            });
                            document.getElementById('subif-count')?.addEventListener('input', updatePreview);
        
                            const updateL2L3ConflictWarning = async () => {
                                const warnEl = document.getElementById('l2l3-conflict-warning');
                                if (!warnEl || !isSubif) return;
                                const parent = (data.subifParents || [])[0];
                                if (!parent || !data.deviceId) { warnEl.style.display = 'none'; return; }
                                const ifaceMode = document.querySelector('input[name="iface-mode"]:checked')?.value || 'l3';
                                const ctx = data.deviceContext || {};
                                const sshHost = ctx.mgmt_ip || ctx.ip || '';
                                try {
                                    const scan = await ScalerAPI.scanExisting({
                                        device_id: data.deviceId,
                                        ssh_host: sshHost,
                                        scan_type: 'interfaces',
                                        parent_interface: parent
                                    });
                                    const l3Conflicts = scan.l3_conflicts || [];
                                    const l2SubIds = scan.l2_sub_ids || [];
                                    const isL2 = ifaceMode === 'l2';
                                    if (isL2 && l3Conflicts.length > 0) {
                                        warnEl.style.display = 'block';
                                        warnEl.innerHTML = `<div class="scaler-l2l3-title">L2/L3 conflict: ${l3Conflicts.length} existing sub-if(s) have IP addresses (L3). Creating L2 here may conflict.</div>
                                            <button type="button" class="scaler-step-chip" data-action="auto-skip-l2l3" data-ids="${l3Conflicts.join(',')}">Auto-skip conflicting IDs</button>
                                            <button type="button" class="scaler-step-chip scaler-step-chip--outline" data-action="ignore-l2l3">Ignore</button>`;
                                        warnEl.querySelector('[data-action="auto-skip-l2l3"]')?.addEventListener('click', () => {
                                            if (ScalerGUI.WizardController?.data) {
                                                ScalerGUI.WizardController.data._l2l3SkipIds = l3Conflicts;
                                            }
                                            warnEl.style.display = 'none';
                                            updatePreview();
                                        });
                                        warnEl.querySelector('[data-action="ignore-l2l3"]')?.addEventListener('click', () => {
                                            if (ScalerGUI.WizardController?.data) ScalerGUI.WizardController.data._l2l3SkipIds = null;
                                            warnEl.style.display = 'none';
                                        });
                                    } else if (!isL2 && l2SubIds.length > 0) {
                                        warnEl.style.display = 'block';
                                        warnEl.innerHTML = `<div class="scaler-l2l3-title">L2/L3 conflict: ${l2SubIds.length} existing sub-if(s) are L2-service. Creating L3 here may conflict.</div>
                                            <button type="button" class="scaler-step-chip" data-action="auto-skip-l2l3" data-ids="${l2SubIds.join(',')}">Auto-skip conflicting IDs</button>
                                            <button type="button" class="scaler-step-chip scaler-step-chip--outline" data-action="ignore-l2l3">Ignore</button>`;
                                        warnEl.querySelector('[data-action="auto-skip-l2l3"]')?.addEventListener('click', () => {
                                            if (ScalerGUI.WizardController?.data) {
                                                ScalerGUI.WizardController.data._l2l3SkipIds = l2SubIds;
                                            }
                                            warnEl.style.display = 'none';
                                            updatePreview();
                                        });
                                        warnEl.querySelector('[data-action="ignore-l2l3"]')?.addEventListener('click', () => {
                                            if (ScalerGUI.WizardController?.data) ScalerGUI.WizardController.data._l2l3SkipIds = null;
                                            warnEl.style.display = 'none';
                                        });
                                    } else {
                                        warnEl.style.display = 'none';
                                    }
                                } catch (_) {
                                    warnEl.style.display = 'none';
                                }
                            };
        
                            if (isPhysical) {
                                document.querySelectorAll('input[name="iface-mode"]').forEach(r => r.addEventListener('change', (e) => {
                                    const isL2 = e.target.value === 'l2';
                                    const ipSec = document.getElementById('ip-section');
                                    const l2Info = document.getElementById('l2-info');
                                    const l3Feat = document.getElementById('l3-features');
                                    const mtuRow = document.getElementById('mtu-row');
                                    if (ipSec) ipSec.style.display = isL2 ? 'none' : 'block';
                                    if (l2Info) l2Info.style.display = isL2 ? 'block' : 'none';
                                    if (l3Feat) l3Feat.style.display = isL2 ? 'none' : 'flex';
                                    if (mtuRow) mtuRow.style.display = isL2 ? 'none' : 'flex';
                                    if (isL2) {
                                        const mpls = document.getElementById('mpls-enabled');
                                        const fs = document.getElementById('flowspec-enabled');
                                        const bfd = document.getElementById('bfd-enabled');
                                        if (mpls) mpls.checked = false;
                                        if (fs) fs.checked = false;
                                        if (bfd) bfd.checked = false;
                                        const bfdRow = document.getElementById('bfd-options-row');
                                        if (bfdRow) bfdRow.style.display = 'none';
                                    }
                                    updateL2L3ConflictWarning();
                                    updatePreview();
                                }));
                                document.getElementById('mpls-enabled')?.addEventListener('change', updatePreview);
                                document.getElementById('flowspec-enabled')?.addEventListener('change', updatePreview);
                                document.getElementById('bfd-enabled')?.addEventListener('change', (e) => {
                                    const row = document.getElementById('bfd-options-row');
                                    if (row) row.style.display = e.target.checked && isPhysical ? 'flex' : 'none';
                                    updatePreview();
                                });
                                document.getElementById('iface-mtu')?.addEventListener('input', updatePreview);
                                document.getElementById('iface-desc')?.addEventListener('input', updatePreview);
                                document.getElementById('bfd-interval')?.addEventListener('input', updatePreview);
                                document.getElementById('bfd-multiplier')?.addEventListener('input', updatePreview);
                                updateL2L3ConflictWarning();
                            }
        
                            document.querySelectorAll('input[name="ip-version"]').forEach(r => r.addEventListener('change', (e) => {
                                const ipOpts = document.getElementById('ip-options');
                                const v6Row = document.getElementById('ipv6-row');
                                if (ipOpts) ipOpts.style.display = e.target.value !== 'none' ? 'block' : 'none';
                                if (v6Row) v6Row.style.display = e.target.value === 'dual' ? 'flex' : 'none';
                                updatePreview(); validateIpAddress(); updateIPOverlapBanner();
                            }));
                            const dottedStepToInt = (d) => {
                                try {
                                    const p = d.trim().split('.');
                                    if (p.length !== 4) return 1;
                                    return (parseInt(p[0]) << 24) + (parseInt(p[1]) << 16) + (parseInt(p[2]) << 8) + parseInt(p[3]);
                                } catch { return 1; }
                            };
                            const updateIpStepPreview = () => {
                                const el = document.getElementById('ip-step-preview');
                                if (!el) return;
                                const ipStr = document.getElementById('ip-start')?.value || '10.0.0.1';
                                const dotted = document.getElementById('ip-step-dotted')?.value || '0.0.0.1';
                                const step = dottedStepToInt(dotted);
                                if (!ipStr.includes('.')) return;
                                const parts = ipStr.split('/')[0].split('.');
                                if (parts.length !== 4) return;
                                let ipInt = parts.reduce((a, o) => (a << 8) + (parseInt(o) || 0), 0) >>> 0;
                                const ips = [];
                                for (let i = 0; i < 3; i++) {
                                    ips.push([(ipInt >>> 24) & 255, (ipInt >>> 16) & 255, (ipInt >>> 8) & 255, ipInt & 255].join('.'));
                                    ipInt = (ipInt + step) >>> 0;
                                }
                                el.textContent = `Preview: ${ips.join(', ')}...`;
                            };
                            document.getElementById('ip-start')?.addEventListener('input', () => { updatePreview(); validateIpAddress(); updateIpStepPreview(); updateIPOverlapBanner(); });
                            document.getElementById('ip-prefix')?.addEventListener('input', () => { updatePreview(); validateIpAddress(); updateIpStepPreview(); updateIPOverlapBanner(); });
                            document.getElementById('ipv6-start')?.addEventListener('input', () => { updatePreview(); updateIPOverlapBanner(); });
                            document.getElementById('ipv6-prefix')?.addEventListener('input', () => { updatePreview(); updateIPOverlapBanner(); });
                            document.getElementById('ip-step-dotted')?.addEventListener('input', () => { updatePreview(); validateIpAddress(); updateIpStepPreview(); });
                            const _syncStepChipActive = () => {
                                const val = (document.getElementById('ip-step-dotted')?.value || '').trim();
                                const pv = parseInt(document.getElementById('ip-prefix')?.value) || 30;
                                const autoStep = Math.pow(2, 32 - Math.min(pv, 31));
                                const ao4 = autoStep & 255, ao3 = (autoStep >> 8) & 255, ao2 = (autoStep >> 16) & 255, ao1 = (autoStep >> 24) & 255;
                                const autoVal = `${ao1}.${ao2}.${ao3}.${ao4}`;
                                document.querySelectorAll('#ip-step-presets .scaler-step-chip').forEach(c => {
                                    const s = c.dataset.step;
                                    const isActive = s === 'auto' ? val === autoVal : val === s;
                                    c.classList.toggle('scaler-step-chip--active', isActive);
                                });
                            };
                            document.querySelectorAll('#ip-step-presets .scaler-step-chip').forEach(btn => {
                                btn.addEventListener('click', () => {
                                    const step = btn.dataset.step;
                                    const el = document.getElementById('ip-step-dotted');
                                    if (!el) return;
                                    if (step === 'auto') {
                                        const pv = parseInt(document.getElementById('ip-prefix')?.value) || 30;
                                        const s = Math.pow(2, 32 - Math.min(pv, 31));
                                        const o4 = s & 255, o3 = (s >> 8) & 255, o2 = (s >> 16) & 255, o1 = (s >> 24) & 255;
                                        el.value = `${o1}.${o2}.${o3}.${o4}`;
                                    } else {
                                        el.value = step;
                                    }
                                    _syncStepChipActive();
                                    updatePreview(); validateIpAddress(); updateIpStepPreview();
                                });
                            });
                            document.getElementById('ip-step-dotted')?.addEventListener('input', _syncStepChipActive);
                            document.getElementById('ip-prefix')?.addEventListener('input', _syncStepChipActive);
                            _syncStepChipActive();
                            updateIpStepPreview();
                            updatePreview(); validateIpAddress(); updateIPOverlapBanner();
                        },
                        collectData: () => {
                            const t = document.querySelector('input[name="iface-type"]:checked')?.value || 'bundle';
                            const isPhysical = t === 'subif';
                            if (t === 'loopback') {
                                return {
                                    createSubinterfaces: false,
                                    ipEnabled: !!document.getElementById('ip-start')?.value,
                                    ipStart: document.getElementById('ip-start')?.value || '',
                                    ipPrefix: 32,
                                    description: document.getElementById('lo-desc')?.value || '',
                                };
                            }
                            const ifaceMode = document.querySelector('input[name="iface-mode"]:checked')?.value || 'l3';
                            const isL2 = isPhysical && ifaceMode === 'l2';
                            const ipVer = isL2 ? 'none' : (document.querySelector('input[name="ip-version"]:checked')?.value || 'none');
                            return {
                                createSubinterfaces: document.getElementById('create-subif')?.checked ?? false,
                                subifCount: parseInt(document.getElementById('subif-count')?.value) || 1,
                                interfaceMode: isPhysical ? ifaceMode : undefined,
                                l2Service: isL2,
                                ipEnabled: ipVer !== 'none',
                                ipVersion: ipVer !== 'none' ? ipVer : undefined,
                                ipStart: document.getElementById('ip-start')?.value || '',
                                ipPrefix: parseInt(document.getElementById('ip-prefix')?.value) || 30,
                                ipv6Start: document.getElementById('ipv6-start')?.value || '2001:db8::1',
                                ipv6Prefix: parseInt(document.getElementById('ipv6-prefix')?.value) || 128,
                                ipStepDotted: document.getElementById('ip-step-dotted')?.value || '0.0.0.1',
                                ipMode: document.getElementById('ip-mode')?.value || 'per_subif',
                                mplsEnabled: isPhysical ? (document.getElementById('mpls-enabled')?.checked || false) : false,
                                flowspecEnabled: isPhysical ? (document.getElementById('flowspec-enabled')?.checked || false) : false,
                                bfdEnabled: isPhysical ? (document.getElementById('bfd-enabled')?.checked || false) : false,
                                bfdInterval: isPhysical ? (document.getElementById('bfd-interval')?.value || undefined) : undefined,
                                bfdMultiplier: isPhysical ? (document.getElementById('bfd-multiplier')?.value || undefined) : undefined,
                                description: document.getElementById('iface-desc')?.value || '',
                                mtu: isPhysical ? (parseInt(document.getElementById('iface-mtu')?.value) || null) : null,
                            };
                        }
                    },
                    {
                        id: 'encap',
                        title: 'VLAN & Encap',
                        skipIf: (data) => !data.createSubinterfaces && data.interfaceType !== 'subif',
                        render: (data) => {
                            const isQinQ = data.encapsulation === 'qinq';
                            const pat = data.detectedPattern || {};
                            const suggestedVlan = pat.suggested_next_vlan ?? (pat.last_vlan != null ? pat.last_vlan + 1 : 100);
                            const vlanStartVal = data.vlanStart ?? (pat.last_vlan != null ? suggestedVlan : 100);
                            const outerStartVal = data.outerVlanStart ?? (pat.last_vlan != null ? suggestedVlan : 100);
                            return `
                            <div class="scaler-form">
                                <div class="scaler-encap-header" style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:10px">
                                    <button type="button" id="encap-refresh-btn" class="scaler-btn scaler-btn-secondary scaler-refresh-btn" title="Refresh config from device">Refresh</button>
                                    <span id="encap-config-time" class="scaler-config-time" style="font-size:11px;opacity:0.7"></span>
                                </div>
                                ${pat.vlan_mode ? `<div class="scaler-info-box scaler-pattern-detected" style="margin-bottom:10px">
                                    <strong>Detected from device:</strong> ${pat.vlan_mode} mode, last VLAN ${pat.last_vlan ?? '?'}. Suggested start: ${suggestedVlan}
                                    <div style="margin-top:6px;display:flex;gap:8px">
                                        <button type="button" class="scaler-step-chip" data-action="use-pattern">Use detected</button>
                                        <button type="button" class="scaler-step-chip scaler-step-chip--outline" data-action="clear-pattern">Custom</button>
                                    </div>
                                </div>` : ''}
                                <div class="scaler-form-group">
                                    <label>Encapsulation Mode</label>
                                    <div class="scaler-radio-group">
                                        <label class="scaler-radio">
                                            <input type="radio" name="encap" value="dot1q" ${!isQinQ ? 'checked' : ''}>
                                            <span>Single Tag (dot1q) -- <code>vlan-id</code></span>
                                        </label>
                                        <label class="scaler-radio">
                                            <input type="radio" name="encap" value="qinq" ${isQinQ ? 'checked' : ''}>
                                            <span>Double Tag (QinQ) -- <code>vlan-tags outer/inner</code></span>
                                        </label>
                                    </div>
                                </div>
        
                                <div id="single-vlan-section" style="display:${!isQinQ ? 'block' : 'none'}">
                                    <div class="scaler-form-row">
                                        <div class="scaler-form-group">
                                            <label>VLAN Start</label>
                                            <input type="number" id="vlan-start" class="scaler-input" value="${vlanStartVal}" min="1" max="4094">
                                        </div>
                                        <div class="scaler-form-group">
                                            <label>VLAN Step</label>
                                            <input type="number" id="vlan-step" class="scaler-input" value="${data.vlanStep || 1}" min="0" max="4094">
                                        </div>
                                    </div>
                                    <div class="scaler-info-box" style="font-size:11px;padding:6px 10px;margin-top:4px">
                                        Sub-if naming: <code>parent.{vlan}</code> where VLAN = start + (index * step).
                                        Step 0 = all sub-ifs share the same VLAN.
                                        <span class="scaler-inline-hint">VLAN must be 1-4094.</span>
                                    </div>
                                </div>
        
                                <div id="qinq-section" style="display:${isQinQ ? 'block' : 'none'}">
                                    <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
                                        <span style="font-size:12px;font-weight:600;color:rgba(255,255,255,0.7);text-transform:uppercase;letter-spacing:0.5px">Outer Tag (S-tag)</span>
                                        <span style="flex:1;height:1px;background:rgba(255,255,255,0.1)"></span>
                                    </div>
                                    <div class="scaler-form-row">
                                        <div class="scaler-form-group">
                                            <label>Outer VLAN Start</label>
                                            <input type="number" id="outer-vlan-start" class="scaler-input" value="${outerStartVal}" min="1" max="4094">
                                        </div>
                                        <div class="scaler-form-group">
                                            <label>Outer VLAN Step</label>
                                            <select id="outer-vlan-step" class="scaler-input">
                                                <option value="1" ${(data.outerVlanStep || 1) == 1 ? 'selected' : ''}>+1 per sub-if (flat sequential)</option>
                                                <option value="-1" ${data.outerVlanStep == -1 ? 'selected' : ''}>+1 per parent (shared within parent)</option>
                                                <option value="0" ${data.outerVlanStep === 0 || data.outerVlanStep === '0' ? 'selected' : ''}>Fixed (same for all)</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div style="display:flex;gap:8px;align-items:center;margin:12px 0 8px">
                                        <span style="font-size:12px;font-weight:600;color:rgba(255,255,255,0.7);text-transform:uppercase;letter-spacing:0.5px">Inner Tag (C-tag)</span>
                                        <span style="flex:1;height:1px;background:rgba(255,255,255,0.1)"></span>
                                    </div>
                                    <div class="scaler-form-row">
                                        <div class="scaler-form-group">
                                            <label>Inner VLAN Start</label>
                                            <input type="number" id="inner-vlan-start" class="scaler-input" value="${data.innerVlanStart || 1}" min="1" max="4094">
                                        </div>
                                        <div class="scaler-form-group">
                                            <label>Inner VLAN Step</label>
                                            <select id="inner-vlan-step" class="scaler-input">
                                                <option value="1" ${(data.innerVlanStep || 1) == 1 ? 'selected' : ''}>+1 per sub-if within parent</option>
                                                <option value="-2" ${data.innerVlanStep == -2 ? 'selected' : ''}>+1 per parent (reset per parent)</option>
                                                <option value="0" ${data.innerVlanStep === 0 || data.innerVlanStep === '0' ? 'selected' : ''}>Fixed (same for all)</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="scaler-info-box" style="font-size:11px;padding:6px 10px;margin-top:4px">
                                        Generates <code>vlan-tags outer-tag X inner-tag Y outer-tpid 0x8100</code>.
                                        Outer step -1 = one S-tag per parent. Inner step -2 = reset C-tag per parent.
                                    </div>
                                    <div id="qinq-inner-suggestion" class="scaler-info-box scaler-qinq-suggestion" style="display:none;margin-top:8px"></div>
                                </div>
        
                                <div id="encap-overlap-warning" class="scaler-collision-warning scaler-overlap-banner" style="display:none"></div>
        
                                <div class="scaler-preview-box" style="margin-top:12px">
                                    <label>DNOS SYNTAX PREVIEW:</label>
                                    <pre id="encap-preview" class="scaler-syntax-preview">Loading...</pre>
                                </div>
                            </div>`;
                        },
                        afterRender: async (data) => {
                            let debounceTimer;
                            let scanDebounceTimer;
                            let lastScan = null;
                            const ctx = data.deviceContext || {};
                            const sshHost = ctx.mgmt_ip || ctx.ip || '';
                            const parent = (data.subifParents || [])[0];
        
                            const _getEncapParams = () => {
                                const encap = document.querySelector('input[name="encap"]:checked')?.value || 'dot1q';
                                const isQinQ = encap === 'qinq';
                                const vlanStart = parseInt(document.getElementById('vlan-start')?.value) || 100;
                                const vlanStep = parseInt(document.getElementById('vlan-step')?.value) ?? 1;
                                const outerStart = parseInt(document.getElementById('outer-vlan-start')?.value) || 100;
                                const outerStep = parseInt(document.getElementById('outer-vlan-step')?.value) ?? 1;
                                const innerStart = parseInt(document.getElementById('inner-vlan-start')?.value) || 1;
                                const innerStep = parseInt(document.getElementById('inner-vlan-step')?.value) ?? 1;
                                return { encap, isQinQ, vlanStart, vlanStep, outerStart, outerStep, innerStart, innerStep };
                            };
        
                            const runOverlapScan = async () => {
                                if (!parent || !data.deviceId) return null;
                                try {
                                    const scan = await ScalerAPI.scanExisting({
                                        device_id: data.deviceId,
                                        ssh_host: sshHost,
                                        scan_type: 'interfaces',
                                        parent_interface: parent
                                    });
                                    lastScan = scan;
                                    return scan;
                                } catch (_) {
                                    return null;
                                }
                            };
        
                            const updateOverlapBanner = async () => {
                                clearTimeout(scanDebounceTimer);
                                scanDebounceTimer = setTimeout(async () => {
                                    const warnEl = document.getElementById('encap-overlap-warning');
                                    const qinqSugg = document.getElementById('qinq-inner-suggestion');
                                    if (!warnEl) return;
                                    const ep = _getEncapParams();
                                    const subCount = Math.min(data.subifCount || 1, 4094);
                                    const vStart = ep.isQinQ ? ep.outerStart : ep.vlanStart;
                                    const vStep = Math.max(ep.isQinQ ? (ep.outerStep === -1 || ep.outerStep === 0 ? 1 : ep.outerStep) : ep.vlanStep, 1);
                                    const newIds = [];
                                    for (let si = 0; si < subCount; si++) {
                                        newIds.push(Math.min(Math.max(vStart + si * vStep, 1), 4094));
                                    }
                                    const scan = lastScan || await runOverlapScan();
                                    if (!scan) {
                                        warnEl.style.display = 'none';
                                        if (qinqSugg) qinqSugg.style.display = 'none';
                                        return;
                                    }
                                    const configTimeEl = document.getElementById('encap-config-time');
                                    if (configTimeEl && scan.config_fetched_at) {
                                        try {
                                            const d = new Date(scan.config_fetched_at);
                                            configTimeEl.textContent = `Config: ${d.toLocaleString()}`;
                                        } catch (_) {}
                                    }
                                    const existingIds = new Set(scan.existing_sub_ids || []);
                                    data._existingSubIds = scan.existing_sub_ids || [];
                                    const overlaps = newIds.filter(id => existingIds.has(id));
                                    const lastExisting = Math.max(0, ...(scan.existing_sub_ids || []));
                                    const safeStart = lastExisting + 1;
                                    const nonOverlap = newIds.filter(id => !existingIds.has(id)).length;
        
                                    if (ep.isQinQ && scan.outer_inner_map && ep.outerStart) {
                                        const inners = scan.outer_inner_map[String(ep.outerStart)] || scan.outer_inner_map[ep.outerStart];
                                        if (inners && inners.length) {
                                            const maxInner = Math.max(...inners.map(x => parseInt(x, 10)));
                                            const suggInner = maxInner + 1;
                                            if (qinqSugg) {
                                                qinqSugg.innerHTML = `Outer-tag ${ep.outerStart} in use: highest inner = ${maxInner}. <button type="button" class="scaler-step-chip" data-inner-sugg="${suggInner}">Use inner start ${suggInner}</button>`;
                                                qinqSugg.style.display = 'block';
                                                qinqSugg.querySelector('button')?.addEventListener('click', () => {
                                                    const el = document.getElementById('inner-vlan-start');
                                                    if (el) { el.value = suggInner; updatePreview(); updateOverlapBanner(); }
                                                });
                                            }
                                        } else if (qinqSugg) qinqSugg.style.display = 'none';
                                    } else if (qinqSugg) qinqSugg.style.display = 'none';
        
                                    if (overlaps.length > 0) {
                                        warnEl.style.display = 'block';
                                        warnEl.classList.add('scaler-collision-warning');
                                        warnEl.classList.remove('scaler-collision-ok-state');
                                        const choice = data._collisionChoice || 'skip';
                                        const chk = (v) => v === choice ? ' checked' : '';
                                        warnEl.innerHTML = `
                                            <div class="scaler-collision-title">Overlap detected: ${overlaps.length} sub-interface(s) already in use</div>
                                            <div class="scaler-collision-detail-list">${overlaps.slice(0, 10).join(', ')}${overlaps.length > 10 ? '...' : ''}</div>
                                            <div class="scaler-collision-actions">
                                                <label><input type="radio" name="encap-collision-choice" value="skip"${chk('skip')}> Skip existing IDs (create ${nonOverlap} non-conflicting)</label>
                                                <label><input type="radio" name="encap-collision-choice" value="start-after"${chk('start-after')}> Continue after existing (from .${safeStart})</label>
                                                <label><input type="radio" name="encap-collision-choice" value="override"${chk('override')}> Override existing (may overwrite WAN/other configs)</label>
                                            </div>`;
                                        const rbs = warnEl.querySelectorAll('input[name="encap-collision-choice"]');
                                        rbs.forEach(rb => {
                                            rb.checked = rb.value === choice;
                                            rb.addEventListener('change', () => {
                                                const v = rb.value;
                                                if (ScalerGUI.WizardController?.data) ScalerGUI.WizardController.data._collisionChoice = v;
                                                if (v === 'start-after') {
                                                    ScalerGUI.WizardController.data.vlanStart = safeStart;
                                                    ScalerGUI.WizardController.data.outerVlanStart = safeStart;
                                                    const vs = document.getElementById('vlan-start');
                                                    const os = document.getElementById('outer-vlan-start');
                                                    if (vs) vs.value = safeStart;
                                                    if (os) os.value = safeStart;
                                                }
                                                updatePreview();
                                                updateOverlapBanner();
                                            });
                                        });
                                    } else {
                                        warnEl.innerHTML = '<div class="scaler-collision-ok">No overlap with existing config</div>';
                                        warnEl.style.display = 'block';
                                        warnEl.classList.remove('scaler-collision-warning');
                                        warnEl.classList.add('scaler-collision-ok-state');
                                    }
                                }, 400);
                            };
        
                            const updatePreview = async () => {
                                clearTimeout(debounceTimer);
                                debounceTimer = setTimeout(async () => {
                                    const preview = document.getElementById('encap-preview');
                                    if (!preview) return;
                                    try {
                                        const ep = _getEncapParams();
                                        const isSubif = data.interfaceType === 'subif';
                                        const isPhys = data.interfaceType === 'subif';
                                        const subCount = Math.min(data.subifCount || 1, 3);
                                        const parents = isSubif ? (data.subifParents || []) : [];
                                        const result = await ScalerAPI.generateInterfaces({
                                            interface_type: data.interfaceType || 'subif',
                                            start_number: data.startNumber || 1,
                                            count: isSubif ? Math.min(parents.length || 1, 2) : Math.min(data.count || 1, 2),
                                            parent_interfaces: isSubif ? parents.slice(0, 2) : undefined,
                                            slot: data.slot || 0,
                                            bay: data.bay || 0,
                                            port_start: data.portStart || 0,
                                            create_subinterfaces: true,
                                            subif_count_per_interface: subCount,
                                            subif_vlan_start: ep.isQinQ ? ep.outerStart : ep.vlanStart,
                                            subif_vlan_step: ep.isQinQ ? ep.outerStep : ep.vlanStep,
                                            vlan_mode: ep.isQinQ ? 'qinq' : 'single',
                                            outer_vlan_start: ep.outerStart,
                                            outer_vlan_step: ep.outerStep,
                                            inner_vlan_start: ep.innerStart,
                                            inner_vlan_step: ep.innerStep,
                                            l2_service: isPhys ? (data.l2Service || false) : false,
                                            ip_enabled: data.ipEnabled || false,
                                            ip_version: data.ipVersion || 'ipv4',
                                            ip_start: data.ipStart || '10.0.0.1',
                                            ip_prefix: data.ipPrefix || 30,
                                            ipv6_start: data.ipv6Start || '2001:db8::1',
                                            ipv6_prefix: data.ipv6Prefix || 128,
                                            ip_step: data.ipStepDotted || data.ipStep || '0.0.0.1',
                                            ip_mode: data.ipMode || 'per_subif',
                                            mpls_enabled: isPhys ? (data.mplsEnabled || false) : false,
                                            flowspec_enabled: isPhys ? (data.flowspecEnabled || false) : false,
                                            bfd: isPhys ? (data.bfdEnabled || false) : false,
                                            bfd_interval: isPhys && data.bfdEnabled ? (data.bfdInterval || undefined) : undefined,
                                            bfd_multiplier: isPhys && data.bfdEnabled ? (data.bfdMultiplier || undefined) : undefined,
                                            mtu: isPhys ? (data.mtu || null) : null,
                                            description: data.description || '',
                                        });
                                        const lines = result.config.split('\n').slice(0, 20);
                                        const total = (data.count || 1) * subCount;
                                        preview.textContent = lines.join('\n') +
                                            (total > 6 ? `\n... (${data.count} parents x ${subCount} sub-ifs = ${total} total)` : '');
                                    } catch (e) {
                                        preview.textContent = `Error: ${e.message}`;
                                    }
                                    updateOverlapBanner();
                                }, 300);
                            };
        
                            document.querySelectorAll('input[name="encap"]').forEach(radio => {
                                radio.onchange = (e) => {
                                    const q = e.target.value === 'qinq';
                                    const single = document.getElementById('single-vlan-section');
                                    const qinq = document.getElementById('qinq-section');
                                    if (single) single.style.display = q ? 'none' : 'block';
                                    if (qinq) qinq.style.display = q ? 'block' : 'none';
                                    updatePreview();
                                };
                            });
                            document.getElementById('vlan-start')?.addEventListener('input', updatePreview);
                            document.getElementById('vlan-step')?.addEventListener('input', updatePreview);
                            document.getElementById('outer-vlan-start')?.addEventListener('input', updatePreview);
                            document.getElementById('outer-vlan-step')?.addEventListener('change', updatePreview);
                            document.getElementById('inner-vlan-start')?.addEventListener('input', updatePreview);
                            document.getElementById('inner-vlan-step')?.addEventListener('change', updatePreview);
        
                            document.querySelector('[data-action="use-pattern"]')?.addEventListener('click', () => {
                                const pat = data.detectedPattern || {};
                                const v = pat.suggested_next_vlan ?? 100;
                                const vs = document.getElementById('vlan-start');
                                const os = document.getElementById('outer-vlan-start');
                                if (vs) vs.value = v;
                                if (os) os.value = v;
                                updatePreview();
                            });
                            document.querySelector('[data-action="clear-pattern"]')?.addEventListener('click', () => {
                                if (ScalerGUI.WizardController?.data) ScalerGUI.WizardController.data.detectedPattern = null;
                                ScalerGUI.WizardController?.render();
                            });
        
                            const refreshBtn = document.getElementById('encap-refresh-btn');
                            const configTimeEl = document.getElementById('encap-config-time');
                            refreshBtn?.addEventListener('click', async () => {
                                if (!data.deviceId) return;
                                refreshBtn.disabled = true;
                                refreshBtn.textContent = 'Syncing...';
                                try {
                                    await ScalerAPI.syncConfig(data.deviceId, sshHost);
                                    lastScan = null;
                                    await runOverlapScan();
                                    if (parent) {
                                        const pat = await ScalerAPI.detectPattern({ device_id: data.deviceId, ssh_host: sshHost, parent_interface: parent });
                                        if (ScalerGUI.WizardController?.data) ScalerGUI.WizardController.data.detectedPattern = pat;
                                    }
                                    updateOverlapBanner();
                                    ScalerGUI.WizardController?.render();
                                } catch (e) {
                                    if (configTimeEl) configTimeEl.textContent = `Sync failed: ${e.message}`;
                                }
                                refreshBtn.disabled = false;
                                refreshBtn.textContent = 'Refresh';
                            });
        
                            updatePreview();
                        },
                        collectData: () => {
                            const encap = document.querySelector('input[name="encap"]:checked')?.value || 'dot1q';
                            const isQinQ = encap === 'qinq';
                            return {
                                encapsulation: encap,
                                vlanStart: parseInt(document.getElementById('vlan-start')?.value) || 100,
                                vlanStep: parseInt(document.getElementById('vlan-step')?.value) ?? 1,
                                outerVlanStart: isQinQ ? (parseInt(document.getElementById('outer-vlan-start')?.value) || 100) : undefined,
                                outerVlanStep: isQinQ ? (parseInt(document.getElementById('outer-vlan-step')?.value) ?? 1) : undefined,
                                innerVlanStart: isQinQ ? (parseInt(document.getElementById('inner-vlan-start')?.value) || 1) : undefined,
                                innerVlanStep: isQinQ ? (parseInt(document.getElementById('inner-vlan-step')?.value) ?? 1) : undefined,
                            };
                        }
                    },
                    {
                        id: 'review',
                        title: 'Review',
                        render: (data) => {
                            const t = data.interfaceType || 'subif';
                            const isPhys = t === 'subif';
                            const isLoop = t === 'loopback';
                            const isSubif = t === 'subif';
                            const hasSubs = (data.createSubinterfaces || isSubif) && !isLoop;
                            const isQinQ = data.encapsulation === 'qinq';
                            const parentCount = isSubif ? (data.subifParents || []).length : data.count;
                            const totalIfs = hasSubs ? (parentCount * (data.subifCount || 1)) : parentCount;
                            const _stepLabel = (v) => v == -1 ? 'per-parent' : v == -2 ? 'per-parent' : v == 0 ? 'fixed' : `+${v}`;
                            const rows = [
                                `<tr><td>Device</td><td>${data.deviceId}</td></tr>`,
                                `<tr><td>Type</td><td><strong>${isSubif ? 'Sub-interface (on existing parents)' : t}</strong></td></tr>`,
                                isSubif
                                    ? `<tr><td>Parents</td><td>${(data.subifParents || []).join(', ') || 'none'}</td></tr>`
                                    : `<tr><td>Parents</td><td>${data.count} (starting at ${data.startNumber})</td></tr>`,
                            ];
                            if (hasSubs)
                                rows.push(`<tr><td>Sub-interfaces</td><td>${data.subifCount} per parent = <strong>${totalIfs} total</strong></td></tr>`);
                            if (hasSubs && !isQinQ)
                                rows.push(`<tr><td>VLAN</td><td>dot1q, start ${data.vlanStart || 100}, step ${_stepLabel(data.vlanStep ?? 1)}</td></tr>`);
                            if (hasSubs && isQinQ)
                                rows.push(`<tr><td>VLAN</td><td>QinQ: outer ${data.outerVlanStart || 100} (${_stepLabel(data.outerVlanStep ?? 1)}), inner ${data.innerVlanStart || 1} (${_stepLabel(data.innerVlanStep ?? 1)})</td></tr>`);
                            if (data.bundleMembers?.length)
                                rows.push(`<tr><td>Members</td><td>${data.bundleMembers.join(', ')} (LACP: ${data.lacpMode || 'active'})</td></tr>`);
                            if (isPhys && data.interfaceMode)
                                rows.push(`<tr><td>Mode</td><td>${data.interfaceMode === 'l2' ? 'L2 (l2-service)' : 'L3 (Routing)'}</td></tr>`);
                            if (data.ipEnabled) {
                                let ipDesc = `${(data.ipVersion || 'ipv4').toUpperCase()} from ${data.ipStart || '10.0.0.1'}/${data.ipPrefix || 30}`;
                                if (data.ipVersion === 'dual') ipDesc += ` + ${data.ipv6Start || '2001:db8::1'}/${data.ipv6Prefix || 128}`;
                                ipDesc += ` (step ${data.ipStepDotted || data.ipStep || '0.0.0.1'})`;
                                rows.push(`<tr><td>IP</td><td>${ipDesc}</td></tr>`);
                            }
                            if (data.description) rows.push(`<tr><td>Description</td><td>${data.description}</td></tr>`);
                            if (data.mplsEnabled) rows.push(`<tr><td>MPLS</td><td>Enabled</td></tr>`);
                            if (data.flowspecEnabled) rows.push(`<tr><td>Flowspec</td><td>Enabled</td></tr>`);
                            if (data.bfdEnabled) rows.push(`<tr><td>BFD</td><td>Enabled</td></tr>`);
                            if (data.mtu) rows.push(`<tr><td>MTU</td><td>${data.mtu}</td></tr>`);
                            const rerunWarn = data._wasRerun ? `<div class="scaler-rerun-warning">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f39c12" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                                <div><strong>Re-run detected:</strong> These parameters were pushed before. IPs and VLANs may already exist on the device. Check the IP scan results below or change the IP start address before pushing.</div>
                            </div>` : '';
                            return `
                            <div class="scaler-review">
                                ${rerunWarn}
                                <div class="scaler-review-header" style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:10px">
                                    <h4 style="margin:0;flex:1">Configuration Summary</h4>
                                    <button type="button" id="review-refresh-btn" class="scaler-btn scaler-btn-secondary scaler-refresh-btn" title="Refresh config from device">Refresh</button>
                                    <span id="review-config-time" class="scaler-config-time" style="font-size:11px;opacity:0.7"></span>
                                </div>
                                <table class="scaler-table scaler-summary-table">
                                    ${rows.join('\n')}
                                </table>
                                <div class="scaler-preview-box">
                                    <label>Full DNOS Config Preview:</label>
                                    <pre id="config-preview">Generating preview...</pre>
                                </div>
                                <div id="config-validation"></div>
                                <div id="collision-warning" class="scaler-collision-warning" style="display:none"></div>
                                <div class="scaler-diff-section">
                                    <button type="button" id="show-diff-btn" class="scaler-btn scaler-btn-secondary">Show diff vs running</button>
                                    <pre id="config-diff" class="scaler-diff-preview" style="display:none"></pre>
                                </div>
                                <div id="whats-next-container"></div>
                            </div>`;
                        },
                        afterRender: async (data) => {
                            try {
                                const t = data.interfaceType || 'subif';
                                const isSubif = t === 'subif';
                                const isPhys = t === 'subif';
                                const encap = data.encapsulation || 'dot1q';
                                const isQinQ = encap === 'qinq';
                                const parent = isSubif && (data.subifParents || [])[0];
                                const ctx = data.deviceContext || {};
                                const sshHost = ctx.mgmt_ip || ctx.ip || '';
                                let collisionChoice = data._collisionChoice || 'skip';
                                let overlapsForSkip = [];
                                if (parent && data.deviceId) {
                                    try {
                                        const scan = await ScalerAPI.scanExisting({
                                            device_id: data.deviceId,
                                            ssh_host: sshHost,
                                            scan_type: 'interfaces',
                                            parent_interface: parent
                                        });
                                        const existingIds = new Set(scan.existing_sub_ids || []);
                                        data._existingSubIds = scan.existing_sub_ids || [];
                                        const details = scan.sub_id_details || {};
                                        const nextFree = scan.next_free?.sub_id || 1;
        
                                        const vStart = isQinQ ? (data.outerVlanStart || 100) : (data.vlanStart || 100);
                                        const vStep = isQinQ ? (data.outerVlanStep ?? 1) : (data.vlanStep ?? 1);
                                        const subCount = data.subifCount || 1;
                                        const effStep = Math.max(vStep, 0) === 0 ? 1 : vStep;
                                        const newIds = [];
                                        for (let si = 0; si < subCount; si++) {
                                            newIds.push(Math.min(Math.max(vStart + si * effStep, 1), 4094));
                                        }
                                        const overlaps = newIds.filter(id => existingIds.has(id));
                                        const isCreatingL2 = data.l2Service || false;
                                        if (collisionChoice === 'skip') overlapsForSkip = [...overlaps];
        
                                        const warnEl = document.getElementById('collision-warning');
                                        if (warnEl) warnEl.classList.remove('scaler-collision-ok-state');
                                        if (warnEl && overlaps.length > 0) {
                                            const lines = [];
                                            overlaps.slice(0, 8).forEach(id => {
                                                const d = details[String(id)] || {};
                                                let cur = d.has_l2 ? 'L2-service' : d.has_ip ? `L3 (${d.ipv4 || d.ipv6 || 'has IP'})` : 'configured';
                                                let conflict = '';
                                                if (isCreatingL2 && d.has_ip) conflict = '  \u2190 mode conflict: existing L3, you want L2';
                                                else if (!isCreatingL2 && d.has_l2) conflict = '  \u2190 mode conflict: existing L2, you want L3';
                                                else conflict = '  \u2190 will overwrite';
                                                lines.push(`  ${parent}.${id}  currently: ${cur}${conflict}`);
                                            });
                                            if (overlaps.length > 8) lines.push(`  ... and ${overlaps.length - 8} more`);
                                            const nonOverlap = subCount - overlaps.length;
                                            const lastExisting = Math.max(...existingIds, 0);
                                            const safeStart = lastExisting + 1;
                                            warnEl.style.display = 'block';
                                            warnEl.innerHTML = `
                                                <div class="scaler-collision-header">${overlaps.length} of ${subCount} new sub-interfaces overlap with existing on ${parent}</div>
                                                <pre class="scaler-collision-detail-list">${this.escapeHtml(lines.join('\n'))}</pre>
                                                <div class="scaler-collision-detail" style="margin-top:6px;font-size:11px;opacity:0.7">${existingIds.size} sub-ID(s) already exist on this parent (range ${Math.min(...existingIds)}\u2013${lastExisting})</div>
                                                <div class="scaler-collision-actions">
                                                <label><input type="radio" name="collision-choice" value="skip" checked> Skip existing IDs (create ${nonOverlap} non-conflicting)</label>
                                                <label><input type="radio" name="collision-choice" value="start-after"> Start after existing (from .${safeStart})</label>
                                                <label><input type="radio" name="collision-choice" value="override"> Override existing (may overwrite WAN/other configs)</label>
                                                </div>
                                            `;
                                            const rbs = warnEl.querySelectorAll('input[name="collision-choice"]');
                                            rbs.forEach(rb => {
                                                rb.checked = rb.value === collisionChoice;
                                                rb.addEventListener('change', () => {
                                                    collisionChoice = rb.value;
                                                    ScalerGUI.WizardController.data._collisionChoice = collisionChoice;
                                                    if (collisionChoice === 'start-after') {
                                                        ScalerGUI.WizardController.data.vlanStart = safeStart;
                                                        ScalerGUI.WizardController.data.outerVlanStart = safeStart;
                                                    }
                                                    ScalerGUI.WizardController.render();
                                                });
                                            });
                                        } else if (warnEl && existingIds.size > 0 && overlaps.length === 0) {
                                            warnEl.style.display = 'block';
                                            warnEl.classList.add('scaler-collision-ok-state');
                                            warnEl.innerHTML = `<div class="scaler-collision-header" style="color:var(--dn-green,#2ecc71)">No overlap \u2014 ${existingIds.size} existing sub-ID(s) on ${parent} won't conflict with your range (.${newIds[0]}\u2013.${newIds[newIds.length - 1]})</div>`;
                                        }
                                        const reviewTimeEl = document.getElementById('review-config-time');
                                        if (reviewTimeEl && scan.config_fetched_at) {
                                            try {
                                                const d = new Date(scan.config_fetched_at);
                                                reviewTimeEl.textContent = `Config: ${d.toLocaleString()}`;
                                            } catch (_) {}
                                        }
                                    } catch (_) {}
                                }
                                const reviewRefreshBtn = document.getElementById('review-refresh-btn');
                                reviewRefreshBtn?.addEventListener('click', async () => {
                                    if (!data.deviceId) return;
                                    reviewRefreshBtn.disabled = true;
                                    reviewRefreshBtn.textContent = 'Syncing...';
                                    try {
                                        await ScalerAPI.syncConfig(data.deviceId, sshHost);
                                        ScalerGUI.WizardController?.render();
                                    } catch (e) {
                                        const el = document.getElementById('review-config-time');
                                        if (el) el.textContent = `Sync failed: ${e.message}`;
                                    }
                                    reviewRefreshBtn.disabled = false;
                                    reviewRefreshBtn.textContent = 'Refresh';
                                });
                                const params = {
                                    interface_type: t,
                                    start_number: data.startNumber,
                                    count: isSubif ? (data.subifParents || []).length : data.count,
                                    parent_interfaces: isSubif ? (data.subifParents || []) : undefined,
                                    slot: data.slot || 0,
                                    bay: data.bay || 0,
                                    port_start: data.portStart || 0,
                                    create_subinterfaces: data.createSubinterfaces || isSubif || false,
                                    subif_count_per_interface: data.subifCount ?? 1,
                                    subif_vlan_start: isQinQ ? (data.outerVlanStart || 100) : (data.vlanStart || 100),
                                    subif_vlan_step: isQinQ ? (data.outerVlanStep ?? 1) : (data.vlanStep ?? 1),
                                    vlan_mode: isQinQ ? 'qinq' : 'single',
                                    outer_vlan_start: data.outerVlanStart || data.vlanStart || 100,
                                    inner_vlan_start: data.innerVlanStart || 1,
                                    outer_vlan_step: data.outerVlanStep ?? 1,
                                    inner_vlan_step: data.innerVlanStep ?? 1,
                                    l2_service: isPhys ? (data.l2Service || false) : false,
                                    bundle_members: data.bundleMembers || [],
                                    lacp_mode: data.lacpMode || 'active',
                                    ip_enabled: data.ipEnabled || false,
                                    ip_version: data.ipVersion || 'ipv4',
                                    ip_start: data.ipStart || '10.0.0.1',
                                    ip_prefix: data.ipPrefix || 30,
                                    ipv6_start: data.ipv6Start || '2001:db8::1',
                                    ipv6_prefix: data.ipv6Prefix || 128,
                                    ip_step: data.ipStepDotted || data.ipStep || '0.0.0.1',
                                    ip_mode: data.ipMode || 'per_subif',
                                    mpls_enabled: isPhys ? (data.mplsEnabled || false) : false,
                                    flowspec_enabled: isPhys ? (data.flowspecEnabled || false) : false,
                                    bfd: isPhys ? (data.bfdEnabled || false) : false,
                                    bfd_interval: isPhys && data.bfdEnabled ? (data.bfdInterval || undefined) : undefined,
                                    bfd_multiplier: isPhys && data.bfdEnabled ? (data.bfdMultiplier || undefined) : undefined,
                                    mtu: isPhys ? (data.mtu || null) : null,
                                    description: data.description || '',
                                };
                                const skipVlans = [...(collisionChoice === 'skip' ? overlapsForSkip : []), ...(data._l2l3SkipIds || [])];
                                if (skipVlans.length) params.skip_vlans = skipVlans;
                                if (collisionChoice !== 'override' && data._existingSubIds?.length) {
                                    params.skip_subif_ids = data._existingSubIds;
                                }
                                if (typeof console !== 'undefined' && console.debug) {
                                    console.debug('[Interface Wizard] generateInterfaces params:', JSON.stringify(params));
                                }
                                const result = await ScalerAPI.generateInterfaces(params);
        
                                const preview = document.getElementById('config-preview');
                                if (preview) {
                                    const lines = result.config.split('\n');
                                    preview.textContent = lines.slice(0, 40).join('\n') +
                                        (lines.length > 40 ? `\n... (${lines.length} lines total)` : '');
                                }
        
                                ScalerGUI.WizardController.data.generatedConfig = result.config;
                                try {
                                    const val = await ScalerAPI.validateConfig({ config: result.config, hierarchy: 'interfaces' });
                                    const vEl = document.getElementById('config-validation');
                                    if (vEl) vEl.innerHTML = ScalerGUI._renderValidationResults(val.errors, val.warnings, val.suggestions);
                                } catch (e) { console.warn('[ScalerGUI] validation display error:', e.message); }
                                const diffBtn = document.getElementById('show-diff-btn');
                                const diffPre = document.getElementById('config-diff');
                                if (diffBtn && diffPre) {
                                    diffBtn.onclick = async () => {
                                        if (diffPre.style.display === 'none') {
                                            diffBtn.disabled = true;
                                            diffBtn.textContent = 'Loading...';
                                            try {
                                                const ctx = data.deviceContext || {};
                                                const r = await ScalerAPI.previewConfigDiff(data.deviceId, result.config, ctx.mgmt_ip || ctx.ip || '');
                                                diffPre.textContent = r.diff_text || '(no diff)';
                                                diffPre.style.display = 'block';
                                                diffBtn.textContent = 'Hide diff';
                                            } catch (e) {
                                                diffPre.textContent = `Error: ${e.message}`;
                                                diffPre.style.display = 'block';
                                                diffBtn.textContent = 'Show diff vs running';
                                            }
                                            diffBtn.disabled = false;
                                        } else {
                                            diffPre.style.display = 'none';
                                            diffBtn.textContent = 'Show diff vs running';
                                        }
                                    };
                                }
                                const container = document.getElementById('whats-next-container');
                                if (container) {
                                    const t = data.interfaceType || 'subif';
                                    const isSubif = t === 'subif';
                                    const isLoopback = t === 'loopback';
                                    let createdData = { deviceId: data.deviceId };
                                    if (isLoopback) {
                                        createdData.loopback = data.ipStart || data.ip_start || '10.0.0.1';
                                        createdData.interfaces = ['lo0'];
                                    } else if (isSubif) {
                                        const parents = data.subifParents || [];
                                        const subCount = data.subifCount || 1;
                                        const ifaces = [];
                                        parents.forEach(p => { for (let i = 1; i <= subCount; i++) ifaces.push(`${p}.${i}`); });
                                        createdData.interfaces = ifaces;
                                    } else {
                                        const start = data.startNumber || 1;
                                        const count = data.count || 1;
                                        const subCount = data.createSubinterfaces ? (data.subifCount || 1) : 0;
                                        const slot = data.slot || 0, bay = data.bay || 0, portStart = data.portStart || 0;
                                        const prefix = t === 'bundle' ? 'bundle' : t === 'ph' ? 'ph' : t === 'irb' ? 'irb' : t;
                                        const ifaces = [];
                                        for (let n = 0; n < count; n++) {
                                            const base = false
                                                ? `${t}-${slot}/${bay}/${portStart + n}` : `${prefix}-${start + n}`;
                                            ifaces.push(base);
                                            for (let s = 1; s <= subCount; s++) ifaces.push(`${base}.${s}`);
                                        }
                                        createdData.interfaces = ifaces;
                                    }
                                    const section = await ScalerGUI._renderWhatsNextSection('interfaces', data, createdData, result.config);
                                    if (section) { container.innerHTML = ''; container.appendChild(section); }
                                }
                            } catch (e) {
                                const previewEl = document.getElementById('config-preview');
                                if (previewEl) previewEl.textContent = `Error: ${e.message}`;
                            }
                        }
                    },
                    ScalerGUI._buildDecisionStep({
                        wizardType: 'interfaces',
                        getCreatedData: (data) => {
                            const t = data.interfaceType || 'subif';
                            const isSubif = t === 'subif';
                            const isLoopback = t === 'loopback';
                            const createdData = { deviceId: data.deviceId };
                            if (isLoopback) {
                                createdData.loopback = data.ipStart || data.ip_start || '10.0.0.1';
                                createdData.interfaces = ['lo0'];
                            } else if (isSubif) {
                                const parents = data.subifParents || [];
                                const subCount = data.subifCount || 1;
                                const ifaces = [];
                                parents.forEach(p => { for (let i = 1; i <= subCount; i++) ifaces.push(`${p}.${i}`); });
                                createdData.interfaces = ifaces;
                            } else {
                                const start = data.startNumber || 1;
                                const count = data.count || 1;
                                const subCount = data.createSubinterfaces ? (data.subifCount || 1) : 0;
                                const prefix = t === 'bundle' ? 'bundle' : t === 'ph' ? 'ph' : t === 'irb' ? 'irb' : t;
                                const ifaces = [];
                                for (let n = 0; n < count; n++) {
                                    const base = `${prefix}-${start + n}`;
                                    ifaces.push(base);
                                    for (let s = 1; s <= subCount; s++) ifaces.push(`${base}.${s}`);
                                }
                                createdData.interfaces = ifaces;
                            }
                            return createdData;
                        }
                    }),
                    ScalerGUI._buildPushStep({
                        id: 'push',
                        includeClipboard: true,
                        infoText: (d) => `<strong>Config:</strong> ${(d.generatedConfig || '').split('\\n').length} lines, ${d.count} ${d.interfaceType} interface${d.count > 1 ? 's' : ''}`
                    })
                ];
        
                const _ifaceTypeFlows = {
                    subif:    ['type', 'parent', 'subifs', 'encap', 'review', 'decision', 'push'],
                };
        
                const _ifaceStepKeyMap = {
                    type:     ['interfaceType', 'startNumber', 'count'],
                    members:  ['bundleMembers', 'lacpMode'],
                    parent:   ['subifParents'],
                    subifs:   ['createSubinterfaces', 'subifCount', 'interfaceMode', 'l2Service', 'ipEnabled', 'ipVersion', 'ipStart', 'ipPrefix', 'ipv6Start', 'ipv6Prefix', 'ipStepDotted', 'ipMode', 'mplsEnabled', 'flowspecEnabled', 'bfdEnabled', 'bfdInterval', 'bfdMultiplier', 'mtu', 'description'],
                    encap:    ['encapsulation', 'vlanStart', 'vlanStep', 'outerVlanStart', 'outerVlanStep', 'innerVlanStart', 'innerVlanStep'],
                    review:   ['generatedConfig'],
                    decision: [],
                    push:     ['dryRun', 'pushMode', 'push_method', 'load_mode'],
                };
        
                const _stepById = {};
                _ifaceAllSteps.forEach(s => { _stepById[s.id] = s; });
        
                function _buildIfaceSteps(data) {
                    const t = (data.interfaceType || 'subif').toLowerCase();
                    const flow = _ifaceTypeFlows[t] || _ifaceTypeFlows.subif;
                    const steps = flow.map(id => _stepById[id]);
                    const deps = {};
                    const keys = {};
                    deps[0] = flow.slice(1).map((_, i) => i + 1);
                    for (let i = 0; i < flow.length; i++) {
                        keys[i] = _ifaceStepKeyMap[flow[i]] || [];
                        if (i > 0 && i < flow.length - 2) {
                            deps[i] = [flow.length - 2, flow.length - 1];
                        }
                    }
                    return { steps, deps, keys };
                }
        
            this.WizardController.init({
                panelName: 'interface-wizard',
                quickNavKey: 'interface-wizard',
                lastRunWizardType: 'interfaces',
                title: `Interface Wizard - ${deviceId}`,
                initialData: { deviceId, deviceContext: ctx, ...(prefillParams || {}) },
                stepBuilder: _buildIfaceSteps,
                wizardHeader: (data) => {
                    return self.renderContextPanel(deviceId, data.deviceContext || {}, {
                        wizardType: 'interfaces',
                        onRefresh: async () => {
                            const c = await self.refreshDeviceContextLive(deviceId);
                            self.WizardController.data.deviceContext = c;
                            self.WizardController.render();
                        }
                    });
                },
                onLastRunRerun: (rec) => self._handleLastRunAction(rec, deviceId, ctx),
                onLastRunRerunOther: (rec) => {
                    self.closePanel('interface-wizard');
                    self.openMirrorWizard(rec.deviceId);
                },
                onComplete: async (data) => {
                    if (data.pushMode === 'clipboard') {
                        const config = data.generatedConfig || '';
                        try {
                            await window.safeClipboardWrite(config);
                        } catch (_) {}
                        const ctx = data.deviceContext || {};
                        const host = ctx.mgmt_ip || ctx.ip || '';
                        const user = 'dnroot';
                        if (host) {
                            window.open(`ssh://${user}@${host}`, '_blank');
                        }
                        this.showNotification(
                            `Config copied to clipboard (${config.split('\n').length} lines).${host ? ' Opening SSH to ' + host + '...' : ' Set device IP for SSH.'}`,
                            'success', 6000
                        );
                        this.closePanel('interface-wizard');
                        return;
                    }
                    try {
                        const ctx = data.deviceContext || {};
                        const subCount = data.createSubinterfaces ? (data.subifCount ?? 1) : 0;
                        const total = subCount ? (data.count ?? 1) * subCount : (data.count ?? 1);
                        const configLines = (data.generatedConfig || '').split('\n').length;
                        if (typeof console !== 'undefined' && console.debug) {
                            console.debug('[Interface Wizard] pushConfig:', { count: data.count, subifCount: data.subifCount, total, configLines, deviceId: data.deviceId });
                        }
                        const jobName = subCount
                            ? `${data.count} ${data.interfaceType} + ${total} sub-ifs on ${data.deviceId}`
                            : `${data.count} ${data.interfaceType} on ${data.deviceId}`;
                        const result = await ScalerAPI.pushConfig({
                            device_id: data.deviceId,
                            config: data.generatedConfig,
                            hierarchy: 'interfaces',
                            mode: data.pushMode === 'dry_run' ? 'merge' : (data.push_mode || 'merge'),
                            dry_run: data.dryRun,
                            push_method: data.push_method || 'terminal_paste',
                            load_mode: data.load_mode || 'merge',
                            ssh_host: ctx.mgmt_ip || ctx.ip || '',
                            job_name: jobName
                        });
                        this.closePanel('interface-wizard');
                        this.recordWizardChange(data.deviceId, 'interfaces', {
                            interfaceType: data.interfaceType,
                            count: data.count,
                            startNumber: data.startNumber,
                            subifCount: data.subifCount,
                            subifParents: data.subifParents,
                            createSubinterfaces: data.createSubinterfaces,
                            bundleMembers: data.bundleMembers || [],
                            dryRun: data.dryRun,
                        }, {
                            params: { ...data },
                            generatedConfig: data.generatedConfig,
                            pushMode: data.pushMode || (data.dryRun ? 'dry_run' : 'commit'),
                            jobId: result.job_id,
                        });
                        const modeLabel = data.dryRun ? 'Commit Check' : 'Commit';
                        this.showProgress(result.job_id, `${modeLabel}: ${data.count} ${data.interfaceType} to ${data.deviceId}`, {
                            device_id: data.deviceId,
                            onReopenWizard: (analysis) => {
                                const reopenData = { ...data };
                                reopenData._rerunMode = false;
                                this.openInterfaceWizard(data.deviceId, reopenData);
                            },
                            onComplete: (success, res) => {
                                this.updateWizardRunResult(result.job_id, success);
                                if (!success && !res?.cancelled) {
                                    this.showNotification(
                                        `Push failed on ${data.deviceId}: ${res?.message || 'Check terminal output above for DNOS errors'}`,
                                        'error', 10000
                                    );
                                } else if (success) {
                                    this.showNotification(`Committed successfully on ${data.deviceId}`, 'success', 6000);
                                }
                            }
                        });
                    } catch (e) {
                        this.showNotification(`Push failed: ${e.message}`, 'error');
                    }
                }
            });
        
            if (!hasFresh) {
                this.getDeviceContext(deviceId).then(c => {
                    if (self.WizardController.data?.deviceId === deviceId) {
                        self.WizardController.data.deviceContext = c;
                        self.WizardController.render();
                    }
                }).catch(e => console.warn('[ScalerGUI] wizard operation failed:', e.message));
            }
        },
        
        // =========================================================================
        // SERVICE WIZARD (5 Steps)
        // =========================================================================
        
        async openServiceWizard(deviceId = null, prefillParams = null) {
            if (!deviceId) {
                this.openDeviceSelector('Service Wizard', (id) => this.openServiceWizard(id, prefillParams));
                return;
            }
            if (!this._isDeviceConfigurable(deviceId)) return;
        
            const content = document.createElement('div');
            content.innerHTML = '<div class="scaler-loading">Loading...</div>';
        
            this.openPanel('service-wizard', `Service Wizard - ${deviceId}`, content, {
                width: '540px',
                parentPanel: 'scaler-menu'
            });
        
            const self = this;
            const cachedCtx = this._deviceContexts[deviceId];
            const hasFresh = cachedCtx && (Date.now() - (cachedCtx._fetchedAt || 0)) < this._contextCacheTTL;
            let ctx = hasFresh ? this._applyPendingChanges(deviceId, cachedCtx) : null;
            const summary = ctx?.config_summary || {};
            const services = ctx?.services || {};
            this.WizardController.init({
                panelName: 'service-wizard',
                quickNavKey: 'service-wizard',
                title: `Service Wizard - ${deviceId}`,
                initialData: { deviceId, deviceContext: ctx, eviStart: services.next_evi || 1000, bgpAsn: summary.as_number ? parseInt(summary.as_number, 10) : 65000, routerId: summary.loopback0_ip || summary.router_id || '1.1.1.1', ...(prefillParams || {}) },
                lastRunWizardType: 'services',
                onLastRunRerun: (rec) => self._handleLastRunAction(rec, deviceId, ctx),
                onLastRunRerunOther: (rec) => {
                    self.closePanel('service-wizard');
                    self.openMirrorWizard(rec.deviceId);
                },
                wizardHeader: (data) => self.renderContextPanel(deviceId, data.deviceContext || {}, { wizardType: 'services', onRefresh: () => self.refreshDeviceContextLive(deviceId).then(c => { self.WizardController.data.deviceContext = c; self.WizardController.render(); }) }),
                steps: [
                    {
                        title: 'Type',
                        render: (data) => `
                            <div class="scaler-form">
                <div class="scaler-form-group">
                    <label>Service Type</label>
                    <select id="svc-type" class="scaler-select">
                                        <option value="evpn-vpws-fxc">EVPN VPWS FXC (Flexible Cross-Connect)</option>
                                        <option value="evpn">EVPN VPLS</option>
                                        <option value="bridge-domain">Bridge Domain</option>
                                        <option value="vrf">L3VPN VRF</option>
                    </select>
                </div>
                                <div id="svc-type-info" class="scaler-info-box">
                                    EVPN VPWS FXC: Point-to-point Layer 2 service using EVPN for signaling.
                                </div>
                            </div>
                        `,
                        afterRender: () => {
                            const infoMap = {
                                'evpn-vpws-fxc': 'EVPN VPWS FXC: Point-to-point Layer 2 service using EVPN for signaling.',
                                'evpn': 'EVPN VPLS: Multipoint Layer 2 service using bridge domains.',
                                'bridge-domain': 'Bridge Domain: L2 switching domain for local bridging.',
                                'vrf': 'L3VPN VRF: Layer 3 VPN using VRF instances with route-targets.'
                            };
                            document.getElementById('svc-type').onchange = (e) => {
                                document.getElementById('svc-type-info').textContent = infoMap[e.target.value];
                            };
                        },
                        collectData: () => ({
                            serviceType: document.getElementById('svc-type')?.value || 'evpn-vpws-fxc'
                        })
                    },
                    {
                        title: 'Naming',
                        render: (data) => `
                            <div class="scaler-form">
                <div class="scaler-form-group">
                                    <label>Name Prefix</label>
                                    <input type="text" id="svc-prefix" class="scaler-input" value="${data.namePrefix || 'FXC_'}" placeholder="e.g., FXC_, CUST-A_">
                </div>
                <div class="scaler-form-row">
                    <div class="scaler-form-group">
                                        <label>Start Number</label>
                                        <input type="number" id="svc-start" class="scaler-input" value="${data.startNumber || 1}" min="1">
                    </div>
                    <div class="scaler-form-group">
                        <label>Count</label>
                                        <input type="number" id="svc-count" class="scaler-input" value="${data.count || 100}" min="1" max="8000">
                    </div>
                </div>
                                <div class="scaler-preview-box">
                                    <label>DNOS SYNTAX PREVIEW:</label>
                                    <pre id="svc-naming-preview" class="scaler-syntax-preview">Loading...</pre>
                                </div>
                            </div>
                        `,
                        afterRender: (data) => {
                            let debounceTimer;
                            const updatePreview = async () => {
                                clearTimeout(debounceTimer);
                                debounceTimer = setTimeout(async () => {
                                    const prefix = document.getElementById('svc-prefix')?.value || 'FXC_';
                                    const start = parseInt(document.getElementById('svc-start')?.value) || 1;
                                    const count = Math.min(parseInt(document.getElementById('svc-count')?.value) || 100, 3); // Preview max 3
                                    const preview = document.getElementById('svc-naming-preview');
                                    if (preview) {
                                        try {
                                            const result = await ScalerAPI.generateServices({
                                                service_type: data.serviceType || 'evpn-vpws-fxc',
                                                name_prefix: prefix,
                                                start_number: start,
                                                count: count,
                                                service_id_start: 1000,
                                                evi_start: 1000,
                                                rd_base: '65000'
                                            });
                                            const actualCount = parseInt(document.getElementById('svc-count')?.value) || 100;
                                            const lines = result.config.split('\n').slice(0, 15);
                                            preview.textContent = lines.join('\n') + (actualCount > 3 ? `\n... (${actualCount} services total)` : '');
                                        } catch (e) {
                                            preview.textContent = `Error: ${e.message}`;
                                        }
                                    }
                                }, 300);
                            };
                            document.getElementById('svc-prefix').addEventListener('input', updatePreview);
                            document.getElementById('svc-start').addEventListener('input', updatePreview);
                            document.getElementById('svc-count').addEventListener('input', updatePreview);
                            updatePreview();
                        },
                        collectData: () => ({
                            namePrefix: document.getElementById('svc-prefix')?.value || 'FXC_',
                            startNumber: parseInt(document.getElementById('svc-start')?.value) || 1,
                            count: parseInt(document.getElementById('svc-count')?.value) || 100
                        })
                    },
                    {
                        title: 'RT/EVI',
                        skipIf: (data) => data.serviceType === 'bridge-domain',
                        render: (data) => {
                            const nextEvi = data.eviStart ?? data.deviceContext?.services?.next_evi ?? 1000;
                            const asn = data.bgpAsn ?? (data.deviceContext?.config_summary?.as_number ? parseInt(data.deviceContext.config_summary.as_number, 10) : 65000);
                            const rid = data.routerId ?? data.deviceContext?.config_summary?.loopback0_ip ?? data.deviceContext?.config_summary?.router_id ?? '1.1.1.1';
                            return `
                            <div class="scaler-form">
                <div class="scaler-form-row">
                    <div class="scaler-form-group">
                                        <label>BGP ASN</label>
                                        <input type="number" id="bgp-asn" class="scaler-input" value="${isNaN(asn) ? 65000 : asn}" min="1" max="4294967295">
                    </div>
                    <div class="scaler-form-group">
                                        <label>RT Start (EVI)</label>
                                        <input type="number" id="evi-start" class="scaler-input" value="${nextEvi}" min="1">
                    </div>
                </div>
                <div id="rt-evi-suggestions"></div>
                <div class="scaler-form-group">
                                    <label>Router ID (Lo0 address for RD)</label>
                                    <input type="text" id="router-id" class="scaler-input" value="${rid}" placeholder="e.g., 1.1.1.1">
                                    <small class="scaler-form-hint">Used for route-distinguisher: &lt;router-id&gt;:&lt;rt-value&gt;</small>
                </div>
                <div class="scaler-form-row">
                    <div class="scaler-form-group"><label>Description (optional)</label><input type="text" id="svc-description" class="scaler-input" value="${data.serviceDescription || ''}" placeholder="e.g., Customer A {n}"></div>
                    <div class="scaler-form-group"><label>Route Policy Import</label><input type="text" id="svc-route-policy-in" class="scaler-input" value="${data.routePolicyImport || ''}" placeholder="Optional"></div>
                </div>
                <div class="scaler-form-group"><label>Route Policy Export</label><input type="text" id="svc-route-policy-out" class="scaler-input" value="${data.routePolicyExport || ''}" placeholder="Optional"></div>
                <div class="scaler-preview-box">
                                    <label>DNOS SYNTAX PREVIEW:</label>
                                    <pre id="rt-evi-preview" class="scaler-syntax-preview">Loading...</pre>
                </div>
                </div>
                        `;
                        },
                        afterRender: (data) => {
                            const sugg = document.getElementById('rt-evi-suggestions');
                            if (sugg) {
                                const chips = [];
                                const nextEvi = data.deviceContext?.services?.next_evi;
                                if (nextEvi) chips.push({ value: nextEvi, label: `Next EVI: ${nextEvi}`, target: 'evi' });
                                const asn = data.deviceContext?.config_summary?.as_number;
                                if (asn) chips.push({ value: asn, label: `AS ${asn}`, target: 'asn' });
                                const rts = data.deviceContext?.config_summary?.route_targets || [];
                                rts.slice(0, 3).forEach(rt => chips.push({ value: rt.split(':')[1] || rt, label: rt, target: 'evi' }));
                                if (chips.length) sugg.appendChild(ScalerGUI.renderSuggestionChips(chips, { type: 'smart', onSelect: (v, target) => {
                                    if (target === 'asn') document.getElementById('bgp-asn').value = v;
                                    else document.getElementById('evi-start').value = v;
                                    document.getElementById('evi-start').dispatchEvent(new Event('input'));
                                } }));
                            }
                            let debounceTimer;
                            const updatePreview = async () => {
                                clearTimeout(debounceTimer);
                                debounceTimer = setTimeout(async () => {
                                    const bgpAsn = parseInt(document.getElementById('bgp-asn').value) || 65000;
                                    const eviStart = parseInt(document.getElementById('evi-start').value) || 1000;
                                    const routerId = document.getElementById('router-id').value || '1.1.1.1';
                                    const count = Math.min(data.count || 100, 2);
                                    const preview = document.getElementById('rt-evi-preview');
                                    if (preview) {
                                        try {
                                            const result = await ScalerAPI.generateServices({
                                                service_type: data.serviceType || 'evpn-vpws-fxc',
                                                name_prefix: data.namePrefix || 'FXC_',
                                                start_number: data.startNumber || 1,
                                                count: count,
                                                service_id_start: eviStart,
                                                evi_start: eviStart,
                                                rd_base: String(bgpAsn),
                                                router_id: routerId
                                            });
                                            const actualCount = data.count || 100;
                                            const lines = result.config.split('\n').slice(0, 22);
                                            preview.textContent = lines.join('\n') + (actualCount > 2 ? `\n... (${actualCount} services, RTs ${bgpAsn}:${eviStart}-${eviStart + actualCount - 1})` : '');
                } catch (e) {
                                            preview.textContent = `Error: ${e.message}`;
                                        }
                                    }
                                }, 300);
                            };
                            document.getElementById('bgp-asn').addEventListener('input', updatePreview);
                            document.getElementById('evi-start').addEventListener('input', updatePreview);
                            document.getElementById('router-id').addEventListener('input', updatePreview);
                            updatePreview();
                        },
                        collectData: () => ({
                            bgpAsn: parseInt(document.getElementById('bgp-asn')?.value) || 65000,
                            eviStart: parseInt(document.getElementById('evi-start')?.value) || 1000,
                            routerId: document.getElementById('router-id')?.value || '1.1.1.1',
                            rdBase: String(parseInt(document.getElementById('bgp-asn')?.value) || 65000),
                            serviceDescription: document.getElementById('svc-description')?.value || undefined,
                            routePolicyImport: document.getElementById('svc-route-policy-in')?.value || undefined,
                            routePolicyExport: document.getElementById('svc-route-policy-out')?.value || undefined
                        })
                    },
                    {
                        title: 'Interface Attachment',
                        skipIf: (data) => data.serviceType === 'vrf',
                        render: (data) => {
                            const subifs = (data.deviceContext?.interfaces?.subinterface || []).map(s => s.name || s).filter(Boolean);
                            const hint = data.serviceType === 'bridge-domain' ? 'Bridge domain interfaces (sub-interfaces)' : 'FXC/EVPN requires sub-interfaces (e.g. bundle-1.100, ph1.1)';
                            return `
                            <div class="scaler-form">
                                <div class="scaler-form-group">
                                    <label>Interfaces (comma-separated, sub-interfaces only)</label>
                                    <input type="text" id="svc-attach-ifaces" class="scaler-input" value="${(data.attachInterfaces || []).join(', ')}" placeholder="bundle-1.100, bundle-1.101, ph1.1">
                                    <div class="scaler-form-hint">${hint}</div>
                                </div>
                                <div id="svc-attach-suggestions"></div>
                                <div class="scaler-form-group">
                                    <label>Interfaces per service</label>
                                    <input type="number" id="svc-ifaces-per" class="scaler-input" value="${data.interfacesPerService ?? 1}" min="1" max="10">
                                </div>
                                <div class="scaler-preview-box"><label>PREVIEW:</label><pre id="svc-attach-preview" class="scaler-syntax-preview">Loading...</pre></div>
                            </div>`;
                        },
                        afterRender: (data) => {
                            const subifs = (data.deviceContext?.interfaces?.subinterface || []).map(s => s.name || s).slice(0, 15);
                            const sugg = document.getElementById('svc-attach-suggestions');
                            if (sugg && subifs.length) {
                                sugg.appendChild(ScalerGUI.renderSuggestionChips(subifs.map(s => ({ value: s, label: s })), { type: 'config', label: 'Sub-interfaces:', onSelect: (v) => {
                                    const input = document.getElementById('svc-attach-ifaces');
                                    const cur = (input.value || '').split(',').map(s => s.trim()).filter(Boolean);
                                    if (!cur.includes(v)) cur.push(v);
                                    input.value = cur.join(', ');
                                    input.dispatchEvent(new Event('input'));
                                } }));
                            }
                            let t;
                            const up = async () => {
                                clearTimeout(t);
                                t = setTimeout(async () => {
                                    const ifaces = (document.getElementById('svc-attach-ifaces')?.value || '').split(',').map(s => s.trim()).filter(Boolean);
                                    const perSvc = parseInt(document.getElementById('svc-ifaces-per')?.value) || 1;
                                    const count = Math.min(data.count || 100, 2);
                                    try {
                                        const params = {
                                            service_type: data.serviceType || 'evpn-vpws-fxc',
                                            name_prefix: data.namePrefix || 'FXC_',
                                            start_number: data.startNumber || 1,
                                            count: count,
                                            service_id_start: data.eviStart ?? 1000,
                                            evi_start: data.eviStart ?? 1000,
                                            rd_base: String(data.bgpAsn || 65000),
                                            router_id: data.routerId || '1.1.1.1',
                                            description: data.serviceDescription,
                                            route_policy_import: data.routePolicyImport,
                                            route_policy_export: data.routePolicyExport,
                                            interface_list: ifaces,
                                            interfaces_per_service: perSvc
                                        };
                                        const r = await ScalerAPI.generateServices(params);
                                        const p = document.getElementById('svc-attach-preview');
                                        if (p) p.textContent = r.config || '(empty)';
                                    } catch (e) { const p = document.getElementById('svc-attach-preview'); if (p) p.textContent = e.message; }
                                }, 300);
                            };
                            document.getElementById('svc-attach-ifaces')?.addEventListener('input', up);
                            document.getElementById('svc-ifaces-per')?.addEventListener('input', up);
                            up();
                        },
                        collectData: () => {
                            const ifaces = (document.getElementById('svc-attach-ifaces')?.value || '').split(',').map(s => s.trim()).filter(Boolean);
                            return {
                                attachInterfaces: ifaces,
                                interfacesPerService: parseInt(document.getElementById('svc-ifaces-per')?.value) || 1
                            };
                        }
                    },
                    {
                        title: 'Review',
                        render: (data) => `
                            <div class="scaler-review">
                                <h4>Service Configuration Summary</h4>
                                <table class="scaler-table scaler-summary-table">
                                    <tr><td>Device</td><td>${data.deviceId}</td></tr>
                                    <tr><td>Service Type</td><td>${data.serviceType}</td></tr>
                                    <tr><td>Count</td><td>${data.count} services</td></tr>
                                    <tr><td>Names</td><td>${data.namePrefix}${data.startNumber} - ${data.namePrefix}${data.startNumber + data.count - 1}</td></tr>
                                    <tr><td>BGP ASN</td><td>${data.bgpAsn || 65000}</td></tr>
                                    <tr><td>Route Targets</td><td>${data.bgpAsn || 65000}:${data.eviStart} - ${data.bgpAsn || 65000}:${data.eviStart + data.count - 1}</td></tr>
                                    <tr><td>Router ID (RD)</td><td>${data.routerId || '1.1.1.1'}</td></tr>
                                </table>
                                <div class="scaler-preview-box">
                                    <label>DNOS SYNTAX PREVIEW:</label>
                                    <pre id="config-preview">Generating preview...</pre>
                                </div>
                                <div id="config-validation"></div>
                                <div id="whats-next-container"></div>
                            </div>
                        `,
                        afterRender: async (data) => {
                            try {
                                const params = {
                                    service_type: data.serviceType,
                                    name_prefix: data.namePrefix,
                                    start_number: data.startNumber,
                                    count: data.count,
                                    service_id_start: data.eviStart ?? 1000,
                                    evi_start: data.eviStart ?? 1000,
                                    rd_base: data.rdBase || '65000',
                                    router_id: data.routerId,
                                    description: data.serviceDescription,
                                    route_policy_import: data.routePolicyImport,
                                    route_policy_export: data.routePolicyExport,
                                    interface_list: data.attachInterfaces,
                                    interfaces_per_service: data.interfacesPerService ?? 1
                                };
                                const result = await ScalerAPI.generateServices(params);
        
                                const preview = document.getElementById('config-preview');
                                if (preview) {
                                    const lines = result.config.split('\n');
                                    preview.textContent = lines.slice(0, 30).join('\n') + 
                                        (lines.length > 30 ? `\n... (${lines.length} lines total)` : '');
                                }
        
                                ScalerGUI.WizardController.data.generatedConfig = result.config;
                                try {
                                    const val = await ScalerAPI.validateConfig({ config: result.config, hierarchy: 'services' });
                                    const vEl = document.getElementById('config-validation');
                                    if (vEl) vEl.innerHTML = ScalerGUI._renderValidationResults(val.errors, val.warnings, val.suggestions);
                                } catch (e) { console.warn('[ScalerGUI] validation display error:', e.message); }
                                const container = document.getElementById('whats-next-container');
                                if (container) {
                                    const createdData = { deviceId: data.deviceId, interfaces: data.interfaceList || [], serviceType: data.serviceType };
                                    const section = await ScalerGUI._renderWhatsNextSection('services', data, createdData, result.config);
                                    if (section) { container.innerHTML = ''; container.appendChild(section); }
                                }
                            } catch (e) {
                                const previewEl = document.getElementById('config-preview');
                                if (previewEl) previewEl.textContent = `Error: ${e.message}`;
                            }
                        }
                    },
                    ScalerGUI._buildPushStep({
                        radioName: 'push-mode',
                        includeClipboard: false,
                        infoText: (d) => `<strong>Config:</strong> Ready to push ${d.count} ${d.serviceType} services to ${d.deviceId}.`
                    })
                ],
                onComplete: async (data) => {
                    try {
                        const ctx = data.deviceContext || {};
                        const result = await ScalerAPI.pushConfig({
                            device_id: data.deviceId,
                            config: data.generatedConfig,
                            hierarchy: 'services',
                            mode: data.pushMode === 'dry_run' ? 'merge' : (data.load_mode || 'merge'),
                            dry_run: data.dryRun,
                            push_method: data.push_method || 'terminal_paste',
                            load_mode: data.load_mode || 'merge',
                            ssh_host: ctx.mgmt_ip || ctx.ip || '',
                            job_name: `${data.count} services on ${data.deviceId}`
                        });
        
                        this.closePanel('service-wizard');
                        this.recordWizardChange(data.deviceId, 'services', {
                            serviceType: data.serviceType,
                            count: data.count,
                            eviStart: data.eviStart,
                            dryRun: data.dryRun,
                        }, {
                            params: { ...data },
                            generatedConfig: data.generatedConfig,
                            pushMode: data.pushMode || (data.dryRun ? 'dry_run' : 'commit'),
                            jobId: result.job_id,
                        });
                        this.showProgress(result.job_id, `Pushing services to ${data.deviceId}`, {
                            device_id: data.deviceId,
                            onComplete: (success) => { this.updateWizardRunResult(result.job_id, success); }
                        });
                    } catch (e) {
                        this.showNotification(`Push failed: ${e.message}`, 'error');
                    }
                }
            });
        
            if (!hasFresh) {
                this.getDeviceContext(deviceId).then(c => {
                    if (self.WizardController.data?.deviceId === deviceId) {
                        const s = c?.config_summary || {};
                        const svc = c?.services || {};
                        self.WizardController.data.deviceContext = c;
                        if (svc.next_evi) self.WizardController.data.eviStart = svc.next_evi;
                        if (s.as_number) self.WizardController.data.bgpAsn = parseInt(s.as_number, 10) || 65000;
                        self.WizardController.render();
                    }
                }).catch(e => console.warn('[ScalerGUI] wizard operation failed:', e.message));
            }
        },
        
        async openVRFWizard(deviceId = null, prefillParams = null) {
            if (!deviceId) {
                this.openDeviceSelector('VRF / L3VPN Wizard', (id) => this.openVRFWizard(id, prefillParams));
                return;
            }
            if (!this._isDeviceConfigurable(deviceId)) return;
            const content = document.createElement('div');
            content.className = 'scaler-wizard-container';
            content.innerHTML = '<div class="scaler-loading">Loading...</div>';
            this.openPanel('vrf-wizard', `VRF / L3VPN - ${deviceId}`, content, {
                width: '540px',
                parentPanel: 'scaler-menu'
            });
            const self = this;
            const cachedCtx = this._deviceContexts[deviceId];
            const hasFresh = cachedCtx && (Date.now() - (cachedCtx._fetchedAt || 0)) < this._contextCacheTTL;
            let ctx = hasFresh ? cachedCtx : null;
            try {
                if (!hasFresh) ctx = await this.getDeviceContext(deviceId);
            } catch (_) {}
            if (ctx) this._deviceContexts[deviceId] = { ...ctx, _fetchedAt: Date.now() };
            const subifs = (ctx?.interfaces?.subinterface || []).map(s => s.name).filter(Boolean) || [];
            const nextVrf = (ctx?.services?.vrf_count || ctx?.vrfs?.length || 0) + 1;
            ScalerGUI.WizardController.init({
                panelName: 'vrf-wizard',
                quickNavKey: 'vrf-wizard',
                title: 'VRF / L3VPN',
                initialData: {
                    deviceId,
                    deviceContext: ctx,
                    namePrefix: 'VRF_',
                    startNumber: nextVrf,
                    count: 1,
                    description: 'VRF {n}',
                    attachInterfaces: false,
                    interfaceList: [],
                    interfacesPerVrf: 1,
                    enableBgp: true,
                    bgpAs: 65000,
                    routerId: ctx?.config_summary?.router_id || '1.1.1.1',
                    rtMode: 'same_as_rd',
                    rtBase: '65000',
                    ...(prefillParams || {})
                },
                lastRunWizardType: 'vrf',
                onLastRunRerun: (rec) => self._handleLastRunAction(rec, deviceId, ctx),
                onLastRunRerunOther: (rec) => {
                    self.closePanel('vrf-wizard');
                    self.openMirrorWizard(rec.deviceId);
                },
                steps: [
                    {
                        title: 'VRF Naming',
                        render: (d) => `
                            <div class="scaler-form">
                                <div class="scaler-form-row">
                                    <div class="scaler-form-group">
                                        <label>Name Prefix</label>
                                        <input type="text" id="vrf-prefix" class="scaler-input" value="${d.namePrefix || 'VRF_'}" placeholder="VRF_">
                                    </div>
                                    <div class="scaler-form-group">
                                        <label>Start Number</label>
                                        <input type="number" id="vrf-start" class="scaler-input" value="${d.startNumber || 1}" min="1">
                                    </div>
                                    <div class="scaler-form-group">
                                        <label>Count</label>
                                        <input type="number" id="vrf-count" class="scaler-input" value="${d.count || 1}" min="1">
                                    </div>
                                </div>
                                <div class="scaler-form-group">
                                    <label>Description Template</label>
                                    <input type="text" id="vrf-desc" class="scaler-input" value="${d.description || 'VRF {n}'}" placeholder="VRF {n}">
                                </div>
                            </div>`,
                        collectData: () => ({
                            namePrefix: document.getElementById('vrf-prefix')?.value || 'VRF_',
                            startNumber: parseInt(document.getElementById('vrf-start')?.value, 10) || 1,
                            count: parseInt(document.getElementById('vrf-count')?.value, 10) || 1,
                            description: document.getElementById('vrf-desc')?.value || 'VRF {n}'
                        })
                    },
                    {
                        title: 'Interface Attachment',
                        render: (d) => {
                            const chips = (subifs.slice(0, 20).map(s => `<button type="button" class="suggestion-chip" data-value="${s}">${s}</button>`)).join('');
                            const depWarnings = ScalerGUI._getWizardDependencyWarnings('vrf', d);
                            const depHtml = ScalerGUI._renderDependencyWarnings(depWarnings);
                            return `
                            <div class="scaler-form">
                                ${depHtml}
                                <div class="scaler-form-group">
                                    <label><input type="checkbox" id="vrf-attach" ${d.attachInterfaces ? 'checked' : ''}> Attach interfaces to VRFs</label>
                                </div>
                                <div id="vrf-iface-section" style="${d.attachInterfaces ? '' : 'display:none'}">
                                    <label>Sub-interfaces (comma-separated or click)</label>
                                    <input type="text" id="vrf-ifaces" class="scaler-input" value="${(d.interfaceList || []).join(', ')}" placeholder="ge100-18/0/0.100, ...">
                                    ${chips ? `<div class="suggestion-chips">${chips}</div>` : ''}
                                    <div class="scaler-form-group" style="margin-top:8px">
                                        <label>Interfaces per VRF</label>
                                        <input type="number" id="vrf-ifaces-per" class="scaler-input" value="${d.interfacesPerVrf || 1}" min="1">
                                    </div>
                                </div>
                            </div>`;
                        },
                        afterRender: (d) => {
                            document.getElementById('vrf-attach')?.addEventListener('change', (e) => {
                                const sec = document.getElementById('vrf-iface-section');
                                if (sec) sec.style.display = e.target.checked ? 'block' : 'none';
                            });
                            document.querySelectorAll('#vrf-iface-section .suggestion-chip').forEach(b => {
                                b.onclick = () => {
                                    const inp = document.getElementById('vrf-ifaces');
                                    const cur = (inp?.value || '').split(',').map(s => s.trim()).filter(Boolean);
                                    if (!cur.includes(b.dataset.value)) cur.push(b.dataset.value);
                                    if (inp) inp.value = cur.join(', ');
                                };
                            });
                        },
                        collectData: () => {
                            const ifaces = (document.getElementById('vrf-ifaces')?.value || '').split(',').map(s => s.trim()).filter(Boolean);
                            return {
                                attachInterfaces: document.getElementById('vrf-attach')?.checked || false,
                                interfaceList: ifaces,
                                interfacesPerVrf: parseInt(document.getElementById('vrf-ifaces-per')?.value, 10) || 1
                            };
                        }
                    },
                    {
                        title: 'BGP & Route Targets',
                        render: (d) => `
                            <div class="scaler-form">
                                <div class="scaler-form-group">
                                    <label><input type="checkbox" id="vrf-bgp" ${d.enableBgp !== false ? 'checked' : ''}> Enable BGP in VRF</label>
                                </div>
                                <div id="vrf-bgp-section" style="${d.enableBgp !== false ? '' : 'display:none'}">
                                    <div class="scaler-form-row">
                                        <div class="scaler-form-group">
                                            <label>BGP AS</label>
                                            <input type="number" id="vrf-bgp-as" class="scaler-input" value="${d.bgpAs || 65000}">
                                        </div>
                                        <div class="scaler-form-group">
                                            <label>Router ID</label>
                                            <input type="text" id="vrf-router-id" class="scaler-input" value="${d.routerId || '1.1.1.1'}" placeholder="1.1.1.1">
                                        </div>
                                    </div>
                                    <div class="scaler-form-group">
                                        <label>Route Target Mode</label>
                                        <select id="vrf-rt-mode" class="scaler-select">
                                            <option value="same_as_rd" ${d.rtMode === 'same_as_rd' ? 'selected' : ''}>Same as RD</option>
                                            <option value="custom" ${d.rtMode === 'custom' ? 'selected' : ''}>Custom</option>
                                        </select>
                                    </div>
                                    <div class="scaler-form-group">
                                        <label>RT Base (ASN for RT)</label>
                                        <input type="text" id="vrf-rt-base" class="scaler-input" value="${d.rtBase || '65000'}">
                                    </div>
                                </div>
                                <div class="scaler-form-group" style="margin-top:12px">
                                    <label title="Enables FlowSpec address-family in the VRF (ipv4-flowspec). Required for per-VRF FlowSpec filtering."><input type="checkbox" id="vrf-flowspec" ${d.enableFlowspec ? 'checked' : ''}> Enable FlowSpec in VRF</label>
                                </div>
                            </div>`,
                        afterRender: (d) => {
                            document.getElementById('vrf-bgp')?.addEventListener('change', (e) => {
                                const sec = document.getElementById('vrf-bgp-section');
                                if (sec) sec.style.display = e.target.checked ? 'block' : 'none';
                            });
                        },
                        collectData: () => ({
                            enableBgp: document.getElementById('vrf-bgp')?.checked !== false,
                            bgpAs: parseInt(document.getElementById('vrf-bgp-as')?.value, 10) || 65000,
                            routerId: document.getElementById('vrf-router-id')?.value || '1.1.1.1',
                            rtMode: document.getElementById('vrf-rt-mode')?.value || 'same_as_rd',
                            rtBase: document.getElementById('vrf-rt-base')?.value || '65000',
                            enableFlowspec: document.getElementById('vrf-flowspec')?.checked || false
                        })
                    },
                    {
                        title: 'Review',
                        render: (d) => `
                            <div class="scaler-review">
                                <h4>VRF Configuration Summary</h4>
                                <table class="scaler-table scaler-summary-table">
                                    <tr><td>Device</td><td>${d.deviceId}</td></tr>
                                    <tr><td>VRFs</td><td>${d.namePrefix}${d.startNumber} - ${d.namePrefix}${d.startNumber + d.count - 1}</td></tr>
                                    <tr><td>Count</td><td>${d.count}</td></tr>
                                    <tr><td>BGP</td><td>${d.enableBgp ? `AS ${d.bgpAs}, Router-ID ${d.routerId}` : 'Disabled'}</td></tr>
                                    <tr><td>FlowSpec</td><td>${d.enableFlowspec ? 'Enabled' : 'Disabled'}</td></tr>
                                    <tr><td>Interfaces</td><td>${d.attachInterfaces ? (d.interfaceList || []).length + ' attached' : 'None'}</td></tr>
                                </table>
                                <div class="scaler-preview-box">
                                    <label>DNOS Preview:</label>
                                    <pre id="vrf-config-preview">Generating...</pre>
                                </div>
                                <div id="config-validation"></div>
                                <div id="whats-next-container"></div>
                            </div>`,
                        afterRender: async (d) => {
                            try {
                                const params = {
                                    service_type: 'vrf',
                                    name_prefix: d.namePrefix,
                                    start_number: d.startNumber,
                                    count: d.count,
                                    description: d.description,
                                    attach_interfaces: d.attachInterfaces,
                                    interface_list: d.interfaceList || [],
                                    interfaces_per_vrf: d.interfacesPerVrf || 1,
                                    enable_bgp: d.enableBgp,
                                    bgp_config: {
                                        as: d.bgpAs,
                                        router_id: d.routerId,
                                        rd_base: d.routerId,
                                        rd_start: d.startNumber
                                    },
                                    rt_config: { mode: d.rtMode || 'same_as_rd' },
                                    enable_flowspec_on_vrf: d.enableFlowspec || false
                                };
                                const result = await ScalerAPI.generateServices(params);
                                const el = document.getElementById('vrf-config-preview');
                                if (el) el.textContent = result.config || '(empty)';
                                ScalerGUI.WizardController.data.generatedConfig = result.config;
                                try {
                                    const val = await ScalerAPI.validateConfig({ config: result.config, hierarchy: 'services' });
                                    const vEl = document.getElementById('config-validation');
                                    if (vEl) vEl.innerHTML = ScalerGUI._renderValidationResults(val.errors, val.warnings, val.suggestions);
                                } catch (e) { console.warn('[ScalerGUI] validation display error:', e.message); }
                                const container = document.getElementById('whats-next-container');
                                if (container) {
                                    const vrfs = [];
                                    for (let i = 0; i < (d.count || 1); i++) vrfs.push(`${d.namePrefix || 'VRF_'}${(d.startNumber || 1) + i}`);
                                    const createdData = { deviceId: d.deviceId, vrfs, interfaces: d.interfaceList || [] };
                                    const section = await ScalerGUI._renderWhatsNextSection('vrf', d, createdData, result.config);
                                    if (section) { container.innerHTML = ''; container.appendChild(section); }
                                }
                            } catch (e) {
                                const el = document.getElementById('vrf-config-preview');
                                if (el) el.textContent = `Error: ${e.message}`;
                            }
                        }
                    },
                    ScalerGUI._buildPushStep({
                        radioName: 'vrf-push-mode',
                        includeClipboard: false,
                        infoText: (d) => `<strong>Config:</strong> Ready to push ${d.count} VRF(s) to ${d.deviceId}.`
                    })
                ],
                onComplete: async (data) => {
                    try {
                        const ctx = data.deviceContext || {};
                        const result = await ScalerAPI.pushConfig({
                            device_id: data.deviceId,
                            config: data.generatedConfig,
                            hierarchy: 'services',
                            mode: data.pushMode === 'dry_run' ? 'merge' : (data.load_mode || 'merge'),
                            dry_run: data.dryRun,
                            push_method: data.push_method || 'terminal_paste',
                            load_mode: data.load_mode || 'merge',
                            ssh_host: ctx.mgmt_ip || ctx.ip || '',
                            job_name: `${data.count} VRF(s) on ${data.deviceId}`
                        });
                        this.closePanel('vrf-wizard');
                        this.recordWizardChange(data.deviceId, 'vrf', { count: data.count, dryRun: data.dryRun }, {
                            params: { ...data },
                            generatedConfig: data.generatedConfig,
                            pushMode: data.pushMode || (data.dryRun ? 'dry_run' : 'commit'),
                            jobId: result.job_id,
                        });
                        this.showProgress(result.job_id, `Pushing VRF to ${data.deviceId}`, {
                            device_id: data.deviceId,
                            onComplete: (success) => { this.updateWizardRunResult(result.job_id, success); }
                        });
                    } catch (e) {
                        this.showNotification(`Push failed: ${e.message}`, 'error');
                    }
                }
            });
            if (!hasFresh) {
                this.getDeviceContext(deviceId).then(c => {
                    if (self.WizardController.data?.deviceId === deviceId) {
                        self.WizardController.data.deviceContext = c;
                        self.WizardController.render();
                    }
                }).catch(e => console.warn('[ScalerGUI] wizard operation failed:', e.message));
            }
        },
        
        async openBridgeDomainWizard(deviceId = null, prefillParams = null) {
            if (!deviceId) {
                this.openDeviceSelector('Bridge Domain Wizard', (id) => this.openBridgeDomainWizard(id, prefillParams));
                return;
            }
            if (!this._isDeviceConfigurable(deviceId)) return;
            const content = document.createElement('div');
            content.className = 'scaler-wizard-container';
            content.innerHTML = '<div class="scaler-loading">Loading...</div>';
            this.openPanel('bridge-domain-wizard', `Bridge Domain - ${deviceId}`, content, {
                width: '540px',
                parentPanel: 'scaler-menu'
            });
            const self = this;
            const cachedCtx = this._deviceContexts[deviceId];
            const hasFresh = cachedCtx && (Date.now() - (cachedCtx._fetchedAt || 0)) < this._contextCacheTTL;
            let ctx = hasFresh ? cachedCtx : null;
            try {
                if (!hasFresh) ctx = await this.getDeviceContext(deviceId);
            } catch (_) {}
            if (ctx) this._deviceContexts[deviceId] = { ...ctx, _fetchedAt: Date.now() };
            const subifs = (ctx?.interfaces?.subinterface || []).map(s => s.name).filter(Boolean) || [];
            const bdCount = (ctx?.bridge_domains || []).length || 0;
            const nextBd = bdCount + 1;
            ScalerGUI.WizardController.init({
                panelName: 'bridge-domain-wizard',
                quickNavKey: 'bridge-domain-wizard',
                title: 'Bridge Domain',
                initialData: {
                    deviceId,
                    deviceContext: ctx,
                    namePrefix: 'BD_',
                    startNumber: nextBd,
                    count: 1,
                    description: 'Bridge Domain {n}',
                    interfaceList: [],
                    interfacesPerBd: 1,
                    stormControlRate: 0,
                    ...(prefillParams || {})
                },
                lastRunWizardType: 'bridge-domain',
                onLastRunRerun: (rec) => self._handleLastRunAction(rec, deviceId, ctx),
                onLastRunRerunOther: (rec) => {
                    self.closePanel('bridge-domain-wizard');
                    self.openMirrorWizard(rec.deviceId);
                },
                steps: [
                    {
                        title: 'BD Naming',
                        render: (d) => `
                            <div class="scaler-form">
                                <div class="scaler-form-row">
                                    <div class="scaler-form-group">
                                        <label>Name Prefix</label>
                                        <input type="text" id="bd-prefix" class="scaler-input" value="${d.namePrefix || 'BD_'}" placeholder="BD_">
                                    </div>
                                    <div class="scaler-form-group">
                                        <label>Start Number</label>
                                        <input type="number" id="bd-start" class="scaler-input" value="${d.startNumber || 1}" min="1">
                                    </div>
                                    <div class="scaler-form-group">
                                        <label>Count</label>
                                        <input type="number" id="bd-count" class="scaler-input" value="${d.count || 1}" min="1">
                                    </div>
                                </div>
                                <div class="scaler-form-group">
                                    <label>Description Template</label>
                                    <input type="text" id="bd-desc" class="scaler-input" value="${d.description || 'Bridge Domain {n}'}" placeholder="Bridge Domain {n}">
                                </div>
                            </div>`,
                        collectData: () => ({
                            namePrefix: document.getElementById('bd-prefix')?.value || 'BD_',
                            startNumber: parseInt(document.getElementById('bd-start')?.value, 10) || 1,
                            count: parseInt(document.getElementById('bd-count')?.value, 10) || 1,
                            description: document.getElementById('bd-desc')?.value || 'Bridge Domain {n}'
                        })
                    },
                    {
                        title: 'Interface Attachment',
                        render: (d) => {
                            const chips = (subifs.slice(0, 20).map(s => `<button type="button" class="suggestion-chip" data-value="${s}">${s}</button>`)).join('');
                            return `
                            <div class="scaler-form">
                                <label>Sub-interfaces (comma-separated or click)</label>
                                <input type="text" id="bd-ifaces" class="scaler-input" value="${(d.interfaceList || []).join(', ')}" placeholder="ge100-18/0/0.100, ...">
                                ${chips ? `<div class="suggestion-chips">${chips}</div>` : ''}
                                <div class="scaler-form-group" style="margin-top:8px">
                                    <label>Interfaces per BD</label>
                                    <input type="number" id="bd-ifaces-per" class="scaler-input" value="${d.interfacesPerBd || 1}" min="1">
                                </div>
                            </div>`;
                        },
                        afterRender: () => {
                            const form = document.getElementById('bd-ifaces')?.closest('.scaler-form');
                            form?.querySelectorAll('.suggestion-chip').forEach(b => {
                                b.onclick = () => {
                                    const inp = document.getElementById('bd-ifaces');
                                    const cur = (inp?.value || '').split(',').map(s => s.trim()).filter(Boolean);
                                    if (!cur.includes(b.dataset.value)) cur.push(b.dataset.value);
                                    if (inp) inp.value = cur.join(', ');
                                };
                            });
                        },
                        collectData: () => {
                            const ifaces = (document.getElementById('bd-ifaces')?.value || '').split(',').map(s => s.trim()).filter(Boolean);
                            return {
                                interfaceList: ifaces,
                                interfacesPerBd: parseInt(document.getElementById('bd-ifaces-per')?.value, 10) || 1
                            };
                        }
                    },
                    {
                        title: 'Storm Control',
                        render: (d) => `
                            <div class="scaler-form">
                                <div class="scaler-form-group">
                                    <label>Broadcast packet rate limit (pps, 0=disabled)</label>
                                    <input type="number" id="bd-storm" class="scaler-input" value="${d.stormControlRate || 0}" min="0" placeholder="0 = disabled">
                                </div>
                                <div class="scaler-info-box">Optional. 10-100000000 pps. 0 disables storm control.</div>
                            </div>`,
                        collectData: () => ({
                            stormControlRate: parseInt(document.getElementById('bd-storm')?.value, 10) || 0
                        })
                    },
                    {
                        title: 'Review',
                        render: (d) => `
                            <div class="scaler-review">
                                <h4>Bridge Domain Summary</h4>
                                <table class="scaler-table scaler-summary-table">
                                    <tr><td>Device</td><td>${d.deviceId}</td></tr>
                                    <tr><td>BDs</td><td>${d.namePrefix}${d.startNumber} - ${d.namePrefix}${d.startNumber + d.count - 1}</td></tr>
                                    <tr><td>Interfaces</td><td>${(d.interfaceList || []).length} attached</td></tr>
                                    <tr><td>Storm Control</td><td>${d.stormControlRate ? d.stormControlRate + ' pps' : 'Disabled'}</td></tr>
                                </table>
                                <div class="scaler-preview-box">
                                    <label>DNOS Preview:</label>
                                    <pre id="bd-config-preview">Generating...</pre>
                                </div>
                                <div id="config-validation"></div>
                                <div id="whats-next-container"></div>
                            </div>`,
                        afterRender: async (d) => {
                            try {
                                const params = {
                                    service_type: 'bridge-domain',
                                    name_prefix: d.namePrefix,
                                    start_number: d.startNumber,
                                    count: d.count,
                                    description: d.description,
                                    interface_list: d.interfaceList || [],
                                    interfaces_per_service: d.interfacesPerBd || 1,
                                    storm_control_broadcast_rate: d.stormControlRate || null
                                };
                                const result = await ScalerAPI.generateServices(params);
                                const el = document.getElementById('bd-config-preview');
                                if (el) el.textContent = result.config || '(empty)';
                                ScalerGUI.WizardController.data.generatedConfig = result.config;
                                try {
                                    const val = await ScalerAPI.validateConfig({ config: result.config, hierarchy: 'services' });
                                    const vEl = document.getElementById('config-validation');
                                    if (vEl) vEl.innerHTML = ScalerGUI._renderValidationResults(val.errors, val.warnings, val.suggestions);
                                } catch (e) { console.warn('[ScalerGUI] validation display error:', e.message); }
                                const container = document.getElementById('whats-next-container');
                                if (container) {
                                    const createdData = { deviceId: d.deviceId, interfaces: d.interfaceList || [] };
                                    const section = await ScalerGUI._renderWhatsNextSection('bridge-domain', d, createdData, result.config);
                                    if (section) { container.innerHTML = ''; container.appendChild(section); }
                                }
                            } catch (e) {
                                const el = document.getElementById('bd-config-preview');
                                if (el) el.textContent = `Error: ${e.message}`;
                            }
                        }
                    },
                    ScalerGUI._buildPushStep({
                        radioName: 'bd-push-mode',
                        includeClipboard: false,
                        infoText: (d) => `<strong>Config:</strong> Ready to push ${d.count} Bridge Domain(s) to ${d.deviceId}.`
                    })
                ],
                onComplete: async (data) => {
                    try {
                        const ctx = data.deviceContext || {};
                        const result = await ScalerAPI.pushConfig({
                            device_id: data.deviceId,
                            config: data.generatedConfig,
                            hierarchy: 'services',
                            mode: data.pushMode === 'dry_run' ? 'merge' : (data.load_mode || 'merge'),
                            dry_run: data.dryRun,
                            push_method: data.push_method || 'terminal_paste',
                            load_mode: data.load_mode || 'merge',
                            ssh_host: ctx.mgmt_ip || ctx.ip || '',
                            job_name: `${data.count} BD(s) on ${data.deviceId}`
                        });
                        this.closePanel('bridge-domain-wizard');
                        this.recordWizardChange(data.deviceId, 'bridge-domain', { count: data.count, dryRun: data.dryRun }, {
                            params: { ...data },
                            generatedConfig: data.generatedConfig,
                            pushMode: data.pushMode || (data.dryRun ? 'dry_run' : 'commit'),
                            jobId: result.job_id,
                        });
                        this.showProgress(result.job_id, `Pushing Bridge Domain to ${data.deviceId}`, {
                            device_id: data.deviceId,
                            onComplete: (success) => { this.updateWizardRunResult(result.job_id, success); }
                        });
                    } catch (e) {
                        this.showNotification(`Push failed: ${e.message}`, 'error');
                    }
                }
            });
            if (!hasFresh) {
                this.getDeviceContext(deviceId).then(c => {
                    if (self.WizardController.data?.deviceId === deviceId) {
                        self.WizardController.data.deviceContext = c;
                        self.WizardController.render();
                    }
                }).catch(e => console.warn('[ScalerGUI] wizard operation failed:', e.message));
            }
        },
        async openMultihomingWizard() {
            const content = document.createElement('div');
            content.className = 'scaler-mh-wizard';
            content.innerHTML = '<div class="scaler-loading">Loading devices...</div>';
            this.openPanel('multihoming-wizard', 'Multihoming ESI Wizard', content, {
                width: '560px',
                parentPanel: 'scaler-menu'
            });
        
            try {
                const devices = await this._getWizardDeviceList();
                if (devices.length === 0) {
                    content.innerHTML = '<div class="scaler-info-box" style="color:var(--dn-orange,#e67e22)">Add devices to the topology first. No devices on canvas.</div>';
                    return;
                }
        
                const self = this;
        
                this.WizardController.init({
                    panelName: 'multihoming-wizard',
                    title: 'Multihoming ESI Wizard',
                    initialData: {
                        devices,
                        selectedDeviceIds: [],
                        esiPrefix: '00:11:22:33:44',
                        redundancyMode: 'single-active',
                        matchRt: true,
                        compareResult: null,
                        _comparing: false,
                    },
                    wizardHeader: (data) => {
                        const ids = data.selectedDeviceIds || [];
                        if (ids.length !== 2) return null;
                        const devs = (data.devices || []).filter(d => ids.includes(d.id));
                        const div = document.createElement('div');
                        div.className = 'device-context-panel';
                        div.innerHTML = `<div class="mirror-direction-bar">
                            <span class="mirror-direction-device">${self.escapeHtml(devs[0]?.hostname || ids[0])}</span>
                            <span class="mirror-direction-arrow">&harr;</span>
                            <span class="mirror-direction-device">${self.escapeHtml(devs[1]?.hostname || ids[1])}</span>
                        </div>`;
                        return div;
                    },
                    steps: [
                        {
                            title: 'Device Pair',
                            render: (data) => {
                                const devs = data.devices || [];
                                const withSsh = devs.filter(d => d.hasSSH);
                                const noSsh = devs.filter(d => !d.hasSSH);
                                const renderDev = (d, disabled) => {
                                    const sel = (data.selectedDeviceIds || []).includes(d.id);
                                    return `<label class="scaler-checkbox-item"${disabled ? ' style="opacity:0.5"' : ''}>
                                        <input type="checkbox" value="${d.id}" ${sel ? 'checked' : ''}${disabled ? ' disabled' : ''}>
                                        <span>${d.hostname || d.id}${disabled ? ' (no SSH)' : ''}</span>
                                        <span class="scaler-device-ip">${disabled ? '' : (d.ip || '')}</span>
                                    </label>`;
                                };
                                return `<div class="scaler-form">
                                    <div class="scaler-info-box">Select exactly 2 PE devices to synchronize ESI multihoming.</div>
                                    <div class="scaler-form-group">
                                        <label>Devices</label>
                                        <div id="mh-devices" class="scaler-checkbox-list">
                                            ${withSsh.map(d => renderDev(d, false)).join('')}
                                            ${noSsh.length ? `<div class="scaler-device-select-separator" style="margin-top:8px">No SSH configured</div>${noSsh.map(d => renderDev(d, true)).join('')}` : ''}
                                        </div>
                                    </div>
                                    <div class="scaler-form-row">
                                        <div class="scaler-form-group">
                                            <label>ESI Prefix</label>
                                            <input type="text" id="mh-esi-prefix" class="scaler-input" value="${data.esiPrefix || '00:11:22:33:44'}" placeholder="00:11:22:33:44">
                                        </div>
                                        <div class="scaler-form-group">
                                            <label>Redundancy Mode</label>
                                            <select id="mh-mode" class="scaler-select">
                                                <option value="single-active" ${(data.redundancyMode || 'single-active') === 'single-active' ? 'selected' : ''}>Single-Active</option>
                                                <option value="all-active" ${data.redundancyMode === 'all-active' ? 'selected' : ''}>All-Active</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="scaler-form-group">
                                        <label class="scaler-checkbox-item"><input type="checkbox" id="mh-match-rt" ${data.matchRt !== false ? 'checked' : ''}> Match interfaces by Route Target + VLAN</label>
                                    </div>
                                </div>`;
                            },
                            collectData: () => ({
                                selectedDeviceIds: self._getCheckedDeviceIds('mh-devices'),
                                esiPrefix: document.getElementById('mh-esi-prefix')?.value || '00:11:22:33:44',
                                redundancyMode: document.getElementById('mh-mode')?.value || 'single-active',
                                matchRt: document.getElementById('mh-match-rt')?.checked !== false,
                                compareResult: null,
                            }),
                            validate: (data) => {
                                const ids = data.selectedDeviceIds || [];
                                if (ids.length !== 2) {
                                    self.showNotification('Select exactly 2 devices', 'warning');
                                    return false;
                                }
                                return true;
                            }
                        },
                        {
                            title: 'Compare',
                            render: (data) => {
                                const result = data.compareResult;
                                const ids = data.selectedDeviceIds || [];
                                const dev1 = (data.devices || []).find(d => d.id === ids[0]);
                                const dev2 = (data.devices || []).find(d => d.id === ids[1]);
                                if (!result) {
                                    return `<div class="scaler-form"><div class="scaler-loading">Comparing ESI config between ${dev1?.hostname || ids[0]} and ${dev2?.hostname || ids[1]}...</div></div>`;
                                }
                                const total = (result.matching || 0) + (result.device1_only || 0) + (result.device2_only || 0);
                                const syncNeeded = result.device1_only > 0 || result.device2_only > 0;
                                return `<div class="scaler-form">
                                    <div class="mirror-analysis-summary">
                                        <div class="mirror-stat mirror-stat--skip"><span class="mirror-stat-num">${result.matching || 0}</span><span class="mirror-stat-label">Matching</span></div>
                                        <div class="mirror-stat mirror-stat--add"><span class="mirror-stat-num">${result.device1_only || 0}</span><span class="mirror-stat-label">Only ${dev1?.hostname || ids[0]}</span></div>
                                        <div class="mirror-stat mirror-stat--del"><span class="mirror-stat-num">${result.device2_only || 0}</span><span class="mirror-stat-label">Only ${dev2?.hostname || ids[1]}</span></div>
                                    </div>
                                    ${syncNeeded
                                        ? `<div class="scaler-info-box" style="margin-top:12px">ESI config differs between devices. Sync will copy ESI from <strong>${dev1?.hostname || ids[0]}</strong> to <strong>${dev2?.hostname || ids[1]}</strong>.</div>`
                                        : `<div class="scaler-info-box" style="margin-top:12px;border-color:var(--dn-cyan,#00d4aa)">ESI config is already in sync across both devices (${total} interfaces).</div>`
                                    }
                                    <div class="scaler-form-group" style="margin-top:8px">
                                        <button type="button" class="scaler-btn scaler-btn-sm" id="mh-recompare">Re-compare</button>
                                    </div>
                                </div>`;
                            },
                            afterRender: (data) => {
                                if (!data.compareResult && !data._comparing) {
                                    const ids = data.selectedDeviceIds || [];
                                    if (ids.length === 2) {
                                        self.WizardController.data._comparing = true;
                                        ScalerAPI.compareMultihoming(ids).then(result => {
                                            self.WizardController.data.compareResult = result;
                                            self.WizardController.data._comparing = false;
                                            self.WizardController.render();
                                        }).catch(e => {
                                            self.WizardController.data._comparing = false;
                                            self.showNotification(`Compare failed: ${e.message}`, 'error');
                                        });
                                    }
                                }
                                document.getElementById('mh-recompare')?.addEventListener('click', () => {
                                    self.WizardController.data.compareResult = null;
                                    self.WizardController.data._comparing = false;
                                    self.WizardController.render();
                                });
                            },
                            collectData: () => ({}),
                            skipIf: (data) => (data.selectedDeviceIds || []).length !== 2
                        },
                        {
                            title: 'Sync',
                            finalButtonText: 'Sync Multihoming',
                            render: (data) => {
                                const ids = data.selectedDeviceIds || [];
                                const dev1 = (data.devices || []).find(d => d.id === ids[0]);
                                const dev2 = (data.devices || []).find(d => d.id === ids[1]);
                                const result = data.compareResult;
                                const syncNeeded = result && (result.device1_only > 0 || result.device2_only > 0);
                                return `<div class="scaler-form">
                                    <div class="scaler-info-box">${syncNeeded
                                        ? `Sync will copy multihoming ESI config from <strong>${dev1?.hostname || ids[0]}</strong> to <strong>${dev2?.hostname || ids[1]}</strong>.`
                                        : `ESI config is already in sync. Push will re-apply to ensure consistency.`
                                    }</div>
                                    <div class="mh-sync-summary">
                                        <div class="mh-sync-row"><span class="mh-sync-label">Source</span><span class="mh-sync-value">${dev1?.hostname || ids[0]}</span></div>
                                        <div class="mh-sync-row"><span class="mh-sync-label">Target</span><span class="mh-sync-value">${dev2?.hostname || ids[1]}</span></div>
                                        <div class="mh-sync-row"><span class="mh-sync-label">ESI Prefix</span><span class="mh-sync-value"><code>${data.esiPrefix || '00:11:22:33:44'}</code></span></div>
                                        <div class="mh-sync-row"><span class="mh-sync-label">Redundancy</span><span class="mh-sync-value">${data.redundancyMode || 'single-active'}</span></div>
                                        <div class="mh-sync-row"><span class="mh-sync-label">Match by RT</span><span class="mh-sync-value">${data.matchRt !== false ? 'Yes' : 'No'}</span></div>
                                    </div>
                                    ${result ? `<div class="mh-sync-summary" style="margin-top:8px">
                                        <div class="mh-sync-row"><span class="mh-sync-label">Matching ESIs</span><span class="mh-sync-value">${result.matching || 0}</span></div>
                                        <div class="mh-sync-row"><span class="mh-sync-label">To sync</span><span class="mh-sync-value">${(result.device1_only || 0) + (result.device2_only || 0)}</span></div>
                                    </div>` : ''}
                                </div>`;
                            },
                            collectData: () => ({}),
                            validate: (data) => (data.selectedDeviceIds || []).length === 2
                        }
                    ],
                    onComplete: async (data) => {
                        const ids = data.selectedDeviceIds || [];
                        if (ids.length !== 2) return;
                        self.closePanel('multihoming-wizard');
                        try {
                            const sshHosts = {};
                            (data.devices || []).filter(d => ids.includes(d.id)).forEach(d => {
                                sshHosts[d.id] = d.ssh_host || d.ip || '';
                            });
                            const result = await ScalerAPI.syncMultihoming({
                                device_ids: ids,
                                esi_prefix: data.esiPrefix || '00:11:22:33:44',
                                redundancy_mode: data.redundancyMode || 'single-active',
                                match_neighbor: data.matchRt !== false,
                                ssh_hosts: sshHosts
                            });
                            self.showProgress(result.job_id, `MH Sync: ${ids[0]} -> ${ids[1]}`, {
                                device_id: ids[1],
                                onComplete: (success, res) => {
                                    if (success) self.showNotification('Multihoming sync committed', 'success');
                                    else if (!res?.cancelled) self.showNotification('MH sync failed', 'error');
                                }
                            });
                        } catch (e) {
                            self.showNotification(`Sync failed: ${e.message}`, 'error');
                        }
                    }
                });
            } catch (e) {
                const panel = this.state.activePanels['multihoming-wizard'];
                if (panel) {
                    const cd = panel.querySelector('.scaler-panel-content');
                    if (cd) cd.innerHTML = `<div class="scaler-error">${e.message}</div>`;
                }
            }
        },

    });
})(window.ScalerGUI);
