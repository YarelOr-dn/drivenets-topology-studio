/**
 * ScalerGUI: routing policy, BGP, IGP wizards
 * @requires scaler-api.js
 * @requires scaler-gui.js (core)
 */
(function (G) {
    'use strict';
    if (!G) {
        console.error('[scaler-gui-wizards-routing.js] ScalerGUI core not loaded');
        return;
    }
    Object.assign(G, {
        async openRoutingPolicyWizard(deviceId = null, prefillParams = null) {
            if (!deviceId) {
                this.openDeviceSelector('Routing Policy Wizard', (id) => this.openRoutingPolicyWizard(id, prefillParams));
                return;
            }
            if (!this._isDeviceConfigurable(deviceId)) return;
            const content = document.createElement('div');
            content.className = 'scaler-wizard-container';
            content.innerHTML = '<div class="scaler-loading">Loading...</div>';
            this.openPanel('routing-policy-wizard', `Routing Policy - ${deviceId}`, content, {
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
            const existingPolicies = ctx?.routing_policies?.policies || [];
            ScalerGUI.WizardController.init({
                panelName: 'routing-policy-wizard',
                quickNavKey: 'routing-policy-wizard',
                title: 'Routing Policy',
                initialData: {
                    deviceId,
                    deviceContext: ctx,
                    policyType: 'prefix-list',
                    name: 'PL-1',
                    ipVersion: 'ipv4',
                    entries: [{ prefix: '10.0.0.0/8', action: 'permit' }],
                    routePolicyBody: 'return deny',
                    ...(prefillParams || {})
                },
                lastRunWizardType: 'routing-policy',
                onLastRunRerun: (rec) => self._handleLastRunAction(rec, deviceId, ctx),
                onLastRunRerunOther: (rec) => {
                    self.closePanel('routing-policy-wizard');
                    self.openMirrorWizard(rec.deviceId);
                },
                steps: [
                    {
                        title: 'Type',
                        render: (d) => `
                            <div class="scaler-form">
                                <div class="scaler-form-group">
                                    <label>Building Block Type</label>
                                    <select id="rp-type" class="scaler-select">
                                        <option value="prefix-list" ${d.policyType === 'prefix-list' ? 'selected' : ''}>Prefix List</option>
                                        <option value="route-policy" ${d.policyType === 'route-policy' ? 'selected' : ''}>Route-Policy (new syntax)</option>
                                    </select>
                                </div>
                            </div>`,
                        collectData: () => ({
                            policyType: document.getElementById('rp-type')?.value || 'prefix-list'
                        })
                    },
                    {
                        title: 'Definition',
                        render: (d) => {
                            if (d.policyType === 'route-policy') {
                                return `
                            <div class="scaler-form">
                                <div class="scaler-form-group">
                                    <label>Policy Name</label>
                                    <input type="text" id="rp-name" class="scaler-input" value="${d.name || 'POL-1'}" placeholder="POL-1">
                                </div>
                                <div class="scaler-form-group">
                                    <label>Policy Body (e.g. if (prefix-ipv4 in PL_X) { return allow } return deny)</label>
                                    <textarea id="rp-body" class="scaler-input" rows="3" placeholder="return deny">${d.routePolicyBody || 'return deny'}</textarea>
                                </div>
                                <div class="scaler-info-box">New syntax (SW-181332). Use if/return allow/return deny. Body becomes quoted one-liner.</div>
                            </div>`;
                            }
                            const ents = (d.entries || [{ prefix: '10.0.0.0/8', action: 'permit' }]);
                            const rows = ents.map((e, i) =>
                                `<tr><td><input type="text" id="rp-prefix-${i}" value="${e.prefix || ''}" placeholder="10.0.0.0/8" class="scaler-input" style="width:100%"></td>
                                <td><input type="number" id="rp-ge-${i}" value="${e.ge || ''}" placeholder="ge" class="scaler-input" style="width:50px" min="0" max="128" title="Greater-than-or-equal prefix length"></td>
                                <td><input type="number" id="rp-le-${i}" value="${e.le || ''}" placeholder="le" class="scaler-input" style="width:50px" min="0" max="128" title="Less-than-or-equal prefix length"></td>
                                <td><select id="rp-action-${i}" class="scaler-select"><option value="permit" ${e.action === 'permit' ? 'selected' : ''}>permit</option><option value="deny" ${e.action === 'deny' ? 'selected' : ''}>deny</option></select></td></tr>`).join('');
                            return `
                            <div class="scaler-form">
                                <div class="scaler-form-group">
                                    <label>Prefix List Name</label>
                                    <input type="text" id="rp-name" class="scaler-input" value="${d.name || 'PL-1'}" placeholder="PL-1">
                                </div>
                                <div class="scaler-form-group">
                                    <label>IP Version</label>
                                    <select id="rp-ipv" class="scaler-select">
                                        <option value="ipv4" ${d.ipVersion === 'ipv4' ? 'selected' : ''}>IPv4</option>
                                        <option value="ipv6" ${d.ipVersion === 'ipv6' ? 'selected' : ''}>IPv6</option>
                                    </select>
                                </div>
                                <div class="scaler-form-group">
                                    <label>Entries</label>
                                    <table class="scaler-table"><thead><tr><th>Prefix</th><th title="Greater-than-or-equal prefix length">ge</th><th title="Less-than-or-equal prefix length">le</th><th>Action</th></tr></thead><tbody id="rp-entries">${rows}</tbody></table>
                                    <button type="button" id="rp-add-entry" class="scaler-btn scaler-btn-secondary" style="margin-top:6px">Add entry</button>
                                </div>
                            </div>`;
                        },
                        afterRender: (d) => {
                            const addBtn = document.getElementById('rp-add-entry');
                            if (addBtn) {
                                addBtn.onclick = () => {
                                    const tbody = document.getElementById('rp-entries');
                                    const i = tbody.querySelectorAll('tr').length;
                                    const row = document.createElement('tr');
                                    row.innerHTML = `<td><input type="text" id="rp-prefix-${i}" value="0.0.0.0/0" placeholder="0.0.0.0/0" class="scaler-input" style="width:100%"></td>
                                        <td><input type="number" id="rp-ge-${i}" value="" placeholder="ge" class="scaler-input" style="width:50px" min="0" max="128" title="Greater-than-or-equal prefix length"></td>
                                        <td><input type="number" id="rp-le-${i}" value="" placeholder="le" class="scaler-input" style="width:50px" min="0" max="128" title="Less-than-or-equal prefix length"></td>
                                        <td><select id="rp-action-${i}" class="scaler-select"><option value="permit">permit</option><option value="deny" selected>deny</option></select></td>`;
                                    tbody.appendChild(row);
                                };
                            }
                        },
                        collectData: () => {
                            const type = ScalerGUI.WizardController?.data?.policyType || 'prefix-list';
                            if (type === 'route-policy') {
                                return {
                                    name: document.getElementById('rp-name')?.value || 'POL-1',
                                    routePolicyBody: document.getElementById('rp-body')?.value || 'return deny'
                                };
                            }
                            const rows = document.querySelectorAll('#rp-entries tr');
                            const entries = [];
                            rows.forEach((r, i) => {
                                const pref = document.getElementById(`rp-prefix-${i}`)?.value;
                                const act = document.getElementById(`rp-action-${i}`)?.value;
                                const ge = parseInt(document.getElementById(`rp-ge-${i}`)?.value);
                                const le = parseInt(document.getElementById(`rp-le-${i}`)?.value);
                                if (pref) {
                                    const entry = { prefix: pref, action: act || 'deny' };
                                    if (ge > 0) entry.ge = ge;
                                    if (le > 0) entry.le = le;
                                    entries.push(entry);
                                }
                            });
                            return {
                                name: document.getElementById('rp-name')?.value || 'PL-1',
                                ipVersion: document.getElementById('rp-ipv')?.value || 'ipv4',
                                entries: entries.length ? entries : [{ prefix: '0.0.0.0/0', action: 'deny' }]
                            };
                        }
                    },
                    {
                        title: 'Review',
                        render: (d) => `
                            <div class="scaler-review">
                                <h4>Routing Policy Summary</h4>
                                <table class="scaler-table scaler-summary-table">
                                    <tr><td>Device</td><td>${d.deviceId}</td></tr>
                                    <tr><td>Type</td><td>${d.policyType}</td></tr>
                                    <tr><td>Name</td><td>${d.name}</td></tr>
                                    ${d.policyType === 'prefix-list' ? `<tr><td>Entries</td><td>${(d.entries || []).length}</td></tr>` : ''}
                                </table>
                                <div class="scaler-preview-box">
                                    <label>DNOS Preview:</label>
                                    <pre id="rp-config-preview">Generating...</pre>
                                </div>
                                <div id="config-validation"></div>
                                <div id="whats-next-container"></div>
                            </div>`,
                        afterRender: async (d) => {
                            try {
                                let params;
                                if (d.policyType === 'route-policy') {
                                    const body = (d.routePolicyBody || 'return deny').trim();
                                    const fullBody = body.includes('route-policy') ? body : `route-policy ${d.name}() { ${body} }`;
                                    params = { type: 'route-policy', name: d.name, body: fullBody };
                                } else {
                                    params = { type: 'prefix-list', name: d.name, ip_version: d.ipVersion, entries: d.entries || [] };
                                }
                                const result = await ScalerAPI.generateRoutingPolicy(params);
                                const el = document.getElementById('rp-config-preview');
                                if (el) el.textContent = result.config || '(empty)';
                                ScalerGUI.WizardController.data.generatedConfig = result.config;
                                try {
                                    const val = await ScalerAPI.validateConfig({ config: result.config, hierarchy: 'routing-policy' });
                                    const vEl = document.getElementById('config-validation');
                                    if (vEl) vEl.innerHTML = ScalerGUI._renderValidationResults(val.errors, val.warnings, val.suggestions);
                                    if (d.policyType === 'route-policy' && result.config) {
                                        try {
                                            const pol = await ScalerAPI.validatePolicy({ config_text: result.config, device_id: d.deviceId, ssh_host: (d.deviceContext || {}).mgmt_ip || (d.deviceContext || {}).ip || '' });
                                            if (pol?.issues?.length && vEl) {
                                                const polHtml = pol.issues.map(i => `<div class="scaler-validation-issue" style="color:${i.severity === 'error' ? '#e74c3c' : '#f39c12'}">${i.issue || i.component}${i.suggestion ? ' - ' + i.suggestion : ''}</div>`).join('');
                                                vEl.innerHTML = (vEl.innerHTML || '') + polHtml;
                                            }
                                        } catch (_) {}
                                    }
                                } catch (_) {}
                                const container = document.getElementById('whats-next-container');
                                if (container) {
                                    const createdData = { deviceId: d.deviceId };
                                    const section = await ScalerGUI._renderWhatsNextSection('routing-policy', d, createdData, result.config);
                                    if (section) { container.innerHTML = ''; container.appendChild(section); }
                                }
                            } catch (e) {
                                const el = document.getElementById('rp-config-preview');
                                if (el) el.textContent = `Error: ${e.message}`;
                            }
                        }
                    },
                    ScalerGUI._buildPushStep({
                        radioName: 'rp-push-mode',
                        includeClipboard: false,
                        infoText: (d) => `<strong>Config:</strong> Ready to push ${d.policyType} ${d.name} to ${d.deviceId}.`
                    })
                ],
                onComplete: async (data) => {
                    try {
                        const ctx = data.deviceContext || {};
                        const result = await ScalerAPI.pushConfig({
                            device_id: data.deviceId,
                            config: data.generatedConfig,
                            hierarchy: 'routing-policy',
                            mode: data.pushMode === 'dry_run' ? 'merge' : (data.load_mode || 'merge'),
                            dry_run: data.dryRun,
                            push_method: data.push_method || 'terminal_paste',
                            load_mode: data.load_mode || 'merge',
                            ssh_host: ctx.mgmt_ip || ctx.ip || '',
                            job_name: `Routing policy ${data.name} on ${data.deviceId}`
                        });
                        this.closePanel('routing-policy-wizard');
                        this.recordWizardChange(data.deviceId, 'routing-policy', { name: data.name, dryRun: data.dryRun }, {
                            params: { ...data },
                            generatedConfig: data.generatedConfig,
                            pushMode: data.pushMode || (data.dryRun ? 'dry_run' : 'commit'),
                            jobId: result.job_id,
                        });
                        this.showProgress(result.job_id, `Pushing routing policy to ${data.deviceId}`, {
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
        
        // =========================================================================
        // MULTIHOMING WIZARD (WizardController, 3 steps)
        // =========================================================================
        async openBGPWizard(deviceId = null, prefillParams = null) {
            if (!deviceId) { this.openDeviceSelector('BGP Configuration', (id) => this.openBGPWizard(id, prefillParams)); return; }
            if (!this._isDeviceConfigurable(deviceId)) return;
            const content = document.createElement('div');
            content.innerHTML = '<div class="scaler-loading">Loading...</div>';
            this.openPanel('bgp-wizard', `BGP Wizard - ${deviceId}`, content, { width: '540px', parentPanel: 'scaler-menu' });
            const self = this;
            const cachedCtx = this._deviceContexts[deviceId];
            const hasFresh = cachedCtx && (Date.now() - (cachedCtx._fetchedAt || 0)) < this._contextCacheTTL;
            let ctx = hasFresh ? this._applyPendingChanges(deviceId, cachedCtx) : null;
            const summary = ctx?.config_summary || {};
            let localAs = summary.as_number ? parseInt(summary.as_number, 10) : 65000;
            try {
                const resolved = this._resolveDeviceId(deviceId);
                const smart = await ScalerAPI.getSmartDefaults(deviceId, resolved.sshHost || '');
                if (smart?.defaults) {
                    if (!summary.as_number && smart.defaults.asn) localAs = smart.defaults.asn;
                    if (!ctx?.config_summary) ctx = ctx || {};
                    if (!ctx.config_summary) ctx.config_summary = {};
                    if (!ctx.config_summary.router_id && smart.defaults.router_id) ctx.config_summary.router_id = smart.defaults.router_id;
                }
            } catch (_) {}
            this.WizardController.init({
                panelName: 'bgp-wizard',
                quickNavKey: 'bgp-wizard',
                title: `BGP Wizard - ${deviceId}`,
                initialData: { deviceId, deviceContext: ctx, local_as: isNaN(localAs) ? 65000 : localAs, ...(prefillParams || {}) },
                lastRunWizardType: 'bgp',
                onLastRunRerun: (rec) => self._handleLastRunAction(rec, deviceId, ctx),
                onLastRunRerunOther: (rec) => {
                    self.closePanel('bgp-wizard');
                    self.openMirrorWizard(rec.deviceId);
                },
                wizardHeader: (data) => self.renderContextPanel(deviceId, data.deviceContext || {}, { wizardType: 'bgp', onRefresh: () => self.refreshDeviceContextLive(deviceId).then(c => { self.WizardController.data.deviceContext = c; self.WizardController.render(); }) }),
                steps: [
                    {
                        title: 'Peer Setup',
                        render: (d) => {
                            const asVal = d.local_as || (d.deviceContext?.config_summary?.as_number ? parseInt(d.deviceContext.config_summary.as_number, 10) : 65000);
                            return `
                            <div class="scaler-form">
                                <div class="scaler-form-row">
                                    <div class="scaler-form-group"><label>Local AS</label><input type="number" id="bgp-local-as" class="scaler-input" value="${isNaN(asVal) ? 65000 : asVal}"></div>
                                    <div class="scaler-form-group"><label>Peer AS</label><input type="number" id="bgp-peer-as" class="scaler-input" value="${d.peer_as || 65001}"></div>
                                </div>
                                <div id="bgp-local-as-suggestions"></div>
                                <div class="scaler-form-row" style="align-items:flex-end">
                                    <div class="scaler-form-group"><label>Peer IP Start</label><input type="text" id="bgp-peer-ip" class="scaler-input" value="${d.peer_ip_start || '10.0.0.1'}" placeholder="10.0.0.1"></div>
                                    <div class="scaler-form-group"><label>Count</label><input type="number" id="bgp-count" class="scaler-input" value="${d.count || 1}" min="1"></div>
                                    <div class="scaler-form-group"><button type="button" class="scaler-btn scaler-btn-sm" id="bgp-detect-neighbors">Detect</button></div>
                                </div>
                                <div class="scaler-form-row">
                                    <div class="scaler-form-group"><label>Peer IP Step</label><input type="number" id="bgp-peer-ip-step" class="scaler-input" value="${d.peer_ip_step ?? 1}" min="1"></div>
                                    <div class="scaler-form-group"><label>Peer AS Step</label><input type="number" id="bgp-peer-as-step" class="scaler-input" value="${d.peer_as_step ?? 0}" min="0"></div>
                                </div>
                                <div class="scaler-preview-box"><label>PREVIEW:</label><pre id="bgp-preview" class="scaler-syntax-preview">Loading...</pre></div>
                            </div>`;
                        },
                        afterRender: (d) => {
                            const asn = d.deviceContext?.config_summary?.as_number;
                            const sugg = document.getElementById('bgp-local-as-suggestions');
                            if (sugg && asn) {
                                sugg.appendChild(ScalerGUI.renderSuggestionChips([{ value: asn, label: `AS ${asn} (from config)` }], { type: 'config', onSelect: (v) => { document.getElementById('bgp-local-as').value = v; document.getElementById('bgp-local-as').dispatchEvent(new Event('input')); } }));
                            }
                            document.getElementById('bgp-detect-neighbors')?.addEventListener('click', async () => {
                                const btn = document.getElementById('bgp-detect-neighbors');
                                if (btn) { btn.disabled = true; btn.textContent = '...'; }
                                try {
                                    const ctx = d.deviceContext || {};
                                    const r = await ScalerAPI.detectBGPNeighbors({ device_id: d.deviceId, ssh_host: ctx.mgmt_ip || ctx.ip || '' });
                                    const nbrs = r?.neighbors || r?.detected || [];
                                    if (nbrs.length > 0) {
                                        const first = nbrs[0];
                                        const ip = first.ip || first.peer_ip || first.neighbor;
                                        if (ip) {
                                            document.getElementById('bgp-peer-ip').value = ip;
                                            document.getElementById('bgp-peer-ip').dispatchEvent(new Event('input'));
                                        }
                                        if (first.remote_as) document.getElementById('bgp-peer-as').value = first.remote_as;
                                        self.showNotification(`Detected ${nbrs.length} neighbor(s)`, 'info');
                                    } else {
                                        self.showNotification('No BGP neighbors detected', 'info');
                                    }
                                } catch (e) {
                                    self.showNotification(`Detect failed: ${e.message}`, 'error');
                                } finally {
                                    if (btn) { btn.disabled = false; btn.textContent = 'Detect'; }
                                }
                            });
                            let t;
                            const up = async () => {
                                clearTimeout(t);
                                t = setTimeout(async () => {
                                    try {
                                        const r = await ScalerAPI.generateBGP(ScalerGUI._collectBgpParams());
                                        const p = document.getElementById('bgp-preview');
                                        if (p) p.textContent = r.config || '(empty)';
                                    } catch (e) { const p = document.getElementById('bgp-preview'); if (p) p.textContent = e.message; }
                                }, 300);
                            };
        
                            ['bgp-local-as','bgp-peer-as','bgp-peer-ip','bgp-count','bgp-peer-ip-step','bgp-peer-as-step'].forEach(id => { const el = document.getElementById(id); if (el) el.oninput = up; });
                            up();
                        },
                        collectData: () => ({
                            local_as: parseInt(document.getElementById('bgp-local-as')?.value) || 65000,
                            peer_as: parseInt(document.getElementById('bgp-peer-as')?.value) || 65001,
                            peer_ip_start: document.getElementById('bgp-peer-ip')?.value || '10.0.0.1',
                            count: parseInt(document.getElementById('bgp-count')?.value) || 1,
                            peer_ip_step: parseInt(document.getElementById('bgp-peer-ip-step')?.value) ?? 1,
                            peer_as_step: parseInt(document.getElementById('bgp-peer-as-step')?.value) ?? 0
                        })
                    },
                    {
                        title: 'Advanced Options',
                        render: (d) => {
                            const afs = d.address_families || ['ipv4-unicast'];
                            const wan = d.deviceContext?.wan_interfaces || [];
                            const free = d.deviceContext?.interfaces?.free_physical || [];
                            const ifaces = ['loopback0'].concat(wan.filter(i => i !== 'loopback0')).concat(free.slice(0, 8)).filter((v, i, a) => a.indexOf(v) === i);
                            const afList = ['ipv4-unicast','ipv6-unicast','ipv4-vpn','ipv6-vpn','ipv4-flowspec','ipv6-flowspec','ipv4-flowspec-vpn','ipv6-flowspec-vpn'];
                            const fsAfList = ['ipv4-flowspec','ipv6-flowspec','ipv4-flowspec-vpn','ipv6-flowspec-vpn'];
                            const baseAfList = afList.filter(af => !fsAfList.includes(af));
                            const nbrs = d.deviceContext?.detected_bgp_neighbors || [];
                            const fsHint = nbrs.filter(n => n.has_v4_fs_vpn || n.has_v6_fs_vpn).map(n => {
                                const parts = [];
                                if (n.has_v4_fs_vpn) parts.push('ipv4-fs-vpn');
                                if (n.has_v6_fs_vpn) parts.push('ipv6-fs-vpn');
                                return `${n.ip} (${parts.join(', ')})`;
                            });
                            const fsHintHtml = fsHint.length ? `<div class="scaler-info-box scaler-flowspec-hint" style="margin-top:8px"><strong>FlowSpec on existing neighbors:</strong> ${fsHint.join('; ')}</div>` : '';
                            return `
                            <div class="scaler-form">
                                <div class="scaler-form-group">
                                    <label>Address Families</label>
                                    <div class="scaler-checkbox-group" id="bgp-af-group">
                                        ${baseAfList.map(af => `<label class="scaler-checkbox"><input type="checkbox" name="bgp-af" value="${af}" ${afs.includes(af) ? 'checked' : ''}> ${af}</label>`).join('')}
                                    </div>
                                </div>
                                <div class="scaler-form-group">
                                    <label>FlowSpec AFI</label>
                                    <div class="scaler-checkbox-group scaler-flowspec-af-group" id="bgp-fs-af-group">
                                        ${fsAfList.map(af => `<label class="scaler-checkbox"><input type="checkbox" name="bgp-af" value="${af}" ${afs.includes(af) ? 'checked' : ''}> ${af}</label>`).join('')}
                                    </div>
                                    ${fsHintHtml}
                                </div>
                                <div class="scaler-form-row">
                                    <div class="scaler-form-group"><label>Peer Group</label><input type="text" id="bgp-peer-group" class="scaler-input" value="${d.peer_group || ''}" placeholder="Optional"></div>
                                    <div class="scaler-form-group"><label>Update Source</label><select id="bgp-update-source" class="scaler-select"><option value="">None</option>${ifaces.map(i => `<option value="${i}" ${d.update_source === i ? 'selected' : ''}>${i}</option>`).join('')}</select></div>
                                </div>
                                <div class="scaler-form-row">
                                    <label class="scaler-checkbox"><input type="checkbox" id="bgp-rr-client" ${d.route_reflector_client ? 'checked' : ''}> Route Reflector Client</label>
                                    <label class="scaler-checkbox"><input type="checkbox" id="bgp-bfd" ${d.bfd ? 'checked' : ''}> BFD</label>
                                </div>
                                <div class="scaler-form-row">
                                    <div class="scaler-form-group"><label>eBGP Multihop (TTL)</label><input type="number" id="bgp-ebgp-multihop" class="scaler-input" value="${d.ebgp_multihop || ''}" placeholder="Leave empty for iBGP" min="1" max="255"></div>
                                    <div class="scaler-form-group"><label>Description</label><input type="text" id="bgp-description" class="scaler-input" value="${d.description || ''}" placeholder="Optional"></div>
                                </div>
                                <div class="scaler-form-row">
                                    <div class="scaler-form-group"><label>Hold Time</label><input type="number" id="bgp-hold-time" class="scaler-input" value="${d.hold_time || ''}" placeholder="Default" min="0"></div>
                                    <div class="scaler-form-group"><label>Keepalive</label><input type="number" id="bgp-keepalive" class="scaler-input" value="${d.keepalive || ''}" placeholder="Default" min="0"></div>
                                </div>
                                <div class="scaler-form-group"><label>Password (MD5)</label><input type="password" id="bgp-password" class="scaler-input" value="${d.password || ''}" placeholder="Optional" autocomplete="off"></div>
                                <div class="scaler-preview-box"><label>PREVIEW:</label><pre id="bgp-adv-preview" class="scaler-syntax-preview">Loading...</pre></div>
                            </div>`;
                        },
                        afterRender: (d) => {
                            let t;
                            const up = async () => {
                                clearTimeout(t);
                                t = setTimeout(async () => {
                                    try {
                                        const r = await ScalerAPI.generateBGP(ScalerGUI._collectBgpParams());
                                        const p = document.getElementById('bgp-adv-preview');
                                        if (p) p.textContent = r.config || '(empty)';
                                    } catch (e) { const p = document.getElementById('bgp-adv-preview'); if (p) p.textContent = e.message; }
                                }, 300);
                            };
                            document.querySelectorAll('input[name="bgp-af"], #bgp-peer-group, #bgp-update-source, #bgp-rr-client, #bgp-bfd, #bgp-ebgp-multihop, #bgp-description, #bgp-hold-time, #bgp-keepalive, #bgp-password').forEach(el => { if (el) el.addEventListener('input', up); el.addEventListener('change', up); });
                            up();
                        },
                        collectData: () => {
                            const afEls = document.querySelectorAll('input[name="bgp-af"]:checked');
                            const afs = Array.from(afEls).map(e => e.value);
                            const ebgp = document.getElementById('bgp-ebgp-multihop')?.value;
                            const ht = document.getElementById('bgp-hold-time')?.value;
                            const ka = document.getElementById('bgp-keepalive')?.value;
                            return {
                                address_families: afs.length ? afs : ['ipv4-unicast'],
                                peer_group: document.getElementById('bgp-peer-group')?.value || undefined,
                                update_source: document.getElementById('bgp-update-source')?.value || undefined,
                                route_reflector_client: document.getElementById('bgp-rr-client')?.checked || false,
                                bfd: document.getElementById('bgp-bfd')?.checked || false,
                                ebgp_multihop: ebgp ? parseInt(ebgp) : undefined,
                                hold_time: ht ? parseInt(ht) : undefined,
                                keepalive: ka ? parseInt(ka) : undefined,
                                description: document.getElementById('bgp-description')?.value || undefined,
                                password: document.getElementById('bgp-password')?.value || undefined
                            };
                        }
                    },
                    {
                        title: 'Review',
                        render: (d) => `
                            <div class="scaler-form">
                                <table class="scaler-review-table">
                                    <tr><td>Device</td><td>${d.deviceId}</td></tr>
                                    <tr><td>Local AS</td><td>${d.local_as}</td></tr>
                                    <tr><td>Peer AS</td><td>${d.peer_as}</td></tr>
                                    <tr><td>Peer IP</td><td>${d.peer_ip_start}</td></tr>
                                    <tr><td>Count</td><td>${d.count}</td></tr>
                                </table>
                                <div class="scaler-preview-box"><label>GENERATED CONFIG:</label>
                                    <pre id="bgp-review-config" class="scaler-syntax-preview">Generating...</pre>
                                </div>
                                <div id="config-validation"></div>
                                <div id="whats-next-container"></div>
                            </div>`,
                        afterRender: async (d) => {
                            try {
                                const params = {
                                    local_as: d.local_as, peer_as: d.peer_as,
                                    peer_ip_start: d.peer_ip_start, count: d.count,
                                    peer_ip_step: d.peer_ip_step ?? 1, peer_as_step: d.peer_as_step ?? 0,
                                    address_families: d.address_families || ['ipv4-unicast'],
                                    peer_group: d.peer_group, update_source: d.update_source,
                                    route_reflector_client: d.route_reflector_client, bfd: d.bfd,
                                    ebgp_multihop: d.ebgp_multihop, hold_time: d.hold_time, keepalive: d.keepalive,
                                    description: d.description, password: d.password
                                };
                                const r = await ScalerAPI.generateBGP(params);
                                const el = document.getElementById('bgp-review-config');
                                if (el) el.textContent = r.config || '(empty)';
                                ScalerGUI.WizardController.data.generatedConfig = r.config;
                                try {
                                    const val = await ScalerAPI.validateConfig({ config: r.config, hierarchy: 'bgp' });
                                    const vEl = document.getElementById('config-validation');
                                    if (vEl) vEl.innerHTML = ScalerGUI._renderValidationResults(val.errors, val.warnings, val.suggestions);
                                } catch (e) { console.warn('[ScalerGUI] validation display error:', e.message); }
                                const container = document.getElementById('whats-next-container');
                                if (container) {
                                    const createdData = { deviceId: d.deviceId, bgp: { peer_ip: d.peer_ip_start, local_as: d.local_as } };
                                    const section = await ScalerGUI._renderWhatsNextSection('bgp', d, createdData, r.config);
                                    if (section) { container.innerHTML = ''; container.appendChild(section); }
                                }
                            } catch (e) {
                                const el = document.getElementById('bgp-review-config');
                                if (el) el.textContent = `Error: ${e.message}`;
                            }
                        }
                    },
                    ScalerGUI._buildDecisionStep({
                        wizardType: 'bgp',
                        getCreatedData: (d) => ({ deviceId: d.deviceId, bgp: { peer_ip: d.peer_ip_start, local_as: d.local_as } })
                    }),
                    ScalerGUI._buildPushStep({
                        radioName: 'bgp-push-mode',
                        includeClipboard: true,
                        infoText: (d) => `<strong>Config:</strong> ${d.count} BGP peer${d.count > 1 ? 's' : ''}, AS ${d.peer_as}`
                    })
                ],
                onComplete: async (data) => {
                    if (data.pushMode === 'clipboard') {
                        const config = data.generatedConfig || '';
                        try { await window.safeClipboardWrite(config); } catch (_) {}
                        const ctx = data.deviceContext || {};
                        const host = ctx.mgmt_ip || ctx.ip || '';
                        if (host) window.open(`ssh://dnroot@${host}`, '_blank');
                        this.showNotification(
                            `Config copied (${config.split('\n').length} lines).${host ? ' Opening SSH...' : ''}`,
                            'success', 6000
                        );
                        this.closePanel('bgp-wizard');
                        return;
                    }
                    try {
                        const ctx = data.deviceContext || {};
                        const jobName = `${data.count} BGP peer${data.count > 1 ? 's' : ''} on ${data.deviceId}`;
                        const result = await ScalerAPI.pushConfig({
                            device_id: data.deviceId,
                            config: data.generatedConfig,
                            hierarchy: 'bgp',
                            mode: 'merge',
                            dry_run: data.dryRun,
                            push_method: data.push_method || 'terminal_paste',
                            load_mode: data.load_mode || 'merge',
                            ssh_host: ctx.mgmt_ip || ctx.ip || '',
                            job_name: jobName
                        });
                        this.closePanel('bgp-wizard');
                        this.recordWizardChange(data.deviceId, 'bgp', { peerIp: data.peer_ip_start, asn: data.local_as, dryRun: data.dryRun }, {
                            params: { ...data },
                            generatedConfig: data.generatedConfig,
                            pushMode: data.pushMode || (data.dryRun ? 'dry_run' : 'commit'),
                            jobId: result.job_id,
                        });
                        const modeLabel = data.dryRun ? 'Commit Check' : 'Commit';
                        this.showProgress(result.job_id, `${modeLabel}: BGP on ${data.deviceId}`, {
                            device_id: data.deviceId,
                            onComplete: (success, res) => {
                                this.updateWizardRunResult(result.job_id, success);
                                if (!success && !res?.cancelled) {
                                    this.showNotification(`Push failed on ${data.deviceId}`, 'error', 10000);
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
                        const s = c?.config_summary || {};
                        self.WizardController.data.deviceContext = c;
                        if (s.as_number) self.WizardController.data.local_as = parseInt(s.as_number, 10) || 65000;
                        self.WizardController.render();
                    }
                }).catch(e => console.warn('[ScalerGUI] wizard operation failed:', e.message));
            }
        },
        async openIGPWizard(deviceId = null, prefillParams = null) {
            if (!deviceId) { this.openDeviceSelector('IGP Configuration', (id) => this.openIGPWizard(id, prefillParams)); return; }
            if (!this._isDeviceConfigurable(deviceId)) return;
            const content = document.createElement('div');
            content.innerHTML = '<div class="scaler-loading">Loading...</div>';
            this.openPanel('igp-wizard', `IGP Wizard - ${deviceId}`, content, { width: '540px', parentPanel: 'scaler-menu' });
            const self = this;
            const cachedCtx = this._deviceContexts[deviceId];
            const hasFresh = cachedCtx && (Date.now() - (cachedCtx._fetchedAt || 0)) < this._contextCacheTTL;
            let ctx = hasFresh ? this._applyPendingChanges(deviceId, cachedCtx) : null;
            const igp = ctx?.igp || {};
            const wan = ctx?.wan_interfaces || [];
            const protocol = igp.protocol || 'isis';
            this.WizardController.init({
                panelName: 'igp-wizard',
                quickNavKey: 'igp-wizard',
                title: `IGP Wizard - ${deviceId}`,
                initialData: { deviceId, deviceContext: ctx, protocol, area_id: igp.area || '49.0001', interfaces: wan.length ? wan : ['loopback0'], ...(prefillParams || {}) },
                lastRunWizardType: 'igp',
                onLastRunRerun: (rec) => self._handleLastRunAction(rec, deviceId, ctx),
                onLastRunRerunOther: (rec) => {
                    self.closePanel('igp-wizard');
                    self.openMirrorWizard(rec.deviceId);
                },
                wizardHeader: (data) => self.renderContextPanel(deviceId, data.deviceContext || {}, { wizardType: 'igp', onRefresh: () => self.refreshDeviceContextLive(deviceId).then(c => { self.WizardController.data.deviceContext = c; self.WizardController.render(); }) }),
                steps: [
                    {
                        title: 'Protocol',
                        render: (d) => {
                            const prot = d.protocol || d.deviceContext?.igp?.protocol || 'isis';
                            const area = d.area_id || d.deviceContext?.igp?.area || '49.0001';
                            const routerIp = d.router_ip || d.deviceContext?.config_summary?.loopback0_ip || d.deviceContext?.config_summary?.router_id || '1.1.1.1';
                            const ifaces = (d.interfaces || d.deviceContext?.wan_interfaces || ['loopback0']).join(', ');
                            const lvl = d.level || 'level-1-2';
                            return `
                            <div class="scaler-form">
                                <div class="scaler-form-group"><label>Protocol</label><select id="igp-protocol" class="scaler-select"><option value="isis" ${prot === 'isis' ? 'selected' : ''}>ISIS</option><option value="ospf" ${prot === 'ospf' ? 'selected' : ''}>OSPF</option></select></div>
                                <div id="igp-isis-level-row" class="scaler-form-group" style="display:${prot === 'isis' ? 'block' : 'none'}">
                                    <label>ISIS Level</label>
                                    <select id="igp-level" class="scaler-select">
                                        <option value="level-1-2" ${lvl === 'level-1-2' ? 'selected' : ''}>Level 1-2 (both)</option>
                                        <option value="level-1" ${lvl === 'level-1' ? 'selected' : ''}>Level 1 only</option>
                                        <option value="level-2" ${lvl === 'level-2' ? 'selected' : ''}>Level 2 only</option>
                                    </select>
                                </div>
                                <div class="scaler-form-group"><label>Area ID</label><input type="text" id="igp-area" class="scaler-input" value="${area}"></div>
                                <div class="scaler-form-group"><label>Router IP</label><input type="text" id="igp-router-ip" class="scaler-input" value="${routerIp}" placeholder="e.g. 1.1.1.1 (lo0)"></div>
                                <div id="igp-isis-net-row" class="scaler-form-group" style="display:${prot === 'isis' ? 'block' : 'none'}">
                                    <label>ISIS NET (auto-generated)</label>
                                    <div class="scaler-info-box" style="font-family:monospace;font-size:12px;padding:8px" id="igp-isis-net-display">${ScalerGUI.ipToIsisNet(routerIp, area)}</div>
                                    <div class="scaler-info-box" style="font-size:10px;margin-top:4px;color:rgba(255,255,255,0.6)">Derived from Router IP. Used for ISIS system-id.</div>
                                </div>
                                <div class="scaler-form-group"><label>Interfaces (comma-separated)</label><input type="text" id="igp-ifaces" class="scaler-input" value="${ifaces}" placeholder="loopback0, ge100-0/0/0"></div>
                                <div id="igp-ifaces-suggestions"></div>
                                <div class="scaler-form-row">
                                    <label class="scaler-checkbox"><input type="checkbox" id="igp-passive" ${d.passive_for_all ? 'checked' : ''}> Passive (all interfaces)</label>
                                    <div class="scaler-form-group" style="flex:1;max-width:120px"><label>Default Metric</label><input type="number" id="igp-metric" class="scaler-input" value="${d.default_metric || ''}" placeholder="Optional" min="1"></div>
                                </div>
                                <div class="scaler-form-group" style="margin-top:8px">
                                    <label class="scaler-checkbox" title="Override passive, metric, or circuit-type per interface"><input type="checkbox" id="igp-per-iface-toggle" ${d.interfaceOptions && Object.keys(d.interfaceOptions).length ? 'checked' : ''}> Per-interface overrides</label>
                                </div>
                                <div id="igp-per-iface-section" style="display:${d.interfaceOptions && Object.keys(d.interfaceOptions).length ? 'block' : 'none'};margin-top:4px">
                                    <div id="igp-per-iface-rows" class="scaler-form" style="font-size:11px;max-height:200px;overflow-y:auto"></div>
                                </div>
                                <div class="scaler-preview-box"><label>PREVIEW:</label><pre id="igp-preview" class="scaler-syntax-preview">Loading...</pre></div>
                            </div>`;
                        },
                        afterRender: (d) => {
                            const wan = d.deviceContext?.wan_interfaces || [];
                            const sugg = document.getElementById('igp-ifaces-suggestions');
                            if (sugg && wan.length) {
                                const chips = wan.map(w => ({ value: w, label: w }));
                                sugg.appendChild(ScalerGUI.renderSuggestionChips(chips, { type: 'config', label: 'WAN interfaces:', onSelect: (v) => {
                                    const input = document.getElementById('igp-ifaces');
                                    const cur = (input.value || '').split(',').map(s => s.trim()).filter(Boolean);
                                    if (!cur.includes(v)) cur.push(v);
                                    input.value = cur.join(', ');
                                    input.dispatchEvent(new Event('input'));
                                } }));
                            }
                            const updateNetDisplay = () => {
                                const netEl = document.getElementById('igp-isis-net-display');
                                const netRow = document.getElementById('igp-isis-net-row');
                                const prot = document.getElementById('igp-protocol')?.value || 'isis';
                                if (netRow) netRow.style.display = prot === 'isis' ? 'block' : 'none';
                                if (netEl && prot === 'isis') {
                                    const area = document.getElementById('igp-area')?.value || '49.0001';
                                    const rip = document.getElementById('igp-router-ip')?.value || '1.1.1.1';
                                    netEl.textContent = ScalerGUI.ipToIsisNet(rip, area);
                                }
                            };
                            document.getElementById('igp-protocol')?.addEventListener('change', (e) => {
                                const row = document.getElementById('igp-isis-level-row');
                                if (row) row.style.display = e.target.value === 'isis' ? 'block' : 'none';
                                updateNetDisplay();
                            });
                            let t;
                            const up = async () => {
                                updateNetDisplay();
                                clearTimeout(t);
                                t = setTimeout(async () => {
                                    try {
                                        const prot = document.getElementById('igp-protocol')?.value || 'isis';
                                        const ifaces = (document.getElementById('igp-ifaces')?.value || '').split(',').map(s => s.trim()).filter(Boolean);
                                        const ifOpts = {};
                                        if (document.getElementById('igp-per-iface-toggle')?.checked) {
                                            document.querySelectorAll('.igp-iface-passive').forEach(cb => { if (cb.checked) { if (!ifOpts[cb.dataset.iface]) ifOpts[cb.dataset.iface] = {}; ifOpts[cb.dataset.iface].passive = true; } });
                                            document.querySelectorAll('.igp-iface-metric').forEach(inp => { const v = parseInt(inp.value); if (v > 0) { if (!ifOpts[inp.dataset.iface]) ifOpts[inp.dataset.iface] = {}; ifOpts[inp.dataset.iface].metric = v; } });
                                            document.querySelectorAll('.igp-iface-circuit').forEach(sel => { if (sel.value) { if (!ifOpts[sel.dataset.iface]) ifOpts[sel.dataset.iface] = {}; ifOpts[sel.dataset.iface].circuit_type = sel.value; } });
                                        }
                                        const params = {
                                            protocol: prot,
                                            area_id: document.getElementById('igp-area')?.value || '49.0001',
                                            router_ip: document.getElementById('igp-router-ip')?.value || '1.1.1.1',
                                            interfaces: ifaces.length ? ifaces : ['loopback0'],
                                            passive_for_all: document.getElementById('igp-passive')?.checked || false,
                                            default_metric: document.getElementById('igp-metric')?.value || undefined,
                                            interface_options: Object.keys(ifOpts).length ? ifOpts : undefined
                                        };
                                        if (prot === 'isis') params.level = document.getElementById('igp-level')?.value || 'level-1-2';
                                        const r = await ScalerAPI.generateIGP(params);
                                        const p = document.getElementById('igp-preview');
                                        if (p) p.textContent = r.config || '(empty)';
                                    } catch (e) { const p = document.getElementById('igp-preview'); if (p) p.textContent = e.message; }
                                }, 300);
                            };
        
                            const buildPerIfaceRows = () => {
                                const container = document.getElementById('igp-per-iface-rows');
                                if (!container) return;
                                const ifaces = (document.getElementById('igp-ifaces')?.value || '').split(',').map(s => s.trim()).filter(Boolean);
                                const prot = document.getElementById('igp-protocol')?.value || 'isis';
                                const prevOpts = self.WizardController.data.interfaceOptions || {};
                                container.innerHTML = ifaces.length ? ifaces.map(iface => {
                                    const o = prevOpts[iface] || {};
                                    const circuitRow = prot === 'isis' ? `<select class="scaler-input igp-iface-circuit" data-iface="${iface}" style="width:80px" title="ISIS circuit-type override"><option value="">Default</option><option value="point-to-point" ${o.circuit_type === 'point-to-point' ? 'selected' : ''}>P2P</option><option value="broadcast" ${o.circuit_type === 'broadcast' ? 'selected' : ''}>Bcast</option></select>` : '';
                                    return `<div style="display:flex;align-items:center;gap:6px;padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.06)">
                                        <span style="flex:1;min-width:100px;font-family:monospace">${iface}</span>
                                        <label style="white-space:nowrap" title="Mark this interface passive"><input type="checkbox" class="igp-iface-passive" data-iface="${iface}" ${o.passive ? 'checked' : ''}> Passive</label>
                                        <input type="number" class="scaler-input igp-iface-metric" data-iface="${iface}" placeholder="Metric" min="1" value="${o.metric || ''}" style="width:60px" title="Override metric for this interface">
                                        ${circuitRow}
                                    </div>`;
                                }).join('') : '<div style="color:rgba(255,255,255,0.4);padding:8px">Add interfaces above first</div>';
                            };
                            document.getElementById('igp-per-iface-toggle')?.addEventListener('change', (e) => {
                                const sec = document.getElementById('igp-per-iface-section');
                                if (sec) sec.style.display = e.target.checked ? 'block' : 'none';
                                if (e.target.checked) buildPerIfaceRows();
                            });
                            document.getElementById('igp-ifaces')?.addEventListener('input', () => {
                                if (document.getElementById('igp-per-iface-toggle')?.checked) buildPerIfaceRows();
                            });
                            if (document.getElementById('igp-per-iface-toggle')?.checked) buildPerIfaceRows();
        
                            ['igp-protocol','igp-level','igp-area','igp-router-ip','igp-ifaces','igp-passive','igp-metric'].forEach(id => { const el = document.getElementById(id); if (el) el.oninput = up; el && (el.onchange = up); });
                            up();
                        },
                        collectData: () => {
                            const prot = document.getElementById('igp-protocol')?.value || 'isis';
                            const interfaceOptions = {};
                            if (document.getElementById('igp-per-iface-toggle')?.checked) {
                                document.querySelectorAll('.igp-iface-passive').forEach(cb => {
                                    const iface = cb.dataset.iface;
                                    if (!interfaceOptions[iface]) interfaceOptions[iface] = {};
                                    if (cb.checked) interfaceOptions[iface].passive = true;
                                });
                                document.querySelectorAll('.igp-iface-metric').forEach(inp => {
                                    const iface = inp.dataset.iface;
                                    const val = parseInt(inp.value);
                                    if (val > 0) {
                                        if (!interfaceOptions[iface]) interfaceOptions[iface] = {};
                                        interfaceOptions[iface].metric = val;
                                    }
                                });
                                document.querySelectorAll('.igp-iface-circuit').forEach(sel => {
                                    const iface = sel.dataset.iface;
                                    if (sel.value) {
                                        if (!interfaceOptions[iface]) interfaceOptions[iface] = {};
                                        interfaceOptions[iface].circuit_type = sel.value;
                                    }
                                });
                            }
                            return {
                                protocol: prot,
                                area_id: document.getElementById('igp-area')?.value || '49.0001',
                                router_ip: document.getElementById('igp-router-ip')?.value || '1.1.1.1',
                                interfaces: (document.getElementById('igp-ifaces')?.value || '').split(',').map(s => s.trim()).filter(Boolean) || ['loopback0'],
                                level: prot === 'isis' ? (document.getElementById('igp-level')?.value || 'level-1-2') : undefined,
                                passive_for_all: document.getElementById('igp-passive')?.checked || false,
                                default_metric: document.getElementById('igp-metric')?.value || undefined,
                                interfaceOptions: Object.keys(interfaceOptions).length ? interfaceOptions : undefined
                            };
                        }
                    },
                    {
                        title: 'Review',
                        render: (d) => `
                            <div class="scaler-form">
                                <table class="scaler-review-table">
                                    <tr><td>Device</td><td>${d.deviceId}</td></tr>
                                    <tr><td>Protocol</td><td><strong>${(d.protocol || 'isis').toUpperCase()}</strong></td></tr>
                                    <tr><td>Area</td><td>${d.area_id || '49.0001'}</td></tr>
                                    <tr><td>Router IP</td><td>${d.router_ip || '1.1.1.1'}</td></tr>
                                    <tr><td>Interfaces</td><td>${(d.interfaces || []).join(', ')}</td></tr>
                                </table>
                                <div class="scaler-preview-box"><label>GENERATED CONFIG:</label>
                                    <pre id="igp-review-config" class="scaler-syntax-preview">Generating...</pre>
                                </div>
                                <div id="config-validation"></div>
                                <div id="whats-next-container"></div>
                            </div>`,
                        afterRender: async (d) => {
                            try {
                                const params = {
                                    protocol: d.protocol, area_id: d.area_id,
                                    router_ip: d.router_ip, interfaces: d.interfaces,
                                    passive_for_all: d.passive_for_all, default_metric: d.default_metric
                                };
                                if (d.protocol === 'isis') params.level = d.level || 'level-1-2';
                                const r = await ScalerAPI.generateIGP(params);
                                const el = document.getElementById('igp-review-config');
                                if (el) el.textContent = r.config || '(empty)';
                                ScalerGUI.WizardController.data.generatedConfig = r.config;
                                try {
                                    const val = await ScalerAPI.validateConfig({ config: r.config, hierarchy: 'igp' });
                                    const vEl = document.getElementById('config-validation');
                                    if (vEl) vEl.innerHTML = ScalerGUI._renderValidationResults(val.errors, val.warnings, val.suggestions);
                                } catch (e) { console.warn('[ScalerGUI] validation display error:', e.message); }
                                const container = document.getElementById('whats-next-container');
                                if (container) {
                                    const createdData = { deviceId: d.deviceId, interfaces: d.interfaces || [], loopback_ip: d.router_ip };
                                    const section = await ScalerGUI._renderWhatsNextSection('igp', d, createdData, r.config);
                                    if (section) { container.innerHTML = ''; container.appendChild(section); }
                                }
                            } catch (e) {
                                const el = document.getElementById('igp-review-config');
                                if (el) el.textContent = `Error: ${e.message}`;
                            }
                        }
                    },
                    ScalerGUI._buildDecisionStep({
                        wizardType: 'igp',
                        getCreatedData: (d) => ({ deviceId: d.deviceId, interfaces: d.interfaces || [], loopback_ip: d.router_ip })
                    }),
                    ScalerGUI._buildPushStep({
                        radioName: 'igp-push-mode',
                        includeClipboard: true,
                        infoText: (d) => `<strong>Config:</strong> ${(d.protocol || 'isis').toUpperCase()} on ${(d.interfaces || []).length} interface${(d.interfaces || []).length > 1 ? 's' : ''}`
                    })
                ],
                onComplete: async (data) => {
                    if (data.pushMode === 'clipboard') {
                        const config = data.generatedConfig || '';
                        try { await window.safeClipboardWrite(config); } catch (_) {}
                        const ctx = data.deviceContext || {};
                        const host = ctx.mgmt_ip || ctx.ip || '';
                        if (host) window.open(`ssh://dnroot@${host}`, '_blank');
                        this.showNotification(
                            `Config copied (${config.split('\n').length} lines).${host ? ' Opening SSH...' : ''}`,
                            'success', 6000
                        );
                        this.closePanel('igp-wizard');
                        return;
                    }
                    try {
                        const ctx = data.deviceContext || {};
                        const prot = (data.protocol || 'isis').toUpperCase();
                        const jobName = `${prot} on ${data.deviceId}`;
                        const result = await ScalerAPI.pushConfig({
                            device_id: data.deviceId,
                            config: data.generatedConfig,
                            hierarchy: 'igp',
                            mode: 'merge',
                            dry_run: data.dryRun,
                            push_method: data.push_method || 'terminal_paste',
                            load_mode: data.load_mode || 'merge',
                            ssh_host: ctx.mgmt_ip || ctx.ip || '',
                            job_name: jobName
                        });
                        this.closePanel('igp-wizard');
                        this.recordWizardChange(data.deviceId, 'igp', { protocol: data.protocol, area: data.area_id, dryRun: data.dryRun }, {
                            params: { ...data },
                            generatedConfig: data.generatedConfig,
                            pushMode: data.pushMode || (data.dryRun ? 'dry_run' : 'commit'),
                            jobId: result.job_id,
                        });
                        const modeLabel = data.dryRun ? 'Commit Check' : 'Commit';
                        this.showProgress(result.job_id, `${modeLabel}: ${prot} on ${data.deviceId}`, {
                            device_id: data.deviceId,
                            onComplete: (success, res) => {
                                this.updateWizardRunResult(result.job_id, success);
                                if (!success && !res?.cancelled) {
                                    this.showNotification(`Push failed on ${data.deviceId}`, 'error', 10000);
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

    });
})(window.ScalerGUI);
