console.log('%c[ScalerGUI] core module loaded', 'color:#ff9800;font-weight:bold;font-size:12px');
/**
 * SCALER GUI -- core (state, WizardController, shared builders, panels, menu, notifications)
 * @requires scaler-api.js
 * @version 2.1.0-modular
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
    // SHARED UTILITIES
    // =========================================================================

    _getCheckedDeviceIds(containerId) {
        return Array.from(
            document.querySelectorAll(`#${containerId} input:checked:not(:disabled)`)
        ).map(cb => cb.value);
    },

    _classifyDeviceState(stateStr) {
        if (!stateStr) return '';
        const s = stateStr.toUpperCase();
        if (s === 'UPGRADING') return 'UPGRADING';
        if (s === 'DEPLOYING') return 'DEPLOYING';
        const GI_STATES = ['GI', 'BASEOS_SHELL', 'ONIE'];
        const RECOVERY_STATES = ['RECOVERY', 'DN_RECOVERY'];
        if (GI_STATES.includes(s)) return 'GI';
        if (RECOVERY_STATES.includes(s)) return 'RECOVERY';
        if (s === 'DNOS' || s === 'STANDALONE') return 'DNOS';
        if (s === 'BOOT' || s === 'BOOTING') return 'BOOT';
        if (s === 'UNREACHABLE' || s === 'TIMEOUT' || s === 'SSH_FAILED') return 'UNREACHABLE';
        if (s === 'FAILED' || s === 'ERROR' || s === 'INSTALL_FAILED') return 'FAILED';
        if (s === 'INSTALLING') return 'INSTALLING';
        if (s === 'LOADING') return 'LOADING';
        if (s === 'CONFIG_REPAIR') return 'CONFIG_REPAIR';
        if (s) return s;
        return '';
    },

    _getDeviceMode(deviceId) {
        const editor = window.topologyEditor;
        if (editor?.objects) {
            const dev = editor.objects.find(o =>
                o.type === 'device' && (o.label === deviceId || o.id === deviceId)
            );
            if (dev?._deviceMode) return dev._deviceMode.toUpperCase();
        }
        return '';
    },

    _isDeviceConfigurable(deviceId) {
        const mode = this._getDeviceMode(deviceId);
        if (mode === 'GI' || mode === 'RECOVERY') {
            const modeLabel = mode === 'GI' ? 'GI' : 'Recovery';
            this.showNotification(
                `${deviceId} is in ${modeLabel} mode and cannot be configured. Deploy to DNOS first using the Image Upgrade wizard.`,
                'error', 8000
            );
            return false;
        }
        return true;
    },

    _parseStackVersions(components) {
        const out = { dnos: '--', gi: '--', baseos: '--' };
        if (!Array.isArray(components)) return out;
        for (const c of components) {
            const name = (c.name || c.component || '').toLowerCase();
            const ver = c.current || c.version || '';
            if (!ver || ver === '-') continue;
            if (name.includes('dnos') || name === 'system') out.dnos = ver;
            else if (name.includes('gi') || name.includes('generic')) out.gi = ver;
            else if (name.includes('baseos') || name.includes('base')) out.baseos = ver;
        }
        return out;
    },

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
            if (this.panelName && this.panelName !== config.panelName) {
                ScalerGUI.closePanel(this.panelName);
            }
            this.steps = config.steps || [];
            this.currentStep = 0;
            this.data = config.initialData || {};
            this.panelName = config.panelName;
            this.title = config.title;
            this.onComplete = config.onComplete;
            this.wizardHeader = config.wizardHeader || null;
            this.wizardFooter = config.wizardFooter || null;
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
            if (this.data._rerunMode) {
                const reviewIdx = this.steps.findIndex(s => s.id === 'review');
                if (reviewIdx >= 0) {
                    this.currentStep = reviewIdx;
                    this._highestStepReached = reviewIdx;
                }
                this.data._wasRerun = true;
                delete this.data._rerunMode;
            }
            this.render();
        },
        
        /**
         * Go to next step
         */
        next() {
            const currentStepConfig = this.steps[this.currentStep];
            const prevType = (this.currentStep === 0) ? this.data.interfaceType : undefined;
            const trackedKeys = this.stepKeys?.[this.currentStep] || [];
            const prevValues = {};
            trackedKeys.forEach(k => { if (this.data[k] !== undefined) prevValues[k] = JSON.stringify(this.data[k]); });
            if (currentStepConfig.collectData) {
                const _collected = currentStepConfig.collectData();
                if (_collected === null) return false;
                Object.assign(this.data, _collected);
            }
            if (currentStepConfig.validate && !currentStepConfig.validate(this.data)) {
                return false;
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
            if (isRevisit && this.stepDependencies?.[this.currentStep]) {
                let dataChanged = false;
                if (this.currentStep === 0 && prevType !== newType) {
                    dataChanged = true;
                } else {
                    for (const k of trackedKeys) {
                        const newVal = this.data[k] !== undefined ? JSON.stringify(this.data[k]) : undefined;
                        if (prevValues[k] !== newVal) { dataChanged = true; break; }
                    }
                }
                if (dataChanged) {
                    const invalidated = this.stepDependencies[this.currentStep];
                    invalidated.forEach(idx => {
                        (this.stepKeys[idx] || []).forEach(k => delete this.data[k]);
                    });
                }
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
                const step = this.steps[stepIndex];
                if (step.skipIf && step.skipIf(this.data)) return;
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

            if (this.wizardFooter && typeof this.wizardFooter === 'function') {
                const footerEl = this.wizardFooter(this.data);
                if (footerEl) content.appendChild(footerEl);
            }
            
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
                if (idx > this.currentStep && idx <= this._highestStepReached) stepEl.classList.add('visited');
                
                const isNavigable = idx <= this._highestStepReached && idx !== this.currentStep;
                const stepTitle = isNavigable
                    ? `Step ${idx + 1}: ${step.title} (click to jump)`
                    : `Step ${idx + 1}: ${step.title}`;
                stepEl.setAttribute('title', stepTitle);
                stepEl.innerHTML = `
                    <div class="step-number">${idx <= this._highestStepReached && idx !== this.currentStep ? '\u2713' : idx + 1}</div>
                    <div class="step-label">${step.title}</div>
                `;
                
                if (isNavigable) {
                    stepEl.style.cursor = 'pointer';
                    stepEl.onclick = () => this.goTo(idx);
                }
                
                indicator.appendChild(stepEl);
                
                if (idx < this.steps.length - 1) {
                    const connector = document.createElement('div');
                    connector.className = 'step-connector';
                    if (idx < this._highestStepReached) connector.classList.add('completed');
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
            const useCustomNav = stepConfig.customNav === true;
            
            const navExtraHtml = typeof stepConfig.navExtra === 'function' ? stepConfig.navExtra(this.data) : (stepConfig.navExtra || '');
            nav.innerHTML = `
                <button class="scaler-btn" id="wizard-back" ${isFirst ? 'disabled' : ''} title="Go to previous step">
                    ← Back
                </button>
                ${navExtraHtml}
                <div class="scaler-wizard-nav-right">
                    ${!useCustomNav ? (stepConfig.skipable ? '<button class="scaler-btn" id="wizard-skip" title="Skip this optional step">Skip</button>' : '') + `
                    <button class="scaler-btn scaler-btn-primary" id="wizard-next" title="${isLast ? 'Complete the wizard and generate config' : 'Continue to next step'}">
                        ${isLast ? (stepConfig.finalButtonText || 'Complete') : nextLabel + (isRevisit ? '' : ' →')}
                    </button>` : ''}
                </div>
            `;
            
            // Bind events scoped to nav (avoids document.getElementById finding stale panel's button)
            const backBtn = nav.querySelector('#wizard-back');
            const nextBtn = nav.querySelector('#wizard-next');
            const skipBtn = nav.querySelector('#wizard-skip');

            if (backBtn) backBtn.onclick = () => this.back();
            if (nextBtn) nextBtn.onclick = () => this.next();
            if (skipBtn) skipBtn.onclick = () => {
                this.currentStep++;
                this.render();
            };

            return nav;
        }
    },
    // =========================================================================
    // DEVICE CONTEXT CACHE (cached-then-live for wizard suggestions)
    // =========================================================================

    _deviceContexts: {},
    _contextCacheTTL: 300000,
    _wizardChangeLog: [],
    _wizardHistory: [],
    _WIZARD_HISTORY_KEY: 'scaler_wizard_history',
    _WIZARD_HISTORY_MAX: 100,

    // WizardBatch: accumulates configs from chained wizards for batch push
    _wizardBatch: {
        deviceId: null,
        configs: [],
        wizardChain: [],
        pendingInterfaces: [],
        pendingLoopback: null,
        pendingVRFs: [],
        pendingBGP: null
    },

    _wizardBatchInit(deviceId) {
        this._wizardBatch = {
            deviceId: deviceId || null,
            configs: [],
            wizardChain: [],
            pendingInterfaces: [],
            pendingLoopback: null,
            pendingVRFs: [],
            pendingBGP: null
        };
    },

    _wizardBatchAdd(wizardType, config, createdData = {}) {
        const b = this._wizardBatch;
        if (!b.deviceId) b.deviceId = createdData.deviceId || null;
        b.configs.push({ wizardType, config, createdData });
        b.wizardChain.push(wizardType);
        if (createdData.interfaces && createdData.interfaces.length) {
            b.pendingInterfaces = (b.pendingInterfaces || []).concat(createdData.interfaces);
        }
        if (createdData.loopback_ip) b.pendingLoopback = createdData.loopback_ip;
        if (createdData.loopback) b.pendingLoopback = createdData.loopback;
        if (createdData.vrfs && createdData.vrfs.length) {
            b.pendingVRFs = (b.pendingVRFs || []).concat(createdData.vrfs);
        }
        if (createdData.bgp) b.pendingBGP = createdData.bgp;
    },

    _wizardBatchClear() {
        this._wizardBatchInit(null);
    },

    _getNextWizardSuggestions(currentWizard, batchState) {
        const b = batchState || this._wizardBatch;
        const suggestions = [];
        const hasInterfaces = (b.pendingInterfaces || []).length > 0;
        const hasLoopback = !!b.pendingLoopback;
        const hasVRFs = (b.pendingVRFs || []).length > 0;
        const hasBGP = !!b.pendingBGP;

        if (currentWizard === 'interfaces') {
            if (hasInterfaces) {
                suggestions.push({ wizard: 'vrf', reason: 'Attach new sub-interfaces to VRFs', prefill: { attachInterfaces: true, interfaceList: b.pendingInterfaces } });
                suggestions.push({ wizard: 'service', reason: 'Create FXC/VPWS with these interfaces', prefill: { attachInterfaces: true, interfaceList: b.pendingInterfaces } });
            }
            if (hasLoopback || hasInterfaces) {
                const igpIfaces = hasLoopback ? ['lo0'].concat(b.pendingInterfaces || []) : (b.pendingInterfaces || []);
                suggestions.push({ wizard: 'igp', reason: 'Add loopback + interfaces to IGP', prefill: { interfaces: igpIfaces, router_ip: b.pendingLoopback } });
                suggestions.push({ wizard: 'bgp', reason: 'Configure BGP with loopback as update-source', prefill: { update_source: 'lo0', router_id: b.pendingLoopback } });
            }
        } else if (currentWizard === 'services' || currentWizard === 'bridge-domain') {
            if (hasInterfaces) suggestions.push({ wizard: 'multihoming', reason: 'Add multihoming ESI to L2 interfaces', prefill: { interfaces: b.pendingInterfaces } });
            suggestions.push({ wizard: 'flowspec', reason: 'Add FlowSpec local policy', prefill: {} });
        } else if (currentWizard === 'vrf') {
            if (hasVRFs) suggestions.push({ wizard: 'bgp', reason: 'Add BGP VRF instance for new VRFs', prefill: { vrfs: b.pendingVRFs } });
            suggestions.push({ wizard: 'flowspec-vpn', reason: 'Add FlowSpec VPN policy', prefill: { vrfs: b.pendingVRFs } });
        } else if (currentWizard === 'igp') {
            suggestions.push({ wizard: 'bgp', reason: 'Configure BGP peers', prefill: { update_source: 'lo0' } });
        } else if (currentWizard === 'bgp') {
            suggestions.push({ wizard: 'flowspec', reason: 'Enable BGP FlowSpec AFI on neighbors', prefill: {} });
        } else if (currentWizard === 'flowspec' || currentWizard === 'flowspec-vpn') {
            suggestions.push({ wizard: 'routing-policy', reason: 'Create routing policy for BGP attach', prefill: {} });
        }
        return suggestions;
    },

    _highlightDnosConfig(text) {
        if (!text || typeof text !== 'string') return '';
        const hier = ['system', 'interfaces', 'protocols', 'network-services', 'routing-policy', 'forwarding-options', 'access-lists', 'services'];
        const keys = ['admin-state', 'ipv4-address', 'route-distinguisher', 'route-target', 'address-family', 'neighbor', 'remote-as', 'apply-policy', 'match-class', 'action-type', 'name', 'instance', 'vrf'];
        let out = this.escapeHtml(text);
        hier.forEach(h => {
            out = out.replace(new RegExp(`^(\\s*)(${h})\\b`, 'gm'), '$1<span class="dns-hier">$2</span>');
        });
        keys.forEach(k => {
            out = out.replace(new RegExp(`^(\\s+)(${k.replace(/-/g, '\\-')})\\s+`, 'gm'), '$1<span class="dns-key">$2</span> ');
        });
        return out;
    },

    ipToIsisNet(ipStr, areaId) {
        if (!ipStr || typeof ipStr !== 'string') return '';
        const ip = ipStr.split('/')[0].trim();
        const octets = ip.split('.');
        if (octets.length !== 4) return (areaId || '49.0001') + '.0000.0000.0001.00';
        const padded = octets.map(o => String(parseInt(o, 10) || 0).padStart(4, '0'));
        return `${areaId || '49.0001'}.${padded[0]}.${padded[1]}.${padded[2]}.00`;
    },

    _WIZARD_SUGGESTION_TO_OPEN: {
        vrf: 'openVRFWizard',
        service: 'openServiceWizard',
        'bridge-domain': 'openBridgeDomainWizard',
        igp: 'openIGPWizard',
        bgp: 'openBGPWizard',
        flowspec: 'openFlowSpecWizard',
        'flowspec-vpn': 'openFlowSpecVPNWizard',
        'routing-policy': 'openRoutingPolicyWizard',
        multihoming: 'openMultihomingWizard'
    },

    async _renderWhatsNextSection(wizardType, data, createdData, generatedConfig) {
        const deviceId = data.deviceId;
        if (!deviceId) return null;
        if (!this._wizardBatch.deviceId || this._wizardBatch.deviceId !== deviceId) {
            this._wizardBatchInit(deviceId);
        }
        const b = this._wizardBatch;
        let suggestions = this._getNextWizardSuggestions(wizardType, b);
        try {
            const ctx = data.deviceContext || {};
            const api = await ScalerAPI.wizardSuggestions({
                device_id: deviceId,
                completed_wizard: wizardType,
                created_data: createdData || {},
                ssh_host: ctx.mgmt_ip || ctx.ip || ''
            });
            if (api?.suggestions?.length) {
                const seen = new Set(suggestions.map(s => s.wizard));
                api.suggestions.forEach(s => {
                    if (s.wizard && !seen.has(s.wizard)) {
                        seen.add(s.wizard);
                        suggestions.push({ wizard: s.wizard, reason: s.reason || '', prefill: s.prefill || {} });
                    }
                });
            }
        } catch (_) {}
        const batchCount = b.configs.length;
        const hasBatch = batchCount > 0;

        const div = document.createElement('div');
        div.className = 'scaler-whats-next';
        div.id = 'whats-next-section';
        let html = '<h4>What\'s Next?</h4><div class="scaler-whats-next-actions">';
        html += '<button type="button" class="scaler-btn scaler-btn-primary scaler-whats-next-push" data-action="push">Push This Config</button>';
        if (suggestions.length > 0) {
            suggestions.slice(0, 3).forEach((s, i) => {
                const label = s.wizard === 'vrf' ? 'VRF' : s.wizard === 'service' ? 'Service' : s.wizard === 'igp' ? 'IGP' : s.wizard === 'bgp' ? 'BGP' : s.wizard === 'flowspec' ? 'FlowSpec' : s.wizard === 'flowspec-vpn' ? 'FlowSpec VPN' : s.wizard === 'routing-policy' ? 'Policy' : s.wizard === 'bridge-domain' ? 'Bridge Domain' : s.wizard;
                html += `<button type="button" class="scaler-btn scaler-btn-secondary scaler-whats-next-continue" data-action="continue" data-wizard="${s.wizard}" data-reason="${this.escapeHtml(s.reason || '')}">Continue to ${label}</button>`;
            });
            html += '<button type="button" class="scaler-btn scaler-btn-secondary scaler-whats-next-batch" data-action="add-batch">Add to Batch and Continue</button>';
        }
        if (hasBatch) {
            html += `<button type="button" class="scaler-btn scaler-btn-primary scaler-whats-next-push-all" data-action="push-all">Push All (${batchCount + 1} configs)</button>`;
        }
        html += '</div>';
        div.innerHTML = html;

        div.querySelector('.scaler-whats-next-push')?.addEventListener('click', () => {
            ScalerGUI.WizardController.next();
        });
        div.querySelectorAll('.scaler-whats-next-continue').forEach(btn => {
            btn.addEventListener('click', () => {
                const targetWizard = btn.getAttribute('data-wizard');
                const prefill = suggestions.find(s => s.wizard === targetWizard)?.prefill || {};
                prefill.deviceId = deviceId;
                this._wizardBatchAdd(wizardType, generatedConfig || '', { ...createdData, deviceId });
                const openFn = this._WIZARD_SUGGESTION_TO_OPEN[targetWizard];
                const panelName = this.WizardController?.panelName;
                if (panelName) this.closePanel(panelName);
                if (openFn && typeof this[openFn] === 'function') {
                    this[openFn](deviceId, prefill);
                }
            });
        });
        div.querySelector('.scaler-whats-next-batch')?.addEventListener('click', () => {
            const first = suggestions[0];
            if (!first) return;
            const prefill = { ...(first.prefill || {}), deviceId };
            this._wizardBatchAdd(wizardType, generatedConfig || '', { ...createdData, deviceId });
            const openFn = this._WIZARD_SUGGESTION_TO_OPEN[first.wizard];
            const panelName = this.WizardController?.panelName;
            if (panelName) this.closePanel(panelName);
            if (openFn && typeof this[openFn] === 'function') {
                this[openFn](deviceId, prefill);
            }
        });
        div.querySelector('.scaler-whats-next-push-all')?.addEventListener('click', async () => {
            const allConfigs = [...b.configs, { config: generatedConfig || '' }];
            const combined = allConfigs.map(c => c.config).filter(Boolean).join('\n\n');
            const ctx = data.deviceContext || {};
            try {
                const result = await ScalerAPI.pushConfig({
                    device_id: deviceId,
                    config: combined,
                    hierarchy: 'batch',
                    mode: 'merge',
                    dry_run: true,
                    ssh_host: ctx.mgmt_ip || ctx.ip || '',
                    job_name: `Batch (${allConfigs.length} configs) on ${deviceId}`
                });
                this._wizardBatchClear();
                const panelName = this.WizardController?.panelName;
                if (panelName) this.closePanel(panelName);
                this.showProgress(result.job_id, `Pushing ${allConfigs.length} configs to ${deviceId}`, {});
            } catch (e) {
                this.showNotification(`Batch push failed: ${e.message}`, 'error');
            }
        });
        return div;
    },

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
        'flowspec-vpn-wizard': 'flowspec-vpn',
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
            case 'interfaces': {
                const parentCount = p.count ?? (p.subifParents?.length ?? 1);
                const subifCount = p.subifCount ?? 1;
                const total = parentCount * subifCount;
                if ((p.interfaceType || '') === 'subif' && total > 0) {
                    return `${total} sub-ifs from ${parentCount} parent${parentCount !== 1 ? 's' : ''}`;
                }
                return `${parentCount} ${p.interfaceType || 'subif'}${subifCount > 1 ? ' + ' + total + ' sub-ifs' : ''}`;
            }
            case 'services':
                return `${p.count ?? 1} ${p.serviceType || 'fxc'}, EVI ${p.eviStart ?? 1000}`;
            case 'vrf':
                return `${p.count ?? 1} VRF(s)`;
            case 'bridge-domain':
                return `${p.count ?? 1} BD(s)`;
            case 'flowspec':
                return `Policy ${p.policyName || '?'}`;
            case 'flowspec-vpn':
                return `FlowSpec VPN ${p.vrf || '?'} - ${p.policyName || '?'}`;
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
        const id = (deviceId || '').toLowerCase();
        const allRuns = this._wizardHistory
            .filter(r => (r.wizardType || '') === wizardType && (r.deviceId || '').toLowerCase() === id)
            .sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
        const lastRun = allRuns.find(r => r.success !== 'saved') || null;
        const savedRuns = allRuns.filter(r => r.success === 'saved');
        if (!lastRun && savedRuns.length === 0) return null;

        const container = document.createElement('div');

        if (savedRuns.length > 0) {
            const savedDiv = document.createElement('div');
            savedDiv.className = 'scaler-last-run-card scaler-saved-run-card';
            let savedHtml = `<div class="scaler-last-run-header"><span class="scaler-last-run-label scaler-saved-label">Saved for Later</span><span class="scaler-last-run-count">${savedRuns.length}</span></div>`;
            savedRuns.forEach((sr, idx) => {
                const summary = this._formatLastRunSummary(sr);
                const ts = sr.timestamp ? new Date(sr.timestamp).toLocaleString() : '';
                savedHtml += `
                    <div class="scaler-saved-entry" data-idx="${idx}">
                        <div class="scaler-saved-entry-row">
                            <span class="scaler-saved-summary">${this.escapeHtml(summary)}</span>
                            <span class="scaler-saved-ts">${ts}</span>
                        </div>
                        <div class="scaler-last-run-actions">
                            <button type="button" class="scaler-btn scaler-btn-sm scaler-btn-primary scaler-saved-push" data-saved-idx="${idx}">Push</button>
                            <button type="button" class="scaler-btn scaler-btn-sm scaler-btn-secondary scaler-saved-edit" data-saved-idx="${idx}">Edit</button>
                        </div>
                    </div>`;
            });
            savedDiv.innerHTML = savedHtml;
            savedDiv.querySelectorAll('.scaler-saved-push').forEach(btn => {
                const sr = savedRuns[parseInt(btn.dataset.savedIdx)];
                if (sr) btn.addEventListener('click', () => onRerun?.({ ...sr, _rerunMode: true }));
            });
            savedDiv.querySelectorAll('.scaler-saved-edit').forEach(btn => {
                const sr = savedRuns[parseInt(btn.dataset.savedIdx)];
                if (sr) btn.addEventListener('click', () => {
                    const { deviceContext, generatedConfig, ...params } = sr.params || {};
                    onRerun?.({ ...sr, params, _editMode: true });
                });
            });
            container.appendChild(savedDiv);
        }

        if (lastRun) {
            const summary = this._formatLastRunSummary(lastRun);
            const ts = lastRun.timestamp ? new Date(lastRun.timestamp).toLocaleString() : '';
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
            div.querySelector('[data-action="rerun"]')?.addEventListener('click', () => onRerun?.(lastRun));
            div.querySelector('[data-action="rerun-other"]')?.addEventListener('click', () => onRerunOther?.(lastRun));
            container.appendChild(div);
        }
        return container;
    },

    updateWizardRunResult(jobId, success) {
        const rec = this._wizardHistory.find(r => r.jobId === jobId);
        if (rec) {
            rec.success = success;
            this._saveWizardHistory();
        }
    },

    _handleLastRunAction(rec, deviceId, ctx) {
        const wc = this.WizardController;
        if (!rec?.params || !wc) return;
        const params = rec._editMode ? rec.params : (rec.params || {});
        Object.assign(wc.data, params);
        wc.data.deviceId = deviceId;
        wc.data.deviceContext = ctx;
        if (rec.generatedConfig) wc.data.generatedConfig = rec.generatedConfig;
        if (wc.stepBuilder) {
            const built = wc.stepBuilder(wc.data);
            wc.steps = built.steps;
            wc.stepDependencies = built.deps || {};
            wc.stepKeys = built.keys || {};
        }
        if (rec._editMode) {
            wc.currentStep = 0;
            wc._highestStepReached = wc.steps.length - 1;
        } else {
            const reviewIdx = wc.steps.findIndex(s => s.id === 'review');
            wc.currentStep = reviewIdx >= 0 ? reviewIdx : 0;
            wc._highestStepReached = wc.currentStep;
        }
        wc.render();
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
        { key: 'flowspec-vpn-wizard', label: 'FlowSpec VPN', action: 'flowspec-vpn-wizard' },
        { key: 'routing-policy-wizard', label: 'Policy', action: 'routing-policy-wizard' },
        { key: 'system-wizard', label: 'System', action: 'system-wizard' },
    ],

    _WIZARD_OPEN_MAP: {
        'interface-wizard':       'openInterfaceWizard',
        'service-wizard':         'openServiceWizard',
        'vrf-wizard':             'openVRFWizard',
        'bridge-domain-wizard':   'openBridgeDomainWizard',
        'bgp-wizard':             'openBGPWizard',
        'igp-wizard':             'openIGPWizard',
        'flowspec-wizard':        'openFlowSpecWizard',
        'flowspec-vpn-wizard':    'openFlowSpecVPNWizard',
        'routing-policy-wizard':  'openRoutingPolicyWizard',
        'system-wizard':          'openSystemWizard',
    },

    _buildWizardQuickNav(activeKey, deviceId) {
        return (data) => {
            const nav = document.createElement('div');
            nav.className = 'scaler-wizard-quicknav';
            const devId = deviceId || data.deviceId || '';
            const wizardType = this._WIZARD_NAV_KEY_MAP?.[activeKey];
            const b = this._wizardBatch;
            const inBatch = (b?.wizardChain || []);
            const suggestions = wizardType ? this._getNextWizardSuggestions(wizardType, b) : [];
            const suggestedKeys = suggestions.map(s => {
                const openFn = this._WIZARD_SUGGESTION_TO_OPEN?.[s.wizard];
                return Object.entries(this._WIZARD_OPEN_MAP || {}).find(([, fn]) => fn === openFn)?.[0];
            }).filter(Boolean);
            this._WIZARD_NAV_ITEMS.forEach(item => {
                const btn = document.createElement('button');
                btn.className = 'scaler-quicknav-tab' + (item.key === activeKey ? ' active' : '');
                const wizType = this._WIZARD_NAV_KEY_MAP?.[item.key];
                const completed = wizType && inBatch.includes(wizType);
                const suggested = suggestedKeys.includes(item.key);
                let labelHtml = item.label;
                if (completed) labelHtml += ' <span class="scaler-quicknav-check" title="In batch">✓</span>';
                if (suggested) labelHtml += ' <span class="scaler-quicknav-badge" title="Suggested next">•</span>';
                btn.innerHTML = labelHtml;
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
     * Build a Decision step (Save for Later / Push Config / Next Section) before the push step.
     * @param {Object} opts - { wizardType, getCreatedData }
     * @returns {Object} Step config for WizardController
     */
    _buildDecisionStep(opts = {}) {
        const wizardType = opts.wizardType || 'interfaces';
        const getCreatedData = opts.getCreatedData || (() => ({}));
        return {
            id: 'decision',
            title: 'Decision',
            customNav: true,
            render: (data) => {
                const lineCount = (data.generatedConfig || '').split('\n').length;
                return `
                <div class="scaler-form">
                    <div class="scaler-form-group">
                        <label>What would you like to do?</label>
                        <div class="scaler-decision-options">
                            <button type="button" class="scaler-decision-option scaler-decision-save" data-action="save">
                                <span class="scaler-decision-title">Save for Later</span>
                                <span class="scaler-decision-desc">Save to wizard history. Push or edit later from the History panel.</span>
                            </button>
                            <button type="button" class="scaler-decision-option scaler-decision-push scaler-decision-primary" data-action="push">
                                <span class="scaler-decision-title">Push Config</span>
                                <span class="scaler-decision-desc">Proceed to delivery method (Commit Check, Terminal Paste, File Upload).</span>
                            </button>
                            <button type="button" class="scaler-decision-option scaler-decision-next" data-action="next">
                                <span class="scaler-decision-title">Next Section</span>
                                <span class="scaler-decision-desc">Add to batch and open next wizard (e.g. Interfaces -> BGP, BGP -> IGP).</span>
                            </button>
                        </div>
                        <div class="scaler-info-box" style="margin-top:12px;font-size:12px">
                            Config: ${lineCount} lines ready.
                        </div>
                    </div>
                </div>`;
            },
            afterRender: (data) => {
                const wc = ScalerGUI.WizardController;
                const deviceId = data.deviceId;
                const config = data.generatedConfig || '';
                const createdData = getCreatedData(data);

                document.querySelectorAll('.scaler-decision-option').forEach(btn => {
                    btn.onclick = async () => {
                        const action = btn.getAttribute('data-action');
                        if (action === 'save') {
                            const wizType = ScalerGUI._wizardKeyToType[wc.panelName] || wizardType;
                            const record = {
                                id: typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `wz-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
                                deviceId,
                                wizardType: wizType,
                                params: { ...createdData },
                                generatedConfig: config,
                                configLineCount: config.split('\n').length,
                                pushMode: 'saved',
                                success: 'saved',
                                jobId: null,
                                timestamp: Date.now(),
                                deviceLabel: deviceId,
                            };
                            ScalerGUI._wizardHistory.push(record);
                            ScalerGUI._saveWizardHistory();
                            ScalerGUI.showNotification('Config saved to wizard history. Open History to push or edit later.', 'success');
                            ScalerGUI.closePanel(wc.panelName);
                            return;
                        }
                        if (action === 'push') {
                            wc.next();
                            return;
                        }
                        if (action === 'next') {
                            const b = ScalerGUI._wizardBatch;
                            if (!b.deviceId || b.deviceId !== deviceId) {
                                ScalerGUI._wizardBatchInit(deviceId);
                            }
                            ScalerGUI._wizardBatchAdd(wizardType, config, { ...createdData, deviceId });
                            const suggestions = ScalerGUI._getNextWizardSuggestions(wizardType, b);
                            const first = suggestions[0];
                            if (!first) {
                                ScalerGUI.showNotification('No suggested next wizard. Push this config.', 'info');
                                return;
                            }
                            const prefill = { ...(first.prefill || {}), deviceId };
                            const openFn = ScalerGUI._WIZARD_SUGGESTION_TO_OPEN[first.wizard];
                            ScalerGUI.closePanel(wc.panelName);
                            if (openFn && typeof ScalerGUI[openFn] === 'function') {
                                ScalerGUI[openFn](deviceId, prefill);
                            }
                        }
                    };
                });
            }
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
        const _fmtEst = (sec) => {
            if (sec == null || sec < 0) return '';
            if (sec < 60) return `~${Math.round(sec)}s`;
            const m = Math.floor(sec / 60);
            const s = Math.round(sec % 60);
            return s ? `~${m}m ${s}s` : `~${m}m`;
        };
        return {
            id,
            title: 'Push',
            finalButtonText: 'Commit Check',
            render: (data) => {
                const ctx = data.deviceContext || {};
                const host = ctx.mgmt_ip || ctx.ip || '';
                const resolved = ctx.resolved_via || '';
                const est = data._pushEstimate || {};
                const estData = est.estimates || {};
                const termEst = estData.terminal_paste?.total;
                const fileEst = estData.file_upload?.total;
                return `
                <div class="scaler-form">
                    <div class="scaler-form-group">
                        <label>Delivery Method</label>
                        <div class="scaler-radio-group">
                            <label class="scaler-radio">
                                <input type="radio" name="${radioName}" value="dry_run" checked>
                                <span><strong>Commit Check First</strong></span>
                                <span class="scaler-estimate-badge">${_fmtEst(termEst)}</span>
                            </label>
                            <div class="scaler-radio-desc">Paste config via SSH terminal, run <code>commit check</code>.
                            Nothing is applied. If check passes, you can commit from the result dialog.</div>
                            <label class="scaler-radio">
                                <input type="radio" name="${radioName}" value="terminal_merge">
                                <span><strong>Terminal Paste + Commit</strong></span>
                                <span class="scaler-estimate-badge">${_fmtEst(termEst)}</span>
                            </label>
                            <div class="scaler-radio-desc">Paste config via SSH terminal + <code>commit</code>.
                            Use when you've already validated with a commit check.</div>
                            <label class="scaler-radio">
                                <input type="radio" name="${radioName}" value="file_merge">
                                <span><strong>File Upload + Load Merge</strong></span>
                                <span class="scaler-estimate-badge">${_fmtEst(fileEst)}</span>
                            </label>
                            <div class="scaler-radio-desc">SCP upload + <code>load merge</code> + commit. Best for large configs.</div>
                            <label class="scaler-radio">
                                <input type="radio" name="${radioName}" value="file_override">
                                <span><strong>File Upload + Load Override</strong></span>
                                <span class="scaler-estimate-badge">${_fmtEst(fileEst)}</span>
                            </label>
                            <div class="scaler-radio-desc">SCP upload + <code>load override</code> + commit. Replaces entire candidate config.</div>
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
            afterRender: async (data) => {
                const config = data.generatedConfig || data.config || '';
                const ctx = data.deviceContext || {};
                if (config && data.deviceId) {
                    try {
                        const est = await ScalerAPI.getPushEstimate({
                            config,
                            device_id: data.deviceId,
                            ssh_host: ctx.mgmt_ip || ctx.ip || '',
                        });
                        data._pushEstimate = est;
                        const estData = est.estimates || {};
                        const termEst = estData.terminal_paste?.total;
                        const fileEst = estData.file_upload?.total;
                        document.querySelectorAll('.scaler-estimate-badge').forEach((el, i) => {
                            const radios = document.querySelectorAll(`input[name="${radioName}"]`);
                            const r = radios[i];
                            if (r?.value === 'dry_run' || r?.value === 'terminal_merge') el.textContent = _fmtEst(termEst);
                            else if (r?.value === 'file_merge' || r?.value === 'file_override') el.textContent = _fmtEst(fileEst);
                        });
                    } catch (_) {}
                }
                document.querySelectorAll(`input[name="${radioName}"]`).forEach(r => {
                    r.addEventListener('change', () => {
                        const panel = r.closest('.scaler-panel');
                        const btn = panel?.querySelector('#wizard-next');
                        const mode = document.querySelector(`input[name="${radioName}"]:checked`)?.value;
                        if (btn) {
                            if (mode === 'clipboard') btn.textContent = 'Copy & Open SSH';
                            else if (mode === 'terminal_merge') btn.textContent = 'Commit';
                            else if (mode === 'file_merge' || mode === 'file_override') btn.textContent = 'Push';
                            else btn.textContent = 'Commit Check';
                        }
                    });
                });
            },
            collectData: () => {
                const mode = document.querySelector(`input[name="${radioName}"]:checked`)?.value || 'dry_run';
                const dryRun = mode === 'dry_run';
                let pushMethod = 'terminal_paste';
                let loadMode = 'merge';
                if (mode === 'file_merge') { pushMethod = 'file_upload'; loadMode = 'merge'; }
                else if (mode === 'file_override') { pushMethod = 'file_upload'; loadMode = 'override'; }
                else if (mode === 'terminal_merge') { pushMethod = 'terminal_paste'; loadMode = 'merge'; }
                return {
                    dryRun,
                    pushMode: mode,
                    push_method: pushMethod,
                    load_mode: loadMode,
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
        const { onRefresh, collapsed = false, wizardType = '' } = options;
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
        const fetchedAt = ctx?._fetchedAt || 0;
        const staleThreshold = 300000;
        const isStale = fetchedAt && (Date.now() - fetchedAt) > staleThreshold;
        const stack = ctx?.stack || {};
        const stackLine = (stack.dnos_version || ctx?.dnos_version) ? `DNOS ${stack.dnos_version || ctx.dnos_version} | GI ${stack.gi_version || ctx.gi_version || '-'} | BaseOS ${stack.baseos_version || '-'}` : '';

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
                ${isStale ? '<span class="device-context-stale" title="Data older than 5 min">[STALE]</span>' : ''}
                <span class="device-context-status ${statusClass}"></span>
            </div>
            <div class="device-context-body">
                ${statusLine}
                ${stackLine ? `<div class="device-context-row device-context-stack">${stackLine}</div>` : ''}
                <div class="device-context-row device-context-compact">${sysLine}</div>
                ${ifaceBar}
                ${lldpChips ? `<div class="device-context-row"><span class="ctx-lldp-label">LLDP:</span><span class="ctx-lldp-chips">${lldpChips}${lldpCount > 6 ? ` <span class="ctx-lldp-more">+${lldpCount - 6}</span>` : ''}</span></div>` : (isDnaas ? '<div class="device-context-row" style="opacity:0.5">DNAAS device -- LLDP skipped</div>' : '')}
                ${freeCount ? `<div class="device-context-row" style="font-size:11px;opacity:0.7">${freeCount} free physical</div>` : ''}
                ${ctx?.policy_suggestions?.length && ['bgp', 'policy', 'flowspec', 'flowspec-vpn', 'igp', ''].includes(wizardType) ? `<div class="device-context-row"><span class="ctx-lldp-label">Policies:</span><span class="ctx-lldp-chips">${ctx.policy_suggestions.slice(0, 5).map(p => `<button type="button" class="suggestion-chip suggestion-chip--policy ctx-smart-chip" data-type="policy" data-value="${String(p).replace(/"/g, '&quot;')}" title="Use policy">${p}</button>`).join('')}${ctx.policy_suggestions.length > 5 ? ` <span class="ctx-lldp-more">+${ctx.policy_suggestions.length - 5}</span>` : ''}</span></div>` : ''}
                ${ctx?.lo0_isis_net && ['igp', ''].includes(wizardType) ? `<div class="device-context-row"><span class="ctx-lldp-label">ISIS NET:</span><button type="button" class="suggestion-chip suggestion-chip--net ctx-smart-chip" data-type="net" data-value="${ctx.lo0_isis_net}" title="Auto-generated from lo0">${ctx.lo0_isis_net}</button></div>` : ''}
                ${ctx?.detected_l2ac_parent && ['interfaces', 'services', 'bd', 'bridge-domain', ''].includes(wizardType) ? `<div class="device-context-row"><span class="ctx-lldp-label">L2-AC parent:</span><button type="button" class="suggestion-chip suggestion-chip--l2parent ctx-smart-chip" data-type="l2parent" data-value="${ctx.detected_l2ac_parent}" title="Detected from config">${ctx.detected_l2ac_parent}</button></div>` : ''}
                ${ctx?.scale_suggestions?.length && ['scale', 'multihoming', ''].includes(wizardType) ? `<div class="device-context-row"><span class="ctx-lldp-label">Scale:</span><span class="ctx-lldp-chips">${ctx.scale_suggestions.slice(0, 3).map(s => { const d = (s.description || s.type || 'suggestion').replace(/\[.*?\]/g, '').trim(); return `<button type="button" class="suggestion-chip suggestion-chip--scale ctx-smart-chip" data-type="scale" title="${d.replace(/"/g, '&quot;')}">${d.slice(0, 25)}</button>`; }).join('')}</span></div>` : ''}
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
        this._checkRunningUpgrades();
        console.log('[ScalerGUI] Ready');
    },
    /**
     * Valid DNOS system-type labels for deploy (GI/upgrade wizard).
     * Rejects DNAAS/inventory noise (e.g. "SA-40C8CD, Family: NCR").
     */
    _WIZARD_KNOWN_SYS_TYPES: [
        'CL-16', 'CL-32', 'CL-48', 'CL-49', 'CL-51', 'CL-64', 'CL-76', 'CL-86', 'CL-96', 'CL-134', 'CL-153', 'CL-192', 'CL-409', 'CL-768',
        'SA-10CD', 'SA-32CD', 'SA-32E-S', 'SA-36CD-S', 'SA-36CD-S-SA', 'SA-38E', 'SA-40C', 'SA-40C6CD-S', 'SA-40C8CD',
        'SA-64X8C-S', 'SA-64X12C-S', 'SA-64XXV8C', 'SA-96X6C', 'SA-96X6C-S',
        'SA-VR', 'SA-VR-10CD', 'SA-VR-32CD', 'SA-VR-32E-S', 'SA-VR-36CD-S', 'SA-VR-36CD-S-SA', 'SA-VR-40C', 'SA-VR-40C6CD-S', 'SA-VR-64X12C-S', 'SA-VR-96X6C-S',
    ],

    _sanitizeWizardSystemType(raw) {
        if (raw == null || raw === '') return '';
        const s = String(raw).trim();
        if (!s) return '';
        if (/family\s*:/i.test(s) || /,\s*/.test(s)) return '';
        const known = this._WIZARD_KNOWN_SYS_TYPES;
        const up = s.toUpperCase();
        for (const k of known) {
            if (up === k.toUpperCase()) return k;
        }
        const m = /^([A-Z]{2}-[A-Z0-9-]+)/i.exec(s);
        if (m) {
            const cand = m[1].toUpperCase();
            const hit = known.find(k => k.toUpperCase() === cand);
            if (hit) return hit;
        }
        return '';
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
        container.addEventListener('keydown', (e) => { e.stopPropagation(); });
        container.addEventListener('keyup', (e) => { e.stopPropagation(); });
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
        
        const requestedWidth = parseInt(options.width) || 450;
        panel.style.width = requestedWidth + 'px';
        panel.style.maxWidth = 'calc(100vw - 20px)';
        panel.dataset.parentPanel = options.parentPanel || '';
        
        const hasParent = options.parentPanel || this.state.panelHistory.find(h => h.current === name);
        this.state.lastPanel = name;
        this.updateButtonStates();
        
        const header = document.createElement('div');
        header.className = 'scaler-panel-header';
        header.innerHTML = `
            <h3>${title}</h3>
            <div class="scaler-panel-actions">
                ${options.minimizable ? '<button class="scaler-btn-icon" data-action="minimize" title="Minimize"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="12" x2="19" y2="12"/></svg></button>' : ''}
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
        
        requestAnimationFrame(() => {
            panel.classList.add('scaler-panel-open');
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
            if (Object.keys(this.state.activePanels).length === 0) {
                const canvas = document.getElementById('topology-canvas');
                if (canvas) canvas.focus();
            }
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
            'flowspec-vpn-wizard': () => this.openFlowSpecVPNWizard(),
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
        const isMinimized = panel.classList.toggle('scaler-panel-minimized');
        const btn = panel.querySelector('[data-action="minimize"]');
        if (btn) {
            btn.innerHTML = isMinimized
                ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="5" y="5" width="14" height="14" rx="2"/></svg>'
                : '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="12" x2="19" y2="12"/></svg>';
            btn.title = isMinimized ? 'Restore' : 'Minimize';
        }
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
            <div id="scaler-menu-summary" class="scaler-menu-summary-bar" style="display: flex; align-items: center; gap: 12px; padding: 6px 10px; margin-bottom: 10px; background: rgba(0,0,0,0.25); border-radius: 6px; font-size: 11px; color: rgba(255,255,255,0.7);">
                <span id="scaler-summary-text">Loading...</span>
            </div>
            <div class="scaler-menu-section scaler-ssh-pool-row" style="padding: 8px 12px; background: rgba(0,0,0,0.2); border-radius: 8px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span id="ssh-pool-label" style="color: rgba(255,255,255,0.8); font-size: 12px; font-weight: 500;">Persistent SSH</span>
                        <span id="ssh-pool-status" style="font-size: 11px; color: rgba(255,255,255,0.5);">OFF -- connect per action</span>
                    </div>
                    <div id="ssh-pool-toggle" class="scaler-ssh-pool-toggle" style="position: relative; width: 44px; height: 24px; background: rgba(255,255,255,0.15); border-radius: 12px; cursor: pointer; transition: background 0.2s;">
                        <div id="ssh-pool-knob" style="position: absolute; width: 20px; height: 20px; left: 2px; top: 2px; background: rgba(255,255,255,0.8); border-radius: 50%; transition: left 0.2s;"></div>
                    </div>
                </div>
                <div style="font-size: 10px; color: rgba(255,255,255,0.35); margin-top: 4px; line-height: 1.4;">Keep SSH sessions open in background for faster wizard/push/status operations. Uses ~2MB per device.</div>
            </div>
            <div class="scaler-menu-section scaler-menu-section-collapsible" data-section="device-management">
                <div class="scaler-menu-section-header">
                    <span class="scaler-menu-section-toggle">-</span>
                    <h4>Device Management</h4>
                </div>
                <div class="scaler-menu-section-body">
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
            </div>
            
            <div class="scaler-menu-section scaler-menu-section-collapsible" data-section="configuration-wizards">
                <div class="scaler-menu-section-header">
                    <span class="scaler-menu-section-toggle">-</span>
                    <h4>Configuration Wizards</h4>
                </div>
                <div class="scaler-menu-section-body">
                <button class="scaler-menu-btn" data-action="interface-wizard">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M4 4h6v6H4z"/><path d="M14 4h6v6h-6z"/>
                        <path d="M4 14h6v6H4z"/><path d="M14 14h6v6h-6z"/>
                    </svg>
                    Interface Wizard
                    <span class="scaler-menu-hint">Create scaled interfaces</span>
                    <span class="scaler-menu-badge" data-badge="interface" style="display:none"></span>
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
                <button class="scaler-menu-btn" data-action="flowspec-vpn-wizard">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/>
                    </svg>
                    FlowSpec VPN
                    <span class="scaler-menu-hint">VRF-scoped FlowSpec policies</span>
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
            </div>
            
            <div class="scaler-menu-section scaler-menu-section-collapsible" data-section="history">
                <div class="scaler-menu-section-header">
                    <span class="scaler-menu-section-toggle">-</span>
                    <h4>History</h4>
                </div>
                <div class="scaler-menu-section-body">
                <button class="scaler-menu-btn" data-action="wizard-history">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
                    </svg>
                    Wizard Run History
                    <span class="scaler-menu-hint">Recent wizard runs, re-run</span>
                </button>
                </div>
            </div>
            
            <div class="scaler-menu-section scaler-menu-section-collapsible" data-section="operations">
                <div class="scaler-menu-section-header">
                    <span class="scaler-menu-section-toggle">-</span>
                    <h4>Operations</h4>
                </div>
                <div class="scaler-menu-section-body">
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
                    <span class="scaler-menu-badge" data-badge="scale" style="display:none"></span>
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
            </div>
            
            <div class="scaler-menu-section scaler-menu-section-collapsible" data-section="system">
                <div class="scaler-menu-section-header">
                    <span class="scaler-menu-section-toggle">-</span>
                    <h4>System</h4>
                </div>
                <div class="scaler-menu-section-body">
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
            </div>
            `;
            
            content.querySelectorAll('[data-action]').forEach(btn => {
                btn.onclick = () => {
                    const action = btn.dataset.action;
                    this.closePanel('scaler-menu');
                    this.handleMenuAction(action);
                };
            });

            content.querySelectorAll('.scaler-menu-section-collapsible').forEach(section => {
                const key = section.dataset.section;
                const header = section.querySelector('.scaler-menu-section-header');
                const body = section.querySelector('.scaler-menu-section-body');
                const toggle = section.querySelector('.scaler-menu-section-toggle');
                const collapsed = localStorage.getItem('scaler_menu_collapsed_' + key) === 'true';
                if (collapsed && body) {
                    section.classList.add('collapsed');
                    if (toggle) toggle.textContent = '+';
                }
                if (header && body && toggle) {
                    header.onclick = () => {
                        const isCollapsed = section.classList.toggle('collapsed');
                        toggle.textContent = isCollapsed ? '+' : '-';
                        localStorage.setItem('scaler_menu_collapsed_' + key, String(isCollapsed));
                    };
                }
            });

            const sshPoolToggle = content.querySelector('#ssh-pool-toggle');
            const sshPoolKnob = content.querySelector('#ssh-pool-knob');
            const sshPoolStatus = content.querySelector('#ssh-pool-status');
            const savedEnabled = localStorage.getItem('ssh_pool_enabled') === 'true';
            if (sshPoolToggle && sshPoolKnob && sshPoolStatus) {
                const withSshCount = this._getCanvasDeviceObjects().filter(d => !!d.sshHost).length;
                const updatePoolUI = (enabled, statusText) => {
                    sshPoolKnob.style.left = enabled ? '22px' : '2px';
                    sshPoolToggle.style.background = enabled ? 'rgba(0, 180, 216, 0.4)' : 'rgba(255,255,255,0.15)';
                    sshPoolStatus.textContent = statusText || (enabled ? `ON -- ${withSshCount} device(s) eligible` : 'OFF -- connect per action');
                };
                updatePoolUI(savedEnabled);
                let _poolTogglePending = false;
                (async () => {
                    try {
                        await ScalerAPI.toggleSSHPool(savedEnabled);
                        const st = await ScalerAPI.getSSHPoolStatus();
                        if (st.enabled) {
                            updatePoolUI(true, st.count > 0 ? `ON -- ${st.count} active` : `ON -- ${withSshCount} device(s) eligible`);
                        }
                    } catch (e) { /* bridge may be down */ }
                })();
                sshPoolToggle.onclick = async () => {
                    if (_poolTogglePending) return;
                    _poolTogglePending = true;
                    const currentlyOn = sshPoolKnob.style.left === '22px';
                    const newState = !currentlyOn;
                    updatePoolUI(newState, newState ? 'Enabling...' : 'Disabling...');
                    try {
                        await ScalerAPI.toggleSSHPool(newState);
                        localStorage.setItem('ssh_pool_enabled', String(newState));
                        if (newState) {
                            const st = await ScalerAPI.getSSHPoolStatus();
                            updatePoolUI(true, st.count > 0 ? `ON -- ${st.count} active` : `ON -- ${withSshCount} device(s) eligible`);
                        } else {
                            updatePoolUI(false);
                        }
                        this.showNotification(newState ? 'Persistent SSH enabled -- connections reused across operations' : 'Persistent SSH disabled -- fresh connection per action', 'info');
                    } catch (e) {
                        updatePoolUI(!newState);
                        this.showNotification(e?.message || 'SSH pool toggle failed', 'error');
                    } finally {
                        _poolTogglePending = false;
                    }
                };
            }

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

            (async () => {
                const summaryEl = content.querySelector('#scaler-summary-text');
                if (!summaryEl) return;
                try {
                    const canvasDevs = this._getCanvasDeviceObjects();
                    const total = canvasDevs.length;
                    const withSsh = canvasDevs.filter(d => !!d.sshHost).length;
                    const noSsh = total - withSsh;
                    const green = 'rgba(76, 175, 80, 0.9)';
                    const gray = 'rgba(255,255,255,0.4)';
                    summaryEl.innerHTML = total === 0
                        ? '<span style="color:' + gray + '">No devices on canvas</span>'
                        : '<span style="color:' + (withSsh ? green : gray) + '">' + total + ' device' + (total !== 1 ? 's' : '') + '</span>' +
                          (withSsh > 0 ? ' | <span style="color:' + green + '">' + withSsh + ' with SSH</span>' : '') +
                          (noSsh > 0 ? ' | <span style="color:' + gray + '">' + noSsh + ' no SSH</span>' : '');
                } catch (e) {
                    summaryEl.textContent = 'Devices: --';
                }
            })();

            (async () => {
                try {
                    const canvasDevs = this._getCanvasDeviceObjects();
                    const ids = canvasDevs.filter(d => !!d.sshHost).map(d => d.label).filter(Boolean);
                    if (ids.length === 0) return;
                    const summary = await ScalerAPI.getMenuSummary(ids);
                    const ifBadge = content.querySelector('[data-badge="interface"]');
                    const scaleBadge = content.querySelector('[data-badge="scale"]');
                    if (ifBadge && summary.interfaces) {
                        const total = (summary.interfaces.phys || 0) + (summary.interfaces.bundle || 0) + (summary.interfaces.subif || 0);
                        if (total > 0) {
                            ifBadge.textContent = total + ' ifs';
                            ifBadge.style.display = 'inline';
                        }
                    }
                    if (scaleBadge && summary.services) {
                        const s = summary.services;
                        const parts = [];
                        if (s.fxc) parts.push('FXC:' + s.fxc);
                        if (s.l2vpn) parts.push('L2VPN:' + s.l2vpn);
                        if (s.evpn) parts.push('EVPN:' + s.evpn);
                        if (s.vpws) parts.push('VPWS:' + s.vpws);
                        if (s.vrf) parts.push('VRF:' + s.vrf);
                        if (parts.length > 0) {
                            scaleBadge.textContent = parts.slice(0, 3).join(' ');
                            scaleBadge.style.display = 'inline';
                        }
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
            'flowspec-vpn-wizard': () => this.openDeviceSelector('FlowSpec VPN Wizard', (id) => this.openFlowSpecVPNWizard(id)),
            'routing-policy-wizard': () => this.openDeviceSelector('Routing Policy Wizard', (id) => this.openRoutingPolicyWizard(id)),
            'multihoming-wizard': () => this.openMultihomingWizard(),
            'mirror-wizard': () => this.openMirrorWizard(),
            'bgp-wizard': () => this.openDeviceSelector('BGP Configuration', (id) => this.openBGPWizard(id)),
            'igp-wizard': () => this.openDeviceSelector('IGP Configuration', (id) => this.openIGPWizard(id)),
            'system-wizard': () => this.openDeviceSelector('System Config', (id) => this.openSystemWizard(id)),
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
};
window.ScalerGUI = ScalerGUI;
