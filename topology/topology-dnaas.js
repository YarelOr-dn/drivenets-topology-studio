// ============================================================================
// TOPOLOGY DNAAS MODULE
// ============================================================================
// Handles DNAAS (Disaggregated Network As A Service) discovery and operations.
//
// Features:
//   - Network topology discovery via LLDP
//   - Multi-BD (Bridge Domain) discovery
//   - Device inventory management
//   - Path tracing by serial number
//   - BD legend and visualization
//   - DNAAS topology loading/saving
//
// Usage:
//   const dnaas = new DnaasManager(editor);
//   dnaas.startDiscovery('SERIAL123');
//   dnaas.loadTopology('discover');
// ============================================================================

class DnaasManager {
    constructor(editor) {
        this.editor = editor;
        this._currentDiscoveryJobId = null;
        this._discoveryAbortController = null;
    }

    // ========== PANEL SETUP ==========

    /**
     * Set up DNAAS panel button and event listeners
     * Called by ToolbarManager.setupDnaasPanel()
     */
    setupPanel() {
        const dnaasBtn = document.getElementById('btn-dnaas');
        const dnaasPanel = document.getElementById('dnaas-panel');
        
        if (!dnaasBtn || !dnaasPanel) {
            console.warn('[DNAAS] Panel elements not found');
            return;
        }

        // Toggle panel on button click
        dnaasBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isVisible = dnaasPanel.style.display === 'block';
            
            if (!isVisible) {
                // Close Topologies dropdown if open
                const topoDD = document.getElementById('topologies-dropdown-menu');
                const topoBtn = document.getElementById('btn-topologies');
                if (topoDD && topoDD.style.display === 'block') {
                    topoDD.style.display = 'none';
                    if (topoBtn) topoBtn.classList.remove('topologies-open');
                }
                // Close Network Mapper panel if open
                const nmPanel = document.getElementById('network-mapper-panel');
                const nmBtn = document.getElementById('btn-network-mapper');
                if (nmPanel && nmPanel.style.display === 'block') {
                    nmPanel.style.display = 'none';
                    if (nmBtn) nmBtn.classList.remove('nm-panel-open');
                }
                
                this.positionPanel(dnaasBtn, dnaasPanel);
                dnaasPanel.style.display = 'block';
                dnaasBtn.classList.add('dnaas-panel-open');
                this.populateSuggestions();
            } else {
                dnaasPanel.style.display = 'none';
                dnaasBtn.classList.remove('dnaas-panel-open');
            }
        });

        // Close panel when clicking outside
        document.addEventListener('click', (e) => {
            if (!dnaasBtn.contains(e.target) && !dnaasPanel.contains(e.target)) {
                dnaasPanel.style.display = 'none';
                dnaasBtn.classList.remove('dnaas-panel-open');
            }
        });

        // Set up panel buttons
        this.setupPanelButtons(dnaasPanel);
        console.log('[OK] DnaasManager panel set up');
    }

    positionPanel(btn, panel) {
        const btnRect = btn.getBoundingClientRect();
        const panelWidth = Math.min(380, window.innerWidth - 20);
        const padding = 10;
        
        let left = btnRect.left;
        let top = btnRect.bottom + 5;
        
        // Keep within viewport
        if (left + panelWidth > window.innerWidth - padding) {
            left = window.innerWidth - panelWidth - padding;
        }
        if (top + 400 > window.innerHeight) {
            top = btnRect.top - 400 - 5;
        }
        
        panel.style.left = left + 'px';
        panel.style.top = top + 'px';
    }

    setupPanelButtons(panel) {
        // Start Discovery button
        const startBtn = document.getElementById('dnaas-start-discovery');
        const serialInput = document.getElementById('dnaas-serial-input');
        if (startBtn && serialInput) {
            startBtn.addEventListener('click', () => {
                const serial = serialInput.value.trim();
                if (!serial) {
                    this.editor.showToast('Please enter a device serial', 'warning');
                    return;
                }
                if (this.isRouter(serial)) {
                    this.editor.showToast('Discovery must start from a Termination device (PE/CE), not from DNAAS routers', 'error');
                    return;
                }
                this.startMultiBdDiscovery(serial);
            });
        }

        // Cancel Discovery button
        const cancelBtn = document.getElementById('dnaas-cancel-discovery');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.cancelDiscovery());
        }

        // Dismiss Result button
        const dismissBtn = document.getElementById('dnaas-dismiss-result');
        if (dismissBtn) {
            dismissBtn.addEventListener('click', () => this.dismissResult());
        }

        // Load from file button
        const loadJsonBtn = document.getElementById('dnaas-load-json');
        if (loadJsonBtn) {
            loadJsonBtn.addEventListener('click', () => this.loadFromFile());
        }

        // Load Latest (BD210) button
        const bd210Btn = document.getElementById('dnaas-bd210');
        if (bd210Btn) {
            bd210Btn.addEventListener('click', () => this.loadLatestDiscovery());
        }

        // Trace Serial button
        const traceBtn = document.getElementById('dnaas-trace-serial');
        if (traceBtn) {
            traceBtn.addEventListener('click', () => this.showTraceDialog());
        }

        // Find BDs button
        const findBdsBtn = document.getElementById('dnaas-find-bds');
        if (findBdsBtn) {
            findBdsBtn.addEventListener('click', () => this.showFindBDsDialog());
        }

        // View Inventory button
        const inventoryBtn = document.getElementById('dnaas-view-inventory');
        if (inventoryBtn) {
            inventoryBtn.addEventListener('click', () => this.showInventoryDialog());
        }

        // View Path Devices button
        const pathDevicesBtn = document.getElementById('dnaas-view-path-devices');
        if (pathDevicesBtn) {
            pathDevicesBtn.addEventListener('click', () => this.showPathDevicesDialog());
        }
    }

    // ========== DISCOVERY ==========

    /**
     * Start Multi-BD discovery from a seed device
     * @param {string} serial - Device serial number
     */
    startMultiBdDiscovery(serial) {
        // Delegate to editor method for now (will be moved later)
        if (this.editor.startMultiBdDiscovery) {
            this.editor.startMultiBdDiscovery(serial);
        } else {
            console.warn('[DNAAS] startMultiBdDiscovery not implemented');
            this.editor.showToast('Discovery not available', 'error');
        }
    }

    /**
     * Cancel ongoing discovery
     */
    cancelDiscovery() {
        if (this.editor.cancelDnaasDiscovery) {
            this.editor.cancelDnaasDiscovery();
        }
    }

    /**
     * Dismiss discovery result without loading
     */
    dismissResult() {
        if (this.editor.dismissDnaasResult) {
            this.editor.dismissDnaasResult();
        }
    }

    // ========== LOADING ==========

    /**
     * Load DNAAS topology by type
     * @param {string} type - 'discover', 'logical-bd210', etc.
     */
    loadTopology(type) {
        if (this.editor.loadDnaasTopology) {
            this.editor.loadDnaasTopology(type);
        }
    }

    /**
     * Load latest discovery file from server
     */
    async loadLatestDiscovery() {
        try {
            const resp = await fetch('/api/dnaas/discovery/list');
            if (!resp.ok) throw new Error(`API error: ${resp.status}`);
            
            const files = await resp.json();
            if (files.length === 0) {
                this.editor.showToast('No discovery files found', 'warning');
                return;
            }
            
            // Get the most recent file
            const latestFile = files[0];
            const dataResp = await fetch(`/api/dnaas/discovery/file/${encodeURIComponent(latestFile.name)}`);
            if (!dataResp.ok) throw new Error(`Failed to load file: ${dataResp.status}`);
            
            const data = await dataResp.json();
            this.loadData(data);
            this.editor.showToast(`Loaded: ${latestFile.name}`, 'success');
            
        } catch (err) {
            console.error('[DNAAS] Load error:', err);
            this.editor.showToast(`Failed to load: ${err.message}`, 'error');
        }
    }

    /**
     * Load DNAAS data into canvas
     * @param {object} data - Discovery data
     */
    loadData(data) {
        if (this.editor.loadDnaasData) {
            this.editor.loadDnaasData(data);
        }
    }

    /**
     * Load DNAAS data from local file
     */
    loadFromFile() {
        if (this.editor.loadDnaasFromFile) {
            this.editor.loadDnaasFromFile();
        }
    }

    // ========== DIALOGS ==========

    showTraceDialog() {
        if (this.editor.showDnaasTraceDialog) {
            this.editor.showDnaasTraceDialog();
        }
    }

    showFindBDsDialog() {
        if (this.editor.showDnaasFindBDsDialog) {
            this.editor.showDnaasFindBDsDialog();
        }
    }

    showInventoryDialog() {
        if (this.editor.showDnaasInventoryDialog) {
            this.editor.showDnaasInventoryDialog();
        }
    }

    showPathDevicesDialog() {
        if (this.editor.showDnaasPathDevicesDialog) {
            this.editor.showDnaasPathDevicesDialog();
        }
    }

    // ========== UTILITIES ==========

    /**
     * Check if device is a DNAAS router/fabric device (not allowed as discovery start)
     * These are the DNAAS fabric devices, not termination devices like PE/CE.
     * @param {string} labelOrAddr - Device label, hostname, or address to check
     * @returns {boolean} True if this is a DNAAS router
     */
    isRouter(labelOrAddr) {
        if (!labelOrAddr) return false;
        const upperLabel = labelOrAddr.toUpperCase();
        
        // DNAAS fabric device patterns
        const dnaasPatterns = [
            'DNAAS',
            'LEAF',
            'SPINE',
            'FABRIC',
            'TOR',
            'AGGREGATION',
            'AGG-',
            'CORE-',
            '-LEAF',
            '-SPINE',
            'NCM',  // Network Control Module
            'NCF'   // Network Control Fabric
        ];
        
        return dnaasPatterns.some(pattern => upperLabel.includes(pattern));
    }

    /**
     * Populate device suggestions in the serial input
     */
    populateSuggestions() {
        if (this.editor.populateDnaasSuggestions) {
            this.editor.populateDnaasSuggestions();
        }
    }

    /**
     * Show auto-fill indicator for DNAAS data
     */
    showAutoFillIndicator() {
        if (this.editor.showDnaasAutoFillIndicator) {
            this.editor.showDnaasAutoFillIndicator();
        }
    }
}

// Factory function
window.createDnaasManager = function(editor) {
    return new DnaasManager(editor);
};

// Export for module use
window.DnaasManager = DnaasManager;
