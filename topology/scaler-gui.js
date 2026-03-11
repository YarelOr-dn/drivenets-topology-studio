/**
 * SCALER GUI - Interactive GUI components for network configuration
 * 
 * Provides panels and dialogs for:
 * - Device management
 * - Configuration wizards (Interface, Service, BGP, IGP, MH)
 * - Operations (Compare, Sync, Delete, Scale, Upgrade)
 * - Real-time progress display
 * 
 * @version 2.0.0
 * @requires scaler-api.js
 */

const ScalerGUI = {
    // =========================================================================
    // STATE
    // =========================================================================
    
    state: {
        currentDevice: null,
        selectedDevices: [],
        activePanel: null,
        activePanels: {},
        jobs: {},
        deviceCache: {},
        panelHistory: [],
        lastPanel: null,
        lastOpenPanel: null
    },
    
    // Panel container reference
    panelContainer: null,
    
    // =========================================================================
    // WIZARD CONTROLLER
    // =========================================================================
    
    WizardController: {
        steps: [],
        currentStep: 0,
        data: {},
        panelName: null,
        title: null,
        onComplete: null,
        
        /**
         * Initialize a new wizard
         * @param {Object} config - Wizard configuration
         */
        init(config) {
            this.steps = config.steps || [];
            this.currentStep = 0;
            this.data = config.initialData || {};
            this.panelName = config.panelName;
            this.title = config.title;
            this.onComplete = config.onComplete;
            this.wizardHeader = config.wizardHeader || null;
            this.quickNavKey = config.quickNavKey || null;
            this.stepDependencies = config.stepDependencies || {};
            this.stepKeys = config.stepKeys || {};
            this.stepBuilder = config.stepBuilder || null;
            this._highestStepReached = 0;
            this.lastRunWizardType = config.lastRunWizardType || null;
            this.onLastRunRerun = config.onLastRunRerun || null;
            this.onLastRunRerunOther = config.onLastRunRerunOther || null;
            if (this.stepBuilder) {
                const built = this.stepBuilder(this.data);
                this.steps = built.steps;
                this.stepDependencies = built.deps || {};
                this.stepKeys = built.keys || {};
            }
            this.render();
        },
        
        /**
         * Go to next step
         */
        next() {
            const currentStepConfig = this.steps[this.currentStep];
            if (currentStepConfig.validate && !currentStepConfig.validate(this.data)) {
                return false;
            }
            const prevType = (this.currentStep === 0) ? this.data.interfaceType : undefined;
            if (currentStepConfig.collectData) {
                Object.assign(this.data, currentStepConfig.collectData());
            }
            const newType = (this.currentStep === 0) ? this.data.interfaceType : undefined;
            if (this.stepBuilder && this.currentStep === 0) {
                const built = this.stepBuilder(this.data);
                this.steps = built.steps;
                this.stepDependencies = built.deps || {};
                this.stepKeys = built.keys || {};
                if (prevType !== newType) {
                    this._highestStepReached = 0;
                }
            }
            const isRevisit = this.currentStep < this._highestStepReached;
            const typeUnchangedAt0 = (this.currentStep === 0 && prevType === newType);
            if (isRevisit && this.stepDependencies[this.currentStep] && !typeUnchangedAt0) {
                const invalidated = this.stepDependencies[this.currentStep];
                invalidated.forEach(idx => {
                    (this.stepKeys[idx] || []).forEach(k => delete this.data[k]);
                });
            }
            if (this.currentStep < this.steps.length - 1) {
                this.currentStep++;
                while (this.currentStep < this.steps.length - 1 &&
                       this.steps[this.currentStep].skipIf &&
                       this.steps[this.currentStep].skipIf(this.data)) {
                    this.currentStep++;
                }
                this._highestStepReached = Math.max(this._highestStepReached, this.currentStep);
                this.render();
                return true;
            } else {
                if (this.onComplete) this.onComplete(this.data);
                return true;
            }
        },
        
        /**
         * Go to previous step
         */
        back() {
            if (this.currentStep > 0) {
                this.currentStep--;
                while (this.currentStep > 0 &&
                       this.steps[this.currentStep].skipIf &&
                       this.steps[this.currentStep].skipIf(this.data)) {
                    this.currentStep--;
                }
                this.render();
                return true;
            }
            return false;
        },
        
        /**
         * Go to specific step
         */
        goTo(stepIndex) {
            if (stepIndex >= 0 && stepIndex < this.steps.length) {
                this.currentStep = stepIndex;
                this.render();
            }
        },
        
        /**
         * Render the current wizard state
         */
        render() {
            const content = document.createElement('div');
            content.className = 'scaler-wizard';

            if (this.quickNavKey && ScalerGUI._buildWizardQuickNav) {
                const navBuilder = ScalerGUI._buildWizardQuickNav(this.quickNavKey, this.data?.deviceId);
                const navEl = navBuilder(this.data);
                if (navEl) content.appendChild(navEl);
            }

            if (this.wizardHeader && typeof this.wizardHeader === 'function') {
                const headerEl = this.wizardHeader(this.data);
                if (headerEl) content.appendChild(headerEl);
            }

            const wizardType = this.lastRunWizardType || (this.quickNavKey && ScalerGUI._wizardKeyToType[this.quickNavKey]);
            const deviceId = this.data?.deviceId;
            if (wizardType && deviceId && ScalerGUI._renderLastRunCard) {
                const card = ScalerGUI._renderLastRunCard(wizardType, deviceId,
                    (rec) => this.onLastRunRerun?.(rec),
                    (rec) => this.onLastRunRerunOther?.(rec)
                );
                if (card) content.appendChild(card);
            }
            
            // Step indicator
            content.appendChild(this.renderStepIndicator());
            
            // Current step content
            const stepContent = document.createElement('div');
            stepContent.className = 'scaler-wizard-step-content';
            
            const stepConfig = this.steps[this.currentStep];
            if (stepConfig.render) {
                const stepHtml = stepConfig.render(this.data);
                if (typeof stepHtml === 'string') {
                    stepContent.innerHTML = stepHtml;
                } else {
                    stepContent.appendChild(stepHtml);
                }
            }
            content.appendChild(stepContent);
            
            // Navigation buttons
            content.appendChild(this.renderNavigation());
            
            // Update the panel
            const panel = ScalerGUI.state.activePanels[this.panelName];
            if (panel) {
                const contentDiv = panel.querySelector('.scaler-panel-content');
                if (contentDiv) {
                    contentDiv.innerHTML = '';
                    contentDiv.appendChild(content);
                }
                
                // Bind step-specific events after render
                if (stepConfig.afterRender) {
                    stepConfig.afterRender(this.data);
                }
            }
        },
        
        /**
         * Render step indicator
         */
        renderStepIndicator() {
            const indicator = document.createElement('div');
            indicator.className = 'scaler-wizard-steps';
            
            this.steps.forEach((step, idx) => {
                const stepEl = document.createElement('div');
                stepEl.className = 'scaler-wizard-step-indicator';
                if (idx < this.currentStep) stepEl.classList.add('completed');
                if (idx === this.currentStep) stepEl.classList.add('active');
                
                stepEl.innerHTML = `
                    <div class="step-number">${idx + 1}</div>
                    <div class="step-label">${step.title}</div>
                `;
                
                // Allow clicking on completed steps to go back
                if (idx < this.currentStep) {
                    stepEl.style.cursor = 'pointer';
                    stepEl.onclick = () => this.goTo(idx);
                }
                
                indicator.appendChild(stepEl);
                
                // Add connector line
                if (idx < this.steps.length - 1) {
                    const connector = document.createElement('div');
                    connector.className = 'step-connector';
                    if (idx < this.currentStep) connector.classList.add('completed');
                    indicator.appendChild(connector);
                }
            });
            
            return indicator;
        },
        
        /**
         * Render navigation buttons
         */
        renderNavigation() {
            const nav = document.createElement('div');
            nav.className = 'scaler-wizard-nav';
            
            const isFirst = this.currentStep === 0;
            const isLast = this.currentStep === this.steps.length - 1;
            const stepConfig = this.steps[this.currentStep];
            const isRevisit = this.currentStep < this._highestStepReached;
            const nextLabel = isLast ? (stepConfig.finalButtonText || 'Complete') : (isRevisit ? 'Update' : 'Next');
            
            nav.innerHTML = `
                <button class="scaler-btn" id="wizard-back" ${isFirst ? 'disabled' : ''}>
                    ← Back
                </button>
                <div class="scaler-wizard-nav-right">
                    ${stepConfig.skipable ? '<button class="scaler-btn" id="wizard-skip">Skip</button>' : ''}
                    <button class="scaler-btn scaler-btn-primary" id="wizard-next">
                        ${isLast ? (stepConfig.finalButtonText || 'Complete') : nextLabel + (isRevisit ? '' : ' →')}
                    </button>
                </div>
            `;
            
            // Bind events after adding to DOM
            setTimeout(() => {
                const backBtn = document.getElementById('wizard-back');
                const nextBtn = document.getElementById('wizard-next');
                const skipBtn = document.getElementById('wizard-skip');
                
                if (backBtn) backBtn.onclick = () => this.back();
                if (nextBtn) nextBtn.onclick = () => this.next();
                if (skipBtn) skipBtn.onclick = () => {
                    this.currentStep++;
                    this.render();
                };
            }, 0);
            
            return nav;
        }
    },

    // =========================================================================
    // DEVICE CONTEXT CACHE (cached-then-live for wizard suggestions)
    // =========================================================================

    _deviceContexts: {},
    _contextCacheTTL: 60000,
    _wizardChangeLog: [],
    _wizardHistory: [],
    _WIZARD_HISTORY_KEY: 'scaler_wizard_history',
    _WIZARD_HISTORY_MAX: 100,

    _loadWizardHistory() {
        try {
            const raw = localStorage.getItem(this._WIZARD_HISTORY_KEY);
            if (raw) {
                const parsed = JSON.parse(raw);
                this._wizardHistory = Array.isArray(parsed) ? parsed : [];
            }
        } catch (e) {
            this._wizardHistory = [];
        }
    },

    _saveWizardHistory() {
        try {
            const toSave = this._wizardHistory.slice(-this._WIZARD_HISTORY_MAX);
            localStorage.setItem(this._WIZARD_HISTORY_KEY, JSON.stringify(toSave));
        } catch (e) {
            console.warn('[ScalerGUI] Failed to save wizard history:', e);
        }
    },

    getWizardHistory() {
        return this._wizardHistory;
    },

    _wizardKeyToType: {
        'interface-wizard': 'interfaces',
        'service-wizard': 'services',
        'vrf-wizard': 'vrf',
        'bridge-domain-wizard': 'bridge-domain',
        'flowspec-wizard': 'flowspec',
        'routing-policy-wizard': 'routing-policy',
        'bgp-wizard': 'bgp',
        'igp-wizard': 'igp',
    },

    _getLastRunForWizard(wizardType, deviceId) {
        const id = (deviceId || '').toLowerCase();
        return this._wizardHistory
            .filter(r => (r.wizardType || '') === wizardType && (r.deviceId || '').toLowerCase() === id)
            .sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0))[0] || null;
    },

    _formatLastRunSummary(record) {
        if (!record || !record.params) return '';
        const p = record.params;
        switch (record.wizardType) {
            case 'interfaces':
                return `${p.count ?? 1} ${p.interfaceType || 'bundle'}${p.subifCount > 1 ? ' + ' + ((p.count || 1) * (p.subifCount || 1)) + ' sub-ifs' : ''}`;
            case 'services':
                return `${p.count ?? 1} ${p.serviceType || 'fxc'}, EVI ${p.eviStart ?? 1000}`;
            case 'vrf':
                return `${p.count ?? 1} VRF(s)`;
            case 'bridge-domain':
                return `${p.count ?? 1} BD(s)`;
            case 'flowspec':
                return `Policy ${p.policyName || '?'}`;
            case 'routing-policy':
                return `${p.policyType || 'prefix-list'} ${p.name || '?'}`;
            case 'bgp':
                return `${p.count ?? 1} peer(s), AS ${p.local_as ?? p.peer_as ?? '?'}`;
            case 'igp':
                return `${(p.protocol || 'isis').toUpperCase()} area ${p.area_id ?? '?'}`;
            default:
                return 'Last run';
        }
    },

    _renderLastRunCard(wizardType, deviceId, onRerun, onRerunOther) {
        const rec = this._getLastRunForWizard(wizardType, deviceId);
        if (!rec) return null;
        const summary = this._formatLastRunSummary(rec);
        const ts = rec.timestamp ? new Date(rec.timestamp).toLocaleString() : '';
        const div = document.createElement('div');
        div.className = 'scaler-last-run-card';
        div.innerHTML = `
            <div class="scaler-last-run-header">
                <span class="scaler-last-run-label">Last run</span>
                <span class="scaler-last-run-ts">${ts}</span>
            </div>
            <div class="scaler-last-run-summary">${this.escapeHtml(summary)}</div>
            <div class="scaler-last-run-actions">
                <button type="button" class="scaler-btn scaler-btn-secondary scaler-last-run-btn" data-action="rerun">Re-run with same params</button>
                <button type="button" class="scaler-btn scaler-btn-secondary scaler-last-run-btn" data-action="rerun-other">Re-run on different device</button>
            </div>
        `;
        div.querySelector('[data-action="rerun"]')?.addEventListener('click', () => onRerun?.(rec));
        div.querySelector('[data-action="rerun-other"]')?.addEventListener('click', () => onRerunOther?.(rec));
        return div;
    },

    updateWizardRunResult(jobId, success) {
        const rec = this._wizardHistory.find(r => r.jobId === jobId);
        if (rec) {
            rec.success = success;
            this._saveWizardHistory();
        }
    },

    async getDeviceContext(deviceId) {
        const cached = this._deviceContexts[deviceId];
        if (cached && (Date.now() - (cached._fetchedAt || 0)) < this._contextCacheTTL) {
            return this._applyPendingChanges(deviceId, cached);
        }
        const resolved = this._resolveDeviceId(deviceId);
        const ctx = await ScalerAPI.getDeviceContext(deviceId, false, resolved.sshHost);
        ctx._fetchedAt = Date.now();
        ctx._canvasLabel = deviceId;
        ctx._isDnaas = resolved.isDnaas;
        this._deviceContexts[deviceId] = ctx;
        return this._applyPendingChanges(deviceId, ctx);
    },

    async refreshDeviceContextLive(deviceId, onUpdated) {
        try {
            const resolved = this._resolveDeviceId(deviceId);
            const ctx = await ScalerAPI.getDeviceContext(deviceId, true, resolved.sshHost);
            ctx._fetchedAt = Date.now();
            ctx._canvasLabel = deviceId;
            ctx._isDnaas = resolved.isDnaas;
            this._deviceContexts[deviceId] = ctx;
            const enriched = this._applyPendingChanges(deviceId, ctx);
            if (onUpdated) onUpdated(enriched);
            return enriched;
        } catch (e) {
            if (onUpdated) onUpdated(null, e);
            throw e;
        }
    },

    invalidateDeviceContext(deviceId) {
        delete this._deviceContexts[deviceId];
    },

    recordWizardChange(deviceId, changeType, details, options = {}) {
        this._wizardChangeLog.push({
            deviceId,
            changeType,
            details,
            timestamp: Date.now(),
        });
        if (options.generatedConfig !== undefined || options.jobId !== undefined) {
            const config = options.generatedConfig || '';
            const record = {
                id: typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `wz-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
                deviceId,
                wizardType: changeType,
                params: options.params || details,
                generatedConfig: options.generatedConfig || '',
                configLineCount: config.split('\n').length,
                pushMode: options.pushMode || 'commit',
                success: undefined,
                jobId: options.jobId || null,
                timestamp: Date.now(),
                deviceLabel: deviceId,
            };
            this._wizardHistory.push(record);
            this._saveWizardHistory();
        }
        this.invalidateDeviceContext(deviceId);
    },

    _collectBgpParams() {
        const d = this.WizardController?.data || {};
        const g = (id) => document.getElementById(id);
        const base = {
            local_as: parseInt(g('bgp-local-as')?.value || d.local_as) || 65000,
            peer_as: parseInt(g('bgp-peer-as')?.value || d.peer_as) || 65001,
            peer_ip_start: g('bgp-peer-ip')?.value || d.peer_ip_start || '10.0.0.1',
            count: parseInt(g('bgp-count')?.value || d.count) || 1,
            peer_ip_step: parseInt(g('bgp-peer-ip-step')?.value || d.peer_ip_step) ?? 1,
            peer_as_step: parseInt(g('bgp-peer-as-step')?.value || d.peer_as_step) ?? 0,
        };
        const afEls = document.querySelectorAll('input[name="bgp-af"]:checked');
        const afs = afEls.length ? Array.from(afEls).map(e => e.value) : (d.address_families || ['ipv4-unicast']);
        Object.assign(base, {
            address_families: afs,
            peer_group: g('bgp-peer-group')?.value || d.peer_group || undefined,
            update_source: g('bgp-update-source')?.value || d.update_source || undefined,
            route_reflector_client: (g('bgp-rr-client')?.checked ?? d.route_reflector_client) || false,
            bfd: (g('bgp-bfd')?.checked ?? d.bfd) || false,
            ebgp_multihop: (() => { const v = g('bgp-ebgp-multihop')?.value ?? d.ebgp_multihop; return v ? parseInt(v) : undefined; })(),
            hold_time: (() => { const v = g('bgp-hold-time')?.value ?? d.hold_time; return v ? parseInt(v) : undefined; })(),
            keepalive: (() => { const v = g('bgp-keepalive')?.value ?? d.keepalive; return v ? parseInt(v) : undefined; })(),
            description: g('bgp-description')?.value || d.description || undefined,
            password: g('bgp-password')?.value || d.password || undefined,
        });
        return base;
    },

    _renderValidationResults(errors, warnings, suggestions) {
        if ((!errors || !errors.length) && (!warnings || !warnings.length) && (!suggestions || !suggestions.length))
            return '';
        const items = [];
        (errors || []).forEach((e) => {
            items.push(`<div class="scaler-validation-item scaler-validation-error"><span class="scaler-validation-label">[ERROR]</span> ${e.message}${e.suggestion ? ` <em>${e.suggestion}</em>` : ''}</div>`);
        });
        (warnings || []).forEach((w) => {
            items.push(`<div class="scaler-validation-item scaler-validation-warning"><span class="scaler-validation-label">[WARN]</span> ${w.message}${w.suggestion ? ` <em>${w.suggestion}</em>` : ''}</div>`);
        });
        (suggestions || []).forEach((s) => {
            items.push(`<div class="scaler-validation-item scaler-validation-info"><span class="scaler-validation-label">[INFO]</span> ${s.message}</div>`);
        });
        return `<div class="scaler-validation-box">${items.join('')}</div>`;
    },

    _WIZARD_NAV_ITEMS: [
        { key: 'interface-wizard', label: 'Interfaces', action: 'interface-wizard' },
        { key: 'service-wizard',   label: 'Services',   action: 'service-wizard' },
        { key: 'vrf-wizard',       label: 'VRF',        action: 'vrf-wizard' },
        { key: 'bridge-domain-wizard', label: 'BD',     action: 'bridge-domain-wizard' },
        { key: 'bgp-wizard',       label: 'BGP',        action: 'bgp-wizard' },
        { key: 'igp-wizard',       label: 'IGP',        action: 'igp-wizard' },
        { key: 'flowspec-wizard',  label: 'FlowSpec',   action: 'flowspec-wizard' },
        { key: 'routing-policy-wizard', label: 'Policy', action: 'routing-policy-wizard' },
    ],

    _WIZARD_OPEN_MAP: {
        'interface-wizard':       'openInterfaceWizard',
        'service-wizard':         'openServiceWizard',
        'vrf-wizard':             'openVRFWizard',
        'bridge-domain-wizard':   'openBridgeDomainWizard',
        'bgp-wizard':             'openBGPWizard',
        'igp-wizard':             'openIGPWizard',
        'flowspec-wizard':        'openFlowSpecWizard',
        'routing-policy-wizard':  'openRoutingPolicyWizard',
    },

    _buildWizardQuickNav(activeKey, deviceId) {
        return (data) => {
            const nav = document.createElement('div');
            nav.className = 'scaler-wizard-quicknav';
            const devId = deviceId || data.deviceId || '';
            this._WIZARD_NAV_ITEMS.forEach(item => {
                const btn = document.createElement('button');
                btn.className = 'scaler-quicknav-tab' + (item.key === activeKey ? ' active' : '');
                btn.textContent = item.label;
                if (item.key !== activeKey) {
                    btn.onclick = () => {
                        this.closePanel(activeKey);
                        const openFn = this._WIZARD_OPEN_MAP[item.key];
                        if (devId && openFn && typeof this[openFn] === 'function') {
                            this[openFn](devId);
                        } else {
                            this.handleMenuAction(item.action);
                        }
                    };
                }
                nav.appendChild(btn);
            });
            const menuBtn = document.createElement('button');
            menuBtn.className = 'scaler-quicknav-tab scaler-quicknav-menu';
            menuBtn.textContent = '...';
            menuBtn.title = 'Full menu';
            menuBtn.onclick = () => { this.closePanel(activeKey); this.showScalerMenu(); };
            nav.appendChild(menuBtn);
            return nav;
        };
    },

    /**
     * Build a reusable Push step for wizards.
     * @param {Object} opts - { id, infoText, radioName, includeClipboard }
     * @returns {Object} Step config for WizardController
     */
    _buildPushStep(opts = {}) {
        const id = opts.id || 'push';
        const radioName = opts.radioName || 'push-mode';
        const includeClipboard = opts.includeClipboard === true;
        const infoText = typeof opts.infoText === 'function' ? opts.infoText : (d) => opts.infoText || 'Ready to push configuration.';
        return {
            id,
            title: 'Push',
            finalButtonText: 'Commit Check',
            render: (data) => {
                const ctx = data.deviceContext || {};
                const host = ctx.mgmt_ip || ctx.ip || '';
                const resolved = ctx.resolved_via || '';
                return `
                <div class="scaler-form">
                    <div class="scaler-form-group">
                        <label>Delivery Method</label>
                        <div class="scaler-radio-group">
                            <label class="scaler-radio">
                                <input type="radio" name="${radioName}" value="dry_run" checked>
                                <span><strong>Commit Check First</strong></span>
                            </label>
                            <div class="scaler-radio-desc">Paste config via SSH terminal, run <code>commit check</code>.
                            Nothing is applied. If check passes, you can commit from the result dialog.</div>
                            <label class="scaler-radio">
                                <input type="radio" name="${radioName}" value="merge">
                                <span><strong>Commit Directly</strong></span>
                            </label>
                            <div class="scaler-radio-desc">Paste config via SSH terminal + <code>commit</code>.
                            Use when you've already validated with a commit check.</div>
                            ${includeClipboard ? `
                            <label class="scaler-radio">
                                <input type="radio" name="${radioName}" value="clipboard">
                                <span><strong>Copy to Clipboard + Open SSH</strong></span>
                            </label>
                            <div class="scaler-radio-desc">Copies the full DNOS config to your clipboard and opens
                            an SSH terminal to the device. Paste manually in config mode.</div>
                            ` : ''}
                        </div>
                    </div>
                    <div id="push-target-info" class="scaler-info-box" style="font-size:12px">
                        <strong>Target:</strong> ${data.deviceId}${host ? ` (${host})` : ''}${resolved ? ` -- via ${resolved}` : ''}<br>
                        ${infoText(data)}
                    </div>
                </div>`;
            },
            afterRender: (data) => {
                document.querySelectorAll(`input[name="${radioName}"]`).forEach(r => {
                    r.addEventListener('change', () => {
                        const btn = document.getElementById('wizard-next');
                        const mode = document.querySelector(`input[name="${radioName}"]:checked`)?.value;
                        if (btn) btn.textContent = mode === 'clipboard' ? 'Copy & Open SSH' : mode === 'merge' ? 'Commit' : 'Commit Check';
                    });
                });
            },
            collectData: () => {
                const mode = document.querySelector(`input[name="${radioName}"]:checked`)?.value || 'dry_run';
                return {
                    dryRun: mode === 'dry_run',
                    pushMode: mode
                };
            }
        };
    },

    /**
     * Build a reusable Review step shell (summary table + preview + validation + diff).
     * Caller provides summaryRows HTML and generate logic via afterRender override.
     * @param {Object} opts - { id, previewId, summaryRows, hierarchy }
     * @returns {Object} Step config (render only; afterRender must be provided by caller)
     */
    _buildReviewStep(opts = {}) {
        const id = opts.id || 'review';
        const previewId = opts.previewId || 'config-preview';
        const summaryRows = typeof opts.summaryRows === 'function' ? opts.summaryRows : () => opts.summaryRows || '';
        const hierarchy = opts.hierarchy || 'interface';
        return {
            id,
            title: 'Review',
            render: (data) => `
                <div class="scaler-review">
                    <h4>Configuration Summary</h4>
                    <table class="scaler-table scaler-summary-table">
                        ${summaryRows(data)}
                    </table>
                    <div class="scaler-preview-box">
                        <label>Full DNOS Config Preview:</label>
                        <pre id="${previewId}">Generating preview...</pre>
                    </div>
                    <div id="config-validation"></div>
                    <div class="scaler-diff-section">
                        <button type="button" id="show-diff-btn" class="scaler-btn scaler-btn-secondary">Show diff vs running</button>
                        <pre id="config-diff" class="scaler-diff-preview" style="display:none"></pre>
                    </div>
                </div>`,
            hierarchy
        };
    },

    /**
     * Build an interface selector (text input for comma-separated interface names).
     * @param {Object} opts - { inputId, placeholder, dataKey, label }
     * @returns {Object} { html, collectData }
     */
    _buildInterfaceSelector(opts = {}) {
        const inputId = opts.inputId || 'interface-list';
        const placeholder = opts.placeholder || 'ge100-18/0/0.100, bundle-1.1, ...';
        const dataKey = opts.dataKey || 'interfaceList';
        const label = opts.label || 'Interfaces';
        return {
            html: (data) => `
                <div class="scaler-form-group">
                    <label>${label}</label>
                    <input type="text" id="${inputId}" class="scaler-input" value="${(data[dataKey] || []).join(', ')}" placeholder="${placeholder}">
                </div>`,
            collectData: () => {
                const raw = document.getElementById(inputId)?.value || '';
                const ifaces = raw.split(/[,\s]+/).map(s => s.trim()).filter(Boolean);
                return { [dataKey]: ifaces };
            }
        };
    },

    /**
     * Build an address family selector (checkboxes for BGP-style AFs).
     * @param {Object} opts - { inputName, families, dataKey, defaultAf }
     * @returns {Object} { html, collectData }
     */
    /**
     * Get dependency warnings for a wizard based on device context.
     * @param {string} wizardType - 'vrf'|'flowspec'|'multihoming'|'service'
     * @param {Object} data - Wizard data with deviceContext
     * @returns {string[]} Array of warning messages
     */
    _getWizardDependencyWarnings(wizardType, data) {
        const ctx = data?.deviceContext || {};
        const warnings = [];
        if (wizardType === 'vrf') {
            const subifs = ctx?.interfaces?.subinterface || [];
            if (!subifs.length) {
                warnings.push('VRF typically requires sub-interfaces to attach. Add interfaces first or enter them manually in the Interface Attachment step.');
            }
        }
        if (wizardType === 'flowspec') {
            const policies = ctx?.flowspec_policies || [];
            if (data?.policyName && policies.some(p => (p.name || p) === data.policyName)) {
                warnings.push(`FlowSpec policy "${data.policyName}" already exists. Choose a different name to avoid conflict.`);
            }
        }
        if (wizardType === 'multihoming' && data?.deviceIds?.length === 2) {
            warnings.push('Multihoming requires matching ESI configuration on both devices. Use Compare to verify before sync.');
        }
        return warnings;
    },

    _renderDependencyWarnings(warnings) {
        if (!warnings || !warnings.length) return '';
        return `<div class="scaler-validation-box scaler-dependency-warnings" style="margin-bottom:12px">${warnings.map(w => `<div class="scaler-validation-item scaler-validation-info"><span class="scaler-validation-label">[INFO]</span> ${w}</div>`).join('')}</div>`;
    },

    _buildAddressFamilySelector(opts = {}) {
        const inputName = opts.inputName || 'bgp-af';
        const families = opts.families || ['ipv4-unicast','ipv6-unicast','ipv4-vpn','ipv6-vpn','ipv4-flowspec','ipv6-flowspec','ipv4-flowspec-vpn','ipv6-flowspec-vpn'];
        const dataKey = opts.dataKey || 'address_families';
        const defaultAf = opts.defaultAf || ['ipv4-unicast'];
        return {
            html: (data) => {
                const selected = data[dataKey] || defaultAf;
                return `
                <div class="scaler-form-group">
                    <label>Address Families</label>
                    <div class="scaler-checkbox-group">
                        ${families.map(af => `<label class="scaler-checkbox"><input type="checkbox" name="${inputName}" value="${af}" ${selected.includes(af) ? 'checked' : ''}> ${af}</label>`).join('')}
                    </div>
                </div>`;
            },
            collectData: () => {
                const afEls = document.querySelectorAll(`input[name="${inputName}"]:checked`);
                const afs = Array.from(afEls).map(e => e.value);
                return { [dataKey]: afs.length ? afs : defaultAf };
            }
        };
    },

    getWizardChanges(deviceId) {
        const cutoff = Date.now() - 300000;
        return this._wizardChangeLog.filter(c => c.deviceId === deviceId && c.timestamp > cutoff);
    },

    _applyPendingChanges(deviceId, ctx) {
        const changes = this.getWizardChanges(deviceId);
        if (!changes.length) return ctx;
        const enriched = JSON.parse(JSON.stringify(ctx));
        enriched._pendingChanges = changes.map(c => `${c.changeType}: ${c.details}`);
        for (const change of changes) {
            if (change.changeType === 'interfaces' && change.details) {
                const d = typeof change.details === 'object' ? change.details : {};
                if (d.bundleMembers?.length) {
                    const existing = new Set(enriched.interfaces?.free_physical || []);
                    d.bundleMembers.forEach(m => existing.delete(m));
                    enriched.interfaces.free_physical = [...existing];
                }
                if (d.interfaceType === 'bundle' && d.count && d.startNumber) {
                    const maxNew = d.startNumber + d.count - 1;
                    enriched.next_bundle_number = Math.max(enriched.next_bundle_number || 1, maxNew + 1);
                }
            }
            if (change.changeType === 'services' && change.details) {
                const d = typeof change.details === 'object' ? change.details : {};
                if (d.eviStart && d.count) {
                    const maxNew = d.eviStart + d.count - 1;
                    enriched.services = enriched.services || {};
                    enriched.services.next_evi = Math.max(enriched.services.next_evi || 1000, maxNew + 1);
                    enriched.services.fxc_count = (enriched.services.fxc_count || 0) + d.count;
                }
            }
        }
        return enriched;
    },

    renderSuggestionChips(items, options = {}) {
        const { type = 'default', onSelect, label } = options;
        if (!items || items.length === 0) return '';
        const chips = items.map((item) => {
            const val = typeof item === 'object' ? (item.value ?? item.name ?? item) : item;
            const labelText = typeof item === 'object' ? (item.label ?? item.name ?? val) : val;
            const target = typeof item === 'object' ? item.target : null;
            const cls = `suggestion-chip suggestion-chip--${type}`;
            const dataTarget = target ? ` data-target="${target}"` : '';
            return `<button type="button" class="${cls}" data-value="${String(val).replace(/"/g, '&quot;')}"${dataTarget} title="Click to use">${labelText}</button>`;
        }).join('');
        const container = document.createElement('div');
        container.className = 'suggestion-chips';
        if (label) {
            const lbl = document.createElement('span');
            lbl.className = 'suggestion-chips-label';
            lbl.textContent = label;
            container.appendChild(lbl);
        }
        const wrap = document.createElement('div');
        wrap.className = 'suggestion-chips-wrap';
        wrap.innerHTML = chips;
        container.appendChild(wrap);
        if (onSelect) {
            wrap.querySelectorAll('.suggestion-chip').forEach(btn => {
                btn.onclick = () => onSelect(btn.dataset.value, btn.dataset.target, btn);
            });
        }
        return container;
    },

    renderContextPanel(deviceId, ctx, options = {}) {
        const { onRefresh, collapsed = false } = options;
        const panel = document.createElement('div');
        panel.className = 'device-context-panel' + (collapsed ? ' collapsed' : '');
        const summary = ctx?.config_summary || {};
        const sys = ctx?.system_type || '';
        const asn = summary.as_number || '-';
        const rid = summary.router_id || summary.loopback0_ip || '-';
        const phys = (ctx?.interfaces?.physical || []).length;
        const bundles = (ctx?.interfaces?.bundle || []).length;
        const subifs = (ctx?.interfaces?.subinterface || []).length;
        const freeCount = (ctx?.interfaces?.free_physical || []).length;
        const loopbacks = (ctx?.interfaces?.loopback || []).length;
        const lldp = ctx?.lldp || [];
        const lldpCount = lldp.length;
        const isDnaas = ctx?._isDnaas || false;
        const resolvedVia = ctx?.resolved_via || '';
        const hasData = phys > 0 || bundles > 0 || lldpCount > 0;
        const resolved = this._resolveDeviceId(deviceId);

        const barSegments = [];
        if (phys) barSegments.push(`<span class="ctx-bar-segment ctx-bar-phys">${phys} phys</span>`);
        if (bundles) barSegments.push(`<span class="ctx-bar-segment ctx-bar-bundle">${bundles} bundle</span>`);
        if (loopbacks) barSegments.push(`<span class="ctx-bar-segment ctx-bar-lo">${loopbacks} lo</span>`);
        if (subifs) barSegments.push(`<span class="ctx-bar-segment ctx-bar-subif">${subifs} sub-if</span>`);
        const ifaceBar = barSegments.length ? `<div class="device-context-bar">${barSegments.join('')}</div>` : '';

        const statusClass = !resolved.sshHost ? 'ctx-status-red' : !hasData ? 'ctx-status-orange' : 'ctx-status-green';

        let statusLine = '';
        const resolvedIp = ctx?.resolved_ip || '';
        const displayHost = resolvedIp || resolved.sshHost || '';
        const isLoading = !ctx || (!ctx.resolved_via && !ctx.timestamp);
        if (isLoading) {
            statusLine = '<div class="device-context-row ctx-status-loading">Loading device context...</div>';
        } else if (!resolved.sshHost) {
            statusLine = '<div class="device-context-row ctx-status-red">[WARN] No SSH configured -- right-click device to set SSH address</div>';
        } else if (!hasData) {
            statusLine = `<div class="device-context-row ctx-status-orange">[INFO] No cached data -- click "Refresh Live" to fetch from ${displayHost}</div>`;
        }

        const sysLine = sys || asn !== '-' || rid !== '-' ? `${sys || '-'} | AS ${asn} | RID ${rid}` : '-';
        const lldpChips = !isDnaas && lldp.length > 0
            ? lldp.slice(0, 6).map(n => `<span class="ctx-lldp-chip" title="${n.local} -> ${n.neighbor}">${n.local}</span>`).join('')
            : '';

        panel.innerHTML = `
            <div class="device-context-header">
                <span class="device-context-toggle">${collapsed ? '+' : '-'}</span>
                <span class="device-context-title">Device Context: ${deviceId}${displayHost ? ' (' + displayHost + ')' : ''}</span>
                <span class="device-context-status ${statusClass}"></span>
            </div>
            <div class="device-context-body">
                ${statusLine}
                <div class="device-context-row device-context-compact">${sysLine}</div>
                ${ifaceBar}
                ${lldpChips ? `<div class="device-context-row"><span class="ctx-lldp-label">LLDP:</span><span class="ctx-lldp-chips">${lldpChips}${lldpCount > 6 ? ` <span class="ctx-lldp-more">+${lldpCount - 6}</span>` : ''}</span></div>` : (isDnaas ? '<div class="device-context-row" style="opacity:0.5">DNAAS device -- LLDP skipped</div>' : '')}
                ${freeCount ? `<div class="device-context-row" style="font-size:11px;opacity:0.7">${freeCount} free physical</div>` : ''}
                ${(ctx?._pendingChanges?.length) ? `<div class="device-context-row device-context-pending">[PENDING] ${ctx._pendingChanges.length} change(s) from other wizards</div>` : ''}
                ${resolvedVia ? `<div class="device-context-row" style="font-size:10px;opacity:0.4">Resolved: ${resolvedVia}</div>` : ''}
                ${onRefresh ? '<button type="button" class="scaler-btn scaler-btn-sm" id="ctx-refresh-live">Refresh Live</button>' : ''}
            </div>
        `;
        const toggle = panel.querySelector('.device-context-toggle');
        const body = panel.querySelector('.device-context-body');
        if (toggle) {
            toggle.onclick = () => {
                panel.classList.toggle('collapsed');
                toggle.textContent = panel.classList.contains('collapsed') ? '+' : '-';
            };
        }
        const refreshBtn = panel.querySelector('#ctx-refresh-live');
        if (refreshBtn && onRefresh) {
            refreshBtn.onclick = async () => {
                refreshBtn.disabled = true;
                refreshBtn.textContent = 'Refreshing...';
                try {
                    await onRefresh();
                } finally {
                    refreshBtn.disabled = false;
                    refreshBtn.textContent = 'Refresh Live';
                }
            };
        }
        return panel;
    },

    // =========================================================================
    // INITIALIZATION
    // =========================================================================
    
    init() {
        console.log('[ScalerGUI] Initializing v2.0...');
        this._loadWizardHistory();
        this.createPanelContainer();
        this.bindKeyboardShortcuts();
        this.addScalerButton();
        this._setupTopologyChangeListener();
        console.log('[ScalerGUI] Ready');
    },
    _isDnaasDevice(name) {
        if (!name) return false;
        const u = name.toUpperCase();
        const patterns = ['DNAAS', 'LEAF', 'SPINE', 'FABRIC', 'TOR', 'AGGREGATION', 'AGG-', 'CORE-', '-LEAF', '-SPINE', 'NCM', 'NCF', 'NCC', 'SUPERSPINE'];
        return patterns.some(p => u.includes(p));
    },
    _getCanvasDeviceObjects(includeDnaas = false) {
        const editor = window.topologyEditor;
        if (!editor?.objects) return [];
        return editor.objects
            .filter(o => o.type === 'device' && o.label?.trim())
            .filter(o => includeDnaas || !this._isDnaasDevice(o.label))
            .map(o => ({
                label: o.label.trim(),
                sshHost: o.sshConfig?.host || '',
                sshUser: o.sshConfig?.user || '',
                sshPassword: o.sshConfig?.password || '',
                serial: o.deviceSerial || '',
                isDnaas: this._isDnaasDevice(o.label),
            }));
    },
    _getCanvasDevices(includeDnaas = false) {
        return this._getCanvasDeviceObjects(includeDnaas).map(d => d.label);
    },
    _resolveDeviceId(label) {
        const devs = this._getCanvasDeviceObjects(true);
        const dev = devs.find(d => d.label === label);
        return {
            label,
            sshHost: dev?.sshHost || '',
            sshUser: dev?.sshUser || '',
            sshPassword: dev?.sshPassword || '',
            serial: dev?.serial || '',
            isDnaas: dev?.isDnaas || false,
        };
    },
    _setupTopologyChangeListener() {
        const trySubscribe = () => {
            const editor = window.topologyEditor;
            if (editor?.events?.on && !this._topologyListenerSetup) {
                this._topologyListenerSetup = true;
                editor.events.on('topology:loaded', () => {
                    if (this.state.activePanels['device-manager']) {
                        this.refreshDeviceList();
                    }
                });
            }
        };
        trySubscribe();
        if (!this._topologyListenerSetup) setTimeout(trySubscribe, 800);
    },
    
    createPanelContainer() {
        if (document.getElementById('scaler-panel-container')) {
            this.panelContainer = document.getElementById('scaler-panel-container');
            return;
        }
        
        const container = document.createElement('div');
        container.id = 'scaler-panel-container';
        container.className = 'scaler-panel-container';
        document.body.appendChild(container);
        this.panelContainer = container;
    },
    
    bindKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.state.activePanel) {
                this.closePanel(this.state.activePanel);
            }
            if (e.ctrlKey && e.shiftKey && e.key === 'D') {
                e.preventDefault();
                this.openDeviceManager();
            }
            if (e.ctrlKey && e.shiftKey && e.key === 'S') {
                e.preventDefault();
                this.openScalerMenu();
            }
        });
    },
    
    addScalerButton() {
        // ENHANCED: Use the existing cloud-styled CONFIG button from index.html
        // instead of creating a duplicate button
        const existingBtn = document.getElementById('btn-scaler-config');
        if (existingBtn) {
            // Hook into the existing cloud-styled button
            existingBtn.onclick = () => this.openScalerMenu();
            return;
        }
        
        // Fallback: If the cloud button doesn't exist, wait and retry
        const topBar = document.querySelector('.top-bar') || document.querySelector('#top-bar');
        if (!topBar) {
            setTimeout(() => this.addScalerButton(), 1000);
            return;
        }
        
        // Only create button if neither exists (backward compatibility)
        if (document.getElementById('scaler-menu-btn')) return;
        
        const btn = document.createElement('button');
        btn.id = 'scaler-menu-btn';
        btn.className = 'top-bar-btn scaler-btn-primary';
        btn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
            </svg>
            <span>CONFIG</span>
        `;
        btn.onclick = () => this.openScalerMenu();
        topBar.appendChild(btn);
    },
    
    // =========================================================================
    // PANEL MANAGEMENT
    // =========================================================================
    
    openPanel(name, title, content, options = {}) {
        if (!this.state.panelHistory) {
            this.state.panelHistory = [];
        }
        
        if (options.parentPanel && !this.state.panelHistory.find(h => h.current === name)) {
            this.state.panelHistory.push({
                parent: options.parentPanel,
                current: name
            });
        }
        
        if (this.state.activePanels[name]) {
            this.closePanel(name, true);
        }
        
        const panel = document.createElement('div');
        panel.id = `scaler-panel-${name}`;
        panel.className = `scaler-panel ${options.className || ''}`;
        
        // Ensure panel width doesn't exceed viewport
        const requestedWidth = parseInt(options.width) || 450;
        const maxWidth = window.innerWidth - 30; // 30px margin
        const actualWidth = Math.min(requestedWidth, maxWidth);
        panel.style.width = actualWidth + 'px';
        panel.dataset.parentPanel = options.parentPanel || '';
        
        const hasParent = options.parentPanel || this.state.panelHistory.find(h => h.current === name);
        this.state.lastPanel = name;
        this.updateButtonStates();
        
        const header = document.createElement('div');
        header.className = 'scaler-panel-header';
        header.innerHTML = `
            <h3>${title}</h3>
            <div class="scaler-panel-actions">
                ${options.minimizable ? '<button class="scaler-btn-icon" data-action="minimize" title="Minimize">_</button>' : ''}
                ${hasParent ? `
                <button class="scaler-btn-icon scaler-btn-back" data-action="back" title="Back">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/>
                    </svg>
                </button>` : ''}
                <button class="scaler-btn-icon scaler-btn-close" data-action="close" title="Close">×</button>
            </div>
        `;
        
        const backBtn = header.querySelector('[data-action="back"]');
        if (backBtn) {
            backBtn.onclick = () => this.navigateBack(name);
        }
        
        header.querySelector('[data-action="close"]').onclick = () => this.closePanel(name);
        
        const minimizeBtn = header.querySelector('[data-action="minimize"]');
        if (minimizeBtn) {
            minimizeBtn.onclick = () => this.minimizePanel(name);
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'scaler-panel-content';
        if (typeof content === 'string') {
            contentDiv.innerHTML = content;
        } else {
            contentDiv.appendChild(content);
        }
        
        panel.appendChild(header);
        panel.appendChild(contentDiv);
        this.panelContainer.appendChild(panel);
        
        this.state.activePanels[name] = panel;
        this.state.activePanel = name;
        
        // Ensure panel fits in viewport before animation
        const viewportWidth = window.innerWidth;
        if (actualWidth > viewportWidth - 20) {
            panel.style.width = (viewportWidth - 20) + 'px';
        }
        
        requestAnimationFrame(() => {
            panel.classList.add('scaler-panel-open');
            
            // Double-check positioning after animation frame
            requestAnimationFrame(() => {
                const panelRect = panel.getBoundingClientRect();
                
                // If panel still overflows, adjust width
                if (panelRect.right > viewportWidth - 10) {
                    const newWidth = viewportWidth - panelRect.left - 10;
                    if (newWidth > 200) { // Minimum width
                        panel.style.width = newWidth + 'px';
                    }
                }
            });
        });
        
        return panel;
    },
    
    closePanel(name, silent = false) {
        const panel = this.state.activePanels[name];
        if (!panel) return;
        
        if (!silent && this.state.panelHistory) {
            this.state.panelHistory = this.state.panelHistory.filter(h => h.current !== name);
        }
        
        panel.classList.remove('scaler-panel-open');
        panel.classList.add('scaler-panel-closing');
        
        setTimeout(() => {
            panel.remove();
            delete this.state.activePanels[name];
            if (this.state.activePanel === name) {
                this.state.activePanel = null;
            }
            this.updateButtonStates();
        }, 300);
    },
    
    closeAllPanels() {
        this.state.panelHistory = [];
        Object.keys(this.state.activePanels).forEach(name => {
            this.closePanel(name);
        });
    },
    
    navigateBack(currentName) {
        const historyEntry = this.state.panelHistory?.find(h => h.current === currentName);
        
        if (historyEntry && historyEntry.parent) {
            this.closePanel(currentName, true);
            this.state.panelHistory = this.state.panelHistory.filter(h => h.current !== currentName);
            this.reopenPanel(historyEntry.parent);
        } else {
            const panel = this.state.activePanels[currentName];
            const parentName = panel?.dataset?.parentPanel;
            
            if (parentName) {
                this.closePanel(currentName, true);
                this.reopenPanel(parentName);
            } else {
                this.closePanel(currentName, true);
                this.showScalerMenu();
            }
        }
    },
    
    reopenPanel(name) {
        const panelMap = {
            'scaler-menu': () => this.showScalerMenu(),
            'wizard-history': () => this.openWizardHistoryPanel(),
            'device-manager': () => this.openDeviceManager(),
            'interface-wizard': () => this.openInterfaceWizard(),
            'service-wizard': () => this.openServiceWizard(),
            'vrf-wizard': () => this.openVRFWizard(),
            'bridge-domain-wizard': () => this.openBridgeDomainWizard(),
            'flowspec-wizard': () => this.openFlowSpecWizard(),
            'routing-policy-wizard': () => this.openRoutingPolicyWizard(),
            'multihoming-wizard': () => this.openMultihomingWizard(),
            'mirror-wizard': () => this.openMirrorWizard(),
            'upgrade-wizard': () => this.openUpgradeWizard(),
            'scale-wizard': () => this.openScaleWizard(),
            'device-compare': () => this.openDeviceCompare(),
            'batch-operations': () => this.openBatchOperations()
        };
        
        const fn = panelMap[name];
        if (fn) fn();
        else this.showScalerMenu();
    },
    
    updateButtonStates() {
        const scalerBtn = document.getElementById('scaler-menu-btn');
        const hasScalerPanels = Object.keys(this.state.activePanels).length > 0;
        
        if (scalerBtn) {
            if (hasScalerPanels) {
                scalerBtn.classList.add('scaler-btn-active');
        } else {
                scalerBtn.classList.remove('scaler-btn-active');
            }
        }
    },
    
    minimizePanel(name) {
        const panel = this.state.activePanels[name];
        if (!panel) return;
        panel.classList.toggle('scaler-panel-minimized');
    },
    
    // =========================================================================
    // MAIN MENU
    // =========================================================================
    
    openScalerMenu() {
        if (Object.keys(this.state.activePanels).length > 0) {
            this.state.lastOpenPanel = this.state.lastPanel;
            this.closeAllPanels();
            return;
        }
        
        if (this.state.lastOpenPanel && this.state.lastOpenPanel !== 'scaler-menu') {
            const lastPanel = this.state.lastOpenPanel;
            this.state.lastOpenPanel = null;
            this.reopenPanel(lastPanel);
            return;
        }
        
        this.showScalerMenu();
    },
    
    showScalerMenu() {
        const content = document.createElement('div');
        content.className = 'scaler-menu';
        content.innerHTML = `
            <div class="scaler-menu-section">
                <h4>Device Management</h4>
                <button class="scaler-menu-btn" data-action="device-manager">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="2" y="3" width="20" height="14" rx="2"/>
                        <path d="M8 21h8"/><path d="M12 17v4"/>
                    </svg>
                    Device Manager
                    <span class="scaler-menu-hint">View & manage devices</span>
                </button>
                <button class="scaler-menu-btn" data-action="sync-all">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 2v6h-6"/><path d="M3 12a9 9 0 0 1 15-6.7L21 8"/>
                        <path d="M3 22v-6h6"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/>
                    </svg>
                    Sync All Devices
                    <span class="scaler-menu-hint">Fetch configs from all</span>
                </button>
                <button class="scaler-menu-btn" data-action="quick-load">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <path d="M14 2v6h6"/><path d="M12 18v-6"/><path d="M9 15h6"/>
                    </svg>
                    Quick Load Saved Configs
                    <span class="scaler-menu-hint">Load previous configs</span>
                </button>
            </div>
            
            <div class="scaler-menu-section">
                <h4>Configuration Wizards</h4>
                <button class="scaler-menu-btn" data-action="interface-wizard">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M4 4h6v6H4z"/><path d="M14 4h6v6h-6z"/>
                        <path d="M4 14h6v6H4z"/><path d="M14 14h6v6h-6z"/>
                    </svg>
                    Interface Wizard
                    <span class="scaler-menu-hint">Create scaled interfaces</span>
                </button>
                <button class="scaler-menu-btn" data-action="service-wizard">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                        <path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
                    </svg>
                    Service Wizard
                    <span class="scaler-menu-hint">FXC, VPLS, L3VPN</span>
                </button>
                <button class="scaler-menu-btn" data-action="vrf-wizard">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/>
                    </svg>
                    VRF / L3VPN
                    <span class="scaler-menu-hint">VRF instances, BGP, RTs</span>
                </button>
                <button class="scaler-menu-btn" data-action="bridge-domain-wizard">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2v4"/><path d="M12 18v4"/><path d="M4.93 4.93l2.83 2.83"/><path d="M16.24 16.24l2.83 2.83"/><path d="M2 12h4"/><path d="M18 12h4"/><path d="M4.93 19.07l2.83-2.83"/><path d="M16.24 7.76l2.83-2.83"/><circle cx="12" cy="12" r="3"/>
                    </svg>
                    Bridge Domain
                    <span class="scaler-menu-hint">BD instances, storm control</span>
                </button>
                <button class="scaler-menu-btn" data-action="bgp-wizard">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="5" r="3"/><circle cx="5" cy="19" r="3"/><circle cx="19" cy="19" r="3"/>
                        <path d="M12 8v4"/><path d="M8 16l4-4 4 4"/>
                    </svg>
                    BGP Configuration
                    <span class="scaler-menu-hint">Neighbors & address families</span>
                </button>
                <button class="scaler-menu-btn" data-action="igp-wizard">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="12,2 2,22 22,22"/>
                    </svg>
                    IGP Configuration
                    <span class="scaler-menu-hint">ISIS / OSPF</span>
                </button>
                <button class="scaler-menu-btn" data-action="flowspec-wizard">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/>
                    </svg>
                    FlowSpec Local
                    <span class="scaler-menu-hint">Local policies, match-class, actions</span>
                </button>
                <button class="scaler-menu-btn" data-action="routing-policy-wizard">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>
                    </svg>
                    Routing Policy
                    <span class="scaler-menu-hint">Prefix-list, route-policy (new syntax)</span>
                </button>
                <button class="scaler-menu-btn" data-action="multihoming-wizard">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M12 2v20"/><path d="M2 12h20"/>
                    </svg>
                    Multihoming Wizard
                    <span class="scaler-menu-hint">Sync ESI across PEs</span>
                </button>
                <button class="scaler-menu-btn" data-action="mirror-wizard">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M21 8V5a2 2 0 0 0-2-2h-3"/>
                        <path d="M3 16v3a2 2 0 0 0 2 2h3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/>
                    </svg>
                    Mirror Config
                    <span class="scaler-menu-hint">Copy config from source to target PE</span>
                </button>
            </div>
            
            <div class="scaler-menu-section">
                <h4>History</h4>
                <button class="scaler-menu-btn" data-action="wizard-history">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
                    </svg>
                    Wizard Run History
                    <span class="scaler-menu-hint">Recent wizard runs, re-run</span>
                </button>
            </div>
            
            <div class="scaler-menu-section">
                <h4>Operations</h4>
                <button class="scaler-menu-btn scaler-commits-btn" data-action="commits-panel">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                    </svg>
                    Commits
                    <span class="scaler-menu-hint">Track config pushes</span>
                    <span class="scaler-commits-badge" id="scaler-commits-badge" style="display:none">0</span>
                </button>
                <button class="scaler-menu-btn" data-action="compare">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 8h-7"/><path d="M18 12h-10"/><path d="M18 16h-7"/>
                        <path d="M3 8l3 3-3 3"/>
                    </svg>
                    Compare Configs
                    <span class="scaler-menu-hint">Diff between devices</span>
                </button>
                <button class="scaler-menu-btn" data-action="sync-status">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                        <path d="M22 4L12 14.01l-3-3"/>
                    </svg>
                    Sync Status Analysis
                    <span class="scaler-menu-hint">RT & MH comparison</span>
                </button>
                <button class="scaler-menu-btn" data-action="delete">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
                        <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                    Delete Hierarchy
                    <span class="scaler-menu-hint">Remove config sections</span>
                </button>
                <button class="scaler-menu-btn" data-action="modify-interfaces">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                                </svg>
                    Modify Service Interfaces
                    <span class="scaler-menu-hint">Add/remove/remap</span>
                            </button>
                <button class="scaler-menu-btn" data-action="scale-wizard">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 20V10"/><path d="M18 20V4"/><path d="M6 20v-4"/>
                                </svg>
                    Scale Up/Down
                    <span class="scaler-menu-hint">Bulk service operations</span>
                            </button>
                <button class="scaler-menu-btn" data-action="stag-check">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                        <path d="M3 9h18"/><path d="M9 21V9"/>
                                </svg>
                    Stag Pool Check
                    <span class="scaler-menu-hint">QinQ Stag usage</span>
                            </button>
                        </div>
            
            <div class="scaler-menu-section">
                <h4>System</h4>
                <button class="scaler-menu-btn" data-action="upgrade-wizard">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <path d="M17 8l-5-5-5 5"/><path d="M12 3v12"/>
                    </svg>
                    Image Upgrade
                    <span class="scaler-menu-hint">DNOS/GI/BaseOS from Jenkins</span>
                    </button>
                <button class="scaler-menu-btn" data-action="batch">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
                        <rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>
                    </svg>
                    Batch Operations
                    <span class="scaler-menu-hint">Multi-device actions</span>
                    </button>
                <button class="scaler-menu-btn" data-action="templates">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <path d="M14 2v6h6"/><path d="M12 18v-6"/><path d="M9 15h6"/>
                    </svg>
                    Config Templates
                    <span class="scaler-menu-hint">Save & reuse configs</span>
                    </button>
                <button class="scaler-menu-btn" data-action="xray-settings" style="border-top: 1px solid rgba(255,255,255,0.08); margin-top: 4px; padding-top: 10px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/>
                    </svg>
                    XRAY Settings
                    <span class="scaler-menu-hint">Mac, credentials, Wireshark</span>
                </button>
                </div>
            `;
            
            content.querySelectorAll('[data-action]').forEach(btn => {
                btn.onclick = () => {
                    const action = btn.dataset.action;
                    this.closePanel('scaler-menu');
                    this.handleMenuAction(action);
                };
            });

            (async () => {
                try {
                    const health = await ScalerAPI.checkHealth();
                    const bridgeDown = health?.scaler_bridge && health.scaler_bridge.status !== 'ok';
                    if (bridgeDown) return;
                    const r = await ScalerAPI.getJobs();
                    const active = (r.jobs || []).filter((j) => j.status === 'running' || j.status === 'pending').length;
                    const badge = content.querySelector('#scaler-commits-badge');
                    if (badge) {
                        badge.style.display = active > 0 ? 'inline' : 'none';
                        badge.textContent = active;
                    }
                } catch (_) {}
            })();

        this.openPanel('scaler-menu', 'CONFIG Menu', content, {width: '320px'});
    },
    
    handleMenuAction(action) {
        const actionMap = {
            'device-manager': () => this.openDeviceManager(),
            'sync-all': () => this.syncAllDevices(),
            'quick-load': () => this.openQuickLoad(),
            'interface-wizard': () => this.openDeviceSelector('Interface Wizard', (id) => this.openInterfaceWizard(id)),
            'service-wizard': () => this.openDeviceSelector('Service Wizard', (id) => this.openServiceWizard(id)),
            'vrf-wizard': () => this.openDeviceSelector('VRF / L3VPN Wizard', (id) => this.openVRFWizard(id)),
            'bridge-domain-wizard': () => this.openDeviceSelector('Bridge Domain Wizard', (id) => this.openBridgeDomainWizard(id)),
            'flowspec-wizard': () => this.openDeviceSelector('FlowSpec Wizard', (id) => this.openFlowSpecWizard(id)),
            'routing-policy-wizard': () => this.openDeviceSelector('Routing Policy Wizard', (id) => this.openRoutingPolicyWizard(id)),
            'multihoming-wizard': () => this.openMultihomingWizard(),
            'mirror-wizard': () => this.openMirrorWizard(),
            'bgp-wizard': () => this.openDeviceSelector('BGP Configuration', (id) => this.openBGPWizard(id)),
            'igp-wizard': () => this.openDeviceSelector('IGP Configuration', (id) => this.openIGPWizard(id)),
            'wizard-history': () => this.openWizardHistoryPanel(),
            'commits-panel': () => this.openCommitsPanel(),
            'compare': () => this.openDeviceCompare(),
            'sync-status': () => this.openSyncStatus(),
            'delete': () => this.openDeviceSelector('Delete Hierarchy', (id) => this.openDeleteHierarchy(id)),
            'modify-interfaces': () => this.openModifyInterfaces(),
            'scale-wizard': () => this.openScaleWizard(),
            'stag-check': () => this.openStagCheck(),
            'upgrade-wizard': () => this.openUpgradeWizard(),
            'batch': () => this.openBatchOperations(),
            'templates': () => this.openTemplateManager(),
            'xray-settings': () => this.openXraySettings()
        };
        
        const fn = actionMap[action];
        if (fn) fn();
    },
    
    // =========================================================================
    // XRAY SETTINGS
    // =========================================================================

    openXraySettings() {
        const content = document.createElement('div');
        content.innerHTML = '<div class="scaler-loading">Loading XRAY config...</div>';
        this.openPanel('xray-settings', 'XRAY Settings', content, { width: '360px' });

        fetch('/api/xray/config').then(r => r.json()).then(cfg => {
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
                fetch('/api/xray/config', {
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
                fetch('/api/xray/verify-mac', {
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

    // =========================================================================
    // INTERFACE WIZARD (6 Steps)
    // =========================================================================
    
    async openInterfaceWizard(deviceId = null, prefillParams = null) {
        if (!deviceId) {
            this.openDeviceSelector('Interface Wizard', (id) => this.openInterfaceWizard(id, prefillParams));
            return;
        }
        
        const content = document.createElement('div');
        content.innerHTML = '<div class="scaler-loading">Loading...</div>';
        
        this.openPanel('interface-wizard', `Interface Wizard - ${deviceId}`, content, {
            width: '550px',
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
                        const nextBundle = ctx.next_bundle_number ?? 1;
                        const t = data.interfaceType || 'bundle';
                        const startVal = t === 'bundle' ? nextBundle : t === 'loopback' ? (data.startNumber ?? 0) : (data.startNumber || 1);
                        const parentCount = (() => {
                            const ctx2 = data.deviceContext || {};
                            const phys = (ctx2.interfaces?.physical || []).filter(p => p.oper === 'up');
                            const bun = ctx2.interfaces?.bundle || [];
                            return phys.length + bun.length;
                        })();
                        const subifDefault = data.interfaceType === undefined && parentCount > 0;
                        const sel = subifDefault ? 'subif' : (data.interfaceType || 'bundle');
                        return `
                        <div class="scaler-form">
            <div class="scaler-form-group">
                <label>Interface Type</label>
                <div class="scaler-type-options" id="iface-type-options">
                    <label class="scaler-type-option ${sel === 'subif' ? 'option-active' : ''}" data-type="subif">
                        <input type="radio" name="iface-type" value="subif" ${sel === 'subif' ? 'checked' : ''}>
                        <span class="option-title">Sub-interface</span>
                        <span class="option-desc">Create sub-interfaces on existing oper-up parents${parentCount ? ` (${parentCount} available)` : ''}</span>
                    </label>
                    <label class="scaler-type-option ${sel === 'bundle' ? 'option-active' : ''}" data-type="bundle">
                        <input type="radio" name="iface-type" value="bundle" ${sel === 'bundle' ? 'checked' : ''}>
                        <span class="option-title">Bundle (LAG)</span>
                        <span class="option-desc">Logical aggregation of physical ports</span>
                    </label>
                    <label class="scaler-type-option ${sel === 'ph' ? 'option-active' : ''}" data-type="ph">
                        <input type="radio" name="iface-type" value="ph" ${sel === 'ph' ? 'checked' : ''}>
                        <span class="option-title">ph (PWHE)</span>
                        <span class="option-desc">Pseudo-wire head-end (phN parents + phN.Y sub-ifs)</span>
                    </label>
                    <label class="scaler-type-option ${sel === 'irb' ? 'option-active' : ''}" data-type="irb">
                        <input type="radio" name="iface-type" value="irb" ${sel === 'irb' ? 'checked' : ''}>
                        <span class="option-title">IRB</span>
                        <span class="option-desc">Integrated Routing and Bridging (irb.N for bridge routing)</span>
                    </label>
                    <label class="scaler-type-option ${sel === 'loopback' ? 'option-active' : ''}" data-type="loopback">
                        <input type="radio" name="iface-type" value="loopback" ${sel === 'loopback' ? 'checked' : ''}>
                        <span class="option-title">Loopback</span>
                        <span class="option-desc">Loopback interfaces (lo0/lo1 for router-id, BGP)</span>
                    </label>
                </div>
            </div>
            <div id="iface-numbering" style="display:${sel === 'subif' ? 'none' : 'block'}">
            <div class="scaler-form-row">
                <div class="scaler-form-group">
                    <label>Start Number</label>
                                    <input type="number" id="iface-start" class="scaler-input" value="${startVal}" min="1">
                </div>
                <div class="scaler-form-group">
                    <label>Count</label>
                                    <input type="number" id="iface-count" class="scaler-input" value="${data.count || 10}" min="1" max="1000">
                </div>
            </div>
            </div>
            <div id="iface-type-suggestions"></div>
                            <div class="scaler-preview-box" id="iface-type-preview-box" style="display:${sel === 'subif' ? 'none' : 'block'}">
                                <label>DNOS SYNTAX PREVIEW:</label>
                                <pre id="iface-type-preview" class="scaler-syntax-preview">Loading...</pre>
                            </div>
                        </div>
                    `;
                    },
                    afterRender: (data) => {
                        let debounceTimer;
                        const getType = () => document.querySelector('input[name="iface-type"]:checked')?.value || 'bundle';
                        const toggleNumbering = (type) => {
                            const numBlock = document.getElementById('iface-numbering');
                            const prevBox = document.getElementById('iface-type-preview-box');
                            const isSubif = type === 'subif';
                            if (numBlock) numBlock.style.display = isSubif ? 'none' : 'block';
                            if (prevBox) prevBox.style.display = isSubif ? 'none' : 'block';
                        };
                        const updatePreview = async () => {
                            clearTimeout(debounceTimer);
                            debounceTimer = setTimeout(async () => {
                                const type = getType();
                                if (type === 'subif') return;
                                const start = parseInt(document.getElementById('iface-start')?.value) || 1;
                                const count = Math.min(parseInt(document.getElementById('iface-count')?.value) || 10, 3);
                                const preview = document.getElementById('iface-type-preview');
                                if (preview) {
                                    try {
                                        const result = await ScalerAPI.generateInterfaces({
                                            interface_type: type,
                                            start_number: start,
                                            count: count,
                                            create_subinterfaces: false
                                        });
                                        const actualCount = parseInt(document.getElementById('iface-count')?.value) || 10;
                                        const lines = result.config.split('\n').slice(0, 12);
                                        preview.textContent = lines.join('\n') + (actualCount > 3 ? `\n... (${actualCount} interfaces total)` : '');
                                    } catch (e) {
                                        preview.textContent = `Error: ${e.message}`;
                                    }
                                }
                            }, 300);
                        };
                        const typeOptions = document.getElementById('iface-type-options');
                        if (typeOptions) {
                            typeOptions.querySelectorAll('.scaler-type-option').forEach(opt => {
                                opt.addEventListener('click', () => {
                                    typeOptions.querySelectorAll('.scaler-type-option').forEach(o => o.classList.remove('option-active'));
                                    opt.classList.add('option-active');
                                    const type = getType();
                                    toggleNumbering(type);
                                    if (type !== 'subif') updatePreview();
                                    const ctx = ScalerGUI.WizardController.data.deviceContext;
                                    const sugg = document.getElementById('iface-type-suggestions');
                                    if (sugg) {
                                        sugg.innerHTML = '';
                                        if (type === 'bundle' && ctx?.next_bundle_number) {
                                            const chip = ScalerGUI.renderSuggestionChips(
                                                [{ value: ctx.next_bundle_number, label: `bundle-${ctx.next_bundle_number}` }],
                                                { type: 'smart', onSelect: (v) => { document.getElementById('iface-start').value = v; updatePreview(); } }
                                            );
                                            sugg.appendChild(chip);
                                        }
                                    }
                                });
                            });
                        }
                        document.querySelectorAll('input[name="iface-type"]').forEach(radio => {
                            radio.addEventListener('change', () => { toggleNumbering(getType()); updatePreview(); });
                        });
                        document.getElementById('iface-start')?.addEventListener('input', updatePreview);
                        document.getElementById('iface-count')?.addEventListener('input', updatePreview);
                        const type = getType();
                        toggleNumbering(type);
                        const ctx = data.deviceContext;
                        const sugg = document.getElementById('iface-type-suggestions');
                        if (sugg && type === 'bundle' && ctx?.next_bundle_number) {
                            const chip = ScalerGUI.renderSuggestionChips(
                                [{ value: ctx.next_bundle_number, label: `bundle-${ctx.next_bundle_number}` }],
                                { type: 'smart', onSelect: (v) => { document.getElementById('iface-start').value = v; updatePreview(); } }
                            );
                            sugg.appendChild(chip);
                        }
                        if (type !== 'subif') updatePreview();
                    },
                    collectData: () => {
                        const type = document.querySelector('input[name="iface-type"]:checked')?.value || 'bundle';
                        if (type === 'subif') return { interfaceType: 'subif', startNumber: 1, count: 1 };
                        return {
                            interfaceType: type,
                            startNumber: parseInt(document.getElementById('iface-start')?.value) || 1,
                            count: parseInt(document.getElementById('iface-count')?.value) || 10
                        };
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
                    id: 'location',
                    title: 'Port Location',
                    skipIf: () => true,
                    render: () => '<div></div>',
                    collectData: () => ({})
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
                    afterRender: (data) => {
                        const chips = document.querySelectorAll('#parent-bundles .suggestion-chip, #parent-physical .suggestion-chip');
                        const display = document.getElementById('parent-selected-display');
                        const input = document.getElementById('parent-selected-input');
                        const selected = new Set(data.subifParents || []);

                        const updateDisplay = () => {
                            const arr = [...selected];
                            if (display) display.textContent = arr.length ? arr.join(', ') : 'None -- click interfaces above';
                            if (input) input.value = arr.join(',');
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
                        const t = (ScalerGUI.WizardController.data?.interfaceType || 'bundle');
                        if (t === 'loopback') return 'IP & Description';
                        if (t === 'subif') return 'Mode & Features';
                        return 'Sub-ifs & IP';
                    },
                    render: (data) => {
                        const t = data.interfaceType || 'bundle';
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
                            </div>` : ''}
                            <div id="ip-section" style="display:${isPhysical && data.interfaceMode === 'l2' ? 'none' : 'block'}">
                                <div class="scaler-form-group" style="margin-top:12px">
                                    <label>IP Addressing</label>
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
                                        <label>IP Step Mode</label>
                                        ${(() => { const p = data.ipPrefix || defaultPrefix; const autoUnique = !data.ipMode && p <= 30; const mode = data.ipMode || (autoUnique ? 'unique_subnet' : 'per_subif'); return `
                                        <div class="scaler-radio-group">
                                            <label class="scaler-radio"><input type="radio" name="ip-mode" value="per_subif" ${mode === 'per_subif' ? 'checked' : ''}><span>Per sub-interface (10.0.0.1, .2, .3...)</span></label>
                                            <label class="scaler-radio"><input type="radio" name="ip-mode" value="per_parent" ${mode === 'per_parent' ? 'checked' : ''}><span>Per parent (10.0.1.x, 10.0.2.x...)</span></label>
                                            <label class="scaler-radio"><input type="radio" name="ip-mode" value="unique_subnet" ${mode === 'unique_subnet' ? 'checked' : ''}><span>Unique subnet (step by /prefix size)</span></label>
                                        </div>`; })()}
                                    </div>
                                    ${(() => { const p = data.ipPrefix || defaultPrefix; const autoUnique = !data.ipMode && p <= 30; const mode = data.ipMode || (autoUnique ? 'unique_subnet' : 'per_subif'); const autoStep = Math.pow(2, 32 - p); return `
                                    <div id="ip-step-row" class="scaler-form-group" style="display:${mode === 'unique_subnet' ? 'block' : 'none'}">
                                        <label>IP Step (for unique subnet)</label>
                                        <input type="number" id="ip-step" class="scaler-input" value="${data.ipStep || autoStep}" min="1" max="256">
                                        <div class="scaler-info-box" style="font-size:10px;margin-top:4px">Step between subnets. /31 -> 2, /30 -> 4, /29 -> 8</div>
                                    </div>`; })()}
                                    <div id="ip-validation-warning" class="scaler-info-box" style="display:none;color:var(--dn-orange,#e67e22);border-color:var(--dn-orange,#e67e22);margin-top:8px"></div>
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
                        const t = data.interfaceType || 'bundle';
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
                                ip_mode: document.querySelector('input[name="ip-mode"]:checked')?.value || 'per_subif',
                                ip_step: parseInt(document.getElementById('ip-step')?.value) || 2,
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
                            const isLoopbackLocal = (data.interfaceType || 'bundle') === 'loopback';
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
                                    const mode = document.querySelector('input[name="ip-mode"]:checked')?.value || 'per_subif';
                                    const step = parseInt(document.getElementById('ip-step')?.value) || 2;
                                    const count = parseInt(document.getElementById('subif-count')?.value) || 1;
                                    if (mode === 'per_subif' && count > 1) {
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

                        document.getElementById('create-subif')?.addEventListener('change', (e) => {
                            const opts = document.getElementById('subif-options');
                            if (opts) {
                                if (e.target.checked) opts.classList.remove('collapsed');
                                else opts.classList.add('collapsed');
                            }
                            updatePreview();
                        });
                        document.getElementById('subif-count')?.addEventListener('input', updatePreview);

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
                        }

                        document.querySelectorAll('input[name="ip-version"]').forEach(r => r.addEventListener('change', (e) => {
                            const ipOpts = document.getElementById('ip-options');
                            const v6Row = document.getElementById('ipv6-row');
                            if (ipOpts) ipOpts.style.display = e.target.value !== 'none' ? 'block' : 'none';
                            if (v6Row) v6Row.style.display = e.target.value === 'dual' ? 'flex' : 'none';
                            updatePreview(); validateIpAddress();
                        }));
                        document.getElementById('ip-start')?.addEventListener('input', () => { updatePreview(); validateIpAddress(); });
                        document.getElementById('ip-prefix')?.addEventListener('input', () => {
                            const pv = parseInt(document.getElementById('ip-prefix')?.value) || 30;
                            if (pv <= 30) {
                                const stepEl = document.getElementById('ip-step');
                                const stepRow = document.getElementById('ip-step-row');
                                const autoStep = Math.pow(2, 32 - pv);
                                if (stepEl) stepEl.value = autoStep;
                                if (stepRow) stepRow.style.display = 'block';
                                const uniRadio = document.querySelector('input[name="ip-mode"][value="unique_subnet"]');
                                if (uniRadio) uniRadio.checked = true;
                            }
                            updatePreview(); validateIpAddress();
                        });
                        document.getElementById('ipv6-start')?.addEventListener('input', updatePreview);
                        document.getElementById('ipv6-prefix')?.addEventListener('input', updatePreview);
                        document.querySelectorAll('input[name="ip-mode"]').forEach(r => r.addEventListener('change', (e) => {
                            const row = document.getElementById('ip-step-row');
                            if (row) row.style.display = e.target.value === 'unique_subnet' ? 'block' : 'none';
                            updatePreview(); validateIpAddress();
                        }));
                        document.getElementById('ip-step')?.addEventListener('input', () => { updatePreview(); validateIpAddress(); });
                        updatePreview(); validateIpAddress();
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
                            ipMode: document.querySelector('input[name="ip-mode"]:checked')?.value || 'per_subif',
                            ipStep: parseInt(document.getElementById('ip-step')?.value) || 2,
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
                        return `
                        <div class="scaler-form">
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
                                        <input type="number" id="vlan-start" class="scaler-input" value="${data.vlanStart || 100}" min="1" max="4094">
                                    </div>
                                    <div class="scaler-form-group">
                                        <label>VLAN Step</label>
                                        <input type="number" id="vlan-step" class="scaler-input" value="${data.vlanStep || 1}" min="0" max="4094">
                                    </div>
                                </div>
                                <div class="scaler-info-box" style="font-size:11px;padding:6px 10px;margin-top:4px">
                                    Sub-if naming: <code>parent.{vlan}</code> where VLAN = start + (index * step).
                                    Step 0 = all sub-ifs share the same VLAN.
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
                                        <input type="number" id="outer-vlan-start" class="scaler-input" value="${data.outerVlanStart || 100}" min="1" max="4094">
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
                            </div>

                            <div class="scaler-preview-box" style="margin-top:12px">
                                <label>DNOS SYNTAX PREVIEW:</label>
                                <pre id="encap-preview" class="scaler-syntax-preview">Loading...</pre>
                            </div>
                        </div>`;
                    },
                    afterRender: (data) => {
                        let debounceTimer;
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
                                        interface_type: data.interfaceType || 'bundle',
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
                                        ip_mode: data.ipMode || 'per_subif',
                                        ip_step: data.ipStep ?? 2,
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
                        const t = data.interfaceType || 'bundle';
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
                            ipDesc += ` (${data.ipMode || 'per_subif'})`;
                            rows.push(`<tr><td>IP</td><td>${ipDesc}</td></tr>`);
                        }
                        if (data.description) rows.push(`<tr><td>Description</td><td>${data.description}</td></tr>`);
                        if (data.mplsEnabled) rows.push(`<tr><td>MPLS</td><td>Enabled</td></tr>`);
                        if (data.flowspecEnabled) rows.push(`<tr><td>Flowspec</td><td>Enabled</td></tr>`);
                        if (data.bfdEnabled) rows.push(`<tr><td>BFD</td><td>Enabled</td></tr>`);
                        if (data.mtu) rows.push(`<tr><td>MTU</td><td>${data.mtu}</td></tr>`);
                        return `
                        <div class="scaler-review">
                            <h4>Configuration Summary</h4>
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
                        </div>`;
                    },
                    afterRender: async (data) => {
                        try {
                            const t = data.interfaceType || 'bundle';
                            const isSubif = t === 'subif';
                            const isPhys = t === 'subif';
                            const encap = data.encapsulation || 'dot1q';
                            const isQinQ = encap === 'qinq';
                            const parent = isSubif && (data.subifParents || [])[0];
                            const ctx = data.deviceContext || {};
                            const sshHost = ctx.mgmt_ip || ctx.ip || '';
                            let collisionChoice = data._collisionChoice || 'override';
                            if (parent && data.deviceId) {
                                try {
                                    const scan = await ScalerAPI.scanExisting({
                                        device_id: data.deviceId,
                                        ssh_host: sshHost,
                                        scan_type: 'interfaces',
                                        parent_interface: parent
                                    });
                                    const existing = scan.existing_sub_ids || [];
                                    const l3Conflicts = scan.l3_conflicts || [];
                                    const nextFree = scan.next_free?.sub_id || 1;
                                    if (existing.length > 0 || l3Conflicts.length > 0) {
                                        const warnEl = document.getElementById('collision-warning');
                                        if (warnEl) {
                                            warnEl.style.display = 'block';
                                            warnEl.innerHTML = `
                                                <div class="scaler-collision-header">Existing sub-interfaces detected on ${parent}</div>
                                                <div class="scaler-collision-detail">${existing.length} sub-ID(s) in use. ${l3Conflicts.length} L3 (have IP, would conflict with l2-service).</div>
                                                <div class="scaler-collision-actions">
                                                    <label><input type="radio" name="collision-choice" value="skip"> Skip conflicts (use free IDs only)</label>
                                                    <label><input type="radio" name="collision-choice" value="start-after"> Start after existing (from #${nextFree})</label>
                                                    <label><input type="radio" name="collision-choice" value="override" checked> Override (may fail)</label>
                                                </div>
                                            `;
                                            const rbs = warnEl.querySelectorAll('input[name="collision-choice"]');
                                            rbs.forEach(rb => {
                                                rb.checked = rb.value === collisionChoice;
                                                rb.addEventListener('change', () => {
                                                    collisionChoice = rb.value;
                                                    ScalerGUI.WizardController.data._collisionChoice = collisionChoice;
                                                    if (collisionChoice === 'start-after') {
                                                        ScalerGUI.WizardController.data.vlanStart = nextFree;
                                                        ScalerGUI.WizardController.data.outerVlanStart = nextFree;
                                                    }
                                                    ScalerGUI.WizardController.render();
                                                });
                                            });
                                        }
                                    }
                                } catch (_) {}
                            }
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
                                ip_step: data.ipStep ?? 2,
                                ip_mode: data.ipMode || 'per_subif',
                                mpls_enabled: isPhys ? (data.mplsEnabled || false) : false,
                                flowspec_enabled: isPhys ? (data.flowspecEnabled || false) : false,
                                bfd: isPhys ? (data.bfdEnabled || false) : false,
                                bfd_interval: isPhys && data.bfdEnabled ? (data.bfdInterval || undefined) : undefined,
                                bfd_multiplier: isPhys && data.bfdEnabled ? (data.bfdMultiplier || undefined) : undefined,
                                mtu: isPhys ? (data.mtu || null) : null,
                                description: data.description || '',
                            };
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
                            } catch (_) {}
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
                        } catch (e) {
                            document.getElementById('config-preview').textContent = `Error: ${e.message}`;
                        }
                    }
                },
                {
                    id: 'push',
                    title: 'Push',
                    finalButtonText: 'Commit Check',
                    render: (data) => {
                        const ctx = data.deviceContext || {};
                        const host = ctx.mgmt_ip || ctx.ip || '';
                        const resolved = ctx.resolved_via || '';
                        return `
                        <div class="scaler-form">
                            <div class="scaler-form-group">
                                <label>Delivery Method</label>
                                <div class="scaler-radio-group">
                                    <label class="scaler-radio">
                                        <input type="radio" name="push-mode" value="dry_run" checked>
                                        <span><strong>Commit Check First</strong></span>
                                    </label>
                                    <div class="scaler-radio-desc">Paste config via SSH terminal, run <code>commit check</code>.
                                    Nothing is applied. If check passes, you can commit from the result dialog.</div>
                                    <label class="scaler-radio">
                                        <input type="radio" name="push-mode" value="merge">
                                        <span><strong>Commit Directly</strong></span>
                                    </label>
                                    <div class="scaler-radio-desc">Paste config via SSH terminal + <code>commit</code>.
                                    Use when you've already validated with a commit check.</div>
                                    <label class="scaler-radio">
                                        <input type="radio" name="push-mode" value="clipboard">
                                        <span><strong>Copy to Clipboard + Open SSH</strong></span>
                                    </label>
                                    <div class="scaler-radio-desc">Copies the full DNOS config to your clipboard and opens
                                    an SSH terminal to the device. Paste manually in config mode.</div>
                                </div>
                            </div>
                            <div id="push-target-info" class="scaler-info-box" style="font-size:12px">
                                <strong>Target:</strong> ${data.deviceId}${host ? ` (${host})` : ''}${resolved ? ` -- via ${resolved}` : ''}<br>
                                <strong>Config:</strong> ${(data.generatedConfig || '').split('\\n').length} lines,
                                ${data.count} ${data.interfaceType} interface${data.count > 1 ? 's' : ''}
                            </div>
                        </div>`;
                    },
                    afterRender: (data) => {
                        document.querySelectorAll('input[name="push-mode"]').forEach(r => {
                            r.addEventListener('change', () => {
                                const btn = document.getElementById('wizard-next');
                                const mode = document.querySelector('input[name="push-mode"]:checked')?.value;
                                if (btn) btn.textContent = mode === 'clipboard' ? 'Copy & Open SSH' : mode === 'merge' ? 'Commit' : 'Commit Check';
                            });
                        });
                    },
                    collectData: () => {
                        const mode = document.querySelector('input[name="push-mode"]:checked')?.value || 'dry_run';
                        return {
                            dryRun: mode === 'dry_run',
                            pushMode: mode
                        };
                    }
                }
            ];

            const _ifaceTypeFlows = {
                subif:    ['type', 'parent', 'subifs', 'encap', 'review', 'push'],
                loopback: ['type', 'subifs', 'review', 'push'],
                bundle:   ['type', 'members', 'subifs', 'encap', 'review', 'push'],
                ph:       ['type', 'subifs', 'encap', 'review', 'push'],
                irb:      ['type', 'subifs', 'encap', 'review', 'push'],
            };

            const _ifaceStepKeyMap = {
                type:     ['interfaceType', 'startNumber', 'count'],
                members:  ['bundleMembers', 'lacpMode'],
                parent:   ['subifParents'],
                subifs:   ['createSubinterfaces', 'subifCount', 'interfaceMode', 'l2Service', 'ipEnabled', 'ipVersion', 'ipStart', 'ipPrefix', 'ipv6Start', 'ipv6Prefix', 'ipMode', 'ipStep', 'mplsEnabled', 'flowspecEnabled', 'bfdEnabled', 'bfdInterval', 'bfdMultiplier', 'mtu', 'description'],
                encap:    ['encapsulation', 'vlanStart', 'vlanStep', 'outerVlanStart', 'outerVlanStep', 'innerVlanStart', 'innerVlanStep'],
                review:   ['generatedConfig'],
                push:     ['dryRun', 'pushMode'],
            };

            const _stepById = {};
            _ifaceAllSteps.forEach(s => { _stepById[s.id] = s; });

            function _buildIfaceSteps(data) {
                const t = (data.interfaceType || 'bundle').toLowerCase();
                const flow = _ifaceTypeFlows[t] || _ifaceTypeFlows.bundle;
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
                    onRefresh: async () => {
                        const c = await self.refreshDeviceContextLive(deviceId);
                        self.WizardController.data.deviceContext = c;
                        self.WizardController.render();
                    }
                });
            },
            onLastRunRerun: (rec) => {
                if (rec?.params) {
                    Object.assign(self.WizardController.data, rec.params);
                    self.WizardController.data.deviceId = deviceId;
                    self.WizardController.data.deviceContext = ctx;
                    self.WizardController.currentStep = 0;
                    self.WizardController._highestStepReached = 0;
                    if (self.WizardController.stepBuilder) {
                        const built = self.WizardController.stepBuilder(self.WizardController.data);
                        self.WizardController.steps = built.steps;
                        self.WizardController.stepDependencies = built.deps || {};
                        self.WizardController.stepKeys = built.keys || {};
                    }
                    self.WizardController.render();
                }
            },
            onLastRunRerunOther: (rec) => {
                self.closePanel('interface-wizard');
                self.openMirrorWizard(rec.deviceId);
            },
            onComplete: async (data) => {
                if (data.pushMode === 'clipboard') {
                    const config = data.generatedConfig || '';
                    try {
                        await navigator.clipboard.writeText(config);
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
                        mode: data.pushMode === 'dry_run' ? 'merge' : data.pushMode,
                        dry_run: data.dryRun,
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
            }).catch(() => {});
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
        
        const content = document.createElement('div');
        content.innerHTML = '<div class="scaler-loading">Loading...</div>';
        
        this.openPanel('service-wizard', `Service Wizard - ${deviceId}`, content, {
            width: '550px',
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
            onLastRunRerun: (rec) => {
                if (rec?.params) {
                    Object.assign(self.WizardController.data, rec.params);
                    self.WizardController.data.deviceId = deviceId;
                    self.WizardController.data.deviceContext = ctx;
                    self.WizardController.currentStep = 0;
                    self.WizardController._highestStepReached = 0;
                    self.WizardController.render();
                }
            },
            onLastRunRerunOther: (rec) => {
                self.closePanel('service-wizard');
                self.openMirrorWizard(rec.deviceId);
            },
            wizardHeader: (data) => self.renderContextPanel(deviceId, data.deviceContext || {}, { onRefresh: () => self.refreshDeviceContextLive(deviceId).then(c => { self.WizardController.data.deviceContext = c; self.WizardController.render(); }) }),
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
                        serviceType: document.getElementById('svc-type').value
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
                                const prefix = document.getElementById('svc-prefix').value || 'FXC_';
                                const start = parseInt(document.getElementById('svc-start').value) || 1;
                                const count = Math.min(parseInt(document.getElementById('svc-count').value) || 100, 3); // Preview max 3
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
                                        const actualCount = parseInt(document.getElementById('svc-count').value) || 100;
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
                        namePrefix: document.getElementById('svc-prefix').value || 'FXC_',
                        startNumber: parseInt(document.getElementById('svc-start').value) || 1,
                        count: parseInt(document.getElementById('svc-count').value) || 100
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
                            } catch (_) {}
                        } catch (e) {
                            document.getElementById('config-preview').textContent = `Error: ${e.message}`;
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
                        mode: data.pushMode === 'dry_run' ? 'merge' : data.pushMode,
                        dry_run: data.dryRun,
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
            }).catch(() => {});
        }
    },

    async openVRFWizard(deviceId = null, prefillParams = null) {
        if (!deviceId) {
            this.openDeviceSelector('VRF / L3VPN Wizard', (id) => this.openVRFWizard(id, prefillParams));
            return;
        }
        const content = document.createElement('div');
        content.className = 'scaler-wizard-container';
        content.innerHTML = '<div class="scaler-loading">Loading...</div>';
        this.openPanel('vrf-wizard', `VRF / L3VPN - ${deviceId}`, content, {
            width: '520px',
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
            onLastRunRerun: (rec) => {
                if (rec?.params) {
                    Object.assign(self.WizardController.data, rec.params);
                    self.WizardController.data.deviceId = deviceId;
                    self.WizardController.data.deviceContext = ctx;
                    self.WizardController.currentStep = 0;
                    self.WizardController._highestStepReached = 0;
                    self.WizardController.render();
                }
            },
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
                        rtBase: document.getElementById('vrf-rt-base')?.value || '65000'
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
                                <tr><td>Interfaces</td><td>${d.attachInterfaces ? (d.interfaceList || []).length + ' attached' : 'None'}</td></tr>
                            </table>
                            <div class="scaler-preview-box">
                                <label>DNOS Preview:</label>
                                <pre id="vrf-config-preview">Generating...</pre>
                            </div>
                            <div id="config-validation"></div>
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
                                rt_config: { mode: d.rtMode || 'same_as_rd' }
                            };
                            const result = await ScalerAPI.generateServices(params);
                            const el = document.getElementById('vrf-config-preview');
                            if (el) el.textContent = result.config || '(empty)';
                            ScalerGUI.WizardController.data.generatedConfig = result.config;
                            try {
                                const val = await ScalerAPI.validateConfig({ config: result.config, hierarchy: 'services' });
                                const vEl = document.getElementById('config-validation');
                                if (vEl) vEl.innerHTML = ScalerGUI._renderValidationResults(val.errors, val.warnings, val.suggestions);
                            } catch (_) {}
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
                        mode: data.pushMode === 'dry_run' ? 'merge' : data.pushMode,
                        dry_run: data.dryRun,
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
            }).catch(() => {});
        }
    },

    async openBridgeDomainWizard(deviceId = null, prefillParams = null) {
        if (!deviceId) {
            this.openDeviceSelector('Bridge Domain Wizard', (id) => this.openBridgeDomainWizard(id, prefillParams));
            return;
        }
        const content = document.createElement('div');
        content.className = 'scaler-wizard-container';
        content.innerHTML = '<div class="scaler-loading">Loading...</div>';
        this.openPanel('bridge-domain-wizard', `Bridge Domain - ${deviceId}`, content, {
            width: '520px',
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
            onLastRunRerun: (rec) => {
                if (rec?.params) {
                    Object.assign(self.WizardController.data, rec.params);
                    self.WizardController.data.deviceId = deviceId;
                    self.WizardController.data.deviceContext = ctx;
                    self.WizardController.currentStep = 0;
                    self.WizardController._highestStepReached = 0;
                    self.WizardController.render();
                }
            },
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
                            } catch (_) {}
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
                        mode: data.pushMode === 'dry_run' ? 'merge' : data.pushMode,
                        dry_run: data.dryRun,
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
            }).catch(() => {});
        }
    },

    async openFlowSpecWizard(deviceId = null, prefillParams = null) {
        if (!deviceId) {
            this.openDeviceSelector('FlowSpec Wizard', (id) => this.openFlowSpecWizard(id, prefillParams));
            return;
        }
        const content = document.createElement('div');
        content.className = 'scaler-wizard-container';
        content.innerHTML = '<div class="scaler-loading">Loading...</div>';
        this.openPanel('flowspec-wizard', `FlowSpec Local - ${deviceId}`, content, {
            width: '520px',
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
            onLastRunRerun: (rec) => {
                if (rec?.params) {
                    Object.assign(self.WizardController.data, rec.params);
                    self.WizardController.data.deviceId = deviceId;
                    self.WizardController.data.deviceContext = ctx;
                    self.WizardController.currentStep = 0;
                    self.WizardController._highestStepReached = 0;
                    self.WizardController.render();
                }
            },
            onLastRunRerunOther: (rec) => {
                self.closePanel('flowspec-wizard');
                self.openMirrorWizard(rec.deviceId);
            },
            steps: [
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
                    })
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
                    })
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
                    })
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
                            if (el) el.textContent = result.config || '(empty)';
                            ScalerGUI.WizardController.data.generatedConfig = result.config;
                            try {
                                const val = await ScalerAPI.validateConfig({ config: result.config, hierarchy: 'flowspec' });
                                const vEl = document.getElementById('config-validation');
                                if (vEl) vEl.innerHTML = ScalerGUI._renderValidationResults(val.errors, val.warnings, val.suggestions);
                            } catch (_) {}
                        } catch (e) {
                            const el = document.getElementById('fs-config-preview');
                            if (el) el.textContent = `Error: ${e.message}`;
                        }
                    }
                },
                ScalerGUI._buildPushStep({
                    radioName: 'fs-push-mode',
                    includeClipboard: false,
                    infoText: (d) => `<strong>Config:</strong> Ready to push FlowSpec policy ${d.policyName} to ${d.deviceId}.`
                })
            ],
            onComplete: async (data) => {
                try {
                    const ctx = data.deviceContext || {};
                    const result = await ScalerAPI.pushConfig({
                        device_id: data.deviceId,
                        config: data.generatedConfig,
                        hierarchy: 'flowspec',
                        mode: data.pushMode === 'dry_run' ? 'merge' : data.pushMode,
                        dry_run: data.dryRun,
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
            }).catch(() => {});
        }
    },

    async openRoutingPolicyWizard(deviceId = null, prefillParams = null) {
        if (!deviceId) {
            this.openDeviceSelector('Routing Policy Wizard', (id) => this.openRoutingPolicyWizard(id, prefillParams));
            return;
        }
        const content = document.createElement('div');
        content.className = 'scaler-wizard-container';
        content.innerHTML = '<div class="scaler-loading">Loading...</div>';
        this.openPanel('routing-policy-wizard', `Routing Policy - ${deviceId}`, content, {
            width: '520px',
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
            onLastRunRerun: (rec) => {
                if (rec?.params) {
                    Object.assign(self.WizardController.data, rec.params);
                    self.WizardController.data.deviceId = deviceId;
                    self.WizardController.data.deviceContext = ctx;
                    self.WizardController.currentStep = 0;
                    self.WizardController._highestStepReached = 0;
                    self.WizardController.render();
                }
            },
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
                                <table class="scaler-table"><thead><tr><th>Prefix</th><th>Action</th></tr></thead><tbody id="rp-entries">${rows}</tbody></table>
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
                            if (pref) entries.push({ prefix: pref, action: act || 'deny' });
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
                            } catch (_) {}
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
                        mode: data.pushMode === 'dry_run' ? 'merge' : data.pushMode,
                        dry_run: data.dryRun,
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
            }).catch(() => {});
        }
    },
    
    // =========================================================================
    // MULTIHOMING WIZARD
    // =========================================================================
    
    async openMultihomingWizard() {
        const content = document.createElement('div');
        content.className = 'scaler-mh-wizard';
        content.innerHTML = `<div class="scaler-loading">Loading devices...</div>`;
        
        this.openPanel('multihoming-wizard', 'Multihoming Sync Wizard', content, {
            width: '550px',
            parentPanel: 'scaler-menu'
        });
        
        try {
            const data = await ScalerAPI.getDevices();
            
        content.innerHTML = `
                <div class="scaler-form">
            <div class="scaler-info-box">
                        Select 2 PE devices to synchronize ESI multihoming configuration.
            </div>
            <div class="scaler-form-group">
                        <label>Select Devices (exactly 2)</label>
                <div id="mh-devices" class="scaler-checkbox-list">
                            ${data.devices.map(dev => `
                                <label class="scaler-checkbox-item">
                                    <input type="checkbox" value="${dev.id}">
                                    <span>${dev.hostname}</span>
                                    <span class="scaler-device-ip">${dev.ip}</span>
                                </label>
                            `).join('')}
                </div>
            </div>
            <div class="scaler-form-row">
                <div class="scaler-form-group">
                    <label>ESI Prefix (Type 1)</label>
                    <input type="text" id="mh-esi-prefix" class="scaler-input" value="00:11:22:33:44" placeholder="00:11:22:33:44">
                </div>
                <div class="scaler-form-group">
                    <label>Redundancy Mode</label>
                    <select id="mh-mode" class="scaler-select">
                        <option value="single-active">Single-Active</option>
                        <option value="all-active">All-Active</option>
                    </select>
                </div>
            </div>
            <div class="scaler-form-group">
                <label>
                    <input type="checkbox" id="mh-match-rt" checked> 
                    Match interfaces by Route Target + VLAN
                </label>
            </div>
            <div class="scaler-form-actions">
                <button class="scaler-btn" id="mh-compare-btn">Compare MH</button>
                <button class="scaler-btn scaler-btn-primary" id="mh-sync-btn">Sync Multihoming</button>
            </div>
            <div id="mh-result" class="scaler-result-box" style="display:none;"></div>
                </div>
            `;
            
        document.getElementById('mh-compare-btn').onclick = async () => {
            const checked = document.querySelectorAll('#mh-devices input:checked');
            const ids = Array.from(checked).map(cb => cb.value);
            
            if (ids.length !== 2) {
                    this.showNotification('Select exactly 2 devices', 'warning');
                return;
            }
            
            const resultBox = document.getElementById('mh-result');
            resultBox.style.display = 'block';
            resultBox.innerHTML = '<div class="scaler-loading">Comparing...</div>';
            
            try {
                const result = await ScalerAPI.compareMultihoming(ids);
                resultBox.innerHTML = `
                    <div class="scaler-mh-compare">
                        <div class="scaler-stat"><span class="scaler-stat-num">${result.matching}</span> Matching ESIs</div>
                        <div class="scaler-stat"><span class="scaler-stat-num">${result.device1_only}</span> Only in ${result.device1}</div>
                        <div class="scaler-stat"><span class="scaler-stat-num">${result.device2_only}</span> Only in ${result.device2}</div>
                    </div>
                `;
            } catch (e) {
                resultBox.innerHTML = `<div class="scaler-error">${e.message}</div>`;
            }
        };
        
        document.getElementById('mh-sync-btn').onclick = async () => {
            const checked = document.querySelectorAll('#mh-devices input:checked');
            const ids = Array.from(checked).map(cb => cb.value);
            
                if (ids.length !== 2) {
                    this.showNotification('Select exactly 2 devices', 'warning');
                return;
            }
            
            const esiPrefix = document.getElementById('mh-esi-prefix').value;
            const mode = document.getElementById('mh-mode').value;
            const matchRt = document.getElementById('mh-match-rt').checked;
            
                this.closePanel('multihoming-wizard');
            
            try {
                const result = await ScalerAPI.syncMultihoming({
                    device_ids: ids,
                    esi_prefix: esiPrefix,
                    redundancy_mode: mode,
                    match_neighbor: matchRt
                });
                this.showProgress(result.job_id, `Syncing MH across ${ids.length} devices`);
            } catch (e) {
                this.showNotification(`Sync failed: ${e.message}`, 'error');
            }
        };
        } catch (e) {
            content.innerHTML = `<div class="scaler-error">${e.message}</div>`;
        }
    },
    
    // =========================================================================
    // UPGRADE WIZARD
    // =========================================================================
    
    async openUpgradeWizard() {
        const content = document.createElement('div');
        content.innerHTML = '<div class="scaler-loading">Loading devices...</div>';
        
        this.openPanel('upgrade-wizard', 'Image Upgrade Wizard', content, {
            width: '550px',
            parentPanel: 'scaler-menu'
        });
        
        try {
            const data = await ScalerAPI.getDevices();
            
        content.innerHTML = `
            <div class="scaler-form">
                    <div class="scaler-info-box">
                        Upgrade DNOS, GI, and BaseOS from Jenkins builds.
                    </div>
                <div class="scaler-form-group">
                        <label>Select Devices</label>
                        <div id="upgrade-devices" class="scaler-checkbox-list">
                            ${data.devices.map(dev => `
                                <label class="scaler-checkbox-item">
                                    <input type="checkbox" value="${dev.id}" checked>
                                    <span>${dev.hostname}</span>
                                </label>
                            `).join('')}
                        </div>
                    </div>
                    <div class="scaler-form-group">
                        <label>Branch</label>
                        <input type="text" id="upgrade-branch" class="scaler-input" value="main" placeholder="main or private branch name">
                    </div>
                    <div class="scaler-form-group">
                        <label>Components to Upgrade</label>
                        <div class="scaler-checkbox-list">
                            <label class="scaler-checkbox-item"><input type="checkbox" value="DNOS" checked> DNOS</label>
                            <label class="scaler-checkbox-item"><input type="checkbox" value="GI" checked> GI</label>
                            <label class="scaler-checkbox-item"><input type="checkbox" value="BaseOS" checked> BaseOS</label>
                        </div>
                    </div>
                    <div class="scaler-form-group">
                        <label>Upgrade Type</label>
                        <select id="upgrade-type" class="scaler-select">
                            <option value="normal">Normal (Same Major Version)</option>
                            <option value="delete_deploy">Delete & Deploy (Major Version Change)</option>
                    </select>
                </div>
                <div class="scaler-form-actions">
                        <button class="scaler-btn" id="upgrade-cancel">Cancel</button>
                        <button class="scaler-btn scaler-btn-primary" id="upgrade-start">Start Upgrade</button>
                </div>
            </div>
        `;
            
            document.getElementById('upgrade-cancel').onclick = () => this.closePanel('upgrade-wizard');
            document.getElementById('upgrade-start').onclick = async () => {
                const deviceCheckboxes = document.querySelectorAll('#upgrade-devices input:checked');
                const deviceIds = Array.from(deviceCheckboxes).map(cb => cb.value);
                
                const componentCheckboxes = content.querySelectorAll('.scaler-checkbox-list input[value="DNOS"], .scaler-checkbox-list input[value="GI"], .scaler-checkbox-list input[value="BaseOS"]');
                const components = Array.from(componentCheckboxes).filter(cb => cb.checked).map(cb => cb.value);
                
                if (deviceIds.length === 0) {
                    this.showNotification('Select at least one device', 'warning');
                return;
            }
            
                if (components.length === 0) {
                    this.showNotification('Select at least one component', 'warning');
                return;
            }
            
                const branch = document.getElementById('upgrade-branch').value || 'main';
                const upgradeType = document.getElementById('upgrade-type').value;
                
                this.closePanel('upgrade-wizard');
                
                try {
                    const result = await ScalerAPI.imageUpgrade({
                        device_ids: deviceIds,
                        branch: branch,
                        components: components,
                        upgrade_type: upgradeType,
                        parallel: true
                    });
                    this.showProgress(result.job_id, `Upgrading ${deviceIds.length} devices`);
            } catch (e) {
                    this.showNotification(`Upgrade failed: ${e.message}`, 'error');
                }
            };
        } catch (e) {
            content.innerHTML = `<div class="scaler-error">${e.message}</div>`;
        }
    },
    
    // =========================================================================
    // SCALE WIZARD
    // =========================================================================
    
    async openScaleWizard() {
        const content = document.createElement('div');
        content.innerHTML = '<div class="scaler-loading">Loading devices...</div>';
        
        this.openPanel('scale-wizard', 'Scale Up/Down Wizard', content, {
            width: '550px',
            parentPanel: 'scaler-menu'
        });
        
        try {
            const data = await ScalerAPI.getDevices();
            
        content.innerHTML = `
            <div class="scaler-form">
                    <div class="scaler-info-box">
                        Bulk add or delete services with their correlated interfaces.
                    </div>
                <div class="scaler-form-group">
                        <label>Select Devices</label>
                        <div id="scale-devices" class="scaler-checkbox-list">
                            ${data.devices.map(dev => `
                                <label class="scaler-checkbox-item">
                                    <input type="checkbox" value="${dev.id}" checked>
                                    <span>${dev.hostname}</span>
                                </label>
                            `).join('')}
                </div>
                    </div>
                    <div class="scaler-form-row">
                <div class="scaler-form-group">
                            <label>Operation</label>
                            <select id="scale-op" class="scaler-select">
                                <option value="down">Scale DOWN (Delete)</option>
                                <option value="up">Scale UP (Add)</option>
                    </select>
                </div>
                <div class="scaler-form-group">
                            <label>Service Type</label>
                            <select id="scale-type" class="scaler-select">
                                <option value="fxc">FXC</option>
                                <option value="l2vpn">L2VPN</option>
                                <option value="evpn">EVPN</option>
                                <option value="vpws">VPWS</option>
                            </select>
                        </div>
                    </div>
                    <div class="scaler-form-group">
                        <label>Range Specification</label>
                        <input type="text" id="scale-range" class="scaler-input" value="last 100" placeholder="last 100, or 100-400, or 1,2,3">
                        <small class="scaler-form-hint">Examples: "last 300", "100-400", "1,2,50,100"</small>
                    </div>
                    <div class="scaler-form-group">
                        <label>
                            <input type="checkbox" id="scale-interfaces" checked>
                            Include correlated interfaces (PWHE, sub-interfaces)
                        </label>
                </div>
                <div class="scaler-form-actions">
                        <button class="scaler-btn" id="scale-preview">Preview</button>
                        <button class="scaler-btn scaler-btn-danger" id="scale-execute">Execute</button>
                </div>
                    <div id="scale-result" class="scaler-result-box" style="display:none;"></div>
            </div>
        `;
        
            const getParams = () => {
                const deviceCheckboxes = document.querySelectorAll('#scale-devices input:checked');
                return {
                    device_ids: Array.from(deviceCheckboxes).map(cb => cb.value),
                    operation: document.getElementById('scale-op').value,
                    service_type: document.getElementById('scale-type').value,
                    range_spec: document.getElementById('scale-range').value,
                    include_interfaces: document.getElementById('scale-interfaces').checked
                };
            };
            
            document.getElementById('scale-preview').onclick = async () => {
                const params = getParams();
                if (params.device_ids.length === 0) {
                    this.showNotification('Select at least one device', 'warning');
                return;
            }
            
                const resultBox = document.getElementById('scale-result');
                resultBox.style.display = 'block';
                resultBox.innerHTML = '<div class="scaler-loading">Analyzing...</div>';
                
                try {
                    params.dry_run = true;
                    const result = await ScalerAPI.scaleUpDown(params);
                    this.showProgress(result.job_id, 'Analyzing scale operation');
            } catch (e) {
                    resultBox.innerHTML = `<div class="scaler-error">${e.message}</div>`;
                }
            };
            
            document.getElementById('scale-execute').onclick = async () => {
                const params = getParams();
                if (params.device_ids.length === 0) {
                    this.showNotification('Select at least one device', 'warning');
                    return;
                }
                
                if (!confirm(`Are you sure you want to scale ${params.operation} ${params.service_type} services?\n\nThis will modify ${params.device_ids.length} device(s).`)) {
                    return;
                }
                
                this.closePanel('scale-wizard');
                
                try {
                    params.dry_run = false;
                    const result = await ScalerAPI.scaleUpDown(params);
                    this.showProgress(result.job_id, `Scale ${params.operation} ${params.service_type}`);
                } catch (e) {
                    this.showNotification(`Scale failed: ${e.message}`, 'error');
                }
            };
        } catch (e) {
            content.innerHTML = `<div class="scaler-error">${e.message}</div>`;
        }
    },
    
    // =========================================================================
    // STAG CHECK
    // =========================================================================
    
    async openStagCheck() {
        const content = document.createElement('div');
        content.innerHTML = '<div class="scaler-loading">Loading devices...</div>';
        
        this.openPanel('stag-check', 'Stag Pool Check', content, {
            width: '600px',
            parentPanel: 'scaler-menu'
        });
        
        try {
            const data = await ScalerAPI.getDevices();
            
        content.innerHTML = `
                <div class="scaler-form">
                    <div class="scaler-info-box">
                        Check QinQ Stag pool usage (ifindex 88001-92000, limit 4000).
                </div>
                <div class="scaler-form-group">
                        <label>Select Devices</label>
                        <div id="stag-devices" class="scaler-checkbox-list">
                            ${data.devices.map(dev => `
                                <label class="scaler-checkbox-item">
                                    <input type="checkbox" value="${dev.id}" checked>
                                    <span>${dev.hostname}</span>
                                </label>
                            `).join('')}
                </div>
            </div>
            <div class="scaler-form-actions">
                        <button class="scaler-btn scaler-btn-primary" id="stag-check-btn">Check Stag Pool</button>
            </div>
                    <div id="stag-result" class="scaler-result-box" style="display:none;"></div>
                </div>
            `;
            
            document.getElementById('stag-check-btn').onclick = async () => {
                const deviceCheckboxes = document.querySelectorAll('#stag-devices input:checked');
                const deviceIds = Array.from(deviceCheckboxes).map(cb => cb.value);
                
                if (deviceIds.length === 0) {
                    this.showNotification('Select at least one device', 'warning');
                    return;
                }
                
                const resultBox = document.getElementById('stag-result');
                resultBox.style.display = 'block';
                resultBox.innerHTML = '<div class="scaler-loading">Checking Stag pools...</div>';
                
                try {
                    const result = await ScalerAPI.stagCheck({ device_ids: deviceIds });
                    
                    let html = `<table class="scaler-table">
                        <thead>
                            <tr><th>Device</th><th>Stags</th><th>Limit</th><th>Usage</th><th>Status</th></tr>
                        </thead>
                        <tbody>`;
                    
                    for (const dev of result.devices) {
                        const statusClass = dev.exceeded ? 'scaler-status-error' : 
                                           (dev.at_risk ? 'scaler-status-warning' : 'scaler-status-ok');
                        const statusText = dev.exceeded ? 'EXCEEDED' : (dev.at_risk ? 'AT RISK' : 'OK');
                        
                        html += `<tr>
                            <td>${dev.hostname}</td>
                            <td>${dev.total_stags.toLocaleString()}</td>
                            <td>${dev.limit.toLocaleString()}</td>
                            <td>
                                <div class="scaler-progress-bar">
                                    <div class="scaler-progress-fill ${statusClass}" style="width: ${dev.percentage}%"></div>
                                </div>
                                ${dev.percentage}%
                            </td>
                            <td class="${statusClass}">${statusText}</td>
                        </tr>`;
                        
                        if (dev.error) {
                            html += `<tr><td colspan="5" class="scaler-error">${dev.error}</td></tr>`;
                        }
                    }
                    
                    html += '</tbody></table>';
                    html += `<div class="scaler-summary">
                        Total: ${result.summary.total_devices} devices | 
                        At Risk: ${result.summary.devices_at_risk} | 
                        Exceeded: ${result.summary.devices_exceeded}
                    </div>`;
                    
                    resultBox.innerHTML = html;
            } catch (e) {
                    resultBox.innerHTML = `<div class="scaler-error">${e.message}</div>`;
                }
            };
        } catch (e) {
            content.innerHTML = `<div class="scaler-error">${e.message}</div>`;
        }
    },
    
    // =========================================================================
    // OTHER PANELS (from original implementation)
    // =========================================================================
    
    async openDeviceManager() {
        const content = document.createElement('div');
        content.className = 'scaler-device-manager';
        content.innerHTML = `
            <div class="scaler-toolbar">
                <button class="scaler-btn scaler-btn-primary" id="dm-add-device">+ Add Device</button>
                <button class="scaler-btn" id="dm-refresh">Refresh</button>
            </div>
            <div class="scaler-device-list" id="dm-device-list">
                <div class="scaler-loading">Loading devices...</div>
            </div>
        `;
        
        this.openPanel('device-manager', 'Device Manager', content, {width: '500px', parentPanel: 'scaler-menu'});
        
        await this.refreshDeviceList();
        
        document.getElementById('dm-add-device').onclick = () => this.openAddDeviceDialog();
        document.getElementById('dm-refresh').onclick = () => this.refreshDeviceList();
    },
    
    async refreshDeviceList() {
        const listEl = document.getElementById('dm-device-list');
        if (!listEl) return;
        
        this.state.deviceCache = {};
        const canvasDevObjs = this._getCanvasDeviceObjects(false);

        if (canvasDevObjs.length === 0) {
            listEl.innerHTML = '<div class="scaler-empty">No devices on canvas.<br>Add devices to the topology first.</div>';
            return;
        }

        const devices = canvasDevObjs.map(co => ({
            id: co.label,
            hostname: co.label,
            ip: co.sshHost || '',
            serial: co.serial || '',
            platform: 'NCP',
            _hasSSH: !!co.sshHost,
        }));

        listEl.innerHTML = devices.map(device => {
            this.state.deviceCache[device.id] = device;
            return `
                <div class="scaler-device-card${device._hasSSH ? '' : ' scaler-device-no-ssh'}" data-device-id="${device.id}">
                    <div class="scaler-device-status" data-status="${device._hasSSH ? 'unknown' : 'no-ssh'}"></div>
                    <div class="scaler-device-info">
                        <div class="scaler-device-name">${device.hostname}</div>
                        <div class="scaler-device-ip">${device.ip || '<span style="font-size:10px;opacity:0.4">No SSH -- right-click device</span>'}</div>
                        <div class="scaler-device-platform">${device.platform}</div>
                    </div>
                    <div class="scaler-device-actions">
                        <button class="scaler-btn-icon" data-action="test" title="Test Connection"${device._hasSSH ? '' : ' disabled'}>
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                                <path d="M22 4L12 14.01l-3-3"/>
                            </svg>
                        </button>
                        <button class="scaler-btn-icon" data-action="sync" title="Sync Config"${device._hasSSH ? '' : ' disabled'}>
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 2v6h-6"/>
                                <path d="M3 12a9 9 0 0 1 15-6.7L21 8"/>
                            </svg>
                        </button>
                        <button class="scaler-btn-icon scaler-btn-danger" data-action="delete" title="Remove from list">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M3 6h18"/>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
                            </svg>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        ScalerAPI.getDevices().then(data => {
            const apiDevs = data.devices || [];
            const apiMap = {};
            apiDevs.forEach(d => { apiMap[(d.hostname || d.id || '').toLowerCase()] = d; });
            devices.forEach(device => {
                const apiDev = apiMap[device.hostname.toLowerCase()];
                if (apiDev) {
                    if (!device.ip && apiDev.ip) device.ip = apiDev.ip;
                    if (apiDev.platform) device.platform = apiDev.platform;
                    if (apiDev.system_type) device.platform = apiDev.system_type;
                }
                this.state.deviceCache[device.id] = device;
                const card = listEl.querySelector(`[data-device-id="${device.id}"]`);
                if (card) {
                    const ipEl = card.querySelector('.scaler-device-ip');
                    if (ipEl && device.ip) ipEl.textContent = device.ip;
                    const platEl = card.querySelector('.scaler-device-platform');
                    if (platEl && device.platform) platEl.textContent = device.platform;
                }
            });
        }).catch(() => {});

        listEl.querySelectorAll('[data-action]').forEach(btn => {
            btn.onclick = (e) => {
                e.stopPropagation();
                const card = btn.closest('.scaler-device-card');
                const deviceId = card.dataset.deviceId;
                this.handleDeviceAction(btn.dataset.action, deviceId);
            };
        });
        
        listEl.querySelectorAll('.scaler-device-card').forEach(card => {
            card.onclick = () => this.showConfigSummary(card.dataset.deviceId);
        });
    },
    
    async handleDeviceAction(action, deviceId) {
        const card = document.querySelector(`[data-device-id="${deviceId}"]`);
        const statusEl = card?.querySelector('.scaler-device-status');
        
        switch(action) {
            case 'test':
                if (statusEl) statusEl.dataset.status = 'testing';
                try {
                    const resolved = this._resolveDeviceId(deviceId);
                    await ScalerAPI.testConnection(deviceId, resolved.sshHost);
                    if (statusEl) statusEl.dataset.status = 'ok';
                    this.showNotification(`${deviceId}: Connection OK`, 'success');
                } catch (error) {
                    if (statusEl) statusEl.dataset.status = 'error';
                    this.showNotification(`${deviceId}: ${error.message}`, 'error');
                }
                break;
                
            case 'sync':
                if (statusEl) statusEl.dataset.status = 'syncing';
                try {
                    await ScalerAPI.syncDevice(deviceId);
                    if (statusEl) statusEl.dataset.status = 'ok';
                    this.showNotification(`${deviceId}: Config synced`, 'success');
                } catch (error) {
                    if (statusEl) statusEl.dataset.status = 'error';
                    this.showNotification(`${deviceId}: ${error.message}`, 'error');
                }
                break;
                
            case 'delete':
                if (confirm(`Delete device ${deviceId}?`)) {
                    try {
                        await ScalerAPI.deleteDevice(deviceId);
                        this.showNotification(`${deviceId}: Deleted`, 'success');
                        await this.refreshDeviceList();
                    } catch (error) {
                        this.showNotification(`${deviceId}: ${error.message}`, 'error');
                    }
                }
                break;
        }
    },
    
    async openDeviceSelector(title, onSelect, options = {}) {
        const content = document.createElement('div');
        content.innerHTML = '<div class="scaler-loading">Loading devices...</div>';
        
        this.openPanel('device-selector', `Select Device - ${title}`, content, {width: '400px'});
        
        try {
            const canvasDevObjs = this._getCanvasDeviceObjects();

            let apiDevices = [];
            try {
                apiDevices = (options.devices || (await ScalerAPI.getDevices()).devices || []);
            } catch (e) {
                console.warn('[ScalerGUI] Device list fetch failed:', e);
            }

            const apiByName = {};
            const apiByIp = {};
            for (const d of apiDevices) {
                const key = (d.hostname || d.id || '').toLowerCase().trim();
                if (key && !this._isDnaasDevice(d.hostname || d.id || '')) apiByName[key] = d;
                if (d.ip || d.mgmt_ip) apiByIp[(d.ip || d.mgmt_ip).trim()] = d;
            }

            let devices = [];
            if (canvasDevObjs.length > 0) {
                for (const cd of canvasDevObjs) {
                    const nameMatch = apiByName[cd.label.toLowerCase()];
                    const ipMatch = cd.sshHost ? apiByIp[cd.sshHost] : null;
                    const api = nameMatch || ipMatch;
                    devices.push({
                        id: api?.id || api?.hostname || cd.label,
                        hostname: api?.hostname || cd.label,
                        ip: cd.sshHost || api?.ip || api?.mgmt_ip || '',
                        canvasLabel: cd.label,
                        sshHost: cd.sshHost,
                        sshUser: cd.sshUser,
                        sshPassword: cd.sshPassword,
                        serial: cd.serial || api?.serial || '',
                        isDnaas: cd.isDnaas,
                    });
                }
            } else {
                devices = Object.values(apiByName).map(d => ({
                    id: d.id || d.hostname,
                    hostname: d.hostname || d.id,
                    ip: d.ip || d.mgmt_ip || '',
                    canvasLabel: d.hostname || d.id,
                    sshHost: d.ip || d.mgmt_ip || '',
                    sshUser: '', sshPassword: '', serial: d.serial || '', isDnaas: false,
                }));
            }

            const changes = this._wizardChangeLog.filter(c => Date.now() - c.timestamp < 300000);
            const changedLabels = new Set(changes.map(c => c.deviceId.toLowerCase()));

            const noSshDevices = devices.filter(d => !d.sshHost);
            const hasSshDevices = devices.filter(d => d.sshHost);
            
            content.innerHTML = `
                <div class="scaler-device-list scaler-device-select-list">
                    ${devices.length === 0 ? '<div class="scaler-empty">No devices found. Add devices to your topology canvas.</div>' : ''}
                    ${hasSshDevices.map(device => {
                        const hasChanges = changedLabels.has(device.canvasLabel.toLowerCase());
                        return `
                        <div class="scaler-device-select-item${hasChanges ? ' scaler-device-changed' : ''}" data-canvas-label="${device.canvasLabel}">
                            <div style="display:flex;flex-direction:column;gap:2px;flex:1">
                                <span class="scaler-device-name">${device.canvasLabel}</span>
                                <span class="scaler-device-ip">${device.sshHost}${device.hostname !== device.canvasLabel ? ' (' + device.hostname + ')' : ''}</span>
                            </div>
                            ${hasChanges ? '<span class="scaler-device-change-badge">changed</span>' : ''}
                        </div>
                    `;}).join('')}
                    ${noSshDevices.length ? `
                        <div class="scaler-device-select-separator">No SSH configured</div>
                        ${noSshDevices.map(device => `
                            <div class="scaler-device-select-item scaler-device-no-ssh" data-canvas-label="${device.canvasLabel}">
                                <span class="scaler-device-name" style="opacity:0.5">${device.canvasLabel}</span>
                                <span class="scaler-device-ip" style="color:var(--dn-orange,#e67e22);font-size:11px">Set SSH first</span>
                            </div>
                        `).join('')}
                    ` : ''}
                </div>
            `;
            
            content.querySelectorAll('.scaler-device-select-item').forEach(item => {
                item.onclick = () => {
                    const label = item.dataset.canvasLabel;
                    const dev = devices.find(d => d.canvasLabel === label);
                    if (!dev?.sshHost) {
                        this.showNotification(`Set SSH address for ${label} first (right-click device > Set SSH)`, 'warning');
                        return;
                    }
                    this.closePanel('device-selector');
                    onSelect(label);
                };
            });
        } catch (error) {
            content.innerHTML = `<div class="scaler-error">Failed to load devices: ${error.message}</div>`;
        }
    },

    openWizardHistoryPanel() {
        const history = this.getWizardHistory();
        const sorted = [...history].sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
        const byDate = {};
        sorted.forEach(r => {
            const d = r.timestamp ? new Date(r.timestamp).toDateString() : 'Unknown';
            if (!byDate[d]) byDate[d] = [];
            byDate[d].push(r);
        });
        const content = document.createElement('div');
        content.className = 'scaler-history-panel';
        content.innerHTML = `
            <div class="scaler-history-header">
                <span>Recent wizard runs</span>
            </div>
            <div class="scaler-history-list" id="scaler-history-list"></div>
        `;
        const panel = this.openPanel('wizard-history', 'Wizard Run History', content, { width: '520px', minimizable: true });
        const listEl = document.getElementById('scaler-history-list');
        if (sorted.length === 0) {
            listEl.innerHTML = '<div class="scaler-history-empty">No wizard runs yet. Complete a wizard to see history here.</div>';
        } else {
            const wizardLabels = { interfaces: 'Interface', services: 'Service', vrf: 'VRF', 'bridge-domain': 'Bridge Domain', flowspec: 'FlowSpec', 'routing-policy': 'Routing Policy', bgp: 'BGP', igp: 'IGP' };
            Object.keys(byDate).forEach(date => {
                const group = document.createElement('div');
                group.className = 'scaler-history-group';
                group.innerHTML = `<div class="scaler-history-date">${date}</div>`;
                const ul = document.createElement('ul');
                ul.className = 'scaler-history-entries';
                byDate[date].forEach(rec => {
                    const summary = this._formatLastRunSummary(rec);
                    const status = rec.success === true ? 'success' : rec.success === false ? 'failed' : 'pending';
                    const statusText = rec.success === true ? 'OK' : rec.success === false ? 'Failed' : 'Pending';
                    const li = document.createElement('li');
                    li.className = 'scaler-history-entry';
                    li.dataset.recId = rec.id || '';
                    li.innerHTML = `
                        <div class="scaler-history-entry-header">
                            <span class="scaler-history-type">${this.escapeHtml(wizardLabels[rec.wizardType] || rec.wizardType || '?')}</span>
                            <span class="scaler-history-device">${this.escapeHtml(rec.deviceLabel || rec.deviceId || '?')}</span>
                            <span class="scaler-history-status scaler-history-status-${status}">${statusText}</span>
                        </div>
                        <div class="scaler-history-summary">${this.escapeHtml(summary)}</div>
                        <div class="scaler-history-ts">${rec.timestamp ? new Date(rec.timestamp).toLocaleTimeString() : ''}</div>
                        <div class="scaler-history-actions" style="display:none">
                            <button type="button" class="scaler-btn scaler-btn-sm scaler-history-rerun">Re-run</button>
                            <button type="button" class="scaler-btn scaler-btn-sm scaler-history-rerun-other">Re-run on other device</button>
                        </div>
                    `;
                    li.querySelector('.scaler-history-entry-header')?.addEventListener('click', () => {
                        const acts = li.querySelector('.scaler-history-actions');
                        if (acts) acts.style.display = acts.style.display === 'none' ? 'flex' : 'none';
                    });
                    const typeToOpen = { interfaces: 'openInterfaceWizard', services: 'openServiceWizard', vrf: 'openVRFWizard', 'bridge-domain': 'openBridgeDomainWizard', flowspec: 'openFlowSpecWizard', 'routing-policy': 'openRoutingPolicyWizard', bgp: 'openBGPWizard', igp: 'openIGPWizard' };
                    const openMethod = typeToOpen[rec.wizardType] || 'openInterfaceWizard';
                    li.querySelector('.scaler-history-rerun')?.addEventListener('click', (e) => {
                        e.stopPropagation();
                        this.closePanel('wizard-history');
                        const fn = this[openMethod];
                        if (typeof fn === 'function') {
                            fn.call(this, rec.deviceId);
                            setTimeout(() => {
                                if (this.WizardController?.onLastRunRerun) this.WizardController.onLastRunRerun(rec);
                            }, 200);
                        }
                    });
                    li.querySelector('.scaler-history-rerun-other')?.addEventListener('click', (e) => {
                        e.stopPropagation();
                        this.closePanel('wizard-history');
                        this.openMirrorWizard(rec.deviceId);
                    });
                    ul.appendChild(li);
                });
                group.appendChild(ul);
                listEl.appendChild(group);
            });
        }
    },

    openCommitsPanel() {
        const content = document.createElement('div');
        content.className = 'scaler-commits-panel';
        content.innerHTML = `
            <div class="scaler-commits-header">
                <span>Active and recent configuration pushes</span>
                <button class="scaler-btn scaler-btn-sm" id="commits-refresh">Refresh</button>
            </div>
            <div class="scaler-commits-list" id="scaler-commits-list">
                <div class="scaler-loading">Loading jobs...</div>
            </div>
        `;
        const panel = this.openPanel('running-commits', 'Running Commits', content, { width: '560px', minimizable: true });
        let pollTimer = null;
        const listEl = document.getElementById('scaler-commits-list');

        const suggestErrorFix = (text) => {
            const t = (text || '').toLowerCase();
            const out = [];
            if (t.includes('already exists')) out.push('Interface already configured. Use Replace mode or delete first.');
            if (t.includes('not found')) out.push('Referenced item missing. Create parent interfaces/services first.');
            if (t.includes('invalid')) out.push('Check syntax and valid value ranges.');
            if (t.includes('limit') || t.includes('exceeded') || t.includes('stag')) out.push('Platform limit reached. Reduce count or delete unused interfaces.');
            if (t.includes('hook failed') || t.includes('assign_new_if_index')) out.push('Resource allocation failed. Check NCC logs.');
            if (t.includes('too many elements') || t.includes('leaflist')) out.push('Too many elements for this hierarchy. Reduce count.');
            if (t.includes('ip-address') && t.includes('l2-service')) out.push('Cannot add L2 to interface with IP. Delete IP first or use different sub-interface.');
            if (t.includes('conflict')) out.push('Configuration conflict. Check for duplicates.');
            if (t.includes('syntax')) out.push('Check missing keywords, brackets, or parameter order.');
            return out.length ? out : ['Check the terminal output above for details.'];
        };

        const formatAgo = (iso) => {
            if (!iso) return '';
            const d = new Date(iso);
            const s = Math.floor((Date.now() - d) / 1000);
            if (s < 60) return s + 's ago';
            if (s < 3600) return Math.floor(s / 60) + 'm ago';
            if (s < 86400) return Math.floor(s / 3600) + 'h ago';
            return Math.floor(s / 86400) + 'd ago';
        };

        const renderJobCard = (job) => {
            const status = job.status || 'pending';
            const dotClass = status === 'running' ? 'scaler-job-dot-running' : status === 'completed' ? 'scaler-job-dot-ok' : status === 'failed' ? 'scaler-job-dot-fail' : 'scaler-job-dot-pending';
            const name = job.job_name || job.device_id || 'Push';
            const pct = job.percent || 0;
            const msg = job.message || job.phase || '';
            const lines = job.terminal_lines || [];
            const terminalHtml = lines.map((l) => `<div class="scaler-terminal-line">${this.escapeHtml(l)}</div>`).join('');
            const isExpanded = this._commitsExpanded && this._commitsExpanded[job.job_id];
            const fullText = lines.join('\n');
            const suggestions = status === 'failed' ? suggestErrorFix(job.message || fullText) : [];
            const suggestionHtml = suggestions.length ? `<div class="scaler-job-error-box"><strong>Suggestions:</strong><ul>${suggestions.map((s) => `<li>${this.escapeHtml(s)}</li>`).join('')}</ul></div>` : '';
            return `
                <div class="scaler-job-card ${status}" data-job-id="${job.job_id}">
                    <div class="scaler-job-card-header">
                        <span class="scaler-job-dot ${dotClass}"></span>
                        <span class="scaler-job-name">${this.escapeHtml(name)}</span>
                        <span class="scaler-job-ago">${formatAgo(job.started_at)}</span>
                        <button class="scaler-job-toggle" data-job-id="${job.job_id}" title="${isExpanded ? 'Minimize' : 'Expand'}">${isExpanded ? '-' : '+'}</button>
                    </div>
                    <div class="scaler-job-progress" style="display:${status === 'running' ? 'block' : 'none'}">
                        <div class="scaler-progress-bar"><div class="scaler-progress-fill" style="width:${pct}%"></div></div>
                        <span class="scaler-job-phase">${this.escapeHtml(msg)}</span>
                    </div>
                    <div class="scaler-job-terminal scaler-collapse-section ${isExpanded ? '' : 'collapsed'}" data-job-id="${job.job_id}">
                        <div class="scaler-terminal-content">${terminalHtml}</div>
                        ${suggestionHtml}
                        ${(status === 'failed' || status === 'completed') ? `
                        <div class="scaler-job-actions">
                            <button class="scaler-btn scaler-btn-sm scaler-job-retry" data-job-id="${job.job_id}">Retry</button>
                            <button class="scaler-btn scaler-btn-sm scaler-job-copy" data-job-id="${job.job_id}">Copy output</button>
                        </div>` : ''}
                    </div>
                </div>`;
        };

        const render = async () => {
            if (!listEl.isConnected) {
                stopPoll();
                return;
            }
            try {
                const res = await ScalerAPI.getJobs();
                const jobs = res.jobs || [];
                if (jobs.length === 0) {
                    listEl.innerHTML = '<div class="scaler-empty">No push jobs yet. Run a wizard and push config to see them here.</div>';
                } else {
                    listEl.innerHTML = jobs.map((j) => renderJobCard(j)).join('');
                    listEl.querySelectorAll('.scaler-job-toggle').forEach((btn) => {
                        btn.onclick = () => {
                            this._commitsExpanded = this._commitsExpanded || {};
                            const jid = btn.dataset.jobId;
                            this._commitsExpanded[jid] = !this._commitsExpanded[jid];
                            render();
                        };
                    });
                    listEl.querySelectorAll('.scaler-job-retry').forEach((btn) => {
                        btn.onclick = async () => {
                            try {
                                const r = await ScalerAPI.retryJob(btn.dataset.jobId);
                                this.showProgress(r.job_id, r.job_id);
                                this.showNotification('Retry started', 'success');
                                render();
                            } catch (e) {
                                this.showNotification(e.message, 'error');
                            }
                        };
                    });
                    listEl.querySelectorAll('.scaler-job-copy').forEach((btn) => {
                        btn.onclick = async () => {
                            const card = btn.closest('.scaler-job-card');
                            const jid = card?.dataset?.jobId;
                            const job = jobs.find((j) => j.job_id === jid);
                            const text = (job?.terminal_lines || []).join('');
                            try {
                                await navigator.clipboard.writeText(text);
                                this.showNotification('Terminal output copied', 'success');
                            } catch (_) {}
                        };
                    });
                }
                const activeCount = jobs.filter((j) => j.status === 'running' || j.status === 'pending').length;
                const badge = document.getElementById('scaler-commits-badge');
                if (badge) {
                    badge.style.display = activeCount > 0 ? 'inline' : 'none';
                    badge.textContent = activeCount;
                }
            } catch (e) {
                listEl.innerHTML = `<div class="scaler-error">Failed to load jobs: ${e.message}</div>`;
            }
        };

        const startPoll = () => {
            if (pollTimer) clearInterval(pollTimer);
            pollTimer = setInterval(render, 2000);
        };
        const stopPoll = () => {
            if (pollTimer) clearInterval(pollTimer);
            pollTimer = null;
        };

        document.getElementById('commits-refresh').onclick = () => render();
        this._commitsExpanded = this._commitsExpanded || {};
        render();
        startPoll();
    },
    
    showProgress(jobId, title, options = {}) {
        const content = document.createElement('div');
        content.className = 'scaler-progress-panel';
        content.innerHTML = `
            <div class="scaler-progress-bar-container">
                <div class="scaler-progress-bar">
                    <div class="scaler-progress-fill" id="progress-fill-${jobId}" style="width: 0%"></div>
                </div>
                <span class="scaler-progress-text" id="progress-text-${jobId}">Connecting...</span>
            </div>
            <div class="scaler-progress-steps" id="progress-steps-${jobId}">
                <div class="scaler-step-info" style="color:var(--dn-orange,#e67e22)">Establishing SSH connection...</div>
            </div>
            <div class="scaler-terminal scaler-terminal-live" id="progress-terminal-${jobId}">
                <div class="scaler-terminal-header">
                    <span class="scaler-terminal-dot"></span> Device Terminal
                </div>
                <div class="scaler-terminal-content"></div>
            </div>
            <div class="scaler-progress-actions">
                <button class="scaler-btn scaler-btn-danger" id="progress-cancel-${jobId}">Cancel</button>
            </div>
        `;

        const panel = this.openPanel(`progress-${jobId}`, title, content, {minimizable: true, width: '560px'});

        const actionsEl = document.querySelector(`#progress-cancel-${jobId}`)?.parentElement;

        const showAwaitingButtons = () => {
            if (!actionsEl) return;
            actionsEl.innerHTML = `
                <button class="scaler-btn scaler-btn-primary" id="progress-commit-${jobId}">Commit Now</button>
                <button class="scaler-btn scaler-btn-danger" id="progress-cancel-held-${jobId}">Cancel (discard)</button>
            `;
            document.getElementById(`progress-commit-${jobId}`).onclick = async () => {
                try {
                    await ScalerAPI.commitHeldJob(jobId);
                    document.getElementById(`progress-text-${jobId}`).textContent = '100% - Committing...';
                } catch (e) {
                    this.showNotification(e.message, 'error');
                }
            };
            document.getElementById(`progress-cancel-held-${jobId}`).onclick = async () => {
                try {
                    await ScalerAPI.cancelHeldJob(jobId);
                    document.getElementById(`progress-text-${jobId}`).textContent = 'Cancelled';
                } catch (e) {
                    this.showNotification(e.message, 'error');
                }
            };
        };

        document.getElementById(`progress-cancel-${jobId}`).onclick = async () => {
            try {
                await ScalerAPI.cancelOperation(jobId);
                this.showNotification('Operation cancelled', 'warning');
            } catch (e) {
                this.showNotification(e.message, 'error');
            }
        };

        let terminalHasContent = false;
        const ws = ScalerAPI.connectProgress(jobId, {
            onProgress: (percent, message) => {
                const fill = document.getElementById(`progress-fill-${jobId}`);
                const text = document.getElementById(`progress-text-${jobId}`);
                if (fill) fill.style.width = `${percent}%`;
                if (text) text.textContent = `${percent}% - ${message || ''}`;
                const stepsEl = document.getElementById(`progress-steps-${jobId}`);
                if (stepsEl && message) {
                    stepsEl.innerHTML = `<div class="scaler-step-info">${this.escapeHtml(message)}</div>`;
                }
            },
            onTerminal: (line) => {
                const terminal = document.querySelector(`#progress-terminal-${jobId} .scaler-terminal-content`);
                if (!terminal) return;
                if (!terminalHasContent) {
                    terminalHasContent = true;
                    const dot = document.querySelector(`#progress-terminal-${jobId} .scaler-terminal-dot`);
                    if (dot) dot.classList.add('active');
                }
                const lines = (line || '').split('\n');
                lines.forEach(l => {
                    if (!l.trim()) return;
                    const div = document.createElement('div');
                    div.className = 'scaler-terminal-line';
                    div.textContent = l;
                    terminal.appendChild(div);
                });
                terminal.scrollTop = terminal.scrollHeight;
            },
            onStep: (current, total, name) => {
                const stepsEl = document.getElementById(`progress-steps-${jobId}`);
                if (stepsEl) {
                    stepsEl.innerHTML = `<div class="scaler-step-info">Step ${current}/${total}: ${name}</div>`;
                }
            },
            onAwaitingDecision: () => {
                showAwaitingButtons();
            },
            onComplete: (success, result) => {
                const fill = document.getElementById(`progress-fill-${jobId}`);
                const text = document.getElementById(`progress-text-${jobId}`);
                if (fill) {
                    fill.style.width = '100%';
                    fill.classList.add(success ? 'scaler-progress-success' : 'scaler-progress-error');
                }
                if (text) text.textContent = success ? 'Complete!' : (result?.cancelled ? 'Cancelled' : 'Failed');
                const dot = document.querySelector(`#progress-terminal-${jobId} .scaler-terminal-dot`);
                if (dot) { dot.classList.remove('active'); dot.classList.add(success ? 'done' : 'error'); }

                if (actionsEl) {
                    actionsEl.innerHTML = '';
                    const closeBtn = document.createElement('button');
                    closeBtn.className = 'scaler-btn';
                    closeBtn.textContent = 'Close';
                    closeBtn.onclick = () => this.closePanel(`progress-${jobId}`);
                    actionsEl.appendChild(closeBtn);
                    if (!success && !result?.cancelled) {
                        const cleanupBtn = document.createElement('button');
                        cleanupBtn.className = 'scaler-btn scaler-btn-danger';
                        cleanupBtn.textContent = 'Cleanup';
                        cleanupBtn.onclick = async () => {
                            try {
                                await ScalerAPI.cleanupHeldJob(jobId);
                                this.showNotification('Cleanup complete', 'success');
                                cleanupBtn.disabled = true;
                                cleanupBtn.textContent = 'Cleaned';
                            } catch (e) {
                                this.showNotification(e.message, 'error');
                            }
                        };
                        actionsEl.appendChild(cleanupBtn);
                    }
                }

                this.showNotification(
                    success ? 'Operation completed successfully' : (result?.cancelled ? 'Cancelled' : 'Operation failed'),
                    success ? 'success' : 'error'
                );

                options.onComplete?.(success, { ...result, job_id: jobId });
            },
            onError: (message) => {
                const dot = document.querySelector(`#progress-terminal-${jobId} .scaler-terminal-dot`);
                if (dot) dot.classList.add('error');
                this.showNotification(`Error: ${message}`, 'error');
            }
        });

        this.state.jobs[jobId] = { ws, panel };
        return panel;
    },
    
    showNotification(message, type = 'info') {
        if (window.NotificationManager) {
            window.NotificationManager.showNotification(window.topologyEditor, message, type);
        } else if (window.topologyEditor?.showToast) {
            window.topologyEditor.showToast(message, type);
        } else {
            console.log(`[ScalerGUI] ${type.toUpperCase()}: ${message}`);
        }
    },
    
    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },
    
    // Placeholder methods for additional features
    async syncAllDevices() {
        // Create modal overlay
        const overlay = document.createElement('div');
        overlay.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.6); z-index: 9999; display: flex; align-items: center; justify-content: center;';
        
        // Create the sync panel
        const panel = document.createElement('div');
        panel.style.cssText = 'background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%); border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.5); width: 500px; max-width: 90vw; max-height: 80vh; display: flex; flex-direction: column; overflow: hidden;';
        panel.innerHTML = `
            <div style="padding: 15px 20px; border-bottom: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.02);">
                <h3 style="margin: 0; color: #fff; font-size: 16px;">🔄 Syncing All Devices</h3>
                <button id="sync-close-btn" style="background: none; border: none; color: #888; font-size: 24px; cursor: pointer; padding: 0 5px; display: none;">&times;</button>
            </div>
            <div style="padding: 20px; overflow-y: auto; flex: 1;">
                <div id="sync-status-msg" style="font-size: 14px; margin-bottom: 15px; color: #aaa;">
                    Fetching device list...
                </div>
                <div id="sync-device-list" style="max-height: 300px; overflow-y: auto;"></div>
                <div id="sync-summary" style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); display: none;">
                    <strong style="color: #fff;">Summary:</strong> <span id="sync-summary-text"></span>
                </div>
            </div>
        `;
        overlay.appendChild(panel);
        document.body.appendChild(overlay);
        
        const statusMsg = panel.querySelector('#sync-status-msg');
        const deviceList = panel.querySelector('#sync-device-list');
        const summary = panel.querySelector('#sync-summary');
        const summaryText = panel.querySelector('#sync-summary-text');
        const closeBtn = panel.querySelector('#sync-close-btn');
        
        closeBtn.onclick = () => overlay.remove();
        
        let successCount = 0;
        let failCount = 0;
        
        try {
            const data = await ScalerAPI.getDevices();
            
            if (data.devices.length === 0) {
                statusMsg.innerHTML = '⚠️ No devices registered. Add devices first.';
                statusMsg.style.color = 'var(--warning-color, orange)';
                closeBtn.style.display = 'block';
                return;
            }
            
            statusMsg.innerHTML = `Syncing ${data.devices.length} device(s)... Extracting running configs via SSH.`;
            
            // Create device status rows
            for (const device of data.devices) {
                const row = document.createElement('div');
                row.id = `sync-row-${device.id}`;
                row.style.cssText = 'display: flex; justify-content: space-between; padding: 8px 12px; margin-bottom: 4px; background: var(--bg-secondary); border-radius: 4px; align-items: center;';
                row.innerHTML = `
                    <span style="font-weight: 500;">${device.hostname || device.id}</span>
                    <span class="sync-status" style="color: var(--text-secondary);">
                        <span class="sync-spinner" style="display: inline-block; animation: spin 1s linear infinite;">⏳</span> Connecting...
                    </span>
                `;
                deviceList.appendChild(row);
            }
            
            // Sync each device and update status
            for (const device of data.devices) {
                const row = panel.querySelector(`#sync-row-${device.id}`);
                const statusSpan = row.querySelector('.sync-status');
                
                try {
                    statusSpan.innerHTML = '<span style="display: inline-block; animation: spin 1s linear infinite;">⏳</span> Extracting config...';
                    
                    const result = await ScalerAPI.syncDevice(device.id);
                    
                    successCount++;
                    statusSpan.innerHTML = `[OK] Synced (${result.lines || '?'} lines)`;
                    statusSpan.style.color = 'var(--success-color, #4caf50)';
                    row.style.background = 'rgba(76, 175, 80, 0.1)';
                } catch (e) {
                    failCount++;
                    statusSpan.innerHTML = `[ERROR] ${e.message}`;
                    statusSpan.style.color = 'var(--error-color, #f44336)';
                    row.style.background = 'rgba(244, 67, 54, 0.1)';
                }
            }
            
            // Show summary
            summary.style.display = 'block';
            if (failCount === 0) {
                summaryText.innerHTML = `<span style="color: var(--success-color, #4caf50);">[OK] All ${successCount} device(s) synced successfully!</span>`;
                statusMsg.innerHTML = '[OK] Sync complete! Config cache updated.';
                statusMsg.style.color = 'var(--success-color, #4caf50)';
                    } else {
                summaryText.innerHTML = `<span style="color: var(--success-color, #4caf50);">${successCount} succeeded</span>, <span style="color: var(--error-color, #f44336);">${failCount} failed</span>`;
                statusMsg.innerHTML = '⚠️ Sync completed with errors.';
                statusMsg.style.color = 'var(--warning-color, orange)';
            }
            
            closeBtn.style.display = 'block';
            
        } catch (error) {
            statusMsg.innerHTML = `[ERROR] Failed to fetch devices: ${error.message}`;
            statusMsg.style.color = 'var(--error-color, #f44336)';
            closeBtn.style.display = 'block';
        }
    },
    
    async openQuickLoad() {
        // Get devices first
        let devices;
        try {
            const data = await ScalerAPI.getDevices();
            devices = data.devices || [];
        } catch (e) {
            this.showNotification('Failed to get devices: ' + e.message, 'error');
            return;
        }
        
        if (devices.length === 0) {
            this.showNotification('No devices registered. Add devices first.', 'warning');
            return;
        }

        // Build the panel content HTML
        const content = document.createElement('div');
        content.innerHTML = `
            <div class="scaler-form-group" style="margin-bottom: 15px;">
                <label>Select Device</label>
                <select id="quickload-device" class="scaler-select">
                    ${devices.map(d => `<option value="${d.id}">${d.hostname || d.id}</option>`).join('')}
                </select>
            </div>
            <div id="quickload-files" style="min-height: 200px; max-height: 400px; overflow-y: auto; border: 1px solid var(--border-color); border-radius: 6px; padding: 10px;">
                <div style="color: var(--text-secondary); text-align: center; padding: 40px;">
                    Loading saved configs...
                </div>
            </div>
            <div id="quickload-preview" style="display: none; margin-top: 15px; border-top: 1px solid var(--border-color); padding-top: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <strong id="quickload-preview-title" style="color: var(--text-primary);">Preview</strong>
                    <div>
                        <button id="quickload-push-btn" class="scaler-btn scaler-btn-primary" style="margin-right: 8px;">📤 Push to Device</button>
                        <button id="quickload-compare-btn" class="scaler-btn">🔍 Compare</button>
                    </div>
                </div>
                <pre id="quickload-preview-content" class="scaler-syntax-preview" style="max-height: 200px; overflow: auto; font-size: 12px; background: var(--bg-tertiary); padding: 10px; border-radius: 4px;"></pre>
            </div>
        `;

        // Use the existing openPanel system which works correctly
        this.openPanel('quick-load', '📂 Quick Load Saved Configs', content, { width: '600px' });

        // Setup after panel is rendered
        setTimeout(() => {
            const deviceSelect = document.getElementById('quickload-device');
            const filesContainer = document.getElementById('quickload-files');
            const previewSection = document.getElementById('quickload-preview');
            const previewTitle = document.getElementById('quickload-preview-title');
            const previewContent = document.getElementById('quickload-preview-content');
            const pushBtn = document.getElementById('quickload-push-btn');
            const compareBtn = document.getElementById('quickload-compare-btn');
            
            if (!deviceSelect || !filesContainer) {
                return;
            }

            let selectedFile = null;

            const loadFiles = async (deviceId) => {
                filesContainer.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-secondary);">⏳ Loading saved configs...</div>';
                if (previewSection) previewSection.style.display = 'none';
                
                try {
                    const response = await fetch(`/api/config/${encodeURIComponent(deviceId)}/saved-files`);
                    if (!response.ok) throw new Error('Failed to load files');
                    const data = await response.json();
                    
                    if (!data.files || data.files.length === 0) {
                        filesContainer.innerHTML = `
                            <div style="text-align: center; padding: 40px; color: var(--text-secondary);">
                                <div style="font-size: 40px; margin-bottom: 15px;">📭</div>
                                <div style="font-size: 14px;">No saved configs found for this device.</div>
                                <div style="font-size: 12px; margin-top: 8px; opacity: 0.7;">Use the wizards to generate and save configs.</div>
                            </div>
                        `;
                        return;
                    }
                    
                    filesContainer.innerHTML = data.files.map(f => `
                        <div class="quickload-file-item" data-path="${f.path}" data-filename="${f.filename}" 
                             style="display: flex; justify-content: space-between; align-items: center; padding: 12px; 
                                    margin-bottom: 6px; background: var(--bg-secondary); border-radius: 6px; cursor: pointer;
                                    border: 2px solid transparent; transition: all 0.15s ease;">
                            <div style="flex: 1;">
                                <div style="font-weight: 500; color: var(--text-primary); margin-bottom: 4px;">${f.filename}</div>
                                <div style="font-size: 11px; color: var(--text-secondary);">
                                    📅 ${f.timestamp} • 📝 ${f.lines} lines
                                    ${f.pushed ? ' • <span style="color: #4caf50;">✓ Pushed</span>' : ''}
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <button class="quickload-delete-btn" data-path="${f.path}" data-filename="${f.filename}"
                                        style="background: transparent; border: 1px solid #dc3545; color: #dc3545; 
                                               padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 11px;
                                               transition: all 0.15s ease;"
                                        onmouseover="this.style.background='#dc3545';this.style.color='#fff';"
                                        onmouseout="this.style.background='transparent';this.style.color='#dc3545';">
                                    🗑️ Delete
                                </button>
                                <span style="color: var(--text-secondary); font-size: 18px;">›</span>
                            </div>
                        </div>
                    `).join('');
                    
                    // Add click handlers for file selection
                    filesContainer.querySelectorAll('.quickload-file-item').forEach(item => {
                        item.onclick = async (e) => {
                            // Don't trigger if clicking the delete button
                            if (e.target.closest('.quickload-delete-btn')) return;
                            
                            // Highlight selected
                            filesContainer.querySelectorAll('.quickload-file-item').forEach(i => {
                                i.style.borderColor = 'transparent';
                                i.style.background = 'var(--bg-secondary)';
                            });
                            item.style.borderColor = 'var(--primary-color, #7c3aed)';
                            item.style.background = 'rgba(124, 58, 237, 0.15)';
                            
                            selectedFile = {
                                path: item.dataset.path,
                                filename: item.dataset.filename,
                                deviceId: deviceId
                            };
                            
                            // Load preview
                            if (previewTitle) previewTitle.textContent = `Preview: ${item.dataset.filename}`;
                            if (previewContent) previewContent.textContent = 'Loading...';
                            if (previewSection) previewSection.style.display = 'block';
                            
                            try {
                                const resp = await fetch(`/api/config/file?path=${encodeURIComponent(item.dataset.path)}`);
                                if (resp.ok) {
                                    const text = await resp.text();
                                    if (previewContent) {
                                        previewContent.textContent = text.substring(0, 5000) + (text.length > 5000 ? '\n\n... (truncated)' : '');
                                    }
                                } else {
                                    if (previewContent) previewContent.textContent = '(Could not load preview)';
                                }
                            } catch (e) {
                                if (previewContent) previewContent.textContent = '(Error loading preview)';
                            }
                        };
                    });
                    
                    // Add click handlers for delete buttons
                    filesContainer.querySelectorAll('.quickload-delete-btn').forEach(btn => {
                        btn.onclick = async (e) => {
                            e.stopPropagation(); // Prevent file selection
                            const filePath = btn.dataset.path;
                            const fileName = btn.dataset.filename;
                            
                            if (!confirm(`Are you sure you want to delete "${fileName}"?\n\nThis action cannot be undone.`)) {
                                return;
                            }
                            
                            try {
                                const resp = await fetch(`/api/config/file?path=${encodeURIComponent(filePath)}`, {
                                    method: 'DELETE'
                                });
                                if (resp.ok) {
                                    this.showNotification(`Deleted ${fileName}`, 'success');
                                    // Refresh the file list
                                    loadFiles(deviceId);
                                    // Clear preview if this was the selected file
                                    if (selectedFile && selectedFile.path === filePath) {
                                        selectedFile = null;
                                        if (previewSection) previewSection.style.display = 'none';
                                    }
                                } else {
                                    const error = await resp.json();
                                    throw new Error(error.detail || 'Delete failed');
                                }
                            } catch (e) {
                                this.showNotification(`Delete failed: ${e.message}`, 'error');
                            }
                        };
                    });
                    
                } catch (e) {
                    filesContainer.innerHTML = `<div style="color: var(--error-color); padding: 40px; text-align: center;">[ERROR] ${e.message}</div>`;
                }
            };
            
            deviceSelect.onchange = () => loadFiles(deviceSelect.value);
            
            if (pushBtn) {
                pushBtn.onclick = async () => {
                    if (!selectedFile) {
                        this.showNotification('Select a file first', 'warning');
                        return;
                    }
                    // Push the config to device
                    try {
                        const configContent = await fetch(`/api/config/file?path=${encodeURIComponent(selectedFile.path)}`).then(r => r.text());
                        const resp = await fetch(`/api/config/${encodeURIComponent(selectedFile.deviceId)}/push`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ config: configContent, filename: selectedFile.filename })
                        });
                        if (resp.ok) {
                            this.showNotification(`Pushed ${selectedFile.filename} to device`, 'success');
                        } else {
                            throw new Error('Push failed');
                        }
                    } catch (e) {
                        this.showNotification(`Push failed: ${e.message}`, 'error');
                    }
                };
            }
            
            if (compareBtn) {
                compareBtn.onclick = async () => {
                    if (!selectedFile) {
                        this.showNotification('Select a file first', 'warning');
                        return;
                    }
                    this.openDeviceCompare();
                };
            }
            
            // Load first device's files automatically
            loadFiles(devices[0].id);
        }, 100);
    },
    async openBGPWizard(deviceId = null, prefillParams = null) {
        if (!deviceId) { this.openDeviceSelector('BGP Configuration', (id) => this.openBGPWizard(id, prefillParams)); return; }
        const content = document.createElement('div');
        content.innerHTML = '<div class="scaler-loading">Loading...</div>';
        this.openPanel('bgp-wizard', `BGP Wizard - ${deviceId}`, content, { width: '520px', parentPanel: 'scaler-menu' });
        const self = this;
        const cachedCtx = this._deviceContexts[deviceId];
        const hasFresh = cachedCtx && (Date.now() - (cachedCtx._fetchedAt || 0)) < this._contextCacheTTL;
        let ctx = hasFresh ? this._applyPendingChanges(deviceId, cachedCtx) : null;
        const summary = ctx?.config_summary || {};
        const localAs = summary.as_number ? parseInt(summary.as_number, 10) : 65000;
        this.WizardController.init({
            panelName: 'bgp-wizard',
            quickNavKey: 'bgp-wizard',
            title: `BGP Wizard - ${deviceId}`,
            initialData: { deviceId, deviceContext: ctx, local_as: isNaN(localAs) ? 65000 : localAs, ...(prefillParams || {}) },
            lastRunWizardType: 'bgp',
            onLastRunRerun: (rec) => {
                if (rec?.params) {
                    Object.assign(self.WizardController.data, rec.params);
                    self.WizardController.data.deviceId = deviceId;
                    self.WizardController.data.deviceContext = ctx;
                    self.WizardController.currentStep = 0;
                    self.WizardController._highestStepReached = 0;
                    self.WizardController.render();
                }
            },
            onLastRunRerunOther: (rec) => {
                self.closePanel('bgp-wizard');
                self.openMirrorWizard(rec.deviceId);
            },
            wizardHeader: (data) => self.renderContextPanel(deviceId, data.deviceContext || {}, { onRefresh: () => self.refreshDeviceContextLive(deviceId).then(c => { self.WizardController.data.deviceContext = c; self.WizardController.render(); }) }),
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
                            <div class="scaler-form-row">
                                <div class="scaler-form-group"><label>Peer IP Start</label><input type="text" id="bgp-peer-ip" class="scaler-input" value="${d.peer_ip_start || '10.0.0.1'}" placeholder="10.0.0.1"></div>
                                <div class="scaler-form-group"><label>Count</label><input type="number" id="bgp-count" class="scaler-input" value="${d.count || 1}" min="1"></div>
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
                        return `
                        <div class="scaler-form">
                            <div class="scaler-form-group">
                                <label>Address Families</label>
                                <div class="scaler-checkbox-group" id="bgp-af-group">
                                    ${afList.map(af => `<label class="scaler-checkbox"><input type="checkbox" name="bgp-af" value="${af}" ${afs.includes(af) ? 'checked' : ''}> ${af}</label>`).join('')}
                                </div>
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
                            } catch (_) {}
                        } catch (e) {
                            const el = document.getElementById('bgp-review-config');
                            if (el) el.textContent = `Error: ${e.message}`;
                        }
                    }
                },
                {
                    title: 'Push',
                    finalButtonText: 'Commit Check',
                    render: (data) => {
                        const ctx = data.deviceContext || {};
                        const host = ctx.mgmt_ip || ctx.ip || '';
                        return `
                        <div class="scaler-form">
                            <div class="scaler-form-group">
                                <label>Delivery Method</label>
                                <div class="scaler-radio-group">
                                    <label class="scaler-radio">
                                        <input type="radio" name="push-mode" value="dry_run" checked>
                                        <span><strong>Commit Check First</strong></span>
                                    </label>
                                    <div class="scaler-radio-desc">Paste config via SSH terminal, run <code>commit check</code>.
                                    If check passes, you can commit from the result dialog.</div>
                                    <label class="scaler-radio">
                                        <input type="radio" name="push-mode" value="merge">
                                        <span><strong>Commit Directly</strong></span>
                                    </label>
                                    <div class="scaler-radio-desc">Paste config via SSH terminal + <code>commit</code>.</div>
                                    <label class="scaler-radio">
                                        <input type="radio" name="push-mode" value="clipboard">
                                        <span><strong>Copy to Clipboard + Open SSH</strong></span>
                                    </label>
                                </div>
                            </div>
                            <div class="scaler-info-box" style="font-size:12px">
                                <strong>Target:</strong> ${data.deviceId}${host ? ` (${host})` : ''}<br>
                                <strong>Config:</strong> ${data.count} BGP peer${data.count > 1 ? 's' : ''}, AS ${data.peer_as}
                            </div>
                        </div>`;
                    },
                    afterRender: () => {
                        document.querySelectorAll('input[name="push-mode"]').forEach(r => {
                            r.addEventListener('change', () => {
                                const btn = document.getElementById('wizard-next');
                                const mode = document.querySelector('input[name="push-mode"]:checked')?.value;
                                if (btn) btn.textContent = mode === 'clipboard' ? 'Copy & Open SSH' : mode === 'merge' ? 'Commit' : 'Commit Check';
                            });
                        });
                    },
                    collectData: () => {
                        const mode = document.querySelector('input[name="push-mode"]:checked')?.value || 'dry_run';
                        return { dryRun: mode === 'dry_run', pushMode: mode };
                    }
                }
            ],
            onComplete: async (data) => {
                if (data.pushMode === 'clipboard') {
                    const config = data.generatedConfig || '';
                    try { await navigator.clipboard.writeText(config); } catch (_) {}
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
            }).catch(() => {});
        }
    },
    async openIGPWizard(deviceId = null, prefillParams = null) {
        if (!deviceId) { this.openDeviceSelector('IGP Configuration', (id) => this.openIGPWizard(id, prefillParams)); return; }
        const content = document.createElement('div');
        content.innerHTML = '<div class="scaler-loading">Loading...</div>';
        this.openPanel('igp-wizard', `IGP Wizard - ${deviceId}`, content, { width: '520px', parentPanel: 'scaler-menu' });
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
            onLastRunRerun: (rec) => {
                if (rec?.params) {
                    Object.assign(self.WizardController.data, rec.params);
                    self.WizardController.data.deviceId = deviceId;
                    self.WizardController.data.deviceContext = ctx;
                    self.WizardController.currentStep = 0;
                    self.WizardController._highestStepReached = 0;
                    self.WizardController.render();
                }
            },
            onLastRunRerunOther: (rec) => {
                self.closePanel('igp-wizard');
                self.openMirrorWizard(rec.deviceId);
            },
            wizardHeader: (data) => self.renderContextPanel(deviceId, data.deviceContext || {}, { onRefresh: () => self.refreshDeviceContextLive(deviceId).then(c => { self.WizardController.data.deviceContext = c; self.WizardController.render(); }) }),
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
                            <div class="scaler-form-group"><label>Router IP</label><input type="text" id="igp-router-ip" class="scaler-input" value="${routerIp}"></div>
                            <div class="scaler-form-group"><label>Interfaces (comma-separated)</label><input type="text" id="igp-ifaces" class="scaler-input" value="${ifaces}" placeholder="loopback0, ge100-0/0/0"></div>
                            <div id="igp-ifaces-suggestions"></div>
                            <div class="scaler-form-row">
                                <label class="scaler-checkbox"><input type="checkbox" id="igp-passive" ${d.passive_for_all ? 'checked' : ''}> Passive (all interfaces)</label>
                                <div class="scaler-form-group" style="flex:1;max-width:120px"><label>Default Metric</label><input type="number" id="igp-metric" class="scaler-input" value="${d.default_metric || ''}" placeholder="Optional" min="1"></div>
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
                        document.getElementById('igp-protocol')?.addEventListener('change', (e) => {
                            const row = document.getElementById('igp-isis-level-row');
                            if (row) row.style.display = e.target.value === 'isis' ? 'block' : 'none';
                        });
                        let t;
                        const up = async () => {
                            clearTimeout(t);
                            t = setTimeout(async () => {
                                try {
                                    const prot = document.getElementById('igp-protocol')?.value || 'isis';
                                    const ifaces = (document.getElementById('igp-ifaces')?.value || '').split(',').map(s => s.trim()).filter(Boolean);
                                    const params = {
                                        protocol: prot,
                                        area_id: document.getElementById('igp-area')?.value || '49.0001',
                                        router_ip: document.getElementById('igp-router-ip')?.value || '1.1.1.1',
                                        interfaces: ifaces.length ? ifaces : ['loopback0'],
                                        passive_for_all: document.getElementById('igp-passive')?.checked || false,
                                        default_metric: document.getElementById('igp-metric')?.value || undefined
                                    };
                                    if (prot === 'isis') params.level = document.getElementById('igp-level')?.value || 'level-1-2';
                                    const r = await ScalerAPI.generateIGP(params);
                                    const p = document.getElementById('igp-preview');
                                    if (p) p.textContent = r.config || '(empty)';
                                } catch (e) { const p = document.getElementById('igp-preview'); if (p) p.textContent = e.message; }
                            }, 300);
                        };

                        ['igp-protocol','igp-level','igp-area','igp-router-ip','igp-ifaces','igp-passive','igp-metric'].forEach(id => { const el = document.getElementById(id); if (el) el.oninput = up; el && (el.onchange = up); });
                        up();
                    },
                    collectData: () => {
                        const prot = document.getElementById('igp-protocol')?.value || 'isis';
                        return {
                            protocol: prot,
                            area_id: document.getElementById('igp-area')?.value || '49.0001',
                            router_ip: document.getElementById('igp-router-ip')?.value || '1.1.1.1',
                            interfaces: (document.getElementById('igp-ifaces')?.value || '').split(',').map(s => s.trim()).filter(Boolean) || ['loopback0'],
                            level: prot === 'isis' ? (document.getElementById('igp-level')?.value || 'level-1-2') : undefined,
                            passive_for_all: document.getElementById('igp-passive')?.checked || false,
                            default_metric: document.getElementById('igp-metric')?.value || undefined
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
                            } catch (_) {}
                        } catch (e) {
                            const el = document.getElementById('igp-review-config');
                            if (el) el.textContent = `Error: ${e.message}`;
                        }
                    }
                },
                {
                    title: 'Push',
                    finalButtonText: 'Commit Check',
                    render: (data) => {
                        const ctx = data.deviceContext || {};
                        const host = ctx.mgmt_ip || ctx.ip || '';
                        return `
                        <div class="scaler-form">
                            <div class="scaler-form-group">
                                <label>Delivery Method</label>
                                <div class="scaler-radio-group">
                                    <label class="scaler-radio">
                                        <input type="radio" name="push-mode" value="dry_run" checked>
                                        <span><strong>Commit Check First</strong></span>
                                    </label>
                                    <div class="scaler-radio-desc">Paste config via SSH terminal, run <code>commit check</code>.
                                    If check passes, you can commit from the result dialog.</div>
                                    <label class="scaler-radio">
                                        <input type="radio" name="push-mode" value="merge">
                                        <span><strong>Commit Directly</strong></span>
                                    </label>
                                    <div class="scaler-radio-desc">Paste config via SSH terminal + <code>commit</code>.</div>
                                    <label class="scaler-radio">
                                        <input type="radio" name="push-mode" value="clipboard">
                                        <span><strong>Copy to Clipboard + Open SSH</strong></span>
                                    </label>
                                </div>
                            </div>
                            <div class="scaler-info-box" style="font-size:12px">
                                <strong>Target:</strong> ${data.deviceId}${host ? ` (${host})` : ''}<br>
                                <strong>Config:</strong> ${(data.protocol || 'isis').toUpperCase()} on ${(data.interfaces || []).length} interface${(data.interfaces || []).length > 1 ? 's' : ''}
                            </div>
                        </div>`;
                    },
                    afterRender: () => {
                        document.querySelectorAll('input[name="push-mode"]').forEach(r => {
                            r.addEventListener('change', () => {
                                const btn = document.getElementById('wizard-next');
                                const mode = document.querySelector('input[name="push-mode"]:checked')?.value;
                                if (btn) btn.textContent = mode === 'clipboard' ? 'Copy & Open SSH' : mode === 'merge' ? 'Commit' : 'Commit Check';
                            });
                        });
                    },
                    collectData: () => {
                        const mode = document.querySelector('input[name="push-mode"]:checked')?.value || 'dry_run';
                        return { dryRun: mode === 'dry_run', pushMode: mode };
                    }
                }
            ],
            onComplete: async (data) => {
                if (data.pushMode === 'clipboard') {
                    const config = data.generatedConfig || '';
                    try { await navigator.clipboard.writeText(config); } catch (_) {}
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
            }).catch(() => {});
        }
    },
    openMirrorWizard(prefillSourceId, prefillTargetId) {
        const devices = this._getCanvasDevices();
        if (devices.length < 2) { this.showNotification('Add at least 2 devices to the canvas to mirror', 'warning'); return; }
        const deviceItems = devices.map(id => ({ id, hostname: id, ip: '' }));
        if (prefillSourceId && prefillTargetId) {
            if (prefillSourceId === prefillTargetId) { this.showNotification('Source and target must be different', 'warning'); return; }
            this._openMirrorWizardPanel(prefillSourceId, prefillTargetId);
            return;
        }
        if (prefillSourceId) {
            this.openDeviceSelector('Mirror Config - Select target device', (targetId) => {
                if (prefillSourceId === targetId) { this.showNotification('Source and target must be different', 'warning'); return; }
                this._openMirrorWizardPanel(prefillSourceId, targetId);
            }, { devices: deviceItems });
            return;
        }
        this.openDeviceSelector('Mirror Config - Select source device', (sourceId) => {
            this.openDeviceSelector('Mirror Config - Select target device', (targetId) => {
                if (sourceId === targetId) { this.showNotification('Source and target must be different', 'warning'); return; }
                this._openMirrorWizardPanel(sourceId, targetId);
            }, { devices: deviceItems });
        }, { devices: deviceItems });
    },

    _openMirrorWizardPanel(sourceId, targetId) {
        const content = document.createElement('div');
        content.className = 'scaler-mirror-wizard';
        content.innerHTML = `
            <div class="scaler-form">
                <div class="scaler-info-box">Copy config from <strong>${this.escapeHtml(sourceId)}</strong> to <strong>${this.escapeHtml(targetId)}</strong>.</div>
                <div class="scaler-form-group">
                    <button type="button" class="scaler-btn scaler-btn-primary" id="mirror-analyze">Analyze</button>
                </div>
                <div id="mirror-analysis" style="display:none"></div>
                <div id="mirror-generate-section" style="display:none">
                    <div class="scaler-form-group">
                        <button type="button" class="scaler-btn scaler-btn-primary" id="mirror-generate">Generate Config</button>
                    </div>
                </div>
                <div id="mirror-config-preview" style="display:none">
                    <label>Generated Config:</label>
                    <pre id="mirror-config-text"></pre>
                    <div class="scaler-form-group">
                        <button type="button" class="scaler-btn scaler-btn-secondary" id="mirror-show-diff">Show diff vs target</button>
                        <button type="button" class="scaler-btn scaler-btn-primary" id="mirror-push">Push to Target</button>
                    </div>
                    <pre id="mirror-diff" style="display:none"></pre>
                </div>
            </div>
        `;
        this.openPanel('mirror-wizard', `Mirror: ${sourceId} -> ${targetId}`, content, { width: '580px', parentPanel: 'scaler-menu' });
        let analysisResult = null;
        let generatedConfig = null;
        const srcResolved = this._resolveDeviceId(sourceId);
        const tgtResolved = this._resolveDeviceId(targetId);
        const srcSsh = srcResolved?.sshHost || '';
        const tgtSsh = tgtResolved?.sshHost || '';
        document.getElementById('mirror-analyze').onclick = async () => {
            const btn = document.getElementById('mirror-analyze');
            btn.disabled = true;
            btn.textContent = 'Analyzing...';
            try {
                analysisResult = await ScalerAPI.mirrorAnalyze({
                    source_device_id: sourceId,
                    target_device_id: targetId,
                    ssh_hosts: [srcSsh, tgtSsh]
                });
                const el = document.getElementById('mirror-analysis');
                el.style.display = 'block';
                const sd = analysisResult.smart_diff?.summary || {};
                el.innerHTML = `
                    <div class="scaler-mirror-summary">
                        <div>FXC: ${sd.need_add || 0} add, ${sd.need_modify || 0} modify, ${sd.need_delete || 0} delete, ${sd.can_skip || 0} identical</div>
                        <div>VPLS: same structure</div>
                        <div>Interfaces: ${(analysisResult.smart_diff?.interfaces?.add?.length || 0)} to add</div>
                    </div>
                `;
                document.getElementById('mirror-generate-section').style.display = 'block';
            } catch (e) {
                this.showNotification(e.message, 'error');
            }
            btn.disabled = false;
            btn.textContent = 'Analyze';
        };
        document.getElementById('mirror-generate').onclick = async () => {
            const btn = document.getElementById('mirror-generate');
            btn.disabled = true;
            btn.textContent = 'Generating...';
            try {
                const r = await ScalerAPI.mirrorGenerate({
                    source_device_id: sourceId,
                    target_device_id: targetId,
                    ssh_hosts: [srcSsh, tgtSsh],
                    interface_map: analysisResult?.interface_map || {},
                    output_mode: 'diff_only'
                });
                generatedConfig = r.config;
                document.getElementById('mirror-config-text').textContent = generatedConfig || '(empty)';
                document.getElementById('mirror-config-preview').style.display = 'block';
            } catch (e) {
                this.showNotification(e.message, 'error');
            }
            btn.disabled = false;
            btn.textContent = 'Generate Config';
        };
        document.getElementById('mirror-show-diff').onclick = async () => {
            try {
                const r = await ScalerAPI.mirrorPreviewDiff({
                    target_device_id: targetId,
                    config: generatedConfig,
                    ssh_host: tgtSsh
                });
                const diffEl = document.getElementById('mirror-diff');
                diffEl.textContent = r.diff_text || '(no diff)';
                diffEl.style.display = diffEl.style.display === 'none' ? 'block' : 'none';
            } catch (e) {
                this.showNotification(e.message, 'error');
            }
        };
        document.getElementById('mirror-push').onclick = async () => {
            if (!generatedConfig) return;
            try {
                const result = await ScalerAPI.pushConfig({
                    device_id: targetId,
                    config: generatedConfig,
                    hierarchy: 'network-services',
                    mode: 'merge',
                    dry_run: true,
                    ssh_host: tgtSsh,
                    job_name: `Mirror ${sourceId} -> ${targetId}`
                });
                this.closePanel('mirror-wizard');
                this.showProgress(result.job_id, `Mirror: ${sourceId} -> ${targetId}`, {
                    onComplete: (success, res) => {
                        if (success) this.showNotification('Mirror committed successfully', 'success');
                        else if (!res?.cancelled) this.showNotification('Mirror push failed', 'error');
                    }
                });
            } catch (e) {
                this.showNotification(e.message, 'error');
            }
        };
    },

    openDeviceCompare() {
        const devices = this._getCanvasDevices();
        if (devices.length < 2) { this.showNotification('Add at least 2 devices to the canvas to compare', 'warning'); return; }
        const deviceItems = devices.map(id => ({ id, hostname: id, ip: '' }));
        this.openDeviceSelector('Compare Configs (select first)', (id1) => {
            this.state._compareFirst = id1;
            this.openDeviceSelector('Compare Configs (select second)', async (id2) => {
                if (id1 === id2) { this.showNotification('Select two different devices', 'warning'); return; }
                const content = document.createElement('div');
                content.innerHTML = '<div class="scaler-loading">Comparing configs...</div>';
                this.openPanel('config-compare', `Compare: ${id1} vs ${id2}`, content, { width: '600px' });
                try {
                    const r = await ScalerAPI.compareConfigs([id1, id2]);
                    content.innerHTML = `<div class="scaler-diff-view"><pre>${this.escapeHtml(r.diff_text || '(no diff)')}</pre></div>`;
                } catch (e) { content.innerHTML = `<div class="scaler-error">${e.message}</div>`; }
            }, { devices: deviceItems });
        }, { devices: deviceItems });
    },
    openSyncStatus() {
        const devices = this._getCanvasDevices();
        if (!devices.length) { this.showNotification('Add devices to the canvas first', 'warning'); return; }
        const content = document.createElement('div');
        content.className = 'scaler-sync-status';
        content.innerHTML = '<div class="scaler-loading">Checking sync status...</div>';
        this.openPanel('sync-status', 'Sync Status', content, { width: '500px' });
        (async () => {
            const html = [];
            for (const d of devices) {
                try {
                    const r = await ScalerAPI.getConfigDiff(d);
                    html.push(`<div class="scaler-sync-row"><span>${d}</span><span class="${r.in_sync ? 'scaler-sync-ok' : 'scaler-sync-out'}">${r.in_sync ? 'In sync' : 'Out of sync'}</span><button class="scaler-btn" data-dev="${d}">View diff</button></div>`);
                } catch (e) { html.push(`<div class="scaler-sync-row"><span>${d}</span><span class="scaler-sync-err">${e.message}</span></div>`); }
            }
            content.innerHTML = html.join('') || '<div class="scaler-empty">No devices</div>';
            content.querySelectorAll('[data-dev]').forEach(btn => {
                btn.onclick = () => {
                    const dev = btn.dataset.dev;
                    ScalerAPI.getConfigDiff(dev).then(r => {
                        const pop = document.createElement('div');
                        pop.className = 'scaler-diff-popup';
                        pop.innerHTML = `<pre>${this.escapeHtml(r.diff_text || '')}</pre>`;
                        pop.onclick = () => pop.remove();
                        document.body.appendChild(pop);
                    });
                };
            });
        })();
    },
    openDeleteHierarchy(deviceId) {
        if (!deviceId) { this.openDeviceSelector('Delete Hierarchy', (id) => this.openDeleteHierarchy(id)); return; }
        const hierarchies = ['system','interfaces','services','bgp','igp','multihoming','vrf','flowspec'];
        const content = document.createElement('div');
        content.innerHTML = `
            <div class="scaler-form">
                <div class="scaler-form-group"><label>Hierarchy to delete</label><select id="dh-hierarchy" class="scaler-select">${hierarchies.map(h => `<option value="${h}">${h}</option>`).join('')}</select></div>
                <div class="scaler-form-group"><label><input type="checkbox" id="dh-dry" checked> Dry run (preview only)</label></div>
                <button id="dh-run" class="scaler-btn scaler-btn-primary">Execute</button>
                <pre id="dh-result" class="scaler-syntax-preview" style="margin-top:10px;min-height:60px;"></pre>
            </div>`;
        this.openPanel('delete-hierarchy', `Delete Hierarchy - ${deviceId}`, content, { width: '480px' });
        document.getElementById('dh-run').onclick = async () => {
            const hier = document.getElementById('dh-hierarchy').value;
            const dry = document.getElementById('dh-dry').checked;
            const res = document.getElementById('dh-result');
            res.textContent = 'Running...';
            try {
                const r = await ScalerAPI.deleteHierarchyOp(deviceId, hier, dry);
                res.textContent = JSON.stringify(r, null, 2);
                this.showNotification(dry ? 'Dry run complete' : 'Delete complete', 'success');
            } catch (e) { res.textContent = e.message; this.showNotification(e.message, 'error'); }
        };
    },
    openModifyInterfaces() {
        this.openDeviceSelector('Modify Interfaces', async (deviceId) => {
            const content = document.createElement('div');
            content.innerHTML = '<div class="scaler-loading">Loading interfaces...</div>';
            this.openPanel('modify-interfaces', `Modify Interfaces - ${deviceId}`, content, { width: '500px' });
            try {
                const r = await ScalerAPI.getInterfaces(deviceId);
                content.innerHTML = `<div class="scaler-form"><h4>Interfaces (${r.count})</h4><pre class="scaler-syntax-preview">${(r.interfaces || []).map(i => `${i.name} ${i.vlan || ''}`).join('\n') || 'None'}</pre><p class="scaler-summary-hint">Use scaler-wizard for add/remove. This panel shows current state.</p></div>`;
            } catch (e) { content.innerHTML = `<div class="scaler-error">${e.message}</div>`; }
        });
    },
    openBatchOperations() {
        const devices = this._getCanvasDevices();
        if (!devices.length) { this.showNotification('Add devices to the canvas first', 'warning'); return; }
        this.showNotification(`Batch ops: ${devices.length} devices. Use scaler-wizard for push/scale.`, 'info');
    },
    openTemplateManager() {
        const content = document.createElement('div');
        content.innerHTML = '<div class="scaler-loading">Loading templates...</div>';
        this.openPanel('template-manager', 'Policy Templates', content, { width: '500px' });
        ScalerAPI.getTemplates().then(r => {
            const tpl = (r.templates || []).map(t => `<div class="scaler-template-item"><strong>${t.name}</strong><br><span class="scaler-dim">${t.description || ''}</span></div>`).join('');
            content.innerHTML = tpl ? `<div class="scaler-form">${tpl}</div><p class="scaler-summary-hint">Use scaler-wizard to generate from templates.</p>` : '<div class="scaler-empty">No templates</div>';
        }).catch(e => { content.innerHTML = `<div class="scaler-error">${e.message}</div>`; });
    },
    async showConfigSummary(deviceId) {
        const content = document.createElement('div');
        content.className = 'scaler-config-summary';
        content.innerHTML = '<div class="scaler-loading">Loading config summary...</div>';
        this.openPanel('config-summary', `Config Summary - ${deviceId}`, content, {width: '420px', parentPanel: 'device-manager'});
        try {
            const summary = await ScalerAPI.getConfigSummary(deviceId);
            content.innerHTML = '';
            const lines = summary.lines;
            const lo0 = summary.loopback0_ip || '-';
            const asNum = summary.as_number || '-';
            const rid = summary.router_id || '-';
            const rts = (summary.route_targets || []).length;
            const mh = summary.multihoming_interfaces || 0;
            const evpn = summary.evpn_services || {};
            let evpnHtml = '';
            for (const [k, v] of Object.entries(evpn)) {
                evpnHtml += `<div class="scaler-summary-row"><span>${k}</span><span>${v}</span></div>`;
            }
            content.innerHTML = `
                <div class="scaler-summary-section">
                    <div class="scaler-summary-row"><span>Lines</span><span>${lines}</span></div>
                    <div class="scaler-summary-row"><span>Loopback0</span><span>${lo0}</span></div>
                    <div class="scaler-summary-row"><span>AS Number</span><span>${asNum}</span></div>
                    <div class="scaler-summary-row"><span>Router ID</span><span>${rid}</span></div>
                    <div class="scaler-summary-row"><span>Route Targets</span><span>${rts}</span></div>
                    <div class="scaler-summary-row"><span>MH Interfaces</span><span>${mh}</span></div>
                </div>
                ${evpnHtml ? `<div class="scaler-summary-section"><h5>EVPN Services</h5>${evpnHtml}</div>` : ''}
                <div class="scaler-summary-hint">Click Sync on the device card to refresh config.</div>
            `;
        } catch (e) {
            content.innerHTML = `<div class="scaler-error">${e.message}<br><br>Ensure scaler_bridge.py is running and device config is synced.</div>`;
        }
    },
    openAddDeviceDialog() {
        const content = document.createElement('div');
        content.innerHTML = `
            <div class="scaler-form">
                <div class="scaler-form-group"><label>Device IP</label><input type="text" id="add-device-ip" class="scaler-input" placeholder="192.168.1.1"></div>
                <button id="add-device-btn" class="scaler-btn scaler-btn-primary">Discover and Add</button>
                <div id="add-device-result" style="margin-top:10px;min-height:24px;"></div>
            </div>`;
        this.openPanel('add-device', 'Add Device', content, { width: '400px', parentPanel: 'device-manager' });
        document.getElementById('add-device-btn').onclick = async () => {
            const ip = (document.getElementById('add-device-ip').value || '').trim();
            const res = document.getElementById('add-device-result');
            if (!ip) { this.showNotification('Enter device IP', 'warning'); return; }
            res.textContent = 'Discovering...';
            try {
                const r = await ScalerAPI.discoverDevice(ip);
                res.textContent = `Added: ${r.hostname || r.key} (${r.ip})`;
                this.showNotification(`Device ${r.hostname || r.key} added`, 'success');
                if (this.state.activePanels['device-manager']) this.refreshDeviceList();
            } catch (e) { res.textContent = e.message; this.showNotification(e.message, 'error'); }
        };
    }
};

// Add ScalerAPI extensions for new endpoints
if (typeof ScalerAPI !== 'undefined') {
    ScalerAPI.imageUpgrade = async function(params) {
        const response = await fetch('/api/operations/image-upgrade', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Image upgrade failed');
        }
        return response.json();
    };
    
    ScalerAPI.stagCheck = async function(params) {
        const response = await fetch('/api/operations/stag-check', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Stag check failed');
        }
        return response.json();
    };
    
    ScalerAPI.scaleUpDown = async function(params) {
        const response = await fetch('/api/operations/scale-updown', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Scale operation failed');
        }
        return response.json();
    };
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => ScalerGUI.init());

console.log('[ScalerGUI] Loaded v2.0 with WizardController');
