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
            this.render();
        },
        
        /**
         * Go to next step
         */
        next() {
            // Validate current step
            const currentStepConfig = this.steps[this.currentStep];
            if (currentStepConfig.validate && !currentStepConfig.validate(this.data)) {
                return false;
            }
            
            // Collect data from current step
            if (currentStepConfig.collectData) {
                Object.assign(this.data, currentStepConfig.collectData());
            }
            
            if (this.currentStep < this.steps.length - 1) {
                this.currentStep++;
                this.render();
                return true;
            } else {
                // Complete
                if (this.onComplete) {
                    this.onComplete(this.data);
                }
                return true;
            }
        },
        
        /**
         * Go to previous step
         */
        back() {
            if (this.currentStep > 0) {
                this.currentStep--;
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
            
            nav.innerHTML = `
                <button class="scaler-btn" id="wizard-back" ${isFirst ? 'disabled' : ''}>
                    ← Back
                </button>
                <div class="scaler-wizard-nav-right">
                    ${stepConfig.skipable ? '<button class="scaler-btn" id="wizard-skip">Skip</button>' : ''}
                    <button class="scaler-btn scaler-btn-primary" id="wizard-next">
                        ${isLast ? (stepConfig.finalButtonText || 'Complete') : 'Next →'}
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
    // INITIALIZATION
    // =========================================================================
    
    init() {
        console.log('[ScalerGUI] Initializing v2.0...');
        this.createPanelContainer();
        this.bindKeyboardShortcuts();
        this.addScalerButton();
        console.log('[ScalerGUI] Ready');
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
            'device-manager': () => this.openDeviceManager(),
            'interface-wizard': () => this.openInterfaceWizard(),
            'service-wizard': () => this.openServiceWizard(),
            'multihoming-wizard': () => this.openMultihomingWizard(),
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
                <button class="scaler-menu-btn" data-action="multihoming-wizard">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M12 2v20"/><path d="M2 12h20"/>
                    </svg>
                    Multihoming Wizard
                    <span class="scaler-menu-hint">Sync ESI across PEs</span>
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
            </div>
            
            <div class="scaler-menu-section">
                <h4>Operations</h4>
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
            
        this.openPanel('scaler-menu', 'CONFIG Menu', content, {width: '320px'});
    },
    
    handleMenuAction(action) {
        const actionMap = {
            'device-manager': () => this.openDeviceManager(),
            'sync-all': () => this.syncAllDevices(),
            'quick-load': () => this.openQuickLoad(),
            'interface-wizard': () => this.openDeviceSelector('Interface Wizard', (id) => this.openInterfaceWizard(id)),
            'service-wizard': () => this.openDeviceSelector('Service Wizard', (id) => this.openServiceWizard(id)),
            'multihoming-wizard': () => this.openMultihomingWizard(),
            'bgp-wizard': () => this.openDeviceSelector('BGP Configuration', (id) => this.openBGPWizard(id)),
            'igp-wizard': () => this.openDeviceSelector('IGP Configuration', (id) => this.openIGPWizard(id)),
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
    
    openInterfaceWizard(deviceId = null) {
        if (!deviceId) {
            this.openDeviceSelector('Interface Wizard', (id) => this.openInterfaceWizard(id));
            return;
        }
        
        const content = document.createElement('div');
        content.innerHTML = '<div class="scaler-loading">Loading wizard...</div>';
        
        this.openPanel('interface-wizard', `Interface Wizard - ${deviceId}`, content, {
            width: '550px',
            parentPanel: 'scaler-menu'
        });
        
        // Initialize wizard
        this.WizardController.init({
            panelName: 'interface-wizard',
            title: `Interface Wizard - ${deviceId}`,
            initialData: { deviceId },
            steps: [
                {
                    title: 'Type',
                    render: (data) => `
                        <div class="scaler-form">
            <div class="scaler-form-group">
                <label>Interface Type</label>
                <select id="iface-type" class="scaler-select">
                                    <option value="bundle">bundle (LAG)</option>
                                    <option value="ge100">ge100 (100GigE)</option>
                                    <option value="ge400">ge400 (400GigE)</option>
                                    <option value="ge10">ge10 (10GigE)</option>
                                    <option value="ph">ph (PWHE)</option>
                </select>
            </div>
            <div class="scaler-form-row">
                <div class="scaler-form-group">
                    <label>Start Number</label>
                                    <input type="number" id="iface-start" class="scaler-input" value="${data.startNumber || 1}" min="1">
                </div>
                <div class="scaler-form-group">
                    <label>Count</label>
                                    <input type="number" id="iface-count" class="scaler-input" value="${data.count || 10}" min="1" max="1000">
                </div>
            </div>
                            <div class="scaler-preview-box">
                                <label>DNOS SYNTAX PREVIEW:</label>
                                <pre id="iface-type-preview" class="scaler-syntax-preview">Loading...</pre>
                            </div>
                        </div>
                    `,
                    afterRender: () => {
                        let debounceTimer;
                        const updatePreview = async () => {
                            clearTimeout(debounceTimer);
                            debounceTimer = setTimeout(async () => {
                                const type = document.getElementById('iface-type').value;
                                const start = parseInt(document.getElementById('iface-start').value) || 1;
                                const count = Math.min(parseInt(document.getElementById('iface-count').value) || 10, 3);
                                const preview = document.getElementById('iface-type-preview');
                                if (preview) {
                                    try {
                                        const result = await ScalerAPI.generateInterfaces({
                                            interface_type: type,
                                            start_number: start,
                                            count: count,
                                            create_subinterfaces: false
                                        });
                                        const actualCount = parseInt(document.getElementById('iface-count').value) || 10;
                                        const lines = result.config.split('\n').slice(0, 12);
                                        preview.textContent = lines.join('\n') + (actualCount > 3 ? `\n... (${actualCount} interfaces total)` : '');
                                    } catch (e) {
                                        preview.textContent = `Error: ${e.message}`;
                                    }
                                }
                            }, 300);
                        };
                        document.getElementById('iface-type').addEventListener('change', updatePreview);
                        document.getElementById('iface-start').addEventListener('input', updatePreview);
                        document.getElementById('iface-count').addEventListener('input', updatePreview);
                        updatePreview();
                    },
                    collectData: () => ({
                        interfaceType: document.getElementById('iface-type').value,
                        startNumber: parseInt(document.getElementById('iface-start').value) || 1,
                        count: parseInt(document.getElementById('iface-count').value) || 10
                    })
                },
                {
                    title: 'Location',
                    render: (data) => `
                        <div class="scaler-form">
                            <div class="scaler-info-box">
                                ${data.interfaceType === 'bundle' ? 
                                    'Bundle interfaces use logical numbering only.' :
                                    'Physical interfaces require slot/bay/port location.'}
                            </div>
                            ${data.interfaceType !== 'bundle' ? `
            <div class="scaler-form-row">
                <div class="scaler-form-group">
                    <label>Slot</label>
                                    <input type="number" id="iface-slot" class="scaler-input" value="${data.slot || 0}" min="0">
                </div>
                <div class="scaler-form-group">
                    <label>Bay</label>
                                    <input type="number" id="iface-bay" class="scaler-input" value="${data.bay || 0}" min="0">
                </div>
                                <div class="scaler-form-group">
                                    <label>Port Start</label>
                                    <input type="number" id="iface-port" class="scaler-input" value="${data.portStart || 0}" min="0">
            </div>
                            </div>
                            ` : '<p class="scaler-info">Bundle interfaces will be numbered sequentially.</p>'}
                        </div>
                    `,
                    collectData: () => ({
                        slot: parseInt(document.getElementById('iface-slot')?.value) || 0,
                        bay: parseInt(document.getElementById('iface-bay')?.value) || 0,
                        portStart: parseInt(document.getElementById('iface-port')?.value) || 0
                    }),
                    skipable: true
                },
                {
                    title: 'Sub-ifs',
                    render: (data) => `
                        <div class="scaler-form">
            <div class="scaler-form-group">
                                <label>
                                    <input type="checkbox" id="create-subif" ${data.createSubinterfaces !== false ? 'checked' : ''}>
                                    Create Sub-interfaces
                                </label>
            </div>
                            <div id="subif-options" ${data.createSubinterfaces === false ? 'style="display:none"' : ''}>
                <div class="scaler-form-row">
                                    <div class="scaler-form-group">
                                        <label>Sub-ifs per Parent</label>
                                        <input type="number" id="subif-count" class="scaler-input" value="${data.subifCount || 1}" min="1" max="4094">
                                    </div>
                    <div class="scaler-form-group">
                        <label>VLAN Start</label>
                                        <input type="number" id="vlan-start" class="scaler-input" value="${data.vlanStart || 100}" min="1" max="4094">
                    </div>
                                </div>
                            </div>
                            <div class="scaler-preview-box">
                                <label>DNOS SYNTAX PREVIEW:</label>
                                <pre id="subif-preview" class="scaler-syntax-preview">Loading...</pre>
                            </div>
                        </div>
                    `,
                    afterRender: (data) => {
                        const parentCount = Math.min(data.count || 10, 2);
                        let debounceTimer;
                        const updatePreview = async () => {
                            clearTimeout(debounceTimer);
                            debounceTimer = setTimeout(async () => {
                                const createSubif = document.getElementById('create-subif').checked;
                                const subifCount = Math.min(parseInt(document.getElementById('subif-count')?.value) || 1, 3);
                                const vlanStart = parseInt(document.getElementById('vlan-start')?.value) || 100;
                                const preview = document.getElementById('subif-preview');
                                if (preview) {
                                    try {
                                        const result = await ScalerAPI.generateInterfaces({
                                            interface_type: data.interfaceType || 'bundle',
                                            start_number: data.startNumber || 1,
                                            count: parentCount,
                                            create_subinterfaces: createSubif,
                                            subif_count_per_interface: subifCount,
                                            subif_vlan_start: vlanStart,
                                            subif_vlan_step: 1,
                                            encapsulation: 'dot1q'
                                        });
                                        const actualParentCount = data.count || 10;
                                        const actualSubifCount = parseInt(document.getElementById('subif-count')?.value) || 1;
                                        const totalSubifs = actualParentCount * actualSubifCount;
                                        const lines = result.config.split('\n').slice(0, 18);
                                        preview.textContent = lines.join('\n') + 
                                            (actualParentCount > 2 || actualSubifCount > 3 ? `\n... (${totalSubifs} total sub-interfaces)` : '');
                                    } catch (e) {
                                        preview.textContent = `Error: ${e.message}`;
                                    }
                                }
                            }, 300);
                        };
                        document.getElementById('create-subif').addEventListener('change', (e) => {
                            document.getElementById('subif-options').style.display = e.target.checked ? 'block' : 'none';
                            updatePreview();
                        });
                        document.getElementById('subif-count')?.addEventListener('input', updatePreview);
                        document.getElementById('vlan-start')?.addEventListener('input', updatePreview);
                        updatePreview();
                    },
                    collectData: () => ({
                        createSubinterfaces: document.getElementById('create-subif').checked,
                        subifCount: parseInt(document.getElementById('subif-count')?.value) || 1,
                        vlanStart: parseInt(document.getElementById('vlan-start')?.value) || 100
                    })
                },
                {
                    title: 'Encap',
                    render: (data) => `
                        <div class="scaler-form">
                    <div class="scaler-form-group">
                        <label>Encapsulation</label>
                                <div class="scaler-radio-group">
                                    <label class="scaler-radio">
                                        <input type="radio" name="encap" value="dot1q" ${data.encapsulation !== 'qinq' ? 'checked' : ''}>
                                        <span>Single Tag (dot1q)</span>
                                    </label>
                                    <label class="scaler-radio">
                                        <input type="radio" name="encap" value="qinq" ${data.encapsulation === 'qinq' ? 'checked' : ''}>
                                        <span>Double Tag (QinQ)</span>
                                    </label>
                    </div>
                            </div>
                            <div id="qinq-options" style="display: ${data.encapsulation === 'qinq' ? 'block' : 'none'}">
                                <div class="scaler-form-group">
                                    <label>Inner VLAN Start</label>
                                    <input type="number" id="inner-vlan" class="scaler-input" value="${data.innerVlan || 1}" min="1" max="4094">
                                </div>
                            </div>
                            <div class="scaler-form-row">
                                <div class="scaler-form-group">
                                    <label>VLAN Step</label>
                                    <input type="number" id="vlan-step" class="scaler-input" value="${data.vlanStep || 1}" min="1">
                </div>
            </div>
            <div class="scaler-preview-box">
                                <label>DNOS SYNTAX PREVIEW:</label>
                                <pre id="encap-preview" class="scaler-syntax-preview">Loading...</pre>
            </div>
            </div>
                    `,
                    afterRender: (data) => {
                        let debounceTimer;
                        const updatePreview = async () => {
                            clearTimeout(debounceTimer);
                            debounceTimer = setTimeout(async () => {
                                const encap = document.querySelector('input[name="encap"]:checked')?.value || 'dot1q';
                                const vlanStart = data.vlanStart || 100;
                                const innerVlan = parseInt(document.getElementById('inner-vlan')?.value) || 1;
                                const vlanStep = parseInt(document.getElementById('vlan-step')?.value) || 1;
                                const preview = document.getElementById('encap-preview');
                                if (preview) {
                                    try {
                                        const result = await ScalerAPI.generateInterfaces({
                                            interface_type: data.interfaceType || 'bundle',
                                            start_number: data.startNumber || 1,
                                            count: 1,
                                            create_subinterfaces: data.createSubinterfaces !== false,
                                            subif_count_per_interface: Math.min(data.subifCount || 1, 2),
                                            subif_vlan_start: vlanStart,
                                            subif_vlan_step: vlanStep,
                                            encapsulation: encap
                                        });
                                        const lines = result.config.split('\n').slice(0, 15);
                                        preview.textContent = lines.join('\n');
                                    } catch (e) {
                                        preview.textContent = `Error: ${e.message}`;
                                    }
                                }
                            }, 300);
                        };
                        document.querySelectorAll('input[name="encap"]').forEach(radio => {
                            radio.onchange = (e) => {
                                document.getElementById('qinq-options').style.display = 
                                    e.target.value === 'qinq' ? 'block' : 'none';
                                updatePreview();
                            };
                        });
                        document.getElementById('inner-vlan')?.addEventListener('input', updatePreview);
                        document.getElementById('vlan-step')?.addEventListener('input', updatePreview);
                        updatePreview();
                    },
                    collectData: () => ({
                        encapsulation: document.querySelector('input[name="encap"]:checked')?.value || 'dot1q',
                        innerVlan: parseInt(document.getElementById('inner-vlan')?.value) || 1,
                        vlanStep: parseInt(document.getElementById('vlan-step')?.value) || 1
                    })
                },
                {
                    title: 'Review',
                    render: (data) => `
                        <div class="scaler-review">
                            <h4>Configuration Summary</h4>
                            <table class="scaler-table scaler-summary-table">
                                <tr><td>Device</td><td>${data.deviceId}</td></tr>
                                <tr><td>Interface Type</td><td>${data.interfaceType}</td></tr>
                                <tr><td>Count</td><td>${data.count} interfaces</td></tr>
                                <tr><td>Starting Number</td><td>${data.startNumber}</td></tr>
                                <tr><td>Sub-interfaces</td><td>${data.createSubinterfaces ? `${data.subifCount} per parent` : 'None'}</td></tr>
                                <tr><td>Encapsulation</td><td>${data.encapsulation}</td></tr>
                                <tr><td>VLAN Start</td><td>${data.vlanStart}</td></tr>
                            </table>
                            <div class="scaler-preview-box">
                                <label>Preview:</label>
                                <pre id="config-preview">Generating preview...</pre>
                            </div>
                        </div>
                    `,
                    afterRender: async (data) => {
                        try {
                            const result = await ScalerAPI.generateInterfaces({
                                interface_type: data.interfaceType,
                                start_number: data.startNumber,
                                count: data.count,
                                slot: data.slot || 0,
                                bay: data.bay || 0,
                                port_start: data.portStart || 0,
                                create_subinterfaces: data.createSubinterfaces,
                                subif_count_per_interface: data.subifCount,
                                subif_vlan_start: data.vlanStart,
                                subif_vlan_step: data.vlanStep || 1,
                                encapsulation: data.encapsulation
                            });
                            
                            const preview = document.getElementById('config-preview');
                            if (preview) {
                const lines = result.config.split('\n');
                                preview.textContent = lines.slice(0, 25).join('\n') + 
                                    (lines.length > 25 ? `\n... (${result.lines} lines total)` : '');
                            }
                            
                            // Store the generated config
                            ScalerGUI.WizardController.data.generatedConfig = result.config;
                        } catch (e) {
                            document.getElementById('config-preview').textContent = `Error: ${e.message}`;
                        }
                    }
                },
                {
                    title: 'Push',
                    finalButtonText: 'Push Configuration',
                    render: (data) => `
                        <div class="scaler-form">
                            <div class="scaler-form-group">
                                <label>Push Mode</label>
                                <div class="scaler-radio-group">
                                    <label class="scaler-radio">
                                        <input type="radio" name="push-mode" value="dry_run" checked>
                                        <span>Commit Check (Dry Run)</span>
                                    </label>
                                    <label class="scaler-radio">
                                        <input type="radio" name="push-mode" value="push">
                                        <span>Push and Commit</span>
                                    </label>
                                </div>
                            </div>
                            <div class="scaler-info-box">
                                Ready to push ${data.count} interfaces to ${data.deviceId}.
                            </div>
                        </div>
                    `,
                    collectData: () => ({
                        dryRun: document.querySelector('input[name="push-mode"]:checked')?.value === 'dry_run'
                    })
                }
            ],
            onComplete: async (data) => {
                try {
                const result = await ScalerAPI.pushConfig({
                        device_id: data.deviceId,
                        config: data.generatedConfig,
                    hierarchy: 'interfaces', 
                    mode: 'merge', 
                        dry_run: data.dryRun
                });
                    
                    this.closePanel('interface-wizard');
                    this.showProgress(result.job_id, `Pushing interfaces to ${data.deviceId}`);
            } catch (e) {
                    this.showNotification(`Push failed: ${e.message}`, 'error');
                }
            }
        });
    },
    
    // =========================================================================
    // SERVICE WIZARD (5 Steps)
    // =========================================================================
    
    openServiceWizard(deviceId = null) {
        if (!deviceId) {
            this.openDeviceSelector('Service Wizard', (id) => this.openServiceWizard(id));
            return;
        }
        
        const content = document.createElement('div');
        content.innerHTML = '<div class="scaler-loading">Loading wizard...</div>';
        
        this.openPanel('service-wizard', `Service Wizard - ${deviceId}`, content, {
            width: '550px',
            parentPanel: 'scaler-menu'
        });
        
        this.WizardController.init({
            panelName: 'service-wizard',
            title: `Service Wizard - ${deviceId}`,
            initialData: { deviceId },
            steps: [
                {
                    title: 'Type',
                    render: (data) => `
                        <div class="scaler-form">
            <div class="scaler-form-group">
                <label>Service Type</label>
                <select id="svc-type" class="scaler-select">
                                    <option value="evpn-vpws-fxc">EVPN VPWS FXC (Flexible Cross-Connect)</option>
                                    <option value="evpn">EVPN VPLS (Bridge Domain)</option>
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
                    render: (data) => `
                        <div class="scaler-form">
            <div class="scaler-form-row">
                <div class="scaler-form-group">
                                    <label>BGP ASN</label>
                                    <input type="number" id="bgp-asn" class="scaler-input" value="${data.bgpAsn || 65000}" min="1" max="4294967295">
                </div>
                <div class="scaler-form-group">
                                    <label>RT Start</label>
                                    <input type="number" id="evi-start" class="scaler-input" value="${data.eviStart || 1000}" min="1">
                </div>
            </div>
            <div class="scaler-form-group">
                                <label>Router ID (Lo0 address for RD)</label>
                                <input type="text" id="router-id" class="scaler-input" value="${data.routerId || '1.1.1.1'}" placeholder="e.g., 1.1.1.1">
                                <small class="scaler-form-hint">Used for route-distinguisher: &lt;router-id&gt;:&lt;rt-value&gt;</small>
            </div>
            <div class="scaler-preview-box">
                                <label>DNOS SYNTAX PREVIEW:</label>
                                <pre id="rt-evi-preview" class="scaler-syntax-preview">Loading...</pre>
            </div>
            </div>
                    `,
                    afterRender: (data) => {
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
                        bgpAsn: parseInt(document.getElementById('bgp-asn').value) || 65000,
                        eviStart: parseInt(document.getElementById('evi-start').value) || 1000,
                        routerId: document.getElementById('router-id').value || '1.1.1.1',
                        rdBase: String(parseInt(document.getElementById('bgp-asn').value) || 65000)
                    })
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
                        </div>
                    `,
                    afterRender: async (data) => {
                        try {
                            const result = await ScalerAPI.generateServices({
                                service_type: data.serviceType,
                                name_prefix: data.namePrefix,
                                start_number: data.startNumber,
                                count: data.count,
                                service_id_start: data.eviStart,
                                evi_start: data.eviStart,
                                rd_base: data.rdBase
                            });
                            
                            const preview = document.getElementById('config-preview');
                            if (preview) {
                                const lines = result.config.split('\n');
                                preview.textContent = lines.slice(0, 30).join('\n') + 
                                    (lines.length > 30 ? `\n... (${result.lines} lines total)` : '');
                            }
                            
                            ScalerGUI.WizardController.data.generatedConfig = result.config;
                        } catch (e) {
                            document.getElementById('config-preview').textContent = `Error: ${e.message}`;
                        }
                    }
                },
                {
                    title: 'Push',
                    finalButtonText: 'Push Configuration',
                    render: (data) => `
                        <div class="scaler-form">
                            <div class="scaler-form-group">
                                <label>Push Mode</label>
                                <div class="scaler-radio-group">
                                    <label class="scaler-radio">
                                        <input type="radio" name="push-mode" value="dry_run" checked>
                                        <span>Commit Check (Dry Run)</span>
                                    </label>
                                    <label class="scaler-radio">
                                        <input type="radio" name="push-mode" value="push">
                                        <span>Push and Commit</span>
                                    </label>
                                </div>
                            </div>
                            <div class="scaler-info-box">
                                Ready to push ${data.count} ${data.serviceType} services to ${data.deviceId}.
                            </div>
                        </div>
                    `,
                    collectData: () => ({
                        dryRun: document.querySelector('input[name="push-mode"]:checked')?.value === 'dry_run'
                    })
                }
            ],
            onComplete: async (data) => {
                try {
                const result = await ScalerAPI.pushConfig({
                        device_id: data.deviceId,
                        config: data.generatedConfig,
                    hierarchy: 'services',
                    mode: 'merge',
                        dry_run: data.dryRun
                });
                    
                    this.closePanel('service-wizard');
                    this.showProgress(result.job_id, `Pushing services to ${data.deviceId}`);
            } catch (e) {
                    this.showNotification(`Push failed: ${e.message}`, 'error');
                }
            }
        });
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
        
        listEl.innerHTML = '<div class="scaler-loading">Loading devices...</div>';
        
        try {
            const data = await ScalerAPI.getDevices();
            this.state.deviceCache = {};
            
            if (data.devices.length === 0) {
                listEl.innerHTML = `<div class="scaler-empty">No devices registered.<br>Click "Add Device" to get started.</div>`;
                return;
            }
            
            listEl.innerHTML = data.devices.map(device => {
                this.state.deviceCache[device.id] = device;
                return `
                    <div class="scaler-device-card" data-device-id="${device.id}">
                        <div class="scaler-device-status" data-status="unknown"></div>
                        <div class="scaler-device-info">
                            <div class="scaler-device-name">${device.hostname}</div>
                            <div class="scaler-device-ip">${device.ip}</div>
                            <div class="scaler-device-platform">${device.platform || 'NCP'}</div>
            </div>
                        <div class="scaler-device-actions">
                            <button class="scaler-btn-icon" data-action="test" title="Test Connection">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                                    <path d="M22 4L12 14.01l-3-3"/>
                                </svg>
                            </button>
                            <button class="scaler-btn-icon" data-action="sync" title="Sync Config">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 2v6h-6"/>
                                    <path d="M3 12a9 9 0 0 1 15-6.7L21 8"/>
                                </svg>
                            </button>
                            <button class="scaler-btn-icon scaler-btn-danger" data-action="delete" title="Delete Device">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M3 6h18"/>
                                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
                                </svg>
                            </button>
                </div>
            </div>
                `;
            }).join('');
            
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
        } catch (error) {
            listEl.innerHTML = `<div class="scaler-error">Failed to load devices: ${error.message}</div>`;
        }
    },
    
    async handleDeviceAction(action, deviceId) {
        const card = document.querySelector(`[data-device-id="${deviceId}"]`);
        const statusEl = card?.querySelector('.scaler-device-status');
        
        switch(action) {
            case 'test':
                if (statusEl) statusEl.dataset.status = 'testing';
                try {
                    await ScalerAPI.testConnection(deviceId);
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
    
    async openDeviceSelector(title, onSelect) {
        const content = document.createElement('div');
        content.innerHTML = '<div class="scaler-loading">Loading devices...</div>';
        
        this.openPanel('device-selector', `Select Device - ${title}`, content, {width: '350px'});
        
        try {
            const data = await ScalerAPI.getDevices();
            
            content.innerHTML = `
                <div class="scaler-device-list scaler-device-select-list">
                    ${data.devices.map(device => `
                        <div class="scaler-device-select-item" data-device-id="${device.id}">
                            <span class="scaler-device-name">${device.hostname}</span>
                            <span class="scaler-device-ip">${device.ip}</span>
                        </div>
                    `).join('')}
                </div>
            `;
            
            content.querySelectorAll('.scaler-device-select-item').forEach(item => {
                item.onclick = () => {
                    this.closePanel('device-selector');
                    onSelect(item.dataset.deviceId);
                };
            });
        } catch (error) {
            content.innerHTML = `<div class="scaler-error">Failed to load devices: ${error.message}</div>`;
        }
    },
    
    showProgress(jobId, title, options = {}) {
        const content = document.createElement('div');
        content.className = 'scaler-progress-panel';
        content.innerHTML = `
            <div class="scaler-progress-bar-container">
                <div class="scaler-progress-bar">
                    <div class="scaler-progress-fill" id="progress-fill-${jobId}" style="width: 0%"></div>
            </div>
                <span class="scaler-progress-text" id="progress-text-${jobId}">0%</span>
            </div>
            <div class="scaler-progress-steps" id="progress-steps-${jobId}"></div>
            <div class="scaler-terminal" id="progress-terminal-${jobId}">
                <div class="scaler-terminal-content"></div>
            </div>
            <div class="scaler-progress-actions">
                <button class="scaler-btn scaler-btn-danger" id="progress-cancel-${jobId}">Cancel</button>
            </div>
        `;
        
        const panel = this.openPanel(`progress-${jobId}`, title, content, {minimizable: true, width: '500px'});
        
        document.getElementById(`progress-cancel-${jobId}`).onclick = async () => {
            try {
                await ScalerAPI.cancelOperation(jobId);
                this.showNotification('Operation cancelled', 'warning');
            } catch (e) {
                this.showNotification(e.message, 'error');
            }
        };
        
        const ws = ScalerAPI.connectProgress(jobId, {
            onProgress: (percent, message) => {
                const fill = document.getElementById(`progress-fill-${jobId}`);
                const text = document.getElementById(`progress-text-${jobId}`);
                if (fill) fill.style.width = `${percent}%`;
                if (text) text.textContent = `${percent}% - ${message || ''}`;
            },
            onTerminal: (line) => {
                const terminal = document.querySelector(`#progress-terminal-${jobId} .scaler-terminal-content`);
                if (terminal) {
                    terminal.innerHTML += `<div class="scaler-terminal-line">${this.escapeHtml(line)}</div>`;
                    terminal.scrollTop = terminal.scrollHeight;
                }
            },
            onStep: (current, total, name) => {
                const stepsEl = document.getElementById(`progress-steps-${jobId}`);
                if (stepsEl) {
                    stepsEl.innerHTML = `<div class="scaler-step-info">Step ${current} of ${total}: ${name}</div>`;
                }
            },
            onComplete: (success, result) => {
                const fill = document.getElementById(`progress-fill-${jobId}`);
                const text = document.getElementById(`progress-text-${jobId}`);
                if (fill) {
                    fill.style.width = '100%';
                    fill.classList.add(success ? 'scaler-progress-success' : 'scaler-progress-error');
                }
                if (text) text.textContent = success ? 'Complete!' : 'Failed';
                
                const cancelBtn = document.getElementById(`progress-cancel-${jobId}`);
                if (cancelBtn) {
                    cancelBtn.textContent = 'Close';
                    cancelBtn.className = 'scaler-btn';
                    cancelBtn.onclick = () => this.closePanel(`progress-${jobId}`);
                }
                
                this.showNotification(
                    success ? 'Operation completed successfully' : 'Operation failed',
                    success ? 'success' : 'error'
                );
                
                options.onComplete?.(success, result);
            },
            onError: (message) => {
                this.showNotification(`Error: ${message}`, 'error');
            }
        });
        
        this.state.jobs[jobId] = { ws, panel };
        return panel;
    },
    
    showNotification(message, type = 'info') {
        document.querySelectorAll('.scaler-notification').forEach(n => n.remove());
        
        const notification = document.createElement('div');
        notification.className = `scaler-notification scaler-notification-${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        requestAnimationFrame(() => {
            notification.classList.add('scaler-notification-show');
        });
        
        setTimeout(() => {
            notification.classList.remove('scaler-notification-show');
            setTimeout(() => notification.remove(), 300);
        }, 4000);
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
                    statusSpan.innerHTML = `✅ Synced (${result.lines || '?'} lines)`;
                    statusSpan.style.color = 'var(--success-color, #4caf50)';
                    row.style.background = 'rgba(76, 175, 80, 0.1)';
                } catch (e) {
                    failCount++;
                    statusSpan.innerHTML = `❌ ${e.message}`;
                    statusSpan.style.color = 'var(--error-color, #f44336)';
                    row.style.background = 'rgba(244, 67, 54, 0.1)';
                }
            }
            
            // Show summary
            summary.style.display = 'block';
            if (failCount === 0) {
                summaryText.innerHTML = `<span style="color: var(--success-color, #4caf50);">✅ All ${successCount} device(s) synced successfully!</span>`;
                statusMsg.innerHTML = '✅ Sync complete! Config cache updated.';
                statusMsg.style.color = 'var(--success-color, #4caf50)';
                    } else {
                summaryText.innerHTML = `<span style="color: var(--success-color, #4caf50);">${successCount} succeeded</span>, <span style="color: var(--error-color, #f44336);">${failCount} failed</span>`;
                statusMsg.innerHTML = '⚠️ Sync completed with errors.';
                statusMsg.style.color = 'var(--warning-color, orange)';
            }
            
            closeBtn.style.display = 'block';
            
        } catch (error) {
            statusMsg.innerHTML = `❌ Failed to fetch devices: ${error.message}`;
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
                                    this.showNotification(`✅ Deleted ${fileName}`, 'success');
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
                                this.showNotification(`❌ Delete failed: ${e.message}`, 'error');
                            }
                        };
                    });
                    
                } catch (e) {
                    filesContainer.innerHTML = `<div style="color: var(--error-color); padding: 40px; text-align: center;">❌ ${e.message}</div>`;
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
                            this.showNotification(`✅ Pushed ${selectedFile.filename} to device`, 'success');
                        } else {
                            throw new Error('Push failed');
                        }
                    } catch (e) {
                        this.showNotification(`❌ Push failed: ${e.message}`, 'error');
                    }
                };
            }
            
            if (compareBtn) {
                compareBtn.onclick = async () => {
                    if (!selectedFile) {
                        this.showNotification('Select a file first', 'warning');
                        return;
                    }
                    this.showNotification(`Compare ${selectedFile.filename} - coming soon!`, 'info');
                };
            }
            
            // Load first device's files automatically
            loadFiles(devices[0].id);
        }, 100);
    },
    openBGPWizard(deviceId) { this.showNotification('BGP Wizard coming soon', 'info'); },
    openIGPWizard(deviceId) { this.showNotification('IGP Wizard coming soon', 'info'); },
    openDeviceCompare() { this.showNotification('Compare feature available', 'info'); },
    openSyncStatus() { this.showNotification('Sync Status coming soon', 'info'); },
    openDeleteHierarchy(deviceId) { this.showNotification('Delete Hierarchy coming soon', 'info'); },
    openModifyInterfaces() { this.showNotification('Modify Interfaces coming soon', 'info'); },
    openBatchOperations() { this.showNotification('Batch Operations coming soon', 'info'); },
    openTemplateManager() { this.showNotification('Template Manager coming soon', 'info'); },
    showConfigSummary(deviceId) { this.showNotification(`Config Summary for ${deviceId}`, 'info'); },
    openAddDeviceDialog() { this.showNotification('Add Device coming soon', 'info'); }
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
