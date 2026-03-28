/**
 * ScalerGUI: XRAY, FlowSpec, FlowSpec VPN, system, mirror wizards
 * @requires scaler-api.js
 * @requires scaler-gui.js (core)
 */
(function (G) {
    'use strict';
    if (!G) {
        console.error('[scaler-gui-wizards-security.js] ScalerGUI core not loaded');
        return;
    }
    Object.assign(G, {
        openXraySettings() {
            const content = document.createElement('div');
            content.innerHTML = '<div class="scaler-loading">Loading XRAY config...</div>';
            this.openPanel('xray-settings', 'XRAY Settings', content, { width: '360px' });
        
            fetch((typeof ScalerAPI !== 'undefined' && ScalerAPI._api ? ScalerAPI._api('/api/xray/config') : '/api/xray/config')).then(r => r.json()).then(cfg => {
                const mac = cfg.mac || {};
                const creds = cfg.credentials || {};
                const isDark = document.body.classList.contains('dark-mode');
                const inputBg = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)';
                const inputBorder = isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.1)';
                const inputColor = isDark ? '#e0e6ed' : '#1a1a1a';
        
                const fieldRow = (label, id, val, type='text') => `
                    <div style="margin-bottom: 10px;">
                        <label style="font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.6; display: block; margin-bottom: 3px;">${label}</label>
                        <input id="${id}" type="${type}" value="${val || ''}" style="width: 100%; padding: 7px 10px; border-radius: 6px; border: 1px solid ${inputBorder}; background: ${inputBg}; color: ${inputColor}; font-size: 12px; font-family: 'Poppins', sans-serif; box-sizing: border-box;">
                    </div>`;
        
                content.innerHTML = `
                    <div style="font-size: 11px; opacity: 0.6; margin-bottom: 14px;">Configure Mac delivery, device credentials, and Wireshark path for XRAY captures.</div>
                    <div style="border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 12px; margin-bottom: 12px;">
                        <h4 style="font-size: 12px; font-weight: 700; margin-bottom: 10px; color: #0066FA;">Mac Configuration</h4>
                        ${fieldRow('Mac IP (VPN)', 'xray-mac-ip-vpn', mac.ip_vpn)}
                        ${fieldRow('Mac IP (Office)', 'xray-mac-ip-office', mac.ip_office)}
                        ${fieldRow('Mac Username', 'xray-mac-user', mac.user)}
                        ${fieldRow('Mac Password', 'xray-mac-pass', mac.password, 'password')}
                        ${fieldRow('Wireshark Path', 'xray-wireshark-path', mac.wireshark_path)}
                        ${fieldRow('pcap Directory', 'xray-pcap-dir', mac.pcap_directory)}
                        <button id="xray-verify-mac" style="width: 100%; padding: 7px; border-radius: 6px; border: 1px solid #0066FA; background: rgba(0,102,250,0.1); color: #0066FA; cursor: pointer; font-size: 11px; font-weight: 600; font-family: 'Poppins', sans-serif; margin-top: 4px;">Verify Mac Connection</button>
                        <div id="xray-mac-status" style="font-size: 10px; margin-top: 4px; min-height: 14px;"></div>
                    </div>
                    <div style="border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 12px; margin-bottom: 12px;">
                        <h4 style="font-size: 12px; font-weight: 700; margin-bottom: 10px; color: #FF5E1F;">Device Credentials</h4>
                        ${fieldRow('SSH Username', 'xray-dev-user', creds.device_user)}
                        ${fieldRow('SSH Password', 'xray-dev-pass', creds.device_password, 'password')}
                    </div>
                    <div style="margin-bottom: 16px;">
                        <h4 style="font-size: 12px; font-weight: 700; margin-bottom: 10px; color: #27ae60;">Arista Credentials</h4>
                        ${fieldRow('SSH Username', 'xray-arista-user', creds.arista_user)}
                        ${fieldRow('SSH Password', 'xray-arista-pass', creds.arista_password, 'password')}
                    </div>
                    <button id="xray-save-settings" style="width: 100%; padding: 10px; border-radius: 8px; border: none; background: linear-gradient(135deg, #0066FA, #0052CC); color: #fff; font-size: 13px; font-weight: 700; cursor: pointer; font-family: 'Poppins', sans-serif;">Save Settings</button>
                    <div id="xray-save-status" style="font-size: 10px; text-align: center; margin-top: 6px; min-height: 14px;"></div>
                `;
        
                content.querySelector('#xray-save-settings').onclick = () => {
                    const updated = {
                        mac: {
                            ip_vpn: content.querySelector('#xray-mac-ip-vpn').value || null,
                            ip_office: content.querySelector('#xray-mac-ip-office').value || null,
                            user: content.querySelector('#xray-mac-user').value || null,
                            password: content.querySelector('#xray-mac-pass').value || null,
                            wireshark_path: content.querySelector('#xray-wireshark-path').value || null,
                            pcap_directory: content.querySelector('#xray-pcap-dir').value || null
                        },
                        credentials: {
                            device_user: content.querySelector('#xray-dev-user').value || null,
                            device_password: content.querySelector('#xray-dev-pass').value || null,
                            arista_user: content.querySelector('#xray-arista-user').value || null,
                            arista_password: content.querySelector('#xray-arista-pass').value || null
                        }
                    };
                    const statusEl = content.querySelector('#xray-save-status');
                    fetch((typeof ScalerAPI !== 'undefined' && ScalerAPI._api ? ScalerAPI._api('/api/xray/config') : '/api/xray/config'), {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(updated)
                    }).then(r => r.json()).then(res => {
                        statusEl.style.color = '#27ae60';
                        statusEl.textContent = 'Settings saved.';
                        setTimeout(() => { statusEl.textContent = ''; }, 3000);
                    }).catch(e => {
                        statusEl.style.color = '#e74c3c';
                        statusEl.textContent = 'Save failed: ' + e.message;
                    });
                };
        
                content.querySelector('#xray-verify-mac').onclick = () => {
                    const ip = content.querySelector('#xray-mac-ip-vpn').value;
                    const user = content.querySelector('#xray-mac-user').value;
                    const statusEl = content.querySelector('#xray-mac-status');
                    if (!ip || !user) { statusEl.style.color = '#e74c3c'; statusEl.textContent = 'Need IP and username'; return; }
                    statusEl.style.color = '#0066FA';
                    statusEl.textContent = 'Verifying...';
                    fetch((typeof ScalerAPI !== 'undefined' && ScalerAPI._api ? ScalerAPI._api('/api/xray/verify-mac') : '/api/xray/verify-mac'), {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ ip, user })
                    }).then(r => r.json()).then(res => {
                        if (res.reachable) {
                            statusEl.style.color = '#27ae60';
                            statusEl.textContent = 'Mac reachable — connection verified.';
                        } else {
                            statusEl.style.color = '#e74c3c';
                            statusEl.textContent = 'Mac not reachable. Check IP/credentials.';
                        }
                    }).catch(e => {
                        statusEl.style.color = '#e74c3c';
                        statusEl.textContent = 'Verify failed: ' + e.message;
                    });
                };
            }).catch(e => {
                content.innerHTML = `<div style="color: #e74c3c; padding: 20px;">Failed to load XRAY config: ${e.message}</div>`;
            });
        },
        async openFlowSpecWizard(deviceId = null, prefillParams = null) {
            if (!deviceId) {
                this.openDeviceSelector('FlowSpec Wizard', (id) => this.openFlowSpecWizard(id, prefillParams));
                return;
            }
            if (!this._isDeviceConfigurable(deviceId)) return;
            const content = document.createElement('div');
            content.className = 'scaler-wizard-container';
            content.innerHTML = '<div class="scaler-loading">Loading...</div>';
            this.openPanel('flowspec-wizard', `FlowSpec Local - ${deviceId}`, content, {
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
            const existingPolicies = ctx?.flowspec_policies || [];
            const nextMc = (existingPolicies.length || 0) + 1;
            ScalerGUI.WizardController.init({
                panelName: 'flowspec-wizard',
                quickNavKey: 'flowspec-wizard',
                title: 'FlowSpec Local Policies',
                initialData: {
                    deviceId,
                    deviceContext: ctx,
                    policyName: 'POL-FS-1',
                    ...(prefillParams || {}),
                    matchClassName: `MC-${nextMc}`,
                    destIp: '10.0.0.0/24',
                    destPort: '',
                    protocol: '6',
                    action: 'drop',
                    rateBps: 1000000,
                    includeIpv4: true,
                    includeIpv6: false
                },
                lastRunWizardType: 'flowspec',
                onLastRunRerun: (rec) => self._handleLastRunAction(rec, deviceId, ctx),
                onLastRunRerunOther: (rec) => {
                    self.closePanel('flowspec-wizard');
                    self.openMirrorWizard(rec.deviceId);
                },
                steps: [
                    {
                        title: 'FlowSpec Option',
                        render: (d) => {
                            const sel = d.flowspecOption || 'local';
                            return `<div class="scaler-form">
                                <div class="scaler-info-box">Choose FlowSpec configuration type.</div>
                                <div class="scaler-flowspec-options">
                                    <label class="scaler-flowspec-option"><input type="radio" name="fs-option" value="local" ${sel === 'local' ? 'checked' : ''}>
                                        <span class="fs-opt-title">Local Policies</span>
                                        <span class="fs-opt-desc">Define static protection rules (IPv4/IPv6)</span>
                                    </label>
                                    <label class="scaler-flowspec-option"><input type="radio" name="fs-option" value="bgp-afi">
                                        <span class="fs-opt-title">BGP FlowSpec AFI</span>
                                        <span class="fs-opt-desc">Configure SAFI 133/134 on neighbors</span>
                                    </label>
                                    <label class="scaler-flowspec-option"><input type="radio" name="fs-option" value="interface">
                                        <span class="fs-opt-title">Interface FlowSpec</span>
                                        <span class="fs-opt-desc">Enable on WAN interfaces</span>
                                    </label>
                                    <label class="scaler-flowspec-option"><input type="radio" name="fs-option" value="vrf-afi">
                                        <span class="fs-opt-title">VRF FlowSpec AFI</span>
                                        <span class="fs-opt-desc">Configure FlowSpec in VRFs (FS-VPN)</span>
                                    </label>
                                    <label class="scaler-flowspec-option"><input type="radio" name="fs-option" value="dependency">
                                        <span class="fs-opt-title">Dependency Check</span>
                                        <span class="fs-opt-desc">Full report with fix commands</span>
                                    </label>
                                </div>
                            </div>`;
                        },
                        collectData: () => ({
                            flowspecOption: document.querySelector('input[name="fs-option"]:checked')?.value || 'local'
                        })
                    },
                    {
                        title: 'Dependency Check',
                        render: (d) => {
                            const result = d._flowspecDependencyResult || null;
                            if (!result) {
                                return `<div class="scaler-form">
                                    <div class="scaler-info-box">Run FlowSpec dependency check. Verifies BGP FlowSpec AFI, VRF FlowSpec, and related config.</div>
                                    <button type="button" class="scaler-btn scaler-btn-primary" id="fs-dep-check-btn">Run Dependency Check</button>
                                    <div id="fs-dep-result" style="margin-top:12px"></div>
                                </div>`;
                            }
                            const issues = result.issues || [];
                            const statusClass = (s) => (s === 'critical' ? 'error' : s === 'warning' ? 'warning' : 'ok');
                            const statusLabel = (s) => (s === 'critical' ? '[FAIL]' : s === 'warning' ? '[WARN]' : '[INFO]');
                            const rows = issues.map(i => `<tr><td>${i.issue || ''}</td><td><span class="scaler-status-${statusClass(i.severity || '')}">${statusLabel(i.severity || '')}</span></td><td><pre style="margin:0;font-size:0.8em;white-space:pre-wrap">${(i.fix_command || '').replace(/</g, '&lt;')}</pre></td></tr>`).join('');
                            const summary = result.passed ? '<span class="scaler-status-ok">[OK] All FlowSpec dependencies satisfied</span>' : `<span class="scaler-status-error">${issues.length} issue(s) found</span>`;
                            return `<div class="scaler-form">
                                <div class="scaler-info-box">${summary}</div>
                                <table class="scaler-table" style="font-size:0.85em"><thead><tr><th>Issue</th><th>Status</th><th>Fix Command</th></tr></thead><tbody>${rows || '<tr><td colspan="3">No issues</td></tr>'}</tbody></table>
                                <div style="margin-top:8px">
                                    <button type="button" class="scaler-btn scaler-btn-sm" id="fs-dep-copy-fixes" ${issues.length ? '' : 'disabled'}>Copy Fix Commands</button>
                                    <button type="button" class="scaler-btn scaler-btn-sm" id="fs-dep-check-again" style="margin-left:8px">Run Again</button>
                                </div>
                            </div>`;
                        },
                        afterRender: (d) => {
                            const runCheck = async () => {
                                const btn = document.getElementById('fs-dep-check-btn') || document.getElementById('fs-dep-check-again');
                                const resEl = document.getElementById('fs-dep-result');
                                if (btn) { btn.disabled = true; btn.textContent = 'Running...'; }
                                try {
                                    const r = await ScalerAPI.flowspecDependencyCheck({ device_id: d.deviceId, ssh_host: d.deviceContext?.mgmt_ip || d.deviceContext?.ip || '' });
                                    self.WizardController.data._flowspecDependencyResult = r;
                                    self.WizardController.render();
                                } catch (e) {
                                    if (resEl) resEl.innerHTML = '<div class="scaler-error">' + e.message + '</div>';
                                } finally {
                                    if (btn) { btn.disabled = false; btn.textContent = 'Run Dependency Check'; }
                                }
                            };
                            document.getElementById('fs-dep-check-btn')?.addEventListener('click', runCheck);
                            document.getElementById('fs-dep-check-again')?.addEventListener('click', async () => {
                                self.WizardController.data._flowspecDependencyResult = null;
                                self.WizardController.render();
                                setTimeout(runCheck, 100);
                            });
                            document.getElementById('fs-dep-copy-fixes')?.addEventListener('click', () => {
                                const r = self.WizardController.data._flowspecDependencyResult;
                                const issues = r?.issues || [];
                                const text = issues.map(i => `# ${i.component}: ${i.fix_description || ''}\n${i.fix_command || ''}`).join('\n\n');
                                if (text && navigator.clipboard?.writeText) {
                                    navigator.clipboard.writeText(text).then(() => self.showNotification('Fix commands copied to clipboard', 'success')).catch(() => {});
                                }
                            });
                        },
                        collectData: () => ({}),
                        skipIf: (d) => d.flowspecOption !== 'dependency'
                    },
                    {
                        title: 'Other Options',
                        render: (d) => `<div class="scaler-form">
                            <div class="scaler-info-box">Use FlowSpec VPN wizard for VRF FlowSpec AFI, or scaler CLI for BGP FlowSpec AFI and Interface FlowSpec.</div>
                            <p style="font-size:0.9em;color:#888">BGP FlowSpec AFI: configure SAFI 133/134 on BGP neighbors.<br>Interface FlowSpec: enable on WAN interfaces.<br>VRF FlowSpec AFI: use FlowSpec VPN wizard.</p>
                        </div>`,
                        collectData: () => ({}),
                        skipIf: (d) => !['bgp-afi','interface','vrf-afi'].includes(d.flowspecOption)
                    },
                    {
                        title: 'Naming',
                        render: (d) => `
                            <div class="scaler-form">
                                <div class="scaler-form-group">
                                    <label>Policy Name</label>
                                    <input type="text" id="fs-policy" class="scaler-input" value="${d.policyName || 'POL-FS-1'}" placeholder="POL-FS-1">
                                </div>
                                <div class="scaler-form-group">
                                    <label>Match-Class Name</label>
                                    <input type="text" id="fs-mc" class="scaler-input" value="${d.matchClassName || 'MC-1'}" placeholder="MC-1">
                                </div>
                                <div class="scaler-form-group">
                                    <label><input type="checkbox" id="fs-ipv4" ${d.includeIpv4 !== false ? 'checked' : ''}> IPv4</label>
                                    <label style="margin-left:12px"><input type="checkbox" id="fs-ipv6" ${d.includeIpv6 ? 'checked' : ''}> IPv6</label>
                                </div>
                            </div>`,
                        collectData: () => ({
                            policyName: document.getElementById('fs-policy')?.value || 'POL-FS-1',
                            matchClassName: document.getElementById('fs-mc')?.value || 'MC-1',
                            includeIpv4: document.getElementById('fs-ipv4')?.checked !== false,
                            includeIpv6: document.getElementById('fs-ipv6')?.checked || false
                        }),
                        skipIf: (d) => d.flowspecOption !== 'local'
                    },
                    {
                        title: 'Match Criteria',
                        render: (d) => `
                            <div class="scaler-form">
                                <div class="scaler-form-group">
                                    <label>Destination IP (prefix, required)</label>
                                    <input type="text" id="fs-dest-ip" class="scaler-input" value="${d.destIp || '10.0.0.0/24'}" placeholder="10.0.0.0/24">
                                </div>
                                <div class="scaler-form-group">
                                    <label>Destination Port (optional)</label>
                                    <input type="text" id="fs-dest-port" class="scaler-input" value="${d.destPort || ''}" placeholder="53, 80, or 1-1024">
                                </div>
                                <div class="scaler-form-group">
                                    <label>Protocol (optional, 6=TCP, 17=UDP)</label>
                                    <input type="text" id="fs-protocol" class="scaler-input" value="${d.protocol || ''}" placeholder="6">
                                </div>
                            </div>`,
                        collectData: () => ({
                            destIp: document.getElementById('fs-dest-ip')?.value || '10.0.0.0/24',
                            destPort: document.getElementById('fs-dest-port')?.value || '',
                            protocol: document.getElementById('fs-protocol')?.value || ''
                        }),
                        skipIf: (d) => d.flowspecOption !== 'local'
                    },
                    {
                        title: 'Action',
                        render: (d) => `
                            <div class="scaler-form">
                                <div class="scaler-form-group">
                                    <label>Action</label>
                                    <select id="fs-action" class="scaler-select">
                                        <option value="drop" ${d.action === 'drop' ? 'selected' : ''}>Drop</option>
                                        <option value="rate-limit" ${d.action === 'rate-limit' ? 'selected' : ''}>Rate-limit</option>
                                    </select>
                                </div>
                                <div class="scaler-form-group" id="fs-rate-row" style="${d.action === 'rate-limit' ? '' : 'display:none'}">
                                    <label>Rate (bps)</label>
                                    <input type="number" id="fs-rate" class="scaler-input" value="${d.rateBps || 1000000}" min="0">
                                </div>
                            </div>`,
                        afterRender: () => {
                            document.getElementById('fs-action')?.addEventListener('change', (e) => {
                                const row = document.getElementById('fs-rate-row');
                                if (row) row.style.display = e.target.value === 'rate-limit' ? 'block' : 'none';
                            });
                        },
                        collectData: () => ({
                            action: document.getElementById('fs-action')?.value || 'drop',
                            rateBps: parseInt(document.getElementById('fs-rate')?.value, 10) || 1000000
                        }),
                        skipIf: (d) => d.flowspecOption !== 'local'
                    },
                    {
                        title: 'Review',
                        render: (d) => `
                            <div class="scaler-review">
                                <h4>FlowSpec Summary</h4>
                                <table class="scaler-table scaler-summary-table">
                                    <tr><td>Device</td><td>${d.deviceId}</td></tr>
                                    <tr><td>Policy</td><td>${d.policyName}</td></tr>
                                    <tr><td>Match-Class</td><td>${d.matchClassName}</td></tr>
                                    <tr><td>Match</td><td>dest-ip ${d.destIp}${d.destPort ? ', dest-port ' + d.destPort : ''}${d.protocol ? ', protocol ' + d.protocol : ''}</td></tr>
                                    <tr><td>Action</td><td>${d.action}${d.action === 'rate-limit' ? ' ' + d.rateBps + ' bps' : ''}</td></tr>
                                </table>
                                <div class="scaler-preview-box">
                                    <label>DNOS Preview:</label>
                                    <pre id="fs-config-preview">Generating...</pre>
                                </div>
                                <div id="config-validation"></div>
                                <div id="whats-next-container"></div>
                            </div>`,
                        afterRender: async (d) => {
                            try {
                                const mc = {
                                    name: d.matchClassName,
                                    dest_ip: d.destIp,
                                    dest_port: d.destPort || undefined,
                                    protocol: d.protocol || undefined,
                                    action: d.action,
                                    rate_bps: d.action === 'rate-limit' ? d.rateBps : undefined
                                };
                                const params = {
                                    policy_name: d.policyName,
                                    match_classes: [mc],
                                    include_ipv4: d.includeIpv4 !== false,
                                    include_ipv6: d.includeIpv6 || false
                                };
                                const result = await ScalerAPI.generateFlowSpec(params);
                                const el = document.getElementById('fs-config-preview');
                                if (el) el.innerHTML = result.config ? ScalerGUI._highlightDnosConfig(result.config) : '(empty)';
                                ScalerGUI.WizardController.data.generatedConfig = result.config;
                                try {
                                    const val = await ScalerAPI.validateConfig({ config: result.config, hierarchy: 'flowspec' });
                                    const vEl = document.getElementById('config-validation');
                                    if (vEl) vEl.innerHTML = ScalerGUI._renderValidationResults(val.errors, val.warnings, val.suggestions);
                                } catch (e) { console.warn('[ScalerGUI] validation display error:', e.message); }
                                const container = document.getElementById('whats-next-container');
                                if (container) {
                                    const createdData = { deviceId: d.deviceId };
                                    const section = await ScalerGUI._renderWhatsNextSection('flowspec', d, createdData, result.config);
                                    if (section) { container.innerHTML = ''; container.appendChild(section); }
                                }
                            } catch (e) {
                                const el = document.getElementById('fs-config-preview');
                                if (el) el.textContent = `Error: ${e.message}`;
                            }
                        },
                        skipIf: (d) => d.flowspecOption !== 'local'
                    },
                    { ...ScalerGUI._buildPushStep({
                        radioName: 'fs-push-mode',
                        includeClipboard: false,
                        infoText: (d) => `<strong>Config:</strong> Ready to push FlowSpec policy ${d.policyName} to ${d.deviceId}.`
                    }), skipIf: (d) => d.flowspecOption !== 'local' }
                ],
                onComplete: async (data) => {
                    if (data.flowspecOption !== 'local') {
                        this.closePanel('flowspec-wizard');
                        return;
                    }
                    try {
                        const ctx = data.deviceContext || {};
                        const result = await ScalerAPI.pushConfig({
                            device_id: data.deviceId,
                            config: data.generatedConfig,
                            hierarchy: 'flowspec',
                            mode: data.pushMode === 'dry_run' ? 'merge' : (data.load_mode || 'merge'),
                            dry_run: data.dryRun,
                            push_method: data.push_method || 'terminal_paste',
                            load_mode: data.load_mode || 'merge',
                            ssh_host: ctx.mgmt_ip || ctx.ip || '',
                            job_name: `FlowSpec ${data.policyName} on ${data.deviceId}`
                        });
                        this.closePanel('flowspec-wizard');
                        this.recordWizardChange(data.deviceId, 'flowspec', { policyName: data.policyName, dryRun: data.dryRun }, {
                            params: { ...data },
                            generatedConfig: data.generatedConfig,
                            pushMode: data.pushMode || (data.dryRun ? 'dry_run' : 'commit'),
                            jobId: result.job_id,
                        });
                        this.showProgress(result.job_id, `Pushing FlowSpec to ${data.deviceId}`, {
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
        
        async openFlowSpecVPNWizard(deviceId = null, prefillParams = null) {
            if (!deviceId) {
                this.openDeviceSelector('FlowSpec VPN Wizard', (id) => this.openFlowSpecVPNWizard(id, prefillParams));
                return;
            }
            if (!this._isDeviceConfigurable(deviceId)) return;
            const content = document.createElement('div');
            content.className = 'scaler-wizard-container';
            content.innerHTML = '<div class="scaler-loading">Loading...</div>';
            this.openPanel('flowspec-vpn-wizard', `FlowSpec VPN - ${deviceId}`, content, {
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
            const vrfs = ctx?.vrfs || [];
            const vrfNames = vrfs.map(v => (typeof v === 'string' ? v : v?.name || v)).filter(Boolean);
            const prefillVrf = (prefillParams?.vrfs && prefillParams.vrfs[0]) ? (typeof prefillParams.vrfs[0] === 'string' ? prefillParams.vrfs[0] : prefillParams.vrfs[0]?.name) : null;
            const existingPolicies = ctx?.flowspec_policies || [];
            const nextMc = (existingPolicies.length || 0) + 1;
            ScalerGUI.WizardController.init({
                panelName: 'flowspec-vpn-wizard',
                quickNavKey: 'flowspec-vpn-wizard',
                title: 'FlowSpec VPN',
                initialData: {
                    deviceId,
                    deviceContext: ctx,
                    vrf: prefillVrf || vrfNames[0] || '',
                    policyName: 'POL-FS-VPN-1',
                    matchClassName: `MC-${nextMc}`,
                    destIp: '10.0.0.0/24',
                    destPort: '',
                    protocol: '6',
                    action: 'drop',
                    rateBps: 1000000,
                    includeIpv4: true,
                    includeIpv6: false,
                    ...(prefillParams || {})
                },
                lastRunWizardType: 'flowspec-vpn',
                onLastRunRerun: (rec) => self._handleLastRunAction(rec, deviceId, ctx),
                onLastRunRerunOther: (rec) => {
                    self.closePanel('flowspec-vpn-wizard');
                    self.openMirrorWizard(rec.deviceId);
                },
                steps: [
                    {
                        title: 'VRF Selection',
                        render: (d) => {
                            const opts = vrfNames.length ? vrfNames.map(v => `<option value="${v}" ${d.vrf === v ? 'selected' : ''}>${v}</option>`).join('') : '<option value="">No VRFs found - create VRF first</option>';
                            return `
                            <div class="scaler-form">
                                <div class="scaler-form-group">
                                    <label>VRF Instance</label>
                                    <select id="fsvpn-vrf" class="scaler-select">${opts}</select>
                                </div>
                                <p class="scaler-hint">FlowSpec policy will be scoped to this VRF.</p>
                            </div>`;
                        },
                        collectData: () => ({
                            vrf: document.getElementById('fsvpn-vrf')?.value || ''
                        })
                    },
                    {
                        title: 'Naming',
                        render: (d) => `
                            <div class="scaler-form">
                                <div class="scaler-form-group">
                                    <label>Policy Name</label>
                                    <input type="text" id="fsvpn-policy" class="scaler-input" value="${d.policyName || 'POL-FS-VPN-1'}" placeholder="POL-FS-VPN-1">
                                </div>
                                <div class="scaler-form-group">
                                    <label>Match-Class Name</label>
                                    <input type="text" id="fsvpn-mc" class="scaler-input" value="${d.matchClassName || 'MC-1'}" placeholder="MC-1">
                                </div>
                                <div class="scaler-form-group">
                                    <label><input type="checkbox" id="fsvpn-ipv4" ${d.includeIpv4 !== false ? 'checked' : ''}> IPv4</label>
                                    <label style="margin-left:12px"><input type="checkbox" id="fsvpn-ipv6" ${d.includeIpv6 ? 'checked' : ''}> IPv6</label>
                                </div>
                            </div>`,
                        collectData: () => ({
                            policyName: document.getElementById('fsvpn-policy')?.value || 'POL-FS-VPN-1',
                            matchClassName: document.getElementById('fsvpn-mc')?.value || 'MC-1',
                            includeIpv4: document.getElementById('fsvpn-ipv4')?.checked !== false,
                            includeIpv6: document.getElementById('fsvpn-ipv6')?.checked || false
                        })
                    },
                    {
                        title: 'Match Criteria',
                        render: (d) => `
                            <div class="scaler-form">
                                <div class="scaler-form-group">
                                    <label>Destination IP (prefix, required)</label>
                                    <input type="text" id="fsvpn-dest-ip" class="scaler-input" value="${d.destIp || '10.0.0.0/24'}" placeholder="10.0.0.0/24">
                                </div>
                                <div class="scaler-form-group">
                                    <label>Destination Port (optional)</label>
                                    <input type="text" id="fsvpn-dest-port" class="scaler-input" value="${d.destPort || ''}" placeholder="53, 80, or 1-1024">
                                </div>
                                <div class="scaler-form-group">
                                    <label>Protocol (optional, 6=TCP, 17=UDP)</label>
                                    <input type="text" id="fsvpn-protocol" class="scaler-input" value="${d.protocol || ''}" placeholder="6">
                                </div>
                            </div>`,
                        collectData: () => ({
                            destIp: document.getElementById('fsvpn-dest-ip')?.value || '10.0.0.0/24',
                            destPort: document.getElementById('fsvpn-dest-port')?.value || '',
                            protocol: document.getElementById('fsvpn-protocol')?.value || ''
                        })
                    },
                    {
                        title: 'Action',
                        render: (d) => `
                            <div class="scaler-form">
                                <div class="scaler-form-group">
                                    <label>Action</label>
                                    <select id="fsvpn-action" class="scaler-select">
                                        <option value="drop" ${d.action === 'drop' ? 'selected' : ''}>Drop</option>
                                        <option value="rate-limit" ${d.action === 'rate-limit' ? 'selected' : ''}>Rate-limit</option>
                                    </select>
                                </div>
                                <div class="scaler-form-group" id="fsvpn-rate-row" style="${d.action === 'rate-limit' ? '' : 'display:none'}">
                                    <label>Rate (bps)</label>
                                    <input type="number" id="fsvpn-rate" class="scaler-input" value="${d.rateBps || 1000000}" min="0">
                                </div>
                            </div>`,
                        afterRender: () => {
                            document.getElementById('fsvpn-action')?.addEventListener('change', (e) => {
                                const row = document.getElementById('fsvpn-rate-row');
                                if (row) row.style.display = e.target.value === 'rate-limit' ? 'block' : 'none';
                            });
                        },
                        collectData: () => ({
                            action: document.getElementById('fsvpn-action')?.value || 'drop',
                            rateBps: parseInt(document.getElementById('fsvpn-rate')?.value, 10) || 1000000
                        })
                    },
                    {
                        title: 'Review',
                        render: (d) => `
                            <div class="scaler-review">
                                <h4>FlowSpec VPN Summary</h4>
                                <table class="scaler-table scaler-summary-table">
                                    <tr><td>Device</td><td>${d.deviceId}</td></tr>
                                    <tr><td>VRF</td><td>${d.vrf || '(none)'}</td></tr>
                                    <tr><td>Policy</td><td>${d.policyName}</td></tr>
                                    <tr><td>Match-Class</td><td>${d.matchClassName}</td></tr>
                                    <tr><td>Match</td><td>dest-ip ${d.destIp}${d.destPort ? ', dest-port ' + d.destPort : ''}${d.protocol ? ', protocol ' + d.protocol : ''}</td></tr>
                                    <tr><td>Action</td><td>${d.action}${d.action === 'rate-limit' ? ' ' + d.rateBps + ' bps' : ''}</td></tr>
                                </table>
                                <div class="scaler-preview-box">
                                    <label>DNOS Preview:</label>
                                    <pre id="fsvpn-config-preview">Generating...</pre>
                                </div>
                                <div id="fsvpn-config-validation"></div>
                                <div id="fsvpn-whats-next-container"></div>
                            </div>`,
                        afterRender: async (d) => {
                            try {
                                const mc = {
                                    name: d.matchClassName,
                                    dest_ip: d.destIp,
                                    dest_port: d.destPort || undefined,
                                    protocol: d.protocol || undefined,
                                    action: d.action,
                                    rate_bps: d.action === 'rate-limit' ? d.rateBps : undefined
                                };
                                const params = {
                                    policy_name: d.policyName,
                                    match_classes: [mc],
                                    include_ipv4: d.includeIpv4 !== false,
                                    include_ipv6: d.includeIpv6 || false,
                                    vrf: d.vrf || undefined
                                };
                                const result = await ScalerAPI.generateFlowSpec(params);
                                const el = document.getElementById('fsvpn-config-preview');
                                if (el) el.innerHTML = result.config ? ScalerGUI._highlightDnosConfig(result.config) : '(empty)';
                                ScalerGUI.WizardController.data.generatedConfig = result.config;
                                try {
                                    const val = await ScalerAPI.validateConfig({ config: result.config, hierarchy: 'flowspec' });
                                    const vEl = document.getElementById('fsvpn-config-validation');
                                    if (vEl) vEl.innerHTML = ScalerGUI._renderValidationResults(val.errors, val.warnings, val.suggestions);
                                } catch (e) { console.warn('[ScalerGUI] validation display error:', e.message); }
                                const container = document.getElementById('fsvpn-whats-next-container');
                                if (container) {
                                    const createdData = { deviceId: d.deviceId, vrf: d.vrf };
                                    const section = await ScalerGUI._renderWhatsNextSection('flowspec-vpn', d, createdData, result.config);
                                    if (section) { container.innerHTML = ''; container.appendChild(section); }
                                }
                            } catch (e) {
                                const el = document.getElementById('fsvpn-config-preview');
                                if (el) el.textContent = `Error: ${e.message}`;
                            }
                        }
                    },
                    ScalerGUI._buildPushStep({
                        radioName: 'fsvpn-push-mode',
                        includeClipboard: false,
                        infoText: (d) => `<strong>Config:</strong> Ready to push FlowSpec VPN policy ${d.policyName} (VRF ${d.vrf}) to ${d.deviceId}.`
                    })
                ],
                onComplete: async (data) => {
                    try {
                        const ctx = data.deviceContext || {};
                        const result = await ScalerAPI.pushConfig({
                            device_id: data.deviceId,
                            config: data.generatedConfig,
                            hierarchy: 'flowspec',
                            mode: data.pushMode === 'dry_run' ? 'merge' : (data.load_mode || 'merge'),
                            dry_run: data.dryRun,
                            push_method: data.push_method || 'terminal_paste',
                            load_mode: data.load_mode || 'merge',
                            ssh_host: ctx.mgmt_ip || ctx.ip || '',
                            job_name: `FlowSpec VPN ${data.policyName} (${data.vrf}) on ${data.deviceId}`
                        });
                        this.closePanel('flowspec-vpn-wizard');
                        this.recordWizardChange(data.deviceId, 'flowspec-vpn', { policyName: data.policyName, vrf: data.vrf, dryRun: data.dryRun }, {
                            params: { ...data },
                            generatedConfig: data.generatedConfig,
                            pushMode: data.pushMode || (data.dryRun ? 'dry_run' : 'commit'),
                            jobId: result.job_id,
                        });
                        this.showProgress(result.job_id, `Pushing FlowSpec VPN to ${data.deviceId}`, {
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
                        const vrfs = c?.vrfs || [];
                        const vrfNames = vrfs.map(v => (typeof v === 'string' ? v : v?.name || v)).filter(Boolean);
                        self.WizardController.data.deviceContext = c;
                        if (!self.WizardController.data.vrf && vrfNames[0]) self.WizardController.data.vrf = vrfNames[0];
                        self.WizardController.render();
                    }
                }).catch(e => console.warn('[ScalerGUI] wizard operation failed:', e.message));
            }
        },

        async openSystemWizard(deviceId = null, prefillParams = null) {
            if (!deviceId) {
                this.openDeviceSelector('System Config', (id) => this.openSystemWizard(id, prefillParams));
                return;
            }
            if (!this._isDeviceConfigurable(deviceId)) return;
            const content = document.createElement('div');
            content.innerHTML = '<div class="scaler-loading">Loading...</div>';
            this.openPanel('system-wizard', `System Config - ${deviceId}`, content, { width: '540px', parentPanel: 'scaler-menu' });
            const self = this;
            let ctx = this._deviceContexts[deviceId] || null;
            const hasFresh = ctx && (Date.now() - (ctx._fetchedAt || 0)) < this._contextCacheTTL;
            if (!hasFresh) {
                try {
                    ctx = await this.getDeviceContext(deviceId);
                } catch (_) {}
            }
            const cfg = ctx?.config_summary || {};
            const sysName = cfg.system_name || cfg.hostname || deviceId;
            this.WizardController.init({
                panelName: 'system-wizard',
                quickNavKey: 'system-wizard',
                title: `System Config - ${deviceId}`,
                lastRunWizardType: 'system',
                initialData: {
                    deviceId,
                    deviceContext: ctx,
                    name: sysName,
                    timezone: cfg.timezone || 'UTC',
                    timing_mode: 'ntp',
                    ntp_servers: [],
                    ssh_admin_state: 'enabled',
                    ...(prefillParams || {})
                },
                wizardHeader: (data) => self.renderContextPanel(deviceId, data.deviceContext || {}, {
                    wizardType: 'system',
                    onRefresh: () => self.refreshDeviceContextLive(deviceId).then(c => {
                        self.WizardController.data.deviceContext = c;
                        self.WizardController.render();
                    })
                }),
                steps: [
                    {
                        title: 'Hostname & Timezone',
                        render: (d) => `
                            <div class="scaler-form">
                                <div class="scaler-form-group"><label>System Name (hostname)</label><input type="text" id="sys-name" class="scaler-input" value="${d.name || ''}" placeholder="e.g. PE-4"></div>
                                <div class="scaler-form-group"><label>Timezone</label><input type="text" id="sys-timezone" class="scaler-input" value="${d.timezone || 'UTC'}" placeholder="e.g. Israel, UTC"></div>
                                <div class="scaler-form-group"><label>Timing Mode</label><select id="sys-timing" class="scaler-select"><option value="ntp" ${(d.timing_mode || 'ntp') === 'ntp' ? 'selected' : ''}>NTP</option><option value="manual" ${d.timing_mode === 'manual' ? 'selected' : ''}>Manual</option></select></div>
                            </div>`,
                        collectData: () => ({
                            name: document.getElementById('sys-name')?.value || '',
                            timezone: document.getElementById('sys-timezone')?.value || 'UTC',
                            timing_mode: document.getElementById('sys-timing')?.value || 'ntp'
                        })
                    },
                    {
                        title: 'NTP Servers',
                        render: (d) => {
                            const srv = (d.ntp_servers || []).map(s => s.address || s.server || s).filter(Boolean);
                            return `<div class="scaler-form">
                                <div class="scaler-info-box">NTP server IPs (comma-separated). VRF default used.</div>
                                <div class="scaler-form-group"><label>NTP Servers</label><input type="text" id="ntp-servers" class="scaler-input" value="${srv.join(', ')}" placeholder="e.g. 100.64.15.2, 100.64.15.3"></div>
                            </div>`;
                        },
                        collectData: () => {
                            const val = document.getElementById('ntp-servers')?.value || '';
                            const addrs = val.split(',').map(s => s.trim()).filter(Boolean);
                            return { ntp_servers: addrs.map(a => ({ address: a, vrf: 'default' })) };
                        }
                    },
                    {
                        title: 'Review & Push',
                        render: (data) => `<div class="scaler-form">
                            <div class="scaler-form-group"><label>Generated Config</label><pre id="system-config-preview" class="scaler-syntax-preview">Loading...</pre></div>
                            <div class="scaler-form-group"><label>Push Mode</label><div class="scaler-radio-group">
                                <label class="scaler-radio"><input type="radio" name="sys-push-mode" value="dry_run" checked><span>Commit Check First</span></label>
                                <label class="scaler-radio"><input type="radio" name="sys-push-mode" value="commit"><span>Commit</span></label>
                                <label class="scaler-radio"><input type="radio" name="sys-push-mode" value="clipboard"><span>Copy to Clipboard</span></label>
                            </div></div>
                        </div>`,
                        afterRender: async (data) => {
                            const pre = document.getElementById('system-config-preview');
                            if (!pre) return;
                            try {
                                const params = {
                                    name: data.name || data.deviceId,
                                    timezone: data.timezone || 'UTC',
                                    timing_mode: data.timing_mode || 'ntp',
                                    ntp_servers: data.ntp_servers || [],
                                    ssh_admin_state: data.ssh_admin_state || 'enabled'
                                };
                                const r = await ScalerAPI.generateSystem(params);
                                self.WizardController.data.generatedConfig = r.config;
                                pre.textContent = r.config || '(empty)';
                            } catch (e) {
                                pre.textContent = `Error: ${e.message}`;
                            }
                        },
                        collectData: () => ({
                            dryRun: document.querySelector('input[name="sys-push-mode"]:checked')?.value === 'dry_run',
                            pushMode: document.querySelector('input[name="sys-push-mode"]:checked')?.value || 'dry_run'
                        })
                    }
                ],
                onComplete: async (data) => {
                    const config = data.generatedConfig || '';
                    const mode = data.pushMode || 'dry_run';
                    const ctx = data.deviceContext || {};
                    if (mode === 'clipboard') {
                        try { await window.safeClipboardWrite(config); } catch (_) {}
                        this.showNotification('Config copied to clipboard', 'success');
                        this.closePanel('system-wizard');
                        return;
                    }
                    try {
                        const result = await ScalerAPI.pushConfig({
                            device_id: data.deviceId,
                            config,
                            hierarchy: 'system',
                            mode: 'merge',
                            dry_run: mode === 'dry_run',
                            ssh_host: ctx.mgmt_ip || ctx.ip || '',
                            job_name: `System config on ${data.deviceId}`
                        });
                        this.closePanel('system-wizard');
                        this.showProgress(result.job_id, `System: ${data.deviceId}`, {
                            device_id: data.deviceId,
                            onComplete: (success) => {
                                if (success) this.showNotification(`System config applied on ${data.deviceId}`, 'success');
                                else this.showNotification(`Push failed on ${data.deviceId}`, 'error');
                            }
                        });
                    } catch (e) {
                        this.showNotification(`Push failed: ${e.message}`, 'error');
                    }
                }
            });
        },
        
        async openMirrorWizard(prefillSourceId, prefillTargetId) {
            const content = document.createElement('div');
            content.className = 'scaler-mirror-wizard';
            content.innerHTML = '<div class="scaler-loading">Loading devices...</div>';
            this.openPanel('mirror-wizard', 'Mirror Config', content, {
                width: '580px',
                parentPanel: 'scaler-menu'
            });
        
            try {
                const devices = await this._getWizardDeviceList();
                if (devices.length < 2) {
                    content.innerHTML = '<div class="scaler-info-box" style="color:var(--dn-orange,#e67e22)">Add at least 2 devices to the canvas to mirror config.</div>';
                    return;
                }
        
                const self = this;
                const SECTIONS = [
                    { key: 'system', label: 'System' },
                    { key: 'service_interfaces', label: 'Interfaces' },
                    { key: 'protocols', label: 'Protocols' },
                    { key: 'services', label: 'Network Services' },
                    { key: 'routing_policy', label: 'Routing Policy' },
                    { key: 'acls', label: 'ACLs' },
                    { key: 'qos', label: 'QoS' },
                    { key: 'routing', label: 'Routing (BGP)' }
                ];
        
                this.WizardController.init({
                    panelName: 'mirror-wizard',
                    title: 'Mirror Config',
                    initialData: {
                        devices,
                        sourceDeviceId: prefillSourceId || '',
                        targetDeviceId: prefillTargetId || '',
                        analysisResult: null,
                        sectionActions: {},
                        generatedConfig: null,
                    },
                    wizardHeader: (data) => {
                        const src = data.sourceDeviceId;
                        const tgt = data.targetDeviceId;
                        if (!src || !tgt) return null;
                        const srcDev = (data.devices || []).find(d => d.id === src);
                        const tgtDev = (data.devices || []).find(d => d.id === tgt);
                        const div = document.createElement('div');
                        div.className = 'device-context-panel';
                        div.innerHTML = `<div class="mirror-direction-bar">
                            <span class="mirror-direction-device">${self.escapeHtml(srcDev?.hostname || src)}</span>
                            <span class="mirror-direction-arrow">&rarr;</span>
                            <span class="mirror-direction-device">${self.escapeHtml(tgtDev?.hostname || tgt)}</span>
                        </div>`;
                        return div;
                    },
                    steps: [
                        {
                            title: 'Devices',
                            render: (data) => {
                                const devs = (data.devices || []).filter(d => d.hasSSH);
                                const options = devs.map(d =>
                                    `<option value="${d.id}">${d.hostname || d.id}</option>`
                                ).join('');
                                return `<div class="scaler-form">
                                    <div class="scaler-info-box">Copy configuration sections from a source device to a target device. You can selectively keep, skip, or delete each section.</div>
                                    <div class="scaler-form-row">
                                        <div class="scaler-form-group" style="flex:1">
                                            <label>Source Device</label>
                                            <select id="mirror-source" class="scaler-select">
                                                <option value="">-- Select source --</option>
                                                ${options}
                                            </select>
                                        </div>
                                        <div class="mirror-arrow-sep">&rarr;</div>
                                        <div class="scaler-form-group" style="flex:1">
                                            <label>Target Device</label>
                                            <select id="mirror-target" class="scaler-select">
                                                <option value="">-- Select target --</option>
                                                ${options}
                                            </select>
                                        </div>
                                    </div>
                                </div>`;
                            },
                            afterRender: (data) => {
                                const srcSel = document.getElementById('mirror-source');
                                const tgtSel = document.getElementById('mirror-target');
                                if (srcSel && data.sourceDeviceId) srcSel.value = data.sourceDeviceId;
                                if (tgtSel && data.targetDeviceId) tgtSel.value = data.targetDeviceId;
                            },
                            collectData: () => ({
                                sourceDeviceId: document.getElementById('mirror-source')?.value || '',
                                targetDeviceId: document.getElementById('mirror-target')?.value || '',
                                analysisResult: null,
                                generatedConfig: null,
                            }),
                            validate: (data) => {
                                if (!data.sourceDeviceId || !data.targetDeviceId) {
                                    self.showNotification('Select both source and target devices', 'warning');
                                    return false;
                                }
                                if (data.sourceDeviceId === data.targetDeviceId) {
                                    self.showNotification('Source and target must be different devices', 'warning');
                                    return false;
                                }
                                return true;
                            }
                        },
                        {
                            title: 'Smart Mapping',
                            render: (data) => {
                                const result = data.analysisResult;
                                if (!result) {
                                    return `<div class="scaler-form"><div class="scaler-loading">Analyzing source vs target...</div></div>`;
                                }
                                const ss = result.smart_suggestions || {};
                                const bgp = ss.bgp_neighbors || [];
                                const wan = ss.wan_ips || [];
                                const svc = ss.service_ips || [];
                                const lldp = ss.lldp_mapping || [];
                                const ifMap = result.interface_map || {};
                                const ipMapping = data.ipMapping || {};
        
                                const bgpRows = bgp.map((n, i) => {
                                    const val = ipMapping[n.source_ip] ?? n.suggested_ip;
                                    return `<tr><td>${self.escapeHtml(n.source_ip)}</td><td>${self.escapeHtml(n.context || '')}</td><td><input type="text" class="scaler-input mirror-ip-input" data-source="${self.escapeHtml(n.source_ip)}" value="${self.escapeHtml(val)}" placeholder="Target IP" style="width:100%"></td></tr>`;
                                }).join('');
                                const wanRows = wan.map((n, i) => {
                                    const val = ipMapping[n.source_ip] ?? n.suggested_ip;
                                    return `<tr><td>${self.escapeHtml(n.source_iface)}</td><td>${self.escapeHtml(n.source_ip)}</td><td><input type="text" class="scaler-input mirror-ip-input" data-source="${self.escapeHtml(n.source_ip)}" value="${self.escapeHtml(val)}" placeholder="Target IP" style="width:100%"></td></tr>`;
                                }).join('');
                                const svcRows = svc.map((n, i) => {
                                    const val = ipMapping[n.source_ip] ?? n.suggested_ip;
                                    return `<tr><td>${self.escapeHtml(n.source_ip)}</td><td>${self.escapeHtml(n.context || '')}</td><td><input type="text" class="scaler-input mirror-ip-input" data-source="${self.escapeHtml(n.source_ip)}" value="${self.escapeHtml(val)}" placeholder="Target IP" style="width:100%"></td></tr>`;
                                }).join('');
                                const lldpRows = lldp.map((n) => {
                                    const key = `lldp:${n.source_iface}`;
                                    return `<tr><td>${self.escapeHtml(n.source_iface)}</td><td>${self.escapeHtml(n.target_iface)}</td><td>${self.escapeHtml(n.peer || '')}</td></tr>`;
                                }).join('');
        
                                const ifMapRows = Object.entries(ifMap).map(([src, tgt]) =>
                                    `<tr><td>${self.escapeHtml(src)}</td><td>${self.escapeHtml(tgt)}</td></tr>`
                                ).join('');
        
                                let html = `<div class="scaler-form"><div class="scaler-info-box">Review and edit IP/interface mappings. Changes apply when generating config.</div>`;
                                if (Object.keys(ifMap).length > 0) {
                                    html += `<div class="scaler-form-group"><label>Interface Mapping</label><table class="mirror-mapping-table"><thead><tr><th>Source</th><th>Target</th></tr></thead><tbody>${ifMapRows}</tbody></table></div>`;
                                }
                                if (bgp.length > 0) {
                                    html += `<div class="scaler-form-group"><label>BGP Neighbor IPs</label><table class="mirror-mapping-table"><thead><tr><th>Source IP</th><th>Context</th><th>Target IP</th></tr></thead><tbody>${bgpRows}</tbody></table></div>`;
                                }
                                if (wan.length > 0) {
                                    html += `<div class="scaler-form-group"><label>WAN Interface IPs</label><table class="mirror-mapping-table"><thead><tr><th>Interface</th><th>Source IP</th><th>Target IP</th></tr></thead><tbody>${wanRows}</tbody></table></div>`;
                                }
                                if (svc.length > 0) {
                                    html += `<div class="scaler-form-group"><label>Service IPs</label><table class="mirror-mapping-table"><thead><tr><th>Source IP</th><th>Context</th><th>Target IP</th></tr></thead><tbody>${svcRows}</tbody></table></div>`;
                                }
                                if (lldp.length > 0) {
                                    html += `<div class="scaler-form-group"><label>LLDP Interface Mapping</label><table class="mirror-mapping-table"><thead><tr><th>Source</th><th>Target</th><th>Peer</th></tr></thead><tbody>${lldpRows}</tbody></table></div>`;
                                }
                                if (Object.keys(ifMap).length === 0 && bgp.length === 0 && wan.length === 0 && svc.length === 0 && lldp.length === 0) {
                                    html += `<div class="scaler-form-group"><p class="scaler-info-box">No smart suggestions to review. Proceed to Analyze.</p></div>`;
                                }
                                html += `</div>`;
                                return html;
                            },
                            afterRender: (data) => {
                                if (!data.analysisResult) {
                                    const srcRes = self._resolveDeviceId(data.sourceDeviceId);
                                    const tgtRes = self._resolveDeviceId(data.targetDeviceId);
                                    ScalerAPI.mirrorAnalyze({
                                        source_device_id: data.sourceDeviceId,
                                        target_device_id: data.targetDeviceId,
                                        ssh_hosts: [srcRes?.sshHost || '', tgtRes?.sshHost || '']
                                    }).then(result => {
                                        self.WizardController.data.analysisResult = result;
                                        self.WizardController.render();
                                    }).catch(e => {
                                        self.showNotification(`Analysis failed: ${e.message}`, 'error');
                                    });
                                }
                            },
                            collectData: () => {
                                const ipMapping = {};
                                document.querySelectorAll('.mirror-ip-input').forEach(inp => {
                                    const src = inp.dataset.source;
                                    const val = (inp.value || '').trim();
                                    if (src && val) ipMapping[src] = val;
                                });
                                return { ipMapping };
                            }
                        },
                        {
                            title: 'Analyze',
                            render: (data) => {
                                const result = data.analysisResult;
                                if (!result) {
                                    return `<div class="scaler-form"><div class="scaler-loading">Analyzing source vs target...</div></div>`;
                                }
                                const sd = result.smart_diff?.summary || {};
                                const ifAdd = result.smart_diff?.interfaces?.add?.length || 0;
                                const sectionCards = SECTIONS.map(s => {
                                    const act = data.sectionActions?.[s.key] || 'keep';
                                    const opts = ['keep', 'edit', 'skip', 'delete'].map(v =>
                                        `<option value="${v}" ${act === v ? 'selected' : ''}>${v.charAt(0).toUpperCase() + v.slice(1)}</option>`
                                    ).join('');
                                    return `<div class="mirror-section-card">
                                        <span class="mirror-section-label">${s.label}</span>
                                        <select class="scaler-select mirror-section-select" data-section="${s.key}">${opts}</select>
                                    </div>`;
                                }).join('');
                                return `<div class="scaler-form">
                                    <div class="mirror-analysis-summary">
                                        <div class="mirror-stat mirror-stat--add"><span class="mirror-stat-num">${sd.need_add || 0}</span><span class="mirror-stat-label">Add</span></div>
                                        <div class="mirror-stat mirror-stat--mod"><span class="mirror-stat-num">${sd.need_modify || 0}</span><span class="mirror-stat-label">Modify</span></div>
                                        <div class="mirror-stat mirror-stat--del"><span class="mirror-stat-num">${sd.need_delete || 0}</span><span class="mirror-stat-label">Delete</span></div>
                                        <div class="mirror-stat mirror-stat--skip"><span class="mirror-stat-num">${sd.can_skip || 0}</span><span class="mirror-stat-label">Identical</span></div>
                                        ${ifAdd ? `<div class="mirror-stat mirror-stat--add"><span class="mirror-stat-num">${ifAdd}</span><span class="mirror-stat-label">Interfaces</span></div>` : ''}
                                    </div>
                                    <div class="scaler-form-group" style="margin-top:14px">
                                        <label>Section Actions</label>
                                        <div class="mirror-section-list">${sectionCards}</div>
                                    </div>
                                </div>`;
                            },
                            afterRender: (data) => {
                                if (!data.analysisResult) {
                                    const srcRes = self._resolveDeviceId(data.sourceDeviceId);
                                    const tgtRes = self._resolveDeviceId(data.targetDeviceId);
                                    ScalerAPI.mirrorAnalyze({
                                        source_device_id: data.sourceDeviceId,
                                        target_device_id: data.targetDeviceId,
                                        ssh_hosts: [srcRes?.sshHost || '', tgtRes?.sshHost || '']
                                    }).then(result => {
                                        self.WizardController.data.analysisResult = result;
                                        self.WizardController.render();
                                    }).catch(e => {
                                        self.showNotification(`Analysis failed: ${e.message}`, 'error');
                                    });
                                }
                            },
                            collectData: () => {
                                const actions = {};
                                document.querySelectorAll('.mirror-section-select').forEach(sel => {
                                    actions[sel.dataset.section] = sel.value || 'keep';
                                });
                                return { sectionActions: actions, generatedConfig: null };
                            }
                        },
                        {
                            title: 'Review',
                            finalButtonText: 'Push to Target',
                            render: (data) => {
                                const config = data.generatedConfig;
                                if (config === null || config === undefined) {
                                    return `<div class="scaler-form"><div class="scaler-loading">Generating config...</div></div>`;
                                }
                                const lineCount = config ? config.split('\n').length : 0;
                                return `<div class="scaler-form">
                                    <div class="scaler-form-group">
                                        <label>Generated Config (${lineCount} lines)</label>
                                        <pre class="scaler-config-preview" style="max-height:300px;overflow:auto">${self.escapeHtml(config || '(empty)')}</pre>
                                    </div>
                                    <div class="scaler-form-group">
                                        <button type="button" class="scaler-btn scaler-btn-sm" id="mirror-toggle-diff">Show diff vs target</button>
                                    </div>
                                    <div id="mirror-diff-area" style="display:none">
                                        <pre class="scaler-config-preview" id="mirror-diff-text" style="max-height:200px;overflow:auto"></pre>
                                    </div>
                                </div>`;
                            },
                            afterRender: (data) => {
                                if (data.generatedConfig === null || data.generatedConfig === undefined) {
                                    const srcRes = self._resolveDeviceId(data.sourceDeviceId);
                                    const tgtRes = self._resolveDeviceId(data.targetDeviceId);
                                    ScalerAPI.mirrorGenerate({
                                        source_device_id: data.sourceDeviceId,
                                        target_device_id: data.targetDeviceId,
                                        ssh_hosts: [srcRes?.sshHost || '', tgtRes?.sshHost || ''],
                                        interface_map: data.analysisResult?.interface_map || {},
                                        section_actions: data.sectionActions || {},
                                        ip_mapping: data.ipMapping || {},
                                        output_mode: 'diff_only'
                                    }).then(r => {
                                        self.WizardController.data.generatedConfig = r.config || '';
                                        self.WizardController.render();
                                    }).catch(e => {
                                        self.showNotification(`Generate failed: ${e.message}`, 'error');
                                    });
                                    return;
                                }
                                document.getElementById('mirror-toggle-diff')?.addEventListener('click', async function() {
                                    const diffArea = document.getElementById('mirror-diff-area');
                                    const diffPre = document.getElementById('mirror-diff-text');
                                    if (!diffArea || !diffPre) return;
                                    if (diffArea.style.display !== 'none') {
                                        diffArea.style.display = 'none';
                                        this.textContent = 'Show diff vs target';
                                        return;
                                    }
                                    diffPre.textContent = 'Loading diff...';
                                    diffArea.style.display = 'block';
                                    this.textContent = 'Hide diff';
                                    try {
                                        const tgtRes = self._resolveDeviceId(data.targetDeviceId);
                                        const r = await ScalerAPI.mirrorPreviewDiff({
                                            target_device_id: data.targetDeviceId,
                                            config: data.generatedConfig,
                                            ssh_host: tgtRes?.sshHost || ''
                                        });
                                        diffPre.textContent = r.diff_text || '(no differences)';
                                    } catch (e) {
                                        diffPre.textContent = `Error: ${e.message}`;
                                    }
                                });
                            },
                            collectData: () => ({}),
                            validate: (data) => {
                                if (!data.generatedConfig) {
                                    self.showNotification('Config not generated yet', 'warning');
                                    return false;
                                }
                                return true;
                            }
                        }
                    ],
                    onComplete: async (data) => {
                        if (!data.generatedConfig) return;
                        const tgtRes = self._resolveDeviceId(data.targetDeviceId);
                        self.closePanel('mirror-wizard');
                        try {
                            const result = await ScalerAPI.pushConfig({
                                device_id: data.targetDeviceId,
                                config: data.generatedConfig,
                                hierarchy: 'network-services',
                                mode: 'merge',
                                dry_run: true,
                                ssh_host: tgtRes?.sshHost || '',
                                job_name: `Mirror ${data.sourceDeviceId} -> ${data.targetDeviceId}`
                            });
                            self.showProgress(result.job_id, `Mirror: ${data.sourceDeviceId} -> ${data.targetDeviceId}`, {
                                device_id: data.targetDeviceId,
                                onComplete: (success, res) => {
                                    if (success) self.showNotification('Mirror committed successfully', 'success');
                                    else if (!res?.cancelled) self.showNotification('Mirror push failed', 'error');
                                }
                            });
                        } catch (e) {
                            self.showNotification(e.message, 'error');
                        }
                    }
                });
            } catch (e) {
                const panel = this.state.activePanels['mirror-wizard'];
                if (panel) {
                    const cd = panel.querySelector('.scaler-panel-content');
                    if (cd) cd.innerHTML = `<div class="scaler-error">${e.message}</div>`;
                }
            }
        },

    });
})(window.ScalerGUI);
